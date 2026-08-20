# Bandit/Thompson Learning-Loop End-to-End Map — i-class report (2026-08-20)

> Saved verbatim at receipt 2026-08-20 (orchestrator write per `feedback_save_agent_reports_verbatim`).
> ⚠️ HEADLINE: contains the FAN-SHIFT defect (H-1) — independently confirmed by the backtest-exercisability agent's Defect 2. Compiled-probe-proven.

**Repo:** `/home/caramel/code/FoxML_Trader_v2` @ HEAD `417e524`, branch `feat/v5.15-live-readiness`.
**Roots covered by every membership claim:** `CoreFrameworks/ Strategies/ ML_Headers/ MemHeaders/ DataStream/ FixedPoint/ Backtest/ GUI/ tests/ tools/` (named explicitly per Landmine 19; empty probes carried positive controls).
**Method:** CODE_MAP + uncapped greps + direct reads; the one high-stakes claim (H-1 below) is **proven by compiled probe**, not eyeball. Decision-log claims (D-422/D-423/C-424 STATUS) were re-verified against code; two of them are contradicted below.

---

## HEADLINE FINDING (H-1) — the exit-bandit reward UPDATE is DEAD on every production path, and D-423's "update half works" premise is false at HEAD

The single production route into the exit attribution code is:

- LIVE drainer: `CoreFrameworks/EngineSharded/Run.hpp:1588` + `:1627` → `EngineSharded_SlowPath_DrainPostFill` (`CoreFrameworks/EngineSharded/SlowPath.hpp:67-79`, flag passed at `:78`) → wrapper `EventLoop_DrainPostFill` (`CoreFrameworks/ControllerEventLoop.hpp:2056-2079`) → `EventLoop_DrainPostFillOneCore` (`:1627-1654`).
- BACKTEST: `CoreFrameworks/ShardedBacktestDriver.hpp:285-287` + `:485-487` → same wrapper.
- OneCore has exactly ONE production caller: the wrapper's fan at `:2073-2078` (enumerated; everything else is tests).

**The defect:** the fan-out at `ControllerEventLoop.hpp:2073-2078` passes **10 positional args** into OneCore's **12-parameter** signature. `f973b5c` (v5.14.1.F) inserted `confidence_ic_variant = 0` at **position 9** of OneCore (`:1644`) — *between* `drift_auto_kill` and `exit_bandit_enabled` — and never touched the fan-out (its region history ends at `0fa29fe`, v5.13.4.B, the commit that added the exit params correctly *at the time*). Since then every arg after position 8 binds one slot early:

| fan-out arg (`:2077-2078`) | binds to OneCore param | effect |
|---|---|---|
| `exit_bandit_enabled` (the cfg flag) | `confidence_ic_variant` (`:1644`) | cfg exit flag silently selects the drift-IC variant |
| `fee_rate_taker_for_cf` (double `0.001`) | `int exit_bandit_enabled` (`:1649`) | **truncates to 0 — exit attribution gate `:1985` is compile-time-guaranteed false** |
| — (default) | `fee_rate_taker_for_cf = 0.001` (`:1650`) | counterfactual fee always 0.001, never cfg |
| — (default) | `node_cfg = nullptr` (`:1654`) | per-core `bandit_algorithm` dispatch dead at the drainer (see H-2) |

**Proof (compiled, with positive control):** `g++ -std=c++17 -fsyntax-only -Wfloat-conversion` on a TU explicitly instantiating `EventLoop_DrainPostFill<64>` emits `ControllerEventLoop.hpp:2078:42: warning: conversion from 'double' to 'int'` — the fee argument binding into the `int exit_bandit_enabled` parameter — plus the control warning at the probe's own deliberate double→int line. Probe left at the session scratchpad (`argprobe.cpp`/`argprobe.out`).

**Second-order live hazard:** with `exit_bandit_enabled=1` in live cfg, OneCore's `confidence_ic_variant` becomes 1; `FOREACH_IC_VARIANT` has ONLY variant 0 (`ML_Headers/ICVariantRegistry.hpp:56-60`, pearson commented out) and the dispatcher returns **0.0 for out-of-range variants** (`ML_Headers/ConfidenceScore.hpp:887-896`). The drift detector at `ControllerEventLoop.hpp:1889-1897` then pushes constant 0.0 IC → with `drift_floor > 0` that is a **guaranteed sustained breach**, and with `auto_kill_on_drift=1` a **spurious per-node auto-kill** (`:1916-1926`). So the flag the operator would flip to enable exit learning instead poisons a capital safety control. (At today's defaults — flag 0, floor 0 — it is inert.)

