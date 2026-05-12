# Cross-thread snapshot-publish cluster isolation (alignas(64) clusters for live-state atomics read by snapshot publisher)

**Established:** 2026-05-12 (codification of an implicit isolation pattern; v5.15.5.B.2 first explicit reference application)
**Status:** ACTIVE
**Cross-references:**
- Sister: `per-snapshot-cluster-layout-pattern.md` (snapshot-side cluster layout; covers TUISnapshot/PerCoreSnap consumer side)
- Sister: `decision-first-cluster-layout-pattern.md` (intra-cluster ordering; this doc complements with cross-thread alignas axis)
- Parent rule: `cache-layout-discipline-for-hot-side-structs.md` Rule 3 (alignas isolate cross-thread)
- FoxML_Trader_v2 CLAUDE.md item 8 (TUI snapshot pattern — independent of engine)
- FoxML_Trader_v2 CLAUDE.md item 11 (SMT siblings + cache coherency)
- FoxML_Trader_v2 CLAUDE.md item 17 (latency tracking — false-sharing cost)
- FoxML_Trader_v2 latency-path-discipline.md Rule 7 (cross-thread synchronization)

---

## Problem statement

`per-snapshot-cluster-layout-pattern.md` (established v5.14.10.0) covers cluster layout on the SNAPSHOT-CONSUMER side (TUISnapshot / PerCoreSnap structs read by GUI thread). It captures fields by concern + applies alignas(64) cluster boundaries to prevent false-sharing on the SNAPSHOT struct.

There's a SISTER concern: the SNAPSHOT-PUBLISHER reads atomic fields from LIVE STATE structures (CoreContext, EventLoopState, OrderManagerState, ExecutionCore) at publish cadence. The publisher reads happen on a DIFFERENT THREAD from the slow-path writer of those atomic fields. **False-sharing risk:** if publisher-read atomics share a cache line with slow-path-written non-atomic fields, every publish-read INVALIDATES the writer's cache line; next slow-path write incurs a full cache-line bounce (~30-50ns penalty per ping-pong).

This is DISTINCT from snapshot-side clustering:
- Snapshot-side: layout of fields WITHIN TUISnapshot/PerCoreSnap (consumer-side cluster discipline)
- Live-state-side: ISOLATION of cross-thread-accessed atomic fields WITHIN long-lived live-state structures (writer-side cluster discipline)

`cache-layout-discipline-for-hot-side-structs.md` Rule 3 ("alignas isolate cross-thread") mentions the pattern in general but doesn't codify the specific LIVE-STATE-SIDE shape. This doc covers it.

---

## Design space explored

### Option A — Loose atomic fields scattered in struct (ANTI-PATTERN; pre-v5.15.5.B.2)

`CoreContext` had 4 `sp_*` atomics declared as loose fields (`std::atomic<uint64_t> sp_last_tick_us; std::atomic<uint64_t> sp_cycles_total; ...`) mixed in among slow-path-written non-atomic fields. False-sharing every snapshot publish.

REJECTED post-v5.15.5.B.2.

### Option B — Per-atomic alignas(64) field (over-padded)

```cpp
struct CoreContext {
    alignas(64) std::atomic<uint64_t> sp_last_tick_us;
    alignas(64) std::atomic<uint64_t> sp_cycles_total;
    alignas(64) std::atomic<uint64_t> sp_yield_count;
    alignas(64) std::atomic<uint8_t>  sp_state;
};
```

Each atomic gets its own 64B cache line. 4 atomics × 64B = 256B for ~25B of actual data. Wasteful.

REJECTED for clustered access cases.

Acceptable for a single atomic that's truly hot-contended cross-thread. For groups of related atomics read together at publish time, Option C (cluster) is correct.

### Option C — Clustered alignas(64) struct (CHOSEN)

