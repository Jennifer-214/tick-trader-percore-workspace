---
type: data-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-05-12
tags: [data-oriented-design, latency-discipline, concurrency]
surface: [hot-path, slow-path]
sister_specs: [cache-line-discipline.md, decision-first-cluster-layout-pattern.md, latency-vs-cache-decision-framework.md, per-snapshot-cluster-layout-pattern.md, cross-thread-snapshot-publish-cluster-isolation.md]
applies_at_skills: []
---

# Cache-Layout Discipline for Hot-Side Structs

**Status:** generalized pattern (formalized 2026-05-12 during v5.15.5
pre-coding cache audit).
**CLAUDE.md cross-ref:** items 7 (memory hierarchy), 16 (reuse audit),
17 (latency tracking), 19 (structural fix preferred), 20 (bit-packed
flags), 27 (struct padding determinism).

## Problem space

C++ structs touched by hot/slow-path code accumulate fields over time:
- Telemetry/debug fields ("arm_names[8][32]", "history rings", "last_*"
  scalars)
- Display-only data (names, descriptions, tooltips)
- Compositional state (sub-structs, per-arm arrays, posterior states)
- Cross-thread shared atomics (snapshot heads, kill flags)

Without explicit cache-layout discipline, these accumulate inside
hot-side structs, causing:
1. **Cache-line bloat:** each per-cycle access pulls multiple cache
   lines where only one carries useful data
2. **False sharing:** cross-thread writes to one field invalidate
   neighboring fields on the same line for other cores
3. **L1 pressure:** large structs evict other slow-path data; cycle-N
   eviction shows up as cycle-N+1 cache miss

This doc captures three reusable rules from v5.15.5 cache audit
(operator framing: "we should audit for more issues like this around
the bandit and thompson as well" + "the findings can probably be
generalized").

## Rule 1 — Extract display-only fields out of hot-side structs

**Pattern.** Hot-side structs (touched per cycle by slow-path /
hot-path / OMS drainer) should contain ONLY data needed by those paths.
Display-only fields (names, descriptions, human-readable metadata) move
to a separate display-meta struct accessed only by GUI rendering.

**Anti-pattern (caught in v5.15.5 cache audit):**

```cpp
struct BanditState {                     // touched per slow-path cycle
    double weights[8];                   // 64B = 1 line — hot data ✓
    double cum_reward[8];                // 64B = 1 line — hot data ✓
    int    pulls[8];                     // 32B = 0.5 line — hot data ✓
    char   arm_names[8][32];             // 256B = 4 lines — DISPLAY ONLY ✗
    int    n_arms;                       // 4B
    int    total_steps;                  // 4B
    double gamma;                        // 8B
    // ... more scalars ...
};
```

`arm_names` is set at Init time, read at MLStatusPanel render. Never
touched by `Bandit_GetProbabilities` or other slow-path code. But its
256B sit in the middle of the struct → per-cycle access of weights /
cum_reward pulls in 4 lines of arm_names "noise."

**Fix:**

```cpp
struct BanditState {                     // hot side — slim
    double weights[8];                   // 64B = 1 line
    double cum_reward[8];                // 64B = 1 line
    int    pulls[8];                     // 32B = 0.5 line
    int    n_arms;
    int    total_steps;
    double gamma;
    double eta_max;
    double blend_ratio;
    int    min_samples;
    int    ramp_up_samples;
    // Total: ~204B = 4 lines (down from 8 lines)
};

struct BanditDisplayMeta {               // display side — separate
    char arm_names[8][32];               // accessed only by MLStatusPanel
};
```

Access via `ezoo->bandit_display[regime_id].arm_names[i]` from GUI;
slow-path doesn't touch `bandit_display` at all.

**Heuristic for "is this field display-only?":**
- grep for the field name → if all reads are in `GUI/` or
  `DataStream/EngineTUI.hpp` or post-render code, it's display-only
- Test: comment out the field declaration and recompile. If only
  GUI/TUI files fail to compile, it's display-only.

**Savings rule-of-thumb:** each cache line extracted saves ~100 ns per
cold-cache slow-path access. For NUM_REGIMES=5 regimes × ~4 lines of
arm_names each = 5 × 400 ns = 2000 ns saved per regime-switch cycle.

## Rule 2 — Tight-pack frequently-accessed-together arrays into single cache lines

**Pattern.** Per-item arrays (per-arm, per-horizon, per-core) accessed
together in a slow-path loop should fit in 1 cache line. 16 floats
(64B) is the canonical size for "8 items × 2 fields each" tight-pack.

**Anti-pattern (caught in v5.15.5 cache audit):**

Pre-v5.15.5 barrier reads — accessed `ezoo->primary_handles[h].label_tp_pct`
for h=0..7. Each handle is ~512B; field at offset ~349 lands in line 5
of each handle. 8 different handles → 8 separate cache-line fetches
(even though handles are stored contiguously, the field offsets cause
strided access).

**Fix (v5.15.5):**

```cpp
struct EnsembleModelZoo {
    // ... existing fields ...

    // Tight-pack per-arm barriers: 16 floats × 4 = 64B = 1 cache line.
    // Single-writer at boot (CoreModelZoo_TryLoadRole copies from
    // handle->label_tp_pct AT LOAD TIME alongside the handle write).
    // Slow-path reads all 16 floats in one L1 fetch.
    alignas(64) float per_arm_barriers[16];  // [0..7]=tp, [8..15]=sl
};
```

Boot-time pack mirrors the existing per-handle write:

```cpp
// In CoreModelZoo_TryLoadRole, after handle->label_tp_pct write:
ezoo->per_arm_barriers[arm_idx]      = (float)FPN_ToDouble(sr.label_tp_pct);
ezoo->per_arm_barriers[arm_idx + 8]  = (float)FPN_ToDouble(sr.label_sl_pct);
```

**Tight-pack sizing reference:**
- 8 floats = 32 bytes = 0.5 line — pair with another 8 floats to fill a line
- 16 floats = 64 bytes = 1 line — ideal
- 8 doubles = 64 bytes = 1 line — for higher precision
- 4 doubles + 8 floats = 32 + 32 = 64 bytes = 1 line — mixed type

**When NOT to tight-pack:** if the items aren't accessed together (e.g.,
arm_names are only accessed individually at GUI render), tight-packing
buys nothing and hurts cache locality elsewhere.

