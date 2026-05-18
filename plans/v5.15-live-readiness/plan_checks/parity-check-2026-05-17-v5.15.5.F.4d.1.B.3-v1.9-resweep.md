# /parity-check re-sweep — v5.15.5.F.4d.1.B.3 plan body v1.9

**Date:** 2026-05-17
**Scope:** Re-sweep of v1.9 FULL plan body for NEW parity hazards vs the
v1.2 audit; engine HEAD `9b62a72`; Version.hpp `5.15.5.F.4d.1.B.2`.
**Plan path:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md`
**Prior parity-check:** `plan_checks/parity-check-2026-05-17-v5.15.5.F.4d.1.B.3.md` (v1.2 audit, YELLOW; CRIT-1 + HIGH-1/2/3)

---

## Audit verdict: **YELLOW** — 1 NEW CRIT + 2 NEW HIGH + 1 NEW MED specific to v1.9 expanded scope

The v1.9 plan body has substantially expanded scope (9 → 15 deleted POST_CFG entries; NEW Step 0.5d FOREACH_GATE_CFG_FLAG framework walker; NEW Step 1.6.6.b 15-row STAMP-side rename; NEW Step 1.6.8 stamp_model.sh migration). Prior v1.2 audit's CRIT-1 is resolved via Decision F (F.2) SOFT compat. Prior HIGH-1 is resolved via Step 1.7 Layer 5b invocation. Prior HIGH-2 fixture is resolved via Step 1.6.7.5 self-contained hand-written approach. Prior HIGH-3 Decision E E.3 semantic shift is resolved via E.2 partial closure. **However, v1.9 expanded scope introduces 4 NEW parity hazards** centered on the stamp_model.sh migration + FOREACH_GATE_CFG_FLAG framework walker extension.

---

## Findings by severity (NEW vs v1.2 audit)

### CRIT

#### CRIT-1 NEW — `tools/stamp_model.sh` line 221 hardcodes `stamp_format_version=1` literal; Step 1.6.8 enumerates 6 wire-key migrations but does NOT include the version-string bump → bash CLI keeps emitting v1 forever post-`.B.3`

**File:line citations:**
- `tools/stamp_model.sh:221` — `CANONICAL="${CANONICAL}stamp_format_version=1\n"` (hardcoded literal)
- `ML_Headers/ModelInference.hpp:1745-1748` — engine emits `stamp_format_version=1\n` literal (Step 1.6.7.1-3 plan migrates this to STAMP_FORMAT_VERSION_CURRENT constant + bump to 2)
- Plan body v1.9 Step 1.6.8 (`:524-535`) — enumerates 7 wire-key migrations (lines 240/241/242/251/261/262/possible-243-244-freshness-tau-removal) but does NOT mention line 221 version literal

**Observed vs expected:**

Plan Step 1.6.7 bumps engine's STAMP_FORMAT_VERSION_CURRENT 1 → 2; Step 1.6.8 migrates 6 prefixed wire keys at lines 240-262 in stamp_model.sh. But the version literal `stamp_format_version=1` at line 221 is NOT in Step 1.6.8's enumeration. Result: bash CLI keeps writing `stamp_format_version=1` indefinitely, while engine emit + parser see v2-format bytes.

**Failure mode under Decision F (F.2) SOFT compat:**
- Bash-emitted stamps would parse on `.B.3+` engine (parser back-compat at Step 1.6.7.4 dual-recognizes v1 + v2 keys).
- BUT: bash-emitted stamps would have the UNPREFIXED wire keys (`bandit_blend_ratio=...` from Step 1.6.8 migration) WITH `stamp_format_version=1` literal — wire-format-inconsistent. Engine parser would see v1-versioned but v2-keyed stamps — semantically wrong even if loadable.
- Future deprecation tracking via TECH_DEBT-101 ("when production v1 stamps eliminated") becomes ambiguous: are bash-emitted-v2-keyed stamps with v1 literal "v1" or "v2"?

**Recommended fix:** Step 1.6.8 amendment to v1.10:
1. ADD migration of `tools/stamp_model.sh:221` literal `stamp_format_version=1` → `stamp_format_version=2`.
2. ADD migration of stamp_model.sh inline comments at line 214-218 ("Bumped on future stamp body schema changes" — explicit note about `.B.3` bump).
3. Verification: `grep "stamp_format_version" tools/stamp_model.sh` returns "stamp_format_version=2" not "=1" before Step 9 build-verify.

**Effort estimate:** 5 min mechanical addition to Step 1.6.8 enumeration; ~15 min plan body amendment.

**Cross-ref existing protection:** MED-1 from v1.2 parity-check flagged the cross-process byte-equivalence concern; v1.9 addresses the 6 prefixed wire keys but missed the version literal. PARITY_ISSUES.md has no matching entry (NEW class).

---

### HIGH

#### HIGH-1 NEW — `tools/stamp_model.sh:244` STILL emits `inference_cfg_freshness_tau=...` though engine deleted this at v5.14.9.D; Step 1.6.8 line 528 uses tentative "may need removal" language without committing to action

**File:line citations:**
- `tools/stamp_model.sh:239,244` — emits `FTAU_FMT` via `inference_cfg_freshness_tau=${FTAU_FMT}\n`
- `ML_Headers/StampBoundModelConstRegistry.hpp:290` — `/* v5.14.9.D — DELETED X(inference_cfg_freshness_tau, ...) entry */` (engine emit/parse path no longer recognizes this key)
- Plan Step 1.6.8 line 528: "freshness_tau already deleted at v5.14.9.D (script entry may need removal if no longer valid)" — TENTATIVE language

**Observed vs expected:**

Engine deleted `inference_cfg_freshness_tau` X-macro entry at v5.14.9.D (per inline comment); stamp_model.sh STILL emits this key. At HEAD `.B.2`, engine parser tolerates unknown keys (Surface G forward-compat) so this is INVISIBLE drift — bash-emitted stamps include a phantom wire key. At `.B.3`, under SOFT compat parser back-compat for 15 legacy prefixed keys, this 16th "freshness_tau" key is NOT in the closed set:

- If Step 1.6.7.4 implements parser back-compat as `FOREACH_LEGACY_PREFIXED_KEY` X-macro with the 15 keys enumerated — freshness_tau is NOT one of them.
- Parser SHOULD continue tolerating unknown keys (forward-compat); but the "closed set" semantic of TECH_DEBT-101 deprecation tracking becomes confused: when can we delete the back-compat layer? When `freshness_tau` is gone or when the 15 keys are gone?

**Recommended fix:** Step 1.6.8 amendment to commit to DELETION:
1. DELETE stamp_model.sh lines 234 (HELD_OUT_FRACTION + FRESHNESS_TAU OR-guard reference), 239 (FTAU_FMT awk), 244 (emit line).
2. Verify the bash CLI arg parser deletes `--freshness-tau` flag entirely (search lines ~100-130 for the argument handler).
3. Verify Layer 4 round-trip HMAC test catches if any production caller still passes `--freshness-tau` to stamp_model.sh.

**Effort estimate:** ~15 min mechanical deletion + verification; ~10 min plan body amendment.

**Cross-ref existing protection:** Engine parser tolerates unknown keys; failure mode is silent wire-format inconsistency (bash emits N+1 lines, engine emits N lines for same cfg state). Layer 4 round-trip HMAC test SHOULD catch divergence but Step 1.6.7.5 hand-written v1 fixture doesn't include freshness_tau wire key per plan body line 481-491. PARITY_ISSUES.md no matching entry.

---

#### HIGH-2 NEW — Step 0.5d FOREACH_GATE_CFG_FLAG framework walker extension proposes a 5-arg → 6-arg signature change for the sister registry but plan body does NOT include migration of the 5 existing consumer X-macros

**File:line citations:**
- `CoreFrameworks/GateCfgFlagRegistry.hpp:46-52` — current 5-arg signature: `X(NAME, legacy_field, display_label, section, doc)` × 6 rows
- `ML_Headers/MlCfgFlagRegistry.hpp:58-77` — sister registry's 6-arg signature (post-`.B.2` migration): `X(NAME, legacy_field, display_label, section, metadata_flags, doc)`
- Step 0.5d Sub-step 0.5d.a (plan body line 294): "Add parallel emit pass `X_STAMP_CFG_POPULATE_GATE_CFG_FLAG`...Mechanical." — does NOT mention the 5-arg → 6-arg signature change of FOREACH_GATE_CFG_FLAG itself
- Step 1.6.2 entry 12 (plan body line 331): "metadata_flags gains STAMP_BOUND_CFG_DERIVED" — implies the column exists, but at HEAD it does NOT (5-arg sig)
- 5 existing consumers at HEAD: `GUI/SettingsPanel.hpp:505`, `CoreFrameworks/ControllerConfig.hpp:2451`, `tests/controller_test.cpp:22543`, `CoreFrameworks/GateCfgFlagRegistry.hpp:46+59+72` (enum gen + mask gen)

**Observed vs expected:**

The Step 0.5d framework walker extension proposes walking FOREACH_GATE_CFG_FLAG with `metadata_flags`-bit conditional dispatch (per the sister X_STAMP_CFG_POPULATE_ML_CFG_FLAG at MemHeaders/CfgGateRegistry.hpp:297-303). This REQUIRES FOREACH_GATE_CFG_FLAG to have a metadata_flags column. At HEAD `.B.2`, it does NOT.

Migration impact (mirrors `.B.2` Step 0.5b FOREACH_ML_CFG_FLAG 5→6 sig migration per CHANGELOG.md row 28):
- FOREACH_GATE_CFG_FLAG body itself: add metadata_flags column to 6 rows.
- 5 consumer X-macros must accept 5→6 args: SettingsPanel.hpp render macro, ControllerConfig.hpp parse + persist macros, controller_test.cpp test macro, GateCfgFlagRegistry's own X_GEN_GATE_CFG_BIT + X_GEN_GATE_CFG_MASK.

**Coding-time discovery class:** the `.B.2` postmortem documents that the FOREACH_ML_CFG_FLAG 5→6 sig migration discovered an additional `_PARSE_OV_BITMAP_ROW_ml` consumer at coding time (per CHANGELOG row 28 "4 consumer X-macros updated including `_PARSE_OV_BITMAP_ROW_ml` discovered at coding time"). Plan Step 0.5d does NOT pre-enumerate the GATE consumer macro analog.

**Recommended fix:** Step 0.5d amendment to v1.10:
1. ADD explicit Sub-step 0.5d.0 (BEFORE 0.5d.a): "FOREACH_GATE_CFG_FLAG 5→6 sig migration — add `metadata_flags` column to 6 rows. Migrate 5+ consumer X-macros: SettingsPanel render, ControllerConfig parse + persist, test macros, _PARSE_OV_BITMAP_ROW_gate if it exists (per `.B.2` postmortem; check at pre-coding tag time)."
2. ADD Step 0.5d.0 effort: ~1-1.5h (mirrors `.B.2` Step 0.5b ~1h actual + discovery).
3. Total Step 0.5d effort revision: 3-4h → 4-5h focused.
4. Per `feedback_audit_canonical_sister_before_new_infra` — the sister FOREACH_ML_CFG_FLAG migration at `.B.2` is the canonical reference; Step 0.5d should explicitly cite the sister precedent and adopt the same sub-step structure.

**Effort estimate:** ~30 min plan body amendment to enumerate; ~1h additional coding effort.

**Cross-ref existing protection:** None at HEAD. CHANGELOG row 28 documents the 5→6 sig pattern with consumer-enumeration discovery class but the plan body does not apply lesson learned. PARITY_ISSUES.md no matching entry.

---

### MED

#### MED-1 NEW — Step 1.6.6.b 15-row STAMP-side field-access rename in CfgDriftCheckRegistry.hpp (lines 236-311) lands the STAMP-side reads (`h->inference_cfg_<name>` → `h->name`) but plan does NOT enumerate the corresponding ModelHandle field-name migration in CoreModelZoo.hpp

**File:line citations:**
- Plan Step 1.6.6.b (`:438-455`) — enumerates 15 STAMP-side renames in CfgDriftCheckRegistry.hpp
- `ML_Headers/CoreModelZoo.hpp:400-419` — ModelHandle population from `sr.inference_cfg_<name>` to `handle->inference_cfg_<name>` (5 v1.6 model-state sites flagged in Step 1.6.2 lines 358-361)
- Plan Step 1.6.2 production sites enumeration (`:343-345, 359-361`) — addresses CoreModelZoo.hpp lines 411-412 (bandit_blend_ratio) + lines 400-405 (3 sites) + 416-419 (2 sites)

**Observed vs expected:**

Step 1.6.6.b describes the CfgDriftCheckRegistry STAMP-side rename. The STAMP side reads `h->inference_cfg_<name>` — where `h` is `const ModelHandle*` (verified at CfgDriftCheckRegistry.hpp:236 `h->inference_cfg_confidence_threshold_scale`). For the rename to compile, ModelHandle MUST have unprefixed `<name>` fields.

At HEAD `.B.2`, ModelHandle has PREFIXED `inference_cfg_<name>` fields (mirrored by AUTO-GEN in StampInferenceCfgInputs via the prefixed POST_CFG entries). After Step 1.6.2 bit-add + Step 1.6.3 Approach A unconditional struct-gen, ModelHandle should have unprefixed `<name>` fields ALSO. Plan Step 1.6.2 enumerates CoreModelZoo handle-write sites (`handle->inference_cfg_<name> = sr.inference_cfg_<name>` → `handle->name = sr.name`) but does NOT enumerate the read-side migration that Step 1.6.6.b assumes.

The plan body's Step 1.6.2 consumer scope grep ("149 total references across 8 files") presumably covers this via `tests/controller_test.cpp 80 sites` + `CfgDriftCheckRegistry.hpp 17 sites` + `CoreModelZoo.hpp 14 sites` — but the dependency chain (Step 1.6.2 → 1.6.6.b: write site renames must land BEFORE read site rename or build breaks) is not made explicit in sequencing.

**Recommended fix:** Step 1.6.6.b clarification in v1.10:
1. ADD dependency note: "Step 1.6.6.b CfgDriftCheckRegistry STAMP-side rename DEPENDS on Step 1.6.3 Approach A unconditional struct-gen landing (which creates unprefixed `inf.<name>` fields on ModelHandle via the StampBoundCfgRegistry struct-gen sister)".
2. VERIFY: ModelHandle struct-gen reads from master registry walker too (not separate struct-gen). At HEAD, ModelHandle is auto-generated from FOREACH_STAMP_BOUND_MODEL_CONST union (PRE_CFG + POST_CFG) — Step 1.6.3 changes only StampInferenceCfgInputs + ModelStampResult, NOT ModelHandle.
3. If ModelHandle is NOT auto-regenerated from master cfg registry, then Step 1.6.6.b lines `h->confidence_threshold_scale` reads will FAIL TO COMPILE — ModelHandle would still have prefixed fields.

**Effort estimate:** ~30 min verification + plan body amendment to make dependency explicit.

**Cross-ref existing protection:** Build-time verification per Step 1.6 sequencing claim ("BUILD-FORCED" per line 626). Per `feedback_enumerate_consumers_before_registry_row_deletion`, full ModelHandle field-name enumeration should be in scope (it likely is given the 149-site grep, but the dependency between write-site + read-site renames + ModelHandle struct field auto-gen path is not enumerated).

---

### LOW

#### LOW-1 NEW — Step 1.6.7.5 hand-written v1 fixture canonical body string literal at plan body lines 477-491 OMITS the 10 thompson/bandit/per_horizon prefixed wire keys that ARE in the deletion scope (only 9 are listed)

**File:line citations:**
- Plan Step 1.6.7.5 fixture body literal (`:481-491`) — enumerates 9 v1 prefixed cohort wire keys
- Plan Decision D 15-entry scope (`:80-94`) — lists 15 prefixed POST_CFG entries to delete

**Observed vs expected:**

The hand-written v1 fixture canonical body in Step 1.6.7.5 lists 9 prefixed keys (bandit_algorithm, thompson_mu_prior, thompson_precision_prior, thompson_precision_obs, thompson_exp3_blend_alpha, ml_tp_pct, ml_sl_pct, barrier_blend_mode, per_horizon_barrier_blend) but Decision D's expanded 15-entry scope ALSO includes confidence_threshold_scale, barrier_gate_enabled, confidence_hard_block_threshold, fee_rate_maker, fee_rate_taker (5 additional from v1.6 expansion) + standalone bandit_blend_ratio. The v1 fixture should also cover these to make the round-trip Layer 4 test exhaustive.

**Recommended fix:** Step 1.6.7.5 fixture body amendment:
1. ADD 6 more legacy prefixed wire-key lines to the v1 fixture string literal (5 v1.6 expansion + 1 standalone).
2. ADD per-field verification assertions for these (mirrors existing patterns at line 506-507).

**Effort estimate:** ~10 min mechanical addition.

**Cross-ref existing protection:** Step 1.6.7.4 parser back-compat layer covers all 15 keys (per plan body line 333 "parser back-compat enumerates ALL 15 legacy keys"); fixture should match the closed set exactly to exercise the back-compat code path fully. Without exhaustive coverage, the test passes silently if back-compat dispatch misses the 5 new keys.

---

### DOCUMENT-ONLY

#### DOC-1 — v1.9 amendments to skill specs (`/parity-check`, `/precoding-audit-gate`, `/trace-deps`, `audit-driven-pre-coding-gate.md` DESIGN_SPEC) constitute ~1.5h batched workspace amendment at ship close per plan body line 599-602; well-scoped + no parity risk

(Documentation-only; not blocking.)

---

## Cross-cutting concerns

### CC-1 NEW — stamp_model.sh migration scope expanded by 2 items (CRIT-1 + HIGH-1) not covered by plan v1.9 Step 1.6.8

CRIT-1 (version literal bump) + HIGH-1 (freshness_tau deletion) belong in Step 1.6.8 scope per the script's role as wire-format producer. Adding these 2 items to Step 1.6.8 keeps the bash CLI byte-equivalence contract intact under v2 transition.

### CC-2 NEW — FOREACH_GATE_CFG_FLAG 5→6 sig migration is a sister to `.B.2` FOREACH_ML_CFG_FLAG 5→6 sig migration; plan should cite + adopt same Step 0 structure (HIGH-2)

Per `feedback_audit_canonical_sister_before_new_infra` — every plan introducing new framework infrastructure must cite the canonical sister + adopt its discipline. Plan v1.9 cites the sister informally ("Sister to `X_STAMP_CFG_POPULATE_ML_CFG_FLAG`") but does not adopt the sister's 5→6 sig migration sub-step structure.

---

## Behavior matrix (verify train ↔ serve agree under v1.9 SOFT compat under proposed amendments)

| Scenario | bash CLI emit | Engine v2 emit | Engine parser | Identical bytes? |
|---|---|---|---|---|
| v1 legacy stamp with 15 prefixed keys | bash emits prefixed; STAMP literal `=1` | (N/A, legacy) | Parser back-compat dispatch (Step 1.6.7.4) → cohort fields populated | YES (loads cleanly per Decision F (F.2)) |
| **v2 stamp via bash CLI under v1.9 AS WRITTEN** | bash emits 6 UNPREFIXED keys + STAMP literal `=1` (CRIT-1 unaddressed) + freshness_tau line (HIGH-1 unaddressed) | Engine emits 15 unprefixed keys + STAMP `=2` literal + NO freshness_tau line | Parser dispatches both → cohort fields populated | **NO — bash output has wrong version literal + phantom freshness_tau key** |
| v2 stamp via bash CLI under v1.10 (CRIT-1 + HIGH-1 fixed) | bash emits 6 UNPREFIXED + STAMP `=2` + NO freshness_tau | Same | Parser dispatches → cohort fields populated | YES |
| v2 stamp via engine `Stamp_AssembleAndEmit` | (N/A, bash-side) | Engine emits 15 unprefixed + STAMP `=2` | Parser dispatches → cohort fields populated | YES |

---

## Suggested ship sequence — amendment to v1.9 plan body

1. Plan body amendment v1.9 → v1.10 to address CRIT-1 (Step 1.6.8 + version literal), HIGH-1 (Step 1.6.8 + freshness_tau deletion), HIGH-2 (Step 0.5d + GATE_CFG_FLAG sig migration), MED-1 (Step 1.6.6.b dependency explicit), LOW-1 (Step 1.6.7.5 fixture exhaustive coverage).
2. Operator triage on the 5 v1.10 amendments before pre-coding tag.
3. Re-run `/readiness` Check 34 (consumer enumeration verification) post-amendment.
4. Pre-coding tag → coding starts.

**Estimated amendment effort:** ~1.5-2h plan body amendment + verification (per `feedback_plan_right_not_fast` — invest in correctness before coding).

---

## NOT a bug (verified-safe items)

- **Decision F (F.2) SOFT compat** — resolves prior v1.2 CRIT-1 cleanly. Parser dual-recognition for closed set of 15 keys; emit v2-only; no operator action. ALIGNED with `wire-format-byte-preservation-discipline.md` Layer 6 Surface G discipline.
- **Step 1.7 Layer 5b invariant invocation** — verified `tests/wire_format_invariants.hpp` exists at HEAD (171 lines) + supports dual-mask context (verified at line 78 `pop_count += __builtin_popcountll(ctx.per_core_mask_words[w])`). Plan reads correctly; resolves prior HIGH-1.
- **Step 1.6.7.5 self-contained hand-written fixture** — eliminates HIGH-2 filesystem dependency. Compile-time string literal approach is structurally cleaner than binary-file fixture.
- **Decision E (E.2) partial closure** — resolves prior HIGH-3 by preserving documented semantic-divergence at bandit boundary (per `categorical-tag-applicability-pattern.md` orthogonality).
- **149-site consumer enumeration (`feedback_enumerate_consumers_before_registry_row_deletion`)** — comprehensive grep covers production + test sites for 15 deletion-scope fields; per-file counts captured.
- **Step 1.6.7 sub-step reordering** — DESIGN_SPECS amendment lands at Step 0 BEFORE coding sub-steps apply.

---

## Inflection assessment

Per Caramel's `feedback_iteration_spiral_signals_audit_meta_gap`: v1.9 plan body is the 9th amendment. The findings here are NOT material spiral — they are surface-specific to the v1.9 scope expansion (stamp_model.sh + FOREACH_GATE_CFG_FLAG):

- **CRIT-1** is a 1-line addition to Step 1.6.8 enumeration (`stamp_format_version=1` → `=2`).
- **HIGH-1** is a 3-line script deletion (`--freshness-tau` flag + emit line).
- **HIGH-2** is documentation of the sister-migration discipline already-applied at `.B.2` to FOREACH_ML_CFG_FLAG.
- **MED-1** is a sequencing-dependency annotation.
- **LOW-1** is 6 lines added to a hand-written fixture string literal.

**These are NEW surfaces (stamp_model.sh + FOREACH_GATE_CFG_FLAG) introduced by v1.9 expanded scope, not prior-iteration leakage.** The pattern is consistent with `feedback_enumerate_consumers_before_registry_row_deletion`: comprehensive enumeration at v1.8 caught 149 in-engine sites, but the bash CLI + sister framework registry were outside that enumeration's scope. **Recommend the v1.10 amendment scope as enumerated, then take the inflection point.**

---

## Cross-references to existing PARITY_ISSUES.md ledger

No new PARITY-NNN entries needed at this audit pass — all findings are either:
- (a) plan body amendment items (Step 1.6.8 + 0.5d scope), tracked by audit report alone until coding lands, OR
- (b) covered by existing PARITY-013 / PARITY-024 closure precedents (bandit stamping + per-horizon barrier serving)

PARITY-026 (`FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG` cfg-derived-vs-model-const-distinction not enforced; v5.15.5.F.4d close at hand) — referenced by Decision D mechanism 1 closure; verify at `.B.3` ship close that PARITY-026 lifecycle status updates to CLOSED.

---

## Files-changed verification log

For each finding, cited file at HEAD `9b62a72` (Version.hpp `5.15.5.F.4d.1.B.2`):

- `tools/stamp_model.sh` — 382 lines (CRIT-1, HIGH-1)
- `CoreFrameworks/GateCfgFlagRegistry.hpp` — 93 lines, 6 rows in FOREACH_GATE_CFG_FLAG with 5-arg sig (HIGH-2)
- `ML_Headers/CfgDriftCheckRegistry.hpp` — 326 lines, 15 STAMP-side `h->inference_cfg_<name>` reads verified at lines 236, 240, 245, 249, 255, 259, 263, 267, 271, 275, 279, 299, 303, 307, 311 (MED-1)
- `ML_Headers/StampBoundModelConstRegistry.hpp:281-302` — 6 prefixed POST_CFG entries in inference_cfg group covering 5 v1.6-expansion fields (LOW-1)
- `ML_Headers/ModelInference.hpp:1192-1199, 1640-1643, 1782-1788` — 3 struct-gen + production emit sites confirmed (no NEW findings)
- `MemHeaders/CfgGateRegistry.hpp:258-308, 311-362` — framework walker + drift_check_from_derived template fns confirmed; H20 branchless dispatch preserved (no NEW findings)
- `tests/wire_format_invariants.hpp:78-89` — dual-mask popcount support confirmed (resolves prior HIGH-1)

---

## End of report

**5 NEW findings:** 1 CRIT (stamp_format_version literal); 2 HIGH (freshness_tau orphan + GATE_CFG_FLAG sig migration unenumerated); 1 MED (Step 1.6.6.b read-site dependency); 1 LOW (fixture exhaustive coverage). Recommend v1.10 plan body amendment before pre-coding tag. **Inflection point reached** — these findings are scoped to NEW v1.9 surfaces (stamp_model.sh + FOREACH_GATE_CFG_FLAG), not prior-iteration spiral.
