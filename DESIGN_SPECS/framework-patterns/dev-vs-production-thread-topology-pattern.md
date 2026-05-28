---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.1
canonical_applications:
  - v5.15.5.F.4d.1.E.1 (topology.mode cfg flag; dev vs production)
sister_specs:
  - framework-patterns/runtime-mutable-vs-boot-time-config-pattern.md (sister; cfg layer)
  - data-disciplines/cache-line-discipline.md (production thread topology depends on cache discipline)
  - meta-disciplines/configurable-deployment-mode-pattern.md (future sister; broader pattern)
tags: [framework-discipline, thread-topology, dev-mode, production-mode, isolcpus, numa]
surface: [boot-sequence, thread-pinning, deployment]
applies_at_skills: [/precoding-audit-gate, /dod-audit, /readiness]
---

# Dev vs production thread topology pattern

**Pattern intent:** Same engine binary supports two thread topology modes via cfg flag: `dev` (OS-scheduled; laptop-friendly) and `production` (strict isolcpus + nohz_full + per-thread CPU pinning + NUMA-aware). Operator picks mode at deployment.

## Problem statement

Engine architecture requires substantial thread topology for HFT-class operation:
- isolcpus kernel parameter (dedicated CPU cores; no scheduler interference)
- nohz_full (no timer tick on trading cores)
- Per-thread pthread_setaffinity_np pinning
- NUMA-aware memory placement

For PRODUCTION (server with 24-32+ CPU cores + multi-socket NUMA): all required.

For DEV (laptop with 8-16 CPU cores; single NUMA; OS multitasking): impractical. Must fall back to OS scheduler.

Without dual-mode: dev impossible on laptop OR production loses HFT-class isolation.

With dual-mode: same engine binary; cfg flag toggles; functional correctness preserved across modes.

## Pattern description

### Cfg flag

```cpp
// In engine.cfg:
[topology]
mode = dev          # or "production"

# PRODUCTION-only fields (ignored in dev mode):
producer_cpu = 0
adapter_cpu = 1
userdata_cpu = 2
aggregator_cpu = 3
isolcpus_required = 1     # refuse start if isolcpus kernel param not configured
nohz_full_required = 1
numa_aware = 1

# Per-cluster pinning
[clusters.binance.topology]
hot_cpu_per_node = [4, 6, 8, 10]   # node_0 hot on CPU 4; node_1 hot on CPU 6; etc.
slow_cpu_per_node = [5, 7, 9, 11]  # node_0 slow on CPU 5; etc.
numa_node = 0
```

### Mode-aware thread spawn

```cpp
void ThreadTopology_Apply(const ThreadTopologyConfig& cfg, ...) {
    if (cfg.mode == TOPOLOGY_MODE_DEV) {
        // OS-scheduled; no explicit pinning
        // Spawn threads via pthread_create with default attrs
        SpawnThread_OSScheduled(...);
    } else {
        // PRODUCTION: explicit CPU pinning
        if (cfg.isolcpus_required && !KernelIsolcpusEnabled()) {
            FATAL("Production mode requires isolcpus kernel parameter");
        }
        if (cfg.nohz_full_required && !KernelNohzFullEnabled()) {
            FATAL("Production mode requires nohz_full kernel parameter");
        }

        // Per-thread pinning
        pthread_attr_t attr;
        pthread_attr_init(&attr);
        cpu_set_t cpuset;
        CPU_ZERO(&cpuset);
        CPU_SET(cfg.producer_cpu, &cpuset);
        pthread_attr_setaffinity_np(&attr, sizeof(cpuset), &cpuset);

        pthread_create(&producer_thread, &attr, ProducerThread_Run, ...);
        // ... etc for all threads
    }
}
```

### Per-mode tradeoffs

| Axis | Dev mode | Production mode |
|---|---|---|
| Min CPU cores | 4 | 24+ |
| isolcpus required | No | Yes |
| nohz_full required | No | Yes |
| Per-thread pinning | No (OS-scheduled) | Yes (pthread_setaffinity_np) |
| NUMA-aware memory | No | Yes |
| Latency p99 | Best-effort (10-100μs variance) | Bounded (μs-class) |
| Functional correctness | Same as production | Same |
| Tests pass | Same as production | Same |
| Benchmark validity | Unreliable | Reliable |

### Boot-time validation

```cpp
void Engine_BootValidateTopology(EngineState<F>& state) {
    if (state.cfg.topology.mode == TOPOLOGY_MODE_PRODUCTION) {
        // Verify kernel features
        if (state.cfg.topology.isolcpus_required && !KernelIsolcpusEnabled()) {
            FATAL("isolcpus kernel param not configured; required for production mode");
        }

        // Verify CPU count
        uint32_t required_cpus = 1 +  // kernel/system
                                 1 +  // aggregator
                                 (3 * state.cluster_count) +    // per-cluster producer + adapter + userdata
                                 (2 * state.node_count);        // per-node hot + slow
        if (sysconf(_SC_NPROCESSORS_ONLN) < required_cpus) {
            FATAL("Production mode requires %u CPU cores; available %ld",
                  required_cpus, sysconf(_SC_NPROCESSORS_ONLN));
        }

        // Verify NUMA topology (if numa_aware)
        if (state.cfg.topology.numa_aware) {
            if (numa_available() < 0) {
                FATAL("NUMA support required but not available");
            }
        }
    }
    // Dev mode: no verification (works on any hardware)
}
```

## Deployment workflow

```bash
# Laptop dev (default)
$EDITOR configs/engine.cfg     # set topology.mode = dev
./build.sh test               # build
./fox-engine --config configs/  # run; threads OS-scheduled

# Production server
$EDITOR configs/engine.cfg     # set topology.mode = production
# Configure kernel: isolcpus=4-23 nohz_full=4-23 (boot param)
sudo systemctl enable fox-engine.service
sudo systemctl start fox-engine.service
# Engine validates kernel features at boot; refuses if missing
```

## Stage progression criteria

- **Stage 3 first canonical** (`.E.1`): dev + production modes implemented
- **Stage 4 cohort** (when 2nd similar dual-mode pattern surfaces): pattern proven
- **Stage 5 CLAUDE.md** (3rd application + discipline matures): promoted

## Anti-patterns avoided

- **Single-mode engine** (production-only): no dev option on laptop; substantial friction
- **Mode-specific code branches throughout** (instead of cfg-flag + boot-time selection)
- **Silent mode degradation** (production cfg on laptop just falls back without warning) → refuses to start with clear error

## Cross-references

- Sister: `framework-patterns/runtime-mutable-vs-boot-time-config-pattern.md`
- Sister: `data-disciplines/cache-line-discipline.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md`
- Operator deployment guide: `DOCS/DEPLOYMENT_GUIDE.md` (lands at `.E.2`)
