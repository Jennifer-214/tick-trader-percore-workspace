#!/usr/bin/env bash
# run_sanitizer_suite.sh — sanitizer acceptance with PINNED run-conditions (TECH_DEBT-161 close).
#
# WHY the pins (A.5 acceptance findings, 2026-06-09):
#   (a) ulimit -s unlimited — ASan redzones inflate controller_test main()'s large stack locals
#       (EventLoopState<64> ~272KB each) far past interactive ulimits; the ambient 12.5MB shell
#       limit ABORTED the gate with a stack-overflow in main. The gate must not depend on whatever
#       stack limit the invoking shell happens to carry.
#   (b) ASAN_OPTIONS=detect_leaks=0 — the test harness exits WITHOUT teardown BY DESIGN (process
#       exit reclaims); LSan would report the init-time fixture allocations (~115MB / 765 allocs,
#       100% classified to PortfolioController_Init / EventLoopState_Init / test-local fixtures at
#       the A.5 audit — ZERO runtime-path leaks) as failures. Leak-mode runs are a deliberate
#       separate investigation, not the gate.
#
# Usage: tools/run_sanitizer_suite.sh [asan] [ubsan]     (default: both lanes)
# Requires the lane build dirs to exist (./build.sh asan / ./build.sh ubsan first).
set -uo pipefail
# FOXML_SUITE_ROOT override = hermetic self-test hook (run_sanitizer_suite_selftest.sh points it
# at stub lanes) + machine-portable-resolver discipline.
ROOT="${FOXML_SUITE_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
ulimit -s unlimited 2>/dev/null || ulimit -s 65536 || true
export ASAN_OPTIONS="detect_leaks=0${ASAN_OPTIONS:+:$ASAN_OPTIONS}"

lanes=("$@"); [ ${#lanes[@]} -eq 0 ] && lanes=(asan ubsan)
fail=0
for lane in "${lanes[@]}"; do
    bin="$ROOT/build_$lane/controller_test"
    if [ ! -x "$bin" ]; then
        echo "[$lane] MISSING $bin — run ./build.sh $lane first" >&2; fail=1; continue
    fi
    echo "=== $lane lane (ulimit -s $(ulimit -s); detect_leaks=0) ==="
    # Full output to a log; show the verdict + EVERY failure line (a bare tail eats the
    # [FAIL] details — evidence-destroying instrumentation; A.5 close-out lesson).
    log="/tmp/run_sanitizer_suite_$lane.log"
    if ( cd "$ROOT/build_$lane" && ./controller_test ) > "$log" 2>&1; then
        tail -4 "$log"; echo "[$lane] OK (full log: $log)"
    else
        rg -n "\[FAIL" "$log" | head -20; tail -6 "$log"
        echo "[$lane] FAILED (full log: $log)" >&2; fail=1
    fi
done
exit $fail
