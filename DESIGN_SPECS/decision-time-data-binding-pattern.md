# Decision-time data binding pattern

**Established:** 2026-05-15 (v5.15.5.F.4c.3 WIP2d-1.B.0c)
**Status:** Stage 2 DRAFT v1.0 → Stage 3 ACTIVE at `.F.4c.3` ship close
**Tags:** structural-fix, latency, drainer, hot-path-cache, framework-selection; closes Class 27; serves H4 + H6; Stage 2 (DRAFT); 0 applications until `.F.4c.3` ship close
**Cross-references:**
- `cfg-scope-discipline.md` — sister spec (WHERE the field lives); this spec answers WHEN it's READ
- `cache-layout-discipline-for-hot-side-structs.md` — companion (subsystem state layout)
- `hot-side-array-element-alignment-for-sparse-access.md` — composes (per-instance cache fallback layout)
- `postloadsetup-registry-pattern.md` — fallback mechanism integration point
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 27 — the anti-pattern this closes
- CLAUDE.md item 31 — framework discipline meta-principle
- `pattern-codification-lifecycle.md` — Stage 2 → 3 promotion criteria

---

## Problem statement

Per-instance configuration values (per-core fee_rate, per-symbol slippage, per-horizon ML threshold, etc.) need to flow from cfg into per-fill / per-event / per-tick code paths. The naïve approach is to cache cfg values as scalar fields on subsystem state at boot, then read those scalars per fill / per event:

```cpp
// FORBIDDEN — Class 27 anti-shape
struct OrderManagerState {
    FPN<F> fee_rate_maker;   // single scalar; boot-set from cfg.fee_rate_maker
    FPN<F> fee_rate_taker;   // single scalar; boot-set from cfg.fee_rate_taker
    // ...
};

// At boot: oms.fee_rate_maker = cfg.fee_rate_maker;
// Per fill: FPN<F> rate = order->is_maker ? oms->fee_rate_maker : oms->fee_rate_taker;
```

When cfg becomes per-instance (`cfg.cores[c].fee_rate_maker`), the cache silently FLATTENS — every core ends up using core 0's value at every fill, because the cache has no per-instance distinction. Discovered: subsystem caches that mirror cfg as a SCALAR lose their per-instance fidelity the moment cfg grows a per-instance dimension. Catalogued as Class 27.

The class recurs naturally because the "boot-set-from-cfg" pattern is common (~5+ instances across OMS + ConfidenceScorer + PortfolioController + ThompsonBandit state at audit time). Each new mirror that's added flattens silently the moment the cfg surface grows a per-instance axis.

---

## The principle

**Per-instance cfg values bind at decision time and flow forward with the in-flight object, NOT in subsystem state.**

When subsystem A needs cfg value X at moment T, the binding should happen at the EARLIEST point where the relevant instance is known. The value flows forward via the in-flight object (Order, Position, Event, TradeEvent, ...), NOT via cached subsystem state.

### Two lines of defense

**First line (preferred): pre-resolve onto in-flight object.**

The in-flight object knows its own per-instance context (its core_id, symbol, horizon, ...) at creation time. Bind the per-instance cfg value to the object at creation. Downstream consumers read from the object directly — zero cache lookup, zero per-instance distinction lost.

```cpp
// CORRECT — Order carries pre-resolved effective_fee_rate
struct Order {
    uint64_t  id;
    uint8_t   core_id;
    uint8_t   is_maker;
    FPN<F>    effective_fee_rate;   // pre-resolved at submit: is_maker ? cfg.cores[c].fee_rate_maker : cfg.cores[c].fee_rate_taker
    // ...
};

// At Order creation (slow-path; cfg.cores[core_id] in scope):
o->effective_fee_rate = is_maker
    ? cfg.cores[core_id].fee_rate_maker
    : cfg.cores[core_id].fee_rate_taker;

// HandleFill (drainer thread):
FPN<F> entry_fee = FPN_Mul(notional, o->effective_fee_rate);  // zero cache lookup
```

**Second line (fallback): registry-driven per-instance cache.**

