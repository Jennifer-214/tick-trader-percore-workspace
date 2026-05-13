# PRE/POST registry split for canonical emit order preservation

**Established:** 2026-05-09 (v5.14.8.A.merged.4)
**Status:** ACTIVE
**Cross-references:**
- First application: FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG + _POST_CFG
- Companion: `x-macro-registry-with-presence-dispatch.md` (the base registry pattern this extends)
- Companion: `wire-format-byte-preservation-discipline.md` (the constraint this pattern serves)
- Closes: TECH_DEBT-006 fully (the original 4 fields entry called out + 2 sidecar-derived fields)

---

## Problem statement

A canonical wire format requires fields to emit in a SPECIFIC ORDER. When a registry-driven X-macro walk produces emit code for one set of fields, but ANOTHER REGISTRY's fields must emit BETWEEN them in the canonical order, the X-macro can't pause for the sister registry mid-walk.

Concrete example (FoxML_Trader_v2 v5.14.7 stamp body):
```
1. inference_cfg_* fields (5)            ← FOREACH_STAMP_BOUND_MODEL_CONST entries
2. inference_cfg_bandit_blend_ratio       ← same registry
3. inference_cfg_fee_rate_*               ← same registry
4. training_poll_interval                 ← same registry
5. ... (more entries)
6. xgb_train_nthread                      ← LAST entry of FOREACH_STAMP_BOUND_MODEL_CONST
7. ridge_within_horizon                   ← FOREACH_STAMP_BOUND_CFG (sister registry) starts
8. ridge_lambda                           ← sister registry
9. ... (sister entries)
10. gap_acceptable_threshold              ← LAST sister entry
11. expected_num_classes                  ← canonically ALSO model_const but emit-after-cfg
12. expected_role                         ← same
13. ... etc (overlay_hash, effective_hash)
```

Items 11-13 are conceptually architectural model-const fields (same domain as items 1-6) but EMIT POSITION places them AFTER FOREACH_STAMP_BOUND_CFG. A single FOREACH_STAMP_BOUND_MODEL_CONST walk emits items 1-6 OR items 11-13 — never both with the sister registry interleaved correctly.

If we put items 11-13 into the existing FOREACH, they'd emit at the END of MODEL_CONST walk (before sister cfg) → wire format diverges → HMAC chain breaks for legacy stamps.

---

## Design space explored

### Option A: Split FOREACH into _PRE and _POST halves (chosen)

Two sub-macros with the SAME tuple shape; emitter walks each at the right point:
```cpp
#define FOREACH_REGISTRY_PRE_CFG(X)  /* entries 1-6 */
#define FOREACH_REGISTRY_POST_CFG(X) /* entries 11-13 */
#define FOREACH_REGISTRY(X) \
    FOREACH_REGISTRY_PRE_CFG(X) \
    FOREACH_REGISTRY_POST_CFG(X)
```

Emit walks each half separately:
```cpp
FOREACH_REGISTRY_PRE_CFG(EMIT_X)   // entries 1-6
FOREACH_SISTER_REGISTRY(EMIT_X)    // entries 7-10
FOREACH_REGISTRY_POST_CFG(EMIT_X)  // entries 11-13
```

Struct generation + AUTOPOPULATE walk the union (FOREACH_REGISTRY = both halves combined):
```cpp
#define X(name, group, presence, type, fmt, ...) type name;
FOREACH_REGISTRY(X)  // ALL entries declared as struct fields
#undef X
```

### Option B: Marker column ("emit_phase" PRE/POST) on each entry

Single FOREACH; each entry has a `phase` token. Walks check phase and skip mismatching ones.

Rejected — more complex (requires phase-aware emit skip logic) without saving lines. Both halves end up explicit anyway.

### Option C: Two completely separate registries

A whole separate `FOREACH_LATE_REGISTRY(X)` with its own AUTOPOPULATE companion + masks + GROUPS macro.

Rejected — too much duplication. The two halves share the same tuple shape, type-dispatch, struct-generation logic, and bit-packing.

### Option D: Reorder the canonical wire format

Just put expected_* and overlay/effective_hash BEFORE FOREACH_STAMP_BOUND_CFG entries. One registry handles it all.

Rejected — wire format is locked (HMAC chain on legacy stamps; v5.14.7 emit order is the contract).

---

## The pattern (concrete shape)

### Step 1: Split the existing FOREACH macro

Rename existing `FOREACH_REGISTRY(X)` → `FOREACH_REGISTRY_PRE_CFG(X)` (or whatever phase comes FIRST).

