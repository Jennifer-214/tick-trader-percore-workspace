#!/usr/bin/env bash
# D-137 discoverable negative self-test for check_schema_version.py. (has teeth: this script IS the
# negative test — the tool's --selftest goes RED unless it FLAGS a drifted [SCHEMA]_[v1] fixture and
# passes both a locked-version file and an [SCHEMA]_[exempt] one, so it needs no test-of-itself.)
#
# The tool's --selftest proves NON-VACUITY (anti-Class-51): it derives the locked version from the
# spec SSoT ("Status: LOCKED — [SCHEMA]_[v1.0]", D-346), asserts a locked-version file passes CLEAN,
# a drifted [SCHEMA]_[v1] file is FLAGGED, and an [SCHEMA]_[exempt] file opts out. Exits non-zero if
# any regress — so this IS the discoverable "prove it goes red on its target" test the inventory wants.
set -euo pipefail
exec python3 "$(dirname "$0")/check_schema_version.py" --selftest