**Branchless compatibility:** tight-pack arrays are ideal for AVX-512
vectorization (CLAUDE.md item 25): 16 floats = 1 ZMM register. Per-item
mask-multiply with `_mm512_mul_ps` consumes the whole array in one
instruction.

## Rule 3 — Isolate cross-thread shared fields via alignas (false-sharing prevention)

**Pattern.** Fields read or written by MULTIPLE threads (GUI thread,
producer thread, persistence thread) MUST sit on their own cache line,
not share with single-writer hot-side data. Use `alignas(64)` on the
shared field AND `alignas(64)` on the next field to force compiler
padding.

**Anti-pattern (caught in v5.15.5 shadow-mode design):**

```cpp
struct BarrierShadowRing {
    uint64_t head;                       // atomic — written by slow-path,
                                         // read by GUI
    BarrierShadowRecord records[256];    // single-writer slow-path
    // PROBLEM: head and records[0] share cache line 0.
    // GUI's atomic-load of head causes cross-core read → invalidates
    // slow-path writer's line → next records[0] write incurs full
    // cache-line bounce (100-200 ns penalty per GUI poll).
};
```

**Fix:**

```cpp
struct BarrierShadowRing {
    alignas(64) uint64_t head;                       // 8B; own line
    alignas(64) BarrierShadowRecord records[256];    // own line+ (compiler pads
                                                     //   between head and records)
};
```

`alignas(64)` on `records` forces it to start on a fresh 64-byte
boundary. Compiler inserts ~56 bytes of padding between head and
records implicitly. Identical runtime layout to explicit `_pad[]`
arrays but cleaner source.

**When to use explicit `_pad = 0` field instead of alignas:** if the
struct is used in a byte-equivalence context (memcmp / SHA-256 /
wire format / HMAC), implicit compiler padding is UB-readable
(uninitialized bytes leak through bytewise compares). Use
`int32_t _pad = 0;` default-init fields per CLAUDE.md item 27.
Runtime-only structs (like BarrierShadowRing) can use alignas alone.

