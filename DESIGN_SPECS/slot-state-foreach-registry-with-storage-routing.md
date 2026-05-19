---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-13
tags: [framework-discipline, structural-fix, data-oriented-design]
surface: [registry, bitmap-packed, hot-path]
sister_specs: [persisted-struct-with-ephemeral-field-coexistence-pattern.md, x-macro-registry-with-presence-dispatch.md, multi-bit-state-encoding-pattern.md]
applies_at_skills: []
---

# Slot-state FOREACH registry with explicit storage-kind routing

**Established:** 2026-05-13 (v5.15.5.C.4 pre-coding consult)
**Status:** ACTIVE (NEW spec; first canonical application = v5.15.5.C.4 dual-registry split of OMS per-slot scratch state)
**Cross-references:**
- CLAUDE.md item 13 (X-macro registry pattern; this is a per-slot specialization)
- CLAUDE.md item 19 (structural fix preferred; this closes the SoA-mirror Class-18 class)
- CLAUDE.md item 20 (in-record bit-packing trade-off rule; sister — same per-record vs per-array trade-off applies)
- CLAUDE.md item 28 (latency-vs-cache framework; per-slot access pattern is the deciding factor)
- `x-macro-registry-with-presence-dispatch.md` (base pattern)
- `autopopulate-pattern-for-production-caller-class.md` (AUTOPOPULATE companion for slot init/reset)
- `cache-layout-discipline-for-hot-side-structs.md` (sister — per-record HOT/WARM/COLD discipline)
- `function-struct-alignment-for-single-mov-access.md` (sister — slot record access discipline)

---

## Problem statement

In container structs with **per-slot scratch state** (e.g., OrderManagerState with 16-slot Portfolio), per-slot fields can live in two distinct layouts:

1. **SoA cross-slot** — field `X` stored as `X[MAX_SLOTS]` array at container level (16 entries × type-size); all slots' X-values colocated in a single array. Cache-line-shared across slots.

2. **AoS per-record** — field `X` embedded inside a per-slot record struct (e.g., FillRecord) at offset `O`; record array `record[MAX_SLOTS]` at container level. Per-slot fields colocated within a record.

Both layouts are valid for some access patterns; neither dominates. **Choosing the wrong layout for the wrong access pattern wastes cache lines** (worst case: ~3× the cache cost of the optimal choice).

Worse: in ad-hoc field additions, the CHOICE is implicit and historically driven. New per-slot fields get added "wherever the last one was added" — not "where the access pattern dictates." Over time:
- The SoA array gets a NEW unrelated field appended (mirror class: next per-slot scalar gets added here too without thought)
- The AoS record gets a NEW unrelated field appended (record bloat past 1-2 cache lines)
- Both layouts mirror each other (drift between PARALLEL X arrays + FILLRECORD.X fields)

The Class-18 mirror class manifests as: **2-3 different per-slot containers (SoA arrays + AoS records) drifting in parallel, with no structural enforcement of which fields go where.**

---

## Pattern

Use **TWO sister FOREACH registries** with explicit storage-kind routing. The choice of which registry a field goes into IS the design decision — encoded once in the registry tuple, enforced at compile time.

```cpp
// SoA cross-slot arrays: fields accessed via slot index; shared across all slots
//   When to use:
//     - Field is small (≤ 8B)
//     - Drainer reads field for current slot; parallel-array cache line shared
//       across all 16 slots in close-mask iter (sparse-access cache win)
//     - Future per-slot scratch fields with same access pattern
#define FOREACH_OMS_SLOT_SCALAR_ARRAY(X)                \
    X(last_realized_return,    double,  /*init=*/ 0.0) \
    X(last_exit_predicted_p,   double,  /*init=*/ 0.0) \
    X(last_exit_predicted_meta, uint8_t, /*init=*/ 0)  \
    /* Add here: future per-slot scalar (≤8B) with same access pattern */

// AoS per-record: fields embedded in FillRecord struct; per-slot colocated
//   When to use:
//     - Field is large (≥ 16B; FPN<F>) OR closely coupled with other FillRecord fields
//       in same access pattern (e.g., entry_notional + entry_fee read together on ENTRY)
//     - Per-record cache discipline benefits from colocating related fields
#define FOREACH_FILL_RECORD_FIELD(X)                                \
    X(entry_notional,      FPN<F>, /*init=*/ FPN_Zero<F>())         \
    X(entry_fee,           FPN<F>, /*init=*/ FPN_Zero<F>())         \
    X(exit_net_pnl,        FPN<F>, /*init=*/ FPN_Zero<F>())         \
    X(exit_entry_notional, FPN<F>, /*init=*/ FPN_Zero<F>())         \
    X(exit_total_fees,     FPN<F>, /*init=*/ FPN_Zero<F>())         \
    X(was_win,             int8_t, /*init=*/ 0)                     \
    /* Add here: future per-slot field closely coupled with FillRecord access pattern */
```

