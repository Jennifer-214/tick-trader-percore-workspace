// foxtag_codegen.hpp — the CODEGEN fact-producer (D-337 increment 2b; RC-A/RC-C/RC-E built in).
//
// Compiles a NOINLINE PROBE-WRAPPER with g++ (CODEGEN facts are g++-ONLY — clang's instruction
// selection diverges from the shipped compiler, D-321), disassembles it, and reports the
// [DERIVED] codegen axes: instruction count ([SIZE]_[n instr]) · 3-class branch breakdown
// (loop / rare-cold / data-dependent — the H7/H20 meter) · float + div ops · stack-spill proxy ·
// the RC-C SIMD WIDTH-CLASS (scalar-xmm vs packed sse/avx2/avx512 — the old detector matched
// AVX-only and false-cleaned the scalar engine) · call/indirect counts.
//
// The analysis semantics are a LINE-FOR-LINE port of check_latency_path_conformance.py's
// adversarially-hardened core (5 independent refute passes): the probe shape, objdump -d -r -l
// (-r or external calls are INVISIBLE in an unlinked .o), reloc-names-the-PRECEDING-instruction,
// the 75%-span cold-tail heuristic, the FLOAT_OPS regex broadened to v-prefixed/FMA forms (the
// vfmadd false-clean catch), .isra/.constprop clone awareness. GATING (budgets / H-invariant
// enforcement / transitive follow) deliberately stays the analyzer's job — this producer REPORTS.
//
// RC-A: the probe instantiates templates concretely (`Regime_Classify<64>(a,b,c)`) — the fix for
//       header/template TUs that emit nothing. RC-E: a body below the non-vacuity floor is a LOUD
//       "VACUOUS" exit 2 (optimized away / wrong symbol), NEVER a green zero-branch verdict.
//
// Per D-327 these axes are LIVE-PREVIEW class (volatile under flags) — consumers pin [BUILD]
// before ever writing them; the JSON carries the effective flags for exactly that reason.

#pragma once

#include "foxtag_layout.hpp"   // run_capture_split / shell_quote / JSON bits (+ foxtag.hpp)

#include <regex>

