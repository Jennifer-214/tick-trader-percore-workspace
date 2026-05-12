# foxml_suite UX Cleanup — left-off snapshot 2026-05-12

**Context:** Started during 2026-05-12 session while reviewing the
Trainer panel's Label Kind CSV tooltip with Caramel. Conversation
pivoted to v5.15.5 per-horizon TP/SL serving (substantial design
work) and the UX cleanup got sidetracked partway through.

This doc captures DONE vs PENDING so the cleanup can resume cleanly
in a future session without losing context.

---

## DONE (committed in BacktestPanels.hpp 2026-05-12)

| Fix | File:line | What changed |
|---|---|---|
| **X delete column popup** ("peach flash, no popup" bug) | `BacktestPanels.hpp:1405-1428` + `1551-1579` (classification + regression tables) | Popup hoisted out of per-row table-cell scope; new modal at parent-window scope after EndTabBar. Added `PastRunsState.pending_delete_idx` field; row click sets idx + opens modal; modal reads `runs[pending_delete_idx]` and fires `PastRuns_DeleteDir` on Confirm. ImGui popup-in-table-cell scoping bug closed. |
| **Open Folder Path button** | `BacktestPanels.hpp:1604` | Replaced status_msg-only no-op with `fork() + execlp("xdg-open", ...)`. Actually opens the directory in file manager. unistd.h added at top of file. |
| **Delete (manual) button → Copy Path** | `BacktestPanels.hpp:1609` | Was redundant with X column delete (which does the real `nftw` delete with confirmation). Replaced with Copy Path button using `ImGui::SetClipboardText(r->full_path)`. Useful for dropping the path into engine.cfg or terminal. |
| **Samples column** | `BacktestPanels.hpp:120,635-700 (struct),760-799 (parser),5546-5547 (single-horizon writer),3713-3714 (multi-horizon writer),1279+1339 (classification render),1451+1505 (regression render)` | Added `int n_train_samples` to PastRun struct. summary.txt writers (both single-horizon Save Run AND multi-horizon worker) now emit `n_train_samples: %d` from `state->results.sample_count` / `results->sample_count`. PastRuns_LoadOne parses it. Samples column added to both classification + regression tables with k/M scaling (`%.1fM`, `%.1fk`, or `%d`). |
| **Label Kind CSV tooltip** | `BacktestPanels.hpp:4193-4214` | Replaced static tooltip with `IsItemHovered() + BeginTooltip()` + live iteration of `label_table[]` (from `LabelFunctions.hpp` FOREACH_TARGET registry). Operator now sees integer code → display name mapping live. Adding a label to FOREACH_TARGET auto-updates the tooltip. |
| **Train Multi-Horizon button tooltip** | `BacktestPanels.hpp:5052-5060` | Removed the wrong `0,5,1 → binary/multiclass/regression` example (5 = WILL_PEAK = binary; 1 = BARRIER = binary; the example contradicted itself). Replaced with pointer "Hover the 'Label Kind CSV' input for the integer→name lookup." |

**Build verified:** ./build.sh suite GREEN at the time of these edits.

---

## DESIGN_SPECS + going-forward rules established alongside (also done)

- `tick-trader-percore-workspace/FEATURE_LOOKUP.md` — operator-visible
  feature catalog, seeded with 20 features
- `CLAUDE.local.md` going-forward rule: FEATURE_LOOKUP.md auto-write
  on operator-visible features (sister to PARITY_ISSUES.md / TECH_DEBT.md
  auto-write contracts)

---

## PENDING (deferred — for future UX cleanup ship)

### 1. Theme matching sweep (foxml_suite "entire thing probably needs to be themed")

**Caramel's framing 2026-05-12:** "just the entire thing probably need
to be themed". The foxml_suite already calls `Foxml_ApplyTheme()` at
`foxml_suite.cpp:225`, but ~75+ sites across the codebase bypass
`FoxmlColors::` with hardcoded `ImVec4(0.55, 0.76, 0.51, 1.0)` literals.

