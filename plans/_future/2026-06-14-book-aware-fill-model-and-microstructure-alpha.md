---
type: future-roadmap
status: captured (post-E / data-gated; not scheduled — operator-confirmed 2026-06-14: the maker pipeline is DEFERRED until real orderbook data is in hand to work with)
established: 2026-06-14
sprint_origin: v5.15.5.F.4d.1.E.0.10 (#9 cohort-close discussion — the no_trade_band fee-band flag surfaced the liquidity-cost question)
gates_on: .E complete + real depth data at scale + an edge/alpha phase (per [[project_engine_done_edge_is_the_frontier]])
seams: [.E.1 FillEvent/fill-completeness/venue-net-reconcile, ML_Headers/FlowFeatures, RegimeSignals]
sister_docs: [plans/_future/2026-05-12-decoupling-endgoal-roadmap.md]
cross_ref_techdebt: [TECH_DEBT-175]
---

# Book-aware fill model + orderbook-microstructure alpha (two distinct future frontiers)

Captured 2026-06-14 from a Caramel design line-of-thought during the `.E.0.10` #9
cfg-flag-orphan close (the `no_trade_band` fee-breakeven flag is the coarse, existing
form of liquidity-cost awareness — which surfaced "is the orderbook actually factored
into fills/alpha?"). **Verdict: not a foundational mistake — a deliberate,
philosophy-consistent sequencing decision.** The honest gap is narrower and more
specific than "liquidity was left out," and it splits cleanly into TWO independent
items (one correctness, one alpha).

## What already exists (don't re-derive — verify, then build on)

- **Depth/orderbook is plumbed + deterministically replayable:** `DataStream/BinanceDepth`
  + `BookSnapshot<F>`, `DepthRecorder`, `DepthReplayState`, `depth_recorder_test`. The book
  is captured, recorded, and replayable.
- **Order-flow ML seam:** `ML_Headers/FlowFeatures` (a feature seam into the ML path).
- **Execution-cost modeling (coarse):** `slippage_pct` (pessimistic-by-default 0.05% — A9/D-203),
  taker/maker `fee_rate`. That IS liquidity-cost awareness — just a flat, coarse form.
- **The live ENTRY cost-gate (the enrichment home — DON'T build a new one):** `MASK_GATE_CFG_COST_GATE_ENABLED`
  (`StrategyParameters.hpp:1845-1873`) already vetoes an entry (sets `GATE_FLAG_BUY_BLOCKED` + `SHALT_COST_GATE`)
  when a real **market-impact cost model** (`CostModel_Estimate` — spread + volatility + order-size-vs-ADV impact,
  `COST_K1/K2/K3`) says total cost exceeds 50% of the expected gain (`tp_bps`). This is the sophisticated, live
  version of entry cost-gating — the legacy `no_trade_band` (crude `fee_rate × 3`) was its redundant twin.
  **The concrete near-term enrichment is already flagged in-code** at `StrategyParameters.hpp:1843`
  (`Future: thread spread_bps from CoreSlowState::spread_state`) — i.e. feed REAL book-derived spread/depth into
  `CostModel_Estimate` instead of the `spread_bps=0` placeholder. So when the orderbook data lands, entry
  cost-gating gets richer by **enriching `COST_GATE`'s inputs**, not by adding a gate.

## The two real gaps (independent — do not conflate)

### 1. Execution-fidelity gap (CORRECTNESS) — flat slippage → book-walk / market-impact
The fill model is a **flat-slippage approximation**, not a book-walk that consumes orderbook
*levels* to price a fill against actually-available liquidity (market impact). Plugs straight
into the **`.E.1` FillEvent / fill-completeness / venue-net-reconcile** work — that is the
groundwork a book-aware fill model attaches to.

### 2. Alpha gap (EDGE) — microstructure as a signal source
Orderbook microstructure as an **alpha source** (book imbalance, queue position, adverse
selection) is largely unexploited. `FlowFeatures` + `RegimeSignals` (the ML extensibility
seam) are the plug points; the signals are not yet deeply mined. This is the explicit
later frontier (edge/alpha), not a foundation item.

## When it actually matters (regime-dependent — flat slippage is fine *now*)

- **Small clips on liquid pairs (BTC/ETH-USDT):** flat pessimistic slippage is a perfectly
  defensible approximation — you barely walk the book. **Fine now.**
- **Larger size, thinner pairs, OR any maker/passive strategy:** book depth + queue dynamics
  become **first-order, not optional** — flat slippage will *lie* to backtests (optimistic
  fills, no market impact). This is the trigger to build item 1.

## Why deferring is philosophy-consistent (not a mistake)

Correctness-first live-readiness phase, deliberately building "a moldable shape" with edge/alpha
as the explicit later frontier ([[project_engine_done_edge_is_the_frontier]] +
[[user_mvp_to_professional_transition]]). The seams (FlowFeatures, RegimeSignals, the `.E.1`
FillEvent contract) are the groundwork these plug into. We **sequenced** liquidity behind the
foundation; we did not architect away from it.

## ⚠️ Precondition before either build — rule out Class-44 orphaning

Given this codebase's documented **Class-44 history** (values bound-but-unread /
produced-but-discarded — the bandit features silently logging zeros, A11/A12, is the canonical
case): treat "we capture depth + have FlowFeatures" with **healthy suspicion** until the
**produce→consume chain** for the depth/flow features is verified to actually drive *live*
(sharded) decisions, not be captured-but-orphaned. That verification is exactly what the
**struct-field produce/consume tracker = TECH_DEBT-175** (the AST endgame of the Class-44
closure) would catch at field granularity. So: **first prove the existing depth/flow seams are
live-consumed; then build on them.**

## Open shape decisions (for the future-self picking this up)
- Item 1 fill model: where does the book-walk live — drainer (`OrderManager_Tick` fill synth)
  vs a pre-trade impact estimate at the gate? (latency budget: the synth is drainer-cadence
  ≤10μs, not hot-path.)
- Item 1 inputs: which `BookSnapshot<F>` levels, how deep, decay/staleness handling on replay.
- Item 2 features: candidate microstructure features (book_imbalance already in RegimeSignals
  per `CoreFrameworks/CLAUDE.md` — verify it's live-consumed first, see precondition).
