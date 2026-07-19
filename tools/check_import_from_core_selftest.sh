#!/usr/bin/env bash
# D-137 discoverable negative self-test for check_import_from_core.py (E.1.2.B 0.1 / D-375). (has teeth:
# the tool's --selftest plants a roll-own-root + a hardcoded-absolute path and asserts both go RED, and a
# foxroots-importer PASSES — so the lint cannot be vacuously green.)
set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$DIR/check_import_from_core.py" --selftest
