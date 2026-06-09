---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.1 (per D-54)
canonical_applications:
  - v5.15.5.F.4d.1.E.1 (event-driven push-model aggregator)
sister_specs:
  - framework-patterns/global-aggregator-readonly-pattern.md (parent pattern; aggregator role)
  - framework-patterns/kill-switch-hierarchical-pattern.md (consumer; latency-sensitive)
  - data-disciplines/running-aggregate-vs-cycle-recompute-discipline.md (NEW; tangentially)
tags: [framework-discipline, aggregator, event-sourcing, o1-latency, push-model, single-writer]
surface: [aggregator, kill-switch-latency, atomic-state]
applies_at_skills: [/precoding-audit-gate, /dod-audit, /latency-track]
---

# Event-sourced O(1) aggregator pattern

**Pattern intent:** Aggregator state updated INCREMENTALLY on each per-node fill (push-model) instead of cycle-based recompute (pull-model). Kill-switch evaluation becomes O(1) per fill (~50μs latency floor) vs O(N×cycles) per scan (~100ms latency floor).

## Problem statement

Cycle-based aggregator (pull-model):
- Aggregator polls all N nodes every 100ms
- Recomputes totals from scratch
- Kill-switch evaluation latency floor: 100ms cycle
- Risk: fast drawdown between cycles → kill switch late

Event-sourced aggregator (push-model):
- Each per-node fill triggers atomic_fetch_add on aggregator state
- Kill-switch evaluation happens immediately after fill
- Latency floor: ~50μs (fill arrival time)
- Aggregator state always-exact

**2000× latency improvement** for kill-switch evaluation. Critical for fast drawdown events.

## Pattern description

### Per-node fill triggers aggregator update

```cpp
void NodeSlowPath_HandleFill(NodeState<F>& node, const FillEvent<F>& fill) {
    // 1. Update own per-node state (existing pattern)
    node.slow_account.realized_pnl = FPN_Add(node.slow_account.realized_pnl, fill.net_pnl);
    node.slow_account.fills_count++;
    NodeAccountState_PublishViaSeqlock(node);

    // 2. NEW: Atomically update aggregator running totals (push model)
    Aggregator_OnFill(g_state.aggregator, node, fill);
}

// Aggregator receives fill; updates atomic running totals
void Aggregator_OnFill(AggregatorState& agg, NodeState<F>& node, const FillEvent<F>& fill) {
    // Skip paper-mode in real totals
    if (node.hot.mode != NODE_MODE_LIVE && node.hot.mode != NODE_MODE_SHADOW) {
        return;
    }

    uint32_t cluster_id = node.binding.cluster_id;

    // Atomic increment cluster's running totals
    FPN_AtomicAdd(&agg.per_cluster[cluster_id].cached_realized_pnl, fill.net_pnl);
    agg.per_cluster[cluster_id].cached_version.fetch_add(1, std::memory_order_release);
    agg.per_cluster[cluster_id].fills.fetch_add(1, std::memory_order_relaxed);

    // Atomic increment global totals
    FPN_AtomicAdd(&agg.global.cached_total_realized_pnl, fill.net_pnl);
    agg.global.cached_version.fetch_add(1, std::memory_order_release);
    agg.global.total_fills.fetch_add(1, std::memory_order_relaxed);

    // EVENT-DRIVEN kill check (immediate; no cycle wait)
    FPN<F> cluster_drawdown = ComputeClusterDrawdown(agg, cluster_id);
    if (FPN_GreaterEq(cluster_drawdown, agg.per_cluster_kill_drawdown_threshold[cluster_id])) {
        agg.per_cluster_kill[cluster_id].store(1, std::memory_order_release);
        ClusterMirrorKillFlag(cluster_id);
    }

    FPN<F> global_drawdown = ComputeGlobalDrawdown(agg);
    if (FPN_GreaterEq(global_drawdown, agg.global_kill_drawdown_threshold)) {
        agg.global_kill_flag.store(1, std::memory_order_release);
        GlobalMirrorKillFlag();
    }
}
```

### FPN_Binary<F> atomic-add semantics

