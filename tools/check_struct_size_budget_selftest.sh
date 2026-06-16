#!/usr/bin/env bash
# Negative self-test (D-137 teeth) for check_struct_size_budget.py.
# Proves the guard goes RED on its target — a struct that exceeds its cache
# budget. Drives the tool's built-in --selftest, which sets a deliberately-tiny
# 1KB budget against the real 64KB RollingStats<64,1024> ring: the comparison
# MUST flag it. A guard that can't be shown to bite is not shipped.
set -uo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

out="$(python3 "$DIR/check_struct_size_budget.py" --selftest 2>&1)"
rc=$?

if echo "$out" | grep -q "✅ teeth"; then
    echo "✅ check_struct_size_budget_selftest PASS — the guard bites (a 1KB budget flags the 64KB ring)"
    exit 0
else
    echo "❌ check_struct_size_budget_selftest FAIL — the teeth check did not fire (rc=$rc):"
    echo "$out" | tail -8
    exit 1
fi
