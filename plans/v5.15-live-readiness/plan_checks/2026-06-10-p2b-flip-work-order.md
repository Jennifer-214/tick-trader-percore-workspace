<!-- STATUS: EXECUTED 2026-06-10 — engine 838bf09, 3268/0; D-184..D-188 -->

# P2b flip work-order (Step-A enumeration freeze) — Ship B decimal money

**Date:** 2026-06-10 (Session 13/14 boundary) · **HEAD:** engine `6814d4d` (P2a), suite **3268/0** · **Decision record:** D-168..D-183 (`decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md` Session-13 addendum — the SSoT for everything below)
**Status of the ship:** P0 ✅ · P1 ✅ (full decimal core, 1,747 oracle rows, 5 fixtures) · P2 markers ✅ (teeth-proofed RED→GREEN) · P2a ✅ (8 dispatcher decimal branches + Money one-liners) · **THIS = P2b, the atomic flip** · then P3 fee booking → P4 epoch tests → P5 close.

## Why P2b is atomic (and why that's the protection working)

The D-181 guards make a partial flip UNCOMPILABLE: retyping any guarded persisted money field (Position/OrderEvent) or flipping `EngineMoneyT` red-builds until versions 14/10/7 + OMSEL02 cohort + stamp v3 ride the SAME commit. The guard messages ARE the checklist — build red, read the errors, do what they say.

## The probe result (compiler-as-enumerator, D-164 method — VERBATIM, deduped)

Probe: `fee_rate_taker` registry row STORAGE_T `FPN_Binary<F>` → `Money`, full build, capture `error:` sites, REVERT (verified reverted; suite 3268/0 untouched). Consumer set for ONE money cfg row:

```
CoreFrameworks/ControllerEventLoop.hpp:860     (fee_rate_taker_for_core resolve — replay)
CoreFrameworks/ControllerEventLoop.hpp:1922    (production entry-fee chain)
CoreFrameworks/ControllerEventLoop.hpp:1966    (production exit-fee chain)
CoreFrameworks/ControllerEventLoop.hpp:3051    (diag fee floor)
CoreFrameworks/ControllerEventLoop.hpp:3619    (consumer)
CoreFrameworks/ControllerEventLoop.hpp:3687    (consumer)
CoreFrameworks/EngineCommon.hpp:159            (BNB ApplyBnbDiscount rate-transform)
ML_Headers/CfgDriftCheckRegistry.hpp:279       (drift-check walker instantiation)
CoreFrameworks/ShardedSnapshot.hpp:258         (display snapshot bridge)
CoreFrameworks/CfgFieldDispatch.hpp:522/598/667 (walker instantiation seams — assign/diff/emit; the P2a
                                                branches exist, these are the FPN_FromDouble<T::F>-style
                                                generic-walker seams to convert at the flip)
CoreFrameworks/ControllerConfig.hpp:1458       (manual init FPN_FromDouble -> Money literal/assign)
CoreFrameworks/Order.hpp:361                   (pre_resolved.fee_rate binding — decision-time data binding)
```

Scaling estimate: ~12 sites/row × ~30 money rows, heavily OVERLAPPING (the fee chain serves all rate rows; the per-row delta is small). The flip session re-runs this probe per row-batch and lets the compiler keep the list honest.

## The money cfg-row classification (Step-A; finalize at flip via consumer evidence, NOT names)

**Rule:** MONEY = the value IS money or multiplies money into money (rates, pcts applied to notionals/prices, balances). FEATURE (stays `FPN_Binary<F>`) = multiplies/thresholds BINARY signals (stddev mults, R², slopes, scores, blend ratios). D-170 locked: thresholds cast binary→money at GATE-BUILD (egress); `tick.price` is Money end-to-end.

