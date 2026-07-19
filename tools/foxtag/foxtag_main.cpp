// foxtag_main.cpp — CLI for the E.1.2.A tag-toolchain core (D-337 increment 1; see foxtag.hpp).
//
//   foxtag validate [paths...]     mirror of check_code_tag_blocks.py (byte-identical violations;
//                                  exit 0 clean / 1 violations / 2 grammar-or-vacuity error)
//   foxtag units [--json]          unit inventory over the scan set (or explicit paths)
//          [--type T] [--tag TAG] [--name N] [paths...]
//   foxtag unit <file> <line>      innermost enclosing unit at a line, as JSON — the plugin
//                                  keystone query (tagadapter.parse via subprocess)
//   foxtag tags [paths...]         per-file [TAG] inventory
//   foxtag grammar                 loaded grammar counts (SSoT-derived — sanity/parity)
//   foxtag parity-dump             sorted U|/T| lines for parity_check.sh vs the Python collector
//   foxtag layout <tu> [Name...]   LAYOUT fact-producer (clang record-layout dump -> JSON;
//                                  same shape as emit_record_layout.lua — increment 2a)
//   foxtag codegen --header H [--header H2...] --params 'SIG' --call 'EXPR'
//          [--flags 'F1 F2...'] [--prelude 'CODE']
//                                  CODEGEN fact-producer (g++ probe + objdump -> JSON; the
//                                  RC-A instantiation anchor / RC-C width-class / RC-E
//                                  never-green — increment 2b)
//   foxtag codegen-selftest        known-shape probe teeth (branchless/loop/float/AVX/vacuous)
//   foxtag selftest                embedded structural teeth (RED cases must red)

#include "foxtag.hpp"
#include "foxtag_layout.hpp"
#include "foxtag_codegen.hpp"

#include <cstring>

using namespace foxtag;

static int cmd_validate(const Grammar& g, const RefIndex& idx, const Roots& roots,
                        const vector<string>& paths) {
    vector<string> files = paths.empty() ? scan_files(roots) : paths;
    vector<string> all_v;
    long blocks = 0, checked = 0;
    for (const string& f : files) {
        std::error_code ec;
        if (!fs::exists(f, ec)) continue;
        ++checked;
        FileResult r = parse_file(f, g, idx);
        blocks += r.blocks;
        all_v.insert(all_v.end(), r.violations.begin(), r.violations.end());
    }
    std::printf("Scanned %ld files; %ld tag-blocks; %zu concern + %zu surface tags\n",
                checked, blocks, g.concern.size(), g.surface.size());
    if (!all_v.empty()) {
        std::printf("\nVIOLATIONS (%zu):\n", all_v.size());
        for (size_t i = 0; i < all_v.size() && i < 50; ++i) std::printf("  %s\n", all_v[i].c_str());
        if (all_v.size() > 50) std::printf("  ... and %zu more\n", all_v.size() - 50);
        return 1;
    }
    std::printf("\nAll tag-blocks valid (or none present — mixed-state is fine).\n");
    return 0;
}

static int cmd_units(const Grammar& g, const RefIndex& idx, const Roots& roots,
                     const vector<string>& paths, bool json,
                     const string& f_type, const string& f_tag, const string& f_name) {
    vector<string> files = paths.empty() ? scan_files(roots) : paths;
    long n = 0;
    for (const string& f : files) {
        FileResult r = parse_file(f, g, idx);
        for (const Unit& u : r.units) {
            if (!f_type.empty() && u.type != f_type) continue;
            if (!f_name.empty() && u.name != f_name) continue;
            if (!f_tag.empty()) {
                bool hit = false;
                for (const string& t : u.tags) if (t == f_tag) { hit = true; break; }
                for (const string& t : r.file_tags) if (t == f_tag) { hit = true; break; }
                if (!hit) continue;
            }
            ++n;
            if (json) std::printf("%s\n", unit_json(r.path, u).c_str());
            else std::printf("%-10s %-40s %s:%d%s\n", u.type.c_str(), u.name.c_str(),
                             r.path.c_str(), u.open_line,
                             u.close_line ? ("-" + std::to_string(u.close_line)).c_str() : "");
        }
    }
    if (!json) std::printf("(%ld unit%s)\n", n, n == 1 ? "" : "s");
    return 0;
}

