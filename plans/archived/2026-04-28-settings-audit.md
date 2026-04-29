# Settings audit — 2026-04-28

Goal: figure out which settings should be **truly global**, which should be **per-core overrides**, which are **deprecated**, and what ML/backtest pipelines depend on. Output is a categorized inventory + a migration plan.

## Current state

Two layers already exist:

1. **`field_defs[]`** — every cfg field, rendered in the Global tab. ~80 entries.
2. **`per_core_fields[]`** — fields with `core_N_<key>` per-core override variants. ~17 entries. When set non-zero on Core N, override the global default for that core only. Already wired through `ControllerConfig_ResolveForCore`.

The infrastructure works. The PROBLEM is the Global tab still renders **all** fields (including ones that already have per-core variants), strategy-specific tuning is split awkwardly between Global ("SimpleDip Tuning" section) and per-core ("Strategy-Specific" section), and several sections are stale ("Per-Core (Experimental)" — sharded is canonical).

The user-facing fix is two parts:

- **Layout cleanup**: hide global fields whose per-core override is set on every active core; hide strategy tuning sections when no core uses that strategy.
- **Migration**: identify global fields that SHOULD have per-core overrides but don't (esp. ML / regime / partial exits).

## ML / backtest constraints (load-bearing)

Any field that affects model training MUST keep train-serve parity. Backtest reads from `backtest.cfg` → `ControllerConfig` → fed to `BacktestSharded_Run` → trains on those features. Live reads from `engine.cfg` → same `ControllerConfig` → fed to `EngineSharded_Run`.

Implication for per-core migration:
- If a setting moves to `core_N_*`, both backtest and live must call `ControllerConfig_ResolveForCore(N)` to get the effective value. (Already does for the existing 17.)
- ML feature pack (`ModelFeatures_Pack`) reads `RegimeSignals` not cfg directly, so it's already insulated. Good.
- `confidence_*` settings ARE consulted at inference time — currently global. Moving to per-core means each ML core can have its own confidence threshold. Backtest needs to honor the per-core override too.
- `ml_buy_threshold` already has a per-core override entry (`per_core_fields[]` last 3 entries). Other ML knobs do not.

**Rule**: anything you flag for per-core migration below also needs to be added to `per_core_fields[]`, `PerCoreOverrides` struct, `ControllerConfig_ResolveForCore`, and the cfg parser. Four-site change per field.

## Field-by-field audit

### TRULY GLOBAL (engine-wide, no semantic per-core override)

These describe the machine, the account, the market state, or system-level policy. Per-core overrides would be confusing or meaningless.

| Field | Current Section | Reason it stays global |
|---|---|---|
| `fee_rate`, `fee_rate_maker`, `fee_rate_taker` | Trading | Exchange-side, identical for all cores. |
| `slippage_pct` | Trading | Engine-wide adapter behavior. |
| `max_drawdown_pct` | Risk Management | Account-level circuit breaker. |
| `max_exposure_pct` | Risk Management | Account-level cap (sum across cores). |
| `max_positions` | Risk Management | Multi-slot fallback config; sharded uses per-core slots. **Possibly deprecated** in sharded mode. |
| `kill_switch_*` | Kill Switch | Account-level + per-core peak tracker (already has per-core peak under the hood, no need for cfg-level override). |
| `kill_recovery_warmup` | Kill Switch | Engine-level cooldown. |
| `vwap_offset` | Entry Filters | Global VWAP signal. |
| `min_stddev_pct` | Entry Filters | Market quality filter — same market for all cores. |
| `regime_*` (5 fields) | Regime Detection | Global market state classifier. AUTO routing per core, but classification itself is shared. |
| `gate_ema_enabled`, `gate_ema_alpha` | EMA Gate | Global EMA price tracker, fed to all cores. |
| `danger_*` (3 fields) | Danger Gradient | Global crash protection, shared. |
| `record_ticks`, `record_depth`, `record_max_days` | Tick Recording | Engine-wide telemetry. |
| `notify_*` (4 fields) | Operational Monitoring | Engine-wide alerting. |
| `use_real_money` | Toggles | Engine-wide dispatch. |
| `depth_enabled` | Toggles | Engine-wide WS subscription. |
| `min_book_imbalance` | Toggles | Global order book signal. |
| `session_*_mult` (4 fields), `session_filter_enabled` | Session Filters / Toggles | Time-of-day market filter. Could be per-core but probably overkill. |
| `engine_mode`, `num_execution_cores` | Per-Core (currently labeled experimental) | Boot-only, engine-wide. **Re-section as just "Per-Core"**, drop "Experimental". |
| `poll_interval`, `warmup_ticks`, `min_warmup_samples` | Engine Timing | Engine-wide cadence. |
| `idle_reset_cycles` | Gate Recovery | Engine-wide gate decay timer. |
| `held_out_fraction`, `gap_acceptable_threshold` | Validation | ML training-time configuration; engine-wide. |
| `default_strategy` | Strategy | AUTO router fallback (when no per-core strategy set). Engine-wide default. |

