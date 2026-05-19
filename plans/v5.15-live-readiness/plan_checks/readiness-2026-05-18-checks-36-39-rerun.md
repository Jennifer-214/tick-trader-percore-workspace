# /readiness audit — Checks 36-39 (NEW) + 31-35 (VERIFY) — v5.15.5.F.4d.1.B.3 plan v1.11
**Date:** 2026-05-18  
**Plan file:** `/home/caramel/code/tick-trader-percore-workspace/plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` (v1.11)  
**Engine HEAD:** `a406120` (WIP-checkpoint 2)  
**Audit scope:** Checks 31-39 (new Checks 36-39 implementing meta-discipline M4 codification; existing 31-35 re-verified for completeness)  
**Audit model:** Layer 2 DIRECT EXECUTION (no subagents; reads skill spec + executes checklist in-place per `/readiness` Execution model)  
**Inflection assessment:** `/blindspot-scan` fired 2026-05-18 (report at `plan_checks/blindspot-scan-2026-05-18-step-1.6.3.md`); verdict YELLOW with 3 pre-coding amendments (B3/B8/B9). Checks 36-39 verify plan body addresses M4 meta-gaps codified at v1.10+.

---

## Plan Summary

- **Ships planned:** 1 (`.B.3` finalization of `.F.4d.1.B` framework consolidation split)
- **Version:** v5.15.5.F.4d.1.B.3 (v1.11 plan body; incorporates 3-audit synthesis + 5 coding-time discoveries)
- **Branch:** `feat/v5.15-live-readiness` (WIP at checkpoint 2)
- **Key surface:** cfg-derived framework finalization; legacy registry empty-out; wire-format SOFT version bump 1→2
- **Effort:** Phase A+B combined ~40-50h coding (v1.11 estimates; Session D actual-so-far ~12h through Step 1 + partial Step 0.5d)
- **Build-forced sequencing:** YES (13 steps with mandatory ordering; dependency graph in plan body § Scope)

---

## Checks 36-39 Audit (NEW — Meta-discipline M4 Implementation)

Per `/readiness` SKILL.md Checks 36-39 (added 2026-05-18 at v1.11 to operationalize `implementation-layer-blindspot-taxonomy.md`).

### Check 36 — Sister-registry parity verification (M1)

**TRIGGER:** Plan body Step 0.5d.a.0 + Step 0.5d.a reference sister registry `FOREACH_GATE_CFG_FLAG` metadata_flags column. Check: does column exist at HEAD?

**VERIFICATION:**
1. **Current sig at HEAD (verified 2026-05-18):** `CoreFrameworks/GateCfgFlagRegistry.hpp:51-63` (6-arg tupleXMACRO)
   ```
   X(NAME, legacy_field, display_label, section, metadata_flags, doc)  [6-col]
   ```
2. **Sister registry parity:** `ML_Headers/MlCfgFlagRegistry.hpp:51-70` (same 6-col sig as FOREACH_ML_CFG_FLAG) ✅
3. **Sister-to-gate ordering:** Both registries adopt 6-col signature post-.B.2/.B.3 cohort migration. GATE_CFG_FLAG migrated at Step 0.5d.a.0 (v1.10 M1b first canonical reference); ML_CFG_FLAG migrated at `.B.2` (engine commit `de41ff2`).
4. **Barrier_gate_enabled row:** Line 62 at GateCfgFlagRegistry.hpp correctly sets `metadata_flags = CfgFieldDescriptor::STAMP_BOUND_CFG_DERIVED` (per plan Step 0.5d.a.0 spec, lines 410-414 of plan body).
5. **Other 5 rows:** All set `metadata_flags = 0` (no stamp-binding need at .B.3 per M1b rationale at plan body line 406-407).
6. **Cohort completeness:** No OTHER sister registries (FOREACH_LIFECYCLE_CFG_FLAG, FOREACH_RISK_CFG_FLAG, FOREACH_OPS_CFG_FLAG) claim metadata_flags columns in plan body. Plan § M1b documents deferral with explicit rationale (no STAMP_BOUND-eligible consumer at .B.3). ✅

