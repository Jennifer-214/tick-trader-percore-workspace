# Phase A — Slow-Path Audit + Decomposition Map

**Created:** 2026-04-28
**Goal:** before any thread changes, categorize every operation in the current centralized slow-path body as **per-core** (move to per-core slow-path thread) vs **shared** (stays on producer thread / orchestrator). Output: a concrete blueprint for Phase B.

**Scope:** read-only investigation. No code changes. Output is this document — annotate file/line refs for every operation.

---

## Current architecture (corrected)

The slow-path is **inside the producer thread's `fan_out` lambda**, not on a separate controller. `EngineSharded.hpp` lines 786-1180+:

```
Producer thread:
  per-tick loop:
    fan tick → N hot-path rings           [shared write — producer is sole writer]
    ema_price update                       [shared, sequential]
    TickRecorder_Push, CandleAccumulator   [shared writers, GUI consumers]

    if (slow_path_counter >= interval):
      // SLOW-PATH BODY — currently on producer thread
      [BLOCK BELOW — categorized per-section]
```

Hot-path threads (per-core, pinned) consume tick rings. They DON'T touch slow-path state directly — read gate parameters via seqlock.

---

## Slow-path body decomposition

| # | Section | File:Lines | Per-core / Shared | Why |
|---|---|---|---|---|
| 1 | RollingStats_Push (×4: short/long/medium/baseline) | `EngineSharded.hpp:842-853` | **Shared** | Single producer writer makes sense; per-core slow-path reads. Avoids 4× cache thrash. |
| 2 | CumDelta_Push, TickRate_Push | `~854-855` | **Shared** | Same — producer-fed market state. |
| 3 | RORRegressor_Push (regime_ror) | `~856-866` | **Shared** | Single time-series, market-wide. |
| 4 | FlowState_Push, LargeTradeState_Push | `~867-869` | **Shared** | Market-wide flow signals. |
| 5 | BookImbHistory_Push, SpreadState_Push | `~1058-1066` | **Shared** | Depth-driven, single producer feed. |
| 6 | Strategy swap drainer (loop over cores) | `~876-925` | **Per-core** (mostly) — orchestrator coordinates the request, but the apply-on-position-close check is per-core | Each core decides when its own swap is safe. Could move into per-core slow-path. |
| 7 | Drag-TP/SL drainer | `~927-...` | **Per-core** | Mutates only the affected core's position. |
| 8 | Manual close drainer | `~...` | **Per-core** | Same — affects only the targeted core. |
| 9 | Reset Paper handler | `~1156-1204` | **Orchestrator** | Whole-engine state reset; serializes all cores. |
| 10 | **EventLoop_RebuildAllParameters** | `EngineSharded.hpp:1067` calls `ControllerEventLoop.hpp:~1010` | **Per-core** (loops over cores internally) | This is the BIG one — strategy dispatch, regime classify, ConfidenceScorer, SL cooldown decrement, dirty flag set. ALL per-core work. |
| 11 | EventLoop_PushParameters (seqlock writes) | `~1093` | **Per-core** | Each core's parameters published via its own seqlock. |
| 12 | Snapshot save (periodic) | `~1087-1092` | **Orchestrator** | Whole-engine state serialization. |
| 13 | EventLoop_KillSwitchEvaluate | `~1105` | **Per-core** | Per-core kill switch state; no inter-core dependencies. |
| 14 | Warmup permission grant | `~1118-1126` | **Per-core** | `ExecutionCore_SetPermission(&cores[c], 1)` — per-core call. |
| 15 | EventLoop_TimeExit | `~1136` | **Per-core** | Walks per-core state, force-closes stale positions per core. |
| 16 | EventLoop_TrailingSLRatchet | `~1137` | **Per-core** | Same — per-core trailing logic. |
| 17 | GUI snapshot publish (TUISnapshot) | `~1140+` | **Orchestrator** | Aggregates per-core state into GUI-readable form. Single writer. |

---

## Decomposition summary

**Stays on producer thread (or moves to a "data feeder" if separate):**
- Tick fan-out to N rings
- EMA price update
- RollingStats_Push (×4) + Cum/TickRate/ROR/Flow/LargeTrade/BookImb/Spread pushes
- TickRecorder + CandleAccumulator pushes

**Moves to per-core slow-path thread:**
- Per-core strategy dispatch (Strategy_BuildParameters via RebuildAllParameters → split per core)
- Regime classify + AdjustPositions (currently per-AUTO-core inside RebuildAllParameters)
- ConfidenceScorer compute
- Per-core SL cooldown / idle cycle decrement
- EventLoop_PushParameters for that core
- EventLoop_KillSwitchEvaluate for that core
- Warmup permission grant for that core
- EventLoop_TimeExit for that core
- EventLoop_TrailingSLRatchet for that core
- Per-core swap-pending check + apply
- Per-core drag-TP/SL apply
- Per-core manual-close apply