static int cmd_unit_at(const Grammar& g, const RefIndex& idx, const string& file, int line) {
    FileResult r = parse_file(file, g, idx);
    // innermost CLOSED unit whose [open_line, close_line] contains `line`;
    // fallback: the file's orient-only [FILE] unit (covers the whole file).
    const Unit* best = nullptr;
    const Unit* file_unit = nullptr;
    for (const Unit& u : r.units) {
        if (u.type == "FILE") { file_unit = &u; continue; }
        if (u.close_line && u.open_line <= line && line <= u.close_line)
            if (!best || u.open_line > best->open_line) best = &u;   // latest-opening = innermost
    }
    if (!best) best = file_unit;
    if (!best) { std::printf("null\n"); return 1; }
    std::printf("%s\n", unit_json(r.path, *best).c_str());
    return 0;
}

static int cmd_tags(const Grammar& g, const RefIndex& idx, const Roots& roots,
                    const vector<string>& paths) {
    vector<string> files = paths.empty() ? scan_files(roots) : paths;
    for (const string& f : files) {
        FileResult r = parse_file(f, g, idx);
        if (!r.converted || r.file_tags.empty()) continue;
        std::printf("%s:", r.path.c_str());
        for (const string& t : r.file_tags) std::printf(" [%s]", t.c_str());
        std::printf("\n");
    }
    return 0;
}

static int cmd_parity_dump(const Grammar& g, const RefIndex& idx, const Roots& roots) {
    // sorted "U|file|TYPE|name|line" + "T|file|tag" — must equal the Python collector's dump
    vector<string> rows;
    for (const string& f : scan_files(roots)) {
        FileResult r = parse_file(f, g, idx);
        for (const Unit& u : r.units)
            rows.push_back("U|" + r.path + "|" + u.type + "|" + u.name + "|" +
                           std::to_string(u.open_line));
        for (const string& t : r.file_tags) rows.push_back("T|" + r.path + "|" + t);
    }
    std::sort(rows.begin(), rows.end());
    for (const string& s : rows) std::printf("%s\n", s.c_str());
    return 0;
}

// trim ALL surrounding whitespace incl. '\n' (foxtag's strip() intentionally keeps '\n' for the
// single-line tag parser; file contents like TOOLCHAIN_VERSION / .git/HEAD carry a trailing newline).
static string trim_all(const string& s) {
    size_t a = s.find_first_not_of(" \t\r\n");
    if (a == string::npos) return {};
    return s.substr(a, s.find_last_not_of(" \t\r\n") - a + 1);
}

// resolve the engine repo HEAD via a .git/HEAD read (no `git` subprocess); "" if unresolvable
// (packed-refs) — staleness metadata only, excluded from the by-members parity.
static string git_head_of(const Roots& roots) {
    string head = trim_all(read_file(roots.engine / ".git" / "HEAD"));
    if (starts_with(head, "ref:")) {
        string ref = trim_all(head.substr(4));
        return trim_all(read_file(roots.engine / ".git" / ref));
    }
    return head;                                               // detached HEAD = the SHA directly
}

