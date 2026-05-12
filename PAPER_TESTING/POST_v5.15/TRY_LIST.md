# POST_v5.15 — TRY_LIST

**Status:** Active
**Mode:** Active — scenarios to DELIBERATELY exercise during paper-test
to validate v5.15 changes. For passive observation, see `WATCH_LIST.md`.

Each scenario has: setup → action → expected → red-flag (what would be a
bug).

---

## 1. Boot with default cfg (smoke test)

**Setup:** Use your current paper-test cfg (presumably `trading_mode=paper`
or unset).

**Action:** `./bin/engine` (or `engine_gui` for GUI). Let it boot fully.

**Expected:**
- Boot completes; LiveReadiness checks all log (some may FAIL, all
  WARN-only since paper mode); engine enters running state.
- New Model Health panel section visible in GUI between Ensemble +
  Thompson sections.
- Engine processes ticks normally.

**Red flags:**
- Engine refuses boot (paper mode should never REFUSE)
- LiveReadiness checks don't log at all (gate didn't run)
- Model Health panel missing or empty when models are loaded

---

## 2. Stale-model drift detection

**Setup:** Find an old model in `models/` whose training_timestamp_us is
> `cfg.model_max_age_hours` ago (or temporarily set
`cfg.model_max_age_hours=1` to force the case).

**Action:** Boot engine with that model loaded.

**Expected:**
- Boot log: `[ml_drift] core N ROLE: MODEL_AGE_WARN (training_timestamp_us
  > cfg.model_max_age_hours)`
- Model Health panel: YELLOW row for "model_age_warn" with hover tooltip
  showing age in hours
- LiveReadiness check `model_max_age_set` FAILs (WARN-only in paper)

**Red flags:**
- No warning despite obviously-old model
- RED color (should be YELLOW; not REFUSE-severity)
- Boot refuses (paper mode never refuses)

---

## 3. Train a new model via Train Model panel — verify complete stamp

**Setup:** foxml_suite open, Train Model panel ready with a recent
backtest data window loaded. Have a few cfg fields set in non-default
state (e.g., `ridge_within_horizon=1`, `confidence_composite_enabled=1`,
`winsor_pct_low=0.01`).

**Action:** Click Train Model. Wait for completion. Open the generated
`.stamp` file in a text editor.

**Expected:**
- Stamp file contains lines for ALL non-default cfg-bound fields:
  - `has_ridge_within_horizon=1` (+ `ridge_within_horizon=1`)
  - `has_confidence_composite_enabled=1` (+ value)
  - `has_winsor_pct_low=1` + `winsor_pct_low=0.010000`
  - `has_trading_mode=1` + value
  - etc. for every cfg-bound field you've non-default-set
