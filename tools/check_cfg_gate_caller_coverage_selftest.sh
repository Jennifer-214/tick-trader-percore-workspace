#!/usr/bin/env bash
# Negative self-test for check_cfg_gate_caller_coverage.py (D-137 teeth; ③ item-6) — delegates to the
# tool's inline --selftest, which proves the gate-detection distinguishes a GATED caller from an UNGATED
# one (so the guard goes RED on a real ungated caller; not a vacuously-green guard, RBP Class-51).
exec python3 "$(dirname "$0")/check_cfg_gate_caller_coverage.py" --selftest
