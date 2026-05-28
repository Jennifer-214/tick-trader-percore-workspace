---
type: ledger-template
class_id: 27
title: Single-value cache flattens per-instance distinction (subsystem state mirrors cfg as a scalar)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
surface_tags: [oms-drainer, cfg-flow, fixed-point-math, hot-path]
severity: high
recurrence_count: 1
first_instance: v5.15.5.F.4c.3
closure_mechanism: decision-time-data-binding-pattern (pre-resolve onto in-flight Order/Position/Event/TradeEvent at creation; downstream reads from object directly) + registry-driven per-instance cache fallback when no in-flight object exists + scalar cfg-mirror on subsystem state FORBIDDEN + tools/check_per_core_registry_integrity.py Check 7 CI + /accounting-audit + /registry-fit-audit
sister_classes: [18, 23, 24, 25, 26, 28, 29]
---

## Class 27 — Single-value cache flattens per-instance distinction (subsystem state mirrors cfg as a scalar)

**Detected:** 2026-05-15 (during v5.15.5.F.4c.3 WIP2d-1.B.0c Phase 4 codification; surfaced by the OMS fee_rate per-core analysis).
**Severity:** HIGH — silent accounting / model / risk divergence per instance; affects money tracking paths.

### Recurring symptom

A subsystem (OMS, ConfidenceScorer, PortfolioController, ThompsonBandit state, ...) caches one or more cfg values as SCALAR fields on its state struct at boot:

```cpp
struct OrderManagerState {
    FPN<F> fee_rate;
    FPN<F> fee_rate_maker;   // single scalar; boot-set from cfg.fee_rate_maker
    FPN<F> fee_rate_taker;   // single scalar
    FPN<F> slippage_pct;     // single scalar
    // ...
};
// At boot: oms.fee_rate_maker = cfg.fee_rate_maker;
// Per fill: rate = o->is_maker ? oms->fee_rate_maker : oms->fee_rate_taker;
```

When cfg later becomes per-instance (`cfg.cores[c].fee_rate_maker`), the SCALAR cache loses the per-instance distinction. Every instance (every core) ends up using the FIRST core's value at every per-fill / per-event read — silently. Operator sets `cfg.cores[2].fee_rate_maker = X`; the cfg surface accepts it; the Settings panel renders it; the parser writes it. But every fill across every core reads from `oms->fee_rate_maker` which is core 0's value frozen at boot. Accounting is wrong for cores 1..N.

The class is distinct from Class 26 (global consumer reading per-core field): Class 26 is at READ TIME; Class 27 is at CACHE STRUCTURE — the cache itself has no per-instance dimension. Same root family ("subsystem-state mirror of per-instance cfg") but Class 27 is the structural pre-condition that makes Class 26 silent.

**Class 26 sub-shape distinction (v5.15.5.F.4d.1.B.8 amendment):** Class 26 has TWO sub-shapes documented at the catalog (`class-26-global-consumer-reading-per-core-field.md` § Sub-shapes):
- **Sub-shape A** (WRONG-INDEX paired-access; CI Check 9 catches) — `cfg.core_overrides[X]` + `cfg.cores[Y]` paired access with X != Y
- **Sub-shape B** (UNINDEXED-GLOBAL at per-core consumer site; CI Check 10 catches) — `cfg.X` / `cfg->X` / `resolved_cfg.X` UNINDEXED on per-core-with-global-sister fields at per-core consumer sites

Class 26 sub-shape B is the consumer-side analog of Class 27 — both fail to thread per-core context through but at DIFFERENT layers (Class 27 at cache structure; Class 26 sub-shape B at consumer read site). Class 27 closure (decision-time data binding) prevents Class 26 sub-shape B at fill-event sites by construction (consumer reads from in-flight Order, not cfg). Class 26 sub-shape B persists at slow-path strategy adapts where decision-time binding doesn't apply (consumer needs cfg directly; CI Check 10 catches mechanically).

Concrete additional instance discovered: `static const double fee_rate_taker_d = FPN_ToDouble(cfg.fee_rate_taker);` at `EngineSharded.hpp:2469` — an even worse variant. The `static` caches at first lambda invocation, then NEVER refreshes. No sync path. Class 27 anti-pattern at the function-static level.

### Root cause

Two compounding patterns:

1. **Subsystem caches cfg values for performance** — reading cfg through a long pointer chain per fill is slower than reading a local cache. Cache is a reasonable optimization in principle.
2. **The cache is shaped as a SCALAR matching the (then-global) cfg shape** — at the time the cache is added, cfg is global; scalar matches naturally. When cfg later grows a per-instance axis, the cache shape doesn't change.

The flatten happens at cfg-growth time, but the BUG is introduced at cache-design time. The cache pattern is correct; the SHAPE assumption is the lurking bug.

### Structural fix

**First line: pre-resolve onto in-flight object (preferred).** The in-flight object (Order, Position, Event, TradeEvent) knows its per-instance context at creation time. Bind the per-instance cfg value onto the object at creation. Downstream consumers read from the object directly — zero cache, zero per-instance distinction to lose.

```cpp
// CORRECT — Order carries pre-resolved effective_fee_rate
struct Order {
    uint8_t   core_id;
    uint8_t   is_maker;
    FPN<F>    effective_fee_rate;   // pre-resolved at submit
    // ...
};

// At Order creation (slow-path):
o->effective_fee_rate = is_maker
    ? cfg.cores[core_id].fee_rate_maker
    : cfg.cores[core_id].fee_rate_taker;

// HandleFill (drainer):
FPN<F> rate = o->effective_fee_rate;  // zero cache lookup
```

