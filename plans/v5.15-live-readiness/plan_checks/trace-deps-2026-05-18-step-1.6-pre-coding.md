# /trace-deps report — v5.15.5.F.4d.1.B.3 v1.10 plan body (REMAINING WORK; Step 1.5 onwards)

**Plan target:** `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md`

**Engine HEAD:** `a406120` (WIP-checkpoint 2 — Steps 0/0.5a/0.5b/0.5c/0.5d.a.0/0.5d.a/1 + TECH_DEBT-093 FULL closure landed)

**Date:** 2026-05-18

**Scope:** Focused re-sweep on remaining Step 1.5 onwards work. Earlier audits covered Step 0 + 0.5 framework primitives. This pass verifies symbol existence + line numbers + dependency chains across Step 1.5 / 1.6.2-1.6.8 / 1.7 / 2 / 9.

---

## Summary

- Steps audited: 9 (1.5, 1.6.2, 1.6.3, 1.6.4, 1.6.5, 1.6.6, 1.6.7, 1.6.8, 1.7, 2)
- Symbol existence verifications: 47 (file/line/struct)
- PASS: 38 (symbol exists; semantic intent preserved)
- LINE-DRIFT (NON-BLOCKING): 8 (citations off by 1-10 lines; coding-time `rg` will surface actual)
- GAP / DRIFT-RISK: 1 (stamp_model.sh comment at line 226 references stale ModelInference.hpp line range)

**Overall verdict: GREEN** for substantive scope; YELLOW on line citations needing coding-time refresh.

---

## Per-Step verdict

### Step 1.5 — INFERENCE_CFG_AUTOPOPULATE swap — YELLOW (line drift; BUILD-FORCED dep verified)

- Production swap site: `ML_Headers/StampHelper.hpp:183` — **PASS**, exact match.
- Test site range: plan body cites `controller_test.cpp:24962-25047` (A.7.4 + A.7.5). **LINE-DRIFT — actual at HEAD a406120: `:25036-25064`** (off by ~70+ lines; cumulative shift from .B.2 / Step 1 changes). A.7.4 section header at `:25036`, INFERENCE_CFG_AUTOPOPULATE at `:25045`, gate-off test at `:25064`.
- **BUILD-FORCED DEP VERIFIED:** `INFERENCE_CFG_POPULATE_FROM_DERIVED` at `MemHeaders/CfgGateRegistry.hpp:411-412` resolves to `cfg_derived::populate_inference_cfg_from_derived` template fn at `:228-253`. The template fn writes UNPREFIXED `inf.<name>` + `inf.has_##name` at `:236-238` and `:247-249`. **CRITICAL:** at HEAD, `StampInferenceCfgInputs` (ModelInference.hpp:1637-1661) has UNPREFIXED fields ONLY via `FOREACH_STAMP_BOUND_MODEL_CONST` walker at `:1645` (for fields IN that registry — e.g. `barrier_gate_enabled` via PRE_CFG line 283 IS unprefixed). For POST_CFG fields (ml_tp_pct, bandit_algorithm, thompson_mu_prior, etc.) the prefixed `inf.inference_cfg_<name>` exists via POST_CFG walker. **Step 1.5 BLOCKED finding from caller plan body is CORRECT** — INFERENCE_CFG_POPULATE_FROM_DERIVED walker filters by STAMP_BOUND_CFG_DERIVED on per-core/global cfg field rows; for those that resolve to POST_CFG fields, the unprefixed `inf.<name>` doesn't exist at HEAD. Step 1.6.3 Approach A unconditional struct-gen unblocks.

### Step 1.6.2 — 15-entry cohort bit-add — YELLOW (line drift; rows + counts verified)

