---
name: feedback_implement_reconcile_decision_code_binding
description: A captured decision that specifies a code behavior is a CONTRACT — bind it to a non-vacuous pinning test; reconcile decision-log+test in the same step if implementation deviates
metadata: 
  node_type: memory
  type: feedback
  originSessionId: bc02bbd3-9c3f-452a-8839-f8da50d3bd1d
  sister_specs: [feedback_deferral_reasons_merit_not_effort_or_context.md, feedback_no_defer_for_effort.md, feedback_passing_test_is_not_verification.md, feedback_structural_enforcement_when_memory_insufficient.md]
  tags: []
---

A decision-log entry that specifies a CODE BEHAVIOR (a refuse / flip / default / gate / mechanism) is a CONTRACT the code + test must match — or the deviation is RE-CAPTURED immediately. Two failure modes this closes:

1. **Silent deviation during implementation.** When coding reveals the decided mechanism is impractical (e.g. a hard-refuse the loader can't cleanly halt on), the path of least resistance is to code a *different* behavior that "also works" and move on — WITHOUT looping back to the decision-log. That is an **effort-driven deviation from a merit-decided behavior** ([[feedback_no_defer_for_effort]] / [[feedback_deferral_reasons_merit_not_effort_or_context]] applied to a DEVIATION, not a defer — so no defer-trigger fires). Execution-mode momentum in a long session amplifies it (more distance between deciding and coding) — but the long session, not compaction, is the amplifier; the deviation itself is a discipline lapse.
2. **The pinning test is vacuous.** A test that asserts a WEAKER outcome (e.g. `!IsLiveCapital`, true for BOTH the decided hard-refuse AND the coded explicit-wins) does not distinguish the behaviors → a green test HIDES the drift. The non-vacuous discipline ([[feedback_passing_test_is_not_verification]] / characterization-test-discipline) must apply to DECISION-pinning tests: assert the MECHANISM the decision specified, not a safe-looking proxy.

**Why:** the capture system verifies decisions are RECORDED (the mechanical `check_session_docs` checks index/sentinels/structure) but NOT that they are IMPLEMENTED AS RECORDED — a code-vs-decision SEMANTIC drift sails straight through a green sweep. Caught only by an operator's "are you sure?" (D-218, NEW-1 conflict-handling: D-217 said hard-refuse; the code did explicit-wins; the test was vacuous so it passed).

**How to apply:** (1) Every behavior-specifying decision gets a NON-VACUOUS characterization test that pins THAT exact behavior — the test IS the decision↔code enforcement (drift → test failure). (2) If implementation deviates from a captured decision, reconcile the decision-log + the test in the SAME step; never ship a silent deviation. (3) Candidate semi-mechanical check: scan the decision-log for behavior-keywords (REFUSE/halt/blocks/must/sets/gates) lacking a referencing test → flag for semantic review (the has-a-test half is greppable; the semantic match is judgment). M7 structural-enforcement escalation ([[feedback_structural_enforcement_when_memory_insufficient]]).
