#!/usr/bin/env python3
"""
check_latency_path_conformance.py — STATIC latency-path conformance analyzer.

WHAT (the meta-pattern this is the 2nd instance of — sister to check_struct_size_budget.py):
  A manifest-driven, COMPILE-TIME-measured, derived-fact gate. The size tool gates
  sizeof; this gates the *compiled instruction stream* of the latency-critical paths.
  It MECHANIZES `latency-path-discipline.md` + the hot/slow Hard Invariants from the
  disassembly of the PRODUCTION build (no -DLATENCY_PROFILING — the SHIPPED hot path,
  not the sampling-instrumented one). Instruction-count budgets replace wall-clock-ns
  budgets: deterministic, diffable, no run, no box-pinning (D-233/D-234).

THE BRANCH MODEL (D-235 — the headline):
  Every conditional branch is classified by prediction behavior:
    - compile-time-gone (`if constexpr`)      -> emits nothing (invisible; good).
    - loop back-edge (target < addr)          -> predictable; ~free.
    - rare-event-cold (fwd jump to cold tail; -> predicted not-taken (the seqlock-miss,
        `__builtin_expect(...,0)` pattern)         the trade-push); ~free.
    - data-dependent-WARM (everything else)   -> the mispredict-prone JITTER risk; the
                                                  H7/H20 / critical-moment-determinism
                                                  target -> drive to ZERO.
  ALLOWED-rule (operator, D-235): the ONLY acceptable data-dependent branch is one
  DECIDED DURING WARMUP and 100%-PREDICTED thereafter. Statically we cannot PROVE that
  (it is a runtime property) -> TWO-LAYER enforcement:
    (1) STATIC (here): flag every data-dependent-warm branch; each must be ALLOWLISTED
        with a "warmup-decided / 100%-predicted" rationale, or it is a VIOLATION.
    (2) RUNTIME (deferred, option-2 PMU step ~E.1.2): `perf stat -e branch-misses`
        CONFIRMS each allowlisted branch is ~0% mispredict in steady state.

  HONEST CAVEAT: the rare-cold vs data-dependent split is a STRUCTURAL HEURISTIC (gcc
  cold-tail placement). It is a strong starting signal, refined by the allowlist + the
  runtime PMU confirm — it is NOT a proof on its own.

OTHER CHECKS (each maps to an invariant, decidable from ASM):
  no scalar-float (H4) · no div/idiv (§5 reciprocals) · no malloc/free/__libc/lock
  calls (H1/Rule 2) · no indirect call / vtable (H2) · stack-spill count (reg pressure).

NON-VACUITY + REACH (eat-own-dogfood — else this is the Class-51 guard it codifies against):
  ASSERTS the probe symbol was found + a real body disassembled (instr > floor) so an
  optimized-away probe can never pass green. THREE reach mechanisms so we analyze the REAL
  body, never thin glue (the post-3:3 finds — A-1/I-1):
    - INLINED target (always_inline / hot path)  → analyze the probe_fn wrapper directly.
    - OUT-OF-LINE target (inline-not-always_inline, incl. a GCC `.isra.N`/`.constprop.N`
      clone reached by a resolved jmp with NO reloc) → find the target's OWN symbol by its
      mangled length-prefixed name + analyze THAT (the .isra evasion that let a 19-instr
      glue wrapper pass green on a 4617-instr body).
    - TRANSITIVE warm work → a HARD-invariant (float/div/forbidden/indirect) can hide one
      `call` deeper than the analyzed body (the slow path bottoms out in out-of-line FPN
      kernels). Bounded-recurse into WARM residual calls to defined same-TU bodies; a warm
      call to a body we CANNOT see (not in this .o, not forbidden) FAILS LOUD rather than
      certify a false green.

TOOL-DESIGN DISCIPLINE (the 3 lessons, → the ship-close conformance DESIGN_SPEC):
  1. A static-ASM detector can be a STRONGER gate than a source-grep — the compiled ASM
     is ground truth where the source check is undecidable (this is why branch-count
     SUBSUMES the H7/H20 grep: the grep over-fires + can't tell a compliant fn-pointer
     dispatch from a violation; the ASM branch is unambiguous).
  2. Each detector's mnemonic patterns MUST enumerate the FULL variant space
     (SSE + AVX/`v`-prefixed + FMA + scalar `s[sd]` AND packed `p[sd]`). PROVEN by the
     dogfood: the float regex was SSE-only (`mulsd|addsd`) and silently MISSED the
     `-march=native` fused `vfmadd` — a false-clean (now `FLOAT_OPS`/`DIV_OPS` broadened).
  3. The `--selftest` teeth ARE the guard against (2) — only because it injects float math
     did the AVX/FMA hole surface. EVERY check needs inject→RED teeth, not just float
     (the non-float teeth are the open finish-item).

MODES:
  (default)          report-only: MEASURE + print the per-category breakdown (+ ASM).
  --asm              also dump the full per-function disassembly.
  --update-budgets   write measured counts -> budgets sidecar (the ratchet baseline).
  --selftest         teeth: inject each violation into a probe -> its detector MUST fire
                     (float/div/forbidden/indirect/branch/non-vacuity + the reach/transitive/
                     fail-loud/stdio cases — every detector, not just float; D-234 lesson 3).

EXIT: 0 = clean / report-only. 1 = a budget/invariant violation OR un-analyzed warm work.
2 = a probe failed to compile (tooling error — surfaced, never silently skipped).
3 = a --selftest tooth did NOT fire (a detector regressed — under-enumeration).

Run from the engine root or set FOXML_ENGINE. PRODUCTION flags only (no LATENCY_PROFILING).
"""
import os
import re
import subprocess
import sys
import json

ENGINE = os.environ.get("FOXML_ENGINE") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CXX = os.environ.get("CXX", "g++")
# PRODUCTION build flags — pinned (counts shift with compiler/flags; re-baseline on intentional change).
FLAGS = ["-std=c++20", "-O3", "-march=native", f"-I{ENGINE}"]
BUDGETS_SIDECAR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib", "latency_path_budgets.json")
NONVACUITY_FLOOR = 8  # a real inlined hot/slow body is far bigger; < this = optimized away / wrong symbol.
MAX_FOLLOW_DEPTH = 5  # bounded transitive recursion into warm defined callees (cycle-guarded; closes A-1's "div behind a call")

