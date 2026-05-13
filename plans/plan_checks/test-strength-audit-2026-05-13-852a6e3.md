# /test-strength-audit report — commit 852a6e3 — 2026-05-13

**Scope:** `git show 852a6e3` (v5.15.5.C.2 close: OMS bitmap + persist registry + fee helper + canonical mirror + slot bitmap)
**Files audited:**
- `tests/controller_test.cpp` (4 added / 4 removed `check()` lines)
- `experiments/per_core_sharding/test_execution_core_concurrent.cpp` (1 ↔ 1)
- `experiments/per_core_sharding/test_kill_switch.cpp` (8 ↔ 8)
- `experiments/per_core_sharding/test_oms.cpp` (1 ↔ 1)
- `experiments/per_core_sharding/test_sharded_backtest.cpp` (1 ↔ 1)

## Summary

| Pattern | HIGH | MEDIUM | LOW | INFO | Total |
|---|---|---|---|---|---|
| A: Count weakenings (== → >=) | 0 | 0 | 0 | 0 | 0 |
| B: Strict-to-loose substitutions | 0 | 0 | 0 | 1 | 1 |
| C: Test deletion w/o justification | 0 | 0 | 0 | 0 | 0 |
| D: Empty / tautological assertions | 0 | 0 | 0 | 0 | 0 |
| E: Comment-only test deletion | 0 | 0 | 0 | 0 | 0 |
| F (extension): Aggregate-check semantic change | 0 | 0 | 1 | 0 | 1 |

**Test count delta:** +0 (15 added, 15 removed — every removal is a 1:1 migration to the bitmap-API equivalent). No `check()` lines deleted.

## Findings (severity-ordered)

### INFO — Field-rename substitution at `tests/controller_test.cpp:18404`

**Removed:** `check("v5.13.0.B: last_exit_was_predicted[] defaults all-zero post-Init", all_zero);`
**Added:**   `check("v5.13.0.B / v5.15.5.C.2 (S3b): last_exit_predicted_bitmap defaults zero post-Init", all_zero);`

Field renamed from `uint8_t last_exit_was_predicted[16]` to `uint16_t last_exit_predicted_bitmap` per S3b. The version tag is retained (preserves traceability); the assertion variable (`all_zero`) is unchanged. Not a weakening — pure rename to match new storage shape.

### LOW — Aggregate-check semantic change at `tests/controller_test.cpp:18399-18403`

**Pre-S3b loop (16 reads):**
```cpp
for (int i = 0; i < MAX_PORTFOLIO_POSITIONS; ++i) {
    if (oms.last_exit_was_predicted[i] != 0) { all_zero = 0; break; }
    if (oms.last_exit_predicted_p[i] != 0.0) { all_zero = 0; break; }
}
```

**Post-S3b (1 word read + 16 p-array reads):**
```cpp
if (oms.last_exit_predicted_bitmap != 0) all_zero = 0;
for (int i = 0; i < MAX_PORTFOLIO_POSITIONS; ++i) {
    if (oms.last_exit_predicted_p[i] != 0.0) { all_zero = 0; break; }
}
```

**Analysis:** the new check is **strictly stronger or equal**.
- `uint16_t last_exit_predicted_bitmap != 0` detects ANY set bit across all 16 slots in a single read.
- The old `uint8_t[16]` loop could only inspect bytes one at a time.
- Both fail identically on the only failure mode (any bit set / any byte non-zero).
- For valid post-Init state, both equal `all_zero == 1`.

Not a weakening; semantically equivalent for valid input, stronger detection for partial-corruption cases. No action needed.

### INFO — Strict-to-loose-shape substitutions across 14 sites (Pattern B form, but legitimate)

Sites at `tests/controller_test.cpp` lines 5750, 5778, 5789, 7126, 7273, 7343, 7471, 7550, 7690, 7722, 7752, 7816, 9868, 9891 (write sites — not assertions); plus assertions at the experiments/ paths:
- `experiments/.../test_execution_core_concurrent.cpp:282`
- `experiments/.../test_kill_switch.cpp:59, 66, 88, 117, 141, 203, 260, 289`
- `experiments/.../test_oms.cpp:146`
- `experiments/.../test_sharded_backtest.cpp:313`

