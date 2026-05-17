# v5.15-live-readiness sprint — roadmap to paper-test session

**Updated:** 2026-05-17 (after `.B` audit cycle 1+2+3 + `.B.1` v1.1 planning + ML refactor decision to fold into v5.15)
**Sprint:** `v5.15-live-readiness`
**Status:** mid-sprint; framework consolidation phase in flight
**Current ship:** `v5.15.5.F.4d.1.B.1` (framework consolidation; coding started 2026-05-17 at Step 0.5)

---

## Sprint goal

Reach **paper-test session** — operator window to exercise the engine with all framework + Settings panel + tooltip + live-readiness gates in place. Bug testing happens against a STRUCTURALLY SOUND codebase, not a half-cleaned one. Per Caramel's professionalization-phase mandate (`user_mvp_to_professional_transition`).

---

## Phases overview

| Phase | Ships | Effort | Risk | Status |
|---|---|---|---|---|
| **A. Framework consolidation (current)** | `.F.4d.1.B.1` + `.B.2` + `.B.3` + `.C` + `.D` | ~18-25h focused | MED | `.B.1` in flight; `.A` SHIPPED 2026-05-17 |
| **B. Framework validation + cleanup** | `.F.4e` + `.F.4f` | ~3-4 days | LOW-MED | queued |
| **C. ML-side refactor (FOLDED INTO v5.15)** | `.F.5.A` + `.F.5.B` + `.F.5.C` | ~5-8 days | MED-HIGH | queued; scope TBD by audit |
| **D. Operational + safety** | `v5.15.6.A` + `v5.15.6.B` | ~2-3 days | MED | queued |
| **E. PAPER-TEST SESSION** | (operator window) | session | n/a | post-`v5.15` umbrella close |

**Total ~13-19 days focused** from `.B.1` start to paper-test entry.

---

## Phase A — Framework consolidation (CURRENT)

Cfg-derived consumer framework structural close. Eliminates parallel-registry-drift bug class for cfg-derived behavior.

### `.F.4d.1.A` (SHIPPED 2026-05-17)
- Path γ+ v2 framework infra: 1-row FOREACH_METADATA_BIT addition (STAMP_BOUND_CFG_DERIVED bit 13) + CoreFrameworks/StampBoundDerivedFilter.hpp consumer + tests/wire_format_invariants.hpp helper + CFG_COMPOSE_AUDIT_DECISIONS audit registry + H16 static_assert + cli_explain_mask fix + stamp_emit_mask delete + 22 new test sections
- Engine commit `39b9947` + GPG-signed tag `v5.15.5.F.4d.1.A` (pushed to engine remote)
- 3196/0 tests + 5 binaries clean + CI checks PASS

### `.F.4d.1.B.1` (IN FLIGHT)
- Framework consolidation: NEW MemHeaders/CfgGateRegistry.hpp canonical sparse sidecar + 3 derived-filter consumer macros (INFERENCE_CFG_POPULATE_FROM_DERIVED + STAMP_CFG_POPULATE_FROM_DERIVED + DRIFT_CHECK_FROM_DERIVED) + 5 new helper functions + 2 NEW DESIGN_SPECs Stage 3 first reference + 4 amended DESIGN_SPECs
- Walker iterates 0 rows at this ship (cohort migration at `.B.2` populates)
- ~6-8h focused; MED risk
- Pre-coding tag `pre-v5.15.5.F.4d.1.B.1` created 2026-05-17
- Plan body v1.1 at subplans/2026-05-17-v5.15.5.F.4d.1.B.1-framework-consolidation.md

### `.F.4d.1.B.2` (QUEUED)
- Cohort migration: 24-row → STAMP_BOUND_CFG_DERIVED bit + FOREACH_ML_CFG_FLAG 5→6 sig + 2 pre-canonical parity gaps + 4 retroactive `.A.7` cohort + gap_acceptable_threshold migration + Winsor parse-time validation + 4 ModelInference walker site migrations + StampHelper.hpp:156 migration
- CRIT-6 canonical body byte order DECISION lands here
- ~6-8h focused; MED-HIGH risk
- Skeleton at subplans/2026-05-17-v5.15.5.F.4d.1.B.2-cohort-migration.md; full draft after `.B.1` ships

