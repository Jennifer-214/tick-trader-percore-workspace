# Generic ring-buffer template pattern

**Established:** 2026-05-13 (v5.15.5.E.C — RollingIC + RollingRMSE Class-18 mirror closure)
**Status:** ACTIVE (NEW spec; codifies the pre-existing ad-hoc ring-buffer pattern as a reusable substrate)
**Cross-references:**
- CLAUDE.md item 13 (X-macro registry — sister substrate pattern)
- CLAUDE.md item 19 (structural fix preferred when bug class can recur — codification trigger)
- CLAUDE.md item 16 (reuse-audit principle — applies to ring-buffer adds)
- CLAUDE.md item 28 (latency-vs-cache framework — Stage 2 design space analysis)
- CLAUDE.md item 29 (sliding-window pattern — pairs with this template for stat-aggregator types)
- `structural-fix-preferred-decision-framework.md` (Class-18 mirror closure rationale)
- `pattern-codification-lifecycle.md` (this spec applies Stages 2 + 3 + 6 for the template)
- `cache-layout-discipline-for-hot-side-structs.md` Rule 4 (HOT-first ordering inside the template)
- `struct-padding-determinism-pattern.md` (explicit padding requirements when used in byte-equivalence contexts)
- `sliding-window-online-statistics-pattern.md` (companion pattern; templates compose for running-sum aggregates)
- First canonical applications: `ML_Headers/ConfidenceScore.hpp` — RollingIC + RollingRMSE compose `RollingWindow<double, ROLLING_IC_MAX_WINDOW>`

---

## Problem statement

A codebase that maintains rolling/sliding statistics over fixed-size windows accumulates ad-hoc ring-buffer structs:

```cpp
// Variant 1
struct RollingIC {
    double predictions[N];
    double actuals[N];
    int count, head, window;
};

// Variant 2
struct RollingRMSE {
    double squared_errors[N];
    int count, head, window;
};

// Variant 3
struct LargeTradeState {
    FPN<F> sizes[N];
    FPN<F> sum, sum_sq;
    int count, head;
};
```

Each variant duplicates the ring-buffer skeleton (sample array + count + head + window-or-capacity metadata) while differing in:
- Element type (`double`, `FPN<F>`, future custom types)
- Number of stored arrays (1 vs 2 vs N)
- Aggregated state (running sum, sum_sq, neither)
- Compute method (RMSE, Spearman, Z-score, EWMA)

**Failure modes of the ad-hoc shape:**

1. **Class-18 mirror drift** (per `structural-fix-preferred-decision-framework.md` + CLAUDE.md item 19): when N+1 future ring-buffer types each implement their own count/head/window logic, subtle drift accumulates. Example: RollingIC stores `window` as runtime int; RollingRMSE stores it too; future RollingFoo might forget to clamp window to capacity → out-of-bounds writes.

2. **Cache-layout discipline applied inconsistently** (per `cache-layout-discipline-for-hot-side-structs.md` Rule 4): some ring-buffer structs HOT-first; some not. Each variant re-decides the cache strategy. After auditing N variants, you find 3 different layout shapes for essentially the same data.

3. **AVX-512 vectorization scattered**: when a future ship vectorizes RollingFoo's Push, it has to redo the same SIMD discipline for each variant. Templating consolidates the SIMD application site to ONE template body.

4. **Padding bugs in byte-equivalence contexts**: per CLAUDE.md item 27, padding bytes leak through memcmp / SHA-256 / wire format. Multiple ring-buffer variants → multiple potential padding bugs. Template centralizes.

5. **Reuse-audit failure** (per CLAUDE.md item 16): contributors copy-paste from RollingIC → RollingFoo, missing the chance to extract a shared substrate.

The structural fix: **codify the ring-buffer skeleton as a generic template `RollingWindow<T, N>` that variants COMPOSE for their type-specific math.**

---

## Design space explored

### Alternative 1: Composition (chosen)

```cpp
struct RollingIC {
    RollingWindow<double, N> predictions_window;
    RollingWindow<double, N> actuals_window;
    // Compute logic accesses .samples + .count + .head
};
```

