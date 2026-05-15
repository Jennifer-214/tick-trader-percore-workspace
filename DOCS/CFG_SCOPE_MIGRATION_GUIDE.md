# Engine.cfg migration guide — v5.15.5.F.4c.3 architectural split

**Date:** 2026-05-15 (drafted alongside `.F.4c.3` plan)
**Ship:** `v5.15.5.F.4c.3` (architectural cfg split — global vs per-core registry)
**Status:** OPERATOR-FACING migration material (stub at draft; finalize content at `.F.4c.3` Step 8)

---

## What's changing

`v5.15.5.F.4c.3` splits `engine.cfg` into two scopes:
- **Global section** (top of file; no header) — system / training / recording / engine-wide mode / acknowledgments
- **Per-core sections** (`[core N]` headers) — strategy / trading / ML / risk / regime / entry / exit (each core's cfg is authoritative; no inheritance from global)

The previous "global default + per-core override" pattern is FORBIDDEN structurally. Each core sets ITS OWN trading parameters in its `[core N]` section. There's no inheritance fallback.

**Per Caramel's directive 2026-05-15: HARD BREAK of legacy cfg syntax.** No backward-compat shim. Operator rewrites `engine.cfg` once per this guide.

---

## Why this matters

- Each core's trading config is fully self-contained + visible in one section
- Per-core asymmetric tuning becomes first-class (kill switches per core, ML hyperparameters per core, etc.)
- "Did I miss exposing this knob?" failure mode (Class 24) dies structurally — every per-core knob is in the per-core registry by discipline
- Future axes (per-symbol, per-strategy, per-horizon) compose cleanly on the same shape

---

## How to migrate

### Step 1 — Back up your current `engine.cfg`

```bash
cp engine.cfg engine.cfg.pre-v5.15.5.F.4c.3.bak
```

### Step 2 — Identify global vs per-core knobs

Use the field classification table below. For each line in your current `engine.cfg`:

- If the key is in the **Global** list → keep at top of new file
- If the key is in the **Per-core** list → move under the appropriate `[core N]` section
- If the key has `core_N_` prefix → strip prefix, place under matching `[core N]` section

### Step 3 — Rewrite engine.cfg in new sectioned format

```
# Global section — system / training / engine-wide mode / acknowledgments
num_execution_cores=4
engine_mode=sharded
engine_arch=per_core_slow
require_mlockall=1
init_arena_use_hugepages=0
trading_mode=paper
model_verify_strict=-1
reconcile_mode=1
record_ticks=0
record_depth=0
xgb_train_nthread=4
xgb_seed=42
held_out_stamp_secret=secrets/held_out.key
held_out_gate_strict=0
# ... etc.

# Per-core sections
[core 0]
strategy=ml
model_dir=models/classification/multi_2year_01
risk_pct=15.0
take_profit_pct=3.0
stop_loss_pct=1.5
ridge_lambda=0.15
ridge_cost_penalty=0.5
ridge_min_ic_floor=0.001
confidence_freshness_tau_secs=3600.0
bandit_algorithm=1
kill_switch_daily_loss_pct=3.0
kill_switch_drawdown_pct=5.0
max_drawdown_pct=20.0
# ... etc.

[core 1]
strategy=ml
model_dir=models/classification/short_horizon
risk_pct=10.0
take_profit_pct=2.5
stop_loss_pct=1.0
ridge_lambda=0.20
bandit_algorithm=2
kill_switch_drawdown_pct=3.0
# ... etc.

# [core 2], [core 3] similarly
```

### Step 4 — Verify cfg loads + Settings panel populates

```bash
./build.sh test gui
./bin/engine_gui  # check Settings panel; each per-core tab shows its full cfg
```

If cfg fails to load, the error messages name the offending key + suggested scope. Example:
```
[cfg] ERROR: key 'take_profit_pct' is not valid at scope 'global'.
       It moved to 'per-core' scope at v5.15.5.F.4c.3.
       Place under the appropriate [core N] section header.
       See workspace/DOCS/CFG_SCOPE_MIGRATION_GUIDE.md for migration steps.
```

### Step 5 — Paper-trade 60 seconds

```bash
./bin/engine_gui  # verify no errors; per-core panel shows each core's actual cfg
```

---

## Global vs Per-core field classification

### Global fields (~25-30)

**System / Boot**
- `num_execution_cores`
- `engine_mode` (sharded / single_core)
- `engine_arch` (per_core_slow / centralized)
- `require_mlockall`
- `init_arena_use_hugepages`
- `slow_path_max_secs`
- `slow_path_pin_offset`
- `sharded_force_synthetic`

**Training (training-time only; outside trading loop)**
- `xgb_train_nthread`, `xgb_eval_nthread`, `csv_load_workers`, `multi_horizon_max_threads`
- `xgb_subsample`, `xgb_colsample_bytree`, `xgb_min_child_weight`, `xgb_seed`, `xgb_tree_method`
- `feature_collect_max_gb`, `wf_split_max_gb`, `held_out_max_gb`
- `auto_stamp_on_held_out`
- `held_out_stamp_secret`, `held_out_gate_strict`

**Recording (file I/O policy; uniform across engine)**
- `record_ticks`, `record_depth`, `record_max_days`

**Engine-wide mode / lifecycle**
- `trading_mode` (paper / shadow / live — uniform across engine for safety)
- `model_verify_strict`
- `reconcile_mode`
- `oms_event_log_mode`, `oms_bench_enabled`
- `use_aot_inference`
- `pay_fees_in_bnb`

**Acknowledgments (engine-wide opt-in gates)**
- `acknowledge_hardcoded_strategy_in_live`
- `acknowledge_hot_swap_with_open_positions`
- `allow_cross_major_engine`

### Per-core fields (~75-80, including kill switches + risk envelopes)

**Strategy + Model**
- `strategy`
- `model_path`, `model_dir`
- `horizon_list`, `ensemble_blend_mode`, `disabled_horizons`

**Trading**
- `risk_pct`
- `take_profit_pct`, `stop_loss_pct`
- `fee_rate`, `fee_rate_maker`, `fee_rate_taker`, `fee_floor_mult`
- `slippage_pct`

**Entry filters**
- `entry_offset_pct`, `offset_min`, `offset_max`
- `volume_multiplier`, `spacing_multiplier`
- `min_long_slope`, `min_buy_delta`
- `vwap_offset`, `min_stddev_pct`

**Regime detection**
- `regime_slope_threshold`, `regime_crossover_threshold`
- `regime_strong_crossover`, `regime_r2_threshold`
- `regime_hysteresis`

**ML / Bandit / Confidence / Ridge / Winsor / Thompson**
- `ml_buy_threshold`, `ml_tp_pct`, `ml_sl_pct`
- `bandit_algorithm`, `bandit_blend_ratio`
- `thompson_mu_prior`, `thompson_precision_prior`, `thompson_precision_obs`
- `ridge_lambda`, `ridge_cost_penalty`, `ridge_min_ic_floor`
- `winsor_pct_low`, `winsor_pct_high`
- `confidence_freshness_tau_secs`, `confidence_capacity_target_dollars`
- `confidence_capacity_kappa`, `confidence_rmse_baseline`, `confidence_threshold_scale`
- `barrier_blend_mode`
- `exit_threshold`, `exit_bandit_lr`, `exit_signal_model_dir`

**Risk envelope (per-core; previously global per Caramel 2026-05-15)**
- `kill_switch_daily_loss_pct`
- `kill_switch_drawdown_pct`
- `max_drawdown_pct`
- `max_exposure_pct`
- `enable_mtm_kill_switch`

**Exits / Holds**
- `tp_hold_score`, `tp_trail_mult`, `sl_trail_mult`
- `partial_exit_pct`, `tp2_mult`, `breakeven_buffer_pct`
- Gate recovery: `sl_cooldown_*`, `recovery_delay_secs`

**Strategy-specific (per-core)**
- `momentum_min_tp_margin_pct`, `momentum_min_r2`, `momentum_tp_mult`, `momentum_sl_mult`, `momentum_breakout_mult`, `momentum_require_last_win`
- `simpledip_tp_pct`, `simpledip_sl_pct`
- `mr_tp_pct`, `mr_sl_pct`
- `emacross_tp_pct`, `emacross_sl_pct`, `emacross_dip_mult`, `emacross_crossover_min`, `emacross_trail_mult`

**Cfg flag bits** (former `ml_cfg_flags` bitmap bits — now flat KIND_BOOL per-core rows per A2 hybrid migration)
- `ridge_within_horizon`, `ridge_across_horizons`
- `confidence_composite_enabled`, `confidence_enabled`
- `bandit_enabled`, `exit_bandit_enabled`
- `per_horizon_barrier_blend`
- `foxml_vol_scaling_enabled`, `lazy_rebuild_enabled`, `use_exit_model`
- (Plus equivalents from `lifecycle_cfg_flags`, `gate_cfg_flags`, `risk_cfg_flags`, `ops_cfg_flags` bitmaps under F6 extension)

### Stays manual at `.F.4c.3` (defer to `.F.4e` with KIND_STRING infra)

- `symbol` — defer to `.F.4c.3.A` follow-up subplan after `.F.4e` ships
- `core_horizon_list[]`, `core_ensemble_blend_mode[]`, `core_disabled_horizons[]` — string per-core overrides; migrate at `.F.4e`

---

## Validation steps

After rewriting `engine.cfg`:

1. **Cfg loads** — engine starts without parser errors. Any errors name the offending key + suggested scope.
2. **Settings panel populates** — open `engine_gui`; Global tab shows ~25-30 rows; each per-core tab (Engine 0 / Engine 1 / ...) shows ~75-80 rows.
3. **Paper-trade 60 seconds** — engine runs without crashing; no NaN feature events; no missing-field warnings.
4. **Round-trip persistence** — change a value in Settings panel → restart engine → verify the change persisted in `engine.cfg`.
5. **Per-core asymmetry verified** — set different `take_profit_pct` per core; verify each core uses its own value (check ML status panel or per-core trade log).

---

## Common migration errors + fixes

| Error message | Cause | Fix |
|---|---|---|
| `key 'take_profit_pct' is not valid at scope 'global'` | Trading key at top of file | Move under `[core 0]` (and other cores as needed) |
| `key 'num_execution_cores' is not valid at scope 'per-core'` | Global key inside `[core N]` section | Move to top of file before any section header |
| `section [core 0] already defined` | Two `[core 0]` sections | Merge into one; ensure each `[core N]` appears once |
| `[core 5] cfg present but engine runs 4 cores; ignoring` | Section index >= num_execution_cores | Either remove the section OR bump `num_execution_cores` |
| `unknown axis 'foo'` | Typo in section header (e.g., `[cor 0]`) | Fix axis name; only `[core N]` is supported at `.F.4c.3` |

---

## Stamp + drift implications

Each core's HMAC stamp now covers ITS per-core cfg (not a global cfg). At boot:
- Per-core stamp file: `<core_N_model_dir>/cfg-core-<N>.stamp` (filename includes core idx to disambiguate when multiple cores share model_dir)
- Drift check fires per core; per-core drift status published to model-health panel
- v5.14-era stamps DO NOT load (`cfg_scope_split_version` field missing → explicit ERROR; operator retrains models post-`.F.4c.3`)

---

## If you get stuck

- Read this guide top-to-bottom; the field classification list is the authoritative reference
- Check the example `engine.cfg.example` (4-core sample) shipped with `.F.4c.3`
- The plan + DESIGN_SPECs are at:
  - `plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3-global-vs-per-core-registry-split.md`
  - `DESIGN_SPECS/cfg-scope-discipline.md` (the discipline doc with categorical rationale)
  - `DESIGN_SPECS/per-instance-registry-pattern.md` (the framework pattern)
  - `DESIGN_SPECS/cfg-section-parser-state-machine.md` (the parser implementation)

---

**End of migration guide stub.** Finalize content (with concrete classification from Step 0.C audit) at `.F.4c.3` Step 8.