- **MONEY (the core set, audit-ratified):** `fee_rate`, `fee_rate_maker`, `fee_rate_taker`, `take_profit_pct`, `stop_loss_pct`, `risk_pct`, `slippage_pct`, `fee_floor_mult`, `entry_offset_pct`, `offset_min`, `offset_max`, `max_drawdown_pct`, `max_exposure_pct`, `kill_switch_daily_loss_pct`, `kill_switch_drawdown_pct`, `ml_tp_pct`, `ml_sl_pct`, `partial_exit_pct`, `tp2_mult`, `breakeven_buffer_pct`, `simpledip_tp_pct`, `simpledip_sl_pct`, `mr_tp_pct`, `mr_sl_pct`, `emacross_tp_pct`, `emacross_sl_pct`, `starting_balance` (+ global registry money rows — sweep `FOREACH_GLOBAL_CFG_FIELD` the same way), `lazy_rebuild_price_threshold_pct` (price-delta ratio — classify by its compare site).
- **FEATURE (stay binary; verified-by-consumer at flip):** `momentum_*_mult/min_r2/min_buy_delta`, `emacross_dip_mult/crossover_min/trail_mult`, `tp_hold_score`, `tp_trail_mult`, `sl_trail_mult` (×stddev), `vwap_offset`, `regime_slope_threshold`, `ml_buy_threshold`, `bandit_blend_ratio`, `confidence_threshold_scale`, `risk_*_threshold/min_size_pct`(→ check consumers — sizing thresholds may be money).
- 76 FPN rows total in the per-core registry; every row gets a one-line disposition in the flip commit's enumeration freeze (paste-the-tool-output discipline).

## P2b execution map (the guard-railed order)

1. **Pre-tag anchor** + branch state noted; `/sync-workspace`.
2. **Enumeration freeze:** per-row classification table (all 76 + globals) → `plan_checks/` verbatim; re-probe 2-3 representative rows.
3. **The flip commit (single, red-until-done):** registry STORAGE_T swaps (money rows → `Money`) → `EngineMoneyT = Money` → field retypes ripple (Position/Order/OrderEvent/Tick/GateParameters/ExecutionCore money fields; accounting chain ctx fields) → op-site swaps `FPN_*`→`Money_*` at every red site (the compiler enumerates) → D-103 casts at the locked egress seams (`Money_FromBinary` at gate-build in StrategyParameters/PortfolioController; `Money_ToBinary` at the producer ema ingress per D-122) → walker seams (CfgFieldDispatch :522/:598/:667-class) → **the guard demands:** versions 14/10/7 + H21 tombstones + OMSEL01→02 + `reserved[]`→`format_version` + rotate-not-append (D-175a) + S-3 booked-fee field + OrderEvent H12 pad re-derive + stamp v3 CURRENT/MAX + unconditional strict-bypass floor + `[1,2]` dispatch H21-retired.
4. **Gates at green:** suite (expect the epoch==0 marker check to FLIP to an epoch==1 assertion — update it + the D-144 floors auto-raise) · `--require-decimal-branches` in CI (wire into pre-commit at this commit) · ubsan/asan lanes · the D-100 oracle suite (all 5 fixtures still green — they test Money_* directly, flip-invariant) · warm-restart epoch-reject test (P4's test lands here or immediately after: snapshot v13 / OMSEL01 / stamp v2 all REFUSED loud) · A/B oracle N/A (binary VALUES change is not expected — features stay binary; the emitter should stay byte-identical pre/post flip — VERIFY, it's a strong free check).
5. **Tail (same commit or immediate follow):** money-golden regen + the recorded-fills differential + retrain checklist (M4: flatten B-ζ → retrain → re-embed fingerprint → re-stamp → strict-load test → CHANGELOG) — per D-100/D-157 the full golden refreeze + Check-F un-bypass close at P5.
6. **P3 next:** fee booking (the fill-lifecycle rework — terminal taxonomy + reaper + dedup + commission (amount,asset) carry per the fee-booking D-93 fold; the semantically trickiest remaining block).

## Standing decisions in force (do NOT re-open)

D-170 egress lock · D-173 BNB convertibility (boot bnbBurn query + runtime N guard + degrade) · D-174a-f (half-even casts · LIVE-fill degrade · LIVE cfg refuse-boot · ceil-in-FeeCompute · operator re-arm · tickSize load-not-consume) · D-175a/b (OMSEL rotate+proceed · partial-SELL reduce-qty) · D-176 `Money_*` naming · capital-live = `.E` done + v5.16 + explicit operator greenlight (D-168).

## Known-pending operator items
EmaCross privacy triage (since the A.5 handoff) · always-loaded byte-budget compression pass (queued) · the veto windows above (all defaulted, all audited).
