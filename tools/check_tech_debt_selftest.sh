#!/usr/bin/env bash
# NEGATIVE self-test for check_tech_debt.py (the tech-debt surface advisory) — proves it has TEETH.
# --surface is ADVISORY (exit 0 by design), so its "teeth" = it actually DETECTS an overlap (not a silent
# no-op); --stale --strict is the one RED mode. We assert both. Sister: check_determinism_selftest.sh.
set -u
cd "$(dirname "$0")/.." || exit 2
TOOL="tools/check_tech_debt.py"
fail=0

# (1) DETECTION: a file cited in OPEN TECH_DEBT entries must surface >=1 item. OrderManager.hpp is cited
#     by many open entries (008/012/029/071/130/152/...), so this is a stable positive case.
OUT="$(python3 "$TOOL" --surface CoreFrameworks/OrderManager.hpp 2>&1)"
if echo "$OUT" | grep -q 'OPEN item'; then echo "  ok: --surface detects a known overlap"; else
    echo "SELFTEST FAIL: --surface CoreFrameworks/OrderManager.hpp should surface >=1 OPEN item"; fail=1; fi

# (2) NON-MATCH: a file cited by no entry must surface nothing (no false positives).
if python3 "$TOOL" --surface __no_such_file_xyz.hpp 2>&1 | grep -q 'OPEN item'; then
    echo "SELFTEST FAIL: a non-cited file should surface nothing"; fail=1; else echo "  ok: non-cited file -> silent"; fi

# (3) RED mode: --stale 0 --strict must go RED (every entry opened before today is 'stale' at 0 months).
if python3 "$TOOL" --stale 0 --strict >/dev/null 2>&1; then
    echo "SELFTEST FAIL: --stale 0 --strict should be RED"; fail=1; else echo "  ok: --stale 0 --strict -> RED"; fi

# (4) THE MUTATING PATH. --close moves entries between two ledgers with no undo but git, and it
#     had NO tooth here at all — which is how it stayed write-by-default long after TECH_DEBT-255
#     migrated its sibling writer (check_identifier_retirement --update) onto the D-394 contract.
#     Found 2026-07-20 when a read-only verification fired it and silently moved TECH_DEBT-016.
#     Asserts BOTH halves: refuses non-interactively (rc=2), AND leaves the ledgers byte-identical.
#     The byte check is the load-bearing one — an rc=2 returned AFTER writing would still pass a
#     naive exit-code assertion.
#     ASK THE TOOL for the ledger path — never re-encode it here. The first cut of this tooth
#     hardcoded `DOCS/tech-debt/open.md`, which does not resolve from this script's cwd; md5sum
#     errored, both vars became EMPTY, and `"" = ""` compared equal, so the byte assertion passed
#     while asserting nothing. A vacuous tooth inside the tooth written to catch vacuity. The
#     empty-guard below is what makes that impossible to repeat.
LEDGER_DIR="$(python3 -c "import sys,os;sys.path.insert(0,'tools');from check_tech_debt import _tech_debt_dir;print(_tech_debt_dir())" 2>/dev/null)"
if [ -z "$LEDGER_DIR" ] || [ ! -f "$LEDGER_DIR/open.md" ] || [ ! -f "$LEDGER_DIR/closed.md" ]; then
    echo "SELFTEST FAIL: cannot resolve the tech-debt ledgers (dir='$LEDGER_DIR') — the byte check would be VACUOUS"; fail=1; fi
BEFORE_O="$(md5sum "$LEDGER_DIR/open.md" 2>/dev/null | cut -d' ' -f1)"
BEFORE_C="$(md5sum "$LEDGER_DIR/closed.md" 2>/dev/null | cut -d' ' -f1)"
python3 "$TOOL" --close 016 >/dev/null 2>&1; rc=$?
AFTER_O="$(md5sum "$LEDGER_DIR/open.md" 2>/dev/null | cut -d' ' -f1)"
AFTER_C="$(md5sum "$LEDGER_DIR/closed.md" 2>/dev/null | cut -d' ' -f1)"
if [ -n "$BEFORE_O" ] && [ -n "$BEFORE_C" ] && [ "$rc" = 2 ] && [ "$BEFORE_O" = "$AFTER_O" ] && [ "$BEFORE_C" = "$AFTER_C" ]; then
    echo "  ok: --close non-TTY -> rc=2 REFUSED and both ledgers byte-UNCHANGED"
else
    echo "SELFTEST FAIL: --close non-TTY must refuse rc=2 without writing (rc=$rc, open_changed=$([ "$BEFORE_O" != "$AFTER_O" ] && echo yes || echo no), closed_changed=$([ "$BEFORE_C" != "$AFTER_C" ] && echo yes || echo no))"; fail=1; fi

# (5) ZERO-PAD REACH: `--close 16` and `--close 016` must resolve the SAME entry. Before the fix
#     the bare spelling errored ("not found") while the padded one WROTE — the safe spelling
#     failing and the dangerous one succeeding. --dry-run is the non-mutating probe for this.
if python3 "$TOOL" --close 16 --dry-run 2>&1 | grep -q 'TECH_DEBT-016'; then
    echo "  ok: --close 16 resolves the zero-padded TECH_DEBT-016"
else
    echo "SELFTEST FAIL: --close 16 must resolve the padded entry TECH_DEBT-016"; fail=1; fi

if [ "$fail" = 0 ]; then echo "check_tech_debt_selftest: PASS (advisory has teeth)"; else echo "check_tech_debt_selftest: FAIL"; fi
exit "$fail"
