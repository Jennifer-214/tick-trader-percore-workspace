---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-15
tags: [framework-discipline, structural-fix, pattern-codification]
surface: [registry]
sister_specs: [registry-coverage-ci-check-pattern.md, cross-walker-struct-field-uniqueness-discipline.md, universal-cfg-field-registry-pattern.md, sidecar-override-pattern-for-registry-auto-flows.md]
applies_at_skills: []
---

# Manual fields inventory pattern — documented exemptions for registry-driven struct generation

**Stage:** Stage 3 ACTIVE v1.0 (first canonical application landed at v5.15.5.F.4c.3 WIP2d-0.B; engine commit `4154009`)
**Promotes to:** stays Stage 3 ACTIVE; second canonical application at `.F.4d` extends pattern to global cfg surface (FOREACH_GLOBAL_CFG_FIELD + FOREACH_MANUAL_GLOBAL_FIELD)
**Tags:** structural-fix, registry-driven, framework-discipline, build-failing-CI; closes "manual-field-bypass" class; serves H17; Stage 2 (DRAFT); 0 applications until .F.4c.3
**Sister specs:** `per-instance-registry-pattern.md` (per-node registry framework that consumes this discipline's exemption inventory), `cfg-scope-discipline.md` (the scope decision discipline), `universal-cfg-field-registry-pattern.md` (parent pattern; this spec adds the EXEMPTION mechanism)
**Closes bug class:** parallel-array drift + manual-field-bypass (recurred at strategy + risk_pct cohort at WIP2c.1)

---

## Problem statement

When a registry-driven framework (e.g., `FOREACH_PER_CORE_CFG_FIELD` generating `PerCoreCfg<F>` fields via X-macro) becomes the canonical source-of-truth for struct fields, two failure modes emerge:

1. **Manual-field-bypass**: a contributor adds a field directly to the struct body, bypassing the registry. The field exists at runtime but no parser/save/render/stamp/drift auto-flows pick it up. Silent zombie field.

2. **Parallel-array drift**: a contributor adds `<type> name[16]` to the parent struct (alongside `cores[c].name` from the registry). Two sources of truth diverge over time; consumers may read the wrong one. Per cfg-scope-discipline § Anti-pattern 2 ("Per-instance fields in the global registry 'for convenience'") this is FORBIDDEN.

Both shapes recurred in this codebase: `core_strategies[16]` + `core_risk_pct[16]` parallel arrays survived WIP2c.1's classify-first work (the strategy row was never added to the registry; the risk_pct field was duplicated). Detection happened during WIP2d-0 audit; fix is to add the registry rows + structurally close the bypass class.

The structural fix is a **3-tier X-macro discipline + bidirectional CI cross-check + documented exemption inventory**:
- **Default path** — registry-driven (`FOREACH_PER_CORE_CFG_FIELD` with TYPE column as first row column post-WIP2d-0.B; single source of truth) — auto-flows to struct field via `EMIT_PER_CORE_CFG_STRUCT_FIELD` payload macro + parser, save, render, stamp, drift via the same registry's other consumers.
- **Exemption path A — parallel arrays** — explicit X-macro registry (`FOREACH_MANUAL_PER_CORE_FIELD`) — for fields awaiting framework support (e.g., KIND_STRING before .F.4e) or transitional during migration. ControllerConfig.hpp invokes `FOREACH_MANUAL_PER_CORE_FIELD(EMIT_MANUAL_PER_CORE_DECL)` to generate the declarations.
- **Exemption path B — runtime bitmap cluster** — meta-registry (`FOREACH_PER_CORE_DOMAIN_BITMAP`) per `meta-registry-pattern-for-codebase-registry-discipline.md`. Single 5-row table binds each FOREACH_<DOMAIN>_CFG_FLAG child registry to its bitmap storage field; drives struct field declarations + bitmap-overflow static_asserts auto-generation + future WIP2e bitmap-rebuild walker.
- **CI enforcement** — build-failing script cross-checks across all 3 X-macros + inventory bidirectionally. Stray manual declarations in PerCoreCfg<F> or ControllerConfig parallel-array shape outside X-macros = BUILD ERROR.
- **Inventory doc** — `MANUAL_FIELDS_INVENTORY.md` documents each exemption with type / rationale / migration_trigger / canonical_replacement (Section A = parallel arrays; Section B = runtime bitmap cluster references meta-registry rows).

After the primitive lands, manual-field-bypass and parallel-array drift are UNEXPRESSIBLE — every per-node field flows through one of the two X-macros.

## When to apply

Apply this primitive when:
- A registry-driven framework owns struct field declarations via X-macro generation
- Forward growth is expected (new fields will be added regularly)
- Bypass classes have recurred (or are foreseeable) — i.e., contributors could add fields outside the registry
- Some fields legitimately can't fit the registry yet (awaiting Kind support, transitional during migration, or genuinely manual exemptions)

Skip when:
- All struct fields are registry-driven AND no exemptions are needed AND the bypass class hasn't recurred (waiting for first occurrence; per CLAUDE.md item 19 recurrence-count discipline)
- Registry has <10 entries (framework overhead doesn't amortize)
- Field types are heterogeneous in ways that resist registry uniformity (use heterogeneous-registry-pattern.md instead)

## Pattern shape — concrete

### Layer 1 — Registry as struct source

```cpp
// CoreFrameworks/CfgFieldRegistry.hpp

// Default path: registry-driven per-core fields
#define FOREACH_PER_CORE_CFG_FIELD(X) \
    X(FPN<F>,    KIND_DOUBLE_PCT, take_profit_pct, "TP %%", "Trading", 0, DBL(...), ...) \
    X(uint32_t,  KIND_INT,        max_hold_ticks,  "...", ...) \
    X(uint8_t,   KIND_INT_ENUM,   strategy,        "Strategy", ...) \
    /* ... ~92 rows ... */

// Payload macro emits struct field per row:
#define EMIT_PER_CORE_CFG_STRUCT_FIELD(STORAGE_T, KIND_TOKEN, name, label, section, meta, \
                                        payload, tooltip, ...) \
    STORAGE_T name;
```

### Layer 2 — Manual fields exemption registry

```cpp
// Documented exemptions: parallel arrays awaiting framework support OR transitional
// during migration. Each row MUST have a MANUAL_FIELDS_INVENTORY.md entry.
#define FOREACH_MANUAL_PER_CORE_FIELD(X) \
    /* type,    name,                    suffix,  rationale (matches MANUAL_FIELDS_INVENTORY.md) */ \
    X(char,     core_model_dir,          "[64]",  "KIND_STRING cohort at .F.4e") \
    X(char,     core_model_path,         "[64]",  "KIND_STRING cohort at .F.4e") \
    X(char,     core_horizon_list,       "[256]", "KIND_STRING cohort at .F.4e") \
    X(char,     core_ensemble_blend_mode,"[16]",  "KIND_STRING cohort at .F.4e") \
    X(char,     core_disabled_horizons,  "[128]", "KIND_STRING cohort at .F.4e") \
    X(uint64_t, core_feature_mask,       "",      "KIND_HEX64 needed at .F.4e") \
    X(FPN<F>,   core_risk_pct,           "",      "TRANSITIONAL — cores[c].risk_pct authoritative; delete at WIP2g") \
    X(uint8_t,  core_strategies,         "",      "TRANSITIONAL — strategy now in PerCoreCfg<F>; delete at WIP2g")
```

### Layer 3 — Struct generation via X-macro

```cpp
// PerCoreCfg<F> struct body IS the X-macro expansion. No manual fields possible.
template <unsigned F>
struct alignas(64) PerCoreCfg {
    FOREACH_PER_CORE_CFG_FIELD(EMIT_PER_CORE_CFG_STRUCT_FIELD)
};

// Cache discipline preserved:
static_assert(sizeof(PerCoreCfg<64>) % 64 == 0,
              "PerCoreCfg<F> size cache-aligned");
static_assert(alignof(PerCoreCfg<64>) == 64,
              "PerCoreCfg<F> alignment cache-aligned");

// ControllerConfig<F> declares parallel arrays via X-macro expansion ONLY:
template <unsigned F>
struct ControllerConfig {
    // ... global fields ...
    PerCoreCfg<F> cores[MAX_EXECUTION_CORES];

    #define EMIT_MANUAL_PER_CORE_DECL(type, name, suffix, rationale) \
        type name[MAX_EXECUTION_CORES] suffix;
    FOREACH_MANUAL_PER_CORE_FIELD(EMIT_MANUAL_PER_CORE_DECL)
    #undef EMIT_MANUAL_PER_CORE_DECL
};
```

### Layer 4 — CI build-failing cross-check

`tools/check_per_core_registry_integrity.py` (or `.sh`; invoked from `build.sh` pre-compile):

1. **PerCoreCfg<F> bidirectional**: parse struct field declarations + registry rows; require exact match. Any field in struct without registry row → BUILD ERROR. Any registry row without struct field → BUILD ERROR (catches X-macro expansion bugs).

2. **Parallel array placement**: every `<type> core_<name>[(16|MAX_EXECUTION_CORES)]` in `ControllerConfig.hpp` MUST appear inside the `FOREACH_MANUAL_PER_CORE_FIELD` X-macro expansion (delimited region). Stray declarations → BUILD ERROR with diff suggesting registry migration.

3. **Inventory cross-check**: every `FOREACH_MANUAL_PER_CORE_FIELD` entry has a row in `MANUAL_FIELDS_INVENTORY.md`. Every inventory row has an X-macro entry. Missing in either direction → BUILD ERROR.

4. **Name duplication**: no name in `FOREACH_PER_CORE_CFG_FIELD` collides with a name in `FOREACH_MANUAL_PER_CORE_FIELD`. Collision → BUILD ERROR.

5. **Anti-pattern 1 consumer scan**: grep for `cfg.<X>` + `cfg.core_overrides[<c>].<X>` co-occurrence for same `X`. WARN at WIP2d-0 (still expressible during transition); becomes ERROR after WIP2f deletion when `core_overrides[16]` doesn't exist.

6. **Migration trigger sanity**: every TRANSITIONAL entry references a specific ship (e.g., "delete at WIP2g"). Prevents transitional exemptions from rotting into permanent. WARN on missing trigger; ERROR on triggers referencing already-shipped versions.

### Layer 5 — Inventory doc

`DOCS/MANUAL_FIELDS_INVENTORY.md`:

```markdown
# Manual fields inventory — exemptions from registry-driven struct generation

Every entry below MUST have a corresponding row in FOREACH_MANUAL_PER_CORE_FIELD.
CI cross-checks bidirectionally; missing in either source = build error.

| Field | Type | Array size | Rationale | Migration trigger | Canonical replacement |
|---|---|---|---|---|---|
| `core_model_dir` | `char[64]` | 16 | Per-core model directory paths | .F.4e KIND_STRING cohort | `FOREACH_PER_CORE_CFG_FIELD` row with KIND_STRING |
| `core_model_path` | `char[64]` | 16 | Legacy single-model path | .F.4e KIND_STRING cohort | Same |
| ... | | | | | |

Adding a new exemption: 1 row above + 1 row in FOREACH_MANUAL_PER_CORE_FIELD + commit-message justification.
Removing an exemption: confirm migration trigger fired; delete from both sources.
```

## Composition with other patterns

### With per-instance-registry-pattern.md

This pattern IS the exemption mechanism for `per-instance-registry-pattern.md`. The per-instance registry framework generates the default-path struct + descriptor + walker primitives; this pattern adds the exemption escape valve + structural enforcement.

### With universal-cfg-field-registry-pattern.md

This pattern is the H17 invariant's enforcement primitive. At `.F.4d`, H17 codifies "Cfg struct field declarations MUST come from `FOREACH_CFG_FIELD` via X-macro generation; manual cfg field declarations FORBIDDEN; runtime/derived state stays manual but documented in `MANUAL_FIELDS_INVENTORY.md`". The CI script + inventory doc are how the invariant is build-enforced.

### With wire-format-byte-preservation-discipline.md

When the struct is HMAC-signed wire format, the X-macro generation order = canonical emit order. Adding/removing fields shifts byte positions → Layer 5b hash test fires. The dual-X-macro discipline preserves this: registry-row order = field declaration order = canonical emit order.

### With sidecar-override-pattern-for-registry-auto-flows.md (.F.4d)

The sidecar override pattern handles CUSTOM-semantics overrides on standard auto-flow. This pattern is different — it handles fields that CAN'T fit the auto-flow YET (awaiting framework support) or are TRANSITIONAL during migration. Both compose: a registry-driven field can have a sidecar override for custom semantics; the inventory is for fields outside the registry entirely.

## Anti-patterns to avoid

### Anti-pattern 1: Adding to struct without registry/inventory

```cpp
// FORBIDDEN — bypasses both X-macros; CI catches at build
template <unsigned F>
struct alignas(64) PerCoreCfg {
    FOREACH_PER_CORE_CFG_FIELD(EMIT_PER_CORE_CFG_STRUCT_FIELD)
    FPN<F> sneaky_field;   // <-- CI BUILD ERROR
};
```

### Anti-pattern 2: Manual parallel array outside FOREACH_MANUAL_PER_CORE_FIELD

```cpp
// FORBIDDEN — CI catches via regex scan of ControllerConfig
template <unsigned F>
struct ControllerConfig {
    PerCoreCfg<F> cores[16];
    FPN<F> sneaky_per_core[16];   // <-- CI BUILD ERROR; declare in inventory instead
};
```

### Anti-pattern 3: Inventory entry without X-macro entry (or vice versa)

```cpp
// FOREACH_MANUAL_PER_CORE_FIELD has entry but MANUAL_FIELDS_INVENTORY.md doesn't:
// CI BUILD ERROR — bidirectional sync required.
```

### Anti-pattern 4: Permanent exemption (TRANSITIONAL never expires)

```cpp
// Inventory entry with TRANSITIONAL rationale but no migration trigger:
// CI WARN — trigger field missing.
// Trigger field referencing already-shipped version → ERROR.
```

### Anti-pattern 5: Name collision between registry + inventory

```cpp
// FOREACH_PER_CORE_CFG_FIELD has `risk_pct` row AND
// FOREACH_MANUAL_PER_CORE_FIELD has `core_risk_pct` (could be confused as same logical field):
// CI WARN (heuristic name-similarity); operator review at PR.
// HARD collision (same name in both) → BUILD ERROR.
```

## Reference implementations

(Populates at Stage 3 ACTIVE — shipped sites get file:line refs back-linked here.)

- (pending) `CoreFrameworks/CfgFieldRegistry.hpp` — `FOREACH_PER_CORE_CFG_FIELD` with TYPE column + `FOREACH_MANUAL_PER_CORE_FIELD` X-macro (post-`.F.4c.3` WIP2d-0)
- (pending) `CoreFrameworks/ControllerConfig.hpp` — `PerCoreCfg<F>` X-macro-generated struct + ControllerConfig parallel array X-macro emission
- (pending) `tools/check_per_core_registry_integrity.py` — CI cross-check script
- (pending) `DOCS/MANUAL_FIELDS_INVENTORY.md` — 8 documented exemptions at .F.4c.3 ship close

## Stage 3 promotion criteria

- At least 2 canonical applications shipped (per CLAUDE.md item 19 recurrence-count discipline for pattern promotion)
- First application: per-node surface at `.F.4c.3` (this ship)
- Second application: global cfg surface at `.F.4d` (FOREACH_GLOBAL_CFG_FIELD X-macro struct gen + FOREACH_MANUAL_GLOBAL_FIELD inventory; same primitive applied to global fields)
- After both applications land + Stage 3 promote: H17 codified as HARD invariant in DESIGN_PHILOSOPHY § 2 (currently STRONG at `.F.4c.3` per-core surface only)

## Cross-references

- `DESIGN_SPECS/framework-patterns/per-instance-registry-pattern.md` — the framework whose exemption mechanism this spec provides
- `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` § Anti-pattern 1+2 — the scope discipline this primitive enforces structurally
- `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md` — parent pattern; this spec adds the exemption + CI enforcement
- `DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md` — base X-macro pattern composed
- `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` — layer-5b hash test composes
- `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md` — meta-decision motivating this primitive (recurrence count ≥3 for manual-field-bypass after WIP2c.1's strategy + risk_pct misses)
- CLAUDE.md item 31 — framework discipline meta-principle (THIS pattern IS a framework primitive)
- CLAUDE.md item 19 — structural fix preferred (recurrence ≥3 → mandatory)
- DESIGN_PHILOSOPHY.md § 1.5 (framework discipline) + § 7 (structural-fix family) — WHY companion
- DESIGN_PHILOSOPHY.md § 2 H17 — pending invariant codification at `.F.4d` (STRONG → HARD); this spec is the enforcement primitive

---

**Stage 2 DRAFT v1.0 — committed 2026-05-15 ahead of v5.15.5.F.4c.3 WIP2d-0.** Promotes to Stage 3 ACTIVE v1.0 at ship close once per-core surface canonical application lands; second canonical application at `.F.4d` validates pattern across global cfg surface.
