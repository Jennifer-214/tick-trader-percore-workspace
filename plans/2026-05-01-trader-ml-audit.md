# Trader ML capability audit — what exists, what doesn't, what could be better

**Date:** 2026-05-01
**Purpose:** before writing v5.8 absorption phases, audit what FoxML
capabilities the trader ALREADY has. The previous v5.8 plan over-
scoped because I didn't realize how much had already been ported.

**Methodology:** walked `ML_Headers/` and `Backtest/` directories,
grepped for FoxML-port markers, traced the full XGBoost training
pipeline + walk-forward + held-out gate.

**Headline finding:** the trader has ~70% of FoxML's ML pipeline
already. The remaining v5.8 work is much smaller than originally
estimated.

---

## ALREADY in the trader (don't re-port)

### Core ML primitives (`ML_Headers/`)

| Module | Status | Notes |
|---|---|---|
| `BarrierGate.hpp` | ✅ FoxML port | classification gate |
| `BanditLearning.hpp` | ✅ FoxML port | EXP3-IX multi-armed bandit |
| `ConfidenceScore.hpp` | ✅ FoxML port | rolling Spearman IC + RMSE + freshness decay |
| `CoreModelZoo.hpp` | ✅ trader-native | multi-model loader (per-role models per core) |
| `CostModel.hpp` | ✅ FoxML port | timing + impact + spread cost (v5.5.0) |
| `FlowFeatures.hpp` | ✅ trader-native | book imbalance / signed flow / large-trade z-score |
| `GateControlNetwork.hpp` | ⚠ sketched | watcher module, "not sure how to implement" — incomplete |
| `LinearRegression3X.hpp` | ✅ FoxML port | rolling 8-sample OLS with R² |
| `LinearRegressionSimple.hpp` | ✅ trader-native | single-feature OLS |
| `ModelInference.hpp` | ✅ trader-native | XGBoost C inference + held-out gate at load |
| `RewardTracker.hpp` | ✅ trader-native | reward attribution ring + CSV export |
| `RollingStats.hpp` | ✅ trader-native | windowed OLS + R² + variance + VWAP |
| `ROR_regressor.hpp` | ✅ trader-native | regression-on-regression (trend acceleration) |
| `VolScaler.hpp` | ✅ FoxML port | volatility-inverse position sizing |
| `WelfordStats.hpp` | ✅ trader-native | O(1) online mean/variance |

### Backtest + training (`Backtest/`)

| Module | Status | Notes |
|---|---|---|
| `BacktestEngine.hpp` | ✅ trader-native | main training/eval orchestration (~1800 LOC) |
| `BacktestPanels.hpp` | ✅ trader-native | GUI training panel with progress + cancel |
| `BacktestSharded.hpp` | ✅ FoxML-port-adjacent | sharded backtest driver |
| `BacktestSnapshot.hpp` | ✅ trader-native | backtest result persistence |
| `Fingerprint.hpp` | ✅ FoxML port | data fingerprinting (sha256 of features+labels) |
| `HeldOutSplit.hpp` | ✅ trader-native | held-out split logic + lock/unlock token |
| `LabelFunctions.hpp` | ✅ FoxML port | label engineering (binary/multiclass/regression) |
| `OverfitDetection.hpp` | ✅ FoxML port | 4-threshold overfit checks (memorization, train/CV gap, train/val gap, n_features cap) |
| `ValidationSplit.hpp` | ✅ FoxML port | validation split helper |

### Functions already implemented in `BacktestEngine.hpp`

These match FoxML's `TRAINING/` capabilities directly:

- `BacktestData_DetectFormat` / `BacktestData_Load` — CSV ingest
- `XGBoost_ComputeScalePosWeight` — class-imbalance handling for binary
- `XGBoost_ComputeMulticlassWeights` — class-imbalance for multi-class
- `BacktestStats_Compute` / `BacktestStats_ComputeFromEquity` — sharpe, drawdown, profit factor, expectancy
- `Backtest_ComputeLabelsFromSamples` — label generation from tick data
- **`Backtest_RunWalkForward`** — multi-fold walk-forward CV with per-fold accuracy/MSE/correlation/multiclass-accuracy
- `WalkForwardFoldResult` / `WalkForwardResults` — per-fold metric storage
- `WalkForward_ComputeAccuracy` / `_ComputeMSE` / `_ComputeCorrelation` / `_ComputeMulticlassAccuracy`
- **`HeldOutSplit_TrainEval`** — single-fold held-out training + eval
- **`Backtest_RunFullValidation`** — orchestrates WF on train+val portion + held-out on test portion + auto-stamp on success
- `FullValidationResults` with `wf_to_held_out_gap` + `gap_acceptable` + `gap_threshold` — the deployment confidence proxy
- **Auto-stamp pipeline** — `auto_stamp_path` + `auto_stamp_secret` + emits HMAC-signed `.stamp` file alongside model
- `OptimizerRange` / `OptimizerResults` / `Backtest_RunSweep` — parameter sweep!

