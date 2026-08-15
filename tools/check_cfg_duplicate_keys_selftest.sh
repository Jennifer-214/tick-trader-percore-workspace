#!/usr/bin/env bash
# Negative self-test for check_cfg_duplicate_keys.py (D-137 teeth).
#
# Two layers, deliberately:
#
#   (1) the tool's INLINE --selftest — 7 teeth over the scan function itself
#       (positive control, negative control, comment x2, whitespace, prose, prefix,
#       file round-trip).
#
#   (2) an END-TO-END PROCESS-LEVEL proof, which the inline teeth cannot give:
#       plant a duplicate in a real temp cfg, invoke the tool as the gate invokes it,
#       and assert the PROCESS exits non-zero. This closes the vacuity mode where the
#       scan function is correct but `main()` drops the result on the floor and returns
#       0 anyway — a guard that detects and does not gate (Class 51 sub-shape B', the
#       "decorative detector"). The inline teeth would stay green through that bug;
#       only an exit-code assertion catches it.
#       The mirror assertion (clean file MUST exit 0) proves the RED is caused by the
#       duplicate and not by the tool erroring out on every input.
#
# Exit 0 = teeth intact; non-zero = the guard lost its teeth.
#
# Sister pattern: check_cfg_key_prefix_drift_selftest.sh / run_sanitizer_suite_selftest.sh
# (the D-137 negative-self-test cohort). Enrolled TEST-HARNESS in DOCS/TOOLS.md.
set -u
TOOL="$(dirname "$0")/check_cfg_duplicate_keys.py"
fails=0

# --- layer 1: the inline teeth ---
if ! python3 "$TOOL" --selftest; then
    echo "  [teeth] FAIL — inline --selftest did not pass"
    fails=$((fails + 1))
fi

TMPDIR_SELF="$(mktemp -d)"
trap 'rm -rf "$TMPDIR_SELF"' EXIT

# --- layer 2a: RED on target (process-level) ---
printf 'a=1\nb=2\na=3\n' > "$TMPDIR_SELF/dup.cfg"
python3 "$TOOL" "$TMPDIR_SELF/dup.cfg" > /dev/null 2>&1
rc=$?
if [ "$rc" -eq 0 ]; then
    echo "  [teeth] FAIL — planted duplicate did NOT make the process exit non-zero"
    echo "                 (the scan may be correct while main() fails to gate on it)"
    fails=$((fails + 1))
fi

# --- layer 2b: no false-RED (proves 2a's RED is caused by the duplicate) ---
printf 'a=1\nb=2\nc=3\n' > "$TMPDIR_SELF/clean.cfg"
python3 "$TOOL" "$TMPDIR_SELF/clean.cfg" > /dev/null 2>&1
rc=$?
if [ "$rc" -ne 0 ]; then
    echo "  [teeth] FAIL — clean cfg wrongly exits non-zero (rc=$rc); the RED above proves nothing"
    fails=$((fails + 1))
fi

if [ "$fails" -ne 0 ]; then
    echo "[cfg-duplicate-keys] TEETH BROKEN — $fails layer(s) failed"
    exit 1
fi
echo "[cfg-duplicate-keys] TEETH INTACT — inline 7 teeth + process-level RED-on-target + no-false-RED"
exit 0
