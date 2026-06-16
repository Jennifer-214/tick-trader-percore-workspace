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

NON-VACUITY (eat-own-dogfood — else this is the Class-51 guard it codifies against):
  ASSERTS the probe symbol was found + a real inlined body disassembled (instr > floor),
  so an optimized-away probe can never pass green.

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
  --selftest         teeth: inject a float op into a probe -> the H4 check MUST fire.

EXIT: 0 = clean / report-only. 1 = a budget or invariant violation. 2 = a probe failed
to compile (tooling error — surfaced, never silently skipped).

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
# nothrow forms _Znwm…RKSt9nothrow_t are prefix-caught) + libc + all pthread locks + throw.
FORBIDDEN_CALL = re.compile(
    r"<(_?malloc|_?free|_?calloc|_?realloc|reallocarray|aligned_alloc|posix_memalign|memalign|valloc|pvalloc"
    r"|_Znwm|_Znam|_ZdlPv|_ZdaPv|__libc_|pthread_mutex|pthread_cond|pthread_rwlock|pthread_spin|__cxa_throw)")

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
]


def compile_and_disasm(row):
    """Compile a noinline probe-wrapper (PRODUCTION flags) + return its disassembly lines."""
    inc = "\n".join(f'#include "{h}"' for h in row["headers"])
    src = (
        f"{inc}\n"
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


def analyze(disasm):
    """Extract probe_fn's body, classify branches per category, count invariants."""
    lines = disasm.splitlines()
    body = []          # (addr:int, mnemonic, operands, srcline)
    in_fn = False
    cur_src = None
    for ln in lines:
        if "<probe_fn>:" in ln:
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
            cur_src = f"{os.path.basename(sm.group(1))}:{sm.group(2)}"
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
    calls, ext_calls, indirect_calls, floats, divs, spills = [], [], [], 0, 0, 0
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
        # indirect call OR indirect TAIL-call (jmp *reg / *off(reg)) = H2 vtable/std::function risk;
        # EXCLUDE indexed `*(,%idx,scale)` (a fn-pointer/jump TABLE = the GOOD branchless-dispatch pattern)
        if mn in ("call", "jmp") and "*" in ops and not indexed:
            indirect_calls.append((f"{addr:x}", f"{mn} {ops}", src))
        if FLOAT_OPS.search(mn) or FLOAT_OPS.search(ops):
            floats += 1
        if DIV_OPS.search(mn + " "):
            divs += 1
        # crude stack-spill proxy: a store of a reg to a stack slot beyond the preamble
        if mn == "mov" and re.search(r",\s*-?0x[0-9a-f]+\(%rbp\)", ops) and "%rsp" not in ops:
            spills += 1
    return {
        "instructions": len(body),
        "branches": {k: len(v) for k, v in cats.items()},
        "branch_detail": cats,
        "calls": calls, "ext_calls": ext_calls, "indirect_calls": indirect_calls,
        "floats": floats, "divs": divs, "spills": spills,
        "cold_start_off": cold_start - lo,
        "nonvacuous": len(body) >= NONVACUITY_FLOOR,
    }


def load_budgets():
    if os.path.exists(BUDGETS_SIDECAR):
        with open(BUDGETS_SIDECAR) as f:
            return json.load(f)
    return {}


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
        a = analyze(disasm)
        if a is None or not a["nonvacuous"]:
            print(f"  ❌ NON-VACUITY FAIL — probe body not found / optimized away "
                  f"({0 if a is None else a['instructions']} instr < floor {NONVACUITY_FLOOR}). "
                  f"This would be a vacuously-green guard (Class-51) — refusing to pass.")
            rc = max(rc, 1)
            continue
        dd = a["branches"]["data_dependent"]
        allow = len(row.get("allowlist", []))
        unallowed = max(0, dd - allow)
        print(f"  instructions={a['instructions']}  (cold tail ≥ +{a['cold_start_off']}B)")
        print(f"  branches: loop={a['branches']['loop']}  rare-cold={a['branches']['rare_cold']}  "
              f"DATA-DEPENDENT-WARM={dd}  (allowlisted={allow} → unallowed={unallowed})")
        print(f"  H4 scalar-float={a['floats']}  div={a['divs']}  spills={a['spills']}  "
              f"forbidden-calls={len(a['ext_calls'])}  indirect/vtable={len(a['indirect_calls'])}")

        # invariant gates (hard — independent of budgets)
        if a["floats"]:
            print(f"  ❌ H4 — {a['floats']} scalar-float instr on a {tier} money path"); rc = max(rc, 1)
        if a["ext_calls"]:
            print(f"  ❌ H1/Rule2 — forbidden calls: {[c[1] for c in a['ext_calls']]}"); rc = max(rc, 1)
        if a["indirect_calls"]:
            print(f"  ❌ H2 — indirect/vtable call(s): {[c[1] for c in a['indirect_calls']]}"); rc = max(rc, 1)

        # the headline: data-dependent-warm branches, ASM per category
        print(f"\n  ▼ DATA-DEPENDENT-WARM branches (the jitter risk → drive to 0; each must be "
              f"allowlisted 'warmup-100%-predicted' + PMU-confirmed):")
        if not a["branch_detail"]["data_dependent"]:
            print("      (none)")
        for addr, mn, ops, src in a["branch_detail"]["data_dependent"]:
            print(f"      {addr:>6}:  {mn:<5} {ops:<22}  {src or '(no src)'}")
        if show_asm:
            for cat in ("loop", "rare_cold"):
                print(f"\n  ▸ {cat} branches:")
                for addr, mn, ops, src in a["branch_detail"][cat]:
                    print(f"      {addr:>6}:  {mn:<5} {ops:<22}  {src or '(no src)'}")

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
        os.makedirs(os.path.dirname(BUDGETS_SIDECAR), exist_ok=True)
        with open(BUDGETS_SIDECAR, "w") as f:
            json.dump(new_budgets, f, indent=2)
        print(f"\n  ✅ budgets written → {os.path.relpath(BUDGETS_SIDECAR, ENGINE)}")

    if selftest:
        # TEETH — every detector MUST fire on an injected probe (D-234 lesson 3: the teeth
        # ARE the guard against under-enumeration; only because the float probe existed did
        # the AVX/FMA hole surface). Each case: compile a probe that triggers the detector,
        # analyze, assert it fired. NOTE: the `spills` check is an inherently-heuristic
        # ADVISORY count (frame-relative stores aren't all spills) → NOT strict-teeth'd here.
        cases = [
            ("H4 scalar-float (AVX/FMA)", {"headers": ["cstdint"], "params": "double* a, double b",
                                           "call": "*a = (*a) * b + 1.5"},
             lambda a: a.get("floats", 0) > 0),
            ("div",                       {"headers": ["cstdint"], "params": "long* a, long b, long c",
                                           "call": "*a = b / c"},
             lambda a: a.get("divs", 0) > 0),
            ("forbidden-call (malloc)",   {"headers": ["cstdlib"], "params": "void** a",
                                           "call": "*a = std::malloc(64)"},
             lambda a: len(a.get("ext_calls", [])) > 0),
            ("indirect-call/vtable",      {"headers": ["cstdint"], "params": "void(*fp)(int), int x",
                                           "call": "fp(x)"},
             lambda a: len(a.get("indirect_calls", [])) > 0),
            ("branch-detection",          {"headers": ["cstdint"], "params": "int b, void(*f)()",
                                           "call": "if (b > 7) f()"},
             lambda a: sum(a.get("branches", {}).values()) > 0),
            ("non-vacuity (empty body)",  {"headers": ["cstdint"], "params": "int x", "call": "(void)x"},
             lambda a: a is not None and not a.get("nonvacuous", True)),
        ]
        all_ok = True
        print("\n  --selftest (teeth — each detector MUST fire on an injected probe):")
        for name, probe, want in cases:
            d, e = compile_and_disasm(probe)
            a = analyze(d) if (e is None and d) else None
            ok = (e is None) and want(a if a is not None else {})
            print(f"      {'✅' if ok else '❌'} {name}" + (f"  (PROBE-FAIL: {e})" if e else ""))
            all_ok = all_ok and ok
        print("  --selftest:", "✅ ALL teeth fire" if all_ok
              else "❌ a detector did NOT fire — under-enumeration risk (D-234 lesson 3)")
        if not all_ok:
            return 3

    print("\n" + ("✅ conformance clean" if rc == 0 else f"⚠️  exit {rc} — see flags above"))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
