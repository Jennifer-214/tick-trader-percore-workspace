---
name: feedback_define_done_and_arm_scout_subagents
description: A close terminates only when an enumerated Definition-of-Done is verified by a full-context scout-first subagent — not by trickle-discovery
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b95e8b66-07b9-4970-ade6-d4cac233848d
  sister_specs: [feedback_adversarial_framing_default_for_checks.md, feedback_auto_route_input_to_matching_skill.md, feedback_capture_and_check_are_model_bounded.md, feedback_passing_test_is_not_verification.md, feedback_structure_judgment_loop_not_output.md, feedback_a_class_i_class_fanout_vocab.md]
  tags: []
---

The find-gap → fix-gap → find-more loop that never terminates has TWO joined root causes; closing a ship completely needs both fixed.

**1. No enumerated Definition of Done (the criteria half).** "Closed" gets declared on whatever was thought of — always a SUBSET — so the tail is whatever wasn't. A fix-ship close is DONE only when EVERY dimension is green: code fixed · a char-test per fix · sanitizers run (`run_all_tests.sh --full`) · every register/disposition row flipped to LANDED · MASTER banner + handoff pointer current · PARITY entry written for any parity finding · every "owed at close" promise honored · every spawned obligation homed (TECH_DEBT / future plan / register) · docs indexed (`rebuild_doc_indexes`) · meta-lessons codified. The criteria are otherwise implicit + discovered-as-you-go (each gap teaches a new dimension) → enumerate them as a CHECKLIST and let the gaps found become its rows.

**2. Verification fires blind (the awareness half — M8).** A freshly-fired subagent boots with NOTHING but its prompt — no CLAUDE.md/MEMORY/invariants/TOOLS.md/nav-infra. Its accuracy is hard-capped by what got loaded. Arm every audit/verify subagent with **full workspace awareness + the surface's reference docs + the mechanical toolchain (the `check_*.py` to RUN, grep patterns) + the nav-infra (CODE_MAP/DAG) + the domain skill**, and have it **SCOUT its surface BEFORE executing** the directive (load → scout → then execute), so it doesn't tunnel-vision the narrow ask and miss the surroundings. EXCEPTION: withhold the orchestrator's CONCLUSION from ADVERSARIAL agents — parity on FACTS+TOOLS, independence on the VERDICT (a blind subagent is a confident subagent, the dangerous kind).

**Why:** the F1 AUTO-core bug + the stale trackers + the untested A28 all rode to "closed" at `.E.0.10` because (a) no DoD enumerated "char-test per fix / every tracker flipped / producer-not-just-test verified", and (b) the verify subagents got thin prompts (the char-test agent was structurally blind to the producer). The deep check caught everything ONLY because it was armed (mechanical tools + A1 cross-check) + separated by concern. This is the M7 escalation of AR-8 (mechanical-green ≠ semantically-complete recurred despite codification) + the generalization of the nav-infra-cohort rule (we arm the handoff RECEIVER; we never armed SUBAGENTS).

**How to apply:** (1) Run ONE armed scout-first comprehensive pass against the DoD checklist to enumerate the COMPLETE remaining set in one shot — never trickle-discover. (2) Home ALL of it (finish-now or handoff) + STOP at a clean boundary — extending the session instead of defining-done-and-stopping IS the loop. (3) When firing any verify/audit subagent, load context+tools+nav-infra+domain-skill into the prompt; tell it to scout first. Sisters: [[feedback_adversarial_framing_default_for_checks]] · [[feedback_auto_route_input_to_matching_skill]] · [[feedback_passing_test_is_not_verification]] · [[feedback_structure_judgment_loop_not_output]] · [[feedback_capture_and_check_are_model_bounded]].
