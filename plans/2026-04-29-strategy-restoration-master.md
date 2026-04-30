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

### 1.1 — Add strategy state to `CoreContext`

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

**Effort:** ~2h.

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

**Effort:** ~3h.

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

**Effort:** ~3h.

### 2.4 — EmaCross wiring

Same shape as 2.2-2.3. EmaCross is "more like SimpleDip with EMA cross
trigger" so fewer surprises expected.

**Pre-tag:** `pre-v5.4.0-phase2.4-emacross`.

**Effort:** ~2h.

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

**Effort:** ~4h (ML is more complex).

**Phase 2 total:** ~14h. Spread across multiple sessions probably.

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
(single instance, owned by producer thread or one designated core).
`Regime_ComputeSignals` + `Regime_Classify` runs once per cadence;
the result is replicated to each engine's CoreContext (mirror the
ema_price replication pattern from v5.1.0).

**Risk:** parity_harness must remain byte-identical. Run it before
and after.

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

### 5.3 — Behavioral execution-layer test (Type A from earlier discussion)

For each strategy:
- Open position
- Run slow-path adapt + trailing for N cycles with rising price
- Assert: hot path's `effective_sl` HAS CHANGED upward
- This test currently fails (writes are dead) → wiring verifies fix
- Permanent gate against this regression class

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

| Phase | Effort | Cumulative |
|---|---|---|
| 0 — Foundation | 3h | 3h |
| 1 — Infra | 2h | 5h |
| 2.1 — SimpleDip | 2h | 7h |
| 2.2 — MR | 3h | 10h |
| 2.3 — Momentum | 3h | 13h |
| 2.4 — EmaCross | 2h | 15h |
| 2.5 — ML | 4h | 19h |
| 3 — Regime | 5h | 24h |
| 4 — Display | 2h | 26h |
| 5 — Tests | 6h | 32h |
| 6 — Prevention | 5h | 37h |
| 7 — Polish | 1h | 38h |

**~38 hours total.** Realistic spread: ~2 weeks of focused work, or
4-6 weeks at 1-2h/day. NOT a single-session ship.

## Order of attack — what to do first

The quickest path to "strategies aren't badly broken anymore" is
Phases 0 + 1 + 2.1 (SimpleDip). That's ~7 hours and proves the
infrastructure works on the simplest strategy. After SimpleDip is
restored and validated, the rest is mechanical replication.

Don't try to wire all five strategies at once. The validation step
(backtest comparison, behavioral check) is where bugs surface. One
strategy at a time means one set of behavior changes to evaluate.

```
Day 1 (focused session):  Phases 0 + 1 + 2.1 (SimpleDip) — ~7h
Day 2:                    Phase 2.2 (MR) — 3h
Day 3:                    Phase 2.3 (Momentum) — 3h
Day 4:                    Phase 2.4 (EmaCross) — 2h
Day 5:                    Phase 2.5 (ML) — 4h
Day 6-7:                  Phase 3 (Regime) — 5h
Day 8:                    Phase 4 (Display) — 2h
Days 9-10:                Phase 5 (Tests) — 6h
Days 11-12:               Phase 6 (Prevention) — 5h
Day 13:                   Phase 7 (Polish + ship) — 1h
```

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
