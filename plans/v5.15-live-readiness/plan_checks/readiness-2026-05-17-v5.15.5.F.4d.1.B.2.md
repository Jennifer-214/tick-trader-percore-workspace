# /readiness audit — v5.15.5.F.4d.1.B.2 cohort migration

**Date:** 2026-05-17
**Plan body:** `subplans/2026-05-17-v5.15.5.F.4d.1.B.2-cohort-migration.md` v1.0 DRAFT (903 LOC)
**HEAD:** `725fe46` (v5.15.5.F.4d.1.B.1 framework consolidation shipped 2026-05-17)
**Branch:** `feat/v5.15-live-readiness`
**Scope:** 18-row cohort bit-add + gap_acceptable_threshold migration + 2 pre-canonical parity gaps + 4 retroactive .A.7 cohort + FOREACH_ML_CFG_FLAG 5→6 sig migration + FOREACH_CFG_GATE_PER_CORE sparse sidecar population + Winsor parse-time validation + 6 walker site migrations + CRIT-6 byte order option (a) auto-pick + TECH_DEBT-082 absorption candidate

**Audit reports synthesized:** 28-check pass + Check 29 (Canonical sister section) + Check 30 (Design space section) + cold-pickup completeness + stale-claim audit + TECH_DEBT verification + DESIGN_SPECS verification

---

## VERDICT — YELLOW (1 CRIT + 4 HIGH + 5 MED + 4 LOW + 2 DOC)

Plan body is **substantially well-drafted** (Check 29 + Check 30 sections present; line refs accurate; design rationale captured per per-sub-ship cycle discipline). One **CRITICAL FALSE-NEW claim** (Step 1 TECH_DEBT-082 absorption — fields already migrated) + one **HIGH structural framework-incompleteness** (FOREACH_ML_CFG_FLAG not walked by `.B.1` consumer macros — Step 7 walker migration requires framework EXTENSION at .B.2, not just bit-add) require pre-coding amendment before coding can proceed cleanly.

Auto-pick recommendations exist for all 4 design decisions but **CRIT-6 (byte order option (a)) still requires explicit operator confirmation** per plan body line 47 + audit synthesis Decision 4.

---

## Checklist verdicts (28-check + Check 29 + Check 30)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | **PASS** | Plan body asserts hot path UNTOUCHED at Verification gate § "Hot path"; cohort migration is parse/stamp-emit/slow-path/boot only |
| 2 | Train-serve parity | **PASS** | LOCKED hash captured at Step 9.4; HMAC byte preservation tested (CRIT-6 (a): expected MISMATCH against v5.14 fixture; tested explicitly) |
| 3 | Surface area | **PASS** | ~10 files touched, well-bounded to cfg-derived consumer surface |
| 4 | Pointer init / heap | **PASS** | No new heap state introduced |
| 5 | Backward compat | **DEFERRED — operator confirm CRIT-6 (a)** | stamp_format_version bump = breaking v5.14 fixtures; plan body line 47 explicitly surfaces ambiguity; operator triage required |
| 6 | Multi-threading | **PASS** | No new threads/atomics; cohort migration is registry-driven additions |
| 7 | Test coverage | **PASS** | ~25-30 NEW tests + 14 walker integration tests expand from vacuous to substantive (Step 9.6) |
| 8 | Docs + invariants | **PASS** | Step 8 documents stamp_format_version bump in `wire-format-byte-preservation-discipline.md`; CHANGELOG row planned |
| 9 | Forward maintenance | **PASS** | Framework consolidation reduces forward sites — single registry surface |
| 10 | Rollback story | **PASS** | `pre-v5.15.5.F.4d.1.B.2` anchor at Step 0; structured commit + GPG-signed tag |
| 11 | Architectural sprint detection | **PASS** | No "split/decouple/extract" keywords; cohort migration extends `.B.1` framework |
| 12 | Display ↔ execution invariant | **PASS** | Plan body Step 2 deletes manual GUI render (`GUI/SettingsPanel.hpp:414`); auto-flow preserves display↔execution alignment |
| 13 | Strategy lifecycle completeness | **N/A** | Plan doesn't touch strategy code |
| 14 | X-macro / fn-pointer table correctness | **HIGH-1** | Step 7.1 X-macro filtered walker design has ambiguity (Approach A/B/C); Decision deferred to coding time — sees HIGH-1 finding below |
| 15 | ML feature change → parity regression update | **PASS** | LOCKED hash + HMAC byte preservation tests Step 9.4 |
| 16 | New cfg field with stamp-bearing | **PASS** | `gap_acceptable_threshold` migration uses STAMP_BOUND + STAMP_BOUND_CFG_DERIVED + WARN_ON_CLAMP per CfgFieldRegistry conventions |
| 17 | Model-load path changes | **N/A** | No model-load changes |
| 18 | Reuse-audit | **PASS** | Plan body Step 6 explicitly reuses existing WARN_ON_CLAMP at `tt::cfg_parse_field<T>` (`CfgFieldDispatch.hpp:70-71`) per audit synthesis CRIT-4 (b); Decision 4 documents this |
| 19 | Pre-existing-work audit | **CRIT-1** | Step 1 absorption claim for TECH_DEBT-082 is FALSE-NEW (fields already at `CfgFieldRegistry.hpp:641/644/647`); plan body must be amended — see CRIT-1 finding below |
| 20 | Future-proofness sanity (N-of-anything) | **PASS** | Framework consolidation IS the structural fix |
| 21 | Test count assertion fragility | **PASS** | Plan body Step 9 uses `>= N` shape per existing convention |
| 22 | Auto-trigger downstream re-audit after umbrella ships | **PASS** | `.B.1` postmortem + audit synthesis Batch 1+2 informed this plan body |
| 23 | Latency accountability | **PASS** | "Hot path UNTOUCHED"; "HOT_PATH_CHANGELOG: NONE entry" explicitly stated |
| 24 | Mirror-function call-sequence enumeration | **PASS** | Cohort migration extends existing framework — no new mirror functions |
| 25 | TECH_DEBT.md surface-area scan | **MED-1** | TECH_DEBT-082 already CLOSED at v5.15.5.F.4d (verified at HEAD); plan body §TECH_DEBT auto-write line 863 claims open status — see MED-1 |
| 26 | Symmetry test placeholder | **PASS** | Step 9.6 walker integration tests verify framework consumer macros |
| 27 | DESIGN_SPECS pattern-application | **PASS** | Plan body cites `cfg-derived-consumer-framework.md` v1.1→v1.2 + `canonical-sister-extension-discipline.md` v1.1 + `wire-format-byte-preservation-discipline.md` + `categorical-tag-applicability-pattern.md` + `metadata-bit-driven-derived-filter-framework.md` + `future-oriented-plan-template.md` — all DESIGN_SPECs exist on disk at workspace |
| 28 | Test-strength anti-regression | **PASS** | No test weakening; ~25-30 new + 14 expand-from-vacuous |
| **29** | **Canonical sister registries considered section** | **PASS — with 1 LOW gap** | Section present (lines 97-117); 9 candidates audited; per-candidate verdicts + rationale provided. **One gap:** plan body line 111 claims `FOREACH_CFG_DERIVED_INFERENCE_CFG` "eliminated at `.B.1`" — actual HEAD still has it (deletion deferred to `.B.3`). See LOW-1. |
| **30** | **Design space + future-oriented choice section** | **PASS** | Section present (lines 29-95); 4 decisions enumerated; each has ≥2 options + auto-pick rationale + sharp-trade-off surfacing (Decision 1 CRIT-6 explicitly surfaces ambiguity per `feedback_auto_pick_future_oriented`) |
| 31 | Wider-build verification at predecessor sprint close | **PASS** | `.B.1` postmortem documents `./build.sh all` 5 binaries clean (`postmortems/2026-05-17-v5.15.5.F.4d.1.B.1-postmortem.md` §Verification) |