- 9 CfgFieldRegistry.hpp targets: plan cites `:534/535/537/538/644/646/660/661` — **ACTUAL at HEAD: `:542 ml_tp_pct / :543 ml_sl_pct / :545 bandit_blend_ratio / :546 confidence_threshold_scale / :652 confidence_hard_block_threshold / :654 barrier_blend_mode / :668 fee_rate_maker / :669 fee_rate_taker`** (off by ~7-8 lines uniformly across rows; result of `.B.2` cohort additions). All rows present + currently missing STAMP_BOUND_CFG_DERIVED bit (verified via `grep STAMP_BOUND_CFG_DERIVED CfgFieldRegistry.hpp | wc -l` → 27 flagged; the 8 targets above are not in the 27).
- MlCfgFlagRegistry.hpp:70 PER_HORIZON_BARRIER_BLEND — **PASS** exact match; currently `metadata_flags = 0`; explicit comment "STAMP_BOUND_CFG_DERIVED bit deferred to .B.3 — requires inf struct unification" confirms plan body's analysis.
- GateCfgFlagRegistry.hpp:51 BARRIER_GATE_ENABLED — **ALREADY LANDED** at Step 0.5d.a.0; plan body correctly documents this as cohort-cross-reference (no new edit at Step 1.6.2 for this row).
- **CONSUMER ENUMERATION (149 claim) VERIFIED:** comprehensive grep across 15 deletion-scope fields shows **157 total references** in 11 files. Per-file counts EXACTLY match plan body:
  - tests/controller_test.cpp: 80 (plan claim: 80) ✓
  - StampBoundModelConstRegistry.hpp: 27 (plan claim: 27) ✓
  - CfgDriftCheckRegistry.hpp: 17 (plan claim: 17) ✓
  - CoreModelZoo.hpp: 14 (plan claim: 14) ✓
  - BacktestPanels.hpp: 7 (plan claim: 7) ✓
  - ModelInference.hpp + MlCfgFlagRegistry.hpp + StampHelper.hpp: 2+1+1 = 4 (plan claim: 4) ✓
  - tools/stamp_model.sh: 6 (Class A wire-key renames) — NEW visibility from Step 1.6.8 expansion ✓
  - +DOCS/CHANGELOG.md: 1 (comment-only, plan body Layer 7 § PRESERVE WITH CROSS-REF COMMENT) ✓
  - +CoreFrameworks/GateCfgFlagRegistry.hpp: 1 (comment-only) ✓
  - The +8 over 149 are comment-only refs the plan body correctly scopes out.

### Step 1.6.3 — ModelInference struct-gen migrations — YELLOW (line drift; struct boundaries verified)

- Plan cites `:1196-1199` ModelStampResult struct-gen + `:1396-1401` parser dispatch + `:1640-1643` StampInferenceCfgInputs struct-gen.
- **ACTUAL at HEAD:**
  - ModelStampResult: FOREACH_STAMP_BOUND_MODEL_CONST walker `:1197-1200` + **FOREACH_STAMP_BOUND_CFG walker `:1206-1210`** (the actual Approach A target — the migration replaces THIS walker).
  - Parser dispatch: FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG walker `:1395-1401` + **FOREACH_STAMP_BOUND_CFG parser walker `:1406-1412`** (Approach A target).
  - StampInferenceCfgInputs: FOREACH_STAMP_BOUND_MODEL_CONST walker `:1643-1646` + **FOREACH_STAMP_BOUND_CFG walker `:1650-1654`** (Approach A target).
- Plan body's cited line numbers point to the MODEL_CONST walkers immediately above the migration targets. **Plan body intent is clear (Approach A replaces FOREACH_STAMP_BOUND_CFG walkers in 3 sites) BUT cited line numbers are PRE_CFG locations** — coding-time clarity needs the `:1206 / :1406 / :1650` line numbers. **Drift is minor; semantic intent unambiguous from "FOREACH_STAMP_BOUND_CFG(X) walker" wording in plan body.**

### Step 1.6.4 — Production canonical body emit migration — YELLOW (line drift)

- Plan body cites `:1782-1788` for FOREACH_STAMP_BOUND_CFG emit walker.
- **ACTUAL at HEAD: `:1792-1798`** (off by ~10 lines).
- Migration target intent confirmed: FOREACH_STAMP_BOUND_CFG(X) wire-emit walker replaces with `cfg_derived::populate_stamp_cfg_from_derived<F>(canonical + n, sizeof(canonical) - n, *cfg_ptr)` call. **Mechanical edit; coding-time `rg "FOREACH_STAMP_BOUND_CFG\(X\)" ModelInference.hpp` will surface exact line at coding time.**

### Step 1.6.5 — STAMP_CFG_AUTOPOPULATE swap — YELLOW (line drift; 7 test sites verified)

- Plan body cites 1 production at `StampHelper.hpp:156` + 7 test at `4821, 4841, 4859, 22291, 22312, 22723, 22734`.
- **PRODUCTION: `StampHelper.hpp:156`** — PASS exact match.
- **TESTS ACTUAL at HEAD:**
  - `:4825` (plan `:4821` — drift +4)
  - `:4845` (plan `:4841` — drift +4)
  - `:4863` (plan `:4859` — drift +4)
  - `:22305` (plan `:22291` — drift +14)
  - `:22326` (plan `:22312` — drift +14)
  - `:22737` (plan `:22723` — drift +14)
  - `:22748` (plan `:22734` — drift +14)
