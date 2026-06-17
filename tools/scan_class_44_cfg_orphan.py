#!/usr/bin/env python3
"""scan_class_44_cfg_orphan.py — full-codebase Class 44 cfg-flag-ORPHAN scanner (#10, `.E.0.10` Phase C).

The standalone full-scan sibling of `check_per_core_registry_integrity.py` Check 11 (the targeted
Class-44 cfg-MUTATION check) — exactly the two-tool shape Class 27 already uses (Check 7 +
`scan_class_27_full.py`). This catches the Class-44 cfg-flag-ORPHAN sub-variant (A13/A14/A35/A36/A37):
an operator-settable `MASK_*_CFG_*` flag with NO LIVE (sharded) reader — read ONLY on DEAD paths
(the legacy single_core `PortfolioController` + TUI/GUI display) → the operator flips it and NOTHING
happens on the production sharded path (a config foot-gun + a Class-2 display↔execution lie). No
existing tool caught this class (register §:398).

Flag universe = the `FOREACH_*_CFG_FLAG` registry X-rows (the SSoT — `X(NAME,…)` → `MASK_<DOMAIN>_CFG_<NAME>`),
NOT a regex over usages (which catches the `MASK_<DOMAIN>_CFG_##name` macro-paste fragment).
A flag READ = `BITMAP_IS_SET(<expr>, MASK_X)` / `(<expr> & MASK_X)` in code (not a comment). A read is
LIVE unless its file is DEAD. 0 live reads + ≥1 dead read = ORPHAN; 0 reads anywhere = UNUSED.

NOT in scope — the state-field producer/consumer direction over ARBITRARY struct fields (A11/A12
read-live-write-absent) is TECH_DEBT-175 (the AST struct-field produce/consume tracker, its own `.E`
ship); a grep over arbitrary fields is noise. This tool is the reliable, ENUMERABLE cfg-flag slice.

Advisory by default (exit 0). `--strict` exits 1 on any NEW orphan beyond the KNOWN #9 cohort
(close-the-class: NEW = build-error; the cohort = KNOWN-PENDING, shrinking as #9 wires/tombstones).
Validation oracle: A13/A14/A35/A36/A37 MUST be flagged (a miss ⇒ the live/dead taxonomy is wrong).

Policy: RECURRING_BUG_PATTERNS Class 44 (`DOCS/recurring-bug-patterns/class-44-*.md`, cfg-flag-orphan
sub-variant) + register §"#9/#10". M3 false-positive discipline: EXEMPT documents every legitimately-
dead-only flag (rationale required).
"""
import sys
import re
import os
import glob

# Landmine-5-safe resolver (.absolute(), not .resolve()): workspace/tools/<this> → engine sibling.
ENGINE = os.environ.get('FOXML_ENGINE', os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'FoxML_Trader_v2'))

SCAN_DIRS = ('CoreFrameworks', 'Strategies', 'DataStream', 'GUI', 'MemHeaders', 'ML_Headers', 'Backtest')

# DEAD reader paths — legacy single_core controller + TUI/GUI display. A read here is NOT a live
# sharded consumer (the A13-A37 cohort's reads all land here; PortfolioController.hpp:277 = "the
# legacy single-core controller").
DEAD_FILES = {
    'CoreFrameworks/PortfolioController.hpp',     # legacy single_core / centralized controller
    'DataStream/EngineTUI.hpp',                    # TUI display snapshot
}
DEAD_DIRS = ('GUI/',)                              # all GUI panels (display/render)

# The A13/A14/A35/A36/A37 cohort — NOT exempt (it is the #9 close target); listed so --strict reports
# them KNOWN-PENDING (shrinking), and as the detector's self-test oracle.
KNOWN_COHORT = {
    'MASK_GATE_CFG_NO_TRADE_BAND_ENABLED',      # A13
    'MASK_RISK_CFG_VOL_SIZING_ENABLED',         # A14
    'MASK_GATE_CFG_GATE_EMA_ENABLED',           # A35
    'MASK_LIFECYCLE_CFG_BREAKEVEN_ON_PARTIAL',  # A36
    'MASK_OPS_CFG_SESSION_FILTER_ENABLED',      # A37
}
EXEMPT = set()  # genuinely-dead-by-design flags (none yet; populate WITH RATIONALE as found — M3)

# Negative-self-test hook (D-137): a hermetic temp tree overrides the oracle cohort to its synthetic flag.
_oc = os.environ.get('FOXML_ORACLE_COHORT')
if _oc:
    KNOWN_COHORT = set(_oc.split(','))

