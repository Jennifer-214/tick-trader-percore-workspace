---
type: meta-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.1
canonical_applications:
  - v5.15.5.F.4d.1.E.1 (4-step transition discipline codified)
sister_specs:
  - framework-patterns/per-node-paper-mode-flag-pattern.md (mode enum supporting this discipline)
  - meta-disciplines/structural-enforcement-when-memory-insufficient.md (M7; structural enforcement)
  - meta-disciplines/canonical-sister-extension-discipline.md
tags: [meta-discipline, strategy-lifecycle, backtest-to-live, drift-management]
surface: [strategy-development, paper-mode, capital-management]
applies_at_skills: [/parity-check, /post-ship-audit]
---

# Backtest → paper → live convergence discipline

**Pattern intent:** Strategy promotion from concept to production follows 4-step transition. Each step has different drift sources; mitigations per step. Sub-account isolation (per `per-node-economic-isolation-pattern.md`) supports gradual capital ramp.

## Problem statement

A strategy that "works in backtest" may not work in production due to:
- **Slippage:** backtest assumes mid-price fills; live has spread + impact
- **Latency variance:** backtest assumes instant; live has network + processing delay
- **Order rejection / partial fill:** backtest assumes fills; live can fail
- **Rate-limit:** backtest doesn't model; live may hit
- **Regime change:** backtest period may not match current market
- **Market microstructure:** backtest may use simplified order book; live is full

Direct backtest → live transition risks substantial capital loss. The 4-step transition catches drift sources progressively.

## Pattern description: 4-step transition

### Step 1: Backtest (historical data; simulated fills)

```
Mode: NODE_MODE_BACKTEST
Data source: Historical market data files
Fills: Simulated (mid-price assumption; configurable slippage model)
Capital: Synthetic; no real funds
Cadence: Run before each strategy variant promotion
Duration: Months of historical data
```

**Drift sources caught at this step:**
- Strategy logic bugs
- Bad parameter selection
- Bad feature engineering
- Severe regime mismatch

**Mitigations:**
- Multiple historical periods (regime-diversity)
- Walk-forward validation
- Held-out test set
- Statistical significance testing

### Step 2: Paper mode (real market data; simulated fills)

```
Mode: NODE_MODE_PAPER
Data source: REAL exchange market-data WS
Fills: Simulated (paper-fill module; configurable slippage)
Capital: Engine-tracked virtual capital
Cadence: 1-4 weeks per variant
Duration: Until performance metrics stabilize
```

**Drift sources caught at this step:**
- Real-time latency variance
- Real market microstructure (order book depth; bid-ask spread)
- Real volatility patterns
- Sister-node interaction (multi-node trading shares market)

**Mitigations:**
- Run paper-mode node ALONGSIDE existing live nodes (per-node mode flag enables this; per `per-node-paper-mode-flag-pattern.md`)
- Compare paper P&L to live P&L over same period
- Track latency distributions

### Step 3: Small-capital live (real submission; minimal funds)

```
Mode: NODE_MODE_LIVE
Data source: REAL exchange
Fills: REAL fills via exchange
Capital: $100-500 typically (small enough to absorb full loss)
Cadence: 2-4 weeks per variant
Duration: Until live performance matches paper expectations
```

**Drift sources caught at this step:**
- Submit latency in actual execution
- Order rejection / partial fill semantics
- Rate-limit interactions
- Real fill slippage (paper-mode slippage model may differ from reality)
- Real-money psychology (operator decision-making changes slightly with real $)

**Mitigations:**
- Per-sub-account isolation (loss bounded to small-capital sub-account)
- Tight kill switches (lower drawdown thresholds for small-capital node)
- Daily review of live P&L vs paper P&L expectations
- fox-cli rollback-strategy ready

### Step 4: Full live (gradual capital ramp)

```
Mode: NODE_MODE_LIVE
Capital: Gradually increased to target allocation
Cadence: Capital increases at performance milestones
Duration: Indefinite (production)
```

**Capital ramp policy (operator-defined):**

```
Week 1:  $500   (Step 3 baseline)
Week 2:  $1000  (if Step 3 met performance targets)
Week 4:  $2500  (full allocation)
Month 3: $5000  (if sustained performance + market regime confirmed)
```

**Drift detection ongoing:**
- Live performance compared to backtest + paper expectations
- Aggregator-driven kill switches (per `kill-switch-hierarchical-pattern.md`)
- Periodic re-backtest with updated data
- Strategy retirement workflow if performance degrades

## Operator workflow

```bash
# Step 1: Backtest
foxml-train --config training/momentum_v3.training.cfg
# Output: models/momentum_v3/ + backtest report

# Step 2: Paper-mode node
$EDITOR configs/clusters/binance/nodes/node_5/core.cfg
# Set: mode = paper; strategy = momentum; variant_id = v3
fox-cli add-node binance --sub-account 5 --node 5 --mode paper

# Compare paper node_5 to live node_0 over 2 weeks via fox-tui

# Step 3: Promote to small-capital live
$EDITOR configs/clusters/binance/nodes/node_5/core.cfg
# Set: mode = live; capital_allocation = 500
fox-cli reload-node-config binance/node_5
fox-cli transfer-funds --from binance:0 --to binance:5 --amount 500

# Step 4: Gradual ramp
# Week 2: fox-cli set-capital binance/node_5 1000
# Week 4: fox-cli set-capital binance/node_5 2500
```

## Stage progression criteria

- **Stage 3 first canonical** (`.E.1`): 4-step transition codified
- **Stage 4 cohort** (when 2nd strategy applied via this discipline): pattern proven
- **Stage 5 CLAUDE.md** (3rd application): promoted

## Anti-patterns avoided

- **Direct backtest → live transition** — substantial capital risk
- **Paper-mode in isolation** (not alongside live) — no comparison baseline
- **Capital ramp without performance milestones** — risk amplification without validation

## Cross-references

- Sister: `framework-patterns/per-node-paper-mode-flag-pattern.md` (enables this discipline)
- Sister: `framework-patterns/per-node-economic-isolation-pattern.md` (sub-account isolation for capital ramp)
- Sister: `framework-patterns/kill-switch-hierarchical-pattern.md` (per-node tight thresholds for small-capital)
- Operator doc: `DOCS/STRATEGY_LIFECYCLE.md` (lands at `.E.2`)
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md`
