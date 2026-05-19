---
type: ledger-template
class_id: 29
title: Silent zero-fee-rate from Order missing pre-resolution binding
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 29 — Silent zero-fee-rate from Order missing pre-resolution binding

**Detected:** 2026-05-15 (during v5.15.5.F.4c.3 WIP2d-1.B.1 architectural audit; surfaced after Class 27 closure exposed the need for an explicit "is this Order's pre_resolved sub-struct bound?" guard at fill time).
**Severity:** HIGH — silent accounting corruption: trade fills with `fee_rate = 0` (FPN default) get accounted as zero-fee, inflating apparent PnL. Cumulative bias. No log message at the silent path; only diagnosable by trade-log post-mortem comparing realized fees against expected `taker_fee × notional` schedule.

### Recurring symptom

After Class 27's structural closure (Order::pre_resolved sub-struct as authoritative source for per-instance cfg values like fee_rate, slippage_pct), any code path that constructs an `Order<F>` MUST call `Order_BindPreResolved(o, core_cfg, ...)` before the Order can flow through HandleFill / DrainPostFill / Reconcile. If a path forgets the binding, the Order arrives at AccountMakerTakerFee with `pre_resolved.fee_rate == FPN<F>{}` (zero). The accounting math runs cleanly with zero — no NaN, no fault, no signal — and books the fill at zero fee. The mistake is invisible until trade-log audit.

Construction sites are scattered:
- Normal entry-order path (`OMS_DrainSubmit` → `OrderManager_TryFill` → `Order_BindPreResolved` ✓)
- Recovery path (`Reconcile_ApplyMissedFills` synthesizes Orders from exchange-reported missed fills)
- Backtest path (`BacktestSharded_PushTick` → `OrderManager_TryFill` ✓)
- Future per-core-N-strategy hot-attach paths (when partial exits add new construction sites)

Each new construction site is a fresh chance to silently forget the binding. Class 18 (Mirror-incomplete) family at the cross-construction-site layer.

Distinct from Class 27 (state-design layer bug — wrong shape of subsystem state). Class 29 is a CONSTRUCTION-SITE bug (right shape; missing call). Class 27's closure SURFACED Class 29 by making the binding mandatory.

### Root cause

Construction-site discipline can't be enforced with a single registry — Orders are constructed from many surfaces (drain, reconcile, backtest, future-strategies) and the binding step is conceptually adjacent to "where the Order is constructed" rather than "where it's consumed." Two compounding patterns:

1. **Out-of-thread-of-attention bindings.** Construction code reads naturally as "fill in the fields"; pre_resolved is one more field that's easy to skip because the Order looks valid without it (default-zero is a valid FPN<F>).
2. **No type-system distinction between bound and unbound Orders.** `Order<F>*` is the same type at every construction site; the C++17 type system can't distinguish "fully bound Order" from "raw Order with empty pre_resolved."

The framing failure: "everything compiles + Order is non-null = good." Class 29 is the canonical "silent-zero" anti-class where defaults are valid-looking but semantically wrong.

### Structural fix

Three-barrier closure landed at `v5.15.5.F.4c.3`:

**Barrier 1: `MASK_ORDER_PRE_RESOLVED` bit (bit 16 of `Order::flags_packed`).** Widened `flags_packed` from uint16 → uint32 to add this bit (cost: 2B per Order; ~0.6% size growth on 256B Order). `Order_BindPreResolved` SETS the bit; default constructor leaves it CLEAR. The bit is the source-of-truth signal "this Order's pre_resolved is bound."

**Barrier 2: `TT_ASSERT_PRE_RESOLVED_BOUND` runtime warn at HandleFill entry.**

```cpp
template <unsigned F>
inline void OrderManager_HandleFill(OrderManagerState<F>* oms, Order<F>* o, FPN<F> fill_price, FPN<F> fill_qty) {
    TT_ASSERT_PRE_RESOLVED_BOUND(o);   // Barrier 2: warn-once if unbound at fill time
    g_fill_dispatch<F>[(uint8_t)Order_GetType(o)](oms, o, fill_price, fill_qty);
}
```

The assert (warn-once + log filename+line of the offending construction site, identified via Order::origin_*) fires at fill time but is non-fatal — production keeps trading even if a binding is forgotten (since fees are accounted to the per-Order pre_resolved, the cost is "fee defaults to 0 instead of crashing"; logging the violation gives ops a fix path without aborting trading). In debug builds, it's a hard assert.

