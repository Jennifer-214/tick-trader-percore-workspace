---
type: framework-pattern
stage: 3-first-canonical
version: 1.1
established: 2026-05-14
tags: [framework-discipline, pattern-codification, doc-discipline]
surface: [registry, cfg-flow, wire-format]
sister_specs: [universal-cfg-field-registry-pattern.md, metadata-bit-driven-derived-filter-framework.md, sidecar-override-pattern-for-registry-auto-flows.md, cfg-derived-consumer-framework.md, meta-registry-pattern-for-codebase-registry-discipline.md]
applies_at_skills: []
---

# Framework composition overview — cfg infrastructure at v5.15.5.F.4d

**Established:** 2026-05-14 (v5.15.5.F.4d planning); **v1.1 Path γ correction in progress at v5.15.5.F.4d.1.A planning 2026-05-16**
**Status:** **v1.1 Path γ correction in progress (2026-05-16)** — Stage 3 ACTIVE promotion at `.F.4d` ship close was ASPIRATIONAL; the DERIVED_FILTER framework component was not actually built (only the metadata bit was reserved). v1.0 topology diagram + composition tables describe a parallel walker mechanism that doesn't match the codebase. The **actual** canonical mechanism uses existing `FOREACH_METADATA_BIT` + `cfg_compute_mask` + `CFG_FIELD_FOR_EACH_SET_BIT` infrastructure at `CfgFieldRegistry.hpp:1020-1159` (since `.F.4c.3`). Plus 3 canonical composed-filter masks at `:1162-1257` (`render_mask` / `save_mask` / `cli_explain_mask`). Full topology + table updates land at `.F.4d.1.A` ship close. See `plans/v5.15-live-readiness/plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` for Path γ rationale + sister patterns (`composed-filter-mask-pattern.md` + `wire-format-canonical-body-invariants-helper.md`). Topology + per-framework brief tables below are v1.0 SUPERSEDED text pending rewrite at `.A` ship close.
**Tags:** framework-discipline, discoverability; serves H15 + H16 + H17 + H18 + H19; v1.1 Path γ correction in progress; 1 composition application planned (.F.4d.1.A using corrected Option E mechanism)

**Cross-references:**
- Composes: `universal-cfg-field-registry-pattern.md` (parent universal cfg registry)
- Composes: `type-trait-dispatch-via-tt-namespace.md` (parse / save / render trio)
- Composes: `metadata-bit-driven-derived-filter-framework.md` (derived filters over FOREACH_CFG_FIELD)
- Composes: `sidecar-override-pattern-for-registry-auto-flows.md` (custom-semantics overrides)
- Composes: `meta-registry-pattern-for-codebase-registry-discipline.md` (FOREACH_REGISTRY codebase-wide roster)
- Composes: `wire-format-byte-preservation-discipline.md` (Layer 2 locale pinning + Layer 5b hash lock)
- Composes: `multi-bit-state-encoding-pattern.md` (bit-packed framework structs)
- Composes: `autopopulate-pattern-for-production-caller-class.md` (consumer-side mechanical)
- Composes: `categorical-tag-applicability-pattern.md` (applies_to_*_cat dimension)
- CLAUDE.md item 31 (Framework-driven extensibility — meta-principle)

---

## Purpose

The v5.15.5.F.4d cfg infrastructure ship composes ~6 documented frameworks into one cohesive cfg discipline stack. This doc visualizes how they connect — useful for **cold-pickup orientation** + **audit-gate framework-completeness verification** + **future cohort migration sequencing**.

Each framework handles ONE concern; together they extinguish 5 bug classes (Class 14, 18, 19, 21, 23) + serve 5 hard invariants (H9, H15-H19 + H18 STRONG-pending) + scale to 7+ future derived filter applications + 6+ future sidecar applications + ~20+ existing X-macro registries.

---

## Composition topology

