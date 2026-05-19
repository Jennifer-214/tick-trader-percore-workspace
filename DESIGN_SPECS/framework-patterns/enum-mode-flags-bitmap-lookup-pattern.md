---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-12
tags: [framework-discipline, data-oriented-design, branchless-discipline]
surface: [registry, bitmap-packed, hot-path]
sister_specs: [universal-registry-bitmap-dispatcher-pattern.md, x-macro-registry-with-presence-dispatch.md, bitmap-flag-api.md]
applies_at_skills: []
---

# Enum Mode-Flags Bitmap Lookup Pattern

**Status:** ACTIVE (formalized 2026-05-12; first application v5.15.5.A.1
FOREACH_BARRIER_BLEND_MODE with MODE_FLAGS[] table).
**CLAUDE.md cross-ref:** items 13 (X-macro registry), 17 (latency
tracking), 18 (slow-path branch minimization), 20 (BITMAP_* API),
26 (branchless math kernel), 28 (latency-vs-cache decision framework).

## Problem

A feature has multiple named MODES with per-mode BEHAVIOR FLAGS — e.g.,
"this mode writes blend value; that mode writes dominant value; this
other mode does both and logs one for shadow telemetry." Each cycle's
dispatch must select behavior based on the active mode.

Naïve approach: nested if/else on the enum value:

```cpp
if (mode == LEGACY) {
    tp_pct = cfg.ml_tp_pct;
} else if (mode == BLEND) {
    tp_pct = blend_value;
} else if (mode == DOMINANT) {
    tp_pct = dominant_value;
} else if (mode == BOTH_BLEND_DRIVES) {
    tp_pct = blend_value;
    shadow_record_dominant();
} else if (mode == BOTH_DOMINANT_DRIVES) {
    tp_pct = dominant_value;
    shadow_record_blend();
}
```

**Recurring pain points:**
1. **N branches per dispatch.** Branch predictor handles cfg-stable
   modes well in steady state, but mask-compute is faster + more
   predictable (CLAUDE.md item 28 decision framework — branchless
   beats branchy at >N/16% mispredict; per-cycle dispatch IS
   data-dependent enough to favor branchless).
2. **Adding a new mode touches N+ sites:** enum + if-chain + cfg
   parser + tests. Per CLAUDE.md item 13, ≥2 sites = registry
   territory.
3. **Behavior flags duplicate across consumers.** If 3 different
   dispatch sites all need to test "does this mode shadow-log?",
   each writes its own `if (mode == BOTH_BLEND_DRIVES || mode ==
   BOTH_DOMINANT_DRIVES)` chain — duplication that drifts.
4. **No reflection.** "List modes that drive blend" requires a
   parallel string table the operator keeps in sync.

## Pattern — X-macro registry with bit-packed FLAGS column + auto-generated lookup table

### Step 1 — define per-mode bit semantics

```cpp
// Each behavior axis becomes a 1-bit flag in the lookup-table value.
// 4 bits used today; 4 bits free for future modes.
constexpr uint8_t MODE_F_BLEND_DRIVES    = BITMAP_BIT_U8(0);  // 0x01
constexpr uint8_t MODE_F_DOMINANT_DRIVES = BITMAP_BIT_U8(1);  // 0x02
constexpr uint8_t MODE_F_SHADOW_ACTIVE   = BITMAP_BIT_U8(2);  // 0x04
constexpr uint8_t MODE_F_LEGACY          = BITMAP_BIT_U8(3);  // 0x08
```

### Step 2 — X-macro tuple with flags column

```cpp
// Tuple: X(name, mode_flags_expr, doc_string)
//   name        — UPPERCASE token; used for MODE_<X>_<name> enum
//   mode_flags  — MODE_F_* bitmap composition (OR-combined per mode)
//   doc_string  — engine.cfg.example auto-doc

#define FOREACH_BARRIER_BLEND_MODE(X) \
    X(LEGACY,                MODE_F_LEGACY,                                  "cfg-direct fallback") \
    X(BLEND,                 MODE_F_BLEND_DRIVES,                            "weighted blend drives") \
    X(DOMINANT,              MODE_F_DOMINANT_DRIVES,                         "argmax arm drives") \
    X(BOTH_BLEND_DRIVES,     MODE_F_BLEND_DRIVES | MODE_F_SHADOW_ACTIVE,     "blend drives + shadow log") \
    X(BOTH_DOMINANT_DRIVES,  MODE_F_DOMINANT_DRIVES | MODE_F_SHADOW_ACTIVE,  "dominant drives + shadow log")
```

