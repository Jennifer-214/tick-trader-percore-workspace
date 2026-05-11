# Post-v4.0 follow-ups

Things flagged during the v4.0 release night that aren't blockers for live
testing but should be picked up afterward. Sorted roughly by leverage.

## UX polish on the new Settings tabs

These are quick wins (~30-60 min each) that directly address the "settings
page is a mess, hard to use" feedback that drove the v4.0 per-core config
work. The mechanism shipped, but the surface around it still has rough
edges.

### 1. Per-core tab: show inherited values next to override fields

Right now an override field reading 0.00 is ambiguous — does that mean "0%
TP" or "inherit from Global tab"? Should display the inherited value as a
small grey hint:

```
TP %    [    0.00]   (inherit: 6.00)
TP %    [    4.50]   (override)
```

Implementation: in `Settings_RenderPerCoreTab`, after the InputFloat, look
up the same-named field in `field_defs[]` (or pass the global state in)
and render the resolved value. Tooltip the field with both values.

### 2. Move strategy + risk + model_path into per-core Settings tabs

Today, three categories of per-core settings live in three different
places:

- Strategy — set via the separate "Per-Core Strategy" panel (dropdown +
  Apply button)
- Risk — `core_N_risk_pct`, cfg-only (no GUI)
- Model — `core_N_model_dir` / `core_N_model_path`, cfg-only (no GUI)

All three should live in each per-core tab so a Core N tab is the single
source of truth for that core's behavior. The "Per-Core Strategy" panel
can stay as a quick-swap shortcut, but the canonical control is in
Settings.

Implementation:

- Add a new section "Strategy + Risk" at the top of each Core N tab
- Strategy: ImGui::Combo with the same labels (MR/MOM/DIP/ML/EMA), writes
  `core_N_strategy=<name>` and triggers the same swap-pending flow as the
  panel (atomic write to `shared->swap_strategy_requested[N]`).
- Risk: InputFloat for `core_N_risk_pct`, writes the cfg field.
- Model: InputText for `core_N_model_dir` (preferred) and
  `core_N_model_path` (legacy fallback). Touching either triggers an
  engine restart hint — model load happens at boot only.

Tricky bit: model_path/dir requires engine restart to take effect.
Either add a "save & restart hint" on those fields, or accept the
limitation and document.

### 3. Hide / relabel legacy per-strategy global sections

The Global tab still has "MR Tuning", "Momentum Tuning", "EMA Cross
Tuning" sections. Same field names appear in per-core tabs. Confusing.

Two options, both fine:

- **Hide**: drop those sections from Global. They become per-core-only.
  Cfg keeps the global field for backward compat but no GUI surface.
- **Relabel**: keep them but rename to "Global default — MR" etc., with
  a note "per-core tabs can override". Less destructive.

Lean toward hide. The strategy-type globals were always the "if no
override is set" defaults, which is exactly what a `take_profit_pct`
type field does — we don't need a parallel mechanism.

## Operational gaps for live testing

These matter once you're running with real money. Don't pre-build them —
let real friction tell you which one hurts most. Listed in rough order
of likely impact.

### 4. Kill switch panel

`ks_*` cfg fields are settable but the live kill-switch state isn't
visible. Worth a panel showing:
- Current peak equity / current equity / drawdown $
- Drawdown % vs `ks_max_drawdown_pct` threshold
- Days-to-trip estimate based on recent burn rate
- "Tripped at $X on YYYY-MM-DD HH:MM" if it tripped
- A reset button (also wired today via `K` keybind)

The data exists in `OrderManagerState::ks_*`. Plumbing into a snapshot
field + GUI panel is straightforward.

### 5. Notification log panel

`Notify_Send` writes to stderr and/or external command, but there's no
GUI display of recent alerts. A scrollable panel showing the last N
notifications (color-coded by `NotifyLevel`) means you don't need a
terminal open during live trading.

Implementation: add a ring buffer to `NotifyState` (already exists for
backend cooldown) that the GUI reads via TUISnapshot. Or have the GUI
tail `logging/notify.log` (if we add a file backend).

### 6. Panic flatten button

Single-click "close all positions on all cores immediately." Wired to
clear permission on every core + submit market sell on every active
position via OMS. For when something looks wrong and you don't want to
wait for TP/SL.

Important: behavior in paper vs live mode differs (in live, this
submits real market sells; in paper, just closes the slot). Consider a
confirmation dialog with current position values.

## Bigger projects (separate sessions)

