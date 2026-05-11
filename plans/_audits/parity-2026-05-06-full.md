# /parity-check report — 2026-05-06

## Plan summary

- **HEAD** 7f0b9a9 (merge: v5.10 epic — Sprint B 6/6 complete)
- **Tests** 1621/0 (operator-confirmed baseline; tests not re-run in this audit per sandbox policy)
- **calls_graph_diff** unconfirmed (no calls_graph artifact in working tree)
- **Audit scope** full
- **Cross-check baseline** post-v5.10.0e protections inventory:
  - FEATURE_REGISTRY_HASH (v5.8.6, FNV-1a over enabled feature names+versions)
  - LABEL_REGISTRY_HASH (v5.10.0d — NEW; FNV-1a over FOREACH_TARGET rows)
  - Snapshot tests (v5.9.2a; features/labels/scoring fn bodies)
  - Scaler `feature_registry_hash` binding (v5.9.3a)
  - Stamp body `scaler_sha256` (v5.9.3a)
  - Stamp body `engine_version` (v5.8.6) + `cross_major_engine` check (v5.9.2b)
  - `acknowledge_cross_binary_version_drift` (v5.9.4)
  - 10 stamp body inference_cfg fields (v5.9.2b/v5.9.4a/v5.9.5h/v5.9.5i)
  - `inference_cfg_drift` Tier 1/Tier 2 boot WARN/REFUSE (v5.9.5i)
  - `MODEL_FORMAT_VERSION = 5`
  - Runtime IC drift detection + auto-retire (v5.10.0e — NEW)
  - Hot model swap (v5.10.0c — NEW)
  - Multi-horizon ensemble + bandit blend (v5.10.0a — NEW)
  - FPN-end-to-end slow path (v5.10.0b — NEW; bytewise-deterministic Sin/Cos/Sqrt/Exp)

---

## Findings by severity

### CRITICAL

#### 1. LABEL_REGISTRY_HASH structurally dead in production (Section L — production-caller field-population)

**Summary** — v5.10.0d added `LABEL_REGISTRY_HASH()` and stamp body `label_registry_hash` field, with full verifier coverage. But ZERO production callers populate `inf.has_label_registry_hash = 1` at stamp emit, and ZERO production callers pass `expected_label_registry_hash` to `verify_model_stamp`. The new protection is silently disabled across the entire engine.

**File:line citations**:
- Verifier supports it: `ML_Headers/ModelInference.hpp:1010` (sig), `:1306-1318` (refusal logic)
- Emitter supports it: `ML_Headers/ModelInference.hpp:1697-1700` (canonical body emit when `has_label_registry_hash=1`)
- Stamp inputs struct: `ML_Headers/ModelInference.hpp:1491-1492`
- **GAP — production stamp emit (RFV)**: `Backtest/BacktestEngine.hpp:1104-1184` — `Backtest_RunFullValidation` populates ~25 fields of `inf` but does NOT set `has_label_registry_hash` / `label_registry_hash`.
- **GAP — production stamp emit (Train Model worker)**: `Backtest/BacktestPanels.hpp:2641-2710` — same omission.
- **GAP — production stamp consume (live load)**: `ML_Headers/CoreModelZoo.hpp:134-138` — `verify_model_stamp(found_path, secret, gap, MODEL_FORMAT_VERSION, FEATURE_REGISTRY_HASH())`. Misses 6th positional arg (`expected_label_registry_hash`); defaults to 0 → `if (expected_label_registry_hash != 0)` skips the entire check.
- **GAP — production stamp consume (Verify Stamp UI)**: `Backtest/BacktestPanels.hpp:1289-1294` — same omission.
- Tests-only coverage: `tests/controller_test.cpp:13331` (sets has_label_registry_hash=1), `:13343` (passes expected hash to verifier).

**Reproducer**:
1. Train a model with a stable FOREACH_TARGET registry; auto-stamp via Run Full Validation.
2. Add a new label row to FOREACH_TARGET (e.g. append `LABEL_NEW`); recompile training-build only (engine binary unchanged).
3. Retrain → new stamp.
4. Engine loads the new stamp without complaint despite the engine binary having the OLD `LABEL_REGISTRY_HASH`. (Expected: REFUSE on label-set drift.)

**Recommended fix** (Surface L pattern):
1. In `Backtest_RunFullValidation` and the Train Model worker, after `inf.has_xgb_hyperparams = 1` block, add:
   ```cpp
   inf.has_label_registry_hash = 1;
   inf.label_registry_hash     = LABEL_REGISTRY_HASH();
   ```
2. In `CoreModelZoo_TryLoadRole` (CoreModelZoo.hpp:134) and BacktestPanels Verify Stamp (BacktestPanels.hpp:1289), pass `LABEL_REGISTRY_HASH()` as the 6th arg to `verify_model_stamp`.
3. Add a snapshot/round-trip test that emits via the production helpers and verifies the field round-trips end-to-end (NOT through a synthetic `inf`).

**Effort estimate** — 30 min (4 file edits + 1 test). Same shape as v5.9.5b's `inf` plumb-through closure for fee_rate fields.

**Cross-ref** — Same regression class as v5.9.5b (Backtest_RunFullValidation passed nullptr for `inf`; v5.10.0d shipped tests but no production wiring — wide-blast structural omission).

---

#### 2. grid_member_count stamp body field dead in production (Section L)

**Summary** — v5.10.0a.G.2 added `grid_member_count` / `grid_member_idx` stamp body fields to identify horizon members of a multi-horizon ensemble. The verifier parses them; ZERO production callers emit them; ZERO production callers consume them.

