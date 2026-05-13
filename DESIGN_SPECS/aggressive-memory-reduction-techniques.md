# Aggressive memory-reduction techniques (cursed but safe)

**Established:** 2026-05-13 (v5.15.5.C.4 pre-coding consult; "cursed bit-packing techniques we can use safely")
**Status:** ACTIVE (NEW spec; catalogs reusable techniques + the discipline that keeps each one safe)
**Cross-references:**
- CLAUDE.md item 1 (Portfolio uint16_t bitmap — sister; the OG bitmap precedent)
- CLAUDE.md item 19 (structural fix preferred — applied when these techniques close recurring bug classes)
- CLAUDE.md item 20 (bit-packed flag storage via BITMAP_* API — sister; per-record vs cross-record discipline applies here too)
- CLAUDE.md item 27 (struct-padding-determinism — sister; padding correctness is the floor; this spec is the ceiling)
- CLAUDE.md item 28 (latency-vs-cache framework — applies when evaluating each technique's trade-off)
- `bitmap-flag-api.md` (sister; per-record vs cross-record bit-packing trade-off)
- `multi-bit-state-encoding-pattern.md` (sister; K-state slot encoding within bitmap)
- `function-struct-alignment-for-single-mov-access.md` (sister; access discipline complements compression)
- `slot-state-foreach-registry-with-storage-routing.md` (sister; choosing storage kind per access pattern)

---

## Problem statement

After applying standard memory disciplines (size-descending field order, alignas where needed, bit-packed flags via bitmap-flag-api, multi-bit state encoding for K-state slots), struct sizes can STILL be larger than the information-theoretic minimum. The remaining slack lives in:

- Padding bytes (mandatory for alignment) that aren't otherwise used
- Sign bits / high bits of integer fields representing values that are guaranteed-bounded
- Fields that store DERIVED values when the source data is also available
- Fields that are MUTUALLY EXCLUSIVE in their lifecycle (entry vs exit; allocated vs freed; etc.)
- Per-slot single-bit flags stored byte-per-flag at slot granularity

Each of these has a memory-reduction technique. Each technique has a discipline that keeps it safe — overflow can't be silently triggered; metadata bits can't be accidentally overwritten by arithmetic; derivations can't lose precision relative to stored values.

This spec catalogs the techniques with their discipline + safety analysis. Each technique has a *when-safe* / *when-unsafe* checklist so future applications don't accidentally regress.

---

## Technique 1 — Sign-bit reuse for guaranteed-non-negative values

### Pattern

For a signed integer field that's GUARANTEED non-negative by its semantics (counter, fee, price, quantity), the sign bit is dead weight. Repurpose it as a 1-bit flag.

```cpp
// Before — int64_t with 63 usable bits; sign bit unused
struct Record {
    int64_t entry_fee_cents;   // always >= 0
    bool    is_maker;          // 1B + 7B pad = 8B for one bit
};
// Size: 16B

// After — sign bit of entry_fee carries is_maker flag
struct Record {
    int64_t entry_fee_cents_with_maker_flag;  // bit 63 = is_maker; bits 0-62 = entry_fee_cents
};
// Size: 8B

// Accessor discipline (in same header as struct):
inline int64_t record_get_fee(const Record& r) {
    return r.entry_fee_cents_with_maker_flag & 0x7FFFFFFFFFFFFFFFLL;  // mask off bit 63
}
inline bool record_is_maker(const Record& r) {
    return (r.entry_fee_cents_with_maker_flag >> 63) & 1;
}
inline void record_set(Record& r, int64_t fee_cents, bool is_maker) {
    r.entry_fee_cents_with_maker_flag = (fee_cents & 0x7FFFFFFFFFFFFFFFLL) | ((int64_t)is_maker << 63);
}
```

### When safe

- Field is provably non-negative for the lifetime of the value (compile-time-invariant; e.g., fee always > 0)
- No raw `+` / `-` / comparison operators called directly on the packed field; ALL access via accessor functions
- `static_assert` documents the bit assignment + max value
- Decoder masks BEFORE returning (defense against later refactor that uses raw field)

### When UNSAFE

- Field might legitimately be negative (signed P&L; deltas; balance)
- Raw arithmetic operators called on packed field (`x + y` adds the metadata bit to the result — silent corruption)
- Field is involved in comparison-based sorting / max/min reductions
- Field crosses thread boundary without synchronization (atomic raw reads might see the metadata bit)

### Application to v5.15.5.C.4

`FillRecord.was_win` is a 1-bit flag colocated with FPN<F> exit_net_pnl. exit_net_pnl is SIGNED (loss = negative). Sign-bit reuse on exit_net_pnl is UNSAFE (P&L can be negative).

**Not applied.** Alternative: cross-slot bitmap (Technique 4).

---

## Technique 2 — Low-bit reuse for aligned pointers (tagged pointers)

### Pattern

An N-byte-aligned pointer has the low `log2(N)` bits guaranteed zero. For example:
- 4B-aligned pointer = 2 low bits available
- 8B-aligned (default x86_64 heap) = 3 low bits available
- 16B-aligned = 4 low bits available
- 64B-aligned (`alignas(64)` / `aligned_alloc(64)`) = 6 low bits available

Repurpose these bits for flags.

```cpp
// Before — pointer + flag byte (16B + alignment pad)
struct Slot {
    Order* order;       // 8B
    bool   is_partial;  // 1B + 7B pad
};
// Size: 16B

// After — tagged pointer (order MUST be 8B-aligned; bit 0 = is_partial)
struct Slot {
    uintptr_t order_with_partial_flag;  // 8B
};
// Size: 8B

inline Order* slot_get_order(const Slot& s) {
    return (Order*)(s.order_with_partial_flag & ~0x1ULL);  // mask off low bit
}
inline bool slot_is_partial(const Slot& s) {
    return s.order_with_partial_flag & 0x1ULL;
}
inline void slot_set(Slot& s, Order* o, bool partial) {
    // o must be 8B-aligned (verified by static_assert or runtime check)
    s.order_with_partial_flag = (uintptr_t)o | (uintptr_t)partial;
}
```

### When safe

- Pointer alignment is GUARANTEED — verified by `alignas` on target type OR allocation discipline (aligned_alloc / pool with known alignment)
- ALL access via accessor functions that mask before deref
- Static assertion documents required alignment: `static_assert(alignof(Order) >= 2)` for 1 tag bit
- Pointer is non-null when accessed (or accessor returns nullptr appropriately)
- Pointer not passed by raw value to external APIs (would carry tag bits, breaking their assumption)

### When UNSAFE

- Pointer might not be aligned (e.g., points into the middle of a buffer; arbitrary user-supplied)
- Code outside the accessor's TU might dereference raw value (would crash via misaligned access)
- Pointer might be NULL — accessor needs explicit null handling (mask might convert NULL to a non-NULL-looking value if low bit is set)
- Migration: prior code reads raw pointer; tagging now means readers see corrupted addresses

### Application to v5.15.5.C.4

OMS state doesn't have any candidate pointer-with-flag scenarios at hot path. **Not applied to C.4** but kept catalogued for future use (e.g., OrderManager's order_pool could use tagged pointer for "is_inflight" flag when allocator alignment ≥ 4B).

