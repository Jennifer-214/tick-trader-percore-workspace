# Latency-Path Discipline

**Architectural rules for any code on a latency-impacting path.** Hot
path is the priority focus (strictest rules), but slow path / OMS
drainer / parsing also benefit from the same patterns at relaxed
intensity. This document captures patterns that aren't obvious from
reading `STRATEGY_AND_CODING_RULES.md` alone — they emerged from the
v5.10/v5.11 audit cycles and are easy to violate without realizing.

**Discipline scales with cadence:**
- Hot path (per-tick) — all 7 rules, strictly.
- Slow path (per-cadence rebuild) — Rules 1, 2, 3, 5, 6, 7 apply; Rule 4
  (branch predictor) relaxed since slow-path branch mispredicts cost
  amortizes across the cadence interval.
- OMS drainer (per-fill) — Rules 2 (no I/O), 3 (no inline retry),
  6 (no pointer chasing) apply; cache layout / branch discipline
  relaxed.
- Parsing (per-WS-frame) — Rules 2 (no malloc), 3 (no inline blocking),
  6 (dense buffers).
- Snapshot publish — Rule 7 (cross-thread sync) is paramount; v5.11.3
  Seqlock pattern.

**Read this BEFORE writing or modifying:**
- `CoreFrameworks/ExecutionCore.hpp` (per-tick hot path)
- `CoreFrameworks/ControllerEventLoop.hpp` slow-path rebuild loop
- `CoreFrameworks/OrderManager.hpp` drainer paths
- `Strategies/StrategyParameters.hpp` dispatch table
- Anything touching `RollingStats_Push` / `Regime_ComputeSignals`
- Anything called from `EngineSharded_Run`'s per-core thread loops

**Source audits:** `LATENCY_OPTIMIZATION_AUDIT.md` Parts 1-3, 6, 7;
`STRATEGY_AND_CODING_RULES.md` (companion rules doc).

---

## What "latency-impacting path" means

| Path | Cadence | Discipline applies? |
|---|---|---|
| Hot path (`ExecutionCore_Tick`, `BG_Evaluate`, `SG_Evaluate`) | Per tick (~1µs apart) | YES — strictest |
| Slow path (`EventLoop_RebuildOneCore`, `RollingStats_Push`, `Regime_ComputeSignals`) | Per cadence (~100 ticks) | YES — high-priority |
| OMS drainer (`OMS_DrainSubmit`, `OrderManager_Tick`) | Per fill / per-tick check | YES |
| Producer thread fan-out | Per tick | YES |
| Snapshot publish (TUISnapshot copy) | Per cadence | YES — torn-read class |
| Parsing (WS ingest, REST execution reports) | Per WS frame / per fill | YES |
| Boot init / cfg parse / TCP connect | Once at startup | NO — readable code wins |
| Stamp emission / model save | At training time | NO |
| TUI render loop | ~60Hz on render thread | NO (separate thread) |

The discipline scales with cadence. Per-tick code gets all 7 rules
below; per-cadence slow-path gets most of them; per-fill OMS gets the
"no I/O / no sleep" subset.

---

## Rule 1 — Cache line layout discipline

**Cache line = 64 bytes.** A struct field that's read every tick must
fit in a cache line — never span two — or you load 2 lines per tick
instead of 1. Same applies to writes.

### Field-span analysis

When adding a field to an existing hot struct:

1. Compute `sizeof(field)` exactly. **Common gotchas:**
   - `FPN_Binary<64>` = **16 bytes** (bare two's-complement `__int128`; 4 per cache line) — since Ship A
     `v5.15.5.F.4d.1.E.0.7`; it was 24B sign-magnitude (`w[2]`+sign+pad) pre-Ship-A. (Fixed at A.5: this
     line survived the Ship-A doc sweep still teaching 24B — the widened doc-size guard now scans this file.)
   - Arbitrary widths (`<128>`/`<256>`) are SHED — the primary template is declaration-only; only `<64>`
     exists (D-143/D-151).
   - `std::atomic<T>` is `sizeof(T)` plus alignment requirements.
   - Pointers are 8 bytes; references compile to pointers.

2. Compute the field's offset (sum of preceding fields + their padding).

3. Check if `offset + sizeof(field) > (offset / 64 + 1) * 64`. If yes,
   the field spans two cache lines — bad.

### Cache line cluster pattern

Group fields by access pattern, not declaration convention:

```cpp
struct alignas(64) Foo {
    // Line 0 (hot READS every tick):
    field_a;          // hot read
    field_b;          // hot read
    // ...pad to keep all hot reads in line 0...

    // Line 1+ (hot WRITES on rare events):
    field_c;          // entry-only write
    field_d;          // entry-only write

    // Line N (cross-thread atomic):
    alignas(64) atomic_field;
    pad_to_64[];

    // Line N+1+ (cold init-time fields):
    cold_field;
};
```

### Cross-thread fields → own cache line

Any field written by thread A and read by thread B (or vice versa)
should sit on its own cache line. Otherwise:
- Thread A's write invalidates the cache line in thread B's L1d
- Thread B reloads the entire line on next read
- Cost: ~30-50ns per ping-pong

The `permission` flag in `ExecutionCore` violated this until v5.11.1.5
isolated it. **Verify with grep before merging:** any field accessed via
`__atomic_load_n` / `__atomic_store_n` / `std::atomic<T>` should have
`alignas(64)` (or be in a struct that does).

### Steady-state cache footprint cap

Per-tick code should fit its working set in 4-8 cache lines (256-512
bytes). Tiger Lake L1d = 48KB / 64B = 768 lines per core; per-core
sharded design means L1d isn't shared across cores, so eviction
pressure is bounded — but discipline prevents creep.

---

## Rule 2 — No I/O on hot/slow paths (no `fprintf`, no syscalls, no `malloc`)

`fprintf` grabs libc's stdio mutex. `printf` does too. `write()` is a
syscall. `malloc` may take an internal lock. Any of these on a
latency-impacting path can cascade-stall the entire engine.

### Failure-path observability pattern

When a hot-path operation can fail (SPSC ring full, NaN feature, etc.),
**increment a counter** instead of logging:

```cpp
// BAD: hot path
if (push_failed) {
    fprintf(stderr, "[core %d] push failed\n", core_id);  // libc mutex!
}

// GOOD: hot path
if (push_failed) {
    core->push_failures++;  // single store, no I/O
}

// Slow path (or snapshot publisher):
// Reads core->push_failures periodically, logs delta if non-zero,
// or surfaces via TUISnapshot for GUI display.
```

Counters are:
- Lock-free single-writer (the hot path's own thread)
- Read by slow path with `__atomic_load_n(..., ATOMIC_RELAXED)` — relaxed
  is fine since the slow path is OK with stale-by-1-tick data
- Visible to TUI via existing PerCoreSnap field-add pattern

### Observed in the wild

`ExecutionCore_Tick`'s ring-push-failure path used to call `fprintf`
inline. Fixed in v5.11.0.1: replaced with `ring_push_failures` counter.
The `fprintf` only fired under degraded conditions (drainer stalled),
but the libc mutex acquisition during such conditions could cascade-stall
the hot path further.

### Same rule for `malloc` / `free`

If you find yourself reaching for `new` / `malloc` / `std::vector` on
a hot/slow path, stop. Use:
- Pre-allocated buffers (`char buf[64]`)
- Custom allocators drawing from the engine's `mmap` arena
  (post-v5.11.6 this becomes the canonical pattern)
- Lock-free SPSC/MPSC rings for inter-thread communication

---

## Rule 3 — SPSC ring failure → counter, not retry

`SPSCRing_TryPush` returns `false` when the ring is full. **Do not
retry inline.** Don't busy-wait. Don't re-push next tick blindly.

The correct pattern (already in `ExecutionCore_Tick`):
1. Check the return value.
2. If false, increment a failure counter (Rule 2).
3. **Preserve state** — don't flip flags that depend on the push
   succeeding. e.g., if a position-exit event failed to push, leave
   `core->active = 1` so next tick retries naturally with a fresh tick.
4. Slow path / drainer detects the back-pressure separately
   (high counter, or the ring's `Depth` reading max).

### Why retry-inline is wrong

If you retry inline (loop until push succeeds), you couple hot-path
latency to drainer responsiveness. Drainer briefly stalled (page
fault, kernel preemption, sleep) → hot path stalls for the same
duration. That's the exact tail-variance category we're killing.

Counter + preserve state means: a single dropped tick has bounded
recovery (one tick's delay), the engine self-heals next tick.

---

## Rule 4 — Branch predictor discipline

Branches on the hot path are OK if and only if:
1. The branch direction is data-independent OR predicts ~100% one way
2. You annotate predicted-rare branches with `__builtin_expect(cond, 0)`
3. The compiler knows the cold side is genuinely cold (use
   `__attribute__((cold))` for cold helpers)

### Common patterns

**Predicted-not-taken (rare event):**
```cpp
if (__builtin_expect(can_enter | can_exit_a | can_exit_b, 0)) {
    // event push, mostly cold
}
```
The branch predictor learns "not taken" within ~1k ticks. Steady-state
cost: ~0ns.

**Compile-time elision (config flag):**
```cpp
template <bool LAT_ENABLED>
__attribute__((always_inline))
static inline void ExecutionCore_Tick(...) {
    if constexpr (LAT_ENABLED) {
        // sampled code: completely compiled out when LAT_ENABLED=false
    }
}
```
Zero runtime overhead in production builds. Used in v5.11.1.1.

**Branchless predicate combination:**
```cpp
// Combine multiple bool conditions without branches:
uint64_t can_enter = (~any_active & (uint64_t)perm & bg_fires) & 1ULL;
// vs
if (!any_active && perm && bg_fires) { ... }  // branchy
```

### What NOT to do

- **Data-dependent branches** (e.g., `if (price > threshold)`). These are
  mispredicted ~50% of the time on noisy data → 15-20 cycle bubble per
  miss. Use the bitwise pattern above.
- **`if (lat_enabled)` checks every tick** when `lat_enabled` flips
  rarely. The branch is well-predicted, but the LOAD of `lat_enabled`
  itself touches a cold cache line. Use template bool elision.

---

## Rule 5 — FPN_Binary sizing awareness

`FPN_Binary<64>` is the engine's binary fixed-point type — **16 bytes** (a bare
`__int128 v`, two's-complement). The Ship-A 16B flip (`.E` #11) compacted it from
the old 24B sign-magnitude (`uint64_t w[2]` + `int32_t sign` + pad) and shed
arbitrary width at the same time: the primary `FPN_Binary<F>` is now a declaration-only
incomplete type, so only `FPN_Binary<64>` exists (`FPN_Binary<128>`/`<256>` are gone).

| Type | Size | Cache line position |
|---|---|---|
| `FPN_Binary<64>` (the binary fixed-point type) | **16 bytes** | 4 fit in a 64B cache line |

**Implications:**
- 4 `FPN<64>` fit per cache line (was 2.6 at 24B) — a struct with up to 4
  back-to-back stays within one line; still reorder + pad hot structs by access
  pattern.
- AVX-512 zmm reg = 64 bytes, holds 4 `FPN<64>` (was 2.6). Plan wide math
  accordingly.

**Mistake to avoid (inverted at the 16B flip):** `FPN_Binary<64>` is now exactly
`sizeof(__int128) == 16` — no sign field, no padding. Code still assuming the old
24B layout (`.w[]`/`.sign` members, `sizeof==24`) is a post-flip bug; those
members are gone.

---

## Rule 6 — Pointer chasing → dense flat arrays

Linked lists, trees, hash maps all involve pointer chasing. Each
dereference is a potential L1 miss. On the hot path that's catastrophic.

**The codebase avoids:**
- `std::unordered_map` / `std::map` / `std::list` (compile-time enforced
  via grep audit; CLAUDE.md Decision 13 X-macro registry pattern when
  multi-site additions are needed)
- `std::function` (vtable + heap)
- `std::shared_ptr` / `std::unique_ptr` on hot path (atomics + heap)

**The codebase uses:**
- `std::array` (stack, fixed size, dense)
- C-style arrays sized via `constexpr` (e.g., `MAX_EXECUTION_CORES`)
- Bitmaps (`uint16_t portfolio.active_bitmap`)
- Index-keyed lookup tables (e.g., `core_id` as direct array index)

Compile-time check: `static_assert(!std::is_polymorphic<T>::value, ...)`
on key structs (added in v5.11.0.E for ExecutionCore + PortfolioController).

---

## Rule 7 — Cross-thread synchronization patterns

For inter-thread state handoff, use the appropriate pattern:

| Pattern | Use case | Latency |
|---|---|---|
| **SPSCRing<T, N>** | Producer/consumer, fixed throughput | ~1ns try_push when not full |
| **ParameterSlot<T> seqlock** | Slow→hot push of GateParameters (already 1 reader, 1 writer) | ~6ns full read; ~1ns cached-seq check |
| **`alignas(64) atomic<T>`** | Single-byte flags (e.g., `permission`, `kill_tripped`) | ~1ns atomic load (acquire) |
| **TUISnapshot double-buffer** ⚠️ | (DEPRECATED — torn-read class; v5.11.3 replaces with seqlock) | N/A |

### Don't use

- `std::mutex` — kernel call on contention; tail spike up to ms
- `std::condition_variable` — kernel call on wait
- `std::shared_mutex` — both atomics + potential blocking
- `pthread_rwlock` — same problems

If you find yourself wanting one of these on a hot/slow path, you
probably need:
1. A SPSC ring instead, OR
2. Eventually-consistent reads (relaxed atomic load + accept staleness), OR
3. To restructure the design so the read can happen on the slow path

---

## Verification before merging hot-path changes

Run this checklist before any PR that modifies `ExecutionCore_Tick`,
`BG_Evaluate`, `SG_Evaluate`, or fields of `ExecutionCore` /
`GateParameters` / `ParameterSlot`:

1. **`./build.sh latency`** — builds with LATENCY_PROFILING=ON; run
   the engine in synthetic mode + observe p50/p99/p99.9 in TUI.
2. **`-S` assembly inspection** — `g++ ... -S -o exec_core.s` then
   inspect `ExecutionCore_Tick` body. Check for:
   - No `call malloc` / `call free` / `call __libc_*`
   - No stack spills (look for `mov %rXX, -8(%rbp)` patterns
     beyond the function preamble)
   - No `vmovups` / `vmovdqu` reads beyond the expected hot fields
3. **`./tools/calls_graph_diff.sh`** — confirms no new orphan symbols.
4. **Replay-determinism test** at `tests/controller_test.cpp:10251` —
   bytewise-equal output across runs.
5. **Bench gate (audit's standard for hot-path mods)** — p99 ≤ baseline
   p99 across 10M-tick replay; p99.9 should improve.

If any item fails, the change isn't ready.

---

## Anti-patterns observed historically

These all happened in this codebase before being caught + fixed.
**Do not reintroduce.**

1. **Field span across cache lines** — `live_sl` spans line 0→1 in
   `ExecutionCore` due to `FPN_Binary<64>=24B` math being miscalculated as
   16B. Fixed in v5.11.1.5 layout reorder.

2. **`fprintf` on rare-failure hot-path branch** — was in
   `ExecutionCore_Tick` push-failure path. Replaced with counter in
   v5.11.0.1. (Cascading mutex-stall risk under degraded conditions.)

3. **Permission flag on hot cache line** — controller atomic-stores from
   another CPU; line 0 ping-pongs. Fixed in v5.11.1.5 by isolating
   to its own `alignas(64)` block.

4. **`if (active_b)` branch on hot path** — leg-B compares branch-gated
   because FPN_Binary compares didn't pipeline cleanly. AVX-512 vectorization
   in v5.11.1.2 removes the branch.

5. **`lat_enabled` runtime load** — every tick read a cold cache line
   for the enable flag. Eliminated via template bool in v5.11.1.1.

6. **Snapshot torn reads** — TUISnapshot double-buffer toggle without
   seqlock; producer can lap reader. Fixed in v5.11.3 (seqlock pattern).

7. **`is_buyer_maker` dropped on slow-path scalar bus** — slow path
   hardcoded 0 for is_buyer_maker because v5.1.2 architectural carry-
   forward dropped the field. Train-serve parity preserved (both broken
   the same way), but `volume_delta` feature locked at +1.0 →
   zero-information. Documented in `KNOWN_ISSUES.md`; full closure
   deferred to v5.10.X / v5.11+.

When the next anti-pattern emerges, add it here.

---

## Rule 8 — Branchless mask-blend over data-dependent branches (added v5.11.2)

When a latency-path computation has "do work A else do work B" semantics where:
- The condition is data-dependent (varies tick-to-tick or push-to-push)
- Both A and B can be computed at small marginal cost
- The branch isn't a one-shot warmup transition that the predictor learns once

**Prefer:** unconditional compute of both, mask-blend selection by the condition.
Eliminates the non-predictive branch entirely; same throughput, no mispredict tail.

### Canonical pattern

```cpp
// BAD: data-dependent branch
if (some_condition) {
    result = compute_A();
} else {
    result = compute_B();
}

// GOOD: unconditional compute + mask blend
auto a = compute_A();              // always computed
auto b = compute_B();              // always computed
uint64_t mask = -((uint64_t)some_condition);  // 0 or all-1s
result = blend(a, b, mask);        // bitwise blend, no branch
```

### FPN-specific helper (added v5.11.2.C; body below = the LIVE 16B `<64>` specialization since Ship A)

```cpp
// FixedPoint/FixedPointN.hpp — the live <64> body (16B __int128 core). The pre-Ship-A generic
// w[]-word-loop + sign-field body it replaced is dead-pending the Ship-B core cleanup (S-13).
template<> inline FPN_Binary<64> FPN_BlendOnMask<64>(FPN_Binary<64> if_true, FPN_Binary<64> if_false, uint64_t mask) {
    unsigned __int128 m = (unsigned __int128)(__int128)(int64_t)mask;  // 0 / all-ones-128 (sign-extended)
    return { (__int128)(((unsigned __int128)if_true.v & m) | ((unsigned __int128)if_false.v & ~m)) };
}
```

### When to use

- ✓ Slow-path running sum updates (eviction term active vs warmup)
- ✓ Conditional zeroing of FPN_Binary values in branchless predicates
- ✓ Per-handle parameter dispatch where compute is similar across paths
- ✓ Any "predicate fires once, condition stable post-warmup" transition

### When NOT to use

- ✗ Compute is genuinely heavy (one path 100ns, other path 10ns) — even with mispredict tail, the branch saves more than mask-blend overhead
- ✗ Hot path with literal 0ns predicted-stable branches (compile-time `if constexpr` via template bool is cheaper)
- ✗ Multi-output computation where blending each output costs more than a single mispredict (rare)

### Cross-pattern: monotonic deque for sliding-window min/max

Maintaining sliding-window min/max in O(1) **without branches** uses a monotonic
deque. Standard algorithm:

- Push: pop indices from the back while their values are `<= new_value` (max
  deque) or `>= new_value` (min deque). Push new index. Result: deque values
  are monotonically decreasing (for max) or increasing (for min).
- Front of deque is always the current min/max (window's min/max from oldest
  in-deque sample).
- Evict (out-of-window): if front's index is the evicted slot, pop front.
- O(1) amortized per push (each element enters and leaves the deque once).

For our use case (RollingStats min/max over window of W=128 prices), the deque
size is bounded by W. The pop-while-back-is-dominated loop CAN have data-
dependent iterations, but each iteration pops a previously-popped-when-it-
itself-was-dominated index → amortized O(1). The branch is on "deque empty?"
which is correctly predicted in steady state (new sample rarely dominates
all existing ones).

For RollingStats post-v5.11.2.C: monotonic deque replaces the
"if (evicted == min/max) recompute" branch with O(1) amortized branchless-ish
maintenance. The deque pop-loop fires occasionally but is bounded.

---

## Audit recommendations evaluated + deferred

Some audit-suggested optimizations were evaluated during v5.11.1 and skipped
after closer analysis showed they don't deliver claimed gains for the actual
code shape / workload. Documented here so a fresh session doesn't re-attempt
them without revisiting the analysis.

### Phase 1.3 — AVX-512 mask blend for active/inactive thresholds (DEFERRED)

**Audit claim** (LATENCY_OPTIMIZATION_AUDIT.md Part 1.3):
> "Use `_mm512_mask_blend_epi64` to simultaneously blend the active/inactive
> thresholds for both Leg A and Leg B in one instruction rather than multiple
> sequential CMOV chains." ~5-10ns saved.

**Reality check (2026-05-06):**
- Current CMOV instructions: 1-cycle latency, dispatched in parallel by Tiger
  Lake's 4 ALU ports → effectively 1 cycle for 4 selects.
- AVX-512 `vpblendmq`: 1-cycle latency, plus mask-register setup (~1 cycle to
  load mask from `active` byte).
- 4 × FPN_Binary<64> = **64 bytes — exactly one __m512i/zmm** (updated at A.5: was "96B / 2-per-zmm"
  under the 24B layout; Ship A's 16B flip changed this arithmetic).
- (The old magnitude-only/sign-field nuance died with the sign field — two's-complement since Ship A.)
- NOTE: 4-per-zmm MAY shift the CMOV-vs-vpblendmq trade below; re-deriving that analysis belongs to the
  post-Ship-B re-pack pass (TECH_DEBT-159 /dod-audit), not this currency fix — the 2026-05-06 conclusion
  stands as written until then.

**Net realistic gain: 0-2ns at best, possibly zero or negative due to register
pressure changes from mask-register setup.** Not worth the bytewise-determinism
risk + scalar-fallback infrastructure.

**Revisit when:**
- A new generation CPU significantly improves AVX-512 mask blend throughput
  vs CMOV
- The binary representation changes again (widths are D-129-parked; decimal money lands at Ship B —
  re-run this math then)
- Hot path adds a 5th or 6th simultaneous threshold compare (where mask blend's
  fixed cost amortizes better)

### Phase 1.4 — Branchless ring-buffer commit (DEFERRED)

**Audit claim** (LATENCY_OPTIMIZATION_AUDIT.md Part 1.4):
> "Make the ring buffer commit completely branchless. Write the `TradeEvent`
> to the current ring buffer slot unconditionally, and advance the head
> pointer conditionally using: `head += (can_enter | can_exit)`. This removes
> the final remaining control-flow branch in the hot path."

**Reality check (2026-05-06):**

The branch wraps the entire event-push block (entries + exits + failure
counter). It's not a data-dependent branch — it's a "did anything fire this
tick?" check. Branch predictor handles this well:

| Fire rate per tick | Mispredict cost amortized | Branchless cost per tick |
|---|---|---|
| 0.1% (slow scalping) | ~0.005ns | ~5-7ns (always-construct) |
| 1% | ~0.05ns | ~5-7ns |
| 5% (active trading) | ~0.25ns | ~5-7ns |
| 50% (every other tick) | ~3ns | ~5-7ns |
| 90% (extreme HFT) | ~5ns | ~5-7ns |

For any realistic strategy fire rate (≤10% of ticks), the branched version
wins because the branchless version pays unconditional event-construction +
ring-slot-write cost (~15-20 cycles) on every tick.

**The branchless version only wins when fire rate >> 50%** — which would
imply microsecond hold times. None of the current strategies operate at that
frequency.

**Revisit when:**
- Strategy mix shifts to maker-order based execution where fire rate per tick
  could be much higher (every quote update fires a cancel/replace/fill event)
- Ultra-tight scalping strategies (microsecond holds) get added
- Bench measurement on operator's actual workload shows branch mispredict cost
  visible in p99 / p99.9 (would suggest fire rate is higher than estimated)

**Test for "should I revisit?":** Run the engine for a representative session.
Check `core->ring_push_failures` counter (added in v5.11.0.1) + estimated event
push rate from controller drainer logs. If event push rate > ~10% of tick
rate, run the bench gate comparison: `pre-v5.11.1` (branched) vs branchless
prototype. If p50 improves by ≥ 3ns, ship branchless. Otherwise stay branched.

### General principle from these deferrals

Audit recommendations are **starting points** for analysis, not gospel. Always
work through:
1. **What's the actual cost of the current code?** (branch with predictable
   pattern ≈ ~0ns; branch on data-dependent compare ≈ ~5-7ns mispredict cost
   × 50% rate)
2. **What's the cost of the proposed alternative?** (branchless replacement
   often pays unconditional work cost where branch was free)
3. **What workload pattern justifies the change?** (fire rate, hold time,
   strategy mix)

The audit was right that the v5.11 sprint should focus on hot-path
optimization. But within Part 1, items 1.1 + 1.2 + 1.5 deliver the actual
gains; 1.3 + 1.4 are micro-optimizations whose ROI depends on workload
characteristics that don't match our current strategies.

---

## Cross-references

- `STRATEGY_AND_CODING_RULES.md` (Gemini-distilled invariants; companion)
- `LATENCY_OPTIMIZATION_AUDIT.md` (per-Part findings)
- `OPERATOR_DEPLOYMENT.md` (OS-level tuning beyond what code can do)
- `CLAUDE_INVARIANTS.md` (general engine-wide invariants)
- `KNOWN_ISSUES.md` (operational gotchas; some hot-path-related)
- v5.11 master plan: `plans/2026-05-06-MASTER-v5.11-optimization-sprint.md`
