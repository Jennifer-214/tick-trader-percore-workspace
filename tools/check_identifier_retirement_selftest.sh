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

# --- stamp-key category (D-425 #10, 2026-08-17) -------------------------------
# The stamp WIRE KEYS. These two cases are deliberately anchored on the CODE side, not on the
# ledger's blessed state: they plant a ledger row for a key the registry ALREADY defines, so they
# prove teeth identically before and after the operator's `--update`. Anchoring them on a blessed
# ledger row would have made them vacuous for exactly the window in which the enrollment is new and
# least trusted — the live-value anchoring trap case (2) fell into.

# (4) RENUMBER a stamp wire key -> must be RED. A reorder perturbs an HMAC-signed body (H9/H21).
cp "$BAK" "$LEDGER"
if grep -q '^stamp-key|feature_mask|' "$LEDGER"; then
    sed -i 's/^stamp-key|feature_mask|.*$/stamp-key|feature_mask|9999/' "$LEDGER"
else
    printf 'stamp-key|feature_mask|9999\n' >> "$LEDGER"
fi
if assert_planted "stamp-key renumber"; then
    out=$(python3 "$TOOL" 2>&1)
    if printf '%s' "$out" | grep -q 'RENUMBERED stamp-key :: feature_mask'; then
        echo "  ok: stamp-key renumber -> RED (wire-key reorder caught)"
    else
        echo "SELFTEST FAIL: stamp-key renumber should be RED naming feature_mask."
        echo "               If feature_mask was legitimately retired, RE-POINT this case at another"
        echo "               live wire key — do not delete it; the category would lose its teeth."
        fail=1
    fi
fi

# (5) SILENT REMOVAL of a stamp wire key -> must be RED. This is the shape the Tier-2 emit-side
# deletion lands on, which is why enrolling the category was its prerequisite.
cp "$BAK" "$LEDGER"
printf 'stamp-key|inference_cfg_ghost_retired_key|9998\n' >> "$LEDGER"
if assert_planted "stamp-key removal"; then
    out=$(python3 "$TOOL" 2>&1)
    if printf '%s' "$out" | grep -q 'REMOVED  stamp-key :: inference_cfg_ghost_retired_key'; then
        echo "  ok: stamp-key silent-removal -> RED (dropped wire key caught)"
    else
        echo "SELFTEST FAIL: stamp-key silent-removal should be RED"; fail=1
    fi
fi

# (6) NON-VACUITY — the category must actually RESOLVE against the live registry. A SOURCES row whose
# macro was renamed parses to nothing; without this leg that is indistinguishable from a clean tree.
cp "$BAK" "$LEDGER"
n_keys=$(python3 - <<'PY'
import importlib.util, os, sys
spec = importlib.util.spec_from_file_location("cir", "tools/check_identifier_retirement.py")
m = importlib.util.module_from_spec(spec); sys.modules["cir"] = m; spec.loader.exec_module(m)
print(len(m.parse_current().get("stamp-key", {})))
PY
)
if [ "${n_keys:-0}" -ge 2 ]; then
    echo "  ok: stamp-key non-vacuity -> ${n_keys} wire keys resolved from the live registry"
else
    echo "SELFTEST FAIL: stamp-key resolved ${n_keys:-0} keys — the SOURCES row matches nothing."
    echo "               A category that cannot fail is worse than one that is missing."
    fail=1
fi

# restore + GREEN again
restore
python3 "$TOOL" >/dev/null 2>&1 || { echo "SELFTEST FAIL: restored ledger should be GREEN"; fail=1; }

# the REAL golden must be untouched by this run — assert it, do not assume it
cmp -s "$REAL" "$BAK" || { echo "SELFTEST FAIL: the tracked ledger was MUTATED by the selftest"; fail=1; }

if [ "$fail" = 0 ]; then echo "check_identifier_retirement_selftest: PASS (guard has teeth)"; else echo "check_identifier_retirement_selftest: FAIL"; fi
exit "$fail"
