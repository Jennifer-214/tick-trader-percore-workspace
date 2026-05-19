# /trace-deps report — v5.14.10 Bayesian Thompson sampling bandit — 2026-05-10

**Plan:** `/home/caramel/code/FoxML_Trader_v2/plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.10-bayesian-thompson-bandit.md`
**Plan heading:** `v5.14.11` (STALE — operator renamed sprint to v5.14.10; flagged by orchestrator as Task #5)
**Branch verified:** `feat/v5.14-foxml-port-and-maker` (HEAD)
**Skill spec:** `.claude/skills/trace-deps/SKILL.md` (with v5.14.2.E.1 Step-6 strengthening — call-sequence enumeration applied)

---

## Verdict: YELLOW

- **GAP (BLOCKING):** 0
- **DRIFT (review; non-blocking):** 4 stale file:line refs + 1 wrong header name
- **PASS:** 14 (all callees exist, all signatures compatible, no cfg-field collision)
- **DRIFT-RISK (deprecated path):** 0
- **STRUCTURAL RECOMMENDATION:** convert dual-array to curve-registry pattern (NOT a blocker)

Plan is technically implementable as written; line-ref + header-name corrections required for cold-pickup readability. Structural recommendation deserves explicit defer-now / retrofit-later decision before coding starts.

---

## Per-claim verification

### Claim 1 — `BanditState` struct + `Bandit_Init` + `Bandit_Update` + `Bandit_GetProbabilities` exist at `ML_Headers/BanditLearning.hpp`

**VERIFIED:**
- `struct BanditState` at `ML_Headers/BanditLearning.hpp:65`
- `static inline void Bandit_Init(BanditState *b, int n_arms, double gamma, double eta_max, double blend_ratio, int min_samples, int ramp_up)` at `:82`
- `static inline void Bandit_Update(BanditState *b, int arm, double reward_bps)` at `:222`
- `static inline void Bandit_GetProbabilities(const BanditState *b, double *probs_out)` at `:118`
- `BANDIT_MAX_ARMS=8` at `:60`

PASS — handoff line refs match exactly.

### Claim 2 — `EnsembleModelZoo.bandits[NUM_REGIMES]` + `exit_bandits[NUM_REGIMES]`

**VERIFIED with FILE-NAME DRIFT:**
- `struct EnsembleModelZoo` at `ML_Headers/CoreModelZoo.hpp:817` (NOT `EnsembleModelZoo.hpp` as plan implies — that file does NOT exist)
- `BanditState bandits[NUM_REGIMES]` at `:833`
- `BanditState exit_bandits[NUM_REGIMES]` at `:845`
- `int initialized_bandits` and `int initialized_exit_bandits` flags present (gated by `EnsembleModelZoo_IsReadyForInference` registry contract)
- `int primary_count` at `:925` (used as bandit n_arms — NOT `buy_signal_count`)
- `int exit_predictor_count` (used as exit-bandit n_arms)

PASS for the type + fields; DRIFT for the implied header path (plan never explicitly says `EnsembleModelZoo.hpp` but the wording "parallel array to existing `bandits[]`" without naming the file invites confusion). **Recommendation:** plan should explicitly cite `ML_Headers/CoreModelZoo.hpp:833` for the existing field placement when adding `thompson_bandits[NUM_REGIMES]`.

### Claim 3 — `EnsembleModelZoo_InitBandits` + `_InitExitBandits` boot wiring

**VERIFIED:**
- `inline void EnsembleModelZoo_InitBandits(EnsembleModelZoo<F>* ezoo, double eta, int min_warmup)` at `ML_Headers/CoreModelZoo.hpp:1238`
- `inline void EnsembleModelZoo_InitExitBandits(EnsembleModelZoo<F>* ezoo, double exit_eta, int min_warmup)` at `:1286`
- Both consume `cfg.ensemble_bandit_eta` (`:1086`) + `cfg.ensemble_min_warmup_predictions` + `cfg.exit_bandit_lr` (`:1096`)

PASS.

### Claim 4 — `Bandit_SaveJSON` + `Bandit_LoadJSON`

**VERIFIED with line-ref correction:**
- `static inline int Bandit_SaveJSON(const BanditState* bandits, int n_regimes, const char* path, const char* model_bundle_sha256_hex, const char* const* regime_names)` at `ML_Headers/BanditLearning.hpp:369` ✓ (handoff said `:369` — correct)
- `static inline int Bandit_LoadJSON(BanditState* bandits, int n_regimes, const char* path, const char* expected_model_bundle_sha256_hex, int expected_n_arms)` at `:503` ✓ (handoff said `:503` — correct)

PASS. Plan can directly reuse these (Thompson save/load wraps the same per-regime array shape); see Recommendation #1 for why a parallel `Thompson_SaveJSON` / `LoadJSON` is appropriate vs reusing `Bandit_*JSON` directly.

### Claim 5 — `EnsembleModelZoo_SaveBanditState` + `_LoadBanditState` + Save/LoadExitBanditState

**VERIFIED:**
- `EnsembleModelZoo_SaveBanditState` at `ML_Headers/CoreModelZoo.hpp:1865`
- `EnsembleModelZoo_SaveExitBanditState` at `:1887` (v5.13.4.C; sister; "forward-compat by absence")
- `EnsembleModelZoo_LoadBanditState` at `:1911`
- `EnsembleModelZoo_LoadExitBanditState` at `:1942`
- `EnsembleModelZoo_LoadBanditStateFromPath` at `:1977` (operator-explicit override; backtest-only)

PASS. Plan's proposed `_SaveThompsonState` / `_LoadThompsonState` mirrors this shape exactly.

### Claim 6 — ML_BuildParameters dispatch at `Strategies/StrategyParameters.hpp:~835`

**STALE LINE REF — DRIFT:**
- Plan says `:~835`
- Actual: `inline void ML_BuildParameters(...)` at `Strategies/StrategyParameters.hpp:658`
- Bandit dispatch block at `:887-1009` (use_weighted branch + regime hysteresis blend + Ridge override + Model_Predict_Ensemble_Weighted call)
- Specifically:
  - `if (use_weighted && ezoo->initialized_bandits)` at `:887`
  - `Bandit_GetProbabilities(&ezoo->bandits[regime_id], weights_buf)` at `:912` (current-regime path) and `:899-900` (hysteresis blend path)
  - Ridge override block (`_ridge_gate`) at `:930-989` — this is the v5.14.0.B sister pattern the plan calls out
  - `pred_raw = Model_Predict_Ensemble_Weighted(...)` at `:1002` — consumes `weights_buf`

Plan's proposed switch statement on `config->bandit_algorithm` slots in cleanly between line 887 and the Ridge override at 930 — but plan code snippet (around plan line 129) doesn't show the regime hysteresis branch (lines 896-913) or the Ridge override branch (lines 930-989). Two-tier integration is needed:

1. Wrap the existing Bandit_GetProbabilities calls (lines 899/900/912) under `case 0`
2. Add `case 1` (Thompson_Sample → one-hot) and `case 2` (both run; Thompson logged as telemetry)
3. The hysteresis blend special case at lines 896-913 only applies when `bandit_algorithm=0` (Exp3 has weights; Thompson outputs an arm pick — no "blend old + new" semantics for one-hot weights). Plan must either explicitly skip hysteresis for Thompson OR define what hysteresis means when switching arms.

**Recommendation:** plan Step 3 code snippet is a SIMPLIFICATION; actual integration touches more sites. Plan should be amended to show the ACTUAL line range that gets the switch wrapper + decide hysteresis behavior under Thompson.

### Claim 7 — Cfg fields — `bandit_algorithm` / `thompson_mu_prior` / `thompson_precision_prior` / `thompson_precision_obs` / `thompson_rng_seed`

**VERIFIED — NO COLLISIONS:**
- `bandit_algorithm` does NOT exist in `CoreFrameworks/ControllerConfig.hpp` (grep clean)
- `thompson_*` does NOT exist anywhere in the codebase (grep clean)
- Sister patterns confirmed:
  - `int ridge_within_horizon` at `:664` (Ridge sister; cfg-flag for v5.14.0.B override)
  - `int ensemble_bandit_save_interval` at `:1135`
  - `double ensemble_bandit_eta` at `:1086`
  - `double exit_bandit_lr` at `:1096`

**DESIGN NOTE — bandit_algorithm should follow newer ml_cfg_flags pattern:** v5.14.9.F.2 migrated boolean cfg flags to bit-packed `uint16_t ml_cfg_flags` at `:448`. `bandit_algorithm` is an enum (3 values: Exp3 / Thompson / Both) so it does NOT fit `BIT_FLAG` storage class — it stays a separate `int`. But the plan should consider:
- If plan grows to ≥3 algorithms (UCB1, Bayesian linear, etc.) → curve-registry-pattern (see Recommendation #1)
- Cfg field should be stamp-bound via `FOREACH_STAMP_BOUND_CFG` (algorithm choice IS train/serve drift; Thompson trained → Exp3 served means different posterior)

PASS for collision-free; DESIGN-NOTE for stamp binding (plan currently says "Surface G discipline: N/A — no stamp body" which is INCORRECT — `bandit_algorithm` is a stamp-bound cfg field per `FOREACH_STAMP_BOUND_CFG`).

### Claim 8 — Thompson fn signatures match BanditLearning.hpp patterns

**VERIFIED MATCH:**

Plan proposes:
- `Thompson_Init(ThompsonBanditState* tb, ...)`  vs `Bandit_Init(BanditState* b, int n_arms, double gamma, double eta_max, double blend_ratio, int min_samples, int ramp_up)`
- `Thompson_Update(ThompsonBanditState* tb, int arm, double reward)`  vs `Bandit_Update(BanditState* b, int arm, double reward_bps)`
- `Thompson_Sample(ThompsonBanditState* tb)` returns int (argmax)  — NEW shape (Bandit_Select returns int but takes uniform_rand parameter at `:201`)
- `Thompson_GetProbabilities(ThompsonBanditState* tb, double* probs_out)`  vs `Bandit_GetProbabilities(const BanditState* b, double* probs_out)`

PASS — signatures mirror BanditLearning.hpp shape (state-pointer first, single primitive args, output pointer last). One spec gap: plan does not show `Thompson_Init`'s arg list explicitly — should mirror `Bandit_Init` discipline (init-time hyperparams via args, not via cfg pointer; cfg-to-prior translation at caller).

PASS pending Thompson_Init signature spelled out in Step 1 code block.

---

## Stale line refs to update

| Plan reference | Actual location | Fix |
|---|---|---|
| `Strategies/StrategyParameters.hpp:~835` (line 90 in plan, REUSE claims) | `:658` (fn signature) + `:887-1009` (dispatch block) | Replace with `:658 (fn) + :887-1009 (dispatch block)` |
| Implied `EnsembleModelZoo.hpp` (plan never says it explicitly but the prose "alongside Exp3" implies a separate ensemble file) | `ML_Headers/CoreModelZoo.hpp:833` | Add explicit `ML_Headers/CoreModelZoo.hpp:833` cite for `bandits[]` placement when extending with `thompson_bandits[]` |
| Plan Step 3 code snippet (`switch (config->bandit_algorithm)` block) doesn't show regime hysteresis (`:896-913`) or Ridge override (`:930-989`) interaction | Real dispatch at `:887-1009` includes both | Plan Step 3 must show how Thompson interacts with hysteresis (is hysteresis skipped under Thompson, since one-hot weights have no "blend OLD + NEW"?) |
| Plan `Step 2 — EnsembleModelZoo extension` shows `int initialized_thompson_bandits` field but does not extend `EnsembleModelZoo_IsReadyForInference` predicate at `ML_Headers/CoreModelZoo.hpp:2137-2151` | The IsReadyForInference function asserts `initialized_bandits` and `initialized_exit_bandits` flags | Plan must extend `IsReadyForInference` to include `initialized_thompson_bandits` (otherwise the ready-check stays honest only for Exp3) |

---

## Sequencing concerns (Step 6 — call-sequence enumeration; v5.14.2.E.1 strengthening)

**Plan claim:** "Init: zero in `EnsembleModelZoo_Init` (memset); full init via new `EnsembleModelZoo_InitThompsonBandits` after _LoadFromCfg."

**Actual init sequence (verified at all 3 callers):**

```
ALL 3 callers (boot=EngineSharded.hpp:1206, backtest=BacktestSharded.hpp:345, hot-swap=EnsembleHotSwap.hpp:109)
flow through ONE shared helper:

EnsembleModelZoo_PostLoadSetup<F>(ezoo, cfg, core_id, base_dir)
  → expands FOREACH_ENSEMBLE_POST_LOAD (CoreModelZoo.hpp:2088-2104):
      1. init_bandits        — EnsembleModelZoo_InitBandits(eta, min_warmup)
      2. init_exit_bandits   — EnsembleModelZoo_InitExitBandits(exit_eta, min_warmup)
      3. blend_mode          — ensemble_post_load_apply_blend_mode()
      4. disabled_horizons   — EnsembleModelZoo_SetDisabledHorizons()
      5. load_bandit_state   — EnsembleModelZoo_LoadBanditState(base_dir)
      6. save_interval       — EnsembleModelZoo_SetBanditSaveInterval()
      7. load_exit_bandit    — EnsembleModelZoo_LoadExitBanditState(base_dir)
```

This X-macro registry is the v5.14.2.E.1 PARITY-009/010/011/012 structural fix (Class 18 mirror extinguished). 7 entries; `FOREACH_ENSEMBLE_POST_LOAD_COUNT=7` at `:2107`.

**Plan's `EnsembleModelZoo_InitThompsonBandits` call MUST be added as registry entry, not as a separate call at one site.** If plan adds it only at boot, backtest + hot-swap will silently miss it — same Class 18 mirror gap that v5.14.2.E.1 just closed. This is the canonical instance the registry exists to prevent.

**Required plan amendment for Step 2:**

```cpp
// NEW entry added to FOREACH_ENSEMBLE_POST_LOAD between init_exit_bandits + blend_mode:
X(init_thompson_bandits, EnsembleModelZoo_InitThompsonBandits(ezoo,                  \
                             cfg.thompson_mu_prior,                                    \
                             cfg.thompson_precision_prior,                             \
                             cfg.thompson_precision_obs,                               \
                             cfg.thompson_rng_seed,                                    \
                             cfg.ensemble_min_warmup_predictions))                     \
```

Plus: `FOREACH_ENSEMBLE_POST_LOAD_COUNT 7` → `8` at `:2107`.

Plus: `EnsembleModelZoo_IsReadyForInference` predicate at `:2137-2151` must check `initialized_thompson_bandits` (or skip-check when `cfg.bandit_algorithm == 0` and Thompson stays uniform — define this semantic).

Plus: a corresponding `load_thompson_state` entry (between `load_bandit_state` and `save_interval`):

```cpp
X(load_thompson_state, EnsembleModelZoo_LoadThompsonState(ezoo, base_run_path))
```

Then `FOREACH_ENSEMBLE_POST_LOAD_COUNT` becomes 9.

**This is a HARD requirement — the v5.14.2.E.1 ship explicitly created this registry to make Class 18 mirror gaps impossible. Bypassing it would be a regression.**

---

## Mirror-array recommendation

**Plan introduces:** `EnsembleModelZoo.thompson_bandits[NUM_REGIMES]` parallel to existing `bandits[NUM_REGIMES]`.

**Class 18 framing (per `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md`):**

| Recurrence count of "parallel bandit array" pattern in EnsembleModelZoo | Decision per framework |
|---|---|
| 1 (current — only `bandits[]`) | One-off; no class |
| 2 (after v5.13.4 added `exit_bandits[]`) | SUSPECT recurring class — flag |
| 3 (after this plan adds `thompson_bandits[]`) | CONFIRMED recurring class — structural fix appropriate |
| 4 (if a 4th algorithm — UCB1, Bayesian linear, EXP4 — were planned) | STRUCTURAL FIX MANDATORY |

**Current state:** count=2 today (`bandits[]` + `exit_bandits[]`), with this plan it becomes count=3. Per framework, structural fix is "appropriate" at count=3. The framework is empirical not mandatory — the question to ask is whether a 4th algorithm is foreseeable.

**Forward-looking signal in plan body:** plan cross-refs `Pass 2 #5 finding (FoxML_Core decisioning/bayesian_policy.py:50-120)` + frames Thompson as "alternative for non-stationary markets". If the operator's Pass 2 backlog includes UCB1 / EXP4 / linear Thompson variants → 4th and 5th algorithm WILL come → structural fix MANDATORY at 5th instance regardless. Better to do it now at the 3rd than to do it later at the 5th.

**Sister pattern in the codebase:** `DESIGN_SPECS/framework-patterns/curve-registry-pattern.md` explicitly handles "named compute fns chosen by enum" with `FOREACH_<DOMAIN>_CURVE` X-macro registry + function-pointer dispatch table. This is the EXACT shape: bandit algorithm is a compute-mode enum chosen by `cfg.bandit_algorithm`. Pattern map:

```cpp
// PROPOSED (parallel to FOREACH_DEGRADATION_CURVE in ConfidenceScore.hpp:498-634):
#define FOREACH_BANDIT_ALGORITHM(X)                                        \
    X(EXP3,     0, BanditState,         Bandit_Init,         Bandit_Update,         Bandit_GetProbabilities,         "exponential weights, deterministic; pre-v5.14.10") \
    X(THOMPSON, 1, ThompsonBanditState, Thompson_Init,       Thompson_Update,       Thompson_GetProbabilities,       "Bayesian Gaussian conjugate; non-stationary") \
    X(BOTH,     2, /* dual storage */,  /* dispatch both */, /* dispatch both */,   /* dispatch both */,             "both run; Thompson choice telemetry-only")
```

But the curve-registry-pattern requires **uniform signature** for the dispatch contract. `Bandit_*` and `Thompson_*` have different state types (`BanditState` vs `ThompsonBanditState`) → uniform fn-ptr table doesn't fit cleanly. Either:

- **Option D-mod:** wrap each algorithm in a `BanditAlgorithmHandle { int kind; BanditState exp3_state; ThompsonBanditState thompson_state; }` union-style struct + dispatch on `kind` field. Pure registry pattern.
- **Option D-split:** keep parallel arrays (current plan); accept Class-18 risk; defer registry until 4th algorithm forces it. Document trigger in `DOCS/TECH_DEBT.md`.

**Recommendation:** **Option D-split for v5.14.10 + explicit TECH_DEBT trigger entry.** Reasoning:
1. Operator's recent rule (CLAUDE.local.md "structural fix preferred") leans toward fix-now, but the framework explicitly says "premature abstraction is anti-pattern" and "wait for triggers" when count is at 3 (not yet 4+).
2. Current plan keeps boundary stable (existing `bandits[]` callers untouched; backward-compat preserved for cfg=0 default).
3. Curve-registry signature mismatch (different state types) means a clean registry shape requires extra design work — not bounded; could expand the v5.14.10 ship beyond its current ~610 LOC budget.
4. TECH_DEBT entry with explicit trigger ("Next bandit-algorithm addition (4th instance) triggers FOREACH_BANDIT_ALGORITHM registry refactor") makes the deferral visible + preserved across sessions per the deferred-items-must-be-queryable rule.

**If operator decides retrofit-now instead:** plan must add a `BanditAlgorithmRegistry.hpp` design step before Step 1; ship size grows to ~900-1100 LOC; v5.14.10.A becomes the registry foundation, .B-.D become the Thompson application + persistence + tests on top of the registry.

---

## Call-sequence audit (Step 6 strengthening — Class 18 mirror prevention)

Walked source range `Strategies/StrategyParameters.hpp:887-1009` (Bandit dispatch block). Calls inventoried:

| Source-range call | Mirror-needed under Thompson? | Status |
|---|---|---|
| `Bandit_GetProbabilities(&ezoo->bandits[regime_id], w_curr)` (`:899`) | NO under cfg=1 (Thompson_Sample one-hot replaces); YES under cfg=2 (run both) | Plan Step 3 case 0/2 ✓ |
| `Bandit_GetProbabilities(&ezoo->bandits[ezoo->prev_regime_id], w_prev)` (`:900`) | Hysteresis blend — does Thompson have `prev` semantics? | **GAP** — plan does not address regime hysteresis under Thompson |
| `(int)config->regime_hysteresis` access (`:901`) | NO under cfg=1 (one-hot has no blend); YES under cfg=2 | **GAP** — plan does not address |
| `Bandit_GetProbabilities(&ezoo->bandits[regime_id], weights_buf)` (`:912`) | YES under cfg=0; replaced by Thompson_Sample under cfg=1 | Plan Step 3 ✓ |
| `BITMAP_IS_SET(gate_state->flags, MASK_RIDGE_WITHIN_ACTIVE)` (`:931`) | YES (Ridge override applies regardless of bandit algorithm; Ridge wins LAST) | Plan calls this out at Step 3 ✓ |
| `RidgeBlender_BuildCorr / RidgeBlender_Compute` (`:956, 973`) | YES (Ridge override interacts with weights_buf; Thompson sets weights_buf to one-hot before Ridge) | Plan calls this out at Step 3 ✓ |
| `topk_mask_from_weights(weights_buf, ezoo->primary_count, mctx->turnover_topk)` (`:996`) | YES (turnover diagnostic; reads weights_buf — works for one-hot + Exp3) | Plan does not mention; should be OK transparently since weights_buf is the boundary |
| `RollingTurnover_Push((RollingTurnover*)mctx->turnover_state, topk_mask)` (`:999`) | YES (downstream of weights_buf; works) | Plan does not mention; OK |
| `Model_Predict_Ensemble_Weighted(..., weights_buf, ...)` (`:1002`) | YES (consumes weights_buf — works for one-hot + Exp3) | Plan does not mention; OK |

**Class-18 mirror gap caught:** Hysteresis blend at `:896-913`. Plan code snippet only shows `case 0: Bandit_GetProbabilities; break; case 1: Thompson_Sample → one-hot; case 2: both` — does NOT show the hysteresis-on-regime-transition wrapper that wraps Bandit_GetProbabilities in the actual code. Plan must either:

(a) Define hysteresis behavior under Thompson — does Thompson's posterior get "blended" across regime transition? (Bayesian posterior doesn't have a natural "blend" — it's a draw, not a weight; arguably the natural Thompson hysteresis is to draw from BOTH regime posteriors and pick the higher-mean arm. This is ill-defined.)
(b) Skip hysteresis under Thompson — when `cfg.bandit_algorithm != 0`, hysteresis is no-op; Thompson always samples from current regime's posterior. (Simplest; loses some smoothing but acceptable.)
(c) Apply hysteresis only to Ridge weights when Ridge override fires + Thompson disabled — but this becomes confusing semantics.

**Recommendation:** option (b). Plan should explicitly state in Step 3: "Regime hysteresis blend (lines 896-913) only applies when `cfg.bandit_algorithm == 0`. Under Thompson, sampling always uses current regime's posterior; no hysteresis."

---

## Surface G discipline — plan claims N/A; verification says NOT N/A

**Plan says (line 53):** "Surface G discipline: N/A (no stamp body — runtime state only)"

**Actual:** `cfg.bandit_algorithm` IS a train/serve drift surface. If trainer runs with Thompson + serve runs with Exp3, the model behavior differs (different action selection → different reward attribution → different bandit posterior trajectory). This is exactly what FOREACH_STAMP_BOUND_CFG protects against.

**Required addition (sister to v5.14.0.B Ridge cfg fields' stamp binding):** Add `bandit_algorithm` to `FOREACH_STAMP_BOUND_CFG` registry at `ML_Headers/StampBoundCfgRegistry.hpp:99`. Stamp parser auto-handles via `STAMP_CFG_AUTOPOPULATE` (CLAUDE.md item 21). Drift detected at load time via `ValidateAgainstCfg`.

The `thompson_*` hyperparam fields (mu_prior / precision_prior / precision_obs / rng_seed) probably don't need stamp binding — they affect bandit *learning* not model *prediction* — but `bandit_algorithm` definitely does.

**Recommendation:** plan amendment to add `bandit_algorithm` as stamp-bound cfg field. Plan revision needed.

---

## Recommendations (priority order)

### 1. BLOCKING (plan-amendment required before coding)

a) **Add `EnsembleModelZoo_InitThompsonBandits` and `EnsembleModelZoo_LoadThompsonState` to `FOREACH_ENSEMBLE_POST_LOAD` registry** at `ML_Headers/CoreModelZoo.hpp:2088-2104` (extends count 7→9; updates `_IsReadyForInference` at `:2137-2151`). Bypassing the registry would re-introduce Class 18 mirror gaps that v5.14.2.E.1 just structurally extinguished.

b) **Address regime hysteresis under Thompson.** Plan Step 3 code snippet does not show hysteresis interaction. Recommend option (b): explicitly skip hysteresis under `bandit_algorithm != 0`.

c) **Add `bandit_algorithm` to `FOREACH_STAMP_BOUND_CFG`.** Plan claim "Surface G discipline: N/A" is incorrect. Algorithm choice IS train/serve drift.