COND_JUMPS = {
    "je", "jne", "jz", "jnz", "jg", "jge", "jl", "jle", "ja", "jae", "jb", "jbe",
    "js", "jns", "jo", "jno", "jp", "jnp", "jc", "jnc", "jcxz", "jecxz", "jrcxz",
}
# -march=native uses AVX/FMA float forms (v-prefixed + vfmadd) — match scalar AND packed
# (FPN_Binary is __int128 INTEGER, so ANY float op on these paths is an H4 signal). Integer
# packed ops (vpaddq/vpmullq…) end in b/w/d/q after a `p`-prefix → correctly NOT matched.
FLOAT_OPS = re.compile(r"\bv?(mul|add|sub|div|sqrt|max|min|comi|ucomi|cvt|fn?m(add|sub))[a-z0-9]*[sp][sd]\b")
DIV_OPS = re.compile(r"\bi?div[a-z]?\b|\bv?div[sp][sd]\b")
# Full variant space (D-234 lesson 2): C allocators + aligned variants + every C++
# new/delete mangling (_Znwm new / _Znam new[] / _ZdlPv delete / _ZdaPv delete[]; the
# nothrow forms _Znwm…RKSt9nothrow_t are prefix-caught) + libc + all pthread locks + throw
# + STDIO (fprintf/printf/puts/fwrite/fflush/write — the Rule-2 stdio-mutex hazard on a
# latency path; I-1 found a cold fprintf on Regime_Classify + Notify's queue-full fprintf
# that this detector was blind to — under-enumeration, same class as the AVX/FMA miss).
FORBIDDEN_CALL = re.compile(
    r"<(_?malloc|_?free|_?calloc|_?realloc|reallocarray|aligned_alloc|posix_memalign|memalign|valloc|pvalloc"
    r"|_Znwm|_Znwj|_Znam|_Znaj|_ZdlPv|_ZdaPv|__libc_|pthread_mutex|pthread_cond|pthread_rwlock|pthread_spin|__cxa_throw"
    r"|f?printf|vf?printf|fwrite|fputs|fputc|puts|putchar|fflush|\bwrite\b)")
# Compiler-runtime / benign externals (NOT user code that could hide a HARD violation) — a residual
# call to one of these is SEEN + known-safe, so it must NOT fail-loud as "un-analyzable work" (else a
# static-init guard / memset would false-RED a clean fn). Static-init / atexit / stack-protector /
# bulk-mem / crash paths. (Distinct from FORBIDDEN_CALL: these are allowed, just opaque-but-known.)
BENIGN_EXTERN = re.compile(
    r"^(__cxa_guard_acquire|__cxa_guard_release|__cxa_atexit|__cxa_pure_virtual|__stack_chk_fail"
    r"|__assert_fail|abort|memset|memcpy|memmove|memcmp|bcmp|getenv|secure_getenv)$")
# Feature-domain / display double-math runtime calls (libm + compiler-rt) — the H4-SANCTIONED escape:
# transcendentals have NO exact fixed-point form (H4 § feature-domain) and double min/max/round +
# int128↔double conversions are the feature/display seam — the SAME family as the inlined fp2_*/vsqrtsd
# already exempted by source-`allow`, just emitted OUT-OF-LINE as a `call`. KNOWN + benign for the HARD
# invariants (pure math; no malloc/lock/money-arithmetic) and appear ONLY on feature/ML paths (money
# math is integer/decimal udiv256_qr). Skip from the un-analyzed-warm gate — a PRECISE name-whitelist
# that keeps fail-loud ABSOLUTE for unknown ENGINE calls (not a blanket). D-237/s4 (libm-exemption).
FEATURE_MATH_EXTERN = re.compile(
    r"^(sqrtf?|exp2?f?|expm1f?|powf?|logf?|log2f?|log10f?|log1pf?|cbrtf?"
    r"|sinf?|cosf?|tanf?|asinf?|acosf?|atanf?|atan2f?|sinhf?|coshf?|tanhf?|hypotf?|fmaf?"
    r"|fmaxf?|fminf?|fabsf?|llroundf?|lroundf?|roundf?|rintf?|nearbyintf?|truncf?|ceilf?|floorf?|ldexpf?"
    r"|__floattidf|__floattisf|__floatuntidf|__floatunsdidf|__fixdfti|__fixunsdfti)$")

