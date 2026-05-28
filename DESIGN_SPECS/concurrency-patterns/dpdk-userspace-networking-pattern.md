---
type: concurrency-pattern
stage: 2-draft
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.8 (DEFERRED INDEFINITELY per D-57; no hardware)
sister_specs:
  - concurrency-patterns/io-uring-kernel-bypass-pattern.md (sister; kernel-bypass-lite)
  - concurrency-patterns/userspace-tls-pattern.md (sister; userspace TLS at DPDK)
tags: [concurrency, dpdk, userspace-networking, kernel-bypass, hardware-required]
surface: [network-stack, latency-critical]
---

# DPDK userspace networking pattern (Stage 2 DRAFT — DEFERRED)

**Pattern intent:** Userspace TCP/IP via DPDK; kernel-bypass; per-NIC poll mode. ~3-5μs tick-to-wire on commodity x86_64. DEFERRED per D-57 (operator lacks DPDK-compatible hardware).

## When to revisit

Re-activate at `.E.8` ship if/when:
- Operator acquires DPDK-compatible NIC (Mellanox / Intel; verified compatibility)
- OR operator co-locates on cloud instance with DPDK-supported NIC

## Pattern outline

```cpp
struct DPDKEnvironment {
    uint16_t num_ports;
    uint16_t num_queues_per_port;
    rte_mempool* mbuf_pool;
};

// Per-node DPDK context
struct NodeDPDKContext {
    uint16_t port_id;
    uint16_t queue_id;        // = node_id (RSS hash routing)
    rte_mempool* mbuf_pool;
    TCPState tcp_state;       // userspace TCP
    UserspaceTLSState tls_state;
};

int DPDK_SendTCPPayload(NodeDPDKContext* ctx, const void* data, size_t len) {
    rte_mbuf* mbuf = rte_pktmbuf_alloc(ctx->mbuf_pool);
    UserspaceTCP_BuildSegment(&ctx->tcp_state, &ctx->tls_state, mbuf, data, len);
    return rte_eth_tx_burst(ctx->port_id, ctx->queue_id, &mbuf, 1) == 1 ? 0 : -1;
}
```

## Latency target

- Tick → wire: ~3-5μs (vs ~10-20μs at `.E.4` io_uring + kTLS)
- ~5× improvement on-box

## Hardware requirements

- DPDK-compatible NIC (verified list at https://core.dpdk.org/supported/)
- Hugepages enabled
- isolcpus + nohz_full
- DPDK-version-compatible kernel

## Stage progression

- **Stage 2 DRAFT**: reference; awaits hardware
- **Stage 3 first canonical**: when operator deploys DPDK-supported hardware

## Cross-references

- Sister: `concurrency-patterns/io-uring-kernel-bypass-pattern.md`
- Sister: `concurrency-patterns/userspace-tls-pattern.md`
- Future: `plans/v5.15.5.F.4d.1.E.8-dpdk-kernel-bypass.md` (deferred)
