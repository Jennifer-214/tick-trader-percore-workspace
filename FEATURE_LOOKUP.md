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

## Capital-authority single-source: `trading_mode` (use_real_money retired) (v5.15.5.F.4d.1.E.0.10+)

**What.** `trading_mode` (paper/live/shadow) is THE single capital-authority field — `ControllerConfig_IsLiveCapital(cfg) := (trading_mode==LIVE)`; every authorizer (OMS live bit, secrets/adapter, paper-reset, display mirrors, legacy `main.cpp`) routes through it. The legacy `use_real_money` bool is RETIRED (NEW-1) — it parses as a back-compat ALIAS only.
**Cfg flags.** `trading_mode = paper|live|shadow` (or `0|1|2`). `use_real_money=1` still parses (deprecated) → promotes `trading_mode=live` + a WARN. Legacy single_core LIVE is HARD-REFUSED (the sharded engine is the sole real-money authority).
**Fallback.** Default = paper (safe). SHADOW (=2) is RESERVED/unimplemented → behaves as paper + a boot-WARN.
**Where to verify.** `ControllerConfig.hpp` `ControllerConfig_IsLiveCapital` + the alias resolution in `ControllerConfig_Load`; authorizers at `Run.hpp:577/493`, `Async.hpp:565`, `main.cpp`.
**Paper-test sanity.** `trading_mode=paper` (or unset) → paper. `use_real_money=0` → paper + a one-time deprecation WARN. `use_real_money=1` (no trading_mode) → promotes LIVE + WARN. `use_real_money=1` + explicit `trading_mode=paper` → **boot REFUSED** (contradictory capital config; D-218).
**Gotchas.** The conflict (use_real_money=1 + explicit non-LIVE trading_mode) HARD-REFUSES boot (D-218 — don't silently pick on a capital field; Load sets `live_capital_cfg_conflict` → `main.cpp` returns 1). The tooltip was inverted (now 1=LIVE, 2=SHADOW). HotReload protects `trading_mode` (a cfg reload can't flip capital mid-session). The GUI `use_real_money` checkbox was removed (trading_mode is registry-rendered). **The live-enable HARD gate (torn-read/conc-5 → `.E.1`) is still MISSING** — sharded live is NOT yet blocked on the unresolved race.
**Related.** RBP Class 47 (split-brain control authority); DESIGN_SPEC `single-authority-predicate-for-mode-gating`; D-217 / D-218.

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

### Stamp model CLI binary (framework-driven; v5.15.5.F.4d.1.B.3+)

**What.** `tools/stamp_model_cli` C++ binary (built at `build/stamp_model_cli`) replaces legacy `tools/stamp_model.sh` bash script for offline stamp signing of trained models. CLI uses engine framework API (`stamp_write_for_model`) directly — no bash↔C++ wire format mirror; drift impossible by construction. CLI flag table auto-generated via X-macro walkers from FOREACH_PER_CORE_CFG_FIELD + FOREACH_GLOBAL_CFG_FIELD + FOREACH_ML_CFG_FLAG + FOREACH_GATE_CFG_FLAG + FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG + POST_CFG (~33 CLI flags total). Adding a new cfg field with stamp-binding = 1 row in master registry → `--<field_name>` CLI flag auto-appears at next compile; no manual CLI sync.

**Cfg flags / CLI flags:** All operator-controllable stamp-bound cfg fields auto-flow to CLI flags by registry name (snake_case: `--ridge_lambda`, `--bandit_algorithm`, `--xgb_max_depth`, etc.). Plus hardcoded workflow flags: `--model`, `--secret`, `--wf-mean-val`, `--held-out-metric`, `--gap-threshold`, `--trained-on`, `--format-version`, `--force`. Use `tools/stamp_model_cli --help` for full auto-generated list with per-flag tooltip from registry.

**Fallback / Operator workflow continuity.** `tools/stamp_model.sh` REMAINS at `.B.3+` as a 1-line `exec` deprecation shim → redirects to `build/stamp_model_cli "$@"`. Operator scripts hardcoded to `tools/stamp_model.sh --model X` invocation continue working during retention period. Deletion target tracked via TECH_DEBT-110 (typical retention: 1-2 ship cycles).

**Where to verify:**
- Build target: `build/stamp_model_cli` (added at `CMakeLists.txt` alongside `compare_scalers`)
- HMAC chain identity: `tests/controller_test.cpp` extensibility test (X-macro walker validates per-row round-trip byte-identity)
- Layer 5b structural invariants apply to CLI emit (sister to engine in-process emit; same `populate_stamp_cfg_from_derived` path)
- `tools/stamp_model.sh` deprecation shim: 1-line `exec` + header notice

**Paper-test sanity:**
1. Train a model via `foxml_suite` (in-process Backtest_RunFullValidation)
2. Note metrics (wf_mean_val, held_out_metric, gap)
3. Run `build/stamp_model_cli --model <path> --secret <secret> --wf-mean-val 0.5 --held-out-metric 0.48 --gap-threshold 0.05` to sign
4. Verify `.stamp` produced; load model on engine; verify HMAC + no drift refuse
5. Sanity check: legacy bash-stamped model (pre-`.B.3`) still verifies on `.B.3+` engine (via Decision F SOFT parser back-compat)

**Gotchas:**
- CLI flag names = registry field names (snake_case). Operator scripts using kebab-case bash flags (e.g., `--confidence-threshold-scale`) get a deprecation alias layer with stderr warning during retention period.
- Adding new cfg field with stamp-binding = CLI flag auto-appears at next compile; no manual CLI code edit required.
- `--xgb_min_child_weight` / `--xgb_seed` / `--xgb_train_nthread` exist in BOTH FOREACH_GLOBAL_CFG_FIELD AND FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG at HEAD; CLI binary excludes these from cfg walker (MC walker is authoritative for architectural-constant semantic) via existing `FOREACH_STAMP_RESULT_FIELD_EXCLUSION` sidecar reuse.
- Pinned `LC_NUMERIC=C` (matches engine in-process emit; HMAC byte preservation).
- Engine-downgrade hazard: v2-formatted stamps from `.B.3+` CLI don't load on `.B.2` engine; forward-compat OK, backward-compat requires Decision F parser back-compat at `.B.3+`.

**Related:** DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md v1.1 (Stage 2 DRAFT; Stage 3 first canonical at this binary); DESIGN_SPECS/framework-patterns/cfg-derived-consumer-framework.md v1.3 (extensibility test pattern); TECH_DEBT-110 (shim deletion target); TECH_DEBT-111 (CI defense-in-depth: tools/check_cli_flag_drift.py at 2nd canonical).

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

### Per-horizon TP/SL serving (v5.15.5.A+)

**What:** Multi-horizon ensemble models trained against label-specific
barriers (via v5.13.5 Label Kind CSV + TP/SL CSV inputs) now drive
trade barriers per-horizon at serving time. 5-mode dispatch chooses
which arm's barriers to use (LEGACY = cfg.ml_tp_pct fallback; BLEND
= Σ wᵢ·barrierᵢ; DOMINANT = argmax(weights) arm's barriers;
BOTH_BLEND_DRIVES/BOTH_DOMINANT_DRIVES = one drives + the other
recorded in shadow ring). Cfg-drift Tier 1 promotion catches
silent train-serve barrier miscalibration at strict-mode boot.

**Cfg flags:**
- `barrier_blend_mode` (enum: legacy/blend/dominant/both_blend_drives/both_dominant_drives; default legacy)
- `per_horizon_barrier_blend` (bool master gate; in ml_cfg_flags bitmap; default 0)
- Per-core override: `core_N_barrier_blend_mode=<mode>`
- Existing: `cfg.ml_tp_pct` / `cfg.ml_sl_pct` (legacy fallback values; now also stamp-bound)

**Fallback:** Feature disabled (per_horizon_barrier_blend=0 default) →
bytewise-identical to pre-v5.15.5 behavior. Single-model and non-ensemble
cores unaffected regardless of feature flag.

**Where to verify:**
- MLStatusPanel — `last_buy_dominant_horizon`, `last_barrier_mode_used`,
  `barrier_shadow_event_count` fields per core
- PerCoreSnap: `ml_last_buy_dominant_horizon` (int8_t),
  `ml_last_barrier_mode_used` (uint8_t), `ml_barrier_shadow_event_count` (uint32_t)
- Stamp body: 4 new entries `inference_cfg_ml_tp_pct/_ml_sl_pct/_barrier_blend_mode/_per_horizon_barrier_blend`
  on ModelHandle + parser

**Paper-test sanity:**
1. Train ensemble with multi-horizon labels (Label Kind CSV)
2. Set `per_horizon_barrier_blend=1` + `barrier_blend_mode=dominant`
3. Run paper-mode; observe dominant_horizon updating
4. Modify cfg.ml_tp_pct mid-run, restart with `model_verify_strict=1` →
   boot REFUSES with Tier 1 drift message
