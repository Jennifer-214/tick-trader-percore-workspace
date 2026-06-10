# Quorum money-correctness audit — auditor 3 of 3 (2026-06-09)

- **Target:** `subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md` (v0.3) + `subplans/2026-05-31-v5.15.5.F.4d.1.E-11-new-function-designs.md` (#1–#6) + `plan_checks/2026-06-01-11-phase1-divmul-proof/PROOF.md`
- **Engine HEAD:** 0e48150 (v5.15.5.F.4d.1.E.0.8). All citations re-verified against actual code this session.
- **Question:** where would the planned design, AS WRITTEN, produce wrong money values or wrong money behavior?
- **Verdict:** 1 CRIT, 2 HIGH, 2 MED, 1 LOW. Several angles CLEAN (listed at end).

---

## Finding 1 — CRIT — B1 books exchange-reported commission with NO denomination handling (base-asset BUY fees + BNB fees booked in the wrong unit)

**Where:** plan § Venue-SSoT R-1/F-A + § Re-fire B1 + acceptance row "LIVE fee = exchange-reported"; code `DataStream/BinanceUserData.hpp:361-363` (commission `n` parsed as double; `commission_asset` `N` parsed at :363, carried at :378-380), `CoreFrameworks/OrderManager.hpp:1163/:1209-1215` (fee → `total_fee` → `net = gross − total_fee` → `balance`), `CoreFrameworks/EngineCommon.hpp:154-165` (`pay_fees_in_bnb` is a real cfg mode).

**Why wrong:** The accounting chain is QUOTE-denominated (USDT): `net = gross − total_fee; balance += net`. The plan's own D-109 research states the commission is charged in the RECEIVED asset — **base on BUY, quote on SELL, BNB if enabled** — yet B1's fix is specified as "carry `result.commission` onto the in-flight Order + book it for LIVE," with no conversion step, no `commission_asset` check, and no design for the BNB case (which the engine explicitly supports via `pay_fees_in_bnb`). Booking the raw reported NUMBER:
- **Every LIVE BUY fill:** commission is in base (e.g., BTC). 0.00000750 BTC booked as 0.00000750 USDT understates the fee by ~the price factor (~70,000× at BTC $70k) → balance/realized PnL overstated on every round trip; `core_fees`, win/loss stats, and kill-switch drawdown all corrupted.
- **BNB mode:** ALL fills' commissions are BNB-denominated → wrong by the BNB/quote price factor, both sides.

Source-exactness of a number is not source-exactness of a VALUE when the unit differs. F-B ("base-asset fee = modeling approximation, low priority") covers the COMPUTE path only; B1 turns that known approximation into a unit ERROR on the booked path. **Corollary:** base-denominated commission also depletes the RECEIVED qty (actual base received = `fill_qty − commission`); the engine books `fill_qty` as position quantity → full-position SELLs can exceed actual holdings (live `-2010` / dust drift). Unaddressed anywhere in the plan.

**Required amendment:** B1 must specify denomination resolution: branch on `commission_asset` — quote → book raw; base → convert at the fill price (or deduct from qty + book converted); BNB → convert at BNB/quote (or flag-halt LIVE booking if no BNB price source, loud per D-106). The "computed-vs-reported empirical binding check" must include BUY fills and BNB-mode fills explicitly.

---

## Finding 2 — HIGH — replay recomputes fees; B1 makes LIVE replay≠production structurally unsatisfiable (OrderEvent carries no fee)

**Where:** `CoreFrameworks/OrderEventLog.hpp:79-92` (`OrderEvent` = price/qty/tp/sl — NO fee field), `:657/:676` (fold recomputes `fee = notional × fee_rate` param); `CoreFrameworks/ControllerEventLoop.hpp:863/:877` (per-core fold recomputes from `effective_cores[].fee_rate_taker`), `:953-955` (boot Init calls the fold with **nullptr cfg → "Replayed fees default to zero"** — per the in-code comment); plan C2/D-105 acceptance "replay==production rounding differential."

**Why wrong:** Both replay folds reconstruct booked money (`balance`, `realized_pnl`, `core_realized`, `core_fees`, `core_open_notional` — the last feeds budget/risk gating) by RECOMPUTING fees from a cfg rate. Once B1 books exchange-reported commission for LIVE, the booked fee is EXTERNAL DATA not derivable from `(price, qty, rate)` — replay can never reproduce it. The plan's C2 differential (replay==production ROUNDING parity) is the wrong test for LIVE: it can be GREEN on computed-fee parity while warm-restart replay still diverges from every LIVE-booked fill. Aggravators, verified at HEAD: (a) boot-context replay already books ZERO fees (nullptr cfg stub); (b) the two folds disagree with each other (per-core taker rate vs single `fee_rate` param). The plan never proposes adding a fee field to `OrderEvent` (a schema + `entry_size` change) nor declares LIVE replay fee-fidelity out of scope. As written, post-B1 warm restart silently rewrites LIVE money history with computed (or zero) fees.

**Required amendment:** either log the booked fee on the fill event (OrderEvent schema change + header gate bump) and make replay READ it, or explicitly scope replay to paper-fidelity and exclude LIVE fee reconstruction from the C2 gate with a documented bounded-drift statement.

---

## Finding 3 — HIGH — epoch rejection gap: Ship B changes money SEMANTICS at identical sizeof; event-log files have NO version gate at all

**Where:** `CoreFrameworks/OrderEventLog.hpp:126-131` (header = magic "OMSEL01" + `fpn_width` + `entry_size` only) + `:498-516` (load gates: all three pass unchanged across the decimal flip — `F` stays 64, money fields stay 16B, `entry_size` identical); `ShardedSnapshotPersist.hpp:94` (=9u, Ship-A bump), `PortfolioController.hpp:2026` (=13), `Portfolio.hpp:134` (=6); plan § R3 (marked EXECUTED at Ship A) + acceptance "old snapshots version-rejected."

**Why wrong:** Ship B reinterprets the SAME 16B `__int128` storage from 2⁻⁶⁴ scale to 10⁻⁸ scale — a semantic flip with **zero layout change**. Two gaps:
- **(a) Event-log files:** no version field exists; magic/`fpn_width`/`entry_size` are ALL unchanged at Ship B → a pre-decimal event log loads cleanly into the decimal engine and replays binary-scaled prices/qtys as decimals (values wrong by ~2⁶⁴/10⁸ ≈ 1.8×10¹¹) into `balance`/`core_*` at warm restart. Ship A was protected incidentally (24→16 changed `entry_size`); Ship B has NO such accident. The plan's persistence acceptance row names `ShardedSnapshotPersist` only — event-log files are never mentioned as an epoch surface.
- **(b) Snapshot versions:** the only enumerated bumps (R3 → 13/9/6) were CONSUMED at Ship A, and the plan's own bump-trigger discipline is keyed to "the same ship `sizeof(FPN)` changed" — which does NOT fire at Ship B (16B→16B). The Ship-B bump (→14/10/7) exists only as an implied outcome ("version-rejected"), not as an enumerated work item. A literal implementer ships the semantic flip with all layout `static_assert`s green, the version test silent, and v9/v13/v6 files loading as garbage decimal money.

**Required amendment:** enumerate explicit Ship-B version bumps for all three snapshot constants AND add an epoch gate to the OrderEventLog header (version field or new magic, e.g. "OMSEL02"); re-key the layout-coupled-version test to "money REPRESENTATION changed," not sizeof.

---

## Finding 4 — MED — #6 promises tickSize/PRICE quantization from a source that doesn't carry it

**Where:** sidecar #6 ("Quantize value to venue `tickSize`/`stepSize` … off the already-loaded `SymbolFilters`"); `DataStream/BinanceOrderAPI.hpp:75-82` (`SymbolFilters` = lot_step/min_qty/max_qty/min_notional/qty_decimals — **no tickSize, no price field**); plan blast-radius row itself: "NO `tickSize`/PRICE_FILTER anywhere"; § Venue-SSoT defers `price_decimals`/`tickSize` columns to `.E.1`'s ExchangeRegistry.

**Why wrong:** Internal contradiction — the #6 deliverable cannot be built from its declared data source. PRICE quantization has no data at Ship B as written. Benign while the engine is MARKET-only (no price on submitted orders, per the dormant maker guard at `OrderManager.hpp:1140-1145`), but the deliverable either silently shrinks to qty+notional (gap goes live with LIMIT orders / TECH_DEBT-154) or forces unplanned exchangeInfo-parse work mid-ship. Secondary: paper-fill parity — paper fills book intended (unquantized) qty while live books venue-quantized fills; #6 quantizes "at order submit" only, leaving paper↔live qty drift (bounded by one step) unaddressed.

**Required amendment:** either add PRICE_FILTER/tickSize to the `SymbolFilters` load at Ship B, or scope #6 explicitly to stepSize+MIN_NOTIONAL with a tombstoned tickSize row pointing at `.E.1`; state paper-side quantization parity either way.

---

## Finding 5 — MED — money overflow "flag-loud" posture has no mechanism and no acceptance row; inherited default is SILENT saturate

**Where:** plan D-147 ("flag-loud deferred to Ship-B money," "still live"); PROOF.md guard ("routes any out-of-range value to the existing overflow/flag path"); code: the existing path is branchless `of_mask` saturate (`FixedPointN.hpp` mul cores) — silent, no flag; plan § Acceptance criteria — no row for money-op overflow behavior.

**Why wrong:** For money, saturate-to-MAX is a silently wrong value (D-147's own posture says so). The divmul `|operand|<2⁶³` guard's correct-by-construction claim depends on the violation ACTION being loud — but no flag/halt mechanism is designed anywhere (SHALT code? counter? kill-switch?), and the acceptance list lets Ship B close with decimal ops inheriting binary's silent saturation while formally meeting every row. Practically unreachable for venue-bounded operands (P_max≈2¹¹⁰ vs 2¹²⁶), which is why this is MED not HIGH — but the guard exists precisely for the un-modeled case.

**Required amendment:** add an acceptance row: decimal money ops trip a LOUD, tested flag path (named mechanism) on guard violation/overflow; saturate-silent is binary-only.

---

## Finding 6 — LOW — #5 reject-set is function-level only; per-site `ok=false` handling unspecified

**Where:** sidecar #5 ("error-detecting `(value, ok)` — surfaced, never silent-zero"); sites `BinanceCrypto.hpp:744-745` (tick ingest), `BinanceUserData.hpp:361` (fill `n` parse), `Reconcile.hpp:544-546`.

**Why wrong:** The contract stops at the function boundary. What each money SITE does on `ok=false` is undefined: a malformed tick (drop the tick, presumably — matching the :738-741 skip pattern) vs a malformed FILL price/qty/commission (a real executed trade the engine then can't book → position/balance desync if simply dropped, which is worse than a parse error). Fill-parse failure handling needs an explicit disposition (halt/flag/reconcile-trigger), not just an `ok` flag.

---

## CLEAN angles (verified)

- **Negative-PnL rounding:** #4 half-even on unsigned magnitude + sign reapplied = value-symmetric (RHE(−x) = −RHE(x); the parity tie-break is magnitude-invariant). Correct for negative PnL/fees. CLEAN.
- **divmul_pow10 proof + integration:** G–M analytic bound + predicate validated against exhaustive small-case ground truth + 208k differential is a sound proof shape; N=127 with per-operand <2⁶³ guard exactly admits Binance's maxQty (2⁶³−1 in 10⁻⁸ units) and the product stays <2¹²⁶ within the proven range. Constants check out. CLEAN (subject to Finding 5's violation-action gap).
- **Wire dispatchers (B3):** verified at HEAD — `CfgFieldDispatch.hpp:331-336` family `static_assert` excludes decimal; disjoint traits at `FixedPointN.hpp:97-107`. A decimal cfg/stamp field red-builds until the exact-decimal branch is written; it cannot silently take the `%.17g` lossy path. CLEAN as claimed.
- **Persist round-trip exactness:** raw fwrite/fread of the 16B scaled int is bit-exact by construction; exactness itself is CLEAN (the epoch gate is Finding 3, a separate failure).
- **Boundary-cast direction (D-103):** no BOOKED money derives from binary round-trips — decimal→binary is feature-ingress only; binary→decimal egress lands on decision thresholds (TP/SL/dip), which become exact money at the cast and are re-anchored by venue fills; sizing divides are all-decimal. Lossy-by-design is confined to the signal domain. CLEAN.
- **Parse exactness (#5 math):** single-pass digit-accumulate at ≤8dp into 10⁸ scale is exact; reject set (malformed/overflow/>8dp/scientific) is enumerated and oracle-tested incl. the venue-alphabet asymmetry. CLEAN at the function layer (site layer = Finding 6).
- **BNB 0.75 cfg factor (`EngineCommon.hpp:156`):** exactly representable in both radices; already dispositioned in B2 as an exact decimal constant. CLEAN.
- **Hot path:** money compares only; the 3 rare-entry muls + fixed-cost reduce claim verified consistent with the proof. CLEAN.

## Synthesis note

Findings 1+2 share a root: **B1 changes the SOURCE of the booked fee (computed → external) without re-deriving the consequences for every consumer of "fee"** (denomination unit, replay reconstruction, event-log schema). Finding 3 shares a root with the plan's Ship-A framing: **epoch gates were keyed to LAYOUT change, but Ship B is a SEMANTIC change at identical layout** — every layout-keyed guard goes silent exactly when the meaning flips.

— auditor 3/3, independent; no coordination with auditors 1-2.