**Heuristic for "is this field cross-thread shared?":**
- Atomic load/store from any thread that isn't the writer → YES, isolate
- Snapshot fields read by GUI thread → YES, isolate
- Single-writer + single-reader on same thread (e.g., slow-path read
  + slow-path write) → NO isolation needed

## Rule 4 — Hot/Warm/Cold field clustering by access frequency

**Pattern.** Large structs accumulate fields with very different access
frequencies. Treating them all as a homogeneous blob causes the
slow-path-cycle-N access of HOT fields to pull WARM and COLD fields
into L1 too (cache pollution), AND causes COLD-field writes (init,
persistence, display) to invalidate HOT cache lines.

**Tier classification:**

| Tier | Access frequency | Examples |
|---|---|---|
| **HOT** | Every slow-path cycle (or hot path per tick) | `weights_buf`, `per_arm_barriers`, `current_regime_id`, prediction outputs, gate flags |
| **WARM** | Every N cycles or on transitions | regime transition state, Ridge state, ratchet state, lazy-rebuild gates |
| **COLD** | Once at boot / rarely / display only | init flags, persistence paths, blend mode strings, debug counters, name buffers |

**Layout structure:**

```cpp
struct alignas(64) EnsembleModelZoo {
    // ==== HOT cluster (lines 0-2; touched every slow-path cycle) ====
    alignas(64) float per_arm_barriers[16];     // 64B = 1 line
    alignas(64) ModelHandle primary_handles[8]; // ~4KB = 64 lines (separate)
    // ... other per-cycle fields ...

    // ==== WARM cluster (lines N+1..N+M; touched per N cycles) ====
    alignas(64) RidgeWeights<F> ridge_state;
    alignas(64) RidgeWeights<F> exit_ridge_state;
    int regime_transition_cycles_remaining;
    int prev_regime_id;
    // ... per-transition fields ...

    // ==== COLD cluster (lines M+1..end; touched once or rarely) ====
    alignas(64) char bandit_save_path[400];
    alignas(64) char blend_mode[16];
    uint8_t init_flags;  // bit-packed (see Rule 5)
    // ... init/persistence/display fields ...
};
```

**Benefit:** slow-path cycle-N reads HOT cluster (1-3 cache lines)
without pulling WARM/COLD into L1. WARM cluster gets pre-warmed by
its own occasional access. COLD cluster stays in main memory until
needed.

**Precedent (v5.14.10.0):** PerCoreSnap was audited and reorganized
this way. Original layout had display-fields adjacent to hot-snap
fields; per-snapshot-cluster-layout-pattern.md formalized the tier
clustering. Bandit telemetry cluster (Exp3 + Thompson combined) =
162B used in 192B / 3 cache lines exact.

**Anti-pattern to flag during /dod-audit:**
- "Feature grouping" instead of "frequency grouping": fields about
  the same feature (e.g., all bandit-related) placed together
  regardless of whether they're touched per cycle vs per init
- Persistence-related strings (paths, file names) in HOT cluster

## Rule 5 — Bit-pack boolean cohorts (CLAUDE.md item 20)

**Pattern.** When 3+ boolean / small-enum fields cluster semantically,
bit-pack into a single uint8_t / uint16_t / uint32_t / uint64_t with
MASK_* constants per BITMAP_* API (item 20). Wins: memory compactness,
atomic multi-flag check via mask AND, branchless multi-flag dispatch,
single-word "any flag set?" check.

**Anti-pattern caught in v5.15.5 cache audit:**

```cpp
struct EnsembleModelZoo {
    int initialized_bandits;          // 4B (boolean state in int)
    int initialized_exit_bandits;     // 4B
    int initialized_thompson_bandits; // 4B
    int active;                       // 4B (ensemble-active boolean)
    // = 16 bytes for 4 booleans
};
```

**Fix:**