**Stays on orchestrator (= rename of "producer" thread):**
- Tick fan-out (already there)
- Shared market-state pushes (already there)
- Reset Paper handler (whole-engine)
- Snapshot save (periodic)
- GUI snapshot publish (aggregates per-core state)
- Lifecycle (boot, shutdown, paper-reset coordination)

**Hot path** (no change):
- Read gate parameters via seqlock
- BG/SG evaluate (branchless, per-tick, ~30-50ns)
- Push TradeEvent to OMS ring on entry/exit decision

---

## Synchronization map (post-migration)

```
                     Producer (orchestrator)
                          ─ writes ─▶
        ┌─────────────────────────────────┐
        │  Shared market state (atomic)   │
        │  - RollingStats × 4             │
        │  - regime_ror, flow_state, etc. │
        │  - depth snapshot               │
        │  - ema_price (atomic store)     │
        └─────────────────────────────────┘
                          ─ reads ─▶
                       (acquire-load)
        ┌─────────┐  ┌─────────┐  ┌─────────┐
        │ Slow 0  │  │ Slow 1  │  │ Slow N  │
        │ (per-   │  │ (per-   │  │ (per-   │
        │  core)  │  │  core)  │  │  core)  │
        └────┬────┘  └────┬────┘  └────┬────┘
             │ seqlock    │ seqlock    │ seqlock
             ▼            ▼            ▼
        ┌─────────┐  ┌─────────┐  ┌─────────┐
        │ Hot 0   │  │ Hot 1   │  │ Hot N   │
        └────┬────┘  └────┬────┘  └────┬────┘
             │            │            │
             └────────────┼────────────┘
                          ▼
                   ┌────────────┐
                   │  TradeEvent│
                   │  SPSC × N  │
                   └─────┬──────┘
                         ▼
                   ┌────────────┐
                   │  Drainer   │  ← single thread
                   │  thread    │  ← OMS_Tick + DrainPostFill
                   └────────────┘
```

Key sync rules:
- **Producer → slow-path reads**: shared state is read-mostly. Producer writes happen in single thread (no race between producers). Slow-paths read with `std::memory_order_acquire`.
- **Slow-path → hot-path**: existing seqlock unchanged.
- **Slow-path → drainer (OMS commands)**: per-core SPSC queue (existing `core.tick_ring` is hot-path bound; need a separate `core.command_ring` for slow-path → drainer or have slow-path call OMS_Submit directly with internal locking).

---

## Risk register (Phase A discoveries)

| Risk | Severity | Mitigation |
|---|---|---|
| `EventLoop_RebuildAllParameters` is monolithic — splits over multiple cores internally | MEDIUM | Phase B will refactor: extract `EventLoop_RebuildOneCore(state, core_id, ...)` that the per-core slow-path calls. Centralized path keeps calling the loop wrapper. |
| Producer thread loses slow-path = becomes pure tick fan-out + market-state feeder | LOW | Rename producer thread to "data feeder" or keep "producer" for clarity. Architecturally cleaner. |
| Drag-TP/SL + manual-close drainers currently iterate all cores looking for requests | LOW | Per-core slow-path checks only its own request slot. Cleanup. |
| Warmup permission grant currently checks `rolling_short.count >= min_samples` once per cycle | LOW | Per-core slow-path makes the same check. |
| Reset Paper + snapshot save touch all-cores state — must serialize across slow-paths | MEDIUM | Orchestrator pauses/coordinates slow-paths during reset. Use a `std::atomic<bool> reset_in_progress` checked at slow-path top. |
| Drainer thread currently consumes OMS, calls EventLoop_DrainPostFill which mutates per-core state | HIGH | DrainPostFill writes to `state.cores[c]` fields (core_realized, core_wins, etc.) — these are also written by per-core slow-paths (e.g. partner_pending). Need to decide: is per-core CoreContext owned by slow-path or drainer? **Likely**: drainer mutates only on fill; slow-path mutates other fields; SAME thread = no race. But verify carefully. |
| Snapshot version compatibility | LOW | No struct layout changes in Phase A. |

---

## Open questions (decide before Phase B starts)

