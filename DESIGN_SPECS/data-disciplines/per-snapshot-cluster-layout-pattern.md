---
type: data-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-05-10
tags: [data-oriented-design, concurrency, latency-discipline]
surface: [slow-path, gui-thread]
sister_specs: [cache-layout-discipline-for-hot-side-structs.md, cache-line-discipline.md, decision-first-cluster-layout-pattern.md, cross-thread-snapshot-publish-cluster-isolation.md]
applies_at_skills: []
---

# Per-snapshot cluster layout pattern (alignas(64) clusters by concern)

**Established:** 2026-05-10 (v5.14.10.0 — first systematic application to PerCoreSnap bandit telemetry)
**Status:** ACTIVE
**Cross-references:**
- First application: `DataStream/EngineTUI.hpp:1188+` (PerCoreSnap bandit telemetry cluster)
- Sister pattern: `bitmap-flag-api.md` (often used WITHIN clusters for compact boolean state)
- Sister pattern: `heterogeneous-registry-pattern.md` (cluster-by-domain analog for cfg fields)
- TECH_DEBT-011 (PerCoreSnap layout discipline; substantially closed by this pattern)
- CLAUDE.md item 4 (data-oriented design: per-node arrays SoA for cache locality)
- CLAUDE.md item 12 (display↔execution invariant: snapshots are display surface)
- CLAUDE.md item 18 (slow-path latency reduction: cluster fields by access cadence)

---

## Problem statement

Cross-thread snapshot structs (`PerCoreSnap`, `TUISnapshot`, `MLSnapshot`, etc.) accumulate fields organically — each new feature appends fields at the end of the struct without considering cache layout. Over time:

- **Hidden false-sharing:** unrelated fields share a cache line; one field's writer invalidates the other field's reader, causing cross-thread cache misses
- **Wasted prefetches:** GUI render thread reads scattered fields from N different cache lines instead of one
- **Layout fragility:** when a new field lands "wherever convenient," its placement may break a hidden cluster boundary that previously worked
- **Cache-locality discussions repeat:** every new field triggers fresh "where should this go?" discussion

The standard remedies — `alignas(64)` per cluster + explicit cluster-boundary comments + compile-time offset asserts — are well-known but UNDERAPPLIED because no DESIGN_SPECS doc captures when/how to do it. New contributors don't know to apply the pattern; reviewers don't know to ask.

This doc captures the pattern + decision tree + audit detection.

---

## When does it apply? (Trigger conditions)

Apply this pattern when ALL of the following hold:

1. **Cross-thread access pattern** — struct is written by one thread (writer) and read by another (reader). Pure single-thread structs don't benefit from cluster boundaries.
2. **Mixed write cadence** — fields with DIFFERENT write frequencies share the struct. Same-cadence fields can pack freely; mixed-cadence fields need cluster separation.
3. **≥3 fields per concern** — a concern with 1-2 fields doesn't justify cluster overhead. For 3+ related fields, clustering saves cache lines + groups maintenance.
4. **Reader access locality** — a reader code path touches fields BY CONCERN (e.g., GUI panel renders bandit telemetry as one block; account panel renders P&L as one block). If reads are scattered across concerns, clustering helps less.
5. **Future expansion expected** — the concern will grow (more bandit fields, more risk fields). Clustering reserves headroom; ad-hoc placement fragments.

---

## The pattern (concrete shape)

### Step 1: Identify clusters by concern

Walk the struct field-by-field. Tag each field with its CONCERN:
- `BANDIT_TELEMETRY` — Exp3 weights, Thompson posterior, regime-arm matrix
- `ML_OBSERVABILITY` — predictions, confidence, drift counters
- `GATE_DIAGNOSTICS` — actual/threshold pairs for each gate predicate
- `SLOW_PATH_LATENCY` — per-cycle timing percentiles
- `ACCOUNT_PNL` — realized + fees + open notional + balance
- `RISK` — kill switch, drawdown, peak balance
- `ENGINE_TOPOLOGY` — CPU pinning, poll intervals
- `STRATEGY_STATE` — halt reasons, gate flags, strategy IDs
- (etc.)

Each concern is a CANDIDATE cluster.

### Step 2: Decide cluster boundaries

For each candidate cluster, decide whether to apply `alignas(64)`:

- **YES if:** ≥3 fields + cross-thread access + reader touches the cluster as a unit + future expansion expected
- **NO if:** <3 fields, or all fields share write cadence with adjacent (non-clustered) fields, or expected to remain stable

### Step 3: Apply alignas(64) at first field of each cluster

```cpp
// CLUSTER START — applied alignas(64) for cache-line boundary
alignas(64)
uint8_t  ensemble_active;          // first field of bandit telemetry
uint8_t  ensemble_n_horizons;      // ...
double   ensemble_weights[5][8];   // ...
// ... rest of cluster fields ...
```

The compiler inserts padding before the first field to align it to 64 bytes. The cluster occupies contiguous memory; trailing padding fills to next 64-byte boundary; subsequent cluster (or the next struct field) starts fresh.

