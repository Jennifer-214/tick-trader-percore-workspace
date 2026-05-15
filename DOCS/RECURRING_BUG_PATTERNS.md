# Recurring bug patterns

The complement to `tests/INVARIANTS_MAP.md`. That doc tracks
**positive** invariants ("X must hold true"); this doc tracks
**negative** patterns ("this class of bug keeps showing up — here's
the detection signature, here's where it bites").

Each pattern has:
- **Class N** identifier — stable, referenced from postmortems
- **Symptom** — what the user sees
- **Root cause** — why it happens
- **Detection** — exact grep / script to find new instances
- **Known instances** — file:line of past occurrences + commit that fixed
- **Prevention** — what to add to readiness/dust skills or to tests

When a new instance is found, add it under "Known instances" with
the fix commit. When a new class emerges (>2 fixes of the same
shape), add a new Class entry.

Read this doc before any architectural sprint, especially anything
that mentions "split", "shard", "decouple", "extract", "centralize",
or "per-core". Run each Class's detection script as a pre-coding
gate.

---

## Class 1 — Strategy lifecycle orphans

**Surface:** live (engine slow-path strategy dispatch).

**Symptom:** strategy adaptive behavior (regression-driven filter
tightening, trailing SL ratchet, regime-driven retune) silently
absent. Strategies "appear to work" because their entry gate fires,
but everything past entry behaves like a dumb cfg-static strategy.

**Root cause:** sharded port wired the entry point
(`Strategy_BuildParameters` dispatcher) but never plumbed the rest of
the lifecycle (`_Init`, `_Adapt`, `_BuySignal`, `_ExitAdjust`,
`Regime_AdjustPositions`). State structs (`MomentumState` etc.) were
defined but never allocated per-core; legacy callers were the only
ones invoking them.

**Detection:**
```bash
# Find functions called in legacy PortfolioController but not in the
# sharded entry points
tools/calls_graph_diff.sh
```
Functions with zero call sites in `engine_sharded` / `controller_event_loop`
but present in `portfolio_controller` are candidate orphans.

**Known instances:**
- v5.4.0 — all 5 strategies' `_Init`/`_Adapt`/`_ExitAdjust`/`_BuySignal`
  were orphaned. Fixed in commits `ad4fbb7..6049fa5` (Phase 1-2.5).

**Prevention:**
- Readiness skill Check 13 (strategy lifecycle completeness) — load
  before any plan touching strategies.
- `DOCS/STRATEGY_INTERFACE.md` — canonical 5-stage doc.
- `tools/calls_graph_diff.sh` — run as pre-merge gate when sharding
  any subsystem.

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

---

## Class 3 — Drain count under partials

**Surface:** drainer (OMS drainer + partial fill consumption).

**Symptom:** Cores beyond `num_cores` under partials silently never
trade. Submit commands stranded in queues forever.

**Root cause:** `OMS_PushSubmit` keys `submit_queues[]` by
`portfolio_slot` (0..2N-1 under partials, where N=num_cores). But
`OMS_DrainSubmit(num_cores=N)` iterates queues 0..N-1. Mismatch.
Confused by the `core_id` parameter name on `OMS_PushSubmit` —
under partials it's actually carrying the portfolio slot, not the
core index.

**Detection:**
```bash
grep -rn "OMS_DrainSubmit\b" CoreFrameworks/ | \
    grep -v "* 2\|partial_exit"
# Any caller passing num_cores without the *2 multiplier under
# partials is a candidate.
```

**Known instances:**
- v5.4.1 — `EngineSharded.hpp:1842` and `ShardedBacktestDriver.hpp:208`
  drained N queues, missed N..2N-1. Fixed in `f82d94f`. Regression
  test at `controller_test.cpp` v5.4.1.B2.

**Prevention:**
- Naming smell: `OMS_PushSubmit`'s `core_id` parameter is misnamed.
  Future refactor should rename to `slot_id` and add a static_assert
  that `submit_queues[]` is sized for `MAX_PORTFOLIO_POSITIONS`,
  not `MAX_EXECUTION_CORES`.

---

## Class 4 — Snapshot save/load asymmetry

**Surface:** boot (snapshot serialization on shutdown + load on startup).

**Symptom:** Per-core stats reset on engine restart even though the
file exists and the user expected continuity. Stats panel shows
zero W/L until the next post-restart trade.

**Root cause:** Field added to `CoreContext` in vN.M after the
snapshot save/load was authored. Save was updated, load was forgotten
(or vice versa). The save-only fields silently get truncated on next
load; the load-only fields read garbage from disk past the saved
extent.

**Detection:**
```bash
# Save-side fields
grep -oE "fwrite\(&ctx\.[a-z_]+" ShardedSnapshotPersist.hpp | sort -u
# Load-side fields
grep -oE "fread\(&s\.[a-z_]+" ShardedSnapshotPersist.hpp | sort -u
# Any imbalance is suspect
```

**Known instances:**
- v5.4.3 (this commit) — `core_gross_wins` and `core_gross_losses`
  added in v4.7.25 but never persisted. After restart, Stats panel's
  avg_win / avg_loss / profit_factor / expectancy all read zero
  until next trade.
- v5.4.3 — `idle_cycles` (death-spiral counter) not persisted.

**Prevention:**
- Bump `SHARDED_SNAPSHOT_VERSION` whenever a CoreContext field is
  added that needs persistence.
- Readiness check: when a plan adds a `CoreContext<F>` field, require
  explicit answer to "should this be persisted?" — yes/no/deferred,
  no implicit "no answer."

---

## Class 5 — Reset Paper completeness

**Surface:** boot (reset action — must clear all state, not just visible state).

**Symptom:** Click "Reset Paper", expect blank slate, but the next
trade exhibits subtle stale behavior — entry blocked by stale
cooldown, adaptive feedback contaminated by pre-reset state, etc.

**Root cause:** Reset handler in `EngineSharded.hpp` zeroes balance,
realized_pnl, and a hand-curated list of per-core fields. New fields
added to CoreContext after the handler was written are silently
NOT zeroed. Reset becomes "mostly fresh" instead of fully fresh.

**Detection:**
```bash
# Compare CoreContext field declarations with what reset zeros
grep -oE "FPN<F>\s+[a-z_]+|uint[0-9]+_t\s+[a-z_]+" \
    CoreFrameworks/ControllerEventLoop.hpp | head -100
# Then find what's reset
grep -A40 "paper_reset_in_progress" CoreFrameworks/EngineSharded.hpp
```

**Known instances:**
- v5.4.3 — `sl_cooldown_remaining` not reset. Post-reset, a core
  with prior SL exit stays zero-gated for sl_cooldown_cycles ticks
  (no UI indicator).
- v5.4.3 — `idle_cycles` not reset. Death-spiral pnl_feeder reset
  threshold not fresh after reset.
- Pre-fix history: v4.7.26 had to add `partner_pending_pnl /
  partner_pending_active / core_gross_wins / core_gross_losses`
  resets after similar issues — recurring class.

**Prevention:**
- Reset handler should iterate via X-macro or struct-zero-clear
  pattern to avoid drift. Adding a field shouldn't require remembering
  to also touch the reset handler.
- Test: after Reset Paper, every CoreContext field should equal its
  Init-time default. Simple property test catches future regressions.

---

## Class 6 — OMS counter persistence

**Surface:** boot (snapshot save/load of OMS state — counters must round-trip).

**Symptom:** session-cumulative counters on the OMS (fee totals,
maker/taker breakdown, fill counts) reset to zero on engine restart
even though `balance` and `realized_pnl` continue from the snapshot.
After restart, the GUI's fees tooltip / session forensics drop the
session totals and the user can't reconcile cumulative spend.

**Root cause:** `ShardedSnapshotPersist.hpp` save/load was authored
for the financial-state primitives (balance, realized_pnl, peak,
kill_switch_tripped) and never expanded as the OMS grew counter
fields. Maker/taker / fee-totals were added in Phase 8; never
propagated into the snapshot file.

**Detection:**
```bash
# Fields on OMS struct that look like cumulative counters
grep -E "uint(32|64)_t|FPN<F>" CoreFrameworks/OrderManager.hpp \
    | grep -iE "total|count|fee|fill" | head -20
# What's actually persisted
grep "fwrite(&state->oms->" CoreFrameworks/ShardedSnapshotPersist.hpp
# Diff: counters that exist but aren't written are candidates
```

**Known instances:**
- v5.4.4 — `total_fees`, `total_maker_fees`, `total_taker_fees`,
  `maker_fills_count`, `taker_fills_count` not persisted. Snapshot
  version bumped 5→6.

**Prevention:**
- Same as Class 4: bump SHARDED_SNAPSHOT_VERSION when adding any OMS
  counter that needs continuity, with a save/load symmetry check.
- Future refactor: snapshot save/load should iterate fields from a
  schema struct rather than open-coded fwrite/fread. A schema
  mismatch then becomes a static_assert at compile time.

---

## Class 7 — Threading topology violations (audited clean post-v5.4.x)

**Surface:** audited-clean (per-core SoA topology + atomic-or-per-core mutating state).

**Detection:** [audited-clean — N/A; durable validation is `./build.sh tsan` clean run]

**Symptom:** would manifest as data races on per-core fields under
TSan stress. Pre-fixes in v4.7.x already converted shared mutating
state to per-core or atomic. Round 2 audit (2026-04-30) flagged two
candidate violations; both turned out to be false alarms:

1. `EventLoop_QueueParameters` writes `pending_params` from producer
   while per-core thread also writes — flagged. Verification: the
   function is only called by an experiment test, never in the live
   drainer or per-core slow path. False alarm.

2. `OnEvent` writes `ctx->idle_cycles = 0` from drainer while
   per-core thread increments it — flagged. Verification: `OnEvent`
   in mode 1 (default since v4.7.x) early-returns at line 1083
   before reaching the increment. The write is unreachable in
   production. Classified as inert dead code; cleanup can fold it
   into the mode-0 legacy block (low priority).

**Prevention:**
- `./build.sh tsan` clean run on `engine` synthetic mode is the
  durable validation. v5.0.5 confirmed clean; rerun before any
  new threading work.
- Future audits: distinguish "field written by multiple threads" from
  "fields written by multiple threads at the same time" — many
  per-core fields appear to have multiple writers but the writes are
  serialized by mode/cadence/topology gating.

---

## Class 8 — User-configurable features silently inactive in sharded

**Surface:** live (cfg-flag → runtime decision-path consumption).

**Symptom:** user flips a cfg flag, expects behavior change, sees
none. TUI may even display "enabled" status. The cfg field is parsed,
stored, displayed — but the runtime decision path that should consume
it doesn't exist in the sharded code, only in the legacy
PortfolioController.

**Root cause:** the sharded port migrated the structural execution
path (slow-path → strategy → gate parameters → hot path) but did not
port every modulator / gating layer. Cost gating (CostModel) and vol
scaling (VolScaler) were two such layers — fully implemented in
legacy, fully orphaned in sharded.

**Detection:**
```bash
# For each cfg field that's marked "enabled" or has explicit gating
# semantics, check if it's read in the sharded path
for field in $(grep -oE "[a-z_]+_enabled" CoreFrameworks/ControllerConfig.hpp | sort -u); do
    legacy_reads=$(grep -c "config.$field\|cfg.$field" CoreFrameworks/PortfolioController.hpp 2>/dev/null)
    sharded_reads=$(grep -rh "config.$field\|cfg.$field" \
        CoreFrameworks/EngineSharded.hpp \
        CoreFrameworks/ControllerEventLoop.hpp \
        Strategies/ 2>/dev/null | wc -l)
    if [ $legacy_reads -gt 0 ] && [ $sharded_reads -eq 0 ]; then
        echo "ORPHAN: $field (legacy=$legacy_reads, sharded=0)"
    fi
done
```

**Known instances:**
- v5.4.4 (DOCUMENTED, NOT YET FIXED) —
  - `cost_gate_enabled`: legacy reads at PortfolioController.hpp:1751.
    Sharded zero reads. CostModel evaluates expected cost vs
    expected gain at entry; if `cost > k × gain`, vetoes the entry.
    Sharded skip means cost-aware entry filtering is dead.
  - `foxml_vol_scaling_enabled`: legacy reads at
    PortfolioController.hpp:1168, 1789. Sharded zero reads. Scales
    risk_pct by recent volatility (cuts size in high-vol regimes).
    Sharded skip means user's risk_pct is constant regardless of
    volatility.

**Prevention:**
- Readiness skill check: when a plan touches an `*_enabled` cfg
  field, require explicit "where is this consumed" answer for both
  legacy AND sharded paths. Block ship if sharded path is empty.
- Dust scan: extend Scan 9 (orphaned function detection) to also
  scan for orphaned cfg-enabled fields.
- Long-term fix: port CostModel + VolScaler integration into the
  sharded `Strategy_BuildParameters` dispatcher path. Tracked as a
  v5.5+ feature ship.

---

## Class 9 — Shutdown blocking on operations the user didn't want

**Surface:** boot (shutdown ordering + cancellation propagation).

**Symptom:** Ctrl+C / window-close hangs the terminal for tens of
seconds (or indefinitely). User can't tell if the engine is dead or
working. Process appears stuck.

**Root cause:** A "graceful" cleanup step on the shutdown path is
trying to do something the user didn't ask for — flatten positions
to zero, close exchange orders, drain queues to empty — and is
blocking the join sequence waiting for that work to complete.

**Detection:**
```bash
# Functions called between SIGINT delivery and pthread_join in the
# shutdown sequence
grep -n -A2 "shutdown requested\|joining threads" CoreFrameworks/EngineSharded.hpp
# Anything between the signal-flag check and the first thread join
# is a candidate hang point.
```

**Known instances:**
- v5.4.5 — `EngineSharded_ForceCloseOnShutdown` blocked the join
  sequence for up to 30s while submitting market SELLs and waiting
  for fills. User intent was "positions persist across restart"
  (engine runs 24/7), not "flatten on exit." Fixed: replaced the
  force-close call with a single warning log; positions persist via
  snapshot. Force-close logic preserved in codebase for callers that
  explicitly want it.

**Prevention:**
- Shutdown path sequence should be: (1) save state, (2) join threads,
  (3) close files. Do NOT introduce blocking work between (1) and (2)
  without an explicit cfg gate. If you add a "graceful X" step, give
  it a `cfg.X_on_shutdown` toggle defaulting to off.
- Test: shutdown with N open positions completes within S seconds
  (S < 5). Property test catches future regressions.

---

## Class 10 — Strategy-regime mismatch

**Surface:** live (regime classifier → strategy dispatch coupling).

**Symptom:** A strategy fires entries in regimes where its
contract doesn't make sense (e.g. MOM buying breakouts in RANGING
markets where every breakout reverts), accumulating fee-only losing
trades.