FOREACH_DEF = re.compile(r'#define\s+FOREACH_([A-Z]+)_CFG_FLAG\s*\(\s*X\s*\)')
ROW = re.compile(r'^\s*X\(\s*([A-Z0-9_]+)\s*,')


def is_dead(rel):
    return rel in DEAD_FILES or any(rel.startswith(d) for d in DEAD_DIRS)


def enumerate_flags():
    """Flag universe from the FOREACH_*_CFG_FLAG registry X-rows (SSoT, no `##` artifacts)."""
    flags = {}  # MASK_name -> "registry_rel:line"
    reg_files = []
    for d in ('CoreFrameworks', 'ML_Headers'):  # ML flags live in ML_Headers/MlCfgFlagRegistry.hpp
        reg_files += glob.glob(os.path.join(ENGINE, d, '**', '*CfgFlagRegistry.hpp'), recursive=True)
    for f in sorted(set(reg_files)):
        rel = os.path.relpath(f, ENGINE)
        lines = open(f, encoding='utf-8', errors='replace').read().splitlines()
        domain, in_macro = None, False
        for i, line in enumerate(lines, 1):
            md = FOREACH_DEF.search(line)
            if md:
                domain = md.group(1)
                in_macro = line.rstrip().endswith('\\')
                continue
            if domain and in_macro:
                mr = ROW.match(line)
                if mr:
                    flags[f"MASK_{domain}_CFG_{mr.group(1)}"] = f"{rel}:{i}"
                if not line.rstrip().endswith('\\'):
                    domain, in_macro = None, False
    return flags


def read_re(flag):
    f = re.escape(flag)
    return re.compile(r'BITMAP_IS_SET\s*\([^,]+,\s*' + f + r'\b' + r'|[&|]\s*' + f + r'\b')


def main():
    strict = '--strict' in sys.argv
    files = []
    for d in SCAN_DIRS:
        base = os.path.join(ENGINE, d)
        files += glob.glob(os.path.join(base, '**', '*.hpp'), recursive=True)
        files += glob.glob(os.path.join(base, '**', '*.cpp'), recursive=True)
    cache = {os.path.relpath(f, ENGINE): open(f, encoding='utf-8', errors='replace').read().splitlines()
             for f in sorted(set(files))}

    flags = enumerate_flags()
    if not flags:
        print("[scan_class_44_cfg_orphan] ERROR — 0 flags enumerated from *CfgFlagRegistry.hpp "
              "(FOREACH_*_CFG_FLAG parse broke). Cannot trust the scan.")
        return 1

    orphans, unused = [], []
    for flag, defsite in sorted(flags.items()):
        if flag in EXEMPT:
            continue
        rr = read_re(flag)
        live, dead = [], []
        for rel, lines in cache.items():
            for i, raw in enumerate(lines, 1):
                code = raw[:raw.find('//')] if '//' in raw else raw  # drop // comments
                if rr.search(code):
                    (dead if is_dead(rel) else live).append(f"{rel}:{i}")
        if live:
            continue
        (orphans if dead else unused).append((flag, defsite, dead))

    print(f"[scan_class_44_cfg_orphan] {len(flags)} cfg flags (from registries) × {len(cache)} files: "
          f"{len(orphans)} dead-path-only orphan(s), {len(unused)} unused.")
    for flag, defsite, dead in orphans:
        tag = "KNOWN-PENDING(#9)" if flag in KNOWN_COHORT else "NEW-ORPHAN"
        print(f"  [{tag}] {flag}  (def {defsite}) — read ONLY on dead paths:")
        for s in dead[:6]:
            print(f"      dead-read: {s}")
    for flag, defsite, _ in unused:
        print(f"  [UNUSED] {flag}  (def {defsite}) — no read anywhere (defined, never consumed).")

    # Oracle self-check — the known cohort MUST be flagged (a miss ⇒ wrong live/dead taxonomy).
    found = {f for f, _, _ in orphans}
    missing = KNOWN_COHORT - found
    if missing:
        print(f"  [ORACLE-FAIL] detector MISSED known cohort flags: {sorted(missing)} — the live/dead "
              f"taxonomy is wrong; do NOT trust the output until fixed.")
        return 1

    new = sorted([f for f, _, _ in orphans if f not in KNOWN_COHORT] + [f for f, _, _ in unused])
    if new:
        tag = "FAIL" if strict else "WARN"
        print(f"[scan_class_44_cfg_orphan] {tag} — {len(new)} NEW orphan(s) beyond the #9 cohort: "
              f"{new} → wire-into-sharded OR tombstone (H21).")
        return 1 if strict else 0
    print("[scan_class_44_cfg_orphan] OK — oracle PASS (cohort caught); no NEW orphans beyond #9.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
