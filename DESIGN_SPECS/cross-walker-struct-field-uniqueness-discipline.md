# Cross-walker struct-field uniqueness discipline

**Stage:** Stage 2 DRAFT v1.0 (drafted 2026-05-18 at `.B.3` Step 1.6.3 mid-coding after collision discovery between FOREACH_STAMP_BOUND_MODEL_CONST and master FOREACH_GLOBAL_CFG_FIELD on ModelStampResult)
**Promotes to:** Stage 3 ACTIVE v1.0 at `.B.3` ship close (first canonical reference: H18 SIDECAR EXCLUSION for xgb_min_child_weight / xgb_seed / xgb_train_nthread)
**Sister specs:** `implementation-layer-blindspot-taxonomy.md` § B13 (the taxonomy entry this codifies), `sidecar-override-pattern-for-registry-auto-flows.md` (H18 parent pattern; this is a sibling EXCLUSION variant), `canonical-sister-extension-discipline.md` (M1 sister), `wire-format-byte-preservation-discipline.md` Layer 7 (M2 sister)

---

## Problem statement

A single struct can receive auto-generated fields from MULTIPLE X-macro walkers (e.g., ModelStampResult receives architectural-constants fields from FOREACH_STAMP_BOUND_MODEL_CONST AND cfg-derived fields from STAMP_RESULT_DERIVED_FIELDS_AUTO_GEN walking master cfg registries). When two walkers generate fields with the SAME NAME, struct holds duplicate member declarations → compile error.

The collision can arise from:
- **Legitimate dual semantics:** same field NAME with two semantically distinct usages (e.g., `xgb_seed` as "training-time architectural constant recorded in stamp" via MODEL_CONST AND "runtime cfg value operator can change" via master cfg)
- **Drift:** field accidentally added to two registries; needs consolidation

When the semantics are legitimately distinct, REMOVING from one registry would LOSE the dual-source semantic. When the semantics are drift, REMOVING is correct cleanup. The discipline must distinguish + handle both.

**Distinct from sister patterns:**
- Pillar B2 catches collision WITHIN single walker scope (4 master cfg registries unified into one struct via single walker)
- B13 (this discipline) catches collision ACROSS DIFFERENT walkers contributing to same struct

---

## The pattern

### Detection (automated)

CI tool `tools/check_struct_field_uniqueness.py`:
1. Enumerate ALL X-macro registries that generate struct fields anywhere in the codebase (master cfg + MODEL_CONST sub-registries + future struct-shape registries)
2. Pairwise intersect field-name sets across walker pairs
3. For each detected collision, verify name appears in an H18 SIDECAR EXCLUSION sparse sidecar registered for the relevant struct
4. CI fail if any collision is unregistered

### Resolution (when collision is legitimate dual-semantic)

**H18 SIDECAR EXCLUSION sparse sidecar:**

```cpp
// In CfgGateRegistry.hpp or relevant framework header:
#define FOREACH_<TARGET_STRUCT>_FIELD_EXCLUSION(X) \
    X(name_1) \
    X(name_2) \
    X(name_3)
```

Each entry = one colliding name. Sparse list maintained alongside the walker definitions.

**Redirect bracket at struct site:**

```cpp
struct TargetStruct {
    // ... fields from walker A ...
    
    // EXCLUSION REDIRECT: redirect colliding names to dead-prefixed during walker B expansion.
    // Per H18 SIDECAR EXCLUSION + Pillar B13. Real fields come from walker A (preserved semantic).
    #define name_1 _target_struct_excluded_name_1
    #define name_2 _target_struct_excluded_name_2
    #define name_3 _target_struct_excluded_name_3
    WALKER_B_AUTO_GEN()
    #undef name_1
    #undef name_2
    #undef name_3
};
```

Excluded names get redirected to dead-prefixed fields (~16 bytes wasted each). Real fields come from walker A walker. Semantic preserved on both sides; struct compiles.

### Resolution (when collision is drift)

