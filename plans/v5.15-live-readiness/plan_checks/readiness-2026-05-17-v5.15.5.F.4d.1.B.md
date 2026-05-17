# /readiness report — `.F.4d.1.B` migration + consumer plan — 2026-05-17

**Plan path:** `plans/v5.15-live-readiness/subplans/2026-05-16-v5.15.5.F.4d.1.B-migration-consumer.md` v1.2 + sidecar v1.1
**Predecessor HEAD:** `39b9947` (`v5.15.5.F.4d.1.A` shipped 2026-05-17)
**Engine baseline:** 3196 controller_test + 17 depth_recorder_test GREEN post-`.A`
**DESIGN_SPECS preloaded:** metadata-bit-driven-derived-filter-framework.md (v1.2), categorical-tag-applicability-pattern.md, cfg-flag-eligibility-criteria.md, sidecar-override-pattern-for-registry-auto-flows.md, branchless-dispatch-discipline.md, x-macro-registry-with-presence-dispatch.md, wire-format-byte-preservation-discipline.md

---

## Plan summary
- Single sub-ship (.B); 14 chronological Steps; ~6-8h focused
- Branch: `feat/v5.15-live-readiness` (correct; sprint branch)
- Rollback anchor: `pre-v5.15.5.F.4d.1.B` mandatory at Step 0 + per-Phase mid-flight tags
- ~25-30 new tests projected; baseline ~3196 → expected ~3221-3226
- MED risk (wide blast radius: 24-row migration + 12 ML_CFG_FLAG sig + 3 consumer sites + legacy registry empty-out)

---

