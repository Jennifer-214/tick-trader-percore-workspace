---
type: data-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-05-10
tags: [data-oriented-design, branchless-discipline]
surface: [hot-path, bitmap-packed]
sister_specs: [bitmap-flag-api.md, per-bit-per-core-override-pattern.md, transient-aggregation-bitmap-pattern.md]
applies_at_skills: []
---

# Partner-core bitmap pattern (per-node boolean → 1-bit-per-node bitmap)

**Established:** 2026-05-10 (v5.14.9.G — `partner_pending_bitmap`)
**Status:** ACTIVE
**Cross-references:**
- Parent: `bitmap-flag-api.md` (BITMAP_IS_SET / BITMAP_SET / BITMAP_CLR + BITMAP_BIT_U16)
- Sister: `transient-aggregation-bitmap-pattern.md` (different scope: transient summary vs persistent per-node state)
- First application: `CoreFrameworks/ControllerEventLoop.hpp:533` (`partner_pending_bitmap` on EventLoopState)
- CLAUDE.md item 20 (bit-packed flag storage)
- CLAUDE.md item 4 (per-node data plane)
- TECH_DEBT-013 (candidate 6)

---

## Problem statement

A struct holds an ARRAY of per-node state — one entry per core, up to MAX_EXECUTION_CORES (typically 16). One of the per-node fields is a boolean:

```cpp
struct CoreContext { 
    // ... per-core state ...
    uint8_t partner_pending_active;  // 1 byte
    uint8_t _pad_partner[7];          // alignment padding to next field
};

struct EventLoopState { 
    CoreContext cores[MAX_EXECUTION_CORES];  // 16 entries
    // ...
};
```

**Storage cost:** 1 byte per core + 7 bytes alignment padding = 8 bytes per core × 16 cores = **128 bytes** of EventLoopState dedicated to this boolean.

**Read pattern:**

```cpp
// Per-core check:
if (state->cores[core_id].partner_pending_active) { ... }

// Engine-wide "any core?" check (rare but useful for ops/UI):
bool any = false;
for (int c = 0; c < state->registered_count; c++) {
    if (state->cores[c].partner_pending_active) { any = true; break; }
}
```

**Pain points:**

