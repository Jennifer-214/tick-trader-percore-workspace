# /trace-deps report — v5.14.4 multi-mode reconciliation — 2026-05-08

**Verdict:** **RED** (initial) → addressable with 2 plan-level fixes

## 2 BLOCKING gaps

### GAP-1: `BinanceOrderAPI_CancelOrder` does NOT exist

Plan Step 4 (`Reconcile_AutoCancelStale`) calls a non-existent function.
Grep confirms `BinanceOrderAPI.hpp` has `_GetOpenOrders`, `_GetMyTrades`,
`_GetBalances`, `_MarketBuy`, `_MarketSell` but NO `_CancelOrder`.
Even existing `EngineSharded.hpp:1305` comment acknowledges:
*"Requires BinanceOrderAPI_CancelOrder...that don't exist yet."*

**Cross-ship coordination:** v5.14.7 ALSO claims to add
`BinanceOrderAPI_CancelOrder`. Master plan ordering: Phase 2
(v5.14.4) ships before Phase 3 (v5.14.7) → v5.14.4 creates the
cancel API as Phase 0 sub-tag; v5.14.7 reuses.

**Resolution:** Add v5.14.4.0 sub-tag (~70 LOC) BEFORE v5.14.4.A:
- Implement `BinanceOrderAPI_CancelOrder(api, symbol, client_id)`
- Pattern mirrors `_MarketBuy` / `_MarketSell` at :503 / :549
- Uses existing `binance_signed_request` (BinanceOrderAPI.hpp:395)
  with `method="DELETE"` (line 297 comment confirms support)

### GAP-2: `OrderManagerState.last_seen_trade_id` does NOT exist

Plan Step 3 (`Reconcile_ApplyMissedFills`) reads
`oms->last_seen_trade_id` for resume-tracking. Field doesn't exist
on `OrderManagerState` struct.

**Resolution:** Add v5.14.4.0 sub-tag also includes:
- `uint64_t last_seen_trade_id` field on OrderManagerState
- Init to 0 in `OrderManager_Init`
- Update after each `ApplyMissedFills` (sets to highest trade_id replayed)

## Verified existing skeletons (PASS)

| Claim | Location verified | Status |
|---|---|---|
| `ReconcileResult` struct | Reconcile.hpp:69 | PASS |
| `ReconcileOpenOrder` struct | :47 | PASS |
| `ReconcileTrade` struct | :58 | PASS |
| `Reconcile_ParseOpenOrders` | :188 | PASS |
| `Reconcile_ParseMyTrades` | :221 | PASS |
| Phase 2 deferred comment | :22 (operator's past-self breadcrumb) | PASS |
| `cfg.reconcile_dry_run` (current binary) | ControllerConfig.hpp parser :1912-1913 | PASS |
| `OrderManager_HandleFill` (existing replay path) | OrderManager.hpp:838 | PASS |
| Boot reconcile site | EngineSharded.hpp:1294-1350 | PASS |

## Per-fn analysis

### `Reconcile_ApplyMissedFills` (NEW)
- Callees: `Order_Init` (PASS), `OrderManager_HandleFill` (PASS),
  `OrderManagerState` struct (PASS if GAP-2 fixed), `ReconcileTrade`
  struct (PASS)
- Verdict: PASS callees IF GAP-2 resolved

### `Reconcile_AutoCancelStale` (NEW)
- Requires: `BinanceOrderAPI_CancelOrder` (BLOCKED on GAP-1)
- `ReconcileOpenOrder` struct (PASS)
- Verdict: BLOCKED on GAP-1

## YELLOW (cfg back-compat)

Plan claims shim for old `reconcile_dry_run` → new `ReconcileMode`
enum. ControllerConfig.hpp parser :1912-1913 handles old field.
Verify it can parse both old + new field names simultaneously.
Review in v5.14.4.A.

## Effort summary

- Original plan: v5.14.4.A (~80 LOC), .B (~150), .C (~180) = ~410 LOC
- Pre-req additions: v5.14.4.0 BinanceOrderAPI_CancelOrder + last_seen_trade_id (~80 LOC)
- Total: +80 LOC; contained in one sub-ship

## Recommendations

1. **PLAN UPDATE NEEDED:** Add v5.14.4.0 sub-tag explicitly listing:
   - `BinanceOrderAPI_CancelOrder` impl (~70 LOC)
   - `OrderManagerState.last_seen_trade_id` field (~10 LOC)
2. Mark v5.14.4.0 as PHASE 0 (must complete before .A/.B/.C)
3. v5.14.7 plan UPDATE: remove `BinanceOrderAPI_CancelOrder` from
   its NEW claims list; reference v5.14.4.0 as already-shipped
   predecessor

## Verdict: **RED → fixable with v5.14.4.0 sub-tag addition**

After plan updates: GREEN. Re-run /trace-deps.