## 28-check verdicts (10-item review + cold-pickup C.1-C.10 + 8 sub-categories)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | PASS | Plan explicitly states "Hot path UNTOUCHED"; `calls_graph_diff verify NONE` in close ritual. Framework/consumer migrations land at boot+slow path only. |
| 2 | Train-serve parity | PASS | Migration preserves byte-shape per row (invariants I1-I7 from `.A` verify; `.D` v5.14 fixture round-trip catches drift). Always-emit canonical per Q3.G. |
| 3 | Surface area | YELLOW | 29 source-row touches (22 cohort + 2 parity gap + 4 `.A.7` retro + 1 NEW) + 12 ML_CFG_FLAG rows + 2 X-macro consumers + 3 consumer sites + 8-10 comment text updates + 2 NEW headers (CfgDriftAutoPopulate.hpp, CfgDriftGate.hpp) + Winsor validation. Mitigated by per-Phase mid-flight tags. |
| 4 | Pointer/heap lifecycle | PASS | No heap state added; tt::cfg_emit_synthetic_field operates on stack buffers (snprintf into caller buffer per H1). |
| 5 | Backward compat | PASS | `STAMP_BOUND_CFG_DERIVED` bit-add coexists with `STAMP_BOUND` during transition; v5.14 stamps continue parsing byte-identical (no parser changes); ml_buy_threshold + bandit_blend_ratio explicit two-bit transition path. |
| 6 | Multi-threading | PASS | No new thread/shared state/atomic; framework code is boot/test/setup only. |
| 7 | Test coverage | PASS | Plan body Step 13 enumerates ~30 expected tests across 10 categories; matches projected count. |
| 8 | Docs + invariants | PASS | Auto-writes per CLAUDE.local.md contract (CHANGELOG / TECH_DEBT / FEATURE_LOOKUP / DESIGN_SPECS README / CLAUDE.local.md sprint state). H15-H20 audit table present. |
| 9 | Forward maintenance | PASS | Whole point of `.B` is to make future additions 1-row mechanical; β4 dispatch table is the structural-fix shape (sister to FOREACH_DRIFT_OVERRIDE at .C). |
| 10 | Rollback story | PASS | Pre-tag `pre-v5.15.5.F.4d.1.B` + per-Phase mid-flight tags + recovery section per failure mode. |
| C.1 | Branch state | PASS | "stay on sprint branch" explicit. |
| C.2 | Phase order matches deps | PASS | Step 1 (helper) → Step 2 (sig) → Step 3 (walker) → Step 4 (rows) → ... → Step 12 (empty-out LAST). Plan body line 141 has the chronological order ordering. |
| C.3 | First concrete move | PASS | Step 0 + Step 1 are explicit + mechanical. |
| C.4 | Function/constructor names cited | PASS | `tt::cfg_emit_synthetic_field<T>`, `CFG_DRIFT_AUTOPOPULATE`, `STAMP_BOUND_CFG_walk_bitmap_rows`, `gate_default<F>` etc. all named. |
| C.5 | File:line refs for tests/baselines | PASS | Plan + sidecar cite `CfgFieldRegistry.hpp:524`, `:528`, `:569`, `MlCfgFlagRegistry.hpp:52+/70/82-83/92-103`, `CoreModelZoo.hpp:225-247/243`, `StampHelper.hpp:150`, `ConfidenceScore.hpp:729` — verified at HEAD. |
| C.6 | Stale-claim audit | **GAP** | Plan claims "1 NEW row in `FOREACH_GLOBAL_CFG_FIELD` (gap_acceptable_threshold)" — but `gap_acceptable_threshold` is ALREADY a manual cfg field at `ControllerConfig.hpp:889` + parser at `:2554` + default at `:1729` + used in Backtest/. Actual work shape is **MIGRATION from manual declaration → FOREACH_CFG_FIELD row** (delete manual `FPN<F> gap_acceptable_threshold;` declaration + delete manual CFG_PARSE_FPN call + add to registry). NOT a greenfield NEW row. |
| C.7 | Effort claims reconcile with deltas | YELLOW | 6-8h estimate is plausible for: 22 row bit-adds (~30min mechanical) + 12 ML_CFG_FLAG sig (~30min) + 3 consumer migrations (~1.5h with verification) + β4 dispatch + sidecar registry (~1.5h with CfgDriftGate.hpp NEW ~80 LOC) + CFG_DRIFT_AUTOPOPULATE macro (~1h) + 30 tests (~2h). Body residual cleanup (~45min, per `.A` postmortem) added. Total ~7-8h focused; consistent. |
| C.8 | Source-audit references | PASS | Cites `plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` Path γ source + sub-master Charter 9/12/14 + `.A` postmortem. |
| C.9 | Predecessor/dependent plans named with paths | PASS | `.A` plan body + sub-master path explicit; successor `.C` path stub identified. |
| C.10 | Tag names locked | PASS | `pre-v5.15.5.F.4d.1.B` + `wip-v5.15.5.F.4d.1.B-step{2,3,4,6,7,9,11}-*` + `v5.15.5.F.4d.1.B` (signed annotated). |
| 27 | DOD pattern application (catalog) | PASS | Plan body § "DOD analysis" present + per-cohort branchless dispatch via β4 fn-pointer table (Pattern 1 per H20) + sidecar pattern Stage 4 2nd canonical + `tt::` dispatch (H13) preserved + composed-filter-mask via auto-generated masks. Bitmap walker uses CFG_FIELD_FOR_EACH_SET_BIT TZCNT iteration. |

## Cohort eligibility audit per `cfg-flag-eligibility-criteria.md`
- 22 clean cohort migrations: ALL already have `STAMP_BOUND` bit set at HEAD (winsor, ridge, composite, bandit, thompson, soft-risk) → `STAMP_BOUND_CFG_DERIVED` is bit-coexistence, NOT new eligibility decision. PASS.
- `gap_acceptable_threshold` (claimed NEW): see C.6 GAP above. Categorical applicability `STRAT_CAT_ML, OP_MODE_CAT_ALL, REGIME_CAT_ALL, RISK_CAT_ALL` per sidecar = reasonable per cohort-audit rule (already in cohort with other ML training thresholds). `lives_in_struct=STRUCT_CFG` correct per Backtest usage.
- ml_buy_threshold + bandit_blend_ratio pre-canonical fix = two-step `STAMP_BOUND` + `STAMP_BOUND_CFG_DERIVED` bit-add. Eligibility verified — both meaningful fields read at inference per CoreModelZoo. PASS.

