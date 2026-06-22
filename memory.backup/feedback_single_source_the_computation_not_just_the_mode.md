---
name: feedback_single_source_the_computation_not_just_the_mode
description: "For any money (or determinism-bound) value computed in ≥2 places, single-source the COMPUTATION/formula — not just the rounding mode. Uniform rounding mode ≠ consistent value when the formulas differ (round((a−b)×q) vs round(a×q)−round(b×q) diverge by 1 ULP under decimal). And re-check any 'not a present bug' inconsistency under a representation change — it may have been benign only under the old representation."
metadata: 
  node_type: memory
  type: feedback
  tags: [ssot, audit-methodology]
  originSessionId: 3e806606-ac69-40fd-ac33-45906443bae4
  sister_specs: [feedback_defer_to_source_authority_for_external_semantics.md, feedback_passing_test_is_not_verification.md, feedback_single_source_of_truth_discipline.md, project_no_margin_trading.md]
---

When the same money value is computed in more than one place (parallel accounting paths, per-core vs aggregate, live vs replay), single-source the FORMULA — not merely the rounding mode. A uniform rounding mode (half-even everywhere) does NOT make two paths agree if one computes `round((exit−entry)×qty)` (1 mul) and another `round(exit×qty) − round(entry×qty)` (2 muls): they diverge by 1 ULP. The complete fix is ONE shared helper (e.g. `Money_FillGross`) every path calls, so the values reconcile BY CONSTRUCTION, not by discipline.

**Why:** D-105 (Ship B) correctly identified the decimal-sensitive P&L cohort + the "live≠replay" risk, and applied ONE rounding MODE uniformly — but left the gross FORMULA split (DrainPostFill `:1536` 2-mul vs everywhere-else 1-mul). Under FPN's 2⁻⁶⁴ rounding the gap was ~1e-19 (invisible), and D-105 graded the inconsistency "correctness-WIN, not a present bug." Decimal half-even at 1e-8 then ACTIVATED it: `core_realized` and `oms.realized_pnl` diverge by 1 ULP on ~25% of real fills, accumulating. Mode-uniformity was necessary but NOT sufficient; formula-SSoT is.

**How to apply:** (1) any money value derived ≥2 ways → ONE shared computation, never open-coded per path. (2) A representation/epoch change (binary→decimal, truncate→half-even) RE-OPENS every "benign inconsistency" judgment — re-verify that a gap graded "not a present bug" under the old representation survives the new one (here it activated a latent FPN-era class). (3) The decimal epoch silently changed the meaning of every multiply-then-round on the money path → after such a change, SWEEP for parallel derivations. Sister: [[feedback_single_source_of_truth_discipline]] · [[feedback_defer_to_source_authority_for_external_semantics]] · [[feedback_passing_test_is_not_verification]].

Codified as a code anti-pattern — **Class 43** (money value derived ≥2 ways without single-sourcing the computation; Sub-shape A = divergent/implicit rounding-mode [D-105], Sub-shape B = open-coded formula duplication [D-190]) — at `.E.0.10` 2026-06-12 (the never-authored "AP4" draft label lands here). The char-test that freezes such a value: `DESIGN_SPECS/audit-methodologies/characterization-test-discipline.md`.
