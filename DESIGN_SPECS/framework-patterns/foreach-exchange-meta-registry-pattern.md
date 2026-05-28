---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.1
canonical_applications:
  - v5.15.5.F.4d.1.E.1 (Binance first canonical row)
  - v5.15.5.F.4d.1.E.6 (framework genericity validation; operator-triggered specific exchange adds = Stage 4 promotion when 2nd canonical lands)
sister_specs:
  - framework-patterns/x-macro-registry-with-presence-dispatch.md (parent pattern)
  - framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md (H15 enrollment)
  - framework-patterns/foreach-subaccount-meta-registry-pattern.md (sister at sub-account scope)
  - framework-patterns/exchange-adapter-tt-dispatch-pattern.md (consumer of this registry)
  - framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md (H18 customization)
  - framework-patterns/per-cluster-shared-resource-pattern.md (per-exchange shared resources)
tags: [framework-discipline, multi-exchange-substrate, x-macro-registry, meta-registry]
surface: [registry, exchange-adapters, per-cluster-resources]
applies_at_skills: [/precoding-audit-gate, /dod-audit, /registry-fit-audit]
---

# FOREACH_EXCHANGE meta-registry pattern

**Pattern intent:** Codify ALL supported exchanges as X-macro registry rows. Each row carries metadata columns (subaccount support; rate budget; market hours kind; adapter type; submit protocol). Adding a new exchange = 1 row + 1 adapter library; entire framework auto-flows.

## Problem statement

Multi-exchange trading engine needs:
- Per-exchange adapter (REST/WS-API/FIX/etc.)
- Per-exchange rate budget
- Per-exchange auth flavor (HMAC; OAuth; API key headers; FIX session)
- Per-exchange market hours (24/7 crypto vs business hours equities)
- Per-exchange sub-account support
- Per-exchange feature registry (for ML features)
- Per-exchange wire format

Without a meta-registry: each exchange is ad-hoc code; hardcoded if/else dispatch; framework doesn't compose.

With FOREACH_EXCHANGE: each exchange is 1 row; framework auto-flows.

## Pattern description

```cpp
// CoreFrameworks/ExchangeRegistry.hpp

// FOREACH_EXCHANGE(X) — every supported exchange = 1 row
// X(ENUM_VAL,         AdapterT,            name,        supports_sub, rate_per_min, market_hours_kind, submit_protocol)
#define FOREACH_EXCHANGE(X) \
    X(EXCHANGE_BINANCE,   BinanceAdapter<F>,   "binance",   /*sub=*/1, /*rate=*/1200, MARKET_HOURS_ALWAYS,     SUBMIT_PROTOCOL_WS_API) \
    /* .E.6 / future operator-triggered: */ \
    /* X(EXCHANGE_ALPACA, AlpacaAdapter<F>,    "alpaca",    /*sub=*/0, /*rate=*/200,  MARKET_HOURS_US_EQUITIES, SUBMIT_PROTOCOL_REST)   */ \
    /* X(EXCHANGE_IBKR,   IBKRAdapter<F>,      "ibkr",      /*sub=*/1, /*rate=*/3000, MARKET_HOURS_MULTI_ASSET, SUBMIT_PROTOCOL_FIX)    */
```

**Auto-generated abstractions:**

```cpp
// Enum
enum ExchangeEnum {
#define X(EN, _at, _nm, _sub, _r, _mh, _sp) EN,
    FOREACH_EXCHANGE(X)
#undef X
    NUM_EXCHANGES
};

// Per-exchange adapter type alias (tt:: dispatch)
template<ExchangeEnum E> struct ExchangeAdapter;
#define X(EN, AdapterT, _nm, _sub, _r, _mh, _sp) \
    template<> struct ExchangeAdapter<EN> { using type = AdapterT; };
FOREACH_EXCHANGE(X)
#undef X

// Per-exchange metadata accessors
constexpr bool exchange_supports_subaccounts(ExchangeEnum e);
constexpr uint32_t exchange_rate_per_minute(ExchangeEnum e);
constexpr MarketHoursKind exchange_market_hours_kind(ExchangeEnum e);
constexpr SubmitProtocol exchange_submit_protocol(ExchangeEnum e);
```

**Per-exchange auto-flow:**

