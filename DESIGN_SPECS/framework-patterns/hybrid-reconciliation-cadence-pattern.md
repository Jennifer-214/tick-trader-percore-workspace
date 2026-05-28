---
type: framework-pattern
stage: 2-draft
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.1 (interface) + v5.15.5.F.4d.1.E.5 (full implementation)
sister_specs:
  - framework-patterns/per-node-economic-isolation-pattern.md (per-sub-account reconcile)
tags: [framework-discipline, reconciliation, hybrid-cadence]
surface: [reconciliation, drift-detection]
---

# Hybrid reconciliation cadence pattern (Stage 2 DRAFT)

**Pattern intent:** Reconciliation against exchange truth at HYBRID cadence: per-fill triggered + time-based (every 5min). Per D-50.

## Pattern

### Per-fill triggered (low latency)

```cpp
void NodeSlowPath_OnFill(NodeState<F>& node, const FillEvent<F>& fill) {
    NodeSlowPath_UpdateAccount(node, fill);

    if (g_cfg.reconcile_per_fill) {
        // Trigger async reconcile after fill
        ReconcileQueue_Submit(node.binding.cluster_id, node.binding.subaccount_id);
    }
}
```

### Time-based (every 5min; safety net)

```cpp
void ClusterReconcile_TimerCallback(ClusterState<...>& cluster) {
    for each node in cluster:
        ReconcileQueue_Submit(cluster.exchange_id, node.binding.subaccount_id);
}
```

Configurable cadence:
```
# configs/engine.cfg:
reconcile_per_fill = true       # default
reconcile_interval_seconds = 300   # 5 min
```

### Boot-time parallel reconcile

```cpp
void Engine_BootReconcile(EngineState<F>& state) {
    std::array<pthread_t, MAX_NODES> threads;
    for each node:
        pthread_create(&threads[n], nullptr, ReconcileThread, &state.nodes[n]);
    for each thread:
        pthread_join(threads[n], nullptr);
}
```

## Drift detection

```cpp
void Reconcile_Verify(NodeState<F>& node) {
    PositionList<F> exchange_truth;
    tt::query_positions<AdapterT>(adapter, node.binding.subaccount_id, &exchange_truth);

    if (!PositionEqual(node.slow_account.position, exchange_truth[0])) {
        LOG_WARN("Drift detected: node=%u; engine=%s exchange=%s",
                 node.binding.subaccount_id, ...);
        // Trust exchange truth
        node.slow_account.position = exchange_truth[0];
        AuditLog_Append(reconcile_discrepancy_event);
        EmitWebhookAlert(ALERT_RECONCILE_DRIFT);
    }
}
```

## Stage progression

- **Stage 2 DRAFT** (.E.1 interface)
- **Stage 3 first canonical** at `.E.5` (full implementation with real sub-accounts)
- **Stage 4 cohort** at 2nd application

## Cross-references

- Sister: `framework-patterns/per-node-economic-isolation-pattern.md`
- Decision: D-50
