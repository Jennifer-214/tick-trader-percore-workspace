---
type: audit-report
audit: blindspot-scan
scope: .D.1 plan body v0.3 (doc-sweep adapted)
target_ship: v5.15.5.F.4d.1.D.1
cycle: 2
date: 2026-05-28
plan_body: plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.D.1-doc-system-end-goal-language-sweep.md
plan_version_audited: v0.3 (frontmatter + footer aligned)
skill: /blindspot-scan
sister_audits: [/readiness cycle 2, /trace-deps cycle 2]
predecessor: D.1-blindspot-scan-cycle1.md (v0.2 audit; 12 findings → 7 implementation-detail blindspots actionable)
---

# /blindspot-scan cycle 2 against .D.1 plan body v0.3

## Verdict

**GREEN-with-1-MED** — v0.3 closes the cycle-1 implementation-detail blindspot space to high satisfaction. 7 of 7 cycle-1 blindspot findings (H-1 / M-1..M-4 / L-1 / L-5) close PASS; 1 cycle-1 INFO finding (B19 codification) closes PASS via Phase H.10. Cycle 2 surfaces TWO NEW blindspots — one MED-severity (B19/B14 boundary ambiguity surfaces design question about whether two pillars should merge) and one LOW (workspace-side rollback asymmetry not explicitly documented in plan body Phase A.0 narrative). Convergence trajectory is clean: cycle-1 surfaced 7 actionable blindspots; cycle 2 surfaces 2 NEW (smaller, narrower, more specific). Per `feedback_iteration_spiral_signals_audit_meta_gap`: this is convergent, not divergent — META-gap signal NOT present.

## Cycle 1 closure verification