**Why every green stayed green:** test C.3c (`tests/controller_test.cpp:26549-26622`) drives `g_exit_reward_dispatch<F>[algo]` and `BanditAlgorithm_Apply` **directly** — the leaf halves — exactly bypassing the wrapper seam where the binding breaks. All conversions are legal C++; nothing warns at default flags. This is `feedback_passing_test_is_not_verification` in its purest form, and it means **D-423's core narrative ("exit pool received reward on every qualifying fill; select was the missing half") was already false when written** — reward had been unreachable through production since v5.14.1.F. The loop was not write-only; it was *neither*-half-live.

**H-2 (same mechanism, buy side):** `node_cfg = nullptr` through the wrapper means `EnsembleModelZoo_TradeCloseReward` (`ControllerEventLoop.hpp:1958-1960`) always resolves `algo = EXP3` (`ML_Headers/NodeModelZoo.hpp:1757`) — **buy-side Thompson never receives trade-close rewards in production**. The `.F.4d` comments claiming "Production callers pass node_cfg" (`NodeModelZoo.hpp:1639-1640`, `:1724-1725`) are false for this path. Thompson's only live reward source is the slow-path lookback, where `node_cfg` IS passed (`Strategies/StrategyParameters.hpp:1389-1395`).

**H-3 (false comment):** `SlowPath.hpp:92-97` claims the `fee_rate_taker_for_cf` param chain was "DELETED from EventLoop_DrainPostFill / DrainPostFillOneCore signatures" — both params exist at `:2071`/`:1650` and the exit counterfactual consumes one at `:2014`. Point-in-time comment drift on the exact surface it describes.

---

## Q1 — The exit-bandit loop TODAY

**SELECT** — `Strategies/StrategyParameters.hpp:1497-1511`:
- Outer exit-model block gate (`:1425-1429`): `MASK_ML_CFG_USE_EXIT_MODEL` set AND `ezoo_ex->exit_predictor_count > 0` AND `mctx->out_exit_prediction` wired.
- Bandit gate (`:1498-1500`): `MASK_ML_CFG_EXIT_BANDIT_ENABLED` AND `MASK_EZOO_EXIT_BANDITS_READY` AND `exit_predictor_count >= 2`. Dispatch via `BanditAlgorithm_Apply(node_cfg->bandit_algorithm, &exit_bandits[regime], exit_thompson_bandits[regime] if MASK_EZOO_EXIT_THOMPSON_READY, …, thompson_exp3_blend_alpha)` (`:1503-1511`).
- `dominant` re-point (`:1530-1537`): Thompson's explicit `chosen_arm`, else argmax of learned weights — scoped inside the bandit branch.
- Ridge override AFTER bandit (`:1541-1588`): gate = `gate_state MASK_EXIT_BLENDER_ACTIVE` else `MASK_ML_CFG_EXIT_BLENDER_MODE`, + `exit_predictor_count >= 2`; overwrites `weights` when ≥2 samples of history.
- Blend + publish (`:1590-1596`) → `*out_exit_prediction`, `*out_exit_dominant_horizon`, wired per-cycle at `ControllerEventLoop.hpp:3030-3033` (reset `-1`/`0.0` first).

**FIRE (SELECT→UPDATE seam)** — `CoreFrameworks/EngineCommon.hpp:668-753`: gates `MASK_ML_CFG_USE_EXIT_MODEL` + `last_exit_prediction > cfg.nodes[c].exit_threshold` (per-node; `:668-670`) + `price_d > 0.01` + open positions. Captures `captured_arm = last_exit_dominant_horizon` (`:706-707`) + regime (`:708-709`), bounds-checks, packs `OMS_META_PACK(arm, regime)` into `oms.last_exit_predicted_meta[pidx]` (`:738-743`), sets `last_exit_predicted_bitmap` (`:694`), submits SELL (`:746-748`), sets `SHALT_EXIT_PREDICTED` (`:750-751`).

**UPDATE** — `CoreFrameworks/ControllerEventLoop.hpp:1985-2036` (exact site the mission asked for): gates (1) the `exit_bandit_enabled` **function parameter** (`:1985` — dead per H-1), (2) per-slot predicted bit (`:1987`), (3) `flatten_pending == 0` (`:1988`), (4) `MASK_EZOO_EXIT_BANDITS_READY` + `OMS_META_IS_VALID` + arm/regime bounds (`:1998-2001`), (5) `entry>0 && orig_tp>entry` (`:2011`). Reward = `actual_pnl_bps − (tp_pct − 2·fee)·10⁴` (advantage vs hold-to-TP; `:2012-2019`), dispatched `g_exit_reward_dispatch<F>[exit_algo](ezoo, regime, chosen_arm, reward_bps)` (`:2031-2033`; table at `ML_Headers/bandit_dispatch_table.hpp:254+`). Per-slot state cleared after (`:2047-2049`).

