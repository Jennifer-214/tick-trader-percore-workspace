---
name: audit-canonical-sister-before-new-infra
description: "Before proposing new framework infrastructure (X-macro registry / metadata bit / dispatch table / sidecar / consumer macro), grep codebase for canonical sister patterns. If sister exists, extend it rather than build parallel. Closes Path γ-class structural critiques pre-coding."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e52d563e-1fb7-4ce4-ac68-6b9fa4608fec
  sister_specs: [feedback_plans_cite_sister_registry_inspection.md, project_anti_spaghetti_audit_cadence.md, feedback_consult_on_audit_findings.md, feedback_overengineering_boundary_when_future_easier.md, feedback_structural_fix_for_recurring_class.md, feedback_categorize_by_consumer_pattern_not_field_name.md, feedback_cfg_field_categorization_at_registry_add_time.md, feedback_enumerate_consumers_before_registry_row_deletion.md, feedback_enumerate_helper_signature_args_before_extract.md, feedback_new_plans_use_future_oriented_template.md, feedback_operator_pushback_as_audit_signal.md, feedback_prefer_action_parameterized_walker_over_per_consumer_walker_bodies.md, feedback_proactive_novel_alternative_consideration.md, feedback_recheck_designspecs_on_pushback.md, feedback_single_source_of_truth_discipline.md, feedback_sister_cohort_amendment_completeness.md, feedback_test_change_enumeration_per_plan_body.md, feedback_tiered_audit_discipline_per_plan_scope.md, feedback_train_serve_execution_layer_meta_gap.md, feedback_verify_symbol_existence_at_plan_drafting_time.md]
  tags: [audit-methodology, framework-discipline, structural-fix]
---

Before proposing any new framework infrastructure — X-macro registry, metadata bit, dispatch table, sidecar registry, consumer macro, AUTOPOPULATE-style walker — audit the codebase for canonical sister patterns. If a sister exists with the same conceptual surface, EXTEND it; do not build parallel.

**Why:** Path γ-class structural critiques caught twice in a row at pre-coding audit gate 2026-05-16 (`.A`) + 2026-05-17 (`.B`). Both incidents: plan proposed parallel infrastructure when canonical sister already existed in code. At `.A`: proposed `DerivedFilterFramework.hpp` parallel walker macros; canonical `FOREACH_METADATA_BIT` + `cfg_compute_mask` + `CFG_FIELD_FOR_EACH_SET_BIT` existed at `CfgFieldRegistry.hpp:1020-1159` since `.F.4c.3`. At `.B`: proposed β4 `FOREACH_DRIFT_GATE` sparse sidecar (~80 LOC + DriftGateKind + dispatch table); canonical `FOREACH_CFG_DERIVED_INFERENCE_CFG` existed at `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101-123` with 93% row overlap (β4 plan even MISSED the 5th BANDIT_THOMPSON field that was already in canonical at line 113 — direct evidence of duplication-induced drift). Both incidents share the same shape: build parallel when canonical exists → Class 14/18/21 instances produced + drift surface created. Pre-coding audit gate catches them but only if discipline is applied; codify so future plans don't have to be caught.

**How to apply:**
- Trigger: any plan body proposing FOREACH_X(X) new registry / new metadata bit row / new dispatch table / new sidecar / new consumer macro
- Action: BEFORE writing the proposed new infrastructure, grep codebase for:
  - Same concern keyword (cfg / stamp / drift / model-const / filter)
  - Same row-content shape (3-tuple `(name, expr, gate)`, 4-tuple `(name, type, format, default)`, etc.)
  - Same consumer behavior pattern (AUTOPOPULATE walker, walk-and-emit, walk-and-check)
- Per candidate sister found, ask:
  1. Same conceptual surface? (Y/N)
  2. >=50% projected row name overlap? (Y/N)
  3. Same consumer behavior pattern? (Y/N)
  - If Y to ≥2 of 3 → **FOLD** (extend the sister; don't build parallel)
  - If Y to 1 only → consider; might be distinct concern
  - If N to all → **NO-FOLD** (legitimately new infrastructure; document rationale)
- Plan body MUST include "Canonical sister registries considered" section with per-candidate fold/no-fold verdict + rationale
- Pre-coding audit gate's `/merge-scan` + `/anti-spaghetti` fire on this dimension
- Caught at this stage = scope amendment before `pre-<tag>` rollback anchor created

**Sister rules:**
- [[feedback_plans_cite_sister_registry_inspection]] (plan body discipline)
- [[project_anti_spaghetti_audit_cadence]] (periodic audit cadence)
- [[feedback_consult_on_audit_findings]] (consult on audit findings before coding)
- [[feedback_overengineering_boundary_when_future_easier]] (pick harder when future easier — extending canonical is harder now / much easier forever)
- [[feedback_structural_fix_for_recurring_class]] (closes Class 14/18/21 structurally)

**Codified at:** 2026-05-17 (v5.15.5.F.4d.1.B.1 planning); `DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md` Stage 2 DRAFT → Stage 3 first reference at `.B.1` ship.
