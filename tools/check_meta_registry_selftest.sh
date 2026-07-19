#!/usr/bin/env bash
# D-137 discoverable negative self-test for check_meta_registry.py. (has teeth: the tool's --selftest
# goes RED unless evaluate_registry FLAGS each violation — an unregistered codebase macro (Check 1) /
# a FOREACH_REGISTRY row with no #define (Check 2) / a LEVEL-PARENT topology violation (Check 3) — AND
# passes a clean set, AND the canonical check_doc_metadata.ENGINE resolver actually locates the real
# MetaRegistry.hpp (the regression guard for the 2026-07-19 canonical-resolver fix).)
set -euo pipefail
exec python3 "$(dirname "$0")/check_meta_registry.py" --selftest
