---
name: feedback_deferral_reasons_merit_not_effort_or_context
description: "do-now-vs-defer is decided on MERIT (correctness-risk / scope-boundary / proof-burden / marginal-cost); the AI's effort or \"we have context loaded\" is NOT a valid axis"
metadata: 
  node_type: memory
  type: feedback
  tags: [operator-collaboration, scope-discipline]
  originSessionId: 51696014-e078-4937-8012-21dd2596cc14
  sister_specs: [feedback_design_once_maintain_forever.md, feedback_evaluate_options_on_robustness_latency_design_not_time.md, feedback_listen_and_execute_simply.md, feedback_opportunistic_tech_debt_closure.md]
---

When deciding whether to do an adjacent/future item NOW vs defer it, the discriminator is MERIT only: correctness risk (correct-by-construction vs correct-by-verification), scope / tag-boundary cleanliness, value-equivalence / determinism proof burden, and subsumption-vs-adjacency marginal cost ([[feedback_opportunistic_tech_debt_closure]]). "We have context loaded" / "it's a focused sitting" / "it's a real chunk of work" is NOT a valid axis — the AI's effort and time are not real costs and must never enter the decision.

**Why:** Caramel caught me importing a human effort cost model ("a focused sitting," "not free-with-context") to justify deferring a branchless `FromString` rewrite — illegitimate for an AI that generates code instantly. And "we have context" is almost always true (you're always adjacent to *something*), so as a literal rule it justifies pulling anything into anything. The honest discriminators are the merit ones; the value-equivalence diff-test was the real gate, and it passed (297/0) → the rewrite belonged in now.

**How to apply:** State deferral reasons in merit terms only. If the only thing arguing for defer is effort/context, that is not a reason → do it now, gated on the real constraint (e.g. prove value-equivalence with a differential test before it ships). When I catch myself writing "a focused sitting / a real sitting / not free-with-context / a real chunk of work," delete it — it is a relatability tell, not an argument. Genuine non-effort deferral reasons still hold (a distinct algorithm needing its own proof; muddying a clean tag boundary; an over-read safety wall). Sister: [[feedback_evaluate_options_on_robustness_latency_design_not_time]] (time isn't the deciding factor — generalized: neither is MY effort), [[feedback_opportunistic_tech_debt_closure]], [[feedback_design_once_maintain_forever]], [[feedback_listen_and_execute_simply]].