**PERSIST** — shutdown: `Run.hpp:2336-2343` (`exit_bandit_state.json`), plus `:2326` (buy), `:2357` (buy Thompson), `:2365` (exit Thompson); outer gate `MASK_EZOO_ACTIVE + MASK_EZOO_BANDITS_READY + cfg.node_model_dir[i][0]` (`:2324-2325`). Periodic: `NodeModelZoo.hpp:3268-3318` — all four pools (`:3283`, `:3313-3315`); base_dir derived by truncating `bandit_save_path` at its last `/` (`:3306-3312`), which is an invariant of `LoadBanditState`'s construction at `:2692-2694`. STATUS-block line cites (3312/3304-3315) drifted by ~2 lines but the substance is confirmed. Note: the periodic counter is bumped **only by buy-side updates** (`:1705`, `:1775`) — exit-side rewards never advance it.

**RELOAD** — `FOREACH_ENSEMBLE_POST_LOAD` rows `load_exit_bandit` (`NodeModelZoo.hpp:3395-3396`) + `load_exit_thompson_state` (`:3416-3417`), inside `EnsembleModelZoo_PostLoadSetup` (`:3433-3441`), called from the shared boot helper `EngineCommon.hpp:380-381` with `base_run_path = cfg.node_model_dir[c]` (also hot-swap `EnsembleHotSwap.hpp:99`, `HotSwap.hpp:148`). Loader guards: `EXIT_BANDITS_READY` + `exit_predictor_count >= 2` + bundle-id match (`:2718-2728`).

**Gate flags + cfg defaults (exit loop):**

| Gate | Where defined | Default | cfg key |
|---|---|---|---|
| `MASK_ML_CFG_USE_EXIT_MODEL` | `ML_Headers/MlCfgFlagRegistry.hpp:69` | **0** (`ControllerConfig.hpp:2014`) | `use_exit_model` |
| `MASK_ML_CFG_EXIT_BANDIT_ENABLED` | `MlCfgFlagRegistry.hpp:68` | **0** (`:2013`) | `exit_bandit_enabled` |
| `MASK_EZOO_EXIT_BANDITS_READY` | `EzooInitFlagRegistry.hpp:104` (0x04) | set/cleared by `InitExitBandits` (`NodeModelZoo.hpp:1867/1874/1892`) | — (derived) |
| `MASK_EZOO_EXIT_THOMPSON_READY` | set at `NodeModelZoo.hpp:1995` | — | — (derived) |
| `exit_predictor_count >= 2` | `StrategyParameters.hpp:1500` | 0 today (no artifacts) | — (derived from `<dir>/exit.json`) |
| `exit_threshold` | `CfgFieldRegistry.hpp:787` | 0.6, per-node | `exit_threshold` |
| `exit_bandit_lr` (→ Exp3 eta_max) | `ControllerConfig.hpp:1294/2193` | 0.1 | `exit_bandit_lr` |
| `bandit_algorithm` | `CfgFieldRegistry.hpp:744` | 0 = EXP3 (0..4) | `bandit_algorithm` |

**What breaks the loop TODAY — three independent breaks, in order of encounter:**
1. **No exit models exist.** The loader wants `<base>_horizon_<H>/exit.{json,xgb,txt}` (`NodeModelZoo.hpp:2148-2155`; filename from role at `:233-248`). Uncapped `find models/ data/ -iname "*exit*"` → **zero hits**, positive control (barrier.json across many horizon dirs) present. So `exit_predictor_count == 0` → `EXIT_BANDITS_READY` cleared (`:1867`) → SELECT, UPDATE, persist, reload all no-op. Mission's hypothesis **confirmed**.
2. Even with models: **the UPDATE is unreachable** (H-1) — since v5.14.1.F, live and backtest both.
3. Even with H-1 fixed: defaults `use_exit_model=0`, `exit_bandit_enabled=0` (operator opt-in required); `engine.cfg` at HEAD contains **no** ML/bandit keys at all (positive-controlled grep; 304 lines).

---

## Q2 — The BUY-side bandit/Thompson

**SELECT** — `StrategyParameters.hpp:1145-1215`. Gate (`:1145-1147`): `blend_mode == "weighted"` (documented default; `:1083`) AND `MASK_EZOO_BANDITS_READY` AND `MASK_ML_CFG_BANDIT_ENABLED` (default **1** since `5d45ecc`; `ControllerConfig.hpp:2004-2012` — verified, and note **`backtest.cfg:456` explicitly sets `bandit_enabled=0`**) AND `primary_count >= 2`.
- `bandit_algorithm==0`: Exp3 probabilities with regime-transition hysteresis blend (`:1165-1186`).
- else: `BanditAlgorithm_Apply` over `bandits[regime]` + `buy_thompson_bandits[regime]` when `MASK_EZOO_BUY_THOMPSON_READY`, `thompson_exp3_blend_alpha` (`:1199-1206`); chosen arm telemetry `last_predicted_buy_thompson_arm` (`:1209-1211`).

