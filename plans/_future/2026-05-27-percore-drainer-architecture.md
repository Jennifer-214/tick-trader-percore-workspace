---
type: future-roadmap-exploration
title: Per-core drainer architecture — cache locality + pipeline parallelism
established: 2026-05-27
established_context: v5.15.5.F.4d.1.B.6 planning; operator-driven architectural exploration during drain_manual_closes per-core/global question
status: future-exploration (not immediate priority; queued post-paper-test-session)
sister_debt: TECH_DEBT-129
sister_roadmap: plans/_future/2026-05-12-decoupling-endgoal-roadmap.md (long-horizon decoupling)
trigger: post-paper-test-session (data-driven) OR drainer-thread profiling shows bottleneck OR multi-core p99 exceeds slow-path budget
---

# Per-core drainer architecture — exploration roadmap

**Future-roadmap doc.** Captures architectural options surfaced during v5.15.5.F.4d.1.B.6 planning when operator explored alternatives to current global drainer pattern. Not for immediate implementation; documents the design space + trade-offs for when the decision becomes data-driven post-paper-test session.

---

## Current architecture (baseline)

Per `CLAUDE.md § Concurrency model summary`:

```
PRODUCER (1 thread)         DRAINER (1 thread)        PER-CORE CONSUMERS (N=2..16)
─────────────────           ──────────────────        ──────────────────────────────
Binance WS                  OMS_DrainSubmit           SLOW thread (1 per core)
  ├─ parse tick    ──┐      OrderManager_Tick         ├─ EventLoop_UpdateRollingState
  ├─ ema_price    ──┤       DrainPostFill            ├─ Regime_Classify
  ├─ fan_out:      ──┘────→ SPSC ring               ├─ Strategy rebuild
  │   for c in N: │                                  ├─ ExecutionCore_SetParameters
  │     push(c)   │                                  │   (seqlock → HOT)
  └─ GUI publish  │                                  ├─ TimeExitOneCore
                  ↓                                  └─ TrailingSLRatchet
              SPSC ring → HOT thread (1 per core)
                          ├─ BG_Evaluate (branchless)
                          ├─ SG_Evaluate ×2
                          └─ push TradeEvent (rare branch)
```

**Drainer's current responsibilities (single thread, all cores):**
- `OMS_DrainSubmit` — process queued order submissions (operator-initiated + automatic)
- `OrderManager_Tick` — process fill notifications from exchange (Binance WS)
- `DrainPostFill` — bookkeeping after fills (P&L update, trade log, position update)
- `drain_manual_closes` — operator GUI close events (lambda at line 2155)
- `drain_with_submit` — drainer-cycle order submission (lambda at line 2126)
- Kill switch evaluation per core
- Various other per-core state transitions touched on drainer's iteration

**Single drainer thread is shared across all N cores' order flow.**

---

## Architectural options

Three nested options; increasing scope. Each option includes the prior.

### Option A — Per-core `drain_manual_closes` only (scoped)

**Scope:** Move GUI-initiated manual close events from global drainer → per-core slow-path queues.

**Mechanism:**
- NEW per-core SPSC queue: `state.cores[c].gui_event_queue` (GUI thread writes; slow-path reads)
- GUI close button → builds close request → routes to `state.cores[c].gui_event_queue` based on which core owns the position
- Each core's slow-path drains its queue on next cycle (~microseconds)
- Drainer thread NO LONGER processes manual closes

**Pros:**
- Cache locality for manual close handling (per-core L1)
- GUI responsiveness improvement (latency from click → action shorter)
- Drainer thread offload (less work per cycle)
- Architecturally clean: GUI events live with the core that owns the position

**Cons:**
- New per-core queue infrastructure (memory cost: 1 cache line per core for queue + N×queue_capacity per slot)
- GUI routing logic gains complexity (already knows which core owns position; small)
- New cross-thread sync surface (GUI thread vs slow-path thread)

