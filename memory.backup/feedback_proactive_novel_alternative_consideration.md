---
name: feedback-proactive-novel-alternative-consideration
description: "When applying existing patterns, ALSO consider whether a novel design would fit better given the specific purpose of THIS code. Don't default to existing patterns out of inertia. Sister to canonical-sister-extension discipline — checks BOTH directions (use existing OR design novel given purpose). Applies at the FOUNDATIONAL/STRUCTURAL level too — post-audit, evaluate whether a better STRUCTURE exists vs patching within the current one (operator priority 2026-06-13)."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ba5429a9-2f65-4f8d-950c-3ae250973f24
  sister_specs: [feedback_audit_canonical_sister_before_new_infra.md, feedback_audit_own_proposals_with_same_rigor.md, feedback_enumerate_helper_signature_args_before_extract.md, feedback_design_once_maintain_forever.md, feedback_overengineering_boundary_when_future_easier.md, project_engine_done_edge_is_the_frontier.md]
  tags: [audit-methodology]
---

When proposing a design that applies existing patterns, ALSO evaluate whether a NOVEL design would fit better given the SPECIFIC purpose of THIS code.

The discipline isn't "use existing patterns" OR "design novel" — it's: **check existing patterns first (sister-discipline) AND check if a novel alternative is better-fit given specific purpose**. Don't default to existing patterns out of inertia; don't default to novelty out of cleverness.

Evaluate per axes per `feedback-evaluate-options-on-robustness-latency-design-not-time` + `feedback-surface-operator-migration-path-proactively`:
- Robustness (bug class closure depth)
- Latency (path impact)
- Design alignment (H1-H20 + framework discipline)
- Future-easier multiplier (N future applications mechanical?)
- Operator migration impact

If novel design wins on ≥3 axes, surface for operator triage. If existing pattern wins on ≥3 axes, use existing without surfacing.

**Why:** Codified 2026-05-17 at `.B.3` audit cycle. Caramel pushback meta-question ("is there a novel design that would fit better given the purpose?") forced me to evaluate novel alternatives I'd been skipping. For Decisions A/B/C/D/E, novel alternatives were considered + REJECTED (existing patterns won) — but the REJECTION rationale matters; without it, I was defaulting to existing patterns out of inertia. Codify to make the check explicit.

**How to apply:** In every plan body decision matrix, include explicit "Novel alternative considered" row per decision with verdict. Verdict shapes:
- **REJECTED (specific reason)** — novel alt evaluated; existing pattern wins on stated axes
- **ACCEPTED** — novel alt wins; surface for operator triage if ambiguous OR auto-pick if clear
- **SISTER TO EXISTING** — novel framing reduces to existing pattern application; not actually novel

**Foundational / structural level (post-audit — operator priority, 2026-06-13):** the novel-alternative check applies not just per-fix/per-decision but at the FOUNDATIONAL/STRUCTURAL level. When an audit/`/decision-check`/sweep surfaces info, the synthesis MUST evaluate — as a FIRST-CLASS output, not just "fix the instance" — *is the CURRENT foundation/structure the best available, or is there a better structural solution to move toward?* (canonical: patch the OMS partial-fill state machine now vs let the `.E.1` venue-net / per-node-sub-pool rework subsume it more cleanly). Don't patch within a structure the audit just revealed is the wrong shape — that's the inertia trap one level up. Ties to [[feedback-design-once-maintain-forever]] (one cycle exist→good), the structural-fix-preferred framework, [[feedback-overengineering-boundary-when-future-easier]] (pick the harder structural option when the future-multiplier is real), and [[project-engine-done-edge-is-the-frontier]] (major-structural NOW, optimize after; the goal is a moldable shape). The audit gives the info; the synthesis asks the foundational question BEFORE committing to a patch.

**Recognition markers:**
- Plan body decision matrix without "Novel alternative considered" row → not ready
- Patching within a structure an audit JUST flagged as the wrong shape, without evaluating the better STRUCTURAL solution → not ready (the foundational-level check above)
- Auto-pick existing pattern without considering "is there a better novel design here?" → not ready
- Defaulting to existing pattern out of "fits our codebase style" rather than fits SPECIFIC purpose → reconsider

**Sister:** [[feedback-audit-canonical-sister-before-new-infra]] (the existing-pattern direction — check sister registries BEFORE proposing new infra) + this memory is the COMPANION (check novel alternatives WHEN proposing to apply existing) + [[feedback-audit-own-proposals-with-same-rigor]] (4-pillar discipline).
