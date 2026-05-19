# /accounting-audit findings — 2026-05-17 — v5.15.5.F.4d.1.B.3 plan body v1.2 DRAFT

**Plan body:** `/home/caramel/code/tick-trader-percore-workspace/plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` v1.2 DRAFT
**Engine HEAD:** `9b62a72` (v5.15.5.F.4d.1.B.2 ship close)
**Ship:** `v5.15.5.F.4d.1.B.3` (Legacy empty-out)
**Scope shape:** current — focused on this plan body's surface (cfg→stamp wire-format emit, drift, populate; 5 prefixed POST_CFG deletes; stamp_format_version=1→2 bump; CfgDriftCheck consolidation Decision E)
**Auditor stance:** /accounting-audit. Accounting paths NOT directly touched by this ship; instead the audit walks the wire-format byte-preservation surface for collateral parity hazards + Class 27 sweep + locale-pin + FPN↔double asymmetry consequences. /parity-check sister has the primary jurisdiction over the HMAC chain question — this report focuses on the accounting-eligible failure surfaces only.

## Summary

- **CRITICAL: 1** (wire-format-changing scope without HMAC chain re-baseline procedure)
- **HIGH:     3** (Step 1.6.7 stamp_format_version procedure has gaps; Decision E semantic-shift money-path implication; Step 5 LENIENT mode unspecified scope)
- **MEDIUM:   4** (POST_CFG delete completeness; framework `cfg_emit_field` FPN→double asymmetry locale-pin re-entry; v1 stamps' accounting-relevant inference_cfg surface; CI Check 9 coverage gap)
- **LOW:      2** (DESIGN_SPEC amendment concreteness; FEATURE_LOOKUP entry precision)
- **DOC:      1** (PARITY_ISSUES.md auto-write for the v1→v2 stamp policy decision)

Money-path verdict: **NO direct accounting-path changes at `.B.3`.** Step 1.6.4 is stamp emit path (cfg→canonical body bytes; HMAC-input only); no fee_rate / commission / PnL / balance / kill-switch / drawdown surfaces touched. **H4 (FPN<F> accounting invariant) UNAFFECTED.** **Class 27 sweep: CLEAN — framework walker reads cfg.<name> at slow-path/load-time only; no scalar-mirror caches added; the 5 prefixed POST_CFG fields' consumers (drift check, stamp emit) already read FPN<F> cfg at decision-time via `tt::cfg_drift_compare<StampT,CfgT>` + `tt::cfg_emit_field<T>`.** The findings below are entirely about *adjacent* wire-format-byte-preservation hazards that the accounting-audit lens catches because the cfg-drift surface (which IS gated on `STAMP_HAS(*h, inference_cfg)` and feeds `FAILURE_MASK_cfg_binding_drift` — money-path-relevant since cost gates + fee_rate drift rows participate in the same drift-flags bitmap consumed by `MLStatusPanel.hpp:469,552`) is one structural-layer away from the wire-format change scope.

---

## Findings

### [CRITICAL-1] Step 1.6.7 stamp_format_version=2 bump is FIRST canonical use AND DESIGN_SPEC amendment LANDS AT THE SAME SHIP — discipline circularity risk (`subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md:226-232` + `tick-trader-percore-workspace/DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md:194-274`)

- **Severity:** CRITICAL
- **Category:** § 1 Wire-format byte preservation under version bump (DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md Layer 5b methodology — structural invariant tests at consumer site)
- **Class:** Wire-format chain re-baseline; H9 invariant (per CLAUDE.md "wire-format byte preservation for HMAC-signed bodies")
- **Details:** plan-body Step 1.6.7 sequences 5 sub-steps (`.0` extract literal → `.1` add MAX_SUPPORTED bounds check → `.2` bump constant → `.3` v1 fixture failure-mode test → `.4` DESIGN_SPEC amendment). Two structural gaps:
  1. **The DESIGN_SPEC procedure being amended at sub-step `.4` is the procedure being EXECUTED for the first time at sub-steps `.0`-`.3`.** The plan body cites `wire-format-byte-preservation-discipline.md` Layer 5b methodology as the methodology, but Layer 5b is the structural-invariant TEST mechanism for derived filters (added 2026-05-14 / revised 2026-05-16 per Option F at lines 194-274), NOT a procedure for stamp_format_version bumps. The procedure being codified IS new at `.B.3`; the plan should not present the amendment as if the procedure already exists elsewhere.
  2. **No re-baseline of Layer 4 (round-trip HMAC test) for v2 stamps.** Per Layer 4 (`wire-format-byte-preservation-discipline.md:140-177`), the canonical round-trip test takes a v(N-1) committed fixture, parses via new code, re-emits via new code, checks bytes + HMAC byte-identical. Step 5 of plan ONLY tests v1 stamps' load failure-mode under STRICT (or LENIENT warn+skip); there is NO test that takes a NEW v2 stamp + re-emits + verifies HMAC byte-identical post-`.B.3`. Without this, the v2 wire-format chain is untested for self-consistency.
- **Recommended fix:**
  - **At Step 1.6.7.3:** ADD a v2 fixture round-trip test alongside the v1 failure-mode test. Synthesize a populated `StampInferenceCfgInputs` with all cohort + 5 prefixed-only fields → emit via framework `populate_stamp_cfg_from_derived<F>` + `cfg_emit_field<T>` → re-parse → verify bytes + HMAC byte-identical. Commit fixture `tests/fixtures/v5_15_5_F_4d_1_B_3_stamp_canonical.bin`.
  - **At Step 1.6.7.4 (DESIGN_SPEC amendment):** make the procedure CONCRETE by inlining the 5-sub-step recipe + worked example showing: (a) which DESIGN_SPEC layer is amended (Layer 4 fixture re-baseline pattern; Layer 5b stays semantic-invariant), (b) what artifacts SHIP with the bump (constant + bounds check + fixture file + failure-mode test + round-trip test + CHANGELOG entry), (c) what a future bump (v2→v3) inherits mechanically.
  - **At Verification gate:** add line "v2 canonical body round-trip HMAC byte-identical via fixture" as a ship-blocker check.
- **DESIGN_SPEC reference:** `wire-format-byte-preservation-discipline.md` Layer 4 (round-trip HMAC test on real legacy stamp) + Layer 6 (Surface G back-compat). The amendment at sub-step 1.6.7.4 should EXTEND Layer 4 with the version-bump procedure (not introduce a parallel structure).
- **CI check:** ship-blocker round-trip test belongs in `controller_test.cpp` per Layer 5b convention.

---

### [HIGH-1] Step 5 v5.14 stamp fixture regression — STRICT vs LENIENT decision unspecified for accounting-relevant inference_cfg drift surface (`subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md:251-254` + `ML_Headers/CfgDriftCheckRegistry.hpp:274-281`)

- **Severity:** HIGH
- **Category:** § 3 Slippage / fee / cost gate consistency across paths under wire-format version skew
- **Class:** Cross-binary parity hazard (drift detection surface touches `fee_rate_maker` / `fee_rate_taker` rows at `CfgDriftCheckRegistry.hpp:274-281` gated by `STAMP_HAS(*h, fees) && BITMAP_IS_SET(cfg.gate_cfg_flags, MASK_GATE_CFG_COST_GATE_ENABLED)` → flags `FAILURE_MASK_cfg_binding_drift`)
- **Details:** plan-body Step 5 surfaces STRICT vs LENIENT as a Decision at audit triage, but does NOT specify behavior for the accounting-relevant subset of drift rows. If LENIENT mode is picked:
  - Drift check runs against a v1 stamp's recorded `inference_cfg_*` fields. The 5 prefixed-only fields (`inference_cfg_ml_tp_pct` / `inference_cfg_ml_sl_pct` / `inference_cfg_barrier_blend_mode` / `inference_cfg_per_horizon_barrier_blend` / `inference_cfg_bandit_blend_ratio` + 4 thompson) are recorded in v1 stamps via POST_CFG entries.
  - After `.B.3` Decision D mechanism 1 delete: framework emits unprefixed `ml_tp_pct=X` etc. v1 stamp parser had `inference_cfg_ml_tp_pct=` keys → recorded as `r.inference_cfg_ml_tp_pct`. v2 stamps don't carry the prefixed keys → drift compares with `0.0` recorded value AND non-zero `cfg.ml_tp_pct` → drift fires erroneously.
  - **Specifically for `fee_rate_maker` / `fee_rate_taker`:** unaffected by this ship (rows NOT in Decision D delete scope; remain in POST_CFG via different sister registry `FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG` `inference_cfg_fee_rate_*` rows added separately at v5.14.8.D NEW fields; verify). But the SAME drift-flags bitmap (`FAILURE_MASK_cfg_binding_drift`) handles both groups → a false-positive fire from one row causes the bitmap to set; operator-facing failure attribution at `MLStatusPanel.hpp:552` shows `cfg_binding_drift` without indicating which sub-class.
- **Recommended fix:**
  - **At plan body Step 5:** specify STRICT (auto-pick per `feedback_evaluate_options_on_robustness_latency_design_not_time` — structurally cleanest; trains operator to regenerate). Articulate the LENIENT alternative ONLY as fallback for production operator who has live v1 stamps in production they can't regenerate cheaply (not the case for Caramel's solo paper-test cycle).
  - **At Step 5 STRICT mode test:** verify operator-visible error message references `stamp_format_version=1 < MAX_SUPPORTED=2` + actionable: "Regenerate stamp via `tools/stamp_model.sh <path>` after v5.15.5.F.4d.1.B.3 upgrade." NOT just "drift detected".
  - **Document at PARITY_ISSUES.md:** "v1 stamps (pre-`.B.3`) incompatible with `.B.3+` STRICT engine; LENIENT mode supports load with WARN + skip cfg drift check entirely for that load; cost-gate fee_rate drift rows skipped under LENIENT carry forensic-only WARN_ALWAYS severity already (lines 274-281 of CfgDriftCheckRegistry.hpp) — no accounting impact."