Each registry generates its own struct + init pattern. The OMS container uses both:

```cpp
struct OrderManagerState {
    // ...other fields...

    // Per-slot scratch state — split by access pattern via FOREACH registries
    #define EMIT_ARRAY(name, type, init) type name[MAX_PORTFOLIO_POSITIONS];
    FOREACH_OMS_SLOT_SCALAR_ARRAY(EMIT_ARRAY)
    #undef EMIT_ARRAY

    FillRecord last_fill[MAX_PORTFOLIO_POSITIONS];  // FillRecord generated from FOREACH_FILL_RECORD_FIELD

    // ...other fields...
};

// FillRecord struct itself is registry-generated:
struct FillRecord {
    #define EMIT_FIELD(name, type, init) type name = init;
    FOREACH_FILL_RECORD_FIELD(EMIT_FIELD)
    #undef EMIT_FIELD
};

// Init companion: walks both registries to zero/init all per-slot state for a given slot
#define OMS_PER_SLOT_INIT(oms, slot) \
    do { \
        #define EMIT_ARRAY_INIT(name, type, init) (oms)->name[(slot)] = (init); \
        FOREACH_OMS_SLOT_SCALAR_ARRAY(EMIT_ARRAY_INIT) \
        #undef EMIT_ARRAY_INIT \
        #define EMIT_RECORD_INIT(name, type, init) (oms)->last_fill[(slot)].name = (init); \
        FOREACH_FILL_RECORD_FIELD(EMIT_RECORD_INIT) \
        #undef EMIT_RECORD_INIT \
    } while (0)
```

Future per-slot scratch field = **1 row in the appropriate registry**. The storage-kind choice is the design decision — encoded explicitly at addition time.

---

## Decision tree for storage-kind routing

```
NEW per-slot scratch field FOO needs storage. Which registry?

  ┌─ Is FOO read together with OTHER FillRecord fields in the same access pattern?
  │
  ├── YES → FOREACH_FILL_RECORD_FIELD
  │         (e.g., new exit-accounting field paired with exit_net_pnl reads)
  │
  └── NO  → Is FOO ≤ 8B and read sparsely per-slot via close-mask iter?
            │
            ├── YES → FOREACH_OMS_SLOT_SCALAR_ARRAY
            │         (e.g., per-slot probability score; parallel-array cache line shared across slots)
            │
            └── NO  → consider FOREACH_FILL_RECORD_FIELD anyway
                     (e.g., field is medium-sized 16B but doesn't pair with existing accesses;
                      colocation in record still avoids straddle; trailing slack absorbs)
```

The decision is documented in the field's registry-row position (which registry + which adjacent fields) AND in a `/*access-pattern:*/` comment near the row for future contributors.

---

## Trade-offs

### SoA cross-slot wins when:
- Sparse access (close-mask iter touches 1-3 slots per cycle) — parallel array's cache line shared
- Field small (≤8B) — array fits in 1-2 cache lines for all 16 slots
- Drainer reads in batches that benefit from sequential array stride

### AoS per-record wins when:
- Field large (≥16B; FPN<F>) — separate array would waste cache lines per slot access
- Field closely coupled with other record fields in access pattern (entry_notional + entry_fee on ENTRY)
- Per-slot iteration touches many record fields at once

### Per-slot iteration cache analysis (drainer close-mask iter example)