5. Set `acknowledge_inference_cfg_drift=1` → loads with WARN

**Gotchas:**
- Tier 1 REFUSE in strict mode catches train-serve calibration drift
- `acknowledge_*_drift` cfg flags migrated to `ops_cfg_flags` bitmap
  at v5.15.5.A.7 (legacy keys still parse for backward-compat)
- Legacy pre-v5.15.5 stamps + feature ON → triggers drift (intentional;
  parity violation surface)

**Related:** CLAUDE.md items 13/15/19/20/21/23; DESIGN_SPECS
`dual-axis-y3-dispatch-pattern.md`, `stamp-vs-runtime-drift-detection-registry.md`,
`autopopulate-pattern-for-production-caller-class.md` (3rd application);
TECH_DEBT-037 + -009 boolean-tail CLOSED.

---

### Corrupt-model detection + per-node majority-SHALT (v5.15.5.F.4d.1.E.0.10 / A6 INGRESS)

**What:** A model whose serving barrier is CORRUPT — `label_tp_pct`/`label_sl_pct` that is NaN, +Inf, negative, or beyond a sane percentage cap — is DETECTED AT LOAD and refused per-arm. A single corrupt arm in an ensemble is DROPPED (the node trades on the survivors); when a MAJORITY of arms are corrupt the whole node SHALTs (refuses to open new positions) and raises a sticky "model: CORRUPT — RETRAIN" health alert. This is DISTINCT from a MISSING model (no artifact on disk → degrades to SimpleDip): a corrupt artifact is more alarming than an absent one (it implies tampering or a broken trainer), so the response is refuse-to-trade + retrain, NOT a silent strategy swap. A trainer-emit floor refuses to STAMP a corrupt model in the first place (the upstream sister to the load-time refuse). The A6 EGRESS half (prior) clamps a corrupt barrier at emit-time + `SHALT_BAD_PCT`; the INGRESS half (this entry) detects + refuses + surfaces at load.

**Cfg flags:**
- `model_corrupt_shalt_ratio` (FPN_Binary<F>, KIND_DOUBLE; default **0.5** = simple majority; range [0,1]; "Drift Acknowledgments" group; WARN_ON_CLAMP) — the corrupt-arm fraction at/above which the node SHALTs. 0.5 = "more than half the arms corrupt → refuse." Set lower to SHALT sooner (more conservative); 1.0 = SHALT only when ALL arms corrupt. `CoreFrameworks/CfgFieldRegistry.hpp`.
- No per-core override (global cfg). The per-arm DROP is unconditional (always drops a poisoned arm regardless of the ratio).

**Fallback:** Single corrupt arm → that arm disabled (unioned into `disabled_horizon_mask`); node trades the survivors. Majority corrupt → whole-node SHALT (every cycle emits BUY_BLOCKED for that core via the egress veto path; existing positions NOT force-closed — block-new-only). Fully-corrupt single-zoo (non-ensemble) model → SHALT. Trainer floor → a corrupt stamp write returns `ok=0` (the model never reaches an engine).

**Where to verify:**
- CoreState bit `MODEL_CORRUPT` (bit 5; `MASK_CORE_STATE_MODEL_CORRUPT`) — distinct from `MODEL_LOAD_FAILED` (bit 2, the missing-model path).
- SHALT code `SHALT_MODEL_CORRUPT` (=19) on the blocked gate.
- Failure mode `ml_model_corrupt` (SEV_RED) → `GUI/MLStatusPanel.hpp` red "model: CORRUPT — RETRAIN" banner (rendered before the load_failed branch).
- Per-arm bitmap `corrupt_arms_mask` on `EnsembleModelZoo<F>` (set in `ezoo_set_per_arm_barrier`, `CoreModelZoo.hpp`); the majority verdict in `EnsembleZoo_FinalizeCorrupt<F>` (called at boot in `EngineCommon.hpp` + at hot-swap in `EngineSharded/Run.hpp`).
- The SSoT predicate `tt::barrier_is_corrupt(tp,sl)` (`ML_Headers/BarrierValidation.hpp`) — ONE function called by the load validate, the trainer floor (`StampHelper.hpp`), AND the char-tests.
- The snapshot surfaces `ml_model_corrupt` whenever ANY arm is corrupt (`ShardedSnapshot.hpp`), even sub-majority (a single dropped arm stays operator-visible before it escalates to a SHALT).

**Paper-test sanity:**
1. Train an ensemble (multi-horizon labels); confirm it loads + trades normally.
2. Hand-corrupt ONE arm's `label_tp_pct` in the stamp to `nan` (or a value > 10.0) → reload → observe the arm-drop (the `corrupt_arms_mask` bit + the `ml_model_corrupt` health surface) but the node STILL trades on the survivors.
3. Corrupt a MAJORITY of arms (> `model_corrupt_shalt_ratio` × n_arms) → reload → observe the node SHALT (BUY_BLOCKED every cycle) + the sticky red "RETRAIN" banner.
4. Try to STAMP a corrupt model from the trainer → observe the emit floor refuses (`ok=0` + WARN), so the corrupt artifact never lands.

**Gotchas:**
- SANE caps are SEPARATE per side + are PERCENTAGES (fractions), NOT prices: `BARRIER_SANE_MAX_SL = 1.0` (100% — a stop beyond your whole stake is nonsense), `BARRIER_SANE_MAX_TP = 10.0` (1000% — generous, asymmetric on purpose). Equity-agnostic: BTC over $100k is irrelevant; the barrier is a percentage of the position, not a price.
- `0.0` is a LEGITIMATE barrier value, NOT corrupt (the predicate rejects `< 0`, not `<= 0`).
- `< 0` ALONE misses NaN/+Inf (they round-trip the stamp via `%.6g` / `parse_double_fast`) — the predicate uses `!isfinite || < 0 || > cap`.
- The load validate + the trainer floor call the SAME `barrier_is_corrupt` predicate (no parallel reimplementation → they CANNOT drift; this two-seam-one-predicate guarantee is the SSoT — guard it: a future edit must not fork the predicate). This is why there is NO train↔serve PARITY entry — the surface is parity-safe-by-construction.
- Block-new-only: a SHALT refuses to OPEN; it does not force-close existing positions (a single position per node makes this low-risk).

**Related:** D-220 (the SHALT-vs-degrade policy) + D-221 (the ingress reshape) in the `.E`-architecture-v2 decision log; TECH_DEBT-198 (label_*_pct 3-convention unit hazard) / -199 (SANE_MAX hard-cap-vs-configurable + bit-pack) / -201 (MLBuildContext MODEL_HEALTH bitmap consolidation); RBP Class 49; the A6 EGRESS half (`SHALT_BAD_PCT`, `GateParameters_FinalizeEmit`); the "Per-horizon TP/SL serving" surface above (the barrier values A6 guards); `single-source-of-truth-discipline.md` (the `barrier_is_corrupt` SSoT).

### Blanket live-capital boot-gate — live trading REFUSED until the `.E`-series lands (v5.15.5.F.4d.1.E.0.10 / Phase-D)

**What:** Until the `.E`-series live-readiness rework (per-node aggregator + reconciliation + the cross-thread torn-read closure) lands, the engine REFUSES to boot in live-capital mode. `LiveReadiness_Verify` carries a blanket REFUSE check (`check_live_capital_gated_until_e`, the first `FOREACH_LIVE_READINESS_CHECK` row) that FAILS whenever live capital is requested — routed through the single capital-authority predicate `ControllerConfig_IsLiveCapital` (RBP Class 47). Fail-safe by design: accidental live trading on the pre-`.E` engine is made impossible. paper + shadow boot normally (both capital-FALSE).

**Cfg flags:** none new — keys off the existing `trading_mode` (`paper`|`live`|`shadow`). By design there is no way to set `trading_mode=live` and boot until v5.16.

**Fallback:** none — a deliberate hard gate (`LR_SEV_REFUSE`). Boot stderr prints the reason + fix hint. Use `trading_mode=paper` (or `shadow`).

**Where to verify:** `CoreFrameworks/LiveReadiness.hpp` (`check_live_capital_gated_until_e` + the `FOREACH_LIVE_READINESS_CHECK` row + the `H21 TOMBSTONE` comment). Boot a `trading_mode=live` cfg → `[live_readiness] LIVE REFUSE: live_capital_gated_until_e failed` + `LIVE REFUSED … engine will NOT start`. Tests: controller_test `.E.0.10 Phase-D` (live→refuse / paper+shadow→pass / count==10).