# ── MANIFEST: latency-critical functions (1 row each; registry discipline) ──
#   params/call = a noinline probe-wrapper that FORWARDS args (never constructs them),
#   so the analyzed body is the inlined target + minimal glue.
#   budgets = None until `--update-budgets` measures them (no hand-asserted derived facts).
#   allowlist = data-dependent branches asserted warmup-100%-predicted {addr_hint, why}.
MANIFEST = [
    {
        "name": "ExecutionCore_Tick", "tier": "hot",
        "headers": ["CoreFrameworks/ExecutionCore.hpp"],
        "params": "tt::ExecutionCore<64>* a, const tt::Tick<64>& b",
        "call": "tt::ExecutionCore_Tick<64>(a, b)",
        "allowlist": [],
    },
    {
        "name": "RollingStats_Push", "tier": "slow",
        "headers": ["ML_Headers/RollingStats.hpp"],
        "params": "RollingStats<64,128>* a, FPN_Binary<64> b, FPN_Binary<64> c",
        "call": "RollingStats_Push<64,128>(a, b, c)",
        "allowlist": [],
    },
    # NOTE: EventLoop_RebuildOneCore (the slow-rebuild ORCHESTRATOR) is deliberately NOT a manifest row.
    # The probe (tt::EventLoopState<64>* …22 args) compiles + the .isra-follow reaches its real ~4617-instr
    # body — but it INLINES the WHOLE slow ML+bandit+strategy+persistence pipeline → ~190 signals: the
    # 1645 floats/154 divs are all feature-domain H4-exempt (~50 ML/feature source files) BUT it also
    # surfaces file-I/O (fopen/fclose/rename/unlink) + system() + time/locale on the slow path (FINDING
    # B2, task #18 — triage cold/sanctioned). Gating the orchestrator floods + would mask those; a
    # standalone probe also over-inlines vs the real multi-TU build. The latency-critical KERNELS are the
    # gate-able unit (RollingStats_Push + Regime_Classify below; expand per the per-cycle kernel set).
    # Decided D-237/s4 dogfood: manifest KERNELS, not the orchestrator.
    {
        "name": "Regime_Classify", "tier": "slow",
        "headers": ["CoreFrameworks/ControllerEventLoop.hpp"],   # pulls in RegimeDetector + the complete ControllerConfig/RegimeState/RegimeSignals
        "params": "RegimeState<64>* a, const RegimeSignals<64>* b, const ControllerConfig<64>* c",
        "call": "Regime_Classify<64>(a, b, c)",
        "allowlist": [],
        # Exemptions now travel WITH the code as `// [LAT_EXEMPT]` source markers (shift-robust; an
        # E.1.2 insert shifted the old RegimeDetector.hpp:642 fprintf allow to :708 → false BLOCK):
        #   · the TT_REGIME_DEBUG env-gated cold-debug fprintf  (Strategies/RegimeDetector.hpp)
        #   · fp2_to_double — the feature/display double-conversion seam, all 18 regime-score floats  (FixedPoint/FixedPointN.hpp)
    },
    {   # ML ridge-blend weight kernel — bounded (1097 instr), NOT an orchestrator; its Cholesky sqrt
        # inlines to vsqrtsd (exemptable) rather than a libm `call sqrt`, so it's a clean gate-unit.
        "name": "RidgeBlender_Compute", "tier": "slow",
        "headers": ["ML_Headers/RidgeBlender.hpp"],
        "params": "RidgeWeights<64>* a, const double* b, const double* c, int d, double e, double f, double g",
        "call": "RidgeBlender_Compute<64>(a, b, c, d, e, f, g)",
        "allowlist": [],
        "allow": [
            "RidgeBlender.hpp",        # N=8 Cholesky risk-parity solve — feature-domain double math (Σ corr matrix, μ net-IC, weight renorm); not money
            # fp2_from_double — the feature↔double output-weight seam (FPN_FromDouble) — now exempt via
            # `// [LAT_EXEMPT]` markers at the conversion ops in FixedPoint/FixedPointN.hpp (shift-robust; H4-exempt).
        ],
    },
    {   # ML confidence scorer — 3-factor IC×Freshness×Stability; bounded (64 instr). libm exp
        # (ConfidenceScore.hpp:335) / sqrt (:320) gate-able via FEATURE_MATH_EXTERN (unanalyzed-warm=0).
        "name": "ConfidenceScorer_Compute", "tier": "slow",
        "headers": ["ML_Headers/ConfidenceScore.hpp"],
        "params": "ConfidenceScorer* a, double b",
        "call": "ConfidenceScorer_Compute(a, b)",
        "allowlist": [],
        "allow": [
            "ConfidenceScore.hpp",     # RollingIC/RollingRMSE + Confidence_* feature-domain double math (Spearman corr, RMSE, freshness/stability) — not money
        ],
    },
    {   # ML confidence scorer — 4-factor composite IC×Freshness×Capacity×Stability; bounded (98 instr).
        "name": "ConfidenceScorer_ComputeComposite", "tier": "slow",
        "headers": ["ML_Headers/ConfidenceScore.hpp"],
        "params": "ConfidenceScorer* a, uint64_t b",
        "call": "ConfidenceScorer_ComputeComposite(a, b)",
        "allowlist": [],
        "allow": [
            "ConfidenceScore.hpp",     # 4-factor composite confidence — feature-domain double math (IC/freshness/capacity/stability) — not money
        ],
    },
    {   # ML ridge correlation finalize — O(N²) corr-from-sums, N=8; bounded (815 instr). The 8× std
        # sqrt (RidgeBlender.hpp:411/:420) inline to vsqrtsd (no libm call); unanalyzed-warm=0.
        "name": "RidgeBlender_FinalizeCorrFromSums", "tier": "slow",
        "headers": ["ML_Headers/RidgeBlender.hpp"],
        "params": "double (*a)[MAX_RIDGE_MODELS], const double* b, const double (*c)[MAX_RIDGE_MODELS], uint64_t d, int e",
        "call": "RidgeBlender_FinalizeCorrFromSums<64>(a, b, c, d, e)",
        "allowlist": [],
        "allow": [
            "RidgeBlender.hpp",        # N=8 correlation finalize — feature-domain double math (mean/var/cov/corr from sum-of-squares) — not money
        ],
    },
    # NOT manifested (kernel-granularity, dogfood-verified s4):
    #  · RidgeBlender_OnlineCycleStep — orchestrator-scale (1910 instr, inlines update+finalize+Cholesky);
    #    its AVX-512 floats clear via an avx512fintrin.h allow, but it retains an unresolvable `.text.unlikely`
    #    tail-jmp (RidgeBlender.hpp:439) the fail-loud won't certify. Its bounded math IS covered by
    #    RidgeBlender_FinalizeCorrFromSums above (gate the sub-kernel, not the orchestrator).
    #  · Model_Predict* (XGBoost inference, ModelInference.hpp:733) — KNOWN COVERAGE GAP. Under prod flags
    #    (no -DUSE_XGBOOST) it's a vacuous stub; with -DUSE_XGBOOST it's 39 instr = 3 external XGBoost C-API
    #    calls (XGDMatrixCreateFromMat/XGBoosterPredict/XGDMatrixFree) + NO engine compute underneath → not
    #    actionable to gate (verified s4). If ever wanted: a per-row extra_flags + an XGBOOST_API_EXTERN
    #    name-whitelist (sketch in the decision log). Homed gap, not a row.
]


def compile_and_disasm(row):
    """Compile a noinline probe-wrapper (PRODUCTION flags) + return its disassembly lines."""
    inc = "\n".join(f'#include "{h}"' for h in row["headers"])
    prelude = row.get("prelude", "")   # optional extra TU code (the --selftest teeth define helpers here)
    src = (
        f"{inc}\n{prelude}\n"
        f'extern "C" __attribute__((noinline)) void probe_fn({row["params"]}) {{\n'
        f'    {row["call"]};\n'
        f"}}\n"
    )
    import tempfile
    with tempfile.TemporaryDirectory(dir=ENGINE) as td:  # in-repo tree (/tmp may be noexec — LANDMINE)
        cpp = os.path.join(td, "probe.cpp")
        obj = os.path.join(td, "probe.o")
        with open(cpp, "w") as f:
            f.write(src)
        comp = subprocess.run([CXX, *FLAGS, "-g", "-c", cpp, "-o", obj], capture_output=True, text=True, cwd=ENGINE)
        if comp.returncode != 0:
            errs = [l.strip() for l in comp.stderr.splitlines() if "error:" in l]
            tail = comp.stderr.strip().splitlines()
            return None, (errs[0] if errs else (tail[-1] if tail else "compile failed"))
        # -r = relocations: an UNLINKED .o shows an external `call malloc` as `call <placeholder>`
        # with the real target only in a reloc line — without -r the forbidden-call check is VACUOUS
        # (the teeth caught this). -l = source lines for the per-branch "why".
        dis = subprocess.run(["objdump", "-d", "-r", "-l", "--no-show-raw-insn", obj], capture_output=True, text=True)
        if dis.returncode != 0:
            return None, "objdump failed"
        return dis.stdout, None


INSTR_RE = re.compile(r"^\s+([0-9a-f]+):\s+([a-z][a-z0-9.]*)\s*(.*)$")
SRCLINE_RE = re.compile(r"^(/?\S+\.(?:hpp|cpp|h|cc)):(\d+)")
TARGET_RE = re.compile(r"^([0-9a-f]+)\b")
RELOC_RE = re.compile(r"R_X86_64\w*\s+(\S+)")  # objdump -r reloc line → the external-call target symbol
                                               # (e.g. `malloc-0x4`); INVISIBLE in an unlinked .o without -r
