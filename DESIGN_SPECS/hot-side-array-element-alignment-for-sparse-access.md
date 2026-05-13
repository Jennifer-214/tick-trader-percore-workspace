# Hot-side array-element alignment for sparse-access struct arrays

**Established:** 2026-05-13 (v5.15.5.C.5)
**Status:** ACTIVE
**Cross-references:**
- CLAUDE.md item 7 (memory hierarchy / cache discipline)
- CLAUDE.md item 12 (display ↔ execution invariant)
- CLAUDE.md item 17 (latency tracking)
- CLAUDE.md item 18 (slow-path branch + cycle minimization)
- CLAUDE.md item 28 (latency-vs-cache decision framework)
- `cache-layout-discipline-for-hot-side-structs.md` (Rule 2 covers TIGHT-PACK: struct fits in 1 line. **THIS spec covers MULTI-LINE structs where hot subset fits in 1 line** — complementary)
- `per-snapshot-cluster-layout-pattern.md` (sister; cross-thread snapshot alignas; this spec is the SINGLE-THREAD sparse-access analog)
- `function-struct-alignment-for-single-mov-access.md` (sister; prerequisite 3 mentions cache alignment; this spec gives the array-element case)
- `latency-vs-cache-decision-framework.md` (cost framework for memory-pad vs cache-line-saved trade-off)
- `decision-first-cluster-layout-pattern.md` (sister; intra-cluster field ordering)

---

## Problem statement

Codebases that pack many struct instances into arrays (per-slot, per-core, per-record) frequently encounter a HIDDEN cache-line-straddle pattern:

1. Struct `T` lives in an array `T arr[N]`
2. Hot path iterates `arr[]` via SPARSE access (bitmap-driven, indexed lookup; NOT linear scan)
3. Each hot-path access reads a SUBSET of fields per element (typically the first 1-2 cache lines of fields; ignores the remainder)
4. `sizeof(T)` is > 1 cache line (64B) but is NOT a clean multiple of 64

When all 4 conditions hold, the hot path's per-element read STRADDLES cache lines for most array indices N>0. Specifically: `addr(arr[N]) = base + N × sizeof(T)`. If `sizeof(T) mod 64 != 0`, then `addr(arr[N]) mod 64` cycles through values 0, sizeof(T) mod 64, 2·sizeof(T) mod 64, ..., creating per-N alignment-within-cache-line variation. Most N values land the hot-field subset across a cache line boundary.

**Concrete example (FoxML_Trader_v2 Position pre-v5.15.5.C.5):**
- `Position` size = 216B (3.375 cache lines per record)
- `Position[16]` array iterated via active_bitmap walk in `BG_Evaluate` / `SG_Evaluate` (hot path)
- Hot path reads `take_profit_price` (offset 0, 24B) + `stop_loss_price` (offset 24, 24B) = 48B per active slot
- For N=1: Position[1] starts at byte 216 = cache line 3 byte 24 → TP+SL straddles lines 3 and 4
- For N=4: Position[4] starts at byte 864 = cache line 13 byte 32 → TP+SL straddles lines 13 and 14
- Pattern: ~50%+ of slot accesses straddle 2 cache lines instead of 1

The hot path pays 2× cache lines per active slot vs the physical minimum (1 line for 48B of data).

---

## The pattern

For arrays of multi-cache-line structs accessed sparsely on hot path, **make `sizeof(T)` a multiple of the cache-line size (typically 64B)** via either:

### Approach A — `alignas(64)` on struct definition

```cpp
template <unsigned F>
struct alignas(64) Position {
    // ... fields totaling 184B ...
    // alignas(64) auto-pads sizeof(Position<F>) to 192B (next 64B multiple)
};
static_assert(sizeof(Position<64>) == 192, "alignas(64) padded to 3 cache lines exact");
```

- Compiler pads `sizeof` to next 64B multiple
- Each `arr[N]` starts on 64B boundary regardless of container alignment
- Documents intent at struct definition
- Cost: padding bytes (up to 63 per element)

### Approach B — manual layout to hit 64B multiple

```cpp
template <unsigned F>
struct Position {
    // Carefully order fields to total EXACTLY 192B (or 128B, 256B, etc.)
};
static_assert(sizeof(Position<64>) == 192, "manual layout hits 3-line multiple");
```

- No `alignas` decorator needed; size happens to fit
- More fragile (struct grows → falls off the cache-line multiple)
- Same cache-line-aligned access guaranteed IF container is also 64B-aligned

**Recommendation:** Use Approach A (`alignas(64)` explicit) unless eliminating the padding is essential. Explicit `alignas` documents intent + survives future field additions (compiler re-pads automatically).

### Both approaches: array iteration becomes predictable

```cpp
// Hot path:
for (int slot = __builtin_ctz(active_bitmap); slot < MAX_SLOTS; ...) {
    if (arr[slot].take_profit_price >= last_price) ...   // 1 cache line; aligned
    if (arr[slot].stop_loss_price <= last_price) ...      // SAME 1 cache line; aligned
}
```

