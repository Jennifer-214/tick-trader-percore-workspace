# /accounting-audit findings — 2026-06-09 — scoped: Ship-B money plan (remaining work)

**Target:** `plans/v5.15-live-readiness/subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md` (v0.3, post-A.5 re-audit)
**Engine HEAD:** 0e48150 (v5.15.5.F.4d.1.E.0.8). Audit mode: does the plan's MECHANISM deliver the DECIDED items (D-104/105/109/127/128) — decided items not re-litigated.
**Skill:** `/accounting-audit` per `claude-skills/accounting-audit/SKILL.md`; Layer-2 inline execution (no subagents). Stage-0 anchors: H4, Class 26/27, decision-time-data-binding-pattern.md, golden-master-over-reimplemented-oracle.md.

## Summary

- CRITICAL: 2 (both on B1's fix shape — the carry vehicle and the unit of the carried value)
- HIGH: 2 (replay≠production structural divergence post-B1)
- MEDIUM: 4
- LOW: 2
- Focus verdicts: (d) Class 27 CLEAN · (e) per-core fee indexing PASS (one replay outlier → HIGH-2) · (g) atomicity PASS

---

## Findings

### [CRITICAL-1] B1 books `result.commission` without commission-asset denomination conversion (`DataStream/BinanceUserData.hpp:361-363,378-380`; plan § Venue-SSoT F-A/F-B, § Re-fire B1)
- **Severity:** CRITICAL · **Category:** 7 (backtest↔live parity) + 4 (H4/unit correctness) · **Class:** N/A (new class candidate: unit-blind source-exact booking)
- **Details:** Binance `n` is denominated in `N` (`commission_asset`): **base asset on BUY, quote on SELL, BNB when discount enabled** — the plan's own R-1 (D-109) says exactly this. B1's fix shape is "carry `result.commission` onto the in-flight Order + book it for LIVE", and `handle_sell_fill` computes `net = gross − total_fee` in **quote** units (`OrderManager.hpp:1212-1215`). Booking the raw reported number for a BUY fill books a **base-denominated amount into quote-denominated accounting** — e.g. 0.00001 BTC commission booked as 0.00001 USDT, a ~70,000× understatement at current prices; with `pay_fees_in_bnb=1` it's BNB-denominated and the engine tracks no BNB mark price at all. The plan's F-B labels asset-denomination a "modeling approximation… low priority" — true while fees were COMPUTED (quote-side model), **false once B1 books the reported value**: denomination becomes the booking path. Nothing in B1/B6/#5 carries or consumes `commission_asset` (it dies in `OrderResult.commission_asset`, `ExchangeAdapter.hpp:57`, consumed nowhere).
- **Recommended fix:** carry the **(amount, asset) pair** onto the in-flight Order; convert at booking: quote-asset → book directly; base-asset → `commission × fill_price` (decimal mul through #4); BNB → requires an explicit decision (BNB/quote mark source, OR per-asset fee ledger, OR boot-refuse `pay_fees_in_bnb=1` in LIVE until `.E.1` multi-asset). Add the conversion rule to the D-100 computed-vs-reported differential so the gate verifies it.
- **DESIGN_SPEC:** `feedback_defer_to_source_authority_for_external_semantics` (source-exact means value+UNIT); `decision-time-data-binding-pattern.md`.

### [CRITICAL-2] B1's carry vehicle dies after the FIRST fill event — order slot freed on `ORDER_PARTIAL` (`CoreFrameworks/OrderManager.hpp:1383→1414-1415`, drop at `:1336-1344`)
- **Severity:** CRITICAL · **Category:** 6 (balance/position update integrity) · **Class:** pre-existing live accounting bug; B1 inherits it
- **Details:** `OrderManager_ProcessFillCommand` sets `ORDER_PARTIAL` when `order_complete=0` (`:1383`), runs `OrderManager_HandleFill` with that event's per-fill qty (`l`/`L` are PER-TRADE values, `BinanceUserData.hpp:338-339`), then **unconditionally clears the order-bitmap slot** (`:1415` — the `:1380-1382` comment "keeps the order alive in the OMS" is contradicted by the code; only the ACK-only path `:1364-1366` keeps the slot). A market order filling across N trades emits N executionReports; events 2..N find the slot freed (`:1336-1338`) and are **silently dropped** → position qty, notional, fees, and (post-B1) commission all book only the first partial. This is the exact hop sequence B1's "carry onto the in-flight Order" rides: there is **no living Order to accumulate onto** after hop 1. Additionally `n` is per-fill, so the carry must be an **accumulator** (`FPN_Add`-style `+=` per event), never an assign-once scalar — the plan's B1 text doesn't state accumulation semantics.
- **Recommended fix (must precede or land inside B1):** keep the slot open until terminal (`order_complete=1` or reject); accumulate `filled_qty` + commission and maintain weighted avg price across events (or alternatively book per-event deltas — but `Portfolio_OpenSlot` per-partial would clobber the slot, so accumulate-then-book-at-terminal is the cleaner shape); fire `handle_*_fill` once at terminal with totals. Add a multi-fill (2+ executionReport) test to the Tests-changed slate — none exists (`controller_test.cpp:5106-5119` covers only the state enum).
- **CI/regression:** none today; the D-100 recorded-fills differential would catch it ONLY if the recording includes a multi-fill order — make that an explicit fixture.

### [HIGH-1] Post-B1, replay structurally CANNOT reproduce production — `OrderEvent` carries no fee field; both replays RECOMPUTE (`CoreFrameworks/OrderEventLog.hpp:79-92` struct; recompute at `:657/:676` and `ControllerEventLoop.hpp:860-877`)
- **Severity:** HIGH · **Category:** 7 · **Class:** Class-18-adjacent (replay mirror recomputing what production books)
- **Details:** The plan's C2 acceptance is a "replay==production **rounding** differential," and the shared #4 helper is structurally feasible at every COMPUTED site (all 4 families funnel a `(notional, rate)` mul: `OrderManager.hpp:1163/:1209`, `ControllerEventLoop.hpp:1923/:1967` legacy mode-0, `ControllerEventLoop.hpp:863/877` replay, `OrderEventLog.hpp:657/676` replay — a single chokepoint works). **But B1 changes production from computed to BOOKED-reported for LIVE**, and the replay inputs (`OrderEvent`: price/qty/tp/sl only) cannot reconstruct an exchange-reported value from any rate. Warm-restart replay of a LIVE session will rebuild different `balance`/`realized_pnl` than production booked — by construction, not by rounding.
- **Recommended fix:** extend `OrderEvent` with the **booked fee** (decimal) written at `OrderManager_HandleFill` (`:1298-1303`); replays READ it instead of recomputing — this makes the event log the fee chokepoint for replay and collapses HIGH-2. The `entry_size`-gated log header (`OrderEventLog.hpp:126-131`) + Ship-B epoch (D-100, R3-style version bump) make the layout break free now.
- **DESIGN_SPEC:** `golden-master-over-reimplemented-oracle.md` (replay recompute = a reimplemented oracle of the booking path); single-source-of-truth.

### [HIGH-2] Fee-RATE resolution asymmetry across the four fee families — the C2 differential will trip even pre-B1 (`OrderEventLog.hpp:636` vs `ControllerEventLoop.hpp:860` vs `Order.hpp:358-364`)
- **Severity:** HIGH · **Category:** 2 (per-core indexing) · **Class:** Class 26 sub-shape B adjacent (replay-side)
- **Details:** Production books per-Order `o->pre_resolved.fee_rate` (bound from per-core maker/taker at submit, `Order.hpp:358-364` — the `.B.1` Class-27 closure, correctly preserved). CEL replay uses per-core `effective_cores[core_id].fee_rate_taker` (`:860` — `fee_rate_taker_for_core`, OK). **`OrderEventLog.hpp` replay takes ONE global `fee_rate` parameter for ALL slots** (`:636`) — wrong whenever per-core fee rates differ (and blind to maker fills if LIMIT ever lands, same blind spot as TECH_DEBT-154's dormant guard `OrderManager.hpp:1131-1145`). The plan's B2 enumerates these sites for the ROUNDING helper but never names the rate-resolution asymmetry. If HIGH-1's carry-fee-in-event fix lands, this collapses into it; if not, the single-rate replay must take per-core rates.
- **CI:** Check 10 (sub-shape B) does not cover this signature shape (rate passed as a fn parameter, not read as `cfg.X` at the consumer) — note as a false-negative surface.

### [MED-1] `ExitBuffer_PendingProceeds` "matches what will be credited" invariant breaks for LIVE under B1 (`CoreFrameworks/Portfolio.hpp:194-207`; sole caller `PortfolioController.hpp:947` kill-switch equity)
- **Severity:** MEDIUM · **Category:** 3 (fee/slippage cross-path consistency) + 10 (kill-switch)
- **Details:** Pending-proceeds is an ESTIMATE computed before the exit fill exists; under B1 the LIVE credited amount is the exchange-reported commission — unknowable at estimate time, so the comment's exact-match claim (`Portfolio.hpp:194`, `PortfolioController.hpp:945`) becomes approximate for LIVE. Plan M3 routes the site through the #4 helper (covers paper/backtest exactly) but does not document the LIVE estimate-vs-booked bound at this kill-switch boundary. Caller is legacy single-core (deprecated path) passing GLOBAL `ctrl->config.fee_rate_taker` — benign in single-core (global==core-0) but the helper migration should take a per-record rate if this ever serves sharded. Decimal type swap itself is clean here (Mul/SubSat/AddSat are radix-agnostic; `<10,8>` sat bound ~9.2e10 quote — ample).
- **Recommended fix:** document the bounded mismatch (≤ per-record |reported−computed|, empirically bounded by the D-100 differential); keep the estimate on the computed round-UP model.

### [MED-2] The cmd-ring fill vehicle is `double` — exact-parse needs an `OrderResult` retype the plan implies but never states (`ExchangeAdapter.hpp:43-58` :46/:47/:56; ingress `OrderManager.hpp:1369-1370` `FPN_FromDouble`)
- **Severity:** MEDIUM · **Category:** 5 (lossy conversion in carry path)
- **Details:** B6 resolves C4 to "guarded exact-`FromString` on the raw venue JSON (`p`/`q`/`n`)" — but the values cross the ring as `double avg_fill_price/fill_qty/commission` (parsed lossy at `BinanceUserData.hpp:338-339,361`), then `FromDouble` at `:1369-1370`. The exact parse is meaningless unless the RING vehicle is retyped. `OrderResult` is deliberately non-templated width-independent POD (`ExchangeAdapter.hpp:30-31`) — a 10⁸-scaled `int64_t` (or the 16B decimal, which is F-independent) satisfies the constraint; spell it out in the plan so C4 closes structurally, killing the `FromDouble` ingress in the same stroke (D-102's sister seam).

### [MED-3] Runtime reconcile balance overwrite is a double ingress the D-103 cast list misses (`OrderManager.hpp:1423-1433` `FPN_FromDouble(exchange_balance)`; `Reconcile.hpp:63` `double commission`, `:546` double-parse)
- **Severity:** MEDIUM · **Category:** 4 (H4 sweep) · **Class:** D-102 sibling (lossy ingress)
- **Details:** Plan names the boot-reconcile `Run.hpp:653 usdt_recovered` boundary, but `OrderManager_ProcessReconcile` overwrites the ENTIRE `oms->balance` from a double carried in repurposed `OrderResult` fields (`:1424-1425,1431`) — a second, runtime balance ingress. Double is integer-exact only to 2⁵³ (scaled: balances ≤ ~9×10⁷ quote at 8dp) — bounded today, but violates source-exact and bypasses the decimal parse cohort. `ReconcileTrade.commission` (`Reconcile.hpp:63`) stays double unless the #5 cohort retypes the FIELD, not just the parse (B6 says "add the parse to the cohort" — make the field retype explicit).
- **Recommended fix:** add both to the D-103/#5 enumeration: venue balance string → exact decimal `FromString` end-to-end (ring carries scaled int per MED-2).

### [MED-4] Paper↔live fee DIFFERENCE is intentional + documented but not BOUNDED (plan § Venue-SSoT R-1, acceptance "LIVE fee = exchange-reported")
- **Severity:** MEDIUM · **Category:** 7
- **Details:** (h) verdict: the round-UP-computed (paper/backtest) vs booked-reported (LIVE) split is decided (D-109/D-127) and documented, and the empirical computed-vs-reported differential exists in acceptance. But no TOLERANCE is stated, and the bound is asset-dependent once CRIT-1's conversion lands (base-denominated buys convert at fill price; BNB adds a second mark). A drift in this differential is also the detector for venue fee-schedule changes — give it a numeric gate (e.g. |computed − reported_converted| ≤ K ULP @ 10⁻⁸ per fill, K documented per asset case) so it fails loud rather than informatively.

### [LOW-1] Trade-id dedup key parsed via double (`BinanceUserData.hpp:340` `(uint64_t)binance_json_extract_double("t")`)
- **Severity:** LOW · **Category:** 5 — exact only to 2⁵³; trade ids are int64 counters (~10⁹ today; decades of headroom). Add to the #5 integer-parse cohort opportunistically (TECH_DEBT-144's checked-int family), not a Ship-B gate.

### [LOW-2] `GUI/TradeReader.hpp:145-146` double P&L recompute — already dispositioned (plan B6: "follows the log format"); confirm at code time the decimal log format flows through and the recompute stays display-only (H4-exempt). No action beyond the existing disposition.

---

## Focus verdicts (clean lanes)

- **(d) Class 27 — CLEAN.** No new scalar cfg-mirror: B1's carry IS decision-time binding (the correct pattern); scale 10⁸ = compile-time constant, not cfg; #6 quantize reads `SymbolFilters` at submit cadence (decision-time by construction). Note only: `EngineCommon_ApplyBnbDiscount` (`EngineCommon.hpp:154-165`) bakes 0.75× into `cfg.cores[].fee_rate_*` at boot (pre-existing; under B1, LIVE divergence from the baked rate is absorbed by booking reported — paper keeps the model; the `FromDouble(0.75)` → exact decimal constant is already B2).
- **(e) Per-core fee indexing — PASS.** `Order_BindPreResolved` (`Order.hpp:358-364`) reads per-core `PerCoreCfg` maker/taker; a pure type swap (decimal `fee_rate`) preserves the indexing; CEL replay per-core (`:860`). Outlier = HIGH-2's single-rate `OrderEventLog` replay.
- **(g) Balance/realized-PnL atomicity — PASS.** `handle_sell_fill` updates balance → realized_pnl → peak sequentially on the single drainer thread (`OrderManager.hpp:1214-1217`); no atomics on these fields; GUI reads snapshot copies (doubles, H4-exempt). The 16B decimal store is non-atomic exactly as the 24B/16B binary was; no raw cross-thread reader found in this sweep. Type swap changes nothing structurally.

## Disposition summary for plan amendment (operator triage)

| Finding | Suggested home |
|---|---|
| CRIT-1 commission_asset conversion | B1 amendment (fix shape incomplete without it) + D-100 differential rule |
| CRIT-2 partial-fill slot-free + accumulation | NEW pre-B1 or in-B1 deliverable + multi-fill test fixture |
| HIGH-1 OrderEvent fee field | B1/B2 amendment (event-log layout rides the Ship-B epoch free) |
| HIGH-2 replay rate asymmetry | collapses into HIGH-1; else B2 row |
| MED-1..4 | plan-body line items (M3 extension, C4 vehicle spec, D-103 additions, differential tolerance) |
| LOW-1..2 | ledger note / existing disposition |

*Generated by /accounting-audit 2026-06-09, scope: Ship-B money plan remaining work. No code edits made.*
