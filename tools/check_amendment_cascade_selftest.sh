#!/usr/bin/env bash
# D-137 discoverable negative self-test for check_amendment_cascade.py.
# Proves the CP-1 detector has TEETH: extraction ignores terms present on both
# sides of a diff and terms only ADDED; the historical-record filter preserves
# frozen dirs + superseded frontmatter but not a `status:` buried in prose; the
# rarity gate suppresses shared vocabulary while sparing citable IDs; and both
# the positive and negative controls fire (a detector that reds on everything is
# as useless as one that reds on nothing).
set -uo pipefail
cd "$(dirname "$0")"
python3 check_amendment_cascade.py --selftest
rc=$?
if [ $rc -ne 0 ]; then
  echo "[amendment-cascade selftest wrapper] FAIL (rc=$rc)" >&2
  exit 1
fi
echo "[amendment-cascade selftest wrapper] PASS (guard has teeth)"
