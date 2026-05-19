---
type: ledger-template
class_id: 28
title: Branchy SP/HP dispatch when branchless feasible (variance injection in determinism-prioritizing path)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
surface_tags: [hot-path, slow-path, oms-drainer, producer]
severity: high
recurrence_count: 7
first_instance: v5.15.5.F.4c.3
closure_mechanism: 5-pattern branchless toolkit (Pattern 1 fn pointer table + Pattern 2 2D state×type table + Pattern 3 mask-select / bitmap-search via ctz + Pattern 4 pre-resolution at decision time + Pattern 5 sink-fn-pointer for optional side effects) + branchless-dispatch-discipline.md + H20 hard invariant + /hft-audit branchless-opportunity scan + documented exemptions (boot-time / __builtin_expect rare / if constexpr / genuine binary predicate)
sister_classes: [14, 18, 27, 29]
---

## Class 28 — Branchy SP/HP dispatch when branchless feasible (variance injection in determinism-prioritizing path)

**Detected:** 2026-05-15 (during v5.15.5.F.4c.3 WIP2d-1.B.0d hand-wave audit; surfaced after Caramel called out the framing "branch is fine because predictor handles it" applied to HandleFill BUY/SELL dispatch).
**Severity:** HIGH — variance injection in code path that values determinism; p99-vs-p50 spread widens; cumulative tail latency exposure.

### Recurring symptom

Slow-path, hot-path, drainer, or producer-fan-out code dispatches on a runtime enum value (Order type, Order state, Cmd type, strategy enum, regime enum, bandit algorithm, ...) via `if/else if` chain or `switch` statement. The compiler lowers to conditional jumps. Branch predictor catches predictable patterns well (90%+ correct prediction on alternating BUY/SELL); rare access patterns get higher mispredict rate.

Even at low mispredict rates (5-15%), the cost compounds in real-world HFT measurement: pipeline flush + dependent op cascade + possible L1i miss = 30-100ns per mispredict event (vs textbook 5-15ns single-stall number).

The deeper issue: branches inject VARIANCE. Even when AVERAGE is acceptable, p99 vs p50 spread widens. For HFT, that variance compounds through downstream pipeline stages — variable engine latency means variable tick-to-trade latency means harder reasoning about end-to-end timing.

Distinct from Class 27 (scalar cfg-mirror cache): Class 27 is a STATE-DESIGN bug (subsystem state has wrong shape); Class 28 is a DISPATCH-CODE bug (branch where branchless was feasible).

Concrete first-canonical instances landed at `v5.15.5.F.4c.3` WIP2d-1.B.1:
- `OrderManager_HandleFill` BUY/SELL type dispatch — converted to **Pattern 1 (1D fn pointer table)** `g_fill_dispatch<F>[type]` (audit found dedup branch on Order state was unreachable; per-fill path never sees terminal Order, so 1D dispatch sufficed)
- `AccountMakerTakerFee` maker/taker fee selection — Pattern 3 (mask-select) reading from `Order::pre_resolved.fee_rate` (Pattern 4 composition)
- `Portfolio_RecordExit` win/loss tracking — Pattern 3 (`last_was_win_bitmap` mask-select)
- `OrderManager` last-maker / last-win bookkeeping — Pattern 3 (bitmap mask-select replacing scalar flags)
- `Reconcile_ApplyMissedFills` origin_core_id recovery — Pattern 3 sub-variant (bitmap-search via match-mask + `__builtin_ctz`) replacing per-slot branchy scan
- `ShardedLiveSafety_PreSubmitGate` slot iteration — Pattern 3 sub-variant (bitmap iteration via match-mask + `__builtin_ctz`)
- `FlattenAll_OneCore` partial_on slot computation — Pattern 3 (branchless shift instead of if-mask)
- Pattern 5 sink-fn-pointer for trade_log + calibration_log emit branches — `OmsState::on_entry_fill_emit / on_exit_fill_emit / on_exit_calibration` fn-pointer fields with `noop_fill_emit` default + `real_*` attach at boot when trade_log_path / calibration_log_file configured

### Root cause

Two compounding patterns:

1. **Cultural default of branchy dispatch.** `if/else if` chains are the natural C++ expression of multi-way dispatch. Function pointer tables and computed-goto are less idiomatic; reach for them only when explicitly thinking about branchless.

2. **Throughput-frame justification.** "Branch predictor handles predictable patterns at ~0ns" is TRUE on average but ignores variance + real-world mispredict cost. The hand-wave: defaulting to branch because the average looks fine, without thinking about p99 / consistency / variance injection.