SYMHDR_RE = re.compile(r"^[0-9a-f]+ <(.+)>:$")  # a function-block header line: `<addr> <symbol>:`
CALLTGT_RE = re.compile(r"<([^>+]+)(?:\+0x[0-9a-f]+)?>")  # the resolved `<sym(+off)?>` operand of a same-TU call/jmp
CLONE_SUFFIX = re.compile(r"\.(?:isra|constprop|part|cold)\.\d+$")  # GCC IPA-clone suffixes (.isra.0 …)


def _strip_clone(sym):
    return CLONE_SUFFIX.sub("", sym)


def _defined_map(disasm):
    """{symbol AND its clone-stripped form → full defined symbol} for every fn block in the .o.
    objdump -d only disassembles .text, so data symbols (vtables/typeinfo) never enter here — the
    transitive/target follow is .text-only BY CONSTRUCTION (A-1's data-symbol-safety note; pinned
    by this comment so a future -d→-D change can't silently break it)."""
    d = {}
    for ln in disasm.splitlines():
        m = SYMHDR_RE.match(ln.strip())
        if m:
            full = m.group(1)
            d[full] = full
            d.setdefault(_strip_clone(full), full)
    return d


def _call_target(ops, reloc):
    """The symbol a `call` goes to — the -r reloc (unlinked external) or the resolved `<sym+off>`
    operand (same-TU, incl. an .isra clone reached without a reloc — I-1's evasion). None ⟹ a
    register/relative target (an indirect call, flagged separately)."""
    if reloc:
        return re.sub(r"[-+]0x[0-9a-f]+$", "", reloc)
    m = CALLTGT_RE.search(ops)
    return m.group(1) if m else None


def analyze(disasm, symbol="probe_fn"):
    """Extract `symbol`'s body (default the probe wrapper; or a followed out-of-line callee),
    classify branches per category, count invariants."""
    lines = disasm.splitlines()
    body = []          # (addr:int, mnemonic, operands, srcline)
    in_fn = False
    cur_src = None
    for ln in lines:
        if f"<{symbol}>:" in ln:
            in_fn = True
            continue
        if not in_fn:
            continue
        if ln.strip() == "":
            break
        rm = RELOC_RE.search(ln)
        if rm and body:                  # reloc line → names the PRECEDING instruction's external target
            body[-1][4] = rm.group(1)     # (an unlinked `call <placeholder>` whose real target is e.g. `malloc`)
            continue
        sm = SRCLINE_RE.match(ln.strip())
        if sm:
            # Retain the FULL path (was basename-discarded) so the marker-reader can OPEN the file at
            # this line — a `// [LAT_EXEMPT]` marker makes an exemption travel WITH the code (shift-robust)
            # instead of a brittle absolute FILE:LINE that an unrelated insertion silently shifts out from
            # under. Substring `allow` still matches (basename ⊂ fullpath); `_disp` basenames it for display.
            cur_src = f"{sm.group(1)}:{sm.group(2)}"
            continue
        m = INSTR_RE.match(ln)
        if m:
            body.append([int(m.group(1), 16), m.group(2), m.group(3).strip(), cur_src, None])
    if not body:
        return None
    addrs = [e[0] for e in body]
    lo, hi = addrs[0], addrs[-1]
    span = max(1, hi - lo)
    cold_start = lo + int(span * 0.75)   # heuristic: gcc tails cold blocks (upper quartile)

    cats = {"loop": [], "rare_cold": [], "data_dependent": []}
    calls, ext_calls, indirect_calls, residual, float_srcs, div_srcs, spills = [], [], [], [], [], [], 0
    for addr, mn, ops, src, reloc in body:
        indexed = bool(re.search(r",%\w+,\d", ops))   # (,%idx,scale) = a fn-pointer/jump TABLE = branchless dispatch (OK), not a vtable
        if mn in COND_JUMPS:
            tm = TARGET_RE.match(ops)
            tgt = int(tm.group(1), 16) if tm else addr
            cat = "loop" if tgt < addr else ("rare_cold" if tgt >= cold_start else "data_dependent")
            cats[cat].append((f"{addr:x}", mn, ops, src))
        if mn == "call":
            calls.append((f"{addr:x}", ops, src))
            # forbidden-call: match the linked `<sym>` OR the -r reloc symbol (unlinked .o — the vacuity the teeth caught)
            if FORBIDDEN_CALL.search(ops) or (reloc and FORBIDDEN_CALL.search("<" + reloc)):
                ext_calls.append((f"{addr:x}", ops + (f"  [→ {reloc}]" if reloc else ""), src))
            # residual-call record for the transitive HARD scan (target + warm/cold per addr)
            residual.append({"addr": f"{addr:x}", "warm": addr < cold_start,
                             "target": _call_target(ops, reloc), "src": src})
        if mn == "jmp":
            # a DIRECT tail-`jmp` to ANOTHER body (the void / discarded-result tail-call form) is
            # residual work continuing OUTSIDE this body — capture it like a call so a tail-`jmp
            # malloc` / tail-`jmp <unseen>` can't slip the forbidden + fail-loud gates (the --selftest
            # teeth caught this hole). Intra-function jumps (target == self) are skipped; indirect
            # `jmp *reg` stays a separate finish-item (indistinguishable from a switch jump-table).
            jt = _call_target(ops, reloc)
            if jt and _strip_clone(jt) != _strip_clone(symbol):
                residual.append({"addr": f"{addr:x}", "warm": addr < cold_start, "target": jt, "src": src})
                if FORBIDDEN_CALL.search(ops) or (reloc and FORBIDDEN_CALL.search("<" + reloc)):
                    ext_calls.append((f"{addr:x}", f"jmp {ops}" + (f"  [→ {reloc}]" if reloc else ""), src))
        # indirect CALL through a single fn-pointer / vtable / std::function = the H2 risk → flag.
        # EXCLUDE an indexed `call *(,%idx,scale)` (a fn-pointer TABLE = the sanctioned branchless
        # dispatch). NOTE: indirect TAIL-calls (`jmp *reg`) are deliberately NOT flagged — a GCC
        # `switch` jump-table ALSO compiles to an unindexed `jmp *reg` (the index is in a PRIOR
        # movslq), so jmp* can't be told from a real tail-call without data-flow (a look-back).
        # Flagging jmp* false-RED'd jump-tables (reviewer-caught) → homed finish-item (look-back detect).
        if mn == "call" and "*" in ops and not indexed:
            indirect_calls.append((f"{addr:x}", f"{mn} {ops}", src))
        if FLOAT_OPS.search(mn) or FLOAT_OPS.search(ops):
            float_srcs.append(src or "(no src)")     # record the SOURCE so the per-row `allow` list can exempt by-seam (D-237)
        if DIV_OPS.search(mn + " "):
            div_srcs.append(src or "(no src)")
        # crude stack-spill proxy: a store of a reg to a stack slot beyond the preamble
        if mn == "mov" and re.search(r",\s*-?0x[0-9a-f]+\(%rbp\)", ops) and "%rsp" not in ops:
            spills += 1
    return {
        "instructions": len(body),
        "branches": {k: len(v) for k, v in cats.items()},
        "branch_detail": cats,
        "calls": calls, "ext_calls": ext_calls, "indirect_calls": indirect_calls,
        "residual": residual,
        "float_srcs": float_srcs, "div_srcs": div_srcs,
        "floats": len(float_srcs), "divs": len(div_srcs), "spills": spills,
        "transitive_floats": 0, "transitive_divs": 0, "unanalyzed_warm": [],
        "cold_start_off": cold_start - lo,
        "nonvacuous": len(body) >= NONVACUITY_FLOOR,
    }


