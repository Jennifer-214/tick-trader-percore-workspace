---
name: proportionate-response-to-audit-findings
description: "When an audit catches a structural issue (parallel-infrastructure, duplication, drift surface), the response menu has MORE OPTIONS than \"architect new framework\". Surface the full menu (INLINE MERGE / ACCEPT WITH RATIONALE / FOLD into canonical / ARCHITECT NEW FRAMEWORK / NO-FOLD first-of-kind) and evaluate each honestly. The audit catching the issue is the system working; the response is judgment. Don't default to architect; don't default to smallest either — evaluate and pick what's actually right. Per `feedback_plan_right_not_fast`: planning depth produces right answers; speed heuristics undercut it."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d6b9cf31-8bdc-41b7-aaf5-20e8983e9dfb
  sister_specs: [feedback_enumerate_helper_signature_args_before_extract.md, feedback_implementation_detail_blindspot_recovery_via_taxonomy.md, feedback_prefer_action_parameterized_walker_over_per_consumer_walker_bodies.md, feedback_recheck_designspecs_on_pushback.md, feedback_tiered_audit_discipline_per_plan_scope.md, feedback_train_serve_execution_layer_meta_gap.md, feedback_address_med_low_findings_not_just_high_crit.md]
  tags: [audit-methodology, scope-discipline]
---

When an audit (`/merge-scan`, `/anti-spaghetti`, `/precoding-audit-gate`, `/readiness`) catches a structural issue — parallel infrastructure, sister-registry duplication, drift surface, Class 14/18/21 instance — the **response menu has more options than "architect new framework"**. Default audit-then-architect reflex skips alternatives that may actually be the right answer.

## The response menu

Present the full menu when audit finds a structural issue. Evaluate each option honestly against the situation; pick what's actually right (per `feedback_plan_right_not_fast`: not the first sufficient option; not the smallest option; the RIGHT option).

- **(A) INLINE MERGE** — delete the duplicate; inline its content into the canonical sister; ship as one piece + close the case. Smallest response.
  - Right when: duplication is small (< 5 rows); canonical sister is the structurally correct home; the inline doesn't grow current ship scope.
  - Wrong when: duplication is large; sister's shape doesn't accommodate inline cleanly; future-app multiplier suggests this duplication will recur.

- **(B) ACCEPT WITH RATIONALE** — keep both structures; document why duplication is appropriate (distinct semantics, distinct concerns, intentional asymmetry).
  - Right when: the audit's "duplication" framing turned out incorrect on closer inspection; two structures look similar but encode legitimately different axes; forcing unification would compress legitimately-distinct concerns into a shape that drifts again.
  - Wrong when: rationale is "we'd have to think about it" rather than a genuine structural distinction.

- **(C) FOLD into canonical sister** — extend the canonical with the new rows/scope; deprecate the parallel structure; migrate consumers.
  - Right when: sites-eliminated significantly exceeds sites-added; sister registry is the right structural home; sister has the consumer pipeline you'd otherwise recreate.
  - Wrong when: the fold itself adds substantial scope or breaks sister's coherent shape.

- **(D) ARCHITECT NEW FRAMEWORK** — propose new registry / sidecar / DESIGN_SPEC / skill / consumer macro.
  - Right when: (A) + (B) + (C) clearly insufficient AND sites-eliminated × N future applications justifies the meta-layer cost AND project is in build/consolidation phase (not post-inflection per `feedback_framework_layer_payoff_diminishing_returns`).
  - Wrong when: default reflex skipped alternatives; sites-added-vs-eliminated ratio is poor; payoff curve has flattened.

- **NO-FOLD / first-of-kind** — genuinely new infrastructure required for distinct concern; no canonical sister exists. Document rationale.

## Mechanical filter as INPUT to evaluation (not as triage shortcut)

Counting **sites added vs sites eliminated** is one input to honest evaluation, not a decision shortcut:
- 60 sites eliminated + 4 files added → suggests C or D is justified
- 6 sites eliminated + 5 files added → suggests framework approach is dubious; A or B may be right; but EVALUATE not auto-pick
- Walker iterating 0 rows at proposal time → strong signal that infrastructure hasn't earned its keep yet

These are sanity-check numbers. They support honest evaluation. They don't replace it.

## Why this discipline matters

The reflex was: audit catches duplication → architect a new framework that prevents the duplication. Each catch escalates scope. The audit catching the issue was VALID. But the response was DISPROPORTIONATE — meta-layers added that don't earn back.