**Barrier 3: Construction-site survey.** All known construction sites in `CoreFrameworks/`, `Backtest/`, `Strategies/` updated to call `Order_BindPreResolved` immediately after Order init. Reconcile's synth path bound; Backtest path bound; DrainSubmit path bound.

```cpp
// Canonical construction-site shape:
Order<F>* o = Portfolio_AllocOrder(/* ... */);
Order_Init(o, /* base fields */);
Order_BindPreResolved(o, core_cfg, /* fee_rate, slippage_pct, ... resolved at decision time */);
// o is now safe to enqueue for HandleFill
```

**FORBIDDEN going-forward:**

```cpp
// FORBIDDEN — Order constructed without Order_BindPreResolved call before enqueue
Order<F>* o = Portfolio_AllocOrder(...);
Order_Init(o, ...);
oms->order_queue.push(o);   // ⚠ pre_resolved unbound; fills will silently book at 0 fee
```

Closed structurally at `v5.15.5.F.4c.3` WIP2d-1.B.1.

### Prevention (going-forward rule + audit + CI)

Codified as a sister rule to Class 27 prevention. Triggers when adding a new Order construction site OR new per-instance cfg field to pre_resolved.

> **Order construction sites must call Order_BindPreResolved before enqueue.** Trigger: any new code path that constructs `Order<F>` and enqueues it for OMS/HandleFill consumption → call `Order_BindPreResolved(o, core_cfg, ...)` immediately after Order_Init / equivalent. Compile-time enforcement awaits C++20 type-stratified Order types (`UnboundOrder<F>` → `BoundOrder<F>`); until then, runtime barrier (TT_ASSERT_PRE_RESOLVED_BOUND) + CI scan + construction-site audit prevent regressions.

Audit skill enforcement:
- `/accounting-audit` (NEW skill at `.F.4c.3`) — scans for Order construction sites + verifies Order_BindPreResolved is the next non-trivial call. First canonical run at WIP2d-1.B.1.b will sweep the codebase.
- `/parity-check` — extended at `.F.4c.3` to verify Order::pre_resolved is non-default at HandleFill entry (parity gate: fail if any path constructs unbound Orders).
- CI Check 8 (NEW; planned at `.F.4d`) — static scan: grep for `Order_Init(` callers, require subsequent `Order_BindPreResolved(` within N lines (or documented exemption).

Anti-pattern grep signatures (for `/accounting-audit` integration):

```bash
# A1: Order construction without subsequent Order_BindPreResolved within 5 lines
rg -nP -A5 'Order_Init\s*\(' --type cpp CoreFrameworks/ Backtest/ Strategies/ | rg -B5 -v 'Order_BindPreResolved'

# A2: Push to OMS queue / fan-out ring without prior binding
rg -nP 'oms.*\.order_queue\.(push|emplace)|fanout_ring\.push' --type cpp CoreFrameworks/
```

False-positive exemptions (documented per case):
- Test-fixture Orders that don't flow through HandleFill (controller_test direct-state setup)
- Diagnostic / introspection Orders (e.g., trade-log replay reconstruction — not enqueued for fills)
- Synthetic Orders in unit tests with explicit `_unbound_for_test = true` marker

### Related classes

- **Class 27** (Scalar cfg-mirror cache) — parent class; closing Class 27 (Order::pre_resolved as authoritative) is what required pre-resolved binding to be a discipline. Class 29 is the runtime-discipline sister of Class 27's structural fix.
- **Class 18** (Mirror-incomplete) — same family; Class 29 is "construction-site mirror incomplete" where new sites forget the binding mirror.
- **Class 14** (Plan API drift) — sister at API-stability; if Order_BindPreResolved signature changes, every construction site must update.
- **Class 28** (Branchy SP/HP dispatch) — sister; both classes closed in the same B.1 commit cluster; Class 29 emerged from Class 27 closure; Class 28 emerged from the same branchless audit.

### Cross-references

- `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` § "Construction-site discipline" — Pattern 4 binding rule
- `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` § "Recovery-path nullable pointer" — Reconcile's binding shape
- `CoreFrameworks/Order.hpp` (post-`v5.15.5.F.4c.3` WIP2d-1.B.1) — `MASK_ORDER_PRE_RESOLVED` bit + `Order_BindPreResolved` helper + `Order_WarnIfNotPreResolved` runtime assert
- `CoreFrameworks/OrderManager.hpp` (post-`v5.15.5.F.4c.3` WIP2d-1.B.1) — `TT_ASSERT_PRE_RESOLVED_BOUND` at HandleFill entry
- CLAUDE.md item 27 + item 29 — pre-resolution discipline references
