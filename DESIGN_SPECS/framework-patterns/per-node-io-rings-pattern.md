---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.4
canonical_applications:
  - v5.15.5.F.4d.1.E.4 (each per-node owns its own io_uring rings; NUMA-aware)
sister_specs:
  - concurrency-patterns/io-uring-kernel-bypass-pattern.md (parent)
  - framework-patterns/per-cluster-shared-resource-pattern.md (relationship: adapter eliminated)
tags: [framework-discipline, per-node-io, numa-aware, io-uring]
surface: [per-node-io, network-stack]
---

# Per-node io_uring rings pattern

**Pattern intent:** Each per-node owns its own io_uring SQ + CQ rings. NUMA-aware ring placement on local NUMA node. Eliminates per-cluster adapter worker thread (per-node owns I/O lifecycle).

## Pattern

```cpp
struct NodeState {
    // ... existing per-.E.1 fields ...

    // NEW at .E.4: per-node io_uring + WS connection
    alignas(64) NodeIORings io_rings;

    // ... rest ...
};

// At boot: allocate ring on local NUMA node
void NodeIORings_Init(NodeIORings* rings, int numa_node) {
    unsigned long nodemask = 1UL << numa_node;
    set_mempolicy(MPOL_BIND, &nodemask, sizeof(nodemask) * 8);
    io_uring_queue_init(rings->ring_depth /* 256 */, &rings->ring, 0);
    set_mempolicy(MPOL_DEFAULT, nullptr, 0);

    // kTLS enable on socket
    KTLS_Enable(rings->ws_conn.socket_fd, rings->ws_conn.ssl_state);
}
```

## Trade-off vs .E.3 (per-cluster shared WS)

| Axis | `.E.3` per-cluster shared WS | `.E.4` per-node WS + io_uring |
|---|---|---|
| Connection count | 1 per cluster | N per cluster |
| Memory | ~200KB per cluster | N × ~200KB per cluster |
| Contention | per-cluster lock-free | per-node zero contention |
| SPOF | per-cluster (1 conn down → cluster nodes affected) | per-node (1 conn down → 1 node) |
| Adapter worker thread | YES (per cluster) | DELETED |

## NUMA-aware placement

Per `data-disciplines/cache-line-discipline.md` + production thread topology:

```
# configs/clusters/binance/nodes/node_0/core.cfg:
topology.hot_cpu = 4
topology.slow_cpu = 5
topology.numa_node = 0      # ring allocated on this NUMA
```

Verify at /proc/<pid>/numa_maps.

## Cross-references

- Parent: `concurrency-patterns/io-uring-kernel-bypass-pattern.md`
- Sister: `concurrency-patterns/ktls-kernel-tls-pattern.md`
- First application: `plans/v5.15.5.F.4d.1.E.4-io-uring-ktls.md`
