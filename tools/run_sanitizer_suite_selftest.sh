#!/usr/bin/env bash
# run_sanitizer_suite_selftest.sh — teeth-proof for run_sanitizer_suite.sh (D-137: every
# load-bearing tool proves it goes RED on its target). Hermetic: stub lanes via FOXML_SUITE_ROOT.
#
# Proves: (1) a FAILING lane -> runner exits nonzero AND surfaces the [FAIL] line (the
# evidence-preservation property — a bare tail ate a failing test's name at the A.5 dogfood);
# (2) a PASSING lane -> runner exits 0.
set -uo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
RUNNER="$HERE/run_sanitizer_suite.sh"
# Stub dir lives NEXT TO the tools (not /tmp): hardened hosts mount /tmp noexec, which made the
# stub binaries unrunnable and produced two phantom selftest failures on first run (the runner
# was fine; the SELFTEST's environment assumption wasn't — verify-the-verifier, again).
TMP="$(mktemp -d "$HERE/.selftest_tmp.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
fail=0

mk_stub() {  # $1 = lane dir; $2 = pass|fail
    mkdir -p "$TMP/build_$1"
    if [ "$2" = "fail" ]; then
        cat > "$TMP/build_$1/controller_test" <<'STUB'
#!/usr/bin/env bash
echo "  [PASS] selftest stub: something fine"
echo "  [FAIL] selftest stub: THE-INJECTED-FAILURE-NAME"
echo "  RESULTS: 1 passed, 1 failed"
exit 1
STUB
    else
        cat > "$TMP/build_$1/controller_test" <<'STUB'
#!/usr/bin/env bash
echo "  [PASS] selftest stub: all fine"
echo "  RESULTS: 1 passed, 0 failed"
exit 0
STUB
    fi
    chmod +x "$TMP/build_$1/controller_test"
}

# RED case: failing asan stub — runner must exit nonzero AND print the [FAIL] line.
mk_stub asan fail
out="$(FOXML_SUITE_ROOT="$TMP" "$RUNNER" asan 2>&1)"; rc=$?
if [ $rc -eq 0 ]; then echo "FAIL: runner exited 0 on a FAILING lane"; fail=1; fi
if ! grep -q "THE-INJECTED-FAILURE-NAME" <<<"$out"; then
    echo "FAIL: runner did NOT surface the [FAIL] line (evidence-preservation broken)"; fail=1
fi

# GREEN case: passing asan stub — runner must exit 0.
mk_stub asan pass
if ! FOXML_SUITE_ROOT="$TMP" "$RUNNER" asan >/dev/null 2>&1; then
    echo "FAIL: runner exited nonzero on a PASSING lane"; fail=1
fi

# MISSING-lane case: runner must exit nonzero (never silently skip a requested lane).
if FOXML_SUITE_ROOT="$TMP" "$RUNNER" ubsan >/dev/null 2>&1; then
    echo "FAIL: runner exited 0 on a MISSING lane"; fail=1
fi

if [ $fail -eq 0 ]; then echo "PASS -- run_sanitizer_suite teeth-proof (RED-on-fail + [FAIL] surfaced + GREEN-on-pass + RED-on-missing)"; fi
exit $fail
