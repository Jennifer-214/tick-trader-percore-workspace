# /merge-scan META-SELF-AUDIT — v5.15.5.F.4d.1.B.1 framework consolidation amendment

**Date:** 2026-05-17
**Target:** `.B.1` plan body v1.0 + sidecar v1.0 (Path γ #2 correction itself)
**Question:** Does the Path γ #2 correction introduce NEW parallel infrastructure (Path γ #3)?

---

## Top-line verdict: **YELLOW** (one DUPLICATE detected + four minor concerns)

**One genuine duplication uncovered (Path γ #3-class):** the FOREACH_CFG_GATE sparse sidecar **duplicates an existing canonical** — the `gate_when` 8th column of `FOREACH_CFG_DRIFT_CHECK` at `ML_Headers/CfgDriftCheckRegistry.hpp:194-322` + the 3rd column of `FOREACH_CFG_DERIVED_INFERENCE_CFG` at `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101-123`. Both encode `(row_name → gate_when_expr)`. The amendment fails its own discipline (`canonical-sister-extension-discipline.md`) by not citing this in a "Canonical sister registries considered" section.

Path γ #2 correction direction is CORRECT (eliminate β4 + walk master cfg field registry + tt:: dispatch). But the SHAPE of the FOREACH_CFG_GATE sidecar replicates rather than extends the inline gate_when convention proven across 3 prior canonicals. RECONSIDER recommended.

Other items are non-duplications (sister patterns codifying genuinely-new structural shapes).

---

## Finding F1 — FOREACH_CFG_GATE (HIGH severity / RECONSIDER) — sidecar duplicates inline gate_when convention

**Plan claim:** `FOREACH_CFG_GATE` is "first canonical of gate-type sidecar; sister to FOREACH_DRIFT_OVERRIDE planned at `.C` which is severity-type".

**VERIFIED at HEAD:** The inline `gate_when` column shape ALREADY exists at:
- `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101-123` — tuple `X(name, cfg_extraction_expr, gate_when)` with 14 rows of `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)` style expressions inline
- `ML_Headers/CfgDriftCheckRegistry.hpp:194-322` — `FOREACH_CFG_DRIFT_CHECK` 10-col tuple with `gate_when` as 8th column; ~18 entries with inline `STAMP_HAS(*h, inference_cfg)` / `BITMAP_IS_SET(...)` expressions
- `MemHeaders/OmsFieldRegistry.hpp` AUTOPOPULATE rows — `emit_when` boolean column inline

**Sister registry inspection MISSING from plan body.** Per `feedback_plans_cite_sister_registry_inspection.md` discipline (codified at THIS planning cycle), plan body MUST include "Canonical sister registries considered" section with per-candidate fold/no-fold verdict. `.B.1` plan body has NO such section. Self-violation.

**Structural critique:** Adding a SEPARATE sparse FOREACH_CFG_GATE sidecar when 3 prior canonicals encode gate_when inline = same structural shape as Path γ #2 (β4 sparse sidecar duplicating inline column convention). The "sister to FOREACH_DRIFT_OVERRIDE" framing is rhetorical — FOREACH_DRIFT_OVERRIDE encodes 5 OVERRIDE FIELDS (severity + category + compare_kind + eps_idx + has_override flag); a per-row gate_when_expr is conceptually a SINGLE-COLUMN annotation, naturally inline.

**Alternative direction (FOLD):** add `gate_when` column to the master cfg field registry tuple OR add metadata column to `FOREACH_METADATA_BIT` row (currently 2-col `(lname, BITNAME)`; would extend to `(lname, BITNAME, default_gate)`) OR keep gate_when inline at the cohort source (the row that flags STAMP_BOUND_CFG_DERIVED already has all context for its own gate_when).

**Severity rationale:** HIGH because (a) the amendment self-violates the discipline it codifies; (b) the structural shape (sparse sidecar for single-column annotation) is EXACTLY what `.B.1` plan claims to be eliminating from β4. RECONSIDER, don't ship as drafted.

---

## Finding F2 — 3 consumer macros (MEDIUM / KEEP with caveat) — distinct concerns but naming drift

**Plan claim:** INFERENCE_CFG_POPULATE_FROM_DERIVED + STAMP_CFG_POPULATE_FROM_DERIVED + DRIFT_CHECK_AUTOPOPULATE are "sister to existing STAMP_CFG_AUTOPOPULATE + INFERENCE_CFG_AUTOPOPULATE".

**VERIFIED:**
- `STAMP_CFG_AUTOPOPULATE` at `ML_Headers/StampBoundCfgRegistry.hpp:226-232` — production cfg→inf populate via FOREACH_STAMP_BOUND_CFG walk
- `INFERENCE_CFG_AUTOPOPULATE` at `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:148-152` — production cfg→inf populate via FOREACH_CFG_DERIVED_INFERENCE_CFG walk

Per `autopopulate-pattern-for-production-caller-class.md` § "3 applications" + 5-application precedent (STAMP/MODEL_CONST/INFERENCE/OMS_INIT/OMS_RESET + LIFECYCLE_CFG_FLAG), the proposed 3 new consumer macros are:

1. **INFERENCE_CFG_POPULATE_FROM_DERIVED** — populate inf struct fields (DISTINCT consumer concern from STAMP_CFG_POPULATE_FROM_DERIVED). KEEP.
2. **STAMP_CFG_POPULATE_FROM_DERIVED** — emit canonical body bytes for HMAC chain (DISTINCT from inf populate). KEEP. CRIT-2 closure structurally requires this.
3. **DRIFT_CHECK_AUTOPOPULATE** — per-row drift compare (DISTINCT from populate). KEEP. Walker shape mirrors `CoreModelZoo_ValidateAgainstCfg<F,LogFn>` consumer at `CoreFrameworks/ModelValidation.hpp`.

**Naming drift concern:** Two macros use suffix `_POPULATE_FROM_DERIVED` (verbose, explains mechanism); one uses suffix `_AUTOPOPULATE` (matches family convention). Inconsistent. RECOMMEND uniform naming: either all `_AUTOPOPULATE` (matches existing convention) or all `_FROM_DERIVED` (descriptive but breaks family pattern). KEEP all three; rename for symmetry.

---

## Finding F3 — 3 tt:: helpers (LOW / KEEP) — genuinely distinct concerns

**Plan claim:** `tt::cfg_emit_field<T>` + `tt::cfg_populate_inf_field<T>` + `tt::cfg_drift_compare<T>` are distinct from existing `tt::cfg_save_field<T>` + `tt::cfg_parse_field<T>`.

**VERIFIED at `CoreFrameworks/CfgFieldDispatch.hpp` (4 existing tt:: helpers):**
- `tt::cfg_parse_field<T>` (text → typed; LC_NUMERIC pinned)
- `tt::cfg_save_field<T>` (typed → text; LC_NUMERIC pinned)
- `tt::cfg_assign_field<T>` (default → typed)
- `tt::cfg_diff_field<T>` (typed vs default → bool)

Proposed 3 new helpers:
- `tt::cfg_emit_field<T>` — wire-format HMAC body bytes (typed → wire format); plan sidecar correctly notes Layer 2 locale pin per ModelInference.hpp:1697 precedent
- `tt::cfg_populate_inf_field<T>` — cfg → inf struct (typed → typed write to different struct)
- `tt::cfg_drift_compare<T>` — stamp value vs cfg value comparison

**Genuinely distinct from save/parse/assign/diff.** KEEP. However:

**Minor concern — `cfg_save_field` vs `cfg_emit_field` overlap:** both convert typed → text with locale pin. The difference is BUFFER FORMAT (cfg file vs HMAC wire format) — different format strings (`%.4f` vs canonical body keys). Genuinely distinct, but PLAN BODY SHOULD CITE the `cfg_save_field` precedent explicitly to demonstrate the inspection was done.

---

## Finding F4 — 2 NEW DESIGN_SPECs (LOW / KEEP) — sister discipline with distinct purpose

**Plan claim:**
- `canonical-sister-extension-discipline.md` is sister to existing `structural-fix-preferred-decision-framework.md`
- `cfg-derived-consumer-framework.md` is composition layer over `metadata-bit-driven-derived-filter-framework.md`

**VERIFIED:**
- `structural-fix-preferred-decision-framework.md` (2026-05-09) — meta-framework: when to apply structural fix vs direct patch (4-step decision algorithm: identify shape → check recurrence → upfront-cost weighing → enabling pattern lookup)
- `canonical-sister-extension-discipline.md` (NEW Stage 2 DRAFT) — narrower discipline: BEFORE proposing new infrastructure, grep for canonical sister. Operates at plan-time PRE-coding-gate.

Genuinely distinct: structural-fix-preferred operates at BUG-CLASSIFICATION-time (a bug is present; decide direct vs structural); canonical-sister-extension operates at INFRASTRUCTURE-PROPOSAL-time (no bug yet; decide build new vs extend canonical). Different triggers, different applications. KEEP.

`cfg-derived-consumer-framework.md` is a composition-layer doc citing `metadata-bit-driven-derived-filter-framework.md` + `sidecar-override-pattern-for-registry-auto-flows.md` + `type-trait-dispatch-via-tt-namespace.md`. Not duplicate — composition narrative. KEEP.

---

## Finding F5 — 3 NEW memory files + 3 going-forward rules (LOW / KEEP) — sister discipline

**Plan claim:** `feedback_audit_canonical_sister_before_new_infra.md` is sister to existing `feedback_structural_fix_for_recurring_class.md`.

**VERIFIED:** `feedback_structural_fix_for_recurring_class.md` operates at BUG-FIX-time (audit surfaces recurring pattern → prefer X-macro/helper over direct patch). `feedback_audit_canonical_sister_before_new_infra.md` operates at INFRASTRUCTURE-PROPOSAL-time (audit codebase before building new). Distinct triggers; complementary disciplines. KEEP.

`feedback_plans_cite_sister_registry_inspection.md` — adds plan-body section requirement (`/readiness` Check 29 new). Distinct discipline. KEEP.

`project_anti_spaghetti_audit_cadence.md` — first of its kind (periodic codebase-wide audit cadence). KEEP.

**However:** The new rules already EXIST in memory dir (verified — `feedback_audit_canonical_sister_before_new_infra.md` is 7-day-old memory). The amendment claims them as "NEW going-forward rules at this ship" but they're already codified. Plan body Step 8 says "Commit 3 new memory files" — that work is ALREADY DONE per existing memory. Mechanical edit needed: rephrase Step 8 as "verify existing memory files persist + add 3 going-forward rule lines to CLAUDE.local.md if missing".

---

## Finding F6 — Self-violation: plan body missing "Canonical sister registries considered" section (HIGH)

The plan body codifies the discipline (`feedback_plans_cite_sister_registry_inspection.md`) requiring this section. The plan body itself DOES NOT INCLUDE the section. Self-violation; ship-blocker per the discipline's own ship-blocker clause.

**Required addition to plan body header:**

```markdown
## Canonical sister registries considered

| Candidate sister | Existing at | Fold/no-fold verdict | Rationale |
|---|---|---|---|
| FOREACH_CFG_DERIVED_INFERENCE_CFG | MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101-123 | ELIMINATE | Path γ #2 closure; 93% overlap with master |
| FOREACH_CFG_DRIFT_CHECK | ML_Headers/CfgDriftCheckRegistry.hpp:194-322 | EXTEND OR ELIMINATE | gate_when 8th column; consumer migrates to walker |
| FOREACH_DRIFT_OVERRIDE (.C planned) | per `sidecar-override-pattern-for-registry-auto-flows.md` | NO-FOLD distinct concern | severity/category override vs gate annotation |
| FOREACH_METADATA_BIT | CoreFrameworks/CfgFieldRegistry.hpp:1064-1075 | EXTEND | could carry default_gate column for new behaviors |
| STAMP_CFG_AUTOPOPULATE | ML_Headers/StampBoundCfgRegistry.hpp:226-232 | RETAIN | wraps consumer-side (legacy path until .B.3) |
| INFERENCE_CFG_AUTOPOPULATE | MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:148-152 | REPLACE | by INFERENCE_CFG_POPULATE_FROM_DERIVED |
```

---

## Top-3 recommended amendments (before pre-coding tag)

1. **F1 RECONSIDER FOREACH_CFG_GATE.** Either FOLD into master cfg field registry tuple (add gate_when column to source rows) OR FOLD into FOREACH_METADATA_BIT (extend tuple with default_gate). Don't ship as sparse sidecar — that's the very shape `.B.1` is supposed to eliminate.
2. **F6 ADD missing "Canonical sister registries considered" section** to plan body header. Self-violation otherwise.
3. **F2 UNIFY naming convention** across 3 consumer macros (all `_AUTOPOPULATE` per family precedent OR all `_FROM_DERIVED`; don't mix).

## Items deferrable to coding-time

- F3 cfg_save_field precedent citation (minor doc improvement)
- F5 Step 8 rephrasing (memory files already exist)
- Stamp_format_version bump decision (CRIT-6; .B.2 territory per plan)

---

## Verdict summary

**YELLOW.** One Path γ #3-class structural duplication (F1 FOREACH_CFG_GATE as sparse sidecar where inline column convention is canonical) + one self-violation (F6 missing sister-inspection section the plan itself codifies). Both are mechanical fixes — F1 RECONSIDER (~30-45min decision) + F6 add section (~10min). After amendments, expected GREEN.

The amendment direction (eliminate β4 + walk master via existing FOREACH_METADATA_BIT + tt:: dispatch + 3 distinct consumer macros) is structurally CORRECT and not parallel infrastructure. The ONE parallel structure proposed (FOREACH_CFG_GATE sidecar) needs reconsidering.

This META-SELF-AUDIT itself validates the discipline working: the very framework the amendment codifies catches a structural drift in the amendment.

---

**End of META-SELF-AUDIT report.** Recommend amendment cycle before pre-coding tag.