FPN_Binary<F=64> is 16 bytes (a bare `__int128`; two's-complement, sign in the top bit — post Ship-A `v5.15.5.F.4d.1.E.0.7`). Not native-atomic on x86_64 (16B > the 8B single-word atomic width — the point holds). Options:

1. **__int128 atomic** (16B CAS via `cmpxchg16b`; sometimes available; not portable)
2. **Per-node delta accumulators** (each node atomic-write own slot; aggregator sums lazily)
3. **Spinlock per FPN_Binary field** (violates H3 if used in hot path; OK at slow-path)
4. **Approximate via uint64_t for fast-path; full FPN_Binary at cycle boundary**

Current `.E.1` implementation: option 2 (per-node delta accumulators with atomic ops on aligned fields; sum lazily at aggregator read).

```cpp
// Per-cluster delta accumulator (atomic-friendly)
struct alignas(64) ClusterDelta {
    std::atomic<int64_t> realized_pnl_atoms;   // FPN raw atom count
    std::atomic<int64_t> open_notional_atoms;
    std::atomic<uint64_t> fills_count;
};

// Per-node fill triggers atomic delta apply
void Aggregator_AtomicAddFill(ClusterDelta& delta, FPN<F> delta_pnl, FPN<F> delta_notional) {
    int64_t pnl_atoms = FPN_ToRawAtoms(delta_pnl);
    int64_t notional_atoms = FPN_ToRawAtoms(delta_notional);
    delta.realized_pnl_atoms.fetch_add(pnl_atoms, std::memory_order_relaxed);
    delta.open_notional_atoms.fetch_add(notional_atoms, std::memory_order_relaxed);
    delta.fills_count.fetch_add(1, std::memory_order_relaxed);
}
```

### Defense-in-depth: integrity verification cycle

Per `feedback_motivated_collaborator_for_caramel` (best-software path): event-driven primary + cycle-based integrity verification as safety net.

```cpp
void Aggregator_IntegrityCycle(EngineState<F>& state) {
    // Walk all nodes via seqlock; recompute totals from scratch
    FPN<F> verify_realized = ComputeTotalRealizedFromNodes(state);

    // Compare to cached running aggregate
    FPN<F> cached_realized = FPN_AtomicLoad(&state.aggregator.global.cached_total_realized_pnl);
    if (!FPN_Equal(verify_realized, cached_realized)) {
        // Integrity drift detected
        state.aggregator.last_integrity_drift_count++;
        LOG_ERROR("Aggregator integrity drift: cached=%s, walked=%s",
                  FPN_ToString(cached_realized), FPN_ToString(verify_realized));
        // Webhook alert
        EmitOperatorAlert(ALERT_AGGREGATOR_DRIFT, ...);

        // Self-heal: trust seqlock walk over running aggregate
        FPN_AtomicStore(&state.aggregator.global.cached_total_realized_pnl, verify_realized);
    }
}
```

Runs every 100ms (default; cfg-overridable). Drift count exposed via Prometheus metric.

## Latency analysis

| Path | Cycle-based (pre-D-54) | Event-driven (D-54) |
|---|---|---|
| Aggregator state update | 100ms (every cycle) | ~50μs (per fill) |
| Kill-switch latency floor | 100ms | ~50μs |
| Worst-case kill-switch (drawdown burst) | 100ms + slow-path | ~50μs + atomic propagation (~1μs) |
| CPU overhead | Steady N×O(1) per cycle | Per-fill O(1); rare cycle O(N) for integrity |

Net: ~2000× latency improvement for kill-switch.

## Correctness considerations

- **Atomicity:** atomic_fetch_add on aligned 64-bit fields; lock-free; bit-exact
- **Ordering:** memory_order_acq_rel for state updates; release/acquire for kill flag propagation
- **Cache contention:** N writers (per-node) + 1 reader (aggregator) per cluster delta line. At 20 fills/sec aggregate, contention is negligible.
- **Mode separation:** paper-mode fills SKIP aggregator update (tagged separately)
- **Integrity drift detection:** cycle-based safety net catches any anomaly

## Stage progression criteria

- **Stage 3 first canonical** (`.E.1`): event-sourced O(1) aggregator implemented
- **Stage 4 cohort** (when 2nd application surfaces; e.g., per-strategy aggregation): pattern proven
- **Stage 5 CLAUDE.md** (3rd application + discipline matures): promoted

## Anti-patterns avoided

- **Cycle-based-only aggregation** — kill-switch latency floor too high for fast drawdown events
- **Per-fill aggregation without integrity verification** — silent drift class
- **Cross-cluster cache-line contention** — per-cluster delta cache-line aligned; no false sharing

## Cross-references

- Parent: `framework-patterns/global-aggregator-readonly-pattern.md`
- Refinement source: `D-54` in `decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md`
- Source operator research: F-11 (Caramel cited "Zero-Walk O(1) Event-Sourced Portfolios" 2026-05-28)
- Sister: `framework-patterns/kill-switch-hierarchical-pattern.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md`