### Step 3 — auto-generate enum

```cpp
enum {
#define X(id, flags, doc) MODE_BARRIER_BLEND_##id,
    FOREACH_BARRIER_BLEND_MODE(X)
#undef X
    MODE_BARRIER_BLEND_COUNT
};
```

### Step 4 — auto-generate MODE_FLAGS[] lookup table

```cpp
constexpr uint8_t MODE_FLAGS[MODE_BARRIER_BLEND_COUNT] = {
#define X(id, flags, doc) [MODE_BARRIER_BLEND_##id] = (uint8_t)(flags),
    FOREACH_BARRIER_BLEND_MODE(X)
#undef X
};
```

This is the LOAD-BEARING piece. The lookup table is indexed by the
mode enum value; each entry holds the bit-packed semantic flags.

### Step 5 — consumer branchless dispatch

```cpp
// Slow-path dispatch:
uint8_t flags = MODE_FLAGS[mode];               // 1 cycle (L1 hit on small table)
bool blend_drives    = flags & MODE_F_BLEND_DRIVES;     // cmov, no branch
bool dominant_drives = flags & MODE_F_DOMINANT_DRIVES;  // cmov, no branch
bool shadow_active   = flags & MODE_F_SHADOW_ACTIVE;    // cmov, no branch

// Single branchless ternary chain — no nested if/else:
FPN<F> tp_pct = blend_drives    ? blend_value
              : dominant_drives ? FPN_FromDouble<F>(per_arm_barriers[dominant_h].tp)
              : config->ml_tp_pct;

if (shadow_active) {
    // shadow record (one branch — predictable; only fires in modes 3+4)
    record_shadow(...);
}
```

### Step 6 — accessor helpers (optional but recommended)

```cpp
static inline bool BarrierBlendMode_BlendDrives(int mode) {
    if (mode < 0 || mode >= MODE_BARRIER_BLEND_COUNT) return false;
    return (MODE_FLAGS[mode] & MODE_F_BLEND_DRIVES) != 0;
}
// + DominantDrives, ShadowActive, IsLegacy
```

Hides the lookup-table indexing from consumer sites; centralizes the
out-of-range bounds check.

## Why this pattern over alternatives

| Approach | Dispatch cost | Mispredict cost | Add new mode | Reflection |
|---|---|---|---|---|
| Nested if/else | 1-N branches | 30-50% on data-dependent | 5+ sites (enum, ifs, parser, doc, tests) | Manual parallel table |
| `switch` on enum | 1 branch (jump table at -O2+) | Branch predictor helps when cfg-stable | 5+ sites | Manual |
| **Function pointer table** (curve-registry-pattern) | 1 indirect call (~1-2ns) | N/A | 1 row in FOREACH + fn definition | Auto via registry |
| **MODE_FLAGS[] bit-packed lookup** (this pattern) | 1 L1 load + N mask-AND (~1ns total) | NONE (branchless via cmov) | 1 row in FOREACH + flag expression | Auto via registry |

**When MODE_FLAGS[] wins over function-pointer table:**
- Behavior at dispatch is data-flow oriented (assign A vs B vs both) rather than algorithm-oriented (call function A vs B with shared signature). MODE_FLAGS[] is for the FORMER; curve-registry is for the LATTER.
- Multiple INDEPENDENT behavior axes per mode (drives_blend ⊥ shadow_active ⊥ legacy_fallback). Function pointer table forces ONE axis (the function); flag bitmap allows N axes via N bits.
- Consumer wants branchless cmov dispatch, not indirect call. CMov pipeline-friendlier than indirect calls on modern CPUs.

**When function pointer table (curve-registry-pattern) wins:**
- Each mode has DIFFERENT compute math, not just different output assignment. Function pointer is the natural shape.
- Mode-specific state needs to live with the function (closures, per-mode statics, etc.).
- Branch prediction is reliable (mode-stable over many cycles).

## Sister patterns

| Pattern | When to use |
|---|---|
| `curve-registry-pattern.md` | Per-enum named compute functions (linear / exp / step curves; bandit algorithms; label fns) |
| `slow-path-gate-registry-pattern.md` | Boolean gates cached at slow-path entry from cfg (gate state, not behavior dispatch) |
| `bitmap-flag-api.md` | Bit-packed flag storage on STRUCTS (per-record state; not per-enum-value semantics) |
| `heterogeneous-registry-pattern.md` | Single registry with mixed-shape entries; SCOPE COLUMN dispatch |
| **`enum-mode-flags-bitmap-lookup-pattern.md` (this)** | Per-enum bit-packed BEHAVIOR FLAGS; consumers do branchless mask-AND for dispatch |

