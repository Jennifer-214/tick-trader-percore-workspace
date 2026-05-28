---
type: framework-pattern
stage: 5-claude-md
version: 1.1
established: 2026-05-14
tags: [framework-discipline, structural-fix, pattern-codification]
surface: [registry, cfg-flow]
sister_specs: [metadata-bit-driven-derived-filter-framework.md, manual-fields-inventory-pattern.md, universal-cfg-field-registry-pattern.md, cfg-derived-consumer-framework.md, framework-composition-overview.md, meta-registry-pattern-for-codebase-registry-discipline.md]
applies_at_skills: []
---

# Sidecar override pattern for registry auto-flows

**Established:** 2026-05-14 (v5.15.5.F.4d planning); **v1.1 Path γ+ v2 status correction (2026-05-17)**
**Status:** **Stage 2 DRAFT v1.1 (corrected 2026-05-17)** — Stage 3 ACTIVE promotion claim at `.F.4d` ship close was ASPIRATIONAL. `.F.4d` reserved relevant infrastructure but NO `FOREACH_DRIFT_OVERRIDE` registry / `DriftOverride` struct / `g_*_drift_overrides` arrays actually shipped. ZERO matches for these symbols at engine HEAD `545b087`. **Stage 3 first canonical reference now sequenced at `v5.15.5.F.4d.1.C` ship close** (when 5 XGBoost training-only fields + bit-packed `DriftOverride` + sidecar arrays actually land per `.C` plan body v1.2). Per D4 audit + Path γ+ v2 triage 2026-05-17 per `plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` § Finding 2. Sister to `metadata-bit-driven-derived-filter-framework.md` v1.2 Path γ correction (same aspirational-promotion class). Closes Class 14 (plan API drift) at spec-claim layer. Full spec body content below stays accurate (describes the pattern correctly); status badge corrected to match actual landing timeline.
**Tags:** structural-fix, registry-driven, framework-discipline; closes Class 21 at auto-flow-with-overrides surface + Class 14 (spec-vs-code drift correction); serves H18; Stage 2 DRAFT v1.1; 0 production applications until `.F.4d.1.C` ships

