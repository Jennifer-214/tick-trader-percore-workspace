# /merge-scan audit — v5.14.2 (Hot-Swap Ensemble)

**Commit:** `a3810b6`
**Date:** 2026-05-09
**Auditor:** Manual /merge-scan walk per Layer 2 execution model

---

## Verdict: GREEN (with 2 non-actionable YELLOWs)

- ✅ No hidden duplication; design choice (discovery vs. deterministic swap) is sound.
- ✅ No high-impact reuse opportunities beyond trivial constant-folding.
- ✅ Free completeness is safe; no regression risk.
- ✅ Downstream (v5.14.3, v5.14.4) are orthogonal; no merge candidates.

**Recommendation:** v5.14.2 is ready to merge. No factoring, no refactoring, no integration blockers detected.

---

## Q1 — Duplication check (YELLOW; defensible)

The full Free→Init→LoadFromCfg→InitBandits→InitExitBandits→LoadBanditState→LoadExitBanditState
sequence does NOT exist elsewhere. However, the underlying sub-sequence
Init→(LoadFromCfg OR AutoDetectFromDir)→InitBandits→InitExitBandits→LoadBanditState→LoadExitBanditState
IS called at engine boot via `EnsembleModelZoo_AutoDetectFromDir()` (`EngineSharded.hpp:1157`).

**Boot path:** Calls `AutoDetectFromDir()` which internally:
- Discovers horizon directories via filesystem scan
- Constructs `discovered_horizons[]` array
- Calls `EnsembleModelZoo_LoadFromCfg(discovered_horizons, n_discovered, ...)`
- Runs `EnsembleZoo_VerifyGridMemberConsistency()` validator
- Calls InitBandits, InitExitBandits, LoadBanditState, LoadExitBanditState

**Hot-swap path (v5.14.2):** Directly calls `EnsembleModelZoo_LoadFromCfg()` with
**pre-cached horizons** and **no discovery step**.

**Why v5.14.2 did NOT duplicate:**
The hot-swap path correctly rejects auto-discovery (filesystem rescan is
expensive + risky mid-swap) and instead caches `horizon_ticks_at_idx[]`
BEFORE Free (`EnsembleHotSwap.hpp:61-67`). Deliberate, defensible design
choice: boot-time discovery can afford O(n) filesystem traversal;
hot-swap must be fast + deterministic.

**Future opportunity:** Free→Init prefix in hot-swap could be factored
into `EnsembleModelZoo_Reset()` helper IF error-recovery code emerges.
Not actionable today.

---

## Q2 — Reuse opportunities (YELLOW; minor sharing possible)

| Surface | Boot | Hot-swap | Assessment |
|---|---|---|---|
| horizon_list construction | filesystem discovery | cached pre-Free | Different sources; can't unify |
| InitBandits parameterization | `cfg.ensemble_bandit_eta`, `min_warmup` | identical | Already shared |
| Log message format | "[sharded] core %d ensemble active..." | "[hot_swap] ensemble core %d swapped..." | Different ops context |
| Backend resolution | `cfg.ml_backend ? ... : MODEL_BACKEND_XGBOOST` | identical | Trivial macro candidate |

No high-impact reuse gaps. Both paths share the same underlying
primitives (LoadFromCfg, InitBandits, etc.); composition differences
reflect different operational modes.

---

## Q3 — Regression risk: Free completeness (.D) (GREEN)

**The change:** v5.14.2.D added 4 LOC to `EnsembleModelZoo_Free()`
(`CoreModelZoo.hpp:1341-1344`):
```cpp
RidgeWeights_Init(&ezoo->exit_ridge_state);
memset(ezoo->exit_reward_ring, 0, sizeof(ezoo->exit_reward_ring));
ezoo->exit_reward_ring_head = 0;
ezoo->exit_predict_call_count = 0;
```

**Call sites of `EnsembleModelZoo_Free()` (production):**
1. `EnsembleHotSwap.hpp:76` (NEW v5.14.2): hot-swap path; followed
   immediately by `EnsembleModelZoo_Init()` which also zero-inits
   these fields. Double-init idempotent.
2. `CoreModelZoo.hpp:1773` (error unwind in AutoDetectFromDir grid
   verify failure): no subsequent caller accesses `exit_ridge_state`
   etc. post-failure. Safe.
3. Process exit (hypothetical): no further reads.

**No regression.** All three contexts compatible with clearing.

---

## Q4 — Downstream plan ripples (GREEN)

| Plan | Modifies | Touches v5.14.2 surfaces? |
|---|---|---|
| v5.14.3 (3-layer fingerprint) | `FeatureRegistry.hpp`, stamp body, loader | NO |
| v5.14.4 (3-mode reconcile) | `Reconcile.hpp`, `OrderManager`, `ControllerConfig` | NO |
| v5.14.5+ | TBD | TBD; unlikely to overlap |

v5.14.3 and v5.14.4 are **orthogonal branches** relative to v5.14.2.
Each ships independently without entanglement.

**Future horizon risk:** If v5.14.5+ adds new ensemble modes (e.g.,
multi-symbol rank aggregation in v5.16+), they will inherit the same
Free→Init→LoadFromCfg semantics. No breakage expected given v5.14.2's
clean abstraction in EnsembleHotSwap.hpp.

---

*Report generated 2026-05-09 | merge-scan audit*
