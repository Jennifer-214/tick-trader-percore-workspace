# /trace-deps report — money-numeric-core foundation — 2026-05-31

**Plan:** `subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md`
**Engine HEAD:** 3f415a0 (feat/v5.15-live-readiness). **Mode:** Layer-2 subagent, READ-ONLY.
**Scope:** money-TYPE data-flow end-to-end; blast-radius-table COMPLETENESS (the silent-cast hazard is the headline risk). Decision (decimal + unified radix core, D-97/D-99..D-110) is SETTLED — NOT re-audited.

## Verdict: **YELLOW** (data-flow design sound; blast-radius table INCOMPLETE — 2 money boundaries missed, one capital-critical)

The end-to-end money flow the plan traces is real and the cited mechanisms are accurate. But the blast-radius enumeration — the plan's own headline risk per `feedback_enumerate_set_before_categorical_claim` — **misses the OrderResult fill-result double boundary**, which is the single most capital-critical money ingress in the engine. Not ship-blocking for the DECISION, but the plan body MUST be amended before coding so O-1 strong-typing surfaces every site (the plan's stated mechanism for catching exactly this).

---

## Focus-area verdicts

### (1) D-102 producer carry-through — VERIFIED ACCURATE (GREEN)
Chain confirmed end-to-end:
- `BinanceCrypto.hpp:744-745` parses `string→FPN<F>` EXACTLY (`FPN_FromString`), then derives `price_d = FPN_ToDouble(out->price)` at `:759-760` (LOSSY).
- `DataStream<F>` struct (`OrderGates.hpp:28-35`) carries BOTH `FPN<F> price` (exact) AND `double price_d`.
- **The exact FPN is DISCARDED at the seam:** `Run.hpp:1374` calls `fan_out(ds.price_d, ds.volume_d, …)` — passing ONLY the doubles. `EngineSharded_Async_FanOut` (`Async.hpp:135-140`) takes `double price_d`, then re-derives `t.price = FPN_FromDouble<F>(price_d)` at `:179-180` into the `Tick` ring (`Tick.hpp:31-43`).
- Net: `string → FPN(exact) → double(lossy) → FPN(re-derived from lossy double)`. Plan's claim "kill the double detour, carry the parsed decimal straight into the ring; lossy for binary TODAY too" is **fully correct**. Fix is structurally clean (`DataStream::price` already exists; `fan_out` signature + `ds.price_d`→`ds.price` is the change).