Each `arr[slot].TP` or `.SL` read hits the same first cache line of `arr[slot]`. The 2nd-to-Nth cache lines of each element are NOT pulled. Hot-path cache footprint per active slot = 1 line, regardless of element size.

---

## When to apply

ALL of the following:
1. **Array context** — struct lives in `arr[N]` with N > ~4 (otherwise padding waste outweighs benefit)
2. **Sparse iteration** — hot path iterates a subset (bitmap-driven, slot-index lookup); NOT linear scan over all elements
3. **Hot-field subset** — hot path reads ≤ ~48B of fields per element (fits in first cache line)
4. **Struct size > 64B** AND not naturally aligned — if `sizeof(T)` already happens to be 64, 128, 192, 256, etc., no `alignas` needed (Approach B happens for free)

## When NOT to apply

- **Struct size ≤ 64B** — fits in 1 cache line per element regardless of N; this spec doesn't apply. Use `cache-layout-discipline-for-hot-side-structs.md` Rule 2 (tight-pack) instead.
- **Linear iteration** — if hot path reads ALL N elements sequentially, prefetcher handles straddle. `alignas` adds padding without saving cache lines.
- **Dense field access** — if hot path reads more than first cache line of each element (rare for hot path), per-element cost doesn't reduce; alignas just adds padding.
- **Container is itself misaligned** — if `arr` (the array container) is at an unaligned address, alignas(64) on each element still helps relative alignment but absolute cache-line behavior depends on container. Verify container alignment too.
- **Rare access pattern** — if hot path rarely touches `arr[]`, padding cost outweighs alignment benefit.

---

## Reference implementations (retroactive + new)

The discipline has been applied AD-HOC in the codebase since before this spec existed. This section retroactively documents existing applications + the v5.15.5.C.5 new canonical application.

### Retroactive applications (alignas(64) was already in use)

- **`PerCoreSnap`** (v5.14.10.0; `per-snapshot-cluster-layout-pattern.md` first-application reference) — cross-thread snapshot publishing for the bandit telemetry cluster. Used `alignas(64)` for false-sharing prevention (cross-thread concern). This spec's purpose differs (single-thread sparse access on hot path) but the alignas mechanism is shared.
- **`OrderManagerState` cluster reorg** (v5.15.5.C.1) — HOT/WARM/COLD cluster reorganization with per-cluster `alignas(64)` boundaries. Single-instance struct (not array), so this spec doesn't directly apply, but the alignas discipline does.
- **`CoreContext`** (v5.15.5.B.1) — per-core state struct iterated via active-core bitmap. `alignas(64)` applied during the .B.1 cluster reorg. Now retroactively documented as a v5.15.5.C.5-spec application.

### New canonical application: v5.15.5.C.5 — Position struct

