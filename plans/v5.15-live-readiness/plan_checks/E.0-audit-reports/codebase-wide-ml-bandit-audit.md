---
type: audit-report
audit: ml-bandit-correctness
scope: codebase-wide
target_ship: v5.15.5.F.4d.1.E.0
engine_head: 61ae3cc (v5.15.5.F.4d.1.D)
date: 2026-05-28
audit_methodology: >
  4 parallel deep-read agents (bandit-core / bandit-integration / ml-training / ml-backtest)
  over FoxML_Trader_v2 ML_Headers/ + Backtest/ + CoreFrameworks/ reward-wiring, followed by
  operator-side (Claude) personal verification of every CRITICAL/HIGH claim via targeted reads
  + decisive greps. READ-ONLY scan — NO engine code or existing plans modified.
verification_legend:
  - "[VERIFIED]   — Claude personally read the cited code + confirmed."
  - "[GREP-VERIFIED] — confirmed by exhaustive call-graph grep (writers/callers)."
  - "[CROSS-CONFIRMED] — two independent agents found it with matching line cites."
  - "[REPORTED]   — single-agent finding with specific cite; spot-check at triage."
  - "[SUSPECTED]  — strong static evidence; needs a runtime check to confirm."
prior_runs:
  - 2026-05-28-... codebase-wide-bug-check.md (Class 1-35 registry scan; GREEN-WITH-NOTES)
sister_docs:
  - plans/v5.15-live-readiness/ROADMAP-2026-05-17-to-paper-test.md (paper-test milestone these findings gate)
  - subplans/2026-05-16-v5.15.5.F.4d-merged-framework-bandit-thompson.md (bandit design intent)
  - DESIGN_SPECS (planned) meta-disciplines/backtest-paper-live-convergence-discipline.md (.E.1)
---

# Codebase-wide ML + Bandit correctness audit (`.E.0` Phase A — 5th codebase-wide audit)

**Triggered by:** operator request to scan the bandit architecture + ML backtesting/model-training for
bugs, drift, and improvement opportunities, and to recommend how the findings slot into the `.E` sub-sprint.

**Posture:** This is an additive analysis artifact. No engine source and no existing plan was modified
during this audit.

---

## Verdict

**YELLOW → RED-FOR-PAPER-TEST.** The framework scaffolding (the `FOREACH_BANDIT_ALGORITHM`
5-state dispatch, the `.F.4d` Class 24 Thompson-update fix, determinism hygiene, RidgeBlender +
FeatureStandardizer math) is **sound** — the `.F.4d` registry work landed correctly and the
determinism story is genuinely strong. But the audit surfaced **three independent
backtest/serve correctness gaps that invalidate the model-evaluation pipeline the operator is about to
rely on for the paper-test → live decision**, plus a cluster of bandit reward-attribution and
telemetry-wiring drift.

The headline risk is not "live trading is wrong" — live fills come from the real exchange. The risk is
that **the numbers used to decide whether to go live are optimistic/skewed**:

1. **[CRITICAL] Train/serve standardization skew** — models are trained on **raw** features but served
   **standardized** features. Every served prediction (and every bandit reward derived from it) is fed
   through a transform the model never saw at train time.
2. **[CRITICAL→HIGH] Simulated slippage is dead in all mode-1 paths** — `slippage_pct` is wired only into
   the legacy `OnEvent` body that the sharded (mode-1) production + backtest path skips. Backtest/paper
   P&L is fee-only, no slippage, despite the cfg field + GUI claiming otherwise.
3. **[HIGH-SUSPECTED] Backtest may not route hot-path gate trades to the OMS** — the sharded backtest
   drains via `EventLoop_DrainEvents` (non-submitting) where live uses `DrainWithSubmit` (submitting);
   needs a 5-minute runtime check to confirm/refute.

None of these block the `.E.1` Foundation infra work. **All three should be remediated before the
paper-test milestone** (`ROADMAP-2026-05-17-to-paper-test.md`), because they directly undermine the
`backtest → paper → live convergence discipline` that `.E.1` is scheduled to codify.

The bandit core itself has a **mathematical mismatch worth fixing** (Exp3 importance-weighting applied to
a full-information reward feed) and **no non-stationarity handling** — which is both a finding and the
natural launch-point for the "new algorithms" exploration the operator asked for (§ 6).

---

## 1. Findings summary (triage table)

Severity-sorted. "Live?" = does it affect live-money execution correctness (vs. backtest/paper realism
or telemetry). Cites are `file:line` in `~/code/FoxML_Trader_v2`.

