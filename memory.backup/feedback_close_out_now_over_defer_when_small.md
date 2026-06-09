---
name: close-out-now-over-defer-when-small
description: "Operator meta-stance (D-159, Ship-A session 2026-06-08): a SMALL fixable thing found in-flight — a surfaced bug, a stale doc, a missing guard, a tool gap — gets closed NOW (more-work-now-means-less-later); only genuinely-separate DELIVERABLES (Ship-B-scale work, next-numeric-epoch refreezes) defer. Discriminator = small-fixable-in-flight vs separate-deliverable, NOT effort or schedule pressure. Refines opportunistic-tech-debt-closure (subsumption axis) + no-defer-for-effort (effort axis) with the SIZE/in-flight axis."
metadata: 
  node_type: memory
  type: feedback
  sister_specs: [feedback_opportunistic_tech_debt_closure.md, feedback_no_defer_for_effort.md, feedback_deferral_reasons_merit_not_effort_or_context.md, feedback_design_once_maintain_forever.md]
  tags: [scope-discipline, operator-collaboration]
  originSessionId: 687aa85a-836d-488f-8cb8-2ee60d314782
---

**Close-out-now over defer, when the find is small.** A small fixable thing surfaced in-flight — a pre-existing bug a new tool catches, a stale doc cohort, a missing guard, a flaky test floor — gets closed in the same session/ship, not stacked as tech-debt. Don't let tech-debt stack.

**Why:** Reinforced repeatedly by the operator during the Ship-A close (session 11, 2026-06-08; decision-log D-159). Small finds are cheapest to close while the surface is open and context is loaded; deferring them converts minutes-now into a re-traversal later ([[feedback_design_once_maintain_forever]]). More-work-now-means-less-later.

**How to apply — the discriminator:**
- **SMALL fixable thing found in-flight → close NOW.** Canonical instances (all session 11): the first-ever sanitizer run surfaced a batch of pre-existing bugs → closed in-ship (D-155); the struct-alignment guard → built + teeth-proofed now, not deferred (D-156); the stale FPN doc cohort → 1:1 sweep done post-ship same session + self-healing guard (D-162).
- **Genuinely-separate DELIVERABLE → defer with a tracked home.** Canonical instances: the 16B golden refreeze (D-157 — gated on post-Ship-B core stabilization) and the FPN-struct re-pack (D-161 → TECH_DEBT-159 — same gated surface). These are deliverables in their own right, not in-flight finds.
- The axis is SIZE + in-flight-ness, on top of the sisters' axes: [[feedback_opportunistic_tech_debt_closure]] discriminates by subsumption/marginal-cost; [[feedback_no_defer_for_effort]] + [[feedback_deferral_reasons_merit_not_effort_or_context]] forbid effort/relatability as deferral reasons. All four compose: defer only on MERIT (separate deliverable, gated surface), never because the find is inconvenient.
