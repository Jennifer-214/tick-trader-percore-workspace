---
name: feedback-prefer-action-parameterized-walker-over-per-consumer-walker-bodies
description: "When ≥2 consumer template fns walk the same registry cohort with different per-row actions, prefer action-parameterized meta-walker over per-consumer per-registry walker bodies. Drift impossible by construction; meta-macro = single source of truth for cohort coverage."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b025c86a-fb34-4d41-a80b-15461b4ca5ff
  sister_specs: [feedback_structural_fix_for_recurring_class.md, feedback_audit_canonical_sister_before_new_infra.md, feedback_enumerate_consumers_before_registry_row_deletion.md, feedback_proportionate_response_to_audit_findings.md, feedback_framework_layer_payoff_diminishing_returns.md]
  tags: [framework-discipline, refactor-discipline]
---

When **≥2 consumer template fns walk the same registry cohort** with different per-row actions (e.g., populate / emit / drift-check / parse over the same N cfg registries with same metadata-bit filter), prefer **action-parameterized meta-walker** macro family over per-consumer per-registry walker bodies. The meta-walker is the single source of truth for cohort coverage; consumer can't omit a registry because the meta-macro expands to all N FOREACH invocations unconditionally + per-consumer X-macros must exist by `BASE##_<SCOPE>` naming convention for the meta-walker expansion to compile cleanly.

**Why:** Sister-consumer asymmetric registry-coverage drift caught at `v5.15.5.F.4d.1.B.3` Session E (2026-05-18). 4 cfg-derived consumer template fns at `MemHeaders/CfgGateRegistry.hpp` drifted from each other across `.B.1`/`.B.2`/`.B.3` incremental ship-by-ship extension. `populate_inference_cfg_from_derived` walked only per-core + global; `drift_check_from_derived` walked only per-core + global + ml_cfg_flag; `populate_stamp_cfg_from_derived` + `parse_stamp_cfg_to_derived` walked all 4. Missing walkers cause silent stamp-binding gaps for cohort fields → Class 21 instance at consumer template fn level. Per-consumer manual sister-extension patches THIS instance only; recurrence vectors persist:

1. **New consumer template fn added** — author must remember to walk all N registries; discipline-dependent
2. **New registry added to the cohort** — all existing consumers need new walker; discipline-dependent
3. **New metadata bit activates a new cohort** — new family of consumers needs same coverage discipline

Structural fix via action-parameterized meta-walker prevents the bug class. The pattern matches the Class 18/21 closure precedent at v5.14.2.E.1 (`EnsembleModelZoo_PostLoadSetup` + `CoreModelZoo_PostLoadSetup` + `FOREACH_ENSEMBLE_POST_LOAD` / `FOREACH_SINGLE_ZOO_POST_LOAD`): ONE single source of truth + many consumer views that walk it uniformly + compile-time enforced inclusion at all sites + bypass impossible.

**How to apply:**

1. **Recognition trigger:** ≥2 consumer template fns walking the same registry cohort with different per-row actions. Drift signal: one consumer walks N of K registries; sister walks M of K (M ≠ N) at HEAD. Even if both started symmetric, incremental ship-by-ship registry additions tend to drift coverage.

2. **Build meta-walker:**
   ```cpp
   #define FOREACH_<COHORT>_COHORT(BASE_X)                  \
       FOREACH_<R1>(BASE_X##_<S1>)                          \
       FOREACH_<R2>(BASE_X##_<S2>)                          \
       /* ... one per registry in the cohort ... */         \
       FOREACH_<RN>(BASE_X##_<SN>)
   ```
   Place at the cfg-derived-consumer header (same scope as the consumer template fns).

3. **Per-consumer X-macro family:** Each consumer defines N X-macros following `X_<base>_<scope>` convention. Function-scope `#define` / `#undef` bracket if X-macros reference local context (inf, cfg, handle vars). File-scope if unconditional (struct-field declaration).

4. **Enroll meta-walker in `FOREACH_REGISTRY`** at appropriate Level + parent per H15 + H19 (typically Level 1 with parent FOREACH_REGISTRY; sister to FOREACH_PER_CORE_DOMAIN_BITMAP meta-registry shape).

