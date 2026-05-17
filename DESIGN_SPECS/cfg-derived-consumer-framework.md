# Cfg-derived consumer framework

**Established:** 2026-05-17 (v5.15.5.F.4d.1.B planning — codified as the master pattern doc for cfg-derived behavior; landed alongside `canonical-sister-extension-discipline.md` after Batch 1+2 pre-coding audit gate identified the 3-way triplet `FOREACH_CFG_DERIVED_INFERENCE_CFG × FOREACH_CFG_DRIFT_CHECK × FOREACH_STAMP_BOUND_CFG` consolidation opportunity)
**Status:** **Stage 3 ACTIVE v1.1** (promoted from Stage 2 DRAFT at `v5.15.5.F.4d.1.B.1` ship close 2026-05-17; first canonical = NEW `MemHeaders/CfgGateRegistry.hpp` + 3 derived-filter consumer template fns + tt:: dispatch quartet → septet extension; walker iterates 0 rows at `.B.1` post-Step-6 vacuous-PASS tests; full activation at `.B.2` cohort migration when STAMP_BOUND_CFG_DERIVED bit flagged on 24+ source rows)
**Tags:** framework-discipline, master-pattern, cfg-infrastructure, registry-driven, future-easier; serves H15 + H17 + H18 + H19 + item 31; composes with metadata-bit-driven-derived-filter-framework + sidecar-override-pattern + tt:: dispatch via tt:: namespace + autopopulate-pattern-for-production-caller-class

**Cross-references:**
- Parent discipline: `canonical-sister-extension-discipline.md` (this is the 1st canonical application of that discipline)
- Composes with: `metadata-bit-driven-derived-filter-framework.md` v1.3+ (STAMP_BOUND_CFG_DERIVED metadata bit drives walker)
- Composes with: `sidecar-override-pattern-for-registry-auto-flows.md` (FOREACH_CFG_GATE is 1st canonical of gate-type sidecar)
- Composes with: `type-trait-dispatch-via-tt-namespace.md` (tt::cfg_emit_field + tt::cfg_populate_inf_field + tt::cfg_drift_compare type-trait dispatchers)
- Composes with: `autopopulate-pattern-for-production-caller-class.md` (3 new consumer macros sister to STAMP_CFG_AUTOPOPULATE + INFERENCE_CFG_AUTOPOPULATE)
- Sister: `framework-composition-overview.md` v1.2+ (composition narrative)
- Skill: `/anti-spaghetti` (codebase-wide audit catching parallel cfg-derived registries)
- CLAUDE.md item 31 (framework-driven extensibility meta-principle)
- H15 (every X-macro registry enrolled in FOREACH_REGISTRY)
- H17 (cfg struct fields auto-generated from FOREACH_CFG_FIELD)
- H18 (custom-semantics via sidecar override)
- H19 (meta-registry topology)

---

## Problem statement

Cfg fields have multiple derived behaviors that need to flow through wire-format / drift-check / inference-cfg populate / stamp body emit / parse paths. Historically (pre-`.B`), the codebase had MULTIPLE PARALLEL REGISTRIES encoding subsets of this behavior:

- `FOREACH_STAMP_BOUND_CFG` — cfg fields participating in stamp body
- `FOREACH_CFG_DERIVED_INFERENCE_CFG` — cfg → inference_cfg_* populate mapping (with inline gate_when)
- `FOREACH_CFG_DRIFT_CHECK` — cfg drift check rows
- `FOREACH_STAMP_BOUND_MODEL_CONST` (sister; different concern — model state vs cfg-derived; stays separate)

The CFG_DERIVED_INFERENCE_CFG × CFG_DRIFT_CHECK × STAMP_BOUND_CFG triplet has 93% row overlap (Batch 2 `/anti-spaghetti` audit confirmed). Each row exists in 2-3 registries with parallel encoding. Drift potential: bug fix in one registry's row doesn't auto-flow to siblings. The 5th BANDIT_THOMPSON field that β4 plan body MISSED was already in canonical CFG_DERIVED_INFERENCE_CFG — direct evidence of drift-induced incompleteness.

Naive fix: keep parallel registries; add CI to check row-overlap consistency. Mechanicalizes the wrong shape; entrenches Class 18 mirror anti-pattern at registry granularity.

Better fix: ONE master registry (`FOREACH_PER_CORE_CFG_FIELD` + `FOREACH_GLOBAL_CFG_FIELD` + `FOREACH_ML_CFG_FLAG` for bitmap-bool) with metadata bits; canonical sidecars for cohort-specific behavior; uniform consumer macros each walking master + applying appropriate filter. ONE source of truth; many consumer views; impossible to drift.

This pattern is the FUTURE-EASIER shape — adding a new cfg field = 1 row in master + (rare) 1 row in sidecar. Adding a new consumer concern = 1 new consumer macro walking master.

