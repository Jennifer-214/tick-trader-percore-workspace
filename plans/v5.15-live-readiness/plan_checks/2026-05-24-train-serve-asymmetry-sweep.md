---
type: plan-check
audit_kind: train-serve-asymmetry-sweep
scope: ML/training side vs LIVE/serving side parallel-infrastructure asymmetry
target_ship: v5.15.5.F.4d.1.B.3 (in flight) + v5.15.5.F.4d.1.B.4 (NEW; queued post-this-audit)
audit_date: 2026-05-24
engine_head: 56a689620bb48559597f8b51032b3b43cc499952
branch: feat/v5.15-live-readiness
sprint: v5.15-live-readiness
verdict: RED (4 CRIT + 5 HIGH + 2 MED; live kill_switch dead; train-serve break in 4 places)
audit_agent_prompt_id: ML↔LIVE structural sweep (general-purpose subagent 2026-05-24)
established: 2026-05-24
tags: [audit-methodology, train-serve-parity, execution-layer, structural-fix-preferred, class-18-mirror]
surface: [engine-sharded-boot, slow-path-cycle, oms-drainer, ml-inference, confidence-scoring]
sister_specs:
  - cfg-derived-consumer-framework.md (Phase F closed cfg/stamp parity; this audit covers the layer BELOW)
  - structural-fix-preferred-decision-framework.md (Option D ARCHITECT justified per 4 CRITs + 3 HIGHs covered by 1 refactor)
  - canonical-sister-extension-discipline.md (EngineCommon extract is sister to STAMP_RESULT_DERIVED_FIELDS_AUTO_GEN cohort pattern)
  - implementation-layer-blindspot-taxonomy.md (proposed NEW B14 train-serve execution parity)
---

# Train-serve asymmetry sweep — 2026-05-24

**Audit kind:** structural-asymmetry between training-side (`Backtest/*`) + serving-side (`EngineSharded/* CoreFrameworks/*`) — Class 18 mirror surface
**Scope:** execution layer — boot calls + slow-path cycle body + safety primitives
**Origin:** Caramel operator concern 2026-05-24 — *"im sure there are structural issues between ML and LIVE"*
**Verdict:** RED — 4 CRIT silent train-serve breaks (no plan currently addresses)

---

## Why this audit exists

Phase F of `v5.15.5.F.4d.1.B.3` closed the cfg-derived consumer framework at the registry layer (single master registry → cohort framework → unified emit + parse + drift surface). The framework consolidation gave us audit tools (`/parity-check` Section M + N) that walk train↔serve handoffs systematically.

This audit ran those tools at the **layer below cfg/stamp** — the boot + slow-path execution layer. It found that the cfg/stamp parity discipline doesn't extend down. Multiple safety + correctness primitives are configured by backtest at boot but NOT by live engine (or vice versa).

The findings are NOT created by Phase F refactoring. They predate it by 1-14 months. They were INVISIBLE until the framework consolidation enabled systematic train-serve audit at this layer.

---

## CRIT findings (silent train-serve break OR live-only safety hole)

### A1 — Live `kill_switch` is silently dead (CRIT; safety hole in live trading)

**Verified via direct grep:**
- `CoreFrameworks/EngineSharded.hpp:742` — calls ONLY `EventLoopState_Init(&state, &oms)`; NO `EventLoopState_ConfigureKillSwitch` follows
- `Backtest/BacktestSharded.hpp:218` — DOES call `EventLoopState_ConfigureKillSwitch(&state, 0, cfg.kill_switch_drawdown_pct)`
- Eval body at `CoreFrameworks/ControllerEventLoop.hpp:3300-3314` early-returns when `ks_min_balance == 0 && ks_max_drawdown_pct == 0`. Both stay zero-init from `OrderManager_Init`.

**Operator-impact:** Operator sets `kill_switch_enabled=1, kill_switch_drawdown_pct=5.0` in `engine.cfg`. Backtest replays trip the switch correctly. Live trading runs IGNORE both fields → no drawdown protection in production. **Worst-case silent unbounded loss.**

**Already known?** NOT in TECH_DEBT (searched 001-118). Not in PARITY_ISSUES. `PortfolioController.hpp:957+1619` exercises kill_switch but only on legacy single-core path (deprecated), NOT the sharded production path.

**Severity:** CRIT — this is the most consequential finding in this audit. Live-mode safety primitive is non-functional. Sprint is named `v5.15-LIVE-READINESS`; shipping to paper-test session with dead kill_switch is the OPPOSITE of the sprint goal.

