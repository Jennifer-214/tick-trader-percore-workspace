---
type: refactor-pattern
stage: 5-claude-md
version: 1.0
established: 2026-05-12
tags: [latency-discipline, data-oriented-design]
surface: [hot-path, slow-path]
sister_specs: [cache-layout-discipline-for-hot-side-structs.md, cache-line-discipline.md, decision-first-cluster-layout-pattern.md, branchless-dispatch-discipline.md]
applies_at_skills: []
---

# Latency-vs-Cache Decision Framework

**Status:** generalized engineering principle (formalized 2026-05-12
during v5.15.5 cache-layout audit; promoted to CLAUDE.md item 28).
**CLAUDE.md cross-ref:** items 7 (memory hierarchy), 17 (latency
tracking), 18 (slow-path branch minimization), 26 (branchless math
kernel), 28 (this principle).

## Problem

Performance optimizations frequently present trade-offs between:
- Cycle count (CPU instructions executed)
- Cache line fetches (L1 misses → L2 → L3 → DRAM)
- Branch density (predictable vs data-dependent branches)
- Storage footprint (cache occupancy + L1 pressure)

Without an explicit decision framework, optimizations get evaluated
on cycle count alone (the most visible metric). This leads to choices
that minimize cycles at the cost of cache misses — net SLOWER in
practice because cache miss cost is 75-100× cycle cost.

## Cost reference (3 GHz x86 CPU, modern Intel/AMD)

| Operation | Cycles | ns | Cost ratio (vs cycle) |
|---|---|---|---|
| CPU cycle | 1 | ~0.3 | 1× (baseline) |
| L1 D-cache hit | 4 | ~1.0 | 3× |
| L2 cache hit | 12 | ~4.0 | 12× |
| L3 cache hit | 40 | ~13 | 40× |
| **DRAM (L1 miss, cold cache)** | **300+** | **~100** | **~100×** |
| Branch mispredict | 10-15 | ~3-5 | 10-15× |
| AVX-512 FMA | 4-5 | ~1.5 | 4-5× |
| AVX-512 permute | 3 | ~1.0 | 3× |
| AVX-512 gather (strided) | 20-40 | ~7-13 | 20-40× |
| Atomic load (uncontended) | 5-7 | ~2 | 5-7× |
| Atomic load (contended, cross-core) | 100-200 | ~30-60 | 100-200× |

Numbers are approximate; actual values depend on CPU generation,
contention, memory bandwidth saturation, NUMA topology. The ORDER
of magnitude is what matters for design decisions.

## Decision rules

### Rule 1 — Prefer cycles over cache misses

When two approaches differ in cycle count AND cache miss count:

```
Approach A: +N cycles, saves M cache misses (vs B)
Approach B: -N cycles, +M cache misses

A wins if:  M × 100ns > N × 0.3ns
Equivalently:  M > N / 300
```

**Quick test:** if your "more cycles" approach saves even ONE cache
miss per 300 cycles added, it wins. Most realistic trade-offs are
far inside this margin.

**Worked example 1 — AoS vs SoA for per-arm barriers:**
- AoS (struct{tp,sl}[8]): +4 AVX cycles for permute, saves 1 cache line
- SoA double[8] separate: -4 cycles, +1 cache line per DOMINANT lookup
- AoS wins: 1 saved miss × 100ns = 100ns; 4 cycles cost = 1.3ns
- Net: 98.7ns saved per access (75× win)

**Worked example 2 — algorithm choice (constant-iter vs variable-iter):**
- Constant-iter inner loop (CLAUDE.md item 26): always 8 iterations
  even when only 4 arms loaded; +4 wasted cycles per cycle
- Variable-iter with `if (i < n_arms)` guard: 1 branch per iteration;
  ~1-2% mispredict rate (boundary; predictable)
- Constant-iter wins on:
  - Branchless behavior (deterministic timing)
  - Bytewise determinism for AVX-512 byte-locked kernels (item 25)
  - The +4 cycles is ~1.3 ns; mispredict overhead with even 1% rate
    is ~0.05 ns/cycle — but mispredict variance matters more than
    average for tail latency
- Net: constant-iter is preferred for slow-path budgets that target
  p99 (not just average)

### Rule 2 — Prefer branchless over data-dependent branches

When two approaches differ in branch count AND have data-dependent
condition values:

```
Branchless A: +N cycles unconditional (computes both paths via mask-select)
Branchy B: 1 branch, M% mispredict rate

A wins if:  M × 5ns > N × 0.3ns
Equivalently:  M > N / 16
```

**Quick test:** if your branchless approach adds fewer than 16 cycles
per branch eliminated, AND the branch is data-dependent (>5% mispredict),
branchless wins.

**Worked example 3 — mode dispatch via MODE_FLAGS[] lookup:**
- Branchy: nested if/else on `mode` enum; 5 branches per dispatch
  - Branch predictor learns the operator's mode preference quickly;
    mispredict rate <1% (mode rarely changes)
  - 0 mispredict cost in steady state; only on mode change (~0% of
    cycles)
