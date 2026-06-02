---
name: feedback_process_weight_by_surface_blast_radius
description: "Right-size process ceremony by SURFACE blast-radius: engine/capital code → heavy planning + audit gates; workspace/skill/doc apparatus → light dogfood-and-iterate. Breadth ≠ blast-radius."
metadata: 
  node_type: memory
  type: feedback
  tags: [audit-methodology, meta-discipline, operator-collaboration]
  sister_specs: [feedback_auto_route_input_to_matching_skill.md, feedback_heavier_default_audit_posture_for_capital.md, feedback_never_skip_thoroughness_unless_explicit.md, feedback_tiered_audit_discipline_per_plan_scope.md]
    []
  originSessionId: 730312a8-1185-4682-b01f-544206cbcd6d
---

Process weight (plan body / `/precoding-audit-gate` / heavy in-depth planning) scales with a surface's **blast-radius**, not its size.

- **Engine repo (capital / determinism / wire-format / hot-path) = HEAVY.** A flaw is silent, expensive, hard to reverse → plan body + audit gate + heavier-default posture earned.
- **Workspace / skill / doc apparatus = LIGHT.** A flaw is visible prose, reversible, no capital/determinism on the line → DOGFOOD-and-iterate is the validation mode, NOT pre-gates. "It's harder to introduce issues here."

**Why:** 2026-06-02, building the skill-consult meta-discipline, I mis-applied capital-code gravity to skill *prose* — called a 20-skill consult-stage edit "HIGH-RISK, propagates-a-flaw-20×" and proposed a plan-body + audit-gate before any edits. Caramel corrected it: worst case here is a one-line markdown fix; reserve heavy in-depth planning for the actual engine repo. The error was treating **breadth** (20 files) as **blast-radius** (severity × irreversibility × is-it-capital) — they're orthogonal; a wide doc edit is low-blast.

**How to apply:** Before choosing process weight, ask *"can a flaw on THIS surface be silent + irreversible + capital/determinism-bearing?"* Yes → heavy (engine-repo ceremony: plan body + audit gate). No → light: just implement + dogfood; let use surface the problems. The FLOOR stays non-zero even when light — the cheap **deterministic** checks still run on the apparatus (`check_session_docs.sh` doc/index/citation sweep); only the expensive **judgment** gates are reserved for the engine. Light ≠ careless; light = validate-by-use instead of validate-by-pre-gate. This is the LIGHT end of the same spectrum [[feedback_heavier_default_audit_posture_for_capital]] anchors at the HEAVY end (capital + inverse-coverage); within-a-surface scope-tiering is [[feedback_tiered_audit_discipline_per_plan_scope]]. Operator-explicit "just implement" is the legitimate skip per [[feedback_never_skip_thoroughness_unless_explicit]].