### ALREADY PER-CORE (overrides exist)

These have entries in `per_core_fields[]` and resolve via `ControllerConfig_ResolveForCore`. **The Global tab should keep showing them as defaults** — that's how inheritance works — but per-core tab should clearly indicate "0 = inherit". Already does. Consider renaming Global section labels to "Defaults" to make the relationship explicit.

| Field | Status |
|---|---|
| `take_profit_pct`, `stop_loss_pct`, `fee_floor_mult` | ✓ already overridable |
| `entry_offset_pct`, `volume_multiplier`, `spacing_multiplier`, `offset_stddev_mult` | ✓ already overridable |
| `simpledip_tp_pct`, `simpledip_sl_pct` | ✓ |
| `mr_tp_pct`, `mr_sl_pct` | ✓ |
| `momentum_tp_mult`, `momentum_sl_mult` | ✓ |
| `emacross_tp_pct`, `emacross_sl_pct` | ✓ |
| `ml_tp_pct`, `ml_sl_pct`, `ml_buy_threshold` | ✓ |
| `core_N_strategy`, `core_N_risk_pct`, `core_N_model_path`, `core_N_model_dir` | ✓ structural per-core |

### SHOULD BE PER-CORE (currently global, semantically per-core)

These are tuning knobs that vary by strategy or core but currently have no override. Adding per-core overrides means real per-core tuning becomes possible (e.g. one ML core conservative thresholds, another aggressive).

| Field | Section | Why per-core |
|---|---|---|
| `momentum_breakout_mult` | Momentum / Momentum Tuning | Strategy-specific entry threshold; only relevant to Momentum cores. Already in per-core list as `momentum_tp_mult` / `momentum_sl_mult` siblings — add this one too. |
| `momentum_r2_min` | Momentum | Same logic. |
| `emacross_dip_mult`, `emacross_crossover_min`, `emacross_trail_mult` | EMA Cross | EMA-Cross-specific entry/trail. Per-core-overridable for EMA cores. |
| `confidence_enabled`, `confidence_window`, `confidence_freshness_tau`, `confidence_threshold_scale` | FoxML | ML-only. Each ML core could want different confidence behavior. **High value if you run multiple ML cores with different prediction horizons.** |
| `cost_gate_enabled` | FoxML | Per-strategy entry filter. |
| `foxml_vol_scaling_enabled`, `foxml_vol_scaling_z_max` | FoxML | Position sizing — already partially per-core via risk_pct, but z-clip threshold is shared. |
| `bandit_enabled`, `bandit_blend_ratio` | FoxML | If multiple cores run STRATEGY_ML, bandit weights are per-strategy. Currently a single global bandit instance. **Note**: making this per-core requires the bandit state structure itself to be per-core, not just the cfg field. Bigger change. |
| `partial_exit_pct`, `tp2_mult`, `breakeven_on_partial` | Partial Exits | Partial exit geometry could differ per strategy (e.g. DIP wants fast TP1, EMA wants long TP2 ride). |
| `tp_hold_score`, `tp_trail_mult`, `sl_trail_mult` | Trailing TP/SL | Trailing behavior is strategy-dependent. |
| `max_hold_ticks`, `min_hold_gain_pct` | Time-Based Exit | Time exit horizon depends on strategy holding period. |
| `vol_sizing_enabled`, `vol_scale_min`, `vol_scale_max` | Vol Sizing | Could be per-core, but probably keep global for consistency unless per-strategy sizing is wanted. |
| `no_trade_band_enabled`, `no_trade_band_mult` | No-Trade Band | Currently global; could be per-core for finer control of when each strategy trades. |
| `barrier_gate_enabled`, `peak_model_path`, `valley_model_path` | Barrier | ML-only. Per-core makes sense — one ML core uses peak/valley gating, another doesn't. |
| `ml_model_path` | Models | Already has per-core variant `core_N_model_path`. The Global "Models" section is redundant — should probably hide. |
| `regime_model_path` | Models | Per-strategy regime enrichment. Currently global; reasonable per-core. |