Add `FOREACH_REGISTRY_POST_CFG(X)` (or whatever comes AFTER) with new entries.

Add union macro:
```cpp
#define FOREACH_REGISTRY(X) \
    FOREACH_REGISTRY_PRE_CFG(X) \
    FOREACH_REGISTRY_POST_CFG(X)
```

### Step 2: Bit allocation handles both halves

```cpp
enum HasFlagBit : uint64_t {
    // PRE_CFG section bits
    BIT_field_a = 0,
    BIT_field_b,
    // ... (PRE entries)
    
    // POST_CFG section bits (just continue numbering)
    BIT_field_y,
    BIT_field_z,
    // ... (POST entries)
    
    BIT_COUNT
};
```

Single bitmap; both halves contribute bits. No conceptual difference.

### Step 3: Struct generation walks the union

```cpp
struct ParserResult {
    uint64_t has_flags;
    #define X(name, group, presence, type, ...) type name;
    FOREACH_REGISTRY(X)  // declares fields from BOTH halves
    #undef X
};
```

Same for emit-side struct. Both structs include all fields from PRE_CFG + POST_CFG.

### Step 4: Emitter walks halves separately

```cpp
inline int emit_canonical_body(char* buf, ...) {
    int n = 0;
    
    // PRE_CFG entries (canonical positions 1-N)
    #define X(name, group, presence, type, fmt, def, get, when, doc) \
        if (has_check(group, name)) { \
            n += snprintf(buf + n, ..., #name "=" fmt "\n", inf->name); \
        }
    FOREACH_REGISTRY_PRE_CFG(X)
    #undef X
    
    // Sister registry (canonical positions N+1 to N+M)
    FOREACH_SISTER_REGISTRY(SISTER_EMIT_X)
    
    // POST_CFG entries (canonical positions N+M+1 onward)
    #define X(name, group, presence, type, fmt, def, get, when, doc) \
        if (has_check(group, name)) { \
            n += snprintf(buf + n, ..., #name "=" fmt "\n", inf->name); \
        }
    FOREACH_REGISTRY_POST_CFG(X)
    #undef X
    
    return n;
}
```

Each FOREACH walk produces emit lines in registry-row order. The interleaving matches canonical wire format byte-for-byte.

### Step 5: Parser walks union (order doesn't matter for parsing)

Parser sees the wire format key=value lines in some order; X-macro walk strcmp-dispatches to the right field. Order of entries in registry doesn't affect parse correctness:
```cpp
#define X(name, group, presence, type, fmt, def, get, when, doc) \
    else if (strcmp(key, #name) == 0) { \
        tt::parse_field(r.name, val); \
        STAMP_SET(r, name); \
    }
FOREACH_REGISTRY(X)  // walk both halves; order doesn't matter for parse
#undef X
```

### Step 6: AUTOPOPULATE walks union

Same as parser — population order doesn't affect emit (emit walks halves separately and reads from already-populated struct):
```cpp
#define AUTOPOPULATE(inf, src) \
    do { \
        FOREACH_REGISTRY(AUTOPOPULATE_ONE) \
    } while (0)
```

---

## Trade-offs + when to apply

### Apply when:
- Registry is X-macro-driven for emit + parse + struct generation
- Canonical wire format requires entries to emit in a SPECIFIC ORDER that interleaves with another registry
- The other registry can't easily be merged or reordered (sister registry; locked emit order)
- Splitting preserves all other registry properties (struct fields, has_flags bits, AUTOPOPULATE)

### Skip when:
- Wire format isn't locked — just reorder
- The "interleaved" position is at the END (no separation needed; just append)
- The two halves are conceptually different domains — make truly separate registries (no union helper)

### Cost:
- Rename existing macro (~5 min)
- Define new _POST_CFG / _PRE_CFG half (~10 min depending on entry count)
- Update emitter to walk halves separately (~5 min)
- Possibly add `_GROUPS` / `_STANDALONE` declarations per half if has_* discipline differs

### Win:
- All half-entries share the registry pattern (struct gen, AUTOPOPULATE, parser, has_flags bits)
- Future field addition = 1 row in PRE or POST; mechanical
- Wire format byte preservation maintained (HMAC chain unbroken)

---

## Reference implementations

### FoxML_Trader_v2 v5.14.8.A.merged.4

- Registry: `ML_Headers/StampBoundModelConstRegistry.hpp`
- PRE_CFG: 26 entries (inference_cfg, scaler, fees, xgb_hyperparams, etc.)
- POST_CFG: 6 entries (expected_num_classes, expected_role, expected_num_features, expected_feature_format_version, overlay_hash, effective_hash)
- Sister registry between halves: FOREACH_STAMP_BOUND_CFG (`ML_Headers/StampBoundCfgRegistry.hpp`)
- Closes TECH_DEBT-006

