# Strategy Profitability Fixes — Master Plan (2026-04-29)

## Why this matters

Overnight v5.1.2 soak: **0W/10L, -$39.86 (-0.40%) in ~5 hours**.

The engine is correct (parity_harness 0-drift, 739 tests, no crashes).
What's broken is the strategy layer:

| Pattern | Count | Gross | Fees | Net |
|---|---|---|---|---|
| "TP" exits at +0.1% | 8 fills | +$0.74-0.92 | $1.50 | **−$0.76 each** |
| "SL" exits at real loss | 12 fills | −$2.86 to −$4.36 | $1.50 | −$4 to −$6 each |

**The "TP" exits aren't actually TP fires** — they're price-direction labels.
With `core_1_take_profit_pct=1.00` (1%), TP target = entry × 1.01 ≈ $76466.
Actual exits fire at +0.1% (≈ $75783). **Something is closing positions
~10× earlier than configured TP.** Combined with 0.1% taker fees × 2 sides
= 0.2% round-trip floor, every "winning" trade is a net loss.

## Root-cause hypotheses (priority order)

### H1: Trailing-SL ratchet firing prematurely (most likely)
EmaCross has its own `ExitAdjust` that mutates `pos->take_profit_price` /
`pos->stop_loss_price`. The slow-path `EventLoop_TrailingSLRatchetOneCore`
also writes `ratchet_sl` to pending_params. When `ratchet_sl > sl`, the
hot-path SG uses `effective_sl = max(sl, ratchet_sl)`. If the ratchet is
moving SL above entry within the first ~0.1% of price action, exits fire
on noise.

Evidence: `tp_hold_score=0.10` (10% gain required to ratchet) should
prevent this — but EmaCross_ExitAdjust uses different logic and may
fire independently.

### H2: Position size too small for fee absorption
`risk_pct=10%` / 4 cores = 2.5% / core × $10000 balance × `partial_exit_pct=0.5`
= $125 per leg. Two legs = $250 / trade total. At 0.1% gross, that's $0.25
profit — way under $1.50 fees.

Actually trade log shows $750 notional per leg. Sizing math is more nuanced
than my back-of-envelope. Worth verifying the actual sizing formula.

### H3: EmaCross strategy is structurally lossy in low-vol
EMA enters on dips below EMA in uptrend, then exits on the FIRST upward
move. In a low-vol grind, "the first upward move" is 0.1% noise. The
strategy is essentially "buy noise, sell at first wiggle, lose to fees".

Fixing the trailing wouldn't fix this — the gate itself fires too eagerly.

## Phase 1: Diagnostic verification (~30 min) — DO FIRST

**Goal**: identify EXACTLY what's closing the +0.1% positions. Without
this, Phase 2-3 fixes are guesswork.

### Edits

1. **Add exit-reason logging** to OMS_HandleFill exit branch:
   ```cpp
   // Determine which gate fired this exit:
   // - SG_TP: tick.price >= live_tp (or take_profit_price)
   // - SG_SL: tick.price <= effective_sl (or stop_loss_price)
   // - TIME:  came via EventLoop_TimeExitOneCore force-close
   // - TRAIL: came via ExitAdjust mutation of pos->take_profit_price/stop_loss_price
   // - MANUAL:came via drag_slot or manual_close_requested
   ```
   Emit one line per fill: `[exit] core %d slot %d reason=%s entry=%.2f exit=%.2f
   gain_pct=%.4f live_tp=%.2f live_sl=%.2f ratchet_sl=%.2f`

2. **Log EmaCross_ExitAdjust modifications**:
   ```cpp
   // before mutation
   double old_tp = FPN_ToDouble(pos->take_profit_price);
   // after mutation
   if (FPN_ToDouble(pos->take_profit_price) != old_tp) {
       fprintf(stderr, "[ema-trail] slot %d: tp %.2f → %.2f (price=%.2f)\n", ...);
   }
   ```

3. **Log EventLoop_TrailingSLRatchetOneCore mutations** (already partially
   done — augment to include current_price + entry_price + gain_pct).

### Gate
Restart engine on v5.1.4, run for 30-60 min, capture `engine.log`. Find
the first 5 exits and grep for `[exit]` reasons. **DO NOT proceed to
Phase 2 without this evidence**.

### Acceptance
We can answer: "what gate fired this position close?" for every exit in
the log.

---

## Phase 2: Fix the early-exit mechanism (~1-2h, depends on Phase 1)

### If H1 confirmed (trailing ratchet)

- **Add fee-floor guard to TrailingSLRatchet**: don't ratchet `ratchet_sl`
  above `entry × (1 - 3 × fee_rate_taker)`. Even if the slow-path WANTS to
  trail tight, the floor prevents net-negative exits.

  ```cpp
  FPN<F> sl_floor = FPN_Mul(entry_price, FPN_FromDouble<F>(1.0 - 3 * fee_rate));
  pending_params.ratchet_sl = FPN_Min(new_ratchet, sl_floor);
  ```

- **Same guard inside `EmaCross_ExitAdjust`** before any
  `pos->stop_loss_price` write.

### If H2 confirmed (sizing)

