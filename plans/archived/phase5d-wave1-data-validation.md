# Phase 5d — Wave 1: Data + selection validation

**Time budget:** ~30 minutes · **Commits:** 5 · **Risk:** low (UI + preflight only, no hot path or feature path edits)

## Context anchors — files to read FIRST

Before writing any code, read these files (in order):

```
plans/phase5d-master.md                  ← failure catalog, sequencing, anti-drift discipline
Backtest/BacktestPanels.hpp              ← all GUI panels (DataPanel, RunControl, Training)
Backtest/BacktestEngine.hpp              ← Backtest_Run + BacktestData_Load (load path)
Backtest/BacktestSharded.hpp             ← sharded path (where features ARE NOT collected)
CoreFrameworks/ControllerConfig.hpp      ← engine_mode field, ENGINE_MODE_SHARDED constant
Limits.hpp                                ← MAX_DATA_FILES = 2048
```

Also useful for context:

```
DataStream/EngineTUI.hpp                  ← SESSION_NAMES (existing centralized table)
ML_Headers/ModelInference.hpp             ← MODEL_NUM_FEATURES + label_table reference patterns
```

Branch state expected: `experiment/phase5-zoo` at HEAD `ab24d14` or later. If different, read `git log --oneline -10` to verify all Phase 5b/5c commits are present.

## Failure mode IDs covered

From `phase5d-master.md`:

- 1.1 — engine_mode=sharded + Collect Features = 0 samples
- 2.1 — selected file deleted between Scan and Run
- 2.2 — selected file empty
- 2.3 — date gaps in selection
- 2.4 — malformed lines (log only)
- 2.5 — total ticks < min_warmup × buffer
- 2.8 — ✅ **mostly done** — class distribution surfaced by label-kind-aware sample panel (`cd2936d`); commit 5 below is now optional / can be downgraded to a 1-line stderr summary
- 7.7 — two backtest.cfg files (build_gui dup)

## Status update (2026-04-25 afternoon)

- **Commit 5 (class distribution report)** — partly redundant. The sample panel in `BacktestPanels.hpp` now branches by label kind: binary shows `+/-/neutral`, multiclass shows per-class histogram, regression shows `range/mean/σ`. The original plan was a stderr report at end of Collect Features; this is now duplicative of the always-visible panel. Either skip, or downgrade to a single-line summary line `[backtest] label distribution: ...` written when `Backtest_Run` finishes (still useful for non-GUI runs and log review).
- **All other commits (1-4) untouched** — still relevant and high-value.

NEW (added during plan audit, 2026-04-25):
- **2.9 — progress bar updates too rarely (every 16383 ticks)** — at 4.6M total
  ticks, first update fires after ~0.4% of run, user thinks it's frozen.
  Fix: update every 1024 ticks instead of every 16383. Cost: more atomic
  writes to volatile int, negligible at slow-path frequency. Alternative:
  also update immediately after each file load completes (so user sees
  "1/90 files" type granularity). Both, ideally.
- **2.10 — Training panel "Collect Features" missing Cancel button** —
  introduced when the disabled+status indicator was added. Run Control
  panel has Cancel using the same cancel_flag, but Training panel users
  expect the Cancel right there. Fix: add a Cancel button next to the
  "running... (X%)" status text. 3 lines.

## Commit plan (in order)

### Commit 1: Sharded mode warning before Collect Features (1.1)

**Goal:** when user clicks Collect Features but `run_control->config.engine_mode == ENGINE_MODE_SHARDED`, show a clear warning + skip the no-op run.

**File:** `Backtest/BacktestPanels.hpp` — Training panel Collect Features button handler.

**Approach:**
1. Read `run_control->results.config_used.engine_mode` after backtest start (or read from cfg directly before kicking off worker).
2. If sharded, log to stderr: `[TRAIN] WARNING — engine_mode=sharded, sharded backtest does not collect features. Switch to engine_mode=single_core in backtest.cfg, or use Run Backtest for stats-only mode.`
3. Skip starting the worker thread.
4. Set `state->status_msg` to the warning so it appears in the Training panel UI.

**Anti-drift check:** This is purely a precondition guard. No feature pipeline edits.

**Testing:** Manual — set engine_mode=sharded, click Collect Features, verify warning + no run.

### Commit 2: backtest.cfg symlink consolidation (7.7)

**Goal:** eliminate two backtest.cfg files (project root + build_gui copy). Symlink `build_gui/backtest.cfg → ../backtest.cfg` matching the existing engine.cfg pattern.

**File system change only — no code:**

```bash
rm build_gui/backtest.cfg
ln -sf ../backtest.cfg build_gui/backtest.cfg
ls -la build_gui/backtest.cfg  # verify symlink target
```

**Anti-drift check:** symlink only, no compiled artifact change.

**Testing:** Manual — `cd build_gui && ./foxml_suite`, verify Settings panel shows fields from project-root backtest.cfg.

### Commit 3: Date gap detection in Data panel (2.3)