**Cross-references:**
- Parent pattern: `x-macro-registry-with-presence-dispatch.md` (registry-driven dispatch)
- Composes with: `autopopulate-pattern-for-production-caller-class.md` (standard-case auto-flow via AUTOPOPULATE)
- Composes with: `metadata-bit-driven-derived-filter-framework.md` (sidecar typically attaches to a derived filter's parent registry)
- Composes with: `bitmap-flag-api.md` (DriftOverride flags packed per `multi-bit-state-encoding-pattern.md`)
- Supersedes (for cfg-drift surface): `stamp-vs-runtime-drift-detection-registry.md` § "Wide variant" — see TECH_DEBT-059 deprecation
- Closes: Class 21 at auto-flow-with-overrides surface (no parallel wide-variant registries)
- Serves: H18 (custom-semantics overrides via sidecar; no parallel wide-variant registries)
- CLAUDE.md item 31 (Framework-driven extensibility — meta-principle)

---

## Problem statement

A registry has **heterogeneous behavior across its rows**:
- 70-90% of rows follow a **standard pattern** (e.g., for STAMP_BOUND cfg fields: drift severity REFUSE_STRICT + category INFERENCE_CFG + comparison via default tolerance)
- 10-30% of rows need **custom semantics** that don't fit the standard mold (e.g., 5 of 19 STAMP_BOUND fields are XGBoost hyperparameters needing WARN_ALWAYS + CROSS_BINARY category + tighter per-field epsilon)

Naive approach: declare a SEPARATE wide-variant registry with full per-row metadata for ALL rows. Standard cases redundantly re-specify defaults; custom cases get their richer semantics. **This is Class 21 anti-pattern** (multiple parallel descriptors at auto-flow surface): adding a new STAMP_BOUND field requires editing both `FOREACH_CFG_FIELD` AND the wide-variant `FOREACH_CFG_DRIFT_CHECK`; forgetting either causes drift.

Better approach: keep parent registry as single source of truth for standard cases; declare a **smaller sidecar override registry** containing only the custom-semantics rows; consumer's AUTOPOPULATE walks the parent + dispatches to default OR override based on sidecar lookup.

The recurring shape: **"parent registry has standard auto-flow + minority of rows need custom semantics."** Class 21 drift latent without sidecar pattern; recurrence guaranteed (6+ planned applications across drift / strategy gating / feature validation / cfg rendering / etc.).

---

## Design space explored

### Option A — Wide-variant parallel registry (status-quo before `.F.4d`)

```cpp
// FOREACH_CFG_DRIFT_CHECK at ML_Headers/CfgDriftCheckRegistry.hpp — 19 entries
#define FOREACH_CFG_DRIFT_CHECK(X) \
    X(confidence_threshold_scale, double, REFUSE_STRICT, INFERENCE_CFG, EPS_DEFAULT, \
      h->inference_cfg_confidence_threshold_scale, FPN_ToDouble(cfg.confidence_threshold_scale), \
      STAMP_HAS(*h, inference_cfg), FAILURE_MASK_cfg_inference_drift, "Tier 1 ...") \
    X(xgb_subsample, double, WARN_ALWAYS, CROSS_BINARY, EPS_DEFAULT, \
      h->xgb_subsample, FPN_ToDouble(cfg.xgb_subsample), \
      STAMP_HAS(*h, xgb_hyperparams), FAILURE_MASK_cfg_cross_binary_drift, "XGB subsample drift") \
    /* ... 17 more entries ... */
```

**Rejected (for cfg-drift surface).** Class 21 risk: parallel registry maintenance. Standard cases (14/19 entries) redundantly re-specify default severity + category + compare_kind. Adding a new STAMP_BOUND field needs row in both FOREACH_CFG_FIELD AND FOREACH_CFG_DRIFT_CHECK; forgetting the latter → no drift check.

### Option B — Add columns to parent registry for ALL custom semantics

```cpp
// Extend FOREACH_CFG_FIELD tuple with drift_severity / drift_category / drift_epsilon columns
X(KIND_DOUBLE, ridge_lambda, "Ridge λ", "ML", STAMP_BOUND, ..., DRIFT_SEVERITY_DEFAULT, DRIFT_CATEGORY_DEFAULT, DRIFT_EPS_DEFAULT)
X(KIND_DOUBLE, xgb_subsample, "XGB Subsample", "ML", STAMP_BOUND, ..., DRIFT_SEVERITY_WARN, DRIFT_CATEGORY_CROSS_BINARY, DRIFT_EPS_TIGHT)
```

**Rejected.** Schema bend per concern; if 6+ consumers want custom-semantics columns, tuple grows linearly. Default columns dominate (14/19 rows use defaults); the registry becomes verbose for 30% benefit. Doesn't generalize to other applications (per-strategy custom gating wouldn't fit drift columns; would need its own column set).

### Option C — Function-pointer column with per-field override callbacks

```cpp
// Extend FOREACH_CFG_FIELD with drift_compare_fn function-pointer column
X(KIND_DOUBLE, xgb_subsample, ..., &drift_compare_xgb_subsample)
```

**Rejected.** Schema bend per concern (one function-pointer column per consumer). Indirection cost at runtime (function pointer vs inline). Anti-DOD (function-pointer table loses compile-time inlining). Compile-time enforcement weakened (forgotten function = null pointer; runtime crash vs compile error).

### Option D — Sidecar override table indexed by parent's FIELD_IDX (chosen)

