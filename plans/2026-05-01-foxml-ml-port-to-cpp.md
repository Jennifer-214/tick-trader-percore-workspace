# FoxML ML pipeline → C++ port plan

**Date:** 2026-05-01
**Source:** ~/code/FoxML_Core (Python + Rust ML infra, archiving)
**Target:** ~/code/tick-trader-percore (C++ engine, absorbing the ML side)

**Strategic context:** FoxML_Core is being archived. Its ML
infrastructure ideas (walk-forward CV, leakage detection, feature
standardization, training pipeline) are the part worth preserving.
Reimplementing in C++ inside the trader gets:
- Faster training/inference (no Python interpreter overhead)
- Drift-resistance by construction (same FPN math + OneCore
  helpers + locale pinning as the rest of the engine)
- One codebase, one mental model
- The 431-line hot path stays untouched (training is slow-path /
  offline)

This is a multi-phase plan. Each ship is independently valuable.
Pick + reorder based on appetite.

---

## What's already in tick-trader

- XGBoost C API inference (`ML_Headers/ModelInference.hpp`)
- Held-out validation gate at model-load time (v5.2.0+)
- HMAC-signed model stamps (`stamp_write_for_model`,
  `verify_model_stamp`, in-process via OpenSSL EVP)
- ConfidenceScorer (rolling Spearman IC + RMSE stability + freshness)
- BarrierGate
- ML feature pack (`ModelFeatures_Pack`) for inference
- RegimeSignals → strategy routing
- Single-fold held-out split (`Backtest/HeldOutSplit`)
- Run history JSONL appender
- Walk-forward concept (mentioned in CHANGELOG, partial)

## What's in FoxML that's worth bringing over

Ranked by ML-pipeline-load-bearingness × C++-port-feasibility.

---

## Phase 1 — Walk-forward CV harness (v5.8.0)

**What FoxML has:** Multi-fold walk-forward CV with per-fold metrics
(IC, AUC, hit rate, etc.), aggregated mean + variance + stability.
Each fold trains on `[0, fold_end)`, evaluates on `[fold_end, fold_end + horizon)`.
The MEAN-VS-HELD-OUT gap is the deployment confidence proxy.

**What trader has:** `Backtest/HeldOutSplit.hpp` does single-fold
held-out at the end. The walk-forward concept is referenced in
CHANGELOG but not formalized as multi-fold infrastructure.

**Port shape:**
```cpp
// new: Backtest/WalkForward.hpp
template <unsigned F>
struct WalkForwardConfig {
    int     num_folds;          // typical: 5-10
    int     fold_horizon_ticks; // hold-out window per fold
    double  min_train_ticks;    // anchor: minimum train data
    int     mode;               // EXPANDING | ROLLING
};

template <unsigned F>
struct WalkForwardFold {
    int     fold_idx;
    int     train_start;
    int     train_end;
    int     eval_start;
    int     eval_end;
    double  metric;             // IC for regression, AUC for classification
    double  metric_stddev;
    int     n_samples_eval;
};

template <unsigned F>
struct WalkForwardResult {
    int                            num_folds_completed;
    double                         mean_metric;
    double                         metric_stddev_across_folds;
    double                         held_out_metric;          // final fold or
                                                              // separate test split
    double                         gap;                       // |mean - held_out|
    std::vector<WalkForwardFold<F>> folds;
};

template <unsigned F>
WalkForwardResult<F> WalkForward_Run(
    const Tick<F>* ticks, int n_ticks,
    const WalkForwardConfig<F>& cfg,
    /* model + feature spec */);
```

**Files:** `Backtest/WalkForward.hpp` + `tests/walk_forward_test.cpp`.
Stamp body's `wf_mean_metric` field already exists (v5.2.0); WF
implementation populates it for real instead of via the stub.

**Effort:** ~10-12h. Largest of the phases — the engine is the
load-bearing part.

**Value:** real walk-forward stability data for every model trained.
Stamps stop being theoretically-validated and start being
empirically-validated.

---

## Phase 2 — Feature standardization with persisted train-time params (v5.8.1)

**What FoxML has:** `LIVE_TRADING/prediction/standardization.py`
applies train-time per-feature mean/std at inference. Closes the
"feature looks the same but scaled differently in train vs serve"
silent drift.

**What trader has:** Implicit standardization via live rolling
stats. Train and serve both use rolling stats but the WINDOW is
the same — so they agree numerically only when warmup is identical.
Cold-start train-serve gap.