**Recommended close:** Option α HOTFIX (~5 LOC; trivial mirror of backtest call) OR fold into `.B.4` EngineCommon extract. Caramel decision pending.

---

### A2 — Live ML exit-prediction submit path has no backtest equivalent (CRIT; silent train-serve break)

**Verified via direct grep:**
- `CoreFrameworks/EngineSharded.hpp:3142-3227` (~85 LOC) — when `MASK_ML_CFG_USE_EXIT_MODEL` + `state.cores[c].last_exit_prediction > cfg.exit_threshold`, fires `OMS_PushExitForSlot` MARKET_SELL on open positions; sets `last_exit_predicted_bitmap` for v5.13.4 bandit reward attribution.
- `Backtest/BacktestSharded.hpp` + `CoreFrameworks/ShardedBacktestDriver.hpp:189-397` — ZERO hits for `use_exit_model|last_exit_prediction|OMS_PushExitForSlot|MASK_ML_CFG_USE_EXIT_MODEL`. Entire dispatch is live-only.

**Operator-impact:** When operator enables `use_exit_model=1`, backtest exits via TP/SL/time-exit ONLY; live additionally fires ML exit predictions. Trained model never sees the early-exit pattern in backtest equity curve. Bandit reward attribution for exit predictor learns from live with zero training-time signal. Models trained on backtest will systematically under-estimate exit-predictor value; live performance will diverge from backtest projection in either direction.

**Already known?** PARITY-010 covered exit-bandit INIT state parity; this is the DISPATCH parity gap — DIFFERENT concern.

**Severity:** CRIT — silent train-serve break for `use_exit_model=1` users.

**Recommended close:** `.B.4` EngineCommon extract — hoist the exit-prediction submit block into shared `EventLoop_ExitPredictionSubmitOneCore(state, oms, cfg, c, price_d)` helper called from BOTH `EngineSharded:3142` AND `ShardedBacktest_RunTick` slow-path block (`ShardedBacktestDriver.hpp:336+`). ~40 LOC extract + 5 LOC each callsite.

---

### A3 — `ConfidenceScorer_BindCompositeCfg` + `RollingTurnover_Init` missing in backtest (CRIT; silent train-serve drift)

**Verified via direct grep:**
- `CoreFrameworks/EngineSharded.hpp:1125` calls `ConfidenceScorer_Init`; `:1130` calls `ConfidenceScorer_BindCompositeCfg`; `:1138` calls `RollingTurnover_Init` per-core with cfg values (`confidence_freshness_tau_secs`, `confidence_capacity_target_dollars`, `confidence_capacity_kappa`, `confidence_rmse_baseline`, `confidence_turnover_window`, `confidence_turnover_topk`).
- `Backtest/BacktestSharded.hpp:408` calls `ConfidenceScorer_Init` only; `BindCompositeCfg` + `RollingTurnover_Init` ABSENT.

**Operator-impact:** With `confidence_composite_enabled=1`, live uses composite freshness/capacity/RMSE blend; backtest scorer falls back to legacy product mode + EventLoopState_Init defaults (100/3). Training labels + features collected with one composite shape; serving emits a different shape. Bandit_blend_ratio + confidence-gated submission decisions diverge between train and serve.

**Already known?** PARITY-003 closed the BindCompositeCfg parity for the LIVE path (v5.14.1.B.1) but did NOT enforce backtest mirror. NOT in current TECH_DEBT.

**Severity:** CRIT — silent train-serve drift on composite-confidence configs (new feature path; growing surface).

**Recommended close:** `.B.4` EngineCommon extract — 10-LOC block copy from `EngineSharded:1130-1140` to `BacktestSharded:411`. Better: extract to shared `Confidence_BindFromCfg(scorer, turnover, cfg, core_idx)` helper.

---

### A4 — `Strategy_InitPerCore` never called in backtest (pre-v5.4 F7 bug NEVER closed)

**Verified via direct grep:**
- `CoreFrameworks/EngineSharded.hpp:1154` — `tt::Strategy_InitPerCore(&state, i, state.cores[i].strategy_id, &state.cores[i].slow_state->rolling_short, &cfg)` (v5.4.0 Phase 1.3 fix). Comment cites "Pre-v5.4 status: this call was MISSING in the sharded path — the entire strategy state lifecycle was orphaned (postmortem F7)".
- `Backtest/BacktestSharded.hpp` — ZERO hits for `Strategy_InitPerCore`. Backtest started with the F7 bug; live got fixed (v5.4.0 Phase 1.3); backtest still has it.

