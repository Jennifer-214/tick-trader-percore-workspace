---
type: refactor-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-13
tags: [latency-discipline, data-oriented-design]
surface: [hot-path, slow-path]
sister_specs: [cache-layout-discipline-for-hot-side-structs.md, latency-vs-cache-decision-framework.md, decision-first-cluster-layout-pattern.md]
applies_at_skills: []
---

# Loop fusion pattern (consolidate multi-pass iterations over shared data for cache + bandwidth)

**Established:** 2026-05-13 (codification post v5.15.5.B.8 ShardedSnapshot 4-walk → 1-walk consolidation; first explicit reference application)
**Status:** ACTIVE
**Cross-references:**
- Parent rule: `cache-layout-discipline-for-hot-side-structs.md` (HOT/WARM/COLD tiering enables cache-warm cluster sweeps inside fused loops)
- Sister: `decision-first-cluster-layout-pattern.md` (ND3 — forward-sequential layout amplifies fusion benefit via prefetcher)
- Sister: `latency-vs-cache-decision-framework.md` (cost reference; memory bandwidth costs section)
- Sister: `cross-thread-snapshot-publish-cluster-isolation.md` (ND1 — fused loops still respect cross-thread cluster boundaries)
- FoxML_Trader_v2 CLAUDE.md item 16 (reuse-audit before adding new code)
- FoxML_Trader_v2 CLAUDE.md item 17 (latency-additions tracking — fusion-based reductions are NEGATIVE-cost entries)
- FoxML_Trader_v2 CLAUDE.md item 28 (latency-vs-cache decision framework)

---

## Problem statement

When N independent operations all iterate the SAME data structure (e.g., `for (int i = 0; i < count; ++i)` over `arr[i]`), each pass triggers cold-cache refills of the same memory. The compiler usually CAN'T fuse these automatically when the loops have body-level side effects on different state.

The cost is bandwidth + cache-line-fill latency. Modern DRAM is ~50-100 GB/s peak, SHARED across cores + GPU + competing with cache writebacks. A workload that walks `cores[16] × 7 KB` four times per snapshot publish at 60 Hz burns 4 × 16 × 7 KB × 60 = **~26 MB/s** of DRAM bandwidth — small per-second, but compounds with concurrent producer fan-out (~80 MB/s on busy markets) + slow-path rolling-window updates (~30-50 MB/s). On a saturated bus, those reads STALL waiting for memory cycles.

The fix: **loop fusion** (also called "loop jamming" in the compiler literature). Merge N adjacent loops with identical iteration bounds into one loop body. Each `cores[i]` is fetched ONCE per pass; all N operations execute on the warm cache line; the line evicts only after all N are done.

This is THE canonical bandwidth-reduction pattern for snapshot-style workloads (one walk to populate many output fields). Distinct from loop tiling/blocking (cache-size-aware), loop interchange (loop-order swap), or loop unrolling (instruction-level parallelism).

---

## Design space explored

### Why not let the compiler do it?

Compilers `-O3` can fuse loops when:
- Iteration bounds are identical (compile-time-known)
- Bodies have no observable side-effect ordering constraints
- No data dependency between loop N+1's body and loop N's body that escapes the loop

But our cases ALL violate at least one constraint:
- Loop 1 (bitmap consistency) writes `state_flags = 0` THEN sets `BITMAP_CONSISTENT`
- Loop 4 (per_core publisher) writes other STATE_FLAG_SET bits later
- If the compiler reordered them, the final state_flags value would be wrong (Loop 4's bits would precede Loop 1's reset)

So the compiler conservatively keeps them separate. Manual fusion with explicit ordering preserves correctness while reaping the bandwidth win.

### Why not memcpy / SIMD / vectorize?

Fusion is COMPLEMENTARY to vectorization. After fusion, each loop iteration's body may itself be a candidate for AVX-512 / SIMD parallelism over the data fields. But fusion comes first — vectorizing N separate cold-cache walks doesn't help if the bandwidth bottleneck is the walks themselves.

