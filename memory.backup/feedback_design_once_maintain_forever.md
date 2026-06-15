---
name: single-cycle-exist-good-design-once-maintain-forever
description: "Caramel's policy (set 2026-06-02) for THIS codebase — take a piece exist→good within ONE cycle (not exist-now/good-later); re-traversing interconnected determinism-gated code is the cost to avoid; design once, maintain forever"
metadata: 
  node_type: memory
  type: feedback
  tags: [operator-collaboration, scope-discipline, structural-fix]
  sister_specs: [feedback_no_defer_for_effort.md, feedback_plan_right_not_fast.md, feedback_motivated_collaborator_for_caramel.md, feedback_no_mvp_for_plumbing_only_for_unknown_unknowns.md, feedback_heavier_default_audit_posture_for_capital.md, feedback_opportunistic_tech_debt_closure.md, feedback_guards_compound_enforcement_is_leverage.md, feedback_deferral_reasons_merit_not_effort_or_context.md, feedback_close_out_now_over_defer_when_small.md, feedback_proactive_novel_alternative_consideration.md, feedback_fix_toward_future_trajectory_not_static_state.md]
  originSessionId: 404732ed-f74c-4c1d-a12d-3dad513c1be2
---

For THIS codebase, build a piece **exist → good within ONE cycle**. Do not ship "it exists" and defer "make it good" to a later cycle — the good (branchless, SSoT, framework-fit, dead code removed, full op surface) goes INTO the first pass, not a follow-up ship. **Design once, maintain forever:** after the first cycle the piece should need only maintenance, never rework.

**Why:** the engine is interconnected + determinism-gated. A second pass over the same code is expensive AND risky — re-touching capital-bearing / determinism-gated / value-equivalence-gated code re-opens the whole verification surface (re-prove, re-freeze goldens, re-audit, re-stamp). The cost of getting-it-good-now is far below the cost of re-traversing "massive pieces" later. Caramel (2026-06-02): "i dont wanna have to run back over massive pieces, like design once, maintain forever."

**This is NOT the common "make it exist, then make it good."** That advice is for *exploratory product code with unknown-unknowns* — an MVP to discover the requirement (see [[feedback_no_mvp_for_plumbing_only_for_unknown_unknowns]]). For *foundational / interconnected / determinism-gated infrastructure* where the requirement is KNOWN, splitting exist-now / good-later forces the wasteful re-traversal. Single-cycle exist+good is correct there.

**Often there is no exist-vs-good tradeoff at all.** Ship-A instance (2026-06-02): making the 16B ops branchless (good) was *value-identical* to the saturating versions (exist) — branchless fits INSIDE value-equivalence, so "good" cost nothing extra to fold into the first pass. When good and exist don't conflict, there is no reason to split them, and "make it exist first" is a false economy.

**How to apply:**
1. When building foundational infra, plan the "good" INTO the first cycle's scope — branchless dispatch, SSoT, framework-fit, no dead code left behind — not as a deferred polish ship.
2. When the requirement is KNOWN + the surface is interconnected/determinism-gated, treat "ship minimal, polish later" as a defer-smell ([[feedback_no_defer_for_effort]]).
3. Scope guard: genuine unknown-unknowns still warrant an MVP probe — this is for KNOWN-requirement foundational work, NOT a blanket "never iterate."

Sister to [[feedback_no_defer_for_effort]] (defer is last-ditch), [[feedback_plan_right_not_fast]] (design IS the work), [[feedback_motivated_collaborator_for_caramel]] (best-software bar), [[feedback_heavier_default_audit_posture_for_capital]] (capital → heavier default), and the dead-code / identifier-retirement discipline (no dead code left behind is part of "good").
