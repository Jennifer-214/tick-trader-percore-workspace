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
//   foxtag selftest                embedded structural teeth (RED cases must red)

#include "foxtag.hpp"
#include "foxtag_layout.hpp"

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

static int cmd_grammar(const Grammar& g) {
    std::printf("categories=%zu ref_subcats=%zu concern=%zu surface=%zu\n",
                g.categories.size(), g.ref_subcats.size(), g.concern.size(), g.surface.size());
    return 0;
}

//----------------------------------------------------------------------
// embedded selftest — structural teeth (a checker that cannot RED is Class-51 vacuous)
//----------------------------------------------------------------------
struct Case { const char* label; const char* src; const char* expect; };  // expect nullptr = clean

static const Case SELFTEST[] = {
    {"clean FUNCTION",
     "// [SCHEMA]_[v1]\n// [FUNCTION]_[F]\n// [TAG]_[[SLOW_PATH]]\n// [CODE]\nint f();\n"
     "// [END_CODE]\n// [END_FUNCTION]_[F]\n", nullptr},
    {"clean NESTED (STRUCT holds ENUM child)",
     "// [SCHEMA]_[v1]\n// [STRUCT]_[O]\n// [CODE]\n// [ENUM]_[I]\n// [CODE]\nenum I { A };\n"
     "// [END_CODE]\n// [END_ENUM]_[I]\n// [END_CODE]\n// [END_STRUCT]_[O]\n", nullptr},
    {"unknown category", "// [SCHEMA]_[v1]\n// [FUNCTON]_[typo]\n", "UNKNOWN category"},
    {"two categories", "// [SCHEMA]_[v1]\n// [FUNCTION]_[X] [TAG]_[[HOT_PATH]]\n", "TWO categories"},
    {"missing closer", "// [SCHEMA]_[v1]\n// [FUNCTION]_[Orphan]\n", "no matching [END_FUNCTION]"},
    {"missing END_ENUM", "// [SCHEMA]_[v1]\n// [ENUM]_[Orphan]\n", "no matching [END_ENUM]"},
    {"name mismatch", "// [SCHEMA]_[v1]\n// [FUNCTION]_[A]\n// [END_FUNCTION]_[B]\n", "name mismatch"},
    {"end with no open", "// [SCHEMA]_[v1]\n// [END_STRUCT]_[X]\n", "no open [STRUCT]"},
    {"bad tag value", "// [SCHEMA]_[v1]\n// [TAG]_[[NOT_A_REAL_SURFACE_TAG]]\n",
     "not in doc-tag-vocabulary"},
    {"ref dangling INVARIANT", "// [SCHEMA]_[v1]\n// [REFERENCE]_[INVARIANT]_[H999]\n", "dangling"},
    {"ref valid INVARIANT", "// [SCHEMA]_[v1]\n// [REFERENCE]_[INVARIANT]_[H4]\n", nullptr},
    {"ref unknown subcat", "// [SCHEMA]_[v1]\n// [REFERENCE]_[REGISTRY]_[X]\n",
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
    for (int i = 2; i < argc; ++i) {
        string a = argv[i];
        if (a == "--json") json = true;
        else if (a == "--type" && i + 1 < argc) f_type = argv[++i];
        else if (a == "--tag" && i + 1 < argc) f_tag = argv[++i];
        else if (a == "--name" && i + 1 < argc) f_name = argv[++i];
        else paths.push_back(a);
    }

    if (cmd == "layout") {
        if (paths.empty()) { std::fprintf(stderr, "usage: foxtag layout <tu.cpp> [Struct ...]\n"); return 2; }
        return cmd_layout(paths[0], vector<string>(paths.begin() + 1, paths.end()));
    }
    if (cmd == "validate") return cmd_validate(g, idx, roots, paths);
    if (cmd == "units") return cmd_units(g, idx, roots, paths, json, f_type, f_tag, f_name);
    if (cmd == "unit") {
        if (paths.size() != 2) { std::fprintf(stderr, "usage: foxtag unit <file> <line>\n"); return 2; }
        return cmd_unit_at(g, idx, paths[0], std::atoi(paths[1].c_str()));
    }
    if (cmd == "tags") return cmd_tags(g, idx, roots, paths);
    if (cmd == "grammar") return cmd_grammar(g);
    if (cmd == "parity-dump") return cmd_parity_dump(g, idx, roots);
    if (cmd == "selftest") return cmd_selftest(g, idx);
    std::fprintf(stderr, "unknown command: %s\n", cmd.c_str());
    return 2;
}