The framing failure is the bug seed. Codebases that prioritize determinism need branchless-by-default discipline; defaulting to branch and only converting when "we measure a problem" lets variance accumulate invisibly.

### Structural fix

**Function pointer table dispatch (Pattern 1) for single-enum dispatch.** See `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md` § Pattern 1.

```cpp
template <unsigned F>
inline constexpr FillHandler<F> g_fill_dispatch[4] = {
    &handle_buy_fill<F>,  // ORDER_MARKET_BUY  = 0
    &handle_sell_fill<F>, // ORDER_MARKET_SELL = 1
    &handle_buy_fill<F>,  // ORDER_LIMIT_BUY   = 2 (treat as buy at limit price)
    &handle_sell_fill<F>, // ORDER_LIMIT_SELL  = 3
};
g_fill_dispatch<F>[(uint8_t)Order_GetType(o)](oms, o, fill_price, fill_qty);
```

**2D state×type dispatch table (Pattern 2) for composite dispatch** — reserved for cases where dedup + type dispatch must collapse. Pattern 1 is the canonical first-form when terminal-state guard is unreachable (per-fill path never sees terminal Order).

**Mask-select (Pattern 3) for binary with cheap both-sides** (already-canonical for BITMAP_* operations). Sub-variants:
- **Bitmap-search via match-mask + `__builtin_ctz`** for sparse iteration over occupied slots (replaces per-slot branchy scan; e.g. Reconcile origin_core_id recovery + ShardedLiveSafety pre-submit gate).

**Pre-resolution at decision time (Pattern 4) for cfg-derived dispatch** — eliminates per-fill cmov entirely. See `decision-time-data-binding-pattern.md`. Canonical at `Order::pre_resolved.fee_rate`.

**Sink-fn-pointer (Pattern 5) for optional side effects** — eliminates per-fill `if (sink_attached)` guard via fn-pointer field defaulting to `noop_*` and attached at boot when configured. See `DESIGN_SPECS/framework-patterns/sink-fn-pointer-for-optional-side-effect-pattern.md` (NEW at `.F.4c.3`).

**FORBIDDEN going-forward:**

```cpp
// FORBIDDEN — branchy dispatch on runtime enum in SP/HP/drainer code
if (Order_GetType(o) == ORDER_MARKET_BUY) {
    /* BUY handler body */
} else if (Order_GetType(o) == ORDER_MARKET_SELL) {
    /* SELL handler body */
}

// FORBIDDEN — switch on runtime enum in SP/HP/drainer code (same shape, different syntax)
switch (Order_GetType(o)) {
    case ORDER_MARKET_BUY:  /* ... */ break;
    case ORDER_MARKET_SELL: /* ... */ break;
}
```

Closed at `v5.15.5.F.4c.3` WIP2d-1.B.1 — first canonical close via HandleFill 2D state×type dispatch table. OrderManager_HandleFill if/else chain DELETED; replaced with `g_fill_dispatch[state][type](...)`.

### Prevention (going-forward rule + audit + CI)

Codified at `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md` (NEW at `.F.4c.3` WIP2d-1.B.0d).

> **Branchless dispatch preferred for SP/HP data-dependent code.** Trigger: data-dependent dispatch (if/else or switch on runtime enum) on slow-path, hot-path, drainer, or producer-fan-out code → convert to fn pointer table (Pattern 1) or 2D state×type table (Pattern 2) or pre-resolve at decision time (Pattern 4). Branch is acceptable ONLY when predicate is boot-time-only OR `__builtin_expect`-tagged rare OR `if constexpr` compile-time OR genuine binary predicate with no alternative computation.

Audit skill enforcement:
- `/hft-audit` extended at `.F.4c.3` WIP2d-1.B.0d with **Branchless dispatch opportunity scan** section — scans SP/HP/drainer code for if/else chains + switch statements on runtime enums; flags candidates for fn pointer table conversion; outputs severity-classified findings report
- `/dod-audit` references `branchless-dispatch-discipline.md` as a missed-pattern check
- `/bug-check` picks up Class 28 codification (registry-driven; no skill edit needed)
- `/precoding-audit-gate` audit_set extended to include `/hft-audit` when SP/HP/drainer changes are in plan scope

Anti-pattern grep signatures (for `/hft-audit` integration):