Memcpy doesn't apply when the loop body performs computation (aggregation, conditional writes, FPN conversions), not bulk copy.

### Why not Struct-of-Arrays (SoA) layout?

For workloads where most consumers read ONE field from many elements, SoA outperforms AoS — each field is contiguous, so a per-field walk hits dense memory. In this codebase, `cores[16] × CoreContext` is AoS, and most consumers (snapshot publisher, slow-path) read MANY fields from each `cores[i]` per pass. AoS is the right choice; loop fusion reuses the AoS cache locality.

If a different consumer ever emerges that walks ONE field across many cores (e.g., a future "list all 16 cores' wins") then SoA could win for that consumer — but it's not the current shape.

### Why not just live with the bandwidth?

For boot-time or rare-event code, yes — bandwidth doesn't matter at 1 invocation/lifetime. But for PERIODIC workloads (snapshot publishing at 30-60 Hz, slow-path cycles at 1000 Hz/core), the bandwidth COMPOUNDS over hours. Plus it COMPETES with the producer thread's DRAM traffic — saving 20 MB/s on the GUI thread is 20 MB/s MORE for the producer to fan-out ticks.

---

## The pattern (concrete shape)

### Step 1 — Identify fusable loops

A loop is fusion-eligible if:
1. Same iteration bounds (same array, same `for (int i = 0; i < N; ++i)` shape)
2. Each body operates on `arr[i]` independently of `arr[j]` for `j != i` (no cross-element dependencies within the loop)
3. The combined body's variable scope is manageable (declarations in outer scope, results stored in outer-scope accumulators)

### Step 2 — Hoist shared declarations

Pull each loop's local declarations OUT of the loop, before the unified loop. Each becomes an outer-scope variable visible to the merged body.

### Step 3 — Merge bodies in original order

Preserve the original execution order of the loop bodies (Loop 1 body, then Loop 2 body, then ...). This guarantees observability semantics match the pre-fusion code.

If a loop had `break` to short-circuit (e.g., "find first AUTO core"), replace it with a flag (`bool found = false; if (!found && condition) { ...; found = true; }`). Breaking from the merged loop would skip subsequent iterations' work for OTHER consumers.

### Step 4 — Move post-loop computations

Code that ran AFTER the original loops (consuming aggregates) must also run AFTER the fused loop. Otherwise it reads pre-aggregation zeros.

### Step 5 — Verify byte-equivalent output

Run the test suite. Output fields populated by the publisher should be bytewise-identical pre/post-fusion.

---

## Worked example — v5.15.5.B.8 ShardedSnapshot consolidation

**Before** (`CoreFrameworks/ShardedSnapshot.hpp` pre-.B.8):

```cpp
// Loop 1: bitmap consistency (writes snap->per_core[c].state_flags)
for (int c = 0; c < state->registered_count && c < 16; ++c) {
    // ... uses xc->active, snap->positions[], partial_on ...
    snap->per_core[c].state_flags = 0;  // reset
    if (hot_any_active == gui_any_pos) {
        STATE_FLAG_SET(snap->per_core[c], BITMAP_CONSISTENT);
    }
}

// Loop 2: wins/losses aggregation
uint32_t total_wins = 0, total_losses = 0;
FPN<F> gross_wins = FPN_Zero<F>(), gross_losses = FPN_Zero<F>();
for (int i = 0; i < state->registered_count && i < 16; ++i) {
    total_wins += state->cores[i].core_wins;
    total_losses += state->cores[i].core_losses;
    gross_wins = FPN_Add(gross_wins, state->cores[i].core_gross_wins);
    gross_losses = FPN_Add(gross_losses, state->cores[i].core_gross_losses);
}
snap->wins = total_wins; snap->losses = total_losses;
// ... win_rate, avg_win, avg_loss, profit_factor, expectancy ...

// Loop 3: headline regime (first AUTO match)
int headline_regime = REGIME_RANGING;
for (int i = 0; i < state->registered_count && i < 16; ++i) {
    if (state->cores[i].strategy_id == STRATEGY_AUTO) {
        headline_regime = state->cores[i].regime_state.current_regime;
        break;  // <-- break-on-first-match
    }
}
snap->current_regime = headline_regime;

// Loop 4: per_core publisher (the BIG one, ~360 lines of body)
for (int i = 0; i < state->registered_count && i < 16; ++i) {
    snap->per_core[i].strategy_id_display = state->cores[i].strategy_id;
    // ... lots of per-field publishing ...
}
```

