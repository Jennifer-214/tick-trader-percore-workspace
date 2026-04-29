# Live Exchange Reconciliation — Plan (2026-04-29)

## Why this matters

The engine paper-trades cleanly: fills are simulated, the local view of
"my positions" is the source of truth, snapshot persistence handles
restart-while-position-open. Going live introduces an **external source
of truth** (Binance's actual fill state) that the engine can drift from:

- Engine submits BUY → network drops → local says "order pending" but
  exchange may have filled it. On restart, engine doesn't know it owns 0.01 BTC.
- Engine submits SELL → exchange fills → engine crashes before
  HandleFill processes the result → local still says "open position",
  exchange has flat position → next tick triggers a phantom SG → another
  SELL fires → unintended SHORT.
- Partial fill (`ORDER_PARTIAL`) on entry → engine crashes mid-fill →
  local quantity is wrong on restart.
- Manual order cancel via Binance UI → engine doesn't know.

These don't matter for paper. They matter the moment real money is in play.

## Scope

Reconciliation = "on engine startup AND on every WS reconnect, ask the
exchange what's actually true and patch the local view."

Does NOT cover:
- Live order submission correctness (BinanceOrderAPI exists, assume it works)
- Slippage / fill quality (separate concern)
- Multi-account / sub-account support (out of scope)

## Phase 1: Boot reconciliation (~1h)

When `engine_mode=live` (real exchange) at startup, BEFORE accepting any
ticks for trading:

1. Call REST `GET /api/v3/account` → fetch USDT balance + BTC balance.
   - Compare to snapshot: if balance differs by > 0.001 BTC or > $1
     USDT, log WARNING and use exchange truth (snapshot loses).
2. Call REST `GET /api/v3/openOrders?symbol=BTCUSDT` → list of orders
   currently live on exchange.
   - For each open order: was it submitted by us? (Use `clientOrderId`
     prefixed `tt-{symbol}-{seq}` so we can recognize ours).
   - Cancel any of OUR orders that are still open (pre-shutdown
     leftovers should not auto-resume).
3. Call REST `GET /api/v3/myTrades?symbol=BTCUSDT&limit=100` → recent
   fills.
   - For each fill since last snapshot's `last_processed_trade_id`,
     synthesize a `Command::CMD_REST_FILL` and process via
     `OrderManager_ProcessFillCommand`. This catches fills the WS missed.
4. Reconcile local position state:
   - If exchange says BTC > 0 but local says 0 positions: log CRITICAL,
     refuse to boot (manual intervention required — could be testnet
     residue, real position, or accounting bug).
   - If local says position open but exchange BTC = 0: stale local
     snapshot, force-close the local slot (no fill simulated, just
     bookkeeping).
   - If both agree: proceed.

### Acceptance
Engine boots cleanly when exchange + local agree. Logs a warning + uses
exchange truth when they disagree. Refuses to boot in CRITICAL cases.

## Phase 2: WS reconnect reconciliation (~1h)

Binance trade WS / userData WS connections drop occasionally
(scheduled maintenance, network blip, stream lag). On reconnect:

1. Re-fetch open orders + recent fills via REST (same as Phase 1).
2. Compare REST-recent-fills to OMS `last_fill[]` records — any fills
   in REST that aren't in our local processed list = process via
   `OrderManager_ProcessFillCommand` to catch up.
3. Log: `[reconcile] WS reconnect: replayed N missed fills`.

### Acceptance
A simulated 30-second WS dropout that includes a fill: engine catches
the fill on reconnect, no double-process if the fill ALSO arrives via
re-subscribed WS (use Binance's trade ID for dedup).

## Phase 3: Heartbeat reconciliation (~30 min, optional)

Every M minutes (cfg `reconcile_interval_sec`, default 300), poll REST
even when WS is healthy. Catches silent fills — fills that exchange
applied but never sent via WS due to bugs on their side or ours.

- Cheap: 1 REST call / 5 min, plenty of rate limit headroom.
- Belt-and-suspenders for high-stakes runs.

Cfg toggle to disable (default off; enable when running with real money).

## Phase 4: Manual cancel detection (~30 min)

If exchange `openOrders` shows an order canceled (state=CANCELED) that
we believe is still active, mark our local order as REJECTED with reason
`"manual_cancel_via_exchange"`. Don't retry (user intervened
intentionally).

## Files touched

- `CoreFrameworks/BinanceOrderAPI.hpp` — REST helpers for `account`,
  `openOrders`, `myTrades` (probably already exists; verify)
- `CoreFrameworks/OrderManager.hpp` — `OrderManager_Reconcile()` entry
  point; `last_processed_trade_id` field on state
- `main.cpp` (live path) — call reconcile at boot before
  accepting ticks
- `DataStream/BinanceCrypto.hpp` — call reconcile on WS reconnect
- `engine.cfg.example` — `reconcile_interval_sec` default
- `tests/controller_test.cpp` — mock exchange responses + assertions
  on Reconcile behavior (8-12 new tests)

## Versioning

- v5.2.0 — Phase 1 (boot reconcile) — minor bump (live behavior changes)
- v5.2.1 — Phase 2 (WS reconnect)
- v5.2.2 — Phase 3 + 4

Phase 1 is the must-have before going live. 2-4 are quality improvements.

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Reconcile triggers on testnet residue and force-closes legit positions | Add `reconcile_dry_run=1` cfg for first deploy — log what would change without applying |
| REST rate limits | 4 calls per reconcile × every 5min = 48/hour, well under 1200/min limit |
| Snapshot vs exchange disagreement is the engine's bug, not exchange's | CRITICAL log + refuse boot until investigated; never silently overwrite |
| `clientOrderId` collisions across restarts | Include UNIX timestamp in id seed |

## Rollback story

Tag `pre-reconcile`. If reconcile causes problems on first live deploy,
boot with `engine_mode=paper` to bypass while debugging. Reconcile is
LIVE-only by design.

## Out of scope

- Multi-symbol reconciliation (single-symbol BTCUSDT only)
- Cross-exchange (only Binance)
- Settlement-currency (only USDT-quoted pairs)
- Fee tier rebates / rebate accounting (Binance handles this; we just
  trust the fee field on the fill)
