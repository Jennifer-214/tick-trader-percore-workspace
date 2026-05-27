---
name: feedback-cfg-field-categorization-at-registry-add-time
description: "When adding a new cfg field row to any FOREACH_*_CFG_FIELD registry, explicitly declare conceptual nature (PER_CORE_MODE_NO_FLAT_FIELD vs PER_CORE_FLAT_SYNC_PARAMETER vs GLOBAL_ONLY) + apply canonical pattern per category. Also applies to RE-CATEGORIZATION migration (multi-step; partial migration creates orphan state worse than original)."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 37c74114-8590-473f-993e-3dcf0f784339
---

**At cfg field row-add time, categorize by conceptual nature, not field-name taxonomy.** Decision tree:

1. **PER_CORE_MODE_NO_FLAT_FIELD** — each core EXPLICITLY picks per-core (no uniform default makes sense). Apply NO_FLAT_FIELD bit + FOREACH_PER_CORE_NO_FLAT_FIELD_SYNC sister registry entry. Canonical example: `strategy` (CfgFieldRegistry.hpp:682) — each core has different strategy.

2. **PER_CORE_FLAT_SYNC_PARAMETER** — operator wants uniform default + per-core override exception. Default for per-core registry rows WITHOUT NO_FLAT_FIELD bit. Walker propagation via EMIT_PER_CORE_COPY auto-flows global → all cores[c]. Per-core override syntax requires PER_CORE_OVERRIDE_INT_FIELDS macro membership (currently 3 fields: poll_interval + risk_degradation_curve + barrier_blend_mode). Canonical examples: regime_hysteresis + exit_threshold (per-core PARAMETERS with uniform default + sparse per-core overrides).

3. **GLOBAL_ONLY** — engine-wide; no per-core variation. FOREACH_GLOBAL_CFG_FIELD membership. Canonical: pay_fees_in_bnb, num_execution_cores, kill_recovery_warmup (post-Cx-D extension at v5.15.5.F.4d.1.B.4 v1.7.6).

4. **CFG-FLAG BITMAP BIT** — BOOL-semantic field; H14 bit-packing discipline. Add to FOREACH_RISK_CFG_FLAG / FOREACH_GATE_CFG_FLAG / FOREACH_LIFECYCLE_CFG_FLAG / FOREACH_ML_CFG_FLAG / FOREACH_OPS_CFG_FLAG (5 domains). NEVER use uint32_t/uint8_t/int scalar for BOOL-typed cfg fields. Canonical: MASK_RISK_CFG_KILL_SWITCH_ENABLED + MASK_RISK_CFG_MTM_KILL_SWITCH_ENABLED + MASK_RISK_CFG_SL_COOLDOWN_ADAPTIVE_ENABLED (post-Cx-T/U H14 migrations at v5.15.5.F.4d.1.B.4 v1.7.6).

## Re-categorization migration (5-step procedure)

**When discovering a field is in wrong registry category, the migration must be COMPLETE — partial migration creates worse architectural state than original:**

1. DELETE row in wrong-category registry
2. ADD row in right-category registry (with operational default as registry payload per Registry default precedence v1.1)
3. DELETE/ADD manual struct field per H17 status at target surface (global surface H17 STRONG; per-core surface H17 STRONG)
4. DELETE manual init line (auto-populates from registry default via EMIT_GLOBAL_CFG_DEFAULT or EMIT_PER_CORE_CFG_DEFAULT_GLOBAL_MIRROR walker)
5. UPDATE consumers if access pattern changes (global → per-core read or vice versa)

**Partial migration anti-pattern:** Just step 1 (delete wrong-category row) leaves field in "orphan" state — declarations exist without registry coverage; defaults via manual init only; future contributor sees ambiguous pattern. WORSE than original.

## How to apply

**When adding new cfg field row:**

Apply 5-question consumer-pattern verification (sister to feedback_categorize_by_consumer_pattern_not_field_name):

1. What macro family is the field in?
2. Does the field have a global manual struct field?
3. What's the walker behavior at this row?
4. What consumer reads exist + scope of each?
5. Does the field have per-core override syntax?

Decide category based on consumer-pattern analysis, NOT field-name taxonomy.

## Recognition markers

- Adding new cfg field row to any FOREACH_*_CFG_FIELD registry
- Discovering field is in wrong registry category (re-categorization candidate)
- Reviewing existing cfg field for H14 compliance (BOOL → bitmap migration)
- Reviewing existing cfg field for H17 STRONG→HARD progression at global surface
- Operator question about cfg field placement / behavior

## Sister memories

- [[feedback_categorize_by_consumer_pattern_not_field_name]] — sub-discipline (5-question consumer-pattern verification)
- [[feedback_audit_canonical_sister_before_new_infra]] — DESIGN_SPECS cross-ref before recommending
- [[feedback_no_defer_for_effort]] — re-categorization must be COMPLETE; partial is worse than nothing

## Worked examples

**v5.15.5.F.4d.1.B.4 v1.7.6 cycle (codification cycle):**

- **regime_hysteresis** + **exit_threshold**: PER_CORE_FLAT_SYNC_PARAMETER (correctly categorized; cosmetic consumer fix for Class 25 scope-discipline at EngineCommon.hpp:618)
- **sl_cooldown_cycles** + **kill_recovery_warmup** + **sl_cooldown_base/extra** + **idle_reset_cycles** + **model_max_age_hours** + **lazy_rebuild_price_threshold_pct**: 7 fields RE-CATEGORIZED from PER_CORE_FLAT_SYNC_PARAMETER (wrong) to GLOBAL_ONLY (correct) — full 5-step migration applied per Cx-D extension
- **enable_mtm_kill_switch** + **sl_cooldown_adaptive**: 2 fields RE-CATEGORIZED from PER_CORE_FLAT_SYNC_PARAMETER scalar uint32/int (H14 violation) to CFG-FLAG BITMAP BIT in risk_cfg_flags (correct) — full migration applied per Cx-T/U

Each migration applied 5-step procedure; no orphan-state partial migrations.

## DESIGN_SPECS sister

- `framework-patterns/cfg-field-categorization-discipline.md` (NEW Stage 2 DRAFT at v5.15.5.F.4d.1.B.4 v1.7.6) — canonical decision tree + worked examples
- `framework-patterns/universal-cfg-field-registry-pattern.md` § Registry default precedence v1.1 — manual init vs registry payload resolution procedure
- `framework-patterns/cfg-derived-consumer-framework.md` — consumer-side discipline
- `framework-patterns/manual-fields-inventory-pattern.md` — vestigial manual field cleanup

## CI Check 8 (M7 4th canonical)

`tools/check_per_core_registry_integrity.py` extended with 5-question /consumer-pattern-verify check at COMMIT layer:
- Flag A: per-core registry row with 0 per-core consumers
- Flag B: per-core consumer reading global cfg field where per-core registry exists
- Flag C: per-core registry row without NO_FLAT_FIELD bit AND without global manual struct field

## When this rule applies

Per feedback_categorical_triggers_over_hardcoded_refs:

- Any cfg field row addition to any FOREACH_*_CFG_FIELD registry
- Any cfg field re-categorization migration (wrong category → right category)
- Any plan body proposing cfg field architectural change
- Any audit catching wrong-categorization pattern
- Any DOD audit / H14 / H17 cleanup at cfg field surface
