---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: P-1 — NodeContext persist-exemption VERIFICATION, group 1/3: the HANDLE + LIFECYCLE family
agent_class: i-class
delivered: 2026-08-15
ground: engine HEAD 564f099, branch feat/v5.15-live-readiness
headline: gate_state is UNSAFE and S-4's finding is CONFIRMED not moot — probe-proven that neither EventLoopState container is value-initialized and NODE_CTX_INIT_AUTOPOPULATE never touches it, so the field is indeterminate (UB) with an unsynchronized cross-thread reader. Severity nuanced honestly in BOTH directions - a fresh stack reads 0x0000 by accident while a dirtied stack keeps the poison, and the sole consumer bit LADDER_BOTTOM_HIT has zero readers tree-wide, so a latent defect is currently masked by a dead feature. Separately, strategy_state's obvious RUNTIME_POINTER reason is true-but-insufficient - it is silent about 720B of accumulated adaptation behind the pointer
operator_decision_owed: P1-1 (gate_state — record as UNESTABLISHED_UNTIL_FIRST_PASS, a category the guard treats as RED rather than a valid exemption; the fix is one Layer-2 line) · the vocabulary corrections in § 6 (RUNTIME_POINTER must carry a re-establishment SITE; a pointer's exemption does not cover its POINTEE; DERIVED_EACH_PASS must answer "what reads it before the first derive?" or the guard accepts gate_state and is vacuously green on the one real defect) · X-1 (LADDER_BOTTOM_HIT set-but-never-read snapshot bit) · X-2 (a stale single-threaded comment that is very likely WHY the missing init survived)
sister_reports: P2-eval-transient-display.md · P3-substructs.md
---

All probes removed; `git status` is byte-identical to session start. Here is my report.

---

# P-1 — NodeContext persist-exemption VERIFICATION, group 1/3: the HANDLE + LIFECYCLE family

**Agent:** I-class (investigative) · **Date:** 2026-08-15 · **Ground:** `/home/caramel/code/FoxML_Trader_v2` @ `564f099`, branch `feat/v5.15-live-readiness` · **Mode:** read-only (no edits; two probes compiled into `build/` and removed — `git status` verified byte-identical to session start, same 4 untracked files).

**Methodology:** `/dependency-chain-trace` SKILL.md (`/home/caramel/code/FoxML_Trader_v2/.claude/skills/dependency-chain-trace/SKILL.md`) walked per its 7-step workflow. Mechanical tools run: `tools/node_persist_layout.py` (GREEN, 46 flattened wire rows match golden), `tools/gen_code_map.sh --composition SlowPathGateState`, `tools/gen_code_map.sh --byte-context GateParameters`. Two compiled probes settled the questions grep could not.

---

## 1. Verdict table

| # | off | field | Category | Verdict |
|---|---|---|---|---|
| 1 | 0 | `gate_state` | **none of the four fit** — I propose `UNESTABLISHED_UNTIL_FIRST_PASS` | **UNSAFE** — real defect. S-4's finding **CONFIRMED, NOT moot**. Structural HIGH / live impact LOW-today, LATENT-HIGH |
| 2 | 8 | `core` | `RUNTIME_POINTER` → `NodeCtxInitRegistry.hpp:100` + `ControllerEventLoop.hpp:1275` | **SAFE-UNPERSISTED** |
| 3 | 16 | `slow_state` | `RUNTIME_POINTER` → `NodeCtxInitRegistry.hpp:322` (Layer 4 arena alloc) | **SAFE-UNPERSISTED** |
| 4 | 24 | `model_handle` | `RUNTIME_POINTER` → `NodeCtxInitRegistry.hpp:101` + `EngineCommon.hpp:343` | **SAFE-UNPERSISTED** |
| 5 | 32 | `ensemble_handle` | `RUNTIME_POINTER` → `NodeCtxInitRegistry.hpp:102` + `EngineCommon.hpp:394` | **SAFE-UNPERSISTED** |
| 6 | 40 | `strategy_state` | `RUNTIME_POINTER` is **TRUE BUT INSUFFICIENT** — needs a second clause. I propose `POINTEE_STATE_REDERIVED(warmup-gated)` | **SAFE-UNPERSISTED, but the obvious reason is the wrong reason.** See §4.6 — this is the near-miss of the ic.actuals shape |
| 7 | 1920 | `pending_params` | `DERIVED_EACH_PASS` + boot-init + consumer-gated | **SAFE-UNPERSISTED** (strongest case of the seven) |

Probe-confirmed offsets match the orchestrator's mechanically-computed table exactly (0/8/16/24/32/40/1920), `sizeof(NodeContext<64>) = 7168`, `sizeof(EventLoopState<64>) = 272640`.

---

## 2. The decisive structural fact (applies to all 7)

The boot sequence is **fully ordered and single-threaded** up to the producer spawn:

| Step | Site | What it establishes |
|---|---|---|
| 1 | `CoreFrameworks/EngineSharded/Run.hpp:821` — `EventLoopState<F> state;` | **default-init**, no `{}`, not `static`. **Nothing is zeroed.** |
| 2 | `Run.hpp:830` → `CoreFrameworks/EngineCommon.hpp:214` → `ControllerEventLoop.hpp:1142-1144` | `NODE_CTX_INIT_AUTOPOPULATE` over **all 16** slots (not just registered) |
| 3 | `EngineCommon.hpp:266+` `EngineCommon_BootPerCore` per node | `core` (RegisterCore), `strategy_id`, `model_handle`, `ensemble_handle`, `strategy_state` |
| 4 | `Run.hpp:1069` — `ShardedSnapshot_Load` (**paper mode only**; live reconciles vs exchange instead) | overlays the 29 persisted rows |
| 5 | `Run.hpp:1358` — `std::thread producer(...)` | **first concurrency** |
| 6 | `Run.hpp:1475` hot executors · `:1539` drainer · `:1712` per-node slow threads | |

`ShardedSnapshotPersist.hpp:513-514` states the contract explicitly: *"no atomic needed — core hot-path thread isn't running yet at snapshot-load time."* Verified against the spawn line numbers above.

**`NODE_CTX_INIT_AUTOPOPULATE` (`MemHeaders/NodeCtxInitRegistry.hpp:300-325`) has 5 layers.** `gate_state` appears in none of them, and in no row of `FOREACH_NODE_CTX_FIELD` (`:98-145`). Every other field of my seven is covered:

- Layer 1 (`:306`, registry walk): `core`/`model_handle`/`ensemble_handle`/`strategy_state` ← `nullptr` (rows `:100-103`)
- Layer 2 (`:308`): `GateParameters_Init(&_autop_ctx.pending_params)`
- Layer 4 (`:322`): `_alloc_and_init_slow_state` → `slow_state`

**No `memset`/`calloc` of `EventLoopState` or `NodeContext` exists anywhere** (searched `CoreFrameworks/`, `Backtest/`; the only hits are unrelated `BacktestPanels` panel-state resets).

---

## 3. FINDING P1-1 — `gate_state` (S-4 finding CONFIRMED, escalated on one axis, downgraded on another)

### 3.1 What I proved, mechanically

Probe 1 (placement-new over 0xAA-poisoned storage — the *same initialization category* as `EventLoopState<F> state;`):

```
-- AFTER default-init, BEFORE EventLoopState_Init (node 0) --
  gate_state.flags          = 0xAAAA
  core                      = 0xaaaaaaaaaaaaaaaa
  slow_state                = 0xaaaaaaaaaaaaaaaa
  model_handle              = 0xaaaaaaaaaaaaaaaa
  ensemble_handle           = 0xaaaaaaaaaaaaaaaa
  strategy_state            = 0xaaaaaaaaaaaaaaaa
  pending_params.flags      = 0x000000AA
  strategy_id               = 170

-- AFTER EventLoopState_Init (== NODE_CTX_INIT_AUTOPOPULATE x16) (node 0) --
  gate_state.flags          = 0xAAAA          <-- STILL POISONED
  core                      = (nil)
  slow_state                = 0x7f1b4c365040
  model_handle              = (nil)
  ensemble_handle           = (nil)
  strategy_state            = (nil)
  pending_params.flags      = 0x00000000
  pending_params.strategy_id= 255             (STRATEGY_NONE)
  strategy_id               = 255

BITMAP_IS_SET(gate_state, MASK_CONFIDENCE_ENABLED) = 1   <-- reads TRUE on poison
after ONE SLOW_PATH_GATE_AUTOPOPULATE_PER_NODE(default cfg): 0x0000
trivially_default_constructible<SlowPathGateState> = 1
```

**Answer to your direct question — "is `NodeContext` ever value-initialized somewhere that would zero it anyway?" NO.** Both container sites are default-init function-locals:
- `CoreFrameworks/EngineSharded/Run.hpp:821` — `EventLoopState<F> state;`
- `Backtest/BacktestSharded.hpp:225` — `EventLoopState<BACKTEST_FP> state;`

`NodeContext<64>` is *not* trivially default constructible (its `sp_telemetry`/`WsHeartbeatTelemetry` atomics carry NSDMIs), so its implicit ctor runs — but it default-initializes members without NSDMIs, leaving `SlowPathGateState gate_state;` (`ControllerEventLoop.hpp:330`; struct at `CoreFrameworks/SlowPathGateRegistry.hpp:184-186`, no NSDMI) **indeterminate**.

### 3.2 The nuance that changes the severity story — probe 2

Because I did not want to over-claim, I ran a second probe replicating the **real frame shape** (function-local `EventLoopState<64> state;`, `-O2`):

```
[FRESH-STACK  (no prior deep callee)]  BEFORE Init: 0x0000   AFTER Init: 0x0000
[DIRTIED-STACK(after a 400KB callee)]  BEFORE Init: 0xAAAA   AFTER Init: 0xAAAA
```

**Fresh OS anonymous pages are zero-filled, so the field reads 0 *by accident*. A prior callee's frame survives, and `EventLoopState_Init` does not clear it.** Which one production gets is a function of unrelated pre-boot stack usage.

Measured context: `sizeof(ControllerConfig<64>) = 53056`, and `ControllerConfig_Load` (`main.cpp:76`) runs before `EngineSharded_Run` (`main.cpp:220/222`) as a sibling callee of `main`. So roughly the **top ~53KB** of `EngineSharded_Run`'s ~273KB frame region is pre-dirtied. Whether `nodes[i].gate_state` lands inside that 53KB is a **compiler frame-layout coincidence** that any edit to the boot path can flip.

**That is the argument for closing it structurally rather than reasoning about whether it manifests:** it can read benign-zero for a year and silently flip when someone adds a local buffer to a boot function. It is also an indeterminate read of a `uint16_t` (UB per `[basic.indet]` — `unsigned char`/`std::byte` are the only exempt types), MSan-detectable.

### 3.3 The race window is real — I traced both ends

| End | Site | Cadence |
|---|---|---|
| **Writer** (the only one) | `ControllerEventLoop.hpp:2684-2686` `SLOW_PATH_GATE_AUTOPOPULATE_PER_NODE(state->nodes[slot].gate_state, resolved_cfg)` inside `EventLoop_RebuildOneCore` | per-node slow-path thread, spawned `Run.hpp:1712` |
| **Cross-thread reader** | `CoreFrameworks/ShardedSnapshot.hpp:597` `BITMAP_IS_SET(state->nodes[i].gate_state.flags, tt::MASK_LADDER_ACTIVE)` | **producer thread** (`Run.hpp:1358`), via `Async.hpp:507` → `TUI_CopySnapshotSharded` |
| **In-band readers** | `Strategies/StrategyParameters.hpp:1201,1203,1217,1435,1444,1604,1613,1706,1725` via `mctx->gate_state` | ordering-**safe** — see below |

**There is no happens-before edge between them.** The producer's publish fires on `slow_path_counter >= slow_path_interval` (`CoreFrameworks/EngineSharded/Async.hpp:302`), a producer-local counter that starts at `Run.hpp:1358`. Node *i*'s first populate requires its own thread (`Run.hpp:1712`) to clear `now_tick - last_seen_tick < slow_path_interval` (`Run.hpp:1762`). Two independent counters, independently started, producer first.

**I confirmed the producer's cadence block contains NO rebuild.** I read `Async.hpp:302-509` end-to-end: it does cfg hot-reload, kill-resets, `EventLoop_KillSwitchEvaluate`, periodic snapshot save, and the GUI publish. No `EventLoop_RebuildOneCore`, no `SLOW_PATH_GATE_AUTOPOPULATE_PER_NODE`. The per-node rebuild lives *entirely* on the per-node slow threads.

**Window-widening paths I found** (this is what your S-4 refute-spot #1 asked for, and it goes the *upgrade* direction):
- `Run.hpp:1746` — a node in `paused_engines_mask` `continue`s **before** the rebuild. Paused from the GUI ⇒ window is indefinite, not milliseconds.
- `Run.hpp:1754` — `paper_reset_in_progress` park, same shape.
- `Run.hpp:1781` — `if (state.nodes[c].strategy_id == STRATEGY_NONE) continue;` ⇒ a STRATEGY_NONE node's `gate_state` is **never** populated, for the process lifetime. *(Benign today: the `:597` read is gated on `strategy_id == STRATEGY_ML` at `ShardedSnapshot.hpp:575`. Consistent — I checked.)*

**Refuting my own escalation, honestly:** the lazy-rebuild early `return` at `ControllerEventLoop.hpp:2669` sits *before* the populate at `:2685`, which looked like a second hole. It is not: that path requires `sst_lazy->us_at_last_rebuild != 0 && !FPN_IsZero(sst_lazy->price_at_last_rebuild)` (`:2646-2648`), both set only by a prior full rebuild. The first cycle always populates. **Hypothesis refuted by the code.**

### 3.4 The populate ASSIGNS, so contamination is bounded

`CoreFrameworks/SlowPathGateRegistry.hpp:212-219` — `uint16_t _new_flags = 0; … (state).flags = _new_flags;` — a **whole-value assign**, not an OR-into-existing. Probe-confirmed: `0xAAAA → 0x0000` after one pass. The poison is fully overwritten at the first populate; no permanent corruption. This is the fact that bounds the blast radius to the boot window.

### 3.5 Blast radius — **I downgrade S-4's "MED live effect" to effectively ZERO today, and I can prove it**

S-4 called this "observability, not capital." It is **less than that**. The single consumer chain is:

```
ShardedSnapshot.hpp:597-599 → STATE_FLAG_SET(snap->per_node[i], LADDER_BOTTOM_HIT)
```

**`LADDER_BOTTOM_HIT` is SET AND NEVER READ.** Exhaustive tree scan (excluding `build*`, `plans/`) returns exactly 4 hits: the registry row (`MemHeaders/PerNodeStateFlagsRegistry.hpp:95`), the two `ShardedSnapshot.hpp:595/599` lines, and a comment at `Strategies/StrategyParameters.hpp:63`. There is **no** `STATE_FLAG_IS_SET(..., LADDER_BOTTOM_HIT)` anywhere, and **no generic `FOREACH_PER_NODE_STATE_FLAG` walker** in any GUI/TUI renderer that could read it indirectly (I checked — the only expansions are the registry's own bit/mask/count generators at `:115/:122/:131`, plus the H15 enrollment row at `CoreFrameworks/MetaRegistry.hpp:83`).

So the indeterminate read today writes into a snapshot bit that nothing consumes. **This is a set-but-never-read snapshot-bit orphan** — a Class-44-adjacent finding in its own right (see §5).

**The in-band ML readers are ordering-safe, and I verified the exclusivity S-4 only asserted.** `ml_ctx.gate_state` is wired at exactly ONE site — `ControllerEventLoop.hpp:3003`, `(void*)&state->nodes[slot].gate_state`, same `slot`, in the same function body **downstream** of the `:2685` populate. There is no second `mctx.gate_state =` anywhere in the tree. `MASK_LADDER_ACTIVE` / `MASK_CONFIDENCE_ENABLED` / `MASK_RIDGE_*` **do** gate entry sizing (`StrategyParameters.hpp:1201+`) — but they are unreachable ahead of the populate. **Your S-4 refute-spot #2 (a construction path that skips the populate) is REFUTED: no such path exists.** The backtest driver never reaches this — `Backtest/BacktestSharded.hpp:876` calls `TUI_CopySnapshotSharded` once at end-of-run, after all cycles, single-threaded.

### 3.6 Severity

**HIGH structural / LOW live-today / LATENT-HIGH.** Two independent things currently mask it — the poison may or may not land, and the one consumer bit has no reader. Both are accidents, neither is a guarantee, and either can be removed by an unrelated edit. `gate_state` sits at **offset 0 of the HOT cluster by deliberate design** (`ControllerEventLoop.hpp:304, 318-329, 666`), which is exactly the field a future reader is most likely to be added to.

**It is also the only one of my seven with zero test coverage:** `rg gate_state tests/` returns one comment (`tests/controller_test.cpp:20685`) and one unrelated golden-header include. No test exercises its lifecycle.

---

## 4. Per-field evidence

### 4.1 `core` — `ExecutionCore<64>*` @ 8 — **SAFE-UNPERSISTED / RUNTIME_POINTER**

- **Writes (2):** `MemHeaders/NodeCtxInitRegistry.hpp:100` (Layer 1, `nullptr`) · `CoreFrameworks/ControllerEventLoop.hpp:1275` `state->nodes[slot].core = core` (`EventLoopState_RegisterCore`, boot, from `EngineCommon.hpp:282`).
- **Reads (16):** `ShardedSnapshotPersist.hpp:510` · `ShardedBacktestDriver.hpp:243` · `EngineSharded/SlowPath.hpp:172-174` · `EngineCommon.hpp:645, 809` · `EngineSharded/Async.hpp:827` · `ShardedSnapshot.hpp:238, 405, 541` · `ControllerEventLoop.hpp:2324, 3487-3488, 3554, 3620, 4236`.
- **Read-before-write on warm restart?** **No.** The snapshot-load read (`ShardedSnapshotPersist.hpp:510`) is at Run.hpp:1069, *after* RegisterCore (~:1000), and is `if (!node_ptr) continue`-guarded (`:511`).
- **Mechanism:** the pointee is `static ExecutionCore<F> nodes[MAX_EXECUTION_NODES]` — process-lifetime storage, so `core` can never dangle within a process.
- **Robustness note (not a defect):** `EngineCommon.hpp:809` `ExecutionCore_SetPermission(state.nodes[c].core, 1)` is **unguarded**, and `ExecutionCore.hpp:370-371` dereferences without a null check. Safe by boot ordering (the slow thread for `c` only exists because BootPerCore registered `c`), but it is inconsistent with the guarded style at `ControllerEventLoop.hpp:3555`.

### 4.2 `slow_state` — `NodeSlowState<64>*` @ 16 — **SAFE-UNPERSISTED / RUNTIME_POINTER**

- **Writes (3):** `NodeCtxInitRegistry.hpp:229/233` (`_alloc_and_init_slow_state` — arena placement-new, `new` fallback, then `NodeSlowState_Init` at `:235`), invoked as **Layer 4** at `:322` · `ControllerEventLoop.hpp:1228` (`= nullptr` in `EventLoopState_Free`, shutdown only).
- **Reads:** `ShardedSnapshot.hpp:448-449` (guarded) · `EngineSharded/Async.hpp:505-506` (guarded) · `EngineCommon.hpp:462, 596` · `ControllerEventLoop.hpp:2517-2519` (guarded `if (!sst) return;`), `:2556-2557` (guarded), `:2645-2646` (guarded), `:3509`.
- **Read-before-write?** **No** — Layer 4 runs for all 16 slots at `ControllerEventLoop.hpp:1143`, before every read site.
- **Probe-confirmed:** post-`Init`, `slow_state = 0x7f1b4c365040` (a real allocation), not the poison.
- **Robustness note:** `EngineCommon.hpp:462` (`&state.nodes[c].slow_state->rolling_short`) and `:596`+`:803` (`sst->rolling_short.count`) are **unguarded derefs**. Safe by boot ordering; inconsistent with the guarded style elsewhere. Same class as §4.1.

### 4.3 `model_handle` — `void*` @ 24 — **SAFE-UNPERSISTED / RUNTIME_POINTER**

- **Writes (3):** `NodeCtxInitRegistry.hpp:101` (Layer 1, `nullptr`) · `EngineCommon.hpp:343` `= zoo_ptr` (only when `strategy == STRATEGY_ML && zoo_ptr && ezoo_ptr && loaded`) · `EngineCommon.hpp:350` `= NULL` (strict-verify unload) · hot-swap via `HotSwap.hpp:291` (atomic swap of the handle slot).
- **Note worth carrying:** when `loaded == 0` the ML branch does **not** write `model_handle` at all — it relies on Layer 1's `nullptr`. Correct today because Layer 1 always precedes it; it is a dependency worth naming in the exemption reason rather than leaving implicit.
- **Reads:** `LiveReadiness.hpp:117` (**capital-relevant** — `check_all_ml_cores_have_model` gates live boot), `:131,143,155,167,179` · `ShardedSnapshot.hpp:579` (guarded) · `ControllerEventLoop.hpp:2947` · `Run.hpp:1800, 1862, 1979` · `StrategyParameters.hpp:903`.
- All zoo derefs route through `aggregate_zoo_drift`, which null-guards at `LiveReadiness.hpp:62`. Verified.
- **Why unpersisted is correct:** the handle points into caller-scope `static NodeModelZoo<F> ml_zoos[16]`; the model itself is re-loaded from disk per `node_model_dir`/`node_model_path` cfg at every boot (`EngineCommon.hpp:314/327`). Persisting the pointer would be a use-after-restart.

### 4.4 `ensemble_handle` — `void*` @ 32 — **SAFE-UNPERSISTED / RUNTIME_POINTER**

- **Writes (2 + hot-swap):** `NodeCtxInitRegistry.hpp:102` (Layer 1) · `EngineCommon.hpp:394` (`= ezoo_ptr` on active ensemble) / `:397` (`= nullptr`) · `HotSwap.hpp:168` (ACQ_REL swap).
- **Reads:** `Run.hpp:1042, 1872, 1914, 2323` · `EngineCommon.hpp:415, 711` · `ShardedSnapshot.hpp:641, 721, 753` · `ControllerEventLoop.hpp:1937-1938, 1979-1980, 2948` · `BacktestSharded.hpp:315` · `HotSwap.hpp:88`. All nullptr-checked or nullptr-safe by contract (`ControllerEventLoop.hpp:2948` comment: *"nullptr-safe; single-zoo when null"*).
- **Same reasoning as §4.3.** Additionally, the boot path is strictly ordered before the `Run.hpp:1042` read.

### 4.5 `pending_params` — `GateParameters<64>` @ 1920 — **SAFE-UNPERSISTED / DERIVED_EACH_PASS (strongest case)**

Three independent layers make this one airtight:

1. **Boot-initialized:** `NodeCtxInitRegistry.hpp:308` `GateParameters_Init(&_autop_ctx.pending_params)` → all `Money` fields `Money_Zero()`, `strategy_id = STRATEGY_NONE`, `flags = 0` (`CoreFrameworks/GateParameters.hpp:293-305`). Probe-confirmed: `flags 0x000000AA → 0x00000000`, `strategy_id 170 → 255`.
2. **Re-derived every full rebuild:** written by `Strategy_BuildParameters` at `ControllerEventLoop.hpp:3066` and the post-dispatch block `:3090-3221`, staged via `EventLoop_StageParameters` `:2367`.
3. **The consumer is gated on the derive having happened.** `EventLoop_PushParameters` (`ControllerEventLoop.hpp:3552-3563`) pushes **only** when `NODE_STATE_FLAG_IS_SET(…, DIRTY)`. `node_state_flags` is init'd to `0` (`NodeCtxInitRegistry.hpp:107`), and `DIRTY` is set only by a rebuild that wrote `pending_params`. So the all-zeros boot value can never reach the hot path's seqlock.

**Not wire-relevant:** `gen_code_map.sh --byte-context GateParameters` returns **zero** `sizeof(GateParameters…)` sites and no GateParameters-specific `fwrite`/`memcmp`/HMAC op. `GateParameters` is purely in-memory runtime state.

**And persisting it would be actively wrong**: it holds absolute price thresholds derived from a prior session's price level. Restored positions do *not* depend on it — `ShardedSnapshotPersist.hpp:553-563` re-arms `live_tp`/`live_sl` **directly on the ExecutionCore**, recomputed from `entry × (1 ± pct)` using the per-node per-strategy resolved pct (`:540-551`, the `.E.0.10` A1/H22 fix). Exit gates are armed without touching `pending_params` at all.

### 4.6 `strategy_state` — `void*` @ 40 — **SAFE-UNPERSISTED, but `RUNTIME_POINTER` is the wrong reason**

**This is the field where the obvious exemption reason is true-but-insufficient, and it is the closest thing on this shard to the `ic.actuals` shape.**

- **Writes:** `NodeCtxInitRegistry.hpp:103` (Layer 1, `nullptr`) · `Strategies/StrategyLifecycle.hpp:150` (`ctx.strategy_state = s` per `FOREACH_STRATEGY` row) / `:159` (`nullptr` for AUTO/NONE) · `:501` (`FreePerCore`) · `ControllerEventLoop.hpp:1240` (leak-guard null in `EventLoopState_Free`).
- **Reads:** `StrategyLifecycle.hpp:124` (idempotency check in `InitPerCore`), `:209, 233, 255, 391, 401, 447, 463-464` (all null-guarded) · `ControllerEventLoop.hpp:3069` (passed to the dispatcher; typed-cast per branch at `StrategyParameters.hpp:1834/1839/1844/1904`).
- **Read-before-write?** **No.** Layer 1 nulls it before `Strategy_InitPerCore` (`EngineCommon.hpp:459-463`) reads it at `StrategyLifecycle.hpp:124`.

**The gap the pointer-shaped reason hides.** The persist registry documents at length (`ShardedSnapshotPersist.hpp:422-460`) why `strategy_state_kind` is `NO_COMMIT`. Nothing documents what happens to the **pointee**. It is not nothing:

`MeanReversionState<F>` (`Strategies/MeanReversion.hpp:62-78`, **720B**) holds
`feeder` (its **own** `RegressionFeederX<F>` P&L regression ring), `ror` (RORRegressor), `live_offset_pct` / `live_vol_mult` / `live_stddev_mult` (the **adapted** filter values), `buy_conds_initial` (the max-shift clamp anchor), `last_regression` + `has_regression`, `price_feeder`.

**All of it is lost on warm restart** and reset to the cfg seed (`Strategy_SeedFromCfg`, `StrategyLifecycle.hpp:95-103`) plus `init_fn(s, rolling, …)` (`:149`) where `rolling` is the *freshly-zeroed* `rolling_short`. And `MeanReversion_Adapt` (`MeanReversion.hpp:140+`) **accumulates** — the idle-squeeze block mutates `live_offset_pct` toward `offset_min` cumulatively; it does not recompute from scratch.

So there is a genuine asymmetry with the wire: `NodeContext::pnl_feeder` (the D10 controller-level feeder, `ControllerEventLoop.hpp:548`) **is** persisted (`NodeCtxPersistRegistry.hpp:102`), while `MeanReversionState::feeder` (the strategy-internal one) is not. Two sibling accumulators, one on the wire and one off it.

**Why it is nonetheless SAFE — and this is the mechanism the exemption row must cite, not "it's a pointer":**

1. Unlike the IC case, the two feeders are **not lockstep-paired**. Losing the strategy-internal one is a *reset to defaults*, not a *corruption*. It reproduces exactly the cold-boot state, which is a state the system is already designed to trade out of.
2. **The permission warmup gate makes it unreachable for entries.** `ExecutionCore_Init` sets `permission = 0` (`ExecutionCore.hpp:281`). It is granted only at `EngineCommon.hpp:803-809`, requiring `sst->rolling_short.count >= min_warmup_samples` (default 64). `rolling_short` is pushed **per slow-path cycle**, not per tick, so that is **64 slow-path cycles** post-restart — during every one of which `Strategy_AdaptPerCore` runs unconditionally (`ControllerEventLoop.hpp:3048`, before `BuildParameters`). The adaptive state re-converges before a single entry can fire.
3. Verified at code level that permission gates **entries only**: `ExecutionCore.hpp:603` `can_enter = (~any_active & perm & bg_fires)`; `:604-605` `can_exit_a/can_exit_b` do **not** consult `perm`. So restored positions exit at their re-armed TP/SL immediately and independently of any strategy state.

**Recommendation:** this row's exemption must not read `RUNTIME_POINTER`. That reason is true of the pointer and silent about the 720B of accumulated adaptation behind it — the exact failure mode you asked me to hunt. Propose `POINTEE_STATE_REDERIVED(warmup-gated)` citing `EngineCommon.hpp:803-809` + `ControllerEventLoop.hpp:3048` + `ExecutionCore.hpp:603`.

---

## 5. Things I found that you did not ask about

| # | Finding | Severity |
|---|---|---|
| **X-1** | **`LADDER_BOTTOM_HIT` is a set-but-never-read snapshot bit.** Set at `ShardedSnapshot.hpp:599`; zero readers tree-wide; no generic registry walker. Class-44-adjacent orphan (`scan_class_44_cfg_orphan.py` covers cfg flags, not snapshot bits — a coverage gap in the orphan-scanner family). It is also the *only* thing making P1-1's live impact ~zero, i.e. **a latent bug is being masked by a dead feature**. | MED |
| **X-2** | **Stale code-fact comment (§2.5 of my arming).** `CoreFrameworks/SlowPathGateRegistry.hpp:263-266`: *"per-core slow-path thread is the single writer + reader for SlowPathGateState … No atomics needed … GUI display reads PerNodeSnap, not gate_state directly."* **Both clauses are false as of `ShardedSnapshot.hpp:597`**, which reads `gate_state.flags` from the **producer** thread with no synchronization. Suggested wording: *"Writer: the owning per-core slow-path thread. Readers: same thread in-band (via `mctx->gate_state`), PLUS the snapshot publisher on the producer thread (`ShardedSnapshot.hpp:597`) — an unsynchronized cross-thread read of a `uint16_t` accepted as benign-racy for display; it is NOT single-reader."* This stale comment is very likely *why* the missing init survived — it told every subsequent reader the field was single-threaded. | MED (doc) |
| **X-3** | **Zero test coverage of `gate_state`'s lifecycle.** `rg gate_state tests/` → one comment at `tests/controller_test.cpp:20685`. No test constructs a poisoned `EventLoopState` and asserts post-`Init` field state. A `NODE_CTX_INIT_AUTOPOPULATE` completeness test (poison → Init → assert every member established) would have caught this and would mechanically enforce your CI guard's INIT partition. | MED |
| **X-4** | **Guard-style inconsistency on `slow_state`/`core` derefs.** Guarded: `ControllerEventLoop.hpp:2518-2519, 2556, 2645-2646, 3555`; `ShardedSnapshot.hpp:448`; `Async.hpp:505-506`; `ShardedBacktestDriver.hpp:244`. Unguarded: `EngineCommon.hpp:462, 596→803, 809`. All safe by boot ordering today. Not a defect — but it means a reader cannot tell from the call site which invariant is load-bearing. | LOW |
| **X-5** | **`ShardedSnapshot_Load` is paper-mode-only** (`Run.hpp:1064` `if (!live_trading)`). Live boot reconciles against exchange truth instead. Worth stating explicitly in the guard's framing: **the persist-exemption question is a PAPER-mode question**; live warm-restart correctness rides an entirely different mechanism (`tt::Reconcile_Decide`) that this guard does not cover. If the guard's rationale text implies "the wire is how state survives a restart," that is only half true. | Framing |

---

## 6. Recommendation on your CI guard's exemption vocabulary

Your four candidate categories are sound but, as written, **two of them can be satisfied by a reason that is true and still wrong**. Concretely:

1. **`RUNTIME_POINTER` must carry the re-establishment SITE, not just the type-shape.** "It's a pointer" is a property of the *declaration*; it is not evidence about the *runtime*. Require `RUNTIME_POINTER(<file:line where it is re-established>)`. Fields 2-5 satisfy this trivially; field 6 does not.

2. **A pointer's exemption does not cover its pointee.** `strategy_state` is the worked proof (§4.6). Add a distinct category — `POINTEE_STATE_REDERIVED(<mechanism site>)` — and make it **mandatory whenever the pointee is a struct with accumulator fields**. Mechanically detectable: if the pointee type contains a `RegressionFeederX` / `Rolling*` / `*Regressor` / any `_count`+ring pair, `RUNTIME_POINTER` alone should RED. This is the generalization of the `ic.actuals` lesson to the pointer axis.

3. **`DERIVED_EACH_PASS` must answer "what reads it before the first derive?"** This is the single question that separates `pending_params` (**PASS** — the `DIRTY` gate at `ControllerEventLoop.hpp:3553` structurally prevents pre-derive consumption) from `gate_state` (**FAIL** — an unsynchronized cross-thread reader exists with no gate). Without this clause the guard would accept `gate_state` as `DERIVED_EACH_PASS` and be **vacuously green on the one real defect on this shard** — exactly the Class-51 shape. Propose the row schema carry a required `pre_derive_reader:` field: either `none` (with the enumeration) or `<gated-by file:line>`.

4. **S-4's HAZ-S4-1 is confirmed and I would strengthen it:** a per-partition exemption reason **does not transfer across partitions**. `gate_state`'s *persist* rationale ("cfg-derived cache, repopulated every slow pass") is **correct**, and it is **silent about the first pass** — which is the INIT partition's question. If the guard shares one vocabulary across INIT/SUMMARY/PERSIST, `gate_state` gets waved through on a true statement. Recommend the reason string be **partition-scoped by construction** (the row key includes the partition), not a shared enum.

5. **`gate_state` fits none of the four categories.** That is the guard's first real catch. Propose it be recorded not as an exemption but as `UNESTABLISHED_UNTIL_FIRST_PASS` — a category the guard treats as **RED, never a valid exemption**.

---

## 7. Where I would push hardest if I were the adversary — for the paired A-class

1. **Attack the frame-layout question I could not settle.** I proved (probe 2) that fresh stack ⇒ `0x0000` and dirty stack ⇒ poison survives, and I measured `sizeof(ControllerConfig<64>) = 53056` vs `sizeof(EventLoopState<64>) = 272640`. I did **not** determine where `state` sits inside `EngineSharded_Run`'s `-O3` frame, nor where `nodes[]` sits inside `EventLoopState`. **Settle it:** disassemble the shipped `engine_gui`, compute `%rsp`-relative offset of `state`, add `offsetof(EventLoopState<64>, nodes)`, and compare against the ~53KB pre-dirtied top band. If `gate_state` provably lands on always-fresh pages in every shipping build, P1-1 downgrades to hygiene *today* (it stays a latent defect). If it lands in the dirty band, it upgrades.

2. **Attack my "LADDER_BOTTOM_HIT has no reader" claim.** I searched engine source only. **Try to break it:** the GUI's ImGui render loop, `foxml_suite`, any `TUISnapshot` consumer that memcmp's/serializes `per_node[i].state_flags` wholesale, or a panel that renders the flags word numerically. One reader anywhere flips P1-1 from LOW-live to MED/HIGH-live immediately.

3. **Attack my "in-band ML readers are ordering-safe" conclusion.** I found exactly one `mctx.gate_state =` site (`ControllerEventLoop.hpp:3003`) and confirmed it is downstream of `:2685` in the same body. **Try to break it:** an `MLBuildContext` that is *copied* or *retained* across cycles; a `dispatch_ctx` aliased into a strategy's own state; any path where `EventLoop_RebuildOneCore` is invoked with a `slot` different from the one whose `gate_state` gets wired. If any exists, this becomes a capital-path finding, because `MASK_LADDER_ACTIVE`/`MASK_CONFIDENCE_ENABLED`/`MASK_RIDGE_*` gate entry sizing.

4. **Attack my `strategy_state` SAFE verdict — this is the softest of my seven.** My acquittal rests on (a) not-lockstep-paired and (b) the 64-cycle permission warmup. **Try to break (b):** find a path where permission is granted without `rolling_short.count >= min_warmup_samples` — a warm-restart shortcut, a cfg `min_warmup_samples = 0` (note: `EngineCommon.hpp:801-802` falls back to 64 only when the cfg value is `> 0`… verify what happens at exactly `0`), an operator override, or `Strategy_ExitAdjustPerCore`/`Strategy_WriteRatchetSL` reading `strategy_state` on an **exit** path (which is *not* permission-gated per `ExecutionCore.hpp:604-605`). An exit-side read of cold-reset strategy state on a snapshot-restored position would be a genuine capital finding and would invert my verdict. I checked `StrategyLifecycle.hpp:391` (`ExitAdjust`) null-guards, but I did **not** audit whether its *output* differs materially between warm and cold strategy state.

5. **Attack the guard-design recommendation in §6.2.** I claim a pointee-accumulator detector is mechanically feasible. Push on whether that produces false positives at scale (e.g. `MLStrategyState`, `EmaCrossState`, `SimpleDipState` — I only examined `MeanReversionState` in depth and inferred the class from `Strategy_SeedFromCfg`'s three overloads at `StrategyLifecycle.hpp:76-103`). **UNVERIFIED:** I did not enumerate the accumulator content of `EmaCrossState`, `MomentumState`, `SimpleDipState`, `MLStrategyState`. Per M9 (enumerate the set before a categorical claim), my `strategy_state` verdict generalizes from ONE member of a five-member set and should be read as such.

---

## 8. Hypotheses of mine the code refuted

- **"The container might be value-initialized or memset somewhere, making S-4 moot."** Refuted — no `memset`/`calloc`/`{}` on either container site (`Run.hpp:821`, `BacktestSharded.hpp:225`), probe-confirmed the poison survives `EventLoopState_Init`.
- **"The lazy-rebuild early return at `:2669` is a second gate_state hole."** Refuted — it requires a prior full rebuild (`:2646-2648`), so it can never precede the first populate.
- **"The autopopulate might OR into the existing flags, making the poison permanent."** Refuted — `SlowPathGateRegistry.hpp:215-217` is a whole-value assign; probe-confirmed `0xAAAA → 0x0000`.
- **"S-4's MED live impact is right."** Refuted downward — the sole consumer bit `LADDER_BOTTOM_HIT` has no reader anywhere.
- **"The backtest driver constructs `ml_ctx` without the populate" (S-4 refute-spot #2).** Refuted — one wiring site only, always downstream; backtest publishes once at end-of-run.
- **"`gate_state` is always garbage in production."** Refuted (probe 2) — on a fresh stack it reads `0x0000`. The defect is the **absence of a guarantee**, not an observed garbage value. I flag this because over-claiming here is exactly the failure mode that would get the finding dismissed.