Trade-offs:
- ✓ Clear separation: template owns ring-buffer mechanics; variant owns math semantics
- ✓ Type-specific accessors stay in the variant's namespace
- ✓ Each variant can hold MULTIPLE ring-buffers if needed (e.g., RollingIC's parallel predictions + actuals)
- ✗ Two indirection levels: `cs->ic.predictions_window.samples[idx]` (vs prior `cs->ic.predictions[idx]`)
- ✗ Slightly more verbose field paths

### Alternative 2: Inheritance

```cpp
struct RollingIC : public RollingWindow<double, N> { ... };
```

Trade-offs:
- ✓ Cleaner field paths (predictions inherited directly)
- ✗ Forces single-buffer variants (can't have parallel predictions + actuals)
- ✗ Inheritance hierarchy adds complexity; codebase convention is C-style + templates, NOT inheritance (CLAUDE.md code conventions: "C-style with templates, no classes")
- **REJECTED**: violates codebase convention.

### Alternative 3: Just-leave-it-ad-hoc

Trade-offs:
- ✓ No refactor cost
- ✗ Mirror drift accumulates (per failure modes above)
- ✗ Future RollingFoo ships duplicate the skeleton again
- ✗ Doesn't close the Class-18 mirror that already exists (RollingIC ≅ RollingRMSE)
- **REJECTED per CLAUDE.md item 19**: structural fix preferred when bug class can recur.

### Alternative 4: AoS sample-pair struct + template

```cpp
template <typename T1, typename T2, unsigned N>
struct RollingPairWindow {
    struct Pair { T1 a; T2 b; };
    Pair samples[N];
    int count, head;
};
```

Trade-offs:
- ✓ Single struct for parallel-array variants (RollingIC's predictions + actuals)
- ✓ AoS cache locality (1 cache line per iteration vs 2)
- ✗ Forces same N for both arrays (currently true; rigid for future)
- ✗ More complex; harder to reason about per-element type
- **DEFERRED**: useful future extension; not in scope for v5.15.5.E first reference. Add as future-application candidate after 2+ ring-buffer types want it.

### Why not "use std::array + std::ring_buffer"?

C++ STL ring-buffer types (e.g., proposed `std::ring_buffer`) bring exception-safety + iterator overhead. This codebase is no-exceptions + no-RTTI per `STRATEGY_AND_CODING_RULES.md`. Hand-written template is consistent with codebase style (RollingStats, BookImbalanceHistory all use plain templated structs).

---

## The pattern (concrete shape)

### Template declaration

```cpp
// v5.15.5.E.C — Generic ring-buffer template. Variants compose this for
// type-specific math; cache-layout discipline applied here once.
//
// T: element type (typically double, FPN<F>, or a Sample{x,y} struct)
// N: compile-time capacity
//
// Layout: HOT scalars (count + head + window) at offset 0;
//         COLD samples[N] following. alignas(64) on struct.
//
// Pattern: generic-ring-buffer-template-pattern.md
template <typename T, unsigned N>
struct alignas(64) RollingWindow {
    static constexpr unsigned CAPACITY = N;

    // HOT cluster (offset 0; touched per Push + per Compute)
    int count;     // valid samples [0, N]
    int head;      // next write idx mod N
    int window;    // currently-configured window [2, N]; runtime-tunable

    // COLD cluster (offset 16; touched at samples[head] per Push)
    T   samples[N];
};

// Layout locks (typedef per .D.A pattern to handle multi-arg template + offsetof)
// Variant-specific instantiations add their own locks in the variant's TU.
```

### Init

```cpp
template <typename T, unsigned N>
static inline void RollingWindow_Init(RollingWindow<T, N>* w, int window) {
    memset(w, 0, sizeof(*w));
    if (window < 2)  window = 2;
    if (window > (int)N) window = (int)N;
    w->window = window;
}
```

### Push (single sample)

```cpp
template <typename T, unsigned N>
static inline void RollingWindow_Push(RollingWindow<T, N>* w, T sample) {
    int idx = w->head % w->window;
    w->samples[idx] = sample;
    w->head++;
    if (w->count < w->window) w->count++;
}
```

### Composing variant types

A variant struct embeds one or more `RollingWindow<T, N>` instances + its type-specific Compute logic:

```cpp
// RollingIC — Spearman rank correlation over (prediction, actual) pairs
struct alignas(64) RollingIC {
    RollingWindow<double, ROLLING_IC_MAX_WINDOW> predictions_window;
    RollingWindow<double, ROLLING_IC_MAX_WINDOW> actuals_window;
};

static inline void RollingIC_Init(RollingIC* r, int window) {
    RollingWindow_Init(&r->predictions_window, window);
    RollingWindow_Init(&r->actuals_window, window);
}

static inline void RollingIC_Push(RollingIC* r, double pred, double actual) {
    RollingWindow_Push(&r->predictions_window, pred);
    RollingWindow_Push(&r->actuals_window, actual);
}

static inline double RollingIC_Compute(const RollingIC* r) {
    // Type-specific math (Spearman rank correlation) — composes the template's
    // samples + count via member access.
    // ... (see ConfidenceScore.hpp for full body)
}
```

### Layout locks for variant instantiations

Each variant's TU adds:

```cpp
using RollingWindowDoubleDefaultT = RollingWindow<double, ROLLING_IC_MAX_WINDOW>;
static_assert(sizeof(RollingWindowDoubleDefaultT) == /*captured*/ 0, "...");
static_assert(offsetof(RollingWindowDoubleDefaultT, count) == 0, "HOT scalar at offset 0");
static_assert(offsetof(RollingWindowDoubleDefaultT, samples) == 16, "COLD cluster at offset 16");
static_assert(alignof(RollingWindowDoubleDefaultT) == 64, "cache-line aligned");
```

---

## Trade-offs + when to apply

### Apply when:

- New ring-buffer struct needs count + head + window + samples[] in same layout
- 2+ ring-buffer variants share the skeleton (Class-18 mirror trigger per `structural-fix-preferred-decision-framework.md`)
- Variant doesn't need to bit-pack fields inside the ring (template is generic; variant's type can be a struct if packing needed)
- Window size is compile-time known (template parameter N)

### Skip when:

- Ring-buffer is one-off (no 2nd variant likely)
- Element type itself needs templating beyond just a type parameter (e.g., variadic templates for heterogeneous samples)
- Variant needs control over per-element padding or alignment that differs from template's `alignas(64)` (rare)
- The variant's running aggregate maintenance is the load-bearing structure (use `sliding-window-online-statistics-pattern.md` instead; that's where the aggregate state lives)

### Cost:

- One template definition (~40 LOC)
- Each variant's Push/Compute/Init gains 1 indirection level in field paths (e.g., `r->samples[i]` → `r->window.samples[i]`)
- Layout locks per instantiation (3-4 static_asserts)

### Win:

- Class-18 mirror closed for ring-buffer skeleton drift
- Cache-layout discipline applied ONCE for all ring-buffer types
- Future variants reuse the template; new ring-buffer adds = ~30 LOC (template instantiation + Compute fn) vs ~150 LOC from scratch
- `/dod-audit` Stage 6 enforcement (see Audit detection section below) catches "new ring-buffer struct that doesn't use the template" automatically
- AVX-512 vectorization (when added) applies to ONE template body, not N variants
- Pairs naturally with `sliding-window-online-statistics-pattern.md` — variants that maintain running sums get the running-sum field colocated with the embedded RollingWindow

---

## Reference implementations

### v5.15.5.E.C — First canonical applications

| Variant | Composition | Compute math |
|---|---|---|
| `RollingIC` | 2× `RollingWindow<double, ROLLING_IC_MAX_WINDOW>` (predictions + actuals) | Spearman rank correlation |
| `RollingRMSE` | 1× `RollingWindow<double, ROLLING_IC_MAX_WINDOW>` + `double sum_squared_errors` running aggregate (per `sliding-window-online-statistics-pattern.md` 3rd app) | O(1) sqrt(sum_sse / count) |

Both shipped in v5.15.5.E.C. Class-18 mirror between them CLOSED structurally — the skeleton is shared; only the Compute math differs.

### Future application candidates

Adjacent ring-buffer structs in the codebase that COULD migrate to the template (deferred to follow-up sprints per pattern-codification-lifecycle.md Stage 7 wider audit):

| Existing struct | File | Notes |
|---|---|---|
| `BookImbalanceHistory<F, W>` | `ML_Headers/FlowFeatures.hpp` | Already templated; could compose RollingWindow internally OR stay independent (it has dual-window state from v5.15.5.D; might prefer to keep that specialization for clarity) |
| `LargeTradeState<F, W>` | `ML_Headers/FlowFeatures.hpp` | Has running sum + sum_sq; would compose `RollingWindow<FPN<F>, W>` + 2 aggregate fields |
| `SpreadState<F, W>` | `ML_Headers/FlowFeatures.hpp` | Same shape as LargeTradeState; would benefit from shared template |
| `RollingStats<F, W>` | `ML_Headers/RollingStats.hpp` | More complex (slope + r-squared + EWMA); independent investigation needed |
| `RORRegressor<F>` | `ML_Headers/ROR_regressor.hpp` | Maintains sample window for regression; candidate |
| `RollingTurnover` | `ML_Headers/RollingTurnover.hpp` | Likely candidate |
| `DriftHistory.samples[256]` | `ML_Headers/ConfidenceScore.hpp` (post-.E.B AoS) | Could compose `RollingWindow<DriftSample, 256>` (would unify with RollingIC/RollingRMSE) |

Each future application triggers Stage 4 (subsequent application) of the codification lifecycle. /dod-audit Stage 6 detection signature flags them automatically.

---

## Lessons / gotchas

### Field-path verbosity at compose sites

`cs->ic.predictions_window.samples[idx]` vs prior `cs->ic.predictions[idx]`. Adds one path component. Acceptable cost for the structural win; future contributors discover the pattern via the DESIGN_SPEC.

**Mitigation**: use `auto& w = cs->ic.predictions_window;` local references in tight loops if readability matters.

### Template + offsetof requires typedef alias (per .D.A discovery)

The C preprocessor sees `offsetof(RollingWindow<double, N>, samples)` as 3 macro args because of the comma in `<...>`. Fix: typedef the instantiation first.

```cpp
using RollingWindowDoubleN_T = RollingWindow<double, N>;
static_assert(offsetof(RollingWindowDoubleN_T, samples) == 16, "...");
```

Same pattern as v5.15.5.D's `BookImbHistDefaultT` typedef.

### `<cstddef>` include for offsetof

GCC transitively includes offsetof through other headers; clangd doesn't. Add explicit `#include <cstddef>` in the file defining the template + its layout locks.

### memset(s, 0, sizeof(*s)) is still safe with alignas(64)

The struct's alignas trailing pad is included in sizeof; memset zeros it cleanly. Default-init via Init() function is the canonical entry point.

### RollingWindow alone is not the sliding-window pattern

This template provides the SKELETON. The actual statistical-aggregate maintenance (running sum, sum_sq, EWMA decay) is per `sliding-window-online-statistics-pattern.md` Approach 3. Variants that need O(1) aggregates COMPOSE both patterns: embed RollingWindow + add aggregate fields + maintain in Push.

RollingRMSE in v5.15.5.E.D is the first canonical example of this composition.

### Don't template-parameterize alignment

`alignas(64)` is hardcoded inside the template. Don't parameterize via `template <typename T, unsigned N, unsigned Align = 64>` — it's almost always 64 for hot-side ring buffers, and parameterizing creates a templating taxonomy that doesn't add value. If a future variant needs different alignment, instantiate a sibling template.

---

## Audit detection

`/dod-audit` should flag candidates for template reuse + missed applications:

### Symptom 1 — new ring-buffer struct with manual skeleton

```cpp
struct SomeNewStat {
    double samples[N];        // ← array of fixed size N
    int count;                // ← valid count
    int head;                 // ← ring head
    // ... possibly window or other fields
};
```

When `/dod-audit` finds this pattern WITHOUT `RollingWindow<T, N>` composition, flag as **MISSED — generic-ring-buffer-template-pattern**. Recommend: refactor to compose `RollingWindow<T, N>` per the spec.

### Symptom 2 — duplicate Push function across ring-buffer types

Multiple `_Push` functions with identical bodies (`int idx = X->head % X->window; X->samples[idx] = sample; X->head++; if (X->count < X->window) X->count++;`). The duplication = Class-18 mirror; refactor to compose RollingWindow which provides RollingWindow_Push generically.

### Symptom 3 — ring-buffer struct without alignas(64) + layout locks

Even if the struct doesn't use the template, ring-buffer-shaped structs touched per slow-path cycle should be alignas(64) per cache-layout-discipline-for-hot-side-structs.md Rule 4. Flag as cache-discipline audit finding; recommend RollingWindow composition as the simultaneous fix.

### /dod-audit integration

Skill update: add baseline check category `3k` (ring-buffer skeleton detection) pointing at this DESIGN_SPEC. v5.15.5.E.C ship adds the category. Future contributors who write a new ring-buffer struct from scratch get a /dod-audit finding pointing them at the template.

---

## Patterns NOT used here (and why)

### inheritance (`struct RollingIC : public RollingWindow<...>`)

Violates codebase convention (CLAUDE.md "C-style with templates, no classes"). Rejected.

### CRTP (curiously recurring template pattern)

Overkill for the simple skeleton. RollingWindow is a data substrate, not a behavior interface. No need for static polymorphism via CRTP.

### Single std::vector / std::array per variant

STL containers bring exception-safety + iterator overhead. Codebase is no-exceptions per STRATEGY_AND_CODING_RULES.md. Plain `T samples[N]` array matches existing convention (BookImbHistory, LargeTradeState, etc.).

### Concept-based constraints (`template <Numeric T, unsigned N> requires ...`)

C++20 concepts add value for generic-library code but are overkill for an internal substrate. Plain template parameters suffice; misuse caught at compile time via the variant's Compute body.

---

## Cross-references

- `CLAUDE.md` items 13, 16, 19, 28, 29
- `structural-fix-preferred-decision-framework.md` (codification trigger: Class-18 mirror RollingIC ≅ RollingRMSE)
- `pattern-codification-lifecycle.md` (this spec applies Stages 2 + 3 + 6)
- `cache-layout-discipline-for-hot-side-structs.md` Rule 4 (HOT-first ordering inside the template)
- `struct-padding-determinism-pattern.md` (explicit padding when ring-buffer types enter byte-equivalence contexts; not applicable to v5.15.5.E.C first apps since wire format is field-by-field per `wire-format-byte-preservation-discipline.md`)
- `sliding-window-online-statistics-pattern.md` (companion pattern; RollingRMSE composes both in v5.15.5.E.D)
- `latency-vs-cache-decision-framework.md` (CLAUDE.md item 28; framework that motivates cache-layout discipline inside the template)
- `wire-format-byte-preservation-discipline.md` (when ring-buffer state crosses persistence boundary, use registry pattern; see v5.15.5.E.0 FOREACH_CONFIDENCE_PERSIST_FIELD)
- v5.15.5.E.C subplan: `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.E-confidence-cache-layout-sweep.md`
- First reference applications: `ML_Headers/ConfidenceScore.hpp` — RollingIC + RollingRMSE
- BookImbalanceHistory<F, W> (v5.15.5.D): independent templated ring; future candidate for migration to RollingWindow composition

## Promotion criteria (this doc was promoted)

Per CLAUDE.local.md "codify design principles in CLAUDE.md as patterns mature" rule:
- 2+ applications: ✓ (RollingIC + RollingRMSE in v5.15.5.E.C)
- DESIGN_SPEC documented: ✓ (this doc)
- Pattern applies broadly: ✓ (≥6 candidate future applications listed above)

→ Promotion to CLAUDE.md item planned at v5.15.5.E.C ship close OR at 3rd application trigger (whichever comes first). For v5.15.5.E.C, this DESIGN_SPEC is the codification artifact; CLAUDE.md cross-link added in umbrella ship via item-update.

---

**End of spec.**
