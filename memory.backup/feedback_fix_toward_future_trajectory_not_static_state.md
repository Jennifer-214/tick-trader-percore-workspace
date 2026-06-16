---
name: feedback_fix_toward_future_trajectory_not_static_state
description: "changing code a documented future ship will rework → design the fix as a forward-compatible foundation increment toward that destination, never a patch against the about-to-change present; the audit subagent classes carry it as a standing lens"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d04c6027-6cab-4b9d-84f5-356891adc8e6
  sister_specs: [feedback_auto_pick_future_oriented.md, feedback_design_once_maintain_forever.md, feedback_dont_generalize_substrate_before_input_space_known.md, feedback_fold_findings_into_destination_plan.md, feedback_no_mvp_for_plumbing_only_for_unknown_unknowns.md, feedback_no_unhomed_debt_code_smell.md, feedback_overengineering_boundary_when_future_easier.md, feedback_phased_pre_rework_correctness_foundation.md, feedback_arm_subagents_plan_and_future_aware.md]
  tags: []
---

When changing capital- or architecture-bearing code that a **documented** future ship will rework (the E-series DAG · `plans/_future/*` vision docs · the destination plan body), design the change as a forward-compatible **foundation increment** toward that destination — NEVER a point-in-time patch against a static present that is about to change.

**Why:** a patch the rework later undoes is throwaway work AND it re-traverses capital/determinism-gated code (re-opening the whole verification surface — the [[feedback_design_once_maintain_forever]] violation). A fix aligned with the documented destination is the rework's FIRST increment — same effort, but it COMPOUNDS instead of being discarded. Operator frame (2026-06-15, `.E.0.10` TD-202 gate): *"are the fixes in line with the future E plans, so we aren't patching based on a static state, but a targeted foundation for a future plan?"*

**How to apply:**
- Read the trajectory FIRST — the destination plan + the relevant `plans/_future/*` vision docs + the E DAG. Identify what the future rework MAKES this surface BE.
- Design the fix as a strict SUBSET / precursor the rework EXTENDS, never UNDOES → forward-compatible, no re-traversal. If the destination would throw the fix away, it is a static-state patch — reshape it.
- HOME the rest in the destination plan (fold the findings into it, [[feedback_fold_findings_into_destination_plan]]) — homed-and-deferred, never unhomed ([[feedback_no_unhomed_debt_code_smell]]).
- BOUNDARY (don't over-apply): this is for KNOWN, DOCUMENTED trajectories ONLY. For unknown-unknowns MVP still applies ([[feedback_no_mvp_for_plumbing_only_for_unknown_unknowns]]); do NOT pre-build the future or generalize a substrate before its input space is known ([[feedback_dont_generalize_substrate_before_input_space_known]]). ALIGN the fix; don't BUILD the destination.
- SUBAGENT LENS (the "so the subagent classes use it" requirement): the audit classes (I/A · `/precoding-audit-gate` · `/decision-check`) carry this as standing arming — every proposed fix is evaluated against the documented trajectory, and a fix the destination would discard is flagged as static-state patching. The gate injects the trajectory-doc pointers into the Layer-2 subagent prompts. Canonical body: `DESIGN_SPECS/meta-disciplines/fix-toward-future-trajectory-not-static-state.md`.

Sisters: [[feedback_design_once_maintain_forever]] · [[feedback_auto_pick_future_oriented]] · [[feedback_overengineering_boundary_when_future_easier]] · [[feedback_fold_findings_into_destination_plan]] · [[feedback_phased_pre_rework_correctness_foundation]] · [[feedback_dont_generalize_substrate_before_input_space_known]].

First canonical: `.E.0.10` TD-202 event-log UAF — the quiesce-first `OrderEventLog_Init` guard is the forward-compatible increment of the Init/Free/Start/Stop lifecycle-idempotency discipline `.E.1` explicitly owns; the single-owner-`disk_file` + writer→control-plane redesign is the `.E.1` rework (per `plans/_future/2026-06-15-control-plane-data-plane-housekeeping-separation.md` + per-node-purity H22). RBP Class 50.
