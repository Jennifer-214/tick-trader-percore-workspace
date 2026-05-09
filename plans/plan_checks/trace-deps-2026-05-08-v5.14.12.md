# /trace-deps report — v5.14.12 online correlation matrix updates — 2026-05-08

**Verdict:** **GREEN** — all REUSE verified; NEW claims coherent; ready to code

## Summary
- 6 REUSE components verified (RidgeBlender_BuildCorr, RidgeWeights<F>,
  EnsembleModelZoo.reward_ring, ML_BuildParameters dispatch, Welford
  pattern from RollingStats, v5.11.7 AVX-512 vectorization discipline)
- 0 GAPS / 0 DRIFT / 0 DRIFT-RISK

## REUSE verification

| Claim | Location (verified) | Status |
|---|---|---|
| `RidgeBlender_BuildCorr` (path being optimized; full recompute kept in else branch) | `ML_Headers/RidgeBlender.hpp:287-368` | PASS |
| `RidgeWeights<F>` extension target | `ML_Headers/RidgeBlender.hpp:84-103` | PASS (forward-compatible field append) |
| `EnsembleModelZoo.reward_ring` input source | `ML_Headers/CoreModelZoo.hpp:790` | PASS (unchanged) |
| ML_BuildParameters dispatch site | `Strategies/StrategyParameters.hpp:907-924` (Ridge call site) | PASS |
| Welford pattern (sister technique) | `ML_Headers/RollingStats.hpp:83-87` | PASS (production-proven via v5.11.2.C) |
| AVX-512 vectorization with bytewise-determinism | `ML_Headers/BanditLearning.hpp:118-194` (v5.11.7) | PASS (discipline cited correctly) |

## Critical validations

- ✓ Default bytewise-determinism: `ridge_online_corr=0` → unchanged full BuildCorr path
- ✓ Periodic reset every 1000 cycles → bounds numerical drift
- ✓ Welford correctness test: 1e-9 tolerance vs full recompute
- ✓ No deprecated callsites
- ✓ AVX-512 deferred to .B with explicit ordering discipline (mul-reciprocal forbidden; FMA fusion preserved)

## Verdict: **GREEN** — Phase 4 sub-ship ready to code
