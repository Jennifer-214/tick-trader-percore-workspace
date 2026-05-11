# /trace-deps report — v5.14.7-maker-order-mvp — 2026-05-08

**Verdict:** **YELLOW** (3 BLOCKING fixes, all small-scope)

## Summary
- NEW functions analyzed: 5
- Callees verified: 12+
- PASS: 10
- GAP: 2
- DRIFT: 0

## Gaps (BLOCKING — must update plan before coding)

### 1. `BinanceAdapter_CancelOrder` does not exist

`DataStream/BinanceOrderAPI.hpp` has MARKET submit functions
(`BinanceOrderAPI_MarketBuy` at :503, `BinanceOrderAPI_MarketSell`
at :549) but NO cancel (DELETE) endpoint. Plan Step 4 calls this
function in `OMS_CheckStaleLimits`.

**Fix:** Implement `BinanceOrderAPI_CancelOrder` via DELETE
`/api/v3/order` endpoint (Binance standard). Pattern exists in
`binance_signed_request` for `method="DELETE"`. Effort: ~30 min.

### 2. `Order<F>` struct extension needed

Plan references `o->cancel_after_us`, `o->submit_us`,
`o->limit_price`, `o->is_post_only` — none of these exist in
current Order struct (Order.hpp:70-109).

**Fix:** Update plan's Step 1 to explicitly list 4 new Order
fields + update Order_Init to zero-init + update `sizeof(Order<64>)`
static_assert (currently 280).

### 3. `OMS_CancelAndReplace` referenced but undefined

Plan title/abstract mentions cancel-and-replace but Step 4 only
shows `OMS_CheckStaleLimits` calling cancel + (optional) market
fallback. No `OMS_CancelAndReplace` function actually defined.

**Fix:** Either remove "OMS_CancelAndReplace" from plan body
(current implementation in Step 4 is sufficient — cancel + fall
back to MARKET via `OMS_PushSubmit`) OR add explicit pseudo-code.

## Clarifications (YELLOW)

### 4. Slow-path book_snapshot wiring

Plan Step 3 assumes `book_snapshot_valid` + access to
`book_snap.best_bid`/`best_ask` in slow-path-to-submit code path.
Need to specify whether passed as parameter (via ControllerEventLoop
context) or read from global `DepthSharedState` /
`DepthReplayState`.

`BookSnapshot` struct exists at `DataStream/BinanceDepth.hpp:29`
with `bids[5]`, `asks[5]`, `spread`, `mid_price`. Best bid/ask
accessed via `bids[0].price` / `asks[0].price` (top-of-book).

**Fix:** Plan Step 3 update to clarify wiring + best_bid/ask
accessor pattern.

### 5. BinanceAdapter function naming

Plan says `BinanceAdapter_SubmitLimitBuy` — should this wrap a
new `BinanceOrderAPI_LimitBuy` or extend existing MarketBuy with
type override? Pattern: separate function paralleling MarketBuy
is cleaner.

## REUSE Verification (all PASS)

| Claim | Location | Status |
|---|---|---|
| `OrderType` ORDER_LIMIT_BUY=2 / ORDER_LIMIT_SELL=3 | Order.hpp:50-55 | PASS |
| `Order.type` field | Order.hpp:75 | PASS |
| `Order.is_maker` field | Order.hpp:94-98 | PASS |
| `fee_rate_maker` | OrderManager.hpp:205 | PASS |
| `BookSnapshot<F>` | BinanceDepth.hpp:29 | PASS (top-of-book via bids[0]/asks[0]) |
| `DepthReplayState` | DepthReplayState.hpp:51 | PASS (current.BookSnapshot field) |
| `OMS_PushSubmit` signature | OrderManager.hpp:754 | PASS (8 params, defaults handle plan's call) |
| `OrderManager_HandleFill` is_maker fee selection | OrderManager.hpp:838 | PASS |

## Recommendations

**Update plan before coding:**
1. Add `BinanceOrderAPI_CancelOrder` to "TRULY NEW" section
2. List 4 Order struct fields explicitly in Step 1
3. Remove or define `OMS_CancelAndReplace`
4. Clarify slow-path book_snapshot wiring + best_bid/ask accessor

**Then re-run /trace-deps to confirm GREEN.**
