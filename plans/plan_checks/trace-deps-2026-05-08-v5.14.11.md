# /trace-deps report — v5.14.11 Bayesian Thompson sampling — 2026-05-08

**Verdict:** **GREEN** — all REUSE verified; NEW claims coherent; ready to code

## Summary
- 12 REUSE components verified (BanditState struct, all Bandit_* fns,
  EnsembleModelZoo, persistence pattern from v5.10.0a.G.7 + v5.13.4)
- 0 GAPS / 0 DRIFT / 0 DRIFT-RISK

## Key findings

### 1. Mirroring pattern VALID
- `ThompsonBanditState` mirrors `BanditState` structure
- `thompson_bandits[NUM_REGIMES]` mirrors `bandits[]` + `exit_bandits[]`
- No struct field conflicts; parallel arrays safe

### 2. Initialization pipeline COHERENT
- Boot flow: `EnsembleModelZoo_Init` → `_LoadFromCfg` → `_InitBandits`
  → `_InitExitBandits` → (NEW) `_InitThompsonBandits`
- Gating via `initialized_thompson_bandits` flag (mirrors
  `initialized_exit_bandits`)
- Linear extension; no circular deps

### 3. ML_BuildParameters dispatch CONFLICT-FREE
- `switch(cfg.bandit_algorithm)` positioned BEFORE Ridge override
- Ridge override (v5.14.0.B) fires AFTER bandit dispatch
- "Ridge wins last" precedence: Thompson_Sample → weights_buf →
  Ridge override → Model_Predict
- Both v5.14.0.B Ridge AND v5.14.11 Thompson coexist

### 4. Persistence pattern PROVEN
- Follows v5.13.4.C exit_bandit model: separate JSON file
  `thompson_state.json`; forward-compat-by-absence
- `Bandit_SaveJSON` / `Bandit_LoadJSON` already used for
  bandits + exit_bandits; same shape for thompson

### 5. Determinism contract PRESERVED
- `std::mt19937_64` seeded by `cfg.thompson_rng_seed`
- `rng_state` persisted in ThompsonBanditState
- Identical seed + identical rewards → identical sample sequence
  (C++ standard guarantee)
- Replay-determinism: load thompson_state.json → restore rng_state
  → deterministic re-execution

### 6. Cfg dispatch SAFE
- All 5 cfg fields follow existing patterns
- Default `bandit_algorithm=0` → bytewise-identical pre-v5.14.11
  behavior (Exp3 path unchanged)
- No conflicts with `ridge_within_horizon` or `exit_bandit_enabled`

## Pre-coding sign-off recommendations

- Ensure `Thompson_SaveJSON` / `_LoadJSON` mirror `Bandit_SaveJSON`
  format (bundle-id, format_version, per-regime iteration)
- Validate Box-Muller Gaussian draws (or std::normal_distribution)
  match determinism intent
- Set sensible cfg defaults: `bandit_algorithm=0`, `mu_prior=0.0`,
  `precision_prior=1.0`, `rng_seed=42`
- Add parity test: `cfg.bandit_algorithm=0` produces bytewise-
  identical weights to pre-v5.14.11

## Verdict: **GREEN** — ready to code (Phase 4 sub-ship)
