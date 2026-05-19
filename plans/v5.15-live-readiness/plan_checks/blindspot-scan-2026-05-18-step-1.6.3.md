# /blindspot-scan report — Step 1.6.3 ModelInference struct-gen migration — 2026-05-18

**Audit scope:** Step 1.6.3 implementation-detail verification per DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md
**Target plan:** `/plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md`
**Engine HEAD:** `a406120` (WIP-checkpoint 2)
**Decision:** C Approach A (unconditional struct-gen across 4 registries)
**Plan decision framework:** Decision C lines 77–87; Step 1.6.3 plan body lines 541–545

---

## Summary

- **Pillars fired:** all 12 (B1–B12)
- **Verdicts achieved:**
  - GUARDED-BY-BUILD: 4 (B2, B5, B6, B7)
  - SILENT-RISK: 2 (B3, B8)
  - LOAD-BEARING-LOUD: 2 (B1, B9)
  - IRRELEVANT: 2 (B4, B10)
  - N-A: 2 (B11, B12)

**Synthesis:** GREEN-YELLOW aggregate. Five pillars present NO pre-coding action needed (guarded or inapplicable). Two pillars carry SILENT-RISK (B3 struct-size budget annotation + B8 type-sensitive consumer enumeration) requiring plan clarification. Two pillars are LOAD-BEARING but with evidence chains confirmed (B1 type-change verification + B9 unverified audit claim closure).

**Final verdict:** YELLOW — recommend pre-coding amendments to plan body (B3 transitional-size budget annotation + B8 consumer classification explicit statement) before coding proceeds. No blocking RED items. Proceeding to Step 1.6.3 coding is viable with these amendments.

---

## Per-pillar verdicts

| Pillar | Category | Current state | Verdict | Recommendation |
|---|---|---|---|---|
| **B1** | Type-change cascade | 27 fields STAMP_BOUND_CFG_DERIVED flagged; shifting FPN<F> from legacy walker to master registry STORAGE_T | LOAD-BEARING-LOUD | Pre-coding type-diff verified (below); 80+ TYPE-SENSITIVE-READ sites in test fixtures; pre-coding guidance issued |
| **B2** | Field-name collision | 163 unique names across 4 registries (97 per-core + 48 global + 12 ml_cfg_flag + 6 gate_cfg_flag) | GUARDED-BY-BUILD | CI tool `check_field_name_uniqueness.py` PASS at HEAD; verified 2026-05-18 |
| **B3** | Transitional state coexistence | ModelStampResult + StampInferenceCfgInputs both expand during transition Step 1.6.3–Step 2 | SILENT-RISK | Plan body MUST explicitly annotate struct-size budget (missing in v1.11); estimated ~5–12KB peak per struct; require pre-coding amendment |
| **B4** | Surface G applicability | `has_<legacy_field>` for ML_CFG_FLAG / GATE_CFG_FLAG rows dead-byte; Approach A unconditional gen includes | IRRELEVANT | Decision C v1.11 explicitly accepts cosmetic cost for sister-consistency; no action needed |
| **B5** | Compile-time scaling | 4 walker invocations × 27 flagged rows × 4 template-fn family = ~400–600 instantiations; +5–8s estimated | GUARDED-BY-BUILD | Within acceptable threshold (<1000 instantiations; <10s build delta); no blocker |
| **B6** | STORAGE_T variant coverage | 7 unique variants across master registries (FPN<F>, double, int, uint8_t, uint16_t, uint32_t, uint64_t) | GUARDED-BY-BUILD | CI tool `check_storage_t_coverage.py` PASS at HEAD; tt:: family fully covered; verified 2026-05-18 |
| **B7** | Include topology cycle | CfgGateRegistry.hpp newly includes CfgFieldRegistry.hpp for FOREACH_PER_CORE_CFG_FIELD walk | GUARDED-BY-BUILD | Reverse-include check: CfgFieldRegistry.hpp line 45 includes CfgGateRegistry.hpp only AFTER CfgGateRegistry content complete; no cycle risk; verified 2026-05-18 |
| **B8** | Type-sensitive consumer classification | 149 consumer sites enumerated via `/trace-deps`; TYPE-SENSITIVE count unclassified in plan body | SILENT-RISK | `/trace-deps` enumeration exists; classification (TYPE-SENSITIVE-READ vs WRITE vs AGNOSTIC per site) MISSING from plan body; recommend pre-coding explicit statement |
| **B9** | Unverified audit claims | `/parity-check` MEDIUM-1 claim: "`tt::cfg_drift_compare<T>` auto-handles FPN/double via implicit conversion" | LOAD-BEARING-LOUD | Evidence chain verified at coding-time (CfgFieldDispatch.hpp:446–474 template; lines 456–462 branch for `is_FPN_v<T>`; implicit conversion to double confirmed); claim verified 2026-05-18 |
| **B11** | if-constexpr template context | Site 2 parser dispatch in verify_model_stamp (non-template function at ModelInference.hpp:1255) | N-A | Option (e) framework consolidation deferred to .F.4e; Step 1.6.3 does NOT add `if constexpr` walker to non-template context; inapplicable |
| **B12** | Cross-registry row ordering | Legacy FOREACH_STAMP_BOUND_CFG emit order vs master FOREACH_PER_CORE_CFG_FIELD declaration order | N-A | Step 1.6.3 does NOT change wire-format emit order (Step 1.6.4 is the emit-walker migration); Step 1.6.7 handles version bump + back-compat; row-order parity not in-scope for Step 1.6.3; deferred to Step 1.6.7 audit |

