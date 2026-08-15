---
name: feedback_resource_use_gated_on_existence_not_felt_need
description: "Default to the curated resource (tool/skill/spec/decision-log/agent) on EXISTENCE not felt-need; on a gap EXTEND the tool/skill, don't work around — the operator-independent, self-improving surface (rides M7 escalation + M8 arming)."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: a9f02eea-b737-43be-9dda-4497b9a95922
  sister_specs: [feedback_adversarial_framing_default_for_checks.md, feedback_audit_canonical_sister_before_new_infra.md, feedback_capture_and_check_are_model_bounded.md, feedback_consult_indexes_before_full_reads.md, feedback_ground_design_in_real_code.md, feedback_guards_compound_enforcement_is_leverage.md, feedback_recheck_designspecs_on_pushback.md, feedback_run_cascade_upfront_for_rename_and_registry.md, feedback_run_doc_ci_tools_first_never_hand_verify.md, feedback_structure_judgment_loop_not_output.md, user_structure_is_correctness_risk_control_for_capital.md, feedback_comments_point_in_time_verify_against_code.md]
  tags: []
---

The operating discipline for the whole apparatus, as one loop:

1. **Default to the curated resource, gated on its EXISTENCE — not felt-need.** Whether to reach for a `check_*` tool, a skill, a DESIGN_SPEC, an anti-pattern class, a prior decision (the decision log), or an armed agent must NOT be gated on *"do I feel I need it?"* — that gate is systematically wrong. The resource EXISTS because that surface is error-prone for unaided reasoning, so felt-need is least reliable exactly there: solo reasoning feels identical whether right or wrong, so "do I need it?" returns "no" precisely when the answer is "yes." The failure is invisible from the inside. Treat the resource as the evidence you reason FROM, not optional confirmation of a conclusion already reached.

2. **Route tooled-surface investigation/verification through ARMED agents** — this is **M8** (`definition-of-done-and-armed-scout-verification`; `SUBAGENT_ARMING` §3 = tools-first). Armed agents boot toolchain-first and lack the discretionary skip — WHY the agent legs of a sweep outperform the solo legs.

3. **On a gap (the resource doesn't cover the case), EXTEND the resource — don't work around it.** A gap is a signal to grow the shared surface, not to solve it ad-hoc in one session's head. This is the continuous-mode of **M7** (`structural-enforcement-when-memory-insufficient`; the 6-stage memory→audit→CI-tool→pre-commit lifecycle) — M7 fires on *recurrence*; the standing default is "every gap is an extend-the-tool opportunity." The surface stays coherent via `check_tools_inventory.py` (every tool = a `TOOLS.md` row) + H15 registry-coverage.

**Why (both load-bearing):** (a) capture-and-check are model-bounded ([[feedback_capture_and_check_are_model_bounded]]); the resources ARE the deterministic/independent backstop ([[feedback_adversarial_framing_default_for_checks]]). (b) **Operator-independence / portability** — the tool/skill surface works the SAME no matter who (which model, which session, which contributor) is at it; extending the tool compounds a shared substrate, a workaround creates one-off knowledge that dies with the session. This is the framework-driven philosophy (CLAUDE.md § 1.5, 1-row-auto-flow) + the `workspace-template` product thesis ([[feedback_structure_judgment_loop_not_output]], [[user_structure_is_correctness_risk_control_for_capital]], [[feedback_guards_compound_enforcement_is_leverage]]).

**Proof (`.E.1.2` sweep, 2026-07-03):** every tool/armed-agent run gave ground truth or caught an error; both solo-reasoned conclusions (defer-serializer-to-E.1.3; born-struct-generate NodeState) were confidently wrong — and both were ALREADY answered by resources not consulted first (the cascade = 0 containers; decision log D-283/D-287 showed born-generation's flag already refuted; OMS was the canonical sibling). D-290 (tools-over-grep) had to be codified AND was still under-applied the same session → memory-tier alone insufficient (hence the M7 escalation + this always-loaded default).

**Sisters — this GENERALIZES them from single-resource-types to the whole surface:** [[feedback_run_doc_ci_tools_first_never_hand_verify]] (tools), [[feedback_recheck_designspecs_on_pushback]] + [[feedback_audit_canonical_sister_before_new_infra]] (specs/anti-patterns), [[feedback_consult_indexes_before_full_reads]] (indexes), [[feedback_ground_design_in_real_code]] (code), + D-290. M7 = the escalation mechanism (§3); M8 = the arming (§2).

**Worked instance (2026-08-15, E.1.2/D-421 close-out) — the third recurrence at the same surface.**
I hand-rolled a 20-commit close instead of invoking `/close-session`. Every individual step I chose
looked sufficient at the time; the skill's Stage 5.5 item 7 names CODE_MAP staleness *by name* and
Stage 7.5 invokes the close-out guard, and I did neither because I did not FEEL I needed to — the
mechanical sweep was green. It was green while six reference-doc auto-writes were missing, one of
which I had named as owed mid-session and then dropped.

The felt-need signal was not merely weak, it was **actively inverted**: the greener the mechanical
sweep, the less need I felt for the judgment half — which is precisely the half the sweep cannot
see. That is the calibration failure this memory names, and the reason the rule is EXISTENCE-gated
rather than need-gated. Detector, all three times: the operator asking.