**Paper-test sanity:** paper/shadow boot unaffected (the gate passes silently). A `live` cfg refuses at boot (`LiveReadiness_Verify` returns -1) BEFORE any order/adapter path.

**Gotchas:** REMOVED at v5.16 when live-readiness lands (H21 tombstone; **TECH_DEBT-203**) — do NOT assume it's permanent, and do NOT silently leave it (it would block the intended go-live). Until then "live" is structurally unavailable — intentional, not a bug.

**Related:** A6 corrupt-model SHALT (above — the other `.E.0.10` capital guard); NEW-1 `ControllerConfig_IsLiveCapital` (RBP Class 47, the predicate it routes through); the `.E.1` live-readiness completion; D-77/F-2 + D-168.

---

### Cfg-drift detection (v5.15.5.A.7 structural refactor)

**What:** Stamp ↔ cfg drift detection via FOREACH_CFG_DRIFT_CHECK
X-macro registry walker. 18 entries (8 cross-binary WARN + 6
inference_cfg Tier 1/2 + 4 v5.15.5.A.7 per-horizon barrier cohort).
Tri-axis Y3 dispatch (severity × category × compare_kind). REFUSE
in strict + Tier 1; WARN otherwise. Per-category drift bits on
ModelHandle.drift_flags_at_load.

**Cfg flags:**
- `acknowledge_inference_cfg_drift` (operator suppress; ops_cfg_flags bitmap)
- `acknowledge_cross_binary_version_drift` (operator suppress; ops_cfg_flags bitmap)
- `held_out_gate_strict=1` triggers REFUSE on Tier 1 drift (LIVE-mode default)

**Where to verify:**
- Boot stderr: `[cfg-drift] <category> <severity>: core N role=X stamp.<field>=<val> cfg.<field>=<val> — <doc>`
- PerCoreSnap.failure_flags bits: `cfg_binding_drift`, `cfg_cross_binary_drift`
- MLStatusPanel Model Health surface (auto-aggregates per-category bits)
- CoreContext counters: `cfg_drift_tier1_count`, `cfg_drift_tier2_count`, `cfg_drift_strict_refused`

**Gotchas:**
- Per-category fail_mask shared across entries in same category
  (uint16_t failure_flags headroom forces per-category granularity)
- Surface G forward-compat: legacy stamps without new fields → has_*=0
  → drift check skips silently (no MODEL_FORMAT_VERSION bump)
- Adding a new drift check = 1 row in FOREACH_CFG_DRIFT_CHECK; future
  per-entry granularity requires uint32_t widening (not yet justified)

**Related:** CLAUDE.md items 13/15/17/19/20/23; DESIGN_SPECS
`stamp-vs-runtime-drift-detection-registry.md`,
`template-deferred-dependency-injection.md` (3rd application);
sister narrow variant `MemHeaders/ArchFieldDriftRegistry.hpp` (v5.15.1).

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

---

### paper-reset archive flow (v5.15.5.C.3+)

**What:** When operator triggers "Reset Paper" in paper mode, the prior session's state is captured into a timestamped archive directory BEFORE the OMS resets. Each archive contains a full snapshot + trade-log copy + summary.json, enabling date-range session review + per-strategy aggregation across completed sessions.

**Cfg flags:** None — paper-reset archive is always-on for paper mode (no operator opt-out; cost bounded — fopen + ~few MB write per reset; reset events rare).

**Fallback:** If `data/paper_resets/` mkdir fails (disk full, permission denied), CRITICAL message logs to stderr and the reset proceeds WITHOUT archive. Production behavior unaffected; OMS_RESET_AUTOPOPULATE wipe always succeeds.

**Where to verify:** After triggering "Reset Paper":
- `ls -la data/paper_resets/` — new dir named `{start_iso}_to_{end_iso}.paper/`
- `data/paper_resets/{dirname}/snapshot.dat` — full ShardedSnapshot_Save (binary)
- `data/paper_resets/{dirname}/trades.csv` — copy of `logging/SYMBOL_order_history.csv` at reset time (aggregate)
- `data/paper_resets/{dirname}/trades/core_<N>.csv` — Phase 5.B+ per-core mirror copies (1 file per execution core that had trade activity; `<dirname>/trades/` subdir created at archive time)
- `data/paper_resets/{dirname}/summary.json` — JSON with 5 sections: `session` / `global` / `per_core[]` / `per_strategy[]` / `per_regime[]` (per_regime empty `[]` placeholder; per-regime aggregation is a separate follow-up — Phase 5.B per-core CSV split shipped 2026-05-13 but it splits BY CORE, not by regime; per-trade regime data is in `regime` + `regime_name` columns of every CSV)
- Engine stderr: `[archive] paper-reset session archived: <dirname>`

**Paper-test sanity:**
1. Run engine in paper mode ≥ 1 minute (let trades fill).
2. Click "Reset Paper".
3. Verify `data/paper_resets/` has new directory.
4. `cat .../summary.json | jq` — pretty-prints 5 sections.
5. Verify `summary.json.global.balance_end` matches balance immediately before reset.
6. Verify `summary.json.per_core[].entries` array length == num_cores.

**Gotchas:**
- Archive dirname uses ISO `YYYY-MM-DD-HHMMSS` format. Same-second resets would collide.
- `paper_session_start_us` is captured BEFORE OMS_RESET_AUTOPOPULATE wipes it. Layer ordering documented at EngineSharded.hpp paper-reset block.
- `trades.csv` is a COPY (not rename) — live trade log unaffected; `ShardedTradeLog_Rotate` creates its own `logging/`-side backup separately. 2 trade-log copies per reset (aggregate + per-core); acceptable cost.
- Per-core archive copies (`trades/core_<N>.csv`) added v5.15.5.C.3 Phase 5.B (2026-05-13). Per-core source filename built via `ShardedTradeLog_FormatPerCoreFilename` (same helper used by `_Init` + `_Rotate`); local `copy_file` lambda deduplicates the aggregate + per-core fread/fwrite loops.
- `per_regime[]` is still empty after Phase 5.B (per-core CSV split splits BY CORE, not by regime). A per-regime aggregator that scans the trades.csv `regime_name` column post-archive is a separate follow-up. Per-trade regime data IS in the CSV (Phase 5.A added `regime` + `regime_name` columns).

**Related:** `OmsFieldRegistry.hpp` (paper_session_start_us field), `PaperResetArchive.hpp` (Summary_WriteJson + dirname/mkdir helpers), `CoreCtxSummaryFieldRegistry.hpp` (per_core + per_strategy emission), `EngineSharded.hpp` paper-reset block (orchestration), `ShardedTradeLog.hpp` (per_core_files[] + helpers; Phase 5.B), TECH_DEBT-045 (Phase 7.B integration tied to bench gate, not paper-reset).

---

### per-core trade log mirror files (v5.15.5.C.3 Phase 5.B+)

**What:** Each fill row in the trade log is written to BOTH the aggregate `logging/SYMBOL_order_history.csv` (GUI/TradeReader reads this; unchanged) AND a per-core mirror file `logging/SYMBOL_core_<N>_order_history.csv` (N = 0..MAX_EXECUTION_CORES-1). Per-core files enable per-core trade analysis without parsing the aggregate. Per-core file is selected by the fill event's `core_id`.

**Cfg flags:** None — per-core mirror is always-on (no operator opt-out; cost bounded — 1× extra fwrite per fill event on slow-path drainer thread). MAX_EXECUTION_CORES = 16 caps the file count well under any FILE* limit.

**Fallback:** If a per-core file fails to open (mkdir issue, fd exhaustion), its slot in `per_core_files[c]` stays nullptr; subsequent fills with that core_id skip the per-core write. Aggregate file always serves the trade log — failure is silent + non-fatal. The aggregate file is the canonical source for any consumer that does not need per-core breakdown.

**Where to verify:**
- `ls -la logging/SYMBOL_*` after a paper-test session — should show 1 aggregate + N per-core files (assuming N cores fired ≥ 1 fill each)
- `head -2 logging/SYMBOL_core_0_order_history.csv` — first line `# v3 sharded engine (per-core mirror; core=0) ...`; second line column header
- `awk -F, 'NR>2 && $2==0' logging/SYMBOL_order_history.csv | wc -l` (rows where core_id column = 0) should match `tail -n+3 logging/SYMBOL_core_0_order_history.csv | wc -l`
- Tests: `tests/controller_test.cpp` "v5.15.5.C.3 Phase 5.B" block (8 tests covering Init opens all per-core files, RecordEntry mirrors to correct per-core file, per-core file isolation, aggregate completeness)

