---
type: refactor-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-10
tags: [data-oriented-design, branchless-discipline]
surface: [hot-path, slow-path, bitmap-packed]
sister_specs: [bitmap-flag-api.md, partner-core-bitmap-pattern.md, composed-filter-mask-pattern.md, registry-bitmap-set-discipline.md]
applies_at_skills: []
---

# Transient aggregation bitmap pattern (local-scope summary bitmap with headroom)

**Established:** 2026-05-10 (v5.14.9.H — ShardedSnapshot scaler_summary_flags)
**Status:** ACTIVE
**Cross-references:**
- Parent: `bitmap-flag-api.md` (BITMAP_IS_SET / MASK constants)
- Sister: `partner-core-bitmap-pattern.md` (different scope: per-node bitmap vs aggregation bitmap)
- First application: `CoreFrameworks/ShardedSnapshot.hpp:615-645` (scaler_summary_flags)
- CLAUDE.md item 20 (bit-packed flag storage)
- TECH_DEBT-013 (candidate 7)

---

## Problem statement

A function aggregates multiple boolean signals into a SUMMARY before consuming them. The booleans live for ONE FUNCTION CALL — they're not persisted to a struct, not exposed across threads, not part of the wire format. Just transient locals.

**Pre-bitmap pattern (multiple booleans):**

```cpp
// In ShardedSnapshot snap-publish loop, per core:
bool any_scaler_present = false;
bool any_scaler_failed = false;

if (zoo->buy_signal.scaler.has_scaler)    any_scaler_present = true;
if (zoo->barrier.scaler.has_scaler)       any_scaler_present = true;
if (zoo->regime.scaler.has_scaler)        any_scaler_present = true;
if (zoo->exit.scaler.has_scaler)          any_scaler_present = true;
if (zoo->buy_signal.scaler_load_failed)   any_scaler_failed = true;
if (zoo->barrier.scaler_load_failed)      any_scaler_failed = true;
// ...

snap->per_core[i].ml_scaler_present = any_scaler_present ? 1 : 0;
if (any_scaler_failed) FAILURE_SET(snap->per_core[i], ml_scaler_load_failed);
```

**Pain points:**

1. 2 booleans now; adding a 3rd "any_scaler_<X>" requires a 3rd bool + 4-8 more if-statements.
2. No headroom — refactoring to add the 3rd flag touches every aggregation site.
3. Branching pattern is verbose; multi-flag check requires N branches.

**Bitmap pattern (single field with masks):**

```cpp
static constexpr uint8_t MASK_SCALER_PRESENT = (uint8_t)(1u << 0);
static constexpr uint8_t MASK_SCALER_FAILED  = (uint8_t)(1u << 1);
uint8_t scaler_summary_flags = 0;

if (zoo->buy_signal.scaler.has_scaler)   scaler_summary_flags |= MASK_SCALER_PRESENT;
if (zoo->barrier.scaler.has_scaler)      scaler_summary_flags |= MASK_SCALER_PRESENT;
// ... etc ...

snap->per_core[i].ml_scaler_present = BITMAP_IS_SET(scaler_summary_flags, MASK_SCALER_PRESENT) ? 1 : 0;
if (BITMAP_IS_SET(scaler_summary_flags, MASK_SCALER_FAILED)) {
    FAILURE_SET(snap->per_core[i], ml_scaler_load_failed);
}
```

**Wins:**

1. 2 bits used; 6 bits headroom. Adding 3rd flag = 1 MASK constant + 1 OR line.
2. Multi-flag check via `BITMAP_ANY(flags, MASK_A | MASK_B)` (branchless mask AND).
3. Consistent with the bitmap pattern used elsewhere (BITMAP_IS_SET / BITMAP_SET / BITMAP_ANY).
4. Storage footprint: 1 uint8_t vs 2+ bools (memory marginal; pattern consistency matters more).

---

## Design space explored

### Option A: Multiple booleans (rejected)

Already described above. Drift class as flag count grows.

### Option B (chosen): Single bitmap with MASK constants + headroom

uint8_t for ≤8 flags; uint16_t for 9-16. Headroom future-proofs without breaking function signature.

### Option C: Promote to a struct field (overkill for transient state)

Transient summary doesn't need persistence across function calls. Adding a struct field implies "this state matters past this function" — wrong abstraction.

If aggregation matters across calls → use the actual struct field pattern. If aggregation is purely intra-function → transient bitmap.

---

## The pattern (concrete shape)

### Step 1: Declare MASK constants at the top of the function

