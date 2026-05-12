# POST_v5.12-v5.14-mini — PUNCH_LIST

**Status:** Open (paper-test never completed; per Caramel 2026-05-12 "i never got around to actually testing that stuff, and need to"). Pre-dates the 3-file WATCH+TRY+OBSERVATIONS pattern (introduced for POST_v5.15); kept as a single consolidated punch list since it was already structured that way.

**Engine state when this doc was written (2026-05-11):** v5.14.11 closed at `feat/v5.14-foxml-port-and-maker` HEAD `c4e45d1` (2904 tests). Engine has since advanced to v5.15.4 + v5.15 umbrella close (3006 tests). v5.15 changes are tracked separately in `../POST_v5.15/`. **Paper-test the v5.12-v5.14 features in this doc FIRST** since they're opt-in (default cfg behavior preserved through all 3 sprints) and don't depend on v5.15 changes — then validate v5.15 on top per `../POST_v5.15/`.

**Default cfg behavior is preserved through all 3 sprints** — every new feature is opt-in via cfg flags. A "stock run" with no cfg edits is bytewise-identical to v5.11 baseline (modulo the bugfixes called out below).

This doc is a **testing punch list**, not a feature spec. For each feature: what cfg toggles it, what to watch for, what would be a regression. Order: highest-impact first within each sprint. Findings go in `OBSERVATIONS.md` in this same directory.

**Cross-references:**
- Sister doc: `../POST_v5.15/{WATCH_LIST,TRY_LIST,OBSERVATIONS}.md` for v5.15 sprint-specific items
- Index: `../README.md` for paper-test workflow conventions

---

## TL;DR before you start

1. **Backtest first, paper-trade second.** Each opt-in feature has a backtest path that's faster + safer to validate before exposing to live data.
2. **Default cfg is the baseline.** Run a stock backtest as your control; flip one flag at a time when comparing.
3. **`tests/controller_test.cpp` passes 2904/2904** — that catches functional regressions but NOT semantic correctness of new ML features. Paper-test is where you'll see if Ridge / Thompson / exit_predictor / online_corr actually deliver alpha.
4. **Calibration log is the friend.** `cfg.calibration_log_path=...` writes per-fill rows with predicted probability + realized PnL. Brier / ROC AUC analysis lives here; it's how you'll grade ML changes offline.

---

## v5.12 — Pre-live safety + slow-path optimization + ML research infra

### v5.12.1.A — WS-staleness flatten + recovery refusal (SAFETY — PRE-LIVE)

**Default:** OFF (`cfg.ws_dead_time_flatten_enabled=0`).
**Test it:** set `ws_dead_time_flatten_enabled=1` + `ws_dead_time_threshold_secs=10` (or your tolerance) + `recovery_delay_secs=30`. Disconnect your network briefly during a paper run; engine should emergency-flatten all positions via OMS, then refuse new entries for 30 seconds after WS reconnects.
**Watch for:**
- ✅ Open positions exit at market when WS dies past threshold
- ✅ No new entries during recovery cooldown
- ❌ Phantom orders during WS hiccup (race condition)
- ❌ Failure to recover after WS comes back (stuck refusing forever)
**Regression watch:** with the flag OFF, behavior must be bytewise-identical to pre-v5.12 (no flatten ever fires; no recovery state ever triggers). Smoke test with default cfg.

### v5.12.1.B — Hot-path staleness gate (PARAMS_STALE SHALT)