### Future application candidates

- FOREACH_RUN_HISTORY_COL (CSV writer columns) — if RunHistory ever has emit-order constraints relative to a sister registry
- FOREACH_PERSIST_FIELD (snapshot serialization) — if SHARDED_SNAPSHOT_VERSION emit order interleaves with sister snapshot fragments

Most registries WON'T need the split; emit order is internal to the registry. Only when a SISTER registry's emit must interleave does this pattern apply.

### Sibling pattern — registry projection via tuple-column filter (v5.15.5.C.3 Phase 3b)

When the wire-format-byte-preservation discipline (`wire-format-byte-preservation-discipline.md`) must be enforced WITHOUT inter-registry interleaving (i.e., the persisted subset is a contiguous projection of one registry), the PRE/POST split is unnecessary. Instead, use a per-entry `PERSIST_KIND` tuple column + `static_assert(FOREACH_OMS_FIELD_PERSIST_COUNT == N)` to lock wire byte count.

Canonical reference: `MemHeaders/OmsFieldRegistry.hpp` — `FOREACH_OMS_FIELD` walks all OMS fields; PERSIST_KIND column filters to the 10 fields that participate in snapshot v8. Wire format byte count locked structurally; adding a new field requires explicit PERSIST_KIND classification (compile-time enforcement that new fields don't accidentally pollute the wire format).

Choice rule: **PRE/POST split** when emit-order INTERLEAVES with sister registry; **projection** when the emitted subset is a CONTIGUOUS filter of one registry. Both serve the same wire-format-byte-preservation discipline via different X-macro mechanisms.

---

## Lessons / gotchas

### Half-specific dispatchers may differ

If PRE_CFG has has_<group> dispatch but POST_CFG entries are all standalone (group="_"), the parser X-macro for POST_CFG might use a simpler `STAMP_SET(target, name)` directly vs PRE_CFG's `STAMP_AUTOPOPULATE_SET_HAS_##group(name)` token-paste dispatch.

Document the per-half dispatch convention if it differs.

### `if constexpr` cast issue in non-template macros

When the registry includes mixed types (char[N] strings + scalars), the parser X-macro's `if constexpr` branches must avoid syntactically-invalid casts in non-taken branches. The fix: extract type dispatch into a templated helper function (`stamp_parse_field<T>`) that's instantiated per-T. Each instantiation properly discards branches.

This is required ANY TIME a non-template context uses `if constexpr` with branches that have different syntax requirements per type.

### Bit allocation discipline across halves

Single `enum HasFlagBit` covers both halves. Adding new POST_CFG entry = add to enum + add MASK_<name> + add to FOREACH_POST_CFG. Same as PRE_CFG addition; no fork between halves' bit allocation.

### Tests don't typically need to know about the split

Tests check emit/parse round-trip + struct field presence. Both halves contribute to the same canonical body output and the same struct fields. Tests are split-agnostic.

### When to migrate manual fields → POST_CFG

Apply when:
- Manual fields use the Surface G `has_*` discipline (forward-compat flag)
- Type fits the registry type-dispatch (int/uint/double/char[N])
- Emit-time has_* gating semantics match (caller pre-sets has_*; emitter checks; populates conditionally)

The migration is mechanical: move manual fields to POST_CFG entries, remove manual struct field declarations + manual emit/parse blocks.

---

## Patterns NOT used here (and why)

### Compile-time concatenation of FOREACH macros via `__VA_ARGS__`

C preprocessor supports variadic macros but doesn't have a clean way to concatenate two FOREACH expansions into a flat list while preserving order. The literal concatenation we use (`FOREACH_PRE_CFG(X) FOREACH_POST_CFG(X)` in the union) IS the simplest solution.

### Phase-aware filter via dispatch

Considered using a `phase` column with `EMIT_IF_PRE(name)` / `EMIT_IF_POST(name)` macros. Rejected because the split-into-halves approach is cleaner — no per-entry phase column overhead.

---

## Cross-references

- `x-macro-registry-with-presence-dispatch.md` — the base registry pattern; this extends it
- `wire-format-byte-preservation-discipline.md` — the constraint this pattern serves
- `bitmap-flag-api.md` — has_flags storage backend (single bitmap covers both halves)
- FoxML_Trader_v2 `DOCS/TECH_DEBT.md` TECH_DEBT-006 — fully closed by this pattern's first application
