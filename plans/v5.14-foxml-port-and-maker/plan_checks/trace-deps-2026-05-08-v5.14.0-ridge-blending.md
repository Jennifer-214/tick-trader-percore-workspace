# /trace-deps report — v5.14.0-ridge-blending — 2026-05-08

**Verdict:** **GREEN** (all callees verified; ready to code)

## Summary
- NEW functions analyzed: 3 (RidgeBlender_Compute, BuildCorr, Cholesky_Solve)
- Callees verified: 9 unique fns + 7 struct fields
- PASS: 9
- GAP: 0 / DRIFT: 0 / DRIFT-RISK: 0

## REUSE verification (all PASS)

| Claim | Location | Status |
|---|---|---|
| `EnsembleModelZoo.bandits[NUM_REGIMES]` | CoreModelZoo.hpp:737 | PASS |
| `primary_handles` / `primary_count` | CoreModelZoo.hpp:800-801 | PASS |
| `reward_ring[256]` PredictionRecord | CoreModelZoo.hpp:766-774 | PASS |
| `Bandit_GetProbabilities` | BanditLearning.hpp:118 | PASS |
| `Model_Predict_Ensemble_Weighted` | ModelInference.hpp:883-904 | PASS (signature matches plan exactly) |
| `ML_BuildParameters` ensemble dispatch | StrategyParameters.hpp:626 + 843-877 | PASS |
| `FPN_Sqrt` | FixedPointN.hpp:813 (template) + :1194 (F=64 spec) | PASS (12-NR-iter; bytewise-deterministic) |
| `EnsembleModelZoo_Init` | CoreModelZoo.hpp:807-852 | PASS (uses memset pattern; ridge_state add is 1-line) |
| `PredictionRecord.predictions[ENSEMBLE_HORIZON_MAX]` | CoreModelZoo.hpp:769 | PASS |

## Deprecated-path audit
- No `PortfolioController` (legacy) usage — PASS
- No `SingleCoreEngine` (legacy) usage — PASS
- All paths target sharded engine (post-v5.0) — PASS

## Recommendations

- No blocking issues. Plan ready to code.
- Verification at code-write time:
  1. Add `memset(&ezoo->ridge_state, 0, sizeof(ezoo->ridge_state))` in `EnsembleModelZoo_Init`
  2. Cfg parser entries for 5 new fields
  3. Tests per plan's verification gate (Cholesky correctness vs numpy reference; singular fallback; 2-arm closed-form; 8-arm sum-to-1)

**Sprint ready: v5.14.0 = GREEN, proceed to coding.**
