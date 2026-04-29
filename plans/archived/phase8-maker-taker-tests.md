# Phase 8 Tests — Maker/Taker + ORDER_PARTIAL state machine

last updated: 2026-04-25

**Sidecar to:** `plans/phase8-maker-taker.md`
**Time budget:** ~half day on top of Phase 8 implementation
**Test target:** `tests/controller_test.cpp` extension + new `tests/oms_state_test.cpp` if scope warrants
**Coverage goal:** 18-22 new assertions

## Why a sidecar

Phase 8 implementation is 6 commits across multiple files. Pinning the test work in its own document means:
- Tests are written deliberately, not "we'll get to them"
- Each test maps to a specific commit's anti-drift check
- The Phase 8 plan stays focused on production code; tests live alongside

## Sequencing

Tests run **as a final commit in the Phase 8 series**, after all production code is in place. Reasons:
- Tests reference all the new types + helpers, which only exist after commits 1-5
- Running tests during in-progress phases produces churn (test gets rewritten as the production code evolves)

The exception: backward-compat tests (Group 4 below) can land EARLY (after commit 1) to lock the legacy fee_rate path before the rest of the work risks breaking it.

## Test groups (ordered by Phase 8 commit they validate)

### Group 1: Fee_Compute helper (validates Phase 8 commit 4)

```cpp
// maker rate selected when is_maker=1
{
    ControllerConfig<BACKTEST_FP> cfg = ControllerConfig_Default<BACKTEST_FP>();
    cfg.fee_rate_maker = FPN_FromDouble<BACKTEST_FP>(0.00075);
    cfg.fee_rate_taker = FPN_FromDouble<BACKTEST_FP>(0.00100);
    FPN<BACKTEST_FP> notional = FPN_FromDouble<BACKTEST_FP>(1000.0);
    FPN<BACKTEST_FP> fee_maker = Fee_Compute(&cfg, notional, /*is_maker=*/1);
    FPN<BACKTEST_FP> fee_taker = Fee_Compute(&cfg, notional, /*is_maker=*/0);
    ASSERT_NEAR(FPN_ToDouble(fee_maker), 0.75, 1e-4);  // 1000 * 0.075% = $0.75
    ASSERT_NEAR(FPN_ToDouble(fee_taker), 1.00, 1e-4);  // 1000 * 0.100% = $1.00
}
```

**~3 assertions**

### Group 2: OMS state transitions (validates Phase 8 commit 4)

This is the load-bearing test class. The new ORDER_PARTIAL state has consequences for slot lifetime + accounting; these tests pin them down.

```cpp
// PENDING → ACK → PARTIAL → PARTIAL → FILLED
{
    Order<BACKTEST_FP> o;
    Order_Init(&o, 1, /*core_id=*/0, ORDER_TYPE_MARKET);
    o.requested_qty = FPN_FromDouble<BACKTEST_FP>(1.0);
    ASSERT_EQ(o.state, ORDER_PENDING);

    // Simulate ACK
    o.state = ORDER_ACKNOWLEDGED;
    ASSERT_EQ(Order_IsTerminal(&o), 0);

    // First partial fill (0.4 of 1.0)
    OrderManager_OnFill(&oms, &o, /*qty=*/0.4, /*price=*/100.0,
                       /*is_maker=*/1, /*order_complete=*/0);
    ASSERT_EQ(o.state, ORDER_PARTIAL);
    ASSERT_NEAR(FPN_ToDouble(o.filled_qty), 0.4, 1e-6);
    ASSERT_EQ(Order_IsTerminal(&o), 0);

    // Second partial fill (0.3 more, total 0.7)
    OrderManager_OnFill(&oms, &o, /*qty=*/0.3, /*price=*/100.5,
                       /*is_maker=*/1, /*order_complete=*/0);
    ASSERT_EQ(o.state, ORDER_PARTIAL);
    ASSERT_NEAR(FPN_ToDouble(o.filled_qty), 0.7, 1e-6);

    // Final fill (0.3 more, complete)
    OrderManager_OnFill(&oms, &o, /*qty=*/0.3, /*price=*/100.8,
                       /*is_maker=*/1, /*order_complete=*/1);
    ASSERT_EQ(o.state, ORDER_FILLED);
    ASSERT_NEAR(FPN_ToDouble(o.filled_qty), 1.0, 1e-6);
    ASSERT_EQ(Order_IsTerminal(&o), 1);
    // avg fill price weighted across partials
    // 0.4*100.0 + 0.3*100.5 + 0.3*100.8 = 40 + 30.15 + 30.24 = 100.39
    ASSERT_NEAR(FPN_ToDouble(o.avg_fill_price), 100.39, 0.01);
}

// Order pool slot stays allocated while PARTIAL, freed on FILLED
{
    OrderPool<BACKTEST_FP> pool;
    OrderPool_init(&pool, 16);
    int slot = OrderPool_alloc(&pool);
    ASSERT_GTE(slot, 0);

    pool.orders[slot].state = ORDER_PARTIAL;
    OrderPool_maybe_free(&pool, slot);  // helper that frees terminal-state orders
    ASSERT_EQ(pool.orders[slot].state, ORDER_PARTIAL);  // still allocated

    pool.orders[slot].state = ORDER_FILLED;
    OrderPool_maybe_free(&pool, slot);
    // slot should now be available for re-allocation
    int slot2 = OrderPool_alloc(&pool);
    ASSERT_EQ(slot2, slot);
}
```

