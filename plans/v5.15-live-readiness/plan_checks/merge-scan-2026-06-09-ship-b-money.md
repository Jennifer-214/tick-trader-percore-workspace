# /merge-scan report — Ship B (decimal money) remaining work — 2026-06-09

**Target plan:** `subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md` (v0.3, post-A.5 re-audit)
**Scope:** Ship-B REMAINING work only (decimal `<10,8>` instantiation + #3-#6 + B1-B6 + D-103 casts + FP64 absorb). DECIDED items D-97..D-167 not re-litigated.
**Engine HEAD:** 0e48150 (v5.15.5.F.4d.1.E.0.8; FPN_Binary<F> 16B two's-complement; FixedPoint<RADIX,FRAC> :82, <2,64> :84; traits :97-107).
**Skill sections N/A for a plan-scoped type-foundation scan:** repeated-atomic-load / clock-read / cfg-access (no new cross-thread or clock surface in Ship B); branch-vs-branchless (already governed by the plan's H20/D-145 commitments). Active sections: function-body parallelism (#4), state-field reuse (#5), cross-plan merge (#6).

Philosophy anchors: DESIGN_PHILOSOPHY § 4 (reuse-audit — two consumers doing the same work in one cycle/surface = merge candidate) and § 7 (structural-fix family — mirror patterns get a shared helper/chokepoint even under 70% overlap, Class-18 prevention).

---

## Ranked merge/reuse candidates

### 1. [HIGH · chokepoint] Fee math — ONE rate-agnostic `Fee_Apply(notional, rate)` core; rate SELECTION stays per-site

**FOCUS (b).** All 9 enumerated fee-charge sites compute the identical shape `fee = FPN_Mul(notional, rate)` and differ ONLY in where `rate` comes from:

- `OrderManager.hpp:1163` (buy) / `:1209` (sell) — `o->pre_resolved.fee_rate` (decision-time binding)
- `ControllerEventLoop.hpp:863/:877` (replay) + `:1923/:1967` (production) — `effective_cores[].fee_rate_taker`
- `Portfolio.hpp:206` (`ExitBuffer_PendingProceeds`) — `fee_rate` param
- `OrderEventLog.hpp:657/:676` (2nd replay) — `fee_rate` param
- `ControllerConfig.hpp:1366-1369` (`Fee_Compute`) — global cfg rate-select + mul (canonical for tests/legacy/global display ONLY)
- legacy: `PortfolioController.hpp:1215` family

**Answer to "can ONE chokepoint serve all":** YES for the MATH, NO for the rate-select. `Fee_Compute`'s own header comment (`ControllerConfig.hpp:1352-1364`) forbids per-core callers (Class 26 sub-shape B) — merging rate SOURCE into a widened Fee_Compute would reverse a settled discipline. The correct chokepoint is one level down: a rate-agnostic `Fee_Apply(notional, rate)` (= decimal mul + #4 venue-fee ROUND-UP + the B1/C3 LIVE-books-reported-commission fork lives here, once), called by all 9 sites with their own rate; `Fee_Compute` refits as a thin wrapper (rate-select → `Fee_Apply`) so its test/legacy consumers keep one name. This also dissolves a latent design tension: if decimal `FPN_Mul<10,8>` defaults to half-even (#4 internal mode), the fee sites need the ROUND-UP variant — without a named fee helper that's 9 per-site mode annotations (drift surface); with it, the mode lives in ONE body. Satisfies C2 ("all fee sites route through #4's helper") + B2's enumeration structurally.

**Exclusion (prevents over-application):** `EngineCommon.hpp:156-159` BNB discount is a rate-TRANSFORM, not a fee charge — `0.0001×0.75` is exact at ≤8dp (no rounding involved); it takes plain exact decimal mul + the B2 exact-decimal `0.75` constant (replacing `FPN_FromDouble<F>(0.75)` :156). Do NOT route it through `Fee_Apply` (round-up would distort the rate). Same for `ControllerEventLoop.hpp:3056` diag (H4-exempt candidate per B2).

**Affects:** #4, B1, B2, C2/C3, acceptance row "LIVE fee = exchange-reported".

### 2. [HIGH · duplicate-helper] 128×128→256 product — the C1 hoist landed as an inline COPY, not a shareable primitive; extract it BEFORE #3 copies it a third time

**FOCUS (c)+(e).** Answer to "is the planned hoist ALREADY effectively done?": **value-wise yes, structurally no.** At HEAD the 4-partial schoolbook product exists TWICE, inline:

- `FixedPoint64.hpp:142-152` (`FP64_Mul` guts — the original certified body)
- `FixedPointN.hpp:1289-1297` (`fp2_mul` — Ship A's hoist landed as a verbatim inline copy: `ll/lh/hl/hh → mid/shifted → mag`)

There is NO named callable primitive. The plan text for #3 says `divmul_pow10` "reuses #2's 128×128→256 primitive" (`P·M` 254-bit product, grab high end `>> S=153`) — at HEAD there is nothing to reuse BY NAME, so a literal implementation would author a THIRD copy of money-bearing product math (Class-18 mirror shape; three bodies that must stay bit-identical forever). **Proposal:** Ship B's first #2 deliverable = extract `umul_128x128_256(amag, bmag) → (hi, lo)` (or hi+mid accessor) as the named primitive; `fp2_mul` refactors onto it (value-identical — guarded by the frozen 16B golden + suite); `divmul_pow10` + `to_decimal` (item 6) consume it; `FP64_Mul`'s copy dies at the FP64 absorb. Note the decimal money MUL itself does NOT need it (operands ≤63-bit → native `__int128` product, per the sidecar #2 note) — the primitive's Ship-B consumers are `divmul_pow10` + the binary mul + `to_decimal`.

**Affects:** #2 (the "OPEN: pin against FP64_Mul's exact body" item — this IS the resolution), #3, FP64-absorb acceptance row.

### 3. [MED-HIGH · duplicate-state] #6 supersede = DELETE the double quantization apparatus + retype `SymbolFilters` money fields — else double-quantization drift

**FOCUS (d).** Existing apparatus at HEAD: `binance_round_qty` (`BinanceOrderAPI.hpp:178-181` — double truncate-to-step via `(int64_t)(qty/step)*step`), `binance_step_decimals` (:184-188), `%.*f` snprintf emit (:514/:559), filters load (:717). Two hazards if #6 merely ADDS `FPN_Quantize` at submit:

- **Double quantization:** OMS quantizes exactly (decimal), then `:511/:556` re-truncates in double — `lot_step_size` is a `double` (:76) and `0.00000100` is NOT binary-exact, so the double floor can land one step off the exact decimal result → silent submit-qty drift, exactly the class this ship kills.
- **`SymbolFilters` keeps money state in double:** `lot_step_size/lot_min_qty/lot_max_qty/min_notional` (`BinanceOrderAPI.hpp:75-82`) are the declared #11 precision SSoT (M5/H4-refire) yet stay `double` — the D-106 `static_assert(storage ≥ venue_precision)` guard would sit atop a lossy source.

**Proposal:** supersede = (i) qty crosses the `MarketBuy/MarketSell` boundary as exact decimal (or the pre-rendered exact wire string from #6's emit), (ii) `binance_round_qty` + `binance_step_decimals` + both `%.*f` sites DELETED (or demoted to assert-already-quantized during transition), (iii) `SymbolFilters` money fields retyped `FixedPoint<10,8>` (parse via #5 from the exchangeInfo strings). (ii)+(iii) are not explicitly in the plan's deliverable enumeration — the blast-radius row only says "SymbolFilters, qty-only; NO tickSize". **Affects:** #6, D-106 guard, B6 (which already names the supersede but not the deletion set).

### 4. [MED · duplicate-helper] #5 decimal FromString — sister is the BRANCHLESS `<64>` specialization (:1579), not the dead generic (:394); share the digit-scan front-end + POW10 table; fork only the scale tail

**FOCUS (a).** The FOCUS cite `FPN_FromString` :394 is the w[]/sign GENERIC — dead-for-instantiation at HEAD (primary `FPN_Binary<F>` is declaration-only except `<64>`); the LIVE body is the `<64>` specialization `FixedPointN.hpp:1579-1607`: branchless single-pass digit-accumulate (`int_part`/`frac_int`/`n_frac`/`seen_dot` masks) + a binary-only tail (`frac_low = (frac_int<<64)/POW10[nf]` :1603) + `POW10[20]` table (:1580). #5's decimal parser needs the IDENTICAL scan front-end; only the tail differs (`mantissa = int_part·10⁸ + frac_int·10^(8−nf)` + ok-flag semantics). **Proposal:** extract the scan into a shared front-end returning `(sign, int_part, frac_int, n_frac, ok)`; binary tail UNCHANGED in behavior (frozen golden + `build_probe/fromstring_difftest.cpp` 297/0 re-run guards the extraction); decimal tail consumes `ok` (malformed/scientific/overflow surfaced per #5), binary tail ignores it this ship (behavior change on the binary side would touch the frozen golden — out of Ship-B scope). Hoist `POW10` to namespace scope — the decimal tail needs `10^(8−nf)` and must not grow a second static table. This mirrors the plan's OWN #2 design rule (shared front-end, radix-fork only in the reduce) applied to parse. Sites confirmed: `BinanceCrypto.hpp:744-745`, `BinanceDepth.hpp:163-164`. **Affects:** #5.

### 5. [MED · cohort-gap] ONE `(value, ok)` parser must serve ALL FIVE money double-extraction families — REST sync-fill response parse is unenumerated

The plan's #5/B6/C4 cohort names UserData + Reconcile + cfg-file. At HEAD there are FIVE distinct money-ingest helper families that the one parser should replace at money fields:

1. `parse_double_fast` cfg branch — `CfgFieldDispatch.hpp:74-81` (`FPN_FromDouble` :81; plus the `v /= 100.0` KIND_DOUBLE_PCT scale :77-78, lossy in double — decimal-exact treatment = parse then exact ÷10² at boot cadence)
2. `binance_json_extract_double` — `BinanceUserData.hpp:361` (commission `n`) + :370-371 fill price/qty
3. `reconcile_get_double` — `Reconcile.hpp:544-546` (price/qty/commission)
4. `FPN_FromString` — `BinanceCrypto.hpp:744-745` / `BinanceDepth.hpp:163-164`
5. **UNENUMERATED:** `BinanceOrderAPI.hpp:534-536` REST sync-fill response — `executedQty`/`cummulativeQuoteQty` via `binance_json_extract_double` + `avg_price = cum_quote/exec_qty` computed in DOUBLE division; `fill_price_out/fill_qty_out` flow into `OrderResult` → P&L. Same class as the C4 WS-fill boundary (it is the REST FALLBACK of that exact path) — add to the #5 cohort + the avg-price divide becomes a decimal divide.

**Affects:** #5, B6, C4, M1.

### 6. [MED · compose-dont-author] `to_binary()`/`to_decimal()` — compose existing proven machinery; `FPN_FromFP64/ToFP64` are DEAD code to delete, not the shape to extend

**FOCUS (f).** `FPN_FromFP64/ToFP64` (`FixedPointN.hpp:466-489`) are `#ifdef FIXED_POINT_64_H`-gated word-relocation between SAME-radix layouts, deliberately NOT specialized for `<64>` (:1609-1611 note: "the engine red-build never instantiates them"), zero call sites outside the header (grep-verified) → DEAD at HEAD. They are the WRONG sister for the cross-radix casts (different math: 2⁶⁴↔10⁸ rescale, inherently rounding in one direction) and should be named in the FP64-absorb deletion set (plain dead code; not wire-visible, no H21 tombstone needed). The RIGHT composition: `to_decimal(b) = round₄(umul256(|b.v|, 10⁸) >> 64)` — reuses item-2's primitive + #4; `to_binary(d) = round₄(divmul_pow10-machinery on (|mant| << 64))` — the dividend `< 2¹²⁷` stays inside the PROVEN (M,S,N=127) domain (D-140), so the cast needs NO new reduce and NO new proof beyond a range note. Shape/edge-handling sister = `fp2_from_double/fp2_to_double` (:1372-1395 — deterministic saturate on out-of-range, branchless sign via `i128_cneg`). **Affects:** D-103 casts (~12 sites), FP64-absorb row, #3.

### 7. [LOW · duplicate-helper] Decimal sign handling calls `i128_abs`/`i128_cneg` (:1274-1275) — already reserved for Ship B; optionally fold `fp2_mul`'s inline re-derivation

The helpers' comment already promises "Reused by … Ship B's decimal math" — the decimal mul/div/casts must CALL them, not re-derive `(v^s)-s` inline. Note `fp2_mul` itself currently re-derives the trick inline (:1285-1287) instead of calling `i128_abs` six lines above it — a zero-semantic cosmetic fold available while in the file (golden-guarded). **Affects:** #2, D-103 casts.

### 8. [LOW · chokepoint-confirm] All four rounding consumers call the ONE `(q,r)` round core

#4's core is consumed by: the decimal Mul/Div internal reduce (half-even), `Fee_Apply` (round-up), #5's >8dp defensive round, #6's round-to-step, and the item-6 casts. #6's round-to-step uses a RUNTIME divisor (per-symbol step → no constexpr magic; submit cadence so a plain wide divide is fine per the sidecar) — but its round-from-`(q,r)` step must still be #4's function, not a re-derived `2r>step` inline. One body, five consumers — confirm in the D-93 design audit. **Affects:** #4/#5/#6.

### 9. [LOW · plan-accuracy] `BacktestSharded.hpp:84-85` is `FPN_FromDouble(h->price)` from a HistoricalTick DOUBLE, not a string parse

The blast-radius "Parse: string→money" row lists it alongside the string sites; at HEAD (:83-85) the backtest ingest is already-double (recorder format) → the exact-parse boundary for backtest lives at the TickRecorder/HistoricalTick format (D-102 sister), not a FromString swap at :84. One-line row correction so the #5 site list stays tool-verifiable. **Affects:** blast-radius table, #5 site enumeration.

---

## Overall recommendation

**Top-3 act-on:** items 1 (Fee_Apply chokepoint — capital-bearing, kills a 9-site mode-drift surface), 2 (extract umul256 BEFORE #3 lands a third copy), 3 (#6 deletion set + SymbolFilters retype — silent submit-qty drift otherwise).
**Fold into existing plan items (no new scope):** 4, 5, 6 sharpen #5/B6/D-103 wording; 8 is a design-audit checklist line.
**Leave alone / cosmetic:** 7 (fp2_mul inline abs — optional), 9 (row correction).
**Intentional non-merges (verified correct as-is):** rate-SELECT stays per-site (Class 26); BNB discount stays OUT of Fee_Apply; binary FromString behavior frozen (golden); decimal money mul does NOT adopt the 256-bit widen (native product suffices, per sidecar #2).

No candidate contradicts a DECIDED item; all six FOCUS questions answered above (a→4, b→1, c→2, d→3, e→2, f→6).
