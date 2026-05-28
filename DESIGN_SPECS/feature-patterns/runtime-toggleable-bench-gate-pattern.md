---
type: feature-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-13
tags: [latency-discipline, framework-discipline]
surface: [hot-path, slow-path, ci-tooling]
sister_specs: [universal-cfg-field-registry-pattern.md]
applies_at_skills: []
---

# Runtime-toggleable bench gate pattern

**Established:** 2026-05-13 (pre-v5.15.5.C.3)
**Status:** PROPOSED (zero applications yet; DESIGN_SPEC drafted before first application per CLAUDE.local.md "DESIGN_SPECS written BEFORE coding" rule)
**Cross-references:**
- CLAUDE.md item 18 (slow-path latency reduction; compile-time elision via `template <bool ENABLED>` + `if constexpr`)
- Existing build-flag-driven precedent: `LATENCY_PROFILING` cmake flag (compile-time only; cannot toggle without rebuild)
- TECH_DEBT-012 (FOREACH_OMS_STATE / OMS_INIT registry — bench gate is the verification substrate)
- Related: `latency-vs-cache-decision-framework.md` (cost framework for the OFF state)
- Pattern precedent: `partner-core-bitmap-pattern.md` boot-time-dispatched mode (similar shape: cfg → template instantiation)

---

## Problem statement

Latency micro-bench instrumentation has three modes today:

1. **Always-off** (production): zero instructions; latency unmeasured. Drift goes undetected.
2. **Build-flag-on** (`cmake -DLATENCY_PROFILING=ON`): instructions emitted; per-call rdtsc bracket measures end-to-end latency. But requires REBUILD to toggle; binary diverges from production binary — can't A/B-compare in-session; deployment to a colo machine for one-off measurement requires rebuild + redeploy.
3. **Always-on** (`-DLATENCY_BENCH=ON`): same as above with more histograms. Still rebuild-bound.

What's missing: **runtime cfg flag** that:
- Defaults OFF, costs ZERO in the off state (no branch, no instruction in the hot path)
- Can be flipped ON via cfg edit + restart (no rebuild) — same binary serves prod + bench
- Emits per-call latency histograms when ON
- Surface in TUI/GUI for live operator inspection

The "zero cost when off" requirement is load-bearing. Adding a runtime predicate `if (cfg.bench_enabled) ...` to a hot path is itself a cost: ~1 ns per cycle for the predicate read + branch. At 60-Hz publish × 16 cores × many call sites, that compounds. Per CLAUDE.md item 18 the canonical answer is **compile-time elision via template parameter + `if constexpr`** — but the template parameter has to be set somewhere.

This pattern: cfg flag at boot → template instantiation dispatch → all downstream code is templated on the bool → `if constexpr` discards the OFF branch entirely.

---

## Design space explored

### Option A: Always-on runtime predicate

```cpp
if (cfg.bench_enabled) {
    uint64_t t0 = __rdtsc();
    do_work();
    accumulate(_rdtsc() - t0);
} else {
    do_work();
}
```

Rejected: ~1 ns predicate cost per cycle in the OFF state, compounded across N sites × N cycles/sec. Fails the zero-cost-when-off requirement.

### Option B: Build-flag dispatch

```cpp
#ifdef LATENCY_PROFILING
    uint64_t t0 = __rdtsc();
#endif
    do_work();
#ifdef LATENCY_PROFILING
    accumulate(__rdtsc() - t0);
#endif
```

Rejected for the use case: production binary cannot toggle. Same binary cannot serve prod + bench A/B comparison without rebuild + redeploy. Acceptable as a SECOND layer (compile out further when truly never needed) but not the primary toggle.

### Option C: Template parameter + if constexpr (CHOSEN)

```cpp
// Cfg sets a bool at boot.
// Boot path dispatches to one of two template instantiations:
if (cfg.bench_enabled) {
    EngineSharded_Run<F, /*BENCH=*/true>(cfg, bcfg);
} else {
    EngineSharded_Run<F, /*BENCH=*/false>(cfg, bcfg);  // zero bench cost
}

// Inside Run<F, BENCH>:
template <unsigned F, bool BENCH>
inline void OrderManager_Tick(OrderManagerState<F>* oms) {
    if constexpr (BENCH) {
        uint64_t t0 = __rdtsc();
        do_tick_work(oms);
        oms_bench_histogram.accumulate(__rdtsc() - t0);
    } else {
        do_tick_work(oms);
    }
}
```

