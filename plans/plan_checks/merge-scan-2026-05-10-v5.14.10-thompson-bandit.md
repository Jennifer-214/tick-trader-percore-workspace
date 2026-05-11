# /merge-scan report — v5.14.10 Bayesian Thompson sampling bandit — 2026-05-10

**Target plan:** `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.10-bayesian-thompson-bandit.md`
**Target surfaces:** `ML_Headers/ThompsonBandit.hpp` (NEW), `ML_Headers/CoreModelZoo.hpp` (extend), `Strategies/StrategyParameters.hpp` (dispatch), `CoreFrameworks/OrderManager.hpp` (calibration log columns)
**Reference precedents in tree:** Bandit_GetProbabilities @ StrategyParameters.hpp:912, exit_bandits dispatch @ StrategyParameters.hpp:1127, FOREACH_ENSEMBLE_POST_LOAD @ CoreModelZoo.hpp:2088, FOREACH_SLOW_PATH_GATE @ SlowPathGateRegistry.hpp:69, calibration log writer @ OrderManager.hpp:1008

---

## Pre-existing context confirmation (verified against HEAD)

| Handoff claim | Status @ HEAD |
|---|---|
| `bandits[NUM_REGIMES]` @ CoreModelZoo.hpp:833 | VERIFIED (was: 833) |
| `exit_bandits[]` @ CoreModelZoo.hpp:845 | VERIFIED |
| `_SaveBanditState` @ 1865, `_SaveExitBanditState` @ 1887, `_LoadBanditState` @ 1911, `_LoadExitBanditState` @ 1942 | VERIFIED |
| `Bandit_SaveJSON` @ BanditLearning.hpp:369, `Bandit_LoadJSON` @ 503 | VERIFIED |
| `_InitBandits` @ 1238, `_InitExitBandits` @ 1286 | VERIFIED |
| `primary_count` is the n_arms source (CoreModelZoo.hpp:1246, 1306) | VERIFIED |
| FOREACH_ENSEMBLE_POST_LOAD pattern @ CoreModelZoo.hpp:2088 | VERIFIED — 7 entries; INIT_BANDITS + LOAD_BANDIT_STATE + INIT_EXIT_BANDITS + LOAD_EXIT_BANDIT_STATE all present |
| `cfg.bandit_algorithm` is NEW (no existing field) | CONFIRMED — only `bandit_enabled` (in `ml_cfg_flags` bitmap), `ridge_within_horizon`, `exit_blender_mode` exist as similar dispatch flags |
| TECH_DEBT-010 (FOREACH_CALIB_LOG_COL) status | OPEN per `DOCS/TECH_DEBT.md:254` — handoff is correct |
| TECH_DEBT-013 (BIT_FLAG storage) status | **CLOSED v5.14.9** per `DOCS/TECH_DEBT.md:273` — handoff incorrectly implies still-open; not relevant to Thompson plan anyway since `bandit_algorithm` is INT enum (3 values) not boolean |

