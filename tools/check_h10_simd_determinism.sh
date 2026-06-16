#!/bin/bash
# check_h10_simd_determinism.sh — H10 determinism gate (.E.1.0 §4d).
#
# H10 (CLAUDE.md): AVX-512 SIMD kernels MUST produce BYTEWISE-IDENTICAL output to
# their scalar fallback. Compiles the REAL kernel (RidgeBlender_BuildCorr) two ways:
#     forced AVX-512  (-march=skylake-avx512)   vs   scalar (-march=native -mno-avx512f)
# runs both on fixed inputs, and memcmps the kernel output bytes. Extends the
# standing determinism net (sister to check_fp_determinism.sh's compile-2-ways shape;
# NOT a parallel gate — wired as check_determinism.sh gate 4).
#
# Exit 0 = CLEAN (byte-identical). 1 = DIVERGE (H10 violation). 2 = build/vacuity error.
#
# NON-VACUITY IS ASSERTED (the .E.1.0 anti-pattern this very gate must not become):
# the AVX build must actually define __AVX512F__ and the scalar build must NOT — else
# the compare is scalar-vs-scalar, a vacuously-green guard.
#
# Run:      tools/check_h10_simd_determinism.sh
# Selftest: tools/check_h10_simd_determinism.sh --selftest   (teeth: a 1e-12 perturbation is caught)
set -uo pipefail

ROOT="${FOXML_ENGINE:-$(cd "$(dirname "$0")/.." && pwd)}"
HARNESS="$ROOT/tools/h10_kernel_harness.cpp"
CXX="${CXX:-g++}"
FLAGS="-std=c++17 -O3"
# /tmp may be noexec (per the .E.1.0 I-surface finding) — build + run UNDER the repo.
TMP="$(mktemp -d "$ROOT/.h10tmp.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
AVX="$TMP/h10_avx"
SCA="$TMP/h10_scalar"

build() {  # $1=out-binary  $2=march-flags
    if ! $CXX $FLAGS $2 -I"$ROOT" "$HARNESS" -o "$1" 2>"$TMP/build.log"; then
        echo "[h10] FAIL: build ($2) failed:" >&2
        cat "$TMP/build.log" >&2
        return 2
    fi
}
build "$AVX" "-march=skylake-avx512"        || exit 2
build "$SCA" "-march=native -mno-avx512f"   || exit 2

AVX_OUT="$("$AVX")"
SCA_OUT="$("$SCA")"

# --- Non-vacuity asserts ---
echo "$AVX_OUT" | grep -q '^AVX512=1' || {
    echo "[h10] FAIL (vacuous): -march=skylake-avx512 did NOT define __AVX512F__ — the compare would be scalar-vs-scalar."; exit 2; }
echo "$SCA_OUT" | grep -q '^AVX512=0' || {
    echo "[h10] FAIL (vacuous): -mno-avx512f still had __AVX512F__ — not exercising the scalar #else."; exit 2; }

hex() { echo "$1" | grep '^HEX'; }
identical() { [[ "$(hex "$1")" == "$(hex "$2")" ]]; }

if [[ "${1:-}" == "--selftest" ]]; then
    # Teeth: a perturbed scalar run MUST diverge from the AVX run (proves the
    # memcmp actually catches a 1-ULP-ish difference — not a vacuously-green guard).
    SCA_PERTURB="$(H10_PERTURB=1 "$SCA")"
    if identical "$AVX_OUT" "$SCA_PERTURB"; then
        echo "[test-h10] FAIL — NO teeth: a 1e-12 perturbation was NOT caught."; exit 1
    fi
    # Real property: the unperturbed builds must agree byte-for-byte.
    if ! identical "$AVX_OUT" "$SCA_OUT"; then
        echo "[test-h10] FAIL — AVX vs scalar diverge on the real (unperturbed) kernel."; exit 1
    fi
    echo "[test-h10] PASS — teeth proven (1e-12 perturbation caught) + AVX==scalar on the real kernel."
    exit 0
fi

if identical "$AVX_OUT" "$SCA_OUT"; then
    echo "[h10] CLEAN — RidgeBlender_BuildCorr AVX-512 byte-identical to scalar fallback (H10)"
    exit 0
else
    echo "[h10] FAIL — AVX-512 vs scalar fallback DIVERGE (H10 violation):"
    diff <(hex "$AVX_OUT" | fold -w64) <(hex "$SCA_OUT" | fold -w64) | head
    exit 1
fi
