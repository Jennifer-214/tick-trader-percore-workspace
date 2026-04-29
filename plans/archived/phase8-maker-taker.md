# Phase 8 — Maker/Taker Accounting + Partial-Fill State Machine

last updated: 2026-04-25 (evening — cross-plan amendments applied)

**Time budget:** 1-2 days
**Commits:** 7 (planned, was 6 — split tests into their own commit)
**Risk:** medium — touches OMS state machine + fee computation; backward compat critical

## Amendments applied 2026-04-25 evening

After cross-plan analysis vs. master plan errata + codebase spot-check + cache-alignment review:

1. **Commit 1: mixed-cfg warning** — when user sets `fee_rate=X` AND only one of `fee_rate_maker`/`fee_rate_taker`, the unset one silently keeps default (could be very wrong). Per master plan errata #6, log loud warning.
2. **Commit 1: fingerprint policy decision** — keep `Backtest/Fingerprint.hpp` reading legacy `fee_rate` only. Adding `fee_rate_maker`/`fee_rate_taker` to fingerprint would invalidate every saved model bundle. Document as a known limitation: backtest fingerprints don't distinguish maker/taker rates.
3. **Commit 2: `static_assert` on `Order` size** — adding `is_maker` (uint8_t) shifts struct layout. After the field add, `static_assert(sizeof(Order<F>) == EXPECTED_SIZE, ...)` turns silent ABI breakage into compile error. Verify OrderPool slot size assumption holds.
4. **Commit 4: ExitBuffer fee site** — original plan listed 6 fee math sites but missed `Portfolio.hpp::ExitBuffer_PendingProceeds` (called from `PortfolioController.hpp:823`). The exit buffer drains exits and computes proceeds = gross − fee. After this phase, exit fees should reflect `is_maker` of the exit fill. Likely needs `is_maker` on `ExitRecord`.
5. **Commit 4: document non-fee uses of `fee_rate`** — these sites use `fee_rate` as a quantity in pre-trade computations, NOT as a fee charge on a fill. Leave them as `fee_rate` (don't is_maker-aware them):
   - `PortfolioController.hpp:718-720` (no-trade band — gate threshold)
   - `PortfolioController.hpp:1178-1181` (fee floor for TP — pre-trade computation)
   - `PortfolioController.hpp:1418` (kill switch estimated_exit_fees — pre-trade estimate)
   - `PortfolioController.hpp:1611` (spread_bps display — pure display)
6. **Commit 5: counter field placement** — new `maker_fills_count`, `taker_fills_count`, `total_maker_fees`, `total_taker_fees` fields go at the **END** of `PortfolioController` struct, after all hot-path fields (`portfolio.active_bitmap`, `buying_halted`, `gate_offset`, etc.). Adding ~1KB (2× FPN<F=64>) in the middle could push hot-path fields off their cache line. Document the placement decision in the commit message.
7. **Commit 5: simplified snapshot rule** — only update `TUI_CopySnapshot()`, NOT `BacktestSnapshot_Copy`. CLAUDE.md "Snapshot sync rule (simplified 2026-04)" already documents that BacktestSnapshot is a thin wrapper that auto-syncs. Original plan over-specified.
8. **NEW commit 6: tests** — explicit commit for the test sidecar's 18-22 assertions. Split out from original commit 6 so production code lands first, then tests, then docs. Test Group 4 (backward compat) can land EARLY as part of commit 1 if cleaner.
9. **Commit 7 (was commit 6): docs + changelog** — unchanged scope, just renumbered.
10. **Phase 8 partial-fill recovery across crashes** (Tier 2 verification): if engine crashes with `ORDER_PARTIAL` in OMS memory, restart loses that state. Verify orphan recovery handles it during commit 4 implementation. Document the behavior in CLAUDE.md.

Original prose preserved below; corrections inline at relevant blocks. Commit numbering adjusted: 1→2→3→4→5→**6 (tests, NEW)**→**7 (docs, was 6)**.

## Context anchors — files to read FIRST

Before writing any code, read in order:

```
plans/live-readiness-master.md         ← orchestration + anti-drift discipline
DataStream/BinanceUserData.hpp                ← lines 290-353: executionReport parser
CoreFrameworks/Order.hpp                      ← Order struct + OrderState enum
CoreFrameworks/OrderManager.hpp               ← OMS state machine + fill handlers
DataStream/BinanceAdapter.hpp                 ← Command/FillResult struct
CoreFrameworks/ControllerConfig.hpp           ← fee_rate field, around line 60-90
CoreFrameworks/PortfolioController.hpp        ← lines 460-470, 1075-1090: fee math sites
CoreFrameworks/ControllerEventLoop.hpp        ← lines 397-433: entry/exit fee computation
CoreFrameworks/OrderEventLog.hpp              ← line 387-430: alternate fee site
CoreFrameworks/LegacyReferenceDriver.hpp      ← line 88, 149, 163: legacy fee site
DataStream/EngineTUI.hpp                      ← TUISnapshot (find existing fee field)
GUI/DashboardPanels.hpp                       ← Account panel (where new counters render)
DataStream/TUIAnsi.hpp                        ← ANSI Account section
```

Branch state expected: on `experiment/live-readiness`. `controller_test` baseline depends on phase ordering: 296/296 if Phase 8 runs first after 5d, higher if 8a/8b/6prep/7prep ran first (each adds tests).

## Failure mode IDs covered

From `live-readiness-master.md`:

- **Fee inaccuracy in live stats** — currently a single `fee_rate` (default 0.10%) is used for all trades. Maker fills on Binance are 25% cheaper (0.075% vs 0.10% on tier 0). Stats overstate fee burden on maker fills, understate on taker.
- **`ORDER_PARTIAL` is dead enum** — defined in Order.hpp:61 but no code transitions an order to this state. Real fills can be partial; pretending all fills are full is a correctness gap that will surface as confusion when partial fills land in production.
- **Fee model differs between live and backtest** — backtest assumes a single fee_rate. Phase 8 keeps that for backward compat (no drift) but documents the divergence.

## Status update

The `ORDER_PARTIAL` state was added to the enum during early OMS design but never wired. The Binance executionReport parser at `DataStream/BinanceUserData.hpp:310-353` extracts price/qty/exchange_id/trade_id but not `m` (isMaker), `n` (commission), or `X` (order status). The OMS fill path currently treats every CMD_WS_FILL as a terminal full-fill.

This phase wires both — and they're tightly coupled because partial-fill handling needs the maker flag too (otherwise we'd compute wrong fees on the partial portion).

