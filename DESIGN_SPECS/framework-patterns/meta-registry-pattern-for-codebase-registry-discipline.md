---
type: framework-pattern
stage: 5-claude-md
version: 1.1
established: 2026-05-14
tags: [framework-discipline, structural-fix, meta-discipline, pattern-codification]
surface: [registry, ci-tooling]
sister_specs: [registry-coverage-ci-check-pattern.md, framework-composition-overview.md, sidecar-override-pattern-for-registry-auto-flows.md, metadata-bit-driven-derived-filter-framework.md]
applies_at_skills: [/registry-fit-audit]
---

# Meta-registry pattern for codebase-wide registry discipline

**Established:** 2026-05-14 (v5.15.5.F.4d planning — DRAFT v1.0); **v1.1 Path γ+ v2 status + schema correction (2026-05-17)**
**Status:** **Stage 3 ACTIVE v1.1 (schema corrected 2026-05-17)** — pattern IS real at engine HEAD `545b087` (`FOREACH_REGISTRY` exists at `CoreFrameworks/MetaRegistry.hpp` with 63+ enrolled rows). **Schema correction:** spec body originally described 8-column tuple `X(NAME, "source_file", LEVEL, PARENT, "design_spec", BUG_CLASS, WIRE_FORMAT_KIND, "doc")` but actual code uses **4-column tuple** `X(registry_name, LEVEL, PARENT_NAME, description)`. Filename ref correction: spec said `RegistryRoster.hpp` but file is `CoreFrameworks/MetaRegistry.hpp` (renamed at `.F.4d`). Non-existent `FOREACH_DERIVED_FILTER` Level-1 references in spec body REMOVED per Path γ correction (FOREACH_METADATA_BIT IS the canonical metadata-bit registry; FOREACH_DERIVED_FILTER concept superseded). 8-column tuple migration scheduled at TECH_DEBT-057. Per D4 audit + Path γ+ v2 triage 2026-05-17 per `plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` § Finding 2. Spec body schema examples need update at ship close to use 4-col tuple.
**Tags:** structural-fix, framework-discipline, discoverability; closes Class 18 at meta-layer (added registry but forgot to document) + Class 21 (parallel descriptors at registry-roster level) + Class 14 (spec-vs-code schema drift correction); serves H15 + H19; Stage 3 ACTIVE v1.1 (2 canonical applications landed at HEAD: FOREACH_PER_CORE_DOMAIN_BITMAP + FOREACH_REGISTRY codebase-wide; H15 codified at `.F.4d`)

