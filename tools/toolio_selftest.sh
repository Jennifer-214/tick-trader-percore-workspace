#!/usr/bin/env bash
# D-137 discoverable negative self-test for toolio.py (E.1.2.B 0.1.5). has teeth: toolio's --selftest
# plants a bad payload row, a bad findings row, and an unknown table and asserts each REDs, plus a
# known-good envelope round-trips (schema sourced from the registry) — so the emit/validate SSoT
# cannot be vacuously green.
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/toolio.py" --selftest
