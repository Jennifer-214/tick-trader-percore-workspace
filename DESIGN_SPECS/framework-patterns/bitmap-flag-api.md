---
type: framework-pattern
stage: 5-claude-md
version: 1.0
established: 2026-05-09
tags: [framework-discipline, data-oriented-design, branchless-discipline, structural-fix]
surface: [hot-path, bitmap-packed, registry]
sister_specs: [bitmap-overflow-protection-discipline.md, multi-bit-state-encoding-pattern.md, registry-bitmap-set-discipline.md, universal-registry-bitmap-dispatcher-pattern.md]
applies_at_skills: []
---

# Bitmap flag API (BITMAP_* macros) — reusable bit-packed flag accessors

**Established:** 2026-05-09 (v5.14.8.A.0.b.1)
**Status:** ACTIVE
**Cross-references:**
- First application: `MemHeaders/BitmapMacros.hpp`
- First consumer: `FOREACH_STAMP_BOUND_MODEL_CONST` has_flags (v5.14.8.A.merged)
- Second consumer: `FOREACH_FAILURE_MODE` failure_flags (v5.14.8.B)
- Pattern precedent: `Portfolio<uint16_t>` bitmap (CLAUDE.md item 1, FoxML_Trader_v2)
- Sister pattern: `partner-core-bitmap-pattern.md` (per-core 1-bit-per-core variant)
- Sister pattern: `transient-aggregation-bitmap-pattern.md` (function-local summary bitmap variant)
- Sister pattern: `per-bit-per-core-override-pattern.md` (per-bit per-core override on bitmap fields)
- Related: `bit-packed-storage-class-pattern.md` (TECH_DEBT-013 sweep candidates)

---

## Problem statement

Many code paths use `uint8_t flag1; uint8_t flag2; uint8_t flag3;` (one byte per boolean). Wins:
- Memory waste (1 byte per flag where 1 bit suffices; 7 bits wasted)
- Per-flag atomic stores instead of single multi-flag atomic op
- Multi-flag check via N field reads + N branches (predictor unfriendly)
- "Any flag set?" check requires N comparisons

These are recurring inefficiencies in:
- Per-stamp `has_*` flags (24+ in some stamp body schemas)
- PerCoreSnap state flags (failure modes, mode indicators)
- FOREACH_FEATURE enabled flags
- Engine-wide cfg flags (partial_exit_enabled, lat_enabled, etc.)
- Snapshot summary flags

The fundamental shift: `uint8_t flag_<X>` patterns should be replaced with `BITMAP_BIT_U64(N)` masks in a uint16_t / uint32_t / uint64_t bitmap field, accessed via a uniform API.

This pattern provides that API.

---

## Design space explored

### Option A: Hand-rolled bit operations per call site

```cpp
if (s.flags & (1 << 3)) { ... }  // bit 3 set?
s.flags |= (1 << 3);  // set bit 3
s.flags &= ~(1 << 3); // clear bit 3
```

Works but has well-known footguns:
- `1 << N` is signed int promotion — bit 31 in uint32_t triggers UB; bit 63 in uint64_t silently wraps
- `s.flags & MASK` returns the masked VALUE not bool — int truncation in caller bool contexts
- No standard atomic variants — every call site reinvents

Rejected: too much per-site discipline.

### Option B (chosen): Reusable macro API in shared header

Single header defines:
- Predicate macros (returns bool always; safe across all integer widths)
- Mutation macros (set / clear / toggle)
- Atomic variants (cross-thread visibility)
- Helper macros (bit position to mask, popcount, first-set)

All macros are 1-cycle ops at runtime. Compile-time elided where possible.

### Option C: C++ bitmap wrapper class

```cpp
template <typename T> class Bitmap { ... };
Bitmap<uint64_t> flags;
flags.set(MASK_X);
```

Rejected: adds C++ object semantics (constructors, operators) to a primitive that should be pure data. The struct field becomes a Bitmap<uint64_t> object, not a uint64_t — hostile to memcpy snapshot serialization, hostile to hardware atomic ops, hostile to alignas() expectations. The macro approach keeps the field as a primitive integer.

---

## The pattern (concrete shape)