---

## Technique 3 — Cross-slot SoA bit-packing for per-slot booleans

### Pattern

Per-slot single-bit flags currently stored as `uint8_t flag[MAX_SLOTS]` (1 byte per slot, 87.5% wasted) collapse to a single bitmap at container level: `uint16_t flag_bitmap` (1 bit per slot for 16 slots).

```cpp
// Before — 16 bytes for 16 single-bit flags
struct OMS {
    uint8_t per_slot_flag[16];  // 16B; 1B/slot
    // ...
};

// After — 2 bytes for 16 single-bit flags
struct OMS {
    uint16_t per_slot_flag_bitmap;  // 2B; 1 bit/slot
    // ...
};
// Saves 14 bytes; access via BITMAP_IS_SET (CLAUDE.md item 20)
```

### When safe

- Flag is single-bit (binary state) per slot
- Cross-thread access discipline same as existing bitmap fields (use atomic-bitmap variants if cross-thread)
- The MASK_<NAME>_SLOT(N) macros use BITMAP_BIT_U16/U32/U64(N) to compute the bit at the correct width (prevents int-truncation bugs at high bits)

### When UNSAFE

- Cross-record bit-packing (storing ONE per-slot flag for ALL slots in a single word) is the OPPOSITE of in-record bit-packing. Mixed semantics confuse readers. Per CLAUDE.md item 20: "DO NOT bit-pack ACROSS records" applies to FIELDS WITHIN A RECORD'S FLAG SET. Cross-record bitmaps for per-slot flags (like Portfolio's slot bitmap) ARE the canonical pattern; this is the inverse case where it's CORRECT.
- Multi-bit-per-slot state needs multi-bit-state-encoding-pattern, not single-bit bitmap

