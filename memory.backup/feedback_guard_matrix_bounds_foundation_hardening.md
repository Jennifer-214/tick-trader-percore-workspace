---
name: guard-matrix-bounds-foundation-hardening
description: "The guard-coverage-matrix is the bound that makes 'solid foundation' finite — harden until every invariant the next phase touches is an enforced matrix row (no HOLE/TBD), then build. The stop condition against bottomless foundation-hardening."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e0432c39-f2fb-4a6b-844b-d2ce99975ef0
  sister_specs: [feedback_phased_pre_rework_correctness_foundation.md, feedback_heavier_default_audit_posture_for_capital.md, feedback_close_the_class_vs_migrate_every_site.md]
  tags: [audit-methodology, meta-discipline, scope-discipline]
---

"You can't build an empire on sand" / "make the foundation solid first" is RIGHT, but it risks becoming a bottomless well — you can always harden more. The **guard-coverage-matrix** (`plans/<sprint>/E-guard-coverage-matrix.md`) is the **stop condition**: harden until every invariant the next phase *actually touches* is an ENFORCED row (Tier-1 `static_assert` / Tier-2 CI / Tier-3 test / golden), not a HOLE (convention-only) or TBD — then build. The floor only rises after (the ratchet); this is the *minimum* standing apparatus, not the ceiling.

**Why:** it turns "solid enough" from a vibe into a checklist, and it prevents foundation-hardening from swallowing the sprint. The matrix tells you BOTH where to go heavy (audit-weight ∝ inverse deterministic coverage — heavy where the matrix has a HOLE) AND when you're done (no HOLE for the touched surface). Without it, "make it solid" has no terminating condition. Surfaced at `.E.0.1`/`.E.0.3`: it bounds the determinism/H12/locale foundation work to what `.E.1` touches, so it doesn't balloon.

**How to apply:** before a high-risk rework, read the touched invariants off the guard-coverage-matrix; push the HOLE/TBD ones to an enforced tier; STOP when none remain for what the rework touches. Sister: [[feedback_phased_pre_rework_correctness_foundation]] (D-73 — the matrix is its completeness contract), [[feedback_heavier_default_audit_posture_for_capital]] (the matrix is what you read audit-weight off of). The guard is also the tracking substrate for [[feedback_close_the_class_vs_migrate_every_site]].
