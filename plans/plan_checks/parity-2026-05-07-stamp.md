# Parity Check Report: v5.11.41 Multi-Horizon Stamp Body

**Scope:** Audit stamp body schema, production-caller field population, cross-mode determinism contract, per-horizon-specific drift hazards, atomic write contention, HMAC secrets, and snapshot test coverage.

**Plan reference:** `plans/2026-05-07-v5.11.41-multi-horizon-complete.md`

**Audit date:** 2026-05-07

---

## Executive Summary

**Overall verdict:** CRITICAL GAPS FOUND. Plan introduces stamp-body parity drift if not amended per Findings 1–3 below. All per-horizon parameters required to distinguish models at load time are currently **absent from the stamp body** and verifier.

---

## Findings (by severity)

### CRITICAL-1: Missing Per-Horizon Label Parameters in Stamp Body

**Finding:** Plan's per-horizon stamps will embed different `label_forward_ticks`, `label_tp_pct`, `label_sl_pct` values per horizon. However, `StampInferenceCfgInputs` struct (`ML_Headers/ModelInference.hpp:1478–1565`) contains **zero fields** to record these label-defining parameters.

**Evidence:**
- Audit of `StampInferenceCfgInputs` struct (lines 1478–1565) shows fields for:
  - 5 inference-affecting cfg fields (confidence_threshold_scale, barrier_gate_enabled, etc.)
  - Bandit/fee flags
  - Training poll interval
  - Scaler fields
  - Model num_outputs
  - 8 XGBoost hyperparams (max_depth, learning_rate, n_estimators, subsample, colsample_bytree, min_child_weight, seed, tree_method)
  - Build flags hash
  - Grid member count + idx
  - Label registry hash
  - Feature mask
- **No fields for:** `label_lookahead_ticks` (i.e., `label_forward_ticks`), `label_tp_pct`, `label_sl_pct`.

**Impact:** When operator loads a per-horizon model at inference time, the engine has no way to verify the loaded model's training-time label parameters match runtime expectations. Scenario: operator trains model A with `label_forward_ticks=100`, model B with `label_forward_ticks=500`, saves both to same dir, loads model A expecting model B → **silent misprediction**.

**Parity contract violation:** Plan claims per-horizon stamps differ ONLY in label params (section "Parity contract", line 409). But stamps don't record label params, so the difference is invisible to verifier.

**Fix required:** Add 3 fields to `StampInferenceCfgInputs`:
```cpp
int      has_label_params;
int      label_lookahead_ticks;    // aka label_forward_ticks
double   label_tp_pct;
double   label_sl_pct;
```
Then emit in canonical body position 22 (after feature_mask at position 21). Update verifier parser + ModelStampResult struct accordingly.

**Source:** `ML_Headers/ModelInference.hpp:1478–1565` (struct def); `BacktestEngine.hpp:1021–1190` (Backtest_RunFullValidation caller); `Backtest/BacktestEngine.hpp:194–196` (BacktestRunConfig fields exist; never passed to stamp).

---

### CRITICAL-2: Missing xgb_train_nthread in Stamp Body — Cross-Mode Determinism Invisible

**Finding:** Plan pins `xgb_train_nthread=1` in parallel mode per line 340 (per-horizon worker function). However, **`xgb_train_nthread` is NOT in the stamp body**. Parallel-trained stamps are bytewise-identical to serial-trained stamps (same cfg + nthread=1 pinning), but the stamp does not record which mode produced it.

**Consequence:** Operator runs serial Multi-Horizon (4 threads per model default), gets stamps. Later runs parallel (nthread=1 pinned). Stamps appear identical (both have nthread=1 effect). But:
- If a future change enables nthread > 1 in parallel mode, stamps diverge.
- If stamp verification logic is added to enforce mode-matching, verifier cannot detect the mismatch (stamp records nothing about it).
- Operator cannot forensically determine: "did this model train in serial or parallel mode?"

