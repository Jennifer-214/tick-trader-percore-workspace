---
name: defer-to-source-authority-for-external-semantics
description: "For externally-DEFINED values/semantics (exchange price+qty precision, venue fee-rounding, tick/lot size, protocol field widths), the external authority is the SSoT — mirror it source-exact + GUARD it, never internalize an arbitrary choice; removes a decision AND a drift source."
metadata: 
  node_type: memory
  type: feedback
  sister_specs: [feedback_single_source_of_truth_discipline.md, feedback_two_foundations_determinism_vs_correctness.md, feedback_single_source_the_computation_not_just_the_mode.md]
  tags: [ssot, framework-discipline, wire-format]
  originSessionId: b1ce1b7e-9d36-4f05-a210-c616603d3d9d
---

When a value or representational semantic is DEFINED by an external authority — the exchange/venue's price+qty precision, tick/lot size, fee-rounding convention; a protocol's field widths; a spec's canonical form — defer to that authority as the single source of truth rather than choosing our own internal convention.

**Why:** every internal choice that DUPLICATES an external authority's decision is (1) a decision we didn't have to make, and (2) a silent drift source — our convention vs theirs can diverge and corrupt money/correctness without a type error. Deferring removes BOTH. The flip side of the phantom-invariant trap (don't ASSUME the invariant — READ it from the source + guard it). Operator framing (2026-05-30, decimal money core): "match binance or whatever venue we're trading on — then we never have to make a decision, we just let the venue decide."

**How to apply:**
- **Mirror** — store source-exact (the stored int IS what the source sent; D-97).
- **Registry-ize the semantics** — per-source params become REGISTRY metadata (a FOREACH_EXCHANGE row per venue: price_decimals/qty_decimals/tick/lot/fee-rounding), so adding a source = 1 row (composes with the framework-driven philosophy + multi-exchange D-3).
- **Guard** — `static_assert`/boot-check that our storage can hold the source's precision; a source that exceeds our capacity FAILS LOUD, never silently truncates.
- **Split compile-time vs runtime** — a FIXED storage scale ≥ max-source precision is compile-time (keep the type clean; don't make scale a runtime exponent); the semantics (rounding/tick/lot/display) are runtime-per-source.
- **Turns "which convention?" into "what does the source do?"** — a fact to read, not a choice to argue (e.g. decimal money rounding = "match Binance's fee-rounding convention," not "pick half-even vs truncate").

Generalizes D-97 (source-exact) into a reusable principle; D-104/D-106 are its money-core application. Sister: [[feedback_single_source_of_truth_discipline]] (this is its EXTERNAL-authority complement — internal SSoT says "one canonical site for OUR facts"; this says "defer to THEIR site for THEIR facts"), [[feedback_two_foundations_determinism_vs_correctness]].
