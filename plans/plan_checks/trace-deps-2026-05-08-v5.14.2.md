# /trace-deps report — v5.14.2 hot-swap ensemble — 2026-05-08

**Verdict:** **GREEN** — all 7 reused fns verified; helper composition sound; no signature drift

## Summary
- 7 existing functions verified at claimed (or near-claimed; ±20 lines) locations
- 1 new helper (`EngineSharded_HotSwapEnsemble`) — composition validated
- 1 cfg flag reused (`acknowledge_hot_swap_with_open_positions` v5.10.0c)
- 1 existing REFUSE site identified for replacement
- 0 GAPS / 0 DRIFT / 0 DRIFT-RISK

## REUSE verification (all PASS)

| Claim | Plan said | Actual | Status |
|---|---|---|---|
| EnsembleModelZoo_Free | CoreModelZoo.hpp:1222 | :1243 | PASS (±20 lines) |
| EnsembleModelZoo_Init | CoreModelZoo.hpp:807 | :823 | PASS |
| EnsembleModelZoo_LoadFromCfg | CoreModelZoo.hpp:1248 | :1269 (covers exit_predictor; calls TryLoadRole at :1531) | PASS |
| EnsembleModelZoo_InitBandits | post-LoadFromCfg | :1124 | PASS |
| EnsembleModelZoo_InitExitBandits | v5.13.4 | :1172 | PASS |
| EnsembleModelZoo_LoadBanditState | v5.10.0a.G.9 | :1789 | PASS |
| EnsembleModelZoo_LoadExitBanditState | v5.13.4.C | :1820 | PASS |
| `acknowledge_hot_swap_with_open_positions` cfg | ControllerConfig.hpp:647 | :661 | PASS |
| Existing REFUSE site | EngineSharded.hpp:2745-2756 | :2745-2756 (exact match; message even mentions "v5.14.2 candidate") | PASS |

## NEW helper coherence

`EngineSharded_HotSwapEnsemble` composition (7-step pipeline):
- Step 1: `Free` ✓
- Step 2: `Init` ✓
- Step 3: `LoadFromCfg` ✓ (with `held_out_gate_strict` + `acknowledge_cross_binary_version_drift`)
- Step 4: `InitBandits` ✓ (with `ensemble_bandit_eta` + `ensemble_min_warmup_predictions`)
- Step 5: `InitExitBandits` ✓ (with `exit_bandit_lr` + same warmup)
- Step 6: `LoadBanditState` ✓
- Step 7: `LoadExitBanditState` ✓

All cfg field accesses verified to exist in ControllerConfig.hpp.

## Atomicity contract

Plan correctly notes (line 73-75): same-thread (slow-path c is
single-reader/writer for its zoo); brief empty-zoo window is safe.
ML inference runs on same thread, cannot preempt itself. No race.

## Verdict: **GREEN** — ready to code Phase 1 sub-ship
