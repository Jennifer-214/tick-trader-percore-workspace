#!/usr/bin/env bash
# NEGATIVE self-test (teeth) for check_latency_path_conformance.py — per the D-137
# inventory guard (a load-bearing tool must prove its gate bites). Drives the tool's
# --selftest: a float-injection probe MUST trip the H4 detector. This is the teeth that
# CAUGHT the AVX/FMA float-detector hole during the .E.1.0 dogfood (mulsd|addsd missed
# the -march=native fused vfmadd form) — so it is load-bearing, not ceremony.
set -uo pipefail
ENGINE="${FOXML_ENGINE:-$(cd "$(dirname "$0")/.." && pwd)}"
out=$(python3 "$ENGINE/tools/check_latency_path_conformance.py" --selftest 2>&1)
if echo "$out" | grep -q "teeth (float math tripped"; then
    echo "PASS — check_latency_path_conformance teeth fire (float injection caught by H4 detector)"
    exit 0
fi
echo "FAIL — teeth did NOT fire; the H4 float detector is not biting:"
echo "$out" | tail -6
exit 1