### Step 4: Arrays-first reorder within cluster (optional)

When fields in a cluster have mixed alignment requirements (small u8 fields + large double[] arrays), placing arrays FIRST minimizes internal padding:

```cpp
// Less efficient (arrays-last; padding after small fields):
alignas(64)
uint8_t  flag1;        // 1B
uint8_t  flag2;        // 1B
                       // 6B padding for double[8] alignment
double   array_a[8];   // 64B
double   array_b[8];   // 64B

// More efficient (arrays-first; padding only at end):
alignas(64)
double   array_a[8];   // 64B
double   array_b[8];   // 64B
uint8_t  flag1;        // 1B
uint8_t  flag2;        // 1B
                       // 62B trailing padding to next 64B boundary
                       // (or absorbed by next cluster's alignas(64))
```

Both occupy the same cache lines (allocated bytes); arrays-first is cleaner. Apply when convenient; not strictly required.

### Step 5: Static_assert cluster boundary

```cpp
#include <stddef.h>  // for offsetof

static_assert(offsetof(EnclosingStruct::ClusteredStruct, first_cluster_field) % 64 == 0,
    "Cluster boundary must align to 64-byte cache line. "
    "Did a new field land before <first_cluster_field> without preserving alignas(64)?");
```

Catches future inadvertent layout drift at compile time. ZERO runtime cost.

### Step 6: Document via inline comment + DESIGN_SPECS reference

Above the cluster boundary, add a comment block:

```cpp
// v5.X.Y — <CLUSTER_NAME> CLUSTER BOUNDARY (alignas(64)).
// First/Nth application of per-snapshot-cluster-layout-pattern.md.
// Cluster starts here on a fresh cache-line boundary to prevent
// false-sharing with adjacent fields (cross-thread write cadence
// differs) and co-locate <N> fields for cache-warm reader access.
// Cluster span: ~XB (Y cache lines exact). Static_assert below
// enforces the boundary at compile time.
```

This makes the cluster discoverable by code search + future contributors understand WHY.

### Step 7: Update DESIGN_SPECS reference applications

Add the new application to this doc's "Reference applications" section. Each application = one row in the table at the bottom of this doc.

---

## Cluster size budgeting

Per-cluster size targets for cache-line efficiency:

| Cluster size | Cache lines | Comment |
|---|---|---|
| ≤ 64 B | 1 | Ideal for small clusters; reader fetches in one cache miss |
| 65-128 B | 2 | Acceptable; standard small cluster |
| 129-256 B | 3-4 | Medium cluster; common for ML telemetry surfaces |
| 257-512 B | 5-8 | Large cluster; consider whether sub-clustering is warranted |
| > 512 B | 9+ | Very large; SUB-CLUSTER candidate (e.g., split bandit by buy/exit) |

If a cluster grows past 512 bytes (~8 cache lines), audit whether it should split into 2 sub-clusters with separate alignas(64) markers. Boundary lives where the access pattern naturally separates.

---

## Cross-thread cache traffic analysis

For each cluster, characterize write/read cadence:

- **Writer cadence** — slow-path (10K Hz) / per-fill / boot-only / never (constant)
- **Reader cadence** — GUI render (60 Hz) / per-tick (rare for snapshots) / boot-only

Cluster cache cost per second:
- **Writer-side invalidations/sec:** writer cadence × cluster_lines (cache line invalidations broadcast to other cores via MESI)
- **Reader-side fetches/sec:** reader cadence × cluster_lines (cache misses on reader thread when reading after invalidation)

Example for v5.14.10.0 bandit telemetry cluster (8 lines after Thompson):
- Writer (slow path 10K Hz when active): 10,000 × 8 = 80,000 invalidations/sec/core
- Reader (GUI 60 Hz): 60 × 8 = 480 fetches/sec/core
- Combined cost: ~80K MESI broadcasts + ~480 cache misses per core ≈ negligible vs slow-path budget

If cluster cost > 1% of slow-path budget, audit cluster placement / split candidates.

---

## Trade-offs + when NOT to apply