1. 128 bytes for 1 logical bit per core — 1024× memory inefficiency.
2. Engine-wide "any?" check is O(N) with N memory loads (cache-line ping-pong across cores).
3. Per-node check accesses CoreContext (likely cached for that core's owning thread but not for cross-core read paths).
4. Alignment padding is wasted forever.

---

## Design space explored

### Option A: Keep per-CoreContext uint8_t (current state — pre-.G)

Already described above. Drift: each new per-node boolean adds another 8 bytes (or wedges into existing padding non-uniformly).

### Option B (chosen): Single uint16_t with 1 bit per core, on EventLoopState

```cpp
struct EventLoopState {
    uint16_t partner_pending_bitmap;  // bit N = core N's pending state
    // ...
};

// Set:
BITMAP_SET(state->partner_pending_bitmap, BITMAP_BIT_U16(core_id));

// Clear:
BITMAP_CLR(state->partner_pending_bitmap, BITMAP_BIT_U16(core_id));

// Test (per-core):
if (BITMAP_IS_SET(state->partner_pending_bitmap, BITMAP_BIT_U16(core_id))) { ... }

// Test (engine-wide "any?"):
if (state->partner_pending_bitmap != 0) { ... }
```

**Wins:**

- Storage: 2 bytes total (vs 128 bytes). **64× memory reduction.**
- Engine-wide "any?": single 16-bit load + compare to 0 → branchless boolean. No iteration.
- Cache locality: one cache line holds all 16 cores' state. Any thread reading any core's state pays only 1 cache miss (instead of N).
- Set/Clear/Test: all branchless (1-2 instructions each).

### Option C: Per-node atomic flag bitmap (rejected for this use case)

If multiple threads could MUTATE different bits concurrently, atomic ops would be needed. For partner_pending, single-writer (slow-path thread per core; cross-core writes use OMS dispatch → also slow-path serialized). Atomic overhead unjustified.

---

## The pattern (concrete shape)

### Step 1: Declare bitmap on the owning struct

```cpp
struct EventLoopState {
    uint16_t partner_pending_bitmap;  // bit N = core N's <state>
    // ...
};
```

For MAX_EXECUTION_CORES ≤ 16: uint16_t. For ≤32: uint32_t. For ≤64: uint64_t. Don't pre-allocate uint64_t if MAX_CORES is 16.

### Step 2: Document the bit-to-core mapping

```cpp
// bit N corresponds to core N's <state>
// 0 = inactive; 1 = active
```

Explicit documentation prevents ambiguity. Some codebases use bit N for core MAX-N-1; others for core N. Pick one and document.

### Step 3: Zero-init at struct init

```cpp
state->partner_pending_bitmap = 0;
```

All cores start in the default state (typically "inactive").

### Step 4: Use BITMAP_BIT_U16(core_id) for mask construction

```cpp
BITMAP_SET(state->partner_pending_bitmap, BITMAP_BIT_U16(core_id));
BITMAP_CLR(state->partner_pending_bitmap, BITMAP_BIT_U16(core_id));
if (BITMAP_IS_SET(state->partner_pending_bitmap, BITMAP_BIT_U16(core_id))) ...
```

`BITMAP_BIT_U16(core_id)` is `(uint16_t)((uint16_t)1u << (core_id))` — width-typed mask. Don't use raw `(1 << core_id)` (signed-int promotion bug at high bits).

### Step 5: Engine-wide "any active?" via direct comparison

```cpp
// Branchless any-core-active check:
if (state->partner_pending_bitmap != 0) { ... }

// Branchless count-active-cores:
unsigned count = BITMAP_POPCOUNT_U16(state->partner_pending_bitmap);
```

---

## Canonical example: partner_pending_bitmap

```cpp
// In EventLoopState:
uint16_t partner_pending_bitmap;

// Init:
state->partner_pending_bitmap = 0;

// When core N starts partner-pending:
BITMAP_SET(state->partner_pending_bitmap, BITMAP_BIT_U16(core_id));

// When core N's partner resolves:
BITMAP_CLR(state->partner_pending_bitmap, BITMAP_BIT_U16(core_id));

// Per-core check in the per-core slow-path:
if (BITMAP_IS_SET(state->partner_pending_bitmap, BITMAP_BIT_U16(core_id))) {
    // core has partner pending; defer entry/exit
}

// Engine-wide "any core has partner pending?" (for ops/UI):
bool any_pending = (state->partner_pending_bitmap != 0);
```

**Pre-migration footprint:** 128 bytes.
**Post-migration footprint:** 2 bytes.
**Saved:** 126 bytes per EventLoopState. (Engine has 1 EventLoopState, so 126 bytes saved net.)

The memory win is modest — but the cache-locality + branchless engine-wide query win matters when cross-core code paths sample state often.

---

## Trade-offs + when to apply

### Apply when:
- A per-node struct holds a BOOLEAN field (1 byte + alignment padding)
- Total cores ≤ 64 (fits a single uint64_t)
- Engine-wide "any core?" / "count cores?" queries are useful
- Single-writer-per-bit OR single-thread-coordinated writes (no concurrent multi-thread bit mutation)

### Skip when:
- Per-node field is multi-byte (e.g., uint32_t / FPN — bitmap doesn't fit)
- Concurrent multi-thread per-bit mutation (would need atomic; consider whether the design needs this complexity)
- The per-node field is read EVERY hot-path tick (1-cycle access from owning core's cache is already optimal; bitmap doesn't speed up)

### Cost:
- 2 bytes per bitmap (vs N bytes per per-node field × N cores)
- ~Same instructions per per-node check (BITMAP_IS_SET ≈ direct uint8_t load + compare)
- 1 migration effort: ~30 min (move field; update all read/write sites)

### Win:
- 64× memory reduction for the per-node boolean (16 × 8 bytes → 2 bytes)
- Branchless engine-wide "any?" check (1 compare to 0 vs N-iteration loop)
- Cache locality (16 cores in 1 cache line)
- Set/Clear/Test all branchless

---

## Reference implementations

### v5.14.9.G — first per-core bitmap migration

`CoreFrameworks/ControllerEventLoop.hpp:533` (`partner_pending_bitmap`) — replaced 16 × `partner_pending_active` byte fields.

Read sites: ~5 across `ControllerEventLoop.hpp` (partner pending check, ops/UI), all mechanically converted to `BITMAP_IS_SET(state->partner_pending_bitmap, BITMAP_BIT_U16(core_id))`.

Set/Clear sites: ~3 across `ControllerEventLoop.hpp` (when partner starts pending, when it resolves).

Memory: -126 bytes per EventLoopState.

### Future candidates

Any per-CoreContext boolean that's truly 1-bit:

- `dirty` flag (per-node "rebuild needed")
- `partner_resolved_ack` (per-node "ack pending")
- Engine-wide gate-active flags per core (if a slow-path-gate cache wants per-node variants)

These haven't been migrated yet; they're individual decisions per-field (some may benefit from per-CoreContext locality for the OWNING core's reads).

---

## Lessons / gotchas

### Cache-line implications: 1 line, all cores

The bitmap is 2 bytes — fits in one cache line + ~62 bytes of other state. Cross-thread reads (e.g., GUI thread reading per-node state) hit one cache line; pre-migration would have hit N cache lines (one per core's CoreContext).

**Trade-off:** the OWNING core's reads might have been faster pre-migration (own core's CoreContext in L1). Post-migration, all cores' state lives in one cache line on EventLoopState — accessed via shared L2/L3. For boolean access at slow-path cadence (~100µs), this is negligible.

**Don't migrate if** the per-node field is read EVERY HOT-PATH TICK by the owning core — then per-node local storage stays faster.

### Width selection: MAX_EXECUTION_CORES informs the type

```cpp
#if MAX_EXECUTION_CORES <= 16
typedef uint16_t partner_bitmap_t;
#elif MAX_EXECUTION_CORES <= 32
typedef uint32_t partner_bitmap_t;
#else
typedef uint64_t partner_bitmap_t;
#endif
```

Today FoxML_Trader_v2 caps at 16 cores → uint16_t fits. If MAX_EXECUTION_CORES ever expands, this pattern grows the bitmap width.

Static_assert at compile time:

```cpp
static_assert(MAX_EXECUTION_CORES <= 16, "partner_pending_bitmap is uint16_t");
```

### BITMAP_BIT_U16(core_id) — not raw (1 << core_id)

`BITMAP_BIT_U16(N)` is the width-typed builder:

```cpp
#define BITMAP_BIT_U16(n) ((uint16_t)((uint16_t)1u << (n)))
```

Raw `(1 << core_id)` is `int` (signed); for core_id 15, that's `0x8000` which is the SIGN bit of `int16_t` → bug. Width-typed builder avoids.

### Engine-wide "any?" branchless via `!= 0`

```cpp
bool any_pending = (state->partner_pending_bitmap != 0);
```

This is branchless on modern compilers (compiles to `cmp + setne` or `test + setne`). Pre-migration's loop-with-break was branchy + iterative. Migration gives a strict speedup for engine-wide queries.

### Per-bit atomic if concurrent multi-thread mutation needed

Today `partner_pending_bitmap` is single-thread-coordinated (slow-path thread). If a future design needs concurrent multi-thread bit mutation:

```cpp
BITMAP_ATOMIC_SET(state->partner_pending_bitmap, BITMAP_BIT_U16(core_id));
```

Uses `__atomic_fetch_or` — atomic per-bit set without locking. Same width-typed mask; same code shape.

### Comment migration sites with bit semantics

Pre-migration comment style: `// 1 = active`.
Post-migration comment style: `// bit N = core N's active state`.

The "bit N = core N" mapping convention is important — without it, future maintainers might assume bit 0 means something other than core 0.

### Tests: bitmap-aware assertions

Pre-migration test: `EXPECT_EQ(state->cores[3].partner_pending_active, 1)`.

Post-migration test: `EXPECT_TRUE(BITMAP_IS_SET(state->partner_pending_bitmap, BITMAP_BIT_U16(3)))`.

Update test assertions during migration; don't leave them reading the old field name.

### Don't migrate per-node fields that are SHARED between owning core + GUI

Per-node fields read by both the owning slow-path thread AND a GUI thread should stay per-CoreContext (owning core's L1 hit is preserved). Bitmap migration moves the field to EventLoopState — both threads now race for the shared cache line.

`partner_pending_bitmap` happens to be safe: it's set/cleared by slow-path thread; GUI reads via snapshot publish (not direct), so the bitmap-on-EventLoopState placement is fine.

For other candidates, verify the cross-thread read pattern before migrating.

---

## Audit detection

`/dod-audit` detects missed applications by:

- Symptom: `uint8_t` field on per-node struct + alignment padding (`uint8_t _pad_X[7]`) that's just storing a boolean
- Symptom: engine-wide "any core has X active?" loops iterating over per-node array

When detected → flag as `MISSED — partner-core-bitmap-pattern`. Recommended fix: migrate to single bitmap on the parent struct.

---

## Patterns NOT used here (and why)

### Per-node local uint8_t with explicit padding

Original pattern. Wasteful (described above).

### `std::bitset<MAX_CORES>`

Standard library bitset. Same objections as parent doc — STL dependency, not memcpy-friendly, operator semantics.

### Hierarchical bitmap (e.g., 64-bit summary + per-group detail)

Overkill for MAX_EXECUTION_CORES ≤ 16. Pattern fits well within a single uint16_t.

### Per-bit C++ bit-field syntax

```cpp
struct { unsigned core0_partner : 1; unsigned core1_partner : 1; ...; } flags;
```

Verbose; compiler-dependent layout; doesn't generalize to dynamic core counts. uint16_t + BITMAP_BIT_U16 is cleaner.

---

## Cross-references

- `bitmap-flag-api.md` — BITMAP_IS_SET / BITMAP_SET / BITMAP_CLR / BITMAP_BIT_U16 / BITMAP_POPCOUNT_U16
- `transient-aggregation-bitmap-pattern.md` — sister pattern (transient summary; different lifetime)
- FoxML_Trader_v2 `CLAUDE.md` item 4 — per-node data plane
- FoxML_Trader_v2 `CLAUDE.md` item 20 — bit-packed flag storage
- FoxML_Trader_v2 `DOCS/TECH_DEBT.md` TECH_DEBT-013 — candidate inventory (this is candidate 6)
- FoxML_Trader_v2 `CoreFrameworks/ControllerEventLoop.hpp:533` — reference implementation
