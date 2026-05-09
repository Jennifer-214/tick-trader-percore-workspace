# FoxML_Core → FoxML_Trader_v2 deep math audit — 2026-05-08

**Pass 2** of FoxML_Core porting analysis. Pass 1 focused on
architecture (`plans/2026-05-08-foxml-core-port-ideas.md`); this
pass focuses on MATHEMATICAL FOUNDATIONS.

## Executive summary

7 high-value mathematical frameworks worth porting beyond Pass 1:

1. **Ridge risk-parity signal blending** — multi-model alpha
   combination via `w ∝ (Σ + λI)^{-1} μ` Markowitz-style weighting.
   C++ engine has only single-model + bandit selection today;
   Ridge unlocks soft combination of multiple signals. **#1 port
   candidate.**
2. **Composite confidence scoring** (IC × Freshness × Capacity ×
   Stability) — extends existing ConfidenceScorer; feeds the
   already-shipped v5.12.1.D sizing path with a richer signal.
3. **Cross-sectional target families** (percentile rank + robust
   z-score with MAD + vol-scaled CS demeaned) — 3 target
   normalizations vs. our 1; better for ranking losses.
4. **Spearman IC** (rank correlation) — more robust than Pearson
   for non-linear prediction-return relationships.
5. **Bayesian Thompson sampling policy** (ArmStats with Gaussian
   conjugate posterior) — alternative to Exp3-IX for config
   search; not a replacement.
6. **Pairwise ranking losses** — training-only (offline Python
   pipeline); engine just loads exported weights. NOT a C++ port.
7. **GMM regime detection** — 3-component Gaussian mixture on
   PCA features. Offline trainer, not engine code.

**Maker-order verdict (correcting Pass 1):**
- Pass 1 said C++ is "taker-only" → FALSE
- Engine has `ORDER_LIMIT_BUY`/`ORDER_LIMIT_SELL` enum reserved
  (Phase 08), `is_maker` flag populated from Binance fills, and
  separate `fee_rate_maker` accounting
- MISSING: cancel-and-replace logic, price-ladder placement, queue
  position estimation