When `BENCH=false`, the `if constexpr (BENCH)` discards the entire then-branch at template instantiation. Generated assembly is identical to "no bench gate exists". Zero cost when off.

When `BENCH=true`, the rdtsc bracket + histogram accumulate are emitted as ~20-30 ns/cycle overhead. Acceptable for measurement runs.

### Option D: Function pointer dispatch

```cpp
using TickFn = void(*)(OrderManagerState<F>*);
TickFn fn = cfg.bench_enabled ? &OrderManager_Tick_Bench<F> : &OrderManager_Tick_NoBench<F>;
fn(oms);
```

Rejected: indirect call cost (~5 ns/branch mispredict) per cycle. Defeats the "zero cost when off" goal. Also breaks compiler inlining — TickFn can't be inlined.

---

## The pattern (concrete shape)

### Step 1 — cfg flag definition

```cpp
// ControllerConfig.hpp (engine cfg block)
struct ControllerConfig {
    // ... existing fields ...
    int oms_bench_enabled = 0;  // 0 = production (zero cost); 1 = runtime bench gate
};
```

cfg parser entry maps `oms_bench_enabled=1` text → int. Default 0 keeps production behavior unchanged.

### Step 2 — Boot-time template dispatch

```cpp
// engine main / EngineSharded_Run wrapper
if (cfg.oms_bench_enabled) {
    EngineSharded_Run<F, /*BENCH=*/true>(cfg, bcfg);
} else {
    EngineSharded_Run<F, /*BENCH=*/false>(cfg, bcfg);
}
```

The dispatch is at the entry point of the long-running engine loop. Per-cycle dispatch is amortized to zero (one branch at startup; engine runs for hours / days).

Two template instantiations of the engine body exist in the binary: one with bench, one without. ~2× the code size of EngineSharded_Run instantiations, but absolute size is small (~10-50 KB per instantiation; binary already ~50 MB). Both instantiations share most upstream / downstream code.

### Step 3 — bench gate at instrumented call sites

```cpp
template <unsigned F, bool BENCH>
inline void OrderManager_Tick(OrderManagerState<F>* oms) {
    if constexpr (BENCH) {
        uint64_t t0 = __rdtsc();
        OrderManager_Tick_Body(oms);
        uint64_t dt = __rdtsc() - t0;
        oms_bench.tick_hist.accumulate(dt);
    } else {
        OrderManager_Tick_Body(oms);
    }
}
```

`if constexpr` evaluates at template instantiation; the discarded branch is NOT compiled. When `BENCH=false`, the entire `if constexpr (BENCH) { ... }` block is GONE from the instantiated function body. The generated assembly is identical to writing `OrderManager_Tick_Body(oms)` directly.

### Step 4 — Histogram primitives

```cpp
// MemHeaders/LatencyHistogram.hpp (or similar; per-design)
struct LatencyHistogram {
    // Buckets: 64 logarithmically-spaced cycle counts (~1ns to ~1ms at 3 GHz)
    // Lock-free single-writer single-reader (drainer writes; snapshot publisher reads)
    alignas(64) uint64_t buckets[64];
    alignas(64) std::atomic<uint64_t> total_count;
    uint64_t min_observed;
    uint64_t max_observed;
};

inline int latency_bucket_index(uint64_t cycles) {
    // log2(cycles), clamped to [0, 63]
    return cycles ? __builtin_ctzll(__builtin_bit_floor(cycles)) : 0;
}

inline void LatencyHistogram_Accumulate(LatencyHistogram* h, uint64_t cycles) {
    int idx = latency_bucket_index(cycles);
    h->buckets[idx]++;
    h->total_count.fetch_add(1, std::memory_order_relaxed);
    if (cycles < h->min_observed) h->min_observed = cycles;
    if (cycles > h->max_observed) h->max_observed = cycles;
}
```

