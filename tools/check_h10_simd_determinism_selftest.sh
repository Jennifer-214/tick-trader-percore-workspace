#!/bin/bash
# Teeth-proof selftest for check_h10_simd_determinism.sh (.E.1.0).
# Delegates to the gate's --selftest mode: proves a 1e-12 kernel perturbation IS
# caught (the gate has teeth) AND that AVX==scalar holds on the real unperturbed
# kernel. A determinism gate that can't be shown to catch a divergence is a
# vacuously-green guard — this closes that.
exec "$(dirname "$0")/check_h10_simd_determinism.sh" --selftest