```cpp
// Bitmap mask constants (matches FOREACH_FAILURE_MODE pattern)
constexpr uint8_t MASK_EZOO_BANDITS_READY         = BITMAP_BIT_U8(0);
constexpr uint8_t MASK_EZOO_EXIT_BANDITS_READY    = BITMAP_BIT_U8(1);
constexpr uint8_t MASK_EZOO_THOMPSON_READY        = BITMAP_BIT_U8(2);
constexpr uint8_t MASK_EZOO_ACTIVE                = BITMAP_BIT_U8(3);
// 4 free bits for future flags

struct EnsembleModelZoo {
    uint8_t init_flags;  // 1B — 4 bits used; 4 free
    // ... 15 bytes saved + branchless multi-flag check enabled
};

// Atomic multi-flag check (single AND vs 2 branches):
if (BITMAP_ALL(ezoo->init_flags,
               MASK_EZOO_BANDITS_READY | MASK_EZOO_THOMPSON_READY)) {
    // both initialized
}
```

**Storage class decision (per item 13 + 20):**
- < 4 booleans: leave as bytes (overhead of MASK constants not worth it)
- 4-8 booleans: bit-pack into uint8_t
- 9-16 booleans: uint16_t
- 17-32: uint32_t
- 33-64: uint64_t

**Per-arm bit-packing:**

```cpp
// 8 arms × 4 per-arm boolean states packed into one uint32_t:
uint32_t per_arm_flags;
// bits  0-7:  arms_warmed_up_mask
// bits  8-15: arms_drift_breached_mask
// bits 16-23: arms_disabled_mask (existing `disabled_horizon_mask`)
// bits 24-31: arms_reward_observed_mask
```

Caveat: bit-packing across DIFFERENT booleans (warm vs drift) only
makes sense if they're accessed in the same slow-path region. If
warm and drift are accessed by different functions, separate packs.

## Rule 6 — AVX-512-friendly tight-pack alignment (CLAUDE.md item 25)

**Pattern.** Tight-pack arrays (Rule 2) sized to fit 1 ZMM register
(512 bits = 64 bytes = 16 floats / 8 doubles) enable single-instruction
SIMD reductions. Σ wᵢ · barrierᵢ for 16 floats = 1 `_mm512_fmadd_ps`
in 1 cycle.

**Sizing reference:**

| Type | Per ZMM register | Per cache line | Combined? |
|---|---|---|---|
| float | 16 | 16 | yes — 1 line = 1 register |
| double | 8 | 8 | yes — 1 line = 1 register |
| int32_t | 16 | 16 | yes |
| int64_t | 8 | 8 | yes |

**Bytewise-determinism requirement.** AVX-512 path must have a scalar
fallback (`#if defined(__AVX512F__) else baseline`) producing
BYTEWISE IDENTICAL output. Cross-binary replay determinism is the
load-bearing concern. Per DESIGN_SPECS/avx512-byte-determinism-pattern.md
Rule 7 (SHA-256 lock test) — every AVX-512 kernel ships with a SHA
test asserting scalar + vectorized paths produce identical bytes.

**When to add AVX-512:** if profiling shows the reduction is hot path
slow-path-budget-pressuring. Skip if cycle count fits within
slow-path budget without vectorization.

## Rule 7 — Per-cycle access budget rule

**Pattern.** Set an explicit budget for cache-line accesses per
slow-path cycle. Any struct's slow-path access footprint > 2 cache
lines (128 bytes) per cycle is a candidate for Rules 1-3 extraction.

**Per-cycle measurement:**

```bash
# Compile with -DLATENCY_PROFILING
perf stat -e L1-dcache-load-misses,L1-dcache-loads \
          --interval-print 1000 ./bin/engine

# Look for slow-path miss spikes correlated with cycle cadence
```

**Budget targets (CLAUDE.md items 7 + 17):**
- HOT path per tick: ≤ 1 cache line of working set; aggressive
- Slow path per cycle: ≤ 3-5 cache lines of access; budget tight
- OMS drainer per fill: ≤ 5 lines; budget moderate
- Boot/init: no budget

**Apply to plans:** plans touching per-cycle code should include a
cache-line access estimate per CLAUDE.md item 17 latency tracking.

## Combining the rules — checklist for hot-side struct review

When reviewing or designing a struct that's touched per cycle:

1. **Cache-line size audit.** Compute total bytes; flag any field that
   straddles 64-byte boundaries. Use `static_assert(sizeof(MyStruct) ==
   N)` and `static_assert(offsetof(MyStruct, my_field) == M)` for
   compile-time enforcement.