```
+============================================================================+
|                  Level 2 (codebase-wide ROOT_META)                          |
|                                                                             |
|        FOREACH_REGISTRY  ← meta-registry-pattern-for-codebase-registry-     |
|         (RegistryRoster.hpp)        discipline.md                           |
|         15-22 initial rows                                                  |
|         (TECH_DEBT-057: migrate ~15 remaining)                              |
|         CI: H15 (every registry has a row) + H19 (LEVEL>0 has PARENT)       |
|                                                                             |
+======================+======================================================+
                       |
       +---------------+---------------+
       |                               |
       v                               v (managed-by ROOT)
+======================+   +==========================================+
| Level 1 (META):       |   | Level 0 (concrete registries; ~15+):     |
|                       |   |                                          |
| FOREACH_DERIVED_      |   | STRATEGY, FEATURE, REGIME, FAILURE_MODE, |
|   FILTER              |   | CFG_DRIFT_CHECK*, ARCH_FIELD_DRIFT,      |
|  (DerivedFilter       |   | OMS_FIELD, SLOW_PATH_GATE,               |
|   Roster.hpp)         |   | 5 × FOREACH_*_CFG_FLAG (LIFECYCLE/GATE/  |
|                       |   |    ML/RISK/OPS bitmap registries),       |
| 7 cfg-derived filters |   | STAMP_BOUND_MODEL_CONST_PRE/_POST,       |
| (STAMP_BOUND_DERIVED, |   | BANDIT_ALGORITHM, BARRIER_BLEND_MODE,    |
|  IS_SECRET_DERIVED,   |   | DEGRADATION_CURVE, ... etc.              |
|  HIDDEN_BY_DEFAULT_   |   |                                          |
|    DERIVED, etc.)     |   | *CFG_DRIFT_CHECK wide variant            |
|                       |   |  superseded by sidecar pattern post-     |
| ← metadata-bit-       |   |  .F.4d ship (TECH_DEBT-059)              |
|   driven-derived-     |   +==========================================+
|   filter-framework.md |
|                       |
|   CI: H16 (every      |
|   metadata bit has a  |
|   derived filter or   |
|   documented exempt)  |
+========+==============+
         |
         v (consumes from)
+============================================================================+
|              FOREACH_CFG_FIELD (Level 0 — the universal cfg                 |
|              source of truth)                                              |
|              CoreFrameworks/CfgFieldRegistry.hpp                           |
|              ~213 cfg fields × 12-col Option D tuple                       |
|                                                                             |
|  ← universal-cfg-field-registry-pattern.md                                  |
|  ← registry-tuple-as-single-source-of-truth.md                              |
|  ← categorical-tag-applicability-pattern.md                                 |
|                                                                             |
|  CI: T4 (every row has non-zero applies_to_strategy_cat)                    |
|  H17: cfg struct fields generated from this via X-macro                     |
|                                                                             |
|  Schema LOCKED at .F.4b (Kind enum extended within reserved slots 7-9       |
|   at .F.4d for storage-width tokens; no struct layout change)              |
+================+============================================================+
                 |
        +--------+--------+----------+--------+----------+
        |        |        |          |        |          |
        v        v        v          v        v          v
   +--------+ +-----+ +------+ +-----+  +------+  +-----------+
   | tt::   | | tt::| | tt:: | |X-mac|  |Per-  |  | Sidecar   |
   | cfg_   | |cfg_ | |cfg_  | |ro   |  |core  |  | overrides |
   | parse_ | |save_| |render| |strct|  |over- |  |(FOREACH_  |
   | field  | |field| |_field| |gen  |  |ride  |  | DRIFT_    |
   |  <T>   | | <T> | | <T>  | |     |  |emit  |  |  OVERRIDE)|
   +---+----+ +--+--+ +--+---+ +--+--+  +--+---+  +-----+-----+
       |         |       |        |         |           |
       v         v       v        v         v           v
   Parser   File save  GUI    Cfg struct  Per-core    Custom-
   inline   path-       60Hz   fields     override    semantics
   in       splice;     render; auto-     storage     drift rows
   Control- locale-     ImGui;  generated  emit       (5 of 19)
   ler-     pinned     tooltip from         when      via sidecar
   Config_  per Layer- byte-   metadata    PER_CORE_  pattern
   Load<F>  2          identi- bits        OK bit
   at line  (wire-     ty                  set
   ~1798    format-    discip-
            byte-      line
            preserv-   test
            ation-     (.F.4c
            discipline +)
            .md)
   ↑          ↑           ↑          ↑           ↑           ↑
   |          |           |          |           |           |
   tt-namespace-dispatch ──┘          |           |           |
   (3 sisters; 3-barrier              |           |           |
    Class 23 prevention)              |           |           |
                                      |           |           |
   X-macro registry-with-presence-dispatch ────────┘           |
   (Y3 token-paste dispatch on Kind enum)                      |
                                                               |
   autopopulate-pattern-for-production-caller-class.md ────────┘
   (sidecar override + AUTOPOPULATE for consumer drift checks)

+============================================================================+
|        Wire-format chain (Layer 2 + Layer 5b)                              |
|                                                                             |
|  Layer 2 (locale pinning)  ←─ shipped at .F.4b in tt::cfg_save_field<T>    |
|     uselocale(LC_NUMERIC=C) per-thread                                     |
|                                                                             |
|  Layer 5b (canonical body snapshot hash lock) ←─ shipped at .F.4d         |
|     LOCKED_STAMP_BOUND_DERIVED_HASH_V5_15_5_F4D constant                    |
|     fires on accidental row reorder; CHANGELOG-locked intentional change   |
|                                                                             |
|  Layer 4 (round-trip HMAC vs v5.14 fixture) ←─ commits at .F.4d           |
|     tests/fixtures/v5_14_stamp_canonical.bin                               |
|                                                                             |
|  ← wire-format-byte-preservation-discipline.md (full 6-layer defense)       |
+============================================================================+

+============================================================================+
|        Bit-packed framework structs (multi-bit state encoding)             |
|                                                                             |
|  DriftOverride          (8 bytes; flags + eps_idx + padding)               |
|  RegistryRosterEntry    (40 bytes; flags packs LEVEL + WIRE_KIND)          |
|  ManualFieldInventoryEntry (16 bytes; kind packed)                          |
|                                                                             |
|  ← multi-bit-state-encoding-pattern.md (CLAUDE.md item 30 → INVARIANT      |
|    promotion at .F.4d with 3 canonical applications)                       |
|  ← bitmap-flag-api.md (BITMAP_* accessors)                                  |
+============================================================================+
```