### Skip when:
- Single-thread struct (no cross-thread coherency concern)
- ≤ 2 fields per concern (cluster overhead not justified)
- All fields share write cadence (no false-sharing risk)
- Reader accesses fields scattered across concerns (clustering doesn't help locality)
- Stable struct (no expansion expected; ad-hoc placement won't drift)

### Cost:
- ~20-30 LOC per cluster (alignas + comment + static_assert)
- Slight memory bloat from padding (typically < 64B per cluster)
- Cognitive overhead: developers must know the pattern + apply consistently

### Win:
- Eliminates false-sharing risk between clustered fields and adjacent fields
- GUI/reader render thread fetches cluster as one cache-warm sweep
- Future fields slot into cluster headroom (no fresh layout discussion)
- Static_assert catches inadvertent layout drift at compile time
- Documents architectural intent (cluster-by-concern is visible in code)

---

## Reference applications

| Application | Cluster | First field | Lines used | Doc ref |
|---|---|---|---|---|
| v5.14.10.0 | PerCoreSnap bandit telemetry | `ensemble_active` | 7 (8 after Thompson .D) | `DataStream/EngineTUI.hpp:1188+` |

(Future ships extending this pattern: append rows here.)

---

## Future application candidates

For TECH_DEBT-011 substantial close, the v5.14.10.0 ship establishes the pattern + first application. Remaining candidate clusters in PerCoreSnap (deferred to future ships):

| Candidate cluster | Concern | Field count | Lines used | Notes |
|---|---|---|---|---|
| ML observability | predictions + confidence + drift | ~12 | ~3-4 | Mixed types; medium priority |
| Gate diagnostics | actual/threshold pairs | 12 | 2 | Tight cluster; LOW priority (already mostly contiguous) |
| Slow-path latency | per-cycle percentiles | 7 | 1 | Tight; LOW priority |
| Account P&L | realized + fees + balance | 8 | 2 | Read by Account panel; medium priority |
| Risk | kill switch + drawdown | 4 | 1 | Read by Risk panel; LOW priority (already small) |
| Engine topology | CPU pinning + poll | 3 | <1 | Boot-frozen; SKIP (no cross-thread benefit) |

Each candidate ships as its own focused refactor sub-tag when triggered (e.g., next time that panel is significantly modified).

---

## Lessons / gotchas

### Compiler may insert MORE padding than expected

`alignas(64)` guarantees the field starts at a 64-byte boundary; the compiler may insert up to 63 bytes of padding before it. If the struct is large + memory-sensitive, audit total struct size after applying alignas — savings from cluster grouping must outweigh padding cost.

### Nested structs need fully-qualified offsetof

For nested struct field offsets:
```cpp
static_assert(offsetof(EnclosingStruct::NestedStruct, field) % 64 == 0, "...");
```

If `NestedStruct` is a member of `EnclosingStruct`, the offsetof inside `NestedStruct` is RELATIVE to `NestedStruct`'s start, NOT `EnclosingStruct`'s start. The cache-line alignment is preserved as long as the enclosing struct is itself aligned to 64+ bytes (typical for top-level struct types).

### Static_assert location: outside the struct

In C++17, `offsetof` requires standard-layout types and must be at namespace/file scope, not inside the struct definition. Place the static_assert after the struct's closing brace.

### The pattern is for CLUSTERS, not individual fields

Don't `alignas(64)` every field — that wastes massive memory (each field gets 64-byte slot). Apply once per CLUSTER (group of related fields).

### Default cache line size

Modern x86_64: 64 bytes. ARM Cortex-A series: 64-128 bytes (architecture-dependent). For HFT trading on x86, 64-byte cache line is the safe default. If targeting ARM/Apple Silicon, audit `__cpp_lib_hardware_interference_size` (C++17 stdlib) for portable cache-line size.

### Updating an existing cluster: extend, don't fragment

When adding a new field to an EXISTING cluster, place it WITHIN the cluster (between alignas(64) boundary and next cluster). Don't append at end of struct — that defeats the cluster purpose. Cluster headroom is reserved for this.

---

## Audit detection

`/dod-audit` flags missed applications by:

- Symptom: cross-thread snapshot struct with ≥3 related fields lacking `alignas(64)` cluster boundary
- Symptom: snapshot struct that has GROWN past N fields without any alignas markers (likely ad-hoc layout)
- Symptom: slow-path writer hot in profiler accessing a snapshot struct + GUI reader hot in cache-miss profile on the same struct (false-sharing signature)

When detected → flag as `MISSED — per-snapshot-cluster-layout-pattern`. Recommended fix: apply pattern Steps 1-7.

---

## Cross-references

- `bitmap-flag-api.md` — often used WITHIN clusters for compact boolean state
- `heterogeneous-registry-pattern.md` — cluster-by-domain analog for cfg fields
- `wire-format-byte-preservation-discipline.md` — separate concern (serialization layout, not in-memory layout)
- `hot-side-array-element-alignment-for-sparse-access.md` (v5.15.5.C.5; **sister mechanism**: this spec is CROSS-THREAD alignas (false-sharing prevention for snapshot fields); sister spec is SINGLE-THREAD alignas (per-element cache-line alignment for sparse hot-path array access). Same `alignas(64)` mechanism, different motivations. v5.15.5.C.5 retroactively documents PerCoreSnap as a canonical application of one or both specs.)
- FoxML_Trader_v2 `CLAUDE.md` items 4, 12, 17, 18
- FoxML_Trader_v2 `DOCS/TECH_DEBT.md` TECH_DEBT-011 (substantially closed by v5.14.10.0)
- FoxML_Trader_v2 `DataStream/EngineTUI.hpp:1188+` — first reference application
- v5.14.9.B postmortem (CLAUDE.md item 12 + TECH_DEBT-011 codification)