When no in-flight object exists (genuinely; not because we forgot to thread one through), the fallback is a per-instance cache on subsystem state. This is rare in practice — most subsystems that need cfg values have an in-flight object available — but the framework exists for the edge cases.

```cpp
// FALLBACK — registry-driven per-instance cache
FOREACH_<SUBSYS>_CFG_CACHE(X)                                                   \
    X(fee_rate_maker,  FPN<F>,  cfg.cores[c].fee_rate_maker)                    \
    X(fee_rate_taker,  FPN<F>,  cfg.cores[c].fee_rate_taker)

// Auto-generates per-instance struct on subsystem state + sync helper +
// accessor + CI cross-check. Composes with postloadsetup-registry-pattern.md
// for cfg-reload hook integration.
```

### When to use which line

| Trigger | Line of defense |
|---|---|
| In-flight object (Order, Position, Event, ...) exists at the binding point AND knows its per-instance context | First line: pre-resolve onto object |
| Subsystem needs cfg value but no in-flight object exists (background task, periodic sweep, init-time setup) | Second line: registry-driven cache (rare) |
| Subsystem caches cfg as a SCALAR and is read per-fill / per-event without per-instance distinction | **FORBIDDEN — Class 27.** Migrate to first or second line. |

### Anti-patterns explicitly FORBIDDEN

**Anti-pattern 1: Scalar cfg-mirror field on per-instance-sharded subsystem state.** Silently flattens per-instance distinction. See Class 27.

**Anti-pattern 2: `static const T cached = FPN_ToDouble(cfg.X);` inside a fn body.** Caches first-cfg-value FOREVER; even less recoverable than a struct field (no syncing path). Detected at EngineSharded:2469 v5.15.5.F.4c.3 sweep.

**Anti-pattern 3: Cross-thread cfg read at fill / event time** (drainer reading slow-path cfg directly per fill). Brittle if cfg ever grows a hot-swap path; safe today only by accident (boot-time-only cfg). Pre-resolution at submit eliminates this concern entirely (rate locked when Order is created).

**Anti-pattern 4: Sync helper called "once at boot" without composing into a postload registry.** When cfg reload arrives, sync is missed. Use `postloadsetup-registry-pattern.md` to ensure cfg-reload paths automatically re-sync caches.

---

## Design space explored

### Option A — Subsystem per-instance arrays + sync helper (PARTIAL)

```cpp
struct OrderManagerState {
    FPN<F> per_core_fee_rate_maker[16];
    FPN<F> per_core_fee_rate_taker[16];
};
OrderManager_SyncFromCfg(oms, cfg);  // populates from cfg.cores[c]
```

- ✓ Fixes the immediate Class 27 instance for OMS fee_rate
- ✗ Doesn't eliminate the CLASS — same shape needed for slippage_pct + ConfidenceScorer + etc.
- ✗ Cache footprint grows (per-core arrays on every affected subsystem)
- ✗ Maintains a mirror — Class 18 adjacent (mirror-incomplete risk if cfg changes)
- Verdict: tactical fix, not class closure

### Option B — Delete OMS cache entirely + direct cross-thread cfg read

```cpp
// HandleFill (drainer):
FPN<F> rate = order->is_maker
    ? cfg.cores[order->core_id].fee_rate_maker
    : cfg.cores[order->core_id].fee_rate_taker;
```

- ✓ No cache to maintain
- ✓ No flatten risk
- ✗ Cross-thread cfg read at fill time (drainer reading slow-path-owned cfg)
- ✗ Brittle if cfg grows a hot-swap path (need seqlock or similar then)
- ✗ Doesn't generalize to subsystems whose caller doesn't have cfg in scope
- Verdict: works today by accident (boot-time cfg); brittle long-term

### Option C — Pre-resolve onto in-flight object (CHOSEN)

```cpp
// Slow-path (cfg in scope, knows core_id, knows is_maker at Order creation):
o->effective_fee_rate = is_maker
    ? cfg.cores[core_id].fee_rate_maker
    : cfg.cores[core_id].fee_rate_taker;

// HandleFill (drainer):
FPN<F> rate = o->effective_fee_rate;
```

