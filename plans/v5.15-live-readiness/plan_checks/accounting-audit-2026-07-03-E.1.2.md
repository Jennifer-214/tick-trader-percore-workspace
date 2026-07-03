# /accounting-audit findings — 2026-07-03 — E.1.2 (F-096 Money-ize leg + derived-vs-persisted money fields)

**Target:** `plans/v5.15-live-readiness/subplans/2026-06-15-v5.15.5.F.4d.1.E.1.2-nodestate-soa-layout.md` (Phase C derived-field marking + Phase E F-096 Money-ize).
**Engine HEAD:** `b10e778` (byte-identical to E.1.1 `0ee227a`). **Agent:** I-class investigative. **Invariant:** H4. **Anti-patterns:** Class 27 / 54 / 55; SSoT (`feedback_single_source_the_computation_not_the_mode`).
**Skill:** `/accounting-audit` — 10-category checklist walked (cats 4/5 H4+lossy-ToDouble, 6 atomicity, 7 backtest-parity primary).
**Tool baseline:** `check_money_gross_single_source.py` = **PASS** (D-190; node_dd_pct recompute via `Money_FillGross` is compliant).

## Summary
- CRITICAL: 0
- HIGH:     2  (exit-path double left by the entry-only fix; partner_pending_pnl fix incomplete without the bitmap)
- MEDIUM:   3  (conservation assert mis-fits drainer structure; persist-vs-defer TD-227; leg-split SSoT duplication)
- LOW:      2  (no CI guard on the drainer double; adjacent out-of-scope H4 doubles)
- VERIFIED-CORRECT (agree w/ plan): 4  (node_dd_pct recompute-on-load; node_peak_balance stays persisted; GUI-snapshot doubles are display-exempt; Money_Mul/Sub semantics)

---

## Findings

### [HIGH-1] F-096 fix is entry-only — the EXIT qty still round-trips Money→double→Money (`CoreFrameworks/EngineSharded/Async.hpp:829-830 → :896`)
- **Severity:** HIGH   **Category:** 4 (H4) + 5 (lossy ToDouble)   **Class:** H4 violation (TD-167)
- **Details:** The plan's Phase-E fix + its acceptance criterion are both scoped to the ENTRY split at `:842` (`legA=Money_Mul; legB=Money_Sub`). But `order_qty_d` is a `double` declared at `:823`, and the `is_exit` branch at `:829-830` reads `order_qty_d = Money_ToDouble(positions[portfolio_slot].quantity)`, then the SAME variable is converted back at `:896` via `Money{ money_from_double_payload(order_qty_d) }`. So a partial-exit's EXIT order quantity (and the non-partial `else { order_qty_d = full_qty; }` branch at `:851`) still routes the SUBMITTED order qty through `double`. `money_from_double_payload(Money_ToDouble(q)) != q` in general (Money `.v = value*1e8` in `__int128`; `/1e8` then reparse loses sub-satoshi ULPs on 8dp venue precision). This is the item-1(c) "the split may not be the only one" — CONFIRMED. Verified `order_qty_d` occurs ONLY at this site engine-wide (grep), and `BacktestSharded` shares this drain path, so the leak is live AND backtest.
- **Blocking against the plan's OWN acceptance criterion:** ":842 carries NO double" can pass green while `:829` still leaks — the criterion is mis-anchored to the entry line.
- **Recommended fix:** Convert the whole variable `double order_qty_d` → `Money order_qty`. exit: `order_qty = positions[portfolio_slot].quantity;` (direct, no conversion). entry-legA: `Money_Mul(intended, pct)`. entry-legB: `Money_Sub(intended, Money_Mul(intended, pct))`. entry-non-partial: `order_qty = intended;`. Update the guard `:858` `order_qty_d > 0.0` → `Money_Gt(order_qty, Money_Zero())` and the ctor `:896` to pass `order_qty` directly. Only then is the submitted-qty path double-free.
- **DESIGN_SPEC:** H4 (`DESIGN_PHILOSOPHY.md` §2); `wire-format-byte-preservation` n/a.

