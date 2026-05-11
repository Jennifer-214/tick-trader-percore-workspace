# AVX-512 byte-determinism pattern (cross-binary replay-determinism for SIMD kernels)

**Established:** 2026-05-07 (v5.11.7 first application; v5.14.11.B promotes to first-class DESIGN_SPEC after 2nd application)
**Status:** ACTIVE
**Cross-references:**
- First reference application: `ML_Headers/BanditLearning.hpp:139-162` (`Bandit_GetProbabilities` softmax-like normalize + affine blend)
- Second reference application: `ML_Headers/RidgeBlender.hpp` v5.14.11.B (UpdateOnline + BuildCorr accumulation + Cholesky_Solve inner reductions)
- Sister pattern: `sliding-window-online-statistics-pattern.md` (consumer of this discipline)
- Sister pattern: `wire-format-byte-preservation-discipline.md` (HMAC-chain byte preservation; different domain but same byte-equivalence philosophy)
- FoxML_Trader_v2 CLAUDE.md item 16 (reuse-audit — SIMD kernels reuse this pattern)
- FoxML_Trader_v2 CLAUDE.md item 17 (latency tracking — AVX-512 wins documented per kernel)

---

## Problem statement

When a kernel is vectorized with AVX-512, the SIMD path must produce **bytewise-identical** output to the scalar path. This is stronger than tolerance-equivalence (e.g., within 1e-9) — it's bit-for-bit equality.

**Why bytewise matters:**
1. **Replay determinism across binaries.** A scalar-built binary and an AVX-512-built binary processing the same input + cfg must produce identical model outputs, calibration logs, stamp bytes, and HMAC chains. Cross-binary divergence at 1e-15 magnifies through nonlinear ML pipelines into 1e-3 prediction differences over thousands of inferences.
2. **Cache-warm replay tests.** v5.9.2-style determinism tests compare byte-identical outputs from a recorded test scenario. Tolerance-only comparison hides regression-class bugs (e.g., a missing FMA fusion that shifts ULPs predictably).
3. **HMAC chains.** Stamp body, calibration logs, and snapshot byte-streams use HMAC integrity — any byte difference breaks the chain.
4. **Reproducibility of paper-trade audits.** Operators replaying a paper-trade session under any binary variant must get bit-identical fills + signals.

**Why naïve AVX-512 vectorization breaks bytewise:**

Common pitfalls:

1. **`_mm512_reduce_add_pd`** — sums vector lanes in implementation-defined order. Different binaries/CPUs may reduce L-to-R, pairwise, or tree-style. Sums differ at ULP level. **BANNED.**
2. **Mul-by-reciprocal vs division** — `_mm512_mul_pd(x, _mm512_set1_pd(1.0 / y))` is faster but produces 1-ULP difference from `_mm512_div_pd(x, _mm512_set1_pd(y))`. Scalar code uses `/`; vector must too.
3. **FMA fusion mismatch** — gcc -O3 -ffp-contract=fast fuses scalar `a*b + c` into FMA. If the AVX-512 path uses separate `_mm512_mul_pd` + `_mm512_add_pd`, results differ by ~1 ULP per fused operation.
4. **Subnormal flushing differences** — DAZ/FTZ MXCSR flags differ between threads/code paths. SIMD operations may flush subnormals when scalar doesn't.

This doc captures the rules + WHY each + cross-binary test pattern.

---

## Design space explored

### Why bytewise, not tolerance

Tolerance-equivalence (e.g., within 1e-9) seems sufficient — for a single computation. But ML pipelines compose: 
- Tick → feature extraction → standardization → inference → ensemble → bandit → trade signal

A 1-ULP difference at feature extraction can become a 1e-3 prediction difference after 10 layers of nonlinear math, leading to different trade decisions. Bytewise lock at each layer prevents accumulation.

For SIMD kernels SPECIFICALLY: tolerance is easy to verify on a single call but doesn't help with cross-binary determinism over long replay scenarios. Bytewise lock catches every divergence at its source.