### (2) D-103 silent boundary casts — VERIFIED + UNDER-ENUMERATED (YELLOW)
All cited sites confirmed:
- **INGRESS decimal→binary:** `ControllerEventLoop.hpp:2194-2197` (`RollingStats_Push(price,volume)` — money into feature-domain rolling stats) ✓; `PortfolioController.hpp:943-945` (EMA mixes `current_price` money with `ema_price`) ✓.
- **EGRESS binary→decimal:** `StrategyParameters.hpp:347/428/511/634` (all write `out->bg_price_threshold = entry_price` from feature-derived sizing math) ✓; `PortfolioController.hpp:1037-1041` (`buy_conds.price` from `ema_price`±`gate_offset`) ✓, `:1048-1054` (`buy_conds.price = FPN_Mul(buy_conds.price, gate_scale)` — money×feature MUL) ✓.
- O-1 strong-typing (distinct template instantiations, no implicit cross-radix op) WILL turn these into compile-errors-until-cast — mechanism is sound. **BUT see findings: not all money boundaries are FPN-vs-FPN-today; the OrderResult `double` boundary will NOT be caught by O-1** (it's already double, so no compile error fires there — it silently `FromDouble`s into the new decimal type).

### (3) D-110 persistence/recovery — VERIFIED ACCURATE + TEST INFRA EXISTS (GREEN, one gap)
- All 10 raw-fwrite money citations EXACT: `ShardedSnapshotPersist.hpp` `allocated_balance:180 / core_realized:185 / core_fees:186 / core_open_notional:187 / core_gross_wins+losses:195-196 / last_entry_price:200 / core_peak_balance:205 / core_dd_pct:206 / pnl_feeder:232`; 16× `Position<F>:162`. Pattern is `fwrite(&ctx.<f>, sizeof(FPN<F>), 1, f)` — `sizeof`-dependent, confirming the version-bump requirement.
- **Version-reject mechanism CONFIRMED** (`:334`: `version != SHARDED_SNAPSHOT_VERSION` → refuse load; magic-reject `:328`; current `VERSION=8u` `:94`). Plan's "old snapshots version-rejected, not back-compat" acceptance is VALID **provided the ship bumps `SHARDED_SNAPSHOT_VERSION`** — add that as an explicit acceptance line (currently only implied).
- `Run.hpp:653` `live_starting_balance = FPN_FromDouble(usdt_recovered)` boot-reconcile CONFIRMED.
- **Round-trip TEST INFRA EXISTS:** `controller_test.cpp:5736-6047` has extensive `ShardedSnapshot_Save`/`_Load` round-trips. The plan's "warm-restart test GREEN + round-trip money EXACTLY" is satisfiable by extending these with exact-value assertions — but **no existing test asserts money-field EXACTNESS across save→load** (they test structural load success/partials). The decimal-exactness round-trip assertion is genuinely NEW work; plan's "Tests changed" covers it as golden-regen but should name the exact-value gap explicitly.

---

## Top findings

**F1 — CRITICAL (blast-radius GAP): OrderResult fill double-boundary missing from the table.** `ExchangeAdapter.hpp:43-47` `struct OrderResult { double avg_fill_price; double fill_qty; }` is the fill-result wire-format on BOTH paths. PAPER: `OrderManager.hpp:992-993` money→`FPN_ToDouble`→`cmd.result`→ re-derived `FromDouble` at `:1348-1349` (an engine-internal money→double→money round-trip). LIVE: exchange-reported fill arrives as `double` → `:1348-1349` `FromDouble` → `o->avg_fill_price/filled_qty` (the actual fill driving realized PnL). This is a D-102-sibling ("lossy intermediate in carry-through") on the FILL path — the plan enumerated only the PRODUCER double-roundtrip and missed this. **O-1 strong-typing will NOT catch it** (the field is already `double`, so `FromDouble` compiles silently — exactly the hazard O-1 is claimed to close). Capital-critical (LIVE source-exact fill is the D-106 premise). **Plan MUST add the OrderResult boundary** + decide: carry decimal through the result queue, or accept double + document the LIVE precision floor.

**F2 — HIGH (D-109 F-A CONFIRMED, not just suspected): LIVE fee is COMPUTED, not booked-from-reported.** `OrderManager.hpp:1142-1144` `handle_buy_fill`: `entry_fee = FPN_Mul(notional, entry_rate)` where `entry_rate = o->pre_resolved.fee_rate`; sell-side `:1188-1189` identical. There is NO path booking `executionReport`/`fills[].commission`. The plan's F-A ("grep inconclusive; suggests it computes") resolves to **CONFIRMED computes** → a D-106 venue-SSoT violation + paper↔live fee drift. Promote F-A from "verify" to "fix-in-ship: route LIVE fee to reported commission."

**F3 — MED (additional money ingress sites not in table):** `OrderManager.hpp:1410` `oms->balance = FromDouble(exchange_balance)` (LIVE balance reconcile), `:1421` recon drift; `Async.hpp:246-247` TP/SL price ingress, `:357` allocated_balance, `:383` mtm_price, `:865` order_qty; `PortfolioController.hpp:2231-2232` session_start_equity/peak_equity; `Run.hpp:1923-1925` price/volume. All are `FPN_FromDouble` on money values. Several are cfg/equity boundaries the plan's "~30 money cfg fields" row may subsume, but the OMS reconcile + Async TP/SL + mtm sites are NOT cfg and NOT enumerated.

**F4 — LOW (citation drift, self-acknowledged): Fingerprint.** `Backtest/Fingerprint.hpp:180` is the bare `SHA256_Update(&s, cfg_ptr, cfg_size)` site (plan blast-radius says `:181`; plan itself notes `.E.0.1` cited `:180`). Actual = **180**. Harmless; tighten the table.

**F5 — LOW (acceptance line missing): SHARDED_SNAPSHOT_VERSION bump.** D-110 acceptance implies old-snapshot rejection but does not state the version bump (8→9) that triggers it. Add explicit line.

## Ship-blocking gaps
- **F1** is the one to resolve before coding — it is precisely the silent-cast class the plan exists to close, and O-1 (the plan's enumeration mechanism) does not cover it. Amend the blast-radius table + decide the fill-result representation.
- **F2** is correctness-fix-in-ship (capital), not blocking the decision but must land in this ship per `feedback_address_med_low_findings_not_just_high_crit`.
- All other citations (D-102 chain, D-103 sites, D-110 persistence, accounting muls `OrderManager:1186-1194` / `ControllerEventLoop:1959-1967` / `Portfolio:389-392` / replay `:862-866` / ExitBuffer `:200-202` / sizing-div `PortfolioController:1215` / hot muls `ExecutionCore:543/549/570`) VERIFIED ACCURATE.