2. **Rule 1 sweep:** identify display-only / debug-only fields. Move
   them to a separate `MyStructDisplayMeta` struct. Slow-path doesn't
   include the display meta in its access set.

3. **Rule 2 application:** if N items are accessed together in a
   slow-path loop, group them into a tight-pack array (`alignas(64)
   float per_item_data[16]` for 8 items × 2 fields).

4. **Rule 3 isolation:** for cross-thread shared fields, mark them
   `alignas(64)` and `alignas(64)` the next field. Verify no false
   sharing with neighbor-field writes.

5. **Padding policy:** if struct is byte-compared (memcmp, SHA, wire
   format) → use explicit `_pad = 0` default-init fields per item 27.
   Otherwise → `alignas` on adjacent fields is sufficient.

6. **Per-cycle access map:** document which fields the slow-path
   touches per cycle. Target: < 2 cache lines (128 bytes) of access
   per cycle for any single struct. Anything more is a candidate for
   Rule 1 or Rule 2 extraction.

## Reference applications

| Ship | Surface | Rules applied | Savings |
|---|---|---|---|
| v5.15.5.B.1 | CoreContext HOT/WARM/COLD reorg + explicit alignas(64) + 5 static_assert layout locks + CoreSlowState lazy_rebuild hoist | Rules 3 + 4 + 7 (+ ND3 first explicit ref) | per-core L1 footprint 35% → 14%; lazy-rebuild gate ~100 ns/cycle cold-cache saved on ~30-50% of cycles |
| v5.15.5.B.2 | CoreContextDisplayMeta extraction + SlowPathTelemetry / WsHeartbeatTelemetry alignas clusters (dual X-macro registries) | Rules 1 + 3 + 4 (+ ND1 + ND2 first refs) | CoreContext 17 KB → 7 KB / slot (-58%); ~96-288 µs/sec engine-wide saved on snapshot-publisher cross-thread invalidation |
| v5.15.5.B.3 | CoreContext.core_state_flags bitmap (5 booleans + 3-byte pad eliminated) | Rule 5 | ~112 B per EventLoopState saved + branchless multi-flag check enabled |
| v5.15.5.B.5 | SP_SECTION + SESSION_PHASE X-macro registries + branchless SESSION_BY_HOUR[24] table | Rules 4 + 8 | 4-way data-dependent mispredict class eliminated at 3 consumer sites |
| v5.15.5.B.6 | FOREACH_ROLLING_WINDOW registry for CoreSlowState | Rule 4 (template-parameterized cohort variant) | Structural close of 4-window multi-site init/push sync mirror |
| v5.15.5.B.7 | FOREACH_CORE_CTX_INIT_FIELD + FOREACH_CORE_CTX_RESET_FIELD + CORE_CTX_{INIT,RESET}_AUTOPOPULATE | Rule 7 (one-line per-slot init/reset) | EventLoopState_Init body 145 LOC → 1 LOC; paper-reset 45 LOC → 1 LOC |
| v5.15.5.B.8 | ShardedSnapshot publisher 4-walk → 1-walk consolidation | Loop-fusion pattern + Rule 4 | ~20 MB/s memory bandwidth saved at 60 Hz publish (T1 audit close) |
| v5.15.5 | EnsembleModelZoo per_arm_barriers tight-pack | Rule 2 | ~700 ns/cycle cold cache |
| v5.15.5 | BanditState arm_names extraction | Rule 1 | ~400 ns/cycle cold cache (per-regime access) |
| v5.15.5 | BarrierShadowRing.head alignas isolation | Rule 3 | ~100-200 ns per GUI poll avoided |
| v5.15.5 | EnsembleModelZoo hot/warm/cold clustering | Rule 4 | reduces slow-path cycle access to HOT cluster only |
| v5.15.5 | EnsembleModelZoo init_flags bit-pack | Rule 5 | 15B saved + branchless multi-flag dispatch |
| v5.14.10.0 (precedent) | PerCoreSnap bandit telemetry cluster | Rules 2 + 3 + 4 | 162B / 192B = 84% utilization in 3 cache lines |
| v5.14.11.B.2 (precedent) | FPN<F> + ThompsonBanditState explicit padding | Rule 3 alternate (byte-equiv context) | extinguished latent bytewise-identity regression class |
| v5.11.7 (precedent) | Bandit_GetProbabilities AVX-512 | Rule 6 | first reference for SIMD scalar fallback |