Currently in `EventLoop_DrainPostFillOneCore`:
- Reads `oms->last_fill[slot]` (128B = 2 cache lines per record; 16 records × 128B = 32 cache lines for all)
- Reads `oms->last_realized_return[slot]` (double; entire array = 128B = 2 cache lines)
- Reads `oms->last_exit_predicted_p[slot]` (double; entire array = 128B = 2 cache lines)
- Reads `oms->last_exit_predicted_meta[slot]` (uint8_t; entire array = 16B = 1 cache line)

Cache-line cost analysis:

| Access pattern | Pre-D2 (SoA preserved) | Post-D2-Option-A (AoS consolidated 192B/record) | Net |
|---|---|---|---|
| Sparse close-mask iter (1-3 slots) | 2-3 records + 3 parallel-array lines (shared) = ~5-8 cache lines | 3 records × 3 cache lines per record = ~9-12 cache lines | **SoA wins** |
| Dense close-mask iter (10+ slots) | ~20 record cache lines + 7 parallel-array lines (mostly cached) = ~27 cache lines | 10+ records × 3 cache lines = ~30+ cache lines | **SoA wins** |

**Conclusion:** for the drainer's typical sparse access, SoA cross-slot is strictly cheaper. The "consolidate everything into FillRecord" approach worsens cache footprint by 3-4 cache lines per iter.

**Why SoA wins here:** the parallel arrays are small (16 × 8B = 128B for doubles; 16 × 1B = 16B for uint8). Their cache lines are SHARED across all slots in a close-mask iter. After the first slot's access pulls in the parallel-array cache line, subsequent slots' accesses hit cache. Net amortized cost per slot: ~0.

---

## Application checklist

When applying this pattern:

- [ ] Identify the per-slot scratch state (fields read/written by per-slot accessors)
- [ ] Classify each field by access pattern (sparse-per-slot-read vs paired-with-record-fields)
- [ ] Define the two FOREACH registries with explicit `/*access-pattern:*/` comments per row
- [ ] Generate struct + init companion via X-macro expansion
- [ ] Verify cache discipline via `static_assert(sizeof(FillRecord) == X)` + per-array size locks
- [ ] Verify single-mov access discipline per `function-struct-alignment-for-single-mov-access.md`
- [ ] AUTOPOPULATE for per-slot init/reset (composes with `autopopulate-pattern-for-production-caller-class.md`)
- [ ] Document the decision-tree call ("FIELD X goes in REGISTRY Y because ACCESS PATTERN Z") in the rationale comment near the FOREACH definition

---

## Anti-patterns

### Ad-hoc field addition without registry

```cpp
// BAD — new field added directly to OMS struct without registry routing
struct OrderManagerState {
    // ...
    double last_realized_return[MAX_PORTFOLIO_POSITIONS];  // pre-existing parallel array
    double last_exit_predicted_p[MAX_PORTFOLIO_POSITIONS]; // pre-existing parallel array
    double last_brier_score[MAX_PORTFOLIO_POSITIONS];      // NEW — ad-hoc!
    // No registry; no init/reset companion; the "next per-slot field" goes WHERE?
};
```

The Class-18 mirror: now 3 parallel arrays exist; future contributor adds a 4th, 5th, ... — pattern recurs.

### Mixing storage kinds in one registry

```cpp
// BAD — single registry with mixed access patterns
#define FOREACH_OMS_PER_SLOT_SCALAR(X) \
    X(last_realized_return,    double,  0.0)               /* small, sparse access */ \
    X(entry_notional,          FPN<F>,  FPN_Zero<F>())     /* large, paired access */ \
    X(was_win,                 int8_t,  0)                 /* small, paired with FillRecord */
// Drainer can't tell which array layout to use; init/reset macros must handle both;
// future contributors don't know which registry pattern to follow
```

**Fix:** two separate registries with explicit access-pattern documentation per registry.

### Over-consolidation into single AoS record