**Paper-test sanity:**
1. Run engine in paper mode ≥ 5 minutes (let trades fill across multiple cores).
2. `ls -la logging/SYMBOL_*` — 1 aggregate + ≥ 1 per-core file visible.
3. `head -3 logging/SYMBOL_core_0_order_history.csv` — # comment header + column row + first fill (event_type=E or X, core_id=0).
4. Spot-check: pick any per-core file N; verify every row's `core_id` column equals N (`awk -F, 'NR>2 && $2!=N' file` should print 0 rows).
5. Aggregate completeness: row count of aggregate (minus 2 header lines) should equal sum of all per-core rows (minus 2 header lines per per-core file).
6. Trigger "Reset Paper" — verify `data/paper_resets/<dirname>/trades/core_<N>.csv` per-core archive copies created alongside `<dirname>/trades.csv`.

**Gotchas:**
- Per-core files are append-mode (`fopen("a")`) — re-running the engine appends to existing per-core CSVs unless deleted or rotated. Matches the aggregate file behavior.
- `ShardedTradeLog_Rotate` (Reset Paper trigger) renames both aggregate AND all per-core files with the same `YYYYMMDD-HHMMSS` timestamp suffix.
- Per-core files are bounded at MAX_EXECUTION_CORES (16). If the engine is configured for fewer cores (e.g., 4), the extra per-core files exist but stay empty (header-only) — best-effort fopen but no writes.
- Future operator scripts that read `logging/` should treat per-core files as ADDITIVE — the aggregate file remains the canonical trade history.
- Per-core filename + write are both routed through helpers (`ShardedTradeLog_FormatPerCoreFilename` + `ShardedTradeLog_WriteRow`). Adding a new RecordX function (e.g., `RecordPartialFill`) MUST call `ShardedTradeLog_WriteRow` to maintain mirror discipline — closes Class-18 mirror at the dual-write level structurally.

**Related:** `ShardedTradeLog.hpp` (struct + 2 NEW helpers Phase 5.B; RecordEntry / RecordExit delegate to WriteRow), `EngineSharded.hpp` paper-reset archive (per-core copy block; local `copy_file` lambda; uses `FormatPerCoreFilename`), `TradeLogColRegistry.hpp` (FOREACH_TRADE_LOG_COL — same column shape for both aggregate + per-core files), paper-reset archive flow entry above (per-core files are mirrored into `<dirname>/trades/`).

---

### runtime bench gate cfg flag (v5.15.5.C.3+; substrate only, Phase 7.B integration pending)

**What:** Operator-facing cfg flag `oms_bench_enabled` that will (in Phase 7.B follow-up) enable runtime per-cycle latency histograms via boot-time template dispatch. Today (Phase 7.A) the flag is shipped as substrate — cfg field is parsed + defaulted to 0, `LatencyHistogram.hpp` primitive is available — but NO instrumented sites are wired yet.

**Cfg flags:**
- `oms_bench_enabled=0` (default; production; zero cost when off via Phase 7.B compile-time elision)
- `oms_bench_enabled=1` (bench mode; Phase 7.B integration pending; flag has NO observable effect today)

**Fallback:** N/A (cfg flag has no behavior wired yet).

**Where to verify (Phase 7.A only):**
- `cfg.oms_bench_enabled` field accepts `oms_bench_enabled=1` in engine.cfg
- ControllerConfig_Default sets to 0 (verified in test block)
- `LatencyHistogram.hpp` primitive: bucket index, Reset, Accumulate, Percentile all unit-tested

**Paper-test sanity (Phase 7.A only):** Flag has no observable effect. Phase 7.B adds:
- TUI/stderr line `[OMS_BENCH] tick p50=...ns p99=...ns max=...µs` per snapshot publish
- Per-cycle measurement via `__rdtsc` at 3 instrumented sites (OMS_Tick / OMS_DrainSubmit / DrainPostFill)

**Gotchas:** Phase 7.A is SUBSTRATE only. Flag flip has no observable effect TODAY. Phase 7.B integration tracked as `TECH_DEBT-045`.

**Related:** `MemHeaders/LatencyHistogram.hpp` (primitive), `ControllerConfig.hpp` (cfg field + parser), `DESIGN_SPECS/feature-patterns/runtime-toggleable-bench-gate-pattern.md` (full design + 7 composition options), TECH_DEBT-045 (Phase 7.B trigger ledger).

---

## Universal cfg field registry (v5.15.5.F.4b+)

**What.** Single-source-of-truth registry (`FOREACH_CFG_FIELD` in
`CoreFrameworks/CfgFieldRegistry.hpp`) for cfg field declarations. Initial
KIND_DOUBLE/_PCT cohort: ~40 fields (`take_profit_pct`, `stop_loss_pct`,
`fee_rate`, `risk_pct`, `regime_*`, `momentum_*`, `emacross_*`, `ml_*`,
`bandit_blend_ratio`, etc.). Adding a NEW cfg field of these kinds = **ONE
row** in `FOREACH_CFG_FIELD`; parser + GUI render + tooltip + per-core override
emission all auto-flow from that single row. Closes the panel_gap +
parser_gap + persist_gap classes structurally (3-barrier fix for
DOCS/RECURRING_BUG_PATTERNS.md Class 23).

**Cfg flags.** Registry rows have 12-col Option D tuple:
`(KIND, name, label, section, metadata_flags, payload, tooltip,
applies_to_strategy_cat, applies_to_op_mode_cat, applies_to_regime_cat,
applies_to_risk_cat, lives_in_struct)`. Metadata flags include
`PER_CORE_OK`, `RESTART_REQUIRED`, `SAFETY_CRITICAL`, `STAMP_BOUND`,
`HIDDEN_BY_DEFAULT`, `IS_SECRET`, etc.

**Fallback.** Manual `CFG_PARSE_FPN/PCT/U32/INT` macros in
`ControllerConfig_Load<F>` body remain for fields NOT yet in registry
(KIND_INT/_BOOL/_STRING migrate at .F.4c/.F.4d). Manual `field_defs[]`
entries in `GUI/SettingsPanel.hpp` remain for non-migrated fields.
Coexistence is safe — registry walk uses `continue;` so manual fallback
handles unknown keys.

**Where to verify (operator runtime):**
- Boot: registry-driven parser runs at start of `ControllerConfig_Load<F>`
  body (`CoreFrameworks/ControllerConfig.hpp:1873-1903`). Any KIND_DOUBLE/_PCT
  cfg field is parsed via `tt::cfg_parse_field<T>` (type-safe + locale-immune
  via `parse_double_fast`).
- GUI: Settings tab in `foxml_suite` shows the auto-extended cfg fields with
  correct label / section / tooltip. Hand-tuned multi-line tooltips for
  `fee_rate`, `regime_crossover_threshold`, `regime_strong_crossover` etc.
  preserved byte-identical from pre-v5.15.5.F.4b.
- Tests: `tests/controller_test.cpp:test_v5_15_5_F4b_cfg_field_dispatch()` —
  10 PASS runtime tests verify roundtrip, locale-immunity, CI Test 2
  (applies_to_strategy_cat != 0), tooltip preservation. Plus 8 compile-time
  static_asserts for trait correctness + bitmap overflow guards. Run
  `./build/controller_test` → see `[v5.15.5.F.4b CfgFieldRegistry + tt::
  dispatch]` block.
- Compile-time: `static_assert(sizeof(CfgFieldDescriptor) <= 128)` + 3
  bitmap overflow guards (`MetadataFlag`, `StrategyCategory`, `OpModeCategory`).

**Paper-test sanity:** Edit any migrated cfg field (e.g., `take_profit_pct`)
in `foxml_suite` Settings tab; click Save; verify new value persists in
`engine.cfg` (per-field text-splice via `cfg_write_field` preserves operator
comments). Restart engine; verify value loads back correctly via boot log
cfg dump.

**Gotchas.**
- Tooltip preservation is for **migrated fields only** (~14 hand-tuned
  multi-line tooltips byte-identical). New cfg fields added via registry
  get author-supplied tooltips; refine via direct registry edit.
- Format strings: KIND_DOUBLE_PCT renders/saves with `%.2f`; KIND_DOUBLE
  with `%.4f`. Pre-migration some fields used `%.1f` / `%.5f` / `%.6f` —
  minor display precision shift (always RICHER decimals, not poorer).
- **The 3-barrier structural fix means NEVER use** `*reinterpret_cast<T*>((char*)cfg + offset) = v`
  style dispatch. See `DOCS/RECURRING_BUG_PATTERNS.md` Class 23 +
  `DESIGN_SPECS/framework-patterns/type-trait-dispatch-via-tt-namespace.md` for canonical antidote.