**Inventory (rg-able):**
- `BacktestPanels.hpp` — 45 hardcoded ImVec4 sites (e.g., lines 519,
  520, 591, 1131, 1144, 1147, 1149, 1182, 1416, 1420, ...)
- `GUI/ChartPanel.hpp` — 26 sites
- `GUI/DashboardPanels.hpp` — 6 sites
- `GUI/MLStatusPanel.hpp` — 3 sites
- `GUI/EngineHeaderPanel.hpp` — 4 sites

**Scope:** ~100 LOC mechanical replace map. Each `ImVec4(0.55,
0.76, 0.51, 1.0)` → `FoxmlColors::green`, etc. For colors that
don't have an exact match, ADD the constant to FoxmlTheme.hpp.

**Risk:** None — UX-only, no parity / hot-path / wire-format
implications.

**Estimated effort:** ~1-2 hours focused sweep.

### 2. Hide LIVE-only tabs in foxml_suite (Volume, Chart, ML Status, etc.)

**Caramel's framing 2026-05-12:** "and would it be possible to clean up
some of the unused tabs on the ML side? like volume, chart, ML status
and other stuff that is only used by the LIVE side?"

foxml_suite is the training / backtest GUI; engine_gui is the live
GUI. Both currently render the same tab set (Volume / Equity Curve /
Live P&L / Run Control / Chart / ML Status). foxml_suite operators
don't need the live-only tabs.

**Approach:** gate the LIVE-only tab rendering on the BUILD TARGET
(suite vs engine_gui) or on a runtime mode flag. Probably easiest
to add `#ifdef FOXML_SUITE_ONLY` around the live-tab section in
the GUI thread / panel registration.

**Inventory (need to grep):** find the tab-bar code in foxml_suite.cpp
or GUI/GuiThread.hpp; identify which tabs are live-only.

**Risk:** Low — tab visibility only.

**Estimated effort:** ~30-60 minutes.

### 3. cfg-isolation observation (deferred, not actionable yet)

**Caramel's observation 2026-05-12:** "i dont think the ML side reads
the backtest.cfg, i think it reads the engine.cfg, thats probably why
i got confused about settings" + "well it reads it, but the settings
tab in the ML side shows the engine.cfg settings".

foxml_suite's Settings panel displays the same engine.cfg that the
live engine uses. backtest.cfg is mostly a separate concern but the
training pipeline reads `cfg.core_strategies[i]` from engine.cfg
(per `BacktestSharded.hpp:152`). Architectural concern; not a
quick UX fix.

**Possible directions:**
- Add visual indication to foxml_suite Settings panel showing which
  cfg file is loaded (`engine.cfg` vs `backtest.cfg`)
- Or split: foxml_suite loads backtest.cfg, engine loads engine.cfg,
  separate Settings panels

**Defer rationale:** architectural; needs more design thought. Could
become its own ship (e.g., v5.15.6.X cfg-isolation) or roll into the
v6.0 paper-test-era engine-state-exposure protocol per CLAUDE.local.md
decoupling-endgoal-roadmap.

---

## How to resume

1. Read this doc to recall what's done vs pending
2. Pick item 1 (theme sweep) or item 2 (tab hiding) — each independently
   shippable, no dependencies
3. Skip item 3 unless promoted to architectural ship

**Files touched if resuming:** primarily `Backtest/BacktestPanels.hpp`
(theme), `GUI/*` (theme + tab hiding), `foxml_suite.cpp` (tab registration).

## Cross-references

- v5.15.5 plan (current focus that took priority):
  `plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.5-per-horizon-tp-sl-serving.md`
- DESIGN_SPECS: `cache-layout-discipline-for-hot-side-structs.md`,
  `per-horizon-barrier-blending-with-shadow-mode.md`,
  `latency-vs-cache-decision-framework.md` (all from the same session)
- FEATURE_LOOKUP.md: `tick-trader-percore-workspace/FEATURE_LOOKUP.md`
