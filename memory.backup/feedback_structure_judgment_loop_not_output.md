---
name: structure-judgment-loop-not-output
description: "Caramel's apparatus thesis (codified 2026-06-09, mid-A.5; D-166): verification/planning skills carry the leverage; maker/scaffold skills earn their keep ONLY by standardizing input shape so the verifiers can bite. The model is a strong generator + weak self-verifier — tool the weak half (self-attestation, fabrication, staleness, compaction-loss, completeness blindness), leave the strong half raw. Scaffolds make artifacts LEGIBLE; gates make them CORRECT; the leverage lives in the gates. Candidate central thesis of the workspace-template release: structure the AI's JUDGMENT LOOP, not its output."
metadata: 
  node_type: memory
  type: feedback
  sister_specs: [feedback_guards_compound_enforcement_is_leverage.md, feedback_independence_for_judgment_not_mechanical.md, user_structure_is_correctness_risk_control_for_capital.md, feedback_run_doc_ci_tools_first_never_hand_verify.md, feedback_define_done_and_arm_scout_subagents.md]
  tags: [operator-collaboration, audit-methodology]
  originSessionId: 687aa85a-836d-488f-8cb8-2ee60d314782
---

**Structure the AI's judgment loop, not its output.** Verification/planning skills (gates, audits, mechanical floors, completeness critics) are where the apparatus leverage lives; maker/scaffold skills add marginal value on top of what an LLM already does natively — fluent artifact production.

**Why (the structural reason):** the model is a strong generator and a weak self-verifier. Maker skills tool the strong half. Planning/verification skills target the actual binding constraints: self-attestation bias, fabrication, staleness, context death at compaction, completeness blindness. Most of the industry did the opposite — wrapped generation in templates and ignored verification — and the typical result is vibe-code. Same tool, divergent outcomes; the divergence lives almost entirely in the verification layer.

**The asymmetries stack:** a gate protects a whole CLASS of errors forever ([[feedback_guards_compound_enforcement_is_leverage]]); a scaffold saves minutes once per artifact. On a capital-bearing codebase the cost asymmetry compounds it — wrong-but-fast is a LOSS, so verification ROI dominates generation ROI in a way it wouldn't on a CRUD app.

**Receipts (the 2026-06-09 controlled experiment — one session):** `/accept-handoff` caught 3 drift items at pickup (unfulfilled D-159 memory promise; D-156 sentinel contradicting the actual ship diff; stale CLAUDE.local row). The gate + standing completeness critic caught: a dead acceptance gate citing a retired tool; two Python guard sites the compiler oracle can't see; a guard failing blind-green instead of red; a stale "24 bytes" claim in REQUIRED READING that survived the previous sweep; an existing doc-rename executor the generator missed in its own sister-scan. The mechanical floor caught the generator's undefined tag. Meanwhile `/plan-draft` wasn't even invoked — the draft came straight from the template.

**The nuance (keep it honest):** maker skills that earned their keep did it by smuggling planning discipline inside. `/plan-draft`'s real value is the template's REQUIRED SECTIONS (canonical-sister, design-space, end-goal) — which exist to make the artifact GATE-ABLE. `/doc-create` became load-bearing only when D-120 bolted the cohort-grep guard onto it. So the formulation is not "maker skills failed" — the makers' actual job is standardizing the input shape so the verifiers can bite, and every surviving maker skill converged toward that role.

**How to apply:**
- New apparatus investment → default it to the verification layer (a gate/guard/critic), not the generation layer (a scaffold/template), unless the scaffold's purpose is explicitly to make artifacts gate-able.
- Evaluating an existing maker skill → ask "what gate does its output shape feed?"; a scaffold feeding no verifier is decoration.
- Sisters: [[feedback_independence_for_judgment_not_mechanical]] (who runs the check), [[feedback_run_doc_ci_tools_first_never_hand_verify]] (mechanical floor first), [[user_structure_is_correctness_risk_control_for_capital]] (why the apparatus exists at all).

**Forward home:** candidate central thesis of the eventual `workspace-template` release; fold a crisp statement into `DOCS/DESIGN_PHILOSOPHY.md` § 11 (process discipline) at a natural doc boundary — the answer ready for hedge-fund eyes asking why this setup works.
