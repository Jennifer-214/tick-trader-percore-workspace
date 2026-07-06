#!/usr/bin/env bash
# D-137 negative self-test for check_code_tag_blocks.py.  (has teeth: this script IS the
# negative test — its --selftest goes RED on each violation class, so it needs no test-of-itself.)
#
# The tool's --selftest proves NON-VACUITY: it goes RED on each violation class (unknown
# category · two-categories-per-line · missing/mismatched [END_*] closer · bad [TAG] value ·
# [END_*] with no open) AND stays GREEN on a clean block of each first-class type
# (function/struct/registry/file). Exits non-zero if ANY violation class is missed — so this
# script IS the discoverable "prove it goes red on its target" test the tools-inventory wants.
set -euo pipefail
exec python3 "$(dirname "$0")/check_code_tag_blocks.py" --selftest
