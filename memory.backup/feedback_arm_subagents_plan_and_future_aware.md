---
name: feedback_arm_subagents_plan_and_future_aware
description: Arm every planning/audit/verify sub-agent to be PLAN-aware (where the work sits in the trajectory + what predecessors landed + the decisions to honor) + FUTURE-aware (where the surface is GOING) + SPEC-CITED (the governing DESIGN_SPEC for the piece it approaches) — not just task + current-code. Extends M8.
metadata: 
  node_type: memory
  type: feedback
  tags: [audit-methodology]
  sister_specs: [plan-decomposition-and-future-aware-agent-arming.md, feedback_define_done_and_arm_scout_subagents.md, feedback_fix_toward_future_trajectory_not_static_state.md, feedback_run_dedicated_audit_skills_not_just_armed_prompts.md, feedback_a_class_i_class_fanout_vocab.md]
  originSessionId: d350664c-24b6-40b6-a54a-349d9a8de8e7
---

Arm every planning / audit / verify sub-agent to be **PLAN-aware + FUTURE-aware + SPEC-CITED**, on top of M8's nav-infra arming — not just its narrow task + the current code. Three additions:

1. **PLAN-aware (inbound-currency + the decision set):** load what the PREDECESSOR ships ACTUALLY landed (the disposition register's CLOSED rows + the real code + the decision log) and have the agent VERIFY the plan's shape against that landed reality — NOT the plan's stale self-assumptions; + the **already-made decisions the work must HONOR / not re-litigate**.
2. **FUTURE-aware (fix-toward-trajectory):** load the destination docs (`plans/_future/*`, the DAG, the decomposition map) + judge each proposed fix forward-compatible-foundation-increment vs static-state-patch.
3. **SPEC-CITED:** arm the agent with the GOVERNING DESIGN_SPEC(s) for the SPECIFIC piece it approaches (aggregator → the global-aggregator spec; rename → the identifier-retirement spec; fill-path → the fill-completeness spec) + the locked decisions for it — the dedicated spec is the checklist, the bare invariant list is a hint ([[feedback_run_dedicated_audit_skills_not_just_armed_prompts]]).

**Why:** operator-directed (2026-06-15, the `.E.1` decomposition) — *"reference the appropriate spec when we run the audits, and update the sub agents to reference those when approaching specific pieces … make them more plan and future aware."* A plan-blind + future-blind agent audits a static snapshot: it can't tell a foundation-increment from a discardable patch, re-grounds nothing, and will re-litigate a settled decision — the canonical miss was an agent re-proposing `core_N_*` cfg-key aliasing that **D-219 had already ruled against** (reclaim-not-freeze); a decision-aware agent would have honored it. The C-class decision sweep over all 223 `.E` decisions then caught two real mis-builds (cluster/node hierarchy is FOUNDATIONAL layout per D-15/D-28; snapshot epoch breaks are FREE per D-131) the by-the-plan reading missed.

**How to apply:** at every fan-out, the C-class (or orchestrator) runs the currency sweep (code-vs-HEAD + decision-log-vs-work) FIRST; build the surface→(spec + decision) map from the plan's `sister_specs` + the sweep; inject each into the spawned agents' prompts. Methodology BODY: `DESIGN_SPECS/meta-disciplines/plan-decomposition-and-future-aware-agent-arming.md` (Stage-2 DRAFT; this memory is its operator-collaboration trigger). Sisters: M8 ([[feedback_define_done_and_arm_scout_subagents]]) is the arming base; [[feedback_fix_toward_future_trajectory_not_static_state]] the future lens; the decision log is the SSoT the sweep reads.
