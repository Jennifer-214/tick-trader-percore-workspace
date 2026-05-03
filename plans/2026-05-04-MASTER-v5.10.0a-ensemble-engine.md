# Master Plan — v5.10.0a Ensemble Engine Wiring (G.5 → G.10)

**Date:** 2026-05-04
**Branch:** `feat/v5.10-foundation` (continuation from v5.10.0a-bugfix2)
**Predecessor:** `v5.10.0a-bugfix2` (in-panel horizons CSV editor)
**Effort estimate:** ~15-18h across G.5-G.10 (post-perf-fold; was
12-14h pre-fold; +3-5h for 5 perf optimizations folded into G.5/G.7/
G.8/G.9). Optional G.11 (A/B compare): +2-3h → ~18-21h total. 2-3
focused sessions.
**Hot path:** UNTOUCHED (dispatch is slow-path; no per-tick changes)

## Theme

v5.10.0a shipped the multi-horizon TRAINING pipeline (G.1) + the
INFERENCE DISPATCH HELPER (G.4), but did NOT wire the engine boot to
populate `state->ml_strategy.ensemble_zoo`. Operators training N
horizons today get N model files on disk; live engine still loads
ONE. This plan completes the wiring + adds Bandit-Exp3-driven
weighted blend that's regime-aware and learns from real outcomes.

## ⚠️ LATENCY CAVEAT (operator-visible)

**Multi-horizon ensemble inference is INTRINSICALLY SLOWER than
single-model deployment** because every slow-path predict runs N
booster predictions instead of 1. Concrete numbers (XGBoost 3.3.0,
typical 64-feature model):
- Single-model predict: ~2-5 µs per slow-path
- Ensemble N=3 predict: ~6-15 µs per slow-path (3× linear)
- Ensemble N=8 predict: ~16-40 µs per slow-path (8× linear)

This is in the **slow-path** (per `cfg.poll_interval`, default 100
ticks), NOT the hot path. Hot path BG_Evaluate / SG_Evaluate stays
at 40-400ns p99 regardless. So absolute numbers are still fast in
context — slow-path runs ~1% as often as hot-path; an 8-horizon
ensemble adds ~30µs every ~100 ticks vs ~3µs for single-model.

Item A's phase timer (v5.10.0) captures this: operator can read
`feature_collect_ns` (per slow-path predict cost) post-deployment.
Recommended: check the timer on a 10-min live session before
ramping; if predict_ns > 1ms per slow-path, consider reducing N
or the horizon ranges.

**Mitigation in this plan (G.7 §"Per-horizon prediction caching"):**
all N models train on identical features → standardize features ONCE
at slow-path start, reuse the standardized buffer for all N predicts.
Saves N-1 `FeatureStandardizer_Apply` + scaler-math calls. Reduces
N=8 ensemble cost from 8× scaler+predict to 8× predict + 1× scaler
(roughly 5-6× speedup on the scaler portion).

## Online learning approach

Bandit-Exp3 (exponential-weight algorithm for arm selection under
adversarial bandit feedback). Industry-standard for multi-armed
bandits with reward feedback after action. Each horizon = one arm.

**Why Bandit-Exp3 specifically:**
- No prior knowledge required (warmup with uniform weights; converges
  from data)
- Robust to non-stationary rewards (regimes shift; markets evolve)
- Learning rate (`eta`) tunable: smaller = more cautious, larger =
  faster adaptation
- Theoretically bounded regret (Auer et al. 2002)

**Reward signal sources (G.8):**
1. **Slow-path lookback (DENSE):** every poll_interval, look back
   `label_forward_ticks` ago; reward each arm based on prediction-vs-
   actual-price-move correctness. Hypothetical signal; converges fast.
2. **Trade-close (SPARSE, HIGH-FIDELITY):** when a position closes,
   reward arms based on REALIZED P&L direction. Real money signal;
   includes fees + slippage; weighted ×4 by default.

**Convergence expectations:**
- Cold start (uniform weights): ~500-1000 predictions per regime to
  start showing weight differentiation
- Warm start (G.5 reads per-regime val_acc priors from stamp body):
  ~50-100 predictions per regime
- Regime transition: weights re-learn for that regime; existing
  hysteresis prevents thrash (G.7 § "Bandit weight dampening")