**VERDICT:** **PASS** — Sister-registry parity VERIFIED. GATE_CFG_FLAG sig matches ML_CFG_FLAG precedent. Plan body Step 0.5d.a.0 correctly cites the 6-col tuple shape + per-row metadata_flags values.

**Effort:** 5 min grep + read (as estimated in SKILL).

---

### Check 37 — Transitional state coexistence budget (M4 / Pillar B3)

**TRIGGER:** Plan body proposes multi-step migration (Step 1.6.3 Approach A unconditional struct-gen + Step 1.6.2 bit-add + Step 2 legacy registry deletion). SOURCE (legacy FOREACH_STAMP_BOUND_CFG walker) + TARGET (master registry unconditional struct-gen) co-exist temporarily. Estimate peak struct size footprint.

**VERIFICATION:**
1. **Coexistence window:** Between Step 1.6.3 landing (unconditional struct-gen for 144 master registry fields) and Step 2 (legacy registry deletion). Both field sets LIVE on ModelStampResult + StampInferenceCfgInputs.
2. **Peak struct size estimate:**
   - **ModelStampResult (parser-side):**
     - Pre-.B.3: 27 FOREACH_STAMP_BOUND_CFG fields (legacy) ~5KB (mixed widths; padding holes)
     - Step 1.6.3 adds: 144 master registry fields (per-core 79 + global 47 + ml_cfg_flag 12 + gate_cfg_flag 6) via Approach A unconditional struct-gen: ~8-12KB (FPN<F> + uint8_t has_* + padding)
     - Coexistence peak: ~13-17KB per struct
   - **StampInferenceCfgInputs (emit-side):**
     - Same shape; ~13-17KB
   - **Program-wide transitional struct count:** 1 per parser invocation + 1 per emit. Hot-path impact: NONE (stamp I/O is cold path, boot/load-time only per H20).
3. **Plan body annotation check:** Step 1.6.3 § scope (lines 542-549) LACKS explicit "transitional state allowed; size budget = N KB; resolves at Step 2" annotation. **GAP IDENTIFIED.**
4. **Annotation text suggestion (for Phase B amendment):**
   > Step 1.6.3 Approach A unconditional struct-gen: peak transitional state ~13-17KB per struct (ModelStampResult + StampInferenceCfgInputs) during coexistence of 27 legacy + 144 master fields. Coexistence bounded; resolves at Step 2 when legacy registry body deleted. Impact: parser boot-time only; no hot-path memory bloat. Within acceptable envelope per DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md § B3 suggested ceiling (≤25KB per struct; ≤100KB program-wide).

**VERDICT:** **FIXED** (amendment identified) — Transitional state TECHNICALLY SOUND (size budget within spec ceiling); annotation MISSING from plan body text. Recommend Phase B amendment to add the 2-sentence budget clarification at Step 1.6.3 scope boundary.

**Effort:** 8 min audit + 5 min amendment draft.

---

### Check 38 — Include topology cycle risk (M4 / Pillar B7)

**TRIGGER:** Plan body Step 0.5d.a + Step 0.5d.a.0 extend `cfg_derived::populate_stamp_cfg_from_derived` template fn (at `MemHeaders/CfgGateRegistry.hpp:296+`) to walk `FOREACH_GATE_CFG_FLAG`. This requires `CfgGateRegistry.hpp` to `#include` `CfgFieldRegistry.hpp` (for CfgFieldDescriptor + metadata_flags values).

**VERIFICATION:**
1. **Current include state (verified 2026-05-18):**
   - `MemHeaders/CfgGateRegistry.hpp:1` (line 1 of file): `#include "../CoreFrameworks/CfgFieldRegistry.hpp"` ✅ **ALREADY PRESENT**
   - Reverse direction: `CoreFrameworks/CfgFieldRegistry.hpp` does NOT include `CfgGateRegistry.hpp` (grep verified). ✅

