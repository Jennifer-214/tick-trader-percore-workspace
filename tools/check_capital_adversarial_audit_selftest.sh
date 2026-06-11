#!/bin/bash
# check_capital_adversarial_audit_selftest.sh — negative self-test (D-137) for
# check_capital_adversarial_audit.py. Proves the guard goes RED on an UNMARKED capital
# test assertion and GREEN once the `// ADV-REFUTE` marker is present. Hermetic (temp dir).
set -uo pipefail
TOOL="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/check_capital_adversarial_audit.py"
DIR="$(mktemp -d)"
trap 'rm -rf "$DIR"' EXIT
FAIL=0

# 1) UNMARKED capital assert -> must FLAG (--strict exits 1)
printf 'void t(){ check("x", Money_Eq(r->oms.total_fees, MQ(2.412))); }\n' > "$DIR/probe.cpp"
if python3 "$TOOL" --strict "$DIR/probe.cpp" >/dev/null 2>&1; then
    echo "[selftest] FAIL — did NOT flag an UNMARKED capital assert"; FAIL=1
else
    echo "[selftest] ok — RED on unmarked"
fi

# 2) MARKED capital assert -> must PASS (exit 0)
printf '// ADV-REFUTE: 2026-06-11 (selftest)\nvoid t(){ check("x", Money_Eq(r->oms.total_fees, MQ(2.412))); }\n' > "$DIR/probe.cpp"
if python3 "$TOOL" --strict "$DIR/probe.cpp" >/dev/null 2>&1; then
    echo "[selftest] ok — GREEN on marked"
else
    echo "[selftest] FAIL — flagged a MARKED capital assert"; FAIL=1
fi

if [ "$FAIL" = "0" ]; then
    echo "[selftest] PASS — RED on unmarked, GREEN on marked."
    exit 0
fi
echo "[selftest] SELF-TEST FAILED"
exit 1
