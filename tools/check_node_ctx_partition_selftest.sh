#!/usr/bin/env bash
# D-137 discoverable negative self-test for check_node_ctx_partition.py (E.1.2 D-421 step 2).
#
# Thin wrapper running the tool's hermetic --selftest (17 teeth). What it proves, and why each
# leg is here rather than assumed:
#
#   THE THREE RED DIRECTIONS, each of which fails differently:
#     UNACCOUNTED   — an unenrolled member fires (the node_gross_wins silent-drop class,
#                     TECH_DEBT-196; the founding instance).
#     STALE-EXEMPT  — an exemption naming a NON-member fires. This is the vacuity leg: a stale
#                     row protects nothing while making the partition read as fully accounted,
#                     so without this tooth the guard's own INPUT can rot green.
#     CONTRADICTION — a member both persisted AND exempt fires; the tool refuses to guess which
#                     declaration is the lie.
#
#   THE REFUSALS (rc 2, never an empty-set pass — Class 57 / Class 51):
#     absent persist registry · absent exemption registry · unknown category · stub rationale ·
#     unterminated rationale. An absent registry is the sharp one: with the sets swapped it would
#     make EVERY member look fine, so "cannot compute" must never render as "nothing to report".
#
#   THE POSITIVE CONTROLS (without which the guard could RED on everything and still look rigorous):
#     a clean partition yields 0 findings · a well-formed exemption is ACCEPTED · a quoted
#     rationale containing commas stays ONE column · an always-RED category is a VALID ROW
#     (recordable) AND STILL REDS (recorded is not excused — the row exists to state what we know
#     without the field counting as accounted).
#
#   REAL-TREE NON-VACUITY (the leg that catches a parser that stopped parsing):
#     tt::NodeContext<64> yields members · the persist registry yields covered names · and the two
#     sets actually OVERLAP. That last one is load-bearing: two disjoint sets would mean the tool
#     is comparing two different vocabularies, which subtracts to "everything unaccounted" or
#     "everything fine" depending on direction, and either reads as a working guard.
#
# This wrapper has teeth by delegation: the parent's --selftest carries five expect_red refusal
# legs (absent persist registry · absent exemption registry · unknown category · stub rationale ·
# unterminated rationale), each of which must rc-FAIL rather than empty-pass, plus the four
# positive controls above. A wrapper whose parent only ever asserted green would be the
# Class-51 shape it is here to catch.
#
# Sister wrappers: node_persist_layout_selftest.sh (its forward-facing half — that one asks
# "are the rows we have right?", this one asks "are these ALL the rows?") ·
# check_reset_before_producer_selftest.sh · check_corpus_membership_selftest.sh.
set -u
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/check_node_ctx_partition.py" --selftest