**Pattern shape:**
- `EXPECT(state.oms->kill_switch_tripped == 1, "...")` → `EXPECT(BITMAP_IS_SET(state.oms->oms_state_flags, tt::MASK_OMS_STATE_KILL_SWITCH_TRIPPED), "...")`
- `EXPECT(oms.live_trading == 0, "...")` → `EXPECT(!BITMAP_IS_SET(oms.oms_state_flags, tt::MASK_OMS_STATE_LIVE_TRADING), "...")`

**Semantic equivalence verified at `MemHeaders/BitmapMacros.hpp:78`:**
```cpp
#define BITMAP_IS_SET(field, mask)  (((field) & (mask)) != 0)
```
The mask is a single-bit constant (`MASK_OMS_STATE_KILL_SWITCH_TRIPPED` = bit 2 of `oms_state_flags`). For a single-bit mask, `BITMAP_IS_SET(x, mask)` returns `true` iff that bit is set — strictly equivalent to the pre-refactor `field == 1`. No `BITMAP_IS_SET(...) == 1` comparisons were introduced (no implicit-bool-to-int weakness).

The substitution is **structural**, mandated by the S3a bit-pack of 3 OMS booleans into `uint8_t oms_state_flags`. The pre-refactor `kill_switch_tripped == 1` form is no longer reachable because the underlying field no longer exists.

Not a weakening; the commit message documents the substitution as part of CLAUDE.md item 20 (bitmap-flag-api 7th application).

## Pre-existing gap (not introduced by this commit) — flag for follow-up

**Round-trip persist coverage of `kill_switch_tripped` is weak**, but this gap predates v5.15.5.C.2.

The `ShardedSnapshot_Save` / `ShardedSnapshot_Load` round-trip test at `tests/controller_test.cpp:5493-5533` asserts:
- `round-trip: oms.balance restored` (line 5502)
- `round-trip: oms.realized_pnl restored` (line 5504)
- `round-trip: core_kill_tripped` — **per-core** state (line 5512) via `CORE_STATE_FLAG_IS_SET(...)`

It does **NOT** assert round-trip of the OMS-level `kill_switch_tripped` (now `BITMAP_IS_SET(oms.oms_state_flags, MASK_OMS_STATE_KILL_SWITCH_TRIPPED)`). The S3a-W refactor at `MemHeaders/OmsPersistFieldRegistry.hpp:91-100` adds the BIT-kind extraction for this field; wire format is byte-preserved per the registry doc-block comment (lines 73-90).

**Recommendation:** add a test that sets `BITMAP_SET(r->oms.oms_state_flags, tt::MASK_OMS_STATE_KILL_SWITCH_TRIPPED)`, saves, loads into a fresh state, and asserts the bit round-trips. This tests the BIT-kind dispatch macros at `OmsPersistFieldRegistry.hpp:109-121`. Not blocking (gap was pre-existing); raise as a sprint follow-up or queue under TECH_DEBT.

## Recommendations

### Must fix before merge / commit
- None.

### Worth fixing during current sprint
- None.

### Defer / follow-up
- Add OMS `kill_switch_tripped` save/load round-trip test (pre-existing gap surfaced by audit; raise as TECH_DEBT entry if Caramel agrees). Estimated cost: ~30 LOC, follows pattern at `tests/controller_test.cpp:5454-5533`.

## Verdict: GREEN

No HIGH or MEDIUM findings. The 15 test-site migrations are 1:1 semantic-preserving substitutions mandated by the S3a/S3b bit-pack refactors. Test count preserved (15 ↔ 15). No `check()` deletions. No `==`→`>=` count weakenings. No empty/tautological assertions. No comment-disabled tests.

The one observed semantic shift (the 16-slot loop collapsing to a single `bitmap != 0` read) is **strictly stronger** than the pre-refactor form, not weaker.

Commit ready as-shipped from a test-strength perspective. One pre-existing coverage gap (OMS-level `kill_switch_tripped` round-trip) is worth queuing as a follow-up but not blocking.