**Ridge fork + precedence (both sides):** bandit writes weights first; Ridge **overwrites** when its gate passes — buy: `gate_state (MASK_RIDGE_WITHIN_ACTIVE && !MASK_THOMPSON_ACTIVE)` else `MASK_ML_CFG_RIDGE_WITHIN_HORIZON && bandit_algorithm==0` (`:1240-1247`, Ridge is Exp3-mutually-exclusive with Thompson); exit: `MASK_EXIT_BLENDER_ACTIVE` / `MASK_ML_CFG_EXIT_BLENDER_MODE` (`:1541-1545` — key `exit_blender_mode`, default 0, `MlCfgFlagRegistry.hpp:74`). Order on both sides: **uniform → bandit → Ridge wins**. With <2 history samples Ridge silently leaves bandit weights (`:1293-1294`, `:1587`). Exit-side Ridge IC inputs are hardcoded 0.0 (`:1567-1575` — "ic_avg_exit[] when available" never built).

**UPDATE (two paths, both full-information — every arm updated per record, not the chosen arm):**
1. Per-tick lookback: `EnsembleModelZoo_TickRewardsFromLookback` (`NodeModelZoo.hpp:1643-1707`) — matured ring records; per-arm reward **±50 bps by direction-correctness** (`:1687-1689`); dispatch `g_buy_reward_dispatch<F>[algo]` (`:1695`); called from the SELECT block WITH `node_cfg` (`StrategyParameters.hpp:1389-1395`) → Thompson genuinely updates here when algo≠0.
2. Trade-close: `EnsembleModelZoo_TradeCloseReward` (`:1727-1776`) — most recent un-rewarded record; **sign-of-PnL only × ±50 × `ensemble_trade_reward_mult`** (`:1753`, `:1764-1766`); the `pnl_bps = exit_net_pnl/balance` computed at `ControllerEventLoop.hpp:1950-1953` is thresholded to its sign at the leaf. **D-423's "buy = exit_net_pnl/balance in bps" describes the argument, not what reaches `Bandit_Update`** — a decision-log inaccuracy worth recording. Gated only on `EZOO_ACTIVE + BANDITS_READY` (`:1949`) — **no** `BANDIT_ENABLED` gate = the intentional "shadow learning" (`StrategyParameters.hpp:1137-1144`). Via the wrapper, `node_cfg`=nullptr → EXP3-only (H-2).

`Bandit_Update` is Exp3-IX: importance-weighted `r̂ = reward/p_arm`, adaptive `eta = min(eta_max, sqrt(ln K/(K·T)))`, `w *= exp(eta·r̂)`, 1e-10 floor + 1e6 renorm (`ML_Headers/BanditLearning.hpp:385-425`). Magnitude matters — the exit side's advantage-bps carries information; the buy side's is fixed-magnitude.

**PERSIST/RELOAD:** same 4-file cohort — `bandit_state.json` (`:2647`), `buy_thompson_state.json` (save `:2783`; load falls back to legacy `thompson_state.json`, `:2955-2960`); shutdown `Run.hpp:2326/2357`; periodic `:3283/3314`; reload rows `load_bandit_state`/`load_thompson_state` (`NodeModelZoo.hpp:3391-3392/3405-3406`). Thompson state carries posterior + per-regime RNG (`%016lx`), `format_version=1`, `n_arms` match gate (`:2940-2990`). Thompson defaults: `thompson_rng_seed=42`, `mu_prior=0.0`, `precision_prior=1.0`, `precision_obs=1.0`, `thompson_exp3_blend_alpha=0.5` (`CfgFieldRegistry.hpp:698-748`). Buy knobs: `ensemble_bandit_eta=0.1` (`ControllerConfig.hpp:2183`), `ensemble_min_warmup_predictions=100` (`:2184`), `ensemble_trade_reward_mult=4.0` (`:2195`), `ensemble_bandit_save_interval=5000` min **1** (`CfgFieldRegistry.hpp:695` — 0-disable unreachable via cfg clamp).

---

## Q3 — Backtest-side Thompson save gap (and load behavior)

**What exists:** `BacktestSharded_Run` completion seam saves **only buy Exp3** — `Backtest/BacktestSharded.hpp:891-904` (`SaveBanditState`, gated ACTIVE+BANDITS_READY+`node_model_dir[i][0]`).
**What's missing:** `SaveExitBanditState` / `SaveThompsonState` / `SaveExitThompsonState` — zero `Backtest/` callers (persist grep, uncapped). **The insertion point is exactly inside that `:891-904` loop**, mirroring `Run.hpp:2334-2372` (same guards; the three savers self-guard on their READY bits + `count>=2`, so it's three added calls, no new conditions).
**Partial mitigation that muddies A/B design:** the periodic saver CAN fire mid-backtest (buy-side updates run in the backtest slow path; `bandit_save_path` is set by `LoadBanditState` during PostLoadSetup) and it writes **all four** files — so exit/Thompson state escapes a backtest only at 5000-update boundaries, then the tail since the last boundary is dropped.

