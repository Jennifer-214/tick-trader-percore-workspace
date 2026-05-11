# v5.4.0 — Strategy lifecycle restoration + per-core data flow fix + prevention infrastructure

Master plan to restore the strategy lifecycle that was orphaned in the
v4.x sharded port and to build the prevention infrastructure so this
class of regression can't recur silently. Findings documented in
`DOCS/v5.4-regression-postmortem.md` (F1-F10).

This is a multi-phase ship. Each phase has its own pre-tag, validation,
and rollback story. Don't move to phase N+1 until phase N's validation
passes.

## Why this exists

In short: every strategy's per-cadence state-driven logic is dead in
the sharded engine. `_Init`, `_Adapt`, `_BuySignal`, `_ExitAdjust`,
`Regime_AdjustPositions` — none are called in the sharded path. Only
`_BuildParameters` runs, which is stateless and recomputes from rolling
stats every cadence.

Symptoms this caused:
- Trailing SL/TP across all strategies is no-op (F1, F10)
- GUI displays SL values that don't match hot-path execution (F2)
- Strategies behave like stateless "buy on breakout" rather than the
  designed adaptive logic (F7, F8)
- Regime transitions don't retune open positions (F9)
- AUTO/DIP/MOM/EMA strategies aren't behaving as their authors intended

The fix is mechanical (wire functions back in + reroute trailing writes
to the channel the hot path actually reads). The risk is that strategies
will start behaving differently once their state-driven logic is alive
again, so each phase needs backtest validation.

## Goals

| # | Goal | Measure |
|---|---|---|
| G1 | Strategy state lifecycle works end-to-end in sharded engine | All five strategies' `_Init` + `_Adapt` fire per-core; state structs allocated; `_BuildParameters` reads state |
| G2 | Trailing SL/TP actually trails at execution layer | Hot path's `effective_sl` (max of live_sl + ratchet_sl) changes when strategy decides to trail |
| G3 | Display matches reality | GUI Positions panel SL = the value the hot path actually uses for SG_Evaluate |
| G4 | Regime detection responsive + centralized | Regime changes between RANGING / TRENDING / VOLATILE in a 30-min run on real data; one classifier instance, not per-core |
| G5 | Strategies' backtest performance is sensible after restoration | Each strategy's restored backtest produces reasonable trade rate, win rate, P&L distribution (looser bar — just "not catastrophically broken") |
| G6 | This class of regression cannot recur silently | Readiness skill blocks future sprints that orphan a function; behavioral parity test catches divergence |

## Phase 0 — Foundation (no behavior change yet)

Before touching strategy logic, build the infrastructure that makes
everything else faster and safer.

### 0.1 — Ship the health log

`MemHeaders/HealthLog.hpp` is already written this session. Commit it.
Wire engine init to read `cfg.health_log_path` + `cfg.health_log_level`
and call `Health_LogConfigure(...)`. Add the two cfg fields with parsers.

**Effort:** ~30 min.

**Acceptance:**
- `health_log_path = /tmp/foxml-health.jsonl` in cfg → file gets a line
  per Health_Log call
- `health_log_path = ""` → all calls become no-ops, zero overhead
- Existing `TT_REGIME_DEBUG=1` env var continues to work as a separate
  debug toggle

### 0.2 — Strategy interface contract document

`DOCS/STRATEGY_INTERFACE.md` (new). Documents the five-stage strategy
lifecycle that EVERY architecture must implement (or explicitly mark as
skipped):

```
1. Init       — at engine boot, per-core. Allocate state.
2. Adapt      — per slow-path cadence, per-core. Update state from market.
3. BuildParameters — per slow-path cadence, per-core.
                Read state + rolling stats; emit GateParameters for hot path.
4. ExitAdjust — per slow-path cadence, per-core, when positions open.
                Write pending_params.ratchet_sl (NOT pos->stop_loss_price).
5. RegimeAdjust — on regime transition, per-core, when positions open.
                Retune open positions for the new regime.
```

Plus: which struct fields are owned by which thread. Plus: the read-write
contract for shared fields (live_sl, cached_params, pos->stop_loss_price).

**Effort:** ~1h.

### 0.3 — Calls-graph-diff tool

`tools/calls_graph_diff.sh` (new). Greps the legacy entry point
(`PortfolioController.hpp`) and the sharded entry points
(`ControllerEventLoop.hpp` + `EngineSharded.hpp` + `ShardedBacktestDriver.hpp`)
for function calls. Outputs the diff: functions called in legacy but
not in sharded → REVIEW (likely orphaned). Functions called in sharded
but not in legacy → expected (new sharded helpers).

This is the tool that would have caught F7-F10 in 30 seconds.

**Effort:** ~30 min.

**Acceptance:** running it on the current codebase outputs the orphaned
functions we found this session (Momentum_Adapt, _ExitAdjust, etc.).

### 0.4 — Update INVARIANTS_MAP

Add rows for:
- **Strategy lifecycle:** every architecture must call `_Init`, `_Adapt`,
  `_BuildParameters`, `_ExitAdjust`, `_RegimeAdjust` — or explicitly
  document skipped stages with reason.