```cpp
// In aggregation function body:
static constexpr uint8_t MASK_<FLAG_A> = (uint8_t)(1u << 0);
static constexpr uint8_t MASK_<FLAG_B> = (uint8_t)(1u << 1);
// ... up to 8 ...
```

`static constexpr` for compile-time + scoped to function. Use `BITMAP_BIT_U8/16/32/64` if available; raw `(1u << N)` for inline.

### Step 2: Declare the transient bitmap

```cpp
uint8_t <name>_flags = 0;
```

Zero-init. uint8_t for ≤8 flags; uint16_t for 9-16. Don't pre-allocate uint64_t "just in case" — pick width based on current count + 2-4 bits headroom.

### Step 3: OR in flags from source data

```cpp
if (cond_a) <name>_flags |= MASK_FLAG_A;
if (cond_b) <name>_flags |= MASK_FLAG_B;
```

The if-statements are predictable branches (cmov on modern compilers); compile to ~2 instructions each. Same instruction count as the old `bool any_X = true` pattern.

### Step 4: Read flags via BITMAP_IS_SET / BITMAP_ANY

```cpp
if (BITMAP_IS_SET(<name>_flags, MASK_FLAG_A)) { ... }
bool both = BITMAP_ALL(<name>_flags, MASK_FLAG_A | MASK_FLAG_B);
```

---

## Canonical example: scaler_summary_flags

```cpp
// In ShardedSnapshot.hpp snap-publish, per core:
static constexpr uint8_t MASK_SCALER_PRESENT = (uint8_t)(1u << 0);
static constexpr uint8_t MASK_SCALER_FAILED  = (uint8_t)(1u << 1);
uint8_t scaler_summary_flags = 0;

if (zoo) {
    if (zoo->buy_signal.scaler.has_scaler)   scaler_summary_flags |= MASK_SCALER_PRESENT;
    if (zoo->barrier.scaler.has_scaler)      scaler_summary_flags |= MASK_SCALER_PRESENT;
    if (zoo->regime.scaler.has_scaler)       scaler_summary_flags |= MASK_SCALER_PRESENT;
    if (zoo->exit.scaler.has_scaler)         scaler_summary_flags |= MASK_SCALER_PRESENT;
    if (zoo->buy_signal.scaler_load_failed)  scaler_summary_flags |= MASK_SCALER_FAILED;
    if (zoo->barrier.scaler_load_failed)     scaler_summary_flags |= MASK_SCALER_FAILED;
    if (zoo->regime.scaler_load_failed)      scaler_summary_flags |= MASK_SCALER_FAILED;
    if (zoo->exit.scaler_load_failed)        scaler_summary_flags |= MASK_SCALER_FAILED;
}
snap->per_core[i].ml_scaler_present = BITMAP_IS_SET(scaler_summary_flags, MASK_SCALER_PRESENT) ? 1 : 0;
if (BITMAP_IS_SET(scaler_summary_flags, MASK_SCALER_FAILED)) {
    FAILURE_SET(snap->per_core[i], ml_scaler_load_failed);
}
```

2 bits used; 6 bits headroom. Future additions ("scaler partial-load", "scaler version-mismatch", "scaler calibration-stale") fit in the existing uint8_t.

---

## Trade-offs + when to apply

### Apply when:
- A function aggregates 3+ boolean signals into a summary
- The summary is consumed within the same function (transient)
- Headroom for future additions matters
- Multi-flag checks ("any of A/B/C set?") are likely

### Skip when:
- 1-2 boolean signals (overhead of MASK constants > savings)
- Summary is persistent (use struct field; this pattern is for transient state)
- Aggregation logic is trivially inlineable (e.g., one if-else short-circuit; bitmap is overkill)

### Cost:
- 2-4 LOC for MASK constants
- ~Same instruction count as bool aggregation (branchless OR ≈ conditional bool-set)
- 1-2 bytes storage (uint8_t / uint16_t) vs 2+ bytes (multiple bools)

### Win:
- Headroom: 6+ bits free in uint8_t case
- Consistent with bitmap pattern (BITMAP_IS_SET / BITMAP_ANY)
- Multi-flag branchless check: `BITMAP_ANY(flags, MASK_A | MASK_B | MASK_C)` — 1 cycle vs N branches
- Adding a flag: 1 MASK + 1 OR line; no signature change, no caller update

---

## Reference implementations

### v5.14.9.H — first transient aggregation bitmap

`CoreFrameworks/ShardedSnapshot.hpp:615-645`. 2 bits used (SCALER_PRESENT + SCALER_FAILED); 6 bits headroom for future scaler observability flags.

