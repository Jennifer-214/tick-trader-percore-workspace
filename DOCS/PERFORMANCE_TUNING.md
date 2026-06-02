# Performance Tuning

**Audience:** Operator tuning engine for production HFT-class latency.

For deployment: `DOCS/DEPLOYMENT_GUIDE.md`. For architecture: `DOCS/ARCHITECTURE_OVERVIEW.md`. For glossary: `DOCS/GLOSSARY.md`.

---

## Baseline expectations

**On commodity x86_64 hardware:**

| Metric | dev mode (laptop) | production mode (server) | with DPDK (future; deferred) |
|---|---|---|---|
| Hot path p99 | ~500ns-2μs | ~200-500ns | ~50-100ns |
| Slow path p99 | ~50-200μs | ~10-50μs | ~10-50μs |
| Tick-to-wire (USA → Binance) | ~50ms | ~50ms | ~3-5ms colocated |
| Tick-to-wire (colocated) | N/A | ~1-2ms | ~10-50μs |

**Network dominates.** Architecture tuning gives μs-class wins; colocation gives ms-class wins.

---

## Kernel tuning (production)

### isolcpus + nohz_full

Edit `/etc/default/grub`:
```
GRUB_CMDLINE_LINUX_DEFAULT="isolcpus=4-23 nohz_full=4-23 rcu_nocbs=4-23 transparent_hugepage=always"
```

Apply:
```bash
sudo update-grub
sudo reboot
```

Verify:
```bash
cat /sys/devices/system/cpu/isolated   # should show "4-23"
cat /sys/devices/system/cpu/nohz_full
```

Engine threads pinned to isolated CPUs avoid scheduler interference + timer ticks.

### Hugepages

```bash
# Enable transparent hugepages (auto)
echo always | sudo tee /sys/kernel/mm/transparent_hugepage/enabled

# Or explicit hugepages (more predictable)
sudo sysctl vm.nr_hugepages=4096
```

Engine `mmap`'d state region benefits from hugepages (TLB pressure reduced; ~50-100ns per page-crossing access saved).

### CPU frequency governor

```bash
# Set to performance (max frequency always; ignore power saving)
sudo cpupower frequency-set -g performance
```

Saves ~50-200ns on CPU wake-from-low-power-state.

### Disable C-states

```bash
# Disable deep C-states (kernel boot param)
GRUB_CMDLINE_LINUX_DEFAULT="... intel_idle.max_cstate=1 processor.max_cstate=1"
```

C-state exit latency = wasted ns when CPU returns from idle.

### IRQ affinity

Move IRQs OFF trading cores:
```bash
# Move all IRQs to housekeeping cores (0-3)
for irq in $(ls /proc/irq/); do
    if [ -d "/proc/irq/$irq" ] && [ "$irq" != "0" ]; then
        echo 1-3 > /proc/irq/$irq/smp_affinity_list 2>/dev/null
    fi
done
```

Or via tuned profile.

---

## NUMA tuning (multi-socket)

If multi-socket system:

```bash
# Check NUMA topology
numactl --hardware
```

Per-cluster cfg pin NUMA node:
```
# configs/clusters/binance/cluster.cfg:
topology.numa_node = 0      # binance cluster's threads on NUMA 0

# configs/clusters/alpaca/cluster.cfg:
topology.numa_node = 1      # alpaca cluster's threads on NUMA 1
```

Per-node cfg verifies NUMA placement of hot/slow CPU pair:
```
# configs/clusters/binance/nodes/node_0/core.cfg:
topology.hot_cpu = 4        # NUMA 0
topology.slow_cpu = 5       # NUMA 0
```

NUMA-local memory: per-node io_uring rings allocated on local NUMA per `per-node-io-rings-pattern.md`.

Verify: `cat /proc/<engine-pid>/numa_maps`.

---

## CPU pinning verification

```bash
# Get engine PID
PID=$(systemctl show -p MainPID --value fox-engine.service)

# List thread affinity
for tid in /proc/$PID/task/*; do
    tid=$(basename $tid)
    echo -n "TID $tid: "
    taskset -pc $tid
done
```

Expected:
- Producer threads: pinned to per-cluster producer CPUs
- Adapter/WS threads: pinned to per-cluster adapter CPUs (or per-node io_uring at .E.4+)
- Hot threads: pinned to per-node hot CPUs
- Slow threads: pinned to per-node slow CPUs

---

## Build flags

### Production