If two registries encode the SAME semantic (genuine duplicate), consolidate:
1. Identify canonical home (master cfg vs architectural-constants)
2. Remove from non-canonical registry
3. Wire format SOFT bump (per `wire-format-byte-preservation-discipline.md`) if wire emit position shifts
4. Parser back-compat for legacy stamps (per Decision F SOFT compat pattern)

**Discipline question:** "Is this dual-source semantic legitimate, or accidental drift?" The CI tool surfaces collisions; operator judges per case.

---

## When to apply

Apply when:
- Adding a NEW X-macro walker that auto-generates struct fields on a struct that ALREADY has another walker
- Adding a NEW field to a registry where the same field name might exist in another struct-generating registry
- Detected collision via build failure or `tools/check_struct_field_uniqueness.py` CI tool

Skip when:
- Single walker per struct (no cross-walker scope)
- Field names are guaranteed-unique by convention (e.g., domain-prefixed naming)

---

## First canonical application

`.B.3` Step 1.6.3 (2026-05-18) — `FOREACH_STAMP_RESULT_FIELD_EXCLUSION` sidecar in CfgGateRegistry.hpp:

```cpp
#define FOREACH_STAMP_RESULT_FIELD_EXCLUSION(X) \
    X(xgb_min_child_weight) \
    X(xgb_seed)             \
    X(xgb_train_nthread)
```

Resolved 3 collisions between:
- FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG (architectural constants emit; training-time recorded values)
- FOREACH_GLOBAL_CFG_FIELD (master cfg; runtime cfg values)

Both registries are SEMANTICALLY DISTINCT — training-time-recorded vs runtime-tunable. Sidecar exclusion preserves both; ModelStampResult holds training-time values via MODEL_CONST walker (real fields), master walker emits dead-prefixed (no semantic loss).

CI tool `check_struct_field_uniqueness.py` mechanically verifies all 3 collisions are in sidecar.

---

## Anti-patterns to avoid

- **Bulk-remove duplicate-named fields from one registry** — Registries may encode legitimately distinct semantics (training-time vs runtime). Investigation per collision required before consolidation.
- **Sidecar-without-CI** — Manual sidecar maintenance drifts; future collisions silently bypass. CI tool enforces.
- **Single struct receiving fields from too many walkers** — More walkers = more potential collisions + more registry maintenance. Use sidecar exclusion sparingly; structural simplification preferred when registries can be consolidated.
- **Treating B13 as B2** — B2 is single-walker / cross-registry collision; B13 is cross-walker / single-target collision. Different detection scope.

---

## Composition with sister disciplines

- `sidecar-override-pattern-for-registry-auto-flows.md` (H18 parent pattern) — exclusion sidecar IS a sparse override variant
- `metadata-bit-driven-derived-filter-framework.md` § Option E — the FILTER alternative (compile-time subset enumeration via metadata bit); would be cleaner IF C++ supported conditional member decls at struct scope. C++17 doesn't; exclusion sidecar is the workable compromise
- `canonical-sister-extension-discipline.md` (M1) — sister parity verification when extending a registry; B13 catches a different class (cross-walker collision)
- `implementation-layer-blindspot-taxonomy.md` § B13 — the taxonomy registry where this discipline lives

---

## Cross-references

- `implementation-layer-blindspot-taxonomy.md` § B13 (canonical taxonomy entry)
- `tools/check_struct_field_uniqueness.py` — CI tool enforcing the discipline
- `/readiness` Check 40 — plan-time verification
- `feedback_implementation_detail_blindspot_recovery_via_taxonomy` (memory rule) — discipline trigger
- CLAUDE.md H18 — sparse sidecar override pattern (parent)
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 14 — related (fictional symbol prevention)

---

**Stage 2 DRAFT v1.0 — committed 2026-05-18 ahead of `.B.3` ship close.** Promotes to Stage 3 ACTIVE v1.0 at `.B.3` ship close once first canonical application lands (FOREACH_STAMP_RESULT_FIELD_EXCLUSION at CfgGateRegistry.hpp).
