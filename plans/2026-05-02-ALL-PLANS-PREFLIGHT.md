# All-Plans Pre-flight (sidecar to master plan)

**Date:** 2026-05-02
**Master plan:** `plans/2026-05-02-MASTER-v5.9-to-v5.10.md`
**Purpose:** Per-plan concerns, mitigations, watch-points, and pre-coding checklists
captured BEFORE coding starts. Single doc rather than 8 separate sidecar
files — easier to scan + maintain. Updated as work progresses.

## How to use

Before starting any sub-plan:
1. Read its section here (e.g., scroll to "v5.9.5h pre-flight")
2. Walk the **Pre-coding checklist** (must all check before coding)
3. Note the **Watch-points during coding** (mid-implementation gotchas)
4. Run **Operator validation** post-tag

After each ship: add a **Post-ship retrospective** section noting what
surfaced + how mitigations held up. This becomes input for the v5.10
or v5.11 sprint planning cycle.

---

## v5.9.5h pre-flight — Hyperparam ownership

### Concerns

1. **Largest single ship of Sprint A** — 12 files, ~10h estimated.
   Big surface area for one tag.
2. **Stamp body canonical-order is load-bearing** — bash + in-process
   emit must produce byte-identical canonical bodies. v5.8.8
   round-trip test is the tripwire.
3. **Cfg defaults must match current hardcoded values** — bytewise
   train-output identity for non-tuning operators is required for
   "zero behavior change" claim.
4. **Engine_gui Settings panel adds 5 cfg fields** — operator can
   tune in engine_gui but engine doesn't TRAIN. Fields only used
   for load-time WARN. Operator confusion risk.

### Mitigations

1. **Phased commits within the ship** — 9 sub-phases; commit per
   phase; single tag at end. Allows mid-ship rollback.
2. **HMAC parity test extends in same commit** — v5.8.8 test
   block must include the 8 new hyperparam fields BEFORE the bash
   CLI ships, not after.
3. **Snapshot test for cfg defaults** — assert
   `XGBHyperparams_Defaults().subsample == FPN_FromDouble(0.8)`
   etc. Catches accidental default change.
4. **Tooltip on engine_gui hyperparam fields** — explicitly say
   "for load-time WARN comparison; engine doesn't train. Edit
   `backtest.cfg` for training values."

### Watch-points during coding

- ⚠ When emitting stamp body fields, the order must match
  `ML_Headers/ModelInference.hpp:1129-1210` exactly (current
  positions 1-16). New positions 17 (xgb_hyperparams) and 18
  (build_flags) append AFTER `model_num_outputs` (position 16),
  BEFORE any v5.10 additions.
- ⚠ `XGBHyperparams_Apply` is called at 3 sites; if any forgets
  a field, the model trains differently from the others (silent
  drift). Loop through every field, set every param.
- ⚠ Train Model's status_msg at line 1990-1998 already extended
  in v5.9.5d ("next: Run Full Validation hint"). v5.9.5h adds
  scaler_sha256_hex line; don't break the existing hint.

### Pre-coding checklist

- [ ] `git status` clean (no uncommitted changes)
- [ ] `git tag pre-v5.9.5h` exists (rollback safety)
- [ ] `./build.sh test gui suite` clean (1289/0)
- [ ] `/parity-check` on v5.9.5g — GREEN (foundation pre-flight)
- [ ] Read `BacktestPanels.hpp:1944+` (Train Model worker
  scaler block — v5.9.5d added scaler_sha256_hex; v5.9.5h
  reads it)
- [ ] Read `ModelInference.hpp:1129-1210` (canonical body emit
  order — v5.9.5h appends at end)
- [ ] Read `ControllerConfig.hpp:1391-1408` (per-core strategy
  parser pattern — model for adding xgb_subsample parser)

### Operator validation post-tag

1. Train a model with default hyperparams → stamp records
   `xgb_subsample=0.8`, `xgb_seed=42`, etc.
2. Click Verify Stamp → "Stamp details" tree shows
   "Recorded hyperparameters" section with all 8 values
3. Edit `engine.cfg`'s `xgb_subsample=0.5` → restart engine_gui
4. Engine boot WARNs:
   `[xgb_hyperparams] WARN: ... claims xgb_subsample=0.8 but
   cfg.xgb_subsample=0.5`
5. Set `acknowledge_cross_binary_version_drift=1` → WARN gone
6. Bash CLI: `tools/stamp_model.sh ... --xgb-subsample 0.7` →
   stamp emits the value → in-process verifier reads 0.7