- **Hot-path field source of truth:** SG_Evaluate reads `core->live_sl`
  + `cached_params.ratchet_sl` for SL, `core->live_tp` + (no ratchet for
  TP currently) for TP. Strategy code MUST write to ratchet/cached fields
  to affect execution. Direct writes to `pos->stop_loss_price` are
  display-only and dead-code in sharded.
- **Display ↔ execution invariant:** GUI panels showing live trade state
  must read the same field SG_Evaluate uses. If they MUST diverge for
  latency reasons, the divergence is documented as an explicit invariant.

**Effort:** ~30 min.

### 0.5 — Ship the postmortem doc

`DOCS/v5.4-regression-postmortem.md` is already written this session.
Commit it. This becomes the durable artifact future-you reads when
doing similar architectural work.

**Effort:** 5 min (just commit).

**Phase 0 total:** ~3h. Pre-tag: `pre-v5.4.0-phase0`.

## Phase 1 — Infrastructure for state allocation

Allocate per-core strategy state struct unions. Add init dispatch.
NO behavior change yet — strategies still run stateless `_BuildParameters`
because we haven't wired `_Adapt` yet.

### 1.1 — Add strategy state to `CoreContext` + bump snapshot version

In `ControllerEventLoop.hpp`, extend `CoreContext<F>`:

```cpp
struct CoreContext {
    // ... existing fields ...

    // v5.4 — per-strategy state. Heap-allocated; engine init dispatches
    // by strategy_id. Backtest path also allocates.
    void* strategy_state;        // owned by this core; freed on shutdown
    uint8_t strategy_state_kind; // matches the strategy_id at allocation
};
```

Use `void*` to avoid bringing all strategy headers into ControllerEventLoop.
Concrete typing happens at the call site through the dispatcher.

**Snapshot version bump (load-bearing):**

`CoreContext` shape change ⇒ `SHARDED_SNAPSHOT_VERSION` MUST bump from
3 → 4. In `CoreFrameworks/ShardedSnapshotPersist.hpp`:

```cpp
#define SHARDED_SNAPSHOT_VERSION 4u  // was 3u
```

Persist/load policy: `strategy_state` is a pointer — NOT serialized
directly. Snapshot v4 persists `strategy_state_kind` only. On load,
the load path calls `Strategy_InitPerCore(slot, strategy_state_kind)`
to reallocate state from scratch matching the persisted kind. Strategy
state is treated as session-only (matches the deferred-to-v5.5.0 note
under "What's NOT in this plan"). Operator who restarts during open
positions gets:
- Position state restored (entry_price, qty, TP/SL — already persisted)
- Strategy state freshly initialized (no adaptation history carried over)

This is acceptable for v5.4 since strategy state is meant to converge
within a few cadences anyway. v5.5.0 ships proper persistence.

**Old snapshot (v3) handling:** existing load path already rejects
on version mismatch (`version != SHARDED_SNAPSHOT_VERSION` → fail).
With the bump, v3 snapshots fail loudly with "snapshot version 3,
expected 4 — incompatible." Acceptable — v3 snapshots are paper-mode
artifacts; live-mode users start fresh post-upgrade anyway.

**CHANGELOG.md entry:** add to the v5.4.0 row:
> BREAKING — SHARDED_SNAPSHOT_VERSION 3 → 4. Pre-v5.4 snapshots are
> rejected on load with a clear error. Operators with live-trading
> snapshots must close positions on the engine before upgrading,
> or accept that paper-mode session state is reset.

**Test:** new test in `controller_test.cpp` Phase 1.4 group:
- Write a v3 snapshot (synthetic — just the version int + minimal payload)
- Attempt to load with v5.4 code
- Assert load returns failure with the expected error message
- Then write a v4 snapshot, load, verify Strategy_InitPerCore was
  invoked for each persisted core's strategy_state_kind

### 1.2 — `Strategy_InitPerCore(slot, strategy_id)` dispatcher

In `Strategies/StrategyParameters.hpp` (or a new
`Strategies/StrategyLifecycle.hpp`):

```cpp
inline void Strategy_InitPerCore(EventLoopState<F>* state, int slot,
                                  uint8_t strategy_id, /* ... rolling, etc. */) {
    auto& ctx = state->cores[slot];
    if (ctx.strategy_state) {
        Strategy_FreePerCore(state, slot); // deallocate any existing
    }
    switch (strategy_id) {
        case STRATEGY_MOMENTUM:
            ctx.strategy_state = new MomentumState<F>{};
            Momentum_Init((MomentumState<F>*)ctx.strategy_state, /* ... */);
            break;
        case STRATEGY_MEAN_REVERSION:
            ctx.strategy_state = new MeanReversionState<F>{};
            MeanReversion_Init(/* ... */);
            break;
        // ... etc for SimpleDip / EmaCross / MLStrategy
        case STRATEGY_AUTO:
        case STRATEGY_NONE:
            ctx.strategy_state = nullptr;
            break;
    }
    ctx.strategy_state_kind = strategy_id;
}
```

Plus `Strategy_FreePerCore` for cleanup, called from `EventLoopState_Free`.

### 1.3 — Wire `Strategy_InitPerCore` at engine boot