### POSSIBLY DEPRECATED / RE-EVALUATE

| Field | Reason |
|---|---|
| `max_positions` | Sharded mode owns slots per-core (1:1 single-leg, 2:1 partials). The legacy multi-slot fallback is dead code on sharded path. **Keep the field for legacy compat but mark as legacy in tooltip.** |
| `risk_pct` (global) | Sharded uses `core_N_risk_pct` overrides; the global `risk_pct` is the **fallback when no per-core override is set** (= `risk_pct / num_cores` per core). Keep but rename label to "Default Risk %% (per-core fallback)". |
| `engine_mode` | Sharded is the only canonical path. The toggle is vestigial — flipping it OFF in sharded build doesn't even get tested. **Hide unless explicitly building legacy.** |

## Layout proposal

### Global tab — keep these sections, in this order

1. **Trading Defaults** (rename from "Trading") — TP/SL/risk/fee defaults. Note: "These are defaults; cores override per-core."
2. **Entry Filter Defaults** (rename from "Entry Filters") — same logic.
3. **Risk Management** — account-level only (drawdown, exposure cap). Drop `max_positions` or move to a "Legacy" subsection.
4. **Kill Switch** — account-level breakers.
5. **Regime Detection** — market classifier shared by AUTO cores.
6. **EMA Gate**, **Danger Gradient** — global market signals.
7. **Session Filters** — time-of-day shared filter.
8. **Engine Timing** — boot-time cadence.
9. **Validation** — held-out + gap threshold (ML training-time).
10. **Per-Core** (drop "Experimental") — engine_mode + num_execution_cores. Maybe move engine_mode to a "Legacy" hidden section.
11. **Tick Recording** — telemetry.
12. **Operational Monitoring** — alerts.
13. **Toggles** — checkbox cluster (use_real_money, partial_exit_enabled, etc.).

### Hide from Global (move into per-core tabs)

Strategy tuning sections (`SimpleDip Tuning`, `MeanReversion Tuning`, `Momentum Tuning`, `EMA Cross Tuning`) are **redundant with per-core overrides under "Strategy-Specific"**. Either:

- Hide the global sections entirely (they're already overridable per-core; the global value is just the inherited default already exposed under "Trading Defaults").
- Rename them "Strategy Defaults" and only show them when there's a global default set (i.e. user explicitly wants a non-zero default to inherit).

Same for `Momentum`, `EMA Cross` sections in Global — these duplicate `Momentum Tuning` and `EMA Cross Tuning`. **Two sections per strategy is bloat.** Pick one.

### Per-core tab — sections (only show ones relevant to this core's strategy)

- **Strategy** (always show) — strategy_id, model_path/dir
- **Risk** (always show) — risk_pct override, kill switch reset
- **Trading Override** (always show) — TP/SL/fee_floor overrides
- **Entry Filter Override** (show when strategy uses entry filters — basically always)
- **Strategy-Specific Tuning** (show only fields relevant to THIS core's strategy_id):
  - Core uses DIP → show DIP TP/SL
  - Core uses MR → show MR TP/SL
  - Core uses MOM → show MOM TP/SL/breakout/r2
  - Core uses EMA → show EMA TP/SL/dip/crossover/trail
  - Core uses ML → show ML TP/SL/threshold + confidence/cost/vol/barrier overrides
  - Core uses AUTO → show ALL strategy-specific (since AUTO routes to any of them)

This is the **biggest UX win** — a per-core tab that only shows the knobs that matter for what the core is actually doing.

## Migration plan (priorities)

### P1 — Cosmetic / dead-section cleanup (~30 min, this session)

1. Drop "(Experimental)" suffix from "Per-Core" section name (2 entries)
2. Update outdated tooltip: remove "Uses synthetic ticks until Binance feed wiring lands."
3. Fix `0 Cores` display in the GUI: when cfg field is 0/missing, render the live core count
4. Remove redundant Global sections that exact-duplicate per-core sections (`Momentum`/`Momentum Tuning`, `EMA Cross`/`EMA Cross Tuning` — pick one).

### P2 — Per-core tab strategy-aware filtering (~3-4h)

Rewrite `Settings_RenderPerCoreTab` to read each core's resolved strategy and only render the tuning sections relevant to that strategy. Big UX win, no cfg semantic changes.

### P3 — Add per-core overrides for ML/regime fields (~4-6h)

Move `confidence_*` (4), `cost_gate_enabled`, `foxml_vol_scaling_*` (2), `bandit_*` (2), `barrier_*` (3), `partial_exit_*` (3), `momentum_breakout_mult`, `momentum_r2_min`, `tp_hold_score`, `tp_trail_mult`, `sl_trail_mult`, `max_hold_ticks`, `min_hold_gain_pct`, `regime_model_path` into `per_core_fields[]`. Each one needs:

1. Entry in `per_core_fields[]`
2. Entry in `PerCoreOverrides` struct
3. Resolution in `ControllerConfig_ResolveForCore`
4. Parser case in `ControllerConfig_Load`

Total: ~20 fields × 4 sites = ~80 small touches. Mechanical.

**ML/backtest verification**: after migration, retrain and confirm features computed on backtest match live (held-out test set).

### P4 — Bandit per-core (separate, optional)

If multiple ML cores running with different prediction horizons want independent bandit state, the bandit struct itself moves from a single global instance to one per ML core. This is a bigger change than just cfg fields. **Defer** unless multi-ML use case is real.

## Dynamic core count (separate concern)

Updating `num_execution_cores` at runtime is currently restart-required. The cores are pre-allocated (`MAX_EXECUTION_CORES=16`), so the reservoir exists. What's missing:

- Threads are spawned at boot, one per active core. Inactive ones don't exist.
- SPSC ring connections (producer fanout) are wired at startup.
- Risk redistribution on count change.

To make it dynamic: pre-spawn 16 threads, give each a "go inactive" signal (busy-loop or yield instead of consuming ticks), redistribute risk on change. **2-4h focused work.** Worth it if live tuning of core count is actually wanted; otherwise restart-required is fine.

---

## Recommendation

Pick a phase and commit:

- **P1 alone** = settings panel looks clean for the next session, but the structural mess is the same. Ship as v4.7.22.
- **P1 + P2** = much cleaner UX, no cfg changes, no train-serve risk. Ship as v4.7.22 + 4.7.23.
- **P1 + P2 + P3** = real per-core tuning becomes possible. **Right move if you want to A/B test ML cores against each other.** Ship across multiple version bumps.

For tonight: P1 is the safe "make it look right" pass. P2 + P3 are the real engineering. Don't bundle P3 with anything else — too many touch points to risk piling on top of an unrelated change.