**Effort:** ~1-2 days focused.

### Option B — Hybrid (market events global; operator/policy events per-core)

**Scope:** Option A + extend to other operator/policy-driven events.

**Mechanism:**
- **Global drainer** keeps:
  - `OMS_DrainSubmit` — order submission to exchange (single thread = single API client serialization)
  - `OrderManager_Tick` — fill notification processing (exchange-driven)
  - `DrainPostFill` — post-fill bookkeeping (tight coupling to fill arrival)
- **Per-core slow-path** absorbs:
  - `drain_manual_closes` (Option A)
  - Kill switch evaluation (already mostly per-core via `state.cores[c].kill_state`)
  - Time exit evaluation (already per-core via `state.cores[c].time_exit_state`)
  - Trailing SL ratchet (already per-core)
  - "Close all" cross-core events: coordinated via a global flag that all per-cores poll

**Pros (Option A +):**
- Cleaner mental model: "global drainer = events FROM market"; "per-core slow-path = events FROM operator/policy"
- Most operator-initiated work runs on the core that owns the position (full cache locality win)
- Drainer thread load drops substantially (only handles market events)

**Cons (Option A +):**
- "Close all" cross-core coordination needs care (flag + per-core poll OR explicit cross-core message bus)
- Operator may notice slightly different latency profile depending on event type
- More architectural complexity (two event-flow paths instead of one)

**Effort:** ~3-5 days focused.

### Option C — Full per-core drainer architecture (most ambitious)

**Scope:** Eliminate central drainer entirely; fold all drainer responsibilities into per-core slow-path threads.

**Mechanism:**
- Each core's slow-path thread becomes its own mini-drainer for its own positions
- Single API client (Binance REST/WS) becomes threadsafe-serialized via a NEW lock-free MPSC queue (multi-producer = N cores; single-consumer = API client thread)
- Per-core slow-path: builds order requests → enqueues to API-client-MPSC → API client serializes to exchange + returns fill notifications via per-core SPSC
- Fill notifications: exchange → API client thread → routes back to specific core's per-core SPSC for that core's slow-path to process