### `.F.4d.1.B.3` (QUEUED)
- Legacy empty-out: DELETE FOREACH_CFG_DERIVED_INFERENCE_CFG + FOREACH_STAMP_BOUND_CFG + 14 controller_test.cpp count-assertion migrations + CI Checks 9-12 + v5.14 stamp fixture regression + DESIGN_SPECS spec-body cleanup
- ~4-6h focused; MED risk
- Skeleton at subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md

### `.F.4d.1.C` (QUEUED)
- Sidecar override + bit-packed inventory: FOREACH_DRIFT_OVERRIDE sparse sidecar + DriftOverride + RegistryRosterEntry + ManualFieldInventoryEntry (multi-bit-state-encoding canonicals 6/7/8)
- Sister to `.B.1`'s FOREACH_CFG_GATE — gate-type vs severity-type sidecar
- ~3-5h focused; LOW-MED risk
- STUB at subplans/2026-05-16-v5.15.5.F.4d.1.C-sidecar-bitpacked.md

### `.F.4d.1.D` (QUEUED)
- CI verification + fixture regression: CI Checks 9-12 (cohort eligibility + STAMP_BOUND_CFG_DERIVED coverage) + v5.14 stamp fixture regression test (HMAC byte preservation)
- ~2-4h focused; LOW risk

**→ `.F.4d.1` umbrella close**

---

## Phase B — Framework validation + cleanup

### `.F.4e` (QUEUED)
- KIND_STRING + KIND_FILE_PATH support + 5 GUI metadata derived filter applications via framework (HIDDEN_BY_DEFAULT, RESTART_REQUIRED, SAFETY_CRITICAL, IS_SECRET, DEPRECATED) + cfg.example auto-gen + cross-cutting metadata doc + reverse-drift CI
- **Validates the framework via 5 real second-source applications** — proves the pattern works on actual concerns
- LOW-MED risk
- STAGE 2 DRAFT in CLAUDE.local.md sprint state

### `.F.4f` (QUEUED)
- Cleanup ship — TECH_DEBT-076-080 closures:
  - TECH_DEBT-076 (WIP2d-1.B.2/B.3/B.4 ControllerEventLoop+EngineSharded+Backtest wrapper migrations; ~4-6h)
  - TECH_DEBT-077 (WIP2e A2 bitmap-bool migration; ~3-4h)
  - TECH_DEBT-078 (WIP2f legacy deletion; ~2-3h)
  - TECH_DEBT-079 (WIP2g/h atomic flag-day; ~6-10h)
  - TECH_DEBT-080 ([core N] section parser; ~2-3h)
  - Plus: HAS_SIDE_EFFECT 38-site cleanup (dust H1); CoreCtx INIT/RESET/SUMMARY trio consolidation (anti-spaghetti HIGH-1)
- ~2-3 days focused; MED risk
- STUB at subplans/2026-05-16-v5.15.5.F.4f-cleanup-tech-debt-076-080.md

**→ At `.F.4f` close: fire `/anti-spaghetti` codebase-wide audit on ML/ + GUI/ + Backtest/ + DataStream/ surfaces to size Phase C ship count.**

---

## Phase C — ML-side refactor (NEW: folded into v5.15 per 2026-05-17 decision)

Decision rationale: ML refactor is similar work to framework consolidation; tooling + discipline + skill suite is fresh; doing it now is cheaper than later (cold pickup expensive). Caramel mandate 2026-05-17.

### `.F.5.A` ML framework parity (TBD scope)
- Apply cfg-derived-consumer-framework + canonical-sister-extension-discipline to ML surfaces
- Likely: backend-side framework parity (training cfg ↔ engine cfg ↔ stamp parity)
- Audit-driven scope: `/anti-spaghetti` finds parallel-registry candidates in ML/
- Effort estimate TBD; placeholder ~2-3 days

### `.F.5.B` GUI live↔backtest unification (TBD scope)
- Decouple GUI from runtime per `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`
- ImGui panels + cfg mirror discipline + thread isolation (per H3 + thread-isolation rule)
- Unify Settings panel + tooltip + live-readiness gates across live + backtest paths
- Effort estimate TBD; placeholder ~2-3 days

### `.F.5.C` Training harness 1:1 with live execution (TBD scope)
- parity_harness.cpp expansion to cover train→serve identity across full ML pipeline
- Ensure model retrain reproduces engine inference bit-for-bit
- Effort estimate TBD; placeholder ~1-2 days

**→ `.F.5` umbrella close → `.F` umbrella close**

