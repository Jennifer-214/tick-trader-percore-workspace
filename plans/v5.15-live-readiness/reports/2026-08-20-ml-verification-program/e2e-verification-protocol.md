# OPERATOR VERIFICATION PROTOCOL — buy-side train→serve end-to-end (foxml_suite GUI → engine boot)

> Saved verbatim at receipt 2026-08-20 (orchestrator write per `feedback_save_agent_reports_verbatim`).

**I-class report · 2026-08-20 · engine HEAD 417e524 (`feat/v5.15-live-readiness`)**
Roots covered: `Backtest/ ML_Headers/ CoreFrameworks/ MemHeaders/ GUI/ tests/ DOCS/` + `foxml_suite.cpp` / `main.cpp` (named explicitly per Landmine 19; `tests/` searched by name). Docs walked: `DOCS/CLAUDE_ML_INVARIANTS.md` (production ritual + 3-tier strict, :198-263, :331-353), `DOCS/ML_TEST_RECIPES.md` (Recipe 1 + failure table :262-273). Ledger ground truth: `DOCS/PARITY_ISSUES.md:1703-1762` (PARITY-042/-043), both **re-verified against HEAD code** below, not recalled.

**Two headline corrections to the tasking (both verified):**
1. **The cfg keys are `node_N_*`, not `core_N_*`.** The `core_` prefix is RETIRED and REFUSES BOOT: `[cfg] FATAL: '%s' uses the RETIRED 'core_' key prefix … Boot REFUSED.` — `CoreFrameworks/ControllerConfig.hpp:3486-3489`. Real keys: `node_0_strategy=ml` (:3282-3287), `node_0_model_dir=…` (:3281), `node_0_model_path=…` (:3279).
2. **`model_path` ("models/buy_signal.json") is dead on the reachable train path.** Since v5.11.44 the "Train Model" button routes through `train_multi_horizon_worker_fn` with N=1 (`Backtest/BacktestPanels.hpp:5784-5876`, spawn :5875; second spawn site :6080 for N>1). The snapped `model_path` is consumed only in the `#ifndef USE_XGBOOST` void-cast branch (:4946). The old `train_model_worker_fn` (:3657) has **zero** `pthread_create` sites (uncapped probe, rc=0, two hits both = the MH worker) — it is compiled-in dead code. Output paths come exclusively from `run_name`: `models/<classification|regression>/<run>_horizon_<H>/<role>.json` (:4304-4307).

---

## 1. Numbered operator protocol (step → action → expected evidence → failure meaning)