### Application to v5.15.5.C.4

`FillRecord.was_win` is 1 bit per slot, stored 1B per slot in current layout (8B with pad — alignment forces 8B slot in record). Total: 16 records × 8B = 128B used for 16 bits of information.

**APPLY:** Extract `was_win` to a cross-slot bitmap:
```cpp
uint16_t last_was_win_bitmap;  // 2B; bit N = was_win for slot N
```

Savings: 16 × 8B (per-record was_win + pad) - 2B (bitmap) - 6B (alignment pad after bitmap) = ~120B per FillRecord array. **Substantial.**

After extraction, FillRecord's size shrinks by 8B (the was_win + its alignment pad) → 120B per record. Or 96B if other 24B fields can also be trimmed.

---

## Technique 4 — Derive vs store (lazy compute)

### Pattern

A field that stores a value computable from OTHER available data can be eliminated. The derived field is computed at read sites that need it.

```cpp
// Before — store entry_notional (= entry_price × qty)
struct FillRecord {
    FPN<F> entry_price;    // 24B
    FPN<F> qty;            // 24B
    FPN<F> entry_notional; // 24B (DERIVED — could be computed)
};
// Size: 72B per record

// After — compute on demand
struct FillRecord {
    FPN<F> entry_price;    // 24B
    FPN<F> qty;            // 24B
    // entry_notional removed; derive at read site
};
// Size: 48B
// Access: FPN_Mul(rec.entry_price, rec.qty)
```

### When safe

- Source data (entry_price + qty) is reliably available at read site — same lifetime, same access path
- Computation is cheap (single FPN_Mul ≈ ~10 cycles); not in inner loop
- Precision of derivation matches stored value (no rounding drift); for FPN<F> with exact arithmetic, this holds
- Source data is stable between write and read (not mutated; or mutation observed in tests)
- Used at FEWER read sites than write sites; computation cost ≪ storage savings × access count

### When UNSAFE

- Source data not preserved at read time (e.g., entry_price overwritten by next entry on same slot)
- Computation expensive (transcendentals, large-iteration sums)
- Derived value used in tight inner loop where computation cost > cache miss savings (per CLAUDE.md item 28 framework)
- Source data has different precision / scale (would change derived semantics)

### Application to v5.15.5.C.4

`FillRecord.exit_entry_notional` (24B per slot × 16 = 384B). Question: is Position.entry_price + Position.qty preserved at exit fill time?

**Verified UNSAFE 2026-05-13** by /merge-scan agent — same-cycle SELL→BUY on same slot overwrites `Position.entry_price + .quantity` before DrainPostFill reads. See `phase-separated-drainer-for-safe-cross-temporal-derives.md` for the STRUCTURAL FIX that unblocks this technique.

### Transient-source-data failure mode (anti-pattern; added v5.15.5.C.4)

**When derive-vs-store fails by source-data lifecycle, not by precision or compute cost.**

A derive attempt that LOOKS safe (source fields exist; computation is cheap; precision is exact) can still fail when:
- Source state is owned by a TRANSIENT lifecycle object (Order struct freed after fill; Position struct overwritten on slot reuse; event consumed from SPSC ring)
- The read happens AFTER the lifecycle event that destroys/overwrites the source

Detection signature (from FoxML_Trader_v2 v5.15.5.C.4 history — two failed derive attempts):
- D2.C `exit_entry_notional` derive: blocked because Position.entry_price overwritten by same-cycle Portfolio_OpenSlot
- D2.D `exit_total_fees` derive: blocked because Order.is_maker freed after HandleFill; exit fill_price never snapshotted