| # | Sev | Surface | Finding | Live? | Confidence |
|---|---|---|---|---|---|
| F1 | **CRITICAL** | ML train/serve | Model trained on RAW features, served on STANDARDIZED features | yes (every ML pred) | [VERIFIED] |
| F2 | **HIGH** | Backtest/paper | `slippage_pct` never applied in any mode-1 path (orphaned in skipped mode-0 `OnEvent`) | paper/backtest only | [VERIFIED] |
| F3 | **HIGH** | Backtest | Hot-path gate trades may never reach OMS in sharded backtest (drain ≠ live drain) | backtest only | [SUSPECTED] |
| F4 | **HIGH** | Bandit core | Exp3 importance-weight `reward/p_arm` applied to a FULL-INFORMATION per-arm reward feed | learning quality | [VERIFIED] |
| F5 | **HIGH** | Bandit persist | Thompson posterior loaded at boot but NEVER saved → resets to prior every restart | learning persistence | [GREP-VERIFIED] |
| F6 | **HIGH** | ML train | WF + held-out hardcode `n_rounds=200` / default hyperparams ≠ deployed model | eval validity | [CROSS-CONFIRMED] |
| F7 | **HIGH** | ML eval | Held-out split has NO purge/embargo gap → label-horizon leakage | eval validity | [GREP-VERIFIED] |
| F8 | **MED** | Bandit core | `total_steps` increments per-ARM (×n_arms/event) → corrupts eta schedule + blend ramp | learning dynamics | [VERIFIED] |
| F9 | **MED** | Bandit attrib | Buy-side trade-close reward attributed to "most recent" predict record, not the entry's | learning quality | [VERIFIED] |
| F10 | **MED** | Bandit telem | `bandit_reward_bps[]` enrolled + read at calib, never written → calib column constant-0 | observability | [GREP-VERIFIED] |
| F11 | **MED** | Bandit telem | `MBS_OrderSetBanditContext` never called in prod → 3 calib cols dead + Thompson telem mis-regime'd | observability | [GREP-VERIFIED] |
| F12 | **MED** | ML train | Regression labels with NaN/incomplete horizon silently relabeled to `0.0` and trained on | model bias | [REPORTED] |
| F13 | **MED** | ML train | Multiclass weight-cap (anti-segfault) applied in WF only, not held-out / train-worker | crash + eval skew | [REPORTED] |
| F14 | **MED** | ML train | `label_kind == 2` used as "regression" in multi-horizon worker (regression is kind 1; inverted) | metric corruption | [REPORTED] |
| F15 | **MED** | ML eval | Held-out re-run every click + self-unlock; no multiple-testing / PBO control | overfitting | [CROSS-CONFIRMED] |
| F16 | **MED** | Backtest | Purge gap computed in TICK units, applied as SAMPLE-index count, then density-scaled | eval rigor | [CROSS-CONFIRMED] |
| F17 | **MED** | Bandit design | Neither Exp3 nor Thompson forgets — stationary learners on a non-stationary market | learning quality | [VERIFIED] |
| F18 | **MED** | Backtest | SL/TP fills at the exact trigger price (no gap-through, no spread) — optimistic | paper/backtest | [VERIFIED] |
| F19 | **LOW** | ML train | Winsor fit silently disabled for any run > 8192 samples (stack-buffer cap) → dead at prod scale | feature quality | [REPORTED] |
| F20 | **LOW** | Bandit core | "Exp3-IX" in name only — no implicit-exploration (`+γ` denom) term; it's plain Exp3 | doc/correctness | [VERIFIED] |
| F21 | **LOW** | Bandit core | cfg=2 telemetry `Thompson_Sample` advances PERSISTED rng_state → cross-mode replay drift | determinism (minor) | [VERIFIED] |
| F22 | **LOW** | ML serve | Scaler-load failure defaults to "serve anyway with identity" when `held_out_gate_strict=0` | live foot-gun | [REPORTED] |

Plus a drift inventory (§ 4) and improvement / new-algorithm sections (§ 5–6).

---

## 2. Bandit architecture findings (detail)

The bandit lives in `ML_Headers/` and is **slow-path-only** (per-core, no hot-path involvement). The
`.F.4d` 5-state `FOREACH_BANDIT_ALGORITHM` registry (EXP3 / THOMPSON / EXP3_OP_THOMPSON_GHOST /
THOMPSON_OP_EXP3_GHOST / BLENDED) is well-built; the dispatch tables, masks, density asserts, and the
Class 24 Thompson-update fix all verified correct. Findings are about the *math fed into it* and the
*wiring around it*, not the registry.

### F4 [HIGH][VERIFIED] — Exp3 importance-weighting applied to a full-information reward feed

- `ML_Headers/BanditLearning.hpp:297` — `double r_hat = reward_bps / p_arm;` then
  `weights[arm] *= exp(eta * r_hat)` (`:309`).
- `ML_Headers/CoreModelZoo.hpp:1386-1397` (lookback) and `:1463-1474` (trade-close) — the reward loop
  grades **every** arm independently (`for (int a=0; a<n_arms; ++a) { correct = ((p>0.5)==(delta>0)); reward = ±50; g_buy_reward_dispatch[algo](ezoo,regime,a,reward); }`).

**What's wrong.** Dividing the observed reward by `p_arm` is the Exp3 device for building an *unbiased
estimate of the full reward vector from a single observed arm* under **bandit (partial) feedback**. But
the feed here is **full-information**: each arm's own prediction is observed and graded every event. Under
full information the correct exponential-weights (Hedge) update is `w_a *= exp(eta · reward_a)` with **no**
`/p_a`. Dividing a genuinely-observed per-arm reward by that arm's own selection probability inflates the
effective learning rate for under-explored arms by `1/p_a` (capped by the `γ/K` mixing floor at ~`K/γ` =
5/0.05 = 100×). A starved arm's next *real* reward is amplified up to ~100×, driving oscillation / weight
collapse instead of smooth convergence.

**Why this happened (not a careless bug).** It's a faithful port of the FoxML `bandit.py` Exp3 (header
comments), which assumed bandit feedback. Nobody re-derived the estimator when the per-arm grading loop
(full-info) was written. Note: if the engine updated *only* the single driving arm (`bandit_chosen_arm`,
which IS captured), `/p_chosen` would be correct.

**Fix direction.** Either (a) switch to **Hedge** under full-info — drop `/p_arm`, update all arms with raw
per-arm reward (more sample-efficient since the per-arm signal is genuinely available); or (b) keep Exp3
and update **only** the chosen arm with `/p_chosen`. Make the choice explicit via a `BanditFeedbackMode`
enum (a natural FOREACH-registry citizen) so it's auditable and A/B-able. (a) is the better fit.

### F5 [HIGH][GREP-VERIFIED] — Thompson posterior loaded at boot but never saved

- Boot load IS wired (`FOREACH_ENSEMBLE_POST_LOAD` → `load_thompson_state` / `load_exit_thompson_state`).
- Save fns `EnsembleModelZoo_SaveThompsonState` (`CoreModelZoo.hpp:2370`) and `_SaveExitThompsonState`
  (`:2459`) are fully implemented (atomic write, SHA/bundle binding, locale pinning) but have **zero
  production callers** — only `tests/controller_test.cpp:23549`. The shutdown loop + periodic-save wire
  only the two **Exp3** saves.

**Impact.** Any operator running `cfg.bandit_algorithm ∈ {1,2,3,4}` (THOMPSON / ghost / BLENDED) loses all
Thompson online learning on every restart — the load finds no file and silently re-starts from
uninformative priors. This defeats the persistence machinery's stated purpose. **Load-without-save
asymmetry.**

