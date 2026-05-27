---
type: ledger-template
class_id: 35
title: Block-scope statics not accessible from hoisted header functions
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-27
surface_tags: [header-split, lambda-hoisting, block-scope, monolithic-header-decomposition]
severity: high
recurrence_count: 1
first_instance: 2026-05-27 (v5.15.5.F.4d.1.B.6 Phase B.2 fan_out lambda hoist — 6 file-local statics inside producer-thread block scope inaccessible from hoisted Async.hpp::fan_out function body)
closure_mechanism: Enumerate block-scope statics in lambda body BEFORE hoisting; pass each as explicit fn arg; B18 sister blindspot pillar + sister memory feedback_enumerate_block_scope_statics_before_hoist
sister_classes: [11, 18, 34]
---

# Class 35 — Block-scope statics not accessible from hoisted header functions

**Detected:** 2026-05-27 at v5.15.5.F.4d.1.B.6 Phase B.2 (Async.hpp extract — `fan_out` lambda hoist from monolithic `EngineSharded.hpp` into named function in `CoreFrameworks/EngineSharded/Async.hpp`).
**Severity:** HIGH — compile failure (LOUD); compile error is non-obvious ("no member named 'X' in scope" when X is a block-scope static visible only to the original enclosing scope, not the new hoisted-function scope).

## Recurring symptom

A lambda or inline function body extracted from a monolithic header into a named function in a different header / file references block-scope `static` variables that were declared INSIDE the original enclosing function/scope. When the lambda's body is hoisted to a different scope, those block-scope statics are inaccessible.

```cpp
// Pre-hoist: lambda captures block-scope statics inside producer-thread body
void EngineSharded_Run(/* ... */) {
    static uint64_t fan_out_call_count = 0;  // block-scope static inside Run
    static uint64_t fan_out_dropped_total = 0;
    static thread_local timespec last_fan_out_ts;
    /* ... 3 more block-scope statics ... */
    auto fan_out = [&](Tick t) {
        ++fan_out_call_count;          // accesses block-scope static; OK because lambda is in same scope
        last_fan_out_ts = /* ... */;
    };
    /* body that calls fan_out() */
}
```

```cpp
// Post-hoist (WRONG): hoisted function can't access block-scope statics
namespace tt {
    void fan_out(/* fn args without statics */) {
        ++fan_out_call_count;  // ERROR: undeclared identifier (block-scope static not in scope)
    }
}
void EngineSharded_Run(/* ... */) {
    static uint64_t fan_out_call_count = 0;  // still declared here; not visible to tt::fan_out
    /* ... */
    tt::fan_out(/* ... */);  // tt::fan_out can't see these
}
```

```cpp
// Post-hoist (CORRECT): enumerate block-scope statics + pass as explicit args
namespace tt {
    void fan_out(
        /* ... domain args ... */,
        uint64_t* call_count,                // pass by pointer for write-back
        uint64_t* dropped_total,
        timespec* last_ts,
        /* ... 3 more enumerated statics ... */
    ) {
        ++(*call_count);
        *last_ts = /* ... */;
    }
}
void EngineSharded_Run(/* ... */) {
    static uint64_t fan_out_call_count = 0;
    static uint64_t fan_out_dropped_total = 0;
    static thread_local timespec last_fan_out_ts;
    /* ... */
    tt::fan_out(/* ... */, &fan_out_call_count, &fan_out_dropped_total, &last_fan_out_ts, /* ... */);
}
```

## Why this is a class (not a one-off bug)

Block-scope statics are LATENT state that's invisible at first glance during lambda-hoisting work. Recurrence is FORESEEABLE without structural discipline:

- Lambda bodies in monolithic headers often accumulate "private statics" for accounting / debugging / rate-limiting / cooldown tracking
- These statics live inside the enclosing function/scope (not at namespace or class scope)
- During lambda-hoist refactor (e.g., extracting a lambda into a named header function), the body's external-symbol enumeration typically catches MEMBER references (`state->X`) + caller-passed args, but misses block-scope statics
- Compile failure is LOUD (undeclared identifier) but rebuild cycles waste time; if there are 6 statics, that's 6 iterations until convergence

Distinct from Class 34 (Forward-decl namespace shadow) — same surface (monolithic header decomposition / Phase B header extraction work), different root cause (block-scope statics vs forward-decl shadow). Both classes surface at the same Phase B work surface and warrant sister codification + B17/B18 sister pillars.

## False-positive surface (per M3 discipline)

Not all hoist-time scope errors are Class 35:

- **Caller-side state references via captured-by-reference (KEEP):** `auto fn = [&state](...) { state.X = ...; };` captures `state` by reference; hoist signature passes `state` as arg. Not Class 35 (well-recognized pattern; doesn't get missed).
- **Member access through `this->` (KEEP):** when lambda is a class member, `this->member` is accessible; hoist preserves via `*this` or member fn dispatch. Not Class 35.
- **Hoisting into namespace member fn of same enclosing scope (KEEP):** if "hoist" is actually flattening the lambda inline at original site (no scope change), block-scope statics still accessible. Not Class 35.

The Class 35 shape is specifically: block-scope `static` declared inside enclosing function/scope; lambda body accesses those statics directly; hoist moves lambda body to DIFFERENT scope (different header / different namespace / different file).

## Closure mechanism

**Structural discipline at planning surface + sister blindspot pillar:**

1. **Enumerate block-scope statics BEFORE hoisting** — at audit time / plan-draft time, comprehensive grep of the lambda body for `static` references that aren't bound to a struct/class:
   ```bash
   # Find block-scope static refs in lambda body (pseudo-pattern)
   awk '/auto.*=.*\[.*\]\s*\(/,/\};/' <monolithic-header> | grep -E '\bstatic\b'
   ```

2. **Pass each block-scope static as explicit arg** — hoisted function takes pointers (for mutable statics) or by-value (for read-only) per the enumeration. Document each in the function signature.

3. **Sister blindspot pillar B18** at `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` (Stage 2 DRAFT 1st instance at `.B.6`; promotes to Stage 3 at 2nd canonical sister-application)

4. **Sister memory codification** `feedback_enumerate_block_scope_statics_before_hoist.md` (Stage 2 codification at `.B.6` Phase E ship close)

5. **Composition with M6 discipline** `feedback_enumerate_helper_signature_args_before_extract.md` — block-scope statics are sister to "body-content enumeration before helper extract"; M6 captures the comprehensive arg-enumeration discipline; Class 35 specifically calls out block-scope statics as the often-missed sub-category

6. **`/blindspot-scan B18` audit** at pre-coding gate when plan body proposes lambda hoist or function extraction from monolithic header

## Worked instances

### Instance 1 — Phase B.2 Async.hpp `fan_out` lambda hoist (2026-05-27)

**Context:** Producer-thread fan-out lambda extracted from monolithic `EngineSharded.hpp` into named `tt::fan_out` function in `CoreFrameworks/EngineSharded/Async.hpp`. Producer-thread block originally had 6 block-scope `static` variables for:
- `fan_out_call_count` — total fan_out invocations counter (rate-limit log printing)
- `fan_out_dropped_total` — dropped-tick accumulator
- `last_fan_out_ts` — `thread_local timespec` for cadence tracking
- `fan_out_log_cadence_ns` — `static const int64_t` rate-limit threshold
- `last_log_emit_ts` — `thread_local timespec` for log-emit cadence
- `fan_out_warmup_count` — boot-time warmup counter

**Mistake:** Initial hoist signature took 19 args (domain context + state + tick data); did NOT include the 6 block-scope statics. Compile failed with 6 "undeclared identifier" errors during build verification.

**Resolution:** Enumerated block-scope statics via grep of original producer-thread body BEFORE re-extracting; passed each as explicit pointer arg. Final hoisted signature = 25 args (19 domain args + 6 block-scope statics as pointers).

**Plan body amendment:** Added comprehensive enumeration as Phase A.2b CSV artifact at `plans/v5.15-live-readiness/plan_checks/2026-05-27-v5.15.5.F.4d.1.B.6-lambda-block-scope-statics-enumeration.csv`. Captures: lambda name / block-scope static name / type / declaration line / write/read sites / pass-by-pointer requirement.

**Outcome:** Hoist succeeded on 2nd attempt with explicit enumeration. Class 35 codified to prevent recurrence at sister hoist work (next monolithic-header subfolder split or extracted-lambda refactor).

## Sister classes

- **Class 34** (Forward-decl namespace shadow) — sister at same monolithic-header-split surface; different root cause (forward-decl shadow vs block-scope statics); both surface at Phase B header extraction; both warrant sister codification at codification ship close
- **Class 11** (Extensibility friction / silent drift) — parent meta-class; Class 35 is one shape of refactor-introduced drift
- **Class 18** (Mirror plans missing data-flow dependencies) — sister at the planning surface; both involve comprehensive consumer/dependency enumeration before structural change

## Cross-references

- `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` (B18 sister pillar Stage 2 DRAFT — block-scope statics inaccessible from hoisted header functions)
- `feedback_enumerate_block_scope_statics_before_hoist.md` (sister memory; Stage 2 codification at `.B.6` Phase E ship close)
- `feedback_enumerate_helper_signature_args_before_extract.md` (M6 parent discipline; comprehensive arg enumeration before extract; Class 35 is the block-scope-statics sub-category)
- `DESIGN_SPECS/data-disciplines/cpp17-inline-variable-for-header-shared-state.md` (companion at SAME surface — header-only shared state; both surfaced by monolithic-header subfolder split work)
- Phase B.2 commit message in v5.15.5.F.4d.1.B.6 ship history
- Phase A.2b CSV artifact `plans/v5.15-live-readiness/plan_checks/2026-05-27-v5.15.5.F.4d.1.B.6-lambda-block-scope-statics-enumeration.csv` (canonical enumeration template for future hoist work)
- Plan body `plans/v5.15-live-readiness/subplans/2026-05-27-v5.15.5.F.4d.1.B.6-enginesharded-subfolder-split.md` (worked instance documentation)