**Second line (rare): registry-driven per-instance cache (fallback).** When no in-flight object exists, `FOREACH_<SUBSYS>_CFG_CACHE` X-macro generates per-instance arrays + sync helper + accessor. Composes with `postloadsetup-registry-pattern.md` for cfg-reload hook integration.

**FORBIDDEN under going-forward rule:**

```cpp
// FORBIDDEN — scalar cfg-mirror on subsystem state
struct SubsysState {
    FPN<F> some_cfg_value;   // mirrors cfg.cores[c].some_cfg_value
};

// FORBIDDEN — static const fn-local cache
void some_fn(...) {
    static const double rate = FPN_ToDouble(cfg.fee_rate_taker);  // freezes first value forever
    // ...
}
```

Closed at `v5.15.5.F.4c.3` WIP2d-1.B.1 — first canonical application of decision-time-data-binding via Order `effective_fee_rate`. OMS scalar fee_rate fields DELETED; static fn-local cache DELETED. Cohort sweep at WIP2d-1.B.1.b extends to slippage_pct + any other Class 27 instances surfaced by `/accounting-audit` canonical first run.

### Prevention (going-forward rule + audit + CI)

Codified at `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` (NEW at `.F.4c.3`).

> **Per-instance cfg values bind at decision time and flow forward with the in-flight object, NOT in subsystem state.** First line of defense: pre-resolve onto in-flight object. Second line (fallback): registry-driven per-instance cache when no in-flight object exists. Anti-pattern: scalar cfg-mirror field on subsystem state with implicit per-instance distinction.

CI enforcement at `tools/check_per_core_registry_integrity.py` Check 7 (NEW at WIP2d-1.B.0c): scans designated subsystem state types for scalar fields whose names match cfg field names. Match without explicit exemption in `MANUAL_FIELDS_INVENTORY.md` Section C → BUILD FAIL.

Audit skills:
- `/accounting-audit` (NEW at `.F.4c.3`) — canonical scanner for Class 27 instances + sister accounting issues
- `/registry-fit-audit` (NEW at `.F.4c.3`) — scans existing registries for misapplication per framework-selection criteria; surfaces "registry where pre-resolution would be better" findings

Anti-pattern grep signatures (for `/accounting-audit` + `/bug-check` integration):

```bash
# A1: Scalar cfg-mirror field on subsystem state (Class 27 primary shape)
# Heuristic: subsystem state struct fields with names matching FOREACH_PER_CORE_CFG_FIELD entries.
# (Enforced compile-time-failing by tools/check_per_core_registry_integrity.py Check 7.)

# A2: static const fn-local cfg cache (Class 27 fn-local variant)
rg -nP 'static\s+const\s+\w+\s+\w+\s*=\s*\w*FPN_ToDouble\s*\(\s*cfg\.\w' --type cpp

# A3: In-flight object missing pre-resolved per-instance field that should be there
# Detect heuristically: per-fill read of cfg.cores[X].Y when Order/Position/Event also passed
# (operator reviews; less mechanical than A1/A2)
```

False-positive exemptions documented in `MANUAL_FIELDS_INVENTORY.md` Section C with:
- Subsystem name + field name
- Rationale (one of: pre-resolve impossible AT THIS SITE; genuine subsystem-internal aggregate; cfg value is uniform-by-design across instances)
- Migration trigger (if TRANSITIONAL)

### Related classes

- **Class 25** (Scope-erosion in per-core consumer function) — sister at READ-SITE layer (consumer reads wrong scope). Class 27 is at CACHE-DESIGN layer (the scope doesn't exist in the cache structure). Class 25 + Class 27 close together at `.F.4c.3` via cfg-scope-discipline + decision-time-data-binding + Check 6 + Check 7 CI.
- **Class 26** (Global consumer reading per-core field) — sister; Class 27 is the structural pre-condition that makes Class 26 silent. Eliminating Class 27 sources eliminates many Class 26 sites by construction.
- **Class 18** (Mirror-incomplete) — same family of "subsystem state mirrors cfg structure"; Class 27 is the specific scalar-flatten variant.
- **Class 24** (Capability-cfg surface mismatch) — sister at CFG-SURFACE layer; Class 27 is at CONSUMER-STATE layer. Both close at `.F.4c.3` ship.

### Cross-references

- `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` — full principle + design space + reference implementations
- `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` § "Pattern 1 — OMS per-core fee_rate cluster" — the cfg-scope side of the same fix
- `DESIGN_SPECS/data-disciplines/cache-layout-discipline-for-hot-side-structs.md` — companion (subsystem state layout consideration)
- `DESIGN_SPECS/data-disciplines/hot-side-array-element-alignment-for-sparse-access.md` — composes (per-instance cache fallback layout)
- `DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md` — fallback mechanism integration (cfg-reload sync hook)
- `tools/check_per_core_registry_integrity.py` Check 7 — CI enforcement
- `DOCS/MANUAL_FIELDS_INVENTORY.md` Section C — exemption registry
- `CoreFrameworks/OrderManager.hpp` (post-`v5.15.5.F.4c.3` WIP2d-1.B.1) — canonical first application
- CLAUDE.md item 31 + DESIGN_PHILOSOPHY § 11 framework-selection criteria — meta-principle
