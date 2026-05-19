---
type: ledger-template
class_id: 20
title: Bitmap field without overflow guard (silent-truncation)
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
surface_tags: [bitmap-packed, registry]
severity: high
recurrence_count: 1
first_instance: v5.15.5.F.4
closure_mechanism: co-located static_assert(FOREACH_X_COUNT_VALUE <= sizeof(X_flags_type) * 8) at every FOREACH_X declaration + type-upgrade decision tree (uint8 -> uint16 -> uint32 -> uint64 -> split or multi-bit pack) + /dod-audit extension detecting registries lacking paired static_assert
sister_classes: [18]
---

## Class 20 — Bitmap field without overflow guard (silent-truncation)

**Surface:** any registry + bitmap pair (~30+ in the codebase). FOREACH_X paired with X_flags field of fixed width (uint8_t / uint16_t / uint32_t / uint64_t).

**Symptom:** new registry entry's flag bit "doesn't work" — `BITMAP_IS_SET(flags, MASK_NEW)` always returns false; `BITMAP_SET(flags, MASK_NEW)` is a silent no-op. Code compiles cleanly; tests using the flag pass trivially (because the flag is always 0 — there's no bit to test or set); operator-visible behavior diverges from documentation. Hours of debug before realizing the bit shift overflowed the bitmap type.

**Root cause:** FOREACH_X registry grows organically. Bitmap type was uint8_t when registry had 5 entries. Now registry has 9 entries; `1 << 8` exceeds uint8_t's width; result is implementation-defined (typically 0, sometimes UB). The new enum value silently equals 0; `BITMAP_IS_SET(flags, 0)` is always false; `BITMAP_SET(flags, 0)` is a no-op. **No runtime check** can detect this — the bit doesn't exist; nothing to inspect.

**Detection:**
```bash
# Find all FOREACH_X registries + their paired bitmap fields:
rg "^#define FOREACH_(\w+)\s*\(X\)" --type cpp .

# For each, find bitmap field paired with it:
rg "uint(8|16|32|64)_t\s+\w+_flags" CoreFrameworks/ ML_Headers/ MemHeaders/

# For each pair, check for paired static_assert:
rg "static_assert\(FOREACH_\w+_COUNT_VALUE\s*<=\s*sizeof" CoreFrameworks/ ML_Headers/ MemHeaders/
# Missing static_assert = vulnerable to overflow.
```

**Known instances:**
- 2026-05-14: surfaced during v5.15.5.F.4 audit synthesis. Multiple bitmap-paired registries in codebase lack overflow guards. Structurally closed at `.F.4h` via audit pass + adding `static_assert(FOREACH_X_COUNT_VALUE <= sizeof(X_flags_type) * 8)` to every paired bitmap. Pattern: `DESIGN_SPECS/refactor-patterns/bitmap-overflow-protection-discipline.md`. CLAUDE.local.md "Going-forward rule: bitmap overflow static_assert is mandatory (set 2026-05-14)".

**Prevention:**
- **Co-located static_assert** at end of every FOREACH_X declaration:
  ```cpp
  #define FOREACH_X_COUNT_ENTRY(...) +1
  constexpr size_t FOREACH_X_COUNT_VALUE = 0 FOREACH_X(FOREACH_X_COUNT_ENTRY);
  #undef FOREACH_X_COUNT_ENTRY
  
  static_assert(FOREACH_X_COUNT_VALUE <= sizeof(X_flags_type) * 8,
                "FOREACH_X overflowed bitmap type. Upgrade type width OR "
                "split into multiple bitmaps OR use multi-bit state encoding.");
  ```
- **Type-upgrade decision tree** (per `DESIGN_SPECS/refactor-patterns/bitmap-overflow-protection-discipline.md`): uint8_t → uint16_t → uint32_t → uint64_t → split or multi-bit pack.
- **`/dod-audit` extension** detects every FOREACH_X without a paired static_assert.
- CLAUDE.md item promotion candidate (after `.F.4h` audit closes the existing inventory).

**Related classes:**
- Class 18 (Mirror-incomplete) — same "silently appears to work" failure shape
- CLAUDE.md item 20 (BITMAP_* API) — usage pattern; this class is the discipline complement
- CLAUDE.md item 30 (registry-bitmap SET discipline) — sister rule for SET-site consistency
