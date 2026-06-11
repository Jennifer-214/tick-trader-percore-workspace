#!/usr/bin/env bash
# Self-test for check_money_gross_single_source.py — proves the D-190 guard has TEETH
# (catches a re-introduced 2-mul P&L gross) and does NOT false-positive on the clean tree.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GUARD="$ROOT/tools/check_money_gross_single_source.py"
TMP="$ROOT/CoreFrameworks/_d190_selftest_tmp.hpp"   # not #included anywhere → build-inert
rc=0

# 1) clean tree must PASS
python3 "$GUARD" >/dev/null 2>&1 || { echo "SELFTEST FAIL: guard FAILs on the clean tree (false positive)"; rc=1; }

# 2) inject a 2-mul gross → guard MUST fail (teeth)
printf 'const Money gross = Money_Sub(exit_notional, exit_entry_notional);\n' > "$TMP"
if python3 "$GUARD" >/dev/null 2>&1; then echo "SELFTEST FAIL: injected 2-mul gross NOT caught (no teeth)"; rc=1; else echo "  ok: injected 2-mul gross caught"; fi
rm -f "$TMP"

# 3) clean again must PASS
python3 "$GUARD" >/dev/null 2>&1 || { echo "SELFTEST FAIL: guard still FAILs after revert"; rc=1; }

[ "$rc" -eq 0 ] && echo "SELFTEST PASS: D-190 gross-SSoT guard has teeth (catches 2-mul; no false positive)"
exit $rc
