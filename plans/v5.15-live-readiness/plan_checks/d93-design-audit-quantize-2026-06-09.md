---
type: design-audit
audit: D-93 new-function design audit — cluster #6 (FPN_Quantize + MIN_NOTIONAL + exact qty wire-string + SymbolFilters retype/supersede-set)
plan: subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md (v0.4)
sidecar: subplans/2026-05-31-v5.15.5.F.4d.1.E-11-new-function-designs.md (#6 section)
oracle: plan_checks/2026-06-01-11-phase1-divmul-proof/decimal_oracle.py
head: 0e48150 (v5.15.5.F.4d.1.E.0.8)
date: 2026-06-09
verdict: YELLOW — direction + cohort sound; 7/7 questions return DESIGN-GAP; 1 internal contradiction (plan :196 signature vs :133/oracle); zero architecture re-opens
---

# D-93 design audit — #6 quantize cluster (2026-06-09)

Scope: designs as written (no code exists). All referenced code verified at HEAD 0e48150.

## Q1 — Floor-to-step with a RUNTIME step: **DESIGN-GAP** (mechanism unpinned) **+ one DESIGN-WRONG element** (internal contradiction)

**What the design says.** Sidecar :67: "round-to-step (general divide by the *runtime* per-symbol step — submit cadence, not hot path, so no reciprocal-magic needed)." Plan :133: "FLOOR value to venue `stepSize` (runtime per-symbol step; … direction = floor-to-step, oracle-pinned)." Oracle :72-74 pins the general contract `(v // step) * step`.

**Defect 1 (contradiction → DESIGN-WRONG row).** Plan :196 says "add `FPN_Quantize(value, decimals)` at submit" — a *decimals*-shaped signature that silently assumes 10^-k steps. It contradicts plan :133 + the oracle's *step*-shaped contract. Stale row; fix to `(value, step)`.

**Defect 2 (mechanism vs acceptance gate).** A literal "general divide" on `__int128` compiles to `__udivti3` — which the plan's own acceptance (:354 "no-`__udivti3` symbol check"; also #7 row :134) bans. The sidecar's "no reciprocal-magic needed" wording, as written, licenses an implementation that fails the ship gate. The waiver conflated "no *proven magic constant* needed" (true — runtime step has no constexpr magic) with "any divide is fine" (false under the symbol check + H11/H20 posture).

**Step shapes (verified).** HEAD parses stepSize from exchangeInfo strings like "0.00100000" (`BinanceOrderAPI.hpp:716`); `binance_step_decimals` :184-188 derives *decimal places* (it would handle 0.5 → 1dp — today's double path is shape-agnostic). Binance spot steps are 10^-k in practice, but the wire format does not guarantee it, and the `.E.1` multi-exchange trajectory (futures-style 0.25/0.5 ticks) breaks the assumption. The oracle contract is already general; its test domain is NOT (:206 draws steps only from `10^k` — non-power-of-ten rows untested; also the `or 1` on :206 is dead).

**Required decision (pick one, record):**
- **(a) RECOMMENDED:** quantize divide = **#7's constant-trip divider core**, dividend zero-extended (128÷128 sub-case, NO 10^8 widen; `r = v − q·step; result = v − r`). One mechanism, oracle-general, venue-general, satisfies the no-`__udivti3` gate. ⇒ **#6 DEPENDS on #7** — the execution sequence (P1 #7 → P4 #6, plan :314/:317) already orders this correctly but the dependency is UNSTATED; write it into both the #6 and #7 rows so a resequencing can't silently break it.
- (b) Digit-truncate via a 9-entry proven-magic table (`divmul_pow10` generalized to 10^m, m∈[0,8]) + a boot-guard refusing non-10^-k steps (D-106 fail-loud). More machinery, venue-restricted; only worth it if #7 slips.

Plus: add non-power-of-ten step rows (e.g. scaled 0.5 = 50000000) + an idempotence row (`Q(Q(v))==Q(v)`) to the oracle quantize test.

## Q2 — SymbolFilters retype (S-10): **DESIGN-GAP** (parse mechanism + `qty_decimals` derivation unstated)

**Verified at HEAD.** `SymbolFilters` :75-82 (`lot_step_size` :76, `min_notional` :79 — both double; `qty_decimals` :80 derived). Load path :712-723: `binance_json_extract_double` for minQty/maxQty/stepSize/minNotional; `strstr(body,"NOTIONAL")` matches NOTIONAL *or* MIN_NOTIONAL (comment :720).

**Gaps:**
1. "RETYPE … exact decimal at filters load" never states the mechanism = **#5 exact `FromString` on the raw string span**. The #5 sidecar site list (:63 — BinanceCrypto:744 / BinanceDepth / BacktestSharded / C4 fill adapter; B6 adds Reconcile + REST sync-fill) **does not include `BinanceOrderAPI_LoadFilters`**. Add it to the #5 cohort explicitly. Note: `binance_json_extract` returns a `(ptr,len)` span; existing `FPN_FromString` (FixedPointN.hpp:394) is NUL-terminated `char*` — the decimal FromString needs a span/`_n` variant (or a bounded copy) for this site. Unstated.
2. **`qty_decimals` superseded by WHAT — undesigned.** `binance_step_decimals` :184 is supersede-DELETED, but `qty_decimals` remains **load-bearing for emit width** (see Q4). Pin the replacement derivation: `decimals = FRAC − trailing_zero_count_base10(step.v)` computed once at load from the exact decimal step (0.001 → v=10^5 → 8−5=3; 0.5 → v=5·10^7 → 1). Boot cadence; trivial; must be written down.
3. **Unenumerated money ingress (cohort add):** `GetBalances`/`GetBalance` "free" parse (:755) is the **orphan-sell qty source** (`ShardedLiveSafety.hpp:58-59` → :77) — a money double-parse absent from the #5/B6 lists (plan :194 covers only `Run.hpp:653` usdt_recovered, the USDT side).
4. **D-106 completeness notes:** `NOTIONAL.applyMinToMarket` not parsed (unconditional enforcement = conservative-safe — we may reject what the venue would accept; acceptable, document); `MARKET_LOT_SIZE` not parsed (venue-reject direction for MARKET orders where constrained — usually unconstrained; document); `lot_max_qty` parsed (:715) but consumed NOWHERE at HEAD — fold max-qty clamp into the #6 submit check or tombstone-document.

## Q3 — MIN_NOTIONAL enforcement point: **DESIGN-GAP** (point + failure path + entry/exit asymmetry unpinned)

Design says only "at order submit … reject/flag" (sidecar :68; B-α :219). Never resolved to a code point among: sizing (`PortfolioController.hpp:1186` slow path), `OrderManager_Submit` (OMS/drainer), wire worker (`BinanceAdapter.hpp:192-194`). Verified: the production sharded path reads `min_notional` NOWHERE today (consumers = legacy main.cpp only: :754/:875/:940/:961/:1062) — B-α's "parsed-not-enforced" claim is accurate *for sharded*.

**Required design:**
- **Point = OMS submit** (the shared live+paper vehicle — also the Q7 parity hinge), with the wire layer keeping its check as a backstop.
- **Failure path per the observability rule:** ENTRY below min-notional → skip + named counter (FailureModeRegistry/SHALT-style reason), signal consumed, no position, no spin. "reject/flag" is not a design.
- **Entry/exit asymmetry:** legacy main.cpp enforces `min_notional * 2.0` on ENTRIES (:875/:1062) — a deliberate buffer so the later EXIT also clears the filter after adverse moves; without it you mint positions that cannot be exited (venue rejects the close → dust stuck). Decide: adopt the buffer (recommend, cfg-able multiplier) or record why not. EXIT below min-notional → dust disposition (Q5), never a retry loop.

## Q4 — exact qty wire-string: **DESIGN-GAP** (trailing-zero/width policy unpinned); supersede sequencing OK-by-construction but unstated

- **Trailing-zero policy:** Binance accepts trailing zeros within asset precision; `-1111` ("precision over the maximum") fires above it. Safest + behavior-preserving policy: **emit exactly `qty_decimals` digits** (today's `%.*f` width at :514/:559). ⇒ the FromString-inverse takes a **width param** — mirror the existing binary `FPN_ToString(value, buf, size, decimal_places)` shape (FixedPointN.hpp:337/:1550). This is what keeps `qty_decimals` load-bearing (Q2 gap 2). Pin it; "exact digit-emit" alone underdetermines the string.
- **Shape:** pure integer div/mod-by-POW10 digit emit from the scaled value (constant-trip per H20; submit cadence). Money-emit-parity site — add a parse→emit→parse round-trip acceptance row (plan :362 already lists round-trip tests; name the qty-emit explicitly).
- **Supersede-DELETE sequencing (B14-lite):** the S-10 retype red-builds every double consumer (compile net catches all callers — main.cpp legacy included), so callers-migrate-first/helpers-delete-last is forced by the compiler. Fine — but the P4 row should SAY the order (introduce #6 quantize+emit → migrate wire fns + safety cohort + legacy → delete :178/:184/:514/:559 last) so the net is by design, not by accident.

## Q5 — flatten/orphan cohort: **DESIGN-GAP** (dust termination undesigned — with an operational sting at the Ship-B deploy itself)

**Verified sites:**
- `ShardedLiveSafety.hpp:204` FORCE-CLOSE: per-slot `FPN_ToDouble` → `binance_round_qty` → `if (qty_d < lot_min_qty) { skip; continue; }` (:205-208). **The skipped slot's bitmap bit is never cleared**, so the drain-wait (:233) on `active_bitmap != 0` burns the FULL 30s timeout and fires the "manual intervention required" ALERT (:243-252). It TERMINATES (bounded), it does not spin — but every dust slot costs the full timeout + a false alert. **B-ζ makes this acute:** the mandatory flatten-before-deploying-Ship-B leans on exactly this path; a dust slot turns the epoch flatten into a spurious TIMEOUT at the deploy moment.
- `:77` orphan close: one-shot; below-min → "leaving as dust" log (:115) and proceeds. Terminates cleanly; needs only the decimal retype + the same named dust disposition.
- main.cpp legacy (:438/:751/:938/…): deprecated single-core LIVE; the retype red-builds them — sweep mechanically, invest no design (flag for `.E.1` deletion).

**Required design (not currently anywhere in plan/sidecar/S-10):** quantize-to-zero-or-below-min in FORCE-CLOSE → **clear the bit + book the residual as dust** (flagged counter + reconcile pickup; observability rule), and exclude the slot from the drain-wait mask so the wait covers only actually-submitted closes. S-10's "all route through #6" gives path-sameness (good; floor idempotence makes the pre-round + wire-round double-quantize harmless — add the idempotence test row) but path-sameness ≠ failure-mode design.

## Q6 — tickSize: **DESIGN-GAP** (the v0.4 "or" is an undecided decision). Recommendation: **load now + non-MARKET boot-guard; record as a D-number**

Verified: no PRICE_FILTER parse anywhere at HEAD; MARKET-only engine makes price quantization moot today. Recommend: parse `PRICE_FILTER.tickSize` into `SymbolFilters` **in the same S-10 retype pass** (#5-exact, one more row — single traversal of a verified surface per design-once/D-144 re-traversal cost), consumed by nothing; plus a guard refusing any non-MARKET order type with a named reason until price-quantize is wired (the LIMIT future = `.E.3`). Avoids re-opening the BinanceOrderAPI parse surface later and feeds `.E.1` ExchangeRegistry populate-from. Record the choice + rationale in the decision log (D-17x); the plan's "or" must not survive into code.

## Q7 — paper/backtest quantization parity (M5): **DESIGN-GAP** (parity hole persists BY DESIGN as written)

**Verified at HEAD:** quantization exists ONLY in the live wire layer (:511/:556). Paper fills the requested qty verbatim (`OrderManager.hpp` paper path; :995-996 ToDouble→FromDouble round-trip only). Backtest: ZERO filter references (grep over Backtest/ — none). And `SymbolFilters` loads only when live REST initializes ⇒ #6 "off the already-loaded SymbolFilters" quantizes NOWHERE in paper/backtest. Live floors `sized_qty` to step + rejects sub-notional; paper/backtest fill raw `sized_qty` — a paper↔live qty/PnL drift the plan's own twin bar (S-12 boot-allocation LIVE+backtest twins) would not tolerate elsewhere.

**Required decision:** (a) RECOMMENDED — quantize + MIN_NOTIONAL at OMS submit for ALL modes; filters sourced live = REST exchangeInfo, paper/backtest = **cfg-pinned venue snapshot** (D-106-style recorded values for the traded symbol; refuse-if-absent in paper-live-intent modes, identity-step default for pure research backtest if operator prefers); or (b) explicitly ACCEPT + document the asymmetry (weaker; contradicts the M5 posture and S-12's own bar). The plan is currently silent — silence is the defect.

## Punch list — minimal design additions before code

1. **[Q1]** Pin quantize mechanism = #7 constant-trip divider core (no widen) **or** magic-table+boot-guard; write the **#6→#7 dependency** into both fn rows; fix plan :196 signature → `(value, step)`; note the fn name rides Step-0 (money family ⇒ `Money_*`/`FPD_*`, not `FPN_*`).
2. **[Q2]** Add `LoadFilters` (+ `GetBalances` ingress) to the #5 exact-parse cohort; specify the span-variant FromString; pin the `qty_decimals` derivation from the exact decimal step.
3. **[Q3]** Pin MIN_NOTIONAL at OMS submit + named skip-counter + entry-buffer decision (legacy ×2 precedent) + exit-dust disposition; fold `lot_min_qty`/`lot_max_qty` into the same submit check or document.
4. **[Q4]** Pin emit width policy (= `qty_decimals` digits, `FPN_ToString`-shaped signature); name the parse→emit→parse row; state the B14-lite deletion order in P4.
5. **[Q5]** Design FORCE-CLOSE dust termination (clear-bit + book-dust + exclude from wait mask) — B-ζ epoch-flatten depends on it.
6. **[Q6]** Decide tickSize = load-now + non-MARKET guard; record D-number.
7. **[Q7]** Decide paper/backtest filter source (cfg-pinned snapshot) so all modes share the ONE quantize point; add oracle/test rows: non-10^-k step, idempotence, dust-to-zero, sub-notional entry skip.

**Synthesis:** direction (floor-to-step), cohort enumeration (S-10), and venue-SSoT posture are sound — no architecture re-opens. But "FRAMED — mechanical" overstates readiness: the cluster has one internal contradiction (plan :196), one acceptance-gate conflict (general-divide wording vs no-`__udivti3`), an unstated cross-fn dependency (#6→#7), and four undesigned failure paths (min-notional reject, dust flatten, paper parity, tickSize "or"). All are cheap to fix at design time; none should be discovered at code time on a capital surface (D-77).