**Pros (Option B +):**
- Maximum cache locality (no central thread iterating all cores)
- Maximum pipeline parallelism (N cores fully independent)
- NUMA-perfect (each core's threads + data on local socket)
- Drainer thread eliminated entirely → one less context-switch source
- Scales naturally with N (no central-thread-bottleneck)
- Removes the "drainer-as-single-owner-of-order-flow" invariant constraint

**Cons (Option B +):**
- Significant architectural rework: producer/drainer/slow-path/hot threading model changes substantially
- API client serialization queue is NEW infrastructure (lock-free MPSC; must be tested)
- Per-core slow-path threads gain more work (may need cadence tuning)
- Tests + code that assume central drainer need wholesale rework
- Rate-limit handling across N cores requires coordination (current single-thread is simple)
- Cross-core "halt all" / "close all" events need coordinated rollout

**Effort:** ~1-2 weeks focused (largest scope; multi-ship architectural rework).

---

## Headline win (per operator interest 2026-05-27)

**Cache locality is the headlining benefit** across all three options. Operator quote: "cache locality would be the bigger win here, it would give more room to work with."

| Current global drainer | Per-core variants |
|---|---|
| Drainer thread walks `state.cores[c]` for all c on drainer's CPU. Each iteration touches a different cache line cluster (state.cores[c] is alignas(64) → 1 line per core minimum). Drainer CPU's L1 fills with all N cores' state, evicting earlier work. | Each core's slow-path only touches `state.cores[c]` for its OWN c. Perfect L1 residency for that core's state. No cross-core cache-line bounces. NUMA-local if cores pinned to local socket. |

For N=4 cores: drainer iterates 4 cache-line clusters per cycle (~256B of state); each core's L1 fills with ALL 4 clusters → potential cache contention with own working set.
For N=16 cores: drainer iterates 16 clusters (~1KB); much worse cache pressure.

Per-core variants: each core's slow-path L1 holds ONLY its own state cluster (~64B). Order-of-magnitude better locality at high N.

---

## Other wins (cumulative across options)

1. **Pipeline parallelism** — N cores process events in parallel; latency = max(per-core) not sum(per-core).
2. **NUMA-awareness** — per-core threads pinned to local CPU; reduces cross-socket traffic. Important at N ≥ 8 cores with multi-socket NUMA topology.
3. **GUI responsiveness latency win** — operator click → per-core processing within next slow-path cycle (~microseconds); current path goes through drainer queue + drainer cycle cadence.
4. **Backpressure isolation** — heavy event traffic on one core doesn't block other cores' processing.
5. **Slow-path threads already exist + have idle cycles** — adding more work fits existing cadence without new threading infrastructure.
6. **Drainer-as-bottleneck risk removed** — single-point-of-contention for ALL order flow eliminated.

---

## Prerequisites

Before this exploration becomes a serious ship candidate, need:

1. **Paper-test session throughput data** — actual production behavior data showing whether global drainer is a measurable bottleneck. Currently working from architectural reasoning; need empirical confirmation that per-core IS worth the refactor cost.
2. **Decoupling roadmap stability** — `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` covers runtime/viewer split; that work has higher priority + may interact with drainer architecture. Settle decoupling first.
3. **File-size discipline closure** — `.B.5-.B.11` umbrella closes file-size split discipline. Per-core drainer architectural rework would touch many files; cleaner foundation post-umbrella.
4. **Profile drainer-thread CPU usage** — `LATENCY_PROFILING=ON` build + per-thread CPU monitoring during paper-test session. If drainer is < 20% CPU, low priority. If > 50%, high priority.

---

## Trigger (decision point)

Reconsider this exploration when ANY of:

- Paper-test session profiling shows drainer thread > 50% CPU
- Multi-core (N ≥ 8) p99 latency exceeds slow-path budget (per CLAUDE.md latency table)
- GUI responsiveness complaint from operator (close click feels laggy)
- Cross-thread cache-line contention observed via `perf` counters during paper-test
- Decoupling roadmap stabilized AND file-size discipline closed AND a "good architectural ship" opportunity opens

Until then: GLOBAL drainer is the production design. `.B.6` subfolder split moves the LAMBDA bodies between files but preserves the threading model.

---

## Effort/risk matrix

| Option | Effort | Risk | Cache locality win | Refactor scope |
|---|---|---|---|---|
| Stay with current global | 0h | none | baseline | none |
| Option A: per-core manual closes | ~1-2 days | LOW (additive; doesn't break existing) | MED (GUI events only) | Small (1 new queue per core) |
| Option B: hybrid market/operator | ~3-5 days | MED-HIGH (re-org of slow-path responsibilities) | HIGH (most events on owning core) | Medium (per-core queues + cross-core coord for "close all") |
| Option C: full per-core drainer | ~1-2 weeks | HIGH (architectural rework; many files; new MPSC infrastructure) | MAXIMUM | Large (drainer thread eliminated; API client serialization layer) |

---

## Cross-references

- TECH_DEBT-129 (this entry's parent debt entry)
- `CLAUDE.md § Concurrency model summary` (current architecture)
- `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` (sister architectural-exploration; may interact with this)
- `DESIGN_SPECS/concurrency-patterns/concurrency-model-summary.md` (canonical doc; will need amendment if any option lands)
- `DESIGN_SPECS/data-disciplines/cache-line-discipline.md` (Stage 2 DRAFT; cache locality framework)
- `v5.15.5.F.4d.1.B.6` plan body (where this exploration surfaced; Decision H is the within-scope merge that doesn't change threading model)

---

**End of future-roadmap exploration v1.0 (2026-05-27).** Reconsider trigger conditions post-paper-test session.
