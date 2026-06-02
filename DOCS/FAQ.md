# FAQ

**Audience:** Operator + contributor with common questions.

For terminology: `DOCS/GLOSSARY.md`. For architecture: `DOCS/ARCHITECTURE_OVERVIEW.md`. For deployment: `DOCS/DEPLOYMENT_GUIDE.md`.

---

## General

### What is the engine?

HFT-class trading engine for retail-accessible exchanges (Binance; Alpaca; IBKR future). Open-source AGPL. Built for one operator (Caramel) but theoretically usable by anyone with the engineering chops to run it.

### Is it for me?

YES if you:
- Are comfortable with Linux + SSH + systemd
- Understand HFT concepts (latency budgets; branchless dispatch; lock-free)
- Want to operate a trading engine yourself (not a managed service)
- Have engineering background OR willingness to learn from documentation
- Want open-source (AGPL) over commercial alternatives
- Have appropriate hardware (server / desktop; NOT a laptop for 24/7)

NO if you:
- Want a click-and-deposit experience
- Need someone else to manage trading for you
- Aren't comfortable with text-based configs + CLI
- Want a GUI-first dashboard with hand-holding
- Only have a laptop and want to run live 24/7 (the engine WILL damage your laptop)

### What does "HFT-class" mean here?

- Branchless hot path (sub-microsecond decision latency)
- Lock-free SPSC + seqlock primitives
- Fixed-point math (FPN<F=64>; not float)
- Per-node CPU pinning + NUMA-aware
- io_uring kernel-bypass I/O
- Persistent WS-API connections (saves handshake per submit)
- Sub-microsecond tick-to-decision; ~3-5μs tick-to-wire with DPDK

Not all retail engines have this. We have it.

---

## Architecture

### Why per-node sub-accounts?

Per `framework-patterns/per-node-economic-isolation-pattern.md`: economic isolation enforced by Binance, not engine. Each per-node loss bounded to its sub-account; siblings unaffected. N × rate-limit budget. Per-sub-account API key compromise = bounded blast radius.

### Why headless engine?

Multi-cluster + sub-accounts + 24/7 operation = high-stakes funds at trade. GUI thread crash should NOT take down trading. Operator wants attach/detach viewer from laptop without engine restart. Per D-4 + `meta-disciplines/headless-engine-viewer-split-pattern.md`.

### Why Core → Node rename?

"Core" was ambiguous (CPU core vs trading core). "Node" is unambiguous trading unit. Per D-27. Each node uses 2 CPU cores (hot + slow path decoupled per H7).

### Why FOREACH_EXCHANGE?

Multi-exchange substrate. Adding a new exchange = 1 row + 1 adapter library. No framework code touched. Per `framework-patterns/foreach-exchange-meta-registry-pattern.md`.

### Why no DPDK?

Per D-57: operator lacks DPDK-compatible hardware. io_uring + kTLS at `.E.4` gives substantial latency improvement on commodity hardware without specialized NIC. DPDK deferred; lands if operator acquires hardware.

### Why io_uring instead of just kernel sockets?

io_uring eliminates syscall-per-I/O overhead (~5μs context switch); batched submission; kernel-side encryption via kTLS. ~10-20μs saved per I/O. Modern Linux kernel feature; no special hardware required.

---

## Operations

### Can I run on a laptop?

YES for development / backtest / paper-test (finite duration). NO for 24/7 live trading.

**Why not 24/7 on laptop:** This engine sustains 100% CPU + busy-polling across multiple cores indefinitely. Standard laptops are NOT designed for this. Sustained operation WILL cause:
- Thermal damage (cooling designed for bursts, not 24/7)
- Fan wear-out / failure
- Battery degradation
- SSD wear (audit logs + state writes)
- PSU stress

**Use a server for live 24/7:** desktop / workstation / colocated cloud instance. Designed for sustained load.

In dev mode (`topology.mode = dev`), threads are OS-scheduled (no strict isolcpus); functional correctness preserved; latency benchmarks unreliable. Good for development + testing + finite paper-test. **Just don't leave it running 24/7 on a laptop.**

See `DOCS/HARDWARE_REQUIREMENTS.md` § "Hardware Safety Warning" for the full warning.

### Can I run with one Binance account (no sub-accounts)?

YES, via virtual partition mode. `clusters/binance/cluster.cfg: subaccount_mode = virtual`. Engine partitions single account into N slots; tracks per-slot accounting internally. Less isolation than real sub-accounts but operationally simpler.

### What happens if engine crashes?

1. systemd auto-restarts within 5s
2. Engine reads mmap state file from disk
3. Parallel reconcile per sub-account against exchange truth
4. Engine resumes per `on_crash_restart_action` policy:
   - `resume` (default): continue trading
   - `cancel-all`: cancel open orders; preserve positions
   - `flatten`: force-close all positions

Per `framework-patterns/crash-recovery-via-mmap-state-pattern.md`.

### What happens if Binance API goes down?

