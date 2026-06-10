# Adversarial verification pass (Stage 3.5) — 2026-06-09 — Ship B (decimal money) pre-coding gate

## Context

- **Role:** adversarial re-verification of the 11-auditor findings set (V1-V12) against ACTUAL CODE at HEAD. Default-skeptical both directions; every claim re-derived from disk (auditors' permission prompts were partially denied mid-run, so report text was NOT trusted).
- **Plan target:** `plans/v5.15-live-readiness/subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md` (v0.3)
- **Decision log:** `plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md` (D-97..D-167)
- **HEAD verified:** `0e48150` (`feat/v5.15-live-readiness`, Version 5.15.5.F.4d.1.E.0.8)
- **Method:** direct Read/grep of every cited file:line; plan + decision-log text greps; oracle source read. No subagents, no edits to engine or plan.

## Verdict table

| # | Verdict | Severity upheld? |
|---|---|---|
| V1 | **REAL** (all 4 sub-claims) | CRIT upheld |
| V2 | **REAL** | CRIT upheld (single-source but code-verified) |
| V3 | **REAL** (all 3 sub-claims) | HIGH upheld |
| V4 | **REAL** (a, b, c all confirmed) | HIGH upheld |
| V5 | **REAL** | HIGH upheld |
| V6 | **REAL** | HIGH upheld |
| V7 | **REAL** (mechanics verified) | HIGH upheld |
| V8 | **REAL** (sites verified; nuance on (c)) | HIGH upheld |
| V9 | **REAL** | HIGH upheld |
| V10 | **REAL** (with qty_decimals nuance) | HIGH defensible (MED-HIGH) |
| V11 | **RESOLVED → quorum-2 correct** (floor pinned); quorum-1 WRONG | conflict closed |
| V12 | **REAL** (and the class is WIDER than fees) | MED→ raise to HIGH recommended |

No finding killed. One conflict resolved (V11). Several cited line numbers off by 1-6 lines — substance holds in every case (list at bottom).

---

## V1 — B1 commission-asset unit error + plan-contradicts-D-127 + oversell corollary — REAL (CRIT)

**Sub-claim A — code parses but never consumes commission/commission_asset: CONFIRMED.**
- `DataStream/BinanceUserData.hpp:361-363` parses `"n"` (double) + `"N"` (asset string) — exact lines as cited; written into OrderResult at `:378-380`.
- `CoreFrameworks/ExchangeAdapter.hpp:56-57` — `double commission` + `char commission_asset[8]` (cited `:57` exact).
- Comprehensive grep across all engine source: the ONLY other `commission` site is `Reconcile.hpp:546` (`ReconcileTrade.commission` parsed from REST myTrades — also reaches no P&L math). `OrderManager_ProcessFillCommand` (`OrderManager.hpp:1321-1417`) reads success/exchange_id/fill_qty/avg_fill_price/is_maker/order_complete — NEVER `cmd.result.commission` or `commission_asset`. "Consumed nowhere" is exact.

**Sub-claim B — booking sinks are quote-denominated from cfg rate: CONFIRMED.**
- Entry: `OrderManager.hpp:1161-1163` `entry_fee = FPN_Mul(FPN_Mul(fill_price, fill_qty), o->pre_resolved.fee_rate)` → `Portfolio_OpenSlot(..., entry_fee)` at `:1166-1168`.
- Exit: `:1207-1215` `exit_fee = FPN_Mul(exit_notional, exit_rate)` → `total_fee` → `net` → `oms->balance` (cited `:1209-1216` exact).

**Sub-claim C — plan body contradicts decided D-127: CONFIRMED — this is the core defect.**
- Decision log `:802-803` **D-127**: "fees = TWO distinct numbers; **F-B ... FOLDED INTO the design (operator rejected 'minor'-defer = PL-4): book asset-aware** — quote = direct, base (BUY) = via fill price (exact), BNB = needs BNB/quote price → NAME the dependency / fail-loud, never silently approximate."
- Plan body `:165` still carries the PRE-D-127 framing: "**F-B (note, pre-existing)** ... → modeling approximation (not decimal-introduced; **low priority**)" — directly contradicts "operator rejected minor-defer".
- Plan body B1 operative fix text `:245`: "carry `result.commission` onto the in-flight Order ... + book it for LIVE" — **NO commission_asset dimension anywhere in the fix text**. Acceptance row `:333` same.
- The banner `:29` does say "F-B folded (D-127)" — so the AMENDMENT HEADER was updated but the OPERATIVE BODY SECTIONS (165 / 245 / 333) were not. An implementer working from B1-as-written books a base-denominated `n` (BUY) raw into the quote fee sink → **~price-factor understatement** (BTCUSDT ~1e5×). Unit analysis correct.

**Sub-claim D — oversell/dust corollary: CONFIRMED + UNCOVERED.**
- `OrderManager.hpp:1166` books FULL `fill_qty` into `Portfolio_OpenSlot`. Binance `"l"` is gross executed qty; when `N`==base (BUY default without BNB), actual received base = `l − n`. Engine's booked position qty > actual holdings → exit SELL of booked qty oversells / leaves dust.
- D-127 covers the fee **booking dimension** only; neither the plan nor D-127 text addresses **received-qty depletion**. Grep for oversell/dust/depletes across plan + decision log: zero hits. This is an ADDITIONAL design gap beyond restoring D-127 into B1.

**Required amendment:** rewrite B1 + F-B note + acceptance to carry D-127's asset-aware booking verbatim (quote direct / base via fill price / BNB fail-loud), and ADD the qty-depletion decision (book `l − n` when `N`==base, or reconcile-driven dust handling) as a named B1 sub-item.

---

## V2 — Multi-fill vehicle gap: slot freed after first partial — REAL (CRIT, pre-existing live bug)

**Control flow traced at HEAD (`OrderManager.hpp:1321-1417`):**
- `:1383` `Order_SetState(o, cmd.result.order_complete ? ORDER_FILLED : ORDER_PARTIAL)` — exact as cited.
- The ONLY returns-before-free are: WS surprise fill `:1323-1328`, slot-not-found `:1341-1350`, already-FILLED dedup `:1355`, and the ACK-only path `:1364-1367` (`fill_qty==0.0 && avg_fill_price==0.0` → ORDER_ACKNOWLEDGED, "slot stays open"). A PARTIAL fill (`fill_qty>0`, `order_complete=0`) falls THROUGH the success branch — `HandleFill` books the partial at `:1389-1393` — and reaches `:1414-1415` **`// Free the slot on terminal transition.` `oms->order_bitmap &= ~(1u << slot);` UNCONDITIONALLY**. The free is NOT inside a terminal-status guard. Confirmed: comment claims terminal-only; code frees on PARTIAL too.
- Comment contradiction confirmed at `:1380-1382`: "we err toward PARTIAL — **keeps the order alive in the OMS, won't lose track. Subsequent fill events resolve to FILLED**" — false at HEAD; the slot is freed 33 lines later.
- Fills 2..N dropped: `:1335-1339` decodes slot from `order_id` bits 63..60 and requires `order_bitmap` bit set + id match → after the free, `slot=-1` → `:1341-1350` skips. **WS fills skip SILENTLY** (the fprintf at `:1344-1348` fires only for `CMD_FILL_RESULT`). Only fill 1's qty books (`o->filled_qty` OVERWRITTEN at `:1370`, not accumulated).
- `ORDER_PARTIAL` grep: exactly 2 sites codebase-wide (`Order.hpp:67` enum, `OrderManager.hpp:1383` set) — NO sweeper/re-arm path exists.

**Pre-existing live accounting bug: YES.** Live WS multi-fill (a market order sweeping book levels emits one executionReport per trade) books only fill 1; portfolio qty + fees diverge from exchange reality at HEAD, before any Ship-B work.

**Breaks B1's carry-accumulate design: YES.** B1 `:245` carries commission "onto the in-flight Order" — the vehicle is freed after fill 1, and fills 2..N never even reach `ProcessFillCommand` with a live slot. D-109's "per-fill then summed" (plan `:163`) requires an accumulator that survives fills; the plan contains NO multi-fill design (grep partial/multi-fill: only the D-109 convention READ).

**Trap for the fixer (found during verification):** the paper path DEPENDS on the unconditional free — synthetic fills `memset` the result (`:993`) so `order_complete=0` → paper orders are set ORDER_PARTIAL yet must free the slot (and `total_filled` is never incremented for them, `:1384-1386`). A naive "free only on FILLED" fix leaks every paper slot. The fix must also set `order_complete=1` on synthetic paper fills (`:989-996`) or rework the terminal condition.

---

## V3 — OrderEvent carries no fee; replay folds recompute; boot replay = zero fees — REAL (all 3)

1. `OrderEventLog.hpp:79-92` `OrderEvent<F>` fields: event_id/order_id/timestamp_us/type/order_type/core_id/_pad/price/qty/tp/sl/reason — **NO fee field**. Cited lines exact.
2. Both folds recompute from a rate: `OrderEventLog.hpp:656-657` `entry_fee = FPN_Mul(notional, fee_rate)` + `:676-677` `exit_fee` (Portfolio_FromEventLog, rate is a caller param); `ControllerEventLoop.hpp:861-880` Reconstruct fold recomputes from `effective_cores[core_id].fee_rate_taker`.
3. Boot-Init nullptr: `ControllerEventLoop.hpp:951-953` — in-code comment verbatim: "no cfg available at boot Init context; pass nullptr. **Replayed fees default to zero**" → `EventLoopState_ReconstructPerCoreFromEventLog(state)` single-arg; `:839-840` substitutes zeroed `NULL_PER_CORE_CFG_STUB_ARRAY` → `fee_rate_taker = 0` → replayed fees ZERO. (Auditor cited `:953-955`; actual `:951-953` — substance exact.)

Consequence for Ship B confirmed: fee replay can never be source-exact (D-106/D-127 booked-fee) without an OrderEvent fee field — replay≠production divergence is structural today.

---

## V4 — Same-sizeof semantic flip silences every epoch guard — REAL (a+b+c)

- **(a)** `tests/controller_test.cpp:~24448-24453`: `static_assert(CONTROLLER_SNAPSHOT_VERSION >= 13 && SHARDED_SNAPSHOT_VERSION >= 9u && PORTFOLIO_SNAPSHOT_VERSION >= 6)` — comment SAYS ">= keeps it forward-compatible with any later ship (e.g. Ship B decimal) bumping further" — i.e. an UN-bumped Ship B passes 13/9/6 ≥ 13/9/6. Confirmed.
- **(b)** Plan `:235` discipline text: "a layout-coupled-version test asserts each strictly increased **in the same ship `sizeof(FPN)` changed**". `FixedPoint<10,8>` is 16B (D-125/126 two's-complement core) — sizeof does NOT change at the decimal flip → the trigger never fires. Plan `:191` even phrases the Ship-B reject as "decimal `sizeof(FPN)`/layout change → old snapshots rejected by version bump" — but the decimal flip changes NEITHER sizeof NOR layout, only raw-int semantics (2^64 scale → 10^8 scale). The plan's own premise is wrong about what changes.
- **(c)** `OrderEventLog.hpp:126-131` header = `magic[8] "OMSEL01\0"` + `fpn_width` + `entry_size` + `reserved[2]` ("future: checksum, **version**" — never added). Loader `:498-512` checks exactly those three. At Ship B: magic unchanged, `fpn_width = F = 64` unchanged, `entry_size = sizeof(OrderEvent<F>)` unchanged (16B fields → 16B fields) → **pre-epoch binary-radix logs load cleanly and replay misscaled** (raw 64.64 ints reinterpreted as ×10^8 decimals). Ship A was protected by ACCIDENT (24B→16B changed entry_size); Ship B has no such accident.

**Required amendment:** plan must name explicit Ship-B bumps — snapshot versions 14/10/7 (+ test floors raised in the same ship) AND an event-log epoch mechanism (magic `"OMSEL02"` or populate the reserved version word + loader check).

---

## V5 — cfg_drift_compare silent fall-through for unmatched type combos — REAL

Full bodies read at `CfgFieldDispatch.hpp`:
- `:456-461` static_assert constrains **StampT ONLY** (fp_binary | floating | integral | array) — CfgT unconstrained.
- if-constexpr chain `:463-485` covers exactly (float,fpb) / (fpb,fpb) / (float,float) / (array,array) / (int,int); NO `always_false` final else; `:486` **`return false;`** fall-through.
- `cfg_drift_compare<double, FixedPoint<10,8>>`: StampT=double passes the assert; `is_fp_binary_v<FixedPoint<10,8>>` is false (trait matches `<2,F>` only — disjoint traits landed at A.5, `is_fp_decimal_v` exists at `FixedPointN.hpp:100-102`); no branch matches → compiles → returns false = **silent no-drift on a money-rate field**. Exactly as claimed.
- Same shape in `cfg_drift_format_reason`: assert `:505-510`, fall-through `return 0;` at `:532`. Production walker confirmed: `CoreModelZoo.hpp:238` `DRIFT_CHECK_FROM_DERIVED(...)`.

Armed exactly at Ship B (the moment STAMP_BOUND money rates go decimal). Fix = exhaustive `static_assert(always_false<StampT,CfgT>)` final else + decimal branches, sequenced BEFORE/WITH the money flip (matches parity F1).

---

## V6 — No mechanical pre-epoch stamp rejection — REAL

- `ModelInference.hpp:141-142`: `STAMP_FORMAT_VERSION_CURRENT = 2` / `MAX_SUPPORTED_STAMP_FORMAT_VERSION = 2`, comment "parser accepts [1, MAX] inclusive".
- `:1544-1551`: rejects ONLY `> MAX` ("Reject FUTURE versions only"); legacy [1,2] loads. (Cited `:1540-1549`; actual check `:1544` — region matches.)
- `training_fingerprint`: `:511-512` strncpy (parse), `:537-538` printf (display) — no gating consumer. Confirmed parse+display only.
- Plan grep: **zero** `STAMP_FORMAT_VERSION` mentions in the plan body — the bump is not currently mandated anywhere in Ship-B scope. A binary-epoch stamp (v1/v2) loads silently into the decimal engine; drift detection won't save it (V5's fall-through is on the same path). REAL; plan must name the stamp_format_version bump (3) + MAX gate as a Ship-B acceptance row.

---

## V7 — B4 price-domain fork: one arm violates hot-path-untouched — REAL

- Hot compares confirmed: `GateParameters.hpp:~170-174` BG (`FPN_LessThan/GreaterThan(tick.price, params->bg_price_threshold)` + volume compare), `:~199-200` SG (`current_price` vs `effective_tp`/`effective_sl` after `FPN_Max` ratchets). Cited `:171/:198` within ±2.
- Plan B4 `:248` leaves the fork OPEN ("Pick one"): (i) "tick.price casts to binary at compare" → a cross-radix scale conversion (×2^64/10^8-class op, divmul-magnitude work, ~20-25cyc estimate plausible per the D-140 proof's own divmul cost) executed PER TICK on 2-4 operands (price+volume in BG; price reuse in SG ×2 legs) INSIDE `BG/SG_Evaluate` — contradicts plan `:195`'s load-bearing claim "**Hot path: UNTOUCHED at per-tick cost** — the 500ns steady path does money COMPARES (identical in decimal)". (ii) Egress arm: thresholds are PRODUCED on the slow path (StrategyParameters egress cluster, D-103 `:192`) → convert at gate-build, slow cadence ≤100μs, hot compares stay same-radix scaled-int compares = zero per-tick delta. Mechanics check out exactly as the convergent finding states.
- Verdict: REAL — and the fork is not actually free to "pick one": arm (i) falsifies the plan's own hot-path premise (H8/H7 exposure). B4 should be amended to RESOLVE to egress, not offer the fork.

---

## V8 — Internal lossy money round-trips — REAL (sites verified; one nuance)

- **(a)** Paper/backtest fill: `OrderManager.hpp:995-996` `cmd.result.avg_fill_price = FPN_ToDouble(event_price); cmd.result.fill_qty = FPN_ToDouble(qty);` → back through `:1369-1370` `FPN_FromDouble` — a full FPN→double→FPN round-trip on EVERY paper fill. Confirmed.
- **(b)** REST sync-fill: `BinanceOrderAPI.hpp:533-535` `executedQty`/`cummulativeQuoteQty` extracted as doubles + `avg_price = cum_quote / exec_qty` double-division (a derived, non-source value). Confirmed (cited `:533-537`).
- **(c)** `ExchangeAdapter.hpp:43-58` OrderResult money fields all double (`avg_fill_price`/`fill_qty`/`commission`). Confirmed.
- **Nuance:** (c) IS structurally decided — D-123 (decision log `:779`) mandates decimal OrderResult + string→decimal parse. But D-123's parse scope names the WS path (`BinanceUserData :304-305/:338`); the plan body's D-103 ~12-site enumeration (`:192`) and B6 (`:249`, which names BinanceOrderAPI only for `:514/559` qty ROUNDING) include NEITHER the paper-fill emit (a) NOR the REST fill-parse (b). "The plan misses" holds for (a)+(b): an implementer converting the enumerated sites leaves doubles flowing into a decimal OrderResult from two producers. Amendment = add both sites to the D-103/B6 enumeration ((a) becomes a no-op decimal passthrough; (b) needs string-extract or exact re-derivation, and avg_price should derive from decimal division or be carried as (cum_quote, exec_qty)).

---

## V9 — Decimal general-division design gap — REAL

- Call sites confirmed (money÷money, runtime divisor): `PortfolioController.hpp:1186` `sized_qty = FPN_DivNoAssert(risk_amount, fill_price)` (SIZING — order qty); `ControllerEventLoop.hpp:2853` `max_qty = FPN_DivNoAssert(budget_remaining, entry_price)`; `:2906` `core_dd_pct = drop/peak`; `:3256` `dd = drop/ks_peak_balance`. (Cited "1186 or 1215 region": 1186 exact; nearby money-operand divisions also at `:1195/:1240`; nothing at literal 1215 — substance holds.)
- `udiv_q64` shape confirmed `FixedPointN.hpp:1336-1343`: seeds `rem_hi = a_mag >> 64, rem_lo = a_mag << 64` — **the `<<64` BINARY-radix widening is hardcoded** (computes (a·2^64)/b). Decimal needs (a·10^8)/b — a different widening; naive `a.v*10^8` overflows __int128 for large balances AND `__int128/__int128` emits `__udivti3` (variable-latency libcall) — both halves of the claim correct.
- Design artifact absent: the #1-#6 sidecar (`2026-05-31-...-11-new-function-designs.md`) covers type/multiply/divmul_pow10(constant 10^8 reduce)/rounding/parse/quantize — **no general-divisor Div**. #1 (`:23`) even acknowledges "radix appears ONLY in the mul-reduce + **div**" yet no Div design exists. The D-100 oracle (`decimal_oracle.py`) has ops mul_halfeven/fee_roundup/from_string/quantize — **no div reference** → the one-time correctness gate cannot certify division. REAL; a `udiv`-sister with 10^8 pre-widening (the 256-bit `rem_hi:rem_lo` seed structure supports it) + oracle Div op + rounding-mode decision must be added to the design set. (Ratio-shaped sites `:2906/:3256` may alternatively resolve as cast-to-binary-ratio — but that TOO is an undesigned decision.)

---

## V10 — SymbolFilters money fields are double — REAL (one mitigating nuance)

- `BinanceOrderAPI.hpp:76-79`: `double lot_step_size; double lot_min_qty; double lot_max_qty; double min_notional;` — exact as cited.
- Plan names `SymbolFilters` the "#11 precision/quantization source" FOUR times (`:158/:173/:193/:329`) and claims TECH_DEBT-146 closure (`:92`), yet NO enumeration retypes the double fields or exact-parses `stepSize`/`minNotional` strings from exchangeInfo. The D-100 oracle pins #6 as multiple-of-STEP (`oracle_quantize(value_scaled, step_scaled)`) → the step VALUE is in the contract → sourcing it from a double re-introduces the lossy detour at the quantize boundary; `min_notional` is a money comparison needing a typed boundary.
- **Nuance:** `qty_decimals` (int, `:80`) is exact, and IF `FPN_Quantize(value, decimals)` (D-104 signature) quantizes by decimal places only, the double step never enters the math for power-of-10 steps. But the oracle's step contract is general, and min_notional remains uncovered either way. Verdict REAL; amendment = enumerate the SymbolFilters retype (or exact string-parse at load) in the D-103/#5 cohort.

---

## V11 — Quantize-to-step direction conflict — RESOLVED: quorum-2 CORRECT, quorum-1 WRONG

- Oracle read directly (`plan_checks/2026-06-01-11-phase1-divmul-proof/decimal_oracle.py`): `:72-74` `oracle_quantize` = "round value **DOWN** to a multiple of step" = `(value_scaled // step_scaled) * step_scaled` (floor on non-negative scaled ints); `:206-208` engine contract comment "engine quantize = **floor-to-step** (same as oracle here; **pins the contract**)" + asserts `quantize(v,step) <= v`.
- D-104 (decision log `:663`) independently says "exact decimal-**truncate**-to-step".
- Quorum-1 conflated #4 with #6: half-even (`oracle_mul_halfeven`) is the MUL-reduce rounding; the fee variant is ROUND_CEILING; QUANTIZE is a separate pinned-floor op. Any upstream half-even in sizing math is then FLOORED to the step at submit → submitted qty ≤ computed qty ≤ holdings. No oversell-by-rounding path exists as designed. (Oversell risk lives in V1-D/V2 — commission depletion + multi-fill — NOT in rounding direction.)

---

## V12 — KIND_DOUBLE_PCT percent-form defaults vs unscaled assign — REAL; class WIDER than fees

- Registry: `CfgFieldRegistry.hpp:674` `fee_rate_maker DBL(0.075, ...)` / `:675` `fee_rate_taker DBL(0.100, ...)` — percent-form per their own tooltips ("0.100 = 0.100%"). Cited lines exact. Legacy `fee_rate :471` `DBL(0.1, ...)` same.
- Manual init: `ControllerConfig.hpp:1527-1528` `FromDouble(0.00075)` / `FromDouble(0.00100)` — fraction-form. Cited `:1528` exact.
- Mechanism: `cfg_assign_field` (`CfgFieldDispatch.hpp:240-242`) does **NO ÷100** — its comment even asserts "Default is stored as fraction (NOT percent); no PCT scaling needed", which the fee rows violate. `cfg_diff_field` (`:281-284`) same raw compare (→ permanent false "modified" badge today).
- Who wins at boot: the per-core mirror walker fires at `ControllerConfig.hpp:1505` (`FOREACH_PER_CORE_CFG_FIELD(EMIT_PER_CORE_CFG_DEFAULT_GLOBAL_MIRROR)`) writing 0.100-as-fraction = **10%**, then the manual lines at `:1527-1528` overwrite with the correct fractions — **manual-init ordering is the ONLY mask**, exactly as claimed.
- What arms it: the in-code migration plan at `:1497-1501` — "manual init lines for per-core registry rows ... **deleted at Phase Cx-E.3** atomically" — plus the standing registry-default-SSoT rule ("manual struct initializer FORBIDDEN"). Deleting the fee manual lines under that rule = live 100× fee misassign.
- **Wider than filed:** the same shape exists on `take_profit_pct` (`:469` DBL(3.0) vs manual `FromDouble(0.03)`), `stop_loss_pct` (`:470` 1.5 vs 0.015), `risk_pct` (`:477` 2.0 vs 0.02), etc. — while `lazy_rebuild_price_threshold_pct` (`:456` DBL(0.0005)) is fraction-form. The KIND_DOUBLE_PCT cohort is internally INCONSISTENT about payload units. Recommend raising to HIGH and sweeping the whole PCT cohort (pick one unit convention + a unit-consistency check), not just the fee rows. PARITY-037 confirmed filed (`DOCS/PARITY_ISSUES.md:1477`).

---

## Line-cite corrections (substance holds in all)

| Finding | Cited | Actual |
|---|---|---|
| V2 | `:1336-1344` (drop window) | `:1335-1350` (lookup `:1335-1339`, skip `:1341-1350`; WS branch silent) |
| V3 | CEL `:953-955` | `:951-953` (comment `:951-952`, call `:953`) |
| V4 | controller_test `~24446` | static_assert `~24448-24453` |
| V6 | `:1540-1549` | bounds check `:1544-1551` |
| V7 | GateParameters `:171/:198` | within ±2 (BG compares ~`:170-174`, SG ~`:199-200`) |
| V9 | PortfolioController `:1215` | sizing div at `:1186` (also `:1195/:1240`); nothing at literal 1215 |

## Synthesis for the gate

11 of 12 findings verified REAL against disk; V11 resolves to the CLEAN side (floor pinned by oracle + D-104). The two CRITs (V1, V2) interlock: B1's commission booking cannot be implemented correctly until (1) the plan body is re-synced to D-127 asset-aware booking + a qty-depletion decision, and (2) the multi-fill vehicle (V2) is fixed — the in-flight-Order carry has no vehicle after fill 1 at HEAD, and the naive fix breaks the paper path (synthetic fills rely on the unconditional free). V4+V6 together mean Ship B currently has NO mechanical epoch rejection on ANY persistence surface (snapshots un-forced, event log un-versioned, stamps un-gated) — the H21/D-100 epoch posture is checklist-only. V5+V12 are the two silent-walker traps that arm exactly at the decimal flip. V8(a,b)/V9/V10 are enumeration gaps for the D-103/#5/#6 cohorts; V7 forces B4's fork to the egress arm.

— Verified by adversarial pass, 2026-06-09, against HEAD `0e48150` only (no auditor text trusted).