**Critical:** sub-ship count + sequencing in Phase C TBD by audit cycle at `.F.4f` close. May expand to `.F.5.A/.B/.C/.D` if audit surfaces additional parallel-infrastructure candidates. May contract if scope is bounded. Plan body drafts for `.F.5.X` happen at audit cycle.

---

## Phase D — Operational + safety

Direct operator-facing safety items per CLAUDE.local.md sprint state.

### `v5.15.6.A` (QUEUED)
- Drawdown circuit breaker
- Daily PnL cap
- Position size limits
- Other safety items per the "operational safety audit" in CLAUDE.local.md ship-after table
- ~1-2 days; MED risk

### `v5.15.6.B` (QUEUED)
- Live-readiness final touches: cfg validation gates + boot-time safety verification + operator paper-test prep
- ~1 day; LOW-MED risk

**→ `v5.15` umbrella close**

---

## Phase E — Paper-test session

Operator window to exercise the engine. Success criteria:

- Engine boots + accepts live cfg without errors
- Settings panel renders + accepts edits + saves cfg with no parity drift
- Tooltip system reads canonical descriptor info + displays correctly
- Live-readiness gates fire correctly on intentional violations
- Drawdown circuit breaker + daily PnL cap + position size limits work in simulated stress test
- Paper-test trade execution produces bytewise-identical stamps + cfg roundtrip + reproduces in backtest
- Hot path p99 ≤500ns + slow path p99 ≤100μs maintained throughout

Operator decides duration + cohorts to test. Bugs caught here land in cleaner shape because structural foundation is in place. Each bug = isolated symptom + diagnosable via audit gates + skill suite.

---

## Decision points + when they get resolved

| Decision | Resolved at | Default if not surfaced |
|---|---|---|
| CRIT-6 canonical body byte order (a) version bump vs (b) walker enrichment | `.B.2` planning | (a) accept reorder + bump stamp_format_version |
| Phase C sub-ship count + sequencing | `.F.4f` close `/anti-spaghetti` audit | placeholder `.F.5.A/.B/.C` |
| FOREACH_STAMP_BOUND_MODEL_CONST sister consolidation | After Phase C ships | TECH_DEBT future ship |
| controller_test.cpp split (26K lines past 5K rule) | Dedicated test-split ship | TECH_DEBT carryover |
| `tools/check_registry_overlap.py` automation | `.B.3` close OR `.F.4f` | TECH_DEBT entry |

---

## Dependencies

Ship sequence is strict per audit-driven discipline:
- `.A` ✓ → `.B.1` (current) → `.B.2` → `.B.3` → `.C` (or interleaved after `.B.3`) → `.D`
- `.F.4d.1` umbrella close after `.D`
- `.F.4e` after `.F.4d.1` (validates framework via second-source applications)
- `.F.4f` after `.F.4e` (cleanup ship; closes deferred TECH_DEBT)
- `.F.4f` close → fire `/anti-spaghetti` on ML/GUI/Backtest → size Phase C
- `.F.5.A/.B/.C` per audit findings
- `.F.5` close → `.F` umbrella close
- `v5.15.6.A` + `.B` → `v5.15` umbrella close
- Paper-test session

---

## Cross-references

- Sprint MASTER: `plans/v5.15-live-readiness/MASTER.md` (if exists)
- Sub-master: `subplans/2026-05-16-v5.15.5.F.4d.1-thread-a-framework-full.md` v1.3
- `.B` audit synthesis: `plan_checks/2026-05-17-v5.15.5.F.4d.1.B-audit-synthesis.md`
- CLAUDE.local.md sprint state row (ship-after table)
- ML decoupling roadmap: `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`
- DESIGN_SPECS catalog: `tick-trader-percore-workspace/DESIGN_SPECS/README.md`
- Skill suite: `tick-trader-percore-workspace/claude-skills/`

---

## Update policy

- ALL ships in Phases A-D get their own audit→update→implement→ship cycle (per per-sub-ship discipline)
- This roadmap UPDATED at each phase-boundary close (e.g., after `.F.4f` ships, refresh Phase C with audit-determined sub-ship list)
- Decision points resolved at their indicated ships; default applied if not surfaced
- `feedback_compaction_degrades_treat_handoffs_as_hints` applies — verify roadmap claims against current code/state when picking up after compaction

---

**End of roadmap v1.0.** Next update after `.B.1` ships.