**After** (post-.B.8):

```cpp
// Hoisted declarations (was scattered between loops)
uint32_t total_wins = 0, total_losses = 0;
FPN<F>   gross_wins = FPN_Zero<F>(), gross_losses = FPN_Zero<F>();
int      headline_regime = REGIME_RANGING;
bool     headline_regime_set = false;  // replaces `break` in Loop 3
int      headline_ml_core = -1; /* etc. */

// One unified loop
for (int i = 0; i < state->registered_count && i < 16; ++i) {
    // Layer 1 (was Loop 1) — state_flags reset MUST precede other STATE_FLAG_SET
    {
        // ... bitmap consistency logic ...
        snap->per_core[i].state_flags = 0;
        if (hot_any_active == gui_any_pos) {
            STATE_FLAG_SET(snap->per_core[i], BITMAP_CONSISTENT);
        }
    }
    // Layer 2 (was Loop 2) — aggregates
    total_wins   += state->cores[i].core_wins;
    total_losses += state->cores[i].core_losses;
    gross_wins   = FPN_Add(gross_wins,   state->cores[i].core_gross_wins);
    gross_losses = FPN_Add(gross_losses, state->cores[i].core_gross_losses);
    // Layer 3 (was Loop 3) — flag-driven first-match, NO break
    if (!headline_regime_set && state->cores[i].strategy_id == STRATEGY_AUTO) {
        headline_regime = state->cores[i].regime_state.current_regime;
        headline_regime_set = true;
    }
    // Layer 4 (was Loop 4) — per_core publisher body, unchanged
    snap->per_core[i].strategy_id_display = state->cores[i].strategy_id;
    // ... ~360 lines unchanged ...
}

// Post-loop publishing (was scattered between loops)
snap->wins = total_wins; snap->losses = total_losses;
// ... win_rate, avg_win, etc. ...
if (state->registered_count > 0) {
    snap->current_regime = headline_regime;
}
```

**Bandwidth math:**
- Pre-.B.8: 4 walks × 16 cores × ~7 KB per CoreContext = **448 KB cold-cache reads / publish**
- At 60 Hz: 448 KB × 60 = **~26 MB/s**
- Post-.B.8: 1 walk × 16 × ~7 KB = **112 KB / publish** = ~6.5 MB/s
- **Net savings: ~20 MB/s** memory bandwidth (75% reduction)

**Latency math:** each cold-cache CoreContext fill = ~7 KB / 64 B per line = ~110 cache lines × ~100 ns/line = ~11 µs per walk. 3 saved walks × 16 cores = ~530 µs saved per snapshot publish.

**Cycle savings:** beyond bandwidth + latency, each saved walk avoids ~50 branch-condition checks (`i < state->registered_count && i < 16`) + 50 loop-increment ops. ~200 cycles saved per saved walk per publish.

**Total compounded:** at 60 Hz publish × 16 cores in saturated conditions:
- Bandwidth: ~20 MB/s freed = MORE budget for producer fan-out + slow-path rolling stats
- Latency: ~32 ms/sec of GUI thread time recovered (snapshot publisher runs ~5% less often per second)
- Cycles: ~10 µs/sec of CPU work eliminated (small but cumulative)

---

## Reference implementations

### Primary — v5.15.5.B.8 (this doc's first reference)

**Surface:** `CoreFrameworks/ShardedSnapshot.hpp` `TUI_CopySnapshotSharded`
**4 → 1 walk consolidation:** bitmap consistency + wins/losses aggregation + headline_regime + per_core publisher
**Net savings:** ~20 MB/s memory bandwidth at 60 Hz publish