## Sizing reference

- 4 flags per mode → uint8_t MODE_FLAGS[]; 4-8 modes fit comfortably
- 9-16 flags per mode → uint16_t MODE_FLAGS[]
- 17-32 flags per mode → uint32_t MODE_FLAGS[]
- N modes × M flags storage = N×sizeof(uint?_t) bytes; typically < 64B = 1 cache line

For typical use case (4-8 modes × 4-8 flags), MODE_FLAGS[] table fits
in 8-64 bytes — single cache line, single L1 load per dispatch site.

## Compile-time enforcement

```cpp
// Sanity asserts that registry hasn't been silently corrupted:
static_assert(MODE_BARRIER_BLEND_COUNT == 5, "expected 5 entries for v5.15.5");

// Per-mode behavior validation (catches operator typos in flags column):
static_assert(MODE_FLAGS[MODE_BARRIER_BLEND_LEGACY] == MODE_F_LEGACY,
              "LEGACY mode must map to MODE_F_LEGACY exactly");
static_assert((MODE_FLAGS[MODE_BARRIER_BLEND_BOTH_BLEND_DRIVES] &
                MODE_F_SHADOW_ACTIVE) != 0,
              "BOTH_BLEND_DRIVES must have shadow active");
```

These asserts catch:
- Flags column dropped from a registry row (compile error or 0-value)
- Operator typo in mode_flags expression
- Reordering that flips canonical mode → flags mapping

## Cache-locality posture

MODE_FLAGS[] is a constexpr array stored in `.rodata`. At runtime:
- First access: 1 L1 fetch (or L2/L3 if cold). ~1-13 ns.
- Subsequent accesses (same cycle, repeated dispatch sites): L1 hit. ~1 ns each.

The table is small (typically 5-16 bytes) and stable; the branch
predictor + L1 cache make repeated lookups essentially free per
CLAUDE.md item 28 cost reference.

No false sharing risk (constexpr/rodata; read-only across all threads).

## Reference applications

| Ship | Registry | Modes | Flags |
|---|---|---|---|
| **v5.15.5.A.1** (first) | FOREACH_BARRIER_BLEND_MODE | 5 (LEGACY/BLEND/DOMINANT/BOTH_BLEND/BOTH_DOMINANT) | 4 (MODE_F_BLEND_DRIVES/DOMINANT_DRIVES/SHADOW_ACTIVE/LEGACY) |

Future candidates (not yet applied; promotion guarantor for the pattern):
- `bandit_algorithm` modes (EXP3 / THOMPSON / BOTH / future symmetric)
  could grow MODE_F_DRIVES_DECISION / MODE_F_LOGS_SHADOW / MODE_F_USES_PRIOR
  flags via this pattern, simplifying the v5.14.10 dual-mode dispatch
- Future risk-tier enums (kill_switch_severity, drift_response_action,
  exit_predictor_threshold_curve) likely fit
- v6.0+ maker-order-strategy modes (queue-position / book-replay /
  liquidity-rebate routing) — each mode has multiple semantic flags

## Promotion criteria

Per CLAUDE.local.md "codify design principles" rule (2026-05-09),
pattern promoted to DESIGN_SPEC when:
1. ≥2 applications in codebase, OR
2. Generalizable + single application + operator-requested documentation
   (Caramel 2026-05-12: "is this a design spec or just reusing an existing
   one?" + greenlight for option-a documentation now)

This pattern qualifies via (2) — generalizable enum-dispatch shape with
1 application (BarrierBlendModeRegistry) + immediate future application
slot (bandit_algorithm symmetric extension in v5.15.5.G). Promoted now
to lock the canonical pattern shape before the 2nd application diverges.

## Cross-references

- `CLAUDE.md` items 13, 17, 18, 20, 26, 28
- `DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md` (base X-macro pattern)
- `DESIGN_SPECS/framework-patterns/curve-registry-pattern.md` (sister: function pointer dispatch)
- `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md` (BITMAP_* macros used in MODE_F_* constants)
- `DESIGN_SPECS/data-disciplines/cache-layout-discipline-for-hot-side-structs.md` Rule 8 Pattern 8b (branchless mask dispatch)
- `DESIGN_SPECS/refactor-patterns/latency-vs-cache-decision-framework.md` (why branchless wins over branchy at >N/16% mispredict)
- `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md` (registry as the structural fix per item 19)
- `ML_Headers/BarrierBlendModeRegistry.hpp` (canonical first application)