### [HIGH-2] partner_pending_pnl persist is INCOMPLETE without persisting partner_pending_bitmap — pnl-alone is net-negative (`CoreFrameworks/ControllerEventLoop.hpp:747` companion state)
- **Severity:** HIGH   **Category:** 6 (atomicity / W/L integrity)   **Class:** TECH_DEBT-227; Class-55-adjacent (dual-source split-reader)
- **Details:** The W/L pairing at `:1574-1591` is gated on `BITMAP_IS_SET(state->partner_pending_bitmap, bit)`. `partner_pending_bitmap` is `EventLoopState`-level (`:747`), reset to 0 at init (`:914`), and is NOT in the persist serializer. If Phase C persists `partner_pending_pnl` (Money, `:424`) ALONE: on warm-restart mid-pair (leg A closed, leg B open), the bitmap loads 0 → leg B's close takes the ELSE branch (`:1589`) → OVERWRITES the loaded leg-A pnl with leg B's, and SETS a pending bit for a partner that already closed pre-restart → the next UNRELATED exit on this node mis-pairs against the dangling bit → COMPOUNDING W/L miscount (strictly worse than today's single-pair miss). Persisting the pnl alone is a net-negative.
- **Recommended fix:** persist BOTH `partner_pending_pnl` (Money row) AND the per-node `partner_pending_bitmap` bit (1 byte / packed), atomically in the same NodeContext block — or persist NEITHER and accept the single-pair miss. Never pnl-only.
- **DESIGN_SPEC:** cross-thread-multiword-read-consistency (companion-state atomicity); `feedback_exhaustive_capture_and_verify_tracking`.

### [MED-1] Phase-E conservation assert `legA.qty+legB.qty==intended_qty` does not fit the drainer's separate-iteration structure and is vacuous under the proposed construction (`Async.hpp:846-852`)
- **Severity:** MEDIUM   **Category:** 6   **Class:** Class-51-adjacent (vacuous guard)
- **Details:** Both entry legs are pushed in ONE hot tick (`ExecutionCore.hpp:528-564`: `event_a` then `event_b`) but DRAINED in SEPARATE iterations of `drain_with_submit` (one event/iter) — leg A and leg B are NEVER in the same scope in the drainer. So a same-scope runtime `legA+legB==intended` is not implementable there. Moreover, under `legB := Money_Sub(intended, Money_Mul(intended,pct))` the identity `Money_Add(x, Money_Sub(y,x)) == y` is EXACT in-domain → the assert is vacuously true (catches nothing). The real risks it should catch — legs computed from a torn/stale `intended` across iterations, OR a future refactor computing `legB = Money_Mul(intended, Money_Sub(One,pct))` (which does NOT conserve under half-even) — are cross-iteration.
- **Recommended fix:** (a) rely on by-construction conservation (`legB` DEFINED as `intended − legA`) + a documenting `static_assert`/comment — sufficient and honest; OR (b) a non-vacuous per-node cross-iteration check (stash leg-A's submitted qty + the `intended` snapshot on the node; when leg B drains assert the sum). (a) is proportionate; the naive same-scope runtime assert should NOT ship as worded.

### [MED-2] partner_pending_pnl — persist HERE (E.1.2) vs defer to E.1.4 (the adversarial-refute spot)
- **Severity:** MEDIUM   **Category:** 6/7   **Class:** TECH_DEBT-227
- **Details:** GENUINELY LOST on restart, not reconstructable: when `partner_pending_pnl` is set (`:1589`) leg A's position is already CLOSED (removed from portfolio); its individual exit P&L is folded into `node_realized` and not separately recoverable. The MONEY is correct (`node_realized`/`node_fees` intact) — only the W/L CLASSIFICATION of straddling pairs corrupts. Recommendation: **persist HERE.** Rationale — the snapshot VERSION is ALREADY bumping this ship (epoch breaks regardless), the compose-sub-registries NodeContext serializer is being rebuilt in Phase C, so a Money row + bitmap bit is marginal-cost ≈ 0 (`feedback_opportunistic_tech_debt_closure` subsumption-not-adjacency); and W/L correctness across warm-restart is squarely in the live-readiness gate. The refutable counter (hand to the a-class): if E.1.4's fill-attribution / 16-bit fill-record owner reshapes partial-exit pairing, this field may be restructured there — but D-131 epoch-free makes a later rename cheap, so leaving a known miscount across the live gate is the larger risk. MUST land with the [HIGH-2] bitmap companion.

### [MED-3] Leg-split formula will exist in TWO places — extract a shared helper (SSoT) (`Async.hpp` new vs `PortfolioController.hpp:1344-1349`)
- **Severity:** MEDIUM   **Category:** 7 (cross-path parity)   **Class:** SSoT (`feedback_single_source_the_computation_not_the_mode`)
- **Details:** The plan's proposed fix is EXACTLY the canonical production sister `PortfolioController.hpp:1344-1345` (`qty_a=Money_Mul(sized_qty,pct); qty_b=Money_Sub(sized_qty,qty_a)`), which ALSO splits the entry FEE proportionally (`:1348-1349`). Two copies of a money-split formula WILL drift. Note PortfolioController is the legacy/single_core (deprecated) path; the SHARDED backtest shares the Async drain path, so the fix INTRODUCES no live↔backtest divergence (item 4 = CLEAN) and CONVERGES the sharded path onto the sister's exact formula (a parity improvement). But the two-copy state is the codification risk.
- **Recommended fix:** extract `Money_LegSplitQty(intended, pct, leg)` (+ optional fee variant) into a shared header (FixedPoint/ or a leg-split util) and call it from BOTH sites. Sharded fee is naturally per-leg (computed at fill from each leg's qty) so the fee-split helper is PortfolioController-only — verify `round(fee_a)+round(fee_b)` vs sharded per-leg fee if legacy parity is ever asserted (legacy path, low priority).

### [LOW-1] No CI guard covers the drainer qty-double post-fix
- **Severity:** LOW   **Category:** 4
- **Details:** `check_latency_path_conformance.py` H4 no-scalar-float gate covers the PRODUCTION hot (`ExecutionCore_Tick`) + 6 slow kernels, NOT `drain_with_submit` (Async.hpp drainer). So [HIGH-1]'s site has no mechanical regression guard. `check_money_gross_single_source.py` guards only the price-diff GROSS (via `Money_FillGross`), not qty splits. CI candidate: a grep/AST guard for `Money_ToDouble(...)` feeding `money_from_double_payload(...)` on a qty/order path (post-fix, to lock it).

### [LOW-2] Adjacent H4 doubles OUTSIDE the partial-exit path — do NOT fold into E.1.2
- **Severity:** LOW   **Category:** 4
- **Details:** Money-path `double` sites unrelated to F-096 (flagged so the orchestrator knows E.1.2 is not the last H4 cleanup; do NOT expand scope): `allocated_balance` boot allocation via `double` mul/div (`Async.hpp:361-373`, computes a PERSISTED Money field through double — boot-time-only); SL trailing ratchet (`ControllerEventLoop.hpp:3673`); breakeven SL (`:3734`). Separate debt; home/track, don't fold.

---

## Verified-correct (agree with the plan)

- **node_dd_pct recompute-on-load is SOUND.** Currently raw-persisted (`ShardedSnapshotPersist.hpp:213` save / `:466` read / `:556` commit). Its recompute at `ControllerEventLoop.hpp:2909` (`node_dd_pct = Money_Div(drop, node_peak_balance)`, `drop = peak − current_value`, `current_value = alloc + realized + unrealized`) is a pure function of PERSISTED inputs: `node_peak_balance` (`:212`), `allocated_balance` (`:187`), `node_realized` (`:192`), and `unrealized` from the PERSISTED `positions[]` (`:169`, via `Money_FillGross` `:2892`). The kill-check (`:2917-2925`) is INSIDE the rebuild right after the recompute → trading logic always sees a fresh value; the only staleness window (load→first rebuild) is cosmetic (a GUI read could show 0 for one cycle, self-heals). Dropping the raw persist is correct SSoT hygiene. All-in-Money (no double; the `:2927` `Money_ToDouble` is fprintf display-only, H4-exempt).
- **node_peak_balance correctly STAYS persisted** — a running-max accumulator (`Money_Max` over rebuilds), NOT derivable from a single snapshot instant → must persist. Consistent with the D-206 `Position.peak` the plan ADDS (also a persisted non-derivable accumulator).
- **ShardedSnapshot.hpp:490-496 per_node doubles are a DIFFERENT, also-safe category** — they are the GUI TUISnapshot (in-memory, double-buffered), regenerated EVERY publish from live Money state via `Money_ToDouble` (`node_open_notional`/`node_budget_used_pct`/`node_peak_balance`/`node_dd_pct`). Display-only → H4-EXEMPT, no persist → no staleness/drift. NB: the directive lightly conflates this GUI snapshot with the PERSIST snapshot — the "derived-AND-persisted" Fight-#2 concern is ONLY the persist-side node_dd_pct (`ShardedSnapshotPersist.hpp:213`), not these.
- **Money_Mul/Money_Sub semantics are CORRECT for the qty split.** `partial_exit_pct` is a FRACTION (0.0,1.0) — `ControllerConfig.hpp:549` ("fraction... 0.5 = 50%"), `CfgFieldRegistry.hpp:682` `DBL(0.5, 0.0, 1.0)`, parsed `pct_scale=false` (`ControllerConfig.hpp:3072`), validated `(0,1)` (`ControllerEventLoop.hpp:1157-1160`) — so `Money_Mul(intended, pct)` needs NO /100. `Money_Mul` is exact-decimal half-even (`FixedPoint:1583`); `Money_Sub` is exact in-domain (`:1635`) → `legA+legB == intended` EXACT by construction. Saturate/half-even are correct for a qty split.

## Spots most worth an adversarial refute (for the paired a-class)
1. **[MED-2] persist-HERE recommendation** — refute: "defer to E.1.4 because fill-attribution reshapes pairing." Push on whether the field survives E.1.4 unchanged.
2. **[HIGH-2] bitmap-companion claim** — refute by tracing whether ANY other path re-establishes `partner_pending_bitmap` on load (e.g., a post-load reconcile that re-derives pending pairs from position `pair_index`). If such a re-derive exists, the bitmap need not be persisted. (I found none, but the a-class should try to construct one from `pair_index` `+` `partner_pending` semantics.)
3. **[HIGH-1] magnitude** — refute: "the double round-trip is exact for all realizable crypto qtys, so it's cosmetic." Push on whether venue 8dp × large base qty ever exceeds double's exact integer band, and whether H4 categorical trumps magnitude here.
4. **[MED-1] assert form** — refute: "the vacuous assert still documents intent, ship it." Push on Class-51 (vacuously-green guard) vs a real cross-iteration check.
