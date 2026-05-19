---
type: ledger-template
class_id: 1
title: Strategy lifecycle orphans
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 1 — Strategy lifecycle orphans

**Surface:** live (engine slow-path strategy dispatch).

**Symptom:** strategy adaptive behavior (regression-driven filter
tightening, trailing SL ratchet, regime-driven retune) silently
absent. Strategies "appear to work" because their entry gate fires,
but everything past entry behaves like a dumb cfg-static strategy.

**Root cause:** sharded port wired the entry point
(`Strategy_BuildParameters` dispatcher) but never plumbed the rest of
the lifecycle (`_Init`, `_Adapt`, `_BuySignal`, `_ExitAdjust`,
`Regime_AdjustPositions`). State structs (`MomentumState` etc.) were
defined but never allocated per-core; legacy callers were the only
ones invoking them.

**Detection:**
```bash
# Find functions called in legacy PortfolioController but not in the
# sharded entry points
tools/calls_graph_diff.sh
```
Functions with zero call sites in `engine_sharded` / `controller_event_loop`
but present in `portfolio_controller` are candidate orphans.

**Known instances:**
- v5.4.0 — all 5 strategies' `_Init`/`_Adapt`/`_ExitAdjust`/`_BuySignal`
  were orphaned. Fixed in commits `ad4fbb7..6049fa5` (Phase 1-2.5).

**Prevention:**
- Readiness skill Check 13 (strategy lifecycle completeness) — load
  before any plan touching strategies.
- `DOCS/STRATEGY_INTERFACE.md` — canonical 5-stage doc.
- `tools/calls_graph_diff.sh` — run as pre-merge gate when sharding
  any subsystem.
