---
type: concurrency-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-13
tags: [concurrency, structural-fix, latency-discipline]
surface: [oms-drainer, slow-path]
sister_specs: [cross-thread-snapshot-publish-cluster-isolation.md, decision-time-data-binding-pattern.md, persisted-struct-with-ephemeral-field-coexistence-pattern.md]
applies_at_skills: []
---

# Phase-separated drainer for safe cross-temporal derives

**Established:** 2026-05-13 (v5.15.5.C.4 pre-coding consult; emerged from two failed derive attempts D2.C + D2.D in the FillRecord-as-snapshot anti-pattern analysis)
**Status:** ACTIVE (NEW spec; first canonical application = v5.15.5.C.4 Phase F + G — OrderManager_Tick split + 3-field derive cascade)
**Cross-references:**
- CLAUDE.md item 18 (slow-path latency reduction priority — phase split must not bloat 100μs cycle budget)
- CLAUDE.md item 19 (structural fix preferred — phase split is the structural answer to the recurring "FillRecord-snapshot defensive class")
- CLAUDE.md item 28 (latency-vs-cache framework — phase split's win is cache-miss reduction via derive cascade)
- `structural-fix-preferred-decision-framework.md` — meta-framework that picks this pattern (recurrence count 2: D2.C + D2.D)
- `aggressive-memory-reduction-techniques.md` Technique 4 (derive vs store) — phase discipline UNBLOCKS Technique 4 for transient-source-data fields that otherwise fail safety check
- `cache-layout-discipline-for-hot-side-structs.md` — derive cascade is the size-reduction mechanism that this pattern enables
- `slot-state-foreach-registry-with-storage-routing.md` — FOREACH_FILL_RECORD_FIELD registry shrinks naturally after derive cascade
- `bitmap-flag-api.md` — close_mask + open_mask bitmaps are the phase-consumer drivers (existing infrastructure)

---

## Problem statement

In a drain cycle that processes multiple events for the same logical entity (slot, order, signal, position), downstream consumers can see CORRUPTED MID-MUTATION state if events for that entity are processed in interleaved fashion. Specifically:

1. **Event A** (e.g., CLOSE / SELL) mutates entity state E → CLOSED form
2. **Event B** (e.g., OPEN / BUY) for the SAME entity mutates state E → NEW state (overwriting the close-completed values)
3. **Consumer C** (e.g., DrainPostFill accounting) runs AFTER both events; reads state E to compute close-side derivations — but state E now reflects the NEW state, not the closed-trade state

The defensive solution is a SNAPSHOT pattern: capture all close-side derivable values at Event A time into a per-entity buffer (e.g., FillRecord), so Consumer C reads the snapshot instead of state E. This pattern is correct but EXPENSIVE:
- Snapshot fields occupy memory PER-entity, scaled by entity count (e.g., MAX_PORTFOLIO_POSITIONS)
- Snapshot fields straddle cache lines, multiplying drainer's per-entity cache footprint
- Adding the next "derivable from state E" field is ambiguous: add to snapshot or attempt derive? Class-18 mirror risk
- The snapshot pattern is "defensive coding against a contingency" — operationally tested or not, the memory cost is permanent

**Recurrence detection (FoxML_Trader_v2 history):** Two derive attempts within v5.15.5.C.4 (D2.C `exit_entry_notional`, D2.D `exit_total_fees`) both verified UNSAFE by the same mechanism: same-cycle SELL→BUY on same slot overwrites Position state between HandleFill SELL (writes FillRecord) and DrainPostFill (reads). The FillRecord-as-snapshot pattern at `OrderManager.hpp:319-328` exists precisely because of this contingency. The recurrence count (2) meets the structural-fix-preferred threshold.

---

## The pattern (concrete shape)

Split drain-cycle event processing into PHASES by event-type, with consumer passes interleaved at safe phase boundaries:

```cpp
void Drainer_RunCycle(EngineShardedState<F>& state) {
    // ───── Phase A: drain CLOSE-type events ─────
    // Mutations confined to close-side state (clear slot bitmap, etc.).
    // CRITICAL: do NOT touch state used by Consumer C in Phase A.5.
    while (TryPop_FilterByType(CLOSE, &event)) {
        HandleFill_Close(event);  // Writes FillRecord; CloseSlot clears bitmap; preserves Position values
    }

    // ───── Phase A.5: consumer pass (close-mask) ─────
    // Reads state E in CLOSE-completed form. Derive-from-state-E is now safe.
    DrainPostFill(close_mask);  // Reads Position.entry_price + .quantity (CLOSE values; not yet overwritten)

    // ───── Phase B: drain OPEN-type events ─────
    // Now safe to mutate state E — Phase A.5 consumer already ran.
    while (TryPop_FilterByType(OPEN, &event)) {
        HandleFill_Open(event);  // Portfolio_OpenSlot OVERWRITES Position (no race; Phase A.5 already done)
    }

    // ───── Phase B.5 (optional): consumer pass (open-mask) ─────
    // For derives on OPEN-side. If symmetric to Phase A.5.
    DrainPostEntry(open_mask);  // Optional
}
```

### Event-type filtering options

Three implementation mechanisms for "drain only type X events from result_queue":

**Option I — Per-ring drain order:** if events of different types arrive on separate SPSC rings, drain rings in phase-required order. No per-event filtering needed.

```cpp
// If close_ring + open_ring + cancel_ring exist as separate SPSCs:
while (TryPop(close_ring, &e)) { HandleFill_Close(e); }
DrainPostFill(close_mask);
while (TryPop(open_ring, &e)) { HandleFill_Open(e); }
```

**Option II — Peek-and-branch:** single result_queue with `event.type` discriminator. Drain in two passes; skip non-matching events in each pass.

```cpp
// Pass 1: drain close events only
while (TryPop_Peek(&result_queue, &e)) {
    if (e.type == CLOSE) {
        Pop(&result_queue, &e);
        HandleFill_Close(e);
    } else {
        break;  // hit a non-close event; queue head can't advance until ring is FIFO-friendly
    }
}
```
Caveat: requires a peek-without-pop primitive OR the ring's FIFO ordering doesn't matter for events of different types within a phase.

**Option III — Drain-into-buckets:** single pass through result_queue; sort into per-type local arrays; process arrays in phase order.

```cpp
constexpr int MAX_EVENTS_PER_CYCLE = 64;
Event close_bucket[MAX_EVENTS_PER_CYCLE];
Event open_bucket[MAX_EVENTS_PER_CYCLE];
int close_n = 0, open_n = 0;

while (TryPop(&result_queue, &e)) {
    if (e.type == CLOSE && close_n < MAX_EVENTS_PER_CYCLE) close_bucket[close_n++] = e;
    else if (e.type == OPEN && open_n < MAX_EVENTS_PER_CYCLE) open_bucket[open_n++] = e;
}

for (int i = 0; i < close_n; i++) HandleFill_Close(close_bucket[i]);
DrainPostFill(close_mask);
for (int i = 0; i < open_n; i++) HandleFill_Open(open_bucket[i]);
```
Caveat: requires stack buffer; bucket overflow needs explicit handling (per CLAUDE.md item 19 — overflow should be IMPOSSIBLE by design, not just bounded; size bucket arrays to MAX events per cycle).

### Generalization to N event types

For maker-order lifecycles (PARTIAL_FILL_BUY, PARTIAL_FILL_SELL, FILLED, CANCELED, TIMEOUT, REJECTED), extend to N phases:

```cpp
// Phase 0: CLEANUP — CANCEL / TIMEOUT / REJECTED (no state-mutation that affects derives)
while (TryPop_FilterByType(CLEANUP, &e)) { HandleCleanup(e); }

// Phase 1: CLOSE — SELL fills + PARTIAL_FILL_SELL fills
while (TryPop_FilterByType(CLOSE, &e)) { HandleFill_Close(e); }
DrainPostFill(close_mask);

// Phase 2: OPEN — BUY fills + PARTIAL_FILL_BUY fills
while (TryPop_FilterByType(OPEN, &e)) { HandleFill_Open(e); }
DrainPostEntry(open_mask);
```

Each phase's mutations are confined to its event-type domain; consumer passes interleaved at safe phase boundaries; no cross-phase corruption.

---

## When to apply

Apply this pattern when ALL of these hold:

1. **Defensive snapshot exists for derivable values** — a per-entity buffer (FillRecord, etc.) stores values that COULD be derived from other in-cycle state IF that state were preserved through the consumer pass.
2. **Same-cycle entity-reuse can corrupt downstream consumers** — events of different types for the SAME entity can land in one drain cycle; consumer reads happen after both → state read may not match the close-side trade.
3. **Event lifecycle has clear pre/post phases** — events partition cleanly into "close-side" and "open-side" (or richer N-phase taxonomies). If event types overlap or have no natural phase boundary, this pattern doesn't apply.
4. **Snapshot cost is significant** — memory + cache pressure from snapshot fields is meaningful (≥10% of containing struct size; or per-record fields multiplied by ≥10 records). For 1-2 fields × 1 record, defensive snapshot is fine.
5. **Derive math is cheap** — re-computing values from in-cycle state at consumer time is bounded (~5-20 cycles per field; CLAUDE.md item 28 framework applies). For expensive transcendentals or large reductions, snapshot might still win.

## When NOT to apply

- **Single-event-type drains** — no phase distinction; pattern degenerates to today's flow
- **Consumer reads happen mid-event** — if Consumer C reads state E during Event A's processing (not after), phase split doesn't help
- **Cross-cycle dependencies** — if Phase B (open) depends on PRIOR-CYCLE Phase A.5 (close) results that aren't preserved across cycles, phase ordering can't fix
- **Snapshot is mandatory for AUDIT** — wire-format / persistence reasons require snapshot fields to exist regardless of derive feasibility (FillRecord in this codebase is NOT a wire-format field; check before applying)
- **Latency budget is binding** — multi-pass drain adds N-pass cost; if drainer is already at p99 budget, pattern adds risk

---

## Trade-offs

### Wins

- **Eliminates same-cycle entity-reuse race structurally.** Recurring class extinct; no future derive-vs-store decision needs to fail by this mechanism again.
- **Unlocks Technique 4 derive-vs-store for previously-blocked fields.** Memory + cache savings cascade from each derived field. Example (v5.15.5.C.4): FillRecord drops from 128B (2 cache lines) to ~56B (1 cache line per record); drainer close-mask iter touches 1 cache line per slot instead of 2.
- **Scales to richer event lifecycles.** Maker orders, reconcile mid-cycle, hot-swap during in-flight fills — all benefit from the same N-phase structure without re-deriving the pattern.
- **Enforces consumer-pass invariants at compile-time-visible structure.** Future readers see the phase boundaries explicitly; can't accidentally interleave a consumer at a wrong phase.

### Costs

- **Multi-pass drain over result_queue.** Worst case: 2× pass for SELL/BUY split + 3× pass for maker N-phase. Each pass = ~few ns overhead per event. For 16-event burst at ~100ns/event: ~3-5μs added. WITHIN slow-path 100μs budget; verify via bench gate.
- **Bucket-based implementation (Option III) needs stack buffers.** Per-phase fixed-size arrays scaled to MAX events per cycle. Size must be sufficient (overflow handling required).
- **Phase ordering becomes architectural contract.** Any future refactor that touches drainer flow must preserve phase boundaries. Ship-time `/dod-audit` check should verify.

### Risks

- **Hidden phase dependencies.** A consumer in Phase A.5 might inadvertently depend on Phase B state (or vice versa). Pre-coding audit + tests must verify no cross-phase reads.
- **Partner-pairing under partials.** If `Sharded_LegSlot` creates leg A/B pairs where leg A close + leg B open happen in same drain cycle, those events span phases — need to verify partner-pairing logic doesn't break.
- **Reconcile mid-cycle interactions.** If reconcile fires interleaved with the drainer, its state mutations might cross phase boundaries unexpectedly.

---

## Reference implementations

### First application: v5.15.5.C.4 Phase F + G (OrderManager_Tick SELL/BUY split + 3-field derive cascade)

- Surface: `CoreFrameworks/OrderManager.hpp:1318-1341` (OrderManager_Tick while-loop) + `CoreFrameworks/EngineSharded.hpp:2567-2569` (drainer sequencing) + `CoreFrameworks/ControllerEventLoop.hpp:1385/1408/1585` (DrainPostFill derive sites)
- Removes from FillRecord: `exit_net_pnl` (16B), `exit_entry_notional` (16B), `exit_total_fees` (16B) = 48B per record × 16 records = **768B per OMS saved**
- Adds to Position struct: `exit_fill_price` (16B FPN) + `is_maker` (1-bit-flag or full byte; TBD per pre-coding investigation)
- FillRecord drops 3 FPN fields/record (48B at 16B FPN) → ~halves it toward one cache line per record (relative win; absolute size tracks the live struct, not a frozen count)
- Drainer close-mask iter cache footprint: 1 cache line per slot (was 2)

### Anticipated future applications

- **Maker-order lifecycle phases (v6.x+)**: PARTIAL_FILL_BUY / PARTIAL_FILL_SELL / FILLED / CANCELED / TIMEOUT / REJECTED — each phase confined to its own event-type drain pass; consumer passes interleaved at safe boundaries. Eliminates the multiplied same-cycle corruption surface area that maker introduces.
- **Reconcile mid-cycle**: if reconcile fires between drainer phases, reconcile's state mutations are constrained to a separate phase; consumer passes don't see partial-reconcile state.
- **Hot-swap during in-flight fills**: model swap event is its own phase; prediction-side consumers run before swap; post-swap consumers run after.

---

## Lessons / gotchas

### Phase ordering must be enforced architecturally, not by convention

A "phase A then phase A.5 then phase B" comment is fragile. The discipline survives future refactors only if phase ordering is structurally visible — either:
- Single drainer function with explicit phase comments + sequential code blocks (current proposal)
- Helper functions named `Drainer_PhaseA_*`, `Drainer_ConsumerA5_*`, `Drainer_PhaseB_*` (explicit naming)
- A registry-driven phase walk: `FOREACH_DRAINER_PHASE(X)` X-macro with phase-id column (overkill for 2-3 phases; worthwhile for N-phase maker lifecycles)

### Bucket-based vs peek-based: pick by event-type ring structure

If result_queue is a SINGLE SPSC ring with mixed event types, **bucket-based (Option III) is cleaner** — one pass to sort; per-phase processing of stable buffers. Peek-based (Option II) requires peek-without-pop ring primitives which most SPSC implementations don't expose.

If result_queue is N separate SPSC rings per event type (or per source), **per-ring drain order (Option I) is cheapest** — no per-event branch needed.

### Consumer passes between phases must not write state used by next phase

The whole point of phase A.5 is to read state in CLOSE form before Phase B overwrites it. If Phase A.5 WRITES state that Phase B reads, you've inverted the dependency — Phase B's correctness now depends on Phase A.5's completion. Test for this with an explicit `state_E_at_phase_A_end == state_E_at_phase_A.5_start` assertion in tests.

### Latency budget verification

Multi-pass drain adds latency proportional to events per cycle × passes. Verify via bench gate (`oms_bench_enabled=1` from v5.15.5.C.3 Phase 7) that drainer p99 stays within slow-path 100μs budget. If maker-order lifecycle scales to 5+ phases, may need bench-driven optimization (sparse-phase skip; phase fusion for low-activity periods).

---

## Cross-references to CLAUDE.md

This pattern complements + reinforces:

- **Item 18 (slow-path latency priority):** prerequisite — phase split must not bloat the 100μs cycle. Bench gate is the verification mechanism.
- **Item 19 (structural fix preferred):** parent meta-pattern. Phase split is selected as the structural fix for the recurring "FillRecord-snapshot defensive class" once recurrence threshold (2) is met.
- **Item 28 (latency-vs-cache framework):** governs the cost-benefit analysis — phase split costs ~few μs in latency but saves ~hundreds of bytes + cache-miss reductions per drainer iter.

Promotion candidate to CLAUDE.md as item 32 (or later) after 2+ canonical applications shipped. First application = v5.15.5.C.4 Phase F + G. Second application likely emerges from v6.x maker-order work.

---

## Related design patterns

- **`structural-fix-preferred-decision-framework.md`** — meta-framework that picks this pattern via recurrence-count analysis (D2.C + D2.D = 2 recurrences of the snapshot-defensive class)
- **`aggressive-memory-reduction-techniques.md`** — Technique 4 (derive vs store) UNBLOCKS for previously-failed fields under phase discipline; add anti-pattern subsection pointing to this spec
- **`cache-layout-discipline-for-hot-side-structs.md`** — Rule 4 (HOT/WARM/COLD tiering) — phase split's payoff is FillRecord size reduction which improves cluster layout
- **`slot-state-foreach-registry-with-storage-routing.md`** — FOREACH_FILL_RECORD_FIELD registry shrinks after derive cascade; demonstrates registry-driven discipline coexisting with phase discipline
- **`bitmap-flag-api.md`** — close_mask + open_mask bitmaps (existing infrastructure) are the consumer-pass drivers; pattern reuses existing tools
- **`x-macro-registry-with-presence-dispatch.md`** — if scaling to N-phase maker lifecycle, a FOREACH_DRAINER_PHASE registry can drive the phase walk

---

**End of spec.**