**~8-10 assertions**

### Group 3: is_maker propagation (validates Phase 8 commits 2-3)

```cpp
// Binance executionReport with m=true → Order.is_maker=1
{
    const char json[] = "{"
        "\"e\":\"executionReport\","
        "\"x\":\"TRADE\","
        "\"X\":\"FILLED\","
        "\"c\":\"oms_42\","
        "\"i\":\"99\","
        "\"L\":\"60100.5\","
        "\"l\":\"0.001\","
        "\"m\":true,"
        "\"n\":\"0.045\","
        "\"N\":\"USDT\","
        "\"t\":12345,"
        "\"T\":1234567890123"
        "}";
    Command cmd;
    uint64_t trade_id;
    int is_fill = ud_parse_execution_report(json, sizeof(json) - 1, &cmd, &trade_id);
    ASSERT_EQ(is_fill, 1);
    ASSERT_EQ(cmd.type, CMD_WS_FILL);
    ASSERT_EQ(cmd.order_id, 42u);
    ASSERT_EQ(cmd.result.is_maker, 1);
    ASSERT_EQ(cmd.result.order_complete, 1);
    ASSERT_NEAR(cmd.result.avg_fill_price, 60100.5, 1e-3);
    ASSERT_NEAR(cmd.result.fill_qty, 0.001, 1e-6);
    ASSERT_NEAR(cmd.result.commission, 0.045, 1e-4);
}

// "m":false → is_maker=0
// "X":"PARTIALLY_FILLED" → order_complete=0
// missing "m" → is_maker=0 (defensive default)
```

**~6-8 assertions across 3 sub-cases**

### Group 4: Backward compat — single fee_rate path (validates Phase 8 commit 1)

This group can land **early** to anchor the legacy path before later commits risk breaking it.

```cpp
// Old cfg with only fee_rate set: maker and taker mirror it
{
    char path[] = "/tmp/test_cfg_XXXXXX";
    int fd = mkstemp(path);
    dprintf(fd, "fee_rate=0.10\n");  // legacy 0.10% format
    close(fd);
    auto cfg = ControllerConfig_Load<BACKTEST_FP>(path);
    ASSERT_NEAR(FPN_ToDouble(cfg.fee_rate),       0.001, 1e-6);
    ASSERT_NEAR(FPN_ToDouble(cfg.fee_rate_maker), 0.001, 1e-6);
    ASSERT_NEAR(FPN_ToDouble(cfg.fee_rate_taker), 0.001, 1e-6);
    unlink(path);
}

// New cfg with all three set: each is independent
{
    char path[] = "/tmp/test_cfg_XXXXXX";
    int fd = mkstemp(path);
    dprintf(fd, "fee_rate=0.10\nfee_rate_maker=0.075\nfee_rate_taker=0.100\n");
    close(fd);
    auto cfg = ControllerConfig_Load<BACKTEST_FP>(path);
    ASSERT_NEAR(FPN_ToDouble(cfg.fee_rate_maker), 0.00075, 1e-7);
    ASSERT_NEAR(FPN_ToDouble(cfg.fee_rate_taker), 0.00100, 1e-7);
    unlink(path);
}

// Mixed cfg (only fee_rate + fee_rate_maker, taker missing): warn, taker gets default
{
    // user error case — verify it doesn't silently corrupt
    // expected behavior: taker stays at default (0.001), warning printed
    // verify cfg.fee_rate_taker == default
}
```

**~6 assertions**

### Group 5: Maker/taker accounting invariant (validates Phase 8 commit 5)