**Port shape:**
```cpp
// extension to ML_Headers/ModelInference.hpp
template <unsigned F>
struct FeatureStandardization {
    int   n_features;
    FPN<F> mean[MAX_FEATURES];
    FPN<F> stddev[MAX_FEATURES];
    int   version;  // bump if normalization formula changes
};

// stamp body extension — these get HMAC-signed alongside the
// rest of the metadata
inline void Stamp_AddStandardization(StampBody& body,
                                       const FeatureStandardization<F>& norm);

// inference-time apply (slow path, before ModelInference_Predict)
inline void Standardization_Apply(
    const FeatureStandardization<F>& norm,
    FPN<F>* features, int n);
```

**Files:** extends `ModelStamp.hpp` + `ModelInference.hpp`. New
helper for serialize/deserialize the norm params into the stamp
body. New test for round-trip.

**Effort:** ~6h. Requires retraining existing models with the new
stamp format. MODEL_FORMAT_VERSION bump.

**Value:** closes a silent train-serve drift class.

---

## Phase 3 — Leakage sentinels (v5.8.2)

**What FoxML has:** `TRAINING/common/leakage_sentinels.py` —
automated tests detecting:
- **Future leak**: feature uses data only available at t+k
- **Target leak**: feature is a noisy/transformed version of the
  target
- **Look-ahead in CV**: training fold contains samples chronologically
  AFTER eval samples
- **Window leak**: rolling window straddles a fold boundary

**What trader has:** Held-out gate catches gross train↔held-out
gaps but doesn't identify WHICH feature is leaking.

**Port shape:**
```cpp
// new: ML_Headers/LeakageSentinels.hpp

struct SentinelResult {
    char    test_name[64];
    int     passed;
    double  score;     // test-specific (correlation, t-stat, etc)
    double  threshold;
    char    detail[256];
};

template <unsigned F>
SentinelResult Sentinel_FutureLeak(
    const FPN<F>* features, const FPN<F>* targets,
    int n_samples, int n_features, int feature_idx);

template <unsigned F>
SentinelResult Sentinel_TargetCorrelation(
    const FPN<F>* features, const FPN<F>* targets,
    int n_samples, int n_features, int feature_idx,
    double max_correlation = 0.95);

template <unsigned F>
SentinelResult Sentinel_LookAheadFold(
    const Tick<F>* ticks, int train_end, int eval_start, int eval_end);

// Run all sentinels against a training run, return aggregate
template <unsigned F>
struct SentinelReport {
    int     num_tests;
    int     num_passed;
    int     num_failed;
    SentinelResult results[64];
};
```

**Files:** `ML_Headers/LeakageSentinels.hpp` + tests. Wire into
`Backtest_RunFullValidation` so any new training run runs the
sentinels and refuses to stamp on failure.

**Effort:** ~8-10h. Several sentinel rules, each with tests. The
hard part is calibrating thresholds.

**Value:** catches a class of bugs (feature engineering with
implicit leakage) that the held-out gap doesn't surface until
deployment.

---

## Phase 4 — In-process XGBoost training (v5.8.3)

**What FoxML has:** `TRAINING/train.py` — XGBoost training pipeline.
Configurable hyperparameters, callback handling, feature importance,
serialization.

**What trader has:** XGBoost C INFERENCE API only. Training happens
externally (in FoxML, soon to be archived).

**Port shape:**
```cpp
// extension to ML_Headers/ModelInference.hpp or new ModelTrain.hpp
struct XGBoostTrainConfig {
    int      max_depth;          // 6
    double   eta;                // 0.1
    double   subsample;           // 0.8
    double   colsample_bytree;    // 0.8
    int      num_round;           // 200
    int      seed;                // for determinism
    char     objective[64];       // "binary:logistic" / "reg:squarederror"
    char     eval_metric[64];     // "auc" / "rmse"
};

template <unsigned F>
struct XGBoostTrainResult {
    int       num_iters_completed;
    double    train_metric_final;
    double    eval_metric_final;
    char      model_path[512];
    int       success;
};

template <unsigned F>
XGBoostTrainResult XGBoost_Train(
    const FPN<F>* features, int n_samples, int n_features,
    const FPN<F>* targets,
    const FPN<F>* eval_features, int n_eval_samples,
    const FPN<F>* eval_targets,
    const XGBoostTrainConfig& cfg,
    const char* output_model_path);
```

XGBoost C API has `XGBoosterCreate`, `XGBoosterUpdateOneIter`,
`XGBoosterEvalOneIter`, `XGBoosterSaveModel`. All callable from C++.