```cpp
// CoreFrameworks/CfgFieldDriftOverride.hpp
struct DriftOverride { /* packed flags + eps_idx */ };

// First canonical application: 5 XGBoost training-only hyperparameters needing
// WARN_ALWAYS + CROSS_BINARY override (existing rows at CfgDriftCheckRegistry.hpp:202-221
// move from wide-variant inline form to sidecar at `.F.4d`):
#define FOREACH_DRIFT_OVERRIDE(X) \
    X(xgb_subsample,        WARN_ALWAYS, CROSS_BINARY, EPS_DEFAULT, 0) \
    X(xgb_colsample_bytree, WARN_ALWAYS, CROSS_BINARY, EPS_DEFAULT, 0) \
    X(xgb_min_child_weight, WARN_ALWAYS, CROSS_BINARY, EXACT,       0) \
    X(xgb_seed,             WARN_ALWAYS, CROSS_BINARY, EXACT,       0) \
    X(xgb_tree_method,      WARN_ALWAYS, CROSS_BINARY, STRING,      0) \
    /* Per C4 decision at `.F.4d`: split sidecars per registry scope —
     * g_global_drift_overrides + g_per_core_drift_overrides — to mirror
     * the cfg registry split (FOREACH_GLOBAL_CFG_FIELD + FOREACH_PER_CORE_CFG_FIELD).
     * Branchless lookup at X-macro expansion time selects appropriate sidecar.
     */

// Split sidecar arrays indexed by parent registry's FIELD_IDX scheme (most entries zero):
DriftOverride g_global_drift_overrides[FIELD_IDX_GLOBAL_END] = {0};
DriftOverride g_per_core_drift_overrides[FIELD_IDX_PER_CORE_END] = {0};

// CFG_DRIFT_AUTOPOPULATE walks STAMP_BOUND derived filter + dispatches via sidecar:
//   const DriftOverride& ovr = g_drift_overrides[FIELD_IDX_<field>];
//   uint8_t severity = ovr.has_override ? drift_ovr_severity(ovr.flags) : REFUSE_STRICT_DEFAULT;
```

**Chosen.** Standard cases get auto-flow via AUTOPOPULATE; custom cases get explicit override rows (only ~5 of 213 cfg fields need this); single source of truth at parent registry; sidecar is purely additive (not parallel). Class 21 closed structurally.

---

## The pattern (concrete shape)

### Sidecar struct (bit-packed per `multi-bit-state-encoding-pattern.md`)

```cpp
// CoreFrameworks/CfgFieldDriftOverride.hpp
//
// Pattern: sidecar-override-pattern-for-registry-auto-flows.md
// Composes: bitmap-flag-api.md + multi-bit-state-encoding-pattern.md (CLAUDE.md item 30)

struct DriftOverride {
    // Packed flags (1 byte; 5 bits used + 3 reserved):
    //   bit 0     has_override   — 0 = use defaults; 1 = use this row
    //   bit 1     severity       — 0 = REFUSE_STRICT, 1 = WARN_ALWAYS
    //   bit 2     category       — 0 = INFERENCE_CFG, 1 = CROSS_BINARY
    //   bits 3-4  compare_kind   — 0=EXACT, 1=EPS_DEFAULT, 2=EPS_TIGHT, 3=EPS_CUSTOM
    //   bits 5-7  reserved
    uint8_t flags;

    // Index into sparse eps values table (only meaningful when compare_kind == EPS_CUSTOM):
    uint8_t eps_idx;

    // Explicit zero-init padding for byte-equivalence (H12 + struct-padding-determinism-pattern.md):
    int16_t _padding1 = 0;
    int32_t _padding2 = 0;
};
static_assert(sizeof(DriftOverride) == 8,
              "DriftOverride must be 8 bytes (cache-line packs 8 entries per line)");

// Branchless bit accessors (multi-bit-state-encoding-pattern.md API style):
inline bool    drift_ovr_has(uint8_t flags)          { return  flags        & 0x01; }
inline uint8_t drift_ovr_severity(uint8_t flags)     { return (flags >> 1)  & 0x01; }
inline uint8_t drift_ovr_category(uint8_t flags)     { return (flags >> 2)  & 0x01; }
inline uint8_t drift_ovr_compare_kind(uint8_t flags) { return (flags >> 3)  & 0x03; }

// Sparse eps values table (only used by EPS_CUSTOM compare_kind):
inline constexpr double g_drift_custom_eps[] = {
    /* [0] */ 1e-9,    // EPS_DEFAULT fallback
    /* [1] */ 1e-3,    // xgb_subsample / xgb_colsample_bytree (XGBoost subsample fraction tolerance)
    /* [2] */ 1e-12,   // future tight-precision fields
};
```

### Sidecar registry declaration