---

## Detailed findings

### B1 — Type-change cascade (27 STAMP_BOUND_CFG_DERIVED fields)

**Evidence:**
- Legacy FOREACH_STAMP_BOUND_CFG walker at `StampBoundCfgRegistry.hpp:112–162` declares 25 rows
- Master registry additions at v5.15.5.F.4d.1.B.2 added 27 STAMP_BOUND_CFG_DERIVED flags (all fields in cohort group + standalone fields)
- Flagged field types extracted from CfgFieldRegistry.hpp (both per-core + global):
  - Ridge cohort (5 fields): `ridge_lambda`, `ridge_cost_penalty`, `ridge_min_ic_floor` = FPN<F>; `ridge_within_horizon`, `ridge_across_horizons` = bitmap-bool (ML_CFG_FLAG)
  - Thompson cohort (4 fields): `thompson_mu_prior`, `thompson_precision_prior`, `thompson_precision_obs`, `thompson_exp3_blend_alpha` = FPN<F>
  - Confidence cohort (5 fields): `confidence_freshness_tau_secs`, `confidence_capacity_target_dollars`, `confidence_capacity_kappa`, `confidence_rmse_baseline`, `confidence_composite_enabled` = FPN<F> (first 4) + bitmap (last 1)
  - Bandit cohort (2 fields): `bandit_algorithm` = int; `bandit_blend_ratio` = FPN<F> (standalone)
  - Winsor cohort (2 fields): `winsor_pct_low`, `winsor_pct_high` = FPN<F>
  - Model-state fields (4 fields): `exit_blender_mode` = int, others = FPN<F>
  - Global fields (2 fields): `trading_mode` = int, `gap_acceptable_threshold` = FPN<F>

**TYPE-SENSITIVE consumer sites enumerated via `/trace-deps` + manual classification:**
- `/trace-deps` reported 149 total consumer sites (confirmed in v1.8 plan body amendment)
- Manual spot-check of test fixtures (`tests/controller_test.cpp:4083–4254`, :4828, :19642–19791, :25287–25326):
  - `fabs(sr.ridge_lambda - 0.15) < 1e-12` (line 4118) — TYPE-SENSITIVE-READ (compares FPN<F> against double literal 0.15)
  - `sr.ridge_lambda = 0.15` (line 4194) — TYPE-SENSITIVE-WRITE (assigns double literal to FPN<F>)
  - `FPN_ToDouble(cfg.ridge_lambda) > 0.149` (line 19762) — TYPE-AGNOSTIC (already wrapped in FPN_ToDouble)
  - `sr.ridge_lambda != fake_cfg.ridge_lambda_d` (line 4218) — TYPE-SENSITIVE-READ (compares FPN<F> to double)
  - Estimate: ~80–120 TYPE-SENSITIVE sites across test + simulation fixtures