**Fix direction.** Add the two Thompson saves to the shutdown loop (next to the Exp3 saves), gated by
`MASK_EZOO_BUY_THOMPSON_READY` / `MASK_EZOO_EXIT_THOMPSON_READY`; also enroll all four state families in
`EnsembleModelZoo_MaybeSaveBanditPeriodic` so a crash (no clean shutdown) doesn't lose learning.
**Structural fix:** the load side is already an X-macro registry (`FOREACH_ENSEMBLE_POST_LOAD`) but the
save side is hand-maintained — that asymmetry *is* what produced this gap. A sister `FOREACH_BANDIT_PERSIST`
registry (save mirrors load) makes "added a load step, forgot the save" a compile error (Class 18 close).

### F8 [MED][VERIFIED] — `total_steps` increments per-arm, not per-event

- `ML_Headers/BanditLearning.hpp:287` — `b->total_steps++;` inside `Bandit_Update`, which is called once
  **per arm** in the reward loops (`CoreModelZoo.hpp:1397`).

**Impact.** For an N-arm ensemble, one reward event bumps `total_steps` by N. Two consequences:
(1) the adaptive `eta = sqrt(ln K / (K·T))` (`:304`) decays N× too fast; (2) `Bandit_EffectiveBlend`
(`:352-358`) gates the documented "100 trades before bandit activates / 100 to ramp" schedule on
`total_steps`, so the blend actually engages after ~100/N events. `pulls[arm]` is also bumped for every
arm each event, so "pulls" no longer means "times selected" (all arms show equal counts).

**Fix direction.** Increment `total_steps` once per reward *event* (a `Bandit_BeginEvent(b)` that also
snapshots `probs[]` + computes `eta` once — see F4 + the O(N²) note below), with per-arm updates taking
`eta`/`probs` as parameters. Fixes F4-context, F8, and the order-dependence in one refactor.

### F9 [MED][VERIFIED] — Buy-side trade-close reward credits the "most recent" predict record

- `ML_Headers/CoreModelZoo.hpp:1436-1452` — `EnsembleModelZoo_TradeCloseReward` walks the ring backward
  and rewards the FIRST not-yet-trade-rewarded record (the most recent predict). The function's own comment
  (`:1415-1417`) calls it "a proxy for the model recommendation that drove this trade."

**Impact.** The slow path runs a predict every `poll_interval` ticks, so by the time a trade closes (often
thousands of ticks later) the "most recent" record is a later cycle, not the entry cycle. The buy bandit's
highest-signal reward (real money, ×4 weight) is graded against predictions from the wrong cycle.
Mitigation: it's full-info per-arm (each arm graded by its own stored prediction), so it's not a single
wrong-arm credit — but the prediction *values* belong to the wrong cycle. The **exit side does this
correctly** (stores chosen arm + regime per-slot at submit via `last_exit_predicted_meta`,
`ControllerEventLoop.hpp:1733`).

**Fix direction.** Bind the driving prediction-record index (or the per-arm prediction snapshot) to the
Order/slot at entry — reuse the exit-side per-slot pattern — and reward THAT record. This *also* gives the
dead `bandit_reward_bps[]` (F10) and the unset Order bandit bits (F11) a real producer: **one pattern
closes three findings.**

### F10 [MED][GREP-VERIFIED] — `bandit_reward_bps[]` enrolled + read, never written

- Read at `CoreFrameworks/OrderManager.hpp:700` (`reward_bps_attributed = oms->bandit_reward_bps[pslot]`);
  enrolled in `FOREACH_OMS_PER_SLOT_FIELD` (`OmsFieldRegistry.hpp:342`); **written nowhere** in production
  (grep confirms: struct decl, registry, comments, and one test only). The actual exit reward
  (`reward_bps = actual_pnl_bps − hypothetical`) is computed at `ControllerEventLoop.hpp:1756` and fed to
  the dispatch table — never stored into the slot array.

**Impact.** The calib-log column `reward_bps_attributed` (`CalibLogColRegistry.hpp:90`) emits `0.0` for
every fill. Offline bandit-decision analysis using this CSV is silently zero. Comments at
`OmsFieldRegistry.hpp:337` + `OrderManager.hpp:416` claim "Written at HandleFill SELL" — but `handle_sell_fill`
(`OrderManager.hpp:1158-1214`) has no such write. **Drift between `.F.4d` Step 7 scaffolding (field/bits/columns landed) and the producer write (never landed).**