Per histogram: ~512 bytes (64 buckets × 8 bytes + scalars). Lock-free single-writer / single-reader matches drainer (writer) → snapshot publisher (reader) discipline. The `alignas(64)` on each cluster matches CLAUDE.md item 25 cross-thread cache-line isolation.

### Step 5 — TUI / GUI surface

```cpp
// Snapshot publisher reads histograms; renders p50/p99/max in TUI line:
// [OMS_BENCH] tick p50=42ns p99=180ns max=2.1µs  |  drain p50=89ns p99=350ns
```

The TUI display is itself only built when BENCH=true (compile-time-gated by the same template parameter). Cold-cache reads of histograms cost ~100 ns but happen at 60 Hz publish — negligible. Production binary (BENCH=false) emits no TUI bench line at all.

---

## Composition with CLAUDE.md items + existing patterns

| Pattern | Role |
|---|---|
| CLAUDE.md item 18 (compile-time elision) | The `if constexpr (BENCH)` discipline is canonical item 18 application |
| CLAUDE.md item 28 (cycles-vs-cache framework) | Cost analysis below uses item 28 |
| `latency-vs-cache-decision-framework.md` | Justifies the OFF state's zero cost; quantifies ON state cost |
| `cross-thread-snapshot-publish-cluster-isolation.md` (ND1) | LatencyHistogram clusters are alignas(64)-isolated cross-thread |
| `bitmap-flag-api.md` | The cfg flag can be part of a cohort bitmap (TECH_DEBT-XXX if multiple bench-gate-style cfgs accumulate) |

---

## Extreme-optimization composition (compose-with for maximum effect)

Beyond the basic compile-time-elision discipline, the bench gate pattern composes with **7 existing DESIGN_SPECS** for high-leverage wins. Each composition is opt-in — start with the basic shape, layer in compositions when the use case justifies.

### Composition 1 — AUTOPOPULATE companion for N-site bench instrumentation

Reference: `autopopulate-pattern-for-production-caller-class.md`

When 3+ bench sites accumulate (OMS Tick + DrainSubmit + DrainPostFill is already 3), define a single registry + AUTOPOPULATE macro instead of hand-writing the bracket at each site:

```cpp
// FOREACH_OMS_BENCH_SITE(X) — tuple: X(name, fn_to_instrument, hist_field)
#define FOREACH_OMS_BENCH_SITE(X)                            \
    X(tick,    OrderManager_Tick_Body,    tick_hist)         \
    X(drain,   OMS_DrainSubmit_Body,      drain_hist)        \
    X(fill,    DrainPostFill_Body,        fill_hist)

// AUTOPOPULATE companion generates the bracket per site:
#define BENCH_BRACKET_AUTOPOPULATE(name, fn, hist) \
    template <unsigned F, bool BENCH>                                                       \
    inline void OrderManager_##name(OrderManagerState<F>* oms) {                            \
        if constexpr (BENCH) {                                                              \
            uint64_t t0 = __rdtsc();                                                        \
            fn(oms);                                                                        \
            oms->bench.hist.accumulate(__rdtsc() - t0);                                     \
        } else {                                                                            \
            fn(oms);                                                                        \
        }                                                                                   \
    }

FOREACH_OMS_BENCH_SITE(BENCH_BRACKET_AUTOPOPULATE)
```

**Win:** adding the next instrumented site = 1 row. Cannot forget to bracket-wrap; cannot forget the if-constexpr discipline; cannot diverge between sites. Same Class-18-closure logic as FOREACH_OMS_PERSIST_FIELD applied to bench instrumentation.

### Composition 2 — Multi-bit mode encoding for bench granularity

Reference: `multi-bit-state-encoding-pattern.md`

If bench has more than 2 states (off / on), use 2 bits for 4 modes:

```cpp
// 4-mode bench encoding (2 bits in cfg.oms_bench_mode):
//   0b00 = OFF       (zero cost; production)
//   0b01 = COARSE    (per-call rdtsc; ~20 ns/cycle overhead; daily monitoring)
//   0b10 = FINE      (rdtscp + lfence; ~50 ns/cycle; one-off measurement)
//   0b11 = FULL      (rdtscp + per-bucket histograms + p99 tracking + CSV emit; ~200 ns/cycle)
```

