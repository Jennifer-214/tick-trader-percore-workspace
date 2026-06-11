---
name: feedback_passing_test_is_not_verification
description: "A green/passing test proves only that the assertion-as-written holds on the input-as-written — NOT that it's the right invariant, complete, or non-vacuous. Adversarially verify your OWN characterization/test work (complete · non-vacuous · not-a-frozen-bug) before declaring it done. Self-attesting a green suite is the trap; green is a proxy, not the verdict."
metadata: 
  node_type: memory
  type: feedback
  tags: [audit-methodology, test-discipline]
  originSessionId: 3e806606-ac69-40fd-ac33-45906443bae4
  sister_specs: [feedback_adversarial_framing_default_for_checks.md, feedback_enumerate_set_before_categorical_claim.md, feedback_golden_master_over_reimplemented_oracle.md, feedback_independence_for_judgment_not_mechanical.md, feedback_single_source_the_computation_not_just_the_mode.md, feedback_verify_by_context_not_count.md]
---

A green suite is NOT verification of the TEST — it verifies that the assertion you wrote holds for the input you wrote. It is silent on the three things that matter: is the assertion the RIGHT invariant (does it hold in general, not just on the clean test input)? is it COMPLETE (does it cover the whole set it claims)? is it NON-VACUOUS (would it FAIL if the behavior were wrong)? That's AR-4 verification-by-proxy operating at the test-WRITING layer — the proxy (green) read as the verdict (correct + complete).

**Why:** at `.E.0.10` I declared 3 money-core characterization tests "done green" (3288/0). An operator-forced ADVERSARIAL audit found 2 of 3 broken: one froze a FALSE invariant (an exact `Money_Eq` reconciliation that holds only on rounding-clean inputs — 25% of realistic inputs diverge by 1 ULP); one was vacuous (`Portfolio_CountActive >= 1` passed even though 2 of 3 replayed fills were silently dropped); the third asserted 1 of 9 persisted money fields. A self-audit (run the suite + eyeball) would have confirmed all three green. The green check ANESTHETIZED the rigor — the disciplines that would have caught it (enumerate-the-set, anti-self-attestation, golden-master) didn't fire because nothing TRIGGERED them on "I wrote a test + it's green."

**How to apply:** the moment a characterization/test you wrote goes green is NOT "done" — it's the trigger to run the 3 adversarial lenses (complete / non-vacuous / not-a-frozen-bug), preferably by INDEPENDENT eyes (anti-self-attestation; the builder confirms intent, not correctness). On capital/determinism surfaces this is mandatory, not optional. Green is a locator that the path runs, never the verdict that the test is right. Sister: [[feedback_independence_for_judgment_not_mechanical]] · [[feedback_golden_master_over_reimplemented_oracle]] · [[feedback_enumerate_set_before_categorical_claim]] · [[feedback_verify_by_context_not_count]].