```cpp
struct alignas(64) SlowPathTelemetry {
    std::atomic<uint64_t> last_tick_us;
    std::atomic<uint64_t> cycles_total;
    std::atomic<uint64_t> yield_count;
    std::atomic<uint8_t>  state;
    // ~25B used; rest = padding to 64B
};

struct CoreContext {
    // ... other fields ...
    SlowPathTelemetry sp_telemetry;
    // ... other fields ...
};
```

Cluster occupies single cache line (or contiguous lines). All sp_* atomics read together at publish (one cache line invalidated, one line bounced). Adjacent non-atomic fields outside the cluster are SAFE (different line).

CHOSEN. Pattern documented here.

### Option D — Pad-array between atomics + neighbors

```cpp
struct CoreContext {
    std::atomic<uint64_t> sp_last_tick_us;
    /* ... other atomics ... */
    char _pad_to_64[64 - 25];  // hand-rolled padding
    /* ... non-atomic fields ... */
};
```

Functional but cumbersome + brittle. Cluster struct (Option C) gives same protection with cleaner syntax + compile-time alignment guarantee.

REJECTED for new code; acceptable as historical pattern in pre-existing structs.

---

## The pattern (concrete shape)

### Step 1 — Identify cross-thread atomic clusters

For each live-state struct (CoreContext, EventLoopState, OrderManagerState, ExecutionCore), enumerate:
- Atomic fields written by one thread + read by another
- Group by "read-together" at publish cadence

Example for CoreContext sp_telemetry:
- `sp_last_tick_us` — slow-path writes at cycle end; publisher reads at snapshot publish
- `sp_cycles_total` — slow-path bumps per cycle; publisher reads at publish
- `sp_yield_count` — slow-path bumps on yield; publisher reads at publish
- `sp_state` — slow-path writes at state transitions; publisher reads at publish

All 4 read together at publish time. Group into single cluster.

Example for EventLoopState ws_telemetry:
- `last_ws_tick_us` — producer writes per tick; slow-path + GUI read
- `ws_ticks_per_5s` — producer writes per tick; slow-path + GUI read
- `ws_bucket_last_sec[5]` — producer writes per tick
- `ws_bucket_count[5]` — producer writes per tick

All accessed together at WS heartbeat publish. Group into single cluster.

### Step 2 — Define cluster struct with alignas(64)

```cpp
struct alignas(64) SlowPathTelemetry {
    std::atomic<uint64_t> last_tick_us;
    std::atomic<uint64_t> cycles_total;
    std::atomic<uint64_t> yield_count;
    std::atomic<uint8_t>  state;
    // Sizeof: 25B used; alignas(64) rounds total to 64B; ~39B trailing padding
};

struct alignas(64) WsHeartbeatTelemetry {
    std::atomic<uint64_t> last_tick_us;
    std::atomic<uint64_t> ticks_per_5s;
    uint64_t bucket_last_sec[5];      // producer-only writer; not atomic (no cross-thread READ?)
    uint32_t bucket_count[5];          // producer-only writer; not atomic
    // Sizeof: 76B used; alignas(64) rounds to 128B (2 cache lines); ~52B trailing padding
};
```

### Step 3 — Embed as single field in parent struct

```cpp
struct CoreContext {
    // ... HOT/WARM cluster fields ...

    // Cross-thread cluster isolation
    SlowPathTelemetry sp_telemetry;

    // ... COLD cluster fields ...
};
```

### Step 4 — Update consumers to access via cluster

Pattern: `ctx.sp_last_tick_us.load(...)` → `ctx.sp_telemetry.last_tick_us.load(...)`.

Migration scope: every read + write site of the previously-loose atomics. Use rg + careful site-by-site edits (NOT replace_all — member-access patterns can mangle per `feedback_avoid_substring_replace_all_on_member_access.md`).

### Step 5 — Static_assert cluster alignment

```cpp
static_assert(alignof(SlowPathTelemetry) == 64,
              "sp_telemetry cluster MUST be cache-line aligned for cross-thread isolation");
static_assert(sizeof(SlowPathTelemetry) % 64 == 0,
              "sp_telemetry sizeof MUST be 64-multiple for inter-instance non-overlap "
              "(if arrayed as cores[16].sp_telemetry)");
```