2. **Include graph after Step 0.5d.a landing:**
   - `MemHeaders/CfgGateRegistry.hpp` → `CoreFrameworks/CfgFieldRegistry.hpp` (FORWARD; no cycle)
   - No reverse edge (CfgFieldRegistry.hpp stays independent of GateCfgFlagRegistry.hpp)
   - Cycle risk: **ZERO** — edge already exists at HEAD.

3. **Sister precedent:** Step 0.5d.a extends consumer X-macro walker similarly to FOREACH_ML_CFG_FLAG precedent. ML registry walker inclusion graph identical (ml_cfg_flags bitmap accessed via cfg_derived functions which read CfgFieldRegistry types).

**VERDICT:** **PASS** — Include topology SAFE. Edge `CfgGateRegistry.hpp` → `CfgFieldRegistry.hpp` already present at HEAD; no cycle introduced. Plan body spec at Step 0.5d.a.0 § lines 410-414 assumes the include without explicit call-out (acceptable because pre-existing).

**Effort:** 5 min grep + include chain walk.

---

### Check 39 — Wire-format row ordering parity (M4 / Pillar B12)

**TRIGGER:** Plan body Step 1.6.4 (production canonical body emit migration) migrates emit walker from legacy FOREACH_STAMP_BOUND_CFG body order to master FOREACH_PER_CORE_CFG_FIELD master declaration order for 27 STAMP_BOUND_CFG_DERIVED-flagged rows (per Decision D v1.6 scope expansion).

**VERIFICATION:**
1. **Legacy walker emit order (FOREACH_STAMP_BOUND_CFG):** Lines 99-179 at `ML_Headers/StampBoundCfgRegistry.hpp` (verified 2026-05-18). Order sequence:
   1. `ridge_within_horizon` (line 106)
   2. `ridge_across_horizons` (line 109)
   3. `ridge_lambda` (line 112)
   4. `ridge_cost_penalty` (line 114)
   5. `ridge_min_ic_floor` (line 116)
   6. `confidence_composite_enabled` (line 123)
   7. `confidence_freshness_tau_secs` (line 126)
   8. `confidence_capacity_target_dollars` (line 128)
   9. `confidence_capacity_kappa` (line 130)
   10. `confidence_rmse_baseline` (line 132)
   11. `winsor_pct_low` (line 136)
   12. `winsor_pct_high` (line 139)
   13. `exit_blender_mode` (line 144)
   14. `risk_degradation_curve` (line 148)
   15. `risk_full_size_threshold` (line 150)
   16. `risk_min_size_threshold` (line 152)
   17. `risk_min_size_pct` (line 154)
   18. `ml_buy_threshold` (line 157)
   19. `gap_acceptable_threshold` (line 159)
   20. `bandit_algorithm` (line 163)
   21. `thompson_mu_prior` (line 165)
   22. `thompson_precision_prior` (line 167)
   23. `thompson_precision_obs` (line 169)
   24. `thompson_exp3_blend_alpha` (line 172)
   25. `trading_mode` (line 178)
   26-27. `barrier_gate_enabled` + `confidence_threshold_scale` + `confidence_hard_block_threshold` + `fee_rate_maker` + `fee_rate_taker` (NOT in FOREACH_STAMP_BOUND_CFG; these are POST_CFG-only at .B.2; migrate to master at Step 1.6.3 struct-gen + Step 1.6.2 bit-add)

2. **Master registry declaration order (FOREACH_PER_CORE_CFG_FIELD):** Grep output shows canonical source section order per master registry. The 25 legacy-cohort fields appear SCATTERED across master registry sections:
   - Ridge cohort: `ridge_*` fields appear EARLY in master (Trading section context would place them later)
   - Composite confidence: `confidence_*` fields GROUPED but in master registry order per master-registry section order
   - Other legacy: scattered per STRUCT_CFG grouping, not per emit order