- Branchless: `flags = MODE_FLAGS[mode]; bool_a = flags & MASK_A;` etc
  - 1 table load (~1 cycle if L1 hit) + N mask ANDs
  - ~5 cycles vs ~1 cycle for branchy steady state
- Verdict: **branchy STAYS for predictable enums**; branchless wins
  for data-dependent conditions

**Worked example 4 — argmax over weights:**
- Branchless argmax: `is_greater = (w[i] > max_w); max_w = is_greater ? w[i] : max_w;`
  - 2 cmov instructions per iteration; deterministic
- Branchy argmax: `if (w[i] > max_w) { max_w = w[i]; max_idx = i; }`
  - Data-dependent branch; mispredict rate ~50% (Bernoulli-like with
    bandit-converged weights)
- Branchless wins: 2 cycles × 8 iter = 16 cycles ≈ 5 ns
  vs branchy: 8 iter × 5 ns mispredict expected = 40 ns

### Rule 3 — When predictable branches stay (don't force branchless)

Branchless is NOT always better. Keep branches when:

- **Predictor learns the pattern:** boot-only conditions, mode flags
  set once at init, cfg-toggleable flags that rarely change. Mispredict
  rate <5% → branchless overhead not worth it.
- **Branch gates EXPENSIVE work:** if branch=true triggers a 10ms
  XGBoost predict, branching to SKIP the predict is correct.
  Branchless would compute then discard = waste of 10ms.
- **Branch is at the level of broad-control-flow:** function-entry
  early-returns, recovery paths, kill-switch paths — these have
  near-perfect prediction + their branches gate large work.

### Rule 4 — Storage vs cache pressure trade-off

When two layouts differ in storage size:
- Smaller layout: less L1 pressure, fewer competing evictions
- Larger layout: more L1 pressure but possibly better SIMD alignment

```
Approach A: -K bytes, +P cache misses on UNRELATED data (eviction)
Approach B: +K bytes baseline

A wins if:  P × 100ns > 0
(always true — fewer evictions is always positive)
```

**Quick test:** if your "smaller" option doesn't lose anything else
(equivalent cycles, equivalent access patterns), smaller wins on
L1 pressure alone.

### Rule 5 — SIMD vs scalar with cache constraint

SIMD (AVX-512) typically requires aligned, contiguous data for 1-cycle
throughput. If the alignment forces an extra cache line vs scalar
layout:

```
SIMD: -K cycles per operation, +L cache misses per access
Scalar: +K cycles, no extra cache miss

Scalar wins if:  L × 100ns > K × 0.3ns
Equivalently:  L > K / 300
```

For 8-wide AVX-512 FMA (savings ~8-12 cycles vs scalar), 1 extra
cache miss = breakeven at ~33 cycles savings. So SIMD only wins
when the cache penalty stays <1 line OR the savings >>30 cycles.

**Worked example 5 — AVX-512 BLEND for per-arm barriers:**
- AVX-512 (with AoS layout): 1 cache line + 12 cycles ≈ 100 + 4 = 104 ns
- Scalar (with AoS layout): 1 cache line + 30 cycles ≈ 100 + 10 = 110 ns
- AVX wins by ~6 ns per call; tiny but consistent
- If layout forced 2 cache lines for AVX vs 1 for scalar, scalar
  would win

## When to apply this framework

### At plan time
- Cache-layout audit decisions
- SIMD vs scalar choices
- Algorithm selection (constant-iter vs variable-iter)
- Branch-density audits per Rule 8 of cache-layout-discipline.md

### At code review time
- "Could this be branchless?" → apply Rule 2 + Rule 3 to decide
- "Should this be cache-aligned?" → apply Rule 1 + Rule 4
- "Is the cycle cost worth it?" → use the cost tables above

### At profiling time
- `perf stat -e L1-dcache-load-misses,branch-misses` measures actual
- Use measured numbers to refine framework estimates
- Realistic ratios may differ from rules-of-thumb on specific hardware

## Cross-references

- `CLAUDE.md` items 7, 17, 18, 26, 28
- `DESIGN_SPECS/data-disciplines/cache-layout-discipline-for-hot-side-structs.md`
  (Rules 1-8 apply this framework to struct layout)
- `DESIGN_SPECS/refactor-patterns/branchless-math-kernel-pattern.md` (constant-iter
  pattern applies Rule 1)
- `DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md` (SIMD vs scalar
  decisions apply Rule 5)
- `STRATEGY_AND_CODING_RULES.md` items 4, 7 (foundational invariants
  this framework operationalizes)

## Anti-patterns this framework catches

- "Cycle-counting microoptimization" that ignores cache layout
- "Branchless everything" that adds cycles where branches are
  perfectly predicted
- "Pack the struct as small as possible" that creates strided access
  patterns hurting cache utilization