def _short(sym):
    s = _strip_clone(sym)
    return (s[:44] + "…") if len(s) > 45 else s


def _target_body_symbol(disasm, defined, call_expr):
    """Find the manifest target fn's OWN out-of-line body symbol — an `inline`-not-`always_inline`
    fn the compiler kept out of line, INCLUDING a GCC `.isra.N`/`.constprop.N` clone reached by a
    resolved jmp with NO relocation (the evasion that let a 19-instr glue wrapper pass — I-1).
    Match the mangled length-prefixed name component (objdump has no -C); extern "C" matches the
    bare name. None ⟹ the target was INLINED into probe_fn (analyze the wrapper). Among matches,
    pick the largest non-vacuous body (a stub/thunk loses to the real .isra clone)."""
    name = re.split(r"[<(]", call_expr.strip())[0].strip().split("::")[-1]
    if not name:
        return None
    needle = f"{len(name)}{name}"          # Itanium length-prefixed component (e.g. 17RollingStats_Push)
    best, best_n, seen = None, -1, set()
    for sym, full in defined.items():
        if sym == "probe_fn" or full in seen:
            continue
        if needle in sym or _strip_clone(sym) == name or sym == name:
            seen.add(full)
            a = analyze(disasm, full)
            if a and a["nonvacuous"] and a["instructions"] > best_n:
                best, best_n = full, a["instructions"]
    return best


def analyze_path(disasm, symbol, defined, depth=0, visited=None):
    """analyze() + bounded TRANSITIVE HARD-invariant recursion into residual calls to DEFINED same-TU
    bodies — closes A-1's "a div/float/forbidden one `call` level deeper than the analyzed body is
    invisible". instr/branch counts stay on the PRIMARY body (no merge — avoids semantic mush); only
    the HARD findings (float/div/forbidden/indirect) bubble up. A residual call to a body we CANNOT
    see (not in this .o, not forbidden, not a benign compiler-runtime extern) is recorded as
    un-analyzed work → main FAILS LOUD rather than certify a false green (the Class-51 backstop).

    The recurse/fail-loud decision is STRUCTURAL (defined-callee / forbidden / benign-extern), NOT
    positional — R-A found the `lo + 0.75*span` cold-quartile heuristic mis-classifies the FINAL
    delegating `call` of a compute-then-delegate fn as 'cold' and silently skipped it, defeating the
    whole transitive + fail-loud point for the dominant slow-path shape (work, then delegate to an
    out-of-line FPN kernel). Position is the right axis for classifying a conditional BRANCH
    (rare-cold vs data-dependent), but the WRONG axis for 'is this work analyzed'."""
    visited = set() if visited is None else visited
    a = analyze(disasm, symbol)
    if a is None or depth >= MAX_FOLLOW_DEPTH:
        return a
    visited.add(symbol)
    for rcall in a["residual"]:
        tgt = rcall["target"]
        if tgt is None or FORBIDDEN_CALL.search("<" + tgt + ">"):
            continue                        # register-indirect (flagged elsewhere) or already-counted forbidden
        full = defined.get(tgt) or defined.get(_strip_clone(tgt))
        if full and full not in visited:
            sub = analyze_path(disasm, full, defined, depth + 1, visited)   # analyzable → recurse (ANY position)
            if sub:
                a["float_srcs"] += sub["float_srcs"]; a["transitive_floats"] += len(sub["float_srcs"])
                a["div_srcs"] += sub["div_srcs"];     a["transitive_divs"] += len(sub["div_srcs"])
                a["floats"] = len(a["float_srcs"]); a["divs"] = len(a["div_srcs"])
                a["ext_calls"] += [(c[0], c[1] + f"  [via {_short(full)}]", c[2]) for c in sub["ext_calls"]]
                a["indirect_calls"] += [(c[0], c[1] + f"  [via {_short(full)}]", c[2]) for c in sub["indirect_calls"]]
                a["unanalyzed_warm"] += sub["unanalyzed_warm"]
        elif not full and not BENIGN_EXTERN.match(_strip_clone(tgt)) and not FEATURE_MATH_EXTERN.match(_strip_clone(tgt)):
            a["unanalyzed_warm"].append((rcall["addr"], tgt, rcall["src"]))   # unseen + not benign + not feature-math → fail loud (any position)
    return a


def _analyze_probe(disasm, call_expr):
    """Pick the body to analyze (the out-of-line target if the compiler kept it out of line, else
    the inlined probe_fn wrapper) + run the transitive scan. Returns (analysis, followed|None).
    Shared by main + --selftest so the teeth exercise the REAL follow path."""
    defined = _defined_map(disasm)
    target = _target_body_symbol(disasm, defined, call_expr)
    if target:
        a = analyze_path(disasm, target, defined)
        if a and a["nonvacuous"]:
            return a, target
    return analyze_path(disasm, "probe_fn", defined), None


def load_budgets():
    if os.path.exists(BUDGETS_SIDECAR):
        with open(BUDGETS_SIDECAR) as f:
            return json.load(f)
    return {}


def _disp(src):
    """basename:line for HUMAN display. The full path is retained in `src` only so the marker-reader
    can open the file; operators read the basename (matches the pre-shift-robust output)."""
    if not src:
        return "(no src)"
    path, sep, lno = src.rpartition(":")
    return f"{os.path.basename(path)}:{lno}" if (sep and path) else src