```cpp
// total_fees == total_maker_fees + total_taker_fees after every fill
{
    PortfolioController<BACKTEST_FP> ctrl;
    PortfolioController_Init(&ctrl, ControllerConfig_Default<BACKTEST_FP>());
    ASSERT_EQ(ctrl.maker_fills_count, 0u);
    ASSERT_EQ(ctrl.taker_fills_count, 0u);
    ASSERT_NEAR(FPN_ToDouble(ctrl.total_fees), 0.0, 1e-9);

    // Simulate 3 fills: 2 maker, 1 taker (use the helper that handles fill bookkeeping)
    // After each fill, invariant must hold:
    // ctrl.total_fees == ctrl.total_maker_fees + ctrl.total_taker_fees

    // ... [fill simulation calls]

    ASSERT_NEAR(FPN_ToDouble(ctrl.total_fees),
                FPN_ToDouble(ctrl.total_maker_fees) + FPN_ToDouble(ctrl.total_taker_fees),
                1e-6);
    ASSERT_EQ(ctrl.maker_fills_count + ctrl.taker_fills_count, 3u);
}
```

**~3 assertions**

### Group 6: Snapshot sync (validates Phase 8 commit 5)

```cpp
// TUISnapshot has all 4 new fields populated
{
    PortfolioController<BACKTEST_FP> ctrl;
    PortfolioController_Init(&ctrl, ControllerConfig_Default<BACKTEST_FP>());
    ctrl.maker_fills_count = 3;
    ctrl.taker_fills_count = 7;
    ctrl.total_maker_fees  = FPN_FromDouble<BACKTEST_FP>(0.5);
    ctrl.total_taker_fees  = FPN_FromDouble<BACKTEST_FP>(2.0);

    TUISnapshot snap;
    TUI_CopySnapshot(&snap, &ctrl, /*price=*/60000.0, /*volume=*/0.0);
    ASSERT_EQ(snap.maker_fills_count, 3u);
    ASSERT_EQ(snap.taker_fills_count, 7u);
    ASSERT_NEAR(snap.total_maker_fees, 0.5, 1e-6);
    ASSERT_NEAR(snap.total_taker_fees, 2.0, 1e-6);
}

// BacktestSnapshot_Copy populates the same fields (sync rule check)
{
    PortfolioController<BACKTEST_FP> ctrl;
    PortfolioController_Init(&ctrl, ControllerConfig_Default<BACKTEST_FP>());
    ctrl.maker_fills_count = 1;
    ctrl.taker_fills_count = 4;

    TUISnapshot snap;
    BacktestSnapshot_Copy(&snap, &ctrl, /*last_price=*/60000.0, /*last_volume=*/0.0);
    ASSERT_EQ(snap.maker_fills_count, 1u);  // load-bearing — proves both copy paths sync
    ASSERT_EQ(snap.taker_fills_count, 4u);
}
```

**~6 assertions**

## Total: 18-22 assertions

Breakdown:
- Group 1 (Fee_Compute): 3
- Group 2 (OMS state): 8-10
- Group 3 (is_maker propagation): 6-8
- Group 4 (Backward compat): 6
- Group 5 (Accounting invariant): 3
- Group 6 (Snapshot sync): 6

**Range:** 32-36, depending on edge cases. The plan's stated range (18-22) was conservative; full coverage is closer to 32. Updating the master plan estimate.

## Verification

After Phase 8 commits 1-5 land + this test commit:

```bash
cmake --build build -j$(nproc)
build/controller_test
```

Expected: 296 (after Phase 5d regression tests) + ~32 = **~328 assertions, 0 failed**.

## Definition of done

- [ ] All test groups land as a single commit at the end of Phase 8 (or Group 4 lands early after commit 1 if that's cleaner)
- [ ] All assertions pass on first commit
- [ ] Run controller_test 3 times — no flakiness (especially Group 2's OMS state tests)
- [ ] Test names are descriptive — when one fails, the failure message names the bug class (not just "ORDER state mismatch")

## Test stubs that intentionally remain TODO

These are tests the plan says should exist but are deferred because they require infrastructure not yet built:

- **Maker fill simulation in backtest** — Phase 8 keeps backtest as all-taker. When Phase 9 ships hybrid execution + backtest sim of limit fills, add a test that verifies maker fills produce maker-rate fees in backtest.
- **Real Binance executionReport corpus** — Group 3 uses a hand-crafted JSON. Could be strengthened with captured real-event corpus from testnet. Defer until testnet recording infrastructure exists.
- **Stress test for partial fill accumulation** — fire 10,000 partial fills on one order, verify fee totals remain consistent. Useful for catching FPN saturation issues. Defer unless real Binance behavior shows long fill chains.

## Anti-drift contract for future Phase 8 changes

If anyone later modifies the OMS state machine, the fee math, or the snapshot fields, **these tests must still pass without modification**. If a test breaks because of a "legitimate" semantic change, that's a signal to write a NEW test for the new semantic AND keep the old test (mark it as "deprecated, removed when X").

The tests are guards against drift, not specs to update casually.
