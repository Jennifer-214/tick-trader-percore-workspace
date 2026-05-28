---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.3
canonical_applications:
  - v5.15.5.F.4d.1.E.3 (Binance WS-API; framework supports REST/WS-API/FIX dispatch)
sister_specs:
  - framework-patterns/foreach-exchange-meta-registry-pattern.md (registry metadata column)
  - framework-patterns/exchange-adapter-tt-dispatch-pattern.md (sister; dispatch mechanism)
tags: [framework-discipline, submit-protocol, per-exchange, sidecar]
surface: [submit-path, adapter-dispatch]
applies_at_skills: [/precoding-audit-gate]
---

# Per-exchange submit protocol selection

**Pattern intent:** FOREACH_EXCHANGE row's `submit_protocol` column selects per-exchange submit path. REST (Alpaca; some crypto). WS-API (Binance preferred). FIX (IBKR institutional). Selection at compile time via tt:: dispatch; runtime fallback via cfg.

## Pattern

### Metadata column

```cpp
enum SubmitProtocol : uint8_t {
    SUBMIT_PROTOCOL_REST    = 0,
    SUBMIT_PROTOCOL_WS_API  = 1,
    SUBMIT_PROTOCOL_FIX     = 2,
};

// In FOREACH_EXCHANGE row metadata:
// X(EXCHANGE_BINANCE, BinanceAdapter<F>, "binance", sub=1, rate=1200, hours=ALWAYS, protocol=WS_API)
// X(EXCHANGE_ALPACA,  AlpacaAdapter<F>,  "alpaca",  sub=0, rate=200,  hours=US_EQ,  protocol=REST)
// X(EXCHANGE_IBKR,    IBKRAdapter<F>,    "ibkr",    sub=1, rate=3000, hours=MULTI,  protocol=FIX)
```

### Dispatch via tt::

```cpp
template<typename F>
int tt::submit_order<BinanceAdapter<F>>(BinanceAdapter<F>& adapter, const SubmitCommand<F>& cmd) {
    switch (adapter.submit_protocol_cfg) {  // operator-overridable via sidecar
        case SUBMIT_PROTOCOL_WS_API:
            return BinanceSubmit_WSAPI(adapter, cmd);
        case SUBMIT_PROTOCOL_REST:
            return BinanceSubmit_REST(adapter, cmd);  // fallback
    }
}
```

### Sidecar override (H18)

```cpp
// FOREACH_EXCHANGE_SUBMIT_PROTOCOL_OVERRIDE — sparse rows for cfg-driven override
#define FOREACH_EXCHANGE_SUBMIT_PROTOCOL_OVERRIDE(X) \
    /* Example: Binance fallback to REST during WS-API outage */ \
    /* X(EXCHANGE_BINANCE, cfg_field="binance.submit_fallback_to_rest", default=false) */
```

Operator cfg flag: `clusters/binance/cluster.cfg: submit_protocol_override = rest` forces REST instead of WS-API.

## Stage progression

- **Stage 3 first canonical** (`.E.3`): Binance WS-API selection
- **Stage 4 cohort** (when 2nd exchange uses different protocol)

## Cross-references

- Parent: `framework-patterns/foreach-exchange-meta-registry-pattern.md`
- First application: `plans/v5.15.5.F.4d.1.E.3-ws-api-persistent-connections.md`
