---
check_id: 44
title: Cfg field categorization verification (plan-time)
parent_skill: /readiness
established: 2026-05-27
sister_specs:
  - DESIGN_SPECS/framework-patterns/cfg-field-categorization-discipline.md
  - DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md
sister_memories:
  - feedback_cfg_field_categorization_at_registry_add_time
  - feedback_categorize_by_consumer_pattern_not_field_name
codified_at: v5.15.5.F.4d.1.B.4 v1.7.6 Phase Cx-J
---

# /readiness Check 44 — Cfg field categorization verification

## What this check does

When plan body proposes adding NEW cfg field row OR re-categorizing existing cfg field, verifies:

1. **Conceptual nature declared explicitly** — plan body states which of 4 categories: PER_CORE_MODE_NO_FLAT_FIELD / PER_CORE_FLAT_SYNC_PARAMETER / GLOBAL_ONLY / CFG-FLAG BITMAP BIT (per `cfg-field-categorization-discipline.md` decision tree)
2. **Sister-pattern co-location checked** — if field name has `enable_X`/`use_X`/`X_enabled` pattern, plan body confirms grep of MASK_*_X_ENABLED across all 5 cfg-flag bitmap domains
3. **5-step migration procedure applied for re-categorization** — plan body enumerates all 5 steps (delete wrong-category row + add right-category + delete/add manual struct + delete manual init + update consumers if scope changes)
4. **DOD discipline checks applied** — plan body confirms H6 cache layout + H14 bit-packing + H7/H20 branchless dispatch + single-source-of-truth
5. **5-question consumer-pattern verify** — sister to CI Check 8 mechanical check; plan-time application

## Trigger

Plan body contains any of:
- `FOREACH_*_CFG_FIELD(X)` row addition
- `MASK_*_*_ENABLED` bit addition
- "migrate <field> to <registry>" phrasing
- "delete <field> manual struct" phrasing
- New cfg field declaration on ControllerConfig<F>
- Operator-facing cfg key addition (e.g., `<field>=value` in cfg files)

## Procedure

For each cfg field touched by plan body, verify:

### Question 1: Conceptual nature

Plan body must explicitly state ONE of:
- PER_CORE_MODE_NO_FLAT_FIELD (each core EXPLICITLY picks; no uniform default)
- PER_CORE_FLAT_SYNC_PARAMETER (uniform default + per-core override)
- GLOBAL_ONLY (engine-wide; no per-core variation)
- CFG-FLAG BITMAP BIT (BOOL semantic; H14 bit-packing)

NOT acceptable: "per-core" alone (which category?) OR "global" alone (vs cfg-flag bitmap?) OR no categorization stated.

### Question 2: Sister-pattern check

If field name pattern matches `enable_X` / `use_X` / `X_enabled`:
- Plan body must show grep output of `MASK_*_X_ENABLED` across `CoreFrameworks/RiskCfgFlagRegistry.hpp` + `GateCfgFlagRegistry.hpp` + `LifecycleCfgFlagRegistry.hpp` + `MlCfgFlagRegistry.hpp` + `OpsCfgFlagRegistry.hpp`
- If sister exists in any domain: plan body must justify co-location decision OR explain why separate

### Question 3: Re-categorization 5-step (if applicable)

If plan body proposes re-categorization (delete from one registry, add to another):
- Step 1: DELETE row in wrong-category registry — enumerated?
- Step 2: ADD row in right-category registry with operational default — enumerated?
- Step 3: DELETE/ADD manual struct field per H17 status — enumerated?
- Step 4: DELETE manual init line — enumerated?
- Step 5: UPDATE consumers if access pattern changes — enumerated?

Missing any step → BLOCK plan; partial migration creates orphan state.

### Question 4: DOD checks

Per `cfg-field-categorization-discipline.md` § DOD audit at cfg field placement:
- BOOL-semantic field in scalar registry → FLAG H14 violation; recommend CFG-FLAG BITMAP BIT category
- Hot-path read field with non-cache-friendly placement → FLAG H6 review
- Per-tick data-dependent dispatch via branch → FLAG H7/H20; recommend fn pointer table OR bitmap-mask-select

### Question 5: Consumer-pattern verify (sister to CI Check 8)

Plan body must answer 5 mechanical questions per field:
1. What macro family is the field in?
2. Does the field have a global manual struct field?
3. What's the walker behavior at this row?
4. What consumer reads exist + scope of each?
5. Does the field have per-core override syntax?

If plan body can't answer any → BLOCK plan; not ready for coding.

## Output

For each cfg field touched: PASS / YELLOW (warning with remediation) / RED (block).

Aggregate verdict:
- All PASS → /readiness Check 44 GREEN
- Any YELLOW → /readiness Check 44 YELLOW (resolve before coding OR document acceptance)
- Any RED → /readiness Check 44 RED (block plan amendment)

## Sister checks

- Check 32 (B-Plus CI tool symbol-existence verification at plan-drafting time) — sister mechanical check
- Check 33 (M6 body-content arg enumeration completeness) — sister mechanical check at function-extract surface
- Check 34 (audit_tier frontmatter + scope match) — parent tiered-audit discipline
- Check 35/36/37 (B14/B15/operator-doc cohort sidecars) — sister Phase D bookkeeping checks
- Check 41/42/43 (B-Plus v0.4 generator + B14/B15 audit-time checks) — sister cohort-enumeration discipline

## CI Check 8 sister (commit-time enforcement)

Check 44 is plan-time enforcement; CI Check 8 (`tools/check_per_core_registry_integrity.py`) is commit-time enforcement of the same discipline. Together: plan-time + commit-time = complete discipline coverage (M7 4th canonical structural enforcement).

## When this check applies

- Any plan body section proposing cfg field addition or modification
- Any re-categorization migration (cohort cleanup ships, H17 progression ships, H14 violation closure ships)
- Any DESIGN_SPEC update touching cfg field surface
- Quarterly /metadata-audit sweep (categorical trigger per `feedback_metadata_audit_quarterly`)
