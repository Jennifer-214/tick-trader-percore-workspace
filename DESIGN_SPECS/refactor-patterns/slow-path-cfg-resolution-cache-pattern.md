---
type: refactor-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-13
tags: [latency-discipline, data-oriented-design, structural-fix]
surface: [slow-path, cfg-flow]
sister_specs: [decision-time-data-binding-pattern.md, cache-layout-discipline-for-hot-side-structs.md, cache-line-discipline.md]
applies_at_skills: []
---

# Slow-path cfg resolution cache pattern — hoist scattered reads to cache-line-aligned struct

**Established:** 2026-05-13 (v5.15.5.F.4 sprint — pre-implementation draft)
**Status:** DRAFT v1.0 (pre-coding spec; promotes to ACTIVE after .F.4e ships)
**Cross-references:**
- Parent: `latency-vs-cache-decision-framework.md` (CLAUDE.md item 28; cycles vs cache misses cost math)
- Parent: `cache-layout-discipline-for-hot-side-structs.md` (alignas(64) + HOT/WARM/COLD tiering)
- Parent: `universal-cfg-field-registry-pattern.md` (cfg fields driving cache come from this registry)
- Parent: `per-bit-per-core-override-pattern.md` (per-node override resolution semantics)
- Composes with: `multi-bit-state-encoding-pattern.md` (K-state cfg enum cohort packing; CLAUDE.md item 30)
- Composes with: `avx512-byte-determinism-pattern.md` (potential AVX-512 batch-load of resolved struct; CLAUDE.md item 25)
- Composes with: `bitmap-flag-api.md` (cfg-flag bitmaps already resolved per-node; this extends to scalars)
- CLAUDE.md item 16 (reuse-audit); item 18 (slow-path latency reduction priority); item 19 (structural fix)

---

## Problem statement

Per slow-path cycle (`EventLoop_RebuildOneCore`), every core's slow-path body reads ~60 cfg scalar fields. Reads include:

- Direct: `cfg.bandit_blend_ratio`, `cfg.ml_buy_threshold`, `cfg.confidence_freshness_tau_secs`, etc. (~30 fields)
- FP conversions: `FPN_FromDouble(cfg.X)` per read (~10 fields)
- Bitmap extracts: `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_BANDIT_ENABLED)` (~12 bits across 5 bitmaps)
- Per-node override resolutions: `core_X_override_set[i] ? core_X[i] : cfg.X` (~8 fields)

Each read does NOT hit the same cache line. The Cfg struct is ~600 LOC of fields declared in DECLARATION ORDER (alphabetical / historical), not access-frequency order. Slow-path body reads scattered across ~12-18 cache lines per cycle.

### Cost math (per CLAUDE.md item 28)

At 3 GHz (current dev machine speed):
- L1 hit = ~1 ns / ~3 cycles
- L2 hit = ~4 ns / ~12 cycles
- L3 hit = ~13 ns / ~39 cycles
- DRAM miss (cold cache) = ~100 ns / ~300 cycles

If slow-path runs at 10ms intervals (typical poll_interval=100 × tick rate ~10 µs):
- Cold cache: 12-18 lines × ~100 ns = 1.2-1.8 μs per cycle per core
- Warm cache (L2): 12-18 lines × ~4 ns = 50-75 ns per cycle per core
- Multi-core contention (16 cores reading scattered cfg fields concurrently): cache-line bouncing on shared cfg struct adds 50-300 ns of L2/L3 traffic per cycle

**Per slow-path cycle, per core: 100-400 ns of cfg-read cost (warm), 1-2 μs (cold).**

At 100 cycles/sec/core × 16 cores: **~160-640 μs/sec on the cold path, ~5-30 ms/sec on cold-start surges.**

### What the fix achieves

Resolve all needed cfg fields ONCE at slow-path entry into a cache-line-aligned `ResolvedCoreCfg` struct. Downstream slow-path code reads from this resolved struct, not cfg.

