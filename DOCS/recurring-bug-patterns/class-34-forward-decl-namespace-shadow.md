---
type: ledger-template
class_id: 34
title: Forward-decl inside namespace shadows global type from `<chrono>` / standard headers
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-27
surface_tags: [header-split, namespace, forward-decl, monolithic-header-decomposition]
severity: medium
recurrence_count: 2
first_instance: 2026-05-27 (v5.15.5.F.4d.1.B.6 Phase B.3 SlowPath.hpp extract — `namespace tt { class steady_clock; }` shadowed `std::chrono::steady_clock`)
closure_mechanism: Forward-decl at GLOBAL scope (not inside namespace tt); B17 sister blindspot pillar + /blindspot-scan audit at header-extract time + sister memory feedback_forward_decl_at_global_scope_not_namespace
sister_classes: [11, 18, 35]
---

# Class 34 — Forward-decl inside namespace shadows global type from standard headers

**Detected:** 2026-05-27 at v5.15.5.F.4d.1.B.6 Phase B (EngineSharded monolithic header subfolder split). Surfaced at 2 sites in the same Phase B work (≥2-instance recurrence trigger per pattern-codification-lifecycle.md Stage 2):
- Phase B.3 SlowPath.hpp extract: `namespace tt { class steady_clock; }` shadowed `std::chrono::steady_clock` (compile failure: "no member named 'now' in 'tt::steady_clock'")
- Phase B.2 Async.hpp extract: `namespace tt { class CandleAccumulator; }` shadowed global `CandleAccumulator` type (compile failure: "incomplete type 'tt::CandleAccumulator'")

**Severity:** MEDIUM — compile failure (LOUD), but high rework cost (5-15 min per occurrence × N retries until ordering converges; multi-file builds get worse).

## Recurring symptom

Header extraction or subfolder split places forward declarations INSIDE a namespace (typically `namespace tt`) when the type being forward-declared lives at GLOBAL scope OR in `std::`. The forward decl creates a NEW type in the `tt` namespace that SHADOWS the global type.

```cpp
// WRONG: forward-decl shadows global type
namespace tt {
    class steady_clock;  // creates NEW type tt::steady_clock; does NOT refer to std::chrono::steady_clock
    void slow_path_body() {
        auto t0 = steady_clock::now();  // resolves to tt::steady_clock → "no member named 'now'"
    }
}
```

```cpp
// CORRECT: forward-decl at global scope
class CandleAccumulator;  // refers to global ::CandleAccumulator
namespace tt {
    void async_body(CandleAccumulator* acc) { /* uses global type */ }
}
```

## Why this is a class (not a one-off bug)

Two instances in the same Phase B work surfaces the pattern at the monolithic-header-decomposition surface. Recurrence is FORESEEABLE without structural discipline:

- Header-extract work typically grabs a chunk of code from a monolithic header + wraps the new sub-file in the project's namespace (`namespace tt { ... }`)
- Forward declarations for types referenced inside the chunk get hoisted by reflex INTO the namespace block
- C++ ADL + name resolution mean `tt::X` is a DISTINCT type from `::X` even if X is otherwise undefined; the forward-decl-inside-namespace creates the new type
- Compile failure is LOUD but late — surfaces only when the sub-file is consumed by another TU + the body of `tt::function` tries to call methods on the shadowed type
- Class 34 distinct from Class 35 (block-scope statics inaccessible from hoisted header functions) — both surface at the same Phase B header-extract work but have different root causes

## False-positive surface (per M3 discipline)

Not all `namespace tt { class X; }` declarations are Class 34:

- **Intentional `tt::X` types (KEEP):** when `tt::X` IS the canonical type (e.g., `tt::FPN<F>` lives in `namespace tt`); forward-declaring `tt::X` inside `namespace tt` is correct
- **Sister namespace types (KEEP):** declarations of types that legitimately belong in `tt::` (e.g., `tt::ConfidenceScorer`); forward-decl-inside-namespace is correct here
- **Type re-export aliases (KEEP):** `namespace tt { using ::SomeGlobalType; }` is an export shape; NOT a forward decl; not Class 34

The Class 34 shape is specifically: type X is DEFINED at global scope or in `std::`; forward-decl `namespace tt { class X; }` creates SHADOW type tt::X.

## Closure mechanism

**Structural discipline at audit time + memory codification + B17 blindspot pillar:**