### Bandwidth implications (added 2026-05-13 post v5.15.5.B.8)

The latency-savings column above ("~X ns/cycle cold cache") captures
per-access LATENCY wins. The complementary dimension is memory
BANDWIDTH — total DRAM traffic across the system. Rules 1, 4, and
the loop-fusion pattern reduce bandwidth directly:

- **Rule 1** (display-only extraction): post-`.B.2`, ~9.8 KB / slot
  of display-only data sits on a sibling array, OUT of the per-cycle
  HOT cluster. At 1000 cycles/sec/core × 16 cores ≈ ~157 MB/s less
  DRAM traffic from slow-path cycles vs the pre-extraction baseline.
- **Rule 4** (HOT/WARM/COLD tiering): forward-sequential layout
  triggers prefetcher engagement — turns scattered cold reads into
  stream prefetches that saturate FEWER DRAM cycles per useful byte.
- **Loop fusion** (`loop-fusion-pattern.md`; post-`.B.8`): 3 saved
  walks × 16 cores × ~7 KB / CoreContext × 60 Hz = ~20 MB/s saved on
  the snapshot publisher alone. Bandwidth-bound workloads compound.

See `latency-vs-cache-decision-framework.md` § Memory bandwidth costs
for the framework that quantifies these vs latency-adding choices.

## Surfaces to audit next (deferred to v5.15.6 / v5.16 cleanup sprint)

A systematic audit pass across remaining hot-side structs in priority
order:

| Surface | Current concerns | Estimated savings | Effort |
|---|---|---|---|
| `OrderManagerState` | Slot-level data accessed per drainer-tick; verify HOT/WARM/COLD tiers; pending_orders[] cache layout | Drainer-tick latency reduction | ~2-3h |
| `EventLoopCoreState<F>` (per-core slow state) | Touched every slow-path cycle; needs Rule 4 audit; many fields accumulated | Slow-path cycle reduction | ~2-3h |
| `RollingStats<F>` | Slow-path-push per tick (highest-frequency slow-side code); cache-line audit critical | Per-tick slow-path | ~1-2h |
| `FlowFeatures<F>` | Per-cycle update + read; verify tight-pack of per-window stats | Slow-path cycle | ~1-2h |
| `ConfidenceScorer<F>` | Per-cycle confidence computation; composite-mode multi-field access | Slow-path cycle | ~1h |
| `RegimeSignals` | Per-cycle classifier output; Rule 1 candidate (display fields?) | Slow-path read | ~30min |
| `CoreContext<F>` | Per-core shared state; cross-component access; Rule 4 candidate | Slow-path cycle | ~2h |

Each surface gets the 8-rule checklist below (or a subset for cold
structs).

## Rule 8 — Slow-path branch density audit (CLAUDE.md item 18)

**Pattern.** During cache-layout sweeps of slow-path-touched structs,
ALSO audit branch density in the consumer functions. Per CLAUDE.md
item 18 (set 2026-05-08): aim to MINIMIZE slow-path branches + cycles
in every ship.

**Why this fits cache-layout audits.** Struct reorganization changes
which fields are co-located in cache lines; consumer functions
typically have access patterns aligned with the OLD layout. While
rewriting access sites for the new layout, also rewrite the
branch density at those sites.

**Patterns to apply at each access site:**

### Pattern 8a — DEFAULT-OFF safety gates: compile-time elision

For cfg-flag-gated code that defaults OFF (most operators never enable),
use templates + `if constexpr` instead of runtime `if`:

```cpp
// BEFORE — runtime branch on every cycle:
if (cfg.barrier_blend_mode != LEGACY) {
    // expensive blend computation
}

// AFTER — template parameterization:
template <bool BLEND_ENABLED>
void compute_barriers(...) {
    if constexpr (BLEND_ENABLED) {
        // expensive blend computation
    }
    // disabled instantiation has zero branch, zero instructions
}
```

