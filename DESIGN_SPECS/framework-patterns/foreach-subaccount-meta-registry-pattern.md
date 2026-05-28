---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.1 (substrate) + v5.15.5.F.4d.1.E.5 (full wiring)
canonical_applications:
  - v5.15.5.F.4d.1.E.1 (FOREACH_SUBACCOUNT_BINANCE substrate)
  - v5.15.5.F.4d.1.E.5 (real credentials wired)
sister_specs:
  - framework-patterns/foreach-exchange-meta-registry-pattern.md (parent registry)
  - framework-patterns/x-macro-registry-with-presence-dispatch.md (X-macro discipline)
  - framework-patterns/per-node-economic-isolation-pattern.md (consumer)
tags: [framework-discipline, sub-accounts, x-macro-registry, per-exchange, credentials]
surface: [credentials-loading, per-cluster-state, per-node-binding]
applies_at_skills: [/precoding-audit-gate, /dod-audit]
---

# FOREACH_SUBACCOUNT meta-registry pattern

**Pattern intent:** Per-exchange sub-account topology codified as sparse X-macro registry rows. Each row carries sub-account ID + credential references + initial capital target. Adding a sub-account = 1 row + 1 credentials cfg file.

## Problem statement

Per-exchange sub-account support varies:
- **Binance:** master account + N sub-accounts (operator-configurable count; up to ~100)
- **Alpaca:** single account; no sub-accounts (FOREACH_SUBACCOUNT_ALPACA empty OR virtual partition)
- **IBKR:** FA structure (master + N client sub-accounts; optional)
- **Coinbase Pro:** sub-account support via API; similar to Binance

Without registry: each exchange's sub-account handling is ad-hoc.

With FOREACH_SUBACCOUNT_<EXCHANGE>: each per-exchange has its own sparse registry; framework auto-flows credential loading + permission audit + capital tracking.

## Pattern description

### Per-exchange registry

```cpp
// CoreFrameworks/SubAccountRegistry.hpp

// FOREACH_SUBACCOUNT_BINANCE(X) — sub-accounts for Binance cluster
// X(SUBACCOUNT_ID, api_key_env_var,           api_secret_env_var,           initial_capital_target)
#define FOREACH_SUBACCOUNT_BINANCE(X) \
    X(0,            "BINANCE_SUB0_API_KEY",     "BINANCE_SUB0_API_SECRET",     2500_USDT) \
    X(1,            "BINANCE_SUB1_API_KEY",     "BINANCE_SUB1_API_SECRET",     2500_USDT) \
    X(2,            "BINANCE_SUB2_API_KEY",     "BINANCE_SUB2_API_SECRET",     2500_USDT) \
    X(3,            "BINANCE_SUB3_API_KEY",     "BINANCE_SUB3_API_SECRET",     2500_USDT)

// Sub-account count
#define BINANCE_SUBACCOUNT_COUNT 4

// Per-exchange auto-generated accessor
constexpr uint32_t exchange_subaccount_count(ExchangeEnum e) {
    switch (e) {
        case EXCHANGE_BINANCE: return BINANCE_SUBACCOUNT_COUNT;
        // case EXCHANGE_ALPACA: return ALPACA_SUBACCOUNT_COUNT;  // future
        default: return 1;  // single-account exchanges
    }
}

// (.E.6 future) FOREACH_SUBACCOUNT_ALPACA — single virtual partition
// (.E.7 future) FOREACH_SUBACCOUNT_IBKR — FA structure
```

### Boot-time credential loading

```cpp
void LoadSubAccountCredentials(uint32_t cluster_id, uint32_t subaccount_id,
                                SubAccountCredentials* out) {
    char cfg_path[512];
    snprintf(cfg_path, sizeof(cfg_path),
             "configs/clusters/%s/credentials/sub_%u.cfg",
             EXCHANGE_NAME(cluster_id), subaccount_id);

    ParseSubAccountCfg(cfg_path, out);

    // Resolve env vars per FOREACH_SUBACCOUNT_<EXCHANGE> row
    const char* api_key_env = SUBACCOUNT_API_KEY_ENV(cluster_id, subaccount_id);
    out->api_key = getenv(api_key_env);
    if (!out->api_key) FATAL("Env var %s not set for sub-account %u", api_key_env, subaccount_id);

    // Validate permissions (cfg-side declared; verified later via Binance query)
    if (out->enableWithdrawals) {
        FATAL("Sub-account %u declares enableWithdrawals=1; refusing", subaccount_id);
    }
}
```

### Per-cluster sub-account pool

```cpp
template<typename AdapterT>
struct SubAccountPool {
    SubAccountCredentials credentials[MAX_SUBACCOUNTS];
    uint32_t count;
};

// At boot: FOREACH_SUBACCOUNT_<EXCHANGE>(X) walks rows; loads each
void Cluster_LoadSubAccounts(ClusterState<...>& cluster) {
    switch (cluster.exchange_id) {
        case EXCHANGE_BINANCE:
            #define X(id, key_env, secret_env, target) \
                LoadSubAccountCredentials(cluster.exchange_id, id, &cluster.subaccounts.credentials[id]);
            FOREACH_SUBACCOUNT_BINANCE(X)
            #undef X
            cluster.subaccounts.count = BINANCE_SUBACCOUNT_COUNT;
            break;
        // ... per-exchange
    }
}
```

### Per-node sub-account binding

```cpp
// In NodeState.binding (from .E.1 foundation):
alignas(64) struct {
    uint32_t cluster_id;        // FOREACH_EXCHANGE index
    uint32_t subaccount_id;     // FOREACH_SUBACCOUNT_<EXCHANGE> index within cluster
    char client_order_id_prefix[16];  // "C<cluster><sub><node>_"
} binding;

// Validation at boot:
assert(node.binding.subaccount_id < exchange_subaccount_count(node.binding.cluster_id));
```

## Per-exchange sub-account semantics

| Exchange | Sub-account support | FOREACH_SUBACCOUNT count |
|---|---|---|
| Binance | Native sub-accounts | N (operator-configured; typical 4-16) |
| Alpaca | No sub-accounts; virtual partition | 1 (virtual; nodes share single account) |
| IBKR (retail) | No sub-accounts | 1 |
| IBKR (FA) | Client account hierarchy | N (per FA structure) |
| Coinbase Pro | Sub-account API | N |
| Kraken | Single account per user | 1 |

Framework supports all variants via per-exchange FOREACH_SUBACCOUNT_<EXCHANGE>.

## Stage progression criteria

- **Stage 3 first canonical** (`.E.1` substrate + `.E.5` real wiring): Binance N sub-accounts
- **Stage 4 cohort** (when 2nd exchange adds sub-accounts; e.g., Coinbase Pro): pattern proven
- **Stage 5 CLAUDE.md** (3rd application): promoted

## Anti-patterns avoided

- **Hardcoded sub-account count** (Class 11)
- **Sub-account credentials in tracked files** (security risk; env-var refs preferred)
- **Per-exchange-specific code for sub-account handling** (canonical FOREACH_* registry)

## Cross-references

- Parent: `framework-patterns/foreach-exchange-meta-registry-pattern.md`
- Parent: `framework-patterns/x-macro-registry-with-presence-dispatch.md`
- Consumer: `framework-patterns/per-node-economic-isolation-pattern.md`
- First substrate: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md`
- Full wiring: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.5-real-subaccounts-capital-framework.md`