**Does the backtest LOAD bandit state? YES, twice:**
1. Default: the shared `EngineCommon_BootPerCore` (`BacktestSharded.hpp:306-308`) runs `EnsembleModelZoo_PostLoadSetup` (`EngineCommon.hpp:380-381`) = **all four loads from `cfg.node_model_dir[c]`** — i.e., a backtest silently inherits any `bandit_state.json` a previous live session or backtest left in the model dir. Zoos are `static` but Free+Init'd per run (`:260-299`), so cross-run carry is **disk-only**.
2. Operator override: `run_cfg->bandit_state_prior_path` → `LoadBanditStateFromPath(..., skip_bundle_check=1)` (`BacktestSharded.hpp:315-320`; buy Exp3 only). Field `BacktestEngine.hpp:250`; **no cfg-file key parses it and no GUI writer exists — only tests write it** (uncapped grep; writers at `tests/controller_test.cpp:16425`). Advertised transfer-learning, operator-unreachable.

**PARITY note:** the mission's pointer "PARITY-031" actually names the regime N→1 collapse (`DOCS/PARITY_ISSUES.md:1316-1323`), not bandit priors. The closed exit-bandit backtest gap is PARITY-010 (`:590-633`). The "backtest inherits live-learned bandit state by default" surface appears **un-numbered** in the ledger — a fresh parity finding to home.

**Backtest exit-UPDATE is dead twice over:** the driver passes only 4 args (`ShardedBacktestDriver.hpp:285-287`, `:485-487` — `exit_bandit_enabled` default 0, `node_cfg` never), and H-1 would zero it anyway. `backtest.cfg`'s `exit_bandit_enabled` (if set) is **never read by the backtest drain path**.

---

## Q4 — The empirical "exit_bandit_enabled=1 vs uniform" backtest: what a run needs

**Blocking pre-work (in dependency order):** (1) H-1 wrapper fix; (2) driver must forward `exit_bandit_enabled` + per-node `node_cfg` + real fee (design decision: the wrapper takes ONE scalar; per-node cfg wants `cfg.nodes[c]` inside the fan loop); (3) train ≥2 exit-role models; (4) add the 3 completion savers (else the learned state evaporates at run end).

**Model artifacts:** ≥2 horizon sibling dirs `<node_model_dir>_horizon_<H>/exit.json` with stamps passing the horizon/scaler checks (`NodeModelZoo.hpp:2148-2155`). The suite CAN produce them: training requests carry `req_role[16]` accepting `"exit"` (`Backtest/BacktestEngine.hpp:1233`; role plumbed at `BacktestPanels.hpp:4357-4360`; expected.cfg documents the role at `:6323`). There is no exit-specific label — an exit model trains on an existing `FOREACH_TARGET` row (`Backtest/LabelFunctions.hpp:83-96`; `will_peak` is the natural sell-timing target).

**Exact cfg keys (the run matrix):** `core_N_strategy=ml`→**`node_N_strategy=ml`**, `node_N_model_dir=<base>` (ensemble REQUIRES a dir — `EngineCommon.hpp:364`), `ensemble_blend_mode=weighted`, `use_exit_model=1`, `exit_bandit_enabled=1|0` (the A/B axis), `exit_threshold` (default 0.6 — likely needs lowering to get fires), `exit_bandit_lr`, `bandit_algorithm` (0=Exp3 / 1=Thompson), `exit_blender_mode=0` (MUST stay 0 in both arms or Ridge overwrites the bandit and the A/B measures Ridge), `bandit_enabled` (**backtest.cfg:456 currently pins 0** — set explicitly per arm to control the buy side), `ensemble_bandit_save_interval`, `thompson_rng_seed` (=42 default; deterministic replay). Spelling: each flag is its **own key** (the registry `legacy_field` column), packed into `cfg.ml_cfg_flags` by the cohort walker (`ControllerConfig.hpp:208`); there is no literal `ml_cfg_flags=` key in cfg files.

**State carry:** fresh-vs-transfer is controlled by the model dir's JSON files — **delete `*bandit*/*thompson*` state files between runs for a fresh arm; leave them (or use `bandit_state_prior_path` once it's reachable) for transfer**. Today's default is *accidental transfer* of whatever is on disk.

**Metrics out:** `BacktestStats` — `total_pnl`, wins/losses, `profit_factor`, `all_wins_run`, `expectancy`, `max_drawdown(_pct)`, `return_pct` (`BacktestSharded.hpp:855-868`), equity curve per closed trade (`:781-787`). **No per-arm bandit metric CSV exists in backtest output** — the learning evidence is the saved JSON (weights/pulls/cum_reward per regime) + stderr load/save lines. The calibration log (per-arm probs) is LIVE-only (`Run.hpp:759-762`; path default empty `ControllerConfig.hpp:2301`).

