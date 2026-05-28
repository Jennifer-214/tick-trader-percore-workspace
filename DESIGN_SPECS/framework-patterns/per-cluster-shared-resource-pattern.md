---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.1
canonical_applications:
  - v5.15.5.F.4d.1.E.1 (per-cluster producer + adapter + WS threads)
sister_specs:
  - framework-patterns/foreach-exchange-meta-registry-pattern.md (cluster = exchange)
  - framework-patterns/per-cluster-producer-pattern.md (specific per-cluster thread)
  - framework-patterns/cluster-node-hierarchy-filesystem-layout-pattern.md (sister at config layer)
tags: [framework-discipline, per-cluster-resources, thread-topology, multi-exchange]
surface: [cluster-state, thread-architecture]
applies_at_skills: [/precoding-audit-gate, /dod-audit]
---

# Per-cluster shared resource pattern

**Pattern intent:** Each cluster (exchange instance) has its OWN producer + adapter + WS thread infrastructure. Shared across cluster's N nodes; isolated across clusters. One cluster's exchange WS drop doesn't affect other clusters.

## Problem statement

Multi-exchange engine needs:
- Per-exchange market-data stream (Binance trade WS; Alpaca trade-stream; etc.)
- Per-exchange submit path (BinanceAdapter; AlpacaAdapter; etc.)
- Per-exchange fill stream (Binance user-data WS; Alpaca trade-updates; etc.)

Options for placement:
1. **Per-deployment shared** — 1 producer/adapter for all clusters. PROBLEM: couples cluster failure modes (one bad cluster blocks all).
2. **Per-cluster shared** — 1 producer/adapter per cluster; shared across that cluster's nodes. ISOLATION across clusters; sharing within.
3. **Per-node owned** — each node has own. PROBLEM: N×M connections to single exchange; wasteful at retail submit rates.

**Pattern: option 2.** Per-cluster isolation; per-node sharing within cluster.

## Pattern description

### Cluster state container

```cpp
template<typename AdapterT>
struct alignas(64) ClusterState {
    // === BOOT-TIME IMMUTABLE ===
    ExchangeEnum exchange_id;
    const char* exchange_name;
    char market_data_endpoint[256];
    char rest_endpoint[256];
    char ws_api_endpoint[256];
    char user_data_endpoint[256];

    // === PER-CLUSTER SHARED THREADS (1 each per cluster) ===
    pthread_t producer_thread;                  // reads market-data WS; fan-outs to cluster nodes
    pthread_t adapter_thread;                   // adapter worker; consumes submit queue
    pthread_t userdata_thread;                  // user-data WS; routes fills to nodes

    // === SHARED RESOURCES ===
    AdapterT adapter;                           // adapter state
    SubmitQueue<F> submit_queue;                // MPSC (nodes write; adapter reads); vestigial at .E.4+
    SubAccountPool<AdapterT> subaccounts;       // per-cluster sub-account pool

    // === RATE LIMIT ===
    alignas(64) std::atomic<int32_t> rate_tokens;
    std::atomic<uint64_t> rate_window_start_us;
    uint32_t rate_max_per_minute;

    // === HEALTH / RECONNECT ===
    alignas(64) struct {
        std::atomic<uint8_t> connected;
        std::atomic<uint64_t> last_disconnect_us;
        std::atomic<uint32_t> reconnect_count;
        std::atomic<uint64_t> outage_threshold_us;
    } health;

    // === CLUSTER-LEVEL KILL SWITCH ===
    alignas(64) std::atomic<uint8_t> cluster_kill_flag;

    // === NODE LIST ===
    NodeState<F>* nodes[MAX_NODES_PER_CLUSTER];
    uint32_t node_count;
};
```

### Per-cluster topology

```
DEPLOYMENT
├── Cluster: binance (cores reserved per cfg)
│   ├── Producer thread (1 CPU core; reads Binance trade WS; fan-outs)
│   ├── Adapter worker thread (1 CPU core; consumes submit queue; HMAC sign; submits)
│   ├── User-data WS thread (1 CPU core; routes fills)
│   ├── Node 0 (hot + slow CPU pair)
│   ├── Node 1
│   ├── ...
│   └── Node N
├── Cluster: alpaca (cores reserved per cfg)
│   ├── Producer thread (separate; reads Alpaca trade-stream)
│   ├── Adapter worker thread (separate; REST submits)
│   ├── Trade-stream thread (separate; routes fills)
│   └── ...nodes
└── Aggregator (1 CPU core; deployment-wide)
```

### Isolation property

If Binance WS drops:
- Binance cluster's producer thread → reconnect with backoff
- Binance cluster's adapter worker → submits queued; retried after reconnect
- Alpaca cluster's producer/adapter UNAFFECTED
- IBKR cluster's producer/adapter UNAFFECTED
- Global aggregator still runs; observes Binance cluster halted; reports

If Binance cluster has prolonged outage (> threshold):
- Cluster_kill_flag set
- Binance cluster's nodes halt trading
- Other clusters' nodes continue
- Operator alerted

### Per-cluster thread topology in CPU pinning

```
# In configs/cluster/binance/cluster.cfg:
topology.producer_cpu = 0
topology.adapter_cpu = 1
topology.userdata_cpu = 2
topology.numa_node = 0

# In configs/cluster/binance/nodes/node_0/core.cfg:
topology.hot_cpu = 3
topology.slow_cpu = 4
```

Production mode: explicit pinning + isolcpus.
Dev mode: OS-scheduled (per `dev-vs-production-thread-topology-pattern.md`).

## Stage progression criteria

- **Stage 3 first canonical** (`.E.1`): per-cluster shared resources for Binance
- **Stage 4 cohort** (when 2nd cluster added): pattern proven for isolation across clusters
- **Stage 5 CLAUDE.md** (3rd cluster + discipline matures): promoted

## Anti-patterns avoided

- **Per-deployment shared producer/adapter** — couples cluster failure modes
- **Per-node owned producer/adapter** — wasteful resource amplification
- **Cross-cluster thread sharing** — defeats per-cluster isolation

## Cross-references

- Parent: `framework-patterns/foreach-exchange-meta-registry-pattern.md`
- Sister: `framework-patterns/per-cluster-producer-pattern.md`
- Sister: `framework-patterns/cluster-node-hierarchy-filesystem-layout-pattern.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md`
