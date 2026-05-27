---
name: feedback-categorize-by-consumer-pattern-not-field-name
description: "When categorizing a cfg field's architectural placement (PER_CORE_MODE_NO_FLAT_FIELD vs PER_CORE_FLAT_SYNC_PARAMETER vs GLOBAL_ONLY), categorize by CONSUMER-pattern dependency (walker behavior + override macro membership + actual production reader patterns), NOT by field-name taxonomy. Stage 2 DRAFT (single instance v1.7.6; promote to Stage 3 at 2nd canonical per pattern-codification-lifecycle.md)."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 37c74114-8590-473f-993e-3dcf0f784339
---

**Field-name taxonomy is NOT a substitute for consumer-pattern analysis when categorizing cfg fields.** Two fields with similar names can have entirely different correct categorizations based on:
1. What walkers process the field (NO_FLAT_FIELD bit / FOREACH_GLOBAL vs FOREACH_PER_CORE registry membership)
2. Whether per-core override syntax exists (PER_CORE_OVERRIDE_INT_FIELDS macro membership)
3. Actual production reader patterns (`cfg.X` global vs `cfg.cores[c].X` per-core scope)
4. Conceptual nature (per-core MODE vs per-core PARAMETER vs global-uniform)

**Why:** Codified Stage 2 DRAFT 2026-05-27 at v5.15.5.F.4d.1.B.4 v1.7.6 cycle. Initial Path 1 analysis concluded regime_hysteresis + exit_threshold + sl_cooldown_cycles should use NO_FLAT_FIELD pattern (sister to `strategy` row precedent). Mistake: equated field-name taxonomy (per-core registry membership) with architectural categorization (NO_FLAT_FIELD = MODE-only pattern).

Actual code analysis revealed:
- `strategy` (NO_FLAT_FIELD) is per-core MODE — operator EXPLICITLY picks per core; "all cores use ML" isn't typical
- `regime_hysteresis` is per-core PARAMETER — operator wants uniform default + per-core override exception
- These look similar in registry but have OPPOSITE operator UX patterns

The NO_FLAT_FIELD migration would have BROKEN operator UX (forced explicit `core_N_X=Y` for uniform case) for ZERO correctness benefit.

## How to apply

**When categorizing a cfg field (initial placement OR re-categorization):**

Apply 5-question consumer-pattern verification (sister to /precoding-audit-gate Stage 4 + CI Check 8 mechanical check):

1. **What macro family is the field in?** FOREACH_PER_CORE_CFG_FIELD / FOREACH_GLOBAL_CFG_FIELD / PER_CORE_OVERRIDE_INT_FIELDS / FOREACH_*_CFG_FLAG bitmap?
2. **Does the field have a global manual struct field?** (yes = load-bearing for EMIT_PER_CORE_COPY walker propagation; no = NO_FLAT_FIELD candidate)
3. **What's the walker behavior at this row?** NO_FLAT_FIELD bit → skip propagation; default → copy resolved.X to all cores[c].X
4. **What consumer reads exist + scope of each?** `cfg.X` global / `cfg.cores[c].X` per-core / `core_cfg->X` resolved per-core / `ctrl->config.X` legacy single-core
5. **Does the field have per-core override syntax?** PER_CORE_OVERRIDE_INT_FIELDS macro membership (only 3 fields currently: poll_interval + risk_degradation_curve + barrier_blend_mode)

**Categorization decision:**

- **PER_CORE_MODE_NO_FLAT_FIELD** — operator explicitly picks per core (no uniform default); sister to `strategy` row at CfgFieldRegistry.hpp:682. NO_FLAT_FIELD bit + FOREACH_PER_CORE_NO_FLAT_FIELD_SYNC sister registry entry.
- **PER_CORE_FLAT_SYNC_PARAMETER** — operator sets global default; walker propagates to all cores; optional per-core override via PER_CORE_OVERRIDE_INT_FIELDS. Default pattern for per-core registry rows WITHOUT NO_FLAT_FIELD bit.
- **GLOBAL_ONLY** — engine-wide; no per-core variation; FOREACH_GLOBAL_CFG_FIELD membership. Sister to manual-fields-inventory-pattern.md for legacy field migration.

## Recognition markers

- Adding new cfg field row to any FOREACH_*_CFG_FIELD registry
- Discovering field is in wrong registry category (re-categorization migration)
- Reviewing field-name taxonomy as architectural decision (RED FLAG — verify with consumer-pattern analysis instead)

## Sister memories

- [[feedback_cfg_field_categorization_at_registry_add_time]] — parent rule (3-category taxonomy)
- [[feedback_audit_canonical_sister_before_new_infra]] — DESIGN_SPECS cross-ref before recommending
- [[feedback_operator_pushback_as_audit_signal]] — sister discipline; operator pushback IS the verification signal
- [[feedback_iteration_spiral_signals_audit_meta_gap]] — recognition trigger when field-name reasoning produces 3+ amendment cycles

## Worked example

v5.15.5.F.4d.1.B.4 v1.7.6 cycle Path 1 framing error:

- **Field-name taxonomy reasoning (WRONG):** regime_hysteresis is per-core registry row → similar to `strategy` per-core registry row → apply NO_FLAT_FIELD migration
- **Consumer-pattern analysis (CORRECT):** regime_hysteresis is a PARAMETER (integer threshold; operator wants uniform default); strategy is a MODE (discrete enum; operator explicitly picks per core). PER_CORE_FLAT_SYNC_PARAMETER pattern, NOT NO_FLAT_FIELD pattern.

5-question check would have caught Path 1 error at planning surface:
1. Macro family: FOREACH_PER_CORE_CFG_FIELD without NO_FLAT_FIELD bit (DEFAULT category = PER_CORE_FLAT_SYNC_PARAMETER)
2. Global manual struct field? YES at ControllerConfig.hpp:463 (load-bearing for walker)
3. Walker behavior? EMIT_PER_CORE_COPY propagates global → all cores[c]
4. Consumer reads? Per-core scope at EngineCommon.hpp:199 (correct); legacy single_core at PortfolioController.hpp:358 (acceptable; reads global)
5. Per-core override syntax? NO (not in PER_CORE_OVERRIDE_INT_FIELDS)

Conclusion: PER_CORE_FLAT_SYNC_PARAMETER (existing walker propagation is canonical). NO_FLAT_FIELD migration would have BROKEN operator UX.

## Stage progression

- Stage 2 DRAFT: 2026-05-27 codification (single instance — this cycle's Path 1 framing error)
- Stage 3 promotion: pending 2nd canonical instance per `pattern-codification-lifecycle.md` 2-instance Recurrence trigger

## When this rule applies

Per feedback_categorical_triggers_over_hardcoded_refs:

- Any cfg field architectural placement decision
- Any cfg field re-categorization migration
- Any plan body proposing cfg field changes
- Any audit catching "wrong categorization" pattern