---

## The 4-axis taxonomy

Every cfg field with derived behavior has 4 orthogonal axes:

### Axis A — Master registry (where the row lives)

Already canonical at HEAD (`.F.4c.3`+):
- `FOREACH_PER_CORE_CFG_FIELD` — per-core cfg state (in `PerCoreCfg<F>`)
- `FOREACH_GLOBAL_CFG_FIELD` — global cfg state (in `ControllerConfig<F>`)
- `FOREACH_ML_CFG_FLAG` — bitmap-resident bool fields (in `cfg.ml_cfg_flags`)

**No new master registries should ever be added** for cfg fields. New scope = new metadata bit + extend existing master.

### Axis B — Metadata bits (what derived behavior applies)

Already canonical at HEAD (`.F.4c.3`+):
- `FOREACH_METADATA_BIT` — single source of truth for per-bit derived filter mask auto-generation
- Bits at HEAD: STAMP_BOUND + HIDDEN_BY_DEFAULT + IS_SECRET + IS_BOOT_ONLY + AFFECTS_STAMP_PARITY + LOG_VALUE_FORBIDDEN + HAS_SIDE_EFFECT + WARN_ON_CLAMP + RESTART_REQUIRED + SAFETY_CRITICAL + DEPRECATED + STAMP_BOUND_CFG_DERIVED (added `.A`)

**Adding a new behavior axis** = 1 row in `FOREACH_METADATA_BIT` + auto-generated per-bit + per-core sister masks via `cfg_compute_mask` at `CfgFieldRegistry.hpp:1064-1075`.

### Axis C — Gate sidecar (when the behavior applies per row)

NEW at `.B.1`:
- `FOREACH_CFG_GATE` — sparse sidecar mapping `row name → gate_when_expr`
- Sister to `FOREACH_DRIFT_OVERRIDE` (`.C`; severity-type override sidecar)

Per H18 (custom-semantics via sidecar): if a row's behavior differs from the default, an entry exists; if absent, default applies. Sparse → most rows don't need an entry.

**Default gates:**
- For drift check: `STAMP_HAS(*handle, inference_cfg)` (always-emit canonical Q3.G; drift check fires when stamp present)
- For populate: `1` (always populate; gate-time check at row content level when needed via `gate_when_expr`)

**Cohort gates** (custom per-cohort; sparse sidecar entries):
- Bandit/Thompson cohort → `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)`
- Ridge cohort → `BITMAP_ANY(cfg.ml_cfg_flags, MASK_ML_CFG_RIDGE_WITHIN_HORIZON | MASK_ML_CFG_RIDGE_ACROSS_HORIZONS)`
- Composite confidence cohort → `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_CONFIDENCE_COMPOSITE_ENABLED)`
- Soft-risk degradation cohort → `cfg.risk_degradation_curve != 0`

### Axis D — Value extraction (how to get the row's value from cfg)

Already canonical at HEAD (`.F.4c.3`+):
- `tt::` namespace type-trait dispatchers — `tt::cfg_save_field<T>`, `tt::cfg_parse_field<T>`
- Pattern: `if constexpr (is_FPN_v<T>) { ... } else if constexpr (std::is_integral_v<T>) { ... } else if constexpr (std::is_array_v<T>) { ... }` etc.

NEW at `.B.1`:
- `tt::cfg_emit_field<T>` — wire-format byte emit (sister to `tt::cfg_save_field<T>`; locale-pinned Layer 2 per `ModelInference.hpp:1697` precedent)
- `tt::cfg_populate_inf_field<T>` — populate `inf.*` field from `cfg.*`
- `tt::cfg_drift_compare<T>` — drift compare `stamp.*` vs `cfg.*` value

---

## End-state architecture

```
                    +-----------------------+
                    |  Master cfg registry  |
                    |  (per_core + global)  |
                    |  metadata_bits column |
                    +-----------+-----------+
                                |
                  +-------------+-------------+
                  |     FOREACH_METADATA_BIT  |
                  |  auto-gen per-bit masks   |
                  +-------------+-------------+
                                |
                                | walks via CFG_FIELD_FOR_EACH_SET_BIT
                                |
+-------------------+-----------+-----------+--------------------+
|                   |                       |                    |
v                   v                       v                    v
+-------------+ +-----------+ +-------------------+ +-----------------+
| INFERENCE_  | | STAMP_CFG | | DRIFT_CHECK_      | | (future         |
| CFG_POPU... | | _POPU...  | | AUTOPOPULATE      | |  consumer N)    |
+------+------+ +-----+-----+ +---------+---------+ +--------+--------+
       |              |                 |                    |
       |              |                 |                    |
       +--------------+-----------------+--------------------+
                                |
                                | per-row gate lookup
                                v
                    +-----------------------+
                    |  FOREACH_CFG_GATE     |
                    |  sparse sidecar       |
                    |  default if absent    |
                    +-----------------------+
                                |
                                | per-row value extract
                                v
                    +-----------------------+
                    |  tt:: type-trait      |
                    |  dispatch             |
                    +-----------------------+
```