**Operator-impact:** Strategies with per-core state structs (MeanReversion stateful, Momentum with state, MLStrategy bandit context) train with garbage initial state on first slow-path cycle. Convergence eventually happens after `min_warmup_samples`, but feature/label rows captured pre-convergence pollute training. Same operational mode in live correctly initializes per-core state on boot.

**Already known?** No. The original F7 postmortem fix only patched the live side. NOT in TECH_DEBT or PARITY_ISSUES.

**Severity:** CRIT — silent training data contamination affecting ALL stateful strategies. THIS HAS BEEN BROKEN SINCE v5.4 — every model trained on backtest data since then has training data contamination.

**Recommended close:** `.B.4` EngineCommon extract — 5-LOC add matching `tt::Strategy_InitPerCore` call in `BacktestSharded:411`. Auto-write PARITY entry.

---

## HIGH findings (operator confusion / drift hazard)

### B1 — BNB fee discount applied LIVE-only (33% backtest fee inflation)

**Verified:**
- `CoreFrameworks/EngineSharded.hpp:690-699` — `cfg.pay_fees_in_bnb` multiplies `cfg.cores[c].fee_rate_maker/_taker` by 0.75 per-core at boot.
- `Backtest/BacktestSharded.hpp` — ZERO hits for `pay_fees_in_bnb|bnb_factor`. Backtest uses raw `cfg.fee_rate_*` per core.

**Operator-impact:** Models trained on backtest with `pay_fees_in_bnb=1` see inflated costs → bias toward conservative entry thresholds. Live execution actually pays 0.75x fees → models leave alpha on the table. Equity curves diverge systematically.

**Recommended close:** `.B.4` EngineCommon extract — copy per-core multiply block to `BacktestSharded:215`. Better: extract `Cfg_ApplyBnbDiscount(&cfg)` shared helper.

### B2 — Live uses OneCore (per_core_slow); backtest uses AllCores (centralized)

**Verified:**
- `CoreFrameworks/EngineSharded.hpp:3072` `EventLoop_UpdateRollingStateOneCore`, `:3094` `EventLoop_RebuildOneCore`, `:3231` `EventLoop_TimeExitOneCore`, `:3244` `EventLoop_TrailingSLRatchetOneCore` (per_core_slow thread path — v5.0+ DEFAULT for live).
- `CoreFrameworks/ShardedBacktestDriver.hpp:346` `EventLoop_UpdateRollingStateAllCores`, `:356` `EventLoop_RebuildAllParameters_PerCore`, `:378` `EventLoop_TimeExit`, `:380` `EventLoop_TrailingSLRatchet` (centralized arch path).

**Operator-impact:** Backtest NEVER exercises `cfg.engine_arch=per_core_slow` (LIVE default). Any race / ordering / memory-model bug introduced in per-core-slow lambda body at `EngineSharded:3036-3320` manifests only in live. `parity_harness.cpp:8` tests `engine_mode=single_core` vs `sharded` (both centralized arch); NO harness tests `centralized` vs `per_core_slow`.

**Recommended close:** TWO-STEP. `.B.4` shared-helper extract closes the mirror (semantically equivalent → byte-identical). `.F.5.C` parity_harness extension adds explicit per_core_slow path coverage (NEW harness binary OR third sweep in existing parity_harness).

### B3 — Per-core regime divergence at backtest feature collect

**Verified:**
- `CoreFrameworks/ControllerEventLoop.hpp:2641` `ml_ctx.current_regime_id = state->cores[slot].regime_state.current_regime` — per-core regime state per inference call (live).
- `Backtest/BacktestSharded.hpp:541-548` allocates SINGLE `fc_ctx.regime_state` (not per-core). Line 612: `ctx.current_regime = fc->regime_state.current_regime` — collapses N→1.

**Operator-impact:** Per-core configs with different `regime_hysteresis` (allowed via per-core override) train features with ONE collapsed regime. Live serves with N separate regimes. `regime_class_onehot` + downstream regime-context features systematically drift between training matrix + serve-time inference. Silent.

**Recommended close:** `.B.4` — make `fc_ctx.regime_state` `[MAX_EXECUTION_CORES]`; per-core collection per slot. ~30 LOC.

### B4 — `applies_to_op_mode_cat` registry bit is dormant (sibling to foxml_suite cfg-source-of-truth finding)