- Add `min_notional_per_trade` cfg (default `3 × fee_rate × max_position_value`).
- In `Strategy_BuildParameters`, if computed `trade_size × entry < min_notional`,
  set `GATE_FLAG_BUY_BLOCKED`. Logs once per cycle.

### If H3 confirmed (strategy structurally lossy)

- Disable EmaCross's `ExitAdjust` entirely; keep static TP/SL.
- Loosen entry: require gain_pct ≥ 3 × fee_rate before TP can fire (effectively
  raises minimum TP target).

### Gate
Re-run synthetic backtest on yesterday's day. Compare exit-reason histogram
before/after. Acceptance: ratio of "TP at fee-floor" exits drops below 30%.

---

## Phase 3: Runtime fee-floor gate (~1h)

Independent of Phase 2 root cause. Belt-and-suspenders.

### Edit
In `Strategy_BuildParameters` dispatcher, after each strategy's emit:

```cpp
double tp_dist_pct = (FPN_ToDouble(out->sg_take_profit_price) -
                     FPN_ToDouble(out->bg_price_threshold)) /
                    FPN_ToDouble(out->bg_price_threshold);
double fee_floor = 3.0 * FPN_ToDouble(cfg.fee_rate_taker);
if (tp_dist_pct < fee_floor) {
    out->flags |= GATE_FLAG_BUY_BLOCKED;
    // logged once per slow-path cycle, not per tick
}
```

Catches the dynamic-TP-collapse case (EMA's stddev-based when stddev is
small). Static cfg too-tight already warned at boot in v5.1.3.

### Gate
Synthetic run shows `BUY_BLOCKED` count > 0 when stddev is low; entry
count drops; no entries fire that would have been net-negative.

---

## Phase 4: Per-core risk re-balancing (~30 min)

### Diagnose
What is the actual sizing for tonight's $750 notional? Walk
`Strategy_BuildParameters` → `out->trade_size` → OMS_PushSubmit → fill_qty.

### Edit
- Either raise `risk_pct` defaults (fee-tractable sizing for paper)
- Or add per-core `core_N_min_notional` cfg
- Document the trade-off: higher size = bigger drawdown if SL fires

### Gate
Same paper run shows fills with notional ≥ 3× fee floor.

---

## Phase 5: Strategy-regime fit audit (~2-3h)

### Goal
For each (strategy, regime) pair, compute on yesterday's tick day:
- Number of entries
- Win rate
- Net P&L
- Avg hold time

Output: table showing which combinations have edge, which are pure friction.

### Tool
Use the existing `parity_harness` infrastructure + extend with a per-regime
breakdown. Or hack a one-off script reading the trade log + engine log.

### Decision
- Strategies with consistently negative edge → disable in cfg or remove from AUTO routing
- Strategies with regime-specific edge → restrict AUTO to route them only in those regimes
- Regimes with no covering strategy → flag as "needs new strategy or ML"

---

## Phase 6: ML route (~1-2 days, separate session)

Already plumbed (`STRATEGY_ML`, `CoreModelZoo`, `ModelInference`,
`ConfidenceScorer`, `BarrierGate`). What's needed:
- Train a model on `data/BTCUSDT/2024-04-28.csv` via foxml_suite
- Verify IC + RMSE + walk-forward gap < 0.05
- Assign one core to STRATEGY_ML, soak overnight, compare to classical zoo

Out of scope for this plan — track separately in `plans/2026-04-XX-ml-bringup.md`.

---

## Versioning plan

| Version | Phase | Notes |
|---|---|---|
| v5.1.5 | Phase 1 | Diagnostic logging only — no behavior change |
| v5.1.6 | Phase 2 | Fee-floor on trailing + ExitAdjust |
| v5.1.7 | Phase 3 | Runtime BUY_BLOCKED gate |
| v5.1.8 | Phase 4 | Sizing fix |
| v5.2.0 | Phase 5 | Strategy-regime audit + cfg cleanup (minor bump for AUTO routing changes) |

Sequential. Each shipping with parity_harness verification gate (no
training-data drift).

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Phase 2 fix masks the actual bug, doesn't fix root cause | Phase 1 diagnostic is mandatory before Phase 2 |
| Disabling trailing breaks legitimate winners that ride past fees | Compare backtest P&L before/after on a winning day |
| Sizing change blows max_drawdown | `min_kill_loss` + `max_drawdown_pct` already enforce this |
| Strategy zoo audit shows "everything is bad" → no edge anywhere | That's a real outcome — moves us strictly to ML path |

## What this is NOT

- **Not** an engine fix. v5.1.4 architecture is correct.
- **Not** an ML pivot — that's Phase 6, deferred.
- **Not** a tuning sweep — narrow, evidence-driven changes only.

## Order of attack

**Phase 1 today** (30 min). The rest depends on what Phase 1 reveals.

If H1 (trailing): Phase 2 is mechanical, ship by EOD.
If H2 (sizing): Phase 4 first, re-soak overnight, then Phase 5.
If H3 (structural): bigger pivot — strategy redesign or skip to ML.

Most likely outcome (from the 0.097%/0.099%/0.099% repeating pattern in
the trade log): **H1 confirmed**. Phase 2 fix lands today, soak tonight,
review tomorrow.
