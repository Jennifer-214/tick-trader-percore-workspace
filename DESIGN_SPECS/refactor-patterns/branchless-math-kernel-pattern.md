---
type: refactor-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-11
tags: [branchless-discipline, latency-discipline, fixed-point-math]
surface: [hot-path, slow-path, ml-inference]
sister_specs: [branchless-dispatch-discipline.md, struct-padding-determinism-pattern.md, avx512-byte-determinism-pattern.md]
applies_at_skills: []
---

# Branchless math kernel pattern (constant-iter inner reductions + zero-invariant)

**Established:** 2026-05-11 (v5.14.11.B — Cholesky_Solve canonical first reference)
**Status:** ACTIVE
**Cross-references:**
- First reference application: `ML_Headers/RidgeBlender.hpp::Cholesky_Solve` (v5.14.11.B.1)
- Sister patterns: `avx512-byte-determinism-pattern.md` (when math kernel is vectorized); `sliding-window-online-statistics-pattern.md` (consumer of constant-iter form)
- CLAUDE.md item 18 (Slow-path latency reduction priority)
- CLAUDE.md item 26 (Math kernels on slow/hot path are constant-iter + branchless)
- CLAUDE.md item 19 (Structural fix preferred when bug class can recur)

---

## Problem statement

Math kernels on the slow path (correlation matrices, Cholesky decomposition, Welford updates, feature normalization, etc.) frequently have INNER reduction loops bounded by a runtime variable:

```cpp
for (int k = 0; k < j; ++k) {        // j varies per outer iteration; variable iteration count
    s -= L_out[i][k] * L_out[j][k];
}
```

OR contain explicit branches for edge cases:

```cpp
if (j > 0) {                          // guard against empty loop
    // SIMD setup...
    for (int k = 0; k < j; ++k) s -= prod_arr[k];
}
```

Both shapes introduce:

1. **Variable latency** — the cost per outer iteration depends on inner bound; profiling becomes harder; branch predictor may stall on transitions
2. **Non-uniform code shape** — `if`-guarded SIMD blocks have different fast-path-vs-slow-path branch costs depending on edge case frequency
3. **Inconsistent contracts with sibling kernels** — some kernels are branchless, others have edge-case guards; reviewers must context-switch per kernel
4. **Compiler optimization opacity** — variable-iter inner loops may or may not auto-vectorize depending on bound analysis

Per CLAUDE.md item 18 ("aim to MINIMIZE slow-path branches + cycles in every ship"), math kernels should be **constant-iteration + branchless** wherever the algorithm permits.

**Recurring case (v5.14.11.B trigger):** Cholesky_Solve added AVX-512 paths with `if (j > 0)` and `if (i > 0)` guards intending to skip vector setup for empty inner loops. The guards were unnecessary (masked loads with mask=0 produce all-zero lanes; subsequent scalar reduce loops correctly iterate 0 times). Caramel pushback 2026-05-11: *"is this on te slow path? shouldnt we have all calculations like this be branchelss? ... variable latency is bad"* surfaced the gap — no DESIGN_SPEC explicitly required branchless + constant-iter math kernels.

---

## Design space explored

### Option A: Keep variable-iter scalar reductions (status quo)

```cpp
for (int k = 0; k < j; ++k) s -= L_out[i][k] * L_out[j][k];
```

✓ Simplest code. ✓ Compiler can deduce bound at JIT time (sometimes). ✗ Variable latency. ✗ Inconsistent with branchless discipline.

### Option B: Branchless guards via `if (j > 0)` around SIMD path

```cpp
#if defined(__AVX512F__)
if (j > 0) { /* SIMD setup */ }
#endif
```

✗ Adds a branch. ✗ Variable latency. ✗ Inconsistent latency between j=0 and j>0 cases. **REJECTED.**

### Option C: Constant-iter loop with zero-invariant exploitation (CHOSEN)

```cpp
// Pre-zero L_out[i][0..MAX-1] at start of row i — establishes the invariant
for (int k = 0; k < MAX_RIDGE_MODELS; ++k) L_out[i][k] = 0.0;

// Off-diagonal: L[i][0..i-1]
for (int j = 0; j < i; ++j) {
    double s = sigma[i][j];
    // Constant 8 iterations; L_out[i][k]=0 for k >= j (pre-zero invariant + not yet written),
    // L_out[j][k]=0 for k > j (pre-zero invariant on row j; established when i was at j).
    // Zero-contribution iterations are bytewise no-ops (IEEE-754 x - 0.0 = x exact).
    for (int k = 0; k < MAX_RIDGE_MODELS; ++k) {
        s -= L_out[i][k] * L_out[j][k];
    }
    L_out[i][j] = s / L_out[j][j];
}
```