- Resolved struct: ~3 cache lines (192 bytes) HOT-first ordered
- Per-cycle cost: 3 line loads × ~1 ns = ~3 ns per cycle per core
- Multi-core: each core has OWN resolved struct → zero contention

Savings: **~100-400 ns per cycle per core warm, ~1-2 μs cold.** At 100 × 16: **~160-640 μs/sec warm, ~1.6-3.2 ms/sec cold.**

Plus secondary wins: resolution happens at known entry point → branch predictor warm; per-node override resolution amortized to ONE branch per field instead of per-read.

---

## Design

### Resolved struct (cache-line-aligned, HOT-first)

```cpp
// CoreFrameworks/ResolvedCoreCfg.hpp — new file

template <unsigned F>
struct alignas(64) ResolvedCoreCfg {
    // ============================================================
    // CACHE LINE 0 (HOT — read every slow-path cycle) — 64 bytes
    // ============================================================
    FPN<F>   ml_buy_threshold;            // 24 bytes (FPN<64> = 24B per CLAUDE.md hot-path discipline)
    FPN<F>   ml_tp_pct;                   // 24 bytes
    uint16_t ml_cfg_flags_resolved;       // 2 bytes
    uint8_t  gate_cfg_flags_resolved;     // 1 byte
    uint8_t  lifecycle_cfg_flags_resolved;// 1 byte
    uint8_t  risk_cfg_flags_resolved;     // 1 byte
    uint8_t  ops_cfg_flags_resolved;      // 1 byte
    /* K-state enum cohort (item 30) — packed uint16_t */
    uint16_t k_state_word;                // 2 bytes [bandit_algo:1][engine_arch:1][risk_curve:2][barrier_blend:3][regime:2+2]
    uint8_t  _pad_line0[8];               // pad to 64B

    // ============================================================
    // CACHE LINE 1 (WARM — read most cycles but not all) — 64 bytes
    // ============================================================
    FPN<F>   confidence_freshness_tau_secs;
    FPN<F>   confidence_hard_block_threshold;
    FPN<F>   bandit_blend_ratio;
    /* ... */
    uint8_t  _pad_line1[N];

    // ============================================================
    // CACHE LINE 2 (COLD — read on regime change or rare paths) — 64 bytes
    // ============================================================
    FPN<F>   ridge_lambda;
    FPN<F>   ridge_cost_penalty;
    FPN<F>   ridge_min_ic_floor;
    /* ... */
    uint8_t  _pad_line2[N];

    static_assert(sizeof(ResolvedCoreCfg<F>) == 192,
                  "ResolvedCoreCfg<F> must be exactly 3 cache lines for AVX-512 batch-load future-work");
};
```

Per `cache-layout-discipline-for-hot-side-structs.md`:
- alignas(64) prevents false sharing across cores
- HOT fields first: most-frequently-read scalars near struct start
- WARM/COLD tiers: cache-line boundaries align natural read groupings
- Padding to cache-line multiples: enables AVX-512 batch-load (item 25)

### Resolution body (registry-driven, branchy override per item 28)

```cpp
// CoreFrameworks/ResolvedCoreCfg.hpp

// AUTOPOPULATE companion to FOREACH_CFG_FIELD (cfg registry):
// emit one resolution line per field with PER_CORE_OK or non-PER_CORE_OK
#define RESOLVE_CFG_LINE(kind_token, name, label, section, meta, payload, tooltip) \
    RESOLVE_CFG_LINE_IMPL_##kind_token(name, meta)

#define RESOLVE_CFG_LINE_IMPL_DOUBLE(name, meta) \
    resolved->name = FPN_FromDouble(RESOLVE_VAL_##meta(name));

// PER_CORE_OK: branchy override resolution (item 28 — predictable branch wins)
#define RESOLVE_VAL_PER_CORE_OK(name) \
    (cfg->core_##name##_override_set[core_idx] ? cfg->core_##name[core_idx] : cfg->name)

#define RESOLVE_VAL_NONE(name)  cfg->name
/* ... etc ... */

template <unsigned F>
inline void ResolveCoreCfg(const Cfg* cfg, int core_idx, ResolvedCoreCfg<F>* resolved) {
    FOREACH_CFG_FIELD(RESOLVE_CFG_LINE)
}
```

