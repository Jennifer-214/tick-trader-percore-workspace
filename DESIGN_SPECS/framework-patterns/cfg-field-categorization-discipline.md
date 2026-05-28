---
type: framework-pattern
stage: 3-first-canonical
version: 1.1
established: 2026-05-27
promoted_to_stage_3: 2026-05-27
tags: [framework-discipline, data-oriented-design, structural-fix]
surface: [cfg-flow, registry, slow-path]
sister_specs: [universal-cfg-field-registry-pattern.md, cfg-derived-consumer-framework.md, cfg-scope-discipline.md, manual-fields-inventory-pattern.md, decision-time-data-binding-pattern.md]
applies_at_skills: [/readiness, /precoding-audit-gate, /dod-audit, /bug-check]
first_canonical_application: v5.15.5.F.4d.1.B.4 v1.7.6 Phase Cx-cfg-cohort (11 worked instances; promoted Stage 2→3 at .B.4 ship close per canonical pattern-codification-lifecycle.md Stage 3 = first canonical landed)
---

# cfg-field-categorization-discipline

**Stage 3 first-canonical v1.1** — codified 2026-05-27 at v5.15.5.F.4d.1.B.4 v1.7.6 Phase Cx-cfg-cohort closure; promoted Stage 2→3 at .B.4 ship close per canonical pattern-codification-lifecycle.md (Stage 3 = first canonical reference landed; v1.7.6 cycle's 11-worked-instance closure IS the first canonical). Sister to existing `universal-cfg-field-registry-pattern.md` § Registry default precedence v1.1 + `cfg-derived-consumer-framework.md` + `cfg-scope-discipline.md` + `manual-fields-inventory-pattern.md`.

## Problem statement

Cfg fields can be misplaced across registry categories (per-node vs global vs cfg-flag bitmap), creating parallel-mechanism shapes that violate single-source-of-truth + H17 STRONG framework discipline + H14 bit-packing discipline. The v5.15.5.F.4c migration cohort surfaced 11+ instances at v1.7.6 where field-name taxonomy reasoning produced wrong categorization decisions (Class 26 recurrence_count 1→11 at single ship). Discipline missing: explicit decision tree for cfg field placement + 5-step migration procedure for re-categorization + sister-pattern co-location verification.

## The 4 categories

When adding a new cfg field row to any FOREACH_*_CFG_FIELD registry, categorize by conceptual nature (NOT field-name taxonomy):

### Category 1 — PER_CORE_MODE_NO_FLAT_FIELD

**Definition:** Each core EXPLICITLY picks per-node value (no uniform default makes sense).

**Pattern:** Row in `FOREACH_PER_CORE_CFG_FIELD` with `NO_FLAT_FIELD` bit set in meta column + entry in `FOREACH_PER_CORE_NO_FLAT_FIELD_SYNC` sister registry mapping per-node target field to legacy parallel-array source.

**Operator UX:** No top-level cfg key; operator MUST use `core_<N>_<field>=value` for each core.

**Canonical example:** `strategy` row at `CoreFrameworks/CfgFieldRegistry.hpp:682` (first canonical 2026-05-08 at WIP2d-1.B.0). Operator can have core_0=ml + core_1=momentum + core_2=mr; "all cores ML" isn't typical operator intent.

### Category 2 — PER_CORE_FLAT_SYNC_PARAMETER

**Definition:** Operator wants uniform default + per-node override exception. Default for per-node registry rows WITHOUT NO_FLAT_FIELD bit.

**Pattern:** Row in `FOREACH_PER_CORE_CFG_FIELD` without NO_FLAT_FIELD bit; manual global struct field declaration on `ControllerConfig<F>` (load-bearing for `EMIT_PER_CORE_COPY` walker propagation at `ControllerConfig.hpp:1432-1437`); walker auto-propagates `global cfg.X` → all `cfg.cores[c].X` post-parse.

**Per-node override:** Requires `PER_CORE_OVERRIDE_INT_FIELDS` macro membership (only 3 fields currently: `poll_interval` + `risk_degradation_curve` + `barrier_blend_mode`). Operators using `core_<N>_<field>=value` syntax for fields NOT in this macro silently fail (parser doesn't recognize).

**Operator UX:** Operator sets `<field>=value` at top-level; walker propagates. Optional per-node override via `core_<N>_<field>=value` IF field is in PER_CORE_OVERRIDE_INT_FIELDS.

**Canonical example:** `regime_hysteresis` + `exit_threshold` (per-core PARAMETERS at v1.7.6 cycle; uniform default propagated via walker).

### Category 3 — GLOBAL_ONLY

**Definition:** Engine-wide; no per-node variation supported architecturally.

**Pattern:** Row in `FOREACH_GLOBAL_CFG_FIELD`; auto-generated struct field via `EMIT_GLOBAL_CFG_STRUCT_FIELD` walker at `ControllerConfig.hpp:1326`; auto-populated default via `EMIT_GLOBAL_CFG_DEFAULT` walker at `:1477`; parser auto-routed via `EMIT_GLOBAL_CFG_PARSER_CASE` walker at `:2103+`.

**Operator UX:** Operator sets `<field>=value` at top-level. NO per-node override syntax (architecturally unsupported).

**Canonical examples:** `pay_fees_in_bnb`, `num_execution_cores`, `kill_recovery_warmup` + `sl_cooldown_*` + `idle_reset_cycles` + `model_max_age_hours` + `lazy_rebuild_price_threshold_pct` (post-Phase Cx-D extension at v1.7.6).

### Category 4 — CFG-FLAG BITMAP BIT

**Definition:** BOOL-semantic field; H14 bit-packing discipline applies. NEVER use `uint32_t`/`uint8_t`/`int` scalar for BOOL-typed cfg fields.

**Pattern:** Row in one of 5 cfg-flag bitmap domain registries:
- `FOREACH_RISK_CFG_FLAG` — risk / sizing / kill switch safety mechanics
- `FOREACH_GATE_CFG_FLAG` — gate dispatch (no-trade-band, cost-gate, barrier-gate)
- `FOREACH_LIFECYCLE_CFG_FLAG` — partial_exit_enabled / breakeven / lifecycle toggles
- `FOREACH_ML_CFG_FLAG` — ML strategy toggles (use_exit_model, confidence_composite_enabled, etc.)
- `FOREACH_OPS_CFG_FLAG` — operational / drift acknowledgments

Bit access via `BITMAP_IS_SET(cfg.<domain>_cfg_flags, MASK_<DOMAIN>_<NAME>_ENABLED)` per H14 + `bitmap-flag-api.md` primitives.

**Operator UX:** Operator sets `<legacy_field>=1` at top-level (legacy_field column in FOREACH_<DOMAIN>_CFG_FLAG row determines cfg key); parser auto-routes via FOREACH_<DOMAIN>_CFG_FLAG parser walker.

**Canonical examples:** `MASK_RISK_CFG_KILL_SWITCH_ENABLED` (PARITY-026 hotfix) + `MASK_RISK_CFG_MTM_KILL_SWITCH_ENABLED` + `MASK_RISK_CFG_SL_COOLDOWN_ADAPTIVE_ENABLED` (post-Phase Cx-T/U at v1.7.6).

## Decision tree (apply at cfg field row-add time)

For any new cfg field, answer in order:

1. **Is the field BOOL-semantic (true/false / enabled/disabled / on/off)?**
   - YES → **Category 4 CFG-FLAG BITMAP BIT**. Pick appropriate domain (risk/gate/lifecycle/ml/ops); add to FOREACH_<DOMAIN>_CFG_FLAG with `<legacy_field>` column = operator-facing cfg key.
   - NO → continue to question 2.

2. **Is the field engine-wide (no per-node variation makes sense architecturally)?**
   - YES → **Category 3 GLOBAL_ONLY**. Add to FOREACH_GLOBAL_CFG_FIELD.
   - NO → continue to question 3.

3. **Does each core EXPLICITLY pick (no uniform default makes sense)?**
   - YES → **Category 1 PER_CORE_MODE_NO_FLAT_FIELD**. Add to FOREACH_PER_CORE_CFG_FIELD with NO_FLAT_FIELD bit + entry in FOREACH_PER_CORE_NO_FLAT_FIELD_SYNC.
   - NO → continue to question 4.

4. **Does operator want uniform default + per-node override exception?**
   - YES → **Category 2 PER_CORE_FLAT_SYNC_PARAMETER**. Add to FOREACH_PER_CORE_CFG_FIELD WITHOUT NO_FLAT_FIELD bit. If per-node override syntax needed, ALSO add to PER_CORE_OVERRIDE_INT_FIELDS.

## 5-step re-categorization migration procedure

**When discovering a field is in wrong registry category, the migration must be COMPLETE — partial migration creates orphan state worse than original.**

For each field being re-categorized:

1. **DELETE row in wrong-category registry** (FOREACH_PER_CORE_CFG_FIELD or FOREACH_GLOBAL_CFG_FIELD or FOREACH_<DOMAIN>_CFG_FLAG)
2. **ADD row in right-category registry** with operational manual init value as registry payload (per `universal-cfg-field-registry-pattern.md` § Registry default precedence v1.1 — operational defaults preserved as canonical)
3. **DELETE/ADD manual struct field declaration per H17 status at target surface:**
   - Global surface H17 STRONG (FOREACH_GLOBAL_CFG_FIELD(EMIT_GLOBAL_CFG_STRUCT_FIELD) at ControllerConfig.hpp:1326 active): auto-gen IS active → DELETE manual decl when migrating TO FOREACH_GLOBAL_CFG_FIELD (else duplicate-member compile fail)
   - Per-node surface H17 STRONG: auto-gen via FOREACH_PER_CORE_CFG_FIELD(EMIT_PER_CORE_CFG_STRUCT_FIELD); migrating TO per-node registry handles automatically
   - Cfg-flag bitmap: DELETE scalar manual struct field (bitmap bit replaces it)
4. **DELETE manual init line** (auto-populates from registry default via `EMIT_GLOBAL_CFG_DEFAULT` walker OR `EMIT_PER_CORE_CFG_DEFAULT_GLOBAL_MIRROR` walker for per-node-stays OR `<DOMAIN>_CFG_FLAG_AUTOPOPULATE_FROM_*` macro for bitmap)
5. **UPDATE consumers if access pattern changes:**
   - PER_CORE → GLOBAL: consumers already read via global pointer; usually no change
   - PER_CORE → CFG-FLAG BITMAP: consumers change from `config->X` to `BITMAP_IS_SET(config->cfg_flags, MASK_*)`
   - GLOBAL → PER_CORE: consumers add per-node scope; `cfg.X` → `cfg.cores[c].X`

**Partial migration anti-pattern (FORBIDDEN):** Just step 1 (delete wrong-category row) leaves field in "orphan" state — declarations exist without registry coverage; defaults via manual init only; future contributor sees ambiguous pattern. WORSE than original.

## Sister-pattern co-location check

When naming a new cfg field, check if SISTER pattern exists in another cfg-flag bitmap domain:

- Field name starts with `enable_` / `use_` OR ends with `_enabled` → check `MASK_*_<NAME>_ENABLED` existence across all 5 cfg-flag bitmap domain registries
- If sister exists in any domain → co-locate (use same domain bitmap)
- Anti-pattern: putting BOOL field in scalar registry when sister bitmap bit already exists in another domain

**Example:** `enable_mtm_kill_switch` (pre-v1.7.6) was uint32_t scalar despite sister `MASK_RISK_CFG_KILL_SWITCH_ENABLED` already existing in risk_cfg_flags. Discovery: per-cohort audit revealed H14 violation; migrated to `MASK_RISK_CFG_MTM_KILL_SWITCH_ENABLED` (same domain as sister) at Phase Cx-T.

## DOD audit at cfg field placement

Apply DOD discipline checks at cfg field row-add time:

- **H6 cache layout:** Cross-thread access patterns; hot-path vs slow-path placement; alignment requirements
- **H14 bit-packing:** BOOL-semantic fields → cfg-flag bitmap (NEVER scalar)
- **H7 branchless / H20 SP/HP dispatch:** Hot-path data-dependent dispatch via fn pointer table; slow-path branches acceptable
- **Single source of truth:** ONE registry per field; no parallel-mechanism shapes (NEVER manual struct + auto-gen + sidecar of same field name)

## Worked examples — v5.15.5.F.4d.1.B.4 v1.7.6 Phase Cx-cfg-cohort closure

**Category 1 PER_CORE_MODE_NO_FLAT_FIELD examples (existing canonical):**
- `strategy` — sister to NO_FLAT_FIELD pattern landing site at WIP2d-1.B.0

**Category 2 PER_CORE_FLAT_SYNC_PARAMETER examples (codified at v1.7.6):**
- `regime_hysteresis` — operator sets `regime_hysteresis=15` top-level; walker propagates to all cores; consumers read per-node. Cx-A (cosmetic PortfolioController consumer migration to per-node)
- `exit_threshold` — same pattern. Cx-B (cosmetic Class 25 consumer fix at EngineCommon.hpp:618)

**Category 3 GLOBAL_ONLY examples (re-categorized at v1.7.6):**
- `kill_recovery_warmup` + `sl_cooldown_base` + `sl_cooldown_extra` + `sl_cooldown_cycles` + `idle_reset_cycles` + `model_max_age_hours` + `lazy_rebuild_price_threshold_pct` — 7 fields re-categorized from PER_CORE_FLAT_SYNC_PARAMETER (wrong) to GLOBAL_ONLY (correct) at Cx-D extension. 5-step migration applied. Class 26 worked instances bumped recurrence_count 1→11 = MANDATORY structural fix threshold met.

**Category 4 CFG-FLAG BITMAP BIT examples (re-categorized at v1.7.6):**
- `enable_mtm_kill_switch` (H14 violation: was uint32_t scalar) → `MASK_RISK_CFG_MTM_KILL_SWITCH_ENABLED` bit. Cx-T. Default ENABLED (safety-critical sister to KILL_SWITCH_ENABLED).
- `sl_cooldown_adaptive` (H14 violation: was BOOL int scalar) → `MASK_RISK_CFG_SL_COOLDOWN_ADAPTIVE_ENABLED` bit. Cx-U.

## Anti-patterns this prevents

- **Parallel-mechanism shape** — per-node registry membership + global manual field WITHOUT walker propagation = silent per-node override syntax failure
- **Field-name taxonomy categorization** — categorizing by field name pattern instead of conceptual nature + consumer pattern (sister to feedback_categorize_by_consumer_pattern_not_field_name)
- **H14 BOOL-as-scalar** — BOOL semantic in uint32/int scalar instead of cfg-flag bitmap bit
- **Sister-pattern split** — BOOL flag in scalar despite sister `MASK_*_ENABLED` existing in cfg-flag bitmap domain
- **Partial re-categorization** — delete-wrong-category without add-right-category leaves orphan state
- **Vestigial manual init drift** — manual default values diverge from registry payload (Registry default precedence v1.1 § resolution procedure addresses)

## Codification lifecycle

- **Stage 1 RECOGNITION:** 2026-05-27 — Phase Cx-cfg-cohort surface analysis revealed 11+ Class 26 instances + 2 H14 violations cohort
- **Stage 2 DRAFT:** Initial codification at v5.15.5.F.4d.1.B.4 v1.7.6 (v1.0; 2026-05-27)
- **Stage 3 first-canonical:** v5.15.5.F.4d.1.B.4 ship close 2026-05-27 (v1.1) — 11-worked-instance closure landed; promoted at Phase D bookkeeping per canonical pattern-codification-lifecycle.md (Stage 3 = first canonical reference)
- **Stage 4 cohort:** Pending 2nd cohort application at future cfg field row-add / re-categorization migration; CI Check 8 catches violations mechanically; /readiness Check 44 catches at plan-time
- **Stage 5 CLAUDE.md:** Promote to CLAUDE.md "How to..." table once ≥2 codebase applications + DESIGN_SPEC mature
- **Stage 6 cadence-locked:** Future M7 escalation candidate if categorization-error recurs DESPITE codified discipline; structural enforcement via runtime check / pre-tool-call audit

## CI Check 8 (M7 4th canonical sister)

`tools/check_per_core_registry_integrity.py` extended with 5-question /consumer-pattern-verify mechanical check at COMMIT layer:

- **Flag A:** per-node registry row with 0 per-node consumers in production code (catches "wrong registry membership; field is conceptually global")
- **Flag B:** per-node consumer scope reading global cfg field where per-node registry row exists (catches Class 25 "consumer scope-erosion")
- **Flag C:** per-node registry row WITHOUT NO_FLAT_FIELD bit + WITHOUT global manual struct field (catches walker compile-error candidate)

Sister to existing Check 7 (Class 27 cache-structure discipline). M7 4th canonical structural enforcement application (sister to B-Plus v0.2 symbol-existence + v0.3 line-anchor + v0.4 deletion-cohort).

**Consumer-side discipline amendment (v5.15.5.F.4d.1.B.8):** Consumer-side discipline check at registry-add-time should include sister verification that EXISTING consumer sites for a newly-per-node-migrated field are updated to use per-node slot. This is the preventive analog to Check 10 commit-time enforcement (Class 26 sub-shape B UNINDEXED-GLOBAL detection at per-node consumer sites). When a cfg field migrates from GLOBAL → per-node registry, the migration scope MUST include sweep of consumer sites that read the field UNINDEXED — failure to sweep produces silent Class 26 sub-shape B violations (audit-evidence: 4 HIGH instances at `.B.8` from `ea08210` mechanical migration cohort `.F.4c.3` WIP2d-1.B.1 that missed consumer-side sweep). Check 10 catches future regressions mechanically per `tools/check_per_core_registry_integrity.py` Check 10 invocation.

## Cross-references

- `framework-patterns/universal-cfg-field-registry-pattern.md` § Registry default precedence v1.1 — resolution procedure for MATCH/DIFFER cases
- `framework-patterns/cfg-derived-consumer-framework.md` — consumer-side discipline
- `refactor-patterns/cfg-scope-discipline.md` — per-node consumer function signatures (Class 25 closure)
- `refactor-patterns/decision-time-data-binding-pattern.md` — Class 27 closure (sister to Class 26)
- `framework-patterns/manual-fields-inventory-pattern.md` — vestigial manual field cleanup procedure
- `meta-disciplines/structural-enforcement-when-memory-insufficient.md` — M7 framework (CI Check 8 is 4th canonical)
- `memory/feedback_cfg_field_categorization_at_registry_add_time.md` — operator-collaboration sister memory
- `memory/feedback_categorize_by_consumer_pattern_not_field_name.md` — sub-discipline memory (5-question consumer-pattern verification)
- `claude-skills/readiness/checks/check-44-cfg-field-categorization.md` — plan-time enforcement (sister Check landing at v1.7.6)
- `tools/check_per_core_registry_integrity.py` — CI Check 8 commit-time enforcement (M7 4th canonical)

## When this discipline applies

Per `feedback_categorical_triggers_over_hardcoded_refs`:

- Any new cfg field row addition to any FOREACH_*_CFG_FIELD registry
- Any cfg field re-categorization migration (discovered wrong category → right category)
- Any plan body proposing cfg field architectural changes
- Any audit catching wrong-categorization patterns
- Any DOD audit / H14 / H17 cleanup at cfg field surface
- Any sister-pattern discovery (e.g., `enable_X` field while `MASK_*_X_ENABLED` already exists)
