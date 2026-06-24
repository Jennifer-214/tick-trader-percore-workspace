---
type: data-discipline
stage: 2-draft
version: 1.0
established: 2026-05-18
tags: [data-oriented-design, concurrency, latency-discipline]
surface: [hot-path, slow-path]
sister_specs: [concurrency-model-summary.md, multi-bit-state-encoding-pattern.md, bitmap-overflow-protection-discipline.md, register-spill-discipline.md]
applies_at_skills: [/hft-audit, /dod-audit, /blindspot-scan]
---

# Cache-line discipline (DOD codification)

**Established:** 2026-05-18 (v5.15.5.F.4d.1.B.3 doc-layer refresh — codify implicit DOD discipline)
**Status:** Stage 2 DRAFT v1.0 — full body matures at `.C` candidate ship

Codifies the implicit alignas / cache-line / false-sharing-prevention discipline currently scattered across H6 / DESIGN_PHILOSOPHY § 3 / inline code comments.

---

## Layout rules

**Cluster fields by access pattern (DOD core principle):**

1. **Hot reads** — fields read every tick on hot path; cluster together at struct start; ideally fits 1 cache line
2. **Hot writes** — fields written every tick; separate cache line from hot reads (prevent write-invalidates-read)
3. **Cold init** — boot-time-only fields; cluster at struct end; can sprawl
4. **Cross-thread** — fields written by one thread, read by another; `alignas(64)` padding to prevent false-sharing

**Default to alignas(64) for cross-thread structs** (H6).

---

## False-sharing prevention

When 2+ threads share a cache line:
- Thread A writes field X
- Thread B reads field Y (different field, same cache line)
- Cache line ping-pongs between cores; ~40-100ns invalidation cost per ping-pong
- Real cost in HFT: kills p99

**Discipline:**
- Producer-written fields: `alignas(64)` + padding to fill cache line
- Consumer-read fields: separate cache line
- Cross-thread atomic flags: each `alignas(64)`

**Worked example (SPSC ring):**

```cpp
struct alignas(64) SPSCRing_Producer_Cache_Line {
    uint64_t producer_head;  // written by producer
    uint8_t _pad[56];        // fill cache line
};

struct alignas(64) SPSCRing_Consumer_Cache_Line {
    uint64_t consumer_head;  // written by consumer
    uint8_t _pad[56];
};
```

---

## L1d working-set budget

**Hot path target:** ≤32-64KB L1d-resident (CPU L1d cache size typical).

**Per-node slow_state target:** ≤64KB (comfortable L1d + L2).

**Why:** hot loops touching out-of-L1d data hit L2 (3-4x slower) or L3 (10x slower) — kills p99. Cache-resident hot path is THE budget mechanism.

**Verification:**
- `perf stat -e L1-dcache-load-misses` during paper-test
- `pahole` reports struct sizes + alignment
- HOT_PATH_CHANGELOG entry required for any hot-path struct size increase

---

## Bit-packing ideal (sister discipline)

Multi-bit state encoding (MBS_*) packs K-state fields into N-bit slots over uint{8,16,32,64}_t storage. See `multi-bit-state-encoding-pattern.md`.

NEVER C++ bitfield syntax (`name : N`) — H14. Layout/signedness/packing-order implementation-defined; conflicts with H9/H10/H12 (wire byte preservation / SIMD parity / memcmp identity).

---

## SIMD parity considerations

AVX-512 SIMD kernels MUST have bytewise-identical scalar fallback (H10). Cache-line layout must support both:
- SIMD path operates on 64-byte aligned chunks (1 cache line = 1 AVX-512 register)
- Scalar path produces identical output bit-for-bit
- Test harness verifies bytewise identity

---

## Audit detection

`/hft-audit` + `/dod-audit` + `/blindspot-scan` (B6 alignment pillar) check:
- Cross-thread struct fields lack `alignas(64)` → finding
- Hot-read + hot-write fields share cache line → finding
- Hot-path working set exceeds L1d budget → finding (HOT_PATH_CHANGELOG measurement required)
- C++ bitfield syntax used → H14 violation
- SIMD kernel lacks scalar fallback → H10 violation

---

## Pattern lifecycle

- **Stage 1 (problem):** discipline implicit; scattered across H6 + DESIGN_PHILOSOPHY § 3
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-18 sketch)
- **Stage 3+ (first canonical / cohort / promotion):** matures at `.C`/`.D` ships — codify worked examples + cohort applications + CI tool for cache-line discipline verification

---

## Cross-references

- Sister: `concurrency-model-summary.md` (thread architecture; this spec is layout-level)
- Sister: `multi-bit-state-encoding-pattern.md` (bit-packing for K-state fields)
- Sister: `bitmap-overflow-protection-discipline.md` (BITMAP_* + static_assert)
- CLAUDE.md § Design philosophy (DOD core principle)
- CLAUDE.md § Memory budgets
- CLAUDE.md H6 (cross-thread alignment), H10 (SIMD parity), H14 (bitfield syntax forbidden)
- DESIGN_PHILOSOPHY.md § 3 (Data-oriented design family)

---

**End of cache-line-discipline v1.0 DRAFT.** Stage 3+ work matures at `.C`/`.D` candidate ships.