### Compile-time gating vs runtime detection

**Compile-time `#if defined(__AVX512F__)`** (CHOSEN):
- Build matrix decides binary's SIMD level
- Same binary always uses same path → trivial bytewise within binary
- Cross-binary determinism becomes a build-time concern (CI verifies)
- Simple; no runtime dispatch overhead

**Runtime `__builtin_cpu_supports("avx512f")`**:
- One binary works across CPU generations
- Bytewise determinism is then CPU-dependent, not binary-dependent
- Requires runtime dispatch table (small overhead)
- More complex; rejected for our use case

Cross-binary determinism is the load-bearing concern (replay tests, paper-trade audits). Compile-time gating is the simpler answer.

### How strict is "bytewise"?

For DOUBLE-precision: bit-for-bit equality of the IEEE-754 representation.

NaN handling: NaN ≠ NaN under IEEE-754 == comparison, so the byte-determinism test compares via `memcmp` or via NaN-aware equality.

Signed zero: -0.0 and +0.0 are distinct bit patterns; tests must distinguish.

Subnormals: must preserve. DAZ/FTZ flushing breaks byte-equivalence.

---

## The pattern (rules)

### Rule 1 — NEVER `_mm512_reduce_add_pd` (or `_reduce_*` variants)

`_mm512_reduce_add_pd` reduces vector lanes via library-defined order. Different glibc/Intel ICC versions may differ. Bytewise breaks across libraries.

**Replace with:** scalar reduction in explicit L-to-R order:
```cpp
double result[8];
_mm512_storeu_pd(result, vec);
double sum = 0.0;
for (int i = 0; i < 8; ++i) sum += result[i];  // L-to-R; bytewise-fixed
```

For masked stores: same pattern with masked store + loop bound by mask popcount.

### Rule 2 — `_mm512_div_pd`, NEVER mul-by-reciprocal

Scalar `a / b` is bytewise-distinct from `a * (1.0 / b)` due to 1-ULP rounding of the reciprocal.

**Use** `_mm512_div_pd(x_vec, y_vec)` when scalar uses `x / y`. Don't optimize to multiply-by-reciprocal unless you verify scalar code ALSO uses reciprocal (rare).

### Rule 3 — `_mm512_fmadd_pd` to match gcc FMA fusion

gcc -O3 -ffp-contract=fast fuses scalar `a * b + c` into a single FMA instruction. The vector path must also use FMA to stay bytewise-equivalent:

```cpp
// Scalar (gcc -O3 -ffp-contract=fast):  scalar = vfmadd231sd
double scalar = a * b + c;

// AVX-512 path (must match): vfmadd231pd
__m512d vec = _mm512_fmadd_pd(a_vec, b_vec, c_vec);
```

If the build ever switches to `-ffp-contract=off`, the scalar `a * b + c` decomposes into `vmulsd` + `vaddsd`. The AVX-512 path must mirror via `_mm512_mul_pd` + `_mm512_add_pd`. Audit build flags + adjust.

### Rule 4 — Scalar reductions stay scalar (when fed by vector compute)

The pattern: **vectorize the parallel work; reduce serially in scalar.** Mixing vector reductions with scalar-baseline code is the most common source of byte-divergence.

```cpp
// Vector multiply (parallel; bytewise-determined per lane)
__m512d products = _mm512_mul_pd(a_vec, b_vec);

// Scalar reduce (serial; preserves L-to-R order)
double prod_arr[8];
_mm512_mask_storeu_pd(prod_arr, mask, products);
double sum = 0.0;
for (int i = 0; i < lane_count; ++i) sum += prod_arr[i];
```

### Rule 5 — Compile-time gate via `#if defined(__AVX512F__)`

```cpp
#if defined(__AVX512F__)
    // AVX-512 path
#else
    // Scalar fallback (this is the byte-determinism reference)
#endif
```

