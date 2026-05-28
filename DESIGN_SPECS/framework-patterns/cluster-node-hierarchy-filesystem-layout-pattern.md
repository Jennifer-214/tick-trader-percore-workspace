---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.1
canonical_applications:
  - v5.15.5.F.4d.1.E.1 (first canonical: Deployment > Cluster > Node hierarchy)
sister_specs:
  - framework-patterns/foreach-exchange-meta-registry-pattern.md (cluster = exchange concept)
  - framework-patterns/foreach-subaccount-meta-registry-pattern.md (per-cluster sub-accounts)
  - framework-patterns/hierarchical-config-with-per-node-folders.md (config file layout)
  - framework-patterns/per-cluster-shared-resource-pattern.md (cluster-level threads)
tags: [framework-discipline, cluster-node-hierarchy, filesystem-layout, per-node-isolation]
surface: [config-parser, cluster-state, node-state, filesystem]
applies_at_skills: [/precoding-audit-gate, /dod-audit, /readiness]
---

# Cluster/Node hierarchy filesystem layout pattern

**Pattern intent:** Reflect the architectural hierarchy (Deployment > Cluster > Node) in the filesystem config layout. Each layer has its own directory + config file shape. Operator-facing structure mirrors engine-internal structure.

## Problem statement

Multi-exchange + multi-sub-account engine needs operator-managed config files for:
- Deployment-level settings (engine.cfg)
- Per-cluster (per-exchange) settings (cluster.cfg)
- Per-cluster credentials (per-sub-account credentials.cfg)
- Per-node (per-sub-account-instance) settings (core.cfg; strategy.cfg; ml.cfg; observability.cfg)

Flat config files (monolithic engine.cfg) don't scale — config grows unboundedly with N exchanges × M sub-accounts × K strategies.

Hierarchical layout reflects the structure cleanly + enables operator workflows (rm -rf cluster/; cp -r node_0 node_4; per-node git diff).

## Filesystem layout

```
configs/
├── engine.cfg                                  # deployment-level (global)
│
├── clusters/
│   ├── binance/                                # cluster = exchange instance
│   │   ├── cluster.cfg                         # endpoints, rate budget, reserve %, market hours kind
│   │   ├── credentials/                        # gitignored
│   │   │   ├── master.cfg                      # master account credentials
│   │   │   ├── sub_0.cfg                       # sub-account 0
│   │   │   ├── sub_1.cfg
│   │   │   ├── sub_2.cfg
│   │   │   └── sub_3.cfg
│   │   └── nodes/
│   │       ├── node_0/
│   │       │   ├── core.cfg                    # binding: sub-account, symbol, capital, mode
│   │       │   ├── strategy.cfg                # FULL strategy parameters
│   │       │   ├── ml.cfg                      # ML model paths + scaler binding
│   │       │   ├── observability.cfg           # per-node log level, metric tags
│   │       │   └── notes.md                    # operator notes (markdown; optional)
│   │       ├── node_1/
│   │       ├── node_2/
│   │       └── node_3/
│   ├── alpaca/                                 # additional cluster (.E.6 future or operator-add)
│   │   ├── cluster.cfg
│   │   ├── credentials/
│   │   │   └── account.cfg                     # Alpaca: single account (no sub-accounts)
│   │   └── nodes/
│   │       ├── node_0/
│   │       └── node_1/
│   └── ibkr/                                   # future cluster (.E.7 deferred)
│
├── strategies/                                 # strategy code references (NOT cfg)
│   └── (build artifacts; libstrategy_*.so)
│
└── operators/                                  # operator-personal settings (gitignored)
    └── caramel/
        ├── tui-keybindings.cfg
        └── cli-aliases.cfg
```

## Hierarchical loading discipline

Engine boot parses cfg in this order (per `hierarchical-config-validation-pattern.md`):

1. **Deployment level:** `engine.cfg` — global settings
2. **Cluster level:** For each enabled cluster (per FOREACH_EXCHANGE rows): `clusters/<name>/cluster.cfg`
3. **Sub-account level:** For each cluster's enabled sub-accounts: `clusters/<name>/credentials/sub_<id>.cfg`
4. **Node level:** For each node in cluster: `clusters/<name>/nodes/node_<id>/{core,strategy,ml,observability}.cfg`
5. **Cross-file validation:** every node references valid cluster + sub-account; every credential parseable; etc.

## Operator workflows enabled

```bash
# Add new cluster (after adapter is implemented)
mkdir -p configs/clusters/coinbase/{credentials,nodes}
cp -r configs/clusters/binance/nodes/node_0 configs/clusters/coinbase/nodes/node_0
$EDITOR configs/clusters/coinbase/cluster.cfg     # set endpoints
$EDITOR configs/clusters/coinbase/credentials/master.cfg
$EDITOR configs/clusters/coinbase/nodes/node_0/core.cfg

# Remove cluster cleanly
rm -rf configs/clusters/coinbase/

# Diff two clusters
diff -r configs/clusters/binance/ configs/clusters/alpaca/

# Clone a node (e.g., add 2 more Binance nodes)
cp -r configs/clusters/binance/nodes/node_0 configs/clusters/binance/nodes/node_4
$EDITOR configs/clusters/binance/nodes/node_4/core.cfg  # update subaccount_id

# Per-node git diff
git diff configs/clusters/binance/nodes/node_0/strategy.cfg
```

## Permissions discipline

- `configs/clusters/*/credentials/` directory `chmod 700` (only owner)
- `configs/clusters/*/credentials/*.cfg` files `chmod 600` (only owner readable)
- `configs/clusters/*/credentials/` gitignored (never committed)
- env-var references in credentials (e.g., `api_key = ${BINANCE_SUB0_API_KEY}`) preferred over plain-text

## Hot-reload granularity

- **SIGHUP:** reload deployment-level (engine.cfg)
- **SIGUSR1:** reload all node configs (atomic; rollback on validation failure)
- **fox-cli reload-node-config <cluster>/<node>:** reload single node
- **fox-cli reload-cluster-config <cluster>:** reload single cluster
- Boot-time-only fields (e.g., exchange endpoints; CPU pinning) trigger refuse-reload + suggest restart

## Boot-time validation

```cpp
// Cross-file consistency checks at boot
for each node {
    assert(node.cluster_id in FOREACH_EXCHANGE);
    assert(node.subaccount_id < cluster.subaccount_count);
    assert(node.symbol is valid for cluster);
    assert(node.strategy_so exists and parseable);
}
```

Boot REFUSES on any validation failure; clear error message points to specific file:line.

## Stage progression criteria

- **Stage 3 first canonical** (`.E.1`): Deployment > Cluster > Node implemented for Binance
- **Stage 4 cohort** (when 2nd cluster added; Alpaca or operator-triggered): pattern proven across 2 exchanges
- **Stage 5 CLAUDE.md** (3rd cluster + discipline matures): promoted

## Anti-patterns avoided

- **Monolithic engine.cfg** — doesn't scale to multi-exchange + multi-sub-account
- **Per-node config in shared file with section markers** — file-locking + diff issues
- **Credentials in tracked files** — security risk
- **Mixed deployment/cluster/node settings in one file** — config explosion

## Cross-references

- Sister: `framework-patterns/foreach-exchange-meta-registry-pattern.md`
- Sister: `framework-patterns/hierarchical-config-with-per-node-folders.md`
- Sister: `framework-patterns/hierarchical-config-validation-pattern.md`
- Sister: `framework-patterns/runtime-mutable-vs-boot-time-config-pattern.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md`
- Implementation ship: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.2-headless-configs-docs.md`
