# Per-bit per-core override pattern (branchless bit-select on bitmap fields)

**Established:** 2026-05-10 (v5.14.9.F.6 — `PER_CORE_OVERRIDE_BITMAP_DOMAINS`)
**Status:** ACTIVE
**Cross-references:**
- Parent: `bitmap-flag-api.md` (the bitmap field being overridden)
- Sister: `heterogeneous-registry-pattern.md` (DOMAIN SPLIT — overrides per-domain)
- First application: `CoreFrameworks/ControllerConfig.hpp:211-216` (`PER_CORE_OVERRIDE_BITMAP_DOMAINS`)
- Resolve site: `CoreFrameworks/ControllerConfig.hpp:1194-1202` (branchless bit-select)
- CLAUDE.md item 4 (per-core data plane) + item 12 (display↔execution invariant)

---

## Problem statement

Per-core overrides for individual cfg fields (FPN, int) work via "is-set" sentinels:

```cpp
// One field per override:
struct PerCoreOverrides {
    FPN<F> risk_pct;          // value; 0 = inherit
    uint32_t poll_interval;   // value; 0 = inherit
    // ...
};
```

Each override is ~8-16 bytes; resolution at boot:

```cpp
resolved.risk_pct = (ov.risk_pct != 0) ? ov.risk_pct : global.risk_pct;
```

**When cfg-flags migrated to bitmaps (v5.14.9.F-.F.3), per-core override needed to extend:**

- 5 bitmap domains: LIFECYCLE / GATE / ML / RISK / OPS
- Total 21 cfg-flag bits across 6 bytes of bitmap storage
- Naïve approach: 21 × per-bit cfg fields (`core_N_partial_exit_enabled`, `core_N_kill_switch_enabled`, etc.) × N cores = 336 cfg fields for 16 cores
- Cost: 336 cfg.example entries + 336 parser branches + 336 GUI fields + 336 stamp-binding entries

**The cfg-surface explosion is unsustainable.** What we want:
- Per-core override capability for ANY bit in ANY domain
- Single cfg-key pattern per domain (not per-bit)
- Branchless resolution at boot
- Compatible with `PER_CORE_OVERRIDE_BITMAP_DOMAINS` auto-flow (`bitmap-flag-api.md` companion)

---

## Design space explored

### Option A: One cfg field per override bit (rejected)

`core_N_partial_exit_enabled`, `core_N_kill_switch_enabled`, etc.

**Rejected** — 21 bits × 16 cores = 336 cfg fields. Doesn't scale; parser overhead; engine.cfg.example bloat.

### Option B: Per-core full bitmap, all-or-nothing override

```cpp
struct PerCoreOverrides {
    uint8_t lifecycle_cfg_flags;  // if non-zero, COMPLETELY overrides global
};
```

**Rejected** — operator can't override SOME bits in a domain while inheriting others. If operator wants `core_0_kill_switch_enabled=1` but inherit `vol_sizing_enabled` from global, they can't. Wrong abstraction.

### Option C: Per-bit override via single "is-overridden" mask + value bitmap (chosen)

Two bitmap fields per domain:
- `<domain>_cfg_flags_override` — the override VALUES for bits that are overridden
- `<domain>_cfg_flags_override_set` — MASK of which bits are overridden (others inherit)

```cpp
struct PerCoreOverrides {
    uint8_t lifecycle_cfg_flags_override;        // override values
    uint8_t lifecycle_cfg_flags_override_set;    // which bits are overridden
    // ...same for gate, ml, risk, ops
};
```

Resolution: branchless bit-select.

```cpp
resolved = (override_set & override_values) | (~override_set & global_values)
```

For each bit:
- If override_set bit is 1: result = override_values bit (force override)
- If override_set bit is 0: result = global_values bit (inherit)

Adding domain N+1: 1 row in `PER_CORE_OVERRIDE_BITMAP_DOMAINS` registry → ALL touch sites auto-flow.

---

## The pattern (concrete shape)

### Registry: PER_CORE_OVERRIDE_BITMAP_DOMAINS