### Why branchy (not branchless) for override resolution

Per `latency-vs-cache-decision-framework.md` (CLAUDE.md item 28):

- `core_X_override_set[i]` is BOOT-SET, never changes mid-session.
- Branch predictor learns the per-node, per-field bit values in the first ~5 cycles; mispredict rate <1% steady-state.
- Branchy: `cmov` is 1-2 cycles when predicted; mispredict cost ~3-5 ns (~15 cycles).
- Branchless mask-select: ~2-3 cycles always (cmov or AND-select).

**Branchy wins by ~1 cycle per resolve × 60 fields = 60 cycles ≈ 20 ns per slow-path entry.** Item 28 explicitly: "When predictable branches stay (don't force branchless): branch predictor learns the pattern."

The override resolution itself runs ONCE per slow-path entry (not per downstream read). All downstream reads from `resolved->X` are L1-warm scalar loads = ~1 cycle each.

### K-state enum cohort packing (composes with item 30)

Six K-state cfg enums currently stored as separate ints/uint8_t:

| Field | States | Bits needed |
|---|---|---|
| `bandit_algorithm` | 2 (Exp3-IX / Thompson) | 1 |
| `engine_arch` | 2 (Centralized / Per-Node) | 1 |
| `risk_degradation_curve` | 4 (OFF / LINEAR / EXP / STEP) | 2 |
| `barrier_blend_mode` | 5 (LEGACY / BLEND / DOMINANT / SHADOW_A / SHADOW_B) | 3 |
| `regime_state_current` | 4 (RANGING / TRENDING / VOLATILE / MILD_TREND) | 2 |
| `regime_state_proposed` | 4 (same) | 2 |
| **Total** | | **11 bits → 2 bytes (uint16_t)** |

Currently: 6 × `int` fields = 24 bytes (or 6 × `uint8_t` = 6 bytes if compactly typed).

Packed into shared `k_state_word` (uint16_t = 2 bytes): **savings = 4-22 bytes per ResolvedCoreCfg × 16 cores = 64-352 bytes total slow-path budget.**

Access via item 30 inference API:
```cpp
#define K_BANDIT_ALGO_SHIFT       0
#define K_BANDIT_ALGO_MASK        0x0001
#define K_ENGINE_ARCH_SHIFT       1
#define K_ENGINE_ARCH_MASK        0x0002
#define K_RISK_CURVE_SHIFT        2
#define K_RISK_CURVE_MASK         0x000C
#define K_BARRIER_BLEND_SHIFT     4
#define K_BARRIER_BLEND_MASK      0x0070
#define K_REGIME_CURR_SHIFT       7
#define K_REGIME_CURR_MASK        0x0180
#define K_REGIME_PROP_SHIFT       9
#define K_REGIME_PROP_MASK        0x0600

// Access:
uint8_t bandit_algo = MBS_GET(resolved->k_state_word, K_BANDIT_ALGO_MASK, K_BANDIT_ALGO_SHIFT);

// Branchless multi-state predicate (regime in {RANGING, MILD_TREND}):
bool regime_calm = MBS_IN_SET(resolved->k_state_word, K_REGIME_CURR_MASK, K_REGIME_CURR_SHIFT,
                              (1 << REGIME_RANGING) | (1 << REGIME_MILD_TREND));
```

Branchless mask AND + cmp = 1-2 cycles. vs `switch (regime) case ...` = 3-10 cycles branchy. Net win for regime-class predicates.

### Per-node override storage layout — AoS-by-core (cache locality fix)

Currently the per-node override storage is structured as Struct-of-Arrays:

```cpp
struct Cfg {
    FPN<F>   core_bandit_blend_ratio[16];
    uint8_t  core_bandit_blend_ratio_override_set[16];
    FPN<F>   core_ml_buy_threshold[16];
    uint8_t  core_ml_buy_threshold_override_set[16];
    /* ... 8+ × per-core fields ... */
};
```

For core N's resolution, the slow-path body reads `core_bandit_blend_ratio[N]` + `core_ml_buy_threshold[N]` + ... — these are scattered across ~8 cache lines for core N alone.

**Re-layout: AoS-by-core (one struct per core, all overrides for that core in one cache line):**

```cpp
template <unsigned F>
struct alignas(64) PerCoreOverrides {
    // All per-core override values for this core in ONE cache line
    FPN<F>   bandit_blend_ratio;
    FPN<F>   ml_buy_threshold;
    FPN<F>   ml_tp_pct;
    /* ... up to 8 FPN<F> = 192 bytes = 3 cache lines per core ... */

    // Override-set bitmap in ONE word (1 bit per field)
    uint64_t override_set_mask;
};

struct Cfg {
    PerCoreOverrides<F> per_core_overrides[16];  // 16 cores × 3 lines = 48 cache lines TOTAL
};
```

**Cache-locality win:** Resolution for core N reads ONLY `per_core_overrides[N]` = 3 cache lines (vs scattered 8+ lines for SoA). ~5-cache-line savings per resolution × 16 cores × 100 cycles/sec = **~3-5 ms/sec total budget recovered** at cold-start; **~150-300 μs/sec warm.**

**Branchless override check via single mask AND:**
```cpp
bool override_set = (cfg->per_core_overrides[core_idx].override_set_mask >> field_idx) & 1;
```

Compose with item 30 inference API for mask compute.

---

## Robustness analysis

### What this closes

| Inefficiency | Before | After |
|---|---|---|
| Scattered cfg reads | 12-18 cache lines/cycle/core | 3 cache lines/cycle/core |
| Per-node override SoA scatter | 8+ cache lines/resolution | 3 cache lines/resolution |
| K-state enum byte-per-field | 6 × int = 24B | 1 × uint16_t = 2B |
| Per-read override branch | 60 branches/cycle | 60 branches at resolve only |
| Repeated FP conversion | FPN_FromDouble called every read | Converted once at resolve |

### What this enables

- **AVX-512 batch-load** (item 25): if ResolvedCoreCfg is 3 cache lines = 192B = 3 × `_mm512_load_pd` (8 doubles each = 192B exact). Slow-path entry can vector-load the entire resolved struct in 3 uops (~6 cycles) vs ~24 scalar loads (~24 cycles). Future-work; estimate ~30 ns/cycle/core savings.
- **K-state branchless predicates**: regime-class checks via mask AND vs switch-on-enum (item 30).
- **Branch predictor warmth**: resolution at known slow-path-entry point → predictor learns the override pattern in first ~5 cycles.

### Trade-offs

