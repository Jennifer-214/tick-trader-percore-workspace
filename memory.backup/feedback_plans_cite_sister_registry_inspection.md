---
name: plans-cite-sister-registry-inspection
description: "Plans introducing new framework infrastructure (X-macro registry / metadata bit / dispatch table / sidecar / consumer macro) MUST include \"Canonical sister registries considered\" section in plan body header with per-candidate fold/no-fold verdict + rationale. Ship-blocker if missing."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e52d563e-1fb7-4ce4-ac68-6b9fa4608fec
---

Plan bodies introducing any new framework infrastructure (FOREACH_X(X) new registry / new metadata bit row / new dispatch table / new sparse sidecar / new AUTOPOPULATE-style consumer macro) MUST include a "Canonical sister registries considered" section near the plan body header (typically in or adjacent to the Scope section). Each candidate sister gets:
- File:line reference where it lives at HEAD
- Fold / no-fold verdict
- Rationale (per [[feedback_audit_canonical_sister_before_new_infra]] 3-question test: same conceptual surface? ≥50% row overlap? same consumer behavior?)

**Why:** Two Path γ-class structural critiques caught at pre-coding audit gate in 2 weeks (`.A` 2026-05-16, `.B` 2026-05-17) — both same shape: plan author missed canonical sister. The information IS findable via grep; the discipline forces it to be DONE + DOCUMENTED in plan body so audit gate can verify without re-deriving. Catching at this stage = scope amendment before `pre-<tag>` rollback anchor created; catching later = wider blast radius. The 1st-time-cost of inspection (~10-20 min per plan) buys insurance against the structural drift the inspection catches.

**How to apply:**
- Trigger: plan body proposes any new FOREACH_X(X) registry / metadata bit / dispatch table / sidecar / consumer macro
- Action: BEFORE submitting plan body for pre-coding audit gate, fill in "Canonical sister registries considered" section
- Format:
  ```markdown
  ## Canonical sister registries considered

  | Candidate sister | Existing at | Fold/no-fold verdict | Rationale |
  |---|---|---|---|
  | FOREACH_<X> | <file:line> | FOLD / NO-FOLD | <why> |
  | FOREACH_<Y> | <file:line> | FOLD / NO-FOLD | <why> |
  ```
- `/readiness` Check 29 (NEW) — verifies presence + completeness of this section
- Pre-coding `/merge-scan` + `/anti-spaghetti` fire to verify the verdicts (catches missed sisters)
- Ship-blocker if section missing OR each candidate is "no inspection done"

**Exemptions:**
- Genuinely first-of-kind infrastructure (no canonical sister could exist by definition; e.g., FIRST autopopulate pattern, FIRST sidecar) — section still present but indicates "no precedent"
- Hotfix patches that don't add infrastructure (just fix existing code paths) — exempt
- Read-only diagnostics that walk existing registries (no new structure being added) — exempt

**Sister rules:**
- [[feedback_audit_canonical_sister_before_new_infra]] (the audit discipline this codifies for plans)
- [[project_anti_spaghetti_audit_cadence]] (periodic audit catches drift over time)
- [[feedback_consult_on_audit_findings]] (audit gate findings always trigger consult)

**Codified at:** 2026-05-17 (v5.15.5.F.4d.1.B.1 planning); `DESIGN_SPECS/canonical-sister-extension-discipline.md` Stage 2 DRAFT → Stage 3 first reference at `.B.1` ship; `/readiness` Check 29 amendment.
