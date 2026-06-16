#!/usr/bin/env python3
"""
check_struct_size_budget.py — mechanical guard for struct SIZE + CACHE-RESIDENCY.

WHY (the meta-pattern this kills):
  Hand-computed code-facts in comments DRIFT because nothing forces them to agree
  with the code. The `rolling_baseline` comment said "~1.5MB" for a 64KB struct —
  a per-engine (x16 cores) total at the OLD 24B FPN, written on a per-core field,
  never reconciled. `sizeof` has no "scope" assumption: it is one unambiguous
  number. This tool replaces the hand-comment with a compiled measurement, and
  pins latency-critical structs against the host cache budgets.

  Sister guards (canonical, do NOT duplicate):
    - check_struct_alignment.py        — pins sizeof(T)==N for BYTE-SERIALIZED types
                                         (wire/persist/memcmp). Non-serialized runtime
                                         structs (RollingStats, CoreLatencyStats) fall
                                         THROUGH it — that gap is exactly this tool.
    - check_fpn_doc_size_currency.py    — pins DOC statements of a single FPN<> size.

WHAT it checks, per manifest row:
  1. Compiles `sizeof(<instantiation>)` for real (never trusts a comment).
  2. CACHE-BUDGET: flags a struct whose size exceeds its declared cache tier
     (L1d / L2, DERIVED from the host via getconf — NOT magic constants, so the
     guard does not itself reproduce the disease it guards).
  3. PIN-COVERAGE: emits the `static_assert(sizeof(T)==N)` line to paste at the
     declaration so a future layout change is a COMPILE error (compile-time > CI).

EXIT: 0 = all rows within budget. 1 = a budget violation. 2 = a probe failed to
compile (tooling error — surfaced, never silently skipped).

Adding a struct = ONE manifest row (registry discipline). Run from the engine
root or set FOXML_ENGINE.
"""
import os
import re
import subprocess
import sys
import tempfile

# ── machine-portable engine-root resolver (per feedback_machine_portable_resolver) ──
ENGINE = os.environ.get("FOXML_ENGINE") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def host_cache_bytes(level_getconf, fallback):
    """DERIVE the cache budget from the host (eat-own-dogfood: no hand-numbers in
    the guard). getconf gives bytes; fall back to a labelled default if absent."""
    try:
        out = subprocess.run(["getconf", level_getconf], capture_output=True, text=True, timeout=5).stdout.strip()
        return int(out) if out and out.isdigit() and int(out) > 0 else fallback
    except Exception:
        return fallback


L1D = host_cache_bytes("LEVEL1_DCACHE_SIZE", 48 * 1024)   # i7-11850H = 48KB; derived per host
L2 = host_cache_bytes("LEVEL2_CACHE_SIZE", 1280 * 1024)   # i7-11850H = 1.25MB
TIERS = {"L1d": L1D, "L2": L2}

# ── MANIFEST: latency-critical / window-parameterized structs (1 row each) ──
#   tier = the cache level the struct's WORKING SET should fit. NOTE: for the
#   rolling windows the per-PUSH working set is ~a few cache lines (one slot +
#   sums + deque heads), so the FULL ring legitimately lives in L2 — flagging
#   >L1d here is informational, the real residency question is the per-push set
#   (a DYNAMIC perf-counter check that belongs in the H8 bench, not here).
MANIFEST = [
    {"type": "RollingStats<64,128>",  "header": "ML_Headers/RollingStats.hpp",          "tier": "L1d"},
    {"type": "RollingStats<64,256>",  "header": "ML_Headers/RollingStats.hpp",          "tier": "L2"},
    {"type": "RollingStats<64,512>",  "header": "ML_Headers/RollingStats.hpp",          "tier": "L2"},
    {"type": "RollingStats<64,1024>", "header": "ML_Headers/RollingStats.hpp",          "tier": "L2"},
    {"type": "tt::CoreLatencyStats",  "header": "CoreFrameworks/CoreLatencyStats.hpp",  "tier": "L1d"},
    {"type": "tt::LatencyHistogram",  "header": "MemHeaders/LatencyHistogram.hpp",       "tier": "L1d"},
    # ── hot-path / SoA structs (L1d-residency surface) ──
    # NOTE: sizeof is a COARSE proxy — the per-TICK working set is a SUBSET of the
    # struct (RollingStats taught us: ~64B touched of a 64KB ring). A >L1d flag here
    # DIRECTS a perf-counter residency check (the H8-bench dynamic dimension); it is
    # not itself a violation. Pins still pay (catch a silent layout blow-up).
    {"type": "tt::GateParameters<64>", "header": "CoreFrameworks/GateParameters.hpp",    "tier": "L1d"},
    {"type": "Position<64>",          "header": "CoreFrameworks/Portfolio.hpp",          "tier": "L1d"},
    {"type": "Portfolio<64>",         "header": "CoreFrameworks/Portfolio.hpp",          "tier": "L1d"},
    # ExecutionCore: 66.8KB whole-struct, dominated by the EMBEDDED event_ring
    # (write-once-drain FIFO — streaming writes, NO residency need) + tail-placed
    # cold latency_stats. Hot READ cluster = cache line 0 (L1d). So the whole struct
    # honestly fits L2; the "hot cluster fits L1d" question is DYNAMIC (H8 perf-counter
    # check), not a static whole-sizeof verdict. Tiering L1d here false-REDs a
    # cache-disciplined struct (the inverse of the vacuously-green guard).
    {"type": "tt::ExecutionCore<64>",  "header": "CoreFrameworks/ExecutionCore.hpp",     "tier": "L2"},
]