## Drift sub-categories
- Feature drift: PASS (no model feature changes)
- Label drift: PASS
- Metric drift: PASS
- Path drift: PASS
- **Format drift**: PASS — derived filter walk produces byte-identical canonical body to legacy walker (I1-I5 verifies); `.D` v5.14 fixture round-trip will confirm at umbrella close
- Threshold drift: PASS (no formulas duplicated)
- Tick-source: PASS
- Build-flag: PASS

## Hardening checks
- Atomic file writes: N/A (no file emit changes)
- Locale pinning: PASS — `.A` framework macro pins LC_NUMERIC; `tt::cfg_emit_synthetic_field<T>` inherits Layer 2 discipline; invariant I3 verifies under simulated de_DE
- GUI render-thread blocking I/O: PASS (no GUI panel changes)
- Failure telemetry path: PASS (drift increments `sr.inference_cfg_drift_count` + `BITMAP_SET` + WARN/FAIL severity preserved from existing CoreModelZoo)
- Resource cleanup audit: PASS (no new fopen/popen)
- Cross-platform: PASS (X-macro reduction is portable)

## Propagation checks
- New cfg field `gap_acceptable_threshold`: **YELLOW per C.6** — must also DELETE manual declaration + DELETE manual parser entry (the cfg field already exists scattered across manual sites; migration shape, not addition shape)
- New version constant: PASS (Version.hpp bump 5.15.5.F.4d.1.A → .B)
- New invariant claim: PASS (H15 + H16 + H17 + H18 + H19 + H20 audit table; no new invariant)
- New Pattern_FunctionName: PASS (CFG_DRIFT_AUTOPOPULATE macro + gate_* fns + new headers will appear in CODE_MAP regen)

## Cohort dispatch via β4 (Step 11) — H20 Pattern 1 verification
- Branchless dispatch table: PASS (verified `BITMAP_ANY` macro exists at `MemHeaders/BitmapMacros.hpp:95`; `MASK_ML_CFG_BANDIT_ENABLED` etc. auto-generated by X_GEN_ML_CFG_MASK)
- FOREACH_DRIFT_GATE sparse sidecar enrolls 14 rows (4 Bandit/Thompson + 3 RiskDegradation + 3 RidgeAny + 4 CompositeConfidence; Winsor → Default), but `thompson_exp3_blend_alpha` NOT in sidecar enumeration — gates self via gate_bandit_thompson? **YELLOW**: 5th Bandit/Thompson field (line 603 at HEAD) not in plan body Step 11 sidecar table. Confirm during coding whether `thompson_exp3_blend_alpha` is BANDIT_THOMPSON cohort (likely YES; mentioned in cohort summary line 161 "5 fields") or self-gate.

