#!/usr/bin/env bash
# NEGATIVE self-test for check_identifier_retirement.py (the H21 tombstone guard) — proves it has TEETH:
# it goes RED (exit 1) on a renumber / version-decrease / silent-removal, and GREEN on the clean ledger.
# Mirrors the manual verify-by-injection done when the guard was built. Sister: check_determinism_selftest.sh.
# Restores the ledger on exit (trap).
#
# ⚠️ EVERY PLANT IS ASSERTED (added 2026-07-20). Case (2) sat BROKEN for an unknown period: it hardcoded
# `SHARDED_SNAPSHOT_VERSION|8` while the ledger had moved to `|10`, so the sed was a NO-OP, no defect was
# ever planted, the guard passed on an unmutated ledger, and the test reported "version-decrease should be
# RED" — reading as *the guard is broken* when the truth was *the fixture failed to plant*. A negative test
# that cannot tell those apart is worse than none: it burns trust in a guard that was working.
#
# So each case now (a) derives the CURRENT value instead of hardcoding one, and (b) asserts the file
# actually changed before drawing any conclusion from the tool's exit code. This is the same shape as the
# calibration-corpus discipline's rule about fixtures anchored to live values — a live value moves, and an
# anchored fixture silently goes vacuous.
set -u
cd "$(dirname "$0")/.." || exit 2
TOOL="tools/check_identifier_retirement.py"
LEDGER="tools/identifier_ledger.txt"
# Work on a THROWAWAY COPY — the tracked golden is never mutated. IDENTIFIER_LEDGER points the
# tool at our copy, so an interrupted run cannot leave a corrupted H21 ledger in the working tree.
REAL="$LEDGER"
BAK="$(mktemp)"; cp "$REAL" "$BAK"
LEDGER="$(mktemp)"; cp "$REAL" "$LEDGER"
export IDENTIFIER_LEDGER="$LEDGER"
restore(){ cp "$BAK" "$LEDGER"; }
cleanup(){ rm -f "$BAK" "$LEDGER"; }
trap cleanup EXIT
fail=0

# assert_planted <label> — the mutation must have actually landed, else the case proves nothing.
assert_planted(){
    if cmp -s "$BAK" "$LEDGER"; then
        echo "SELFTEST FAIL: fixture for '$1' planted NOTHING (stale anchor?) — the ledger is unmutated,"
        echo "               so this case cannot distinguish a working guard from a broken one."
        fail=1; return 1
    fi
    return 0
}

# baseline: the clean ledger must be GREEN
python3 "$TOOL" >/dev/null 2>&1 || { echo "SELFTEST FAIL: clean ledger should be GREEN"; fail=1; }

# (1) RENUMBER an enum code -> must be RED. Value derived, not hardcoded.
cp "$BAK" "$LEDGER"
ml_cur=$(sed -n 's/^enum:StrategyId|STRATEGY_ML|\([0-9]*\)$/\1/p' "$LEDGER" | head -1)
if [ -z "$ml_cur" ]; then
    echo "SELFTEST FAIL: anchor 'enum:StrategyId|STRATEGY_ML' is GONE from the ledger — re-point this case"
    fail=1
else
    sed -i "s/^enum:StrategyId|STRATEGY_ML|${ml_cur}\$/enum:StrategyId|STRATEGY_ML|$((ml_cur + 6))/" "$LEDGER"
    if assert_planted "enum renumber"; then
        if python3 "$TOOL" >/dev/null 2>&1; then echo "SELFTEST FAIL: enum renumber should be RED"; fail=1
        else echo "  ok: enum renumber -> RED (${ml_cur} -> $((ml_cur + 6)))"; fi
    fi
fi

# (2) VERSION DECREASE (ledger ahead of code => code looks decreased) -> must be RED. Value derived.
cp "$BAK" "$LEDGER"
ver_cur=$(sed -n 's/^version|SHARDED_SNAPSHOT_VERSION|\([0-9]*\)$/\1/p' "$LEDGER" | head -1)
if [ -z "$ver_cur" ]; then
    echo "SELFTEST FAIL: anchor 'version|SHARDED_SNAPSHOT_VERSION' is GONE from the ledger — re-point this case"
    fail=1
else
    sed -i "s/^version|SHARDED_SNAPSHOT_VERSION|${ver_cur}\$/version|SHARDED_SNAPSHOT_VERSION|$((ver_cur + 1))/" "$LEDGER"
    if assert_planted "version decrease"; then
        if python3 "$TOOL" >/dev/null 2>&1; then echo "SELFTEST FAIL: version-decrease should be RED"; fail=1
        else echo "  ok: version-decrease -> RED (${ver_cur} -> $((ver_cur + 1)) in the ledger)"; fi
    fi
fi

# (3) SILENT REMOVAL (ledger has an identifier the code no longer defines) -> must be RED.
# An append always plants, but assert it anyway so the case cannot rot into a silent no-op either.
cp "$BAK" "$LEDGER"
printf 'enum:StrategyId|STRATEGY_GHOST_OLD|9\n' >> "$LEDGER"
if assert_planted "silent removal"; then
    if python3 "$TOOL" >/dev/null 2>&1; then echo "SELFTEST FAIL: silent-removal should be RED"; fail=1
    else echo "  ok: silent-removal -> RED"; fi
fi

# restore + GREEN again
restore
python3 "$TOOL" >/dev/null 2>&1 || { echo "SELFTEST FAIL: restored ledger should be GREEN"; fail=1; }

# the REAL golden must be untouched by this run — assert it, do not assume it
cmp -s "$REAL" "$BAK" || { echo "SELFTEST FAIL: the tracked ledger was MUTATED by the selftest"; fail=1; }

if [ "$fail" = 0 ]; then echo "check_identifier_retirement_selftest: PASS (guard has teeth)"; else echo "check_identifier_retirement_selftest: FAIL"; fi
exit "$fail"