When operators never set the flag, compiler instantiates only the
`<false>` variant — zero cost. When they do, `<true>` variant ships
without the runtime check.

### Pattern 8b — ALWAYS-ON gates: branchless mask compute

For code that runs every cycle regardless of mode, replace branches
with mask multiply:

```cpp
// BEFORE — 4 branches:
if (mode == BLEND) { result = blend; }
else if (mode == DOMINANT) { result = dominant; }
else if (mode == BOTH_BLEND_DRIVES) { result = blend; shadow = dominant; }
else if (mode == BOTH_DOMINANT_DRIVES) { result = dominant; shadow = blend; }

// AFTER — branchless dispatch via mask-select:
bool blend_drives = (mode == BLEND) | (mode == BOTH_BLEND_DRIVES);
result = blend_drives ? blend : dominant;     // cmov, no branch
bool shadow_active = (mode == BOTH_BLEND_DRIVES) | (mode == BOTH_DOMINANT_DRIVES);
shadow = shadow_active ? (blend_drives ? dominant : blend) : 0.0;
```

CPU pipelines cmov as a single uop; predictable-branch on enum is also
~1 cycle, but mask compute is MORE predictable (no branch predictor
state-machine cost on rare flips).

### Pattern 8c — RUNTIME-toggleable gates: cache "any gate enabled" mask at entry

When multiple cfg flags are checked deep in a function body, hoist
them to a single mask at function entry:

```cpp
// BEFORE — repeated cfg reads:
if (cfg.gate_a_enabled) { ... }
if (cfg.gate_b_enabled) { ... }
if (cfg.gate_c_enabled) { ... }

// AFTER — hoisted mask at slow-path entry:
uint16_t enabled_gates =
    (cfg.gate_a_enabled ? MASK_GATE_A : 0) |
    (cfg.gate_b_enabled ? MASK_GATE_B : 0) |
    (cfg.gate_c_enabled ? MASK_GATE_C : 0);

// later in body — single AND:
if (BITMAP_IS_SET(enabled_gates, MASK_GATE_A)) { ... }
// or branchless multi-flag check:
if (BITMAP_ALL(enabled_gates, MASK_GATE_A | MASK_GATE_B)) { ... }
```

Precedent: `SlowPathGateState.flags` (v5.14.9.B.0+) caches gate
predicates at slow-path entry.

### Pattern 8d — Nested if-chains: flatten to mask compute when safe

```cpp
// BEFORE — nested conditions:
if (ezoo && ezoo->active) {
    if (ezoo->primary_count > 0) {
        if (config->per_horizon_barrier_blend) {
            if (n_with_barriers > 0) {
                // do thing
            }
        }
    }
}

// AFTER — single mask AND (assuming pointer-null guarded earlier):
bool active_ensemble =
    (ezoo != nullptr) &
    (ezoo->active) &
    (ezoo->primary_count > 0) &
    config->per_horizon_barrier_blend &
    (n_with_barriers > 0);
if (active_ensemble) { /* do thing */ }
```

Short-circuit `&&` becomes non-short-circuit `&` to avoid branches;
safe when predicates don't have side effects.