- ✓ Zero cache lookup at fill time (latency win)
- ✓ No flatten risk (per-instance binding at creation)
- ✓ Hot-swap-safe by construction (in-flight Orders keep their rate; new Orders get new rate — correct semantic)
- ✓ Self-contained accounting record (Order carries everything for reconciliation)
- ✓ Generalizes to ANY subsystem with an in-flight object (Position, Event, TradeEvent, ...)
- Costs: in-flight object struct grows (Order +24B for `effective_fee_rate`); needs static_assert layout verification
- Verdict: structural closure of the CLASS

### Option D — `FOREACH_SUBSYSTEM_CFG_CACHE` registry as primary mechanism (REJECTED as PRIMARY; kept as FALLBACK)

- ✓ Mechanicalizes cache addition
- ✗ Optimizes for ADDING caches when the right answer is ELIMINATING them
- ✗ Cargo-cult risk — future contributors add registry rows when pre-resolution is better
- Verdict: kept as second-line fallback for genuinely-no-in-flight-object cases; not primary

---

## Why pre-resolution closes the class structurally

The CLASS (Class 27) is: scalar cfg-mirror caches lose per-instance fidelity. Pre-resolution attacks the root: there IS NO CACHE to flatten. The Order carries its own value. The subsystem state field is DELETED.

Compile-time / type-system enforcement:
- Order struct gains `effective_fee_rate`; subsystem state struct LOSES `fee_rate_maker` / `fee_rate_taker` fields
- Any code path that used to read `oms->fee_rate_maker` now compile-fails — caught at build, not at runtime accounting
- New scalar cfg-mirror fields on subsystem state are caught by CI Check 7 (subsystem-state cfg-mirror scan) — see `tools/check_per_core_registry_integrity.py`

The combination — delete current instances + CI prevents new ones + DESIGN_SPEC as operator/reviewer reference — is structural enforcement, not discipline-only.

---

## Reference implementations

Populated at Stage 3 ACTIVE — shipped sites get file:line refs back-linked here.

- (pending) `CoreFrameworks/Order.hpp` — `OrderPreResolved<F>` sub-struct (fee_rate + slippage_pct) + `Order_BindPreResolved(o, core_cfg)` helper; first canonical sub-struct refinement (.F.4c.3 WIP2d-1.B.1)
- (pending) `CoreFrameworks/OrderManager.hpp` — HandleFill reads `o->pre_resolved.fee_rate` (zero OMS cache lookup); OMS scalar fee_rate/maker/taker/slippage_pct fields DELETED (.F.4c.3 WIP2d-1.B.1)
- (pending) `CoreFrameworks/ControllerEventLoop.hpp` — slow-path direct `cfg.cores[c]` reads (.F.4c.3 WIP2d-1.B.2)
- Already exists (recognized retroactively): `Portfolio<F>::positions[slot].entry_fee` — Position carries entry_fee pre-resolved at open; this pattern existed pre-codification; named "decision-time-data-binding" by analysis at .F.4c.3
- Already exists (recognized retroactively): `TradeEvent<F>::intended_tp` / `intended_sl` — Event carries intended values pre-resolved at gate fire

## Sub-struct refinement (preferred shape for ≥2 pre-resolved fields)

When the in-flight object accumulates ≥2 pre-resolved values, group them into a NAMED SUB-STRUCT rather than flat fields. The sub-struct is strictly better than flat fields on three axes (with identical memory layout + zero runtime cost):

1. **Semantic clustering** — all decision-time-bound values visually grouped; reader immediately sees "these are the pre-resolved values, not live cfg reads"
2. **Extension point** — adding a new pre-resolved field = 1 line in the sub-struct + extend the binding helper; consumer sites unchanged
3. **API-level discipline** — the binding helper (`<Object>_BindPreResolved(o, core_cfg)`) is the EXPLICIT "pre-resolve happens HERE" call; prevents forgetting to bind one of the fields when adding a new one

Canonical shape (Order<F> example):