**Existing precedent for mode-recording:** `BacktestEngine.hpp:2376–2379` shows EXISTING forced `xgb_eval_nthread=1` in parallel hyperparameter sweep, with a comment:
```cpp
// Force per-booster nthread=1 in parallel mode for determinism;
// operator's xgb_eval_nthread is preserved in serial mode (only
// overridden when running parallel sweep).
```
This is the same pattern Plan D reuses. But no stamp field records this split behavior.

**Fix required:** Add field to `StampInferenceCfgInputs` to track training-mode thread count:
```cpp
int      has_xgb_train_nthread;
int      xgb_train_nthread;        // training-time per-booster thread count
```
Emit in canonical position 23. Verifier can then log WARN on mismatch (mode divergence detected).

**Mitigation (if deferred):** Document in CHANGELOG that v5.11.41's parallel-mode `xgb_train_nthread=1` pinning is a parity contract, and any future parallelism change must re-audit this.

**Source:** `Backtest/BacktestPanels.hpp:3170–3172` (serial mode reads cfg), line 340 (plan pins nthread=1); no stamp record found via grep.

---

### CRITICAL-3: xgb_train_nthread Field Missing from Backtest_RunFullValidation Stamp Emission

**Finding:** Backtest_RunFullValidation (`BacktestEngine.hpp:1021–1190`) builds `StampInferenceCfgInputs inf` at lines 1106–1174 and populates 8 XGBoost hyperparams (lines 1142–1165). However, **`xgb_train_nthread` is never populated into `inf`**.

**Evidence:**
- Lines 1142–1165: Populates `inf.xgb_max_depth`, `inf.xgb_learning_rate`, ... `inf.xgb_tree_method`.
- No line sets `inf.has_xgb_train_nthread` or `inf.xgb_train_nthread`.
- Comment at line 1136–1140 explains XGBoost hyperparams are for "forensics + reproducibility"; engine load-WARN compares to cfg. But nthread is **explicitly excluded**.

**Why it matters:** Even if nthread is added to the schema (Finding 1 fix), the existing production caller (RFV) doesn't populate it. Plan's per-horizon worker calls RFV per horizon at line 180 (plan), which will **silently omit the nthread field from stamps**.

**Fix required:** In Backtest_RunFullValidation (BacktestEngine.hpp ~1165), after populating other XGBoost params, add:
```cpp
inf.has_xgb_train_nthread = 1;
inf.xgb_train_nthread = data->config_used.xgb_train_nthread > 0 
                        ? data->config_used.xgb_train_nthread : 1;
```

**Note:** This is the v5.9.5b pattern from Finding at line 1097–1103 ("close the half-wired StampInferenceCfgInputs gap"). Plan's per-horizon caller repeats this gap.

**Source:** `BacktestEngine.hpp:1021–1190`.

---

### CRITICAL-4: Per-Horizon Label Parameters Never Passed to Backtest_RunFullValidation

**Finding:** Backtest_RunFullValidation signature (line 1021–1029) takes no label-parameter inputs. Plan's per-horizon worker (line 138–140, plan) mutates `run_control->run_config.label_forward_ticks`, `label_tp_pct`, `label_sl_pct` BEFORE calling Backtest_RunFullValidation. However, **RFV does not read these from the config passed in**; it only reads inference-affecting fields that are already in the cfg.

