---
type: refactor-pattern
tags: [hot-path, determinism, branchless, latency, data-oriented-design]
surface: [hot-path, oms-drainer, slow-path]
stage: 3-first-canonical
established: 2026-06-16
sister_specs:
  - refactor-patterns/branchless-dispatch-discipline.md  # H7/H20 — THIS is its deep WHY
  - meta-disciplines/mechanical-verification-of-derived-code-facts.md  # measure the jitter, never hand-assert it
---

# Critical-moment determinism over low average latency

## The principle (the actual cost function)

For a capital-bearing HFT engine the cost is **NOT average latency** — it is **latency JITTER correlated with the actions that matter** (order placement, signal commitment). A design that introduces a latency spike *exactly on the trade tick* is the worst possible shape: **variance where it is most expensive.** A predictable-but-slightly-higher latency at the critical moment beats a lower-*average* latency that **spikes when you commit capital** — because a constant can be modeled and hedged; correlated variance is unhedgeable risk (worse fills, adverse selection, precisely when acting on a signal).

> We do not want average latency to be low. We want latency to **not jitter under the circumstances where latency variation is critical** — and the current design introduces jitter exactly when it IS critical and stays smooth when it isn't. That is backwards.

## The canonical anti-instance (locked for the fix)

The hot-path trade-event push is a data-dependent branch (`ExecutionCore.hpp:483`; four conditional `SPSCRing_TryPush` sites `:513/:523/:534/:564`). The predictor trains on the common case (no trade → not-taken), so the **rare trade IS a guaranteed misprediction + pipeline flush — and the flush lands precisely on the trade-placement tick.** "Well-predicted" (low *average* mispredict cost) is the trap: true for the 99% that don't matter, **guaranteed on the 1% that do.** Averaging hides the only number that matters.

## The fix-signature

Hot-path work correlated with capital commitment does the **SAME work every tick** — no data-dependent spike. For the conditional push: the H20 form — **always write `event_ring[head]`, mask the head-ADVANCE by the fired flag** — so the trade tick costs the same as a quiet tick. This is the **deep WHY of H20** (branchless preferred *even when nominally slower*): the goal was never raw speed, it is **breaking the correlation between "doing the important thing" and "being slow."** It also reframes **H8**: the ≤500ns budget is about *predictable latency at the critical moment*, not a low average.

## The trade is accepted on purpose

The branchless form adds a cheap dummy-write per quiet tick (a hair slower on average) to delete the trade-tick flush. **That is the correct trade by the cost function above** — buying critical-moment determinism with average-case cents. An "average latency rose 1%" measurement does **NOT** veto it; the measurement's job is to confirm the variance win + that the budget still holds, never to re-litigate the principle.

## Discipline

- A hot/slow-path branch (or cache-miss, or flush) **correlated with order placement / signal commitment** is a DEFECT even when "rare" and "well-predicted." Flag it; make it branchless (H20).
- Latency is judged on **variance-at-the-critical-moment** — measured (the H8 bench classifying trade vs quiet ticks), never a hand-asserted average (`mechanical-verification-of-derived-code-facts`).
- This is settled doctrine, not a per-case debate: the average-vs-jitter question is **closed** — jitter-where-it-matters wins.
