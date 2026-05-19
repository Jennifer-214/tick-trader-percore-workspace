---
type: concurrency-pattern
stage: 2-draft
version: 1.0
established: 2026-05-18
tags: [concurrency, data-oriented-design]
surface: [hot-path, slow-path, oms-drainer, producer, gui-thread]
sister_specs: [cache-line-discipline.md, universal-registry-bitmap-dispatcher-pattern.md]
applies_at_skills: [/hft-audit, /blindspot-scan]
---

# Concurrency model summary (thread architecture codification)

**Established:** 2026-05-18 (v5.15.5.F.4d.1.B.3 doc-layer refresh — codify implicit thread architecture)
**Status:** Stage 2 DRAFT v1.0 — full body matures at `.C` candidate ship

Codifies the implicit thread architecture currently scattered across CLAUDE.md Architecture diagram + H1-H3 / H6 / DESIGN_PHILOSOPHY § 6.

---

## Thread topology (sharded engine)

```
GLOBAL                          PER-CORE (N=2..16, default 4)
──────                          ────────────────────────────────
PRODUCER (1 thread)             SLOW thread (1 per core)
├─ Binance WS parser            ├─ EventLoop_UpdateRollingStateOneCore
├─ DepthRecorder                ├─ Regime_Classify
├─ TickRecorder                 ├─ Strategy rebuild
└─ fan_out: SPSC push to N      ├─ ExecutionCore_SetParameters (seqlock)
                                ├─ TimeExitOneCore
DRAINER (1 thread)              └─ TrailingSLRatchetOneCore
├─ OMS_DrainSubmit              
├─ OrderManager_Tick            HOT thread (1 per core)
└─ DrainPostFill                ├─ ExecutionCore_Tick (≤500ns p99)
                                ├─ BG_Evaluate (branchless)
ASYNC (separate threads)        ├─ SG_Evaluate ×2
├─ BinanceOrderAPI              └─ push TradeEvent (rare branch)
├─ Notify worker                
└─ GUI publish thread           
```

---

## Sync primitives

### SPSC rings (lock-free queues)

- **Producer → per-core consumer:** tick events
- **Slow → hot:** params (seqlock; see below)
- **Hot → drainer:** TradeEvent push
- **Drainer → slow:** post-fill events

All SPSC rings bounded; `Limits.hpp` defines max depth. Backpressure detectable via push-fail count.

### Seqlock (slow → hot parameter handoff)

Why seqlock instead of mutex:
- No blocking on hot path (H3 forbids `std::mutex`)
- Reader sees consistent snapshot (version counter detects mid-write)
- Writer monopolizes write side (slow thread; no contention)

Pattern:
```cpp
// Writer (slow thread):
version.fetch_add(1, release);  // odd → write in progress
// ... write params ...
version.fetch_add(1, release);  // even → write complete

// Reader (hot thread):
do {
    v1 = version.load(acquire);
    if (v1 & 1) continue;
    // read params snapshot
    v2 = version.load(acquire);
} while (v1 != v2);
```

### Atomic flags

Cross-thread state (kill_switch_tripped / flatten_pending / recovery_until_us / last_ws_tick_us):
- `std::atomic<T>` with explicit `memory_order_acquire` / `memory_order_release` semantics
- Each `alignas(64)` to prevent false-sharing
- Slow thread typically writes; hot thread reads on every tick

---

## Visibility rules

**Happens-before:**
- Writer's release → Reader's acquire establishes happens-before (C++ memory model)
- Seqlock version counter provides this via acquire/release pairs
- SPSC ring's head/tail provide this via atomic loads/stores

**Memory ordering choice:**
- `memory_order_relaxed` — only for counters where ordering doesn't matter (rare; usually wrong)
- `memory_order_acquire` / `memory_order_release` — default for cross-thread visibility
- `memory_order_seq_cst` — rarely needed; overkill for most uses

---

## Sister patterns

### GUI ↔ HP/SP thread isolation (CRITICAL)

Per CLAUDE.local.md going-forward rule "GUI ↔ HP/SP thread isolation":
- GUI thread is SEPARATE from engine threads
- NEVER pointer-share state between GUI and engine
- Communicate via file (snapshot) + reload-signal
- Typed mirror per side; no implicit conversion

See `universal-registry-bitmap-dispatcher-pattern.md` § GUI ↔ engine.

### Per-core data-plane single-writer

Each core's slow_state has SINGLE writer (the per-core slow thread). Hot thread reads via seqlock. No cross-core writes to slow_state.

---

## Anti-patterns (NEVER per H1-H3)

- `std::mutex` / `condition_variable` / `sleep_for` / `pthread_rwlock` — ANYWHERE
- `malloc` / `new` / `std::vector` / `std::string` / `std::function` — ANYWHERE
- `virtual` / `std::shared_ptr` / `std::unique_ptr` — on hot path (H2)
- Pointer-sharing between GUI thread and engine threads
- C++ bitfield syntax in cross-thread structs (H14)

---

## Pattern lifecycle

- **Stage 1 (problem):** discipline implicit; scattered across H1-H3 / H6 / CLAUDE.md Architecture diagram
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-18 sketch)
- **Stage 3+ (first canonical / cohort / promotion):** matures at `.C`/`.D` ships — codify worked examples per sub-system (BinanceCrypto WS parser / OMS drainer / per-core slow_state / etc.)

---

## Cross-references

- Sister: `cache-line-discipline.md` (layout-level discipline; this is thread-level)
- Sister: `universal-registry-bitmap-dispatcher-pattern.md` § GUI ↔ engine
- CLAUDE.md § Concurrency model summary (referenced this spec)
- CLAUDE.md H1 (no heap), H2 (no virtual on hot path), H3 (no mutex), H6 (alignas), H14 (no bitfield)
- DESIGN_PHILOSOPHY.md § 6 (Concurrency family)
- CLAUDE.local.md going-forward rule "GUI ↔ HP/SP thread isolation"

---

**End of concurrency-model-summary v1.0 DRAFT.** Stage 3+ work matures at `.C`/`.D` candidate ships.
