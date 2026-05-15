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

- (pending) `CoreFrameworks/OrderManager.hpp` — Order `effective_fee_rate` + `effective_slippage_pct` field; HandleFill simplification (.F.4c.3 WIP2d-1.B.1)
- (pending) `CoreFrameworks/ControllerEventLoop.hpp` — slow-path direct `cfg.cores[c]` reads (.F.4c.3 WIP2d-1.B.2)
- Already exists (recognized retroactively): `Portfolio<F>::positions[slot].entry_fee` — Position carries entry_fee pre-resolved at open; this pattern existed pre-codification; named "decision-time-data-binding" by analysis at .F.4c.3
- Already exists (recognized retroactively): `TradeEvent<F>::intended_tp` / `intended_sl` — Event carries intended values pre-resolved at gate fire

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
