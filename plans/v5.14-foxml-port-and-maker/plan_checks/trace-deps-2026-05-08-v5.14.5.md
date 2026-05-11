# /trace-deps report — v5.14.5 CS targets + regime features + frac diff — 2026-05-08

**Verdict:** **RED → addressable** with 3 plan fixes (1 small, 1 trivial, 1 defer)

## 3 BLOCKING gaps

### #1 — Label_CS* signature drift (BLOCKING)

Plan proposes `(ticks, tick_idx, total_ticks, BacktestRunConfig *cfg)`.
Actual `LabelFn` typedef at `LabelFunctions.hpp:284`:
`(ticks, tick_idx, total_ticks, sample_price, tp_pct, sl_pct, extra_param)`.

All 8 existing labels use the 7-param signature; dispatcher casts via
typedef. Plan signature would fail link.

**Fix:** Refactor 3 Label_CS* fns to 7-param signature; use
`extra_param` (= `forward_ticks`) for horizon; ignore tp/sl (CS targets
don't use barriers). ~5-min plan edit.

### #2 — Regime feature naming drift (BLOCKING)

Plan: `Compute_RegimeTrendStrength` etc.
Actual convention: `ML_Compute_*` prefix (all 34 existing features).
FOREACH_FEATURE dispatcher would call non-existent function names → link error.

**Fix:** Prefix all 3 regime fns with `ML_Compute_`. Trivial.

### #3 — Frac diff missing raw-history data (BLOCKING; DEFER)

`FeatureComputeCtx` only has `signals` + `short_rolling` (aggregates).
RollingStats stores mean/stddev/slope, NOT raw tick values.
Frac diff formula `Δ^d x_t = Σ(-1)^k C(d,k) x_{t-k}` requires raw
sliding window of last N=100 prices.

**Fix:** **DEFER frac diff to v5.16+** (after FeatureComputeCtx
extension or RawPriceRing infra lands). Removes v5.14.5.C sub-tag;
v5.14.5 stays bundled with .A (CS targets) + .B (regime features)
only. Still single retrain cycle (LABEL + FEATURE hash bumps).

## Verified existing skeletons (PASS)

| Claim | Location | Status |
|---|---|---|
| FOREACH_TARGET X-macro | LabelFunctions.hpp:47 | PASS (clean append point) |
| FOREACH_FEATURE X-macro | FeatureRegistry.hpp:294 | PASS (clean append point) |
| HistoricalTick struct | LabelFunctions.hpp:25 | PASS |
| BacktestRunConfig | BacktestEngine.hpp:186 | PASS |
| RegimeSignals<F> | RegimeDetector.hpp | PASS |
| Regime_ComputeSignals | RegimeDetector.hpp:222 | PASS |
| LabelFn typedef | LabelFunctions.hpp:284 | PASS (canonical signature defined here) |
| FeatureComputeCtx<F> | FeatureRegistry.hpp:66 | PASS (but NO raw history field) |

## Per-step results

- Step 1 (FOREACH_TARGET append): PASS ✓
- Step 2 (Label_CS*): RED — signature drift; fix above
- Step 3 (tests): deferred until Step 2 fixed
- Step 4 (regime features): RED — naming drift; fix above
- Step 5 (frac diff): RED — missing data; DEFER to v5.16+

## Effort to GREEN

- Fix #1 + #2 (signature + naming): ~10 min plan edit
- Fix #3 (defer frac diff to v5.16+): ~5 min plan + master update

After fixes: GREEN on v5.14.5.A + .B only.

## Verdict: **RED → fixable in ~15 min plan edits**
