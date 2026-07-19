// foxtag.hpp — the E.1.2.A central tag-toolchain CORE, increment 1 (D-337 / D-349).
//
// ONE parser + scanner + query engine over the locked [SCHEMA]_[v1.0] in-code tag grammar
// (DESIGN_SPECS/doc-disciplines/in-code-documentation-schema.md — the frozen contract),
// consumed by CI (parity-gated migration off the Python tools), the fox-symdeps plugin
// (subprocess + JSON — fills the tagadapter.parse keystone), and the CLI (foxtag_main.cpp).
//
// D-331/D-337: one producer, N consumers — this file is the "one codebase" that kills the
// Python/Lua parser split. MIGRATION CONTRACT: the Python validator (check_code_tag_blocks.py)
// stays the CI authority until `tools/foxtag/parity_check.sh` proves this core produces
// BYTE-IDENTICAL violations + an identical unit/tag inventory on the full tree (golden-master
// discipline; the semantics below deliberately mirror the Python line-for-line).
//
// GRAMMAR IS NEVER HARDCODED (anti-Class-18): the category set + reference-subcats are DERIVED
// at runtime from the schema SSoT fences; [TAG] vocab from doc-tag-vocabulary.md tables —
// exactly as the Python does. Folding a fence row = both tools track it, zero edits here.
// (The OPENERS/UNIT_TYPES node-model sets are the one deliberate mirror of the Python constants
// — the node model is prose in the spec, not fence-encoded; parity_check keeps them honest.)
//
// This is DEV-PLANE tooling (never linked into the engine): std::string/vector etc. are fine
// here — the H1-H3 engine invariants govern the engine hot/slow paths, not this apparatus.

#pragma once

#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>
#include <set>
#include <map>
#include <fstream>
#include <sstream>
#include <algorithm>
#include <filesystem>