**Note on array shape (per C4 decision at `.F.4d` ship; see Option D above):** the `.F.4d` first canonical uses SPLIT sidecars per registry scope (`g_global_drift_overrides[FIELD_IDX_GLOBAL_END]` + `g_per_core_drift_overrides[FIELD_IDX_PER_CORE_END]`) because the cfg registry is split into global + per-node at `.F.4c`. Pedagogical code blocks below show a singular `g_drift_overrides[FIELD_IDX_END]` form for teaching clarity; production code should split per Option D.

```cpp
// CoreFrameworks/CfgFieldDriftOverride.hpp
//
// Tuple: X(field_name_token, SEVERITY_TOKEN, CATEGORY_TOKEN, COMPARE_KIND_TOKEN, eps_idx)
// First canonical row list (matches HEAD CfgDriftCheckRegistry.hpp:202-221 at `.F.4d` ship):
#define FOREACH_DRIFT_OVERRIDE(X) \
    X(xgb_subsample,        WARN_ALWAYS, CROSS_BINARY, EPS_DEFAULT, 0) \
    X(xgb_colsample_bytree, WARN_ALWAYS, CROSS_BINARY, EPS_DEFAULT, 0) \
    X(xgb_min_child_weight, WARN_ALWAYS, CROSS_BINARY, EXACT,       0) \
    X(xgb_seed,             WARN_ALWAYS, CROSS_BINARY, EXACT,       0) \
    X(xgb_tree_method,      WARN_ALWAYS, CROSS_BINARY, STRING,      0)

// Pedagogical singular-array form (production uses split per Option D + C4 decision):
// Auto-generate dense g_drift_overrides[FIELD_IDX_END] sparse array:
#define EMIT_DRIFT_OVERRIDE_INIT(name, severity, category, compare, eps) \
    [FIELD_IDX_##name] = {                                               \
        .flags = (1 << 0)                                /* has_override */ \
               | ((DRIFT_SEVERITY_##severity)  << 1)                       \
               | ((DRIFT_CATEGORY_##category)  << 2)                       \
               | ((DRIFT_COMPARE_##compare)    << 3),                      \
        .eps_idx = (eps),                                                  \
    },

inline DriftOverride g_drift_overrides[FIELD_IDX_END] = {
    FOREACH_DRIFT_OVERRIDE(EMIT_DRIFT_OVERRIDE_INIT)
};
```

### AUTOPOPULATE consumer dispatching via sidecar

```cpp
// CFG_DRIFT_AUTOPOPULATE walks STAMP_BOUND derived filter + dispatches via sidecar lookup.
// Standard cases: defaults. Custom cases: override values from sidecar.

#define EMIT_CFG_DRIFT_CHECK(idx, desc) \
    do { \
        const DriftOverride& ovr = g_drift_overrides[idx]; \
        uint8_t override_mask = -(uint64_t)drift_ovr_has(ovr.flags); \
        uint8_t severity = (drift_ovr_severity(ovr.flags) & override_mask) \
                         | (DRIFT_SEVERITY_REFUSE_STRICT & ~override_mask); \
        uint8_t category = (drift_ovr_category(ovr.flags) & override_mask) \
                         | (DRIFT_CATEGORY_INFERENCE_CFG & ~override_mask); \
        /* ... per-row drift check using severity + category ... */ \
    } while (0);

STAMP_BOUND_CFG_walk_filtered_rows(g_cfg_field_descriptors, FIELD_IDX_END,
                                    +emit_drift_check_lambda, &drift_ctx);
```

### CI cross-check (H18 invariant)