### 2. STRUCTURAL DECISION (operator-level; defer-or-retrofit)

d) **Mirror-array Class 18 candidate.** Recurrence count after this plan = 3 (`bandits[]`, `exit_bandits[]`, `thompson_bandits[]`). Per `structural-fix-preferred-decision-framework.md` Step 2, count=3 is "CONFIRMED recurring class". Recommendation: **defer to next ship** with explicit TECH_DEBT trigger ("Next bandit-algorithm addition (4th instance) triggers FOREACH_BANDIT_ALGORITHM registry refactor"). Reasoning: curve-registry signature mismatch (different state types) makes the registry shape non-trivial; current ship is bounded at ~610 LOC and adding registry foundation expands to ~900-1100 LOC; deferral preserves boundary-stability rule. **Operator should explicitly accept this defer rather than absorb it.**

### 3. STALE-CLAIM CORRECTIONS (cold-pickup readability)

e) Plan REUSE claim line 90: replace `Strategies/StrategyParameters.hpp:~835` with `:658 (fn signature) + :887-1009 (dispatch block)`.

f) Plan should add explicit `ML_Headers/CoreModelZoo.hpp:833` cite for the `bandits[]` placement when adding `thompson_bandits[]`.

g) Plan should include `Thompson_Init` signature in Step 1 code block (currently shown only as forward-decl with `// TODO add args`).

