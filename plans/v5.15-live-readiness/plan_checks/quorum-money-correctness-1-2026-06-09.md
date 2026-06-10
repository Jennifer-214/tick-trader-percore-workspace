---
type: audit-report
doc_kind: quorum money-correctness audit (auditor 1 of 3; k=2-of-3 synthesis)
target: subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md (v0.3) + #1-#6 sidecar + PROOF.md
scope: Ship-B remaining work (decimal money, #4-#6, B1-B6, D-103 casts, stamp/persist decimal, D-100 gate)
engine_head: 0e48150 (v5.15.5.F.4d.1.E.0.8)
created: 2026-06-09
verdict: 2 wrong-money design errors (1 CRIT, 1 HIGH) + 1 HIGH enforcement hole + 2 MED + 2 LOW; remaining angles CLEAN
---

# Quorum money-correctness audit 1/3 — Ship-B money-numeric-core foundation

Single question: where would the planned design, AS WRITTEN, produce wrong money values or wrong
money behavior? All citations verified against actual code at HEAD 0e48150.

---

## Finding 1 — CRIT — B1 books exchange-reported commission with no `commission_asset` unit handling → LIVE fees booked in the wrong denomination

**Plan text:** B1 / D-109 / acceptance: "LIVE books the `executionReport`/`fills[].commission` value
(source-exact, D-106), NOT a client recompute … carry `result.commission` onto the in-flight Order
… + book it for LIVE."

**Code facts at HEAD:**
- `DataStream/BinanceUserData.hpp:361-364` parses `"n"` (amount) AND `"N"` (asset) — the venue
  denominates commission in the RECEIVED asset: **BASE asset on BUY** (e.g. BTC), quote on SELL,
  **BNB when `pay_fees_in_bnb`** (the engine has exactly this cfg: `EngineCommon.hpp:154-166`
  `EngineCommon_ApplyBnbDiscount`).
- Every accounting sink the booked fee reaches is QUOTE-denominated: `OrderManager.hpp:1211-1216`
  (`net = gross − total_fee; balance += net`), `core_fees`, `realized_pnl`. The existing code
  comment at `BinanceUserData.hpp:360-361` ("Recorded for audit; not the authoritative fee number")
  is the guard B1 removes.

**Why wrong:** the plan's own R-1 text states the denomination fact ("fee deducted in the RECEIVED
asset — base on BUY / quote on SELL / BNB if enabled") yet B1 specifies booking the raw reported
number with no conversion and no same-asset guard. "Source-exact" forbids transformation, and for
BNB there is no conversion-rate input loaded anywhere in the engine. As written:
- **every LIVE BUY entry fee** is a base-asset amount booked as quote (e.g. 0.00000750 BTC booked
  as $0.0000075 — fee understated ~70,000× at $70k, overstating net PnL on every round trip);
- with BNB mode on, BOTH legs are BNB amounts booked as quote (~600× off).

F-B dispositions denomination as "modeling approximation, low priority" — that was written for the
COMPUTED-fee path and was never re-opened when B1 made the reported value load-bearing. The B1
design needs: book-reported ONLY when `commission_asset == quote asset`, else an explicit, designed
conversion (at fill price for base-asset commission) or flag-and-fallback-to-computed; plus the
`comm_asset` string must be carried onto the Order alongside the amount (it is parsed but the plan
never mentions it).

---

## Finding 2 — HIGH — B1 makes replay==production structurally impossible: `OrderEvent` carries no fee/commission, and all replay paths RECOMPUTE fees from cfg rate

**Plan text:** C2 acceptance — "a replay==production rounding differential added to the D-100 gate";
B2 — replay sites (`ControllerEventLoop.hpp:863/877`, `OrderEventLog.hpp:656-657/675-676`) must
"route through #4's helper".

**Code facts at HEAD:**
- `OrderEventLog.hpp:79-93` `OrderEvent` fields = price/qty/tp/sl/timestamps — **no fee field**.
- `OrderEventLog.hpp:~656/675` (`tt::Portfolio_FromEventLog`) recomputes
  `entry_fee/exit_fee = FPN_Mul(notional, fee_rate)` from a passed cfg rate.
- `ControllerEventLoop.hpp:~862/877` (`EventLoopState_ReconstructPerCoreFromEventLog`, called at
  boot recovery `:953`) recomputes from `effective_cores[core].fee_rate_taker` — and is documented
  nullptr-tolerant ("nullptr → FPN_Zero fees in reconstructed accounting").
- Production (Ship-B design) books the exchange-REPORTED commission for LIVE per B1.

**Why wrong:** a venue-reported commission is not derivable from `rate × notional` — no amount of
rounding-helper routing (#4, D-105) can make the replay-rebuilt `core_realized` / `core_fees` /
`balance` equal what production booked for LIVE fills. The plan addresses ROUNDING uniformity but
never extends the event-log schema (or the snapshot-vs-replay contract) to carry the booked fee.
As written, warm-restart/event-log recovery after LIVE trading reconstructs different money than
was booked (wrong recovered balances), and the C2 acceptance gate either fails un-passably or only
ever runs in paper mode and silently blesses the LIVE divergence. Fix shape: `OrderEvent` gains a
booked-fee field (epoch bump is free per D-100 — `entry_size` header at `OrderEventLog.hpp:425+`
already version-gates), replay replays the booked fee. Sibling instance: legacy
`ExitBuffer_PendingProceeds` (`Portfolio.hpp:196-207`) claims to "match what DrainExits will
credit" while recomputing from a single global rate — same recompute-vs-booked class (legacy-scoped,
lower priority).

---

## Finding 3 — HIGH — Ship-B snapshot-version bump has NO effective enforcement: the binary→decimal flip changes semantics with sizeof UNCHANGED, so every designed guard passes on stale snapshots

**Plan text:** acceptance — "old snapshots version-rejected"; R3 discipline — "a layout-coupled-
version test asserts each strictly increased **in the same ship `sizeof(FPN)` changed**".

**Code facts at HEAD:** `ShardedSnapshotPersist.hpp:94` v9, `Portfolio.hpp:45` v6,
`CONTROLLER_SNAPSHOT_VERSION` 13 — all three bumps were CONSUMED at Ship A (the 24B→16B flip).
Load rejects only on `version != current` (`ShardedSnapshotPersist.hpp:334-336`).

**Why wrong:** at Ship B, money fields flip `FixedPoint<2,64>` → `FixedPoint<10,8>` — **both 16
bytes**. sizeof/offset ladders (`Portfolio.hpp:80-142`), H12 asserts, and the R3 layout-coupled-
version test are ALL keyed to layout change and will all pass without any code change. If the bump
to 14/10/7 is forgotten, a v9/v13/v6 snapshot whose money bytes are 2⁶⁴-scaled binary loads cleanly
into a 10⁸-scaled decimal engine: every balance/fee/position value misread by a ~1.8×10¹¹ factor,
silently. B-ζ ("flatten positions before deploying") does not cover persisted balances
(`allocated_balance`/`core_realized`/`core_fees` load regardless of flat positions). The
requirement exists in the acceptance row but the only enforcement mechanism the plan designs
provably cannot fire at Ship B. Fix shape: key the version-bump test to the money-TYPE change
(e.g. static_assert tying snapshot version to a radix/type tag, or a golden-snapshot decode test),
not to sizeof.

---

## Finding 4 — MED — #6 quantize-to-step direction unspecified; D-105 "uniform rounding" pressure would CHANGE today's floor semantics → oversell/overspend

**Code facts:** today's submit rounding is truncate-toward-zero
(`BinanceOrderAPI.hpp:178-181` `binance_round_qty`: `(int64_t)(qty/step) * step`), which #6
explicitly supersedes. Sidecar #6 says only "round-to-step"; D-105/#4 mandate ONE canonical mode
(half-even) "applied uniformly".

**Why wrong:** half-even-to-step on a SELL qty can round UP past the held quantity (venue -2010 /
stuck position at flatten); on BUY it can exceed the allocated risk notional. Quantization to a
venue step is a CONSTRAINT-satisfaction rounding (floor-to-step is the only side-safe direction
for qty), not an accounting rounding — the plan never states this carve-out from D-105, and the
D-100 oracle "quantize-to-step: 50k cases" was validated against an unstated convention. Specify
floor-to-step (preserving today's semantics) explicitly as a D-105 exception.

---

## Finding 5 — MED — money overflow semantics undefined: "flag-loud" asserted (D-147 Ship-B posture) but no mechanism designed; default inheritance = binary's silent saturate

**Code facts:** the shared #2 multiply hoists the binary core whose overflow behavior is branchless
saturate-to-max (`FPN_Mul` overflow word check `FixedPointN.hpp:611+`, 16B specializations :1499+;
R2 suite-checked saturate-not-wrap). All 42 accounting call sites use value-returning signatures
(`FPN_Mul(a,b)`) with no error channel.

**Why wrong:** PROOF.md routes divmul's out-of-range guard "to the existing overflow/flag path
(#5/#6, D-106 range guard)" — but #5's `(value, ok)` channel is parse-time only; no flag path
exists for mul/div at fill/PnL sites and the plan designs none (no SHALT code, no kill-switch hook,
no sticky overflow flag). The natural implementation inherits saturate → an overflowed notional
silently clamps and trades/accounting proceed on a wrong value — exactly the "saturate = max
signal" rationale that is CORRECT for features and WRONG for money. Trigger range is remote
(operand ≥ ~$92B), so MED not HIGH — but the posture/mechanism gap should be closed in the plan
body (e.g. per-core sticky overflow flag checked by the drainer → halt), not discovered at code time.

## Finding 6 — LOW — #5 per-site `ok=false` semantics unspecified on the LIVE fill path

Design intent ("surfaced, never silent-zero") is right and oracle-verified, but the plan never says
what the OMS DOES with a fill whose price/qty/commission string fails exact-parse. The venue
executed it: dropping it desynchronizes engine position/balance from the exchange (wrong money
behavior); zeroing it is silent-zero. Needs a named disposition (halt/reconcile path), per site.

## Finding 7 — LOW — #6 design text contradicts HEAD: quantize "to venue tickSize/stepSize … off the already-loaded SymbolFilters", but tickSize is not loaded anywhere

`BinanceOrderAPI.hpp:76-83` `SymbolFilters` is qty-only (the plan's own blast-radius row says "NO
tickSize/PRICE_FILTER anywhere"). Engine is MARKET-only (`OrderManager.hpp:1132`) so no price goes
on the wire today — no wrong money at Ship B — but #6 promises price quantization it cannot deliver
without an unstated PRICE_FILTER load; clean up before it bites at LIMIT-order time.

---

## CLEAN angles (verified)

- **Rounding math #3/#4:** divmul magic proven (G–M bound + exhaustive predicate validation +
  208k differential); N=127 guard correct-by-construction vs venue P_max ≈ 2¹¹⁰; half-even on
  magnitude with sign reapplied ≡ value-domain banker's (sign-symmetric; ties oracle-verified) —
  negative-PnL rounding direction CLEAN.
- **Double-width intermediates:** 128×128→256 product + reduce, 2-bit margin at N=127 — CLEAN.
- **Parse exactness:** single-pass digit-accumulate exact for ≤8dp; reject set (malformed/>8dp/
  scientific) oracle-verified — CLEAN at design level (modulo Finding 6 per-site semantics).
- **Persist/recovery round-trip:** raw fwrite/fread of a 16B scaled int is byte-exact; version
  reject mechanism present — CLEAN mechanically (modulo Finding 3 bump enforcement).
- **Boundary casts (D-103):** ingress/egress enumerated; money never flows BACK from binary into
  ACCOUNTING — egress (StrategyParameters thresholds, GateParameters compares) is decision-domain;
  all booked amounts originate from venue fills/parses. B4 price-domain decision is flagged open
  by the plan itself for the Ship-B gate — acceptable.
- **Stamp/wire decimal:** B3 disjoint-trait red-build net verified at HEAD
  (`FixedPointN.hpp:97-107`; `CfgFieldDispatch` family asserts exclude decimal) — decimal cannot
  silently take the lossy `%.17g` path — CLEAN.
- **Paper/backtest vs LIVE fee drift:** bounded + intentional per D-109/F-B **once Finding 1's
  unit handling exists**; without it the "drift" is unbounded in BNB mode.
- **`Run.hpp:653` `usdt_recovered` + `Reconcile.hpp:546` double-parses:** named in plan (B6 cohort
  + acceptance) — covered.
- **BNB factor constant:** `FromDouble(0.75)` → exact decimal constant (B2) — 0.75 exact in both
  radices — CLEAN.

**Bottom line:** the decimal core itself (type/multiply/reduce/rounding/parse) is sound and
unusually well-proven. The wrong-money risk concentrates in the FEE-BOOKING REDESIGN (B1) — unit
of account (Finding 1) and replay/data-source symmetry (Finding 2) — plus the unenforceable
version-bump at a same-size semantic flip (Finding 3).