The DEFENSIVE snapshot (FillRecord) exists PRECISELY because the source is transient. Two failures by the same mechanism = recurring class per `structural-fix-preferred-decision-framework.md`.

### Structural fix (when this failure mode keeps blocking)

The structural answer is NOT to defensively snapshot every field that might be derived — that's the snapshot-class growing without bound. The structural answer is to RESHAPE THE PROCESSING DISCIPLINE so source state is preserved through the consumer pass:

**Phase-separated drainer** (`phase-separated-drainer-for-safe-cross-temporal-derives.md`) splits the drain cycle into event-type phases with consumer passes interleaved at safe phase boundaries. Source state is guaranteed in CLOSE-completed form during the close-side consumer pass; derive becomes safe.

After applying phase-separated drainer to v5.15.5.C.4:
- `exit_entry_notional` derive → SAFE (Position state preserved through DrainPostFill)
- `exit_total_fees` derive → SAFE (Position preserved + Position.exit_fill_price + Position.is_maker added at HandleFill SELL)
- `exit_net_pnl` derive → SAFE (same)
- FillRecord shrinks from 128B → ~56B (1 cache line per record vs 2)
- Saves ~1152B per OMS structurally + closes the transient-source-data failure mode for this surface

**When considering Technique 4 in the future:** first check whether the source data is transient (owned by an event or a reusable slot). If yes, derive is blocked UNLESS the surrounding processing discipline guarantees the source survives the consumer pass. Phase-separated drainer is the canonical structural enabler.

---

## Technique 5 — Temporal union for mutually-exclusive lifecycle fields

### Pattern

Fields used in DIFFERENT phases of a lifecycle (entry vs exit; allocated vs freed; pre-flight vs post-flight) can SHARE memory via union when their lifecycles don't overlap.

```cpp
// Before — store entry + exit fields separately
struct FillRecord {
    // Entry-only fields (used between entry fill and exit fill)
    FPN<F> entry_intent_price;  // ML's predicted entry price
    FPN<F> entry_slippage;      // entry_price - entry_intent_price

    // Exit-only fields (used between exit fill and next entry)
    FPN<F> exit_intent_price;   // ML's predicted exit price
    FPN<F> exit_slippage;       // exit_price - exit_intent_price
};
// Size: 96B

// After — union the entry + exit halves (mutually exclusive lifecycles)
struct FillRecord {
    union {
        struct { FPN<F> intent_price; FPN<F> slippage; } entry;
        struct { FPN<F> intent_price; FPN<F> slippage; } exit;
    };
    int8_t  phase;  // 0 = entry-only; 1 = exit-only (drives union interpretation)
};
// Size: 56B + alignment pad
```

### When safe

- Phases are TRULY mutually exclusive (not just rare to overlap; truly impossible by lifecycle)
- A discriminator field (`phase` enum) drives which union member is valid
- Accessor functions check `phase` before reading; assert phase matches
- Test coverage exercises both phases including transition
- No external API exposes the raw struct (would see uninitialized union member)

### When UNSAFE

- Phases COULD overlap in edge cases (partial fills crossing boundaries; cancellation paths)
- No discriminator → readers can't tell which union member is valid
- Cross-thread access without synchronization on phase + union
- Byte-equivalence tests (HMAC, memcmp) — union sees uninitialized bytes from the non-active member

### Application to v5.15.5.C.4

FillRecord's entry-side + exit-side ARE temporally ordered (entry comes before exit). But at exit fill, drainer reads BOTH halves (entry-side for fee reconciliation; exit-side for the new accounting). **Phases are NOT mutually exclusive at the read point.** Union doesn't apply.