h) Fix plan heading `v5.14.11` → `v5.14.10` (orchestrator Task #5).

### 4. TEST COVERAGE (mostly already covered in plan Step 6)

i) Plan Step 6 tests look good; add one more test: `cfg.bandit_algorithm=2` dual-mode under regime transition — verify hysteresis applies to Exp3 path but skips Thompson path (or whichever option chosen in 1b).

j) Add a registry-symmetry test (mirror of `tests/controller_test.cpp:20279-20344` PostLoadSetup tests) that verifies `EnsembleModelZoo_PostLoadSetup` invokes `InitThompsonBandits` + `LoadThompsonState`. Boot vs backtest vs hot-swap symmetry test.

---

## Cross-references

- `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md` — used for mirror-array Class-18 framing
- `DESIGN_SPECS/framework-patterns/curve-registry-pattern.md` — proposed structural-fix shape if retrofit-now is chosen
- `DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md` — base pattern (FOREACH_ENSEMBLE_POST_LOAD applies)
- `CLAUDE.md` items 13 + 19 + 21 — X-macro registry, structural fix, AUTOPOPULATE
- `CLAUDE.local.md` "structural fix preferred when bug class can recur" — operator framing
- `DOCS/TECH_DEBT.md` — deferral ledger (per going-forward rule, defer must land here with trigger)
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 18 — mirror-incomplete (same class as PARITY-009/010/011/012)

---

## Effort budget

This audit: ~12 min (medium plan, single-subsystem). Within /trace-deps's 5-15 min budget.
