#!/usr/bin/env bash
# D-137 discoverable negative self-test for check_corpus_membership.py. (has teeth: this script IS
# the negative test — the tool's --selftest goes RED unless every planted mutation is FLAGGED, so
# it needs no test-of-itself.)
#
# The tool's --selftest proves NON-VACUITY (anti-Class-51) on the properties that actually carry
# the gate:
#   · a planted ADD is flagged, and a planted DELETE is flagged — the DELETE direction is the
#     expensive one, since a file that silently leaves the corpus stops being checked at all
#     while every other gate stays green;
#   · a planted RENAME with the count UNCHANGED is flagged — the exact defect a count-pin misses,
#     measured from this repo's own history (commit 1da1c1c moved SIX file identities with the
#     tracked count going 167 -> 167, delta ZERO);
#   · a REORDER is flagged — order is part of the pin, not incidental, and it is the axis two
#     hand-written walkers most plausibly diverge on (parity cannot see it: both legs sort before
#     diffing, parity_check.sh:24-25);
#   · an ABSENT golden is a HARD failure rather than a pass — "nothing to compare" would plant a
#     vacuously-green guard inside the layer built to close Class-51;
#   · every PIN entry is git-TRACKED, AND the tracked filter is proven non-trivial (SCAN 200 vs
#     PIN 171) — an equal count would mean the filter was never exercised. That assertion was
#     itself written vacuously the first time (`all(... or True)`), which is how easy the shape
#     is to produce even while building the tool that exists to catch it.
set -euo pipefail
exec python3 "$(dirname "$0")/check_corpus_membership.py" --selftest