static int cmd_grammar(const Grammar& g, const Roots& roots, bool json) {
    if (!json) {
        std::printf("categories=%zu ref_subcats=%zu concern=%zu surface=%zu\n",
                    g.categories.size(), g.ref_subcats.size(), g.concern.size(), g.surface.size());
        return 0;                                              // bare form byte-identical (parity §3)
    }
    // --json: the standardized tool-I/O envelope (E.1.2.B 0.1.5 / D-382/D-384). The C++ half of the
    // "two readers, one source" model — the per-table `schema` is READ from the shared registry (never a
    // literal → no drift), schema_version is DERIVED, TOOLCHAIN_VERSION is read; parity_check keeps it
    // byte-honest with toolio.py. RC-E discipline: loud-fail, never a silent-empty fact.
    if (g.schema_version.empty()) {
        std::fprintf(stderr, "ERROR: [SCHEMA] version underived from the spec SSoT\n"); return 2;
    }
    string tcv = trim_all(read_file(roots.engine / "tools" / "TOOLCHAIN_VERSION"));
    if (tcv.empty()) {
        std::fprintf(stderr, "ERROR: tools/TOOLCHAIN_VERSION missing or empty\n"); return 2;
    }
    string reg_text = read_file(roots.engine / "tools" / "lib" / "toolio_schemas.json");
    if (reg_text.empty()) {
        std::fprintf(stderr, "ERROR: tools/lib/toolio_schemas.json unreadable\n"); return 2;
    }
    size_t ri = 0;
    JVal reg = json_parse(reg_text, ri);
    const JVal* tables = nullptr;
    if (auto it = reg.obj.find("grammar/1"); it != reg.obj.end())
        if (auto jt = it->second.obj.find("tables"); jt != it->second.obj.end())
            tables = &jt->second;
    if (!tables) {
        std::fprintf(stderr, "ERROR: grammar/1.tables missing in toolio_schemas.json\n"); return 2;
    }
    // the registry-declared column list for a table, as a JSON array string (schema sourced from SSoT)
    auto reg_schema = [&](const string& t) -> string {
        string s = "[";
        if (auto it = tables->obj.find(t); it != tables->obj.end())
            for (size_t k = 0; k < it->second.arr.size(); ++k) {
                if (k) s += ",";
                s += "\"" + json_escape(it->second.arr[k].str) + "\"";
            }
        return s + "]";
    };
    auto table_1col = [&](const string& t, const set<string>& names) -> string {
        string s = "\"" + t + "\":{\"schema\":" + reg_schema(t) + ",\"rows\":[";
        bool first = true;
        for (const string& n : names) { if (!first) s += ","; s += "[\"" + json_escape(n) + "\"]"; first = false; }
        return s + "]}";
    };
    // unit_types carries a `closable` column (closable = name in openers()); openers() is NOT a
    // separate table (D-384 — CODE in openers but not unit_types; the plugin derives closable here).
    string ut = "\"unit_types\":{\"schema\":" + reg_schema("unit_types") + ",\"rows\":[";
    bool ut_first = true;
    for (const string& n : unit_types()) {
        if (!ut_first) ut += ",";
        ut += "[\"" + json_escape(n) + "\"," + (openers().count(n) ? "true" : "false") + "]";
        ut_first = false;
    }
    ut += "]}";

    string out = "{\"envelope_version\":\"1.0\",\"kind\":\"grammar\",\"schema_version\":\"" +
                 json_escape(g.schema_version) + "\",\"payload_schema_version\":\"grammar/1\","
                 "\"producer\":{\"tool\":\"foxtag\",\"version\":\"" + json_escape(tcv) +
                 "\",\"command\":\"grammar\",\"args\":[\"--json\"]},"
                 "\"status\":{\"ok\":true,\"code\":0,\"findings\":[]},"
                 "\"target\":{\"paths\":[],\"git_head\":\"" + json_escape(git_head_of(roots)) + "\"},"
                 "\"payload\":{" +
                 table_1col("categories", g.categories) + "," +
                 table_1col("ref_subcats", g.ref_subcats) + "," +
                 table_1col("concern", g.concern) + "," +
                 table_1col("surface", g.surface) + "," + ut + "}}";
    std::printf("%s\n", out.c_str());
    return 0;
}