✓ Constant latency (8 inner iterations always). ✓ Branchless (no `if` guards). ✓ Compiler auto-vectorizes confidently (knows iteration count at compile time). ✓ Bytewise-equivalent to variable-iter (IEEE-754 invariants). ✓ Single code path; no scalar/AVX-512 fork to maintain.

### Option D: Explicit SIMD intrinsics + scalar reduce with `if (j > 0)` (what was attempted in v5.14.11.B before pushback)

Same as Option B but with explicit `_mm512_*` intrinsics. **REJECTED — has the same branch problem as Option B plus added complexity.**

---

## The pattern (concrete shape)

### Core invariants

A math kernel is **branchless + constant-iter** when:

1. **Inner reduction loops iterate a compile-time-constant count** (e.g., `MAX_RIDGE_MODELS`, not runtime `n`)
2. **No `if` guards inside reduction loops** (no conditional skip / fallback / edge-case handling)
3. **Zero-contribution iterations are bytewise no-ops** via IEEE-754 invariants:
   - `x * 0.0 = 0.0` exact (no rounding)
   - `x - 0.0 = x` exact (no rounding, except `x = -0.0 → +0.0`; rare in accumulator contexts)
   - `0.0 + x = x` exact
4. **Algorithmic state established BEFORE inner loops** guarantees zero-contribution for out-of-bounds iterations:
   - Pre-zero output arrays at the right granularity (per-row, per-solve, per-cycle)
   - Memset-zero initial state from struct init
   - Algorithm's natural zero-upper-triangle / zero-lower-triangle pattern preserved

### Standard kernel shape

```cpp
template <unsigned F>
inline RETURN_TYPE Math_Kernel(STATE* s, /* inputs */) {
    // 1. Pre-zero output arrays at the appropriate granularity
    //    (this establishes the zero-invariant for the constant-iter loops below)
    for (int k = 0; k < MAX_CONST; ++k) {
        s->output[k] = 0.0;
    }

    // 2. Algorithm body with constant-iter inner reductions
    for (int outer = 0; outer < n_outer; ++outer) {  // outer loop may be variable
        // ...
        for (int j = 0; j < MAX_CONST; ++j) {        // INNER LOOPS CONSTANT-ITER
            for (int k = 0; k < MAX_CONST; ++k) {    // (no `if` guards inside)
                acc += /* op using zero-invariant fields */;
            }
        }
        // ...
    }

    return result;
}
```

Outer loops can be variable-iter (algorithm-dependent: n, n_models, etc.) — branch predictor handles them well when per-call-stable. Inner reductions MUST be constant-iter.

### Verifying byte-equivalence with prior variable-iter form

For migrations from variable-iter to constant-iter:

1. **Identify the zero-contribution iterations** — typically iterations where one operand is guaranteed zero by algorithm invariant
2. **Prove IEEE-754 exactness** — `x - 0.0 = x`, `x * 0.0 = 0.0`, `0.0 + x = x` all exact (no rounding) in standard rounding mode
3. **Test on representative input** — old variable-iter code + new constant-iter code must produce bytewise-identical output

If byte-equivalence holds, the migration is safe even for PARITY-locked surfaces.

### Combining with SIMD vectorization

When the math kernel ALSO needs explicit SIMD (per `avx512-byte-determinism-pattern.md`), the branchless invariant applies INSIDE the vectorized block too:

```cpp
#if defined(__AVX512F__)
// NO `if` guards inside the vector block. Use uniform mask across all 8 lanes.
const __mmask8 mask = (__mmask8)((1u << MAX_CONST) - 1u);
__m512d li = _mm512_maskz_loadu_pd(mask, &state->arr[0]);
// ... rest of vectorized math, no inner branches
#else
// Scalar reference also constant-iter (see Option C above)
#endif
```

The vector path uses uniform mask (constant across lanes); the scalar fallback uses constant-iter loops. Both paths share the constant-iter invariant.

---

## Trade-offs + when to apply

### Apply when:

- Math kernel is on the slow path (BG/SG_Evaluate excluded; hot path has stricter rules)
- Inner reduction count has a known compile-time max (e.g., MAX_RIDGE_MODELS = 8)
- Algorithm establishes zero-invariants naturally (pre-zero output, zero upper/lower triangle, memset on init)
- Kernel may need future SIMD vectorization (constant-iter unlocks auto-vec)

### Skip when:

- Inner reduction count is genuinely unbounded (e.g., variable-length feature ring; cannot pre-zero)
- Zero-invariant cannot be established cheaply (would require expensive setup pass)
- Algorithm semantically requires the variable bound (rare; usually constant-iter is a refactor away)

