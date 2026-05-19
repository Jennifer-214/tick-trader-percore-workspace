# /parity-check report — 2026-05-13 — v5.15.5.C.3 Phase 3b

## Plan summary

- **HEAD:** `d4105250c730fbf822aa685d115b31ecdc8a1291`
- **Branch:** `feat/v5.15-live-readiness`
- **Predecessor:** `4486de86` (v5.15.5.C.3 phases 1-3a intermediate checkpoint)
- **Tests:** `3052/3052 passing` (controller_test.cpp, verified on local build)
- **Calls graph diff:** N/A this audit
- **Audit scope:** OMS canonical 8-tuple registry consolidation; snapshot v8 wire-format byte-preservation; `event_log_mode` int → 2-bit slot migration; `OrderManager_Init` signature change adding `partial_exit_enabled` (production-caller class).
- **Cross-check baseline:** post-v5.14.11.B / post-v5.15.5.C.2.1 protections inventory + PARITY-001..024 ledger.

### Phase 3b — what changed (recap from commit message)

1. **Legacy `FOREACH_OMS_PERSIST_FIELD` deleted**; `MemHeaders/OmsPersistFieldRegistry.hpp` removed entirely. PERSIST view now projected from the canonical `FOREACH_OMS_FIELD` registry via `OMS_PROJECT_PERSIST_*` X-macro dispatchers.
2. **`FOREACH_OMS_FIELD` tuple expanded to 8 columns**: `X(NAME, TYPE, INIT, RESET, RESET_KIND, STORAGE_KIND, PERSIST_KIND, STORAGE_MASK)`. 3-axis dispatch: `RESET_KIND × STORAGE_KIND × PERSIST_KIND` orthogonal.
3. **Templated helpers** `tt::_oms_init_value_fields<F>()` + `tt::_oms_reset_value_fields<F>()` encapsulate the FOREACH walk (CLAUDE.md item 23 type-trait dispatch via templated helpers).
4. **Finding A SHIPPED** — `partial_exit_enabled` moved into FOREACH_OMS_FIELD as BIT+SKIP_PERSIST row. `OrderManager_Init` signature changes to add `int partial_exit_enabled` at 4th positional. Engine's external `BITMAP_SET(MASK_OMS_STATE_PARTIAL_EXIT_ENABLED)` call dropped.
5. **Finding A' SHIPPED** — `int event_log_mode` field removed from `OrderManagerState`; replaced by 2-bit slot at bits 3-4 of `oms_state_flags` (MULTI_BIT + SKIP_PERSIST). 4 bytes saved per OMS in COLD cluster.
6. **Multi-bit primitives** added to `BitmapMacros.hpp`: `MBS_GET/_SET/_EQ/_ATOMIC_GET` for U8/U16/U32/U64 + helpers. 2nd codebase application of `multi-bit-state-encoding-pattern.md`.
7. **Hybrid bitmap pattern** in `OmsStateFlagRegistry.hpp`: single-bit flags (bits 0-2) cohabit with multi-bit slot (bits 3-4) in shared uint8_t. New `FOREACH_OMS_STATE_MULTI_BIT` sister registry.
8. **AUTOPOPULATE layers collapsed 8→5**: Layer 2 special-case scalars + Layer 3 atomic stores absorbed into Layer 1 registry walk via STORAGE_KIND dispatch.

---

## Audit summary verdict

**GREEN with 1 HIGH and 2 MEDIUM findings (none parity-blocking).** Wire format byte-preservation verified clean; production-caller class closure for `partial_exit_enabled` correctly extinguishes the Class 18 mirror at EngineSharded but **misses a sister mirror in BacktestSharded** (HIGH). Stale experiment harnesses (not in production build) are broken post-3b (MEDIUM). Round-trip test coverage of the v6 OMS counters + paper_session_start_us is missing direct assertions (MEDIUM); structural byte-byte equivalence still guaranteed by canonical row ordering.

| Category | Verdict | Notes |
|---|---|---|
| A — Tick consumption parity | N/A this sub-ship | Unchanged |
| B — Feature pipeline parity | N/A this sub-ship | Unchanged |
| C — Label pipeline parity | N/A this sub-ship | Unchanged |
| D — Scaler sidecar binding | N/A this sub-ship | Unchanged |
| E — Stamp body schema parity | N/A this sub-ship | ML headers untouched (verified) |
| F — Cfg parity | N/A this sub-ship | Unchanged |
| G — Cross-binary handshake | PASS | Snapshot v8 wire format byte-preserved |
| H — Threading + initialization | PASS | `OrderManager_Init` callers all pass `partial_exit_enabled` derived from cfg.lifecycle_cfg_flags |
| I — Determinism | PASS | Registry-driven init is deterministic; no clock_gettime in hot path |
| J — Observability surface coverage | PASS | No new failure modes added |
| L — Production-caller field-population audit | **HIGH-1** | BacktestSharded retains stale external SET/CLR mirror for PARTIAL_EXIT_ENABLED bit |
| K — Build-warning audit | DEFERRED | Pending operator-run `./build.sh test gui suite` warning audit; spot-check on `./build.sh test` clean |

---

## Findings by severity

### HIGH

#### HIGH-1 — BacktestSharded.hpp retains stale external SET/CLR mirror for PARTIAL_EXIT_ENABLED (Class 18 mirror not fully eliminated by Finding A)