**Related:**
- `CoreFrameworks/CfgFieldRegistry.hpp` (registry + descriptor + bitmap overflow asserts)
- `CoreFrameworks/CfgFieldDispatch.hpp` (tt:: parse + save with locale pinning)
- `Strategies/StrategyCategories.hpp` + `Strategies/OpModeCategories.hpp` (categorical applicability enums)
- `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md` (full pattern spec)
- `DESIGN_SPECS/framework-patterns/type-trait-dispatch-via-tt-namespace.md` (3-barrier antidote)
- `DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md` (applies_to_*_cat columns)
- `DESIGN_SPECS/framework-patterns/registry-tuple-as-single-source-of-truth.md` (12-col Option D)
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 23 (3-barrier structural fix), Class 14 (plan-API-drift 4th recurrence)
- CLAUDE.md item 23 (type-trait dispatch), item 19 (structural fix preferred), item 13 (X-macro registry)
- CLAUDE.local.md going-forward rule "Type-trait dispatch via tt:: namespace" (2026-05-14)
- TECH_DEBT-009 (full KIND coverage migration; .F.4c+ for INT/BOOL/STRING; .F.4i for backtest cfg; v5.15.6 for controller/secrets/training cfg)

### v5.15.5.F.4c extension — Bitmap dispatcher framework + Option 2 GUI refactor

**What landed at v5.15.5.F.4c:**

1. **Bitmap dispatcher framework** (`CoreFrameworks/CfgFieldRegistry.hpp:297+` `[BITMAP DISPATCHER FRAMEWORK]` section): per-metadata-bit constexpr `CfgMaskArray` masks via `FOREACH_METADATA_BIT(X)` X-macro (12 bits) + per-LivesInStruct-value masks via `FOREACH_LIVES_IN_STRUCT(X)` (5 values; forward-compat for ML/training/backtest cohorts) + 5 composed view masks (`g_cfg_render_mask`, `g_cfg_save_mask`, `g_cfg_stamp_emit_mask`, `g_cfg_cli_explain_mask`, `g_cfg_per_core_override_mask`). All `inline constexpr`; lands in `.rodata`; compile-time computed (zero runtime init cost). `g_cfg_field_descriptors[]` promoted `inline const` → `inline constexpr`.

2. **Iteration + stats helpers**: `CFG_FIELD_FOR_EACH_SET_BIT(mask, idx, body)` branchless iteration macro (uses `__builtin_ctzll` single TZCNT instruction); `cfg_field_count(mask)` constexpr popcount for one-shot stats.

3. **tt:: dispatch quintet completed**: `tt::cfg_parse_field<T>` (extended with INT_ENUM strcasecmp string-token + warn-on-invalid + WARN_ON_CLAMP emission + KIND_BOOL truthy-int normalization), `tt::cfg_save_field<T>` (KIND_BOOL 0/1 normalized save), `tt::cfg_assign_field<T>` NEW (sets cfg field from descriptor default), `tt::cfg_diff_field<T>` NEW (current vs default comparison), `tt::cfg_render_field<T>` (lives in `GUI/SettingsPanel.hpp` ns tt — ImGui dispatch via type-trait; INT_ENUM→Combo, BOOL→Checkbox, INT→SliderInt, FPN→SliderFloat).

4. **2 new metadata bits** added to existing 10: `HAS_SIDE_EFFECT` (1<<10; registry walker skips parse for tagged rows; manual block keeps logic), `WARN_ON_CLAMP` (1<<11; emits operator-clarity warning when parse clamps value or KIND_BOOL non-{0,1}).

5. **Option 2 SettingsPanel refactor** (Settings_RenderGlobalTab uses bitmap-dispatch walker via `CfgRenderTable<F>::fns[idx]` calling `cfg_render_and_persist<T>`; `gui_engine_cfg` typed mirror REPLACES parallel-array indirection for scalar Kinds; field_defs[] retains entries only for STRING/FILE_PATH bridge + hardcoded special-case fields).

6. **63 cohort migrations** to `FOREACH_CFG_FIELD`:
   - C1 (15 KIND_BOOL): operational + safety toggles
   - C2 (17 KIND_INT): lifecycle / cooldown / persistence (HIGH-6 tooltip byte-identity preserved for 9 fields)
   - C3 (18 KIND_INT): ML / training BOOT_ONLY params (thompson_rng_seed tagged HAS_SIDE_EFFECT — hex parsing preserved in manual parser)
   - C4+C5 (13 KIND_INT migrations + 4 HAS_SIDE_EFFECT registry rows): notify / health / reconcile / operational

7. **4 HAS_SIDE_EFFECT registry-only rows** (in registry for documentation/CLI surfaces; walker skips parse): `reconcile_mode` (string FromString + cfg_keys_explicit + reconcile_dry_run mirror), `engine_mode` (string FromString), `engine_arch` (string FromString), `model_verify_strict` (cfg_keys_explicit bit for NormalizeForMode flip rule).

8. **Test additions**: `tests/controller_test.cpp:test_v5_15_5_F4c_cfg_field_dispatch` — 12 sub-tests T7-T18 covering KIND_INT/_BOOL parse/save/clamp dispatch + bitmap framework popcount/iteration + composed mask correctness + cfg_assign/diff sisters + HIGH-6 tooltip preservation + registry size sanity + tooltip-byte-count stability. Total: 3144 tests (was 3118; +26 sub-tests).

**Deferred to follow-up ships** (captured as TECH_DEBT or noted in plan body):
- Per-core override path refactor (sister-pattern walker via `g_cfg_per_core_override_mask` consuming `PerCoreOverrides` typed mirror)
- Reset-to-defaults + Modified-badge GUI consumers (framework support shipped; just needs UI button wiring)
- `use_real_money` custom render hook (REAL MONEY warning label needs post-render-hook mechanism design; sidecar override pattern candidate)
- `reconcile_dry_run` HAS_SIDE_EFFECT + DEPRECATED tagging (~10 LOC follow-up)
- ML enum X-macro registries per TECH_DEBT-068 (promotes KIND_INT → KIND_INT_ENUM for `ml_backend` / `regime_model_backend` / `confidence_ic_variant` / `csv_sort_check_mode` / `reconcile_mode` / `ensemble_blend_mode`)
- Constexpr promotion sweep per TECH_DEBT-069 (operator-directed timing: end of `.F` umbrella)

**Related (.F.4c-specific):**
- `DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md` (NEW; Stage 2 DRAFT v1.0) — codifies the pattern; first canonical application is this ship; future applications outlined for stamp emit / drift check / CLI subcommands / per-core observability
- CLAUDE.md item 31 (Framework-driven extensibility meta-principle); H14 (manual bit-packing only — codified this ship)
- CLAUDE.local.md going-forward rule "GUI ↔ HP/SP thread isolation" (codified this ship)
- TECH_DEBT-063 (field_defs[] elimination — progressed 80% → 95% at `.F.4c`; closes at `.F.4e`)
- TECH_DEBT-064 / 065 / 066 / 067 / 068 / 069 (all NEW this ship; headless deferral + observability roadmap + ML enum registries + constexpr sweep)


### v5.15.5.F.4d MERGED extension — Bandit/Thompson 5-state + Pattern 5 path consolidation + 47-col calib log + 3 TECH_DEBT fold-ins

**What.** Comprehensive bandit/thompson cohort migration + framework foundation + 3 TECH_DEBT fold-ins shipped at v5.15.5.F.4d MERGED (2026-05-16; engine commit `545b087` + GPG-signed tag `v5.15.5.F.4d`).

**Operator-affecting changes:**

1. **5-state bandit_algorithm enum** (was 3 states pre-`.F.4d`). New states:
   - cfg=0 EXP3 — UNCHANGED (legacy default; Exp3-IX only; Thompson posterior frozen)
   - cfg=1 THOMPSON — **Class 24 fix**: pre-`.F.4d` Thompson posterior NEVER updated despite this setting; post-`.F.4d` Thompson_Update wires correctly via g_buy_reward_dispatch
   - cfg=2 EXP3_OP_THOMPSON_GHOST — was 'BOTH' pre-`.F.4d`; legacy 'Both'/'BOTH' string aliases preserved; semantic = Exp3 drives chosen_arm + Thompson shadow-learns from per-arm reward signal
   - cfg=3 THOMPSON_OP_EXP3_GHOST — NEW; mirror of cfg=2 (Thompson drives + Exp3 shadow-learns)
   - cfg=4 BLENDED — NEW EXPERIMENTAL; weighted blend via thompson_exp3_blend_alpha cfg knob (default 0.5 = 50/50 Exp3↔Thompson softmax)

2. **NEW cfg field: thompson_exp3_blend_alpha** (FPN<F>; per-core; default 0.5; range [0.0, 1.0]). Only meaningful when bandit_algorithm=4 BLENDED. GUI should grey-out otherwise. Stamp-bound (parity-critical; reproducibility requires α locked to training-time value).