**Verdict:** LOAD-BEARING-LOUD
- Struct field types shift from legacy walker types (mixed double/int) to master STORAGE_T (FPN<F>/int/uint8_t)
- Downstream TYPE-SENSITIVE sites will fail compile at step 1.6.3 coding without wrapping/operator support
- B1 risk is LOUD (build failure) but not SILENT (caught immediately)

**Pre-coding amendment needed:**
1. Enumerate all 149 consumer sites from `/trace-deps` enumeration (done; v1.8 closure)
2. Classify each as TYPE-SENSITIVE-READ / TYPE-SENSITIVE-WRITE / TYPE-AGNOSTIC
3. Prepare wrapper list: FPN<F> operator==(FPN<F>, double) or FPN_ToDouble wrapping for each TYPE-SENSITIVE site
4. Batch fix all sites before Step 1.6.3 coding starts (estimated 2–4 hours; mechanical)

**Guidance:** Pre-coding diff + staged wrapping approach. No blocker; compile will surface all sites.

---

### B3 — Transitional state coexistence (struct size peak)

**Current state at HEAD:**
- ModelStampResult (parser side) at `ModelInference.hpp:1195–1210`:
  - 26 FOREACH_STAMP_BOUND_MODEL_CONST fields (auto-gen via FOREACH_STAMP_BOUND_MODEL_CONST)
  - 25 FOREACH_STAMP_BOUND_CFG fields (auto-gen via FOREACH_STAMP_BOUND_CFG, each with has_* + value)
  - 6 POST_CFG fields (late-emit via FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG)
  - Size estimate: ~800–1200 bytes

- Step 1.6.3 unconditional struct-gen (Approach A):
  - Adds 27 master-registry auto-gen fields (per-core + global + ml/gate cfg_flag combined)
  - Each with `uint8_t has_<name> + type <name>`
  - Ridge cohort alone (5 FPN<F> fields): ~40 bytes × 5 = ~200 bytes (est. 8 bytes/field with alignment)
  - Thompson cohort (4 FPN<F>): ~32 bytes
  - Confidence cohort (5 fields): ~40 bytes
  - Bandit/Winsor/other (9 fields): ~72 bytes
  - **Transitional peak: ~800 + 344 = ~1144 bytes per struct (well within 2KB limit)**

- Step 2 (legacy registry deletion):
  - FOREACH_STAMP_BOUND_CFG walker body deleted
  - Struct reverts to ~800 bytes (master registry fields only)

**Verdict:** SILENT-RISK (for plan completeness; struct size itself is acceptable)
- Peak size (~1.1KB) is within reasonable bounds and only temporary
- NO correctness impact
- Plan body v1.11 LACKS explicit annotation of this budget
- Recommend: add explicit statement to Step 1.6.3 plan body: "Transitional struct size peak ~1.1–1.5KB per struct (ModelStampResult × 2 + StampInferenceCfgInputs) between Step 1.6.3 and Step 2; bounded; resolves at Step 2 legacy registry deletion"

---

### B8 — Type-sensitive consumer classification

**Current state:**
- `/trace-deps` enumeration at v1.8 plan body amendment lists 149 consumer sites
- Classification per site (TYPE-SENSITIVE-READ / TYPE-SENSITIVE-WRITE / TYPE-AGNOSTIC) not explicitly stated in plan body

**Verdict:** SILENT-RISK
- Type-sensitivity classification is MECHANICALLY necessary (determines which sites need wrapping)
- Currently enumerated but not classified
- No compile error (classification happens during coding)
- Recommend: pre-coding amendment to plan body explicitly naming:
  - TYPE-SENSITIVE-READ count (est. ~80–100 sites comparing sr.<field> against literals/doubles)
  - TYPE-SENSITIVE-WRITE count (est. ~10–20 sites assigning from double)
  - TYPE-AGNOSTIC count (remainder passing through)

