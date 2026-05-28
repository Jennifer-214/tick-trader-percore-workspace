---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.1
canonical_applications:
  - v5.15.5.F.4d.1.E.1 (cfg field categorization)
sister_specs:
  - framework-patterns/hierarchical-config-with-per-node-folders.md (hot-reload semantics)
  - framework-patterns/universal-cfg-field-registry-pattern.md (existing; per-node fields)
tags: [framework-discipline, cfg-mutability, hot-reload, concurrency-safety]
surface: [cfg-parser, hot-reload, runtime-mutation]
applies_at_skills: [/precoding-audit-gate, /dod-audit]
---

# Runtime-mutable vs boot-time config pattern

**Pattern intent:** Categorize each cfg field by mutability axis. Boot-time fields (long-lived connections; credentials; thread pinning) require restart. Runtime-mutable fields (parameters; bindings) update via SIGUSR1 hot-reload through slow→hot seqlock.

## Problem statement

Some cfg fields can change at runtime safely:
- Strategy parameters (EMA period; thresholds; etc.)
- Per-node mode (paper / live / etc.)
- Risk thresholds
- Logging level
- Per-cluster reserve_pct

Other cfg fields CANNOT change without restart:
- Exchange enable/disable (TLS connections established at boot)
- Sub-account credentials (engine validates at boot)
- API endpoints (long-lived connections)
- Per-thread CPU pinning (set at thread spawn)
- io_uring / kTLS configuration (kernel-level setup)
- Number of nodes per cluster (resources pre-allocated)

Without categorization: runtime hot-reload either fails ungracefully OR mutates state that the engine assumed was stable.

With explicit categorization: runtime-mutable fields apply atomically; boot-time fields refuse hot-reload + suggest restart.

## Pattern description

### Per-field metadata column in FOREACH_PER_NODE_CFG_FIELD

```cpp
// CoreFrameworks/CfgFieldRegistry.hpp (existing X-macro)

// X(field_name, cfg_key, type, default_value, mutability, applies_to_*)
#define FOREACH_PER_NODE_CFG_FIELD(X) \
    X(strategy_name,     "strategy",          KIND_STRING,  "momentum",      MUTABILITY_RUNTIME, ...) \
    X(risk_pct,          "risk_pct",          KIND_DOUBLE,  0.02,            MUTABILITY_RUNTIME, ...) \
    X(mode,              "mode",              KIND_ENUM,    NODE_MODE_PAPER, MUTABILITY_RUNTIME, ...) \
    X(subaccount_id,     "subaccount_id",     KIND_UINT32,  0,               MUTABILITY_BOOT_TIME, ...) \
    X(symbol,            "symbol",            KIND_STRING,  "BTCUSDT",       MUTABILITY_BOOT_TIME_OR_NO_OPEN_POS, ...) \
    /* ... */
```

### Mutability axis enum

```cpp
enum CfgMutability {
    MUTABILITY_BOOT_TIME,                    // requires engine restart
    MUTABILITY_BOOT_TIME_OR_NO_OPEN_POS,     // runtime-mutable IF node has no open positions
    MUTABILITY_RUNTIME,                      // runtime-mutable always; slow→hot seqlock propagates
    MUTABILITY_RUNTIME_VIA_AGGREGATOR,       // runtime-mutable; aggregator coordinates (e.g., kill thresholds)
};
```

### Hot-reload validation logic

```cpp
int Cfg_HotReload(EngineState<F>& state, const NodeConfig<F>& new_cfg, uint32_t node_id) {
    NodeConfig<F>& current = state.nodes[node_id].cfg;

    // For each field: check mutability + safety condition
    #define X(field, key, type, default_val, mutability, ...) { \
        if (current.field != new_cfg.field) { \
            switch (mutability) { \
                case MUTABILITY_BOOT_TIME: \
                    LOG_ERROR("Field %s is boot-time-only; refuse hot-reload", key); \
                    return -EPERM; \
                case MUTABILITY_BOOT_TIME_OR_NO_OPEN_POS: \
                    if (state.nodes[node_id].has_open_position) { \
                        LOG_ERROR("Field %s requires no open positions; refuse hot-reload", key); \
                        return -EBUSY; \
                    } \
                    break; \
                case MUTABILITY_RUNTIME: \
                    break;  // OK to update \
                case MUTABILITY_RUNTIME_VIA_AGGREGATOR: \
                    break;  // OK; aggregator handles \
            } \
        } \
    }
    FOREACH_PER_NODE_CFG_FIELD(X)
    #undef X

    // All fields validated; apply atomically via slow→hot seqlock
    NodeState_PublishParams(state.nodes[node_id], new_cfg);
    return 0;
}
```

### Operator workflow examples

```bash
# RUNTIME mutable: update strategy parameter
$EDITOR configs/clusters/binance/nodes/node_0/strategy.cfg  # change ema_period 14 → 20
fox-cli reload-node-config binance/node_0
# Engine validates; applies via seqlock; new param visible to hot path next cycle

# BOOT_TIME_OR_NO_OPEN_POS: change strategy (requires flat position)
fox-cli pause-node binance/node_0       # wait for positions to close
$EDITOR configs/clusters/binance/nodes/node_0/core.cfg  # change strategy momentum → ml
fox-cli reload-node-config binance/node_0
fox-cli resume-node binance/node_0

# BOOT_TIME: change subaccount_id (requires restart)
$EDITOR configs/clusters/binance/nodes/node_0/core.cfg  # change subaccount_id 0 → 2
fox-cli reload-node-config binance/node_0
# Engine refuses: "Field subaccount_id is boot-time-only"
# Operator must: stop engine; edit; start engine

# RUNTIME_VIA_AGGREGATOR: kill threshold update
fox-cli set-kill-threshold node binance/node_0 0.15
# Engine updates aggregator state; reflects immediately
```

## Stage progression criteria

- **Stage 3 first canonical** (`.E.1`): mutability axis applied to FOREACH_PER_NODE_CFG_FIELD
- **Stage 4 cohort** (when 2nd application: e.g., FOREACH_CLUSTER_CFG_FIELD): pattern proven
- **Stage 5 CLAUDE.md** (3rd application): promoted

## Anti-patterns avoided

- **Silent hot-reload of boot-time fields** — runtime mutation of state engine assumed stable
- **All-or-nothing hot-reload** — partial reload preferable; refuse fields with safety violations
- **Manual per-field mutability check** — registry metadata column canonical

## Cross-references

- Sister: `framework-patterns/hierarchical-config-with-per-node-folders.md`
- Parent: `framework-patterns/universal-cfg-field-registry-pattern.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md`