```cpp
// BAD — extending FillRecord with every per-slot scalar
struct FillRecord {
    FPN<F> entry_notional, entry_fee, exit_net_pnl, exit_entry_notional, exit_total_fees;
    double realized_return_d;    // moved from parallel array — cache regression
    double exit_predicted_p_d;   // moved from parallel array — cache regression
    uint8_t was_win;
    uint8_t exit_predicted_meta;  // moved from parallel array — cache regression
};
// FillRecord grew from 128B → 152B → straddles 3 cache lines per record (was 2)
// Cache footprint per slot iter WORSENS for sparse access
```

**Fix:** route fields to SoA when sparse access pattern + small size warrant it.

---

## Cross-references to CLAUDE.md

- **Item 13 (X-macro registry):** this spec is a per-slot specialization of the base X-macro registry pattern
- **Item 19 (structural fix preferred):** closes the SoA-mirror Class-18 class structurally — adding a per-slot field requires explicit registry choice (cannot drift)
- **Item 20 (bit-packed flag storage trade-off):** sister — same per-record vs cross-record trade-off applies to bit-packing decisions (bitmap-flag-api spec); same decision pattern, different field type
- **Item 28 (latency-vs-cache framework):** prerequisite for the access-pattern analysis used to route fields

Promotion candidate to CLAUDE.md as item 30 after 2+ applications shipped (v5.15.5.C.4 = first).

---

## Related design patterns

- **`x-macro-registry-with-presence-dispatch.md`** — base pattern; this spec extends with explicit STORAGE_KIND routing across two registries
- **`autopopulate-pattern-for-production-caller-class.md`** — AUTOPOPULATE companion macro consumes both registries
- **`cache-layout-discipline-for-hot-side-structs.md`** — sister; record-level HOT/WARM/COLD cluster discipline (applies to AoS records)
- **`bitmap-flag-api.md`** — sister; per-record bit-packing follows same per-vs-cross-record reasoning

---

## Composition with phase-separated drainer (v5.15.5.C.4)

When the drainer adopts the `phase-separated-drainer-for-safe-cross-temporal-derives.md` pattern, this spec's FOREACH_FILL_RECORD_FIELD registry SHRINKS naturally. Fields that previously HAD to be stored as defensive snapshots become derivable from preserved Position state during the close-side consumer pass:

Pre-C.4 state (3 storage axes — AoS record + SoA cross-slot arrays + bitmaps):
```cpp
#define FOREACH_FILL_RECORD_FIELD(X) \
    X(entry_notional,      FPN<F>, FPN_Zero<F>())  \  /* derivable from Position post-Phase H */
    X(entry_fee,           FPN<F>, FPN_Zero<F>())  \  /* derivable from Position post-Phase H */
    X(exit_net_pnl,        FPN<F>, FPN_Zero<F>())  \  /* derivable post-Phase G */
    X(exit_entry_notional, FPN<F>, FPN_Zero<F>())  \  /* derivable post-Phase G */
    X(exit_total_fees,     FPN<F>, FPN_Zero<F>())  \  /* derivable post-Phase G */
    X(was_win,             int8_t, 0)                 /* → cross-slot bitmap post-Phase J */
```

### Final state (post v5.15.5.C.4 — FillRecord eliminated entirely)

Once `phase-separated-drainer-for-safe-cross-temporal-derives.md` (Phases F+G+H) lands AND was_win moves to bitmap (Phase J), ALL FillRecord fields become derivable or migrated. FillRecord struct is **deleted** (Phase K). FOREACH_FILL_RECORD_FIELD ceases to exist.

The dual-registry pattern simplifies to **single-registry-per-storage-class** with broader storage-axis routing:

```cpp
// FOREACH_OMS_SLOT_SCALAR_ARRAY(X) — transient per-slot scratch (sibling SoA arrays on OMS)
#define FOREACH_OMS_SLOT_SCALAR_ARRAY(X)                       \
    X(last_exit_fill_price,    FPN<F>,  FPN_Zero<F>())         /* Phase G capture; sibling array */ \
    X(last_exit_predicted_p,   double,  0.0)                   /* ML state; predicted probability */ \
    X(last_exit_predicted_meta, uint8_t, 0)                    /* ML state; multi-bit packed */

// FOREACH_OMS_BITMAP(X) — cross-slot per-slot single-bit flags
#define FOREACH_OMS_BITMAP(X)                                                                       \
    X(last_was_win_bitmap,           uint16_t, 0, "1 = exit_pnl > 0 for slot N")                    \
    X(last_is_maker_bitmap,          uint16_t, 0, "1 = exit fill was maker for slot N")             \
    X(last_exit_predicted_bitmap,    uint16_t, 0, "1 = ML predicted this exit; from v5.15.5.C.2 S3b")\
    X(last_closed_mask,              uint16_t, 0, "1 = slot closed this cycle (drainer aggregate)")  \
    X(last_opened_mask,              uint16_t, 0, "1 = slot opened this cycle (drainer aggregate)")

// FOREACH_POSITION_FIELD(X) — per-slot persistent state (per persisted-struct-with-ephemeral-field-coexistence-pattern.md)
//   PERSIST fields → survive snapshot; SKIP_PERSIST fields → transient (cleared on init)
//   Sister registry to FOREACH_OMS_SLOT_SCALAR_ARRAY: same per-slot granularity, different container (Position struct)
//   See `persisted-struct-with-ephemeral-field-coexistence-pattern.md` for the PERSIST_KIND column discipline
#define FOREACH_POSITION_FIELD(X)                                              \
    X(entry_price,         FPN<F>,   FPN_Zero<F>(),  PERSIST, "...")           \
    X(quantity,            FPN<F>,   FPN_Zero<F>(),  PERSIST, "...")           \
    X(entry_fee,           FPN<F>,   FPN_Zero<F>(),  PERSIST, "...")           \
    /* ... other PERSIST fields ...  */                                        \
    /* SKIP_PERSIST fields can live here if needed; v5.15.5.C.4 moves ephemeral exit-side scratch to OMS_SLOT_SCALAR_ARRAY instead */
```

Decision tree for adding a new per-slot field, post-v5.15.5.C.4:

```
NEW per-slot field FOO needs storage. Which registry / container?

  ┌─ Is FOO persistent across snapshot restarts?
  │
  ├── YES → FOREACH_POSITION_FIELD with PERSIST_KIND=PERSIST
  │         (e.g., new entry-side state survived across restarts)
  │
  └── NO  → Is FOO single-bit per slot?
            │
            ├── YES → FOREACH_OMS_BITMAP (cross-slot uint16/32/64 bitmap)
            │         (per CLAUDE.md item 20 + bitmap-flag-api.md)
            │
            └── NO  → Is FOO multi-bit slot K-state value (K=2..16)?
                     │
                     ├── YES → cross-slot SoA via multi-bit-state-encoding-pattern.md
                     │         (uint8/16 byte per slot packed with adjacent K-state fields)
                     │
                     └── NO  → FOREACH_OMS_SLOT_SCALAR_ARRAY
                              (sibling SoA cross-slot array on OMS state; scalar 8B+)
                              OR FOREACH_POSITION_FIELD with PERSIST_KIND=SKIP_PERSIST
                              (ephemeral but semantically per-position; co-located with entry-side state)
```

Note the broader pattern: **per-slot state has TWO container axes (Position / OMS) and THREE storage shapes per container (scalar AoS / scalar SoA / bitmap).** The dual-registry framing this spec originally proposed generalizes to a **multi-registry decision tree** as the codebase matures. Each registry has a clear semantic home; the choice is documented per field via registry placement.

The FillRecord-as-snapshot pattern is permanently extinct after v5.15.5.C.4 ships. The "per-slot AoS scratch state" anti-pattern is replaced by:
- Persistent per-slot state → Position struct (via FOREACH_POSITION_FIELD)
- Ephemeral per-slot scratch → sibling SoA arrays on OMS (via FOREACH_OMS_SLOT_SCALAR_ARRAY) OR Position SKIP_PERSIST fields
- Per-slot single-bit flags → cross-slot bitmap (via FOREACH_OMS_BITMAP)
- Per-slot K-state values → multi-bit-state-encoding-pattern.md

Composable, structurally explicit, registry-driven. Adding the next per-slot field traverses the decision tree above; the result is 1 row in the appropriate registry.

---

**End of spec.**
