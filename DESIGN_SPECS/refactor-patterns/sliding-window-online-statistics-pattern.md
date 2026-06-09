---
type: refactor-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-11
tags: [fixed-point-math, latency-discipline]
surface: [slow-path, ml-inference]
sister_specs: [branchless-math-kernel-pattern.md, generic-ring-buffer-template-pattern.md]
applies_at_skills: []
---

# Sliding-window online statistics pattern (sum-of-squares form)

**Established:** 2026-05-11 (v5.14.11.A — RidgeBlender correlation matrix; first application)
**Status:** ACTIVE
**Cross-references:**
- First application: `ML_Headers/RidgeBlender.hpp` v5.14.11.A (correlation matrix over predictions ring)
- Sister pattern: `avx512-byte-determinism-pattern.md` (SIMD vectorization shape used here)
- Decision framework: `structural-fix-preferred-decision-framework.md` (why this beats vanilla-Welford+periodic-reset)
- CLAUDE.md item 16 (reuse-audit — future online-stats additions reuse this pattern)
- CLAUDE.md item 17 (latency tracking — adoption costs documented)
- CLAUDE.md item 19 (structural fix preferred when bug class can recur)

---

## Problem statement

A system needs ONGOING running statistics (mean, variance, covariance, correlation) over a FIXED-SIZE window of the most recent K records. Three approaches exist; only one is structurally clean.

**Approach 1 — full recompute every cycle.**
Walk the K-record buffer; recompute statistics from scratch. O(K × N²) per cycle.
✓ Numerically stable. ✓ Simple. ✗ Expensive when K × N² grows. ✗ Wastes work since the buffer barely changes per cycle.

