#!/usr/bin/env bash
# tools/run_all_tests.sh — unified test runner (TECH_DEBT-176; D-201)
#
# One command verifies EVERYTHING: the C++ controller_test suite + the doc/plan CI
# (check_session_docs.sh, itself the aggregator of the check_*.py family) + the
# calls_graph_diff orphan check (+ the asan/ubsan/tsan lanes under --full). Aggregates
# to ONE green/red so "running the tests verifies everything" (operator, .E.0.10).
#
# Usage:
#   ./tools/run_all_tests.sh            # --fast (default): C++ suite + doc-CI + orphan check
#   ./tools/run_all_tests.sh --full     # + asan/ubsan/tsan lanes (slow; builds each)
#   ./tools/run_all_tests.sh --selftest # D-137 negative self-test (inject a fail -> assert red)
#
# Exit 0 = all HARD components pass. Exit 1 = a HARD component failed (see the SUMMARY).
# NOTE (AR-5 — evidence-destroying instrumentation): every component runs DIRECTLY; its real
# exit code is captured. None is piped through `| tail` / `| rg -c` that could mask its rc.

set -uo pipefail   # NOT -e: run ALL components + aggregate (do not bail on the first failure)
cd "$(cd "$(dirname "$0")/.." && pwd)"   # repo root

TIER="${1:---fast}"
NAMES=(); RESULTS=(); HARD_FAIL=0

record() {  # record <name> <HARD|ADV> <rc>
    local name="$1" hard="$2" rc="$3"
    if [ "$rc" -eq 0 ]; then RESULTS+=("PASS  "); else RESULTS+=("FAIL($rc)"); [ "$hard" = "HARD" ] && HARD_FAIL=1; fi
    NAMES+=("$name")
}

banner() { printf '\n====================================================\n  > %s\n====================================================\n' "$1"; }

run() {  # run <name> <HARD|ADV> -- <cmd...>
    local name="$1" hard="$2"; shift 3   # drop name, hard, the literal '--'
    banner "$name"
    "$@"; record "$name" "$hard" "$?"
}

if [ "$TIER" = "--selftest" ]; then
    # D-137 negative self-test: a forced-failing HARD component MUST flip HARD_FAIL -> exit 1.
    run "selftest:forced-fail" HARD -- false
    if [ "$HARD_FAIL" -eq 1 ]; then echo "OK selftest PASS — runner correctly reports a HARD failure"; exit 0
    else echo "XX selftest FAIL — runner did NOT catch a forced failure"; exit 1; fi
fi

# --- HARD components (always) ---
run "C++ suite (controller_test)"      HARD -- ./build.sh test
run "doc/plan CI (check_session_docs)" HARD -- ./tools/check_session_docs.sh
run "orphan check (calls_graph_diff)"  HARD -- ./tools/calls_graph_diff.sh

# --- --full / --ci: sanitizer lanes (COMPOSE the canonical gate; do NOT reimplement the
#     asan/ubsan/tsan build+run here — run_sanitizer_suite.sh owns the pinned run-conditions
#     [ulimit -s unlimited + detect_leaks=0; TECH_DEBT-161]. Class-21 parallel-infra avoidance.) ---
if [ "$TIER" = "--full" ] || [ "$TIER" = "--ci" ]; then
    run "sanitizers (run_sanitizer_suite)" HARD -- ./tools/run_sanitizer_suite.sh
fi

# --- SUMMARY ---
banner "run_all_tests SUMMARY ($TIER)"
for i in "${!NAMES[@]}"; do printf '  [%s]  %s\n' "${RESULTS[$i]}" "${NAMES[$i]}"; done
echo
if [ "$HARD_FAIL" -eq 0 ]; then echo "ALL HARD COMPONENTS PASS"; exit 0
else echo "HARD FAILURE — see the components above"; exit 1; fi