```bash
# A1: if/else if chain dispatching on Order type / state / cmd type in SP/HP code
rg -nP '(?s)if\s*\(\s*(Order_GetType|Order_GetState|cmd\.type|cmd_type|.*\.state)\s*[=!]=\s*\w+\s*\).*?else\s+if' --type cpp CoreFrameworks/ ML_Headers/ Strategies/

# A2: switch on runtime enum in CoreFrameworks/ML_Headers/Strategies SP/HP paths
rg -nP 'switch\s*\(\s*(Order_GetType|Order_GetState|cmd\.type|.*\.state)\s*\)' --type cpp CoreFrameworks/ ML_Headers/ Strategies/

# A3: if-chain on bandit_algorithm or strategy_id in SP/HP body
rg -nP 'if\s*\(\s*(bandit_algorithm|strategy_id|regime|strategy)\s*==' --type cpp CoreFrameworks/ ML_Headers/ Strategies/
```

False-positive exemptions (documented per case):
- Boot-time / Init-time branches — cost amortized to zero per fill
- `__builtin_expect`-tagged rare branches per latency-path-discipline.md Rule 4 (steady-state cost ~0ns)
- `if constexpr` compile-time elision — no runtime cost
- Genuine binary predicate without alternative computation (e.g., null-ptr check)
- Test fixtures / non-production code paths

### .F.4d canonical additions (2026-05-16)

6 additional Class 28 sites closed at `v5.15.5.F.4d` MERGED:
- `Bandit_Update` — cmov for per-arm probability normalization
- `Thompson_Sample` — cmov for posterior parameter clamp
- `ModelInference_Predict` — cmov for prediction validity check
- `WeightedBlend` — cmov for blend-mode dispatch
- `RollingTurnover` — cmov for window-warm-up gate
- `__builtin_expect`-tagged rare bounds guard at `FOREACH_OMS_PER_SLOT_FIELD` post-fill clear

Plus **Pattern 5 sink-fn-pointer canonical extension** at `.F.4d` for Thompson_Update dispatch via `EnsembleModelZoo<F>::buy_thompson_update_fn` + `exit_thompson_update_fn` fields (noop default + `real_thompson_update` attach when bandit algorithm requires posterior updates — sister to existing Pattern 5 trade_log + calibration_log canonicals at `.F.4c.3` WIP2d-1.B.1).

**H20 ratification at `.F.4d`** enshrines this discipline in the hard-invariants table (codified `.F.4c.3` WIP2d-1.B.0d; promoted to HARD at `.F.4d` ship close 2026-05-16). H20 generalizes the branchless-dispatch discipline from H7 (hot-path strict) to SP + drainer + producer-fan-out.

### Related classes

- **Class 27** (Scalar cfg-mirror cache) — sister; both are "default-to-easy thinking" anti-patterns. Class 27 is state-design layer; Class 28 is dispatch-code layer. Pre-resolution (Pattern 4) closes both classes when the dispatch is on cfg-derived values.
- **Class 14** (Plan API drift) — sister at API-stability layer; both classes recur when discipline defaults are not enforced.
- **Class 18** (Mirror-incomplete) — same family of "multi-site code that should compose cleanly"; Class 28 is "multi-branch dispatch that should be tabular."

### Cross-references

- `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md` — full discipline definition + patterns + cost framework + decision matrix
- `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` — sister; Pattern 4 (pre-resolution) is the strongest branchless form
- `DESIGN_PHILOSOPHY.md` § 4 Latency cost framework (updated 2026-05-15) — real-world mispredict cost basis
- `DESIGN_PHILOSOPHY.md` § 6 Concurrency family — branchless mask compute principle
- `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` Rule 8 (branchless for data-dependent dispatch)
- `CoreFrameworks/OrderManager.hpp` (post-`v5.15.5.F.4c.3` WIP2d-1.B.1) — canonical first close (Pattern 1 1D `g_fill_dispatch[type]` + Pattern 3 mask-select fee selection + Pattern 5 sink-fn-pointer for trade_log / calibration_log emit)
- `CoreFrameworks/Reconcile.hpp` + `CoreFrameworks/ShardedLiveSafety.hpp` (post-`v5.15.5.F.4c.3` WIP2d-1.B.1) — Pattern 3 sub-variant (bitmap-search via match-mask + `__builtin_ctz`) replacing per-slot scan loops
- `DESIGN_SPECS/framework-patterns/sink-fn-pointer-for-optional-side-effect-pattern.md` — Pattern 5 (NEW; codified at `.F.4c.3`)
- CLAUDE.md item 18 + item 28 — latency discipline references