**File:line citations**:
- Stamp inputs struct: `ML_Headers/ModelInference.hpp:1484-1486`
- Parser: `ML_Headers/ModelInference.hpp:1232-1238`
- Emitter: `ML_Headers/ModelInference.hpp:1685-1690`
- **GAP — production emit**: NO caller of `stamp_write_for_model` sets `inf.has_grid_member_count = 1`. Only `tests/controller_test.cpp:13751`.
- **GAP — production consume**: `EnsembleModelZoo_AutoDetectFromDir` (CoreModelZoo.hpp:1119-1232) docstring (lines 1093-1114) describes "Read stamp body's grid_member_count + grid_member_idx; validate consistency; place each at idx slot". Implementation does NONE of this — `grep "sr.grid_member"` returns empty.

**Reproducer**: Train a 3-horizon ensemble (cfg.horizon_list = "60,300,1500"). Stamp body emitted by RFV will lack grid_member_count. Engine boot at AutoDetectFromDir will discover 3 sibling dirs but never validate that all 3 are members of the same trained ensemble — operator could mix horizons across different training runs without detection.

**Recommended fix**:
1. **Emit side**: In RFV / Train Model, when `cfg.horizon_count > 0`, set `inf.has_grid_member_count = 1`, `inf.grid_member_count = cfg.horizon_count`, `inf.grid_member_idx = h_idx_in_horizon_list`. The trainer needs to know which horizon this stamp is for.
2. **Consume side**: In `EnsembleModelZoo_AutoDetectFromDir`, after calling `EnsembleModelZoo_LoadFromCfg`, walk loaded handles' parsed stamp results and verify grid_member_count agreement; refuse load if siblings disagree (or downgrade to log if held_out_gate_strict=0).

**Effort estimate** — 1.5h (stamp emit per-horizon plus consistency validator). The doc-stated intent has been there since v5.10.0a.G.2 ship — implementing it closes a stale-doc gap as well.

**Cross-ref** — Same dead-schema class as Finding #1. Both v5.10 stamp body field additions shipped without production wiring.

---

### HIGH

#### 3. Hot model swap bypasses inference_cfg drift detection block

**Summary** — v5.10.0c hot model swap calls `CoreModelZoo_LoadFromDir` (EngineSharded.hpp:2478), which loads + populates the `stamp_inf_*` handle fields. But the inference_cfg drift detection block (EngineSharded.hpp:957-1064) and xgb_hyperparams WARN block (EngineSharded.hpp:885-953) only execute at boot time inside the boot-time loop guarded by `cfg.core_model_dir[i][0]`. Post-swap, the new model's stamp may report `freshness_tau=0.5` while runtime cfg is `freshness_tau=0.1` — the operator gets no WARN/REFUSE, predictions silently shift.

**File:line citations**:
- Hot swap reload site: `CoreFrameworks/EngineSharded.hpp:2478-2482`
- Boot-time drift block: `CoreFrameworks/EngineSharded.hpp:957-1064`
- Boot-time xgb WARN block: `CoreFrameworks/EngineSharded.hpp:885-953`

**Reproducer**:
1. Train two models with different `freshness_tau`: M1 (tau=0.1), M2 (tau=0.5).
2. Boot engine with M1 + cfg.confidence_freshness_tau=0.1. Boot succeeds, no Tier 1 drift.
3. GUI: hot-swap to M2 (path with tau=0.5 stamped).
4. Engine logs `[hot_swap] swapped to M2_path (4 roles loaded)`. No WARN about tau drift.
5. M2's predictions go through the engine's tau=0.1 freshness window — silently miscalibrated.

