---
type: ledger-template
class_id: 43
title: Money value derived ≥2 ways without single-sourcing the computation (divergent/implicit rounding-mode OR open-coded formula duplication)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-06-12
surface_tags: [money-math, accounting, ssot, capital-safety, determinism]
severity: high
recurrence_count: 2
first_instance: 2026-06-02 (v5.15.5.F.4d.1.E #11, D-105 — absent/implicit rounding-mode on money mul/div; the "AP4" draft label from D-121 that was never written into the catalog as a class)
closure_mechanism: single-source the COMPUTATION (one helper owns the formula + its rounding mode), not just the mode; route every site through it; freeze with a characterization test (Class-43 surfaces are the canonical char-test target — see characterization-test-discipline.md) + a single-source CI guard. Canonical: `Money_FillGross` (Portfolio.hpp:397) 1-mul SSoT + `tools/check_money_gross_single_source.py` (pre-commit Check L).
sister_classes: [27, 29]
sister_memories: [feedback_single_source_the_computation_not_just_the_mode, feedback_golden_master_over_reimplemented_oracle, feedback_defer_to_source_authority_for_external_semantics]
---

# Class 43 — Money value derived ≥2 ways without single-sourcing the computation

A money value (price-diff gross, fee, net, balance delta) is computed at **two or more sites** with the formula or rounding mode **open-coded at each**, rather than flowing through one canonical helper. The sites agree on most inputs and silently **diverge** on the edge — a different rounding boundary, a different multiply order, a 1-ULP gap — so the bug is invisible in tests with round inputs and surfaces only on a real venue fill. On a capital path a 1-ULP divergence between the booking site and the reconciliation site is a real, compounding accounting error.

This is the [[feedback_single_source_the_computation_not_just_the_mode]] lesson as a code anti-pattern. It **subsumes the never-authored "AP4" draft label** (D-121's #11-anti-pattern-set taxonomy proposed AP1–AP4 as Stage-2 DRAFT classes; only the memory + ledger refs were ever written — `Class 43` is where the money-math shape actually lands, with the D-190 generalization folded in).

## Sub-shape A — Absent / implicit / divergent rounding-mode on money mul/div (D-105)

A `Money` multiply or divide is written without pinning the rounding mode, so two sites that "do the same math" round differently at the 8dp boundary (truncate vs half-even vs half-up). The result depends on which site computed it. **The original "AP4".** Closure: every `Money_*` op saturates + rounds half-even by construction (the `FixedPoint<10,8>` op family); a money value that needs a derived formula pins it in ONE helper, never re-rolls the mul/div at the call site.

## Sub-shape B — Open-coded formula duplication; value derived ≥2 ways (D-190)

The *formula itself* is duplicated. `.E.0.10`: gross P&L was computed as a 2-mul `price_diff × qty` open-coded at 5 sites; the single-source 1-mul form (`Money_FillGross`) differs by 1 ULP on non-round inputs. Every open-coded site is a divergence waiting for the input that splits them. Closure: extract the formula to ONE helper (`Money_FillGross`), route ALL sites through it, guard with a single-source CI check that fails on a re-open-coded call (`check_money_gross_single_source.py`). The adversarial completeness sweep matters here — the D-190 fix initially missed 2 of the 5 sites (`:443`/`:2896`); a 3-agent sweep found them (sister AR-7: a SSoT is only total if you enumerate what's OUTSIDE it).

## Recurring symptom

- The same money quantity (gross / fee / net) computed inline at ≥2 sites rather than via one named helper.
- A `Money_Mul`/`Money_Div` chain re-written at a call site that another site also computes.
- A characterization test with ROUND inputs that goes green while a divergent-input sibling is absent (the divergence is real but unexercised — see the coverage-disclaimer discipline).

## Closure (structural)

1. **Single-source the COMPUTATION, not just the mode.** One helper owns the formula AND its rounding; the type system owns the mode (half-even by construction). A value derived ≥2 ways = an SSoT candidate; default MERGE.
2. **Route every site** through the helper; delete the open-coded forms (don't leave one "for clarity" — it's a divergence).
3. **Single-source CI guard** that red-builds on a re-open-coded computation at any site (the `check_money_gross_single_source.py` shape).
4. **Freeze with a characterization test** per `characterization-test-discipline.md` — including a **divergent-input** case that actually splits the two forms (a round-input-only test does not exercise the bug; say so in a coverage disclaimer).

## False-positive surface

- Two sites computing **genuinely different** quantities that happen to share inputs (entry-fee vs exit-fee on the same fill) — not a duplication; each is its own value. The class is about the SAME value derived two ways.
- A display-only `Money_ToDouble` re-derivation for a GUI label — not a capital path; divergence is cosmetic (still prefer the SSoT, but not HIGH).
- An externally-defined value mirrored source-exact per [[feedback_defer_to_source_authority_for_external_semantics]] (venue fee-rounding, tick/lot) — the "duplication" is faithful mirroring of an external authority + a guard, not an internalized second formula.
- A value computed once and **carried** through subsystem state (the correct pattern — Class 27's decision-time binding) is the OPPOSITE of this class, not an instance.

## Canonical reference

[[feedback_single_source_the_computation_not_just_the_mode]]; `DESIGN_SPECS/meta-disciplines/single-source-of-truth-discipline.md`; `DESIGN_SPECS/audit-methodologies/characterization-test-discipline.md` (the char-test that surfaces + freezes this); `Money_FillGross` @ `CoreFrameworks/Portfolio.hpp:397` + `tools/check_money_gross_single_source.py` (first canonical structural close); D-105 (Sub-shape A) + D-190 (Sub-shape B); H4 (Money for all accounting math).
