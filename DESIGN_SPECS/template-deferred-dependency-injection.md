# Template-deferred dependency injection (logic header preserves I/O-free boundary)

**Established:** 2026-05-09 (v5.14.4.B; multi-mode reconciliation `Reconcile_AutoCancelStale`)
**Status:** ACTIVE
**Cross-references:**
- CLAUDE.local.md "Going-forward rule: prefer boundary-stable refactors over wide cascades" (sister principle)
- `audit-driven-pre-coding-gate.md` (this pattern emerged from `/trace-deps` audit caught Reconcile.hpp logic-only-contract concern)
- `Reconcile.hpp` (canonical first reference: `Reconcile_AutoCancelStale<F, CancelFn>` template)
- `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.4-multi-mode-reconciliation.md` (Option E decision)

---

## Problem statement

Some headers in this codebase carry a **logic-only contract** — they implement business logic, deterministic math, or pure transformations, and MUST NOT introduce I/O dependencies (network, filesystem, OS), because doing so would:
1. Break testability (mocks become invasive)
2. Pollute include graphs (network primitives carry heavy transitive includes)
3. Couple deterministic logic to side-effecting code
4. Break boundary-stable refactor invariants (per CLAUDE.local.md)

Example: `CoreFrameworks/Reconcile.hpp` is a logic-only header — it decides WHAT reconciliation actions are needed (apply missed fills, cancel stale orders, refuse boot on disagreement) based on the engine's current OMS state vs. exchange-reported state. The DECISION is pure; the ACTIONS (network DELETE /api/v3/order calls) require I/O.

A naive approach is to either:
- **Option A:** Put the I/O primitive call directly in Reconcile.hpp → contract broken; logic-only invariant lost; downstream consumers (tests, backtest replay) now need to mock network calls.
- **Option B:** Split the function across two headers — logic in Reconcile.hpp, I/O wiring in a separate ReconcileExecute.hpp → file proliferation; the split feels arbitrary because the two halves are tightly coupled.

There's a third option that's structurally cleaner: **pass the I/O primitive as a template-deferred callable** — caller injects the side-effect at the call site via lambda/function pointer/std::function.

## Design space explored

### Option A: Direct call (BAD — breaks logic-only contract)

```cpp
// Reconcile.hpp
template <int F>
int Reconcile_AutoCancelStale(OMS<F>* oms, const ReconcileTrade* trades, int n) {
    for (int i = 0; i < n; ++i) {
        if (trade_is_stale(trades[i])) {
            int rc = BinanceOrderAPI_CancelOrder(trades[i].order_id);  // !!! I/O dep !!!
            if (rc != 0) return -1;
        }
    }
    return 0;
}
```

**Cost:** Reconcile.hpp now transitively includes BinanceOrderAPI.hpp (curl, signed request, async retry queue, etc.). Tests can't run without network mocks. Replay paths break.

### Option B: Split into separate header (acceptable but file-proliferating)

```cpp
// Reconcile.hpp — logic only
template <int F>
struct ReconcileDecision {
    int n_to_cancel;
    OrderID to_cancel[MAX_RECONCILE];
};

// ReconcileExecute.hpp — I/O bridge
#include "Reconcile.hpp"
#include "BinanceOrderAPI.hpp"
template <int F>
int ReconcileExecute_AutoCancelStale(...) {
    auto decision = Reconcile_DecideCancellations(...);
    for (int i = 0; i < decision.n_to_cancel; ++i) {
        BinanceOrderAPI_CancelOrder(decision.to_cancel[i]);
    }
}
```

**Cost:** Two header files for one logical operation. The split is arbitrary — both halves are called as one operation 100% of the time. File proliferation without modularity benefit.

### Option E (chosen): Template-deferred dependency injection

```cpp
// Reconcile.hpp — logic only; CancelFn is a template parameter
template <int F, typename CancelFn>
int Reconcile_AutoCancelStale(OMS<F>* oms, const ReconcileTrade* trades, int n,
                              CancelFn cancel_fn) {
    for (int i = 0; i < n; ++i) {
        if (trade_is_stale(trades[i])) {
            int rc = cancel_fn(trades[i].order_id);  // call-site-injected
            if (rc != 0) return -1;
        }
    }
    return 0;
}
```

**Call site (engine boot, sharded path):**
```cpp
auto cancel_fn = [](OrderID id) -> int {
    return BinanceOrderAPI_CancelOrder(id);
};
int rc = Reconcile_AutoCancelStale(oms, trades, n, cancel_fn);
```

**Test call site (mock network):**
```cpp
int mock_calls = 0;
auto cancel_fn = [&](OrderID id) -> int {
    mock_calls++;
    return 0;  // simulate success
};
int rc = Reconcile_AutoCancelStale(oms, trades, n, cancel_fn);
check("mock cancel called 3 times", mock_calls == 3);
```

**Backtest call site (no-op or replay):**
```cpp
auto cancel_fn = [](OrderID id) -> int { return 0; };  // backtest doesn't cancel
int rc = Reconcile_AutoCancelStale(oms, trades, n, cancel_fn);
```

### Decision: Option E

