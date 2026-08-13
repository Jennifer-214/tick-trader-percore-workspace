#!/usr/bin/env bash
# D-137 negative-selftest wrapper for check_toolio_kind_parity.py — has teeth: expect_red on
# planted drift (missing-consumer / plugin-ghost / stale-exempt all FIRE) and REFUSES rather
# than empty-passes on mutilated inputs (rc 2). The teeth live in the tool's --selftest (6 legs,
# rc-checked); this wrapper is the enrollment-visible artifact + the one manual entry point.
set -u
here="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$here/check_toolio_kind_parity.py" --selftest
