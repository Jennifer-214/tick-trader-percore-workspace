---
type: audit-report
audit: /accounting-audit
scope: module:OMS / accounting
target_plan: plans/v5.15-live-readiness/subplans/2026-05-30-v5.15.5.F.4d.1.E-money-numeric-core-foundation.md
date: 2026-05-31
auditor: Layer-2 accounting-audit subagent (read-only)
engine_head: 3f415a0
verdict: YELLOW (plan is directionally correct on the decision; two factual-framing gaps + one under-specified gate must be tightened before coding)
---

# /accounting-audit findings — 2026-05-31 — money-numeric-core foundation (#11)

## Summary
- CRITICAL: 1 finding (F-A confirmed — LIVE computes fee, does not book reported; + the plan's "all round" framing is false)
- HIGH:     2 findings
- MEDIUM:   2 findings
- LOW:      1 finding

**Verdict: YELLOW.** The decision (decimal `<10,8>` money / binary `<2,64>` features, unified `FixedPoint<RADIX,FRAC>`) is correct and the H4 split is sound. But the plan's blast-radius table contains **two factual misstatements about current code** that would let the ship under-scope the rounding work and mis-frame the fee fix, and the D-100 correctness gate needs more teeth on the replay axis. Fix the framing + tighten the gate → GREEN.

---

## Findings

### [CRITICAL-1] F-A CONFIRMED — LIVE books a COMPUTED fee, never the exchange-reported commission; AND the plan's "all round" claim is false (the 42 sites currently TRUNCATE)
- **Severity:** CRITICAL
- **Category:** 2 (per-instance fee), 3 (cross-path consistency), 7 (backtest↔live parity)
- **Class:** candidate Class "internalized convention duplicating external authority" (D-106) + the D-105 rounding class
- **F-A resolution (explicit):** **LIVE COMPUTES. D-106 VIOLATION CONFIRMED.**
  - `OrderManager.hpp:1142-1144` (`handle_buy_fill`) and `:1187-1189` (`handle_sell_fill`) book `entry_fee = FPN_Mul(notional, o->pre_resolved.fee_rate)` / `exit_fee = FPN_Mul(exit_notional, exit_rate)` — i.e. `notional * fee_rate`, a client recompute.
  - The exchange-REPORTED commission **is parsed** (`BinanceUserData.hpp:361` `n`, `:363` `N`, stored `:378` `cmd_out->result.commission`) but the parser comment at `:359-360` states verbatim: *"Recorded for audit; not the authoritative fee number (Fee_Compute computes from cfg rates)."* The reported value is dropped on the floor for accounting.
  - Both WS-live fills and reconcile-replayed missed fills funnel through `OrderManager_HandleFill` → `handle_sell_fill` (dispatch `OrderManager.hpp:1285`; reconcile caller `Reconcile.hpp:264`). So there is no separate live path that books reported — **every live fill computes.** Result: paper↔live fee drift is structural, and live PnL/balance will not reconcile to the exchange to the penny (rounding-direction + BNB-discount + maker/taker-misclassification all diverge).
  - The plan's F-A (§ "Venue as SSoT", line 139 + acceptance line 221) already names this as a verify-and-fix item — **GOOD**, the plan anticipated it. This finding RATIFIES it: the fix is mandatory (not "if it was computing"), and the reported-commission plumbing (`result.commission` + `commission_asset`) already exists to consume — the ship must route it into the booking path, with `commission_asset` handling (F-B: BNB / base-asset denomination, `BinanceUserData.hpp:363`).
- **"All round" is FALSE (sub-finding, must correct the plan):** the blast-radius row (plan line 153) labels the 42 mul/div sites "(all round)" and frames D-105 as swapping the rounding *mode*. Ground truth: **grep finds ZERO `FPN_Round` / `FPN_Quantize` at any of the 42 sites**, and `FPN_Mul` (`FixedPointN.hpp:583`) is a truncating shift-reduce. Today the chain TRUNCATES at every mul. So D-105 is not "pick a mode" — it is **introduce rounding where there is none**, a deliberate value-changing behavior shift that MUST go through the D-100 golden regen. The plan under-frames both the scope and the correctness risk.
- **Recommended fix:** (1) route `result.commission` into `handle_*_fill` for LIVE (book reported, source-exact per D-106); keep compute for paper/backtest. (2) Correct the plan's blast-radius row from "(all round)" to "(currently TRUNCATE — rounding to be INTRODUCED)"; make the "every site routes through the one rounding mode" an explicit ADD, enumerated incl. replay. (3) `commission_asset` conversion path for non-quote fees.
- **DESIGN_SPEC reference:** `single-source-of-truth-discipline.md` (external-authority complement, D-106); `decision-time-data-binding-pattern.md` (Class 27 — fee already pre-resolved correctly, the fix is which NUMBER, not where it lives).

### [HIGH-1] Replay (`Portfolio_FromEventLog`) and production must apply the introduced rounding IDENTICALLY — currently both truncate, so the danger is asymmetric introduction
- **Severity:** HIGH
- **Category:** 7 (backtest↔live / replay parity)
- **Class:** D-105 (uniform rounding incl. replay)
- **Details:** Replay at `ControllerEventLoop.hpp:862-890` computes `notional=FPN_Mul(e.price,e.qty)` → `entry_fee=FPN_Mul(notional,rate)` → `gross=FPN_Mul(diff,qty)` → `net=FPN_Sub(gross,total_fee)`. Production twin at `:1959-1967` and `OrderManager.hpp:1186-1194` compute the SAME shape via `Portfolio_CloseSlot` (`Portfolio.hpp:389-390`: `gross=FPN_Mul(diff,qty)` — byte-identical formula to replay). Today they agree because **both truncate**. The risk the plan must guard: when rounding is INTRODUCED (CRITICAL-1), if it lands at production sites but a replay site is missed (or rounds at a different decimal place), warm-restart `Portfolio_FromEventLog` reconstructs a balance that diverges from the live-accumulated one → silent paper↔live and recovery↔live divergence. The plan's D-105 "(incl. replay)" parenthetical is correct intent but the acceptance criteria do not include a replay-equals-production differential test.
- **Recommended fix:** add to the D-100 gate an explicit **"replay a recorded fill stream → assert byte-identical balance/realized_pnl/fees vs the live-accumulated values"** characterization test (golden-master, sister to D-100). Route every replay mul through the same `FPN_Round`-bearing helper as production (single helper, not copy-pasted rounding).
- **DESIGN_SPEC reference:** `golden-master-over-reimplemented-oracle.md`; `two-foundations-determinism-vs-correctness.md`.

### [HIGH-2] D-100 one-time correctness gate under-specifies the to-the-penny reconciliation surface (only "fees/PnL", omits balance-overwrite + recovery round-trip)
- **Severity:** HIGH
- **Category:** 6 (atomicity / SSoT of balance), 7 (parity)
- **Details:** The D-100 gate (plan lines 119-124) specifies decimal-exactness (`0.1+0.2==0.3`), fees/PnL vs hand-computed + Python `decimal`, and round-trip parse→emit→parse. Three money-path surfaces escape that net: (a) `OrderManager.hpp:1410` `oms->balance = FPN_FromDouble<F>(exchange_balance)` — the reconcile path OVERWRITES the whole balance from an exchange double, a money-path double→FPN boundary the gate doesn't cover; (b) `Run.hpp:653` `usdt_recovered` double→FPN boot-reconcile (plan names it in blast-radius but not in the gate); (c) the `ShardedSnapshotPersist.hpp` warm-restart round-trip (plan acceptance line 220 requires "round-trip EXACTLY" but the D-100 gate § doesn't list a persistence differential). For a capital system these are exactly where a decimal-vs-double penny gap hides.
- **Recommended fix:** expand the D-100 gate enumeration to include: balance-overwrite boundary (reconcile), boot `usdt_recovered` boundary, and snapshot save→recover money round-trip — each with an exact (not epsilon) assertion. State explicitly that these double→FPN ingress points are venue/exchange boundaries (D-106) and get a GUARD, not a silent cast.
- **DESIGN_SPEC reference:** `two-foundations-determinism-vs-correctness.md` (D-100 refinement); the plan's own D-110 persistence row.