**Operator workflow target:**
1. Train Multi-Horizon → N models saved to per-horizon dirs
2. Deploy: set `core_N_model_dir=<base_run_dir>` (no `_horizon_<H>` suffix)
3. Engine boot auto-detects N horizons from disk via stamp metadata
4. Per-tick: classify regime → blend N predictions weighted by per-regime bandit
5. Weights learn from dual-source rewards (slow-path lookback + trade-close)
6. State persists across restarts (`bandit_state.json` per core)

## Architectural design

### Per-regime bandit weights (matrix structure)
```
EnsembleModelZoo
├── ModelHandle barrier[N] / regime[N] / exit[N] / buy_signal[N]
├── BanditState bandits[NUM_REGIMES]   // one per regime: RANGING/TRENDING/VOLATILE/TRENDING_DOWN/MILD_TREND (NUM_REGIMES=5 per StrategyInterface.hpp FOREACH_REGIME X-macro)
│   └── weights[N_arms]      // learned weights over horizons within this regime
├── int last_predicted_horizon_idx     // for reward attribution
├── int last_predicted_regime_id       // which bandit gets the reward
└── ... other ensemble fields
```

### Auto-detection from stamps
Engine boot scans `<core_N_model_dir>_horizon_*/` siblings.
For each: verify_model_stamp → if `has_grid_member_count=1` and counts
match → add to ensemble at `grid_member_idx` slot. Operator sets ONE
cfg path; engine discovers structure.

### Dual-source rewards
- **Slow-path lookback (dense):** every poll_interval ticks, look back
  `label_forward_ticks` ago, compute "would prediction-then have been
  right? what's price now vs sample_price?" Per-arm reward signal.
  Fast learning, hypothetical signal.
- **Trade-close (sparse, high-fidelity):** when trade closes (TP/SL),
  compare model's recommendation at entry-time vs realized P&L.
  Real money signal. Slow but corrects fee/slippage divergence.
- Both feed `Bandit_Update` per arm; weights compound.

### State persistence
Per-core `bandit_state.json` at `<core_N_model_dir>/bandit_state.json`:
```json
{
  "format_version": 1,
  "sha256_of_model_bundle": "<hex>",  // invalidates on model swap
  "regimes": {
    "RANGING":   { "weights": [0.18, 0.42, 0.25, 0.10, 0.05], "n_updates": 12340 },
    "TRENDING":  { "weights": [0.05, 0.10, 0.20, 0.30, 0.35], "n_updates": 8200 },
    "VOLATILE":  { ... },
    "MILD_TREND": { ... }
  },
  "global_n_updates": 32000,
  "last_save_ts_ns": 1234567890123
}
```

### Single-model backward compat (LOAD-BEARING)
Operators with `cfg.horizon_count == 0` AND no auto-detected horizon
siblings see ZERO behavior change:
- `EnsembleModelZoo.active = 0`
- `MLStrategy.ensemble_zoo = nullptr`
- `BuySignal` dispatches to `Model_Predict` on `state->buy_model` (existing)
- No bandit state allocated; no `bandit_state.json` written

This invariant must hold across every sub-ship below.

## Sub-ships

### v5.10.0a.G.5 — EnsembleModelZoo lifecycle + auto-detect from disk (~2-3h)
**Sub-plan:** `plans/2026-05-04-v5.10.0a-G.5-ensemble-lifecycle.md`
**Scope:**
- Per-core `EnsembleModelZoo<F>` allocated alongside `CoreModelZoo<F>` in
  `BacktestSharded_Run` + `EngineSharded_Run`
- Boot helper `EnsembleModelZoo_AutoDetectFromDir`: scans
  `<base_dir>_horizon_*` siblings, verifies stamps via existing
  `verify_model_stamp`, populates ensemble at correct member_idx slots
- Lifecycle: `_Init` per core, `_Free` at engine shutdown
- Wires `state->ml_strategy.ensemble_zoo = &core->ml_zoo_ensemble` post-
  `MLStrategy_Init` when `ensemble_zoo.active == 1`

**Tag:** `v5.10.0a.G.5`

### v5.10.0a.G.6 — Per-core cfg fields (~1h)
**Sub-plan:** `plans/2026-05-04-v5.10.0a-G.6-ensemble-cfg.md`
**Scope:**
- `core_N_ensemble_blend_mode` ("selection" / "weighted" / default
  "weighted" when ensemble active)
- `core_N_horizon_list` (CSV; falls back to global `horizon_list`)
- Globals: `ensemble_bandit_eta` (Exp3 learning rate; default 0.1),
  `ensemble_min_warmup_predictions` (default 100; weights uniform until
  this many updates per regime)