---

## Per-framework brief + role at `.F.4d`

| Framework | Role | DESIGN_SPEC |
|---|---|---|
| **Universal cfg field registry** | `FOREACH_CFG_FIELD` is single source of truth for all ~213 cfg fields; 12-col Option D tuple. Parent registry. | `universal-cfg-field-registry-pattern.md` |
| **`tt::` type-trait dispatch** | 3-sister trio (`tt::cfg_parse_field<T>` + `tt::cfg_save_field<T>` + `tt::cfg_render_field<T>`); 3-barrier Class 23 prevention; destination-by-reference + T-deduced. Parser / save / render handle integer + FPN_Binary + array + string types uniformly. | `type-trait-dispatch-via-tt-namespace.md` |
| **Metadata-bit-driven derived filter framework** | `FOREACH_DERIVED_FILTER` (Level-1 meta-registry); 3 variants (GUI-only / wire-format / wire-format-two-source); STAMP_BOUND first canonical application; Layer 5b hash lock for wire-format variants. | `metadata-bit-driven-derived-filter-framework.md` |
| **Sidecar override pattern** | `FOREACH_DRIFT_OVERRIDE` sidecar over FOREACH_CFG_FIELD STAMP_BOUND derived filter; standard cases via AUTOPOPULATE + custom cases via 8-byte bit-packed override entries indexed by FIELD_IDX. Replaces wide-variant CfgDriftCheckRegistry. | `sidecar-override-pattern-for-registry-auto-flows.md` |
| **Meta-registry-of-registries** | `FOREACH_REGISTRY` (Level-2 codebase-wide); LEVEL/PARENT tuple encodes topology; CI cross-check for H15 + H19. | `meta-registry-pattern-for-codebase-registry-discipline.md` |
| **X-macro struct generation** | `FOREACH_CFG_FIELD` generates `ControllerConfig<F>` struct field declarations directly; manual cfg struct fields FORBIDDEN; runtime/derived state stays manual in `MANUAL_FIELDS_INVENTORY.md`. | (sub-pattern of `universal-cfg-field-registry-pattern.md` § Reverse-drift) |
| **Wire-format byte preservation** | Layer 2 locale pinning + Layer 5b hash lock + Layer 4 round-trip HMAC vs v5.14 fixture. STAMP_BOUND derived filter ships Layer 5b first canonical application. | `wire-format-byte-preservation-discipline.md` |
| **Multi-bit state encoding** | DriftOverride / RegistryRosterEntry / ManualFieldInventoryEntry bit-packed; CLAUDE.md item 30 promoted to INVARIANT at `.F.4d` with 3 canonical applications. | `multi-bit-state-encoding-pattern.md` |
| **AUTOPOPULATE companion** | `CFG_DRIFT_AUTOPOPULATE` walks STAMP_BOUND derived filter + dispatches via sidecar; replaces manual CfgDriftCheckRegistry walker; 12+ consumer-site migration. | `autopopulate-pattern-for-production-caller-class.md` |
| **Categorical applicability** | `applies_to_strategy_cat / op_mode_cat / regime_cat / risk_cat` masks per cfg field; CI Test 2 (every row has non-zero strategy mask) + T13 (extended for op_mode/regime/risk). | `categorical-tag-applicability-pattern.md` |