def _has_lat_exempt_marker(srcfull):
    """SHIFT-ROBUST exemption: True iff the resolved source line of `srcfull` (a `path:line` from
    objdump -l) carries a `// [LAT_EXEMPT]` marker. The marker travels WITH the code, so an unrelated
    insertion that shifts the line can never break the exemption — the brittleness the absolute
    FILE:LINE `allow` had (an E.1.2 persist-delegate insert shifted a cold-debug fprintf :642→:708 →
    false BLOCK). Fail-CLOSED: any error (missing file / non-numeric or out-of-range line / no path) →
    False, so a marker we cannot actually READ never yields a phantom exemption."""
    if not srcfull or ":" not in srcfull:
        return False
    path, _, lno = srcfull.rpartition(":")
    if not path or not lno.isdigit():
        return False
    line_no = int(lno)
    # objdump -l paths are absolute (may carry `..` segments the OS resolves) or compile-dir relative;
    # try as-given, then ENGINE-rooted, so the reader works regardless of CWD / FOXML_ENGINE.
    for p in ([path] if os.path.isabs(path) else [os.path.join(ENGINE, path), path]):
        try:
            with open(p, "r", errors="replace") as f:
                lines = f.readlines()
        except OSError:
            continue
        return 1 <= line_no <= len(lines) and bool(re.search(r"\[LAT_EXEMPT\]", lines[line_no - 1]))
    return False


def _unallowed(items, allow, key=lambda x: x):
    """Items whose `-l` source matches NO `allow` pattern — the per-row SOURCE-keyed exemption (D-237).
    ONE allowlist concept shared by float / div / forbidden, mirroring the data-dependent-branch
    allowlist. A blank `allow` ⟹ nothing exempt (every signal counts). Matched by substring so a
    file-level pattern (`RidgeBlender.hpp`) covers every line in it, a file:line (`FixedPointN.hpp:1890`)
    is exact — so a NEW money-float in a mixed file (keyed file:line) still REDs."""
    return [x for x in items if not any(p and p in (key(x) or "") for p in allow)]


def _unallowed_hard(a, row):
    """The (float, div, forbidden) source-lists the HARD gate fires on — SINGLE SOURCE so the printed
    summary counts can never disagree with the gate verdict. Exemption policy (D-237 + shift-robust):
      · float / div  → source-`allow` substring (pure-feature FILES) OR a `// [LAT_EXEMPT]` marker.
      · forbidden    → MARKER ONLY. NEVER a file-level (or any) `allow` — a file-level forbidden allow
        is the 'mode-D' hole (a future malloc/stdio inlined from a feature-allowed file would silently
        mask); the per-line marker keeps forbidden exemptions EXACT + shift-robust (it strictly replaces
        the old brittle absolute FILE:LINE — the marker resolves at the CODE, never a fixed offset)."""
    allow = (row or {}).get("allow", [])
    uf = [s for s in _unallowed(a["float_srcs"], allow) if not _has_lat_exempt_marker(s)]
    ud = [s for s in _unallowed(a["div_srcs"], allow) if not _has_lat_exempt_marker(s)]
    uec = [c for c in a["ext_calls"] if not _has_lat_exempt_marker(c[2])]
    return uf, ud, uec


def _hard_findings(a, tier, row=None):
    """The HARD-invariant gate verdicts (independent of budgets), as (label, detail) — non-empty ⟹
    RC=1. SINGLE SOURCE (with _unallowed_hard) so --selftest asserts the GATE fires, not merely that a
    detector COUNTS (R-A: the div detector counted/printed/teethed while main NEVER gated it — a
    pure-integer idiv exited 'clean'). Exemption: float/div by source-`allow` OR `// [LAT_EXEMPT]`
    marker; forbidden by MARKER ONLY (mode-D closure — no file-level forbidden allow); indirect +
    un-analyzed-warm gate ABSOLUTELY (not exemptable). div = H4/§5 (the certified path is the branchless
    udiv256_qr reciprocal, never hardware idiv)."""
    uf, ud, uec = _unallowed_hard(a, row)
    out = []
    if uf:
        out.append(("H4", f"{len(uf)} non-exempt scalar-float on a {tier} money path (e.g. {_disp(uf[0])})"
                    + (f"; {a['transitive_floats']} via a called helper" if a["transitive_floats"] else "")))
    if ud:
        out.append(("H4/§5", f"{len(ud)} non-exempt div/idiv on a {tier} path — use the certified udiv256_qr (e.g. {_disp(ud[0])})"))
    if uec:
        # ALSO surface the resolved file:line + the fix hint so the operator adds the marker WHERE it
        # travels with the code (vs the old FILE:LINE allow the E.1.2 insert shifted out from under).
        locs = [_disp(c[2]) for c in uec if c[2]]
        hint = ("  @ " + ", ".join(locs) + "  —  add `// [LAT_EXEMPT]` at " + locs[0]) if locs else ""
        out.append(("H1/Rule2", f"forbidden calls: {[c[1] for c in uec][:8]}{hint}"))
    if a["indirect_calls"]:
        out.append(("H2", f"indirect/vtable call(s): {[c[1] for c in a['indirect_calls']][:8]}"))
    if a["unanalyzed_warm"]:
        out.append(("UN-ANALYZED", "residual call(s) to a body not in this .o (can't certify HARD-clean — "
                    f"follow it or manifest it): {[f'{x[0]}:{_short(x[1])}' for x in a['unanalyzed_warm'][:6]]}"))
    return out