### Future candidate applications

The pattern generalizes — any per-iteration workload with multiple consumers of the same data:

- `EngineSharded.hpp` slow-path body — currently `EventLoop_UpdateRollingStateOneCore` + `RebuildOneCore` + `TimeExitOneCore` + `TrailingSLRatchetOneCore` are 4 separate per-core passes inside the slow-path tick. Each pulls slow_state + cores[c] into cache. Fusable IF the inter-pass data dependencies (rolling state writes → regime read → strategy dispatch → trail SL trail) can be re-checked for ordering.
- `Backtest/BacktestEngine.hpp` walk-forward per-fold loops (less critical; runs at startup, not periodic)
- `ML_Headers/CoreModelZoo.hpp` ensemble-aware path's per-horizon walks (only relevant if multiple consumers of per-horizon data emerge)

`/dod-audit` should flag MISSED applications when it detects:
- 2+ adjacent `for (int i = 0; i < N; ++i)` loops over the same array/index variable
- Each loop body reads `arr[i].FIELDS` and writes either local accumulators OR `output[i].FIELDS`
- No cross-iteration dependency within either loop

---

## Trade-offs + when to apply

### Apply when:
- 2+ loops with the SAME iteration bounds over the SAME data structure
- Each loop body operates on `arr[i]` independently (no cross-element coupling within the loop)
- Cadence is periodic / hot enough that the saved bandwidth × frequency matters (60 Hz snapshot publishing, 1000 Hz slow-path)
- Output preservation is feasible (post-loop computations can be moved after the fused loop)

### Skip when:
- One loop's body materially depends on a SHARED COMPUTATION COMPLETED across all `i` (e.g., a sum that's needed mid-walk — keep the separate pre-pass)
- Loops use DIFFERENT iteration counts (e.g., Loop A iterates 0..16, Loop B iterates 0..N where N is computed mid-walk). Fusion would require careful gating; may not be worth the complexity.
- The merged body would exceed reasonable readability (>500 LOC of body code accumulated). Consider EXTRACTING the consolidation work into a helper function instead.
- One-shot / boot-only loops where bandwidth doesn't matter (e.g., struct field init at engine boot — `EventLoopState_Init` already has separate per-core init loops but they run ONCE per program lifetime, so fusion's bandwidth win is irrelevant).

### Cost:
- ~30-50 LOC reshuffling per pair of fused loops (hoisting declarations + merging bodies + relocating post-loop computations)
- Mental overhead: future contributors must understand which "layer" of the fused body their new field belongs to. Comment liberally with `// Layer N (was Loop X)` markers.
- Risk: changing iteration order or breaking observability invariants. Mitigated by byte-equivalence regression tests against PerCoreSnap output.

### Win:
- Direct: cache-line refills × N → ×1 = (N-1)/N bandwidth reduction
- Indirect: lower contention with concurrent threads on the DRAM bus
- Compounds with HOT/WARM/COLD layout (per `cache-layout-discipline-for-hot-side-structs.md`) — once `cores[i]` is in cache from Layer 1's first touch, Layers 2-N hit warm lines through the H/W/C clusters established in `.B.1`
- Compounds with `ND1` cluster isolation — the fused loop's WRITES to `snap->per_core[i].*` don't invalidate cross-thread atomics in `sp_telemetry` (which lives on its own cache line)

---

## Lessons / gotchas

### `break` becomes a flag

If the original loop short-circuited (e.g., "find first AUTO core, break"), the fused loop CAN'T break — that would skip subsequent cores' work for OTHER consumers in the merged body. Use a flag instead:

```cpp
// Before fusion:
for (int i = 0; i < N; ++i) {
    if (cond(i)) { result = compute(i); break; }
}

// After fusion (inside merged loop):
if (!found && cond(i)) {
    result = compute(i);
    found = true;  // subsequent iterations skip the if-body but stay in the loop
}
```

