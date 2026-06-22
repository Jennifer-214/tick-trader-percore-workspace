---
name: feedback-audit-own-proposals-with-same-rigor
description: "Before surfacing any recommendation to Caramel, apply the same discipline I'd apply to operator-proposed plans — DESIGN_SPECS cross-check + anti-pattern catalog check + operator-impact dimension + novel-alternative consideration. If I haven't done all four, I'm not ready to surface."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ba5429a9-2f65-4f8d-950c-3ae250973f24
  sister_specs: [feedback_proactive_novel_alternative_consideration.md, feedback_consult_on_audit_findings.md, feedback_recheck_designspecs_on_pushback.md, feedback_surface_operator_migration_path_proactively.md, feedback_enumerate_helper_signature_args_before_extract.md, feedback_enumerate_set_before_categorical_claim.md, feedback_implementation_detail_blindspot_recovery_via_taxonomy.md, feedback_iteration_spiral_signals_audit_meta_gap.md, feedback_lead_with_architectural_merit_not_operator_tone.md, project_e_series_is_vision_convergence_not_scope_balloon.md, feedback_surface_foundational_decisions_not_just_tactical.md]
  tags: [audit-methodology, operator-collaboration]
---

Before recommending any decision (auto-pick on design space; framework extension; new spec; refactor scope), apply the FULL audit discipline to my OWN proposal:

1. **DESIGN_SPECS cross-check** — does existing DESIGN_SPECS catalog cover this pattern? If yes, use existing pattern; don't reinvent. If no, is a NEW spec warranted (≥2 codebase recurrences + foreseeable future applications)?
2. **Anti-pattern catalog check** — verify proposal against all 30 classes in `DOCS/RECURRING_BUG_PATTERNS.md`. Document CLEAN/CLOSES/N-A per class.
3. **Operator-impact dimension** — what action does Caramel need to take if this lands? Migration burden? Workflow disruption? Existing trained models still work?
4. **Novel-alternative consideration** — could a novel design fit better given the SPECIFIC purpose of THIS code? Don't default to existing patterns out of inertia OR novelty out of cleverness.

**Why:** Codified 2026-05-17 at `.B.3` audit cycle. Caramel's 4 pushbacks this session caught me at every dimension I'd been sandbagging — effort-avoidance on Decision C (would have introduced Class 21 anti-pattern); missing DESIGN_SPECS cross-check (relied on audit findings without checking existing patterns); abbreviated anti-pattern check (only spot-checked classes); binary STRICT/LENIENT framing missed SOFT compat design (audits ALSO missed it). Each pushback found a real gap. Encode the rigor so future-me applies proactively.

**How to apply:** Sister to `feedback_consult_on_audit_findings` (the OPERATOR-TRIAGE companion) — this is the SELF-AUDIT companion. Apply BEFORE surfacing a recommendation, not AFTER pushback. When tempted to surface "here's my pick" — STOP. Apply all 4 dimensions first. If I haven't done all four, I'm not ready to surface; do the audit work + then surface.

**Recognition markers:**
- "Auto-pick (a)" without explicit DESIGN_SPECS reference → not ready
- "CLEAN" anti-pattern claim without per-class enumeration → not ready
- Recommendation that involves wire-format/version/breaking-cfg without explicit operator-impact section → not ready
- Picking existing pattern without considering novel alternatives → not ready (apply [[feedback-proactive-novel-alternative-consideration]])

**Sister:** [[feedback-consult-on-audit-findings]] (operator triage) + [[feedback-proactive-novel-alternative-consideration]] + [[feedback-recheck-designspecs-on-pushback]] + [[feedback-surface-operator-migration-path-proactively]] (the 4-pillar discipline).
