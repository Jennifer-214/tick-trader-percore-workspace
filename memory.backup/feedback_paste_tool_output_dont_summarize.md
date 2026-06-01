---
name: feedback_paste_tool_output_dont_summarize
description: "when a plan/doc claims a set a code-intel tool can enumerate, paste the tool output verbatim — never hand-summarize (it silently drops members); mechanized by check_plan_enumeration_completeness.py wired into /precoding-audit-gate Stage 2.5"
metadata: 
  node_type: memory
  type: feedback
  tags: [audit-methodology, enumeration-discipline, structural-fix]
  sister_specs: [meta-disciplines/meta-anti-pattern-index.md, meta-disciplines/structural-enforcement-when-memory-insufficient.md, feedback_enumerate_set_before_categorical_claim.md, feedback_run_doc_ci_tools_first_never_hand_verify.md]
  originSessionId: aef620ff-7925-4da2-bd46-c3d74632c5e5
---

When a plan body (or any doc) claims an ENUMERATION the code-intelligence tools can produce — a relocation set, a fee-site set, a boundary-cast set, a blast-radius — **paste the tool output verbatim; never hand-summarize it.** Summarizing drops members silently. It is an AR-1 instance (a categorical claim over an un-enumerated set), with a SHARP tell: the tool WAS run and the summary still lost members — *worse* than not running it, because the digest reads as verified.

**Why:** the #11 step-6 fold (`.E` Session-8, 2026-06-01) ran `gen_code_map --byte-context FPN`, then summarized its ~18 layout-assert sites into 6 — dropping `Order.hpp` + `ExecutionCore.hpp` + the Position/FlowFeatures offset ladders entirely. The step-7 re-fire's dod + completeness agents caught it (~3× under-enumeration — convergent with the fee-site and price-domain sets, the same shape thrice in one fold). Recurrence-despite-the-AR-1-note = the M7 escalation to a mechanical guard.

**How to apply:** the relocation/fee/boundary set IS the tool output, pasted — not a paragraph digesting it. Mechanized by `tools/check_plan_enumeration_completeness.py` (plan-set ⊇ tool-output; a dropped FILE = red build; has a negative self-test so the guard itself has teeth), wired into `/precoding-audit-gate` Stage 2.5 (run once per claimed set, `--section` + `--source-cmd`). Generalizes [[feedback_enumerate_set_before_categorical_claim]] from "enumerate the set" to "AND don't summarize the enumeration." Sister to [[feedback_run_doc_ci_tools_first_never_hand_verify]] (run the tool) — this adds "and paste its output, don't digest it."