### Step 0 — Pre-flight (before launching foxml_suite)
- **Action:** confirm `backtest.cfg` and `engine.cfg` agree on stamp-bound fields; set the same HMAC secret in both: trainer signs with **`auto_stamp_secret`** (from the Training panel's secret field, falling back to backtest-cfg `auto_stamp_secret` — `BacktestPanels.hpp:5857-5867`); the engine's ensemble loader verifies with **`held_out_stamp_secret`** (`CoreFrameworks/EngineCommon.hpp:369`). Different values ⇒ signature mismatch at load.
- **Evidence:** at suite launch the log shows `[suite] stderr → logging/foxml_suite.log` (`foxml_suite.cpp:166-169`). If the cfgs differ bytewise you get the loud multi-line `[suite] !!! engine.cfg / backtest.cfg DIVERGENT !!!` banner (`foxml_suite.cpp:387-393`) — treat as a real warning: stamp bodies encode backtest.cfg state; the engine compares against engine.cfg.
- **Where the Log panel reads from:** suite Log panel tails `logging/foxml_suite.log` (`foxml_suite.cpp:323`); the engine GUI Log panel tails `logging/engine.log` (`GUI/GuiThread.hpp:84`).

### Step 1 — Data: select files
- **Action:** Data panel → Scan → check ≥1 CSV.
- **Evidence:** the "Collect Features" button becomes enabled. It is disabled by `data->selected_count > 0` failing (`BacktestPanels.hpp:5203-5204`) with grey caption **"Select data files first"** (:5260), or while a run is live: yellow **"running... (N%)"** (:5258).

### Step 2 — Collect Features (single horizon; the ≤1-horizon-CSV mode)
- **Action:** Training panel → leave Horizons CSV empty or one value → click **Collect Features** (:5211). Spawns `backtest_worker_fn` (:5245) → `Backtest_Run` → `SamplesSnapshot_Compute` → `complete=1, running=0` (:350-367).
- **Expected log evidence, in order** (all in `logging/foxml_suite.log`):
  1. `[backtest sharded] mode=sharded nodes=<N> default_strategy=<d>` — `Backtest/BacktestSharded.hpp:145`
  2. `[backtest] loaded <N> ticks from <path>` per file — `Backtest/BacktestEngine.hpp:144`
  3. `[backtest sharded] warmup complete at tick <N> …` — `BacktestSharded.hpp:731`
  4. `[backtest sharded] completed: <N> ticks in <T>ms, <n> trades (<w>/<l> W/L), P&L $<x>` — :906
  5. `[backtest] label_compute: streaming 2-file window — peak <M> MB (<F> files, <T> total ticks)` — `BacktestEngine.hpp:777-780`
  6. **The success sentinel:** `[backtest] computed <N> labels (type=<t>, tp=<x>%, sl=<y>%)` — :930-931, with optional real-warning suffix ` — NaN/Inf: <n> total, <m> dropped (multiclass)` (:932-936).
- **Expected GUI evidence:** binary labels (default `LABEL_WIN_LOSS`, :3168) render `Samples: <N>  |  +: <p>  |  -: <n>  |  neutral: <k>  |  Ratio: <r>%` (:5557-5561) plus a colored `Diagnosis:` line; regression renders the range/σ form (:5439-5440); multiclass the per-class histogram (:5491-5498).
- **Sample-count math for the oracle:** one sample per slow-path cycle after warmup — collection is gated on `tick_index >= cfg.warmup_ticks` AND `rolling->count >= cfg.min_warmup_samples` (`BacktestSharded.hpp:462-463`), so expect roughly `(ticks − warmup) / poll_interval` samples. `sample_count == 0` with a completed run means the dataset is smaller than warmup — not a bug.
- **Multi-horizon variant:** "Collect Multi-Horizon" (N>1) additionally logs per horizon `[collect-mh] horizon=<H> ticks tp=<x>% sl=<y>%: <v> valid samples (<p> pos, <n> neg, <k> neutral) of <t> total` (:475-478) — this is the class-distribution preview line the button exists for (:384-387).

### Step 3 — Train Model (single horizon, default UI values)
- **Action:** click **Train Model** (enabled only when `sample_count >= 10` and no worker running and XGBoost compiled — :5720-5728). Routes to the MH worker with N=1; the effective horizon = Horizons CSV[0] if typed, else `label_forward_ticks` = **1000** default (:5803-5806, :3191).
- **Expected log evidence, in order:**
  1. `[mh-train] starting multi-horizon train: 1 horizons, <N> samples, run_name='run'` — :4748-4750
  2. `[mh-train] serial mode: 1 horizons sequential (xgb_train_nthread=<n> from cfg)` — :4896-4898 (parallel-mode line :4789 for N≥2)
  3. `[backtest] computed <N> labels …` again (per-horizon label recompute, :4270)
  4. `[validation] generated <k>/<n> valid folds …` + `[validation] fold summary:` block — `Backtest/ValidationSplit.hpp:221, :343-352`
  5. **The stamp sentinel:** `[autostamp] wrote models/classification/run_horizon_1000/buy_signal.json.stamp` — `BacktestEngine.hpp:1456` (stamp path = model path + `.stamp`, `ML_Headers/ModelInference.hpp:2368`; atomic `.stamp.tmp`→rename :2374-2387)
- **Expected GUI evidence:** per-horizon status cell progresses `h=1000: computing labels...` (:4264) → `h=1000: training final model for save+stamp...` (:4378) → `h=1000: WF + held-out (<k> folds)...` (:4453) → terminal **`h=1000 OK: WF=<a> HO=<b> gap=<c> stamped`** (:4474-4477). Final `status_msg`: **`Multi-horizon: 1/1 horizons trained, 1 validated (held-out), 1 stamped. Models in models/<class>/run_horizon_*/.`** (:4934-4937).
- **Artifacts on disk (given defaults run_name="run", label WIN_LOSS→role buy_signal, subdir classification — :4291-4297):**

  | File | Producer | Note |
  |---|---|---|
  | `models/classification/run_horizon_1000/buy_signal.json` | `XGBoosterSaveModel` :4438 | the deployable model |
  | `models/classification/run_horizon_1000/buy_signal.json.stamp` | `Stamp_AssembleAndEmit` → `stamp_write_for_model` (`BacktestEngine.hpp:1440`, `StampHelper.hpp:447`) | HMAC body; `MODEL_FORMAT_VERSION` = **6** (`ModelInference.hpp:151`) |
  | `models/classification/run_horizon_1000/summary.txt` | :4502-4561 | canonical field names incl. `auto_stamp_ok: 1` + `auto_stamp_path_written:` |
  | **NO `.scaler` file** | — | see the critical caveat below |

- **CRITICAL caveat — no scaler on the reachable path.** `FeatureStandardizer_Compute/_Persist` exist ONLY inside the dead `train_model_worker_fn` (:3941, :3958); `mh_run_one_horizon_fv` + `Backtest_RunFullValidation` never compute one, and `Stamp_AssembleAndEmit` only binds a scaler when the caller passes `scaler_sha256_hex` (`StampHelper.hpp:392-400`), which RFV never does (`BacktestEngine.hpp:1390-1444` sets no scaler field). Ergo the stamp has `feature_scaler_present` absent, the engine's scaler block is skipped (`NodeModelZoo.hpp:530` gate), and ML Status will show sand-colored **`scaler: NONE`** — that is the EXPECTED state, not a failure. The v5.9.3 scaler verification chain (stamp sha256 → sidecar → registry-hash) is **unreachable from the GUI at HEAD**; `DOCS/ML_TEST_RECIPES.md` Recipe 1 item 5 and CLAUDE_ML_INVARIANTS' "Sidecar files travel with model" describe the dead path.
- **Also expected-absent:** `state->model_trained` stays false (only the dead worker sets it, :3705/:4098), so anything gated on it (legacy displays) stays dark; `tm_phase_msg`/`tm_running` progress UI belongs to the dead worker too (:5736) — the LIVE progress surface is the MH bar + per-horizon table.

### Step 4 — Verify Stamp (PastRuns panel)
- **Action:** Past Runs → the run row → **Verify Stamp** (`BacktestPanels.hpp:2162`). Probes role files `barrier.json, buy_signal.json, regime.json, *.xgb` under `r->full_path` (:2170-2185), then `verify_model_stamp` with the suite build's `FEATURE_REGISTRY_HASH()` + `LABEL_REGISTRY_HASH()` + `MODEL_FORMAT_VERSION` (:2200-2206). Verify secret = suite cfg `auto_stamp_secret` (:2196-2199).
- **Expected strings (exact):**
  - Green, secret set: `OK (signature verified) — engine=<ver> registry=<hash16>` (:2218-2225)
  - Green, no secret: `OK (devmode, signature UNVERIFIED — set auto_stamp_secret in engine.cfg) — engine=<ver> registry=<hash16>` — devmode green is NOT cryptographic proof
  - Red: `FAIL — <reason>` (:2227-2228) where reason ∈ the `verify_model_stamp` set: `stamp file missing: <p>` (`ModelInference.hpp:1623`) · `format-version mismatch: stamp=<a> engine=<b>` (:1821) · `feature-registry-hash mismatch: stamp=<x> engine=<y> (retrain required)` (:1842) · `label-registry-hash mismatch: … (label set drift; retrain required)` (:1865) · `generalization gap <g> exceeds threshold <t>` (:1908) · `model file hash differs from stamp: …` (:1918) · `signature mismatch: stamp=… computed=…` (:1960) · `pre-epoch stamp (…)` (:1811) · `stamp_format_version too new: …` (:1793).
- **"Stamp details" tree** (renders on green, :2246+): shows `gap`, `model_format_ver: 6`, `engine_version`, `registry_hash`, `model_num_outputs`, `training_poll`. **Known-absent sections:** the scaler block (no scaler, above) and the "Recorded cfg at training time:" block (:2301 gated on `STAMP_HAS(v, inference_cfg)` — never set in any production stamp; PARITY-042). Their absence is expected, proves nothing.
- **Cross-check the registry hash:** the `registry=<hash16>` shown must equal the `registry:` value in the Engine header line of the binary you will serve with (`GUI/EngineHeaderPanel.hpp:52-54` — rendered in both suite and engine_gui). Suite and engine must be built from the same tree for this to hold.

### Step 5 — Engine cfg (serve side)
- **Action:** in `engine.cfg`: `node_0_strategy=ml` + **one** of two deployment shapes (this fork changes what verification runs — see the option matrix):
  - **Shape A (base dir, RECOMMENDED):** `node_0_model_dir=models/classification/run` — ensemble auto-detect scans `run_horizon_*` siblings (`NodeModelZoo.hpp:2469-2534`; workflow comment :2347-2351).
  - **Shape B (horizon dir):** `node_0_model_dir=models/classification/run_horizon_1000` — single-zoo `LoadFromDir`.
- Set `held_out_stamp_secret=<same value as auto_stamp_secret>` and choose `held_out_gate_strict` (0 warn / 1 refuse / -1 skip — `NodeModelZoo.hpp:256-267`).

### Step 6 — Engine boot: load verification
- **Shape A expected boot-log lines** (in `logging/engine.log`), in order:
  1. `[sharded] node 0: zoo from models/classification/run, 0 role(s) loaded` (`EngineCommon.hpp:320-321`) — **"0 role(s)" is EXPECTED here** (the base dir itself contains no model; sibling dirs do)
  2. Per arm: `[model] models/classification/run_horizon_1000/buy_signal.json: trained_engine=<ver> registry=<hash16> (current=<ver>/<hash16>) — ok (signature verified, gap <g> ≤ <t>)` (`NodeModelZoo.hpp:327-333`; reason string :1956). With empty secret the suffix is `ok (dev mode, sig unchecked)` (:1939).
  3. `[ensemble_auto_detect] OK: 1/1 handles agree on grid_member_count=1` (:2443-2445)
  4. `[ensemble] auto-detected 1 horizons under 'models/classification/run': {1000}` (:2580-2581)
  5. `[sharded] node 0: ensemble active (primary=buy_signal, 1 horizons; 1 total models)` (`EngineCommon.hpp:374-379`)
- **Shape B expected:** `[sharded] node 0: zoo from models/classification/run_horizon_1000, 1 role(s) loaded` + the `[model] … — ok …` line; no ensemble lines. **Plus the false cfg-drift lines of § 2** (Shape B runs the drift walk; Shape A skips it — `EngineCommon.hpp:413` gates `NodeModelZoo_ValidateAgainstCfg` on single-zoo `loaded`).
- **strict-mode differences at load:**
  - `held_out_gate_strict=1`: any `sr.valid<=0` ⇒ `[held-out gate] REFUSING to load <path> — <reason> (strict mode)` and the role does not load (`NodeModelZoo.hpp:311-315`). Gap>threshold, hash mismatches, signature mismatch (where a secret is actually passed) all refuse.
  - `held_out_gate_strict=0`: same reasons become `[held-out gate] WARN: <path> — <reason> (strict=0, loading anyway)` (:318-320) — a WARN-load here is a REAL signal, read the reason.
  - **Asymmetry (verified):** the single-zoo path hardcodes `/*secret=*/nullptr` (`EngineCommon.hpp:315`) ⇒ Shape B **never HMAC-verifies** regardless of cfg, and sets `FAILURE_MASK_stamp_hmac_not_verified` (`NodeModelZoo.hpp:612-614`; the v5.15.2 live boot gate refuses on it when `trading_mode=live`). Shape A passes `cfg.held_out_stamp_secret` (:369) and DOES verify. This inverts the naive expectation that the simpler shape is better-verified.

### Step 7 — ML Status panel (LIVE vs warmup vs failed)
All strings from `GUI/MLStatusPanel.hpp`:
- **Warmup:** `warmup: <N>%` (:73-74) until `min_warmup_samples` reached — predictions disabled meanwhile; this is normal for minutes after boot.
- **LIVE:** `model: ensemble (1 horizons)` (:107-108, Shape A) or `model: loaded` (:105, Shape B), then live `pred:`/`thr:`/`conf:` values (:150-179) once warm.
- **Failed:** `model: LOAD FAILED` red (:97) — strict-mode refusal or missing files; `model: CORRUPT — RETRAIN` red (:89, D-221 barrier corruption); `model: (none configured)` sand (:116).
- **Scaler:** `scaler: NONE` sand = EXPECTED at HEAD (:271-274); `scaler: applied` green (:264) cannot occur for a HEAD-trained model; `scaler: WARN — load failed` red (:254) would indicate a stamp claiming a scaler that is absent — cannot occur for HEAD-trained stamps.
- **Drift summary:** `cfg drift: <a> Tier 1 (WARN), <b> Tier 2` orange / `… (REFUSED strict) …` red / `cfg drift: <b> Tier 2 (WARN)` (:284-299) — in Shape B expect the FALSE counts of § 2; in Shape A expect zeros (walk skipped).

---

## 2. KNOWN-FALSE noise inventory (ignore exactly these; every OTHER drift line is real)

### 2a. PARITY-043 — reachable rows that ALWAYS fire falsely (Shape B boots + hot-swap)
Re-verified at HEAD: the only writes to `thompson_mu_prior/precision_prior/precision_obs` anywhere in `ML_Headers/ CoreFrameworks/ Strategies/ Backtest/ MemHeaders/` are the **cfg defaults** (`ControllerConfig.hpp:2199-2201`); an uncapped probe for `h->bandit_blend_ratio= / h->ml_tp_pct= / h->fee_rate_maker= / ->barrier_blend_mode=` returns **zero hits** (rc=1) — the handle side of the cohort is written by nothing and stays 0. The sr→handle inference_cfg copy covers only 3 legacy fields and is gated on the never-set group bit (`NodeModelZoo.hpp:459-468`). Gates are **cfg-only** (`MlCfgFlagRegistry.hpp:130-144`), and `bandit_enabled` **defaults ON since 2026-08-16** (`ControllerConfig.hpp:2004-2012` — note the header comment ":2000 all 7 flags off" is STALE).

**At an all-default cfg, per walked handle** (line format assembled from `ModelValidation.hpp:209-212` + `log_drift_pair` `%.6g` :124; `loc` = `node <N>` or `node <N> ensemble[<h>]` :172-176):

```
[cfg-drift] INFERENCE_CFG WARN_ALWAYS: node 0 role=buy_signal stamp.bandit_blend_ratio=0 cfg.bandit_blend_ratio=0.3 — Tier 2 bandit_blend_ratio drift (gated by bandit_enabled cohort; WARN)
[cfg-drift] INFERENCE_CFG REFUSE_STRICT: node 0 role=buy_signal stamp.thompson_precision_prior=0 cfg.thompson_precision_prior=1 — Tier 1 thompson_precision_prior drift (parity-critical; posterior precision prior)
[cfg-drift] INFERENCE_CFG REFUSE_STRICT: node 0 role=buy_signal stamp.thompson_precision_obs=0 cfg.thompson_precision_obs=1 — Tier 1 thompson_precision_obs drift (parity-critical; observation precision)
```
(Registry rows: `CfgDriftCheckRegistry.hpp:268-271, :282-285, :286-289`.)

- These repeat for **all 4 single-zoo role handles including unloaded zero-handles** (`check_handle` guards only pointer-null, `ModelValidation.hpp:168-169`; walked :231-234) ⇒ expected ML Status summary in Shape B: **`cfg drift: 8 Tier 1 (WARN), 4 Tier 2`** per node. *(Inferred from code, not compile-probed — refute spot R1.)*
- With `held_out_gate_strict=1` additionally: `[cfg-drift] FATAL: node 0 had 8 Tier 1 mismatch(es) in strict mode. Set held_out_gate_strict=0 (warn-only) OR acknowledge_inference_cfg_drift=1 …` (`ModelValidation.hpp:267-274`) — **but at BOOT the engine continues anyway**: the return value is discarded at `EngineCommon.hpp:416` ("engine continues (TODO v5.10: free + refuse)" :411). Only the hot-swap sites capture it (`EngineSharded/Run.hpp:1915, :1980`).
- **Conditional false lines** (fire only if the operator flips the gate; handle side is permanently 0, so ANY non-zero cfg value mints a false line): `bandit_algorithm` ≠0 (:274-277) · `thompson_mu_prior` ≠0 (:278-281) · `thompson_exp3_blend_alpha` when `bandit_algorithm=4` (0 vs default 0.5, :290-293) · `fee_rate_maker`/`fee_rate_taker` when `cost_gate_enabled=1` (0 vs 0.00075/0.001 — :294-301, defaults `ControllerConfig.hpp:1902-1903`) · `ml_tp_pct`/`ml_sl_pct`/`barrier_blend_mode` when `per_horizon_barrier_blend=1` (0 vs 0.015/0.008/mode — :318-329, defaults :2081-2082, :2268).
- **Protocol instruction:** ignore exactly the `[cfg-drift] INFERENCE_CFG` lines for the fields named above. **Every `[cfg-drift] CROSS_BINARY` line is REAL** — `training_poll_interval, xgb_subsample, xgb_colsample_bytree, xgb_min_child_weight, xgb_seed, xgb_tree_method, build_flags_hash, xgb_train_nthread` compare genuinely copied stamp values (`NodeModelZoo.hpp:376-406`) against cfg. Do NOT set `acknowledge_inference_cfg_drift=1` to silence the noise — it suppresses the whole INFERENCE_CFG category including any future real Tier-1 (`ModelValidation.hpp:176-177`).

### 2b. PARITY-042 — the VACUOUS layer (its silence proves nothing)
Verified at HEAD: `cfg_gate::lookup_drift` returns `stamp_has_inference_cfg && (expr)` on **every** branch including both defaults (`MemHeaders/CfgGateRegistry.hpp:186-208`), and no production emit sets the `inference_cfg` group bit (only the test fixture does — `tests/controller_test.cpp:15566-15584`, whose own comment says "THIS FIXTURE IS WHY THE VACUITY SURVIVED"). Therefore:
- The **load-time sr↔cfg drift walk** (`DRIFT_CHECK_FROM_DERIVED`, `NodeModelZoo.hpp:304`) never increments `inference_cfg_drift_count`, so the `sr.valid=0` REFUSE at :305-307 **cannot fire** — a clean `[model] … — ok` line does NOT certify cfg parity.
- The 4 `STAMP_HAS(*h, inference_cfg)`-gated registry rows — `confidence_threshold_scale` (:257), `barrier_gate_enabled` (:261), `confidence_hard_block_threshold` (:266), `per_horizon_barrier_blend` (:332) — **cannot fire**, in every mode. Their absence from the log is not evidence of parity.
- Corollary: **at HEAD there is NO functioning train↔serve cfg-parity gate at all.** The only real cfg-parity control the operator has is Step 0 (keep backtest.cfg ≡ engine.cfg) plus the suite's DIVERGENT banner.
- Shape A additionally skips the whole `ValidateAgainstCfg` walk (`EngineCommon.hpp:413` — gated on single-zoo `loaded`) AND the sr-side walk + `model_max_age` check (ensemble `TryLoadRole` calls pass no `cfg_ptr`, `NodeModelZoo.hpp:2127-2164`, cfg-gated ages at :621-629) — so Shape A's silence on drift is triply uninformative.

### 2c. Other known-false / stale text the operator may hit
- `[ensemble_auto_detect] WARN: … TODO(v5.10.X): wire stamp_write_for_model into train_multi_horizon_worker_fn to emit stamps.` (:2447-2453) — the TODO clause is stale (stamps ARE emitted since v5.11.47); the WARN itself only appears for genuinely legacy/unstamped siblings.
- The `(stamp skipped: auto_stamp_on_held_out=0 in cfg)` branch text (`BacktestPanels.hpp:4484-4488`) — dead since v5.11.47 made stamping unconditional (:4329-4336); if you see "stamp skipped" the operative reason is the write-error string.
- Registry/self-descriptions claiming "18 entries" (`CfgDriftCheckRegistry.hpp:10, :79, :201`; `ModelValidation.hpp:285-286`) — actual count is **23**, test-pinned (`controller_test.cpp:26864-26867`).
- `ControllerConfig.hpp:2000` "all 7 flags off (backward compat)" — stale; bandit_enabled=1 (:2012).

---

## 3. Refusal-point table

| Phase | Refusal/degrade point | Surface + cite | Meaning |
|---|---|---|---|
| Collect (button) | `selected_count==0` → disabled, "Select data files first" | `BacktestPanels.hpp:5203, :5260` | no data selected |
| Collect (button) | `running` → disabled, "running... (N%)" | :5204, :5258 | double-click guard |
| Collect MH (button) | TP/SL CSV misaligned vs horizon count | :5285-5291 | broadcast-or-match rule violated |
| Collect (run) | `[backtest] failed to open <p>` | `BacktestEngine.hpp:92` | bad path |
| Collect (run) | `[backtest sharded] FATAL: partial-exit cfg …` | `BacktestSharded.hpp:166` | cfg invariant |
| Collect (run) | `failed to allocate tick buffer` / `failed to grow sample buffers to <N> (<M> MB)` | :590 / `BacktestEngine.hpp:433` | OOM; capacity guard silently STOPS collection (`BacktestSharded.hpp:465-466`) |
| Collect (run) | warmup gates: no samples until `warmup_ticks` + `min_warmup_samples` | `BacktestSharded.hpp:462-463` | small dataset ⇒ 0 samples, run still "completes" |
| Collect (run) | `[backtest] WARN: NaN/Inf in feature pack at tick <N> — skipping sample (further skips silent)` | :524 | real data-quality warning; first occurrence only |
| Label pass | per-file open fail / sort-validation abort / OOM | `BacktestEngine.hpp:750, :820-825, :743, :773` | labels partially/none computed |
| Train (button) | `sample_count < 10` → "Collect features first (need 10+ samples)" | `BacktestPanels.hpp:5726, :5884-5886` | collect first |
| Train (button) | no XGBoost → "Build with -DUSE_XGBOOST=ON" | :5727-5728, :5880-5882 | wrong build |
| Train (worker) | `Multi-horizon: cfg.horizon_list empty; set horizons first.` | :4733-4738 | no horizons resolvable |
| Train (worker) | `Multi-horizon: Collect Features first.` | :4740-4745 | sample_count 0 |
| Train (per-horizon) | **`n_valid < 50`** → `h=<H> FAILED: only <n> valid labels (need >= 50)` + `[mh-train] horizon <H>: only <n> valid labels; skip` | :4272-4284 | too few non-NaN labels at this horizon |
| Train (save) | `[mh-train] horizon <H>: SaveModel(<p>) failed: <err>` | :4438-4443 | disk/XGB error; stamp will then fail sha256 |
| Train (stamp) | `A6 (D-221): REFUSING corrupt barrier label_tp_pct=… label_sl_pct=…` | `StampHelper.hpp:368-376` | corrupt barrier refused at SOURCE |
| Train (stamp) | `[autostamp] FAIL: <error>` (`could not sha256 <p>` / fopen / rename…) | `BacktestEngine.hpp:1463`; `ModelInference.hpp:2200-2387` | stamp not written |
| Train (FV) | `[FULLVALIDATION] split is locked or null` / `no samples to run on` | `BacktestEngine.hpp:1331, :1336` | internal split invariant |
| Train (FV) | `h=<H> FAILED: held-out did not complete` / `h=<H> CANCELLED mid-validation` | `BacktestPanels.hpp:4493-4499` | cancel or eval failure |
| Engine load | `[held-out gate] REFUSING to load <p> — <reason> (strict mode)` (strict=1) / same as WARN (strict=0) | `NodeModelZoo.hpp:310-320` | reason = the § 1 Step 4 string set |
| Engine load | `[model] REFUSING <p> — stamp claims model_num_outputs=<k> …` / `label_lookahead_ticks=<t>` vs dir | :489-497, :514 | architecture/dir mismatch |
| Engine load | `[ensemble_auto_detect] REFUSED: … Mixed-training-run ensemble.` → whole ensemble unwound | :2432-2437, :2565-2569 | siblings from different training runs |
| Engine boot | `[cfg] FATAL: … RETIRED 'core_' key prefix … Boot REFUSED.` | `ControllerConfig.hpp:3486-3489` | rename keys to `node_*` |
| Engine run | `model: LOAD FAILED` / `model: CORRUPT — RETRAIN` in ML Status | `MLStatusPanel.hpp:97, :89` | per § 1 Step 7 |

---

## 4. Existing automated coverage (what the GUI run adds vs what is already test-pinned)

**Already test-pinned in `tests/controller_test.cpp`** (no new information from the operator run):
- Train-serve feature parity with `collect_features=1`: dual bytewise-identical runs + perturbation non-tautology control (:14110-14172); label-compute fixtures (:19445, :19505, :19534).
- Stamp write→verify round-trip incl. bash parity, hash emission, engine-version, strict-vs-warn `TryLoadRole` (:11484+, :13153, :13623, :14297-14347 with :14314/:14331), scaler write/read/corrupt/drift round-trips (:4835-4839, :14955-15180), `Stamp_AssembleAndEmit` on a default cfg (:28420-28599).
- Ensemble `AutoDetectFromDir` lifecycle with synthetic siblings (:19057-19102); handle scaler-sha round-trip (:20147); drift-registry row count == 23 (:26864-26867).

**NOT covered anywhere — the operator run is the ONLY verification of:**
- Real XGBoost training→save→metrics. `controller_test` is deliberately zero-dep (:11390-11395); its comment defers real-metric assertions to a "suite-build smoke test" that **does not exist** (probe: `rg -n "smoke" CMakeLists.txt build.sh` → zero hits; §2.5 guard-existence class — stale promise).
- The GUI click wiring itself (Class 12/24 — exactly what this protocol exists to exercise), the on-disk artifact layout of a real run, engine load of REAL trained artifacts, and the drift-line behavior at HEAD defaults (the drift fixture is explicitly green-for-the-wrong-reason, :15566-15584; the false-firing `ValidateAgainstCfg` walk has no production-shaped test).

---

## 5. Option matrix (deployment shape for the load-verification step)

| Option | What runs | What it proves | What it silently skips |
|---|---|---|---|
| **O1 — Shape B** (`node_0_model_dir` = horizon dir) | single-zoo load; sr-side walk (vacuous per PARITY-042) + `ValidateAgainstCfg` walk | `[model] ok` line, format/hash/gap gates; exercises the CROSS_BINARY drift rows (real) | **HMAC never verified** (secret=nullptr hardcoded, `EngineCommon.hpp:315`); emits the § 2a false lines |
| **O2 — Shape A** (base dir, RECOMMENDED) | ensemble auto-detect + grid-consistency | HMAC verified with `held_out_stamp_secret`; per-arm `[model] ok (signature verified…)`; grid agreement | `ValidateAgainstCfg` walk, sr-side drift, `model_max_age` — ALL skipped (`EngineCommon.hpp:413`; no `cfg_ptr` in ensemble loads) |
| **O3 — novel alternative considered: headless/CLI verification** (stamp re-verify via `tools/stamp_model.sh` family + `sha256sum` + `cat summary.txt`, skipping the GUI) | file-level artifact checks | artifact integrity without a GUI session | REJECTED as primary: no CLI training entry exists (TECH_DEBT-034 open), and the acceptance oracle this mission needs is precisely the OPERATOR-VISIBLE surface (Class 12 "wired-but-unexercised" is the target bug class — `DOCS/CLAUDE_ML_INVARIANTS.md:267-290`). Retained as a supplement to Step 3 (independent `sha256sum buy_signal.json` vs the stamp's `model_sha` line). |

**Recommendation:** run the protocol with **O2** for the load step (only shape with cryptographic verification), and — if the operator wants the CROSS_BINARY drift rows exercised once — an optional second boot in O1 with § 2a as the ignore-list. Record in the run notes that at HEAD **no cfg-parity gate is live** (PARITY-042 + -043), so cfg-parity rests entirely on Step 0's file-level equality until the PARITY-043 parse→handle leg / PARITY-042 re-key lands.

---

## 6. Spots most worth an adversarial refute (for the paired a-class)

- **R1 — the ×4 zero-handle multiplication** (§ 2a: "8 Tier 1, 4 Tier 2"): inferred from `check_handle`'s pointer-only guard (`ModelValidation.hpp:168-169`) + `NodeModelZoo_Init` zeroing; NOT compile-probed. A probe or an upstream `Model_IsLoaded` gate I missed would change the expected counts (not the per-line text).
- **R2 — single-zoo secret=nullptr generality**: verified at `EngineCommon.hpp:315` (the shared boot). The hot-swap paths (`EngineSharded/Run.hpp:1915, :1980`) were NOT read end-to-end — they may pass the secret, which would narrow the "Shape B never HMAC-verifies" claim to boot only.
- **R3 — no-scaler claim**: grounded on an uncapped `FeatureStandardizer_Compute|_Persist|_FitWinsor` probe across `Backtest/ ML_Headers/ CoreFrameworks/` (only dead-worker + header hits). `HeldOutSplit_TrainEval`'s internals were not read; if it persisted a scaler it would refute § 1 Step 3's caveat.
- **R4 — bandit_enabled default ON**: verified in `_Default` (:2012); the operator's actual `engine.cfg` may explicitly set `bandit_enabled=0`, which would silence the § 2a triple (gate false) — the protocol's ignore-list is default-cfg-conditioned.
- **R5 — the emit half's cohort gating**: I did not read `cfg_derived::populate_stamp_cfg_from_derived` row gates; if the trainer's backtest.cfg diverges from engine.cfg on a STAMP_BOUND field, extra REAL `[held-out gate] WARN` lines could appear that my protocol doesn't enumerate (they would be truthful — but the a-class should confirm the sr-side walk truly cannot fire so no such WARN can originate from the vacuous layer).
- **R6 — Shape A `loaded==0`**: rests on `LoadFromDir` failing for a nonexistent base dir; if `LoadFromDir` has a fallback that "loads" something from the parent, the drift walk would run in Shape A too and the § 2a lines would appear there as well.

**Findings worth fixing regardless (surfaced per §2.5 comment-truth duty):** stale "18 entries" self-descriptions (`CfgDriftCheckRegistry.hpp:10/:79/:201`, `ModelValidation.hpp:285-286`); stale "all 7 flags off" (`ControllerConfig.hpp:2000`); stale smoke-test promise (`controller_test.cpp:11394`); dead-but-compiled `train_model_worker_fn` + its scaler pipeline (H21 dead-code removal candidate — it is the only holder of the v5.9.3 scaler emit, so its deletion should be coupled to a decision on restoring scaler emission in the MH path); the boot-time discard of `ValidateAgainstCfg`'s strict REFUSE (`EngineCommon.hpp:411-421` TODO); the single-zoo `secret=nullptr` (R2).
