# FEATURE_LOOKUP.md

Operator-visible feature catalog. For each feature: what it does,
cfg flags that toggle it, fallback behavior when disabled / models
missing, **where to verify it's actually working at runtime**,
paper-test sanity loop, gotchas, related persistence files.

**Workspace-private.** Auto-write contract — agent MUST add an entry
when a new operator-visible feature ships (see CLAUDE.local.md
"Going-forward rule: FEATURE_LOOKUP.md auto-write on new
operator-visible features"). Sister to PARITY_ISSUES.md, TECH_DEBT.md.

Last full audit: 2026-05-12 (seeded at v5.15.4 close).

---

## Per-core strategy dispatch

**What.** Each pinned CPU core runs its own strategy (`simple_dip`,
`momentum`, `ema_cross`, `ml`). Per-core override means cores can
run heterogeneous strategies on the same symbol.

**Cfg flags:**
- `core_N_strategy=<name>` per core
- `core_N_model_path=<path>` / `core_N_model_dir=<dir>` (ML only)
- `core_N_risk_pct=<pct>` per core

**Fallback.** Default strategy when override absent =
`cfg.strategy`. ML strategy with no model loaded → core idles
(no signals emitted).

**Where to verify:**
- Core panel header in DashboardPanels shows `strat: <name>` per core
- `MLStatusPanel.hpp` model-loaded badge per core when ML strategy
- Boot stderr `[engine] core N strategy=...` lines

**Paper-test sanity:**
1. Set `core_0_strategy=simple_dip`, `core_1_strategy=momentum`
2. Boot; confirm core panels show different strat tags
3. Trades fire from different cores under different regimes

**Related:** `FOREACH_STRATEGY` X-macro registry in
`Strategies/StrategyInterface.hpp`.

---

## Buy-side ML inference (entry ensemble)

**What.** Multi-horizon entry-signal ensemble. N XGBoost models
trained at different lookback horizons; predictions blended per
slow-path cycle into a single buy probability.

**Cfg flags:**
- `core_N_model_dir=<dir>` → engine auto-detects `<dir>_horizon_<N>/`
  siblings and loads them all into `buy_signal[]`
- `ml_threshold_*`, `confidence_threshold` gate the buy decision
- `ridge_within_horizon` / `ridge_across_horizons` toggle blender mode

**Fallback.** `buy_signal_count == 0` → strategy idles (no buy
signals emitted; legacy non-ML strategies unaffected).

**Where to verify:**
- MLStatusPanel `pred: %.3f` per core (`ml_last_pred`)
- MLStatusPanel `conf: %.3f` per core (`ml_last_confidence`)
- DashboardPanels `bandit_probs %` row per core (5-arm display)
- Boot stderr `[ensemble] loaded buy_signal=N exit_predictor=M ...`
  (`CoreModelZoo.hpp:1687-1734`)

**Paper-test sanity:**
1. Train multi-horizon models via foxml_suite (horizons CSV `1000,5000,10000`)
2. Point `cfg.core_0_model_dir` at the run dir
3. Boot engine; confirm boot stderr says `buy_signal=3 loaded`
4. Run 5k+ ticks; confirm `pred:` line in MLStatusPanel moves per cycle

**Gotchas:**
- Sibling scaler check at `CoreModelZoo.hpp:1734` — all loaded
  horizons must share the same scaler. Mismatch logs WARN, engine
  refuses load in strict mode.
- Feature registry hash check — model stamp's `feature_registry_hash`
  must match current FOREACH_FEATURE. Drift refuses load.

**Related:** `CoreModelZoo.hpp:1607-1614` (load), Model stamps,
NaN-free feature pack, Confidence scoring, Ridge blender.

---

## Sell-side ML inference (exit predictor)

**What.** Path 3 architecture (v5.13.0+). Independent ML models for
exit decisions. Predicts probability of "exit now" per slow-path
cycle; when above threshold, fires `MARKET_SELL` via OMS.

**Cfg flags:**
- `use_exit_model=1` (master toggle; default 0)
- `exit_signal_model_dir=<dir>` → engine auto-detects exit
  `<dir>_horizon_<N>/` siblings into `exit_predictor[]`
- `exit_threshold` (default 0.6) — fire-or-skip cutoff
- `exit_blender_mode` — uniform (0) vs ridge (1)

**Fallback (3 layers).**
1. `use_exit_model=0` → entire block skipped (~5ns flag check)
   (`StrategyParameters.hpp:1118`)
2. `exit_predictor_count == 0` → no models loaded, block skipped;
   legacy TP/SL fires (`StrategyParameters.hpp:1123`)
3. Any single horizon NaN/inf → that horizon excluded from blend;
   others continue (`StrategyParameters.hpp:1137`)

**Where to verify:**
- MLStatusPanel `exit: %.3f (h<idx>)` per core
  (`MLStatusPanel.hpp:179-198`). Only renders when
  `ml_last_exit_prediction > 0` — absent = either disabled or no models.
- DashboardPanels `SHALT_EXIT_PREDICTED` halt_reason when sell fires
- Boot stderr `[ensemble] exit_predictor=N loaded` line

**Paper-test sanity:**
1. Train sell-side models via foxml_suite (Training Side = "Exit")
2. Set `cfg.exit_signal_model_dir` at the `models/exit/<run>/` subtree
3. Set `cfg.use_exit_model=1`, `cfg.exit_threshold=0.4` (loose)
4. Boot; confirm `exit:` line appears in MLStatusPanel after first
   cycle. If absent: models didn't load (check boot stderr).
5. Open a position; confirm sell fires when `exit:` value crosses
   threshold AND `SHALT_EXIT_PREDICTED` flag lights.
6. Sanity test the fallback: temporarily point `exit_signal_model_dir`
   at a bogus path; confirm `exit:` line disappears + legacy TP/SL
   fires.

**Gotchas:**
- Exit models train against `Label_*` labels (same set as buy-side);
  the SIDE distinction is path-only, not label-kind-only.
- Exit predictor reuses standardized features from buy-side path
  (scaler is shared via sibling-scaler load-time check).

**Related:** Exit bandit (separate but parallel), Ridge blender
(exit variant), Multi-horizon training (Training Side selector).

---

## Bandits (buy + exit; Exp3-IX + Thompson)

**What.** Arm selection across regimes (buy) and across horizons
(exit). Per-arm reward observability invariant (CLAUDE.md item 24)
makes shadow-training + multi-algo A/B valid.

**Cfg flags:**
- `bandit_enabled=1` (buy-side, default; per-regime arms)
- `exit_bandit_enabled=1` (sell-side, parallel)
- `bandit_algorithm` — 0=Exp3-IX (default), 1=Thompson (v5.14.10),
  2=dual-mode shadow (v5.14.10.B)
- `bandit_warmup_n` — N cycles before bandit takes over from
  uniform priors
- `bandit_persist_every_n` — flush bandit_state.json every N
  updates

**Fallback.** `bandit_enabled=0` → uniform 1/N probabilities, no
update math runs. Single-arm case (only 1 model loaded) → bandit
skipped entirely (`CoreModelZoo.hpp:2060, 2114`).

**Where to verify:**
- DashboardPanels per-arm `bandit_probs %` row
  (`DashboardPanels.hpp:1745`) — drifts from uniform 1/N as reward
  accumulates
- MLStatusPanel arm list with `*` on chosen arm
  (`MLStatusPanel.hpp:585-598`)
- `<core_model_dir>/bandit_state.json` file growth +
  modification time
- `<core_model_dir>/exit_bandit_state.json` (sell-side)
- `<core_model_dir>/thompson_state.json` (Thompson mode)

**Paper-test sanity:**
1. Boot fresh (no `bandit_state.json` present)
2. Run 5k+ ticks
3. Confirm `bandit_probs` row shifts: arms with positive reward
   trend up, negative trend down
4. Kill engine; confirm `bandit_state.json` exists in core_model_dir
5. Restart; confirm `bandit_probs` row picks up where it left off
   (NOT uniform after warmup)
6. Dual-mode (cfg=2): confirm both Exp3 + Thompson states write to
   disk; only one drives decisions, both learn from same reward stream

**Gotchas:**
- Stamp-locked bandit signature — bundle ID check refuses
  `bandit_state.json` from a different model bundle
  (`CoreModelZoo.hpp:2099-2125`). Override:
  `BacktestRunConfig.bandit_state_prior_path` (backtest only).
- Per-regime arm allocation — bandit arms ≠ horizons; they're
  regime-specific arms within each model. exit_bandit ≠ buy_bandit.
- Per-arm reward observability (CLAUDE.md item 24) holds because
  all arms get directionally-graded against same actual; if v6.0+
  maker work changes this, dual-mode validity breaks.

**Related:** Per-arm reward observability invariant, Multi-horizon
exit ensemble (arm count = exit_predictor_count).

---

## Ridge blender (within-horizon + across-horizons + exit)

**What.** Ridge-regression-based ensemble weights, replacing
uniform averaging. Solves weighted least-squares against historical
prediction correlation matrix; bytewise-deterministic (CLAUDE.md
items 25-27).

**Cfg flags:**
- `ridge_within_horizon` — buy-side within-horizon blender
- `ridge_across_horizons` — buy-side cross-horizon blender
- `exit_blender_mode` — sell-side ridge (0=uniform, 1=ridge)
- `ridge_online_corr` — incremental correlation update vs full
  recompute (default 0 = full)
- `ridge_lambda` — regularization (default 0.01)

**Fallback.** Disabled → uniform 1/N averaging. Single-model case
(count < 2) → uniform regardless of flag. Cholesky solve fails
(NaN matrix, ill-conditioned) → falls back to uniform for that
cycle (`StrategyParameters.hpp:1191-1213`).

**Where to verify:**
- Slow-path debug log entry when Ridge corr matrix populates +
  weights computed (look for `RidgeBlender_OnlineCycleStep` returning 0)
- Per-arm weight display in MLStatusPanel (when wired —
  v5.14.11.B+; pre-v5.14.11 = no display yet, must read slow-path
  state directly)
- Reward ring growth: `exit_reward_ring_head` advances each cycle
  predictions are recorded
- Ridge state persistence: `<core_model_dir>/ridge_state.json`
  (sell-side: `exit_ridge_state.json`)

**Paper-test sanity:**
1. Boot with `ridge_within_horizon=1` + multi-horizon ensemble
2. Run 256+ ticks (full reward ring)
3. Confirm slow-path stays clean (no NaN/inf logs)
4. Compare weighted prediction to uniform: should differ once
   reward correlations diverge from random

**Gotchas:**
- AVX-512 / scalar byte-determinism (CLAUDE.md item 25) — both
  paths produce identical output; SHA-256 lock test in
  `controller_test*.cpp` verifies
- Constant-iter inner loop (CLAUDE.md item 26) — 8-wide reduction
  regardless of n_arms; zero-contribution iterations bytewise no-op
- Struct padding (`FPN<F>`, `ThompsonBanditState`) explicit-zero
  (CLAUDE.md item 27) prevents non-deterministic memcmp/hash on
  uninit bytes

**Related:** Cholesky solver, Reward ring, IC tracker (per-arm
drift detection feeds Ridge cost-aware path planned post-v5.15).

---

## Confidence scoring (per-arm + composite)

**What.** Per-arm prediction confidence (entropy / margin / agreement
across horizons) combined into a composite confidence gate.
Below-threshold predictions skip OMS submit even if `pred > threshold`.

**Cfg flags:**
- `confidence_enabled=1` (master)
- `composite_confidence_enabled=1` (cross-arm agreement signal)
- `confidence_threshold=<float>` — gate cutoff
- `confidence_alpha`, `confidence_horizon` — composite mixing
  weights

**Fallback.** Disabled → confidence = 1.0 always (no gate). Single
model → composite reduces to per-arm confidence.

**Where to verify:**
- MLStatusPanel `conf: %.3f` per core (`ml_last_confidence`)
- MLStatusPanel `threshold: %.3f` (`ml_last_threshold`)
- When `conf < threshold` and `pred > pred_threshold`: prediction
  emitted but no OMS submit; look for "confidence gate blocked"
  in slow-path log

**Paper-test sanity:**
1. Set `confidence_threshold=0.9` (very strict)
2. Confirm `conf:` line in MLStatusPanel; expect most cycles to
   show conf < 0.9 → no trades fire
3. Loosen to 0.3 → trades fire even on noisy predictions
4. Compare per-arm vs composite by toggling
   `composite_confidence_enabled`

---

## Vol scaling

**What.** Position sizing scaled by realized volatility — larger
positions in low-vol regimes, smaller in high-vol. Reduces tail-vol
drawdowns.

**Cfg flags:**
- `vol_scaling=1` (master)
- `vol_target_pct` — target portfolio volatility
- `vol_lookback_ticks` — realized vol window

**Fallback.** Disabled → fixed-`risk_pct` sizing.

**Where to verify:**
- DashboardPanels position-size column shows variable amounts
  when on; identical amounts when off
- Vol estimate published in TUISnapshot (look for `realized_vol`
  per core)

**Paper-test sanity:**
1. Run paper with `vol_scaling=0`; record N position sizes
2. Run same period with `vol_scaling=1`; sizes should vary
3. Confirm sizes correlate inversely with regime variance

---

## Lazy rebuild

**What.** Slow-path skips full RebuildOneCore when no input has
changed since last cycle. Cuts 30-50% of slow-path cycles in steady
regimes.

**Cfg flags:**
- `lazy_rebuild=1` (master)
- `lazy_rebuild_force_n` — force full rebuild every N cycles
  (sanity refresh)

**Fallback.** Disabled → every slow-path cycle does full rebuild
(pre-v5.12 behavior).

**Where to verify:**
- Slow-path latency drops in HOT_PATH_CHANGELOG.md per-cycle
  estimates
- Slow-path-cycle counter vs rebuild-fired counter divergence
- Heat dashboard CPU% drop with lazy_rebuild on

**Paper-test sanity:**
1. Run paper with `lazy_rebuild=0` for 60s; record CPU% per core
2. Restart with `lazy_rebuild=1`; CPU% should drop ~30-50%
3. Confirm trade frequency / decisions unchanged (bytewise equiv
   when input changes detected correctly)

**Gotchas:**
- Bytewise-identical to non-lazy when input hash matches (no math
  approximation); diverges only when lazy path missed an input
  change → REGRESSION CLASS, regression-test via parity_harness.

---

## Drift detection + auto-retire

**What.** Rolling IC (information coefficient) tracker per arm.
When avg IC stays below floor for N samples → DRIFT_BREACHED. If
configured to auto-kill → DRIFT_KILL_TRIPPED (core stops trading).

**Cfg flags:**
- `drift_detect_enabled=1`
- `drift_ic_floor` — IC threshold (default 0.0)
- `drift_min_samples` — sample count before drift can fire
- `drift_auto_kill=1` — auto-kill core on breach (else just
  warning)

**Fallback.** Disabled → no IC tracking, core trades forever
regardless of model decay.

**Where to verify:**
- MLStatusPanel `drift: BREACHED (avg_ic=X, n=Y)` (WARN orange)
  or `drift: KILLED` (RED) (`MLStatusPanel.hpp:266-280`)
- DashboardPanels `SHALT_DRIFT_KILL` halt_reason on affected core
- Per-core IC ring in slow_state for debugging the avg

**Paper-test sanity:**
1. Inject deliberately bad model (random predictions); set
   `drift_auto_kill=1`, `drift_min_samples=200`
2. Run 250+ cycles
3. Confirm `drift: BREACHED` appears, then `KILLED` after
   confirmation window
4. Confirm OMS submit blocked on that core (no new trades) but
   open positions still managed by legacy exits

---

## Per-core kill switches + cfg drift

**What.** Multiple kill paths: manual kill switch (operator
trigger), MTM-drawdown kill (per-core P&L floor), drift-kill (above),
cfg-drift strict refuse.

**Cfg flags:**
- `core_kill_drawdown_pct` — MTM floor per core
- `acknowledge_inference_cfg_drift=1` — suppress cfg-drift WARN
- `held_out_gate_strict=1` — refuse model load on stamp violations

**Fallback.** No flag-disable for kills (they're tripwires);
operator can set thresholds wide if they don't want them firing.

**Where to verify:**
- MLStatusPanel halt_reason badge per core: `SHALT_MTM_KILL`,
  `SHALT_DRIFT_KILL`, `SHALT_MANUAL_KILL`, `SHALT_EXIT_PREDICTED`
- MLStatusPanel cfg-drift row: `cfg drift: X Tier 1, Y Tier 2`
  with strict-refused / WARN states (`MLStatusPanel.hpp:236-261`)
- Boot stderr cfg-drift detail lines
- `STATE_FLAG_IS_SET(pc, DRIFT_KILL_TRIPPED)` etc. in snapshot

**Paper-test sanity:**
1. Set `core_kill_drawdown_pct=0.5` (very tight)
2. Boot; first 1% drawdown should trip MTM kill
3. Confirm `SHALT_MTM_KILL` on affected core
4. Confirm other cores keep trading

---

## Model stamps (verify_model_stamp + scaler binding)

**What.** Each `.model` has a signed stamp recording cfg + feature
registry + scaler SHA + build flags at training time. Engine
verifies at load; refuses or warns on drift.

**Cfg flags:**
- `held_out_gate_strict=1` — strict mode: refuse on any drift
- `acknowledge_inference_cfg_drift=1` — explicit ack to load
  despite Tier 2 drift

**Fallback.** Strict-refuse → model unloaded, engine still runs
without it (per-core path leaves core idle if ML required).

**Where to verify:**
- MLStatusPanel scaler row: `scaler: applied / NONE / WARN — load failed`
  (`MLStatusPanel.hpp:201-228`)
- MLStatusPanel cfg-drift row (above)
- Boot stderr per-field stamp comparison
- `model.stamp` sidecar file presence next to `.model`

**Paper-test sanity:**
1. Train a model
2. Change `cfg.threshold_scale` between training + inference
3. Confirm Tier 1 cfg-drift WARN (or REFUSE under strict)
4. Set `acknowledge_inference_cfg_drift=1`; confirm WARN suppresses

**Gotchas:**
- Tier 1 fields (CLAUDE.md item 15) directly affect serving math;
  Tier 2 are forensic. Strict mode refuses Tier 1, WARNs Tier 2.
- Feature registry hash drift = ALWAYS refuse (no override) — adds
  a feature without retraining → won't load.
- Scaler sibling check at multi-horizon load (`CoreModelZoo.hpp:1734`).

**Related:** PARITY_ISSUES.md (any new drift class lands there).

---

## Partial exits (legs A+B)

**What.** Two slots per core; can scale out of a position in
fractional legs. Leg A exits at first TP / SL; leg B can ride
trailing stop. Dispatcher post-cap → strategies stay leg-A-only.

**Cfg flags:**
- `partial_exit_enabled=1`
- `partial_exit_leg_a_pct` — fraction sized to leg A
- `partial_exit_trailing_*` — leg B trailing stop params

**Fallback.** Disabled → single-slot exits per core (legacy).

**Where to verify:**
- Position count per core can reach 2 (vs max 1 when disabled)
- DashboardPanels position rows show A/B leg tags
- TradeHistoryPanel exit-reason column distinguishes leg A vs leg B

**Paper-test sanity:**
1. Enable + open a position
2. Confirm 2 slots fill (split position size)
3. First exit takes ~50% via leg A trigger
4. Remainder rides trailing stop via leg B

**Gotchas:**
- Max cores = 8 when partial_exit_enabled=1 (vs 16 default) —
  each core needs 2 slots in portfolio bitmap.
- Branch-gated on hot path (CLAUDE.md item 10).

---

## Breakeven on profit (v5.15.2)

**What.** Once position reaches +X% profit, stop-loss ratchets up
to entry price (breakeven) so the position can't turn losing.

**Cfg flags:**
- `breakeven_on_profit=1` (master)
- `breakeven_trigger_pct` — profit % that arms breakeven
- `breakeven_buffer_pct` — small buffer above entry to clear fees

**Fallback.** Disabled → SL stays at original level for full
holding period.

**Where to verify:**
- DashboardPanels position row: SL field updates from original to
  ~entry-price after profit trigger
- TUISnapshot per-slot `sl_armed_breakeven=1` flag
- Slow-path trailing-SL ratchet log entry

**Paper-test sanity:**
1. Enable; open position; watch SL move
2. Position should reach `breakeven_trigger_pct` profit
3. SL displayed in position panel jumps to entry + buffer
4. If price reverses, exit at breakeven (no loss)

---

## Trading mode + live readiness

**What.** Boot gate distinguishes live vs paper. Live-mode strict
defaults (v5.15.4) refuse boot if dangerous configs detected.
/readiness Check 31 audits live-readiness across 31 gates.

**Cfg flags:**
- `trading_mode=paper|live` (default paper)
- `live_mode_strict=1` (v5.15.4; default 1 in live)
- Per-core API key / secret bindings (live only)

**Fallback.** `trading_mode=paper` (default) → no Binance live
order submission; all OMS submits route to paper-fill simulator.

**Where to verify:**
- Boot banner: `[engine] trading_mode=<mode>` line
- DashboardPanels mode tag in title bar (PAPER green / LIVE red)
- /readiness shell command output: GREEN per gate or FAIL
- Live-mode strict refuses cfg with unsafe defaults (e.g.,
  bandit_state from different bundle, model without scaler)

**Paper-test sanity:**
1. Paper run: confirm `[engine] trading_mode=paper` + green PAPER tag
2. Try live boot with deliberate misconfig (e.g.,
   `acknowledge_inference_cfg_drift=0` + cfg drift present); should
   refuse boot
3. /readiness should return GREEN before any live attempt

**Gotchas:**
- live_mode_strict gates are intentionally pessimistic — disable
  per-flag rather than disabling strict mode wholesale
- API secrets must NEVER commit; `secrets.cfg` is workspace-private

**Related:** /readiness skill (Check 31), Boot-time loader, OMS
drainer thread.

---

## Hot-swap model loading (v5.15.4)

**What.** Replace loaded model at runtime without engine restart.
Shadow-loads new model in background, swaps atomically once
verified. Unified entry point in v5.15.4 (was 2 separate paths).

**Cfg flags:**
- `hot_swap_enabled=1` (master)
- `hot_swap_path=<dir>` — watch dir for new model bundles

**Fallback.** Disabled → engine restart required to swap models.

**Where to verify:**
- MLStatusPanel ml_swap_event_count growing on each successful swap
- Slow-path log: `hot-swap accepted role=X horizon=Y` lines
- New bundle in `hot_swap_path` triggers load attempt; result
  visible in next slow-path cycle

**Paper-test sanity:**
1. Boot with model A loaded
2. Drop model B in hot_swap_path
3. Confirm slow-path log: shadow-load → verify → swap accepted
4. Confirm predictions now come from B (different signature)

**Gotchas:**
- New model must pass full stamp verification (feature registry
  hash, cfg drift, scaler binding); failure → swap rejected, old
  model continues
- Per-core swap atomic; cross-core swaps not synchronized (each
  core swaps independently next slow-path cycle).

---

## Multi-horizon training (Trainer panel)

**What.** Train N XGBoost models in one click — one per horizon.
Operator types `Horizons CSV` + optional per-horizon
`TP/SL CSV` + `Label Kind CSV` for heterogeneous outputs.

**UI fields:**
- `Horizons (CSV)` — e.g., `1000,5000,10000`
- `TP Barrier % (CSV)` / `SL Barrier % (CSV)` — broadcast or
  positional
- `Label Kind CSV` — broadcast or positional integer LABEL_*
  codes (tooltip iterates label_table[] live)
- `Training Side` combo — Buy / Exit (routes output to
  `models/<run>/` or `models/exit/<run>/`)
- `Multi-horizon max threads` — default 1 (libgomp landmine; see
  CLAUDE.local.md "Known landmine: XGBoost + libgomp")

**Where to verify:**
- foxml_suite Training panel results table per-horizon
- Output dirs `models/<run_subdir>/<run>_horizon_<N>/role.json`
  (or `models/exit/...` for exit side)
- Each horizon gets `.model + .scaler + .stamp` triplet

**Paper-test sanity:**
1. Type Horizons CSV `1000,5000,10000`
2. Type Label Kind CSV (optional) `0,7,2` for heterogeneous
3. Type TP/SL CSV `0.05` (broadcast) or `0.03,0.05,0.07` (positional)
4. Click `Train Multi-Horizon`
5. Confirm 3 model dirs created with all sidecars + stamps
6. Confirm results table shows per-horizon WF + held-out metrics

**Gotchas:**
- libgomp + pthread parallelism segfault — default
  `multi_horizon_max_threads=1` (serial). Don't raise unless you
  understand the landmine.
- Misaligned CSV counts disable Train Multi-Horizon button.
- Label Kind CSV uses raw `LABEL_*` integer codes; hover tooltip
  for the live lookup table.

**Related:** LabelFunctions.hpp FOREACH_TARGET registry,
Mixed-output normalizer, Exit-side path routing.

---

## NaN-free feature pack (Features_PackAll)

**What.** Single chokepoint validates every feature value before
prediction. Two-layer guard: FPN_IsValidFinite (catches FPN
saturation) + IEEE-754 isnan/isinf post float-cast. Skip cycle on
any failure.

**Cfg flags:** None (always on).

**Fallback.** Sentinel return value `-1` → caller skips prediction;
increments `nan_feature_events_total`.

**Where to verify:**
- MLStatusPanel `nan_feat: N` counter when nonzero (FAIL state)
- TUISnapshot `nan_feature_events_total` per core
- Distinct from `nan_prediction_events_total` (post-Predict NaN)

**Paper-test sanity:**
1. Run normal; counter should stay 0
2. If counter grows: a feature is producing NaN/inf; root-cause
   the feature compute fn

**Gotchas:**
- Pack-time is the load-bearing surface — downstream code trusts
  the pack output. Don't add a separate validation site
  (CLAUDE.md item 14).

---

## Regime detection

**What.** Per-engine classifier feeding strategy dispatch.
Combines slope, R², variance, ror_slope, ema_sma_spread,
book_imbalance, flow EWMA, etc. into trending_score +
volatile_score with hysteresis.

**Cfg flags:**
- `regime_*_threshold`, `regime_hysteresis_*` (multiple)
- `regime_lookback_*` per signal

**Where to verify:**
- DashboardPanels per-core `regime: RANGING|TRENDING|VOLATILE|MILD_TREND`
  badge
- TUISnapshot `regime_signals` debug breakdown per core
- ChartPanel regime bands overlay (when enabled)

**Paper-test sanity:**
1. Run through known regime shift (e.g., flash-crash event in
   historical data); confirm regime tag transitions
2. Hysteresis verification: confirm no rapid flicker on
   borderline thresholds

**Related:** `Strategies/RegimeDetector.hpp`, RegimeSignals
extensibility point (CLAUDE.md data-flow diagram).

---

## Model Health drift surface (v5.15.1)

**What.** PerCoreSnap bitmap surfacing aggregated model health
state per core. Single bitmap field replaces 8+ separate flags
(CLAUDE.md items 20 + 13).

**Cfg flags:** None (always on; observability only).

**Where to verify:**
- MLStatusPanel header banner per core with mixed health states
- TUISnapshot `model_health_flags` bitmap field per core
- `BITMAP_IS_SET(snap.model_health_flags, MASK_*)` for individual
  flag checks

**Related:** TECH_DEBT-028 closure, CLAUDE.md items 13 + 20.

---

## Quick reference — where to look first

When something seems wrong, check these in order:

1. **Boot stderr** — `[engine] ...`, `[ensemble] ...`,
   `[oms] ...` lines tell you what loaded + what was refused
2. **Trading mode banner** — confirm paper vs live
3. **MLStatusPanel per-core** — pred / conf / exit / scaler /
   cfg-drift / drift / halt_reason all live
4. **DashboardPanels** — bandit_probs, position legs, fees
5. **`/readiness` skill** — 31-check audit of live-readiness
6. **Persistence files** — `bandit_state.json`,
   `exit_bandit_state.json`, `ridge_state.json`,
   `thompson_state.json` should grow + sync to disk
7. **Slow-path log** (when verbose enabled) — rebuild cycles,
   ridge solves, hot-swap events