3. **47-col calibration log** (was 9-col pre-`.F.4d`). New columns appended after legacy 9:
   - 6 bandit-context singletons: bandit_algorithm, regime_id_at_emit, chosen_arm, reward_bps_attributed, thompson_telemetry_arm, thompson_exp3_blend_alpha
   - 32 per-arm cols: 8 arms × {exp3_w_armN, thompson_mu_armN, thompson_prec_armN, thompson_pulls_armN}
   - Legacy 9-col prefix UNCHANGED (operator parsers depend on byte order for first 9 fields).
   - Non-ML cores OR null-ezoo cores emit 0.0/0u placeholders for new cols (row format byte-stable).

4. **Persistence file path rename** (TECH_DEBT-084 cascade rename close):
   - `<model_dir>/thompson_state.json` → `<model_dir>/buy_thompson_state.json` (Save writes new name)
   - `<model_dir>/thompson_exit_state.json` → `<model_dir>/exit_thompson_state.json` (Save writes new name)
   - **Load-side back-compat alias**: existing on-disk model bundles with legacy names load cleanly (Load tries new name first, falls back to legacy)
   - **Operator action: NONE for existing models** (back-compat alias handles it); new model saves use new names

5. **3 .F.5 residual fields now per-core** (TECH_DEBT-082 close):
   - `lazy_rebuild_price_threshold_pct` — was global; now per-core via `core_N_lazy_rebuild_price_threshold_pct=<val>` syntax (or global `lazy_rebuild_price_threshold_pct=<val>` propagates to all cores via shadow walker until `.F.4f` cleanup)
   - `exit_threshold` — was global; now per-core via `core_N_exit_threshold=<val>` syntax
   - `confidence_ic_floor` — was global; now per-core via `core_N_confidence_ic_floor=<val>` syntax

**Cfg flags (new at `.F.4d`):**
- `bandit_algorithm=0|1|2|3|4` or string form: `EXP3`/`THOMPSON`/`EXP3_OP_THOMPSON_GHOST`/`Both`/`BOTH`/`THOMPSON_OP_EXP3_GHOST`/`BLENDED` (case-insensitive; legacy aliases preserved)
- `thompson_exp3_blend_alpha=<0.0..1.0>` (only consumed when bandit_algorithm=4)
- Plus the 3 newly-per-core fields above

**Fallback:** All defaults pre-existing — bandit_algorithm=0 (legacy EXP3) preserved; thompson_exp3_blend_alpha=0.5 default unused unless cfg=4 BLENDED; per-core fields fall back to global setting via shadow walker.

**Where to verify:**
- **Settings panel** (GUI) — bandit_algorithm dropdown shows 5 options; thompson_exp3_blend_alpha slider appears + grey-out logic when bandit_algorithm != 4
- **Calibration log** — emit at every fill; 47 columns instead of 9; per-arm Thompson posterior values reflect ghost-training behavior
- **Boot log** — bandit init messages show `InitBuyThompsonBandits` + `InitExitThompsonBandits` (renamed per TECH_DEBT-084)
- **Stamp body** — thompson_exp3_blend_alpha only emits when bandit_algorithm == 4 (preserves HMAC byte equivalence for legacy stamps)
- **Drift check** — 5 new drift-check rows: bandit_algorithm + thompson_mu_prior + thompson_precision_prior + thompson_precision_obs + thompson_exp3_blend_alpha (PARITY-026 close)

**Paper-test sanity:**
1. Set `bandit_algorithm=2` + run paper trade — Thompson posterior should shift (visible in MLStatusPanel) after each rewarded close; pre-`.F.4d` Thompson stayed frozen
2. Set `bandit_algorithm=4` + `thompson_exp3_blend_alpha=0.3` — weights should reflect 30% Exp3 + 70% Thompson softmax blend
3. Train model with cfg=0 + paper-test with cfg=2 — drift check should fire (bandit_algorithm changed = drift)
4. Load v5.14-era model bundle (`thompson_state.json` old name on disk) — Load succeeds via back-compat alias; subsequent Save writes new `buy_thompson_state.json` name

**Gotchas:**
- Operator running `.F.4c.3` models or older with cfg=2 on `.F.4d` engine — Thompson posterior NOW updates (was silent pre-`.F.4d`). Existing trained models will see Thompson learn for the first time; may diverge from pre-`.F.4d` backtest expectations.
- thompson_exp3_blend_alpha STAMP_BOUND only when bandit_algorithm == 4 — operator changing alpha while bandit_algorithm != 4 has no effect on stamp body bytes (HMAC chain preserved)
- 3 TECH_DEBT-082 fields (lazy_rebuild_price_threshold_pct + exit_threshold + confidence_ic_floor) now per-core via `core_N_<field>` syntax; global `<field>=<val>` still works during `.F.4d`→`.F.4f` transition (shadow walker propagates)

**Related:**
- `subplans/2026-05-16-v5.15.5.F.4d-merged-framework-bandit-thompson.md` (plan body)
- `subplans/2026-05-16-v5.15.5.F.4d-merged-framework-bandit-thompson-examples.md` (sidecar examples)
- `postmortems/2026-05-16-v5.15.5.F.4d-merged-postmortem.md`
- `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` Stage 3 amendment v1.2 (Order::flags_packed bandit context bits 17-25 5th canonical)
- `DESIGN_SPECS/framework-patterns/sink-fn-pointer-for-optional-side-effect-pattern.md` Pattern 5 (Thompson_Update branchless wire; noop/real sink fns)
- `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md` Pattern 1 (g_buy/g_exit_reward_dispatch auto-derived fn-pointer table) + Class 28 6 cmov sites
- CLAUDE.md H15-H20 (codified at .F.4d) + item 31 (framework-driven extensibility meta-principle)
- TECH_DEBT-082/-083/-084 (closed at .F.4d) + TECH_DEBT-085 (Thread A FULL residual; .F.4d.1 dedicated ship)

### engine_arch=centralized SHARDED mode DELETION (v5.15.5.F.4d.1.B.4)

**What:** Full surface deletion of `engine_arch=centralized` SHARDED mode (51-site cohort delete at WIP-14b). Previously, sharded engine supported BOTH `per_core_slow` (default v5.0+) AND `centralized` (legacy variant); centralized SHARDED mode used same EngineSharded.hpp surface but with single centralized slow-path thread routing strategies to per-core hot paths.

**Why deleted:** Architectural debt; per_core_slow has been default since v5.0+; centralized SHARDED had no operator demand AND was the source of multiple semantic-mismatch consumers reading per-core registry fields as if they were global (Class 26 antecedent surface). Sister to per-core slow_state ownership (v5.1.2+) which structurally made centralized-arch redundant.

**Operator migration impact:** Operators with `engine_arch=centralized` in `engine.cfg` MUST migrate to `engine_arch=per_core_slow` (default; can omit the line entirely). Engine boot REFUSES startup if `engine_arch=centralized` detected post-`.B.4` per H17 framework discipline. Backwards compat NOT preserved per `feedback_backwards_compat_not_default_concern` (OSS personal tool; cleanest deletion preferred over preserve-and-deprecate). Operator-facing-doc cohort (README + DOCS/QUICKSTART.md + engine.cfg.example + DESIGN_SPECS sister mentions) all updated to remove `centralized` references at WIP-14a.

**Where to verify:**
- `CoreFrameworks/EngineSharded.hpp` — full SHARDED surface; only per_core_slow paths remain
- `CoreFrameworks/CfgFieldRegistry.hpp` — `engine_arch` registry-only HAS_SIDE_EFFECT row preserves operator-facing parser (boot-time REFUSE on `centralized` value)
- `engine.cfg.example` — only `engine_arch=per_core_slow` documented
- `DOCS/CHANGELOG.md` — `.B.4` row documents 51-site cohort deletion

**Paper-test sanity:** Boot engine with `engine_arch=centralized` set explicitly in cfg → engine REFUSES startup with clear "centralized SHARDED mode deleted at .B.4; migrate to per_core_slow" error message. Boot with `engine_arch=per_core_slow` OR no `engine_arch` line → boots normally (no behavior change).

**Gotchas:**
- LIVE legacy single_core (`engine_arch=single_core` ON by default for LIVE deprecated path) UNAFFECTED — separate codepath, distinct from centralized SHARDED. Single-core LIVE still warns at boot per pre-existing deprecation.
- BACKTEST single_core UNAFFECTED — wrapper Backtest_Run dispatches to BacktestSharded_Run; centralized backtest code never existed.
- B14 leaves-first ordering (1st canonical at WIP-14b) — deletion ordering matters when cross-file compile dependencies exist. See `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` § B14 pillar.