**Recommended fix**: Extract the drift-detection block (EngineSharded.hpp:957-1064) + xgb_hyperparams block + label_registry_hash refusal (Finding #1) into a function `EventLoop_ValidateLoadedZooAgainstCfg(zoo, cfg, core_id, strict)`. Call it from BOTH:
- The boot loop (post-load, current location)
- The hot swap success branch (post-`CoreModelZoo_LoadFromDir`, before clearing the request flag)

When called from hot swap, on Tier 1 drift in strict mode: reject the swap (re-load M1 OR fall back to SimpleDip dispatcher) instead of REFUSE-at-boot's "exit engine" semantics.

**Effort estimate** — 2h (function extraction + call site addition + 3 hot-swap variants in tests).

**Cross-ref** — display↔execution invariant (CLAUDE.md Decision 12): hot swap was added with TUI surface (model_load_failed, ML Status panel update) but the drift-side observability paths weren't extended. Snapshot tests v5.9.5i exist but only for boot path.

---

#### 4. Hot model swap doesn't touch EnsembleModelZoo (architectural mismatch)

**Summary** — v5.10.0c hot swap reloads `swap_zoo` (the per-core single-horizon CoreModelZoo). It does NOT touch `ml_ensemble_zoos[c]`. If the operator runs with `cfg.horizon_list` non-empty (multi-horizon ensemble active), the dispatcher uses `ml_ctx.ensemble_zoo` from `state.cores[i].ensemble_handle` (set at boot, EngineSharded.hpp:858/860; never updated post-boot).

After a hot swap, the operator's intent is "use new model"; reality is "single-zoo gets swapped, ensemble keeps stale models". The `ML_BuildParameters` dispatcher reads ensemble_zoo first when active, so the new model is never used — operator confusion.

**File:line citations**:
- Hot swap touches single zoo only: `CoreFrameworks/EngineSharded.hpp:2456-2502`
- Ensemble handle set at boot: `CoreFrameworks/EngineSharded.hpp:858`, `Backtest/BacktestSharded.hpp:339`
- Ensemble zoo lifecycle (Free/Init): `ML_Headers/CoreModelZoo.hpp:986`, `:678`
- Dispatcher reads ensemble first: `Strategies/StrategyParameters.hpp:793`

**Reproducer**:
1. Boot engine with `cfg.core_0_model_dir=models/run_A` where run_A has `_horizon_60`, `_horizon_300` siblings.
2. Engine boots with ensemble auto-detected, ensemble_handle != nullptr.
3. GUI hot-swap to `models/run_B` (single-horizon model dir).
4. Engine logs `[hot_swap] core 0 swapped to run_B`. Predictions still come from run_A's ensemble — verify by checking `[ensemble] auto-detected ...` and bandit predictions.

**Recommended fix**:
- Either: extend hot swap to also Free + Init + AutoDetect the ensemble zoo from new path, AND refresh `state.cores[c].ensemble_handle`.
- Or: refuse hot swap when ensemble is active, with a clear log `[hot_swap] REFUSED: ensemble inference active; restart engine to swap horizon set`.

**Effort estimate** — 1h (refusal path) or 2.5h (full ensemble swap including bandit reload).

---

#### 5. is_buyer_maker dropped between SPSC ring and slow-path RollingStats (compound bug)

**Summary** — In the per_core_slow architecture, `is_buyer_maker` per tick is set on the producer's `Tick<F>` (EngineSharded.hpp:1346) and pushed into the SPSC ring. But the slow-path's `EventLoop_UpdateRollingStateOneCore` is called from EngineSharded.hpp:2547 with `/*is_buyer_maker=*/0` HARDCODED — the slow-path can't read the per-tick flag because rolling state is fed from the producer's `last_volume.load()` scalar (no buyer_maker companion).

In BacktestSharded, the `SharedBacktest_FromHistorical` conversion zeros `t.is_buyer_maker` (memset(0), then never assigned despite `h->is_buyer_maker` being available); ShardedBacktestDriver's `RollingStats_Push` (line 250-262) calls without is_buyer_maker (defaults to 0).

**Net effect**: BUY_PRESSURE / SELL_PRESSURE / VOLUME_DELTA features uniformly fed `is_buyer_maker=0` for ALL ticks across both paths. CumDelta and FlowState_Push DO get the correct flag (line 1641, 1650-1652). RollingStats does NOT — `volume_delta` is locked at +1.0.

**File:line citations**:
- Live slow-path hardcode: `CoreFrameworks/EngineSharded.hpp:2547-2550`
- Backtest tick conversion drops field: `Backtest/BacktestSharded.hpp:78-86`
- Backtest driver default-arg drop: `CoreFrameworks/ShardedBacktestDriver.hpp:250, 253, 259, 262`
- RollingStats default arg: `ML_Headers/RollingStats.hpp:116`
- LegacyReferenceDriver also drops it: `CoreFrameworks/LegacyReferenceDriver.hpp:210`
- Legacy PortfolioController did pass it (pre-sharded reference): `CoreFrameworks/PortfolioController.hpp:1026-1030`

**Reproducer**:
1. Backtest a tick CSV with realistic 50/50 buyer_maker distribution.
2. Inspect `r.feature_matrix[*][FEATURE_VOLUME_DELTA]` — values clustered tightly near +1.0 instead of distributed [-1,+1].
3. Live engine: same — model trained on this data sees correct distribution (because train is also broken), so train-serve identity HOLDS, but the feature signal is degraded across both paths.

**Severity rationale** — Train-serve PARITY is preserved (both broken the same way → no drift). But the FEAT_VOLUME_DELTA feature value is not what its docstring says ("net buy/sell pressure ... -1.0 to +1.0" — Strategies/RegimeDetector.hpp:67); it's effectively dead. Models trained against this data cannot use this feature productively. Combined with v5.10.0d structural label-registry-hash protection (Finding #1) being also dead, two notable signals are silently zero-information.

**Recommended fix** — Two-step:
1. Patch `SharedBacktest_FromHistorical` to copy `t.is_buyer_maker = (uint8_t)(h->is_buyer_maker ? 1 : 0)`.
2. Plumb is_buyer_maker through the slow-path API:
   - Add `is_buyer_maker` to whatever scalar bus replaces the SPSC tick (e.g. `g_last_buyer_maker.store(...)` per producer tick).
   - Read it in `EventLoop_UpdateRollingStateOneCore` and pass to `RollingStats_Push`.
   - Same for ShardedBacktestDriver.

**Effort estimate** — 1h (Step 1 alone) or 4h (full plumb-through with replay-determinism re-test).

**Cross-ref** — Suspect this is a v5.1.2 architectural decoupling regression (the comment at EngineSharded.hpp:1399 says "is_buyer_maker not available from the sharded fan_out yet"). Pre-v5.1.2 PortfolioController used it correctly. Worth a /readiness check on the v5.1 sprint to confirm this was a known carry-forward and not just a forgotten edge.

---

#### 6. EnsembleModelZoo_AutoDetectFromDir doesn't pass stamp gates / strict / cross-binary-drift flags to per-horizon loads

**Summary** — When operator boots with multi-horizon ensemble (cfg.core_model_dir + AutoDetect finds siblings), `EnsembleModelZoo_AutoDetectFromDir` is called from `EngineSharded.hpp:832-835` and `Backtest/BacktestSharded.hpp:296-299`. NEITHER call site passes `held_out_stamp_secret`, `gap_threshold`, `held_out_gate_strict`, or `acknowledge_cross_binary_drift`. The function signature defaults these (CoreModelZoo.hpp:1124-1127), so per-horizon model stamps load with secret="" / gap=0.05 / strict=0 — operator's `cfg.held_out_gate_strict=1` is silently bypassed for ensemble.

**File:line citations**:
- Live caller (drops args): `CoreFrameworks/EngineSharded.hpp:832-835`
- Backtest caller (drops args): `Backtest/BacktestSharded.hpp:296-299`
- Function signature: `ML_Headers/CoreModelZoo.hpp:1119-1127`
- Reference single-zoo caller (uses args correctly): `CoreFrameworks/EngineSharded.hpp:805-815`

**Reproducer**:
1. Create a stamped model at horizon_60 dir with intentionally-bad held_out_metric (gap > threshold).
2. Cfg `held_out_gate_strict=1`.
3. Single-zoo path REFUSES the model. AutoDetect path silently loads it.

**Recommended fix** — Plumb the four cfg-derived args through both call sites:
```cpp
EnsembleModelZoo_AutoDetectFromDir(
    &ml_ensemble_zoos[i], cfg.core_model_dir[i], backend,
    cfg.held_out_stamp_secret,
    FPN_ToDouble(cfg.gap_acceptable_threshold),
    cfg.held_out_gate_strict,
    cfg.acknowledge_cross_binary_version_drift);
```

**Effort estimate** — 30 min (2 call sites + test that ensemble auto-detect respects strict mode).

---

#### 7. Inference_cfg drift detection block doesn't iterate ensemble model handles

**Summary** — The Tier 1/Tier 2 inference cfg drift detection (EngineSharded.hpp:957-1064) iterates over `&zoo->buy_signal, &zoo->barrier, &zoo->regime, &zoo->exit` — the SINGLE-horizon CoreModelZoo handles. The `EnsembleModelZoo` has parallel arrays `ezoo->buy_signal[0..buy_signal_count]`, `ezoo->barrier[0..]`, etc. — these are NOT walked.

When operator runs with ensemble active, the per-horizon models (ezoo arrays) get fully populated `stamp_inf_*` fields by `CoreModelZoo_TryLoadRole` (CoreModelZoo.hpp:225-247), but no comparison against runtime cfg ever fires. Tier 1 drift (freshness_tau, threshold_scale, barrier_gate) silently bypasses operator detection in ensemble mode.

**File:line citations**:
- Drift block iterates single zoo only: `CoreFrameworks/EngineSharded.hpp:966-1050`
- Ensemble parallel arrays: `ML_Headers/CoreModelZoo.hpp` EnsembleModelZoo struct
- Per-horizon load populates handle fields: `ML_Headers/CoreModelZoo.hpp:225-247` (called from `EnsembleModelZoo_LoadFromCfg`)

**Reproducer**:
1. Train ensemble at horizon_60 with `confidence_freshness_tau=0.5`; horizon_300 with `confidence_freshness_tau=0.1` (operator misconfig: both stamps inconsistent).
2. Boot with `cfg.confidence_freshness_tau=0.05`.
3. Single-zoo drift block sees no models loaded (ensemble took over). No drift detected.
4. Ensemble runs without comparison; the horizon_60 stamp's tau=0.5 vs runtime's 0.05 = silent decision drift.

**Recommended fix** — Extend the drift block to iterate ensemble handles when active:
```cpp
if (loaded && cfg.core_model_dir[i][0] && !cfg.acknowledge_inference_cfg_drift) {
    // existing single-zoo block

    // v5.10.0a NEW: also iterate ensemble handles
    if (ml_ensemble_zoos[i].active) {
        for (int role = 0; role < 4; ++role) {
            int count = ...; // role-specific count
            for (int h = 0; h < count; ++h) {
                ModelHandle<F>* eh = &ml_ensemble_zoos[i].buy_signal[h]; // etc.
                // same Tier 1/Tier 2 comparison
            }
        }
    }
}
```

**Effort estimate** — 1.5h (extension to iterate 4 roles × N horizons + per-horizon log message + test).

**Cross-ref** — Same architectural mismatch class as Finding #4. v5.9.5i drift block predates v5.10.0a ensemble; ensemble shipped without extending the validator.

---

#### 8. Build warning: -Waggressive-loop-optimizations at TUIAnsi.hpp (NUM_STRATEGIES vs strat_stats[5] mismatch)

**Summary** — `EngineTUI.hpp:906` declares `StrategyStatsSnap strat_stats[5]` (size 5). `TUIAnsi.hpp:824, 828` iterates `for (int i = 0; i < NUM_STRATEGIES; i++)`. `NUM_STRATEGIES = NUM_STRATEGIES_REAL + 1 = 6` (5 real + AUTO sentinel). Iteration index 5 reads past array bounds → undefined behavior, surfaced by GCC `-Waggressive-loop-optimizations` with "iteration 5 invokes undefined behavior".

**File:line citations**:
- Warning sites: `DataStream/TUIAnsi.hpp:824, 828`
- Array declaration: `DataStream/EngineTUI.hpp:906` (`strat_stats[5]`)
- NUM_STRATEGIES expansion: `Strategies/StrategyInterface.hpp:131` (`NUM_STRATEGIES_REAL + 1`)
- Population loop also uses 5: `DataStream/EngineTUI.hpp:1405` (`for (int i = 0; i < 5; i++)`)

**Severity** — HIGH per Section K rule. Build warnings about UB in loop bounds are parity-relevant: the read at index 5 picks up garbage from neighboring stack/struct memory; the value differs by build flags / -O / compiler version. Across builds, the displayed "AUTO" strategy stats (or whatever lands at strat_stats[5] read) will diverge — display↔execution invariant breach (CLAUDE.md Decision 12).

**Reproducer** — Build with `-O3` then `-Og`; observe different "AUTO" display values in TUI.

**Recommended fix** — Two options:
1. **Resize array**: Change `StrategyStatsSnap strat_stats[5]` → `strat_stats[NUM_STRATEGIES]` (one source of truth). Update population loop at EngineTUI.hpp:1405 to `< NUM_STRATEGIES`. Then TUI iterations are valid.
2. **Cap iteration**: Change TUIAnsi.hpp loops to `< 5` (size of array; matches population intent — only real strategies have stats, AUTO is dispatcher-side).

Option 1 is more EASY_ADDITIONS_INVARIANTS-compliant (single source of truth), but requires checking every consumer of strat_stats. Option 2 is a one-file fix.

**Effort estimate** — 30 min (Option 2) or 1.5h (Option 1).

**Cross-ref** — Section K parity-relevant warning per v5.9.5a addendum. EASY_ADDITIONS_INVARIANTS pattern violation: NUM_STRATEGIES drives names + colors + chart but not the snapshot array.

---

### MEDIUM

#### 9. v5.10.0e drift state not surfaced to PerCoreSnap (operator can't tell drift-kill from manual-kill)

**Summary** — Runtime IC drift detection (v5.10.0e) maintains per-core `ctx.drift_history.breached` / `kill_tripped` / `breach_first_us` (ConfidenceScore.hpp:265-273). On `auto_kill_on_drift=1`, drift trips `core_kill_tripped=1` (ControllerEventLoop.hpp:1216-1226). But `core_kill_tripped` conflates drift-kill with MTM-kill, manual-kill, and other causes — operator viewing TUI sees "core 0 KILLED" with no diagnosis.

**File:line citations**:
- DriftHistory struct: `ML_Headers/ConfidenceScore.hpp:265-273`
- Auto-kill setter: `CoreFrameworks/ControllerEventLoop.hpp:1216-1226`
- core_kill_tripped declaration in PerCoreSnap: `DataStream/EngineTUI.hpp:1103`
- ML Status panel drift coverage: only cfg drift counts (`MLStatusPanel.hpp:184-203`); NO runtime IC drift fields.

**Severity rationale** — MEDIUM (observability gap, not parity). Section J discipline (each silent-failure mode gets a distinct PerCoreSnap field) violated by v5.10.0e shipping without `drift_breached` / `drift_avg_ic` / `drift_kill_tripped` fields.

**Recommended fix** (Section J pattern):
1. Add to PerCoreSnap (EngineTUI.hpp): `uint8_t drift_breached`, `uint8_t drift_kill_tripped`, `double drift_avg_ic`, `uint16_t drift_n_samples`.
2. ShardedSnapshot.hpp populator: copy `state->cores[i].drift_history.{breached,kill_tripped}` and live-compute avg from CheckBreach.
3. ML Status panel: render distinct line "drift: avg_ic=0.012 (n=128) — breached for 4h" when `drift_breached=1`.
4. Snapshot persist: extend SHARDED_SNAPSHOT_VERSION to 7 + serialize drift_history (or document non-persistence).

**Effort estimate** — 1h (PerCoreSnap field + populator + panel) — or 2h with snapshot serialization.

**Cross-ref** — Section J of /parity-check; v5.9.0b precedent (`ml_model_load_failed` got its own field, not conflated with `kill_tripped`).

---

#### 10. cfg_drift_tier1/tier2 counts stale after hot model swap (Finding #3 sibling)

**Summary** — `state.cores[i].cfg_drift_tier1_count` / `tier2_count` / `strict_refused` are populated only at boot loop (EngineSharded.hpp:1052-1054). After a hot swap loads a NEW model whose stamp_inf_* values differ from cfg, these counts stay frozen at boot-time values. ML Status panel renders stale data.

**File:line citations**:
- Boot-time setter: `CoreFrameworks/EngineSharded.hpp:1052-1054`
- Init zero: `CoreFrameworks/ControllerEventLoop.hpp:601-603`
- No re-set on swap path: `CoreFrameworks/EngineSharded.hpp:2424-2506` (just resets `model_load_failed`)

**Severity rationale** — MEDIUM (display drift, not execution). Closes naturally if Finding #3's fix routes hot-swap through `EventLoop_ValidateLoadedZooAgainstCfg`.

**Recommended fix** — Inherits Finding #3's extracted function. Function should write to `cfg_drift_tier*_count` regardless of caller (boot or swap).

**Effort estimate** — 0 (closes with Finding #3).

---

#### 11. SHARDED_SNAPSHOT_VERSION=6 doesn't persist drift_history (DOCUMENT-or-fix)

**Summary** — v5.10.0e added `DriftHistory` to CoreContext (ControllerEventLoop.hpp:185); `SHARDED_SNAPSHOT_VERSION=6` doesn't serialize it. Engine restart re-warms drift detection from scratch. Acceptable IF documented (drift detection is wall-clock-windowed, fast warm-up); silent surprise if not.

**File:line citations**:
- Snapshot version: `CoreFrameworks/ShardedSnapshotPersist.hpp:75`
- DriftHistory in CoreContext: `CoreFrameworks/ControllerEventLoop.hpp:185`
- DriftHistory_Init at engine init: `CoreFrameworks/ControllerEventLoop.hpp:526`

**Severity rationale** — MEDIUM as DOCUMENT-ONLY (rapidly self-restoring after restart given `confidence_ic_floor_window` default = 86400 seconds). The 86400s default = 24h sustained-breach window means the warm-up loss IS user-noticed (24h before drift detection re-arms post-restart).

**Recommended fix** (either path):
- Document in `DOCS/KNOWN_ISSUES.md`: "drift_history not persisted across snapshot save/restore — drift detection re-warms from empty post-restart, taking up to confidence_ic_floor_window seconds before re-arming."
- OR bump SHARDED_SNAPSHOT_VERSION to 7 + serialize ic_samples + ts_us + count + head + breached + breach_first_us + kill_tripped.

**Effort estimate** — 5 min (document) or 2.5h (serialize + version bump + back-compat read).

---

#### 12. Ensemble cfg fields not stamp-bound (silent decision drift class)

**Summary** — v5.10.0a added 9 ensemble cfg fields that affect inference behavior:
- `horizon_list[8]` + `horizon_count` (which horizon models load)
- `ensemble_blend_mode` ("weighted" vs "selection")
- `ensemble_bandit_eta`
- `ensemble_min_warmup_predictions`
- `ensemble_min_agreement_pct`
- `ensemble_trade_reward_mult`
- `ensemble_bandit_save_interval`
- per-core: `core_horizon_list`, `core_ensemble_blend_mode`, `core_disabled_horizons`

NONE of these are in `StampInferenceCfgInputs`. Operator could train with `ensemble_blend_mode=selection` (argmax horizon picks) and serve with `weighted` (Bandit-Exp3 weighting) — silent decision drift, no log.

**Severity rationale** — MEDIUM (decision drift, not silent prediction drift): the fields are cfg-driven dispatchers (which model selection logic runs); operator typically sets them once. But Section F lists "anything that affects inference" as a candidate stamp-bind, and ensemble dispatch absolutely affects inference.

**Recommended fix** (Surface G stamp body extension pattern, v5.10.1):
1. Add `has_ensemble_cfg` flag + 4-6 always-present ensemble cfg fields to `StampInferenceCfgInputs`.
2. Extend canonical body emit + parser + handle population.
3. EngineSharded boot drift block: add Tier 1 (blend_mode, horizon_list_hash) and Tier 2 (bandit_eta, min_agreement_pct) checks.

**Effort estimate** — 2-3h (Surface G extension across emitter + parser + handle + drift block; same shape as v5.9.5h xgb_hyperparams).

---

#### 13. Backtest path skips stamp verification (verify_strict path)

**Summary** — `BacktestSharded.hpp:256-257` calls `CoreModelZoo_LoadFromDir` with NO secret / gap / strict / drift args. The function signature defaults gap=0.05, strict=0, etc. So FEATURE_REGISTRY_HASH refusal, label_registry_hash refusal (Finding #1), and inference_cfg drift checks are all silently in warn-only mode for backtest. Live path (EngineSharded.hpp:805) DOES pass these args.

**Severity rationale** — MEDIUM. Different from Finding #1's silent-disabled (default 0 in expected hash). Here the CALL signature doesn't pass `cfg.held_out_gate_strict` to the load. Backtest train-time != serve-time strictness — same model triggers different verification outcomes.

**File:line citations**:
- Backtest no-args call: `Backtest/BacktestSharded.hpp:256-257`
- Live with-args call (reference): `CoreFrameworks/EngineSharded.hpp:805-815`

**Recommended fix** — Plumb `cfg.held_out_stamp_secret`, `gap_acceptable_threshold`, `held_out_gate_strict`, `acknowledge_cross_binary_version_drift` through the BacktestSharded call.

**Effort estimate** — 30 min.

**Cross-ref** — Sibling of Finding #6; both are missing-args bugs at LoadFromDir/AutoDetectFromDir call sites in BacktestSharded path.

---

### LOW

#### 14. Build warning -Wstringop-overflow at ControllerEventLoop.hpp:834

**Summary** — `EventLoopState_SetCoreStrategy` writes `state->cores[slot].strategy_id = strategy_id` after a bound check. Compiler can't statically prove the array index is safe (templated array; warning is benign). Not parity-relevant — write to in-memory state, not serialization.

**File:line** — `CoreFrameworks/ControllerEventLoop.hpp:834`

**Severity** — LOW per Section K rule (cosmetic; bound-checked).

**Recommended fix** — Add explicit `#pragma GCC diagnostic ignored "-Wstringop-overflow"` around the write, or static-assert MAX_EXECUTION_CORES bound.

**Effort estimate** — 15 min.

---

#### 15. Section A — HistoricalTick is_buyer_maker drop is silent

**Summary** — Subset of Finding #5. `SharedBacktest_FromHistorical` (BacktestSharded.hpp:78-86) silently drops `h->is_buyer_maker` because the `t.is_buyer_maker` set is missed. No comment explains the intent; reader can't tell if it's deliberate or oversight.

**File:line** — `Backtest/BacktestSharded.hpp:78-86`

**Severity** — LOW alone (closes with Finding #5 fix). Comment-only finding if Finding #5's structural fix is deferred.

**Recommended fix** — At minimum add a TODO comment: `// TODO(v5.11): is_buyer_maker not propagated; v5.1.2 architectural slow-path read from scalar bus drops this field. See parity-check Finding #5.`

**Effort estimate** — 5 min comment.

---

### DOCUMENT-ONLY

#### 16. Producer SPSC drop class (DOCUMENT-ONLY since v5.0)

**Summary** — Documented architectural bound. Producer fan-out can drop ticks under sustained backpressure (SPSC ring full). Not new in v5.10.

#### 17. XGBoost training-script determinism (DOCUMENT-ONLY)

**Summary** — Per Section I, XGBoost random_state pinning lives outside the engine (in trainer Python). Engine's `xgb_seed` cfg + stamp binding (v5.9.5h) covers cfg side; training-script side is operator responsibility.

---

## Cross-cutting concerns

Three findings root in the same architectural pattern: **v5.10 stamp body / cfg additions shipped without extending validators / production callers**:

- Finding #1 (label_registry_hash) — verifier args + 2 production emit sites
- Finding #2 (grid_member_count) — production emit + AutoDetect consume
- Finding #3 (hot swap drift) — drift block + xgb block + label hash refusal don't run on swap
- Finding #4 (hot swap ensemble) — swap doesn't touch ensemble zoo
- Finding #6 (AutoDetect args) — strict / gate args dropped
- Finding #7 (ensemble drift) — drift block iterates only single zoo
- Finding #12 (ensemble cfg unstamped) — same shape

**Single fix that closes 3 findings**: extract `EventLoop_ValidateLoadedZooAgainstCfg(zoo, ezoo, cfg, core_id, strict)` that runs:
- Tier 1/Tier 2 cfg drift checks (#3, #7)
- xgb_hyperparams WARN (#3)
- label_registry_hash refusal (also covers #1's load-side gap if function calls verify_model_stamp with both hashes)
- Iterate single zoo + ensemble handles uniformly (#7)
- Be callable from boot loop AND hot swap branch (#3, #10)

**Estimated unified fix effort** — 3h. Reduces Findings #1, #3, #7, #10 to one ship.

---

## Behavior matrix (verify train and serve agree for default cfg)

| Scenario | Trainer view | Engine view | Identical? |
|---|---|---|---|
| Feature pack output (FOREACH_FEATURE) | Computed via Features_PackAll | Computed via Features_PackAll | YES (snapshot test v5.9.2a) |
| Feature registry hash | Stamp embeds FEATURE_REGISTRY_HASH | Engine refuses on mismatch | YES (v5.8.6) |
| Label registry hash | Stamp embeds (test only) | Engine accepts any (gap #1) | **NO — Finding #1** |
| Grid member count | Stamp embeds (test only) | AutoDetect ignores (gap #2) | **NO — Finding #2** |
| Scaler sidecar | scaler_sha256 in stamp | Engine verifies SHA on load | YES (v5.9.3a) |
| Confidence freshness tau | Stamp embeds; runtime cfg compared | Tier 1 REFUSE in strict | YES at boot; **NO post-hot-swap** (Finding #3) |
| XGBoost hyperparams | Stamp embeds 8 fields | WARN on mismatch | YES at boot; **NO post-hot-swap** (Finding #3) |
| Ensemble blend mode | Cfg-only, NOT stamp-bound | Operator-set both sides | **NO if op misconfigs** (Finding #12) |
| Multi-horizon strict mode | AutoDetect uses default strict=0 | Boot single-zoo respects cfg | **NO — Finding #6** |
| Inference cfg drift on ensemble handles | Drift block walks single-zoo only | Ensemble handles populated but unchecked | **NO — Finding #7** |
| FPN_Sin/Cos/Sqrt/Exp determinism | Bytewise across calls | Bytewise across calls | YES (v5.10.0b tests) |
| FPN-end-to-end RegimeSignals | hour_sin/cos via FPN_Sin/Cos | Same path | YES (boundary-stable refactor) |
| FlowFeatures internal FPN | Bytewise across runs | Bytewise across runs | YES (v5.9.2 replay test extends) |
| RollingStats is_buyer_maker | Hardcoded 0 (slow-path) | Hardcoded 0 (slow-path) | YES (both broken — Finding #5) |
| volume_delta value semantics | Always +1.0 (degenerate) | Always +1.0 (degenerate) | YES (parity-preserving Finding #5) |
| Bandit state (per-regime) | Persisted to bandit_state.json | Loaded at boot | YES (v5.10.0a.G.9) |
| Drift history (IC ring) | N/A (training doesn't IC) | Re-warms from empty on restart | DOCUMENT-ONLY (Finding #11) |
| TUI strat_stats AUTO bin | Display-side undefined behavior | Display reads garbage | **NO — Finding #8** |

---

## Suggested ship sequence

Pre-v5.11 close-out (1-2 sub-ships):

1. **v5.10.1 — Production-caller field-population closure (CRITICAL findings)**
   - Finding #1 plumb-through: emit + consume label_registry_hash in 4 production sites
   - Finding #2 plumb-through: emit grid_member_count per horizon in trainer; validate at AutoDetect
   - Finding #6 plumb-through: pass strict / gate args to AutoDetectFromDir (2 call sites)
   - Effort: 3h. Tests-only round-trip → tests + production round-trip closure.

2. **v5.10.2 — Hot swap parity hardening (HIGH findings)**
   - Extract `EventLoop_ValidateLoadedZooAgainstCfg` covering single + ensemble handles (closes #3, #7, #10)
   - Decision: refuse hot swap when ensemble active OR extend swap to ensemble (Finding #4)
   - Effort: 3-4h depending on ensemble-swap choice.

3. **v5.10.3 — Display + observability surface (MEDIUM Section J)**
   - PerCoreSnap drift_breached / drift_kill_tripped / drift_avg_ic fields (Finding #9)
   - TUIAnsi.hpp NUM_STRATEGIES vs strat_stats[5] fix (Finding #8 — also fixes UB warning)
   - is_buyer_maker plumb-through OR comment-document the gap (Finding #5/#15)
   - Effort: 2h.

4. **v5.11.x or later — Surface G stamp body extension for ensemble cfg (MEDIUM Finding #12)**
   - Defer to v5.11 since ensemble cfg drift is one operator misconfig away vs the v5.10 surfaces which are silently broken-by-default.

---

## NOT a bug (verified-safe items)

- **FOREACH_FEATURE registry stable in v5.10** — no new features added; FEATURE_REGISTRY_HASH unchanged across the v5.10 epic (v5.10.0/0a/0b/0c/0d/0e all verified-not to touch FeatureRegistry.hpp:294-328). Existing v5.9 protections continue to function for all features.
- **FPN_Sin/Cos/Sqrt/Exp bytewise determinism** — comprehensive tests at controller_test.cpp:12964-13176 cover unit-circle identity, periodicity, range reduction, and bytewise repeat-determinism. Replay-determinism test at line 10251 still applicable.
- **Bandit state load/save round-trip** — v5.10.0a.next.2 explicitly added a replay-determinism test (controller_test.cpp:12610). bundle-id check + skip-bundle-check operator path both exercised.
- **MODEL_FORMAT_VERSION = 5** — preserved across v5.10. New stamp body fields use Surface G `has_*=0` forward-compat pattern (label_registry_hash, grid_member_count both follow the rule).
- **Tick consumption parity (Section A core path)** — `Tick<F>` (live) and `HistoricalTick` (backtest) both flow through `Regime_ComputeSignals` after `SharedBacktest_FromHistorical` conversion. Field naming differs (volume vs qty, timestamp vs timestamp_us) but conversion at single chokepoint preserves type semantics. (Caveat: is_buyer_maker drop covered in Finding #5; that's the only Section A divergence.)
- **Snapshot tests (v5.9.2a) still binding** — body-level snapshots for ML_Compute_*, Label_*, ConfidenceScorer_*, SimpleDip body unchanged in v5.10. CoreModelZoo_TryLoadRole load behavior tested at controller_test.cpp:10322+.
- **Atomic stamp write (v5.3.0)** — `.tmp + rename` POSIX atomic preserved. Locale pinning (LC_NUMERIC=C) preserved.
- **HMAC signature inclusive of all key=value lines** — canonical body construction order locked; bash-compat round-trip test at controller_test.cpp:7517+.
- **NaN-free feature pack (v5.9.0)** — Two-layer guard at Features_PackAll preserved across v5.10 changes. v5.10.0b boundary-stable refactor doesn't touch Features_PackAll's validation site (good — that was the explicit design goal).
- **Threading + initialization** — v5.10 fields zero-init'd at:
  - CoreContext.ensemble_handle (ControllerEventLoop.hpp:516)
  - CoreContext.drift_history (ControllerEventLoop.hpp:526 — DriftHistory_Init)
  - CoreContext.cfg_drift_tier1_count (ControllerEventLoop.hpp:601)
  - g_shared.swap_model_path_requested (EngineSharded.hpp:1222-1225)
  - All v5.10.0c hot swap fields explicitly cleared at boot.
- **Engine version handshake (v5.8.6 + v5.9.4)** — v5.10 didn't touch the cross-major / cross-minor / poll_interval boot WARN paths. Functions correctly post-v5.10.
- **v5.9.2 replay-determinism test** (controller_test.cpp:10251) — still applicable to v5.10.0b FPN-end-to-end refactor since boundary types preserved (`hour_sin`, `flow_*`, `large_trade_z` all stay double; only internal math becomes FPN-deterministic).

---

## Verdict — YELLOW (with caveats)

**Sprint B (v5.10) close-out — YELLOW, not GREEN.**

The expected outcome of "GREEN at v5.10 close" relied on Decision 15 ("Parity-tested-by-construction") being respected for v5.10.0d (label registry) and v5.10.0a.G.2 (grid member). In both cases, the verifier and snapshot tests exist, but the production callers DO NOT exercise them. This is exactly the v5.9.5b regression class (Backtest_RunFullValidation passing nullptr for `inf` despite all 10 inference cfg fields existing in the schema) — same shape, different stamp body fields.

**Blockers for v5.11.0 kickoff** (per master plan checklist `/parity-check GREEN at v5.10 close`):

- **CRITICAL Finding #1** (label_registry_hash dead in production) — must close before v5.11.0
- **CRITICAL Finding #2** (grid_member_count dead in production) — must close before v5.11.0

Both are 30-min Surface L fixes. Recommend a quick v5.10.1 sub-ship to close them, then re-run `/parity-check` for GREEN-at-close confirmation before opening v5.11.0.

**Non-blocker but ship-recommended pre-v5.11**:
- Finding #3, #4, #6, #7 (hot swap parity) — silent on the happy path; one operator misconfig away from undetected miscalibration.
- Finding #8 (NUM_STRATEGIES vs strat_stats[5] UB) — non-parity but a build-warning regression and EASY_ADDITIONS_INVARIANTS violation.

**Documentation-only items** acceptable as v5.11+ scope:
- Finding #11 (drift_history not snapshot-persisted)
- Finding #12 (ensemble cfg unstamped — feature-class scope for v5.11)
- Finding #15 (is_buyer_maker comment) — acceptable as comment if Finding #5 is deferred

**Five-bullet executive summary**:
1. v5.10.0d's `LABEL_REGISTRY_HASH` protection is structurally dead — no production caller emits or verifies it. Tests pass because they exercise the verifier directly with synthetic inputs.
2. v5.10.0a.G.2's `grid_member_count` stamp field is parsed but no production code reads or sets it; the documented ensemble-consistency check at AutoDetectFromDir is unimplemented.
3. v5.10.0c hot model swap bypasses the v5.9.5i inference_cfg drift detection block AND the xgb_hyperparams WARN block — drift between cfg and the swapped-in stamp is silently accepted.
4. v5.10.0a multi-horizon ensemble has TWO architectural mismatches: AutoDetectFromDir doesn't pass strict/gap args to per-horizon stamp verification, AND the inference_cfg drift block iterates single-zoo handles only (skipping ensemble handles entirely).
5. Build warnings exist that are parity-relevant (Section K): `-Waggressive-loop-optimizations` at TUIAnsi.hpp:824/828 (UB on iteration 5; NUM_STRATEGIES=6 vs strat_stats[5]). Mostly v5.10-introduced code is clean; the warnings predate v5.10 but no `/parity-check` had previously flagged them.

**Final note** — v5.10.0e (drift detection), v5.10.0b (FPN-end-to-end), bandit persistence (v5.10.0a.G.9), and the multi-horizon dispatch core are all **structurally clean**. The findings concentrate at the stamp body / cfg / handle interfaces — exactly the surfaces /parity-check is designed to catch. Decision 15 worked: when followed (v5.9.x), no critical findings emerged. Where it was missed (v5.10.0d emit, v5.10.0a.G.2 emit + consume, v5.10.0c re-validation, v5.10.0a ensemble drift block extension), critical/high gaps surfaced.

---

End of report.
