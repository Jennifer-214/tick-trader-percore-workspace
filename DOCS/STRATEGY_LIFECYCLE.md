# Strategy Lifecycle

**Audience:** Operator developing + promoting trading strategies.

Per `meta-disciplines/backtest-paper-live-convergence-discipline.md` (DESIGN_SPECS). This doc is the operator-facing companion.

---

## The 4-step transition

Strategy promotion from concept to production follows 4 steps. Each step catches different drift sources.

```
1. BACKTEST (historical data; simulated fills)
   ↓ (months of historical validation)
2. PAPER MODE (real market data; simulated fills)
   ↓ (1-4 weeks alongside live nodes)
3. SMALL-CAPITAL LIVE (real submission; minimal funds)
   ↓ (2-4 weeks; $100-500)
4. FULL LIVE (gradual capital ramp)
```

---

## Step 1: Backtest

**Goal:** Validate strategy logic + parameters against historical data.

```bash
# Develop strategy
$EDITOR Strategies/MomentumV3.hpp

# Build .so (for hot-reload at .E.X)
./build.sh strategies

# Run backtest
foxml-train --config training/momentum_v3.training.cfg
```

**training/momentum_v3.training.cfg:**
```
strategy = momentum
feature_set = momentum_v3
label_config = labels/3bar_horizon.cfg
split = walk_forward_8week
hyperparams = momentum_v3_grid.cfg
training_window_start = 2024-01-01
training_window_end = 2026-05-01
output_dir = models/momentum_v3
```

**Pass criteria:**
- Walk-forward validation Sharpe > target
- Multiple market regimes covered
- Held-out test set Sharpe close to training
- Statistical significance verified

**Drift sources caught:** strategy logic bugs; parameter selection; regime mismatch.

---

## Step 2: Paper mode

**Goal:** Validate against REAL market data with simulated fills. Run ALONGSIDE existing live nodes for head-to-head comparison.

```bash
# Create paper-mode node alongside live nodes
$EDITOR configs/clusters/binance/nodes/node_5/core.cfg
# Set:
#   subaccount_id = 5
#   symbol = BTCUSDT
#   strategy = momentum_v3
#   mode = paper
#   capital_allocation = 1000  (virtual; not real funds)

# Activate
fox-cli add-node binance --node 5
```

**Watch for 1-4 weeks:**
- Paper P&L should track expected backtest P&L over similar conditions
- Latency distribution should match expectations
- Strategy reactions to volatility events should be sensible

**fox-tui shows paper P&L separately from live P&L** (aggregator tags by mode).

**Drift sources caught:**
- Real-time latency variance
- Real market microstructure (bid-ask spread; order book depth)
- Sister-node interaction
- Real volatility patterns

---

## Step 3: Small-capital live

**Goal:** Test with REAL money but bounded loss exposure.

```bash
# Promote paper node to live with small capital
$EDITOR configs/clusters/binance/nodes/node_5/core.cfg
# Change: mode = paper → mode = live
# Change: capital_allocation = 1000 (virtual) → 500 (real funds)

# Engine refuses promotion if open paper positions (operator must wait for flat)
fox-cli reload-node-config binance/node_5

# Transfer $500 from master to sub-account 5
fox-cli transfer-funds --from binance:master --to binance:5 --amount 500 --asset USDT
```

**Tight kill switches for small-capital node:**
```bash
# Lower drawdown threshold than default (15% vs 30% for production-tier)
fox-cli set-kill-threshold node binance/node_5 0.15
```

**Watch for 2-4 weeks:**
- Live P&L should match paper P&L expectations (within ±10%)
- Slippage should match paper-fill simulation
- Order rejections / partial fills handled correctly
- No unexpected behavior

**Drift sources caught:**
- Real fill slippage
- Submit latency in real execution
- Order rejection semantics
- Real-money decision-making

**If live diverges from paper substantially:** rollback strategy; investigate.

```bash
fox-cli rollback-strategy binance/node_5
# Returns to previous variant
```

---

## Step 4: Full live (gradual capital ramp)

**Goal:** Scale capital to target allocation. Monitor for sustained performance.

**Capital ramp schedule (operator-defined):**

```
Week 1:  $500   (Step 3 baseline)
Week 2:  $1000  (if Step 3 met targets)
Week 4:  $2500  (full allocation tier)
Month 3: $5000  (if sustained performance + favorable regime)
```

```bash
# Week 2 ramp
fox-cli transfer-funds --from binance:master --to binance:5 --amount 500 --asset USDT
# Sub-account 5 now has $1000

# Week 4 ramp
fox-cli transfer-funds --from binance:master --to binance:5 --amount 1500 --asset USDT
# Sub-account 5 now has $2500
```

**Ongoing monitoring:**
- Daily P&L vs backtest + paper expectations
- Aggregator-driven kill switches still active
- Per `feedback_motivated_collaborator_for_caramel`: quality bar maintained

**Periodic re-backtest:**
- Quarterly: re-run backtest with updated historical data
- Verify strategy still profitable in recent regime
- If degradation: pause node; investigate; possibly retire strategy

---

## Strategy retirement workflow

When strategy underperforms:

```bash
# 1. Pause node (no new positions)
fox-cli pause-node binance/node_5

# 2. Wait for open positions to close (or close manually)

# 3. Reassign node to different strategy
$EDITOR configs/clusters/binance/nodes/node_5/core.cfg
# Change: strategy = momentum_v3 → strategy = simple_dip

# 4. Reload
fox-cli reload-node-config binance/node_5

# 5. Resume
fox-cli resume-node binance/node_5
```

OR remove node entirely:

```bash
fox-cli remove-node binance/node_5
# Engine: close positions; stop threads; remove cfg
```

---

## A/B testing infrastructure

Run two strategy variants side-by-side:

```
Cores 0-3: momentum variant A
Cores 4-7: momentum variant B
```

```bash
# Configure each node's strategy variant
$EDITOR configs/clusters/binance/nodes/node_0/strategy.cfg  # variant_id = "momentum_a"
$EDITOR configs/clusters/binance/nodes/node_4/strategy.cfg  # variant_id = "momentum_b"

# Aggregator separates variants in metrics
# Prometheus query: fox_node_realized_pnl{strategy="momentum_a"} vs {strategy="momentum_b"}

# After sufficient sample: statistical significance check (operator-side; via Jupyter or similar)
# Promote winner; retire loser
```

---

## Tips

- **Don't skip steps.** Each step catches different drift; skipping risks substantial capital loss.
- **Paper mode is precious.** Use it; trust it; let it run weeks.
- **Small-capital live is the truth test.** Real money behaves differently than paper. Budget for it.
- **Capital ramp slowly.** Performance milestones first; capital later.
- **Document strategy evolution.** Each variant_id captures lineage; commit cfg changes to git.

---

**End of STRATEGY_LIFECYCLE.md v1.0** (2026-05-28).
