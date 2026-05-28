---
type: data-discipline
stage: 2-draft
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.1 (per D-54; integrated with event-sourced-aggregator)
sister_specs:
  - framework-patterns/event-sourced-aggregator-o1-pattern.md (canonical sister)
  - framework-patterns/global-aggregator-readonly-pattern.md (parent pattern; aggregator role)
tags: [data-discipline, running-aggregate, o1-compute, cycle-recompute, atomic-add]
surface: [aggregator, accounting, statistics]
applies_at_skills: [/precoding-audit-gate, /dod-audit]
---

# Running aggregate vs cycle-recompute discipline (Stage 2 DRAFT)

**Pattern intent:** Architectural axis: state aggregates can be maintained as RUNNING values (event-driven; O(1) update; bit-exact) OR recomputed each cycle (pull-model; O(N) cycle; stale-up-to-cycle). Discipline guides which to use based on access cadence + correctness requirements.

## Problem statement

Multi-source state aggregation has fundamental choice:

**Option A (running aggregate / push):**
- Each producer atomically updates aggregate on event
- Reader gets bit-exact current value (O(1) read)
- Tight cache-line contention if N producers + 1 reader

**Option B (cycle recompute / pull):**
- Producers update own state independently
- Aggregator periodically iterates + recomputes
- O(N) per cycle; stale up to cycle boundary
- No cache contention between producers + aggregator (cached writes to own slot)

Different use cases favor different choices.

## Use case taxonomy

### Use running aggregate when:

✅ Reader needs SUB-CYCLE latency (kill-switch evaluation)
✅ Bit-exact total matters (financial accounting)
✅ Update rate bounded (cache contention manageable)
✅ Atomic ops on aggregate value type (uint64 / int32; FPN via __int128 or split)

**Example:** `.E.1` aggregator P&L total — event-driven O(1) push per fill; kill-switch reads instantly.

### Use cycle recompute when:

✅ Reader cadence is periodic (not latency-critical)
✅ Approximate is OK (don't need bit-exact running)
✅ Update rate is high (would cause cache contention if push)
✅ Aggregation involves complex math (not just addition)

**Example:** Latency histograms; statistics like p99 (computed from buckets each cycle).

### Hybrid (running + integrity-verify cycle):

✅ Sub-cycle latency needed (running aggregate)
✅ Also want drift detection (integrity verify)

**Example:** `.E.1` aggregator — event-driven running + periodic integrity-verification cycle catches any drift between push-aggregate and seqlock-walk.

## Defense-in-depth example (.E.1)

Per `framework-patterns/event-sourced-aggregator-o1-pattern.md`:

```cpp
void NodeSlowPath_OnFill(NodeState<F>& node, const FillEvent<F>& fill) {
    // Path A: Update per-node state (via seqlock; readers see consistent)
    NodeAccountState_PublishViaSeqlock(node);

    // Path B: Atomic-add to aggregator running total (push model)
    Aggregator_OnFill(g_state.aggregator, node, fill);
}

// Periodic integrity check (defense)
void Aggregator_IntegrityCycle(EngineState<F>& state) {
    FPN<F> verify = WalkAllNodesViaSeqlock(state);   // O(N)
    FPN<F> cached = state.aggregator.global.cached_total;   // O(1) atomic
    if (!FPN_Equal(verify, cached)) {
        // Drift detected; log + alert + self-heal
        state.aggregator.global.cached_total = verify;
    }
}
```

## Concurrency considerations

**Running aggregate (push):**
- Multi-writer atomic on aligned cache line
- N producers contend if simultaneous
- ~10ns per atomic_fetch_add on x86_64
- Cache-line ping-pong if cross-core writes frequent

**Cycle recompute (pull):**
- Each producer writes own slot (no contention)
- Reader walks via seqlock (lock-free; possibly torn but retries)
- O(N) per cycle but no contention

## When discipline matters

This discipline matters when designing:
- Aggregator state for multi-node engines
- Statistics collection (histograms; percentiles)
- Capital allocation tracking
- Rate-limit budget tracking

Per `feedback_event_sourced_aggregator_o1_pattern` (Concept 1 from operator research 2026-05-28; codified at D-54): when kill-switch latency matters, USE running aggregate; integrity-verify cycle as safety net.

## Stage progression

- **Stage 2 DRAFT** (current; .E.1 hybrid pattern proves discipline)
- **Stage 3 first canonical** at .E.1 ship close (when event-sourced-aggregator-o1 fully integrated)
- **Stage 4 cohort** when 2nd surface applies (e.g., per-strategy aggregation; latency histograms)

## Cross-references

- Sister canonical: `framework-patterns/event-sourced-aggregator-o1-pattern.md`
- Parent: `framework-patterns/global-aggregator-readonly-pattern.md`
- Source: F-11 + D-54 (Caramel-cited "Zero-Walk O(1) Event-Sourced Portfolios" Concept 1; 2026-05-28)
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md`