In `EngineSharded_Run`, after `state.cores[c]` is initialized, call
`Strategy_InitPerCore` for each registered core.

Same in `ShardedBacktestDriver` for backtest parity.

### 1.4 — Validation

- Build green
- 800+ existing tests still pass
- `controller_test` adds a smoke test: init each strategy_id → state
  allocated, kind matches, free works without leak

**Effort:** ~2h.

**Acceptance:** strategy state structs exist per-core. NO BEHAVIOR
CHANGE because nothing reads them yet. This is purely scaffolding.

**Phase 1 pre-tag:** `pre-v5.4.0-phase1`.

## Phase 2 — Per-strategy wiring (one strategy at a time)

For each strategy, in this order: SimpleDip → MeanReversion → Momentum
→ EmaCross → MLStrategy. Each phase wires `_Adapt` + modifies
`_BuildParameters` to take state + rewrites `_ExitAdjust` against
ratchet_sl. Validate before moving to the next.

Order chosen because SimpleDip is the simplest and the reference impl;
MR/Momentum/EmaCross/ML have progressively more complex state.

**Per-strategy work breakdown** (each phase, except SimpleDip which has
no `_ExitAdjust`):

| sub-task | typical effort |
|---|---|
| Modify `_BuildParameters` signature to take state + read state | 0.5 h |
| Wire `_Adapt` per-cadence in `EventLoop_RebuildOneCore` (dispatcher) | 0.5 h |
| Rewrite `_ExitAdjust` to write `pending_params.ratchet_sl` via shared helper, apply fee-floor cap | 1.5 h |
| Wire `_ExitAdjust` per-cadence in `EventLoop_RebuildOneCore` for cores with open positions | 0.25 h |
| Add behavioral test (effective_sl trails when expected; see Phase 5 design for harness) | 1 h |
| Backtest comparison vs pre-fix (run on known dataset, eyeball trade rate / P&L distribution) | 1 h |
| Rebuild + run all tests, debug any unexpected failures | 0.25–0.75 h |
| **per-strategy total** | **~5 h** (SimpleDip: ~3 h, no _ExitAdjust) |

**Phase 2 revised total:** 21 h (was 14 h — original underestimated
the `_ExitAdjust` rewrite and the per-strategy validation cost).

### 2.1 — SimpleDip wiring

**Steps:**
1. Modify `SimpleDip_BuildParameters` signature to take
   `SimpleDipState<F>* state` (was rolling-only). Read state for any
   adapted thresholds.
2. Add per-core `EventLoop_AdaptOneCore(slot)` helper that dispatches
   to `SimpleDip_Adapt` for SimpleDip cores. Called from
   `EventLoop_RebuildOneCore` BEFORE `_BuildParameters`.
3. SimpleDip doesn't have `_ExitAdjust` (simplest strategy) so skip
   that step here.

**Validation:**
- Backtest: run a known dataset, compare SimpleDip's behavior pre-fix
  vs post-fix. Trade count + P&L should be DIFFERENT (state now
  affects gate params), but should remain in a sensible range
  (not e.g. 100× more trades, not zero trades).
- Diff the per-tick gate parameter trace pre vs post — should show
  values that respond to recent market action (state effect).

**Pre-tag:** `pre-v5.4.0-phase2.1-simpledip`.

**Effort:** ~3 h (no `_ExitAdjust`; reference implementation establishes
the dispatcher + state-allocation patterns the next four phases reuse).

### 2.2 — MeanReversion wiring

Same shape as 2.1 plus `_ExitAdjust` rewrite:

**Steps:**
1. Modify `MeanReversion_BuildParameters` to take state.
2. Wire `MeanReversion_Adapt` per-cadence.
3. **Rewrite `MeanReversion_ExitAdjust`** to write
   `state->cores[slot].pending_params.ratchet_sl` instead of
   `pos->stop_loss_price`. Set `dirty=1` on update so seqlock pushes.
4. Wire `MeanReversion_ExitAdjust` per-cadence in
   `EventLoop_RebuildOneCore` for cores with open positions.

**Validation:**
- Existing tests (775+) still pass
- Backtest comparison
- Specific test: open a position, run several adapt cycles with rising
  price, verify hot path's `effective_sl` (read via diagnostic) actually
  trails up.

**Pre-tag:** `pre-v5.4.0-phase2.2-mr`.

**Effort:** ~5 h (full strategy template: state + adapt + build + exit-adjust
rewrite to ratchet_sl + behavioral test + backtest comparison).

### 2.3 — Momentum wiring

Same shape as 2.2.

**Specific concern:** Momentum's `_ExitAdjust` has the
"falling-knife catch" geometry that confused the user — the trailing
section above original_tp ratchets SL upward rapidly. After rewriting
to ratchet_sl, this would now actually fire. The v5.1.7 fee-floor cap
in `EventLoop_TrailingSLRatchetOneCore` doesn't apply to direct strategy
writes — we need to APPLY THE SAME CAP in the strategy's ratchet write
to prevent over-tight ratcheting. Either:

- (a) Strategies route through a shared helper `Strategy_WriteRatchetSL(slot, new_sl)` that applies the fee-floor cap
- (b) Each strategy applies its own cap inline