### Stamp + verification (`ML_Headers/ModelInference.hpp` + `MemHeaders/HmacSha256.hpp`)

- `verify_model_stamp` — HMAC-SHA256 verification at model load
- `stamp_write_for_model` — sign + emit stamp at training completion
- `hmac_sha256_hex` / `sha256_file_hex_inproc` — in-process EVP (no popen)
- LC_NUMERIC=C pinning around canonical body printf
- Atomic `.stamp` writes via `fopen(.tmp) + rename()`

---

## NOT in the trader (real v5.8 work)

### High-leverage gaps

| # | Capability | Effort | Closes silent bug class? |
|---|---|---|---|
| 1 | Feature standardization with persisted train-time params | 6h | YES — silent train-serve scale drift |
| 2 | Feature registry + version + fingerprint contribution | 5h | YES — "added feature, forgot to retrain" |
| 3 | Leakage sentinels (target-leak, future-leak, look-ahead) | 8-10h | YES — feature-engineering bugs |
| 4 | Walk-forward stability variance metric | 2h | partial — flags unstable models |
| 5 | Bitwise determinism mode for backtest | 8-10h | NO — audit/compliance |

### Lower-priority gaps

| # | Capability | Effort | Notes |
|---|---|---|---|
| 6 | Multi-horizon training + arbitration | ~16h | only useful for ensemble; trader is single-horizon by design |
| 7 | Calibration / temperature scaling | ~4h | converts raw scores to probabilities; useful with Bayesian |
| 8 | GateControlNetwork.hpp completion | unknown | sketched but "not sure how to implement" — defer |

### Already-in-trader-but-could-be-better

| Module | What's there | Possible improvement |
|---|---|---|
| `RewardTracker.hpp` | ring buffer + CSV export | could add per-(strategy × regime) attribution dimensions |
| `BarrierGate.hpp` | classification gate | possibly missing some FoxML thresholds |
| `OverfitDetection.hpp` | 4 sequential checks | could expand to v5.7-style SHALT codes for visibility |
| `Backtest_RunFullValidation` | single held-out fold | extend to N-held-out for robustness |

### What's missing for cross-sectional (DEFERRED — v6.x)

| # | Capability | Notes |
|---|---|---|
| CS-1 | Cross-sectional ranking primitives | ranking objective in XGBoost training |
| CS-2 | Per-symbol rolling stats | architecturally requires v6.0 multi-symbol producer |
| CS-3 | Inter-symbol correlation matrix | needs multi-stream tick data |
| CS-4 | Bayesian decision policy | becomes load-bearing for CS regime decisions |
| CS-5 | CS feature engineering | rank-features across symbols |
| CS-6 | Multi-horizon blending | combine 1m/5m/15m predictions |

All deferred until multi-symbol data stream exists.

---

## Revised v5.8 plan — single-symbol ML hardening

Original plan estimated ~57-67h. After audit, real scope:

**ACTIVE** (real gaps to fix):

1. **v5.8.0 — Feature standardization** (6h)
   - Persist per-feature mean/std in stamp body
   - Apply at inference time before `Model_Predict`
   - MODEL_FORMAT_VERSION bump
   - Closes silent train-serve scale drift

2. **v5.8.1 — Feature registry** (5h)
   - `ML_Headers/FeatureRegistry.hpp` with named feature list + version
   - Compile-time hash → contributes to fingerprint
   - Stamp body's fingerprint mismatches if features change

3. **v5.8.2 — Leakage sentinels** (8-10h)
   - `Backtest/LeakageSentinels.hpp`
   - `Sentinel_FutureLeak`, `Sentinel_TargetCorrelation`, `Sentinel_LookAheadFold`, `Sentinel_WindowStraddle`
   - Wire into `Backtest_RunFullValidation` — refuses to stamp on failure

4. **v5.8.3 — Walk-forward stability metric** (2h)
   - Extend `WalkForwardResults` with `metric_stddev_across_folds`
   - Refuse-to-stamp threshold via cfg.wf_max_stability_stddev
   - Quick win on top of existing WF

5. **v5.8.4 — Determinism mode for backtest** (8-10h)
   - `cfg.deterministic_backtest = 1`
   - Single-threaded pthread + canonical-JSON output ordering
   - Verification harness: same input → byte-identical output

