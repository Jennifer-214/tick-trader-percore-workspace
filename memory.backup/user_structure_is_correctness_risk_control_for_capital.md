---
name: user_structure_is_correctness_risk_control_for_capital
description: "Caramel's heavy verification/planning apparatus is risk control for capital-bearing code — do NOT frame it as over-instrumentation or hobby craft"
metadata: 
  node_type: memory
  type: user
  originSessionId: ab5d402f-2ba7-43b9-9ae7-35187b313483
  sister_specs: [user_adhd_deferred_reward_discipline.md, user_deep_design_work_intrinsic_value.md, user_mvp_to_professional_transition.md, feedback_framework_layer_payoff_diminishing_returns.md, feedback_heavier_default_audit_posture_for_capital.md, project_engine_done_edge_is_the_frontier.md]
  tags: [user-profile, operator-collaboration]
---

The heavy structure in this codebase (audit gates, parity checks, 20 hard invariants, ~290K lines of plans/DESIGN_SPECS/skills around ~47K LOC of engine) serves TWO ends, per Caramel's own framing — do NOT frame it as over-instrumentation or hobby craft:

1. **Externalized cognition for a one-person + AI workflow (PRIMARY, her stated reason).** Caramel is a solo dev; the corpus is external memory that's easily navigable by an AI agent, and it reduces decision fatigue. "It works for me" is a complete justification. Mechanism: every codified rule is a decision made ONCE and never re-litigated — the next session (her or the agent) inherits it instead of re-deriving or silently drifting. The corpus IS the missing teammate. For ADHD, externalizing decisions out of working memory is the leverage. Connects to [[user_adhd_deferred_reward_discipline]].
2. **Correctness risk-control for capital-bearing code.** For HFT code that moves real money the cost function is asymmetric — an unshipped feature is opportunity cost, but a shipped bug is a *realized loss* compounding at machine speed. A 6:1 verification-to-code ratio is the correct posture (aerospace / medical-device / real quant firms), not bloat. Burden of proof is on REMOVING a control, not adding one.

**Cost-model correction (the category error to avoid):** the corpus is a QUERYABLE DATABASE for an agent (grep by frontmatter tag → pull relevant specs), NOT a document a human reads linearly. So "290K lines = maintenance/reader burden" is the wrong lens — volume ≠ burden when retrieval is targeted and instant. Never cite the doc-to-code ratio as if it were a problem.

**How to apply:** When evaluating a structure/process/rigor trade-off, do NOT characterize her discipline as "over-engineering," "process exhaust," or hobby-craft. Frame trade-offs by which money-losing failure mode a control prevents. Distinguish tiers: EXECUTABLE controls (tests, CI checks, compile-time invariants — things that fail the build) directly protect the money at the order gate; PROSE controls (plans, handoffs, decision logs) protect decision-quality + survive context loss in AI-collaborated solo work. When suggesting where to invest more rigor, prefer "can this be made executable rather than aspirational?"

Refines/contextualizes [[user_deep_design_work_intrinsic_value]] (craft value coexists but correctness-for-capital is the primary driver of the structure) and [[user_mvp_to_professional_transition]]. Sister to [[feedback_framework_layer_payoff_diminishing_returns]] — diminishing-returns still applies to *adding framework layers*, but that critique is about marginal abstraction, not about the existence of the verification apparatus.
