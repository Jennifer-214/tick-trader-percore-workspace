---
name: new-plans-use-future-oriented-template
description: New plan bodies (sub-ship or standalone) MUST use the canonical future-oriented-plan-template.md shape. Required sections (Design space + Canonical sister + Bug classes closed + DESIGN_SPECs landed) cannot be skipped. /readiness Check 29 + 30 verify presence. /plan-draft skill scaffolds.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e52d563e-1fb7-4ce4-ac68-6b9fa4608fec
---

New plan body drafts MUST use the canonical `DESIGN_SPECS/future-oriented-plan-template.md` shape. Required sections:

1. **Header** with predecessor / pre-tag rollback anchor / sub-master / audit reports paths
2. **Why this ship exists** — problem statement
3. **Design space + future-oriented choice** — ≥2 options table evaluated on robustness + latency + design alignment + future-easier multiplier; auto-pick rationale explicit
4. **Canonical sister registries considered** — per-candidate fold/no-fold verdict (skip section only if zero new framework infrastructure proposed; document why)
5. **Bug classes this closes** — structural closure mapping (Class N → closure mechanism)
6. **DESIGN_SPECs landed/amended** — NEW Stage 2 DRAFT → Stage 3 lifecycle; AMENDED specs with version delta
7. **Scope** — IN + NOT IN with explicit deferrals
8. **Steps** — numbered 0-N; each step has deliverables + verification + mid-flight tag opportunity
9. **Verification gate** — universal + ship-specific + hot path + replay determinism + HOT_PATH_CHANGELOG
10. **TECH_DEBT auto-write expectations**
11. **Pre-coding triggers** — checklist of items required before promoting DRAFT → ACTIVE
12. **Cross-references**

**Why:** ad-hoc plan drafting produces inconsistent structure; required discipline (canonical sister audit + future-oriented choice + bug class closure + DESIGN_SPECs codification) gets skipped depending on author's energy at draft time. Audit gate catches missing sections AFTER the fact (caught Path γ at `.A` 2026-05-16 + Path γ #2 at `.B` 2026-05-17 + the self-violation in `.B.1` v1.0 — plan body codifying canonical-sister-discipline MISSED its own required section). Bake discipline INTO plan structure so it's impossible to forget.

**How to apply:**
- Trigger: any NEW plan body being drafted (sub-master sub-ship OR standalone ship OR STUB→ACTIVE promotion OR retrofit during per-sub-ship cycle)
- Action: copy `DESIGN_SPECS/future-oriented-plan-template.md` template into new plan body file OR fire `/plan-draft` skill to scaffold
- Required sections present + filled before pre-coding audit gate fires
- `/readiness` Check 29 (Canonical sister registries considered section present) + Check 30 (Design space + future-oriented choice section present with ≥2 options) verify mechanically
- Pre-coding audit gate ship-blocker if required sections missing or each section is "no analysis done"

**Retrofit guidance:**
- Existing plan bodies (drafted pre-2026-05-17 without template) retrofit at per-sub-ship cycle update step
- `.B.1` v1.0 → v1.1 (2026-05-17) was the FIRST retrofit — added Canonical sister + Step 0.5 sections retroactively
- Older plans retrofit on opportunity-cost basis (high-value-for-effort) NOT mandatory all at once

**Sister rules:**
- [[feedback_audit_canonical_sister_before_new_infra]] (the discipline the Canonical sister section encodes)
- [[feedback_plans_cite_sister_registry_inspection]] (the citation requirement the template enforces)
- [[feedback_auto_pick_future_oriented]] (the discipline the Design space section encodes)
- [[feedback_structural_fix_for_recurring_class]] (the discipline the Bug classes section encodes)
- [[feedback_sub_plan_sidecar_files_for_substantial_sections]] (sidecar files for substantial implementation sections)

**Codified at:** 2026-05-17 (v5.15.5.F.4d.1.B.1 planning per Caramel's request "format plans for future-oriented solutions going forward + make something to assist with that guardrail"); `DESIGN_SPECS/future-oriented-plan-template.md` Stage 2 DRAFT → Stage 3 first reference at `.B.1` v1.1 retrofit; `/plan-draft` skill Stage 2 DRAFT at `claude-skills/plan-draft/SKILL.md`; `/readiness` Check 29 + 30 amendments.
