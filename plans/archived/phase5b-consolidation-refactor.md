# Phase 5b — Consolidation refactor (DRY sweep)

last updated: 2026-04-25

## Intent

Reduce technical debt by eliminating duplicated string arrays, scattered name tables, and ad-hoc magic constants. The goal is to make the "add a new X" workflow touch as few files as possible — ideally `<5 places` for any X.

Type of work: **refactoring** (Fowler's sense — change structure, not behavior). Specifically:
- DRY (Don't Repeat Yourself) cleanup
- "Magic string" → "symbolic constant" replacement
- "Shotgun surgery" code-smell → table-driven design

**No behavior change is allowed.** Outputs must be byte-identical to pre-refactor for any given input. Verification: `controller_test` passes 279/279 after every commit. Run-time A/B against pre-refactor binary on synthetic ticks for spot checks.

## Scope philosophy

In: any duplicated table or magic string with **3+ copies** OR with known inconsistency between copies.
Out: switch dispatch ladders (Tier 3 — these are real architectural questions, defer until after Phase 6).
Out: the `engine_gui` GUI panel layout — independent concern, not relevant to ML pipeline.

## Status of each item before we start

| dust | edit points | tier | severity |
|---|---:|---:|---|
| Strategy short names ("MR/MOM/DIP/ML/EMA") | 8 places | 1 | high — `STRATEGY_SHORT_NAMES[]` global already exists, just unused |
| Strategy full names ("MeanReversion" etc.) | 1 place + missing global | 1 | medium |
| Session names ("ASIA/EU/US/OVERNIGHT") | 3 places + inconsistency bug ("OVER" vs "OVERNIGHT" in ChartPanel) | 1 | high — already wrong in wild |
| Gate reason names | 4 places (TUIAnsi×2, DashboardPanels, BacktestEngine) | 1 | medium |
| TUIAnsi block characters (`"▁▂▃▄▅▆▇█"`) | 2 places, same file | 1 | low (drift unlikely, but trivial fix) |
| `label_names[]` in BacktestPanels duplicates `label_table[].name` | 1 place but new dust from Phase 5 | 2 | high — drift on next label add |
| `is_multiclass` / `num_classes` hardcoded in BacktestPanels | 1 function, 2 hardcodes | 2 | medium — drift on next multiclass |
| `CoreModelZoo` role list (struct + init + free + load) | 3 places, same file | 2 | low — file-local |
| Strategy dispatch switch | 3 places (PortfolioController×2 + StrategyParameters×1) | 3 | defer to Phase 6+ |
| Backend dispatch (`#ifdef USE_XGBOOST` ladders) | 4-5 places | 3 | defer until adding ONNX |

## Plan — sequential commits on `experiment/phase5-zoo`

Each commit is independent, builds clean, tests pass before the next starts.

### Commit 1: strategy short names (the big one)

**Action:** all 7 local `sn[]` / `snames[]` / `strat_labels[]` arrays → use the existing `STRATEGY_SHORT_NAMES[]` global from `Strategies/StrategyInterface.hpp`.

**Files touched:**
- `CoreFrameworks/PortfolioController.hpp` (lines 567, 1254 — drop both arrays, use global)
- `GUI/DashboardPanels.hpp` (lines 141, 605, 928 — drop all three)
- `GUI/ChartPanel.hpp` (line 825 — drop)
- Need to make sure `StrategyInterface.hpp` is included where it isn't already (most files already have it transitively).

**Verification:**
- Compile clean (engine, engine_gui, foxml_suite, controller_test)
- Visual diff on TUI / GUI: strategy column shows same labels
- 279/279 tests still pass

**Diff size estimate:** ~25 lines removed, ~2 #include lines added if any. Small and clean.

### Commit 2: strategy full names

**Action:** add `STRATEGY_FULL_NAMES[]` global to `StrategyInterface.hpp`. Replace `strat_names[]` in `PortfolioController.hpp:939`.

**Files touched:**
- `Strategies/StrategyInterface.hpp` (+1 array, ~3 lines)
- `CoreFrameworks/PortfolioController.hpp:939` (-1 array, +1 use of global, ~2 lines)

**Diff size:** ~5 lines net.

### Commit 3: session names + fix the OVERNIGHT/OVER inconsistency

**Action:** create `SESSION_NAMES[NUM_SESSIONS]` in a shared header (probably `DataStream/EngineTUI.hpp` near where `current_session` is computed). Use everywhere. Fix `ChartPanel.hpp:395` which currently says `"OVER"` instead of `"OVERNIGHT"`.

**Files touched:**
- `DataStream/EngineTUI.hpp` (+1 array if not already there, +constant for NUM_SESSIONS)
- `DataStream/TUIAnsi.hpp:367` (drop local array)
- `GUI/ChartPanel.hpp:395` (drop local + fix the OVER bug)
- `GUI/DashboardPanels.hpp:113` (drop local)

**Open question:** ChartPanel uses `"OVER"` because it might be a column-width thing. If the chart panel needs a 4-char form, the array should be the full names AND we add a `SESSION_NAMES_SHORT[]` companion. Decide at refactor time.

**Diff size:** ~10 lines.

### Commit 4: gate reason names

**Action:** create `GATE_REASON_NAMES[]` table. Locate it next to where `GATE_REASON_*` constants are defined (search for `GATE_REASON_COST` to find).

**Files touched:**
- The defining header (TBD — probably `CoreFrameworks/PortfolioController.hpp` or a new `GateReasons.hpp`)
- `DataStream/TUIAnsi.hpp:646, 1075` (both drops)
- `GUI/DashboardPanels.hpp:418` (drop)
- `Backtest/BacktestEngine.hpp:676` (drop — 4th copy spotted in second sweep)

**Diff size:** ~15 lines.

### Commit 5: TUIAnsi block characters

**Action:** lift the 8-char block array to file-scope constant in TUIAnsi.hpp. Use in both render functions.

**Files touched:**
- `DataStream/TUIAnsi.hpp` only (lines 271, 309 collapse to one constant)

**Diff size:** ~5 lines.

### Commit 6: Phase 5 polish — `LabelDef.display_name` + `LabelDef.num_classes`

**Action:**
1. Extend `LabelDef` struct: add `const char *display_name` and `int num_classes` fields.
2. Update `label_table[]` entries to populate the new fields.
3. `BacktestPanels.hpp` Training panel:
   - Drop the `label_names[]` hardcoded array, derive from table at runtime
   - Replace `is_multiclass` / `num_classes` hardcoded if-ladder with `label_table[label_type].num_classes >= 2`

**Files touched:**
- `Backtest/LabelFunctions.hpp` (extend struct + 8 entries)
- `Backtest/BacktestPanels.hpp` (drop hardcoded array, use table)

**Diff size:** ~30 lines. Bigger but isolated.

### Commit 7: zoo role list cleanup (file-local)

**Action:** keep deferred unless we need to add a 5th role this week. The 3-way duplication in CoreModelZoo.hpp is file-local and easy to grep. Wait until we have a real reason (e.g., adding `liquidity_model` or `volatility_model`) — then refactor to enum + table at the same time.

**Skip this commit** — re-evaluate after Phase 7 ship.

## Order of operations rationale

1-2 are pure consolidation around an existing global → safest, smallest diffs first.
3 includes a real bug fix (OVERNIGHT/OVER) so it's worth doing while context is fresh.
4-5 are file-local fixes, low risk.
6 is the largest diff but it's the one we know will pay off because it's NEW dust we just made.

If any commit fails verification, **stop and investigate** — don't pile more refactoring on top of a broken state.

## Verification checklist (run after every commit)

```bash
cmake --build build_gui -j$(nproc)        # both engine_gui + foxml_suite
cmake --build build -j$(nproc)            # ANSI + tests
build/controller_test                      # must say 279/279
```

For commits 1, 3 (visible UI changes): also visually check engine_gui briefly to confirm strategy labels and session labels look identical to pre-refactor.

## Rollback strategy

Branch is `experiment/phase5-zoo`. Each commit is small enough to `git revert <hash>` cleanly if needed. Worst case: `git reset --hard 42a4b1b` returns to clean Phase 5 state with all the zoo work intact, refactor lost.

If we want to be paranoid about any single commit: tag before each one (`git tag pre-commit-N`), revert by tag if needed.

## Out of scope (Tier 3 deferred)

The big architectural refactors are NOT in this plan:

- **Strategy dispatch consolidation** — three switch ladders could become a vtable, but it's a real architectural decision affecting the dispatcher signature. Wait until adding the next strategy.
- **Backend dispatch consolidation** — `Model_Load/Predict/PredictMulti/Free` each have `#ifdef USE_XGBOOST`/`USE_LIGHTGBM` ladders. Vtable-based registration cleans this up but only matters when adding ONNX/TFLite. Defer.
- **Regime → Strategy mapping** — currently a switch in `Regime_ToStrategy`. Could be a table. Low ROI right now (only 5 regimes).
- **GUI panel registration** — each panel is a separate function with its own state struct. Could be made data-driven. Defer until UX changes more frequently.

These get their own plans when they become hot.

## Definition of done

- [ ] All 6 commits land on `experiment/phase5-zoo` cleanly
- [ ] `controller_test` 279/279 after each
- [ ] No new compiler warnings introduced
- [ ] Diff total: <100 lines NET (most of this is deletions)
- [ ] Adding a new strategy now touches <5 places (verified by grep audit on the new state)
- [ ] Adding a new label now touches <3 places
- [ ] Adding a new session, regime, or gate reason touches 1 place

## Estimated time

- Commits 1-5: ~30 minutes total (mostly mechanical sed-like changes + grep verify)
- Commit 6: ~30-45 minutes (touches more code, adds the new struct fields + propagation)
- Verification + smoke test: ~15 minutes

**Total: ~1.5-2 hours of focused work.**