**Root causes (any of):**
1. Hardcoded strategy assignment (`core_N_strategy=momentum`) —
   strategy fires regardless of regime classification.
2. Regime hysteresis flicker — classifier briefly flips to TRENDING
   during noise, AUTO core enters MOM, classifier returns to
   RANGING, position sits at fees-only loss.
3. Classifier-threshold mis-tuning — classifier decides TRENDING in
   actually-ranging markets.
4. Strategy filter too loose — strategy's BuySignal accepts
   marginal entries that can't survive fees + slippage.

**Detection:**
```bash
# Per-strategy x per-regime quality breakdown from health.jsonl
jq -s 'group_by(.cat=="entry") | .[] | select(.[0].cat=="entry") |
  group_by(.msg | capture("strat=(?<s>[0-9]+) regime=(?<r>[0-9]+)").s + ":" + .r) |
  map({key: .[0].msg, count: length})' health.jsonl
# Look for cells where MOM has many entries in regime=0 (RANGING)
# with negative net bps in the matching exits.

# Or use the v5.7.6 GUI Strategy Quality panel — same data via Refresh.
```

**Known instances:**
- v5.7.0 — 2026-04-30 paper run: Core 0 hardcoded MOM entered in
  RANGING regimes, took 16+ near-flat trades that lost fees only.
  Audit (`DOCS/changelogs/2026-04-30-regime-classifier-audit.md`)
  confirmed the regime classifier itself was healthy — Core 0's
  hardcoded assignment bypassed regime gating entirely.

**Prevention:**
- v5.7.2 — boot guard refuses live mode with hardcoded strategies
  unless `acknowledge_hardcoded_strategy_in_live=1` is set explicitly.
  Paper mode warns. Boot abort path emits health log
  `cat="engine"` `boot_abort` line.
- v5.7.5 — MOM-specific quality filters
  (`momentum_min_tp_margin_pct`, `momentum_min_r2`,
  `momentum_min_buy_delta_recent`) gated cfg-side. Default off
  preserves pre-v5.7 behavior; operator opts in after observing
  v5.7.6 quality dashboard data.
- v5.7.6 — per-strategy quality dashboard panel surfaces the
  pattern at-a-glance: any strategy showing many entries in a
  "wrong" regime with negative net bps is the smoking gun.

## Class 11 — Extensibility friction causing silent drift

**Surface:** live (multi-site addition pattern — N sites must agree; X-macro registry pattern is the structural fix).

**Symptom:** A category that supports extension (codes, metrics,
panels, etc.) is implemented at multiple call sites without a
canonical spec. Each site evolves independently. Eventually two
sites disagree: same input, different output. Operator-visible
behavior diverges from operator-expected behavior; sometimes the
divergence affects evaluation logic (optimizer rankings, drift
detection, walk-forward gap thresholds) — making the entire
selection mechanism unreliable.

This class is distinct from Class 1 (lifecycle orphans — code
ABSENT) and Class 2 (display vs execution divergence across
layers — code in the WRONG LAYER). Class 11 is code IN MULTIPLE
PLACES that should agree but doesn't.

**Root cause:** Adding the first instance of a category is fine.
Adding the second copy-pastes the formula. By the third or fourth
site, the formula has been retyped slightly differently. There's
no single source of truth, so no test fails — both sides "look
reasonable in isolation."

**Detection:**
```bash
# Grep the formula's identifying token across the whole codebase.
# E.g. for "profit_factor", search for the divisor pattern.
grep -rnE "(profit_factor|gross_wins.*gross_losses)" --include="*.hpp" .
# Eyeball the matches: do all sites use the same epsilon? Same
# fabs? Same sentinel? If not, you've found a Class 11 instance.

# Variant per-category: search for any "X_names[]" or "X_table[]"
# array hand-maintained in parallel with an enum:
grep -rnE "static const char\* \w+_names\[\]" --include="*.hpp" .
# Mirror arrays are Class 11 in waiting.
```

**Known instances:**
- v5.6.0 — Controller `halt_reason = 10` (book-imbalance) was added
  in `ControllerEventLoop.hpp` but `halt_names[]` mirror in
  `GUI/DashboardPanels.hpp` had only indices 0-9. The display
  silently dropped the imbalance reason — operator saw "halted"
  with no reason text. Fix: the bound check made imbalance
  display work; the structural fix didn't land until v5.8.3.
- v5.8.3 (preventive) — converted `halt_reason` raw integers to
  `HALT_*` named constants via `FOREACH_HALT_REASON(X)`. Mirror
  retired; `HALT_NAMES` is the registry-driven single source.
  Found 8 indirect raw-int sites via `zero_gate(N)` lambda calls
  that the original plan had missed.
- v5.8.4c — `profit_factor` had 4 different formulas across 4
  sites: `(gl > 0.0001)`, `(gl > 0.001)`, no guard, and
  `(gl > 0.001)` with `-1.0` sentinel. The `-1.0` sentinel was
  packed into `profit_factor` itself and read by
  `OPT_METRIC_PF` — the walk-forward optimizer ranked
  perfect-wins runs LOWER than mediocre ones. Fix: canonical
  `Compute_ProfitFactor` returns `0.0` for no-losses; new
  `all_wins_run` flag handles distinct display.
- v5.8.4c — `expectancy` used `fabs(avg_loss)` in BacktestEngine
  but not in EngineTUI/ShardedSnapshot. Harmless when invariant
  held; defensive against future sign-flip. Fix: canonical
  `Compute_Expectancy` keeps `fabs`.
- v5.8.4c — `max_drawdown` had two independent implementations
  (post-hoc walk in `BacktestEngine` vs incremental per-tick in
  `BacktestSharded`). Formal equivalence ≠ bytewise FP
  equivalence. Fix: shared `MaxDrawdown_UpdateIncremental`
  helper called from both paths — bytewise identical by
  construction.

**Prevention:**
- **X-macro registry pattern.** Every "category that supports
  extension" should have a `FOREACH_<CATEGORY>(X)` registry +
  auto-generated arrays + `static_assert` size parity. See
  `DOCS/EASY_ADDITIONS_INVARIANTS.md` for the canonical spec.
- **Single-helper pattern for shared formulas.** When a metric or
  computation is needed at two cadences (post-hoc + incremental,
  backtest + live), extract a single inner-update helper that
  both paths call. Bytewise FP identity is structural, not test-
  validated.
- **Display vs math separation.** When a metric needs distinct
  display semantics (e.g. "all wins" → "∞"), use a separate flag
  rather than a sentinel value packed into the metric itself.
  Sentinel values get read by downstream consumers (optimizers,
  comparison logic) and silently corrupt rankings.
- **Readiness deep-audit before any phase that adds an extensibility
  point.** The v5.8.4c drift findings only surfaced when the
  readiness skill specifically grepped for divergent formulas —
  flagging "Class 11 in waiting" before code was written.

**Adjacent**: see `DOCS/STRATEGY_REFACTOR_IDEAS.md` for the longer-
term observation that adding MORE strategies will increase the
chance of strategy-regime miscalibration. The X-macro refactor
proposed there would NOT fix this class — it just makes new
strategies easier to add. Class-10 prevention is regime-gating +
filters + observability, all already in place post-v5.7.

---

## Class 12 — Wired-but-unexercised ML paths (v5.9 sprint)

**Surface:** ml (ML pipeline — feature pack, model load, inference, fall-through paths).

**Detection:** [delegates to /ml-audit — that skill walks the ML pipeline structurally and surfaces wired-but-unexercised paths]

### Pattern

Code path is structurally present (compiles, links, included in
dispatcher) but no operator workflow actually exercises it. Symptom:
"the function exists, the test passes, but in real use the wiring
silently degrades or fall-through fires unobserved."

### Specific instances caught + fixed in v5.9

- **MLBuildContext fully populated in live sharded path** (v5.4.x
  postmortem). Live engine had model_handle wired but state pointers
  (ror_regressor, ema_price, etc.) were nullptr → ML_BuildParameters
  fell through to SimpleDip on every cycle, silently. Caught by
  reading `Strategy_BuildParameters` dispatch path against actual
  state-population code.

- **Features_PackAll output validation** (v5.9.0). PackAll produced
  NaN/Inf for degenerate features; `prediction = Model_Predict(NaN)`
  silently produced NaN; `prediction > threshold` evaluates false on
  NaN; entry never fired. No log, no alert. Fixed by NaN-guard at
  PackAll output + post-prediction NaN check.

- **ML→SimpleDip fall-through CRITICAL log** (v5.9.0b). Engine
  silently fell back to SimpleDip when ML model failed to load OR
  when feature pack returned NaN. Operator had no surface
  distinguishing "ML wasn't configured" vs "ML configured but
  silently failed." Fixed by per-core `model_load_failed` field +
  rate-limited CRITICAL log + ML Status panel surface.

- **Cfg explicit-set tracking** (v5.9.0c). `core_N_strategy=`
  silently fell through to default when absent from cfg. Operator
  thought they had configured 4 ML cores; engine ran 4 SimpleDip
  cores. No surface. Fixed by explicit-set bitmap on
  ControllerConfig + boot WARN when num_execution_cores>0 with
  bitmap=0 + Per-Core P&L tri-state marker.

- **Train-serve feature parity** (v5.9.2). Even with
  FEATURE_REGISTRY_HASH guarding the X-macro, function-body changes
  (e.g. fix sign error in `ML_Compute_VwapDev`) silently shifted
  output bytes. FEATURE_REGISTRY_HASH only catches X-macro
  structural changes; function-body changes pass it. Fixed by
  v5.9.2a snapshot tests asserting Features_PackAll output bytes
  match recorded values for known-input ctx.

- **Scaler load failure observability** (v5.9.3a, Gap H). v5.9.3
  added `.scaler` sidecar binding via stamp's `scaler_sha256`. In
  non-strict mode, sidecar missing or SHA-mismatch silently applied
  identity. Operator saw "model: loaded" with no indication scaler
  was bypassed. Fixed by `ml_scaler_load_failed` PerCoreSnap field
  + ML Status panel red-state row + rate-limited CRITICAL log.

### Prevention principle

"Wired but not exercised" gaps must be caught at PR-time
(regression test) or plan-time (readiness Checks 11-17), not
paper-test-time. Specifically:

- **Snapshot tests** (v5.9.2a) catch function-body changes that
  preserve X-macro structure but alter output bytes.
- **3-tier strict-mode behavior** (v5.9.3a): every train-serve
  handoff has refuse / warn-with-surface / silent-forbidden modes.
  Silent fallback is the bug class itself.
- **Distinct PerCoreSnap fields** for each failure mode
  (model_load_failed vs scaler_load_failed) prevent operator
  conflation of distinct silent failures.
- **Readiness skill Check 14** (v5.8 X-macro refactors): variant
  selection audit + signature uniformity + calls_graph_diff before
  AND after.

The v5.9 sprint shipped 11+ fixes addressing this class. Future
audits (`/ml-audit`, post-v5.9 `/parity-check`) should catch new
instances before they reach paper testing.

---

## Class 13 — Worker-thread struct extended without updating snap-capture-before-free block

**Surface:** training / GUI worker threads (`Backtest/BacktestPanels.hpp`).
Not on engine hot path; affects training output correctness.

**Symptom:** worker thread reads garbage values for newly-added
struct fields. Manifests as silent data corruption (wrong
label_kind written to stamp, wrong output dir, wrong cfg flags).
May not crash — undefined memory often returns plausible-looking
values (0, recently-freed-then-reused bytes). Tests pass when the
test harness doesn't exercise the GUI worker path. Operator only
notices in paper-test when stamps reject ("unknown label_kind") or
models save to the wrong directory.

**Root cause:** worker functions follow a discipline of copying
malloc'd `args->snap_*` fields to stack locals, then `free(args)`,
then operating on the locals (race-free + early-free for memory
hygiene). When a new field is added to the worker-args struct in
revision N+1, the field is populated by the click handler but the
worker's snap-capture block is NOT updated to copy it before
`free(args)`. Subsequent `args->new_field` reads dereference freed
memory.

A second flavor of the same class: the click handler ITSELF
doesn't populate the new field after malloc, so even if the worker
captured it correctly, it would capture uninitialized memory.

**Detection:**

