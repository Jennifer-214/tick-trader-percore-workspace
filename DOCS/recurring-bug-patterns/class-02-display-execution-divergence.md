---
type: ledger-template
class_id: 2
title: Display ↔ execution divergence
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
surface_tags: [gui-thread, live-trading, hot-path]
severity: high
recurrence_count: 8
first_instance: v5.4.0
closure_mechanism: predicate-display invariant matrix (DOCS/EXECUTION_DISPLAY_INVARIANTS.md) + /readiness Check 12 display↔execution + /dust Scan 8 dead-write detection + single-source rule (GUI reads SAME variable as controller)
sister_classes: [1, 11]
---

## Class 2 — Display ↔ execution divergence

**Surface:** gui + live (display panel reads diverge from hot/slow-path execution writes).

**Symptom:** GUI shows a number that has nothing to do with what
will actually trigger an exit. e.g., displays SL=$50000 but the hot
path will fire at SL=$50500 (the ratchet floor). User makes
decisions on stale display data.

**Root cause:** GUI reads a "logical" field (`pos->stop_loss_price`)
that was the source of truth in legacy. Sharded hot path reads a
DIFFERENT field (`core->live_sl + cached_params.ratchet_sl`) for
the same decision. Both fields exist; both compile; both have
plausible-looking writes. Only the hot path's write matters; the
GUI's read is dead.

**Detection:**
```bash
# For each Position field referenced in GUI/, find the hot-path read
grep -rn "pos->stop_loss_price\|pos->take_profit_price" \
    GUI/ DataStream/ CoreFrameworks/
# Then for each, check if hot path (ExecutionCore.hpp / SG_Evaluate)
# reads the same field — if not, it's a divergence
```

**Known instances:**
- v5.4.0 Phase 4 — Positions panel read `pos->stop_loss_price` while
  hot path used `max(live_sl, ratchet_sl)`. Fixed in `b3b77a6`.
- v5.4.1 / v5.4.2 — `snap->fees`, `snap->maker_fills_count`,
  `snap->taker_fills_count`, `snap->total_maker_fees`,
  `snap->total_taker_fees` set in legacy `EngineTUI.hpp` but never
  in sharded `ShardedSnapshot.hpp`. Fixed in `f82d94f` + `7b04ac1`.
- v5.15.5.F.4d.1.E.0.10 (sharded-migration cohort, 2026-06-12/13) —
  **A29** GUI-drag writes `pos->take_profit_price`/`stop_loss_price`
  (`Async.hpp:246-247`) but the hot exit gate fires on
  `core->live_tp`/`live_sl` → a dragged stop has NO execution effect
  (gates-live; TECH_DEBT-184). **A30** `is_trailing =
  (take_profit_price != original_tp)` is perma-FALSE on sharded (the
  ratchet moves `ratchet_sl`/`live_tp`, never `pos->take_profit_price`).
  **A32** spacing GUI diag (`ControllerEventLoop.hpp:2974`) reads the
  FLAT `spacing_cfg.spacing_multiplier` while the gate `Strategy_SpacingOk`
  reads the per-node slice (folded into A24's option-(c) fix). **A35**
  `GATE_EMA_ENABLED` is GUI-badged but inert on sharded (sub-pattern 2c
  — display says active, isn't). All "sharded migration left the GUI
  reading the legacy field" instances; also Class-44 cfg-flag overlap
  (A35). See `E.0.10-finding-disposition-register.md` + D-211.

**Prevention:**
- Readiness skill Check 12 (display ↔ execution invariant).
- Dust skill Scan 8 (dead-write detection).
- Audit script: `grep -oE "snap->[a-z_]+" EngineTUI.hpp` and
  `grep -oE "snap->[a-z_]+" ShardedSnapshot.hpp`; legacy-only
  fields are candidates.

### Sub-pattern 2c — Display predicate is a strict subset of hot-path predicate

**Symptom:** GUI says "READY" but no fire happens, or shows "off"
with no explanation. Operator looking at the dashboard cannot tell
whether the engine is correctly inactive or silently broken.

**Root cause:** The hot path enforces N conditions for an entry/exit
to fire (e.g. `price_ok & volume_check & ~blocked & permission &
~any_active`). The GUI's "READY" predicate checks fewer than N. Any
condition checked by the hot path but NOT the GUI produces "looks
ready, isn't ready" misleading state.

**Detection:**
```bash
# Inventory hot-path entry predicate terms
grep -A30 "Inlined BG_Evaluate" CoreFrameworks/ExecutionCore.hpp | \
    grep -oE "[a-z_]+_ok|[a-z_]+_check|[a-z_]+_required" | sort -u
# Inventory display predicate terms
grep -A20 "READY\|wait\|in pos" GUI/DashboardPanels.hpp | \
    grep -oE "price_ok|volume_ok|blocked|permission|any_active" | sort -u
# Diff = silent terms.
```

**Known instances:**
- v5.6.0 — Buy Gate top table only checked `price_ok`; ignored
  `BUY_BLOCKED`, `permission`, `volume_required`. Fee-floor BUY_BLOCKED
  (StrategyParameters.hpp:884) silently dropped DIP entries.
- v5.6.0 — `halt_reason = 10` (book-imbalance) was set in the
  controller but `halt_names[]` only had indices 0-9; entire
  imbalance veto was invisible.

**Prevention:**
- v5.6.0 enforces a "predicate ↔ display matrix" in
  `DOCS/EXECUTION_DISPLAY_INVARIANTS.md`. New hot-path predicate
  terms MUST add a corresponding GUI surface in the same PR.
- `controller_test.cpp` predicate-parity test asserts the display
  Status string matches the hot-path mask outcome under each
  isolated condition.
- Single-source rule: numeric thresholds shown in GUI must read the
  SAME variable the controller checks. No display-side recomputation.