- `engine.cfg.example` documentation
- Per-core override pattern via `PER_CORE_OVERRIDE_FIELDS` X-macro
  (auto-extends per v5.8.1a registry pattern)

**Tag:** `v5.10.0a.G.6`

### v5.10.0a.G.7 — Per-regime BanditState integration (~3h)
**Sub-plan:** `plans/2026-05-04-v5.10.0a-G.7-bandit-blend.md`
**Scope:**
- `EnsembleModelZoo` extension: `BanditState bandits[NUM_REGIMES]`
  (NUM_REGIMES = 5 per FOREACH_REGIME X-macro at `Strategies/StrategyInterface.hpp:181`: RANGING/TRENDING/VOLATILE/TRENDING_DOWN/MILD_TREND. Auto-counted via X-macro; if operator adds a regime later, NUM_REGIMES auto-bumps and ensemble code adapts.)
- `EnsembleModelZoo_InitBandits` initializes uniform weights per regime
- Per-tick blend dispatch: `MLStrategy_BuySignal` reads current regime
  classification → calls `Model_Predict_Ensemble_Weighted` with
  `bandits[regime_id]` weights instead of selection logic
- `Model_Predict_Ensemble_Weighted` helper extends G.4's
  `Model_Predict_Ensemble`:
  ```cpp
  float Model_Predict_Ensemble_Weighted(
      ModelHandle<F>* models, int count,
      const float* features, int num_features,
      const double* weights,           // from BanditState
      int* out_selected_idx);          // for display: which horizon dominated
  ```
- Determinism: same features + same weights = same blend output bytewise
- Mode dispatch: cfg.ensemble_blend_mode controls "selection" (G.4 path)
  vs "weighted" (G.7 path)

**Tag:** `v5.10.0a.G.7`

### v5.10.0a.G.8 — Dual-source reward wiring (~3h)
**Sub-plan:** `plans/2026-05-04-v5.10.0a-G.8-rewards.md`
**Scope:**
- **Slow-path lookback rewards:** every slow-path tick, walk a ring
  buffer of recent (sample_price, predictions[N], regime, tick_index)
  records. For records where `current_tick - record_tick >=
  label_forward_ticks`: compute reward per arm (1 if prediction
  direction matched price move, 0 else); call `Bandit_Update` per arm
  on the matching regime's bandit.
  - Ring buffer size: `label_forward_ticks / poll_interval + slack`
    (typically 10-20 entries per core)
- **Trade-close rewards:** post-fill drainer hooks. When a position
  closes (TP/SL exit), look up the entry-time prediction record,
  compute realized-P&L sign vs prediction direction; `Bandit_Update`
  with HIGHER WEIGHT than slow-path (real money signal).
  - Reward weight ratio configurable: `ensemble_trade_reward_mult`
    (default 4.0; trade reward = 4 × slow-path reward)
- Reward attribution: each prediction record stores `last_predicted_regime_id`
  + `predictions[N]` so post-hoc reward can be attributed correctly
  even if regime drifted in the meantime.

**Tag:** `v5.10.0a.G.8`

### v5.10.0a.G.9 — Bandit state persistence (~1-2h)
**Sub-plan:** `plans/2026-05-04-v5.10.0a-G.9-persistence.md`
**Scope:**
- Format: JSON at `<base_run_dir>/bandit_state.json` (atomic write via
  rename pattern, like stamps)
- Save triggers:
  - Every N updates (`ensemble_bandit_save_interval`; default 5000)
  - At engine clean shutdown (signal handler / Ctrl-C)
  - On Save Run (foxml_suite Save Run button copies bandit state too)
- Load trigger: at engine boot, after `EnsembleModelZoo_AutoDetectFromDir`
- Validation:
  - `format_version` matches expected
  - `sha256_of_model_bundle` matches concatenated SHAs of loaded N
    model files (invalidates if operator retrained but didn't regen
    bandit_state)
- Backward-compat: missing `bandit_state.json` → uniform weights;
  warn-only at boot
- Backtest integration: `BacktestRunConfig.bandit_state_path` (optional)
  loads as prior at backtest start; backtest exports its own
  bandit_state at end (closes the train-serve loop)

**Tag:** `v5.10.0a.G.9`