The second assert matters when the cluster appears within an array structure (e.g., `CoreContext cores[16]` means 16 separate sp_telemetry clusters; each MUST land on its own cache line).

### Step 6 — Document cross-thread access cadence

In the cluster struct's doc comment:

```cpp
//======================================================================================================
// [SLOW PATH TELEMETRY — cross-thread cluster isolation]
//
// Single-writer (per-core slow-path thread for this core's slot);
// Multi-reader (snapshot publisher running on GUI thread; also potentially controller
//   thread for cadence-drift display).
//
// Access cadence:
//   Writer: per slow-path cycle (~10K Hz at typical engine pacing)
//   Reader: per snapshot publish (~30 Hz GUI cadence)
//
// False-sharing prevention: alignas(64) isolates the cluster from neighbor slow-path-
// written non-atomic fields. Publisher's snapshot read invalidates THIS cluster's cache
// line but does NOT invalidate the writer's other state.
//
// See DESIGN_SPECS/cross-thread-snapshot-publish-cluster-isolation.md for pattern.
//======================================================================================================
```

---

## Cross-thread cache traffic analysis

For each cluster, characterize:

**Writer-side invalidation rate:**
- Writer cadence × cluster size in cache lines = MESI broadcasts per second

**Reader-side cache miss rate:**
- Reader cadence × cluster size in cache lines = cache misses per second on reader thread

**Example for sp_telemetry (single 64B cluster):**
- Writer: 10K cycles/sec × 1 line = 10K MESI broadcasts/sec/core
- Reader: 30 publishes/sec × 1 line = 30 cache misses/sec/core
- Combined cost: ~10K × 1 line cache-coherency traffic; ~30 × ~100ns reader misses = ~3 µs/sec/core wasted

**16 cores × sp_telemetry:** 16 × 3 µs/sec = ~50 µs/sec engine-wide of cross-thread coherency overhead. Modest but real; the isolation prevents this cost from spreading to NEIGHBOR FIELDS (which would multiply the cost by however many fields share the line).

If cluster cost > 1% of slow-path budget, audit cluster size + access cadence + consider further splits or sub-clustering.

---

## Reference applications (1 new + 0 prior explicit; 2 implicit precedents)

### v5.15.5.B.2 (first explicit) — `SlowPathTelemetry` cluster on CoreContext

**Surface:** `CoreFrameworks/ControllerEventLoop.hpp` post-v5.15.5.B.2

Pre-v5.15.5.B.2 state: 4 loose `sp_*` atomics scattered in CoreContext at lines 462-465. Snapshot publisher (EngineTUI.hpp:1839-1846) reads them via `__atomic_load_n(..., RELAXED)`. Adjacent non-atomic fields shared cache lines.

Post-v5.15.5.B.2: clustered into `SlowPathTelemetry sp_telemetry;` with alignas(64). Adjacent fields isolated.

### v5.15.5.B.2 (first explicit, second cluster) — `WsHeartbeatTelemetry` cluster on EventLoopState

**Surface:** `CoreFrameworks/ControllerEventLoop.hpp` EventLoopState post-v5.15.5.B.2

Pre-v5.15.5.B.2 state: 4 loose ws_* atomics + 2 arrays at EventLoopState lines 557-567. Producer fan-out writes per tick; slow-path + GUI read.

Post-v5.15.5.B.2: clustered into `WsHeartbeatTelemetry ws_telemetry;` with alignas(64).

### Implicit precedent 1 — `ParameterSlot<F>` seqlock (v5.11.3)

The seqlock pattern at `GateParameters.hpp` already isolates the seqlock's `sequence` atomic + FPN data block in a contiguous structure. Pattern is INTRA-STRUCT cross-thread isolation; this DESIGN_SPEC documents the LIVE-STATE-EMBEDDED-CLUSTER variant.

### Implicit precedent 2 — `ExecutionCore.permission` (v5.11.1.5)

