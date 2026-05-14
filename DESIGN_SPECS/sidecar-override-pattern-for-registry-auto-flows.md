# Sidecar override pattern for registry auto-flows

**Established:** 2026-05-14 (v5.15.5.F.4d planning — DRAFT v1.0 pending ship)
**Status:** DRAFT v1.0 (codification Stage 2; first canonical reference application at v5.15.5.F.4d)
**Tags:** structural-fix, registry-driven, framework-discipline; closes Class 21 at auto-flow-with-overrides surface; serves H17; Stage 2 (DRAFT); 0 production applications until `.F.4d` ships

**Cross-references:**
- Parent pattern: `x-macro-registry-with-presence-dispatch.md` (registry-driven dispatch)
- Composes with: `autopopulate-pattern-for-production-caller-class.md` (standard-case auto-flow via AUTOPOPULATE)
- Composes with: `metadata-bit-driven-derived-filter-framework.md` (sidecar typically attaches to a derived filter's parent registry)
- Composes with: `bitmap-flag-api.md` (DriftOverride flags packed per `multi-bit-state-encoding-pattern.md`)
- Supersedes (for cfg-drift surface): `stamp-vs-runtime-drift-detection-registry.md` § "Wide variant" — see TECH_DEBT-059 deprecation
- Closes: Class 21 at auto-flow-with-overrides surface (no parallel wide-variant registries)
- Serves: H17 (custom-semantics overrides via sidecar; no parallel wide-variant registries)
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

#define FOREACH_DRIFT_OVERRIDE(X) \
    X(xgb_subsample,        WARN_ALWAYS, CROSS_BINARY, EPS_TIGHT,  1) \
    X(xgb_eta,              WARN_ALWAYS, CROSS_BINARY, EPS_TIGHT,  2) \
    /* ... 3 more custom entries ... */

// Dense sidecar array indexed by FIELD_IDX (most entries zero):
DriftOverride g_drift_overrides[FIELD_IDX_END] = {0};

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
    /* [1] */ 1e-3,    // xgb_subsample / xgb_colsample_bytree / xgb_gamma
    /* [2] */ 1e-4,    // xgb_eta
    /* [3] */ 1e-12,   // future tight-precision fields
};
```

### Sidecar registry declaration

```cpp
// CoreFrameworks/CfgFieldDriftOverride.hpp
//
// Tuple: X(field_name_token, SEVERITY_TOKEN, CATEGORY_TOKEN, COMPARE_KIND_TOKEN, eps_idx)

#define FOREACH_DRIFT_OVERRIDE(X) \
    X(xgb_subsample,        WARN_ALWAYS, CROSS_BINARY, EPS_TIGHT,  1) \
    X(xgb_eta,              WARN_ALWAYS, CROSS_BINARY, EPS_TIGHT,  2) \
    X(xgb_colsample_bytree, WARN_ALWAYS, CROSS_BINARY, EPS_TIGHT,  1) \
    X(xgb_min_child_weight, WARN_ALWAYS, CROSS_BINARY, EPS_DEFAULT, 0) \
    X(xgb_gamma,            WARN_ALWAYS, CROSS_BINARY, EPS_TIGHT,  1)

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

### CI cross-check (H17 invariant)

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
| Drift override (`.F.4d` canonical) | FOREACH_CFG_FIELD (STAMP_BOUND filter) | severity + category + compare_kind + eps_idx | DRAFT v1.0 |
| Custom strategy gating | FOREACH_STRATEGY | gate_fn_ptr for non-default gates | v5.16+ |
| Custom feature NaN validation | FOREACH_FEATURE | validator_fn_ptr + range overrides | v5.16+ |
| Custom cfg rendering | FOREACH_CFG_FIELD (any metadata bit) | render_fn_ptr for non-default widgets | v5.15.6.C+ |
| Custom failure-mode escalation | FOREACH_FAILURE_MODE | escalation_kind (counter / paged-alert) | v5.16+ |
| Custom slow-path-gate evaluation | FOREACH_SLOW_PATH_GATE | multi_condition_fn_ptr | v5.16+ |

Pattern lifecycle:
- Stage 2 (DRAFT) — this doc; pending ship
- Stage 3 (first reference) — `.F.4d` FOREACH_DRIFT_OVERRIDE application
- Stage 4 (cohort migration) — when 2nd application emerges (e.g., custom strategy gating at v5.16+), promote pattern
- Stage 5 (CLAUDE.md item promotion) — when 3rd application emerges, codify as full CLAUDE.md item

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
- H17 (custom-semantics via sidecar; STRONG initially, HARD after 2nd cohort application — pending codification at `.F.4d` ship)
- TECH_DEBT-059 (wide-variant `CfgDriftCheckRegistry` DEPRECATION post-`.F.4d`)