### The 14-macro API

```cpp
// File: MemHeaders/BitmapMacros.hpp

#ifndef BITMAP_MACROS_HPP
#define BITMAP_MACROS_HPP

// =====================================================================
// Single-thread accessors (use within one thread; no cross-thread sync)
// =====================================================================

// Predicate: any of mask's bits set in field? Returns bool.
#define BITMAP_IS_SET(field, mask)  (((field) & (mask)) != 0)

// Mutation: set bits. Statement.
#define BITMAP_SET(field, mask)     ((field) |= (mask))

// Mutation: clear bits. Statement.
#define BITMAP_CLR(field, mask)     ((field) &= ~(mask))

// Mutation: toggle bits. Statement.
#define BITMAP_TOGGLE(field, mask)  ((field) ^= (mask))

// Predicate: any bit in mask_set set? Branchless multi-flag check.
#define BITMAP_ANY(field, mask_set) (((field) & (mask_set)) != 0)

// Predicate: ALL bits in mask_set currently set?
#define BITMAP_ALL(field, mask_set) (((field) & (mask_set)) == (mask_set))

// Predicate: NO bits in mask_set set?
#define BITMAP_NONE(field, mask_set) (((field) & (mask_set)) == 0)

// =====================================================================
// Atomic accessors (cross-thread visibility)
// =====================================================================

// Atomic load with relaxed ordering (default).
#define BITMAP_ATOMIC_LOAD(field) \
    __atomic_load_n(&(field), __ATOMIC_RELAXED)

// Atomic load with explicit memory order.
#define BITMAP_ATOMIC_LOAD_ORDER(field, order) \
    __atomic_load_n(&(field), (order))

// Atomic OR — set bits; returns prior value.
#define BITMAP_ATOMIC_SET(field, mask) \
    __atomic_fetch_or(&(field), (mask), __ATOMIC_RELAXED)

#define BITMAP_ATOMIC_SET_ORDER(field, mask, order) \
    __atomic_fetch_or(&(field), (mask), (order))

// Atomic AND-NOT — clear bits; returns prior value.
#define BITMAP_ATOMIC_CLR(field, mask) \
    __atomic_fetch_and(&(field), ~(mask), __ATOMIC_RELAXED)

#define BITMAP_ATOMIC_CLR_ORDER(field, mask, order) \
    __atomic_fetch_and(&(field), ~(mask), (order))

// Atomic XOR — toggle bits.
#define BITMAP_ATOMIC_TOGGLE(field, mask) \
    __atomic_fetch_xor(&(field), (mask), __ATOMIC_RELAXED)

// Atomic predicate: bit set? Returns bool. Snapshot-based.
#define BITMAP_ATOMIC_IS_SET(field, mask) \
    ((__atomic_load_n(&(field), __ATOMIC_RELAXED) & (mask)) != 0)

// Atomic predicate: any bit in mask_set set?
#define BITMAP_ATOMIC_ANY(field, mask_set) \
    ((__atomic_load_n(&(field), __ATOMIC_RELAXED) & (mask_set)) != 0)

// =====================================================================
// Helpers (bit position → mask, popcount, first-set)
// =====================================================================

// Width-typed bit-mask builders. AVOIDS signed-int promotion bugs.
#define BITMAP_BIT_U16(n) ((uint16_t)((uint16_t)1u << (n)))
#define BITMAP_BIT_U32(n) ((uint32_t)(1u << (n)))
#define BITMAP_BIT_U64(n) (1ULL << (n))

// Population count (number of bits set).
#define BITMAP_POPCOUNT_U16(field) (__builtin_popcount((unsigned)(field) & 0xFFFFu))
#define BITMAP_POPCOUNT_U32(field) (__builtin_popcount((unsigned)(field)))
#define BITMAP_POPCOUNT_U64(field) (__builtin_popcountll((unsigned long long)(field)))

// First-set-bit index (0-based). Returns 0 if no bits set —
// disambiguate via BITMAP_ANY.
#define BITMAP_FIRST_U16(field) ((unsigned)__builtin_ctz((unsigned)(field) & 0xFFFFu))
#define BITMAP_FIRST_U32(field) ((unsigned)__builtin_ctz((unsigned)(field)))
#define BITMAP_FIRST_U64(field) ((unsigned)__builtin_ctzll((unsigned long long)(field)))

#endif // BITMAP_MACROS_HPP
```