```bash
# In build.sh:
CXXFLAGS="-O3 -march=native -mtune=native -flto -fwhole-program -funroll-loops \
          -fstack-clash-protection -D_FORTIFY_SOURCE=2 -fstack-protector-strong"
```

`-march=native` enables CPU-specific instructions (AES-NI; SHA-NI; AVX-512 if available).

### Dev / debug

```bash
CXXFLAGS="-O0 -g -DDEBUG"
```

For debugging; not performance-optimized.

### Sanitizer

```bash
./build.sh asan     # AddressSanitizer
./build.sh tsan     # ThreadSanitizer
```

Use during development; not for production.

---

## Memory budget

Per Limits.hpp:

```
MAX_NODES = 16
MAX_PORTFOLIO_SLOTS = 32
MAX_ORDERS_PER_NODE = 1024
RING_SIZE (SPSC) = 4096
```

Per-node memory: ~200KB (mostly SPSC rings + state).
Total deployment: ~16 × 200KB + cluster overheads = ~5-10MB working set.

L1d / L2 / L3 cache discipline:
- Per-node hot state should fit L1d (32-64KB per CPU core)
- Per-node slow state should fit L2 (256-1024KB)
- Aggregator state in L3 (shared across nodes; ~32MB+ typical)

---

## Latency benchmarking

Built-in latency histograms per `framework-patterns/built-in-observability-pattern.md`:

```bash
# Real-time view
fox-tui    # shows p50/p99/p99.99 per node

# Historical (Prometheus via Grafana)
# Query: rate(fox_node_latency_hot_p99_ns[5m])

# One-shot benchmark
fox-cli benchmark-latency --node binance/node_0 --duration 60s
# Output: histogram bucketed (50ns / 100ns / 200ns / 500ns / 1μs / 2μs / 5μs / 10μs / 50μs / Inf)
```

Target:
- Hot path p99 ≤ 500ns
- Hot path p99.99 ≤ 2μs

If exceeded: check isolcpus / nohz_full / CPU pinning / NUMA placement / kernel C-state config.

---

## Network tuning

### TCP

```bash
# Enable TCP no-delay (default in engine via setsockopt)
echo 1 > /proc/sys/net/ipv4/tcp_nodelay

# TCP fast open (faster reconnect)
echo 3 > /proc/sys/net/ipv4/tcp_fastopen

# Receive buffer size
echo 16777216 > /proc/sys/net/core/rmem_max
echo 16777216 > /proc/sys/net/core/wmem_max
```

### TLS

Per `framework-patterns/tls-session-resumption-pattern.md`:
- TLS 1.3 (required)
- Session tickets enabled (default in OpenSSL)
- Cached SSL_SESSION reused on reconnect

### io_uring + kTLS (`.E.4` ship)

Per `concurrency-patterns/io-uring-kernel-bypass-pattern.md`:
- Linux 5.6+ required
- kTLS module loaded: `modprobe tls`
- Per-node ring depth = 256 (cfg-tunable)

### DPDK (`.E.8` deferred)

Per `concurrency-patterns/dpdk-userspace-networking-pattern.md`:
- Requires DPDK-compatible NIC
- Hugepages required
- Per-NUMA poll-mode driver

---

## Colocation (long-term)

Network RTT to Binance:
- Home internet: ~30-100ms
- AWS Tokyo (Binance Asia matching): ~1-2ms
- Colocated datacenter: <1ms

Run engine in cloud region near exchange. For Binance Asia: AWS Tokyo (ap-northeast-1). For Alpaca: AWS US East. Operator choice based on which exchanges matter most.

Engine doesn't care about location; operator deploys where useful.

---

## Common bottlenecks + fixes

### Hot path p99 > 2μs

**Causes:** CPU not isolated; timer interrupts; NUMA misconfiguration; thermal throttling.
**Fix:** Verify isolcpus + nohz_full + NUMA + CPU governor.

### Slow path p99 > 200μs

**Causes:** Slow-path doing too much work; rebuild logic expensive.
**Fix:** Audit slow path cycle body; defer expensive work to off-cadence.

### Submit roundtrip > 100ms

**Causes:** REST handshake per submit; bad network; rate-limit hits.
**Fix:** Migrate to WS-API (`.E.3`); check rate budget usage; verify network path.

### Memory growth over time

**Causes:** Leak (rare; ASAN catches at dev); audit log retention unbounded.
**Fix:** Verify `audit_retention_days` cfg; check Prometheus `fox_engine_resident_memory_bytes` trend.

---

**End of PERFORMANCE_TUNING.md v1.0** (2026-05-28).
