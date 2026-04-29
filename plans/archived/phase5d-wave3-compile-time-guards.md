# Phase 5d — Wave 3: Compile-time guards + state hygiene

**Time budget:** ~20 minutes · **Commits:** 2 · **Risk:** low-medium (touches static asserts; could break compile)

## Context anchors — files to read FIRST

```
plans/phase5d-master.md                  ← catalog
plans/phase5d-wave2-config-consistency.md ← prior wave (verify wave2-complete)
ML_Headers/ModelInference.hpp            ← FEAT_*, MODEL_NUM_FEATURES, MODEL_FORMAT_VERSION
ML_Headers/RollingStats.hpp              ← W (default 128), WL (default 512) template params
GUI/SettingsPanel.hpp                    ← Settings panel (gets disabled-while-running guard)
foxml_suite.cpp                           ← Settings panel render call site
```

Branch state expected: `experiment/phase5-zoo` at tag `wave2-complete`.

## Failure mode IDs covered

- 1.4 — RollingStats W/WL template params drift between code paths
- 1.5 — new feature added without bumping MODEL_FORMAT_VERSION
- 1.7 — feature order in ModelFeatures_Pack accidentally re-ordered
- 4.5 — settings save during backtest → mid-run drift

## Status update (2026-04-25 afternoon)

The original commit 9 only covered `FEAT_*` static_asserts. Sunday's structural fixes added two new invariants documented in CLAUDE.md but not yet compile-time-enforced:

- **Label-type-aware metric invariant** — could add a `static_assert` on `LABEL_COUNT == sizeof(label_table)/sizeof(LabelDef)` plus a checksum on label IDs. Same shape as the FEAT_* asserts. ~10 lines additional.
- **Dynamic-buffer lifecycle invariant** — could add `static_assert(sizeof(BacktestResults) == EXPECTED)` as a tripwire so adding a heap field forces explicit acknowledgment. Slightly gross but works. Optional.

Recommendation: fold both into commit 9 since they're the same kind of compile-time guard. Keeps the wave size unchanged but makes commit 9 cover three invariants instead of one. ~30 min total instead of ~10.

## Commit plan

### Commit 9: static_asserts for feature order + count + window sizes (1.4, 1.5, 1.7)

**Goal:** make accidental feature pipeline corruption a compile error.

**File:** `ML_Headers/ModelInference.hpp` — at file scope (after FEAT_* defines, before ModelHandle).

**Approach:**

1. **Feature count assertion:**
   ```cpp
   static_assert(MODEL_NUM_FEATURES == 16,
       "If you've added a feature: bump MODEL_NUM_FEATURES, then update this "
       "assert AND increment MODEL_FORMAT_VERSION below.");
   ```

2. **Feature order checksum:**
   ```cpp
   // sum of FEAT_* enum values — changes if any FEAT_* is reordered or value-changed.
   // intentionally a compile-time constant so feature re-ordering breaks build.
   static_assert(
       (FEAT_SHORT_SLOPE + FEAT_SHORT_R2 + FEAT_SHORT_VARIANCE +
        FEAT_LONG_SLOPE + FEAT_LONG_R2 + FEAT_LONG_VARIANCE +
        FEAT_VOL_RATIO + FEAT_ROR_SLOPE + FEAT_VOLUME_SLOPE + FEAT_VOLUME_DELTA +
        FEAT_EMA_SMA_SPREAD + FEAT_VWAP_DEV + FEAT_PRICE_STDDEV + FEAT_PRICE_AVG +
        FEAT_VOLUME_AVG + FEAT_EMA_ABOVE_SMA) == (15 * 16 / 2),  // sum 0..15 = 120
       "FEAT_* constants reordered or value-changed. If intentional: bump "
       "MODEL_FORMAT_VERSION, retrain all models, update this checksum.");
   ```

3. **Window size assertion:** confirm RollingStats template defaults are what the feature lookback table expects. In `ModelFeatures_Pack`, after the function body parameters are known:
   ```cpp
   static_assert(W == 128, "ModelFeatures_Pack expects RollingStats W=128 (short window). "
                            "If changed: update FEATURE_LOOKBACKS, retrain, bump format version.");
   ```
   (Use `static_assert` inside the template after the parameters are visible. Or just put it at FEATURE_LOOKBACKS definition.)

4. **MODEL_FORMAT_VERSION reminder:** add a comment block above MODEL_FORMAT_VERSION:
   ```cpp
   // BUMP THIS when:
   //   - Any FEAT_* constant changes value
   //   - MODEL_NUM_FEATURES changes
   //   - RollingStats W or WL template parameters change
   //   - ModelFeatures_Pack output semantics change
   // The static_asserts below catch reorders. This counter catches semantic shifts.
   #define MODEL_FORMAT_VERSION 1
   ```

**Anti-dust check:** static_asserts replace the human discipline of "remember to bump VERSION" with compile-time enforcement. No new code paths.

**Anti-drift check:** This IS the anti-drift mechanism. Verify nothing else changes.

**Testing:**
- Build clean → assertions pass
- Manually edit one FEAT_* value → build should fail with clear message
- Revert → build should pass

### Commit 10: Settings panel disabled while backtest running (4.5)

**Goal:** settings inputs greyed out while any backtest worker is running, so user can't save mid-run config drift.

**Files:**
- `GUI/SettingsPanel.hpp` — `GUI_Panel_Settings` accepts a "lock" flag
- `foxml_suite.cpp` — pass `run_control.running || optimizer.running || training.wf_running`

**Approach:**

1. Add an optional bool parameter `bool readonly = false` to `GUI_Panel_Settings`.
2. In the function body, wrap input rendering in `if (readonly) ImGui::BeginDisabled();` ... `ImGui::EndDisabled();`.
3. When readonly, replace the Save button with: `ImGui::TextDisabled("(read-only — backtest in progress)");`.
4. In foxml_suite.cpp render loop:
   ```cpp
   bool any_running = run_control.running || optimizer.running || training.wf_running;
   GUI_Panel_Settings(&settings, &suite_reload_flag, any_running);
   ```

**Anti-dust check:** Single new parameter, single check site. No duplicated logic.

**Anti-drift check:** UI guard only. Settings field semantics unchanged.

**Testing:** Manual — start a backtest, switch to Settings panel, verify inputs greyed out and Save button replaced.

## Verification (after EACH commit)

```bash
cmake --build build && cmake --build build_gui && build/controller_test
```

Anti-drift checks from `phase5d-master.md`.

## Verification (after ALL 2 commits)

Manual end-to-end test:

1. Verify build is clean and tests pass
2. Try to manually corrupt a FEAT_* value temporarily — confirm clear compile error message — revert
3. Start a backtest, switch to Settings panel — confirm read-only mode active

## Definition of done

- [ ] Both commits land on `experiment/phase5-zoo`
- [ ] Tests pass
- [ ] Master plan updated: 1.4, 1.5, 1.7, 4.5 marked done
- [ ] Compile-error test for FEAT reorder confirms guard works

## Tag at end of Wave 3

```bash
git tag wave3-complete
```