The branch predictor learns the flag pattern quickly — typically <5 mispredicts before convergence; ~0% mispredict steady-state.

### Ordering invariants on shared write targets

If multiple original loops wrote to the same output field (e.g., `snap->per_core[i].state_flags`), the merged loop MUST preserve the write order. In `.B.8`'s case, Loop 1's `state_flags = 0` reset MUST occur before Loop 4's STATE_FLAG_SET calls. Place Layer 1 first in the merged body.

### Aggregates must be hoisted + post-published

Local declarations like `uint32_t total_wins = 0` that lived between original loops need to move OUTSIDE the fused loop (so they're accumulated across iterations) AND the snap-publishing assignments that consumed them need to move AFTER the fused loop closes. Common bug pattern: aggregates accumulate but the publishing assignment is left in its original position (still before the fused loop), reading 0.

### Test-binary-only verification

Use the `print_layout_fingerprint()` style probe to confirm output fields are bytewise-identical pre/post-fusion. The existing 3027-test regression at controller_test.cpp catches most divergences; cross-reference with `tests/parity_harness.cpp` for snapshot-level byte-equivalence.

### Cross-thread cache invalidation interaction

When the fused loop writes to `snap->per_core[i].state_flags` (single-writer per i), and a different thread (GUI) reads the same cache line at a different cadence, false sharing is a concern. `ND1` cluster isolation pattern + `alignas(64)` per-core fence boundaries on PerCoreSnap mitigate this — but verify the layout still places `state_flags` on a line that's NOT shared with cross-thread fields. The per-snapshot-cluster-layout-pattern.md cluster boundaries handle this for the .B.8 case.

### Compiler unroll interaction

For SMALL iteration counts (e.g., 5 or 16) the compiler at `-O3` may automatically unroll the fused loop. This compounds with fusion: instead of N walks of 16 iterations + branch overhead, you get 1 walk × 16-way unrolled body. `#pragma GCC unroll N` documents intent + may force unroll the compiler heuristic missed. Skip for LARGE bodies (AUTOPOPULATE-style multi-statement bodies) — code-bloat outweighs branch savings.

---

## Memory bandwidth context (why this matters)

For developers new to bandwidth-bound performance work:

| Resource (Tiger Lake reference) | Peak rate | Cost per cache line (64 B) |
|---|---|---|
| L1d cache | ~48 KB per core | ~1 ns |
| L2 cache | ~1.25 MB per core | ~4 ns |
| L3 cache | ~12 MB shared | ~13 ns |
| **DRAM** | **~50-100 GB/s peak, SHARED across all cores + GPU + integrated graphics** | **~100 ns** |

The trap: DRAM bandwidth is shared. A workload that burns 26 MB/s ON ITS OWN looks tiny vs the ~50 GB/s peak. But:
- Saturated markets generate ~10-50 MB/s of WS tick traffic that the producer thread must fan out
- Per-core slow-path rolling-window updates burn ~5-10 MB/s each × 16 cores = 80-160 MB/s
- ML inference (when active) burns another ~50-100 MB/s on feature pack + model read
- Snapshot publisher's 26 MB/s competes with all of these

When the DRAM bus is saturated, EVERY thread stalls waiting for memory cycles — even ones that THINK they're CPU-bound. The compute units sit idle. Hence the term "bandwidth-bound" — adding more compute or cores doesn't help; the memory subsystem is the bottleneck.

Loop fusion is one of the cheapest ways to reduce bandwidth pressure: structural change that requires zero hardware investment, preserves all output semantics, and compounds with cache-layout discipline.

---

## Audit detection (`/dod-audit` integration)

`/dod-audit` should flag MISSED loop-fusion opportunities by:

- **Symptom 1:** Multiple adjacent `for` loops with identical iteration bounds (same array, same `i < N` form) where each body reads `arr[i].FIELDS`.
- **Symptom 2:** A "preamble loop" that aggregates (sum/max/find-first) followed by a "publish loop" that uses the aggregates — fusion preserves the structure IF aggregate-publishing moves post-loop.
- **Symptom 3:** Cadenced workloads (snapshot publishers, periodic state-export functions) with 3+ separate `for (int i = 0; i < N; ++i)` walks of the same data structure.

When detected → flag as `MISSED — loop-fusion-pattern`. Recommended fix: hoist declarations + merge bodies (preserve order) + move post-loop computations + flag any `break`-eligible loops for flag-driven first-match conversion.

---

## Patterns NOT covered here (and why)

### Loop tiling / blocking (cache-size-aware)

When the working set per loop exceeds cache, tiling splits the iteration into chunks that fit. Different concern from fusion; orthogonal axis. Apply when iteration count × per-iteration footprint > L1d/L2.

### Loop interchange (loop-order swap)

When nested loops access memory in a non-stride-friendly order, swapping loop nesting (outer/inner) can improve locality. Different concern; specific to nested-loop patterns. AoS vs SoA layout decisions inform this.

### Loop unrolling (instruction-level parallelism)

`#pragma GCC unroll N` or manual unrolling — duplicate the loop body N times to reduce branch overhead + expose instruction-level parallelism. Complementary to fusion: fuse FIRST (one walk), then consider unrolling the fused body if it's small enough.

### Software prefetching (`__builtin_prefetch`)

Hint to the cache hierarchy that a future line will be needed, allowing it to fetch ahead of demand. Complementary to fusion: prefetch can hide the latency of the line BEFORE the unified walk reaches it. Apply on cold-cache scenarios where prefetcher's stride detection can't fire (random access, large strides).

### Memory-mapped I/O / mmap arena

Different mechanism — minimize DRAM traffic by sharing pages between processes. The decoupling-roadmap (`plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`) envisions mmap-mediated GUI/engine separation that would further reduce snapshot-publish bandwidth (the GUI process mmap's the cores[] / display_meta[] arrays read-only; no copy through TUISnapshot).

---

## Cross-references

- `cache-layout-discipline-for-hot-side-structs.md` Rule 4 (HOT/WARM/COLD tiering — enables cache-warm walks inside fused loops)
- `decision-first-cluster-layout-pattern.md` (ND3 — forward-sequential ordering amplifies fusion's prefetcher benefit)
- `cross-thread-snapshot-publish-cluster-isolation.md` (ND1 — alignas isolation preserves correctness when fused loops write to per_core fields)
- `display-execution-invariant-registry-pattern.md` (ND2 — registry-driven snapshot population works naturally inside fused publisher loops)
- `latency-vs-cache-decision-framework.md` (cost reference; memory bandwidth costs subsection)
- `autopopulate-pattern-for-production-caller-class.md` (alternative consolidation pattern at call sites; fusion is loop-level, AUTOPOPULATE is field-level)
- FoxML_Trader_v2 CLAUDE.md item 16 (reuse-audit before adding new code — fusion is the loop-level analog)
- FoxML_Trader_v2 CLAUDE.md item 17 (latency-additions tracking — fusion-based reductions log as NEGATIVE-cost entries)
- FoxML_Trader_v2 CLAUDE.md item 28 (latency-vs-cache decision framework)
- FoxML_Trader_v2 `CoreFrameworks/ShardedSnapshot.hpp` `TUI_CopySnapshotSharded` (first explicit reference; v5.15.5.B.8)

## Promotion criteria (this doc was promoted)

Pattern first applied explicitly in v5.15.5.B.8. The technique itself is well-established in compiler-optimization + HPC literature ("loop fusion" / "loop jamming") but this codebase had no prior named application until `.B.8` audit surface. Operator observation 2026-05-13 ("i didnt know that was a thing... we should save design specs for optimizing memory bandwidth") triggered codification.

Re-evaluate when 2nd or 3rd application surfaces (likely candidate: slow-path body's 4 per-core passes if the inter-pass dependencies can be re-checked). Update reference table with each new application + cross-reference any new memory-bandwidth patterns discovered.
