#!/usr/bin/env bash
# Negative self-test for check_cfg_key_prefix_drift.py (D-137 teeth).
#
# Delegates to the tool's INLINE --selftest, which (a) asserts its own parser ground-truth
# (verify_parser_ground_truth — the parse site recognizes `node_`, so the guard can't go
# vacuously-green if the parser drifts; Class-51 self-defense) and (b) proves the guard goes
# RED on a retired-prefix target. Exit 0 = teeth intact; non-zero = the guard lost its teeth.
#
# Sister pattern: run_sanitizer_suite_selftest.sh / test_check_h14_no_bitfield.py (the D-137
# negative-self-test cohort). Enrolled TEST-HARNESS in DOCS/TOOLS.md.
exec python3 "$(dirname "$0")/check_cfg_key_prefix_drift.py" --selftest