```cpp
// Tuple: X(domain_lower, DOMAIN_UPPER, storage_type, FOREACH_macro)
//   domain_lower  — lowercase name; used for field names (lifecycle_cfg_flags_override)
//   DOMAIN_UPPER  — uppercase name; used for MASK constants (MASK_LIFECYCLE_CFG_*)
//   storage_type  — uint8_t / uint16_t — matches the global ControllerConfig field
//   FOREACH_macro — the registry that defines the flag bits (for documentation / audit)

#define PER_CORE_OVERRIDE_BITMAP_DOMAINS(X)                                              \
    X(lifecycle, LIFECYCLE, uint8_t,  FOREACH_LIFECYCLE_CFG_FLAG)                        \
    X(gate,      GATE,      uint8_t,  FOREACH_GATE_CFG_FLAG)                             \
    X(ml,        ML,        uint16_t, FOREACH_ML_CFG_FLAG)                               \
    X(risk,      RISK,      uint8_t,  FOREACH_RISK_CFG_FLAG)                             \
    X(ops,       OPS,       uint8_t,  FOREACH_OPS_CFG_FLAG)
```

### Field declaration on PerCoreOverrides

```cpp
template <unsigned F> struct PerCoreOverrides {
    // ... FPN + int overrides ...

    // v5.14.9.F.6: BITMAP-typed overrides
    #define _DECL_OV_BITMAP_FIELDS(d_lower, D_UPPER, stype, FOREACH_macro) \
        stype d_lower##_cfg_flags_override;     \
        stype d_lower##_cfg_flags_override_set;
    PER_CORE_OVERRIDE_BITMAP_DOMAINS(_DECL_OV_BITMAP_FIELDS)
    #undef _DECL_OV_BITMAP_FIELDS
};
```

Expansion produces 10 fields per core (5 domains × 2 fields each). Storage: 5 × 2 × ~1-2 bytes ≈ ~12-20 bytes per core's PerCoreOverrides.

### Zero-init walk

```cpp
#define _ZERO_OV_BITMAP_FIELDS(d_lower, D_UPPER, stype, FOREACH_macro) \
    ov.d_lower##_cfg_flags_override = 0;       \
    ov.d_lower##_cfg_flags_override_set = 0;
PER_CORE_OVERRIDE_BITMAP_DOMAINS(_ZERO_OV_BITMAP_FIELDS)
#undef _ZERO_OV_BITMAP_FIELDS
```

### Resolution walk (branchless bit-select)

```cpp
// In ControllerConfig_ResolveForCore:
#define _RESOLVE_OV_BITMAP_FIELDS(d_lower, D_UPPER, stype, FOREACH_macro) \
    {                                                                          \
        stype _ov_set = ov.d_lower##_cfg_flags_override_set;                   \
        stype _ov_val = ov.d_lower##_cfg_flags_override;                       \
        stype _global = global.d_lower##_cfg_flags;                            \
        resolved.d_lower##_cfg_flags = (stype)((_ov_set & _ov_val) | ((stype)~_ov_set & _global)); \
    }
PER_CORE_OVERRIDE_BITMAP_DOMAINS(_RESOLVE_OV_BITMAP_FIELDS)
#undef _RESOLVE_OV_BITMAP_FIELDS
```

Per domain: 3 loads (ov_set, ov_val, global) + 2 ANDs + 1 OR + 1 NOT + 1 store = ~5-7 instructions, all branchless.

Total across 5 domains: ~30 instructions. Boot-time only (cfg resolution happens once at engine init); not hot-path.

### Parser walk

```cpp
// engine.cfg key format: core_N_<domain>_cfg_flags_override = MASK_VALUE
// engine.cfg key format: core_N_<domain>_cfg_flags_override_set = MASK_VALUE
//
// Or per-bit shorthand: core_N_<flag_name> = 0/1
// (parser converts shorthand → set+value pair internally)

#define _PARSE_OV_BITMAP_DOMAIN(d_lower, D_UPPER, stype, FOREACH_macro) \
    /* ... per-domain parser code that walks FOREACH_macro for per-bit shorthand,
       OR accepts whole-domain mask via the override + override_set keys ... */
PER_CORE_OVERRIDE_BITMAP_DOMAINS(_PARSE_OV_BITMAP_DOMAIN)
#undef _PARSE_OV_BITMAP_DOMAIN
```

The parser body inside `_PARSE_OV_BITMAP_DOMAIN` handles both forms (whole-mask + per-bit shorthand); operators write `core_0_kill_switch_enabled=1` and the parser sets the right bit in both `risk_cfg_flags_override_set` AND `risk_cfg_flags_override`.

### Adding a new domain

1. Add a row to `PER_CORE_OVERRIDE_BITMAP_DOMAINS`:
   ```cpp
   X(maker, MAKER, uint8_t, FOREACH_MAKER_CFG_FLAG)
   ```

