---
type: data-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-05-27
tags: [cpp17, header-only, shared-state, linker-deduplication]
surface: [boot-time, test-infrastructure]
sister_specs: [file-size-split-discipline.md, cache-line-discipline.md]
applies_at_skills: [/dod-audit, /blindspot-scan, /hft-audit]
---

# C++17 inline variable for header-only shared state

**Established:** 2026-05-27 (v5.15.5.F.4d.1.B.6 Phase B WIP-B3 EngineSharded subfolder split; codified after 2nd canonical application in the same umbrella sprint)
**Status:** Stage 3 FIRST CANONICAL v1.0 — 2 canonical applications landed (tests/test_common.hpp @ `.B.5` WIP-B1 + CoreFrameworks/EngineSharded/Boot.hpp @ `.B.6` WIP-B3); promote to Stage 4 cohort when ≥2 additional applications surface

When a header-only global variable must share storage across translation units (TUs), declare it with C++17 `inline`. NEVER `static` (each TU gets its own copy — silent shared-state corruption). NEVER extern+define-in-cpp (defeats header-only convention; forces a `.cpp` file for what should be a pure header artifact).

---

## What + when

**Applies when:** a global variable lives in a `.hpp` header AND is `#include`d by ≥2 TUs AND those TUs must share the same storage (e.g., a counter, a signal flag, a config struct, a function with module-local state).

**Mechanism:** C++17 `inline` on variable declarations tells the linker "this symbol may appear in multiple TUs; dedup all definitions to a single storage slot." Linker dedups via vague linkage (same mechanism that backs inline functions + template instantiations). One backing storage; all TUs see it.

```cpp
// CORRECT: C++17 inline — single storage across all TUs
inline volatile sig_atomic_t g_engine_shutdown = 0;
inline int tests_passed = 0;
inline int tests_failed = 0;
inline void check(const char* name, bool cond) { /* ... */ }
```

```cpp
// WRONG: static — each TU gets its OWN copy
static volatile sig_atomic_t g_engine_shutdown = 0;  // TU A's copy is independent from TU B's copy
// Symptom: signal handler in TU A flips its copy; consumer in TU B reads its DIFFERENT copy = still 0
```

```cpp
// WRONG: bare declaration in header without inline — multiple-definition linker error
volatile sig_atomic_t g_engine_shutdown = 0;  // every TU including this header gets a definition
// Linker fails: "multiple definition of `g_engine_shutdown`"
```

---

## Why not `static`

In a header, `static` gives each including TU its own private copy (internal linkage). Signal handlers, RAII registration paths, and any cross-TU consumer pattern fails silently — writes to TU A's copy are invisible to TU B.

This is the FATAL shape of the canonical instance at `.B.6` Phase B.3: when `g_engine_sharded_shutdown` was originally declared `static` in `EngineSharded.hpp`, the signal handler ran from the TU containing the `signal()` setup, but the slow-path threads checking the flag for shutdown were in a DIFFERENT TU. Shutdown signal flipped the handler's copy; threads kept polling their stale 0. Resolution: `inline volatile sig_atomic_t` — one storage, one shutdown.

Detection retroactively: if a header-only flag "doesn't propagate" across module boundaries, suspect `static` in header.

---

## Why not extern+define-in-cpp

The traditional pre-C++17 pattern was:
```cpp
// header (.hpp)
extern volatile sig_atomic_t g_engine_shutdown;
// body (.cpp)
volatile sig_atomic_t g_engine_shutdown = 0;
```

This works correctly (single storage) but introduces a `.cpp` file for what should be header-only. For libraries / engines that pride themselves on header-only ergonomics (no per-symbol `.cpp` files; consumer includes one header), the extern+define pattern adds friction at every cross-TU global declaration.

C++17 `inline` variables eliminate that friction. Single header. Single line. Linker handles deduplication via vague linkage. No accompanying `.cpp` required.

---

## Mechanism (linker semantics)

C++17 `inline` for variables triggers **vague linkage** (the same linker concept that powers inline functions + template instantiations):

