#!/usr/bin/env bash
# D-137 discoverable negative self-test for check_conversion_completeness.py. (has teeth: this
# script IS the negative test — the tool's --selftest goes RED unless it correctly flags a known
# half-conversion + passes a known-complete one, so it needs no test-of-itself.)
#
# The tool's --selftest proves NON-VACUITY (anti-Class-51): it asserts the canonical-COMPLETE
# reference CoreFrameworks/ExecutionCore.hpp scans CLEAN, the known half-conversion
# ML_Headers/GateControlNetwork.hpp is FLAGGED (GCN_input + GCN_network lumped in a [FUNCTION]
# block), trivial ≤3-field return-structs stay EXEMPT, and same-family sub-registry variants stay
# EXEMPT while unrelated registries do not (policy #1). Exits non-zero if ANY of those regress —
# so this IS the discoverable "prove it goes red on its target" test the tools-inventory wants.
set -euo pipefail
exec python3 "$(dirname "$0")/check_conversion_completeness.py" --selftest