```cpp
void test_drift_override_sidecar_coverage() {
    // Forward: every row in FOREACH_DRIFT_OVERRIDE must have its parent in FOREACH_CFG_FIELD
    // with STAMP_BOUND metadata bit set.
    #define VERIFY_OVERRIDE_PARENT(name, ...) \
        check("sidecar row " #name " parent has STAMP_BOUND bit", \
              (g_cfg_field_descriptors[FIELD_IDX_##name].metadata_flags \
               & CfgFieldDescriptor::STAMP_BOUND) != 0);
    FOREACH_DRIFT_OVERRIDE(VERIFY_OVERRIDE_PARENT)
    #undef VERIFY_OVERRIDE_PARENT

    // Reverse: count of g_drift_overrides[i] entries with has_override=1 must match
    // FOREACH_DRIFT_OVERRIDE row count.
    size_t override_count_actual = 0;
    for (size_t i = 0; i < FIELD_IDX_END; i++) {
        if (drift_ovr_has(g_drift_overrides[i].flags)) override_count_actual++;
    }
    check("sidecar registry row count matches actual",
          override_count_actual == FOREACH_DRIFT_OVERRIDE_COUNT);
}
```

---

## Trade-offs + when to apply

### Apply when:
- Parent registry has standard-case auto-flow (AUTOPOPULATE-driven dispatch)
- 10-30% of parent rows need custom semantics that don't fit the standard mold
- Custom semantics can be captured in a compact override struct (~5-10 bytes per override)
- Adding new custom rows must NOT require parent-registry schema changes