## Commit plan (in order)

### Commit 1: Bifurcate `fee_rate` config (backward compat preserved)

**Goal:** add `fee_rate_maker` + `fee_rate_taker` config fields. If only legacy `fee_rate` is set in cfg, mirror it to both. New cfg can specify them independently.

**Files:**
- `CoreFrameworks/ControllerConfig.hpp` — struct + Default + parser

**Approach:**

1. Add fields after existing `fee_rate`:
   ```cpp
   FPN<F> fee_rate_maker;  // maker fill fee rate (e.g. 0.00075 = 0.075%)
   FPN<F> fee_rate_taker;  // taker fill fee rate (e.g. 0.00100 = 0.100%)
   ```

2. In `ControllerConfig_Default()`:
   ```cpp
   cfg.fee_rate_maker = FPN_FromDouble<F>(0.00075);  // Binance tier 0 BNB-discount
   cfg.fee_rate_taker = FPN_FromDouble<F>(0.00100);  // Binance tier 0 standard
   ```

3. Parser additions:
   ```cpp
   CFG_PARSE_PCT(fee_rate_maker)
   CFG_PARSE_PCT(fee_rate_taker)
   ```

4. **Backward compat + mixed-cfg warning** at end of `ControllerConfig_Load`, before the existing `min_warmup_samples` clamp (amendment #1):
   ```cpp
   // Backward compat: if user specified only legacy fee_rate, mirror to both.
   FPN<F> default_maker = FPN_FromDouble<F>(0.00075);
   FPN<F> default_taker = FPN_FromDouble<F>(0.00100);
   int maker_at_default = FPN_Equal(cfg.fee_rate_maker, default_maker);
   int taker_at_default = FPN_Equal(cfg.fee_rate_taker, default_taker);
   int legacy_set       = !FPN_IsZero(cfg.fee_rate);

   if (maker_at_default && taker_at_default && legacy_set) {
       // Legacy mode: only fee_rate set, mirror to both.
       cfg.fee_rate_maker = cfg.fee_rate;
       cfg.fee_rate_taker = cfg.fee_rate;
       fprintf(stderr, "[CFG] fee_rate=%.5f → mirrored to maker+taker (legacy mode)\n",
               FPN_ToDouble(cfg.fee_rate));
   } else if (legacy_set && (maker_at_default ^ taker_at_default)) {
       // Mixed-cfg WARNING: user set fee_rate AND exactly one of maker/taker.
       // The other one stays at default — likely user error.
       fprintf(stderr,
               "[CFG] WARNING: fee_rate=%.5f set, but only one of "
               "fee_rate_maker (%.5f) / fee_rate_taker (%.5f) explicitly set. "
               "The other stays at its default. If you meant to set both, "
               "explicitly set both. If you meant legacy mode, remove the "
               "explicitly-set one.\n",
               FPN_ToDouble(cfg.fee_rate),
               FPN_ToDouble(cfg.fee_rate_maker),
               FPN_ToDouble(cfg.fee_rate_taker));
   }
   ```

5. **Fingerprint policy** (amendment #2): in `Backtest/Fingerprint.hpp`, the existing fingerprint computation continues to read **only `fee_rate`** (the legacy field), not `fee_rate_maker`/`fee_rate_taker`. This preserves bundle compatibility — pre-Phase-8 saved models still match their fingerprints. Document the limitation with a comment at the fingerprint computation site:
   ```cpp
   // NOTE (Phase 8): fee_rate_maker / fee_rate_taker are NOT included in the
   // fingerprint. Two cfgs with same fee_rate but different maker/taker rates
   // will produce identical fingerprints. This is intentional — including them
   // would invalidate every saved model bundle. Live fee accounting still uses
   // the per-rate fields (correctness preserved); reproducibility just doesn't
   // distinguish them.
   ```

**Anti-drift checks:**
- [ ] Existing cfg files (with only `fee_rate=0.10`) load without warnings beyond the new mirroring info line
- [ ] Default values match Binance tier 0 BNB-discount (0.075% / 0.100%)
- [ ] `controller_test` passes — fee math sites still work (they read `fee_rate` directly until commit 4)

**Testing:** unit test cfg load with old + new formats. Verify cfg → struct values match expected.

### Commit 2: Add `is_maker` to Order + Command/FillResult

**Goal:** plumb the maker flag from Binance fill event through OMS into Order.

**Files:**
- `CoreFrameworks/Order.hpp` — Order struct
- `DataStream/BinanceAdapter.hpp` — FillResult / Command struct (find the queue message type)

**Approach:**

1. **`Order` struct** (after existing `_pad[6]`):
   ```cpp
   uint8_t is_maker;        // 1 if this order's fills were maker-side, 0 if taker
                            // populated from Binance executionReport "m" field
                            // valid only when state == ORDER_FILLED or ORDER_PARTIAL
   uint8_t _pad2[7];        // adjust _pad sizing as needed for FPN alignment
   ```

2. Update `Order_Init` to set `is_maker = 0` and document that it's set later from fill events.

3. **`FillResult` (or whatever the CMD_WS_FILL payload struct is called)**:
   ```cpp
   uint8_t is_maker;        // mirrors Binance executionReport "m" boolean
   uint8_t order_complete;  // 1 if "X" == "FILLED", 0 if "X" == "PARTIALLY_FILLED"
   double commission;       // Binance "n" field (commission paid this fill, in commission_asset units)
   char commission_asset[8]; // "BNB", "USDT", etc — Binance "N" field
   ```

**Anti-drift checks:**
- [ ] Order struct size growth is acceptable (verify cache line alignment isn't broken — Order should still pack into the existing `OrderPool` slots)
- [ ] FillResult size doesn't break the SPSC queue's slot size assumptions (check `BinanceAdapter.hpp` for queue declaration)
- [ ] Existing `Order_Init` callers don't need updates (new field zero-init is safe default)
- [ ] **Add `static_assert(sizeof(Order<F>) == EXPECTED_SIZE, "ABI break")` (amendment #3)** — capture the post-amendment size as a constant, the static_assert turns silent breakage into a compile error if anyone changes Order layout.

**Testing:** Static asserts on struct sizes (per amendment #3). Run `controller_test` to confirm.

### Commit 3: Extend Binance executionReport parser

**Goal:** extract `m` (isMaker), `n` (commission), `N` (commission_asset), `X` (order status) from the JSON event.

**File:** `DataStream/BinanceUserData.hpp` — `ud_parse_execution_report` function (lines 310-353)

**Approach:**

1. Add JSON field extractions (the existing `binance_json_extract_*` helpers handle the parsing):
   ```cpp
   // isMaker: "m" → boolean (true / false)
   char m_str[8] = {};
   binance_json_extract_str(json, "m", m_str, sizeof(m_str));
   int is_maker = (m_str[0] == 't' || m_str[0] == 'T') ? 1 : 0;

   // order status: "X" → string
   char order_status[24] = {};
   binance_json_extract_str(json, "X", order_status, sizeof(order_status));
   int order_complete = (strcmp(order_status, "FILLED") == 0) ? 1 : 0;

   // commission: "n" → double, "N" → string
   double commission = binance_json_extract_double(json, "n");
   char comm_asset[8] = {};
   binance_json_extract_str(json, "N", comm_asset, sizeof(comm_asset));
   ```

2. Populate the new FillResult fields in `cmd_out`:
   ```cpp
   cmd_out->result.is_maker        = (uint8_t)is_maker;
   cmd_out->result.order_complete  = (uint8_t)order_complete;
   cmd_out->result.commission      = commission;
   strncpy(cmd_out->result.commission_asset, comm_asset,
           sizeof(cmd_out->result.commission_asset) - 1);
   ```

**Anti-drift checks:**
- [ ] If `m` is missing from a fill event (shouldn't be, but defensive), `is_maker` defaults to 0 (assume taker — conservative, slightly overstates fees)
- [ ] If `X` is missing, `order_complete` defaults to 0 (assume partial — keeps order alive, won't lose track)
- [ ] Existing fields (price, qty, exchange_id, trade_id) still extracted correctly

**Testing:** unit test with a real Binance executionReport JSON sample (capture one from testnet). Verify all fields parse.

### Commit 4: OMS fill handler — wire ORDER_PARTIAL state + maker fee

**Goal:** when a fill event arrives, route it correctly through the state machine and apply maker vs taker fee.

**File:** `CoreFrameworks/OrderManager.hpp` — `OrderManager_OnFill` (or whatever the handler is called)

**Approach:**

1. In the fill handler, find the existing logic that updates `Order.filled_qty`, `Order.avg_fill_price`, and transitions to `ORDER_FILLED`. Replace with:
   ```cpp
   // Update running fill totals (already correct for partials)
   FPN<F> new_filled = FPN_AddSat(order->filled_qty,
                                   FPN_FromDouble<F>(fill->fill_qty));
   // Volume-weighted avg price
   // ... [existing weighted average logic, unchanged]

   // Set or accumulate is_maker (current Binance design: all fills of one
   // order have same maker status; if mixed, use last fill's flag)
   order->is_maker = fill->is_maker;

   // Choose terminal vs partial state
   if (fill->order_complete) {
       order->state = ORDER_FILLED;
   } else {
       order->state = ORDER_PARTIAL;
   }

   order->last_update_us = now_us();
   ```

2. Maker fee application — find every site that computes fees as `FPN_Mul(notional, fee_rate)`. Replace with helper:

   New helper in `CoreFrameworks/ControllerConfig.hpp` or a new `Fee.hpp`:
   ```cpp
   template <unsigned F>
   inline FPN<F> Fee_Compute(const ControllerConfig<F>* cfg, FPN<F> notional, int is_maker) {
       FPN<F> rate = is_maker ? cfg->fee_rate_maker : cfg->fee_rate_taker;
       return FPN_Mul(notional, rate);
   }
   ```

   Then update sites (amendment #4: `ExitBuffer_PendingProceeds` added):
   - `PortfolioController.hpp:467` (exit fee — direct site) ✓ verified
   - `PortfolioController.hpp:1079` (entry fee — direct site) ✓ verified
   - `ControllerEventLoop.hpp:399` (entry fee) ✓ verified
   - `ControllerEventLoop.hpp:432` (exit fee) ✓ verified
   - `OrderEventLog.hpp:420, 430`
   - `LegacyReferenceDriver.hpp:149, 163`
   - **`Portfolio.hpp::ExitBuffer_PendingProceeds`** (amendment #4) — called from `PortfolioController.hpp:823` to compute pending proceeds. Currently takes `fee_rate` as a parameter. Will need to take `is_maker` per-record OR have `is_maker` stored on `ExitRecord`. Likely the latter: add `uint8_t is_maker` to `ExitRecord` (set when the exit fill arrives), then `ExitBuffer_PendingProceeds` uses `Fee_Compute(cfg, gross, record->is_maker)` per record.

   For each: take the order's `is_maker` from the matching fill (entry fee uses entry order's flag, exit fee uses exit order's flag).

3. **Sites that use `fee_rate` but are NOT fee charges** (amendment #5) — leave these as `fee_rate`, do NOT make them is_maker-aware. They're using `fee_rate` as a quantity in pre-trade computations (gates, breakeven thresholds, displays):
   - `PortfolioController.hpp:718-720` (no-trade band — gate threshold uses `fee_rate * no_trade_band_mult`)
   - `PortfolioController.hpp:1178-1181` (fee floor for TP — pre-trade `entry × fee_rate × fee_floor_mult`)
   - `PortfolioController.hpp:1418` (kill switch `estimated_exit_fees` — pre-trade estimate)
   - `PortfolioController.hpp:1611` (spread_bps display — pure display)

   Why leave them: these computations happen pre-fill (don't know is_maker yet) OR are aggregate estimates where average `fee_rate` is the right model. Document at each site with a one-line comment: `// Phase 8: pre-trade quantity, not a fee charge — uses single fee_rate intentionally`.

4. **Backtest path**: in `Backtest_Run`, fills are simulated at tick price with no maker/taker concept. Always pass `is_maker=0` (assume taker). Document this in `BacktestEngine.hpp` near the fill-simulation site.

5. **Crash recovery for ORDER_PARTIAL** (amendment #10 — Tier 2 verification): if engine crashes with an `ORDER_PARTIAL` order in OMS memory, restart loses it. Verify orphan recovery (existing mechanism in `main.cpp`) handles the case where exchange shows partial fill but engine has no record. May need to fetch order state from Binance on startup and reconcile. Document the recovery behavior in CLAUDE.md.

**Anti-drift checks:**
- [ ] Backtest results numerically unchanged when cfg has `fee_rate_maker == fee_rate_taker == fee_rate` (legacy mode)
- [ ] No existing test (controller_test) regresses
- [ ] `ORDER_PARTIAL` orders are NOT removed from `OrderPool` until they hit terminal state (verify `Order_IsTerminal` still treats PARTIAL as non-terminal — it does per line 132)

**Testing:**
- `controller_test` passes (baseline depends on phase ordering — see "Branch state expected" above)
- Manual: backtest with explicit cfg `fee_rate_maker=fee_rate_taker=fee_rate` — stats identical to before
- Manual: backtest with different rates — stats reflect taker (since backtest fills are all taker)

### Commit 5: Maker/taker counters + accounting in PortfolioController

**Goal:** track per-fill-type counts and fee totals. Surface in stats.

**File:** `CoreFrameworks/PortfolioController.hpp` — controller struct + fill handler

**Approach:**

1. Add fields to `PortfolioController` struct (warm path, not hot) — **placement at END of struct (amendment #6)**:
   ```cpp
   // ... [existing hot-path fields: portfolio, buying_halted, gate_offset, etc.] ...
   // ... [existing warm-path fields: balance, total_fees, peak_equity, etc.] ...

   // PHASE 8 (2026-04-XX): maker/taker accounting fields.
   // PLACED AT END OF STRUCT — adding ~1KB (2× FPN<F=64>) earlier could push
   // hot-path fields off their cache line. Verify with offsetof if needed.
   uint32_t maker_fills_count;
   uint32_t taker_fills_count;
   FPN<F> total_maker_fees;
   FPN<F> total_taker_fees;
   ```

2. In `PortfolioController_Init`, zero these.

3. In the fill consumption path (where exits/entries are credited to the controller), increment the appropriate counter and add to the appropriate fee total:
   ```cpp
   if (order->is_maker) {
       ctrl->maker_fills_count++;
       ctrl->total_maker_fees = FPN_AddSat(ctrl->total_maker_fees, fee);
   } else {
       ctrl->taker_fills_count++;
       ctrl->total_taker_fees = FPN_AddSat(ctrl->total_taker_fees, fee);
   }
   ```

4. Existing `total_fees` field continues to receive the sum of both (for backward compat with any code reading it).

5. **Snapshot + display** (amendment #7: simplified snapshot rule — only `TUI_CopySnapshot` needs updating):
   - `DataStream/EngineTUI.hpp` — add `maker_fills`, `taker_fills`, `maker_fees`, `taker_fees` to `TUISnapshot`. Update `TUI_CopySnapshot()`.
   - **`Backtest/BacktestSnapshot.hpp`** — **NO CHANGES NEEDED.** It's a thin wrapper around `TUI_CopySnapshot`; new fields auto-sync. Per CLAUDE.md "Snapshot sync rule (simplified 2026-04)".
   - `DataStream/TUIAnsi.hpp` — display in Account section.
   - `GUI/DashboardPanels.hpp` — display in Account panel with maker fill rate %.

**Anti-drift checks:**
- [ ] `total_fees` continues to equal `total_maker_fees + total_taker_fees` (sanity invariant)
- [ ] Snapshot sync: only `TUI_CopySnapshot` updated. Backtest auto-syncs via thin wrapper. Verify with grep: `BacktestSnapshot_Copy` in code is still a one-line wrapper.
- [ ] Display panels handle the case where both counters are 0 (no fills yet) gracefully
- [ ] **Field placement (amendment #6)**: new fields are at END of `PortfolioController` struct. Verify with `offsetof` that hot-path field offsets haven't shifted (e.g., `offsetof(PortfolioController<F>, portfolio.active_bitmap)` should be unchanged from pre-Phase-8).

**Testing:** Manual TUI inspection after a backtest run (will show 0 makers in pure backtest mode). Live testnet verifies real maker tagging.

### Commit 6: Tests (NEW per amendment #8)

**Goal:** all 18-22 assertions from `phase8-maker-taker-tests.md` land here as a single commit, AFTER all production code (commits 1-5) is in place.

**Exception:** Group 4 (backward compat — legacy `fee_rate` mirroring) MAY land EARLY as part of commit 1 to anchor the legacy path before later commits risk breaking it. Decide at implementation: if commit 1 already has good test coverage from existing 5d regression tests, keep all of Group 4 here. Otherwise split.

**File:** `tests/controller_test.cpp` — append new section at end (same pattern as 5d regression tests).

**Verification:** `controller_test` goes from 296 → ~328 assertions, 0 failed.

### Commit 7: Documentation + changelog (was Commit 6)

**Goal:** record the phase + capture the new invariants in CLAUDE.md.

**Files:**
- `DOCS/changelogs/2026-04-XX-phase8-maker-taker.md` — new dated changelog
- `CLAUDE.md` — add a "Maker/Taker Accounting" subsection under Safety Invariants
- `plans/live-readiness-master.md` — mark Phase 8 done

**CLAUDE.md additions:**

Under Safety Invariants:

```markdown
### Maker/Taker Fee Accuracy

When applying fees in any code path:
1. Use `Fee_Compute(cfg, notional, is_maker)` helper (or its inline equivalent), never raw `FPN_Mul(notional, fee_rate)`
2. Source `is_maker` from the order that produced the fill, not from a heuristic
3. In backtest, fills are simulated as taker (`is_maker=0`) — documented divergence from live
4. Sanity check: `total_fees == total_maker_fees + total_taker_fees` after every fill
```

## Verification (after EACH commit)

```bash
cmake --build build -j$(nproc)
cmake --build build_gui -j$(nproc)
build/controller_test                      # passes (baseline varies by phase ordering)
```

Plus the anti-drift checks listed per commit.

## Verification (after ALL 6 commits)

Manual end-to-end on testnet:

1. Set `use_testnet=1` in cfg; configure testnet API key
2. Set `fee_rate_maker=0.00075`, `fee_rate_taker=0.00100`
3. Run engine, let it submit a few orders
4. Inspect Account panel: maker_fills_count + taker_fills_count > 0
5. Verify `total_maker_fees + total_taker_fees ≈ total_fees`
6. Capture a real Binance executionReport from logs; verify `m` field parses correctly

Backtest sanity:

1. With `fee_rate_maker == fee_rate_taker`, stats should be identical to pre-Phase-8 baseline
2. With different rates, all fills tagged as taker (since backtest doesn't simulate maker)

## Definition of done

- [ ] All 7 commits land cleanly on `experiment/live-readiness` (amended commit count)
- [ ] 296/296 tests pass after commits 1-5; 296+~32 = ~328 after commit 6 tests
- [ ] Manual testnet verification passes (1 hour of unattended runtime, real Binance fills)
- [ ] No new compile warnings
- [ ] `static_assert(sizeof(Order<F>))` passes (amendment #3)
- [ ] CLAUDE.md updated with Maker/Taker Accuracy invariant + ORDER_PARTIAL recovery behavior (amendment #10)
- [ ] Phase 6 master plan marked Phase 8 done

## Tag at end of Phase 8

```bash
git tag phase8-complete
```

This anchors the start of Phase 8a/8b parallel work or Phase 9 sequential work.

## Known limitations / deferred

- **Backtest simulation of maker fills**: deferred to Phase 9. Phase 8's backtest assumes all-taker. This is a known divergence (live can outperform backtest if maker fills happen, which is the safe direction).
- **Mixed-maker-status partial fills**: in theory possible if a single order's partial fills change maker status (e.g., the order moves between maker and taker book sides). Phase 8 uses the last fill's flag for the whole order. Documented limitation.
- **Commission asset accounting**: Phase 8 records the commission amount + asset but doesn't convert across assets. If user pays fees in BNB instead of the trading pair currency, fee totals are in mixed units. Phase 8b (operational monitoring) can flag this; full unit-converting accounting is a future phase.
