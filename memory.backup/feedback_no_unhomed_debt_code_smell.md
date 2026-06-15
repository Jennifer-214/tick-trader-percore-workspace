---
name: feedback_no_unhomed_debt_code_smell
description: Tech debt with no future plan/home = code smell — homed-debt is fine to defer; unhomed-debt must be homed-or-closed NOW
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ce648e23-8658-4181-885c-5400b8e672bb
  sister_specs: [feedback_close_out_now_over_defer_when_small.md, feedback_deferral_reasons_merit_not_effort_or_context.md, feedback_fold_findings_into_destination_plan.md, feedback_no_defer_for_effort.md, feedback_opportunistic_tech_debt_closure.md, feedback_fix_toward_future_trajectory_not_static_state.md]
  tags: []
---

Every piece of tech debt MUST trace to a HOME — a future plan/ship that closes it, a TECH_DEBT entry with a trigger, or a live register disposition. **Debt with no home = code smell; homed-debt is fine to defer.** (Operator, repeatedly, `.E.0.10` 2026-06-12: *"lets not leave tech debt we dont have a future plan for on the table since that just makes the code smell."*)

**Why:** "on the table" means FORGOTTEN / UNOWNED, not deferred. Deferred-AND-homed is SAFE — it's owned, has a plan, and (for capital) is gated: the cross-thread torn-read class → `.E.1` aggregator + the HARD live-enable gate; the SP/HP branchless sweep → TECH_DEBT-173. UNHOMED debt is the smell — it rots silently because nothing will ever pick it up. So the discriminator is **homed-vs-unhomed**, layered on top of do-now-vs-defer.

**How to apply:** when current work surfaces debt, give it a home BEFORE moving on — fold it into the owning future plan ([[feedback_fold_findings_into_destination_plan]] — folding TRACKS, it doesn't defer the fix), open a TECH_DEBT entry with a trigger, or close it now ([[feedback_opportunistic_tech_debt_closure]], bidirectional — if the plan's design merely RENAMES it, close now; if it REDOES it, defer-and-home). The do-now-vs-defer call is SUBSUMPTION-not-adjacency; the FLOOR is that it gets a home either way. **A finding you can't home is a finding you must close.** Sister working-model (operator 2026-06-12): plans are **binding AND living** — stick to them, and update the owning plan with whatever touches its blast radius (the rolling-window-seam in `E-guard-coverage-matrix.md` §5). Sisters: [[feedback_no_defer_for_effort]] [[feedback_deferral_reasons_merit_not_effort_or_context]] [[feedback_close_out_now_over_defer_when_small]].
