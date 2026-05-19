---
type: feature-pattern
stage: 2-draft
version: 1.0
established: 2026-05-12
tags: [framework-discipline, structural-fix]
surface: [ml-inference, slow-path, training]
sister_specs: [shadow-load-state-transition-pattern.md]
applies_at_skills: []
---

# Per-Horizon Barrier Blending with Shadow Mode

**Status:** v5.15.5 design (in development 2026-05-12).
**Sister pattern:** v5.14.10.B Thompson dual-mode (cfg.bandit_algorithm=2).
**CLAUDE.md cross-ref:** items 13, 14, 15, 16, 17, 18, 22, 24, 26.

## Problem

Multi-horizon ML ensembles train each horizon model against its own
TP/SL barriers (via v5.13.5 Label Kind CSV + TP/SL CSV inputs). At
serve time, the live engine reads single `cfg.ml_tp_pct` /
`cfg.ml_sl_pct` and applies them to all positions regardless of
which horizon model dominated the prediction. Result: train-serve
drift — model trained on 0.03% barrier labels can fire a trade at
0.05% TP, violating the calibration invariant.

Required prerequisite for credible multi-horizon ensemble production
serving.

## Design choice space

Five mode dispatch options for resolving per-horizon barriers into a
single trade's TP/SL:

| Mode | Formula | Train-serve match | Smoothness | Bandit info used |
|---|---|---|---|---|
| LEGACY | `cfg.ml_tp_pct` direct | poor (single value all horizons) | n/a | none |
| BLEND | `Σ wᵢ · barrierᵢ` | good (interpolated, near training) | best | full (continuous) |
| DOMINANT | `barrier[argmax(weights)]` | exact (one arm's trained barrier) | flickers in ambiguity | partial (rank only) |
| BOTH_BLEND_DRIVES | blend drives, dominant logged | good, telemetry compare | best | full |
| BOTH_DOMINANT_DRIVES | dominant drives, blend logged | exact, telemetry compare | flickers | full |

**Why all five matter:** A vs B is genuinely empirical — depends on
ensemble convergence + regime stability. Operator A/B tests via
BOTH modes; chooses driving mode based on real data.

## Pattern

### Registry-driven mode dispatch (CLAUDE.md item 13)

```cpp
// ML_Headers/BarrierBlendModeRegistry.hpp
#define FOREACH_BARRIER_BLEND_MODE(X) \
    X(LEGACY,                "legacy",                "cfg-direct (pre-v5.15.5 behavior)") \
    X(BLEND,                 "blend",                 "Σ wᵢ · barrierᵢ — bandit-weighted blend") \
    X(DOMINANT,              "dominant",              "argmax(weights) picks one arm's barriers") \
    X(BOTH_BLEND_DRIVES,     "both_blend_drives",     "Blend drives; dominant logged for compare") \
    X(BOTH_DOMINANT_DRIVES,  "both_dominant_drives",  "Dominant drives; blend logged for compare")

enum {
#define X(id, name, desc) MODE_BARRIER_BLEND_##id,
    FOREACH_BARRIER_BLEND_MODE(X)
#undef X
    MODE_BARRIER_BLEND_COUNT
};
```

Adding a 6th mode: append 1 row. AUTOPOPULATE companion handles
stamp wiring (item 21). GUI dropdown auto-derives via FOREACH
iteration (Label Kind CSV pattern from v5.13.5).

### Cache-friendly tight-pack barrier array (CLAUDE.md items 7, 26)

**Problem.** Reading barriers from N scattered ModelHandle objects =
N cache lines per slow-path cycle. ModelHandle is ~512+ bytes (FPN
fields + char buffers + counters); the `label_tp_pct` /
`label_sl_pct` sit at offset ~349 in each handle. 8 handles =
8 separate cache-line fetches just for barriers.

**Solution.** Gather into a tight-pack array on EnsembleModelZoo,
populated at handle-load time alongside the per-handle field write:

```cpp
template <unsigned F>
struct EnsembleModelZoo {
    // ... existing fields ...

    // v5.15.5 — tight-pack per-arm barriers for cache-line-efficient
    // slow-path access. 8 floats × 2 arrays = 64 bytes = exactly 1
    // cache line; alignas(64) prevents straddling. Single-writer at
    // boot (CoreModelZoo_TryLoadRole). Slow-path reads all 8 entries
    // for blend / dominant compute in one L1 fetch. Per CLAUDE.md
    // item 7 (memory hierarchy), this saves ~7 cache misses per
    // slow-path cycle vs reading handles individually.
    alignas(64) struct PerArmBarriers {
        float buy_tp_pct[ENSEMBLE_HORIZON_MAX];   // 32 bytes
        float buy_sl_pct[ENSEMBLE_HORIZON_MAX];   // 32 bytes
    } per_arm_barriers;

    // Shadow mode ring (modes 3-4 only): 256-slot ring of
    // (actual_tp, shadow_tp, actual_sl, shadow_sl) + which mode
    // was driving + dominant_idx. ~32 bytes/record × 256 = 8 KB,
    // single cache page (4KB) per half. alignas(64) on the ring
    // head + alignas(64) on each record.
    alignas(64) BarrierShadowRing barrier_shadow_ring;
};
```

Boot-time wire (mirror of `handle->label_tp_pct = sr.label_tp_pct`):

```cpp
// In CoreModelZoo_TryLoadRole, after STAMP_HAS(sr, label_params) block:
if (STAMP_HAS(sr, label_params)) {
    STAMP_SET(*handle, label_params);
    handle->label_tp_pct = sr.label_tp_pct;
    handle->label_sl_pct = sr.label_sl_pct;
    // v5.15.5 — also write into ezoo's tight-pack array for
    // cache-line-efficient slow-path access.
    if (ezoo && arm_idx < ENSEMBLE_HORIZON_MAX) {
        ezoo->per_arm_barriers.buy_tp_pct[arm_idx] = (float)FPN_ToDouble(sr.label_tp_pct);
        ezoo->per_arm_barriers.buy_sl_pct[arm_idx] = (float)FPN_ToDouble(sr.label_sl_pct);
    }
}
```

### Slow-path-only resolution (CLAUDE.md item 17)

**Hot path UNCHANGED.** Hot path reads `params->tp_pct` / `params->sl_pct`
from ParameterSlot as before. All mode dispatch happens slow-path in
`ML_BuildParameters` AFTER `weights_buf[]` is finalized
(`Strategies/StrategyParameters.hpp:1029`).

Branch profile per mode (slow path):
- LEGACY:   ~0 ns (cfg direct copy as today)
- BLEND:    ~20-30 ns (8-iter constant-iter Σ wᵢ · barrierᵢ; FMA-friendly)
- DOMINANT: ~10-15 ns (8-iter compare-select argmax; ternary-based no data branches)
- BOTH_*:   ~35-50 ns (both paths + ring push)

Hot-path latency add: 0 ns regardless of mode. HOT_PATH_CHANGELOG.md
documents per CLAUDE.md item 17.

### Branchless inner loops (CLAUDE.md item 26)

BLEND uses constant-iter inner reduction:

```cpp
double tp_blend = 0.0, sl_blend = 0.0;
for (int i = 0; i < ENSEMBLE_HORIZON_MAX; i++) {  // constant-iter 8
    double has_w = (i < ezoo->primary_count) ? 1.0 : 0.0;
    tp_blend += has_w * weights_buf[i] * (double)ezoo->per_arm_barriers.buy_tp_pct[i];
    sl_blend += has_w * weights_buf[i] * (double)ezoo->per_arm_barriers.buy_sl_pct[i];
}
```

Inactive arms (i >= primary_count) contribute zero via `has_w` mask
multiply; bytewise-equivalent to variable-iter branched version. Per
item 26: same shape as `Cholesky_Solve` constant-iter pattern.

DOMINANT uses branchless argmax via mask-select:

```cpp
double max_w = -1.0;
int dominant_h = -1;
for (int i = 0; i < ENSEMBLE_HORIZON_MAX; i++) {  // constant-iter 8
    bool active = (i < ezoo->primary_count);
    bool is_greater = active && (weights_buf[i] > max_w);
    max_w      = is_greater ? weights_buf[i] : max_w;
    dominant_h = is_greater ? i             : dominant_h;
}
```

### Shadow-mode ring (concurrency: single-writer slow-path + false-sharing-free layout)

Shadow records pushed by slow-path only (cycle-cadence). Read by
GUI thread at a much slower rate (~60Hz vs ~1kHz slow-path); GUI
reads via atomic-load of the ring head + non-blocking snapshot copy.

**Critical cache-layout discipline.** The ring HEAD index is read
by the GUI thread (cross-core). It MUST live on its OWN cache line,
not shared with records[] or other slow-path-write fields. False
sharing otherwise → GUI reads invalidate slow-path writer's line on
the producer core, causing 100-200ns penalty per GUI read.

```cpp
struct BarrierShadowRecord {
    uint64_t cycle_idx;      // 8 bytes
    float actual_tp;         // 4 bytes
    float actual_sl;         // 4 bytes
    float shadow_tp;         // 4 bytes
    float shadow_sl;         // 4 bytes
    uint8_t driving_mode;    // 1 byte (3 or 4)
    uint8_t dominant_h;      // 1 byte (-1 for blend-driving cycles)
    uint16_t _pad;           // 2 bytes — runtime-only struct, but explicit init-zero
                             //          for future byte-comparison safety per item 27
    // Total: 32 bytes; 256 records = 8192 bytes (~8 KB)
};

struct BarrierShadowRing {
    // === Cache line 0 — cross-thread shared head ===
    // Written by slow-path; read by GUI + persistence thread.
    // alignas(64) on `head` aligns it to 64-byte boundary; alignas(64) on
    // `records` forces it to its OWN line. Compiler inserts implicit
    // padding between head and records automatically. No explicit
    // `_pad[]` array needed (struct is not byte-compared / not HMAC'd,
    // so implicit alignas-padding is safe per CLAUDE.md item 27 caveat).
    alignas(64) uint64_t head;                       // 8B, line 0

    // === Cache lines 1+ — slow-path-only records ===
    alignas(64) BarrierShadowRecord records[256];    // compiler pads from head's line
    // 32B records → exactly 2 records per cache line; clean alignment
};
```

Single-writer slow-path → no seqlock needed for the ring itself; head
index update is `__atomic_store(&ring->head, new_head, __ATOMIC_RELEASE)`
after the record-write completes. GUI reads via
`__atomic_load(&ring->head, __ATOMIC_ACQUIRE)` + snapshot copy.

**Why TWO `alignas(64)` declarations (head + records):** alignas on the
struct-level (`struct alignas(64) {...}`) only aligns the STRUCT'S
START. Without alignas on `records`, the compiler is free to lay it
right next to `head` in line 0 (false sharing). Putting `alignas(64)`
on the `records` field forces it to start on a fresh 64-byte boundary;
compiler inserts the necessary padding bytes between head and records
implicitly. Cleaner than an explicit `_line0_pad[56]` array, and
identical in runtime layout.

**When to prefer explicit `_pad[]` instead:** if the struct is used in
a byte-equivalence context (memcmp / SHA-256 / wire format / HMAC), use
explicit `int32_t _pad = 0` default-init fields per CLAUDE.md item 27
to guarantee padding bytes are zero-initialized (implicit compiler
padding is UB-readable). BarrierShadowRing is runtime-only state →
alignas-only is fine.

### Cfg-drift Tier 1 promotion (CLAUDE.md item 15)

`barrier_blend_mode` is load-bearing — operator changing mode between
training and serving causes actual barrier behavior to diverge.
Promote to Tier 1 cfg-drift in stamp:
- Mode mismatch under strict mode → refuse load
- Loose mode → WARN log + load
- Operator escape via existing `acknowledge_inference_cfg_drift=1`

Wired via existing `FOREACH_STAMP_BOUND_CFG` registry (item 22 PRE/POST
split + AUTOPOPULATE companion per item 21). Adding the row =
1 line in the registry; production-callers populate automatically.

### Bandit invariant preserved (CLAUDE.md item 24)

Per-arm reward observability:
- Each arm's prediction is direction-graded against actuals regardless
  of which mode fired the trade
- Bandit updates each arm's weight via independent reward stream
- Shadow mode is mathematically valid: bandit state evolves identically
  whether the engine drove with blend or dominant
- Counterfactual evaluation directly tractable — replay reward stream
  through either mode's barriers offline

### Concurrency posture summary

| Surface | Writer | Reader | Sync mechanism |
|---|---|---|---|
| `ezoo->per_arm_barriers` | CoreModelZoo_TryLoadRole (boot, single) | ML_BuildParameters (slow-path) | None needed (boot-write, runtime-read) |
| `barrier_shadow_ring.records[]` | ML_BuildParameters (slow-path) | GUI thread, persistence flush | atomic ring head (ACQ_REL), record-write before head-advance |
| `params->tp_pct` / `sl_pct` (in ParameterSlot) | Slow-path | Hot path | Existing seqlock (no change) |
| `barrier_mode_shadow_stats.json` | Slow-path persistence flush (cfg.barrier_shadow_persist_every_n) | Operator manual + Backtest replay | mmap + atomic rename pattern (mirror bandit_state.json) |

No new locks, no new seqlocks. Reuses existing ParameterSlot seqlock
for the hot-path handoff (zero net concurrency surface area added).

### Cache layout summary

| Field | Bytes | Line | Notes |
|---|---|---|---|
| `per_arm_barriers.buy_tp_pct[8]` | 32 | 0 | tight-pack |
| `per_arm_barriers.buy_sl_pct[8]` | 32 | 0 | same line as buy_tp |
| `barrier_shadow_ring.head` | 8 | 1 | atomic; separate line to prevent false sharing with records |
| `barrier_shadow_ring.records[0]` | 28 | 2+ | 28B records; ~2 records per line; ring spans ~57 lines |

Cache-miss savings per slow-path cycle: ~7 lines vs reading 8 handles
individually × ~100ns/miss = ~700 ns/cycle/core. Across 4 cores ×
100 cycles/sec = 400 cycles/sec × 700 ns = 280 μs/sec saved on cache
traffic alone. Marginal but real (per CLAUDE.md item 7).

### Bandit symmetric extension (companion ship, OPTIONAL)

Current bandit_algorithm registry is asymmetric:
- 0 = EXP3 only
- 1 = THOMPSON only
- 2 = BOTH (EXP3 drives, Thompson logs)
- ⚠️ Missing: 3 = REVERSED (Thompson drives, EXP3 logs)

Per CLAUDE.md item 19 (structural-fix-preferred when bug class
recurs): if v5.15.5 establishes symmetric coverage on barrier blend
modes, the bandit asymmetry is the sister class. Bundling closes both
at once (~50 LOC bandit-side: 1 X-macro row + 1 compute fn +
chosen_arm logging). Defer to separate ship if scope tight.

## Failure modes addressed

| Failure | Mitigation |
|---|---|
| Pre-v5.15.5 stamp without barrier fields | `has_label_params=0` sentinel → mode falls back to cfg (LEGACY) for that arm; or whole ensemble if all arms legacy |
| Mixed ensemble (some new + some legacy stamps) | Defensive: fall back to LEGACY for whole trade; WARN log surfaces the mix |
| Bandit uninitialized (cold start, uniform weights) | argmax picks idx 0; bytewise deterministic; bandit warmup converges |
| All weights zero (impossible per Bandit_GetProbabilities contract) | Defensive check: fall back to LEGACY; ensures non-zero divisor |
| Shadow ring full | Overwrite-oldest (standard ring policy); 256 records ≈ 256 cycles of history at typical cadence ≈ 25-50 sec |
| cfg.ml_tp_pct = 0 in LEGACY fallback path | Existing behavior: trade refuses to fire on zero TP; no new failure mode |

## Tests

- Per-mode unit tests: each of 5 modes produces correct
  params->tp_pct for synthetic ensemble (3 horizons; tp values
  0.03 / 0.05 / 0.07; uniform vs skewed weights)
- Shadow mode determinism: BOTH_BLEND_DRIVES with same weights +
  same per-arm barriers → bytewise-identical shadow record across
  runs
- Cache layout assertion: `static_assert(sizeof(PerArmBarriers) == 64)`
- AUTOPOPULATE round-trip: write stamp with mode + read it back; mode
  field preserved bit-for-bit
- Tier 1 strict refuse: load model under different mode than stamp;
  expect refuse with descriptive error
- AVX-512 / scalar byte-determinism (CLAUDE.md item 25): if BLEND
  formula gets vectorized later, scalar fallback bytewise identical

## Cross-references

- `CLAUDE.md` items 13, 14, 15, 16, 17, 18, 22, 24, 26 (the doctrine)
- `claude-skills/parity-check` Section L (production-caller
  field-population audit)
- `claude-skills/dod-audit` (data-oriented design audit walks this
  doc automatically)
- `DESIGN_SPECS/bitmap-flag-api.md` (sister pattern — bitmap
  per-flag storage; here we use tight-pack arrays not bitmaps because
  fields are non-boolean)
- `DESIGN_SPECS/x-macro-registry-with-presence-dispatch.md`
- `DESIGN_SPECS/autopopulate-pattern-for-production-caller-class.md`
- `DESIGN_SPECS/pre-post-cfg-registry-split-for-emit-order-preservation.md`
- `DESIGN_SPECS/avx512-byte-determinism-pattern.md`
- `DESIGN_SPECS/branchless-math-kernel-pattern.md`
- `DESIGN_SPECS/struct-padding-determinism-pattern.md`
- `DOCS/PARITY_LIFECYCLE.md`
- `DOCS/HOT_PATH_CHANGELOG.md`

## Promotion criteria

This pattern is promoted to a DESIGN_SPECS doc on creation (pre-coding
plan stage) because:
1. It captures cache layout + concurrency posture that's load-bearing
   and easy to drift without explicit documentation
2. Operator (Caramel) requested it explicitly 2026-05-12 — "this
   should be a design spec we can save as well"
3. It establishes pattern that other multi-output ensemble work will
   reuse (sister patterns: exit-side blender, regime ensemble)

Document re-evaluated at v5.15.5 ship close + on each subsequent
extension.
