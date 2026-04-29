# Sharded Completion Plan (reviewed 2026-04-26)

Goal: bring sharded engine to "honest production" — every advertised
per-core feature actually works, no aggregate-shaped surfaces lying
about per-core state. ANSI TUI explicitly out of scope (Jenn said
afterthought, sharded GUI is the only product).

Rollback point: `pre-phase2-risk-enforce` tag at commit `2a34845`.
Backup branch: `backup/pre-phase2-2026-04-26`. Both pushed to origin.

---

## Decisions (locked)

1. **ANSI TUI:** revisit later. Keep build target compiling but
   skip display reworks. If snapshot-field cleanup breaks rendering,
   gate the affected ANSI sections on `!sharded_mode_active`.
2. **Phase 2 model:** **B (soft-enforce sizing clamp).** A fights
   the single-Binance-account reality. B is honest about "one pool,
   N risk-limited pilots" — same model as multi-strategy hedge funds.
3. **Kill reset:** **separate Risk panel** with per-core controls.
   Account stays read-only / monitoring.
4. **Persistence:** **no backward compat.** Sharded engine has NO
   persistence today (legacy used `CONTROLLER_SNAPSHOT_VERSION 11`,
   sharded never adopted it). Build fresh, refuse legacy v11 files.

---

## Reviewed risks + corrections

### Discovered during review

- **Sharded has no persistence at all** — Phase 4 isn't "extend v7
  to v8" as the original plan said. It's "build from scratch."
  Bigger than I estimated. Revised estimate: 2-3 days, not 1-2.
- **`allocated_balance` is set ONCE at startup** — not recomputed
  with realized P&L. This is intentional under the static-allocation
  model. Phase 2 enforcement therefore clamps against the static
  value, not a moving target.
- **Single-position-per-core invariant means current sizing already
  consumes full allocation per trade** — `trade_size = allocated_balance / entry_price`. So Phase 2.2's clamp has no observable effect under
  default config (max_positions=1). The meaningful enforcement is:
  (a) defending against a corrupted `intended_qty` from a bug,
  (b) future multi-position-per-core.
  Need to be honest about this in the commit message — it's mostly
  a defensive change, not a quantity-changing one today.
- **CRITICAL: notional accounting symmetry** (Phase 2.1 detail).
  Easy mistake: on entry add `entry_price × qty`, on exit subtract
  `exit_price × qty`. After a winning trade these don't cancel —
  positive residue accumulates per trade. **Correct pattern: subtract
  the SAME entry_price × qty on exit, using the snapshot already
  captured by the existing exit code (`entry_price_snap`, `qty_snap`
  at PortfolioController.hpp:503-505 equivalent in EventLoop_OnEvent).**
- **FPN_Sub doesn't saturate** — if `core_open_notional` ever
  exceeds `allocated_balance` (rollout edge case), subtraction
  wraps. Use `FPN_SubSat` or guard explicitly.
- **FPN division zero guard** — Phase 2.2's
  `(allocated - core_open_notional) / entry_price`. Existing
  `_BuildParameters` guards entry_price; clamp must mirror.
  `FPN_DivNoAssert` saturates to MAX on zero divisor → would clamp
  qty to MAX (no clamp). Per the FPN Division Guards invariant in
  CLAUDE.md, this needs an explicit check.
- **Phase 3 unrealized P&L gap.** Realized-only kill switch fires
  AFTER bad exits, not during bad price moves. A position that
  rides from $100 → $50 with no SL hit yet won't trip kill, even
  if 50% unrealized loss exceeds drawdown threshold. **Recommend:
  mark-to-market on slow path** — `unrealized = (current_price - entry_price) × qty` for each open position, peak/dd computed
  against `allocated + realized + unrealized`. Slow path only,
  cheap, more correct.

### Hot path / branchless verification

Walking each phase against "no hot-path additions, branchless+FPN
preserved":

- **Phase 1 (display):** Pure GUI. No hot path.
- **Phase 2.1 (instrument):**
  - Updates: in `EventLoop_OnEvent` — slow path (not the per-tick
    hot path). Two `FPN_Add` / `FPN_Sub` calls. Branchless ✓
  - Snapshot read: `FPN_ToDouble` for display. System boundary ✓
  - Hot path: untouched ✓