6. **v5.8.5 — Postmortem doc + CHANGELOG**

**DEFERRED** (future ships, only if needed):

- v5.8.6 — multi-horizon training + arbiter (only if multi-horizon ever wanted)
- v5.8.7 — calibration / temperature scaling (only if multi-horizon lands)
- v5.8.8 — GateControlNetwork.hpp completion (only if you figure out what it should do)

**REVISED TOTAL:** ~30-35h of real work for v5.8. Not 57-67h.

That's a single 1-week sprint, not a month.

---

## What you should actually do right now

The audit shows the trader is much more complete than I sized. Three
options for "what's most valuable":

### Option A — close the top 3 silent-bug-class gaps (~25h)

Ship v5.8.0 (feature standardization) + v5.8.1 (feature registry) +
v5.8.2 (leakage sentinels). These close real silent bugs that
would surface as "model behaved differently in live than in
backtest" weeks/months from now. After this lands you can archive
FoxML cleanly.

**Recommendation: Option A.** Highest value-per-hour. The trader
already has training + WF + held-out + auto-stamp. The missing 25h
is the hardening layer that catches silent ML drift before
deployment, not the headline functionality.

### Option B — close FoxML dependency only (~8h)

Audit `BacktestEngine.hpp`'s training path against FoxML's
`TRAINING/train.py`. If they produce equivalent models from
equivalent data, archive FoxML as-is. No new code.

**Risk:** something subtle in FoxML's training (hyperparameter
default? class-weight handling? feature ordering?) might differ.
You'd find out the hard way.

### Option C — paper-validate v5.6/v5.7 first

Before any new ship, run the v5.6/v5.7 work in paper for a few
hours. Verify the diagnostic readouts work as designed. Merge
`feat/v5.6-display-visibility` to main once paper passes. Then
start Option A.

**Recommendation:** Option C → Option A. Verify the previous
sprint shipped before starting the next sprint. The 30 minutes
of paper validation is cheap insurance.

---

## Trigger conditions to revisit deferred work

- **Want to add cross-sectional later** → reactivate v6.0+ master
  plan (`2026-05-01-MASTER-foxml-absorption.md`)
- **Find that single-horizon predictions are missing alpha** →
  reactivate v5.8.6 (multi-horizon)
- **Audit/compliance conversation** → ship v5.8.4 (determinism)
  earlier in the order
- **GateControlNetwork.hpp idea crystallizes** → ship v5.8.8

---

## Updated effort summary

```
COMPLETED (already in trader):
  XGBoost training pipeline ............ Backtest/BacktestEngine.hpp
  Walk-forward CV multi-fold ........... Backtest_RunWalkForward
  Held-out gate + auto-stamp ........... Backtest_RunFullValidation
  Class-imbalance weights .............. XGBoost_ComputeScalePosWeight
  Multi-class weights .................. XGBoost_ComputeMulticlassWeights
  Overfit detection (4 thresholds) ..... Backtest/OverfitDetection.hpp
  HMAC-signed stamps ................... ModelInference.hpp + HmacSha256.hpp
  Data fingerprinting .................. Backtest/Fingerprint.hpp
  Reward tracker ....................... ML_Headers/RewardTracker.hpp
  Bandit learning ...................... ML_Headers/BanditLearning.hpp
  Confidence scoring ................... ML_Headers/ConfidenceScore.hpp
  Parameter sweep ...................... Backtest_RunSweep
  Multi-model zoo ...................... CoreModelZoo.hpp

REAL v5.8 GAPS (~30h work):
  Feature standardization (persisted) .. 6h
  Feature registry ..................... 5h
  Leakage sentinels .................... 8-10h
  WF stability metric .................. 2h
  Determinism mode ..................... 8-10h

DEFERRED (post-v5.8 if ever):
  Multi-horizon arbiter ................ 16h
  Calibration / temperature ............ 4h
  GateControlNetwork completion ........ unknown
  Cross-sectional everything ........... v6.x master plan

ARCHIVED FoxML capabilities NOT being ported:
  Python web Dashboard ................. native imgui already
  IBKR/Alpaca brokers .................. abstract later
  CS ranking on equities ............... wrong scale (Binance crypto != 5000 stocks)
  mkdocs / sphinx ...................... DOCS/*.md is fine
  Bayesian Beta/Bernoulli framework .... too academic for HFT cadence
```

The trader did not need ~70 hours of ML porting. It needs ~30 hours
of hardening on top of an ML pipeline that's already shipping.
