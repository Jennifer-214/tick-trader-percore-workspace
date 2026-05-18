# Readiness audit — v5.15.5.F.4d.1.B.3 (Legacy empty-out)

**Plan body:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` v1.2 DRAFT (49,724 bytes)
**Engine HEAD:** `9b62a72` — v5.15.5.F.4d.1.B.2 ship close (Cohort migration)
**Ship target:** `v5.15.5.F.4d.1.B.3` (Legacy empty-out — 3 of 3 in `.F.4d.1.B` split)
**Audit date:** 2026-05-17
**Audit scope:** `current` per audit-scope-taxonomy.md (single plan body; standard 28 + Check 29/30)

---

## Overall verdict

**YELLOW** — 0 CRIT, 4 HIGH, 6 MED, 4 LOW, 3 DOC. Plan body is structurally sound + cold-pickup ready + design space discipline present + canonical sister section complete + line refs verified at HEAD. 4 HIGH findings warrant plan body v1.2 → v1.3 amendment before pre-coding tag (mostly bookkeeping precision + Decision E explicit triage timing + DESIGN_SPEC draft sequencing). NO ship-blocker findings.

**Recommendation:** amend v1.2 → v1.3 with 4 HIGH fixes (~30-45 min) BEFORE pre-coding tag; MED/LOW findings landed at coding-time.

---

## CLAUDE_REVIEW.md 10-item checklist

### Item 1 — Hot path purity

**PASS** ✓ — Plan body Verification gate "Hot path: UNTOUCHED" claim verified. Step 1.6.6 drift walker (`CoreModelZoo.hpp:243`) is LOAD-TIME slow path. Framework `drift_check_from_derived` is slow-path/boot-only. `calls_graph_diff verify` confirms post-implementation.

### Item 2 — Train-serve parity

**PASS** ✓ — Step 1.6.4 production canonical body emit migration changes wire byte ORDER (master-registry declaration order vs hand-crafted FOREACH_STAMP_BOUND_CFG order); paired with stamp_format_version 1 → 2 bump (TECH_DEBT-099). Plan Verification gate "wire-format byte preservation under stamp_format_version=2 (v1 stamps refused per STRICT or warned per LENIENT)". `/parity-check` queued at ship close.

### Item 3 — Surface area / coupling

**PASS** ✓ — Public surface preserved at framework-consumer + sister-extension boundaries (Decision A extends PerCoreCfg<F> H17 auto-gen pattern via canonical sister; Decision B extends existing `cfg_derived::drift_check_from_derived` signature). No `if (live_trading)` branches added; all changes are framework-walker swap or legacy deletion.

### Item 4 — Pointer init + heap lifecycle

**PASS** ✓ — N/A for this ship (no new pointer init; no realloc paths). Step 0.5 framework extensions are compile-time + slow-path init; no malloc.

### Item 5 — Backward compat

**FIXED (in plan body)** ✓ — `stamp_format_version` 1 → 2 bump is explicitly v(N) → v(N+1) forward-only at TECH_DEBT-099 Step 1.6.7.0-1.6.7.4. STRICT vs LENIENT decision surfaced at Step 5; STRICT mode refuses v1 stamps (operator-visible error). Plan correctly documents this as MODEL_FORMAT_VERSION-class behavior. Wire keys change for 5 prefixed-only fields (`inference_cfg_<name>` → `<name>`) at Decision D mechanism 1 + coupled with version bump.

### Item 6 — Multi-threading correctness

**PASS** ✓ — N/A new threading. Framework walker is slow-path single-threaded. Drift check at model load is slow-path single-threaded per `EventLoop_UpdateRollingStateOneCore` discipline.

### Item 7 — Test coverage

**FIXED (in plan body)** ✓ — Steps 1.6.7.3 v1 stamp fixture failure-mode test + Step 4 CI Check 9 (STAMP_BOUND_CFG_DERIVED coverage) + Step 5 v5.14 stamp fixture regression test. Plan claims "~3245-3275 tests" post-`.B.3` (current baseline ~3245 at HEAD).

### Item 8 — Docs + invariants

**PASS** ✓ — 4 DESIGN_SPEC amendments enumerated (cfg-scope-discipline.md NEW Override-inherit pattern section; wire-format-byte-preservation-discipline.md NEW Procedure section; cfg-derived-consumer-framework.md v1.2 → v1.3; framework-reason-buffer-extension.md NEW if Decision B (a)). Postmortem + CHANGELOG.md + FEATURE_LOOKUP.md auto-write entries enumerated at Step 9.

### Item 9 — Forward maintenance

**PASS** ✓ — Plan's structural thesis is "after `.B.3` ships, adding a new cfg-derived field = 1 row in master registry; framework auto-flows". Decision A extends global cfg struct-gen to mirror per-core PerCoreCfg<F> H17 pattern. Decision B framework reason_buf extension is reusable for future drift consumers.

### Item 10 — Rollback story

**PASS** ✓ — `pre-v5.15.5.F.4d.1.B.3` rollback anchor at Step 0. Per-major-boundary tag opportunities noted at "Steps section" intro. Tag at ship close `v5.15.5.F.4d.1.B.3` signed.

---

## Checks 11-28 (full 28-item discipline — `/readiness` extended)

### Item 11 — Cohort eligibility audit

**PASS** ✓ — Decision D scope (5 prefixed-only fields) — these are scalar fields (FPN<F>/double/int), not boolean cfg-flag candidates. `cfg-flag-eligibility-criteria.md` 5-criteria apply to boolean → bitmap migration, NOT scalar → STAMP_BOUND_CFG_DERIVED. The correct discipline here is: each field passes "is this a cfg-derived value the model stamp needs to capture for drift detection?" — verified YES per existing prefixed POST_CFG entries at `StampBoundModelConstRegistry.hpp:454-483`. Audit task Check 7 framing slightly off; verdict PASS on the actual semantic.

### Item 12 — Categorical applicability columns

**PASS** ✓ — 5 prefixed-only fields' master registry rows at `CfgFieldRegistry.hpp:534/535/537/646` already have applies_to_* columns populated (STRAT_CAT_ML | STRAT_CAT_USES_BANDIT etc.). `MlCfgFlagRegistry.hpp:70` PER_HORIZON_BARRIER_BLEND has metadata_flags column. No new fields added; existing columns drive framework.

### Item 13 — Cross-file cfg surfaces with `lives_in_struct`

**PASS** ✓ — Decision A's `gap_acceptable_threshold` lives in `ControllerConfig<F>` (global scope); existing master-registry row at `FOREACH_GLOBAL_CFG_FIELD` has `lives_in_struct` enum already wired per cfg-scope-discipline.md. Step 0.5b struct-gen extension is sister-pattern to per-core auto-gen.

### Item 14 — Bitmap overflow static_assert (H18 / mandatory)

**PASS** ✓ — No new bitmaps; uses existing `g_per_core_cfg_stamp_bound_cfg_derived_mask` + `g_global_cfg_stamp_bound_cfg_derived_mask` (from `.B.2`). Step 1 test count-assertion migration uses these masks via `cfg_field_count(...)` popcount.

### Item 15 — Type-trait dispatch via `tt::` namespace

**PASS** ✓ — Step 0.5c verifies `tt::cfg_drift_compare<StampT, CfgT>` handles all cohort + 5 prefixed-only field types (FPN<F> + double + int); static_assert coverage added if gaps. Decision D mechanism 1 inf struct unification uses `tt::cfg_populate_inf_field<T>` per existing pattern. No `*reinterpret_cast<T*>` punning.

### Item 16 — Multi-bit state encoding (H14)

**PASS** ✓ — No new K-state fields. `barrier_blend_mode` enum [0/1/2/3] already encoded in master registry row at `:646`. No new MBS_* encoding.

### Item 17 — Cfg↔ML surface-alignment 4-column audit

**PASS** ✓ — Decision D mechanism 1 explicitly addresses: cfg parse (existing, no change) + Settings render (master registry, no change) + Stamp tag (POST_CFG deleted; framework walker emits unprefixed at unified flow) + Per-core override (existing). `/ml-audit` fires at ship close.

### Item 18 — Reuse-audit (merge-scan principle)

**PASS** ✓ — Plan body Canonical sister registries considered section enumerates 11 candidates with per-candidate verdict (4 EXTEND / 4 DELETE / 1 MIGRATE / 1 NO-FOLD / 1 OPERATOR TRIAGE). Decision A explicitly extends canonical sister (PerCoreCfg<F> auto-gen). Decision B explicitly extends canonical sister (`cfg_derived::drift_check_from_derived` template fn). No parallel infrastructure added.

### Item 19 — Decision-time data binding for per-instance cfg values

**PASS** ✓ — Framework reads cfg at slow-path/load-time only. No Class 27 scalar cfg-mirror surface added. Drift check at model load happens once per model load (not per-tick). Production canonical body emit at stamp emit (slow path).

### Item 20 — Branchless dispatch (H20)

**PASS** ✓ — Decision B framework `drift_check_from_derived` uses mask-select `failure_flags` per H20. Decision B (a) `reason_buf` extension preserves branchless dispatch — caller passes nullptr to skip; framework writes first-drift attribution branchlessly. Plan Verification gate "Hot path: UNTOUCHED".

### Item 21 — Audit hand-waves (`feedback_consult_on_audit_findings`)

**PASS** ✓ — Plan body explicitly surfaces Decision E (CfgDriftCheck consolidation) for operator triage rather than auto-pick — correctly identifies this as a genuinely sharp trade-off. No "branch is fine because predictor handles it" framings present.

### Item 22 — Audit scope explicit

**PASS** ✓ — Plan body Pre-coding triggers list `/precoding-audit-gate` at trigger #3 with 6 audits parallel. Scope is `current` (single plan body). Default per audit-scope-taxonomy.md.

### Item 23 — Multi-state dispatch with per-state metadata

**PASS** ✓ — No new N-state enums. `bandit_algorithm` (5-state) + `barrier_blend_mode` (4-state) already encoded via existing X-macro rows + categorical applicability columns. Decision E discusses bandit boundary semantic but does not propose new state encoding.

### Item 24 — Audit canonical sister before new infra

**PASS** ✓ — This is the headline strength of v1.2 plan body. Canonical sister registries considered section with 11 candidates + per-candidate verdict + rationale + 3-question test applied. Per `feedback_audit_canonical_sister_before_new_infra` discipline.

### Item 25 — Framework-layer payoff diminishing returns

**PASS** ✓ — Plan body "Caramel's professionalization-phase context" section explicitly cites `feedback_framework_layer_payoff_diminishing_returns`: "this is one of the last framework-layer additions before the inflection point; the value-add justifies the cost". Decision A struct-gen extension is ~50-100 LOC mechanical extension of canonical sister, not new framework layer. Decision B is ~30 min extension of existing template fn signature.

### Item 26 — Proportionate response to audit findings

**PASS** ✓ — Decision E surfaces full menu (E.1 / E.2 / E.3) with honest evaluation per option + auto-pick (E.2) per `feedback_proportionate_response_to_audit_findings`. Decisions A/B/C/D auto-pick the future-oriented option; Decision E surfaces because trade-off is genuinely sharp (operator-visible behavior change at bandit boundary).

### Item 27 — Plan right not fast

**PASS** ✓ — 5 design decisions enumerated; each with honest evaluation across robustness/latency/design/future-easier axes; auto-pick where clear; surface where genuinely sharp. Effort estimate ~12-18h focused acknowledges depth of work; not compressed for speed. Per `feedback_plan_right_not_fast`.

### Item 28 — Auto-pick discipline + future-oriented choice

**PASS** ✓ — Decisions A/B/C/D auto-pick documented with rationale. Decision E explicitly NOT auto-picked (correctly surfaced). Auto-pick rationale cites `feedback_motivated_collaborator_for_caramel` + `feedback_no_defer_for_effort` where applicable. Per `feedback_auto_pick_future_oriented` discipline.

---

## Check 29 — Canonical sister registries section present

**PASS** ✓ — Section present at lines 116-142 of plan body. 11 candidates enumerated:

| # | Candidate | Verdict | Verified at HEAD |
|---|---|---|---|
| 1 | FOREACH_GLOBAL_CFG_FIELD struct-gen | EXTEND (sister of PerCoreCfg<F> H17 auto-gen) | Confirmed: no struct auto-gen at HEAD; PerCoreCfg<F> via H17 exists |
| 2 | `cfg_derived::drift_check_from_derived` | EXTEND (canonical sister) | Confirmed: signature at `CfgGateRegistry.hpp:316` |
| 3 | FOREACH_STAMP_BOUND_CFG | DELETE (legacy fold-out) | Confirmed: macro body at `StampBoundCfgRegistry.hpp:99-179` |
| 4 | FOREACH_CFG_DERIVED_INFERENCE_CFG | DELETE (legacy fold-out) | Confirmed: macro at `CfgDerivedInferenceCfgRegistry.hpp:101-123` |
| 5 | FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG 5 prefixed | DELETE (Decision D) | Confirmed: 5 entries at `:454-465`; 4 thompson at `:469-483` |
| 6 | FOREACH_STAMP_BOUND_MODEL_CONST (parent) | NO-FOLD (different concern) | Correct — model state vs cfg-derived |
| 7 | FOREACH_CFG_DRIFT_CHECK | OPERATOR TRIAGE (Decision E) | Correctly surfaced |
| 8 | FOREACH_CFG_GATE_PER_CORE + _GLOBAL (from .B.1/.B.2) | NO-CHANGE | Confirmed |
| 9 | FOREACH_ML_CFG_FLAG metadata_flags column | EXTEND (1 row for PER_HORIZON_BARRIER_BLEND) | Confirmed: row at `MlCfgFlagRegistry.hpp:70` flag=0 |
| 10 | STAMP_CFG_AUTOPOPULATE macro | DELETE (legacy mechanism) | Confirmed |
| 11 | FOREACH_STAMP_BOUND_CFG_COUNT constant | MIGRATE (mechanical test fixture) | Confirmed: 4 sites in tests/controller_test.cpp |

Per-candidate verdict has rationale; 3-question test applied; "Verified by `/merge-scan` + `/anti-spaghetti` at pre-coding audit gate Batch 1" present. Discipline shape COMPLETE.

---

## Check 30 — Design space + future-oriented choice section present

**PASS** ✓ — Section present at lines 33-113. 5 major design decisions enumerated:

| Decision | Options | Auto-pick / Surface | Evaluation axes |
|---|---|---|---|
| A — gap_acceptable_threshold cleanup at `.B.3` | (a) struct-gen extension / (b) defer | (a) auto-pick | robustness / latency / design / future-easier |
| B — Framework reason_buf extension vs accept behavior change | (a) extend / (b) accept | (a) auto-pick | robustness / latency / design / future-easier |
| C — Struct-gen approach for StampInferenceCfgInputs + ModelStampResult | (A) unconditional / (B) macro filter / (C) defer | (A) auto-pick | robustness / latency / design / future-easier |
| D — Inf struct unification mechanism (5 prefixed-only fields) | (1) delete POST_CFG + flag master / (2) double-emit / (3) search-replace | (1) auto-pick | wire-format impact / robustness |
| E — CfgDriftCheck registry consolidation | (E.1) leave / (E.2) partial / (E.3) full | (E.2) recommend; SURFACE for operator | robustness / closure depth |

Each decision has ≥2 options + evaluation on robustness / latency / design / future-easier + auto-pick rationale citing memory files. Decision E correctly surfaces rather than auto-picking. Discipline shape COMPLETE.

---

## Findings (severity-tagged)

### HIGH-1 — Effort estimate range broad given Decision E outcome variance

**Severity:** HIGH (plan amendment)

Plan body Steps section estimates "~12-18h focused" — 50% spread. Decision E outcome materially affects estimate:
- (E.1) leave: 0 extra hours
- (E.2) partial: +1-2h drift consumer macro extension + per-row mapping
- (E.3) full: +3-4h CfgDriftCheck deletion + drift consumer migration + drift fixture verify

**Recommendation:** amend plan body to enumerate effort PER Decision E outcome (E.1: ~12-14h / E.2: ~13-16h / E.3: ~15-18h). Per `feedback_evaluate_options_on_robustness_latency_design_not_time` — operator decides Decision E on robustness/design axes, but effort transparency at decision time supports the triage.

### HIGH-2 — `framework-reason-buffer-extension.md` Stage 2 DRAFT not on disk yet

**Severity:** HIGH (plan amendment / Pre-coding requirement)

Plan body Pre-coding trigger #6: "NEW DESIGN_SPECs Stage 2 DRAFT exist on disk (especially `framework-reason-buffer-extension.md` if Decision B (a))". `ls` confirms file does NOT exist at `tick-trader-percore-workspace/DESIGN_SPECS/framework-reason-buffer-extension.md`. Plan correctly cites this as Step 0 deliverable BUT also lists it as pre-coding requirement #6.

**Recommendation:** clarify sequencing — pre-coding trigger #6 must complete BEFORE pre-tag rollback anchor (Step 0); Step 0 should reference "draft file written at Step 0 pre-tag landing" not "Step 0 of coding". Resolve ambiguity by either (a) explicitly state Stage 2 DRAFT lands at v1.3 amendment cycle (BEFORE pre-coding tag) OR (b) state Step 0 of coding = "git tag pre-v5.15.5.F.4d.1.B.3 AFTER Stage 2 DRAFT lands". The latter is cleaner. Per `feedback_plan_right_not_fast` — surface this for operator clarity now rather than discover at Step 0.

### HIGH-3 — Step 1.6.5 sub-step ambiguity (1 vs 2 calls survive)

**Severity:** HIGH (plan amendment)

Plan body Step 1.6.5: "may collapse to 1 call OR keep both if their semantics differ — verify via trace". The "may" + "verify via trace" without a concrete pre-determination violates `feedback_no_defer_for_effort` ("Defer is last-ditch, never effort-avoidance"). The trace work is mechanical (`/trace-deps` on STAMP_CFG_AUTOPOPULATE callers) — should resolve at plan-time rather than coding-time.

**Recommendation:** at v1.3 amendment, fire `/trace-deps chain:STAMP_CFG_AUTOPOPULATE` and bake the result into Step 1.6.5 ("collapse to 1 call at line 156" OR "preserve both calls at 156 + 183 because <semantic difference>"). ~10 min trace + 2-line plan body update.

### HIGH-4 — Decision E timing relative to pre-coding tag unclear

**Severity:** HIGH (plan amendment)

Pre-coding trigger #10: "Operator triage on Decision E completed (E.1 / E.2 / E.3)". Plan body Decision E section states "Surface to Caramel inline at audit triage; her preference governs". But "audit triage" timing is ambiguous — is it pickup Step 4 (audit synthesis) OR a separate operator consult AFTER pre-coding tag created?

**Recommendation:** specify exact pre-coding workflow sequencing:
1. Audit synthesis written (pickup Step 4)
2. Decision E triage with operator BEFORE pre-coding tag (Decision E surfaced; operator picks E.1/E.2/E.3; plan v1.2 → v1.3 with chosen path)
3. NEW DESIGN_SPECs Stage 2 DRAFT land (HIGH-2)
4. Pre-coding tag created at v1.3 lock
5. Step 0 of coding begins

Currently Pre-coding trigger #10 sits last; reorder to make Decision E triage BEFORE Stage 2 DRAFT land + BEFORE pre-coding tag. Per `feedback_consult_on_audit_findings`.

---

### MED-1 — Decision D 4 thompson POST_CFG entries scope ambiguity

**Severity:** MED (coding-time)

Plan body Step 1.6.2: "DELETE 5 prefixed POST_CFG entries at `StampBoundModelConstRegistry.hpp:454-465` + bandit/thompson 4 at `:469-483` if also unifiable (Decision D scope clarification: 4 thompson rows already cohort-migrated at `.B.2`; need to verify whether their POST_CFG mirror entries need deletion at `.B.3` to avoid double-emit)". The "if also unifiable" + "need to verify" is coding-time deferral that should be pre-determined.

**Recommendation:** at v1.3, verify whether 4 thompson POST_CFG entries at `:469-483` need deletion. If their unprefixed sister already in master registry (likely — bandit_algorithm / thompson_mu_prior / etc. at `CfgFieldRegistry.hpp` 1xxx range), they ARE redundant once `.B.3` deletes FOREACH_STAMP_BOUND_CFG. Decision D scope should explicitly enumerate 9 deletions (5 prefixed-only + 4 thompson mirrors) OR document why 4 thompson rows kept.

### MED-2 — Step 1 test migration claim on weakening

**Severity:** MED (coding-time)

Plan body Step 1: "Verify all assertions still STRENGTHEN (not weaken) per `/test-strength-audit` discipline; document rationale per migration". This is correctly framed; the migration `FOREACH_STAMP_BOUND_CFG_COUNT >= N` → `cfg_field_count(per_core_mask) + cfg_field_count(global_mask) >= N` is a SAME-strength migration (same N threshold; same value semantic per `.A`-shipped dual-mask helper).

**Recommendation:** no plan amendment; verify at `/test-strength-audit` Step 8.

### MED-3 — `MlCfgFlagRegistry.hpp:70` line ref vs `:64` cross-ref

**Severity:** MED (coding-time)

Plan body claims `MlCfgFlagRegistry.hpp:70` for per_horizon_barrier_blend (PASS — verified at line 70). But TECH_DEBT-100 cross-ref at `DOCS/TECH_DEBT.md:1790` says `MlCfgFlagRegistry.hpp:64` (per the comment block describing the deferral inline at the row). The :64-70 spread is the comment block + the row; PASS at the row level (`:70`).

**Recommendation:** no plan body amendment needed; document in postmortem that comment block at `:64` + row at `:70` is contiguous. Low-precision cross-ref inconsistency; not load-bearing.

### MED-4 — Step 1.6.7.1 sequencing — bounds check before bump

**Severity:** MED (coding-time)

Plan Step 1.6.7.1: "Add `MAX_SUPPORTED_STAMP_FORMAT_VERSION = N;` constant + parser bounds check at `:1346-1351`". The value of N matters for ordering:
- If N = 2 (current = 2 post-bump), parser refuses anything > 2
- If N = 1 (pre-bump), parser refuses 2 → bumping breaks parser

**Recommendation:** at v1.3, specify N = 2 (final post-bump value). Sub-step 1.6.7.1 sequencing: bounds check N=2 lands BEFORE step 1.6.7.2 bump (so the parser accepts the new bumped value). Or equivalently: both land together as one atomic commit.

### MED-5 — Step 1.6.6 `failure_mask` constant origin

**Severity:** MED (coding-time)

Plan Step 1.6.6: drift walker migration call `cfg_derived::drift_check_from_derived<F>(failure_flags, stamp_has_inference_cfg, FAILURE_MASK_cfg_inference_drift, sr, cfg, drift_count, sr.reason, sizeof(sr.reason))`. The `FAILURE_MASK_cfg_inference_drift` constant — where defined?

**Recommendation:** at v1.3, cite the file:line where `FAILURE_MASK_cfg_inference_drift` is defined (likely `MemHeaders/FailureModeRegistry.hpp` or sister registry). If not yet defined, this becomes a new constant added at Step 0.5d.

### MED-6 — `tools/check_metadata_bit_to_derived_filter_coverage.py` existence at HEAD

**Severity:** MED (coding-time)

Plan body Step 4: "Tools at `tools/check_metadata_bit_to_derived_filter_coverage.py` (per H16) — verify each metadata bit has derived filter row + walker mechanism". Audit task does not require verification but plan claims the tool exists at HEAD.

**Recommendation:** verify tool exists at HEAD before coding; if not, Step 4 is also a tool-write deliverable. ~30 min if write-from-scratch.

---

### LOW-1 — Plan body L19 typo: "Path γ #3 PARTIAL closure" vs "PARTIAL closure"

**Severity:** LOW (cosmetic)

Plan body line 19: "Path γ #3 PARTIAL closure (2-of-3 cohort-gate registries unified via COHORT_GATE_* macros)". Consistent with predecessor `.B.2` postmortem language. PASS.

### LOW-2 — `CoreModelZoo.hpp:225-247` range vs `:243` macro site

**Severity:** LOW (precision)

Plan body cites `CoreModelZoo.hpp:225-247` for drift walker block. The FOREACH_STAMP_BOUND_CFG(X) is at line 243 specifically; the block starts at ~221 and ends ~248. Plan range is correct.

**Recommendation:** none; plan range covers the block per convention.

### LOW-3 — Plan body L222 "training-time fill at `:156` is sister to production stamp emit at `:183`"

**Severity:** LOW (precision)

Verified at HEAD: line 156 is `STAMP_CFG_AUTOPOPULATE(inf, cfg)` in `Stamp_AssembleAndEmit` (production emit caller, NOT training-time). The "training-time fill" framing in plan body is slightly inverted; both calls are in the same production emit context (line 156 walks STAMP_CFG_AUTOPOPULATE; line 183 walks INFERENCE_CFG_AUTOPOPULATE).

**Recommendation:** at v1.3, correct plan body L222 framing: line 156 + 183 are TWO different concerns within the same production emit chain (cfg-bound fields at 156; cfg-derived inf cfg fields at 183). Decision C Approach A unifies both via single framework call OR keeps both if cfg vs cfg-derived distinction warrants.

### LOW-4 — Plan body L260 "first canonical NEW plan body drafted from inception"

**Severity:** LOW (precision)

Plan body status header line 8: "first canonical NEW plan body drafted from inception via `future-oriented-plan-template.md` Stage 3 ACTIVE". Note that `.B.1` v1.1 was the FIRST canonical reference of the template (retrofit at ship close 2026-05-17 per template doc Stage 3). `.B.3` v1.2 is the first NEW plan body using template from inception (not retrofit). Distinction correct; framing slightly confusing.

**Recommendation:** at v1.3, refine language: "first canonical NEW plan body drafted from inception (vs `.B.1` v1.1 retrofit)". Minor.

---

### DOC-1 — Predecessor postmortem ship status terminology

**Severity:** DOC (documentation only)

Plan body Predecessor: "v5.15.5.F.4d.1.B.2 (cohort migration; shipped 2026-05-17 LOCAL; engine `9b62a72`; GPG-signed tag; push pending operator authorization)". "shipped LOCAL" is workspace convention but not enforced in DOCS. Verified at HEAD `9b62a72` matches.

### DOC-2 — Cross-references table missing some sister-plan stub references

**Severity:** DOC (documentation only)

Plan body Cross-references section enumerates: sub-master + predecessor postmortem + audit synthesis + sprint roadmap + sister plan stub + 6 spec files + TECH_DEBT entries + Hard invariants + Recurring bug patterns. Missing: explicit cross-ref to `pattern-codification-lifecycle.md` (which Decision B (a) NEW spec is governed by) + `feedback_motivated_collaborator_for_caramel` (cited inline in Decision A but not in Cross-references). MINOR.

**Recommendation:** at v1.3, add 2 cross-refs.

### DOC-3 — DESIGN_SPECs amendment "Stage X.Y → Stage X.Y+1" version syntax

**Severity:** DOC (documentation only)

Plan body L165-178: "AMENDED" section uses syntax `v1.X → v1.X+1` for cfg-scope-discipline.md + wire-format-byte-preservation-discipline.md; uses `v1.2 → v1.3` for cfg-derived-consumer-framework.md (specific). MINOR inconsistency — for the 2 specs whose current version is not specified, look them up + cite specifically.

**Recommendation:** at v1.3, verify cfg-scope-discipline.md current version (likely v1.0 or v1.1) + wire-format-byte-preservation-discipline.md current version; cite as `vX.Y → vX.Y+1`.

---

## Line-ref verification table (vs HEAD `9b62a72`)

| Plan claim | HEAD verification | Verdict |
|---|---|---|
| `ControllerConfig.hpp:889` — gap_acceptable_threshold decl | Line 889: `FPN<F>   gap_acceptable_threshold;` | PASS |
| `ControllerConfig.hpp:1729` — gap_acceptable_threshold default | Line 1729: `cfg.gap_acceptable_threshold    = FPN_FromDouble<F>(0.05);` | PASS |
| `ControllerConfig.hpp:2555` — gap_acceptable_threshold parser | Line 2555: `CFG_PARSE_FPN(gap_acceptable_threshold)` | PASS |
| `CfgFieldRegistry.hpp:534` — ml_tp_pct | Line 534: `X(FPN<F>, KIND_DOUBLE_PCT, ml_tp_pct, ...)` | PASS |
| `CfgFieldRegistry.hpp:535` — ml_sl_pct | Line 535: `X(FPN<F>, KIND_DOUBLE_PCT, ml_sl_pct, ...)` | PASS |
| `CfgFieldRegistry.hpp:537` — bandit_blend_ratio | Line 537: `X(FPN<F>, KIND_DOUBLE, bandit_blend_ratio, ...)` | PASS |
| `CfgFieldRegistry.hpp:646` — barrier_blend_mode | Line 646: `X(int, KIND_INT, barrier_blend_mode, ...)` | PASS |
| `ModelInference.hpp:1199` — StampInferenceCfgInputs FOREACH walker | Line 1199: `FOREACH_STAMP_BOUND_CFG(X)` in ModelStampResult struct | PASS (plan body uses `:1196-1199` range for struct + walker block; correct) |
| `ModelInference.hpp:1401` — parser branches FOREACH walker | Line 1401: `FOREACH_STAMP_BOUND_CFG(X)` in parser | PASS (`:1396-1401` block) |
| `ModelInference.hpp:1643` — ModelStampResult FOREACH walker | Line 1643: `FOREACH_STAMP_BOUND_CFG(X)` in StampInferenceCfgInputs struct | PASS (`:1640-1643` block; NOTE plan body L66 says ":1640-1643 for ModelStampResult struct-gen" but it's actually StampInferenceCfgInputs — INVERTED at L66 vs L218; see LOW-5 below) |
| `ModelInference.hpp:1788` — canonical body emit FOREACH walker | Line 1788: `FOREACH_STAMP_BOUND_CFG(X)` in emit | PASS (`:1782-1788` block) |
| `CoreModelZoo.hpp:243` — drift walker | Line 243: `FOREACH_STAMP_BOUND_CFG(X)` in drift check | PASS |
| `StampHelper.hpp:156` — STAMP_CFG_AUTOPOPULATE | Line 156: `STAMP_CFG_AUTOPOPULATE(inf, cfg);` | PASS |
| `StampHelper.hpp:183` — INFERENCE_CFG_AUTOPOPULATE | Line 183: `INFERENCE_CFG_AUTOPOPULATE(inf, cfg);` | PASS |
| `MlCfgFlagRegistry.hpp:70` — per_horizon_barrier_blend | Line 70: `X(PER_HORIZON_BARRIER_BLEND, per_horizon_barrier_blend, ...)` flags=0 | PASS |

**Net:** 15/15 line refs verified at HEAD `9b62a72`. One additional precision finding (LOW-5 below).

### LOW-5 — Plan body L66 vs L218 struct-name inversion

**Severity:** LOW (precision)

Plan body L66 (Decision C context): "e.g., `ModelInference.hpp:1196-1199` for `StampInferenceCfgInputs`; `:1640-1643` for `ModelStampResult`". Plan body L218 (Step 1.6.3): "`ModelInference.hpp:1196-1199` (StampInferenceCfgInputs struct-gen)" + "`ModelInference.hpp:1640-1643` (ModelStampResult struct-gen)".

Verified at HEAD: `:1196-1199` is INSIDE the `ModelStampResult` struct (which begins around line 1100). `:1640-1643` is INSIDE the `StampInferenceCfgInputs` struct (which begins at line 1627).

**Inversion:** Plan body L66 + L218 have the struct names SWAPPED. Plan claims `:1196-1199` = StampInferenceCfgInputs but it's actually ModelStampResult; `:1640-1643` = ModelStampResult but it's actually StampInferenceCfgInputs.

**Recommendation:** at v1.3, swap the struct names in both L66 + L218. This is load-bearing for coding accuracy — Step 1.6.3 sub-steps need to correctly identify which struct gets which migration.

---

## TECH_DEBT-09X coverage table

| TECH_DEBT | DOCS/TECH_DEBT.md row | Plan Step home | Severity | Plan structural commitment |
|---|---|---|---|---|
| -093 | 1683 | Step 1.6.1 | LOW-MED | EXPLICIT: "DELETE manual decl at `:889`; DELETE manual default at `:1729`; DELETE manual parser at `:2555`. Field becomes auto-gen via FOREACH_GLOBAL_CFG_FIELD." |
| -094 | 1696 | Step 1.6.2 | MED | EXPLICIT: "metadata_flags gains STAMP_BOUND \| STAMP_BOUND_CFG_DERIVED" + "DELETE 5 prefixed POST_CFG entries" (MED-1 ambiguity about 4 thompson mirrors) |
| -095 | 1709 | Step 1.6.3 | MED | EXPLICIT: "replace FOREACH_STAMP_BOUND_CFG(X) walker with unconditional struct-gen via master per-core + global + ML_CFG_FLAG (filtered by bit)" |
| -096 | 1722 | Step 1.6.4 | HIGH | EXPLICIT: "Replace FOREACH_STAMP_BOUND_CFG(X) walker with `cfg_derived::populate_stamp_cfg_from_derived<F>(...)` call" + "THIS IS THE WIRE-FORMAT-CHANGING STEP — couples with Step 1.6.7 stamp_format_version bump" |
| -097 | 1735 | Step 1.6.5 | MED | EXPLICIT: "swap to framework consumer" — BUT contains "verify whether 1 or 2 calls survive" deferral (HIGH-3) |
| -098 | 1748 | Step 1.6.6 | MED | EXPLICIT: "Replace inline FOREACH_STAMP_BOUND_CFG(X) drift walk with `cfg_derived::drift_check_from_derived<F>(failure_flags, ...)` call. Extended framework signature per Step 0.5a preserves operator-visible first-drift reason message" |
| -099 | 1761 | Step 1.6.7 (5 sub-steps) | HIGH | EXPLICIT: 5 sub-steps (1.6.7.0 extract / 1.6.7.1 bounds check / 1.6.7.2 bump / 1.6.7.3 fixture test / 1.6.7.4 DESIGN_SPEC amendment) — MED-4 sequencing precision concern |
| -100 | 1779 | Step 1.6.2 (paired) | LOW-MED | EXPLICIT: "PER_HORIZON_BARRIER_BLEND: metadata_flags `0` → `STAMP_BOUND_CFG_DERIVED` (TECH_DEBT-100)" |

**Net:** 8/8 TECH_DEBT-09X items have concrete home in plan body with structural commitment. NO "may defer" or "TODO" framings — all have explicit Step + structural action.

---

## LOAD-BEARING deferral non-downgrade verification

Plan body Audit task #6 requires: "verify plan body Step 1.6.X items treat each as ship-blocking (build BREAKS without items 4-6 per Step 2 forces)".

Plan body Step 2: "**BUILD BREAKS HERE if Steps 1.6.3 + 1.6.4 + 1.6.5 + 1.6.6 not addressed**". Items 4, 5, 6 = Steps 1.6.4, 1.6.5, 1.6.6.

| Item | Plan body Step | Build-forcing? | Verdict |
|---|---|---|---|
| TECH_DEBT-093 (gap_acceptable_threshold cleanup) | 1.6.1 | NOT build-forcing (cleanup, not migration) | LOW-MED severity correct; not ship-blocker |
| TECH_DEBT-094 (5 prefixed bit-add + POST_CFG delete) | 1.6.2 | Build-forcing IFF coupled with Step 1.6.4 wire change | Per Step 2 forcing constraint — YES |
| TECH_DEBT-095 (ModelInference struct-gen) | 1.6.3 | Build-forcing per Step 2 | YES |
| TECH_DEBT-096 (canonical body emit migration) | 1.6.4 | Build-forcing per Step 2 + Step 1.6.7 coupling | YES |
| TECH_DEBT-097 (STAMP_CFG_AUTOPOPULATE swap) | 1.6.5 | Build-forcing per Step 2 | YES |
| TECH_DEBT-098 (drift walker migration) | 1.6.6 | Build-forcing per Step 2 | YES |
| TECH_DEBT-099 (stamp_format_version bump) | 1.6.7 | NOT build-forcing in isolation (independent wire-format concern) BUT plan body Sequencing constraint: "MUST couple with Step 1.6.4" | YES (via coupling) |
| TECH_DEBT-100 (PER_HORIZON_BARRIER_BLEND bit) | 1.6.2 paired | Build-forcing per Step 1.6.2 inheriting Step 2 force | YES |

**Net:** 7/8 are build-forcing (TECH_DEBT-093 is cleanup, not migration; correctly marked LOW-MED in TECH_DEBT.md). NONE downgradable. PASS.

---

## DESIGN_SPECS amendment readiness

| Spec | Plan-time status | Pre-coding requirement met? | Notes |
|---|---|---|---|
| `cfg-scope-discipline.md` | At HEAD (existing v1.X) | YES — amendment at Step 6 (post-implementation) | New Override-inherit pattern section per `.B.2` Discovery 5 |
| `wire-format-byte-preservation-discipline.md` | At HEAD (existing v1.X) | YES — amendment at Step 6 | New "Procedure for wire-format changes" section per TECH_DEBT-099 |
| `cfg-derived-consumer-framework.md` v1.2 | At HEAD | YES — amendment at Step 6 v1.2 → v1.3 | Walker migration + inf struct unification sections |
| `framework-reason-buffer-extension.md` (NEW) | NOT on disk | NOT YET — required at Stage 2 DRAFT BEFORE pre-coding tag per trigger #6 | HIGH-2 finding — clarify sequencing |

**Recommendation:** at v1.3, explicitly state Stage 2 DRAFT of `framework-reason-buffer-extension.md` lands BEFORE pre-coding tag (HIGH-2). The other 3 amendments are post-implementation at Step 6.

---

## Effort estimate validation

Plan body claims ~12-18h focused. Breakdown:
- Steps 0 + 0.5a/b/c: ~2-4h (struct-gen extension is the heavy lift)
- Step 1: ~30-60 min (mechanical test fixture migration)
- Step 1.5: ~30 min (2 site swaps)
- Step 1.6 substeps: ~4-6h total
- Step 2 + 3: ~30 min (mechanical deletions)
- Step 4: ~1-2h (CI Check 9 substantive)
- Step 5: ~1-2h (fixture synthesis + failure-mode test)
- Step 6: ~1-2h (DESIGN_SPEC amendments)
- Step 7: ~15-30 min
- Step 8: ~30-60 min
- Step 9: ~1h

**Sum:** ~11-19.5h. Per HIGH-1, Decision E outcome shifts this:
- (E.1): ~11-13h
- (E.2): ~12-15h
- (E.3): ~14-19.5h

**Verdict:** plan estimate ~12-18h is REASONABLE for (E.1)/(E.2); SLIGHTLY OPTIMISTIC at top end for (E.3). Recommend amendment per HIGH-1 to surface Decision E impact on effort.

Sub-step risk areas (per scoping):
- Step 0.5b struct-gen extension: novel work; PerCoreCfg<F> sister exists but FOREACH_GLOBAL_CFG_FIELD struct-gen is NEW (H17 says cfg struct fields auto-gen from FOREACH_CFG_FIELD; global side currently exempt). ~2-3h realistic; could surface unexpected `ControllerConfig<F>` template instantiation issues (plan acknowledges this).
- Step 1.6.4 canonical body emit migration: wire byte order changes; HMAC chain regression risk if Step 1.6.7 stamp_format_version bump not properly coupled.
- Step 1.6.7.3 v1 fixture failure-mode test: synthesizing fixture is non-trivial; ~1h fixture + ~30 min test.
- Step 4 CI Check 9: tool may not exist at HEAD (MED-6); could be +30 min if write-from-scratch.

---

## Cold-pickup completeness audit

| Element | Status | Notes |
|---|---|---|
| Branch | PASS | `feat/v5.15-live-readiness` |
| Exec-order | PASS | Steps 0-9 enumerated; Sequencing constraint explicit |
| Step 0 | PASS | Pre-coding rollback anchor + Stage 2 DRAFT spec land |
| Function names | PASS | `cfg_derived::drift_check_from_derived`, `cfg_derived::populate_inference_cfg_from_derived`, `cfg_derived::populate_stamp_cfg_from_derived`, `tt::cfg_drift_compare`, `cfg_field_count` all enumerated |
| file:line refs | PASS (with LOW-5) | 15/15 verified; struct-name inversion at L66/L218 (LOW-5) |
| Stale-claim audit | PASS | No stale-claim issues found; line refs verified at HEAD |
| Effort-vs-LOC | PASS | ~12-18h focused acknowledged (Decision E variance per HIGH-1) |
| Source-audit paths | PASS | Audit task lists 7 paths; plan body Cross-references enumerates 9 |
| Predecessor paths | PASS | `.B.2` postmortem + audit synthesis + sub-master enumerated |
| Tag+rollback anchors | PASS | `pre-v5.15.5.F.4d.1.B.3` (Step 0) + `v5.15.5.F.4d.1.B.3` (Step 9) + GPG-signed |

**Cold-pickup verdict:** PASS. Another instance could pick this plan up cold from v1.2 draft with HIGH-2/HIGH-3/HIGH-4 amendments + LOW-5 correction.

---

## Recommendations summary (plan body v1.2 → v1.3 amendment list)

**Before pre-coding tag** (HIGH severity):
1. **HIGH-1** — Enumerate effort estimate per Decision E outcome (E.1: ~12-14h / E.2: ~13-16h / E.3: ~15-18h)
2. **HIGH-2** — Clarify `framework-reason-buffer-extension.md` Stage 2 DRAFT lands BEFORE pre-coding tag; explicit sequencing
3. **HIGH-3** — Fire `/trace-deps chain:STAMP_CFG_AUTOPOPULATE` + bake result into Step 1.6.5 (1 vs 2 calls survive)
4. **HIGH-4** — Reorder Pre-coding triggers to make Decision E triage BEFORE Stage 2 DRAFT land + BEFORE pre-coding tag
5. **LOW-5** — Swap struct names at L66 + L218 (StampInferenceCfgInputs ↔ ModelStampResult inversion)

**At coding time** (MED severity):
- MED-1: Verify 4 thompson POST_CFG entries deletion scope (enumerate 9 vs 5 deletions)
- MED-2: `/test-strength-audit` Step 8 confirms STRENGTHEN semantic
- MED-4: Specify `MAX_SUPPORTED_STAMP_FORMAT_VERSION = 2` constant + ordering
- MED-5: Cite `FAILURE_MASK_cfg_inference_drift` origin file:line
- MED-6: Verify `tools/check_metadata_bit_to_derived_filter_coverage.py` existence

**At ship close** (DOC severity):
- DOC-1/DOC-2/DOC-3: Cross-references + version syntax precision

---

## Audit verdict

**YELLOW** — Plan body is structurally sound; canonical sister discipline (Check 29) + design space discipline (Check 30) shapes COMPLETE; 8/8 LOAD-BEARING TECH_DEBT-09X items have concrete homes with build-forcing closure mechanism; 15/15 line refs verified at HEAD `9b62a72`; cold-pickup viable.

4 HIGH findings warrant v1.2 → v1.3 amendment BEFORE pre-coding tag (~30-45 min planning revision). 6 MED findings handled at coding time. NO CRIT findings.

**Greenlight conditions for pre-coding tag:**
1. HIGH-1/HIGH-2/HIGH-3/HIGH-4 amendments land in v1.3
2. LOW-5 struct-name inversion corrected in v1.3
3. Operator Decision E triage completed (E.1/E.2/E.3 selected)
4. `framework-reason-buffer-extension.md` Stage 2 DRAFT lands on disk
5. Other Pre-coding triggers (#1-9) per plan body

---

**End of readiness audit v1.0** — 2026-05-17

**Triage recommendation:** v1.2 → v1.3 amendment cycle (~30-45 min) + operator Decision E triage; then pre-coding tag; then Steps 0-9. Effort ~12-18h focused per Decision E outcome.
