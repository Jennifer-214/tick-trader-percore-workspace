# Phase B — Spawn per-core slow-path threads + extract per-core work

**Created:** 2026-04-28
**Goal:** move slow-path execution from producer thread to N dedicated per-core slow-path threads. Centralized path stays default + intact.

---

## Key insight from Phase A

**Per-core state already exists. We're not duplicating data — we're moving WHO RUNS THE CODE.**

- `state.cores[c]` (CoreContext) — already per-core
- `ExecutionCore<F>` — already per-core
- Seqlock for hot↔slow params — already per-core slot
- Kill switch peak/dd/trip — already per-core
- ConfidenceScorer, regime_state, pnl_feeder — already per-core fields on CoreContext

The migration is **thread re-organization**, not state refactoring. Phase B is much smaller than initial estimate.

---

## Cfg surface

Add ONE field to ControllerConfig:

```cpp
uint32_t engine_arch;  // 0 = ENGINE_ARCH_CENTRALIZED (default), 1 = ENGINE_ARCH_PER_CORE_SLOW
```

```cpp
// in ControllerConfig.hpp
#define ENGINE_ARCH_CENTRALIZED   0
#define ENGINE_ARCH_PER_CORE_SLOW 1
```

Cfg parser (~3 lines added). Default `centralized`. **Live-only setting** — backtest ignores it (always linear iteration per Phase A finding).

---

## Helper extractions

Five existing functions today iterate over all cores. Extract a single-core variant of each. The loop body becomes the helper; the existing function becomes a thin wrapper that calls the helper N times.

### 1. `EventLoop_RebuildAllParameters` → `EventLoop_RebuildOneCore`
- Currently in `ControllerEventLoop.hpp:1025`, ~40-line per-core loop body
- **Pre-loop computation**: `book_imbalance_blocked` (global, computed once before loop). OneCore takes it as a parameter (callers compute and pass it in).
- Extract loop body into `EventLoop_RebuildOneCore(state, core_id, rolling_short, cfg, rolling_long, regime_ror, ema_price, mtm_price, rolling_medium, rolling_baseline, cumdelta, tickrate, rebuild_ts_us, book_imb, book_imb_history, flow_state, large_trade_state, spread_state, current_spread, current_mid_price, book_imbalance_blocked)`
- `RebuildAllParameters` becomes: precompute `book_imbalance_blocked`; `for (slot=0..N) rebuilt += RebuildOneCore(state, slot, ..., book_imbalance_blocked); return rebuilt;`
- Per-core slow-path: precompute `book_imbalance_blocked` locally (one FPN compare, cheap); call `RebuildOneCore(state, my_core_id, ..., book_imbalance_blocked)`

### 2. `EventLoop_TimeExit` → `EventLoop_TimeExitOneCore`
- In `ControllerEventLoop.hpp` line ~1528
- Same pattern: extract per-slot body, wrapper calls in loop

### 3. `EventLoop_TrailingSLRatchet` → `EventLoop_TrailingSLRatchetOneCore`
- In `ControllerEventLoop.hpp` line ~1567
- Same pattern

### 4. `EventLoop_DrainPostFill` → `EventLoop_DrainPostFillOneCore`
- In `ControllerEventLoop.hpp` line ~960
- Currently consumes `oms->last_opened_mask` + `oms->last_closed_mask` for ALL slots
- Per-core variant consumes only the bits matching this core's slots (slot c if partials disabled, slots 2c + 2c+1 if enabled)
- Centralized wrapper calls in loop

### 5. `EventLoop_KillSwitchEvaluate` → `EventLoop_KillSwitchEvaluateOneCore`
- In `ControllerEventLoop.hpp` line ~1778
- Per-core variant evaluates only one core's peak/dd/trip
- Wrapper calls in loop

**Estimated extraction effort: ~3-4 hours.** Each is a lift-and-rename pattern.

---

## Per-core slow-path thread body