**Default:** ON (always-gated; ~1-2ns branchless mask cost per tick).
**Test it:** Cannot easily induce stale params manually without manipulating the slow path. Trust the unit tests + the fact that this is in the hot path's mask compute.
**Watch for:**
- ❌ SHALT_PARAM_STALE firing in normal operation (means slow-path rebuild is delayed for unexpected reasons — diagnose root cause, don't disable the gate)

### v5.12.1.C — WS heartbeat panel

**Default:** ON in GUI (`bin/engine_gui` + `bin/foxml_suite`).
**Test it:** Run the GUI; observe color-coded WS freshness in the header. Should be GREEN under normal conditions; amber as it ages; red after threshold.
**Watch for:**
- ✅ Freshness numbers update every tick
- ❌ Persistent amber/red despite WS being healthy (clock skew or freshness calc bug)

### v5.12.1.D — Confidence-conditional sizing infrastructure

**Default:** OFF (no consumer until v5.14.9 ladder). Infrastructure-only in v5.12; activated in v5.14.9.
**Test in v5.14.9 context (see below).**

### v5.12.2.B — Lazy slow-path rebuild

**Default:** OFF (`cfg.lazy_rebuild_enabled=0`).
**Test it:** set `lazy_rebuild_enabled=1` and run a long-ish backtest. Slow-path cycles should skip when regime + flow + strategy haven't changed.
**Watch for:**
- ✅ Tighter slow-path latency in profiling (`build_lat/` build with `LATENCY_PROFILING=ON`)
- ❌ Stale gate parameters causing wrong-direction trades (slow-path effectively pausing)
- Compare backtest results vs default cfg — should be bytewise-identical (lazy rebuild only skips when state genuinely unchanged)

### v5.12.2.D — Treelite AOT inference stubs

**Default:** Infrastructure-only (no consumer). Skip testing.

### v5.12.3.A/B/E — Composite-signal extractor + mixed-output normalizer

**Default:** Uses identity normalizer when stamp's `label_kind` is unset.
**Test it:** Train a mixed-output ensemble (different `label_kind` per horizon: binary + barrier + regression). The trainer UI per-horizon Label Kind CSV in v5.13.5 enables this.
**Watch for:**
- ✅ Each horizon's prediction matches its training label_kind semantics
- ❌ Wrong class index used as "win" probability (v5.13.0.A had a similar aliasing bug caught by /readiness Check 19; verify this doesn't recur with mixed-output)

### v5.12.3.C — Per-core time-exit override

**Default:** Uses global `cfg.time_exit_ticks`. Override via `cfg.core_N_time_exit_ticks` (N=0..15).
**Test it:** Set different time-exit thresholds per core; verify each core honors its own.
**Watch for:**
- ✅ Time-exits fire at per-core threshold not global
- ❌ Per-core override silently ignored (parser bug)

---

## v5.13 — Sell-side ML (Path 3 architecture)

### v5.13.0 — Exit-side ML predictions (`use_exit_model`)

**Default:** OFF (`cfg.use_exit_model=0`; uses entry model for exit decisions like pre-v5.13).
**Test it:** Train PEAK_VALLEY_STABLE 3-class exit models into `cfg.exit_signal_model_dir` (or use the auto-detected path) → set `cfg.use_exit_model=1` + `cfg.exit_threshold=0.6`. Engine fires `MARKET_SELL` for any open position when the blended exit-predictor probability exceeds threshold on a slow-path cycle.
**Watch for:**
- ✅ Exit fires within ~1 slow-path cycle of the prediction (not on the wrong cycle / wrong slot)
- ✅ SHALT_EXIT_PREDICTED logged on exit
- ✅ Per-slot calibration log entry with predicted_p + realized_pnl_bps + was_win
- ❌ Wrong class index treated as "exit" probability (the v5.13.0.A aliasing fix — verify exit_predictor handles default to VALLEY class 0 with correct aliasing, NOT inverted)
- ❌ Exit firing on the entry model when `use_exit_model=0` (fallback should preserve pre-v5.13 behavior)
**Calibration log analysis (offline):** Brier score + ROC AUC on the exit prediction rows; compare to "always exit at TP/SL only" baseline.

### v5.13.4 — Sell-side bandit (counterfactual reward attribution)

**Default:** OFF (`cfg.exit_bandit_enabled=0`).
**Test it:** Enable after v5.13.0 + after `<core_model_dir>/exit_bandit_state.json` exists (auto-created on first save). Set `cfg.exit_bandit_lr=0.1` initially; tune via paper-test.
**Counterfactual semantics:** reward = `actual_pnl_bps - (tp_pct - 2*fee_taker)*10000` using **original** TP (locked at entry, NOT ratchet'd). This is OPTIMISTIC — assumes TP would have hit before SL.
**Watch for:**
- ✅ Per-slot capture is partials-aware (legs A + B independently attributable)
- ✅ Bandit converges to selecting exit-arms that beat the optimistic-TP baseline
- ❌ Bias toward exiting too late (if reward attribution is wrong-signed)
- ❌ State drift on swap/reload (verify `exit_bandit_state.json` round-trips correctly)

### v5.13.5 — Trainer UI per-horizon label_kind + side selector

**Default:** Single-side training, single label_kind (pre-v5.13.5 behavior).
**Test it:** In the Multi-Horizon training panel:
- Side selector: pick "Exit signals" → models route to `models/exit/<run_subdir>/<run>_horizon_<N>/`
- Per-horizon Label Kind CSV: e.g., `0,5,1` → horizon_0=binary, horizon_1=barrier, horizon_2=regression
**Watch for:**
- ✅ Train Multi-Horizon button disables on alignment mismatch (CSV length ≠ horizon count, and not 1 for broadcast)
- ✅ Buy-side paths still bytewise identical when training_side=0 (default)
- ❌ Off-by-one in per-horizon assignment (positional mapping bug)
- ❌ XGBoost segfault under parallel training (**KNOWN LANDMINE v5.11.45**: default `cfg.multi_horizon_max_threads=1`; opt-in `>=2` carries XGBoost+libgomp segfault risk — see CLAUDE.local.md for details)

---

## v5.14 — Ridge blending + composite confidence + hot-swap + ML hardening (big sprint, ~12 sub-ships)

### v5.14.0 — Ridge risk-parity blending (`ridge_within_horizon`)

**Default:** OFF (`cfg.ridge_within_horizon=0`; bandit weights used directly).
**Test it:** Set `ridge_within_horizon=1` + `ridge_lambda=0.15` + `ridge_cost_penalty=0.5` + `ridge_min_ic_floor=0.001` (defaults).
**Semantics:** When enabled, overrides bandit weights with Ridge-computed weights from `(Σ + λI)⁻¹ μ` where `Σ` is N×N correlation of recent prediction history and `μ[i] = max(IC[i] - cost_penalty × cost[i], min_ic_floor)`. Penalizes correlated models. Mutually-exclusive with Thompson (cfg=1/2) — Ridge override is skipped when Thompson is on (bytewise; not an error).
**Watch for:**
- ✅ Highly-correlated arms get lower combined weight vs bandit-only
- ✅ ~3µs/cycle slow-path cost when enabled (well within budget)
- ❌ Singular Σ falling back to uniform when it shouldn't (`fallback_to_uniform` flag — check PerCoreSnap visibility)
- ❌ Ridge weights NaN or sum != 1 (would be a math kernel bug; .B AVX-512 work has SHA-256-locked byte-determinism tests)
- ❌ With cfg=0 default, ANY deviation from bandit-only path (must be bytewise-identical)

### v5.14.1 — Composite confidence + winsor + IC variants + portfolio turnover

**Composite confidence (`confidence_composite_enabled`)**
**Default:** OFF.
**Test it:** Set `confidence_composite_enabled=1`. Switches the confidence formula from legacy 3-factor (prediction_p, prob_change, freshness) to 4-factor (adds book_imbalance_z). **Stamp-bound** — models trained pre-v5.14.1 with composite=0 won't auto-flip; need retrain or stamp_override.
**Watch for:**
- ✅ Stamp's `has_confidence_composite_enabled=1` + value matches cfg
- ❌ Stamp/cfg mismatch causing REFUSE on boot

**Winsorization (`winsor_pct_low` + `winsor_pct_high`)**
**Default:** ON at 0.005 / 0.995 (clipping outlier feature values at percentile bounds).
**Test it:** Already-on. Disable by setting `winsor_pct_low=0` + `winsor_pct_high=1` for comparison.
**Watch for:**
- ✅ Stamp captures the winsor params (HMAC byte-equivalence)
- ❌ Disabled-winsor backtest having WORSE alpha than winsorized (signals features need winsor)

**v5.14.1.E — Exit-side Ridge blending (`exit_blender_mode`)**
**Default:** OFF.
**Test it:** Set `exit_blender_mode=1`. Mirrors v5.14.0 buy-side Ridge but for exit_predictor[] handles. Heterogeneous winsor per exit handle supported.
**Watch for:** Same as buy-side Ridge; plus per-handle scaler routing correctness.

### v5.14.2 — Hot-swap ensemble coverage

**Default:** Hot-swap was already supported for single-zoo; v5.14.2 extends to ensemble (multiple horizons).
**Test it:** While engine running (paper mode), edit `cfg.core_N_model_dir` or `cfg.core_N_model_path` to point at a new model dir + trigger hot-swap (via signal or by writing to the trigger path).
**Watch for:**
- ✅ Models reload without engine restart; old predictions stop influencing trades; new predictions start within 1 cycle
- ✅ Strict-mode reload failure handling: if new model fails validation, reverts to prior state
- ❌ Brief window where stale predictions trade against new-model assumptions
- ❌ Memory leak in repeated swaps (run 100x swap loop and check RSS)

### v5.14.3 — 3-layer registry fingerprinting (overlay-aware lineage)

**Default:** Optional. Used when training with feature overlays (per-target lookback overrides, disabled flags).
**Test it:** Train a model with a feature overlay sidecar (`tools/feature_overlay.py write ...`); engine load-time should verify the sidecar's `computed_layer2_hash` matches the stamp body's `overlay_hash`.
**Watch for:**
- ✅ Tampered sidecar refused at load
- ✅ Backward-compat: legacy stamps (no overlay claim) load fine (Surface G has_overlay_hash=0 silent-skip)
- ❌ False-positive refusal on legitimately-trained overlay models

### v5.14.4 — Multi-mode reconciliation (STRICT / WARN / AUTO_SYNC)

**Default:** Legacy `reconcile_dry_run=1` → translates to WARN mode.
**Test it:** Set `cfg.reconcile_mode=strict` (or `warn` / `auto_sync`); restart engine. STRICT refuses boot if exchange-side shows missed trades / stale orders. AUTO_SYNC applies missed fills via `OrderManager_HandleFill` + cancels stale orders.
**Watch for:**
- ✅ STRICT refuses to boot with helpful error when disagreement detected
- ✅ AUTO_SYNC idempotent on re-run (same `last_seen_trade_id` skipping previously-applied)
- ❌ AUTO_SYNC accidentally cancelling non-engine orders on shared account (is_ours=0 filter must work)
- ❌ Mode parser misinterpreting cfg value

### v5.14.5 — CS targets + regime-conditional features + fractional differentiation

**Default:** New features are appended to FOREACH_FEATURE — your existing trained models will fail to load (FEATURE_REGISTRY_HASH bumped 2x in this sprint). **Retrain needed.**
**Test it:**
1. Retrain models with v5.14.5's expanded feature set (the trainer auto-includes new features)
2. Verify FEATURE_REGISTRY_HASH in new stamps matches the engine's expected hash
3. Paper-test on retrained models
**Watch for:**
- ✅ Pre-v5.14.5 stamps deliberately refuse-to-load (this is correct; forces retrain)
- ✅ New features (regime_trend_strength, regime_vol_zscore, frac_diff_price_d04/05/06) appear in stamp body + feature importance reports
- ❌ Regime-conditional features producing NaN under specific regime transitions
- 📊 TECH_DEBT-007 followup: empirically verify regime_trend_strength + regime_vol_zscore add information vs existing features — check feature_importance post-first-retrain

### v5.14.6 — `/bug-check` skill (developer tooling; no runtime impact)

**Test it:** Run `/bug-check` from Claude Code; should scan codebase for Class 1-19 recurring bug patterns. Operator-side test: nothing to do at runtime.

### v5.14.7 — Maker order MVP

**Status:** **DEFERRED INDEFINITELY** per TECH_DEBT-008 (no consistent order book data source). Skip testing entirely.

### v5.14.8 — Stamp body lineage + stale gating

**Default:** `cfg.model_max_age_hours=0` (disabled).
**Test it:** Set `model_max_age_hours=24` and try booting with an older model. Should WARN/REFUSE at boot.
**Watch for:**
- ✅ Stale model triggers REFUSE; engine doesn't start
- ✅ Recently-trained models pass
- ❌ Timezone bug in age calculation (always use UTC; verify training_timestamp_us is consistent)

### v5.14.9 — Soft risk degradation ladder + DOMAIN SPLIT + bitmap closure

**Default:** OFF (`cfg.risk_degradation_curve=0/OFF`).
**Test it:** Set `risk_degradation_curve=LINEAR` (or `EXP` / `STEP`) + `confidence_composite_enabled=1` (composite is REQUIRED for ladder to fire). Engine scales position size by confidence factor; at confidence=0 the ladder fires SHALT_LOW_CONFIDENCE instead of opening the trade.
**Watch for:**
- ✅ Boot REFUSE if `risk_degradation_curve != OFF` AND composite is OFF (compile-time invariant via gate cache)
- ✅ Position sizes scale smoothly along the chosen curve
- ✅ SHALT_LOW_CONFIDENCE fires at the ladder bottom (factor=0)
- ❌ Sizing curve producing negative sizes (math bug)
- ❌ Per-core ladder overrides (`cfg.core_N_*` ladder params) silently ignored

### v5.14.10 — Bayesian Thompson sampling bandit (mega-bundle)

**Default:** `cfg.bandit_algorithm=0` (EXP3-IX; pre-v5.14.10 behavior).
**Test it:**
1. `bandit_algorithm=1` (Thompson alone): Gaussian conjugate posterior + own splitmix64 PRNG → arm selection via posterior sampling
2. `bandit_algorithm=2` (Both): Exp3 drives decisions, Thompson logs choices in parallel (per CLAUDE.md item 24 — per-arm reward observability makes this valid)
**Watch for:**
- ✅ `thompson_state.json` writes per ezoo with deterministic format
- ✅ Posterior parameters (mu_post, precision_post) drift toward reward-weighted arm
- ✅ cfg=2 dual-mode tracks BOTH bandits' choices in calib log (TECH_DEBT-030 wires the specific columns)
- ❌ Thompson sampling producing NaN samples (Box-Muller variance issue)
- ❌ State persistence across engine restart drifts (verify JSON round-trip)
**New TUI surface:** ML Status panel → "Thompson Bayesian dashboard" CollapsingHeader (per-arm mu_post + precision + pulls table; color-coded). Open this to validate visually.
**Ridge mutual exclusivity:** `ridge_within_horizon=1` + `bandit_algorithm=1/2` → Ridge silently skipped (per design; Thompson + Ridge mathematically incompatible).

### v5.14.10.D — FOREACH_CALIB_LOG_COL refactor

**Default:** Calibration log output is BYTE-IDENTICAL to pre-v5.14.10.D (refactor preserves wire format via SHA-256-locked tests).
**Test it:** Compare a pre/post-refactor calib log line; should be byte-identical.

### v5.14.10.F — FOREACH_TRADE_LOG_COL refactor

**Default:** Trade log output BYTE-IDENTICAL to pre-refactor.
**Test it:** Same as above; verify trade log columns + delimiters unchanged.

### v5.14.11.A — Sliding-window incremental correlation (Ridge optimization)

**Default:** OFF (`cfg.ridge_online_corr=0`; full BuildCorr recompute per cycle).
**Test it:** Set `ridge_online_corr=1` (only effective when `ridge_within_horizon=1` or `exit_blender_mode=1`). Switches Ridge correlation update from full K-record recompute to incremental drop-add via Welford-style online stats.
**Watch for:**
- ✅ Bytewise-identical Ridge weights vs full recompute path (Welford-equivalent within 1e-9 tolerance)
- ✅ Slow-path cost reduction at K=64 records (full ~1µs → online ~200ns when drop-add path active)
- ❌ Numerical drift after long runs (1000+ cycles) — the design has a numerical-stability reset, validate it triggers correctly

### v5.14.11.B — Branchless math kernels + struct padding determinism

**Default:** Always active (math kernel improvements; no cfg gate).
**Test it:** Verify backtest results from a pre-v5.14.11 run are **bytewise-identical** to a v5.14.11.B run with same inputs + same cfg. The Cholesky_Solve rewrite + AVX-512 vectorization is byte-deterministic with SHA-256 locks.
**Watch for:**
- ✅ Backtest replay-determinism intact (run same inputs twice; outputs should be bytewise-identical)
- ✅ FracDiff features no longer flake under stack-layout shifts (was a latent bug fixed via FPN _padding field)
- ❌ Subtle drift in Ridge weights if AVX-512 vectorization path diverges from scalar (the SHA-256 lock test catches this; runtime smoke test is the second layer)

### v5.14.11.C — Ridge cohort cfg-flag migration to bitmap

**Default:** Migration is transparent — cfg flags read identically as `ridge_within_horizon=1` in engine.cfg, just stored in `ml_cfg_flags` bitmap internally.
**Test it:** Existing cfg files don't need editing. Old-format `ridge_within_horizon=1` still parses correctly.
**Watch for:**
- ✅ Stamp body HMAC chain UNBROKEN for legacy models (byte-equivalence ternary `? 1 : 0`)
- ❌ Stamp/cfg mismatch refusing legitimately-trained pre-v5.14.11 models (would be a byte-equivalence bug)

---

## Regression watch list (cross-sprint)

These are areas where past sprints introduced subtle concerns. Worth touching on if you have time during paper-test:

1. **Hot path latency (target p99 ≤500ns per tick).** Build with `LATENCY_PROFILING=ON` (`./build.sh` → `build_lat/`) + run a short paper segment. v5.12.1.B added a staleness mask (~1-2ns). v5.14 added no hot-path cost.

2. **Slow path latency (target p99 ≤100µs per cycle).** Should still be well within budget. v5.14.0 Ridge adds ~3µs when enabled. v5.14.11.A drops Ridge to ~200ns when `ridge_online_corr=1`.

3. **Replay determinism.** Run a backtest twice with identical inputs + same build; outputs should be bytewise-identical. v5.14.11.B locked AVX-512 paths with SHA-256 byte-determinism tests but only the kernel itself; whole-system replay determinism is the operator-side test.

4. **Calibration log byte-format.** v5.14.10.D refactored the calib log writer via FOREACH_CALIB_LOG_COL X-macro registry. Output is byte-identical to pre-refactor per SHA-256 lock test; verify your offline analysis pipeline (Brier / ROC AUC scripts) still parses correctly.

5. **Train-serve parity.** FEATURE_REGISTRY_HASH must match between training-time and engine-time. Pre-v5.14.5 stamps will REFUSE-to-load after v5.14.5 (this is correct). Post-v5.14.5 stamps should load fine on the v5.14.11 engine.

6. **GUI panel updates.** v5.14.10.D added Thompson Bayesian dashboard (ML Status panel CollapsingHeader). v5.14.9.B added per-core ladder cfg panel (Risk Degradation Curve section). v5.12.1.C added WS heartbeat color-coded freshness in header. All three should populate live in the GUI; absence indicates a snapshot wiring bug.

7. **Bandit state persistence.** `bandit_state.json` (Exp3) + `exit_bandit_state.json` (v5.13.4 sell-side) + `thompson_state.json` (v5.14.10.C) — three separate files. Restart the engine and verify all three round-trip correctly (boot-time load shouldn't reset arm weights to uniform unless model bundle changed).

---

## Known landmines (do NOT step on these)

1. **XGBoost + libgomp segfault under parallel multi-horizon training.** Default `cfg.multi_horizon_max_threads=1` (safe; serial). Setting `>=2` carries known segfault risk on XGBoost's internal libgomp parallel-region setup. See CLAUDE.local.md "Known landmine" section. Workaround: train horizons in separate `foxml_suite` invocations.

2. **CPU clock capped at 3 GHz on dev machine** per `project_cpu_freq_capped_3ghz.md` memory. Bench results from here are 3 GHz numbers, not boost. Don't confuse this with a performance regression.

3. **DOCS/ symlinks via workspace.** Many docs (HOT_PATH_CHANGELOG.md, TECH_DEBT.md, etc.) are workspace-private and symlinked from engine `DOCS/`. Editing the workspace-side path is the only way; engine-side Edit will refuse.

4. **Hot-swap during in-flight orders.** Engine permits hot-swap but doesn't block orders during the swap window. Brief mismatch possible between old-model-submitted orders and new-model-expected behavior — observe in paper before relying on hot-swap in live.

5. **`./build.sh test` does NOT compile `foxml_suite` or `engine_gui`.** A struct migration / refactor can pass `./build.sh test` but fail `./build.sh gui suite` because the GUI targets pull in `BacktestPanels.hpp` + training UI headers that the test target skips. When verifying a code change, run `./build.sh gui suite tsan asan all` for full surface coverage — NOT just `test`. v5.14.post1 was a v5.14.8.A.6 migration gap that hid through 3 sprints because verification kept being `test`-only. (See `plans/v5.14-foxml-port-and-maker/postmortems/2026-05-11-v5.14-post-release-fixes.md`.)

---

## Paper-test smoke test (suggested sequence)

1. **Baseline** — stock cfg (all v5.12/13/14 flags OFF), 1-2 hour paper run on BTCUSDT. Verify: trades open + close cleanly; no SHALTs unexpected; calib log writes; GUI panels populate.

2. **Composite confidence** — `confidence_composite_enabled=1` + retrain models with composite. Compare alpha to baseline.

3. **Risk degradation ladder** — composite=1 + `risk_degradation_curve=LINEAR`. Verify position sizes scale with confidence; SHALT_LOW_CONFIDENCE fires at the bottom.

4. **Ridge buy-side** — `ridge_within_horizon=1` (composite still on). Verify Ridge weights shown in PerCoreSnap; compare alpha to bandit-only.

5. **Exit-side ML** — `use_exit_model=1` + trained exit models. Verify SHALT_EXIT_PREDICTED fires; calibration log captures exit predictions.

6. **Exit Ridge** — `exit_blender_mode=1` on top of exit-side ML. Verify weights diverge from uniform under correlation.

7. **Thompson** — `bandit_algorithm=1`. Verify thompson_state.json writes; posteriors drift sensibly.

8. **WS-staleness flatten (SAFETY)** — `ws_dead_time_flatten_enabled=1` + simulate WS dropout (block port via firewall briefly). Verify flatten + recovery cooldown.

9. **Reconcile STRICT mode** — `reconcile_mode=strict`. Try booting with intentional disagreement; verify REFUSE. Then `auto_sync`; verify missed fills apply.

10. **Lazy rebuild + online corr (perf)** — `lazy_rebuild_enabled=1` + `ridge_online_corr=1`. Compare slow-path latency profile to defaults.

If all 10 steps pass: v5.14 + all predecessors are usable for the next sprint.

---

## Where to find more detail

- **Per-sprint elevator pitch:** `DOCS/CHANGELOG.md` (one row per version)
- **Per-sprint deep-dive postmortems:** `plans/v5.14-foxml-port-and-maker/postmortems/`
- **Hot-path additions:** `DOCS/HOT_PATH_CHANGELOG.md` (per-entry cost analysis)
- **TECH_DEBT ledger:** `DOCS/TECH_DEBT.md` (entries -001 through -032 + -017 closed)
- **Design patterns:** `DESIGN_SPECS/` (24 patterns; cross-linked from CLAUDE.md items 12-27)
- **CLAUDE.md (engine ARCH/INV reference):** `CLAUDE.md` (always-loaded; items 1-27)
- **CLAUDE.local.md (operator policies):** `CLAUDE.local.md` (private; rules + going-forward decisions)