namespace foxtag {

namespace fs = std::filesystem;
using std::string;
using std::vector;
using std::set;

//======================================================================
// small helpers
//======================================================================

inline string read_file(const fs::path& p) {
    std::ifstream f(p, std::ios::binary);
    if (!f) return {};
    std::ostringstream ss;
    ss << f.rdbuf();
    return ss.str();
}

inline vector<string> split_lines(const string& text) {
    vector<string> out;
    string cur;
    for (char c : text) {
        if (c == '\n') { out.push_back(cur); cur.clear(); }
        else cur.push_back(c);
    }
    out.push_back(cur);
    return out;
}

inline string strip(const string& s) {
    size_t a = s.find_first_not_of(" \t\r");
    if (a == string::npos) return {};
    size_t b = s.find_last_not_of(" \t\r");
    return s.substr(a, b - a + 1);
}

inline bool starts_with(const string& s, const string& pre) {
    return s.rfind(pre, 0) == 0;
}

inline string lower_hyphen(const string& tok) {
    // mirror _upper_snake_to_vocab: strip().lower().replace('_','-')
    string t = strip(tok);
    for (char& c : t) {
        if (c >= 'A' && c <= 'Z') c = (char)(c - 'A' + 'a');
        else if (c == '_') c = '-';
    }
    return t;
}

// mirror re.fullmatch(r"[A-Z][A-Z_]+", tok) — ≥2 chars, uppercase+underscore, NO digits
inline bool is_category_form(const string& tok) {
    if (tok.size() < 2) return false;
    if (tok[0] < 'A' || tok[0] > 'Z') return false;
    for (size_t i = 1; i < tok.size(); ++i) {
        char c = tok[i];
        if (!((c >= 'A' && c <= 'Z') || c == '_')) return false;
    }
    return true;
}

// innermost-bracket tokens, in order — the ONE parse rule (\[([^\[\]]+)\]), token[0]=CATEGORY.
inline vector<string> line_tokens(const string& payload) {
    vector<string> toks;
    long start = -1;                     // index just past the most recent unmatched '['
    for (size_t i = 0; i < payload.size(); ++i) {
        char c = payload[i];
        if (c == '[') start = (long)i + 1;          // a deeper '[' resets (innermost wins)
        else if (c == ']') {
            if (start >= 0 && (size_t)start <= i) {
                if (i > (size_t)start)               // non-empty per [^\[\]]+ (empty [] no match)
                    toks.push_back(strip(payload.substr(start, i - start)));
                start = -1;
            }
        }
    }
    return toks;
}

// mirror TAG_LINE_RE = ^\s*//\s*(\[.*)$ — returns payload or empty
inline string tag_line_payload(const string& raw) {
    size_t i = raw.find_first_not_of(" \t");
    if (i == string::npos || i + 1 >= raw.size()) return {};
    if (raw[i] != '/' || raw[i + 1] != '/') return {};
    i += 2;
    while (i < raw.size() && (raw[i] == ' ' || raw[i] == '\t')) ++i;
    if (i >= raw.size() || raw[i] != '[') return {};
    string p = raw.substr(i);
    while (!p.empty() && (p.back() == '\r')) p.pop_back();
    return p;
}

// mirror MAJOR_BAR_RE = ^\s*//=+\s*$
inline bool is_major_bar(const string& raw) {
    size_t i = raw.find_first_not_of(" \t");
    if (i == string::npos || i + 1 >= raw.size()) return false;
    if (raw[i] != '/' || raw[i + 1] != '/') return false;
    i += 2;
    size_t eq = 0;
    while (i < raw.size() && raw[i] == '=') { ++i; ++eq; }
    if (eq == 0) return false;
    while (i < raw.size()) {
        if (raw[i] != ' ' && raw[i] != '\t' && raw[i] != '\r') return false;
        ++i;
    }
    return true;
}

// mirror _BLOCK_ITEM_RE = ^\s*//\s*-\s*\[
inline bool is_block_item(const string& raw) {
    size_t i = raw.find_first_not_of(" \t");
    if (i == string::npos || i + 1 >= raw.size()) return false;
    if (raw[i] != '/' || raw[i + 1] != '/') return false;
    i += 2;
    while (i < raw.size() && (raw[i] == ' ' || raw[i] == '\t')) ++i;
    if (i >= raw.size() || raw[i] != '-') return false;
    ++i;
    while (i < raw.size() && (raw[i] == ' ' || raw[i] == '\t')) ++i;
    return i < raw.size() && raw[i] == '[';
}

inline long first_int(const string& s) {
    for (size_t i = 0; i < s.size(); ++i)
        if (s[i] >= '0' && s[i] <= '9') {
            size_t j = i;
            while (j < s.size() && s[j] >= '0' && s[j] <= '9') ++j;
            return std::stol(s.substr(i, j - i));
        }
    return -1;
}

//======================================================================
// roots (mirror check_doc_metadata's machine-portable resolvers, incl.
// the Landmine-5 Version.hpp shape check)
//======================================================================

struct Roots {
    fs::path engine, workspace, memory_dir;   // memory_dir may be empty (absent)
    bool ok = false;
    string err;
};

inline bool engine_shaped(const fs::path& p) {
    std::error_code ec;
    return fs::is_regular_file(p / "Version.hpp", ec);
}

inline Roots resolve_roots() {
    Roots r;
    // ENGINE: env -> cwd shape-check -> cwd-sibling (workspace cwd) shape-check
    if (const char* e = std::getenv("FOXML_ENGINE"); e && *e && engine_shaped(e)) {
        r.engine = fs::path(e);
    } else {
        fs::path cwd = fs::current_path();
        if (engine_shaped(cwd)) r.engine = cwd;
        else if (engine_shaped(cwd.parent_path() / "FoxML_Trader_v2"))
            r.engine = cwd.parent_path() / "FoxML_Trader_v2";
        else { r.err = "cannot resolve the engine root (no Version.hpp at cwd/sibling; set FOXML_ENGINE)"; return r; }
    }
    // WORKSPACE: env -> sibling -> engine (mirror _resolve_workspace_root)
    if (const char* w = std::getenv("FOXML_WORKSPACE"); w && *w && fs::exists(w)) {
        r.workspace = fs::path(w);
    } else {
        fs::path sib = r.engine.parent_path() / "tick-trader-percore-workspace";
        r.workspace = fs::exists(sib) ? sib : r.engine;
    }
    // MEMORY: env -> ~/.claude/projects/<engine path, '/'+'_' -> '-'>/memory (mirror _resolve_memory_dir)
    if (const char* m = std::getenv("FOXML_MEMORY_DIR"); m && *m) {
        if (fs::exists(m)) r.memory_dir = fs::path(m);
    } else if (const char* home = std::getenv("HOME"); home && *home) {
        string pid = r.engine.string();
        for (char& c : pid) if (c == '/' || c == '_') c = '-';
        fs::path p = fs::path(home) / ".claude" / "projects" / pid / "memory";
        if (fs::exists(p)) r.memory_dir = p;
    }
    r.ok = true;
    return r;
}

//======================================================================
// grammar (derived at runtime from the SSoT fences + vocab tables)
//======================================================================

struct Grammar {
    set<string> categories;        // ```category-set``` fence
    set<string> ref_subcats;       // ```reference-subcats``` fence (col 1)
    set<string> concern, surface;  // doc-tag-vocabulary.md tables
    bool ok = false;
    string err;
};

// FULL-block unit types (locked v1.0 node model, D-339/D-340/D-346) — deliberate mirror of the
// Python OPENERS (the node model is spec PROSE, not fence-encoded); parity_check keeps it honest.
inline const set<string>& openers() {
    static const set<string> s = {"FUNCTION", "STRUCT", "REGISTRY", "ENUM", "TYPE", "STRATEGY", "CODE"};
    return s;
}
inline const set<string>& unit_types() {
    static const set<string> s = {"FILE", "STRUCT", "FUNCTION", "REGISTRY", "ENUM", "TYPE",
                                  "MACRO", "TEST", "STRATEGY", "ASSERT"};
    return s;
}

inline set<string> parse_fence_tokens(const string& text, const string& fence_name) {
    set<string> out;
    string open = "```" + fence_name + "\n";
    size_t a = text.find(open);
    if (a == string::npos) return out;
    a += open.size();
    size_t b = text.find("\n```", a);
    if (b == string::npos) return out;
    for (const string& row : split_lines(text.substr(a, b - a))) {
        string body = row.substr(0, row.find('#'));      // strip #-comments
        std::istringstream ss(body);
        string tok;
        bool first = true;
        while (ss >> tok) {
            // category-set: every token; reference-subcats: col 1 only
            if (fence_name == "reference-subcats" && !first) break;
            first = false;
            // mirror fullmatch [A-Z][A-Z_]* (1+ chars here, per the Python fence loaders)
            bool okt = !tok.empty() && tok[0] >= 'A' && tok[0] <= 'Z';
            for (size_t i = 1; okt && i < tok.size(); ++i)
                okt = (tok[i] >= 'A' && tok[i] <= 'Z') || tok[i] == '_';
            if (okt) out.insert(tok);
        }
    }
    return out;
}

inline Grammar load_grammar(const Roots& roots) {
    Grammar g;
    string schema = read_file(roots.workspace / "DESIGN_SPECS" / "doc-disciplines" /
                              "in-code-documentation-schema.md");
    if (schema.empty()) { g.err = "schema SSoT unreadable"; return g; }
    g.categories  = parse_fence_tokens(schema, "category-set");
    g.ref_subcats = parse_fence_tokens(schema, "reference-subcats");
    if (g.categories.empty() || g.ref_subcats.empty()) { g.err = "SSoT fences unloadable"; return g; }

    // vocab tables (mirror load_vocabulary: `| `tag` |` rows inside the two axis sections)
    string vocab = read_file(roots.workspace / "DESIGN_SPECS" / "meta-disciplines" /
                             "doc-tag-vocabulary.md");
    if (vocab.empty()) { g.err = "doc-tag-vocabulary unreadable"; return g; }
    int section = 0;   // 0=none 1=concern 2=surface
    for (const string& line : split_lines(vocab)) {
        if (line.find("## CONCERN axis") != string::npos) { section = 1; continue; }
        if (line.find("## SURFACE axis") != string::npos) { section = 2; continue; }
        if (starts_with(line, "## ") && section) { section = 0; continue; }
        if (!section || line.empty() || line[0] != '|') continue;
        size_t i = 1;
        while (i < line.size() && (line[i] == ' ' || line[i] == '\t')) ++i;
        if (i >= line.size() || line[i] != '`') continue;
        size_t j = ++i;
        while (j < line.size() && ((line[j] >= 'a' && line[j] <= 'z') ||
                                   (line[j] >= '0' && line[j] <= '9') || line[j] == '-')) ++j;
        if (j == i || j >= line.size() || line[j] != '`') continue;
        (section == 1 ? g.concern : g.surface).insert(line.substr(i, j - i));
    }
    if (g.concern.empty()) { g.err = "vocab tables unloadable"; return g; }
    g.ok = true;
    return g;
}

//======================================================================
// reference index (mirror load_reference_index — frozen workspace paths)
//======================================================================

struct RefIndex {
    // present = has a membership set; absent from `sets` = existence-unchecked (never red)
    std::map<string, set<string>> str_sets;   // INVARIANT, DECISION, DESIGN_SPEC, MEMORY, PLAN (stems)
    std::map<string, set<long>>   int_sets;   // TECH_DEBT, CLASS, PARITY
    fs::path plans_dir, workspace;
    bool has(const string& subcat) const {
        return str_sets.count(subcat) || int_sets.count(subcat);
    }
};

inline void collect_stems(const fs::path& dir, bool recursive, set<string>& out) {
    std::error_code ec;
    if (!fs::is_directory(dir, ec)) return;
    if (recursive) {
        for (auto it = fs::recursive_directory_iterator(dir, fs::directory_options::skip_permission_denied, ec);
             it != fs::recursive_directory_iterator(); it.increment(ec)) {
            if (ec) break;
            if (it->is_regular_file(ec) && it->path().extension() == ".md")
                out.insert(it->path().stem().string());
        }
    } else {
        for (auto& e : fs::directory_iterator(dir, ec))
            if (e.path().extension() == ".md") out.insert(e.path().stem().string());
    }
}

inline RefIndex load_ref_index(const Roots& roots) {
    RefIndex idx;
    idx.plans_dir = roots.workspace / "plans";
    idx.workspace = roots.workspace;

    // INVARIANT — CLAUDE.md Hard-Invariants rows: ^\|\s*\*{0,2}(H\d+)
    {
        set<string> hs;
        for (const string& line : split_lines(read_file(roots.engine / "CLAUDE.md"))) {
            if (line.empty() || line[0] != '|') continue;
            size_t i = 1;
            while (i < line.size() && (line[i] == ' ' || line[i] == '\t')) ++i;
            size_t stars = 0;
            while (i < line.size() && line[i] == '*' && stars < 2) { ++i; ++stars; }
            if (i >= line.size() || line[i] != 'H') continue;
            size_t j = i + 1;
            while (j < line.size() && line[j] >= '0' && line[j] <= '9') ++j;
            if (j > i + 1) hs.insert(line.substr(i, j - i));
        }
        if (!hs.empty()) idx.str_sets["INVARIANT"] = std::move(hs);
    }
    // DECISION — union of plans/*/decision-logs/*.md sentinels: <!-- [DCF/]+ : ([DCF]-\d+) -->
    {
        set<string> ds;
        std::error_code ec;
        for (auto& sprint : fs::directory_iterator(idx.plans_dir, ec)) {
            fs::path dl = sprint.path() / "decision-logs";
            if (!fs::is_directory(dl, ec)) continue;
            for (auto& f : fs::directory_iterator(dl, ec)) {
                if (f.path().extension() != ".md") continue;
                string t = read_file(f.path());
                size_t pos = 0;
                while ((pos = t.find("<!--", pos)) != string::npos) {
                    size_t p = pos + 4;
                    while (p < t.size() && (t[p] == ' ' || t[p] == '\t')) ++p;
                    size_t k = p;
                    while (k < t.size() && (t[k] == 'D' || t[k] == 'C' || t[k] == 'F' || t[k] == '/')) ++k;
                    if (k == p) { pos += 4; continue; }
                    while (k < t.size() && (t[k] == ' ' || t[k] == '\t')) ++k;
                    if (k >= t.size() || t[k] != ':') { pos += 4; continue; }
                    ++k;
                    while (k < t.size() && (t[k] == ' ' || t[k] == '\t')) ++k;
                    if (k < t.size() && (t[k] == 'D' || t[k] == 'C' || t[k] == 'F') &&
                        k + 1 < t.size() && t[k + 1] == '-') {
                        size_t m = k + 2;
                        while (m < t.size() && t[m] >= '0' && t[m] <= '9') ++m;
                        if (m > k + 2) ds.insert(t.substr(k, m - k));
                    }
                    pos = k;
                }
            }
        }
        if (!ds.empty()) idx.str_sets["DECISION"] = std::move(ds);
    }
    // DESIGN_SPEC / MEMORY / PLAN — stems
    {
        set<string> s;
        collect_stems(roots.workspace / "DESIGN_SPECS", true, s);
        if (!s.empty()) idx.str_sets["DESIGN_SPEC"] = std::move(s);
    }
    if (!roots.memory_dir.empty()) {
        set<string> s;
        collect_stems(roots.memory_dir, false, s);
        if (!s.empty()) idx.str_sets["MEMORY"] = std::move(s);
    }
    {
        set<string> s;
        collect_stems(idx.plans_dir, true, s);
        if (!s.empty()) idx.str_sets["PLAN"] = std::move(s);
    }
    // TECH_DEBT — DOCS/TECH_DEBT.md + DOCS/tech-debt/*.md: TECH_DEBT-(\d+)
    {
        set<long> td;
        vector<fs::path> files = {roots.workspace / "DOCS" / "TECH_DEBT.md"};
        std::error_code ec;
        vector<fs::path> split;
        if (fs::is_directory(roots.workspace / "DOCS" / "tech-debt", ec))
            for (auto& e : fs::directory_iterator(roots.workspace / "DOCS" / "tech-debt", ec))
                if (e.path().extension() == ".md") split.push_back(e.path());
        std::sort(split.begin(), split.end());
        files.insert(files.end(), split.begin(), split.end());
        for (auto& f : files) {
            string t = read_file(f);
            size_t pos = 0;
            while ((pos = t.find("TECH_DEBT-", pos)) != string::npos) {
                size_t k = pos + 10, m = k;
                while (m < t.size() && t[m] >= '0' && t[m] <= '9') ++m;
                if (m > k) td.insert(std::stol(t.substr(k, m - k)));
                pos = m;
            }
        }
        if (!td.empty()) idx.int_sets["TECH_DEBT"] = std::move(td);
    }
    // CLASS — RECURRING_BUG_PATTERNS.md: \bClass 0*(\d+)\b
    {
        set<long> cs;
        string t = read_file(roots.workspace / "DOCS" / "RECURRING_BUG_PATTERNS.md");
        size_t pos = 0;
        while ((pos = t.find("Class ", pos)) != string::npos) {
            bool bound = pos == 0 || !(isalnum((unsigned char)t[pos - 1]) || t[pos - 1] == '_');
            size_t k = pos + 6;
            while (k < t.size() && t[k] == '0') ++k;
            size_t m = k;
            while (m < t.size() && t[m] >= '0' && t[m] <= '9') ++m;
            bool tail = m >= t.size() || !(isalnum((unsigned char)t[m]) || t[m] == '_');
            if (bound && tail) {
                if (m > k) cs.insert(std::stol(t.substr(k, m - k)));
                else if (k > pos + 6) cs.insert(0);          // "Class 000" edge — mirror 0* + \d+ needs ≥1 digit total
            }
            pos = pos + 6;
        }
        // + the per-class subfiles (recurring-bug-patterns/class-NN-*.md, file-size-split Stage-3):
        // a subfile-only class (e.g. 23) is NEVER spelled "Class N" inline in the main doc, so glob the
        // subfile numbers too — else corpus-wide false-dangling (mirrors check_code_tag_blocks.py's
        // CLASS_SUBFILE_DIR union; foxtag<->Python CLASS-resolution parity).
        std::error_code cec;
        for (auto& e : fs::directory_iterator(roots.workspace / "DOCS" / "recurring-bug-patterns", cec)) {
            string fn = e.path().filename().string();
            if (fn.compare(0, 6, "class-") != 0) continue;
            size_t k = 6, m = k;
            while (m < fn.size() && fn[m] >= '0' && fn[m] <= '9') ++m;
            if (m > k) cs.insert(std::stol(fn.substr(k, m - k)));
        }
        if (!cs.empty()) idx.int_sets["CLASS"] = std::move(cs);
    }
    // PARITY — DOCS/PARITY_ISSUES.md: ^id:\s*PARITY-(\d+)
    {
        set<long> ps;
        for (const string& line : split_lines(read_file(roots.workspace / "DOCS" / "PARITY_ISSUES.md"))) {
            if (!starts_with(line, "id:")) continue;
            size_t i = 3;
            while (i < line.size() && (line[i] == ' ' || line[i] == '\t')) ++i;
            if (line.compare(i, 7, "PARITY-") != 0) continue;
            size_t k = i + 7, m = k;
            while (m < line.size() && line[m] >= '0' && line[m] <= '9') ++m;
            if (m > k) ps.insert(std::stol(line.substr(k, m - k)));
        }
        if (!ps.empty()) idx.int_sets["PARITY"] = std::move(ps);
    }
    return idx;
}

// mirror REF_MUST_POPULATE — a vacuous member set = a broken source path; refuse to scan
inline vector<string> ref_index_vacuous(const RefIndex& idx) {
    vector<string> v;
    for (const char* k : {"DESIGN_SPEC", "MEMORY", "DECISION", "INVARIANT", "TECH_DEBT", "CLASS",
                          "PLAN", "PARITY"})
        if (!idx.has(k)) v.push_back(k);
    return v;
}

inline bool ref_resolves(const RefIndex& idx, const string& subcat, const string& rid_in) {
    string rid = strip(rid_in);
    if (subcat == "INVARIANT" || subcat == "DECISION")
        return idx.str_sets.at(subcat).count(rid) > 0;
    if (subcat == "DESIGN_SPEC" || subcat == "MEMORY") {
        string stem = rid;
        if (stem.size() > 3 && stem.compare(stem.size() - 3, 3, ".md") == 0)
            stem.resize(stem.size() - 3);
        return idx.str_sets.at(subcat).count(stem) > 0;
    }
    if (subcat == "TECH_DEBT" || subcat == "CLASS" || subcat == "PARITY") {
        long n = first_int(rid);
        return n >= 0 && idx.int_sets.at(subcat).count(n) > 0;
    }
    if (subcat == "PLAN") {
        if (rid.find('/') != string::npos) {
            std::error_code ec;
            return fs::exists(idx.plans_dir / rid, ec) || fs::exists(idx.workspace / rid, ec);
        }
        string stem = rid;
        if (stem.size() > 3 && stem.compare(stem.size() - 3, 3, ".md") == 0)
            stem.resize(stem.size() - 3);
        return idx.str_sets.at("PLAN").count(stem) > 0;
    }
    return true;
}

//======================================================================
// parse model + per-file walk (mirror validate_file + collect_file_tags
// + resolve_references — same three semantics, same violation strings)
//======================================================================

struct Unit {
    string type, name;
    int open_line = 0;
    int close_line = 0;        // 0 = LIGHT / orient-only / unclosed (FILE, MACRO, TEST, ASSERT)
    vector<string> tags;       // [TAG] values attributed to this unit (innermost open at the line)
};

struct FileResult {
    string path;
    bool converted = false;    // passed the [SCHEMA] whitelist gate
    int blocks = 0;            // named FULL-block openers (mirror blocks_seen)
    vector<Unit> units;        // every named UNIT_TYPES header (incl FILE/MACRO/TEST/ASSERT)
    vector<string> file_tags;  // sorted unique [TAG] values (mirror collect_file_tags)
    vector<string> violations; // BYTE-IDENTICAL to the Python validator's strings
};

inline FileResult parse_file(const string& path_str, const Grammar& g, const RefIndex& ref_idx) {
    FileResult r;
    r.path = path_str;
    string text = read_file(path_str);
    if (text.empty()) {
        // unreadable vs empty: mirror Python (unreadable -> "UNREADABLE: <path>"; empty text
        // fails the gate below either way). fs check distinguishes.
        std::error_code ec;
        if (!fs::exists(path_str, ec)) return r;               // caller skips missing (mirror)
    }
    if (text.find("[SCHEMA]_[") == string::npos || text.find("[SCHEMA]_[exempt") != string::npos)
        return r;                                              // un-converted / exempt: not policed
    r.converted = true;

    vector<string> lines = split_lines(text);

    // ---- pass 1: block parse (prose-state honored) — units / tags / structural violations ----
    struct Open { string cat, name; int line; size_t unit_idx; };
    vector<Open> stack;
    set<string> tags_set;
    bool in_prose = false;
    for (size_t li = 0; li < lines.size(); ++li) {
        const string& raw = lines[li];
        int lineno = (int)li + 1;
        if (in_prose) {
            if (is_major_bar(raw)) in_prose = false;
            continue;
        }
        string payload = tag_line_payload(raw);
        if (payload.empty()) continue;
        vector<string> toks = line_tokens(payload);
        if (toks.empty()) continue;
        const string& cat = toks[0];
        bool is_end = starts_with(cat, "END_");

        if (!is_end && !g.categories.count(cat)) {
            if (is_category_form(cat))
                r.violations.push_back(r.path + ":" + std::to_string(lineno) +
                                       "  UNKNOWN category [" + cat + "]");
            continue;
        }
        for (size_t t = 1; t < toks.size(); ++t) {
            if (g.categories.count(toks[t]) && !starts_with(toks[t], "END_")) {
                r.violations.push_back(r.path + ":" + std::to_string(lineno) +
                                       "  TWO categories on one line ([" + cat + "] + [" + toks[t] +
                                       "]) — split them");
                break;
            }
        }
        // unit inventory (mirror collect_file_tags: named UNIT_TYPES headers)
        size_t unit_idx = (size_t)-1;
        if (unit_types().count(cat) && toks.size() > 1 && !toks[1].empty()) {
            Unit u;
            u.type = cat;
            u.name = toks[1];
            u.open_line = lineno;
            r.units.push_back(u);
            unit_idx = r.units.size() - 1;
        }
        // closers (mirror OPENERS bookkeeping)
        if (openers().count(cat) && (cat == "CODE" || (toks.size() > 1 && !toks[1].empty()))) {
            string name = toks.size() > 1 ? toks[1] : "";
            stack.push_back({cat, name, lineno, unit_idx});
            if (cat != "CODE") r.blocks++;
        } else if (is_end) {
            string end_cat = cat.substr(4);
            string name = toks.size() > 1 ? toks[1] : "";
            if (stack.empty()) {
                r.violations.push_back(r.path + ":" + std::to_string(lineno) + "  [" + cat +
                                       "] with no open [" + end_cat + "]");
            } else {
                const Open& top = stack.back();
                if (top.cat != end_cat)
                    r.violations.push_back(r.path + ":" + std::to_string(lineno) + "  [" + cat +
                                           "] closes [" + end_cat + "] but innermost open is [" +
                                           top.cat + "]");
                else if (top.name != name)
                    r.violations.push_back(r.path + ":" + std::to_string(lineno) + "  [" + cat +
                                           "]_[" + name + "] name mismatch — open was [" + top.cat +
                                           "]_[" + top.name + "]");
                else {
                    if (top.unit_idx != (size_t)-1) r.units[top.unit_idx].close_line = lineno;
                    stack.pop_back();
                }
            }
        }
        // [TAG] vocab (mirror: every value resolves in concern OR surface)
        if (cat == "TAG" && (!g.concern.empty() || !g.surface.empty())) {
            for (size_t t = 1; t < toks.size(); ++t) {
                string v = lower_hyphen(toks[t]);
                if (!v.empty() && !g.concern.count(v) && !g.surface.count(v))
                    r.violations.push_back(r.path + ":" + std::to_string(lineno) + "  [TAG] value [" +
                                           toks[t] + "] not in doc-tag-vocabulary");
                if (!strip(toks[t]).empty()) {
                    tags_set.insert(strip(toks[t]));
                    // attribute to the innermost open named unit, if any
                    for (auto it = stack.rbegin(); it != stack.rend(); ++it)
                        if (it->unit_idx != (size_t)-1) {
                            r.units[it->unit_idx].tags.push_back(strip(toks[t]));
                            break;
                        }
                }
            }
        }
        if (cat == "COMMENT" || cat == "DIAGRAM") in_prose = true;
    }
    for (const Open& o : stack)
        r.violations.push_back(r.path + ":" + std::to_string(o.line) + "  [" + o.cat + "]_[" +
                               o.name + "] has no matching [END_" + o.cat + "]");

    // ---- pass 2: [REFERENCE]-resolution (prose-state deliberately IGNORED — D-317) ----
    for (size_t li = 0; li < lines.size(); ++li) {
        const string& raw = lines[li];
        int lineno = (int)li + 1;
        if (raw.find("//") == string::npos) continue;
        vector<string> toks = line_tokens(raw);   // NOTE: the RAW line, mirror the Python
        if (toks.empty()) continue;
        string subcat;
        size_t ids_from = 0;
        if (toks[0] == "REFERENCE" || toks[0] == "FUTURE_WORK") {
            if (toks.size() < 3) continue;
            subcat = toks[1];
            ids_from = 2;
        } else if (g.ref_subcats.count(toks[0]) && is_block_item(raw)) {
            subcat = toks[0];
            ids_from = 1;
        } else continue;
        if (subcat == "AUDIT") continue;
        if (!g.ref_subcats.count(subcat)) {
            r.violations.push_back(r.path + ":" + std::to_string(lineno) +
                                   "  UNKNOWN [REFERENCE] subcat [" + subcat + "]");
            continue;
        }
        if (!ref_idx.has(subcat)) continue;        // existence-unchecked (SOURCE/URL/unavailable)
        for (size_t t = ids_from; t < toks.size(); ++t) {
            if (!ref_resolves(ref_idx, subcat, toks[t])) {
                string low = subcat;
                for (char& c : low) { if (c >= 'A' && c <= 'Z') c = (char)(c - 'A' + 'a'); if (c == '_') c = '-'; }
                r.violations.push_back(r.path + ":" + std::to_string(lineno) + "  dangling [" +
                                       subcat + "]_[" + strip(toks[t]) + "] — no such " + low);
            }
        }
    }

    r.file_tags.assign(tags_set.begin(), tags_set.end());
    return r;
}

//======================================================================
// scan (mirror engine_source_files: rglob hpp+cpp, exclude vendor/build*
// path parts, NO dir-symlink descent, PLUS the schema_golden fixture dir)
//======================================================================

inline bool excluded_part(const fs::path& p) {
    for (const auto& part : p)
        if (part.string() == "vendor" || starts_with(part.string(), "build")) return true;
    return false;
}

inline vector<string> scan_files(const Roots& roots) {
    vector<string> hpp, cpp;
    std::error_code ec;
    for (auto it = fs::recursive_directory_iterator(
             roots.engine, fs::directory_options::skip_permission_denied, ec);
         it != fs::recursive_directory_iterator(); it.increment(ec)) {
        if (ec) break;
        if (!it->is_regular_file(ec)) continue;
        const fs::path& p = it->path();
        string ext = p.extension().string();
        if (ext != ".hpp" && ext != ".cpp") continue;
        if (excluded_part(p)) continue;
        (ext == ".hpp" ? hpp : cpp).push_back(p.string());
    }
    std::sort(hpp.begin(), hpp.end());
    std::sort(cpp.begin(), cpp.end());
    vector<string> files = hpp;
    files.insert(files.end(), cpp.begin(), cpp.end());
    fs::path golden = roots.workspace / "tests" / "schema_golden";
    vector<string> gf;
    if (fs::is_directory(golden, ec))
        for (auto& e : fs::directory_iterator(golden, ec)) {
            string ext = e.path().extension().string();
            if (ext == ".hpp" || ext == ".cpp") gf.push_back(e.path().string());
        }
    std::sort(gf.begin(), gf.end());
    files.insert(files.end(), gf.begin(), gf.end());
    return files;
}

//======================================================================
// JSON emit (minimal, escaped)
//======================================================================

inline string json_escape(const string& s) {
    string o;
    o.reserve(s.size() + 8);
    for (unsigned char c : s) {
        switch (c) {
            case '"':  o += "\\\""; break;
            case '\\': o += "\\\\"; break;
            case '\n': o += "\\n";  break;
            case '\t': o += "\\t";  break;
            case '\r': o += "\\r";  break;
            default:
                if (c < 0x20) { char buf[8]; std::snprintf(buf, sizeof buf, "\\u%04x", c); o += buf; }
                else o += (char)c;
        }
    }
    return o;
}

inline string unit_json(const string& path, const Unit& u) {
    string j = "{\"file\":\"" + json_escape(path) + "\",\"type\":\"" + json_escape(u.type) +
               "\",\"name\":\"" + json_escape(u.name) + "\",\"open_line\":" +
               std::to_string(u.open_line) + ",\"close_line\":" + std::to_string(u.close_line) +
               ",\"tags\":[";
    for (size_t i = 0; i < u.tags.size(); ++i)
        j += (i ? ",\"" : "\"") + json_escape(u.tags[i]) + "\"";
    j += "]}";
    return j;
}

} // namespace foxtag
