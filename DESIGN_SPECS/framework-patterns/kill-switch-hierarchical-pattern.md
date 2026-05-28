---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.1
canonical_applications:
  - v5.15.5.F.4d.1.E.1 (3-layer kill switch hierarchy: global / per-cluster / per-node)
sister_specs:
  - framework-patterns/global-aggregator-readonly-pattern.md (aggregator OWNS write of kill flags)
  - framework-patterns/event-sourced-aggregator-o1-pattern.md (event-driven kill check)
  - meta-disciplines/single-source-of-truth-discipline.md (single-writer principle)
tags: [framework-discipline, kill-switch, safety, atomic-flags, hierarchical]
surface: [aggregator, per-cluster-state, per-node-state, slow-path-entry]
applies_at_skills: [/precoding-audit-gate, /dod-audit, /parity-check]
---

# Kill switch hierarchical pattern

**Pattern intent:** 3-layer hierarchical kill switch (global / per-cluster / per-node). Aggregator OWNS write of kill flags. Per-nodes mirror via atomic read at slow-path entry (cheap; lock-free).

## Problem statement

Multi-cluster engine needs hierarchical safety:
- **Per-node:** specific node behaving badly → halt that node only
- **Per-cluster:** exchange API issue → halt that cluster's nodes; others continue
- **Global:** existential threat (system-wide drawdown; major outage) → halt ALL trading

Each layer must:
- Update atomically (no torn writes)
- Be readable in O(1) at per-node slow-path entry (cheap atomic read)
- Survive engine crash (mmap'd state recovery)
- Be operator-overridable via fox-cli

## Pattern description

### Atomic flag placement

```cpp
// Global (1 deployment-wide; aggregator-owned write)
struct AggregatorState {
    alignas(64) std::atomic<uint8_t> global_kill_flag;
    std::atomic<uint8_t> per_cluster_kill[NUM_EXCHANGES];
    // ...
};

// Per-cluster (1 per cluster; aggregator + manual operator write)
struct ClusterState {
    alignas(64) std::atomic<uint8_t> cluster_kill_flag;
    // ...
};

// Per-node (mirrors of global + cluster + own)
struct NodeState {
    alignas(64) struct {
        std::atomic<uint8_t> per_node_kill;             // aggregator or operator sets
        std::atomic<uint8_t> per_cluster_kill_mirror;   // mirrored from cluster
        std::atomic<uint8_t> global_kill_mirror;        // mirrored from global
    } kill_flags;
};
```

### Aggregator writes; nodes mirror

```cpp
// Aggregator computes drawdown; sets kill flags if threshold breached
void Aggregator_CheckKillThresholds(AggregatorState& agg) {
    // Per-cluster check
    for (uint32_t c = 0; c < NUM_EXCHANGES; ++c) {
        FPN<F> cluster_drawdown = ComputeClusterDrawdown(agg, c);
        uint8_t kill = FPN_GreaterEq(cluster_drawdown,
                                     agg.per_cluster_kill_drawdown_threshold[c]) ? 1 : 0;
        agg.per_cluster_kill[c].store(kill, std::memory_order_release);

        // Mirror to all cluster's nodes (atomic; immediate visibility)
        if (kill) {
            for (NodeState<F>* node : g_state.clusters[c].nodes) {
                node->kill_flags.per_cluster_kill_mirror.store(1, std::memory_order_release);
            }
        }
    }

    // Global check
    FPN<F> global_drawdown = ComputeGlobalDrawdown(agg);
    uint8_t kill = FPN_GreaterEq(global_drawdown, agg.global_kill_drawdown_threshold) ? 1 : 0;
    agg.global_kill_flag.store(kill, std::memory_order_release);

    if (kill) {
        // Mirror to ALL nodes
        for (each cluster, each node) {
            node->kill_flags.global_kill_mirror.store(1, std::memory_order_release);
        }
    }
}
```

### Per-node slow-path entry check (3 atomic reads; cheap)

```cpp
void NodeSlowPath_Cycle(NodeState<F>& node) {
    // 3 atomic reads (3 cache lines; each ~5-10ns under load; total ~30ns)
    uint8_t global = node.kill_flags.global_kill_mirror.load(std::memory_order_acquire);
    uint8_t cluster = node.kill_flags.per_cluster_kill_mirror.load(std::memory_order_acquire);
    uint8_t per_node = node.kill_flags.per_node_kill.load(std::memory_order_acquire);

    if (global || cluster || per_node) {
        NodeSlowPath_HandleKilled(node);
        return;
    }

    // Normal slow-path cycle
}
```

Per H7 hot-path branchless: kill check is at SLOW-PATH entry (NOT hot path); branching here is acceptable.

### Operator manual override

```bash
# Halt specific node
fox-cli set-kill node binance/node_2 ON

# Halt cluster
fox-cli set-kill cluster binance ON

# Global halt
fox-cli set-kill global ON

# Resume
fox-cli set-kill node binance/node_2 OFF
```

fox-cli writes to per-node/cluster/global atomic via UDS command channel. Per-node slow-path picks up at next cycle.

### Crash recovery

Kill flags survive engine crash (mmap'd state file persists). On engine restart, kill flags read from mmap; nodes start in killed state if previously killed.

Operator must explicitly resume via fox-cli post-restart (per `on_crash_restart_action = resume` default; operator-overridable).

## Threshold configuration

```
# configs/clusters/binance/cluster.cfg:
kill_drawdown_threshold = 0.10    # 10% cluster drawdown triggers cluster kill

# configs/clusters/binance/nodes/node_0/core.cfg:
kill_drawdown_threshold = 0.20    # 20% per-node drawdown triggers per-node kill

# configs/engine.cfg:
global_kill_drawdown_threshold = 0.05  # 5% deployment-wide drawdown triggers global kill
```

Operator-tunable via cfg + runtime via fox-cli.

## Stage progression criteria

- **Stage 3 first canonical** (`.E.1`): 3-layer hierarchy implemented
- **Stage 4 cohort** (when 2nd application surfaces; e.g., per-strategy kill switch): pattern proven
- **Stage 5 CLAUDE.md** (3rd application + discipline matures): promoted

## Anti-patterns avoided

- **Single kill flag for entire engine** — insufficient granularity
- **Per-node kill only** — no cluster-wide halt
- **Mutex-protected kill flag** — H3 violation
- **Branchy kill check on hot path** — hot path is BRANCHLESS (H7); kill check at SLOW path

## Cross-references

- Parent: `framework-patterns/global-aggregator-readonly-pattern.md`
- Sister: `framework-patterns/event-sourced-aggregator-o1-pattern.md` (event-driven kill check)
- Parent: `meta-disciplines/single-source-of-truth-discipline.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md`