**Not applied to C.4.** Catalogued for future use (e.g., Order<F>'s exchange_id vs net_pnl_calc fields might be lifecycle-exclusive in submit-vs-fill phases).

---

## Technique 6 — Bit-field packing within a single integer

### Pattern

C++ `uint32_t : N` syntax packs sub-byte fields into a single integer at compile-time-known bit positions.

```cpp
struct Compact {
    uint32_t flag_a       : 1;   // 1 bit
    uint32_t flag_b       : 1;   // 1 bit
    uint32_t small_count  : 6;   // 6 bits (0-63)
    uint32_t state        : 4;   // 4 bits (16 states)
    uint32_t timestamp_us : 20;  // 20 bits (~1 second of microseconds)
};
// Size: 4B; uses 32 bits exactly
```

### When safe

- Bit positions are documented (offset within integer) for ABI stability
- No cross-platform endianness concerns OR explicit byte order discipline
- Fields don't need atomic access (bit-field reads/writes are NOT atomic; compiler does read-modify-write of the enclosing integer)
- No cross-thread mutation (would race)

### When UNSAFE

- Cross-platform / cross-compiler — bit-field layout is implementation-defined
- Cross-thread access — bit-field writes are NOT atomic on the field; the enclosing integer is read-modify-written
- Byte-equivalence tests — bit-field layout depends on compiler; bytes may differ between compilations
- Atomic operations needed on individual bits — use `__atomic_fetch_or` with explicit bit masks instead (per BITMAP_ATOMIC_*)

### Comparison with bitmap-flag-api

`bitmap-flag-api.md`'s BITMAP_* macros are STRICTLY PREFERRED over `uint32_t : N` bit-fields in this codebase. The macros give:
- Explicit bit positions (named MASK_<X> constants)
- Atomic variants (BITMAP_ATOMIC_*)
- Cross-platform predictable layout
- Better single-mov-access discipline (mask is compile-time constant)

`uint32_t : N` bit-fields are catalogued here for completeness but should be AVOIDED in favor of BITMAP_* macros.

### Application to v5.15.5.C.4

**Not applied.** BITMAP_* / MBS_* macros already provide equivalent packing with better discipline.

---

## Technique 7 — Reduced-precision packing (FPN<F> variant types)

### Pattern

Convert a field from FPN<F=64> (24B; ~192-bit precision) to FPN<F=32> (smaller representation) when value range + precision tolerance allow.

### When safe

- Value range fits within reduced precision (analytical bound; not empirical observation)
- Downstream math operators support the reduced type (or explicit conversion at boundaries)
- Tests cover the reduced-precision arithmetic
- The math invariant (CLAUDE.md hot-path math is FPN<F> only) is preserved

### When UNSAFE

- Accounting precision required (entry/exit notional, fee accumulation across many trades)
- Conversion at boundary loses bits silently
- Reduced-precision FPN<F> isn't a defined type in the codebase (FPN<32> would need new arithmetic operator overloads)

### Application to v5.15.5.C.4

Adding FPN<32> as a new type variant is a substantial refactor (new arithmetic overloads, new conversion paths). **Not applied to C.4.** Catalogued for future investigation.

---

## Combined C.4 application

For v5.15.5.C.4 FillRecord, the applicable techniques and savings:

| Technique | Apply? | Savings (per OMS) | Notes |
|---|---|---|---|
| Technique 1 (sign-bit reuse) | NO | — | exit_net_pnl is signed; can't reuse |
| Technique 2 (tagged pointer) | NO | — | No pointer-with-flag candidates in FillRecord |
| Technique 3 (cross-slot SoA bitmap) | **YES** | **~120B** | Extract `was_win` from FillRecord to `last_was_win_bitmap` at OMS level |
| Technique 4 (derive vs store) | **PROVISIONAL** | **~384B** | Remove `exit_entry_notional`; derive from Position.entry_price × Position.qty (verify Position state preservation) |
| Technique 5 (temporal union) | NO | — | Entry/exit fields both read at exit; not exclusive |
| Technique 6 (bit-field packing) | NO | — | BITMAP_* macros preferred |
| Technique 7 (reduced precision) | NO | — | Out of scope (new arithmetic overloads) |

### Combined savings (best case)

- Technique 3: 120B savings (was_win → bitmap)
- Technique 4: 384B savings (exit_entry_notional → derived)
- **Total: ~504B saved out of current 128B × 16 = 2048B FillRecord array → 1544B (25% reduction)**

After applying, FillRecord becomes 96B per record × 16 = 1536B (down from 2048B). 96B = 1.5 cache lines per record (was 2). Sparse close-mask iter saves ~0.5 cache lines per slot access.

### Bonus structural effect

Techniques 3 + 4 EACH reduce FillRecord to a SMALLER, MORE FOCUSED representation:
- was_win bitmap is cross-slot SoA at OMS level (proper home)
- exit_entry_notional is derived → no storage required → no future-mutation bugs

The "FillRecord shape" becomes more deliberate. Adding the next per-slot field requires explicit registry placement (per `slot-state-foreach-registry-with-storage-routing.md`); the SoA-vs-AoS decision is enforced.

---

## Application checklist (per technique)

For each technique application:

- [ ] Document the technique number + safety invariants in a comment near the storage definition
- [ ] Provide accessor functions (named `<struct>_get_<field>` / `_set_<field>`) — all access goes through them
- [ ] Add `static_assert` for invariants (max value, bit positions, alignment requirement, etc.)
- [ ] Test coverage: directly exercise the boundary conditions (max value, sign overflow, alignment violation)
- [ ] Migration: identify all current read sites; verify accessor coverage
- [ ] Verify single-mov access discipline (`function-struct-alignment-for-single-mov-access.md`): each accessor compiles to ≤ 3 instructions

---

## Anti-patterns

### Bit-packing without accessors

```cpp
// BAD — sign bit reused but no accessor; raw arithmetic loses metadata
struct Record {
    int64_t fee_with_maker_flag;  // bit 63 = is_maker
};
int64_t total_fees = r.fee_with_maker_flag + r.other_fee;  // INCLUDES the metadata bit!

// FIX — accessor enforces masking
inline int64_t get_fee(const Record& r) { return r.fee_with_maker_flag & 0x7FFFFFFFFFFFFFFFLL; }
int64_t total_fees = get_fee(r) + r.other_fee;  // metadata masked out
```

### Reusing bits without invariant proof

```cpp
// BAD — assumes value will always fit but doesn't prove it
struct Record {
    int64_t count_high_bit_assumed_unused;  // bit 63 reused as flag; no overflow guard
};
// Months later, count grows to 2^63 → wraps into the flag bit → silent corruption
```

### Forgetting union discriminator

```cpp
// BAD — union without discriminator
struct State {
    union {
        struct { /* entry-phase fields */ } entry;
        struct { /* exit-phase fields */ } exit;
    };
    // No phase field; reader can't tell which is valid
};
```

### Skipping accessor for "fast path"

```cpp
// BAD — bypassing accessor for "perf"
inline int64_t get_fee(const Record& r) { return r.fee_with_maker_flag & 0x7FFFFFFFFFFFFFFFLL; }
// Hot path:
total += rec.fee_with_maker_flag;  // BYPASSED — picks up metadata bit
```

---

## Cross-references to CLAUDE.md

These techniques compose with existing items but are not yet promoted to CLAUDE.md:

- **Item 1 (Portfolio bitmap):** the OG cross-slot SoA bitmap; this spec generalizes
- **Item 20 (bitmap-flag-api):** sister; in-record vs cross-record discipline; this spec adds aggressive techniques beyond standard bit-packing
- **Item 27 (struct padding determinism):** sister; padding bytes are a candidate for repurposing IF byte-equivalence isn't required for the struct
- **Item 28 (latency-vs-cache framework):** prerequisite analysis for whether each technique's compute cost is justified by cache savings

Promotion candidate to CLAUDE.md as item 31 after 3+ applications across techniques shipped (v5.15.5.C.4 = first if applied to was_win bitmap + exit_entry_notional derive).

---

## Trade-offs + when to relax

### Apply aggressive techniques when:

- Struct is on hot path (cache footprint matters; ~10-50% reduction is meaningful)
- Struct is in a 16-slot array (savings multiply by 16; cumulative ~hundreds of bytes)
- Field has provable invariants (compile-time-bound; tested)
- Accessor discipline is enforceable (struct + accessor in same TU; no external raw access)

### Skip aggressive techniques when:

- Struct is one-off boot configuration (memory savings irrelevant)
- Invariants can't be proven (might cause silent corruption)
- Cross-platform / cross-compiler portability concerns (bit-field layout, endian)
- Cross-thread mutation without atomic accessor variants

### Default discipline: standard bit-packing first

Apply `bitmap-flag-api.md` + `multi-bit-state-encoding-pattern.md` FIRST. THEN consider aggressive techniques from this spec for the remaining slack. Don't reach for cursed techniques as the first lever — they compose well only after the boring savings are realized.

---

**End of spec.**