- **Phase 2.2 (enforce):**
  - Sizing clamp: in `Strategy_*_BuildParameters` (slow path —
    runs on slow_path rebuild, not per tick). One `FPN_Min`,
    one zero-guard `FPN_IsZero`, one division. Branchless except
    the division guard (early return on zero — slow path branch is
    OK, but for discipline use mask: `cond × value`).
  - Halt-when-budget-exceeded: zero-gate via mask, identical
    pattern to existing halt reasons (D8). Branchless ✓
  - Hot path: untouched ✓
- **Phase 3 (kill switch):**
  - Peak update: `peak = FPN_Max(peak, current)` on slow path,
    after exit P&L booking. Branchless ✓
  - DD compute: `(peak - current) / peak` on slow path with zero
    guard. One division.
  - MTM (recommended addition): per-open-position loop on slow
    path. Bounded by `MAX_POSITIONS_PER_CORE`. Branchless arithmetic.
  - Trip flag check on entry build: zero-gate via mask. Branchless ✓
  - Hot path: untouched ✓
- **Phase 3.5 (Risk panel):** Pure GUI. No hot path.
- **Phase 4 (persistence):** I/O only, slow path or shutdown.
  No hot path.

**Verdict: hot path stays clean across all phases.** All new state
lives on `CoreContext` / `EventLoopState` (slow-path data structures).
The 40-400ns p99 target is preserved — `ExecutionCore_Tick` /
`BG_Evaluate` / `SG_Evaluate` are not modified.

### Tests we need + tests we won't break

Existing 351 assertions touch:
- `EventLoop_*` accessors and event handling — Phase 2/3 add fields
  to CoreContext, must update Init (already covered in plan).
- Strategy_*_BuildParameters — sizing — Phase 2.2 changes the qty
  output when budget < strategy_qty. Tests that assert exact qty
  values with a known allocation will need to be aware of the clamp.
  Most tests today use single-position-per-core with full allocation
  available, so the clamp is a no-op. Sweep before claiming "clean".
- Snapshot tests — none today for sharded (not built yet).

New test groups needed:
- Phase 2.1: "core_open_notional accounting" — entry adds, exit
  subtracts symmetric value, returns to zero after round trip.
- Phase 2.2: "per-core budget enforcement" — clamp at exact value,
  halt fires when budget exhausted, multi-core scenario where one is
  at-budget and others trade freely.
- Phase 3: "per-core kill switch" — peak tracking with MTM, dd
  computation, trip threshold, halt fires while tripped, manual
  reset clears trip + peak, aggregate breaker independent.
- Phase 4: "sharded persistence v1" — round-trip save/load,
  refuse legacy v11 magic, malformed file doesn't crash.

### Things that could go wrong (and how to detect)

| Risk | Detection |
|---|---|
| Notional accounting drift across many trades | Phase 2.1 test: open + close N positions, assert `core_open_notional == 0` after each round trip |
| Hot reload on `risk_pct` doesn't propagate to `allocated_balance` | Manual: change cfg, observe per-core "Alloc" column in Account panel — does it update? Likely **NO** today (it's set once in EngineSharded_Run); needs explicit handling in HotReload path |
| `Reset Paper` doesn't reset `core_open_notional` / kill state | Smoke test: open positions → click Reset Paper → verify all per-core counters zero |
| Kill switch trips on near-zero allocation (tiny absolute loss = huge %) | Add absolute-loss floor: trip only if `(peak - current) > min_kill_loss` (cfg, default $5) |
| MTM uses stale price if no recent ticks | Slow path uses last seen price from rolling stats — staleness bounded by slow-path cadence (~few seconds) |
| Persistence saves while engine still trading | Save on shutdown signal + periodic backup. Use atomic rename (write to .tmp, rename) to avoid half-written files |
| Persistence file contains different `num_cores` than current engine | Refuse load if mismatch, OR pad/truncate per-core array. Recommend refuse-and-warn |
| `core_open_notional` could go negative if multiple exits race | Single-threaded slow path means no race. But assert non-negative after each subtraction for sanity |

### Things the plan was missing — now integrated below

1. **Hot reload integration** for `risk_pct` / `core_N_risk_pct`
   changes. Today `allocated_balance` is set in `EngineSharded_Run`
   once. ControllerConfig hot reload needs to also call
   `EventLoopState_SetCoreStrategy` (or a subset) to update
   `allocated_balance` per core. → integrated into Phase 2.1.