Pick (a) for consistency.

**Pre-tag:** `pre-v5.4.0-phase2.3-momentum`.

**Effort:** ~5 h (full template + extra care on the falling-knife branch's
fee-floor cap test — assertion: even with momentum_sl_mult tight, the
written ratchet_sl never inverts above entry × (1 - 3 × fee_rate)).

### 2.4 — EmaCross wiring

Same shape as 2.2-2.3. EmaCross is "more like SimpleDip with EMA cross
trigger" so fewer surprises expected.

**Pre-tag:** `pre-v5.4.0-phase2.4-emacross`.

**Effort:** ~4 h (full template; EmaCross has the simplest exit-adjust
of the four trailing strategies).

### 2.5 — MLStrategy wiring

Same shape PLUS the ML-specific ConfidenceScorer interaction. ML's
state includes prediction history, IC tracking, freshness decay — all
state-driven. Re-enabling state means the ML gate becomes responsive
again to model performance over time.

**Specific concern:** MLStrategy's state interaction with the existing
`ml_ctx` passed to `ML_BuildParameters`. The ML_ctx already passes
`confidence` and `out_prediction` — but it doesn't include the per-core
MLStrategyState. After this phase, MLStrategy's state lives in
`ctx.strategy_state` and is read by the modified `ML_BuildParameters`.

**Pre-tag:** `pre-v5.4.0-phase2.5-ml`.

**Effort:** ~6 h (full template + ML-specific ConfidenceScorer state
integration + IC tracking validation + freshness decay sanity check).

**Phase 2 total:** ~21 h (revised from initial 14 h estimate after
readiness pass identified missing _ExitAdjust rewrite + signature
change costs). Spread across multiple sessions.

## Phase 3 — Regime restoration

Two parts: re-enable regime-transition position adjustment, AND
centralize regime detection (Phase C.6 of the audit plan).

### 3.1 — `Regime_AdjustPositions` wiring

**Steps:**
1. In `EventLoop_RebuildOneCore`, after the regime classification block,
   detect if `current_regime` changed since last cycle.
2. On change: call `Regime_AdjustPositions(&portfolio, slot, ...)` for
   open positions on this core.
3. Modify `Regime_AdjustPositions` so its writes go to
   `pending_params.ratchet_sl` for SL changes. TP changes need a
   different mechanism — see 3.3.

### 3.2 — Centralize regime detection

`state->cores[c].regime_state` becomes `state->shared_regime_state`
(single instance). The detailed synchronization design:

**Writer:** producer thread is sole writer of `shared_regime_state`.
Producer already runs `Regime_ComputeSignals` + `Regime_Classify` for
its own purposes (warmup, kill-switch); reuse that compute path.
Centralized arch (legacy) has no producer — for that arch, the
controller core takes the writer role (same single-writer pattern).

**Replication:** mirror `EventLoop_UpdateEmaPriceAllCores` (v5.1.0 pattern).
After producer's classify, copy two ints to each engine's CoreContext:
```cpp
struct CoreContext {
    // ... existing ...
    int  current_regime;   // replicated from producer (was state->cores[c].regime_state.current_regime)
    int  proposed_regime;  // replicated for hysteresis visibility (read-only on per-core thread)
};
```
Two int copies per engine per tick = trivial cost (~50ns total for 16
engines, vs the 4× full Regime_ComputeSignals + Regime_Classify the
per-core arch currently does at ~10µs each).

**Reader:** per-core slow-path thread reads `ctx.current_regime`
directly. No synchronization needed — int load is atomic on x86, and
the value can be stale by at most one tick (eventually consistent,
which is fine for regime).

**Hysteresis state:** lives in the producer's `shared_regime_state`,
not replicated. Per-core threads only see the post-hysteresis
`current_regime` value. This is the correct semantic — hysteresis is
a market-level smoothing, not a per-engine concern.

**Transition detection:** per-core thread compares its locally cached
`last_seen_regime` (a CoreContext field, single-writer by this core)
against `ctx.current_regime` each cadence. Mismatch = transition.
Transition triggers `Regime_AdjustPositions` (Phase 3.1).

**Removed code:** `state->cores[c].regime_state` field (per-core).
The `Regime_ComputeSignals` + `Regime_Classify` calls in
`EventLoop_RebuildOneCore` go away — replaced by the simple read of
`ctx.current_regime`. Saves ~10µs per cadence per core; recoups some
of the 1000µs slow-path tail.

**Risk:** parity_harness must remain byte-identical. Run BEFORE the
centralization to capture baseline (legacy ↔ sharded match), AND
AFTER. If centralized regime introduces tick-offset drift in regime
transitions (hysteresis state evolving on producer cadence vs per-core
cadence), the harness should catch it via the new trade-trajectory
parity check (Phase 5.1).

**Specific test for regime parity** (added to Phase 5.1):
- Run identical input through legacy single_core path, sharded
  centralized-regime path
- Capture every regime transition (tick number, from→to)
- Cross-reference: same tick numbers, same transitions, in both runs
- If timestamps differ by even 1 tick, FAIL the test — that's drift

### 3.3 — TP ratchet channel

