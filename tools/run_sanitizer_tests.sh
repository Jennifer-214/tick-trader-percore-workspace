#!/usr/bin/env bash
# Run the char-test suite under a sanitizer build so it ACTUALLY COMPLETES.
#
# Why this exists (2026-08-16): `./build.sh asan && ./build_asan/controller_test` was unusable —
# it aborted on startup with `AddressSanitizer: stack-overflow ... in main` and never ran a single
# test. Two independent reasons, and neither is a bug in the engine:
#
#   1. STACK. The engine takes H1 seriously (no malloc/new on any steady-state path), so the test
#      fixtures are stack objects and `main`'s frame is already large. ASan wraps every stack object
#      in redzones, inflating that frame to ~72MB measured (bp-sp at the abort) against the usual
#      8MB `ulimit -s`. The plain -O3 build fits fine; the instrumented one cannot.
#   2. LEAKS. Boot-time node arenas are allocated once and never freed — correct for a process meant
#      to run for weeks, and the tests construct many controllers without tearing them down. So
#      LeakSanitizer reports ~187MB across ~1100 allocations from `PortfolioController_Init` /
#      `EventLoopState_Init` / `_alloc_and_init_slow_state`, EVERY run, by design.
#
# (2) is the nastier one, because LSan runs at exit and takes the process down before stdout is
# flushed: the last line is truncated mid-word and the visible tail becomes an INTERMEDIATE section
# summary. It reads exactly like "the suite stopped a third of the way through" when in fact every
# test ran and passed. Do not chase that ghost — it cost a close-session cycle.
#
# With both handled: 3755 passed, 0 failed, 0 memory errors, rc=0.
#
# Usage:  tools/run_sanitizer_tests.sh [asan|ubsan|tsan]     (default: asan)
#         LEAKS=1 tools/run_sanitizer_tests.sh asan          (opt IN to the leak report)
set -u
cd "$(dirname "$0")/.." || exit 2

MODE="${1:-asan}"
case "$MODE" in
    asan|ubsan|tsan) ;;
    *) echo "usage: $0 [asan|ubsan|tsan]"; exit 2 ;;
esac

BIN="build_${MODE}/controller_test"
[ -x "$BIN" ] || { echo "[sanitizer] MISSING $BIN — run ./build.sh ${MODE} first"; exit 2; }

# 256MB: comfortably above the ~72MB measured instrumented frame, with room for fixtures to grow.
# If this ever overflows again the frame has grown ~3.5x; raise it rather than deleting a test.
STACK_KB=262144

# Leak reporting is OFF by default and that is a DELIBERATE, narrow call: the leaks are boot arenas
# never freed at exit. It is off so the suite can complete and so the REAL detectors (use-after-free,
# heap/stack overflow, UB) are readable. Opt back in with LEAKS=1 when auditing allocation lifetime
# specifically — and expect the by-design arenas in the report.
if [ "${LEAKS:-0}" = "1" ]; then
    OPTS=""
    echo "[sanitizer] leak detection ON — expect by-design boot arenas; stdout may truncate at exit"
else
    OPTS="detect_leaks=0"
fi

# TSan suppressions live in a REVIEWED file with a stated reason per entry (tools/tsan_suppressions.txt).
# Currently one entry: the TUISnapshot seqlock, whose payload copy races by design and whose real
# guard is a tear-count test TSan cannot express. Announce it every run — a silently-applied
# suppression file is how detection quietly narrows to nothing.
SUPP="tools/tsan_suppressions.txt"
TSAN_OPTS=""
if [ "$MODE" = "tsan" ] && [ -f "$SUPP" ]; then
    TSAN_OPTS="suppressions=${SUPP}"
    echo "[sanitizer] tsan suppressions ACTIVE from ${SUPP}:"
    grep -vE '^\s*(#|$)' "$SUPP" | sed 's/^/             /'
fi

echo "[sanitizer] ${MODE}: ulimit -s ${STACK_KB} · ASAN_OPTIONS='${OPTS}' · TSAN_OPTIONS='${TSAN_OPTS}'"
out=$(bash -c "ulimit -s ${STACK_KB}; ASAN_OPTIONS='${OPTS}' TSAN_OPTIONS='${TSAN_OPTS}' UBSAN_OPTIONS=print_stacktrace=1 ./${BIN} 2>&1")
rc=$?

# Report on the SUITE's own verdict, not just rc — a sanitizer can exit 0 while the suite failed,
# and can exit nonzero for a leak while every test passed. They answer different questions.
echo "$out" | tail -4
# Match BOTH severities and BOTH spellings. TSan reports a data race as `WARNING: ThreadSanitizer:`
# and summarises as `ThreadSanitizer: reported N warnings` — it does NOT say ERROR. The first cut of
# this script grepped only `ERROR:` and duly printed PASS on a run with rc=66 and 3 live warnings:
# the script's own instance of the AR-18 shape it was written to help avoid. Keep this pattern wide.
errs=$(echo "$out" | grep -cE "(ERROR|WARNING): (Address|Thread|Leak|Memory)Sanitizer|runtime error:")
# TSan's own tally is authoritative when present — a warning suppressed from the body still counts.
tsan_n=$(echo "$out" | sed -nE 's/.*ThreadSanitizer: reported ([0-9]+) warnings.*/\1/p' | tail -1)
[ -n "${tsan_n:-}" ] && [ "$tsan_n" -gt 0 ] && errs=$((errs + tsan_n))
final=$(echo "$out" | grep -E "RESULTS:" | tail -1)

echo "----"
echo "[sanitizer] final suite line : ${final:-<none — the run did not reach the end>}"
echo "[sanitizer] sanitizer errors : ${errs}"
echo "[sanitizer] exit code        : ${rc}"

# A missing final RESULTS is the interesting failure: it means the process died mid-suite, which is
# NOT the same as a test failing and must not be reported as a pass.
if [ -z "$final" ]; then
    echo "[sanitizer] FAIL — the suite never printed a final RESULTS line; the process ended early."
    exit 1
fi
if [ "$errs" -ne 0 ]; then
    echo "[sanitizer] FAIL — ${errs} sanitizer diagnostic(s); grep the output above."
    exit 1
fi
case "$final" in
    *"0 failed"*) ;;
    *) echo "[sanitizer] FAIL — the suite reported failures."; exit 1 ;;
esac

# Every test passed AND no diagnostic fired — but the sanitizer's own exit code is a THIRD signal,
# and disagreeing with it silently is how a run gets rubber-stamped. Surface the disagreement.
if [ "$rc" -ne 0 ]; then
    echo "[sanitizer] FAIL — suite green and no diagnostic parsed, yet ${MODE} exited ${rc}."
    echo "             The runtime saw something this script did not. Read the full output;"
    echo "             do NOT treat a green suite as clearing a nonzero sanitizer exit."
    exit 1
fi
echo "[sanitizer] PASS — suite complete under ${MODE}, no sanitizer diagnostics, rc=0."
exit 0
