---
name: feedback_planning_treadmill_bias_to_execution
description: "when discovery is already sufficient for a concrete fix yet each planning step pushes coding further away (1 step → 5 more), the planning has become avoidance — land one verified change to break the spiral"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ba1a1443-354e-4bd4-897a-416ccbd8be2a
  sister_specs: [feedback_deferral_reasons_merit_not_effort_or_context.md, feedback_listen_and_execute_simply.md, feedback_no_defer_for_effort.md, feedback_plan_right_not_fast.md, user_adhd_deferred_reward_discipline.md, user_deep_design_work_intrinsic_value.md]
  tags: []
---

When discovery/planning is ALREADY sufficient for a concrete next action, yet each planning step pushes coding FURTHER away ("fix one step → now I'm 5 steps further away"), the extra planning has stopped being diligence and become **avoidance**. The tell is RECESSION not depth: steps spawn more steps and never CLOSE, while no code lands all session. Break it by landing ONE concrete, verified change (the smallest real fix, compile+test green), then re-anchor on execution.

**Why:** This is the shadow side of [[user_adhd_deferred_reward_discipline]] — deferred-reward discipline (planning over the dopamine of shipping) is a real strength, but it over-rotates into never collecting the reward (never shipping). It does NOT contradict [[feedback_plan_right_not_fast]]: that governs DECISION QUALITY (decide rightly; indecisiveness-while-deciding is a feature); THIS governs EXECUTION TIMING once the decisions are made. The discriminator: is the planning RESOLVING open decisions (good — continue) or RECEDING from an execution discovery already supports (treadmill — ship the fix)? Also distinct from [[user_deep_design_work_intrinsic_value]]: design-as-value is real when the design IS the deliverable; the treadmill is when planning substitutes for a coding step that is already unblocked. Caramel named it directly (`.E.0.10`, 2026-06-12: "every time I feel like I'm getting close to actually coding, I realize I'm 5 steps away… poisoned by planning") — and the AGENT was feeding it (generating ever-more audit/planning steps); the break was just coding A19, one verified one-line fix.

**How to apply:** (1) Watch the signal — I'm enumerating yet-more planning/audit before ANY code has landed this session AND the discovery already supports a concrete fix → STOP adding steps. (2) Land the smallest real verified change to break the spiral and bank progress. (3) When the operator is visibly close to execution, drive TO the code, don't generate the next five planning steps away from it. (4) Conversation-layer sister: [[feedback_listen_and_execute_simply]] (direct instruction → do it + STOP, don't spiral into meta-treatises). Merit cousins: [[feedback_no_defer_for_effort]] + [[feedback_deferral_reasons_merit_not_effort_or_context]] — the treadmill is indefinite-pre-planning, the do-it-now sibling of don't-defer-for-effort.