- Surface: `CoreFrameworks/Portfolio.hpp` Position struct
- Pre-C.5 size: 216B (POS.2 absorbed SKIP_PERSIST fields exit_fill_price + is_maker)
- Pre-C.5 cache behavior: straddles for most N (hot path TP+SL fits in first cache line of Position but Position[N] start address misaligned)
- C.5 changes:
  - Revert POS.2 SKIP_PERSIST fields back to OMS sibling arrays (per `slot-state-foreach-registry-with-storage-routing.md` decision tree's ephemeral-sibling-array preference for sparse-access state)
  - Position size: 184B (9 PERSIST fields + 7B explicit `_pad_pos` for wire-format compatibility)
  - Add `alignas(64)` → padded to 192B = 3 cache lines exact
  - Per-slot hot-path access: **guaranteed 1 cache line** for the 48B TP+SL read
- Wire format byte-identical (PORTFOLIO_SNAPSHOT_VERSION=5 unchanged; PERSIST_BYTES=184 unchanged; SKIP_PERSIST fields move to OMS sibling arrays which are not persisted)
- Companion: `last_exit_fill_price[16]` (FPN<F>[]; 384B at OMS level) + `last_is_maker_bitmap` (uint16_t; 2B at OMS level via FOREACH_OMS_FIELD)
- Net memory: roughly even with pre-C.5 (Position -24B per slot × 16 = -384B; sibling arrays +386B; net +2B)

### Future application candidates

- **`Order`** (Order.hpp) — array iterated via order bitmap; verify in C.5 audit
- **`ExitRecord`** (Portfolio.hpp) — already 56B (1 cache line); doesn't require alignas
- **FlowFeatures, ConfidenceScorer** (`.D` + `.E` future sweeps) — apply this spec OR `cache-layout-discipline-for-hot-side-structs.md` (HOT/WARM/COLD tiering) depending on whether each surface is array-of-struct or single-instance

---

## Trade-offs

### Wins

- **Hot-path cache footprint cut to physical minimum.** 1 cache line per active slot for the hot-field subset, regardless of element size beyond that. For Position: pre-C.5 ~50% of slots straddle (2 lines); post-C.5 0% straddle (1 line guaranteed).
- **Predictable cache behavior across all N values.** No alignment surprises for specific slot indices.
- **Survives future field additions to element struct.** Adding fields past the first cache line doesn't break hot-path discipline (still fits in first line); compiler re-pads sizeof at recompile.
- **Documents intent at struct definition.** `alignas(64)` makes the cache discipline visible to readers.
- **Reusable across codebase.** Pattern applies to any hot-side struct-in-array with sparse-subset access. Already 3-4 existing surfaces + multiple future surfaces.

### Costs

- **Padding bytes per element.** Up to 63B per element worst case. For Position: 8B per record × 16 = 128B per OMS. Marginal at typical struct counts.
- **Slightly larger array footprint.** May matter if total array size is near L1/L2 cache budget. Verify with bench gate (CLAUDE.md item 17).
- **`alignas(64)` placed on user-defined type may interact with allocator alignment.** Stack arrays are fine; heap allocation via `malloc` may not preserve 64B alignment (compiler may handle for stack; heap requires `aligned_alloc(64, sizeof(T))` per `shadow-load-state-transition-pattern.md`).

### Decision framework (per CLAUDE.md item 28)

```
Memory cost = (padding_per_element × N_elements)
Latency saved = (1 cache_line × hot_path_access_freq × N_active_elements_per_access)

If saved cache misses × ~100ns ≫ wasted memory bytes × ~0ns: APPLY
Typical case: 8-40B padding per element vs ~100ns/cache-miss per hot-path access → easy win
```

---

## Implementation checklist

When applying this pattern to a new surface:

- [ ] Verify the 4 conditions (array context + sparse iteration + hot-field-subset + struct > 64B not aligned)
- [ ] Identify the hot-field subset (which fields does hot path read per element?)
- [ ] Verify hot subset fits in the FIRST cache line (≤ 64B); reorder fields if needed so hot fields are at offset 0..63
- [ ] Apply `alignas(64)` to struct definition
- [ ] Add `static_assert(sizeof(T) == expected_multiple_of_64)` to lock layout
- [ ] Add `static_assert(offsetof(T, hot_field_1) == 0)` etc. for each hot field to lock ordering
- [ ] Verify container alignment if container is non-trivially-located (often `alignas(64)` on parent struct or `aligned_alloc(64)` on heap)
- [ ] Bench gate spot-check (CLAUDE.md item 17 latency-track + v5.15.5.C.3 Phase 7.B runtime-bench-gate substrate) before/after to verify hot-path cycle delta

---

## Anti-patterns

### Applying alignas without verifying conditions

Adding `alignas(64)` to every struct out of "discipline" wastes memory. Apply only where the 4 conditions hold.

### Trusting first-element-only alignment

`alignas(64)` on the array (e.g., `alignas(64) T arr[N]`) only aligns `arr[0]`. Subsequent `arr[N]` align only if `sizeof(T)` is a multiple of 64. Apply alignas to the STRUCT, not just the array.

### Confusing this spec with `per-snapshot-cluster-layout-pattern.md`

The sister spec is about CROSS-THREAD snapshot publishing (false-sharing prevention). This spec is SINGLE-THREAD sparse access (cache-line-straddle reduction). The mechanism (alignas(64)) is shared; the motivations differ. Cross-ref both when relevant.

### Forgetting hot-field-order constraint

If hot fields are NOT at the first 64B of the struct, alignas(64) doesn't help. Reorder fields so hot subset (TP/SL/etc.) comes FIRST. Combine with `decision-first-cluster-layout-pattern.md`.

---

## Cross-references to CLAUDE.md

This pattern complements:
- **Item 7** (memory hierarchy): the framework that motivates per-element cache discipline
- **Item 12** (display ↔ execution invariant): orthogonal concern; spec doesn't address invariant but co-existence with hot-path discipline matters
- **Item 17** (latency tracking): every alignas application gets HOT_PATH_CHANGELOG entry per item 17
- **Item 18** (slow-path latency reduction): if struct is on slow path (not hot), this spec may still apply but with different cost-benefit math
- **Item 28** (latency-vs-cache framework): the analytical foundation for the trade-off

**Promotion candidate to CLAUDE.md item 29+ after 4+ applications shipped:**
- v5.15.5.C.5 Position (new)
- PerCoreSnap (retroactive)
- OrderManagerState clusters (retroactive)
- CoreContext (retroactive)

That's 4 applications now. Promotion-ready.

---

## Related design patterns

- `cache-layout-discipline-for-hot-side-structs.md` (Rule 2 covers SMALL-element 1-line tight-pack; this spec covers LARGE-element first-line alignment)
- `per-snapshot-cluster-layout-pattern.md` (cross-thread alignas; sister mechanism, different motivation)
- `decision-first-cluster-layout-pattern.md` (intra-struct field ordering; complementary)
- `function-struct-alignment-for-single-mov-access.md` (single-element access discipline; this spec extends to array case)
- `slot-state-foreach-registry-with-storage-routing.md` (decision tree: when ephemeral fields go to OMS sibling arrays vs persistent fields stay in Position; complements this spec's alignment discipline)
- `latency-vs-cache-decision-framework.md` (cost model)

---

**End of spec.**