### Cost:

- Per-call: extra (MAX - actual_n) iterations that contribute zero. For N=8 and actual=3: 5 extra iterations × ~1ns each = ~5ns overhead. Negligible on 100µs slow-path budget.
- Memory: pre-zero passes write to memory once per outer iteration; cache-warm after first touch.
- Code complexity: REDUCED (no `if` guards; uniform pattern across sibling kernels)

### Win:

- **Constant latency** — predictable cycle cost; profiling cleaner; no branch predictor stalls
- **Branchless inner blocks** — aligns with CLAUDE.md item 18 + branchless discipline
- **Compiler-friendly** — constant-bound loops auto-vectorize confidently (compiler emits AVX-512 fmadd when target supports)
- **Reusable invariant** — pre-zero pattern applies to many math kernels (Cholesky, Welford, BuildCorr, etc.)
- **Single code path** — no scalar/AVX-512 fork to maintain
- **Bytewise-equivalent migration** — old PARITY contracts preserved via IEEE-754 invariants

---

## Reference implementations

### v5.14.11.B.1 — Cholesky_Solve (canonical first reference)

`ML_Headers/RidgeBlender.hpp::Cholesky_Solve`. All inner reductions migrated from variable-iter (`for k = 0..j-1`) to constant-iter (`for k = 0..MAX_RIDGE_MODELS-1=7`).

Zero-invariants established:
- **Pre-zero L_out[i][0..MAX-1] at start of each row i** — guarantees L_out[i][k]=0 for k >= j during off-diagonal computation at column j
- **Pre-zero y_out[0..MAX-1] before forward solve** — guarantees y_out[k]=0 for k >= i during iter i (so k > i iterations contribute 0)
- **Pre-zero w_out[0..MAX-1] before back-solve** — guarantees w_out[k]=0 for k <= i during iter i (so k < i and k=i iterations contribute 0)

All inner reductions are now 8-iteration constant loops; zero-contribution iterations are bytewise no-ops via IEEE-754 invariants. Compiler auto-vectorizes via `-O3 -march=native`.

Verified byte-equivalent to v5.14.10's variable-iter scalar Cholesky (tests pass; FPN Ridge weights byte-identical given same input).

### v5.14.11.B.3 — RidgeBlender_UpdateOnline (AVX-512 + constant-iter)

`ML_Headers/RidgeBlender.hpp::RidgeBlender_UpdateOnline`. Uses uniform mask across 8 lanes; no `if` guards inside vectorized block. Outer loop iterates `n_models` (per-core-stable; branch predictor handles).

### v5.14.11.B.3 — RidgeBlender_BuildCorr (single-pass + constant-iter)

`ML_Headers/RidgeBlender.hpp::RidgeBlender_BuildCorr`. Single-pass sum-of-squares accumulation; inner loop over `MAX_RIDGE_MODELS` (constant). Outer loop iterates `n_history` (data-driven; predictor handles).

### Future applications (audit-found, anticipated)

- ConfidenceScore composite formula (4-factor weighted product) — likely already constant-iter
- ThompsonBandit Box-Muller transform — likely already constant-iter (2-step)
- Reward attribution arithmetic — verify in audit
- Other ML_Headers math kernels — audit pending in .B.0

---

## Lessons / gotchas

### Pre-zero must happen at the RIGHT granularity

For Cholesky: pre-zero at start of EACH row i (not once at start of function). The invariant is `L_out[i][k] = 0 for k > j when computing L_out[i][j]` — that requires fresh zeros each row.

For forward solve: pre-zero y_out ONCE before the loop (no per-iteration reset).
For back-solve: pre-zero w_out ONCE before the loop.

Wrong granularity → wrong invariant → wrong output. Test cases must cover multi-call scenarios (leftover state from previous calls).

### x - 0.0 = x exact in default IEEE-754 mode

Standard rounding mode (round-to-nearest-even, the default in C++ `<cfenv>`): `x - 0.0 = x` exactly. `x * 0.0 = 0.0` exactly (for any finite x).

Exception: `x = -0.0`. `-0.0 - 0.0 = +0.0` per IEEE-754 sign-of-zero rules. Accumulators in practice stay strictly positive or strictly negative; -0.0 doesn't arise. Verify in test if concerned.

Exception: `x = NaN` or `x = ±Inf`. `NaN - 0.0 = NaN`. `Inf - 0.0 = Inf`. If accumulators have NaN/Inf from upstream error, branchless reduction propagates them deterministically — same as variable-iter would.

For ML prediction accumulators (bounded inputs in [0, 1]; bounded history): no -0.0, no NaN, no Inf. Safe.