//----------------------------------------------------------------------
// embedded selftest — structural teeth (a checker that cannot RED is Class-51 vacuous)
//----------------------------------------------------------------------
struct Case { const char* label; const char* src; const char* expect; };  // expect nullptr = clean

static const Case SELFTEST[] = {
    {"clean FUNCTION",
     "// [SCHEMA]_[v1.0]\n// [FUNCTION]_[F]\n// [TAG]_[[SLOW_PATH]]\n// [CODE]\nint f();\n"
     "// [END_CODE]\n// [END_FUNCTION]_[F]\n", nullptr},
    {"clean NESTED (STRUCT holds ENUM child)",
     "// [SCHEMA]_[v1.0]\n// [STRUCT]_[O]\n// [CODE]\n// [ENUM]_[I]\n// [CODE]\nenum I { A };\n"
     "// [END_CODE]\n// [END_ENUM]_[I]\n// [END_CODE]\n// [END_STRUCT]_[O]\n", nullptr},
    {"unknown category", "// [SCHEMA]_[v1.0]\n// [FUNCTON]_[typo]\n", "UNKNOWN category"},
    {"two categories", "// [SCHEMA]_[v1.0]\n// [FUNCTION]_[X] [TAG]_[[HOT_PATH]]\n", "TWO categories"},
    {"missing closer", "// [SCHEMA]_[v1.0]\n// [FUNCTION]_[Orphan]\n", "no matching [END_FUNCTION]"},
    {"missing END_ENUM", "// [SCHEMA]_[v1.0]\n// [ENUM]_[Orphan]\n", "no matching [END_ENUM]"},
    {"name mismatch", "// [SCHEMA]_[v1.0]\n// [FUNCTION]_[A]\n// [END_FUNCTION]_[B]\n", "name mismatch"},
    {"end with no open", "// [SCHEMA]_[v1.0]\n// [END_STRUCT]_[X]\n", "no open [STRUCT]"},
    {"bad tag value", "// [SCHEMA]_[v1.0]\n// [TAG]_[[NOT_A_REAL_SURFACE_TAG]]\n",
     "not in doc-tag-vocabulary"},
    {"ref dangling INVARIANT", "// [SCHEMA]_[v1.0]\n// [REFERENCE]_[INVARIANT]_[H999]\n", "dangling"},
    {"ref valid INVARIANT", "// [SCHEMA]_[v1.0]\n// [REFERENCE]_[INVARIANT]_[H4]\n", nullptr},
    {"ref unknown subcat", "// [SCHEMA]_[v1.0]\n// [REFERENCE]_[REGISTRY]_[X]\n",
     "UNKNOWN [REFERENCE] subcat"},
};

static int cmd_selftest(const Grammar& g, const RefIndex& idx) {
    bool ok = true;
    fs::path dir = fs::temp_directory_path() / "foxtag_selftest";
    std::error_code ec;
    fs::create_directories(dir, ec);
    int n = 0;
    for (const Case& c : SELFTEST) {
        fs::path p = dir / ("case_" + std::to_string(n++) + ".hpp");
        { std::ofstream f(p, std::ios::binary); f << c.src; }
        FileResult r = parse_file(p.string(), g, idx);
        bool hit;
        if (!c.expect) hit = r.violations.empty();
        else {
            hit = false;
            for (const string& v : r.violations)
                if (v.find(c.expect) != string::npos) { hit = true; break; }
        }
        std::printf("  %s %s: %zu violation(s)\n", hit ? "OK " : "FAIL", c.label,
                    r.violations.size());
        if (!hit) { ok = false; for (const string& v : r.violations) std::printf("      %s\n", v.c_str()); }
        fs::remove(p, ec);
    }
    fs::remove_all(dir, ec);
    std::printf("foxtag selftest: %s\n", ok ? "ALL OK" : "FAILURES");
    return ok ? 0 : 2;
}