Aggregates 8 source booleans (4 scaler-present checks × 4 model roles, plus 4 scaler-failed checks × 4 roles) into 1 transient uint8_t.

### Adjacent / future candidates

- Boot-time validation aggregation (cfg parser errors across N keys → summary)
- Per-snapshot health summary (multiple per-node health checks → engine-wide summary)
- Drift detection aggregation (multiple parity check results → ship-blocking summary)

Any function that needs to AGGREGATE multiple booleans before deciding what to do is a candidate.

---

## Lessons / gotchas

### Don't over-headroom

A uint64_t "just in case" wastes 7 bytes for current 2-bit use. Pick width based on current count + 2-4 bits headroom; expand later when needed. uint8_t covers up to 8 flags; that's typical for an aggregation function.

### Cast on `1u << N`

```cpp
static constexpr uint8_t MASK_X = (uint8_t)(1u << 0);
```

The cast prevents signed-int promotion warnings + makes the type explicit. For uint16_t, use `(uint16_t)(1u << N)`. For uint32_t, `(uint32_t)(1u << N)`. For uint64_t, `(1ULL << N)`.

### `static constexpr` inside function vs file-scope constants

Inside the function: scoped + only allocated once + invisible to outside callers. Preferred for transient pattern.

File-scope `static constexpr` at namespace level: visible to other functions; promotes to a persistent constant. Use only if other functions also need the MASK (which they shouldn't if it's truly transient).

### Don't transmute transient summary across threads

Transient summary lives in a single function call's stack frame. Don't `__atomic_load_n` it; don't share with other threads. If cross-thread sharing emerges, the pattern is wrong — promote to struct field with atomic accessors.

### Branchless aggregation if conditions are uniform

```cpp
// Instead of:
if (a) flags |= MASK_A;
if (b) flags |= MASK_B;

// Use:
flags |= (a ? MASK_A : 0u) | (b ? MASK_B : 0u);
```

Branchless via cmov. Compiler often does this automatically, but explicit OR-reduction reads cleanly + guarantees the branchless property regardless of compiler version.

### Headroom comment is mandatory

Document the headroom at the declaration:

```cpp
// 2 bits used; 6 bits headroom for future scaler observability
// (e.g., partial-load, version-mismatch, calibration-stale)
uint8_t scaler_summary_flags = 0;
```

Future maintainers see the available bits + a hint at what they're for. Prevents "do I have to add a uint16_t?" questions.

### Don't confuse with persistent struct field

The transient pattern is for FUNCTION-LOCAL summary. If the summary outlives the function (e.g., stored in a struct that other functions read), promote to a struct field — different pattern, different lifetime semantics. Mixing the two is a bug pattern.

---

## Audit detection

`/dod-audit` detects missed applications by:

- Symptom: 3+ `bool` local variables in same function used as aggregation flags (e.g., `bool any_X = false; if (...) any_X = true; ...; if (any_X) {...}`)
- Symptom: parallel any-of pattern across N source booleans without bitmap consolidation

When detected → flag as `MISSED — transient-aggregation-bitmap-pattern`. Recommended fix: collapse to uint8_t with MASK constants.

---

## Patterns NOT used here (and why)

### Reduce-via-fold (e.g., std::accumulate)

```cpp
bool any_present = std::any_of(handles, handles+4, [](auto& h){ return h.scaler.has_scaler; });
```

Functional style; C++-class-flavored. Heavier than the bit-OR pattern for transient state. Acceptable in non-hot/slow contexts but bitmap pattern is more aligned with project conventions.

### `std::bitset<N>`

Standard library bitset. Same objections as parent doc — STL dependency, not memcpy-friendly, operator-class semantics.

### Bit-packed via struct (with bit-field syntax)

```cpp
struct { unsigned scaler_present : 1; unsigned scaler_failed : 1; ...; } flags;
```

Compiler-dependent layout; harder to OR/AND multiple flags at once; less portable. Stick with uint8_t + MASK constants.

---

## Cross-references

- `bitmap-flag-api.md` — BITMAP_IS_SET / BITMAP_SET / BITMAP_ANY (the reader/writer API)
- `partner-core-bitmap-pattern.md` — sister pattern (per-node bitmap, different lifetime)
- FoxML_Trader_v2 `CLAUDE.md` item 20 — bit-packed flag storage (BITMAP_* API)
- FoxML_Trader_v2 `DOCS/TECH_DEBT.md` TECH_DEBT-013 — candidate inventory (this is candidate 7)
- FoxML_Trader_v2 `CoreFrameworks/ShardedSnapshot.hpp:615-645` — reference implementation
