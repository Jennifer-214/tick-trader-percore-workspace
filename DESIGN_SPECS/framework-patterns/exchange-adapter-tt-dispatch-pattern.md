---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.1
canonical_applications:
  - v5.15.5.F.4d.1.E.1 (Binance first canonical; via `tt::*<BinanceAdapter<F>>` specializations)
sister_specs:
  - framework-patterns/foreach-exchange-meta-registry-pattern.md (parent registry)
  - framework-patterns/type-trait-dispatch-via-tt-namespace.md (parent dispatch discipline; H13)
  - framework-patterns/exchange-adapter-implementation-contract.md (sister: adapter contract spec)
tags: [framework-discipline, tt-dispatch, exchange-adapter, h13-compliance, type-traits]
surface: [adapter-dispatch, registry-consumption]
applies_at_skills: [/precoding-audit-gate, /dod-audit, /trace-deps]
---

# Exchange adapter tt:: dispatch pattern

**Pattern intent:** Per-exchange adapter dispatch via `tt::<verb>_<noun><ExchangeType>` template specializations (H13 compliant). No reinterpret_cast. No vtable. Compile-time dispatch with per-adapter optimization.

## Problem statement

FOREACH_EXCHANGE has N rows; each row has an AdapterT type. Code that operates on a cluster's adapter needs to dispatch operations (submit_order; query_balance; etc.) to that adapter's specific implementation.

Options:
1. **Virtual function dispatch** — violates H2 on hot path (vtable lookup)
2. **`reinterpret_cast` punning** — H13 forbids (Class 23 anti-pattern)
3. **`switch (cluster.exchange_id) { ... }`** — branchy; Class 28 anti-pattern; doesn't scale to N exchanges
4. **Template specializations via `tt::`** — H13-compliant; compile-time dispatch; per-adapter optimization

**Pattern: option 4.**

## Pattern description

### Adapter contract declaration

```cpp
// In tt:: namespace (CoreFrameworks/TtDispatch.hpp or similar)

namespace tt {
    // Generic primary template — never instantiated; specializations required
    template<typename AdapterT>
    int submit_order(AdapterT& adapter, const SubmitCommand<F>& cmd) = delete;

    template<typename AdapterT>
    int cancel_order(AdapterT& adapter, uint64_t order_id) = delete;

    template<typename AdapterT>
    int query_balance(AdapterT& adapter, AccountBalance<F>* out) = delete;

    template<typename AdapterT>
    int query_positions(AdapterT& adapter, PositionList<F>* out) = delete;

    template<typename AdapterT>
    int establish_trade_stream(AdapterT& adapter, callback_t cb) = delete;

    template<typename AdapterT>
    int establish_market_data(AdapterT& adapter, callback_t cb) = delete;

    template<typename AdapterT>
    int connect(AdapterT& adapter) = delete;

    template<typename AdapterT>
    int disconnect(AdapterT& adapter) = delete;

    template<typename AdapterT>
    int reconcile(AdapterT& adapter) = delete;
}
```

### Per-exchange specializations

```cpp
// In BinanceAdapter.hpp

template<>
int tt::submit_order<BinanceAdapter<F>>(BinanceAdapter<F>& adapter, const SubmitCommand<F>& cmd) {
    // Binance-specific submit logic
    // ... HMAC sign + WS-API frame send (or REST per .E.3 cfg) ...
    return 0;
}

template<>
int tt::cancel_order<BinanceAdapter<F>>(BinanceAdapter<F>& adapter, uint64_t order_id) {
    // ...
}

// ... etc for all contract methods
```

### Per-cluster dispatch (compile-time)

```cpp
// FOREACH_EXCHANGE row provides AdapterT type alias via ExchangeAdapter<E>::type

// Per-cluster runtime selection:
int SubmitToCluster(uint32_t cluster_id, const SubmitCommand<F>& cmd) {
    switch (cluster_id) {  // OK at slow-path (not hot path); rare branch
        case EXCHANGE_BINANCE: {
            BinanceAdapter<F>& adapter = g_state.clusters[cluster_id].adapter;
            return tt::submit_order<BinanceAdapter<F>>(adapter, cmd);
        }
        case EXCHANGE_ALPACA: {
            AlpacaAdapter<F>& adapter = g_state.clusters[cluster_id].adapter;
            return tt::submit_order<AlpacaAdapter<F>>(adapter, cmd);
        }
        // ... per row in FOREACH_EXCHANGE
    }
}

// Hot-path version: use compile-time template parameter
template<ExchangeEnum E>
int NodeHotPath_Submit_T(NodeState<F>& node, const SubmitCommand<F>& cmd) {
    using AdapterT = typename ExchangeAdapter<E>::type;
    AdapterT& adapter = g_state.clusters[E].adapter;
    return tt::submit_order<AdapterT>(adapter, cmd);
}
```

## H13 compliance verification

Per H13 strict invariant: NO type-erased reinterpret_cast dispatch. ALL exchange-adapter dispatch uses `tt::*<AdapterT>` template specializations.

Audit at `.E.0`:
```bash
rg "reinterpret_cast" --type cpp --type hpp | grep -i "adapter\|exchange"
# Expected: empty (no findings)

rg "tt::submit_order\|tt::cancel_order" --type cpp --type hpp
# Expected: per-exchange specializations enumerated
```

## Per-adapter implementation freedom

Each exchange's specialization can use the most-appropriate technique for that exchange:

- **Binance:** HMAC-SHA256 + WS-API frame (or REST fallback)
- **Alpaca:** API-key headers + REST
- **IBKR:** FIX session message OR TWS proprietary
- **Coinbase:** OAuth + REST
- **Kraken:** API-key + REST signed

No common-denominator constraint; each adapter is its own optimized path. Compile-time dispatch means zero overhead at runtime.

## Stage progression criteria

- **Stage 3 first canonical** (`.E.1` with Binance): dispatch pattern proven with 1 adapter
- **Stage 4 cohort** (when 2nd adapter added; .E.6 Alpaca or operator-triggered): pattern proven across 2 adapters
- **Stage 5 CLAUDE.md** (3rd adapter + discipline matures): promoted

## Anti-patterns avoided

- **Virtual function dispatch on hot path** — H2 violation
- **`reinterpret_cast` punning** — H13 violation; Class 23
- **Branchy switch in hot path** — Class 28 violation
- **Vtable-based adapter dispatch** — vtable lookup overhead (~1-5ns) + complexity

## Cross-references

- Parent: `framework-patterns/type-trait-dispatch-via-tt-namespace.md` (H13)
- Parent: `framework-patterns/foreach-exchange-meta-registry-pattern.md` (registry source)
- Sister: `framework-patterns/exchange-adapter-implementation-contract.md` (contract; specifies which `tt::*` to implement)
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md`
- Operator-add documentation: `DOCS/CONTRIBUTING/add-exchange.md` (lands at `.E.2`/`.E.6`)