**Files:** `ML_Headers/ModelTrain.hpp` + tests. The CMake link
already includes XGBoost (USE_XGBOOST=ON path). Tests use a
synthetic dataset with known signal.

**Effort:** ~14-16h. The wrapping is straightforward; the
calibration of "what hyperparameters match what FoxML used"
requires a reference run.

**Value:** training capability stays in C++. No more Python in
the workflow. Faster iteration. Same FPN math + locale pinning
as the rest.

---

## Phase 5 — Feature registry + version (v5.8.4)

**What FoxML has:** `TRAINING/common/feature_registry.py` —
registered feature names with versions. Adding/renaming a feature
forces a registry version bump, which forces a model fingerprint
mismatch, which forces a retrain.

**What trader has:** Implicit feature list in `ModelFeatures_Pack`.
Adding a feature is a code change; nothing automatically catches
"I added a feature but forgot to update the model."

**Port shape:**
```cpp
// new: ML_Headers/FeatureRegistry.hpp

struct FeatureSpec {
    const char* name;       // "ema_sma_spread"
    uint8_t     version;    // bump on formula change
    uint8_t     bytes;      // sizeof(FPN<64>) typically
    uint8_t     window;     // rolling window if applicable
    const char* note;       // 1-line description
};

constexpr FeatureSpec FEATURE_REGISTRY[] = {
    {"ema_sma_spread",       1, 24, 128, "EMA - SMA, normalized by stddev"},
    {"short_r2",             1, 24, 128, "R^2 of short-window price regression"},
    {"ror_slope",            1, 24, 128, "regression-on-regression slope"},
    {"book_imbalance_now",   1, 24, 0,   "(bid_vol - ask_vol) / total"},
    {"flow_ewma_10s",        1, 24, 0,   "signed flow 10s half-life"},
    // ... etc
};

constexpr int FEATURE_REGISTRY_HASH = /* compile-time hash of names + versions */;

// Stamp body includes FEATURE_REGISTRY_HASH; load-time mismatch
// rejects the model.
```

**Files:** `ML_Headers/FeatureRegistry.hpp` + extension to
`ModelStamp.hpp`. Compile-time hash via `constexpr`.

**Effort:** ~5h. Mostly cataloging existing features into the
registry struct.

**Value:** catches "feature added but model forgotten" class of
bug at compile-time fingerprint mismatch instead of runtime
deployment surprise.

---

## Phase 6 — Multi-horizon training + arbitration (v5.8.5)

**What FoxML has:** Train models at multiple horizons (1m / 5m /
15m). At inference, an arbiter picks the best-confidence
prediction across horizons.