- **File:** `/home/caramel/code/FoxML_Trader_v2/Backtest/BacktestSharded.hpp:197-201`
- **Severity:** HIGH (Class 18 mirror — same pattern at multiple sites; Phase 3b's Finding A was specifically intended to eliminate this exact mirror)
- **Class:** v5.15.5.C.3 Finding A (Class 18 mirror at production-caller level — same root cause as PARITY-002/003/004/005/008 / PARITY-009/010/011/012 that prior sprints closed via AUTOPOPULATE / PostLoadSetup registries)

**Symptom — site comparison:**

`CoreFrameworks/EngineSharded.hpp:670-674` post-3b correctly removed the external SET/CLR:
```cpp
// v5.15.5.C.3 (Finding A) — external PARTIAL_EXIT_ENABLED SET call dropped.
// Bit is now set inside OMS_INIT_AUTOPOPULATE via the BIT-kind registry row
// for `partial_exit_enabled` (driven by the parameter passed to OrderManager_Init
// above). Adding a new cfg-derived boot bit flag = ONE row in
// FOREACH_OMS_FIELD; no more external SET sites needed.
```

`Backtest/BacktestSharded.hpp:197-201` post-3b STILL has the redundant mirror:
```cpp
// v4.7.15: mirror partials geometry to OMS for the post-fill drainer's
// slot→core_id mapping. Same as EngineSharded_Run sets it from cfg.
// v5.15.5.C.2 (S3a) — bit-packed in oms_state_flags.
if (BITMAP_IS_SET(cfg.lifecycle_cfg_flags, MASK_LIFECYCLE_CFG_PARTIAL_EXIT_ENABLED)) {
    BITMAP_SET(oms.oms_state_flags, tt::MASK_OMS_STATE_PARTIAL_EXIT_ENABLED);
} else {
    BITMAP_CLR(oms.oms_state_flags, tt::MASK_OMS_STATE_PARTIAL_EXIT_ENABLED);
}
```

This block is **dead code** — line 183 of the same file (`OrderManager_Init(&oms, empty_adapter, 0, bt_partial_exit_enabled, ...)`) already sets/clears the same bit via the registry walk inside `OMS_INIT_AUTOPOPULATE`. Both expressions derive from `cfg.lifecycle_cfg_flags & MASK_LIFECYCLE_CFG_PARTIAL_EXIT_ENABLED`, so they produce IDENTICAL values.

**Behavioral impact:** ZERO today (idempotent SET/CLR with same bit value). **But:**

- **Parity hazard if a future contributor changes one path without the other.** E.g., if a future ship adds a per-core override for partial_exit_enabled, EngineSharded would route via OmsInitCtx + the registry, while BacktestSharded's lines 197-201 would silently desync.
- **Class 18 mirror NOT fully extinguished by Finding A.** The commit message claims "Drops engine's external OMS_STATE_FLAG_SET(PARTIAL_EXIT_ENABLED) call" — singular. The sister site in BacktestSharded was missed.
- **Documentation drift.** The CLAUDE.md item 13 / item 19 / item 21 X-macro registry + AUTOPOPULATE pattern is meant to make adding new entries 1-line. The remaining BacktestSharded mirror invites future contributors to "follow the existing pattern" of external SET/CLR, defeating the structural-fix discipline.

**Reproducer / verifier:**
```bash
grep -n "MASK_OMS_STATE_PARTIAL_EXIT_ENABLED" Backtest/BacktestSharded.hpp
# expects: only IS_SET reads downstream of Init; ZERO SET/CLR calls
# actual: lines 197-201 contain BITMAP_SET + BITMAP_CLR on the bit
```

**Recommended fix (small, surgical):**
```cpp
// Delete lines 194-201 of Backtest/BacktestSharded.hpp. The bit is now set
// by OrderManager_Init (line 183) via the BIT-kind registry row.
// Comment at line 194 ("v4.7.15: mirror partials geometry…") + the block
// becomes a 3-line note explaining the migration:
// v5.15.5.C.3 (Finding A close completion): PARTIAL_EXIT_ENABLED bit set
// inside OMS_INIT_AUTOPOPULATE via the BIT-kind registry row (parameter
// `bt_partial_exit_enabled` above). External SET/CLR mirror removed.
```

**Effort:** ~10 minutes; 8 LOC delete + comment update.

**Cross-ref:** CLAUDE.md item 19 (structural fix preferred for recurring class). Pattern documented in `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md`.

**Auto-write:** This finding allocated as **PARITY-025**. Auto-written to `DOCS/PARITY_ISSUES.md` per the auto-write contract in CLAUDE.local.md (set 2026-05-09).

---

### MEDIUM

#### MEDIUM-1 — Stale experiment harnesses (`experiments/per_core_sharding/test_oms.cpp`, `test_oms_concurrent.cpp`, `test_oms_phase04_06.cpp`) will fail to compile post-3b — `partial_exit_enabled` not supplied at 4th positional

- **Files:**
  - `experiments/per_core_sharding/test_oms.cpp:142, 178, 198, 221, 248, 274, 316, 334` (8 callers)
  - `experiments/per_core_sharding/test_oms_concurrent.cpp:203, 261, 314, 378` (4 callers)
  - `experiments/per_core_sharding/test_oms_phase04_06.cpp:41` (1 caller — uses event_log_mode=1 via named arg)
- **Severity:** MEDIUM (not in `./build.sh test` production build; stale call sites pass `FPN_Zero<64>()` at the 4th positional position which is now `int partial_exit_enabled`; FPN→int is not convertible → compile error)
- **Class:** Production-caller signature change without backward-compat shim

**Symptom:**

Post-3b OrderManager_Init signature:
```cpp
inline void OrderManager_Init(OrderManagerState<F>* oms,
                              const ExchangeAdapter<F>& adapter,
                              int live_trading,
                              int partial_exit_enabled,    // NEW (4th positional)
                              FPN<F> starting_balance,
                              FPN<F> fee_rate,
                              int event_log_mode = 0,
                              const char* event_log_path = "logging/order_events.bin");
```

Stale experiment callers:
```cpp
OrderManager_Init(&oms, empty, /*live_trading=*/0, FPN_Zero<64>(), FPN_Zero<64>());
//                                                  ^^^^^^^^^^^^^^
//                                                  passed as `int partial_exit_enabled`
//                                                  FPN<64> has no operator int() → COMPILE ERROR
```

Pre-3b signature was:
```cpp
inline void OrderManager_Init(oms, adapter, live_trading,
                              FPN<F> starting_balance,  // 4th positional pre-3b
                              FPN<F> fee_rate, ...);
```

So pre-3b: `OrderManager_Init(&oms, empty, 0, FPN_Zero<64>(), FPN_Zero<64>())` was valid. Post-3b: same call **fails to compile**.

`experiments/per_core_sharding/CMakeLists.txt` defines 16 add_executable() targets including `test_oms`, `test_oms_concurrent`, `test_oms_phase04_06` — these would fail at compile if anyone runs the experiments cmake. The `test_event_log_head_to_head.cpp` was correctly updated in Phase 3b (commit message mentions it explicitly + grep verified at line 160).

**Impact:**

- **Zero impact on production verification:** `./build.sh test gui suite` does not touch `experiments/`. The experiments tree has its own CMakeLists. Tests in `tests/controller_test.cpp` (3052/3052 passing) cover the production path completely.
- **Operator-visible if experiments rebuilt:** If anyone runs `cmake -B experiments/per_core_sharding/build && cmake --build experiments/per_core_sharding/build`, 16-26 ish call sites fail to compile.
- **Documentation drift class:** These are historical phase-validation tests left in tree as reference. They were already partially outdated pre-3b (some signatures already broken since v5.15.5.C.2 OMS-state-flags bit-packing refactor — let me verify: pre-3b they DID work, post-3b they DON'T).

**Verifier:**
```bash
grep -n "OrderManager_Init" experiments/per_core_sharding/test_oms.cpp
# 9 matches; all 8 calls miss `partial_exit_enabled`
```

**Recommended fix:**

Three options:

**Option A — Update experiment callers (~30 min):** Mechanical sweep through 13 call sites adding `/*partial_exit_enabled=*/0,` at the 4th positional position. Aligns with the discipline of keeping all historical test fixtures buildable as documentation; matches what Phase 3b did for `test_event_log_head_to_head.cpp`.

**Option B — Provide `OrderManager_InitLegacy` shim (~10 min):** Add inline wrapper at OrderManager.hpp matching pre-3b signature, calling new Init with `partial_exit_enabled=0`. Allows experiments to compile unchanged. Caveat: introduces a "legacy" API path that should be deprecated at some future ship.

**Option C — Document deprecation (~5 min):** Add a TECH_DEBT entry noting that the pre-Phase-04 OMS experiments need a signature sweep to remain buildable. Defer until someone actually rebuilds them.

**Recommended:** Option A. Matches the discipline of `tests/controller_test.cpp:6067-19988` updates that Phase 3b already shipped (16 call sites updated). The experiments tree is small (13 sites) and is part of the historical narrative; keeping it buildable preserves documentation value. If Option A is bundled, the `event_log_mode=` arg position must also be updated (now 7th positional, was 6th positional pre-3b — verified `test_oms_phase04_06.cpp:41` uses named arg `/*event_log_mode=*/1` which is order-insensitive so OK).

**Cross-ref:** No PARITY-NNN allocation (not a production parity gap; tracked as TECH_DEBT candidate).

---

#### MEDIUM-2 — Round-trip persist test (controller_test.cpp:5443-5562) does NOT directly assert post-load values for 7 PERSIST-view fields

- **File:** `/home/caramel/code/FoxML_Trader_v2/tests/controller_test.cpp:5443-5562`
- **Severity:** MEDIUM (test coverage gap; wire-format byte preservation is still structurally guaranteed by canonical FOREACH row ordering, but a direct field-level assertion would catch a future row-reorder accidentally landing in the registry)
- **Class:** Test-coverage drift — registry consolidation expanded the set of fields routed through PERSIST view, but the round-trip test still only directly asserts 3 fields (balance, realized_pnl, kill_switch_tripped)

**Symptom:**

The Phase 3b commit moves the snapshot SAVE + LOAD lifecycle from explicit per-field calls to a 4-pass FOREACH walk:
```cpp
FOREACH_OMS_FIELD(OMS_PROJECT_PERSIST_SAVE)     // save
FOREACH_OMS_FIELD(OMS_PROJECT_PERSIST_DECLARE)  // load tmp decl
FOREACH_OMS_FIELD(OMS_PROJECT_PERSIST_READ)     // load fread
FOREACH_OMS_FIELD(OMS_PROJECT_PERSIST_COMMIT)   // load commit
```

The PERSIST view contains **10 rows** (in canonical wire order):
1. `balance` (FPN<F>)
2. `realized_pnl` (FPN<F>)
3. `ks_peak_balance` (FPN<F>)
4. `kill_switch_tripped` (int, BIT extraction)
5. `total_fees` (FPN<F>)
6. `total_maker_fees` (FPN<F>)
7. `total_taker_fees` (FPN<F>)
8. `maker_fills_count` (uint32_t)
9. `taker_fills_count` (uint32_t)
10. `paper_session_start_us` (uint64_t)

Round-trip test at `controller_test.cpp:5453-5562` directly asserts ONLY:
- `r2->state.oms->balance` (line 5509)
- `r2->state.oms->realized_pnl` (line 5511)
- `r2->state.oms->oms_state_flags` kill_switch_tripped bit (lines 5517-5519, 5531-5533)
- Per-core fields (entries_processed, core_realized, kill_tripped bit, regime, pnl_feeder, IC/RMSE buffers)

**Direct-assertion gap (7 fields):** ks_peak_balance, total_fees, total_maker_fees, total_taker_fees, maker_fills_count, taker_fills_count, paper_session_start_us.

**Indirect coverage exists:** If any of the 7 unasserted fields had wire-byte misalignment, the *subsequent* per-core block reads would land at wrong file positions → per-core assertions would fail. So the round-trip test DOES catch misordering via downstream byte-stream corruption. But:

1. **Misordering within the OMS block** (e.g., swapping `total_fees` and `total_maker_fees`) would NOT be caught — total bytes consumed unchanged, downstream per-core reads still align.
2. **Saved-only-zero values** (test does not set non-zero values for the 7 fields before save) means a "load reads zero for these fields" bug would pass the per-core checks AND the (incidentally-zero) field values.

**Impact:** Low today; high if a future addition to FOREACH_OMS_FIELD reorders the PERSIST rows. The canonical row-ordering convention in OmsFieldRegistry.hpp lines 184-189 is the load-bearing discipline; absent direct test, only `/parity-check` reads catch a violation.

**Reproducer:**
```bash
grep -nE "round-trip:.*(total_fees|total_maker|total_taker|maker_fills|taker_fills|paper_session|ks_peak)" tests/controller_test.cpp
# zero matches today
```

**Recommended fix:**

Bundle into a v5.15.5.C.3 follow-up sub-ship (no urgency):

```cpp
// Add to round-trip Test 2 (controller_test.cpp:5453-5562) before the save:
r->oms.ks_peak_balance     = FPN_FromDouble<64>(11500.00);
r->oms.total_fees          = FPN_FromDouble<64>(12.34);
r->oms.total_maker_fees    = FPN_FromDouble<64>(7.50);
r->oms.total_taker_fees    = FPN_FromDouble<64>(4.84);
r->oms.maker_fills_count   = 5;
r->oms.taker_fills_count   = 9;
r->oms.paper_session_start_us = 1700000000000000ULL;  // fixed wall-clock anchor

// Then after load:
check("round-trip: oms.ks_peak_balance restored",
      fabs(FPN_ToDouble(r2->state.oms->ks_peak_balance) - 11500.00) < 1e-6);
check("round-trip: oms.total_fees restored",
      fabs(FPN_ToDouble(r2->state.oms->total_fees) - 12.34) < 1e-6);
check("round-trip: oms.total_maker_fees restored",
      fabs(FPN_ToDouble(r2->state.oms->total_maker_fees) - 7.50) < 1e-6);
check("round-trip: oms.total_taker_fees restored",
      fabs(FPN_ToDouble(r2->state.oms->total_taker_fees) - 4.84) < 1e-6);
check("round-trip: oms.maker_fills_count restored",
      r2->state.oms->maker_fills_count == 5);
check("round-trip: oms.taker_fills_count restored",
      r2->state.oms->taker_fills_count == 9);
check("round-trip: oms.paper_session_start_us restored",
      r2->state.oms->paper_session_start_us == 1700000000000000ULL);
```

**Effort:** ~15 minutes; ~30 LOC added.

**Additional opportunity (LOW, deferred):** A compile-time `static_assert(_persist_row_count == 10)` would lock the PERSIST row count + force the next contributor to explicitly justify any change. This pairs with the existing `static_assert(FOREACH_OMS_FIELD_COUNT >= 30)` lock in OmsFieldRegistry.hpp:339. Defer or bundle with the test additions.

**Cross-ref:** CLAUDE.md item 15 (Parity-tested-by-construction). DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md. Not a PARITY-NNN allocation (pre-existing test gap, not a new bug class introduced by Phase 3b).

---

### LOW

#### LOW-1 — `cfg.oms_event_log_mode > 1` silently truncated to 2 bits by MULTI_BIT slot (pre-3b: stored raw uint32_t in int field)

- **File:** `/home/caramel/code/FoxML_Trader_v2/MemHeaders/BitmapMacros.hpp:236-239` (MBS_SET_U8 truncates value to slot width)
- **Severity:** LOW (no production caller passes value > 1; cfg parser at `ControllerConfig.hpp:2802` accepts arbitrary uint32 but defaults the cfg field; reserved modes 2-3 not yet defined as cfg-acceptable; modes 4+ would silently round to legacy=0 after 2-bit truncation)
- **Class:** Behavior change — pre-3b stored raw int, post-3b truncates to 2-bit slot

**Symptom:**

Pre-3b:
```cpp
oms->event_log_mode = event_log_mode;  // raw int store; arbitrary value preserved
```

Post-3b:
```cpp
MBS_SET_U8(oms->oms_state_flags, MASK_OMS_STATE_EVENT_LOG_MODE,
           SHIFT_OMS_STATE_EVENT_LOG_MODE, event_log_mode);
// expands to: clear slot bits, then (value & ((1<<2)-1)) << SHIFT_EVENT_LOG_MODE | (rest)
// → truncates value to 2 bits silently
```

If operator typos `oms_event_log_mode = 4` in engine.cfg:
- Pre-3b: stored as raw int 4; subsequent `event_log_mode == 1` checks return false; subsequent `event_log_mode == 0` checks also false → undefined-mode behavior (likely subset of mode-1 paths plus skipped paths).
- Post-3b: silently truncates to 4 & 0x3 = 0; engine runs in **legacy mode 0** without warning.

**Impact:**

- Zero today. No callsite passes anything outside {0, 1}.
- Mild behavioral regression vs pre-3b for operator-typo case (silent fallback to legacy vs surfacing as broken mode).

**Recommended fix (defensive):**

Either:

**Option A — Bounds-check at AUTOPOPULATE call site:**
```cpp
// In OrderManager_Init, before calling AUTOPOPULATE:
if (event_log_mode > 1) {
    std::fprintf(stderr, "[OMS] event_log_mode=%d > 1 invalid; clamping to 1\n", event_log_mode);
    event_log_mode = 1;
}
```

**Option B — Static enum check in cfg parser at `ControllerConfig.hpp:2802`:**
```cpp
cfg.oms_event_log_mode = (uint32_t)atoi(val);
if (cfg.oms_event_log_mode >= (1u << 2)) {  // BITS_OMS_STATE_EVENT_LOG_MODE
    std::fprintf(stderr, "[cfg] oms_event_log_mode=%u out of range [0,3]; resetting to 0\n",
                 cfg.oms_event_log_mode);
    cfg.oms_event_log_mode = 0;
}
```

**Option C — Defer (no action):** Document in TECH_DEBT, revisit if a 3rd or 4th event_log_mode value is ever added (would force the bounds check at that point anyway).

**Recommended:** Option C (defer). The silent-truncate-to-legacy is the safest fallback for operator typos in the current setup. When mode 2 or 3 is defined, bundle Option A + an enum-set test.

**Cross-ref:** Not a PARITY-NNN allocation (behavioral edge case, not a parity gap).

---

#### LOW-2 — No `static_assert` lock on PERSIST view row count (10 fields)

- **File:** `/home/caramel/code/FoxML_Trader_v2/MemHeaders/OmsFieldRegistry.hpp:339-347`
- **Severity:** LOW (defensive — current discipline relies on row ordering convention in the comment header)

**Symptom:**

`OmsFieldRegistry.hpp` has:
```cpp
static_assert(FOREACH_OMS_FIELD_COUNT >= 30,
              "FOREACH_OMS_FIELD must keep at least the v5.15.5.C.3 set "
              "(30+ scalar entries: substrate + 3 BIT/MULTI_BIT + HOT + 10 PERSIST wire + "
              "cfg-derived + observability masks + adapter + 5 atomics + 3 COLD). "
              "Removing entries requires explicit justification.");
```

But no separate count-lock for the PERSIST subset (10 rows). A future contributor could add a PERSIST row at any position (violating wire order) or remove a PERSIST row (silently changing wire format) without tripping a compile-time check. The legacy registry had implicit positional ordering via its 10-row hand-written shape; the new registry intersperses PERSIST rows with SKIP_PERSIST rows in groups.

**Recommended fix:**

Add a PERSIST-row counter macro:
```cpp
#define _OMS_PERSIST_COUNT_PERSIST(name, type, init, reset, rkind, skind, smask) +1
#define _OMS_PERSIST_COUNT_SKIP_PERSIST(name, type, init, reset, rkind, skind, smask) +0
#define _OMS_PERSIST_COUNT_ONE(name, type, init, reset, rkind, skind, pkind, smask) \
    _OMS_PERSIST_COUNT_##pkind(name, type, init, reset, rkind, skind, smask)
constexpr int FOREACH_OMS_PERSIST_FIELD_COUNT =
    0 FOREACH_OMS_FIELD(_OMS_PERSIST_COUNT_ONE);

static_assert(FOREACH_OMS_PERSIST_FIELD_COUNT == 10,
              "Snapshot v8 wire format locks 10 PERSIST rows. Adding/removing a PERSIST row "
              "REQUIRES bumping SHARDED_SNAPSHOT_VERSION and updating the load-side cross-version "
              "compatibility handling in ShardedSnapshot_Load.");
```

**Effort:** ~10 minutes; ~10 LOC added.

**Cross-ref:** CLAUDE.md item 15 (Parity-tested-by-construction). Pattern documented in `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md`.

---

### DOCUMENT-ONLY

#### DOC-1 — Multi-bit-state-encoding-pattern hits 2-application threshold (CLAUDE.md item candidate)

Phase 3b's Finding A' is the **2nd codebase application** of `DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md`:
1. v5.15.5.C.2.1 LOW-2 — `last_exit_predicted_meta[16]` (per-slot 8-bit slots with arm + regime + valid bits)
2. v5.15.5.C.3 Finding A' — `EVENT_LOG_MODE` 2-bit slot in `oms_state_flags`

Per CLAUDE.local.md going-forward rule (2026-05-09 "codify design principles in CLAUDE.md as patterns mature"), the pattern now qualifies for CLAUDE.md item promotion:
- ≥2 applications: ✓
- DESIGN_SPECS doc exists: ✓ (`multi-bit-state-encoding-pattern.md`)
- Pattern applies broadly: ✓ (per-record K-state field with packed slots; future candidates listed in design spec)

The commit message already calls this out:
> "Hits "2+ applications" threshold for promotion to CLAUDE.md item (per CLAUDE.local.md "codify design principles" rule 2026-05-13)."

This is **not a parity finding**; it's a documentation evolution gate. Audit notes it for the operator's sprint-close review queue (CLAUDE.md item proposal).

**Action:** Defer to operator review at next sprint close. Cross-ref CLAUDE.local.md going-forward rule "codify design principles" (2026-05-09).

---

## Cross-cutting concerns

### Wire format byte-preservation analysis

**Verified clean.** The canonical PERSIST view row order (positions 1-10) matches the legacy `FOREACH_OMS_PERSIST_FIELD` order byte-for-byte:

| Wire position | Field | Type | Bytes | Pre-3b registry | Post-3b registry row | Match? |
|---|---|---|---|---|---|---|
| 1 | balance | FPN<F> | sizeof(FPN<F>) | row 1 | line 244 PERSIST_DIRECT | ✓ |
| 2 | realized_pnl | FPN<F> | sizeof(FPN<F>) | row 2 | line 245 PERSIST_DIRECT | ✓ |
| 3 | ks_peak_balance | FPN<F> | sizeof(FPN<F>) | row 3 | line 247 PERSIST_DIRECT | ✓ |
| 4 | kill_switch_tripped | int | 4 | row 4 BIT | line 249 PERSIST_BIT | ✓ (still 4 bytes) |
| 5 | total_fees | FPN<F> | sizeof(FPN<F>) | row 5 | line 251 PERSIST_DIRECT | ✓ |
| 6 | total_maker_fees | FPN<F> | sizeof(FPN<F>) | row 6 | line 252 PERSIST_DIRECT | ✓ |
| 7 | total_taker_fees | FPN<F> | sizeof(FPN<F>) | row 7 | line 253 PERSIST_DIRECT | ✓ |
| 8 | maker_fills_count | uint32_t | 4 | row 8 | line 255 PERSIST_DIRECT | ✓ |
| 9 | taker_fills_count | uint32_t | 4 | row 9 | line 256 PERSIST_DIRECT | ✓ |
| 10 | paper_session_start_us | uint64_t | 8 | row 10 | line 258 PERSIST_DIRECT | ✓ |

**SAVE bytewise comparison (pre-3b vs post-3b):**

Pre-3b expansion:
```cpp
type _v = OMS_PERSIST_SAVE_VAL_DIRECT(name, mask);  // = state->oms->name
fwrite(&_v, sizeof(type), 1, f);
// for BIT: _v = (BITMAP_IS_SET(...) ? 1 : 0); fwrite(&_v, sizeof(int), 1, f)
```

Post-3b expansion (`OMS_PROJECT_PERSIST_SAVE_PERSIST_DIRECT`):
```cpp
type _v_save_##name = state->oms->name;
fwrite(&_v_save_##name, sizeof(type), 1, f);
// for BIT (OMS_PROJECT_PERSIST_SAVE_PERSIST_BIT):
type _v_save_##name = (BITMAP_IS_SET(...) ? (type)1 : (type)0);
fwrite(&_v_save_##name, sizeof(type), 1, f);
```

**Identical bytes emitted.** Cast `(int)1` is just `1` cast to int (no transformation). ✓

**LOAD bytewise comparison (pre-3b vs post-3b):**

Pre-3b:
```cpp
if (fread(&tmp_##name, sizeof(type), 1, f) != 1) { ... }
```

Post-3b (`OMS_PROJECT_PERSIST_READ_PERSIST_DIRECT` / `_BIT`):
```cpp
if (fread(&tmp_##name, sizeof(type), 1, f) != 1) { fclose(f); return 0; }
```

**Identical fread call.** ✓

**COMMIT bytewise behavior:**

Pre-3b BIT:
```cpp
if (tmp_##name) state->oms->oms_state_flags |= (uint8_t)tt::mask;
else            state->oms->oms_state_flags &= (uint8_t)~(uint8_t)tt::mask;
```

Post-3b `OMS_PROJECT_PERSIST_COMMIT_PERSIST_BIT`:
```cpp
if (tmp_##name) state->oms->oms_state_flags |= (uint8_t)(tt::smask);
else            state->oms->oms_state_flags &= (uint8_t)(~(uint8_t)(tt::smask));
```

**Identical.** ✓

Pre-3b DIRECT:
```cpp
state->oms->name = tmp_##name;
```

Post-3b `OMS_PROJECT_PERSIST_COMMIT_PERSIST_DIRECT`:
```cpp
state->oms->name = tmp_##name;
```

**Identical.** ✓

### `event_log_mode` int-field-removal: layout + downstream readers

**`OrderManagerState<F>` layout:** Pre-3b had `int event_log_mode` between `submit_queues[N]` (HOT cluster) and `event_log` (HOT cluster). Post-3b removes it. The 4-byte int + implicit 4-byte pad = 8 bytes saved per OMS. `oms_state_flags` (uint8_t + 7-byte explicit pad `_pad_osf[7]` = 8 bytes total) is in the COLD cluster — separately positioned via `alignas(64)` in `adapter` field, then `oms_state_flags` follows. The slot move does not shift any other field's offset; verified by:
- `static_assert(offsetof(OrderManagerState<64>, result_queue) % 64 == 0)` — unchanged
- `static_assert(offsetof(OrderManagerState<64>, portfolio) % 64 == 0)` — unchanged
- `static_assert(offsetof(OrderManagerState<64>, adapter) % 64 == 0)` — unchanged
- `static_assert(offsetof(OrderManagerState<64>, total_submitted) % 64 == 0)` — unchanged
- `static_assert(offsetof(OrderManagerState<64>, flatten_pending) % 64 == 0)` — unchanged
- `static_assert(offsetof(OrderManagerState<64>, ks_min_balance) % 8 == 0)` — unchanged
All cluster anchors hold.

**Reader migration (4 sites verified post-3b):**

1. `CoreFrameworks/OrderManager.hpp:733` — `BITMAP_NONE(oms->oms_state_flags, MASK_OMS_STATE_EVENT_LOG_MODE)`
   - Semantic: `(slot & mask) == 0` → slot value == 0 (legacy mode). **Equivalent to pre-3b `oms->event_log_mode == 0`.**
2. `CoreFrameworks/OrderManager.hpp:1244, 1260, 1291` — `MBS_EQ_U8(oms->oms_state_flags, MASK_OMS_STATE_EVENT_LOG_MODE, SHIFT_OMS_STATE_EVENT_LOG_MODE, 1)`
   - Semantic: slot value == 1. **Equivalent to pre-3b `oms->event_log_mode == 1`.**
3. `CoreFrameworks/ShardedBacktestDriver.hpp:235, 433` — `BITMAP_ANY(drv->oms->oms_state_flags, MASK_OMS_STATE_EVENT_LOG_MODE)`
   - Semantic: `(slot & mask) != 0` → slot value != 0. **Equivalent to pre-3b `drv->oms->event_log_mode != 0`.**
4. `experiments/per_core_sharding/test_event_log_head_to_head.cpp:86-87` — `MBS_EQ_U8(...)` mode=1 check. **Equivalent.**

**No dead-field accesses remain.** Grep `oms\.event_log_mode\|oms->event_log_mode` across entire codebase returns ZERO matches outside comment references.

### Engine/backtest parity for `partial_exit_enabled` derivation

Both callers derive the bit from the SAME cfg expression:

**`CoreFrameworks/EngineSharded.hpp:634-637`:**
```cpp
int partial_exit_enabled =
    BITMAP_IS_SET(cfg.lifecycle_cfg_flags, MASK_LIFECYCLE_CFG_PARTIAL_EXIT_ENABLED) ? 1 : 0;
OrderManager_Init(&oms, exchange_adapter, live_trading ? 1 : 0,
                  partial_exit_enabled, ...);
```

**`Backtest/BacktestSharded.hpp:181-183`:**
```cpp
int bt_partial_exit_enabled =
    BITMAP_IS_SET(cfg.lifecycle_cfg_flags, MASK_LIFECYCLE_CFG_PARTIAL_EXIT_ENABLED) ? 1 : 0;
OrderManager_Init(&oms, empty_adapter, 0, bt_partial_exit_enabled, ...);
```

Same cfg field + same mask + same ternary → identical value. **Train-serve parity verified.**

### Production-caller field-population audit (Section L)

OrderManager_Init is called by 4 PRODUCTION sites + 16 tests + 1 experiment. All updated to pass `partial_exit_enabled`:

| Caller | File | Line | partial_exit_enabled arg | Status |
|---|---|---|---|---|
| Live engine | `CoreFrameworks/EngineSharded.hpp` | 636 | `partial_exit_enabled` (derived from cfg) | ✓ |
| Backtest | `Backtest/BacktestSharded.hpp` | 183 | `bt_partial_exit_enabled` (derived from cfg) | ✓ |
| Test helper | `CoreFrameworks/ControllerEventLoop.hpp` | 857 | `0` (legacy default) | ✓ |
| Definition | `CoreFrameworks/OrderManager.hpp` | 670 | (function decl) | ✓ |
| controller_test (16 sites) | `tests/controller_test.cpp` | 6067, 6138, 6239, 6313, 6546, 7912, 8130, 9894, 15260, 18141, 18238, 18363, 18431, 18473, 18523, 18683 | various explicit values | ✓ all updated |
| Updated experiment | `experiments/per_core_sharding/test_event_log_head_to_head.cpp` | 160 | `0` | ✓ |
| Stale experiments | `experiments/per_core_sharding/test_oms*.cpp` | various | NOT updated → MEDIUM-1 | ✗ |

Phase 3b's commit message claims "~20 caller sites updated to pass the new arg" — verified for production + main tests; stale experiments (3 files, 13 call sites) NOT updated (MEDIUM-1 above).

### AUTOPOPULATE field-population invariant (CLAUDE.md item 21)

Per CLAUDE.md item 21, AUTOPOPULATE companion macros for X-macro registries should auto-generate per-field populator code so production callers can't drift. Verifier:

**OMS_INIT_AUTOPOPULATE call:**
```cpp
OMS_INIT_AUTOPOPULATE(oms, adapter, live_trading, partial_exit_enabled,
                      starting_balance, fee_rate, event_log_mode, event_log_path);
```

**Macro body** (verified at `MemHeaders/OmsFieldRegistry.hpp:639-702`):
- Layer 1: registry walk via `tt::_oms_init_value_fields<F>` (covers all 30+ scalar/BIT/MULTI_BIT/ATOMIC fields)
- Layer 2: Portfolio_Init + Order_Init loop + per-slot FOREACH walk + OMS_META_CLEAR
- Layer 3: SPSC ring inits (4 rings)
- Layer 4: OrderEventLog conditional init + LoadFromDisk + replay (gated on `event_log_mode == 1 && has_disk_path`)
- Layer 5: OrderEventLog_StartAsyncWriter

**Pre-3b → post-3b coverage check (40 fields/operations):**

Cross-checked each pre-3b init expression in the OrderManager_Init body against the post-3b registry + AUTOPOPULATE layers. ALL 40 ops have an equivalent in post-3b. No field-population gap. (See cross-check table in main audit body.)

### Pre-existing PARITY-NNN ledger sanity

Cross-referenced phase 3b's touched files (OmsFieldRegistry.hpp, OmsStateFlagRegistry.hpp, BitmapMacros.hpp, OrderManager.hpp, EngineSharded.hpp, BacktestSharded.hpp, ShardedSnapshotPersist.hpp, ControllerEventLoop.hpp, ShardedBacktestDriver.hpp, controller_test.cpp) against PARITY-001..024 in `DOCS/PARITY_ISSUES.md`:

- **No regressions:** None of PARITY-001..023 (already CLOSED or RESOLVED) reference any of the file:line citations touched by Phase 3b.
- **No DOCUMENTED-RISK collisions:** No documented-risk entries overlap with the surfaces.
- **PARITY-024 (OPEN HIGH for v5.15.5):** This audit is for v5.15.5.C.3 Phase 3b. PARITY-024 is for v5.15.5 broader scope (per-arm trained TP/SL barriers — not touched by Phase 3b). No interaction.

---

## Behavior matrix (train ↔ serve identity check, post-3b)

Phase 3b is structural / registry consolidation; no train-serve handoff surfaces touched. Verified by:

| Surface | Touched in 3b? | Same train + serve produces same bytes? | Notes |
|---|---|---|---|
| Features (FEATURE_REGISTRY_HASH) | No | N/A | ML headers untouched |
| Labels (label_kind body) | No | N/A | |
| Scaler binding | No | N/A | |
| Stamp body (model_const + cfg) | No | N/A | |
| inference_cfg_* cfg-bound fields | No | N/A | |
| ML build flags fingerprint | No | N/A | |
| Snapshot v8 wire bytes (OMS block) | YES (registry consolidation) | **YES — byte-preserved** | Verified above |
| Snapshot v8 wire bytes (per-core blocks) | NO | N/A | Untouched |
| Engine/backtest cfg derivation of partial_exit_enabled | NEW (Finding A) | **YES — same expression both sites** | Verified above |
| event_log_mode reader behavior | YES (int field → 2-bit slot) | **YES — semantic-equivalent everywhere** | 4 reader sites verified |

---

## Suggested ship sequence (per finding)

If the operator chooses to bundle the findings:

1. **`v5.15.5.C.3.x` — HIGH-1 close** (~10 min): delete BacktestSharded.hpp:194-201 stale mirror; update comment to point to OrderManager_Init's registry-driven set. Add a TECH_DEBT-013 increment counter (bitmap-flag-api running count).
2. **`v5.15.5.C.3.x.1` — MEDIUM-2 close** (~15 min): add 7 round-trip field assertions for ks_peak_balance + total_fees + total_maker/taker_fees + maker/taker_fills_count + paper_session_start_us at controller_test.cpp:5453-5562.
3. **`v5.15.5.C.3.x.2` — LOW-2 close** (~10 min): add PERSIST-row-count static_assert at OmsFieldRegistry.hpp.
4. **TECH_DEBT entry** for MEDIUM-1 stale experiments (~5 min): document the 13 call sites needing partial_exit_enabled, defer until experiments are rebuilt.
5. **LOW-1 deferred:** revisit if event_log_mode 2-3 added.
6. **DOC-1 deferred:** operator review at sprint close.

Estimated total: ~40 min for items 1-3 (closing HIGH-1 + MEDIUM-2 + LOW-2). Items 4-6 are docs/deferrals.

---

## NOT a bug (verified-safe items)

- **`event_log_mode` slot truncation to 2 bits** — no production caller passes value > 1; cfg parser at `ControllerConfig.hpp:2802` accepts arbitrary uint32 but default = 1; mode 0/1 fit cleanly. Truncation is silent for typos but operator-visible failure mode is acceptable (legacy fallback). Flagged as LOW-1 for documentation only.
- **`OmsInitCtx<F>` adapter as const ref** — adapter is copied into OMS struct at registry-walk site (DIRECT init: `_oms->adapter = (ExchangeAdapter<F>)(ctx.adapter)` performs struct copy). No reference-lifetime issue.
- **paper-reset's new DO_RESET coverage for `total_submitted/filled/rejected` atomics** — intentional behavior addition per commit message (v5.5.6 Class-5 recurring-bug close completion). No production reader exists outside the OrderManager_Total{Submitted,Filled,Rejected} accessor functions (which are not called from production GUI/engine paths; only from experiments/tests). Reset is safe + a parity improvement.
- **`oms_state_flags` substrate row at registry position 1** — explicit `_oms->oms_state_flags = 0` runs BEFORE BIT/MULTI_BIT rows. This is the load-bearing dependency for the BIT/MULTI_BIT writes to produce correct values regardless of OMS struct's prior memory state (stack-allocated uninit case). Comment in registry header lines 218-222 documents the dependency explicitly.
- **Per-arm reward observability invariant (CLAUDE.md item 24)** — Phase 3b does not touch any per-arm prediction grading or bandit update paths. Invariant unchanged.

---

## Auto-write contract — PARITY_ISSUES.md update

Per CLAUDE.local.md going-forward rule (2026-05-09 + 2026-05-12), HIGH-1 finding allocated as **PARITY-025** and auto-written to `DOCS/PARITY_ISSUES.md`. Format follows the existing entries (Found / Severity / Class / Site / Symptom / Root cause / Fix path / Target ship / Status: OPEN / Workaround).

MEDIUM-1, MEDIUM-2, LOW-1, LOW-2 NOT allocated PARITY-NNN (none are train↔serve parity gaps; they're scope items for follow-up sub-ships). MEDIUM-1 (stale experiments) is a TECH_DEBT candidate (recommended TECH_DEBT-XXX allocation). MEDIUM-2 + LOW-2 are bundled-fix candidates for v5.15.5.C.3 follow-up sub-ship.

---

## Summary

Phase 3b ships a clean structural consolidation: 8-tuple registry with 3-axis dispatch closes TECH_DEBT-012 (FOREACH_OMS_STATE registry — canonical multi-target dispatch). Wire format byte-preserved (verified row-by-row); template-helper dispatch per CLAUDE.md item 23 correctly compiles; production-caller class for `partial_exit_enabled` closed at EngineSharded; bit-packed COLD cluster saves 4 bytes via EVENT_LOG_MODE slot. Tests pass cleanly at 3052/3052.

**HIGH-1** (stale BacktestSharded mirror for PARTIAL_EXIT_ENABLED) is the only finding that needs follow-up before declaring Finding A fully closed; ~10 min effort. **MEDIUM-1** (stale experiments) is a documentation-only concern (experiments aren't part of `./build.sh test`). **MEDIUM-2** (round-trip test coverage gap) is bundled-fix material.

Net verdict: **GREEN to proceed with v5.15.5.C.3 Phase 4** (FOREACH_CORE_CTX_SUMMARY_FIELD + JSON emitter per bundled plan). HIGH-1 should bundle into the same sub-ship if Phase 4 touches any partials-related code; otherwise it can ride a dedicated cleanup sub-ship.