1. **Forward-decl at GLOBAL scope when type lives globally** — the canonical fix:
   ```cpp
   // At top of header file, BEFORE any namespace block
   class CandleAccumulator;  // global scope
   // OR
   #include <chrono>  // bring in std::chrono::steady_clock; no fwd-decl needed
   namespace tt {
       // body that uses global ::CandleAccumulator or std::chrono::steady_clock
   }
   ```

2. **Sister blindspot pillar B17** at `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` (Stage 2 DRAFT 1st instance at `.B.6`; promotes to Stage 3 at 2nd canonical sister-application beyond Phase B.3 + Phase B.2)
3. **Sister memory codification** `feedback_forward_decl_at_global_scope_not_namespace.md` (Stage 2 DRAFT at `.B.6` Phase E ship close)
4. **`/blindspot-scan B17` audit** at pre-coding gate when plan body proposes header extraction or subfolder split from monolithic header
5. **Detection grep at audit time:**
   ```bash
   # Find forward-declarations inside namespace tt that may shadow global types
   rg "namespace tt \{[^}]*\bclass [A-Z]" --multiline -g '*.hpp'
   # For each match, verify the type is intentional tt::X (canonical) OR shadow risk
   ```

## Worked instances

### Instance 1 — Phase B.3 SlowPath.hpp extract (`tt::steady_clock` shadow)

**Context:** Per-core slow-path thread body extracted from monolithic `EngineSharded.hpp` into `CoreFrameworks/EngineSharded/SlowPath.hpp`. Original body used `auto t0 = std::chrono::steady_clock::now();` indirectly via a `using std::chrono::steady_clock;` line earlier in the monolithic file.

**Mistake:** During extraction, forward-decl `class steady_clock;` was placed inside `namespace tt { ... }` block to "make the sub-file self-contained without forcing `<chrono>` include in the header."

**Symptom:** `error: no member named 'now' in 'tt::steady_clock'`

**Fix:** Replace forward-decl with `#include <chrono>` at top of header file (above namespace block). Body uses `std::chrono::steady_clock::now()` directly.

### Instance 2 — Phase B.2 Async.hpp extract (`tt::CandleAccumulator` shadow)

**Context:** Drainer + fan-out + post-fill lambdas extracted from monolithic `EngineSharded.hpp` into `CoreFrameworks/EngineSharded/Async.hpp`. `CandleAccumulator` is a globally-defined type at `GUI/CandleAccumulator.hpp`.

**Mistake:** Forward-decl `class CandleAccumulator;` placed inside `namespace tt { ... }` block to avoid pulling in GUI header dependency in async sub-file.

**Symptom:** `error: variable has incomplete type 'tt::CandleAccumulator'`

**Fix:** Move forward-decl to GLOBAL scope (above the `namespace tt {` block):
```cpp
// CoreFrameworks/EngineSharded/Async.hpp
class CandleAccumulator;  // global scope forward decl
namespace tt {
    // body uses ::CandleAccumulator correctly
}
```

## Sister classes

- **Class 35** (Block-scope statics inaccessible from hoisted header functions) — sister at same monolithic-header-split surface; different root cause (block-scope statics vs forward-decl shadow); both surface at Phase B header extraction
- **Class 11** (Extensibility friction / silent drift) — parent meta-class; Class 34 is one shape of header-extraction-introduced drift
- **Class 18** (Mirror plans missing data-flow dependencies) — sister at the planning surface; both involve header-decomposition discipline

## Cross-references

- `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` (B17 sister pillar Stage 2 DRAFT — fwd-decl namespace shadow at header-extract surface)
- `DESIGN_SPECS/data-disciplines/cpp17-inline-variable-for-header-shared-state.md` (sister discipline at SAME surface — header-only shared state across TUs; both surfaced by monolithic-header subfolder split work)
- `feedback_forward_decl_at_global_scope_not_namespace.md` (sister memory; Stage 2 codification at `.B.6` Phase E ship close)
- `feedback_multi_surface_deletion_ordering_discipline.md` (B14 sister at deletion surface; B17 is the header-extraction analog)
- Phase B.3 + Phase B.2 commit messages in v5.15.5.F.4d.1.B.6 ship history
- Plan body `plans/v5.15-live-readiness/subplans/2026-05-27-v5.15.5.F.4d.1.B.6-enginesharded-subfolder-split.md` (worked instance documentation)
