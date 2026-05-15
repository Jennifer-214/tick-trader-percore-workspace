# Cfg field scope classification — v5.15.5.F.4c.3

**Date:** 2026-05-15
**Status:** **LOCKED 2026-05-15** — Caramel reviewed + greenlit all 7 borderline calls (matches initial classification recommendations).
**Source:** `CoreFrameworks/CfgFieldRegistry.hpp` FOREACH_CFG_FIELD at engine HEAD `88043ea` (v5.15.5.F.4c.1)
**Total rows in FOREACH_CFG_FIELD:** **129** (verified via `awk '/^#define FOREACH_CFG_FIELD/,/^$/' | grep -cE "^\s+X\("`)
**Plan estimate:** ~113-115 rows (off by ~14; doc estimate, not load-bearing)
**Final bucket counts:** 47 GLOBAL / 79 PER_CORE / 3 REMOVED.

---

## Classification summary

| Bucket | Count | Notes |
|---|---|---|
| **GLOBAL** | 47 | System / training / recording / engine-wide-mode / acknowledgments / notifications / logging / reconcile / CPU pinning |
| **PER_CORE** | 79 | Trading / strategy / entry / exit / ML / risk-gate / regime-detection / per-core kill switches |
| **REMOVED** | 3 | Deprecated rows: legacy single_core, operator-only, DEPRECATED flagged |
| **Total** | 129 | matches FOREACH_CFG_FIELD row count |

**Borderline calls (⚠️ flagged):** 7. These warrant Caramel's review — see § "Decisions surfaced" at bottom.

**Discrepancy with plan estimate:** Plan body said "~15-30 GLOBAL + ~70-80 PER_CORE." Actual is **47 GLOBAL + 79 PER_CORE**. The PER_CORE estimate was right; GLOBAL estimate was ~1.5× under. Reason: plan estimate ignored training-side (~9 xgb/csv rows) + health-log (~3 rows) + notify (~2 rows) + recording (~3 rows) which all belong in GLOBAL. No structural surprise — just honest count.

---

## Decisions surfaced for Caramel review (⚠️ borderline calls)

Each of these was an "either could be defended" judgment. My recommendation is in **bold**; the alternative is documented for your call.