- "Vectorize everything" that adds cache line fetches to enable SIMD
  on data that doesn't justify it

## Memory bandwidth costs (added 2026-05-13 post v5.15.5.B.8)

The cost table above (cycles vs cache lines) focuses on LATENCY per
access. There's a complementary axis: **bandwidth** — the rate at
which the memory subsystem can serve cache-line fills across all
threads + cores + DMA + GPU.

| Resource (Tiger Lake reference) | Peak rate | Cost per cache line (64 B) |
|---|---|---|
| L1d cache (per core) | ~48 KB | ~1 ns |
| L2 cache (per core) | ~1.25 MB | ~4 ns |
| L3 cache (shared) | ~12 MB | ~13 ns |
| **DRAM (shared)** | **~50-100 GB/s peak; shared across cores + GPU + iGPU** | **~100 ns** |

**The trap: DRAM bandwidth is shared.** A workload that consumes 26 MB/s
on its own looks tiny against ~50 GB/s peak. But concurrent loads add up:

- Producer fan-out on saturated markets: ~80 MB/s
- Per-core slow-path rolling-window updates: ~5-10 MB/s × 16 cores = 80-160 MB/s
- ML inference (when active): ~50-100 MB/s on feature pack + model read
- GUI snapshot publisher: ~6-26 MB/s depending on consolidation

Sum of concurrent workloads can approach 200-400 MB/s on busy markets.
At that point, threads STALL waiting for DRAM cycles — even ones that
"should" be CPU-bound. Adding more cores or compute doesn't help when
the memory subsystem is the bottleneck. This is called
**bandwidth-bound** in HPC literature (vs compute-bound).

### Decision rules — bandwidth dimension

- **Approach A saves N MB/s bandwidth** vs **Approach B costs M cycles**:
  - For busy-market scenario (~50% bus saturation), 1 MB/s saved bandwidth
    ≈ 50 cycles freed per second elsewhere (other threads no longer stalling)
  - Bandwidth saves COMPOUND at periodic cadences: 5 MB/s at 60 Hz × 24h/day
    = ~432 GB/day of DRAM traffic eliminated
- **Cross-thread invalidation**: when thread A writes a cache line held
  by thread B, B's copy invalidates (MESI; ~25-50 cycle RFO cost) AND
  the line refills from L2/L3/DRAM. Frequent shared writes burn bandwidth
  on top of latency. Pattern: `cross-thread-snapshot-publish-cluster-
  isolation.md` (ND1) — `alignas(64)` isolation prevents cache-line
  ping-pong on neighbor fields.

### Bandwidth-saving patterns in this codebase

| Pattern | Bandwidth effect |
|---|---|
| `loop-fusion-pattern.md` | Eliminate N-1 cold-cache walks of same array (canonical: v5.15.5.B.8 ~20 MB/s saved at 60 Hz) |
| `cache-layout-discipline-for-hot-side-structs.md` Rule 1 | Display-only field extraction → per-cycle cache doesn't pull display-only lines (.B.2 ~9.8 KB/slot removed from HOT cluster) |
| `cache-layout-discipline-for-hot-side-structs.md` Rule 4 | HOT/WARM/COLD tiering → forward-sequential access amplifies prefetcher (turns scattered cold reads into stream prefetch) |
| `decision-first-cluster-layout-pattern.md` (ND3) | Bail-eligible cycles touch line 0 only → cold-cache reads cut from ~17 to ~2 per skip cycle |
| `cross-thread-snapshot-publish-cluster-isolation.md` (ND1) | Cluster isolation prevents cross-thread RFO storms (.B.2 SlowPathTelemetry + WsHeartbeatTelemetry) |
| `bitmap-flag-api.md` | Multi-flag check via single mask AND (1 line fetch + 1 AND vs N byte-fetches + N branches) |

### Roofline analysis (informal)

For any kernel, compute **arithmetic intensity** = (FLOPs or cycles of
work) ÷ (bytes of memory accessed). If intensity is below
peak_compute / peak_bandwidth (~10-20 FLOPs/byte on Tiger Lake), the
kernel is bandwidth-bound — adding more compute won't help; fix the
bandwidth.

Most snapshot-publisher + slow-path workloads in this codebase are
bandwidth-bound (many memory touches, modest computation per byte
read). That's why v5.15.5.B focused on cache layout + loop fusion
rather than SIMD or compute-side optimizations.

## Promotion criteria (this doc was promoted)

Operator framing 2026-05-12: "can we make a design choice or something
that if we introduce a fix that introduce more latency, but avoids a
cache miss or similar things, we should use it, since the cache miss
ends up being slower anyways? same for branchless?"

This is a foundational engineering principle that's been applied
implicitly through CLAUDE.md items 7, 18, 26 but never codified as a
single decision framework. Making it explicit prevents the
"cycle-counting trap" in future audits.

Future application: every cache-layout audit, every SIMD-vs-scalar
choice, every branch-density audit uses this framework to make
quantitative decisions instead of intuition-based.
