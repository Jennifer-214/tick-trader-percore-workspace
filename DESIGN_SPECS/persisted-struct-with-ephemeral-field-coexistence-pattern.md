# Persisted-struct-with-ephemeral-field coexistence (FOREACH with PERSIST_KIND column)

**Established:** 2026-05-13 (v5.15.5.C.4 pre-coding consult; emerged from "should Position grow `exit_fill_price + is_maker` or do these live on a sibling OMS array?" decision)
**Status:** ACTIVE (NEW spec; first canonical application = v5.15.5.C.4 FOREACH_POSITION_FIELD migration with PERSIST_KIND column for Position struct)
**Cross-references:**
- CLAUDE.md item 13 (X-macro registry for multi-site additions)
- CLAUDE.md item 15 (parity-tested-by-construction — wire-format byte preservation via PERSIST_KIND filter)
- CLAUDE.md item 19 (structural fix preferred — closes "snapshot version bump every ephemeral field addition" class)
- CLAUDE.md item 21 (AUTOPOPULATE companion macro for registry-driven init/reset)
- `x-macro-registry-with-presence-dispatch.md` — base pattern; PERSIST_KIND is a column in the tuple
- `heterogeneous-registry-pattern.md` — SCOPE COLUMN form (PERSIST_KIND as scope axis)
- `wire-format-byte-preservation-discipline.md` — sister; PERSIST_KIND filter enforces byte-preservation
- `autopopulate-pattern-for-production-caller-class.md` — companion AUTOPOPULATE for registry-driven save/load
- `phase-separated-drainer-for-safe-cross-temporal-derives.md` — sister structural enabler; phase discipline + persist-kind registry compose to unlock derive-from-source patterns
- `aggressive-memory-reduction-techniques.md` Technique 4 (derive vs store) — persist-kind registry expands the surface where Technique 4 is safely applicable (ephemeral fields can co-locate with persistent state without bumping wire format)

---

## Problem statement

When a struct is BYTE-PERSISTED to durable storage (snapshot file, binary log, wire protocol body), its layout becomes a wire-format contract. Adding a NEW field to that struct requires:

- Bumping the format version + handling legacy-load migration
- OR introducing a SIBLING struct that lives elsewhere (e.g., on a parent struct or sibling SoA array)

**The bug class:** each time an ephemeral / transient / never-persisted field needs to coexist with persistent state on the same conceptual entity, the developer faces a forced choice:

