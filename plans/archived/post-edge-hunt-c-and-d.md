# Post-Edge-Hunt Plan — Tracks C + D (revised 2026-04-26)

**Revised:** 2026-04-26 overnight, after master roadmap audit + Track E
plan. Major changes from prior version:

- **D.5 (depth replay) absorbed into Track E.3** — see
  `plans/track-e-sharded-backtest.md`. Removed from this plan to
  avoid two docs driving the same work.
- **D.1 reclassified: BLOCKED on E.3.** Prior version marked it
  "train-serve safe today" — incorrect. Backtest doesn't replay
  depth, so `book_imbalance=0` in backtest features. Real fix is
  E.3.
- **D.3 (spread dynamics) gate updated:** was `blocked by D.5`,
  now `blocked by E.3`.
- **C.1 / C.2 status updated** — partially shipped via v4.4 prep.
- **Sequencing rewrite** — old "Week 1: parallelize C.1+C.2 with
  D.1+D.4" assumed train-serve safety that didn't hold. New
  sequence respects Track E gating.

**Companion docs:**
- `plans/master-roadmap.md` — Track C/D's place in the whole arc.
- `plans/track-e-sharded-backtest.md` — the principled fix that
  unblocks D.1 and D.3.

**Goal (unchanged):** turn the verified short-horizon signal
(0.050/1000, +8 lift over random) into something tradeable AND
extend the feature pack to potentially unlock medium-horizon
prediction.

**Status going in:** v4.3 features (25-feature pack) didn't unlock
medium horizon (38% val on 0.250/10000 vs 58.8% baseline). The
0.050/1000 config remains the only configuration with statistical
lift.

---

## Track C — Lower Fees / Tradeable Execution

### C.1 — BNB fee discount **(SHIPPED — v4.4 prep)**

Already in `ControllerConfig.hpp` as `pay_fees_in_bnb`. Set fee_rate
to 0.000675 (0.075% × 0.9 BNB discount) at OMS init when enabled.
Round-trip cost drops from ~6 bps to ~3 bps — 5bps signal becomes
borderline-tradeable.

**Manual step still pending:** verify Binance account is set to pay
fees in BNB via web UI.

### C.2 — Per-fee-tier accounting awareness

**Effort:** 1-2 hours. **Risk:** low.

- Cfg field `binance_vip_tier` (0-9)
- Lookup table for tier → maker/taker rates
- Engine logs "expected fee rate for tier N: maker=X taker=Y"
- Lets you see if VIP volume threshold is worth chasing

**Checklist verdict (full):** all PASS. Display + cfg only, no
hot-path or feature surface.

### C.3 — Maker-only execution infrastructure (the big one)

**Effort:** 1-2 weeks. **Risk:** medium-high.

The bulk of Track C value sits here. With Binance maker fees at 0.012%
(VIP 0) → ~2.4 bps round-trip, even tight 5bps barriers become
tradeable at >70% accuracy. This is the multiplier.

Required changes:
- `BinanceAdapter`: add `submit_limit_buy(price, qty, post_only=true)`,
  `submit_limit_sell(price, qty, post_only=true)`, `cancel_order(id)`
- OMS state: track working limit orders, handle partial fills, age-based
  cancel/replace
- Strategy decision: when ML says "buy", submit limit at bid (or
  bid - 1bp). Wait N seconds for fill. If unfilled, cancel + maybe
  market in (taker fallback) or skip the trade
- Cfg: `ml_maker_only=1`, `ml_maker_offset_bps=1`, `ml_maker_timeout_secs=30`,
  `ml_maker_fallback_taker=0` (default: skip if no fill)
- Tests: limit order lifecycle, partial fill, cancel-replace, timeout
- Hot path implications: fills come back via user-data WS as before;
  no hot-path change. Slow path now manages working orders.

Sub-phases:
- C.3.1 — adapter limit-order primitives (3 days)
- C.3.2 — OMS working-order state + lifecycle (3 days)
- C.3.3 — ML strategy maker decision logic (2 days)
- C.3.4 — tests + paper soak (2-3 days)

**Independence from Track E:** C.3 changes execution semantics, not
feature production. Can run in parallel with E *after* E.2 (multi-
strategy support) lands so backtest exercises the new ML/maker logic.

**Checklist verdict — pre-flight:**