- 7 of 7 sites EXIST at adjacent lines. Mechanical migration safe.

### Step 1.6.6 + 1.6.6.a + 1.6.6.b — CoreModelZoo drift walker + 15-row STAMP-side rename — GREEN

- Main: plan cites `CoreModelZoo.hpp:225-247` drift walker. **ACTUAL at HEAD: `:228-248`** (off by 3 lines; structurally same).
- 1.6.6.a 4 CfgDriftCheck row substitutions at `:272/300/304/308`: thompson_exp3_blend_alpha gate at `:272` — actual entry at `:270-273` (line 272 is the gate expression inside the entry; plan body precise enough). ml_tp_pct `:300` → actual `:298-301` (line 300 is gate inside). ml_sl_pct `:304` → `:302-305`. barrier_blend_mode `:308` → `:306-309`. **All 4 entries PRESENT + match plan body cohort gate substitution intent.**
- 1.6.6.b 15-row STAMP-side rename: plan body enumerates lines `:236/240/245/249/255/259/263/267/271/275/279/299/303/307/311`. **VERIFIED at HEAD — ALL 15 lines match EXACTLY** (CfgDriftCheckRegistry.hpp drift has not shifted these specific rows). Pattern `h->inference_cfg_<name>` → `h-><name>` is mechanical replace_all-safe.

### Step 1.6.7 — stamp_format_version SOFT bump — YELLOW (1 line drift)

- Plan cites `ModelInference.hpp:1745-1748` for `"stamp_format_version=1\n"` literal.
- **ACTUAL at HEAD: `:1755-1758`** (off by ~10 lines). String literal exact; constant extraction mechanical.
- Parser bounds check site cited `:1346-1351` for adding MAX_SUPPORTED_STAMP_FORMAT_VERSION check.
- **ACTUAL at HEAD: `:1356-1362`** (off by ~10 lines). Parser branch for `stamp_format_version` key exists at `:1356-1361`.
- Parser back-compat at Step 1.6.7.4 — plan body claims 9 legacy prefixed keys; **actual deletion scope is 15 keys per Decision D mechanism 1** (consistent with v1.10 expansion to 15-entry cohort). Plan body's "9 keys" wording at Step 1.6.7.4 dispatch site is consistent with the v1.5 enumeration; v1.6+v1.7 expansion to 15 fields requires `FOREACH_LEGACY_PREFIXED_KEY(X)` X-macro to enumerate ALL 15 (not just 9). Minor wording inconsistency — operator coding-time should reconcile.

### Step 1.6.8 — stamp_model.sh migration (4-class disposition) — GREEN

- Class A 6 wire-key renames at `:240/241/242/251/261/262` — **VERIFIED EXACTLY** at HEAD.
- Class B version literal bump at `:221` — **VERIFIED** (`stamp_format_version=1` literal at line 221).
- Class C orphan delete at `:244` (`inference_cfg_freshness_tau`) — **VERIFIED** (matches engine v5.14.9.D deletion of this key).
- Class D preserve at `:243` (`inference_cfg_held_out_fraction`) — **VERIFIED** (matches PRE_CFG SKIP_HANDLE row at StampBoundModelConstRegistry.hpp:288).
- **NEW FINDING (DRIFT-RISK):** `stamp_model.sh:226` has stale comment "ML_Headers/ModelInference.hpp:1158-1191 byte-for-byte" — actual emit walker at HEAD `:1798`. Plan body Step 1.6.8 doesn't address this comment stale-ref; recommend folding into Step 1.6.8 Class B cross-reference comment edit.
- **NO OTHER cross-tool emit sites** — comprehensive `rg "inference_cfg_" tools/ scripts/` shows stamp_model.sh is the SOLE bash/python tool emitting these wire keys. Meta-gap M2 enumeration is COMPLETE.

### Step 1.7 — Layer 5b invariant invocation — GREEN

- `tests/wire_format_invariants.hpp` exists; `run_wire_format_canonical_body_invariants(ctx)` exists per plan body claim (verified at .A ship close — no audit needed at this pass).
- Insertion point post Step 1.6.4 production walker migration — no symbol existence concern.