2. **Reset Paper** needs to zero new per-core counters. Find the
   reset path and add the new fields. → integrated into Phase 2.1
   and Phase 3.
3. **Cfg keys** for the new tunables:
   - `core_N_max_drawdown_pct` (per-core override) → Phase 3
   - `min_kill_loss` (absolute-loss floor for kill switch) → Phase 3
   - `enable_mtm_kill_switch` (default 1; can disable for realized-
     only behavior) → Phase 3
4. **GUI display formatting** for "Budget Used %":
   `core_open_notional / allocated_balance × 100`. Color: green
   <50%, yellow 50-90%, red >90%. → Phase 2.1.
5. **Kill switch state in PerCoreSnap**: `core_kill_tripped`,
   `core_dd_pct` (current drawdown), `core_peak_balance`.
   Risk panel reads these. → Phase 3.

### Why MTM lives on the slow path (not hot path)

Kill switch's contract: "**stop opening new positions** when this
core has bled X%." Not emergency-close — SL handles that on the hot
path already.

If MTM ran on hot path:
- ~5ns + atomic flag load every tick
- Output is "should slow path block entries on next rebuild?"
- Slow path is the only thing that builds entries — it can answer
  this itself. Hot path's job is gate evaluation, not strategy
  decisions.

Slow-path MTM is the right architectural fit:
- SL fires fast (hot path, ns response) — handles the bleeding trade
- MTM on next slow-path cycle (~few seconds) — sees realized loss +
  unrealized + decides if kill trip is warranted
- Kill blocks future entries, existing positions ride to SL/TP

**Future variant:** if "force-close on kill trip" ever becomes
desired (panic exit on trip), THAT becomes a hot-path concern (kill
trip → emit exit event). Defer until evidence demands it.

### Aggregate kill switch parity (bonus)

The existing OMS-level breaker (`ks_max_drawdown_pct`, `ks_peak_balance`)
is realized-only — same gap MTM solves at per-core level. **While we
add MTM to per-core kill, generalize the helper so the aggregate
breaker can use it too.** Single commit, both improved.

### Notify alerts

