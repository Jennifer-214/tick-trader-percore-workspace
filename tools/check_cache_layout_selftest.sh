#!/usr/bin/env bash
# check_cache_layout_selftest.sh — D-137 discoverable negative self-test for check_cache_layout
# (STANDING-CI HARD since the D-414 leaf-3 strict-new promotion). Thin wrapper running its
# `--selftest`: proves RED-direction on planted violations (cross-thread straddle FAIL ·
# size-drift FAIL · partial→straddle-unverified FAIL) and GREEN on clean/exempt/benign cases,
# plus the writer tri-state (refuses none-on-partial) and the orient-only arming parser.
# Sister to check_code_tag_blocks_selftest.sh (same wrapper shape).
# has teeth: the wrapped --selftest carries expect_red gate cases — planted cross-thread
# straddle / size-drift / partial violations MUST fire (non-vacuity is asserted in-suite).
set -euo pipefail
cd "$(dirname "$0")"
exec python3 check_cache_layout.py --selftest