| § | Verdict | Note |
|---|---|---|
| 1 Hot path | NEED-AUDIT | Limit order tracking on slow path is fine. Need to check that `OMS_Tick` slow-path additions don't bleed into hot path. |
| 2 Train-serve | DEFERRED parity | Backtest will simulate maker fills via mid-price; live uses real exchange semantics. **Document the divergence** before C.3 starts. |
| 3 Surface | LARGE | OMS state, BinanceAdapter, strategy logic, several cfg fields, multiple tests. ~6-8 files. |
| 4 Pointer init | NEED-AUDIT | Working-order tracking is new heap state. Apply four-site rule. |
| 5 Backward compat | PASS | Additive cfg, additive OMS state. |
| 6 Threading | NEED-AUDIT | Working-order state is read by both slow path and user-data WS thread. Atomic discipline required. |
| 7 Tests | PASS-by-plan | Sub-phase C.3.4 dedicated to tests. |
| 8 Docs | PASS-by-plan | Will update Safety Invariants with maker-only rules. |
| 9 Forward maintenance | OK | Working-order pattern reusable for any strategy. |
| 10 Rollback | PASS | Pre-C.3 tag, sub-phases revertable. |

**Outcome:** plan accepted as roadmap item; **re-audit before each
sub-phase starts** because GAP items (1, 4, 6) are real.

### C.4 — Lower-fee venue (alternative path)

**Effort:** 1 week. **Risk:** medium. **Status:** alternative to C.3,
not parallel.

If C.3 is too much surgery, alternative is migrating to Bybit/OKX which
have better fee structures. Adapter rework, ws plumbing changes, but
no maker-order infrastructure needed.

Pros: gets lower fees with less surgery than C.3.
Cons: lose Binance-specific tooling (depth feed, archive backfill scripts).
**Defer this unless C.3 stalls.**

---

## Track D — Deeper Microstructure Features

### D.1 — Book imbalance over time **(BLOCKED on Track E.3)**

**Effort:** 4-6 hours of feature work + Track E.3 prerequisite.
**Risk:** low (after E.3).

You already have current `book_imbalance` from Phase 8a depth feed —
*in live*. Backtest doesn't replay depth, so this feature is
**train-serve unsafe** until Track E.3 ships depth replay.

What's missing in features: the *time series* of imbalance. Models
predicting medium-horizon moves benefit from "imbalance has been
one-sided for the last 30s" not just "imbalance is one-sided right
now."

After E.3 ships:
- New state: ring buffer of recent book_imbalance samples (e.g. 1024)
- Compute features: `book_imb_mean_short`, `book_imb_mean_long`,
  `book_imb_drift` (current - mean)
- 3 new FEAT_* constants. Bump MODEL_NUM_FEATURES + VERSION.

**Checklist verdict (post-E.3):** all PASS — single-source-of-truth
in `Regime_ComputeSignals`, both paths get it for free.

### D.2 — Trade-flow asymmetry over time

**Effort:** 6-8 hours. **Risk:** medium (touches tick aggregation).
**Status:** train-serve SAFE today (uses tick data, not depth).

Beyond CumDelta (already added in v4.3): **time-decayed buyer/seller
aggression**. Recent imbalance matters more than historic. Three
half-lives matter (10s, 1min, 5min) — different signals at each.

- New struct: `FlowState<F>` with three EWMA accumulators at different
  half-lives
- Push tick volume + is_buyer_maker through it
- Features: `flow_10s`, `flow_1m`, `flow_5m`
- 3 new FEAT_* constants

**Checklist verdict:** PASS. `is_buyer_maker` already plumbed through
`Tick<F>` (v4.3 work). Both paths populate identically.

**Pre-Track-E status:** can ship today, must update both legacy
backtest path AND sharded path.
**Post-Track-E status:** simplifies — one update site.

### D.3 — Spread dynamics **(BLOCKED on Track E.3)**

**Effort:** 4-6 hours, blocked by Track E.3.

- `FEAT_SPREAD_BPS`, `FEAT_SPREAD_ZSCORE`
- 2 new FEAT_* constants

After E.3: spread features readable from `DepthReplayState` (backtest)
and `DepthSharedState` (live). Single-source-of-truth in
`Regime_ComputeSignals`.

### D.4 — Large-trade detection