**Fix direction.** Write the computed `reward_bps` into `oms->bandit_reward_bps[slot]` at the exit-reward
site, or remove the field + column if unused. Given the column exists to capture it, write it (folds into
F9's per-slot-bind fix).

### F11 [MED][GREP-VERIFIED] — `MBS_OrderSetBanditContext` never called in production

- Setter at `CoreFrameworks/Order.hpp:292`; only caller is `tests/controller_test.cpp:23852`.
  `Order_BindPreResolved` (`:355-364`) sets fee_rate + slippage + the pre-resolved bit but does **not** call
  it, despite comments (`Order.hpp:118`, `273`) claiming it does.

**Impact.** `flags_packed` bandit bits (active_state / regime / chosen_arm) stay 0 in production. In
`real_on_exit_calibration` (`OrderManager.hpp:694-718`) the decoded `bandit_algorithm`, `regime_id_at_emit`,
`chosen_arm` calib columns are constant-0, and — worse — `regime_clamped` (`:716`) is derived from
`bandit_regime=0`, so the **32 per-arm Thompson telemetry columns always read regime-0** regardless of the
trade's actual regime. Telemetry is mis-regime'd for every non-RANGING trade.

**Fix direction.** Call `MBS_OrderSetBanditContext(o, cfg.bandit_algorithm, regime_at_decision, chosen_arm)`
at entry-order construction (where `last_predicted_buy_thompson_arm` is already captured,
`StrategyParameters.hpp:980`). `Order_BindPreResolved` can't (no bandit args in scope) — extend its
signature or set at the submit caller.

### F17 [MED][VERIFIED] — Stationary learners on a non-stationary market

- `ML_Headers/BanditLearning.hpp` — `cum_reward` is a pure running sum; `eta → 0` as `T → ∞` (`:304`);
  no decay/discount anywhere (grep: zero `decay|discount|forget|sliding-window|half-life`).
- `ML_Headers/ThompsonBandit.hpp:183-193` — `precision_post = precision_old + precision_obs` grows
  unboundedly → `sigma = 1/sqrt(precision) → 0` → samples collapse to `mu_post` → **exploration stops
  permanently**, anchored to a mean computed across all historical regimes.

**Impact.** `ThompsonBandit.hpp:13-15` names non-stationarity as the reason Thompson exists, but both
algorithms are stationary learners — they cannot track a regime shift (the whole premise). A valid v1, but
a latent design limitation worth flagging loudly, and the direct motivation for § 6 (new algorithms).

**Fix direction.** Discounted Thompson (`precision_post = ρ·precision_post + precision_obs`, ρ∈(0,1)) and/or
EXP3.S fixed-share for Exp3. See § 6 — this is the single highest-value "spicy" upgrade and a 1-row
registry add.

### Lower-severity bandit findings (verified)

- **F20 [LOW] "Exp3-IX" is plain Exp3.** `BanditLearning.hpp:297` has no additive `+γ_ix` denominator term
  (Neu 2015 IX). The variance-control the name advertises is absent — which is exactly the F4 instability.
  Rename to "Exp3" OR actually implement IX (`r_hat = reward / (p_arm + γ_ix)`).
- **F21 [LOW] cfg=2 telemetry sampling perturbs persisted RNG.** `BanditAlgorithmRegistry.hpp:371`
  `(void)Thompson_Sample(thompson)` advances the persisted `rng_state` for a discarded value; cfg=0/4 don't
  advance, cfg=1/3 advance for the real pick. Flipping modes mid-run desyncs the replay-locked stream. Fix:
  sample from a clone (the `Thompson_GetProbabilities` pattern already does this).
- **O(N²) order-dependence (note).** `Bandit_GetProbabilities` is recomputed inside `Bandit_Update`
  (`BanditLearning.hpp:293`) → called N×/event, and weights mutate between calls so arm `k` is weighted
  against probs already shifted by arms `0..k-1`. Determinism preserved (fixed order) but path-dependent.
  Snapshot `probs[]` once before the loop (folds into the F8 refactor).

**Verified NOT bugs (checked, intentional/correct):** the AVX-512↔scalar bytewise-identical
`Bandit_GetProbabilities`; `Thompson_GetSoftmaxWeights` overflow-safe softmax; `BanditAlgo_Blended_Apply`
renorm (no double-count); the Gaussian conjugate `Thompson_Update`; the Class 24 fix wiring
(`g_*_reward_dispatch` mask-derived, `BANDIT_THOMPSON_UPDATE_MASK=0x1E`); Box-Muller `log(0)` guard;
per-regime/per-side RNG seed decorrelation; `double` usage (slow-path ML, not accounting → not an H4/H9
violation; bandit state enters no HMAC-signed body). RidgeBlender (λI regularization, degenerate-case
handling) and FeatureStandardizer (train-fit/serve-apply, no refit at serve) are clean. Multi-core bandit
isolation is clean (no global cross-core read; no Class 26).

---

## 3. ML training + backtest findings (detail)

### F1 [CRITICAL][VERIFIED] — Train on RAW features, serve on STANDARDIZED features

- **Train (raw):** `XGDMatrixCreateFromMat(train_features, …)` at `BacktestPanels.hpp:3009` (train worker),
  `BacktestEngine.hpp:1547` (WF), `:2084` (held-out), `BacktestPanels.hpp:3657` (multi-horizon) — all on the
  **raw** `feature_matrix`. The scaler is **computed** *after* training (`BacktestPanels.hpp:3229`
  `FeatureStandardizer_Compute`, `:3242` `_FitWinsor`) and persisted as a `.scaler` sidecar — but
  `FeatureStandardizer_Apply` is **never called on any training matrix** (grep: `_Apply` is absent from
  `Backtest/`).
- **Serve (standardized):** `FeatureStandardizer_Apply` IS called before predict at
  `Strategies/MLStrategy.hpp:154`, `Strategies/StrategyParameters.hpp:843` (barrier) + `:882` (buy_signal),
  gated by `has_scaler` (set to 1 by `_Compute`).

**Why it's a bug.** XGBoost split thresholds learned in raw-feature space (`feature_i < threshold_raw`) are
evaluated at serve against `(feature_i − mean)/std` (plus winsor clipping the model never saw). Virtually
every split routes incorrectly. This is the single largest train/serve skew in the codebase and directly
contradicts the train-serve-parity discipline. (Trees are scale-invariant *only if the transform is
consistent across train and serve* — here it's serve-only.) Affects every model trained via the v5.9.3+
scaler-sidecar path; legacy models with `has_scaler=0` are unaffected (identity no-op).

**Fix direction.** Pick ONE representation and use it at both ends: either standardize `train_features`
in place (`_Compute` + `_FitWinsor` *then* `_Apply`) before `XGDMatrixCreateFromMat` at all four training
sites, OR drop the serve-side `_Apply` entirely (cleanest for trees — they barely benefit from
standardization). Add a CI/parity assertion that train and serve feed identical representations.

### F2 [HIGH][VERIFIED] — `slippage_pct` never applied in any mode-1 path

- Applied **only** in the mode-0 `OnEvent` body: `ControllerEventLoop.hpp:1869` reads
  `effective_cores[slip_idx].slippage_pct`, `:1885` adjusts a **local** `event.price` copy — then `:1903`
  `if (!should_apply) return;` early-returns in mode-1 (the local copy is discarded).
- The live drainer `EngineSharded_Async_DrainWithSubmit` (`Async.hpp:863-872`) builds the `SubmitCommand`
  with `cmd.event_price = event.price` (raw, no slippage). `handle_buy_fill` / `handle_sell_fill`
  (`OrderManager.hpp:1142-1190`) apply `pre_resolved.fee_rate` only — **no slippage**.
- `o->pre_resolved.slippage_pct` is *written* (`Order.hpp:361`) but **never read** in the fill path (grep).

**Why it's a bug.** Sharded production runs mode-1 (live + the backtest both force it). Live fills come from
the real exchange (real slippage), so this is harmless for live — but **paper mode and the backtest both
fill at the exact trigger price with fees only**. The cfg field (default 0.05%), the GUI display
(`ShardedSnapshot.hpp:344`), and the comments all imply slippage is modeled. For a sub-µs strategy taking
many small-edge trades, omitting slippage materially inflates expected edge — exactly the number the
paper-test go-live decision hinges on.

**Fix direction.** Apply `slippage_pct` at the mode-1 fill: either adjust `cmd.event_price` in
`DrainWithSubmit` (and mirror in the backtest drain), or read it in `handle_*_fill` (worsen BUY entry up,
SELL exit down). Add a test asserting nonzero `slippage_pct` changes realized P&L for a fixed trade.

### F3 [HIGH-SUSPECTED] — Backtest may not route hot-path gate trades to the OMS

**Static evidence chain (all verified):**
1. `BacktestSharded.hpp:189` forces `event_log_mode=1` *specifically for live parity* (comment `:162-166`:
   "so backtest uses the same fill+drain path as live").
2. The backtest per-tick driver (`ShardedBacktestDriver.hpp:203`, used by `BacktestSharded_Run` at
   `BacktestSharded.hpp:672`) drains via `EventLoop_DrainEvents`.
3. `EventLoop_DrainEvents` (`ControllerEventLoop.hpp:2026-2040`) calls **only** `EventLoop_OnEvent` per
   event — it does **not** push to the OMS submit queue.
4. `EventLoop_OnEvent` early-returns in mode-1 (`:1903`; the inline comment says "mode-1 (production
   sharded) → skip body").
5. The **live** path instead uses `EngineSharded_Async_DrainWithSubmit` (`Async.hpp:872`,
   `OMS_PushSubmit`) — the *only* hot-path→OMS submit path, and it is **never called by either backtest
   path** (grep: `DrainWithSubmit` callers = `Run.hpp:1491/1516` only).
6. The only slow-path OMS submits are **exits** (time-exit, ML exit-predictor `SlowPath.hpp:145`, flatten
   `EngineCommon.hpp`, force-close `ControllerEventLoop.hpp:3356`) — there is no slow-path **entry** submit.

**Implication if the chain holds:** hot-path BG/SG entries + exits are popped and discarded in the mode-1
backtest; since all entries originate on the hot path, **gate-strategy (and ML) entries would never open**
in the sharded backtest — a total execution-parity break vs live.

**Why I did NOT mark this CONFIRMED:** the backtest's win/loss + equity-curve tracking
(`BacktestSharded.hpp:737-759`) actively expects trades, and the operator clearly runs backtests — so
either a compensating path exists that static reading can't see, or the backtest is primarily exercised for
ML feature/label/WF generation (which is execution-independent) and the gate-P&L gap went unnoticed.

**Confirmation step (≈5 min, no code change):** run a sharded backtest with `core_0_strategy=simple_dip`
(no ML), check `stats.total_trades` / `state.total_entries`. If 0 → **CONFIRMED CRITICAL** (close by routing
the backtest drain through a shared event→submit helper so backtest + live use one path). If >0 →
downgrade to "execution-path divergence worth unifying" + the slippage gap (F2) stands regardless.

### F6 [HIGH][CROSS-CONFIRMED] — WF + held-out use different hyperparameters than the deployed model

- `BacktestEngine.hpp:1674` (WF) and `:2140` (held-out) hardcode `n_rounds = 200`. The deployed model uses
  operator `snap_n_estimators` (`BacktestPanels.hpp:3099`). Held-out additionally uses
  `XGBHyperparams_Defaults()` (`:2120`), ignoring cfg `subsample`/`colsample`/`min_child_weight`/`seed`,
  which WF *does* copy (`:1605-1616`). The code comment at `:2101` explicitly says held-out hyperparams
  "MUST match … Diverging here = drift between gap measurement and reality" — and the code diverges.

**Impact.** The WF/held-out generalization gap measures a different model than the one stamped + deployed.
Overfit-gate thresholds are evaluated on the wrong bias/variance point.

**Fix direction.** Extract `XGBHyperparams_FromCfg(cfg)` used by WF + held-out + the train worker (single
source of truth); promote `n_estimators` to a cfg field so it round-trips.

### F7 [HIGH][GREP-VERIFIED] — Held-out split has no purge/embargo gap

- Purge logic (`PurgeGap_Compute = max(horizon, max_feature_lookback) + buffer`) lives only in
  `ValidationSplit.hpp` (the WF path). `HeldOutSplit.hpp` has **no** purge/embargo (grep returns nothing).
  The held-out split is a strict cut at `trainval_end_idx` (`BacktestEngine.hpp:2036-2079`).

**Impact.** The last `horizon` training samples have forward-looking label windows that extend into the
held-out eval region → label-horizon leakage → the "unbiased final estimate" + the headline
`wf_to_held_out_gap` are optimistically biased. The held-out path is the *deployment proxy*; an un-purged
boundary defeats its purpose.

**Fix direction.** Reserve a purge band of `PurgeGap_Compute(horizon, buffer)` (converted to sample-index
units — see F16) before `trainval_end_idx`, exclude from both train and eval; add a post-test embargo.

### Medium ML findings

- **F12 [MED][REPORTED] Regression NaN → 0.0 relabel.** `BacktestEngine.hpp:779-780` substitutes `0.0f` for
  NaN/Inf regression labels (incomplete horizon, `sample_price<=0`) instead of dropping. `filter_nan` is
  multiclass-only (`:1434`, `:2033`). Injects fake "zero return" labels at every data-tail, biasing the
  regressor toward 0. Fix: drop on any non-finite label for regression too (all four training sites).
- **F13 [MED][REPORTED] Multiclass weight-cap inconsistent.** The `WEIGHT_CAP=5.0` that stops XGBoost
  histogram-split segfaults on rare classes (`BacktestEngine.hpp:1642`, WF) is **absent** in
  `HeldOutSplit_TrainEval` (`:2134`), the train worker (`BacktestPanels.hpp:3064`), and the multi-horizon
  loop. Same crash can recur; deployed model uses uncapped weights while WF measures capped. Fix: move the
  cap into `XGBoost_ComputeMulticlassWeights` (single source).
- **F14 [MED][REPORTED] `label_kind==2` treated as regression.** `BacktestPanels.hpp:3723/3726/3784` select
  correlation/MSE metrics when `label_kind==2`, but regression = kind **1** (`LabelFunctions.hpp:440`;
  authoritative sites use `==1`). Inverted: regression labels get accuracy, 2-class labels get correlation.
  Corrupts per-horizon sidecar metrics + bandit-init ranking. Fix: `==1`; add `LabelKind_IsRegression()`.
- **F15 [MED][CROSS-CONFIRMED] Held-out self-unlock + no multiple-testing control.** Both held-out call
  sites unlock the split with its own token (`BacktestPanels.hpp:2814/3577`) — lock discipline is
  friction-only. Sweeps pick `best_idx` by max metric over a grid with no deflation/PBO/Bonferroni, and
  nothing tracks held-out evaluation count. Re-evaluating across trials turns held-out into a validation
  set. Fix: evaluation-budget counter + deflated-Sharpe/PBO (§ 6).
- **F16 [MED][CROSS-CONFIRMED] Purge gap unit confusion.** `PurgeGap_Compute` returns **ticks**, but it's
  applied as a count of **sample indices** (`ValidationSplit_GenerateExplicit`) then density-scaled.
  Samples are sparse (1 sample ≈ `poll_interval` ticks), so this generally over-purges (conservative) but
  is not principled — under some `poll_interval`/density/horizon combos it may under-cover the label
  horizon. Fix: convert to sample units (`ceil(horizon_ticks / poll_interval)`) explicitly.
- **F18 [MED][VERIFIED] Optimistic SL/TP fills.** SG fires at `tick.price >= effective_tp` / `<= sl` and
  the synthetic fill uses that exact crossing tick (`OrderManager.hpp:992`), with no slippage (F2) and no
  gap-through/spread. Real stop-losses fill worse. Underestimates downside.

### Low ML findings

- **F19 [LOW][REPORTED] Winsor fit dead at prod scale.** `FeatureStandardizer.hpp:411-415`:
  `double col[8192]; if (num_samples > 8192) { has_winsor_bounds=0; return; }`. Real training sets are
  10^5–10^6 samples → winsorization silently no-ops (bounds stay ±INF). Heap-allocate or stream the
  percentile computation; WARN when the cap disables the fit.
- **F22 [LOW][REPORTED] Scaler-load-failure serves identity.** With `held_out_gate_strict=0` (default,
  `engine.cfg.example:677`), a scaler SHA mismatch logs `[CRITICAL] … engine continuing` and serves with an
  identity scaler (`CoreModelZoo.hpp:466-505`). Combined with F1, the default posture serves a model whose
  transform doesn't match its stamp. Consider strict-by-default for live.

**Determinism (verified strong, NOT flagged):** XGBoost seed pinned; `nthread` defaults to 1 with explicit
"breaks reproducibility if >1" docs; no unordered containers / wall-clock / pointer-order in training;
shared `Features_PackAll` for train+serve feature parity; stamp/SHA model-const binding. This is the
codebase's genuine strength. (One minor non-determinism: trade-log `submitted_at_us` uses wall-clock
`system_clock::now()` → CSV non-byte-reproducible, but P&L/stats use tick-derived values so results are
deterministic.)

---

## 4. Drift inventory (half-wired / dead / stale)

Distinct from bugs — these are codification/wiring gaps and stale docs (operator cares about not accreting
tech debt):

- **`.F.4d` Step 7 telemetry half-landed** — `bandit_reward_bps[]` (F10), Order bandit-context bits (F11),
  and 4 calib columns: the registry/struct/accessor/column scaffolding shipped, the **producer writes did
  not**. Comments at `Order.hpp:118/273`, `OrderManager.hpp:416`, `OmsFieldRegistry.hpp:337` assert wiring
  that doesn't exist.
- **Orphaned Thompson save fns** (F5) — fully implemented, zero prod callers.
- **Dead telemetry reads** — `Thompson_GetProbabilities` (`ThompsonBandit.hpp:308`) prod-dead (tests only);
  `last_predicted_exit_thompson_arm` (`CoreModelZoo.hpp:981`) init to -1, never written;
  `exp3_probs_telemetry` (`BanditAlgorithmRegistry.hpp:404`) computed-then-`(void)`-discarded.
- **Dead model variants** — `Label_CSPercentileRank` / `_CSZScoreRobust` / `_CSVolScaledDemeaned`
  (`LabelFunctions.hpp:316-347`) are three identical `return future_return` placeholders (v5.16 multi-symbol).
- **Zero-stub feature importances** — `feature_importances` memset(0) at `BacktestEngine.hpp:1888` +
  `BacktestPanels.hpp:3211` ("wire XGBoost importance extraction") — the stability/pruning hooks have no data.
- **Stale comments** — "uniform 5-arg contract" (`BanditAlgorithmRegistry.hpp:282`; it's 6-arg);
  "cfg=2 = BOTH" (`StrategyParameters.hpp:928/959`; renamed at `.F.4d`); `n_rounds=200` constants (F6);
  `FeatureStandardizer.hpp:209/370` "NO CALLERS YET" (now has many).
- **Backtest sim incomplete** — `sample_regimes[]` hardcoded 0 (`BacktestSharded.hpp:515`) → per-regime
  stratified stats impossible (the data is there; wiring missing); WF debug `fprintf(stderr)` bisection
  scaffolding from the v5.11.46 segfault hunt still in the training loop (`BacktestEngine.hpp:1665-1750`).

---

## 5. Architecture improvement suggestions ("a better way to set this up")

1. **A `FOREACH_BANDIT_PERSIST` save-side registry** mirroring the existing `FOREACH_ENSEMBLE_POST_LOAD`
   load registry. The load↔save asymmetry *caused* F5; make save mirror load structurally so "added a load
   step, forgot the save" is a compile error (closes Class 18 at this surface).
2. **One `XGBoost_TrainBooster(features, labels, n, label_kind, hp, &booster)` helper** behind the train
   worker + WF + held-out + multi-horizon. They've each re-implemented DMatrix build + objective + weighting
   + iter loop and **drifted** (n_rounds, weight-cap, hyperparam source, scaler, label_kind test all differ
   — F1/F6/F13/F14). One helper structurally prevents the "validated model ≠ deployed model" class. Matches
   the H15-H19 single-source/registry ethos.
3. **Unify backtest + live execution on one event→submit path** (resolves F3 by construction, and is the
   concrete substrate for the `.E.1` `backtest-paper-live-convergence-discipline`). The backtest currently
   diverges at the drain layer (`EventLoop_DrainEvents` vs `DrainWithSubmit`).
4. **Make the bandit feedback model explicit** — a `BanditFeedbackMode {FULL_INFO_HEDGE, BANDIT_EXP3}` enum
   selecting the update rule (fixes F4, makes the math auditable + A/B-able).
5. **Lift magic reward constants into the registry/cfg** — the `±50 bps` direction-hit + `reward_mult=4.0`
   are hardcoded at the attribution sites (`CoreModelZoo.hpp:1391/1468`), contradicting the "1-row registry"
   design ethos and making reward-shaping un-tunable.
6. **Add probability calibration (Platt/isotonic)** fit on a dedicated calibration fold — there is **none**
   today (grep-confirmed). `binary:logistic` raw scores are used directly vs `ml_buy_threshold` and fed to
   the bandit; calibrated probabilities especially improve the bandit reward signal. Persist as a sidecar
   with the same stamp-binding pattern as the scaler.
7. **Sample-weighting by label uniqueness/overlap** (López de Prado §4) — barrier labels from overlapping
   windows are highly autocorrelated; weight `w_t ∝ 1/avg_uniqueness` via the existing
   `XGDMatrixSetFloatInfo("weight",…)` plumbing. Single highest-leverage statistical fix for the
   "every fold flags as memorization" symptom (`BacktestEngine.hpp:382`).

---

## 6. New algorithm exploration (the "get spicy" track)

The `FOREACH_BANDIT_ALGORITHM` registry makes **adding a bandit algorithm a 1-row change** (enum + dispatch
table + masks + ToString all auto-flow; the `(exp3_up, thompson_up)` metadata auto-extends the reward
dispatch). That makes this a *structured research surface*: each candidate is a registry row + a compute fn,
A/B-able against the existing modes via the calib log. Ordered by **fit × effort** for THIS system
(non-stationary crypto regimes, per-core sharding, determinism-priority, regime signals already computed):

**Tier 1 — highest value, smallest change (directly fixes F17):**
- **Discounted Thompson (ρ-forgetting Gaussian).** `precision_post = ρ·precision_post + precision_obs`,
  ρ∈(0,1) (optionally pull `mu_post` toward prior by `1−ρ`). Caps effective memory at ~`1/(1−ρ)` recent
  rewards → a regime shift re-widens the posterior and re-enables exploration. Reuses `ThompsonBanditState`
  verbatim + one cfg field. **The single best fit for non-stationary regimes.**
- **EXP3.S / fixed-share Exp3.** After each update, mix a share uniformly:
  `w_a ← (1−σ)·w_a + (σ/K)·Σw`. Bounds how stale any arm's weight gets; cures Exp3 ossification. Tiny
  addition to `Bandit_Update`, reuses `BanditState`. Pairs naturally with the F4 Hedge/Exp3 fix.

**Tier 2 — deterministic + theoretically grounded (fits determinism-priority ethos):**
- **Discounted / Sliding-Window UCB (D-UCB / SW-UCB, Garivier–Moulines 2011).** Discounted empirical means +
  counts, `argmax(mean_a + sqrt(c·log Σn / n_a))`. **No RNG** → trivially replay-safe (sidesteps F21 + the
  persisted-RNG concern entirely). The per-arm reward observability you already have makes the discounted
  mean update direct.
- **Rexp3 / periodic-restart Exp3 (Besbes–Gur–Zeevi 2014).** Run Exp3 in epochs of length Δ, reset weights
  each epoch — designed for a "variation budget." Almost free given `total_steps` (reset on
  `total_steps % Δ == 0`). Strong A/B partner against the discounted methods.

**Tier 3 — higher ceiling, more effort (genuinely novel for this engine):**
- **Linear/contextual Thompson (LinUCB) over `RegimeSignals` as context.** Today regime is a hard 5-bucket
  partition (a separate bandit per regime, each cold-starting). A linear-Gaussian posterior over the
  continuous `RegimeSignals` vector (slope, R², variance, book_imbalance, spread_z, flow_*_ewma…) generalizes
  across regime boundaries and exploits structure the bucketing discards. The **Ridge Cholesky-solve
  infrastructure is already in-tree** (`RidgeBlender`) and can be repurposed for the per-arm `d×d` posterior.
  This is the bridge from context-free to contextual bandits, and the regime context is sitting unused.
- **Tsallis-INF / FTRL with ½-Tsallis entropy (Zimmert–Seldin 2019).** Best-of-both-worlds optimal regret in
  *both* stochastic and adversarial regimes simultaneously — exactly the "is the market adversarial or just
  noisy?" ambiguity in HFT. The modern SOTA replacement for Exp3 (Newton step for normalization).
- **Risk-aware / satisficing bandit.** "Highest expected reward" ≠ "best Sharpe." Score arms by
  `mu_a − λ·sigma_a` (both available from the Thompson posterior) or a CVaR objective, or satisfice (pick any
  arm clearing a target, else explore). Reuses `mu_post`/`precision_post`; just changes selection scoring —
  very cheap, high relevance for drawdown-aware trading.

**Cross-cutting "spicy" idea — conformal uncertainty → bandit exploration.** Wrap the model in
split-conformal prediction (nonconformity scores on a calibration fold) to emit calibrated interval widths,
and feed the width as an uncertainty signal so the bandit widens exploration when the model is *genuinely*
uncertain (not merely low-probability). Clean, distribution-free, fits the sidecar+stamp pattern, and ties
the ML calibration gap (§ 5.6) to the bandit. A novel combination worth prototyping.

**Backtest-rigor "spicy" track** (for trustworthy go-live numbers): Deflated Sharpe Ratio + Probability of
Backtest Overfitting (PBO) on sweeps (F15); Combinatorial Purged CV (CPCV) for an OOS *distribution*;
Monte-Carlo permutation / block-bootstrap significance tests; regime-stratified evaluation (wire
`sample_regimes[]`, § 4). These convert single-number stats into intervals + p-values.

---

## 7. Recommended slotting into the `.E` sub-sprint

These findings are **not** in the `.E.1–.E.8` infra scope (Core→Node rename, headless, io_uring,
sub-accounts, exchanges). But they are **live-readiness-critical** because they gate the validity of the
backtest→paper→live evaluation that the whole sprint exists to make safe. Recommendation:

1. **File this as the 5th codebase-wide audit in `.E.0` Phase A** (alongside anti-spaghetti / bug-check /
   registry-fit / test-strength). It's already in the right directory + schema. Carry the F1–F22 table into
   `.E.0` Phase E operator triage (FIX-NOW / ACCEPT / DEFER) per
   `feedback_proportionate_response_to_audit_findings`.

2. **Triage proposal (operator decides):**
   - **FIX-BEFORE-PAPER-TEST (precursor to the paper-test milestone, NOT blocked behind the big `.E.1`
     rename):** F1 (standardization skew), F2 (slippage), F3 (confirm the runtime check first), F6 + F7
     (eval validity). These four determine whether paper-test numbers mean anything. They're small, targeted
     fixes (not infra) and naturally form **one audit-gated ML-correctness ship** — suggest naming it in the
     `.F` ML/framework lineage (e.g. a `.F.4g` "ML train/serve + backtest-execution parity" ship, sister to
     the existing `.F.4f` cleanup) OR a tightly-scoped `.E.0` FIX-NOW batch if the operator prefers to keep
     it inside the audit ship.
   - **FIX-WITH-`.E.1`:** F3's structural close (unify backtest+live execution path) is the concrete
     substrate for the `backtest-paper-live-convergence-discipline` DESIGN_SPEC already scheduled at `.E.1`
     — fold the execution-path unification into that work.
   - **NEXT ML SHIP (post-paper-test, proportionate):** F4 + F5 + F8 + F9 (bandit reward correctness +
     persistence), F10/F11 (telemetry wiring — close the `.F.4d` Step 7 drift), F12–F16 (training rigor),
     plus the § 5 structural refactors (`FOREACH_BANDIT_PERSIST`, `XGBoost_TrainBooster`).
   - **RESEARCH TRACK (operator-driven, decoupled):** § 6 new algorithms. Tier-1 (discounted Thompson,
     EXP3.S) are 1-row registry adds and the cleanest first experiments; they *also* resolve the F17 design
     limitation. Recommend a standalone exploratory branch, A/B'd via the calib log.

3. **Audit gating for the remediation ship(s):** per the codebase's discipline, the FIX-BEFORE-PAPER-TEST
   batch touches the train/serve parity surface (heavily audited) → fire `/precoding-audit-gate` +
   `/parity-check` + `/ml-audit` before coding, and `/test-strength-audit` after (F13 shows a test gap: no
   test drives a gate→event→submit→fill round-trip through the backtest driver, which is why F3 went
   unnoticed).

4. **Forward-promise note:** the `.E.1` cross-ship invariant table already lists "Backtest → paper → live
   discipline" and a planned `backtest-paper-live-convergence-discipline.md` spec. F2 + F3 are direct inputs
   — cross-reference this audit there so the discipline is written against real findings, not in the abstract.

---

## 8. Cross-references

- Engine HEAD: `61ae3cc` (v5.15.5.F.4d.1.D)
- Bandit design intent: `subplans/2026-05-16-v5.15.5.F.4d-merged-framework-bandit-thompson.md`
- Paper-test milestone (gated by F1/F2/F3/F6/F7): `ROADMAP-2026-05-17-to-paper-test.md`
- `.E.0` plan body: `subplans/2026-05-28-v5.15.5.F.4d.1.E.0-precoding-plan-audit-verification.md`
- Sister codebase-wide audits: `E.0-audit-reports/codebase-wide-{anti-spaghetti,bug-check,registry-fit-audit,test-strength-audit}.md`
- Bandit core: `ML_Headers/{BanditLearning,ThompsonBandit,BanditAlgorithmRegistry,bandit_dispatch_table,RewardTracker}.hpp`
- Reward wiring: `ML_Headers/CoreModelZoo.hpp`, `CoreFrameworks/{OrderManager,ControllerEventLoop,Order}.hpp`, `MemHeaders/OmsFieldRegistry.hpp`
- ML train/eval: `Backtest/{BacktestSharded,BacktestEngine,BacktestPanels,HeldOutSplit,ValidationSplit,LabelFunctions,CostModel}.hpp`, `ML_Headers/{FeatureStandardizer,FeatureRegistry,ModelInference}.hpp`

---

**End of codebase-wide ML + bandit correctness audit** (2026-05-28). Read-only scan; no engine code or
existing plan modified. 22 findings (1 CRITICAL verified + 1 CRITICAL-tempered-to-HIGH + 1 HIGH-suspected +
4 HIGH + 11 MED + 4 LOW), drift inventory, 7 architecture improvements, 11 new-algorithm candidates, and an
`.E`-phase slotting recommendation.
