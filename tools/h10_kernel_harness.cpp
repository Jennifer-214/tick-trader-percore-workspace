// H10 byte-determinism harness (.E.1.0 §4d).
//
// Exercises RidgeBlender_BuildCorr — a real AVX-512 kernel (#if __AVX512F__) with a
// scalar #else fallback — on FIXED inputs and dumps the output matrix bytes.
// check_h10_simd_determinism.sh compiles this TWICE (forced-AVX vs -mno-avx512f
// scalar) and memcmps the dumps; H10 requires them byte-identical.
//
// This calls the REAL kernel both ways (golden-master discipline) — NOT a
// re-implemented scalar oracle (the A3 refute: a reimplemented oracle drifts and
// proves nothing). The only difference between the two builds is which arm of the
// kernel's own `#if defined(__AVX512F__)` compiles.
#include <cstdio>
#include <cstdint>
#include <cstdlib>
#include "ML_Headers/RidgeBlender.hpp"

int main() {
    constexpr int N = MAX_RIDGE_MODELS;   // 8 — exercise all AVX-512 lanes
    constexpr int K = 64;                 // prediction-history depth
    static float history[K * N];

    // Deterministic fill (NO rand() — identical bytes for both builds). A fixed LCG
    // over ~[-1, 1] so the correlation matrix is non-trivial (a real workout for the
    // sum/sum-of-squares accumulation that diverges first if the kernel is buggy).
    uint64_t s = 0x12345678ULL;
    for (int i = 0; i < K * N; ++i) {
        s = s * 6364136223846793005ULL + 1442695040888963407ULL;
        history[i] = (float)((int64_t)((s >> 40) % 2000) - 1000) * 0.001f;
    }

    double corr[N][N];
    RidgeBlender_BuildCorr<64>(corr, history, K, N);

    // Teeth-proof hook (selftest only): a 1e-12 perturbation the gate MUST catch.
    if (const char* p = getenv("H10_PERTURB"); p && p[0] == '1') corr[0][0] += 1e-12;

#if defined(__AVX512F__)
    printf("AVX512=1\n");
#else
    printf("AVX512=0\n");
#endif
    const uint8_t* b = reinterpret_cast<const uint8_t*>(corr);
    printf("HEX ");
    for (size_t i = 0; i < sizeof(corr); ++i) printf("%02x", b[i]);
    printf("\n");
    return 0;
}