2. Build. All 4 walks (DECL / ZERO / RESOLVE / PARSE) auto-extend. No manual touch sites.

That's it. The 5-row registry today (LIFECYCLE / GATE / ML / RISK / OPS) becomes 6 rows when MAKER lands.

---

## Branchless bit-select breakdown

The resolution formula:

```cpp
resolved = (override_set & override_values) | (~override_set & global_values)
```

For each bit position:

| override_set bit | override_values bit | global_values bit | Result |
|---|---|---|---|
| 0 (inherit) | * | 0 | 0 (inherits 0) |
| 0 (inherit) | * | 1 | 1 (inherits 1) |
| 1 (override) | 0 | * | 0 (forced 0) |
| 1 (override) | 1 | * | 1 (forced 1) |

Branchless: no `if`, no branch. Compiles to AND + NOT + AND + OR (4 instructions). For uint16_t (ML domain), same instructions; for uint8_t domains, same instructions.

**Why this beats per-bit branches:**

- Per-bit branches: `for each bit: if (override_set & bit) resolved |= (override_values & bit); else resolved |= (global & bit);` — N branches, N OR-stores per domain.
- Branchless: 4 instructions per domain, regardless of bit count. Constant-time + cache-friendly.

For 5 domains × 21 bits = 105 conceptual "decisions", reduced to 5 × 4 = 20 instructions. ~5x speedup at boot.

---

## Trade-offs + when to apply