The `permission` atomic was isolated to its own cache line via alignas(64) in v5.11.1.5 — single-field cluster isolation. This DESIGN_SPEC covers the multi-field cluster variant.

### Future candidate applications

- `OrderManagerState` (.C ship) — drainer's cross-thread atomic counters (fill events, kill state)
- `ExecutionCore` (.future) — hot-path-written atomics read by slow-path / drainer
- `MetricsLog` (TECH_DEBT-031) — multi-writer counter aggregation

---

## Trade-offs + when to apply

### Apply when:
- ≥ 2 atomics in a live-state struct, accessed cross-thread
- Atomics are read TOGETHER at publisher/reader cadence (clustered access)
- Adjacent struct fields are writer-only by a single thread (false-sharing concern)
- Writer cadence × adjacent-field count > publisher cadence (false-sharing dominates)

### Skip when:
- Single isolated atomic with no adjacent writer state (use per-atomic alignas(64) instead — Option B)
- All struct fields are read+written by same thread (no cross-thread concern; ordering matters not isolation)
- Cluster occupies > 4 cache lines (consider sub-clustering or extracting to separate struct)

### Cost:
- Per cluster: ~10 LOC cluster struct definition + ~5 LOC alignas/static_assert + N rewrites at access sites
- Memory: 64B - sizeof(atomics_packed) padding per cluster; acceptable

### Win:
- Cross-thread cache traffic LOCALIZED to cluster; doesn't propagate to neighbor writer-only fields
- ~100-300 ns saved per cross-thread access × cadence multiplier
- Pattern composable with `per-snapshot-cluster-layout-pattern.md` (consumer side) + `decision-first-cluster-layout-pattern.md` (intra-cluster ordering)
- Cluster doc captures cross-thread cadence + access pattern — discoverable

---

## Lessons / gotchas

### `alignof()` doesn't always equal `alignas(N)`

Compiler may align to LARGER than requested if a member needs it. `std::atomic<T>` may have natural alignment of `alignof(T)`. For `std::atomic<uint64_t>`, alignof is typically 8 — but the cluster's alignas(64) governs cluster-level alignment.

Verify with `static_assert(alignof(MyTelemetryCluster) == 64)` after declaration.

### Cluster's last member alignment matters for ARRAY layout

When cluster is embedded in an array (e.g., `cores[16].sp_telemetry`), each slot must START on a 64B boundary. C++ ABI: `sizeof(SlowPathTelemetry) % alignof(SlowPathTelemetry) == 0` enforced. So sizeof IS rounded up. But if cluster declaration doesn't use alignas(64), sizeof may be smaller than 64 → adjacent cluster slots could share cache lines.

Static_assert sizeof%64==0 + alignof==64 together catch this at compile time.

### atomic_load_n RELAXED vs ACQUIRE

Cluster isolation is about FALSE SHARING. Memory ordering is a separate concern.

