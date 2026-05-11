# /trace-deps report — v5.14.11 online-corr-update — 2026-05-11

Plan: `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.11-online-corr-update.md`
HEAD: e0cc877 (v5.14.10 umbrella shipped)

## Summary

- NEW functions analyzed: 2 (`RidgeBlender_UpdateOnline`, `RidgeBlender_FinalizeCorr`)
- NEW struct: 1 (`RidgeOnlineState<F>`)
- NEW cfg field: 1 (`cfg.ridge_online_corr`)
- Callees / file:line claims verified: 18
- **PASS: 17**
- **GAP: 0** (no broken claims)
- **DRIFT: 1** (Step 3 snippet leaks v5.14.10-pre prose: writes only to BUY-side dispatch, doesn't show exit-side mirror — see DRIFT-1)
- **DRIFT-RISK: 0** (no deprecated-path callees)

## Verdict: **GREEN with one mirror-coverage flag**

Plan is structurally sound. The amendment from prior pass (line ref 270→287, Welford citation, TWO sites flagged) addressed all mechanical drift. One remaining sub-gap is mirror-coverage in the implementation snippet (Step 3 shows one site only) — does NOT block ship-start since the REUSE block already calls out both sites + says "address both (or explicitly defer exit-side)".

---

## Per-claim verification table

| Claim (plan line) | Reality (HEAD) | Verdict |
|---|---|---|
| `RidgeBlender_BuildCorr<F>` at `RidgeBlender.hpp:287` | Confirmed at 287; sig `(corr_out[MAX][MAX], predictions_history, n_history, n_models)` | **PASS** |
| `RidgeBlender_Compute<F>` at `:202` (sig: `out, ic[], cost[], n_models, ridge_lambda, cost_penalty, min_ic_floor`) | Confirmed at 202; sig exactly matches | **PASS** |
| `RidgeWeights<F>` struct at `:85`; fields w[8], corr_matrix[8][8], mu[8], L[8][8], y[8], w_internal[8], n_models, fallback_to_uniform, last_compute_us | All 9 fields present at 85-103 | **PASS** |
| BuildCorr call site 1 (buy-side, ridge_within_horizon gate) at `StrategyParameters.hpp:996` | Confirmed at 996 (inside the gated block at 962-1014) | **PASS** |
| BuildCorr call site 2 (exit-side, exit_blender_mode gate) at `:1195` | Confirmed at 1195 (inside gated block at 1162-1217) | **PASS** |
| Thompson mutex check `config->bandit_algorithm == 0` for Ridge override at `:972-974` | Confirmed at 972-974; reads exactly `_ridge_gate && config->bandit_algorithm == 0 && ezoo->primary_count >= 2` | **PASS** |
| `MAX_RIDGE_MODELS=8` at `RidgeBlender.hpp:66` | Confirmed at 66 (`static constexpr int = 8`) | **PASS** |
| `REWARD_RING_SIZE=256` at `CoreModelZoo.hpp:893` | Confirmed at 893 (`static constexpr int = 256`) | **PASS** |
| `RIDGE_HISTORY_DEPTH=64` local constexpr at `StrategyParameters.hpp:979` + `:1178` | Confirmed at 979 AND 1178; both `constexpr int = 64` | **PASS** |
| `PredictionRecord` shape at `CoreModelZoo.hpp:894-901` with `predictions[ENSEMBLE_HORIZON_MAX]` | Confirmed at 894-901; `predictions[ENSEMBLE_HORIZON_MAX]` at 897; ENSEMBLE_HORIZON_MAX=8 (815) | **PASS** |
| `reward_ring[REWARD_RING_SIZE]` field at `:902` | Confirmed at 902 | **PASS** |
| `exit_reward_ring[REWARD_RING_SIZE]` field at `:909` | Confirmed at 909 (parallel buy-side ring; eligibility for exit-side mirror) | **PASS** |
| 9 SlowPathGate entries (LADDER, CONFIDENCE, COMPOSITE, RIDGE_WITHIN, EXIT_BLENDER, THOMPSON, BANDIT_BOTH, LAZY_REBUILD, WS_FLATTEN) at `SlowPathGateRegistry.hpp:69-107` | All 9 confirmed at exactly those line nrs; 7 PER_CORE + 2 ENGINE_WIDE | **PASS** |
| Headroom: `static_assert(GATE_SLOW_PATH_TOTAL_COUNT <= 16)` at `:160-161`; current 9 → 7 free | Confirmed at 160-161; uint16_t bitmap state | **PASS** |
| `cfg.ridge_online_corr` does NOT exist yet | Confirmed: rg empty in engine repo source; only the plan + handoff mention it | **PASS** (truly NEW) |
| `RidgeOnlineState`, `RidgeBlender_UpdateOnline`, `RidgeBlender_FinalizeCorr` do NOT exist yet | Confirmed: rg empty in engine source | **PASS** (truly NEW) |
| v5.11.7 AVX-512 pattern at `BanditLearning.hpp:139-162` (REUSE for vectorization template) | Confirmed: `#if defined(__AVX512F__)` block at 138, fmadd/div/max pattern lines 153-161; bytewise-determinism comments match plan citation | **PASS** |
| Welford citation: "RollingStats.hpp:83-87 uses running-sums (not Welford)" | Confirmed at 83-87: `price_sum_running`, `price_sum_y2_running`, `price_sum_xy_running`, `volume_sum_running`, `vol_sum_xy_running` — naive running-sums, not Welford. Plan distinction is correct. | **PASS** |

---

## DRIFT-1 — Step 3 wiring snippet only shows BUY-side dispatch

**Claim (Step 3, plan lines 137-158):** Pseudocode shows `if (config->ridge_online_corr) { ... RidgeBlender_UpdateOnline ... } else { RidgeBlender_BuildCorr<F>(...) }` — singular, referencing `ezoo->reward_ring[latest_idx]` only.

**Reality:** Plan's REUSE block (lines 14-19) correctly states "Called from TWO sites" + "design must address both sites (or explicitly defer exit-side)". The current code at StrategyParameters.hpp:1190-1197 shows the exit-side mirror reads `ezoo_ex->exit_reward_ring[...]` (NOT `reward_ring`) — so a literal copy of the Step 3 snippet won't work for the exit site without parameter substitution (`ezoo_ex` instead of `ezoo`, `exit_reward_ring` instead of `reward_ring`, `exit_ridge_state` instead of `ridge_state`, `exit_predictor_count` instead of `primary_count`, `exit_predict_call_count` instead of `predict_call_count`).

**Recommended fix:** add a 1-sentence note to Step 3 stating: "Exit-side mirror in .C (sub-tag .C wiring step) does parallel substitution; same logical shape, swap `ezoo`→`ezoo_ex`, `reward_ring`→`exit_reward_ring`, `ridge_state`→`exit_ridge_state`, `primary_count`→`exit_predictor_count`, `predict_call_count`→`exit_predict_call_count`. Each ezoo / ezoo_ex needs its OWN RidgeOnlineState instance (extend EnsembleModelZoo with `ridge_online_state` + `exit_ridge_online_state` parallel fields)." This is a 5-line plan-edit (no code edit) that makes the .C sub-tag mechanically actionable from cold-pickup.

Optional secondary fix: rename the field plan-prose calls "ezoo->ridge_online_state" (line 140, 144) to "ezoo->ridge_online_state" + add a parallel "ezoo_ex->exit_ridge_online_state" callout in the same paragraph.

**Class-18 check (CLAUDE.md item 19):** the two BuildCorr call sites are a Class-18 mirror surface. The plan's REUSE block IS aware of this; it explicitly notes "Mirrors v5.14.0 buy-side ridge_within_horizon block" at code-comment line 1165 (visible in HEAD). Plan calls out "address both sites (or explicitly defer)" — operator decision-point preserved. No GAP, just under-specified pseudocode.

---

## Mirror data-flow audit (per skill spec Step 6)

**Source range mirrored:** plan's Step 3 wiring snippet (137-158) targets BUY site at StrategyParameters.hpp:962-1014. Exit-side mirror surface = 1162-1217.

**Data sources walked at BUY site (StrategyParameters.hpp:962-1014):**

| Read (`obj.field` or `obj->field`) | Y-side equivalent (exit at 1162-1217) | Verdict |
|---|---|---|
| `ezoo->reward_ring` | `ezoo_ex->exit_reward_ring` (CoreModelZoo.hpp:909) | **PASS** |
| `ezoo->reward_ring_head` | `ezoo_ex->exit_reward_ring_head` | **PASS** (exists in zoo) |
| `ezoo->predict_call_count` | `ezoo_ex->exit_predict_call_count` (StrategyParameters.hpp:1182) | **PASS** |
| `ezoo->primary_count` | `ezoo_ex->exit_predictor_count` (used at 1190, 1197, 1204) | **PASS** |
| `ezoo->ridge_state.corr_matrix` | `ezoo_ex->exit_ridge_state.corr_matrix` (1196) | **PASS** |
| `ezoo->drift[i].ic_avg` (1004) | exit side: hardcoded `ic_per_arm[i] = 0.0` at 1209 (comments cite future v5.13.4-style `ic_avg_exit[]`) | **DOCUMENTED-RISK** — plan + code acknowledge exit-side IC tracking deferred to "v5.15+ live cost-aware tracking lands"; current behavior is functionally identical (Ridge floors to `ridge_min_ic_floor`). Plan inherits the same gap; no new risk. |
| NEW `ezoo->ridge_online_state` (the new struct) | Plan must ADD parallel `ezoo_ex->exit_ridge_online_state` field; otherwise .C exit-side wiring has no Y-side state object | **NEEDS-ADD** (data-flow gap — flagged at DRIFT-1) |

**Call-sequence audit (per skill spec Step 6 strengthening):**

| Function called at BUY site | Mirror call at exit site | Verdict |
|---|---|---|
| `RidgeBlender_BuildCorr<F>(corr_matrix, history, avail, n_arms)` | Same fn at 1195-1197 | **MIRROR-PRESENT** |
| `RidgeBlender_Compute<F>(...)` | Same fn at 1213 | **MIRROR-PRESENT** |
| NEW `RidgeBlender_UpdateOnline<F>(...)` | Plan needs to invoke at exit site too | **MIRROR-MISSING-NEEDS-PLAN-NOTE** (DRIFT-1) |
| NEW `RidgeBlender_FinalizeCorr<F>(...)` | Plan needs to invoke at exit site too | **MIRROR-MISSING-NEEDS-PLAN-NOTE** (DRIFT-1) |

**Class-18 recurrence check:** the 2 NEW functions need to invoke in a 2-site mirror. This is the exact pattern that produced PARITY-009/010/011/012 (9 sub-gaps closed by v5.14.2.E.1 via PostLoadSetup registries). Mitigation options:

1. **Direct mirror (current plan implicit)** — add the same conditional block in BOTH BuildCorr call sites. Risk: future cfg drift could miss one site (Class-18 textbook).
2. **Helper extraction (CLAUDE.md item 19 preferred)** — extract the "build-or-update correlation matrix" decision into a `RidgeBlender_BuildOrUpdate<F>(state, online_state, predictions_history, n_history, n_models, online_enabled, cycles_since_recompute)` wrapper. Both call sites invoke the same helper; conditional logic lives ONE place. Adding the next cfg toggle (e.g., sliding-window variant) becomes 1-site.

Plan currently implies option 1 (snippet shows the if/else inline). Recommend operator/agent decide between (1) and (2) before code time. Helper extraction is well-aligned with CLAUDE.md item 19 (Class-18 prevention) and the workspace policy "structural fix preferred when bug class can recur".

---

## Recommendations (non-blocking)

1. **Plan edit** (5 lines): add exit-side substitution note to Step 3 (DRIFT-1).
2. **Plan edit** (2 lines): in TRULY NEW section, list parallel `ezoo_ex->exit_ridge_online_state` field (data-flow gap from Mirror audit).
3. **Decision-point at code time:** direct mirror vs helper extraction. CLAUDE.md item 19 (structural fix preferred) suggests option 2; operator's call.
4. **Sub-tag .C deliverable** should include both BUY-side and exit-side wiring; .B AVX-512 vectorization applies equally to both sites; .A scalar correctness tests can be BUY-only initially as long as .C re-runs the equivalence test against the exit-side history shape (8×64 max, same dimensions).

---

## Cross-references

- `/readiness` Check 24 (mirror-function audit): would flag DRIFT-1 if not yet acted on.
- `/readiness` Check 25 (TECH_DEBT scan): no overlapping items at HEAD (TECH_DEBT.md does not have a Ridge online-corr entry; truly new sprint).
- CLAUDE.md item 19 (structural fix preferred for Class-18) + DESIGN_SPECS/`structural-fix-preferred-decision-framework.md` (workspace).
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 18 — applies to this ship if direct-mirror path is chosen over helper extraction.

Verdict: **GREEN** — plan ready to ship-start. DRIFT-1 is a clarifying note, not a blocking gap.
