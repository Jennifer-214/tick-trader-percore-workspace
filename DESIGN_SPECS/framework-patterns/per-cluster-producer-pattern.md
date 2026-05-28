---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.1
canonical_applications:
  - v5.15.5.F.4d.1.E.1 (Binance per-cluster producer thread)
sister_specs:
  - framework-patterns/per-cluster-shared-resource-pattern.md (parent; producer is one of N cluster resources)
  - framework-patterns/foreach-exchange-meta-registry-pattern.md (registry source)
  - concurrency-patterns/concurrency-model-summary.md (amended at .E.1; producer placement)
tags: [framework-discipline, per-cluster-producer, market-data-fan-out, per-exchange]
surface: [producer-thread, market-data-stream, hot-ring-fan-out]
applies_at_skills: [/precoding-audit-gate, /dod-audit]
---

# Per-cluster producer pattern

**Pattern intent:** Each cluster (exchange) has its OWN producer thread reading exchange's market-data WS. Producer parses ticks + fan-outs to cluster's node hot rings. Isolated across clusters; one exchange WS drop doesn't affect others' producers.

## Problem statement

Multi-exchange engine reads market data from N exchanges:
- Binance trade WS (different protocol/format than Alpaca)
- Alpaca trade-stream WS (different)
- IBKR market data subscription (different)
- Coinbase Pro level-2 WS (different)

Each exchange has its own:
- WS endpoint URL
- Message format (JSON; binary; etc.)
- Symbol notation
- Tick rate
- Reconnect semantics

Options:
1. **1 producer for all exchanges** — couples failure modes; complex message-format dispatch
2. **1 producer per node** — N×M connections; wasteful at retail rates
3. **1 producer per cluster** — per-exchange isolation; per-cluster sharing within

**Pattern: option 3.**

## Pattern description

```cpp
// Per-cluster producer thread reads exchange's market-data WS
void ClusterProducer_Run(ClusterState<...>& cluster) {
    PersistentWSConnection_Connect(&cluster.market_data_conn);

    while (!g_engine_shutdown_flag.load()) {
        // Read WS frame from exchange
        WSFrameParsed frame;
        if (WSFrame_Recv(&cluster.market_data_conn, &frame)) {
            switch (frame.opcode) {
                case WS_OPCODE_TEXT:
                    // Parse tick (exchange-specific format)
                    Tick<F> tick;
                    if (cluster.adapter.ParseTick(frame.payload, frame.payload_len, &tick)) {
                        // Fan-out to cluster's node hot rings
                        ProducerFanOut(cluster, tick);
                    }
                    break;
                case WS_OPCODE_PING:
                    WSFrame_SendPong(&cluster.market_data_conn);
                    break;
                case WS_OPCODE_CLOSE:
                    // Disconnect; reconnect via keepalive thread
                    break;
            }
        }
    }
}

// Fan-out tick to all cluster's nodes (each node has SPSC hot ring)
void ProducerFanOut(ClusterState<...>& cluster, const Tick<F>& tick) {
    for (uint32_t n = 0; n < cluster.node_count; ++n) {
        NodeState<F>* node = cluster.nodes[n];

        // Filter: only fan-out to nodes trading this tick's symbol
        // (alternatively: fan-out to ALL nodes; per-node hot path filters)
        if (TickAppliesTo(tick, node->binding.symbol)) {
            SPSCRing_Push(&node->hot_ring, tick);
        }
    }
}
```

### Per-exchange tick format

Each exchange has a different tick format. Adapter handles parsing:

```cpp
// Binance: JSON tick from trade WS
// {"e":"trade","E":1609459200000,"s":"BTCUSDT","t":12345,"p":"34000.00","q":"0.01",...}

// Alpaca: JSON from trade-stream
// {"T":"t","S":"TSLA","i":12345,"x":"V","p":650.50,"s":100,"t":"2024-01-01T..."}

// IBKR: TWS proprietary binary format

// Per-exchange parser in adapter
template<>
bool BinanceAdapter<F>::ParseTick(const uint8_t* payload, size_t len, Tick<F>* out) {
    // simdjson parse
    return true;
}

template<>
bool AlpacaAdapter<F>::ParseTick(const uint8_t* payload, size_t len, Tick<F>* out) {
    // Alpaca-specific parse
    return true;
}
```

### Per-exchange market-data WS configuration

```
# configs/clusters/binance/cluster.cfg:
market_data_endpoint = wss://stream.binance.com:9443/ws/btcusdt@trade
symbols_subscribed = [BTCUSDT, ETHUSDT, SOLUSDT]

# configs/clusters/alpaca/cluster.cfg:
market_data_endpoint = wss://stream.data.alpaca.markets/v2/iex
symbols_subscribed = [TSLA, NVDA]
```

Producer subscribes to listed symbols at boot.

### Per-cluster isolation

If Binance trade WS drops:
- Binance cluster's producer detects (ping timeout)
- Reconnects with exponential backoff
- Alpaca cluster's producer UNAFFECTED
- IBKR cluster's producer UNAFFECTED

Per-cluster failure containment by design.

## Stage progression criteria

- **Stage 3 first canonical** (`.E.1`): Binance per-cluster producer
- **Stage 4 cohort** (when 2nd cluster's producer lands; .E.6 Alpaca): pattern proven across protocols
- **Stage 5 CLAUDE.md** (3rd cluster): promoted

## Anti-patterns avoided

- **Shared producer for all exchanges** — couples failure modes
- **Per-node producer** — wasteful at retail tick rates
- **Hardcoded per-exchange parse dispatch** — adapter encapsulates

## Cross-references

- Parent: `framework-patterns/per-cluster-shared-resource-pattern.md`
- Parent: `framework-patterns/foreach-exchange-meta-registry-pattern.md`
- Sister: `concurrency-patterns/concurrency-model-summary.md` (amended at `.E.1`)
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md`
