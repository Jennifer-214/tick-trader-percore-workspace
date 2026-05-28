---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.1
canonical_applications:
  - v5.15.5.F.4d.1.E.1 (4-state per-node mode enum; backtest|paper|live|shadow)
sister_specs:
  - framework-patterns/backtest-paper-live-convergence-discipline.md (sister discipline)
  - refactor-patterns/multi-bit-state-encoding-pattern.md (H14 MBS encoding)
  - framework-patterns/global-aggregator-readonly-pattern.md (aggregator separates paper P&L)
tags: [framework-discipline, per-node-mode, paper-trading, live-trading, shadow-mode, mbs-encoding]
surface: [per-node-state, submit-dispatch, aggregator]
applies_at_skills: [/precoding-audit-gate, /dod-audit, /parity-check]
---

# Per-node paper mode flag pattern

**Pattern intent:** Each per-node has a 4-state mode flag (`backtest | paper | live | shadow`). Per-node slow-path branches on mode at submit time. Aggregator tags P&L by mode (paper excluded from kill switch evaluation). Enables paper-test new strategies alongside live trading.

## Problem statement

Power-user operator wants to:
- Test new strategy variant alongside live-trading nodes
- Use REAL market data (not synthetic backtest data)
- Avoid risking capital while testing
- Promote new variant to live once validated

Without per-node mode flag: must restart engine to change mode; tests in isolation; can't compare live vs paper P&L head-to-head.

With per-node mode flag: each node independently chooses mode; aggregator separates totals; operator promotes via cfg change + hot-reload.

## Pattern description

### 4-state mode enum (H14 MBS encoding; 2 bits in uint8_t)

```cpp
enum NodeMode : uint8_t {
    NODE_MODE_BACKTEST = 0,    // Synthetic data; simulated fills (sister to existing Backtest_Run)
    NODE_MODE_PAPER    = 1,    // REAL market data; simulated fills (no exchange submission)
    NODE_MODE_LIVE     = 2,    // REAL submission to exchange; real fills (normal trading)
    NODE_MODE_SHADOW   = 3,    // Real submission; results IGNORED (for future colo testing; .E.8+)
};

// Per `multi-bit-state-encoding-pattern.md` H14 compliance:
// NodeMode = 2 bits (4 states); stored in uint8_t in NodeState.hot.mode
// NO C++ bitfield syntax; manual SHIFT/MASK if packed with sibling fields

// In NodeState.hot:
alignas(64) struct {
    // ... existing ...
    uint8_t mode;  // NodeMode; default NODE_MODE_PAPER for safety
    // ...
};
```

### Per-node slow-path submit dispatch

```cpp
void NodeSlowPath_SubmitOrder(NodeState<F>& node, SubmitCommand<F>& cmd) {
    switch (node.hot.mode) {
        case NODE_MODE_BACKTEST:
            // Synthetic data; simulated fill via backtest engine
            BacktestEngine_SimulateFill(node, cmd);
            break;
        case NODE_MODE_PAPER:
            // Real market data; simulated fill via paper-fill module
            PaperFill_Simulate(node, cmd);
            break;
        case NODE_MODE_LIVE:
            // Real submission via cluster adapter
            ClusterAdapter_Submit(node.binding.cluster_id, cmd);
            break;
        case NODE_MODE_SHADOW:
            // Real submission but flag result as shadow (for future colo testing)
            cmd.shadow_flag = 1;
            ClusterAdapter_Submit(node.binding.cluster_id, cmd);
            break;
    }
}
```

### Aggregator separates P&L by mode

```cpp
void Aggregator_OnFill(AggregatorState& agg, NodeState<F>& node, const FillEvent<F>& fill) {
    if (node.hot.mode == NODE_MODE_LIVE || node.hot.mode == NODE_MODE_SHADOW) {
        // Real money; counts toward global + cluster totals; kill switch evaluation
        FPN_AtomicAdd(&agg.global.cached_total_realized_pnl, fill.net_pnl);
        // ...
    } else {
        // Paper / backtest; tagged separately; excluded from kill switch
        FPN_AtomicAdd(&agg.paper_realized_pnl[node.binding.cluster_id], fill.net_pnl);
        // ...
    }
}
```

### Operator workflow

```bash
# Start new node in paper mode
fox-cli add-node binance --sub-account 5 --symbol AVAXUSDT --strategy ml --mode paper

# Promote to live after validation
$EDITOR configs/clusters/binance/nodes/node_5/core.cfg
# Change: mode = paper → mode = live
fox-cli reload-node-config binance/node_5

# Engine validates: refuses promotion if node has open paper positions
# Engine validates: refuses promotion if sub-account doesn't have allocated capital
# Engine logs the promotion in audit log
```

### Per-cluster mode aggregation

fox-tui displays per-node mode + separates totals:

```
binance/node_0: BTCUSDT  momentum  LIVE   P&L +$182  (real)
binance/node_1: ETHUSDT  ml         PAPER  P&L +$67  (paper; not counted)
binance/node_2: SOLUSDT  simple_dip LIVE   P&L -$23  (real)
binance/node_3: BTCUSDT  ema_cross  SHADOW P&L +$15  (real submit; not counted; shadow)
```

Aggregate: real P&L = $159 (live); paper P&L = $67; shadow P&L = $15 (tracked separately).

## Stage progression criteria

- **Stage 3 first canonical** (`.E.1`): 4-state mode + submit dispatch + aggregator separation
- **Stage 4 cohort** (when 2nd application surfaces; e.g., test-mode bandit): pattern proven
- **Stage 5 CLAUDE.md** (3rd application + discipline matures): promoted

## Anti-patterns avoided

- **Single paper-vs-live engine instance** — restart required for mode change; no live+paper coexistence
- **Branchy mode check on hot path** — mode check is at slow-path (NOT hot path); hot path branchless via cached strategy pointer
- **Mode as separate engine instances** — operator overhead; can't compare head-to-head

## Cross-references

- Sister: `framework-patterns/backtest-paper-live-convergence-discipline.md` (4-step transition discipline)
- Parent: `refactor-patterns/multi-bit-state-encoding-pattern.md` (H14)
- Sister: `framework-patterns/global-aggregator-readonly-pattern.md` (paper P&L separation)
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md`