- **Slow-path entry adds ~60-cycle resolution overhead per core per cycle.** vs ~600-1800 cycles of scattered cfg reads saved. **Net win: 10-30x.**
- **ResolvedCoreCfg adds ~192 bytes per core × 16 cores = 3072 bytes of duplicated state.** Compared to ~2 MB of L1 budget per core: <1% L1 footprint.
- **Per-node AoS re-layout requires touching cfg struct field declarations + parser + save/load.** Mitigated: registry-driven (this pattern's parent) makes the change mechanical.

### When NOT to apply this pattern

- Hot-path cycles (not slow-path). Hot-path is already ~40-400 ns p99 budget; pre-resolving 60 fields doesn't fit. Hot-path reads ~3-5 cfg fields per tick from already-cached ExecutionCore::params — different pattern.
- Cfg fields that are ALREADY cache-warm (e.g., `cfg.live_trading` read 1000x per slow-path body — already in L1 after first read). The resolution overhead doesn't pay back.
- Cfg fields with COMPUTED values (e.g., derived from N other fields via Cfg_PostLoadSetup). Resolve once at boot, not per-cycle.

---

## Implementation checklist

When implementing the resolved cache:

1. **Define ResolvedCoreCfg struct** with alignas(64), HOT/WARM/COLD tiers.
2. **Auto-generate fields** from FOREACH_CFG_FIELD registry expansion (parent pattern). Apply HIDDEN_BY_DEFAULT to exclude boot-only fields from cache.
3. **Implement ResolveCoreCfg(cfg, core_idx, resolved)** via AUTOPOPULATE macro walk.
4. **Modify EventLoop_RebuildOneCore** to call ResolveCoreCfg at entry; downstream code reads `resolved->X` instead of `cfg->X`.
5. **K-state cohort migration** (separate sub-ship — uses item 30 inference API).
6. **Per-node override AoS-by-core re-layout** (separate sub-ship — touches cfg struct).
7. **Benchmark slow-path latency** before + after with perf record / cycle counters.
8. **Verify byte-identical determinism** in backtest: same cfg + same ticks → same outputs.

---

## Cross-spec optimization checklist

Verify these compose correctly:

- [ ] **Item 16 (reuse-audit):** confirm resolution merges previously-duplicated cfg reads across slow-path consumers (RegimeDetector, MeanReversion, ExitPredictor, ...).
- [ ] **Item 17 (HOT_PATH_CHANGELOG):** resolution body adds ~60 cycles per slow-path entry per core; document in changelog.
- [ ] **Item 18 (slow-path priority):** measure cycle delta in p99 before/after; confirm <100 μs p99 maintained.
- [ ] **Item 20 (BITMAP_*):** override_set_mask is a bitmap; use BITMAP_IS_SET for query.
- [ ] **Item 23 (tt:: dispatch):** RESOLVE_CFG_LINE_IMPL_<KIND> macros are kind-specific; matches tt:: parser pattern.
- [ ] **Item 25 (AVX-512 batch-load):** ResolvedCoreCfg sized to N × 64 bytes; future-work AVX load is 1-2 uops per cache line.
- [ ] **Item 26 (branchless math kernel):** resolution body is constant-iter (FOREACH expansion); no `if` guards inside.
- [ ] **Item 28 (latency-vs-cache):** branchy override = predictable branch wins. Document in changelog.
- [ ] **Item 30 (multi-bit state):** K-state cohort packed; branchless predicates via mask AND.

---

## Future work (not in initial scope)

- **Sub-cache-line struct prefetch** at slow-path entry: `__builtin_prefetch(&cfg->per_core_overrides[core_idx])` issued at cycle entry; hides L2 → L1 latency of resolution.
- **AVX-512 batch-load** of entire resolved struct (3 × 64-byte cache lines = 3 uops).
- **Per-cycle resolved struct delta-cache:** if cfg hasn't changed since last cycle (override_set bits + cfg.epoch unchanged), reuse last cycle's resolved struct. Saves resolution overhead entirely. Cost: 1 cycle epoch compare.
- **Compose with snapshot publish:** PerCoreSnap could publish a DIGEST of resolved struct (xxhash) for display-side drift detection. Catches "GUI shows X but engine acts on Y" via snapshot mismatch.

---

## Field-test plan

Implement in 2-3 sub-ships:

- **.F.4e (Phase 1):** Resolved struct + ResolveCoreCfg + slow-path body migration (read `resolved->X` instead of `cfg->X` everywhere in RebuildOneCore). Verify backtest determinism + measure cycle delta.
- **.F.4f (Phase 2 — K-state cohort):** Pack the 6 K-state enums via item 30; convert switch-on-enum predicates to branchless mask AND. Verify backtest determinism.
- **.F.4g (Phase 3 — AoS-by-core re-layout):** Re-layout per-node override storage from SoA to AoS-by-core. Touches cfg struct + parser + save/load. Verify backtest determinism + measure cache-miss delta via perf stat.

Each phase is independently testable; rollback anchor at each tag.
