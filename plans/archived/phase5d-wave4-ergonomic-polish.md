# Phase 5d — Wave 4: Ergonomic polish + warnings

**Time budget:** ~30 minutes · **Commits:** 3 · **Risk:** low (UI/labels only)

## Context anchors — files to read FIRST

```
plans/phase5d-master.md                  ← catalog
plans/phase5d-wave3-compile-time-guards.md ← prior wave (verify wave3-complete)
Backtest/BacktestPanels.hpp              ← Save Run, Comparison, Run Name UI
GUI/SettingsPanel.hpp                    ← Settings panel header
foxml_suite.cpp                           ← which cfg the suite is editing
main.cpp                                  ← which cfg the engine is editing
```

Branch state expected: `experiment/phase5-zoo` at tag `wave3-complete`.

## Failure mode IDs covered

- 4.4 — Comparison Save Run while backtest still running
- 5.3 — Run Name reuse → silent overwrite
- 5.4 — Train but no `core_N_strategy=ml` → tooltip warning
- 6.4 — Walk-forward results auto-shown verification
- 6.7 — Settings: which cfg is being edited

## Commit plan

### Commit 11: Run Name overwrite detection + auto-suffix (5.3)

**Goal:** when user clicks Save Run with a name that already exists in `models/`, either show confirmation dialog OR auto-suffix `_v2`, `_v3`, etc. and inform.

**File:** `Backtest/BacktestPanels.hpp` — Save Run handler.

**Approach:**

1. Before mkdir + file copy, check if `models/{run_name}/` exists via `stat`.
2. If exists, walk `_v2`, `_v3`, ... until an unused name is found (cap at 99).
3. Update the run_dir + dst_model paths to use the new name.
4. Show in `state->save_msg`: `"Saved as {run_name_v2}/ (auto-suffix to avoid overwriting)"` so user knows.

**Alternative:** explicit overwrite confirmation dialog. Use `ImGui::OpenPopup` + modal. More complex but more explicit.

**Recommend the auto-suffix path** — simpler, no extra UI state, and the message tells the user what happened.

**Anti-dust check:** Single helper `static int find_next_run_suffix(const char *base)` if used in 2+ places.

**Anti-drift check:** Doesn't change saved bundle contents, only the directory name.

**Testing:** Manual — Save Run with name `test`, then again with `test`, verify second is `test_v2`.

### Commit 12: Settings panel header — which cfg is being edited (6.7)

**Goal:** users get confused about whether Settings edits engine.cfg (live trading) or backtest.cfg (backtest mode). Add a clear label.

**Files:**
- `GUI/SettingsPanel.hpp` — accept a `cfg_name` string parameter for header display
- `foxml_suite.cpp` — pass "backtest.cfg"
- `main.cpp` (engine_gui) — pass "engine.cfg"

**Approach:**

1. Extend `GUI_Panel_Settings(SettingsState *state, volatile sig_atomic_t *reload_flag, bool readonly = false, const char *cfg_name = "engine.cfg")`.
2. At top of panel: `ImGui::TextColored(FoxmlColors::comment, "Editing: %s", cfg_name);` followed by `ImGui::Separator();`.
3. Wire from foxml_suite (passes "backtest.cfg") and engine_gui (passes "engine.cfg").

**Anti-dust check:** No new array, just a string param.

**Anti-drift check:** UI label only.

**Testing:** Manual — open foxml_suite, see "Editing: backtest.cfg". Open engine_gui, see "Editing: engine.cfg".

### Commit 13: Comparison Save Run guard + walk-forward result auto-show (4.4, 6.4)

**Goal:** prevent Comparison Save Run while backtest still running (4.4); confirm walk-forward results display correctly after run (6.4).

**File:** `Backtest/BacktestPanels.hpp` — Comparison panel.

**Approach for 4.4:**

1. In `GUI_Panel_Comparison`, the "Save current run" button currently just checks `current->stats.total_trades > 0`. Add `&& !run_control->running` (need to thread run_control state in, or use a different signal).
2. Simpler: in `Comparison_SaveRun`, the function itself checks if results are stable (e.g., `state->complete && !state->cancelled` from Wave 2's cancelled field).
3. Wrap the Save button click in this check; show "Backtest in progress — results not stable yet" if not ready.

**Approach for 6.4:**

1. Audit current Walk-Forward panel render — after run completes, verify `state->wf_complete` causes the results table to display.
2. If results don't auto-show: ensure `state->wf_has_results` is set when worker finishes.
3. If they DO auto-show: this commit can skip 6.4 (mark resolved in master plan).

**Anti-dust check:** Reuse `cancelled` field from Wave 2 if needed.

**Anti-drift check:** UI behavior only.

**Testing:** Manual — start a backtest, switch to Comparison panel, try Save Run, verify it's blocked until complete.

## Verification (after EACH commit)

```bash
cmake --build build && cmake --build build_gui && build/controller_test
```

## Verification (after ALL 3 commits)

Manual end-to-end:

1. Save Run twice with same name → verify auto-suffix
2. Open foxml_suite → see "Editing: backtest.cfg" header
3. Open engine_gui → see "Editing: engine.cfg" header
4. Start backtest → switch to Comparison → Save Run blocked until complete
5. Run Walk-Forward → verify results table appears

## Definition of done

- [ ] All 3 commits land on `experiment/phase5-zoo`
- [ ] Tests pass after each
- [ ] Master plan updated: 4.4, 5.3, 6.4, 6.7 marked done

## Tag at end of Wave 4

```bash
git tag wave4-complete phase5d-complete
```

## After Phase 5d

The system has comprehensive guards on:
- Pre-run: data validation, file existence, tick count sanity, gap detection
- Run-time: cancel state, button mutex, settings lock
- Post-run: class distribution surfaced, expected.cfg verification, fingerprint check
- Compile-time: feature order, count, format version
- Cosmetic: clear labels, no silent overwrites, clear cfg context

That covers basically every reasonable failure path. What's left is genuinely deferred (architectural refactors that wait for new features).
