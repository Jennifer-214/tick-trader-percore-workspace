---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.5
canonical_applications:
  - v5.15.5.F.4d.1.E.5 (per-cluster reserve_pct + max_per_node_pct)
sister_specs:
  - framework-patterns/per-node-economic-isolation-pattern.md (sister; sub-account isolation)
  - framework-patterns/global-aggregator-readonly-pattern.md (aggregator enforces policy)
  - framework-patterns/kill-switch-hierarchical-pattern.md (sister safety)
tags: [framework-discipline, capital-allocation, risk-management, reserve, max-per-node]
surface: [capital-management, risk-limits, aggregator]
applies_at_skills: [/precoding-audit-gate, /accounting-audit]
---

# Capital allocation policy pattern

**Pattern intent:** Per-cluster cfg defines `reserve_pct` (% capital always reserved; never deployed) + `max_per_node_pct` (no single node holds > X% of cluster's deployable capital). Aggregator enforces at submit time; refuses submissions that would breach policy.

## Problem statement

Multi-node trading risk management:
- Need RESERVE: never deploy 100% of capital (liquidity for emergency; market-making margin; etc.)
- Need PER-NODE CAP: no single node concentrated risk
- Need ENFORCEMENT: software refuses to breach policy

Without enforcement: operator-discipline only; bug or misconfiguration could over-leverage.
With aggregator-enforced policy: structural safety.

## Pattern description

### Per-cluster cfg

```
# configs/clusters/binance/cluster.cfg:
[capital_policy]
reserve_pct = 0.20             # 20% always in master account; never deployed
max_per_node_pct = 0.30        # No single node holds > 30% of cluster deployable
```

### Aggregator enforcement at submit time

```cpp
bool AggregatorEnforcement_CanSubmit(EngineState<F>& state, NodeState<F>& node,
                                      const SubmitCommand<F>& cmd) {
    uint32_t cluster_id = node.binding.cluster_id;
    ClusterState<...>& cluster = state.clusters[cluster_id];

    // Compute total cluster capital (master + N sub-accounts)
    FPN<F> total_capital = GetTotalClusterCapital(cluster);

    // Compute reserve required
    FPN<F> reserve = FPN_Mul(total_capital, FPN_FromDouble(cluster.cfg.reserve_pct));
    FPN<F> deployable = FPN_Sub(total_capital, reserve);

    // Check reserve constraint
    FPN<F> current_deployed = GetTotalDeployedInCluster(cluster);
    FPN<F> proposed_deployed = FPN_Add(current_deployed, cmd.notional);
    if (FPN_Greater(proposed_deployed, deployable)) {
        LOG_WARN("Reserve breach refused");
        return false;
    }

    // Check per-node cap
    FPN<F> max_per_node = FPN_Mul(total_capital, FPN_FromDouble(cluster.cfg.max_per_node_pct));
    FPN<F> proposed_node_deployed = FPN_Add(node.slow_account.open_notional, cmd.notional);
    if (FPN_Greater(proposed_node_deployed, max_per_node)) {
        LOG_WARN("Per-node cap breach refused");
        return false;
    }

    return true;
}
```

### Worked examples (per `.E.5` plan body)

Cluster with $10,000 capital; reserve 20%; max_per_node 30%:
- Master: $2,000 (reserve)
- Deployable: $8,000
- Max per node: $3,000

Sub-account 0 attempts +$3,000 position:
- Current sub-0 deployed: $2,000
- Proposed sub-0 deployed: $5,000
- BREACH: $5,000 > $3,000; REFUSE

Sub-account 2 attempts +$1,000 position (current $1,800):
- Current cluster deployed: $7,800
- Proposed: $8,800
- BREACH: $8,800 > $8,000 deployable; REFUSE

### Operator visibility

fox-tui shows per-cluster capital state:
```
binance: $10,000 total | $2,000 reserve (20%) | $8,000 deployable | $7,800 deployed (97%)
  sub-0: $2,000 deployed (max $3,000)
  sub-1: $1,800 deployed (max $3,000)
  sub-2: $1,800 deployed (max $3,000)
  sub-3: $2,200 deployed (max $3,000)
```

### Capital rebalance via internal-transfer

```bash
# Transfer $500 from sub-0 to master (reduce sub-0 cap)
fox-cli transfer-funds --from binance:0 --to binance:master --amount 500 --asset USDT

# Engine reconciles; aggregator updates totals
```

## Stage progression criteria

- **Stage 3 first canonical** (`.E.5`): per-cluster reserve + max_per_node enforced
- **Stage 4 cohort** (when 2nd application: e.g., per-strategy budgets): pattern proven
- **Stage 5 CLAUDE.md** (3rd application): promoted

## Anti-patterns avoided

- **Operator-discipline-only enforcement** — bugs/misconfigs slip through
- **Per-node only cap** — cluster-wide reserve not enforced
- **Single cap value for all nodes** — operator can't differentiate per-node risk

## Cross-references

- Sister: `framework-patterns/per-node-economic-isolation-pattern.md`
- Sister: `framework-patterns/global-aggregator-readonly-pattern.md`
- Sister: `framework-patterns/kill-switch-hierarchical-pattern.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.5-real-subaccounts-capital-framework.md`
