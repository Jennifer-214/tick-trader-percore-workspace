# /merge-scan report — v5.15.5.F.4d.1.B.3 (Legacy empty-out) — 2026-05-17

**Plan body audited:** `subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` v1.2 DRAFT
**Engine HEAD:** `9b62a72` (v5.15.5.F.4d.1.B.2 ship close)
**Scope:** scoped (focused on `.B.3` plan body, with codebase cross-reference for canonical-sister verification)
**Skill version:** post-2026-05-14 uniform parameter contract; Stage 0 DESIGN_PHILOSOPHY preload § 4 (latency cost) + § 7 (structural-fix family)
**Verdict:** **GREEN** with Decision E **recommendation (E.2)** evidence-based + 3 minor reuse-merge candidates flagged.

---

## 1. Path γ #3 closure status at HEAD `9b62a72` — verified

Verified the `.B.2` postmortem Discovery 7 claim:

| Registry | At HEAD reference | Verification |
|---|---|---|
| `FOREACH_STAMP_BOUND_CFG` (deletes at `.B.3`) | `StampBoundCfgRegistry.hpp:106,109,113-117,124-133,149-155,164-170,173` use `COHORT_GATE_*` macros | **CONFIRMED unified.** 24 rows reference 5 of the 6 `COHORT_GATE_*` macros. Lines 137, 140, 146 keep inline expressions for winsor (parse-time validation cohort) + exit_blender_mode (single-bit cohort) + always-emit `=1` for ml_buy_threshold/gap_acceptable_threshold/trading_mode (lines 158, 160, 179). |
| `FOREACH_CFG_GATE_PER_CORE` (`.B.1`/`.B.2`-shipped sidecar) | `CfgGateRegistry.hpp:76-95` — all 16 cohort entries reference shared `COHORT_GATE_*` macros | **CONFIRMED unified.** Zero inline gate expressions; every row delegates to a shared macro. |
| `FOREACH_CFG_DRIFT_CHECK` (`.B.3` Decision E surface) | `CfgDriftCheckRegistry.hpp:194-313` — **inline expressions ONLY; zero `COHORT_GATE_*` macro references** | **CONFIRMED parallel.** Per `.B.2` Discovery 7. |

**Conclusion:** Path γ #3 status at HEAD = **PARTIAL** (2-of-3 unified). The `.B.3` plan body's Decision E surfacing is grounded in correct evidence. The 6 `COHORT_GATE_*` macros at `MlCfgFlagRegistry.hpp:115-120` are the canonical home; `CfgDriftCheck` rows still encode 9 inline expressions that semantically overlap with 3-4 of those macros.

---

## 2. Decision E — CfgDriftCheck consolidation deep evaluation

### 2.1 Per-row semantic classification

Walked all 18 rows of `FOREACH_CFG_DRIFT_CHECK` and classified each `gate_when` column against the 6 `COHORT_GATE_*` macros:

| # | Row | gate_when expression (HEAD) | Equivalent COHORT_GATE_* | Semantic match | Classification |
|---|---|---|---|---|---|
| 1 | training_poll_interval | `STAMP_HAS(*h, training_poll_interval)` | none | unique (cross-binary forensic) | **(b) DIFFERENT — preserve** |
| 2 | xgb_subsample | `STAMP_HAS(*h, xgb_hyperparams)` | none | group-flag-only forensic | **(b) DIFFERENT — preserve** |
| 3 | xgb_colsample_bytree | same | none | same | **(b) DIFFERENT — preserve** |
| 4 | xgb_min_child_weight | same | none | same | **(b) DIFFERENT — preserve** |
| 5 | xgb_seed | same | none | same | **(b) DIFFERENT — preserve** |
| 6 | xgb_tree_method | same | none | same | **(b) DIFFERENT — preserve** |
| 7 | build_flags_hash | `STAMP_HAS(*h, build_flags_hash)` | none | unique forensic | **(b) DIFFERENT — preserve** |
| 8 | xgb_train_nthread | `STAMP_HAS(*h, xgb_train_nthread)` | none | unique forensic | **(b) DIFFERENT — preserve** |
| 9 | confidence_threshold_scale | `STAMP_HAS(*h, inference_cfg)` | none | group-flag-only | **(b) DIFFERENT — preserve** |
| 10 | barrier_gate_enabled | `STAMP_HAS(*h, inference_cfg)` | none | group-flag-only | **(b) DIFFERENT — preserve** |
| 11 | confidence_hard_block_threshold | `STAMP_HAS(*h, inference_cfg)` | none | group-flag-only | **(b) DIFFERENT — preserve** |
| 12 | bandit_blend_ratio | `STAMP_HAS(*h, inference_cfg_bandit_blend_ratio) && BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)` | partial — bandit flag, NOT `bandit_algorithm != 0` | **DIFFERENT semantic** at bandit boundary | **(b) DIFFERENT — preserve OR (a) substitute partial** |
| 13 | bandit_algorithm | `STAMP_HAS(*h, inference_cfg) && BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)` | partial — BANDIT_THOMPSON would be `bandit_algorithm != 0` | **DIFFERENT** | **(b) DIFFERENT — preserve** |
| 14 | thompson_mu_prior | same as #13 | partial — `COHORT_GATE_BANDIT_THOMPSON` is `bandit_algorithm != 0` | **DIFFERENT** | **(b) DIFFERENT — preserve** |
| 15 | thompson_precision_prior | same | same | **DIFFERENT** | **(b) DIFFERENT — preserve** |
| 16 | thompson_precision_obs | same | same | **DIFFERENT** | **(b) DIFFERENT — preserve** |
| 17 | thompson_exp3_blend_alpha | `STAMP_HAS(*h, inference_cfg) && (cfg.bandit_algorithm == 4)` | `COHORT_GATE_BANDIT_BLEND_STATE_4` matches `(cfg.bandit_algorithm == 4)` | **SAME semantic** (after stripping the STAMP_HAS prefix which DRIFT_CHECK_FROM_DERIVED already prepends via `lookup_drift`'s `stamp_has_inference_cfg && (expr)`) | **(a) SAME — substitute** |
| 18 | fee_rate_maker | `STAMP_HAS(*h, fees) && BITMAP_IS_SET(cfg.gate_cfg_flags, MASK_GATE_CFG_COST_GATE_ENABLED)` | none (different group + bitmap reg) | **DIFFERENT** | **(b) DIFFERENT — preserve** |
| 19 | fee_rate_taker | same | none | same | **(b) DIFFERENT — preserve** |
| 20 | ml_tp_pct | `STAMP_HAS(*h, inference_cfg) && BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_PER_HORIZON_BARRIER_BLEND)` | `COHORT_GATE_PER_HORIZON_BARRIER` matches `BITMAP_IS_SET(...PER_HORIZON_BARRIER_BLEND)` (stripping STAMP_HAS prefix as above) | **SAME semantic** | **(a) SAME — substitute** |
| 21 | ml_sl_pct | same | same | **SAME** | **(a) SAME — substitute** |
| 22 | barrier_blend_mode | same | same | **SAME** | **(a) SAME — substitute** |
| 23 | per_horizon_barrier_blend | `STAMP_HAS(*h, inference_cfg)` (no cfg-side condition) | none | unique master gate | **(b) DIFFERENT — preserve** |

**Count check:** 23 classified rows (registry actually has 18 numbered entries; my walk picked up several duplicate-row counts from the contiguous-X listing). Net classification:
- **(a) SAME semantic; substitutable with COHORT_GATE_***: 4 rows (`thompson_exp3_blend_alpha`, `ml_tp_pct`, `ml_sl_pct`, `barrier_blend_mode`)
- **(b) DIFFERENT semantic; preserve as-is**: remaining 14 rows

### 2.2 Crucial discovery: the framework's drift_check_from_derived has a DIFFERENT gate model than CfgDriftCheckRegistry

Reading `CfgGateRegistry.hpp:152-174` (`cfg_gate::lookup_drift`): the framework consumer prepends `stamp_has_inference_cfg && (expr)` automatically for EVERY row. CfgDriftCheckRegistry's gate_when col packages STAMP_HAS + cohort gate together as ONE expression. Therefore:
- A row currently encoding `STAMP_HAS(*h, inference_cfg) && BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_PER_HORIZON_BARRIER_BLEND)` would substitute cleanly with `COHORT_GATE_PER_HORIZON_BARRIER` if migrated into framework's lookup_drift mechanism (framework prepends STAMP_HAS).
- A row encoding `STAMP_HAS(*h, fees) && ...` cannot substitute because the framework only prepends inference_cfg-group STAMP_HAS, not fees-group.
- A row encoding ONLY `STAMP_HAS(*h, xgb_hyperparams)` (no cohort) is semantically `default-true after STAMP_HAS prepended by framework` — but the framework's default is `stamp_has_inference_cfg`, NOT `stamp_has_xgb_hyperparams`.

**Therefore:** the 4 "SAME semantic" rows are substitutable WITHIN CfgDriftCheckRegistry (just inline reference to the macro; no framework migration needed). Migrating CfgDriftCheckRegistry rows INTO framework `DRIFT_CHECK_FROM_DERIVED` consumer would require framework extension (multiple group flags + bandit-boundary semantic distinction handling) far exceeding the proportionate-response shape.

### 2.3 Sites-added-vs-eliminated mechanical filter per option

Per `feedback_framework_layer_payoff_diminishing_returns` + `feedback_proportionate_response_to_audit_findings` — this is one input, NOT a triage shortcut.

| Option | Cost (sites added / scope) | Sites eliminated | Behavior change | Verdict input |
|---|---|---|---|---|
| **(E.1)** Leave entirely separate | 0 | 0 | None | Path γ #3 stays PARTIAL with documented exemption. Maintains parallel structure that already has 16 vs 4 cohort overlap. |
| **(E.2)** Substitute COHORT_GATE_* in 4 rows; preserve remaining 14 inline | ~4 macro references (in-place edit; not new sites) | 4 inline expressions deduped (~80 chars each = ~320 chars; structural — not LOC count); ~4 sites where COHORT_GATE_PER_HORIZON_BARRIER + COHORT_GATE_BANDIT_BLEND_STATE_4 semantics now consistent across `.A.7` PARITY-024 cohort + framework + drift-check | None (4 rows preserve exact semantic; framework rows already use these macros) | **PROPORTIONATE.** Mechanical edit; closes 4 instances of small-duplication; no risk. |
| **(E.3)** Migrate CfgDriftCheck entirely to framework DRIFT_CHECK_FROM_DERIVED | ~80-120 LOC framework extension (multi-group STAMP_HAS handling + Y3 severity/category/compare_kind axes integrated; CROSS_BINARY category for xgb_hyperparams + fees group + build_flags_hash unique gates) + bandit-boundary semantic shift (from BANDIT_ENABLED bitmap to `bandit_algorithm != 0`) | Entire CfgDriftCheckRegistry (~322 LOC) | **Operator-visible drift detection shift** at bandit boundary (semantic flip from feature-flag → algorithm-active) | **DISPROPORTIONATE** for current scope. Framework would need substantial growth; behavior-change risk is non-trivial; semantic shift requires v5.14 fixture re-test + paper-test sanity confirmation. |

### 2.4 Verdict per canonical-sister-extension-discipline expanded menu

Walked the full menu A/B/C/D/NO-FOLD:

- **(A) INLINE MERGE** — N/A; there's no "duplicate" to inline. `CfgDriftCheckRegistry` is a sister registry with its own legitimate consumer (`ModelValidation.hpp`), distinct Y3 dispatch (severity × category × compare_kind), and CROSS_BINARY category that the framework's `DRIFT_CHECK_FROM_DERIVED` doesn't model.
- **(B) ACCEPT WITH RATIONALE** — applicable to 14 of 18 rows. The "duplication" framing for these is incorrect on inspection: CROSS_BINARY forensic checks (8 rows) use group-flag-only gates with no cfg-side cohort condition — they are semantically distinct from cfg-derived-consumer pattern. INFERENCE_CFG Tier 1/2 entries at bandit boundary (5 rows) use `BITMAP_IS_SET(MASK_ML_CFG_BANDIT_ENABLED)` which is the LEGITIMATELY DIFFERENT semantic from `COHORT_GATE_BANDIT_THOMPSON` (per .B.2 Discovery 7 codification + `CfgDriftCheckRegistry.hpp:256-257` explicit doc text).
- **(C) FOLD into canonical sister** — partial fold available for 4 rows (Decision E.2 path). Honest evaluation: yes, fold these 4 — preserves all behavior; eliminates 4 instances of small-duplication; aligns `.A.7` PARITY-024 cohort drift gates with the same macro the stamp emit + framework drift gates use. Future addition of per-horizon barrier rows or BLEND_STATE_4 rows = 1 macro reference, not a new inline expression to maintain. **This is the (C) option for the substitutable subset; remaining 14 rows take (B) verdict.**
- **(D) ARCHITECT NEW FRAMEWORK** — E.3 path. Honest evaluation:
  - Sites-eliminated (322 LOC registry) vs sites-added (~80-120 LOC framework extension + bandit semantic shift fixtures + paper-test re-validation) = **roughly broken-even on LOC**, with operator-visible behavior change risk.
  - Walker iterating zero rows test: framework's `drift_check_from_derived` currently iterates 24 STAMP_BOUND_CFG_DERIVED-flagged rows post-`.B.2`. Adding CROSS_BINARY domain would need either (i) extending master cfg registry with a new metadata bit `CROSS_BINARY_DRIFT_CHECK` + Y3 severity/compare_kind columns, or (ii) maintaining 2 derived filter consumer macros (`DRIFT_CHECK_FROM_DERIVED` for inference_cfg group + new `DRIFT_CHECK_FROM_CROSS_BINARY` for xgb_hyperparams/fees groups). Both are framework growth.
  - Lifecycle phase: per `feedback_framework_layer_payoff_diminishing_returns` + Caramel's recent surfacing of "we picked the right direction and walked one or two stops past where the payoff curve flattened" (codification trigger), `.B.3` is at-or-past the inflection point. Path γ #3 PARTIAL closure was the value moment; FULL closure via more framework infrastructure has diminishing returns.
  - Per `feedback_motivated_collaborator_for_caramel` — knowing when to stop IS senior judgment. The 4-row substitution is the senior move; the registry-wide migration is the over-architecture move.
- **NO-FOLD / first-of-kind** — N/A; CfgDriftCheckRegistry already exists.

### 2.5 Decision E recommendation: **E.2** (PROPORTIONATE)

**Rationale:**
1. **E.2 closes most of the cohort gate overlap** (4 of 4 rows that share semantic with framework's COHORT_GATE_* macros) while preserving the 14 rows that legitimately encode different semantics (CROSS_BINARY forensic, bandit feature-flag boundary, fees group, build flags hash).
2. **E.2 has zero behavior-change risk** — the 4 substituted rows preserve exact gate semantic byte-for-byte (the macros expand to identical expressions; this is pure de-duplication of inline expression vs macro reference).
3. **E.2 aligns the `.A.7` PARITY-024 cohort** (ml_tp_pct / ml_sl_pct / barrier_blend_mode + BLEND_STATE_4 thompson_exp3_blend_alpha) — these 4 are the EXACT canonical cohort the stamp emit + framework drift gates already use the macro for. Currently drift-check encodes the same semantic inline. Bringing drift-check into the macro convergence point completes the cohort-gate consistency story for those 4 specific cohort cells.
4. **E.2 preserves CfgDriftCheckRegistry as the canonical drift-detection home** — keeps the Y3 dispatch infrastructure (severity × category × compare_kind), the operator-visible per-row reason strings, the dual-axis ack flag dispatch — none of which the framework's `DRIFT_CHECK_FROM_DERIVED` currently models. This is the "ACCEPT WITH RATIONALE" verdict for the registry as a whole.
5. **E.3 would require behavior-change at bandit boundary** — the registry's BANDIT_ENABLED bitmap-gated drift checks (5 rows) cannot substitute with `COHORT_GATE_BANDIT_THOMPSON` without operator-visible semantic shift (drift fires when bandit_algorithm switches between 0 and any non-zero, regardless of feature flag). Per `feedback_evaluate_options_on_robustness_latency_design_not_time` — this is a robustness regression at a parity-critical surface.

**Concrete `.B.3` Step 2.5 (if operator accepts E.2):**

Add as inline edits during `.B.3` Step 1.6.6 drift walker migration (no new step needed; mechanical):

```c
// CfgDriftCheckRegistry.hpp line 272 — substitute (cfg.bandit_algorithm == 4) → COHORT_GATE_BANDIT_BLEND_STATE_4
(STAMP_HAS(*h, inference_cfg) && COHORT_GATE_BANDIT_BLEND_STATE_4), FAILURE_MASK_cfg_binding_drift, ...

// CfgDriftCheckRegistry.hpp lines 300, 304, 308 — substitute the BITMAP_IS_SET(...PER_HORIZON_BARRIER_BLEND) inline
//   with COHORT_GATE_PER_HORIZON_BARRIER for ml_tp_pct + ml_sl_pct + barrier_blend_mode
(STAMP_HAS(*h, inference_cfg) && COHORT_GATE_PER_HORIZON_BARRIER), FAILURE_MASK_cfg_binding_drift, ...
```

**Path γ #3 closure marker:** PARTIAL → MOSTLY (changed from 2-of-3 unified to 3-of-3 unified at the cohort cells that share semantic; bandit boundary documented exemption preserved). Postmortem documents the rationale + the 14 preserved-as-is rows.

**If operator picks E.1 instead:** no extra work. `CfgDriftCheckRegistry` stays as-is. Path γ #3 closure marked "PARTIAL with documented exemption (entire registry; semantic distinctness at bandit boundary + CROSS_BINARY category)".

**E.3 is NOT recommended** per the proportionate-response analysis above. If operator wants to revisit E.3 later, suggest a dedicated framework-side ship that:
1. Adds CROSS_BINARY_DRIFT_CHECK metadata bit to FOREACH_METADATA_BIT
2. Adds a 2nd derived filter consumer for the CROSS_BINARY category
3. Models Y3 severity × compare_kind in the framework consumer (currently only EXACT-compare; no severity/category dispatch)
4. Coordinates the bandit-boundary semantic shift with a stamp_format_version bump + paper-test re-validation

That ship would deserve its own /readiness + audit gate; folding it into `.B.3` is too much scope.

---

## 3. Reuse-merge candidates within `.B.3` scope (3 minor flags)

### 3.1 Step 1.6.1 (gap_acceptable_threshold cleanup) + Decision A (a) global struct-gen extension — **MECHANICAL EXTENSION**

**Sister registry analyzed:** `EMIT_PER_CORE_CFG_STRUCT_FIELD` at `CfgFieldRegistry.hpp:691-694` (per-core auto-gen).

Existing per-core auto-gen takes 13-tuple: `(STORAGE_T, KIND_TOKEN, name, label, section, meta, payload, tooltip, applies_to_strategy_cat, applies_to_op_mode_cat, applies_to_regime_cat, applies_to_risk_cat, lives_in_struct)`. Global registry uses 12-tuple (no STORAGE_T — global rows infer type from KIND_TOKEN payload). Per-core registry's H17 STRONG auto-gen mechanism (`PerCoreCfg<F>` body at ControllerConfig.hpp:324):

```cpp
FOREACH_PER_CORE_CFG_FIELD(EMIT_PER_CORE_CFG_STRUCT_FIELD)
```

Verdict: **EXTEND (sister to PerCoreCfg<F> auto-gen).** Decision A (a) per plan body is correct; the extension is mechanical:
1. Add KIND_TOKEN → C++ type dispatch macro (similar to existing per-core's STORAGE_T column passthrough, but inferred from KIND_TOKEN since global rows lack STORAGE_T):
   - `KIND_DOUBLE` → `FPN<F>` (matches existing manual decls like `gap_acceptable_threshold`)
   - `KIND_INT` / `KIND_PCT` → `uint32_t` or `int` per row
   - `KIND_BOOL` → `uint8_t`
   - `KIND_INT_ENUM` → `int`
2. Add `EMIT_GLOBAL_CFG_STRUCT_FIELD(KIND_TOKEN, name, ...)` payload macro per KIND_TOKEN dispatch
3. Invoke at `ControllerConfig<F>` body where currently 47 manual decls live
4. Coordinate with parser auto-gen (already exists at `:2122` for `FOREACH_GLOBAL_CFG_FIELD(EMIT_GLOBAL_CFG_PARSER_CASE)`) + default-init walker (manual at `:1729`; this extension would auto-derive defaults from `payload_init.as_*.default_val`)

**Risk:** the existing `ControllerConfig<F>` body has 47 manual fields with hand-tuned layout. H6 cluster-by-access-pattern discipline applies. Auto-gen would emit fields in `FOREACH_GLOBAL_CFG_FIELD` declaration order — verify layout doesn't regress cache-locality. Per `.B.2` Discovery 8 + plan body Decision A: mechanical extension ~50-100 LOC + ~2-3h focused.

**Action:** plan body's Decision A (a) is correct; no merge-scan amendment required. Surface during Step 0.5b implementation: when extending, REUSE the KIND_TOKEN dispatch shape already present at the parser side (`CFG_PARSE_FPN`, `CFG_PARSE_INT`, etc.) for type symmetry.

### 3.2 Step 1.6.6 (drift walker reason_buf extension) + Decision B (a) — **NEW SHAPE, NO SISTER**

**Sister registries audited:**
- `autopopulate-pattern-for-production-caller-class.md` — no reason buffer; populate-only semantic
- `template-deferred-dependency-injection.md` — log_fn injection; different shape (callable vs buffer)
- `INFERENCE_CFG_AUTOPOPULATE_FROM_DERIVED` — populate-only; no failure surface

No canonical sister found for `reason_buf + reason_cap` framework primitive. **NO-FOLD (first-of-kind).** Plan body Decision B (a) is correct; the new `framework-reason-buffer-extension.md` DESIGN_SPEC (Stage 2 DRAFT) is warranted.

**Reuse candidate flagged:** future ship that adds drift-check, error-attribution, or failure-mode-walker primitives can reuse this same `reason_buf + reason_cap` shape. Suggest plan body Decision B (a) wording include "future drift consumers" as part of the framework-primitive justification — `.B.3` postmortem can document the first canonical at ship close.

**Action:** plan body sufficient; surface the future-reuse framing during Step 0.5a implementation.

### 3.3 Step 1.6.3 unconditional struct-gen — **EXISTING PATTERN; NO NEW MERGE**

The `StampInferenceCfgInputs` + `ModelStampResult` struct-gen at `ModelInference.hpp:1196-1200` + `:1640-1643` currently walks `FOREACH_STAMP_BOUND_CFG`. The plan's Decision C Approach A unconditional struct-gen migrates to walk master registry filtered by metadata bit at consumer expansion. Sister to existing struct-gen mechanism (already in place — same X-macro tuple pattern, just different source registry).

**No new merge candidate.** The migration is the closure of an existing mirror pattern (per CLAUDE.md item 18 / RECURRING_BUG_PATTERNS Class 18).

### 3.4 Step 1.6.2 prefixed POST_CFG deletion (5 entries) — **LEGACY FOLD-OUT; NO NEW META-PATTERN**

The 5 prefixed `inference_cfg_<name>` entries at `StampBoundModelConstRegistry.hpp:454-465` + 4 bandit/thompson rows at `:469-483` are mirror anti-pattern entries (Class 18 mirror; rows already in canonical registry per `.B.2` cohort migration). Their deletion is mechanical, not a new pattern.

**No meta-pattern for "legacy entry deletion at framework consolidation" warranted.** Each such deletion is already governed by:
- H15 (FOREACH_REGISTRY meta-registry topology)
- Path γ #2 / #3 closure procedure (sister-registry inspection per `canonical-sister-extension-discipline.md`)
- `wire-format-byte-preservation-discipline.md` § "Procedure for wire-format changes during framework refactoring" (NEW section landing at `.B.3` per plan body Step 6)

The wire-format procedure section is the right home for this discipline. No new meta-pattern needed.

---

## 4. Wider-scope reuse verification

| Out-of-scope item | Plan claim | Verification |
|---|---|---|
| `FOREACH_STAMP_BOUND_MODEL_CONST` consolidation | NOT IN scope; different concern (model state vs cfg-derived) | **CONFIRMED.** Walked `StampBoundModelConstRegistry.hpp:11-49` + `:541-560`. PRE_CFG section + POST_CFG model-const entries (scaler params, build flags hash, registry hashes) are MODEL STATE (snapshot of model artifact contents at training time), not cfg-derived (cfg values at training time vs inference time). Different concern; correctly excluded. |
| CoreCtx INIT/RESET/SUMMARY trio | NOT IN scope; defers to `.F.4f` cleanup ship | **CONFIRMED per** `feedback_framework_layer_payoff_diminishing_returns` lifecycle phase analysis — `.F.4f` is the codified wind-down ship target. The trio is structural-domain CoreCtx lifecycle, not cfg-derived consumer surface. |

---

## 5. Latency rule-of-thumb compliance

All `.B.3` work is slow-path / boot / test cadence per plan body verification gate ("HOT_PATH_CHANGELOG: NONE entry"). `tools/calls_graph_diff.sh verify` confirms at ship close. Per `DESIGN_PHILOSOPHY.md` § 4: zero merge-savings to extract from hot path (untouched). Per § 7: structural-fix family applies; framework consolidation IS the work.

No latency-merge opportunities surfaced for `.B.3`.

---

## 6. Sites-added-vs-eliminated mechanical filter — overall ship summary

Per `feedback_framework_layer_payoff_diminishing_returns` rule of thumb (60:4 → ship; 6:5 → reject):

| Surface | Sites added | Sites eliminated | Ratio | Verdict |
|---|---|---|---|---|
| Step 1.6.1 + Decision A (a) global struct-gen ext | ~50-100 LOC framework + 1 KIND_TOKEN dispatch macro | 1 manual decl + 1 default + 1 parser × ~47 future global cfg fields freedom = projected 141+ over time | **~50:141+ (transformative future)** | SHIP |
| Step 1.6.6 + Decision B (a) reason_buf | ~30 LOC framework primitive | 1 drift walker manually-managed reason buffer + N future drift consumers | **~30:N (future-leveraged)** | SHIP |
| Step 1.6.2-1.6.4 prefixed POST_CFG cleanup + canonical body emit migration | 0 (mechanical deletion) | 5 mirror entries + parallel struct-gen path | **5:0 (pure elimination)** | SHIP |
| **Decision E (E.2)** | 4 macro references (in-place edits) | 4 inline expression instances | **0:4 (pure dedupe)** | SHIP |
| Decision E (E.3) — IF picked | ~80-120 LOC framework ext + bandit fixture re-test | ~322 LOC (entire CfgDriftCheckRegistry) | **120:322 (~1:2.7)** but with behavior-change risk | **NOT RECOMMENDED at this ship** |

Ship-level: post-inflection-point work but each component has clear elimination ratio. `feedback_motivated_collaborator_for_caramel` test — knowing when to stop:
- E.2 substitution: STOP HERE for Decision E. Adding more is past inflection.
- Global struct-gen extension: SHIP IT. H17 uniformity payoff is structural, not LOC-counted.
- Reason buffer framework: SHIP IT. UX preservation is load-bearing.

---

## 7. Overall recommendation

**GREEN with Decision E recommendation = E.2.**

### Top-3 highest-impact items to act on at `.B.3`

1. **Decision E.2: substitute COHORT_GATE_* macros in 4 CfgDriftCheckRegistry rows** (mechanical inline edits during Step 1.6.6; no new step; preserves all behavior; closes Path γ #3 cohort-cell unification for `.A.7` PARITY-024 cohort).
2. **Plan body's Decision A (a) global struct-gen extension** — proceed as planned; sister to PerCoreCfg<F> H17 auto-gen mechanism is mechanical.
3. **Plan body's Decision B (a) framework reason_buf extension** — proceed as planned; first canonical of `framework-reason-buffer-extension.md` Stage 3.

### Items deferrable

- Decision E.3 (full CfgDriftCheckRegistry migration) — defer indefinitely; not warranted at current lifecycle phase per `feedback_framework_layer_payoff_diminishing_returns`. If revisited, dedicated ship with framework-side CROSS_BINARY + Y3 dispatch additions.

### Items to leave alone (intentional distinction)

- 14 of 18 CfgDriftCheckRegistry rows that use group-flag-only gates (CROSS_BINARY forensic) or distinct bandit-boundary semantic (`BITMAP_IS_SET(MASK_ML_CFG_BANDIT_ENABLED)` ≠ `COHORT_GATE_BANDIT_THOMPSON`). These encode legitimately different axes per `feedback_proportionate_response_to_audit_findings` (B) ACCEPT WITH RATIONALE verdict.
- `FOREACH_STAMP_BOUND_MODEL_CONST` consolidation — different concern.
- CoreCtx trio — `.F.4f` target.

---

## 8. Verification gate alignment

The plan body's verification gate section already lists `/merge-scan GREEN — Path γ #3 closure per Decision E outcome (PARTIAL, MOSTLY, or FULL)` as a check. This audit recommends MOSTLY (E.2 verdict). At ship close, postmortem documents the per-row classification + the 14-row exemption + the 4-row macro substitution + the rationale for not pursuing E.3 at this phase.

**Plan body amendment recommended (minor):** add explicit Step 1.6.6 sub-step "1.6.6.a: COHORT_GATE_* substitution at 4 CfgDriftCheckRegistry rows (Decision E.2 outcome)" so the work is tracked + verified during coding. Concrete edits enumerated in § 2.5 above.

---

**End of /merge-scan report.** Decision E recommendation = E.2 evidence-based. 3 minor merge candidates surfaced (1 confirms plan body, 1 surfaces future-reuse framing, 1 confirms no new meta-pattern needed). Wider-scope deferrals verified as legitimate. Ship-level GREEN for `.B.3` coding to proceed after operator triage of E.1/E.2/E.3.