**Related:**
- `subplans/2026-05-24-v5.15.5.F.4d.1.B.4-train-serve-execution-layer-parity.md` v1.7.6 (plan body, Phase WIP-14a + WIP-14b)
- `feedback_backwards_compat_not_default_concern.md` (operator preference codified)
- `feedback_multi_surface_deletion_ordering_discipline.md` (B14 1st canonical)
- `feedback_operator_facing_doc_cohort_at_cfg_deletion.md` (WIP-14a cohort sweep)
- B-Plus v0.4 `--gen-deletion-cohort PATTERN` generator mode (M7 second canonical extension)


### Decimal money core (v5.15.5.F.4d.1.E.0.9+ — Ship B)
- **What**: All money values (prices, qtys, fees, balances, money-pct thresholds) are decimal `Money` (`FixedPoint<10,8>`) — exact at venue ≤8dp; venue WS strings parse exactly; ops saturate + round half-even.
- **Cfg flags**: none new — cfg files keep their existing shapes (PCT fields still authored as percents; values now parse EXACTLY; saves trim trailing zeros past 2dp, e.g. "2.34").
- **Fallback**: none (the binary money encoding is retired; pre-epoch artifacts refuse to load).
- **Where to verify**: boot log — stale `order_events.bin` rotates to `<path>.pre-epoch.<ts>` with a loud line; `[ws-parse] MONEY parse flags` / `[drainer] MONEY FLAGS` warns are NEW operator signals (should be silent in normal operation).
- **Paper-test sanity**: P&L/fee numbers now end at 8dp exactly; old snapshots/event-logs/stamps from before this version are REFUSED at boot (engine starts fresh — expected, paper-only data).
- **Gotchas**: a fill whose venue commission is NOT USDT books the COMPUTED fee + warns (`D-173 fallback`) — if you enable BNB fee-burn on the account, expect those warns until the .E.3 BNB guard lands.
- **Related**: D-168..D-188 (decision log), Class 41, `DOCS/CODE_MAP.md` § FixedPoint.

### Config-compiler — capital/feature cfg validation gate (v5.15.5.F.4d.1.E.1.1+ — the ③ arc)
- **What**: the cfg loader is now a COMPILER — it collects ALL malformed / out-of-range / unknown-key problems into a compiler-style readout and a clean compile GATES every fresh start (boot / backtest / optimizer / hot-reload). Replaces the old swallow-and-coerce parse — `risk_pct=banana`→0 silently DISABLED the stop-loss; `risk_pct=999`→999% risk was un-caught (the ③ founding bug). Refuse-don't-coerce (D-242).
- **Cfg flags**: no NEW operator flag — it validates the EXISTING fields. Fault taxonomy on `cfg_load_fault_flags`: CAPITAL_MALFORMED (bit 0), CAPITAL_OUT_OF_RANGE (bit 1), UNKNOWN_KEY (bit 2), FEATURE_MALFORMED (bit 3). `cfg_compile_ok(cfg)` = all-clear; `cfg_capital_gate_ok(cfg, "<ctx>")` = the shared gate (prints the readout + returns pass/fail).
- **Fallback**: a VALID cfg leaves `cfg_load_fault_flags==0` → byte-identical to pre-③ behavior (NO determinism change — verified GREEN). Only a malformed / out-of-range / unknown-key cfg is refused. The hot-reload refuses by KEEPING the running config (warn-keep-old; never fail-stops a live engine).
- **Where to verify**: boot `main.cpp:203` (engine aborts) · backtest `BacktestSharded.hpp:125` + optimizer base `BacktestEngine.hpp:2370` + sweep-range endpoints `:2384` (fail-the-run) · hot-reload `Async.hpp:319-364` (warn-keep-old) · the sweep `ControllerConfig_CapitalRangeSweep<F>` in `ControllerConfig.hpp` (per-node if-constexpr walk + the global-flat leg) · caller-coverage CI `tools/check_cfg_gate_caller_coverage.py`.
- **Paper-test sanity**: set `risk_pct=999` (or `=banana`, or `stop_loss_pct=0`) in `engine.cfg` → the engine REFUSES to boot with a named-field diagnostic, does NOT trade. A valid cfg boots normally (no behavior change). Edit `engine.cfg` to `risk_pct=999` while running → the reload warns + keeps the old (good) config.
- **Gotchas**: the 2 legacy capital arrays (`node_risk_pct[]`/`node_max_drawdown_pct[]`) merge into `nodes[c]` with 0=inherit preserved (the B-merge), so the sweep needs the global-flat leg for an INHERITING node (F1) · feature fields (~47 FPN/float) fault on the DISTINCT FEATURE_MALFORMED bit, not the capital bits · the hot-reload restores boot-only `starting_balance` AFTER Load, so it re-runs the sweep on the MERGED cfg (else `min_kill_loss<starting_balance` false-negatives).
- **Related**: RBP Class 52 (swallow-and-coerce) / 54 (validation-asymmetry) / 55 (dual-source-storage) · `config-compiler-validation-pattern.md` · D-242/D-253/D-256/D-279/D-280 · TECH_DEBT-212 (the founding finding; capital subset closed, non-capital → E.2).

### Tools parity gate — pre-commit Check T (v5.15.5.F.4d.1.E.1.2.B `0.2`+)

**What** — `parity_check.sh` runs automatically on any commit that stages a toolchain file. It was
MANUAL-only before, so the toolchain — a one-producer-N-consumers surface where a wrong fact fans
out — was the one plane with no standing gate.
**Cfg flags** — none. Trigger-scoped by staged path (`tools/foxtag/`, the six corpus consumers,
`bless.py`, `foxroots`/`toolio`, `lib/{corpus_contract,toolio_schemas}.json`, `goldens/`).
**Fallback** — `SKIP_TOOLS_PARITY_CHECK=1` bypasses it.
**Where to verify** — commit a `tools/foxtag/*` change; the hook prints `[pre-commit] Check T`.
**Paper-test sanity** — ~25s when it fires, nothing on unrelated commits. The foxtag build is
cached; the cost is nvim/clang/objdump.
**Gotchas** — a PASS now means AGREEMENT **and** validity. The validity leg (`PY_RC == 0`, not
merely `== CXX_RC`) landed BEFORE the wiring on purpose: without it, two implementations agreeing
the corpus is broken printed `OK : exit codes identical (1)` and still reached PASS.
**Related** — D-387(3) · F-393/BB-2 · `differential-to-absolute-gate-contract-widening.md`.

### `--bless` — the ONE re-bless control for every committed baseline (v5.15.5.F.4d.1.E.1.2.B `0.2`+)

**What** — `tools/bless.py`. Rewriting ANY committed baseline (the corpus goldens, the H21
identifier ledger, the latency ratchet) now requires an interactive terminal, shows the per-file
diff plus what the record currently holds and how many entries would be REMOVED, and demands a
**typed confirmation** (`bless <label>`, not y/n).
**Cfg flags** — none, deliberately. **There is NO `--yes`/`--force`.**
**Fallback** — none. Non-interactive callers are HARD-REFUSED `rc=2`; it fails fast rather than
blocking on stdin, so it cannot wedge a pipeline.
**Where to verify** — `python3 tools/check_identifier_retirement.py --update` in a pipe → refusal;
in a terminal → diff + prompt.
**Paper-test sanity** — a no-op re-bless is `rc=0` and leaves the file **byte-identical** (D-369),
so "run the producer, expect 0-diff" still holds.
**Gotchas** — this is the CONTROL, not a claim that everything it guards is a golden. A golden asks
*is the output still what we blessed*; a ratchet asks *has this metric regressed past its ceiling*;
an append-only ledger asks *has an identifier been reused*. Different lifecycles, one control.
**Why it exists** — per D-385/M10 a delegated agent is now structurally INCAPABLE of blessing a
baseline, which is what keeps a golden a TOTAL acceptance oracle instead of something that matches
by construction. **Related** — D-394 · TECH_DEBT-255 (closed) · `tools/goldens/README.md`.

### Citable-ID integrity — capture-audit Check 14 (v5.15.5.F.4d.1.E.1.2.B `0.2`+)

**What** — every cited `TECH_DEBT-n` / `PARITY-n` / `AR-n`-family id must resolve to exactly one
defining row, and no id may silently disappear from the corpus.
**Cfg flags** — none. Runs inside `check_capture_audit.py` (hook + `check_session_docs`).
**Fallback** — `SKIP_DOC_FLOOR_CHECK=1` bypasses the whole doc-floor block.
**Where to verify** — `python3 tools/check_capture_audit.py --check 14`.
**Paper-test sanity** — ~14s, once per commit. Since (f) closed (2026-08-07) the baseline is **EMPTY**: any finding is NEW and **FAILS** — red-on-new at full strictness. (Historical: it ran green-on-new against a grandfathered baseline while the (f) triage shrank it 51 → 0.)
**Gotchas** — citations are resolved ONLY for distinctively-prefixed namespaces. Short bare tokens
(`H23`, `M8`, `T13`, `B16`, `Class 7`) are NOT verified because they collide with test ids, finding
ids and forward-references — AR-14's false-positive surface says that must not be mechanized.
Citations inside frozen records (postmortems, plan_checks, superseded handoffs) are also skipped: a
frozen record citing a then-real id is a truthful artifact, not a defect.
**Related** — D-399 · TECH_DEBT-249 · H21 (this is H21 on the doc plane).

