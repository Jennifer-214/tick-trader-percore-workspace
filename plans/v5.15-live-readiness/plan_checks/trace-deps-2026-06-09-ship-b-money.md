# /trace-deps report — money-numeric-core-foundation (Ship-B remaining scope) — 2026-06-09

- **Plan:** `plans/v5.15-live-readiness/subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md` (v0.3) + sidecar `2026-05-31-...-11-new-function-designs.md`
- **HEAD:** 0e48150 (v5.15.5.F.4d.1.E.0.8), `feat/v5.15-live-readiness`
- **Scope:** Ship-B remaining only (decimal `<10,8>` + #4/#5/#6 + B1-B6 + D-103 casts + stamp/persist decimal + D-100 gate + FP64 absorb + FPN_* naming). Ship-A rows treated as SHIPPED.
- **Skill refs:** DESIGN_PHILOSOPHY § 7 (chokepoint not bypassed) + § 11 (boundary-stable); Step 2a filename≠type-name; Step 6 data-flow; M4/B8 type-sensitivity.

## Summary

- NEW symbols analyzed: 7 (`FixedPoint<10,8>` instantiation, decimal op family, `divmul_pow10`, #4 rounding helper, #5 exact decimal FromString, `FPN_Quantize`+MIN_NOTIONAL, `to_binary()`/`to_decimal()`, commission-carry field)
- Callees/anchors verified: 40+ — **every plan-cited D-103/B2/blast-radius anchor verified present at HEAD** (the 2026-06-09 re-derivation is genuine)
- PASS: name-collision sweep CLEAN (no existing `FPN_Quantize`/`divmul_pow10`/`to_binary`/`to_decimal`/half-even symbol anywhere); proof+oracle artifacts on disk; `check_storage_t_coverage.py` exists; `is_fp_decimal_v` already live (`FixedPointN.hpp:100-102`)
- GAP: 4 boundary-enumeration misses (1 HIGH) + 1 dependency-not-decimal-capable (HIGH) — plan fold needed before the Ship-B gate
- DRIFT: 2 (C4 anchor ~20 lines off; B2 legacy fee list missing one site)

**Verdict: YELLOW** — decision architecture sound, no RED/architecture-killer; the D-103 "~12 sites" claim and one #6 dependency need amendment before Ship-B coding.

---

## Per-focus verdicts

### 1. `FixedPoint<10,8>` instantiation — PASS with one forced-design note [MED·structural]

- Generic `template <int RADIX,int FRAC> struct FixedPoint` exists declaration-only (`FixedPointN.hpp:82`); only `<2,64>` specialized (:84-89). `<10,8>` slot is clean — **no collision**.
- `is_fp_decimal<FixedPoint<10,F>>` trait already matches it (:100-102). Dispatchers' `static_assert(is_fp_binary_v<T> ...)` at `CfgFieldDispatch.hpp:63/180/233/274/331/400/456/505` exclude decimal → red-build until the B3 branch is written, exactly as the plan claims (verified all 8 sites gate on `is_fp_binary_v`).
- **FORCED design constraint the plan should state explicitly:** the entire existing op family is `template <unsigned F>` over `FPN_Binary<F>` (e.g., `FPN_Mul<64>` :1499). `FixedPoint<10,8>` has a *different template shape* (`int RADIX, int FRAC`) — it **cannot ride the `FPN_*<F>` family at all**, and the D-151 lesson (alias templates break deduction; FPN_Binary<64> had to be a concrete full specialization) applies equally to the decimal side. The "FPN_* op-family naming = a Ship-B decision" (D-163 non-goal) is therefore **load-bearing, not cosmetic**: every money op call site changes spelling by necessity (consistent with O-1 strong-typing intent, but the plan currently reads as if naming were optional polish). Fold into #1/#2.

### 2. #4 rounding helper / #3 divmul — PASS

- `divmul_pow10` proof artifacts exist: `plan_checks/2026-06-01-11-phase1-divmul-proof/{PROOF.md, divmul_pow10_proof.py, decimal_oracle.py}` ✓. No engine-side symbol collision.
- No existing `*HalfEven*`/rounding-helper name collision. The (q,r) producer→consumer chain is internal to the new family — no HEAD integration risk.

### 3. #5 exact decimal FromString — PASS with naming note

- Binary `FPN_FromString<64>` (`FixedPointN.hpp:394` generic, `:1579` 16B specialization) returns by value, **no error signal**. The decimal `(value, ok)` parse can't overload on return type and can't share the `unsigned F` template → distinct name/signature required (same forced-split as focus 1; the `.E.0.3`-absorbed `tt::` error-detecting family framing covers this — fine).
- Fill-adapter integration point EXISTS: `binance_json_extract_str` is already used at `BinanceUserData.hpp:348/:357/:363` — raw `"L"/"l"/"n"` strings are extractable without new JSON machinery (today they go through `binance_json_extract_double` :338-340/:361). B6's exact-parse rewrite has its callee. PASS.

### 4. #6 FPN_Quantize + MIN_NOTIONAL — **GAP [HIGH·dependency-not-decimal]**

- No name collision; `SymbolFilters` exists (`BinanceOrderAPI.hpp:75-82`); `binance_round_qty` :178 (called :511/:556) + `snprintf("%.*f")` :514/:559 is the all-double path #6 supersedes (plan B6 names :514/559 ✓).
- **GAP:** `SymbolFilters` money fields are **double** (`lot_step_size`, `lot_min_qty`, `lot_max_qty`, `min_notional` — :76-79). The plan declares SymbolFilters the #11 precision SSoT and quantization source, but quantizing decimal money by a double step (0.000001 is not double-exact) re-introduces the D-102 lossy detour at the final gate. Ship B must **re-type the SymbolFilters money fields to decimal (exact `FromString` at the exchangeInfo filters load)** — unenumerated work + an unlisted boundary. Add to #6 + the D-103 set.

### 5. D-103 boundary-cast enumeration (~12 sites) — **INCOMPLETE: 4 missed clusters**

All listed sites verified at HEAD: `ControllerEventLoop.hpp:2198` (RollingStats_Push cluster ✓), `PortfolioController.hpp:931-935` (EMA i128 blend ✓), `StrategyParameters.hpp:244-334` (spacing :248, fee floor :263-264, dip/tp/sl :322-334 ✓), `PortfolioController.hpp:1021-1023/:838-855/:1554-1566` ✓, `BinanceUserData.hpp:361-380` ✓, `GateParameters.hpp:171/:198` (B4 compares ✓), `Async.hpp:137/:179-180/:261-264/:865` ✓, `Run.hpp:653` ✓, `Reconcile.hpp:546` ✓ (B6), `TradeReader.hpp:145-146` double PnL recompute ✓ (B6).

**Missed (not in the ~12-site list nor B6):**

- **[HIGH·GAP] OrderManager.hpp:995-996 → :1369-1370 — internal paper-fill money round-trip.** Paper/backtest fills emit `cmd.result.avg_fill_price = FPN_ToDouble(event_price)` / `fill_qty = FPN_ToDouble(qty)` (:995-996), ship through the double-typed `OrderResult`, then re-ingress `o->avg_fill_price = FPN_FromDouble<F>(...)` (:1369-1370) — the exact D-102 lossy-carry shape, **inside the engine, on every non-live fill** (drives realized PnL + the backtest/money golden). C4 covers only the LIVE WS side. Also a **DRIFT**: the plan cites the C4 consumption as `OrderManager:1348-1349`; at HEAD that's the unknown-order fprintf guard — actual consumption is :1369-1370.
- **[MED·GAP] OrderManager.hpp:1431/:1442 — reconcile balance ingress.** `oms->balance = FPN_FromDouble<F>(exchange_balance)` + drift→`recon_event.price` — the boot/reconcile **balance** boundary, sister of `Run.hpp:653` (which IS listed). Money-bearing; unnamed.
- **[MED·GAP] ControllerEventLoop.hpp:2202/:2211-2219 — flow/depth feature-ingress cluster.** `CumDelta_Push(volume)` :2202; `double signed_vol = FPN_ToDouble(volume)` :2211 → `FlowState_Push(..., double)` :2213; `LargeTradeState_Push(..., volume)` :2214; `BookImbHistory_Push(depth_imbalance)` + `SpreadState_Push(depth_spread)` :2217-2219 (depth money → binary features upstream). The D-103 ingress list names only RollingStats_Push + the EMA blend. D-126's "LargeTradeState base-qty audit" action item acknowledges the area but the enumeration doesn't carry it. Note `FlowState_Push` takes **double** today (`FlowFeatures.hpp:253`) — a pre-existing ToDouble seam that the O-1 compile-error net will NOT catch (double-typed param swallows the cast silently).
- **[LOW-MED·GAP] TickRecorder.hpp:188-198 emit side + LabelFunctions.hpp:80-96.** Recorder emits price/qty via to_chars-from-double; recorded CSVs are the **replay/backtest money source** (`BacktestSharded.hpp:84-85` parse IS listed; the emit half isn't — if D-148's Explore sweep classified TickRecorder under log-emit future-opt, say so explicitly; record→replay is closer to the golden path than engine logs). LabelFunctions does all-double tp/sl first-passage money math (train-side; M5 label-boundary parity note).

### 6. B2 fee-site list — COMPLETE for the fee-shaped set; 2 adjacent misses

All B2 anchors verified at HEAD: `OrderManager.hpp:1160-1176/:1178-1210` (muls ~:1163/:1209 ✓ + `OrderManager_AccountMakerTakerFee` + dormant `OMS_GuardTakerBoundFeeBasis` ✓), `ControllerEventLoop.hpp:862-881` replay / `:1921-1967` production / `:3056` diag ✓, `Portfolio.hpp:205-207` ✓, `OrderEventLog.hpp:656-657/:675-678` ✓, `ControllerConfig.hpp:1366-1369 Fee_Compute` ✓ (maker/taker select), `EngineCommon.hpp:156-159` BnB `FromDouble(0.75)` ✓, legacy `PortfolioController.hpp:596/:855/:1314/:1343/:1566` ✓, `LegacyReferenceDriver.hpp:83+` ✓.

**Not fee-shaped, missed:**
- **[MED·DRIFT] PortfolioController.hpp:1215-1216** — `entry_fee = FPN_Mul(cost, ctrl->config.fee_rate_taker)` + `total_cost` — a real fee mul absent from B2's legacy list (1215 appears in blast-radius only as "sizing-divide"). Same file also :1410/:1414 `total_fees`/`total_taker_fees` accumulators (AddSat; type-migrate-only, LOW).
- **[MED·GAP] Slippage muls are money-rounding sites outside the fee rg shape.** `Portfolio.hpp:202` `slip = FPN_Mul(exit_price, slippage_pct)` (inside ExitBuffer_PendingProceeds, distinct from its listed fee mul :206) — plus `OrderPreResolved.slippage_pct` (`Order.hpp:142`) as a money-typed carry. D-105 says one canonical rounding mode at EVERY money mul/div "(all round)"; the #4-helper routing list should name the slippage mul(s) explicitly (only ~1 site — cheap to add).

### 7. Commission-carry field — PASS with layout enumeration gap [MED]

- **Filename≠type-name (Step 2a):** `OrderResult` is defined at **`CoreFrameworks/ExchangeAdapter.hpp:43`** (`commission` double :56, `avg_fill_price`/`fill_qty` doubles :46-47) — **ExchangeAdapter.hpp is named nowhere in the plan or sidecar** (B1 cites only the write `BinanceUserData.hpp:378` and the read `Reconcile.hpp:546`). The #5 sidecar's "decimal `OrderResult`" re-type lands in this file; it also rides the `Command` ring by value (drainer SPSC) → struct-size change surface.
- Carry vehicle EXISTS and is even documented as the extension point: `Order.hpp:143-146` reserves "Future per-resolved fields". One semantic correction: commission is **fill-time venue data**, not submit-time pre-resolve — it can't ride `Order_BindPreResolved`; it lands with the in-flight fill fields (`o->avg_fill_price`/`filled_qty` cohort at :1369-1370). B1's "rides this SAME pre-resolved/in-flight-Order vehicle" is right on the second half only.
- **Layout cascade to enumerate:** adding a 16B decimal commission to `Order<F>` breaks `Order.hpp:403` `sizeof(Order<64>)==256` (+ `:148` if placed in OrderPreResolved) and shifts `OrderEventLog` `entry_size` (:426/:466/:509) → another OEL format-version event at Ship B. All self-protecting (static_assert / version-gated header ✓), but per the plan's own R1 lesson the Ship-B relocation set should be enumerated up front, not discovered by red-build. Same note generalizes: **type-SWAPS to `<10,8>` keep sizeof==16 → layout asserts pass silently while persisted bytes change MEANING (2⁶⁴ vs 10⁸ scale)** — the snapshot/OEL version bumps (R3 again: 13/9/6 → +1 at Ship B) are the ONLY guard; the acceptance "version-rejected" row covers it, but list the constants explicitly in the Ship-B work-list.

### 8. Deprecated-path check (Step 4)

`PortfolioController.hpp` + `LegacyReferenceDriver.hpp` callees are legacy/deprecated-path — B2 already classes them "lower-priority type-migrates" ✓ correct handling. No Ship-B NEW function depends on a deprecated callee. CLEAN.

## Recommendations (plan amendments before the Ship-B gate)

1. Add to D-103: OM:995-996→:1369-1370 paper-fill round-trip (HIGH), OM:1431/:1442 reconcile balance, CEL:2202/:2211-2219 flow/depth ingress cluster (note FlowState's double param defeats the O-1 net), SymbolFilters re-type (with #6), TickRecorder emit disposition, LabelFunctions M5 note. Correct C4 anchor 1348-1349 → 1369-1370.
2. Add to B2: PC:1215-1216 (legacy list) + the slippage mul Portfolio.hpp:202 under the #4-routing/D-105 uniform-rounding umbrella.
3. Name `ExchangeAdapter.hpp:43-58` as the OrderResult re-type home; enumerate the Order/OEL layout+version cascade for the commission field; correct "pre-resolved vehicle" → in-flight fill fields.
4. State the forced op-family split for `<10,8>` (template-shape + D-151 deduction constraint) inside #1/#2 so the FPN_* naming decision is framed as required, not cosmetic.

— Layer-2 trace agent, 2026-06-09
