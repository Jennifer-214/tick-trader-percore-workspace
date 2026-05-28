---
type: framework-pattern
stage: 2-draft
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.8 (DEFERRED)
sister_specs:
  - concurrency-patterns/dpdk-userspace-networking-pattern.md
  - concurrency-patterns/io-uring-kernel-bypass-pattern.md
tags: [framework-discipline, networking-stack, cfg-driven, deployment-mode]
surface: [networking-init, boot-sequence]
---

# Kernel vs userspace networking cfg pattern (Stage 2 DRAFT)

**Pattern intent:** Cfg-driven networking stack selection. Same engine binary supports kernel I/O (io_uring + kTLS) AND userspace I/O (DPDK + userspace-TLS). Operator picks via cfg.

## Pattern

```cpp
enum NetworkingStack {
    NETWORKING_KERNEL,    // io_uring + kTLS (from .E.4); WORKS without special hardware
    NETWORKING_DPDK,      // DPDK userspace stack (.E.8 deferred; requires DPDK-compatible NIC)
    NETWORKING_ONLOAD,    // Solarflare Onload (transparent; requires Solarflare hardware)
};

// configs/engine.cfg:
// networking.userspace_stack = kernel
// OR
// networking.userspace_stack = dpdk
// OR
// networking.userspace_stack = onload

void Engine_InitNetworking(NetworkingStack stack) {
    switch (stack) {
        case NETWORKING_KERNEL:
            EngineInit_KernelIO();   // .E.4 io_uring + kTLS path
            break;
        case NETWORKING_DPDK:
            DPDK_Init();             // .E.8 deferred; requires hardware
            break;
        case NETWORKING_ONLOAD:
            // Onload is transparent (LD_PRELOAD); standard sockets work
            break;
    }
}
```

## Boot-time validation

```cpp
int VerifyNetworkingStack(NetworkingStack stack) {
    switch (stack) {
        case NETWORKING_KERNEL:
            return VerifyKernelIOSupport();   // Linux 5.6+; kTLS module
        case NETWORKING_DPDK:
            return VerifyDPDKHardware();      // refuses if no DPDK-compat NIC
        case NETWORKING_ONLOAD:
            return VerifyOnloadAvailable();   // checks for Solarflare hardware
    }
}
```

Engine refuses to start on incompatible stack + clear error message.

## Stage progression

- **Stage 2 DRAFT**: reference; awaits hardware deployment
- **Stage 3 first canonical**: when DPDK or Onload actually deployed

## Cross-references

- Sister: `concurrency-patterns/dpdk-userspace-networking-pattern.md`
- Sister: `concurrency-patterns/io-uring-kernel-bypass-pattern.md`
