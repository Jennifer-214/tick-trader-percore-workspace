# Partial Exits to Sharded — Plan

**Created:** 2026-04-27
**Status:** WRITTEN, DEFERRED. Code start gated on a validated
strategy that genuinely needs partial exits to be profitable.
Until then the workaround in `backtest.cfg` (`partial_exit_enabled=0`)
keeps train-serve consistent in single-exit mode.
**Seed notes:** `plans/post-v4.0-followups.md` lines 254-308.

## Why deferred

1. **No model validated as needing partials.** Wave 1 + Wave 2
   features haven't been retrained yet. Partial exits add
   complexity to capture a P&L distribution shape; no current
   evidence that distribution shape matters for any strategy
   we run.
2. **Hot path cost is real.** Adds ~2-4ns per tick on top of
   the current 40-400ns budget. Two `live_tp/live_sl` pairs per
   active core, branchless SG check on both. 5-10% of headroom
   spent for a feature that may not move the P&L needle.
3. **Workaround is cheap.** Set `partial_exit_enabled=0` in
   `backtest.cfg` → backtest matches sharded live (single exit
   per entry). Train models against that. ~30 minutes vs 4-5
   hours of hot-path surgery.
4. **Model selection criterion should match what live executes.**
   If a strategy needs partial exits to be profitable in
   backtest but live can't deliver them, the strategy is the
   problem, not the engine.

## Architecture (when this lands)

Legacy doesn't ratchet a single position from TP1→TP2. It opens
**TWO POSITIONS per entry signal** — leg A with TP=TP1, leg B
with TP=TP2, both share SL. They exit independently. See
`PortfolioController.hpp:1278-1281` and `Position::pair_index`.
`do_split` requires `Portfolio_CountActive + 2 <= max_positions`.

Sharded equivalent: **each core owns a PAIR of slots**, not one.
Effective max_positions per active entry halves. With 4 cores
and partials enabled, slots 0-7 are in play (vs 0-3 with
singles).

This is the right shape because:
- Hot path's "active core has its own TP/SL" pattern extends
  cleanly to "active core has TWO sets of TP/SL." No
  fundamental change to ExecutionCore_Tick's structure.
- Drainer handles pair coupling on slow path without touching
  the fast loop.
- Each leg is a real Position with its own slot, TP, SL — the
  data model matches legacy.

The alternative (ratchet single position from TP1→TP2 by
controller writing `live_tp` mid-trade) requires either an
atomic load on every hot-path tick OR a seqlock-style protocol
between controller and core. Both add cost to the most
performance-critical line in the engine. Rejected.

## Implementation phases

When code start is greenlit:

### Phase P.0 — Pre-work (½ day)

- Tag `pre-partial-exits` at HEAD. Push to origin.
- Branch `backup/pre-partial-exits-YYYY-MM-DD`. Push.
- Re-read this plan + the seed notes in
  `plans/post-v4.0-followups.md` lines 254-308.
- Re-walk the Plan Review Checklist § 1, 4, 6 (the GAPs the
  C+D plan flagged for C.3-style work; same shape applies here).

**Exit:** rollback story locked.

### Phase P.1 — Portfolio slot allocation (1 day)

- `Portfolio<F>`: confirm `MAX_POSITIONS=16` headroom for 4
  cores × 2 legs.
- `EventLoopState`: mark each registered core as
  "single-leg" or "pair-capable" per cfg.partial_exit_enabled.
- Validation: with `cfg.partial_exit_enabled=1` AND
  `cfg.num_execution_cores * 2 > MAX_POSITIONS`, refuse boot
  with clear error.
- Tests: per-core slot pair allocation; bitmap accounting;
  edge cases (3 cores → 6 slots; 8 cores → 16 slots → no headroom
  for non-pair singles, refuse).

### Phase P.2 — ExecutionCore hot path (1 day, the most careful)

- `ExecutionCore<F>`: add `live_tp_b`, `live_sl_b`, `entry_price_b`
  + a `pair_active` flag (uint8_t).
- `ExecutionCore_Tick`: when `pair_active=1`, evaluate
  SG_Evaluate on both legs branchlessly. Use mask-select to
  pick which leg fires (or both if same tick). Push an
  `event.leg = 0|1` field for the drainer to know which leg
  exited.
- Hot-path budget audit: measure cycles before/after with
  `LATENCY_PROFILING=ON`. Target ≤4ns added when pair_active=1;
  ≤1ns added when pair_active=0 (the unrealized-pair-capable
  branch).
- Tests: hammer test — 1M ticks with random TP1/TP2/SL hits
  on both legs; verify both legs exit independently; no
  double-counting; no missed exits.

**Verification gate:** if hot-path measurement shows >5ns added
when pair_active=0, redesign. The branch must be pre-pair-active
free.