---

## Composition flow at runtime (per consumer)

### Parser path (boot)

1. `ControllerConfig_Load<F>(filepath)` opens cfg file
2. Per `key=value` line: registry walks `EMIT_CFG_PARSER_CASE(...)` macro expansion
3. Each row dispatches `tt::cfg_parse_field<T>(cfg.<field_name>, desc, val)` — T deduced
4. tt:: branches on type traits: FPN_Binary / float / array / unsigned int / signed int
5. INT_ENUM rows also branch on `desc.kind == KIND_INT_ENUM` for string-token reverse-lookup + range-clamp
6. Cfg struct fields auto-populated; manual parser branches deleted post-`.F.4d`

### Save path (operator-triggered)

1. SettingsPanel detects cfg-dirty + operator saves
2. Per registry row: `tt::cfg_save_field<T>(cfg.<field_name>, desc, buf, sizeof(buf))` — locale-pinned per Layer 2
3. `cfg_write_field(path, key, buf)` text-splices into cfg file (comment-preserving)
4. Manual `cfg_write_field` invocations for migrated fields deleted post-`.F.4d`

### GUI render path (60 Hz)

1. SettingsPanel `EMIT_PANEL_RENDER` walk over FOREACH_CFG_FIELD
2. Per row: `tt::cfg_render_field<T>(cfg.<field_name>, desc)` — returns true if operator-changed
3. tt:: branches on type + Kind for ImGui dispatch (SliderFloat / Combo / Checkbox / InputText / SliderInt)
4. Tooltip rendered from `desc.tooltip` via ImGui::SetTooltip
5. Tooltip byte-identity discipline test fires at boot (`LOCKED_TOOLTIP_SNAPSHOT_HASH_V5_15_5_F4c`)

### Drift check path (model load)

1. `CoreModelZoo_ValidateAgainstCfg` invokes `CFG_DRIFT_AUTOPOPULATE(failure_flags, *handle, cfg)`
2. AUTOPOPULATE walks STAMP_BOUND_CFG derived filter (per `metadata_bit_driven_derived_filter_framework.md`)
3. Per row: lookup `g_drift_overrides[FIELD_IDX_<name>]` (branchless O(1) array access)
4. If `has_override`: use sidecar override values (severity / category / compare_kind / eps)
5. Else: use default values (REFUSE_STRICT + INFERENCE_CFG + EPS_DEFAULT)
6. Compare `stamp.<field>` vs `cfg.<field>` via `tt::cfg_drift_compare<T>` (type-dispatched epsilon)
7. On drift: `BITMAP_SET(failure_flags, FAILURE_MASK_cfg_<category>_drift)`
8. Wide-variant CfgDriftCheckRegistry manual walker DELETED post-`.F.4d` (TECH_DEBT-059)

### Stamp body emit path (training-time)

1. `stamp_write_for_model(...)` invoked at training completion
2. Locale-pinned canonical body construction (Layer 2 per `wire-format-byte-preservation-discipline.md`)
3. STAMP_BOUND_CFG derived filter walks FOREACH_CFG_FIELD (filter by STAMP_BOUND bit) + FOREACH_ML_CFG_FLAG (filter by STAMP_BOUND bit on flag) — two-source aggregation per derived filter framework variant 3
4. Per row: emit `field_name=value\n` via `tt::cfg_save_field<T>` with locale-pinned snprintf
5. Bitmap-bool rows use `HANDLE_STAMP_EMIT_BITMAP_BIT` `(get_cfg) ? 1 : 0` ternary normalization (per v5.14.9.F.2)
6. SHA-256 hash over canonical body bytes
7. HMAC sign with held-out secret
8. Write `.stamp` file
9. Layer 5b test verifies `LOCKED_STAMP_BOUND_DERIVED_HASH_V5_15_5_F4D` matches; fires on accidental reorder

