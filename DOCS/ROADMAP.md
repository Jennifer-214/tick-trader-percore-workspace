# Roadmap

**Audience:** Operator + contributor wanting the strategic trajectory.

Current state + planned trajectory. Not detailed plan — that's `plans/`. This is the strategic picture.

---

## Where we are: v5.15.5.F.4d.1.D (current)

- Per-node sharded engine (production)
- Binance crypto only
- Single account; engine partitions internally
- GUI (Dear ImGui) + engine integrated single-process
- Audit-driven discipline established
- ~80 DESIGN_SPECS codified
- AGPL public

---

## Next: v0.1.0 (`.E` sub-sprint; ~25-35 days focused work)

**The Architecture E++ rework.** Per `plans/v5.15-live-readiness/E-MASTER-REFERENCE.md` for full detail.

8 ships:

```
.E.0 Pre-coding plan audit + verification    (LOW-RISK; ~3-5d)
  ↓ blocks all subsequent
.E.1 Foundation                              (HIGH-RISK; ~5-7d)
  - Core → Node hard rename
  - Per-node slow-path absorbs drainer
  - FOREACH_EXCHANGE substrate (Binance only wired)
  - Cluster/Node/Deployment hierarchy
  - Event-sourced O(1) aggregator
  - Portfolio/Position SoA
  - Hierarchical kill switches
.E.2 Headless + per-node configs + ML CLI + docs   (HIGH-RISK; ~10-14d)
  - fox-engine (headless service)
  - fox-tui + fox-cli + foxml-train (3 new binaries)
  - Per-node config folder layout
  - mmap state-publication + UDS command channel
  - Comprehensive operator documentation
  - SSH-based remote operations
.E.3 WS-API + persistent TLS connections    (MED-HIGH; ~5-7d)
  - Binance /ws-api/v3 persistent WS
  - TLS session resumption
  - ~15-25ms/submit latency saving
.E.4 io_uring + kTLS                         (HIGH-RISK; ~7-10d)
  - Per-node io_uring rings
  - kTLS for kernel-side encryption
  - ~10-20μs further latency reduction
.E.5 Real sub-accounts + capital framework   (MED; ~3-5d)
  - Per-node Binance sub-account binding
  - N × rate-limit budget
  - Internal-transfer plumbing
  - Capital allocation policy
.E.6 Exchange adapter framework generalization (MED-LOW; ~3-5d)
  - FOREACH_EXCHANGE genericity verification
  - DOCS/CONTRIBUTING/add-exchange.md substantial
  - Template adapter scaffold
.E.X Strategy hot-reload (standalone)        (MED; ~3-5d)
  - .so reload via dlopen
  - Atomic strategy pointer swap
.E.7 IBKR (OPTIONAL-FUTURE)                  (deferred; operator-triggered)
.E.8 DPDK / Onload (DEFERRED INDEFINITELY)   (no hardware)
```

**End state after v0.1.0:** Multi-exchange ready; sub-account isolation; headless service; HFT-class latency improvements; comprehensive documentation; AGPL public.

---

## v0.2.0+ (post-`.E`)

Likely candidates:

### Specific exchange addition (operator-triggered)

When operator wants to actually add Alpaca/Coinbase/etc.:
- Add 1 row to FOREACH_EXCHANGE
- Implement adapter (~3-7 days per exchange)
- Lands FOREACH_EXCHANGE Stage 4 promotion (2nd canonical)

### Hot-reload Layer 2 (if not at `.E.X`)

If `.E.X` hot-reload not done at v0.1.0: lands at v0.2.0+.

### Strategy A/B testing infrastructure

Statistical significance + auto-promotion. Operator-side; depends on actually running strategies long enough to need this.

### Meta-controller (per D-23)

C++ supervisor that monitors per-node P&L; rebalances capital; rotates strategies. Reads engine state via mmap; sends commands via UDS. Sister to engine but separate binary.

---

## v6.X+ (long-term horizon)

### Decoupling endgame

Per `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`:
- Runtime/viewer fully decoupled (partially at `.E.2`)
- Multiple concurrent viewers
- Web dashboard option
- Headless training pipeline

### Context-aware CLAUDE.md

Per `plans/_future/2026-05-28-context-aware-claude-md-loading-roadmap.md`:
- Multi-file `CLAUDE.<context>.md` (cpp / ml / docs / etc.)
- Harness loads relevant overlay per work axis
- Reduces single-monolithic-CLAUDE.md bloat

### Docs-as-meta-code

Per `plans/_future/2026-05-28-docs-as-meta-code-roadmap.md`:
- Structured plans + DESIGN_SPECS function as REFERENCES for CI tools
- Tools auto-generate from doc structure
- LLM removed from drift-prone middle layer

### DPDK / smart NIC (hardware-dependent)

When/if operator acquires DPDK-compatible hardware:
- `.E.8` re-activated
- ~3-5μs tick-to-wire on commodity x86_64
- Practical HFT-class limit

### Repo rename to FoxML_PortfolioManager (per D-62)

At v0.1.0 ship close: evaluate; defer indefinitely; or execute.

---

## What's NOT on the roadmap

❌ GUI-first dashboard (per `meta-disciplines/gui-deprecation-decision-rationale.md`; CLI/TUI preferred)
❌ Managed-service offering (engine is power-user; operator-self-managed)
❌ Click-and-deposit experience
❌ Mobile app (Prometheus + Grafana phone view is sufficient)
❌ Multi-tenant (engine is single-operator; if needed, run multiple engine instances)
❌ Strategy marketplace (operator owns their strategies)

---

## Strategic principles guiding roadmap

Per memory + DESIGN_PHILOSOPHY:

1. **Best-software path** (`feedback_motivated_collaborator_for_caramel`) — quality bar; hedge-fund-visibility
2. **Plan-right-not-fast** — substantial planning before any substantial coding
3. **Structural-fix-preferred** — close bug classes structurally; not symptomatic patching
4. **Canonical-sister-extension** — extend existing patterns; don't parallel
5. **No defer for effort** — substantial scope OK; defer only for empirical-validation or hardware-prerequisite
6. **Power-user-first** — operator builds for self; don't optimize for novice
7. **Audit-driven discipline** — every substantial ship audited before coding

---

## Operator commitment

Strategic trajectory requires:
- Server hardware for production (laptop OK for dev)
- 3-6 months focused engineering for `.E` (or distributed across years)
- Discipline to plan + audit before coding
- AGPL contribution back (if forking; not required for self-use)

Per `feedback_motivated_collaborator_for_caramel`: this is multi-year project. Roadmap is multi-year. Path is clear.

---

**End of ROADMAP.md v1.0** (2026-05-28).
Updated at each major version close.
