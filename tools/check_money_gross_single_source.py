#!/usr/bin/env python3
"""check_money_gross_single_source.py — D-190 structural guard (M7).

The realized/unrealized P&L gross MUST be computed via the single-source `Money_FillGross`
helper (CoreFrameworks/Portfolio.hpp), never open-coded per accounting path. The lone
DrainPostFill 2-mul form — round(exit*qty) - round(entry*qty), open-coded as
`Money_Sub(exit_notional, exit_entry_notional)` — diverged from the 1-mul OMS books by 1 ULP
under decimal half-even (D-105 fixed the rounding MODE but missed the FORMULA; D-190 fixed it
by single-sourcing). See PARITY-038 + LANDMINES.md Landmine 8.

This guard catches the 2-mul gross being re-introduced. Two precise signatures (neither
false-positives on the legit `open_notional` decrements, which carry `ctx.`/`state->` prefixes):
  (1) an UNPREFIXED `Money_Sub(<x>notional, <y>notional)` — subtracting two per-fill notionals;
  (2) `gross = Money_Sub(...)` — a gross assigned from a subtraction (the 2-mul form by name).
It also verifies the `Money_FillGross` SSoT still exists.

Exit 0 = clean. Exit 1 = a 2-mul gross reintroduced, or the SSoT is missing.
Self-test: tools/check_money_gross_single_source_selftest.sh (proves teeth).
"""
import re
import sys
import pathlib

# Landmine 5: tools/ is symlinked to the workspace — .resolve() would follow the symlink to the
# WRONG (workspace) root, where CoreFrameworks/ doesn't exist. .absolute() keeps the engine path.
ROOT = pathlib.Path(__file__).absolute().parent.parent
if not (ROOT / "CoreFrameworks").exists():
    print(f"FAIL: cannot locate the engine tree (CoreFrameworks/ not under {ROOT})")
    sys.exit(2)
SCAN_DIRS = ["CoreFrameworks", "Strategies", "Backtest"]

# (1) unprefixed notional-minus-notional (the bug form); the open_notional decrements are
#     `ctx.node_open_notional`/`state->...node_open_notional` (dotted/arrow prefix) → not matched.
RE_NOTIONAL_SUB = re.compile(r"Money_Sub\(\s*\w*notional\w*\s*,\s*\w*notional\w*")
# (2) a gross computed by subtraction (2-mul) rather than via Money_FillGross.
RE_GROSS_SUB = re.compile(r"\bgross\s*=\s*Money_Sub\(")


def scan():
    violations = []
    for d in SCAN_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for f in sorted(base.rglob("*.hpp")):
            try:
                lines = f.read_text(errors="replace").splitlines()
            except OSError:
                continue
            for i, line in enumerate(lines, 1):
                stripped = line.lstrip()
                if stripped.startswith("//") or stripped.startswith("*"):
                    continue
                if RE_NOTIONAL_SUB.search(line) or RE_GROSS_SUB.search(line):
                    violations.append(f"{f.relative_to(ROOT)}:{i}: {line.strip()}")
    return violations


def main():
    violations = scan()
    portfolio = ROOT / "CoreFrameworks" / "Portfolio.hpp"
    ssot_ok = portfolio.exists() and "inline Money Money_FillGross(" in portfolio.read_text(errors="replace")

    if violations:
        print("FAIL (D-190): open-coded 2-mul P&L gross — route it through Money_FillGross (Portfolio.hpp):")
        for v in violations:
            print("  " + v)
    if not ssot_ok:
        print("FAIL (D-190): the Money_FillGross SSoT is missing from CoreFrameworks/Portfolio.hpp")

    if violations or not ssot_ok:
        print("\n  WHY: round((exit-entry)*qty) (1-mul) != round(exit*qty)-round(entry*qty) (2-mul) under")
        print("  decimal half-even (PARITY-038, D-190, Landmine 8). All price-diff gross is single-sourced.")
        sys.exit(1)
    print("PASS (D-190): P&L gross single-sourced via Money_FillGross; no open-coded 2-mul form")


if __name__ == "__main__":
    main()
