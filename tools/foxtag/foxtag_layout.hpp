// foxtag_layout.hpp — the LAYOUT fact-producer (D-337 increment 2a; consolidates the
// emit_record_layout.lua / recordlayout.lua path into the core).
//
// Drives clang `-Xclang -fdump-record-layouts` (LAYOUT facts are Itanium-ABI-identical to the
// shipped g++ — D-321; CODEGEN facts stay g++, a separate producer) and parses every record's
// sizeof / align / top-level field offsets + the 64B cache-line STRADDLERS out of the dump.
//
// This is a LINE-FOR-LINE port of the plugin's tested logic (sizeprobe.flags_for +
// recordlayout.parse/field_size/straddlers + emit_record_layout.lua's layout-flag subset),
// emitting the SAME JSON shape: { "<record>": { size, align, straddlers:[{name,off,size}] } }.
// `foxtag/parity_check.sh` section 4 diffs this against the Lua emitter on the same TU —
// the D-337 migration gate; the Lua stays authoritative for the plugin until phase 5 swaps.
//
// RC-E discipline: NEVER a silent empty success — zero parsed records = loud exit 2.

#pragma once

#include "foxtag.hpp"

#include <unistd.h>   // getpid (the split-capture stderr temp file)

namespace foxtag {

//======================================================================
// minimal JSON reader (for compile_commands.json — strings/arrays/objects)
//======================================================================

struct JVal {
    enum Kind { STR, ARR, OBJ, OTHER } kind = OTHER;
    string str;
    vector<JVal> arr;
    std::map<string, JVal> obj;
};

inline void json_skip_ws(const string& t, size_t& i) {
    while (i < t.size() && (t[i] == ' ' || t[i] == '\t' || t[i] == '\n' || t[i] == '\r')) ++i;
}

inline string json_parse_string(const string& t, size_t& i) {
    string out;
    ++i;                                        // opening quote
    while (i < t.size() && t[i] != '"') {
        char c = t[i++];
        if (c != '\\') { out += c; continue; }
        if (i >= t.size()) break;
        char e = t[i++];
        switch (e) {
            case 'n': out += '\n'; break;
            case 't': out += '\t'; break;
            case 'r': out += '\r'; break;
            case 'b': out += '\b'; break;
            case 'f': out += '\f'; break;
            case 'u': {
                if (i + 4 <= t.size()) {
                    unsigned v = (unsigned)std::stoul(t.substr(i, 4), nullptr, 16);
                    i += 4;
                    if (v < 0x80) out += (char)v;
                    else if (v < 0x800) { out += (char)(0xC0 | (v >> 6)); out += (char)(0x80 | (v & 0x3F)); }
                    else { out += (char)(0xE0 | (v >> 12)); out += (char)(0x80 | ((v >> 6) & 0x3F));
                           out += (char)(0x80 | (v & 0x3F)); }
                }
                break;
            }
            default: out += e;                   // covers \" \\ \/
        }
    }
    if (i < t.size()) ++i;                       // closing quote
    return out;
}

inline JVal json_parse(const string& t, size_t& i) {
    JVal v;
    json_skip_ws(t, i);
    if (i >= t.size()) return v;
    char c = t[i];
    if (c == '"') { v.kind = JVal::STR; v.str = json_parse_string(t, i); return v; }
    if (c == '[') {
        v.kind = JVal::ARR;
        ++i;
        json_skip_ws(t, i);
        while (i < t.size() && t[i] != ']') {
            v.arr.push_back(json_parse(t, i));
            json_skip_ws(t, i);
            if (i < t.size() && t[i] == ',') { ++i; json_skip_ws(t, i); }
        }
        if (i < t.size()) ++i;
        return v;
    }
    if (c == '{') {
        v.kind = JVal::OBJ;
        ++i;
        json_skip_ws(t, i);
        while (i < t.size() && t[i] != '}') {
            if (t[i] != '"') break;
            string key = json_parse_string(t, i);
            json_skip_ws(t, i);
            if (i < t.size() && t[i] == ':') ++i;
            v.obj[key] = json_parse(t, i);
            json_skip_ws(t, i);
            if (i < t.size() && t[i] == ',') { ++i; json_skip_ws(t, i); }
        }
        if (i < t.size()) ++i;
        return v;
    }
    // number / true / false / null — consumed, unused
    while (i < t.size() && t[i] != ',' && t[i] != '}' && t[i] != ']' &&
           t[i] != ' ' && t[i] != '\n' && t[i] != '\t' && t[i] != '\r') ++i;
    return v;
}

//======================================================================
// compile_commands lookup (mirror sizeprobe.flags_for: upward find; match
// the TU's absolute path; FALLBACK to the first entry)
//======================================================================

struct CompileEntry {
    vector<string> args;   // from "arguments", else "command" split on whitespace (mirror the Lua)
    string directory;
    bool ok = false;
};

inline fs::path find_compile_db(const fs::path& from_dir) {
    std::error_code ec;
    for (fs::path d = from_dir; !d.empty(); d = d.parent_path()) {
        if (fs::exists(d / "compile_commands.json", ec)) return d / "compile_commands.json";
        if (d == d.root_path()) break;
    }
    return {};
}

inline CompileEntry flags_for(const fs::path& tu_abs) {
    CompileEntry out;
    fs::path db_path = find_compile_db(tu_abs.parent_path());
    if (db_path.empty()) return out;
    string text = read_file(db_path);
    size_t i = 0;
    JVal db = json_parse(text, i);
    if (db.kind != JVal::ARR || db.arr.empty()) return out;
    const JVal* entry = nullptr;
    string want = tu_abs.lexically_normal().string();
    for (const JVal& e : db.arr) {
        if (e.kind != JVal::OBJ) continue;
        auto f = e.obj.find("file");
        if (f == e.obj.end() || f->second.kind != JVal::STR) continue;
        fs::path ef = f->second.str;
        if (!ef.is_absolute()) {
            auto d = e.obj.find("directory");
            if (d != e.obj.end() && d->second.kind == JVal::STR) ef = fs::path(d->second.str) / ef;
        }
        if (ef.lexically_normal().string() == want) { entry = &e; break; }
    }
    if (!entry) {
        // RC-B smarter header→TU pick: a HEADER has no DB entry — prefer the main.cpp entry
        // (the engine's canonical whole-program TU: its flags see every subsystem) over a
        // blind first-entry. Falls back to db[0] (the Lua's `entry or db[1]` behavior) when
        // no main.cpp entry exists. No parity impact: exact matches (the parity TU) short-
        // circuit above either way.
        for (const JVal& e : db.arr) {
            if (e.kind != JVal::OBJ) continue;
            auto f = e.obj.find("file");
            if (f != e.obj.end() && f->second.kind == JVal::STR &&
                fs::path(f->second.str).filename() == "main.cpp") { entry = &e; break; }
        }
    }
    if (!entry) entry = &db.arr[0];                        // mirror: entry or db[1]
    auto d = entry->obj.find("directory");
    if (d != entry->obj.end() && d->second.kind == JVal::STR) out.directory = d->second.str;
    auto a = entry->obj.find("arguments");
    if (a != entry->obj.end() && a->second.kind == JVal::ARR) {
        for (const JVal& t : a->second.arr)
            if (t.kind == JVal::STR) out.args.push_back(t.str);
    } else {
        auto c = entry->obj.find("command");
        if (c != entry->obj.end() && c->second.kind == JVal::STR) {
            std::istringstream ss(c->second.str);          // naive %S+ split — mirror the Lua
            string tok;
            while (ss >> tok) out.args.push_back(tok);
        }
    }
    out.ok = !out.args.empty();
    return out;
}

// the clang-portable LAYOUT-flag subset (mirror emit_record_layout.lua: keep -isystem/-include
// (+arg), -I*, -D*, the FIRST -std=; drop codegen flags — layout is ABI-determined; TECH_DEBT-231)
inline vector<string> layout_flag_subset(const vector<string>& args) {
    vector<string> keep;
    bool have_std = false;
    for (size_t i = 1; i < args.size(); ++i) {             // skip argv[0] (the compiler)
        const string& f = args[i];
        if (f == "-isystem" || f == "-include") {
            keep.push_back(f);
            keep.push_back(i + 1 < args.size() ? args[i + 1] : "");
            ++i;
        } else if (starts_with(f, "-I") || starts_with(f, "-D")) {
            keep.push_back(f);
        } else if (starts_with(f, "-std=") && !have_std) {
            keep.push_back(f);
            have_std = true;
        }
    }
    if (!have_std) keep.push_back("-std=gnu++20");
    return keep;
}

//======================================================================
// record-layout dump parse (line-for-line port of recordlayout.parse)
//======================================================================

struct RecField { string name, type; long off = 0; };
struct Record {
    string name;
    long size = -1, align = -1;
    vector<RecField> fields;
};

inline bool layout_noise(const string& name) {
    if (starts_with(name, "std::") || starts_with(name, "__")) return true;
    if (name.size() >= 2 && name[0] == '_' && name[1] >= 'A' && name[1] <= 'Z') return true;
    if (name.find("anonymous") != string::npos || name.find("lambda") != string::npos) return true;
    return false;
}

// "^%s*%d+ | " prefix: returns the position just past "| " (i.e., of the payload) or npos.
inline size_t dump_row_payload(const string& line, long* off_out) {
    size_t i = line.find_first_not_of(" \t");
    if (i == string::npos || line[i] < '0' || line[i] > '9') return string::npos;
    size_t j = i;
    while (j < line.size() && line[j] >= '0' && line[j] <= '9') ++j;
    if (off_out) *off_out = std::stol(line.substr(i, j - i));
    if (j + 1 >= line.size() || line[j] != ' ' || line[j + 1] != '|') return string::npos;
    return j + 2;                                          // index just past '|'
}

inline vector<Record> parse_record_dump(const string& dump) {
    vector<Record> order;
    std::map<string, size_t> seen;                         // name -> index in order (later wins)
    Record cur;
    bool active = false;
    auto flush = [&]() {
        if (active && !cur.name.empty() && cur.size >= 0 && !layout_noise(cur.name)) {
            auto it = seen.find(cur.name);
            if (it != seen.end()) order[it->second] = cur;   // dedup: later, more-complete dump wins
            else { seen[cur.name] = order.size(); order.push_back(cur); }
        }
        cur = Record{};
        active = false;
    };
    for (const string& line : split_lines(dump)) {
        if (line.find("Dumping AST Record Layout") != string::npos) {
            flush();
            active = true;
            continue;
        }
        if (!active) continue;
        long off = 0;
        size_t p = dump_row_payload(line, &off);
        bool named_now = false;
        if (cur.name.empty() && p != string::npos && p < line.size() && line[p] == ' ') {
            // "^%s*%d+ | (%a+) (.+)$" — exactly ONE space after '|', then a letters-only kind
            size_t k = p + 1, e = k;
            while (e < line.size() && ((line[e] >= 'a' && line[e] <= 'z') ||
                                       (line[e] >= 'A' && line[e] <= 'Z'))) ++e;
            string kind = line.substr(k, e - k);
            if ((kind == "struct" || kind == "class" || kind == "union") &&
                e < line.size() && line[e] == ' ' && e + 1 < line.size()) {
                cur.name = strip(line.substr(e + 1));
                named_now = true;
            }
        }
        size_t sz = line.find("[sizeof=");
        if (sz != string::npos) {
            size_t k = sz + 8, e = k;
            while (e < line.size() && line[e] >= '0' && line[e] <= '9') ++e;
            if (e > k) cur.size = std::stol(line.substr(k, e - k));
        }
        if (cur.align < 0) {
            size_t al = line.find(" align=");              // leading space — never matches nvalign
            if (al != string::npos) {
                size_t k = al + 7, e = k;
                while (e < line.size() && line[e] >= '0' && line[e] <= '9') ++e;
                if (e > k) cur.align = std::stol(line.substr(k, e - k));
            }
        }
        if (!named_now && !cur.name.empty() && p != string::npos) {
            // TOP-LEVEL field: '|' + exactly 3 spaces + non-space (deeper nesting has 5+)
            if (p + 3 < line.size() && line[p] == ' ' && line[p + 1] == ' ' && line[p + 2] == ' ' &&
                line[p + 3] != ' ') {
                string decl = line.substr(p + 3);
                while (!decl.empty() && (decl.back() == '\r' || decl.back() == ' ')) decl.pop_back();
                size_t sp = decl.find_last_of(" \t");
                if (sp != string::npos && sp > 0) {
                    string fname = decl.substr(sp + 1);
                    string ftype = strip(decl.substr(0, sp));
                    if (!fname.empty() && !ftype.empty())
                        cur.fields.push_back({fname, ftype, off});
                }
            }
        }
    }
    flush();
    return order;
}

//======================================================================
// field-size resolver + straddlers (line-for-line port)
//======================================================================

inline const std::map<string, long>& prim_sizes() {
    static const std::map<string, long> p = {
        {"bool", 1}, {"_Bool", 1}, {"char", 1}, {"signed char", 1}, {"unsigned char", 1},
        {"int8_t", 1}, {"uint8_t", 1},
        {"short", 2}, {"unsigned short", 2}, {"int16_t", 2}, {"uint16_t", 2}, {"char16_t", 2},
        {"int", 4}, {"unsigned", 4}, {"unsigned int", 4}, {"int32_t", 4}, {"uint32_t", 4},
        {"float", 4}, {"char32_t", 4}, {"wchar_t", 4},
        {"long", 8}, {"unsigned long", 8}, {"long long", 8}, {"unsigned long long", 8},
        {"int64_t", 8}, {"uint64_t", 8}, {"double", 8}, {"size_t", 8}, {"ptrdiff_t", 8},
        {"intptr_t", 8}, {"uintptr_t", 8},
        {"__int128", 16}, {"unsigned __int128", 16}, {"long double", 16},
    };
    return p;
}

inline string replace_all(string s, const string& from, const string& to) {
    size_t p = 0;
    while ((p = s.find(from, p)) != string::npos) { s.replace(p, from.size(), to); p += to.size(); }
    return s;
}

inline string canon_type(const string& t) {
    string s = replace_all(replace_all(replace_all(t, "struct ", ""), "class ", ""), "union ", "");
    string o;
    for (char c : s)
        if (c != ' ' && c != '\t' && c != '\n' && c != '\r') o += c;
    return o;
}

inline string strip_ns(const string& c) {
    // ^([%w_]+::)+  — strip leading ident:: runs
    size_t i = 0;
    while (true) {
        size_t j = i;
        while (j < c.size() && ((c[j] >= 'a' && c[j] <= 'z') || (c[j] >= 'A' && c[j] <= 'Z') ||
                                (c[j] >= '0' && c[j] <= '9') || c[j] == '_')) ++j;
        if (j > i && j + 1 < c.size() && c[j] == ':' && c[j + 1] == ':') i = j + 2;
        else break;
    }
    return c.substr(i);
}

inline long field_size(const string& typ_in, const std::map<string, long>& by_name);

inline long field_size(const string& typ_in, const std::map<string, long>& by_name) {
    string typ = strip(typ_in);
    if (typ.empty()) return -1;
    // array suffix: base + [dims]$ — multiply every numeric [N]
    size_t lb = typ.find('[');
    if (lb != string::npos && typ.back() == ']') {
        string base = typ.substr(0, lb);
        while (!base.empty() && (base.back() == ' ' || base.back() == '\t')) base.pop_back();
        string dims = typ.substr(lb);
        long n = 1;
        size_t p = 0;
        while ((p = dims.find('[', p)) != string::npos) {
            size_t k = p + 1, e = k;
            while (e < dims.size() && dims[e] >= '0' && dims[e] <= '9') ++e;
            if (e > k && e < dims.size() && dims[e] == ']') n *= std::stol(dims.substr(k, e - k));
            p = (e < dims.size()) ? e : p + 1;
        }
        long es = field_size(base, by_name);
        return es >= 0 ? es * n : -1;
    }
    {   // trailing pointer: %*%s*$
        string t = typ;
        while (!t.empty() && (t.back() == ' ' || t.back() == '\t')) t.pop_back();
        if (!t.empty() && t.back() == '*') return 8;
    }
    auto it = prim_sizes().find(typ);
    if (it != prim_sizes().end()) return it->second;
    string c = canon_type(typ);
    auto b = by_name.find(c);
    if (b != by_name.end()) return b->second;
    b = by_name.find(strip_ns(c));
    if (b != by_name.end()) return b->second;
    return -1;
}

struct Straddler { string name; long off, size; };

// map record-name -> straddling fields (only FULLY-resolved records reported — no guessing)
inline std::map<string, vector<Straddler>> straddlers(const vector<Record>& records) {
    std::map<string, long> by;
    for (const Record& r : records)
        if (r.size >= 0) {
            by[canon_type(r.name)] = r.size;
            by[strip_ns(canon_type(r.name))] = r.size;
        }
    std::map<string, vector<Straddler>> out;
    for (const Record& r : records) {
        if (r.fields.empty() || layout_noise(r.name)) continue;
        long unresolved = 0;
        vector<Straddler> hits;
        for (const RecField& f : r.fields) {
            long s = field_size(f.type, by);
            if (s < 0) ++unresolved;
            else if (s > 0 && s <= 64 && (f.off / 64) != ((f.off + s - 1) / 64))
                hits.push_back({f.name, f.off, s});
        }
        if (unresolved == 0 && !hits.empty()) out[r.name] = std::move(hits);
    }
    return out;
}

//======================================================================
// the producer: drive clang on a TU, emit the emit_record_layout.lua JSON shape
//======================================================================

inline string shell_quote(const string& s) {
    string o = "'";
    for (char c : s) { if (c == '\'') o += "'\\''"; else o += c; }
    o += "'";
    return o;
}

inline string run_capture(const string& cmd) {
    string out;
    FILE* p = popen(cmd.c_str(), "r");
    if (!p) return out;
    char buf[8192];
    size_t n;
    while ((n = fread(buf, 1, sizeof buf, p)) > 0) out.append(buf, n);
    pclose(p);
    return out;
}

// Run with stdout and stderr captured SEPARATELY, then concatenated — mirror vim.system.
// NEVER `2>&1`: the streams merge at the PIPE and clang's diagnostics interleave MID-LINE
// with the record dump, splicing text into the middle of digits (the parity gate caught
// `[sizeof=14748In file included from ...` — 147480 corrupted to 14748).
inline string run_capture_split(const string& cmd_no_redirect) {
    fs::path tmp = fs::temp_directory_path() /
                   ("foxtag_stderr_" + std::to_string((long)getpid()) + ".txt");
    string out = run_capture(cmd_no_redirect + " 2>" + shell_quote(tmp.string()));
    out += read_file(tmp);
    std::error_code ec;
    fs::remove(tmp, ec);
    return out;
}

// exit 0 + JSON on stdout; exit 2 + stderr note on failure (RC-E: never an empty success)
inline int cmd_layout(const string& tu, const vector<string>& names) {
    fs::path tu_abs = fs::absolute(tu).lexically_normal();
    CompileEntry ce = flags_for(tu_abs);
    if (!ce.ok) {
        std::fprintf(stderr, "no compile_commands flags for %s\n", tu.c_str());
        return 2;
    }
    vector<string> argv = {"clang++", "-fsyntax-only", "-ferror-limit=0",
                           "-Xclang", "-fdump-record-layouts"};
    for (const string& f : layout_flag_subset(ce.args)) argv.push_back(f);
    argv.push_back(tu_abs.string());                       // ABSOLUTE — cwd is the compile dir

    string cmd;
    if (!ce.directory.empty()) cmd = "cd " + shell_quote(ce.directory) + " && ";
    for (size_t i = 0; i < argv.size(); ++i) cmd += (i ? " " : "") + shell_quote(argv[i]);
    string dump = run_capture_split(cmd);

    vector<Record> records = parse_record_dump(dump);
    if (records.empty()) {
        std::fprintf(stderr, "no record layouts in dump (clang failed?)\n");
        return 2;
    }
    auto strad = straddlers(records);

    // wanted-name match: exact | template-args-stripped | namespace-stripped (mirror the Lua)
    auto wanted = [&](const Record& r) {
        if (names.empty()) return true;
        string base = r.name.substr(0, r.name.find('<'));
        string nons = strip_ns(base);
        for (const string& w : names)
            if (w == r.name || w == base || w == nons) return true;
        return false;
    };

    // deterministic output: records sorted by name
    vector<const Record*> sel;
    for (const Record& r : records)
        if (wanted(r)) sel.push_back(&r);
    std::sort(sel.begin(), sel.end(),
              [](const Record* a, const Record* b) { return a->name < b->name; });

    string j = "{";
    for (size_t i = 0; i < sel.size(); ++i) {
        const Record& r = *sel[i];
        if (i) j += ",";
        j += "\"" + json_escape(r.name) + "\":{\"size\":" + std::to_string(r.size) +
             ",\"align\":" + std::to_string(r.align) + ",\"straddlers\":[";
        auto it = strad.find(r.name);
        if (it != strad.end())
            for (size_t k = 0; k < it->second.size(); ++k) {
                const Straddler& s = it->second[k];
                if (k) j += ",";
                j += "{\"name\":\"" + json_escape(s.name) + "\",\"off\":" + std::to_string(s.off) +
                     ",\"size\":" + std::to_string(s.size) + "}";
            }
        j += "]}";
    }
    j += "}";
    std::printf("%s\n", j.c_str());
    return 0;
}

// per-field layout facts for the register-fit analyzer (RC-F, D-366) — the SAME clang dump as
// `layout`, but exposes EVERY field {name, type, off, size} (size via the shared field_size
// resolver) instead of only the straddlers. A SEPARATE command so `layout`'s parity-gated JSON
// shape is unchanged (parity_check.sh §4 stays valid); the analyzer computes access-cost on top.
inline int cmd_fields(const string& tu, const vector<string>& names) {
    fs::path tu_abs = fs::absolute(tu).lexically_normal();
    CompileEntry ce = flags_for(tu_abs);
    if (!ce.ok) {
        std::fprintf(stderr, "no compile_commands flags for %s\n", tu.c_str());
        return 2;
    }
    vector<string> argv = {"clang++", "-fsyntax-only", "-ferror-limit=0",
                           "-Xclang", "-fdump-record-layouts"};
    for (const string& f : layout_flag_subset(ce.args)) argv.push_back(f);
    argv.push_back(tu_abs.string());
    string cmd;
    if (!ce.directory.empty()) cmd = "cd " + shell_quote(ce.directory) + " && ";
    for (size_t i = 0; i < argv.size(); ++i) cmd += (i ? " " : "") + shell_quote(argv[i]);
    string dump = run_capture_split(cmd);

    vector<Record> records = parse_record_dump(dump);
    if (records.empty()) {
        std::fprintf(stderr, "no record layouts in dump (clang failed?)\n");
        return 2;
    }
    std::map<string, long> by;                             // record-name -> size (mirror straddlers()'s `by`)
    for (const Record& r : records)
        if (r.size >= 0) {
            by[canon_type(r.name)] = r.size;
            by[strip_ns(canon_type(r.name))] = r.size;
        }
    auto wanted = [&](const Record& r) {
        if (names.empty()) return true;
        string base = r.name.substr(0, r.name.find('<'));
        string nons = strip_ns(base);
        for (const string& w : names)
            if (w == r.name || w == base || w == nons) return true;
        return false;
    };
    vector<const Record*> sel;
    for (const Record& r : records)
        if (wanted(r) && !r.fields.empty() && !layout_noise(r.name)) sel.push_back(&r);
    std::sort(sel.begin(), sel.end(),
              [](const Record* a, const Record* b) { return a->name < b->name; });

    string j = "{";
    for (size_t i = 0; i < sel.size(); ++i) {
        const Record& r = *sel[i];
        if (i) j += ",";
        j += "\"" + json_escape(r.name) + "\":{\"size\":" + std::to_string(r.size) +
             ",\"align\":" + std::to_string(r.align) + ",\"fields\":[";
        for (size_t k = 0; k < r.fields.size(); ++k) {
            const RecField& f = r.fields[k];
            if (k) j += ",";
            j += "{\"name\":\"" + json_escape(f.name) + "\",\"type\":\"" + json_escape(f.type) +
                 "\",\"off\":" + std::to_string(f.off) +
                 ",\"size\":" + std::to_string(field_size(f.type, by)) + "}";
        }
        j += "]}";
    }
    j += "}";
    std::printf("%s\n", j.c_str());
    return 0;
}

} // namespace foxtag