The reframe: the audit catch is **information**. The response is **judgment** — and judgment means evaluating the full option set, not auto-picking architect. Reflexive audit-then-architect skips the judgment step entirely.

## Tested-by-construction discipline applies to ALL options

Even INLINE MERGE produces compile failures + CI failures when wrong; doesn't introduce silent bugs. The risk of choosing a smaller response isn't correctness; it's that you might revisit the same site later. The bug-introduction worry is misplaced if your framework discipline is sound — failures show up as build errors, not silent production drift.

## How to apply

1. When audit fires + finds parallel-infrastructure / sister-registry / drift surface, **surface the full menu** (A through D + NO-FOLD). Don't pre-filter to your favorite.

2. **Evaluate each option honestly** against the situation. Use:
   - Sites-added vs sites-eliminated as one input
   - Lifecycle phase (build / consolidation / post-inflection / maintenance) per `feedback_framework_layer_payoff_diminishing_returns`
   - Future-ease multiplier per `feedback_overengineering_boundary_when_future_easier` (still applies — one input among many)
   - Robustness + design alignment + maintenance cost per `feedback_evaluate_options_on_robustness_latency_design_not_time`

3. **Pick what's actually right, not first sufficient.** "Sufficient" is a low bar. Sitting with options long enough to evaluate honestly is what produces right answers (per `feedback_plan_right_not_fast`).

4. **Present recommendation + reasoning, not just recommendation.** Operator's planning depth depends on seeing the full evaluation. Don't compress.

5. Document the chosen option + rationale in plan body / postmortem so future readers see the proportionate-response thinking + the alternatives considered + WHY this option was right (not just that it was chosen).

## What this DOESN'T mean

- Doesn't mean "always pick the smallest option." Smaller is sometimes right; sometimes ARCHITECT is right; depends on the situation.
- Doesn't mean "always present all options every time." For routine cases, recommendations are fine. For substantial structural decisions, present alternatives.
- Doesn't mean "infinite planning." At some point planning concludes + execution starts. The "stop walking" moment per `feedback_framework_layer_payoff_diminishing_returns` is real — but it comes from "we've evaluated and have the right answer", not from "first option that's sufficient".

## Finding-kind axis (names the shape the menu responds to)

`audit-methodologies/audit-finding-kind-taxonomy.md` (D-116, 2026-05-31) tags each finding by KIND {mechanical | structural | design} — orthogonal to severity. The kind maps onto this menu: **mechanical → (A) INLINE MERGE**; **structural → (B) ACCEPT or (C) FOLD**; **design → (D) ARCHITECT / route-to-design-pass**. Kind names the *shape*; this menu picks the *response*; disposition records *where it lands*. Use the shorthand `<SEV>·<kind>[·wide]` when surfacing a finding so the menu choice is legible straight from the tag — and so operator + agent share one compact triage vocabulary.

## Sister memories

- `feedback_plan_right_not_fast` — meta-discipline; this memory's "evaluate honestly not auto-pick" framing applies that meta to audit findings specifically
- `feedback_framework_layer_payoff_diminishing_returns` — inflection-point recognition; informs whether (D) ARCHITECT is even on the table for current lifecycle phase
- `feedback_audit_canonical_sister_before_new_infra` — the pre-coding audit discipline; this memory expands its response menu (was FOLD/NO-FOLD only; now A/B/C/D/NO-FOLD)
- `feedback_consult_on_audit_findings` — present findings + iterate with operator; this discipline strengthens what "present findings" means (full menu, honest reasoning)
- `feedback_motivated_collaborator_for_caramel` — senior-engineer judgment includes presenting alternatives honestly + sitting with decisions long enough to get them right

## Codification trigger

Originally codified after a consolidation sprint where audit catches kept escalating to "spawn new sub-ship + new DESIGN_SPEC" responses; each catch was valid; the SUM of escalations grew meta-layers past inflection point. Operator surfaced reframe: "the audit catching B as duplicating canonical infrastructure is the system working. The question isn't 'did I screw up' — it's 'is the response to each catch proportionate?' Right now the response is 'spawn another sub-ship with its own DESIGN_SPECs.' A proportionate response is sometimes 'merge this back into the parent and move on.'"

Re-calibrated to remove speed bias after operator surfaced: planning IS the hard part of SWE now; discipline should support decide-rightly, not decide-quickly. "Walk menu in order + stop at first sufficient" was speed-bias that compressed planning depth + was therefore wrong-shaped for planning-grade decisions. Discipline now: surface the full menu + evaluate honestly + pick what's actually right.