def probe_sizeof(entry):
    """Compile + run `sizeof(<type>)`. Returns (size:int|None, err:str|None)."""
    src = (
        f'#include "{entry["header"]}"\n'
        "#include <cstdio>\n"
        f"int main(){{ std::printf(\"%zu\\n\", sizeof({entry['type']})); return 0; }}\n"
    )
    with tempfile.TemporaryDirectory(dir=ENGINE) as td:  # in-repo-tree: /tmp may be noexec (LANDMINE)
        cpp = os.path.join(td, "probe.cpp")
        out = os.path.join(td, "probe.bin")   # build in-repo-tree tmp (not /tmp; may be noexec)
        with open(cpp, "w") as f:
            f.write(src)
        comp = subprocess.run(
            ["g++", "-std=c++20", f"-I{ENGINE}", cpp, "-o", out],
            capture_output=True, text=True, cwd=ENGINE,
        )
        if comp.returncode != 0:
            return None, comp.stderr.strip().splitlines()[-1] if comp.stderr.strip() else "compile failed"
        run = subprocess.run([out], capture_output=True, text=True)
        if run.returncode != 0:
            return None, "probe ran non-zero"
        return int(run.stdout.strip()), None


def human(n):
    return f"{n/1024:.1f}KB" if n >= 1024 else f"{n}B"


def main(argv):
    selftest = "--selftest" in argv
    print("=" * 64)
    print(" check_struct_size_budget.py — sizeof + cache-residency guard")
    print(f"   host budgets (derived): L1d={human(L1D)}  L2={human(L2)}")
    print("=" * 64)

    rc = 0
    pins = []
    for e in MANIFEST:
        size, err = probe_sizeof(e)
        if err:
            print(f"  ⚠️  PROBE-FAIL  {e['type']:<26} — {err}")
            rc = max(rc, 2)
            continue
        budget = TIERS[e["tier"]]
        ok = size <= budget
        mark = "✅" if ok else "❌"
        if not ok:
            rc = max(rc, 1)
        print(f"  {mark} {e['type']:<26} = {human(size):>8}  (tier {e['tier']} ≤ {human(budget)})")
        pins.append(f"static_assert(sizeof({e['type']}) == {size}, \"size-pin: layout change = recompute the cache budget\");")

    if selftest:
        # teeth: a deliberately-tiny fake budget MUST flag a real struct as over-budget.
        size, err = probe_sizeof(MANIFEST[3])  # RollingStats<64,1024> ~64KB
        caught = (err is None) and (size is not None) and (size > 1024)
        print("\n  --selftest:", "✅ teeth (a 1KB budget flags the 64KB ring)" if caught else "❌ TEETH FAILED")
        if not caught:
            return 3

    print("\n  Suggested compile-time pins (paste at the declaration; compiler then enforces):")
    for p in pins:
        print("    " + p)
    print("\n" + ("✅ all within budget" if rc == 0 else f"⚠️  exit {rc} — see flags above"))
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