namespace foxtag {

//======================================================================
// constants (verbatim ports — see check_latency_path_conformance.py)
//======================================================================

inline const set<string>& cond_jumps() {
    static const set<string> s = {
        "je", "jne", "jz", "jnz", "jg", "jge", "jl", "jle", "ja", "jae", "jb", "jbe",
        "js", "jns", "jo", "jno", "jp", "jnp", "jc", "jnc", "jcxz", "jecxz", "jrcxz",
    };
    return s;
}

// scalar AND packed, SSE + v-prefixed AVX + FMA (the vfmadd catch); integer packed
// (vpaddq…) correctly NOT matched (p-prefix + b/w/d/q suffix).
inline const std::regex& float_ops_re() {
    static const std::regex r(
        R"(\bv?(mul|add|sub|div|sqrt|max|min|comi|ucomi|cvt|fn?m(add|sub))[a-z0-9]*[sp][sd]\b)");
    return r;
}
inline const std::regex& div_ops_re() {
    static const std::regex r(R"(\bi?div[a-z]?\b|\bv?div[sp][sd]\b)");
    return r;
}
// packed-float form specifically (ends ps/pd) — the RC-C packed-vs-scalar discriminator
inline const std::regex& packed_float_re() {
    static const std::regex r(
        R"(\bv?(mul|add|sub|div|sqrt|max|min|cvt|fn?m(add|sub))[a-z0-9]*p[sd]\b)");
    return r;
}
// packed-INTEGER vector forms (vpaddq / paddd / pmullw …) — SIMD even with zero floats
inline const std::regex& packed_int_re() {
    static const std::regex r(R"(\bv?p(add|sub|mul|and|or|xor|cmp|min|max|sll|srl|sra|unpck|shuf|blend|broadcast|mov)[a-z0-9]*\b)");
    return r;
}

constexpr int NONVACUITY_FLOOR = 8;   // < this = optimized away / wrong symbol (RC-E)

//======================================================================
// probe compile + disassemble (mirror compile_and_disasm)
//======================================================================

struct CodegenInput {
    vector<string> headers;   // engine-root-relative includes
    string params;            // probe_fn parameter list (types the call consumes)
    string call;              // the anchored call expression (RC-A: concrete template args)
    string prelude;           // optional extra TU code (selftest helpers live here)
    vector<string> flags;     // compile flags; empty -> canonical [BUILD] default
    fs::path engine_root;
};

inline vector<string> default_codegen_flags(const fs::path& engine_root) {
    // the schema's canonical [BUILD] pin (D-313: a concrete microarch, NOT -march=native —
    // native is host-resolved and false-REDs asm goldens across build hosts)
    return {"-std=c++20", "-O3", "-march=x86-64-v3", "-I" + engine_root.string()};
}

// returns the disassembly text, or empty + err set
inline string compile_and_disasm(const CodegenInput& in, string& err) {
    string src;
    for (const string& h : in.headers) src += "#include \"" + h + "\"\n";
    src += in.prelude + "\n";
    src += "extern \"C\" __attribute__((noinline)) void probe_fn(" + in.params + ") {\n    " +
           in.call + ";\n}\n";

    // in-repo temp dir — /tmp may be noexec (LANDMINE); mirror the analyzer
    fs::path td = in.engine_root / (".foxtag_probe_" + std::to_string((long)getpid()));
    std::error_code ec;
    fs::create_directories(td, ec);
    fs::path cpp = td / "probe.cpp", obj = td / "probe.o";
    { std::ofstream f(cpp, std::ios::binary); f << src; }

    const char* cxx_env = std::getenv("CXX");
    string cxx = (cxx_env && *cxx_env) ? cxx_env : "g++";
    vector<string> flags = in.flags.empty() ? default_codegen_flags(in.engine_root) : in.flags;
    string cmd = "cd " + shell_quote(in.engine_root.string()) + " && " + shell_quote(cxx);
    for (const string& f : flags) cmd += " " + shell_quote(f);
    cmd += " -g -c " + shell_quote(cpp.string()) + " -o " + shell_quote(obj.string());
    string comp_out = run_capture_split(cmd);
    if (!fs::exists(obj, ec)) {
        // surface the first error: line (mirror: never silently skip a probe failure)
        err = "compile failed";
        for (const string& l : split_lines(comp_out))
            if (l.find("error:") != string::npos) { err = strip(l); break; }
        fs::remove_all(td, ec);
        return {};
    }
    // -r: an UNLINKED .o shows an external `call` only via the reloc line — without it the
    // call accounting is VACUOUS (the analyzer's teeth caught this). -l: source lines.
    string dis = run_capture_split("objdump -d -r -l --no-show-raw-insn " + shell_quote(obj.string()));
    fs::remove_all(td, ec);
    if (dis.empty()) err = "objdump failed";
    return dis;
}

//======================================================================
// analysis (mirror analyze() — REPORT axes only; gating stays the analyzer's)
//======================================================================

struct CodegenFacts {
    long instructions = 0;
    long br_loop = 0, br_rare_cold = 0, br_data_dependent = 0;
    long floats = 0, divs = 0, spills = 0;
    long calls = 0, indirect_calls = 0;
    long xmm = 0, ymm = 0, zmm = 0;          // register-class sightings
    long packed_ops = 0;                     // packed float + packed integer vector ops
    string simd_class;                       // none | scalar-xmm | sse-packed | avx2 | avx512
    bool nonvacuous = false;
    string build;                            // the effective flags (the [BUILD] pin)
};

inline bool instr_line(const string& ln, string& mnemonic, string& ops) {
    // mirror INSTR_RE: ^\s+hex:\s+mnemonic\s*ops   (objdump --no-show-raw-insn)
    size_t i = ln.find_first_not_of(" \t");
    if (i == string::npos || i == 0) { if (i == string::npos) return false; }
    if (i == 0) return false;                                  // must be indented
    size_t j = i;
    while (j < ln.size() && ((ln[j] >= '0' && ln[j] <= '9') || (ln[j] >= 'a' && ln[j] <= 'f'))) ++j;
    if (j == i || j >= ln.size() || ln[j] != ':') return false;
    size_t k = j + 1;
    while (k < ln.size() && (ln[k] == ' ' || ln[k] == '\t')) ++k;
    if (k >= ln.size() || ln[k] < 'a' || ln[k] > 'z') return false;
    size_t m = k;
    while (m < ln.size() && ((ln[m] >= 'a' && ln[m] <= 'z') || (ln[m] >= '0' && ln[m] <= '9') ||
                             ln[m] == '.')) ++m;
    mnemonic = ln.substr(k, m - k);
    ops = strip(ln.substr(m));
    return true;
}

inline long hex_addr(const string& ln) {
    size_t i = ln.find_first_not_of(" \t");
    size_t j = i;
    while (j < ln.size() && ((ln[j] >= '0' && ln[j] <= '9') || (ln[j] >= 'a' && ln[j] <= 'f'))) ++j;
    return (j > i) ? std::stol(ln.substr(i, j - i), nullptr, 16) : -1;
}

inline CodegenFacts analyze_codegen(const string& disasm, const string& symbol) {
    CodegenFacts f;
    struct BodyLine { long addr; string mn, ops; };
    vector<BodyLine> body;
    bool in_fn = false;
    for (const string& ln : split_lines(disasm)) {
        if (ln.find("<" + symbol + ">:") != string::npos) { in_fn = true; continue; }
        if (!in_fn) continue;
        if (strip(ln).empty()) break;
        string mn, ops;
        if (instr_line(ln, mn, ops)) body.push_back({hex_addr(ln), mn, ops});
        // reloc / source lines don't parse as instructions — counts unaffected (the reloc's
        // external-target NAME feeds the analyzer's forbidden gate, not these report axes)
    }
    if (body.empty()) return f;

    long lo = body.front().addr, hi = body.back().addr;
    long span = std::max<long>(1, hi - lo);
    long cold_start = lo + (long)(span * 0.75);   // gcc tails cold blocks (upper quartile)

    for (const BodyLine& b : body) {
        if (cond_jumps().count(b.mn)) {
            long tgt = -1;
            size_t e = 0;
            while (e < b.ops.size() && ((b.ops[e] >= '0' && b.ops[e] <= '9') ||
                                        (b.ops[e] >= 'a' && b.ops[e] <= 'f'))) ++e;
            if (e > 0) tgt = std::stol(b.ops.substr(0, e), nullptr, 16);
            if (tgt < 0) tgt = b.addr;
            if (tgt < b.addr) ++f.br_loop;
            else if (tgt >= cold_start) ++f.br_rare_cold;
            else ++f.br_data_dependent;
        }
        if (b.mn == "call") {
            ++f.calls;
            // indirect through a single fn-pointer (H2 risk-shape); an INDEXED
            // `call *(,%idx,scale)` is a fn-pointer TABLE = sanctioned branchless dispatch
            bool indexed = std::regex_search(b.ops, std::regex(R"(,%\w+,\d)"));
            if (b.ops.find('*') != string::npos && !indexed) ++f.indirect_calls;
        }
        string probe_text = b.mn + " " + b.ops;
        if (std::regex_search(b.mn, float_ops_re()) || std::regex_search(b.ops, float_ops_re()))
            ++f.floats;
        if (std::regex_search(probe_text, div_ops_re())) ++f.divs;
        if (b.mn == "mov" && std::regex_search(b.ops, std::regex(R"(,\s*-?0x[0-9a-f]+\(%rbp\))")) &&
            b.ops.find("%rsp") == string::npos)
            ++f.spills;
        if (b.ops.find("%xmm") != string::npos || b.mn.find("xmm") != string::npos) ++f.xmm;
        if (b.ops.find("%ymm") != string::npos) ++f.ymm;
        if (b.ops.find("%zmm") != string::npos) ++f.zmm;
        if (std::regex_search(b.mn, packed_float_re()) ||
            (std::regex_search(b.mn, packed_int_re()) &&
             (b.ops.find("%xmm") != string::npos || b.ops.find("%ymm") != string::npos ||
              b.ops.find("%zmm") != string::npos)))
            ++f.packed_ops;
    }
    f.instructions = (long)body.size();
    f.nonvacuous = f.instructions >= NONVACUITY_FLOOR;
    // RC-C width-class: report what's REALLY there — scalar-xmm is NOT "no SIMD story",
    // it's the engine's actual float form; packed classes by the widest register used.
    if (f.zmm > 0 && f.packed_ops > 0) f.simd_class = "avx512";
    else if (f.ymm > 0 && f.packed_ops > 0) f.simd_class = "avx2";
    else if (f.packed_ops > 0) f.simd_class = "sse-packed";
    else if (f.xmm > 0) f.simd_class = "scalar-xmm";
    else f.simd_class = "none";
    return f;
}

//======================================================================
// the command
//======================================================================

inline string codegen_json(const CodegenFacts& f, const string& symbol) {
    string j = "{\"symbol\":\"" + json_escape(symbol) + "\"";
    j += ",\"nonvacuous\":" + string(f.nonvacuous ? "true" : "false");
    j += ",\"instructions\":" + std::to_string(f.instructions);
    j += ",\"branches\":{\"loop\":" + std::to_string(f.br_loop) +
         ",\"rare_cold\":" + std::to_string(f.br_rare_cold) +
         ",\"data_dependent\":" + std::to_string(f.br_data_dependent) +
         ",\"total\":" + std::to_string(f.br_loop + f.br_rare_cold + f.br_data_dependent) + "}";
    j += ",\"floats\":" + std::to_string(f.floats);
    j += ",\"divs\":" + std::to_string(f.divs);
    j += ",\"spills\":" + std::to_string(f.spills);
    j += ",\"calls\":" + std::to_string(f.calls);
    j += ",\"indirect_calls\":" + std::to_string(f.indirect_calls);
    j += ",\"simd\":{\"class\":\"" + f.simd_class + "\",\"packed_ops\":" +
         std::to_string(f.packed_ops) + ",\"regs\":{\"xmm\":" + std::to_string(f.xmm) +
         ",\"ymm\":" + std::to_string(f.ymm) + ",\"zmm\":" + std::to_string(f.zmm) + "}}";
    j += ",\"build\":\"" + json_escape(f.build) + "\"}";
    return j;
}

// exit 0 + JSON; exit 2 on compile/objdump failure OR a VACUOUS body (RC-E: never green-on-nothing)
inline int cmd_codegen(const CodegenInput& in) {
    string err;
    string dis = compile_and_disasm(in, err);
    if (dis.empty()) {
        std::fprintf(stderr, "PROBE-FAIL: %s\n", err.c_str());
        return 2;
    }
    CodegenFacts f = analyze_codegen(dis, "probe_fn");
    {
        vector<string> flags = in.flags.empty() ? default_codegen_flags(in.engine_root) : in.flags;
        for (size_t i = 0; i < flags.size(); ++i) f.build += (i ? " " : "") + flags[i];
    }
    if (!f.nonvacuous) {
        // RC-E: the old branchtag painted "branchless ✓" on 0-instruction parses — a FALSE
        // all-clear on a branchless-discipline engine. A vacuous body is an ERROR, never a verdict.
        std::fprintf(stderr,
                     "VACUOUS: %ld instruction(s) < floor %d — optimized away / wrong symbol; "
                     "no verdict emitted (RC-E)\n", f.instructions, NONVACUITY_FLOOR);
        return 2;
    }
    std::printf("%s\n", codegen_json(f, "probe_fn").c_str());
    return 0;
}

//======================================================================
// selftest teeth (known-shape probes — every detector must fire; RED cases must red)
//======================================================================

struct CodegenCase {
    const char* label;
    const char* prelude;
    const char* params;
    const char* call;
    // expectations (−1 = don't care):  vacuous_expected → exit-2 path
    bool expect_vacuous;
    long min_instr;
    long max_branch_total;   // -1 = don't care
    long min_loop;
    long min_floats;
    long min_divs;
    const char* simd_class;  // nullptr = don't care
};

inline int cmd_codegen_selftest(const fs::path& engine_root) {
    // volatile sinks stop the optimizer deleting the work; helpers are INLINE so they
    // inline INTO probe_fn — mirroring the real engine kernels (inline/template in headers),
    // which is the entire point of the probe shape (a noinline helper would leave probe_fn
    // as a bare call — the first teeth run caught exactly that)
    static const CodegenCase CASES[] = {
        {"branchless mask select (0 data-dependent branches)",
         "static inline long msel(long a, long b) {\n"
         "    long m1 = -(long)(a < b);\n"
         "    long x = (a & m1) | (b & ~m1);\n"
         "    long m2 = -(long)((x ^ a) > b);\n"
         "    long y = (x & m2) | ((a + b) & ~m2);\n"
         "    long m3 = -(long)(y != x);\n"
         "    return (y & m3) | ((x >> 3) & ~m3);\n"
         "}\nvolatile long g_sink;\n",
         "long a, long b", "g_sink = msel(a, b)", false, 8, 0, 0, 0, 0, nullptr},
        {"summing loop (loop branch present)",
         "static inline long ssum(const long* v, int n) {\n"
         "    long s = 0;\n"
         "    for (int i = 0; i < n; ++i) s += v[i];\n"
         "    return s;\n"
         "}\nvolatile long g_sink2;\n",
         "const long* v, int n", "g_sink2 = ssum(v, n)", false, 8, -1, 1, 0, 0, nullptr},
        {"scalar double math (floats detected; scalar-xmm class)",
         "static inline double fmix(double a, double b) {\n"
         "    double c = a * b + a / (b + 1.5);\n"
         "    double d = c * c - b * 0.25;\n"
         "    return d * a + c / (d + 2.0);\n"
         "}\nvolatile double g_sinkd;\n",
         "double a, double b", "g_sinkd = fmix(a, b)", false, 8, -1, 0, 2, 1, "scalar-xmm"},
        {"packed AVX2 intrinsics (ymm packed class)",
         "#include <immintrin.h>\n"
         "static inline void vmul(double* o, const double* a, const double* b) {\n"
         "    for (int i = 0; i < 64; i += 4) {\n"
         "        __m256d x = _mm256_loadu_pd(a + i), y = _mm256_loadu_pd(b + i);\n"
         "        _mm256_storeu_pd(o + i, _mm256_mul_pd(x, y));\n"
         "    }\n"
         "}\n",
         "double* o, const double* a, const double* b", "vmul(o, a, b)", false, 8, -1, 0, 1, 0, "avx2"},
        {"RC-E vacuous (inlined-away empty body -> exit 2, never a verdict)",
         "inline void nothing() {}\n",
         "int a", "(void)a; nothing()", true, 0, -1, 0, 0, 0, nullptr},
    };
    bool ok = true;
    for (const CodegenCase& c : CASES) {
        CodegenInput in;
        in.engine_root = engine_root;
        in.prelude = c.prelude;
        in.params = c.params;
        in.call = c.call;
        string err;
        string dis = compile_and_disasm(in, err);
        bool hit = false;
        string note;
        if (dis.empty()) {
            note = "PROBE-FAIL: " + err;
        } else {
            CodegenFacts f = analyze_codegen(dis, "probe_fn");
            if (c.expect_vacuous) {
                hit = !f.nonvacuous;
                note = "instr=" + std::to_string(f.instructions);
            } else {
                long btot = f.br_loop + f.br_rare_cold + f.br_data_dependent;
                hit = f.nonvacuous && f.instructions >= c.min_instr &&
                      (c.max_branch_total < 0 || btot <= c.max_branch_total) &&
                      f.br_loop >= c.min_loop && f.floats >= c.min_floats && f.divs >= c.min_divs &&
                      (!c.simd_class || f.simd_class == c.simd_class);
                note = "instr=" + std::to_string(f.instructions) + " br=" + std::to_string(btot) +
                       " loop=" + std::to_string(f.br_loop) + " floats=" + std::to_string(f.floats) +
                       " divs=" + std::to_string(f.divs) + " simd=" + f.simd_class;
            }
        }
        std::printf("  %s %s: %s\n", hit ? "OK " : "FAIL", c.label, note.c_str());
        ok = ok && hit;
    }
    std::printf("foxtag codegen-selftest: %s\n", ok ? "ALL OK" : "FAILURES");
    return ok ? 0 : 2;
}

} // namespace foxtag