int main(int argc, char** argv) {
    if (argc < 2) {
        std::fprintf(stderr,
                     "usage: foxtag <validate|units|unit|tags|grammar|parity-dump|selftest> ...\n");
        return 2;
    }
    Roots roots = resolve_roots();
    if (!roots.ok) { std::fprintf(stderr, "ERROR: %s\n", roots.err.c_str()); return 2; }
    Grammar g = load_grammar(roots);
    if (!g.ok) { std::fprintf(stderr, "ERROR: %s\n", g.err.c_str()); return 2; }
    RefIndex idx = load_ref_index(roots);
    {
        vector<string> vac = ref_index_vacuous(idx);
        if (!vac.empty()) {
            std::fprintf(stderr, "ERROR: [REFERENCE] index vacuous — {");
            for (size_t i = 0; i < vac.size(); ++i)
                std::fprintf(stderr, "%s%s", i ? ", " : "", vac[i].c_str());
            std::fprintf(stderr, "} resolved 0 ids (broken source path?); refusing to scan\n");
            return 2;
        }
    }

    string cmd = argv[1];
    vector<string> paths;
    bool json = false;
    string f_type, f_tag, f_name;
    CodegenInput cg;
    cg.engine_root = roots.engine;
    for (int i = 2; i < argc; ++i) {
        string a = argv[i];
        if (a == "--json") json = true;
        else if (a == "--type" && i + 1 < argc) f_type = argv[++i];
        else if (a == "--tag" && i + 1 < argc) f_tag = argv[++i];
        else if (a == "--name" && i + 1 < argc) f_name = argv[++i];
        else if (a == "--header" && i + 1 < argc) cg.headers.push_back(argv[++i]);
        else if (a == "--params" && i + 1 < argc) cg.params = argv[++i];
        else if (a == "--call" && i + 1 < argc) cg.call = argv[++i];
        else if (a == "--prelude" && i + 1 < argc) cg.prelude = argv[++i];
        else if (a == "--flags" && i + 1 < argc) {
            std::istringstream ss(argv[++i]);
            string tok;
            while (ss >> tok) cg.flags.push_back(tok);
        } else paths.push_back(a);
    }

    if (cmd == "codegen") {
        if (cg.call.empty()) {
            std::fprintf(stderr, "usage: foxtag codegen --header H --params 'SIG' --call 'EXPR' "
                                 "[--flags '...'] [--prelude '...']\n");
            return 2;
        }
        return cmd_codegen(cg);
    }
    if (cmd == "codegen-selftest") return cmd_codegen_selftest(roots.engine);
    if (cmd == "layout") {
        if (paths.empty()) { std::fprintf(stderr, "usage: foxtag layout <tu.cpp> [Struct ...]\n"); return 2; }
        return cmd_layout(paths[0], vector<string>(paths.begin() + 1, paths.end()));
    }
    if (cmd == "fields") {
        if (paths.empty()) { std::fprintf(stderr, "usage: foxtag fields <tu.cpp> [Struct ...]\n"); return 2; }
        return cmd_fields(paths[0], vector<string>(paths.begin() + 1, paths.end()));
    }
    if (cmd == "validate") return cmd_validate(g, idx, roots, paths);
    if (cmd == "units") return cmd_units(g, idx, roots, paths, json, f_type, f_tag, f_name);
    if (cmd == "unit") {
        if (paths.size() != 2) { std::fprintf(stderr, "usage: foxtag unit <file> <line>\n"); return 2; }
        return cmd_unit_at(g, idx, paths[0], std::atoi(paths[1].c_str()));
    }
    if (cmd == "tags") return cmd_tags(g, idx, roots, paths);
    if (cmd == "grammar") return cmd_grammar(g, roots, json);
    if (cmd == "parity-dump") return cmd_parity_dump(g, idx, roots);
    if (cmd == "selftest") return cmd_selftest(g, idx);
    std::fprintf(stderr, "unknown command: %s\n", cmd.c_str());
    return 2;
}
