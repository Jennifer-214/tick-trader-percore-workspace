---
type: meta-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-06-12
landing_ship: v5.15.5.F.4d.1.E.0.10
canonical_applications:
  - v5.15.5.F.4d.1.E.0.10 (A9 — dead paper/backtest slippage restored: optimistic sim → pessimistic)
sister_specs:
  - meta-disciplines/backtest-paper-live-convergence-discipline.md (the staged-promotion sister — mechanical-convergence half)
  - audit-methodologies/characterization-test-discipline.md (freeze the pessimistic behavior so it can't silently revert)
tags: [meta-discipline, backtest, paper-mode, capital-safety, conservative-bias, trustworthy-sim]
surface: [backtest, paper-mode, strategy-development, capital-management]
applies_at_skills: [/accounting-audit, /parity-check, /post-ship-audit, /ml-audit]
explains_findings: [A9]
---

# Adversarial / pessimistic simulation discipline (make the sim FAIL, don't flatter it)

**Core principle (operator, 2026-06-12):** *"trying to make [the backtest] fail at every point possible is the best idea — instead of trying to make the best backtest."* A backtest/paper simulation must be **biased AGAINST the strategy** — overestimate every cost + adversity (fees, slippage, adverse fills, timing, liquidity) — so that **surviving the sim is a SUFFICIENT (not necessary) signal of live viability.** An optimistic sim that "looks good" is a trap: it inflates expectations the live market will not honor, and the gap surfaces as real capital loss. The margin of safety is built INTO the sim, not hoped for afterward. This is the avionics-grade stance applied to strategy validation: assume the worst plausible execution, and trust only a strategy that profits anyway.

## Why — the error-cost asymmetry

A false POSITIVE in a sim (a strategy that looks good but isn't) costs **real capital** live. A false NEGATIVE (a viable strategy a pessimistic sim rejected) costs only a **missed opportunity**. The costs are wildly asymmetric → deliberately bias the sim toward false negatives (pessimism). A sim tuned to make a strategy look its best optimizes for exactly the wrong error.

**Operator framing (2026-06-12, ratifying this as core — D-203):** *"people would respect a backtest that survives after trying to make it fail every way possible than get a single highest return on average — because if you can force it to work after making it fail in more ways than the market can, you can trust it."* Max-average-return on an optimistic sim is the trap; **survives-every-failure-mode is the signal.** Trust comes from the strategy clearing a bar harder than the live market will set — not from the sim flattering it. (A worked corollary: a conservative non-zero **default** for every cost knob, so the sim is pessimistic out-of-the-box — never optimistic-by-omission; D-203 sets the slippage default.)

## The axes of pessimism (model the worst plausible on EACH — partial coverage isn't conservative)

1. **Cost** — fees + slippage at/above realistic worst-case. Fees: book the higher (taker) rate unless maker is proven; slippage: a conservative non-zero default, **never zero**. *(A9 canonical instance: paper/backtest slippage was silently DEAD — `pre_resolved.slippage_pct` bound but read at zero live sites → fills booked at the raw trigger price = zero execution cost = optimistic. Restored: entry fills worse [higher], exit fills worse [lower].)*
2. **Fill price** — fill at the adverse end (BUY at ask/high, SELL at bid/low), not mid; model a partial fill as the worse outcome.
3. **Timing / latency** — assume the unfavorable move within the latency window; never assume an instant fill at the trigger.
4. **Liquidity / impact** — larger size → worse fill; thin book → wider slip; gap-risk through stops (a stop can fill far past its trigger).

A sim pessimistic on cost but optimistic on fill-timing is only *partially* trustworthy — and reads as "conservative" when it isn't.

## Reconciliation with the convergence discipline (NOT a contradiction)

The sister `backtest-paper-live-convergence-discipline.md` wants backtest ≈ paper ≈ live. This discipline wants the sim biased pessimistic (deliberately *worse* than live-expected). They reconcile on a clean split:
- **Mechanical convergence** — the LOGIC (the fill/booking/accounting code path) MUST match across backtest/paper/live: same `OrderManager_HandleFill`, same `Money_FillGross` (D-190), same gates. Divergent *logic* is a bug.
- **Parameter pessimism** — the COST/adversity PARAMETERS (slippage_pct, fee rate, fill-price assumption) are deliberately set conservative in sim. The sim runs the SAME mechanism with WORSE inputs.

So: **identical mechanism, pessimistic parameters.** Passing the sim means "profitable even under worst-plausible costs, via the exact code that will run live."

## Trustworthy-sim is a live-readiness PRECONDITION

A strategy cannot be promoted (per the convergence discipline's 4-step) on backtest/paper evidence unless that evidence is pessimistic — else the promotion rests on inflated numbers. This is why A9 (restoring dead slippage) was sequenced FIRST in the `.E.0.10` fix-ship: until the sim is honestly pessimistic, paper-test results are not trustworthy as live-readiness evidence at all.

## Anti-patterns

- **Optimistic sim ("make the backtest look good")** — tuning costs down / assuming mid-fills / zero slippage to flatter a strategy. It then disappoints live; the gap is exactly the un-modeled adversity.
- **Silently-dead cost model (the A9 shape — the most dangerous form)** — a cost knob that is wired but inert (bound-but-unread slippage, recompute-instead-of-book fees). The sim is optimistic *without anyone choosing it* — nobody decided to be optimistic; the code just quietly is. Detect via the representation-migration / Class-44 orphan family (a cost field written-but-unread or read-but-unwritten).
- **Cost pessimism without fill/timing/liquidity pessimism** — partial coverage masquerading as conservative.

## How to apply (checklist)

1. For every cost/adversity input on the sim path, confirm it is (a) WIRED + consumed (not a dead knob — A9), and (b) defaulted CONSERVATIVE (worst-plausible, never optimistic).
2. Walk the four axes (cost / fill-price / timing / liquidity); name which are modeled and which are not (honest coverage, like the characterization-test coverage disclaimer).
3. Keep the LOGIC convergent with live (same HandleFill/gross/gates); make only the PARAMETERS pessimistic.
4. Freeze the pessimistic behavior with a characterization test (so a refactor can't silently revert it to optimistic — the A9 dead-slip is exactly a silent reversion).

## Cross-references

Sister: `backtest-paper-live-convergence-discipline.md` (staged promotion; the mechanical-convergence half). `characterization-test-discipline.md` (freeze the pessimistic behavior). Class 44 / `representation-migration-completeness.md` (the silently-dead-knob detection family). [[feedback_two_foundations_determinism_vs_correctness]] (the sim's determinism is orthogonal to its conservative bias). A9 in `plans/v5.15-live-readiness/plan_checks/E.0.10-finding-disposition-register.md` (first canonical instance). **Core-principle candidate for `DOCS/DESIGN_PHILOSOPHY.md` priority gradients** (operator 2026-06-12: "that should be a core principle").
