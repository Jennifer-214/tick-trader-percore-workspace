---
type: ledger-template
class_id: 10
title: Strategy-regime mismatch
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 10 — Strategy-regime mismatch

**Surface:** live (regime classifier → strategy dispatch coupling).

**Symptom:** A strategy fires entries in regimes where its
contract doesn't make sense (e.g. MOM buying breakouts in RANGING
markets where every breakout reverts), accumulating fee-only losing
trades.

**Root causes (any of):**
1. Hardcoded strategy assignment (`core_N_strategy=momentum`) —
   strategy fires regardless of regime classification.
2. Regime hysteresis flicker — classifier briefly flips to TRENDING
   during noise, AUTO core enters MOM, classifier returns to
   RANGING, position sits at fees-only loss.
3. Classifier-threshold mis-tuning — classifier decides TRENDING in
   actually-ranging markets.
4. Strategy filter too loose — strategy's BuySignal accepts
   marginal entries that can't survive fees + slippage.

**Detection:**
```bash
# Per-strategy x per-regime quality breakdown from health.jsonl
jq -s 'group_by(.cat=="entry") | .[] | select(.[0].cat=="entry") |
  group_by(.msg | capture("strat=(?<s>[0-9]+) regime=(?<r>[0-9]+)").s + ":" + .r) |
  map({key: .[0].msg, count: length})' health.jsonl
# Look for cells where MOM has many entries in regime=0 (RANGING)
# with negative net bps in the matching exits.

# Or use the v5.7.6 GUI Strategy Quality panel — same data via Refresh.
```

**Known instances:**
- v5.7.0 — 2026-04-30 paper run: Core 0 hardcoded MOM entered in
  RANGING regimes, took 16+ near-flat trades that lost fees only.
  Audit (`DOCS/changelogs/2026-04-30-regime-classifier-audit.md`)
  confirmed the regime classifier itself was healthy — Core 0's
  hardcoded assignment bypassed regime gating entirely.

**Prevention:**
- v5.7.2 — boot guard refuses live mode with hardcoded strategies
  unless `acknowledge_hardcoded_strategy_in_live=1` is set explicitly.
  Paper mode warns. Boot abort path emits health log
  `cat="engine"` `boot_abort` line.
- v5.7.5 — MOM-specific quality filters
  (`momentum_min_tp_margin_pct`, `momentum_min_r2`,
  `momentum_min_buy_delta_recent`) gated cfg-side. Default off
  preserves pre-v5.7 behavior; operator opts in after observing
  v5.7.6 quality dashboard data.
- v5.7.6 — per-strategy quality dashboard panel surfaces the
  pattern at-a-glance: any strategy showing many entries in a
  "wrong" regime with negative net bps is the smoking gun.