1. Each TU that includes the header gets a copy of the definition.
2. At link time, the linker sees N copies of the symbol with `inline` (= "comdat" / "weak" linkage on most ELF + COFF toolchains).
3. Linker picks ONE copy as canonical; discards the rest.
4. All cross-TU references resolve to the single canonical copy.
5. Initialization happens exactly once at startup (per the C++ standard's [basic.start.dynamic] guarantee for inline variables).

**Result:** one backing storage slot, identical to extern+define-in-cpp but without the `.cpp` file.

---

## Anti-pattern warnings

### A1 — Future refactor that "undoes" `inline` via `static` quick-fix

When refactoring (e.g., extracting a header into a subfolder), do NOT replace `inline` with `static` to "simplify" or "make it local to the header." `static` REGRESSES to per-TU copies. The `inline` keyword IS the discipline; preserve it across refactors.

**Recognition:** Search diff for `-inline ... = ... ;` lines paired with `+static ... = ... ;` lines. That's the silent regression.

### A2 — `inline` on a function-local static (no-op confusion)

`inline static int counter = 0;` inside a function body is NOT the cross-TU-sharing pattern. Function-local statics already share storage by their nature (the function is one symbol; its static is one slot). The `inline` keyword on function-local statics is harmless but adds nothing.

The discipline applies to FILE-SCOPE / NAMESPACE-SCOPE / CLASS-STATIC variables in headers.

### A3 — Forgetting `volatile` / `std::atomic` on cross-thread shared state

`inline` solves the **linkage** problem (one storage). It does NOT solve the **concurrency** problem. If multiple threads read/write the inline variable, the variable still needs `volatile sig_atomic_t` (for signal handlers) or `std::atomic<T>` (for general cross-thread). `inline` + concurrency primitives compose: `inline std::atomic<bool> g_flag{false};` is the canonical shape.

### A4 — Class-static initialization inside body shadowing inline

`class Foo { static inline int counter = 0; };` is C++17's inline-static-member shape. It's the class-member analog of the variable pattern. Use it for class-static members; it has the same vague-linkage semantics. Forgetting `inline` on class-static + defining in body produces multiple-definition errors at link.

### A5 — Don't use for hot-path state expecting cache locality

`inline` puts shared state at a single global address. For cross-thread hot-path state that needs `alignas(64)` + per-core padding to prevent false-sharing, prefer SPSC ring / seqlock cached cfg / per-core slow_state arrays. `inline` is appropriate for COARSE shared state (shutdown flags / test counters / runtime config snapshots), not for hot-path per-core data structures.

---

## Worked examples (canonical applications)

### Application 1 — tests/test_common.hpp (v5.15.5.F.4d.1.B.5 WIP-B1; 2026-05-27)

**Surface:** Test helper extracted from monolithic `tests/controller_test.cpp` (26,259 lines) into shared `tests/test_common.hpp` to prepare for full domain-aligned test split (TECH_DEBT-127).

**Shared state:**
```cpp
// tests/test_common.hpp
inline int tests_passed = 0;
inline int tests_failed = 0;
inline void check(const char* name, bool cond) {
    if (cond) ++tests_passed; else ++tests_failed;
    /* ... */
}
inline void test_warmup_ctrl(/* ... */) { /* ... */ }
```

**Why inline:** When sub-binaries link `test_common.hpp` independently, each binary gets its OWN `tests_passed` counter (per-binary independence). But within a single umbrella binary that links multiple test domain TUs (each `#include`ing test_common.hpp), all TUs share the SAME counters. The `inline` keyword gives both behaviors automatically: per-binary independence (when test_common.hpp's sole including TU compiles to one binary) + single-binary aggregation (when multiple TUs are linked into one binary).

**Lesson:** If `static int tests_passed` had been used instead, each TU within an umbrella binary would have its own counter, and the final ledger ("3215 passed / 0 failed") would silently report only the last-incremented TU's count. Total counts would be wrong WITHOUT compile failure.

### Application 2 — CoreFrameworks/EngineSharded/Boot.hpp (v5.15.5.F.4d.1.B.6 WIP-B3; 2026-05-27)

**Surface:** Engine boot path extracted from monolithic `CoreFrameworks/EngineSharded.hpp` (3,202 lines) into subfolder split (`EngineSharded/Boot.hpp` + `SlowPath.hpp` + `Async.hpp` + `Run.hpp`); INDEX shim at `EngineSharded.hpp` re-exports.

**Shared state:**
```cpp
// CoreFrameworks/EngineSharded/Boot.hpp
inline volatile sig_atomic_t g_engine_sharded_shutdown = 0;
inline volatile sig_atomic_t* g_engine_sharded_gui_quit_ptr = nullptr;
```

**Why inline:** Signal handler installed in one TU (e.g., the TU containing `main()` or `EngineSharded_Run`) writes the shutdown flag; slow-path threads polling for shutdown live in DIFFERENT TUs (the per-core slow-path TUs). All TUs must observe the SAME flag. The `inline` keyword guarantees one backing storage.

Originally (pre-`.B.6`), these globals were declared `static` in the monolithic header. The boot path + slow-path threads happened to compile into the SAME TU (via aggregation through EngineSharded.hpp), so `static` "worked" by accident — there was effectively only one TU after preprocessing. Subfolder split forced multi-TU compilation; `static` would have broken silently.

Migration from `static` → `inline` is the canonical 1-keyword change that closes the latent multi-TU silent-corruption bug class for header-only globals.

**Lesson:** The bug was LATENT in the monolithic header (worked by aggregation accident). Splitting surfaced the discipline. Always-default to `inline` for shared header globals from the start; don't wait for the split to force the discipline.

---

## Detection at audit time

`/dod-audit` + `/blindspot-scan` (B17 sister pillar — see implementation-layer-blindspot-taxonomy.md) check:

- Header-only `.hpp` declares a non-`const` non-template variable at file/namespace scope
- Declaration uses `static` (regress to per-TU copy; silent shared-state corruption if cross-TU sharing intended)
- Declaration uses no specifier (multiple-definition linker error at link time)
- → finding: convert to `inline` if cross-TU sharing intended; convert to `constexpr` + `inline` if compile-time-constant; convert to function-local-static if module-local

`grep` pattern for sweep:
```bash
# Find non-inline, non-extern globals in headers
rg "^(static |volatile |sig_atomic_t|int|bool|float|double|size_t)" --type=cpp -g '*.hpp' | grep -v 'inline\|extern\|namespace\|constexpr\|//\|/\*'
```

---

## Pattern lifecycle

- **Stage 1 (problem identification):** v5.15.5.F.4d.1.B.5 WIP-B1 — `tests/test_common.hpp` extraction surfaced "do we use static or inline here?" decision. Stage 1 signal.
- **Stage 2 (DESIGN_SPEC DRAFT):** SKIPPED — pattern matured directly via 2nd canonical
- **Stage 3 (first canonical) — THIS DOC (2026-05-27):** 2 applications landed in same umbrella sprint (test_common.hpp + EngineSharded/Boot.hpp). DESIGN_SPEC codified at v5.15.5.F.4d.1.B.6 ship close.
- **Stage 4 (cohort migration):** future application(s) at any `.hpp` header extract / monolithic-header split / shared-flag refactor will reference this spec
- **Stage 5 (CLAUDE.md promotion):** when pattern is invoked at ≥3 unrelated surfaces (target: Stage 4 cohort → promote)
- **Stage 6 (CI tool enforcement):** `tools/check_inline_variable_discipline.py` (queued; sister to `tools/check_doc_metadata.py`) — sweep all `.hpp` headers; flag non-const non-template file-scope/namespace-scope variables without `inline`

---

## Cross-references

- Sister: `file-size-split-discipline.md` (parent discipline that triggered both canonical applications; subfolder/per-domain split surfaces the multi-TU shared-state question that this spec answers)
- Sister: `cache-line-discipline.md` (companion DOD discipline; `inline` for shared state ≠ `alignas(64)` for hot-path cache locality — the two patterns compose for different use cases)
- Sister memory: `feedback_cpp17_inline_variable_for_shared_state_across_tus.md` (operator-collaboration trigger memory; this DESIGN_SPEC is the pattern body)
- Sister blindspot pillar: implementation-layer-blindspot-taxonomy.md B17 (header-only global declaration audit — same root cause; pillar perspective)
- Companion bug class: RECURRING_BUG_PATTERNS Class 34 (Forward-decl namespace shadow; sister-class at the `.B.6` split surface) — different root cause (namespace shadow vs `static` vs `inline`), but both surfaced by the same monolithic-header-split work
- CLAUDE.md § Hard invariants — H3 (no `std::mutex`); `inline` + `std::atomic` is the canonical cross-thread shared-state shape that respects H3 (atomics are not mutexes)
- C++17 standard: [basic.def.odr] paragraph 6 + [dcl.inline] paragraphs 9-12 (vague linkage for inline variables)

---

**End of cpp17-inline-variable-for-header-shared-state v1.0 STAGE 3 FIRST CANONICAL.** Stage 4 cohort promotion at next application beyond the 2 canonical instances.
