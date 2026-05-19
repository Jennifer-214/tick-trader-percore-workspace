---
type: refactor-pattern
stage: 5-claude-md
version: 1.1
established: 2026-05-13
tags: [data-oriented-design, branchless-discipline, structural-fix]
surface: [bitmap-packed, hot-path]
sister_specs: [bitmap-flag-api.md, registry-bitmap-set-discipline.md, aggressive-memory-reduction-techniques.md, multi-state-dispatch-with-per-state-update-metadata.md]
applies_at_skills: []
---

# Multi-bit state encoding + branchless inference API

**Established:** 2026-05-13 (post-v5.15.5.C.2); **v1.1 Path γ+ v2 canonical count correction (2026-05-17)**
**Status:** **Stage 5 v1.1 (count corrected 2026-05-17)** — INVARIANT promotion at `.F.4d` claimed 5 canonical applications but only **2 actually shipped at engine HEAD `545b087`**: EVENT_LOG_MODE + Order::flags_packed bandit context bits 17-25. The other 3 canonicals (DriftOverride + RegistryRosterEntry + ManualFieldInventoryEntry) land at `v5.15.5.F.4d.1.C` ship close (TECH_DEBT-085 Path γ+ v2 sub-ship .C). **INVARIANT promotion accurately becomes 5 canonicals at `.C` ship close synchronization** — until then, status is Stage 5 with 2 confirmed canonicals (still meets CLAUDE.md item 30 promotion threshold per ≥2 applications). Per D4 audit + Path γ+ v2 triage 2026-05-17 per `plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` § Finding 2 (3rd DRIFT-MAJOR canonical-count claim correction). Spec body content describes the pattern correctly; only the application-count badge was inflated.
**Tags:** structural-fix, framework-discipline, hot-path-cache-density; closes byte-waste anti-pattern + Class 14 (spec-vs-code application-count drift correction); serves H6 (cache-line discipline) + H12 (struct padding determinism); Stage 5 (CLAUDE.md item 30 — promoted at `.F.4d` with 2 canonicals); 2 applications at HEAD; 5 at `.C` ship close
**Cross-references:**
- Sister pattern: `bitmap-flag-api.md` (the 1-bit specialization — N booleans into 1 word)
- Generalizes: same compressive-storage philosophy as Portfolio<uint16_t> (CLAUDE.md item 1)
- Composition substrate: `x-macro-registry-with-presence-dispatch.md` (registry generates state constants; storage uses N-bit slots)
- Related: CLAUDE.md item 28 (latency-vs-cache decision framework — when packing wins)
- Related: CLAUDE.md item 20 (per-record-not-across-records storage discipline)
- Anti-pattern this replaces: `int enum_field` storing K-state value (wastes 32-N bits per record)

---

## Problem statement

The codebase has many K-state fields stored as `int` (4 bytes) or `uint8_t` (1 byte) when the actual information content is `ceil(log2(K))` bits.

Examples:
- `RegimeClassification rs_current` — 4 states (RANGING/TRENDING/VOLATILE/MILD_TREND). Stored as `int` = 32 bits. **Information content: 2 bits.** 30 bits wasted per field.
- `strategy_id` — 4-5 strategies (SIMPLE_DIP/MOMENTUM/EMA_CROSS/ML/+future). Stored as `uint8_t` = 8 bits. **Information content: 3 bits.** 5 bits wasted per slot.
- `OrderType` — 4-8 types (BUY/SELL/LIMIT_BUY/LIMIT_SELL/CANCELED/...). Stored as `uint8_t` = 8 bits. **Information content: 3 bits.** 5 bits wasted per order.
- `TradeEventType` — 3 states (ENTRY/EXIT/COMBINED). Stored as `uint8_t` = 8 bits. **Information content: 2 bits.**

Compounded over per-core / per-slot / per-order structs, this is hundreds of bytes of waste in HOT-cluster cache lines that would otherwise hold useful data.

Beyond memory waste, the per-state `switch` / `if-else` dispatch pattern at consumer sites is branch-predictor-unfriendly when state varies cycle-to-cycle, and can be replaced with branchless multi-bit primitives that compile to 1-2 cycle ops.

---

## The math (first principles)

A bit holds 2 states (0/1). N bits hold 2^N states. Therefore:

| Bits | States | Common applications |
|---|---|---|
| 1 | 2 | Boolean flags — `bitmap-flag-api.md` |
| 2 | 4 | Regime, trade-event-type, order-side+maker |
| 3 | 8 | Strategy ID, order types, halt-reason codes |
| 4 | 16 | Feature IDs, position slots (Portfolio.active_bitmap precedent) |
| 5 | 32 | Larger enum spaces (still rare in trading hot paths) |
| 6-8 | 64-256 | Use full uint8_t — multi-bit packing offers little win |