---

## CRITICAL findings

### CRIT-1 — Step 1 TECH_DEBT-082 absorption claim is FALSE-NEW

**Severity:** CRIT (Check 19 — pre-existing-work audit FAILURE; FALSE-NEW = thing already exists)

**Plan body claim** (lines 364-370):
> **Decision at Step 1 boundary:** TECH_DEBT-082 absorption (3 `.F.5` residual fields — `confidence_ic_floor` + `lazy_rebuild_price_threshold_pct` + `exit_threshold`). Per audit synthesis: low effort, high consistency value. **Auto-pick: ABSORB into `.B.2` Step 1**:
> - Add 3 more rows to FOREACH_PER_CORE_CFG_FIELD (or FOREACH_GLOBAL_CFG_FIELD) for these fields
> - 3 more rows in 18-row total → 20-row mechanical cohort bit-add
> - Closes TECH_DEBT-082 at `.B.2` instead of `.F.4f` cleanup ship

**Reality at HEAD `725fe46`:** TECH_DEBT-082 is **already CLOSED** at v5.15.5.F.4d (per `tick-trader-percore-workspace/DOCS/TECH_DEBT.md:1555` "Status: **CLOSED at v5.15.5.F.4d 2026-05-16**"). The 3 fields are already migrated to `FOREACH_PER_CORE_CFG_FIELD`:

- `lazy_rebuild_price_threshold_pct` → `CoreFrameworks/CfgFieldRegistry.hpp:641` (KIND_DOUBLE_PCT, FPN<F>)
- `exit_threshold` → `CoreFrameworks/CfgFieldRegistry.hpp:644` (KIND_DOUBLE, FPN<F>)
- `confidence_ic_floor` → `CoreFrameworks/CfgFieldRegistry.hpp:647` (KIND_DOUBLE, `double` storage per H4 non-accounting)

The plan body conflates two distinct deferred-items lists:
1. TECH_DEBT-082 = **REGISTRY MIGRATION** (already closed) — fields ARE in FOREACH_PER_CORE_CFG_FIELD
2. STAMP_BOUND_CFG_DERIVED **BIT-ADD** for these 3 fields = OPEN QUESTION (the real `.B.2` candidate)