```cpp
template <unsigned F>
static void per_core_slow_path_loop(int core_id,
                                     EventLoopState<F>* state,
                                     OrderManagerState<F>* oms,
                                     SharedMarketState<F>* shared,  // RollingStats etc.
                                     const ControllerConfig<F>* cfg,
                                     std::atomic<uint64_t>* ticks_produced,
                                     std::atomic<uint8_t>* shutdown_flag,
                                     std::atomic<uint8_t>* reset_in_progress) {
    int slow_path_counter = 0;
    int interval = (int)cfg->poll_interval;  // Phase D will make this per-core

    while (!shutdown_flag->load(std::memory_order_acquire)) {
        // Park if reset is in progress (orchestrator-coordinated)
        while (reset_in_progress->load(std::memory_order_acquire)) {
            if (shutdown_flag->load(std::memory_order_acquire)) return;
            std::this_thread::yield();
        }

        // Tick-based cadence — wake when enough ticks elapsed
        uint64_t now = ticks_produced->load(std::memory_order_acquire);
        if (now - last_seen_tick < interval) {
            std::this_thread::yield();
            continue;
        }
        last_seen_tick = now;

        // Pick up swap-pending / drag / manual-close requests for THIS core
        process_per_core_requests(core_id, state, oms, shared);

        // Strategy dispatch + gate param rebuild for THIS core
        EventLoop_RebuildOneCore(state, core_id,
                                  shared->rolling_short, cfg, shared->rolling_long,
                                  /* ... */);
        EventLoop_PushParametersOneCore(state, core_id);  // seqlock publish

        // Per-core slow-path duties
        EventLoop_KillSwitchEvaluateOneCore(state, core_id);
        EventLoop_TimeExitOneCore(state, oms, *cfg, now, current_price, core_id);
        EventLoop_TrailingSLRatchetOneCore(state, *cfg, shared->rolling_short, current_price, core_id);

        // Drain fills attributable to this core
        EventLoop_DrainPostFillOneCore(state, oms, cfg->sl_cooldown_cycles, core_id);

        // Warmup permission grant (per-core check)
        if (shared->rolling_short->count >= min_warmup_samples) {
            ExecutionCore_SetPermission(&cores[core_id], 1);
        }
    }
}
```

---

## Orchestrator (renamed producer) responsibilities

Producer thread keeps:
- Tick fan-out to N rings (already there)
- `RollingStats_Push` × 4, flow/depth/EMA pushes (already there)
- TickRecorder + CandleAccumulator pushes (already there)

**Producer GAINS** (moved from inside slow-path body):
- Snapshot save coordination (~once per ~1024 slow-path ticks; orchestrator polls a counter)
- GUI snapshot publish (`TUI_CopySnapshotSharded` from outside slow-path; reads per-core state with relaxed ordering)
- Reset Paper coordination (sets `reset_in_progress` flag, waits for slow-paths to park, runs reset, clears flag)

**Producer LOSES** (moved to per-core slow-paths):
- Per-core RebuildAllParameters body
- Per-core TimeExit / TrailingSL / KillSwitch
- Per-core DrainPostFill
- Per-core swap-pending / drag / manual-close request handling
- Per-core warmup permission grant

---

## Boot sequence with `engine_arch=per_core_slow`

1. Load cfg, init state (existing)
2. Init OMS, register cores (existing)
3. Restore snapshot (existing — happens before any slow-path threads)
4. **NEW**: spawn N pthreads, each running `per_core_slow_path_loop(core_id, ...)`
5. **NEW**: pin each pthread to a chosen CPU (use existing `pthread_setaffinity_np` plumbing)
6. Spawn hot-path threads (existing)
7. Spawn producer thread (existing — but with reduced responsibilities; runs the orchestrator body)
8. Spawn drainer thread (existing — but maybe simpler; per-core slow-paths take over post-fill drain)

---

## Shutdown sequence

1. Set `g_engine_sharded_shutdown = 1` (existing)
2. **NEW**: pthread_join the N slow-path threads
3. pthread_join hot-path threads (existing)
4. Producer + drainer + GUI cleanup (existing)