**Drift discovered (orthogonal to plan, not blocking):** `ML_Headers/MlCfgFlagRegistry.hpp:55-56` already labels `MASK_ML_CFG_BANDIT_ENABLED` / `MASK_ML_CFG_EXIT_BANDIT_ENABLED` with description "Thompson-sampling bandit" but the actual implementation @ CoreModelZoo.hpp uses Exp3-IX (`Bandit_GetProbabilities` returns exponential weights). When v5.14.10 lands, this stale description either becomes truthful (if Thompson takes that flag's role) or needs correction. Operator awareness item; orphan from a prior pass — not v5.14.10's bug.

---

## Atomic load redundancies — none flagged (NA scope)

Thompson is per-core slow-path-only state, no cross-thread atomics. Only `bandits[r].weights[]` accessed via `Bandit_GetProbabilities` reads — single-thread per-core ezoo. No new atomic loads introduced.

---

## Clock-read redundancies — none flagged

Thompson_Sample uses `mt19937_64` advanced by `rng_state` (cfg-set seed); doesn't read clock. Persistence path's `Bandit_SaveJSON` already does its own `clock_gettime(CLOCK_REALTIME)` for `saved_at_ts_ns` — Thompson's parallel save would do the same. **Merge candidate (LOW):** if `_SaveThompsonState` runs in the same shutdown loop as `_SaveBanditState` + `_SaveExitBanditState` (verified: EngineSharded.hpp:3528 loop hits all in one for-i), the 3 clock_gettime calls could share one `now_ts` parameter. Saves ~30ns per shutdown — cosmetic, not worth structural change.

---

## Cfg-access redundancies — none flagged

Plan adds 1 INT (`bandit_algorithm`) + 4 FPN<F> + 1 uint64. ML_BuildParameters reads `config->bandit_algorithm` once per call (in switch). No 5+-times-in-function access pattern introduced.

---

## Function-body parallelism candidates

### M1 — Thompson_Init / Update / Sample MIRROR Bandit_Init / Update / Select pattern (DEFER to T1 below)

The plan's `Thompson_Init`/`Thompson_Update`/`Thompson_Sample` API surface is INTENTIONALLY parallel to `Bandit_Init`/`Bandit_Update`/`Bandit_Select` (the latter exists @ BanditLearning.hpp:201 but is unused; ensemble flow uses `Bandit_GetProbabilities` directly). Math kernels are completely different (Gaussian conjugate posterior vs exponential weights). Body overlap < 10%. **Do NOT extract a shared walker** — wins would be 0; harm to clarity > 0. Two parallel APIs is the right shape.

However, the persistence + boot wiring is a different story — see T1 + T2 below.

### M2 — Calibration log writer ad-hoc extension would activate TECH_DEBT-010

**Current state (OrderManager.hpp:1008-1013, 1293-1295):**
- 9 hardcoded columns, format string + header are sister literals
- Plan Step 6 cfg=2 mode adds "log per-fill telemetry (which algorithm chose what arm)"
- Naive extension = touch 2 sites (header literal + writer fprintf) per new column

**Plan's expected new columns (cfg=2 telemetry):**
1. `exp3_chosen_arm` (int) — argmax of Bandit_GetProbabilities weights
2. `exp3_top_weight` (double) — max weight value
3. `thompson_chosen_arm` (int)
4. `thompson_top_arm_prob` (double, optional from Thompson_GetProbabilities)
5. `regime_id_at_pick` (int) — context for offline analysis

**That's 4-5 new columns in ONE umbrella → meets TECH_DEBT-010 trigger** ("Next ship that adds 3+ calibration log columns in one umbrella"). The debt's exact trigger condition fires.

**Proposed unification (FOREACH_CALIB_LOG_COL registry):**
```cpp
#define FOREACH_CALIB_LOG_COL(X)                                                       \
    X(timestamp_us,         "%llu",  uint64_t,   ts_us)                                \
    X(slot,                 "%d",    int,        pslot)                                \
    X(exit_predicted_flag,  "%u",    unsigned,   pred_flag)                            \
    /* ... 6 existing columns ... */                                                   \
    X(exp3_chosen_arm,      "%d",    int,        exp3_arm)                             \
    X(thompson_chosen_arm,  "%d",    int,        ts_arm)                               \
    /* ... */
```
- Auto-generates: header literal walker, writer fprintf walker, optional reader for tests
- Adding a future column = 1 row
- Wins: extinguishes recurring 2-site (will become 3-site if scaler validation added later) drift class

**Effort:** ~3-4h structural ship per TECH_DEBT-010 cost estimate. Distinct sub-tag from v5.14.10.A-.D math/dispatch/persistence work; can land as v5.14.10.E (registry refactor) BEFORE .B (cfg=2 dispatch) so .B writes through the registry from day one.

**OR:** absorb the 4-5 columns ad-hoc in v5.14.10.B + accept that the 6th-column ship triggers the registry. Operator decides absorb-vs-defer per cost preference.

**Recommendation: ABSORB** — TECH_DEBT-010 is LOW severity, plan's column additions are well-scoped (telemetry-only, no scaler/parser surface), and registry refactor cost > the immediate ad-hoc cost by ~2x for THIS ship. The recurrence cost only compounds if a 3rd ship adds more columns; if v5.14.10 is the last calibration-log extension for ≥6 months, defer pays off. **However**, per CLAUDE.md item 19 (structural fix preferred when bug class can recur) + CLAUDE.local.md "structural fix > direct patch" rule, the conservative call is REGISTRY NOW because Thompson Phase 4 is followed by maker work (v6.0 per TECH_DEBT-010 cross-ref) which adds maker-fill columns. **Suggested decision-aid: ask Caramel.**

---

## State-field reuse candidates

### S1 — Thompson `rng_state` field is JUSTIFIED-NEW (no reusable RNG anywhere)

**Per handoff focus area #1:** scanned `FoxLIB`, `FixedPoint`, `CoreFrameworks`, `Strategies`, `CoreContext`, `ExecutionCore_State`, `EnsembleModelZoo`, `ConfidenceScorer`. **Result: NO existing per-core or engine-wide RNG state.** Findings:

- `BanditLearning.hpp:201` `Bandit_Select(b, uniform_rand)` takes uniform random as PARAMETER (caller supplies); never called in tree (no RNG plumbing exists)
- `MockGenerator.hpp` has its own LCG state but it's deterministic backtest-fixture-local, not engine state — not promotable
- `FoxLIB/include/foxlib/bandit.hpp` has no RNG facility either
- `CoreContext`, `ExecutionCore_State`, `EnsembleModelZoo`, `ConfidenceScorer`, `EventLoopState` — all RNG-free

**Conclusion:** Thompson `rng_state` field on `ThompsonBanditState` is JUSTIFIED-NEW. There is no shared RNG to reuse. Thompson's per-bandit RNG is correct: bandit-local seed + advance preserves replay-determinism per-bandit and avoids inter-bandit coupling.

**FUTURE OPPORTUNITY (post-v5.14.10):** if a 2nd RNG consumer arrives (e.g., Bayesian rolling regression with prior sampling, randomized exploration in maker order placement), promote a per-core `RngState` field to `CoreContext` or `EnsembleModelZoo` and have all consumers borrow from it. Until then, single consumer = on-the-struct is correct and avoids premature abstraction. Capture as comment in ThompsonBanditState declaration.

### S2 — `n_arms` mirroring of `primary_count` is JUSTIFIED-MIRROR (no reduction possible)

Per handoff focus area #5: `Thompson_Init`'s `n_arms` arg = `ezoo->primary_count` mirrors existing pattern at CoreModelZoo.hpp:1259 / :1306 (`Bandit_Init(&ezoo->bandits[r], n_arms, ...)`). The local `n_arms` variable is captured from `ezoo->primary_count` once and reused per-regime — already optimal. Thompson should follow IDENTICAL shape. **No new dimension constant needed.**

---

## Cross-plan merge candidates

### T1 — Thompson PostLoadSetup wiring SHOULD be a new FOREACH_ENSEMBLE_POST_LOAD entry (HIGH PRIORITY structural)

**Current state:** `FOREACH_ENSEMBLE_POST_LOAD` @ CoreModelZoo.hpp:2088 has 7 entries:
1. `init_bandits`
2. `init_exit_bandits`
3. `blend_mode`
4. `disabled_horizons`
5. `load_bandit_state`
6. `save_interval`
7. `load_exit_bandit`

**Plan's stated wiring (Step 2 + 4):**
- `EnsembleModelZoo_InitThompsonBandits` after `_LoadFromCfg`
- `EnsembleModelZoo_SaveThompsonState` in periodic + shutdown
- `EnsembleModelZoo_LoadThompsonState` at boot (parallel to bandit_state path)

**Per CLAUDE.md item 19 + CLAUDE.local.md "structural fix > direct patch":** Thompson init/save/load is the EXACT mirror class that PostLoadSetup was built to extinguish (PARITY-009/010/011/012 closure v5.14.2.E.1). If Thompson init lands as ad-hoc additions to all 3 caller sites (boot in EngineSharded.hpp:~1206, backtest in BacktestSharded.hpp:~345, hot-swap site), the next contributor adding bandit-class state hits Class 18 risk again.

**Proposed unification:**
```cpp
#define FOREACH_ENSEMBLE_POST_LOAD(X)                                          \
    X(init_bandits, ...)                                                       \
    X(init_exit_bandits, ...)                                                  \
    X(init_thompson_bandits,                                                   \
        EnsembleModelZoo_InitThompsonBandits(ezoo,                             \
            cfg.thompson_mu_prior, cfg.thompson_precision_prior,               \
            cfg.thompson_precision_obs, cfg.thompson_rng_seed))                \
    X(blend_mode, ...)                                                         \
    X(disabled_horizons, ...)                                                  \
    X(load_bandit_state, ...)                                                  \
    X(save_interval, ...)                                                      \
    X(load_exit_bandit, ...)                                                   \
    X(load_thompson_state,                                                     \
        EnsembleModelZoo_LoadThompsonState(ezoo, base_run_path))
```
- AND extend `FOREACH_ENSEMBLE_POST_LOAD_COUNT` from 7 → 9
- AND extend `EnsembleModelZoo_IsReadyForInference` predicate (CoreModelZoo.hpp:2147) to include Thompson initialized check (gated on cfg.bandit_algorithm == 1 || == 2 — only if Thompson is in use)

**Wins:**
- Boot, backtest, hot-swap auto-inherit Thompson init/load — zero ad-hoc edits to those 3 sites
- Adding next bandit variant (e.g., UCB1 in v5.X+) = 1 row each; pattern enforced
- Consistent with Class 18 prevention discipline (CLAUDE.md item 19); same shape as v5.14.2.E.1 close

**Cost:** ~30 LOC added to FOREACH macro + 2 helper definitions; vs ~20 LOC saved across 3 caller sites. Net ~+10 LOC but vastly improved enforcement.

**Recommendation: ADOPT (HIGH).** This is the highest-impact merge in the scan. Per CLAUDE.local.md the structural-preferred rule explicitly applies: "When facing a bug whose ROOT CAUSE is 'same pattern at multiple sites drifted apart' (Class 18 mirror), prefer compile-time enforcement." Thompson init/save/load is a textbook Class-18-prevention surface.

### T2 — Thompson shutdown save MIRRORS bandit shutdown save loop (LOW priority — already implicitly covered by T1)

**Current state:** EngineSharded.hpp:3528-3552 — single for-loop iterates cores, calls `_SaveBanditState` + `_SaveExitBanditState` per ezoo. Thompson would naturally extend with `_SaveThompsonState` as a 3rd call inside the same loop.

**If T1 lands:** PostLoadSetup pattern handles boot side; shutdown is the inverse and should follow the same registry treatment if growth continues. Today it's only 2 (now 3) inline saves — registry overhead > inline-save cost. **DEFER** as a `// FUTURE OPPORTUNITY:` comment when the 4th save call would land.

**Proposed sub-tag in plan:** add to v5.14.10.C persistence ship — extend the EngineSharded shutdown loop with `EnsembleModelZoo_SaveThompsonState` call mirroring lines 3543-3550. ~10 LOC. If T1 adopted, the registry handles this for free.

### T3 — Thompson dispatch in ML_BuildParameters can REUSE the ridge-style cached gate pattern (DEFER — bandit_algorithm is INT not bool)

**Per handoff focus area #6:** Could `cfg.bandit_algorithm` dispatch be hoisted to a slow-path predicate cache like `MASK_RIDGE_WITHIN_ACTIVE`? **Answer: NOT directly applicable** — `bandit_algorithm` is INT enum (0/1/2), not boolean, so it can't fit a 1-bit slot in the `gate_state->flags` uint16_t bitmap. The bitmap pattern only stores predicates that are TRUE/FALSE.

**Alternatives evaluated:**

1. **2 bits in a slow-path-cache uint8_t field** (`gate_state->bandit_algorithm_cached`): adds 1 byte to SlowPathGateState. Branch in dispatch becomes "load cached byte → switch on it" instead of "load cfg pointer → deref → switch". Cost saving: ~3-5ns per ML cycle (one fewer pointer chase). Since ML cycles are ~10-50µs, this is sub-1% — **not worth the SlowPathGateState extension**.

2. **2 bool fields in SlowPathGateState** (`thompson_active`, `both_mode_active`) via bitmap MASK_THOMPSON_ACTIVE + MASK_BOTH_ACTIVE: same effective cost as #1 but with DUAL-state design quirk (3 states from 2 bits). Cleaner if Thompson is binary toggleable, but Phase 4's "Both" mode for telemetry argues for keeping the 3-way enum visible. **Skip.**

3. **Keep as inline cfg read.** Modern compilers SROA the cfg pointer + the switch is well-predicted (cfg.bandit_algorithm is set once at boot, never changes mid-session). Mispredict cost ≈ 0 after warmup. **CHOOSE THIS.**

**Recommendation: NO CHANGE.** Plan's switch on `config->bandit_algorithm` is correct as-is. Branch predictor handles a single static-after-boot value perfectly; gate cache adds infrastructure for sub-1% savings. Capture rationale as comment near the switch site so future contributors don't re-litigate.

**Sister observation:** `ridge_within_horizon` and `exit_blender_mode` are ALSO 0/1 INT fields that have been migrated into MASK_RIDGE_WITHIN_ACTIVE / MASK_EXIT_BLENDER_ACTIVE bits — they were promoted because they're boolean-shaped. `bandit_algorithm` doesn't fit that mold (3-way enum). The asymmetry is intentional.

### T4 — JSON I/O primitive reuse — Bandit_SaveJSON / Bandit_LoadJSON shape is BanditState-specific (NOT directly reusable)

**Per handoff focus area #2:** Bandit_SaveJSON @ BanditLearning.hpp:369 takes `const BanditState* bandits, int n_regimes, ...` and emits BanditState-specific fields (`weights`, `cum_reward`, `pulls`, `arm_names`, `total_steps`).

**Thompson's persistence requirements** (per plan Step 4):
- Per-regime per-arm: `mu_post[]`, `precision_post[]`, `total_pulls[]`
- Per-regime: `n_arms`, prior hyperparams (mu_prior, precision_prior, precision_obs), rng_state

**Field overlap with BanditState:** `n_arms`, possibly `total_pulls` ↔ `pulls` (same semantics). **5+ Thompson-specific fields** not in BanditState. Reusing the existing function via templating would require generalizing both:
- `format_version` → per-state-type version constant
- field walker → field set per state type
- this becomes a templated `template<typename StateT> int State_SaveJSON(...)` with type-specific field lists

**Effort:** ~80 LOC to generalize + ~40 LOC ThompsonBanditState specialization vs ~80 LOC straight-copy of Save/Load helpers for ThompsonBanditState. Roughly even.

**Truly reusable primitives (LOW-effort merge):**
- `Bandit_JsonFindKey` @ BanditLearning.hpp:440 (key lookup walker)
- `Bandit_JsonParseDoubleArray` @ :455
- `Bandit_JsonParseIntArray` @ :473

These three are ALREADY generic (no BanditState dependency) — just named with `Bandit_` prefix. **Recommendation:** Extract to a `tt::json_io` namespace (or `JsonIo_FindKey`, `JsonIo_ParseDoubleArray`, `JsonIo_ParseIntArray`) that both `Bandit_LoadJSON` AND new `Thompson_LoadJSON` import. Pure rename + namespace extraction; zero behavior change.

**Effort:** ~15 minutes (rename + 2 callers updated). Wins: clarity (these primitives are now obviously reusable for any future JSON state-load — exit_bandit_state, thompson_state, future ridge_state persistence). **Recommendation: ADOPT** as v5.14.10.A prep step (or fold into v5.14.10.C persistence ship).

For the higher-level `Save/LoadJSON` SHELL: leave parallel — too much per-state divergence to template cleanly. Saves no LOC and harms readability.

### T5 — Cfg field placement: thompson_* fields fit in existing FPN/INT cfg block (NO bitmap migration needed)

Plan adds 1 INT (`bandit_algorithm`) + 4 FPN<F> (`thompson_mu_prior`, `thompson_precision_prior`, `thompson_precision_obs`) + 1 uint64 (`thompson_rng_seed`). None of these are boolean → none qualify for ml_cfg_flags bitmap entry. Standard cfg block placement (group with `ridge_*` and `exit_blender_*` adjacent fields) is correct. **No merge.**

---

## Branch-vs-branchless flags — none flagged

ML_BuildParameters is slow-path (per ML cycle, 10-50µs budget). Per /merge-scan heuristic: "Slow path: leave branches alone unless they're obviously high-mispredict." `bandit_algorithm` is set at boot, never changes — switch is single-target after warmup, predictor accuracy ≈ 100%. Don't touch.

---

## Overall recommendation

### TOP 3 highest-impact items to act on

1. **T1 (HIGH) — Thompson init/save/load via FOREACH_ENSEMBLE_POST_LOAD registry extension.** Per CLAUDE.md item 19 + CLAUDE.local.md "structural fix > direct patch", this is the textbook Class 18 prevention surface. Boot/backtest/hot-swap inherit for free; future bandit variants get same wiring with 1 row. Cost: ~30 LOC; saves 3-site ad-hoc edits. **Adoption changes plan Step 2 + Step 4 wiring approach.**

2. **T4 (MEDIUM) — Extract Bandit_JsonFindKey + Bandit_JsonParseDoubleArray + Bandit_JsonParseIntArray to a generic `tt::json_io` namespace.** Pure rename + 2-caller-update. Zero behavior change. ~15 min. Wins: makes Thompson_LoadJSON reuse trivial; foreshadows future state-persistence reuse. **Fold into v5.14.10.C.**

3. **M2 (MEDIUM, decision-required) — FOREACH_CALIB_LOG_COL registry NOW vs. absorb 4-5 ad-hoc columns.** Plan's cfg=2 telemetry adds enough columns to ACTIVATE TECH_DEBT-010 trigger condition. Per CLAUDE.md item 19, structural-now is preferred; per cost, absorb-now is cheaper by ~2x for this single ship. **Operator-discretion call** — recommend asking Caramel during the synthesis step. If maker work (v6.0) is queued shortly, structural-now is the right call.

### Items deferrable to next sweep

- **T2** — Thompson shutdown save mirrors bandit shutdown save. If T1 adopted, this is automatic. If T1 deferred, ad-hoc shutdown extension is fine for ONE more save (3 calls total); registry triggers at the 4th.
- **T3** — bandit_algorithm cached predicate. Sub-1% savings; defer until either (a) ML cycle budget tightens, OR (b) bandit_algorithm becomes runtime-toggleable mid-session (not currently planned).
- **Clock-share in 3-clock_gettime shutdown loop** — cosmetic ~30ns saving. Skip.

### Items to leave alone (intentional duplication)

- **M1 (Thompson_* mirror Bandit_*)** — math kernels are different; parallel APIs is correct shape.
- **S1 (Thompson rng_state field)** — no shared RNG exists in tree to reuse; field is justified-new.
- **S2 (n_arms = primary_count mirror)** — already uses primary_count; mirrors are local-variable captures, not state duplication.
- **T5 (cfg field placement)** — non-boolean fields don't fit bitmap pattern.
- **Branchless conversion of bandit_algorithm switch** — slow-path, well-predicted, no win.

### Cross-cutting note

The **MlCfgFlagRegistry comment drift** (lines 55-56 already say "Thompson-sampling bandit" for the Exp3-implementing flags) is orphan-doc rot from a prior pass. Independent of plan — recommend operator captures as a 1-line cleanup (`/dust` candidate) regardless of v5.14.10 outcome. If v5.14.10 lands with bandit_algorithm=1 as primary path, the comment becomes truthful; if Exp3 stays default, the comment needs correction. Either way it's not v5.14.10's responsibility, just visible from this scan.

---

**Verdict:** v5.14.10 plan is **GREEN with 1 HIGH-priority structural recommendation (T1)** + 1 MEDIUM-priority easy-win (T4) + 1 MEDIUM-priority operator decision (M2). Plan as-drafted ships correctly without these adoptions but accumulates Class-18-mirror risk (T1) and a recurring ad-hoc-extension drift class (M2 → TECH_DEBT-010). T4 is virtually free.