- ~22 fields total in the cfg-bound block (depending on what you've set)

**Red flags:**
- Stamp missing `has_<field>` lines for cfgs you've explicitly set
  (would mean STAMP_CFG_AUTOPOPULATE didn't fire — regression of PARITY-020)
- `has_grid_member=0` despite training a single model (should be
  `has_grid_member=1` with `grid_member_count=1, grid_member_idx=0` defaults)

---

## 4. Train multi-horizon models — exercise parallel mode

**Setup:** Set `cfg.multi_horizon_max_threads=N` (where N = your CPU
count, or `0` = auto). Set `cfg.core_<X>_horizon_list=100,500,1000`
for some core.

**Action:** Train Multi-Horizon panel; click Train. Watch
`logging/foxml_suite.log` for the parallel-mode confirmation.

**Expected:**
- Log: `[mh-train] parallel mode: 3 horizons across N threads
  (xgb_train_nthread pinned to 1 per thread for parity)`
- All 3 horizons train successfully + emit stamps
- Each stamp has `has_grid_member=1` with `grid_member_count=3` +
  `grid_member_idx=0/1/2` per horizon (PARITY-021 closure)
- **NO SEGFAULT** (libgomp landmine FIXED v5.15.3)

**Red flags:**
- Segfault during parallel training — v5.11.45 landmine resurfaced;
  CRITICAL regression
- `grid_member_count=1, idx=0` defaults persisting in multi-horizon
  stamps (PARITY-021 regression)

---

## 5. Hot-swap a model while engine runs

**Setup:** Engine running. Have a second model dir ready
(`models/run_b/<role>.bin` + `.stamp`).

**Action:** Edit `engine.cfg` while engine running:
`core_N_model_path=models/run_b/<role>.bin` (or
`core_N_model_dir=models/run_b/`). Save. Engine hot-reload picks it up
at next slow-path cycle.

**Expected:**
- Log: `[hot_swap] single-zoo core N shadow-swapped to models/run_b/...
  (X roles loaded; primary=ROLE)` (or `ensemble core N shadow-swapped`
  if ensemble path)
- Predictions in GUI continue uninterrupted (no brief "no model" window)
- Model Health panel updates to reflect new model's stamp drift state

**Red flags:**
- Brief "empty zoo / no predictions" window in GUI during swap (shadow-
  load should prevent this; pre-v5.15.4 had it; v5.15.4 regression if
  you see it)
- Swap "FAILED; pre-swap state preserved" on a path you expect to work
- Crash during swap

---

## 6. Hot-swap to a BAD path — verify pre-swap preserved

**Setup:** Engine running with a valid model loaded.

**Action:** Edit `engine.cfg` to point `core_N_model_path` at a
non-existent path: `core_N_model_path=models/THIS_DOES_NOT_EXIST.bin`.

**Expected:**
- Log: `[hot_swap] single-zoo core N shadow-load FAILED (rc=-2);
  pre-swap state preserved`
- Predictions continue using OLD model (engine doesn't degrade to
  SimpleDip; old zoo is still active)
- Model Health panel still shows OLD model's stamp

**Red flags:**
- Engine degrades to SimpleDip (would mean pre-swap zoo was destroyed)
- Crash on bad path
- Hot-swap "succeeds" silently with no model loaded

(This is the PARITY-023 closure proof in production.)

---

## 7. Set `breakeven_on_profit` + observe SL ratcheting

**Setup:** In `engine.cfg`, set the bit:
`lifecycle_cfg_flags=<bitmap with MASK_LIFECYCLE_CFG_BREAKEVEN_ON_PROFIT set>`.
Or set via cfg-flag-eligibility helper if you have one wired up.

**Action:** Let the engine open a position. Wait until `gain_pct > 2 ×
fee_rate_taker` (typically when position is up ~0.2-0.5%).

**Expected:**
- SL ratchets UP to `entry × (1 - 3 × fee_rate_taker)` (fee-floored
  breakeven; covers round-trip fees + maker/taker spread)
- TUI / chart visible SL line jumps to new level
- No log spam; the ratchet is silent + branchless

**Red flags:**
- SL ratchets DOWN (max-write contract broken)
- SL ratchets BEFORE gain crosses 2× fee_taker (threshold wrong)
- Ratchet happens even when bit unset (wire-up bug; previously dormant
  field should require explicit opt-in)

---

## 8. Backwards compat — load a pre-v5.14 model

**Setup:** Find a model file from `git tag pre-v5.14.0` era (or earlier)
in your `models/` archive.

**Action:** Update cfg to point at it; boot engine.

**Expected:**
- Model loads successfully
- Boot log: drift WARN lines for missing newer fields (e.g.,
  `has_trading_mode=0` → cfg drift detected) — Surface G forward-compat
  fires the WARN but doesn't refuse
- Engine runs normally
- Model Health panel shows YELLOW drift bits for the missing fields
  (expected behavior; not a regression)

**Red flags:**
- Pre-v5.14 model refuses to load (Surface G forward-compat broken)
- Crash on loading legacy stamp
- All drift bits clear despite obviously legacy stamp (drift detection
  isn't firing)

---

## 9. Stress test — long-running paper session

**Setup:** Engine running with standard paper-test cfg.

**Action:** Let it run for ≥24 hours. Mid-stream, exercise scenarios
1-8 above. Check `logging/engine.log` periodically.

**Expected:**
- No crashes / no segfaults / no memory leaks visible in `top` or
  `htop`
- Paper P&L curve matches your historical-backtest expectation for the
  cfg you're running
- Slow-path latency p99 stays under 100µs (check PerformanceMonitor
  panel)

**Red flags:**
- RSS memory growing unboundedly over hours (could be old-zoo leak —
  shadow-load expects single-owner reclamation; if heap grows on every
  hot-swap, something's off)
- Slow-path latency spikes above 100µs without OS interference cause
- Paper PnL wildly different from backtest (something v5.15 changed
  about execution semantics that wasn't expected)

---

## 10. Verify v5.15 leaves PAPER mode unchanged when no new cfg fields set

**Setup:** Use a v5.14.post1-era `engine.cfg` (no `trading_mode`,
no v5.15.4 fields). Engine should default to PAPER + behave identically
to v5.14.post1.

**Action:** Boot + run for a few hours.

**Expected:**
- `trading_mode=PAPER` (default; cfg unset)
- All v5.15.2 LiveReadiness checks log as WARN-only
- No `[live_normalize]` flips (paper mode passthrough)
- Identical paper-PnL trajectory vs v5.14.post1 run on same data window

**Red flags:**
- Different paper-PnL trajectory vs v5.14.post1 baseline — would mean
  v5.15 silently changed execution semantics (regression)
- Boot warnings on a legacy cfg that ran fine on v5.14.post1

---

## When ready to graduate to LIVE

Per umbrella postmortem handoff checklist:

1. Complete this TRY_LIST (10/10 GREEN)
2. Run paper-test ≥1 week continuous; OBSERVATIONS.md clean
3. Run trading_mode=shadow for ≥1 week (live data + simulated fills)
4. THEN flip trading_mode=live + expect `[live_normalize]` auto-flips
5. Verify LiveReadiness REFUSES if any pre-flight item not satisfied
6. Operator deploy checklist (held_out_stamp_secret set; mlockall
   succeeded; all cores explicit strategy; etc.)