### Phase P.3 — OMS HandleFill + drain (1 day)

- `OrderManager_HandleFill`: distinguish leg A vs leg B vs
  single position via `event.leg` + `core->pair_active`.
- Leg A close = ship TP1 P&L, leave leg B alone.
- Leg B close = ship TP2 P&L, mark pair closed (clear
  `pair_active`).
- `drain_with_submit`: pair coupling on the TradeEvent →
  OrderManager_Submit path; partial qty handled.
- Tests: leg-A-only exit; leg-B-only exit; same-tick A+B
  exits; SL hits on shared SL.

### Phase P.4 — Slow path build + tests (½ day)

- `Strategy_BuildParameters` per-strategy: when
  `cfg.partial_exit_enabled=1`, set leg A and leg B params on
  the core. `tp_pct_a = TP1`, `tp_pct_b = TP2 = TP1 * tp2_mult`,
  both `sl_pct = SL`.
- `breakeven_on_partial`: when leg A closes profitably, slow
  path can move leg B's SL to entry_price (if cfg flag set).
  Branchless ratchet.
- Backtest parity: same input → same trade count + P&L as
  legacy. Use `parity_harness` for one-shot validation.

### Phase P.5 — Documentation + ship (½ day)

- CLAUDE.md: add "partial exits invariant" section. Per-core
  pair slot rule. Hot-path cost note. Validation requirements.
- Changelog: dated file + version summary entry. Bump to
  v4.7.0 (Minor — new feature).
- Backtest.cfg + engine.cfg: doc comment about
  `partial_exit_enabled` capacity halving.

## Audit per Plan Review Checklist

Walk the 10 sections before each phase commits.

| § | Verdict | Note |
|---|---|---|
| 1 Hot path | NEED-AUDIT — Phase P.2 | Hot path cost is the load-bearing concern. Measure cycles with LATENCY_PROFILING at every commit in P.2. Target +1ns when pair_active=0, +4ns when active. Red-line at +5ns total. |
| 2 Train-serve | DOCUMENT divergence | Backtest sim of partial fills uses mid-price (no slippage on the second leg). Live uses real exchange semantics. Same divergence shape as C.3 maker-only — accepted, document. |
| 3 Surface | LARGE | Portfolio, ExecutionCore (hot), OrderManager (warm), drain_with_submit, Strategy_BuildParameters, tests, docs. ~6 files. |
| 4 Pointer init | VERIFY | New `live_tp_b/live_sl_b/entry_price_b/pair_active` are non-pointer state; no four-site rule. Confirm no stale fields leak across pair re-use. |
| 5 Backward compat | PASS | New cfg field already parsed (`partial_exit_enabled`); was a no-op in sharded; becomes meaningful. Existing `partial_exit_enabled=0` users see no change. |
| 6 Threading | NEED-AUDIT | `pair_active` written by controller (slow path) + read by core (hot path). Atomic discipline. Same as `permission`. |
| 7 Tests | PASS-by-plan | P.1-P.4 each have explicit test deliverables. Hammer test in P.2 + parity_harness in P.4. |
| 8 Docs | PASS-by-plan | P.5 is dedicated. |
| 9 Forward maintenance | PASS | Pair pattern extends to N-leg if ever needed (rare). Drainer handles via leg index. |
| 10 Rollback | PASS | Per-phase commits revertable; pre-partial-exits tag. |

## Open questions

1. **`max_positions` semantics with partials enabled.** Is
   `max_positions=4` "4 entries, 8 slots when paired" or
   "4 slots total, only 2 paired entries allowed"? Default to
   the former; user can opt to the latter via separate cfg
   field if needed.
2. **Per-core override of `partial_exit_enabled`.** Currently
   global. Some strategies might want partials, others not.
   Defer to per-core override post-launch.
3. **Snapshot persistence.** v8 → v9 bump for `live_tp_b` /
   `pair_active` fields. Document in changelog.
4. **`breakeven_on_partial` with regime adjustment.** If a
   regime change widens TP, does it apply to leg A, leg B, or
   both? Default: leg B only (leg A is effectively closed
   the moment regime tightens).

## Decision criteria for greenlight

Code start when:

- **A retrained model on v4.6 features (or later) shows
  meaningfully better performance with `partial_exit_enabled=1`
  vs `=0`** in walk-forward validation.
- OR a specific strategy under development requires the
  feature shape (rare; most strategies should be expressible
  in single-exit form).
- AND latency budget review shows the +2-4ns is acceptable
  given current p99 (40-400ns).

Until any of those: stay with the workaround
(`partial_exit_enabled=0` in backtest.cfg).

## Rollback story

`pre-partial-exits` tag at start of P.0. Each phase commit
individually revertable. If P.2 hot-path measurement comes in
worse than budget, revert P.2 + redesign before continuing.