- **DESIGN_SPEC reference:** `wire-format-byte-preservation-discipline.md` Layer 6 (Surface G); `version-bump-procedure-for-wire-format-changes.md` (new at this ship per CRITICAL-1).
- **Auto-write:** PARITY_ISSUES.md entry needed.

---

### [HIGH-2] Decision E (E.3) full migration shifts drift-detection gate semantic at bandit boundary — accounting-relevant for cost-gate fee_rate drift coupling (`subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md:104-112` + `ML_Headers/CfgDriftCheckRegistry.hpp:248-273`)

- **Severity:** HIGH
- **Category:** § 7 Backtest ↔ live accounting parity under cfg gate semantic change
- **Class:** drift-check semantic shift; cross-mode parity hazard
- **Details:** plan body surfaces Decision E options (E.1 leave separate / E.2 partial migration / E.3 full migration with semantic shift at bandit boundary). The recommendation is (E.2). **(E.3) impact on accounting paths is real:**
  - At HEAD (`CfgDriftCheckRegistry.hpp:248,256,260,264,268`): bandit-related drift rows use `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)` semantic.
  - After (E.3) migration to framework via `COHORT_GATE_BANDIT_THOMPSON` at `MlCfgFlagRegistry.hpp:115`: semantic becomes `(cfg.bandit_algorithm != 0)`.
  - **Edge case:** an operator who has `bandit_algorithm=2` (a Thompson variant) but `ml_cfg_flags.bandit_enabled=0` (Boolean feature switch OFF) will see DIFFERENT drift behavior:
    - At HEAD: drift skipped (feature flag OFF; legacy-correct — don't compare bandit cfg when feature disabled)
    - Post-(E.3): drift fires (bandit_algorithm != 0 → check) → false-positive drift → operator-visible `cfg_binding_drift` flag → engine refuses load (STRICT) or warns (LENIENT)
  - **Although bandit_blend_ratio is the only accounting-money-path-adjacent field in this set** (the rest are Thompson posterior + state-4 alpha; not direct accounting impact), the bitmap flag `cfg_binding_drift` is the SAME bitmap that catches `fee_rate_maker` / `fee_rate_taker` drift at `CfgDriftCheckRegistry.hpp:274-281`. A false-positive from the bandit edge case taints the cost-gate failure-mode bitmap and hides genuine fee-rate drift in the noise.
  - **Same concern for trading_mode (line 178 of legacy registry):** is in `FOREACH_STAMP_BOUND_CFG` always-emit (`emit_when=1`). Migration of CfgDriftCheck via (E.3) would couple to the same gate semantic question.
- **Recommended fix:** (E.2) per plan body recommendation IS the correct proportionate response per `feedback_proportionate_response_to_audit_findings`; document the semantic-distinction-preservation at bandit boundary in postmortem + add EXPLICIT comment in `MlCfgFlagRegistry.hpp:115` after `COHORT_GATE_BANDIT_THOMPSON` definition: "INTENTIONALLY differs from `MASK_ML_CFG_BANDIT_ENABLED` semantic in `CfgDriftCheckRegistry.hpp` at bandit drift rows — see `.B.3` postmortem Decision E rationale."
- **If operator picks (E.3):** add to Step 2.5 the per-row drift behavior matrix BEFORE migration + a regression test at controller_test.cpp covering the `bandit_algorithm=2 + bandit_enabled=0` edge case explicitly.
- **DESIGN_SPEC reference:** `cfg-scope-discipline.md` (override-inherit pattern landed at this ship + Decision 9 v1.2 reframe at `.B.2` postmortem).

---

### [HIGH-3] `cfg_emit_field<T>` re-entrancy under nested locale-pin invocations + FPN→double asymmetry produces TWO snprintf paths in framework canonical body emit walker (`CoreFrameworks/CfgFieldDispatch.hpp:321-362` + `MemHeaders/CfgGateRegistry.hpp:259-308`)

- **Severity:** HIGH
- **Category:** § 5 Lossy FPN_ToDouble + locale-pin Layer 2 discipline (wire-format-byte-preservation-discipline.md)
- **Class:** locale-pin re-entrancy; FPN→double conversion asymmetry under wire-emit
- **Details:** Production canonical body emit currently runs at `ModelInference.hpp:1697-1809`:
  - Outer locale pin via `uselocale(newlocale(LC_NUMERIC_MASK, "C", 0))` at line 1697
  - Inner X-macro walks for FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG (lines 1772), FOREACH_STAMP_BOUND_CFG (line 1788), FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG (line 1802)
  - Restore at line 1806

  Post-`.B.3` Step 1.6.4: FOREACH_STAMP_BOUND_CFG line 1782-1789 block REPLACED by `cfg_derived::populate_stamp_cfg_from_derived<F>(canonical + n, cap - n, *cfg_ptr)` call.

  - **`cfg_emit_field<T>` (CfgFieldDispatch.hpp:332-334) itself re-pins the locale per invocation** — this is technically per-thread + safe per `uselocale` semantics, but it adds N redundant `newlocale/freelocale` syscall pairs (one per cohort field). Layer 2 of `wire-format-byte-preservation-discipline.md:90-100` documents the outer-pin idiom; the framework walker DUPLICATES the pin inside `cfg_emit_field` → wasteful + a structural drift if outer pin shape ever changes.
  - **FPN→double asymmetry:** `cfg_emit_field<T>` at `CfgFieldDispatch.hpp:337-339` uses `FPN_ToDouble(src)` for FPN<F> → emits as `%.17g`. Legacy `FOREACH_STAMP_BOUND_CFG` at `StampBoundCfgRegistry.hpp:112-117` calls `FPN_ToDouble(cfg.ridge_lambda)` etc. with `%.17g` and same format string — bytewise identical → SAFE. Verify the .B.2 cohort migration tests' byte-identity assertion holds for this swap. Plan body Step 1.6.4 should call out the bytewise verification explicitly.
- **Recommended fix:**
  - **Code path (Step 1.6.4 implementation):** option (a) — accept the N inner locale-pin syscalls (slow-path/stamp-emit cadence; one stamp emit per training-run finish; the syscalls are negligible). Document the redundancy at `cfg_emit_field<T>` as intentional belt-and-suspenders.
  - Option (b) — add `cfg_emit_field_nopin<T>` variant that skips inner pin, used ONLY by `populate_stamp_cfg_from_derived` (which guarantees outer pin). Add static_assert documentation. ~30 LOC.
  - **At Step 1.6.4 verification gate addition:** explicit "Layer 2 outer locale-pin still wraps framework walker call site" check via grep audit `uselocale.*populate_stamp_cfg_from_derived` co-located in stamp_write_for_model.
  - **At Step 1.6.4 implementation:** byte-identity assertion already in plan as "wire-format byte preservation at this swap" — make it CONCRETE: synthesize cfg with all cohort fields populated → emit via legacy walker → emit via framework walker → memcmp == 0. Same `cfg.bandit_algorithm=2, thompson_mu_prior=0.5, ml_buy_threshold=0.55` etc. populated fixture.
- **DESIGN_SPEC reference:** `wire-format-byte-preservation-discipline.md` Layer 2 + Layer 4 (round-trip).
- **Note:** Same observation applies to `cfg_save_field<T>` at CfgFieldDispatch.hpp:179-182 — already has inner pin. The pattern is established. The (a) option is preferred for consistency.

---

### [MED-1] POST_CFG delete completeness — 4 Thompson `inference_cfg_thompson_*` rows AT POST_CFG vs at master cfg registry, with the 4 master-cfg rows already cohort-migrated at `.B.2` (`ML_Headers/StampBoundModelConstRegistry.hpp:469-483` + `CoreFrameworks/CfgFieldRegistry.hpp` — `cfg.thompson_mu_prior` etc.)

- **Severity:** MEDIUM
- **Category:** § 1 + § 3 Wire-format double-emit hazard if both prefixed POST_CFG + framework unprefixed both emit
- **Class:** Class 18 mirror (legacy POST_CFG mirror parallel to framework unprefixed emit)
- **Details:** Plan body Step 1.6.2 says: "5 prefixed POST_CFG entries deleted; framework walker emits unprefixed". Decision D mechanism 1 surfaces 5 prefixed-only fields (ml_tp_pct + ml_sl_pct + barrier_blend_mode + per_horizon_barrier_blend + bandit_blend_ratio). **But `StampBoundModelConstRegistry.hpp:469-483` has 4 ADDITIONAL `inference_cfg_*` rows for the bandit/thompson cohort (`inference_cfg_bandit_algorithm`, `inference_cfg_thompson_mu_prior`, `inference_cfg_thompson_precision_prior`, `inference_cfg_thompson_precision_obs`, `inference_cfg_thompson_exp3_blend_alpha`).** The plan body addresses this at sub-step 1.6.2:
  > "DELETE 5 prefixed POST_CFG entries at StampBoundModelConstRegistry.hpp:454-465 + bandit/thompson 4 at :469-483 if also unifiable (Decision D scope clarification: 4 thompson rows already cohort-migrated at .B.2; need to verify whether their POST_CFG mirror entries need deletion at .B.3 to avoid double-emit)"
  
  **The "need to verify" is unresolved at plan-body time + load-bearing for HMAC chain.** Status of those 4 bandit/thompson POST_CFG entries at `.B.3` ship time MUST be:
  1. DELETED (framework cohort emit at .B.2 already produces unprefixed `bandit_algorithm=X` / `thompson_mu_prior=X` etc.; POST_CFG `inference_cfg_<name>` prefixed sister is double-emit → HMAC chain break).
  2. OR documented exemption (e.g., different drift severity / different semantic — but inspection of registries suggests same semantic).
  
  At HEAD per `ML_Headers/StampBoundCfgRegistry.hpp:163-173` cohort already emits unprefixed `bandit_algorithm=X` etc. via legacy. Plus `StampBoundModelConstRegistry.hpp:469-483` emits `inference_cfg_bandit_algorithm=X` etc. via POST_CFG. **AT HEAD this means BOTH keys emit for the same cfg value** — duplicate wire key. Operator inspection of any current .B.2 model stamp file should show `bandit_algorithm=...\n` AND `inference_cfg_bandit_algorithm=...\n` co-existing. This is itself a pre-existing parity surface that `.B.3` Step 1.6.2 inherits.
- **Recommended fix:**
  - **At Step 1.6.2:** PROMOTE the "if also unifiable" clause to a HARD requirement. List all 9 POST_CFG entries to delete: 5 (ml_tp_pct, ml_sl_pct, barrier_blend_mode, per_horizon_barrier_blend, bandit_blend_ratio) + 5 (bandit_algorithm + thompson_mu_prior + thompson_precision_prior + thompson_precision_obs + thompson_exp3_blend_alpha). Total 10 (not 5; not 9).
  - **At Step 1.6.7.3 fixture test:** v1 stamps from `.B.2` engine ALREADY have BOTH prefixed `inference_cfg_<name>` AND unprefixed `<name>` keys for the bandit/thompson cohort. Per Layer 6 Surface G: parser tolerates BOTH — does HMAC verify the same byte body? CRITICAL question — if `.B.2` stamps already double-emit, the legacy walker order is `PRE_CFG → FOREACH_STAMP_BOUND_CFG (with unprefixed bandit_algorithm) → POST_CFG (with inference_cfg_bandit_algorithm)` → unique HMAC. `.B.3` walker order is `PRE_CFG → framework (unprefixed bandit_algorithm in master-registry order) → POST_CFG (with bandit_algorithm prefixed POST_CFG entries DELETED)`. **Byte order changes; HMAC for the same cfg state DIFFERS.** This is intentional (the version bump signals it). But the verification artifact at Step 1.6.7.3 must explicitly cover this scenario.
  - **At PARITY_ISSUES.md:** auto-write entry describing pre-`.B.3` double-emit + `.B.3` collapse to single unprefixed emit + version bump signaling.
- **DESIGN_SPEC reference:** `wire-format-byte-preservation-discipline.md` Layer 4 + Layer 5 (snapshot test).

---

### [MED-2] CI Check 9 (STAMP_BOUND_CFG_DERIVED coverage) doesn't verify wire-format emit IS bytewise identical for cohort fields between legacy + framework walkers (`subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md:247-249`)

- **Severity:** MEDIUM
- **Category:** § 1 + § 7 CI verification coverage for accounting-relevant parity (cohort fields' wire emit)
- **Details:** Plan body proposes Check 9 at Step 4 as "every STAMP_BOUND_CFG_DERIVED-flagged row has framework consumer". This is a structural-coverage check — does NOT verify the framework consumer produces bytewise-identical wire emit. Without this gate, a future row addition to `FOREACH_CFG_FIELD` with STAMP_BOUND_CFG_DERIVED bit could silently break HMAC chain at production stamp emit time, after `.B.3` has shipped.
- **Recommended fix:** Extend Check 9 (or add Check 9b) at `tools/check_metadata_bit_to_derived_filter_coverage.py` to ALSO verify the framework walker's emit byte output matches legacy walker's emit byte output for all flagged rows at HEAD. Concretely: synthesize cfg with each flagged row populated → emit via legacy walker → emit via framework walker → memcmp == 0. If output drifts, CI fails before merge.
- **DESIGN_SPEC reference:** Layer 5 (snapshot test hash) — adapted to Layer 5b structural invariant style: the test asserts the byte-equivalence INVARIANT, not a hex constant.
- **NOTE:** plan body Step 2 forces deletion of legacy `FOREACH_STAMP_BOUND_CFG` body. After Step 2 the byte-equivalence check has only the framework walker to test against — the legacy walker is gone. Therefore: the byte-equivalence check at Check 9b MUST run BEFORE Step 2 (in CI: against `.B.3` BUT pre-deletion intermediate state) OR a Snapshot fixture captures the byte output AT `.B.2` HEAD + Check 9b asserts the framework walker produces the same bytes at `.B.3+` HEAD. **Recommend the snapshot-fixture approach** — committed `tests/fixtures/b_2_stamp_cohort_emit.bin` + Check 9b memcmp byte test in controller_test.cpp.

---

### [MED-3] v1 stamps' `inference_cfg_thompson_*` fee_rate-adjacent fields' recorded values under LENIENT mode are accounting-adjacent (`ML_Headers/CfgDriftCheckRegistry.hpp:258-273` + Step 5 Decision)

- **Severity:** MEDIUM
- **Category:** § 7 + § 10 Cross-binary parity for accounting-adjacent drift; risk envelope per-instance
- **Details:** Drift check rows for `thompson_mu_prior` / `thompson_precision_prior` / `thompson_precision_obs` at `CfgDriftCheckRegistry.hpp:258-273` are Tier 1 REFUSE_STRICT. The 5th (`thompson_exp3_blend_alpha`) is Tier 1 REFUSE_STRICT gated by `cfg.bandit_algorithm == 4` (BLENDED). All gated by `STAMP_HAS(*h, inference_cfg)`. Under LENIENT mode (per Step 5 surfacing):
  - Engine accepts v1 stamps' load (warn + skip cfg drift).
  - Drift skipped → the runtime cfg→stamp cfg comparison NEVER fires.
  - Even though these rows are NOT direct fee_rate/PnL paths, they are bandit posterior priors used by `Bandit_Update` per-fill (sister to fee_rate as Bandit is part of the trading-decision pipeline; sister to slippage in the sense that posterior drift affects entry-exit timing).
  - **Concrete miscalibration risk:** an operator trained model on `thompson_mu_prior=0.7` + reverts cfg to `thompson_mu_prior=0.5` (default) + loads v1 stamp on `.B.3+` engine in LENIENT mode → drift undetected → engine uses 0.5 (cfg-runtime) for bandit while model was trained for 0.7 → posterior calibration silently broken → bandit arm selection silently miscalibrated → potential silent revenue impact at paper-test time.
- **Recommended fix:**
  - LENIENT mode is a money-path-adjacent silent-failure surface; PER `feedback_evaluate_options_on_robustness_latency_design_not_time`, default STRICT (refuse v1 stamps) per HIGH-1.
  - **If LENIENT preserved as fallback:** LENIENT mode must log per-skipped-drift-row OR a summary line listing ALL skipped drift checks + a flag for the operator-facing GUI panel. Reuse `MLStatusPanel.hpp:469,552` `cfg_binding_drift` flag — add a sibling `cfg_drift_check_skipped` bit + render under "Drift state" panel. This way operator sees in real-time: "stamp loaded LENIENT; X drift checks skipped: thompson_mu_prior, thompson_precision_prior, ...".
- **DESIGN_SPEC reference:** `wire-format-byte-preservation-discipline.md` Surface G (Layer 6) + decision-time-data-binding-pattern.md (the priors are decision-time data).

---

### [MED-4] Plan body sub-step 1.6.7.2 bumps `STAMP_FORMAT_VERSION_CURRENT` 1 → 2 BEFORE any test cover the v2 emit code (sequencing) (`subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md:226-229`)

- **Severity:** MEDIUM
- **Category:** § 6 (sequencing); H9 wire-format byte preservation
- **Details:** Sub-step 1.6.7.0 extracts literal → 1.6.7.1 adds bounds check → 1.6.7.2 bumps 1 → 2 → 1.6.7.3 v1 failure-mode test → 1.6.7.4 DESIGN_SPEC amendment. The order does NOT include a v2-emit-bytes test before the version constant bumps. If sub-step 1.6.7.2 bumps the constant BEFORE the framework walker is verified bytewise-identical to legacy, the bumped emit immediately produces v2 stamps with potentially-broken canonical body.
- **Recommended fix:** REORDER sub-steps: 1.6.7.0 (extract literal) → 1.6.7.1 (MAX_SUPPORTED + bounds check) → **1.6.7.2 (v2 emit byte-equivalence verification via fixture + round-trip HMAC test on POPULATED synthetic stamp; same as recommended at CRITICAL-1)** → 1.6.7.3 (bump 1 → 2) → 1.6.7.4 (v1 failure-mode test) → 1.6.7.5 (DESIGN_SPEC amendment with concrete procedure). Sequencing this way means: the byte chain is verified BEFORE the version constant flips; the bump becomes mechanical-only.

---

### [LOW-1] DESIGN_SPEC amendment at `wire-format-byte-preservation-discipline.md` needs concrete future-bump worked example (`subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md:170 + Step 1.6.7.4`)

- **Severity:** LOW
- **Category:** DOC
- **Details:** Plan body says: "DESIGN_SPEC amendment to wire-format-byte-preservation-discipline.md (procedure section) per spec amendment scope above". A future bump (v2 → v3) operator should be able to read the amendment + mechanically execute the 5-sub-step recipe without rediscovering. The current amendment description is high-level.
- **Recommended fix:** Write the amendment as a WORKED EXAMPLE following the v2 bump literally: "When bumping stamp_format_version N → N+1, do the following 6 steps: (a) extract literal at ModelInference.hpp:1745-1748 if not already extracted to STAMP_FORMAT_VERSION_CURRENT constant — done at .B.3 sub-step 1.6.7.0; (b) verify Layer 4 fixture round-trip via synthetic populated stamp + memcmp byte test + HMAC byte-identical — done at .B.3 sub-step 1.6.7.2; (c) bump constant — done at .B.3 sub-step 1.6.7.3; (d) commit v(N) fixture file at tests/fixtures/v(N)_stamp_canonical.bin if absent; (e) v(N) failure-mode test in controller_test.cpp verifying operator-visible error references stamp_format_version mismatch + actionable regeneration message — done at .B.3 sub-step 1.6.7.4; (f) CHANGELOG entry citing the wire-format change rationale". With (a)-(f) inlined into the DESIGN_SPEC, future operator does not need to rediscover.

---

### [LOW-2] FEATURE_LOOKUP entry "Stamp format version 2" lists cfg flags + fallback + gotchas — precision check needed (`subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md:394-395`)

- **Severity:** LOW
- **Category:** DOC; Auto-write contract
- **Details:** Plan body FEATURE_LOOKUP entry says: "Cfg flags: stamp_format_version is internal; no operator-facing flag." — accurate. "Fallback: STRICT mode refuses v1 stamps; LENIENT mode warns + skips cfg drift (per Step 5 Decision)" — accurate but the LENIENT mode IS effectively a fallback selector + needs cfg flag scope. If LENIENT is added as a runtime cfg flag at all, FEATURE_LOOKUP must surface it. If LENIENT is a build-time mode only / fixture-test only, mark explicitly.
- **Recommended fix:** Once Step 5 decision lands (STRICT vs LENIENT vs both), update FEATURE_LOOKUP entry: if LENIENT is runtime cfg, list cfg flag (e.g., `acknowledge_cross_binary_version_drift` — sister to existing cross-binary drift suppression at `CfgDriftCheckRegistry.hpp:197` Tier — verify whether this knob suppresses or whether new knob `stamp_v1_lenient_load` needed); if LENIENT is build-only, mark "Build flag only — paper-test override". Per `feedback_evaluate_options_on_robustness_latency_design_not_time`, no new cfg flag is the cleanest answer.

---

### [DOC-1] Auto-write entry needed at PARITY_ISSUES.md for `.B.3` stamp wire-format change (`DOCS/PARITY_ISSUES.md` + CLAUDE.local.md auto-write contracts)

- **Severity:** DOC
- **Category:** auto-write contract
- **Details:** Per CLAUDE.local.md "Auto-write contracts" table: "Parity findings → DOCS/PARITY_ISSUES.md → /parity-check or any audit naming a parity surface". This /accounting-audit invokes parity surface (HMAC chain byte preservation + drift gate semantic + v1↔v2 stamp policy). An entry should land at PARITY_ISSUES.md per ship close describing:
  - `.B.3` wire-format change scope (5 prefixed POST_CFG entries → unprefixed framework emit + cohort declaration order change)
  - v1 stamps incompatible with `.B.3+` STRICT engine
  - LENIENT mode semantics if preserved
  - Bandit boundary gate semantic distinction (Decision E (E.2) outcome)
- **Recommended fix:** Plan body Step 9 ship-close ritual ALREADY lists `DOCS/TECH_DEBT.md — 8 entries CLOSED`. ADD: "DOCS/PARITY_ISSUES.md — new entry for v1→v2 stamp policy + bandit boundary gate semantic preservation".

---

## Decision E accounting-path impact assessment (operator-triage requested in invocation)

| Option | Cost-gate fee_rate drift behavior | bandit boundary edge case (algo=2, enabled=0) | thompson posterior fields drift | Verdict |
|---|---|---|---|---|
| **(E.1) — leave separate** | Unchanged | Drift skipped (legacy-correct) | Unchanged Tier 1 REFUSE_STRICT | NO accounting impact; Path γ #3 stays PARTIAL with parallel structures |
| **(E.2) — partial migration** | Unchanged | Drift skipped (preserve `BITMAP_IS_SET(BANDIT_ENABLED)` semantic at bandit row) | Unchanged Tier 1 REFUSE_STRICT (only fold Ridge / Composite / Soft-risk where semantic IS shared) | NO accounting impact; Path γ #3 MOSTLY closed; **CHOSEN per `feedback_proportionate_response_to_audit_findings`** |
| **(E.3) — full migration** | Unchanged at HEAD; future risk if framework gate semantic ever changes | DRIFT FIRES (algo != 0 → check; semantic shift); FALSE POSITIVE on edge case | Unchanged Tier 1 REFUSE_STRICT but gate semantic shifts | accounting-adjacent FALSE-POSITIVE risk; Path γ #3 FULL closure but with behavior shift requiring operator-visible audit-trail |

**/accounting-audit recommendation:** (E.2) per plan body's auto-pick — preserves the BITMAP_IS_SET semantic distinction at bandit boundary; closes shared-semantic cohorts (Ridge / Composite / Soft-risk); no accounting-path semantic shift; no false-positive risk at the bandit edge case; closes Path γ #3 MOSTLY with documented exemption.

---

## Cross-skill convergence

- **CRITICAL-1 (v2 round-trip HMAC test absent)** — anticipate `/parity-check` will flag this independently at Section E (locale + format string + optional semantics). Findings expected to CONVERGE; both audits' recommendation = add v2 fixture round-trip test at Step 1.6.7.3.
- **MED-1 (POST_CFG delete completeness)** — anticipate `/merge-scan` will flag the 9 prefixed POST_CFG rows for unification with framework unprefixed emit. Convergent.
- **MED-3 (LENIENT mode silent-failure risk)** — anticipate `/ml-audit` will flag silent-bandit-miscalibration as parity hazard. Convergent.
- **HIGH-2 (Decision E semantic shift)** — anticipate `/trace-deps` will flag the bandit-boundary edge case + per-row drift behavior matrix. Convergent.

---

## Recommended plan body amendments before pre-coding tag

1. **CRITICAL-1:** Step 1.6.7.3 + 1.6.7.4 sequencing fix; Step 5 STRICT default; Verification gate v2 round-trip line.
2. **HIGH-1:** Step 5 STRICT pick; PARITY_ISSUES.md auto-write entry; operator-visible error message specification.
3. **HIGH-2:** EXPLICIT comment in MlCfgFlagRegistry.hpp at COHORT_GATE_BANDIT_THOMPSON definition citing the distinction.
4. **HIGH-3:** Step 1.6.4 byte-identity assertion concretized; locale-pin sequencing documented.
5. **MED-1:** Step 1.6.2 promote "if also unifiable" to HARD requirement; total deletions = 10 not 5; PARITY_ISSUES.md entry.
6. **MED-2:** Add Check 9b (byte-equivalence) at Step 4 with snapshot fixture.
7. **MED-3:** LENIENT mode operator-facing visibility (GUI panel sibling flag) IF preserved.
8. **MED-4:** Reorder Step 1.6.7 sub-steps to verify-before-bump.
9. **LOW-1 + LOW-2 + DOC-1:** documentation refinements; ship-close auto-write.

---

## End of report.

Findings reflect convergent analysis with `/parity-check`'s expected jurisdiction over the HMAC chain question + `/merge-scan`'s expected jurisdiction over POST_CFG row deletion completeness. /accounting-audit's contribution is the money-path-adjacent angle on Decision E (drift bitmap coupling with fee_rate rows), LENIENT mode silent-failure (bandit posterior miscalibration adjacent to accounting), + the verification-gate sequencing where wire-format change scope intersects accounting-relevant drift detection.
