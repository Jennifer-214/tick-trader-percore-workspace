---
name: sister-cohort-amendment-completeness
description: "When amending a Class catalog / DESIGN_SPEC / ledger entry, enumerate sister-cohort artifacts (cross-refs in the amended artifact + reverse cross-refs from sister artifacts) requiring parallel amendments BEFORE locking scope."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 219ed0c3-e701-4643-ab2e-f475f7b60f64
  sister_specs: [feedback_audit_canonical_sister_before_new_infra.md, feedback_no_defer_for_effort.md, feedback_iteration_spiral_signals_audit_meta_gap.md, feedback_forward_promise_auto_write_verification.md, feedback_proactive_rename_candidate_surfacing.md, feedback_skill_edit_cohort_checklist.md, feedback_verify_every_enumerated_site_at_close.md]
  tags: [session-continuity, doc-discipline, enumeration-discipline]
---

When amending one Class catalog (e.g., Class 26) OR DESIGN_SPEC (e.g., structural-enforcement-when-memory-insufficient.md) OR ledger entry (e.g., TECH_DEBT), parallel sister-cohort artifacts that cross-reference it require parallel amendments. Failure to enumerate sister-cohort produces silent cross-ref drift.

**Why:** /blindspot-scan caught HIGH-3 finding at v5.15.5.F.4d.1.B.8 — plan amended Class 26 only (sub-shape B addition); Class 27 + Class 25 + Class 18 sister cross-refs needed parallel amendments. Recurring pattern: sister-cohort artifacts drift silently when one amends without sister enumeration. Sister to [[feedback_audit_canonical_sister_before_new_infra]] which is at CREATION layer; this discipline is at AMENDMENT layer.

**How to apply:** At any catalog / DESIGN_SPEC / ledger amendment proposal, enumerate sister-cohort artifacts via:
1. Cross-refs IN the amended artifact (sister_specs frontmatter / Cross-references section / Sister classes section)
2. Reverse cross-refs FROM sister artifacts (grep `<amended-artifact-name>` across catalog dir / DESIGN_SPECS / ledger files)
3. Apply parallel amendments in SAME ship per `feedback_no_defer_for_effort`

**Recursion termination:** sister-cohort enumeration may itself trigger further sister-cohort enumeration (e.g., amending Class 27 sister cross-ref may surface Class 25 sister-cross-ref need). Fixpoint reached when amended cohort has no NEW sister cross-refs at next enumeration pass. Worked example: v5.15.5.F.4d.1.B.8 v1.1 → v1.2 closed recursion (cycle 3 /blindspot-scan re-fire verified fixpoint).

**Worked examples:**
- v5.15.5.F.4d.1.B.8 Phase D Steps D.4/D.5/D.6 (Class 27 + 25 + 18 sister-catalog amendments after Class 26 sub-shape B addition)
- v5.15.5.F.4d.1.B.8 Phase H.2.d (/dod-audit SKILL.md sister amendment after /accounting-audit + /capture-audit codification per /blindspot-scan v1.1 H-RECURSIVE-1)

**Sister disciplines:**
- [[feedback_audit_canonical_sister_before_new_infra]] (CREATION layer; this is AMENDMENT layer)
- [[feedback_no_defer_for_effort]] (parallel amendments same ship; not deferred)
- [[feedback_iteration_spiral_signals_audit_meta_gap]] (recursion termination criterion via cycle 3 inflection check)
- `DESIGN_SPECS/meta-disciplines/sister-cohort-amendment-completeness-discipline.md` (**Stage 3 first canonical v1.0**; promoted Stage 2→Stage 3 at v5.15.5.F.4d.1.B.8 ship close per /capture-audit Check 7 surfacing; 4 distinct AMENDMENT-layer canonical applications at single ship)
- `DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md` (sister at CREATION layer; v1.1 at v5.15.5.F.4d.1.B.8 adds CI-tooling-surface axis)

**Skill integration:**
- `/precoding-audit-gate` should fire `/blindspot-scan` against sister-cohort surface when amending Class catalog / DESIGN_SPEC / ledger
- `/capture-audit` Check 9 (memory→DESIGN_SPECS sister cross-ref) catches drift at commit-time

**Lifecycle:** **Stage 3 first canonical v1.0 at v5.15.5.F.4d.1.B.8** (promoted Stage 2→Stage 3 at ship close per /capture-audit Check 7; 4 distinct AMENDMENT-layer canonical applications at single ship: Class 27 + Class 25 sister-catalog cross-ref amendments + canonical-sister-extension-discipline.md v1.0→v1.1 + /dod-audit sister-skill amendment). Stage 4 cohort migration promotion at 2nd canonical at next ship surface (e.g., NEW Class catalog with sister cross-refs to existing classes OR NEW DESIGN_SPEC requiring parallel sister-spec amendments).

**Decision-fold sweep clause (D-172c, 2026-06-10):** when a D-NNN decision SUPERSEDES or
FOLDS a finding's disposition, sweep the plan-body rows still carrying the OLD disposition
in the SAME session — a decision log that moves on while body rows say "low priority" (or
keep a superseded formula) is the same silent cross-ref drift, between the log and the body.
Canonical instance: Ship-B S-1 (D-127 folded F-B; rows kept the stale disposition); the
clause then fired ON ITSELF within hours at the fold-fidelity re-fire (the superseded `2r`
formula swept from plan rows) — confirming the class.