**Effort:** 3-4 hours. **Risk:** low.
**Status:** train-serve SAFE today (uses tick data only).

Whales move markets. When a single trade is >5% of recent rolling
volume, that's a signal worth feeding the model.

- State: rolling window of recent trade sizes
- Feature: `large_trade_z` (z-score of current trade size vs window)
- 1 new FEAT_*

**Checklist verdict:** PASS. Same as D.2 pre-vs-post E logic.

### D.5 — **MOVED to Track E.3**

Originally "Depth replay in backtest." Now lives at
`plans/track-e-sharded-backtest.md` E.3. Removed from this plan.

---

## Sequencing — what to do in what order (revised)

**The change vs. prior version:** D.1 and D.3 are now blocked on Track
E.3 instead of "train-serve safe today" / "blocked on D.5." D.5 is
gone (absorbed into E.3).

### Now → Track E ships (~7-10 days)

Track E is the active build per master roadmap. C/D items are dormant
during this period unless they're train-serve safe AND we want a
short break from Track E.

**Optional during-E work (low-risk, train-serve safe):**
- C.2 (fee tier display, ~1-2 hours) — pure GUI/cfg.
- D.4 (large-trade detection, ~3-4 hours) — feature add. Touches
  both legacy and sharded paths *for now*. Will simplify post-E.

**NOT during-E:** D.1, D.3 (blocked on E.3); D.2 (touches both
paths, easier post-E); C.3 (large lift, needs focus).

### After Track E ships (D.1, D.3 unblocked; everything simpler)

**Wave 1 (low-risk feature additions, ~1-2 days):**
- D.1 (book imbalance over time) — finally train-serve safe.
- D.2 (flow asymmetry).
- D.4 if not done during E.

**Wave 1 retrain decision point:**
- If val accuracy clears majority baseline → continue to D.3.
- If not → skip ahead to C.3 (the big maker-order work).

**Wave 2 (~1 week):**
- D.3 (spread dynamics).
- Retrain at 0.150/5000 + 0.250/10000 with full v4.5 feature pack.

**Wave 3 (~1-2 weeks):**
- C.3 — maker-order infrastructure. The big lift. Requires
  re-audit against the checklist before each sub-phase commits.

**Wave 4 (only if needed):**
- C.4 (venue migration) if C.3 stalls or Binance becomes hostile.

## Decisions to lock in

1. **Are we committing to live trading on Binance?** If yes, C.3 is
   the main effort. If maybe-might-switch-venues, defer C.3 in favor
   of C.4 prep.
2. **Maker timeout fallback policy:** if a maker order doesn't fill
   within N seconds, do we (a) skip the trade entirely (preserve
   maker-only economics) or (b) market in as taker (capture the
   signal at higher cost)? Default to (a) — easier to validate.
3. **Feature pack version cadence:** every D.x is a MODEL_FORMAT_VERSION
   bump. Batch into v4.5 (D.1+D.2+D.4 post-E), v4.6 (D.3+E features)
   so users only retrain at clean breaks.

## Risks (revised)

| Risk | Mitigation |
|---|---|
| Track E delay extends Wave 1 schedule | Track E exit criteria are tight; risk mostly internal to E |
| C.3 limit order races / partial fills break model assumptions | Paper-soak in maker-only mode for 1+ week before live |
| New features overfit on training without paper validation | Walk-forward gap monitoring; held-out lock-token discipline (Phase 7prep) |
| Multiple FEAT_* version bumps invalidate saved Runs | Group bumps into v4.5, v4.6 batches; document migration in changelogs |
| Maker-only with no fallback = missed trades when market moves fast | Track fill-rate metric; tune offset/timeout based on real data |
| Post-E D.x items still get feature divergence | Track E.6 parity harness is the firewall — if it passes, divergence won't happen |

## Success criteria

- Track C: round-trip costs reduced from 6 bps to <3 bps (BNB tier)
  or <2.5 bps (maker-only). At least one tradeable model with positive
  expected P&L on held-out walk-forward folds.
- Track D: at least one config (any barrier/lookahead pair) with val
  accuracy clearing majority baseline by >5 percentage points on
  Walk-Forward, with overfit_folds = 0.

If both criteria hit: **stop, paper-soak the winning config for 1
week, then go live with $10-50 stake.**