**Evidence:**
- RFV function signature at line 1021: `Backtest_RunFullValidation(FullValidationResults *out, const BacktestResults *data, const HeldOutSplit *split, int n_splits, int horizon, ...)`.
- Function does NOT take label_forward_ticks, label_tp_pct, label_sl_pct as explicit params.
- RFV reads `data->config_used` (the already-computed BacktestResults' config), not `run_control->run_config`.

**Critical gap:** By the time RFV is called at plan line 180, the labels have already been computed (line 141: `Backtest_ComputeLabelsFromSamples`). RFV trains on those pre-computed labels. RFV **reads the config_used from the BacktestResults struct** (line 1109–1174), which was captured at Collect Features time, not at per-horizon override time.

**Consequence:** Even if plan fixes the per-horizon label params to the cfg before calling RFV, RFV may not see them if `results->config_used` is stale (captured at feature collection, not per-horizon override).

**Verify:** Check what `config_used` is in BacktestResults. If it's a snapshot from Collect Features and never updated per horizon, plan's per-horizon cfg mutations are **invisible to the stamp**.

- `Backtest/BacktestEngine.hpp` lines 240–280 (BacktestResults struct def): `config_used` is a ControllerConfig snapshot. Need to find where it's populated.
- Grep: where is `results->config_used` assigned? If only at Collect Features, per-horizon stamp will use stale config.

**Source:** `BacktestEngine.hpp:1021–1190`; plan lines 138–141, 180–185.

---

## Findings (continued)

### HIGH-5: Production-Caller Field Population (Backtest_RunFullValidation) Status

**Finding:** Plan calls Backtest_RunFullValidation per horizon (plan line 180). This function is the production stamp emitter for Run Full Validation (RFV) button + suite. v5.9.5b audit found and fixed a gap where inference cfg fields were half-wired (comment at line 1097–1103). Plan's per-horizon use inherits this context.

**Evidence:**
- RFV builds StampInferenceCfgInputs at lines 1106–1174.
- All 10 inference cfg fields are populated (confidence_threshold_scale, barrier_gate_enabled, held_out_fraction, freshness_tau, bandit_blend_ratio, fee_rate_maker, fee_rate_taker, training_poll_interval, model_num_outputs, XGBoost hyperparams, build_flags_hash, label_registry_hash, feature_mask).
- **Missing:** xgb_train_nthread (Finding CRITICAL-3).
- **Missing:** Per-horizon label parameters (Finding CRITICAL-1).

**Verdict:** RFV is well-wired for inference cfg binding. Plan's per-horizon use will inherit full coverage **except** the two critical gaps (Findings 1 + 3).

**Source:** `BacktestEngine.hpp:1106–1174`.

---

### HIGH-6: Backtest_ComputeLabelsFromSamples — In-Place Mutation & Parallel Safety

**Finding:** Plan's parallel worker (line 342, plan) allocates isolated `args->isolated_results` with separate labels array. Calls Backtest_ComputeLabelsFromSamples (line 342) which mutates labels in-place. This is safe from race conditions (each thread gets its own labels buffer).

**Evidence:**
- Plan line 318–319: deep-copy of BacktestResults, then `args->isolated_results.labels = malloc(...)` (new buffer).
- Plan line 342: `Backtest_ComputeLabelsFromSamples(&args->isolated_results, &local_cfg)` operates on thread-local buffer.
- Original `results->labels` in main thread never touched during parallel phase.

**Verdict:** PASS. Parallel labels isolation is correct. No data race.

**Source:** Plan lines 315–325, 342.

---

### MEDIUM-7: Stamp Write Atomic Safety Under Parallel Mode

**Finding:** Plan spawns N pthreads, each calls Backtest_RunFullValidation per horizon. RFV internally calls stamp_write_for_model, which uses atomic rename pattern (tmp → final).

**Signature:** `stamp_write_for_model(model_path, ...)` writes to `<model_path>.stamp.tmp`, then renames to `<model_path>.stamp.stamp`. Path is deterministic; each horizon gets different per-horizon dir (plan line 159–160: `horizon_dir` varies per h).

**Evidence:**
- Plan line 171–172: per-horizon auto_stamp_path is built as `"%s/%s.json", horizon_dir, role`.
- Each horizon has distinct `horizon_dir` → distinct stamp paths → no contention.
- ModelInference.hpp lines 1815–1840: tmp-file naming is `<stamp_path>.tmp` (deterministic, no randomness).

**Verdict:** PASS. No file contention; each thread writes to separate per-horizon path. Atomic rename is per-thread-local path.

**Source:** Plan lines 159–172; `ML_Headers/ModelInference.hpp:1815–1840`.

---

### MEDIUM-8: HMAC Secret Handling Across Per-Horizon Stamps

**Finding:** Plan line 174–175 copies same `snap_auto_stamp_secret` to each horizon's FV struct. All per-horizon stamps signed with **same secret**. No per-stamp secrets or salts.

**Evidence:**
- Plan line 106–107 (Phase A): `char snap_auto_stamp_secret[128]` copied from cfg at click time.
- Plan line 173–175: `memcpy(fv->auto_stamp_secret, snap_auto_stamp_secret, n)`.
- stamp_write_for_model (ModelInference.hpp line 1567) takes single `secret` param; HMAC-SHA256 over canonical body.

**Pattern:** Matches existing RFV pattern (line 1180 in BacktestEngine.hpp: single secret passed to stamp_write_for_model).

**Verdict:** PASS. Single shared secret per multi-horizon run. No cross-secret collision risk.

**Source:** Plan lines 106–107, 173–175; BacktestEngine.hpp:1178–1190.

---

### MEDIUM-9: Snapshot Test Coverage for Per-Horizon Stamps

**Finding:** Plan line 224 (section "Tests for `.A`") calls for "Snapshot test: confirm per-horizon stamp body has correct `label_lookahead_ticks` matching its horizon".

**Current test status:** Existing stamp round-trip tests (controller_test.cpp:7530–7720) cover write/verify round-trip, HMAC compat, locale pinning, and atomic writes. **No test currently exists for per-horizon label-parameter snapshot**.

**Consequence:** If Finding CRITICAL-1 is fixed (add label_lookahead_ticks to StampInferenceCfgInputs), the test must verify:
1. Stamp for horizon H1 contains `label_lookahead_ticks=<H1_value>`.
2. Stamp for horizon H2 contains `label_lookahead_ticks=<H2_value>` (different).
3. Verifier correctly extracts both and detects mismatch if engine cfg doesn't match.

**Verdict:** Test is deferred in plan; must be added in Phase B when schema is fixed.

**Source:** Plan line 224; controller_test.cpp:7530–7720 (existing tests).

---

## No Issues Found (PASS)

### PASS-10: Parallel Mode nthread Pinning to 1

**Evidence:** Plan line 340 forces `local_cfg.xgb_train_nthread = 1` in each parallel worker. Existing precedent at BacktestEngine.hpp:2376–2379 (hyperparameter sweep forced `xgb_eval_nthread=1` in parallel for determinism).

**Verdict:** Parity contract is sound (serial nthread vs parallel nthread=1). When fixed stamps record nthread, verifier can detect mode divergence.

**Source:** Plan line 340; BacktestEngine.hpp:2376–2379.

---

### PASS-11: Held-Out Split Isolation Per Thread

**Evidence:** Plan lines 345–348 build per-thread HeldOutSplit via `HeldOutSplit_Make(args->isolated_results.sample_count, ...)`. Each thread's split is independent; no shared state.

**Verdict:** PASS. Held-out split isolation is correct.

**Source:** Plan lines 345–348.

---

### PASS-12: Serialization and Atomicity of Counters

**Evidence:** `volatile int mh_horizon_complete[h]` (plan line 96, Phase A) and atomic progress (line 183) are written by child threads after RFV completes. Main thread reads after pthread_join. No race.

**Verdict:** PASS. Volatile + pthread_join barrier ensures safety.

**Source:** Plan lines 96, 183, 362.

---

## Recommendations

### Immediate (before Phase A starts)

1. **Add label_lookahead_ticks, label_tp_pct, label_sl_pct to StampInferenceCfgInputs** (Finding CRITICAL-1).
   - Add 3 fields + has_label_params flag to struct (ML_Headers/ModelInference.hpp).
   - Update stamp_write_for_model canonical body to emit at position 22.
   - Update verify_model_stamp parser to capture these fields in ModelStampResult.

2. **Add xgb_train_nthread to StampInferenceCfgInputs** (Finding CRITICAL-2).
   - Add 1 field + has_xgb_train_nthread flag to struct.
   - Update stamp_write_for_model canonical body to emit at position 23.
   - Update verifier to log WARN on mode divergence (e.g., stamp trained with nthread=1 but engine cfg has nthread=4).

3. **Populate xgb_train_nthread in Backtest_RunFullValidation** (Finding CRITICAL-3).
   - At BacktestEngine.hpp ~1165 (after other XGBoost params), add population of inf.xgb_train_nthread from data->config_used.

4. **Verify config_used is current for per-horizon RFV calls** (Finding CRITICAL-4).
   - Check where BacktestResults.config_used is set. If only at Collect Features, plan must update it per horizon before calling RFV, OR RFV must accept per-horizon config override param.
   - If RFV cannot see per-horizon cfg mutations, stamps will be silently incorrect.

### Testing (in Phase B)

5. **Add snapshot test for per-horizon label parameters** (Finding MEDIUM-9).
   - Test that 3-horizon run produces 3 stamps with different label_lookahead_ticks.
   - Test that verifier correctly detects label_lookahead_ticks mismatch at load time.

6. **Add determinism test for parallel vs serial** (Plan line 375–378).
   - Verify parallel-trained stamps (nthread=1 forced) are bytewise-identical to serial-trained stamps.
   - This confirms the parity contract holds end-to-end.

### Documentation (Phase F)

7. **Clarify parity contract in CHANGELOG**.
   - Note that v5.11.41 per-horizon stamps differ ONLY in label_lookahead_ticks, label_tp_pct, label_sl_pct (once CRITICAL-1 is fixed).
   - Note that parallel mode forces xgb_train_nthread=1; serial mode uses cfg default.
   - Note that verifier will WARN (not REFUSE) on label-param mismatch, allowing operator to reload correct model.

---

## Summary Table

| Finding | Severity | Category | Status | Fix effort |
|---------|----------|----------|--------|-----------|
| CRITICAL-1 | CRITICAL | Schema gap: missing label params in stamp body | Unfixed | ~30 min (struct + emit + parse) |
| CRITICAL-2 | CRITICAL | Schema gap: missing xgb_train_nthread in stamp body | Unfixed | ~20 min (struct + emit + parse) |
| CRITICAL-3 | CRITICAL | Producer gap: RFV doesn't populate xgb_train_nthread even when schema added | Unfixed | ~10 min (RFV caller update) |
| CRITICAL-4 | CRITICAL | Producer gap: RFV may not see per-horizon cfg mutations (config_used staleness) | Pending verification | ~5–60 min (depends on root cause) |
| HIGH-5 | HIGH | Production-caller audit complete (except Findings 3 + 1) | Partial PASS | N/A (Finding 3 fixes it) |
| HIGH-6 | HIGH | Parallel labels isolation & mutation safety | PASS | N/A |
| MEDIUM-7 | MEDIUM | Atomic stamp write under parallel contention | PASS | N/A |
| MEDIUM-8 | MEDIUM | HMAC secret handling | PASS | N/A |
| MEDIUM-9 | MEDIUM | Snapshot test coverage for label params | Unfixed | ~20 min (add test) |
| PASS-10 | LOW | Parallel nthread pinning to 1 | PASS | N/A |
| PASS-11 | LOW | Held-out split per-thread isolation | PASS | N/A |
| PASS-12 | LOW | Counter atomicity | PASS | N/A |

---

## Blockers for Phase A Start

**The following must be fixed before Phase A coding begins:**
1. CRITICAL-1: Add label_lookahead_ticks, label_tp_pct, label_sl_pct fields to StampInferenceCfgInputs + emit + parse.
2. CRITICAL-2: Add xgb_train_nthread field to StampInferenceCfgInputs + emit + parse.
3. CRITICAL-3: Populate xgb_train_nthread in Backtest_RunFullValidation caller.
4. CRITICAL-4: Verify BacktestResults.config_used is current per horizon OR update plan to pass per-horizon cfg to RFV.

**Estimated total effort:** ~1.5–2 hours (schema additions + producer updates + testing).

---

## Files Affected (Schema Changes)

- `ML_Headers/ModelInference.hpp`: StampInferenceCfgInputs struct + stamp_write_for_model canonical body + verify_model_stamp parser.
- `Backtest/BacktestEngine.hpp`: Backtest_RunFullValidation caller update (populate new fields).
- `tests/controller_test.cpp`: Add per-horizon label-param snapshot test.

---

End of Report.
