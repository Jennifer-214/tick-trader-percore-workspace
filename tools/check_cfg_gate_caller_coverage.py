#!/usr/bin/env python3
"""③ item-6 (E.1.1, D-256 #6 / D-260 C-5) — config-compiler CALLER-COVERAGE recurrence guard.

Every file that materializes a ControllerConfig via ControllerConfig_Load MUST gate it through
cfg_capital_gate_ok (or the bare cfg_compile_ok predicate) before using it — else a malformed /
out-of-range cfg runs UNGATED (the founding-bug class: a silently-disabled stop-loss / 999% risk).

The grep-based per-file guard: a ControllerConfig_Load caller in a file with NO cfg gate = a NEW
ungated caller → fail. This is the half a compile-time static_assert can't see (it guards the
data shape, not the call graph; the static half — no-capital-row-is-MANUAL_PARSER — lives in
ControllerConfig.hpp). Together they close D-256 #6.

Exempt callers (observability / dead), each with a stated reason — adding a new caller is NOT
silently exemptible: it either gates, or it is added here WITH a reason (the deliberate decision).
"""
import re
import sys
import subprocess
import pathlib

def _engine_root():
    # The engine repo has CoreFrameworks/ + main.cpp. Do NOT resolve() — tools/ is a symlink to the
    # workspace repo (which has the .md docs but no source); resolving would land there. Walk up from this
    # tool's (symlink-path) dir; the normal engine-path invocation → tools/.. is the engine root.
    start = pathlib.Path(__file__).parent
    for cand in [start.parent, *start.parents]:
        if (cand / "CoreFrameworks").is_dir() and (cand / "main.cpp").exists():
            return cand
    raise SystemExit("[cfg-gate-coverage] ERROR: engine root (CoreFrameworks + main.cpp) not found from " + str(start))


ENGINE = _engine_root()

# basename -> reason. An exemption is a DELIBERATE, reasoned entry (not a silent skip).
EXEMPT = {
    "SettingsPanel.hpp": "GUI Settings_Load is OBSERVABILITY (keeps-old on bad cfg), not a capital authority (D-262)",
    "EngineTUI.hpp":     "legacy TUI reload — DEAD on the sharded path (not reached from main.cpp / EngineSharded/Run.hpp)",
}
GATE_RE = re.compile(r"cfg_capital_gate_ok\s*\(|cfg_compile_ok\s*\(")


SRC_EXT = (".cpp", ".hpp", ".cc", ".h", ".cxx", ".hxx")
# The PUBLIC engine source dirs (real dirs, not the symlinked .md doc dirs). Searching these explicitly
# avoids the repo-root gitignore/symlink quirk where `rg $ENGINE` reaches the symlinked DESIGN_SPECS/plans
# (.md) but not the tracked source. main.cpp is a file (handled below).
SRC_DIRS = ["CoreFrameworks", "Backtest", "GUI", "DataStream", "ML_Headers",
            "Strategies", "FixedPoint", "MemHeaders"]


def rg_files(pattern):
    """C++ SOURCE files (in the public source dirs + main.cpp) containing `pattern`; excludes tests + the parse util."""
    roots = [str(ENGINE / d) for d in SRC_DIRS if (ENGINE / d).is_dir()]
    main_cpp = ENGINE / "main.cpp"
    if main_cpp.exists():
        roots.append(str(main_cpp))
    r = subprocess.run(["rg", "-l", pattern] + roots, capture_output=True, text=True)
    out = []
    for line in r.stdout.splitlines():
        if not line:
            continue
        p = pathlib.Path(line)
        if p.suffix not in SRC_EXT:        # drop .md docs, .py, .txt, ...
            continue
        if "tests" in p.parts:             # drop tests/ (incl. the symlinked path)
            continue
        if p.name == "ParseFast.hpp":      # the parse util — no Load caller
            continue
        out.append(line)
    return sorted(out)


def main():
    print("[cfg-gate-coverage] config-compiler caller-coverage check (③ item-6 / D-256 #6)...")
    # `ControllerConfig_Load<` matches CALLERS only — the definition is `ControllerConfig_Load(const char`
    # (the `<F>` is on ControllerConfig, not Load), so the definition file does not match.
    callers = rg_files(r"ControllerConfig_Load<")
    if not callers:
        print("[cfg-gate-coverage] WARN: no ControllerConfig_Load callers found — pattern drift? (investigate)")
        sys.exit(1)

    ungated = []
    for f in callers:
        p = pathlib.Path(f)
        name = p.name
        if name in EXEMPT:
            print(f"  [EXEMPT]  {name} — {EXEMPT[name]}")
            continue
        txt = p.read_text(errors="ignore")
        if GATE_RE.search(txt):
            print(f"  [GATED]   {name} — Load + cfg gate present")
        else:
            ungated.append(name)
            print(f"  [UNGATED] {name} — ControllerConfig_Load with NO cfg_capital_gate_ok / cfg_compile_ok")

    if ungated:
        print(f"\n[cfg-gate-coverage] FAIL — {len(ungated)} ungated cfg-load caller(s): {ungated}")
        print("  -> route each FRESH-START caller through cfg_capital_gate_ok (engine abort / backtest fail-run /")
        print("     reload warn-keep-old); an OBSERVABILITY caller is exempted via EXEMPT[] WITH a stated reason.")
        sys.exit(1)

    print(f"\n[cfg-gate-coverage] PASS — all {len(callers)} ControllerConfig_Load caller(s) gated or exempt.")
    sys.exit(0)


def selftest():
    """Non-vacuity teeth (D-256 #6): prove the gate-detection actually distinguishes a gated caller from an
    ungated one — so a real ungated caller WOULD be flagged (not a vacuously-green guard, RBP Class-51)."""
    fails = []
    if not GATE_RE.search('if (!cfg_capital_gate_ok(cfg, "x")) return 1;'):
        fails.append("GATE_RE failed to match a cfg_capital_gate_ok caller")
    if not GATE_RE.search('if (!cfg_compile_ok(c)) keep_old();'):
        fails.append("GATE_RE failed to match a cfg_compile_ok caller")
    if GATE_RE.search('auto c = ControllerConfig_Load<F>(p); run(c);'):
        fails.append("GATE_RE WRONGLY matched an ungated Load (the FAIL path would never fire)")
    callers = rg_files(r"ControllerConfig_Load<")
    if not callers:
        fails.append("rg_files found ZERO callers (engine-root / pattern drift — the guard would pass vacuously)")
    if fails:
        for f in fails:
            print("  [selftest FAIL] " + f)
        print("[cfg-gate-coverage] --selftest FAIL")
        sys.exit(1)
    print(f"[cfg-gate-coverage] --selftest PASS — gate-detection distinguishes gated/ungated; "
          f"{len(callers)} live caller(s) enumerated.")
    sys.exit(0)


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    main()
