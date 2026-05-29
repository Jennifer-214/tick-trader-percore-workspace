---
type: pre-implementation-findings
scope: ALL
engine_head: ce2173b (v5.15.5.F.4d.1.D.1 WIP)
date: 2026-05-28
source: codebase-deep-sweep-5x9 (49-agent skill-driven sweep) + pass1/pass2 + round-0
status: provisional (49 findings need runtime confirmation; marked inline)
codification: DEFERRED until .D.1 ships (Classes 37+, DESIGN_SPECS, CI tools, ledgers)
---

# MASTER pre-implementation backlog (deep-sweep synthesis)

**141 NEW findings** | filtered out: 35 already-tracked + 20 cross-lens dups.

## Triage buckets

| Bucket | findings | CRIT | HIGH | MED | LOW |
|---|--:|--:|--:|--:|--:|
| BACKLOG-STANDALONE | 24 | 0 | 0 | 11 | 13 |
| E.1 | 30 | 1 | 9 | 12 | 8 |
| E.2 | 14 | 0 | 6 | 6 | 2 |
| E.3 | 10 | 0 | 1 | 3 | 6 |
| E.5 | 6 | 0 | 1 | 5 | 0 |
| E.6 | 2 | 1 | 0 | 0 | 1 |
| PRE-PAPER-TEST | 55 | 0 | 21 | 26 | 8 |

## CRITICAL + HIGH (all buckets)