### Critical design decision: predicate macros return bool explicitly

The single most important footgun-prevention decision:

```cpp
// WRONG: returns the masked value (uint64_t)
#define BITMAP_IS_SET(field, mask)  ((field) & (mask))

// RIGHT: returns bool always
#define BITMAP_IS_SET(field, mask)  (((field) & (mask)) != 0)
```

**Why:** in caller contexts where the result is converted to `int` (e.g., `void check(const char* name, int condition)` test harness; `bool` parameter; `assert(...)`) — uint64_t → int can truncate the lower 32 bits. If only the top bit is set (`0x8000_0000_0000_0000`), the lower 32 bits are zero → truncates to 0 → predicate evaluates false.

This was caught by a top-bit safety regression test: `BITMAP_BIT_U64(63)` set on a uint64_t flags variable; predicate test returned false despite the bit being set. Fix: `!= 0` everywhere predicate semantics are intended.

### Critical design decision: width-typed bit builders

```cpp
// WRONG: int promotion, signed, possibly UB at high bits
#define BIT(n) (1 << (n))

// RIGHT: explicit width per usage
#define BITMAP_BIT_U16(n) ((uint16_t)((uint16_t)1u << (n)))
#define BITMAP_BIT_U32(n) ((uint32_t)(1u << (n)))
#define BITMAP_BIT_U64(n) (1ULL << (n))
```

**Why:** the C/C++ language spec promotes integer literals to `int` during shift. `1 << 63` is undefined behavior for 32-bit `int`. The width-typed builders force the right type at the source.

### Critical design decision: atomic variants use __ATOMIC_RELAXED by default

For observability flags (which is the typical use case), there's no happens-before constraint with other data. Relaxed ordering is sufficient AND lowest cost. Explicit-order variants (`*_ORDER(...)`) let callers upgrade when needed.

---

## Trade-offs + when to apply

### Apply when:
- 3+ boolean flags coexist in a struct (memory savings start here)
- Multi-flag checks are common ("any failure mode set?", "any drift detected?")
- Flags are observed cross-thread (atomic variants are easy to add)
- The struct is performance-sensitive (cache-line tight, snapshot serialized)

### Skip when:
- 1-2 isolated flags (overhead of MASK_<X> constants exceeds savings)
- Per-record flags (e.g., `Order.is_buyer_maker` per order — bit-packing across records adds indirection cost > savings)
- The struct's field count fits one cache line already (no marginal savings)

### Cost:
- ~180 LOC of header + tests
- Per-bitmap site: define a few `MASK_<X> = BITMAP_BIT_UN(...)` constants
- Caller migration from `s.flag_<X>` to `BITMAP_IS_SET(s.flags, MASK_<X>)` is mechanical find/replace

### Win:
- Memory: 16/32/64 binary states in 2/4/8 bytes (vs N bytes byte-per-flag)
- Atomic multi-flag updates: 1 instruction (`__atomic_fetch_or`) vs N stores
- Branchless multi-flag check: 1 cycle (mask AND) vs N branches
- Cache: flag-state for an entire core fits one cache line
- Branch prediction: boolean test on bitmask result is highly predictable

---

## Reference implementations

### First applied: FoxML_Trader_v2 v5.14.8.A.0.b.1

- Header: `MemHeaders/BitmapMacros.hpp`
- 21 tests added in `tests/controller_test.cpp`
- Tests cover: single-thread + uint16_t/uint64_t variants + atomic variants + top-bit safety

### Pattern precedents (pre-existing in codebase)

- `Portfolio<uint16_t>` bitmap — CLAUDE.md item 1
- `OrderManagerState.order_bitmap` — same pattern
- `FeatureMask<uint64_t>` — feature-mask-train (v5.11.18a)

These predate BitmapMacros.hpp; future maintenance can migrate to use the API.

### Second-tier application — hybrid storage classes (v5.15.5.C.3 Phase 3b)