The boot-time dispatch picks ONE of FOUR template instantiations. `if constexpr` discards 3 of the 4 paths at instantiation. Modes are mutually exclusive; mode field is 2 bits in a shared bench-cfg bitmap.

**Win:** richer instrumentation without paying for finest-grained always-on. Operator picks the granularity per session.

### Composition 3 — Per-node bench enable (the extreme optimization)

References: `partner-core-bitmap-pattern.md` + `per-bit-per-core-override-pattern.md`

**Bench just one core**, leave the other 15 cores at production-zero-cost:

```cpp
// cfg.oms_bench_core_mask = uint16_t bitmap; 1 bit per core
// e.g., 0x0020 = bench only core 5

template <unsigned F, bool BENCH>
inline void OrderManager_Tick_PerCore(OrderManagerState<F>* oms, int core_id) {
    if constexpr (BENCH) {
        // Branchless: read bit, mask off if not enabled for this core.
        // Cost: 1 AND (~1 cycle) when BENCH=true; ZERO when BENCH=false.
        bool this_core = BITMAP_IS_SET(cfg.oms_bench_core_mask, BITMAP_BIT_U16(core_id));
        if (this_core) {
            uint64_t t0 = __rdtsc();
            OrderManager_Tick_Body(oms);
            oms->bench.tick_hist[core_id].accumulate(__rdtsc() - t0);
        } else {
            OrderManager_Tick_Body(oms);
        }
    } else {
        OrderManager_Tick_Body(oms);
    }
}
```

**Win:** the operator can instrument core 5's tick latency for a 1-hour live measurement window WITHOUT slowing down cores 0-4, 6-15. When BENCH=false, the per-node check is also elided (zero cost). When BENCH=true, the per-node mask check is 1 cycle — strictly cheaper than the unconditional rdtsc bracket.

**Extreme scenario:** profile a specific core in production without affecting trading on the others. Per-node isolation pattern + bench gate pattern compose to "production-cost on 15 cores + bench-cost on 1 core" simultaneously.

### Composition 4 — Cache-layout discipline on the histogram

Reference: `cache-layout-discipline-for-hot-side-structs.md`

LatencyHistogram has both HOT and COLD sub-fields:

```cpp
struct LatencyHistogram {
    // HOT: drainer writes per cycle
    alignas(64) uint64_t buckets[64];  // 1 cache line × 8 = 512 B (8 cache lines)

    // COLD: snapshot publisher reads at 60 Hz; min/max updated rarely
    alignas(64) std::atomic<uint64_t> total_count;
    uint64_t min_observed;
    uint64_t max_observed;
};
```

`alignas(64)` separates the HOT bucket array from the COLD observability counters. Publisher reads of `total_count` don't invalidate drainer-written bucket cache lines (ND1 cluster isolation applied INSIDE the histogram).

### Composition 5 — Branchless bucket-index calc via BMI2

Reference: `branchless-math-kernel-pattern.md`

The `latency_bucket_index` function (log2-based bucket selection) compiles to `BSR` + clamp on modern x86. For non-power-of-2 bucketing (e.g., linear buckets up to 1000ns + log from there), use BMI2 `PEXT`:

```cpp
inline int latency_bucket_index_bmi2(uint64_t cycles) {
    // Linear < 32 buckets, log above.
    uint64_t lin_part = cycles & 0x1F;                                  // 5 low bits
    uint64_t log_part = __builtin_ctzll(cycles | (1ULL << 32)) - 5;     // log of high bits
    return (cycles < 32) ? lin_part : 32 + log_part;
}
```

(One branch remains — fold via mask trick if profiler shows it matters.)

### Composition 6 — Histogram cluster isolation (already in spec body; re-emphasized)

Reference: `cross-thread-snapshot-publish-cluster-isolation.md` (ND1)

Each LatencyHistogram is `alignas(64)`-isolated as a unit. When multiple histograms coexist on the same OMS struct, each gets its own cache line(s). Drainer writes histogram N; publisher reads histogram N at 60 Hz. No cache-line ping-pong between adjacent histograms or between histogram and neighbor OMS fields.

### Composition 7 — Heterogeneous registry for mixed measurement types

