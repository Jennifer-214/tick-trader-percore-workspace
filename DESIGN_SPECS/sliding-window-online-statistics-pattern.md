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

For N=8: ~584 bytes (sum_x = 64B + sum_xx = 512B + count = 8B). Fits one half of an L1d cache. Per-core only (no cross-thread access).

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

### Future applications (anticipated)

- **Online IC tracking** (v5.15+ candidate): per-arm prediction-vs-realized-return rolling correlation over K=N_recent_trades
- **Online turnover** (v5.15+ candidate): rank-stability metric over K-cycle window
- **Online feature normalization** (v5.15+ candidate): per-feature rolling mean/std over K-tick window for runtime drift compensation
- **Online drift detection** (v5.15+ candidate): rolling moments of (prediction - realized) error distribution

Each follows the same pattern: state struct → Update/UpdateFull → Finalize → consumer. The pattern eliminates per-feature periodic-reset boilerplate.

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