- Registry: `MemHeaders/OmsStateFlagRegistry.hpp` — `oms_state_flags` bitmap field on `OrderManagerState`
- First application of HYBRID storage in the same word:
  - `BIT` kind (1 bit): `LIVE_TRADING`, `PARTIAL_EXIT_ENABLED`, `KILL_SWITCH_TRIPPED`
  - `MULTI_BIT` kind (N bits): `EVENT_LOG_MODE` (2-bit slot) — first canonical
    multi-bit-state-encoding-pattern application (see sister doc)
- Companion macros: `OMS_INIT_AUTOPOPULATE` + `OMS_RESET_AUTOPOPULATE` walk the
  registry and emit per-flag init/reset via `BITMAP_SET` (BIT) or `MBS_SET_*`
  (MULTI_BIT) dispatching on the per-entry KIND column
- Lesson: a single bitmap word can hold MIXED storage classes (1-bit flags
  alongside N-bit slots) when the registry tuple includes a per-entry KIND
  marker — closes the "different storage kinds need different containers"
  anti-pattern

### TECH_DEBT-013 sweep candidates (explicit triggers)

| Site | Flag count today | Bit-pack target | Trigger |
|---|---|---|---|
| `ModelStampResult` / `StampInferenceCfgInputs` / `ModelHandle` `has_*` | 24+ | uint64_t `has_flags` | DONE in v5.14.8.A.merged |
| `PerCoreSnap` failure-mode flags | 2 binary + 4 counters | uint16_t `failure_flags` + counters | DONE in v5.14.8.B/C |
| `PerCoreSnap` non-failure state flags | 3-5 | merge into existing or new state_flags | Next ship touching PerCoreSnap |
| `FOREACH_FEATURE.enabled` (40 features) | 40 byte-per-flag | uint64_t enabled_bitmap | Next FeatureRegistry storage refactor |
| `OrderManager.partial_exit_enabled` + `ExecutionCore.lat_enabled` | 2 | engine-wide uint16_t cfg_flags | Next ship adding 3+ engine-wide flags |
| `ControllerEventLoop.partner_pending_active` | 1 per-core | merge into per-core flags | Next ship adding 2+ per-core flags |
| `ShardedSnapshot.any_scaler_present/_failed` | 2 | snapshot summary bitmap | Next ship touching snapshot serialization |

---

## Lessons / gotchas

### `BITMAP_FIRST_*` with input 0 is undefined behavior

`__builtin_ctz` (count trailing zeros) is undefined for input 0. The macros pass through to the builtin. Document at usage:
> "Returns 0 if no bits set — disambiguate via BITMAP_ANY before calling FIRST_*."

### `BITMAP_ATOMIC_*` macros take field BY ADDRESS

`__atomic_*` builtins need an lvalue. The macros do `&(field)` internally; if the caller passes a non-lvalue (rvalue, function-call return), compile fails. Acceptable; document the constraint.

### Macro double-evaluation risk

`BITMAP_TOGGLE(s.flags, get_mask())` — if `get_mask()` has side effects, it's evaluated once (XOR is one operation). But if a future macro wraps this in a do-while loop with multiple evaluations, side-effect risk emerges. Keep macros simple (single evaluation per arg).

### Memory ordering

Default `__ATOMIC_RELAXED` is correct for observability flags (no happens-before constraint with other data). For flags that synchronize OTHER data (e.g., a "result_ready" flag that releases a result struct), use the `*_ORDER(...)` variants with `__ATOMIC_RELEASE` / `__ATOMIC_ACQUIRE`:

```cpp
// Worker thread:
write_result_struct(...);
BITMAP_ATOMIC_SET_ORDER(flags, MASK_RESULT_READY, __ATOMIC_RELEASE);

// Reader thread:
if (BITMAP_ATOMIC_LOAD_ORDER(flags, __ATOMIC_ACQUIRE) & MASK_RESULT_READY) {
    read_result_struct(...);  // safe; release-acquire established happens-before
}
```

### Compatibility with seqlock

For data published via seqlock (FoxML_Trader_v2 patterns), the bitmap field can live INSIDE the seqlock-published struct. Reader copies the whole struct under the seqlock; bitmap reads after copy are non-atomic on the local copy. Single-thread accessors apply.

