# Class 46 — Completeness-assuming terminal action on a possibly-partial event

**Codified:** 2026-06-13 (v5.15.5.F.4d.1.E.0.10; D-214 — the A16 fill-path cascade + the 4-agent keystone-validation). **Severity:** HIGH (capital-correctness; LIVE-reachable on real venue partials). **recurrence_count:** 2 (A16 book-and-free-on-PARTIAL; the SELL-partial whole-slot close). **The fill path's actual root** per the D-214 three-spines (spine 1 of {fill-completeness, cross-thread-coherence, per-node-purity}).

## The pattern

A **terminal / irreversible OMS action** — free the order slot, book the position, close the position, account the P&L — fires gated on **REACHING a code path** (e.g. "the handler ran", `event_log_mode==1`) rather than on the **venue completeness signal** (`order_complete` / `fill_qty` vs `requested_qty`). So a **PARTIAL / non-terminal event** triggers the terminal action prematurely. The code was built single-fill-synchronous-and-complete; live fills are multi-event, partial, and asynchronous — the assumption "this fill is the whole order" is baked into the action, not checked.

The defect is wrong **even with one clear owner and one published truth** — it is NOT a single-source-of-truth or ownership problem (that distinction is what the over-lumped "keystone" got wrong; see D-214 / the AR-6 recurrence note). `Portfolio_CloseSlot` ignoring `fill_qty` has exactly one owner and still books a full-position P&L on a partial exit. The root is **completeness/temporality**, not representation-divergence.

**Distinct from:**
- **Class 3** (drain count under partials) — Class 3 is the *count* of drained legs; Class 46 is the *terminal action* (free/book/close) gating on a possibly-partial event.
- **Class 44** (bound/computed value with a dead or overwriting consumer) — Class 44 is a value that is written-but-unread / overwritten; Class 46 is an action that *fires too early* on incompleteness. Not a dead consumer.
- **Class 45** (reconstruct path reads a DIFFERENT source field) — Class 45 is a forward-vs-reconstruct *source* divergence; Class 46 is a forward-path *completeness* assumption.
- **Class 38** (phantom invariant) — sibling at the comment layer: `Order.hpp:179-180` ("running total / weighted across partials") is the phantom-invariant comment that *advertises* the completeness this class shows is never honored.

## Detection signature

Find a terminal/irreversible OMS or portfolio action and check what GATES it:
- slot free: `order_bitmap &= ~(1u << slot)` — is it gated on `Order_GetState(o) == ORDER_FILLED` (terminal), or does it run on any path that reaches it (incl. `ORDER_PARTIAL`)?
- booking / fill handling: `OrderManager_HandleFill` / `handle_buy_fill` / `handle_sell_fill` dispatch — gated on a completeness signal, or on `event_log_mode` / "we got here"?
- position close: `Portfolio_CloseSlot(...)` — does it take and respect a `fill_qty`, or close the whole slot regardless of how much actually filled?
- Red flag: a terminal action whose only guard is reaching the handler, on a path that an `order_complete==0` / partial event can reach.

## Canonical instances

- **A16** (`OrderManager.hpp`): `OrderManager_ProcessFillCommand` books `HandleFill` (`:1438`, gated on `event_log_mode==1` not `ORDER_FILLED`) AND frees the slot **unconditionally** (`:1465`) on any terminal-reaching path — a PARTIAL (`order_complete==0` → `ORDER_PARTIAL` at `:1432`) books at the partial qty then frees → the next fill for the remainder finds the bitmap clear → `slot=-1` → **dropped**. (`filled_qty` is per-invocation-overwritten at `:1419`, NOT accumulated — the `Order.hpp:179` "running total" comment is the Class-38 phantom.) LIVE-only (paper/backtest emit one synthetic full fill).
- **SELL-partial whole-slot close** (`OrderManager.hpp:1234` → `Portfolio.hpp:413`): `handle_sell_fill` calls `Portfolio_CloseSlot(&oms->portfolio, pslot, fill_price)` — the signature takes **no `fill_qty`**; it closes the entire slot `quantity` and books gross/P&L on the full position, regardless of how much the SELL actually filled → on a partial exit the engine books a full-position close while the venue still holds the remainder (a naked, un-booked residual). The exit-side twin of A16; survives both the A2 parser fix AND the A16 book/free gate.

## Structural fix

A **protocol-agnostic normalized fill event** at the OMS boundary (the venue adapter normalizes WS-per-increment `"l"` / REST-cumulative `"z"` / FIX → one common POD) + an OMS state machine where **every terminal action gates on `ORDER_FILLED`** (a PARTIAL keeps the slot open + books nothing or accumulates correctly), and recovery **reconstructs the net position from venue truth, NOT by replaying fill-by-fill**. The real handler (weighted-avg re-entry + keep-slot-open + partial-reduce) folds to `.E.1` (the per-node-owned fill consumption + venue-net reconcile, `data-disciplines/per-node-position-ownership-model.md`); the `.E.0.10` interim is a loud-STOP/assert + the LiveReadiness gate (live can't enable until the handler lands). Sister DESIGN_SPEC: the fill-completeness spec (extends `per-node-position-ownership-model.md`). closure_mechanism: the completeness-gated state machine + a CI detector (folds into the Class-44 write-with-no-live-read / dead-flag detector — extend it to "terminal action not gated on the completeness signal").

## False-positive surface

- An action that is **genuinely terminal-only by construction** (it can only be reached after `ORDER_FILLED`, proven — e.g. the dedup early-return at `OrderManager.hpp:1404` already excludes re-entry on FILLED) is NOT this class — Class 46 is the action reachable on a PARTIAL/non-terminal path.
- **Paper/backtest synthetic fills are atomic by construction** (one synthetic full-qty event); forcing `order_complete=1` there (A17) is CORRECT, not a masking of this class — there is no partial path in paper. The class is LIVE-only (real venue partials).
- An action that takes and respects `fill_qty` / a completeness flag (closes/books only the filled portion, keeps the slot for the remainder) is the FIX, not an instance.