1. **Add to the persisted struct** → bump version → migration cost → wire format drift risk → tests that lock SHA-256 break
2. **Add to a sibling struct elsewhere** → semantic scattering (entity's state spread across multiple containers) → readers must know to consult multiple structs → next contributor doesn't know which choice was made for similar fields → drift

Both choices have costs that compound across the codebase's lifetime. Without a structural answer, every persisted struct in the codebase eventually accumulates EITHER repeated version bumps OR scattered sibling state.

**Recurrence signal (FoxML_Trader_v2 history):**
- ShardedSnapshot: bumped from v6 → v7 → v8 across the v5.x sprints as new OMS fields needed persistence
- Portfolio snapshot: version 5 today; would need bump for v5.15.5.C.4's `exit_fill_price + is_maker` additions (which are ephemeral, not actually persistent state)
- Multiple sibling arrays at OMS level (`last_realized_return[16]`, `last_exit_predicted_p[16]`, `last_exit_predicted_meta[16]`, `last_exit_predicted_bitmap`, future additions) accumulating as scratch state next to per-slot AoS records

The forced-choice class recurs every time a persisted struct gets a new ephemeral neighbor.

---

## The pattern

Use a FOREACH X-macro registry with a **PERSIST_KIND column** that drives wire-format participation. Existing persisted fields → PERSIST_KIND=PERSIST. New ephemeral fields → PERSIST_KIND=SKIP_PERSIST. Persist code walks the registry with the PERSIST filter; non-persistent fields are skipped at wire-format emit/parse time but live alongside persistent fields in the struct.

```cpp
// FOREACH_POSITION_FIELD(X) — tuple: (name, type, init, persist_kind, doc)
//   persist_kind ∈ {PERSIST, SKIP_PERSIST}
//   PERSIST       → field appears in Portfolio_Save / Portfolio_Load wire format
//   SKIP_PERSIST  → field lives in Position struct but NOT in wire format
//                    (cleared on Init; never persisted; never restored from snapshot)
#define FOREACH_POSITION_FIELD(X)                                                                                  \
    /* PERSIST fields — current wire format (PORTFOLIO_SNAPSHOT_VERSION=5) — bytewise preserved */                  \
    X(entry_price,         FPN<F>,   FPN_Zero<F>(),  PERSIST,      "entry price at position open")                  \
    X(quantity,            FPN<F>,   FPN_Zero<F>(),  PERSIST,      "position quantity")                             \
    X(entry_fee,           FPN<F>,   FPN_Zero<F>(),  PERSIST,      "entry fee paid (maker or taker)")               \
    X(stop_loss_price,     FPN<F>,   FPN_Zero<F>(),  PERSIST,      "current SL price (ratcheted)")                  \
    X(take_profit_price,   FPN<F>,   FPN_Zero<F>(),  PERSIST,      "TP price")                                      \
    X(intended_tp,         FPN<F>,   FPN_Zero<F>(),  PERSIST,      "TP at strategy_BuildParameters time")           \
    X(allocated_balance,   FPN<F>,   FPN_Zero<F>(),  PERSIST,      "balance allocated to this slot")                \
    X(entry_timestamp_us,  uint64_t, 0,              PERSIST,      "entry market timestamp (microseconds)")         \
    X(pair_index,          int8_t,   -1,             PERSIST,      "partner slot index under partials (legs A/B)") \
    /* SKIP_PERSIST fields — ephemeral exit-side scratch — NOT in wire format */                                    \
    X(exit_fill_price,     FPN<F>,   FPN_Zero<F>(),  SKIP_PERSIST, "exit fill price at HandleFill SELL (transient; cleared on next entry)") \
    X(is_maker,            uint8_t,  0,              SKIP_PERSIST, "exit fill maker/taker (transient; 1 bit; cleared on next entry)")
```

### Struct generation

```cpp
template <unsigned F>
struct Position {
    #define EMIT_FIELD(name, type, init, persist_kind, doc) type name = init;
    FOREACH_POSITION_FIELD(EMIT_FIELD)
    #undef EMIT_FIELD
    // Explicit padding for cache-line + struct-padding-determinism discipline added manually if needed
};
```

### Save walk (PERSIST filter)

```cpp
template <unsigned F>
inline int Portfolio_Save(const Portfolio<F>& portfolio, FILE* out) {
    // Existing snapshot header + version write...
    for (int slot = 0; slot < MAX_PORTFOLIO_POSITIONS; ++slot) {
        const Position<F>& pos = portfolio.positions[slot];
        #define EMIT_SAVE(name, type, init, persist_kind, doc) \
            PERSIST_KIND_EMIT_##persist_kind(WRITE_FIELD, pos.name, type)
        FOREACH_POSITION_FIELD(EMIT_SAVE)
        #undef EMIT_SAVE
    }
    // ...
}

// Token-paste dispatch on PERSIST_KIND value:
#define PERSIST_KIND_EMIT_PERSIST(op, field, type)      op(field, type)
#define PERSIST_KIND_EMIT_SKIP_PERSIST(op, field, type) /* skip — not in wire format */

#define WRITE_FIELD(field, type) fwrite(&field, sizeof(type), 1, out);
```

### Load walk (mirror save)

Same filter; legacy snapshots load unchanged because SKIP_PERSIST fields are not in the wire format — load only reads PERSIST fields, leaves SKIP_PERSIST fields at their default (zero-initialized) state.

### AUTOPOPULATE for init/reset

```cpp
// Companion macro per autopopulate-pattern-for-production-caller-class.md
#define POSITION_INIT(pos)                                                       \
    do {                                                                         \
        #define EMIT_INIT(name, type, init, persist_kind, doc) (pos).name = (init); \
        FOREACH_POSITION_FIELD(EMIT_INIT)                                        \
        #undef EMIT_INIT                                                         \
    } while (0)
```

### Migration steps

For an existing persisted struct (e.g., Position pre-v5.15.5.C.4):
1. Define FOREACH_<STRUCT>_FIELD with all existing fields, all marked PERSIST_KIND=PERSIST
2. Generate the struct via X-macro (mirror current declaration order to preserve wire format)
3. Migrate Save/Load to walk registry with PERSIST filter (byte-identical to manual writes)
4. Verify wire format byte-equivalence via SHA-256 lock test on a representative snapshot
5. THEN add new SKIP_PERSIST fields (separate commit; clean rollback boundary)

---

## When to apply

- **Persisted struct** (snapshot file, binary log, HMAC-locked wire format) — wire format must be preserved across new field additions
- **Ephemeral fields needed on the same conceptual entity** — transient values that don't survive across restarts (computed at runtime, cleared per cycle, derived from non-persisted state)
- **2+ fields anticipated to be added over time** — registry pattern overhead amortizes; for 1 one-off ephemeral field, sibling-array might be simpler
- **The struct lives in a hot/slow-path inner loop** — colocating ephemeral fields with persistent state preserves cache locality (vs sibling-array which scatters)

## When NOT to apply

- **All fields are PERSIST** — no value from the SKIP_PERSIST column; degenerate case
- **Struct is never persisted** — version-bump cost doesn't exist; no need for the filter
- **Cache locality between ephemeral + persistent is not valuable** — sibling-array might be simpler if persistence-state is rarely co-accessed with ephemeral state
- **The struct is one-off (no extension expected)** — pattern overhead not justified

---

## Trade-offs

### Wins

- **Future field additions = 1 row in registry with PERSIST_KIND choice.** No snapshot version bump for ephemeral additions. No legacy-load migration. No SHA-256 lock test breakage.
- **Semantic clarity** — fields representing the same conceptual entity (e.g., Position's per-slot state) live in ONE struct, regardless of persistence-kind. Readers don't need to consult multiple containers.
- **Cache locality** — ephemeral fields colocated with persistent fields in the same struct; per-slot iteration touches one cache line per record (vs sibling-array's cache scattering).
- **Wire format byte preservation enforced at compile time** — token-paste dispatch on PERSIST_KIND prevents accidental persistence of SKIP_PERSIST fields. Future contributor adding a new PERSIST field knows the wire format expanded; adding a SKIP_PERSIST field knows it's ephemeral.
- **Cross-platform invariant** — registry walks deterministic across compilers; no implementation-defined behavior in field ordering.

### Costs

- **Migration upfront cost** — manually-declared struct → registry-driven generation requires LOC investment (typically ~80-200 LOC for a struct with 8-12 fields).
- **Indirection at debug time** — `gdb` shows the struct's generated fields, but the source declares them via FOREACH expansion. Document the registry header file as the source-of-truth.
- **Type system complexity** — generic types in registry entries (e.g., FPN<F>) require careful templating in the EMIT macros. Use existing patterns from FOREACH_OMS_FIELD as reference.
- **Bench gate verification** — Save/Load walk via registry should compile to the same instructions as manual fwrite/fread sequence; verify via `objdump -d` spot check.

### Risks

- **Wire format byte preservation REGRESSION** — if PERSIST_KIND filter logic has a bug, SKIP_PERSIST fields could leak into wire format. Test: SHA-256 lock on representative snapshot before + after migration.
- **Default value drift** — registry's init value column must match prior manual struct default. Test: SHA-256 lock on Init'd Position (all defaults).
- **Reader-side field-access cost** — generated struct fields should have IDENTICAL offsets to pre-migration manual struct. Test: static_assert(offsetof(...) == expected) for each PERSIST field.

---

## Reference implementations

### First application: v5.15.5.C.4 — FOREACH_POSITION_FIELD migration

- Surface: `CoreFrameworks/Portfolio.hpp:24-48` (Position struct definition) + `Portfolio_Save` + `Portfolio_Load` walks
- New registry: `MemHeaders/PositionFieldRegistry.hpp` (NEW header)
- 9 existing PERSIST fields (entry_price, quantity, entry_fee, stop_loss_price, take_profit_price, intended_tp, allocated_balance, entry_timestamp_us, pair_index)
- 2 NEW SKIP_PERSIST fields (exit_fill_price, is_maker)
- Wire format byte-preserved: `PORTFOLIO_SNAPSHOT_VERSION` stays at 5; legacy snapshots load unchanged
- Closes: "Position struct extensions require snapshot version bump" class permanently

### Anticipated future applications

- **ShardedSnapshotPersist** (OMS state) — already uses FOREACH_OMS_FIELD with PERSIST_KIND column (v5.15.5.C.3 Phase 3b); this spec retroactively documents that as the first application of the pattern; v5.15.5.C.4 Position migration is the SECOND application
- **FillRecord** — being eliminated entirely in v5.15.5.C.4 Phase K (no need for the pattern post-elimination)
- **CoreContext** — could adopt for future per-core ephemeral state additions (currently mixed persistence states)
- **ParameterSlot** — seqlock-cached params; could adopt if ephemeral fields ever need to coexist
- **OrderManagerState top-level** — beyond the OMS_FIELD registry, top-level state could adopt if more ephemeral coexistence questions arise

---

## Lessons / gotchas

### PERSIST_KIND column placement in tuple

By convention, PERSIST_KIND should be the LAST or near-last column in the tuple (after name, type, init). This makes the typical read-first-3-columns workflow unobstructed; PERSIST_KIND is a secondary concern after "what is this field?"

### Migration ordering: registry first, then ephemeral additions

When migrating an existing struct:
1. First commit: introduce registry with ALL existing fields as PERSIST. Wire format unchanged. SHA-256 lock test passes.
2. Second commit: add SKIP_PERSIST fields. Wire format STILL unchanged (filter excludes new fields). SHA-256 lock test STILL passes.

Splitting the migration into two commits gives clean rollback anchors AND verifies the wire-format-preservation invariant in isolation before the additive change.

### Static_assert offset locks

For load-bearing structs (Position, ShardedSnapshot, etc.), add `static_assert(offsetof(...) == expected_offset)` for each PERSIST field. Catches accidental field-reorder that would invalidate wire format. Critical when the struct is in a SHA-256-locked / HMAC-locked context.

### Sister pattern composition

This pattern composes with `phase-separated-drainer-for-safe-cross-temporal-derives.md` — phase discipline preserves source state through consumer passes; PERSIST_KIND column lets ephemeral capture fields (e.g., `exit_fill_price`) live on the same struct as the source they accompany (e.g., Position) without persistence-cost.

The two patterns together UNLOCK `aggressive-memory-reduction-techniques.md` Technique 4 (derive vs store) for previously-blocked cases. Each pattern alone is partial; combined, they close the broader "defensive snapshot due to transient source + persisted-struct extension cost" class.

### Anti-pattern: PERSIST_KIND in the wrong direction

Some implementations might be tempted to use a INCLUDE_IN_WIRE_FORMAT flag where PERSIST=true. Prefer the explicit two-state enum (PERSIST / SKIP_PERSIST) because:
- The token-paste dispatch is unambiguous
- Adding a third state (e.g., COMPRESSED, VERSIONED) is one column-value addition vs adding a parallel flag
- Code readers see the persist-kind at a glance

---

## Cross-references to CLAUDE.md

This pattern complements + reinforces:

- **Item 13 (X-macro registry pattern):** parent pattern; PERSIST_KIND is a tuple column for dispatch
- **Item 15 (parity-tested-by-construction):** wire-format byte preservation enforced via registry + filter
- **Item 19 (structural fix preferred):** structural answer to the "snapshot version bump every ephemeral coexistence" class
- **Item 21 (AUTOPOPULATE companion):** registry walks for init / reset / save / load — all generated from the same FOREACH

Promotion candidate to CLAUDE.md as item 32+ after 2+ canonical applications shipped (v5.15.5.C.3 Phase 3b's FOREACH_OMS_FIELD retroactively counts as first; v5.15.5.C.4 FOREACH_POSITION_FIELD is second).

---

## Related design patterns

- **`x-macro-registry-with-presence-dispatch.md`** — base X-macro pattern; this spec specializes with the PERSIST_KIND column
- **`heterogeneous-registry-pattern.md`** — SCOPE COLUMN form; PERSIST_KIND is the scope axis for wire-format participation
- **`wire-format-byte-preservation-discipline.md`** — sister; this pattern is the registry-driven enforcement of that discipline
- **`autopopulate-pattern-for-production-caller-class.md`** — companion AUTOPOPULATE for save/load + init/reset generation
- **`phase-separated-drainer-for-safe-cross-temporal-derives.md`** — sister structural enabler; phase discipline + persist-kind registry compose to unlock derive-from-source patterns
- **`aggressive-memory-reduction-techniques.md`** Technique 4 (derive vs store) — persist-kind registry expands the safe surface for Technique 4

---

**End of spec.**