For observability-only fields (sp_cycles_total, ws_ticks_per_5s — counters whose monotonicity doesn't synchronize OTHER data), RELAXED is correct. The cluster isolation doesn't depend on ordering.

For fields that synchronize OTHER data (e.g., a "result_ready" flag releasing a result struct), use ACQUIRE/RELEASE per CLAUDE.md item 18(c). Cluster isolation still applies independently.

### Cluster split when ≥ 2 cache lines

If a single cluster grows past 64B (e.g., ws_telemetry at 76B → 128B with alignas), consider whether two cache lines actually share access cadence. If line 1 (head) is HOT-read every publish + line 2 (tail) is COLD-read only on slow-path query, sub-cluster them with line 2 outside the alignas region.

For ws_telemetry specifically: keep clustered — both lines are written by producer + read together at publish. 128B = 2 lines OK.

### False-sharing detection via perf

`perf c2c` (Linux 4.10+) reports HITM (hits modified) events from cross-CPU cache-line bouncing. Use to verify cluster isolation worked. Pre-fix: high HITM count on the loose atomics. Post-fix: HITM count drops to ~0 within the cluster.

### Compatibility with seqlock readers

If cluster is itself a seqlock (write-side increments seqnum + writes data + increments again), the seqlock ALREADY isolates writes. Cluster alignas adds the cross-thread alignment guarantee for the COMBINED seqnum + data region.

---

## Audit detection (`/dod-audit` integration)

`/dod-audit` should flag MISSED applications by:

- **Symptom 1:** Struct contains `std::atomic<T>` field(s) AND adjacent non-atomic fields are written by single thread → potential false-sharing surface
- **Symptom 2:** `perf c2c` (if instrumented run available) shows HITM events on struct addresses → confirmed false-sharing
- **Symptom 3:** Struct has cross-thread atomics scattered (not clustered) AND multi-reader access pattern at consistent cadence → missed cluster opportunity
- **Symptom 4:** Cluster declared without alignas(64) OR static_assert(alignof==64) → enforcement gap

When detected → flag as `MISSED — cross-thread-snapshot-publish-cluster-isolation`. Recommended fix: extract cross-thread atomics into alignas(64) cluster struct.

---

## Patterns NOT used here (and why)

### `std::atomic<T>` per-field alignas(64)

Over-padded for cluster cases. Each atomic gets its own 64B → 4 atomics × 64B = 256B vs cluster's 64-128B. Acceptable for SINGLE atomics; wasteful for clusters.

### `volatile T` instead of `std::atomic<T>`

`volatile` is NOT a substitute for atomic across C/C++. Doesn't guarantee atomicity, memory ordering, or visibility. REJECTED for cross-thread fields. Use `std::atomic`.

### Hand-rolled `char _pad[N]` between atomics

Functional but error-prone. Cluster struct (Option C) gives compile-time guarantee + cleaner syntax. Acceptable for legacy code; new code uses cluster struct.

### Read-Copy-Update (RCU) for the cluster

RCU is for READ-mostly cross-thread structures with rare write epochs. The cluster pattern is WRITE-frequent + READ-occasional. RCU machinery is overkill. The simpler cluster + relaxed atomic loads pattern handles this case.

---

## Cross-references

- `per-snapshot-cluster-layout-pattern.md` (consumer-side: TUISnapshot/PerCoreSnap cluster layout; SISTER pattern)
- `decision-first-cluster-layout-pattern.md` (intra-cluster ordering; ORTHOGONAL axis to this doc's cross-thread isolation)
- `cache-layout-discipline-for-hot-side-structs.md` Rule 3 (parent rule: alignas isolate cross-thread)
- `bitmap-flag-api.md` (atomic_load BITMAP_ATOMIC_* variants used in observability clusters)
- `wire-format-byte-preservation-discipline.md` (different concern: serialization byte-equivalence)
- FoxML_Trader_v2 `CoreFrameworks/GateParameters.hpp` (ParameterSlot seqlock; implicit precedent 1)
- FoxML_Trader_v2 `CoreFrameworks/ExecutionCore.hpp` (`permission` atomic isolation; implicit precedent 2)
- FoxML_Trader_v2 `CoreFrameworks/ControllerEventLoop.hpp` post-v5.15.5.B.2 (sp_telemetry + ws_telemetry; first explicit references)
- FoxML_Trader_v2 CLAUDE.md items 8, 11, 17
- FoxML_Trader_v2 `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` Rule 7

## Promotion criteria (this doc was promoted)

Pattern field-validated 2× explicitly (sp_telemetry + ws_telemetry clusters in v5.15.5.B.2) + 2× implicitly (ParameterSlot seqlock + ExecutionCore permission isolation). Operator framing 2026-05-12: "structural fixes that close out entire classes of future bugs" — codified when audit (.B pre-coding) surfaced this as a recurring pattern needing explicit documentation.

Re-evaluate when 3rd-5th applications surface (likely .C / .D / .E sibling sweeps in v5.15.5 continuation; OrderManagerState drainer atomics expected to fit the pattern).