### [MED-1] `last_realized_return[]` is `double` on the OMS struct — H4-borderline; confirm it stays a SIGNAL, never an accounting input
- **Severity:** MEDIUM
- **Category:** 4 (H4 enforcement)
- **Details:** `OrderManager.hpp:336` `double last_realized_return[MAX_PORTFOLIO_POSITIONS]`, written at `:1181-1182` from `FPN_ToDouble`-derived `(exit-entry)/entry`. Consumed at `ControllerEventLoop.hpp:1554/1602` as a return ratio for cooldown/decision logic — NOT booked into balance/realized_pnl (those are `FPN<F>`, H4-clean: `OrderManager.hpp:305-306`). So this is a display/signal double, technically H4-permissible. BUT it is computed inside the accounting handler via a double divide, and the plan's H4 acceptance ("ZERO float/double on the decimal accounting path") should make a deliberate ruling that this field is signal-domain (stays binary/double) vs accounting-domain. Don't let the audit's "H4 clean" be implicit.
- **Recommended fix:** plan adds one line classifying `last_realized_return` (and `last_vol_scale` `PortfolioController.hpp:183`) as signal-domain display values, explicitly H4-exempt, so the decimal migration knowingly leaves them. If any consumer ever multiplies them back into a money value, they become accounting and must move to FPN.
- **DESIGN_SPEC reference:** DESIGN_PHILOSOPHY § 3 H4 (display-only double permitted).