---

## v5.9.5i pre-flight — Cfg enforcement + ML Status row + Stamps Inspection

### Concerns

1. **3-tier strict mode** for inference cfg drift — fields enforced
   differently (Tier 1 = REFUSE; Tier 2 = WARN). Documenting WHY
   each field is which tier matters for operator clarity.
2. **Stamps Inspection panel** — opendir/stat I/O on render is
   forbidden (v5.9.5f scaler scan precedent). Refresh-button
   driven only.
3. **ML Status row** must NOT add hot-path overhead — render is
   already on slow-path display, but verify panel doesn't trigger
   per-tick state recalc.

### Mitigations

1. **Tier classification explicit in code comments** — when adding
   the per-field comparison loop in `CoreModelZoo._TryLoadRole`,
   each field gets a `// Tier X: <reason>` comment.
2. **Refresh-button-driven scan** + auto-rescan on panel-appearing
   trigger (mirrors v5.9.5f Settings panel model scan).
3. **ML Status row reads cached ModelHandle fields only** — no
   verify_model_stamp re-call per render.

### Watch-points during coding

- ⚠ The 3-tier mapping (which field is Tier 1 vs Tier 2) is
  operator-policy. If unclear, default to Tier 2 (WARN-only) to
  avoid breaking existing deploys.
- ⚠ Stamps Inspection panel could grow to hundreds of stamped
  models. Cap at 64 + WARN if more found.
- ⚠ FOREACH_PANEL X-macro registry — adding a new entry must
  follow the canonical signature. Look at v5.8.5 panel for
  pattern.

### Pre-coding checklist

- [ ] v5.9.5h shipped + tagged + tests pass
- [ ] `git tag pre-v5.9.5i` exists
- [ ] Read `CoreModelZoo.hpp:200-244` (v5.9.3a 3-tier scaler
  pattern — model for cfg enforcement)
- [ ] Read `GUI/SettingsPanel.hpp:Settings_RescanModels`
  (v5.9.5f scan pattern — model for Stamps panel scan)
- [ ] Read `BacktestPanels.hpp:1066+` (v5.9.5d Stamp details
  tree — extract for shared rendering)

### Operator validation post-tag

1. Load a model with `inference_cfg_freshness_tau=300` recorded
2. Set `cfg.confidence_freshness_tau=600` → restart engine_gui
3. Tier 1 strict mode (`held_out_gate_strict=1`) → REFUSE load
4. Tier 1 warn mode → load with WARN
5. ML Status panel shows "freshness_tau: 300 (stamp) | 600
   (runtime) — DRIFT" highlighted yellow
6. Stamps Inspection panel: filter "FAIL only" → shows the
   refused model with reason

---

## v5.9.5j pre-flight — Multiclass + auto-stamp + snapshot tests

### Concerns

1. **Design decision #17 LOCKED to Option A** — Train Model
   stamps with WF only, no held-out. Operators wanting held-out
   workflow stay on Run Full Validation.
2. **gap_threshold=0.0 sentinel** — may collide with operator
   accidentally setting threshold to 0 in cfg. Need explicit
   check: `gap_threshold == 0.0 AND held_out_metric == 0.0` →
   "training-only stamp."
3. **Per-class display** assumes label_kind == 2 (multiclass);
   binary/regression flow must remain unchanged.

### Mitigations

1. **Option B path explicitly deferred** to v5.11+. Documented
   in plan + master. If operators ask, point at the design note.
2. **Sentinel double-guard** — both fields must be 0.0 to qualify
   as training-only. Single field zero (e.g., `gap_threshold=0.0`
   with `held_out_metric=0.5`) is treated as malformed stamp →
   refuse.
3. **`label_kind` switch** in WF table render — multiclass shows
   per-class columns; binary/regression shows existing single-line
   accuracy. No regression for existing workflows.

### Watch-points during coding

- ⚠ When extending `WalkForwardFoldResult` with per-class arrays,
  zero-init in the struct's default constructor (struct
  `{}` syntax). Garbage in arrays = false display.
- ⚠ Snapshot test for ConfidenceScorer — record IC + RMSE at
  10 evenly-spaced points; ensure deterministic seed (push
  `sin(i)` for predictable values).