```cpp
template <unsigned F>
struct OrderPreResolved {
    FPN<F> fee_rate;       // pre-resolved at submit: is_maker ? maker_rate : taker_rate
    FPN<F> slippage_pct;   // pre-resolved per-core
    // Future per-resolved fields extend here mechanically:
    // - effective_kill_switch_threshold (per-core risk envelope at submit time)
    // - effective_min_holding_ticks (per-core time-exit floor)
    // - effective_intended_strategy_dispatch (pre-resolved dispatch arm)
};

template <unsigned F>
struct Order {
    // ... HOT identity + intent fields ...
    OrderPreResolved<F> pre_resolved;  // 48B at end of HOT cluster; future extension point
    // ... COLD cluster ...
};

template <unsigned F>
inline void Order_BindPreResolved(Order<F>* o, const PerCoreCfg<F>& core_cfg) {
    bool is_maker = Order_GetIsMaker(o);
    o->pre_resolved.fee_rate = is_maker
        ? core_cfg.fee_rate_maker
        : core_cfg.fee_rate_taker;
    o->pre_resolved.slippage_pct = core_cfg.slippage_pct;
    // Future bindings extend here in lockstep with OrderPreResolved fields
}
```

Consumer reads (HandleFill, drainer thread):
```cpp
FPN<F> entry_rate = o->pre_resolved.fee_rate;        // semantically clear
FPN<F> slip_pct   = o->pre_resolved.slippage_pct;    // self-documenting
```

vs the flat-field alternative (`o->effective_fee_rate`, `o->effective_slippage_pct`) which is functionally equivalent but loses the semantic grouping + API-level discipline anchor.

### When to introduce the sub-struct

- **Stage 1 single field**: flat field on in-flight object is fine. No premature sub-struct.
- **Stage 2 second field added**: refactor to sub-struct AT THAT POINT. The second addition is when the grouping pays off.
- **Stage 3 ≥3 fields**: sub-struct is mandatory; `<Object>_BindPreResolved` helper is mandatory.

Order<F> at v5.15.5.F.4c.3 enters at Stage 2 (fee_rate + slippage_pct simultaneously). The sub-struct + helper are introduced at the same commit.

### Cross-references

