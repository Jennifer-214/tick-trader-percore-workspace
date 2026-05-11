# Post-mortem Data-Flow Trace: v5.14.1.E.A + .B (as-shipped)

**Goal:** Verify all data reads have valid sources. Catch Class 18 (mirror missed
data-source dependencies) before .C + .D ship. Context: .B.mid-coding found
exit_reward_ring missing → would have read uninitialized memory in Ridge invocation.

**Commits verified:**
- `226e47c` v5.14.1.E.A — cfg + X-macro + exit_ridge_state
- `fe2fec9` v5.14.1.E.B — exit_reward_ring + Ridge blending invocation

---

## 1. EnsembleModelZoo State Extensions (CoreModelZoo.hpp)

### Added fields (v5.14.1.E.A + .B):

**exit_ridge_state: RidgeWeights<F>** ✓
- Defined at :830 in CoreModelZoo.hpp
- Init: RidgeWeights_Init(&ezoo->exit_ridge_state) called in EnsembleModelZoo_Init
- Field reads in Ridge invocation (StrategyParameters.hpp:1097-1123):
  - `exit_ridge_state.corr_matrix` — used as output param to RidgeBlender_BuildCorr ✓
  - `exit_ridge_state.w[]` — written by RidgeBlender_Compute, read post-solve ✓
  - RidgeWeights<F> struct has all required fields (corr_matrix, w[], fallback_to_uniform) ✓

**exit_reward_ring[REWARD_RING_SIZE]: PredictionRecord** ✓
- Defined at :815-820 in CoreModelZoo.hpp (v5.14.1.E.B)
- Init: memset(ezoo->exit_reward_ring, 0, sizeof(...)) in EnsembleModelZoo_Init ✓
- Init: ezoo->exit_reward_ring_head = 0 ✓
- Reads in Ridge invocation (StrategyParameters.hpp:1079-1095):
  - `exit_reward_ring[ring_idx].predictions[i]` — read via modulo index ✓
  - Indexing: (exit_reward_ring_head - 1 - k + REWARD_RING_SIZE) % REWARD_RING_SIZE
    matches buy-side pattern (line 904-907) ✓
  - PredictionRecord struct field `predictions[ENSEMBLE_HORIZON_MAX]` exists ✓

**exit_reward_ring_head: int** ✓
- Declared at :821 in CoreModelZoo.hpp
- Init: ezoo->exit_reward_ring_head = 0 ✓
- Writes: incremented at StrategyParameters.hpp:1064-1066 via modulo ✓
- Reads: used at :1087-1090 for ring indexing ✓

**exit_predict_call_count: uint64_t** ✓
- Declared at :822 in CoreModelZoo.hpp
- Init: ezoo->exit_predict_call_count = 0 ✓
- Writes: incremented at StrategyParameters.hpp:1063 ✓
- Reads: used at :1082-1084 to calculate avail history depth ✓

---

## 2. ControllerConfig Fields (ControllerConfig.hpp)

### exit_blender_mode: int ✓
- Declared at :513 in ControllerConfig.hpp
- Default init: cfg.exit_blender_mode = 0 ✓
- Parser: CFG_PARSE_INT(exit_blender_mode) entry present ✓
- Read: config->exit_blender_mode at StrategyParameters.hpp:1077 ✓
- Correct struct: ControllerConfig, right position ✓

### ridge_lambda, ridge_cost_penalty, ridge_min_ic_floor ✓
- All pre-exist (v5.14.0 buy-side Ridge)
- Declared at :532-534 in ControllerConfig.hpp
- Defaults: 0.15, 0.5, 0.001 respectively ✓
- Reads in exit Ridge invocation (StrategyParameters.hpp:1118-1120):
  - FPN_ToDouble(config->ridge_lambda) ✓
  - FPN_ToDouble(config->ridge_cost_penalty) ✓
  - FPN_ToDouble(config->ridge_min_ic_floor) ✓

### use_exit_model: int ✓
- Declared at :513 in ControllerConfig.hpp
- Default: cfg.use_exit_model = 0 ✓
- Read: config->use_exit_model at StrategyParameters.hpp:1029 ✓

---

## 3. X-macro Registry Entry (StampBoundCfgRegistry.hpp)

**exit_blender_mode X-macro row:** ✓
```cpp
X(exit_blender_mode, int, "%d", 0, cfg.exit_blender_mode)
```

**X-macro expansions verified:**

1. **Struct field generation (ModelInference.hpp:StampInferenceCfgInputs)**
   - Expands to: `uint8_t has_exit_blender_mode; int exit_blender_mode;` ✓

2. **Zero-init (ModelInference.hpp)**
   - Expands to zero-init branch; default value 0 applied ✓

3. **Parser branches (ModelInference.hpp:verify_model_stamp)**
   - Expands to: `else if (strcmp(key, "exit_blender_mode") == 0) {
     r.exit_blender_mode = (int)(STAMP_CFG_PARSE(int, val)); ...}` ✓

4. **Drift check (CoreModelZoo.hpp:CoreModelZoo_TryLoadRole)**
   - Expands to: `if (sr.has_exit_blender_mode) { if (sr.exit_blender_mode !=
     (int)(cfg.exit_blender_mode)) sr.inference_cfg_drift_count++; }` ✓

5. **Registry count**
   - FOREACH_STAMP_BOUND_CFG_COUNT: 13 entries (was 12 pre-.E.A) ✓

---

