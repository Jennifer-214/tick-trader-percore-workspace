# POST_v5.15 — WATCH_LIST

**Status:** Active (sprint shipped 2026-05-12; paper-test ≥1 week recommended)
**Sub-ships:** v5.15.0, v5.15.1, v5.15.2, v5.15.3, v5.15.4
**Mode:** Passive — things to observe during normal paper-trading. For
active scenarios to exercise, see `TRY_LIST.md`. For findings scratchpad,
see `OBSERVATIONS.md`.

---

## What changed this sprint (1-paragraph summary)

5 sub-ships closed 6 TECH_DEBT items + 4 PARITY items + 1 known landmine
via structural refactors. New surfaces visible to operator: **LiveReadiness
boot gate** (9-item pre-flight checklist logged at every boot); **Model
Health drift surface** (new GUI panel section with RED/YELLOW severity);
**`trading_mode` cfg field** (PAPER/LIVE/SHADOW); **`breakeven_on_profit`
wire-up** (was dormant; now actually ratchets SL); **shadow-load hot-swap**
(eliminates brief-empty-zoo window during model swaps); **`Stamp_AssembleAndEmit`
helper** (Train Model panel now emits complete stamps with all 22 cfg-bound
fields); **libgomp pthread-race FIXED** (parallel multi-horizon training
no longer segfaults). Hot path UNTOUCHED.

---

## BOOT LOGS (every engine start)

Watch `logging/engine.log` (or stderr if foreground) at boot:

### NEW v5.15.2 — LiveReadiness boot gate output

Expect 9 check lines logged at boot AFTER cfg load + model load:

```
[live_readiness] check: held_out_stamp_secret_nonempty — PASS / FAIL
[live_readiness] check: mlockall_required — PASS / FAIL
[live_readiness] check: all_cores_strategy_explicit — PASS / FAIL
[live_readiness] check: all_ml_cores_have_model — PASS / FAIL
[live_readiness] check: model_max_age_set — PASS / FAIL
[live_readiness] check: no_feature_hash_drift — PASS / FAIL
[live_readiness] check: no_label_hash_drift — PASS / FAIL
[live_readiness] check: no_build_flags_drift — PASS / FAIL
[live_readiness] check: all_stamps_hmac_verified — PASS / FAIL
```

