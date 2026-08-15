#!/usr/bin/env bash
# D-137 discoverable negative self-test for node_persist_layout.py (E.1.2 D-305).
# Thin wrapper running the tool's hermetic --selftest: planted DROP / ADD /
# count-neutral NAME-SWAP (the triple-vacuity case) / TYPE change / REORDER /
# delegate-internal DROP each FIRE; unmapped-delegate + missing-macro REFUSE
# (rc 2, never an empty-set pass); real-tree non-vacuity (29 parent + 17
# delegate-internal rows resolve at HEAD). This wrapper has teeth by
# delegation: the parent's --selftest carries the expect_red refusal legs
# (unmapped delegate + missing macro must rc-fail, never empty-pass).
# Sister wrappers: check_import_from_core_selftest.sh / toolio_selftest.sh.
set -u
exec python3 "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/node_persist_layout.py" --selftest