- **Realistic MVP effort: 3-4 days** (not Pass 1's inflated 15-20)

---

## Section-by-section findings

### 1. Cross-sectional (CS) statistics

**FOUND in FoxML_Core (`TRAINING/common/targets/cross_sectional.py:53-404`):**
- CS percentile rank `[0, 1]` — `ranks = scipy.rankdata(r); pct = ranks / (n+1)`
- CS robust z-score `(r - median) / (1.4826 × MAD + 1e-10)` — handles fat tails
- Vol-scaled CS demeaned `r/vol - mean_cs(r/vol)` — risk-adjusted relative perf
- All winsorize (0.01 / 0.99 percentiles or ±3σ)

**ALREADY in C++:** `Backtest/LabelFunctions.hpp` has z-score targets only (LABEL_FORWARD_PNL, etc.); no percentile-rank, no vol-scaled CS.

**NEW worth porting:** Add 3 new label kinds via `FOREACH_TARGET`
X-macro append (auto-generates LABEL_* enums, table rows,
dispatcher entries — same pattern v5.10.0d established).

**Effort:** 1-2 days for percentile rank (sort, rank, divide); +
1-2 for vol-scaled. Total ~3 days for all 3.

### 2. Online estimators

**FoxML_Core has:**
- Exponential moving variance (Bayesian policy uses; not true Welford)
- Spearman correlation via scipy
- Confidence rolling buffers (deque-based history)

**C++ engine has BETTER:**
- True Welford O(1) variance updates (`RollingStats.hpp:83-87`)
- Monotonic deque O(1) min/max
- More memory-efficient

**Verdict:** No port needed. C++ numerics already superior for this
class.

**FUTURE:** Online quantile sketches (t-digest, KLL, GK) for
adaptive percentile gates without sorted-buffer overhead. Not in
FoxML_Core; would be design-from-scratch. Lower priority.

### 3. Information coefficient (IC) variants

**FoxML_Core (`LIVE_TRADING/prediction/confidence.py:118-145`):**
- Spearman IC (rank correlation; min 5 samples; returns 0 on NaN)
- Per-horizon IC tracking
- Net IC after cost penalty: `μ[i] = max(IC_i - 0.5 × cost_i, 0.001)`

**ALREADY in C++:** `RollingIC` (Pearson IC; `RollingIC_Compute`
in `ConfidenceScore.hpp`). Used by v5.10.0e drift detection.

**NEW worth porting:**
- **Spearman IC inline**: ~1 day. Sort-based rank computation;
  more robust to outliers + monotonic-but-non-linear predictions.
  C++ implementation: maintain rolling buffer + sort + compute
  rank correlation on each push (still O(n log n) per push;
  acceptable for slow-path).
- **Cost-aware IC** (`max(IC - cost_penalty × cost, floor)`):
  trivial extension; ~30 min.

### 4. Signal combination (BLENDING) — **#1 NEW PORT**

**FoxML_Core (`LIVE_TRADING/blending/ridge_weights.py:25-139`):**

Math:
```
w ∝ (Σ + λI)^{-1} μ
where:
  Σ = correlation matrix of standardized predictions across N models
  λ = ridge regularization (default 0.15)
  μ[i] = max(IC_i - 0.5 × cost_i, 0.001)  // net IC, cost-penalized
```

Algorithm:
1. Build correlation matrix from prediction history (last K predicts)
2. Solve regularized linear system `(Σ + λI) w = μ` (Cholesky)
3. Clip to non-negative, renormalize to sum=1
4. Fallback to equal weights if matrix singular

**ALREADY in C++:** Nothing similar. Bandit-Exp3 weights select
ONE model per horizon (G.4 selection mode) or weighted-blend
across horizons via bandit weights (G.7 weighted mode), but no
Markowitz-style cost-aware IC weighting across signal sources.

**NEW worth porting:**

- C++ struct:
  ```cpp
  // ML_Headers/RidgeBlender.hpp
  template <unsigned F, int MAX_MODELS>
  struct RidgeWeights {
      double w[MAX_MODELS];                    // output weights (sum=1)
      double corr_matrix[MAX_MODELS][MAX_MODELS];
      double ridge_lambda;
  };
  void RidgeBlender_Compute(RidgeWeights<F,N>* out,
                             const double ic[],
                             const double cost[],
                             int n_models);
  ```
- Cholesky decomposition of `(Σ + λI)` (3-line algorithm for
  symmetric PD matrix; libm dependency only).
- Fallback to `w[i] = 1/n_models` on Cholesky failure.

**Effort:** 3-5 days. Risk: LOW (numerically stable, well-tested
in Python; falling-back-on-singular preserves ensemble alpha).

**Unlocks:**
- Multi-model alpha compounding (instead of single-best selection)
- Cost-aware blending (penalize fee-heavy models)
- Soft load-balancing across signal sources
- Foundation for v5.15 soft-risk-degradation (composite confidence
  → Ridge weight scaling)

### 5. Ranking losses

**FoxML_Core (`TRAINING/losses/ranking_losses.py:1-556`):**
- Pairwise logistic / hinge / softmax KL / listwise KL
- Hybrid (pairwise + pointwise) with weights

**C++ status:** Engine doesn't TRAIN models — Python trainer
exports XGBoost binary, C++ loads via Model_Predict. So loss
functions live offline.

**Verdict:** NOT a C++ port. If operator wants ranking-loss
training, modify `tools/train_*.py` (not in FoxML_Trader_v2 yet;
candidate for v5.15 trainer-side improvement).

### 6. Risk math

**FoxML_Core:** Hard kills (daily loss + drawdown) + composite
confidence as soft scaling proxy.

**C++ engine:** Hard kills (kill_switch_tripped, drawdown_pct,
v5.10.0e IC drift). NO Kelly, Sortino, Calmar, Information Ratio.

**Verdict:** Sharpe variants belong in **daily reporting**
(BacktestPanels Past Runs), not the live engine loop. Composite
confidence scoring (#1 in Pass 1, confirmed here) IS the
soft-degradation lever; port that, defer Sharpe variants to
reporting layer.

### 7. Loss functions / calibration

**FoxML_Core:** Huber loss + (implied) Brier/log-loss in metrics.

**Verdict:** Same as #5 — training-time only. Not a C++ port.
However, **calibration metrics IN PRODUCTION** are useful — Brier
score, ECE (Expected Calibration Error) on the v5.13.0.B
calibration log would help operator diagnose model degradation
post-paper-test. ~1 day of post-processing script work; not a C++
ship.

### 8. Numerical methods

**Already covered in #2.** C++ better than FoxML_Core for the
common cases (Welford > simple EWMA variance).

### 9. Statistical tests / drift detection

**FoxML_Core:**
- PSI (Population Stability Index, threshold 0.2)
- KS test (Kolmogorov-Smirnov, threshold 0.1)

**C++ engine:** v5.10.0e IC drift detection (rolling IC < floor →
WARN/kill). PSI + KS are batch operations.

**Verdict:** PSI + KS belong in **daily reporting** (post-fill
batch processing of the calibration log). Not engine-loop work.
~2 days of Python script in `tools/`. v5.16+ candidate.

### 10. Feature engineering

**FoxML_Core (`DATA_PROCESSING/features/simple_features.py:31-150`):**
50+ technical indicators (SMA, EMA, RSI, MACD, Bollinger, Ichimoku,
etc.). NO fractional differentiation.

**C++ engine:** Feature registry computes price/vol/spread/flow
features; ML model handles indicator combinations implicitly via
XGBoost trees.

**NEW worth porting:**
- **Fractional differentiation** (Lopez de Prado, 2018) —
  `Δ^d x_t = Σ(-1)^k C(d,k) x_{t-k}`, d ∈ (0, 1). Reduces
  autocorrelation while preserving stationarity. Better feature
  engineering for mean-reversion signals.
  - **NOT IN FoxML_Core** — would be design-from-scratch.
  - Effort: ~2 days (binomial weights LUT, sliding-window
    convolution).
  - Risk: LOW.

### 11 (bonus). Bandit math richness

**FoxML_Core (`TRAINING/decisioning/bayesian_policy.py:50-120`):**
- ArmStats with Bayesian Gaussian conjugate priors
- Thompson sampling for arm selection
- Exponential moving variance updates

**ALREADY in C++:** Exp3-IX bandit (v5.10.0a.G.7) + persistence +
sell-side variant (v5.13.4).

**NEW worth porting:**
- **Thompson sampling alternative path** to Exp3-IX. Not a
  replacement — different exploration strategy (TS is randomized
  via posterior sampling vs. Exp3 deterministic with random
  exploration).
- Effort: 4-5 days. Risk: MEDIUM (operator paper-test should
  decide which performs better in their regime).
- Defer to v5.15+ unless paper-test reveals Exp3 limitations.

---

## TOP 10 RANKED PORTS TABLE

| # | Math | Formula | FoxML_Core file:line | C++ target | Effort | Risk | Sprint |
|---|---|---|---|---|---|---|---|
| 1 | Ridge risk-parity blending | `w ∝ (Σ + λI)^{-1} μ` | ridge_weights.py:25-139 | ML_Headers/RidgeBlender.hpp | 3-5 days | LOW | v5.14 |
| 2 | Composite confidence scoring | `IC × Fresh × Capacity × Stability` | confidence.py:52-200 | ConfidenceScore.hpp extension | 2-3 days | MED | v5.14 |
| 3 | CS percentile + z-score targets | `pct = rankdata/n+1`; `z = (r-med)/MAD` | cross_sectional.py:83-255 | LabelFunctions.hpp X-macro append | 1-2 days | LOW | v5.15 |
| 4 | Spearman IC | rank correlation | confidence.py:118-145 | ConfidenceScore.hpp | 1 day | LOW | v5.15 |
| 5 | Bayesian Thompson sampling | ArmStats with Gaussian conjugate | bayesian_policy.py:50-120 | (alternative to Exp3) | 4-5 days | MED | v5.15+ |
| 6 | Cost-aware IC penalty | `μ = max(IC - 0.5×cost, floor)` | ridge_weights.py:34 | inline with #1 | <1 day | LOW | v5.14 |
| 7 | Fractional differentiation | `Δ^d x_t = Σ(-1)^k C(d,k) x_{t-k}` | NOT IN FoxML_Core | Feature eng layer | 2 days | LOW | v5.16+ |
| 8 | PSI + KS drift detection | `PSI=Σ(p-q)log(p/q); KS=max\|P-Q\|` | metrics.py:215-220 | tools/ Python (daily reporting) | 2 days | LOW | v5.16+ (reporting) |
| 9 | Online correlation matrix | `Σ_new = (Σ(n-1) + x⊗x) / n` | ridge_weights.py:183-189 | RollingStats extension | 2-3 days | MED | v5.16+ |
| 10 | Calibration metrics on v5.13.0.B log | Brier + ECE | metrics.py | tools/ Python | 1 day | LOW | post-paper-test |

---

## MAKER-ORDER STATUS (CORRECTED FROM PASS 1)

**Pass 1 claim:** "C++ engine is taker-only" → **FALSE**

**Evidence in `CoreFrameworks/OrderManager.hpp`:**
- Line 49 area: `OrderType` enum reserves `ORDER_LIMIT_BUY` /
  `ORDER_LIMIT_SELL` (Phase 08)
- Line 94-98: `Order.is_maker` field populated from Binance
  `executionReport "m"` field
- Line 205: `fee_rate_maker` separate from `fee_rate_taker`
- Line 864 / 939: `HandleFill` correctly picks per-order fee rate
  based on `is_maker`
- Line 868 / 943: `maker_fills_count` + `total_maker_fees`
  separate counters

**ALREADY IMPLEMENTED:**
- Order state machine (PENDING → SUBMITTED → ACKNOWLEDGED →
  PARTIAL → FILLED)
- Fill tracking with `is_maker` flag
- Per-order fee accounting differentiation

**MISSING (genuine gap for full maker support):**
- LIMIT order TYPE in `SubmitCommand` (currently only MARKET)
- `limit_price` field on `SubmitCommand`
- `BinanceAdapter` POST_ONLY (`timeInForce=GTX`) submit path
- Cancel-and-replace logic for stale limits
- Price-ladder placement heuristic (where to place limit relative
  to best bid/ask)
- Partial-fill state machine extension

**Realistic MVP effort:** 3-4 days for cancel-and-replace + post-
only flag + simple price-ladder. NOT 15-20 days as Pass 1 claimed.

**Order book infrastructure:** ALREADY HAVE — `DepthReplayState`
+ `BookSnapshot<F>` (best_bid, best_ask, spread, mid_price);
backtest replay + live WS feed both populate it. Maker submit
just needs a read path from slow-path-to-submit code.

---

## PORTING ROADMAP BY SPRINT

### v5.14 (HIGH-VALUE, LOW-RISK — start here)

| Item | Effort | Risk | Source |
|---|---|---|---|
| **Ridge risk-parity blending** | 3-5 days | LOW | Math audit #1 |
| **Composite confidence scoring** | 2-3 days | MED | Pass 1 + Math audit #2 |
| **3-layer registry fingerprinting** | 3-4 days | LOW | Pass 1 |
| **Multi-mode reconciliation** | 2-3 days | LOW | Pass 1 |
| **/bug-check skill** | 4 hours | LOW | v5.13.5 close |
| **Hot-swap exit_predictor coverage** | 2 days | MED | v5.13.6.B finding |

**Total: ~17-23 days** (3-4 sub-ships if parallelized; 4-week
sprint if serialized)

### v5.15 (MEDIUM-VALUE)

| Item | Effort | Risk |
|---|---|---|
| Spearman IC | 1 day | LOW |
| CS percentile + z-score targets (X-macro append) | 1-2 days | LOW |
| Cost-aware IC penalty | <1 day | LOW |
| Soft risk degradation ladder (builds on composite confidence) | 3-4 days | MED |
| Bayesian Thompson sampling alternative | 4-5 days | MED |

**Total: ~10-13 days**

### v5.16+ (NICE-TO-HAVE / REPORTING)

- Fractional differentiation features
- Online correlation matrix updates
- PSI + KS distribution shift (Python tools/ for daily reporting)
- Calibration metrics on v5.13.0.B log (Python tools/)

### MAJOR ARCHITECTURAL ADDITION (separate sprint)

- **Maker-order MVP** (3-4 days; v5.14 candidate IF paper-test
  validates fill-rate assumptions; otherwise v5.16+)
- **Crypto options** (~2-4 weeks; standalone; defer to post-spot
  paper-test)

---

## KEY INSIGHTS

1. **Ridge blending is the highest-leverage NEW math port.** It
   complements (not replaces) the bandit selector by enabling SOFT
   combination of multiple signal sources. Unlocks multi-model
   alpha compounding.

2. **Composite confidence + soft degradation** transform our hard-
   kill risk math into graceful degradation. Position size scales
   with signal health instead of cliff-edge stops.

3. **C++ engine numerics already exceed FoxML_Core** for the
   common rolling-stats class (true Welford > simple EWMA
   variance). Don't port what we already do better.

4. **Most loss functions / calibration metrics live offline.**
   C++ trains via XGBoost binary export; ranking losses + Brier
   score belong in the Python trainer / reporting layer.

5. **Maker-order infrastructure is 70% there.** Just needs cancel-
   and-replace + price-ladder + POST_ONLY flag. 3-4 day MVP, not
   the 15-20 days Pass 1 estimated.

6. **Order book is fully plumbed.** DepthReplayState +
   BookSnapshot exist for backtest + live; ML already uses
   book_imbalance / spread_z features. Maker placement just
   reads what's already there.