```bash
# 1. Find every worker_fn that does free(args).
grep -rn "free(args)" --include="*.hpp" --include="*.cpp" Backtest/

# 2. For each worker_fn, list args->* reads BEFORE free(args)
#    and compare against args->* reads AFTER free(args). Any
#    POST-free read is a bug.
#    (Per-function awk record-based scan works.)

# 3. Cross-reference: for every struct that's malloc'd + freed by
#    a worker, grep for ALL its field names in BOTH the worker's
#    pre-free capture block AND every click-handler that populates
#    it. Missing field on either side = bug.
```

A `/bug-check` skill (queued for v5.14) reads this class definition
+ runs the detection greps automatically + reports matches.

**Known instances:**

- **v5.13.5 use-after-free in `train_multi_horizon_worker_fn`**
  (`Backtest/BacktestPanels.hpp:~3814` fix; tag `v5.13.5.B`,
  commit `6f3296c`). v5.13.5 added
  `snap_label_kind_per_horizon[]` + `snap_training_side` to
  `MultiHorizonWorkerArgs`. Old fields (horizons/tp_pcts/sl_pcts/
  auto_stamp_secret) were memcpy'd to stack before free; new fields
  were not. Subsequent reads at 4 sites (parallel-job populate +
  serial-mode loop call ×2) dereferenced freed memory → undefined
  label_kind in stamp + wrong training_side path routing. Caught
  by `/parity-check` Section L immediately after coding (audit ran
  in parallel with ship).

