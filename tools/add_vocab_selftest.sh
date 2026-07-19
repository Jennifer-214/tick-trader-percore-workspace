#!/usr/bin/env bash
# D-137 discoverable negative self-test for add_vocab.py. (has teeth: the tool's --selftest goes RED
# unless its PURE insert helpers correctly append/insert AND refuse duplicates + existing tokens.)
#
# add_vocab.py --selftest proves the insert logic non-vacuously (anti-Class-51): a category token
# appends to the ```category-set``` fence + a duplicate/existing token is REFUSED; a concern/surface
# [TAG] row inserts into the correct axis table (CONCERN before SURFACE) + a duplicate is REFUSED.
# Exits non-zero if any regress — the discoverable "prove it does the thing" test the inventory wants.
set -euo pipefail
exec python3 "$(dirname "$0")/add_vocab.py" --selftest