def main(argv):
    show_asm = "--asm" in argv
    update = "--update-budgets" in argv
    selftest = "--selftest" in argv
    print("=" * 70)
    print(" check_latency_path_conformance.py — static latency-path analyzer")
    print(f"   PRODUCTION flags: {' '.join(FLAGS)}  (no LATENCY_PROFILING)")
    print("=" * 70)

    budgets = load_budgets()
    new_budgets = {}
    rc = 0
    for row in MANIFEST:
        name, tier = row["name"], row["tier"]
        print(f"\n── {name}  [{tier} path] " + "─" * (48 - len(name) - len(tier)))
        disasm, err = compile_and_disasm(row)
        if err:
            print(f"  ⚠️  PROBE-FAIL — {err}")
            rc = max(rc, 2)
            continue
        # Pick the REAL body: the out-of-line target (incl. an .isra/.constprop clone) if the
        # compiler kept it out of line, else the inlined probe_fn wrapper — then transitively scan
        # warm defined callees for HARD violations (closes the .isra-evasion + transitive holes).
        a, followed = _analyze_probe(disasm, row["call"])
        if a is None or not a["nonvacuous"]:
            print(f"  ❌ NON-VACUITY FAIL — probe body not found / optimized away "
                  f"({0 if a is None else a['instructions']} instr < floor {NONVACUITY_FLOOR}). "
                  f"This would be a vacuously-green guard (Class-51) — refusing to pass.")
            rc = max(rc, 1)
            continue
        if followed:
            print(f"  ↳ target out-of-line → analyzed its own body `{_short(followed)}` (not the glue wrapper)")
        dd = a["branches"]["data_dependent"]
        allow = len(row.get("allowlist", []))
        unallowed = max(0, dd - allow)
        print(f"  instructions={a['instructions']}  (cold tail ≥ +{a['cold_start_off']}B)")
        print(f"  branches: loop={a['branches']['loop']}  rare-cold={a['branches']['rare_cold']}  "
              f"DATA-DEPENDENT-WARM={dd}  (allowlisted={allow} → unallowed={unallowed})")
        allow = row.get("allow", [])
        ufl, udl, uecl = _unallowed_hard(a, row)   # SINGLE SOURCE with the gate (source-`allow` + marker policy)
        uf, ud, uec = len(ufl), len(udl), len(uecl)
        ftr = f"+{a['transitive_floats']}t" if a["transitive_floats"] else ""
        print(f"  H4 float={a['floats']}{ftr} (exempt→{a['floats'] - uf} unallowed→{uf})  "
              f"div={a['divs']} (unallowed→{ud})  spills={a['spills']}  "
              f"forbidden={len(a['ext_calls'])} (unallowed→{uec})  indirect={len(a['indirect_calls'])}  "
              f"unanalyzed-warm={len(a['unanalyzed_warm'])}"
              + (f"   [allow: {len(allow)} exempt sources]" if allow else ""))

        # invariant gates (hard — independent of budgets; merged transitively across defined callees;
        # float/div/forbidden exempted by the row's source-`allow` list per D-237). SINGLE SOURCE
        # (_hard_findings) so --selftest asserts the GATE fires, not just the detector count.
        for label, detail in _hard_findings(a, tier, row):
            print(f"  ❌ {label} — {detail}"); rc = max(rc, 1)

        # the headline: data-dependent-warm branches, ASM per category
        print(f"\n  ▼ DATA-DEPENDENT-WARM branches (the jitter risk → drive to 0; each must be "
              f"allowlisted 'warmup-100%-predicted' + PMU-confirmed):")
        if not a["branch_detail"]["data_dependent"]:
            print("      (none)")
        for addr, mn, ops, src in a["branch_detail"]["data_dependent"]:
            print(f"      {addr:>6}:  {mn:<5} {ops:<22}  {_disp(src)}")
        if show_asm:
            for cat in ("loop", "rare_cold"):
                print(f"\n  ▸ {cat} branches:")
                for addr, mn, ops, src in a["branch_detail"][cat]:
                    print(f"      {addr:>6}:  {mn:<5} {ops:<22}  {_disp(src)}")

        # budget ratchet (report-only until --update-budgets sets a baseline)
        new_budgets[name] = {"instructions": a["instructions"], "data_dependent": dd}
        b = budgets.get(name)
        if b and not update:
            if a["instructions"] > b["instructions"]:
                print(f"  ❌ RATCHET — instructions {a['instructions']} > budget {b['instructions']}"); rc = max(rc, 1)
            if dd > b["data_dependent"]:
                print(f"  ❌ RATCHET — data-dependent branches {dd} > budget {b['data_dependent']}"); rc = max(rc, 1)
        elif not b:
            print("  ℹ️  report-only (no budget baseline yet; run --update-budgets to set the ratchet).")

    if update:
        missing = [r["name"] for r in MANIFEST if r["name"] not in new_budgets]
        os.makedirs(os.path.dirname(BUDGETS_SIDECAR), exist_ok=True)
        with open(BUDGETS_SIDECAR, "w") as f:
            json.dump(new_budgets, f, indent=2)
        print(f"\n  ✅ budgets written ({len(new_budgets)}/{len(MANIFEST)} manifest rows) → {os.path.relpath(BUDGETS_SIDECAR, ENGINE)}")
        if missing:   # reviewer-caught: a skipped row was silently dropped from the ratchet
            print(f"  ⚠️  INCOMPLETE BASELINE — rows skipped (probe-fail / non-vacuity) with NO ratchet: "
                  f"{missing}. Fix them (e.g. the slow-path callee-symbol follow) before trusting the "
                  f"grandfathered baseline (D-236).")
            rc = max(rc, 1)

    if selftest:
        # TEETH — every detector MUST fire on an injected probe (D-234 lesson 3: the teeth
        # ARE the guard against under-enumeration; only because the float probe existed did
        # the AVX/FMA hole surface). Each case: compile a probe that triggers the detector,
        # analyze, assert it fired. NOTE: the `spills` check is an inherently-heuristic
        # ADVISORY count (frame-relative stores aren't all spills) → NOT strict-teeth'd here.
        gates = lambda a, allow=[]: {l for l, _ in _hard_findings(a, "hot", {"allow": allow})}   # HARD gate-labels that FIRED; allow = source-exempt patterns
        cases = [
            ("H4 scalar-float (AVX/FMA)", {"headers": ["cstdint"], "params": "double* a, double b",
                                           "call": "*a = (*a) * b + 1.5"},
             lambda a: "H4" in gates(a)),
            ("div (GATE, not just count)", {"headers": ["cstdint"], "params": "long* a, long b, long c",
                                           "call": "*a = b / c"},
             lambda a: "H4/§5" in gates(a)),                                    # asserts the GATE (HOLE #1 regression-proof)
            ("forbidden-call (malloc)",   {"headers": ["cstdlib"], "params": "void** a",
                                           "call": "*a = std::malloc(64)"},
             lambda a: "H1/Rule2" in gates(a)),
            ("indirect-call/vtable",      {"headers": ["cstdint"], "params": "void(*fp)(int), int x, int* s",
                                           "call": "fp(x); *s = 1"},   # trailing store → a real `call *`, not a tail-`jmp *`
             lambda a: "H2" in gates(a)),
            ("branch-detection",          {"headers": ["cstdint"], "params": "int b, void(*f)()",
                                           "call": "if (b > 7) f()"},
             lambda a: sum(a["branches"].values()) > 0),                        # detector (branches feed the ratchet, not a hard gate)
            ("non-vacuity (empty body)",  {"headers": ["cstdint"], "params": "int x", "call": "(void)x"},
             lambda a: not a["nonvacuous"]),                                    # the non-vacuity REFUSAL gate
            # ── reach + transitive + fail-loud teeth (the post-3:3 finds; each asserts the GATE) ──
            ("out-of-line follow + div",  {"prelude": 'extern "C" __attribute__((noinline)) void oobf_div(long* o, long x, long y){ *o = x / (y | 1); }',
                                           "headers": [], "params": "long* a, long b, long c", "call": "oobf_div(a, b, c)"},
             lambda a: "H4/§5" in gates(a)),                                    # follow to the out-of-line body + GATE on its div
            ("transitive div (1 call deeper)", {"prelude": 'extern "C" __attribute__((noinline)) long ttd_deep(long x, long y){ return x / (y | 1); }\n'
                                                           'extern "C" __attribute__((noinline)) void ttd_mid(long* o, long b, long c){ *o = ttd_deep(b, c) + b; }',
                                           "headers": [], "params": "long* a, long b, long c", "call": "ttd_mid(a, b, c)"},
             lambda a: "H4/§5" in gates(a) and a["transitive_divs"] > 0),       # the div hides one `call` deeper than the body
            ("late-delegate div (cold-quartile regression)", {"prelude": 'extern "C" __attribute__((noinline)) long ld_kernel(long x, long y){ return x / (y | 1); }\n'
                                                           'extern "C" __attribute__((noinline)) void ld_body(long* o, long b, long c){ long s=b; for(long i=0;i<c;i++){ s=(s*1103515245+12345)^(s>>7); } *o = s + ld_kernel(s, c); }',
                                           "headers": [], "params": "long* a, long b, long c", "call": "ld_body(a, b, c)"},
             lambda a: "H4/§5" in gates(a) and a["transitive_divs"] > 0),       # HOLE #2: the delegating call is LATE (post-bulk-work) → must still recurse
            ("un-analyzed work (undefined extern)", {"prelude": 'extern "C" long ttu_extern(long);',
                                           "headers": [], "params": "long* a, long b", "call": "*a += ttu_extern(b)"},
             lambda a: "UN-ANALYZED" in gates(a)),                             # unseen call → fail-loud GATE
            ("benign extern NOT fail-loud (memset)", {"headers": ["cstring"], "params": "char* a, unsigned long n",
                                           "call": "memset(a, 0, n)"},          # variable n → a real memset CALL (not inlined)
             lambda a: "UN-ANALYZED" not in gates(a)),                          # a SEEN benign runtime extern must NOT false-RED
            ("feature-math extern NOT fail-loud (libm exp)", {"prelude": 'extern "C" double exp(double);',
                                           "headers": [], "params": "double* a, double b", "call": "*a = exp(b)"},
             lambda a: "UN-ANALYZED" not in gates(a)),                          # a libm transcendental = the H4 feature-domain escape — exempt from fail-loud (not an un-analyzable risk)
            ("stdio forbidden-call (fprintf)", {"headers": ["cstdio"], "params": "int x", "call": 'fprintf(stderr, "%d", x)'},
             lambda a: "H1/Rule2" in gates(a)),                                 # the Rule-2 stdio hazard the detector was blind to
            # ── source-`allow` exemption teeth (D-237 — the precision proof) ──
            ("source-allow: suppresses ONLY the matching source", {"prelude": 'extern "C" __attribute__((noinline)) void exf_div(long* o, long x, long y){ *o = (x * x) / (y | 1); }',
                                           "headers": [], "params": "long* a, long b, long c", "call": "exf_div(a, b, c)"},
             lambda a: "H4/§5" in gates(a)                                      # un-allowed → REDs
                       and "H4/§5" not in gates(a, allow=["probe.cpp"])         # allow its source → exempt
                       and "H4/§5" in gates(a, allow=["OtherFile.hpp"])),       # a NON-matching allow does NOT suppress (precise, not a blanket mute)
            ("forbidden NOT allow-exemptable (marker-only)", {"headers": ["cstdio"], "params": "int x", "call": 'fprintf(stderr, "%d", x)'},
             lambda a: "H1/Rule2" in gates(a, allow=["probe.cpp"])),            # NO `allow` (file-level OR file:line) masks a forbidden call — marker-ONLY (mode-D closure; the shift-robust replacement)
        ]
        all_ok = True
        print("\n  --selftest (teeth — each asserts its GATE fires (RC), not just the detector count):")
        for name, probe, want in cases:
            d, e = compile_and_disasm(probe)
            a, _ = _analyze_probe(d, probe["call"]) if (e is None and d) else (None, None)
            ok = (e is None) and (a is not None) and want(a)
            print(f"      {'✅' if ok else '❌'} {name}" + (f"  (PROBE-FAIL: {e})" if e else ""))
            all_ok = all_ok and ok

        # ── source-MARKER teeth (the shift-robust exemption — the crux of this fix). Can't ride the
        # compile path: that probe's tempdir is DELETED by gate-time, so the marker-reader would find
        # nothing. Drive the REAL gate (_hard_findings → _unallowed_hard → _has_lat_exempt_marker) with
        # a synthetic analysis over a PERSISTENT marked fixture — exercises the whole marker mechanism. ──
        import tempfile
        def _fixture(fx_lines):
            fd, path = tempfile.mkstemp(suffix=".hpp", dir=ENGINE, text=True)   # abs path (ENGINE is abspath)
            with os.fdopen(fd, "w") as fh:
                fh.write("\n".join(fx_lines) + "\n")
            return path
        def _a_forbidden(src):   # minimal analysis carrying ONE forbidden ext_call attributed to `src`
            return {"float_srcs": [], "div_srcs": [], "ext_calls": [("100", "call <fprintf>", src)],
                    "indirect_calls": [], "unanalyzed_warm": [], "transitive_floats": 0}
        marked = _fixture(["// pad line 1", 'fprintf(stderr, "x");  // [LAT_EXEMPT]_[selftest]', "// pad line 3"])
        shifted = _fixture(["// pad"] * 40 + ['fprintf(stderr, "x");  // [LAT_EXEMPT]_[selftest]'])  # SAME call, now line 41
        marker_cases = [
            ("marker: a forbidden line WITH `// [LAT_EXEMPT]` → exempt",
             "H1/Rule2" not in gates(_a_forbidden(f"{marked}:2"))),
            ("marker: a forbidden line WITHOUT the marker → RED",
             "H1/Rule2" in gates(_a_forbidden(f"{marked}:1"))),
            ("marker: a file-level `allow` does NOT exempt a forbidden call (mode-D closure)",
             "H1/Rule2" in gates(_a_forbidden(f"{marked}:1"), allow=[os.path.basename(marked)])),
            ("marker: SHIFT-ROBUST — the same marked call at a different line offset stays exempt",
             "H1/Rule2" not in gates(_a_forbidden(f"{shifted}:41"))),
        ]
        for name, ok in marker_cases:
            print(f"      {'✅' if ok else '❌'} {name}")
            all_ok = all_ok and ok
        os.remove(marked); os.remove(shifted)

        print("  --selftest:", "✅ ALL teeth fire" if all_ok
              else "❌ a detector did NOT fire — under-enumeration risk (D-234 lesson 3)")
        if not all_ok:
            return 3

    print("\n" + ("✅ conformance clean" if rc == 0 else f"⚠️  exit {rc} — see flags above"))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