### Outer loop variability is acceptable

Constant-iter is required for **INNER reductions** only. Outer loops can be variable (algorithm-dependent: `n_models`, `n_history`, `n_outer_iter`). Branch predictor handles outer-loop variability cleanly when per-call-stable.

Don't force constant-iter at outer level if it would require pre-zeroing huge unused regions. Cost-benefit fails.

### Compiler auto-vectorization

For constant-iter inner loops with simple body (multiply + subtract; multiply + add), gcc `-O3 -march=native` typically emits AVX-512 fmadd (if target supports) without explicit intrinsics. This eliminates the scalar/AVX-512 fork.

For more complex inner bodies (divide, sqrt, conditional moves), compiler may not auto-vectorize — fall back to explicit intrinsics following `avx512-byte-determinism-pattern.md`.

Verify auto-vectorization status via assembly inspection or compiler reports (`-fopt-info-vec`).

### Memset-zero-then-write pattern is cache-friendly

Pre-zeroing an array writes to all cache lines. Subsequent reads + writes hit warm cache. Net memory bandwidth cost: 1 write + N reads/writes instead of (memory-load-on-first-read + writes). Often a net WIN due to write-allocate cache behavior.

### Bytewise determinism in vectorized vs scalar paths

If both scalar fallback and AVX-512 path are constant-iter + use the same arithmetic order (per `avx512-byte-determinism-pattern.md` Rules 1-4), bytewise equivalence is preserved across builds.

Verify via SHA-256 lock test in CI.

---

## Audit detection

`/dod-audit` should flag MATH KERNELS that violate the pattern:

- **Symptom 1:** inner reduction loop with variable upper bound (e.g., `for (int k = 0; k < j; ++k) acc += ...`) where `j` is itself a loop counter — flag as variable-iter math kernel
- **Symptom 2:** `if` statement inside a reduction loop body (no early-exit or short-circuit; just edge-case skip) — flag as branchy math kernel
- **Symptom 3:** `#if defined(__AVX512F__)` block with `if (...)` guards inside the vector setup — flag (same as Symptom 2 but in vector form)
- **Symptom 4:** Cholesky-like algorithm without pre-zero pattern at the appropriate granularity — flag as missing zero-invariant

When detected → recommend Option C migration (constant-iter + pre-zero invariant) per this pattern. Cross-reference to first-reference application in `RidgeBlender_Cholesky_Solve`.

---

## Patterns NOT used here (and why)

### `_mm512_reduce_*` for branchless reduction

Library-defined reduction order; not bytewise across binaries. Use scalar L-to-R reduce of the prod_arr per `avx512-byte-determinism-pattern.md` Rule 1. (Note: with constant-iter, scalar L-to-R reduce of 8 entries is `8 subtracts` — same cost as variable-iter j subtracts in practice.)

### Compile-time `if constexpr` per-iteration

Would unroll the loop with per-k conditional logic — same as constant-iter loop with `if`s inside. Same problem as Option B. **REJECTED.**

### Loop unrolling via `#pragma GCC unroll`

Compiler hint; doesn't guarantee constant-iter at semantic level. Use as performance hint AFTER establishing constant-iter via algorithmic refactor.

### Variable-iter with `__builtin_expect` for branch hint

Doesn't eliminate the branch; just hints predictor. Branchless preferred per CLAUDE.md item 18.

---

## Cross-references

- `avx512-byte-determinism-pattern.md` — when math kernel is vectorized
- `sliding-window-online-statistics-pattern.md` — math-kernel pattern consumer (online statistics)
- `structural-fix-preferred-decision-framework.md` — decision framework for variable-iter → constant-iter migrations (recurring class)
- FoxML_Trader_v2 `CLAUDE.md` item 18 — slow-path latency reduction priority (this pattern's primary motivation)
- FoxML_Trader_v2 `CLAUDE.md` item 26 — math kernels constant-iter + branchless (this pattern's codification)
- FoxML_Trader_v2 `ML_Headers/RidgeBlender.hpp::Cholesky_Solve` v5.14.11.B.1 (canonical first reference)
- FoxML_Trader_v2 `ML_Headers/RidgeBlender.hpp::RidgeBlender_UpdateOnline` v5.14.11.B.3 (vectorized application)
- FoxML_Trader_v2 `ML_Headers/RidgeBlender.hpp::RidgeBlender_BuildCorr` v5.14.11.B.3 (single-pass application)
- IEEE 754-2019 — guarantees `x - 0.0 = x`, `x * 0.0 = 0.0` exact in standard rounding
- Caramel framing 2026-05-11: *"variable latency is bad"* + *"shouldnt we have all calculations like this be branchelss?"*
