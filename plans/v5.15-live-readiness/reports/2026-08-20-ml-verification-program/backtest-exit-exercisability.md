# I-CLASS REPORT — Backtest ML exit-model path: end-to-end exercisability audit

> Saved verbatim at receipt 2026-08-20 (orchestrator write per `feedback_save_agent_reports_verbatim`).
> ⚠️ Independently converges with bandit-loop-state.md H-1 on the FAN-SHIFT defect (Defect 2 here).

**Engine HEAD 417e524 (feat/v5.15-live-readiness) · 2026-08-20 · agent I-1 (dedicated skill walked: `/dependency-chain-trace`, chain:`last_exit_prediction`/`exit_bandit_enabled` flow)**
**Roots covered:** `Backtest/`, `CoreFrameworks/` (incl. `CoreFrameworks/EngineSharded/`), `ML_Headers/`, `Strategies/`, `DataStream/`, `GUI/`, `MemHeaders/`, `tests/` — named explicitly per Landmine 19; all probes uncapped with rc captured directly; empty probes re-run with positive controls.

## VERDICT

**BACKTEST EXIT PATH: EXERCISABLE for load → predict → exit-submit → fill → P&L. BLOCKED-BY-DrainPostFill-ARG-PLUMBING for the exit-bandit REWARD UPDATE — and that update is dead at HEAD on the LIVE path too (positional-shift defect at the fan→OneCore hop), so the "empirical exit-bandit backtest" cannot measure learning until the plumbing is fixed.**

PARITY-027's closure (workspace `DOCS/PARITY_ISSUES.md:470`, "closed at WIP-13 via EngineCommon_SlowPathCycleOneCore") **is REAL at HEAD** for what it claims — the exit-model *dispatch/submit* — and both architectures reach it. The bandit reward half was never in PARITY-027's scope, and it is where the program blocker lives.

---

## Q1 — Does the backtest slow-path cycle reach the exit-model dispatch? YES (every hop verified shared)

| # | Hop | Site | Backtest reaches it? |
|---|---|---|---|
| 1 | Per-tick driver | `ShardedBacktest_RunTick`, `CoreFrameworks/ShardedBacktestDriver.hpp:299` (cadence `(tick_index+1) % drv->slow_path_interval == 0`) | YES — `BacktestSharded.hpp:701` calls it per tick; driver wired at `BacktestSharded.hpp:405-423` (`ShardedBacktestDriver_Init(&drv, &state, &rolling, &cfg, (int)cfg.poll_interval, &rolling_long, &oms)` :406) |
| 2 | Fan wrapper | `EngineCommon_SlowPathCycleAllCores<F>` call at `ShardedBacktestDriver.hpp:412-415` (guarded `drv->config && drv->oms && drv->rolling` :400 — all wired) | YES |
| 3 | Per-node body | `EngineCommon_SlowPathCycleAllCores` loops `EngineCommon_SlowPathCycleOneCore` over `state.registered_count`, `CoreFrameworks/EngineCommon.hpp:930-933` | YES |
| 4 | Predict (writes the prediction) | `EventLoop_RebuildOneCore` call at `EngineCommon.hpp:621-631` → fn def `CoreFrameworks/ControllerEventLoop.hpp:2614` → `Strategy_BuildParameters(...)` `:3097-3115` with `dispatch_ctx=&ml_ctx` for `STRATEGY_ML` (`:2956`, `:3041`) → ML exit block writes `*mctx->out_exit_prediction` at `Strategies/StrategyParameters.hpp:1594` | YES — same function, both paths |
| 5 | Exit-submit gate | `EngineCommon.hpp:668-671`: `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_USE_EXIT_MODEL) && state.nodes[c].last_exit_prediction > FPN_ToDouble(cfg.nodes[c].exit_threshold) && price_d > 0.01` | YES — inside the shared body |
| 6 | Submit | `tt::OMS_PushExitForSlot(&oms, pidx, qty, strategy_id, price_fpn, leg 0, &cfg.nodes[c])` `EngineCommon.hpp:746-748` → `OMS_PushSubmit` via `MemHeaders/OmsPushExitHelper.hpp:87-90`; per-slot attribution marks set BEFORE push (`last_exit_predicted_bitmap` :694, `last_exit_predicted_p` :695-696, `OMS_META_PACK(arm, regime)` :738-743); `SHALT_EXIT_PREDICTED` set :750-751 | YES |
| 7 | Drain + fill | Backtest drains synchronously same tick: `OMS_DrainSubmit` `ShardedBacktestDriver.hpp:263` → `OrderManager_Tick` `:269` (paper adapter: `OrderManager_Init(&oms, empty_adapter, 0, …, event_log_mode=1, "")` `Backtest/BacktestSharded.hpp:207-210`); `handle_sell_fill` is the `ORDER_MARKET_SELL=1` row of the fill dispatch table `CoreFrameworks/OrderManager.hpp:1594` | YES |

