---
type: concurrency-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-13
tags: [concurrency, data-oriented-design, latency-discipline]
surface: [hot-path, oms-drainer]
sister_specs: [cache-layout-discipline-for-hot-side-structs.md, cache-line-discipline.md, cross-thread-snapshot-publish-cluster-isolation.md, raii-destructor-with-cluster-reorg-interaction.md]
applies_at_skills: []
---

# SPSC ring embedded in hot struct — cluster discipline (preventing the "ring head shares a line with the preceding field" gotcha)

**Established:** 2026-05-13 (codification triggered by v5.15.5.C.1 audit of `OrderManagerState` — first hot-side struct in this codebase that embeds N `SPSCRing<T, K>` fields and required cluster discipline beyond the ring's internal alignas)
**Status:** ACTIVE
**Cross-references:**
- Parent rule: `cross-thread-snapshot-publish-cluster-isolation.md` (ND1; this doc is the "embedded-field" specialization)
- Sister: `cache-layout-discipline-for-hot-side-structs.md` Rule 3 (alignas isolation for cross-thread shared fields)
- FoxML_Trader_v2 `CoreFrameworks/SPSCRing.hpp` (the ring implementation; alignas(64) on head + tail internally)
- FoxML_Trader_v2 `CoreFrameworks/OrderManager.hpp` (canonical first reference; 3 + N embedded rings)

---

## Problem statement

`SPSCRing<T, K>` (`CoreFrameworks/SPSCRing.hpp`) is a lock-free single-producer single-consumer ring. Its internals look like:

```cpp
template <typename T, size_t K> struct SPSCRing {
    alignas(64) std::atomic<size_t> head;   // producer-write, consumer-read
    alignas(64) std::atomic<size_t> tail;   // consumer-write, producer-read
    T buf[K];
};
```

The internal `alignas(64)` on `head` + `tail` ensures the producer-write line + consumer-write line don't share a cache line (prevents producer↔consumer false-sharing). This is the canonical RFO-storm prevention for the lock-free protocol.

**But.** When `SPSCRing` is embedded as a FIELD in an enclosing struct, the `head` member's `alignas(64)` only applies WITHIN the ring's layout. It does NOT prevent the ring's `head` cache line from being SHARED with the PRECEDING field in the enclosing struct.

Specifically: if `OrderManagerState` has

```cpp
struct OrderManagerState {
    SomePreviousField prev;          // ends at offset X
    SPSCRing<Cmd, 256> result_queue; // SPSCRing layout has alignas(64) on its first field (head)
    // ...
};
```

then the C++ compiler will pad `prev`'s end up to the next 64-byte boundary BEFORE laying out `result_queue` (because the ring's alignas(64) requirement propagates to the ring's location in the enclosing struct). So `prev`'s tail bytes + the padding before `result_queue` may share a cache line, but `result_queue.head` ITSELF starts at a 64-byte boundary.

So far so good. **The actual gotcha:**

If `prev` is a CROSS-THREAD shared field (e.g., another atomic written by a different thread than the ring's producer), then the line containing `prev`'s tail bytes still suffers cross-thread invalidation. The ring's head is on a CLEAN line (no neighbor) but `prev`'s tail line bounces. The cross-thread pattern leaks through the boundary.

More subtly: if `prev` is a NON-ATOMIC HOT field (e.g., `uint8_t event_log_mode` set once at init, read every drain), then `prev`'s line is read by ONE thread (drainer) → consistent. But if `prev` is a counter incremented by N slow-paths via CAS (e.g., `flatten_pending`), then `prev`'s line bounces under multi-thread contention even though `result_queue.head` is on its own line.

The fix: make the CLUSTER discipline EXPLICIT at the ENCLOSING struct level — wrap each cross-thread-sensitive group of fields in its own `alignas(64) struct {...}` cluster. Don't rely on the embedded ring's internal alignas to protect neighboring fields.

---

## The pattern

### Rule 1: `alignas(64)` on the ring at the enclosing struct level

Declare each embedded SPSCRing with explicit `alignas(64)`:

```cpp
struct OrderManagerState {
    // ... HOT fields ...
    alignas(64) SPSCRing<Command, 256> result_queue;
    alignas(64) SPSCRing<Command, 256> ws_result_queue;
    alignas(64) SPSCRing<Command, 256> reconcile_queue;
    alignas(64) SPSCRing<SubmitCommand, 32> submit_queues[16];
    // ... more HOT fields ...
};
```

This is redundant with the ring's internal alignas — but it's documentation: "the ring starts at a new cache line; the PRECEDING field's tail doesn't share with the ring's head."

### Rule 2: cluster cross-thread atomics that AREN'T inside SPSCRings into their own alignas(64) struct

If the enclosing struct has cross-thread atomics that are NOT part of an SPSCRing protocol (e.g., observability counters, safety CAS flags), wrap them in their own alignas(64) cluster — same pattern as ND1 (`cross-thread-snapshot-publish-cluster-isolation.md`).

```cpp
struct OrderManagerState {
    // ... SPSCRings (each alignas(64)) ...

    alignas(64) struct OmsObservabilityCounters {
        std::atomic<uint64_t> total_submitted;
        std::atomic<uint64_t> total_filled;
        std::atomic<uint64_t> total_rejected;
    } obs;

    alignas(64) struct OmsSafetyCAS {
        std::atomic<uint64_t> flatten_pending;
        std::atomic<uint64_t> recovery_until_us;
    } safety;

    // ... rest of struct ...
};
```

Don't co-locate observability counters with safety CAS — they're cross-thread to DIFFERENT thread sets (publisher reads obs at 60 Hz from snapshot thread; safety CAS is contended across N slow-path threads). Separate clusters prevent reader-X invalidating writer-Y's line.

### Rule 3: static_assert(offsetof) lock at the enclosing struct level

```cpp
static_assert(offsetof(OrderManagerState<64>, result_queue) % 64 == 0,
              "OMS result_queue MUST start at 64-byte boundary "
              "(prevents preceding field's tail from sharing the line; "
              "see spsc-ring-embedded-in-hot-struct-cluster-discipline.md)");
static_assert(offsetof(OrderManagerState<64>, obs) % 64 == 0,
              "OMS observability cluster MUST be cache-line aligned "
              "(snapshot publisher cross-thread reads; ND1 isolation)");
static_assert(offsetof(OrderManagerState<64>, safety) % 64 == 0,
              "OMS safety CAS cluster MUST be cache-line aligned "
              "(N-slow-path-thread CAS contention; ND1 isolation)");
```

These compile-time asserts catch future field-insertion that would silently break alignment.

### Rule 4: SPSCRing buffer storage doesn't need separate alignas (the rings handle their own)

The buffer (`T buf[K]`) inside SPSCRing is INTERNAL to the ring's layout. No need for the enclosing struct to add `alignas(64)` on the rings' BUFFER fields — that's not exposed at the enclosing struct level.

---

## Worked example — `OrderManagerState` v5.15.5.C.1

`OrderManagerState<F>` embeds:
- 3 result/ws_result/reconcile SPSCRings (drainer-only consumer side; producer is OrderManager_Submit caller — drainer thread itself in the funneled-submit invariant)
- N (=16) per-core submit_queues SPSCRings (per-core producer = slow-path thread for core N; consumer = drainer thread)

Pre-`.C.1` layout (`OrderManager.hpp:152-418`):
- The 3 result rings sit at lines 171-193 with NO explicit `alignas(64)` on their declarations. Pre-fields: `orders[16]` (4480 B; ends at offset 4480 + 0 = 4480; 4480 % 64 = 0 — accidentally aligned).
- The per-core submit_queues at line 296 has implicit alignas via SPSCRing's internal but the preceding field is `_pad_pe[7]` (alignment padding).
- Cross-thread atomics scattered: `total_submitted/filled/rejected` at lines 370-372 sit between `event_log`'s end and `last_seen_trade_id` (boot scalar). `flatten_pending` + `recovery_until_us` at lines 337-344 sit between `kill_switch_tripped` (non-atomic) and `trade_log` (cold pointer).

`.C.1` reorg (per this pattern):
```cpp
struct OrderManagerState {
    // ─────────── HOT cluster ───────────
    Order<F> orders[16];
    alignas(64) SPSCRing<Command, 256>     result_queue;
    alignas(64) SPSCRing<Command, 256>     ws_result_queue;
    alignas(64) SPSCRing<Command, 256>     reconcile_queue;
    alignas(64) SPSCRing<SubmitCommand, 32> submit_queues[16];
    int event_log_mode;
    OrderEventLog<F> event_log;

    // ─────────── WARM cluster ───────────
    alignas(64) Portfolio<F> portfolio;
    FPN<F> balance;
    // ... etc ...

    // ─────────── COLD cluster ───────────
    alignas(64) ExchangeAdapter<F> adapter;
    int live_trading;
    // ... etc ...

    // ─────────── Cross-thread CSAS clusters ───────────
    alignas(64) struct OmsObservabilityCounters {
        std::atomic<uint64_t> total_submitted{0};
        std::atomic<uint64_t> total_filled{0};
        std::atomic<uint64_t> total_rejected{0};
    } obs;

    alignas(64) struct OmsSafetyCAS {
        std::atomic<uint64_t> flatten_pending{0};
        std::atomic<uint64_t> recovery_until_us{0};
    } safety;

    ~OrderManagerState() { OrderManager_Shutdown(this); }
};

static_assert(offsetof(OrderManagerState<64>, result_queue) % 64 == 0, "...");
static_assert(offsetof(OrderManagerState<64>, obs) % 64 == 0, "...");
static_assert(offsetof(OrderManagerState<64>, safety) % 64 == 0, "...");
```

Result: every embedded SPSCRing starts at a 64-byte boundary independent of the preceding field's size. Observability + safety clusters each occupy their own cache line.

---

## Trade-offs + when to apply

### Apply when:
- A struct embeds 2+ SPSCRing fields
- The struct has cross-thread atomics that are NOT inside SPSCRings (observability counters, safety CAS flags)
- The struct's enclosing access pattern crosses thread boundaries (publisher reads at one cadence, drainer/producer writes at another)

### Skip when:
- Single SPSCRing embedded + no other cross-thread fields → ring's internal alignas is sufficient
- Stack-local SPSCRings (no enclosing struct concern)

### Cost:
- ~3-5 LOC per ring (alignas decoration + static_assert)
- One additional cluster struct per cross-thread atomic group (~5-10 LOC for the cluster + members)
- Compile-time enforcement of offsetof — zero runtime cost

### Win:
- Prevents the silent "preceding field's tail invalidates ring's head line" gotcha at compile time
- Clearer documentation of cross-thread access patterns at the struct definition level
- Future field-insertion can't accidentally break ring alignment (static_assert catches)
- Pairs with ND1 (`cross-thread-snapshot-publish-cluster-isolation.md`) for full cross-thread cluster discipline

---

## Lessons / gotchas

### The compiler WILL pad

Even without explicit alignas at the enclosing struct level, the compiler pads to honor the embedded type's alignas requirement. So `result_queue.head` will start at a 64-byte boundary regardless. The risk is NOT misalignment of the ring — the risk is that the PRECEDING field's tail bytes share a cache line with neighboring data structures (which they might do anyway via the implicit padding).

The explicit `alignas(64)` on the embedded SPSCRing field is DOCUMENTATION + INTENT signal. It makes the layout explicit so future maintainers don't break it.

### Don't double-pad

Adding `alignas(64)` twice (once on the enclosing field declaration AND inside the embedded type) doesn't double the padding — it just requests the same alignment. Idempotent. So adding explicit alignas at the enclosing struct level is safe even though SPSCRing already has it internally.

### Per-core submit_queues array

When `SPSCRing<T, K> submit_queues[16]`, each element of the array is alignas(64) (since the array's element type carries the alignment). Each `submit_queues[i].head` is on its own cache line. **But** the LAST element's `submit_queues[15].buf[K-1]` may share its tail bytes with the field AFTER the array — which is fine for HOT-cluster discipline but worth noting if that subsequent field is cross-thread sensitive.

For `.C.1`: the field after `submit_queues[16]` is `event_log_mode` (boot-set int) → no cross-thread concern.

### Co-locating SPSCRings for cache-line packing

Since each SPSCRing's internal layout is `alignas(64) head + alignas(64) tail + buf[]`, two SPSCRings adjacent in memory will have: ring0_head | ring0_tail | ring0_buf | ring1_head | ring1_tail | ring1_buf. No sharing — each ring's head/tail are on their own lines. Good.

### The `K` parameter affects total ring size

`SPSCRing<Command, 256>` with `sizeof(Command) = 64` is 64*256 = 16384 B (=256 cache lines) per ring. 3 such rings = 49152 B + 6 head/tail lines = ~49 KB total. This is HOT-cluster footprint per OMS. Compared to L2 (1.25 MB), it's fine — but worth tracking in the layout-fingerprint probe.

### Snapshot publisher reads observability counters at 60 Hz

`OmsObservabilityCounters` is read by `ShardedSnapshot.hpp` (lines ~96-105 pre-`.C.1`). With its own alignas(64) cluster, publisher reads invalidate ONLY that cluster's line — drainer's writes to fees/counters in WARM cluster are unaffected. Validated for `.B.2`'s SlowPathTelemetry; same pattern.

---

## Audit detection (`/dod-audit` integration)

`/dod-audit` should flag MISSED applications when it detects:

- **Symptom 1:** A struct with 2+ embedded SPSCRing fields without explicit `alignas(64)` on each at the enclosing struct level.
- **Symptom 2:** Cross-thread atomic fields in the same struct as SPSCRings, NOT clustered into their own `alignas(64) struct {...}` (per ND1).
- **Symptom 3:** No `static_assert(offsetof)` cluster anchor on the ring positions.

When detected → flag as `MISSED — spsc-ring-embedded-cluster-discipline`.

---

## Cross-references

- `cross-thread-snapshot-publish-cluster-isolation.md` (ND1 — parent pattern for cross-thread cluster isolation; this doc specializes for the SPSCRing-embedded case)
- `cache-layout-discipline-for-hot-side-structs.md` Rule 3 (alignas isolation for cross-thread shared fields)
- `raii-destructor-with-cluster-reorg-interaction.md` (sister; how to reorganize a struct with a RAII destructor — applies to OrderManagerState)
- FoxML_Trader_v2 `CoreFrameworks/SPSCRing.hpp` (ring implementation)
- FoxML_Trader_v2 `CoreFrameworks/OrderManager.hpp` (canonical first reference; 3+N embedded rings + 2 cross-thread atomic clusters)

## Promotion criteria (this doc was promoted)

Pattern triggered by `.C.1` pre-coding audit (2026-05-13). OrderManagerState is the first struct in this codebase that embeds multiple SPSCRings + has additional cross-thread atomics outside the rings — requiring the explicit "ring + atomic cluster discipline at enclosing struct level" pattern beyond the ring's internal alignas.

Future candidates: any new IPC-heavy struct (e.g., a future inter-process shared-memory wrapper for v6.0 colo work; a multi-stream depth aggregator that uses N SPSCRings for ws-stream fan-in).

Re-evaluate when a 2nd application surfaces.
