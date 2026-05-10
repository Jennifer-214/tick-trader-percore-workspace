# X-macro registry with presence dispatch for partial-mirror struct generation

**Established:** 2026-05-09 (v5.14.8.A.0.b + A.merged)
**Status:** ACTIVE
**Cross-references:**
- First application: `ML_Headers/StampBoundModelConstRegistry.hpp` (FOREACH_STAMP_BOUND_MODEL_CONST)
- Sister registry (simpler, no partial-mirror): `ML_Headers/StampBoundCfgRegistry.hpp` (FOREACH_STAMP_BOUND_CFG)
- Companion pattern: `bitmap-flag-api.md` (used for has_flags bit-packing)
- Closes: TECH_DEBT-006 (FoxML_Trader_v2)

---

## Problem statement

Some serializable / introspectable data has a **canonical wire format** (key=value lines on disk, or struct fields in a snapshot) that's read by multiple consumers, with each consumer needing a slightly different VIEW of the data:

- **Parser-side struct** sees ALL fields parsed from the wire format.
- **Emitter-side struct** sees ALL fields needed to produce the wire format.
- **Runtime-side struct** sees a SUBSET — only fields needed at runtime; other parsed fields are check-only at parse time and not propagated.

Manual approach: declare each struct independently, list fields per struct. Adding a new field requires N-site updates: parser struct + emit struct + runtime struct (if applicable) + parser branch + emitter line + production-caller populator + accessor sites.

This is the **N-site bug class** (CLAUDE.md item 13 in FoxML_Trader_v2 codebase). Recurrent symptoms: forgotten populator at production caller; runtime struct missing a field; parser/emitter drift on field ordering or naming.

The classic X-macro registry pattern (one row in a FOREACH macro generates parser + emitter + struct fields uniformly) doesn't directly handle the **partial-mirror** case where the runtime struct includes only a SUBSET of registered fields.

This pattern extends X-macro registries with **presence dispatch via token paste** to handle partial-mirror cleanly while keeping the "1 row per field" property.

---

## Design space explored

### Option A: Bitmask presence column

Tuple includes `presence` as a bitmask of (PARSER | EMIT | RUNTIME).
```cpp
X(name, group, STAMP_PRESENT_PARSER | STAMP_PRESENT_EMIT, type, ...)
```

**Rejected.** Preprocessor can't conditionally suppress macro expansion based on integer arithmetic. The bitmask is opaque to the X-macro expansion; you can't write `if constexpr ((presence) & STAMP_PRESENT_RUNTIME) { type name; }` because struct member declarations aren't `constexpr` expressions.

### Option B: Multiple sub-FOREACH macros (split by presence)

```cpp
#define FOREACH_REGISTRY_RUNTIME_INCLUDED(X) X(field1, ...) X(field2, ...) ...
#define FOREACH_REGISTRY_PARSER_ONLY(X)      X(field3, ...) ...
#define FOREACH_REGISTRY(X) \
    FOREACH_REGISTRY_RUNTIME_INCLUDED(X) \
    FOREACH_REGISTRY_PARSER_ONLY(X)
```

**Rejected (for wire-format-locked registries).** Splitting + concatenating changes the interleaved order. If the canonical wire format requires entries in a SPECIFIC interleaved order (because legacy emit order is HMAC-locked), splitting reorders them.

Acceptable for registries WITHOUT canonical-order constraints.

### Option C (chosen): Token-paste dispatch on presence column

Tuple includes `presence` as a TOKEN (not integer). Token paste dispatches to per-presence macros:

```cpp
#define X(name, group, presence, type, ...) \
    HANDLE_GEN_##presence(name, type)

#define HANDLE_GEN_INCLUDE(name, type)      type name;
#define HANDLE_GEN_SKIP_HANDLE(name, type)  /* expand to nothing */
```

Token paste resolves `HANDLE_GEN_##INCLUDE` → `HANDLE_GEN_INCLUDE` → `type name;`. Likewise for `SKIP_HANDLE` → empty.

Future presence categories (e.g., `PARSER_ONLY` if a field is parsed but not emitted): add ONE new `HANDLE_GEN_<MARKER>` macro definition; no per-entry edits.