5. **Sister meta-walker for struct-gen:** If the cohort has a struct-gen meta-walker (e.g., `STAMP_RESULT_DERIVED_FIELDS_AUTO_GEN`), refactor to use the same meta-walker via `FOREACH_<COHORT>_COHORT(_<STRUCT_PREFIX>)`. Unifies struct-gen + consumer template fns under one cohort-coverage source of truth.

**First canonical reference:** `FOREACH_STAMP_BOUND_DERIVED_COHORT(BASE_X)` at `MemHeaders/CfgGateRegistry.hpp` (v5.15.5.F.4d.1.B.3 Step 1.6.5b 2026-05-18); covers 5 sites (4 cfg-derived consumer template fns + `STAMP_RESULT_DERIVED_FIELDS_AUTO_GEN` struct-gen meta-walker) over 4 cfg registries (per_core + global + ml_cfg_flag + gate_cfg_flag) filtered by `STAMP_BOUND_CFG_DERIVED` metadata bit.

**When to skip:**

- Single consumer template fn over a registry cohort (no sister; meta-walker is overkill — use W1 single-registry walker per `cfg-derived-consumer-framework.md` § "Single consumer concern")
- Consumers walking DIFFERENT cohorts (e.g., one walks cfg fields; sister walks model-const fields — separate cohorts get separate meta-walkers)
- Runtime-idx-only access sufficient (use W2 `CFG_FIELD_FOR_EACH_SET_BIT` per `cfg-derived-consumer-framework.md` walker dichotomy)

**Sister memories:**

- [[feedback_structural_fix_for_recurring_class]] — parent meta-rule (the recurrence-class structural-fix discipline; this memory applies it to consumer-cohort walker shape)
- [[feedback_audit_canonical_sister_before_new_infra]] — sister-extension producer-side discipline (companion: this memory is the consumer-side discipline; both together prevent producer/consumer drift)
- [[feedback_enumerate_consumers_before_registry_row_deletion]] — consumer enumeration discipline at deletion time (this memory's complement: action-parameterized walker prevents consumer-side drift at producer-side cohort GROWTH)
- [[feedback_proportionate_response_to_audit_findings]] — option D ARCHITECT (when audit catches sister-consumer drift, this is the canonical structural fix shape; proportionate-response evaluation should weigh A/B/C alternatives honestly first per the expanded menu)
- [[feedback_framework_layer_payoff_diminishing_returns]] — inflection-point check (this pattern earns its place in consolidation phase; question its addition past inflection; do NOT proliferate meta-walkers for every cohort just because the pattern exists)

**Related anti-patterns:**

- `DOCS/RECURRING_BUG_PATTERNS.md` Class 21 (Multiple parallel descriptors for similar surfaces) — bug class this pattern closes at consumer template fn surface
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 18 STRENGTHENED (call-sequence enumeration for mirror plans) — sister bug class; meta-walker prevents call-sequence drift across consumer fns
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 14 (plan calls function/struct field that doesn't exist) — sister bug class; meta-walker enforces existence of all N consumer X-macros at compile time

**Cross-references:**

- `DESIGN_SPECS/framework-patterns/cfg-derived-consumer-framework.md` v1.2 — canonical doc for the pattern (§ "Action-parameterized meta-walker for cohort consumer template fns")
- `DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md` § INLINE MERGE — proportionate-response option C (FOLD into canonical sister); meta-walker absorbs the "FOLD" shape at consumer cohort level
- `DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md` — parent pattern (production-caller class extinction); meta-walker is the multi-consumer-cohort extension at the walker-family level
- `DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md` § Y3 dispatch — token-paste-by-name dispatch mechanism; meta-walker uses Y3-shape token-paste for per-scope X-macro dispatch
- v5.14.2.E.1 PostLoadSetup precedent — Class 18/21 closure at boot/backtest/hot-swap surfaces with same shape (single source of truth + many consumer views + compile-time enforcement)
