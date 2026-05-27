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

### Option B — Hybrid (market events global; operator/policy events per-core) — **REJECTED 2026-05-27**

**Operator reasoning:** "the per core drainer just straight up seems to win tbh, when you lay it out like that, like not even hybrid just per core is functionally better right?"

Hybrid was originally proposed as a "safer middle ground" between Option A (scoped) and Option C (full). On reflection it's an **awkward middle**: more complexity than Option A (introduces dual event-flow paths), less win than Option C (still has global drainer thread = doesn't eliminate the bottleneck or get full cache locality). The dual-path mental model ("market events here; operator events there") is harder to reason about than either "all global" (current) or "all per-core" (Option C).

**Verdict:** Skip Option B. If we go beyond Option A, go directly to Option C.

(Original Option B content preserved below for historical context.)

~~Scope: Option A + extend to other operator/policy-driven events. Global drainer keeps OMS_DrainSubmit + OrderManager_Tick + DrainPostFill; per-core slow-path absorbs drain_manual_closes + kill switch eval + time exit eval + trailing SL ratchet. "Close all" cross-core events coordinated via global flag.~~

### Option C — Full per-core drainer architecture (TARGET ARCHITECTURE)

**Status:** OPERATOR-PREFERRED eventual target per 2026-05-27 reasoning. Mental model "each core owns everything about its positions, end to end" is unambiguously cleaner than current global drainer OR hybrid.

**Scope:** Eliminate central drainer entirely; fold all drainer responsibilities into per-core slow-path threads. Replace drainer with NEW API serialization infrastructure.

**Mechanism:**

```
Current architecture                  Option C target architecture
────────────────────                  ────────────────────────────
Producer (1)    → fans out ticks      Producer (1)        → fans out ticks (unchanged)
Drainer (1)     → owns order flow     [DRAINER ELIMINATED]
                                      API client thread (NEW) → consumes MPSC from N cores;
                                                                  serializes to Binance (rate-limit safe)
                                      Fill router thread (NEW) → reads Binance user-data WS;
                                                                  routes fills to per-core SPSC
                                                                  (by order_id → core mapping)
Per-core slow-path (N)  → strategy    Per-core slow-path (N)  → owns ENTIRE position lifecycle:
                                                                strategy + order build + fill consume +
                                                                manual close + kill switch + post-fill
Per-core hot (N)        → BG/SG eval  Per-core hot (N)        → unchanged
```

**Pros (Option A +):**
- **Maximum cache locality** (no central thread iterating all cores; each core's L1 only holds own state)
- **Maximum pipeline parallelism** (N cores fully independent for entire position lifecycle)
- **NUMA-perfect** (each core's threads + data on local socket; per-core API queue slots too)
- **Drainer thread eliminated entirely** → one less context-switch source; one less single-point-of-contention
- **Scales naturally with N** (no central-thread-bottleneck; adding cores adds throughput proportionally)
- **Cleanest mental model**: "each core owns position lifecycle"; no special-case dispatch logic
- **Future-extensible**: adding per-core features (per-core risk profile, per-core latency budgets, per-core kill-switch policy) becomes trivial because the threading model already supports core-isolated state

**Cons (Option B +; the REAL cost of Option C):**

The big cost is NEW infrastructure for API client serialization, not just "delete the drainer":

1. **API client thread is NEW** (replaces drainer's `OMS_DrainSubmit` role). Binance has rate limits + connection limits → single connection serialized via MPSC queue is the safe pattern. This thread:
   - Consumes order-submit requests from a NEW MPSC queue (N producers = N cores)
   - Serializes calls to Binance REST API (rate-limit safe)
   - Returns submit-ack via per-core SPSC queue (acks → per-core slow-path)

2. **Fill router thread is NEW** (replaces drainer's `OrderManager_Tick` role). Receives fill notifications from Binance user-data WS + routes each to the correct core's SPSC queue based on `order_id → core` mapping (need to maintain this mapping; small struct per active order).

3. **MPSC queue is NEW infrastructure** (lock-free; multi-producer single-consumer). FoxLIB has SPSC primitives but not MPSC currently — need to design + test under contention scenarios.

4. **Cross-core "close all" / "halt all" events** need a coordinated rollout mechanism (currently trivial via drainer). Options: per-core poll a global flag (simple; small overhead) OR explicit cross-core message via MPSC (cleaner; more infrastructure).

5. **Test + code rework**: any test that assumes central drainer needs adjustment. Significant test-side scope.

6. **Per-core slow-path threads gain more work** — may need cadence tuning (currently 8 Hz slow-path cycle; might need to be more frequent if absorbing drainer's responsibilities).

7. **Rate-limit handling across N cores** — currently trivial (1 thread = 1 rate-limit budget). With N producers via MPSC, need backpressure / rate-aware enqueue (don't let one core's high-frequency submits starve others).

**Effort (HONEST re-estimate 2026-05-27 PM per operator pushback "are you sure the per core drainer is a huge change?"):** ~5-10 days focused work, NOT 1-2 weeks as initially claimed. The initial "multi-week" estimate was over-cautious; honest component breakdown:

| Component | Honest estimate |
|---|---|
| MPSC queue primitive in FoxLIB (Vyukov bounded; well-known pattern) | 1-2 days |
| API client thread (mostly moves existing drainer OMS_DrainSubmit code) | 1-2 days |
| Fill router thread (Binance WS → per-core SPSC by order_id → core mapping) | 1-2 days |
| Per-core slow-path absorbs drainer responsibilities (code exists; execution context shifts) | 2-3 days |
| Cross-core "close all" coordination (shared flag; simple) | ~half day |
| Test rework (unknown depth of drainer-test coupling; biggest variable) | 1-3 days |
| Drainer thread deletion + cleanup | ~1 day |

**Total: ~5-10 days focused** (closer to 5-7 if test coupling is shallow; closer to 10 if deep).

Suggested 3-ship split (smaller per-ship; easier to verify):

- **Ship 1 — Foundation**: MPSC primitive in FoxLIB + tests; new thread infrastructure (API client + fill router) running in PARALLEL with existing drainer for safety fallback
- **Ship 2 — Migration**: Per-core slow-path absorbs drainer responsibilities one event class at a time (manual closes first, then fills, then post-fill)
- **Ship 3 — Cleanup**: Drainer thread deletion + cross-core "close all" coordination + final test pass

**The real risk isn't scope size — it's that paper-test throughput data doesn't exist yet** to validate whether this architectural shift produces measurable improvement. Premature architectural optimization without throughput data could deliver an elegant refactor with zero observable production benefit. Trigger remains: post-paper-test session profiling.

**Prerequisites (must land first):**
- Paper-test session throughput data showing drainer-thread bottleneck (data-driven justification)
- File-size discipline closure (.B.5-.B.11) — cleaner foundation for the rework
- Decoupling roadmap stability — runtime/viewer split priority + may interact with Option C
- FoxLIB MPSC primitive landed (could be done independently as a foundation ship)

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
| Option C: full per-core drainer | ~5-10 days (revised down from 1-2 weeks) | HIGH (architectural rework; new MPSC infrastructure; touches threading model) | MAXIMUM | Medium-Large (drainer thread eliminated; API client serialization layer; ~3 ships) |

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
