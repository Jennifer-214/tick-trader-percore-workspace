# /latency-track Audit — v5.14.2 (a3810b6) — 2026-05-09

## Summary

**Claim:** v5.14.2 added ZERO per-cycle steady-state latency cost.

**Verdict:** ✅ **GREEN** — Claim verified and upheld.

---

## Core Claim Verification

### 1. Atomic Load + Branch Pre-existence

The commit message states: "The atomic load + branch on `swap_model_path_requested[c]` 
was already paid pre-v5.14.2 (was guarding the REFUSE block)."

**Verification result:** CONFIRMED.

HEAD~1 (commit 2d12fc3) contains at CoreFrameworks/EngineSharded.hpp lines ~2717–2720:
```cpp
uint8_t mswap = __atomic_load_n(
    &g_shared.swap_model_path_requested[c],
    __ATOMIC_ACQUIRE);
if (mswap) {
```

v5.14.2 (a3810b6) preserves this structure and adds the helper call **inside** 
the existing `if (mswap)` guard at the ensemble-specific branch 
(EngineSharded.hpp lines 2759–2786).

**Cost delta:** 0 ns per steady-state cycle (no new branch, no new atomic load).

---

### 2. What Was Replaced

**Pre-v5.14.2:** REFUSE fprintf + atomic_store_n() at `state.cores[c].ensemble_handle != nullptr` branch.

**v5.14.2:** Helper call `EngineSharded_HotSwapEnsemble(swap_ezoo, cfg, c, new_path, swap_backend)` 
inside same `if (mswap)` predicate.

**Instruction count:** Negligible delta (−1 fprintf, +1 helper function call). 
Helper executes only on operator-initiated swap requests (~50–100 ms event window), 
not every cycle.

---

## EnsembleModelZoo_Free Completeness (.D)

### Call Sites Census

**All 17 call sites:**

| Site | Context | Tier | Frequency |
|------|---------|------|-----------|
| CoreFrameworks/EnsembleHotSwap.hpp:76 | Inside hot-swap sequence | Slow-path event | Operator-initiated, ~50–100ms |
| Backtest/BacktestSharded.hpp:258 | Per-backtest-run init | Cold-path | Once per backtest |
| ML_Headers/CoreModelZoo.hpp:1773 | LoadFromCfg validation error unwinding | Cold-path (error) | Rare (config/grid mismatch) |
| tests/controller_test.cpp (14 sites) | Test cleanup teardown | Test-only | N/A |

### Classification

**NOT on per-cycle hot path:** ✅ Confirmed.
- Backtest init: cold (single occurrence per backtest session)
- Error unwinding: cold (rare, triggered by validation failure)
- Hot-swap: slow-path, rare event window (not steady-state per-cycle)
- Tests: test cleanup only (not shipped code)

---

## Latency Impact Analysis

### v5.14.2.B — EngineSharded.hpp Ensemble Hot-Swap Replacement

**Location:** CoreFrameworks/EngineSharded.hpp lines 2759–2786

| Metric | Value | Notes |
|--------|-------|-------|
| Per-cycle steady-state cost | 0 ns | Atomic load + branch pre-existed |
| Per-swap event cost | ~50–100 ms | XGBoost model load + bandit JSON parse (slow-path, rare) |
| Branchless | NO | Data-dependent `if (mswap)` predicate on slow-path (acceptable; slow-path is not sub-microsecond) |
| New memory load | None | Pre-existing swap_model_path_requested[] load |
| New atomic op | None | Pre-existing __atomic_load_n() + __atomic_store_n() |
| New function call | Yes, 1 | Helper call (EngineSharded_HotSwapEnsemble) only on swap request |

**Tier:** Slow-path, rare event handler (not per-cycle).

---

### v5.14.2.D — EnsembleModelZoo_Free Completeness

**Location:** ML_Headers/CoreModelZoo.hpp lines 1337–1344

**4 LOC added:**
```cpp
RidgeWeights_Init(&ezoo->exit_ridge_state);              // ~5 ns (cold)
memset(ezoo->exit_reward_ring, 0, sizeof(...));         // ~20 ns (cold)
ezoo->exit_reward_ring_head = 0;                        // ~0.3 ns
ezoo->exit_predict_call_count = 0;                      // ~0.3 ns
```

| Metric | Value | Notes |
|--------|-------|-------|
| Per-cycle cost | 0 ns | Free never called per-cycle |
| Cold-path cost (per-call) | ~25 ns | Only paid on process exit or error unwinding |
| Branchless | N/A | Initialization sequence (not a conditional) |
| Tier | Cold-path | Cold-path only; never on hot path |

**Rationale:** v5.14.1.E added exit_ridge_state, exit_reward_ring, head, predict_call_count 
to EnsembleModelZoo. The hot-swap path re-inits these in EnsembleHotSwap.hpp (L80), 
but Free called outside hot-swap (process exit, error recovery) must not leave stale data. 
This fix adds semantic completeness without latency burden (cold-path only).

---

## Hot Path Status Check

**ExecutionCore.hpp / GateParameters.hpp / ParameterSlot.hpp / FixedPointN.hpp / SPSCRing.hpp:**
✅ UNTOUCHED by v5.14.2.

**Producer fan_out (EngineSharded.hpp ~1476–1600):**
✅ UNTOUCHED by v5.14.2.

**Slow-path per-cycle handler (EngineSharded.hpp ~2600–2850):**
✅ Only change is within `if (mswap)` guard (swap request handling, rare).
Pre-existing atomic_load + branch preserved.

---

## Changelog Entry Requirement

Per /latency-track spec:
- New atomic operation: No (pre-existing `__atomic_load_n`)
- New branch on hot path: No (pre-existing `if (mswap)` on slow-path)
- New per-cycle cost: No (0 ns delta)
- New struct field: No (no changes to GateParameters, ParameterSlot, ExecutionCore)

**Recommendation:** No DOCS/HOT_PATH_CHANGELOG.md entry needed.

---

## Cross-Site Audit Notes

**Hot-swap helper boundary:**
- EnsembleHotSwap.hpp (new, 115 LOC) is cold-path only
- Internally calls: Free → Init → LoadFromCfg → InitBandits → InitExitBandits → LoadBanditState → LoadExitBanditState
- All cold-path (model load + bandit JSON parse dominate cost, ~50–100 ms)
- No new atomic operations or branches in the helper body affecting steady-state

**Merge-scan note:** No new computation overlap detected. Helper cleanly separates 
ensemble-specific swap from single-zoo swap, reducing conditional nesting on hot path 
(post-swap, reads ensemble_zoo directly via StrategyParameters.hpp:794 dispatcher).

---

## Final Verdict

✅ **GREEN** — Latency accountability verified.

- Pre-cycle steady-state cost: **0 ns** (atomic load + branch pre-existed, no new per-cycle work)
- EnsembleModelZoo_Free completeness: **cold-path only** (never on per-cycle path)
- Hot path: **UNTOUCHED** (no new branches, no new atomic ops, no new struct fields)
- Producer fan_out: **UNTOUCHED**
- All new work: **gated by rare operator-initiated event** (~50–100 ms swap window)

v5.14.2 cost-neutral on latency tier. Pre-v5.14.2 steady-state profile preserved.