The scalar path is the BYTE-DETERMINISM REFERENCE. AVX-512 must match scalar bit-for-bit. Tests assert this.

### Rule 6 — SHA-256 snapshot lock test (cross-binary determinism)

For each vectorized kernel, write a test that:
1. Runs the kernel on a fixed input vector
2. Captures output as bytes (`memcpy` from result array)
3. Computes SHA-256 of bytes
4. Asserts the SHA-256 matches a recorded baseline

Run the test in BOTH scalar build (`-mno-avx512f`) AND AVX-512 build (`-mavx512f`). Both must produce identical SHA-256.

Reference test pattern: `tests/controller_test.cpp:22479-22533` (v5.14.10 Thompson sampler SHA-256 lock test).

### Rule 7 — Subnormal preservation

Ensure `MXCSR` DAZ/FTZ flags are NOT set in code paths called by the kernel. Typically default-off; verify on platform.

If a calling thread/context has DAZ/FTZ enabled (rare; e.g., audio code), the kernel produces divergent results for subnormal inputs. Either: assert-no-subnormals in test setup, OR explicitly clear MXCSR at kernel entry.

For typical ML kernels with [0, 1] inputs: subnormals don't arise; rule 7 is informational.

---

## Worked example: refactoring scalar to AVX-512 with byte-determinism

**Before (scalar baseline):**
```cpp
for (int i = 0; i < N; ++i) {
    double s = sigma[i][j];
    for (int k = 0; k < j; ++k) {
        s -= L[i][k] * L[j][k];  // gcc fuses into vfnmsub
    }
    L[i][j] = s / L[j][j];
}
```

**After (AVX-512, byte-determinism preserved):**
```cpp
for (int i = 0; i < N; ++i) {
    double s = sigma[i][j];
#if defined(__AVX512F__)
    // Rule 4: vector compute + scalar reduce
    __mmask8 mask = (__mmask8)((1u << j) - 1u);
    __m512d li = _mm512_maskz_loadu_pd(mask, &L[i][0]);
    __m512d lj = _mm512_maskz_loadu_pd(mask, &L[j][0]);
    __m512d prod = _mm512_mul_pd(li, lj);
    double prod_arr[8];
    _mm512_mask_storeu_pd(prod_arr, mask, prod);
    // Rule 4: scalar reduce L-to-R
    for (int k = 0; k < j; ++k) s -= prod_arr[k];
#else
    // Scalar baseline (reference)
    for (int k = 0; k < j; ++k) s -= L[i][k] * L[j][k];
#endif
    L[i][j] = s / L[j][j];  // Rule 2: division, not mul-by-reciprocal
}
```

SHA-256 lock test verifies bytewise equivalence:
```cpp
TEST("Cholesky_Solve AVX-512 byte-determinism") {
    double sigma[8][8] = { /* fixed test input */ };
    double mu[8]       = { /* fixed test input */ };
    double L[8][8], y[8], w[8];
    Cholesky_Solve(L, y, w, sigma, mu, 0.15, 8);

    uint8_t bytes[sizeof(L) + sizeof(y) + sizeof(w)];
    memcpy(bytes, L, sizeof(L));
    memcpy(bytes + sizeof(L), y, sizeof(y));
    memcpy(bytes + sizeof(L) + sizeof(y), w, sizeof(w));

    sha256_digest_t digest = sha256(bytes, sizeof(bytes));
    // Baseline captured on scalar build; AVX-512 build must match
    check_sha256_eq("expected: a1b2c3...", digest);
}
```

Run via both build variants:
- `./build.sh test` (scalar baseline)
- `./build.sh test -DUSE_AVX512=ON` (vector path)

Both must produce identical SHA-256.

---

## Trade-offs + when to apply

### Apply when:
- Kernel is in the slow path (latency justification for vectorization)
- Output is consumed by downstream byte-determinism-sensitive code (ML inference, stamp body, HMAC chain, calibration log)
- Reasonably-sized vector width fit (N=4..16 for AVX-512; larger may benefit too)
- Build matrix supports compile-time AVX-512 gating (already standard)