**Recommendation:** REFRAME Step 1 absorption as **"STAMP_BOUND_CFG_DERIVED bit-add for 3 fields already in registry"** (with explicit eligibility audit per `cfg-flag-eligibility-criteria.md` — DO they participate in stamp/drift? `confidence_ic_floor` likely YES; `exit_threshold` likely YES; `lazy_rebuild_price_threshold_pct` likely NO — it's a performance-only knob). Effort estimate stays low (mechanical 0-3 bit-adds depending on eligibility verdict). Plan body §"NOT IN scope (explicit deferral)" line 302 also needs reframe — TECH_DEBT-082 is closed; the open item is "stamp-bound participation audit for these 3 fields".

**Sister artifact for amendment:** plan body §"TECH_DEBT auto-write expectations" line 863 currently says TECH_DEBT-082 "CLOSED if absorbed; remains OPEN if operator overrides" — should be reframed as "verify TECH_DEBT-082 actually CLOSED at HEAD; open NEW TECH_DEBT for stamp-bound participation if any of 3 fields gain bit at `.B.2`".

**Effort to amend:** ~10 min plan body edit (Step 1 Decision wording + NOT IN scope row 302 + TECH_DEBT auto-write line 863).

---

## HIGH findings

### HIGH-1 — `FOREACH_ML_CFG_FLAG` is NOT walked by `.B.1` cfg_derived consumer macros (framework EXTENSION needed at `.B.2`)

**Severity:** HIGH (Check 14 — X-macro dispatch correctness; framework-incompleteness affects 5 cohort fields)

**Plan body claim** (Step 4 + Step 7.1):
- Step 4 adds `STAMP_BOUND_CFG_DERIVED` bit to 5 `FOREACH_ML_CFG_FLAG` rows (CONFIDENCE_COMPOSITE_ENABLED, RIDGE_WITHIN_HORIZON, RIDGE_ACROSS_HORIZONS, EXIT_BLENDER_MODE, PER_HORIZON_BARRIER_BLEND)
- Step 7.1 struct-gen X_STRUCT_GEN_ML_CFG_FLAG walks `FOREACH_ML_CFG_FLAG` filtered by STAMP_BOUND_CFG_DERIVED
- Step 9.6 says walker integration tests should verify ml_cfg_flag bitmap iteration

**Reality at HEAD `725fe46`:** The `.B.1` shipped `cfg_derived::populate_inference_cfg_from_derived` + `populate_stamp_cfg_from_derived` + `drift_check_from_derived` template fns at `MemHeaders/CfgGateRegistry.hpp:198-260` walk ONLY:

- `FOREACH_PER_CORE_CFG_FIELD` (with `STAMP_BOUND_CFG_DERIVED` filter)
- `FOREACH_GLOBAL_CFG_FIELD` (with same filter)

They do **NOT** walk `FOREACH_ML_CFG_FLAG`. Adding the metadata bit to ML_CFG_FLAG rows at Step 4 produces no observable behavior change because no consumer iterates that registry filtered by the bit.

**Two paths to resolve:**

(a) **EXTEND `.B.1` framework at `.B.2`:** Add a third X_*_ML_CFG_FLAG walker macro to each of the 3 template fns; filter by `STAMP_BOUND_CFG_DERIVED` bit; iterate over ml_cfg_flags bitmap to extract per-flag value. ~15-30 LOC framework addition; structural shape preserved. ~30-45 min effort.

(b) **DROP the ML_CFG_FLAG bit-add at `.B.2`:** Defer 5 bitmap rows' stamp-bound participation to a later ship; legacy `FOREACH_STAMP_BOUND_CFG` walker (still alive at `.B.2`) continues to emit these via existing rows (`exit_blender_mode`/`ridge_within_horizon`/etc. already in legacy registry per `StampBoundCfgRegistry.hpp:106-159`). When legacy registry empties at `.B.3`, these 5 rows need framework-extension.

**Recommendation:** Auto-pick **(a) framework EXTENSION at `.B.2`** per per-sub-ship cycle discipline ("audit ENOUGH to make THIS sub-ship structurally sound") — defer-class-3 (the 5 bitmap rows would be orphaned at `.B.3` without framework extension; better to extend now). Document the framework extension as new Step 0.5 (analogous to `.B.1`'s template-fn-wrapper Step 0.5 added at coding time). Plan body §"DESIGN_SPECs landed/amended" line 145 should track this as `cfg-derived-consumer-framework.md` v1.1 → v1.3 (not just v1.2) — the framework expands to 3 source registries from 2.

**Effort to amend:** ~30 min plan body edit (add Step 0.5 framework extension; clarify Steps 4 + 7.1 + 9.6 dependencies on the extension).

### HIGH-2 — `stamp_format_version` is a string literal in snprintf, NOT a named constant

**Severity:** HIGH (Check 19 — false-REUSE / signature drift; Step 8 implementation simplification doesn't match reality)

**Plan body claim** (Step 8, lines 671-679):
> Bump the constant by 1:
> ```cpp
> static constexpr uint32_t STAMP_FORMAT_VERSION = 7;  // was 6
> ```

**Reality at HEAD `725fe46`:** `ML_Headers/ModelInference.hpp:1747` emits the value as a string literal inside snprintf:
```cpp
int wrote = snprintf(canonical + n, sizeof(canonical) - n,
    "stamp_format_version=1\n");
```

There is no `static constexpr uint32_t STAMP_FORMAT_VERSION` constant. The literal `=1` at line 1747 has been hardcoded since v5.9.0 (per comment at line 1713). Bumping requires either:
1. Adding a NEW constant + replacing the hardcoded literal at line 1747 (preferred future-oriented shape; future bumps mechanical via 1 constant change)
2. Direct string-literal edit of "stamp_format_version=1\n" → "stamp_format_version=2\n" (current shape; brittle for future bumps)

Plan body Step 8 example assumes option 1 but doesn't say so; coding-time agent might pick option 2 (the literal-string edit) which doesn't future-proof.

**Recommendation:** Plan body Step 8 should EXPLICITLY direct: introduce `static constexpr uint32_t STAMP_FORMAT_VERSION = 2; // .B.2 bump per CRIT-6 (a)` at suitable location (e.g., `ModelInference.hpp` near line 1170 where `stamp_format_version` field lives in `ModelStampResult`); replace the line-1747 string literal with `%d` format + the constant. This is the future-oriented shape per `feedback_overengineering_boundary_when_future_easier`.

**Effort to amend:** ~5 min plan body edit (clarify Step 8 wording + locate line 1170 nearby).

### HIGH-3 — Plan body §"Canonical sister registries considered" claims `FOREACH_CFG_DERIVED_INFERENCE_CFG` "eliminated at `.B.1`"

**Severity:** HIGH (Check 29 — canonical sister section gap; stale claim about predecessor ship)

**Plan body claim** (line 111):
> `FOREACH_CFG_DERIVED_INFERENCE_CFG` | (eliminated at `.B.1`) | n/a | **DELETED** | Already removed by `.B.1` framework consolidation

**Reality at HEAD `725fe46`:** `FOREACH_CFG_DERIVED_INFERENCE_CFG` is **NOT eliminated**. Still present at:
- `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101` (full registry body; 16 rows)
- `CoreFrameworks/MetaRegistry.hpp:99` (FOREACH_REGISTRY row; description: "Cfg-derived inference cfg fields (legacy; deletion deferred to `.B.3` after `.B.2` cohort migration validates new framework).")
- `ML_Headers/StampHelper.hpp:183` (production caller: `INFERENCE_CFG_AUTOPOPULATE(inf, cfg)`)
- `tests/controller_test.cpp:24982` (count assertion: `FOREACH_CFG_DERIVED_INFERENCE_CFG_COUNT == 16`)

`.B.1` postmortem (Discovery 1) documents deletion was DEFERRED to `.B.3` per regression risk. Plan body's canonical-sister table row 111 is stale.

**Recommendation:** Plan body line 111 should be reframed:
> `FOREACH_CFG_DERIVED_INFERENCE_CFG` | `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101` (16 rows) | NO new artifact | **SUPERSEDED — deletion at `.B.3`** | Legacy registry; `.B.1` shipped replacement infrastructure; `.B.2` exercises replacement non-empty; `.B.3` deletes legacy + finalizes consolidation.

This is cosmetic but important — the canonical sister section is the discipline; inaccuracies here break the discipline's value.

**Effort to amend:** ~3 min plan body edit (rewrite line 111 row).

### HIGH-4 — Plan body Step 3 conflates "retroactive .A.7 cohort migration" with POST_CFG entry deletion

**Severity:** HIGH (Check 19 — false-REUSE claim; misframes existing `inference_cfg_<name>` POST_CFG entries)

**Plan body claim** (Step 3, lines 423-437):
> 3. `ml_tp_pct` at `CfgFieldRegistry.hpp:525`:
>    - APPEND `| CfgFieldDescriptor::STAMP_BOUND_CFG_DERIVED` (STAMP_BOUND already set or not? verify)
>    - DELETE manual POST_CFG entry in `StampBoundModelConstRegistry.hpp` (search for `ml_tp_pct`)

**Reality at HEAD `725fe46`:**
- `ml_tp_pct` at `CfgFieldRegistry.hpp:525` — current metadata_flags is `0` (no STAMP_BOUND); the `applies_to_strategy_cat = STRAT_CAT_ML` + `lives_in_struct = STRUCT_CFG`. NOT in legacy `FOREACH_STAMP_BOUND_CFG`.
- The POST_CFG entry the plan refers to at `StampBoundModelConstRegistry.hpp:454-456` is `X(inference_cfg_ml_tp_pct, ...)` (PREFIXED with `inference_cfg_`), NOT `X(ml_tp_pct, ...)`. This entry is the STAMP BODY EMIT side for the field after it's been populated into `inf.inference_cfg_ml_tp_pct` (cfg-derived field on the inf struct).

So Step 3 actually requires two distinct mechanical changes:
1. Add `STAMP_BOUND | STAMP_BOUND_CFG_DERIVED` to `CfgFieldRegistry.hpp:525` row (the SOURCE cfg field's metadata)
2. **DO NOT DELETE** `StampBoundModelConstRegistry.hpp:454-456` — that's the EMIT side; deleting breaks the wire-format output. It would only be deleted at `.B.3` when the new framework's `STAMP_CFG_POPULATE_FROM_DERIVED` walker emits the `inference_cfg_<name>` bytes from the master registry walk.

**Same issue applies to ml_sl_pct (line 430-431), barrier_blend_mode (line 433), per_horizon_barrier_blend (line 436), AND `bandit_blend_ratio` (line 420-422).**

The misframing carries risk: at coding time, the agent might delete the POST_CFG entries (per plan body literal wording) → wire-format bytes change WITHOUT the framework walker yet producing them (the framework only iterates rows that BOTH have STAMP_BOUND_CFG_DERIVED bit AND the inf struct has matching `has_inference_cfg_<name>` + `inference_cfg_<name>` fields). The framework walker shape at `.B.1` already requires StampInferenceCfgInputs struct to have `inference_cfg_<name>` fields — these fields are auto-generated by the legacy `FOREACH_CFG_DERIVED_INFERENCE_CFG` walker at `StampInference.hpp:~210-220` (similar X-macro pattern).

**Recommendation:** Plan body Step 3 must be reframed:
1. Step 3 ADDS `STAMP_BOUND | STAMP_BOUND_CFG_DERIVED` bits to `CfgFieldRegistry.hpp` rows for ml_tp_pct/ml_sl_pct/barrier_blend_mode/bandit_blend_ratio + `FOREACH_ML_CFG_FLAG` STAMP_BOUND_CFG_DERIVED for per_horizon_barrier_blend (which is bitmap-resident; Step 4 handles)
2. Step 3 EXPLICITLY does NOT delete POST_CFG entries; those stay for byte-emit
3. At `.B.3` legacy empty-out, POST_CFG entries get cleaned up alongside `FOREACH_CFG_DERIVED_INFERENCE_CFG` deletion

This affects Step 3 (lines 412-437) + the related claims in Bug Classes table (line 130).

**Effort to amend:** ~15 min plan body edit (rewrite Step 3 with corrected file:line context).

---

## MED findings

### MED-1 — TECH_DEBT-082 status at `.B.2` ship-close auto-write claims premature

**Severity:** MED (Check 25 — TECH_DEBT auto-write contract; bookkeeping accuracy)

**Plan body claim** (line 863):
> **TECH_DEBT-082** ... CLOSED if absorbed at Step 1 per auto-pick; OR remains OPEN if operator overrides

**Reality:** TECH_DEBT-082 already CLOSED at v5.15.5.F.4d 2026-05-16 (per TECH_DEBT.md:1555). Plan body should NOT claim ship-close action on already-closed TECH_DEBT.

**Recommendation:** Plan body line 863 → "verify TECH_DEBT-082 still shows CLOSED at HEAD; if new stamp-bound-participation audit at Step 1 surfaces 1-3 fields gaining STAMP_BOUND_CFG_DERIVED bit, open NEW TECH_DEBT-09X tracking the bit-add migration completeness".

**Effort:** ~3 min.

### MED-2 — Step 5 sparse sidecar entry count (~20 entries) doesn't include `gap_acceptable_threshold` or `trading_mode` correctly

**Severity:** MED (Check 14 — X-macro dispatch correctness; sparse sidecar default semantics)

**Plan body claim** (Step 5, lines 222-228, 506-510):
> **Always-emit rows: NO entries** (default gate applies):
>   - `trading_mode` (Operational; always emit)
>   - `gap_acceptable_threshold` (engine validation threshold; always emit)
>   - `ml_buy_threshold` (always emit per legacy semantics)

> `FOREACH_CFG_GATE_GLOBAL`: empty at `.B.2`

This claim is CORRECT for the SIDECAR (sparse — only non-default entries). But the sidecar is empty for the global registry at `.B.2` per the auto-pick. However:
- `gap_acceptable_threshold` migrating to FOREACH_GLOBAL_CFG_FIELD with STAMP_BOUND_CFG_DERIVED bit means it WILL be walked by `populate_stamp_cfg_from_derived` (Step 7.4); since sidecar is empty for global, default gate "true" applies → byte emit unconditionally. This matches plan body intent.
- `trading_mode` is similar — Step 1 bit-add → walked → default-gate-true → unconditional emit.

The MED is informational: Step 5 explicit comment "FOREACH_CFG_GATE_GLOBAL: No global-cohort entries at `.B.2`" is correct BUT the plan body Verification gate (line 838) says "`FOREACH_CFG_GATE_GLOBAL` has 0 entries (all global rows use default gate)" — which is correct. No actual error; just want to confirm plan body's mental model is sound: empty sidecar + STAMP_BOUND_CFG_DERIVED bit on global row = always-emit. **Verified.** No amendment needed.

**Recommendation:** No edit required; flagged for awareness during coding to verify expected byte-emit behavior in Step 9.4 LOCKED hash regeneration.

### MED-3 — Step 7.5 design churn between v1.0 plan body's two readings

**Severity:** MED (Check 14 — internal consistency between scope and Step bodies)

**Plan body claim** (Step 7.5, lines 633-645):

Plan body text 633-637 first says "Keep STAMP_CFG_AUTOPOPULATE(inf, cfg) call at `.B.2`" — then text 640-645 corrects itself with "Wait — this needs more thought..." analysis and concludes:
> So at `.B.2`:
> - Walker 1788 (canonical body emit): migrates to `STAMP_CFG_POPULATE_FROM_DERIVED(buf, cap, cfg)` direct buffer emit
> - Walker 156 (StampHelper inf struct populate): KEEP `STAMP_CFG_AUTOPOPULATE(inf, cfg)` legacy call

The inline conclusion is correct but the section reads like an unfinished draft (literal "Wait — this needs more thought" comment in plan body). This is a presentation/discipline concern, not technical.

**Recommendation:** Plan body Step 7.5 should be cleaned up — remove the "Wait — this needs more thought" interjection; present the final position cleanly. Future-oriented plans should not contain mid-thought interjections that reader has to parse.

**Effort:** ~5 min.

### MED-4 — Verification gate ship-specific test count target ~3235-3250 may be aggressive

**Severity:** MED (Check 21 — test count assertion accuracy)

**Plan body claim** (lines 273, 757, 827):
> tests GREEN (expected ~3235-3250)

Counting: HEAD shows `3215/0` from `.B.1` close. Plan body Step 9 says "~25-30 NEW tests" + "14 walker integration tests expand from vacuous PASS to substantive". The 14 are existing tests being upgraded (still 14); the 25-30 are new. So count target should be:
- 3215 (baseline) + 25-30 (new) = 3240-3245

This matches plan body's ~3235-3250 estimate (slight overshoot at low end is acceptable buffer). **OK.**

**Recommendation:** No amendment; flag for ship-close to verify count actually lands in 3240-3245 range (regression alert if outside).

### MED-5 — Plan body §10 Step 10 build verify mentions `tools/calls_graph_diff.sh` but doesn't capture expected output

**Severity:** MED (Check 11 — architectural sprint detection sub-rule)

**Plan body claim** (Step 10, line 760):
> `tools/calls_graph_diff.sh`               # expect: empty diff (no hot-path callgraph changes)

This is correct for a non-architectural-sprint cohort migration. But "expect: empty diff" is ambiguous — does empty mean "no orphans found" or "no changes from baseline"? Without explicit guidance, coding-time agent might misinterpret the output.

**Recommendation:** Plan body Step 10 should explicitly capture expected output: "`tools/calls_graph_diff.sh` exits 0 + reports 0 new orphans; hot-path-call list unchanged from `.B.1` close baseline".

**Effort:** ~2 min.

---

## LOW findings (informational)

### LOW-1 — Plan body line 111 stale claim about `FOREACH_CFG_DERIVED_INFERENCE_CFG` elimination

**Severity:** LOW (subsumed by HIGH-3 above; flagged separately as it appears in Check 29 review)

Already covered in HIGH-3. Same fix.

### LOW-2 — Plan body Step 2 "ADD source row" example column shape needs cross-check against neighbors

**Severity:** LOW (informational; plan body already notes this)

**Plan body claim** (Step 2, line 404):
> (Verify exact column shape against neighbors in FOREACH_GLOBAL_CFG_FIELD; this is approximate.)

Plan body honestly flags the approximation. Good practice. Coding-time agent must verify the FOREACH_GLOBAL_CFG_FIELD X-macro column shape against existing rows (e.g., `trading_mode` at line 394 is a 12-column tuple in current FOREACH_GLOBAL_CFG_FIELD).

**Recommendation:** None; plan body is honest about the approximation. Coding agent must verify.

### LOW-3 — Plan body line 167 "search line via Step 1 grep" for `risk_min_size_pct`

**Severity:** LOW (Check 29 — cold-pickup completeness; mechanical gap)

**Plan body claim** (line 167):
> `risk_min_size_pct` (search line via Step 1 grep — likely `:617` or `:620`)

**Reality at HEAD `725fe46`:** `risk_min_size_pct` is at `CoreFrameworks/CfgFieldRegistry.hpp:617`. Plan body could be more precise.

**Recommendation:** Replace "search line via Step 1 grep" with exact line `:617`.

**Effort:** ~1 min.

### LOW-4 — Plan body §"Pre-coding triggers" line 871 + 882 claim audit synthesis "TO BE CREATED"

**Severity:** LOW (Check 22 — auto-trigger downstream re-audit)

**Plan body claim** (lines 12, 874):
> **Pre-coding audit synthesis:** `plan_checks/2026-05-XX-v5.15.5.F.4d.1.B.2-audit-synthesis.md` (TO BE CREATED post `/precoding-audit-gate` fire on this plan body)

The audit synthesis filename uses `2026-05-XX` placeholder. At synthesis time (likely same day = 2026-05-17), this should be `2026-05-17-v5.15.5.F.4d.1.B.2-audit-synthesis.md`.

**Recommendation:** Fill in `2026-05-17` once synthesis is actually written; this happens AFTER `/readiness` (the current audit) lands as part of /precoding-audit-gate Batch 1.

**Effort:** Trivial; happens during synthesis write.

---

## DOC findings

### DOC-1 — DESIGN_SPEC `cfg-derived-consumer-framework.md` v1.1 "Files migrated" section is stale

**Severity:** DOC (Check 29 / Check 27 — DESIGN_SPECS drift)

**DESIGN_SPEC claim** (`cfg-derived-consumer-framework.md:176-178`):
> ### Files migrated
>
> - `ML_Headers/StampHelper.hpp:183` — `INFERENCE_CFG_AUTOPOPULATE` → `INFERENCE_CFG_POPULATE_FROM_DERIVED`
> - `CoreFrameworks/MetaRegistry.hpp:99` — remove FOREACH_CFG_DERIVED_INFERENCE_CFG; add FOREACH_CFG_GATE + 3 consumer macros
> - `tests/controller_test.cpp:24962-25047` — A.7 round-trip + gate-off semantics tests update

**Reality at HEAD `725fe46`:** None of these migrations occurred at `.B.1` — they were ALL deferred to `.B.2`/`.B.3` per Discovery 1 in postmortem. The DESIGN_SPEC is documenting an INTENDED post-`.B.1` state, not the actual shipped state.

**Recommendation:** DESIGN_SPEC `cfg-derived-consumer-framework.md` should be amended at `.B.2` ship close to reflect actual shipped state: "Files migrated at `.B.2`" (after `.B.2` actually migrates them) + "Files deleted at `.B.3`". Plan body §"DESIGN_SPECs landed/amended" already lists `cfg-derived-consumer-framework.md v1.1 → v1.2` — verify the amendment captures this stale-section cleanup. Not a `.B.2` blocker.

**Effort:** ~5 min DESIGN_SPEC edit at `.B.2` ship close.

### DOC-2 — DESIGN_SPEC `cfg-derived-consumer-framework.md` references singular `FOREACH_CFG_GATE` (plural in actual ship)

**Severity:** DOC (Check 27 — DESIGN_SPECS drift)

**DESIGN_SPEC claim** (`cfg-derived-consumer-framework.md:64-65, 124, 171`):
> NEW at `.B.1`: `FOREACH_CFG_GATE` — sparse sidecar mapping `row name → gate_when_expr`

**Reality:** `.B.1` shipped TWO sidecars: `FOREACH_CFG_GATE_PER_CORE` + `FOREACH_CFG_GATE_GLOBAL` at `MemHeaders/CfgGateRegistry.hpp:65 + :75`. Plan body matches reality.

**Recommendation:** Amend `cfg-derived-consumer-framework.md` to use plural form. Coordinate with `cfg-derived-consumer-framework.md v1.1 → v1.2` amendment at `.B.2` ship close.

**Effort:** ~3 min DESIGN_SPEC edit.

---

## Cold-pickup completeness verdict (10 fields)

| # | Field | Verdict | Notes |
|---|------|---------|-------|
| C.1 | Branch state | **PASS** | `feat/v5.15-live-readiness` named at line 3 |
| C.2 | Phase execution order matches dependency | **PASS** | Steps 0-10 follow build order; Step 0.5 absent (HIGH-1 would add) |
| C.3 | First concrete move | **PASS** | Step 0 has explicit `git tag -s -a pre-v5.15.5.F.4d.1.B.2 -m "..."` |
| C.4 | Function/constructor names cited | **MED** | Most named; "search via grep" for `risk_min_size_pct` (LOW-3) + `ControllerConfig_ParseFile`/`cfg_parser_finalize` for Step 6 |
| C.5 | File:line refs for tests/baselines | **PASS** | tests/controller_test.cpp:5141-5146 + :4893 + :26140 cited |
| C.6 | Stale-claim audit | **HIGH-3** | Plan body line 111 "FOREACH_CFG_DERIVED_INFERENCE_CFG eliminated at `.B.1`" is stale |
| C.7 | Effort reconciles with file size deltas | **PASS** | Effort estimate not explicit but scope (~10 files, ~25-30 LOC framework additions + ~20 sidecar entries + cohort bit-adds) is reasonable |
| C.8 | Source-audit references | **PASS** | `plan_checks/2026-05-17-v5.15.5.F.4d.1.B-audit-synthesis.md` cited (line 10) + `postmortems/2026-05-17-v5.15.5.F.4d.1.B.1-postmortem.md` (line 11) |
| C.9 | Predecessor / dependent plans named with paths | **PASS** | Predecessor `.B.1` named at line 4 + path; successor `.B.3` at line 6 + path |
| C.10 | Tag names locked | **PASS** | `pre-v5.15.5.F.4d.1.B.2` rollback anchor + `v5.15.5.F.4d.1.B.2` GPG-signed tag |

**Cold-pickup overall:** 8/10 (PASS); 1 HIGH-3 stale claim + 1 MED-class C.4 search reference. Above PASS threshold per cold-pickup rule.

---

## Stale-claim audit (spot-check 10 random refs)

| Plan body claim | Actual at HEAD | Verdict |
|---|---|---|
| `ridge_lambda` at `CfgFieldRegistry.hpp:559` | `:559` ✓ | PASS |
| `risk_min_size_pct` at `:617 or :620` | `:617` | PASS (LOW-3 imprecision) |
| `trading_mode` at `:394` | `:394` ✓ | PASS |
| `gap_acceptable_threshold` at `ControllerConfig.hpp:889` | `:889` ✓ | PASS |
| `:1729` default + `:2554` parser | both ✓ | PASS |
| `BacktestSharded.hpp:294 + :341` | both ✓ | PASS |
| `HotSwap.hpp:137 + :243` | both ✓ | PASS |
| `EnsembleHotSwap.hpp:84 + :94` | both ✓ | PASS |
| `EngineSharded.hpp:1043` | `:1043` ✓ | PASS |
| `GUI/SettingsPanel.hpp:414` | `:414` ✓ | PASS |
| `ModelInference.hpp` walker sites `:1199 / :1401 / :1643 / :1788` | all ✓ | PASS |
| `StampHelper.hpp:156` STAMP_CFG_AUTOPOPULATE | `:156` ✓ | PASS |
| `:183` INFERENCE_CFG_AUTOPOPULATE | `:183` ✓ | PASS |
| `CoreModelZoo.hpp:243` drift check | `:243` ✓ | PASS |
| `CoreModelZoo.hpp:796` stamp parser | `:796` ✓ | PASS |
| `MlCfgFlagRegistry.hpp:52-65` 12-row registry | rows 53-64 (12 rows) | PASS (off-by-1 in start line) |
| `:70` X_GEN_ML_CFG_BIT | `:70` ✓ | PASS |
| `:82-83` X_GEN_ML_CFG_MASK | `:82-83` ✓ | PASS |
| `:76-77` static_assert(ML_CFG_COUNT <= 16) | `:76-77` ✓ | PASS |
| `tests/controller_test.cpp:5141-5146` test sites | confirmed `:5122-5146` cluster ✓ | PASS |

**Stale-claim audit: PASS** with one off-by-1 (LOW; row range starts at 53 not 52) + LOW-3 imprecision. Plan body's mechanical line refs are accurate.

---

## TECH_DEBT entries verification

| Cited entry | Status at HEAD | Notes |
|---|---|---|
| TECH_DEBT-082 | **CLOSED at v5.15.5.F.4d 2026-05-16** | CRIT-1 / MED-1 — plan body claims as absorbable |
| TECH_DEBT-085 | OPEN; IN-FLIGHT (`.A` + `.B.1` shipped; `.B.2`/`.B.3`/`.C`/`.D` pending) | Plan body line 862 cites correctly |
| NEW TECH_DEBT-09X (stamp_format_version bump procedure) | TO BE OPENED at `.B.2` ship close | Plan body line 864 cites correctly |
| Possible NEW TECH_DEBT (StampHelper.hpp:156 STAMP_CFG_AUTOPOPULATE legacy orphan) | TO BE OPENED at `.B.2`; closed at `.B.3` | Plan body line 865 cites correctly |

---

## DESIGN_SPECS referenced

All DESIGN_SPECs referenced in plan body verified to exist at `tick-trader-percore-workspace/DESIGN_SPECS/`:
- `canonical-sister-extension-discipline.md` (Stage 3 ACTIVE v1.1) ✓
- `cfg-derived-consumer-framework.md` (Stage 3 ACTIVE v1.1; DOC-1 / DOC-2 drift) ✓
- `future-oriented-plan-template.md` (Stage 3 ACTIVE v1.1) ✓
- `wire-format-byte-preservation-discipline.md` ✓
- `metadata-bit-driven-derived-filter-framework.md` ✓
- `categorical-tag-applicability-pattern.md` ✓
- `pattern-codification-lifecycle.md` ✓
- `sidecar-override-pattern-for-registry-auto-flows.md` ✓

---

## Plan amendment list (ordered)

1. **CRIT-1** — REFRAME Step 1 TECH_DEBT-082 absorption claim (false-NEW; fields already migrated at `.F.4d`)
2. **HIGH-1** — ADD Step 0.5 framework extension to walk `FOREACH_ML_CFG_FLAG` (filtered by STAMP_BOUND_CFG_DERIVED); update Steps 4 + 7.1 + 9.6 dependencies
3. **HIGH-2** — Step 8: introduce `static constexpr uint32_t STAMP_FORMAT_VERSION = 2;` + replace `ModelInference.hpp:1747` string literal with format string + constant
4. **HIGH-3** — Plan body line 111 amend canonical sister verdict for `FOREACH_CFG_DERIVED_INFERENCE_CFG` (SUPERSEDED — deletion at `.B.3`, not eliminated at `.B.1`)
5. **HIGH-4** — Step 3 retroactive .A.7 cohort: do NOT delete POST_CFG entries at `.B.2` (they migrate at `.B.3` legacy empty-out); ADD STAMP_BOUND_CFG_DERIVED bits only
6. **MED-1** — Line 863 TECH_DEBT-082 auto-write reframe (already CLOSED; open new TECH_DEBT for stamp-bound participation if applicable)
7. **MED-3** — Step 7.5 cleanup (remove "Wait — this needs more thought" interjection)
8. **MED-5** — Step 10 calls_graph_diff.sh expected output explicit
9. **LOW-3** — Line 167 `risk_min_size_pct` exact line `:617`
10. **DOC-1 / DOC-2** — Amend `cfg-derived-consumer-framework.md` v1.1 → v1.2 at `.B.2` ship close (Files migrated section + plural FOREACH_CFG_GATE_PER_CORE/_GLOBAL)

**Plan body amendment effort:** ~70-90 min focused (mostly mechanical text edits; HIGH-1 is the substantive scope expansion).

---

## Recommendations + decision points

### Must fix before coding

- **CRIT-1** Step 1 TECH_DEBT-082 absorption reframe — plan body claims a false-NEW; coding agent would discover this at Step 1 build verify
- **HIGH-1** Framework extension for FOREACH_ML_CFG_FLAG — without this, Steps 4 + 7.1 + 9.6 produce no observable behavior change for 5 bitmap rows
- **HIGH-4** Step 3 POST_CFG entry deletion claim — coding agent following plan literally would break wire format at `.B.2` close

### Worth fixing during coding

- **HIGH-2** stamp_format_version constant introduction (HIGH severity but mechanically fixable when coding agent reaches Step 8)
- **HIGH-3** canonical sister section cleanup
- **MED-1** through **MED-5** + **LOW-3** mechanical edits

### Acceptable risk (don't block)

- **DOC-1 / DOC-2** DESIGN_SPECs drift — amend at `.B.2` ship close per pattern-codification-lifecycle

### Operator decision required

- **CRIT-6 (per audit synthesis Decision 4 + plan body line 47):** byte order option (a) auto-pick — operator confirmation needed for stamp_format_version bump = v5.14 fixture break. Plan body honestly surfaces this. **DEFAULT to (a) if operator doesn't override at triage.**

---

## Verdict: YELLOW

Plan body is well-structured (Check 29 + Check 30 sections present + per-sub-ship cycle discipline visible) but has 1 CRIT + 4 HIGH findings that require pre-coding amendment.

**GREEN path:** Plan body v1.0 → v1.1 amendment (~70-90 min focused) addressing CRIT-1 + HIGH-1 + HIGH-2 + HIGH-3 + HIGH-4 + MED items. Then plan body is GREEN.

**RED escalation:** If CRIT-1 reframe surfaces deeper scope (e.g., 3 .F.4d-closed fields need different placement than plan body envisioned, OR HIGH-1 framework extension turns out to be 100+ LOC instead of ~30), reconsider `.B.2` split into `.B.2.a` / `.B.2.b`.

**Default course:** Address findings in plan body v1.0 → v1.1 amendment; triage with Caramel; promote DRAFT → ACTIVE; create pre-tag rollback anchor + begin coding.

---

**End of /readiness report.** Saved to `plan_checks/readiness-2026-05-17-v5.15.5.F.4d.1.B.2.md`.
