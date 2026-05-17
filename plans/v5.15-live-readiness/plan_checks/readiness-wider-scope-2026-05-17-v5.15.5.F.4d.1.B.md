# /readiness — wider-scope `.B` proposal — 2026-05-17

**Plan:** `v5.15.5.F.4d.1.B` migration + consumer + **wider scope** (DELETE `FOREACH_CFG_DERIVED_INFERENCE_CFG`; ADD canonical `FOREACH_CFG_GATE` + 3 consumer macros; migrate ALL consumers)
**Source plan body:** `subplans/2026-05-16-v5.15.5.F.4d.1.B-migration-consumer.md` v1.2
**Sidecar:** `subplans/2026-05-16-v5.15.5.F.4d.1.B-migration-consumer-examples.md` v1.1
**Batch 1 synthesis (RED accounting-audit; CRIT-1 = same-shape Path γ critique #2):** `plan_checks/2026-05-17-v5.15.5.F.4d.1.B-audit-synthesis.md`
**HEAD verified:** `39b9947` (`.A` ship local)

---

## Stage 0 — DESIGN_SPECS preload

Loaded per surface keywords:
- `autopopulate-pattern-for-production-caller-class.md` — **Stage 3 ACTIVE** (canonical AUTOPOPULATE family discipline; wider scope adds 3 sisters)
- `sidecar-override-pattern-for-registry-auto-flows.md` — v1.1 Stage 2 DRAFT (status corrected 2026-05-17; first canonical at `.C`)
- `metadata-bit-driven-derived-filter-framework.md` — v1.2 Path γ correction
- `framework-composition-overview.md` v1.1
- `structural-fix-preferred-decision-framework.md` (governing Path γ-class pivots)
- DESIGN_PHILOSOPHY § 1.5 framework-selection criteria + item 31 framework discipline

---

## Wider-scope deliverable inventory (verified at HEAD)

| Deliverable | HEAD anchor | Surface count |
|---|---|---|
| A. DELETE `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp` (13.3K, 167 lines, 14 rows across 5 cohorts) | exists; 11 walker/comment hits in tests + 1 in MetaRegistry.hpp + 4 in CfgFieldRegistry/ML_Headers | replaces 14 rows with 14 metadata-bit rows |
| B. NEW `MemHeaders/CfgGateRegistry.hpp` sparse sidecar `FOREACH_CFG_GATE(X)` | NEW file ~100 LOC | 1 file |
| C1. `STAMP_CFG_POPULATE_FROM_DERIVED(inf, cfg)` macro | sister to existing `STAMP_CFG_AUTOPOPULATE` at `StampBoundCfgRegistry.hpp:226` | NEW macro |
| C2. `DRIFT_CHECK_AUTOPOPULATE(failure_flags, handle, cfg, drift_count)` macro | replaces β4 dispatch + Step 8 `CFG_DRIFT_AUTOPOPULATE` | NEW macro |
| C3. `INFERENCE_CFG_POPULATE_FROM_DERIVED(inf, cfg)` macro | replaces `INFERENCE_CFG_AUTOPOPULATE` at `CfgDerivedInferenceCfgRegistry.hpp:148` | NEW macro |
| D. Migrate existing `INFERENCE_CFG_AUTOPOPULATE` consumer | `ML_Headers/StampHelper.hpp:183` (single call site) | 1 site |
| E1. 4 ModelInference.hpp walker sites | `:1199, :1401, :1643, :1788` | 4 sites |
| E2. ~25 test-side references | `tests/controller_test.cpp` (rg count = 25 `FOREACH_STAMP_BOUND_CFG_COUNT|FOREACH_STAMP_BOUND_CFG\b`) | 25 sites |
| E3. StampHelper.hpp:156 `STAMP_CFG_AUTOPOPULATE` call | exists at line 156 | 1 site |
| F. All `.B` v1.2 scope | 24-row cohort + ML_CFG_FLAG sig + Winsor + gap_acceptable + legacy empty-out | ~30 sites |

**Surface total:** ~70 file/line touches across ~20 files. Wide-blast-radius migration.

---

## Checklist verdicts

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | PASS | Boot-time + slow-path drift check only |
| 2 | Train↔serve parity | **GAP** | Wider scope DELETES the production stamp populate sister registry. `STAMP_CFG_POPULATE_FROM_DERIVED` MUST land atomic with deletion or PARITY-020 reopens (synthesis CRIT-2 already flagged this for minimal scope) |
| 3 | Surface area | **GAP** | ~70 touches across ~20 files; > 8 file ceiling violated wide. Mid-flight tag granularity is the saving grace |
| 4 | Pointer init / heap | PASS | No allocator changes |
| 5 | Backward compat | **GAP** | Canonical body row order changes under framework walker (CRIT-6 unresolved); stamp_format_version decision required |
| 6 | Multi-threading | PASS | No new thread/atomic/lock |
| 7 | Test coverage | FIXED | ~30 new tests at minimal; wider scope adds ~10-15 more for canonical-sister extensions + 14-row migration row-by-row; **25 controller_test sites need fixture migration** (current count, verified by rg) |
| 8 | Docs + invariants | **GAP** | 2 new DESIGN_SPECS needed Stage 2 DRAFT (cfg-derived-consumer-framework + cfg-field-classification-taxonomy) BEFORE coding; existing 4 specs need v1.2/v1.3 updates |
| 9 | Forward maintenance | FIXED | Wider scope IMPROVES this — canonical extension means future cohorts = 1 row in `FOREACH_CFG_GATE` + 1 bit on source row vs 2 rows (current parallel registry pattern) |
| 10 | Rollback story | FIXED | Mid-flight tags per Step preserved; phase decomposition (below) gives ~8 rollback anchors |

### Cold-pickup C.1-C.10

| # | Field | Verdict |
|---|---|---|
| C.1 | Branch state | PASS (stays on `feat/v5.15-live-readiness`) |
| C.2 | Phase execution order | **GAP** (Step 12 ordering wrong — empty-out before consumer migration would break compilation; same issue as minimal-scope CRIT-3) |
| C.3 | Step 0 concrete move | PASS |
| C.4 | Function/macro names cited | **GAP** (3 NEW consumer macros not yet draft-implemented at sidecar level; sidecar v1.1 still shows β4 SUPERSEDED shape) |
| C.5 | File:line refs | PASS (synthesis enumerates all 4 ModelInference.hpp sites + StampHelper.hpp:156,:183) |
| C.6 | Stale-claim audit | **GAP** (synthesis already flagged ~6 stale references; wider scope adds more — Step 11 β4 dispatch entirely DELETED) |
| C.7 | Effort claims reconcile | DEFERRED (see Effort realism below) |
| C.8 | Source-audit refs | PASS |
| C.9 | Predecessor/dependent named | PASS |
| C.10 | Tag names locked | FIXED (mid-flight tags renamed per Phase decomp below) |

### Drift audit

- **Feature drift:** PASS (no fingerprint contributors change)
- **Format drift:** **DRIFT-RISK** — canonical body row order changes; stamp_format_version decision pending (Synthesis CRIT-6)
- **Threshold drift:** PASS
- **Path drift:** PASS (no file rename)
- **Tick-source drift:** PASS
- **Build-flag drift:** PASS
- **Label drift:** PASS
- **Metric drift:** PASS

---

## Effort realism: **REALISTIC** at 15-20h focused for wider scope

Breakdown:
- Minimal `.B` v1.2 baseline (after CRIT amendments): ~10-14h
- DELETE `CfgDerivedInferenceCfgRegistry.hpp` + ADD `CfgGateRegistry.hpp`: ~2-3h (canonical-sister pattern application; the registry shape already lives in head 1:1)
- 3 NEW consumer macros (mechanical sisters to existing AUTOPOPULATE): ~1-2h
- Migrate existing 1 INFERENCE_CFG_AUTOPOPULATE consumer + 4 ModelInference.hpp walker sites + StampHelper.hpp:156: ~2-3h
- 25 controller_test.cpp fixture migrations: ~2-3h
- DESIGN_SPECS Stage 2 DRAFT (2 new + 4 amendments): ~1-2h

**Subtotal: 18-27h.** Upper bound (~27h) is unrealistic if all amendments converge; lower bound (~18h) realistic if Phases are run sequentially with mid-flight tags.

**Effort verdict: REALISTIC at 18-22h; recommend 22h budget with split.**

---

## Risk classification: **MED-HIGH**

Comparison to `.F.4d` ship close (wide-blast-radius MED, ~3174 tests in play):
- `.F.4d`: ~6 files added/modified, single-day, MED.
- **Wider `.B`: ~70 touches across ~20 files, multi-session, MED-HIGH** — qualitatively wider blast radius than `.F.4d` because it includes TEST FIXTURE MIGRATION (25 sites — a class which `.F.4d` did not touch).

**Verdict: MED-HIGH** (vs minimal `.B` MED). The +1 risk tier driver is the 25-site test fixture sweep + 14-row canonical registry DELETE (rare action category).

---

## Suggested Phase decomposition (numbered 0-9)

| Phase | Deliverable | Effort | Tag suffix |
|---|---|---|---|
| **0** | Pre-coding verify + DESIGN_SPECS Stage 2 DRAFTs (cfg-derived-consumer-framework.md + cfg-field-classification-taxonomy.md) + 4 spec amendments + `pre-v5.15.5.F.4d.1.B` rollback tag | 1-2h | `pre-...` |
| **1** | NEW `CfgGateRegistry.hpp` + 14-row mirror of canonical registry shape with placeholder `FIELD_IDX` references (legacy registry stays during transition) | 2-3h | `step1-gate-registry` |
| **2** | 3 NEW consumer macros (`STAMP_CFG_POPULATE_FROM_DERIVED` + `DRIFT_CHECK_AUTOPOPULATE` + `INFERENCE_CFG_POPULATE_FROM_DERIVED`) — full sister-to-AUTOPOPULATE shape | 1-2h | `step2-consumer-macros` |
| **3** | `tt::cfg_emit_synthetic_field<T>` (Step 1 from v1.2) + `tt::cfg_emit_field<T>` production split per synthesis HIGH-B | 1h | `step3-tt-emit` |
| **4** | ML_CFG_FLAG 5→6 sig + bitmap walker activation + Step 4 22-row clean migration + Step 5 gap_acceptable_threshold migration + Step 6 pre-canonical parity gaps + Step 7 `.A.7` retroactive cohort | 4-5h | `step4-cohort-migration` |
| **5** | Winsor parse-time validation (synthesis CRIT-4 amendment: leverage WARN_ON_CLAMP) | 30min | `step5-winsor` |
| **6** | Migrate `INFERENCE_CFG_AUTOPOPULATE` consumer at `StampHelper.hpp:183` to `INFERENCE_CFG_POPULATE_FROM_DERIVED` + Active consumer sites (`CoreModelZoo.hpp:225-247`, `StampHelper.hpp:150`, `ConfidenceScore.hpp:729`) + migrate `STAMP_CFG_AUTOPOPULATE` at `StampHelper.hpp:156` to `STAMP_CFG_POPULATE_FROM_DERIVED` | 2-3h | `step6-consumer-migration` |
| **7** | 4 ModelInference.hpp walker sites (`:1199, :1401, :1643, :1788`) migration | 1-2h | `step7-modelinference` |
| **8** | 25 controller_test.cpp test fixture migrations + ~8 comment text updates | 2-3h | `step8-fixture-migration` |
| **9** | Legacy `FOREACH_STAMP_BOUND_CFG` empty-out + DELETE `CfgDerivedInferenceCfgRegistry.hpp` + FOREACH_REGISTRY 2-row removal + tests + ship close | 2h | `step9-empty-out` + `v5.15.5.F.4d.1.B` |

**Phase count:** 10 (0-9) per "aim for 6-10". Each Phase has a mid-flight tag for rollback granularity.

---

## Sub-ship split recommendation: **SPLIT into `.B.1` + `.B.2` + `.B.3`**

**Rationale:** 18-22h crosses the 20h sub-ship guideline. Three-way split per operator-proposed boundaries:

### `.B.1` — Framework consolidation (~6-8h)
- Phase 0 (pre-coding + Stage 2 DRAFTs + rollback)
- Phase 1 (NEW `CfgGateRegistry.hpp` + 14-row mirror)
- Phase 2 (3 NEW consumer macros)
- Phase 3 (`tt::cfg_emit_synthetic_field<T>` + production split)
- Phase 6.1 (migrate `INFERENCE_CFG_AUTOPOPULATE` consumer + `STAMP_CFG_AUTOPOPULATE`)
- Phase 7 (4 ModelInference.hpp walker sites — but only WALKER replacement; cohort migration deferred to `.B.2`)
- Ship `.B.1` — framework + consumer-macro infrastructure lands; LEGACY `CfgDerivedInferenceCfgRegistry.hpp` + `FOREACH_STAMP_BOUND_CFG` STAY (parallel registries during transition; both walked; consumers go through new macros routing to new sidecar but old registry still exists for safety)
- Tag `v5.15.5.F.4d.1.B.1`

### `.B.2` — Cohort migration (~6-8h)
- Phase 4 (24-row cohort + ML_CFG_FLAG sig + bitmap walker + parity gaps + `.A.7` retroactive)
- Phase 5 (Winsor parse-time validation)
- Phase 6.2 (Active consumer site migrations CoreModelZoo / ConfidenceScore / StampHelper:150)
- Ship `.B.2` — 24-row migration through framework lands; legacy registries STILL alive for byte-equivalence verification
- Tag `v5.15.5.F.4d.1.B.2`

### `.B.3` — Legacy empty-out + test sweep (~4-6h)
- Phase 8 (25 controller_test.cpp fixture migrations + comment text updates)
- Phase 9 (Legacy `FOREACH_STAMP_BOUND_CFG` empty-out + DELETE `CfgDerivedInferenceCfgRegistry.hpp` + 2-row FOREACH_REGISTRY removal)
- Ship `.B.3` — legacy registries gone; final architectural state
- Tag `v5.15.5.F.4d.1.B.3`

**Split benefits:**
1. Each sub-ship < 8h (operator can complete in a single focused session)
2. `.B.1` ships framework BEFORE any cohort migration — defensive ordering; if anything breaks in framework, doesn't compromise cohort migration in-flight
3. `.B.3` is the high-stakes irreversible step (deletes registries); preceded by 2 working ships where legacy is still alive
4. Test fixture migration (25 sites) gets a focused ship — historically THE highest-risk substep per `.F.4c.3` precedent

**Split costs:**
1. 3 version bumps + 3 postmortems + 3 ship rituals (~1-2h overhead vs monolithic)
2. Slight inconvenience: `.B.1` ships a transient parallel-registry state (intentional safety; ~7-10 days max in this state)

**Per `feedback_overengineering_boundary_when_future_easier`:** Split is the more future-oriented choice — each split-ship is a cleaner rollback anchor + `.B.1` builds a tested framework before exercising it widely.

---

## Categorical applicability + cohort eligibility

- `gap_acceptable_threshold` migration (synthesis CRIT-5): MUST set `applies_to_strategy_cat=STRAT_CAT_ML`, `applies_to_op_mode_cat=OP_MODE_CAT_ALL`, `applies_to_regime_cat=REGIME_CAT_ALL`, `applies_to_risk_cat=RISK_CAT_ALL`, `lives_in_struct=STRUCT_CFG`
- 5 cohorts already identified in Step 11 β4 / Step 11 wider-scope `FOREACH_CFG_GATE`: Bandit/Thompson, Risk-Degradation, Ridge-Any, Composite-Confidence, Default (Winsor merges into Default via parse-time validation)
- Cohort eligibility per `cfg-flag-eligibility-criteria.md` § Cohort audit: 5 cohorts all eligible (≥2 siblings each)

---

## TECH_DEBT auto-write expectations

Wider scope generates these TECH_DEBT entries:
- TECH_DEBT-091: deferred byte-equivalence canary test (pull v5.14 fixture forward from `.D` OR add minimal canary) — Synthesis MED-B
- TECH_DEBT-092: stamp_format_version decision audit cadence (canonical body row order change CRIT-6)
- TECH_DEBT-093: extraction of additional sister registry-fields if `/merge-scan` Batch 2 surfaces more parallel registries (deferred; not in `.B.1/.B.2/.B.3` scope)
- TECH_DEBT-094: `FOREACH_CFG_GATE` should evolve to absorb override semantics from `.C` `FOREACH_DRIFT_OVERRIDE` (per-concern unification opportunity; defer to `.F.4f` or later)

---

## DESIGN_SPECS pre-coding requirement

**MUST land Stage 2 DRAFT BEFORE Phase 1 starts:**
1. `cfg-derived-consumer-framework.md` (NEW) — codifies the 3-macro AUTOPOPULATE family + `FOREACH_CFG_GATE` sidecar parent pattern; Stage 2 DRAFT pre-`.B.1`, Stage 3 ACTIVE at `.B.1` ship close
2. `cfg-field-classification-taxonomy.md` (NEW) — codifies STAMP_BOUND vs STAMP_BOUND_CFG_DERIVED vs AFFECTS_STAMP_PARITY vs gate-only classifications; needed because `gap_acceptable_threshold` semantic ambiguity (Synthesis CRIT-5) demands a documented taxonomy

**4 v1.2/v1.3 amendments:**
3. `autopopulate-pattern-for-production-caller-class.md` — add 3 new sister applications + cross-ref to new `cfg-derived-consumer-framework.md`
4. `metadata-bit-driven-derived-filter-framework.md` v1.2 → v1.3 — note STAMP_BOUND_CFG_DERIVED first canonical at `.B.1`
5. `sidecar-override-pattern-for-registry-auto-flows.md` v1.1 → v1.2 — note `FOREACH_CFG_GATE` as 2nd canonical at `.B.1` (sister to `FOREACH_DRIFT_OVERRIDE` at `.C`)
6. `framework-composition-overview.md` v1.1 → v1.2 — add wider-scope row to composition matrix

**Effort:** ~1-2h drafting + ~30 min cross-reading at Phase 0.

---

## Verdict: **YELLOW to refine — but committable after refinements**

**Top-line:** The wider-scope proposal is structurally sound + future-oriented (eliminates the canonical registry that is the SAME PATH γ-SHAPE β4 reinvents per Synthesis CRIT-1). Wider scope:
- Closes Path γ-class structural critique #2 same way `.A` closed #1
- Eliminates a 14-row parallel registry instead of building a 5-cohort sidecar that mechanicalizes the wrong shape
- Aligns with "registries optimize for ADDING; principle + sweep for ELIMINATING" rule (set 2026-05-15)
- Auto-derives the 5th BANDIT_THOMPSON field (`thompson_exp3_blend_alpha`) that β4 plan body MISSED — direct evidence of duplication-induced drift

**YELLOW because before commit:**
1. **Confirm SPLIT into `.B.1/.B.2/.B.3`** (operator decision; recommended above) OR keep monolithic (then revise effort to 22h ceiling)
2. **Resolve CRIT-6 stamp_format_version decision** (canonical body row order change under framework walker) — operator decision
3. **Stage 2 DRAFT 2 new DESIGN_SPECS + amend 4 existing** before Phase 1 starts
4. **Plan body v1.3 amendments** per Synthesis 15-item list (CRIT-1 dissolves β4; ADD `STAMP_CFG_POPULATE_FROM_DERIVED`; enumerate 4 ModelInference sites + 25 test fixture sites; reframe `gap_acceptable_threshold` as migration; reformulate Winsor; sequence Step 9 last; split `tt::` synthetic vs production)
5. **Surface CRIT-6 operator decision** before drafting v1.3

**GREEN once:** SPLIT decision made + CRIT-6 resolved + plan body v1.3 lands + DESIGN_SPECS Stage 2 DRAFTs land.

**Time-to-GREEN:** ~3-4h of planning work (1-2h DESIGN_SPECS + 1-2h plan body v1.3 + brief operator consult on SPLIT + CRIT-6).

---

## Cross-references
- Synthesis CRIT-1 (β4 → canonical pivot): `plan_checks/2026-05-17-v5.15.5.F.4d.1.B-audit-synthesis.md` lines 30-46
- Canonical registry at HEAD: `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101-123`
- Existing AUTOPOPULATE siblings: `StampBoundCfgRegistry.hpp:226` (`STAMP_CFG_AUTOPOPULATE`), `CfgDerivedInferenceCfgRegistry.hpp:148` (`INFERENCE_CFG_AUTOPOPULATE`)
- Consumer at HEAD: `StampHelper.hpp:156, :183`
- Walker sites at HEAD: `ModelInference.hpp:1199, :1401, :1643, :1788`
- Test sites at HEAD: 25 matches `FOREACH_STAMP_BOUND_CFG_COUNT|FOREACH_STAMP_BOUND_CFG\b` in `tests/controller_test.cpp`

---

**End of readiness wider-scope report.**