A boolean field carries 1 bit of information but conventional code wastes 7 bits per boolean by using a whole byte (Shannon's source coding bound). For K-state fields the analogous waste is `8 - ceil(log2(K))` bits per byte, or `32 - ceil(log2(K))` bits per int.

**This pattern packs K-state fields to their information-theoretic minimum within the constraints of byte-aligned struct storage** — multiple K-state fields share a single byte/uint16_t when they belong to the same access pattern.

---

## Design space explored

### Option A: enum int (current state of art for non-flag enums)

```cpp
enum RegimeClassification { REGIME_RANGING = 0, REGIME_TRENDING = 1, ... };
struct CoreContext {
    int rs_current;        // 4 bytes; 30 bits wasted
    int rs_proposed;       // 4 bytes; 30 bits wasted
};
```

Rejected baseline: 32-bit storage for 2-bit information; switch-dispatch incurs branch prediction overhead.

### Option B: uint8_t with single value per byte

```cpp
struct CoreContext {
    uint8_t rs_current;    // 1 byte; 6 bits wasted
    uint8_t rs_proposed;   // 1 byte; 6 bits wasted
};
```

Better than A but still wastes 6 bits per field. Multi-state set membership and conditional dispatch still incur branch costs.

### Option C (chosen): N-bit packed slot within a shared word

```cpp
struct CoreContext {
    uint8_t regime_field;  // bits[0..1] = current, bits[2..3] = proposed, bits[4..7] reserved
};
```

Information-theoretic minimum storage (2 bits + 2 bits = 4 bits in 1 byte). Branchless inference API replaces switch dispatch with mask + shift + lookup. Compose with X-macro registry to auto-generate per-state constants.

### Option D (rejected): bit-pack across records

Take `regime` field out of CoreContext into a top-level cross-core packed array:
```cpp
uint64_t all_cores_regimes;  // 4 cores × 2 bits + padding
```

Rejected per CLAUDE.md item 20 — bit-packing across records breaks per-record cache locality unless cross-record scan is the dominant access pattern. For regime, per-core access dominates (each slow-path cycle reads its own core's regime), so per-record packing wins.

---

## The pattern (concrete shape)

### Step 1 — X-macro registry generates state constants

```cpp
// FOREACH_REGIME_STATE(X) — tuple: X(name, bit_value)
#define FOREACH_REGIME_STATE(X)         \
    X(RANGING,    0b00)                  \
    X(TRENDING,   0b01)                  \
    X(VOLATILE,   0b10)                  \
    X(MILD_TREND, 0b11)

// Auto-generated value constants:
#define X_GEN_REGIME(name, val) constexpr uint8_t REGIME_##name = (uint8_t)val;
FOREACH_REGIME_STATE(X_GEN_REGIME)
#undef X_GEN_REGIME

// Static checks:
static_assert(REGIME_RANGING < 4,  "regime values fit in 2 bits");
static_assert(REGIME_MILD_TREND < 4, "regime values fit in 2 bits");
```

### Step 2 — Storage uses N-bit slot within a shared word

```cpp
struct CoreContext {
    // bits[0..1] = rs_current  (2-bit regime — 4 states)
    // bits[2..3] = rs_proposed (2-bit regime — 4 states)
    // bits[4..7] reserved for future regime-related state
    uint8_t regime_field;
};

// Field-position macros:
#define REGIME_CURRENT_SHIFT   0
#define REGIME_CURRENT_MASK    0x03u   // (1u << 2) - 1
#define REGIME_PROPOSED_SHIFT  2
#define REGIME_PROPOSED_MASK   0x0Cu   // 0x03 << 2
```

### Step 3 — Branchless accessor macros (the inference API)

These all compile to 1-2 instruction ops. No branches on the hot path.

```cpp
//----------------------------------------------------------------------
// EXTRACTION — read the K-state value out of the packed word
//----------------------------------------------------------------------
// Single uop: AND + SHR (compiler often fuses into BMI BEXTR).
#define MBS_GET(field, mask, shift) \
    ((uint8_t)(((field) & (mask)) >> (shift)))

#define REGIME_CURRENT_GET(field) \
    MBS_GET((field), REGIME_CURRENT_MASK, REGIME_CURRENT_SHIFT)
#define REGIME_PROPOSED_GET(field) \
    MBS_GET((field), REGIME_PROPOSED_MASK, REGIME_PROPOSED_SHIFT)

//----------------------------------------------------------------------
// MUTATION — write a new K-state value into the packed word
//----------------------------------------------------------------------
// Two ops: AND + OR. Branchless.
#define MBS_SET(field, mask, shift, value) \
    ((field) = (uint8_t)(((field) & (uint8_t)~(mask)) | \
                          (((uint8_t)(value) << (shift)) & (mask))))

#define REGIME_CURRENT_SET(field, val) \
    MBS_SET((field), REGIME_CURRENT_MASK, REGIME_CURRENT_SHIFT, (val))

//----------------------------------------------------------------------
// EQUALITY CHECK — branchless test for "state == VAL"
//----------------------------------------------------------------------
// Single CMP. No branch (modern CPUs SETcc into a register).
#define MBS_EQ(field, mask, shift, val) \
    (MBS_GET((field), (mask), (shift)) == (uint8_t)(val))

#define REGIME_IS_CURRENT(field, name) \
    MBS_EQ((field), REGIME_CURRENT_MASK, REGIME_CURRENT_SHIFT, REGIME_##name)
// Usage:  if (REGIME_IS_CURRENT(ctx.regime_field, TRENDING)) { ... }

//----------------------------------------------------------------------
// SET MEMBERSHIP — branchless test for "state in subset S"
//----------------------------------------------------------------------
// Precompute a "set mask" with 1 bit per state in S. Test via:
//   ((SET_MASK >> state_value) & 1) != 0
// Single SHR + AND + compare. Branchless.
//
// Build SET_MASK at compile time as `(1 << val_A) | (1 << val_B) | ...`
// One bit per state value (not per bit position in the storage word).
// Bit N of SET_MASK = "state value N is a member".
constexpr uint16_t REGIME_SET_RISKY =
    (1u << REGIME_TRENDING) | (1u << REGIME_VOLATILE);
constexpr uint16_t REGIME_SET_QUIET =
    (1u << REGIME_RANGING)  | (1u << REGIME_MILD_TREND);

#define MBS_IN_SET(field, mask, shift, set_mask) \
    ((((set_mask) >> MBS_GET((field), (mask), (shift))) & 1u) != 0)

#define REGIME_CURRENT_IS_RISKY(field) \
    MBS_IN_SET((field), REGIME_CURRENT_MASK, REGIME_CURRENT_SHIFT, REGIME_SET_RISKY)
// Usage:  if (REGIME_CURRENT_IS_RISKY(ctx.regime_field)) { reduce_size(); }

//----------------------------------------------------------------------
// STATE-DRIVEN VALUE DISPATCH — branchless replacement for switch
//----------------------------------------------------------------------
// Lookup table indexed by state value. 1 array deref. No branch.
// Compiler emits a single MOV from constant-data section.
//
// Example: per-regime fee multiplier.
constexpr FPN<64> REGIME_FEE_MULT[4] = {
    /*RANGING*/    FPN_FromConst<64>(1.0),
    /*TRENDING*/   FPN_FromConst<64>(0.9),
    /*VOLATILE*/   FPN_FromConst<64>(1.5),
    /*MILD_TREND*/ FPN_FromConst<64>(1.0),
};
#define REGIME_FEE_MULT_FOR(field) \
    REGIME_FEE_MULT[REGIME_CURRENT_GET(field)]
// Usage:  FPN<64> mult = REGIME_FEE_MULT_FOR(ctx.regime_field);

//----------------------------------------------------------------------
// CONDITIONAL COMPUTE — branchless "if state == X then A else B"
//----------------------------------------------------------------------
// Build mask -(state == X) where mask = 0xFF..FF (all-1) when true, 0 when false.
// Result = (A & mask) | (B & ~mask). Branchless conditional move.
//
// For HOT path use only when both A and B are cheap to compute up front.
#define MBS_SELECT_EQ(field, mask, shift, val, a, b)              \
    (((a) & -(uintptr_t)MBS_EQ((field), (mask), (shift), (val))) | \
     ((b) & ~(-(uintptr_t)MBS_EQ((field), (mask), (shift), (val)))))

//----------------------------------------------------------------------
// TRANSITION PREDICATE — branchless "allowed_transitions[from][to]"
//----------------------------------------------------------------------
// For K-state where transitions are constrained, encode the K×K allowed
// matrix as bits in a uint16_t / uint32_t / uint64_t. 4 states → 16 bits.
//
// allowed_matrix bit (from * K + to) = 1 if transition (from → to) is legal.
// Predicate: (allowed_matrix >> (from*K + to)) & 1. Single SHR + AND.
constexpr uint16_t REGIME_TRANSITION_MATRIX = 0
    | (1u << (REGIME_RANGING*4    + REGIME_TRENDING))    // RANGING -> TRENDING ok
    | (1u << (REGIME_RANGING*4    + REGIME_MILD_TREND))  // RANGING -> MILD_TREND ok
    | (1u << (REGIME_TRENDING*4   + REGIME_VOLATILE))    // TRENDING -> VOLATILE ok
    | (1u << (REGIME_TRENDING*4   + REGIME_RANGING))     // TRENDING -> RANGING ok
    | (1u << (REGIME_VOLATILE*4   + REGIME_RANGING))     // VOLATILE -> RANGING ok
    | (1u << (REGIME_MILD_TREND*4 + REGIME_TRENDING))    // MILD_TREND -> TRENDING ok
    | (1u << (REGIME_MILD_TREND*4 + REGIME_RANGING));    // MILD_TREND -> RANGING ok

#define REGIME_CAN_TRANSITION(from, to)                       \
    (((REGIME_TRANSITION_MATRIX >> ((from) * 4 + (to))) & 1u) != 0)
```

### Step 4 — Population in registry-driven code generation

Use the X-macro to generate lookup tables and validators:

```cpp
// Auto-generate string names for debug / log output:
#define X_GEN_NAME(name, val) [REGIME_##name] = #name,
constexpr const char* REGIME_NAME[] = { FOREACH_REGIME_STATE(X_GEN_NAME) };
#undef X_GEN_NAME

// Auto-generate count for static asserts:
#define X_COUNT_ONE(name, val) +1
constexpr int REGIME_STATE_COUNT = (0 FOREACH_REGIME_STATE(X_COUNT_ONE));
#undef X_COUNT_ONE

static_assert(REGIME_STATE_COUNT <= 4, "Increase regime field bit width if 5+ states");
```

---

## Parallel multi-slot decode (the "single clock cycle" pattern)

When a packed word holds 2+ K-state slots that are accessed together, you can decode all slots in 1-2 cycles total via instruction-level parallelism + special CPU instructions.

### Why ILP works on packed slots

Each slot extract is `(byte >> shift_i) & mask_i`. The N extract operations have **no data dependency on each other** — they all read the same source byte but produce independent destinations. Modern superscalar x86 (Haswell+, Zen+) issues 4-5 ALU ops per cycle. So decoding 4 slots from a single byte takes ~1-2 cycles total when issued together, vs 4×~1 cycle if serialized.

```cpp
// Naive: serialized read, ~4-5 cycles total (each AND+SHR depends on prior register)
uint8_t s0 = (packed >> 0) & 0x3;
uint8_t s1 = (packed >> 2) & 0x3;
uint8_t s2 = (packed >> 4) & 0x3;
uint8_t s3 = (packed >> 6) & 0x3;

// ILP-friendly: load packed once, write 4 independent regs.
// Modern compilers emit this from naive form. Verify with godbolt
// or `-S` if hot path. ~1-2 cycles measured.
```

### BMI2 PEXT — single-instruction arbitrary-bit extract

On Haswell+ (and Zen2+), the BMI2 `PEXT` instruction extracts arbitrary masked bits in 1 cycle:
```cpp
#include <x86intrin.h>
// Extract bits [0..1, 4..5] (e.g., regime + a non-adjacent flag) into low bits.
uint64_t mask = 0x33;  // bits we want
uint64_t out = _pext_u64(packed, mask);
// 'out' contains compacted extracted bits.
```

Useful when slots are non-adjacent or when you want to compact a wide bitmap into dense indices in one op. Not needed for adjacent slots in the same byte — a regular AND+SHR is already 1 cycle there.

### Batch decode of arrays via SIMD

When decoding an ARRAY of packed bytes (e.g., `uint8_t meta[16]` per portfolio slot), AVX-512 can process 64 bytes at a time:
```cpp
// AVX-512 byte-shuffle decodes 64 packed bytes into 64 extracted slot-0 values.
// _mm512_and_si512 with broadcast mask + _mm512_srli_epi8 for shift.
__m512i packed = _mm512_load_si512((__m512i*)meta);
__m512i mask   = _mm512_set1_epi8(0x3);  // 2-bit mask broadcast
__m512i slot0  = _mm512_and_si512(packed, mask);
// slot0 now holds 64 decoded "regime" values.
```

When the consumer iterates over a packed array (e.g., per-cycle per-core decode of all packed slots), AVX-512 collapses 16-64 sequential decodes into a single SIMD op. Combine with the AVX-512 byte-determinism discipline (CLAUDE.md item 25) for replay-safety.

### Cross-slot multi-state queries (one-instruction predicates)

When asking "do all 4 slots hold the same target value V?", build a packed target and compare directly:
```cpp
// All 4 slots are 2-bit; target value V repeats: VVVV in pattern 0xAA where V=2.
constexpr uint8_t MASK_ALL_SLOTS_V = 0b10101010;  // V=2 (0b10) repeated 4×
bool all_v = (packed == MASK_ALL_SLOTS_V);  // single CMP, no decode needed
```

For "any slot is in subset S?":
```cpp
// MASK_ANY_RISKY: 1 bit per slot-position where slot value ∈ S.
// Computed at compile time as bitmask over slot positions.
// Then: byte AND mask != 0  → any slot is risky.
```

For "count of slots in state V" across the byte: `popcount(packed XOR repeated_V_pattern)` masked appropriately. Single PEXT+POPCNT+CMP combo on Haswell+ (3 cycles).

### When this matters

Hot-path or per-cycle slow-path code that iterates many packed records. Cold-cache penalty (1 cache miss = ~300 cycles per CLAUDE.md item 28) usually dominates the decode cost — the optimization is "decode is free relative to cache load", so the question becomes "did we save cache lines?" If yes (multi-bit packing collapses N bytes → 1), the decode cost is negligible vs the avoided cache misses.

Worked numbers from item 28's framework:
- Pre-pack: 2 fields × 1 byte = 2 cache touches per record, 32 cache touches across 16 records (or 2 cache lines if dense, 32 lines if scattered)
- Post-pack: 1 byte per record = 16 cache touches across 16 records (1 cache line if dense)
- Decode cost: ~1-2 cycles per slot × N slots = negligible vs cache miss savings

### Caveat: branch on decoded value still costs

The decode itself is branchless + parallel, but if you `switch` on each decoded slot independently, you re-introduce branches. Pair the parallel decode with the dispatch-table pattern (`fns[state]()`) for a fully branchless pipeline.

### Width-independence — N×M-bit packing generalizes

The parallel-decode discipline applies **regardless of slot bit-width**. Decode cost stays at 1-2 cycles for any single slot extract; the variables that change with width are:

| Slot width | Slots per uint64_t | Cohort to use |
|---|---|---|
| 1 bit | 64 | Use `bitmap-flag-api.md` (canonical 1-bit specialization) |
| 2 bits | 32 | This pattern (4-state fields like regime) |
| 3 bits | 21 (3 bits waste at boundary) | This pattern (8-state fields like halt_reason) |
| 4 bits | 16 | This pattern (16-state fields like portfolio slot indices) |
| 5-8 bits | 8-12 | Borderline; use uint8_t per slot directly unless cohort-packing saves cache lines |

**The decode cost stays constant** (`(byte >> shift) & mask` is 1 cycle regardless of mask width). What varies is **how many slots fit per cache line** — narrower slots = denser packing = more potential cache savings, at the cost of slightly more ALU work on the consumer side (which is free due to ILP).

**Rule:** when designing a new bitmap API for ANY bit-width, design with parallel decode in mind from the start. Write extracts as independent ops; ensure dispatch tables index by extracted value; provide `BATCH_*` / `ANY_*` predicates for cross-slot queries.

### Compiler reliance — verify hot paths once

GCC 13+ and Clang 17+ correctly emit single-instruction extracts for `(x >> S) & M` and recognize ILP opportunities for adjacent independent extracts. Older compilers may emit 2-3 instructions per extract.

**Discipline:**
- Write the source as independent extracts. Don't manually fuse — compiler does it better.
- For HOT path applications, **assembly-verify once** at first application (via godbolt or `g++ -S -masm=intel`). Confirm the compiler emits BMI2 PEXT or a fused AND+SHR for the cohort. Document the verified output in the application's commit message.
- For SLOW path applications, trust the compiler — measure end-to-end if perf-critical, but don't hand-optimize.
- If a compiler regression is observed (toolchain bump produces worse code), add an explicit BMI2 intrinsic fallback gated by `__BMI2__`.

This is the same "compile-time trust + verify-once at first application" discipline as `bitmap-flag-api.md`, and aligns with the AVX-512 byte-determinism discipline (CLAUDE.md item 25).

---

## Composition with X-macro registries

The pattern is orthogonal to but COMPOSES with X-macro registries. Two registries cleanly separate concerns:

| Registry | Concern | Output |
|---|---|---|
| `FOREACH_<STATE>_STATE(X)` | Define K states with bit values | Constants `<STATE>_<NAME>`, names array, count |
| `FOREACH_<MULTI-BIT-FIELD>(X)` | Define fields packed into a shared word + their bit positions | SHIFT + MASK constants per field, accessor macros |

Concrete shape:

```cpp
// Registry 1: regime state values
#define FOREACH_REGIME_STATE(X)         \
    X(RANGING,    0b00)                  \
    X(TRENDING,   0b01)                  \
    X(VOLATILE,   0b10)                  \
    X(MILD_TREND, 0b11)

// Registry 2: multi-bit field layout (which packed fields live in regime_field byte)
//   tuple: X(field_name, bit_count, shift)
#define FOREACH_REGIME_FIELD_SLOT(X)    \
    X(current,  2, 0)                    \
    X(proposed, 2, 2)
    // bits 4..7 reserved

#define X_GEN_FIELD_MASK(name, bits, shift) \
    constexpr uint8_t REGIME_##name##_MASK = (uint8_t)(((1u << (bits)) - 1) << (shift)); \
    constexpr uint8_t REGIME_##name##_SHIFT = (uint8_t)(shift);
FOREACH_REGIME_FIELD_SLOT(X_GEN_FIELD_MASK)
#undef X_GEN_FIELD_MASK
```

Adding a new state (e.g. RANGING_LOW_VOL = 0b100) → 1 row in `FOREACH_REGIME_STATE` + bump bit-width in `FOREACH_REGIME_FIELD_SLOT`.

Adding a new packed sub-field (e.g. a 1-bit "regime is high confidence" flag) → 1 row in `FOREACH_REGIME_FIELD_SLOT`.

---

## Worked example: full regime field migration

**Pre-migration (CoreContext.hpp):**
```cpp
struct CoreContext {
    int rs_current;        // 4 bytes
    int rs_proposed;       // 4 bytes
    int rs_count;          // 4 bytes (count for hysteresis — STAYS as int)
    int rs_threshold;      // 4 bytes (threshold — STAYS as int)
    int rs_last_strat;     // 4 bytes (last strategy mapped — STAYS as int)
    // ... 8 bytes saved per CoreContext × 16 cores = 128 bytes saved per EventLoopState
};
```

**Post-migration:**
```cpp
struct CoreContext {
    // Was: int rs_current + int rs_proposed = 8 bytes.
    // Now: 4 bits in shared byte (bits 0..1 = current, bits 2..3 = proposed).
    uint8_t regime_field;
    // 7 bytes savings here re-purposable for adjacent cold fields.
    int rs_count;
    int rs_threshold;
    int rs_last_strat;
};
```

**Consumer migration:**

Pre:
```cpp
switch (ctx.rs_current) {
    case REGIME_RANGING:    handle_ranging(ctx);    break;
    case REGIME_TRENDING:   handle_trending(ctx);   break;
    case REGIME_VOLATILE:   handle_volatile(ctx);   break;
    case REGIME_MILD_TREND: handle_mild_trend(ctx); break;
}
```

Post (branchless dispatch via function-pointer table):
```cpp
using regime_handler = void(*)(CoreContext&);
constexpr regime_handler REGIME_HANDLERS[4] = {
    handle_ranging, handle_trending, handle_volatile, handle_mild_trend
};
REGIME_HANDLERS[REGIME_CURRENT_GET(ctx.regime_field)](ctx);
// Single MOV + indirect call. Branchless dispatch. Modern CPUs predict
// the indirect call accurately when the regime is stable cycle-to-cycle.
```

Pre:
```cpp
if (rs_current == REGIME_TRENDING || rs_current == REGIME_VOLATILE) {
    reduce_position_size();
}
```

Post (set-membership in 1 instruction):
```cpp
if (REGIME_CURRENT_IS_RISKY(ctx.regime_field)) {
    reduce_position_size();
}
```

Pre:
```cpp
if (ctx.rs_current == ctx.rs_proposed) {
    commit_proposed();
}
```

Post (compare two slots from same byte — 2 shifts + cmp):
```cpp
if (REGIME_CURRENT_GET(ctx.regime_field) ==
    REGIME_PROPOSED_GET(ctx.regime_field)) {
    commit_proposed();
}
```

Or, even better via XOR (single instruction):
```cpp
// 4-bit XOR of regime_field with itself shifted by 2 bits.
// If current == proposed, low 2 bits of XOR are zero.
if ((ctx.regime_field ^ (ctx.regime_field >> 2)) & 0x3) == 0) {
    commit_proposed();
}
```

---

## When to use this pattern

✅ **K-state field with 2 ≤ K ≤ 16, stored within a single record.**
✅ Per-cycle dispatch on the field is common (slow path or hot path).
✅ Multi-state predicates (`state in {A, C, E}`) appear in consumer code — set-membership pattern wins.
✅ Multiple K-state fields in the same record (cache savings + shared word + intra-record compare).
✅ Lookup-table-driven processing (per-state value, per-state handler, per-state config).
✅ Hot-path branch-prediction-unfriendly state transitions (regime can change mid-session).

## When NOT to use this pattern

❌ **K > 16** (5+ bits) — diminishing returns; use full uint8_t / uint16_t directly.
❌ State value has **rich associated data** that can't fit a single lookup-table cell (the data is the actual cost; bit-packing the index saves nothing).
❌ State stored **across records** for cross-record scan that doesn't dominate per-record access (per CLAUDE.md item 20 — Portfolio.active_bitmap is the legal exception; most cases fail this).
❌ State mutated under **cross-thread CAS** with adjacent fields in the same word — bit mutation race-window-safe requires `__atomic_fetch_or` / `__atomic_fetch_and` patterns and careful happens-before reasoning; not worth the complexity for marginal memory savings.
❌ **K = 2** — use `bitmap-flag-api.md` (boolean specialization) directly.
❌ The K-state set is **highly volatile in design** (states added/removed every few weeks) — registry rewrites become friction. Wait for stability.

## Decision tree

```
Is the field K states with 2 ≤ K ≤ 16?
├─ No (K > 16): use uint8_t/uint16_t directly. Stop.
├─ No (K = 2): use bitmap-flag-api.md (boolean variant). Stop.
└─ Yes (2 ≤ K ≤ 16): continue.

Is the field stored within a single record (per-core, per-slot, etc.)?
├─ No (top-level cross-record): use only if cross-record scan dominates.
└─ Yes (per-record): continue.

Are there 2+ K-state fields in the same record that could share a word?
├─ Yes: pack them into a shared uint8_t/uint16_t. Strong win.
└─ No (just one K-state field): still worthwhile — saves 6 bits per record + enables branchless inference API. Modest win.

Is the field mutated cross-thread?
├─ Yes (CAS adjacent fields share the word): require `__atomic_*` discipline + design review.
└─ No (single-thread or release-acquire fence): proceed with regular MBS_* macros.
```

---

## Branchless inference cost-benefit

CLAUDE.md item 28 cost framework applied:

| Operation | Branchy cost (worst-case mispredict) | Branchless cost | Win condition |
|---|---|---|---|
| Read state (`int` field) | 4 bytes cache touch | 1 byte cache touch + 1-2 cycles (AND + SHR) | Always wins for hot path |
| Equality check | 1 cmp + 1 branch (3-5 ns if mispredict) | 1 cmp + 1 SETcc (no branch, 1 ns) | Wins when mispredict rate > 5% |
| Set membership (2-state subset) | 2 cmp + 2 OR + 1 branch (5-10 ns mispredict) | 1 SHR + 1 AND + 1 cmp (1 ns) | Always wins |
| Dispatch on K states | switch jump table (1 indirect branch, 5 ns mispredict) | 1 array deref + 1 indirect call (1 ns + 5 ns indirect call) | Wins when state changes per-cycle |
| Transition validation | K×K nested if-else chain (10-30 ns) | 1 SHR + 1 AND (1 ns) | Always wins |

For a slow-path body that processes 16 cores per cycle and computes a regime predicate per core (e.g., "is core c's current regime in {TRENDING, VOLATILE}?"), the branchless set-membership saves ~50-100 ns/cycle aggregate.

Hot-path applications (BG_Evaluate, SG_Evaluate) gain more — every cycle the dispatch happens, and the branch predictor's failure-mode cost compounds when state varies per tick.

---

## Caveats and footguns

1. **Bit-width overflow:** when adding a new state pushes the value past `(1 << bits)`, the packed slot silently truncates. **Mitigation:** `static_assert(STATE_COUNT <= (1 << SLOT_BITS), "increase slot width")` next to each registry.

2. **Field shift bugs:** writing the wrong shift constant for a slot corrupts adjacent slots. **Mitigation:** generate SHIFT + MASK pairs from a single X-macro registry; never hand-write the shifts.

3. **Set-mask bit positions:** SET_MASK indexes by state VALUE, not bit-position in the storage word. Confusing. **Mitigation:** name set-masks with `_SET_` infix (`REGIME_SET_RISKY`) and the regular masks with `_MASK_` suffix (`REGIME_CURRENT_MASK`) to prevent confusion.

4. **Compiler optimization fragility:** modern compilers (gcc 13+, clang 17+) emit single-instruction extracts for `(x & MASK) >> SHIFT`. Older toolchains may emit 2-3 instructions. **Mitigation:** assembly-verify HOT path one time after first application; the codebase requires a 2026-vintage compiler anyway (C++20 features).

5. **Debugging visibility:** GDB / objdump display the packed byte as a whole — operator reading a core dump must decode mentally. **Mitigation:** provide `REGIME_DEBUG_STR(field)` helper that pretty-prints all slots in the word.

6. **Snapshot / serialization compatibility:** if a packed field is written to a wire format, the wire format is now byte-encoded — single migration risk on state-value renumbering. **Mitigation:** treat the X-macro state values as wire-version-locked (renumbering bumps snapshot version).

---

## Implementation checklist (per application)

When introducing this pattern to a new K-state field:

- [ ] X-macro `FOREACH_<NAME>_STATE(X)` registry defines all state values
- [ ] X-macro `FOREACH_<NAME>_FIELD_SLOT(X)` (if multiple sub-fields share a word) defines slot layout
- [ ] Auto-generate VALUE constants from state registry
- [ ] Auto-generate MASK + SHIFT constants from slot registry
- [ ] Auto-generate state-NAME[] array for debug output
- [ ] `static_assert(STATE_COUNT <= (1 << SLOT_BITS))` overflow guard
- [ ] `MBS_GET / SET / EQ / IN_SET / SELECT_EQ` macros (or convenience aliases like `REGIME_CURRENT_GET`)
- [ ] All consumer sites migrated to branchless accessors (no remaining `field == VAL` or `switch (field)`)
- [ ] If the field is wire-format-bound: snapshot version bumped OR encoding is byte-preserved
- [ ] Compile-time check: `__has_builtin(__builtin_constant_p)` confirms the mask + shift constants fold at compile time
- [ ] Unit test confirms branchless inference yields the same results as the prior switch dispatch (parity gate)

---

## Candidate inventory (first applications)

Found in the FoxML_Trader_v2 codebase as of 2026-05-13:

1. **`rs_current` + `rs_proposed` on CoreContext** — 4 states each (REGIME_*) → 2 bits each. Pack into single uint8_t. Savings: 7 bytes per CoreContext × 16 cores = **112 bytes per EventLoopState**.

2. **`strategy_id` on CoreContext (+ per-core slow-state)** — 4-5 strategies, headroom for 8 → 3 bits. Currently uint8_t. Modest savings, but enables branchless multi-strategy dispatch in slow-path body.

3. **`OrderType` in Order<F>** — 4-8 types (BUY/SELL/LIMIT_*/CANCELED/...) → 3 bits. Currently uint8_t per Order. With Portfolio<uint16_t>'s 16 slots, packing the 16 OrderTypes saves at most 14 bytes; not worth the across-record cost per item 20 unless cross-order scan is dominant.

4. **`TradeEventType` on TradeEvent<F>** — 3 states (ENTRY/EXIT/COMBINED) → 2 bits. Currently uint8_t per event. Per-event compactness modest; not yet worth the migration cost unless TradeEvent is heavily memory-bound.

5. **`OrderState` on Order<F>** — SUBMITTED/PARTIAL_FILL/FILLED/REJECTED/CANCELED — ~5 states → 3 bits. Currently uint8_t per Order. Similar trade-off to (3).

6. **`halt_reason` on PerCoreSnap** — currently a small enum (HALT_*); pack with adjacent flags. Modest savings, fits the cohort-audit rule when adjacent slots also K-state.

**First-application recommendation:** start with (1) — regime fields in CoreContext. Highest savings + branchless dispatch wins are largest (regime is consulted every slow-path cycle by every core). After (1) field-validates the pattern, audit cohort (2-6) for follow-ups.

---

## Applied at

### First application: EVENT_LOG_MODE 2-bit slot (v5.15.5.C.3 Phase 3b)

- Registry: `MemHeaders/OmsStateFlagRegistry.hpp` — `EVENT_LOG_MODE` declared
  with `MULTI_BIT` storage class, 2-bit slot in shared `oms_state_flags` word
- Replaced: prior `int event_log_mode` field on `OrderManagerState` (per
  CLAUDE.md item 20 in-record bit-pack trade-off rule)
- Companions: `OMS_INIT_AUTOPOPULATE` + `OMS_RESET_AUTOPOPULATE` walk the
  registry; entries with KIND=MULTI_BIT dispatch through `MBS_SET_U16` with
  per-slot SHIFT + WIDTH constants generated by the registry walk
- Tests: `tests/controller_test.cpp` "v5.15.5.C.3 Phase 10" block validates
  MULTI_BIT slot bits don't bleed into adjacent BIT-kind flags
- Sister: `bitmap-flag-api.md` second-tier application section (same registry;
  first canonical HYBRID storage application)

### Second application: DriftOverride bit-packed flags (v5.15.5.F.4d)

- File: `CoreFrameworks/CfgFieldDriftOverride.hpp` (NEW at `.F.4d`)
- Struct: `DriftOverride` — 8 bytes (flags uint8_t + eps_idx uint8_t + explicit
  padding)
- Bits packed: has_override (1 bit) + severity (1 bit) + category (1 bit) +
  compare_kind (2 bits) = 5 bits used / 3 bits reserved
- Replaces: would-have-been `struct { uint8_t severity; uint8_t category;
  uint8_t compare_kind; uint8_t _pad; double custom_eps; }` (16 bytes) →
  `struct { uint8_t flags; uint8_t eps_idx; int16_t _padding1; int32_t _padding2; }`
  (8 bytes). 50% memory reduction; cache-line packs 8 entries per 64B line
  vs 4 entries previously.
- Branchless accessors: `drift_ovr_has` / `_severity` / `_category` /
  `_compare_kind` per `bitmap-flag-api.md` API style
- Sparse eps values via separate constexpr `g_drift_custom_eps[]` table
  (~5 unique values; index 1 byte into per-row struct)
- Pattern: applies bit-packing-for-state-fields discipline (DESIGN_PHILOSOPHY § 4
  STRONG bullet added 2026-05-14)

### Third application: RegistryRosterEntry bit-packed flags (v5.15.5.F.4d)

- File: `CoreFrameworks/RegistryRoster.hpp` (NEW at `.F.4d`)
- Struct: `RegistryRosterEntry` — 40 bytes total
- Bits packed: `flags` uint8_t = LEVEL (4 bits; 0-15) + WIRE_FORMAT_KIND
  (2 bits; NOT_WIRE/WIRE_FORMAT/TWO_SOURCE/MIXED) + reserved (2 bits)
- Replaces: would-have-been `uint8_t level; uint8_t wire_format_kind; uint8_t _pad[2];` =
  4 bytes → 1 byte packed flags
- Branchless accessors: `roster_level(flags)` / `roster_wire_format_kind(flags)`
- Bug_class column: 5 bits used / 3 bits reserved in `uint8_t bug_class`
  (Class N codes 0-31 fit; future growth to Class 32-255 fits in reserved)

### Fourth application: ManualFieldInventoryEntry bit-packed kind (v5.15.5.F.4d)

- File: `MANUAL_FIELDS_INVENTORY.md` (workspace DOCS; output of cfg field audit)
- Struct: per-entry encoding for non-cfg manual fields documented in inventory
- Bits packed: `kind` uint8_t = CATEGORY (3 bits; DERIVED/RUNTIME_STATE/PER_CORE_OVERRIDE/INTERNAL) + reserved (5 bits)

### Fifth application: Order::flags_packed bandit context bits (v5.15.5.F.4d Thread B)

- File: `CoreFrameworks/Order.hpp` `Order<F>::flags_packed` uint32_t field (canonical bit-pack carrier since `.F.4c.3` r-1)
- Struct: `Order<F>` (320B; bit-pack added at bits 17-25 of flags_packed; sister to existing `MASK_ORDER_PRE_RESOLVED` at bit 16)
- Bits packed: 9 bits across 3 sub-slots — `bandit_active_state` (3 bits; 5 states fit) + `bandit_regime` (3 bits; NUM_REGIMES=5 fits) + `bandit_chosen_arm` (3 bits; ENSEMBLE_HORIZON_MAX=8 fits)
- Accessors: `MBS_OrderBanditActiveState(o)` / `MBS_OrderBanditRegime(o)` / `MBS_OrderBanditChosenArm(o)` / `MBS_OrderSetBanditContext(o, state, regime, arm)` per H14 manual-bit-packing-discipline
- Set at: `Order_BindPreResolved` sister helper (decision-time binding per `decision-time-data-binding-pattern.md` Pattern 4 carrier variant — bits flow with Order through lifecycle to calib emit time)
- Read at: calib log emission (`real_on_exit_calibration` body in `OrderManager.hpp:651`) for diagnostic columns (bandit_algorithm + regime_id_at_emit + chosen_arm singletons per `.F.4d` § N.1 + § M)
- Cluster placement: existing `flags_packed` field is in HOT cluster (read at every fill); 9 new bits piggyback on existing alignment + cache-line residency — zero new allocation, zero cache impact
- 5 free bits remain at bits 26-31 of flags_packed for future Order metadata

### 4-application threshold → INVARIANT promotion (now 5 applications at `.F.4d`)

Per `pattern-codification-lifecycle.md` Stage 5 criteria (≥2 applications OR
DESIGN_SPEC + ≥1 application AND pattern is broad → CLAUDE.md item promotion):
the pattern has **5 canonical applications** across DIFFERENT domains (OMS state
encoding + sidecar drift override + registry roster + manual fields
inventory + Order::flags_packed bandit context bits 17-25). Promoted to INVARIANT STATUS at `.F.4d` ship. Same status as
sliding-window-online-statistics-pattern (CLAUDE.md item 29).

---

## Cross-references to CLAUDE.md

**CLAUDE.md item 30** (codified v5.15.5.F.3; promoted to INVARIANT at v5.15.5.F.4d):
> **30. Multi-bit state encoding via N-bit packed slots — INVARIANT.** K-state field (K=2..16) within a record stores in `ceil(log2(K))` bits. Branchless inference API (MBS_GET / EQ / IN_SET / SELECT_EQ / dispatch table). See `DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md` + sister `bitmap-flag-api.md` (1-bit specialization). **5 canonical applications** at `.F.4d` ship close: EVENT_LOG_MODE (v5.15.5.C.3) + DriftOverride + RegistryRosterEntry + ManualFieldInventoryEntry (Thread A canonicals 2-4 at `.F.4d`) + Order::flags_packed bandit context bits 17-25 (Thread B 5th canonical at `.F.4d`; sister to existing MASK_ORDER_PRE_RESOLVED at bit 16).

**Future application candidates** (cfg field audit at `.F.4d` may surface more):
- `RegimeClassification` in CoreContext (4 states; 2 bits)
- `strategy_id` in per-core slow-state (5-8 strategies; 3 bits)
- `OrderType` in Order<F> (4-8 types; 3 bits)
- `TradeEventType` on TradeEvent<F> (3 states; 2 bits)
- `OrderState` on Order<F> (5 states; 3 bits)
- `halt_reason` on PerCoreSnap (4-8 reasons; 3 bits)

Per `/dod-audit` Stage 6 detection signature added 2026-05-14: any new struct
with ≥2 adjacent `uint8_t state_<N>` fields where each represents an enum
≤4 values → flagged as bit-packing candidate.

---

**End of spec.**