- `cache-layout-discipline-for-hot-side-structs.md` — sub-struct placement within HOT/WARM/COLD clusters
- `decision-first-cluster-layout-pattern.md` — sub-struct placement within HOT cluster (decision-relevant fields toward front; pre-resolved values can sit at end-of-HOT since they're READ after dispatch decision)
- `function-struct-alignment-for-single-mov-access.md` — sub-struct alignment for cache-friendly access

---

## Trade-offs + when to apply

**Apply when:**
- Subsystem A caches cfg scalar values that are/could-become per-instance
- In-flight object exists at the decision point with per-instance context known
- Accounting / wire-format / safety-critical paths (where flatten bugs are unacceptable)

**Skip when:**
- Cfg value is genuinely global engine-wide (`num_execution_cores`, `engine_mode`) — no per-instance distinction to lose
- Subsystem has no in-flight object AND value is uniform across instances by design

**Cost:**
- In-flight object struct grows (per pre-resolved field; typically 8-24B depending on type)
- Slow-path / decision-path gains one assignment per object creation
- Static_assert layout verification per new field

**Win:**
- Class 27 closure at this site (no scalar cache to flatten)
- Net latency improvement on the read path (zero cache lookup vs cmov + 1-2 cache line loads today)
- Hot-swap safety by construction
- Self-contained accounting reconciliation (object carries its own context)

---

## Framework-selection meta-principle

This DESIGN_SPEC is the canonical example of a sub-principle worth codifying:

> **Registries optimize for ADDING MORE of a pattern. When the right answer is to STOP HAVING the pattern, a principle + audit + delete is better than a registry.**

Decision matrix:

| Pattern characteristic | Reach for |
|---|---|
| N items share structure + multi-site addition is recurring + N is GROWING | Registry (X-macro / FOREACH_X) |
| Pattern shouldn't exist or should be ELIMINATED | Principle + audit + delete + CI |
| Mix: some instances genuine + most should be eliminated | Principle PRIMARY + registry as fallback for the rare genuine instances |

Class 27 fits the third row: most "subsystem cfg mirrors" should become Order-pre-resolved (eliminated); the rare cases where no in-flight object exists fall back to `FOREACH_SUBSYSTEM_CFG_CACHE`. Principle + sweep + CI is the primary mechanism; registry is vestigial.

Codified in `DOCS/DESIGN_PHILOSOPHY.md` § 11 sub-section "Framework-selection criteria" and CLAUDE.md item 31 amendment.

---

## Lessons / gotchas

- **In-flight object alignment matters.** `Order` is in a SPSC ring buffer; growing it by 24B may push it across a cache line boundary. Verify via `static_assert(sizeof(Order<F>) ...)` + `static_assert(offsetof(Order<F>, effective_fee_rate) ...)`. If alignment cost is non-trivial, consider sub-struct packing (`OrderPreResolved` sub-struct).
- **The retroactive recognition pattern.** Position.entry_fee already followed this principle pre-codification. Codifying the principle let us NAME what was already working — and apply it deliberately to new surfaces. Worth scanning the codebase for other retroactive applications when the spec promotes to Stage 3.
- **Cross-thread cfg read brittleness is masked by boot-time-only cfg today.** If a future hot-swap path is added without pre-resolution discipline, accounting can briefly use mixed rates. Pre-resolution at decision time sidesteps the entire concurrency question.
- **Don't reach for the registry mechanism first.** The registry was the first impulse during design; the principle was the second. Naming the principle first lets us see when the registry isn't actually needed.

---

## Stage 3 ACTIVE amendments (added at v5.15.5.F.4c.3 r-8 ship close, 2026-05-15)

### Lesson: downstream consumer READS canonical value, never recomputes from cfg

**The recompute-from-cfg anti-pattern** — discovered during `.F.4c.3` r-4 when 2 failing tests pointed at a real architectural gap:

`DrainPostFillOneCore` was RECOMPUTING `exit_fee = exit_notional * cfg_lookup(fee_rate_maker_or_taker)` even though `HandleFill SELL` had ALREADY computed the authoritative `exit_fee` from `o->pre_resolved.fee_rate`. The recompute-from-cfg path loses authority over edge cases:

- **Per-core variation**: post-Class 27 closure, cfg has per-core fee_rate. Recompute-from-cfg path got wrong fee for cross-core fills.
- **Hot-swap timing**: if cfg reloads mid-trade (future hot-swap), recompute uses NEW cfg rate for OLD trade's accounting.
- **Authority duplication**: 3-place compute (HandleFill BUY, HandleFill SELL, DrainPostFill) → drift risk.

**Pattern**: downstream consumers READ canonical value from authoritative storage; never recompute.

**Implementation pattern**: HandleFill SELL writes `oms->last_exit_fee[pslot] = exit_fee` (sibling array; SoA layout); DrainPostFill reads `oms->last_exit_fee[slot]`. ONE compute (at decision time, from Order pre_resolved) + N reads (downstream consumers). Sister to existing `last_exit_fill_price[pslot]` pattern.

**When to apply**: any downstream consumer of a fill / event / position lifecycle that's tempted to recompute. Reach for the sibling-array-read pattern instead.

**First canonical**: `CoreFrameworks/OrderManager.hpp::handle_sell_fill` writes `oms->last_exit_fee[pslot]`; `CoreFrameworks/ControllerEventLoop.hpp::EventLoop_DrainPostFillOneCore` reads. Closes a latent correctness bug + simplifies (no cfg-threading needed at DrainPostFill wrapper).

### Compose with Pattern 5 (sink-fn-pointer)

The `noop_fill_emit` fn from `sink-fn-pointer-for-optional-side-effect-pattern.md` is the canonical "stub" semantic — always-call, default no-op. Composes with decision-time-data-binding's "second line of defense" stub pattern:

- **Decision-time-data-binding stub**: per-instance cfg cache fallback when no in-flight object exists (rare case; second line of defense)
- **Pattern 5 noop fn stub**: optional side-effect emit when subsystem is disabled (always-call, default no-op)

Both express the same shape: an always-callable sentinel that defaults to no-op + can be set to real on enable. Distinct domains; shared shape.

### Scope boundary — Pattern 4 doesn't apply to dispatch-state enums (added v5.15.5.F.4c.4)

Pattern 4 pre-resolves per-instance cfg VALUES onto in-flight objects (Order, Position, Event, TradeEvent) at decision time, where the object knows its per-instance context (core_id, symbol, horizon). The downstream consumer reads from the object — zero cache lookup, zero per-instance distinction lost.

This works for SCALAR cfg values that the in-flight object can carry: `effective_fee_rate`, `effective_slippage_pct`, `effective_kill_switch_threshold`. The object is the natural carrier because:
- It exists at decision time (Order created in slow-path with cfg in scope)
- It carries one value per instance (one rate per Order)
- The consumer (HandleFill, DrainPostFill) reads from the object on its hot/drainer path

Pattern 4 does NOT apply when the per-instance cfg value is a **dispatch-state enum** that selects a DIFFERENT consumer fn — e.g., `cfg.cores[c].bandit_algorithm` selects which bandit algorithm runs for core c's reward attribution. The bandit-algorithm choice happens BEFORE any in-flight Order is created (at slow-path-rebuild time when ML_BuildParameters runs); no Order to pre-resolve onto. The dispatch happens at reward-attribution time on the slow path with `cfg.cores[c].bandit_algorithm` in scope.

The right shape for dispatch-state enums:
- Cfg value lives in `FOREACH_PER_CORE_CFG_FIELD` per `cfg-scope-discipline.md` default-per-core rule
- Consumer reads `core_cfg->bandit_algorithm` via single-param `const PerCoreCfg<F>*` sig (Class 25 prevention)
- Dispatch via Pattern 1 fn-pointer table indexed by the enum value (per `branchless-dispatch-discipline.md`)
- For multi-state asymmetric dispatch, compose with `multi-state-dispatch-with-per-state-update-metadata.md` (auto-derived dispatch table from row metadata)

So: Pattern 4 for SCALAR per-instance values that flow forward with an in-flight object; Pattern 1 + multi-state-dispatch + cfg-scope-discipline for DISPATCH-STATE enums that select consumer behavior at slow-path-rebuild time. Distinct shapes; both branchless; both per-core via direct registration (no override mechanism).

---

### Stage 3 amendment v1.1 — Sibling-array family canonical (added 2026-05-16 at v5.15.5.F.4c.4)

The sibling-array variant (sister to in-flight-object sub-struct expansion) has accumulated **7 canonical applications** at the `.F.4c.4` retroactive recognition + grow-to-6-OMS-cluster work:

| # | Canonical | Site | Set at | Read at |
|---|---|---|---|---|
| 1 | `Position::entry_fee` | `Portfolio<F>::positions[slot].entry_fee` | HandleFill BUY (decision time for entry side) | calib emit + post-fill consumers |
| 2 | `oms->per_slot.last_realized_return[pslot]` | OmsPerSlotContext sub-struct (retroactively recognized at `.F.4c.4`) | HandleFill SELL | Aggregate calculations + sweep loops |
| 3 | `oms->per_slot.last_exit_fill_price[pslot]` | Same OmsPerSlotContext cluster | HandleFill SELL | calib emit + post-fill |
| 4 | `oms->per_slot.last_exit_fee[pslot]` | Same cluster (originally `.F.4c.3` r-4 canonical; named-cluster refactored at `.F.4c.4`) | HandleFill SELL (decision time for exit side) | DrainPostFill + calib emit |
| 5 | `oms->per_slot.last_exit_predicted_p[pslot]` | Same cluster (retroactively recognized) | HandleFill SELL | calib emit body |
| 6 | `oms->per_slot.last_exit_predicted_meta[pslot]` | Same cluster (retroactively recognized) | HandleFill SELL | calib emit body |
| 7 | `oms->per_slot.bandit_reward_bps[pslot]` | Same cluster (NEW `.F.4c.4`) | HandleFill SELL (just before calib emit) | calib emit body |

### Cohort threshold reached → `FOREACH_OMS_PER_SLOT_FIELD` registry primitive

With 6 sibling arrays in the OmsPerSlotContext named cluster, the cohort-threshold (4+ siblings) is met per framework-selection-criteria (CLAUDE.md item 31). The sibling-array variant family promotes to a registry primitive at `.F.4c.4`:

```cpp
// CoreFrameworks/OrderManager.hpp — FOREACH_OMS_PER_SLOT_FIELD canonical
#define FOREACH_OMS_PER_SLOT_FIELD(X)                                                                            \
    X(last_realized_return,     FPN<F>,    "Realized return at HandleFill SELL")                                  \
    X(last_exit_fill_price,     FPN<F>,    "Exit fill price at HandleFill SELL")                                  \
    X(last_exit_fee,            FPN<F>,    "Exit fee from Order pre_resolved (Pattern 4 canonical .F.4c.3 r-4)")  \
    X(last_exit_predicted_p,    double,    "Predicted exit probability at HandleFill SELL")                       \
    X(last_exit_predicted_meta, uint16_t,  "Predicted exit meta flags at HandleFill SELL")                        \
    X(bandit_reward_bps,        double,    "Bandit reward attribution at HandleFill SELL (.F.4c.4)")

#define EMIT_PER_SLOT_FIELD(name, type, doc) type name[MAX_PORTFOLIO_POSITIONS];
template <unsigned F>
struct alignas(64) OmsPerSlotContext {
    FOREACH_OMS_PER_SLOT_FIELD(EMIT_PER_SLOT_FIELD)
    uint8_t _padding_oms_per_slot[32] = {0};  // explicit trailing padding for 64-byte cluster boundary
};
#undef EMIT_PER_SLOT_FIELD
static_assert(sizeof(OmsPerSlotContext<64>) % 64 == 0, "OmsPerSlotContext must be 64-byte multiple");
```

Future per-slot decision-time-bound additions = 1 row in `FOREACH_OMS_PER_SLOT_FIELD` mechanical. Enrolled in `FOREACH_REGISTRY` meta-registry per H15 (CI gate `tools/check_meta_registry.py` enforces).

### Sweep loop discipline note (SoA wins for our access pattern)

OmsPerSlotContext uses SoA (Struct-of-Arrays) layout despite AoS marginally winning at single-slot read (per-trade emit ~5-15ns saved). Workload-weighted analysis at `.F.4c.4`:

- Per-trade calib emit (~0.05 Hz): AoS saves ~5-15ns per emit; total ~1ns/sec at typical cadence
- Sweep loops over single field × all slots (~5 Hz at slow-path-rebuild): SoA saves ~50-150ns per sweep; total ~500ns/sec at typical cadence

**Net latency: SoA wins by ~499ns/sec at typical trading tempo.** AoS reserved for cases where single-slot access dominates frequency (e.g., Position struct — one per slot, accessed as a unit at trade lifecycle events).

**Shape definition (sibling-array variant family):**

```cpp
// Owning subsystem state struct (Portfolio, OmsState, etc.) declares NAMED sub-struct
// holding per-slot decision-time-bound data. alignas(64) on the sub-struct preserves
// cache discipline. Sibling array of size MAX_PORTFOLIO_SLOTS (or analogous) per field.

template <unsigned F>
struct OwnerPerSlotDecisionContext {  // Example: OmsPerSlotDecisionContext, PortfolioPerSlotEntry, ...
    FPN<F>  field1[MAX_PORTFOLIO_SLOTS];  // decision-time-bound at one event
    double  field2[MAX_PORTFOLIO_SLOTS];  // decision-time-bound at another event
    // Future per-slot decision-time-bound additions = 1 row here mechanical
};

template <unsigned F>
struct OwnerState {
    // ... HOT cluster ...
    alignas(64) OwnerPerSlotDecisionContext<F> per_slot_decision;
    // ... rest ...
};

// Write at decision time (single-source-of-truth event):
oms->per_slot_decision.field1[pslot] = value_at_decision_time;

// Read at downstream consumer time (NEVER recompute):
value = oms->per_slot_decision.field1[pslot];
```

**When to apply sibling-array variant vs in-flight-object sub-struct variant:**

| Variant | Use when... |
|---|---|
| **In-flight-object sub-struct** (e.g., `Order::pre_resolved`) | Object has its own lifecycle that flows through multiple consumers (Order: Submit → Fill → Cancel). Multiple consumers each read from the object on its path. Sub-struct refinement Stage 1 → 2 → 3 on the object. |
| **Sibling-array on owning subsystem** (e.g., `oms->per_slot_decision.X[]`) | Subsystem owns a slot lifecycle with single decision-time write + single (or few) downstream consumer reads in same slot lifecycle (HandleFill BUY → HandleFill SELL → calib emit). Slot index is the natural key. |
| **Both** can apply to different fields on same subsystem (e.g., Order::pre_resolved.fee_rate flows with Order; OmsState's last_exit_fee flows per-slot) — each field picks its best variant by lifecycle. |

### Stage 3 amendment v1.2 — Multi-bit-state-encoding bit-pack on existing struct field as Pattern 4 carrier (added 2026-05-16 at v5.15.5.F.4c.4)

**Sister Pattern 4 carrier mechanism** discovered at `.F.4c.4`: when at-decision-time fields are small K-state values (e.g., 3 enums each fitting in 3 bits), they can be bit-packed into an EXISTING struct field on the in-flight object, sister to an existing canonical bit on the same field.

**First canonical:** Order::flags_packed bandit context bits at `.F.4c.4` (sister to existing `MASK_ORDER_PRE_RESOLVED` bit at the same field per `.F.4c.3`). Saves Order layout disruption that sub-struct expansion would cause; composes with `multi-bit-state-encoding-pattern.md` (also at Stage 3 promotion).

**Shape:** existing uint32_t field on the in-flight object; manual SHIFT_*/MASK_* allocation; MBS_*-named branchless accessors per H14:

```cpp
// Bit allocation documented at struct definition site
constexpr int SHIFT_OBJ_<FIELD> = N;
constexpr uint32_t MASK_OBJ_<FIELD>_<KBIT> = ...;
inline int MBS_Obj<Field>(const Obj& o) {
    return (o.existing_packed_field >> SHIFT_OBJ_<FIELD>) & MASK_OBJ_<FIELD>_<KBIT>;
}
inline void MBS_ObjSet<Field>(Obj* o, int value) {
    constexpr uint32_t CLEAR_MASK = ~(MASK_OBJ_<FIELD>_<KBIT> << SHIFT_OBJ_<FIELD>);
    o->existing_packed_field = (o->existing_packed_field & CLEAR_MASK) |
        ((uint32_t)(value & MASK_OBJ_<FIELD>_<KBIT>) << SHIFT_OBJ_<FIELD>);
}
```

**When to apply this variant vs sub-struct expansion:**

| Variant | Use when... |
|---|---|
| **Bit-pack into existing packed field** | At-decision-time values are small K-state enums (≤8 values fits 3 bits; ≤16 fits 4 bits); existing packed field has free bits; struct size invariant is load-bearing (would break if grown) |
| **Sub-struct expansion** | At-decision-time values include scalars that can't bit-pack (FPN<F>, double, large ints); OR struct doesn't have an existing packed field with free bits; OR there are ≥3 fields and a sub-struct is structurally clearer |

**Composition:** the two variants can co-exist on the same in-flight object. Example: `Order::pre_resolved` sub-struct for fee_rate/slippage_pct (scalars; HOT cluster) + `Order::flags_packed` bit-pack for bandit context (small enums; same field as existing canonical bit).

---

**Stage 3 ACTIVE v1.2 — promoted 2026-05-15 at v5.15.5.F.4c.3 r-8; sibling-array family canonical + bit-pack carrier variant added 2026-05-16 at v5.15.5.F.4c.4.** Three Pattern 4 carrier variants documented: (1) in-flight-object sub-struct refinement (Order::pre_resolved), (2) sibling-array on owning subsystem (OmsPerSlotDecisionContext), (3) bit-pack into existing packed field on in-flight object (Order::flags_packed bandit context).