1. **Where does `EventLoop_DrainPostFill` run?** Currently on drainer thread. If per-core slow-path also touches `CoreContext.partner_pending_pnl`, both threads write to the same struct. Either:
   - (a) Move DrainPostFill into per-core slow-path (slow-path drains its own core's mask) — cleaner, removes drainer thread for sharded mode
   - (b) Keep DrainPostFill on drainer; per-core slow-path doesn't touch fields drainer owns. Document the partition.
   - **Recommend (a)** — lets drainer thread go away, slow-path owns ALL per-core state mutation.

2. **OMS submission**: per-core slow-path submits orders. Today there's one OMS thread that consumes ring + calls Submit. With per-core slow-path:
   - (a) Per-core slow-path calls `OrderManager_Submit` directly (OMS becomes thread-safe internally)
   - (b) Per-core slow-path pushes to per-core SPSC; OMS thread drains all rings
   - **Recommend (b)** — keeps OMS single-writer (already established invariant), low overhead.

3. **`EventLoop_RebuildAllParameters` decomposition**: currently builds for ALL cores in one call. Need a `RebuildOneCore(state, core_id, ...)` variant.

4. **Producer thread — keep slow-path counter or move to per-core?** Each per-core slow-path can have its own `slow_path_counter` driven by ticks_produced atomic. Cleaner.

---

## Cross-cutting concerns verified

### Snapshot save/load
- **Save** (`ShardedSnapshot_Save`): currently called from inside slow-path body (`EngineSharded.hpp:~1090`), once per ~1024 slow-path cycles. **Move to orchestrator (producer) thread** — runs periodically there instead. Reads per-core state atomically (or accepts torn reads since save is for paper-mode resume, not live-money critical).
- **Load** (`ShardedSnapshot_Load:709`): runs at BOOT, before any slow-path thread is spawned. No race. Phase B doesn't change this.

### GUI snapshot publish (`TUI_CopySnapshotSharded`)
- Currently called from inside slow-path body in producer thread (`~1140`). With per-core slow-path, producer no longer runs slow-path — needs to reach into per-core state from outside.
- **Plan**: keep on orchestrator (producer) thread. Reads per-core state with relaxed ordering — torn reads of one field are visually irrelevant for display. State fields written by per-core slow-path at low frequency (every poll_interval ticks); orchestrator reads at GUI cadence.
- For persistence (snapshot save), use a brief atomic copy or quiesce one slow-path at a time.

### Shutdown teardown
- Global `g_engine_sharded_shutdown` flag polled by all threads. Adding N slow-path threads = each polls the same flag, exits cleanly. No new mechanism needed.
- Phase B must add: join the N new pthreads in the shutdown sequence after setting the flag.

### Reset Paper across slow-paths
- Reset Paper handler currently in slow-path body (`~1156-1204`) — pauses, zeros per-core state, restarts. With per-core slow-paths running independently, reset must serialize.
- **Plan**: orchestrator detects reset request → atomic `reset_in_progress` flag → each per-core slow-path checks at top of its loop, parks → orchestrator runs the reset → clears flag → slow-paths resume. Standard pause-resume.

### Backtest path equivalence
- `ShardedBacktest_RunTick` is **single-threaded** — runs slow-path body inline via linear `for (int slot = 0; slot < state->registered_count; ++slot)` loop. No threading.
- **`engine_arch` is LIVE-ONLY**. Backtest always uses linear-iteration path. Train-serve parity holds because the per-core slow-path body produces the same EFFECTS per core regardless of execution model.

### Drainer thread interaction (open question now resolved)
- Pre-migration: drainer thread runs `OrderManager_Tick + EventLoop_DrainPostFill`. DrainPostFill writes to `state.cores[c]` fields (core_realized, core_wins, etc.).
- Post-migration: per-core slow-path takes over `EventLoop_DrainPostFill` for its own core. Drainer thread either (a) goes away in `engine_arch=per_core_slow` mode or (b) becomes the OMS_Tick consumer only (per-core slow-paths drain their own slots after OMS tick).
- **Plan**: option (b) — keep drainer as OMS-Tick worker (calls `OrderManager_Tick`); per-core slow-paths drain post-fill state for their own slot via mask check. No race because each core's slot bits are written by exactly one slow-path.

---

## Touch-site count comparison

**Current architecture — per-core iterations to migrate:**
- `EngineSharded.hpp` slow-path body has 7 per-core loops (swap drainer, drag drainer, manual-close drainer, warmup permission, time-exit aggregator, trailing-SL aggregator, GUI publish aggregator)
- `ControllerEventLoop.hpp` has 5 per-core internal loops inside `RebuildAllParameters`, `TimeExit`, `TrailingSLRatchet`, `KillSwitchEvaluate`, `DrainPostFill`

**Post-migration:**
- 7 EngineSharded loops → moved into per-core slow-path body (no loop; one execution per slow-path tick)
- 5 ControllerEventLoop loops → become 5 single-core variants (`RebuildOneCore`, `TimeExitOneCore`, etc.)
- Each helper extracted ONCE; per-core slow-path calls 5 single-core variants

**Net code touch sites for Phase B**: ~12 sites refactored, ~5 new helper functions extracted. Existing callers (centralized path) keep working by calling the loop wrapper that calls the OneCore variant N times.

---

## Phase A deliverable

This document. No code changes.

## Phase B inputs (from this audit)

- The 17 sections classified above
- The 4 open questions answered
- The risk register addressed in B's design

Phase B can now start with a concrete map: each section of the current slow-path body has a known target home (per-core thread / producer / orchestrator / drainer / removed).