---

## Composition flow for ADDING new content post-`.F.4d`

### Adding a new cfg field (non-STAMP_BOUND, KIND_INT/_BOOL)

1. **One row** in `FOREACH_CFG_FIELD` with chosen Kind + metadata + categorical applicability
2. Auto-flow:
   - Cfg struct field auto-generated (H17 via X-macro struct gen)
   - Parser walks the new row (no manual parser edit)
   - Save walks the new row (no manual save edit)
   - GUI renders the new row (no manual field_defs[] edit)
   - Per-node override storage auto-emits if PER_CORE_OK bit set
   - Tooltip locked in tooltip snapshot hash (must run test + update hash if intentional change)
3. **Net cost: 1 row + intentional tooltip hash update if applicable.**

### Adding a new STAMP_BOUND cfg field

Same as above, **plus**:
4. STAMP_BOUND derived filter auto-includes the new field (no manual derived filter edit)
5. CFG_DRIFT_AUTOPOPULATE auto-includes the new field with default severity (REFUSE_STRICT + INFERENCE_CFG)
6. If custom drift semantics needed: 1 row in `FOREACH_DRIFT_OVERRIDE` sidecar
7. Layer 5b hash test fires on the new row's effect → recompute hash → update LOCKED constant → CHANGELOG note
8. **Net cost: 1 row in parent registry + (optional) 1 row in sidecar + Layer 5b hash update.**

### Adding a new derived filter (new cohort over a new metadata bit)

1. New metadata bit in `MetadataFlag` enum (within 6-bit headroom; per `bitmap-overflow-protection-discipline.md`)
2. **One row** in `FOREACH_DERIVED_FILTER` declaring NAME + variant + source + metadata bit
3. Add to `FOREACH_REGISTRY` (1 row at Level 0 with PARENT=DERIVED_FILTER)
4. Tag relevant cfg fields with the new bit via `FOREACH_CFG_FIELD` row edits
5. (Wire-format variant only) Commit LOCKED hash + fixture + round-trip HMAC test
6. **Net cost: 1 metadata bit + 1 row in FOREACH_DERIVED_FILTER + 1 row in FOREACH_REGISTRY + N row edits in FOREACH_CFG_FIELD for cohort + (wire-format variant) Layer 5b setup.**

### Adding a new X-macro registry

1. Write the registry per existing patterns (`x-macro-registry-with-presence-dispatch.md`)
2. **One row** in `FOREACH_REGISTRY` declaring NAME + LEVEL + PARENT + design_spec + tags
3. If managed by an existing Level-1 meta-registry: PARENT = meta-registry name
4. CI test verifies H15 (registry has a row) + H19 (parent exists)
5. **Net cost: registry body + 1 row in FOREACH_REGISTRY.**

---

## Anti-patterns this composition prevents

| Anti-pattern | Bug class | Prevention mechanism |
|---|---|---|
| Plan body references fictional API | Class 14 | Pre-coding audit gate + DELETE-stale-don't-preserve-with-notice lesson |
| Two parallel cfg parsers / GUI renderers / save paths | Class 18 | tt:: trio + AUTOPOPULATE; single source of truth |
| Mirror-incomplete enum label arrays | Class 18 | X_GEN_LABEL extern reuse |
| Hardcoded enum names in applicability gating | Class 19 | categorical-tag-applicability-pattern (bitmap masks) |
| Multiple parallel descriptors for cfg fields | Class 21 | universal-cfg-field-registry-pattern (single descriptor + lives_in_struct) |
| Parallel wide-variant registries for drift / rendering / etc. | Class 21 | sidecar-override-pattern (custom-semantics via small sidecar; no parallel registries) |
| Type-erased reinterpret_cast through char*+offset | Class 23 | tt:: 3-barrier dispatch (no void*+offset API; X-macro extractor chokepoint; compile-time type-family static_assert) |
| Adding metadata bit but forgetting derived filter | (NEW potential class; pre-emptively closed) | H16 CI cross-check (FOREACH_DERIVED_FILTER coverage of MetadataFlag enum values) |
| Adding X-macro registry but forgetting documentation | (NEW potential class; pre-emptively closed) | H15 CI cross-check (FOREACH_REGISTRY coverage of all FOREACH_* in codebase) |