**Live-only branches inside the chain:** none in the SlowPathCycleOneCore body itself. Live-only pieces are *outside* the helper by design (M5 exemptions, `EngineCommon.hpp:60-65`): `ShardedTradeLog_Init`/`OrderManager_OpenCalibrationLog` (`EngineSharded/Run.hpp:791`/`:762`) and the `oms.ezoo_refs[i]`/`node_cfg_refs[i]` wires (`Run.hpp:1043-1044`; noted LIVE-only at `EngineCommon.hpp:360-362`) — these gate *observability sinks* (Q6), not the execution path.

Callers cross-check: LIVE calls OneCore directly per-thread (`EngineSharded/Run.hpp:2046`); BACKTEST via the AllCores fan (`ShardedBacktestDriver.hpp:412`); no other production callers (uncapped grep across all roots, rc=0).

## Q2 — Does the backtest LOAD models? YES, including exit.json siblings, via the shared boot half

- Boot sharing: `Backtest/BacktestSharded.hpp:223` `EngineCommon_ApplyBnbDiscount` → `:237` `EngineCommon_BootGlobal` → `:306-308` `EngineCommon_BootPerCore(cfg, i, state, tick_rings[i], nodes[i], zoo_ptr, ezoo_ptr, node_balance)`.
- Zoo storage: static `ml_zoos[MAX_EXECUTION_NODES]` / `ml_ensemble_zoos[...]` (`BacktestSharded.hpp:260,:265`); Free+Init per run; pointers non-null iff `cfg.node_strategies[i] == STRATEGY_ML` (`:292-299`).
- Load inside the shared helper (`CoreFrameworks/EngineCommon.hpp`): single-zoo `NodeModelZoo_LoadFromDir` :314 (gated `cfg.node_model_dir[c][0]` :307); ensemble `EnsembleModelZoo_AutoDetectFromDir` :365-372 (also gated on `node_model_dir` :364) → scans `<base>_horizon_<digits>` sibling dirs (`ML_Headers/NodeModelZoo.hpp:2508-2528`) → **`EnsembleModelZoo_LoadFromCfg` at `NodeModelZoo.hpp:2550`** → per horizon tries roles `barrier`/`regime`/**`exit`**/`buy_signal` via `NodeModelZoo_TryLoadRole` (`:2127-2164`; exit at `:2148-2157`), filename `<dir>/<role>.json` then `.xgb` (`:233,:240`). So **exit models = `<node_model_dir>_horizon_<H>/exit.json`, and they DO load in backtest.**
- Post-load (shared, `EngineCommon.hpp:380`): `EnsembleModelZoo_PostLoadSetup` walks the 11-step `FOREACH_ENSEMBLE_POST_LOAD` (`NodeModelZoo.hpp:3380-3441`) — including `init_exit_bandits` (`:3384`, `cfg.exit_bandit_lr`), `load_exit_bandit` (`:3395`, reads `<base>/exit_bandit_state.json`), `init_exit_thompson_bandits` (`:3411`), `load_exit_thompson_state` (`:3416`). `MASK_EZOO_EXIT_BANDITS_READY` is set when `exit_predictor_count >= 1` and bandits genuinely init at `>= 2` arms (`NodeModelZoo.hpp:1862-1892`).
- Cfg keys (backtest.cfg — the suite's cfg file, `Backtest/BacktestPanels.hpp:260,:2660`; `BacktestSharded_Run` loads `ControllerConfig_Load<BACKTEST_FP>(run_cfg->config_path)` `BacktestSharded.hpp:127-131`): `node_N_model_dir=` (parse `ControllerConfig.hpp:3262-3281`), `node_N_strategy=ml` (`:3282-3292`, "ml"→3). **`core_N_*` keys are RETIRED and REFUSE BOOT** (`ControllerConfig.hpp:3486-3489`) — the mission's `core_N_*` spelling would hard-fail a run.

**Not a blocker.** The backtest loads single + ensemble + exit models identically to live by construction.

## Q3 — Is `mctx->out_exit_prediction` wired on the backtest path? YES — there is no separate backtest populator; the populator is SHARED

- The three-condition gate: `Strategies/StrategyParameters.hpp:1425-1429` — `BITMAP_IS_SET(node_cfg->ml_cfg_flags, MASK_ML_CFG_USE_EXIT_MODEL) && ezoo_ex && ezoo_ex->exit_predictor_count > 0 && mctx && mctx->out_exit_prediction`.
- The ONE populator lives inside `EventLoop_RebuildOneCore` (fn def `ControllerEventLoop.hpp:2614`; ML block `:2954-3041`): resets then wires `ml_ctx.out_exit_prediction = &state->nodes[slot].last_exit_prediction` / `out_exit_dominant_horizon` at `:3029-3032`. Since `EngineCommon_SlowPathCycleOneCore` calls `EventLoop_RebuildOneCore` on BOTH paths (`EngineCommon.hpp:621`), the backtest gets the identical wiring per cycle. **The mission's cite "live populator ~:1818-1840 per CLAUDE_ML_INVARIANTS" is STALE** — `:1818-1846` is now inside `EventLoop_DrainPostFillOneCore` (exit-P&L derivation region); the doc's line-anchor should be refreshed to ~`:3029`.
- `node_cfg` at the gate = `&resolved_cfg.nodes[slot]` (`ControllerEventLoop.hpp:3100`); per-node `ml_cfg_flags` is propagated from the resolved global at `ControllerConfig.hpp:1815` — value-equivalent on both paths. `tools/check_per_node_registry_integrity.py` runs clean at HEAD (rc=0, Checks 1-11 PASS) — the per-node reads in this chain are registry-conformant.

## Q4 — Exit-fill attribution + the bandit reward UPDATE. Fill/P&L: SHARED and works. Reward UPDATE: DEAD — two independent defects

**Fill → realized P&L (works, shared):** the ML exit's MARKET_SELL fills through the same `OrderManager_Tick`/HandleFill pipeline (backtest `event_log_mode=1` since v4.7.15, `BacktestSharded.hpp:182-210`); `EventLoop_DrainPostFillOneCore` derives `exit_entry_notional`/`exit_net_pnl` via the D-190 `Money_FillGross` SSoT (`ControllerEventLoop.hpp:1784-1795`) and applies `ctx.node_realized` (`:1798`), `total_exits++` (`:1802`). Backtest invokes the fan per tick + at final flush (`ShardedBacktestDriver.hpp:285-288`, `:485-488`).

**Reward UPDATE site** — shared code, `ControllerEventLoop.hpp:1985-2036`, inside `EventLoop_DrainPostFillOneCore`, gated on the **parameter** `exit_bandit_enabled` plus per-slot attribution marks + `MASK_EZOO_EXIT_BANDITS_READY` + valid packed arm/regime; dispatches `g_exit_reward_dispatch<F>[exit_algo](ezoo, regime, chosen_arm, reward_bps)` (`:2033`).

**Defect 1 — backtest never forwards the flag (the PARITY-027-shaped sibling gap).** Both backtest call sites pass only 4 args — `EventLoop_DrainPostFill(drv->state, drv->oms, drv->config->sl_cooldown_cycles, drv->config->ensemble_trade_reward_mult)` (`ShardedBacktestDriver.hpp:285-287` and `:485-487`) — so `exit_bandit_enabled` falls to its declared default `= 0` (`ControllerEventLoop.hpp:2070`). LIVE's binder does forward it: `EngineSharded_SlowPath_DrainPostFill` passes `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_EXIT_BANDIT_ENABLED)` (`EngineSharded/SlowPath.hpp:72-78`).

**Defect 2 — NEW FINDING, HIGH severity, hits LIVE too: positional-arg shift at the fan→OneCore hop.** `EventLoop_DrainPostFillOneCore`'s signature (verbatim, `ControllerEventLoop.hpp:1627-1654`) has **12 params** with `int confidence_ic_variant = 0` at **position 9** (`:1644`, added v5.14.1.F), then `exit_bandit_enabled` (10, `:1649`), `fee_rate_taker_for_cf` (11, `:1650`), `node_cfg` (12, `:1654`). The fan `EventLoop_DrainPostFill` (`:2056-2071`) has **no `confidence_ic_variant` param** and forwards **10 positional args** (`:2073-2078`). Net binding on EVERY production call:
  - fan's `exit_bandit_enabled` (arg 9) → binds **`confidence_ic_variant`** (int→int, silent);
  - fan's `fee_rate_taker_for_cf` (arg 10, `0.001` double) → binds **`exit_bandit_enabled`** (double→int standard conversion, **truncates to 0**, compiles silently — no `-Wconversion` found in `CMakeLists.txt`, 0 hits for `CMAKE_CXX_FLAGS|add_compile_options`);
  - real `fee_rate_taker_for_cf` and `node_cfg` take their defaults (0.001 / nullptr).

  Consequences at HEAD: **(a)** the exit-bandit reward update never fires ANYWHERE — live included — regardless of cfg; **(b)** in LIVE, enabling `exit_bandit_enabled=1` silently flips the drift-path IC variant from Spearman(0) to variant 1 (consumed at `:1890`; registry `ML_Headers/ICVariantRegistry.hpp`) — a spooky cross-feature coupling; **(c)** `cfg.confidence_ic_variant` (row `CfgFieldRegistry.hpp:689`) is never honored on this path (no caller passes it; only the snapshot display reads it, `ShardedSnapshot.hpp:617`). Overload check: exactly one definition of each fn (uncapped grep). No test exercises the production chain with the flag set — all `exit_bandit` tests call `Bandit_Update` directly or test cfg parse/save-load (`tests/controller_test.cpp:21642-21838`); all fan/OneCore test calls use 3-4-arg forms (`tests/controller_test.cpp:9101` et al.) — masked, Class-12 shape.

**Defect 3 (consequence of nullptr `node_cfg`):** `exit_algo = node_cfg ? node_cfg->bandit_algorithm : BANDIT_ALGO_EXP3` (`:2031`) — the fan never passes `node_cfg`, so even with defects 1-2 fixed, the exit reward would always dispatch `exp3_only_reward` (`bandit_dispatch_table.hpp:257-261`): the exit-side Thompson posterior never updates from fills, contradicting the .F.4d closure comment at `:2022-2030`. Same nullptr also reaches the buy-side `EnsembleModelZoo_TradeCloseReward(..., node_cfg)` at `:1958-1960` — the buy-side Thompson reward claim is suspect for the same reason (flagged, not fully traced).

**Stale-comment finding (this surface's false-claim history, per arming § 2.5):** `EngineSharded/SlowPath.hpp:92-97` claims the "`fee_rate_taker_for_cf` scalar param chain DELETED from EventLoop_DrainPostFill / DrainPostFillOneCore signatures" — FALSE at HEAD; both signatures still declare and the counterfactual math still consumes it (`:1650`, `:2071`, `:2014`). Also the 2026-08-16 SELECT comment "fed reward on every qualifying fill" (`StrategyParameters.hpp:1476-1478`) is FALSE at HEAD given defect 2. Also the fan's "Centralized + backtest paths use this" (`:2054`) is stale — the live sharded binder calls it too (`SlowPath.hpp:72`).

**SELECT half (for completeness):** the 2026-08-16 bandit-SELECT block (`StrategyParameters.hpp:1497-1537`) IS shared and fires in backtest when `MASK_ML_CFG_EXIT_BANDIT_ENABLED` + `MASK_EZOO_EXIT_BANDITS_READY` + `exit_predictor_count >= 2`; it re-points `dominant` (the reward-attribution arm) at the bandit's chosen arm. So in a backtest today: bandit SELECTS (from prior/loaded state) but never LEARNS.

## Q5 — Minimal backtest.cfg fragment + silent-disable defaults

Keys parse: flag keys via the ML bitmap walk (`ControllerConfig.hpp:2907-2914`) using the registry `legacy_field` spellings (`ML_Headers/MlCfgFlagRegistry.hpp:68-69`); scalars via `FOREACH_CFG_FIELD` rows.

```ini
# --- nodes (exact per-node prefix is node_N_ ; core_N_ REFUSES BOOT at HEAD) ---
num_execution_nodes=1
node_0_strategy=ml                  # required: zoo load + ml_ctx wiring gate on STRATEGY_ML
node_0_model_dir=models/mybundle    # exit models auto-detect at models/mybundle_horizon_<H>/exit.json
                                    # >=2 horizon dirs with exit.json => 2+ bandit arms (READY + SELECT)
                                    # buy_signal/barrier models must exist too, or no ENTRIES => nothing to exit

# --- exit-model path (all default OFF/neutral) ---
use_exit_model=1                    # default 0 (ControllerConfig.hpp:2014) — leaves last_exit_prediction at 0.0, submit gate never fires
exit_threshold=0.6                  # default 0.6 (CfgFieldRegistry.hpp:787); global propagates per-node; lower to fire more exits

# --- exit-bandit (SELECT works; UPDATE currently dead — see Q4 blockers) ---
exit_bandit_enabled=1               # default 0 (ControllerConfig.hpp:2013)
exit_bandit_lr=0.1                  # default 0.1 (ControllerConfig.hpp:2193)
bandit_algorithm=0                  # per-node row, default 0=EXP3 (CfgFieldRegistry.hpp:744); reward side is EXP3-forced anyway at HEAD (Q4 defect 3)
thompson_rng_seed=42                # default 42 (CfgFieldRegistry.hpp:698) — pins Thompson-select determinism
```

Silently-disabling defaults to watch: `use_exit_model=0`, `exit_bandit_enabled=0`, empty `node_N_model_dir` (`:2303` — no models, `MODEL_LOAD_FAILED`), missing `node_N_strategy=` (defaults SIMPLE_DIP with a boot WARN, `ControllerConfig.hpp:3507-3514`), `exit_threshold` 0.6 (predictions below it never submit), warmup (`min_warmup_samples` fallback 64, `EngineCommon.hpp:801-810` — no entries until ~64 slow-path cycles), and `held_out_gate_strict` default warn-only (unstamped exit.json loads with WARN — convenient for dev bundles). Note `bandit_enabled` (buy-side) now defaults **1** (`ControllerConfig.hpp:2004-2012`).

## Q6 — Scoreboard: where exit-attributable results land after a backtest run

| Surface | Backtest? | Cite |
|---|---|---|
| `BacktestStats` (total_pnl, trades, W/L, win_rate, avg_win/loss, PF, expectancy, max_dd, return_pct) + `equity_curve` per closed trade | YES — the primary comparator for bandit-on vs uniform (A/B two runs over the same ticks) | `BacktestSharded.hpp:836-868`, wins/losses classified per realized-pnl delta `:765-775`, equity `:783-787` |
| Per-node last exit prediction/horizon in dashboard snapshot | END-OF-RUN only (single `TUI_CopySnapshotSharded` after the loop) | copy `BacktestSharded.hpp:875-880`; fields `ShardedSnapshot.hpp:604-605` → `EngineTUI.hpp:1225-1226`; GUI reader `GUI/MLStatusPanel.hpp:189-198` |
| `SHALT_EXIT_PREDICTED` per node | set in-state (`EngineCommon.hpp:750-751`); visible only via the same end-of-run snapshot | |
| Buy-side `bandit_state.json` saved at backtest completion | YES | `BacktestSharded.hpp:891-904` |
| **Exit** `exit_bandit_state.json` (+ Thompson states) at backtest completion | **NO — end-of-run save is buy-side only**; exit-side shutdown save is LIVE-only (`Run.hpp:2336-2341`). Periodic path saves exit too since 2026-08-16 (`NodeModelZoo.hpp:3306-3316`) but its counter feeds off buy-side update crossings (interval default 5000) — and with the Q4 blockers there is nothing new to save anyway | |
| Trade CSV with exit rows (`ShardedTradeLog_RecordExit`) | NO — `on_exit_fill_emit` stays noop; trade log wired only in LIVE (`Run.hpp:791,:797`; noop default `OrderManager.hpp:1577`) | |
| Exit calibration CSV (pred_flag, pred_p, bandit arm/regime, reward_bps per exit fill — the richest per-exit attribution record) | NO — `OrderManager_OpenCalibrationLog` is called only at `Run.hpp:762`; backtest's `on_exit_calibration` stays noop (`OrderManager.hpp:685,:1552-1553`; emitter `:816-864`) | |

Practical consequence: an exit-bandit A/B backtest today can compare only aggregate `BacktestStats`/equity between runs; per-exit attribution (which arm, what reward) has NO backtest sink.

---

## Option matrix (for making the empirical exit-bandit backtest real)

| Option | What | Pros | Cons |
|---|---|---|---|
| **A. Minimal 3-line repair** | (1) thread `confidence_ic_variant` through the fan + fix the fan→OneCore forward order; (2) backtest driver forwards `BITMAP_IS_SET(drv->config->ml_cfg_flags, MASK_ML_CFG_EXIT_BANDIT_ENABLED)` at `:285` + `:485`; (3) fan passes `&cfg…nodes[c]` — but the fan has no cfg param, so (3) forces a signature change anyway | Smallest diff; unblocks the experiment | Leaves the defaulted-mid-tail landmine armed (it has now fired twice on this one signature: default-swallow + positional shift); still hand-mirrors the cfg→arg binding per caller (the exact Class-18 shape .B.4 was built to kill) |
| **B. Structural, M5-conformant (recommended)** | Extract ONE shared binder — `EngineCommon_DrainPostFill(cfg, state, oms)` (relocate/generalize `EngineSharded_SlowPath_DrainPostFill`, `SlowPath.hpp:67-79`) — called by LIVE drainer + both backtest sites; fan loops per-core passing `&cfg.nodes[c]` as `node_cfg`; strip the defaulted tail from fan/OneCore (keep the 3-4-arg head stable to preserve ~40 test call sites) | Closes defects 1+2+3 and the exit-Thompson dead-end in one motion; same by-construction logic that closed PARITY-026..032; kills the whole "cfg-bit threaded as positional scalar across two hops" class | OneCore signature surgery (12 params); needs the M5 checklist + test-call audit; slightly bigger blast radius |
| **C. Novel alternative considered** (`feedback_proactive_novel_alternative_consideration`) | Delete the boolean ARG entirely: read `MASK_ML_CFG_EXIT_BANDIT_ENABLED` from `node_cfg->ml_cfg_flags` inside OneCore at the point of use (`node_cfg` param already exists, `:1654`; fan supplies `&cfg.nodes[c]`); keep genuinely-global scalars (drift floor/window/kill, ic_variant) as NON-defaulted explicit args or move them to cfg reads too | Removes the mirror-arg category rather than patching it (structural-fix-over-belt-and-suspenders); decision-time cfg read matches the codebase's own decision-time-binding doctrine; a future flag addition = zero new params | `node_cfg`'s nullptr fallback semantics must be pinned for the 3-4-arg test callers (nullptr ⇒ feature off = today's behavior); drift knobs are global-scope so a pure per-node read doesn't cover them — hybrid form in practice (this is B's deeper variant, not a separate destination) |
| **D. No-code workaround** | Load a live-learned exit state via `run_cfg->bandit_state_prior_path` (`BacktestSharded.hpp:315-319`) and A/B frozen-bandit vs uniform | Zero engine change; tests SELECT quality with fixed weights | Cannot test LEARNING (the stated goal); reward loop still dead; scoreboard still aggregate-only |

**Recommendation: B, folding in C's per-node-bit read for the boolean.** Rationale per the maintenance gradient (structural fix when the class recurs — it has, twice, on this signature) and M5 (the drainer arg-binding is the last execution-layer hop still mirrored by hand after .B.4). Whatever is chosen, the **backtest end-of-run save should add the exit-side savers** (mirror `Run.hpp:2336-2365` at `BacktestSharded.hpp:891-904`), and a backtest-side exit-attribution sink (calibration-log open behind a run_cfg knob, or a results-array of per-exit records) is needed for the experiment to be *readable*. Separately: the fan positional-shift class has NO covering CI tool — a candidate M7 guard is "no defaulted parameter may precede a non-defaulted-in-caller forward" or simply banning defaulted mid-tail insertion on multi-hop forwards (grep-able signature lint).

## Spots most worth an adversarial refute (for the paired a-class)

1. **The positional-shift claim (Q4 defect 2) — highest value.** My case is source-read of two signatures + one forward (`:1627-1654`, `:2056-2078`). Refute by: compiling a minimal probe of the real headers asserting which param receives the fan's arg 9; checking build flags actually used (`build.sh` — I only checked `CMakeLists.txt`, 0 hits, rc=1 on the grep); and `git log -L` on `ControllerEventLoop.hpp:1644` to date the insertion vs the fan forward (I did NOT blame it — if `confidence_ic_variant` predates the fan's exit-bandit args, the story inverts to "fan authored against the wrong signature", same defect different genesis).
2. **"No test exercises the production reward chain"** — I grepped `exit_bandit` across `tests/` (4 files, hits only in `controller_test.cpp`). Refute by scanning for indirect drivers (a fixture that builds cfg with the flag and runs the driver loop).
3. **The claim exit updates were EVER live** — the 2026-08-16 comment says reward "was fed on every qualifying fill"; if some pre-.B.6 call path passed args differently, the shift may be a regression introduced by the SlowPath.hpp hoist (v5.15.5.F.4d.1.B.6, `SlowPath.hpp:88-90`) rather than v5.14.1.F. Archaeology changes the fix's framing, not its necessity.
4. **Backtest determinism of the SELECT half** — `BanditAlgorithm_Apply` for EXP3 (is arm selection RNG-bearing? seeded from what?) and Thompson (seeded `thompson_rng_seed`, `NodeModelZoo.hpp:3411-3415`) — I did not read `BanditAlgorithm_Apply`'s body. If EXP3 select consumes an unseeded RNG, A/B runs aren't replay-identical.
5. **Drift-arg forwarding semantics in backtest** (option A/B scope call): forwarding `cfg.confidence_ic_floor`/`auto_kill_on_drift` to backtest activates IC-drift auto-kill during replay — desirable parity or replay contamination? Needs an operator call.
6. **`exit_threshold` per-node override key** — the row is per-node via `FOREACH_PER_NODE_CFG_FIELD` (`ControllerConfig.hpp:2813`); I did not positively verify that `node_0_exit_threshold=` parses (the auto-flow per-node parser path). The global key verifiably parses.

## Risks / unknowns

- **CLAUDE_ML_INVARIANTS line-anchor drift**: the "~:1818-1840 live populator" cite is stale (now `:3029-3032`, and it's shared, not live) — doc fix owed.
- `real_on_exit_calibration` uses `system_clock::now()` (`OrderManager.hpp:821-823`) — if a backtest calibration sink is added (recommendation), that timestamp must switch to tick time for determinism.
- Buy-side Thompson trade-close reward may share defect 3 (nullptr `node_cfg` at `:1958-1960`) — flagged, not fully traced; separate verification pass warranted.
- `BACKTEST_FP` assumed 64 (F=64 templates throughout); not independently pinned.
- Per arming § 6: I edited nothing; this report is the returned data. Uncovered roots: none of the named roots were skipped; `tools/` was consulted only via `DOCS/TOOLS.md`-listed runners.
