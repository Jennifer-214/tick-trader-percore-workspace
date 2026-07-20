---
name: structural-enforcement-when-memory-insufficient
description: When memory codification of a discipline proves insufficient at next-cycle observation (same bug class recurs DESPITE the codified memory), escalate to STRUCTURAL ENFORCEMENT (CI tool / pre-commit hook / compile-time check). Memory + audit cycles work for many bug classes; some have recurrence dynamics that memory alone cannot prevent. Sister to feedback_structural_fix_for_recurring_class (parent rule: structural fix beats one-time patch); THIS RULE is the OBSERVATIONAL TRIGGER for upgrading from MEMORY-ENFORCEMENT to STRUCTURAL-ENFORCEMENT at the same surface.
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fc2542a7-8662-4b21-a393-f1598d05e50b
  sister_specs: [feedback_structural_fix_for_recurring_class.md, feedback_verify_symbol_existence_at_plan_drafting_time.md, feedback_enumerate_helper_signature_args_before_extract.md, feedback_iteration_spiral_signals_audit_meta_gap.md, feedback_implementation_detail_blindspot_recovery_via_taxonomy.md, feedback_motivated_collaborator_for_caramel.md, feedback_forward_promise_auto_write_verification.md, feedback_independence_for_judgment_not_mechanical.md, feedback_no_question_boxes.md, feedback_proactive_rename_candidate_surfacing.md, feedback_session_decision_log_discipline.md, feedback_address_med_low_findings_not_just_high_crit.md, feedback_run_doc_ci_tools_first_never_hand_verify.md, feedback_capture_and_check_are_model_bounded.md, feedback_implement_reconcile_decision_code_binding.md, feedback_mechanically_verify_derived_code_facts.md, feedback_run_cascade_upfront_for_rename_and_registry.md, feedback_name_members_never_tallies_in_docs.md]
  tags: [structural-fix, meta-discipline]
---

Memory codification is a discipline-installation layer; it works for many bug classes by surfacing the right rule at the right moment via auto-loaded context. But some bug classes have RECURRENCE DYNAMICS that memory alone cannot prevent — specifically: when the discipline applies at a planning/drafting layer where context-switching, fatigue, or complexity create high cognitive load + the rule is easy to forget at the moment of action.

For these bug classes, MEMORY + AUDIT-CYCLES + DISCIPLINE-CODIFICATION are NECESSARY-BUT-INSUFFICIENT. STRUCTURAL ENFORCEMENT (CI tool / pre-commit hook / compile-time check / static_assert / linter rule) is needed to close the loop.

**Why:** Codified 2026-05-26 at `.B.4` v1.7.4 cycle after empirical evidence:

- **v1.7.3 codified M6 META-discipline** `feedback_enumerate_helper_signature_args_before_extract` — body-content arg enumeration before helper extract; Class 14 (fabricated-symbol) sister discipline at body-content layer
- **In SAME v1.7.4 cycle (AFTER M6 codification)**, I introduced 6 NEW Class 14 fabrications during plan body mechanical fixes:
  - `current_book_imbalance` (cfg member that doesn't exist)
  - `depth_enabled` (BookSnapshot field that doesn't exist)  
  - `current_spread` / `current_mid_price` (renamed prefix drift)
  - `tick.timestamp_us` (Tick<F> field is `timestamp` not `timestamp_us`)
  - `FPN_IsZero(double)` (type mismatch — atomic returns double, FPN_IsZero takes FPN<F>)
- **5 audit agents + M6 memory codification missed all 6.** Tool catches all deterministically at compile time.

The pattern: memory codification surfaces the rule, BUT during high-cognitive-load amendment cycles (9 amendments v1.0 → v1.7.4 with cross-methodology audits + scope expansions), the right-symbol-at-right-time check gets skipped or mis-applied. Memory says "verify symbol exists"; I think "I just verified that one" and miss the next one introduced 5 lines later.

Per `feedback_motivated_collaborator_for_caramel` + `feedback_structural_fix_for_recurring_class`: when memory alone proves insufficient AT THE SAME SURFACE in the SAME CYCLE as codification, that's the escalation trigger.

**How to apply — observational trigger for structural-enforcement upgrade:**

| Signal | What it means | Action |
|---|---|---|
| Memory codified at vX.Y; bug class recurs at vX.Y+1 of same cycle | Cognitive-load failure mode; memory loads but doesn't fire at action moment | Build CI tool / pre-commit hook / static_assert |
| Multiple agents miss same bug class instance | Audit-shape can't catch this class; needs deterministic check | Build mechanical verifier |
| Bug class has compile-detectable signature (symbol existence / type match / signature parity) | Compile-time check is feasible | Prefer compile-time over runtime check |
| Bug class is amendment-cycle-prone (introduced during edits, not initial drafts) | High-cognitive-load surface | Pre-commit hook gates commits |
| Bug class involves source-code-drift (X renamed to Y; A field removed; signature changed) | Memory can't track HEAD state | Tool that reads HEAD directly |

**Lifecycle (Stage 6 promotion meta-pattern):**

Each Class N bug class progresses:
- **Stage 1** — anti-pattern recognized at instance; one-time patch
- **Stage 2** — recurrence (2nd-3rd instance); discipline articulated in RECURRING_BUG_PATTERNS or memory
- **Stage 3** — memory codified; loads via MEMORY.md index; sister DESIGN_SPECS pattern
- **Stage 4** — `/readiness` check added; audit-time enforcement
- **Stage 5** — multi-agent audit fires the check; structural review
- **Stage 6** — STRUCTURAL ENFORCEMENT — CI tool / pre-commit hook / static_assert / compile-time check (THIS RULE governs WHEN to escalate)

Most bug classes plateau at Stage 3-5 because the discipline-installation works. Bug classes that recur AT Stage 5 are candidates for Stage 6 escalation per this rule.

**Recognition markers (when to escalate to structural enforcement):**

- Bug class instance count keeps rising despite memory + audits in place
- Same operator (Claude) introduces same bug class in same cycle AS the memory codification
- Audit verdict GREEN at SHAPE layer but instance count grows at IMPLEMENTATION layer (M4 territory)
- Compile-time-detectable signature exists for the bug class
- Cognitive-load amplifier present at surface (long files / mechanical amendments / cross-file drift)
- Multi-agent convergence MISSES the bug class while finding others

**Sister memories:**

- [[structural-fix-for-recurring-class]] — PARENT meta-rule (structural fix beats one-time patch); THIS RULE is the OBSERVATIONAL TRIGGER for memory→structural escalation
- [[verify-symbol-existence-at-plan-drafting-time]] — Class 14 discipline; worked example for Stage 6 promotion (Stage 3 → 6 at .B.4 v1.7.4 via B-Plus CI tool)
- [[enumerate-helper-signature-args-before-extract]] — M6 sister discipline; Stage 3 → may need Stage 6 if recurrence continues
- [[iteration-spiral-signals-audit-meta-gap]] — DIFFERENT trigger (3+ smaller findings = META-gap codify); THIS RULE is single-instance-recurrence trigger
- [[implementation-detail-blindspot-recovery-via-taxonomy]] — M4 META-discipline; complementary blind-spot layer
- [[motivated-collaborator-for-caramel]] — best-software-path requires investing in structural enforcement when memory alone proves insufficient

**Worked examples (Stage 6 promotions):**

| Bug class | Memory codified | Recurrence cycle | Structural enforcement landed | Tool |
|---|---|---|---|---|
| Class 14 (fabricated symbol) | v5.15.5.F.4d.1.B.3 v1.5 | .B.4 v1.7.3 → v1.7.4 (6 instances) | .B.4 v1.7.4 | `tools/check_plan_body_symbol_existence.py` + pre-commit hook |
| Class 26 sub-shape A (paired-access mismatch) | feedback_categorize_by_consumer_pattern_not_field_name | .B.7 Async.hpp:814+853 hotfix | .B.7 | `tools/check_per_core_registry_integrity.py` Check 9 |
| Class 26 sub-shape B (UNINDEXED-GLOBAL) | feedback_cfg_field_categorization_at_registry_add_time | .B.8 4 HIGH consumer-site fixes | .B.8 | `tools/check_per_core_registry_integrity.py` Check 10 |
| Class 33 sub-shape (forward-promise auto-write drift) | feedback_forward_promise_auto_write_verification at .B.8 | .B.3→.B.4→.B.6→.B.7→.B.8→.D session (8+ instances across 6 ships caught at .D dogfood) | v5.15.5.F.4d.1.D | NEW `tools/check_forward_promise_audit.py` Check 11 + pre-commit hook extension + 5-skill integration cohort |
| (future) Class 23 (type punning) | tt:: type-trait dispatch | (none yet) | (already at Stage 5 via 4-pillar audit) | CI Check |

**Codification trigger (worked example for future):**

`.B.4` v1.7.3 → v1.7.4 cycle. M6 codified at v1.7.3 with body-content enumeration discipline. v1.7.4 mechanical fix cycle introduced 6 NEW Class 14 fabrications IN THE SAME CYCLE — despite M6 memory load + 5-agent audits. CI tool (B-Plus) caught all 6 deterministically at compile time. Empirical proof that memory + audit-cycles are insufficient for Class 14 at body-content layer; structural enforcement (CI tool + pre-commit hook) bridged the gap. NEW MEMORY codified to capture the OBSERVATIONAL TRIGGER for future Stage 6 escalations of other bug classes.
