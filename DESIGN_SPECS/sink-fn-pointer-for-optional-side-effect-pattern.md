# Sink-fn-pointer for optional side-effect pattern

**Established:** 2026-05-15 (v5.15.5.F.4c.3 WIP2d-1.B.1 r-6 phase 2)
**Status:** Stage 3 ACTIVE v1.0 (promoted 2026-05-15 at v5.15.5.F.4c.3 r-8 ship close)
**Tags:** structural-fix, branchless, determinism, side-effect-gating, framework-discipline; serves H20; sister to Pattern 1 / Pattern 3 in `branchless-dispatch-discipline.md`
**Cross-references:**
- `branchless-dispatch-discipline.md` — sister spec (Pattern 1 / Pattern 3 / Pattern 4); this is the "Pattern 5" variant for optional side effects
- `decision-time-data-binding-pattern.md` — composes; noop fn = the "stub" semantic (always-call, default no-op)
- `DOCS/DESIGN_PHILOSOPHY.md` § 4 Latency cost framework — branchless preferred for SP/HP even when nominally slower
- CLAUDE.md H20 invariant — branchless preferred for SP/HP data-dependent dispatch

---

## Problem statement

Slow-path and hot-path code frequently includes OPTIONAL side-effect calls — logging, telemetry, debug emit, calibration capture — gated by null state checks at the callsite:

```cpp
// FORBIDDEN at scale — Class 28 adjacent (per-callsite branch on optional emit)
void OrderManager_HandleFill(...) {
    // ... main work ...
    if (oms->trade_log) {                              // BRANCH per fill
        TradeEvent synth = ...;
        ShardedTradeLog_RecordEntry(oms->trade_log, synth, ...);
    }
    if (oms->calibration_log_file) {                   // BRANCH per fill
        // calibration row emit
    }
    if (oms->bench_log) { ... }                        // BRANCH per fill
    // ... more optional emit guards ...
}
```

Each callsite branch:
- Adds a predictor entry (BTB pressure; finite capacity ~4K entries on modern x86)
- Injects variance (mispredict cost 30-100ns real-world per `DESIGN_PHILOSOPHY.md` § 4)
- Spreads the null-check semantic across many sites (each must remember to guard)
- Violates H20 if applied to SP/HP/drainer code

The branches fit H20 exception #4 ("genuine binary predicate without alternative") only because the alternative — always-call + check inside — was assumed to be the only option. But there IS a third option: branchless dispatch via fn-pointer with noop default.

---

## The pattern

**Subsystem state holds a fn-pointer per optional emit point. Default = noop fn. Real fn set at boot when subsystem is enabled. Callsites ALWAYS call via fn-pointer; null check is eliminated.**

```cpp
// Forward-declare noop fns (defined below)
template <unsigned F> inline void noop_on_entry_fill_log(...);
template <unsigned F> inline void noop_on_exit_fill_log(...);
template <unsigned F> inline void noop_on_exit_calibration(...);

template <unsigned F>
struct OrderManagerState {
    // ... regular fields ...

    // ─── Sink-fn-pointer dispatch (Pattern 5 — branchless optional side-effect emit) ───
    // Default = noop fns; set to real fns at boot when respective subsystems are enabled.
    void (*on_entry_fill_log)(OrderManagerState<F>*, Order<F>*, FPN<F>, FPN<F>, FPN<F>);
    void (*on_exit_fill_log)(OrderManagerState<F>*, Order<F>*, FPN<F>, FPN<F>, FPN<F>, FPN<F>, FPN<F>);
    void (*on_exit_calibration)(OrderManagerState<F>*, Order<F>*, FPN<F>, FPN<F>, FPN<F>, FPN<F>, int);
};

// Noop fns — return immediately; production cost = indirect call (~3-5ns).
template <unsigned F>
inline void noop_on_entry_fill_log(OrderManagerState<F>*, Order<F>*, FPN<F>, FPN<F>, FPN<F>) {}
template <unsigned F>
inline void noop_on_exit_fill_log(OrderManagerState<F>*, Order<F>*, FPN<F>, FPN<F>, FPN<F>, FPN<F>, FPN<F>) {}
template <unsigned F>
inline void noop_on_exit_calibration(OrderManagerState<F>*, Order<F>*, FPN<F>, FPN<F>, FPN<F>, FPN<F>, int) {}

// Real fns — wrap existing body. Set at boot when subsystem Init succeeds.
template <unsigned F>
inline void real_on_entry_fill_log(OrderManagerState<F>* oms, Order<F>* o,
                                    FPN<F> fill_price, FPN<F> fill_qty, FPN<F> entry_fee) {
    TradeEvent<F> synth{};
    synth.price     = fill_price;
    synth.timestamp = o->submitted_at_us;
    synth.core_id   = (uint16_t)o->core_id;
    synth.type      = TRADE_EVENT_ENTRY;
    ShardedTradeLog_RecordEntry(oms->trade_log, synth, o->strategy_id,
                                fill_price, fill_qty, entry_fee, oms->balance);
}

// Boot wiring — at log enable site (e.g., ShardedTradeLog_Init succeeds):
oms->on_entry_fill_log = &real_on_entry_fill_log<F>;
oms->on_exit_fill_log  = &real_on_exit_fill_log<F>;
// Disable site (e.g., test fixtures without log enabled): leave defaults at noop fns.

// OMS_INIT_AUTOPOPULATE defaults (wires noop fns):
oms->on_entry_fill_log    = &noop_on_entry_fill_log<F>;
oms->on_exit_fill_log     = &noop_on_exit_fill_log<F>;
oms->on_exit_calibration  = &noop_on_exit_calibration<F>;

// Callsite (handle_buy_fill / handle_sell_fill):
oms->on_entry_fill_log(oms, o, fill_price, fill_qty, entry_fee);  // branchless dispatch
oms->on_exit_fill_log(oms, o, fill_price, qty_snap, entry_price_snap, net, total_fee);
oms->on_exit_calibration(oms, o, fill_price, qty_snap, entry_price_snap, net, pslot);
```

