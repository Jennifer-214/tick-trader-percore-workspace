---
name: feedback_capture_and_check_are_model_bounded
description: "Self-check AND document-as-you-go are MODEL-BOUNDED — both run within your mental model of a change's footprint, so neither catches OUT-OF-MODEL sites (the coupled index/pointer/sibling/elsewhere-ledger you didn't model as in-scope). Only EXTERNAL enumeration catches those: an independent reviewer (a different model) or a structural full-set guard. The deepest M7 why."
metadata: 
  node_type: memory
  type: feedback
  tags: [audit-methodology, meta-discipline]
  sister_specs: [feedback_document_as_you_go_over_catch_at_end.md, feedback_structural_enforcement_when_memory_insufficient.md, feedback_adversarial_framing_default_for_checks.md, feedback_sister_cohort_amendment_completeness.md, feedback_passing_test_is_not_verification.md, feedback_define_done_and_arm_scout_subagents.md]
  originSessionId: eb863fe9-13c6-448b-b458-ba72b5419c75
---

Why does the same drift keep getting MISSED in-flight and caught only at the close (or by operator pushback)? Because every discipline that runs INSIDE your own head is bounded by your model of the change's footprint:

- **Self-check** verifies against your model of what-to-check → misses what you didn't model ([[feedback_passing_test_is_not_verification]] / AR-8 self-attestation).
- **Document-as-you-go** captures against your model of what-needs-documenting → it faithfully records your INCOMPLETE set. It closes the *do→write* gap but NOT the *write-primary→propagate-to-every-coupled-site* gap, and it CANNOT capture a site you don't know is in scope.
- **"Remember to propagate" (CP-1 / sister-cohort completeness)** is still within-model — you propagate to the siblings you already KNOW about.

So the misses are systematically the OUT-OF-MODEL sites: the always-loaded INDEX after you edit a memory BODY; the summary TABLE after you add a detail SECTION; the MASTER POINTER after you write a new HANDOFF; the real LEDGER LOCATION when the filesystem isn't what you assumed. You can't as-you-go-capture or self-check a site outside your model — a logical limit, not a willpower failure. The tell it's a MODEL gap and not fatigue: independent/fresh eyes catch these reliably while self-check doesn't.

**This is the deepest M7 "why"** ([[feedback_structural_enforcement_when_memory_insufficient]]): manual disciplines recur-and-miss because they're model-bounded. The only real closes are EXTERNAL — they do not depend on your model being complete:
- an **independent reviewer** brings a DIFFERENT model → why the binding adversarial-default + the independent close-reviews catch what self-check never does ([[feedback_adversarial_framing_default_for_checks]]);
- a **structural full-set guard** holds the AUTHORITATIVE set mechanically → why TECH_DEBT-166's close-ritual index-reconciliation guard is the real close for the WH-2 stale-index class, and `check_capital_adversarial_audit` / `check_tools_inventory` are the same shape for their domains.

**How to apply:** for any multi-site change, do NOT trust as-you-go / self-check to cover the index/pointer/sibling sites — those are exactly where your model is thinnest. Route them through the structural guard (if one exists) or independent eyes. When the SAME class of miss recurs across checks (e.g. WH-2 four times in one close), STOP instance-fixing — that's whack-a-mole on an open class — and build/cite the full-set guard. The recurrence IS the proof your model can't hold the set.

**Corollary — mutating subagents (operator-surfaced 2026-06-11):** a subagent that MAKES CHANGES is the sharpest out-of-model case — its edits are DEFINITIONALLY outside the orchestrator's model (the orchestrator didn't make them and can't see the subagent's full footprint). So every MUTATING subagent MUST return a structured CHANGE-MANIFEST (files touched · what changed · what's now OWED / needs-propagation), and the orchestrator captures + propagates it. The manifest IS the external enumeration the parent's model lacks; without it the subagent's edits are pure out-of-model drift. Wire it into the spawn PROMPT: read-only agents report findings; mutating agents (incl. Workflow / worktree agents) ALSO return the manifest. (Default-prefer read-only review agents that report-don't-fix — this session's independent reviewers were deliberately "do NOT fix" precisely to avoid this surface.)

**Worked evidence (`.E.0.10` Net-1 close, 2026-06-11):** across FOUR operator-prompted verification passes, WH-2 (stale-index) was the dominant recurring finding — the MEMORY.md hook (edited body, stale index), AR-8/AR-9 added as detail sections but NOT table rows (catalogued-but-not-enforced), the MASTER pickup pointer left at a superseded handoff, and TECH_DEBT-166's OWN README claims stale-on-commit. Each was OUT of the model that wrote the primary edit; each caught only by an external check, never by as-you-go capture or self-review. The entry PROPOSING the index-reconciliation guard (166) shipped carrying two instances of its own class — the cleanest possible proof. Composes with: [[feedback_document_as_you_go_over_catch_at_end]] (the do→write half; THIS is the write→propagate + out-of-model half) · [[feedback_sister_cohort_amendment_completeness]] (the within-model propagation discipline whose LIMIT this names).