---

## Synchronization rules

| Data | Writer(s) | Reader(s) | Sync |
|---|---|---|---|
| Tick rings | Producer (single writer per ring) | Hot-paths (single reader per ring) | SPSC, existing |
| Cached params (gate state) | Per-core slow-path (single writer per slot) | Hot-path (single reader per slot) | seqlock, existing |
| `state.cores[c]` (CoreContext) | Per-core slow-path | Producer (GUI snap, relaxed reads) | Relaxed reads OK for display |
| RollingStats × 4 | Producer | Per-core slow-paths (N readers) | Acquire-load on slow-path side |
| Flow / depth / EMA | Producer | Per-core slow-paths | Acquire-load on slow-path side |
| OMS portfolio bitmap | Drainer (existing) | Per-core slow-paths (read), drainer (write) | Atomic reads on slow-path side |
| `g_engine_sharded_shutdown` | Signal handler | All threads | std::atomic, existing |
| `reset_in_progress` (NEW) | Orchestrator | All slow-paths | std::atomic acquire/release |

No new locks. No new atomics on the hot path. All sync mechanisms already exist or are trivial atomic flags.

---

## Open question — DrainPostFill ownership

Currently drainer thread runs `OMS_Tick → DrainPostFill`. Per-core slow-path could take over DrainPostFill, leaving drainer thread to just run `OMS_Tick`.

**Decision: drainer keeps `OMS_Tick`. Per-core slow-paths drain their own slots from the masks.**

