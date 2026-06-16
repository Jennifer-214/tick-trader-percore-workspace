#!/usr/bin/env bash
# NEGATIVE self-test (teeth) for check_latency_path_conformance.py — per the D-137
# inventory guard (a load-bearing tool must prove its gates bite). Drives the tool's
# --selftest, whose per-detector teeth table injects a probe per check (float / div /
# forbidden-call / indirect / branch / non-vacuity) and asserts EACH fires. These teeth
# CAUGHT 3 real holes during the .E.1.0 dogfood: the SSE-only float regex missing the
# -march=native vfmadd, the indirect detector missing jmp* tail-calls, and the
# forbidden-call detector being BLIND to external syms in an unlinked .o — load-bearing,
# not ceremony.
set -uo pipefail
ENGINE="${FOXML_ENGINE:-$(cd "$(dirname "$0")/.." && pwd)}"
out=$(python3 "$ENGINE/tools/check_latency_path_conformance.py" --selftest 2>&1)
if echo "$out" | grep -q "ALL teeth fire"; then
    echo "PASS — check_latency_path_conformance: all per-detector teeth fire"
    exit 0
fi
echo "FAIL — a detector did NOT fire (under-enumeration risk):"
echo "$out" | tail -10
exit 1
