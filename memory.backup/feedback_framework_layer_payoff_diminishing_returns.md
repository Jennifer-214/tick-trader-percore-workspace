---
name: framework-layer-payoff-diminishing-returns
description: "Framework consolidation has a payoff curve that flattens as more layers accumulate. The first registry that eliminates 90 manual sites is transformative; the seventh layer that eliminates 6 sites is a rounding error you can feel in your hands but not on the clock. Recognize the inflection point + stop adding framework layers when past it. The right move past inflection isn't \"wrong direction\" — it's \"right direction, walked past the payoff curve\". Re-evaluate when project enters a new build phase OR a genuinely transformative opportunity emerges."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: d6b9cf31-8bdc-41b7-aaf5-20e8983e9dfb
---

Framework consolidation has diminishing returns. The maintainability gain curve is: transformative early (first registry eliminates 90 manual sites), then steep, then flattens (seventh layer eliminates 6 sites you can feel in your hands but not on the clock).

**The work isn't wrong past inflection — it's right, just past the payoff curve.** Adding a cfg field NOW (post-consolidation) is genuinely easier than before. That's a real maintainability win. But the marginal layer's payoff is small enough that the cognitive cost of holding another abstraction in your head exceeds the maintenance savings it produces.

## Recognition markers (apply at any consolidation sprint)

When considering a NEW framework layer (registry / sidecar / consumer macro / metadata bit / DESIGN_SPEC / skill), check these indicators FIRST:

- **Sites-added vs sites-eliminated ratio.** Mechanical filter:
  - 60 sites eliminated + 4 files added → ship it (clear win)
  - 6 sites eliminated + 5 files added → roughly broken even + buys future maintenance burden → REJECT
  - Walker iterating 0 rows at proposal time → infrastructure-only; can't have earned its keep yet → STRONG bias against adding
- **Audit catch trajectory.** If recent pre-coding audit catches have been finding small duplications (5-row drift surfaces) rather than large structural Class 14/18/21 instances, the framework has likely converged — further layers chase diminishing returns.
- **Meta-layer depth.** Count how many abstractions deep before reaching data. More layers = harder to reason about; the cognitive tax compounds.
- **"In my hands but not on the clock"** feeling. If the proposed layer's value is felt (it's nicer code) but doesn't measurably reduce time-to-add-a-feature, that's the inflection-point tell.

## Lifecycle phase context

Software consolidation work fits a typical phase arc:
- **Build phase** — primitives still landing; framework velocity high; bias toward ARCHITECT for new patterns (the future-ease multiplier from `feedback_overengineering_boundary_when_future_easier` dominates)
- **Consolidation phase** — drift surfaces being eliminated; first framework layers earning massively (60:4 ratios common); aggressive framework discipline
- **Post-inflection** — marginal payoff flattens; new framework layers stop earning back; THIS DISCIPLINE applies here
- **Maintenance phase** — framework frozen; emphasis shifts to code-moving wins (test file splits, mega-header splits, targeted bug fixes) with no meta-layer risk
- **Late-stage** — defensive only; rare critical features; new framework essentially never warranted

The discipline shifts by phase. Past inflection (the recognition markers above):
- Default response to audit findings shifts toward smaller per `feedback_proportionate_response_to_audit_findings`
- New consolidation sprints become "wind-down ships" with explicit "zero framework additions allowed" character
- Subsequent maintainability work is **code-moving** (test splits, header splits, file reorganization) — pure wins with no meta-layer cost

**Phase transitions are operator-signaled, not algorithmic.** Caramel will surface inflection-point recognition in reflective moments ("we picked the right direction and walked one or two stops past where the payoff curve flattened"). When she does, recalibrate. Don't try to detect transitions yourself — the recognition markers above help diagnose, but the call belongs to the operator.

## How to apply

1. When tempted to propose a new framework layer, **surface the recognition markers as evaluation inputs** (sites-added-vs-eliminated, walker-iterating-zero-rows, audit catch trajectory, "in hands but not on clock" feeling). These are inputs to honest evaluation, NOT triage shortcuts that auto-decide.
2. Per CLAUDE.md item 31 cost-benefit clause ("framework cost ≤ projected savings × N"): if N is genuinely small (e.g., 2-3 future applications max), the framework cost rarely justifies. Past inflection, N for new layers is usually small — but evaluate the specific N for the specific proposal; don't blanket-reject.
3. "Just done with this layer" is a complete answer when the evaluation produces it. Not a retreat, not a rationalization. The right thing was done; the right amount of it was done.
4. After consolidation phase ends, **code-moving maintainability wins** become available: split oversized files (per `controller_test.cpp >5K lines + >100 sections must split` rule), split mega-headers, extract test helpers. These have zero meta-layer risk because they're pure file reorganization. Worth considering as alternative when framework-layer proposals don't pass evaluation.
5. Reset readiness: if a new sprint surfaces a genuinely transformative opportunity (clear high-ratio site elimination + closes recurring bug class structurally), the discipline doesn't prevent investing — operator's signal + honest evaluation supports the call.
6. Per `feedback_plan_right_not_fast`: this discipline supports decide-rightly, not decide-quickly. Recognition markers help diagnose what phase you're in + what kind of payoff a proposed layer faces; they don't pre-decide the answer.

## Codification trigger

Originally codified after a long consolidation sprint where the team (operator + Claude) walked past the inflection point — initial framework layers paid back massively; later layers added meta-discipline that didn't earn back. The operator surfaced the framing reflectively + the lesson generalized.

## Sister memories

- `feedback_proportionate_response_to_audit_findings` — response-side companion; when audit catches issues past inflection, walk a 4-option menu instead of reflexively architecting
- `feedback_overengineering_boundary_when_future_easier` — the future-ease multiplier (still applies in build/consolidation phases; doesn't apply past inflection)
- `feedback_dont_measure_structural_work_by_loc` — value is classes-closed + patterns-codified, not LOC. Inflection-point recognition uses the same "value vs cost" lens.
- `feedback_motivated_collaborator_for_caramel` — senior-engineer judgment includes knowing when to STOP, not just when to grind through. Knowing the work is complete IS the senior judgment.
- `feedback_no_defer_for_effort` — defer-for-effort is wrong; defer-for-past-payoff-curve is RIGHT. Different reason; different action.