### [MED-2] Kill-switch boundary (`ExitBuffer_PendingProceeds`) recomputes fee from a `fee_rate` PARAM, not the booked exit_fee — a second fee model on the money path
- **Severity:** MEDIUM
- **Category:** 3 (fee model consistency across paths)
- **Details:** `Portfolio.hpp:191-204` `ExitBuffer_PendingProceeds` computes `fee=FPN_Mul(gross,fee_rate)` + applies `slippage_pct` to estimate pending net proceeds for the kill-switch boundary. This is a THIRD fee computation (alongside `handle_sell_fill` and `Portfolio_FromEventLog`), parameterized on a passed `fee_rate`/`slippage_pct`. Under the decimal migration + rounding introduction (CRITICAL-1), this site must round identically and — post F-A fix — the question arises whether the pending-proceeds estimate should also reflect reported-vs-computed (it's an estimate, so computed is defensible, but the plan should rule on it). Not booked to balance (it's a gate estimate), hence MED not HIGH.
- **Recommended fix:** include this site in the D-105 "every money mul routes through the one rounding helper" enumeration (the plan's blast-radius row already lists `Portfolio.hpp:200-202` — GOOD); add a one-line note that the kill-switch estimate intentionally uses computed fee (estimate, not a booked value).
- **DESIGN_SPEC reference:** `decision-time-data-binding-pattern.md`.

### [LOW-1] Class 27 fee_rate path is CLEAN — note for completeness
- **Severity:** LOW (positive finding)
- **Category:** 1 (Class 27 scalar cfg-mirror)
- **Details:** Verified the prior Class 27 closure holds: OMS no longer caches a scalar `fee_rate` (`OrderManager.hpp:307-310` documents the deletion); fee is pre-resolved onto `Order::pre_resolved.fee_rate` at submit (`Order.hpp:141/358`) and read decision-time at `handle_*_fill`. Per-core exit-fee reads go through `effective_cores[slot].fee_rate_taker` (`ControllerEventLoop.hpp:862/1962`) — per-instance, not unindexed-global. No Class 26 sub-shape B at these sites. The decimal migration should preserve this binding shape (swap the type, keep the pre-resolve). No action; flagged so the ship doesn't accidentally reintroduce a scalar cache during the type swap.
- **DESIGN_SPEC reference:** `decision-time-data-binding-pattern.md` § Class 27.

---

## Blocking gaps (must resolve before coding)
1. **CRITICAL-1 / F-A:** plan must commit to routing `result.commission` (reported) into LIVE booking (not "if it was computing") + correct the false "(all round)" framing → rounding is INTRODUCED, not mode-swapped.
2. **HIGH-1:** add a replay-equals-production balance differential to the D-100 gate; single shared rounding helper across production + replay + kill-switch-estimate.
3. **HIGH-2:** expand the D-100 gate to cover the balance-overwrite (`OrderManager.hpp:1410`) + boot (`Run.hpp:653`) + snapshot-recovery money boundaries with exact assertions.

## What the plan got RIGHT
- The decimal-for-money / binary-for-features split + H4 ruling is correct; accounting accumulators (balance/realized_pnl/total_fees/core_realized) are already `FPN<F>`.
- F-A was anticipated (§ Venue-as-SSoT + acceptance) — this audit ratifies it as mandatory.
- D-110 persistence surface + the ~12 D-103 boundary-cast enumeration + strong-typing (O-1) are sound and capital-appropriate.
- The golden-EPOCH + one-time-correctness-gate (D-100) is the right shape; it just needs the three boundary surfaces above added to its enumeration.