### v5.10.0a.G.10 — ML Status panel ensemble visualization (~2h)
**Sub-plan:** `plans/2026-05-04-v5.10.0a-G.10-ml-status.md`
**Scope:**
- New section in `GUI/MLStatusPanel.hpp`: "Ensemble (multi-horizon)"
- Renders only when `ensemble_zoo.active == 1`
- Heatmap: regimes × horizons (4 × N grid). Cell color = current bandit
  weight (green=high, yellow=medium, red=low/disabled)
- Per-horizon stats: cumulative predictions, n_correct, IC running
  average
- Live event stream: last 10 reward events (regime / horizon_idx /
  reward / source [slow-path|trade-close])
- "Persist Now" button: triggers immediate `bandit_state.json` save
- "Reset Weights" button (cfg-gated `ensemble_allow_manual_reset`):
  uniform-init all regime bandits — operator escape hatch when weights
  diverge

**Tag:** `v5.10.0a.G.10`

### v5.10.0a.G.11 — A/B compare mode (optional ship; ~2-3h)
**Sub-plan:** `plans/2026-05-04-v5.10.0a-G.11-ab-compare.md`
**Scope:** Inference-time A/B comparison. When
`cfg.ensemble_ab_compare_with_single_model_path` is set, engine runs
BOTH ensemble + single-model predict per slow-path. Logs which
would-have-been-better on each closed trade. Builds operator
confidence in the ensemble before full cutover.

**Deferred-or-shipped decision:** ship as v5.10.0a.G.11 only if
operator wants validation tooling; otherwise capture as v5.10.0a.next
item. Not load-bearing for ensemble feature itself.

**Tag:** `v5.10.0a.G.11`

### v5.10.0a final close (after G.5-G.10, optional G.11)
- Bump `Version.hpp` 5.10.0a → 5.10.0b? Probably no — G.5-G.10 are
  natural continuation of v5.10.0a (the multi-horizon FEATURE).
  Final tag: `v5.10.0a-final` (mirrors v5.9.5j-final pattern) once all
  6 sub-ships green + operator-validated.
- Master plan Sprint B 2/6 → still 2/6 (v5.10.0a remains; just feature-
  complete now)
- v5.10-design-notes Idea #1 (parallel hyperparam search) + Idea #4
  (multi-horizon prediction) marked SHIPPED with v5.10.0a-final.

## Integration Matrix

### Files touched per sub-ship

| File | G.5 | G.6 | G.7 | G.8 | G.9 | G.10 |
|---|---|---|---|---|---|---|
| `ML_Headers/CoreModelZoo.hpp` | ✓ AutoDetectFromDir + lifecycle | — | ✓ BanditState fields | ✓ ring buffer | ✓ load/save | — |
| `ML_Headers/ModelInference.hpp` | — | — | ✓ _Weighted helper | — | — | — |
| `ML_Headers/BanditLearning.hpp` | — | — | (use existing) | (use existing) | ✓ JSON serialize | — |
| `Strategies/MLStrategy.hpp` | ✓ ensemble_zoo wiring | — | ✓ blend dispatch | ✓ reward feed | — | — |
| `CoreFrameworks/EngineSharded.hpp` | ✓ per-core lifecycle | — | — | ✓ trade-close hook | ✓ shutdown save | — |
| `Backtest/BacktestSharded.hpp` | ✓ per-core lifecycle | — | — | ✓ trade-close hook | ✓ load prior | — |
| `CoreFrameworks/ControllerConfig.hpp` | — | ✓ +5 cfg fields | — | ✓ +1 reward_mult | ✓ +1 save_interval | — |
| `engine.cfg.example` | — | ✓ documented | — | ✓ documented | ✓ documented | — |
| `GUI/MLStatusPanel.hpp` | — | — | — | — | — | ✓ ensemble section |
| `tests/controller_test.cpp` | ✓ +6 tests | ✓ +6 tests | ✓ +5 tests | ✓ +6 tests | ✓ +5 tests | — |

**File-touch density:**
- `MLStrategy.hpp`: G.5 + G.7 + G.8 (3 ships) → tightly-coupled changes; ship sequentially not in parallel
- `EngineSharded.hpp` + `BacktestSharded.hpp`: G.5 + G.8 + G.9 (3 ships) → same constraint
- `BanditLearning.hpp`: G.7 + G.8 + G.9 use existing surface; G.9 adds JSON serializer

### Cfg field additions