### Skip when:
- Kernel runs once at boot (vectorization unjustified for one-shot)
- Output is consumed only by debugging/logging code (byte-determinism doesn't matter; tolerance is fine)
- Vector width doesn't fit (N=2 or N=3; vectorization overhead exceeds gain)
- Hot path with sub-100ns budget (function call + intrinsic dispatch overhead exceeds gain)

### Cost:
- AVX-512 path adds ~30-100 LOC per kernel (intrinsics + scalar fallback)
- SHA-256 lock test: ~20-40 LOC per kernel
- Build matrix verification: 1 CI job per binary variant
- Knowledge cost: contributors must understand byte-determinism rules

### Win:
- Cross-binary replay-determinism preserved
- Cache-warm replay tests catch regressions at the byte level
- Long-replay paper-trade audits reproducible across binary variants
- Latency win without correctness cost

---

## Reference implementations

### v5.11.7.A — `Bandit_GetProbabilities` (FIRST application)

Located at `ML_Headers/BanditLearning.hpp:139-162` (verified at HEAD = e0cc877).

Pattern applications:
- Rule 1 (no `_reduce_add`): scalar L-to-R reduction at line ~160
- Rule 2 (`_mm512_div_pd`): line 152 explicit comment "_mm512_div_pd(x, y) NOT _mm512_mul_pd(x, 1/y)"
- Rule 3 (`_mm512_fmadd_pd`): line 155 explicit comment "_mm512_fmadd_pd(a, b, c) for a*b + c — gcc -O3 with default -ffp-contract=fast fuses scalar (1-gamma)*normd + g/K into FMA"
- Rule 5 (compile-time gate): line 139 `#if defined(__AVX512F__)`

Output: softmax-like probability vector + affine blend with gamma + floor. v5.11.7 SHA-256 test (in controller_test.cpp).

### v5.14.11.B — RidgeBlender online + Cholesky (SECOND application)

Three vectorized sites within `ML_Headers/RidgeBlender.hpp`:
1. `RidgeBlender_UpdateOnline` outer-product update (sliding-window state)
2. `RidgeBlender_BuildCorr` single-pass sum-of-squares accumulation (refactored)
3. `Cholesky_Solve` inner reductions (decomposition + forward solve + back solve)

Each site applies all 7 rules + has a SHA-256 lock test.

---

## Lessons / gotchas

### gcc -O3 -ffp-contract=fast is the default; verify if build flags change

If your build adds `-ffp-contract=off` (e.g., for debugging FMA precision), scalar `a * b + c` decomposes into separate operations. AVX-512 path's `_mm512_fmadd_pd` then DIVERGES from scalar (FMA produces 1-ULP-better result than separate mul+add).

Solution: audit build flags. If `-ffp-contract=off`, replace `_mm512_fmadd_pd` with `_mm512_mul_pd` + `_mm512_add_pd`.

### Masked operations preserve byte-determinism

`_mm512_maskz_loadu_pd(mask, ptr)` loads lanes per mask; zeros unmasked lanes. Bytewise deterministic.

`_mm512_mask_storeu_pd(ptr, mask, vec)` stores lanes per mask; leaves other memory untouched. Test setup must INITIALIZE the target memory before masked store (otherwise unmasked lanes contain garbage).

### Don't optimize prematurely

Vectorize ONLY the inner loops where N ≥ 4 (vector width). For tiny inner loops (N ≤ 3), scalar is faster (intrinsic dispatch overhead exceeds gain).

For loops with variable bound (e.g., N runtime-determined): vectorize with mask; scalar fallback when N < 2.

### Don't fuse what scalar doesn't fuse

If scalar code does `temp = a * b; result = temp + c;` (explicit two-step), the AVX-512 path must NOT fuse via `_mm512_fmadd_pd`. Use `_mm512_mul_pd` + `_mm512_add_pd`.

This is rare in performance-sensitive code (compilers usually fuse), but watch for it in numerical-stability-conscious code that deliberately separates ops.

### Beware `_mm512_loadu_pd` from misaligned pointers

Unaligned load is legal but slower. For aligned data, use `_mm512_load_pd`. Doesn't affect byte-determinism; affects only performance.

For state structs (e.g., RidgeWeights<F>), align state via `alignas(64)` if it lives in cache-locality-critical position.

### Cross-binary test infrastructure

CI must build BOTH scalar and AVX-512 binaries + run SHA-256 lock tests on both. A missing CI job means byte-determinism regresses silently.

For local dev: `./build.sh test` (scalar) + `./build.sh test -DUSE_AVX512=ON` (vector). Run both manually after touching vectorized kernels.

---

## Audit detection

`/dod-audit` should flag candidates by:

- **Symptom 1:** SIMD intrinsic call (`_mm*_*`) without nearby scalar fallback `#else` branch → missing compile-time gate (Rule 5)
- **Symptom 2:** `_mm512_reduce_*` call → BANNED reduction operation (Rule 1)
- **Symptom 3:** `_mm512_mul_pd` with reciprocal `_mm512_set1_pd(1.0 / ...)` → BANNED mul-by-reciprocal (Rule 2)
- **Symptom 4:** vectorized kernel without an adjacent SHA-256 lock test → missing byte-determinism contract (Rule 6)
- **Symptom 5:** AVX-512 path that doesn't mirror scalar's FMA usage → fusion mismatch (Rule 3)

When detected → flag as `MISSED — avx512-byte-determinism-pattern`. Recommended fix: refactor per the 7 rules + add SHA-256 lock test.

---

## Patterns NOT used here (and why)

### `_mm512_reduce_add_pd` for "fast" reductions

Library-defined order → cross-binary divergence at 1-ULP level → byte-determinism breaks. Trading sub-ns per reduction for byte-determinism is wrong direction.

### Runtime CPU dispatch

`__builtin_cpu_supports("avx512f")` allows one binary to work across CPU generations. Adds runtime dispatch overhead + complicates byte-determinism guarantee (bytes now CPU-dependent, not binary-dependent). Compile-time gating is simpler and sufficient.

### Approximation intrinsics (`_mm512_rcp14_pd`, `_mm512_rsqrt14_pd`)

Faster but only ~14-bit precision; doesn't match scalar `1.0 / x` or `1.0 / sqrt(x)`. Bytewise breaks. Use only when scalar code ALSO uses approximations (rare).

### `_mm512_*_pd` with rounding mode override

Intrinsics with explicit rounding mode (`_mm512_div_round_pd(x, y, _MM_FROUND_TO_NEAREST_INT | _MM_FROUND_NO_EXC)`) differ from default rounding. Doesn't match scalar code. Use defaults.

---

## Cross-references

- `sliding-window-online-statistics-pattern.md` — consumer of this discipline (vectorizes outer-product updates)
- `wire-format-byte-preservation-discipline.md` — sister byte-equivalence philosophy (HMAC chain preservation)
- FoxML_Trader_v2 `CLAUDE.md` item 16 — reuse-audit (SIMD kernels reuse this pattern)
- FoxML_Trader_v2 `CLAUDE.md` item 17 — latency tracking (AVX-512 wins documented per kernel)
- FoxML_Trader_v2 `ML_Headers/BanditLearning.hpp:139-162` — v5.11.7 first application
- FoxML_Trader_v2 `ML_Headers/RidgeBlender.hpp` — v5.14.11.B second application (3 sites)
- FoxML_Trader_v2 `tests/controller_test.cpp:22479-22533` — v5.14.10 Thompson sampler SHA-256 lock test (reference test pattern)
- IEEE 754-2019 — floating-point standard governing bytewise semantics
- Intel Intrinsics Guide — https://www.intel.com/content/www/us/en/docs/intrinsics-guide/ — operation-level documentation