- ⚠ Train Model's `auto_stamp_*` fields parallel Full
  Validation's; copy the structural shape but NOT the held-out
  computation (it doesn't have one).

### Pre-coding checklist

- [ ] v5.9.5h + v5.9.5i shipped + tags
- [ ] `git tag pre-v5.9.5j` exists
- [ ] Read `BacktestPanels.hpp:1730+` (Full Validation
  auto-stamp flow — mirror exactly)
- [ ] Read `controller_test.cpp:3434-3455` (existing
  ConfidenceScorer tests — extend, don't replace)
- [ ] Confirm `label_kind` field exists on
  `WalkForwardFoldResult` or `BacktestRunConfig`

### Operator validation post-tag

1. Click Train Model with auto-stamp enabled + secret set →
   stamp written status appears below status_msg
2. Verify Stamp on Train-Model-stamped model → "Stamp details"
   shows `gap=0.0`, "training-only" banner
3. Drop Train-Model-stamped model into engine.cfg → engine loads
   with info-level log, not refuse
4. Train multiclass label (PEAK_VALLEY_STABLE) → WF results
   table shows per-class accuracy columns
5. ConfidenceScorer test passes (snapshot match)

---

## v5.10.0a pre-flight — Grid search + multi-horizon

### Concerns

1. **Cross-core XGBoost thread-safety** — current `nthread=1`
   was set for determinism. Per-core parallelism may break
   reproducibility.
2. **Triple-split data leakage risk** — easy to accidentally
   include test set in selection metric.
3. **Sweep space explosion** — operator who specifies broad
   ranges may train hours of irrelevant models.

### Mitigations

1. **Each core trains independently** with its own thread; verify
   bytewise predictions per-core given identical seed + data.
   If different, set `nthread=1` per core (sequential within core,
   parallel across cores).
2. **Locked test set** — separate `HeldOutSplit_TrainEval` call
   on test partition; metric computed there ONLY for final
   selection display, never input to sweep loop.
3. **Sweep-space cap** — refuse if sweep would produce > 1000
   total runs. Operator must narrow or explicit-acknowledge.

### Watch-points during coding

- ⚠ When parallelizing across cores, log per-core seed +
  hyperparam tuple at each iteration. Diagnostic for any
  "results differ from serial" surprise.
- ⚠ Multi-horizon (#4) builds on grid search (#1). If #1 has
  any thread-safety bug, #4 inherits it. Don't ship #4 until
  #1 is bytewise-deterministic.
- ⚠ Aggregation: pick best by metric across all cores. If
  best is tied (multiple iterations same val_acc), use
  consistent tiebreak (lower seed wins).

### Pre-coding checklist

- [ ] v5.9.5h shipped (provides hyperparam cfg fields)
- [ ] v5.9.5j shipped (provides auto-stamp pattern)
- [ ] v5.9 → experiment/per-core-sharding merged
- [ ] `git checkout experiment/per-core-sharding`
- [ ] `git checkout -b feat/v5.10.0a-grid-search`
- [ ] Read `BacktestEngine.hpp:1775-1834` (current serial
  Backtest_RunSweep)
- [ ] Read `OptimizerPanel` UI flow at `BacktestPanels.hpp:1346+`
- [ ] Read sharded backtest driver — `CoreFrameworks/ShardedBacktestDriver.hpp`
  for per-core dispatch precedent

### Operator validation post-tag

1. OptimizerPanel UI shows hyperparam selector combo (after #1)
2. Sweep `xgb_subsample` from 0.5 to 1.0 in 0.1 steps → 6
   models train, best identified
3. Triple-split: training never sees test data; verifiable by
   logging sample indices used per fold
4. Multi-horizon (after #4): train 5 models on horizons; predict
   on test; highest-confidence prediction wins

---

## v5.10.0b pre-flight — FPN-end-to-end (HIGH RISK)

### Concerns

1. **Highest-risk ship in entire sprint** — ~500 LOC refactor;
   all reference models must retrain; potential precision drift.
2. **FPN sin/cos design gate** — must be locked BEFORE B.1
   coding starts. Lookup table recommended.
3. **MODEL_FORMAT_VERSION 5 → 6 is one-way** — pre-v5.10 stamps
   refuse-on-load. Operator coordination required.

### Mitigations

1. **Pre-tag per stage** — `pre-v5.10.0b.1`, `pre-v5.10.0b.2`,
   `pre-v5.10.0b` (final). Granular rollback.
2. **Design gate doc** — write `DOCS/v5.10.0b-fpn-design.md`
   BEFORE B.1 start. Lock the sin/cos approach (recommend
   lookup table). Operator approves before coding begins.
3. **Lower-cost fallback** — if epsilon-tolerance fails on B.1
   (FPN values diverge from double values beyond bound), abort
   the sprint. Defer to v5.11. Keep v5.10.0b as a known-future
   improvement; ship #10 build_flags as the cross-build drift
   detection in the meantime.

### Watch-points during coding

- ⚠ B.1 epsilon-tolerance test — FPN mean/variance/slope
  vs double counterparts must agree within 1e-6. Snapshot
  test the boundary.
- ⚠ B.2 replay-determinism — bytewise identical predictions
  across two runs of same backtest. Existing test in
  `tests/parity_harness.cpp`; extend coverage.
- ⚠ B.3 reference-model retrain — operator coordination.
  Document the retrain ritual in DOCS/RETRAIN_RITUAL.md (or
  ML_TRAINING.md).
- ⚠ Hour-of-day signal: if going with lookup table, table
  must be identical across all build configs (compile-time
  constant). Test: hash the table, assert hash unchanged
  across builds.

### Pre-coding checklist

- [ ] v5.10.0a shipped
- [ ] **DESIGN GATE:** `DOCS/v5.10.0b-fpn-design.md` written
  + operator approves sin/cos approach
- [ ] `git tag pre-v5.10.0b` exists (covers entire ship)
- [ ] Backup all reference models to `models/pre-v5.10/` before
  retraining (operator decision: keep old models accessible
  for forensics)
- [ ] Read `Strategies/RegimeDetector.hpp` (~150 LOC double math
  to convert)
- [ ] Read `ML_Headers/RollingStats.hpp` (mean/variance/slope
  primitives)
- [ ] `tests/parity_harness.cpp` baseline run — capture current
  bytewise output for replay-determinism comparison

### Operator validation post-tag

1. **Build-config matrix:** compile with `-O2`, `-O3`, with/without
   `-DUSE_NATIVE_128`, with/without FMA → all 4 configs produce
   bytewise-identical replay-determinism predictions
2. **Reference model retrained** matches per-core P&L within
   epsilon of v5.9 reference (sanity check that conversion didn't
   break semantics)
3. **MODEL_FORMAT_VERSION refusal:** drop a v5.9-stamped model
   into v5.10.0b engine → refused with clear "model_format_version
   too old; retrain to v5.10+" message

---

## v5.10.0c pre-flight — Hot model swap

### Concerns

1. **Atomic ordering of swap_model_path_requested[]** — must be
   single-writer (slow-path consumer); GUI is producer. Mirror
   strategy hot-swap RCU pattern exactly.
2. **Position-handling design** — default safe (wait for close);
   operator opt-in to immediate-swap. Watch for documentation
   clarity here.
3. **Old-handle free timing** — too eager = use-after-free; too
   lazy = memory leak. Grace period of one slow-path cycle.

### Mitigations

1. **Pattern mirror exactly** from `SettingsPanel.hpp:923` strategy
   swap. Single writer (engine slow-path), atomic store-release;
   GUI does atomic load-acquire, store new request.
2. **Cfg default = safe**:
   `acknowledge_hot_swap_with_open_positions=0`. Tooltip explains
   the implications.
3. **Old-handle freed AFTER one slow-path cycle** — gives hot path
   one tick to finish reading via stable pointer. RCU semantics.

### Watch-points during coding

- ⚠ When swap requested but stamp verify fails: state must clear
  (request bit set to 0) so operator can retry without confusion.
- ⚠ When swap requested + position open + cfg=wait-for-close:
  swap deferred. Subsequent Apply clicks should overwrite the
  pending request, not queue.
- ⚠ Strategy hot-swap + model hot-swap simultaneous: operator
  could trigger both. Test concurrent: both succeed without
  deadlock, both visible in ML Status panel.

### Pre-coding checklist

- [ ] v5.10.0b shipped (FPN refactor stable)
- [ ] `git tag pre-v5.10.0c` exists
- [ ] Read `SettingsPanel.hpp:920-940` (strategy hot-swap
  pattern — mirror exactly)
- [ ] Read `CoreModelZoo._TryLoadRole` (load + verify path
  reused for swap)
- [ ] `Model_Init` / `Model_Free` lifecycle — confirm safe
  to call mid-engine-run

### Operator validation post-tag

1. Load model A in engine_gui
2. Pick model B in Settings → Apply (live)
3. Engine swaps within 1 slow-path cycle (verify via stderr log)
4. ML Status panel shows new model's predictions
5. Open position pre-swap → exits naturally on old model
6. Bad stamp scenario: pick a refused model → swap fails,
   request cleared, ML Status shows "swap REFUSED: <reason>"

---

## v5.10.0d pre-flight — FOREACH_TARGET retrofit

### Concerns

1. **X-macro consistency** — dispatcher must be auto-generated;
   if hand-maintained, defeats the purpose.
2. **LABEL_REGISTRY_HASH stability** — once shipped, the hash is
   stable. Operator-visible: changing label set forces stamp
   refusal. Document.
3. **Pre-v5.10.0d stamps** — forward-compat via has_*=0 + WARN
   (NOT refuse). Some operators may skip the WARN; clear
   docs needed.

### Mitigations

1. **Auto-gen check** in `Backtest/LabelFunctions.hpp` — assert
   that `LABEL_COUNT == sum(FOREACH_TARGET(X))`. If they
   disagree at compile time → static_assert error.
2. **Hash stability snapshot test** — assert
   `LABEL_REGISTRY_HASH() == EXPECTED_HASH`; force operator
   acknowledgment when bumping.
3. **WARN mode only for legacy** — never auto-refuse on
   has_label_registry_hash=0. v5.11+ may elevate to refuse if
   needed.

### Watch-points during coding

- ⚠ When converting `label_table[]` to X-macro, verify all 8
  existing labels (LABEL_WIN_LOSS through LABEL_PEAK_VALLEY_STABLE)
  retain their numeric IDs. Renumbering breaks model_format
  compat (different `label_type` cfg values).
- ⚠ FNV-1a constexpr hash same as FEATURE_REGISTRY_HASH pattern.
  Reuse the helper.
- ⚠ `LabelType_NumClasses` etc. must continue to work without
  modification (read from the same `label_table[]` symbol).

### Pre-coding checklist

- [ ] v5.10.0c shipped
- [ ] `git tag pre-v5.10.0d` exists
- [ ] Read `Backtest/LabelFunctions.hpp:276-293` (current
  label_table)
- [ ] Read `ML_Headers/FeatureRegistry.hpp:FOREACH_FEATURE`
  (the X-macro pattern to mirror)
- [ ] Confirm `LabelType_NumClasses`, `LabelType_IsRegression`
  etc. read from `label_table[]` directly (not hardcoded)

### Operator validation post-tag

1. Train model with current label set → stamp records
   LABEL_REGISTRY_HASH = (current build's hash)
2. Verify Stamp shows label_registry_hash = the value
3. (Hypothetical: if FOREACH_TARGET ever changes) old stamp
   refused with "label set drift" message
4. Pre-v5.10.0d stamp → loads with WARN
   "label drift NOT verified"

---

## v5.10.0e pre-flight — Drift detection / model retirement

### Concerns

1. **Threshold tuning is empirical** — default IC floor 0.02 may
   not fit all symbols. Operator must recalibrate.
2. **False positives during regime transitions** — IC dips during
   genuine market change look like drift. 24h window mitigates
   but doesn't eliminate.
3. **Auto-kill-on-drift** trips kill_switch which has cascading
   effects (no new buys, halts all trading). Operator opt-in
   only.

### Mitigations

1. **Default OFF for auto-kill** — `auto_kill_on_drift=0`.
   Operator must deliberately enable.
2. **Sustained-window discipline** — require N hours of below-floor
   IC before trip; transient dips don't fire.
3. **ML Status panel display** — operator sees "drift watch"
   state at a glance. Yellow at floor breach, red at sustained.

### Watch-points during coding

- ⚠ Kill switch trip mechanism: per /plan-check audit
  2026-05-02, use direct `state->oms->kill_switch_tripped = 1`
  (no named helper function exists).
- ⚠ Rolling IC infrastructure: bounded ring buffer; size
  calculated from window seconds × poll_interval. Allocate at
  Init time; never realloc mid-run.
- ⚠ False-positive avoidance during warmup: skip drift check
  until `ic_history_count >= ic_history_capacity`. Operator
  may notice "no drift check active for first 24h" — document.

### Pre-coding checklist

- [ ] v5.10.0d shipped
- [ ] `git tag pre-v5.10.0e` exists
- [ ] Read `ML_Headers/ConfidenceScore.hpp:210+` (current IC
  computation)
- [ ] Read `controller_test.cpp:3434-3455` (existing
  ConfidenceScorer tests)
- [ ] `Health_LogCriticalRateLimited` (v5.9.0b) — for
  sustained-breach log

### Operator validation post-tag

1. Healthy IC (synthetic 0.05) + floor 0.02 → no drift fired
2. IC drops to 0.01 + floor 0.02 → drift watch starts
3. Sustained 24h+ → CRITICAL log fires; if
   `auto_kill_on_drift=1`, kill_switch trips
4. IC recovers above floor → drift watch resets
5. Warmup (first 24h after deploy) → no false positives

---

## v5.11+ deferred items pre-flight

When opening a v5.11 sub-plan from `2026-05-08-v5.11-deferred-items.md`:

1. Re-run `/plan-check` against the new sub-plan
2. Verify codebase hasn't drifted since the deferred item was
   captured
3. Check the design questions are still relevant (operator may
   have changed mind)
4. Write a fresh PREFLIGHT section for the chosen item

---

## Sprint-level pre-flight (run before Sprint A starts)

Status as of 2026-05-02 pre-flight:

### Foundation verification

- [x] HEAD = `cbad8fb` (v5.9.5g)
- [x] Branch = `feat/v5.9-ml-hardening`
- [x] `./build.sh test gui suite` clean — 1289/0 (verified)
- [x] `/parity-check` on v5.9.5g — GREEN (inline source audit + 0 new warnings)
- [x] All v5.9.5x tags pushed to origin
- [x] Workspace synced (commit `7d89afc`)

### Sprint A readiness

- [x] Master plan exists with Integration Matrix
- [x] All 9 sub-plans drafted
- [x] PREFLIGHT sidecars (this doc)
- [x] `/plan-check` GREEN (last run 2026-05-02)
- [ ] `/parity-check` foundation report folded into sprint
  concerns

### Live deployment gate

- [ ] **Open question:** ship a real stamped model on paper for
  24h+ at MERGE v5.9 → main, before starting v5.10. Plan-level
  question, not blocking sub-ships.

---

## Concerns surfaced by pre-flight (cross-cutting)

These don't fit neatly into a single sub-plan but affect the sprint:

1. **Live validation gap** — by the time we ship Sprint A+B
   (~28 tags), no stamped model has been live-validated for
   sustained operation. Risk: subtle parity issues only surface
   under live tick rates / cadences. **Recommendation:** at
   MERGE v5.9 → `experiment/per-core-sharding`, run a 24h paper
   soak with a real stamped model before starting Sprint B.
   Validate v5.9.5h's hyperparam cfg fields work end-to-end.
2. **Documentation lag** — `DOCS/ML_TRAINING.md` will get
   expanded but no operator-facing "quickstart" guide.
   New users will need a one-page how-to. **v5.11 candidate.**
3. **Multi-symbol future compat** — stamps bind to engine_version
   + feature_registry_hash but not to symbol. Train BTCUSDT,
   deploy ETHUSDT with same data shape → engine doesn't notice.
   **v5.11 candidate.**
4. **End-to-end workflow test** — manual validation per ship
   covers Train → Stamp → Deploy → Paper. No automated E2E
   test. **v5.11 candidate.**
5. **Skill versioning** — `/readiness`, `/parity-check`,
   `/plan-check` evolve. Past verdicts become stale as skills
   update. **v5.11 candidate.**
6. **No automated rollback verification** — every ship creates
   `pre-vX.Y.Z` tag; we never test rollback actually works.
   **v5.11 candidate** (cheap: `git checkout <pre-tag>; ./build.sh
   test`; takes 2 min per ship).
7. **Test count maintenance** — at ~1382 expected tests,
   `controller_test.cpp` will be > 12k lines. **v5.11 candidate**:
   split into multiple test binaries (`controller_test_features.cpp`,
   `controller_test_stamps.cpp`, etc.).
8. **FPN sin/cos design** — v5.10.0b blocks until decided.
   Lookup table recommended. **Design gate before B.1.**

---

## Update log

- 2026-05-02 — initial draft pre-master-plan-check
- 2026-05-02 — `/plan-check` GREEN, foundation pre-flight complete
- 2026-05-02 — foundation parity audit (Sections A-K) GREEN inline.
  No new parity gaps introduced by v5.9.5a-g. Build clean across
  all 3 targets, 1289/0 tests, 0 new warnings beyond pre-existing
  (constprop false-positives in FauxFIX/SPSCRing/ControllerEventLoop —
  unchanged since pre-v5.9).
