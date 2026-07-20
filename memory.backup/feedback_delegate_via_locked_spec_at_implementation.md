---
name: feedback_delegate_via_locked_spec_at_implementation
description: design = hands-on solo (un-delegatable taste/decisions); implementation = agents INFORM, the main session WRITES — never delegate code authoring, even against a locked spec; the tag-system docs ARE the delegation substrate
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 9f2efedc-135a-42ff-a6c6-e3c32c03b1af
  sister_specs: [feedback_consult_on_audit_findings.md, feedback_delegate_on_total_oracle_handreview_on_partial.md, feedback_independence_for_judgment_not_mechanical.md, feedback_passing_test_is_not_verification.md, feedback_structure_judgment_loop_not_output.md]
  tags: []
  modified: 2026-07-20T06:27:00.088Z
---

Caramel repeatedly wishes for "a system to coordinate multiple agents" but doesn't want to build that framework + doesn't want to lose visibility ("I don't know what all is being done"). The resolution, by phase:

- **DESIGN phase → hands on everything.** The taste, the vision, the format/architecture decisions ARE the product — un-delegatable — and she's building her own understanding, which delegation would rob. During design: consult + co-decide, do NOT fan out.
- **IMPLEMENTATION phase (once the spec is LOCKED) → agents INFORM; the main session WRITES.** The coordination "system" she wishes for IS the locked spec (north-star / taxonomy / decision-log). Fan out for **information** — surface mapping, reference digests, currency sweeps, adversarial verification. Everything lands in the docs so she keeps visibility.

> **⚠️ CORRECTED 2026-07-20 (direct operator instruction).** This memory previously read *"implementation phase → it parallelizes"* and told me to *"offer to fan out agents once the design is locked."* **That is wrong for CODE AUTHORING and caused real problems.** Her words: *"dont let sub agents code this, do it in the top level one please, we only use subagents for info and other things, as problems pop up more when we delegate that to subagents."* A locked spec makes work *specifiable*; it does not make a subagent's code *trustworthy*.

**Why:** it dissolves the tension (control-and-understanding vs speed) by splitting it across phases + naming the spec as the coordinator — while keeping the edit surface in one place. The correction is **empirically derived, not cautious**: it is the hardening of [[feedback_delegate_on_total_oracle_handreview_on_partial]] (M10). M10 says delegate on a TOTAL oracle and hand-review on a PARTIAL one; the observed failure rate on delegated *authoring* says the code-writing case does not clear that bar often enough to be worth the retry cost — the canonical instance being the `0.3` plugin cutover, where 12/12 unit tests, a parity section and a green doc-CI sweep were ALL green while a hand read still found two real defects (a per-token subprocess storm, a hardcoded repo name in a publishable plugin), neither expressible as a test assertion. Delegated code also fragments the reviewer's context exactly where continuity is load-bearing.

**How to apply:** during a design/decision cycle, don't propose fanning out; co-decide. Once the spec is LOCKED, fan out **agents that read, map, verify, and report** — never agents that edit. Write every code change in the main session, where the accumulated context lives. Do NOT offer to "parallelize the implementation." And carry the meta she landed: **a tagged/documented codebase IS the delegation substrate** — building the tag system builds the very thing that makes handing work to an agent (or a future hire) safe, because they read the tags instead of needing her. Sisters: [[feedback_structure_judgment_loop_not_output]] · [[feedback_independence_for_judgment_not_mechanical]] · [[feedback_consult_on_audit_findings]] · [[feedback_passing_test_is_not_verification]].