- **v5.13.5 single-horizon Train Model snap omission**
  (`Backtest/BacktestPanels.hpp:~4917` fix; tag `v5.13.5.A`,
  commit `743f228`). Same ship; sister bug. The Train Model click
  handler (single-horizon) routes through MultiHorizon worker
  since v5.11.44 but its click handler only populated the OLD snap
  fields, leaving the NEW v5.13.5 fields uninitialized in the
  malloc'd args. Worker read uninitialized memory → undefined
  label_kind / training_side. Caught by self-review during audit
  cycle (operator question "is the Train Model handler also
  populating the new fields?" prompted the check).

Both caught by `/parity-check` Section L (production-caller field-
population audit) — the parity audit was designed exactly for this
class after v5.9.5b found the same pattern in a stamp body context
(StampInferenceCfgInputs with 10 cfg-binding fields silently
unpopulated by the suite caller). Worth retroactively running
`/parity-check` when ANY worker-arg struct is extended.

**Prevention:**

- **Snap-capture invariant:** when extending a struct that's
  malloc'd → passed to pthread → freed in worker, the worker MUST
  capture every new field to a stack local before `free(args)`.
  PR-time check: `grep -A30 "struct .*WorkerArgs" file` lists the
  struct fields; cross-reference EVERY field appears in both the
  worker's pre-free capture block AND every click handler that
  allocates the struct.

- **Click-handler population invariant:** every malloc-site for a
  worker-args struct must populate EVERY field. Default-init via
  `(StructT*)calloc(1, sizeof(StructT))` would catch uninitialized-
  memory reads at runtime via deterministic-zero, but would NOT
  catch the use-after-free in flavor 1. Prefer explicit per-field
  population + a `/bug-check` scan.

- **`/parity-check` Section L** explicitly walks production callers
  for newly-added struct fields. Run it after ANY ship that
  extends a worker-arg struct.

- **`/bug-check` skill (v5.14):** mechanizes the detection greps
  here. Reads `RECURRING_BUG_PATTERNS.md` + walks `Backtest/` for
  `free(args)` sites + diffs `args->field` reads pre/post-free +
  reports mismatches. Lower friction than the manual grep.

---

## Class 14 — Plan calls a function or struct field that doesn't exist

**Surface:** plan-time. (Detail: any plan in `plans/` that names a callee or struct
member without verifying it exists in the current codebase. Catches
silent staleness ("v5.10 plan claimed X exists; v5.13 deleted X")
AND wishful planning ("plan author meant to add X but forgot to
list it as NEW").

**Symptom:** plan-driven coding fails to link or compile partway
through implementation. Operator + Claude lose 30-90 minutes
investigating "why doesn't this build" when the answer is "the
function the plan referenced doesn't exist." Worse: if the plan
loosely references "the existing cancel API" without naming it,
implementation may invent a wrong signature → runtime UB instead
of compile failure.

**Detection:** [delegates to /trace-deps — that skill performs the plan-vs-codebase grep walk. Body below documents the pattern.]

**Root cause:** plan author wrote against assumed-existing surface
without `grep`ping the codebase. Common when:
- The plan references a function from an adjacent codebase (e.g.,
  v5.10 trader had it but v5.14 trader doesn't)
- The plan author saw a related function (e.g., `_MarketBuy`) and
  assumed siblings exist (`_CancelOrder`)
- The struct field was renamed in a recent ship the plan author
  didn't see (e.g., `dry_run` → `reconcile_mode`)
- Cross-ship coordination missed (Plan A adds field; Plan B claims
  to use it but A hasn't shipped yet — plans don't list dependency
  edge)

**Detection:**

```bash
# For each function name mentioned in a plan:
grep -rn "^inline.*PROPOSED_FN_NAME\|^.*PROPOSED_FN_NAME\s*(" \
   --include="*.hpp" --include="*.cpp" \
   CoreFrameworks/ ML_Headers/ Strategies/ DataStream/ Backtest/
# Empty result → BLOCKING gap; either add NEW claim or rename in plan

# For each struct field referenced (e.g., obj->field_name):
grep -A100 "^struct StructName" CoreFrameworks/<file>.hpp | \
   grep "field_name"
# Empty result → BLOCKING gap; either add field as NEW or fix plan

# For pre-coding plan audits, /trace-deps automates both walks +
# reports BLOCKING vs verified-PASS per callee.
```

**Known instances:**

- **v5.14.4 plan**: `BinanceOrderAPI_CancelOrder` — plan Step 4
  called the function; grep showed no such function exists in
  `DataStream/BinanceOrderAPI.hpp`. Detected by /trace-deps before
  coding. Fixed by adding v5.14.4.0 Phase 0 sub-tag to create the
  function (mirror `_MarketBuy`/`_MarketSell` pattern at :503/:549).
- **v5.14.4 plan**: `OrderManagerState.last_seen_trade_id` — plan
  Step 3 read the field; struct doesn't have it. Same fix
  (v5.14.4.0 adds field + zero-init in `OrderManager_Init`).
- **v5.14.7 plan (caught via cross-ship coordination)**: also
  claimed to add `BinanceOrderAPI_CancelOrder` as NEW. Master plan
  ordering: v5.14.4 ships first → v5.14.7's claim updated to
  REUSE v5.14.4.0's API instead of creating a duplicate.
- **v5.15.5.F.4b plan (2026-05-14 — caught at pre-coding audit gate)**:
  plan referenced 5 functions that don't exist — `CfgParser_HandleKV`,
  `Cfg_Save`, `Cfg_LoadFromString`, `Cfg_LoadFromFile`,
  `parse_csv_engine_config`. Actual API surface: parser is the inline
  body of `ControllerConfig_Load<F>` at
  `CoreFrameworks/ControllerConfig.hpp:1798` (single function; no
  extracted KV handler); save is per-field text-splice via
  `cfg_write_field(path, key, value)` at `GUI/SettingsPanel.hpp:472`
  (comment-preserving operator UX; NOT a monolithic `Cfg_Save(FILE*)`).
  Caught by `/readiness` RED #1 (5 missing functions) + `/trace-deps`
  BL-2 (actual API surface identified). Reported in
  `plans/plan_checks/2026-05-14-v5.15.5.F.4b-fresh-audits-synthesis.md`.
  Cold-pickup hostility: fresh session would have lost ~1h re-auditing
  actual API surface before coding could start. Plan amended to
  rewrite Steps 4/5/6 against the real API. **4th detection event
  for Class 14** — pattern remains active; pre-coding mitigation
  via `/readiness` + `/trace-deps` skills working as intended (zero
  production occurrences across all 4 detection events).
- **v5.15.5.F.4c plan body (2026-05-14 — caught at `/precoding-audit-gate`
  Layer-1 orchestrator)**: 6 fictional APIs surfaced again — `Cfg_LoadFromString`,
  `Cfg_Save`, `Cfg_LoadFromFile`, `cfg_field_offset`, `cfg_dispatch_target<KIND>`,
  `template <Kind K> void cfg_parse_field<KIND_X>`. The `.F.4c` plan had an
  authoritative amendment notice at lines 15-66 explicitly invalidating these,
  but the PLAN BODY preserved the stale code samples as "scope intent."
  Caught by `/trace-deps` GAP-B + GAP-D + `/dod-audit` Class 14 detection;
  reported in `plans/plan_checks/2026-05-14-v5.15.5.F.4c-fresh-audits-synthesis.md`.
  **5th detection event for Class 14 + lesson learned:** amendment-notice
  scaffolding is INSUFFICIENT. A fresh-context coder reading top-down might
  copy body samples verbatim before noticing the notice. **Going forward:
  when amending a plan with stale code samples, DELETE the stale body —
  don't preserve-with-notice.** Plan amended at v5.15.5.F.4d planning to
  delete Step 1 entirely ("nothing to do — tt:: covers integers via shipped
  infrastructure") and rewrite Step 6 tests against canonical T1-T6 shape
  at `tests/controller_test.cpp:1548`. Lesson codified in
  `DESIGN_SPECS/audit-driven-pre-coding-gate.md` § Lessons + CLAUDE.local.md
  Sprint State Tracker.

**Prevention:**

- **`/trace-deps` skill** (created v5.14): pre-coding audit walks
  every callee + struct-field reference in a plan, runs the
  detection greps above, reports per-callee PASS/GAP. Run BEFORE
  starting any sub-plan's `.A` coding.
- **`/readiness` Check 19** (strengthened v5.14, ship-blocking):
  procedural 6-step grep for plan-to-code references. Catches
  same class via different invocation path.
- **Cross-ship dependency edges**: master plan's Integration Matrix
  lists "Plan B depends on Plan A's deliverable X". `/plan-check`
  verifies the edge.
- **Phase 0 sub-tag pattern**: when a plan needs pre-requisite
  infra that doesn't exist yet, add a `.0` sub-tag at the top
  of the sub-tag table that ships BEFORE `.A`. Example:
  v5.14.4.0 (pre-req) → v5.14.4.A (main). Makes the sequencing
  explicit + prevents stalled coding.

---

## Class 15 — Function signature drift between plan and canonical typedef

**Surface:** plan-time. (Detail: any plan adding a new function that must match an
existing typedef (e.g., `LabelFn`, `FeatureComputeFn`,
`StrategyEvalFn`). The dispatcher casts function pointers via the
typedef — wrong signature = silent runtime UB.

**Symptom:** code compiles (each function compiles in isolation;
typedef cast doesn't validate parameter shapes at compile time);
runtime calls dispatch through wrong stack layout → wrong values
read for arguments, undefined behavior. Tests that exercise the
function directly pass; tests that exercise it through the
dispatcher fail with non-deterministic values.

**Detection:** [delegates to /trace-deps Step 3 — signature drift check.]

**Root cause:** plan author wrote the new function's signature
from memory, not from the canonical typedef. Common when:
- The typedef was extended in a recent ship (e.g., `LabelFn`
  gained `extra_param` for forward_ticks lookups)
- The plan author confused two related typedefs (label vs feature
  compute fns have different shapes)
- The dispatcher uses `void*` casts internally, hiding the typedef
  contract

**Detection:**

```bash
# Find the canonical typedef:
grep -rn "typedef.*Fn\b\|using.*Fn\s*=" \
   --include="*.hpp" \
   ML_Headers/ Strategies/ Backtest/

# For each new function in a plan claiming to register via X-macro
# dispatcher: extract proposed signature from plan, diff against
# the typedef line-by-line.

# /trace-deps Step 3 (signature drift check) runs this automatically.
```

**Known instances:**

- **v5.14.5 plan, Label_CS* functions**: plan proposed signature
  `(ticks, tick_idx, total_ticks, BacktestRunConfig*)`. Canonical
  `LabelFn` typedef at `LabelFunctions.hpp:284-286` is
  `(ticks, tick_idx, total_ticks, sample_price, tp_pct, sl_pct,
  extra_param)` (7-param). All 8 existing labels use the 7-param
  form; dispatcher casts via typedef. Plan signature would have
  failed link. Detected by /trace-deps; fix was 5 minutes
  (refactor 3 fn signatures to canonical 7-param, ignore tp/sl,
  use extra_param for horizon).

**Prevention:**

- **`/trace-deps` Step 3**: signature drift audit. Compares plan
  proposed signatures against canonical typedefs for any plan
  that registers via X-macro.
- **CLAUDE_INTEGRATION.md "Adding a label/feature/strategy" recipe**:
  always cites the canonical typedef line first. Plan authors
  expected to copy that signature verbatim into the plan.
- **Plan-template discipline** (going forward): when proposing a
  new function in a plan, paste the typedef from the codebase
  into the plan as quoted reference. Forces the author to
  actually read it.

---

## Class 16 — Naming convention drift breaks X-macro dispatcher

**Surface:** plan-time. (Detail: any plan adding a function that must be discovered by
an X-macro registry (e.g., `FOREACH_FEATURE(X)`, `FOREACH_TARGET(X)`,
`FOREACH_STRATEGY(X)`). Registry expects a specific function-name
PREFIX; missing prefix = link failure (registry calls
non-existent name).

**Symptom:** clean compile per-translation-unit; link failure with
"undefined reference to `Compute_RegimeTrendStrength`" (the
registry expanded `FEATURE(RegimeTrendStrength, ...)` to
`ML_Compute_RegimeTrendStrength` but the plan defined
`Compute_RegimeTrendStrength`). Easy to fix once detected;
frustrating to detect mid-coding because the linker error doesn't
explicitly name the registry / X-macro as the calling site.

**Detection:** [delegates to /trace-deps — symbol-prefix verification before coding.]

**Root cause:** plan author saw the symbol in conversation
("Compute the regime trend strength") and named the function
literally, missing the codebase's prefix discipline. Common when:
- The codebase has two prefix conventions for sibling concepts
  (e.g., `ML_Compute_*` for features vs `Label_*` for labels)
- The convention was set in a recent ship; older callers haven't
  been migrated yet so the docstrings/examples are inconsistent
- The plan was drafted from a high-level design doc that used
  shorthand names

**Detection:**

```bash
# For each new function intended for an X-macro registry:
# 1. Find the registry macro definition:
grep -n "^#define FOREACH_FEATURE\|^#define FOREACH_TARGET\|^#define FOREACH_STRATEGY" \
   --include="*.hpp" -r ML_Headers/ Strategies/

# 2. Read the registry's expansion to learn the prefix it generates:
grep -B2 -A5 "^#define FOREACH_FEATURE" ML_Headers/FeatureRegistry.hpp
# (e.g., reveals expansion `ML_Compute_##NAME`)

# 3. Verify plan's proposed function names use the prefix.
```

**Known instances:**

- **v5.14.5 plan, regime feature functions**: plan proposed
  `Compute_RegimeTrendStrength`, `Compute_RegimeVolZscore`,
  `Compute_RegimeClassOneHot`. Codebase convention is
  `ML_Compute_*` (all 34 existing features). FOREACH_FEATURE
  expansion would call `ML_Compute_RegimeTrendStrength` (with
  prefix) → link error. Detected by /trace-deps Step 4
  (naming convention check). Fix: trivial rename (3 functions).

**Prevention:**

- **`/trace-deps` Step 4**: naming convention audit. For each
  X-macro registry, verifies plan's new functions use the
  expected prefix.
- **DOCS/FEATURE_INTERFACE.md / TARGET_INTERFACE.md** (canonical
  per-registry docs): top-of-file states the prefix; plan author
  expected to read these before drafting.
- **Plan-template snippet**: registry-related sections of new
  plans must paste the X-macro expansion line verbatim from the
  codebase (e.g., `// FOREACH_FEATURE expands NAME → ML_Compute_##NAME`).

---

## Class 17 — Architectural deferral made without grepping adjacent struct fields

**Surface:** plan-time. (Detail: any plan that defers a feature with rationale "we
don't have data X". Can be wrong if X (or a usable analog) IS
already in an adjacent struct that the plan author didn't grep.
Expensive class because it punts months of work for zero reason.

**Symptom:** a feature gets deferred to vN+1 sprint with effort
estimate "needs new infra (M LOC, 2 weeks)". Operator (or future-
Claude) reads the plan months later, asks "wait, isn't X
accessible via Y?" — yes, X is in `someStruct->ring_buf[]` which
the plan author didn't check. The deferral was invalid; vN could
have shipped in 2 hours instead of vN+1's 2 weeks.

**Detection:** [delegates to /trace-deps Step 5 — 2-hop adjacent-struct walk before accepting deferrals.]

**Root cause:** pre-coding audit (typically /trace-deps) checks
"does the surface I'm calling EXIST" but doesn't always check
"is the data I need somewhere accessible, even if not in the
obvious place". The audit's "data not in this struct" finding
is correct as far as it goes, but the author + auditor stop
before walking adjacent structs that the obvious one points to.

**Detection:**

```bash
# When considering deferring "feature X needs data Y":
# 1. List every struct accessible from the function's input ctx:
grep -A20 "^struct CtxStructName" CoreFrameworks/<file>.hpp
# (note every pointer field — those are doors to other structs)

# 2. For each pointer field's type, walk INTO that struct and
#    grep for fields that could provide Y:
grep -A50 "^struct PointedToStruct" <file>.hpp

# 3. Specifically look for:
#    - `*_buf[]` ring buffers (raw history)
#    - `*_history[]` arrays
#    - `running_*` accumulators (deltas can give raw values)
#    - `head` / `count` write-position markers (signal a ring exists)

# Pre-coding skill /trace-deps Step 5 (NEW v5.14): for any deferral,
# run a 2-hop walk through adjacent structs before accepting the
# defer rationale.
```

**Known instances:**

- **v5.14.5 frac diff (caught + reverted same day)**: plan
  initially deferred `ML_Compute_FracDiff_*` to v5.16+ with
  rationale "FeatureComputeCtx<F> only has `signals` +
  `short_rolling` (aggregates); no raw price history accessible".
  Operator caught it: "we have raw tick data for backtesting".
  Investigation: `ctx->short_rolling->price_buf[W]` is the raw
  ring (pre-existing for eviction logic; W=128 = 128 lags
  available). Plus `head` (write position) + `count` (warmup
  state). Frac diff truncates at K≈50 lag terms (|C(0.5,50)|<1e-6),
  well within W=128. The feature needs ZERO new infrastructure —
  3 inline functions reading the existing ring with `(head-1-k)
  & (W-1)` indexing. Re-shipped as v5.14.5.C, not deferred.

**Prevention:**

- **`/trace-deps` Step 5** (NEW): for any deferral with rationale
  "missing data X", explicitly walk adjacent structs (1-2 hops
  from the input ctx) and grep for ring buffers / history arrays
  / accumulators that could provide X. ONLY accept the deferral
  if the 2-hop walk turns up nothing.
- **Plan-template discipline** (going forward): "Deferred to vN+M"
  blocks must list "Adjacent structs walked: <list>" + "Why none
  provide the data: <reason>". Forces the deferring author to
  show their work.
- **CLAUDE.local.md memory** (already exists, generalizes here):
  "boundary-stable refactor" rule — prefer NOT cascading struct
  changes. Frac diff was deferred specifically because we thought
  cascading FeatureComputeCtx was needed. This class memory
  reminds us to look for boundary-preserving access first.

---

## Class 18 — "Mirror" plans missing data-flow dependencies

**Surface:** plan-time. (Detail: any plan that says "mirror X for Y" or "duplicate the
pattern of X for the new Y context" without enumerating the DATA
SOURCES that X reads from. Audits verify the SYMBOLS in the
mirrored block resolve at the new call site, but skip the upstream
data dependencies that X consumes.

**Symptom:** code COMPILES + LINKS cleanly because all named
symbols (functions, struct fields, cfg constants) exist on the
new side. At runtime, the mirrored block reads garbage / NaN /
zeros / wrong handle's data because the data source X depended on
has no Y-side equivalent. May not even trigger NaN guard if the
zero-init looks plausible (e.g., empty ring → uniform fallback
weights → "looks normal" but isn't actually computing what the
operator thinks it's computing).

**Root cause:** plan abstraction layer ("mirror X") hides the
implementation detail that X reads from a specific data source.
Audit walks SYMBOL existence (function declarations, struct field
declarations, cfg fields) but not READ-FLOW (what the body of X
actually consumes). For "duplicate this pattern" plans, the audit
must walk the body of the source code being mirrored + verify
each upstream read has an equivalent on the new side.

**Detection:** [delegates to /trace-deps Step 6 — data-flow dependency walk for mirror plans.]

```bash
# For any plan saying "mirror X" or "duplicate X for Y":
# 1. Identify X's source code location (file:line range)
# 2. Grep the source range for `obj->field` reads:
sed -n '<start>,<end>p' source.hpp | grep -oE '[a-z_]+(_)?->[a-z_]+'
# 3. For each `obj->field` read, identify which struct obj is.
# 4. For each (struct, field) pair, verify the Y-side equivalent
#    has the SAME field name (or a documented parallel name).
# 5. If any field is missing on Y-side: plan must add it BEFORE
#    coding, OR plan must explicitly note the data-source gap.

# Example: v5.14.0 buy-side Ridge override at StrategyParameters:891-947
# Reads: ezoo->reward_ring, ezoo->reward_ring_head,
#        ezoo->predict_call_count, ezoo->ridge_state, ezoo->primary_count,
#        ezoo->drift[i].ic_avg, config->ridge_lambda etc.
# For the v5.14.1.E exit-side mirror, equivalents needed:
#   ezoo_ex->exit_reward_ring (MISSING — caught mid-coding)
#   ezoo_ex->exit_reward_ring_head (MISSING)
#   ezoo_ex->exit_predict_call_count (MISSING)
#   ezoo_ex->exit_ridge_state (planned + added in .E.A)
#   ezoo_ex->exit_predictor_count (existing v5.13.4)
# 3 of 5 dependencies were missing from the plan; only caught
# during coding when the implementation hit them.
```

**Known instances:**

- **v5.14.1.E.B (caught + fixed mid-coding 2026-05-09)**: plan said
  "mirror v5.14.0 buy-side ridge_within_horizon override block".
  Audit verified all NAMED symbols (RidgeBlender_Compute, ridge_state,
  MAX_RIDGE_MODELS, etc.) exist on both buy + exit sides. Missed:
  the buy-side block reads `ezoo->reward_ring` which is buy-side-only.
  Without `exit_reward_ring`, the mirrored block would have read
  zero-initialized ring → empty correlation matrix → Ridge would
  silently return uniform fallback weights, "looking like it works"
  but not actually computing correlation-aware blending. Caught
  during coding when implementing the Ridge invocation; added
  exit_reward_ring + populator + counter (~30 LOC) before tagging
  v5.14.1.E.B. Audit reports were GREEN; class of miss not in any
  existing audit checklist.
- **v5.15.5.F.4c plan body (2026-05-14 — caught at `/merge-scan` audit
  during `/precoding-audit-gate` Layer-1 orchestrator)**: plan Step 3
  proposed declaring NEW arrays `BANDIT_ALGO_LABELS[]`,
  `RISK_CURVE_LABELS[]`, `BARRIER_BLEND_LABELS[]`, `ENGINE_ARCH_LABELS[]`
  for INT_ENUM cfg field dropdown rendering. **All four enums already
  had full X-macro registries with ToString/FromString:**
  `Strategies/BanditAlgorithmRegistry.hpp:87` (3 entries — plan claimed 2,
  drift); `ML_Headers/ConfidenceScore.hpp:714` FOREACH_DEGRADATION_CURVE;
  `Strategies/BarrierBlendModeRegistry.hpp:82` (5 entries — plan's
  proposed labels `SHADOW_A`/`SHADOW_B` did NOT match actual
  `BOTH_BLEND_DRIVES`/`BOTH_DOMINANT_DRIVES`, would have rendered
  wrong labels in GUI). Mirror-incomplete shape at the **enum label
  table layer** — same shape as function-mirror at predicate layer.
  Caught by `/merge-scan` F1 (Class 18 mirror-incomplete risk in plan
  Step 3) reported in
  `plans/plan_checks/2026-05-14-v5.15.5.F.4c-fresh-audits-synthesis.md`.
  Plan amended at v5.15.5.F.4d planning to reuse via X_GEN_LABEL
  helper at each registry source → exports auto-generated
  `extern const char* const NAME_LABELS[]` → CfgFieldRegistry
  references the extern. Single source of truth preserved; future
  enum-name renames flow automatically. Pattern codification candidate:
  "cross-registry label export pattern" (sub-pattern of
  `x-macro-registry-with-presence-dispatch.md`); promote to
  DESIGN_SPEC after 2nd application.

**Prevention:**

- **`/trace-deps` skill spec update** (added v5.14.1.E.B): for any
  plan keyword "mirror" / "duplicate" / "parallel to X" / "same
  pattern as X", add a Step N: "Mirror data-flow audit". Walk the
  body of X (file:line range from plan), grep for `obj->field`
  reads, verify each (struct, field) pair has a Y-side equivalent.
  Flag missing data sources as RED before coding starts.
- **Plan-template discipline**: "mirror X for Y" plans MUST include
  an "X data-flow inventory" section listing every upstream read X
  performs + the matching Y-side data source for each. Forces the
  plan author to enumerate dependencies, not abstract them behind
  the "mirror" word.
- **Audit-skill enhancement**: /readiness Check 19 (procedural
  pre-existing-work audit) extended with a 7th step for "mirror"
  plans: "for the source pattern being mirrored, list every struct
  field read in its body; verify each has a target-side equivalent
  in the same scope".

**Related classes:**
- Class 12 (Wired-but-unexercised) — similar "looks fine, isn't fine"
  failure mode but at the call-site level rather than data-flow
- Class 14 (Plan calls non-existent function) — symbol-existence
  gap; this class is the data-flow analog

---

## Class 18 STRENGTHENED — call-sequence enumeration (added 2026-05-09 by v5.14.2.E.1)

**Surface:** plan-time. (Sub-section under Class 18; same delegation applies.)

**Detection:** [delegates to /trace-deps Step 6 — call-sequence enumeration extension to data-flow walk.]

**The strengthening:** Class 18's original detection focused on
DATA-FLOW INPUTS (struct field reads). Equally critical for "mirror X
for Y" plans is enumerating the CALL SEQUENCE — which functions the
mirrored body INVOKES.

PARITY-009/010/011/012 (4 separate Class 18 findings closed by v5.14.2.E.1):

| ID | Mirror | Calls missed |
|---|---|---|
| PARITY-009 | EnsembleHotSwap.hpp mirrors boot ensemble setup | 6 of 8 boot post-load calls (blend_mode, SetDisabledHorizons, SetBanditSaveInterval, ValidateAgainstCfg, + 2 cfg passthroughs) |
| PARITY-010 | BacktestSharded mirrors boot ensemble setup | 2 of 8 calls (InitExitBandits, LoadExitBanditState; v5.13.4 additions never propagated to backtest) |
| PARITY-011 | Single-zoo hot-swap mirrors boot single-zoo | 1 call (VerifyExpected; original v5.10.0c hot-swap omitted) |
| PARITY-012 | Backtest single-zoo mirrors boot single-zoo | 1 call (ValidateAgainstCfg; v5.10.2.A added to live boot but not backtest) |

**Total:** 10 sub-gaps, all SAME shape — boot's full call sequence drifted
from 3 mirror sites because audits checked inputs but not calls.

**Strengthened detection:**

```bash
# Original Step 6 (data-flow audit):
sed -n '<start>,<end>p' source.hpp | grep -oE '[a-z_]+(_)?->[a-z_]+'

# NEW: also enumerate function CALLS
sed -n '<start>,<end>p' source.hpp | grep -oE '[A-Z][a-zA-Z0-9_]+\s*\('
sed -n '<start>,<end>p' source.hpp | grep -oE '[a-z][a-zA-Z0-9_]+\s*\('
# For each call, verify Y-side mirror invokes it OR has explicit reason not to
```

**Strengthened prevention:**

- **`/trace-deps` Step 6** strengthened with call-sequence audit
  sub-clause (v5.14.2.E.3 ship)
- **`/readiness` Check 24** added (v5.14.2.E.3 ship): "If your plan
  adds a function that mirrors an existing one, run /trace-deps Step
  6 with explicit call-sequence enumeration. If duplication is found,
  is X-macro registry the right shape?"
- **CLAUDE.md item 19** added (v5.14.2.E.3 ship): "Structural fix >
  direct patch when bug class can recur." When `/parity-check` or
  `/merge-scan` surfaces a recurring pattern, default to X-macro
  registry / helper extraction (PostLoadSetup helpers are canonical
  example).
- **Symmetry tests at CI level** (v5.14.2.E.1 pattern): when an
  X-macro registry has cross-site callers, write a test that runs
  the helper from each site + asserts state bytewise-identical.

**Class extinguished structurally for the model-load surface area** by
v5.14.2.E.1's `EnsembleModelZoo_PostLoadSetup` + `CoreModelZoo_PostLoadSetup`
helpers + `FOREACH_ENSEMBLE_POST_LOAD` / `FOREACH_SINGLE_ZOO_POST_LOAD`
X-macro registries. Adding a new post-load step is ONE line in the
registry; boot, backtest, hot-swap inherit automatically. Compile-time
enforced inclusion at all sites; bypass impossible.

**The class can still recur for OTHER surfaces** (OMS init, Reconcile
init, ConfidenceScorer extension, etc.) — Check 24 catches those at
audit time. v5.X+ should extract similar helpers if those surfaces
develop their own boot↔backtest↔hot-swap mirror gaps.

---

## Class 19 — Hardcoded instance names in applicability gating (Class 18 at predicate-condition level)

**Surface:** live + slow-path + GUI. Wherever code reads cfg/state and decides "does this matter for the current setup?" — strategy gating, regime conditional logic, op-mode dispatch, risk-mode handling.

**Symptom:** adding a new strategy (or regime, op-mode, variant) requires editing N call sites that gate behavior based on the old enum value. Sometimes silently misses sites → new strategy's cfg fields are inaccessible / new regime's filtering doesn't apply / new variant's feature is dead code. Operator sees "the new strategy doesn't seem to use bandit_blend_ratio even though docs say it should."

**Root cause:** code expresses "this cfg field / behavior is relevant when X" as `if (strategy == STRATEGY_ML) { ... }` — hardcoded enum value. When STRATEGY_ENSEMBLE_V1 is added (same capability cluster as STRATEGY_ML), every gating site must add `|| strategy == STRATEGY_ENSEMBLE_V1`. Forgetting any site causes silent gap. Same Class 18 mirror shape, but at the **predicate-condition level** instead of function-composition level.

**Detection:**
```bash
# Find hardcoded strategy/regime/mode comparisons in gating contexts:
rg "strategy\s*==\s*STRATEGY_\w+" Strategies/ ML_Headers/ GUI/
rg "regime\s*==\s*REGIME_\w+" Strategies/ ML_Headers/
rg "op_mode\s*==\s*OP_MODE_\w+|mode\s*==\s*BACKTEST|is_backtest|is_live" Backtest/ CoreFrameworks/

# Each match is a candidate for categorical-tag conversion.
# True applicability is "capability bit" (STRAT_CAT_USES_BANDIT), not "specific instance name" (STRATEGY_ML).
```

**Known instances:**
- 2026-05-14: surfaced during v5.15.5.F.4 categorical-tag pattern design. Multiple cfg gating sites (`if (strategy == STRATEGY_ML) render(cfg.bandit_blend_ratio)`) would have silently broken on STRATEGY_ENSEMBLE_V1 addition or similar variants. Structurally closed at `.F.4b/h` via categorical applicability + capability tags. Pattern: `DESIGN_SPECS/categorical-tag-applicability-pattern.md`. CLAUDE.local.md "Going-forward rule: categorical applicability for new cfg fields (set 2026-05-14)".

**Prevention:**
- **Categorical-tag pattern**: instances declare capability categories (`STRATEGY_ML` declares `STRAT_CAT_USES_BANDIT | STRAT_CAT_USES_RIDGE | ...`); consumers gate on bitmap intersection (`if (descriptor.applies_to_strategy_cat & active_strategy_cats)`). Adding a new instance = declare its categories; consumers auto-apply.
- **CI consistency tests** (Test 1: no orphan categories; Test 2: no orphan cfg fields; Test 3: instance capability dependencies hold).
- **`/dod-audit` extension:** detection signature above; flag hardcoded instance-name gating as candidates for categorical conversion.

**Related classes:**
- Class 18 (Mirror-incomplete plans) — same shape at function-composition level
- Class 14 (Plan calls non-existent function) — symbol-existence gap
- Class 21 (Multiple parallel descriptors) — both are "N parallel things drift" at different layers

---

## Class 20 — Bitmap field without overflow guard (silent-truncation)

**Surface:** any registry + bitmap pair (~30+ in the codebase). FOREACH_X paired with X_flags field of fixed width (uint8_t / uint16_t / uint32_t / uint64_t).

**Symptom:** new registry entry's flag bit "doesn't work" — `BITMAP_IS_SET(flags, MASK_NEW)` always returns false; `BITMAP_SET(flags, MASK_NEW)` is a silent no-op. Code compiles cleanly; tests using the flag pass trivially (because the flag is always 0 — there's no bit to test or set); operator-visible behavior diverges from documentation. Hours of debug before realizing the bit shift overflowed the bitmap type.

**Root cause:** FOREACH_X registry grows organically. Bitmap type was uint8_t when registry had 5 entries. Now registry has 9 entries; `1 << 8` exceeds uint8_t's width; result is implementation-defined (typically 0, sometimes UB). The new enum value silently equals 0; `BITMAP_IS_SET(flags, 0)` is always false; `BITMAP_SET(flags, 0)` is a no-op. **No runtime check** can detect this — the bit doesn't exist; nothing to inspect.

**Detection:**
```bash
# Find all FOREACH_X registries + their paired bitmap fields:
rg "^#define FOREACH_(\w+)\s*\(X\)" --type cpp .

# For each, find bitmap field paired with it:
rg "uint(8|16|32|64)_t\s+\w+_flags" CoreFrameworks/ ML_Headers/ MemHeaders/

# For each pair, check for paired static_assert:
rg "static_assert\(FOREACH_\w+_COUNT_VALUE\s*<=\s*sizeof" CoreFrameworks/ ML_Headers/ MemHeaders/
# Missing static_assert = vulnerable to overflow.
```

**Known instances:**
- 2026-05-14: surfaced during v5.15.5.F.4 audit synthesis. Multiple bitmap-paired registries in codebase lack overflow guards. Structurally closed at `.F.4h` via audit pass + adding `static_assert(FOREACH_X_COUNT_VALUE <= sizeof(X_flags_type) * 8)` to every paired bitmap. Pattern: `DESIGN_SPECS/bitmap-overflow-protection-discipline.md`. CLAUDE.local.md "Going-forward rule: bitmap overflow static_assert is mandatory (set 2026-05-14)".

**Prevention:**
- **Co-located static_assert** at end of every FOREACH_X declaration:
  ```cpp
  #define FOREACH_X_COUNT_ENTRY(...) +1
  constexpr size_t FOREACH_X_COUNT_VALUE = 0 FOREACH_X(FOREACH_X_COUNT_ENTRY);
  #undef FOREACH_X_COUNT_ENTRY
  
  static_assert(FOREACH_X_COUNT_VALUE <= sizeof(X_flags_type) * 8,
                "FOREACH_X overflowed bitmap type. Upgrade type width OR "
                "split into multiple bitmaps OR use multi-bit state encoding.");
  ```
- **Type-upgrade decision tree** (per `DESIGN_SPECS/bitmap-overflow-protection-discipline.md`): uint8_t → uint16_t → uint32_t → uint64_t → split or multi-bit pack.
- **`/dod-audit` extension** detects every FOREACH_X without a paired static_assert.
- CLAUDE.md item promotion candidate (after `.F.4h` audit closes the existing inventory).

**Related classes:**
- Class 18 (Mirror-incomplete) — same "silently appears to work" failure shape
- CLAUDE.md item 20 (BITMAP_* API) — usage pattern; this class is the discipline complement
- CLAUDE.md item 30 (registry-bitmap SET discipline) — sister rule for SET-site consistency

---

## Class 21 — Multiple parallel descriptors for similar surfaces (cross-file drift)

**Surface:** any subsystem where multiple structurally-similar descriptors exist (e.g., separate per-cfg-file descriptors: CfgFieldDescriptor + BacktestCfgFieldDescriptor + ControllerCfgFieldDescriptor; or multiple per-field metadata tables side-by-side).

**Symptom:** adding a feature to one descriptor (e.g., new metadata bit like RESTART_REQUIRED, new tt:: dispatch specialization for a new Kind) requires updating N parallel descriptors. Forgetting any = inconsistent behavior across surfaces (e.g., backtest cfg has SAFETY_CRITICAL modals but live cfg doesn't, or vice versa). Same Class 18 mirror shape at the descriptor level.

**Root cause:** historical organic growth — each cfg file got its own descriptor when introduced. As features accrue (RESTART_REQUIRED, SAFETY_CRITICAL, IS_SECRET, categorical applicability, etc.), each must be added to N descriptors. Drift accumulates.

**Detection:**
```bash
# Find multiple structurally-similar descriptor types:
rg "struct\s+\w+Descriptor" CoreFrameworks/ ML_Headers/ MemHeaders/
# Compare field lists; if 2+ descriptors share ~70% of fields, candidate for consolidation via discriminator pattern.

# Find consumers that switch on descriptor TYPE:
rg "switch\s*\(.*descriptor\.type|\.kind\s*==.*Descriptor" .
```

**Known instances:**
- 2026-05-14: surfaced during v5.15.5.F.4 design discussion. Pre-design considered separate BacktestCfgFieldDescriptor / ControllerCfgFieldDescriptor / SecretsCfgFieldDescriptor / TrainingCfgFieldDescriptor for the 5 cfg files; rejected in favor of ONE CfgFieldDescriptor + `lives_in_struct` discriminator + extension points (metadata bits, Kind enum values, sidecar tables). Per `DESIGN_SPECS/universal-cfg-field-registry-pattern.md` + `DESIGN_SPECS/categorical-tag-applicability-pattern.md` § "Cross-file cfg unification".
- **v5.15.5.F.4d planning (2026-05-14 — structural closure at the drift-detection surface)**: original Option D framing kept `FOREACH_CFG_DRIFT_CHECK` wide variant (19 entries) as a PARALLEL registry alongside `FOREACH_CFG_FIELD` post-derived-filter — preserving Class 21 risk at the drift-detection surface. Re-examined during operator consult; replaced wide-variant with **sidecar override pattern** (`FOREACH_DRIFT_OVERRIDE` ~5 entries indexed by FIELD_IDX; CFG_DRIFT_AUTOPOPULATE walks STAMP_BOUND derived filter + dispatches via override lookup). Single auto-flow path; per-field customization via small sparse sidecar; wide-variant CfgDriftCheckRegistry deprecated. Class 21 structurally closed at the auto-flow-with-overrides surface. Pattern codified in `DESIGN_SPECS/sidecar-override-pattern-for-registry-auto-flows.md` (DRAFT v1.0 pending .F.4d ship); generalizable to 6 future surfaces (per-strategy custom gating, per-feature custom validation, custom cfg rendering, custom INT_ENUM parsing, per-failure-mode escalation, per-slow-path-gate evaluation). Per `DESIGN_PHILOSOPHY.md` § 1.5 (Framework discipline meta-principle) + CLAUDE.md item 31.

**Prevention:**
- **Single descriptor + discriminator pattern:** ONE descriptor type + an enum field (e.g., `LivesInStruct`) that routes data to the appropriate underlying struct. Adding a new "kind" of data = new enum value; descriptor unchanged.
- **Extension points:** metadata bitmap for feature flags; Kind enum for type-specific handling; sidecar tables for sparse per-entry data that doesn't fit the common descriptor.
- **Sidecar override pattern for auto-flowed registries** (added 2026-05-14 from .F.4d planning): when a registry has standard-case auto-flow PLUS custom-semantics cases, use a sidecar override table indexed by parent registry's FIELD_IDX + CI cross-check; NEVER a parallel wide-variant registry. See `DESIGN_SPECS/sidecar-override-pattern-for-registry-auto-flows.md`. Aligns with H17 (pending invariant at .F.4d ship).
- **`/merge-scan` extension:** flag parallel descriptors with ≥70% field overlap as consolidation candidates. Extended to flag parallel registries-over-same-parent.
- CLAUDE.local.md "Going-forward rule: cross-file cfg surfaces use lives_in_struct (set 2026-05-14)" + "Framework discipline over ad-hoc (set 2026-05-14)".

**Related classes:**
- Class 18 (Mirror-incomplete plans) — same shape at function level
- Class 19 (Hardcoded instance names) — both are "N parallel things drift" — different layer
- Class 22 (Runtime cfg gating in code paths) — sibling drift class within cfg surface

---

## Class 22 — Runtime cfg gating scattered in code paths (instead of registry)

**Surface:** cfg field with runtime enablement chain (e.g., `thompson_*_prior` cfg fields only matter when `bandit_algorithm == THOMPSON`; `ridge_lambda` only matters when `ridge_within_horizon || ridge_across_horizons`).

**Symptom:** changing a cfg field's gating condition requires editing N call sites that all check the same gating predicate. Forgetting any site → cfg field is read in some paths but not others → inconsistent runtime behavior (e.g., operator changes `bandit_algorithm`, GUI updates correctly but ML inference still reads the old algorithm's params). Adding a new gated read = remember to add the gating check; missing it causes silent dead-config.

**Root cause:** gating predicate (`if (cfg.bandit_algorithm == THOMPSON)`) is repeated wherever the cfg field is read or rendered. Sites include parser validation, GUI rendering, validator checks, inference body. Adding a new consumer = remember to add the same gating predicate. Drift across N sites.

**Detection:**
```bash
# Find repeated gating predicates around cfg field reads:
rg "if\s*\(.*bandit_algorithm.*==.*THOMPSON\)" .
rg "if\s*\(.*ridge_within_horizon.*\|\|.*ridge_across_horizons\)" .
# Each occurrence is a candidate for centralized registry-level gating.
```

**Known instances:**
- 2026-05-14: surfaced during v5.15.5.F.4 design. Multiple cfg fields have runtime gating predicates scattered across consumer sites (parser validates, GUI hides, inference reads). Structurally closed at `.F.4b` via `requires_cfg` column in CfgFieldDescriptor + centralized predicate evaluation in GUI render walk.

**Prevention:**
- **`requires_cfg` column** in CfgFieldDescriptor — names the gating cfg condition as a string expression. GUI evaluates at render time; validators can query the predicate via centralized helper; consumers reference the column instead of inlining the check.
- **CI test:** every `requires_cfg` expression is reachable + non-contradictory (no field whose gating predicate is impossible to satisfy).
- **`/dod-audit` extension:** flag scattered identical `if (cfg.X == Y)` patterns as candidates for `requires_cfg` migration.

**Related classes:**
- Class 21 (Multiple parallel descriptors) — both are "centralize metadata to avoid drift" at different layers
- Class 19 (Hardcoded instance names) — different applicability axis (categorical scope vs runtime gate); both compose at the cfg field level

---

## Class 23 — Type-erased typed-field write via reinterpret_cast through char* offset

**Surface:** any registry-driven typed-field access (parser, save, render, drift-check, snapshot publish). High-risk when destination field types are template-instantiated (`FPN<F>`, custom POD types) vs trivial scalars (`double`, `int`).

**Symptom:** silent data corruption when writing to typed fields via opaque byte offsets. Parser/save appears to work for cfg roundtrip tests that exercise scalar fields (double, int) but produces garbage when the same code path runs against `FPN<F>`-typed fields. Bug latent in production for any field whose actual type differs from the assumed pun type. Tests that compare struct-field-after-load to struct-field-before-save miss it if they only exercise the trivial-type subset. Catastrophic for backtest determinism + train-serve parity because FPN mantissa words get clobbered while the load+compare-back roundtrip silently agrees within the corrupted 8-byte view.

**Root cause:** the code pattern `*reinterpret_cast<T*>((char*)dst + offset) = value` PUNS the destination address as type T regardless of the actual field type stored there. For 8-byte `double` punned through a 24-byte `FPN<F>` address: writes 8 bytes (double mantissa+exponent) into the first 8 bytes of the FPN's `uint64_t w[2]` storage. The FPN's remaining 16 bytes (second word + sign + padding) keep stale data. Subsequent FPN arithmetic operates on corrupt state → silent precision loss + non-deterministic outputs.

The shape is "type erasure at registry dispatch time": the registry knows the cfg field NAME but not its TYPE; the dispatcher uses Kind enum (DOUBLE/INT/etc.) to drive the type, decoupling it from the actual struct field declaration. When Kind ≠ actual field type, the dispatch silently corrupts.

**Detection:**

```bash
# Find reinterpret_cast through char* offset arithmetic (the anti-shape):
rg "reinterpret_cast<\s*\w+\s*\*>\(.*\(char\s*\*\)|reinterpret_cast<\s*\w+\s*\*>\(\s*reinterpret_cast<\s*char\s*\*>" --type cpp .

# Tighten: cfg/registry dispatch context specifically:
rg "reinterpret_cast<.*>.*\+\s*\w*offset" CoreFrameworks/ ML_Headers/ Strategies/ Backtest/

# Find offsetof + reinterpret_cast pairs (most common anti-form):
rg -B2 "reinterpret_cast<.*\*>" CoreFrameworks/ ML_Headers/ | rg -A2 "offsetof"
```

Audit hooks: `/dod-audit` Stage 6 detection signature; `/bug-check` registry-driven scan picks this up automatically once Class 23 is in the registry.

**Known instances:**

- **2026-05-14 — v5.15.5.F.4b pre-coding audit (CAUGHT BEFORE SHIP).** Plan Step 2 specified `tt::cfg_parse_field<KIND_DOUBLE>` using `*reinterpret_cast<double*>((char*)cfg + cfg_field_offset(name)) = v;` for ~40 KIND_DOUBLE/_PCT cfg fields. ~38 of those 40 fields are actually `FPN<F>` (24 bytes) in `ControllerConfig<F>`. Caught by `/trace-deps` BL-1 (independent finding) and `/merge-scan` #3 (related pattern alignment); reported in `plans/plan_checks/2026-05-14-v5.15.5.F.4b-fresh-audits-synthesis.md`. **Anti-pattern caught at pre-coding gate — zero production occurrences.** Plan amended to use type-dispatch-on-T pattern per Prevention below.

**Prevention — 3-barrier structural fix (extinguishes the class):**

The bug is structurally unreachable when ALL three barriers are in place. Each barrier alone is insufficient; together they make the anti-shape impossible to write accidentally + grep-detectable on intentional bypass.

**Barrier 1 — API surface: no void*+offset entry point exists.** The only `tt::cfg_*_field` overloads take destination by reference; T is deduced. There is NO `tt::cfg_parse_field<KIND>(void* base, size_t offset, ...)` form to invoke.

```cpp
namespace tt {
    template <typename T>
    inline void cfg_parse_field(T& dst, const CfgFieldDescriptor& desc, const char* val);

    template <typename T>
    inline void cfg_save_field(const T& src, const CfgFieldDescriptor& desc, char* buf, size_t cap);

    template <typename T>
    inline bool cfg_render_field(T& field, const CfgFieldDescriptor& desc);
}
```

A new contributor cannot accidentally write the anti-shape because the unsafe symbol doesn't exist. Bypassing requires inventing new infrastructure — grep-detectable.

**Barrier 2 — X-macro extractor is the chokepoint.** The only way to walk a cfg field registry is through extractor macros that follow the canonical shape:

```cpp
#define EMIT_CFG_PARSER_CASE(kind_token, name, label, section, meta, payload, tooltip, \
                              applies_to_strategy, applies_to_op_mode, lives_in) \
    else if (strcmp(key, #name) == 0) { \
        tt::cfg_parse_field(cfg->name, g_cfg_field_descriptors[FIELD_IDX_##name], val); \
    }
FOREACH_CFG_FIELD(EMIT_CFG_PARSER_CASE)
```

`cfg->name` is a real field access; T is deduced from the field declaration. There's no `&((char*)cfg)[offset]` form in the extractor template. New contributors copy the existing shape; the safe form is the only template available.

**Barrier 3 — compile-time type-family guard inside the dispatcher.** The dispatch helper `static_assert`s that T is in a recognized family before any if-constexpr branch:

```cpp
namespace tt {
    template <typename T>
    inline void cfg_parse_field(T& dst, const CfgFieldDescriptor& desc, const char* val) {
        static_assert(is_FPN_v<T>
                   || std::is_floating_point_v<T>
                   || std::is_integral_v<T>
                   || std::is_array_v<T>,
                      "cfg field type not in recognized family — "
                      "extend tt::cfg_parse_field<T> with a new branch before using this T as a cfg field");
        if constexpr (is_FPN_v<T>) {
            double v = parse_double_fast(val);
            v = std::clamp(v, desc.payload.as_double.clamp_min, desc.payload.as_double.clamp_max);
            dst = FPN_FromDouble<T::F>(v);
        } else if constexpr (std::is_floating_point_v<T>) {
            dst = (T)parse_double_fast(val);
        } else if constexpr (std::is_array_v<T>) {
            strncpy(dst, val, std::extent_v<T> - 1);
            dst[std::extent_v<T> - 1] = '\0';
        } else if constexpr (std::is_unsigned_v<T>) {
            dst = (T)strtoull(val, nullptr, 10);
        } else { // signed integral
            dst = (T)atoi(val);
        }
    }
}
```

Adding a cfg field of an unrecognized type **fails the build**. Forces a deliberate decision (extend the dispatcher) rather than silent truncation.

**Required type traits:**
```cpp
// FixedPoint/FixedPointN.hpp
template <typename T> struct is_FPN : std::false_type {};
template <unsigned F> struct is_FPN<FPN<F>> : std::true_type {};
template <typename T> inline constexpr bool is_FPN_v = is_FPN<T>::value;
```

**Plus audit detection** (defense in depth): `/dod-audit` + `/bug-check` scan for any historical or future `reinterpret_cast<X*>((char*)Y + Z)` pattern. Even if a contributor invents a bypass, the audit catches it at the next sub-ship gate.

**Architectural principle:** the Kind enum in the descriptor is **metadata-only** — drives GUI presentation (slider vs textbox, format string, percentage scaling, clamp coercion) but NOT type dispatch. Decouples GUI metadata from storage type. KIND_DOUBLE_PCT vs KIND_DOUBLE differs only in GUI rendering (×100 + "%" suffix), not in how the value is stored. This separation is what makes the 3-barrier design sustainable.

**Related classes:**

- **Class 11** (Extensibility friction causing silent drift) — same "manual integration site drifts from registered list" shape at a different layer
- **Class 14** (Plan calls a function or struct field that doesn't exist) — sibling process class for type-vs-API misalignment at plan-draft time. The CRITICAL-1 (Class 23 origin) + CRITICAL-2 (Class 14 recurrence) findings on v5.15.5.F.4b were detected together — the plan that proposed the anti-shape was the same plan that referenced the wrong API surface. Both stem from "drafted under imperfect API knowledge."
- **Class 16** (Naming convention drift breaks X-macro dispatcher) — both are "dispatcher behaves wrong when assumed mapping fails" at different points. Class 16 is name → bit-position; Class 23 is name → type.
- **Class 18** (Mirror-incomplete) — both are "looks correct at compile time; corrupts at runtime" failure shape.
- **Class 21** (Multiple parallel descriptors) — sibling cfg-surface class; the CfgFieldDescriptor unification (single descriptor + lives_in_struct discriminator) eliminated Class 21 at the same architectural ship as Class 23's structural fix.

**Cross-references:**

- CLAUDE.md item 23 (type-trait dispatch via templated helpers) — base pattern
- CLAUDE.md item 19 (structural fix preferred when bug class can recur) — meta-pattern motivating the 3-barrier design
- `DESIGN_SPECS/x-macro-registry-with-presence-dispatch.md` § "Y3 dispatch caveat re: if-constexpr in non-template context" — sister concern at the macro-dispatch layer
- `DESIGN_SPECS/type-trait-dispatch-via-tt-namespace.md` (NEW 2026-05-14) — dedicated antidote pattern doc; canonical reference implementation at `tt::stamp_parse_field<T>` in `ML_Headers/StampBoundModelConstRegistry.hpp:86-99`
- `DESIGN_SPECS/structural-fix-preferred-decision-framework.md` — meta-decision to apply 3-barrier structural fix vs direct patch
- `plans/plan_checks/2026-05-14-v5.15.5.F.4b-fresh-audits-synthesis.md` — full audit synthesis that surfaced the class

---

## Class 24 — Capability-cfg surface mismatch (ML pipeline supports it; operator can't see / configure / verify it)

**Detected:** 2026-05-14 (post v5.15.5.F.4c paper-test, surfaced by `/ml-audit` + operator-verification pass).
**Severity:** HIGH — operator-invisible ML capability = silent miscalibration risk.

### Recurring symptom

ML pipeline ships a capability (model role, ensemble dimension, blender mode, bandit algorithm, posterior parameter, exit-side mirror, etc.) but the cfg / Settings panel / HMAC stamp / drift-check surface doesn't expose it. The capability is *invisible* despite being in production code. Three observed instances:

- **v5.15.5.F.4c paper-test (2026-05-14):** `bandit_algorithm`, `thompson_*`, `ridge_*`, `confidence_*` (~17 fields) exist as struct fields with working parsers + stamp-bound emit, but NOT in `FOREACH_CFG_FIELD` — Settings panel renders nothing for them. Operator can't tune them via GUI.
- **v5.15.5.F.4c.2 (Thompson update wire):** `Thompson_Update` defined at `ML_Headers/ThompsonBandit.hpp:183` + fully tested, but **never called in any production reward-attribution path**. Slow-path lookback (`CoreModelZoo.hpp:1341`), trade-close reward (`CoreModelZoo.hpp:1402`), exit-side (`ControllerEventLoop.hpp:1731`) only call `Bandit_Update`. With `cfg.bandit_algorithm=1` (THOMPSON), Thompson reads its posterior for arm selection but the posterior never updates — Thompson sampling effectively-broken in production. Mode selectable, doesn't work.
- **v5.13.4 exit-side mirror (closed by v5.14.0.E):** `exit_bandits` / `exit_ridge_state` / `exit_reward_ring` exist parallel to buy-side, but for one ship the cfg surface only exposed buy-side knobs.

The shape: CODE adds a capability; SURFACE (cfg parser → Settings → stamp → drift) misses it. Capability is half-shipped — present in execution but invisible to operator.

### Root cause

Four downstream surfaces need updating per ML capability:
1. **Cfg parser** — does `engine.cfg` accept the operator-settable key?
2. **Settings render** — does the GUI panel show + allow editing?
3. **HMAC stamp tag** — is the value tagged in stamp body if parity-relevant?
4. **Per-core override** — if per-core makes sense, is `core_N_<key>` wired?

Adding an ML capability without auditing all four is the recurring failure.

### Structural fix

Per CLAUDE.md item 31 + DESIGN_PHILOSOPHY § 1.5: the universal cfg registry + bitmap dispatcher at v5.15.5.F.4c makes new capabilities → registry-row-only. Once a capability is a row in `FOREACH_CFG_FIELD`, cfg + Settings + stamp + drift auto-flow. "Added the feature, forgot the cfg surface" dies structurally.

`v5.15.5.F.4c.1` codifies this class + ships 18-row STAMP_BOUND cohort migration (first batch fix). `v5.15.5.F.4c.2` closes the Thompson_Update wire gap (second canonical instance).

### Prevention (going-forward rule + skill)

New CLAUDE.local.md going-forward rule (codified at .F.4c.1):

> **Cfg↔ML surface-alignment audit at every ML feature add.** Trigger: any new ML capability → answer four columns (cfg parse / Settings render / stamp tag / per-core override). Any "no" without documented exemption = feature not done. Fire `/ml-audit` at sub-ship close for any ship touching ML capability.

Optional `/cfg-ml-alignment` skill (deferred until 2nd ML feature add validates the rule fires correctly).

### Related classes

- **Class 11** (Extensibility friction) — sister at a different layer.
- **Class 18** (Mirror-incomplete) — same shape at single mirror; this class is the cross-surface variant.
- **Class 21** (Parallel descriptors) — sibling; same structural fix closes both for cfg fields.
- **Class 23** (Type-erased dispatch) — same ship's other anti-pattern; both eliminated via the .F.4c framework + .F.4d derived filter framework.

### Cross-references

- `plans/plan_checks/ml-audit-2026-05-14-cfg-ml-surface.md` — full audit findings + interpretation matrix
- `DESIGN_SPECS/universal-cfg-field-registry-pattern.md` — the framework that prevents this class
- `DESIGN_SPECS/universal-registry-bitmap-dispatcher-pattern.md` — the dispatcher consumer that auto-flows registered rows
- `DESIGN_SPECS/multi-state-dispatch-with-per-state-update-metadata.md` (NEW 2026-05-14 ahead of .F.4c.2) — pattern that closes the Thompson_Update-wire-missing shape via per-state metadata
- CLAUDE.md item 31 + DESIGN_PHILOSOPHY § 1.5 — framework discipline meta-principle

---

## Class 25 — Scope-erosion in per-core consumer function (registry says per-core; consumer reads from wrong scope)

**Detected:** 2026-05-15 (during v5.15.5.F.4c.3 Step 2 `_BuildParameters` migration scoping; caught BEFORE the bug shipped).
**Severity:** HIGH — per-core configuration set by operator silently ignored; behavior diverges from cfg surface invisibly.

### Recurring symptom

Per-core capability is correctly classified in `FOREACH_PER_CORE_CFG_FIELD` and present on `PerCoreCfg<F>` cores[c]. Operator sets `cfg.cores[2].take_profit_pct = 5.0` via Settings panel — value persists, reload reflects it correctly in the Settings UI for core 2.

But the CONSUMER function (e.g., `SimpleDip_BuildParameters`) takes `const ControllerConfig<F>* config` and reads `config->take_profit_pct` — which is the FLAT/GLOBAL field, or core 0's value, or a stale pre-`.F.4c.3` value depending on what the shadow-migration window is doing. Cores 1-15 silently use the wrong value.

The cfg surface CORRECTLY exposes the capability; the EXECUTION code doesn't honor scope. This is distinct from Class 24 (capability not surfaced) — here capability IS surfaced but consumer reads from wrong scope.

### Root cause

A consumer function that takes the FULL `const ControllerConfig<F>*` (or `const ControllerConfig<F>&`) when it's called per-core has access to BOTH:
- The flat / "global" field path: `config->take_profit_pct` (legacy or stale)
- The per-core path: `config->cores[c].take_profit_pct` (correct)

Author writes `config->take_profit_pct` because it's shorter, the field name is in scope, the compiler accepts it. The per-core slice is bypassed entirely. The compile succeeds; the test on core 0 passes (since `cores[0].take_profit_pct == config->take_profit_pct` under the shadow-sync window); only multi-core runtime divergence reveals the bug.

The full-cfg pointer is the discipline boundary failure. Once a per-core consumer can see the global cfg, it can lazily reach for the wrong field.

### Structural fix

**Per-core consumer functions take `const PerCoreCfg<F>*` (single-param), NEVER `const ControllerConfig<F>*`.** Globals (when genuinely needed by a per-core consumer, e.g., `poll_interval` for tick→time conversion) are caller-resolved as scalar args.

```cpp
// CORRECT
SimpleDip_BuildParameters(const RollingStats<F>* rolling,
                            const PerCoreCfg<F>* core_cfg,    // <-- per-core slice ONLY
                            FPN<F> allocated_balance,
                            GateParameters<F>* out, ...);

ML_BuildParameters(..., const PerCoreCfg<F>* core_cfg, ..., int poll_interval_arg);
                                                          // ^ scalar global, caller-resolved

// FORBIDDEN
SimpleDip_BuildParameters(const RollingStats<F>* rolling,
                            const ControllerConfig<F>* config,   // <-- WRONG; full cfg
                            ...);

// FORBIDDEN — two-param "convenience" sig silently re-introduces the anti-pattern
SimpleDip_BuildParameters(..., const ControllerConfig<F>* config,
                                const PerCoreCfg<F>* core_cfg, ...);
                       // ^ never do this; `config->X` lazy reads return for whoever ships next
```

The discipline: there is NO PATH for a per-core consumer to read the global cfg pointer. Per-core reads MUST go through `core_cfg->X`. Genuinely-global reads happen at the CALLER (which has the full cfg), are pre-resolved to scalar values, passed as explicit args. The consumer signature itself is the structural enforcement — the type system makes the wrong access non-expressible.

Closed at `v5.15.5.F.4c.3` WIP2c.2 — first canonical application; 5 strategy fns + 1 dispatcher migrated to single-param sigs; `poll_interval` extracted as scalar arg in `ML_BuildParameters`.

### Prevention (going-forward rule + audit)

Codified at `DESIGN_SPECS/cfg-scope-discipline.md` § "Consumer function signatures over per-core slices" (NEW at `.F.4c.3`).

> **Per-core consumer functions take `const PerCoreCfg<F>*` (single-param), NEVER `const ControllerConfig<F>*`.** Genuinely-global reads are caller-resolved as scalar args. Two-param sigs `(const ControllerConfig<F>* config, const PerCoreCfg<F>* core_cfg)` are FORBIDDEN — they silently re-introduce the anti-pattern.

Anti-pattern grep signatures (for `/dod-audit` + `/bug-check` integration):

```bash
# A1: Consumer fn (per-core sig family) taking ControllerConfig<F>*
rg -n "(BuildParameters|_Tick|_Adapt|_Rebuild|_Step)\(.*const ControllerConfig<F>\*" --type cpp

# A2: Per-core fn with `core_cfg` param ALSO reading `config->` (mixed-scope erosion)
rg -nP "(?s)PerCoreCfg<F>\*.*?config->[a-z_]+" --multiline --type cpp
```

Documented exemptions (false-positives):
- `ControllerConfig_ResolveForCore` — the resolver itself; producing per-core view from full cfg by design. (Deleted at `.F.4c.3` Step 2 end anyway.)
- `ControllerConfig_NormalizeForMode` — operates on whole cfg by design (mode-flip normalize pass).
- Boot-time engine init paths — full cfg needed for multi-core setup.

### Related classes

- **Class 24** (Capability-cfg surface mismatch) — sister at SURFACE layer (capability not exposed in cfg). Class 25 is at EXECUTION layer (capability exposed but execution doesn't honor scope). Both close structurally at `.F.4c.3` via the cfg-scope-discipline + single-param consumer convention.
- **Class 18** (Mirror-incomplete) — same family of "all surfaces must update together"; Class 25 is the specific consumer-side variant.
- **Class 23** (Type-erased dispatch) — same `.F.4c` ship's anti-pattern; both are "scope or type erosion through a pointer that's too broad"; structural fix is narrowing the pointer's type (tt:: namespace for type; PerCoreCfg<F>* for scope).

### Cross-references

- `DESIGN_SPECS/cfg-scope-discipline.md` § "Consumer function signatures over per-core slices" — full discipline definition
- `DESIGN_SPECS/per-instance-registry-pattern.md` — per-core registry (Class 25 applies to all per-instance axes)
- `Strategies/StrategyParameters.hpp` (post-v5.15.5.F.4c.3) — canonical 5-fn application
- CLAUDE.md item 31 — framework discipline meta-principle


## Class 27 — Single-value cache flattens per-instance distinction (subsystem state mirrors cfg as a scalar)

**Detected:** 2026-05-15 (during v5.15.5.F.4c.3 WIP2d-1.B.0c Phase 4 codification; surfaced by the OMS fee_rate per-core analysis).
**Severity:** HIGH — silent accounting / model / risk divergence per instance; affects money tracking paths.

### Recurring symptom

A subsystem (OMS, ConfidenceScorer, PortfolioController, ThompsonBandit state, ...) caches one or more cfg values as SCALAR fields on its state struct at boot:

```cpp
struct OrderManagerState {
    FPN<F> fee_rate;
    FPN<F> fee_rate_maker;   // single scalar; boot-set from cfg.fee_rate_maker
    FPN<F> fee_rate_taker;   // single scalar
    FPN<F> slippage_pct;     // single scalar
    // ...
};
// At boot: oms.fee_rate_maker = cfg.fee_rate_maker;
// Per fill: rate = o->is_maker ? oms->fee_rate_maker : oms->fee_rate_taker;
```

When cfg later becomes per-instance (`cfg.cores[c].fee_rate_maker`), the SCALAR cache loses the per-instance distinction. Every instance (every core) ends up using the FIRST core's value at every per-fill / per-event read — silently. Operator sets `cfg.cores[2].fee_rate_maker = X`; the cfg surface accepts it; the Settings panel renders it; the parser writes it. But every fill across every core reads from `oms->fee_rate_maker` which is core 0's value frozen at boot. Accounting is wrong for cores 1..N.

The class is distinct from Class 26 (global consumer reading per-core field): Class 26 is at READ TIME; Class 27 is at CACHE STRUCTURE — the cache itself has no per-instance dimension. Same root family ("subsystem-state mirror of per-instance cfg") but Class 27 is the structural pre-condition that makes Class 26 silent.

Concrete additional instance discovered: `static const double fee_rate_taker_d = FPN_ToDouble(cfg.fee_rate_taker);` at `EngineSharded.hpp:2469` — an even worse variant. The `static` caches at first lambda invocation, then NEVER refreshes. No sync path. Class 27 anti-pattern at the function-static level.

### Root cause

Two compounding patterns:

1. **Subsystem caches cfg values for performance** — reading cfg through a long pointer chain per fill is slower than reading a local cache. Cache is a reasonable optimization in principle.
2. **The cache is shaped as a SCALAR matching the (then-global) cfg shape** — at the time the cache is added, cfg is global; scalar matches naturally. When cfg later grows a per-instance axis, the cache shape doesn't change.

The flatten happens at cfg-growth time, but the BUG is introduced at cache-design time. The cache pattern is correct; the SHAPE assumption is the lurking bug.

### Structural fix

**First line: pre-resolve onto in-flight object (preferred).** The in-flight object (Order, Position, Event, TradeEvent) knows its per-instance context at creation time. Bind the per-instance cfg value onto the object at creation. Downstream consumers read from the object directly — zero cache, zero per-instance distinction to lose.

```cpp
// CORRECT — Order carries pre-resolved effective_fee_rate
struct Order {
    uint8_t   core_id;
    uint8_t   is_maker;
    FPN<F>    effective_fee_rate;   // pre-resolved at submit
    // ...
};

// At Order creation (slow-path):
o->effective_fee_rate = is_maker
    ? cfg.cores[core_id].fee_rate_maker
    : cfg.cores[core_id].fee_rate_taker;

// HandleFill (drainer):
FPN<F> rate = o->effective_fee_rate;  // zero cache lookup
```

**Second line (rare): registry-driven per-instance cache (fallback).** When no in-flight object exists, `FOREACH_<SUBSYS>_CFG_CACHE` X-macro generates per-instance arrays + sync helper + accessor. Composes with `postloadsetup-registry-pattern.md` for cfg-reload hook integration.

**FORBIDDEN under going-forward rule:**

```cpp
// FORBIDDEN — scalar cfg-mirror on subsystem state
struct SubsysState {
    FPN<F> some_cfg_value;   // mirrors cfg.cores[c].some_cfg_value
};

// FORBIDDEN — static const fn-local cache
void some_fn(...) {
    static const double rate = FPN_ToDouble(cfg.fee_rate_taker);  // freezes first value forever
    // ...
}
```

Closed at `v5.15.5.F.4c.3` WIP2d-1.B.1 — first canonical application of decision-time-data-binding via Order `effective_fee_rate`. OMS scalar fee_rate fields DELETED; static fn-local cache DELETED. Cohort sweep at WIP2d-1.B.1.b extends to slippage_pct + any other Class 27 instances surfaced by `/accounting-audit` canonical first run.

### Prevention (going-forward rule + audit + CI)

Codified at `DESIGN_SPECS/decision-time-data-binding-pattern.md` (NEW at `.F.4c.3`).

> **Per-instance cfg values bind at decision time and flow forward with the in-flight object, NOT in subsystem state.** First line of defense: pre-resolve onto in-flight object. Second line (fallback): registry-driven per-instance cache when no in-flight object exists. Anti-pattern: scalar cfg-mirror field on subsystem state with implicit per-instance distinction.

CI enforcement at `tools/check_per_core_registry_integrity.py` Check 7 (NEW at WIP2d-1.B.0c): scans designated subsystem state types for scalar fields whose names match cfg field names. Match without explicit exemption in `MANUAL_FIELDS_INVENTORY.md` Section C → BUILD FAIL.

Audit skills:
- `/accounting-audit` (NEW at `.F.4c.3`) — canonical scanner for Class 27 instances + sister accounting issues
- `/registry-fit-audit` (NEW at `.F.4c.3`) — scans existing registries for misapplication per framework-selection criteria; surfaces "registry where pre-resolution would be better" findings

Anti-pattern grep signatures (for `/accounting-audit` + `/bug-check` integration):

```bash
# A1: Scalar cfg-mirror field on subsystem state (Class 27 primary shape)
# Heuristic: subsystem state struct fields with names matching FOREACH_PER_CORE_CFG_FIELD entries.
# (Enforced compile-time-failing by tools/check_per_core_registry_integrity.py Check 7.)

# A2: static const fn-local cfg cache (Class 27 fn-local variant)
rg -nP 'static\s+const\s+\w+\s+\w+\s*=\s*\w*FPN_ToDouble\s*\(\s*cfg\.\w' --type cpp

# A3: In-flight object missing pre-resolved per-instance field that should be there
# Detect heuristically: per-fill read of cfg.cores[X].Y when Order/Position/Event also passed
# (operator reviews; less mechanical than A1/A2)
```

False-positive exemptions documented in `MANUAL_FIELDS_INVENTORY.md` Section C with:
- Subsystem name + field name
- Rationale (one of: pre-resolve impossible AT THIS SITE; genuine subsystem-internal aggregate; cfg value is uniform-by-design across instances)
- Migration trigger (if TRANSITIONAL)

### Related classes

- **Class 25** (Scope-erosion in per-core consumer function) — sister at READ-SITE layer (consumer reads wrong scope). Class 27 is at CACHE-DESIGN layer (the scope doesn't exist in the cache structure). Class 25 + Class 27 close together at `.F.4c.3` via cfg-scope-discipline + decision-time-data-binding + Check 6 + Check 7 CI.
- **Class 26** (Global consumer reading per-core field) — sister; Class 27 is the structural pre-condition that makes Class 26 silent. Eliminating Class 27 sources eliminates many Class 26 sites by construction.
- **Class 18** (Mirror-incomplete) — same family of "subsystem state mirrors cfg structure"; Class 27 is the specific scalar-flatten variant.
- **Class 24** (Capability-cfg surface mismatch) — sister at CFG-SURFACE layer; Class 27 is at CONSUMER-STATE layer. Both close at `.F.4c.3` ship.

### Cross-references

- `DESIGN_SPECS/decision-time-data-binding-pattern.md` — full principle + design space + reference implementations
- `DESIGN_SPECS/cfg-scope-discipline.md` § "Pattern 1 — OMS per-core fee_rate cluster" — the cfg-scope side of the same fix
- `DESIGN_SPECS/cache-layout-discipline-for-hot-side-structs.md` — companion (subsystem state layout consideration)
- `DESIGN_SPECS/hot-side-array-element-alignment-for-sparse-access.md` — composes (per-instance cache fallback layout)
- `DESIGN_SPECS/postloadsetup-registry-pattern.md` — fallback mechanism integration (cfg-reload sync hook)
- `tools/check_per_core_registry_integrity.py` Check 7 — CI enforcement
- `DOCS/MANUAL_FIELDS_INVENTORY.md` Section C — exemption registry
- `CoreFrameworks/OrderManager.hpp` (post-`v5.15.5.F.4c.3` WIP2d-1.B.1) — canonical first application
- CLAUDE.md item 31 + DESIGN_PHILOSOPHY § 11 framework-selection criteria — meta-principle


## Class 28 — Branchy SP/HP dispatch when branchless feasible (variance injection in determinism-prioritizing path)

**Detected:** 2026-05-15 (during v5.15.5.F.4c.3 WIP2d-1.B.0d hand-wave audit; surfaced after Caramel called out the framing "branch is fine because predictor handles it" applied to HandleFill BUY/SELL dispatch).
**Severity:** HIGH — variance injection in code path that values determinism; p99-vs-p50 spread widens; cumulative tail latency exposure.

### Recurring symptom

Slow-path, hot-path, drainer, or producer-fan-out code dispatches on a runtime enum value (Order type, Order state, Cmd type, strategy enum, regime enum, bandit algorithm, ...) via `if/else if` chain or `switch` statement. The compiler lowers to conditional jumps. Branch predictor catches predictable patterns well (90%+ correct prediction on alternating BUY/SELL); rare access patterns get higher mispredict rate.

Even at low mispredict rates (5-15%), the cost compounds in real-world HFT measurement: pipeline flush + dependent op cascade + possible L1i miss = 30-100ns per mispredict event (vs textbook 5-15ns single-stall number).

The deeper issue: branches inject VARIANCE. Even when AVERAGE is acceptable, p99 vs p50 spread widens. For HFT, that variance compounds through downstream pipeline stages — variable engine latency means variable tick-to-trade latency means harder reasoning about end-to-end timing.

Distinct from Class 27 (scalar cfg-mirror cache): Class 27 is a STATE-DESIGN bug (subsystem state has wrong shape); Class 28 is a DISPATCH-CODE bug (branch where branchless was feasible).

Concrete first-canonical instance: `OrderManager_HandleFill` if/else dispatch on Order type (BUY/SELL) + dedup branch on Order state (FILLED → return). Both are runtime data-dependent dispatch on drainer per-fill path. Both expressible as branchless via 2D `[state][type]` dispatch table.

### Root cause

Two compounding patterns:

1. **Cultural default of branchy dispatch.** `if/else if` chains are the natural C++ expression of multi-way dispatch. Function pointer tables and computed-goto are less idiomatic; reach for them only when explicitly thinking about branchless.

2. **Throughput-frame justification.** "Branch predictor handles predictable patterns at ~0ns" is TRUE on average but ignores variance + real-world mispredict cost. The hand-wave: defaulting to branch because the average looks fine, without thinking about p99 / consistency / variance injection.

The framing failure is the bug seed. Codebases that prioritize determinism need branchless-by-default discipline; defaulting to branch and only converting when "we measure a problem" lets variance accumulate invisibly.

### Structural fix

**Function pointer table dispatch (Pattern 1) for single-enum dispatch.** See `DESIGN_SPECS/branchless-dispatch-discipline.md` § Pattern 1.

```cpp
template <unsigned F>
static constexpr FillHandler<F> g_fill_handlers[4] = {
    handle_buy_fill<F>, handle_sell_fill<F>, handle_buy_fill<F>, handle_sell_fill<F>
};
g_fill_handlers<F>[Order_GetType(o)](oms, o, fill_price, fill_qty);
```

**2D state×type dispatch table (Pattern 2) for composite dispatch.** Collapses dedup + type dispatch into ONE branchless lookup; terminal states map to `handle_noop` handler.

```cpp
template <unsigned F>
static constexpr FillHandler<F> g_fill_dispatch[16][4] = { /* ... */ };
g_fill_dispatch<F>[Order_GetState(o)][Order_GetType(o)](oms, o, fill_price, fill_qty);
```

**Mask-select (Pattern 3) for binary with cheap both-sides** (already-canonical for BITMAP_* operations).

**Pre-resolution at decision time (Pattern 4) for cfg-derived dispatch** — eliminates per-fill cmov entirely. See `decision-time-data-binding-pattern.md`.

**FORBIDDEN going-forward:**

```cpp
// FORBIDDEN — branchy dispatch on runtime enum in SP/HP/drainer code
if (Order_GetType(o) == ORDER_MARKET_BUY) {
    /* BUY handler body */
} else if (Order_GetType(o) == ORDER_MARKET_SELL) {
    /* SELL handler body */
}

// FORBIDDEN — switch on runtime enum in SP/HP/drainer code (same shape, different syntax)
switch (Order_GetType(o)) {
    case ORDER_MARKET_BUY:  /* ... */ break;
    case ORDER_MARKET_SELL: /* ... */ break;
}
```

Closed at `v5.15.5.F.4c.3` WIP2d-1.B.1 — first canonical close via HandleFill 2D state×type dispatch table. OrderManager_HandleFill if/else chain DELETED; replaced with `g_fill_dispatch[state][type](...)`.

### Prevention (going-forward rule + audit + CI)

Codified at `DESIGN_SPECS/branchless-dispatch-discipline.md` (NEW at `.F.4c.3` WIP2d-1.B.0d).

> **Branchless dispatch preferred for SP/HP data-dependent code.** Trigger: data-dependent dispatch (if/else or switch on runtime enum) on slow-path, hot-path, drainer, or producer-fan-out code → convert to fn pointer table (Pattern 1) or 2D state×type table (Pattern 2) or pre-resolve at decision time (Pattern 4). Branch is acceptable ONLY when predicate is boot-time-only OR `__builtin_expect`-tagged rare OR `if constexpr` compile-time OR genuine binary predicate with no alternative computation.

Audit skill enforcement:
- `/hft-audit` extended at `.F.4c.3` WIP2d-1.B.0d with **Branchless dispatch opportunity scan** section — scans SP/HP/drainer code for if/else chains + switch statements on runtime enums; flags candidates for fn pointer table conversion; outputs severity-classified findings report
- `/dod-audit` references `branchless-dispatch-discipline.md` as a missed-pattern check
- `/bug-check` picks up Class 28 codification (registry-driven; no skill edit needed)
- `/precoding-audit-gate` audit_set extended to include `/hft-audit` when SP/HP/drainer changes are in plan scope

Anti-pattern grep signatures (for `/hft-audit` integration):

```bash
# A1: if/else if chain dispatching on Order type / state / cmd type in SP/HP code
rg -nP '(?s)if\s*\(\s*(Order_GetType|Order_GetState|cmd\.type|cmd_type|.*\.state)\s*[=!]=\s*\w+\s*\).*?else\s+if' --type cpp CoreFrameworks/ ML_Headers/ Strategies/

# A2: switch on runtime enum in CoreFrameworks/ML_Headers/Strategies SP/HP paths
rg -nP 'switch\s*\(\s*(Order_GetType|Order_GetState|cmd\.type|.*\.state)\s*\)' --type cpp CoreFrameworks/ ML_Headers/ Strategies/

# A3: if-chain on bandit_algorithm or strategy_id in SP/HP body
rg -nP 'if\s*\(\s*(bandit_algorithm|strategy_id|regime|strategy)\s*==' --type cpp CoreFrameworks/ ML_Headers/ Strategies/
```

False-positive exemptions (documented per case):
- Boot-time / Init-time branches — cost amortized to zero per fill
- `__builtin_expect`-tagged rare branches per latency-path-discipline.md Rule 4 (steady-state cost ~0ns)
- `if constexpr` compile-time elision — no runtime cost
- Genuine binary predicate without alternative computation (e.g., null-ptr check)
- Test fixtures / non-production code paths

### Related classes

- **Class 27** (Scalar cfg-mirror cache) — sister; both are "default-to-easy thinking" anti-patterns. Class 27 is state-design layer; Class 28 is dispatch-code layer. Pre-resolution (Pattern 4) closes both classes when the dispatch is on cfg-derived values.
- **Class 14** (Plan API drift) — sister at API-stability layer; both classes recur when discipline defaults are not enforced.
- **Class 18** (Mirror-incomplete) — same family of "multi-site code that should compose cleanly"; Class 28 is "multi-branch dispatch that should be tabular."

### Cross-references

- `DESIGN_SPECS/branchless-dispatch-discipline.md` — full discipline definition + patterns + cost framework + decision matrix
- `DESIGN_SPECS/decision-time-data-binding-pattern.md` — sister; Pattern 4 (pre-resolution) is the strongest branchless form
- `DESIGN_PHILOSOPHY.md` § 4 Latency cost framework (updated 2026-05-15) — real-world mispredict cost basis
- `DESIGN_PHILOSOPHY.md` § 6 Concurrency family — branchless mask compute principle
- `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` Rule 8 (branchless for data-dependent dispatch)
- `CoreFrameworks/OrderManager.hpp` (post-`v5.15.5.F.4c.3` WIP2d-1.B.1) — canonical first close (2D dispatch table)
- CLAUDE.md item 18 + item 28 — latency discipline references
