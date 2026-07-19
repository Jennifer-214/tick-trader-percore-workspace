#!/usr/bin/env bash
# D-137 discoverable negative self-test for check_register_fit.py. (has teeth: the tool's --selftest
# goes RED unless access_cost classifies each case right — single-mov (a mov-width power-of-2, naturally
# aligned) vs unaligned (off%size!=0) vs multi-op (non-mov-width size) vs unknown (unresolved size).)
set -euo pipefail
exec python3 "$(dirname "$0")/check_register_fit.py" --selftest