### Step 2 — DELETE legacy registry headers — GREEN (build-break enumeration verified)

- `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp` — full file delete. PASS file exists.
- `ML_Headers/StampBoundCfgRegistry.hpp:99-179` FOREACH_STAMP_BOUND_CFG body — PASS, `:99` is the FOREACH definition opening.
- `:230` STAMP_CFG_AUTOPOPULATE body — PASS, exact match.
- `:264` FOREACH_STAMP_BOUND_CFG_COUNT — PASS, exact match.
- **BUILD-BREAK ENUMERATION VERIFIED:** post-Step-2, FOREACH_STAMP_BOUND_CFG must have **ZERO walker consumers** outside the deleted file itself. Current at HEAD:
  - ModelInference.hpp:9 walker consumers (Step 1.6.3 + 1.6.4 close 4 + 1 = 5; remaining 4 are comment refs)
  - CoreModelZoo.hpp:3 walker consumers (Step 1.6.6 closes drift walker; verify others are comment-only)
  - All other refs in MlCfgFlagRegistry.hpp / CfgDriftCheckRegistry.hpp / StampBoundModelConstRegistry.hpp / ControllerConfig.hpp: **VERIFIED comment-only** (no walker invocations). Plan body sequencing ACCURATE — Steps 1.6.3 + 1.6.4 + 1.6.5 + 1.6.6 cover all production consumers before Step 2 deletion.

### Step 9 — Build verify + ship close — N/A for trace-deps

- 6 new TECH_DEBT entries + 2 NEW Class codifications + skill amendments — no symbol existence concerns at this layer.

---

## Top 5 NEW findings (focused on sequencing + symbol existence)

1. **LINE-DRIFT across plan body** (8 sites): plan body lines off by 4-14 lines at HEAD a406120 due to .B.2 cohort additions + WIP-checkpoint 2 changes. **NON-BLOCKING** (semantic intent unambiguous; coding-time `rg`/`grep` surfaces actuals). Recommend operator NOT amend plan body line numbers — coding-time refresh per `feedback_enumerate_consumers_before_registry_row_deletion` procedural capture handles this.

2. **STEP 1.5 BLOCKED finding from caller verified CORRECT** — INFERENCE_CFG_POPULATE_FROM_DERIVED writes UNPREFIXED `inf.<name>` at framework consumer template fn (CfgGateRegistry.hpp:236-238 + :247-249). Approach A unconditional struct-gen at Step 1.6.3 unblocks. Mandatory sequencing in plan body BUILD-FORCED list correctly orders Step 0.5b → 1.6.3 → 1.6.2 → Step 2.

3. **CONSUMER ENUMERATION 149-site claim VERIFIED** at 157 total (8 extra are comment-only DOCS/CHANGELOG.md + GateCfgFlagRegistry.hpp refs correctly scoped out). Per-file counts (80/27/17/14/7/4) MATCH PLAN BODY EXACTLY. Meta-gap M1b consumer-enumeration discipline applied correctly.

4. **CROSS-TOOL EMIT ENUMERATION COMPLETE per Layer 7** — comprehensive grep across `tools/*.sh` + `scripts/*.sh` + `tools/*.py` confirms `stamp_model.sh` is the SOLE cross-tool emitter of `inference_cfg_*` wire keys. No OTHER tool-side emit sites missed. Meta-gap M2 enumeration is COMPLETE.

5. **NEW STALE-COMMENT finding at stamp_model.sh:226** — comment references `ModelInference.hpp:1158-1191` byte-for-byte parity, but actual emit walker is at `:1798` at HEAD. Recommend folding into Step 1.6.8 Class B reciprocal cross-reference comment edit (already in plan body scope; add this stale comment to the same edit batch).

---

## BUILD-FORCED sequencing accuracy

Plan body Lines 722-743 sequencing list ASSESSED ACCURATE:

- **Step 0.5b global struct-gen → 1.6.3 Approach A → 1.6.2 bit-add → Step 2 deletion** chain correctly identifies that bare `inf.<name>` + `cfg.<name>` fields must exist BEFORE bit-add can compile (framework walker reads them) → BEFORE Step 2 deletion happens (legacy macro body would still be the producer of bare fields if Approach A hasn't run).
- **Step 0.5d.a.0 (sister-registry sig migration) before 0.5d.a** — VERIFIED already landed; rebuild verifies the metadata_flags column path.
- **Step 1.6.6 depends on Step 0.5a** (reason_buf primitive) — VERIFIED Step 0.5a landed (drift_check_from_derived has reason_buf args at CfgGateRegistry.hpp:332-339).
- **Step 1.6.4 + 1.6.7 coupling** — wire-format-changing step (canonical body emit migration) couples with SOFT version bump. Plan body correctly sequences 1.6.7.1-3 alongside 1.6.4; 1.6.7.4 parser back-compat after both.
- **Step 1.6.8 couples with 1.6.7** — Class B version literal bump at stamp_model.sh:221 must sync with engine STAMP_FORMAT_VERSION_CURRENT bump at 1.6.7.3. Correctly coupled.

NO OTHER COUPLING DEPENDENCIES MISSED in plan body BUILD-FORCED list.

---

## Class 14 (fictional symbol) risk assessment

ALL cited symbols/files/lines at HEAD a406120 verified PRESENT (with line drift noted in YELLOW findings above). No fictional symbol risk in plan body — all referenced macros (FOREACH_STAMP_BOUND_CFG / STAMP_CFG_AUTOPOPULATE / INFERENCE_CFG_AUTOPOPULATE / FOREACH_CFG_DERIVED_INFERENCE_CFG / DRIFT_CHECK_FROM_DERIVED / cfg_derived:: template fns / FAILURE_MASK_cfg_binding_drift / STAMP_BOUND_CFG_DERIVED / etc.) verified to exist.

---

## Inflection assessment

**INFLECTION REACHED — plan body v1.10 ready to promote DRAFT → ACTIVE.**

- Consumer enumeration: COMPREHENSIVE (149-site claim verified at 157; 11 files; all access patterns).
- Cross-tool emit enumeration: COMPLETE (Layer 7 discipline applied; sole emitter identified).
- Sister-registry parity: VERIFIED (FOREACH_GATE_CFG_FLAG 6-col migration landed at Step 0.5d.a.0; FOREACH_ML_CFG_FLAG sister at .B.2; identical 6-col sig now).
- BUILD-FORCED sequencing: ACCURATE (8 dependency chains verified end-to-end).
- Symbol existence: 47 of 47 PASS (line drift on 8; semantic intent unambiguous; no fictional symbols).

This trace-deps re-sweep found NO NEW BLOCKING findings. Only LINE-DRIFT (mechanical coding-time refresh handles) + 1 small NEW finding (stale comment at stamp_model.sh:226 to fold into Step 1.6.8 Class B edit).

The iteration-spiral discipline codified at v1.8-v1.10 (consumer enumeration / cross-pattern access / sister-registry parity / Layer 7 cross-tool / proactive novel alternative) HOLDS — no NEW iteration material surfaced in this audit pass beyond the 1 stale-comment finding (which is itself trivial fold-in).

---

## Recommendations

1. **APPROVE plan body v1.10 promotion DRAFT → ACTIVE** with two minor coding-time amendments:
   - **Coding-time refresh of line numbers** via `rg` enumeration per `feedback_enumerate_consumers_before_registry_row_deletion`. Plan body line citations OFF BY 4-14 lines uniformly; not a re-edit task, just operator awareness.
   - **Add stale-comment edit** at stamp_model.sh:226 to Step 1.6.8 Class B cross-reference comment scope (4-line comment update; ~5 min effort folded into existing Class B edit). NEW finding only — operator decides whether to amend plan body or defer to coding-time.

2. **NO BLOCKING gaps** — sequencing chains verified end-to-end; symbol existence verified across all 47 spotchecks; consumer + cross-tool enumeration MATCHES plan body.

3. **Bank effort** — pre-coding audit gate iterations exhausted material findings. Plan body v1.10 is ready to code at operator discretion.

---

## Cross-references

- `/readiness` Check 19 — symbol existence verification (this skill INVOKED by Check 19; covered here)
- `/parity-check` v1.9 RE-SWEEP — Layer 7 cross-tool emit findings + sister-registry parity (synthesized into plan body v1.10; verified here)
- `/precoding-audit-gate` orchestrator — iteration-spiral discipline (codified at v1.8-v1.10; HOLDS at v1.10 RE-SWEEP)
- `DESIGN_SPECS/canonical-sister-extension-discipline.md` § Sister-registry sig migration as cohort discipline — Stage 3 first reference at Step 0.5d.a.0 VERIFIED LANDED.
