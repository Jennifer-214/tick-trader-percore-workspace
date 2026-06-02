# Architecture Overview

**Audience:** New contributors + future-Caramel. High-level mental model for the engine architecture.

For deep-dive: see specific DESIGN_SPECS at `tick-trader-percore-workspace/DESIGN_SPECS/`. For implementation detail: see plan bodies at `tick-trader-percore-workspace/plans/`.

---

## The big picture

```
DEPLOYMENT (engine instance running on one server)
├── Cluster: binance (one per exchange)
│   ├── Producer thread (1 CPU core)
│   │     Reads Binance trade WS; fans out ticks to nodes
│   ├── Adapter worker thread (1 CPU core)  [.E.4: replaced by per-node io_uring]
│   │     Submits orders to Binance via REST or /ws-api/v3
│   ├── User-data WS thread (1 CPU core)
│   │     Reads fills; routes to per-node fill rings
│   ├── Node: binance/node_0
│   │   ├── Hot thread (1 CPU core; branchless H7 dispatch)
│   │   │     Per-tick strategy evaluation
│   │   └── Slow thread (1 CPU core; rebuild + submit)
│   │         Per-node trading state ownership
│   ├── Node: binance/node_1 → sub-account 1
│   ├── Node: binance/node_2 → sub-account 2
│   └── Node: binance/node_3 → sub-account 3
├── Cluster: alpaca  (future)
├── Cluster: ibkr    (future; deferred)
├── Aggregator (1 CPU core; deployment-wide)
│       Reads all node state via seqlock
│       Computes global + per-cluster totals
│       Sets hierarchical kill flags
└── Kernel/system (1 CPU core; NOT isolcpus)
```

**Total CPU cores for 2-cluster × 4-node deployment: 24 (production mode).**

---

## Trading flow

```
[Market Data]
    ↓ (Binance trade WS)
Per-cluster producer thread
    ↓ (fan-out to per-node hot rings; SPSC)
Per-node hot thread
    ↓ (branchless H7 strategy evaluation; <500ns p99)
    ↓ (emit TradeEvent to per-node slow ring; SPSC)
Per-node slow thread
    ↓ (rebuild strategy state)
    ↓ (build SubmitCommand)
    ↓ (rate-limit check; capital allocation check)
    ↓ (call tt::submit_order<BinanceAdapter>)
[Per-cluster adapter worker (or per-node io_uring at .E.4)]
    ↓ (HMAC sign + send via WS-API or REST)
[Binance matching engine]
    ↓ (fill / partial / reject)
[User-data WS]
    ↓ (executionReport event)
Per-cluster user-data thread
    ↓ (parse fill; route to per-node fill ring; SPSC)
Per-node slow thread
    ↓ (process fill; update account state)
    ↓ (atomic update to aggregator's running totals; event-sourced per D-54)
[Aggregator]
    ↓ (check kill thresholds)
    ↓ (mirror kill flags to per-node via atomic if breached)
```

---

## Key design principles

### 1. Per-node sharding (architectural)

Each node is a self-contained trading unit:
- Own sub-account (real Binance sub-account; per-node failure isolation)
- Own hot + slow CPU cores
- Own strategy + symbol + capital + mode
- Own state (positions; balance; P&L)

Aggregator is read-only observer.

### 2. Single-writer principle

Per-node OWNS WRITE of own state; aggregator READS via seqlock.
Aggregator OWNS WRITE of global + cluster totals + kill flags; per-nodes READ via atomic mirrors.

No multi-writer contention; lock-free everywhere; correctness by design.

### 3. Cluster-level isolation

Per-exchange shared resources (producer + adapter + WS thread) live in cluster scope. One cluster's WS drop doesn't affect siblings.

### 4. Hot/slow path decoupling

Each node uses 2 CPU cores:
- Hot path: branchless H7 dispatch; <500ns p99 latency budget
- Slow path: branchy logic OK; rebuild + submit + bookkeeping

Decoupled via SPSC ring. Never collapse.

### 5. FOREACH_* meta-registries

Pattern proliferation via X-macro registries:
- FOREACH_EXCHANGE (each row = one exchange)
- FOREACH_SUBACCOUNT_<EXCHANGE> (per-exchange sub-account topology)
- FOREACH_PER_NODE_CFG_FIELD (cfg field schema)
- FOREACH_FEATURE_<EXCHANGE> (per-exchange ML features)

Adding new exchange/sub-account/cfg-field/feature = 1 row + auto-flow.

### 6. Headless service + multi-viewer

Engine runs headless 24/7. State published via mmap'd shared memory. Viewers (fox-tui; fox-cli; Grafana via Prometheus) attach on demand. Multiple concurrent viewers OK.

### 7. Audit-driven discipline

Plans audited before coding (5-agent /precoding-audit-gate). Sub-sprint trajectories audited as a whole (.E.0 pre-coding plan audit ship). Recurring bug patterns codified (Class N catalog). Structural-fix-preferred over symptom patches.

---

## File layout

```
FoxML_Trader_v2/
├── CLAUDE.md                # Architectural orientation
├── CoreFrameworks/          # Engine core (per-node state; aggregator; etc.)
├── Strategies/              # Strategy implementations + adapter libraries
├── ML_Headers/              # Feature registry; model inference
├── DataStream/              # Per-exchange adapters (BinanceAdapter; future: AlpacaAdapter; etc.)
├── FixedPoint/              # FPN<F=64> fixed-point math
├── MemHeaders/              # Lock-free primitives (SPSC; seqlock; bitmap)
├── GUI/                     # Legacy ImGui (archived at .E.2)
├── Backtest/                # Backtest harness
├── tests/                   # controller_test + integration
├── DOCS/                    # Operator-facing documentation
└── plans/                   # Sprint plans (gitignored; symlinked to workspace)

tick-trader-percore-workspace/
├── plans/                   # Sprint plans (canonical; gitignored from engine)
├── DESIGN_SPECS/            # Reusable architectural patterns
├── claude-skills/           # Audit skill suite
└── DOCS/                    # Audit catalogs (RECURRING_BUG_PATTERNS; TECH_DEBT; etc.)
```

---

## Hot path budget (per H8)

- **Hot path p99: ≤500ns** (BG_Evaluate per tick)
- **Slow path p99: ≤100μs** (full rebuild cycle)
- **Submit roundtrip: ~10-50ms** (network-bound; not engine)

Hot path latency budget is HARD ceiling. Regression = ship blocker.

---

## Where to find more detail

| Question | Location |
|---|---|
| How do I add a new exchange? | `DOCS/CONTRIBUTING/add-exchange.md` |
| How do I add a new strategy? | `DOCS/CONTRIBUTING/add-strategy.md` |
| How do I deploy on a server? | `DOCS/DEPLOYMENT_GUIDE.md` |
| How do I operate the engine? | `DOCS/OPERATOR_MANUAL.md` |
| What if something breaks? | `DOCS/INCIDENT_RUNBOOK.md` |
| Strategy lifecycle? | `DOCS/STRATEGY_LIFECYCLE.md` |
| Disaster recovery? | `DOCS/DR_TESTING.md` |
| Terminology? | `DOCS/GLOSSARY.md` |
| What's archived to legacy/? | `DOCS/REPO_CLEANUP_GUIDE.md` |
| Architectural patterns? | `tick-trader-percore-workspace/DESIGN_SPECS/` |
| Recurring bug patterns? | `DOCS/RECURRING_BUG_PATTERNS.md` |
| H1-H20 invariants? | `CLAUDE.md` (always loaded) |

---

**End of ARCHITECTURE_OVERVIEW.md v1.0** (2026-05-28).