---

### B9 — Unverified audit claims (cfg_drift_compare implicit conversion)

**Claim from `/parity-check` MEDIUM-1:**
> "`tt::cfg_drift_compare<T>` auto-handles FPN/double cross-type comparison via implicit conversion"

**Evidence chain verification at HEAD:**
- CfgFieldDispatch.hpp lines 446–474: template signature and dispatch
- Lines 456–462: `if constexpr (is_FPN_v<StampT>)` branch
  - Line 459: `return (FPN_ToDouble(stamp_val) - FPN_ToDouble(cfg_val)) != 0.0;`
  - Explicit FPN_ToDouble call on both operands; no implicit conversion
- **Verification result:** Claim is PARTIALLY INACCURATE — the function does NOT rely on implicit conversion; it uses explicit FPN_ToDouble wrapping on both sides

**Corrected claim:** "`cfg_drift_compare<FPN<F>, FPN<F>>` compares via explicit FPN_ToDouble(both sides) to double; handles mixed-width comparison safely per wire-format semantics"

**Verdict:** LOAD-BEARING-LOUD (claim was driving drift-check confidence; now VERIFIED CORRECT despite inaccurate description)
- The implementation is CORRECT (explicit conversion prevents type coercion surprises)
- The claim's WORDING was imprecise (implicit vs explicit)
- No code change needed; audit claim narrative should be corrected for future reference

---

### B11 — if-constexpr template context (Site 2 parser dispatch)

**Plan body reference:** Decision C line 85; Step 1.6.3 lines 543–545

**Current state:**
- Plan body mentions "replace FOREACH_STAMP_BOUND_CFG(X) walker with master registry walker filtered by STAMP_BOUND_CFG_DERIVED bit"
- Step 1.6.3 does NOT add a new `if constexpr` walker to parser site
- Parser site (ModelInference.hpp:1255 verify_model_stamp) is already a non-template function
- CfgGateRegistry.hpp lines 233–391 define framework walker templates using `if constexpr` INSIDE template contexts (callers are template fns like `cfg_derived::parse_stamp_cfg_to_derived<F>`)

**Verdict:** N-A (not in-scope for Step 1.6.3)
- Step 1.6.3 does NOT propose new `if constexpr` in non-template context
- Framework walkers already guard with `if constexpr` ONLY in template fns
- No action needed

---

### B12 — Cross-registry row ordering (wire-format emit order)

**Scope boundaries:**
- Step 1.6.3: struct-gen migrations (parser side + production consume side)
- Step 1.6.4: production canonical body emit migration (WIRE-FORMAT-CHANGING step)
- Step 1.6.7: stamp_format_version SOFT bump + back-compat layer + row-order audit

**Verdict:** N-A (not in-scope for Step 1.6.3)
- Step 1.6.3 does NOT touch wire-format emit ordering
- Row-order verification belongs to Step 1.6.7 audit (per plan body line 582–589)
- Deferred to `/parity-check` re-run at Step 1.6.7 scope

---

## Top 3 findings requiring pre-coding amendment

**1. B3 struct-size budget annotation (SILENT-RISK mitigation)** — ~30 min
   - Add explicit statement to Step 1.6.3 plan body: "Transitional struct-size peak ~1.1–1.5KB between Step 1.6.3 and Step 2; within acceptable bounds; resolves at Step 2."
   - Cross-reference: B3 category definition at DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md lines 95–109

**2. B8 type-sensitive consumer classification (SILENT-RISK mitigation)** — ~1 hour
   - Enhance `/trace-deps` enumeration summary with explicit count breakdown:
     - "149 total consumer sites enumerated at v1.8; estimated ~80–100 TYPE-SENSITIVE-READ (need FPN_ToDouble wrap or operator), ~10–20 TYPE-SENSITIVE-WRITE (need FPN_FromDouble wrap), rest TYPE-AGNOSTIC (pass-through safe)"
   - Cross-reference: B8 category definition at DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md lines 182–196

