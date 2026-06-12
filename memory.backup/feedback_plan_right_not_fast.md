---
name: plan-right-not-fast
description: "Planning IS the hard part of software engineering when AI handles the mechanical coding. The human value-add concentrates in what-to-build / how-to-architect / what's-the-right-fix / what-discipline-applies — all PLANNING work. Disciplines should support decide-rightly, not decide-quickly. Indecisiveness during planning is a feature, not a bug; sitting with multiple options long enough to honestly evaluate them is what produces the right answer. Speed heuristics (\"walk menu in order + stop at first sufficient\") preempt the sitting-with-it that planning depth requires. Don't compress the planning step."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d6b9cf31-8bdc-41b7-aaf5-20e8983e9dfb
  sister_specs: [feedback_enumerate_helper_signature_args_before_extract.md, feedback_iteration_spiral_signals_audit_meta_gap.md, feedback_lead_with_architectural_merit_not_operator_tone.md, feedback_plan_body_length_no_target_loc.md, feedback_plans_have_explicit_end_goal.md, feedback_recheck_designspecs_on_pushback.md, feedback_sequential_audit_for_granular_operator_triage.md, feedback_session_decision_log_discipline.md, feedback_tiered_audit_discipline_per_plan_scope.md, project_e_series_is_vision_convergence_not_scope_balloon.md, feedback_design_once_maintain_forever.md, user_correctness_first_not_ship_fast.md, feedback_planning_treadmill_bias_to_execution.md]
  tags: [planning-discipline, operator-collaboration]
---

In the era of AI-assisted coding, the typing part is fast + mechanical. The human value-add concentrates in PLANNING:

- **What to build** (product judgment)
- **How to architect** (design judgment)
- **What's the right fix for this issue or tech debt** (engineering judgment)
- **What discipline applies here** (meta-judgment)

All of these are planning work. The coding that follows is largely mechanical given a good plan. So **disciplines should support decide-rightly, not decide-quickly.**

## Indecisiveness is a feature during planning

Genuinely sitting with multiple options — turning each over, evaluating honestly, comparing on the right axes — is what produces right answers. Speed heuristics that preempt this ("walk menu in order + stop at first sufficient", "auto-pick the future-oriented option", default-to-X reflexes) can be useful in routine decisions, but they're the WRONG shape for planning-grade decisions where the stakes justify sitting with the problem.

The cost of indecisiveness in planning is small: maybe an extra hour or session weighing alternatives.
The cost of decide-quickly in planning is high: you build the wrong thing OR fix the wrong way OR add an abstraction that doesn't earn back.

When operator surfaces a planning question, the right response is usually: **present the full option set + evaluate each honestly + then pick.** Not: pick the first option that meets the bar. The first option that meets the bar might not be the option that's actually right.

## How to apply

1. When recommending a response to a finding / decision / audit catch:
   - **Present the full option set first**, not your pre-filtered favorite
   - **Evaluate each option honestly** on the axes that matter (robustness, latency, design alignment, future-ease, maintenance cost) per `feedback_evaluate_options_on_robustness_latency_design_not_time`
   - **Don't auto-pick first sufficient**. Sufficient is a low bar. Pick what's right.
   - Reach for `feedback_auto_pick_future_oriented` only when the trade-off is genuinely clear; surface ambiguity when it isn't

2. When operator wants to sit with a decision, **support that.** Don't drive toward closure. The "stop walking" framing is for AFTER planning produces the right answer, not for shortcutting the planning itself.

3. Disciplines codified in memories + DESIGN_SPECS should ENABLE planning depth, not compress it:
   - "Walk menu in order, stop at first sufficient" — speed bias; **DROP this framing**
   - "Expand the option set; evaluate each honestly; pick what's right" — planning-depth framing; **KEEP this framing**
   - Mechanical filters (e.g., sites-added vs sites-eliminated) are INPUTS to honest evaluation, NOT triage shortcuts

4. When tempted to consolidate options into a single recommendation, ask: "Does presenting multiple options + my honest reasoning produce better planning outcomes than just giving the answer?" Usually yes for non-trivial decisions.

5. Coding speed isn't the bottleneck anymore. Planning depth is. Optimize the discipline for the bottleneck.

## What this DOESN'T mean

- Doesn't mean perpetual indecisiveness. At some point planning produces a decision + execution starts. The "stop planning, start building" moment is real — but it should come from "we've evaluated and have the right answer", not from "we walked the menu and the first option was sufficient".
- Doesn't mean refusing to recommend. Recommendations are useful inputs to planning. But recommendations should expose the alternatives + reasoning, not just present the chosen answer.
- Doesn't mean infinite scope. Planning depth is for the DECISION; the scope of work that follows can still be tight.
- Doesn't override `feedback_audit_update_implement_ship_cycle` (per-sub-ship cycle prevents endless planning loops). Each sub-ship gets one cycle of audit→triage→implement→ship; within that cycle planning depth applies; across sub-ships forward motion still happens.

## Sister memories

- `feedback_proportionate_response_to_audit_findings` — companion; this memory provides the speed-bias-removal framing applied to that discipline
- `feedback_evaluate_options_on_robustness_latency_design_not_time` — the axes for honest evaluation
- `feedback_auto_pick_future_oriented` — applies when trade-off is genuinely clear; doesn't apply when planning depth needed
- `feedback_consult_on_audit_findings` — present findings + iterate; this discipline strengthens the "iterate" part (don't drive to closure)
- `feedback_overengineering_boundary_when_future_easier` — still applies as one input among many; not a fast-decision shortcut
- `feedback_dont_measure_structural_work_by_loc` — speed/LOC aren't the right metrics; planning quality is
- `feedback_motivated_collaborator_for_caramel` — high-quality planning IS what motivated collaboration looks like for Caramel's workflow

## Codification trigger

Originally codified after a discipline-rewrite session where operator surfaced that the codified discipline had speed bias baked in ("walk menu in order + stop at first sufficient") — and that bias was counter to her workflow where planning depth IS the value-add. Quote: "i feel like some indecisiveness is needed for this, its how i get the right fixes i think... yeah at some point i need to stop planning, but also planning is the hard part of SWE now, not the actual coding... i wanna make sure i plan right, not fast." The meta-lesson: speed heuristics codified for planning-grade decisions actively undercut the value of planning. Disciplines for planning should ENABLE depth, not compress it.
