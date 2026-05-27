---
name: feedback-cpp17-inline-variable-for-shared-state-across-tus
description: "When a header-only global variable must share storage across TUs (signal handler flags / test counters / runtime config snapshots / cross-thread state), declare it with C++17 `inline` keyword. NEVER `static` (each TU gets own copy → silent shared-state corruption). NEVER extern+define-in-cpp (defeats header-only convention)."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: phase-e-ship-close-v5.15.5.F.4d.1.B.6
---

When a header-only global variable must share storage across translation units (TUs), declare it with C++17 `inline`. NEVER `static`. NEVER extern+define-in-cpp.

**The rule:**

```cpp
// CORRECT: C++17 inline — single storage across all TUs (linker dedups via vague linkage)
inline volatile sig_atomic_t g_engine_shutdown = 0;
inline int tests_passed = 0;
inline void check(const char* name, bool cond) { /* ... */ }
```

```cpp
// WRONG: static — each TU gets its OWN copy
static volatile sig_atomic_t g_engine_shutdown = 0;
// Symptom: signal handler in TU A flips its copy; consumer in TU B reads its DIFFERENT copy = still 0 (silent shutdown failure)
```

```cpp
// WRONG: bare declaration in header — multiple-definition linker error
volatile sig_atomic_t g_engine_shutdown = 0;
// Linker fails: "multiple definition of `g_engine_shutdown`"
```

**Why:** Codified Stage 3 first canonical 2026-05-27 at v5.15.5.F.4d.1.B.6 ship close after 2 canonical applications in the same umbrella sprint:

1. `tests/test_common.hpp` @ `.B.5` WIP-B1 — `inline int tests_passed/failed` + `inline void check(...)` + `inline void test_warmup_ctrl(...)` extracted from monolithic `tests/controller_test.cpp` for test split prep
2. `CoreFrameworks/EngineSharded/Boot.hpp` @ `.B.6` WIP-B3 — 2 globals `g_engine_sharded_shutdown` + `g_engine_sharded_gui_quit_ptr` migrated `static` → `inline volatile sig_atomic_t` during monolithic header subfolder split

The Boot.hpp migration EXPOSED a latent bug: in the monolithic header, `static` "worked" because all consumers compiled into the same TU through aggregation. Subfolder split forced multi-TU compilation; `static` would have broken silently (signal handler writes its TU's copy; slow-path threads in different TU read their stale 0 copy).

**Default to `inline` from the start for shared header globals.** Don't wait for the split to surface the latent bug. The same discipline applies to cross-TU shared state generally — counters / flags / function definitions in headers.

## How to apply

1. **At header creation time:** if declaring a non-`const` file/namespace-scope variable in a `.hpp`, default to `inline` keyword unless explicitly intentional `static` (module-local; never cross-TU shared)
2. **At header extraction time** (header-extract / subfolder split / monolithic decomposition refactor): audit existing `static` declarations in extracted headers — flip to `inline` if cross-TU sharing intended (default for all globals that aren't deliberately module-local)
3. **At /dod-audit / /blindspot-scan B17 audit:** sweep headers for non-inline non-extern non-const file/namespace-scope variables; convert to `inline`

```bash
# Sweep pattern (header-only file-scope/namespace-scope variables without inline)
rg "^(static |volatile |sig_atomic_t|int|bool|float|double|size_t)" --type=cpp -g '*.hpp' | grep -v 'inline\|extern\|namespace\|constexpr\|//\|/\*'
```

## Anti-patterns

- **Future refactor "fixes" `inline` → `static`** (silent regression to per-TU copies; recognize via diff sweep)
- **`inline` on function-local static** (no-op; function-local statics already share storage via function symbol)
- **Forgetting `volatile` / `std::atomic` on cross-thread shared state** — `inline` solves linkage; concurrency primitives compose: `inline std::atomic<bool> g_flag{false};` is the canonical cross-thread shape
- **Using for hot-path cache-locality state** — `inline` puts state at a single global address; for cross-thread hot-path state needing `alignas(64)` per-core padding, prefer SPSC ring / seqlock cached cfg / per-core slow_state arrays

## Sister memories

- [[feedback_enumerate_helper_signature_args_before_extract]] — M6 parent discipline for helper extraction; this rule is sister at the header-only-globals layer
- [[feedback_multi_surface_deletion_ordering_discipline]] — B14 sister at deletion surface; this rule is the analog for monolithic-header decomposition

## DESIGN_SPECS sister

- `data-disciplines/cpp17-inline-variable-for-header-shared-state.md` (Stage 3 first canonical at v5.15.5.F.4d.1.B.6; 2 canonical applications worked-example documented)
- `meta-disciplines/implementation-layer-blindspot-taxonomy.md` B17 sister pillar (forward-decl namespace shadow — different root cause at same monolithic-header-split surface)
- `doc-disciplines/file-size-split-discipline.md` (parent file-size discipline that triggered the canonical applications via monolithic-header subfolder split)

## Recognition markers

- Declaring a non-`const` global in a `.hpp` header
- Header-extract / subfolder split / monolithic decomposition refactor
- Cross-thread shared flag / counter / runtime state
- "Signal doesn't propagate" / "counter wrong across modules" / "linker multiple-definition" symptoms

## When this rule applies

Per feedback_categorical_triggers_over_hardcoded_refs:

- Any header-only global variable declaration
- Any monolithic header extraction / subfolder split
- Any cross-TU shared state refactor
- Any `static` keyword in a `.hpp` at file/namespace scope (audit if cross-TU sharing intended)