### 7. Per-core dashboard view

All 4 cores' positions / P&L / state side-by-side, not just aggregated
into one Account panel. Probably a new top-level panel that takes a
horizontal strip of the screen. Each core gets a column with:
- Strategy name (live-updating with hot-swap)
- Active position (entry / TP / SL / unrealized P&L)
- Equity contribution (this core's share of session P&L)
- Per-core latency p99
- ML state if STRATEGY_ML (prediction, conf, IC)

### 8. Replay mode

Load a recorded tick CSV (the engine already records via TickRecorder
when `record_ticks=1`), replay at variable speed in the GUI.
Use cases:
- Validate a strategy change against yesterday's market without waiting
  for live ticks
- Reproduce a specific entry/exit sequence to debug
- Demo the engine without needing a live connection

The producer thread already supports a synthetic mode; "replay" is
synthetic-from-CSV. Speed control: 1× (real time) up to maybe 1000×
(burn through a day in seconds).

### 9. Live A/B comparison panel

When two cores run the same strategy with different overrides, this is
the panel that says "Core 0 with TP=4% beat Core 1 with TP=6% by $X
over the last hour." Shows per-core equity curves overlaid + summary
stats.

This is the feature the per-core overrides exist to enable, but the
visualization is its own work.

## Defects to revisit

### ID stack popup in ImGui

Originally diagnosed as the per-core strategy panel's PushID/PopID
imbalance and fixed (commit 4b6a36f). User reports still seeing a
similar popup occasionally — couldn't reproduce reliably during the
release night. If it surfaces again, capture the exact assertion text
(ImGui's popup has the ID hash + line) and trace from there.

The most likely remaining culprits are
- Settings_RenderPerCoreTab's PushID(j) inside the inner loop — could
  collide with PushID from a containing scope
- ImGui::Combo using "##strat" hidden label within the row's PushID
  scope — should be unique but worth double-checking

Defensive fix if it persists: wrap each tab body with PushID(tab_index)
+ PopID, isolating each tab's ID stack completely.

### Settings_Load doesn't initialize defaults

`Settings_Load` only populates fields that appear literally in
engine.cfg. Missing keys leave the corresponding `s->float_vals[i]`
at zero. This caused the "only Core 0 tab visible" bug when
`num_execution_cores` was unset (cfg default = 4 on engine side, but
SettingsState saw 0 → clamped to 1).

Fix shipped: GUI_Panel_Settings now takes `live_core_count` from the
TUISnapshot and uses it as the source of truth, falling back to the
cfg-loaded value, falling back to 4. But the underlying issue is that
SettingsState defaults don't match engine defaults. Should call
`ControllerConfig_Default<F>()` once at SettingsState init and seed
`s->float_vals[]` from the resulting struct via the same field-name
mapping. Then missing cfg lines get the engine's actual default
instead of zero.

## Don't bother

Things that came up but aren't worth doing:

- Save-config-as / load-config-from-file in GUI: cfg is one file, edit
  it directly when you want a different config. Don't need a save
  dialog.
- Hot-add a core at runtime: complicated and rarely needed. Restart is
  fine.
- Strategy hot-swap with open position (force flatten): the deferred-
  swap is correct behavior. Adding a "force-close-and-swap" path
  introduces fee/timing surprises that are hard to reason about.

## Audit findings (added 2026-04-25 evening)

Issues found while auditing what v4.0 might have introduced. Critical
one (cfg_write_field) shipped fixed in a1ace6d; medium/low listed here
for later.

### Hot-swap-to-ML on no-model core silently falls back to SimpleDip

`model_handle` is set at engine boot for cores configured with
`core_N_strategy=ml` and a model path. If you hot-swap a non-ML core to
ML mid-session, that core has `model_handle == nullptr` →
`ML_BuildParameters` sees no zoo → fallback path runs SimpleDip with
`strategy_id=STRATEGY_ML`. Display claims ML, behavior is DIP.

Fix: in the slow-path swap handler in EngineSharded, when applying a
swap to STRATEGY_ML on a core whose model_handle is null, emit a
fprintf warning and either (a) refuse the swap or (b) accept it but
flag the core as "ML-no-model" for the GUI to display clearly.

Probably option (a) — refusing makes the failure mode loud. The
scenario "I want to swap to ML but I don't have a model" is a setup
mistake, not a runtime decision.

### Sharded per-core ConfidenceScorer state doesn't persist

Lives in `CoreContext::confidence` (controller-side runtime state),
not in the v7 PortfolioController snapshot format. Engine restart =
all per-core scorers reset to the noise-floor IC=0.01.

For research / paper trading this is fine — restart resets the IC
calibration but that's recoverable. For production live trading where
a model has built up real IC over days, you'd lose that calibration
on every restart, falsely triggering the noise-floor armed-but-
inactive safety mode.

Fix: bump snapshot to v8, extend with per-core CoreContext state
(confidence, staged_prediction, active_prediction, last_confidence).
Save/restore in EngineSharded_Run alongside the existing
PortfolioController snapshot.

### Buy Gate panel status uses global gate_direction

The new per-core Buy Gate table (commit ad9f2b9) computes the
"READY/wait" status by comparing `s->price` against
`per_core[i].buy_gate_price` using the GLOBAL `s->gate_direction`.
Cores running mixed strategies (MOM = price >= gate, MR = price <=
gate) get the wrong direction shown for the non-headline strategy.

Fix: add `gate_direction` to TUISnapshot::PerCoreSnap, populate from
per-core GateParameters in TUI_CopySnapshotSharded (look at the
strategy_id and apply the same direction logic the live path uses).
Use that per-core direction in the panel.

### Sharded silently doesn't honor partial_exit_enabled

`partial_exit_enabled` / `partial_exit_pct` / `tp2_mult` /
`breakeven_on_partial` are processed only by legacy
`PortfolioController` (see `PortfolioController.hpp:~1261`). Sharded
`ExecutionCore` has one TP and one SL per position — the entire
infrastructure for partial fills doesn't exist on the sharded side.

**Train-serve consequence:** if you backtest with split exits enabled
and live-trade in sharded mode, the trade COUNT and P&L distribution
will differ. Backtest produces 2× as many win/loss events per entry
(each entry exits in TP1 + TP2/SL); live produces 1 exit per entry
at the original TP / SL. Same strategy, different P&L curve.

**Architectural note (corrected scope):** legacy doesn't ratchet a
single position from TP1→TP2. It opens **TWO POSITIONS** per entry
signal — leg A with TP=TP1, leg B with TP=TP2, both share SL. They
exit independently. See `PortfolioController.hpp:1278-1281` and the
`pair_index` field on Position. `do_split` requires
`Portfolio_CountActive + 2 <= max_positions` — partials need 2 free
slots.

**Real scope to port to sharded: 4-5 hr, hot-path surgery.** Each
core needs to own a PAIR of slots, not one. Touches:

- `Portfolio` slot allocation: each core gets `slot[2*core_id]`
  (leg A) and `slot[2*core_id+1]` (leg B). Capacity halves: 4 cores
  use slots 0-7 instead of 0-3.
- `ExecutionCore` hot path: two `live_tp` / `live_sl` pairs to track
  both legs simultaneously. Branchless SG check on both (~2-4ns
  added per tick to a 40-400ns budget — significant).
- `OrderManager_HandleFill`: differentiate "leg A of pair" vs
  "leg B of pair" vs "single position." Leg A close = ship TP1
  P&L, do not touch leg B; leg B close = ship TP2 P&L, mark pair
  closed.
- `drain_with_submit`: needs to know about pair coupling so the
  TradeEvent → OrderManager_Submit chain handles partial qty.
- Per-core capacity halves with partials enabled. Either document
  this constraint or wire `num_execution_cores` validation.
- Tests: add multi-position-per-core test fixtures to
  `controller_test.cpp`.

**Why option-A (ratchet single position) won't work:** the hot path
reads `core->live_tp` directly (not via cached_params, see
`ExecutionCore.hpp:240`). The controller can't safely write
`live_tp` from another core without either an atomic-load on every
hot-path tick or some seqlock-style protocol. Both add cost to the
most performance-critical line in the engine.

**Why option-B (two-positions-per-core) is right:** matches legacy's
data model exactly (each leg is a real Position with its own slot,
TP, SL, exit logic). Hot path's pattern of "active core has its own
TP/SL" extends cleanly to "active core has TWO sets of TP/SL."
Drainer can handle pair coupling without touching the hot path's
fast loop.

**Workaround until then:** set `partial_exit_enabled=0` in
backtest.cfg so backtest matches live. Retrain models with single
exit. ~30 min vs 4-5 hr. If a strategy genuinely needs partial
exits to be profitable, do the proper port — but the model
selection criterion should match what live executes, full stop.
