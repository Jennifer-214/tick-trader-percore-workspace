#!/usr/bin/env bash
# D-137 discoverable negative self-test for check_reset_before_producer.py (E.1.2 D-421).
# Thin wrapper running the tool's hermetic --selftest. This wrapper has teeth by delegation
# — the parent's --selftest carries every leg below, including the expect_red refusals:
#   planted producer-BEFORE-reset FIRES · correct order PASSES (the positive control,
#   without which the check could red on everything and look rigorous) · the inverse
#   direction inverts the verdict · a vanished reset OR producer site REFUSES rc 2,
#   never an empty-set pass · real-tree non-vacuity (both live rules resolve at HEAD).
# The last leg is the load-bearing one: this guard's whole subject is a regex pair, and
# a pattern that stops matching is indistinguishable from a clean codebase unless
# absence is fatal. Its first live run RED-ed on a mis-encoded RULE direction (mine),
# not on wrong code — which is the behaviour to preserve.
# Sister wrappers: node_persist_layout_selftest.sh / check_cfg_duplicate_keys_selftest.sh.
set -u
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/check_reset_before_producer.py" --selftest