| # | Field | My call | Alt | Tension |
|---|---|---|---|---|
| ⚠️1 | `fee_rate`, `slippage_pct`, `fee_floor_mult` | **PER_CORE** (per plan body locks "trading: fee_rate*, slippage_pct" → PER_CORE) | GLOBAL (exchange-config-level; operator sets once for all cores) | Plan body says PER_CORE explicitly; I locked PER_CORE. Flag for cohort-purity reconsideration: if you prefer "exchange config = GLOBAL even though it's in trading section," flip 3 rows. |
| ⚠️2 | `confidence_window` | **PER_CORE** | GLOBAL (today's behavior is engine-wide; tooltip says "Same window per ML core today") | PER_CORE forward-looks at per-core ConfidenceScorer divergence; GLOBAL preserves current behavior. PER_CORE costs ~32 per-core read-site migrations. |
| ⚠️3 | `confidence_ic_variant` | **PER_CORE** | GLOBAL (IC variant = uniform engine-wide ML pipeline choice) | PER_CORE allows per-core IC variants if A/B-testing IC methods. GLOBAL if uniform. |
| ⚠️4 | `risk_degradation_curve` (STAMP_BOUND ENUM) | **PER_CORE** | GLOBAL (uniform risk-philosophy across all cores) | PER_CORE matches "different cores warrant different risk envelopes" amendment direction. GLOBAL if curve shape is uniform engine-wide policy. |
| ⚠️5 | `model_max_age_hours` | **PER_CORE** | GLOBAL (engine-wide model freshness policy) | PER_CORE matches "each core loads its own model" — natural per-core gate. GLOBAL if model freshness is uniform engine policy. |
| ⚠️6 | `thompson_rng_seed` | **PER_CORE** | GLOBAL with derived offset | PER_CORE: each core's bandit needs distinct seeds for stochastic independence; explicit per-core seed = operator-readable. GLOBAL: cleaner; engine derives per-core seed = global ^ core_idx. |
| ⚠️7 | `max_positions` | **GLOBAL** | PER_CORE | Sharded architecture is "one position per core" — engine-wide MAX_EXECUTION_CORES limit already enforces this. Per-core max_positions would be 1 by construction. Keeping GLOBAL as engine policy. PER_CORE if you want per-core override (e.g., one core multi-leg). |

**Default classification bias:** when uncertain, I prefer GLOBAL to reduce per-core fixture migration cost. PER_CORE rows force ~414 test sites to set per-core explicitly; GLOBAL rows preserve test fixture simplicity. The PER_CORE wins where the plan body locked them or the operator-visible per-core divergence is concrete.

---

## GLOBAL bucket (47 rows)

### System / Operational (5)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `num_execution_cores` | KIND_INT | Operational | Number of cores itself — definitionally engine-wide. |
| `require_mlockall` | KIND_BOOL | Operational | OS memory pinning; engine-process-level. |
| `init_arena_use_hugepages` | KIND_BOOL | Operational | Hugepage TLB tuning; engine-process-level. |
| `sharded_force_synthetic` | KIND_BOOL | Operational | Debug/test toggle; engine-wide. |
| `slow_path_pin_offset` | KIND_INT | Operational | CPU pin discipline; engine-wide. |

### Engine timing / Slow-path discipline (5)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `poll_interval` | KIND_INT | Engine Timing | All cores share slow-path cadence by architecture. |
| `slow_path_max_secs` | KIND_INT | Engine Timing | Engine-wide timing budget. |
| `warmup_ticks` | KIND_INT | Engine Timing | Engine-wide warmup gate (raw tick count). |
| `min_warmup_samples` | KIND_INT | Engine Timing | Engine-wide rolling-stats warmup. |
| `lazy_rebuild_force_period_us` | KIND_INT | Performance | Slow-path force-rebuild cadence; engine-wide. |

### Hot-path discipline (1)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `param_max_age_ticks` | KIND_INT | Lifecycle | Hot-path staleness gate; engine-wide policy. |

### Risk / Position limits (2)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `max_positions` ⚠️7 | KIND_INT | Risk Management | Sharded architecture: 1 position per core enforced; engine-wide limit. |
| `recovery_delay_secs` | KIND_INT | Risk Management | Post-flatten engine-wide wait; flatten is engine event. |
| `ws_dead_time_flatten_threshold_secs` | KIND_INT | Risk Management | WS dead-time gate; engine-wide flatten trigger. |

(Note: `max_positions` is borderline #7; the others are clearly engine-wide.)

### Recording (3)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `record_ticks` | KIND_BOOL | Tick Recording | Engine-wide tick recorder. |
| `record_depth` | KIND_BOOL | Tick Recording | Engine-wide depth recorder. |
| `record_max_days` | KIND_INT | Tick Recording | Disk cap; engine-wide. |

### Training (9)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `xgb_min_child_weight` | KIND_INT | ML Hyperparams | Training-time XGBoost regularization. |
| `xgb_seed` | KIND_INT | ML Hyperparams | Training reproducibility seed. |
| `xgb_train_nthread` | KIND_INT | Training | OpenMP training threads. |
| `xgb_eval_nthread` | KIND_INT | Training | OpenMP eval threads. |
| `csv_load_workers` | KIND_INT | Training | Training data load parallelism. |
| `multi_horizon_max_threads` | KIND_INT | Training | Training-time parallelism. |
| `feature_collect_max_gb` | KIND_INT | Training | Training OOM cap. |
| `wf_split_max_gb` | KIND_INT | Training | Walk-forward split OOM cap. |
| `held_out_max_gb` | KIND_INT | Training | Held-out load OOM cap. |

### Training discipline / Held-out (3)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `csv_sort_check_mode` | KIND_INT | Training | Training data discipline (engine-wide load policy). |
| `auto_stamp_on_held_out` | KIND_BOOL | ML | Suite/training behavior. |
| `held_out_gate_strict` | KIND_INT | Drift Acknowledgments | Held-out validation gate; training policy. |

### ML inference backend (3)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `ml_backend` | KIND_INT | ML | Engine-wide inference backend (XGBoost/ONNX/AOT). |
| `regime_model_backend` | KIND_INT | ML | Engine-wide regime model backend. |
| `use_aot_inference` | KIND_BOOL | ML | Engine-wide AOT inference flag (boot-only). |

### Notifications (2)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `notify_backend` | KIND_INT | Notifications | Engine-wide notification channel. |
| `notify_cooldown_secs` | KIND_INT | Notifications | Engine-wide notification debounce. |

### Health Logging (3)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `health_log_level` | KIND_INT | Health Logging | Engine-wide log severity. |
| `health_log_max_bytes` | KIND_INT | Health Logging | Engine-wide log rotation size. |
| `health_log_keep_count` | KIND_INT | Health Logging | Engine-wide log retention. |

### Reconcile (2)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `reconcile_interval_sec` | KIND_INT | Reconcile | Engine-wide reconcile cadence. |
| `reconcile_mode` | KIND_INT | Reconcile | Engine-wide reconcile policy (HAS_SIDE_EFFECT). |

### Engine-wide mode (3)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `engine_mode` | KIND_INT | Operational | Sharded/single_core architecture (boot-only). |
| `engine_arch` | KIND_INT | Operational | Slow-path threading model (boot-only). |
| `model_verify_strict` | KIND_INT | Drift Acknowledgments | Engine-wide verification strictness; default-flipped by `trading_mode`. |
| `trading_mode` | KIND_INT | Operational | Engine-wide paper/shadow/live mode (SAFETY_CRITICAL; STAMP_BOUND). |

### Acknowledgments (3)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `acknowledge_hardcoded_strategy_in_live` | KIND_BOOL | Drift Acknowledgments | Engine-wide safety acknowledgment. |
| `acknowledge_hot_swap_with_open_positions` | KIND_BOOL | Drift Acknowledgments | Engine-wide safety acknowledgment. |
| `allow_cross_major_engine` | KIND_BOOL | Drift Acknowledgments | Engine-wide compatibility flag. |

### Runtime GUI toggle (1)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `danger_enabled` | KIND_BOOL | Danger Gradient | Engine-wide GUI hazard toggle. |

**GLOBAL subtotal: 47** (5 + 5 + 1 + 3 + 3 + 9 + 3 + 3 + 2 + 3 + 2 + 4 + 3 + 1 = 47 ✓)

---

## PER_CORE bucket (79 rows)

### Trading (5) — plan body locks these
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `take_profit_pct` | KIND_DOUBLE_PCT | Trading | Strategy parameter; per-core. |
| `stop_loss_pct` | KIND_DOUBLE_PCT | Trading | Strategy parameter; per-core. |
| `fee_rate` ⚠️1 | KIND_DOUBLE_PCT | Trading | Plan body says PER_CORE — locked per cohort. |
| `slippage_pct` ⚠️1 | KIND_DOUBLE_PCT | Trading | Plan body says PER_CORE — locked per cohort. |
| `fee_floor_mult` ⚠️1 | KIND_DOUBLE | Trading | Trading-category cohort sibling of fee_rate. |
| `risk_pct` | KIND_DOUBLE_PCT | Trading | Already PER_CORE today via `core_risk_pct[16]`. |

### Entry Filters (9)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `entry_offset_pct` | KIND_DOUBLE_PCT | Entry Filters | Per-strategy entry gate (PER_CORE_OK today). |
| `offset_min` | KIND_DOUBLE_PCT | Entry Filters | Adaptive bound (PER_CORE_OK today). |
| `offset_max` | KIND_DOUBLE_PCT | Entry Filters | Adaptive bound (PER_CORE_OK today). |
| `volume_multiplier` | KIND_DOUBLE | Entry Filters | Volume gate per strategy. |
| `spacing_multiplier` | KIND_DOUBLE | Entry Filters | Per-strategy entry spacing. |
| `min_long_slope` | KIND_DOUBLE | Entry Filters | MR-specific slope gate. |
| `min_buy_delta` | KIND_DOUBLE | Entry Filters | MR-specific volume delta gate. |
| `vwap_offset` | KIND_DOUBLE | Entry Filters | Strategy-specific VWAP gate. |
| `min_stddev_pct` | KIND_DOUBLE | Entry Filters | Per-strategy minimum volatility gate. |

### Time-Based Exit (4)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `tp_hold_score` | KIND_DOUBLE | Time-Based Exit | Per-strategy hold criterion (PER_CORE_OK today). |
| `tp_trail_mult` | KIND_DOUBLE | Time-Based Exit | Per-strategy trail (PER_CORE_OK today). |
| `sl_trail_mult` | KIND_DOUBLE | Time-Based Exit | Per-strategy trail (PER_CORE_OK today). |
| `max_hold_ticks` | KIND_INT | Time-Based Exit | Per-strategy time-out (PER_CORE_OK today). |

### Risk per-core (4) — plan amendment: kill switches + max-drawdown moved per-core
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `max_drawdown_pct` | KIND_DOUBLE_PCT | Risk Management | Per plan amendment 2026-05-15: "different cores warrant different risk envelopes." |
| `max_exposure_pct` | KIND_DOUBLE_PCT | Risk Management | Same per-core-envelope rationale. |
| `kill_switch_daily_loss_pct` | KIND_DOUBLE_PCT | Kill Switch | Per plan amendment; SAFETY_CRITICAL stays. |
| `kill_switch_drawdown_pct` | KIND_DOUBLE_PCT | Kill Switch | Per plan amendment. |
| `enable_mtm_kill_switch` | KIND_BOOL | Kill Switch | Per-core kill switch toggle. |
| `kill_recovery_warmup` | KIND_INT | Kill Switch | Per-core kill recovery cadence. |

(6 rows actually — counting `enable_mtm_kill_switch` + `kill_recovery_warmup`; subtotal note below)

### Gate Recovery (5)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `sl_cooldown_adaptive` | KIND_BOOL | Gate Recovery | Per-strategy cooldown mode. |
| `sl_cooldown_base` | KIND_INT | Gate Recovery | Per-strategy cooldown base cycles. |
| `sl_cooldown_extra` | KIND_INT | Gate Recovery | Per-strategy adaptive cooldown extra. |
| `sl_cooldown_cycles` | KIND_INT | Gate Recovery | Per-strategy cooldown duration. |
| `idle_reset_cycles` | KIND_INT | Gate Recovery | Per-strategy idle-reset cadence. |

### Momentum strategy (6)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `momentum_min_tp_margin_pct` | KIND_DOUBLE | Strategies | Momentum-specific (PER_CORE_OK today). |
| `momentum_min_buy_delta_recent` | KIND_DOUBLE | Strategies | Momentum-specific (PER_CORE_OK today). |
| `momentum_min_r2` | KIND_DOUBLE | Strategies | Momentum-specific (PER_CORE_OK today). |
| `momentum_tp_mult` | KIND_DOUBLE | Strategies | Momentum-specific. |
| `momentum_sl_mult` | KIND_DOUBLE | Strategies | Momentum-specific. |
| `momentum_breakout_mult` | KIND_DOUBLE | Strategies | Momentum-specific. |
| `momentum_require_last_win` | KIND_BOOL | Momentum Tuning | Momentum-specific SHALT gate. |

(7 rows actually)

### EMA Cross strategy (3)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `emacross_dip_mult` | KIND_DOUBLE | Strategies | EmaCross-specific. |
| `emacross_crossover_min` | KIND_DOUBLE | Strategies | EmaCross-specific. |
| `emacross_trail_mult` | KIND_DOUBLE | Strategies | EmaCross-specific. |

### Regime Detection (5)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `regime_slope_threshold` | KIND_DOUBLE | Regime Detection | Per-core RegimeDetector. |
| `regime_crossover_threshold` | KIND_DOUBLE | Regime Detection | Per-core RegimeDetector. |
| `regime_strong_crossover` | KIND_DOUBLE | Regime Detection | Per-core RegimeDetector. |
| `regime_r2_threshold` | KIND_DOUBLE_PCT | Regime Detection | Per-core RegimeDetector. |
| `regime_hysteresis` | KIND_INT | Regime Detection | Per-core RegimeDetector hysteresis. |

### ML — entry threshold + TP/SL (3)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `ml_buy_threshold` | KIND_DOUBLE | ML | Per-core ML strategy. |
| `ml_tp_pct` | KIND_DOUBLE_PCT | ML | Per-core ML TP. |
| `ml_sl_pct` | KIND_DOUBLE_PCT | ML | Per-core ML SL. |

### ML — Bandit/Confidence/Ridge (per-core authoritative) (13)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `bandit_blend_ratio` | KIND_DOUBLE | ML | Per-core bandit blend (PER_CORE_OK today). |
| `confidence_threshold_scale` | KIND_DOUBLE | ML | Per-core confidence threshold (PER_CORE_OK today). |
| `confidence_window` ⚠️2 | KIND_INT | FoxML | Forward-look: per-core ConfidenceScorer divergence. |
| `confidence_turnover_window` | KIND_INT | FoxML | Per-core confidence stats window. |
| `confidence_turnover_topk` | KIND_INT | FoxML | Per-core top-K confidence sample. |
| `confidence_ic_floor_window` | KIND_INT | FoxML | Per-core IC floor enforcement window. |
| `confidence_ic_variant` ⚠️3 | KIND_INT | FoxML | Per-core IC variant choice (A/B-able). |
| `ensemble_min_warmup_predictions` | KIND_INT | Ensemble | Per-core ensemble warmup. |
| `ensemble_bandit_save_interval` | KIND_INT | Ensemble | Per-core ensemble save cadence. |
| `thompson_rng_seed` ⚠️6 | KIND_INT | FoxML | Per-core bandit seed (HAS_SIDE_EFFECT). |
| `model_max_age_hours` ⚠️5 | KIND_INT | Lifecycle | Per-core model freshness gate. |

(11 rows actually — counting flagged + unflagged)

### STAMP_BOUND scalar cohort (Ridge + Winsor + Confidence + Thompson) (12)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `ridge_lambda` | KIND_DOUBLE | ML/Ridge | Per-core ML/Ridge (STAMP_BOUND). |
| `ridge_cost_penalty` | KIND_DOUBLE | ML/Ridge | Per-core ML/Ridge (STAMP_BOUND). |
| `ridge_min_ic_floor` | KIND_DOUBLE | ML/Ridge | Per-core ML/Ridge (STAMP_BOUND). |
| `winsor_pct_low` | KIND_DOUBLE | ML/Winsor | Per-core ML/Winsor (STAMP_BOUND). |
| `winsor_pct_high` | KIND_DOUBLE | ML/Winsor | Per-core ML/Winsor (STAMP_BOUND). |
| `confidence_freshness_tau_secs` | KIND_DOUBLE | ML/Confidence | Per-core composite confidence (STAMP_BOUND). |
| `confidence_capacity_target_dollars` | KIND_DOUBLE | ML/Confidence | Per-core composite confidence (STAMP_BOUND). |
| `confidence_capacity_kappa` | KIND_DOUBLE | ML/Confidence | Per-core composite confidence (STAMP_BOUND). |
| `confidence_rmse_baseline` | KIND_DOUBLE | ML/Confidence | Per-core composite confidence (STAMP_BOUND). |
| `thompson_mu_prior` | KIND_DOUBLE | ML/Thompson | Per-core bandit Bayesian prior (STAMP_BOUND). |
| `thompson_precision_prior` | KIND_DOUBLE | ML/Thompson | Per-core bandit Bayesian prior (STAMP_BOUND). |
| `thompson_precision_obs` | KIND_DOUBLE | ML/Thompson | Per-core bandit Bayesian obs precision (STAMP_BOUND). |
| `bandit_algorithm` | KIND_INT | ML/Bandit | Per-core bandit dispatcher (STAMP_BOUND; HAS_SIDE_EFFECT). |

(13 rows actually)

### Per-core risk thresholds (STAMP_BOUND) (4)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `risk_full_size_threshold` | KIND_DOUBLE | Risk Management | Per-core risk curve (STAMP_BOUND). |
| `risk_min_size_threshold` | KIND_DOUBLE | Risk Management | Per-core risk curve (STAMP_BOUND). |
| `risk_min_size_pct` | KIND_DOUBLE | Risk Management | Per-core risk curve floor (STAMP_BOUND). |
| `risk_degradation_curve` ⚠️4 | KIND_INT | Risk Management | Per-core risk curve shape (STAMP_BOUND; HAS_SIDE_EFFECT). |

### Partial exits / Breakeven (3)
| field_name | Kind | Section | Rationale |
|---|---|---|---|
| `partial_exit_pct` | KIND_DOUBLE | Partial Exits | Per-strategy partial exit. |
| `tp2_mult` | KIND_DOUBLE | Partial Exits | Per-strategy TP2. |
| `breakeven_buffer_pct` | KIND_DOUBLE_PCT | Partial Exits | Per-strategy breakeven offset. |

**PER_CORE subtotal: 79** (6 + 9 + 4 + 6 + 5 + 7 + 3 + 5 + 3 + 11 + 13 + 4 + 3 = 79 ✓)

Wait — recount: 6 trading + 9 entry + 4 time-exit + 6 risk + 5 gate-recovery + 7 momentum + 3 emacross + 5 regime + 3 ml-basic + 11 ml-bandit-conf + 13 stamp-bound-cohort + 4 risk-thresholds + 3 partial = 79 ✓

---

## REMOVED bucket (3 rows)

| field_name | Kind | Rationale |
|---|---|---|
| `default_strategy` | KIND_INT | Legacy single_core default; per plan body: "Per-core strategy override at core_<N>_strategy is the canonical surface." Single_core engine is deprecated. |
| `pay_fees_in_bnb` | KIND_BOOL | Per plan body REMOVED list: "operator-side cfg; doesn't affect engine behavior." |
| `reconcile_dry_run` | KIND_INT | DEPRECATED at v5.14.4 (already flagged with `CfgFieldDescriptor::DEPRECATED`); engine reads `reconcile_mode` instead. Shim removed at this ship. |

---

## A2 bitmap-bool cohort note (separate from this 129-row count)

Per operator-locked decision 2026-05-15: ~32 KIND_BOOL flat rows ADDED to per-core registry at `.F.4c.3` (12 bits ml_cfg_flags + ~7 lifecycle + ~6 gate + ~5 risk + ~6 ops). These are NEW rows derived from the 5 `FOREACH_*_CFG_FLAG` bitmap domains, not migrations of existing rows. **8 non-stamp-emit ml_cfg_flags bits + 4 stamp-emit-BITMAP_BIT bits defer to `.F.4d`** = 8 ml_cfg_flags rows at `.F.4c.3`; remaining 4 stamp-emit bits at `.F.4d`.

After the A2 expansion: per-core registry final count ≈ **79 + 32 = ~111 rows** (with one caveat: 4 ml_cfg_flags stamp-emit bits stay in ml_cfg_flags source through `.F.4d`).

---

## Verification before Step 1 — LOCKED 2026-05-15

- [x] Caramel reviews this table — flagged borderline calls ⚠️1-⚠️7 resolved
- [x] Caramel locks GLOBAL bucket = 47
- [x] Caramel locks PER_CORE bucket = 79
- [x] Caramel confirms 3 REMOVED rows
- [x] Greenlight given — Step 1 starts (FOREACH_GLOBAL_CFG_FIELD + FOREACH_PER_CORE_CFG_FIELD declaration with the row migrations per this table)

### Decisions locked

| Borderline call | LOCKED resolution |
|---|---|
| ⚠️1 `fee_rate` / `slippage_pct` / `fee_floor_mult` | **PER_CORE** |
| ⚠️2 `confidence_window` | **PER_CORE** |
| ⚠️3 `confidence_ic_variant` | **PER_CORE** |
| ⚠️4 `risk_degradation_curve` | **PER_CORE** |
| ⚠️5 `model_max_age_hours` | **PER_CORE** |
| ⚠️6 `thompson_rng_seed` | **PER_CORE** |
| ⚠️7 `max_positions` | **GLOBAL** |

**Operator framing 2026-05-15:** *"given the frameworks were making, it would be easy to change in the future right?"* — Yes. Future global↔per-core flip = move X() row between registry macros (1 line) + struct field auto-regenerates + mechanical fixture migration grep + re-lock per-core Layer 5b if STAMP_BOUND. ~10-30 min per field. Today's classification is adequate-not-perfect because the cost of being wrong is bounded — that's the framework discipline meta-principle in concrete form.

---

## Decisions surfaced (concrete questions)

Caramel — these are the ⚠️ borderline calls. Quick yes/no on each:

1. **⚠️1 `fee_rate` / `slippage_pct` / `fee_floor_mult`** — Plan body locked PER_CORE under "trading" cohort. Lock PER_CORE? Or flip to GLOBAL (exchange-config-level)?
   → My recommendation: **PER_CORE** (per plan body; matches per-core authoritative discipline; trivial fixture migration). Flip-cost is low if you decide later.

2. **⚠️2 `confidence_window`** — Today engine-wide. PER_CORE forward-looks at per-core ConfidenceScorer divergence. GLOBAL preserves current behavior with less fixture churn.
   → My recommendation: **PER_CORE** (per "all ML knobs per-core" framing). Cost: ~32 fixture migrations.

3. **⚠️3 `confidence_ic_variant`** — Could be uniform engine-wide ML pipeline (GLOBAL) or per-core IC A/B (PER_CORE).
   → My recommendation: **PER_CORE** (consistency with confidence_* cohort).

4. **⚠️4 `risk_degradation_curve`** (STAMP_BOUND ENUM) — Per-core risk envelope (PER_CORE) or uniform engine policy (GLOBAL)?
   → My recommendation: **PER_CORE** (matches "different cores warrant different risk envelopes" amendment).

5. **⚠️5 `model_max_age_hours`** — Per-core model freshness (PER_CORE) or engine-wide (GLOBAL)?
   → My recommendation: **PER_CORE** (each core loads its own model with its own age policy).

6. **⚠️6 `thompson_rng_seed`** — Explicit per-core seed (PER_CORE) or global with derived offset (GLOBAL)?
   → My recommendation: **PER_CORE** (operator-readable; explicit > derived). 

7. **⚠️7 `max_positions`** — GLOBAL (architecture enforces 1/core) or PER_CORE (forward-flex)?
   → My recommendation: **GLOBAL** (architecturally fixed; PER_CORE costs ~16 fixture sites for no behavioral gain).

**Bias question:** my default when uncertain is GLOBAL (to keep fixture migration cost down). If your default is PER_CORE (anything trading-adjacent), flip cases 2/3/5/6 toward PER_CORE more aggressively. If your default is GLOBAL (only obvious per-core knobs go per-core), flip cases 4 back toward GLOBAL.

After your call on these 7, I'll lock the table + proceed to Step 1 (registry declarations).