**A null result is currently guaranteed:** with the UPDATE dead, `exit_bandit_enabled=1`+Exp3 selects from never-updated uniform weights → byte-identical blend to baseline (only the attribution metadata `dominant` changes, `StrategyParameters.hpp:1530-1537`); with Thompson it changes behavior via one-hot posterior *sampling* but never learns. The A/B is meaningless until H-1 + the driver forwarding land.

---

## Q5 — Observability for a live/paper confirmation

**Published today (buy side only):** per-regime Exp3 probability matrix `ensemble_weights[5][8]` + `ensemble_n_updates_per_regime` (`ShardedSnapshot.hpp:790-808`, guarded READY+`primary_count>=2`), Thompson posterior μ/precision/pulls + packed chosen-arm/active byte when `bandit_algorithm!=0` (`:815-824+`); rendered as the ML Status heatmap (`GUI/MLStatusPanel.hpp:356-451`) and the Thompson Bayesian dashboard (`:604-681`). PerNodeSnap bandit telemetry cluster: `DataStream/EngineTUI.hpp:1338-1370`.
**Exit side:** ONLY `ml_last_exit_prediction` + `ml_last_exit_dominant_horizon` (`ShardedSnapshot.hpp:604-605` → `MLStatusPanel.hpp:193-196`). **No exit-bandit weights, pulls, or posteriors are published anywhere** — the operator cannot watch exit learning from the GUI at all; the only evidence is the saved `exit_bandit_state.json` and shutdown-save stderr lines (`Run.hpp:2340-2343`).
**What the operator would WATCH (buy):** heatmap rows departing uniform per regime; `n_updates` counters climbing; Thompson μ separating across arms; boot line `[ensemble] loaded bandit state from …` proving reload; `SHALT_EXIT_PREDICTED` in the halt-reason surface for exit fires.
**Legacy block:** `TUISnapshot.bandit_*[5]` (`EngineTUI.hpp:738-750`) belongs to the dead single-core per-strategy Exp3 (subsystem L) — ignore it for sharded confirmation.

**`MBS_OrderSetBanditContext` (queued item, verified):** defined `CoreFrameworks/Order.hpp:394` (packs bandit active-state/regime/chosen-arm into `Order::flags_packed` bits 17-25, decision-time-bound so the calib row logs the context the order was *submitted* under). **Sole caller anywhere: `tests/controller_test.cpp:26885`.** Getters read in production at `OrderManager.hpp:838-840` inside `real_on_exit_calibration` (`:816-865`), where `bandit_regime` selects **which regime's per-arm Exp3 probabilities go into the calibration row** (`:860-862`). Missing setter ⇒ every row logs regime-0 probabilities, arm 0, inactive — exactly C-424's finding, re-confirmed. The natural producer sites are the two submit seams where the context is in hand: exit fire (`EngineCommon.hpp:706-748`) and the buy entry submit (with `last_predicted_regime_id` + chosen arm). **Adjacent, worse:** `oms->bandit_reward_bps[pslot]` read into the calib row (`OrderManager.hpp:844`) has **ZERO writers** (uncapped grep, positive control: `last_exit_fee[pslot] =` at `:1539` exists) — the `:842-843` comment "written at HandleFill SELL" is **false**. Two of the calib log's bandit columns are permanently zero.

---

## Q6 — Advertised-capability gaps still open (the `advertised-capability-never-exercised` lens)