| Cycle 1 finding | Severity | v0.3 closure | Verification |
|---|---|---|---|
| **H-1** Plan body self-test bootstrap classification ambiguity (CUSTOM-5) | HIGH | **PASS** | `transition-documentation` class added at line 221 (matrix) + line 250 (tool detection rule) + line 753 (verification gate). Class recognizes "X was per-core; is now per-node" / "per-NODE sharded (was per-core in pre-`.E`)" patterns. Per operator directive, plan body uses NEW terminology dominantly + cites OLD only in transition context — makes rename self-documenting. **HIGH closure.** |
| **M-1** Cross-doc transitive terminology drift (CUSTOM-1) | MED | **PASS** | Phase H.4.1 added at line 623-632. Semantic-context spot-check methodology codified: operator manually spot-checks top-5 high-impact docs for transitive semantic drift; output appended to TSV as `transitive-semantic-drift` finding for operator triage. Time-box ~30 min. **MED closure.** |
| **M-2** Glossary scope-boundary undefined (CUSTOM-2) | MED | **PASS** | Phase B.0 preamble added at lines 317-318. Explicit scope note: "This Glossary is DEPLOYMENT/ARCHITECTURE level only — Cluster/Node/Deployment/ExecutionCore/threading/economic/build artifacts/version flags. Runtime-level primitives (seqlock/SPSC/BG_Evaluate/FPN/tt:: etc.) intentionally OUT; belong in DOCS/GLOSSARY.md (NEW at `.E.2`)." Boundary-stable. **MED closure.** |
| **M-3** Pre-drafted content currency (CUSTOM-3) | MED | **PASS** | Phase H.4.2 currency registry added at line 634-648. 7-row registry enumerates every pre-drafted block + propagation target + owner. Rule: "When any pre-drafted block changes mid-cycle: bump plan body version (v0.3 → v0.4) + update propagation targets in same edit." **MED closure.** |
| **M-4** Sister-tool cohort completeness (CUSTOM-4) | MED | **PASS** | Phase A.7 added at lines 292-311 with 8-row sister-tool table. Includes `check_per_core_registry_integrity.py` rename queued for `.E.1` + 7 internal-logic updates at `.E.1`. Running-list entry added (verified at `rename-candidates-running-list.md:44` entry #10). Forward promise to `.E.1` documented. **MED closure.** |
| **L-1** Plan body footer v0.1 drift (B1 dogfood) | LOW | **PASS** | Footer at line 914 reads "End of `.D.1` plan body v0.3." (matches frontmatter `plan_version: v0.3`). No drift. |
| **L-2** Check 44 defense-in-depth gaps (CUSTOM-6) | LOW | PARTIAL | R5 mitigation block updated (Severity downgraded to LOW with H1 closure rationale), but the specific "developer bypasses all 3 gates" residual-risk acknowledgment isn't explicitly worded. Acceptable per L2's own "as long as documented as residual risk" recommendation — defense-in-depth structure is described. |
| **L-3** Pre-tag rollback semantics for non-code surfaces (CUSTOM-7) | LOW | **NOT-CLOSED** | Phase A.0 at lines 240-242 still ONLY says `git tag -s pre-...` without the workspace-side asymmetry note. This is the carried-over finding (also noted in fresh-eyes #6 below). |
| **L-4** Tool TSV output operator-burden | LOW | PARTIAL | Tool design at A.1 includes confidence column (HIGH/MED/LOW) but no explicit SUMMARY-first ergonomic affordance. Acceptable as cycle-2 P2. |
| **L-5** /readiness Check 44/45 numbering | LOW | **PASS** | All references use Check 44 (verified at lines 61, 509, 513, 521, 645, 723, 755). Last-landed Check is 43 per SKILL.md verification at lines 618-619. Numbering is consistent. **LOW closure.** |
| **N1** engine_arch reframing as DELETED | INFO/CORRECTION | **PASS** | Site classification matrix at line 190 reframes `engine_arch` as DELETED at `.B.4`. WITHDRAWN from TECH_DEBT queue at line 677 (strikethrough). Verified zero `engine_arch` hits in current `CoreFrameworks/` + `Strategies/` (confirmed by `grep -rn 'engine_arch'`). |
| **B19 pillar codification** (cycle 1 INFO) | INFO | **PASS** | Phase H.10 added at lines 681-705. B19 pillar Stage 2 DRAFT codified with 7 sub-categories. Sister cross-ref to B14 (multi-surface deletion ordering — sister-pillar at deletion class vs B19 sister-pillar at terminology-sweep class). Stage 3 first canonical = this ship itself. |

**Closure summary:** 8 PASS / 2 PARTIAL / 1 NOT-CLOSED (L-3). Acceptance bar reached for v0.3.

## Cycle 2 fresh-eyes blindspots

### NEW-1 — Phase A.7 sister-tool cohort completeness (MED-LOW)

Phase A.7 lists 8 tools but the actual workspace `tools/` directory contains 23 entries. Verified inventory at `/home/caramel/code/FoxML_Trader_v2/tools/`:

**In A.7 table (8):** `check_per_core_registry_integrity.py`, `check_meta_registry.py`, `check_forward_promise_audit.py`, `check_plan_body_symbol_existence.py`, `check_doc_metadata.py`, `check_field_name_uniqueness.py`, `check_struct_field_uniqueness.py`, `check_storage_t_coverage.py`

**MISSING from A.7 table (verified extant):**
- `tools/install-git-hooks.sh` — hook-installer; if `tools/hooks/pre-commit` body amended at `.D.1`, install-hooks references need verification + corresponding `tools/hooks/pre-commit` source-of-truth currency
- `tools/hooks/pre-commit` — VERSIONED hook source (separate from `.git/hooks/pre-commit` which is local-install). Plan body A.3 says "Extend `.git/hooks/pre-commit`" but should ALSO update `tools/hooks/pre-commit` (the versioned source) for new contributor install symmetry. NOT mentioned. Operator install discipline could drift.
- `tools/calls_graph_diff.sh` + `tools/calls_graph_diff_baseline.txt` + `tools/calls_graph_diff_v5.8_phase0_baseline.txt` — call-graph baselines; baselines reference per-core function names; at `.E.1` rename these baselines must regenerate. Could be auto-handled at `.E.1` ship-close `/ship`, but worth flagging as cohort.
- `tools/gen_code_map.sh` — code-map generator; may reference per-core terminology
- `tools/rebuild_doc_indexes.py` — operator-facing index rebuild; checks doc frontmatter; may need awareness of glossary anchor
- `tools/scan_class_27_full.py` + `tools/subdivide_design_specs.py` — domain-specific tools; verify per-core narrative not embedded
- ML tooling (`chart.py`, `feature_overlay.py`, `compare_scalers.cpp`, `compare_scalers.sh`, `validate_feature_mask.sh`) — `.E.2` ML-CLI scope; not `.D.1` scope, but cohort completeness check matters

**Recommendation (not blocking):** Amend A.7 table to add `tools/hooks/pre-commit` (source-of-truth versioned hook; sister-cohort to `.git/hooks/pre-commit` edit) + `tools/install-git-hooks.sh` (cohort verifier). Other tools (call-graph baselines, gen_code_map.sh, rebuild_doc_indexes.py) deferred to `.E.1` cohort enumeration is acceptable, BUT explicit deferral note in A.7 would close the cohort-undercounting blindspot.

### NEW-2 — B19/B14 pillar boundary ambiguity (LOW-INFO)

Phase H.10 codifies B19 with 7 sub-categories. Plan body line 700 states: "Sister: Pillar B14 (multi-surface deletion ordering) — sister-pillar at deletion-class; B19 is sister-pillar at terminology-sweep class."

**Potential boundary issue:** B14 covers "multi-surface deletion ordering" (deletion class). B19 sub-cat 1 covers "doc-sweep classification correctness" (narrative vs code-citation vs historical vs transition-documentation; misclassification risks docs↔code divergence or orphan terminology). These overlap conceptually:

- B14: ordering of deletion sites across multiple files (cfg-field-row LAST per H17)
- B19 sub-cat 1: classification of sites (RENAME vs LEAVE vs DELETE-CANDIDATE)

The sub-cat 7 (workspace-side rollback asymmetry) also reads more like a META-discipline than a sweep-specific pillar — could apply to ANY ship where workspace state lands before engine-side commit.

**Recommendation (not blocking):** at B19 Stage 3 promotion (per `pattern-codification-lifecycle.md`, requires 2nd canonical), revisit boundary with B14 — possibly fold sub-cat 7 into separate META pillar OR explicitly delineate which sub-cats are "classification" (mirrors B14 site-enumeration) vs "drift detection" (semantic-context spot-check). Plan body acknowledges this is Stage 2 DRAFT (first canonical = `.D.1` itself); boundary refinement defers naturally.

### NEW-3 — Currency registry self-coverage gap (LOW)

Phase H.4.2 currency registry (line 634-648) enumerates 7 pre-drafted blocks. Verified inventory of pre-drafted content in plan body:

In registry: D-65 / D-66 entries / Template "Tests changed" section / Glossary content / Decoupling roadmap reframe / SKILL.md Check 44 amendment / Phase A.7 sister-tool cohort table.

**MISSING from registry (pre-drafted content NOT in registry):**
- Site classification matrix (lines 209-222) — IS this pre-drafted? It IS canonical for the tool to implement. If matrix changes mid-cycle (e.g., new classification class), tool spec changes; should propagate to tool unit-test fixtures (A.2 + A.5). Currently NOT in registry.
- Token inventory order-of-magnitude estimates (lines 178-198) — IS pre-drafted; matrix says actual counts come from tool baseline at A.4. Not in registry; not a blocker.
- TECH_DEBT entry text (line 675-679) — IS pre-drafted; auto-write at ship close per ledger contract. Not in registry; ledger auto-write captures the discipline.
- B19 pillar Stage 2 DRAFT body (lines 686-703) — IS pre-drafted; lands at H.10. Not in registry.

**Recommendation (not blocking):** Phase H.4.2 currency registry could add Site classification matrix + B19 pillar Stage 2 DRAFT body as additional rows. Trivial amendment if cycle 3 catches a matrix-rule edit; otherwise residual.

### NEW-4 — Other cfg fields cited as vestigial but actually-deleted (LOW)

Cycle 1 N1 corrected `engine_arch` (DELETED at `.B.4`; not vestigial). Cycle 2 systematic verification of remaining "vestigial" claims:

**Verified state via `grep -rn '<field>' CoreFrameworks/`:**

| Field | Plan body claim | Actual state | Verdict |
|---|---|---|---|
| `engine_mode` | Vestigial post-`.E.0.1`; queue deletion | 20+ live citations in CoreFrameworks/ + active in CfgFieldRegistry.hpp:393 (KIND_INT row; HAS_SIDE_EFFECT \| IS_BOOT_ONLY); ENGINE_MODE_SHARDED constant in ControllerConfig.hpp:1834; live parse path at ControllerConfig.hpp:2785-2788 | **VESTIGIAL CLAIM ACCURATE** — `engine_mode` is currently active per-fleet operating mode (sharded vs single_core legacy); will become vestigial post-`.E.0.1` LIVE single_core deprecation, then deletion at `.E.0.1`/`.E.1`. Plan body wording correct. |
| `engine_arch` | DELETED at `.B.4` (N1 correction) | Zero hits in CoreFrameworks/ + Strategies/ + engine.cfg | **DELETION VERIFIED** — N1 closure accurate. |
| `BacktestSharded_Run` | Unification candidate at `.E.1` (rename to `Backtest_Run` direct) | 7 live citations in Backtest/ (definitions in BacktestSharded.hpp:105 + BacktestEngine.hpp:534; consumer wrapper at BacktestEngine.hpp:848) | **CLAIM ACCURATE** — `BacktestSharded_Run` exists as real fn; `Backtest_Run` (legacy) wraps it per `BacktestSharded.hpp:20`. Unification candidate at `.E.1` is correct framing. |

**Verdict:** No "phantom vestigial" claims discovered. Plan body cfg field claims accurate post-N1.

### NEW-5 — L-3 workspace-side rollback asymmetry NOT-CLOSED (LOW)

Verified cycle-1 finding L-3 carried-over: Phase A.0 (lines 240-242) shows:

```
**A.0** Create pre-tag rollback anchor (per L2 self-audit):
```bash
git tag -s pre-v5.15.5.F.4d.1.D.1 -m "rollback anchor before .D.1 doc sweep"
```
```

NO note about workspace-side asymmetry (memories + MEMORY.md + TaskList + audit-reports landed mid-cycle NOT reverted by engine-side pre-tag rollback). B19 sub-cat 7 covers it at the META level, but Phase A.0 narrative itself doesn't reference B19 sub-cat 7 or document the asymmetry.

**Recommendation (low priority):** add 1-line note to Phase A.0: "Pre-tag rollback anchor preserves ENGINE-side state only; workspace-side artifacts (memories, decision logs, audit reports landed mid-cycle) NOT reverted — operator manually triages workspace state if rollback needed. See B19 sub-cat 7."

### NEW-6 — transition-documentation regex robustness (LOW-INFO)

The classification rule at line 221 lists 5 example patterns:
- `per-core (renamed from .E.1)`
- `old: per-core → new: per-node`
- `per-core (now per-node)`
- `X was per-core; is now per-node`
- `per-NODE sharded (was per-core in pre-.E)`

**Potential false-positive surface:** patterns relying on `→` arrow OR "was X; is now Y" require literal substring match. Variations like:
- `per-core (→ per-node @ .E.1)` — slightly different syntax
- "the transition from per-core to per-node" — long-form narrative
- "per-core legacy vs per-node target" — comparison framing without explicit "old/new"

These COULD slip through detection; tool would mis-classify as `narrative-current-state` → RENAME, when operator intent was LEAVE. Mitigation = operator TSV review catches; per A.4 step.

**Recommendation (not blocking):** Phase A.2 testing should include 2-3 transition-documentation FIXTURES with intentional variation in arrow syntax to verify detection robustness. Otherwise tool risks false-rename on plan body itself OR docs that legitimately use varied transition wording.

## Per-pillar verdict (standard 12+B14+B15+B17+B18 + 7 doc-sweep CUSTOM)

| Pillar | Status | Notes |
|---|---|---|
| **Standard 12+** | | |
| B1-B8, B10-B12 | IRRELEVANT | No code-layer change (engine UNTOUCHED) |
| B9 — Unverified audit claim | N-A | All cited findings + sister memories verified to exist (per cycle 1 + cycle 2 systematic verification) |
| B13 — Cross-walker struct-field uniqueness | IRRELEVANT | No walker bodies |
| B14 — Multi-surface deletion ordering | N-A | Doc-sweep is RENAME, not DELETE; TECH_DEBT entries deferred to downstream ships per cycle 1 |
| B15 — Unconditionalization | IRRELEVANT | No cfg-gate removals |
| B17 — Forward-decl at global scope | IRRELEVANT | No header changes |
| B18 — Block-scope statics in lambda hoist | IRRELEVANT | No code hoisting |
| **Doc-sweep custom CUSTOM-1..CUSTOM-7 (B19 candidate)** | | |
| CUSTOM-1 transitive drift | **N-A** | Phase H.4.1 semantic spot-check landed; cycle 1 M-1 closed |
| CUSTOM-2 glossary scope | **N-A** | Phase B.0 preamble landed; cycle 1 M-2 closed |
| CUSTOM-3 pre-drafted currency | **SILENT-RISK (NEW-3)** | Phase H.4.2 registry landed but NEW-3 surfaces 4 additional pre-drafted blocks missing from registry; acceptable as cycle-2 residual |
| CUSTOM-4 sister-tool cohort | **SILENT-RISK (NEW-1)** | Phase A.7 8-tool table landed but NEW-1 surfaces `tools/hooks/pre-commit` (versioned source) + `install-git-hooks.sh` missing from cohort; acceptable residual |
| CUSTOM-5 self-test bootstrap | **N-A** | transition-documentation class landed; cycle 1 H-1 closed |
| CUSTOM-6 Check 44 defense-in-depth | N-A (PARTIAL) | R5 mitigation re-worded; residual-risk acknowledgment implicit |
| CUSTOM-7 rollback asymmetry | **SILENT-RISK (NEW-5)** | Phase A.0 narrative still lacks workspace-side rollback asymmetry note; B19 sub-cat 7 covers at META level but Phase A.0 cross-ref absent |

**Verdict summary:**
- IRRELEVANT: 16 pillars (standard 12+ mostly N-A for doc work)
- N-A: 6 pillars (cycle 1 closures all PASS; CUSTOM-1/2/5 + B9/B13/B14 etc.)
- SILENT-RISK: 3 pillars (NEW-1 + NEW-3 + NEW-5 — all LOW-MED severity; residuals acceptable)
- GUARDED-BY-BUILD: 0 (doc work)
- LOAD-BEARING-LOUD: 0

## Convergence assessment

- **Cycle 1 findings:** 12 total (H1 + M1-M9 + L1-L5 from operator self-audit; H-1 + M-1..M-4 + L-1..L-5 + I-1..I-3 from cycle 1 /blindspot-scan = 7 implementation-detail blindspots actionable)
- **Cycle 2 NEW findings:** 5 surfaced (NEW-1 MED-LOW + NEW-2 LOW-INFO + NEW-3 LOW + NEW-4 verification-pass + NEW-5 LOW carried-over + NEW-6 LOW-INFO)
- **Actionable cycle 2 NEW findings:** 3 (NEW-1 / NEW-3 / NEW-5); other 3 are INFO/verification

**Trajectory: CONVERGENT.** Cycle 1 surfaced 7 actionable; cycle 2 surfaced 3 actionable. Findings are narrower, more specific, lower-severity (no HIGH; 1 MED-LOW + 2 LOW). The "audit-meta-gap signal" per `feedback_iteration_spiral_signals_audit_meta_gap` is NOT present:

- NOT divergent (not surfacing same-shape findings at higher cadence)
- NOT new-shape (all 5 cycle-2 findings fit existing pillar taxonomy — CUSTOM-3 currency / CUSTOM-4 sister-tool / CUSTOM-7 rollback / META-boundary B19/B14 boundary refinement)
- IS smaller-finding-set (3 vs 7 actionable)
- IS more-specific (per-line citations vs broad-class)

**Cycle 3 NOT recommended.** Residual NEW-1/NEW-3/NEW-5 amendments are inline-merge-easy (~15 min total) OR accept-with-rationale.

## Recommended next move

**(X) Inline merge** NEW-1 (Phase A.7 table extension — add `tools/hooks/pre-commit` + `install-git-hooks.sh` rows). **~5 min**.

**(X) Inline merge** NEW-5 (Phase A.0 1-line workspace-side rollback asymmetry note). **~2 min**.

**(Y) Accept-with-rationale** NEW-3 (currency registry self-coverage gap; site classification matrix + B19 pillar body NOT in registry). Acceptable residual; trivial if cycle 3 ever surfaces matrix-rule edit. **0 min**.

**(Y) Accept-with-rationale** NEW-2 (B19/B14 boundary). Stage 2 DRAFT codification per Phase H.10 explicitly defers boundary refinement to Stage 3 first canonical (2nd doc-sweep ship). Acceptable. **0 min**.

**(Y) Accept-with-rationale** NEW-6 (transition-documentation regex robustness). Phase A.2 testing recommendation; not blocking; covered by operator TSV review at A.4. **0 min**.

**Total cycle 2 → v0.4 effort: ~7 min.** OR skip amendments + accept all NEW as residuals; proceed to Phase A.0 coding.

## Inflection check

Per `feedback_iteration_spiral_signals_audit_meta_gap`:
- **Iteration count:** v0.1 (operator self-audit) → v0.2 (operator self-audit) → v0.3 (cycle 1 audit cohort: readiness + trace-deps + blindspot-scan) → potential v0.4 (cycle 2). 3 amendment cycles, 4 if v0.4 lands.
- **Finding shape:** convergent — NEW-1/NEW-3/NEW-5 fit existing CUSTOM-4 / CUSTOM-3 / CUSTOM-7 categories already codified. Not new pillar shape.
- **Recommendation:** B19 Stage 2 DRAFT codification at Phase H.10 captures all 7 sub-categories. If `.D.2` follow-on emerges, B19 Stage 3 promotion candidate. NO new META pillar codification needed at cycle 2.

## Cross-references

- Plan body: `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.D.1-doc-system-end-goal-language-sweep.md` (v0.3; 914 lines)
- Predecessor audit: `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/plan_checks/E.0-audit-reports/D.1-blindspot-scan-cycle1.md`
- Sister cycle 2 audits: `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/plan_checks/E.0-audit-reports/D.1-readiness-cycle2.md` + `D.1-trace-deps-cycle2.md` (pending)
- B19 pillar Stage 2 DRAFT body: plan body lines 686-703 (Phase H.10)
- Verified pre-commit hook source: `/home/caramel/code/FoxML_Trader_v2/.git/hooks/pre-commit` (B-Plus + Check 11 blocks; pattern reference for Phase A.6 + Check 44 invocation)
- Versioned hook source: `/home/caramel/code/FoxML_Trader_v2/tools/hooks/pre-commit` (sister to `.git/hooks/pre-commit`; flagged in NEW-1)
- Hook installer: `/home/caramel/code/FoxML_Trader_v2/tools/install-git-hooks.sh` (flagged in NEW-1)
- Implementation-detail blindspot taxonomy (target of B19 amendment): `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md`

---

**End of /blindspot-scan cycle 2 report. Verdict GREEN-with-1-MED — convergent trajectory; cycle 3 NOT recommended; operator triages NEW-1/NEW-3/NEW-5 inline-merge OR accept-as-residual before Phase A.0 coding.**
