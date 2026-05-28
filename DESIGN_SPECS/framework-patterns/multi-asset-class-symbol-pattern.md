---
type: framework-pattern
stage: 2-draft
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.7 (DEFERRED; operator-triggered)
sister_specs:
  - framework-patterns/foreach-exchange-meta-registry-pattern.md
tags: [framework-discipline, multi-asset, symbol-normalization, asset-class]
surface: [symbol-parsing, adapter-implementation]
---

# Multi-asset-class symbol pattern (Stage 2 DRAFT)

**Pattern intent:** Per-asset-class symbol normalization. Stocks (TSLA); futures (ESM5); options (TSLA  240517P00250000); forex (EUR/USD); crypto (BTCUSDT). Operator-facing canonical naming; exchange-native parsing in adapter.

## Pattern

```cpp
enum AssetClass {
    ASSET_CLASS_CRYPTO,
    ASSET_CLASS_STOCK,
    ASSET_CLASS_FUTURE,
    ASSET_CLASS_OPTION,
    ASSET_CLASS_FOREX,
};

struct SymbolDescriptor {
    AssetClass asset_class;
    char exchange_native_symbol[32];      // exchange's notation
    char engine_canonical_symbol[16];     // operator-facing
    union {
        struct {  // FUTURE
            char contract_month[4];        // "M5" = May 2025
            char root_symbol[8];           // "ES"
        } future;
        struct {  // OPTION
            uint64_t strike_price_micros;
            uint32_t expiry_date;          // YYYYMMDD
            char option_type;              // 'C' or 'P'
        } option;
    };
};
```

## Per-cluster symbol parser

```cpp
// Operator declares per-node symbol in cfg
// node_0/core.cfg: symbol = "ES_FUT_2025_05"
// Engine parses to SymbolDescriptor; adapter translates to exchange-native

template<typename F>
SymbolDescriptor IBKRAdapter<F>::ParseSymbol(const char* canonical) {
    // "ES_FUT_2025_05" → {FUTURE, "ESM5", "ES_FUT_2025_05", future{...}}
    SymbolDescriptor s;
    // ... parse ...
    return s;
}
```

## Stage progression

- **Stage 2 DRAFT**: reference for future
- **Stage 3 first canonical**: when operator adds non-crypto exchange (IBKR; Alpaca futures)

## Cross-references

- Sister: `framework-patterns/foreach-exchange-meta-registry-pattern.md`
- Operator: `plans/v5.15.5.F.4d.1.E.7-ibkr-exchange.md`