### Skip when:
- All parent rows follow the same pattern (no overrides needed → pure AUTOPOPULATE)
- Custom semantics are too heterogeneous to fit a uniform override struct (consider Option C function-pointer column then; but rare)
- Custom rows >50% of parent registry (parent registry itself probably needs splitting; sidecar's value erodes)

### Cost:
- Sidecar struct + bit-packed flags: ~30 LOC (1 struct + accessors)
- Sidecar registry declaration + AUTOPOPULATE init: ~30 LOC (handles ~5-10 override rows)
- Dense sidecar array (FIELD_IDX_END entries; mostly zero): negligible memory cost (~2KB for 213 fields × 8 bytes)
- Consumer AUTOPOPULATE walker: ~50 LOC (replaces wide-variant manual walker)
- CI cross-check test: ~30 LOC

Net: ~140 LOC NEW. Versus wide-variant approach: ~250 LOC of FOREACH_CFG_DRIFT_CHECK + manual walker; net SAVINGS of ~110 LOC + Class 21 closure.

### Win:
- Single source of truth at parent registry (FOREACH_CFG_FIELD with STAMP_BOUND bit)
- Custom-semantics rows ~10% of total; sidecar is small + focused
- Class 21 extinct at auto-flow-with-overrides surface
- Future custom additions: 1 row in sidecar (~5 min)
- Wide-variant CfgDriftCheckRegistry can be DELETED (TECH_DEBT-059)

---

## Reference implementations

### v5.15.5.F.4d (FIRST canonical application — pending ship)

- `CoreFrameworks/CfgFieldDriftOverride.hpp` (NEW file; ~150 LOC including sidecar registry + accessors + CI test)
- `FOREACH_DRIFT_OVERRIDE` with 5 entries (5 XGBoost hyperparameter fields needing WARN_ALWAYS + CROSS_BINARY + tight epsilon)
- `CFG_DRIFT_AUTOPOPULATE` walks STAMP_BOUND derived filter (per `metadata-bit-driven-derived-filter-framework.md`) + dispatches via sidecar lookup
- Replaces `ML_Headers/CfgDriftCheckRegistry.hpp` wide-variant (19-entry registry; superseded). Wide-variant gets DEPRECATION note (TECH_DEBT-059) at `.F.4d` ship + actual deletion after migration verified.
- Branchless dispatch at override-vs-default selection (mask compute per § (3) in Caramel's design walkthrough; .F.4d DOD-discipline refactor).

### Future application catalog (6 surfaces planned)

| Application | Parent registry | Override columns | Status |
|---|---|---|---|
| Drift override (`.F.4d` canonical) | FOREACH_CFG_FIELD (STAMP_BOUND filter) | severity + category + compare_kind + eps_idx | **Stage 3 ACTIVE v1.0** (landed `.F.4d` ship close 2026-05-16) |
| Custom strategy gating | FOREACH_STRATEGY | gate_fn_ptr for non-default gates | v5.16+ |
| Custom feature NaN validation | FOREACH_FEATURE | validator_fn_ptr + range overrides | v5.16+ |
| Custom cfg rendering | FOREACH_CFG_FIELD (any metadata bit) | render_fn_ptr for non-default widgets | v5.15.6.C+ |
| Custom failure-mode escalation | FOREACH_FAILURE_MODE | escalation_kind (counter / paged-alert) | v5.16+ |
| Custom slow-path-gate evaluation | FOREACH_SLOW_PATH_GATE | multi_condition_fn_ptr | v5.16+ |

Pattern lifecycle:
- Stage 2 (DRAFT) — this doc; pending ship
- Stage 3 (first reference) — `.F.4d` FOREACH_DRIFT_OVERRIDE application (custom-semantics override sidecar; sparse 5/213 rows for XGBoost cohort)
- **Stage 4 (cohort migration) — landed at `v5.15.5.F.4d.1.B` with `FOREACH_DRIFT_GATE`** (cohort gate dispatch sidecar; sparse ~15/24 STAMP_BOUND_CFG_DERIVED rows; sister to FOREACH_DRIFT_OVERRIDE; different concern, same shape). **Codifies per-concern separation discipline** — see § "Per-concern separation: multiple sidecars per distinct concern" below.
- Stage 5 (CLAUDE.md item promotion) — when 3rd application emerges (e.g., custom strategy gating at v5.16+ OR GUI gate dispatch at v5.15.6+), codify as full CLAUDE.md item

---

## Per-concern separation: multiple sidecars per distinct concern (Stage 4 codification 2026-05-16)

**Codified at `v5.15.5.F.4d.1` planning** with `FOREACH_DRIFT_GATE` (cohort gate dispatch sidecar at `.B`) as 2nd canonical application of the sidecar pattern, sister to `FOREACH_DRIFT_OVERRIDE` (custom-semantics override sidecar at `.C`).

### The principle

When multiple distinct ADDING-pattern concerns exist over the same parent registry, **each concern gets its own sidecar — NOT stacked into one** "god sidecar" with bit-packed handling of multiple concerns.

Concrete contrast at `v5.15.5.F.4d.1`:

| Concern | Sidecar | Sparseness | Default semantic | Bit-pack |
|---|---|---|---|---|
| Custom-semantics override for drift compare (5 XGBoost training-only rows need WARN_ALWAYS + CROSS_BINARY) | `FOREACH_DRIFT_OVERRIDE` at `.C` | ~5/213 (truly sparse) | `has_override=0` → use defaults | `DriftOverride.flags` = severity + category + compare_kind |
| Cohort gate dispatch for drift gate (~15/24 STAMP_BOUND_CFG_DERIVED rows need non-Default cohort tag) | `FOREACH_DRIFT_GATE` at `.B` | ~15/24 (semi-dense within flagged subset) | unset entry → `DRIFT_GATE_DEFAULT` cohort | `DriftGateKind` enum (single value per row) |

Both sidecars are indexed by parent's `FIELD_IDX`. Both follow the same pattern shape. Different concerns; different sparseness profiles; different default semantics.

### Why NOT stack into one sidecar

Tempting to merge: extend `DriftOverride.flags` with cohort_gate_kind bits (3 bits within the existing reserved bits 5-7). Why this is the wrong shape:

1. **Conflates two distinct concerns.** Override semantics (severity + category) and cohort gate (which cfg state gates the field) are independent dimensions. A field could need WARN_ALWAYS override AND be in the bandit cohort — both apply, but they're orthogonal. Conflating means every consumer disentangles two concerns from one byte.

2. **Sparseness profile mismatch.** DRIFT_OVERRIDE is truly sparse (5/213, ~2.3%); DRIFT_GATE is semi-dense within the flagged subset (15/24, 62%). Forcing them into one sidecar means rows that need cohort gate but NO override-semantics get sparse-table entries just for the cohort tag. Sparse pattern degrades.

3. **Future extension stacks badly.** When 3rd cohort-style concern emerges (e.g., per-row render-conditional GUI gating at `.F.4e`; or `.F.5+` backtest-conditional behavior), stacking into one sidecar consumes more bit budget in `DriftOverride.flags` (currently 5 bits used; 3 reserved → would saturate fast). Per-concern separation = ADD new sister sidecar (`FOREACH_GUI_GATE`, `FOREACH_BACKTEST_GATE`) without disrupting existing.

4. **CI verification independence.** Each sidecar gets its own forward + reverse coverage cross-check (sister to `test_drift_override_sidecar_coverage`). Conflating concerns means CI check has to disentangle which concern's coverage gap fired.

5. **Test isolation.** Each sidecar's behavior is testable independently (gate dispatch tests + override dispatch tests, separate). Conflated mode requires coupled tests.

### When to add a NEW sidecar vs extend existing

**Add NEW sidecar when:**
- The new data dimension is semantically independent of existing sidecar's dimensions (different concern)
- The new data dimension has a different sparseness profile (sparse vs semi-dense vs dense)
- The new data dimension's default semantic differs from existing (default-on-zero means different things)

**Extend existing sidecar when:**
- The new data is an additional facet of the same concern (e.g., adding `eps_idx` to `DriftOverride.flags` because eps tolerance is part of drift semantics)
- The new data has matching sparseness profile + default-on-zero semantic
- The new data dimension is naturally bit-pack-able alongside existing fields without saturating budget

### CI cross-check applies per sidecar

Each sidecar gets its own forward + reverse coverage check:

```cpp
// Per sidecar: forward (every sidecar row's parent has the required source-registry bit set)
// Per sidecar: reverse (every flagged source-registry row has expected coverage in sidecar OR explicit default)
```

For FOREACH_DRIFT_OVERRIDE: forward = "every override row's parent has STAMP_BOUND_CFG_DERIVED bit"; reverse = sparse (most rows DON'T need override; default-on-zero is correct).

For FOREACH_DRIFT_GATE: forward = "every gate row's parent has STAMP_BOUND_CFG_DERIVED bit"; reverse = "every STAMP_BOUND_CFG_DERIVED row has an explicit gate tag OR uses DEFAULT (no row in FOREACH_DRIFT_GATE)".

### Composition relationships

- **Same parent registry** (`FOREACH_CFG_FIELD` filtered by `STAMP_BOUND_CFG_DERIVED`)
- **Different consumers** (DRIFT_OVERRIDE consumed by drift-check severity / category selection; DRIFT_GATE consumed by drift-check gate predicate)
- **Independent CI cross-checks** (each forward + reverse, per sidecar)
- **Sister meta-registry enrollment** (both as Level-0 with PARENT=DERIVED_FILTER in `FOREACH_REGISTRY`)
- **Sister `multi-bit-state-encoding-pattern.md` applications** (DriftOverride.flags + DriftGateKind enum both bit-packed where appropriate)

### Future cohort applications

When 3rd sidecar emerges, it should follow the same shape:
- Sparse / semi-dense sidecar indexed by parent's FIELD_IDX
- Default-on-zero semantic (or default-on-absence-of-row)
- Bit-packed struct OR enum tag (multi-bit-state-encoding-pattern.md)
- CI cross-check forward + reverse
- Enrolled in FOREACH_REGISTRY (LEVEL=0; PARENT=parent-meta-registry)
- Concrete examples: FOREACH_GUI_GATE (`.F.4e+`); FOREACH_BACKTEST_GATE (`v5.16+`); FOREACH_TRAINING_GATE (`v5.15.6.C+`)

---

## Lessons / gotchas

### Sidecar is INDEXED BY parent's FIELD_IDX

Direct array access `g_drift_overrides[FIELD_IDX_X]` is branchless O(1). No hash table; no linear scan. Dense array (most entries zero-init via `{0}`); FIELD_IDX_END = ~213; memory cost ~2KB for 8-byte sidecar struct. Cache-friendly.

### Default-on-zero is the discipline

`DriftOverride` default value (all fields 0; `has_override = 0`) signals "use defaults." Custom rows set `has_override = 1` + populate override values. Consumer code reads the lookup; if `has_override == 0`, uses default constants. Branchless dispatch via mask compute (cost equivalent to branched at boot/load-time path).

### Multi-bit state encoding for flags packing

Per CLAUDE.md item 30 + DESIGN_PHILOSOPHY § 4 bit-packing bullet: pack severity (1 bit) + category (1 bit) + compare_kind (2 bits) + has_override (1 bit) = 5 bits into single uint8_t. Avoids the anti-pattern `struct { uint8_t severity; uint8_t category; uint8_t mode; uint8_t _pad; }` (4 bytes wasted on what fits in 5 bits).

### Sparse eps values via separate table

For EPS_CUSTOM compare_kind: store `eps_idx` (1 byte) in sidecar; index into a separate `g_drift_custom_eps[]` constexpr table (only ~5 unique values across all custom rows). Beats per-row inline double (8 bytes per row × 213 rows = 1.7KB) AND beats per-row hash lookup (eliminates indirection).

### Wide-variant deprecation path (TECH_DEBT-059)

Replacing the wide-variant CfgDriftCheckRegistry requires:
1. Cohort migrate (`.F.4d` ship): FOREACH_DRIFT_OVERRIDE absorbs custom-semantics rows; FOREACH_CFG_FIELD STAMP_BOUND filter handles standard cases via AUTOPOPULATE.
2. Verify CI cross-check tests pass (forward + reverse coverage between FOREACH_DRIFT_OVERRIDE and FOREACH_CFG_FIELD).
3. Add DEPRECATION note to `stamp-vs-runtime-drift-detection-registry.md` § "Wide variant" (TECH_DEBT-059; post-ship).
4. Future ship: actually delete `CfgDriftCheckRegistry.hpp` + remove manual walker.

The narrow variant `FOREACH_ARCH_FIELD_DRIFT` STAYS — different surface (architectural fields, not cfg). Wide-variant pattern itself remains valid for OTHER non-cfg drift surfaces.

### Composition with derived filter framework

Sidecar pattern naturally composes with metadata-bit-driven-derived-filter-framework: the derived filter's walker dispatches via sidecar lookup. Both patterns together = single-source-of-truth at parent registry + cohort-style consumer walk + per-row customization via small sidecar.

---

## Patterns NOT used here (and why)

### `std::unordered_map<FieldIdx, DriftOverride>` sparse lookup

Heap allocation. NOT ALLOWED on hot/slow/drainer/boot paths per H1.

### Linear scan over FOREACH_DRIFT_OVERRIDE per consumer call

Branchless O(1) array access is better than O(N) linear scan even at boot/load-time.

### Inheriting from wide-variant pattern with per-row default-suppression

Considered: keep wide-variant registry; mark some rows as `DEFAULT_SUPPRESSED` so consumer skips them when sidecar has override. Rejected — still parallel registry (Class 21); doesn't reduce maintenance cost.

---

## Cross-references

- `autopopulate-pattern-for-production-caller-class.md` (CLAUDE.md item 21) — standard-case auto-flow companion
- `metadata-bit-driven-derived-filter-framework.md` — sidecar naturally pairs with derived filters
- `x-macro-registry-with-presence-dispatch.md` — parent registry pattern
- `bitmap-flag-api.md` — DriftOverride flags packing
- `multi-bit-state-encoding-pattern.md` (CLAUDE.md item 30) — DriftOverride as canonical application (3rd application; INVARIANT promotion at `.F.4d`)
- `struct-padding-determinism-pattern.md` (CLAUDE.md item 27) — DriftOverride explicit padding fields
- `stamp-vs-runtime-drift-detection-registry.md` — wide-variant supersession; narrow variant unchanged
- `registry-tuple-as-single-source-of-truth.md` — sidecar is purely additive; parent registry stays SoT
- `pattern-codification-lifecycle.md` — Stage 2 → 3 at `.F.4d` ship
- `DOCS/DESIGN_PHILOSOPHY.md` § 1.5 (Framework discipline) + § 7 (Structural-fix family)
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 21 (Multiple parallel descriptors — closed at auto-flow-with-overrides surface)
- CLAUDE.md item 31 (Framework-driven extensibility)
- H18 (custom-semantics via sidecar; STRONG initially, HARD after 2nd cohort application — pending codification at `.F.4d` ship)
- TECH_DEBT-059 (wide-variant `CfgDriftCheckRegistry` DEPRECATION post-`.F.4d`)