1. WS keepalive detects (~30s pong timeout)
2. Reconnect with exponential backoff (1s, 2s, 4s, ... cap 60s)
3. TLS session resumption skips handshake on reconnect
4. If outage > cluster threshold (default 10min): cluster halts; operator alert
5. After exchange recovery + automatic reconnect: trading resumes

Per `concurrency-patterns/persistent-ws-connection-management-pattern.md`.

### Can I monitor remotely?

YES. Three ways:

1. **SSH-tunneled fox-tui:** Native TUI via mmap shared memory; sub-ms updates
2. **Grafana via Prometheus:** Historical metrics + alerts; browser-based
3. **fox-cli scripts:** Operator can query state via CLI from any shell

### Can I operate multiple operators?

YES (sort of). UDS control channel is filesystem-permission-based. Multiple operators with shell access to engine user can all attach fox-tui + send fox-cli commands. Audit log records every command + originating session. For external operators: gate via SSH + sudo.

### How do I add a new exchange?

Per `DOCS/CONTRIBUTING/add-exchange.md`: 1 row in FOREACH_EXCHANGE registry + 1 adapter library implementing `tt::*` contract + cfg files. Framework auto-flows the rest.

### How do I hot-reload a strategy?

Per `framework-patterns/strategy-hot-reload-via-dlopen-pattern.md` (at `.E.X`):

1. Edit strategy code in `Strategies/<name>.hpp`
2. Rebuild: `./build.sh strategies`
3. Hot-swap: `fox-cli model-swap binance/node_0 --to build/libstrategy_<name>.so`
4. Engine atomically swaps function pointer at next slow-path cycle
5. Rollback available: `fox-cli rollback-strategy binance/node_0`

---

## Performance

### What's my expected latency?

Per `DOCS/PERFORMANCE_TUNING.md`:

| Path | Production mode + io_uring + kTLS | With DPDK colocated (future) |
|---|---|---|
| Hot path p99 | ~200-500ns | ~50-100ns |
| Submit roundtrip | ~50ms (network-bound) | ~1-2ms |
| Tick-to-wire | ~10-20μs | ~3-5μs |

Network RTT dominates. Architecture tuning matters for p99 variance + correctness; colocation matters for raw mean latency.

### Can I run this profitably?

That depends on:
- Your strategies' alpha (engine doesn't generate edge; you do)
- Risk management discipline (capital allocation; kill switches)
- Market conditions (no strategy works in all regimes)

Engine provides the INFRASTRUCTURE; strategy + operator decisions provide the EDGE.

---

## Development

### How do I contribute?

See `DOCS/CONTRIBUTING/`:
- `add-exchange.md`
- `add-strategy.md`
- `add-feature.md`
- `add-cfg-field.md`
- `add-design-spec.md`
- `build-system.md`
- `testing-strategy.md`
- `audit-workflow.md`

PRs welcome but be aware: discipline bar is high (H1-H20 invariants; audit-driven workflow; structural-fix-preferred; etc.).

### Can I fork the engine for my own use?

YES, AGPL. Modifications must remain AGPL. Network use of modified code triggers AGPL disclosure (AGPL is the network-share-alike GPL).

### Why such substantial planning discipline?

Per `feedback_motivated_collaborator_for_caramel`: 5-10y codebase lifetime quality bar. Public AGPL + hedge-fund visibility = exacting standards. Bugs cost real money. Planning discipline catches issues at $0 (planning time) vs $$$ (production runtime).

---

## Common confusions

### "Why is mode for-node-only? Why not engine-level?"

Power-user use case: paper-test new strategy variant ALONGSIDE live nodes. Need per-node granularity for direct head-to-head comparison. Per `framework-patterns/per-node-paper-mode-flag-pattern.md`.

### "How is per-cluster different from per-node?"

- **Cluster** = one exchange (Binance; Alpaca). Owns shared resources (producer + adapter + WS thread).
- **Node** = one sub-account within cluster. Owns trading state + hot + slow CPU threads.

One cluster contains many nodes. One deployment contains many clusters.

### "Is paper mode same as backtest?"

NO. Paper mode = REAL market data + simulated fills. Backtest = synthetic / historical data + simulated fills. Paper mode catches real-time latency variance + market microstructure; backtest catches strategy logic on regime-diverse data.

### "Does the engine make trading decisions?"

NO. Engine provides the INFRASTRUCTURE for strategies to make trading decisions. Strategies are code you write (or use existing ones). Engine handles: submit; fill; reconcile; risk enforcement; observability; etc.

### "What's the difference between `feedback_*` rules and DESIGN_SPECS?"

- `feedback_*` memories = operator-collaboration rules (how to engage with operator); auto-loaded
- DESIGN_SPECS = architectural patterns + disciplines (how the engine works); load-on-demand
- Class catalog (RECURRING_BUG_PATTERNS) = anti-patterns to avoid
- H1-H20 (CLAUDE.md) = always-loaded hard invariants

Each layer has its home; no duplication.

---

**End of FAQ.md v1.0** (2026-05-28).
