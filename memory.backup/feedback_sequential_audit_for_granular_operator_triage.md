---
name: feedback_sequential_audit_for_granular_operator_triage
description: "When operator needs case-by-case triage input on a multi-target audit batch, prefer sequential per-target firing over massive parallel batch — even when wall-clock cost grows"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f8d1354c-702d-4ff6-b985-c90cafb1a1f2
  sister_specs: [feedback_consult_on_audit_findings.md, feedback_plan_right_not_fast.md, feedback_evaluate_options_on_robustness_latency_design_not_time.md, user_adhd_deferred_reward_discipline.md]
  tags: [audit-methodology, operator-collaboration]
---

When firing a multi-target audit batch (multi-plan pre-coding gate, sub-sprint trajectory verification, cohort-wide retrospective audit), the default agent instinct is **parallel batch** — fire all N targets simultaneously to minimize wall-clock. Operator may prefer **sequential per-target** when granular triage matters more than wall-clock speed.

**Why:** Parallel batch saves wall time but lands all findings simultaneously → forces mass-triage which may miss context dependencies AND forces mass batch plan-body edits at the end (vs incremental sequential edits per plan). Sequential lets operator:
- Load context one target at a time
- Apply triage learnings to subsequent audits (target N+1 audit can reference target N decisions)
- Edit plan bodies incrementally instead of mass batch updates at the end
- Avoid "massive parallel thinking" cognitive load (operator-stated: "i don't have that")

Caramel works at HFT-class correctness bar where best decision per target > fastest aggregate triage. Default agent bias toward parallel-everything optimizes for the wrong variable.

**How to apply:** Before firing audit batch > 5 invocations, surface the sequential-vs-parallel trade-off explicitly. Default to **sequential per-target** when ANY of:

- Operator has stated correctness priority OR explicitly preferred granular control
- Plan bodies have cross-dependencies (one plan's amendment affects another's audit interpretation)
- Multi-cycle iteration likely (findings will change shape across cycles after amendments)
- Operator wants triage input between batches

Default to **parallel** when targets are genuinely independent (no cross-deps) AND operator wants speed AND wall-clock is the binding constraint.

**Hybrid pattern (canonical for sub-sprint audits):**

1. **Codebase-wide audits FIRST, IN PARALLEL** (since they're mutually independent + establish baseline) — `/anti-spaghetti` + `/registry-fit-audit` + `/test-strength-audit` + `/bug-check`
2. **Per-target audits SEQUENTIALLY** (one plan at a time) — operator triages each plan's findings before next plan's audit fires

This hybrid recovers ~30% of parallel speedup (Phase 1 parallel) while preserving full granular control on the high-value Phase 2.

**Worked example:** v5.15.5.F.4d.1.E.0 META audit (2026-05-28). Initially recommended "Option A: 39 parallel firings". Caramel countered: *"per plan would be better as that would let me give input and go case by case... you may have massive parallel thinking and context but i don't lol... plan by plan also allows for sequential editing instead of massive batch updates too... correctness is more valuable over speed for this domain"*. Settled on hybrid: 4 codebase-wide parallel (baseline) → sequential per-plan with operator triage between each.

**Sister:** [[feedback_consult_on_audit_findings]] (always consult; this extends discipline to BETWEEN audit granules not just after) + [[feedback_plan_right_not_fast]] (planning IS the hard part; granular triage is planning-right) + [[feedback_evaluate_options_on_robustness_latency_design_not_time]] (time is rarely the deciding factor; here correctness wins) + [[user_adhd_deferred_reward_discipline]] (operator-stated cognitive load reason).
