---
name: anti-spaghetti-audit-cadence
description: "Periodic codebase-wide /anti-spaghetti audit cadence — quarterly health check + post-new-anti-pattern-codification sweep + ad-hoc when \"is this becoming spaghetti?\" feeling surfaces. Skill spec at claude-skills/anti-spaghetti/SKILL.md."
metadata: 
  node_type: memory
  type: project
  originSessionId: e52d563e-1fb7-4ce4-ac68-6b9fa4608fec
---

Periodic codebase-wide `/anti-spaghetti` audit fires on the following cadence:

1. **Quarterly health check** — codebase-wide scan for parallel-infrastructure anti-patterns; output ranked list of fold candidates (CRITICAL/HIGH/MED/LOW). First run was 2026-05-17 at `.B` Batch 2 audit (1st canonical of the skill); next scheduled ~2026-08-17 (3 months).

2. **Post-new-anti-pattern-codification sweep** — after a new Class lands in `DOCS/RECURRING_BUG_PATTERNS.md`, fire `/anti-spaghetti` to scan for instances codebase-wide. Often surfaces additional instances of the just-codified pattern that wouldn't otherwise be caught.

3. **Operator instinct check** — when "is this becoming spaghetti?" feeling surfaces during a sprint (audit findings volume feels overwhelming; codebase complexity feels accelerating), fire `/anti-spaghetti` to ground the feeling in actual data. Codebase data + operator feeling typically reconcile (data confirms transition in progress, not actual spaghetti).

**Why:** Path γ-class structural critiques recur over time. Plan-time discipline ([[feedback_audit_canonical_sister_before_new_infra]] + [[feedback_plans_cite_sister_registry_inspection]]) catches them at audit gate; periodic audit catches drift that crept in between gates (e.g., code modifications post-ship that introduce parallel shapes). Plus the operator instinct check provides feedback loop: when codebase FEELS spaghetti, audit confirms or refutes with data, restoring confidence (or surfacing legitimate concerns).

**How to apply:**
- Quarterly: `/anti-spaghetti` fires codebase-wide; output saved to `plans/<sprint>/plan_checks/anti-spaghetti-<date>-quarterly.md`; findings triaged + folded into next sprint's planning OR opened as TECH_DEBT entries
- Post-codification: after new Class is added to RECURRING_BUG_PATTERNS.md (e.g., Class 28 codified 2026-05-15 `.F.4c.3`), fire `/anti-spaghetti` with new class as focus_keyword
- Operator instinct: fire ad-hoc when "is this becoming spaghetti?" feeling surfaces; output validates the feeling vs codebase data

**Skill spec:** `tick-trader-percore-workspace/claude-skills/anti-spaghetti/SKILL.md` (Stage 2 DRAFT 2026-05-17; first canonical run already validated methodology at Batch 2)

**Distinct from:**
- `/bug-check` — line-level instance scan of known bug classes
- `/dod-audit` — DESIGN_SPECS pattern application
- `/merge-scan` — code-level reuse opportunities
- `/dust` — generic cleanup (rotting comments, oversized fns, dead code)

**Sister rules:**
- [[feedback_audit_canonical_sister_before_new_infra]] (plan-time discipline)
- [[feedback_plans_cite_sister_registry_inspection]] (plan body documentation discipline)
- [[feedback_consult_on_audit_findings]] (findings always trigger consult)

**Codified at:** 2026-05-17 (v5.15.5.F.4d.1.B.1 planning); `DESIGN_SPECS/canonical-sister-extension-discipline.md` + `claude-skills/anti-spaghetti/SKILL.md`.

**Cadence schedule:**
- 2026-05-17: 1st canonical run (Batch 2 audit at `.B` planning) — found 3-way triplet CRITICAL + CoreCtx INIT/RESET/SUMMARY HIGH + 6 MEDs KEEP
- 2026-08-17 (target): Q2 health check
- 2026-11-17 (target): Q3 health check
- Plus ad-hoc per triggers above