| Field | Added by | Type | Default |
|---|---|---|---|
| `core_N_horizon_list` | G.6 | string (CSV) | "" (fallback to global horizon_list) |
| `core_N_ensemble_blend_mode` | G.6 | string | "weighted" (when ensemble active; "selection" available) |
| `ensemble_bandit_eta` | G.6 | float | 0.1 |
| `ensemble_min_warmup_predictions` | G.6 | int | 100 |
| `ensemble_trade_reward_mult` | G.8 | float | 4.0 |
| `ensemble_bandit_save_interval` | G.9 | int | 5000 |
| `ensemble_allow_manual_reset` | G.10 | int | 0 (operator opts in) |

### Stamp body additions
**None** (G.2's `grid_member_count` + `grid_member_idx` already cover
the ensemble metadata; G.5-G.10 don't extend the stamp body).

### Architectural invariants (every sub-ship preserves)

| Invariant | Verification |
|---|---|
| Single-model deployment bytewise unchanged | Operator with `horizon_count=0` cfg sees zero behavior change; integration test verifies bytewise determinism |
| Hot path UNTOUCHED | All ensemble work in slow-path / boot / shutdown only |
| Backward-compat: missing `bandit_state.json` | Uniform weights warn-only; G.9 explicitly tests missing-file load |
| Stamp body forward-compat | G.5 reads has_grid_member_count for auto-detect; legacy stamps load fine via single-zoo path |
| Bandit determinism (within build) | Same features + same weights → same blend bytewise; G.7 has explicit test |
| Reward attribution correctness | Prediction record stores regime_id at predict-time; G.8 test verifies reward goes to correct bandit even if regime drifted |
| Train-serve parity | Backtest can replay live bandit state via G.9 prior load; same blend logic both sides |

### Test count progression

| Sub-ship | New tests | Cumulative |
|---|---|---|
| 1403 (v5.10.0a-bugfix2 baseline) | — | 1403 |
| G.5 | +6 | ~1409 |
| G.6 | +6 | ~1415 |
| G.7 | +5 | ~1420 |
| G.8 | +6 | ~1426 |
| G.9 | +5 | ~1431 |
| G.10 | +0 (UI; smoke-test post-tag) | ~1431 |

## Performance optimizations (folded across G.5-G.10)

Six optimizations identified by /plan-check 2026-05-04; each fold
into the appropriate sub-ship rather than separate ships:

| # | Optimization | Sub-ship | Win | Effort |
|---|---|---|---|---|
| 1 | Per-horizon prediction caching (single feature pack + scaler apply, reuse N predicts) | G.7 | ~5-6× speedup on scaler portion at N=8 | +30 min in G.7 |
| 2 | Per-regime warmup priors from stamp body (val_acc per regime) | G.5 reader; **trainer-side deferred to v5.10.0a.next** (G.1 + G.2 already shipped; would need retraining all multi-horizon models) | ~10× faster convergence (50 vs 500 predictions/regime) | +30 min G.5 reader; v5.10.0a.next sub-ship for trainer |
| 3 | Per-horizon drift watchdog (IC tank → fast weight demotion) | G.8 | Operator escape from a degenerated horizon without manual intervention | +1h in G.8 |
| 4 | A/B comparison mode (parallel ensemble + single-model) | G.11 (optional) | High diagnostic value; operator confidence pre-ramp | +2-3h G.11 (separate ship) |
| 5 | Bandit weight dampening on regime hysteresis | G.7 | Smoother transitions; reduces single-tick weight thrash | +30 min in G.7 |
| 6 | Backtest replay-determinism explicit test | G.9 | Catches non-determinism regressions in ensemble dispatch | +30 min test in G.9 |

**Total perf-fold overhead:** ~3-5h additional across G.5/G.7/G.8/G.9
+ G.11 as separate optional ship.

**v5.10.0a.next backlog (deferred items, captured as future sub-ships):**

- **v5.10.0a.next.1 — Trainer-side per-regime val_acc stamping (~2-3h).**
  Extends G.1 worker to compute per-fold per-regime accuracy +
  emits new stamp body fields (`has_per_regime_val_acc` + per-regime
  array at canonical position 21, after v5.10.0d's position 20).
  G.5's reader (already defensive) picks up the priors automatically
  once trained models have the field. Forces retrain of multi-horizon
  models that want priors; old models still load with uniform
  warmup. Sub-plan to draft when operator decides to ship.

- **v5.10.0a.next.2 — Multi-asset isolated bandits (~3-4h).** Currently
  per-core; if operator runs BTCUSDT on cores 0-1 and ETHUSDT on
  cores 2-3, both share BTC's bandit weights when wrong. Per-symbol
  bandit isolation: cfg.core_N_symbol field + per-symbol bandit
  store. Becomes relevant once operator runs multi-asset.

- **v5.10.0a.next.3 — Auto-A/B-cutover (~2h).** Builds on G.11. When
  ensemble's win rate over single-model exceeds threshold for N
  days, auto-flip the deployment (single → ensemble). Operator-side
  guardrail; not load-bearing.

## Risk register

| Risk | Mitigation |
|---|---|
| Per-regime bandit thrash (regime classifier flips frequently → weights average) | Use existing `regime_hysteresis` cfg (cycles before regime switch); test at typical hysteresis values; document interaction |
| Reward attribution race (regime changed between predict-time and reward-time) | Predict record stores regime_id at predict-time; reward goes to that bandit, not current. Test explicitly. |
| `bandit_state.json` corruption (concurrent write + crash) | Atomic write via fopen(tmp)+rename pattern. Matches stamp persistence. |
| Stale bandit weights vs new model bundle | Stored sha256_of_model_bundle in bandit_state.json; mismatch → reset to uniform with warn |
| Backtest replay-determinism breaks with bandit | Bandit updates are deterministic given same input sequence; replay should be bytewise-identical. Test explicitly. |
| Auto-detect on disk: ambiguous siblings (e.g. partial training half-saved) | G.5 verifies `has_grid_member_count` AND `grid_member_count` matches across all siblings; mismatched siblings logged + skipped |
| Operator deploys ensemble but uses ONE model accidentally (forgot horizon_list cfg) | G.5 boot WARN: "auto-detected N horizon siblings on disk but ensemble inactive (cfg.horizon_count=0); did you mean to enable ensemble?" |

## Operator-validation gates

After each sub-ship:
- **G.5:** boot log shows "[ensemble] auto-detected N horizons" when
  ensemble dirs exist; "ensemble inactive" when not. ML Status panel
  shows ensemble_zoo.active state.
- **G.6:** `core_0_ensemble_blend_mode=weighted` cfg parses + reaches
  G.7 dispatch.
- **G.7:** synthetic test data + uniform weights → blend output =
  unweighted average. With non-uniform weights → blend follows weights
  bytewise.
- **G.8:** simulate dense reward stream over 1000 ticks; bandit weights
  converge toward the highest-IC arm. Trade-close reward applies 4×
  multiplier.
- **G.9:** save → restart engine → weights restored bytewise. Mismatched
  model SHA → uniform reset with warn.
- **G.10:** ML Status panel renders heatmap; cells update live as
  rewards stream in; Persist Now button writes JSON.

## Updates this plan triggers

After each sub-ship:
- Update master plan Current State (sub-ship tally within v5.10.0a.G.x)
- Push branch + per-sub-tag (rollback granularity)
- Update `tests/INVARIANTS_MAP.md` if new ensemble invariants land

After v5.10.0a-final:
- `DOCS/CHANGELOG.md` row reflects all sub-ships
- `DOCS/v5.10-design-notes.md` mark Ideas #1 + #4 SHIPPED
- Master plan Sprint B remains 2/6 (v5.10.0a feature-complete; v5.10.0b
  starts next)

## Cross-references

- Existing master plan: `plans/2026-05-02-MASTER-v5.9-to-v5.10.md`
- v5.10.0a sub-plan: `plans/2026-05-03-v5.10.0a-grid-search-multihorizon.md`
- v5.10.0a-final tag (after G.5-G.10): closes the multi-horizon feature
- Predecessor for next plan: `v5.10.0a-final` → v5.10.0b FPN-e2e

## Per-sub-ship tag summary

```
v5.10.0a-bugfix2    — In-panel horizons CSV editor       [SHIPPED]
v5.10.0a.G.5        — EnsembleModelZoo lifecycle + auto-detect [PENDING]
v5.10.0a.G.6        — Per-core ensemble cfg fields            [PENDING]
v5.10.0a.G.7        — Per-regime BanditState + blend dispatch [PENDING]
v5.10.0a.G.8        — Dual-source reward wiring               [PENDING]
v5.10.0a.G.9        — Bandit state persistence                [PENDING]
v5.10.0a.G.10       — ML Status panel ensemble heatmap        [PENDING]
v5.10.0a-final      — Multi-horizon feature COMPLETE           [PENDING]
```

`git reset --hard <tag>` for surgical rollback at any granularity.
