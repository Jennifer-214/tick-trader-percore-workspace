---
name: feedback-future-headache-vs-optimization-scope-framework
description: "When scope discoveries surface during refactor/cleanup ships, the axis for include-vs-defer is \"does this reduce FUTURE HEADACHE\" not \"is this MORE WORK NOW\". Future-headache reducers grind through; pure performance optimizations skip + document. Caramel's framework for scope decisions on consolidation ships."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: ba5429a9-2f65-4f8d-950c-3ae250973f24
  sister_specs: [feedback_no_defer_for_effort.md, feedback_motivated_collaborator_for_caramel.md, feedback_evaluate_options_on_robustness_latency_design_not_time.md, feedback_overengineering_boundary_when_future_easier.md, feedback_framework_layer_payoff_diminishing_returns.md, feedback_opportunistic_tech_debt_closure.md]
  tags: [scope-discipline, audit-methodology]
---

When scope discoveries surface mid-ship (e.g., TECH_DEBT-104 surfaced ~5 surviving anti-pattern instances at model-state cohort during `.B.3` pre-coding verification), the right axis for include-vs-defer is:

**FUTURE HEADACHE REDUCERS → CLOSE AT THIS SHIP**
- Anti-pattern instances that future feature work will collide with
- Inconsistencies that make codebase harder to navigate for future contributors
- Mirror/parallel structures that future bug fixes have to update in N places
- Discipline gaps that grow worse as more code lands on top
- Anything that increases cost of future understanding/modification

**PURE PERFORMANCE OPTIMIZATIONS → SKIP + DOCUMENT AS TECH_DEBT**
- Latency improvements that don't affect correctness
- Slow-path cycle reductions (not hot-path)
- Memory layout tweaks for cache when not paired with correctness gain
- Micro-optimizations with diminishing returns per `feedback-framework-layer-payoff-diminishing-returns`

**Why:** Codified 2026-05-17 at `.B.3` v1.6 pre-coding gate. Caramel's exact framing: "we should close them out if they reduce future headache, if theyre just optimziations we can skip that right now and just document, this refactor is about cleaning up messy code and making it future maintainable". Applied to:
- TECH_DEBT-104 (5 surviving Class 32 instances at model-state cohort) → **CLOSE** (future ML feature work would collide with prefix asymmetry; reduces future headache)
- TECH_DEBT-103 (locale-pin optimization in cfg_emit_field) → **DEFER + DOCUMENT** (pure slow-path perf optimization; no future-headache reduction)

Both deferrals had structural rationale on the surface, but applying this framework cleanly distinguished them: TECH_DEBT-104 is anti-pattern-instance-survival (future-headache); TECH_DEBT-103 is cycles-eliminated (optimization).

**How to apply:** When evaluating TECH_DEBT entries or scope expansions during refactor/cleanup ships:

1. **Identify the underlying concern.** Is it (a) an anti-pattern instance surviving / inconsistency that creates future-headache, or (b) a performance opportunity?
2. **For (a) future-headache reducers:** GRIND THROUGH at the current ship. Per `feedback_motivated_collaborator_for_caramel` — when tempted to defer for effort, ask "would a motivated engineer skip this on a cleanup ship?". No.
3. **For (b) performance optimizations:** DEFER + open TECH_DEBT entry with target-ship-TBD. Document the optimization for future review when latency profile justifies.
4. **Honest verdict per item** — don't conflate. Apply framework cleanly.

**Recognition markers:**
- "Different concern" framing for deferring scope expansion → STOP; apply framework. Different concern is structural-rationale-IF the concern genuinely diverges; if the same anti-pattern applies, "different concern" can be effort-avoidance dressed up.
- "Slow-path optimization" framing → likely (b); usually safe to defer + document
- "Future feature work will collide" → (a); usually grind through
- "Adds parallel mirror to surviving instances" → (a); grind through

**Trade-off vs `feedback_framework_layer_payoff_diminishing_returns`:** that memory says STOP adding framework layers past inflection. This memory says CLOSE anti-pattern instances when reducing future headache. Both apply at consolidation phase: don't ADD new framework infrastructure (per framework-payoff); DO close existing anti-pattern instances at the existing framework surfaces (per this memory). Distinct: framework-payoff is about whether to LAYER MORE; future-headache is about whether to CLOSE LIES IN PLACE.

**Sister memories:**
- [[feedback-no-defer-for-effort]] (last-ditch defer; this memory adds the WHAT distinguishes effort-defer from rational-defer)
- [[feedback-motivated-collaborator-for-caramel]] (quality bar; this memory applies it to scope expansion decisions)
- [[feedback-evaluate-options-on-robustness-latency-design-not-time]] (evaluation axes; future-headache is robustness/design axis applied to scope decisions)
- [[feedback-overengineering-boundary-when-future-easier]] (sister principle — future-work-much-easier multiplier when borderline)
- [[feedback-framework-layer-payoff-diminishing-returns]] (when to stop adding framework layers; companion at consolidation phase)