### `--close` is TTY-gated — the tech-debt ledger writer joins the D-394 contract (v5.15.5.F.4d.1.E.1.2.B `0.2`+)

**What** — `tools/check_tech_debt.py --close N` moves a TECH_DEBT entry `open.md` → `closed.md`. It
now SHOWS the entry, then demands a typed confirmation at an interactive terminal, and HARD-REFUSES
`rc=2` when there is no TTY. Previously it wrote **by default** (`--dry-run` was opt-in, no diff, no
prompt). Same contract as `--bless`, via one shared `bless.confirm_mutation()`.
**Cfg flags** — none. `--dry-run` still prints the move without writing and needs no terminal.
**Fallback** — none, deliberately: there is no `--yes` / `--force`. If you need the move in a script,
you do not — a ledger move is a human act.
**Where to verify** — `python3 tools/check_tech_debt.py --close 016` from a pipe → `rc=2`, ledgers
byte-unchanged. `bash tools/check_tech_debt_selftest.sh` asserts exactly that.
**Paper-test sanity** — instant; the refusal path does no I/O.
**Gotchas** — the id is now ZERO-PAD NORMALIZED, so `--close 16` and `--close 016` reach the same
entry. Before this, `--close 16` errored "not found" while `--close 016` silently WROTE — the safe
spelling failing while the dangerous one succeeded. Also, closing an entry whose `status:` field
cannot be stamped (neither the bare `status:` line nor the bold `· **status:** ·` form present) now
REFUSES rather than moving an entry that would read `open` inside `closed.md`.
**If you are an agent and hit the rc=2** — that is the control working as designed (D-385/M10: a
delegated agent must be structurally incapable of rewriting the record). Do not route around it; ask
Caramel to run it.
**Related** — D-407 · D-394 (the contract) · TECH_DEBT-255 (closed over an un-enumerated set; this
was the missed writer) · Landmine 15 · Class-51 mode F.

### `bless --console` — the universal bless menu (v5.15.5.F.4d.1.E.1.2.B `0.2`+)

**What** — `python3 tools/bless.py --console` lists every blessable record (citable-ID golden ·
corpus pins ×2 · H21 identifier ledger · latency ratchet) with live drift status (`✓ CLEAN` /
`✗ DRIFTED +a/−r` / `? LAZY` for the slow ratchet). Enter a row number → that record's OWN bless
path runs — diff shown, typed confirmation demanded. `r` rechecks all (incl. slow), `r<N>` one
row, `q` quits.
**Cfg flags** — none.
**Fallback** — each record's own CLI still works (`check_corpus_membership --profile X --bless`,
`check_identifier_retirement --update`, the citable-ids one-liner in `tools/CLAUDE.md`).
**Where to verify** — `python3 tools/bless.py --selftest` (13 teeth, incl. roster-coverage of
`tools/goldens/*.txt` + the console's own non-TTY refusal).
**Paper-test sanity** — startup status pass ~2s (the ratchet is lazy by design).
**Gotchas** — the console is a MENU over the existing D-394 gates, never a gate itself: there is
still no `--yes`, no batch mode, and a non-TTY invocation refuses rc=2 — an agent cannot drive it.
The `⚠️ REMOVALS` flag on a drifted row is the only alarming state (H21: additions are legal).
**Related** — D-394 · D-410 (bless authority declined; cadence is the friction fix) · TECH_DEBT-255
· `tools/goldens/README.md` (the golden/baseline/ratchet taxonomy).

### Docview — the `[REFERENCE]` doc-viewer: float · pin · chooser (v5.15.5.F.4d.1.E.1.2.B `0.4`+)

**What** — inside any tagged unit (or its FILE header — macros/file-scope fall back), `m → Docs`
resolves the unit's `[REFERENCE]` ids and opens the DEFINING doc beside the code: one hit floats
immediately (real buffer, cursor on the defining line, `q` closes, **`p` promotes to a pinned
rightmost split** — the docs+code layout); several hits open the recency-sorted chooser (newest
ids first, prefix-grouped). All ELEVEN fenced subcats route: id-shaped (INVARIANT/DECISION/
TECH_DEBT/CLASS/PARITY) via `citable_ids.py --where` (defining-site envelope), doc-shaped
(DESIGN_SPEC/MEMORY/PLAN) via `--resolve` (bare-name probe), AUDIT/SOURCE/URL skipped BY NAME.
**Cfg flags** — none (python3 + `tools/citable_ids.py` on the repo root; `:checkhealth
fox-symdeps` verifies the chain).
**Fallback** — tri-state honest at every seam: resolver-failed = named ERROR (never empty), dead
id = named WARN (never a blank float), RENAMED = old→new notify. Float dismisses on focus-leave
(transient lens); the pin owns persistence.
**Where to verify** — `FixedPoint/FixedPointN.hpp:20` (`[[H4] [H9] [H12] [H21]]` + decisions) →
`<leader>dm → Docs`.
**Gotchas** — the doc float is `q`-only by design (a buffer-local `<Esc>` on a REAL doc buffer
would leak into other windows showing it).
**Related** — D-417 (the resolver lift) · `DOCS/TOOLCHAIN_CONTRACTS.md` §2 (consumer semantics) ·
TD-270 (two-cores convergence) · the 682 mined ids below.

### `mine_reference_tags.py` — the `[REFERENCE]` corpus miner (v5.15.5.F.4d.1.E.1.2.B `0.4`+)

**What** — lifts EXISTING in-span id mentions (`per D-142` / `H4` / `Class 51` / doc names) into
the unit's `[REFERENCE]` tags: additive merge (hand-written ids never removed/reordered), every
id validated against the VALIDATOR's own membership index, innermost-unit attribution, indented
banners preserved, `x-pattern` ≡ `x-pattern.md`. Maiden passes: 550 id-shaped + 132 doc-shaped
across the corpus.
**Cfg flags** — dry-run is the DEFAULT; `--fix` writes (D-374 flag-not-auto; the git diff is the
review surface); `--paths` restricts.
**Fallback** — MINE-NEVER-INVENT: unresolved mentions are excluded + reported; ambiguous
both-set doc names refused; unmatched loose hits silently ignored (a filename mention is not a
reference claim).
**Where to verify** — `python3 tools/mine_reference_tags.py` (dry-run) then `--selftest` (14 teeth).
**Gotchas** — comments-only by construction (prove with: every changed diff line starts `//`).
**Related** — D-413/D-414 (the fabrication arc whose law this obeys) · Class 57 · the docview
entry above (its data).

### The unified action menu — menu-as-root · layer-stack · TAG ADD (v5.15.5.F.4d.1.E.1.2.B `0.4`+)

**What** — `<leader>dm` (or `m` in any HUD) is THE root surface: unit-gated analyses (who-writes ·
false-sharing · docs · derived-write ✎ · lock-layout ⚠ · straddle/ambient/asm per type) + the
global launchers (browse · roam · dashboard · size chip · use-lens), identical items from every
invoker (one registry, rows pass verbatim), ✎/⚠ write-tier icons + legend everywhere. The
LAYER-STACK rule: `opened item > menu > HUD` — the HUD stays alive under its child menu; running
an item collapses ancestors (analysis rows that render INTO the HUD keep it). **TAG ADD** (`m →
Add [TAG]`, ✎): browse the REAL concern+surface vocab (derived from the grammar payload) and
merge a token into the unit's orient `[TAG]` line — idempotent, indent-preserving; minting NEW
vocab points at `tools/add_vocab.py` (the SSoT).
**Cfg flags** — none new.
**Fallback** — reserved keys refuse shadowing lens binds with a one-time warning; unknown unit
types / subcats warn instead of silently gating; from `dm` with no HUD the analyses surface
verdict notifies + a pointer at the jumpable tree.
**Where to verify** — a struct unit: `<leader>dm` should title `STRUCT <name>` with ~14 rows +
launchers; board `s` compares again; `m` opens the menu on EVERY hud kind.
**Gotchas** — the `n` mention-sweep lens was REMOVED (operator call): curated `◆ Docs` + the
mention machinery live in git history if ever wanted as a row. `opts.doc_dirs` retired with it.
**Related** — the plugin-parity fleet register (`plan_checks/2026-08-10-plugin-parity-fleet-register.md`,
CLOSED zero-tail) · ideas §11 · north-star §6.
