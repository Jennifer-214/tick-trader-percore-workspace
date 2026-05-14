# Bitmap overflow protection discipline — compile-time guard for registry-paired bitmaps

**Established:** 2026-05-14 (v5.15.5.F.4 sprint)
**Status:** DRAFT v1.0 (pre-coding spec; promotes to ACTIVE after `.F.4h` audit pass closes the missing-guard inventory)
**Cross-references:**
- Parent: `bitmap-flag-api.md` (CLAUDE.md item 20 — bitmap accessor primitives; this spec adds the overflow guard discipline)
- Parent: `registry-bitmap-set-discipline.md` (CLAUDE.md item 30 — the SET-discipline sister; both surfaces apply to registry-paired bitmaps)
- Sister: `categorical-tag-applicability-pattern.md` (categorical mask enums require the same overflow guards)
- Sister: `x-macro-registry-with-presence-dispatch.md` (registries that emit into bitmaps are the primary risk surface)
- Composes with: `multi-bit-state-encoding-pattern.md` (when bitmap overflows, multi-bit pack is sometimes the better alternative)
- FoxML_Trader_v2 `CLAUDE.md` items 13 (X-macro registry), 19 (structural fix preferred), 20 (BITMAP_*), 30 (registry-bitmap SET discipline)

---

## Problem statement

The engine has 30+ `FOREACH_<X>` registries; many are paired with a bitmap field of fixed width (`uint8_t` / `uint16_t` / `uint32_t` / `uint64_t`) where each registry entry occupies one bit.

```cpp
// Typical pattern: registry + bitmap pair
#define FOREACH_ML_CFG_FLAG(X) \
    X(BANDIT_ENABLED,          ...) \
    X(RIDGE_WITHIN_HORIZON,    ...) \
    X(RIDGE_ACROSS_HORIZONS,   ...) \
    /* ... 10 more entries today; how many tomorrow? ... */

struct Cfg {
    uint16_t ml_cfg_flags;  // 16 bits = 16 max entries
    // ...
};
```

**Risk:** when registry entry count exceeds bitmap type width, behavior is **silently incorrect**:

```cpp
enum MlCfgFlag : uint16_t {
    MASK_BANDIT_ENABLED        = 1 << 0,   // bit 0
    MASK_RIDGE_WITHIN_HORIZON  = 1 << 1,   // bit 1
    /* ... 14 more bits 2-15 ... */
    MASK_FUTURE_BIT_16         = 1 << 16,  // SILENTLY TRUNCATES TO 0 on uint16_t
};
```

The shift `1 << 16` exceeds `uint16_t`'s width; result is implementation-defined (typically 0, but undefined behavior on signed types). The flag silently becomes a no-op: `BITMAP_IS_SET(flags, MASK_FUTURE_BIT_16)` always returns false; `BITMAP_SET(flags, MASK_FUTURE_BIT_16)` is a no-op.

This is the **silent-truncation bug class** — code compiles, runs, doesn't crash, but the bit it claims to test doesn't exist. Behavior diverges from operator intent without any observable error.

