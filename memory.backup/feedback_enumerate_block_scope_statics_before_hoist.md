---
name: feedback-enumerate-block-scope-statics-before-hoist
description: "When hoisting a lambda body or inline function into a named header function (different scope), enumerate ALL block-scope `static` variables in the original enclosing scope BEFORE writing the hoisted signature. Pass each as explicit fn arg (pointer for mutable; by-value for read-only). Codified Stage 2 DRAFT 2026-05-27 after fan_out hoist required 2 attempts to surface all 6 missing block-scope statics at v5.15.5.F.4d.1.B.6 Phase B.2. Sister to Class 35 + B18 pillar."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: phase-e-ship-close-v5.15.5.F.4d.1.B.6
  sister_specs: [feedback_enumerate_helper_signature_args_before_extract.md, feedback_forward_decl_at_global_scope_not_namespace.md, feedback_cpp17_inline_variable_for_shared_state_across_tus.md]
  tags: [enumeration-discipline, block-scope-statics, refactor-discipline]
---

**When hoisting a lambda body or inline function from a monolithic header into a named function (different scope/file), enumerate ALL block-scope `static` variables in the original enclosing scope BEFORE writing the hoisted signature.** Pass each as explicit fn arg (pointer for mutable; by-value for read-only).

```cpp
// Pre-hoist: lambda accesses block-scope statics inside producer-thread body
void EngineSharded_Run(/* ... */) {
    static uint64_t fan_out_call_count = 0;       // block-scope statics
    static uint64_t fan_out_dropped_total = 0;
    static thread_local timespec last_fan_out_ts;
    /* ... 3 more ... */
    auto fan_out = [&](Tick t) {
        ++fan_out_call_count;          // direct access works in same scope
    };
}
```

```cpp
// Post-hoist (WRONG): hoisted fn can't see block-scope statics
namespace tt {
    void fan_out(/* domain args only */) {
        ++fan_out_call_count;  // ERROR: undeclared identifier
    }
}
```

```cpp
// Post-hoist (CORRECT): enumerate block-scope statics + pass as explicit args
namespace tt {
    void fan_out(
        /* domain args */,
        uint64_t* call_count,     // ← block-scope static, by pointer for write-back
        uint64_t* dropped_total,
        timespec* last_ts,
        /* ... 3 more ... */
    ) {
        ++(*call_count);
    }
}
```

**Why:** Codified Stage 2 DRAFT 2026-05-27 at v5.15.5.F.4d.1.B.6 Phase B.2 (Async.hpp `fan_out` lambda hoist from monolithic `EngineSharded.hpp`). Producer-thread block had 6 block-scope statics for accounting + cadence tracking. Initial hoist signature took 19 args; failed with 6 "undeclared identifier" errors. Final hoisted signature = 25 args.

Block-scope statics are LATENT state invisible at first glance during lambda-hoist work. Compile failure is LOUD (undeclared identifier) but rebuild cycles waste time; N statics missed = N iterations to convergence.

**Composes with M6 parent discipline** (`feedback_enumerate_helper_signature_args_before_extract`) — block-scope statics are a sister sub-category of comprehensive arg enumeration.

## How to apply

1. **At plan-draft time:** for each lambda being hoisted, enumerate block-scope statics in the enclosing function/scope via grep:
   ```bash
   # In the enclosing function body, find static declarations
   awk '/<enclosing-function-signature>/,/^void|^auto/' <header> | grep -E '\bstatic\b'
   ```
2. **Generate enumeration CSV artifact:** sister to M6 body-content enumeration; per-lambda CSV with columns (lambda name / block-scope static / type / decl line / write+read sites / pass-by-pointer required). Path convention: `plans/<sprint>/plan_checks/<date>-<ship>-<helper>-block-scope-statics-enumeration.csv`
3. **Write hoisted fn signature:** include ALL enumerated block-scope statics as args BEFORE first build verify
4. **At /blindspot-scan B18 audit:** sweep plan body for lambda-hoist proposals; verify enumeration CSV exists OR is captured in plan body

## Anti-patterns

- **Trusting "I think I caught them all" without enumeration** — block-scope statics hide in unexpected places (rate-limiting cadence variables / debug-print counters / boot-time warmup state)
- **Skipping the CSV artifact** — multi-iteration rebuild cycles waste 5-15 min per missed static; CSV cost is ~5 min upfront
- **Not composing with M6** — block-scope statics are sister to "all captured-by-reference state"; both warrant the same comprehensive enumeration discipline

## Sister memories

- [[feedback_enumerate_helper_signature_args_before_extract]] — M6 parent discipline; this rule is the block-scope-statics sub-category
- [[feedback_forward_decl_at_global_scope_not_namespace]] — sister at same monolithic-header-split surface; different root cause (forward-decl shadow vs block-scope statics); B17 sister pillar
- [[feedback_cpp17_inline_variable_for_shared_state_across_tus]] — companion at same monolithic-header-decomposition work surface

## DESIGN_SPECS sister

- `DOCS/recurring-bug-patterns/class-35-block-scope-statics-not-accessible-from-hoisted-fns.md` (the Class entry)
- `meta-disciplines/implementation-layer-blindspot-taxonomy.md` B18 sister pillar (Stage 2 DRAFT)
- `meta-disciplines/body-content-enumeration-at-plan-time-discipline.md` (M6 parent discipline)

## Recognition markers

- Lambda hoist / function extraction from monolithic header
- "Undeclared identifier" compile errors immediately post-extract
- N rebuild iterations clustering on the same enclosing scope's lambda
- Block-scope statics referenced for accounting / debugging / rate-limiting / cooldown / boot-warmup state

## When this rule applies

Per feedback_categorical_triggers_over_hardcoded_refs:

- Any lambda hoist into named header function
- Any function extraction from monolithic header
- Any helper-extract refactor crossing scope boundaries
- Any /blindspot-scan / /merge-scan finding proposing lambda → named fn migration