**Result:** zero data-dependent branches at callsites. Dispatch is deterministic indirect call. Mispredict variance eliminated for this class of optional side effect.

---

## Cost framework

| Mechanism | Cost per call | Variance | When applicable |
|---|---|---|---|
| Branchy `if (state) { ... }` at callsite | 0-1 ns predicted; 30-100 ns mispredict | Variable (predictor-dependent) | H20 exception #4 baseline |
| Sink-fn-pointer (Pattern 5) | 3-5 ns indirect call (deterministic) | None | When optional side effect on SP/HP |

**Branchless wins on:**
- p99 + variance (deterministic always)
- BTB pressure (1 entry per subsystem vs N per callsite)
- Self-documentation (null state is encoded in fn-pointer = noop; obvious from struct field)

**Branch wins on:**
- Pure average (predicted-correctly branch is faster than indirect call)
- Single-callsite cases (one branch < one fn-pointer field + boot wiring)

Per H20 spirit + Caramel's stated principle ("branchless even when slightly slower"): for HFT determinism, the predictability win outweighs the average-cycle cost.

---

## When to apply

Apply when ALL of:
- Optional side effect (logging, telemetry, debug emit, calibration capture) gated by null state check
- Callsite is on slow-path / hot-path / drainer / per-fill / per-tick (variance matters)
- State is set-once at boot (not toggled per-tick; fn-pointer doesn't need atomic update)
- Side effect cannot be cheaply mask-gated via Pattern 3 store-with-mask (writes involve syscalls, fn calls, or are non-idempotent)
- ≥2 callsites for the same optional emit (one callsite doesn't pay back the boot wiring cost)

Skip when:
- Per-tick state toggle — use Pattern 1 dispatch table (enum-indexed) instead
- Side effect is store-only — use Pattern 3 store-with-mask
- Single callsite — inline the null check with `__builtin_expect` per H20 exception #4
- Boot wiring is impractical (e.g., subsystem state changes mid-run; fn-pointer atomic-update needed)

---

## Composition with other patterns

### With Pattern 1 (1D type dispatch table)

ORTHOGONAL + COMPOSABLE. Pattern 1 dispatches on a runtime enum (Order type, strategy enum, etc.); Pattern 5 dispatches on state-enable (subsystem on/off). Both can fire in the same handler:

```cpp
// HandleFill: Pattern 1 on Order type → handle_buy_fill / handle_sell_fill (deterministic)
g_fill_dispatch<F>[Order_GetType(o)](oms, o, fill_price, fill_qty);

// Inside handle_buy_fill: Pattern 5 on trade_log enable (deterministic)
oms->on_entry_fill_log(oms, o, fill_price, fill_qty, entry_fee);
```

### With Pattern 3 (mask-select)

Pattern 5 is the right answer when side effect is a FN CALL with non-idempotent state. Pattern 3 is the right answer when side effect is a STORE that can be mask-gated. They cover different shapes.

### With decision-time-data-binding-pattern.md

The noop fn is the "stub" semantic — always-call + default no-op. Composes with the "second line of defense" (registry-driven per-instance cache) from decision-time-data-binding: noop fn IS the stub for "subsystem not initialized."

### With per-instance-registry-pattern.md

For multi-instance subsystems (per-core log, per-symbol log), fn-pointer becomes per-instance:
```cpp
struct PerCoreState {
    void (*on_fill_log)(...) = &noop_per_core_log<F>;  // per-core enable
};
```

### With multi-state-dispatch-with-per-state-update-metadata.md (per-state side-effect emit)

When optional side effects should fire per certain dispatch states (e.g., per-arm Thompson posterior emission only when Thompson is learning), per-state side-effect bits live in the dispatch enum's X-macro metadata. The Pattern 5 sink-fn-pointer assignment can be DRIVEN by metadata: real_fn for states where the side effect fires, noop_fn for states where it doesn't.

Simpler composition (most common): the Pattern 5 sink-fn-pointer is set by SUBSYSTEM enable (file configured) and fires unconditionally when called; per-state filtering happens INSIDE the real fn (or not at all if the side effect should emit comprehensively). Maximum diagnostic data when subsystem enabled; zero callsite branches.

More complex composition (deferred until 2nd application): per-state fn-pointer table where each state's row metadata picks real_fn or noop_fn:

```cpp
// Hypothetical per-state telemetry emit dispatch — auto-derived from metadata column
#define _TELEMETRY_DISPATCH(name, val, fn, exp3_up, thompson_up, drives, emit_telem, doc) \
    [val] = (emit_telem) ? &real_telemetry_emit<F> : &noop_telemetry_emit<F>,
template <unsigned F>
static constexpr TelemetryEmitFn<F> g_telemetry_dispatch[FOREACH_BANDIT_ALGORITHM_COUNT] = {
    FOREACH_BANDIT_ALGORITHM(_TELEMETRY_DISPATCH)
};
```

Adding a new state with `emit_telem=1` automatically extends the telemetry dispatch table without callsite changes.

See `multi-state-dispatch-with-per-state-update-metadata.md` § "Composition with Pattern 5" for the full pattern body.

---

## Anti-patterns

### Anti-pattern 1: Inline guard with `__builtin_expect` at hot callsites

```cpp
// AVOID at scale (acceptable for ≤2 callsites; per H20 #4 + scope cost)
if (__builtin_expect(oms->trade_log != nullptr, 1)) {
    // ... emit
}
```

Use sink-fn-pointer when the same optional emit appears at 2+ hot callsites.

### Anti-pattern 2: Sink-fn-pointer without boot wiring

```cpp
// FORBIDDEN — defaults must be noop fn (never nullptr)
oms->on_entry_fill_log = nullptr;  // calling crashes
```

Default MUST be the noop fn pointer at all paths. Use `OMS_INIT_AUTOPOPULATE` (or analogous init macro) to wire defaults.

### Anti-pattern 3: Mutating fn-pointer mid-run without atomic discipline

If the subsystem CAN toggle mid-run (live config reload enabling/disabling logging), the fn-pointer update must be atomic (single 8-byte CAS) AND callers must be safe against torn reads. For boot-time-only enable, plain write is fine.

### Anti-pattern 4: Stuffing complex per-call logic into the real fn

The real fn is a TRANSPARENT WRAPPER around the existing emit body. Don't bundle additional logic (state mutation, multi-subsystem coordination) into it — keep it simple so it composes with the noop fn cleanly.

---

## Reference implementations

**Shipped at v5.15.5.F.4c.3 r-6 phase 2 (2026-05-15) — FIRST CANONICAL APPLICATION:**

- `CoreFrameworks/OrderManager.hpp::OrderManagerState<F>::on_entry_fill_emit / on_exit_fill_emit / on_exit_calibration` — 3 fn-pointer fields, default member init = `&noop_fill_emit<F>`
- `CoreFrameworks/OrderManager.hpp::noop_fill_emit<F>` — single noop fn shared across all 3 dispatch slots (matching sig)
- `CoreFrameworks/OrderManager.hpp::real_on_entry_fill_emit / real_on_exit_fill_emit / real_on_exit_calibration` — wrap previous `if (oms->trade_log) { ... }` / `if (oms->calibration_log_file) { ... }` bodies
- **Boot wiring sites** (set fn-pointers to real_* on subsystem enable):
  - `CoreFrameworks/EngineSharded.hpp:712` — after `oms.trade_log = &g_sharded_trade_log;` sets entry + exit log fn pointers
  - `CoreFrameworks/ControllerEventLoop.hpp:1214` — `EventLoopState_AttachTradeLog` sets entry + exit log fn pointers
  - `CoreFrameworks/OrderManager.hpp::OrderManager_OpenCalibrationLog:1447` — after fopen succeeds sets calibration fn pointer
- **Callsites** (always-call via fn pointer; no null check):
  - `CoreFrameworks/OrderManager.hpp::handle_buy_fill` — `oms->on_entry_fill_emit(oms, o, fill_price, fill_qty, entry_fee);`
  - `CoreFrameworks/OrderManager.hpp::handle_sell_fill` — `oms->on_exit_fill_emit(...)` + `oms->on_exit_calibration(...)`

Eliminated 3 callsite branches (`if (oms->trade_log)` × 2 + `if (oms->calibration_log_file)`) in HandleFill body. Net per-fill latency delta: +3-5ns indirect call cost; deterministic (zero variance). Branchless wins on p99 + variance per H20 spirit + Caramel's "branchless even when nominally slower" principle.

---

## Lessons / gotchas

- **Default to noop, never nullptr.** Calling a nullptr fn-pointer crashes; calling a noop fn-pointer is a 3-5ns deterministic no-op. Wire defaults at struct construction.
- **Fn-pointer field placement.** For SP/HP read pressure, place fn-pointer fields in the HOT cluster of the struct. Boot-time-set; per-tick-read.
- **Template fn pointers in C++17.** `&real_fn<F>` is valid in C++17 (template fn-pointer takes a constexpr address). Place fn definitions BEFORE struct that holds the pointer OR forward-declare.
- **Per-template-instantiation.** For `template <unsigned F>` subsystems, each F gets its own real_fn + noop_fn instances. Fn-pointer field type is `void (*)(OmsState<F>*, ...)`; matches the specific F.
- **Debugging tip.** When debugging, set a breakpoint on `noop_*_fn`: if hit, the subsystem is disabled. If real_fn breakpoint hit, subsystem is enabled. Easier than checking state fields.
- **Indirect call cost is REAL (not negligible).** 3-5ns per call adds up over millions of fills/sec. Apply Pattern 5 when determinism gain matters; skip when single-callsite + perf-sensitive.

---

## Audit + prevention

CI / skill enforcement:
- `/hft-audit` extended to detect "optional state null guard at SP/HP callsite" pattern — surfaces sites where Pattern 5 might apply
- `/dod-audit` references this DESIGN_SPEC

Going-forward rule (CLAUDE.local.md, set 2026-05-15 at r-6 phase 2):

> **Sink-fn-pointer for optional side effects on SP/HP.** When an optional side-effect call (logging, telemetry, debug emit, calibration capture) is gated by null state check at ≥2 SP/HP callsites, prefer Pattern 5 sink-fn-pointer (default=noop; set-to-real at boot). Per H20 spirit — branchless preferred for SP/HP data-dependent dispatch EVEN WHEN NOMINALLY SLOWER (indirect call cost ~3-5ns vs predicted-correctly branch ~0-1ns; determinism wins).

---

**Stage 3 ACTIVE v1.0 — promoted 2026-05-15 at v5.15.5.F.4c.3 r-8 ship close.** First canonical application: 3 fn-pointer fields on OmsState (trade_log entry/exit + calibration) eliminating 3 callsite branches in HandleFill body. Sister to Pattern 1/3/4 in `branchless-dispatch-discipline.md`.

**Second canonical application — v5.15.5.F.4d (2026-05-16):** 2 fn-pointer fields on `EnsembleModelZoo<F>` (`thompson_update_fn` + `exit_thompson_update_fn` per `FOREACH_BANDIT_SIDE` auto-mirror; default `&noop_thompson_update`; boot-wired to `&real_thompson_update` at `EnsembleModelZoo_InitThompsonBandits` / `_InitExitThompsonBandits` when subsystem actually initializes). Eliminates `if (thompson_active) Thompson_Update(...)` branches throughout reward-attribution dispatch sites. Composes with `multi-state-dispatch-with-per-state-update-metadata.md` (FOREACH_BANDIT_ALGORITHM `thompson_up` bit → reward dispatch table auto-selects `thompson_only_reward` / `both_reward` leaf fns; both call through the sink-fn-pointer unconditionally). Closes Class 24 sister + Class 28 instances structurally for the reward-attribution dispatch family. Files: `ML_Headers/ThompsonBandit.hpp` (noop/real wrappers + `ThompsonUpdateFn` typedef) + `ML_Headers/CoreModelZoo.hpp` (sink-fn fields + boot wiring) + `ML_Headers/bandit_dispatch_table.hpp` (consumer dispatch via leaf reward fns).

**Two-application milestone** — promotes pattern from "single-canonical" toward "well-established" tier per `pattern-codification-lifecycle.md`. Subsequent applications expected in callsites where optional subsystem callbacks remain branchy (drift-watchdog notify, telemetry capture per-arm history). Going-forward rule (CLAUDE.local.md set 2026-05-15) now has 2 real-world reference points to evaluate "is this a Pattern 5 fit" decisions against.