Preserves logic-only contract (Reconcile.hpp doesn't include BinanceOrderAPI.hpp). Same shape across all callers (live boot, test, backtest). No file proliferation. Caller has full control over the side-effect — no abstraction layer hides what's happening at the I/O boundary.

The pattern was named "Option E" in the v5.14.4 plan because Options A-D were earlier-considered shapes (direct call, header split, std::function pointer, virtual interface). E won on "preserves contract + symmetric across callers + no abstraction overhead."

## The pattern (concrete shape)

### Template signature

```cpp
template <int F, typename Fn>
ReturnType LogicFn_Name(StateType<F>* state, /* logic args */, Fn side_effect) {
    // Pure decision-making logic
    if (condition_to_trigger_side_effect) {
        int rc = side_effect(side_effect_args);
        if (rc != 0) return ERROR;
    }
    return SUCCESS;
}
```

### Constraints on `Fn`

- Must be **callable** with the expected argument signature (`int(OrderID)` in the Reconcile example)
- Should return a **status code** that the logic header can react to (success/failure)
- **Stateless or stateful** — both work; lambda captures are fine but the logic header doesn't care

### When the callable should/shouldn't return data

If `side_effect` produces a value the logic needs (e.g., "did the cancel succeed AND was the order found?"), the callable should return that data via:
- Status int with semantic meaning (-1 = error, 0 = success, 1 = "no-op, already gone")
- Output parameter (`Fn cancel_fn(OrderID id, bool* was_found)`)
- Pair / struct return type (`Fn cancel_fn(OrderID id) -> Result`)

The third form (struct return) is cleanest but requires defining the result type at the logic-header level. The first form (status int) is least cluttered but limits the data flow.

## Trade-offs + when to apply

**Apply when:**
- Logic header has a load-bearing logic-only contract (no I/O dependencies; testable in isolation; replay-deterministic)
- The side-effect is a small, well-defined primitive (single call; well-typed inputs/outputs)
- The side-effect is called inside a logic loop (Reconcile pattern: decide what to cancel → loop → call cancel_fn)
- Multiple callers need different side-effect behavior (live = real network, test = mock, backtest = no-op)

**Skip when:**
- The side-effect is so complex it deserves its own header anyway → split via Option B
- The logic doesn't need the side-effect's return value → consider passing a callback that's a STORE (logic decides; caller executes after returning the decision)
- Only ONE caller will ever exist → direct call is simpler; YAGNI applies
- The side-effect requires complex state that lambda capture would make awkward → use functor object instead of lambda

**Cost:**
- ~5-10 LOC per template-parameterized function (vs. direct call); negligible
- One extra include path consideration (logic header includes nothing extra; call site includes BOTH)
- Compile-time cost: 1 template instantiation per call site (small for header-only design)

**Win:**
- Logic-only contract preserved (testability, replay-determinism, include-graph cleanliness)
- Same shape across live / test / backtest callers (no special-case branching)
- No abstraction overhead at runtime (lambda inlines; same machine code as direct call after optimization)
- File count stays small (no logic/execute split)

## Reference implementations

- **First applied (canonical reference):** v5.14.4.B.2 (commit in v5.14.4 umbrella) — `CoreFrameworks/Reconcile.hpp:Reconcile_AutoCancelStale<F, CancelFn>`.
- **Symmetric sister application:** v5.14.4.B.1 — `Reconcile_ApplyMissedFills<F>` uses the SAME template-deferred shape for `OrderManager_HandleFill` (logic header takes the fill-application primitive as a template parameter). Both halves of the multi-mode reconciliation flow use the pattern.
- **Subsequent uses:** None yet (pattern is documented for future logic-only-contract preservation cases).

## Lessons / gotchas

1. **The pattern emerged from an audit, not from the original plan.** v5.14.4 plan's original Option A was direct call (Reconcile.hpp would include BinanceOrderAPI.hpp). `/trace-deps` audit caught the include-graph contamination + the logic-only-contract break. The fix was structural (Option E), not a band-aid. Per CLAUDE.md item 19 (structural fix preferred): audit-time discovery of contract concerns triggers the structural fix, not the patch.

2. **Symmetric application across sister functions matters.** `Reconcile_ApplyMissedFills` and `Reconcile_AutoCancelStale` both use the template-deferred pattern. If only one used it, the asymmetry would feel like accidental complexity. Apply consistently across related functions in the same header.

3. **Lambda capture is fine; functor objects are fine; std::function adds overhead.** The pattern doesn't require `std::function<int(OrderID)>` — that adds heap allocation + virtual dispatch overhead. Plain template parameter (`typename Fn`) is the cheapest form; the compiler can inline the lambda call. Use `std::function` only when caller polymorphism is required at runtime (rare).

4. **The pattern is NOT a virtual interface.** Don't reach for `class ICancelPrimitive { virtual int cancel(OrderID) = 0; };` here. Template-deferred is more flexible (any callable shape works), zero runtime cost, and avoids the class-hierarchy framing that doesn't fit C-style trading-engine idioms.

5. **Test mock-injection is trivially clean.** With Option A, testing reconciliation would require either (a) mocking BinanceOrderAPI globally (invasive) or (b) compile-time `#ifdef TESTING_RECONCILE` branches (gross). With Option E, the test lambda IS the mock; no global state, no preprocessor magic.

## When to revisit

Re-evaluate this pattern when:
- A logic-only header accumulates 5+ template-deferred callables → consider whether the header is doing too much (extract sub-header for related primitives)
- The callable signature gets complex (4+ parameters, multiple output paths) → consider a "side-effect context struct" instead of multi-arg callable
- Multiple call sites need the SAME side-effect implementation → factor the lambda to a function (still passed by template param; just reduces duplication)
