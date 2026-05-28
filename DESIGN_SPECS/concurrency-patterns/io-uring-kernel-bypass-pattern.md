---
type: concurrency-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.4
canonical_applications:
  - v5.15.5.F.4d.1.E.4 (per-node io_uring + kTLS)
sister_specs:
  - concurrency-patterns/ktls-kernel-tls-pattern.md (sister; kernel-side TLS)
  - framework-patterns/per-node-io-rings-pattern.md (sister; per-node placement)
  - concurrency-patterns/persistent-ws-connection-management-pattern.md (parent; integration target)
tags: [concurrency, io-uring, kernel-bypass-lite, async-io, linux-specific]
surface: [network-io, syscall-overhead, latency-critical]
applies_at_skills: [/precoding-audit-gate, /latency-track, /hft-audit]
---

# io_uring kernel-bypass pattern

**Pattern intent:** Per-node io_uring (SQ + CQ rings) for async network I/O. Submit batching reduces syscall overhead. Completion polling at slow-path entry. Kernel-bypass-lite (not full userspace stack like DPDK; still uses kernel TCP/IP). Saves ~10-20μs per I/O operation vs userspace-syscall path.

## Problem statement

Userspace I/O via send() + recv() syscalls:
- send() = kernel context switch (~5μs)
- TLS encrypt in userspace via SSL_write (~10μs CPU)
- Kernel TCP/IP stack (~5μs)
- Total: ~20-25μs CPU per I/O

io_uring + kTLS:
- io_uring_prep_send = userspace queue push (~200ns; no syscall)
- io_uring_submit = batched syscall (amortized ~1μs per submit)
- kTLS encrypt in kernel (~3μs; AES-NI accelerated)
- Kernel TCP/IP stack (~5μs; unchanged)
- Total: ~10μs CPU per I/O

**Net: ~10-15μs saved per I/O.** Combined with `.E.3` (~15-25ms saved per submit via WS-API), stacked latency improvement.

## Pattern description

### Per-node io_uring rings

```cpp
struct alignas(64) NodeIORings {
    struct io_uring ring;                     // liburing handle
    unsigned ring_depth;                      // typically 256

    alignas(64) struct {
        uint64_t next_user_data;
        SPSCRing<PendingIO, 256> pending;     // tracks in-flight ops
    } sq;

    alignas(64) struct {
        std::atomic<uint64_t> completions_processed;
    } cq;

    PersistentWSConnection_Inlined ws_conn;   // per-node from .E.4
    int numa_node;                            // NUMA-aware placement
};
```

### Initialization (NUMA-aware)

```cpp
int IOUring_Init_NUMA(NodeIORings* rings, int numa_node) {
    // Set mem policy to bind allocations to NUMA node
    unsigned long nodemask = 1UL << numa_node;
    set_mempolicy(MPOL_BIND, &nodemask, sizeof(nodemask) * 8);

    int ret = io_uring_queue_init(rings->ring_depth, &rings->ring, 0);

    set_mempolicy(MPOL_DEFAULT, nullptr, 0);

    rings->numa_node = numa_node;
    return ret;
}
```

### Submit via io_uring

```cpp
int IOUring_SubmitWSFrame(NodeIORings* rings, const char* frame, size_t frame_len) {
    struct io_uring_sqe* sqe = io_uring_get_sqe(&rings->ring);
    if (!sqe) {
        // SQ full; drain completions first
        IOUring_PollCompletions(...);
        sqe = io_uring_get_sqe(&rings->ring);
        if (!sqe) return -EAGAIN;
    }

    uint64_t user_data = rings->sq.next_user_data++;
    PendingIO pending = {user_data, PENDING_KIND_SUBMIT, frame_len, NowUs()};
    SPSCRing_Push(&rings->sq.pending, pending);

    io_uring_prep_send(sqe, rings->ws_conn.socket_fd, frame, frame_len, 0);
    io_uring_sqe_set_data(sqe, (void*)user_data);

    io_uring_submit(&rings->ring);  // batched syscall
    return 0;
}
```

### Completion polling at slow-path entry

```cpp
void NodeSlowPath_Cycle(NodeState<F>& node) {
    // Poll completions at cycle entry (cheap; ~1μs if any ready)
    IOUring_PollCompletions(&node.io_rings);

    // ... rest of slow-path ...
}

void IOUring_PollCompletions(NodeIORings* rings) {
    struct io_uring_cqe* cqe;
    while (io_uring_peek_cqe(&rings->ring, &cqe) == 0) {
        uint64_t user_data = (uint64_t)io_uring_cqe_get_data(cqe);
        int32_t result = cqe->res;

        PendingIO pending;
        if (SPSCRing_PopBy(&rings->sq.pending, user_data, &pending)) {
            switch (pending.kind) {
                case PENDING_KIND_SUBMIT:
                    HandleSubmitCompletion(rings, pending, result);
                    break;
                case PENDING_KIND_RECV:
                    HandleRecvCompletion(rings, pending, result);
                    break;
            }
        }

        io_uring_cqe_seen(&rings->ring, cqe);
        rings->cq.completions_processed.fetch_add(1, std::memory_order_relaxed);
    }
}
```

### Kernel version requirements

- Minimum: Linux 5.6 (io_uring rings; basic ops)
- Recommended: Linux 6.0+ (advanced features; multishot recv; etc.)

Boot-time check refuses to start if kernel too old:

```cpp
int VerifyKernelSupport() {
    struct utsname uts;
    uname(&uts);
    int major, minor;
    sscanf(uts.release, "%d.%d", &major, &minor);

    if (major < 5 || (major == 5 && minor < 6)) {
        FATAL("io_uring requires Linux 5.6+; detected %s", uts.release);
    }
    return 0;
}
```

## Stage progression criteria

- **Stage 3 first canonical** (`.E.4`): per-node io_uring + kTLS
- **Stage 4 cohort** (when 2nd application: e.g., DPDK at `.E.8` deferred): pattern proven (or pattern superseded by DPDK in deployment)
- **Stage 5 CLAUDE.md** (3rd application): promoted

## Anti-patterns avoided

- **Userspace syscall-per-I/O** — context switch overhead
- **Shared adapter worker thread** — synchronization overhead; SPOF for cluster
- **io_uring without NUMA awareness** — cross-NUMA cache lines on multi-socket

## Cross-references

- Sister: `concurrency-patterns/ktls-kernel-tls-pattern.md`
- Sister: `framework-patterns/per-node-io-rings-pattern.md`
- Parent: `concurrency-patterns/persistent-ws-connection-management-pattern.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.4-io-uring-ktls.md`