- **Paper mode (default):** all checks WARN-only. Engine boots regardless.
- **Live mode (you won't be there yet):** any FAIL on a REFUSE-severity
  check (8 of 9) blocks boot.
- **Watch for:** any check that FAILs on a config you think is correct.
  That's a real signal worth investigating.
- **Fix hints:** each FAIL line includes operator-actionable next steps.

### NEW v5.15.4 — Live-mode normalize logs (only fires when trading_mode=live)

If/when you flip to `trading_mode=live` in cfg, expect:
```
[live_normalize] trading_mode=live: model_verify_strict 0→1 (STRICT). Set explicitly in cfg to override.
[live_normalize] trading_mode=live: reconcile_mode WARN→STRICT. Set explicitly in cfg to override.
```

Both fire automatically when the cfg field is UNSET (operator left default).
If you've set either explicitly, that flip won't fire for that key (other
key still might).

**Paper testing: these will NOT fire** (you're at trading_mode=paper).

### NEW v5.15.4 — Boot heap-allocation logs

Boot now uses `aligned_alloc(64)` for zoo containers per core. Normal
behavior is silent. Watch for:

```
[sharded] core %d: aligned_alloc(CoreModelZoo) failed; ML core cannot init
[sharded] core %d: aligned_alloc(EnsembleModelZoo) failed; ML core cannot init
```

These are OOM errors. Should be VERY rare (zoo is ~40KB). If you see one,
something else is wrong (memory pressure, ulimit, etc.).

### v5.15.0 — Drift detection in CoreModelZoo_TryLoadRole

When the engine loads a model, it now sets drift bits on
`handle->drift_flags_at_load uint16_t`. These propagate to the boot gate
+ the new Model Health panel. Boot log lines for drift:

```
[ml_drift] core %d %s: feature_registry_hash mismatch (stamp=0xHHHH, expected=0xHHHH)
[ml_drift] core %d %s: label_registry_hash mismatch ...
[ml_drift] core %d %s: build_flags_hash mismatch ...
[ml_drift] core %d %s: scaler binding drift ...
[ml_drift] core %d %s: STAMP_HMAC_NOT_VERIFIED (held_out_stamp_secret empty)
[ml_drift] core %d %s: MODEL_AGE_WARN (training_timestamp_us > cfg.model_max_age_hours)
```

- **Watch for:** drift on a model you think is current. Means you've
  rebuilt the engine since training; retrain OR set
  `acknowledge_cross_binary_version_drift=1` for known intentional drift.

---

## GUI / MLStatusPanel

### NEW v5.15.1 — Model Health CollapsingHeader

Between Ensemble + Thompson sections in MLStatusPanel.

**Header summary line:** `Model Health: 0/0 drift flags set` (paper-test
goal: stay at 0). If any drift bit fires:
- RED color = REFUSE-severity drift (would block live boot)
- YELLOW color = WARN-severity drift

**Per-row diagnostics:**
- Hover tooltips on each row explain what the drift bit means
- Model age in hours displayed for each core's primary handle

**Watch for:**
- Any RED row — investigate immediately
- YELLOW rows on models you think are fine — usually means cfg drift
  or model age > `cfg.model_max_age_hours`
- Model ages that look much older than expected (stale models)

---

## Hot-swap behavior (if you swap models while engine runs)

NEW shadow-load implementation per v5.15.4. Trigger by changing
`core_<N>_model_path` in cfg while engine is running (hot-reload picks
it up at next poll cycle).

**Success log:**
```
[hot_swap] ensemble core N shadow-swapped to /new/path (X roles loaded; primary=ROLE; exit=Y)
```
OR
```
[hot_swap] single-zoo core N shadow-swapped to /new/path (X roles loaded; primary=ROLE)
```

**Failure log:**
```
[hot_swap] ensemble core N shadow-load FAILED (rc=N); pre-swap state preserved
[hot_swap] single-zoo core N shadow-load FAILED (rc=N); pre-swap state preserved
```

- `rc=-1`: OOM allocating new zoo
- `rc=-2`: load failed (bad path, no roles)
- `rc=-3`: strict validate failed (post-load drift)

**Watch for:**
- "shadow-swapped" success line — confirms new model is now active
- "FAILED; pre-swap state preserved" — engine kept running on OLD
  model; investigate new path
- **You should NEVER see a brief "empty zoo" window in GUI predictions
  during a swap** — pre-v5.15.4 had this; shadow-load eliminates it.
  If you DO see predictions disappear briefly during swap, that's a
  regression worth flagging.

---

## Train Model + Multi-Horizon Train (if you train during paper-test)

### NEW v5.15.3 — Complete stamps from Train Model panel

Pre-v5.15.3 Train Model panel silently emitted stamps missing 22 cfg-bound
fields (Ridge, composite, winsor, exit_blender, trading_mode, etc.). Now
the panel uses the same helper as Run Full Validation; stamps have full
field set.

**Watch for:**
- New stamps trained via Train Model panel — open the resulting `.stamp`
  file to verify it has lines for the cfg-bound fields you've set
  (`has_ridge_within_horizon=1`, `has_confidence_composite_enabled=1`,
  `has_trading_mode=1`, etc.)

### NEW v5.15.3 — libgomp pthread-race FIXED

If you previously set `cfg.multi_horizon_max_threads >= 2` and got
segfaults during multi-horizon training (`RowsWiseBuildHistKernel`,
`PredictDMatrix`), that's fixed. Parallel mode is now safe.

**Watch for (in `logging/foxml_suite.log`):**
```
[mh-train] parallel mode: N horizons across N threads (xgb_train_nthread pinned to 1 per thread for parity)
```

- **Should NOT see segfault.** If you do, that's a regression (different
  root cause than v5.11.45 landmine).
- v5.11.45 forced-serial workaround REMOVED. v5.11.45 CRITICAL WARN log
  REMOVED. If you had been working around the landmine with
  `multi_horizon_max_threads=1` cfg, you can now flip it to your CPU
  count (or 0 = auto).

---

## `breakeven_on_profit` cfg field

PREVIOUSLY DORMANT — wired up in v5.15.2. If `cfg.lifecycle_cfg_flags`
has `MASK_LIFECYCLE_CFG_BREAKEVEN_ON_PROFIT` bit set:

- Open positions whose `gain_pct > 2 × fee_rate_taker` (net-profitable
  threshold) will have their SL ratcheted to fee-floored breakeven
  (`entry × (1 − 3 × fee_rate_taker)`).
- Max-write composes with trailing-SL ratchet (trailing wins above
  `tp_hold_score`; breakeven holds the floor below).

**Watch for:**
- If this is set in your cfg, watch for unexpected SL movements on
  open positions. Should ratchet UP only (max-write); never relax.
- If this is NOT set (default), no behavior change vs pre-v5.15.

---

## Performance / latency

Hot path UNTOUCHED across all 5 sub-ships. Slow-path cost analysis:

- v5.15.2 LiveReadiness_Verify: ~10µs total (BOOT-only; not per-cycle)
- v5.15.2 breakeven ratchet: ~80-150ns per active position per slow-path
  cycle when bit set; ~1ns when unset (wrapper early-exits)
- v5.15.1 drift OR-aggregation in snapshot publish: ~5 uint16 OR-ops
  per cycle (negligible)
- v5.15.4 shadow-load hot-swap: rare-event; ~1ms per swap (filesystem
  I/O dominates); not on per-tick path

**Watch for:**
- Slow-path total above 100µs (CLAUDE.md item 18 budget) — should never
  happen but check PerformanceMonitor panel if engine feels slower
- Hot-path p99 above ~500ns — should NEVER happen this sprint (no hot-
  path edits)

---

## Backwards compat

- **Pre-v5.14 stamps load cleanly** — Surface G `has_*=0` forward-compat
  preserves legacy stamp loading. If you have models trained pre-v5.14
  in `models/`, they should still load + run (drift detection may fire
  for missing newer fields like `has_trading_mode=0`, which is expected
  behavior; not a regression).
- **Pre-v5.14 cfg files load cleanly** — new cfg fields (`trading_mode`,
  `cfg_keys_explicit`) have safe defaults.
- **No MODEL_FORMAT_VERSION bump this sprint** — wire format byte-preserved.

**Watch for:**
- Pre-v5.14 model loading errors that look unrelated to drift —
  unexpected; flag immediately.

---

## What you should NEVER see

- Engine crash on boot (this is a smoke test; v5.15.0-.4 all GREEN
  across sanitizer + wider builds)
- Segfault during multi-horizon training (libgomp landmine FIXED)
- "Empty zoo" window in GUI during hot-swap (shadow-load eliminates)
- Cross-build stamp loading silently (drift detection should fire on
  intentional cross-build cases)
- Missing stamp body fields after Train Model panel (helper auto-populates
  all 22 cfg-bound fields)

If you see any of these, that's a real regression — capture in
`OBSERVATIONS.md` + come back to me.
