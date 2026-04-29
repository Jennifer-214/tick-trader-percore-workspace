# Legacy Deprecation Cleanup — TODO Tracker

**Created:** 2026-04-27
**Status:** Living document. Edit as items ship.
**Context:** After v4.7.0, sharded engine is feature-complete vs legacy.
Legacy backtest body deleted (E.7); legacy LIVE engine still runs when
`engine_mode=single_core` but is runtime-warned + deprecated. Time to
catalog the cleanup so it doesn't accumulate forever.

## Doctrine

**What stays for now:**
- `PortfolioController` struct + most of its slow-path helpers — used
  by legacy strategy unit tests in `controller_test.cpp` (regression
  fixtures we don't want to lose) and the `BacktestStats_Compute`
  helper that takes a `PortfolioController*` reference.
- `parity_harness.cpp` — one-shot diagnostic, useful as a "what
  changed between sharded and legacy" reference if anyone resurrects
  legacy. Not load-bearing but cheap to keep.

**What can go in cleanup passes:**
- Anything that ONLY the legacy live engine consumes
- TUISnapshot fields that ANSI TUI uniquely renders
- Cfg fields that are parsed-but-ignored
- Stale plan docs that reference deleted phases

## Cleanup items by priority

### Tier 1 — Safe, mechanical, ~½ day total

These are pure-deletion or rename items with no behavioral risk.

#### 1a. Drop `engine_mode` cfg parser entirely
**Where:** `CoreFrameworks/ControllerConfig.hpp` lines ~1003-1010 (parser
block), `~363` (struct field), `~37` (constants `ENGINE_MODE_SINGLE_CORE`
+ `ENGINE_MODE_SHARDED`).
**Why:** Parsed-but-ignored since E.7. The cfg field exists so user
cfgs setting `engine_mode=single_core` don't fail to load (one release
cycle of grace). After this drop, the field is removed; user cfgs
with the line will produce an "unknown key" warning (or whatever the
parser does with unknown keys — verify pre-drop).
**Risk:** Almost zero. User cfgs may need a one-line edit if they
explicitly set `engine_mode=...`.
**Tests:** ensure `controller_test` still passes (it shouldn't reference
engine_mode after this change).

#### 1b. Delete `tests/parity_harness.cpp` + CMake target
**Where:** `tests/parity_harness.cpp`, `CMakeLists.txt` lines 184-194 (the
`add_executable(parity_harness ...)` block).
**Why:** Compares legacy-vs-sharded; legacy backtest is gone, so it
literally cannot run anymore (the SINGLE_CORE branch in `Backtest_Run`
is deleted). Delete to remove dead code.
**Risk:** Zero — never run as part of test suite.
**Bonus:** removes one CMake target, faster `cmake -B` reconfigure.

#### 1c. Drop `BacktestSnapshot_Copy` + `Backtest/BacktestSnapshot.hpp`
**Where:** `Backtest/BacktestSnapshot.hpp` (entire file, ~30 LOC).
**Why:** Documented in CLAUDE.md FoxML Suite Code Key as "obsolete after
Track E — sharded backtest calls `TUI_CopySnapshotSharded` directly."
The file is a thin wrapper around `TUI_CopySnapshot(ctrl, ...)` — only
useful for the deleted legacy backtest body.
**Risk:** Zero if no caller remains. `grep -r BacktestSnapshot_Copy`
should return only the file itself + comments referencing it.

#### 1d. Stale comments + dead doc references
- CLAUDE.md "Adding a new TUI/GUI display field" step 4 says "if ANSI
  TUI needed" — remove the qualifier since ANSI is deprecated.
- Several comments still reference "post-coding cN" which referred to
  pre-Track-E phasing; obsolete labels.
- `DOCS/CHANGELOG.md` v4.0.x rows reference legacy specifically; rephrase
  if/when legacy live is removed.

### Tier 2 — Bigger, careful, ~1 day total

These touch shared code paths and need care.

