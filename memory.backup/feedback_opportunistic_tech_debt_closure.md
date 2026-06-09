---
name: opportunistic-tech-debt-closure-subsumption-not-adjacency
description: "Caramel's policy (2026-06-02) — when new work SUBSUMES / trivially-completes a tracked tech-debt item (≈zero marginal cost), close it in the same ship; when merely ADJACENT (same surface, distinct deliverable), cross-link + leave tracked. The discriminator is marginal-cost/subsumption, NOT surface-adjacency."
metadata: 
  node_type: memory
  type: feedback
  tags: [scope-discipline, operator-collaboration]
  sister_specs: [feedback_no_defer_for_effort.md, feedback_future_headache_vs_optimization_scope_framework.md, feedback_close_the_class_vs_migrate_every_site.md, feedback_design_once_maintain_forever.md, project_e_series_is_vision_convergence_not_scope_balloon.md, feedback_guards_compound_enforcement_is_leverage.md, feedback_deferral_reasons_merit_not_effort_or_context.md, feedback_close_out_now_over_defer_when_small.md]
  originSessionId: 404732ed-f74c-4c1d-a12d-3dad513c1be2
---

When new work touches a surface that ALSO carries tracked tech-debt, the close-vs-leave call is decided by **marginal cost / subsumption — NOT mere surface-adjacency**:

- **SUBSUMED / trivially-completed** — the new work already did ~90%, you built the primitive, closing it is ≈zero extra cost → **CLOSE it in the same ship.** Leaving an easy close open is just deferred debt ([[feedback_no_defer_for_effort]]).
- **Merely ADJACENT** — same surface / same theme, but a *distinct* deliverable with its own code + test + trigger → **cross-link + leave tracked + refresh the entry.** Force-closing every adjacent item is how a focused task balloons.

**Why this framing, and what it is NOT:**
- NOT "the `.E` plan closes every tech-debt item" — that balloons `.E` (82 OPEN items; `.E` is foundational rework, per [[project_e_series_is_vision_convergence_not_scope_balloon]]).
- NOT a new "scan at close" rule — `/readiness` **Check 25** already scans the ship's surface-area tech-debt at close and forces an explicit decide. This is the sharper DURING-the-work trigger layered on top: of the items Check 25 surfaces, the *subsumed* ones get closed now, the *distinct* ones get tracked.
- It is the considered answer to "should every subplan close as much tech-debt as possible?" → yes, but bounded by subsumption, not adjacency.

**Worked examples (the dead-code / identifier-retirement codification, 2026-06-02):**
- **CLOSED (subsumed):** the dead `fp2_to_mag_fpn` helper — removing it was zero-marginal-cost while already editing `FixedPointN.hpp`. Closed in the same pass.
- **LEFT TRACKED (adjacent):** `TECH_DEBT-151` #8 (promote `calls_graph_diff` to a pre-commit orphan-guard) — same pre-commit surface + same dead-code theme as the new Check H, but a DISTINCT guard (function-orphans ≠ identifier-reuse), its own negative-self-test, and a specific `.E.1`-prep trigger (it must exist *before* `.E.1`'s orphan-generating rename). Cross-linked (renumbered to Check I) + left tracked — NOT force-closed.
- **LEFT TRACKED (adjacent):** `TECH_DEBT-152` (enroll bitmap bits + cfg-field names into the identifier guard) — distinct parser branches; paced enrollment per [[feedback_close_the_class_vs_migrate_every_site]].

**How to apply:** when `/readiness` Check 25 surfaces surface-area tech-debt at a ship, classify each — subsumed → close now; adjacent → cross-link + refresh. Don't leave a subsumed item open; don't force-close a distinct one. Sister to [[feedback_future_headache_vs_optimization_scope_framework]] (close anti-pattern instances at ship; defer pure-perf) and [[feedback_design_once_maintain_forever]] (design once — and that includes closing the easy adjacent debt while you're there).