**Verified:**
- `CoreFrameworks/CfgFieldRegistry.hpp:184` declares `applies_to_op_mode_cat` column; rows populate it (mostly `OP_MODE_CAT_ALL` sentinel); ZERO READ consumers (no gates anywhere consume the bit).
- Sibling to foxml_suite CRIT-2 — same dormant-metadata pattern.

**Operator-impact:** `backtest_*` cfg fields visible in live Settings panel + LIVE cfg fields visible in backtest Suite panel — no gating. Operator can set `live_only_cfg=X` in backtest cfg + get silent ignore + no warning.

**Recommended close:** `v5.15.6.A/B/C` cfg unification follow-on. Already queued. Fold into foxml_suite TECH_DEBT entry.

### B5 — `bandit_state_prior_path` exists in BacktestRunConfig but not engine.cfg (asymmetric transfer-learning)

**Verified:**
- `Backtest/BacktestEngine.hpp:205` `bandit_state_prior_path[400]` — backtest-only operator-explicit override for transfer-learning.
- Live engine reads bandit state via `EnsembleModelZoo_PostLoadSetup` default path; no cfg field for explicit prior override.

**Operator-impact:** Operator trains new model bundle with sibling-bundle bandit weights as starting prior; ships to production; live boot ignores the prior + starts from per-bundle default. Rare operator path; surfaces on first transfer-learning attempt to live.

**Recommended close:** `.F.5.A` ML framework parity — add equivalent cfg field `bandit_state_prior_path` to `engine.cfg` + matching post-PostLoadSetup override block. TECH_DEBT entry.

---

## MED findings

### C1 — STRUCTURAL FIX (the proportionate-response option D ARCHITECT)

**Surface evidence:** `BacktestSharded.hpp` has 15+ explicit comment citations `"Mirrors EngineSharded_Run lines X-Y"` (lines 141, 152, 162, 167, 233, 269, 350, 404, 430, 447, 470, 664, 761, 811, 872). Class 18 mirror, explicit + comment-acknowledged.

**Operator-impact:** Any future patch to `EngineSharded` boot/slow-path body has 15+ "remember to mirror in backtest" trigger points. Drift accumulates per-patch — findings A1-A4 above are direct evidence drift HAS happened.

**Recommended close — `.B.4` train-serve-execution-layer-parity NEW sub-ship:**

Extract shared helpers in NEW `CoreFrameworks/EngineCommon.hpp`:
- `EngineCommon_BootPerCore(cfg, core_idx, state, oms)` — per-core boot work (ConfigureKillSwitch + BindCompositeCfg + RollingTurnover_Init + Strategy_InitPerCore + BNB fee discount + bandit prior + ...)
- `EngineCommon_SlowPathCycleOneCore(cfg, c, state, oms, price, ts_us)` — per-core slow-path body (UpdateRollingState + RebuildOneCore + TimeExitOneCore + TrailingSLRatchetOneCore + exit-prediction submit + per-core regime collection + ...)