If the bitmap is accessed CONCURRENTLY by multiple writers OR readers (without seqlock), use atomic variants.

---

## Patterns NOT used here (and why)

### `std::bitset<N>`

Standard library bitset. Rejected because:
- Adds standard-library dependency to lock-free hot-path code
- Not memcpy-friendly (storage layout not guaranteed for snapshots)
- API is C++-class-flavored (.set(), .test()) vs primitive integer ops
- No atomic variants
- More cognitive load (constructor/operator semantics)

### `std::atomic<uint64_t>`

Standard library atomic wrapper. Rejected because:
- Wraps primitive in C++ object semantics (operator overloads, constructor)
- Snapshots / memcpy / FFI lose atomicity contract
- The macro approach treats the field as a plain uint64_t with explicit atomic ops where needed — more transparent

### Boost.Atomic

External dependency. FoxLIB has zero core dependencies; macros stay in-tree.

---

## Variants — applied shapes from v5.14.9 sprint

The BITMAP_* API is the base layer. v5.14.9 surfaced 4 distinct USE-SHAPES with different scopes + lifetimes. Each has its own sister DESIGN_SPEC; they share BITMAP_* primitives but apply at different surfaces:

### Variant 1: domain bitmap on engine cfg (Form 2 — DOMAIN SPLIT)

**Shape:** uint8/16 per cfg domain on ControllerConfig. Bits = cfg-flag toggles for that domain. Lifetime: engine-wide; boot-loaded; persistent until cfg-reload.

**See:** `heterogeneous-registry-pattern.md` (DOMAIN SPLIT decision framework), `registry-tuple-as-single-source-of-truth.md` (5-col tuple per registry).

**Example:** `cfg.lifecycle_cfg_flags` (3 bits: partial_exit + 2 breakeven). Read via `BITMAP_IS_SET(cfg.lifecycle_cfg_flags, MASK_LIFECYCLE_CFG_PARTIAL_EXIT_ENABLED)`.

### Variant 2: per-core bitmap (1 bit per core on a parent struct)

**Shape:** uint16/32/64 on EventLoopState (or similar). Bit N = core N's boolean state. Lifetime: persistent across slow-path cycles; single-thread coordinated.

**See:** `partner-core-bitmap-pattern.md` (full doc on this variant).

**Example:** `state->partner_pending_bitmap` (16 bits; one per core). Set via `BITMAP_SET(state->partner_pending_bitmap, BITMAP_BIT_U16(core_id))`.

**Memory win:** 64× reduction vs per-core byte+padding storage.

### Variant 3: transient aggregation bitmap (function-local summary)

**Shape:** uint8 local var in a function body. Bits = source booleans aggregated into a summary. Lifetime: single function call.

**See:** `transient-aggregation-bitmap-pattern.md` (full doc on this variant).

**Example:** `scaler_summary_flags` in ShardedSnapshot snap-publish loop. Aggregates 8 source booleans into 2-bit summary; 6 bits headroom for future flags.

### Variant 4: per-bit per-core override on bitmap fields

**Shape:** TWO uint8/16 per cfg domain on PerCoreOverrides: `<domain>_cfg_flags_override` (values) + `<domain>_cfg_flags_override_set` (mask of which bits are overridden). Branchless bit-select at resolution: `(set & values) | (~set & global)`.

**See:** `per-bit-per-core-override-pattern.md` (full doc on this variant).

**Example:** `PER_CORE_OVERRIDE_BITMAP_DOMAINS` registry walks 5 domains; resolution at boot is ~30 instructions total across all domains and bits.

### Variant 5: registry has_flags (parent doc's original use case)

**Shape:** uint64 has_flags on a registry-derived struct (ParserResult, EmitterInputs, RuntimeHandle). Bit per registry entry. Lifetime: persistent on the struct.

**See:** `x-macro-registry-with-presence-dispatch.md`, `autopopulate-pattern-for-production-caller-class.md`.

**Example:** ModelHandle.has_flags (24+ bits for stamp-bound model fields).

### Variant 6: per-struct decision-state bitmap (per-instance boolean cohort)

