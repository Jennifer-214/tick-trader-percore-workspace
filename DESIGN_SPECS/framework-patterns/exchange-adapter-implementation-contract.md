---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.6
canonical_applications:
  - v5.15.5.F.4d.1.E.6 (codified exchange adapter contract; framework genericity verified)
sister_specs:
  - framework-patterns/exchange-adapter-tt-dispatch-pattern.md (parent; tt:: dispatch)
  - framework-patterns/foreach-exchange-meta-registry-pattern.md (registry consumes contract)
tags: [framework-discipline, exchange-adapter, implementation-contract, tt-dispatch]
surface: [adapter-implementation, framework-genericity]
applies_at_skills: [/precoding-audit-gate]
---

# Exchange adapter implementation contract

**Pattern intent:** Codifies the `tt::*` interface contract that every exchange adapter MUST implement. Operator adding new exchange follows this contract; no need to re-derive design decisions. Sister to `exchange-adapter-tt-dispatch-pattern.md` (pattern is HOW dispatched; contract is WHAT must be implemented).

## Adapter struct requirements

Every adapter type must be a template-parameterized struct:

```cpp
template<typename F>
struct ExampleExchangeAdapter {
    // === REQUIRED FIELDS ===

    // Authentication
    char api_key[<size>];
    char api_secret[<size>];

    // Endpoints
    char rest_endpoint[256];
    char ws_endpoint[256];        // if exchange supports WS
    char trade_stream_endpoint[256];

    // Connection state
    PersistentWSConnection_Inlined ws_conn;   // if applicable

    // === REQUIRED STATIC METADATA ===

    static constexpr bool supports_subaccounts = ...;        // true/false
    static constexpr uint32_t rate_per_minute = ...;         // per Binance/Alpaca/etc. docs
    static constexpr const char* auth_flavor = ...;          // "hmac" / "api_key_headers" / "oauth" / "fix"
    static constexpr MarketHoursKind market_hours_kind = ...; // MARKET_HOURS_ALWAYS / MARKET_HOURS_US_EQUITIES / etc.
    static constexpr SubmitProtocol submit_protocol = ...;   // REST / WS_API / FIX
};
```

## Required `tt::*` specializations

Every adapter must implement these 9 specializations:

```cpp
namespace tt {
    // 1. Submit order (CRITICAL latency path)
    template<typename A> int submit_order(A&, const SubmitCommand<F>&);

    // 2. Cancel order
    template<typename A> int cancel_order(A&, uint64_t order_id);

    // 3. Query account info (boot-time permission audit)
    template<typename A> int query_account_info(A&, uint32_t subaccount_id, AccountInfo*);

    // 4. Query balance (reconciliation)
    template<typename A> int query_balance(A&, uint32_t subaccount_id, AccountBalance<F>*);

    // 5. Query positions (reconciliation)
    template<typename A> int query_positions(A&, uint32_t subaccount_id, PositionList<F>*);

    // 6. Establish trade stream (market data WS; producer consumes)
    template<typename A> int establish_trade_stream(A&, market_data_callback);

    // 7. Establish user-data stream (fills WS; fill router consumes)
    template<typename A> int establish_user_data_stream(A&, fill_callback);

    // 8. Connect
    template<typename A> int connect(A&);

    // 9. Disconnect
    template<typename A> int disconnect(A&);
}
```

## Optional `tt::*` specializations

Exchange-specific operations; implement if exchange supports:

```cpp
namespace tt {
    // Internal transfer (Binance; sub-account capital reallocation)
    template<typename A> int internal_transfer(A&, uint32_t from_sub, uint32_t to_sub,
                                                 FPN<F> amount, const char* asset);

    // Get rate-limit usage (some exchanges report)
    template<typename A> int query_rate_limits(A&, RateLimitState*);

    // Subscribe to specific symbol stream
    template<typename A> int subscribe_symbol(A&, const char* symbol);

    // Listen-key keepalive (Binance user-data; renew every 25min)
    template<typename A> int listen_key_keepalive(A&);
}
```

Engine queries presence via dlsym; uses if available; degrades gracefully if not.

## Required tick + fill parsers

Adapter must provide:

```cpp
// Parse incoming tick from market-data WS
template<typename F>
bool ExampleExchangeAdapter<F>::ParseTick(const uint8_t* payload, size_t len,
                                          Tick<F>* out);

// Parse incoming fill from user-data WS
template<typename F>
bool ExampleExchangeAdapter<F>::ParseFill(const uint8_t* payload, size_t len,
                                          FillEvent<F>* out);
```

## Sub-account handling (if supported)

If `supports_subaccounts = true`:

```cpp
// Sub-account routing in submit
template<>
int tt::submit_order<ExampleExchangeAdapter<F>>(
    ExampleExchangeAdapter<F>& adapter,
    const SubmitCommand<F>& cmd) {

    uint32_t subaccount_id = ExtractSubAccountId(cmd.client_order_id_prefix);
    SubAccountCredentials& creds = adapter.subaccount_pool[subaccount_id];

    // Sign with sub-account credentials
    // ... HMAC or OAuth with sub-account API key + secret ...

    return SendSubmit(adapter.rest_endpoint, signed_payload);
}
```

If `supports_subaccounts = false`:
- Virtual partition mode (engine-side accounting per "sub-account slot"; single Binance account)
- All submits use single account credentials

## How operator adds a new exchange

1. **Implement adapter struct** in `Strategies/<ExchangeName>Adapter.hpp`
2. **Implement 9 required `tt::*` specializations** (~500-1500 LOC depending on protocol)
3. **Implement optional `tt::*` specializations** if applicable
4. **Implement ParseTick + ParseFill** for exchange's format
5. **Add 1 row to FOREACH_EXCHANGE registry** per `foreach-exchange-meta-registry-pattern.md`
6. **Add cfg files** at `configs/clusters/<exchange>/` per `cluster-node-hierarchy-filesystem-layout-pattern.md`
7. **Test against exchange testnet/paper** API
8. **Boot engine**; cluster auto-registers; nodes auto-spawn per cfg

NO other framework code touched. Per `feedback_audit_canonical_sister_before_new_infra` — extend pattern; don't parallel.

## Common exchange protocol families

- **REST + HMAC** (Binance; OKX; many crypto): synchronous REST submit; HMAC-SHA256 signature; WS for streams
- **REST + API-key headers** (Alpaca; some crypto): synchronous REST; API key + secret in HTTP headers; no HMAC
- **WS-API** (Binance /ws-api/v3; some pro): persistent WS for order submission; saves handshake per submit
- **FIX session** (institutional; IBKR; CME): stateful FIX 4.4 session with sequence numbers; reliable + ordered
- **Proprietary** (TWS for IBKR retail; some venues): exchange-specific protocols

Adapter encapsulates differences; framework dispatch is uniform.

## Stage progression criteria

- **Stage 3 first canonical** (`.E.6`): contract codified; framework genericity verified
- **Stage 4 cohort** (when operator-triggered 2nd canonical adapter lands): contract proven
- **Stage 5 CLAUDE.md** (3rd canonical): promoted

## Cross-references

- Parent: `framework-patterns/exchange-adapter-tt-dispatch-pattern.md`
- Parent: `framework-patterns/foreach-exchange-meta-registry-pattern.md`
- Operator doc: `DOCS/CONTRIBUTING/add-exchange.md` (lands at `.E.2`/`.E.6`)
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.6-alpaca-exchange.md`