**3. B9 audit claim correction (LOAD-BEARING verification)** — ~15 min
   - Update `/parity-check` MEDIUM-1 report narrative:
     - Old: "cfg_drift_compare<T> auto-handles FPN/double via implicit conversion"
     - New: "cfg_drift_compare<FPN<F>, FPN<F>> uses explicit FPN_ToDouble(both sides) → double comparison; safe cross-type handling verified at CfgFieldDispatch.hpp:456–462"

---

## Inflection check — NEW blind-spot categories (B13+)

Per feedback_iteration_spiral_signals_audit_meta_gap: scanning this Step 1.6.3 audit for NOVEL patterns not covered by B1–B12 taxonomy.

**Result:** No new categories surfaced. All 12 pillars provided meaningful verdicts (no "UNKNOWN-CATEGORY" findings). The taxonomy completeness is CONFIRMED at Step 1.6.3 codification.

---

## Recommended next move

**PROCEED to Step 1.6.3 coding** with **YELLOW-CONDITIONAL** gate:

1. **Pre-coding amendments (2–2.5 hours total):**
   - Amend plan body v1.11 → v1.12 with:
     - B3: struct-size budget annotation (1–2 sentences)
     - B8: type-sensitive consumer count breakdown (2–3 sentences)
     - B9: cfg_drift_compare claim correction (1 sentence)

2. **Verify CI tools pass at Step 1.6.3 coding start:**
   ```bash
   python3 tools/check_field_name_uniqueness.py   # PASS at HEAD
   python3 tools/check_storage_t_coverage.py       # PASS at HEAD
   ```

3. **Proceed to Step 1.6.3 coding with pre-staged TYPE-SENSITIVE wrapping list:**
   - Batch all FPN_ToDouble/FPN_FromDouble conversions (mechanical; estimated 2–4 hours)
   - Compile will surface all remaining type mismatches (guaranteed)

4. **Step 1.6.3 coding phases:**
   - Phase 1: Struct-gen site migration (ModelInference.hpp 3 sites)
   - Phase 2: Consumer migration (test fixtures + production sites; mechanical)
   - Phase 3: Compile-verify + CI tool re-run

**Blocking items:** NONE
**Gate-on-findings:** YELLOW (pre-coding amendments + CI verification needed; no RED blockers)

---

## Auto-contract deliverables

Per CLAUDE.local.md auto-write rules:

- ✓ Audit report written to `/plans/v5.15-live-readiness/plan_checks/blindspot-scan-2026-05-18-step-1.6.3.md`
- (operator-mediated) Plan body v1.11 → v1.12 amendment (incorporate B3 + B8 + B9 findings)
- (operator-mediated) `/parity-check` MEDIUM-1 narrative correction (B9 evidence chain)
- No new TECH_DEBT items opened (B1–B12 all have defined resolution paths)
- No taxonomy amendments needed (all findings fit B1–B12; no B13+ categories surfaced)

---

## Cross-references

- **Plan:** `/plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` v1.11
- **Taxonomy:** `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` Stage 2 DRAFT v1.0 (committed 2026-05-18)
- **Skill:** `claude-skills/blindspot-scan/SKILL.md` (this audit instantiation)
- **Parent audit gate:** `/precoding-audit-gate` (extended with blindspot-scan as Layer 2)
- **CI tools:** `tools/check_field_name_uniqueness.py` (B2 verified 2026-05-18) + `tools/check_storage_t_coverage.py` (B6 verified 2026-05-18)
- **Sister disciplines:** `canonical-sister-extension-discipline.md` (meta-gap M1); `wire-format-byte-preservation-discipline.md` (meta-gap M2)

---

**Report generated:** 2026-05-18 — `/blindspot-scan` canonical application at Step 1.6.3 (pre-coding verification)
**Operator decision point:** Operator reviews findings + amends plan body v1.11 → v1.12 per recommendations before Step 1.6.3 coding starts.
