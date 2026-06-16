---
type: meta-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.0
canonical_applications:
  - v5.15.5.F.4d.1.E.0 — first canonical (THIS pattern's first instance)
sister_specs:
  - audit-methodologies/audit-driven-pre-coding-gate.md (parent at per-ship scope)
  - meta-disciplines/plan-decomposition-and-future-aware-agent-arming.md (the PREQUEL — FINDS the correctness-driven cut-lines this spec then VERIFIES the trajectory of)
  - meta-disciplines/plan-hierarchy-and-sub-master-decomposition.md (sibling — the plan-TREE the decomposition produces, whose multi-ship trajectory this VERIFIES)
  - meta-disciplines/sister-cohort-amendment-completeness-discipline.md
  - meta-disciplines/canonical-sister-extension-discipline.md
  - meta-disciplines/iteration-spiral-signals-audit-meta-gap.md (sister discipline)
tags: [audit-methodology, sub-sprint-discipline, plan-trajectory-verification, pre-coding-gate, cross-ship-integration]
surface: [planning, audit-orchestration]
applies_at_skills: [/precoding-audit-gate, /readiness, /bug-check, /dod-audit, /parity-check, /anti-spaghetti]
---

# Audit-driven sub-sprint trajectory verification

**Pattern intent:** When a sub-sprint trajectory spans many ships (~7+) AND substantial architectural restructure, run the pre-coding audit gate at SUB-SPRINT scope (not just per-ship scope) BEFORE any coding starts.

## Problem statement

Per-ship audit gate (`audit-driven-pre-coding-gate.md`) catches plan body issues for ONE ship. But it doesn't catch:

- **Cross-ship integration issues:** ship X's forward-promise doesn't match ship Y's substrate assumption
- **Canonical-sister-extension gaps spanning ships:** ship X introduces NEW infra that should have extended ship Y's substrate
- **Anti-pattern reintroduction risk in restructure scope:** Class N closed at ship X; ship Z accidentally reintroduces
- **DESIGN_SPECS Stage promotion tracking accuracy:** ship X claims Stage 3 promotion but ship Y's `.E.0` audit reveals premature claim
- **Forward-promise misalignment:** ship X's TECH_DEBT-NEW-N claimed closed at ship Y; verification at sub-sprint scope

At per-ship scope, these slip through (each ship looks OK in isolation; trajectory-spanning concerns invisible).

## Pattern description

**Discipline applies when:** sub-sprint scope > 5 ships OR > 4 weeks projected effort OR architectural restructure exceeds single-ship scope.

**Workflow:**

1. **Add a dedicated audit-only sub-sprint ship** (e.g., `.E.0` for `.E` trajectory). Precedes ALL coding ships.

2. **Comprehensive parallel audits per plan body:**
   - 5-agent `/precoding-audit-gate` HIGH-RISK tier (parity-check + trace-deps + dod-audit + readiness + blindspot-scan)
   - `/bug-check` against full RECURRING_BUG_PATTERNS catalog
   - `/dod-audit` against DESIGN_SPECS pattern application

3. **Codebase-wide audits at sub-sprint scope:**
   - `/anti-spaghetti` pre-restructure baseline
   - `/registry-fit-audit` (verifies framework substrate readiness)
   - `/test-strength-audit` (baseline)
   - `/parity-check` (cross-cluster identity)

4. **Cross-ship invariant verification:**
   - Dependency graph holds
   - Forward-promises align with successors
   - TECH_DEBT closure tracking accurate
   - DESIGN_SPECS Stage promotion tracking accurate

5. **Operator triage + plan body amendments:**
   - Per `feedback_proportionate_response_to_audit_findings`
   - FIX-NOW / ACCEPT WITH RATIONALE / DEFER per finding
   - Plan body amendments applied

6. **Cycle 2 verification:**
   - Re-fire 5-agent audit per amended plan body
   - GREEN-READY-TO-CODE required before coding starts
   - If cycle 3+ needed: META gap signal per `iteration-spiral-signals-audit-meta-gap`

7. **Synthesis reports archived:**
   - Per-plan synthesis at `plan_checks/E.0-audit-reports/<plan-name>-synthesis.md`
   - Cross-ship synthesis at `plan_checks/E.0-audit-reports/cross-ship-synthesis.md`
   - Anti-pattern + DOD synthesis

## Worked example: `.E` sub-sprint at v5.15-live-readiness

- 8 active plan bodies (.E.0 through .E.X)
- 8 Stage 3 first canonical promotions across plans
- 6 amended existing DESIGN_SPECS
- 25+ NEW DESIGN_SPECS landing
- ~25-35 days projected total effort
- HIGH-RISK architectural restructure (drainer architecture replacement)

Without `.E.0`: each ship's Phase A would catch only its own findings. Cross-ship issues would surface mid-sub-sprint causing catastrophic rework.

With `.E.0`: all cross-ship integration verified BEFORE `.E.1` coding starts. Per-plan + cross-ship + anti-pattern + DOD audits surface 50-100+ findings at planning time (cheap to fix). Plan bodies iterated to GREEN-READY-TO-CODE collectively. Coding begins with high confidence.

## Stage progression criteria

- **Stage 2 DRAFT** (this status before `.E.0`): pattern outlined; awaits first canonical
- **Stage 3 first canonical** (lands at `.E.0`): `.E` sub-sprint applies pattern; lessons learned captured
- **Stage 4 cohort** (when 2nd sub-sprint applies): pattern proven across multiple trajectories
- **Stage 5 CLAUDE.md** (when 3rd application + discipline matures): promoted to CLAUDE.md item
- **Stage 6 cadence-locked** (CI enforcement): automated check that sub-sprints > 5 ships fire pre-coding audit gate

## Sister disciplines

- `audit-methodologies/audit-driven-pre-coding-gate.md` — parent pattern (per-ship scope); this extends to sub-sprint scope
- `meta-disciplines/sister-cohort-amendment-completeness-discipline.md` — amendments coherent across sister artifacts
- `meta-disciplines/canonical-sister-extension-discipline.md` — verify each plan extends canonical sisters
- `meta-disciplines/iteration-spiral-signals-audit-meta-gap.md` — recognition: cycle 3+ = META gap
- `meta-disciplines/structural-fix-preferred-decision-framework.md` — audit catches non-structural symptom fixes
- `meta-disciplines/single-source-of-truth-discipline.md` — audit verifies single-writer principle preserved

## Anti-patterns avoided

- **Discovering at code-time that ship X's substrate assumption is wrong** — pre-coding audit catches
- **Catastrophic mid-sub-sprint rework** — pre-audit prevents
- **Inconsistent DESIGN_SPECS Stage promotion claims** — verification catches premature claims
- **Cross-ship invariant violations during coding** — invariants enforced at plan-body level

## When to apply

✅ Sub-sprint with 5+ planned ships
✅ Architectural restructure spanning multiple ships
✅ Substantial Stage promotion churn across plans
✅ Multiple forward-promise chains across ships
✅ Cross-cluster or cross-domain integration concerns

❌ Single-ship work (use per-ship `audit-driven-pre-coding-gate.md` instead)
❌ Trivial scope (cleanup; doc-only; etc.)
❌ Bug-fix urgency where speed > comprehensive audit

## Decision log integration

Findings classified per `feedback_proportionate_response_to_audit_findings`:
- HIGH severity (blocking) → FIX-NOW or RED-BLOCKING
- MED severity (recommended fix) → operator-triaged
- LOW severity (acceptable) → ACCEPT WITH RATIONALE
- DEFERRED → captured in TECH_DEBT for later ship

Decision log entries (D-X) track triage outcomes; sentinel discipline per `feedback_session_decision_log_discipline`.

## Cross-references

- Parent: `audit-methodologies/audit-driven-pre-coding-gate.md`
- Sister: `meta-disciplines/sister-cohort-amendment-completeness-discipline.md`
- Sister: `meta-disciplines/canonical-sister-extension-discipline.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.0-precoding-plan-audit-verification.md`
