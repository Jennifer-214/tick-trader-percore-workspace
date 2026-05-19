---
type: refactor-pattern
stage: 5-claude-md
version: 1.0
established: 2026-05-15
tags: [branchless-discipline, latency-discipline, structural-fix]
surface: [hot-path, slow-path, oms-drainer, producer]
sister_specs: [branchless-math-kernel-pattern.md, latency-vs-cache-decision-framework.md]
applies_at_skills: []
---

# Branchless dispatch discipline (SP/HP data-dependent dispatch)

**Established:** 2026-05-15 (v5.15.5.F.4c.3 WIP2d-1.B.0d — codified after a hand-wave audit caught Stage 1 dispatch decisions in the OMS HandleFill that defaulted to "branch is fine because predictor handles it" thinking, contrary to the codebase's deterministic-latency premise).
**Status:** Stage 2 DRAFT v1.0 → Stage 3 ACTIVE at `.F.4c.3` ship close
**Tags:** structural-fix, latency, drainer, hot-path, slow-path, branchless, framework-discipline; closes Class 28; serves H7 + H8; Stage 2 (DRAFT); 0 applications until B.1 HandleFill refactor
**Cross-references:**
- `decision-first-cluster-layout-pattern.md` — sister (layout decisions); branchless dispatch is the ACCESS-time discipline counterpart
- `latency-vs-cache-decision-framework.md` — provides cost reference (cycles vs cache vs branch)
- `cache-layout-discipline-for-hot-side-structs.md` — sister (struct layout); branchless dispatch comes after layout decision
- `multi-bit-state-encoding-pattern.md` — sister (state encoding); branchless dispatch consumes packed state
- `bitmap-flag-api.md` — primitive (BITMAP_* macros) for branchless flag checks
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 28 — anti-pattern this closes
- `DOCS/DESIGN_PHILOSOPHY.md` § 4 Latency cost framework — cost basis
- CLAUDE.md item 18 + 28 — latency discipline references
- `decision-time-data-binding-pattern.md` — composes (pre-resolution is itself a branchless win)
- `multi-state-dispatch-with-per-state-update-metadata.md` — composes (Pattern 1 fn-pointer dispatch table entries auto-derived from registry metadata via X-macro reduction; adding a new dispatch state = 1 row mechanical change; sister pattern for metadata-driven branchless dispatch on multi-state enums)
- `sink-fn-pointer-for-optional-side-effect-pattern.md` — Pattern 5 (sister to Pattern 1/2/3/4); branchless optional side-effect emit via fn-pointer with noop default

---

## Problem statement

Slow-path and hot-path code in this codebase frequently dispatches on data — Order type (BUY/SELL/LIMIT_BUY/LIMIT_SELL), Order state (PENDING/SUBMITTED/ACK/PARTIAL/FILLED/REJECTED/...), Cmd type (FILL/RECONCILE/CANCEL/...), strategy enum, regime enum, bandit algorithm, etc. The naïve expression is `if/else if` chains or `switch` statements, which the compiler typically lowers to conditional jumps + branch predictor.

The textbook cost narrative for branches is "predictor handles it; mispredict is 5-15ns." This is the optimistic single-stall number. In practice on a pinned drainer thread executing a slow-path body:

- Pipeline depth on modern Intel/AMD CPUs is 14-20 stages; a mispredict flushes the entire pipeline
- Dependent operations cascade: instructions downstream of the mispredict that were speculatively executed must be discarded
- If the wrong-side branch target wasn't in L1i cache, the recovery includes an instruction-cache miss
- Cumulative measured mispredict cost in HFT codebases: **30-100 ns commonly observed**, 100+ ns in worst cases with cascading effects

This codebase is built around deterministic execution + tight tail latency — p99 budgets are hard limits (H8). Even when a single mispredict fits within budget, branches inject VARIANCE: average is fine, but p99 vs p50 spread widens. For HFT, that variance compounds across pipeline stages downstream of the engine.

**The hand-wave anti-pattern:** "branch is fine because the access pattern is predictable, predictor handles it at near-zero cost." This is throughput thinking applied to a system that values determinism. The correct frame: branch presence in SP/HP data-dependent dispatch is the anti-pattern; branchless via fn pointer table or 2D state table is the default.

---

## The principle (H20 invariant)

**Data-dependent dispatch on slow-path / hot-path / drainer code is BRANCHLESS by default. Branches in these paths require explicit justification per the decision matrix below.**

**H20 INVARIANT (CLAUDE.md):** Branchless preferred for SP/HP data-dependent dispatch EVEN WHEN NOMINALLY SLOWER. Mask code / fn pointer tables / cmov / mask-select / dummy-redirect approaches can be optimized later (better instruction selection at next compiler upgrade, vectorization opportunity, prefetch hints, hot-cold split). Branch mispredicts CANNOT be optimized away — they're a hardware cost (30-100ns real-world per `DESIGN_PHILOSOPHY.md` § 4). The choice isn't "minimize average cycles"; it's "minimize variance to make the system deterministic." A branchless dispatch that costs +5ns deterministic is better than a branch that costs 0-100ns variable, because the +5ns CAN be reduced over time while the 100ns mispredict tail CAN'T.

This invariant inverts the throughput-frame default: don't ask "is the branch's expected cost acceptable?"; ask "can this be branchless?" If yes (per the decision matrix), make it branchless. Reach for branchy only when one of the documented exceptions applies (boot-time / `__builtin_expect`-rare / `if constexpr` / genuine binary predicate without alternative).

Dispatch examples that should be branchless:
- Order type → fill handler (BUY / SELL / LIMIT_BUY / LIMIT_SELL)
- Order state → fill handler with dedup (FILLED → noop_handler; active states → real_handler)
- Cmd type → cmd processor (FILL_RESULT / RECONCILE / CANCEL_RESULT / WS_FILL)
- Strategy enum → BuildParameters handler
- Bandit algorithm enum → reward update handler
- Regime enum → gate decision dispatch
- ConfidenceScorer mode → score computation dispatch

These all expand to N-way dispatch on a tagged enum-like value. Function pointer table is the canonical mechanism.

### Decision matrix

| Path / context | Default | When branch is acceptable |
|---|---|---|
| Hot path (per-tick) | **BRANCHLESS** (H7) | Only when value is compile-time constant (`if constexpr`) — never runtime data |
| Slow path (per-cycle) | **BRANCHLESS** for data-dependent dispatch | Predicate is `__builtin_expect`-tagged + truly rare (e.g., kill-switch fire, gate change events) + steady-state cost ~0ns |
| Drainer (per-fill / per-cmd) | **BRANCHLESS** for type/state dispatch | Same as slow path |
| Boot path (one-time at startup) | Branch is fine | Cost amortized to zero per fill; branchless gains nothing |
| Test fixtures / non-production | Branch is fine | Not on production execution path |
| Genuine binary predicate with no alternative computation (e.g., `if (ptr == nullptr) return;`) | Branch | Cannot be expressed as table dispatch without computing both sides |

**Anti-pattern (Class 28):** if/else if chain or switch statement on a runtime enum value in SP/HP/drainer code where the branches map to distinct handlers. Fix: convert to function pointer table indexed by the enum.

---

## The patterns (concrete shapes)

### Pattern 1 — Function pointer table dispatch (1D)

For single-enum dispatch (e.g., Order type → handler):

```cpp
template <unsigned F>
using FillHandler = void (*)(OrderManagerState<F>*, Order<F>*, FPN<F>, FPN<F>);

template <unsigned F>
inline void handle_buy_fill(OrderManagerState<F>* oms, Order<F>* o, FPN<F> fill_price, FPN<F> fill_qty) {
    // BUY-specific body (~20 LOC)
}

template <unsigned F>
inline void handle_sell_fill(OrderManagerState<F>* oms, Order<F>* o, FPN<F> fill_price, FPN<F> fill_qty) {
    // SELL-specific body (~30 LOC)
}

// Dispatch table — indexed by OrderType enum (0=MARKET_BUY, 1=MARKET_SELL, 2=LIMIT_BUY, 3=LIMIT_SELL)
template <unsigned F>
static constexpr FillHandler<F> g_fill_handlers[4] = {
    handle_buy_fill<F>,   // ORDER_MARKET_BUY  = 0
    handle_sell_fill<F>,  // ORDER_MARKET_SELL = 1
    handle_buy_fill<F>,   // ORDER_LIMIT_BUY   = 2 (future; same buy logic)
    handle_sell_fill<F>,  // ORDER_LIMIT_SELL  = 3 (future)
};

template <unsigned F>
inline void OrderManager_HandleFill(OrderManagerState<F>* oms, Order<F>* o, FPN<F> fill_price, FPN<F> fill_qty) {
    g_fill_handlers<F>[Order_GetType(o)](oms, o, fill_price, fill_qty);
}
```

Cost per fill: 1 table lookup (~1ns L1 hit) + 1 indirect call (~3-5ns) + handler body. ZERO mispredict variance regardless of access pattern.

#### Pattern 1 sub-variant — Metadata-driven auto-derived dispatch table

When the enum has per-state metadata in its X-macro registry row (per `multi-state-dispatch-with-per-state-update-metadata.md`), the dispatch table entries can be COMPUTED at compile time from the metadata via X-macro reduction instead of hand-coded. Adding a new state = 1 row in the registry → dispatch table auto-extends; no scattered changes; Class 18 + Class 28 closed in one shape.

```cpp
// Per-state metadata in FOREACH_X declares each row's dispatch behavior:
//   FOREACH_BANDIT_ALGORITHM(X) row: (name, value, apply_fn, exp3_up, thompson_up, drives, doc)
// Reduction computes dispatch entry from metadata at compile time:
#define _DISPATCH_ENTRY(name, val, fn, exp3_up, thompson_up, drives, doc) \
    [val] = ((exp3_up) && (thompson_up)) ? &both_handler<F> \
          : (exp3_up)                    ? &exp3_only_handler<F> \
          : &thompson_only_handler<F>,

template <unsigned F>
static constexpr DispatchFn<F> g_dispatch_table[FOREACH_BANDIT_ALGORITHM_COUNT] = {
    FOREACH_BANDIT_ALGORITHM(_DISPATCH_ENTRY)
};
```

Same Pattern 1 dispatch cost at the callsite (~5-7ns deterministic). The win is structural: 6th state addition = 1 row in `FOREACH_X` → table auto-extends → all dispatch sites work unchanged. Class 18 mirror closure works at the row level because adding a row with the right metadata extends every consumer that consumes the metadata.

See `multi-state-dispatch-with-per-state-update-metadata.md` for the full pattern body + orthogonal-axes shape + composition with Pattern 5 sink-fn-pointer.

### Pattern 2 — 2D state×type dispatch table (composite dispatch)

**When to apply:** BOTH axes must be genuinely data-dependent dispatch axes — state AND type both vary, AND the dispatch needs to react to their combination. If one axis is trivially constant by invariant (e.g., entering function in only one state by construction) OR doesn't reach terminal/dedup states at the dispatch point, Pattern 1 (1D) suffices and is cleaner. The hypothetical example below illustrates the shape; verify your site actually needs the 2D dispatch before reaching for it.

For dispatch on a COMBINATION of state values (e.g., Order state × Order type, where state determines dedup AND type determines handler):

```cpp
// Indexed by [state][type] — terminal states map to handle_noop for branchless dedup
template <unsigned F>
static constexpr FillHandler<F> g_fill_dispatch[16][4] = {
    /*PENDING*/      { handle_buy_fill<F>, handle_sell_fill<F>, handle_buy_fill<F>, handle_sell_fill<F> },
    /*SUBMITTED*/    { handle_buy_fill<F>, handle_sell_fill<F>, handle_buy_fill<F>, handle_sell_fill<F> },
    /*ACKNOWLEDGED*/ { handle_buy_fill<F>, handle_sell_fill<F>, handle_buy_fill<F>, handle_sell_fill<F> },
    /*PARTIAL*/      { handle_buy_fill<F>, handle_sell_fill<F>, handle_buy_fill<F>, handle_sell_fill<F> },
    /*FILLED*/       { handle_noop_fill<F>, handle_noop_fill<F>, handle_noop_fill<F>, handle_noop_fill<F> }, // dedup
    /*REJECTED*/     { handle_noop_fill<F>, handle_noop_fill<F>, handle_noop_fill<F>, handle_noop_fill<F> },
    /*CANCELED*/     { handle_noop_fill<F>, handle_noop_fill<F>, handle_noop_fill<F>, handle_noop_fill<F> },
    /*TIMEOUT*/      { handle_noop_fill<F>, handle_noop_fill<F>, handle_noop_fill<F>, handle_noop_fill<F> },
    /*UNKNOWN*/      { handle_noop_fill<F>, handle_noop_fill<F>, handle_noop_fill<F>, handle_noop_fill<F> },
    // (remaining slots default to noop via zero-init or explicit fill)
};

template <unsigned F>
inline void OrderManager_HandleFill(OrderManagerState<F>* oms, Order<F>* o, FPN<F> fill_price, FPN<F> fill_qty) {
    g_fill_dispatch<F>[Order_GetState(o)][Order_GetType(o)](oms, o, fill_price, fill_qty);
}
```

Cost per fill: 1 table lookup (16×4×8B = 512B = 8 cache lines; stays L1 on pinned drainer) + 1 indirect call + handler body. Single deterministic dispatch path for ALL state×type combinations.

This collapses TWO branches (dedup + type) into ONE table lookup. p99 = p50 = ~5-7ns dispatch overhead + handler body cost.

### Pattern 3 — Mask-select for binary or small-K branches

For binary branches where both sides are CHEAP (1-3 ALU ops each):

```cpp
// PRE — branchy
if (Order_GetIsMaker(o)) BITMAP_SET(oms->mask, bit);
else                     BITMAP_CLR(oms->mask, bit);

// POST — branchless mask-select
uint16_t maker_bit  = BITMAP_BIT_U16(slot);
uint16_t maker_mask = Order_GetIsMaker(o) ? maker_bit : (uint16_t)0;
oms->mask = (uint16_t)((oms->mask & ~maker_bit) | maker_mask);
```

The ternary lowers to cmov; the mask-select replaces branch + conditional store with deterministic ALU ops. Cost: ~3-4 cycles deterministic vs branch + mispredict potential.

#### Pattern 3 sub-variant — Bitmap-search via match-mask + tzcnt

For find-first-match search loops over a small bitmap-gated array (typical case: 16 OMS slots), the branchy shape is:

```cpp
// PRE — branchy: per-slot bitmap gate + early-exit on match
int found = -1;
for (int s = 0; s < N; ++s) {
    if (!(bitmap & (1u << s))) continue;       // data-dependent branch (gate)
    if (predicate(arr[s])) {                    // data-dependent branch (match)
        found = s;
        break;
    }
}
```

Two data-dependent branches per slot (gate + match) plus an early-exit `break`. Variable cost = O(match-position); injects p99 variance.

```cpp
// POST — branchless: build match-bitmap via fixed-cost compare per slot;
// AND with gate-bitmap; tzcnt picks first set bit.
uint16_t match_mask = 0;
for (int s = 0; s < N; ++s) {
    int eq = predicate(arr[s]) ? 1 : 0;        // cmov; no branch
    match_mask = (uint16_t)(match_mask | ((uint16_t)eq << s));  // ALU only
}
uint16_t valid = (uint16_t)(match_mask & bitmap);
int found = valid ? (int)__builtin_ctz(valid) : -1;
```

Branchless inside the loop: ternary → cmov, mask-or is pure ALU. The `__builtin_ctz` is a single `tzcnt` instruction. Cost: fixed N × (predicate cycles + 2-3 ALU ops). Variance = 0.

When to apply: search loops where N is small (≤16-32 typical), predicate has fixed cost (e.g., `memcmp` on fixed-size data), and the cost difference between branchy avg vs branchless fixed is dominated by mispredict variance — which it is on SP/HP per the cost framework above.

Composes with `bitmap-flag-api.md` (BITMAP_* primitives) and `decision-time-data-binding-pattern.md` (the matched slot's `core_id` flows forward as pre-resolved value).

### Pattern 4 — Branchless via pre-resolution at decision time

When the dispatched value is cfg-derived and the dispatch happens on a hot path, pre-resolve at the SUBMIT point (where caller has cfg in scope) onto the in-flight object. Hot path reads pre-resolved value directly. See `decision-time-data-binding-pattern.md`.

Example: `o->pre_resolved.fee_rate` replaces `o->is_maker ? oms->fee_rate_maker : oms->fee_rate_taker` cmov. Pre-resolution eliminates the per-fill cmov entirely; HandleFill reads ONE field instead of conditionally selecting between two.

This is the strongest branchless form: the dispatch DOESN'T HAPPEN on hot path because it was already resolved at submit time.

---

## Cost framework (real-world, not textbook)

Per `DESIGN_PHILOSOPHY.md` § 4 Latency cost framework (updated 2026-05-15 with real-world mispredict cost):

| Operation | Textbook cost | Real-world cost (HFT pipelined) |
|---|---|---|
| Correctly predicted branch | ~0 ns | ~0 ns |
| Mispredict (single stall) | 5-15 ns | 5-15 ns when isolated |
| **Mispredict (real-world compound)** | (not modeled) | **30-100 ns** with pipeline flush + dependent op cascade + possible L1i miss on wrong-side target |
| Indirect call (fn pointer) | 3-5 ns | 3-5 ns deterministic |
| Table lookup (L1 hit) | 1 ns | 1 ns |

Branchless break-even vs branch:
- Branchless cost (deterministic): ~5-7 ns (table lookup + indirect call)
- Branch cost (variable): 0 ns × (1 - p_mispredict) + 30-100ns × p_mispredict
- Branchless wins at p_mispredict ≥ ~5-15% (which is typical for non-trivial access patterns)
- Branchless ALWAYS wins on p99 (deterministic vs variable tail)

Even when branch wins on AVERAGE (low mispredict rate), branchless wins on CONSISTENCY (tighter p99/p50 spread).

For a system that values determinism over throughput (HFT), the consistency win is the deciding factor.

---

## When branchless is the wrong tool

Honest list of exceptions:

1. **Boot-time / one-time setup branches** — Cost amortized to zero per fill. Branchless gains nothing.
2. **Genuine binary predicate without alternative computation** — `if (ptr == nullptr) return;` cannot be branchless without computing both sides; if the "both sides" cost > branch cost, branch wins.
3. **__builtin_expect-tagged rare branches** — Per latency-path-discipline.md Rule 4. Predicate is genuinely rare (e.g., kill switch fire, gate change); steady-state cost ~0ns with predictor.
4. **Compile-time elision** — `if constexpr` evaluates at compile time; no runtime cost. Strictly better than table dispatch when the decision is compile-time-known.
5. **Per-record bit-packing across millions of records** — Cache locality + indirection cost > memory savings (per DESIGN_PHILOSOPHY § 3 anti-pattern). Stay branchy if branchless requires unpacking.

If your case doesn't fit one of the above, branchless is the default.

---

## Reference implementations

Populated at Stage 3 ACTIVE — shipped sites get file:line refs.

- (pending) `CoreFrameworks/OrderManager.hpp` — `OrderManager_HandleFill` **1D type dispatch table** (.F.4c.3 WIP2d-1.B.1). First canonical **Pattern 1** application. Originally planned as Pattern 2 (2D state×type) but body inspection showed Order is never in terminal state at HandleFill entry by state-machine invariant — Pattern 2's terminal-state-noop rows would be dead code. Pattern 1 (1D type) is the correct shape; portfolio-bitmap dedup at slot-already-closed stays as `__builtin_expect`-rare branch (race-protection only, legitimate per decision matrix).
- (pending) `CoreFrameworks/OrderManager.hpp` — `OrderManager_HandleFill` `last_was_win_bitmap` SET/CLR converted to mask-select (.F.4c.3 WIP2d-1.B.1). Pattern 3 first canonical.
- (pending) `CoreFrameworks/Reconcile.hpp` — `Reconcile_ApplyMissedFills` originating-core_id bitmap-search via match-mask + tzcnt (.F.4c.3 WIP2d-1.B.1). **Pattern 3 sub-variant first canonical** (bitmap-search). Closes Reconcile cross-core fee accuracy structurally.
- Already exists (retroactively recognized): `bitmap-flag-api.md` BITMAP_* macros — branchless bitmap flag checks via mask-select. Pattern 3 precedent.
- Already exists (retroactively recognized): hot-path `ExecutionCore_Tick` mask compute for SG dispatch — branchless from inception. Pattern 1 precedent.
- Already exists (retroactively recognized): `OrderManager_Submit` free-slot allocation via `~oms->order_bitmap` + `__builtin_ctz` — Pattern 3 sub-variant precedent (free-bit search vs match-bit search; same primitive).
- (pending) `CoreFrameworks/Order.hpp` — `OrderPreResolved` sub-struct + `Order_BindPreResolved` helper (.F.4c.3 WIP2d-1.B.1). First canonical **Pattern 4** application. Sister: `flags_packed` widened to `uint32_t` + `MASK_ORDER_PRE_RESOLVED` bit + `TT_ASSERT_PRE_RESOLVED_BOUND` test-build assert structurally closes the silent-zero-fee class.
- (landed; v5.15.5.F.4d 2026-05-16) `ML_Headers/bandit_dispatch_table.hpp` — **`g_buy_reward_dispatch<F>[N]` + `g_exit_reward_dispatch<F>[N]`** Pattern 1 fn-pointer dispatch tables. **Second canonical Pattern 1 application.** Auto-derived from `FOREACH_BANDIT_ALGORITHM` 7-arg metadata via `?:` chain over `(exp3_up, thompson_up)` bits — adding a 6th bandit algorithm = 1 row in `FOREACH_BANDIT_ALGORITHM` → both buy + exit reward tables auto-extend with zero callsite changes. Closes Class 24 sister + Class 28 instances structurally for the reward-attribution dispatch family. Composes with `sink-fn-pointer-for-optional-side-effect-pattern.md` (leaf reward fns call `ezoo->thompson_update_fn(...)` Pattern 5 sink — branchless even when Thompson subsystem disabled) + `multi-state-dispatch-with-per-state-update-metadata.md` (per-row metadata bits drive dispatch table contents). Per-side mirror via `FOREACH_BANDIT_SIDE(X) X(buy) X(exit)` meta-X-macro — 3rd side (e.g., per-symbol Thompson) = 1 row addition. Side selection inside leaf fns via `if constexpr (Side == BanditSide::Buy)` — compile-time; zero runtime cost.
- (landed; v5.15.5.F.4d 2026-05-16) `CoreFrameworks/Order.hpp` — `MBS_OrderBanditActiveState` / `MBS_OrderBanditRegime` / `MBS_OrderBanditChosenArm` / `MBS_OrderSetBanditContext` shift+mask accessors over `Order::flags_packed` bits 17-25. **Sister Pattern 4 application** to existing `MASK_ORDER_PRE_RESOLVED` bit canonical — bandit context at decision time bound to Order at submit; flows with Order through lifecycle; read at calib emit + reward attribution sites without per-call cfg read. 5th canonical of `multi-bit-state-encoding-pattern.md` INVARIANT pattern.

---

## Lessons / gotchas

- **Function pointer table defeats inlining.** Each handler becomes a separate function call. For LARGE handler bodies (20-40 LOC), this is fine — the function call overhead is dwarfed by body execution. For TINY handler bodies (1-5 LOC), inlining loss may not be worth the dispatch consistency. Measure if uncertain.
- **Function pointer table must stay L1-hot.** On pinned threads with constant-pattern dispatch (every fill goes through HandleFill), the table is hot. Cold path scenarios (rare command types) may suffer L1 miss on first invocation per cache line. Mitigate by placing table in a hot cache line + prefetch hints if needed.
- **2D tables grow quickly with state space.** For (16 states × 4 types) = 64 entries × 8B = 512B = 8 cache lines, OK. For larger composite dispatch (e.g., 8 states × 8 strategies × 4 regimes = 256 entries), consider hierarchical dispatch (state-table picks a type-table) to keep cache footprint bounded.
- **Compiler optimization level matters.** At -O2/-O3, fn pointer tables + indirect calls inline well into the dispatch site. At lower opt levels, indirection cost is higher. Production builds are -O3; verify.
- **DON'T branchless-ify TOO eagerly.** The decision matrix is the guide. Boot-time branches, `if constexpr`, and __builtin_expect-tagged rare predicates are all valid branches. Pattern 1/2 is for SP/HP DATA-DEPENDENT dispatch specifically.
- **The hand-wave failure mode is "branch is fine because predictor handles it."** That framing is throughput thinking. The codebase optimizes for determinism. Default to branchless; require explicit justification for branch presence in SP/HP.

---

## Audit + prevention

CI / skill enforcement:
- `/hft-audit` extended at .F.4c.3 with "Branchless dispatch opportunity scan" — surfaces if/else chains + switch statements on data-dependent runtime enums in SP/HP code; flags candidates for fn pointer table conversion
- `/dod-audit` references this DESIGN_SPEC as a missed-pattern check
- `/bug-check` picks up Class 28 codification (registry-driven)

Going-forward rule (CLAUDE.local.md, set 2026-05-15 at WIP2d-1.B.0d):

> **Branchless dispatch preferred for SP/HP data-dependent code.** Trigger: data-dependent dispatch (if/else or switch on runtime enum) on slow-path, hot-path, drainer, or producer-fan-out code → convert to fn pointer table (Pattern 1) or 2D state×type table (Pattern 2) or pre-resolve at decision time (Pattern 4) per `branchless-dispatch-discipline.md`. Branch is acceptable ONLY when predicate is boot-time-only OR `__builtin_expect`-tagged rare OR `if constexpr` compile-time OR genuine binary predicate with no alternative computation. Mispredict cost in real-world HFT measurement is 30-100ns (not textbook 5-15ns); branches inject variance even when AVERAGE is acceptable.