**Shape:** uint8 (or wider) on a per-instance struct that holds a cohort of pure-boolean DECISION flags. Lifetime: per-struct-instance; single-writer per instance (per-core slow-path thread); no atomics within the per-instance write window. Registry-driven (`FOREACH_<CTX>_STATE_FLAG`); accessor macros `<CTX>_STATE_FLAG_{IS_SET,SET,CLR,TOGGLE}` mirror the snapshot-side `STATE_FLAG_*` ergonomics.

**See:** `MemHeaders/CoreStateFlagRegistry.hpp` (canonical first reference).

**Example:** `CoreContext.core_state_flags` (uint8_t; 5 bits used: DIRTY, KILL_TRIPPED, MODEL_LOAD_FAILED, CFG_DRIFT_STRICT_REFUSED, WARMUP_LOG_EMITTED; 3 bits headroom). Registry: `FOREACH_CORE_STATE_FLAG(X)` in `MemHeaders/CoreStateFlagRegistry.hpp`. Shipped v5.15.5.B.3. Memory win: 5 byte-per-flag fields + `_pad_kill[3]` alignment padding = 8 B/CoreContext × 16 cores = 128 B/EventLoopState → 1 byte × 16 cores = 16 B (saved ~112 B/EventLoopState).

**Distinct from Variant 2 (per-core bitmap on parent struct):** Variant 2 stores ONE bit per core on the PARENT (e.g., `EventLoopState.partner_pending_bitmap` packs 16 cores into one uint16_t). Variant 6 stores MULTIPLE bits per instance on EACH instance (e.g., each `CoreContext` has its own `core_state_flags` uint8_t with 5+ bits used). Variant 2 packs cores; Variant 6 packs flags within a struct.

**Distinct from Variant 1 (engine-wide cfg-flag bitmap):** Variant 1 is engine-wide cfg (cfg-flag toggles persistent until reload). Variant 6 is per-instance runtime state (decision flags flipped during execution; e.g., DIRTY flipped per cycle).

### Which variant fits?

| Need | Variant | Doc |
|---|---|---|
| Engine-wide cfg-flag toggles | 1 | `heterogeneous-registry-pattern.md` |
| Per-core boolean state | 2 | `partner-core-bitmap-pattern.md` |
| Function-local boolean aggregation | 3 | `transient-aggregation-bitmap-pattern.md` |
| Per-core override on bitmap field | 4 | `per-bit-per-core-override-pattern.md` |
| Registry parsed/emitted field presence | 5 | `x-macro-registry-with-presence-dispatch.md` |
| Per-struct decision-state cohort (multi-bit per instance) | 6 | `MemHeaders/CoreStateFlagRegistry.hpp` (canonical first reference) |

All variants use BITMAP_* primitives at the read/write sites. The differences are in SHAPE (one bitmap field on what struct? function-local? per-domain?) and LIFETIME (transient / persistent / per-core / engine-wide).

---

## Cross-references

- `x-macro-registry-with-presence-dispatch.md` — uses BITMAP_* for has_flags storage in registries
- `partner-core-bitmap-pattern.md` — per-core 1-bit-per-core variant (v5.14.9.G)
- `transient-aggregation-bitmap-pattern.md` — function-local summary variant (v5.14.9.H)
- `per-bit-per-core-override-pattern.md` — per-bit per-core override variant (v5.14.9.F.6)
- `heterogeneous-registry-pattern.md` — DOMAIN SPLIT for cfg-flag domain bitmaps
- `registry-tuple-as-single-source-of-truth.md` — 5-col tuple per domain registry
- `bit-packed-storage-class-pattern.md` (future doc) — TECH_DEBT-013 systematic application
- FoxML_Trader_v2 `CLAUDE.md` item 1 — Portfolio bitmap precedent
- FoxML_Trader_v2 `CLAUDE.md` item 18 — data-oriented design + branchless mask compute philosophy
- FoxML_Trader_v2 `DOCS/EASY_ADDITIONS_INVARIANTS.md` — "Storage classes within X-macro registries" section
- FoxML_Trader_v2 `DOCS/TECH_DEBT.md` TECH_DEBT-013 — sweep candidates inventory