**Approach 2 — vanilla Welford with periodic reset.**
Maintain incremental running sums via canonical Welford M2 form. Drift accumulates with `n` → refresh-from-scratch every M cycles to bound drift.
✓ Cheap per-cycle (O(N²)). ✗ The periodic reset is a CODE SMELL — admission that the incremental algorithm drifts, with a band-aid mitigation.
✗ The reset itself is bug-prone (PARITY-018 was a v5.14.11 plan-draft bug: rebuilds output matrix but doesn't rebuild Welford accumulators).
✗ Drift behavior depends on n grow-rate; numerical analysis is non-local.

**Approach 3 — sliding-window incremental (THIS PATTERN).**
Maintain incremental sums over EXACTLY the K most recent records. When a new record arrives at full window, REPLACE the oldest record's contribution.
✓ Accumulator magnitudes bounded by window contents → bounded drift → NO periodic reset.
✓ Single math kernel; no special-case reset path.
✓ Numerical stability local to per-record arithmetic + window size.

This doc captures Approach 3 using the **sum-of-squares form** (simpler than canonical Welford M2 for fixed window; numerically stable for bounded inputs over bounded K).

---

## Design space explored

### Why sum-of-squares form, not Welford M2?

Welford M2 form (`mean + M2 + outer_xy`) is preferred for UNBOUNDED sample counts because the canonical recurrence avoids catastrophic cancellation as n grows. For a BOUNDED window (K fixed; accumulator magnitudes bounded), the simpler sum-of-squares form (`sum_x + sum_xx`) has equivalent numerical stability with a cleaner "drop oldest" arithmetic:

| Form | Add record | Drop record |
|---|---|---|
| Welford M2 | mean += (x - mean) / n; M2 += (x - mean_old)(x - mean_new) | Complex West-1979 replacement formula |
| Sum-of-squares | sum_x += x; sum_xx += x ⊗ x | sum_x -= x; sum_xx -= x ⊗ x |

The sum-of-squares drop is trivial subtraction. Welford's drop requires careful arithmetic to invert the M2 update.

**Trade-off:** sum-of-squares variance formula `var = sum_xx/K - mean²` has cancellation when `mean²` ≈ `sum_xx/K`. For bounded predictions in [0, 1] over K=64 records, max relative error ≈ ε × max(sum_xx) ≈ 10^-14 (5 orders of magnitude headroom below typical PARITY tolerance of 1e-9).

For UNBOUNDED accumulators (e.g., running stats over full session lifetime), prefer Welford M2 with periodic compensation or Kahan summation. The sliding-window pattern is for BOUNDED window cases.

### Why bounded inputs × bounded K guarantee stability

Cancellation error in `var = sum_xx/K - mean²` is bounded by:
```
|err(var)| ≤ ε × max(|sum_xx/K|, |mean²|)
```
where ε ≈ 2.2 × 10^-16 (double-precision machine epsilon).

For predictions x ∈ [-X, X] over K samples:
- max(|sum_xx|) ≤ K × X²
- max(|sum_xx/K|) = X²
- max(|mean²|) ≤ X²

So `|err(var)| ≤ ε × X²`. For ML predictions typically in [0, 1] or [-1, 1]:
- |err(var)| ≤ 2.2 × 10^-16

That's well below any practical correlation tolerance.

### Why no periodic reset is needed

Sliding-window accumulators reflect ONLY the current window contents:
- sum_x[i] is the exact sum of the K most recent x_i values
- sum_xx[i][j] is the exact sum of the K most recent x_i × x_j products

Numerical errors come from per-update floating-point rounding, NOT from accumulated history (since each record's contribution is added once and subtracted once across its K-record lifetime).

If a hypothetical input pattern caused error to grow per-update (e.g., catastrophic cancellation in drop), bounded by K=64 updates the error stays bounded. No periodic reset needed.

### Why replace via subtract-then-add, not via direct replace

```cpp
// Method A: subtract-then-add (chosen)
sum_x[i] += predictions_new[i] - predictions_oldest[i];

// Method B: rebuild from scratch each cycle (Approach 1; rejected)

// Method C: full Welford with West-1979 replacement (Approach 2; rejected)
```

Method A is one fmadd per element (subtract-mul-add fused). Numerically equivalent to "drop oldest, add new" via two separate operations. Compilers (gcc -O3 -ffp-contract=fast) DO fuse `(a - b)` into operations downstream, preserving FMA byte-equivalence.

---

## The pattern (concrete shape)

### State

```cpp
struct OnlineStatsState {
    double  sum_x[N];           // running sum Σ x_i over window
    double  sum_xx[N][N];       // running cross-products Σ x_i × x_j over window
    uint64_t window_count;      // ≤ K; saturates at K
};
```

For N=8: ~584 bytes (sum_x = 64B + sum_xx = 512B + count = 8B). Fits one half of an L1d cache. Per-node only (no cross-thread access).

### Update (when window not yet full: count < K)

```cpp
void Update_NotFull(OnlineStatsState* s, const double* x_new, int N) {
    for (int i = 0; i < N; ++i) {
        s->sum_x[i] += x_new[i];
        for (int j = 0; j < N; ++j) {
            s->sum_xx[i][j] += x_new[i] * x_new[j];
        }
    }
    s->window_count++;
}
```

### Update (when window full: count == K, replace oldest)

```cpp
void Update_Full(OnlineStatsState* s, const double* x_new, const double* x_oldest, int N) {
    for (int i = 0; i < N; ++i) {
        s->sum_x[i] += x_new[i] - x_oldest[i];
        for (int j = 0; j < N; ++j) {
            s->sum_xx[i][j] += x_new[i] * x_new[j] - x_oldest[i] * x_oldest[j];
        }
    }
    // window_count stays at K
}
```

### Finalize

```cpp
void Finalize(double mean[N], double var[N], double cov[N][N], double corr[N][N],
              const OnlineStatsState* s, int N) {
    double K = (double)s->window_count;
    for (int i = 0; i < N; ++i) {
        mean[i] = s->sum_x[i] / K;
        var[i]  = s->sum_xx[i][i] / K - mean[i] * mean[i];
    }
    for (int i = 0; i < N; ++i) {
        for (int j = 0; j < N; ++j) {
            cov[i][j] = s->sum_xx[i][j] / K - mean[i] * mean[j];
            corr[i][j] = cov[i][j] / std::sqrt(var[i] * var[j]);
        }
    }
}
```

### AVX-512 vectorization (per `avx512-byte-determinism-pattern.md`)

Inner-product update is one row per AVX-512 instruction at N=8:

```cpp
#if defined(__AVX512F__)
for (int i = 0; i < n_models; ++i) {
    __m512d xi = _mm512_set1_pd(x_new[i]);
    __m512d xnew = _mm512_loadu_pd(x_new);
    __m512d xold = _mm512_loadu_pd(x_oldest);
    __m512d xi_old = _mm512_set1_pd(x_oldest[i]);
    __m512d sum_xx_i = _mm512_loadu_pd(&s->sum_xx[i][0]);
    // sum_xx[i] += xi × xnew - xi_old × xold (4 vector ops; FMA-friendly)
    __m512d delta = _mm512_sub_pd(_mm512_mul_pd(xi, xnew), _mm512_mul_pd(xi_old, xold));
    sum_xx_i = _mm512_add_pd(sum_xx_i, delta);
    _mm512_storeu_pd(&s->sum_xx[i][0], sum_xx_i);
}
#endif
```

N=8 rows × ~5 AVX-512 instructions per row = ~40 instructions for the full O(N²) update. Underlying work is N² doubles touched; instruction count is O(N).

For finalize: same shape applied to mean computation + variance computation + correlation computation. Scalar reductions stay scalar (per byte-determinism discipline).

---

## Trade-offs + when to apply

### Apply when:
- Running statistics needed over a FIXED-SIZE window (not unbounded session lifetime)
- Inputs are bounded magnitude (ML predictions in [0, 1] or [-1, 1] typical)
- Window size K is bounded (≤ 256 or so; larger windows OK but cache behavior degrades)
- Oldest record is available for retrieval (e.g., in a ring buffer)
- Statistics consumed every record OR periodically (not just once per session)

### Skip when:
- Unbounded session-lifetime statistics → use canonical Welford with care (compensated summation if needed)
- Unbounded inputs (e.g., raw price values without normalization) → cancellation error grows with input magnitude
- Statistics needed only ONCE (full-recompute is simpler; pattern overhead unjustified)
- Sparse-update access (statistics rarely consumed) → full-recompute on demand is cheaper

### Cost:
- Per-record update: O(N²) outer-product
- Drop-oldest: O(N²) subtract (same shape as add)
- Per-cycle total: ~2× O(N²) = still O(N²)
- Storage: N² doubles for sum_xx + N doubles for sum_x + 8 bytes for count
- For N=8: 584 bytes per state instance

### Win:
- Eliminates periodic-reset code smell
- Bounded drift by design (no accumulated error)
- Simpler than canonical Welford for fixed window (3 fewer arithmetic operations per update)
- Reusable for online IC tracking, online turnover, online feature normalization, online correlation matrices
- Math kernel can be SHARED between full-recompute and incremental paths (single FinalizeCorrFromSums shared by both — anti-mirror discipline)

---

## Reference implementations

### v5.14.11.A — RidgeBlender online correlation matrix

First application. Tracks N=8 model predictions over a K=64 record sliding window. Used to compute the N×N correlation matrix for Ridge regression weighting.

State embedded in `RidgeWeights<F>` struct (boundary-stable; buy + exit ezoo fields both inherit). Math kernel `RidgeBlender_FinalizeCorrFromSums` shared by refactored `RidgeBlender_BuildCorr` (full-recompute path; cfg=0 default) AND `RidgeBlender_OnlineCycleStep` (incremental path; cfg=1 operator opt-in).

Numerical stability: predictions bounded to [0, 1] (sigmoid output) + K=64 → max(sum_xx) ≤ 64 → cancellation error ≈ 10^-14. PARITY tolerance is 1e-9; 5 orders of magnitude headroom.

### v5.15.5.D — BookImbalanceHistory dual-window mean

Second canonical application. Single-variable case (N=1) over a ring buffer with TWO simultaneous windows: long-window W=1024 (~17 min cadence) and short-window K=64 (~1 min cadence). Both window sums are maintained incrementally over the SAME `samples[]` ring buffer; the only difference is the eviction offset (long evicts at `samples[head]`, short evicts at `samples[head - K]`).

State embedded in `BookImbalanceHistory<F, W>` struct (`ML_Headers/FlowFeatures.hpp`). Pre-v5.15.5.D, `BookImbHistory_MeanShort(k=64)` did an O(K=64) sequential walk every slow-path cycle (~24 cache lines / read). Post-v5.15.5.D, a parallel `short_sum` field is maintained at Push time + `BookImbHistory_MeanShortFast(s)` reads it directly in O(1). ~10-20 cache lines saved / slow-path cycle / core.

Numerical stability: book imbalance bounded to [-1, 1] + K=64 → max(|short_sum|) ≤ 64 → far below FPN_Binary<64>'s ±2^63 range → no saturation → FPN_Add is bytewise associative for these magnitudes. Bytewise parity vs the walked path verified in `tests/controller_test.cpp` via a 200-push deterministic sequence covering warm-up (count < K) and steady-state (count > K) phases.

### v5.15.5.E.D — RollingRMSE running-sum

Third canonical application. Single-variable (squared-error doubles) over a ring buffer of window=32 with running `sum_squared_errors` aggregate maintained at Push via subtract-then-add at eviction (the pattern's canonical update form).

State embedded in `RollingRMSE` struct (`ML_Headers/ConfidenceScore.hpp`). Pre-v5.15.5.E.D, `RollingRMSE_Compute` walked all 32 samples per call (O(N) loop). Post-v5.15.5.E.D, Compute reads `sqrt(sum_squared_errors / count)` in O(1).

`sum_squared_errors` is intentionally NOT in `FOREACH_CONFIDENCE_PERSIST_FIELD` (derivable from samples). Post-load helper `ConfidenceScorer_RecomputeRunningSums` reconstructs it from samples — keeps wire format minimal (no SHARDED_SNAPSHOT_VERSION bump for a derivable field).

**FP non-associativity caveat:** RollingRMSE uses `double` (not FPN_Binary<F>); running-sum vs walked-sum are NOT bytewise identical due to FP rounding order. Bytewise parity test (`tests/controller_test.cpp` 200-push deterministic sequence) uses 1e-12 tolerance, well below realistic squared-error magnitudes (~1e-4) at window=32. For TRUE bytewise determinism, use FPN_Binary<F> (as BookImbHistory does); for slow-path scalar consumers like RMSE, tolerance-based equivalence is sufficient.

### Pattern strengthens to invariant status

With 3 canonical applications shipped (Ridge correlation + BookImbHistory dual-window + RollingRMSE), the pattern is firmly invariant. CLAUDE.md item 29 cross-references all 3 applications. Future sliding-window candidates (per the "Future applications" section below) inherit the pattern; the codification lifecycle has completed all 7 stages for this pattern as of v5.15.5.E.D.

### Future applications (anticipated)

- **Online IC tracking** (v5.15+ candidate): per-arm prediction-vs-realized-return rolling correlation over K=N_recent_trades
- **Online turnover** (v5.15+ candidate): rank-stability metric over K-cycle window
- **Online feature normalization** (v5.15+ candidate): per-feature rolling mean/std over K-tick window for runtime drift compensation
- **Online drift detection** (v5.15+ candidate): rolling moments of (prediction - realized) error distribution

Each follows the same pattern: state struct → Update/UpdateFull → Finalize → consumer. The pattern eliminates per-feature periodic-reset boilerplate.

---

## Multi-window variant (added 2026-05-13 post v5.15.5.D)

When the same ring buffer must serve TWO (or more) simultaneous windows of different sizes, maintain INDEPENDENT running sums per window over the shared `samples[]` ring. Each window's eviction logic reads samples at a different ring offset.

### State (multi-window shape)

```cpp
template <unsigned F, unsigned W = 1024>
struct alignas(64) RingWithTwoWindows {
    static constexpr int SHORT_K = 64;

    FPN<F> sum;          // long-window running sum (W samples)
    FPN<F> short_sum;    // short-window running sum (SHORT_K samples)
    int    count;        // valid sample count; saturates at W
    int    head;         // next write position

    FPN<F> samples[W];   // shared ring buffer
};
```

Both windows share the same `samples[]` array — no duplication. The HOT cluster (sum / short_sum / count / head) fits in 1 cache line. Cache discipline per `cache-layout-discipline-for-hot-side-structs.md` Rule 4.

### Push (maintain both windows)

```cpp
template <unsigned F, unsigned W>
static inline void Ring_Push(RingWithTwoWindows<F, W>* s, FPN<F> sample) {
    // Long-window maintenance: evict at samples[head] (W-cycles-old)
    if (s->count >= (int)W) {
        s->sum = FPN_Sub(s->sum, s->samples[s->head]);
    } else {
        s->count++;
    }

    // Short-window maintenance: evict at samples[head - SHORT_K] (K-cycles-old)
    // Note: check `count > SHORT_K` AFTER long-window count increment so
    // warm-up phase (count <= SHORT_K) accumulates without eviction.
    if (s->count > RingWithTwoWindows<F, W>::SHORT_K) {
        int evict_short = (s->head + (int)W - RingWithTwoWindows<F, W>::SHORT_K) % (int)W;
        s->short_sum = FPN_Sub(s->short_sum, s->samples[evict_short]);
    }

    s->samples[s->head] = sample;
    s->sum       = FPN_Add(s->sum, sample);
    s->short_sum = FPN_Add(s->short_sum, sample);
    s->head      = (s->head + 1) % W;
}
```

### Read (O(1) per window)

```cpp
template <unsigned F, unsigned W>
static inline FPN<F> Ring_MeanLong(const RingWithTwoWindows<F, W>* s) {
    if (s->count <= 0) return FPN_Zero<F>();
    return FPN_DivNoAssert(s->sum, FPN_FromDouble<F>((double)s->count));
}

template <unsigned F, unsigned W>
static inline FPN<F> Ring_MeanShortFast(const RingWithTwoWindows<F, W>* s) {
    if (s->count <= 0) return FPN_Zero<F>();
    int effective_k = (s->count < RingWithTwoWindows<F, W>::SHORT_K)
                          ? s->count
                          : RingWithTwoWindows<F, W>::SHORT_K;
    return FPN_DivNoAssert(s->short_sum, FPN_FromDouble<F>((double)effective_k));
}
```

### Per-Push cost analysis

| Operation | Long-only | Long + short (multi-window) |
|---|---|---|
| Eviction subtract | 1 (samples[head]) | 2 (samples[head] + samples[head-K]) |
| Add new sample | 1 | 1 |
| Cache lines touched | 2 (scalars + samples[head]) | 3 (scalars + samples[head] + samples[head-K]) |

The samples[head-K] line is typically L1-warm because head-K was visited K=64 cycles ago and the ring buffer is small enough that L1 retains the recent window. Practical extra cost: ~1-2 ns / Push.

**Trade vs the read-side savings:** if MeanShort is called once per cycle and previously walked K=64 samples (~24 cache lines), moving to O(1) saves ~20+ cache lines per cycle. The extra Push cost (1-2 ns) is dwarfed by the read-side savings (~500-1500 ns when cold).

### Eligibility (Multi-window variant)

Apply the multi-window variant when ALL of:

1. **Single ring buffer** serves the data for multiple analytical windows (vs separate ring buffers per window — that's a different layout)
2. **Each window's sum is independently consumed** — caller wants both long-mean and short-mean (or variance, etc.) every cycle
3. **Bounded inputs + bounded K** for each window (per main spec eligibility) — applies independently per window
4. **Short-window's K is well-defined at compile time** (otherwise can't pre-allocate `short_sum`; falls back to O(K) walk for runtime-variable K consumers)

### Skip the multi-window variant when:

- Only ONE window is consumed (single-window pattern suffices; `short_sum` field is dead weight)
- Short window's K varies at runtime across callers (e.g., test calls with k=2 + production with k=64) — keep the O(K) walk callable for non-canonical K; add `short_sum` only if the production K is fixed AND dominant
- Memory budget is tight enough that 1 extra FPN_Binary<F> per record is prohibitive (uncommon; ~16 B for FPN_Binary<64> — the canonical 16B binary core, per CLAUDE.md)

### Generalization (N-window variant)

The pattern extends to N windows: N running sums + N eviction offsets per Push. Cost scales linearly with N. Diminishing returns beyond N=2-3 windows; consider whether each window genuinely needs O(1) read or if some can stay O(K) walks.

The compile-time-fixed-K constraint (per Eligibility item 4) becomes harder for N>2 — would need a registry pattern (`FOREACH_WINDOW_K(X)` X-macro per `registry-tuple-as-single-source-of-truth.md`) to drive parallel SHORT_K1 / SHORT_K2 / ... constants if multiple short windows of different fixed sizes are needed.

### Bytewise parity discipline

When converting an existing O(K) walked consumer to the new O(1) running-sum reader (as v5.15.5.D did for BookImbHistory's MeanShort), preserve bytewise parity by:

1. Verifying FPN_Add associativity holds for the input magnitudes + accumulator range (analytical check; no overflow possible at any reorder)
2. Using the SAME divisor representation in both paths (FPN_FromDouble vs FPN_FromInt produce different bytes for fractional divisors; for whole-number K typically identical, but lock the choice explicitly)
3. Locking the contract via a bytewise parity test exercising warm-up (count < K) + steady-state (count > K) + boundary transition

See v5.15.5.D's `controller_test.cpp` BookImbHistory parity test (200-push deterministic sequence) for the canonical template.

---

## Lessons / gotchas

### Bounded-input assumption is load-bearing

If predictions can spike outside their typical [0, 1] range (e.g., model misconfiguration emits 1e6), cancellation error can blow up. Defensive: assert/log input magnitudes; clamp before accumulator update.

For ML predictions: sigmoid output is naturally [0, 1]; ensemble averages preserve this; ridge weights normalized to sum=1 preserve magnitudes. Bounded by construction.

### sum_xx storage is N² doubles — cache-line aware

For N=8: sum_xx is 8 rows × 8 doubles = 8 cache lines exactly. UpdateOnline walks one row per cache line → sequential access; good locality.

For larger N (e.g., N=64), sum_xx is 64×64 doubles = 32KB. Exceeds L1d; access pattern matters. Consider SoA layout (column-major) if access patterns favor it.

### Drop-oldest requires access to the dropped record

The pattern requires the oldest record to be available when adding a new one. Typically achieved via ring buffer that retains records.

If the source data doesn't preserve old records, the pattern degrades to full-recompute every cycle.

### Window count saturation at K

Update_NotFull increments `window_count` until it reaches K, then stays at K forever (Update_Full keeps count constant). This avoids unbounded integer growth + matches finalize's K = window_count semantics.

If `K` is parameterized (not a compile-time constant), the implementation must distinguish "filling" vs "rolling" phases consistently.

### Floating-point drop-add ordering

`a - b + c` is NOT bytewise identical to `a + c - b` in IEEE-754 (subnormal handling differs in rare cases). The pattern uses `(c - b)` then `a += (c - b)` to keep the subtract-mul-add fused per gcc -O3 -ffp-contract=fast.

For replay-determinism: lock the operation order via tests (SHA-256 snapshot per `avx512-byte-determinism-pattern.md`).

### Finalize is called per consumption, not per update

Update only maintains sum_x + sum_xx. Finalize computes mean/var/corr from sums. Caller invokes finalize when statistics are needed (typically once per slow-path cycle, not per record).

If finalize is needed per-record, the pattern wins less (Update has same O(N²) cost; just adds finalize O(N²) overhead). For per-record finalize, consider Welford M2 form which maintains finalized stats incrementally.

---

## Audit detection

`/dod-audit` should flag candidates by:

- **Symptom 1:** comment "periodic full-recompute reset" or "drift accumulation" near an incremental statistics loop → likely candidate for sliding-window refactor
- **Symptom 2:** O(K × N²) full-recompute called every cycle when only the newest record changed → likely candidate
- **Symptom 3:** parallel implementations of correlation/variance math for full-recompute vs incremental → math-kernel unification candidate (extract shared Finalize)

When detected → check eligibility (bounded inputs, bounded window, ring availability) → propose refactor referencing this doc.

---

## Patterns NOT used here (and why)

### Canonical Welford M2 form

Preferred for unbounded sample counts due to incremental variance numerator (M2) that avoids catastrophic cancellation. For FIXED window with bounded inputs, sum-of-squares form is equivalent in stability AND simpler. Welford M2 is overkill.

### Kahan summation in accumulators

Compensated summation reduces accumulator drift. For BOUNDED window + BOUNDED inputs, cancellation error is bounded WITHOUT Kahan (per stability analysis above). Adding Kahan would double the per-update cost without measurable accuracy gain.

For UNBOUNDED windows or HIGH-MAGNITUDE inputs, Kahan becomes valuable. Document it as escalation path.

### Approximate correlation via low-rank decomposition

Maintain only top-K eigenvectors of covariance + diagonal. O(N×K) state instead of O(N²); cheaper for large N. But: approximate (loses off-diagonal info); changes Ridge math behavior. Not equivalent to exact correlation matrix.

For exact correlation needs (Ridge's Cholesky requires positive-definite Σ), exact state is the cheaper choice for typical N ≤ 16.

---

## Cross-references

- `avx512-byte-determinism-pattern.md` — SIMD vectorization shape used in this pattern's AVX-512 path
- `structural-fix-preferred-decision-framework.md` — why sliding-window beats vanilla-Welford+reset (band-aid → structural fix transition)
- `bitmap-flag-api.md` — N/A for this pattern (state is double-precision floats, not booleans)
- FoxML_Trader_v2 `CLAUDE.md` item 16 — reuse-audit principle (future online-stats inherit this pattern)
- FoxML_Trader_v2 `CLAUDE.md` item 17 — latency tracking (per-cycle cost documented in HOT_PATH_CHANGELOG)
- FoxML_Trader_v2 `CLAUDE.md` item 19 — structural fix preferred for recurring classes
- FoxML_Trader_v2 `ML_Headers/RidgeBlender.hpp` (v5.14.11.A first application)
- FoxML_Trader_v2 `ML_Headers/RollingStats.hpp:78-95` — sister technique (running-sums; unbounded; different use case)
- West, D. H. D. (1979). "Updating mean and variance estimates: an improved method." — canonical sliding-window-mean recurrence; this pattern's drop math is equivalent
- Schubert, E. & Gertz, M. (2018). "Numerically stable parallel computation of (co-)variance." — modern numerical-stability analysis for incremental moments