**Cross-references:**
- Parent pattern: `x-macro-registry-with-presence-dispatch.md` (registries themselves; this is the meta-layer)
- Sister: `metadata-bit-driven-derived-filter-framework.md` (`FOREACH_DERIVED_FILTER` is a Level-1 meta-registry managed by THIS spec's Level-2 `FOREACH_REGISTRY`)
- Composes with: `bitmap-flag-api.md` (RegistryRosterEntry packed flags per `multi-bit-state-encoding-pattern.md`)
- Composes with: `pattern-codification-lifecycle.md` (each row tracks its DESIGN_SPEC + lifecycle stage)
- Closes: Class 18 at meta-layer (silent registry drift across codebase)
- Serves: H15 (every X-macro registry in `FOREACH_REGISTRY`) + H19 (LEVEL > 0 registries declare PARENT)
- CLAUDE.md item 31 (Framework-driven extensibility — meta-principle)

---

## Problem statement

As a codebase accumulates X-macro registries (FOREACH_*), several drift classes emerge at the **meta-level** — at the level of "what registries does this codebase have?" rather than "what's in this specific registry?":

1. **Discoverability gap.** New contributors don't know which registries exist. `grep -r FOREACH_` is noisy; the catalog isn't centralized. Tribal knowledge.
2. **Adding a registry without documenting it.** A new `FOREACH_X` lands somewhere in `MemHeaders/` or `ML_Headers/`; the DESIGN_SPEC cross-link isn't added; future audits don't include it. Class 18 at meta-layer.
3. **Audit coverage gap.** `/dod-audit` walks `DESIGN_SPECS/*.md` to find patterns to audit against; if a registry's pattern isn't in DESIGN_SPECS, the audit can't audit it.
4. **Cohort discipline gap.** When multiple registries share a parent meta-registry (e.g., 7 derived filters all managed by `FOREACH_DERIVED_FILTER`), the cohort lacks a structural anchor.
5. **Topology obscurity.** The codebase has hierarchy: Level 2 codebase-wide meta-registry → Level 1 cohort meta-registries → Level 0 concrete registries. Without explicit data, the topology is implicit.

Codebase has ~20+ X-macro registries at v5.15.5.F.4b: FOREACH_CFG_FIELD, FOREACH_STAMP_BOUND_CFG, FOREACH_STRATEGY, FOREACH_FEATURE, FOREACH_FAILURE_MODE, FOREACH_SHALT, FOREACH_REGIME, FOREACH_DEGRADATION_CURVE, FOREACH_BANDIT_ALGORITHM, FOREACH_BARRIER_BLEND_MODE, 5 × FOREACH_*_CFG_FLAG bitmap registries, FOREACH_OMS_FIELD, FOREACH_CFG_DRIFT_CHECK, FOREACH_ARCH_FIELD_DRIFT, FOREACH_SLOW_PATH_GATE, FOREACH_CFG_DERIVED_INFERENCE_CFG, FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG/_POST_CFG, etc.

Recurrence guaranteed: every future sprint adds 1-3 more registries. Without a structural anchor, the drift compounds.

---

## Design

> [!WARNING]
> **This Design section is STALE vs the shipped implementation** (flagged `.E.0.10` 2026-06-11; full refresh tracked at **TECH_DEBT-172**). It describes the ORIGINAL design — `CoreFrameworks/RegistryRoster.hpp` with an 8-field tuple `X(NAME, file, LEVEL, PARENT, spec, BUG_CLASS, WIRE_KIND, doc)` + a bit-packed `RegistryRosterEntry` struct + **concrete = Level 0 / root = Level 2** numbering. **What shipped is simpler and numbered the OTHER way:** `CoreFrameworks/MetaRegistry.hpp`, a 4-field `X(registry_name, LEVEL, PARENT_NAME, description)`, with **root `FOREACH_REGISTRY` = Level 0**, direct registries = Level 1, a child of a Level-1 meta = Level 2 — the numbering the tool's Check 3 enforces and that CLAUDE.md / DESIGN_PHILOSOPHY H19 now match. **Read every level number below as INVERTED** until the refresh lands. The PATTERN (a meta-registry of registries + topology discipline) is sound; the specific structure + numbering here are pre-implementation.

### Three-level topology (no artificial cap; document the expectation)

```
Level 2 (ROOT_META):    FOREACH_REGISTRY (the registry-of-registries; this file)
   │
   ├── Level 1 (META):  FOREACH_DERIVED_FILTER (manages 7 cfg-derived filters)
   │                    FOREACH_<future_cohort_meta> (room for more Level-1 metas)
   │
   └── Level 0 (concrete): 18+ stand-alone X-macro registries
        ├── CFG_FIELD, STRATEGY, FEATURE, REGIME, FAILURE_MODE
        ├── 5 FOREACH_*_CFG_FLAG bitmap domains
        ├── STAMP_BOUND_MODEL_CONST_PRE/_POST, OMS_FIELD
        ├── CFG_DRIFT_CHECK, ARCH_FIELD_DRIFT
        ├── SLOW_PATH_GATE, DEGRADATION_CURVE, BANDIT_ALGORITHM, BARRIER_BLEND_MODE
        └── ... (others as added)
```

**Caps:** none enforced. 3 levels is the expected topology today; deeper allowed with rationale (per CLAUDE.local.md 2026-05-14 design decision: don't pre-cap; let structure emerge naturally). Header comment documents the expectation; CI doesn't `static_assert` a depth limit.

### `FOREACH_REGISTRY` tuple

```cpp
// CoreFrameworks/RegistryRoster.hpp
//
// Tuple: X(NAME_TOKEN, "source_file", LEVEL, PARENT, "design_spec", BUG_CLASS, WIRE_FORMAT_KIND, "doc")
//
//   NAME_TOKEN:        macro-friendly registry name (e.g., CFG_FIELD, DERIVED_FILTER)
//   source_file:       relative path where the registry's macro is defined
//   LEVEL:             0 (concrete data registry) / 1 (cohort meta-registry) / 2 (codebase-wide meta)
//   PARENT:            ROOT (top-level) or another registry's NAME_TOKEN (managed-by)
//   design_spec:       DESIGN_SPECS/ filename that documents the pattern
//   BUG_CLASS:         NONE / Class_<N> from RECURRING_BUG_PATTERNS (if pattern closes a class)
//   WIRE_FORMAT_KIND:  NOT_WIRE / WIRE_FORMAT / WIRE_FORMAT_TWO_SOURCE / MIXED
//   doc:               1-line description for catalog rendering

#define FOREACH_REGISTRY(X) \
    /* === Universal cfg infrastructure === */                              \
    X(CFG_FIELD,                                                            \
      "CoreFrameworks/CfgFieldRegistry.hpp", 0, ROOT,                       \
      "universal-cfg-field-registry-pattern.md", Class_18, NOT_WIRE,        \
      "Universal cfg field source-of-truth (.F.4 sprint)")                  \
    X(DERIVED_FILTER,                                                       \
      "CoreFrameworks/DerivedFilterRoster.hpp", 1, ROOT,                    \
      "metadata-bit-driven-derived-filter-framework.md", Class_21, MIXED,   \
      "Manages 7 cfg-derived filters")                                      \
    X(STAMP_BOUND_DERIVED,                                                  \
      "CoreFrameworks/StampBoundDerivedFilter.hpp", 0, DERIVED_FILTER,      \
      "metadata-bit-driven-derived-filter-framework.md",                    \
      Class_21, WIRE_FORMAT_TWO_SOURCE,                                     \
      "Stamp-bound derived filter; built at .F.4d via framework")           \
    /* === Strategy / ML / regime enumeration === */                        \
    X(STRATEGY,                                                             \
      "Strategies/StrategyRegistry.hpp", 0, ROOT,                           \
      "categorical-tag-applicability-pattern.md", Class_19, NOT_WIRE,       \
      "Strategy enum + category masks")                                     \
    /* ... ~15-20 more initial rows at .F.4d ship; remaining ~10-15 ... */  \
    /* ... migrate via TECH_DEBT-057 as time allows ...                  */
```

### Per-row data struct (bit-packed per `multi-bit-state-encoding-pattern.md`)

```cpp
struct RegistryRosterEntry {
    const char* name;           // human-readable registry name
    const char* source_file;    // relative path to .hpp defining FOREACH_<NAME>
    uint8_t     parent_idx;     // 0xFF = ROOT; else index into g_registry_roster[]
    uint8_t     flags;          // PACKED: bits 0-3 LEVEL (0-15); bits 4-5 WIRE_FORMAT_KIND; bits 6-7 reserved
    uint8_t     bug_class;      // 0 = NONE; else Class N (5 bits used; 3 bits reserved)
    uint8_t     _padding = 0;
    const char* design_spec;    // DESIGN_SPECS/ filename
    const char* doc;            // 1-line catalog description
};
static_assert(sizeof(RegistryRosterEntry) == 40,
              "RegistryRosterEntry must be 40 bytes (cache-friendly; ~2 entries per cache line)");

// Branchless accessors:
constexpr uint8_t ROSTER_FLAGS_LEVEL_MASK     = 0x0F;
constexpr uint8_t ROSTER_FLAGS_WIRE_KIND_MASK = 0x30;
constexpr uint8_t ROSTER_FLAGS_WIRE_KIND_SHIFT = 4;

inline uint8_t roster_level(uint8_t flags)            { return flags & ROSTER_FLAGS_LEVEL_MASK; }
inline uint8_t roster_wire_format_kind(uint8_t flags) {
    return (flags & ROSTER_FLAGS_WIRE_KIND_MASK) >> ROSTER_FLAGS_WIRE_KIND_SHIFT;
}
```

### CI cross-check (H15 + H19 invariant)

```cpp
void test_foreach_registry_completeness() {
    // H15: every X-macro registry in the codebase MUST have a row in FOREACH_REGISTRY.
    // CI script greps for "^#define FOREACH_[A-Z_]+\\(X\\)" across codebase, compares
    // against FOREACH_REGISTRY entries. Missing rows → build warning (or error per H15 maturity).
    //
    // H19: every row with LEVEL > 0 MUST declare a valid PARENT.
    // - PARENT == ROOT for Level-0 concrete registries with no managing meta
    // - PARENT == <name> for Level-0 registries managed by Level-1 meta
    // - PARENT == ROOT for Level-1 metas (managed by Level-2 FOREACH_REGISTRY itself)
    for (size_t i = 0; i < FOREACH_REGISTRY_COUNT; i++) {
        const auto& e = g_registry_roster[i];
        uint8_t lvl = roster_level(e.flags);
        if (lvl > 0) {
            check("H19: LEVEL > 0 row has valid PARENT",
                  e.parent_idx == ROOT_PARENT_IDX || e.parent_idx < FOREACH_REGISTRY_COUNT);
        }
        // source_file exists at compile time (verified via static_assert(__has_include(source_file)))
    }
}
```

### Topology auto-generation (TECH_DEBT-058)

A Python script `tools/generate_registry_topology.py` parses `RegistryRoster.hpp` `FOREACH_REGISTRY` entries + emits an ASCII tree visualization to `workspace/DOCS/REGISTRY_TOPOLOGY.md`. CI regenerates + diffs against committed version to ensure freshness. Manual version ships at `.F.4d`; auto-gen lands when entry count grows past ~25 or manual drift surfaces.

---

## Trade-offs + when to apply

### Apply when:
- Codebase has ≥10 X-macro registries (current count: ~20)
- Discoverability becomes a real problem (new contributors can't find existing registries)
- Audit/CI infrastructure wants a single iteration surface (one walk over `FOREACH_REGISTRY` covers all)
- Multiple registries share a managing meta-registry (cohort discipline; `FOREACH_DERIVED_FILTER` etc.)

### Skip when:
- Few registries (≤3); discoverability via grep is sufficient
- Each registry is fundamentally local concern (no cross-cutting audit needs)
- Cost of meta-registry > value of discoverability (rare for HFT codebases)

### Cost:
- `RegistryRoster.hpp` declaration + ~20 initial rows: ~150 LOC
- CI completeness test: ~50 LOC (covers H15 + H19 invariants)
- Per-registry migration (adding a row to FOREACH_REGISTRY for existing registries): ~5 min per registry × 15 unmigrated = ~75 min total — tracked via TECH_DEBT-057
- Auto-generation script (deferred per TECH_DEBT-058): ~50 LOC Python
- New registry addition: 1 row to FOREACH_REGISTRY (5 min)

### Win:
- Single discoverability surface (`grep FOREACH_REGISTRY` shows all)
- `/dod-audit` can walk the roster + verify pattern compliance per registry
- `/precoding-audit-gate` Stage 1 auto-derivation uses roster metadata (DESIGN_SPEC links + tags) to match plan content
- Adding a new registry without registering it FAILS the build (H15 CI test)
- Cohort discipline anchored (FOREACH_DERIVED_FILTER managed by FOREACH_REGISTRY at Level 2)
- DESIGN_SPECS cross-links auto-maintained (CI verifies design_spec column matches a real file)

---

## Reference implementations

### v5.15.5.F.4d (FIRST canonical application — pending ship)

- `CoreFrameworks/RegistryRoster.hpp` (NEW file; ~150 LOC)
- ~15-22 initial rows: CFG_FIELD, DERIVED_FILTER (Level 1), STAMP_BOUND_DERIVED, STRATEGY, FEATURE, REGIME, FAILURE_MODE, CFG_DRIFT_CHECK, ARCH_FIELD_DRIFT, ML_CFG_FLAG, OMS_FIELD, STAMP_BOUND_MODEL_CONST (split presented as one entry with PRE/POST note in doc), CFG_DERIVED_INFERENCE_CFG, BANDIT_ALGORITHM, BARRIER_BLEND_MODE
- Remaining ~10-15 registries migrate per TECH_DEBT-057 as time allows
- CI completeness test (H15 + H19) added to controller_test
- Manual `REGISTRY_TOPOLOGY.md` (workspace DOCS/) shipped at `.F.4d` (auto-gen Python script per TECH_DEBT-058)

### Future application catalog

Pattern lifecycle:
- Stage 2 (DRAFT) — this doc; pending ship
- Stage 3 (first reference) — `.F.4d` FOREACH_REGISTRY initial 15-22 rows
- Stage 4 (cohort migration) — TECH_DEBT-057 sweep migrates remaining ~10-15 registries (1 row each; mechanical)
- Stage 5 (CLAUDE.md item promotion) — after 2+ Level-1 meta-registries exist (FOREACH_DERIVED_FILTER + ~1 future Level-1 meta), promote to full CLAUDE.md item
- Stage 6 (tooling enforcement) — CI completeness test promotes to build-error severity once all registries migrated
- Stage 7 (wider audit) — `/dod-audit` walks FOREACH_REGISTRY to verify each registry's pattern compliance

---

## Lessons / gotchas

### Cross-file source-foreach references are TOKENS not invocations

`FOREACH_REGISTRY` rows reference other registries by NAME token (e.g., `CFG_FIELD`), not by macro invocation (`FOREACH_CFG_FIELD(...)`). Macro invocation would expand at the wrong time. CI script resolves the token to the source file via the row's `source_file` column.

### LEVEL/PARENT encode the tree as data

The hierarchy is encoded in tuple columns, not implicit from declaration order. This lets auto-generation tools render the topology + CI cross-check parent-child consistency without re-deriving structure from code.

### Cohort discipline at the meta-level

When multiple Level-0 registries share a Level-1 meta (e.g., 7 derived filters under DERIVED_FILTER parent), the meta-registry's row in FOREACH_REGISTRY anchors the cohort. Adding an 8th derived filter = 1 row in FOREACH_DERIVED_FILTER (Level-1 meta walks); the FOREACH_REGISTRY entry for the meta stays unchanged.

### Avoid Level-3+ meta-meta-registries unless genuinely needed

The codebase's natural topology is 3 levels (Level 2 codebase-wide + Level 1 cohort + Level 0 concrete). Deeper nesting (Level 3 = meta-meta-meta) is metaphysical engineering. Document the expectation in `RegistryRoster.hpp` header comment; don't enforce via static_assert (per CLAUDE.local.md 2026-05-14 decision: cap is a soft guideline, not policy).

### CI completeness test severity gradient

At `.F.4d` ship: CI completeness test is a BUILD WARNING (some registries unmigrated; TECH_DEBT-057 tracks). After TECH_DEBT-057 sweep: CI completeness test promotes to BUILD ERROR (every new registry MUST have a row before merge). Migration sequence: warning → error.

### Bit-packing per multi-bit-state-encoding-pattern.md

`RegistryRosterEntry.flags` packs LEVEL (4 bits) + WIRE_FORMAT_KIND (2 bits) + reserved (2 bits) into single uint8_t. Future growth via reserved bits + bug_class headroom (5 bits used; 3 bits reserved). Per CLAUDE.md item 30 (multi-bit state encoding promoted to INVARIANT at `.F.4d` ship with 3 canonical applications: DriftOverride + RegistryRosterEntry + ManualFieldInventoryEntry).

---

## Patterns NOT used here (and why)

### Self-registration per registry header

Considered: each registry's header includes `RegistryRoster.hpp` + adds itself via a static-init macro. Rejected — creates circular include dependencies (RegistryRoster.hpp would need to know about all registries; all registries would need to know about RegistryRoster.hpp). Centralized declaration in one file is simpler.

### Runtime reflection via dlsym / debug symbols

Considered: enumerate registries at runtime via dlsym lookup. Rejected — loses compile-time guarantees (H15 CI test wouldn't catch missing rows); platform-specific (Linux-only via dlsym); incompatible with the codebase's static-binary deployment model.

### Auto-generated FOREACH_REGISTRY from grep + parse

Considered: Python script greps codebase for `^#define FOREACH_*` patterns + emits FOREACH_REGISTRY automatically. Rejected — fragile (heuristic grep can't extract LEVEL/PARENT/design_spec/bug_class/wire_format_kind metadata; those are human decisions). Manual declaration with CI verification is more robust.

---

## Cross-references

- `x-macro-registry-with-presence-dispatch.md` — the registries themselves; this is the meta-layer
- `metadata-bit-driven-derived-filter-framework.md` — `FOREACH_DERIVED_FILTER` is a Level-1 meta-registry managed by `FOREACH_REGISTRY`
- `bitmap-flag-api.md` — `RegistryRosterEntry.flags` packing
- `multi-bit-state-encoding-pattern.md` (CLAUDE.md item 30) — RegistryRosterEntry as canonical application
- `pattern-codification-lifecycle.md` — each row tracks its DESIGN_SPEC + lifecycle stage
- `structural-fix-preferred-decision-framework.md` — motivation (Class 18 mirror at meta-layer)
- `registry-coverage-ci-check-pattern.md` — **ORTHOGONAL AT PERPENDICULAR LAYER**: H15 / this spec = registries-in-meta-registry (codebase-wide topology + each registry is enrolled in `FOREACH_REGISTRY`); sister spec = fields-in-registries (per-registry coverage enforcement — every struct field matching predicate must be in its registry, OR explicit-exempt with rationale). Both enforce framework discipline at different layers and compose: each row in `FOREACH_REGISTRY` can have its own coverage CI check via the sister spec's Python tool template. Discoverability at meta-layer (this spec) + integrity at field-add layer (sister spec).
- `DOCS/DESIGN_PHILOSOPHY.md` § 1.5 (Framework discipline) + § 7 (Structural-fix family)
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 18 (mirror-incomplete at meta-layer) + Class 21 (parallel descriptors)
- CLAUDE.md item 31 (Framework-driven extensibility — codification)
- H15 (every X-macro registry in FOREACH_REGISTRY — pending codification at `.F.4d` ship)
- H19 (LEVEL > 0 registries declare PARENT in FOREACH_REGISTRY tuple — pending codification at `.F.4d` ship)
- TECH_DEBT-057 (migrate remaining ~15 registries to FOREACH_REGISTRY)
- TECH_DEBT-058 (REGISTRY_TOPOLOGY.md auto-generation Python script)
- `workspace/DOCS/REGISTRY_TOPOLOGY.md` (manual at `.F.4d`; auto-gen post-TECH_DEBT-058)
