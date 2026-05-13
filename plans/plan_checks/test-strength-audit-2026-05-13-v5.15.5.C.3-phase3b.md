# /test-strength-audit report — v5.15.5.C.3 Phase 3b (097f91f..d410525) — 2026-05-13

**Scope:** commit range `097f91f..d410525` on branch `feat/v5.15-live-readiness`
**Files scanned:** `tests/controller_test.cpp`, `experiments/per_core_sharding/test_event_log_head_to_head.cpp`
**Net diff:** 28 insertions / 14 deletions in `controller_test.cpp` (42 line delta); 4 insertions / 2 deletions in `test_event_log_head_to_head.cpp`
**Test count claim from commit:** 3032/3032 passing
**Migration shape:** 16 `OrderManager_Init` call sites updated (added `/*partial_exit_enabled=*/0` param) + 10 `r->oms.event_log_mode = N` direct field writes converted to `MBS_SET_U8(...)`

---

## Summary

| Pattern | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|
| A: Count weakenings (== → >=) | 0 | 0 | 0 | 0 |
| B: Strict-to-loose substitutions | 0 | 0 | 0 | 0 |
| C: Test deletion w/o justification | 0 | 0 | 0 | 0 |
| D: Empty / tautological assertions | 0 | 0 | 0 | 0 |
| E: Comment-only test deletion | 0 | 0 | 0 | 0 |
| INFO: Coverage gaps from migration (not weakenings) | 0 | 2 | 1 | 3 |

**No assertion weakenings detected.** Phase 3b changes are mechanical migrations
of test fixtures to match the new `OrderManager_Init` signature and
`event_log_mode` storage location. All 26 changed sites preserve their original
test intent.

---

## Per-question response to caller (5 specific items)

### Question 1: Any assertion weakening?

**Answer: NONE.** Only ONE `check(...)` line was modified in the entire range
(line 9160 `SHARDED_SNAPSHOT_VERSION`), and it's a legitimate version-constant
bump from `== 7u` to `== 8u` with the doc-string body updated to record the
v5.15.5.C.3 → v8 lineage. STRICT `==` form preserved on both sides — not a
weakening.

- `tests/controller_test.cpp:9160-9161`
  - Pre: `check("v5.11.65: SHARDED_SNAPSHOT_VERSION is 7 ...", SHARDED_SNAPSHOT_VERSION == 7u);`
  - Post: `check("v5.15.5.C.3: SHARDED_SNAPSHOT_VERSION is 8 ...", SHARDED_SNAPSHOT_VERSION == 8u);`

No deletions of `check(` lines. No `// check(` (comment-only disable). No empty
or tautological assertions added. No `==` → `>=` count weakenings.

### Question 2: Bytewise equivalence of MBS_SET_U8 conversion

**Answer: SEMANTICALLY EQUIVALENT, but with one important nuance — the field
itself was deleted, so MBS_SET is the ONLY way to write the value.**

Pre-Phase-3b: `r->oms.event_log_mode = 1` wrote a 4-byte int field.

