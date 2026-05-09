# /trace-deps RERUN — v5.14.7 Maker MVP — 2026-05-08

**Verdict:** **GREEN on plan clarity; CODE NOT YET WRITTEN (expected)**

## Audit context note

This rerun is a PRE-CODING audit. The first round (verdict YELLOW)
flagged real plan gaps:
1. `BinanceOrderAPI_CancelOrder` not in TRULY NEW list
2. Order struct field extensions not enumerated
3. `OMS_CancelAndReplace` referenced but undefined

All 3 plan-clarity gaps are now CLOSED. The agent re-audit
correctly verified:
- All REUSE callees exist + signatures match
- Plan now explicitly lists 7 NEW functions
- Plan now explicitly enumerates 4 Order struct fields
- Plan now explicitly enumerates 5 NEW cfg fields
- Slow-path book_snapshot wiring uses correct accessor pattern
  (`bids[0].price` / `asks[0].price`; index-0 = top-of-book)

## What the agent flagged as "GAP" but isn't

The agent (Haiku 4.5) rendered the verdict as YELLOW/RED because
it found the new struct fields + functions not present in the
codebase. **That's the expected state** — we're pre-coding. The
plan's "NEW claims" section explicitly says these will be added.

The /trace-deps skill spec is ambiguous about pre-coding vs
post-coding evaluation. Agent's own bottom-line note:

> "If pre-coding, verdict is GREEN on PLAN CLARITY but RED on
> CODE READINESS."

For our purposes (pre-coding plan validation), the relevant verdict
is GREEN on plan clarity.

## REUSE verification (PASS)

| Claim | Location | Status |
|---|---|---|
| `binance_signed_request` (DELETE method support) | BinanceOrderAPI.hpp:395 | PASS |
| `binance_retry_request` | BinanceOrderAPI.hpp:417 | PASS |
| `OMS_PushSubmit` | OrderManager.hpp:754 | PASS |
| `BinanceOrderAPI_MarketBuy` / `_MarketSell` | BinanceOrderAPI.hpp:503, 549 | PASS (pattern to mirror) |
| `BinanceAdapter_SubmitMarketBuy` / `_SubmitMarketSell` | BinanceAdapter.hpp:330, 350 | PASS (wrapper pattern) |
| `Order_Init` | Order.hpp:119 | PASS (will extend for new fields) |
| `BookSnapshot.bids[0].price` / `asks[0].price` | BinanceDepth.hpp:24-41 | PASS (top-of-book canonical) |
| FPN primitives (`FPN_Zero`, `FPN_Sub`, `FPN_Add`, `FPN_Mul`) | FixedPoint/ | PASS |

## NEW additions (correctly enumerated in plan)

| Item | Type | Status |
|---|---|---|
| `BinanceOrderAPI_LimitBuy` | NEW fn | Plan describes; not yet coded |
| `BinanceOrderAPI_LimitSell` | NEW fn | Plan describes; not yet coded |
| `BinanceOrderAPI_CancelOrder` | NEW fn | Plan describes; not yet coded |
| `BinanceAdapter_SubmitLimitBuy` | NEW adapter wrapper | Plan describes; not yet coded |
| `BinanceAdapter_SubmitLimitSell` | NEW adapter wrapper | Plan describes; not yet coded |
| `BinanceAdapter_CancelOrder` | NEW adapter wrapper | Plan describes; not yet coded |
| `OMS_CheckStaleLimits` | NEW drainer fn | Plan describes; not yet coded |
| `Order.limit_price` | NEW field | Plan describes; not yet coded |
| `Order.submit_us` | NEW field | Plan describes; not yet coded |
| `Order.cancel_after_us` | NEW field | Plan describes; not yet coded |
| `Order.is_post_only` | NEW field | Plan describes; not yet coded |
| `SubmitCommand.limit_price` | NEW field | Plan describes; not yet coded |
| 5 cfg fields | NEW | Plan describes; not yet coded |

## Sprint readiness verdict

**Plan is ready to code.** Re-running /trace-deps post-coding
(after v5.14.7 sub-tags ship) will verify the actual code matches
the plan's NEW claims.

## Action item: improve /trace-deps skill spec

Add explicit pre-coding vs post-coding mode flag (or single-mode
that handles both correctly). Current spec defaults to "is code
there?" which is the wrong question pre-coding.

**Fix in next /trace-deps update:** distinguish:
- PRE-CODING mode: verify plan's REUSE claims exist + plan's NEW
  claims are coherent (signatures, dependencies)
- POST-CODING mode: verify plan's NEW claims got actually
  implemented + REUSE claims still exist + signatures unchanged

For now: this rerun = GREEN (plan clarity); awaiting v5.14.8
rerun.