- **[CRITICAL]** `conc-5` (concurrency → E.1) [NEEDS-RUNTIME]: Multi-producer race on per-core submit_queues SPSC ring: drainer thread AND per-core slow thread both push the same ring on the LIVE order-submit path
- **[CRITICAL]** `live-bc-1` (live-binance → E.6) [NEEDS-RUNTIME]: User-data WS points at Binance GLOBAL (stream.binance.com) while orders + listen key use Binance US (api.binance.us) — real-time fills never arrive in non-testnet live
- **[HIGH]** `cfg-10` (cfg-registry → PRE-PAPER-TEST) [NEEDS-RUNTIME]: Two live drift-check walkers over ~13 overlapping STAMP_BOUND_CFG_DERIVED fields, with divergent gating that produces different model-load REFUSE verdicts (Class 18/21 the framework header claims closed is still open)
- **[HIGH]** `cfg-ts-2` (cfg-registry → PRE-PAPER-TEST): Production cfg-binding drift detector tested ONLY on 0-row vacuous walks; the 'drift detection' tests re-implement the logic inline against a FakeCfg and never call the production walker
- **[HIGH]** `conc-bc-1` (concurrency → E.1) [NEEDS-RUNTIME]: Paper-reset mutates + snapshots shared OMS/per-core state with no quiescence handshake; drainer never parks, slow-paths may be mid-cycle
- **[HIGH]** `dsgui-1` (datastream-gui → E.2) [NEEDS-RUNTIME]: GUI chart trade markers + equity curve silently broken in sharded mode: TradeReader parses legacy CSV schema while engine writes format-v3 to the same file
- **[HIGH]** `dsgui-2` (datastream-gui → PRE-PAPER-TEST): Notify per-kind cooldown drops repeated same-kind CRITICAL alerts with no severity bypass or escalation
- **[HIGH]** `dsgui-2` (datastream-gui → PRE-PAPER-TEST): backtest<->live feature asymmetry: DepthRecorder stores top-of-book only, so replayed book_imbalance is top-only while live computes 5-level imbalance (same consumer field, two transforms)
- **[HIGH]** `dsgui-1` (datastream-gui → E.2): CandleAccumulator takes a pthread_mutex on the producer per-tick fan_out path (H3 violation + producer p99 budget breach, GUI build)
- **[HIGH]** `dsgui-2` (datastream-gui → PRE-PAPER-TEST): Backtest tick + depth CSV parse use locale-honoring strtod with no process-level LC_NUMERIC=C pin — non-C locale silently corrupts every price/book value, breaking replay determinism
- **[HIGH]** `dsgui-1` (datastream-gui → E.2): GUI force-close drain (EngineSharded_SlowPath_DrainManualCloses) is preprocessor-elided in the CI test binary -> entire GUI->execution write path is uncompiled and untested
- **[HIGH]** `dsgui-2` (datastream-gui → E.2): CandleAccumulator has zero tests; bucketing / ring-wrap / VWAP / snapshot-ordering / interval-reset all unverified, and it takes a pthread_mutex on the producer fan_out path under the GUI build
- **[HIGH]** `det-1` (determinism-xcut → PRE-PAPER-TEST): Backtest tick-CSV + depth-replay parsers use locale-dependent strtod() on the replay-critical input path (H5 + cross-locale determinism); live path already migrated to tt::parse_double_fast, backtest/depth left behind
- **[HIGH]** `fpmem-1` (fixedpoint-mem → E.1): USE_NATIVE_128 FPN_Sqrt<64> specialization reverts to IEEE-754 double round-trip, silently voiding v5.10.0b deterministic Newton-Raphson sqrt in production (H10 fast/scalar bytewise-identity violation)
- **[HIGH]** `fpmem-2` (fixedpoint-mem → E.1): controller_test + parity_harness compile WITHOUT USE_NATIVE_128 while all production targets compile WITH it — the entire FPN<64> native fast path is untested and a determinism test validates a never-shipped code path
- **[HIGH]** `fpmem-1` (fixedpoint-mem → E.1) [NEEDS-RUNTIME]: Production accounting path runs strict-aliasing UB type-punning (_to_fp64/_from_fp64) under -O3 -flto
- **[HIGH]** `fpmem-2` (fixedpoint-mem → PRE-PAPER-TEST) [NEEDS-RUNTIME]: No bytewise-identity test between scalar FPN<64> and native-128 FP64 paths (H10 scalar-fallback parity gap on a wire/hash surface)
- **[HIGH]** `fpmem-1` (fixedpoint-mem → E.1) [NEEDS-RUNTIME]: USE_NATIVE_128 (production default) silently defeats the documented bytewise-deterministic FPN_Sqrt — feeds ML feature stddev
- **[HIGH]** `fpmem-2` (fixedpoint-mem → E.1) [NEEDS-RUNTIME]: Strict-aliasing UB in _to_fp64/_from_fp64 — the production FPN<64> accounting chokepoint, compiled at -O3 -flto with no -fno-strict-aliasing
- **[HIGH]** `fpmem-1` (fixedpoint-mem → PRE-PAPER-TEST) [NEEDS-RUNTIME]: FPN_Sqrt<64> native-128 specialization routes through sqrt() IEEE-754 round-trip, breaking the documented bytewise-determinism contract on the DEFAULT production build
- **[HIGH]** `fpmem-2` (fixedpoint-mem → PRE-PAPER-TEST): Test/production FPN implementation divergence: controller_test + parity_harness compile WITHOUT USE_NATIVE_128, so all FPN determinism tests validate code that never ships
- **[HIGH]** `fpmem-1` (fixedpoint-mem → PRE-PAPER-TEST) [NEEDS-RUNTIME]: Production FP64 (__uint128_t) FPN<64> path is untested: controller_test omits -DUSE_NATIVE_128 while production defaults it ON; no generic-vs-FP64 bytewise-equivalence test exists (H10-analog)
- **[HIGH]** `hpg-bc-1` (hot-path-gates → E.1): Head-to-head parity oracle (LegacyReferenceDriver) validates against the SG_Evaluate stub, which cannot model the production per-fill tp_pct/sl_pct exit path — byte-identity claim is false for the real exit path
- **[HIGH]** `live-bc-2` (live-binance → PRE-PAPER-TEST) [NEEDS-RUNTIME]: Periodic ReconciliationLoop ignores reconcile_mode/dry_run — unconditionally force-overwrites oms->balance (and ks_peak_balance) every 30s in live mode
- **[HIGH]** `lbs-5` (live-binance → E.3) [NEEDS-RUNTIME]: User-data WS frame buffer is 4KB; large outboundAccountPosition events overflow ud_ws_read_frame and trigger a reconnect loop, dropping fills
- **[HIGH]** `live-pc-1` (live-binance → PRE-PAPER-TEST) [NEEDS-RUNTIME]: clientOrderId idempotency key collides across restart (next_order_id not persisted)
- **[HIGH]** `tsa-live-1` (live-binance → PRE-PAPER-TEST): Paper<->live SUBMIT gate has no adversarial test — every Submit test uses a null adapter, so 'paper never places a real order' is unverified
- **[HIGH]** `tsa-live-2` (live-binance → PRE-PAPER-TEST): Reconcile_ApplyMissedFills (boot fill-recovery money path) tests assert only the replay COUNT + watermark, never the OMS portfolio/balance side effect
- **[HIGH]** `oms-bc-1` (oms-money → PRE-PAPER-TEST): EventLoop_DrainPostFill wrapper never extended with core_cfg -> live path always passes nullptr -> .F.4d per-core bandit_algorithm reward dispatch silently collapses to EXP3 (Thompson reward dead in production)
- **[HIGH]** `oms-money-blindspot-1` (oms-money → PRE-PAPER-TEST): Calib log bandit columns (arm/regime/algo/reward) read a producer-never-written channel — emit constant 0 in production, breaking offline ML reward attribution
- **[HIGH]** `oms-ts-1` (oms-money → PRE-PAPER-TEST): Production OMS balance/PnL round trip has no exact-value assertion; the one balance check is a fee-blind ±$15 range whose comment falsely claims it verifies fees
- **[HIGH]** `oms-ts-2` (oms-money → E.5): No test cross-checks sum(core_realized)==oms->realized_pnl or sum(core_fees)==oms->total_fees — two independent net-P&L derivations on the money path are never reconciled
- **[HIGH]** `persist-8` (persistence → E.1): Paper-reset does not reset per-core ExecutionCore hot state → post-reset entry lockout + spurious exit (Class 5 reset incompleteness)
- **[HIGH]** `persist-8` (persistence → PRE-PAPER-TEST) [NEEDS-RUNTIME]: Paper-reset omits ExecutionCore_Init: hot-path active/live_tp/live_sl mirrors survive reset-with-open-position -> phantom-active permanently blocks new entries (init<->reset asymmetry)
- **[HIGH]** `persist-8` (persistence → E.1) [NEEDS-RUNTIME]: Paper-reset never resets per-core ExecutionCore hot-path mirror -> zombie active flag blocks all future entries on that core
- **[HIGH]** `persist-dod-1` (persistence → E.2) [NEEDS-RUNTIME]: Periodic snapshot save reads full live OMS+per-core state un-synchronized on the producer thread; torn state persisted as the warm-restart seed
- **[HIGH]** `wfa-1` (persistence → E.2) [NEEDS-RUNTIME]: Warm-restart restores positions EXIT-DISARMED: cached_params.flags=0 (TP/SL_ENABLED unset) until first slow-path rebuild → restored position cannot honor its own stop-loss during the boot window
- **[HIGH]** `rf-1` (regime-features → PRE-PAPER-TEST): cumdelta + flow_10s/1m/5m train/serve divergence: backtest feature-collect uses REAL is_buyer_maker, live serve hardcodes 0 (reverses rsf-1 REFUTED)
- **[HIGH]** `rf-1` (regime-features → PRE-PAPER-TEST): Regime classifier ML-enrichment (Mode A / model_score / regime_model_weight) is structurally dead on the production sharded path
- **[HIGH]** `rsf-ts-1` (regime-features → PRE-PAPER-TEST): Regime_Classify has no direct classification unit test — only the cold-start gate is exercised; all score/direction/strength/hysteresis logic is untested at the assertion level

## Codification rollup (queued for post-.D.1)

- **140 anti-pattern instances** → consolidate into candidate Classes 37+.
- **97 CI-tool candidates** → mechanical prevention checks.
- **122 test-gap specs** → regression guards.
- **49 findings need runtime confirmation** before acting.
