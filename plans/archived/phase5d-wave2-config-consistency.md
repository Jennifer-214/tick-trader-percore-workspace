# Phase 5d — Wave 2: Config consistency + cancel handling

**Time budget:** ~45 minutes · **Commits:** 3 · **Risk:** medium (touches cfg loading + cancel state)

## Context anchors — files to read FIRST

```
plans/phase5d-master.md                  ← catalog + anti-drift discipline
plans/phase5d-wave1-data-validation.md   ← prior wave (verify wave1-complete tag)
CoreFrameworks/ControllerConfig.hpp      ← Config struct, defaults, CFG_PARSE_* macros
ML_Headers/CoreModelZoo.hpp              ← CoreModelZoo_VerifyExpected (extend this)
Backtest/BacktestPanels.hpp              ← Save Run handler (writes expected.cfg), worker thread
Backtest/BacktestEngine.hpp              ← Backtest_Run signature, cancel_flag handling
```

Branch state expected: `experiment/phase5-zoo` at tag `wave1-complete`. Verify:

```bash
git log --oneline -1 wave1-complete
git log --oneline -3   # current HEAD should match wave1-complete
```

If not, do not start Wave 2 — Wave 1 is incomplete.

## Failure mode IDs covered

From `phase5d-master.md`:

- 1.2 — slow_path_interval differs between training and live cfg
- 1.3 — min_warmup_samples differs
- 2.6 — feature collection on un-warmed rolling stats
- 4.3 — cancel mid-backtest → false complete
- 5.1 — negative TP/SL or risk_pct
- 5.2 — sum of core_N_risk_pct > 1.0

## Status update (2026-04-25 afternoon)

- **2.6.1 (`min_warmup_samples` semantic bug)** — ✅ **conservative fix shipped** (`c6aa0cc`). Clamp at config load + warning + suggestion to use `warmup_ticks` for "longer raw warmup" intent. The full structural rewrite from this plan (add monotonic `total_ticks_processed` counter to PortfolioController) is no longer urgent — keep it documented but downgrade priority.
- **2.6.2 (rename `min_warmup_samples` → `min_rolling_samples`)** — **lower priority now**. The clamp + warning + clearer struct comment cover the naming confusion in practice. Defer until/unless a concrete need arises.
- **4.3.1 (cancel during file load)** — added 2026-04-25 morning, still pending. `BacktestData_Load` doesn't check `cancel_flag`. Real bug, ~10 min fix. Should be folded into commit 8 here.
- **1.10 (warmup_count reset at day boundary)** — ✅ **resolved (verified false alarm)**. `warmup_count` is NOT in the day-boundary reset block in `BacktestEngine.hpp` lines ~477-535. Mark closed.
- **Commits 6, 7, 8 untouched** — still relevant and high-value. When implementing commit 7 (`ControllerConfig_Validate`), fold today's `min_warmup_samples` clamp into it (currently inline at the bottom of `ControllerConfig_Load`).