Why: `OMS_Tick` walks the order ring (single producer = drainer's existing role). DrainPostFill operates on `oms->last_opened_mask` / `last_closed_mask` which are populated by `HandleFill` inside `OMS_Tick`. Per-core slow-paths read these masks, drain their own bits, clear them.

Race: if two slow-paths read the same mask concurrently and try to drain different bits, that's safe (atomic bit clears). But mask write by drainer + read by slow-paths needs ordering. Use `std::memory_order_acq_rel` on `last_opened_mask` / `last_closed_mask`.

---

## Invariants introduced by Phase B (to add to CLAUDE.md when shipped)

### Per-Core Slow-Path Single-Writer Invariant (NEW, load-bearing)
Each per-core slow-path thread is the SOLE writer of its core's `state.cores[c]` fields except those owned by the drainer thread (`oms->last_*_mask` bits, OMS-fed fields). New code that writes to `state.cores[c].X` must:
1. Verify there are no other writers (existing centralized path is also a writer in `engine_arch=centralized` mode — same per-core invariant holds because centralized runs sequentially, only one logical writer at a time)
2. Document which thread owns the field
3. Not cross-write to `state.cores[other]` from inside per-core slow-path c

### Slow-Path Park During Reset (NEW)
When `reset_in_progress` atomic flag is set, every per-core slow-path must:
1. Park at the next safe point (top of poll loop)
2. Not begin new work until the flag clears
3. Yield CPU while parked (avoid busy-loop)

Orchestrator coordinates by setting the flag, waiting for all slow-paths to acknowledge (counter or barrier), running the reset, then clearing the flag.

### OneCore Helper Identity (NEW, load-bearing)
The 5 OneCore helpers (`RebuildOneCore`, `TimeExitOneCore`, `TrailingSLRatchetOneCore`, `DrainPostFillOneCore`, `KillSwitchEvaluateOneCore`) are the structural train-serve parity guarantee. Three callers MUST hit the same helpers:
- Live `engine_arch=centralized` (wrapper iterates)
- Live `engine_arch=per_core_slow` (per-core thread calls directly)
- Backtest `ShardedBacktest_RunTick` (wrapper iterates)

Adding a new per-core slow-path operation: extract OneCore variant FIRST, then have all three paths call it. Adding logic only to one path = train-serve drift.

---

## Test plan for Phase B

### Existing test coverage (transitive, must stay green)
The 693 existing assertions in `controller_test` cover:
- W/L pairing under partials (v4.7.21)
- Gross win/loss accumulators (v4.7.25)
- Counter atomicity + double-close guard (v4.7.19)
- Backtest parity for DrainPostFill (v4.7.16, v4.7.21 backtest parity)
- ConfidenceScorer single-update-site (v4.7.4)
- Per-core resolved cfg (X-macro from v4.7.24+)

These tests call `EventLoop_DrainPostFill`, `EventLoop_RebuildAllParameters` etc. via the existing wrapper functions — they DON'T spawn engine threads. After helper extraction, the wrappers call OneCore variants in a loop, so existing tests transitively cover the OneCore helpers. **Goal: 693/693 must pass after Phase B's helper extractions, before any thread changes.**

### New tests for Phase B (add as part of the ship)

**1. OneCore identity test** (~10 assertions per helper × 5 = ~50 assertions)
- For each of the 5 OneCore helpers: drive a single core's state, call OneCore directly, verify state mutation matches what the wrapper-loop produces with the same input
- Confirms the wrapper IS exactly N invocations of OneCore — no logic divergence

**2. Spawn + shutdown lifecycle test**
- Init engine with `engine_arch=per_core_slow`, N=2
- Verify 2 slow-path threads spawn, pin to expected CPUs, advance their slow-path counters
- Set shutdown flag, verify all N pthread_join within 1s timeout

**3. Per-core slow-path single-writer invariant test**
- Set up 2 cores running per_core_slow
- Inject simultaneous fill events on both cores
- Verify each core's `core_realized` / `core_wins` / `core_gross_wins` mutate independently with no interleaving
- (Hard to test without thread fuzzing; consider thread sanitizer pass)

**4. Reset Paper park-resume test**
- Spawn slow-paths, let them run for N ticks
- Set `reset_in_progress=1`, verify slow-paths park
- Mutate state in orchestrator (zero balance, etc.), clear flag
- Verify slow-paths resume with new state, no stale reads

**5. Centralized vs per_core_slow parity smoke test**
- Same deterministic tick sequence through both architectures
- Compare per-core state arrays after N ticks: `core_realized`, `core_wins`, `core_losses`, `core_gross_*`, `partner_pending_*`, `core_peak_balance`, `core_dd_pct`, gate parameters
- Must be byte-identical (or FPN-equal modulo timestamp-derived fields)
- (Phase F builds this into a comprehensive parity suite; Phase B adds a smoke version.)

### Threading correctness (non-test verification)

- **Compile with `-fsanitize=thread`** for a stress test build, run synthetic-tick scenario, confirm no warnings
- **Compile with `-fsanitize=address`** to catch use-after-free in shutdown sequence
- These aren't test assertions but they're part of the "before flipping default" gate

### Invariant violation detection (build-time + runtime)

- Add `static_assert` or runtime check at slow-path thread entry: `assert(my_core_id < state->registered_count)`
- Add debug-only check inside OneCore helpers: parameter `core_id` must match the slot being mutated
- These catch programmer errors before they corrupt state

---

## Estimated effort

- Helper extractions: 3-4h
- Per-core slow-path loop function: 2h
- Boot/shutdown wiring + cfg toggle: 1h
- Initial integration test (spawn + run synthetic): 2h
- Parity smoke test: 1h
- Bugfix iteration: 2-4h depending on what surfaces

**Total: 1-1.5 days focused** (revised down from 2 days based on Phase A findings — state is already per-core, so this is purely thread re-org).

---

## What this NOT in Phase B

- **Not** OMS MPSC — that's Phase C (only matters if multiple slow-paths submit orders simultaneously; rare, but Phase C makes it safe)
- **Not** per-core poll cadence — Phase D
- **Not** slow-path latency profiling — Phase E
- **Not** parity flip — Phase F
- **Not** GUI changes — Phase H

Phase B ships the architecture skeleton. Centralized stays default; per_core_slow becomes opt-in.