The hot path currently has `cached_params.ratchet_sl` but no
`ratchet_tp`. Either:

- (a) Add `cached_params.ratchet_tp`; SG_Evaluate uses
  `effective_tp = min(live_tp, ratchet_tp)` if ratchet non-zero
  (since for TP, lower trail = lock in profit on falling target,
  but for LONG we want trailing TP that ratchets UP — so it's
  `effective_tp = max(live_tp, ratchet_tp)` matching the SL pattern)
- (b) Update `core->live_tp` directly via a controlled slow-path
  channel (atomic store, ordered with the seqlock)

(a) is more consistent with existing patterns. Add it.

**Pre-tag:** `pre-v5.4.0-phase3-regime`.

**Effort:** ~5h.

## Phase 4 — Display ↔ execution alignment

Fix F2: GUI Positions panel reads same field hot path uses.

**Steps:**
1. Identify GUI sites that read `pos->stop_loss_price` /
   `pos->take_profit_price` for display.
2. Replace with reads of `core->live_sl + cached_params.ratchet_sl`
   (formatted as "effective SL" matching SG_Evaluate's logic).
3. Same for TP.

**Validation:** GUI display matches what would actually trigger an
exit in any market scenario. Specifically: when the displayed SL is X,
price dropping below X actually fires exit.

**Pre-tag:** `pre-v5.4.0-phase4-display`.

**Effort:** ~2h.

## Phase 5 — Behavioral parity gates + tests

Now that strategies actually do things, lock in regression-resistance.

### 5.1 — Extend parity_harness

Currently `parity_harness` compares legacy single_core ↔ sharded backtest
training data. Extend so it also compares **trade trajectories**:
position open/close events, gate parameter snapshots, regime transitions.
Same input → same trades. If a future architectural sprint breaks this,
the harness fails before merge.

### 5.2 — Per-strategy "smoke fire" tests

For each strategy: synthetic input that SHOULD produce a buy → assert
gate fires + parameters sensible. Catches dispatcher regressions.

### 5.3 — Behavioral execution-layer test (Type A)

For each strategy:
- Open position via OMS_HandleFill (synthetic fill at known price)
- Run slow-path adapt + trailing for N cycles with rising price
- After each cadence, inspect `state.cores[slot].cached_params.ratchet_sl`
  AND `state.cores[slot].core->live_sl` (read directly from the
  ExecutionCore via test-friendly accessor)
- Assert: `effective_sl = max(live_sl, ratchet_sl)` HAS CHANGED upward
  (with optional fee-floor cap respected)

**Test harness design** (chosen approach: read core state directly):

The test harness pattern already used in `controller_test.cpp` keeps a
local `EventLoopState<F>` + `OrderManagerState<F>` + `ExecutionCore<F>`
on the test stack. Tests can already read `state.cores[slot].*` fields
directly. Extending this to read `core->cached_params.ratchet_sl` and
`core->live_sl` requires zero new infrastructure — just one helper:

```cpp
// In tests/controller_test.cpp test fixture:
template <unsigned F>
inline FPN<F> get_effective_sl(const ExecutionCore<F>& core, uint8_t active) {
    FPN<F> sl = active
        ? core.live_sl
        : core.cached_params.sg_stop_loss_price;
    return FPN_Max(sl, core.cached_params.ratchet_sl);
}
```

This mirrors ExecutionCore.hpp:268+322 logic exactly. Test reads it
after each cadence to assert trailing behavior.

**Worked test case for MeanReversion (template for others):**

```cpp
{
    // Setup
    EventLoopState<64> state;
    EventLoopState_Init(&state, &cfg);
    OrderManagerState<64> oms;
    ExecutionCore<64> core;
    state.cores[0].core = &core;
    Strategy_InitPerCore(&state, 0, STRATEGY_MEAN_REVERSION);

    // Open position (synthetic fill at $100, qty=1, TP=$103, SL=$97)
    // ... boilerplate matching existing controller_test patterns ...

    FPN<64> sl_t0 = get_effective_sl(core, /*active=*/1);
    check("MR initial effective_sl ≈ entry_price - sl_amount",
          FPN_ToDouble(sl_t0) > 96.0 && FPN_ToDouble(sl_t0) < 98.0);

    // Run 5 cadences with rising price
    for (int t = 0; t < 5; ++t) {
        FPN<64> price = FPN_FromDouble<64>(100.0 + 0.5 * (t+1));  // $100.5 ... $102.5
        EventLoop_UpdateRollingStateOneCore(&state, 0, price, ...);
        EventLoop_RebuildOneCore(&state, 0, ...);
        // Strategy._Adapt + _ExitAdjust ran inside RebuildOneCore;
        // ratchet_sl pushed via seqlock; ExecutionCore_SetParameters
        // already happened (state.cores[0].dirty consumed)
    }

    FPN<64> sl_t5 = get_effective_sl(core, /*active=*/1);
    check("MR effective_sl trails upward after 5 cadences with rising price",
          FPN_ToDouble(sl_t5) > FPN_ToDouble(sl_t0));
    check("MR effective_sl respects fee-floor cap (never above entry × (1 - 3 × fee_rate))",
          FPN_ToDouble(sl_t5) <= 100.0 * (1.0 - 3.0 * 0.001));
}
```

**Why this works without new infrastructure:** existing tests already
construct `ExecutionCore<64>` on stack and call slow-path helpers
directly. Reading `core->cached_params.ratchet_sl` post-Setparameters
is just a struct field read — same pattern as existing assertions
checking `state.cores[c].core_realized` etc.

**Effort impact on Phase 5.3:** ~30 min for the helper + ~30 min per
strategy for the test case = total ~3 h for all 5 strategies (was
implicitly budgeted in Phase 5's 6 h block).

This test currently FAILS (strategy `_ExitAdjust` writes are dead — no
ratchet update). After Phase 2 wiring + Phase 5.3 test, it PASSES.
Permanent gate against this regression class.

### 5.4 — Calls-graph-diff CI integration

Make `tools/calls_graph_diff.sh` (from Phase 0.3) a CI-gated
script. If a function exists in `PortfolioController` but not in any
sharded entry point, FAIL — prompt review of whether it's intentional
or another orphan.

**Pre-tag:** `pre-v5.4.0-phase5-tests`.

**Effort:** ~6h.

## Phase 6 — Prevention infrastructure (the durable value)

This is what makes the next architectural sprint safer.

### 6.1 — Update readiness skill

Add to `.claude/skills/readiness/SKILL.md`:

**New check section: Architectural sprint detection.** When a plan
mentions "split", "decouple", "extract", "centralize", "per-core", etc.:
- Require enumeration of every public function of the affected modules
- For each function: where is it called pre-sprint? where will it be
  called post-sprint? if "nowhere," is that intentional and documented?
- Require running `tools/calls_graph_diff.sh` against current vs
  proposed state; orphaned functions = block ship until reviewed.

**New check: Display ↔ execution invariant.** When a plan touches GUI
state display OR hot-path field reads, require that GUI reads the same
field execution reads. Flag divergences as explicit invariants.

**New check: Strategy lifecycle.** When a plan touches strategy code,
verify all 5 lifecycle stages (Init/Adapt/BuildParameters/ExitAdjust/
RegimeAdjust) are accounted for. Stages can be marked "skipped — reason"
but never silently absent.

### 6.2 — Update dust skill

Add to `.claude/skills/dust/SKILL.md`:

**New scan: dead-write detection.** For each struct field, grep all
writes. For each write site, verify there is at least one read path
from execution / display that reads the field. Writes with no matching
read = candidate dead-write.

**New scan: orphaned function detection.** For each `Pattern_FunctionName`
function definition, grep call sites across active build configs (engine,
engine_gui, foxml_suite). Functions with zero call sites in any active
build = candidate dead code.

### 6.3 — Code-map auto-coverage

Extend `tools/gen_code_map.sh` to also emit each function's call sites.
The output becomes a "coverage map" — readable answer to "what calls
this function?" without grepping. Feeds the readiness skill's
architectural-sprint check.

### 6.4 — Strategy interface contract enforcement

Compile-time or test-time: ensure each strategy implements all five
lifecycle stages. Could be:
- C++ template trait: `StrategyLifecycle<MomentumState>` requires
  `Init`, `Adapt`, `BuildParameters`, `ExitAdjust`, `RegimeAdjust`
  member functions
- Or a test that asserts each strategy ID has all five functions
  present in the dispatcher

Either approach prevents new strategies from skipping stages by accident.

**Pre-tag:** `pre-v5.4.0-phase6-prevention`.

**Effort:** ~5h.

## Phase 7 — Postmortem polish + master tag

Update `DOCS/v5.4-regression-postmortem.md` with:
- Final findings count after all phases
- What each fix actually changed
- Behavioral comparison: pre-v5.4 stateless vs post-v5.4 stateful per strategy
- Cross-references to specific commits / pre-tags for each finding

Tag `v5.4.0`. Push.

**Effort:** ~1h.

## Total effort estimate

Revised after readiness pass identified gaps in Phase 2 sub-tasks
and Phase 1 snapshot-version work:

| Phase | Effort | Cumulative |
|---|---|---|
| 0 — Foundation (HealthLog, contract, calls-graph-diff, INVARIANTS, postmortem) | 3 h | 3 h |
| 1 — Infra (state alloc + dispatcher + SHARDED_SNAPSHOT_VERSION 3→4 + load-rejection test) | 2.5 h | 5.5 h |
| 2.1 — SimpleDip (no _ExitAdjust; reference impl) | 3 h | 8.5 h |
| 2.2 — MR (full template) | 5 h | 13.5 h |
| 2.3 — Momentum (full template + falling-knife fee-floor cap test) | 5 h | 18.5 h |
| 2.4 — EmaCross (full template, simplest exit logic) | 4 h | 22.5 h |
| 2.5 — ML (full template + ConfidenceScorer integration) | 6 h | 28.5 h |
| 3 — Regime (Regime_AdjustPositions wiring + centralize + TP ratchet channel) | 6 h | 34.5 h |
| 4 — Display ↔ execution alignment | 2 h | 36.5 h |
| 5 — Tests (parity_harness extension + smoke fires + behavioral effective_sl + calls-graph CI) | 6 h | 42.5 h |
| 6 — Prevention (readiness skill update, dust scan, code-map call coverage, contract enforcement) | 5 h | 47.5 h |
| 7 — Polish (postmortem update + master tag) | 1 h | 48.5 h |

**~48-49 hours total.** Realistic spread: ~2 weeks of focused work, or
4-6 weeks at 1-2h/day. NOT a single-session ship. The fastest path to
"strategies aren't badly broken anymore" is Phases 0 + 1 + 2.1 (~9 h,
gets SimpleDip restored as the proof-of-concept) — after that the per-
strategy work is mostly mechanical replication.

## Order of attack — what to do first

The quickest path to "strategies aren't badly broken anymore" is
Phases 0 + 1 + 2.1 (SimpleDip). That's ~9 hours and proves the
infrastructure works on the simplest strategy. After SimpleDip is
restored and validated, the rest is mechanical replication.

Don't try to wire all five strategies at once. The validation step
(backtest comparison, behavioral check) is where bugs surface. One
strategy at a time means one set of behavior changes to evaluate.

```
Day 1 (focused session):  Phases 0 + 1 + 2.1 (SimpleDip) — ~9 h
Day 2:                    Phase 2.2 (MR) — 5 h
Day 3:                    Phase 2.3 (Momentum) — 5 h
Day 4:                    Phase 2.4 (EmaCross) — 4 h
Day 5:                    Phase 2.5 (ML) — 6 h
Days 6-7:                 Phase 3 (Regime) — 6 h
Day 8:                    Phase 4 (Display) — 2 h
Days 9-10:                Phase 5 (Tests) — 6 h
Days 11-12:               Phase 6 (Prevention) — 5 h
Day 13:                   Phase 7 (Polish + ship) — 1 h
```

Each "day" is a 2-6h focused block, not a calendar day. Calendar-wise
this could span 2-6 weeks depending on cadence.

## Future-thinking infrastructure (the part that matters most)

The v5.4 ship is one fix. The infrastructure built in Phases 0 and 6
makes the NEXT fix easier:

### Architecture migration playbook

`DOCS/ARCHITECTURE_MIGRATIONS.md` (new — write as part of Phase 7):
captures the pattern observed in v4.x sharded port + v5.0 per-core
split + v5.4 lifecycle restoration. Future-you reads this before doing
any architectural decoupling sprint.

Sections:
- The "implicit behavior loss" failure mode (centralized → per-core
  drops behaviors that weren't documented)
- The "dead-write" failure mode (cache snapshot in hot path makes
  per-tick struct writes ineffective)
- The "calls graph diff" check (always run before merging)
- The strategy lifecycle as a worked example
- Pattern: every architecture migration must produce TWO artifacts:
  (a) the new code, (b) a postmortem-style doc enumerating what was
  preserved and what changed in behavior

### Health log integration

Once shipped (Phase 0.1), every fix and feature should log to it.
Categories used so far: regime, sl_emission, sg_eval, cooldown,
latency, fee_accounting, strategy_adapt. New features add new
categories. The log becomes the operational debugging surface — when
the next regression appears, enable the log and tail it; the cause
shows up without code changes.

### Calls-graph-diff as ongoing gate

Extend `tools/calls_graph_diff.sh` (Phase 0.3) into a quarterly /
pre-release scan. Output any function present in one architecture but
not another. Track the diff over time — if functions appear/disappear,
that's a signal for review.

### The strategy lifecycle as a contract

Once `DOCS/STRATEGY_INTERFACE.md` is written (Phase 0.2), it becomes
the spec for ANY future strategy. Adding a new strategy = implementing
all five stages or explicitly marking skipped ones. Existing strategies
can't silently lose stages because the readiness skill checks against
this doc.

### Behavior parity tests as the "won't drift" gate

`parity_harness` extended to compare trade trajectories (Phase 5.1)
becomes the ultimate regression gate. If sharded engine behavior
diverges from legacy on identical input, the test fails. This catches
even subtle drift that doesn't show up in feature/training data.

### Per-cadence diagnostic via Health log

Replace TT_REGIME_DEBUG / TT_SL_DEBUG env vars with always-available
health log categories. Operator enables `cfg.health_log_path` and gets
structured output for any future debugging session. No code changes,
no rebuilds — flip a config and tail.

## Rollback story (consolidated)

Every phase has its own pre-tag. Granular rollback at any point if a
phase introduces unexpected behavior. The pre-tags pushed to origin in
this session and the ones planned for v5.4.0:

| Tag | What it captures | Status |
|---|---|---|
| `pre-v5.4.0-investigation` | clean state before any v5.4.0 work | **PUSHED 2026-04-29** |
| `pre-v5.4.0-phase0` | before HealthLog wired + contract doc + INVARIANTS | planned |
| `pre-v5.4.0-phase1` | before strategy state added to CoreContext + SHARDED_SNAPSHOT_VERSION bump | planned |
| `pre-v5.4.0-phase2.1-simpledip` | before SimpleDip wiring | planned |
| `pre-v5.4.0-phase2.2-mr` | before MeanReversion wiring | planned |
| `pre-v5.4.0-phase2.3-momentum` | before Momentum wiring (falling-knife concern) | planned |
| `pre-v5.4.0-phase2.4-emacross` | before EmaCross wiring | planned |
| `pre-v5.4.0-phase2.5-ml` | before MLStrategy wiring | planned |
| `pre-v5.4.0-phase3-regime` | before Regime_AdjustPositions wiring + centralization | planned |
| `pre-v5.4.0-phase4-display` | before GUI/execution alignment | planned |
| `pre-v5.4.0-phase5-tests` | before test infrastructure additions | planned |
| `pre-v5.4.0-phase6-prevention` | before readiness/dust skill updates | planned |
| `v5.4.0` | final ship | planned |

**13 rollback points total.** Reverting from any phase:
1. `git reset --hard <pre-tag>`
2. Engine continues to function as it did before that phase
3. Each phase's behavior is independent of subsequent phases

**Operational rollback (no code change needed):** if any sharded-arch
behavior is worse after a phase ships, set `engine_arch = centralized`
in `engine.cfg` to fall back to the legacy single_core path entirely.
That path is unaffected by Phase 1-3 changes (CoreContext additions
don't touch PortfolioController). The centralized escape hatch is the
ultimate "if all else fails" rollback for live deploys.

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Wiring `_Adapt` causes strategies to behave very differently from current paper-mode behavior | Backtest validation between each phase; per-strategy pre-tags allow rollback to "stateless but working" if the stateful version misbehaves |
| `_ExitAdjust` rewrite to ratchet_sl conflicts with existing `EventLoop_TrailingSLRatchetOneCore` | They write to the same field; design Phase 2.3+ so both paths coexist (strategy writes ratchet, global ratchet helper also writes — the higher value wins via `FPN_Max` semantics) |
| Centralizing regime breaks parity_harness | Run parity before AND after the centralization in Phase 3.2; if it fails, the centralization is wrong — pause Phase 3 and investigate |
| ML strategy state restoration changes ConfidenceScorer behavior | ConfidenceScorer is per-core already; MLStrategyState restoration only affects the per-strategy memory. Validate via backtest comparison |
| Phase 6 prevention skills produce false positives | First runs may flag legitimate cases (e.g., functions that are intentionally called only in legacy backtest paths). Refine the false-positive rate over a few runs before making them blocking gates |
| Display fix in Phase 4 surprises operator (SL value displayed differently than before) | Document the display change in CHANGELOG.md + tooltip in GUI; SL display now reads "effective SL" with the ratchet semantics |

## What's NOT in this plan (deferred)

- **Full re-architecture of slow-path threading** — the per-core split
  has subtle issues but reverting to centralized would be a bigger ship
  than this plan addresses. Phase 3.2 centralizes only regime detection,
  which is the most defensible piece to recentralize.
- **Snapshot persistence of strategy state** — currently strategy state
  isn't in `ShardedSnapshotPersist`. After Phase 1 it should be (so
  restart preserves state). Defer to v5.5.0.
- **GUI panel for "strategy state inspector"** — would let operator see
  each strategy's adapted parameters in real-time. Useful but not
  load-bearing. v5.5.x candidate.
- **Backwards compatibility with the centralized engine** — once
  Phase 2 ships, centralized arch still uses the old `PortfolioController`
  path which calls _Adapt etc. Both arches will work; they'll do
  different things. Eventually centralized should be deprecated entirely
  but that's a v6.0 concern.

## Success criteria

- All five strategies run their full lifecycle (Init → Adapt →
  BuildParameters → ExitAdjust → RegimeAdjust) per slow-path cadence
- Hot path's `effective_sl` actually changes when strategies decide
  to trail; verifiable via behavioral test
- GUI Positions panel SL = hot-path SL (display ↔ execution aligned)
- Regime classifier transitions between distinct regimes during a
  30-min real-data run; visible in health log
- `parity_harness` passes (legacy ↔ sharded byte-identical training
  data) AND a NEW trade-trajectory parity test passes
- Backtests of all five strategies on a known dataset show "different
  but sensible" trade behavior compared to pre-v5.4 baseline
- `tools/calls_graph_diff.sh` shows zero orphaned functions between
  legacy and sharded
- Readiness skill blocks a hypothetical future sprint that orphans
  a function
- INVARIANTS_MAP gains 5+ new rows
- DOCS/v5.4-regression-postmortem.md and DOCS/STRATEGY_INTERFACE.md
  exist and explain the architectural decisions

## Why this matters beyond fixing the bugs

The fix itself is mechanical. The durable value is the prevention
infrastructure: readiness skill checks for architectural sprints, the
calls-graph-diff tool, the health log, the strategy interface contract,
the trade-trajectory parity test. These turn the next regression of
this class from "discovered after weeks of confusion in paper mode"
into "blocked at plan-review time before any code is written."

That's the thing professional teams have that solo builders typically
don't: a senior who's lived through this exact failure mode. Building
that into tooling means future-you doesn't have to keep re-learning
the lesson.

Strategies running their full lifecycle is necessary; preventing the
next class of orphaned-architecture bug is the actual ship value.
