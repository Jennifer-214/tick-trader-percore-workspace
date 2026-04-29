# Future Directions — Captured 2026-04-29

These are real architectural questions that came up but are NOT
near-term priorities. Captured here so we don't have to re-derive the
analysis when they resurface.

## 1. Multi-exchange support (IBKR, Alpaca, others)

### Current state

The codebase already has the abstraction: `OrderManager_Init` takes
`ExchangeAdapter<F>` as a template parameter. Today it's only filled by
Binance's REST + WS code (`CoreFrameworks/BinanceAdapter.hpp`,
`DataStream/BinanceCrypto.hpp`, `DataStream/BinanceDepth.hpp`).

What's missing: alternate-exchange implementations of the adapter
interface.

### The pattern when we get to it

```cpp
template <unsigned F>
struct ExchangeAdapter {
    void (*submit_market_buy)(const SubmitContext<F>*);
    void (*submit_market_sell)(const SubmitContext<F>*);
    void (*fetch_account)(AccountSnapshot<F>*);
    void (*fetch_open_orders)(OpenOrderList<F>*);
    void (*fetch_recent_trades)(TradeList<F>*);
    // ... ~10 hooks total
};
```

Per-exchange adapters fill the function pointers:
- `BinanceAdapter` (current)
- `AlpacaAdapter` (TODO)
- `IBKRAdapter` (TODO — different shape, uses TWS gateway not REST)

Cfg: `exchange=binance|alpaca|ibkr` + `<exchange>_api_key=` (or
account/password for IBKR). **Always explicit, never auto-detect** —
API key prefixes don't reliably encode exchange identity (Binance is
64-char alphanumeric; Alpaca uses UUID-style; IBKR doesn't even use
API keys).

### Cost

Each new exchange ≈ **1-2 weeks** of careful work:
- Different REST schemas (account, order, trade endpoints)
- Different auth flows (HMAC-SHA256 for Binance vs OAuth for Alpaca)
- Different WS subscription protocols + message formats
- Different fill event payloads (`is_maker` field exists on Binance,
  may need synthesis on others)
- Different fee models (per-trade tier on Binance vs flat on Alpaca)
- Different time-in-force options
- Different rate limit semantics

The adapter interface itself is the easy part (~1 day). The
implementations are where the time goes.

### When to revisit

Not until you've **banked alpha on Binance live**. Multi-exchange is
optimization for portability — useless until you have something worth
porting. After a quarter of profitable live BTCUSDT, IBKR (for equity
universes) or Alpaca (for paper-trading US stocks) become real options.

### Public release angle

The current v5.x architecture is **Binance-only with a clean adapter
interface**. The interface itself is public — anyone who wants to add
Alpaca support gets a contract to fill, not a tangled dependency to
unwind. That's the right shape for OSS without overpromising.

---

## 2. API key UI + secrets handling

### Current state

`secrets.cfg` is the convention (gitignored, alongside `engine.cfg`).
Engine reads at boot. No GUI input — you edit the file by hand.

### The cleanup

- Add password-style input field in `GUI/SettingsPanel.hpp`
- Mask display (show `••••••••` when populated)
- Save writes to `secrets.cfg` (encrypted? probably overkill — file is
  already gitignored + permissions-700)
- Engine continues to read `secrets.cfg` at boot

### Cost

1-2h. Trivial. Should land alongside live exchange reconciliation in
v5.2.x since reconciliation is the work that actually USES the key.

### What NOT to do

- **Don't reach for keychain/keyring/Vault** — overkill for a single-user
  trading rig
- **Don't add encryption at rest unless adding multi-user** — the
  permissions+gitignored posture is fine for solo
- **Don't environment-variable it** as primary — `engine_gui` GUI session
  doesn't get them naturally; cfg file is the right primary

### When to revisit

Land alongside `2026-04-29-live-reconciliation.md` Phase 1.

---

## 3. Multi-interval support (tick → 1m / 5m / 1h bars)

### Current state

Engine consumes per-trade ticks (raw Binance trade events). The
`CandleAccumulator` reconstructs 1m bars **for the GUI chart only** —
it does not feed strategies. Strategies operate on `RollingStats`
windows that are **count-based** (every N ticks), not time-based (every
N minutes).

### What "trade on 1m bars" would require

Not a config tweak — a different operational mode:

1. New event type: `BarEvent` with OHLCV — fed to the engine instead of
   raw `Tick`.
2. Hot path consumes BarEvent. The 30-50ns design is *pointless* at
   1-minute cadence — the architecture is over-engineered for slow bars.
3. Strategies adapt: SimpleDip's "recent_high" is now a bar high, not a
   tick max. EMA Cross uses bar closes. Etc.
4. RollingStats windows become bar-count-based (e.g. "20 bars") instead
   of tick-count-based.
5. Slow path cadence changes from "every poll_interval ticks" to
   "every bar".

### Cost

3-5 days of careful work. Most of it is strategy adaptation + verifying
that the gate/exit semantics still make sense at slower cadence.

### When to revisit

Probably **never** for this engine. Reasoning:
- Most edge in BTCUSDT lives at **sub-second** timescales (HFT-pattern
  market making, latency arb on micro-moves, etc.). Bar trading drops
  into a much more competitive timeframe (everyone with a Python script
  is doing 1m bar momentum).
- The architecture's *real* value is the sub-second hot path. Bar
  trading throws that away — at which point you'd be better off
  using a different framework (vectorbt, backtesting.py, freqtrade)
  that's designed for that timeframe.
- If you find a strategy that genuinely wants 1m bars, write a
  separate, simpler engine for it. Don't retrofit this one.

### Edge case worth considering

**Hybrid mode**: tick-driven engine but with a "minimum hold time"
filter that prevents fills from re-entering within N seconds. Catches
"trade pattern is bar-like but execution is tick-like" use cases
without rewriting. Already partially exists via `min_spacing_ticks`.

---

## Decision matrix (when to revisit each)

| Item | Trigger to revisit |
|---|---|
| Multi-exchange | After 1 quarter of profitable BTCUSDT live |
| API key UI | When live exchange reconciliation Phase 1 ships |
| Multi-interval bars | Probably never — write a separate engine if needed |

## What lives in this doc

Not a TODO list. **Architectural reads** I want preserved so future-me
doesn't have to re-derive whether multi-exchange is worth it (no, not
yet) or whether bar trading would be a quick add (no, fundamental).
