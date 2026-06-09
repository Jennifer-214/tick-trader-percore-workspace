# Glossary

**Audience:** Operators + contributors. New to the codebase? Read this first.

Terminology used throughout the engine. Disambiguates concepts that have similar names but different meaning.

---

## Architecture terminology

### Deployment

A single running instance of the engine on one server. Has one global aggregator + producer + multiple clusters.

### Cluster

A per-exchange shared resource pool. Each cluster = one exchange (Binance; Alpaca; IBKR; etc.). Owns:
- Per-cluster producer thread (reads exchange's market data WS)
- Per-cluster adapter worker thread (submit path)
- Per-cluster user-data WS thread (fills routing)
- Per-cluster sub-account pool (if exchange supports sub-accounts)
- Per-cluster rate-limit budget
- Per-cluster kill switch

### Node

A per-sub-account trading unit. Each node:
- Binds to ONE sub-account (or virtual partition for non-sub-account exchanges)
- Has its OWN hot thread (CPU core; branchless H7 dispatch)
- Has its OWN slow thread (CPU core; rebuild + submit + bookkeeping)
- Trades one symbol with one strategy

Each node uses 2 CPU cores (hot + slow path decoupled).

### CPU core vs node

- **CPU core** = physical CPU hardware thread (counted in /proc/cpuinfo)
- **Node** = trading unit (uses 2 CPU cores; bound to one sub-account)

Disambiguate explicitly: "CPU core" when discussing hardware; "node" when discussing trading.

### Hot path

Per-tick branchless dispatch on per-node hot thread. Latency budget: ≤500ns p99 (H8 strict).

### Slow path

Per-node slow thread; runs at cadence (default 100ms cycle). Rebuilds strategy state; pops fills from ring; submits orders; bookkeeping.

### Producer

Per-cluster thread reading exchange market data WS; parses ticks; fans-out to cluster's node hot rings.

### Aggregator

Single deployment-wide thread reading all node state via seqlock. Computes per-cluster + global totals. Sets hierarchical kill flags. Read-only (single-writer principle).

---

## Trading concepts

### Sub-account

Independent trading account on exchange (Binance supports; Alpaca doesn't; IBKR via FA structure). Each sub-account has:
- Own API key + secret
- Own balance
- Own rate-limit budget
- Own user-data WS

Per-node binds to one sub-account → economic isolation.

### Virtual partition (mode)

When exchange doesn't support sub-accounts, engine partitions single account into N virtual slots. Each per-node tracks its virtual balance. Aggregate = sum of virtual slots.

### Mode (per-node)

4-state enum:
- `backtest` — synthetic data; simulated fills
- `paper` — real market data; simulated fills
- `live` — real submission; real fills
- `shadow` — real submission; results ignored (future colo testing)

### Hierarchical kill switch

3 layers:
- **Per-node** — halt specific node
- **Per-cluster** — halt all nodes in cluster
- **Global** — existential halt

Per-node mirrors global + cluster + own kill flags via atomic at slow-path entry.

### Client order ID

Unique identifier per submitted order. Format: `C<cluster><sub><node>_<seq>` (e.g., `C0_S2_N5_12345`). Encoded so engine routes fills back to originating node.

### Reconcile

Engine queries exchange for actual positions + balances; compares to engine-side mirror; logs discrepancy; trusts exchange truth. Runs at boot (parallel per-sub-account) + every 5min (cfg-driven) + per-fill (cfg-driven).

---

## Configuration concepts

### Hierarchical config

Filesystem layout: `configs/engine.cfg + clusters/<name>/{cluster.cfg, credentials/, nodes/node_<id>/*.cfg}`. Each per-node has dedicated folder. No template inheritance (each per-node self-contained).

### Boot-time vs runtime mutable

- **Boot-time** fields: change requires engine restart (exchange endpoints; credentials; CPU pinning; etc.)
- **Runtime mutable** fields: change applies via SIGUSR1 hot-reload (strategy parameters; risk thresholds; mode)
- **Boot-time-or-no-open-pos**: runtime mutable IF no open positions on that node

### FOREACH_EXCHANGE

X-macro meta-registry of all supported exchanges. Each row carries metadata (adapter type; rate budget; market hours; auth flavor; submit protocol). Adding a new exchange = 1 row + 1 adapter library.

### FOREACH_SUBACCOUNT_<EXCHANGE>

Per-exchange X-macro for sub-account topology. Each row = one sub-account configuration.

### State publish region

mmap'd shared memory region (`/var/lib/fox/state/state.mmap`) where engine writes state. Multiple viewers (fox-tui; etc.) read via seqlock-consistent lock-free reads.

---

## Binary names

### fox-engine

The trading engine. Headless service. Runs 24/7. systemd-managed in production.

### fox-tui

Native terminal UI (notcurses-based). Reads mmap state region. vi-style keybindings. Multiple concurrent attach OK.

### fox-cli

Operator control interface. Sends commands via Unix domain socket. Scriptable; idempotent; exit codes.

### foxml-train

ML training CLI tool. Config-file-driven training pipeline. Replaces foxml_suite GUI.

### (Legacy; archived to legacy/)

- `engine` — old combined engine + GUI binary
- `engine_gui` — Dear ImGui GUI (deprecated; archived)
- `foxml_suite` — old ML training GUI (deprecated; archived)

---

## Concurrency primitives

### SPSC ring

Single-producer single-consumer lock-free ring buffer. Used for must-not-miss event streams (trade events; fills; submits; audit log).

### MPSC ring

Multi-producer single-consumer. NOT used in current architecture (per `.E.4` per-node design replaces); reserved for future patterns if needed.

### Seqlock

Multi-reader lock-free consistency primitive. Writer increments counter before update (odd = in-progress); increments after (even = consistent). Readers retry if odd or counter changed. Used for slow→hot cfg parameters; aggregator state publication; mmap state publication.

### Atomic blackboard

Single-writer single-atom-of-state publication. Latest value wins. Used for kill flags; rate-limit tokens; etc.

---

## Discipline concepts (per DESIGN_SPECS)

### H1-H20

Hard invariants. ALWAYS preserved. Documented in `CLAUDE.md`. Examples: H7 (hot path branchless); H9 (wire format byte-preservation); H13 (tt:: dispatch; no reinterpret_cast); etc.

### Class N

Recurring bug pattern in `DOCS/RECURRING_BUG_PATTERNS.md`. Examples: Class 26 (global consumer reading per-node field); Class 27 (single-value cache flattens per-instance).

### Mn (meta-discipline)

Audit-methodology gaps codified in `DOCS/DESIGN_PHILOSOPHY.md` § 11.5. Examples: M5 (train-serve execution-layer parity); M7 (structural enforcement when memory insufficient).

### Stage 2 / 3 / 4 / 5 / 6 (pattern lifecycle)

Pattern codification lifecycle stages:
- **Stage 2 DRAFT** — pattern outlined; awaits first canonical
- **Stage 3 first canonical** — first concrete application; lessons captured
- **Stage 4 cohort** — proven across ≥2 applications
- **Stage 5 CLAUDE.md** — promoted to always-loaded discipline
- **Stage 6 cadence-locked** — CI enforcement

### `feedback_*`

Operator-collaboration rules in `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/`. Examples: `feedback_motivated_collaborator_for_caramel`; `feedback_audit_canonical_sister_before_new_infra`; etc.

---

## Operational concepts

### Audit log

Categorized JSONL files at `/var/lib/fox/audit/`:
- `trades.jsonl` — every fill, order, cancel
- `state-changes.jsonl` — every cfg reload, node start/stop, kill switch
- `commands.jsonl` — every fox-cli command (operator audit trail)
- `errors.jsonl` — every error condition
- `metrics-checkpoint.jsonl` — periodic snapshots

Optional SHA-256 hash chain for tamper-evidence (cfg-driven).

### Webhook alert

Engine emits HTTP POST to operator-configured URL on alert events (drawdown threshold; sub-account suspended; etc.). Operator wires webhook → Slack/Discord/email.

### Preflight check

Boot-time validation: connectivity to each exchange; API permissions (refuse `enableWithdrawals`); rate-limit headroom; sub-account binding valid; symbol valid; hardware features (SHA-NI; AVX2; TSC). Refuses to start trading on any failure.

### Topology mode

`topology.mode = dev | production` cfg field. Dev = OS-scheduled threads (laptop); production = strict isolcpus + nohz_full + per-thread pinning + NUMA-aware (server).

---

**End of GLOSSARY.md v1.0** (2026-05-28).
Updated as new concepts surface.

---

## Numeric core types (added at A.5, `v5.15.5.F.4d.1.E.0.8`, 2026-06-09)

### FPN_Binary<64>

The engine's binary fixed-point core: **16 bytes**, two's-complement `__int128`, value = `v / 2^64` (sign in the top bit; 4 per cache line). Used for FEATURE/SIGNAL math (and, until Ship B lands decimal money, accounting per H4's current form). **Spelling bridge:** named bare `FPN` before A.5 — in pre-A.5 docs, commits, and history, `FPN` ≈ today's `FPN_Binary`. It was 24B sign-magnitude (`w[2]`+sign+pad) before Ship A (`v5.15.5.F.4d.1.E.0.7`) flipped the representation.

### FPN_* function family

`FPN_Mul`, `FPN_AddSat`, `FPN_ToDouble`, `FPN_BlendOnMask`, … — the op surface over the binary core. **Deliberately NOT renamed at A.5** (the family's final shape is decided at Ship B when decimal ops land). A doc citing `FPN_DivNoAssert` is current, not stale.

### is_fp_binary_v / is_fp_decimal_v

Disjoint domain traits (B6): binary `FixedPoint<2,F>`+`FPN_Binary<64>` vs decimal `FixedPoint<10,F>` (Ship B). The legacy trait spelling `is_FPN_v` was retired at A.5 — every dispatcher gates on `is_fp_binary_v` directly.

### FPN_Decimal (arrives at Ship B)

The decimal money type (`FixedPoint<10,8>`, scale 10⁸) — NOT yet in the codebase; documented here so the binary/decimal naming pair reads as designed (D-143).