**Why this isn't caught today:**
- The compiler may emit a warning for `1 << 16` on a `uint16_t` IF the shift is within an explicit `uint16_t` context, but enum value definitions are usually `int` typed → the shift produces an `int` → assigned to the enum → silent narrowing
- No runtime check (the bit doesn't exist; nothing to detect)
- Tests using BITMAP_IS_SET pass trivially because the bit is always 0
- Code review may miss it during incremental bit additions ("we're at bit 14; one more is fine" → "we're at bit 16; one more is fine" — slow drift)

**Structural fix:** compile-time `static_assert` that ties the registry's entry count to the bitmap's type width. Adding an entry that overflows fails the assert; CI blocks the commit. **The bug class becomes structurally impossible.**

---

## The pattern (concrete shape)

### Step 1: Count macro for FOREACH walk

Every FOREACH registry gets a compile-time entry count:

```cpp
// In the registry header, AFTER FOREACH_X is defined:

#define FOREACH_X_COUNT_ENTRY(...) +1
constexpr size_t FOREACH_X_COUNT_VALUE = 0 FOREACH_X(FOREACH_X_COUNT_ENTRY);
#undef FOREACH_X_COUNT_ENTRY
```

The X-macro expands `FOREACH_X(FOREACH_X_COUNT_ENTRY)` to `+1 +1 +1 ...` (one per row). Prefixed by `0`, the expression evaluates to the entry count at compile time. Zero runtime cost.

### Step 2: Static_assert paired with the bitmap field

```cpp
// In the same header (or wherever the bitmap field is declared):

static_assert(FOREACH_X_COUNT_VALUE <= sizeof(X_flags_type) * 8,
              "FOREACH_X (" __FILE__ ") overflowed bitmap type X_flags_type. "
              "Upgrade type width OR split into multiple bitmaps "
              "OR use multi-bit state encoding (item 30). "
              "See bitmap-overflow-protection-discipline.md for type-upgrade decision tree.");
```

Compile fails if entry count exceeds bitmap width. The error message points to the remediation spec.

### Step 3: Co-locate the assert with the FOREACH declaration

Put the `static_assert` in the SAME HEADER as `FOREACH_X`, immediately after the macro definition. Why:

1. **Visible at the source.** Reader sees the constraint next to the registry.
2. **Triggers at the right time.** Adding a row in FOREACH_X recompiles the header; assert fails immediately.
3. **No drift between registry header and consumer.** If the bitmap field is in a separate header, the assert can be in EITHER but ideally in the registry header (the assert references the bitmap type, which the registry header needs to know anyway).

### Step 4: Document the bitmap type relationship

Above the static_assert, comment the design intent:

```cpp
// Bitmap pair: FOREACH_X registry ↔ <consumer>::x_flags (<type>)
// Overflow guard: prevents silent truncation when registry grows beyond <type>'s bit width.
// Type-upgrade ladder: uint8_t → uint16_t → uint32_t → uint64_t → split or multi-bit pack.
static_assert(FOREACH_X_COUNT_VALUE <= sizeof(x_flags_type) * 8, "...");
```

---

## Type-upgrade decision tree

When `static_assert` fails (bitmap full), the decision tree:

```
Current entries vs current bitmap type:

8-bit (uint8_t)
  ↓ 9th entry needed
  → Upgrade to uint16_t (rare cost; 1 extra byte per instance)

16-bit (uint16_t)
  ↓ 17th entry needed
  → Upgrade to uint32_t (2 extra bytes per instance; usually trivial)

32-bit (uint32_t)
  ↓ 33rd entry needed
  → Upgrade to uint64_t (4 extra bytes per instance; check cache budget for hot-path structs)

64-bit (uint64_t)
  ↓ 65th entry needed
  → STOP and reconsider the design:
     (a) Split into 2 bitmaps along domain boundary (e.g., FOREACH_X_PRIMARY + FOREACH_X_SECONDARY)
     (b) Use multi-bit state encoding (item 30) if entries are MUTUALLY EXCLUSIVE states
         rather than independent flags
     (c) Refactor: are some "flags" actually static (boot-only)? Remove them from the runtime bitmap
```

### When to upgrade vs split

| Scenario | Choice |
|---|---|
| Entries are independent flags (any combination valid) + width <64 | Upgrade type width |
| Entries are mutually exclusive states + ≤K options | Multi-bit state encoding (per item 30); save bits |
| Entries split naturally into 2+ orthogonal axes | Split into separate bitmaps (e.g., per-domain) |
| Entries include boot-only flags that never change at runtime | Remove from runtime bitmap; promote to compile-time constants or boot-once struct |
| Entries exceed 64 and don't decompose | Two `uint64_t` bitmaps; consumers check both; cache impact analyzed |

### Cache-line impact of upgrades

For hot-path structs where the bitmap shares a cache line with other hot fields:

| Type | Size | Cache-line impact |
|---|---|---|
| uint8_t | 1 B | minimal |
| uint16_t | 2 B | minimal |
| uint32_t | 4 B | usually fine |
| uint64_t | 8 B | check struct layout; may push next field to new cache line |
| Multi-bitmap (2× uint64_t) | 16 B | likely pushes next field to new cache line; verify with `pahole` |

For slow-path structs (cfg, descriptors, GUI-only state), cache impact is hygiene-level not critical (per `latency-vs-cache-decision-framework.md` cost analysis). Free to upgrade.

---

## Audit script: `/dod-audit` extension

Detection signature (Python-ish pseudocode):

```python
def audit_bitmap_overflow_protection(repo_root):
    findings = []
    
    # 1. Find all FOREACH_<X> macros + their headers
    foreach_macros = grep_recursive(r'^#define FOREACH_(\w+)\s*\(X\)', repo_root)
    
    for macro_name, header_path in foreach_macros:
        # 2. Find the count constant in the same header
        count_pattern = rf'FOREACH_{macro_name}_COUNT_VALUE'
        has_count = grep_file(header_path, count_pattern)
        
        # 3. Find the static_assert pairing count to bitmap type
        assert_pattern = rf'static_assert\(FOREACH_{macro_name}_COUNT_VALUE\s*<=\s*sizeof\('
        has_assert = grep_file(header_path, assert_pattern)
        
        # 4. Find consumer bitmap fields (heuristic: <macro_name_lower>_flags or X_flags)
        bitmap_field_candidates = grep_recursive(
            rf'(uint8|uint16|uint32|uint64)_t\s+{macro_name.lower()}_flags',
            repo_root)
        
        # 5. Verdict
        if not has_count:
            findings.append((macro_name, "MISSING — no _COUNT_VALUE compile-time constant"))
        if not has_assert and bitmap_field_candidates:
            findings.append((macro_name, f"MISSING_OVERFLOW_GUARD — bitmap fields found: {bitmap_field_candidates}"))
        if not bitmap_field_candidates:
            findings.append((macro_name, "NOTE — no obvious bitmap pair found; verify manually"))
    
    return findings
```

Heuristics to improve:
- Some bitmaps use non-obvious names (e.g., `failure_flags` paired with `FOREACH_FAILURE_MODE`). The audit script should support a known-mapping table for non-derivable pairings.
- Some bitmaps are local to functions (transient state). These typically don't grow over time; lower priority.

**Audit run frequency:** at every `.F.X` sprint's `/dod-audit` pass; specifically required at `.F.4h` to close the missing-guard inventory for v5.15.5.F.4.

---

## Reference implementations

### v5.14.8.B FOREACH_FAILURE_MODE (good example)

```cpp
// MemHeaders/FailureModeRegistry.hpp (illustrative; verify exact form)

#define FOREACH_FAILURE_MODE(X) \
    X(MODEL_LOAD_FAILED,       BIT_FLAG, "Model load failed") \
    X(SCALER_HASH_MISMATCH,    BIT_FLAG, "Scaler hash mismatch") \
    /* ... */

#define COUNT_FAILURE_BIT_FLAG(name, kind, doc) +(kind == BIT_FLAG ? 1 : 0)
constexpr size_t FOREACH_FAILURE_MODE_BIT_COUNT = 0 FOREACH_FAILURE_MODE(COUNT_FAILURE_BIT_FLAG);
#undef COUNT_FAILURE_BIT_FLAG

static_assert(FOREACH_FAILURE_MODE_BIT_COUNT <= sizeof(uint16_t) * 8,
              "FOREACH_FAILURE_MODE bit-flag count overflowed uint16_t failure_flags");
```

Note: the count macro filters by `kind == BIT_FLAG` because the registry has mixed storage classes (BIT_FLAG / COUNTER_U32 / PERCENT_U8 per `bitmap-flag-api.md` storage-class extension). Only BIT_FLAG entries occupy the bitmap.

### v5.15.5.F.4 categorical-tag enums (pre-coding spec)

```cpp
// Strategies/StrategyCategories.hpp (planned for .F.4h)

enum StrategyCategory : uint32_t {
    STRAT_CAT_STATIC_RULES         = 1u << 0,
    // ... 12 more bits ...
    STRAT_CAT_USES_FLOW_DATA       = 1u << 12,
};

static_assert(STRAT_CAT_USES_FLOW_DATA < (1ull << 32),
              "StrategyCategory bitmap overflowed uint32_t — upgrade to uint64_t "
              "OR split orthogonal axes into separate enums");
```

Note: for category enums, the assert is on the HIGHEST DECLARED BIT VALUE, not on a FOREACH count (categories aren't always FOREACH-driven). Same overflow class; slightly different assert form.

### Inventory: bitmap pairs currently in the codebase (subject to `.F.4h` audit)

| FOREACH registry | Bitmap field (heuristic) | Type | Bits used (estimate) | Headroom | Action |
|---|---|---|---|---|---|
| FOREACH_ML_CFG_FLAG | `ml_cfg_flags` | uint16_t | ~10 | ~6 | upgrade to uint32_t before next ship |
| FOREACH_GATE_CFG_FLAG | `gate_cfg_flags` | uint8_t | ? | ? | audit |
| FOREACH_LIFECYCLE_CFG_FLAG | `lifecycle_cfg_flags` | uint8_t | ? | ? | audit |
| FOREACH_OPS_CFG_FLAG | `ops_cfg_flags` | uint8_t | ? | ? | audit |
| FOREACH_RISK_CFG_FLAG | `risk_cfg_flags` | uint8_t | ? | ? | audit |
| FOREACH_FAILURE_MODE | `failure_flags` | uint16_t | ? (BIT_FLAGs only) | ? | audit; possibly already protected |
| FOREACH_CORE_STATE_FLAG | `core_state_flags` | ? | ? | ? | audit |
| FOREACH_PER_CORE_STATE_FLAG | `per_core_state_flags` | ? | ? | ? | audit |
| FOREACH_OMS_STATE_FLAG | `oms_state_flags` | ? | ? | ? | audit |
| FOREACH_EZOO_INIT_FLAG | `ezoo_init_flags` | ? | ? | ? | audit |
| FOREACH_CFG_DRIFT_CHECK | `drift_flags_at_load` | ? | ? | ? | audit |

`.F.4h` Step N: populate the `?` cells via grep + add missing static_asserts; emit type upgrades where headroom is <3.

---

## Anti-patterns to avoid

### Anti-pattern 1: Bitmap field declared without paired overflow guard

```cpp
// BAD — no static_assert co-located
struct State {
    uint16_t status_flags;  // paired with FOREACH_STATUS_FLAG; no overflow guard
};
```

```cpp
// GOOD
struct State {
    uint16_t status_flags;
};
static_assert(FOREACH_STATUS_FLAG_COUNT_VALUE <= sizeof(uint16_t) * 8,
              "FOREACH_STATUS_FLAG overflowed status_flags type");
```

### Anti-pattern 2: Static_assert in wrong location

```cpp
// BAD — assert lives in consumer header, far from FOREACH definition
// FOREACH_X is in RegistryHeader.hpp; static_assert is in ConsumerCode.cpp
// → adding a row in RegistryHeader.hpp doesn't recompile ConsumerCode.cpp
// → assert fires at unrelated build steps, not immediately
```

```cpp
// GOOD — assert co-located with FOREACH_X declaration
// Adding a row triggers immediate re-eval of the count + assert
```

### Anti-pattern 3: Hard-coded magic-number bit position

```cpp
// BAD — bit position hardcoded; doesn't track registry count
#define MASK_NEW_FLAG (1 << 7)  // "we have room — bit 7 is free"
// Adding 9th flag: developer counts manually; may miscount; no compile-time check
```

```cpp
// GOOD — enum bit position derived from registry order; checked by static_assert
enum StatusFlag : uint16_t {
    #define X_GEN_BIT(name, ...) MASK_##name = 1u << (FOREACH_STATUS_FLAG_INDEX_##name),
    FOREACH_STATUS_FLAG(X_GEN_BIT)
    #undef X_GEN_BIT
};
```

(Or simpler: assign bits sequentially via FOREACH expansion; index = position in the registry.)

### Anti-pattern 4: Silently widening bitmap type without ensuring all consumers updated

```cpp
// BAD — upgrade type in producer struct; forget to update consumer's local copy
struct State { uint32_t flags; };  // upgraded from uint16_t
// Consumer code STILL has:
uint16_t local_flags = state.flags;  // silently truncates to 16 bits
```

```cpp
// GOOD — grep for all uses + update; consider `using StatusFlagsType = uint32_t;` alias
using StatusFlagsType = uint32_t;
struct State { StatusFlagsType flags; };
// Consumers reference the alias; type changes propagate.
```

Code review or `/dod-audit` should grep for raw uintN_t flag-typed variables paired with the registry.

### Anti-pattern 5: Overflow detection deferred to runtime

```cpp
// BAD — runtime check
if (flag_index >= 16) abort();  // catches at runtime; build still ships

// GOOD — compile-time check
static_assert(FOREACH_X_COUNT_VALUE <= 16, "...");  // build fails; no bad binary
```

### Anti-pattern 6: Mixed-purpose bitmap (independent flags + multi-bit state)

```cpp
// BAD — same bitmap holds 5 independent flags + a 3-bit state value
uint16_t mixed_state;  // bits 0-4 = flags; bits 5-7 = state; bits 8-15 = future
```

```cpp
// GOOD — separate concerns
uint8_t flags;          // independent flags
uint8_t state_packed;   // multi-bit state per item 30 (multi-bit-state-encoding-pattern.md)
```

Mixing complicates the overflow analysis (which bits are "free"?). Separating makes both bitmaps easier to grow + audit.

### Anti-pattern 7: Treating registry count as a static documentation comment

```cpp
// BAD — comment says "16 flags" but no compile-time enforcement
// 16 flags currently
struct State { uint16_t flags; };
```

```cpp
// GOOD — static_assert IS the documentation; can't drift
struct State { uint16_t flags; };
static_assert(FOREACH_X_COUNT_VALUE <= 16, "X has more entries than flags has bits");
```

---

## Trade-offs + when to apply

### Apply when:
- Bitmap field is paired with a FOREACH_X registry that may grow
- Bitmap field is used across multiple call sites (drift risk)
- Registry has 5+ entries (small registries are easier to audit manually but still benefit from the guard)
- ANY bitmap field that grows over time

### Skip when:
- Bitmap field is hardcoded constants only (no FOREACH growth path); just verify type width covers needs at declaration
- Truly transient bitmap used in a single function; not stored anywhere

### Cost:
- ~5 LOC per registry (count macro + static_assert + comment)
- One-time audit pass to retrofit existing registries (`.F.4h`)
- No runtime cost

### Win:
- Silent-truncation bug class structurally extinct
- Type-upgrade decisions surface at the right time (compile failure when adding the overflow-causing entry)
- Code review burden reduced (compiler catches the case, not human reviewers)

---

## CLAUDE.md promotion candidate

After `.F.4h` audit pass retrofits the existing bitmap inventory (10+ pairs above) with the static_assert pattern, this discipline is canonicalized in 10+ places. Promotion candidate to `CLAUDE.md` after v5.15.5.F.4 ships:

- New CLAUDE.md item (numbered after item 30): "Bitmap fields paired with growth-prone registries MUST have a co-located `static_assert(COUNT <= sizeof(TYPE) * 8)` overflow guard. Adding the next entry that would overflow fails the build."

---

## Cross-references

- `bitmap-flag-api.md` — bitmap accessor primitives (CLAUDE.md item 20); this spec adds the overflow guard discipline
- `registry-bitmap-set-discipline.md` — sister SET-discipline (CLAUDE.md item 30); both surfaces apply to registry-paired bitmaps
- `categorical-tag-applicability-pattern.md` — categorical mask enums use this same overflow guard pattern
- `x-macro-registry-with-presence-dispatch.md` — registries that emit into bitmaps are the primary risk surface
- `multi-bit-state-encoding-pattern.md` — alternative when entries are mutually exclusive states (item 30)
- `cache-layout-discipline-for-hot-side-structs.md` — type-upgrade impact on hot-path struct cache budgets
- `latency-vs-cache-decision-framework.md` — when bitmap type-upgrade is hygiene vs critical performance
- FoxML_Trader_v2 `CLAUDE.md` items 13, 19, 20, 30
- FoxML_Trader_v2 `DOCS/RECURRING_BUG_PATTERNS.md` — silent-truncation bug class entry (to be added)