**What trader has:** Single horizon (next-tick or near-term defined
by the strategy's TP/SL geometry). No arbitration.

**Port shape:**
```cpp
// new: ML_Headers/HorizonArbiter.hpp

template <unsigned F>
struct HorizonModel {
    int               horizon_ticks;   // 60, 300, 900
    BoosterHandle     model;
    FeatureStandardization<F> norm;
    FPN<F>            last_prediction;
    FPN<F>            last_confidence;
};

template <unsigned F>
struct HorizonArbiter {
    int          n_horizons;
    HorizonModel<F> horizons[8];
    int          last_chosen_idx;
    FPN<F>       last_chosen_prediction;
};

template <unsigned F>
inline int HorizonArbiter_Choose(
    HorizonArbiter<F>* arbiter,
    const FPN<F>* features, int n_features);

// Strategies can opt-in to multi-horizon by reading the arbiter
// output instead of a single-model prediction.
```

**Files:** `ML_Headers/HorizonArbiter.hpp` + integration in
`Strategies/MLStrategy.hpp`. Optional cfg flag (default off).

**Effort:** ~8h. Mostly bookkeeping; the per-horizon inference is
just N parallel model loads.

**Value:** ensemble-style robustness without leaving the per-core
sharded design. Each core can still own one arbiter; arbiter
chooses best horizon per tick.

---

## Phase 7 — Determinism mode for backtest (v5.8.6)

**What FoxML has:** `TRAINING/common/determinism.py` +
`bin/run_deterministic.sh` — bitwise reproducible runs. Same input
→ same output, byte-for-byte.

**What trader has:** Backtest is deterministic in spirit (single-
threaded execution path, FPN math) but no formal guarantee. Fan-out
to per-core threads MAY introduce timing-dependent ordering in
event_rings drain.

**Port shape:**
- New `cfg.deterministic_backtest = 1`. When set:
  - Producer + drainer + slow-path threads run in deterministic
    interleaving (single-threaded loop, not pthread)
  - tick rings drained per-fan-out (no interleave from real-time
    scheduling)
  - Output canonical-JSON serialization order
- Verification harness: run same backtest twice, diff outputs.
  Refuse to ship if diff > 0 bytes.

**Files:** new `Backtest/Deterministic.hpp` driver + cfg field +
verification test.

**Effort:** ~8-10h. Threading mode change is the hard part;
verification is straightforward.

**Value:** "this backtest is bit-for-bit reproducible" claim
becomes provable. Useful for any future audit/customer
conversation.

---

## Phase 8 — Walk-forward stability tracker (v5.8.7)

**What FoxML has:** `TRAINING/stability/` — tracks per-feature
performance across walk-forward folds. Detects features that look
good on average but are unstable across time.

**What trader has:** Nothing equivalent. Walk-forward (Phase 1)
gives mean+stddev; stability adds per-fold deltas + trend.

**Port shape:**
- Extension to Phase 1's `WalkForwardResult`. Add per-fold deltas
  (this fold's metric vs running mean).
- Stability score = stddev / mean. Below threshold = unstable.
- Optional: refuse to stamp models whose stability is poor.

**Files:** extension to `Backtest/WalkForward.hpp`.

**Effort:** ~4h once Phase 1 is shipped.

**Value:** catches "this model has a great mean but the variance
is huge" — the kind of model that looks good in the held-out
metric but blows up on a single bad fold during deployment.

---

## Phase 9 — Bayesian decision policy (DEFERRED)

**What FoxML has:** `TRAINING/decisioning/bayesian_policy.py` —
Bayesian framework for routing decisions (which target to trade,
which model to use, which horizon to weight).

**Trader's case:** The regime classifier + REGIME_STRATEGY_TABLE +
hysteresis already handle "which strategy fires when" via a
simpler voting + dwell mechanism. Bayesian framework is heavier
than current design needs.

**Action:** keep as inspiration. Don't port unless the regime
classifier proves insufficient.

---

## Sequencing recommendation

Ship Phase 4 (in-process XGBoost training) FIRST — it unblocks
archiving FoxML by replacing the training pipeline. Then:

1. **Phase 4** — XGBoost training (closes the FoxML dependency)
2. **Phase 1** — Walk-forward CV (replaces FoxML's WF)
3. **Phase 2** — Feature standardization (closes a silent drift)
4. **Phase 5** — Feature registry (catches a future bug class)
5. **Phase 3** — Leakage sentinels (catches a future bug class)
6. **Phase 7** — Determinism mode (audit/compliance)
7. **Phase 8** — Walk-forward stability (Phase 1 extension)
8. **Phase 6** — Multi-horizon (only if multi-horizon is a real need)

Total estimated: ~70-90h across 8 phases. ~3-4 weeks calendar
time at typical ship cadence. Each phase is independently
shippable; you can stop after Phase 4 and have already replaced
FoxML's training role.

## Tagging

Same per-phase tag discipline as v5.6/v5.7. v5.8.0 = first ship,
v5.8.7 = full ML reabsorption complete.

## Branch

Recommend new branch `feat/v5.8-ml-absorbs-foxml` from `main`
(`experiment/per-core-sharding`) once v5.6/v5.7 is merged. Don't
pile on the v5.6 branch.

## What stays in FoxML's git history

The DASHBOARD code (Python web UI), the IBKR/Alpaca broker
adapters, the cross-sectional ranking infra, the multi-symbol
panel data handling, the Bayesian policy framework. None of these
fit the trader's scope. They live in FoxML's archived state for
reference.

## What we get when this is done

- Training entirely in C++. No Python in the live workflow.
- Walk-forward CV + held-out gate + stability tracker — every
  model has empirical deployment confidence numbers, not stubbed
  ones.
- Feature standardization closes the silent train-serve drift.
- Feature registry catches "added feature, forgot to retrain"
  before the model ships.
- Leakage sentinels catch a class of feature engineering bugs
  before they make it to a stamp.
- Determinism mode lets you say "this backtest is reproducible"
  and prove it.
- One codebase. ~50K LOC after this work lands. Still tight.

The trader gains roughly the entire research-grade ML
infrastructure FoxML had, but in C++ at hot-path-adjacent speed,
with the trader's existing drift-resistance discipline applied.