## Body residual cleanup (Path γ+ v2)
Plan body header (lines 10-17) + sidecar header (lines 8-14) BOTH have annotation blocks enumerating spots needing mechanical update at `.B` update step:
- Plan body lines 114, 234, 247, 260-265, 642, 827: `STAMP_BOUND_CFG_walk_filtered_rows` → `CFG_FIELD_FOR_EACH_SET_BIT(g_*_cfg_stamp_bound_cfg_derived_mask.words, ...)`. **VERIFIED** via grep: line 114 confirms `Bitmap walker activation in StampBoundDerivedFilter.hpp`; line 234 confirms section header. Self-consistent.
- Line 116 predecessor description: still mentions DerivedFilterFramework macros + DerivedFilterRoster.hpp deliverables (SUPERSEDED — `.A` shipped Path γ; FOREACH_METADATA_BIT row addition + StampBoundDerivedFilter.hpp consumer + wire_format_invariants.hpp helper + CFG_COMPOSE_AUDIT_DECISIONS — see `.A` postmortem Deliverables 1-8). Mechanical fix at `.B` update.
- Lines 641, 827 (FOREACH_DERIVED_FILTER doesn't exist) — CONFIRMED no such registry at HEAD (FOREACH_METADATA_BIT is canonical at `CfgFieldRegistry.hpp:1064`).
- Sidecar lines 247, 289, 292 callback-indirection sample → CFG_FIELD_FOR_EACH_SET_BIT direct.
- ~30-45 min mechanical cleanup estimate per annotation block.

## TECH_DEBT auto-writes
- Plan body line 866 already lists `TECH_DEBT-085 status remains IN-FLIGHT (.C + .D remaining)`.
- No new TECH_DEBT entries opened by `.B` itself per plan body. PASS.

## Dependency verification (top file:line claims)

| Claim | Verified |
|---|---|
| `CfgFieldRegistry.hpp:524` ml_buy_threshold has `metadata_flags = 0` | PASS at HEAD |
| `CfgFieldRegistry.hpp:528` bandit_blend_ratio has `metadata_flags = 0` | PASS at HEAD |
| `CfgFieldRegistry.hpp:569+572` winsor_pct_low/high have STAMP_BOUND | PASS |
| `CfgFieldRegistry.hpp:559/562/565` ridge cohort has STAMP_BOUND | PASS |
| `CfgFieldRegistry.hpp:589/592/595/599/603` bandit/thompson cohort has STAMP_BOUND | PASS |
| `CfgFieldRegistry.hpp:608/611/614/617` soft-risk cohort has STAMP_BOUND | PASS |
| `CfgFieldRegistry.hpp:576/579/582/585` composite confidence has STAMP_BOUND | PASS |
| `MlCfgFlagRegistry.hpp:70/82-83/92` consumer macros | PASS at HEAD |
| `CoreModelZoo.hpp:243` FOREACH_STAMP_BOUND_CFG(X) walk | PASS at HEAD |
| `StampHelper.hpp:150` comment | PASS |
| `ConfidenceScore.hpp:729` COUNT usage comment | PASS |
| `StampBoundCfgRegistry.hpp:99` FOREACH_STAMP_BOUND_CFG body | PASS |
| `MetaRegistry.hpp:52` FOREACH_STAMP_BOUND_CFG enrolled row | PASS |
| `StampBoundDerivedFilter.hpp` exists (76 LOC, post-`.A`) | PASS |
| `MemHeaders/CfgDriftAutoPopulate.hpp` doesn't exist (NEW at .B) | PASS (will create) |
| `MemHeaders/CfgDriftGate.hpp` doesn't exist (NEW at .B) | PASS (will create) |
| `gap_acceptable_threshold` already exists in cfg | **C.6 GAP**: manual field at `ControllerConfig.hpp:889` + parser `:2554` + default `:1729` — plan claims "NEW row" but is MIGRATION shape |

---

## Punch list of unstated gaps

1. **G-1 (HIGH; C.6 finding)** — `gap_acceptable_threshold` is NOT a greenfield NEW row. The field exists as manual cfg declaration at `ControllerConfig.hpp:889` + parser at `:2554` + default at `:1729` + Backtest usage. Step 5 needs reframing: **MIGRATION** from manual decl → FOREACH_GLOBAL_CFG_FIELD row. Plan body must add: (a) DELETE manual `FPN<F> gap_acceptable_threshold;` from ControllerConfig.hpp; (b) DELETE manual `CFG_PARSE_FPN(gap_acceptable_threshold)` from parser; (c) DELETE manual default-init at `:1729`; (d) verify Backtest usage at `BacktestSharded.hpp:294,341` still compiles after registry-driven declaration replaces manual. Effort: +30-45 min vs "new row". Test fixture sweep for any harness setting `gap_acceptable_threshold` directly stays valid (registry-generated struct member name unchanged).

2. **G-2 (MED)** — `thompson_exp3_blend_alpha` (line 603 in CfgFieldRegistry.hpp at HEAD) is the 5th Bandit/Thompson field but plan body Step 11 FOREACH_DRIFT_GATE sidecar only enumerates 4 BANDIT_THOMPSON rows (Step 11 sidecar at lines 552-555). Either: (a) add 5th row to sidecar with `BANDIT_THOMPSON` cohort, OR (b) document why it gates → Default. Plan body line 161 says "5 fields" in cohort but Step 11 sidecar only lists 4. Inconsistency.

3. **G-3 (LOW)** — `risk_degradation_curve` (the gate-self field for soft-risk cohort) — plan body Step 11 sidecar uses 3 rows (full_size + min_size_thresh + min_size_pct) which correctly excludes `risk_degradation_curve` itself (gates self → Default cohort). PASS but worth annotating "risk_degradation_curve gates self → Default; not in sidecar" in plan body for cold-pickup clarity.

4. **G-4 (LOW)** — Body residual cleanup (Path γ+ v2 ~30-45 min) is documented in plan body header annotation block + sidecar header. Treat as mandatory pre-coding mechanical fix BEFORE Step 0 tag (so plan body that Step 0 references is canonical). Recommend: do the body cleanup in a single commit "v5.15.5.F.4d.1.B planning: Path γ+ v2 body residual cleanup" tagged as the .B planning-cleanup step BEFORE `pre-v5.15.5.F.4d.1.B`.

5. **G-5 (LOW)** — Plan body line 906 says "End of plan body draft v1.0" but plan body header says v1.2 + Path γ context. Stale closing line. Mechanical fix.

6. **G-6 (LOW)** — Plan body Step 12 says "tools/check_meta_registry.py PASS" — verify the tool runs against the new state where FOREACH_STAMP_BOUND_CFG is empty + enrolled. Confirm whether tool tolerates empty-body registries OR if the H15 enrollment row needs to be DELETED + the registry literally erased before the check passes. Worth ~5 min verification BEFORE Step 12 to know which.

---

## Recommendations

### Must fix before coding (~30-45 min)
- **G-1 + G-2**: Update plan body Step 5 to reframe `gap_acceptable_threshold` as MIGRATION (with manual-cleanup substeps); confirm G-2 5th BANDIT_THOMPSON sidecar row. Effort ~30 min.
- **G-4**: Apply Path γ+ v2 body residual cleanup at plan body lines 114/234/247/260-265/642/827 + sidecar lines 247/289/292 + line 116 predecessor description + lines 641/827 FOREACH_DERIVED_FILTER refs. ~45 min mechanical edit. Annotation blocks at top of both files already enumerate the spots.

### Worth fixing during coding (acceptable as YELLOW)
- **G-3**: Annotate risk_degradation_curve gate-self decision in plan body Step 11.
- **G-5**: Update "v1.0" closing line to "v1.2 Path γ+ v2".
- **G-6**: Verify `tools/check_meta_registry.py` behavior on empty-body legacy registry; adjust Step 12 accordingly.

### Acceptable risk (don't block)
- Surface area (29 source-row touches + 12 ML_CFG_FLAG rows + 3 consumer sites + 2 NEW headers) is wide but mitigated by per-Phase mid-flight tags + invariant tests I1-I7 firing immediately on misconfiguration.
- Body residual cleanup is well-flagged in both plan + sidecar header annotation blocks; will not be missed.

---

## Verdict: **YELLOW**

Plan is structurally sound. Path γ+ v2 simplification of `CFG_DRIFT_AUTOPOPULATE` to use auto-generated mask is the right move; β4 sparse sidecar + branchless dispatch table at Step 11 closes Class 14/18/19/28 latents structurally. All claimed file:line refs verified at HEAD. Cohort eligibility is clean (all 22 cohort migrations have `STAMP_BOUND` already; bit-add is mechanical). Pre-coding rollback anchor + per-Phase mid-flight tags + invariant tests + test count projection all present.

**Must-fix before coding** (~75 min total):
1. **G-1** Reframe `gap_acceptable_threshold` as migration (manual decl/parser/default → registry row); +30 min
2. **G-2** Add 5th BANDIT_THOMPSON row to Step 11 sidecar OR document why thompson_exp3_blend_alpha→Default; +5 min
3. **G-4** Apply Path γ+ v2 body residual cleanup at the 8-10 annotated spots; +45 min

After must-fix triage: **GREEN to tag `pre-v5.15.5.F.4d.1.B` + start Step 0**.

---

**End of /readiness report.** Saved to `plan_checks/readiness-2026-05-17-v5.15.5.F.4d.1.B.md`.