1. **Exit reward UPDATE chain dead via arg cross-wire** (H-1) — flag gates a block that can't run; flipping it live poisons drift-IC instead. `ControllerEventLoop.hpp:2073-2078`.
2. **Buy Thompson trade-close rewards dead** (H-2, `node_cfg` nullptr) — comments advertise per-core dispatch that never happens on the drainer path.
3. **Backtest final-flush asymmetry** — 3 of 4 pools save-less at completion (`BacktestSharded.hpp:891-904`).
4. **`bandit_state_prior_path`** — no cfg key, no GUI writer; transfer-learning advertised, test-only reachable (`BacktestEngine.hpp:250`).
5. **`MBS_OrderSetBanditContext`** — getter read in production, setter never called (`Order.hpp:394` / `OrderManager.hpp:838-840`).
6. **`bandit_reward_bps[]`** — registry-enrolled (`OmsFieldRegistry.hpp:401`), logged, never written; false producer comment (`OrderManager.hpp:842-844`).
7. **`exit_bandit_display` / ensemble `bandit_display` arm names** — written at init (`NodeModelZoo.hpp:1841/1889`), zero readers (only the legacy `ctrl->bandit_display_meta` is consumed, `EngineTUI.hpp:801-802`).
8. **`MASK_BANDIT_SHADOW_LEARNING`** — zero production readers (tests only); already flagged as express-or-tombstone at `StrategyParameters.hpp:1141-1144`.
9. **`bandit_blend_ratio`** — on the sharded path: GUI/stamp/drift-row only; `InitBandits` hardcodes `blend_ratio=1.0` (`NodeModelZoo.hpp:1834`); the only behavioral consumer is the dead legacy path (`PortfolioController.hpp:493`).
10. **Exit Ridge IC hardcoded 0.0** (`StrategyParameters.hpp:1567-1575`) — "ic_avg_exit when available" never built.
11. **Exit-bandit observability absent** — a learning system whose learning is invisible (Q5).
12. **False comments on this exact surface** (Class 58 A′ fuel): `SlowPath.hpp:92-97` (H-3), `OrderManager.hpp:842-843` (#6), `NodeModelZoo.hpp:1639-1640/1724-1725` (#2).
13. **`ensemble_bandit_save_interval` min-clamp 1** — the documented `interval=0 disables` state is unreachable through cfg (`CfgFieldRegistry.hpp:695` vs `NodeModelZoo.hpp:3247`).

---

## Loop diagram (as-built, with break points)

```
                          ┌──────────────── BOOT (LIVE + BACKTEST + HOT-SWAP, shared) ────────────────┐
                          │ EngineCommon_BootPerCore → AutoDetectFromDir(node_model_dir)              │
                          │   role files: barrier/regime/exit/buy_signal .json per _horizon_<H>       │
                          │ PostLoadSetup = FOREACH_ENSEMBLE_POST_LOAD (NodeModelZoo.hpp:3380-3417)   │
                          │   Init{Bandits,ExitBandits,BuyThompson,ExitThompson} → *_READY bits       │
                          │   Load{BanditState,ExitBanditState,ThompsonState,ExitThompsonState}       │
                          │   ✗ BREAK-0: no exit.json anywhere → exit_predictor_count=0 → exit READY=0│
                          └──────────────────────────────────────────────────────────────────────────┘
                                                        │
       BUY SIDE (per slow-path rebuild)                 │                EXIT SIDE (per slow-path rebuild)
  SELECT StrategyParameters.hpp:1145-1215               │           SELECT StrategyParameters.hpp:1497-1511
  gate: weighted+BANDITS_READY+BANDIT_ENABLED(=1)+n≥2   │           gate: USE_EXIT_MODEL(=0)+EXIT_BANDIT_ENABLED(=0)
  Exp3 hysteresis | BanditAlgorithm_Apply(+Thompson)    │                 +EXIT_BANDITS_READY+n≥2
  → Ridge override (ridge_within_horizon, Exp3-only)    │           BanditAlgorithm_Apply → dominant re-point
  → weights_buf → Model_Predict_Ensemble_Weighted       │           → Ridge override (exit_blender_mode)
  → RecordPrediction (reward ring)                      │           → blended prob → out_exit_prediction/dominant
  → TickRewardsFromLookback (±50bps all arms,           │                       │
    node_cfg REAL → Thompson updates)  ←──── UPDATE-A   │           FIRE EngineCommon.hpp:668-753
                                                        │           pred > exit_threshold → SELL submit
  UPDATE-B (trade close): drainer                       │           + OMS_META_PACK(arm,regime) per slot
   Run.hpp:1588/1627 → SlowPath.hpp:72-78               │                       │
   → EventLoop_DrainPostFill :2056 ── fan :2073-2078 ───┼──────────→ fill → DrainPostFillOneCore
   ✗ BREAK-1 (H-1): 10 args → 12 params                 │            exit attribution :1985-2036
     exit_bandit_enabled → confidence_ic_variant        │            ✗ gate reads param == (int)0.001 == 0
     0.001 → exit_bandit_enabled (=0)   node_cfg=null   │            (dead since v5.14.1.F f973b5c)
   → TradeCloseReward (algo forced EXP3)                │            else: reward = actual − holdToTP
                                                        │            → g_exit_reward_dispatch[algo]
                          ┌──────────────── PERSIST ────────────────────────────────────────────────┐
                          │ periodic (buy-update-count only): MaybeSaveBanditPeriodic :3268-3318 →   │
                          │   all 4 JSONs      shutdown LIVE: Run.hpp:2321-2374 → all 4 JSONs        │
                          │   ✗ BREAK-2: backtest completion saves buy Exp3 ONLY (:891-904)          │
                          └──────────────── RELOAD: PostLoadSetup next boot (closes the circle) ─────┘
```

---

## What the verification program must run to call this CONFIRMED

**Stage 0 — repair the seam (nothing downstream is measurable until these):**
1. Fix the fan-out binding (`ControllerEventLoop.hpp:2073-2078`) to pass `confidence_ic_variant`, `exit_bandit_enabled`, `fee_rate_taker_for_cf`, and per-node `cfg.nodes[c]` explicitly. **Structural close, not a patch** (M7 — this is the second defaulted-tail silent-re-map on one signature family): de-default the tail params or move to a params-struct so the next mid-signature insertion is a compile error; add `-Werror=float-conversion` (or a targeted CI probe like mine) to pin the class.
2. Forward the flag + node_cfg + real fee through `ShardedBacktestDriver.hpp:285/:485`.
3. Add the 3 missing savers at `BacktestSharded.hpp:891-904`.
4. A seam-level regression test: drive the **wrapper** (not the dispatch table) with `exit_bandit_enabled=1` through a synthetic fill and assert `exit_bandits[r].pulls` moved — the exact blind spot C.3c leaves.

**Stage 1 — artifacts:** train ≥2 exit-role models (`req_role="exit"`, pick target e.g. `will_peak`) into 2+ horizon dirs; boot and assert log `ensemble active` + `exit_predictor_count>=2` + `EXIT_BANDITS_READY` (add a boot log line if absent).

**Stage 2 — loop closure in vivo (paper):** `use_exit_model=1 exit_bandit_enabled=1`, threshold low enough to fire; confirm in order: `SHALT_EXIT_PREDICTED` observed → `exit_bandit_state.json` written at shutdown with `pulls>0` and non-uniform weights → restart logs `loaded exit_bandit state` → weights persisted. Same for `bandit_algorithm=1` with `exit_thompson_state.json` (posterior μ moved off 0.0). Also verify `confidence_ic_variant` is NOT perturbed post-fix (drift panel shows real IC, not 0.0).
**Observability gap to close first or accept:** publish exit-bandit weights/pulls into PerNodeSnap (mirror `:790-808`) — otherwise Stage 2 is JSON-forensics only.

**Stage 3 — the empirical A/B (the D-423 STILL-OPEN):** matrix per Q4; both arms `exit_blender_mode=0`, explicit `bandit_enabled`, fixed `thompson_rng_seed`, controlled state files (fresh: delete JSONs; transfer: keep); N runs across data windows; compare `BacktestStats` PF/expectancy/max-DD/return; declare on out-of-sample consistency, not a single run. Loop CLOSING is then proven at Stage 2; PROFITABLE (or not) at Stage 3.

---

## Risks / unknowns / refute-spots (where the a-class should push)

1. **H-1 itself** — strongest attack: find a production caller of `EventLoop_DrainPostFillOneCore` outside the wrapper, or show the `-Wfloat-conversion` at `:2078:42` maps to a different argument. My enumeration (all roots) found none and column 42 is the fee arg; a runtime instrumented run (print `exit_bandit_enabled` inside OneCore) would be the definitive third leg.
2. **"Dead since v5.14.1.F"** — I dated by `git log -L` region history; a-class could bisect a compiled probe across f973b5c to confirm the exact flip, and check whether any interim commit temporarily re-aligned the fan.
3. **Backtest slow-path parity assumption** — I assert the backtest runs the same `ML_BuildParameters` SELECT+lookback path via the shared `EngineCommon_SlowPathCycle*`; verified structurally (Backtest CLAUDE + shared helpers), not line-walked this session.
4. **Bundle-id coupling** — exit/Thompson persistence keys the bundle-id on **primary** fingerprints (`NodeModelZoo.hpp:2672/2726`): swapping exit models while keeping primaries reloads stale exit state against new arms (n_arms check partially mitigates only when the count changes).
5. **Exit reward shape** — the hold-to-TP counterfactual (`:2013-2019`) is optimistic (assumes TP would fill) and biases against exits by design; with the always-default fee 0.001 the bias magnitude is cfg-blind. Worth an a-class sanity pass before Stage 3 interprets P&L deltas.
6. **Buy-side reward is sign-only ±50** despite decision-log prose; whether that's the *intended* reward (vs magnitude bps) is an operator design question the empirical program inherits.
7. **`(int)0.001 == 0`** is guaranteed truncation-toward-zero (well-defined); no UB angle.

**Decision-log corrections to record:** D-423's "received reward on every qualifying fill" and "buy reward = pnl/balance bps" are both contradicted at HEAD (H-1; Q2). The D-423 STATUS cites `NodeModelZoo.hpp:3312` for the periodic `SaveThompsonState` call — it is `:3314` at HEAD (drift, not substance).

**Key files:** `CoreFrameworks/ControllerEventLoop.hpp` · `Strategies/StrategyParameters.hpp` · `ML_Headers/NodeModelZoo.hpp` · `CoreFrameworks/EngineSharded/{Run.hpp,SlowPath.hpp}` · `CoreFrameworks/{ShardedBacktestDriver.hpp,EngineCommon.hpp,OrderManager.hpp,Order.hpp,ShardedSnapshot.hpp}` · `Backtest/BacktestSharded.hpp` · `ML_Headers/{MlCfgFlagRegistry.hpp,BanditLearning.hpp,BanditAlgorithmRegistry.hpp,bandit_dispatch_table.hpp,ICVariantRegistry.hpp}` · `GUI/MLStatusPanel.hpp`.
