---
name: feedback_critical_moment_determinism_not_average_latency
description: "The latency cost function is jitter-at-the-critical-moment, NOT low average — a spike correlated with order placement / signal commitment is the worst shape; closed doctrine, don't re-litigate average-vs-jitter"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1ca40db2-672f-4994-b19c-e3440ae9a8b9
  sister_specs: [feedback_mechanically_verify_derived_code_facts.md]
  tags: []
---

For this capital-bearing HFT engine the latency cost is **NOT average latency** — it is **jitter correlated with the actions that matter** (order placement, signal commitment). A design that spikes *exactly* on the trade tick is the worst possible shape: variance where it's most expensive (worse fills / adverse selection, precisely when acting on a signal). A predictable-but-higher latency at the critical moment beats a lower *average* that spikes when capital is committed — a constant is hedgeable; correlated variance is not.

**Why:** the hot-path trade-event push is a data-dependent branch (`ExecutionCore.hpp:483`); the predictor trains on no-trade→not-taken, so the rare trade is a GUARANTEED mispredict+flush landing on the trade-placement tick. "Rare + well-predicted = low cost" is AVERAGE-case reasoning — true for the 99% that don't matter, guaranteed on the 1% that do. Caramel corrected this directly + wants it settled doctrine.

**How to apply:** a hot/slow-path branch / cache-miss / flush correlated with order-placement or signal-commitment is a DEFECT even when "rare" — make it branchless (H20: always-write + mask-the-advance). This is the deep WHY of H20 (branchless even when nominally slower) + reframes H8 (≤500ns = predictable AT the critical moment, not a low average). The branchless trade (a dummy-write/quiet-tick to delete the trade-tick flush) is ACCEPTED on purpose — an "average rose 1%" measurement does NOT veto it; measurement confirms the variance win + budget, never re-litigates the principle. The average-vs-jitter debate is CLOSED. Spec `DESIGN_SPECS/refactor-patterns/critical-moment-determinism-over-average-latency.md`; sisters [[feedback_mechanically_verify_derived_code_facts]] (measure the jitter, don't assume it) + branchless-dispatch-discipline (H7/H20).