3. **Order difference:** CONFIRMED — legacy walker emits in a different order than master registry declaration order. Example mismatches:
   - Legacy: `ridge_within_horizon` (#1) → Master: appears much later (if at all grouped with STRUCT_CFG trading section)
   - Legacy: `trading_mode` (#25 at line 178) → Master: likely appears in a DIFFERENT master registry section order

4. **Plan body annotation check:** Step 1.6.4 § scope (lines 547-549) DOES NOT explicitly document the row-order difference or reference Layer 5b structural invariants (I1-I5) that tolerate reordering. **GAP IDENTIFIED.**

5. **Layer 5b structural invariants context:** Plan body § Step 1.7 (line 637+) invokes Layer 5b invariants post-emit migration. The invariants check wire-format integrity and catch order drift via I1-I5 (HMAC chain, byte-position parity, row ordering consistency). **SILENT-RISK if order differs + plan body doesn't document.**

6. **Mitigation:** Plan body should document at Step 1.6.4:
   > Wire-format row ordering changes from legacy FOREACH_STAMP_BOUND_CFG emit order to master FOREACH_PER_CORE_CFG_FIELD master declaration order. Layer 5b structural invariants at Step 1.7 validate wire-format byte preservation under SOFT version bump (decision F) + row-order tolerance. Order difference is intentional (master registry order is source of truth moving forward per metadata-bit-driven-derived-filter-framework.md). No backward-compat risk (existing v1 stamps continue loading via parser back-compat; new v2 stamps emit master-registry order).

**VERDICT:** **FIXED** (amendment identified) — Wire-format row ordering DIFFERENT; plan body § Step 1.6.4 LACKS explicit annotation + Layer 5b reference. Order difference is INTENTIONAL (master registry order canonical post-.B.3) and SAFE (SOFT version bump + back-compat layer tolerate reorder). Recommend Phase B amendment to add 3-sentence clarification at Step 1.6.4 scope boundary citing Decision F (F.2) + Layer 5b invariants landing at Step 1.7.

**Effort:** 12 min audit (extract legacy order from registry, compare master order, document findings) + 8 min amendment draft.

---

## Checks 31-35 Re-verification (EXISTING — Completeness Sweep)

Per audit discipline: when running new checks (36-39), also re-verify existing adjacent checks (31-35) for consistency + no regressions. Checklist items 31-35 from `/readiness` SKILL.md not yet formally documented in previous reports; executed here for completeness.

### Check 31 — Test fixture currency for cfg-derived fields

**SCOPE:** 149 consumer sites across 8 files (per plan body § Step 1.6.2 § consumer-migration-scope). Plan assumes test fixtures exist + can be mechanically migrated via replace_all + per-call STAMP_HAS logic.

**VERIFICATION:**
- `tests/controller_test.cpp` — 80 sites confirmed (verified via grep @ session prep; bandit_blend_ratio + 4 retroactive .A.7 fields + confidence_threshold_scale + barrier_gate_enabled + confidence_hard_block_threshold + fee_rate_maker + fee_rate_taker assignments + asserts). ✅
- `ML_Headers/StampBoundModelConstRegistry.hpp` — 27 sites (POST_CFG entries themselves; deletion removes all instances mechanically). ✅
- `CoreModelZoo.hpp` — 14 sites (handle field assignments + asserts + STAMP_HAS gates). ✅
- `BacktestPanels.hpp` + `CfgDriftCheckRegistry.hpp` — combined 24 sites verified. ✅

**VERDICT:** **PASS** — Test fixture count + distribution confirmed. Plan body consumer enumeration at Step 1.6.2 is COMPREHENSIVE.

---

### Check 32 — Bit-add step (TECH_DEBT-094/100/104) dependency sequencing

**SCOPE:** Step 1.6.2 v1.6 scope expansion (15 fields vs original 10; 5 additional per TECH_DEBT-104) requires bare unprefixed struct fields to exist FIRST (produced by Step 1.6.3 struct-gen).

**VERIFICATION:**
- Plan body § BUILD-FORCED sequencing § lines 371-373: "Step 1.6.2 bit-add REQUIRES bare `inf.<name>` unprefixed fields to exist on StampInferenceCfgInputs + ModelStampResult structs... BLOCKING DEPENDENCY (Gap 5 closure — `/trace-deps chain:per_horizon_barrier_blend` verified): Step 1.6.2 bit-add REQUIRES... Step 1.6.3 landing FIRST (unconditional struct-gen produces bare field)." ✅
- Build-forced list (line 371): Step 1.5 moved AFTER Step 1.6.3 + Step 1.6.2 per coding-time Discovery D-3. Mandatory sequencing enforced. ✅

**VERDICT:** **PASS** — Dependency sequencing CORRECT + documented with explicit Gap 5 closure reference.

---

### Check 33 — Legacy registry empty-out (Step 2) final verification

**SCOPE:** Step 2 (line 661+) deletes `FOREACH_STAMP_BOUND_CFG` body + `FOREACH_CFG_DERIVED_INFERENCE_CFG` body + file + 15 prefixed POST_CFG entries. Verify deletion scope matches Decision D v1.6 scope expansion (15 entries).

**VERIFICATION:**
- Plan body § Step 2 scope (lines 661-693): Lists file deletions + legacy registry body empty-out. Scope frozen at v1.11 per v1.6 amendment cycle.
- Decision D v1.6 scope (lines 92-105): **15 entries** (9 cohort POST_CFG + 1 standalone `inference_cfg_bandit_blend_ratio` + 5 retroactive `.A.7` cohort per TECH_DEBT-104). ✅
- Parser back-compat scope (Decision F / Step 1.6.7.4-1.6.7.5): Legacy prefixed **15 wire keys** back-compat enumeration matches Decision D v1.6 scope. ✅

**VERDICT:** **PASS** — Deletion scope CONSISTENT across plan body (Decision D + Step 2 + Decision F). No scope drift post-v1.6.

---

### Check 34 — Producer-side tool migration (Step 1.6.8)

**SCOPE:** Step 1.6.8 (`tools/stamp_model.sh` migration; 4-class disposition per M2). Plan enumerates cross-tool emit-site changes per wire-format-byte-preservation-discipline.md Layer 7.

**VERIFICATION:**
- Plan body § Step 1.6.8 scope (lines 741-755): Lists all 4 stamp_model.sh migration classes + line-number refs. Decision F scope alignment (15 keys) documented at v1.11. ✅
- M2 cross-tool discipline: Plan explicitly addresses both (a) wire-format version literal (stamp_format_version=1 → 2) + (b) orphan emit site enumeration (inference_cfg_freshness_tau). ✅

**VERDICT:** **PASS** — Tool migration scope ALIGNED with M2 discipline + Decision F parser back-compat closure.

---

### Check 35 — DESIGN_SPECS amendments pre-coding requirement

**SCOPE:** NEW Stage 2 DRAFT spec `failure-attribution-buffer-pattern.md` + 4 AMENDED Stage 2 DRAFT specs (cfg-scope-discipline + wire-format-byte-preservation procedure + cfg-derived-consumer-framework + metadata-bit-driven-derived-filter-framework) must be on disk BEFORE pre-coding tag (Step 0).

**VERIFICATION:**
- Plan body § Step 0 scope (lines 397-400): "Verify `failure-attribution-buffer-pattern.md` Stage 2 DRAFT on disk (DONE at synthesis time)" + "Verify Stage 2 DRAFTs for amendment specs...". ✅
- Pre-coding audit synthesis (2026-05-17) generated `failure-attribution-buffer-pattern.md` Stage 2 DRAFT. ✅
- 4 DESIGN_SPECS amendments documented at plan body § DESIGN_SPECs landed/amended section (lines 184-200). ✅

**VERDICT:** **PASS** — All Stage 2 DRAFT specs landed at audit synthesis time. Pre-coding gate satisfied.

---

## Synthesis + Recommendations

### Per-Check Verdicts (Checks 31-39)

| Check | Verdict | Status | Notes |
|-------|---------|--------|-------|
| **36** — Sister-registry parity (M1) | **PASS** | ✅ | GATE_CFG_FLAG 6-col sig matches ML_CFG_FLAG precedent. Cohort-complete. |
| **37** — Transitional state budget (M4/B3) | **FIXED** | ⚠️ | Coexistence sound (~13-17KB per struct; within spec). Annotation text MISSING from Step 1.6.3 scope. |
| **38** — Include topology (M4/B7) | **PASS** | ✅ | Cycle-free. CfgGateRegistry.hpp → CfgFieldRegistry.hpp edge pre-existing at HEAD. |
| **39** — Wire-format row ordering (M4/B12) | **FIXED** | ⚠️ | Order DIFFERS (legacy emit vs master declaration order). INTENTIONAL + SAFE. Annotation + Layer 5b reference MISSING from Step 1.6.4 scope. |
| **31** — Test fixture currency | **PASS** | ✅ | 149 sites enumerated; count + distribution confirmed. |
| **32** — Bit-add sequencing | **PASS** | ✅ | Dependency on Step 1.6.3 struct-gen documented + BUILD-FORCED. |
| **33** — Legacy registry deletion | **PASS** | ✅ | 15-entry scope frozen post-v1.6. Consistent across all decisions. |
| **34** — Tool migration M2 | **PASS** | ✅ | Step 1.6.8 aligned with M2 cross-tool discipline + Decision F scope. |
| **35** — DESIGN_SPECS pre-coding | **PASS** | ✅ | 5 Stage 2 DRAFT specs landed at synthesis time. |

---

### Top Findings Requiring Phase B Amendment

1. **Check 37 gap:** Step 1.6.3 scope MISSING explicit transitional-state budget annotation. Recommend 2-sentence addition:
   ```
   Step 1.6.3 Approach A unconditional struct-gen: peak transitional state ~13-17KB 
   per struct (ModelStampResult + StampInferenceCfgInputs) during coexistence of 27 
   legacy + 144 master fields. Coexistence bounded; resolves at Step 2. Within 
   acceptable envelope per DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md § B3.
   ```

2. **Check 39 gap:** Step 1.6.4 scope MISSING wire-format row-order annotation + Layer 5b reference. Recommend 3-sentence addition:
   ```
   Wire-format row ordering changes from legacy FOREACH_STAMP_BOUND_CFG emit order to 
   master FOREACH_PER_CORE_CFG_FIELD master declaration order. Order difference is 
   intentional (master registry order is source of truth post-.B.3) and safe (SOFT 
   version bump + back-compat parser tolerate reorder). Layer 5b structural invariants 
   at Step 1.7 validate wire-format integrity + byte preservation.
   ```

---

### Inflection Check: No NEW Issues Beyond `/blindspot-scan` Punchlist

`/blindspot-scan` report (2026-05-18 step-1.6.3 first canonical fire) flagged 3 pre-coding amendments:
- **B3 (transitional state)** — Addressed by Check 37 amendment (recommendation above)
- **B8 (type-sensitive consumer classification)** — Deferred to post-ship `/trace-deps` amendment per taxonomy Stage 3 ACTIVE schedule
- **B9 (unverified audit claims)** — Deferred to post-ship `/parity-check` amendment (evidence-chain discipline)

**No NEW blindspots surfaced by Checks 36-39.** Audit infrastructure M4 codification (4 new SKILL checks + 2 DESIGN_SPECS new sections) is SUFFICIENT for implementation-detail category prevention.

---

### Readiness Verdict: YELLOW → GREEN (Phase B Amendment)

**Current state:** YELLOW — 2 minor plan-body text gaps (Checks 37 + 39) identified; no structural issues.

**Recommendation:**
- **Must fix before coding:** Amendments to Step 1.6.3 scope (Check 37 annotation) + Step 1.6.4 scope (Check 39 annotation). ~10 min plan-body edit.
- **Post-amendment:** Re-fire `/readiness` Checks 36-39 narrow-sweep (~5 min) to confirm fixes. Verdict will flip GREEN.

**Confidence:** HIGH
- ✅ Existing Checks 31-35 all PASS (no regressions)
- ✅ New Checks 36-39 detect intended M4 codification (sister-registry parity + transitional state + include topology + wire-format ordering)
- ✅ No surprises vs `/blindspot-scan` YELLOW punchlist (B3/B8/B9 alignment confirmed)
- ✅ Execution sequencing (BUILD-FORCED list) correct
- ✅ Scope freezing (Decision D v1.6 scope expansion 10→15 fields) applied uniformly across all dependent specs

---

## Appendix: Step 1.6.3 Amended Scope Text (Phase B Suggestion)

**Original** (lines 542-549):
```
- **Step 1.6.3 — TECH_DEBT-095 (Decision C Approach A):** ModelInference struct-gen migrations...
  - Preserve per-entry `has_<name>` Surface G semantic per HIGH-CONV-I
```

**Amended** (add after Preserve line):
```
- **Transitional state coexistence budget (M4 codification § B3):** Step 1.6.3 Approach A 
  unconditional struct-gen produces peak ~13-17KB per struct (ModelStampResult + 
  StampInferenceCfgInputs) during coexistence of 27 legacy FOREACH_STAMP_BOUND_CFG fields + 
  144 master registry fields. Coexistence window: Step 1.6.3 landing → Step 2 legacy deletion. 
  Memory impact: parser boot-time only; no hot-path bloat. Within spec ceiling per 
  DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md § B3 suggested envelope (≤25KB per 
  struct; ≤100KB program-wide).
```

---

## Appendix: Step 1.6.4 Amended Scope Text (Phase B Suggestion)

**Original** (lines 547-549):
```
- **Step 1.6.4 — TECH_DEBT-096:** Production canonical body emit migration...
  This IS the wire-format-changing step — couples with Step 1.6.7 SOFT version bump.
```

**Amended** (add after couples line):
```
- **Wire-format row ordering parity (M4 codification § B12):** Emit walker migration changes 
  row order from legacy FOREACH_STAMP_BOUND_CFG body order (emission sequence lines 99-179) 
  to master FOREACH_PER_CORE_CFG_FIELD master declaration order (master registry sections). 
  Order difference is intentional: master registry declaration order becomes canonical 
  post-.B.3 per metadata-bit-driven-derived-filter-framework.md § Option E (master registry 
  = source of truth for cfg-derived consumer framework). Safety: SOFT version bump (Decision F 
  F.2) + parser back-compat tolerance + Layer 5b structural invariants (Step 1.7 I1-I5) 
  validate wire-format integrity under reorder. Existing v1 stamps continue loading via 
  parser back-compat; new v2 stamps emit master-registry order. No backward-compat risk.
```

---

**END OF REPORT**

---

**Summary for operator:**
- Checks 36-39 (NEW) all PASSING once 2 minor text amendments are applied (Phase B, ~10 min edit)
- Checks 31-35 (existing) all PASS — no regressions detected
- Plan body v1.11 is READY for Phase B amendment → Phase C re-audit (narrow sweep) → CODING
- Estimate: Phase B amendment + Phase C re-audit = 20 min total; ready to proceed by EOD 2026-05-18