NEW (discovered during 2026-04-25 training attempt):
- **2.6.1 — `min_warmup_samples` semantic bug** — the check
  `rolling.count >= min_warmup_samples` uses `rolling.count` which is
  bounded by W=128 (short window size). Setting min > 128 means warmup
  NEVER completes → 0 trades, 0 samples, infinite WARMUP state.
  Field name implies "samples ingested" (uncapped) but check is
  "samples in short window" (capped at 128). User-hostile bug.

  **Fix options:**
    A. Change check to `rolling_long.count >= min_warmup_samples`
       (caps at 512, matches the warning's stated requirement).
    B. Add `total_ticks_processed` monotonic counter to PortfolioController,
       check against that. Most general fix, no upper bound.
    C. Rename field to `min_warmup_short_count` and document max=128.

  **Recommended:** Option B. It's the most general and matches the
  field's documented intent. Add `uint64_t total_ticks_processed`
  next to `rolling`, increment on each `_Tick` entry, use in warmup
  check. Old configs with min_warmup_samples ≤ 128 keep working
  identically (because total_ticks > 128 happens before rolling.count
  hits 128 anyway, since rolling.count increments per tick). Old
  configs with min > 128 START WORKING (currently broken).

  **Verification:** `controller_test` should still pass 279/279.
  Manual: set min_warmup_samples=512, run backtest, verify warmup
  completes around tick 512 (not stuck forever).

NEW (discovered late 2026-04-25):
- **2.6.2 — `warmup_ticks` vs `min_warmup_samples` field confusion**
  The actual gate is `warmup_ticks` (in `ControllerConfig.hpp`). The
  field `min_warmup_samples` is an OPTIONAL secondary check that has
  the rolling.count cap bug (2.6.1). Documentation (and our session
  tonight) led us to edit `min_warmup_samples` thinking it was the
  primary gate. **Fix:** rename `min_warmup_samples` → `min_rolling_samples`
  to disambiguate, or remove the field entirely if it's redundant
  with `warmup_ticks`.

- **4.3.1 — Cancel doesn't work during file load**
  `cancel_flag` is only checked inside the tick loop (Backtest_Run
  line 475). File load (`BacktestData_Load`) iterates CSV lines without
  checking cancel_flag. For 90 files × 1M ticks ≈ 90 seconds of file
  load, user can't cancel. **Fix:** add `if (*cancel_flag) return -1`
  inside BacktestData_Load's read loop, propagate -1 return up so the
  outer loop bails.

- **1.10 — `warmup_count` reset at day boundary**
  Backtest day boundary handler (line 477-535) resets session state.
  Need to verify if `warmup_count` is also reset — if yes and
  `warmup_ticks > daily_tick_count` (rare but possible for low-volume
  days), warmup never re-completes after day 1, all subsequent days
  have no trades. Check `PortfolioController.hpp:518-534` reset block
  to confirm warmup_count is or isn't included. Live engine would have
  the same issue at the daily reconnect boundary.

## Commit plan (in order)

### Commit 6: Extend expected.cfg with slow_path_interval + min_warmup_samples (1.2, 1.3)

**Goal:** include training-time config that affects feature distribution in expected.cfg, verify against live config on model load.

**Files:**
- `Backtest/BacktestPanels.hpp` — Save Run expected.cfg writer (around line ~1240, where current expected fields are written)
- `ML_Headers/CoreModelZoo.hpp` — `CoreModelZoo_VerifyExpected` (extend the parser + comparison)

**Approach:**
1. In Save Run, add to expected.cfg:
   ```
   slow_path_interval = N
   min_warmup_samples = N
   ```
   Read values from `results->config_used.slow_path_interval` and `results->config_used.min_warmup_samples`.
2. In `CoreModelZoo_VerifyExpected`, add parser cases for these two keys. Compare against `live_slow_path_interval` and `live_min_warmup_samples` (new function parameters).
3. Update `EngineSharded.hpp` call site to pass these from cfg.
4. Mismatch → log at warning level (or fail in strict).

**Anti-dust check:** Reuse the existing parser pattern. No duplicate parser code.

**Anti-drift check:** Verify-only flow; doesn't modify live config.

**Testing:** Manual — train a model, save run, edit backtest.cfg's slow_path_interval, restart engine_gui pointing at the saved run, verify warning fires.

### Commit 7: ControllerConfig_Validate function (5.1, 5.2, 2.6 in part)

**Goal:** centralized config sanity validation. Called at config load time. Logs warnings for impossible/dangerous values. Optional strict mode (already have `model_verify_strict`) makes warnings fatal.

**File:** `CoreFrameworks/ControllerConfig.hpp` — add at end of file or near ControllerConfig_Load.

**Checks (in order, log each):**
1. `take_profit_pct > 0` — if not, `[CFG] WARNING: take_profit_pct = X (must be > 0)`
2. `stop_loss_pct > 0`
3. `risk_pct ∈ (0, 1]` — values outside indicate user typed `15` instead of `0.15`
4. `slow_path_interval > 0`
5. `min_warmup_samples >= 512` (long window size) — if smaller, features will be computed on un-warmed rolling stats
6. `volume_multiplier > 0`
7. `fee_rate >= 0` (can be 0 for free-trade venues, but never negative)
8. **NEW:** sum of `core_N_risk_pct[0..16]` for active cores ≤ 1.0
9. `barrier_gate_enabled ∈ {0, 1}`
10. `model_verify_strict ∈ {-1, 0, 1}`

**Implementation pattern:**
```cpp
template <unsigned F>
inline int ControllerConfig_Validate(const ControllerConfig<F> *cfg) {
    int warnings = 0;
    if (FPN_ToDouble(cfg->take_profit_pct) <= 0.0) {
        fprintf(stderr, "[CFG] WARNING: take_profit_pct must be > 0\n");
        warnings++;
    }
    // ... etc
    return warnings;
}
```

**Caller:** `ControllerConfig_Load` calls this after parsing, before returning. Log total warning count.

**Anti-dust check:** Single function, called from both engine.cfg load and backtest.cfg load (and any future cfg loads).

**Anti-drift check:** Read-only validation. No config mutation.

**Testing:** Manual — set negative TP in cfg, restart, verify warning + count > 0.

### Commit 8: Cancel state handling — `complete` vs `cancelled` distinction (4.3)

**Goal:** when user cancels a backtest mid-run, results panel should NOT display the partial stats as if they were complete. Currently `state->complete = 1` is set even on cancel.

**Files:**
- `Backtest/BacktestPanels.hpp` — `RunControlState` struct, results-display conditional checks
- `Backtest/BacktestEngine.hpp` — `Backtest_Run` worker function (sets complete; needs to differentiate)

**Approach:**
1. Add `volatile int cancelled` field to RunControlState (next to `complete`).
2. In `backtest_worker_fn`: after `Backtest_Run` returns, check the cancel_flag — if set, set `state->cancelled = 1` instead of `complete = 1`.
3. In display code (Results panel, Comparison Save Run, etc.): change `if (state->complete)` checks to `if (state->complete && !state->cancelled)`.
4. Add a "Cancelled — partial results not shown" indicator in Run Control panel when cancelled.

**Anti-dust check:** Add the field to the existing struct, don't fork a new state machine.

**Anti-drift check:** Cancel flag already exists (cancel_flag); just add a corresponding result state.

**Testing:** Manual — start a backtest, click Cancel mid-run, verify Results panel doesn't show partial stats. Re-run, let complete, verify normal flow still works.

## Verification (after EACH commit)

```bash
cmake --build build -j$(nproc) && cmake --build build_gui -j$(nproc) && build/controller_test
```

Plus anti-drift checks from `phase5d-master.md`.

## Verification (after ALL 3 commits)

Manual end-to-end test:

1. Restart foxml_suite
2. Train + Save Run with explicit `slow_path_interval=128` in backtest.cfg
3. Edit backtest.cfg to slow_path_interval=64
4. Restart engine_gui pointing at the saved run → see verify warning
5. Set negative TP in backtest.cfg → restart → see config warnings on load
6. Set core_0_risk_pct=80 + core_1_risk_pct=80 → restart → see sum-> 1.0 warning
7. Start a backtest, click Cancel — verify Results panel says "cancelled" not "complete"

## Definition of done

- [ ] 3 commits land on `experiment/phase5-zoo`
- [ ] Tests pass after each
- [ ] Master plan updated: 1.2, 1.3, 2.6, 4.3, 5.1, 5.2 marked done
- [ ] Manual end-to-end test passes

## Tag at end of Wave 2

```bash
git tag wave2-complete
```
