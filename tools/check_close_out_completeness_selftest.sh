#!/usr/bin/env bash
# D-137 discoverable negative self-test for check_close_out_completeness.py (M8 / TECH_DEBT-250).
#
# Two halves, because the tool's own --selftest proves its INTERNALS while this proves its VERDICT:
#   (a) the tool's --selftest (surface table non-empty, every row actionable, every path EXISTS —
#       a typo'd path would be silently un-checkable, which is the vacuity mode that matters here);
#   (b) a REAL negative case: a window in which an auto-write surface saw ZERO commits MUST exit 1.
#
# (b) is anchored on a SYNTHETIC surface rather than a real one, deliberately. Anchoring it to a
# live ledger would make the test pass or fail depending on whether that ledger happened to be
# touched recently — the same live-value-anchoring that left the H21 version-decrease tooth dead
# for an unknown period (see check_identifier_retirement_selftest.sh). A synthetic path is untouched
# by construction, forever.
#
# ⚠️ The synthetic surface is NOT sufficient on its own, and this cost a close-session cycle to
# find (2026-08-16). `run()` evaluates TWO halves — the surface table AND the live active handoff's
# quality/sync findings — and a single HIGH from the second half returns 1 no matter what the first
# half concluded. So the probes below ALSO stub the handoff-quality half out. Without that stub:
#   - the --explain tooth went RED whenever the live handoff had any HIGH finding, for a reason
#     having nothing to do with --explain (this is how it was found);
#   - and worse, the UNTOUCHED tooth could pass for the WRONG REASON — hq_hi alone yields rc=1,
#     so untouched-detection could be wholly broken while the tooth still read green.
# Live-value-anchoring re-entered through a second door. Isolate the unit you are actually asserting.
set -u
cd "$(dirname "$0")/.." || exit 2
TOOL="tools/check_close_out_completeness.py"
fail=0

python3 "$TOOL" --selftest >/dev/null 2>&1 || { echo "SELFTEST FAIL: the tool's own --selftest is RED"; fail=1; }
[ "$fail" = 0 ] && echo "  ok: internals --selftest GREEN"

# (b) VERDICT teeth — a never-committed path must be reported UNTOUCHED and exit 1.
#     Both probes stub the handoff-quality half (see the header note) so the assertion is about
#     the surface table and NOTHING else.
out=$(python3 - <<'PY' 2>&1
import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "tools"))
import check_close_out_completeness as C
C.AUTO_WRITE_SURFACES = [("DOCS/__never_committed_probe__.md", "probe", "planted")]
C.check_handoff_quality = lambda *a, **k: []
C.check_sync_owed = lambda *a, **k: []
sys.exit(C.run("HEAD~20", 1, [], False))
PY
)
rc=$?
if [ "$rc" -eq 1 ] && echo "$out" | grep -q "ZERO commits"; then
    echo "  ok: an untouched auto-write surface -> RED (exit 1)"
else
    echo "SELFTEST FAIL: an untouched surface did NOT go RED (rc=$rc)"; fail=1
fi

# and --explain must SUPPRESS it, else the escape hatch is broken and the guard is unusable
out2=$(python3 - <<'PY' 2>&1
import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "tools"))
import check_close_out_completeness as C
C.AUTO_WRITE_SURFACES = [("DOCS/__never_committed_probe__.md", "probe", "planted")]
C.check_handoff_quality = lambda *a, **k: []
C.check_sync_owed = lambda *a, **k: []
sys.exit(C.run("HEAD~20", 1, ["DOCS/__never_committed_probe__.md=not owed this session"], False))
PY
)
rc2=$?
if [ "$rc2" -eq 0 ] && echo "$out2" | grep -q "EXPLAINED"; then
    echo "  ok: --explain suppresses it (the escape hatch works)"
else
    echo "SELFTEST FAIL: --explain did not suppress an untouched surface (rc=$rc2)"; fail=1
fi

# (c) The stub above must not become a permanent blindfold: assert the handoff-quality half is
#     REACHED by run() and CAN drive the verdict on its own. Otherwise a future refactor could
#     delete that half entirely and (b) would stay green — the stub would be hiding its absence.
out3=$(python3 - <<'PY' 2>&1
import sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "tools"))
import check_close_out_completeness as C
C.AUTO_WRITE_SURFACES = [("DOCS/__never_committed_probe__.md", "probe", "planted")]
C.check_handoff_quality = lambda *a, **k: [("HIGH", "planted handoff-quality finding")]
C.check_sync_owed = lambda *a, **k: []
# surface explained away -> the ONLY thing that can fail is the handoff-quality half
sys.exit(C.run("HEAD~20", 1, ["DOCS/__never_committed_probe__.md=not owed"], False))
PY
)
rc3=$?
if [ "$rc3" -eq 1 ] && echo "$out3" | grep -q "planted handoff-quality finding"; then
    echo "  ok: a HIGH handoff-quality finding alone -> RED (the second half has teeth too)"
else
    echo "SELFTEST FAIL: a planted HIGH handoff-quality finding did not go RED (rc=$rc3)"; fail=1
fi

if [ "$fail" = 0 ]; then echo "check_close_out_completeness_selftest: PASS (guard has teeth)"; else echo "check_close_out_completeness_selftest: FAIL"; fi
exit "$fail"