**Wins:**
- Preserves canonical entry order in the main FOREACH.
- "1 row per field" property maintained (presence is just one column).
- Mechanically extensible (one macro per presence category).

### Y3 dispatch — the canonical name for this preprocessor mechanism

The token-paste dispatch above is called **Y3 dispatch** in v5.14.9+ docs (named after the recurring 3-axis "Y" pattern of registry / dispatcher / consumer that recurs across patterns). Y3 dispatch is the LOAD-BEARING mechanism for:

- **Presence dispatch** (parser/emitter/runtime mirror — this doc's primary use)
- **Storage class dispatch** (`HANDLE_GEN_BIT_FLAG` vs `HANDLE_GEN_COUNTER_U32` vs `HANDLE_GEN_PERCENT_U8` per FailureModeRegistry)
- **Emit source dispatch** (`HANDLE_STAMP_EMIT_DIRECT_FIELD` vs `HANDLE_STAMP_EMIT_BITMAP_BIT` per v5.14.9.F.2 stamp-bound bitmap-field migration)
- **Scope dispatch** (`HANDLE_GEN_PER_CORE` vs `HANDLE_GEN_ENGINE_WIDE` per FOREACH_SLOW_PATH_GATE)
- **Type dispatch via templated helpers** (`tt::stamp_parse_field<T>` — combines Y3 with C++17 if-constexpr per CLAUDE.md item 23)

**Y3 dispatch recipe:**

1. Tuple has a token-column (the dispatch axis), not integer.
2. Per-axis-value macro `HANDLE_GEN_<value>` defines what to emit at that axis-value.
3. The X-macro extractor uses `HANDLE_GEN_##axis(...)` — preprocessor token-paste resolves at expansion time.
4. Adding a new axis-value = 1 new `HANDLE_GEN_<value>` macro definition; no per-entry edits.

**Caveats:**

- **Y3 dispatch is NOT C++17 `if constexpr`.** In NON-template macro contexts, all branches of an `if constexpr` chain must be SYNTACTICALLY VALID for ALL types (char[N] strncpy + scalar cast both must compile). Y3 dispatch happens at preprocessor time → ONLY the chosen branch is emitted; other branches are discarded textually. Use Y3 when branches have INCOMPATIBLE syntax per type (char[N] vs scalar); use `if constexpr` in TEMPLATE contexts.
- See CLAUDE.md item 23 for templated-helper integration when both are needed (e.g., `tt::stamp_parse_field<T>` per registry entry).

### Emit source column extension (v5.14.9.F.2)

`FOREACH_STAMP_BOUND_CFG` extended its tuple with an `emit_source` column to support cfg-flag bitmap migration:

```cpp
// Tuple: X(NAME, ..., emit_source, ...)
//   emit_source = DIRECT_FIELD — value reads from cfg.X directly
//   emit_source = BITMAP_BIT   — value reads from BITMAP_IS_SET(cfg.X_flags, MASK_<NAME>) ? 1 : 0

#define HANDLE_STAMP_EMIT_DIRECT_FIELD(get_cfg) (get_cfg)
#define HANDLE_STAMP_EMIT_BITMAP_BIT(get_cfg)   ((get_cfg) ? 1 : 0)

#define EMIT_STAMP_BOUND_FIELD(name, ..., emit_source, ..., get_cfg) \
    inf.name = (decltype(inf.name))HANDLE_STAMP_EMIT_##emit_source(get_cfg)
```

The `? 1 : 0` normalization is critical for HMAC byte-equivalence: bool→int promotion may differ across compilers/architectures; explicit ternary forces `int 0` or `int 1` byte-for-byte across both branches. Without it, the bitmap-bit-extracted fields would emit different bytes than DIRECT_FIELD on some platforms → HMAC chain breaks.

See `wire-format-byte-preservation-discipline.md` for the byte-equivalence discipline; see `heterogeneous-registry-pattern.md` Hybrid Form 3 for the full integration.

---

## The pattern (concrete shape)

### Step 1: Registry tuple

```cpp
// X(name, group, presence, type, fmt, default_val, get_value_expr, emit_when, doc)
//
//   name           : canonical wire key (also struct field name post-Option-1
//                    unification)
//   group          : has_* group name, or "_" for standalone
//   presence       : token marker — INCLUDE / SKIP_HANDLE / etc.
//   type           : C++ type token (use array-typedef for char[N], e.g.
//                    `tt::stamp_str_65`; std::is_array_v detects at compile
//                    time for if-constexpr dispatch)
//   fmt            : printf format string ("%d", "%g", "%s", "%016lx", etc.)
//   default_val    : zero-init value (0 for numeric, "" for char arrays)
//   get_value_expr : expression at production-caller scope to extract value
//   emit_when      : boolean expression at production-caller scope; gates emit
//   doc            : short string explaining the field's purpose

#define FOREACH_REGISTRY(X)                                                     \
    X(canonical_field_a, group_x, INCLUDE,     int,    "%d",  0,                \
      src->field_a, src->has_group_x, "doc")                                    \
    X(canonical_field_b, group_x, SKIP_HANDLE, double, "%.6g", 0.0,             \
      src->field_b, src->has_group_x, "doc")                                    \
    X(canonical_field_c, _,       INCLUDE,     uint32_t, "%u", 0,               \
      src->field_c, src->has_canonical_field_c, "doc")                          \
    /* etc */
```

### Step 2: String-field type aliases (C++ array-typedef)

```cpp
namespace tt {
    using stamp_str_16 = char[16];
    using stamp_str_65 = char[65];
}
```

Single token (`tt::stamp_str_65`) usable as the X-macro `type` column. `std::is_array_v<tt::stamp_str_65>` returns true; `std::extent_v<tt::stamp_str_65>` returns 65 at compile time. Enables `if constexpr` dispatch in parser/AUTOPOPULATE.

### Step 3: Token-paste presence dispatch

```cpp
#define HANDLE_GEN_INCLUDE(name, type)      type name;
#define HANDLE_GEN_SKIP_HANDLE(name, type)  /* skip — parser-only */
// Future markers add one new HANDLE_GEN_<MARKER> macro.
```

### Step 4: Struct generation per consumer

```cpp
// Parser-side struct (all fields):
struct ParserResult {
    uint64_t has_flags;
    #define X(name, group, presence, type, fmt, def, get, when, doc) type name;
    FOREACH_REGISTRY(X)
    #undef X
};

// Emitter-side struct (all fields):
struct EmitterInputs {
    uint64_t has_flags;
    #define X(name, group, presence, type, fmt, def, get, when, doc) type name;
    FOREACH_REGISTRY(X)
    #undef X
};

// Runtime-side struct (presence-filtered):
struct RuntimeHandle {
    uint64_t has_flags;
    #define X(name, group, presence, type, fmt, def, get, when, doc) \
        HANDLE_GEN_##presence(name, type)
    FOREACH_REGISTRY(X)
    #undef X
    // Plus runtime-only fields (not from registry)
};
```

The dispatch macro applies ONLY to the runtime struct. Parser + emitter structs use the simpler `type name;` expansion (all entries included).

### Step 5: AUTOPOPULATE pattern (production-caller class extinction)

```cpp
// Token-paste dispatcher: which has_* to set per group.
#define AUTOPOPULATE_SET_HAS__(name)                  (inf).has_##name = 1
#define AUTOPOPULATE_SET_HAS_group_x(name)            (inf).has_group_x = 1
// One #define per group.

#define REGISTRY_AUTOPOPULATE_ONE(name, group, presence, type, fmt, def, get, when, doc) \
    if (when) {                                                                          \
        AUTOPOPULATE_SET_HAS_##group(name);                                              \
        if constexpr (std::is_array_v<type>) {                                           \
            strncpy((inf).name, (get), std::extent_v<type> - 1);                         \
            (inf).name[std::extent_v<type> - 1] = '\0';                                  \
        } else {                                                                         \
            (inf).name = (type)(get);                                                    \
        }                                                                                \
    }

#define REGISTRY_AUTOPOPULATE(inf, src) \
    do { \
        FOREACH_REGISTRY(REGISTRY_AUTOPOPULATE_ONE) \
    } while (0)
```

Production callers replace manual population blocks with one call:
```cpp
EmitterInputs inf{};
REGISTRY_AUTOPOPULATE(inf, source_state);
emit_to_wire(&inf);
```

### Step 6: Parser dispatch (registry-driven)

```cpp
// In parser body, walk wire-format key=value lines:
#define X(name, group, presence, type, fmt, def, get, when, doc) \
    else if (strcmp(key, #name) == 0) { \
        if constexpr (std::is_array_v<type>) { \
            strncpy(r.name, val, std::extent_v<type> - 1); \
            r.name[std::extent_v<type> - 1] = '\0'; \
        } else if constexpr (std::is_floating_point_v<type>) { \
            r.name = (type)tt::parse_double_fast(val); \
        } else if constexpr (std::is_unsigned_v<type>) { \
            r.name = (type)strtoull(val, nullptr, 10); \
        } else { \
            r.name = (type)atoi(val); \
        } \
        AUTOPOPULATE_SET_HAS_##group(name); /* mark presence on parser-side struct */ \
    }
FOREACH_REGISTRY(X)
#undef X
```

### Step 7: Emitter dispatch (registry-driven)

```cpp
// In emit body, walk registry and emit one snprintf line per entry:
#define X(name, group, presence, type, fmt, def, get, when, doc) \
    if (BITMAP_IS_SET(inf->has_flags, MASK_##group)) { \
        n += snprintf(buf + n, cap - n, #name "=" fmt "\n", inf->name); \
    }
FOREACH_REGISTRY(X)
#undef X
```

(Group has_* checked once per entry; for entries sharing a group, the check is redundant but compiler-eliminable. Wire format byte-for-byte matches manual emit semantics.)

### Step 8: Reusable bitmap accessors (alias to BITMAP_* API)

```cpp
#define REGISTRY_HAS(s, name)  BITMAP_IS_SET((s).has_flags, MASK_##name)
#define REGISTRY_SET(s, name)  BITMAP_SET((s).has_flags, MASK_##name)
#define REGISTRY_CLR(s, name)  BITMAP_CLR((s).has_flags, MASK_##name)
```

Callers: `if (REGISTRY_HAS(*m, group_x)) ...` instead of touching has_flags directly.

---

## Trade-offs + when to apply

### Apply when:
- Multiple consumers (parser, emitter, runtime, snapshot, etc.) share a canonical schema
- Adding a new field has been a recurrent bug class (forgotten populator, drift between consumers)
- Wire format is locked (HMAC-bound, JSON schema, etc.) — registry order must match emit order
- Some consumers need a SUBSET of fields (partial mirror)

### Skip when:
- Single-consumer struct (no need for registry abstraction)
- Wire format isn't locked (simpler split-into-sub-FOREACHes is fine)
- Field count is small (<5) and growth is bounded — manual is tractable
- All consumers see the same fields (no partial-mirror; basic X-macro registry suffices)

### Cost:
- ~280 LOC of registry header + dispatch macros for a 25-entry registry
- ~30 min per new presence category (one HANDLE_GEN_<MARKER> macro)
- Caller migration: mechanical find/replace from manual access to registry accessor (~5-15 files for medium-sized codebases)

### Win:
- Adding next field = 1 row in registry → all 4 sites auto-flow (parser, emitter, struct, populator)
- N-site bug class structurally extinct (compile-time enforcement; can't forget a site)
- Documentation co-located with data (each tuple's `doc` column)
- Future audit gates trivial (one place to verify completeness)

---

## Reference implementations

### First applied: FoxML_Trader_v2 v5.14.8.A.0.b + v5.14.8.A.merged

- Registry header: `ML_Headers/StampBoundModelConstRegistry.hpp`
- 25 entries (post-A.0.b); canonical stamp body fields
- 6 groups (inference_cfg, scaler, fees, xgb_hyperparams, grid_member_count_group, label_params) + 7 standalone entries
- 19 INCLUDE entries + 6 SKIP_HANDLE entries (parser-only)
- 2 presence categories: INCLUDE (default), SKIP_HANDLE (parser-only)
- Closes TECH_DEBT-006 + extinguishes v5.9.5b production-caller class for stamp body fields

### Sister registry (simpler, no partial-mirror): FOREACH_STAMP_BOUND_CFG

- `ML_Headers/StampBoundCfgRegistry.hpp` (v5.14.1.B.3)
- No presence column (8-col tuple); all entries on all consumers
- Has STAMP_CFG_AUTOPOPULATE companion (precedent for STAMP_MODEL_CONST_AUTOPOPULATE)

### Future application candidates

- `FOREACH_FAILURE_MODE` (v5.14.8.B): observability flags + counters; uses same presence + dispatch pattern with different markers (BIT_FLAG / COUNTER_U32 / PERCENT_U8 storage classes per entry)
- `FOREACH_PER_CORE_SNAP_FIELD` (TECH_DEBT-011): general visible-state PerCoreSnap fields
- `FOREACH_OMS_STATE` (TECH_DEBT-012): OrderManagerState fields

---

## Lessons / gotchas

### Compaction-degraded handoffs lose precision

Each design decision in the registry tuple shape (column order, dispatch logic, presence semantics) is easy to lose between sessions. Capture in DESIGN_SPECS + postmortem during the work, not after.

The v5.14.8.A.1 ship dropped 3 fields between training_poll_interval and xgb_hyperparams during registry data population — caught by post-handoff fresh `/parity-check`. Lesson: **always re-audit registry data completeness vs canonical emit order** as part of the sub-ship after registry data lands.

### The "STANDALONE list" anti-pattern

Initial v5.14.8.0 design had a separate `FOREACH_REGISTRY_STANDALONE(X)` macro listing short has_* names for entries with group="_". Maintained alongside the main FOREACH = 2-site update per addition.

**Final design dropped STANDALONE entirely.** Standalone entries' has_* names are mechanically derived from entry name (verbose like `has_inference_cfg_bandit_blend_ratio`, but unambiguous). 1-row addition; bug class extinct.

### `if constexpr` type dispatch must cover ALL types in the registry

Adding a new type (e.g., `int16_t`) to a registry entry without a corresponding `if constexpr` branch in AUTOPOPULATE / parser causes silent compilation but wrong runtime behavior (would fall through to the catch-all int branch). Test pattern: extensibility loop test asserts each entry's type compiles via the dispatch.

### Wire-format byte-for-byte preservation is fragile

Registry order must match emit order EXACTLY. Future PRs that add entries in the middle (rather than appending) break the HMAC chain. Mitigation:
- Snapshot test that hashes the canonical body output for a synthetic AUTOPOPULATE'd struct
- Locked hash value catches accidental reorder at CI time
- Round-trip HMAC test against a known v(N-1) stamp to verify load compatibility

### Adding a new group requires 2 sites

1. Add to `FOREACH_REGISTRY_GROUPS` (declares has_<group> bit)
2. Add to AUTOPOPULATE_SET_HAS_<group> dispatch macro (one #define line)

Bounded; co-located in same header. Build-time check catches drift via extensibility loop test.

---

## Patterns NOT used here (and why)

### Function-pointer dispatch tables (instead of macros)
Considered for parser/emitter dispatch. Rejected because struct field type isn't known at runtime — must be compile-time.

### Variadic template metaprogramming
Considered for type-driven dispatch. C++17 `if constexpr` + std::is_array_v achieves the same result with simpler readability + no instantiation surface area.

### Reflection (C++23+)
Would obviate this entire pattern. Not yet available; we'll revisit when C++26 reflection lands.

---

## Cross-references

- `bitmap-flag-api.md` — has_flags bit-packing (companion pattern; used for has_* storage)
- `autopopulate-pattern-for-production-caller-class.md` — STAMP_MODEL_CONST_AUTOPOPULATE specifically
- `wire-format-byte-preservation-discipline.md` — guards against future row-reorder breaking HMAC
- FoxML_Trader_v2 `DOCS/EASY_ADDITIONS_INVARIANTS.md` — registry pattern audited categories table
- FoxML_Trader_v2 `DOCS/RECURRING_BUG_PATTERNS.md` — N-site bug class catalog
- FoxML_Trader_v2 `CLAUDE.md` item 13 — X-macro registry as the standard pattern
- FoxML_Trader_v2 `CLAUDE.md` item 19 — structural fix preferred when bug class can recur