- **Cfg parser:** reads `cfg.clusters[<exchange>]` for each enabled exchange
- **Per-cluster spawn:** producer + adapter + WS threads per cluster
- **Aggregator:** per-cluster totals computed automatically
- **Kill switch:** per-cluster kill flag in hierarchical pattern
- **fox-tui display:** per-cluster panel auto-generated

## Adapter contract

Every adapter type must specialize all `tt::*` exchange operations:

```cpp
namespace tt {
    template<typename A> int submit_order(A&, const SubmitCommand<F>&);
    template<typename A> int cancel_order(A&, uint64_t order_id);
    template<typename A> int query_balance(A&, AccountBalance<F>*);
    template<typename A> int query_positions(A&, PositionList<F>*);
    template<typename A> int establish_trade_stream(A&, callback);
    template<typename A> int establish_market_data(A&, callback);
    template<typename A> int connect(A&);
    template<typename A> int disconnect(A&);
    template<typename A> int reconcile(A&);
}
```

Per H13 type-trait dispatch (NOT reinterpret_cast). See `exchange-adapter-tt-dispatch-pattern.md`.

## H15 / H19 compliance

- **H15:** FOREACH_EXCHANGE enrolled in FOREACH_REGISTRY meta-registry
- **H19:** Level 1 meta-registry; parent = FOREACH_REGISTRY (Level 2)

```cpp
// In MetaRegistry.hpp:
// FOREACH_REGISTRY adds row for FOREACH_EXCHANGE with level=1, parent=FOREACH_REGISTRY
```

## H18 sidecar override discipline

For exchange-specific customizations beyond the metadata columns:

```cpp
// FOREACH_EXCHANGE_OVERRIDE(X) — sparse rows for custom semantics
#define FOREACH_EXCHANGE_OVERRIDE(X) \
    /* X(EXCHANGE_INDEX, custom_field, custom_value) */ \
    /* Example: */ \
    /* X(EXCHANGE_ALPACA, oauth_token_endpoint, "https://api.alpaca.markets/oauth/token") */
```

NEVER parallel `FOREACH_EXCHANGE_FOR_OAUTH` etc. — sidecar pattern preserves single source of truth.

## Worked example: adding Coinbase

```cpp
// 1. Implement CoinbaseAdapter<F> in Strategies/CoinbaseAdapter.hpp (~600-1200 LOC)
//    - REST submit endpoint; OAuth or API-key headers; trade-stream WS

// 2. Add row to FOREACH_EXCHANGE:
//    X(EXCHANGE_COINBASE, CoinbaseAdapter<F>, "coinbase", /*sub=*/0, /*rate=*/10000, MARKET_HOURS_ALWAYS, SUBMIT_PROTOCOL_REST)

// 3. Implement tt::* specializations for CoinbaseAdapter

// 4. Add per-cluster cfg files at configs/clusters/coinbase/

// 5. Boot engine; cluster auto-spawns; nodes auto-register

// Done. No other framework code touched.
```

## Stage progression criteria

- **Stage 3 first canonical** (lands at `.E.1` with Binance): pattern proven with 1 canonical
- **Stage 4 cohort** (operator-triggered when 2nd canonical lands): proven across ≥2 exchanges; framework gaps surfaced + closed
- **Stage 5 CLAUDE.md** (3rd canonical + discipline matures): promoted to CLAUDE.md item
- **Stage 6 cadence-locked** (CI enforcement): `check_foreach_exchange_substrate.py` verifies registry coverage

## Anti-patterns avoided

- **Hardcoded exchange dispatch via if/else** — Class 11 risk
- **Parallel wide-variant registry** — Class 21 risk; sidecar pattern preferred
- **Type-erased dispatch via reinterpret_cast** — H13 violation; tt:: pattern preferred
- **Hardcoded rate-limit / market-hours / auth flavor values scattered in code** — metadata columns canonical

## Cross-references

- Parent: `framework-patterns/x-macro-registry-with-presence-dispatch.md`
- Sister: `framework-patterns/foreach-subaccount-meta-registry-pattern.md`
- Consumer: `framework-patterns/exchange-adapter-tt-dispatch-pattern.md`
- Compliance: `framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md` (H15)
- Customization: `framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md` (H18)
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md`
- Framework verification: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.6-alpaca-exchange.md`