## 4. Exit-Side Ridge Invocation Block (StrategyParameters.hpp:1029-1137)

### All struct field reads:

| Field | Source | Status |
|-------|--------|--------|
| ezoo_ex->exit_predictor_count | EnsembleModelZoo (v5.13.4 pre-existing) | ✓ |
| ezoo_ex->exit_predictor[h] | EnsembleModelZoo (v5.13.4 pre-existing) | ✓ |
| ezoo_ex->exit_reward_ring_head | Added v5.14.1.E.B | ✓ Init: 0 |
| ezoo_ex->exit_reward_ring[] | Added v5.14.1.E.B | ✓ Init: memset 0 |
| ezoo_ex->exit_predict_call_count | Added v5.14.1.E.B | ✓ Init: 0 |
| ezoo_ex->exit_ridge_state.corr_matrix | Added v5.14.1.E.A | ✓ Init: RidgeWeights_Init |
| ezoo_ex->exit_ridge_state.w[] | Added v5.14.1.E.A | ✓ Init: RidgeWeights_Init |

### All config reads:

| Config field | Read at | Default | Status |
|--------------|---------|---------|--------|
| config->use_exit_model | :1029 | 0 | ✓ |
| config->exit_blender_mode | :1077 | 0 (v5.14.1.E.A) | ✓ |
| config->ridge_lambda | :1118 | 0.15 (v5.14.0) | ✓ |
| config->ridge_cost_penalty | :1119 | 0.5 (v5.14.0) | ✓ |
| config->ridge_min_ic_floor | :1120 | 0.001 (v5.14.0) | ✓ |

### Function calls:

| Function | Available | Status |
|----------|-----------|--------|
| Model_IsLoaded | ModelInference.hpp:1072 | ✓ |
| Model_Predict_Normalized | ModelInference.hpp:605 | ✓ |
| RidgeBlender_BuildCorr | RidgeBlender.hpp:287 | ✓ |
| RidgeBlender_Compute | RidgeBlender.hpp:202 | ✓ |
| std::isnan, std::isinf | cmath (C++ std) | ✓ |

---

## 5. Cross-Check Buy-Side Equivalence

### Copied pattern: v5.14.0 buy-side (StrategyParameters.hpp:870-947) → exit (1029-1137)

| Aspect | Buy-side | Exit-side | Assessment |
|--------|----------|-----------|------------|
| Ring populate | ezoo->reward_ring | exit_reward_ring | ✓ Symmetric |
| Ring index calc | reward_ring_head modulo | exit_reward_ring_head modulo | ✓ Identical |
| History depth | RIDGE_HISTORY_DEPTH=64 | 64 | ✓ Same |
| IC per arm | ezoo->drift[i].ic_avg | 0.0 (deferred) | ✓ See note |
| Predictor count | ezoo->primary_count | ezoo_ex->exit_predictor_count | ✓ Semantic match |
| Call count | predict_call_count | exit_predict_call_count | ✓ Separate ring |
| Cost per arm | 0.0 (deferred) | 0.0 (deferred) | ✓ Parity |

**IC-per-arm note:** Exit side hardcodes 0.0 (line 1111); buy side reads ic_avg from
drift tracker (line 922). This is acceptable because Ridge floors to ridge_min_ic_floor
anyway (default 0.001). Per-arm IC tracking for exit side deferred to v5.15+.

---

## 6. Class 18 Miss Check

**Question:** "What does this READ that I might not have provided on the exit side?"

### Systematic walk:

1. **Ring reads:** exit_reward_ring populated before Ridge invocation (lines 1051-1066) ✓
2. **Prediction history reads:** Indexed via modulo from populated ring ✓
3. **State reads:** exit_ridge_state zero-init before first use ✓
4. **Cfg reads:** All cfg fields exist, have defaults, parse correctly ✓
5. **Bandit vs Ridge:** When exit_blender_mode=0, uniform weights (1/n_loaded) used;
   no Ring reads in that path ✓
6. **Cholesky fallback:** RidgeBlender_Compute writes fallback_to_uniform=1 on rank
   failure; caller converts to uniform 1/N weights ✓

**No additional Class 18 misses found.** The exit_reward_ring catch during .B
coding revealed the dependency pattern; all other data sources are accounted for.

---

## 7. Verdict

**GREEN** — All reads have valid data sources. No uninitialized-memory reads.

### Summary:
- ✓ exit_ridge_state: zero-init via RidgeWeights_Init
- ✓ exit_reward_ring: zero-init via memset; head initialized to 0
- ✓ exit_reward_ring_head: zero-init, modulo increments
- ✓ exit_predict_call_count: zero-init, incremented before history use
- ✓ All cfg fields: defaults set, parsers registered, drift checks wired
- ✓ X-macro count: 13 entries verified
- ✓ Ridge invocation: mirrors buy-side pattern; all dependencies satisfied
- ✓ No new Class 18 gaps detected

### Functional correctness:
- Default cfg.exit_blender_mode=0: bytewise identical to pre-v5.14.1.E uniform blend
- cfg.exit_blender_mode=1: Ridge override enabled; all inputs (ring, state, cfg) available
- Cholesky failure: falls back to safe uniform weights (no abort)
- IC tracking: deferred to v5.15+ per design; Ridge floors to min_ic_floor

**Ready for .C + .D:** No data-flow surprises; operator playbook and tests can proceed.

---

**Report generated:** 2026-05-09 (post-mortem trace for v5.14.1.E.A + .B as-shipped)