#### 2a. Audit + remove stale `TUISnapshot` fields
**Where:** `DataStream/EngineTUI.hpp` `TUISnapshot` struct.
**Why:** After Track E.7 (sharded-only backtest path), the GUI
`DashboardPanels.hpp` and ANSI `TUIAnsi.hpp` may consume different
subsets of `TUISnapshot`. Fields that ONLY the ANSI renderer reads
become dead weight in the snapshot copy + GUI build.
**How:** grep each `TUISnapshot::` field for consumers. If only
`TUIAnsi.hpp` references it, mark `// [legacy ANSI only — delete with
TUIAnsi]`. If unused entirely, delete.
**Risk:** Medium — a wrongly-deleted field crashes the GUI silently
(field reads garbage from struct padding). Build with
`-Wmissing-field-initializers` to catch.
**Effort:** ~2-3 hours. Worth it: the snapshot is on the hot-ish
slow-path; smaller struct = less memcpy.

#### 2b. Delete `DataStream/TUIAnsi.hpp` entirely + `build/engine` ANSI binary
**Where:** `DataStream/TUIAnsi.hpp` (entire file, ~1259 LOC),
`CMakeLists.txt` `add_executable(engine main.cpp)` block (build/ target),
`build.sh` references to `build/`.
**Why:** Already marked deprecated for production. Useful for headless
operation BUT `engine_gui` runs headless too if you don't init the GUI.
Once an `engine_gui --headless` mode exists, ANSI binary is fully
redundant.
**Pre-req:** add headless mode to `engine_gui` (suppress GUI thread
spawn when `--no-gui` or similar). Small change.
**Risk:** Medium — anyone running `./engine` directly loses that
binary. Document migration in changelog.
**Effort:** ~½ day including the headless flag.

#### 2c. Drop legacy strategy `_Adapt` + `_ExitAdjust` slow-path code
**Where:** `Strategies/MeanReversion.hpp`, `Strategies/Momentum.hpp`,
`Strategies/SimpleDip.hpp`, `Strategies/EmaCross.hpp`,
`Strategies/MLStrategy.hpp`. Each file has functions that the LEGACY
`PortfolioController_StrategyDispatch` invokes per slow path.
**Why:** Sharded uses `Strategy_BuildParameters` from
`StrategyParameters.hpp` exclusively. The `_Adapt` / `_ExitAdjust`
functions only run from `PortfolioController_Tick`'s slow path, which
no longer runs in backtest (E.7 deleted that). Live legacy still runs
them.
**Pre-req:** delete legacy live engine (Tier 3 below).
**Effort:** ~1-2 hours per strategy × 5 = ½ day after pre-req.

### Tier 3 — Big, removes legacy live entirely, ~1 day

Only after Tier 2 + you've decided you'll never want legacy live again.

#### 3a. Delete legacy live engine
**Where:** `main.cpp` lines that handle `engine_mode == ENGINE_MODE_SINGLE_CORE`
(roughly lines 200-1000-ish — the legacy live path BEFORE the
`EngineSharded_Run` dispatch). `PortfolioController_Init` /
`_Tick` / `_DrainExits` / `_HotReload` callsites.
**Why:** Sharded is the production engine; legacy live runtime-warns
already. Removing the path simplifies main.cpp considerably.
**Risk:** High if you ever want legacy back. Tag `pre-legacy-live-removal`
before doing this.
**Pre-req:** verify nothing in the live infra (depth recorder,
notify, snapshot v8) has a code path that ONLY runs in legacy.
**Effort:** ~½ day to delete + ½ day to test.
**Net deletion:** ~700-1000 LOC.

#### 3b. Delete `PortfolioController` struct + `PortfolioController.hpp` body
**Where:** `CoreFrameworks/PortfolioController.hpp` (~2000 LOC).
**Pre-reqs:**
- Tier 3a complete (no legacy live engine)
- Migrate `BacktestStats_Compute` to read from sharded `EventLoopState` /
  `OrderManagerState` instead of `PortfolioController*`
- Migrate or delete legacy strategy unit tests in `controller_test.cpp`
  (the regression fixtures that build a PortfolioController)
**Why:** Largest single legacy file. Dwarfs every other file in the
codebase. Removing it forces sharded-only for everything.
**Risk:** High. Many tests build a `PortfolioController` for state
fixtures.
**Effort:** ~1 day if Tier 3a is clean. ~2 days if test migration is
needed.
**Net deletion:** ~2000 LOC.