Both `EngineSharded_Run` + `BacktestSharded_Run` call same helpers. Per-call-site differences (live needs ConfigureKillSwitch boot + threading; backtest doesn't need WS staleness + DepthRecorder; etc.) handled via cfg flags or no-op when state nullptr.

**Single largest payoff structural ship — closes A1+A2+A3+A4+B1+B2+B3 SIMULTANEOUSLY.** Boundary-stable refactor (helper signature is the boundary; existing call sites delegate). Per `feedback_proportionate_response_to_audit_findings` Option D ARCHITECT, justified because closures cover 4 CRITs + 3 HIGHs with one structural extract.

### C2 — `parity_harness.cpp` doesn't test backtest-vs-live parity

**Verified:**
- `tests/parity_harness.cpp:8-23` tests `engine_mode=single_core` vs `sharded`. Both consume `Backtest_Run` (training-side). No `EngineSharded_Run` invocation. No live-path coverage.

**Operator-impact:** Operator believes parity_harness validates train↔serve. It doesn't — it validates that legacy backtest produces the same features as sharded backtest. Findings A1-A4 above would all evade this harness. False confidence.

**Recommended close:** `.F.5.C` training harness 1:1 with live execution — explicit ROADMAP scope already queued. New `tests/train_serve_parity_harness.cpp` binary that replays a tick file through `EngineSharded_Run` (paper mode + synthetic data) + compares decision outputs against backtest. Moderate effort (need synthetic-data wrapper around EngineSharded that doesn't require Binance WS).

---

## Meta-discipline gap surfaced (M5 candidate)

**Pattern:** Pre-coding audit gate (`/precoding-audit-gate` + `/parity-check` + `/dod-audit` + `/readiness` + `/trace-deps` + `/merge-scan`) caught zero of these 4 CRITs.

**Why:** Existing audit suite walks the cfg/stamp/drift surface (M1+M2 train-serve cfg-parity disciplines). It does NOT walk the boot + slow-path lifecycle surface. The audits are layer-specific; the gap was layer-coverage, not audit-rigor.

**Codification target — M5: train-serve EXECUTION-LAYER parity meta-discipline**
- NEW DESIGN_SPEC at `DESIGN_SPECS/meta-disciplines/train-serve-execution-layer-parity.md` — codifies the audit walk: for every Init/Bind/Configure call in EngineSharded boot, verify matching call in BacktestSharded boot; for every slow-path-cycle dispatch in EngineSharded body, verify matching dispatch in BacktestSharded body.
- NEW SKILL `/train-serve-asymmetry-sweep <layer>` — parameterized agent prompt (layer keyword = execution / oms / gui / boot / logging / stamp-cohort / datastream). Today's prompt shape captured for future-Claude reuse.
- AMEND `implementation-layer-blindspot-taxonomy.md` — add B14 train-serve execution parity to 12-category taxonomy.
- AMEND `/readiness` Check 40 — verify any new boot-time Init/Bind call has matching backtest mirror site OR documented exemption.
- AMEND `DOCS/DESIGN_PHILOSOPHY.md § 11.5` — add M5 row to meta-discipline registry.
- NEW feedback memory `feedback_train_serve_execution_layer_meta_gap` — operator-collaboration rule for surfacing this discipline at HIGH-RISK boot/slow-path-touching ships.

**Codifies at `.B.4` ship close per `pattern-codification-lifecycle.md`** (first canonical lands AT the structural close, not before).

---

## Closure matrix — every finding has a home

| Finding | Home sub-ship | Status |
|---|---|---|
| A1 kill_switch dead | Hotfix today OR `.B.4` | Decision pending |
| A2 exit-model submit gap | `.B.4` EngineCommon extract | Queued |
| A3 BindCompositeCfg missing | `.B.4` EngineCommon extract | Queued |
| A4 Strategy_InitPerCore missing | `.B.4` EngineCommon extract | Queued |
| B1 BNB fee discount live-only | `.B.4` EngineCommon extract | Queued |
| B2 OneCore vs AllCores arch | `.B.4` (mirror close) + `.F.5.C` (harness test) | Two-step |
| B3 per-core regime collapse | `.B.4` EngineCommon extract | Queued |
| B4 op_mode_cat dormant | `v5.15.6.A/B/C` cfg unification | Already queued |
| B5 bandit_state_prior_path asymmetric | `.F.5.A` ML framework parity | Queued |
| C1 EngineCommon extract structural | `.B.4` IS this | Queued |
| C2 parity_harness inadequate | `.F.5.C` training harness 1:1 | Already queued |
| M5 meta-discipline codification | `.B.4` ship close auto-write | Codifies WITH the close |

**Every finding has a named home. Sprint close runway ~3-4 weeks focused.**

---

## Cross-references

- Operator concern surfaced: 2026-05-24 mid-`.B.3` audit cycle
- Sister audit reports same day: opp-scan / dead-code-trace / `/readiness` / `/dod-audit` / `/parity-check` / foxml_suite-cfg-source-of-truth (all at `plans/v5.15-live-readiness/plan_checks/2026-05-24-*`)
- Plan body context: `.B.3` v1.17 at `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md`
- Sprint MASTER: `plans/v5.15-live-readiness/MASTER.md` + `ROADMAP-2026-05-17-to-paper-test.md`
- Decoupling endgoal positioning: `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` — `.B.4` closes a major Class 18 mirror that positions cleanly for v6.0 viewer split (`EngineCommon.hpp` becomes the natural runtime/viewer boundary)
- Operator framing memories cited: `feedback_motivated_collaborator_for_caramel` / `feedback_proportionate_response_to_audit_findings` / `feedback_plan_right_not_fast` / `feedback_no_defer_for_effort` / `user_mvp_to_professional_transition`

---

**End of audit report.** Full agent investigation log (~640s; 86 tool uses; 171k tokens) — agent ID `a515baff4a2af8c1a` for reference. Verified via direct grep cross-checks. All 4 CRITs + B1 are real findings against current HEAD.