Reference: `heterogeneous-registry-pattern.md`

If different bench sites measure different quantities (cycle counts at tick, byte counts at OMS_PushSubmit ring depth, event counts at DrainPostFill), the FOREACH_OMS_BENCH_SITE tuple can carry the measurement TYPE:

```cpp
#define FOREACH_OMS_BENCH_SITE(X)                                       \
    X(tick,        CYCLES,    OrderManager_Tick_Body,    tick_hist)     \
    X(submit_ring, BYTES,     OMS_PushSubmit,            ring_hist)     \
    X(fills,       COUNT,     DrainPostFill_Body,        fill_hist)

// Per-type AUTOPOPULATE dispatch:
#define BENCH_AUTOPOPULATE_CYCLES(name, fn, hist) /* rdtsc bracket */
#define BENCH_AUTOPOPULATE_BYTES(name, fn, hist)  /* ring-depth sample */
#define BENCH_AUTOPOPULATE_COUNT(name, fn, hist)  /* event counter increment */
```

Pattern shape mirrors FOREACH_OMS_PERSIST_FIELD's DIRECT/BIT kind dispatch.

---

## Cost analysis (per CLAUDE.md item 28)

### OFF state (production)

| Surface | Cost |
|---|---|
| Hot path cycle | **0 cycles** (if constexpr discards bench branch entirely) |
| Cold path cycle | **0 cycles** (same) |
| Binary size | +2× EngineSharded_Run instantiation (~10-50 KB) |
| Memory footprint | +0 bytes (BENCH=false instantiations don't allocate histograms) |
| Cache footprint | +0 bytes (histograms not instantiated) |

### ON state (bench measurement run)

| Surface | Cost |
|---|---|
| Per-cycle rdtsc bracket | ~20-30 ns (1 rdtsc enter + 1 rdtsc exit + bucket lookup + counter increment) |
| Histogram cache line | 1 cache line per histogram, alignas(64)-isolated |
| Memory footprint | ~512 bytes per instrumented site (handful of sites) |
| Production-binary divergence | NONE — same binary, cfg flag flip + restart toggles mode |

The 20-30 ns/cycle ON-state cost is acceptable for measurement: bench runs are time-bounded (minutes to hours, not days), and the goal is RELATIVE comparison between code variants, not absolute production timing.

### Decision rule

Always-on runtime predicate would cost ~1 ns/cycle × N sites × N cycles = ~10-100 μs/sec wasted production work. Template-elided pattern saves this entirely. Per CLAUDE.md item 28 cycle-vs-cache framework, the binary-size cost (~50 KB at 50 MB total = 0.1%) is dwarfed by the latency win.

---

## When to use this pattern

✅ Hot or slow path needs instrumentation but production must run instrumentation-free.
✅ Same binary must serve both production and benchmark modes (no rebuild barrier).
✅ Cost of "always-on predicate" is non-negligible on the surface (hot path, per-cycle).
✅ The instrumentation is opt-in for the operator (cfg flag flip + restart).
✅ Multiple bench surfaces co-vary (one cfg flag governs all OMS bench gates, etc.) — single template parameter dispatches a cohesive surface.

## When NOT to use this pattern

❌ Instrumentation needed continuously in production (use always-on but cheaper instrumentation, e.g., atomic counter without rdtsc — accept the ~0.5-1 ns/cycle cost).
❌ The instrumented code path is COLD (called rarely; predicate cost is amortized to zero anyway). Use Option A's always-on runtime predicate; saves binary size.
❌ Multiple bench surfaces vary INDEPENDENTLY (need separate templates per surface) — the design space gets complex; reconsider whether full template-elision is warranted vs accepting per-surface predicate cost.
❌ Toggling needs to happen mid-session without restart — the boot-time template dispatch can't toggle (would need a runtime dispatch table, which defeats elision).

---

## Implementation checklist (per application)

When adding the pattern to a new instrumentation surface:

- [ ] cfg flag declared with default = 0 (off in production)
- [ ] cfg parser entry maps text → int
- [ ] Boot-time dispatch site reads cfg flag once, picks template instantiation
- [ ] `template <..., bool BENCH>` propagates through call chain to instrumented sites
- [ ] `if constexpr (BENCH)` wraps every bench-only block (rdtsc, histogram, TUI line)
- [ ] LatencyHistogram clusters use `alignas(64)` for cross-thread isolation
- [ ] Snapshot publisher reads histograms via atomic.load(RELAXED) — display only
- [ ] **Assembly-verify ONE time at first application** that the OFF instantiation has zero bench-related instructions in the body. Document the verified assembly output in the application's commit message.
- [ ] Binary size delta measured + accepted before merge (~10-50 KB per duplicated template instantiation)
- [ ] Operator documentation: how to flip the flag + interpret the histogram output
- [ ] cfg flag entry added to `FEATURE_LOOKUP.md` per the auto-write contract

---

## Caveats and footguns

1. **Template instantiation blow-up:** every function in the bench-gated subtree gets 2× instantiations. If the subtree is large (multi-thousand-LOC engine body), binary size grows quickly. **Mitigation:** scope the BENCH template parameter to the smallest enclosing function that needs the bench gate; don't propagate it to upstream callers unless they instrument too. The boot-time dispatch wraps the smallest possible scope.

2. **Compiler regression risk:** older toolchains (gcc < 13) may fail to fully discard `if constexpr (false)` branches in some contexts (e.g., when the discarded branch references undefined symbols). **Mitigation:** assembly-verify at first application; test with both gcc + clang.

3. **rdtsc cycle-count variance:** raw rdtsc is not serializing; out-of-order execution can move instructions across the bracket. For coarse-grained measurement (>~1 μs intervals), this is noise. For fine-grained (10-100 ns intervals), use rdtscp + lfence/mfence. **Mitigation:** document the expected measurement granularity per bench site; use rdtscp where fine-grained matters.

4. **Histogram bucket overflow:** uint64 counters at very high event rates can overflow over very long runs (years). **Mitigation:** snapshot publisher reads + clears (or uses sliding window). For OMS-tick-rate (~1k/sec), no overflow in practical session lengths.

5. **Cross-thread visibility:** drainer writes histogram; snapshot publisher reads. Must use `std::atomic<uint64_t>` for `total_count` (publisher reads at 60 Hz). Bucket counts can be plain `uint64_t` since drainer is the sole writer (single-writer / single-reader; no atomic needed within drainer scope).

6. **Boot-time template dispatch fan-out:** if multiple unrelated cfg flags each pick template parameters, the cartesian product of instantiations grows. **Mitigation:** at >2 independent bool flags, consider packing into a bench-mode enum + per-mode template instantiation, OR accept that the worst case is ~4 cohesive instantiations of EngineSharded_Run.

---

## First application target

**v5.15.5.C.3** — `OrderManager_Tick` + `OMS_DrainSubmit` + `DrainPostFill` per-call rdtsc histograms.

- cfg flag: `oms_bench_enabled` (default 0)
- Boot-time dispatch at EngineSharded_Run entry
- Three instrumented call sites: `OrderManager_Tick`, `OMS_DrainSubmit`, `DrainPostFill` (per-fill timing inside its loop)
- TUI surface: 3-line bench histogram readout when ON
- Histograms: `oms_bench.tick_hist`, `oms_bench.drain_hist`, `oms_bench.fill_hist` — each 512 bytes, alignas(64)
- Assembly verification: confirm BENCH=false instantiation has identical body to pre-.C.3 reference (use `objdump -d` diff on `OrderManager_Tick<64, false>` vs reference)

---

## Cross-references to CLAUDE.md

After 1-2 applications + assembly-verified zero-cost-when-off claim, this pattern qualifies for promotion to a CLAUDE.md item per the "codify design principles as patterns mature" going-forward rule:

> **N. Runtime-toggleable bench gate via boot-time template dispatch + if constexpr elision** — cfg flag picks template parameter at engine boot; instrumentation discarded entirely when off (zero instructions). See `DESIGN_SPECS/feature-patterns/runtime-toggleable-bench-gate-pattern.md` + CLAUDE.md item 18 (compile-time elision principle).

Pre-promotion: this DESIGN_SPEC stands alone; consumers reference it directly from their cfg-flag declaration.

---

**End of spec.**
