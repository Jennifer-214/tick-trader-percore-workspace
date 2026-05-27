---
name: feedback-forward-decl-at-global-scope-not-namespace
description: "When forward-declaring a type that lives at global scope OR in std::, place the forward-decl at GLOBAL scope (NOT inside `namespace tt { ... }`). Forward-decl inside namespace creates a NEW shadow type tt::X distinct from ::X. Codified Stage 2 DRAFT 2026-05-27 after 2 instances in v5.15.5.F.4d.1.B.6 Phase B (steady_clock + CandleAccumulator shadows). Sister to Class 34 + B17 pillar."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: phase-e-ship-close-v5.15.5.F.4d.1.B.6
---

**When forward-declaring a type that lives at global scope OR in std::, place the forward-decl at GLOBAL scope.** NOT inside `namespace tt { ... }`. C++ name resolution makes `tt::X` a DISTINCT type from `::X` even when X is otherwise undefined — the forward-decl-inside-namespace creates a NEW shadow type.

```cpp
// WRONG: forward-decl inside namespace shadows global type
namespace tt {
    class steady_clock;  // creates tt::steady_clock; does NOT refer to std::chrono::steady_clock
    void body() {
        auto t = steady_clock::now();  // resolves to tt::steady_clock → "no member named 'now'"
    }
}
```

```cpp
// CORRECT: forward-decl at global scope OR include the header
class CandleAccumulator;  // refers to ::CandleAccumulator
#include <chrono>         // brings in std::chrono::steady_clock (preferred for std types)
namespace tt {
    void body(CandleAccumulator* acc) { /* uses ::CandleAccumulator + std::chrono::steady_clock */ }
}
```

**Why:** Codified Stage 2 DRAFT 2026-05-27 at v5.15.5.F.4d.1.B.6 Phase B (monolithic-header subfolder split) after 2 instances surfaced in same Phase B work:

1. Phase B.3 SlowPath.hpp extract: `namespace tt { class steady_clock; }` shadowed `std::chrono::steady_clock`
2. Phase B.2 Async.hpp extract: `namespace tt { class CandleAccumulator; }` shadowed global `::CandleAccumulator`

Both compile-failed; both required moving forward-decl to global scope (or using `#include` for std types). Recurrence trigger: 2 instances in same Phase B work → categorical pattern at header-extraction surface.

**Prefer `#include <header>` over forward-decl for standard library types.** Cleaner; doesn't risk the shadow surface; future maintainers don't have to navigate "where is std::chrono::steady_clock declared?"

## How to apply

1. **At header-extract / subfolder-split time:** before placing any forward-decl inside `namespace tt { ... }`, ask "is X a global type OR std:: type?" — if YES, place forward-decl at GLOBAL scope above the namespace block (or `#include` proper header for std types)
2. **At /blindspot-scan B17 audit:** sweep sub-files for forward-decls inside namespace blocks; classify each per the C-bucket rubric (intentional tt::X / sister namespace type / re-export alias / shadow risk); fix shadow risks
3. **Detection grep:**
   ```bash
   # Forward-decls inside namespace tt that may shadow global types
   rg "namespace tt \{[^}]*\bclass [A-Z]" --multiline -g '*.hpp'
   # For each match, verify the type is intentional tt::X OR shadow risk
   ```

## False-positive surface

- **Intentional `tt::X` types** (canonical types in `tt` namespace; e.g., `tt::FPN<F>`) — forward-decl inside namespace is correct
- **Sister namespace types** (legitimately `tt::`-scoped; e.g., `tt::ConfidenceScorer`) — forward-decl inside namespace is correct
- **Re-export aliases** (`namespace tt { using ::SomeGlobalType; }`) — export shape, not forward-decl

The Class 34 / B17 shape is specifically: type X DEFINED at global scope or in `std::`; forward-decl `namespace tt { class X; }` creates SHADOW type.

## Sister memories

- [[feedback_enumerate_block_scope_statics_before_hoist]] — sister at same monolithic-header-split surface; different root cause (block-scope statics vs forward-decl shadow); B18 sister pillar
- [[feedback_cpp17_inline_variable_for_shared_state_across_tus]] — companion at SAME surface (header-only shared state); both surfaced by `.B.6` monolithic-header subfolder split work

## DESIGN_SPECS sister

- `DOCS/recurring-bug-patterns/class-34-forward-decl-namespace-shadow.md` (the Class entry; this memory is the operator-collaboration trigger)
- `meta-disciplines/implementation-layer-blindspot-taxonomy.md` B17 sister pillar (Stage 2 DRAFT)
- `data-disciplines/cpp17-inline-variable-for-header-shared-state.md` (sister discipline at same surface)

## Recognition markers

- Header-extract / subfolder-split / monolithic-header decomposition refactor
- Forward-decl `namespace tt { class X; }` in newly-extracted sub-file
- Compile error: "no member named 'X' in scope" / "incomplete type 'tt::Y'" / "use of undeclared identifier"
- Sub-file in a project namespace blocks needing types from `<chrono>` / `<string>` / `<vector>` / etc.

## When this rule applies

Per feedback_categorical_triggers_over_hardcoded_refs:

- Any monolithic-header subfolder split / header extraction
- Any sub-file declaring forward-decls inside namespace block
- Any "type not found" / "incomplete type" compile error during header-extract work
- Any audit-time sweep for header-decomposition discipline