#### 3c. Drop `Backtest_Run` legacy wrapper
**Where:** `Backtest/BacktestEngine.hpp` `Backtest_Run` function (the
12-line thin wrapper from Track E.7).
**Why:** After Tier 3a + 3b, the wrapper is the only `Backtest_Run`
caller path. Rename callers to `tt::BacktestSharded_Run` directly,
delete the wrapper.
**Risk:** Low — pure rename in 2 callsites (`BacktestPanels.hpp:217`
and `BacktestEngine.hpp:1626` Sweep).
**Effort:** ~30 minutes.

### Tier 4 — Cosmetic, anytime

#### 4a. Update `plans/master-roadmap.md`
- Mark Track E + Wave 1 + Wave 2 + partial exits all DONE
- Update "remaining items" with the Tier 1-3 cleanups above
- Note that this file (legacy-deprecation-cleanup.md) is the cleanup tracker

#### 4b. Update `plans/post-edge-hunt-c-and-d.md`
- D.5 already moved to Track E.3 (noted)
- D.1, D.3 unblocked + shipped (Wave 1 + 2)
- D.2, D.4 shipped
- Re-state remaining items: C.3 only

#### 4c. CLAUDE.md "Active rollback tags" section
- Update with the new tags from this session: pre-track-e, pre-track-e-polish,
  pre-track-e3, pre-track-e7, pre-v4.5-wave1, pre-v4.6-wave2,
  pre-partial-exits.
- Drop the older v4.0-era tags if no longer relevant.

#### 4d. Drop `BacktestStats_Compute(stats, ctrl, ...)` if Tier 3b lands
- If PortfolioController is gone, this helper has no callers. Already
  noted "kept; harmless" in v4.7 changelog.

## Items NOT to clean up

These look like cleanup candidates but aren't:

- **`controller_test.cpp` legacy strategy unit tests.** They're
  regression fixtures — they catch bugs in strategy logic without
  depending on the full sharded pipeline. Migrate to sharded only if
  Tier 3b removes PortfolioController, otherwise keep.
- **`Strategies/RegimeDetector.hpp`.** Not legacy — single source of
  truth for `Regime_ComputeSignals`, used by both sharded paths.
- **`MeanReversion_Init`, `Momentum_Init`, etc.** Used by sharded
  Strategy_BuildParameters dispatcher (after Track E + post-cap they
  set the leg A primitives). Stay.
- **`OrderGates.hpp`.** Buy gate logic re-used by sharded BG_Evaluate.
  Stay.

## Open questions

1. **Headless `engine_gui --no-gui` mode** — needed before Tier 2b
   (ANSI TUI deletion). Worth doing? Or keep ANSI as the headless
   path and just delete its renderer churn?
2. **Legacy live engine deletion (Tier 3a)** — yes or no? Once gone,
   benchmark comparisons "vs legacy" are impossible. Worth it for the
   ~700-1000 LOC win?
3. **`plans/` doctrine** — currently gitignored. As the codebase
   matures, do these tracker docs belong somewhere committed (DOCS/
   ?) so future contributors see them? Trade-off: committing means
   they need to be polished + maintained.

## Order of operations

If we tackle this systematically:

1. **Tier 1 in one session** (~½ day) — pure mechanical cleanup, no
   risk. Ship as a single "v4.7.1 — legacy cleanup pass 1" commit.
2. **Tier 4 cosmetic items** anytime, batched into the same commit.
3. **Tier 2 in a focused session** (~1 day). Tag `pre-tui-cleanup`
   first.
4. **Tier 3** only when you've decided legacy live is truly gone.
   Multi-decision; needs explicit "I'll never want this back" buy-in.

## Why this matters

Right now the codebase has TWO mental models running in parallel:
"sharded is the spec" and "legacy is the benchmark." Track E E.7
collapsed backtest to one path; tier 3 above collapses live to one
path too. Each tier reduces the cognitive load when reading
unfamiliar code — fewer places where the question "wait, does
this run in sharded or legacy?" comes up.

Net of all tiers: ~3000-3500 LOC removed, plus all the conditional
logic + comments + grep noise. Worth ~1-2 focused sessions to land
across a few weeks.