Post-Phase-3b: the `event_log_mode` int field was REMOVED from
`OrderManagerState` (commit message: "event_log_mode int field removed from
OrderManagerState; replaced by 2-bit slot at bits 3-4 of oms_state_flags").

`MBS_SET_U8(r->oms.oms_state_flags, MASK_OMS_STATE_EVENT_LOG_MODE,
SHIFT_OMS_STATE_EVENT_LOG_MODE, 1)` writes value `1` to the 2-bit slot at bits
3-4 of `oms_state_flags` (uint8_t). With `BITS=2, SHIFT=3`, this:
- Sets bit 3 (value 1)
- Clears bit 4 (high bit of the 2-bit slot)
- Preserves bits 0-2 (single-bit flag region: LIVE_TRADING, PARTIAL_EXIT_ENABLED, KILL_SWITCH_TRIPPED)
- Preserves bits 5-7 (reserved region)

Result: `oms_state_flags |= 0x08` and `oms_state_flags &= ~0x10` semantically.
Reads via `MBS_EQ_U8(... , 1)` or `BITMAP_ANY(... MASK_EVENT_LOG_MODE)` return
true after this write, matching the pre-migration `event_log_mode == 1`
semantic. **Production code reader paths (5 sites in
`CoreFrameworks/OrderManager.hpp`, `ShardedBacktestDriver.hpp`,
`ControllerEventLoop.hpp`) all use the new `MBS_EQ_U8` form.**

Verification of the bytewise/semantic equivalence:

| Pre-migration write | Post-migration write | Production read (post) |
|---|---|---|
| `oms.event_log_mode = 0` (default) | `oms_state_flags` bits 3-4 stay 0 | `BITMAP_NONE(... MASK_EVENT_LOG_MODE)` → true |
| `oms.event_log_mode = 1` | `MBS_SET_U8(... ,1)` sets bit 3 | `MBS_EQ_U8(... ,1)` → true |
| `oms.event_log_mode == 1` (test read) | (no equivalent reads in tests; field deleted) | N/A |

### Question 3: Any remaining test-side reads of `oms.event_log_mode` as field?

**Answer: NONE. Clean.** Grepped both `tests/controller_test.cpp` and
`experiments/per_core_sharding/test_event_log_head_to_head.cpp`:

- `grep -nE 'oms\.event_log_mode|oms->event_log_mode'` → **no matches**

The 4 remaining occurrences of the string `event_log_mode` in
`tests/controller_test.cpp` are all in comments or parameter-label syntax:
- Line 7346: comment (`// Regression guard for v4.7.15 fix...`)
- Line 9899: parameter label (`/*event_log_mode=*/0`)
- Line 15257: comment
- Line 15264: parameter label (`/*event_log_mode=*/1`)

Build cleanliness (3032/3032 passing) confirms there are no orphaned field
reads — they would fail to compile since the field was deleted from the
struct.

### Question 4: Round-trip persist test at controller_test.cpp:5443-5550 — does it still assert ALL PERSIST-kind fields?

**Answer: NO — but this is a pre-existing coverage gap, not introduced by
Phase 3b. Phase 3b did add ONE new PERSIST field that the round-trip does NOT
exercise.**

The round-trip test was NOT touched in the audit range (no diff hunk in
5443-5550). Field-by-field comparison:

**Pre-Phase-3b PERSIST registry (`FOREACH_OMS_PERSIST_FIELD`; 9 rows):**

| Row | Field | Asserted in round-trip? | Where |
|---|---|---|---|
| 1 | `balance` | YES | line 5510 |
| 2 | `realized_pnl` | YES | line 5512 |
| 3 | `ks_peak_balance` | NO | — |
| 4 | `kill_switch_tripped` | YES (set + clear cases) | lines 5517, 5531 (added v5.15.5.C.2.1) |
| 5 | `total_fees` | NO | — |
| 6 | `total_maker_fees` | NO | — |
| 7 | `total_taker_fees` | NO | — |
| 8 | `maker_fills_count` | NO | — |
| 9 | `taker_fills_count` | NO | — |

**Post-Phase-3b PERSIST view of `FOREACH_OMS_FIELD` (10 rows — added 1):**

Same 9 rows above PLUS:

| Row | Field | Asserted in round-trip? |
|---|---|---|
| 10 | `paper_session_start_us` (added Phase 2 of this sprint) | **NO** |

**No field silently dropped by the migration.** Wire format byte-preserved
per commit message. Pre-existing gap of 6 unverified PERSIST fields
(`ks_peak_balance`, `total_fees`, `total_maker_fees`, `total_taker_fees`,
`maker_fills_count`, `taker_fills_count`) remains unchanged.

The NEW gap from this sprint is `paper_session_start_us` (added by Phase 2,
NOT by Phase 3b — but live in the audit range because the persist test is the
canonical surface for verifying it). Surfaced as **INFO-1 below**.

### Question 5: OrderManager_Init defaults test — 8 boot-init fields per AUTOPOPULATE walk?

**Answer: The codebase has NO single-site comprehensive "OrderManager_Init
defaults" test that covers the 8 init parameters as a whole.** Coverage of
the new AUTOPOPULATE bit-init paths (LIVE_TRADING, PARTIAL_EXIT_ENABLED,
EVENT_LOG_MODE) is INDIRECT — exercised through downstream side-effect tests
but never asserted directly.

`OrderManager_Init` signature post-Phase-3b takes 8 parameters:
1. `oms` (target)
2. `adapter`
3. `live_trading` → sets `MASK_OMS_STATE_LIVE_TRADING` bit (via BIT row)
4. `partial_exit_enabled` → sets `MASK_OMS_STATE_PARTIAL_EXIT_ENABLED` bit (NEW, Finding A)
5. `starting_balance` → writes `balance`, `ks_peak_balance` (DO_RESET DIRECT)
6. `fee_rate` → writes `fee_rate`, `fee_rate_maker`, `fee_rate_taker`
7. `event_log_mode` (optional, default 0) → sets 2-bit slot (NEW MULTI_BIT, Finding A')
8. `event_log_path` (optional)

**Direct boot-init assertions in tests (post-Phase 3b):**

| Field | Test | Line |
|---|---|---|
| `last_seen_trade_id == 0` | "v5.14.4.0: OrderManager_Init zero-inits..." | 19995-19996 |
| `last_exit_predicted_meta[i] == 0` | "v5.13.4.A / v5.15.5.C.2.1 (LOW-2): meta[] valid=0 by default" | 18694-18697 |

**Boot-init assertions for the 8 AUTOPOPULATE-driven init paths: NONE.**
No test directly verifies:
- After `OrderManager_Init(..., live_trading=1, ...)`, is `MASK_OMS_STATE_LIVE_TRADING` bit set?
- After `OrderManager_Init(..., partial_exit_enabled=1, ...)`, is `MASK_OMS_STATE_PARTIAL_EXIT_ENABLED` bit set?
- After `OrderManager_Init(..., event_log_mode=1, ...)`, is the 2-bit slot value == 1?
- After `OrderManager_Init(...)`, is `balance == starting_balance`?
- After `OrderManager_Init(...)`, is `fee_rate == fee_rate_taker == fee_rate_maker`?

**Pre-Phase-3b had the same gap** (no direct OrderManager_Init init-state
test). Phase 3b did NOT make this worse, but it added 2 new init paths
(`partial_exit_enabled` bit + `event_log_mode` 2-bit slot via
AUTOPOPULATE) that have no direct test coverage.

This is NOT a weakening (no prior test was removed); it's a coverage gap
unchanged by Phase 3b for the original paths, and a NEW coverage gap for
the 2 added paths. Surfaced as **INFO-2 below**.

---

## Findings (severity-ordered)

### INFO-1 — New PERSIST field `paper_session_start_us` lacks round-trip test coverage

**Surface:** `tests/controller_test.cpp:5443-5562` (round-trip persist test)

**Context:** Phase 2 (commit 4486de8 within audit range) added
`paper_session_start_us` as a `DO_RESET DIRECT PERSIST` row in
`FOREACH_OMS_FIELD`. Snapshot version bumped 7→8 to accommodate. The
round-trip test (the canonical verification surface for wire format
byte-preservation) does not exercise the new field.

**What's missing:** Assertions of shape:
```cpp
// In the round-trip test body, before save:
r->oms.paper_session_start_us = 1715600000000000ULL;  // sentinel value

// After load:
check("round-trip: paper_session_start_us restored",
      r2->state.oms->paper_session_start_us == 1715600000000000ULL);
```

**Risk:** Wire format regression in `paper_session_start_us` save/load (e.g.,
endianness, off-by-8-bytes in stream position, tmp_<name> typo in
PERSIST_DECLARE/READ/COMMIT projections) would NOT be caught by the existing
round-trip test. Currently relies on compile-time enforcement of the X-macro
expansion, which is strong but not equivalent to runtime verification.

**Severity:** INFO (sprint-level coverage gap; not a regression introduced
by Phase 3b — the gap was created when Phase 2 added the field without an
assertion). The X-macro expansion + commit message claim of byte-preservation
is strong structural evidence; runtime assertion would be belt-and-suspenders.

**Recommendation:**
- Add a one-line assertion to the round-trip test before sub-ship close.
- Cost: ~10 LOC (1 setter pre-save + 1 check post-load + sentinel constant).
- Trigger: should land before Phase 10 close (the umbrella v5.15.5.C.3 tag).

### INFO-2 — AUTOPOPULATE bit-init paths (LIVE_TRADING, PARTIAL_EXIT_ENABLED, EVENT_LOG_MODE) lack direct boot-state tests

**Surface:** `tests/controller_test.cpp` (no specific line; gap is a missing
test fixture not a deletion)

**Context:** Phase 3b migrated `OrderManager_Init` body to single
`OMS_INIT_AUTOPOPULATE` call. The macro expands via `FOREACH_OMS_FIELD`
with `STORAGE_KIND` dispatch (DIRECT / BIT / MULTI_BIT / ATOMIC). Three new
or refactored bit-init paths:
- `live_trading` int param → `MASK_OMS_STATE_LIVE_TRADING` BIT row
  (Finding A: moved from Layer 2 special-case into the registry)
- `partial_exit_enabled` int param → `MASK_OMS_STATE_PARTIAL_EXIT_ENABLED`
  BIT row (Finding A: NEW; was post-Init external SET pre-Phase-3b)
- `event_log_mode` int param → `MASK_OMS_STATE_EVENT_LOG_MODE` MULTI_BIT
  2-bit slot (Finding A': NEW; was a separate int field pre-Phase-3b)

**What's missing:** A direct test fixture along these lines:
```cpp
{
    OrderManagerState<64> oms;
    ExchangeAdapter<64> empty{};
    // Test 1: partial_exit_enabled=1 → bit set
    OrderManager_Init(&oms, empty, /*live=*/1, /*partial_exit_enabled=*/1,
                      FPN_FromDouble<64>(10000.0), FPN_FromDouble<64>(0.001),
                      /*event_log_mode=*/1);
    check("Phase 3b: live_trading=1 → LIVE_TRADING bit set",
          BITMAP_IS_SET(oms.oms_state_flags, tt::MASK_OMS_STATE_LIVE_TRADING));
    check("Phase 3b: partial_exit_enabled=1 → PARTIAL_EXIT_ENABLED bit set",
          BITMAP_IS_SET(oms.oms_state_flags, tt::MASK_OMS_STATE_PARTIAL_EXIT_ENABLED));
    check("Phase 3b: event_log_mode=1 → slot value == 1",
          MBS_EQ_U8(oms.oms_state_flags, tt::MASK_OMS_STATE_EVENT_LOG_MODE,
                    tt::SHIFT_OMS_STATE_EVENT_LOG_MODE, 1));
    // Test 2: defaults → all bits clear
    OrderManagerState<64> oms2;
    OrderManager_Init(&oms2, empty, /*live=*/0, /*partial_exit_enabled=*/0,
                      FPN_FromDouble<64>(10000.0), FPN_FromDouble<64>(0.001));
    check("Phase 3b: defaults → LIVE_TRADING bit clear",
          !BITMAP_IS_SET(oms2.oms_state_flags, tt::MASK_OMS_STATE_LIVE_TRADING));
    check("Phase 3b: defaults → PARTIAL_EXIT_ENABLED bit clear",
          !BITMAP_IS_SET(oms2.oms_state_flags, tt::MASK_OMS_STATE_PARTIAL_EXIT_ENABLED));
    check("Phase 3b: defaults → EVENT_LOG_MODE slot value == 0",
          MBS_EQ_U8(oms2.oms_state_flags, tt::MASK_OMS_STATE_EVENT_LOG_MODE,
                    tt::SHIFT_OMS_STATE_EVENT_LOG_MODE, 0));
}
```

**Risk:**
- AUTOPOPULATE registry-driven BIT/MULTI_BIT init logic has no direct test
  asserting the bits get set correctly from the parameter values. If a
  future contributor regressed the BIT-row `INIT` expression (e.g.,
  `ctx.partial_exit_enabled` → `0`), it would compile cleanly and the
  existing 9 tests that `BITMAP_SET(... PARTIAL_EXIT_ENABLED)` AFTER Init
  would mask the regression.
- The 9 tests at lines 7159, 7723, 7755, 7849, 9902 etc. that
  `BITMAP_SET(MASK_OMS_STATE_PARTIAL_EXIT_ENABLED)` post-Init are
  effectively testing the bit storage, not the AUTOPOPULATE init path.
- Indirect production-path tests (e.g., live engine tests that pass
  `live_trading=1` and observe live-mode behavior) DO exercise the
  AUTOPOPULATE flow but don't isolate the bit-init from downstream
  behavior. A subtle init-bug would show up as a downstream failure, not
  as a clean test of "AUTOPOPULATE writes the bit."

**Severity:** INFO. Coverage gap, not a weakening; pre-existing for
`live_trading`, NEW for `partial_exit_enabled` and `event_log_mode`.

**Recommendation:**
- Add a 10-15 LOC test fixture per Phase 3b close.
- Pair with the round-trip `paper_session_start_us` assertion (INFO-1).
- These together would close ~20 LOC of regression-protection gap before
  the umbrella v5.15.5.C.3 tag.

### INFO-3 — Pre-existing tautological assertion at line 18748 (NOT in audit range)

**Surface:** `tests/controller_test.cpp:18748-18749`

```cpp
check("v5.13.4.B: optimistic counterfactual biases against firing (sanity)",
      true);
```

Pure tautology. Per Pattern D this is a finding, BUT `git blame` shows
this line was committed in `c03749eb` (Caramel, 2026-05-08) — well before
the audit range. Not introduced by Phase 3b.

**Severity:** INFO (pre-existing tech debt). Audit range CLEAN on this dimension.

**Recommendation:** Either delete the assertion (it provides no signal) or
strengthen with a meaningful invariant. Out of scope for v5.15.5.C.3 — log
in `DOCS/TECH_DEBT.md` as a sprint-end cleanup candidate. No commit-time
action.

---

## Recommendations

### Must fix before merge / commit
- None. Phase 3b is a clean mechanical migration with no assertion
  weakenings.

### Worth fixing during current sprint (v5.15.5.C.3 close)
- **INFO-1**: Add round-trip persist assertion for `paper_session_start_us`
  (added Phase 2; canonical wire-format verification surface). ~10 LOC.
- **INFO-2**: Add a direct AUTOPOPULATE bit-init test fixture covering
  `live_trading`, `partial_exit_enabled`, `event_log_mode` boot-init. ~20 LOC.

These pair naturally — both touch `OrderManager_Init` / persist surfaces.
Single test block in `tests/controller_test.cpp` would close both gaps.
Both inputs were added/modified in this sprint (Phase 2 + Phase 3b); both
are first-class observability surfaces that warrant a direct test before
the umbrella v5.15.5.C.3 tag.

### Defer with TECH_DEBT entry
- **INFO-3**: Pre-existing tautological `check(..., true)` at line 18748.
  Out of audit range; log in `DOCS/TECH_DEBT.md` if not already tracked.

No auto-writes to `DOCS/TECH_DEBT.md` performed — INFO-1 + INFO-2 are
sprint-close coverage adds (not deferrals); INFO-3 is pre-existing and
already a candidate for the existing dust/triage backlog.

---

## Verdict: **GREEN**

No HIGH or MEDIUM findings. No assertion weakenings. The 26-site
migration (16 `OrderManager_Init` calls + 10 `event_log_mode` field
conversions) is mechanically clean and semantically equivalent to the
pre-Phase-3b test surface. The ONLY `check(...)` line modified is a
legitimate `SHARDED_SNAPSHOT_VERSION` constant bump (7→8) with strict
`==` form preserved.

INFO findings are coverage gaps (not weakenings) — pre-existing or
introduced by Phase 2 (`paper_session_start_us` adds) / Phase 3b
(AUTOPOPULATE bit-init paths). Recommended to close before the
umbrella v5.15.5.C.3 tag but not blocking for Phase 3b checkpoint.

3032/3032 tests passing per commit message. Build green. Migration
discipline upheld.
