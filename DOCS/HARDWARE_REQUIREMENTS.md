# Hardware Requirements

**Audience:** Operator planning hardware for engine deployment.

For tuning the hardware once installed: `DOCS/PERFORMANCE_TUNING.md`. For deployment workflow: `DOCS/DEPLOYMENT_GUIDE.md`.

---

## ⚠️ HARDWARE SAFETY WARNING — READ FIRST

**DO NOT run this engine on a standard laptop for live trading.** This is HFT-class infrastructure that sustains 100% CPU usage across multiple cores indefinitely. On a standard laptop, this WILL cause:

- **Thermal damage:** sustained max CPU + busy-polling pins cores at 100%. Laptop cooling is designed for bursts, not 24/7 sustained load. Result: thermal throttling at best; degraded silicon / fan failure / motherboard damage at worst.
- **Fan failure:** continuous fan operation at max RPM accelerates fan bearing wear-out. Eventual fan failure → thermal shutdown → potentially permanent CPU/GPU damage.
- **Battery degradation:** sustained AC charging while CPU at max load thermally stresses battery. Battery life and capacity degrade significantly faster than normal usage.
- **Disk wear:** audit log + state mmap writes accumulate over 24/7 operation. SSD wear-leveling will exhaust write cycles faster on consumer-grade laptop SSDs (vs server-grade).
- **Power supply stress:** sustained AC power draw at max load can stress laptop PSU; OEM-spec PSUs not designed for 24/7 max.

**Laptop use is RESTRICTED to:**
- Development (`topology.mode = dev`)
- Backtesting (`foxml-train` CLI; finite duration)
- Paper-test (FINITE DURATION; pause overnight; monitor temperatures)
- Reading documentation
- NOT live trading 24/7

**For 24/7 live operation: USE A SERVER.** Workstation / desktop / colocated cloud instance. Designed for sustained load. Has proper cooling. SSDs rated for 24/7.

If you ignore this and damage your laptop: that's on you. The engine doesn't apologize for being demanding; it's designed to be.

---

## Minimum (development laptop) — DEV ONLY; NOT 24/7

| Component | Requirement |
|---|---|
| **CPU** | 8+ cores; modern x86_64 (Skylake+) |
| **CPU features** | SHA-NI (HMAC acceleration); AVX2 (FPN math); TSC (timing) |
| **RAM** | 16GB |
| **Network** | Standard broadband |
| **Storage** | 100GB SSD (state + audit logs + models) |
| **Kernel** | Linux 5.6+ recommended (for io_uring at `.E.4`); 5.10+ for kTLS |
| **Topology** | `topology.mode = dev` (OS-scheduled threads) |

Sufficient for: 1 cluster × 2 nodes; paper-test workflow; backtest; development.

---

## Recommended (production server)

| Component | Requirement |
|---|---|
| **CPU** | 24-32 cores; Threadripper / EPYC / Xeon Gold |
| **CPU features** | SHA-NI + AVX2 + AVX-512 (preferred); TSC; AES-NI |
| **RAM** | 32GB+ (engine + audit logs + monitoring overhead) |
| **Network** | Low-latency network to exchange; gigabit+ |
| **Storage** | 500GB+ NVMe SSD (audit logs accumulate ~100MB/day; state file ~1MB) |
| **Kernel** | Linux 6.0+ (mature io_uring + kTLS support) |
| **Topology** | `topology.mode = production` (strict isolcpus + nohz_full) |

Supports: 2 clusters × 8 nodes each = ~24 CPU cores allocated.

### Topology budget (24-core server example)

```
2 clusters × 4 nodes = 8 nodes total
- 1 Producer thread per cluster × 2: 2 CPU cores
- 1 Adapter worker (or per-node io_uring at .E.4) × 2: 2 CPU cores
- 1 User-data WS thread per cluster × 2: 2 CPU cores
- 1 Hot thread per node × 8: 8 CPU cores
- 1 Slow thread per node × 8: 8 CPU cores
- 1 Aggregator: 1 CPU core
- Reserved (kernel; system; logging): 1 CPU core
TOTAL: 24 CPU cores
```

Higher node counts: scale CPU cores accordingly. N=16 nodes per cluster: ~48 CPU cores needed.

---

## Pro / colocated (HFT-class)

| Component | Requirement |
|---|---|
| **CPU** | 32+ cores; clock 4GHz+; latest gen Intel Xeon / AMD EPYC |
| **RAM** | 64GB+ ECC |
| **Network** | DPDK-compatible NIC (Mellanox ConnectX; Intel X710); 10Gb+ |
| **Network latency** | Colocated at exchange data center; <1ms RTT |
| **Storage** | NVMe SSD for state; separate disk for audit logs |
| **Topology** | `topology.mode = production` + DPDK kernel-bypass (`.E.8` deferred) |
| **NUMA** | Multi-socket OK; cluster pinned to NUMA node |

Supports: full HFT-class performance; ~3-5μs tick-to-wire (with DPDK + colocation).

### DPDK-compatible NICs (verified list)

Per `concurrency-patterns/dpdk-userspace-networking-pattern.md`:
- Mellanox ConnectX-5 / ConnectX-6 / ConnectX-7
- Intel X710 / E810
- (Full list: https://core.dpdk.org/supported/)

Not all NICs work with DPDK. Verify before purchase.

---

## NOT recommended

- **Cloud VMs without dedicated CPU** (noisy neighbor; unpredictable latency variance)
- **Low-end laptops** (<8 cores; throttling; thermal issues at sustained load)
- **Old kernels** (<5.6 for io_uring; <5.10 for full kTLS support)
- **Spinning disks** (audit log + state file I/O suffer)
- **WiFi networks** (unpredictable latency; packet loss)

---

## Storage layout

```
/var/lib/fox/                       (recommend separate volume for audit + state)
├── state/
│   └── state.mmap                  # ~1-10 MB; mmap'd; kernel-flushed
└── audit/
    ├── trades.jsonl                # ~50-200 MB per active month
    ├── state-changes.jsonl
    ├── commands.jsonl
    ├── errors.jsonl
    └── metrics-checkpoint.jsonl

/etc/fox/
├── configs/                        # ~10-100 KB
└── secrets.env                     # API keys (chmod 600)

/opt/fox/                           (optional; built binaries)
├── bin/
│   ├── fox-engine
│   ├── fox-tui
│   ├── fox-cli
│   └── foxml-train
└── lib/strategies/
    ├── libstrategy_momentum.so
    └── ... (per-strategy .so for .E.X hot-reload)
```

90-day audit log retention (cfg-driven): ~150GB total for active engine.
Models + training data: depends on operator (~10-100GB).

---

## Cloud deployment specs

### AWS (Binance Asia colocation)

- **Instance type:** c6i.8xlarge (32 vCPU; 64GB RAM) for production
- **Region:** ap-northeast-1 (Tokyo; near Binance Asia)
- **EBS:** 500GB io2 (or instance store for performance)
- **Network:** Enhanced networking enabled; placement group

### AWS (Alpaca US colocation)

- **Region:** us-east-1 (N. Virginia; near Alpaca)
- **Same instance specs**

### GCP / Azure

Equivalent: similar CPU count + memory; cloud-region near exchange.

---

## Cost estimates (operator-side)

For one production server:
- **Self-hosted:** $5K-15K hardware investment (one-time)
- **AWS EC2:** ~$1000-2000/month (c6i.8xlarge + storage + network)
- **GCP / Azure:** similar to AWS

For dev:
- **Laptop:** any modern 8+ core (existing hardware OK)

---

**End of HARDWARE_REQUIREMENTS.md v1.0** (2026-05-28).
