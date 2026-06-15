---
name: feedback_dont_generalize_substrate_before_input_space_known
description: "A substrate proven over the CURRENT instances isn't general — enumerate the PLANNED consumers' input space before declaring it universal; premature generalization locks out the future"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e94ec146-0520-406c-aacf-edaef169f6f2
  sister_specs: [feedback_adversarial_framing_default_for_checks.md, feedback_enumerate_set_before_categorical_claim.md, feedback_framework_layer_payoff_diminishing_returns.md, feedback_overengineering_boundary_when_future_easier.md, feedback_tombstone_the_name_reclaim_the_nonpersisted_bit.md, feedback_fix_toward_future_trajectory_not_static_state.md]
  tags: []
---

A data/dispatch substrate that cleanly absorbs the CURRENT set of consumers is NOT thereby a GENERAL substrate. Before declaring it the universal home for a concern — or building a registry/framework around that generality — enumerate the PLANNED consumers and check their INPUT space, not just the current ones.

**Why:** the current consumers may share a shape precisely because they are the same KIND; the planned ones may not. Declaring generality on the current sample locks the substrate into that shape and forces a break (or a parallel substrate) when the divergent consumer lands — the opposite of the maintainability the generalization was meant to buy. This is a categorical-claim-over-a-set error where the set silently shrank to "current" — sister to [[feedback_enumerate_set_before_categorical_claim]].

**How to apply:** when an audit concludes "this substrate already generalizes / the over-abstraction risk is refuted," ask: over WHICH instances? Does the roadmap name a consumer whose inputs the substrate can't express? If yes → the substrate is general for the current KIND only; consolidate within that shape and home the divergent consumer's inputs to the work that introduces it. Say "general for &lt;the current kind&gt;," never bare "general."

**Worked example (.E.0.10 gate-substrate cascade, 2026-06-14):** `GateParameters<F>` cleanly absorbs all 5 current strategies → the I-class concluded "generalization empirically refuted (the Procrustean risk is gone)." The A-class REFUTED that: the 5 are all taker-market-order strategies; the pack has zero maker/limit/queue/book-side vocabulary; ML already smuggles ~40 inputs through a separate `MLBuildContext void*`. The PLANNED maker/passive strategy (gated on real orderbook data — operator-deferred) needs queue-position / cross-vs-rest inputs the pack structurally can't carry. So the pack is general for taker OUTPUT, not a universal gate model — declaring it universal would lock out the `.E.1` multi-exchange + book-aware-fill frontier (`plans/_future/2026-06-14-book-aware-fill-model-and-microstructure-alpha.md`). The adversarial-default pass is what caught the over-claim.

Sister: [[feedback_framework_layer_payoff_diminishing_returns]] (build→consolidate→stop ADDING — this is the don't-OVER-CLAIM-generality corollary), [[feedback_overengineering_boundary_when_future_easier]], [[feedback_enumerate_set_before_categorical_claim]], [[feedback_adversarial_framing_default_for_checks]] (the A-class found it). RBP: Class 48 (the value-encoded-control instance from the same cascade).