**When NESTED branches stay (don't force branchless):**
- The condition is a perfect predictor (boot phase, mode set once at
  init) — branch predictor learns it; mask compute provides no benefit
- The condition gates EXPENSIVE work; you DO want the branch to skip
  the work entirely (mask compute would compute then discard)
- Per operator framing 2026-05-12: "assuming its not a perfect
  prediction after a given condition" — keep predictable branches;
  flatten data-dependent ones

**When to apply branch density audit during cache-layout sweep:**

At each access site you're rewriting for the new struct layout:
1. Count the branches per slow-path cycle
2. Classify: predictable (boot/mode/cfg-set-once) vs unpredictable
   (data-dependent)
3. Flatten unpredictable to mask compute (Pattern 8b, 8d)
4. Hoist runtime cfg-flag checks (Pattern 8c)
5. Template-elide compile-time-known DEFAULT-OFF gates (Pattern 8a)

**Target:** every 5+ branches in a per-cycle function = consider helper
extraction or mask-collapse refactor. Track per-cycle branch count
before/after; goal is monotonic reduction.

## Combining the rules — checklist for hot-side struct review

When reviewing or designing a struct that's touched per cycle:

1. **Tier classification (Rule 4).** Label every field HOT / WARM /
   COLD. Reorganize layout to cluster by tier.

2. **Cache-line size audit.** Compute total bytes per tier; flag any
   field that straddles 64-byte boundaries. Use `static_assert
   (sizeof(MyStruct) == N)` and `static_assert(offsetof(MyStruct,
   my_field) == M)` for compile-time enforcement.

3. **Rule 1 sweep:** identify display-only / debug-only fields. Move
   to a separate `MyStructDisplayMeta` struct.

4. **Rule 2 application:** if N items are accessed together in a
   slow-path loop, group them into a tight-pack array (`alignas(64)
   float per_item_data[16]` for 8 items × 2 fields).

5. **Rule 3 isolation:** for cross-thread shared fields, mark them
   `alignas(64)` and `alignas(64)` the next field. Verify no false
   sharing.

6. **Rule 5 bit-pack:** if ≥3 boolean cohort fields, pack into a
   single integer with MASK_* constants per item 20 BITMAP_* API.

7. **Rule 6 AVX-512 candidate:** for tight-pack arrays that fit 1
   ZMM register (16 floats / 8 doubles), consider SIMD vectorization
   IF profiling shows the reduction is budget-pressuring. Always
   ship scalar fallback (item 25).

8. **Rule 7 budget check:** per-cycle cache-line access ≤ 3-5 lines
   for slow path; ≤ 1 line for hot path. Re-evaluate if budget
   exceeded.

9. **Padding policy:** if struct is byte-compared (memcmp, SHA, wire
   format) → use explicit `_pad = 0` default-init fields per
   item 27. Otherwise → `alignas` on adjacent fields is sufficient.

10. **Per-cycle access map:** document which fields the slow-path
    touches per cycle. Embed as a comment block at struct
    declaration.

## What this doc is NOT

- Not a substitute for `STRATEGY_AND_CODING_RULES.md` Rule 7 (which
  covers L1 cache prioritization more generally)
- Not a replacement for runtime measurement (`perf stat -e
  L1-dcache-load-misses`) — measure actual savings after applying
- Not applicable to every struct — boot-only / once-per-run / cold-path
  structs don't need this discipline

## Cross-references

- `CLAUDE.md` items 7, 16, 17, 19, 20, 27
- `DESIGN_SPECS/per-horizon-barrier-blending-with-shadow-mode.md` (uses
  all 3 rules)
- `DESIGN_SPECS/per-snapshot-cluster-layout-pattern.md` (v5.14.10
  precedent; snapshot-side variant of this discipline)
- `DESIGN_SPECS/struct-padding-determinism-pattern.md` (Rule 5 caveat
  for byte-comparison contexts)
- `DESIGN_SPECS/avx512-byte-determinism-pattern.md` (tight-pack arrays
  are AVX-512-friendly)
- `DESIGN_SPECS/hot-side-array-element-alignment-for-sparse-access.md` (v5.15.5.C.5; **complementary**: Rule 2 here covers TIGHT-PACK for 1-line elements; sister spec covers MULTI-LINE structs where sparse hot-path access reads first-line subset. Same cache-discipline philosophy, different element-size regime.)
- `DOCS/HOT_PATH_CHANGELOG.md` (per-ship cache-impact entries)
- `STRATEGY_AND_CODING_RULES.md` Rule 7 (L1 cache prioritization)
- `claude-skills/dod-audit/SKILL.md` (walks this doc for compliance
  audit)

## Promotion criteria (this doc was promoted)

This pattern is promoted to a DESIGN_SPECS doc when:
1. 2+ applications surface (here: barrier tight-pack + bandit arm_names
   extraction + shadow ring isolation = 3 applications in one ship)
2. The applications share a generalizable rule (all are cache-layout
   discipline for hot-side structs)
3. Operator (Caramel) explicitly requested generalization 2026-05-12
   ("the findings can probably be generalized")

Document re-evaluated when the 4th and 5th applications surface;
extend or split if new rule emerges.