**Goal:** when user has files selected, parse YYYY-MM-DD from filenames, detect missing days in the selected range, show yellow warning row.

**File:** `Backtest/BacktestPanels.hpp` — `GUI_Panel_DataBrowser` after the file count display.

**Approach:**
1. Helper function `static int parse_date_yyyymmdd(const char *filename, int *y, int *m, int *d)` that uses `sscanf("%d-%d-%d", ...)`.
2. Walk selected files in order, convert each to a Julian day count (or use mktime).
3. Compute first_selected_jd, last_selected_jd. Expected count = last - first + 1.
4. If expected_count > selected_count, gaps exist.
5. Display: `ImGui::TextColored(yellow, "⚠ %d-day gap(s) in selection — features near gaps may be contaminated", expected_count - selected_count);`
6. Optional enhancement: list the first 3 missing dates.

**Anti-dust check:** Use `parse_date_yyyymmdd` once, not duplicated logic. No magic strings (filenames are user-provided).

**Anti-drift check:** UI display only.

**Testing:** Manual — select 5 files with a known gap, verify warning shows.

### Commit 4: Preflight checks before any backtest start (2.1, 2.2, 2.4, 2.5)

**Goal:** before starting Backtest worker thread, validate:
- Each selected file exists (stat check)
- Each selected file is non-zero size
- Total estimated ticks > min_warmup_samples × 4 (sanity)

**File:** `Backtest/BacktestPanels.hpp` — both Run Backtest and Collect Features handlers (or extract a shared `static int Backtest_Preflight(BacktestRunConfig*, ControllerConfig*)` helper).

**Approach:**
1. New function `Backtest_Preflight(const BacktestRunConfig *cfg, int min_warmup)` returns 0 on fail, 1 on pass.
2. Iterate `cfg->data_paths[0..num_data_files]`:
   - `stat(path)` — fail if !exists or size==0
   - Sum sizes (rough estimate ~150 bytes per Binance aggTrade row)
3. Estimated total ticks = total_size / 150. If estimated < min_warmup × 4, fail.
4. On any fail: log to stderr with specific reason, set `state->status_msg`, return 0.
5. Caller checks return code; only starts worker if 1.

**Anti-dust check:** Single helper used by both Run Backtest and Collect Features. No duplicated stat calls.

**Anti-drift check:** Preflight reads cfg, doesn't modify. Backtest internals unchanged.

**Testing:** Manual — delete a selected file, click Run Backtest, verify failure log + no run start.

### Commit 5: Class distribution report after Collect Features (2.8)

**Goal:** post-feature-collection (in Backtest_Run after labels are computed), log the label class distribution. Helps catch "all stable" failures before training.

**File:** `Backtest/BacktestEngine.hpp` — after the label computation pass (around line 660 where labels are filled in).

**Approach:**
1. After labels populated, count unique label values + their counts.
2. For binary labels (0/1): print `[TRAIN] label distribution: 0=X.X% 1=X.X% (N samples)`
3. For multiclass (REGIME, PEAK_VALLEY_STABLE): bucketed counts per class.
4. For regression (FORWARD_PNL): print min/max/mean instead.
5. Determine label type from `run_cfg->label_type` and dispatch accordingly. Use existing `label_table[].num_classes` field added in Phase 5b for the dispatch.
6. Warn if any class < 5% (extreme imbalance, training will struggle).

**Anti-dust check:** Use `label_table[].num_classes` (existing). No hardcoded class counts per label.

**Anti-drift check:** Logging only, no data modification.

**Testing:** Manual — Collect Features with peak/valley label, see distribution log.

## Verification (after EACH commit)

```bash
cmake --build build -j$(nproc)            # ANSI engine + tests
cmake --build build_gui -j$(nproc)        # engine_gui + foxml_suite
build/controller_test                      # must say 279 passed, 0 failed
```

Plus the anti-drift checks from `phase5d-master.md`:

- [ ] `ModelFeatures_Pack` UNCHANGED
- [ ] `RollingStats_Push` UNCHANGED
- [ ] `ExecutionCore_Tick` UNCHANGED
- [ ] FEAT_* constants UNCHANGED

## Verification (after ALL 5 commits)

Manual end-to-end test in foxml_suite:

1. Restart foxml_suite — should boot with no warnings
2. Data panel: scan, click Last 90, verify gap detection (if any gaps in 90 days)
3. Try Collect Features in single_core mode → should run, show class distribution at end
4. Set engine_mode=sharded in Settings → save → click Collect Features → should warn + skip
5. Reset to single_core, delete a selected file via terminal, click Run Backtest → should preflight-fail with clear message

## Definition of done

- [ ] All 5 commits land cleanly on `experiment/phase5-zoo`
- [ ] 279/279 tests pass after each
- [ ] Manual end-to-end test passes (above)
- [ ] No new compile warnings
- [ ] Master plan updated: each ID (1.1, 2.1-2.5, 2.8, 7.7) marked done

## Tag at end of Wave 1

```bash
git tag wave1-complete
```

This anchors the start of Wave 2.