### Apply when:
- Bitmap field already exists (or is being introduced) for the cfg-flag domain
- Per-core override capability is required
- ≥2 bits in the domain (single-bit domain doesn't justify the doubled storage)
- Bit-level override granularity matters (operator wants to override SOME bits, inherit others)

### Skip when:
- Single-bit domain (use simple `is_overridden` sentinel + value)
- All-or-nothing override semantics (use Option B; cheaper)
- No per-core override capability needed (skip the entire pattern)

### Cost:
- Storage: 2 bytes per uint8_t domain × N cores. For 5 domains × 16 cores = ~150 bytes for the override fields.
- Resolution cost: ~30 instructions per core at boot. Negligible.
- Code: ~30 LOC for the registry + 4 walks (DECL / ZERO / RESOLVE / PARSE).

### Win:
- Adding a new domain: 1 row in `PER_CORE_OVERRIDE_BITMAP_DOMAINS`. All 4 walks auto-extend.
- Bit-level override granularity (any bit, any core).
- Branchless resolution (4 instructions per domain regardless of bit count).
- Compatible with all existing cfg-flag patterns (BITMAP_IS_SET reads transparent to override resolution).

---

## Reference implementations

### v5.14.9.F.6 — first 5-domain registry

5 domains × 2 fields per domain × N cores = 10 fields per core's PerCoreOverrides struct.

Resolution at `CoreFrameworks/ControllerConfig.hpp:1194-1202`. Boot-time only; ~30 instructions per core.

### Future domain candidates

- MAKER domain (when v5.X maker-orders flags land)
- DEBUG domain (if a debugging cfg surface grows)

Pattern handles new domains uniformly — no design re-derivation needed.

---

## Lessons / gotchas

### `~override_set` cast preservation

```cpp
resolved.X_cfg_flags = (stype)((_ov_set & _ov_val) | ((stype)~_ov_set & _global));
```

The `(stype)` cast on `~_ov_set` is critical for uint8_t and uint16_t domains:

- `~uint8_t` promotes to signed int (~0xFF = 0xFFFFFF00 in 32-bit int)
- Without cast, `& _global` would AND with the full 32-bit value
- Cast back to `stype` ensures the AND operates on the right width

For uint8_t domains: `~0xFF` would be `0xFFFFFF00`; `_global` is `0xAB`; without cast, `0xFFFFFF00 & 0xAB = 0x00` (clears all bits). With cast: `(uint8_t)0x00 & 0xAB = 0x00`. Either way works HERE, but the cast is correct and prevents subtle promotion bugs in similar patterns.

### Override_set bit clears value bit ambiguity

If operator sets `override_set` bit but doesn't set `override_values` bit, the resolved bit is 0 (cleared by the override). Operators must understand: setting override_set is "force this bit to whatever override_values says, including 0."

**Mitigation:** parser convention. When operator writes `core_0_kill_switch_enabled=1`, parser sets BOTH bits (override_set + override_values both 1). When operator writes `core_0_kill_switch_enabled=0`, parser sets override_set=1 + override_values=0 (force-off).

To INHERIT global: operator OMITS the line. Parser leaves both override_set and override_values bits at 0 (the default).

### Cfg.example documentation

Per-bit shorthand is operator-friendly; document it in `engine.cfg.example` under each domain's section:

```
# RISK domain — per-core override (overrides whichever bits operator sets)
# core_0_kill_switch_enabled = 1       # force kill-switch ON for core 0
# core_0_vol_sizing_enabled = 0        # force vol-sizing OFF for core 0
# (omit any line to inherit global value)
```

The whole-mask form (`core_0_risk_cfg_flags_override = 5`) is also accepted but operator-hostile; document as advanced.

### Tests must cover the inherit path

A common test bug: tests set per-core override AND global to the same value, then assert resolved matches. The test passes even if the override mechanism is broken (because inheritance still gives the right answer).

**Test pattern:** set per-core override to value DIFFERENT from global, then assert resolved == override (not == global). Verifies override path works. Then test omission case (override_set=0); assert resolved == global. Verifies inheritance path.

### Compatibility with stamp-binding

If a cfg flag is stamp-bound (e.g., `confidence_composite_enabled` ∈ FOREACH_STAMP_BOUND_CFG via Y3 dispatch), the STAMP captures the RESOLVED per-core value, not the global. Drift detection compares resolved-at-train vs resolved-at-serve. Per-core override is transparent to stamp-binding.

See `heterogeneous-registry-pattern.md` HYBRID Form 3 for the stamp-binding integration.

### Don't try to fit non-bitmap overrides here

This pattern is specific to BITMAP fields. Per-core overrides for FPN (`risk_pct`) or int (`poll_interval`) fields use the simpler "non-zero is override" sentinel (see `PER_CORE_OVERRIDE_FIELDS` + `PER_CORE_OVERRIDE_INT_FIELDS`).

Don't mix the patterns; the registry tuple shape differs.

### Cache locality consideration

PerCoreOverrides is read at boot (resolved once into ControllerConfig per core). The override fields aren't in the hot path. So cache-line layout doesn't matter — group by domain for readability:

```cpp
uint8_t lifecycle_cfg_flags_override;
uint8_t lifecycle_cfg_flags_override_set;
uint8_t gate_cfg_flags_override;
uint8_t gate_cfg_flags_override_set;
uint16_t ml_cfg_flags_override;
uint16_t ml_cfg_flags_override_set;
// etc.
```

vs. interleaving all values then all sets. Either works; grouping by domain matches the registry order + audit-friendlier.

---

## Audit detection

`/dod-audit` detects missed applications by:

- Symptom: per-bit cfg fields like `core_N_partial_exit_enabled`, `core_N_kill_switch_enabled` explicitly declared on PerCoreOverrides
- Symptom: per-domain override resolution with explicit per-bit branches (`if (ov.kill_switch_set) resolved |= MASK_KILL_SWITCH`)

When detected → flag as `MISSED — per-bit-per-core-override-pattern`. Recommended fix: migrate to bitmap override + override_set; resolve via branchless bit-select.

---

## Patterns NOT used here (and why)

### Atomic per-bit override

Per-core overrides resolve ONCE at boot (or cfg-reload). They're not concurrent state. Atomic ops would be overhead for no win.

If overrides were live-toggleable at runtime (e.g., operator changes core_0_kill_switch_enabled while engine runs), atomic would be needed. Today: cfg-reload is the trigger, not runtime mutation.

### Per-core override on cross-domain composite flag

A flag like "`risk_active`" computed as AND across multiple domain flags: per-core override for the COMPUTED flag is wrong abstraction. Override the underlying flags individually; let the AND compute fresh per core.

### One mega-bitmap across all domains

Combine all 5 domains into one uint64_t. Loses domain ownership boundaries; one domain's override touches another's. Pattern keeps domains separate.

---

## Cross-references

- `bitmap-flag-api.md` — BITMAP_IS_SET reads transparent to override resolution
- `heterogeneous-registry-pattern.md` — DOMAIN SPLIT registries
- `cfg-flag-eligibility-criteria.md` — only flags that pass criteria 1+2 can have per-core overrides
- FoxML_Trader_v2 `CoreFrameworks/ControllerConfig.hpp:211-216` — registry definition
- FoxML_Trader_v2 `CoreFrameworks/ControllerConfig.hpp:1194-1202` — resolve walk
- FoxML_Trader_v2 `CLAUDE.md` item 4 (per-core data plane)
- FoxML_Trader_v2 `CLAUDE.md` item 12 (display↔execution invariant)