---

## Composition cost at `.F.4d` ship

| Component | LOC |
|---|---|
| Universal cfg registry foundation (shipped at `.F.4b`) | (already shipped) |
| tt:: dispatch trio (parse + save shipped at `.F.4b`; render at `.F.4c`) | (foundation already done) |
| Derived filter framework + roster | ~220 |
| Sidecar override pattern + DriftOverride struct + AUTOPOPULATE | ~150 |
| Meta-registry of registries + RegistryRoster + CI test | ~270 |
| X-macro struct generation + cfg field audit | ~430 (incl 113-row migration) |
| Layer 5b hash lock + v5.14 fixture commit | ~80 |
| Cohort migration (14 fields + 4 bitmap-bools) | ~150 |
| 12+ consumer-site migration via AUTOPOPULATE | ~80 |
| CFG_DRIFT_AUTOPOPULATE | ~80 |
| Bit-packed framework structs + branchless dispatch | ~80 |
| 4 new DESIGN_SPECs (this composition overview + 3 component specs) | ~600 |
| TECH_DEBT entries + recurrence notes + invariant codifications | ~50 |
| Tests + verification gates | ~150 |
| **TOTAL** | **~1500 LOC code + ~600 LOC specs + ~400 LOC docs + ~3 hr cfg field audit** |

---

## Pattern lifecycle composition

| Pattern | Stage at `.F.4d` ship | Promotion at `.F.4e` ship |
|---|---|---|
| Universal cfg registry | Stage 5 (CLAUDE.md item 13 + many applications) | (already at Stage 5+) |
| tt:: type-trait dispatch | Stage 5 (CLAUDE.md item 23) → 3 sister applications | Stage 5+ |
| Derived filter framework | Stage 2 (DRAFT) → Stage 3 (first reference at `.F.4d`) | Stage 4 (5 GUI applications validate at `.F.4e`) → Stage 5 |
| Sidecar override pattern | Stage 2 (DRAFT) → Stage 3 (first reference at `.F.4d`) | Stage 4 (when 2nd application emerges; v5.16+) |
| Meta-registry of registries | Stage 2 (DRAFT) → Stage 3 (first reference at `.F.4d`) | Stage 4 (TECH_DEBT-057 migration completes Stage 4) |
| Multi-bit state encoding | Stage 5 (CLAUDE.md item 30 + 2 applications) → 3rd application at `.F.4d` → INVARIANT promotion | INVARIANT |
| Framework composition (this doc) | Stage 2 (DRAFT) → Stage 3 (first reference at `.F.4d`) | Stage 4 (validation via `.F.4e` second-source applications) |

---

## How to read this doc

- **Cold-pickup orientation:** read the topology diagram + per-framework brief table; ground knowledge of which framework handles which concern
- **Audit-gate framework-completeness verification:** check the "Composition flow for ADDING new content" sections + verify each framework is in scope when ADDING the relevant content type
- **Future cohort migration sequencing:** read the pattern-lifecycle table + identify which patterns are at which stage; sequence migrations to advance multiple patterns toward Stage 5 codification

This doc is the **map**. Each framework's own DESIGN_SPEC is the **detailed reference**.

---

## Cross-references

All specs referenced in the topology + role tables above. Also:
- `pattern-codification-lifecycle.md` — 7-stage lifecycle this composition advances
- `audit-driven-pre-coding-gate.md` — `/precoding-audit-gate` Stage 1 auto-derives focus from this composition's framework keywords
- `DOCS/DESIGN_PHILOSOPHY.md` § 1.5 (Framework discipline) + § 7 (Structural-fix family)
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 14 + 18 + 19 + 21 + 23 (closed at composition surface)
- CLAUDE.md item 31 (Framework-driven extensibility) — meta-principle codification
- H9 + H15-H19 (invariants served)
- TECH_DEBT-009 (cfg field migration progress); TECH_DEBT-056 (codebase-wide bitpacking sweep — Caramel's later review); TECH_DEBT-057 (FOREACH_REGISTRY migration); TECH_DEBT-058 (REGISTRY_TOPOLOGY.md auto-gen); TECH_DEBT-059 (wide-variant deprecation)