Per Phase 8b doctrine: every alertable event gets an `NK_*` kind +
`Notify_Send` call. New kinds needed:
- `NK_CORE_KILL_TRIP` — per-core kill switch trip (level: ALERT)
- `NK_CORE_BUDGET_EXHAUST` — repeated HALT_CORE_BUDGET (level: WARN,
  with cooldown so a runaway core doesn't spam)

Aggregate breaker already has `NK_KILL_SWITCH`; keep it.

### Dependencies between phases

- **Phase 2.1 → 2.2** — enforcement needs the counter to clamp
  against. Ship 2.1 first, watch numbers, then 2.2.
- **Phase 2.2 → Phase 3** — kill switch should be aware of budget
  state (a kill-tripped core can't trade anyway). Order is fine but
  not strictly enforced.
- **Phase 3 → Phase 3.5** — Risk panel needs kill state to display.
- **Phase 3.5 → Phase 4** — persistence saves kill state. Ship Risk
  panel first so we can verify state is correct before serializing.

---

## Phase 1 — Display polish (deferred per Jenn priority)

Polish work. Skip for now; revisit after architecture is honest.

- 1.1 Stats panel per-core breakdown
- 1.2 Positions panel core_id column
- 1.3 Trade History core filter
- 1.4 Stale TUISnapshot field rename

---

## Phase 0 — Legacy live-trading safety parity (2-3 days, blocks live use)

**Discovered late in review.** Three live-trading safety features
exist in legacy `main.cpp` but never got ported to sharded
(`EngineSharded_Run`). All three matter for "crash → restart" or
"manual Binance interaction" scenarios. Should be done BEFORE Phase
2/3 because they're a real risk gap for any live use today.

### 0.1 Orphan BTC detection + recovery on startup
- **Legacy:** main.cpp:315 — on live boot, queries Binance for BTC
  balance; if non-zero and not matched by paper portfolio, sells to
  recover USDT.
- **Sharded gap:** EngineSharded_Run doesn't query Binance balance
  on startup. Restart after crash with leftover BTC = silent orphan.
- **Implementation:** add to EngineSharded_Run init phase, after
  exchange adapter is ready, before tick processing starts. Mirror
  legacy's pattern exactly (it's well-tested).

### 0.2 Force-close on shutdown
- **Legacy:** main.cpp:56-101 — on quit signal, refuses exit if
  `ctrl.portfolio.active_bitmap != 0`. Sells positions first.
- **Sharded gap:** sharded shutdown sequence doesn't enforce this.
  Could exit with open Binance positions.
- **Implementation:** in EngineSharded_Run shutdown sequence, walk
  per-core portfolio slots, emit market exit for each open position,
  wait for confirmations (with timeout) before final exit.

### 0.3 External trade detection
- **Legacy:** main.cpp:894-921 — periodically reconciles Binance
  balance/positions against paper portfolio. Detects manual trades
  outside the engine; sells orphans found.
- **Sharded gap:** sharded does not reconcile periodically. Manual
  trade on Binance during an engine session = paper drift.
- **Implementation:** slow-path background reconciliation. Compare
  Binance balance ± expected delta against `oms->balance + open
  notional`. On mismatch, log + alert + (configurable) auto-correct.

### Tests

- Manual smoke: start sharded with orphan BTC → verify recovery
- Manual smoke: ctrl-C with open position → verify it's closed before
  exit
- Manual smoke: open position, manually sell on Binance, watch
  reconciliation fire

### Risk

- Medium. Touches live API during boot/shutdown. Test in paper
  mode first; live testing requires real Binance API key.
- Critical to keep paper-mode no-op for these (don't query Binance
  if `live_trading == 0`).

---

---

## Phase 2.1 — Instrument core_open_notional (1 day)

### Implementation

1. **CoreContext field:**
   ```cpp
   FPN<F> core_open_notional;  // sum of entry_price × qty for open positions
   ```
   Init to `FPN_Zero<F>()` in EventLoopState_Init.

2. **EventLoop_OnEvent entry branch** (after `Portfolio_OpenSlot`):
   ```cpp
   FPN<F> notional = FPN_Mul(event.price, ctx->intended_qty);
   ctx->core_open_notional = FPN_Add(ctx->core_open_notional, notional);
   ```

3. **EventLoop_OnEvent exit branch** (using existing snapshot):
   ```cpp
   // entry_price_snap, qty_snap already captured before CloseSlot
   FPN<F> entry_notional_snap = FPN_Mul(entry_price_snap, qty_snap);
   ctx->core_open_notional = FPN_SubSat(ctx->core_open_notional,
                                         entry_notional_snap);
   ```
   `FPN_SubSat` (saturating subtract) prevents underflow if state
   is somehow inconsistent.

4. **PerCoreSnap fields:**
   ```cpp
   double core_open_notional;
   double core_budget_used_pct;  // open_notional / allocated × 100
   ```

5. **ShardedSnapshot population:** simple FPN_ToDouble.

6. **Account panel:** replace "Open" column with "Budget Used" —
   show "% used" with color coding. Tooltip shows raw notional vs
   allocation.

### Tests

- New group `Phase 2.1: notional accounting`:
  - Open one position → notional matches expected
  - Close it → notional returns to exactly zero
  - **Hammer test**: open + close 100 times, varied entry/exit
    prices (winners + losers) → notional still exactly zero, no
    drift. This is the symmetry-bug detector.
  - Multi-core: each core tracks independently
  - Underflow safety: artificially set core_open_notional to 0,
    fire exit → no underflow (FPN_SubSat saturates)

### Hot reload integration

Today `allocated_balance` is set ONCE in `EngineSharded_Run` and
never updated. Hot reload of `risk_pct` or `core_N_risk_pct` is
silently stale. Fix in this phase:

- In hot-reload path (wherever `Settings_Save` triggers reload):
  recompute `allocated_balance` for each core using the same
  formula as startup (`total_balance × risk_pct / num_cores`, or
  `total_balance × core_N_risk_pct` if override set).
- Critical: do NOT also reset `core_open_notional` on hot reload
  — open positions still exist. The new allocation either
  expands or shrinks the budget; the open notional is unchanged.

### Reset Paper integration

Find the existing Reset Paper handler (zeroes `oms->balance`,
`portfolio.active_bitmap`, etc.). Add zeroing of new per-core
fields:
- `core_open_notional = FPN_Zero<F>()`
- (Phase 3+) `core_peak_balance`, `core_kill_tripped`,
  `core_ks_trips_total`, `core_realized`, `core_fees`,
  `core_wins`, `core_losses` — all reset to fresh state

### Risk

- Low. Instrumentation only, no enforcement, no quantity changes.
- Symmetry bug (entry vs exit notional) would show up immediately
  in the Budget Used % drift on the GUI — and the hammer test
  catches it before it ships.
- Hot reload bug would show up as "I changed risk_pct in cfg, the
  Account panel didn't update" — easy to verify manually.

---

## Phase 2.2 — Enforce sizing clamp (1-2 days)

### Implementation

1. **In every Strategy_*_BuildParameters**, after `trade_size`
   computed, before write to out:
   ```cpp
   // Phase 2.2: clamp against remaining per-core budget
   FPN<F> budget_remaining = FPN_SubSat(allocated_balance, core_open_notional);
   FPN<F> max_qty = FPN_Zero<F>();
   if (!FPN_IsZero(expected_entry)) {
       max_qty = FPN_DivNoAssert(budget_remaining, expected_entry);
   }
   trade_size = FPN_Min(trade_size, max_qty);
   ```
   Note: `core_open_notional` is per-core state, not currently
   accessible from `_BuildParameters` (which gets `allocated_balance`
   directly). Need to thread it through:
   ```cpp
   FPN<F> Strategy_BuildParameters(..., FPN<F> allocated_balance,
                                    FPN<F> core_open_notional, ...);
   ```
   Update all call sites in `EventLoop_RebuildAllParameters`.

2. **Halt reason:** add `HALT_CORE_BUDGET = 8` (next available).
   Set when `budget_remaining <= 0` AND a strategy wanted to enter.
   Zero-gate via existing mask pattern.

3. **Snapshot:** halt_reason already plumbed; just add to display
   in Buy Gate panel halt-reason text.

### Tests

- `Phase 2.2: per-core budget enforcement`:
  - Single core with full budget → unclamped qty
  - Single core with one position open → second entry clamped to remaining
  - Single core with budget exhausted → halt fires with HALT_CORE_BUDGET
  - Multi-core: core 0 at-budget, core 1 still trades freely
  - Per-core override: core_N_risk_pct=20.0 sets allocation correctly

### Risk

- Medium. Touches sizing — but every strategy already has the same
  sizing pattern; the clamp is a uniform addition.
- Sweep existing tests for "asserts exact qty against full allocation."

---

## Phase 3 — Per-core kill switch with MTM (3-4 days)

### Implementation

1. **CoreContext fields:**
   ```cpp
   FPN<F> core_peak_balance;       // max of (allocated + realized + unrealized)
   FPN<F> core_dd_pct;             // current drawdown (display only, recomputed)
   uint8_t core_kill_tripped;      // 1 = halted by per-core kill switch
   uint32_t core_ks_trips_total;   // historical trip count
   ```

2. **MTM compute on slow path** (in `EventLoop_RebuildAllParameters`,
   per core):
   ```cpp
   FPN<F> unrealized = FPN_Zero<F>();
   for (int slot = 0; slot < MAX_POSITIONS_PER_CORE; ++slot) {
       if (!Portfolio_IsActive(&oms->portfolio, slot)) continue;
       Position<F>* p = &oms->portfolio.positions[slot];
       FPN<F> diff = FPN_Sub(current_price, p->entry_price);
       unrealized = FPN_Add(unrealized, FPN_Mul(diff, p->quantity));
   }
   FPN<F> current_value = FPN_Add(allocated_balance,
                                    FPN_Add(core_realized, unrealized));
   ctx->core_peak_balance = FPN_Max(ctx->core_peak_balance, current_value);
   ```

3. **DD evaluation:**
   ```cpp
   if (FPN_GreaterThan(core_peak_balance, FPN_Zero<F>())) {
       FPN<F> drop = FPN_Sub(core_peak_balance, current_value);
       ctx->core_dd_pct = FPN_DivNoAssert(drop, core_peak_balance);
       // trip if dd exceeds threshold AND drop exceeds min_kill_loss floor
       FPN<F> threshold = ctx->core_max_dd_pct;  // from cfg
       if (FPN_GreaterThan(ctx->core_dd_pct, threshold) &&
           FPN_GreaterThan(drop, cfg->min_kill_loss)) {
           ctx->core_kill_tripped = 1;
           ctx->core_ks_trips_total++;
           Notify_Send(NOTIFY_ALERT, NK_CORE_KILL, ...);
       }
   }
   ```

4. **Halt on entry build:** zero-gate when `core_kill_tripped == 1`.
   New halt reason `HALT_CORE_KILL = 9`.

5. **Manual reset:** `TUISharedState::kill_reset_per_core[16]`
   array. Slow path checks each frame, on reset:
   ```cpp
   ctx->core_kill_tripped = 0;
   ctx->core_peak_balance = current_value;  // fresh start
   ```

6. **Cfg keys:**
   - `core_N_max_drawdown_pct` (override global `ks_max_drawdown_pct`)
   - `min_kill_loss` (default $5 — prevent trips from rounding noise)

### Tests

- `Phase 3: per-core kill switch`:
  - Peak tracks max of (alloc + realized + unrealized)
  - DD computation with realized + unrealized
  - Trip fires at exact threshold + min_kill_loss floor
  - Trip below threshold doesn't fire
  - Halt zero-gates entries when tripped
  - Manual reset clears trip + restores peak to current
  - Multi-core: one tripped, others trade
  - Aggregate breaker still trips on whole-account loss

### Risk

- Medium-high. Numeric edge cases (peak update timing, dd calc
  when allocation tiny). Test coverage critical.
- MTM adds slow-path work proportional to open positions × cores.
  Bounded ≤ 16 × 16 = 256 iterations per slow path. Negligible.

---

## Phase 3.5 — Risk panel (1 day)

### Implementation

New panel `GUI_Panel_Risk` in DashboardPanels.hpp. Per-core row:
- Core | Strat | Peak | Current | DD% | Status (OK / KILLED) | [Reset]

Reset button writes to `shared->kill_reset_per_core[i] = 1`.

Future-extensible: add Manual Halt, Force Close Position, etc.

### Risk

- Low. Pure GUI. Wires to existing per-core state via snapshot.

---

## Phase 4 — Sharded persistence (2-3 days)

### Implementation

New file `CoreFrameworks/ShardedSnapshotPersist.hpp`:

1. **Magic + version:** `0xSHA0001` magic, `SHARDED_SNAPSHOT_VERSION = 1`.

2. **Refuse legacy:** if magic == `PORTFOLIO_SNAPSHOT_MAGIC`, log
   warning + skip load.

3. **Save on shutdown** (signal handler) and **periodic** (every
   N slow-path cycles, atomic rename pattern).

4. **Per-core block** for each registered core:
   - regime_state (current_regime + candidate_regime + hysteresis_count)
   - pnl_feeder rolling buffer + sum + count
   - core_realized / core_fees / core_wins / core_losses
   - core_open_notional
   - core_peak_balance / core_kill_tripped / core_ks_trips_total
   - allocated_balance (so cfg risk_pct change post-restart is detectable)
   - last_entry_price / last_entry_tick (spacing state)

5. **Global block:**
   - oms->balance / realized_pnl / fees totals
   - portfolio bitmap + positions
   - session stats

6. **num_cores stored in header.** On load, if mismatch:
   - Loading more cores than configured → ignore extra cores (warn)
   - Loading fewer cores than configured → init missing cores
     fresh, load existing ones (warn)

### Tests

- `Phase 4: sharded persistence`:
  - Round-trip: save → load → state matches byte-for-byte (modulo
    timestamps if any)
  - Refuse legacy v11 magic
  - Refuse bad checksum
  - num_cores mismatch handled gracefully
  - Half-written file (truncated mid-write) doesn't crash load
  - Atomic rename actually atomic (mid-save crash leaves old file
    intact)

### Risk

- Low. Pure I/O. Well-isolated.

---

## Out of scope / explicit non-goals

- ANSI TUI display reworks
- Per-core data streams
- Per-core charts (single chart with overlays is fine)
- Backtest sharding
- Per-file trade log split (CSV tags core_id already)
- Hard-isolated per-core balance pools (Option A — fights reality)

---

## Suggested release plan

- **v4.0.5** — Phase 2.1 instrumentation only (low risk, ship early)
- **v4.1.0** — Phase 2.2 enforcement (semantics change, minor bump)
- **v4.1.1** — Phase 3 kill switch + 3.5 Risk panel
- **v4.2.0** — Phase 4 persistence (new feature, minor bump)

Tag rollback before each: `pre-v4.0.5`, `pre-v4.1.0`, etc.