---

## Adding a new cfg field with derived behavior (the discipline this framework produces)

**Step 1.** Add 1 row to `FOREACH_PER_CORE_CFG_FIELD` or `FOREACH_GLOBAL_CFG_FIELD` (master) with metadata_flags column set to relevant bits (e.g., `STAMP_BOUND | STAMP_BOUND_CFG_DERIVED`).

**Step 2 (rare).** If the field needs a non-default gate_when, add 1 row to `FOREACH_CFG_GATE` sparse sidecar with `X(<field_name>, <gate_when_expr>)`.

**Step 3 (rare).** If the field is bitmap-resident (KIND_BOOL → ml_cfg_flags), add to `FOREACH_ML_CFG_FLAG` instead (post-5→6 sig migration at `.B.2`).

**That's it.** All consumer macros (INFERENCE_CFG_POPULATE_FROM_DERIVED + STAMP_CFG_POPULATE_FROM_DERIVED + DRIFT_CHECK_AUTOPOPULATE + future consumers) automatically pick up the new row. No consumer code touches.

This is the "never worry about this again" shape for cfg fields with derived behavior. The framework is the discipline; adding rows can't drift because all consumers walk the same master.

---

## Adding a new consumer concern (the discipline this framework produces)

**Step 1.** Define a new consumer macro that walks via `CFG_FIELD_FOR_EACH_SET_BIT(g_*_cfg_<bit>_mask.words, idx, { ... })` for the relevant metadata bit.

**Step 2.** Per-row, look up gate via `FOREACH_CFG_GATE` sidecar (default if absent).

**Step 3.** Per-row, dispatch value extraction via `tt::` namespace (add new `tt::cfg_<verb>_field<T>` helper if a new value-extraction shape is needed).

**Step 4.** Enroll the new consumer macro in `FOREACH_REGISTRY` meta-registry per H15 + H19.

**That's it.** Adding a new consumer concern (e.g., a new GUI surface, new diagnostic output, new stamp variant) doesn't touch master registry rows. It doesn't touch existing consumer macros. It doesn't risk drift.

---

## Reference implementation (`.B.1` ship)

### Files created

- `MemHeaders/CfgGateRegistry.hpp` — `FOREACH_CFG_GATE(X)` sparse sidecar + 3 consumer macros
- `tick-trader-percore-workspace/DESIGN_SPECS/cfg-derived-consumer-framework.md` — THIS DOC

### Files migrated

- `ML_Headers/StampHelper.hpp:183` — `INFERENCE_CFG_AUTOPOPULATE` → `INFERENCE_CFG_POPULATE_FROM_DERIVED`
- `CoreFrameworks/MetaRegistry.hpp:99` — remove FOREACH_CFG_DERIVED_INFERENCE_CFG; add FOREACH_CFG_GATE + 3 consumer macros
- `tests/controller_test.cpp:24962-25047` — A.7 round-trip + gate-off semantics tests update

### Files NOT touched at `.B.1` (deferred to `.B.2`/`.B.3`)

- 24-row cohort source rows in master (cohort migration at `.B.2`)
- FOREACH_CFG_GATE sidecar entries (populated at `.B.2` per cohort)
- 4 ModelInference.hpp walker site migrations (`.B.2`)
- StampHelper.hpp:156 STAMP_CFG_AUTOPOPULATE migration (`.B.2`)
- 14 controller_test.cpp count-assertion migrations (`.B.3`)
- DELETE FOREACH_CFG_DERIVED_INFERENCE_CFG (`.B.3` after `.B.2` verifies)

### Behavior at `.B.1` close

- Walker iterates 0 rows (STAMP_BOUND_CFG_DERIVED bit flagged on 0 source rows at `.B.1`)
- All 3 consumer macros vacuous PASS for empty body
- HMAC chain byte preservation verified via `wire_format_invariants.hpp` helper from `.A` (vacuous PASS)
- Framework infrastructure ready for cohort exercise at `.B.2`

---

## Trade-offs + when to apply

### Apply when:

- New cfg field with stamp body / drift / wire-format / inference_cfg derived behavior
- New consumer concern over existing cfg fields (e.g., new GUI surface walking flagged cohort)
- Refactoring parallel registries with overlapping row name sets (per `canonical-sister-extension-discipline.md` audit findings)

### Skip when:

- Cfg field with no derived behavior (display-only / parse-only / runtime-only with no stamp participation)
- One-off consumer that doesn't recur (use direct field access)
- Concerns that genuinely warrant their own master registry (model state vs cfg-derived; HMAC body ordering)

### Cost:

- ~80-150 LOC framework infrastructure per derived-filter family (1-time cost at framework consolidation; e.g., this `.B.1`)
- ~5-15 LOC per consumer macro
- ~1 LOC per new cfg field (add metadata bit; rare gate sidecar row)

### Win:

- Adding new cfg field = 1 row in master; framework auto-flows behavior to all consumers
- Adding new consumer concern = 1 new macro; doesn't touch master or existing consumers
- ZERO drift potential between parallel structures (no parallel structures exist)
- Bug fix in one consumer applies to all rows automatically
- Compile-time verifiable (X-macro static_assert + H15/H17/H18/H19 CI checks)

---

## Lessons / gotchas

### Sidecar default semantics differ per consumer

- Drift check default: `STAMP_HAS(*handle, inference_cfg)` (drift fires when stamp present)
- Populate default: `1` (always populate; row content level gate via gate_when_expr if needed)
- Emit default: typically `1` (always-emit canonical Q3.G); cohort exceptions via sidecar

Different consumer macros encode default differently in their walker. This is OK; sidecar entries override the default uniformly.

### Locale pin is consumer-side

`tt::cfg_emit_field<T>` MUST honor Layer 2 locale-pin per `ModelInference.hpp:1697` precedent (`uselocale(LC_NUMERIC=C)` per-thread). I3 invariant in `wire_format_invariants.hpp` helper from `.A` catches drift.

### Sidecar registry is enrolled in meta-registry per H15 + H19

`FOREACH_CFG_GATE` row in `FOREACH_REGISTRY` at Level 1 with PARENT = `FOREACH_METADATA_BIT` (since the sidecar's purpose is to qualify rows that flag a specific metadata bit).

### `.B.1` walker is 0-row at ship close (and that's correct)

Don't confuse "vacuous PASS" tests with "tests not exercising the code". The walker mechanism itself is exercised; the rows being iterated are empty. `.B.2` populates the cohort; framework exercises non-empty thereafter.

### Multi-consumer pattern is the structural shape, not the API

Don't expose "Multi-consumer registry" as a public API. The discipline is: ONE master + many private consumer macros. External callers see only the consumer macros (e.g., `STAMP_CFG_POPULATE_FROM_DERIVED`); they don't see or touch master registry directly.

---

## Pattern lifecycle (per `pattern-codification-lifecycle.md`)

- **Stage 1 (problem identification):** Path γ #2 caught at `.B` planning 2026-05-17 (3-way triplet overlap analysis surfaced 93% drift surface)
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-17 at `.B.1` planning)
- **Stage 3 (first canonical reference):** `.B.1` ship — `FOREACH_CFG_GATE` + 3 consumer macros land
- **Stage 4 (cohort migration / exercise):** `.B.2`/`.B.3` — 24-row cohort flags STAMP_BOUND_CFG_DERIVED; legacy registries deleted; framework exercised non-empty
- **Stage 5+ (CLAUDE.md item promotion):** when 3+ derived-filter consumer families ship over this framework AND the "1 row in master = 1 row everywhere" discipline becomes load-bearing for sprint planning

---

## Cross-references

- Parent discipline: `canonical-sister-extension-discipline.md` (this is the 1st canonical application)
- Composes: `metadata-bit-driven-derived-filter-framework.md` v1.3+ (provides STAMP_BOUND_CFG_DERIVED bit + walker primitive)
- Composes: `sidecar-override-pattern-for-registry-auto-flows.md` (provides FOREACH_CFG_GATE sidecar shape)
- Composes: `type-trait-dispatch-via-tt-namespace.md` (provides tt:: per-type dispatchers)
- Composes: `autopopulate-pattern-for-production-caller-class.md` (provides AUTOPOPULATE consumer macro shape)
- Sister: `framework-composition-overview.md` v1.2+ (composition narrative)
- Skill: `/anti-spaghetti` at `claude-skills/anti-spaghetti/SKILL.md` (catches future parallel cfg-derived registries)
- CLAUDE.md item 31 (framework-driven extensibility meta-principle)
- H15 + H17 + H18 + H19 (the structural invariants this framework serves)
- RECURRING_BUG_PATTERNS.md Class 14 / 18 / 21 (the classes this framework closes)
- Memory: `feedback_audit_canonical_sister_before_new_infra.md`
- Memory: `feedback_plans_cite_sister_registry_inspection.md`
- Memory: `project_anti_spaghetti_audit_cadence.md`

---

**End of pattern v1.0 DRAFT.** Stage 3 first reference lands at `.B.1` ship close.
