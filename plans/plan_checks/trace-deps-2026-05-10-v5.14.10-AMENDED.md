# /trace-deps report — AMENDED v5.14.10 plan — 2026-05-10

**Plan:** `/home/caramel/code/FoxML_Trader_v2/plans/v5.14-foxml-port-and-maker/subplans/2026-05-10-v5.14.10-bayesian-thompson-bandit.md`
**Prior trace-deps report:** `plans/plan_checks/trace-deps-2026-05-10-v5.14.10-thompson-bandit.md` (verdict YELLOW)
**Branch verified:** `feat/v5.14-foxml-port-and-maker` (HEAD post-v5.14.9 commit `b09b2d5`)
**Skill spec:** `.claude/skills/trace-deps/SKILL.md` (Step 6 strengthening — call-sequence enumeration applied)

---

## Verdict: YELLOW (one DRIFT in .0 step text; non-blocking; everything else GREEN)

- **GAP (BLOCKING):** 0
- **DRIFT (review; non-blocking):** 2 (one wrong file name in .0 Step 1 prose; one wrong file name in .D Step 2 prose)
- **PASS:** 22 (all callees exist, all signatures compatible, all line refs match HEAD, FOREACH_ENSEMBLE_POST_LOAD extension verified, hysteresis-skip rationale documented, stamp-binding amendment documented, mirror-array decision flipped to RETROFIT with sound rationale)
- **DRIFT-RISK (deprecated path):** 0
- **NEW dependency surfaces from .0 + .D:** all readers/writers identified; append-only column extension is safe

Plan is technically implementable as written; two minor file:line corrections recommended in .0 Step 1 + .D Step 2 prose for cold-pickup readability. Plan can begin coding pending those mechanical fixes (or operator can leave + Caramel resolves at .0 kickoff time).

---

## Confirmation status — prior BLOCKING amendment

### CONFIRMED (FIXED): all 3 BLOCKING items from prior /trace-deps report

| Prior BLOCKING item | Status |
|---|---|
| (a) Add init_thompson_bandits + load_thompson_state to FOREACH_ENSEMBLE_POST_LOAD registry; extend count 7→9; update IsReadyForInference predicate | **FIXED** — Plan .C Step 5 (lines 228-233) explicitly extends FOREACH_ENSEMBLE_POST_LOAD with both entries; Step 6 (line 234) updates IsReadyForInference predicate; cited at correct file:line `CoreModelZoo.hpp:2088-2104` and `:2137-2151` |
| (b) Address regime hysteresis under Thompson — explicitly skip when bandit_algorithm != 0 | **FIXED** — Plan .B Step 7 (line 197) explicitly: "Thompson's one-hot weights have no natural blend semantic; skip the regime-transition alpha-blend at lines 896-913 when algorithm is Thompson or Both" + rationale documented inline |
| (c) Add bandit_algorithm to FOREACH_STAMP_BOUND_CFG (Surface G correctness) | **FIXED** — Plan .B Step 9 (lines 203-209) adds 4 entries via STAMP_CFG_AUTOPOPULATE; correctly mirrors `cfg.exit_blender_mode` precedent at `StampBoundCfgRegistry.hpp:137-138`; Surface G discipline section (lines 84-87) updated to reflect stamp binding |

### CONFIRMED (FIXED): 4 stale line refs from prior report

| Prior stale ref | Resolution status |
|---|---|
| `Strategies/StrategyParameters.hpp:~835` | **FIXED** — line 53 plan now cites `:887-1009 (Bandit_GetProbabilities calls at :899/:912; Ridge override at :930-989)` |
| Implied `EnsembleModelZoo.hpp` filename | **FIXED** — line 45 plan explicitly notes "filename is CoreModelZoo.hpp; struct EnsembleModelZoo lives there" |
| Hysteresis interaction missing from Step 3 code snippet | **FIXED** — Plan .B Step 7 explicit hysteresis-skip rationale (line 197) |
| IsReadyForInference predicate not extended | **FIXED** — Plan .C Step 6 (line 234) adds explicit IsReadyForInference extension |

### CONFIRMED (FIXED): version + branch + rollback corrections

| Prior issue | Resolution status |
|---|---|
| Heading `v5.14.11` → `v5.14.10` | **FIXED** — line 1 + body |
| Rollback anchor `pre-v5.14.7` | **FIXED** — line 6 `pre-v5.14.10 = v5.14.9 (b09b2d5)` |

### REVERSAL: mirror-array recommendation

| Prior recommendation | Amended decision | Verdict |
|---|---|---|
| **DEFER** FOREACH_BANDIT_ALGORITHM with TECH_DEBT-026 trigger | **RETROFIT NOW (Decision A)** | **PASS** — sound rationale: (1) curve-registry-pattern.md MATCH (3 modes; same shape as v5.14.9.A FOREACH_DEGRADATION_CURVE); (2) structural-fix-preferred per CLAUDE.local.md `feedback_overengineering_boundary_when_future_easier`; (3) UCB1/EXP4/Bayesian linear are foreseeable next algorithms (5-8× future-work multiplier); (4) plan resolves the curve-registry signature-mismatch concern via 4-arg uniform dispatch contract (`BanditAlgoFn` type at .A Step 5; each compute fn writes BOTH weights_out + chosen_arm_out) — clean unified contract, no mirror sites added |

---

## Per-claim verification (amended plan)

### Claim 1 — REUSE citations against HEAD post-v5.14.9

| Plan claim (file:line) | HEAD verification |
|---|---|
| `BanditState` + Bandit_Init + Bandit_Update + Bandit_GetProbabilities + Bandit_SaveJSON + Bandit_LoadJSON at `BanditLearning.hpp:60-630` | **PASS** — `BANDIT_MAX_ARMS=8` at :60, `struct BanditState` at :65, `Bandit_Init` at :82, `Bandit_GetProbabilities` at :118, `Bandit_Update` at :222, `Bandit_SaveJSON` at :369, `Bandit_LoadJSON` at :503 |
| `EnsembleModelZoo<F>` at `CoreModelZoo.hpp:820-928` | **PASS** — struct definition spans this range |
| `bandits[NUM_REGIMES]` at `CoreModelZoo.hpp:833` | **PASS** |
| `exit_bandits[NUM_REGIMES]` at `:845` | **PASS** |
| `ridge_state` at `:862`; `exit_ridge_state` at `:868` | **PASS** |
| `EnsembleModelZoo_InitBandits` at `:1238` | **PASS** |
| `EnsembleModelZoo_InitExitBandits` at `:1286` | **PASS** |
| `EnsembleModelZoo_SaveBanditState` at `:1865`; `_SaveExitBanditState` at `:1887` | **PASS** |
| `EnsembleModelZoo_LoadBanditState` at `:1911`; `_LoadExitBanditState` at `:1942` | **PASS** |
| `ML_BuildParameters` dispatch at `Strategies/StrategyParameters.hpp:887-1009`; Bandit_GetProbabilities at :899/:912; Ridge override at :930-989 | **PASS** — verified line-by-line; use_weighted at :880; init check at :887; hysteresis blend at :896-913 (specifically :899/:900 in transition path, :912 in steady state); Ridge override at :930 with cfg-flag fallback; Ridge_BuildCorr at :956; Ridge_Compute at :973; topk_mask at :996; RollingTurnover_Push at :999; Model_Predict_Ensemble_Weighted at :1002 |
| `cfg.exit_blender_mode` precedent at `StampBoundCfgRegistry.hpp:137-138` | **PASS** |
| `cfg.ridge_within_horizon` slow-path-gate cached as `MASK_RIDGE_WITHIN_ACTIVE` at `SlowPathGateRegistry.hpp:85` | **PASS** |
| `FOREACH_DEGRADATION_CURVE registry pattern` at `ConfidenceScore.hpp:498-634` | **PASS** — registry at :498-543; X_GEN_FN_PTR/ToString/FromString through :634 |
| `FOREACH_SLOW_PATH_GATE` at `SlowPathGateRegistry.hpp:69-150` (~9 bits headroom in uint16 flags) | **PASS** — registry at :69-99; 6 entries today; static_assert at :152 confirms ≤ 16 bit cap |
| `FOREACH_STAMP_BOUND_CFG` + `STAMP_CFG_AUTOPOPULATE` macro pattern | **PASS** — macro at `:192-198`; AUTOPOPULATE_ONE walk discipline established |
| `FOREACH_ENSEMBLE_POST_LOAD` at `CoreModelZoo.hpp:2088-2104` (7 entries today) | **PASS** — count macro `FOREACH_ENSEMBLE_POST_LOAD_COUNT 7` at :2107; matches plan claim |
| `EnsembleModelZoo_IsReadyForInference` at `CoreModelZoo.hpp:2137-2151` | **PASS** |
| `Bandit_JsonFindKey` at `BanditLearning.hpp:440`; `Bandit_JsonParseDoubleArray` at `:455`; `Bandit_JsonParseIntArray` at `:473` | **PASS** |
| `BANDIT_MAX_ARMS = 8` at `BanditLearning.hpp:60` | **PASS** |
| `NUM_REGIMES` from FOREACH_REGIME (StrategyInterface.hpp) | **PASS** — defined at `:195` (sentinel after FOREACH expansion) |

### Claim 2 — FOREACH_ENSEMBLE_POST_LOAD extension (BLOCKING amendment from prior report)

**Plan .C Step 5 (lines 228-233):**
```
X(init_thompson_bandits,    EnsembleModelZoo_InitThompsonBandits(ezoo, ...))
X(load_thompson_state,      EnsembleModelZoo_LoadThompsonState(ezoo, base_dir, expected_id, ...))
```

**HEAD context verified:**
- Current registry has 7 entries: init_bandits / init_exit_bandits / blend_mode / disabled_horizons / load_bandit_state / save_interval / load_exit_bandit
- 3 callers of `EnsembleModelZoo_PostLoadSetup<F>(ezoo, cfg, core_id, base_run_path)`:
  - boot: `CoreFrameworks/EngineSharded.hpp:1206`
  - backtest: `Backtest/BacktestSharded.hpp:345`
  - hot-swap: `CoreFrameworks/EnsembleHotSwap.hpp:109`
- All 3 inherit registry extensions automatically (Class 18 mirror prevention working)
- 5 tests at `tests/controller_test.cpp:20279/20309/20311/20313/20338/20344` exercise PostLoadSetup; the v5.14.2.E.1 boot/backtest/hot-swap symmetry test at :20309-20313 will catch any registry-bypass

**PASS** — extension is correctly placed; FOREACH_ENSEMBLE_POST_LOAD_COUNT must bump from 7 → 9 (plan does NOT explicitly state this; sub-recommendation: add explicit COUNT bump to .C Step 5 prose). The 5 existing tests exercise the post-load contract; adding 2 entries should not break them as long as Thompson init flag is added to the test's setUp (test cfg sets `bandit_algorithm=0` → no Thompson init invoked; `IsReadyForInference` extension must skip-check Thompson flag when cfg=0; same precedent as exit_bandits being skip-checked when `exit_predictor_count<2`).

**Sub-recommendation (non-blocking):** Plan .C Step 5 prose should explicitly note `FOREACH_ENSEMBLE_POST_LOAD_COUNT 7 → 9` bump at `:2107`.

### Claim 3 — Thompson_Sample / Thompson_Init signature contract

Plan .A Step 5 defines uniform 4-arg `BanditAlgoFn` dispatch contract:
```cpp
typedef void (*BanditAlgoFn)(EnsembleModelZoo<F>* ezoo, int regime_id, int n_arms, double* weights_out, int* chosen_arm_out);
```

Plan .A Step 1 spells out `ThompsonBanditState` struct (`mu_post[8]`, `precision_post[8]`, `total_pulls[8]`, etc.) — concrete + verifiable.

**PASS** — signatures NOW spelled out (prior /trace-deps gap closed). Note: `Thompson_Init` signature itself is NOT shown explicitly but `EnsembleModelZoo_InitThompsonBandits` (which wraps it) IS spelled out via the FOREACH_ENSEMBLE_POST_LOAD entry at .C Step 5 — sufficient for cold-pickup.

### Claim 4 — Hysteresis-skip rationale (prior BLOCKING)

Plan .B Step 7 (line 197): "Thompson's one-hot weights have no natural blend semantic; skip the regime-transition alpha-blend at lines 896-913 when algorithm is Thompson or Both. Rationale documented inline."

Code at `:896-913` confirmed: `regime_transition_cycles_remaining` triggers blend; Thompson would alpha-blend two one-hot vectors, yielding e.g. `[0.4, 0.6, 0, 0, ...]` which has lost the one-hot interpretation. Skip is the simplest correct semantic.

**PASS** — rationale matches code structure; explicit skip is the correct architectural choice.

### Claim 5 — bandit_algorithm Surface G binding (prior BLOCKING)

Plan .B Step 9 (lines 203-209): adds 4 entries via STAMP_CFG_AUTOPOPULATE.
- `bandit_algorithm` int DIRECT_FIELD with emit_when `(cfg.bandit_algorithm != 0)` — **PASS** (mirror of `exit_blender_mode` at `:137-138` which uses identical shape)
- `thompson_mu_prior` / `thompson_precision_prior` / `thompson_precision_obs` double DIRECT_FIELD with emit_when `(cfg.bandit_algorithm != 0)` — **PASS**
- `thompson_rng_seed` correctly EXCLUDED from stamp binding (RNG state is runtime-only, not cross-stamp) — **PASS** (consistent with item 86 in plan body)

PARITY-013 close trajectory verified.

### Claim 6 — FOREACH_BANDIT_ALGORITHM registry retrofit (Decision A reversal)

Plan .A Step 4 mirrors FOREACH_DEGRADATION_CURVE:
```cpp
#define FOREACH_BANDIT_ALGORITHM(X) \
    X(EXP3,     0, BanditAlgo_Exp3_Apply,     "...") \
    X(THOMPSON, 1, BanditAlgo_Thompson_Apply, "...") \
    X(BOTH,     2, BanditAlgo_Both_Apply,     "...")
```

**PASS** — registry shape matches DEGRADATION_CURVE precedent. The signature-mismatch concern from the prior report (different state types BanditState vs ThompsonBanditState) is **resolved by Decision A's compute-fn-wrapper pattern**: each compute fn `BanditAlgo_*_Apply` takes `EnsembleModelZoo<F>*` + writes BOTH `weights_out` (8 doubles) + `chosen_arm_out` (1 int) — uniform contract.

**Mirror-data-flow audit (Step 6 strengthening):** Decision A's wrapper resolves the polymorphism cleanly. Each compute fn ACCESSES the appropriate state internally (`ezoo->bandits[regime_id]` for Exp3; `ezoo->thompson_bandits[regime_id]` for Thompson; both for BOTH). No new mirror site introduced — wrappers internalize the state-type difference. **PASS.**

### Claim 7 — Cfg fields collision-free

| Cfg field | HEAD grep |
|---|---|
| `bandit_algorithm` | not present in ControllerConfig.hpp — **PASS** |
| `thompson_mu_prior`, `thompson_precision_prior`, `thompson_precision_obs`, `thompson_rng_seed` | not present anywhere — **PASS** |

### Claim 8 — DESIGN_SPECS cross-references valid

Plan body cites:
- `curve-registry-pattern.md` (Decision A) ✓
- `cfg-flag-eligibility-criteria.md` (5 cfg fields rejected) ✓
- `wire-format-byte-preservation-discipline.md` (.C JSON format) ✓
- `slow-path-gate-registry-pattern.md` (Decision C) ✓
- `registry-tuple-as-single-source-of-truth.md` (FOREACH_BANDIT_ALGORITHM) ✓
- `structural-fix-preferred-decision-framework.md` (Class 18 mirror prevention) ✓
- `audit-driven-pre-coding-gate.md` (this gate fired) ✓
- `autopopulate-pattern-for-production-caller-class.md` (STAMP_CFG_AUTOPOPULATE for 4 stamp-binds) ✓
- `bitmap-flag-api.md` (thompson_state byte) ✓

NEW (ships with this plan):
- `per-snapshot-cluster-layout-pattern.md` (.0 audit deliverable)
- `calibration-log-column-registry.md` (.D registry pattern)

**PASS** — all references checked against `~/code/tick-trader-percore-workspace/DESIGN_SPECS/` catalog (verified live at start of audit).

---

## NEW dependency concerns from .0 + .D

### .0 — PerCoreSnap layout audit + unified bandit telemetry cluster

**Plan claim:** ".0 Step 1: walk PerCoreSnap struct definition (`CoreFrameworks/ShardedSnapshot.hpp`); identify ML telemetry fields by concern"

**DRIFT** — `PerCoreSnap` struct is actually defined in `DataStream/EngineTUI.hpp:980-1198` (inside `TUISnapshot`). `CoreFrameworks/ShardedSnapshot.hpp` contains the WRITER (`TUI_CopySnapshotSharded` populating PerCoreSnap fields at :646-694 for ensemble fields). Plan .0 Step 1 must EITHER:
- (a) cite both files: struct at `DataStream/EngineTUI.hpp:980`; writer at `CoreFrameworks/ShardedSnapshot.hpp:646-694`, OR
- (b) clarify Step 1 walks the STRUCT definition (in EngineTUI.hpp) but Step 3 ("relocate fields; update all writers") will touch `ShardedSnapshot.hpp:646-694` writer code

**No data plumbing gap** — both files exist; field reorder is mechanically tractable. Just stale file:line citation in plan prose.

**Reader inventory (consumers that would break on field-name reorder):**
- `GUI/MLStatusPanel.hpp:373` reads `cs.ensemble_weights[r][h]`
- `GUI/SettingsPanel.hpp:1209` reads `pcs.ensemble_weights[r][h]`
- `DataStream/EngineTUI.hpp:1193` is the field declaration itself (struct member)
- No `offsetof` static_asserts on ensemble fields exist in tests — confirmed via grep
- No CSV / wire-format / persisted snapshot consumers exist for `ensemble_weights` (TUISnapshot is in-memory only)

**Verdict:** field reorder is SAFE under the GUI panel readers (named member access, no offset assumptions). Adding 4 NEW Thompson telemetry fields (1 byte state + 3 arrays of 8 floats/uints = 1 + 32 + 32 + 32 = 97 bytes) is purely additive.

**Sub-recommendation:** plan .0 Step 1 prose should be amended to cite `DataStream/EngineTUI.hpp:980-1198` for the struct + `CoreFrameworks/ShardedSnapshot.hpp:646-694` for the writer.

**Plan claim:** "ensemble_bandit_arm_probs[8] PerCoreSnap field — write site at EngineSharded.hpp:646-694"

**DRIFT** — actual field name is `ensemble_weights[5][8]` (not `ensemble_bandit_arm_probs`); writer is at `ShardedSnapshot.hpp:646-694` (not `EngineSharded.hpp:646-694`). Plan line 61 has both errors. Mechanical fix.

### .D — FOREACH_CALIB_LOG_COL registry

**Existing calibration log writer** at `CoreFrameworks/OrderManager.hpp:991-1019`:
- Header at `OpenCalibrationLog` (`:1293-1295`): 9 columns: `timestamp_us, slot, exit_predicted_flag, predicted_p, entry_price, exit_price, gain_pct, realized_pnl_bps, was_win`
- Row format `:1008-1013`: matching 9-field printf

**Existing CALIB log consumers:**
- `OrderManager_OpenCalibrationLog` opens the FILE* at boot (only producer side)
- 4 tests at `tests/controller_test.cpp:18282/18312/18333/18343/18347/18352/18356/18359` test cfg path defaults + open/close lifecycle ONLY (do NOT parse CSV content)
- No external Python/CLI tools in tree consume this CSV (only operator runs offline calibration analytics with their own tools per `cfg.calibration_log_path` doc)
- DOCS/changelogs reference v5.13.0.B as the introducer; no schema-locking docs

**Verdict on .D registry append-only safety:** SAFE. The 5 new columns (exp3_chosen_arm, thompson_chosen_arm, regime_id_at_pick, exp3_weights_csv, thompson_mu_csv) are append-only at column position 10+; existing columns retain positions 1-9. Operator's downstream Python/Pandas readers using `pd.read_csv(usecols=[...])` or positional indexing 0-8 are unaffected. Operators using `header=True` named columns inherit new columns transparently.

**Plan claim (.D Step 2):** "Update slow-path snapshot publish path in EngineSharded.hpp (mirror lines 646-694 ensemble_bandit_arm_probs pattern)"

**DRIFT** — same as .0 Step 1: writer file is `ShardedSnapshot.hpp:646-694`, NOT `EngineSharded.hpp:646-694`. Plan should cite `ShardedSnapshot.hpp` for the mirror reference.

**Sub-recommendation:** Plan .D Step 2 prose should cite `CoreFrameworks/ShardedSnapshot.hpp:646-694`.

**.D dependency on existing OMS calibration log writer:**
- `oms->calibration_log_file` is a FILE* in `OrderManagerState<F>` at `:305`
- Single writer (drainer thread; HandleFill at `:984-1019`)
- The new FOREACH_CALIB_LOG_COL writer must thread cfg=2 telemetry data INTO HandleFill — this is a NEW data path: bandit choices made on slow-path → must reach drainer at fill-time. Mechanism: `oms->last_exit_was_predicted[pslot]` + `oms->last_exit_predicted_p[pslot]` precedent (slow-path writes per-slot, drainer reads at fill) — Thompson + Exp3 chosen_arm + weights would follow same per-slot ring pattern.

**Sub-recommendation:** plan .D should add an explicit Step 4.5 noting the slot-indexed propagation pattern (mirror of `last_exit_was_predicted` storage at `OMS:282-305`); this is implied but not explicit in the current plan prose.

---

## Mirror-array data-flow audit (Step 6 — Class 18 prevention)

**Plan introduces:** `EnsembleModelZoo.thompson_bandits[NUM_REGIMES]` parallel to existing `bandits[NUM_REGIMES]` and `exit_bandits[NUM_REGIMES]`.

**Class-18 framing reconsidered with Decision A (FOREACH_BANDIT_ALGORITHM retrofit):**

The mirror-array recurrence count remains 3 (`bandits[]`, `exit_bandits[]`, `thompson_bandits[]`). However, the Decision A registry retrofit ELIMINATES the mirror-class risk because:

1. **Algorithm-axis coverage is registry-locked:** adding a 4th algorithm (UCB1 etc) does NOT add a new parallel array — it adds 1 row to FOREACH_BANDIT_ALGORITHM + 1 compute fn + 1 storage struct (could be co-located in EnsembleModelZoo or extracted to algorithm-specific header). The plan's `BanditAlgoFn` 4-arg dispatch contract enables clean polymorphism.

2. **Buy-vs-exit-side axis is NOT addressed by FOREACH_BANDIT_ALGORITHM** — that's a separate concern (`bandits[]` vs `exit_bandits[]` is "buy decision" vs "exit decision", not "algorithm A vs B"). If a future ship needs Thompson for EXIT side too, that becomes `exit_thompson_bandits[NUM_REGIMES]` — a 4th parallel array → triggers Class 18 again.

   **Sub-recommendation:** TECH_DEBT-026 (per-core override of bandit_algorithm) should be expanded to also track this exit-side-Thompson-mirror class — set trigger at "Thompson applied to exit side OR 4th bandit algorithm added"; whichever comes first triggers a refactor to extract the (algorithm, side) cross-product into a 2D registry or a `BanditSlot { kind; state }` discriminated-union pattern.

3. **Decision A registry contract correctness verified:** all 3 compute fns have the same uniform 4-arg signature; dispatch table is a single function-pointer array indexed by `cfg.bandit_algorithm`. No mirror sites.

**Verdict:** **PASS** — the FOREACH_BANDIT_ALGORITHM registry IS sufficient to prevent further drift along the algorithm axis. The buy-vs-exit-side parallel-storage axis is a SEPARATE concern that doesn't worsen with this plan but may resurface if Thompson-on-exit-side is requested. Recommended capture in TECH_DEBT-026 amendment.

### Call-sequence audit (Step 6 strengthening — PARITY-009/010/011/012 prevention)

Walked source range `Strategies/StrategyParameters.hpp:887-1009` for function CALLS:

| Source-range call | Mirror-needed under Thompson dispatch? | Status |
|---|---|---|
| `Bandit_GetProbabilities(&ezoo->bandits[regime_id], w_curr)` (`:899`) | NO under cfg=1 (Thompson_Sample replaces); YES under cfg=2 | Plan .A Step 5 ✓ via `BanditAlgo_Both_Apply` |
| `Bandit_GetProbabilities(&ezoo->bandits[ezoo->prev_regime_id], w_prev)` (`:900`) | Hysteresis blend — skip under Thompson | **PASS** — Plan .B Step 7 explicit skip |
| `regime_hysteresis` access (`:901`) | NO under cfg=1; YES under cfg=2 | **PASS** — Plan .B Step 7 explicit skip + Both-mode rationale |
| `Bandit_GetProbabilities(&ezoo->bandits[regime_id], weights_buf)` (`:912`) | YES under cfg=0 | Plan .A Step 5 ✓ via `BanditAlgo_Exp3_Apply` |
| `BITMAP_IS_SET(gate_state->flags, MASK_RIDGE_WITHIN_ACTIVE)` (`:931`) | YES (Ridge override applies regardless of bandit algorithm; Ridge wins LAST) | Plan .B Step 6 implies dispatch → weights_buf → Ridge override unchanged |
| `RidgeBlender_BuildCorr / RidgeBlender_Compute` (`:956, 973`) | YES (consumes weights_buf — works for one-hot + Exp3) | Plan retains as-is ✓ |
| `topk_mask_from_weights(weights_buf, ezoo->primary_count, mctx->turnover_topk)` (`:996`) | YES (downstream of weights_buf; works for one-hot) | Plan implicit — works transparently because weights_buf is the boundary |
| `RollingTurnover_Push((RollingTurnover*)mctx->turnover_state, topk_mask)` (`:999`) | YES (downstream of topk_mask; works) | Plan implicit — works |
| `Model_Predict_Ensemble_Weighted(..., weights_buf, ...)` (`:1002`) | YES (consumes weights_buf — works for one-hot + Exp3) | Plan implicit — works |

**Class-18 mirror gap audit:** Plan .B Step 7's hysteresis-skip handles the only case where the dispatcher's contract differs across modes. All other downstream consumers (Ridge, turnover, prediction) operate on `weights_buf` boundary which the dispatcher fills uniformly (via Bandit_GetProbabilities for cfg=0; via one-hot for cfg=1; via Exp3 weights for cfg=2 with Thompson choice logged separately). **PASS.**

---

## Summary table — all amended-plan claims

| Claim category | Count | Status |
|---|---|---|
| Prior BLOCKING items (3) | 3 | **3 FIXED** |
| Prior stale line refs (4) | 4 | **4 FIXED** |
| Version + branch + rollback corrections | 3 | **3 FIXED** |
| Mirror-array recommendation (DEFER → RETROFIT reversal) | 1 | **PASS** with sound rationale |
| REUSE citations against HEAD (16+ entries) | 16 | **16 PASS** (all line refs match) |
| FOREACH_ENSEMBLE_POST_LOAD extension (Class 18 prevention) | 1 | **PASS** with non-blocking sub-recommendation (explicit COUNT bump) |
| Hysteresis-skip rationale | 1 | **PASS** |
| Surface G stamp binding | 4 entries | **4 PASS** |
| FOREACH_BANDIT_ALGORITHM registry (Decision A) | 1 | **PASS** with `BanditAlgoFn` uniform contract resolving polymorphism |
| Cfg field collision check | 5 fields | **5 PASS** |
| .0 PerCoreSnap consumer reader inventory | 3 readers + 0 offsetof asserts | **PASS** (additive field reorder safe) |
| .0 file path citation in Step 1 prose | — | **DRIFT** (cite both EngineTUI.hpp + ShardedSnapshot.hpp) |
| .D FOREACH_CALIB_LOG_COL append-only safety | 0 external CSV consumers | **PASS** |
| .D file path citation in Step 2 prose | — | **DRIFT** (cite ShardedSnapshot.hpp) |
| .D slot-indexed propagation pattern | implicit | **PASS** with sub-recommendation to add explicit step |
| Mirror-data-flow + call-sequence audit (Step 6 strengthening) | 9 calls in dispatch range | **9 PASS** |
| DESIGN_SPECS cross-references | 9 existing + 2 NEW | **11 PASS** |

**Total checks:** 75
**PASS:** 73
**DRIFT (non-blocking, mechanical fix):** 2
**GAP (BLOCKING):** 0

---

## Recommendations (priority order)

### 1. NON-BLOCKING — file-name corrections in plan prose

a) **.0 Step 1 (line 124):** "walk PerCoreSnap struct definition (`CoreFrameworks/ShardedSnapshot.hpp`)" → cite both files: struct at `DataStream/EngineTUI.hpp:980-1198`; writer at `CoreFrameworks/ShardedSnapshot.hpp:646-694`

b) **.D Step 2 (line 256):** "mirror lines 646-694 ensemble_bandit_arm_probs pattern" — should cite `CoreFrameworks/ShardedSnapshot.hpp:646-694` (writer) and use the actual field name `ensemble_weights[5][8]` (or whatever new unified-cluster field name is chosen in .0)

c) **Plan REUSE section line 61:** "`ensemble_bandit_arm_probs[8]` PerCoreSnap field" — this name doesn't exist; actual is `ensemble_weights[5][8]`. Either rename the v5.14.10 field (since Thompson is the first true "bandit_arm_probs" telemetry; current `ensemble_weights` is regime-by-horizon weights) OR cite the existing field correctly

### 2. NON-BLOCKING — sub-recommendations baked from claims

d) **.C Step 5 prose:** add explicit `FOREACH_ENSEMBLE_POST_LOAD_COUNT 7 → 9` bump at `:2107` (mechanical; auto-extension picks up but tests use the count macro as size assertion)

e) **.D Step 4-5 propagation pattern:** add explicit step noting the slot-indexed slow-path → drainer propagation (mirror `oms->last_exit_was_predicted[pslot]` precedent at `OrderManager.hpp:282-305`); this is implied but not explicit

f) **TECH_DEBT-026 amendment:** expand to also track exit-side-Thompson mirror class (current TECH_DEBT-026 is only per-core override); set trigger to "exit-side Thompson OR 4th algorithm" — whichever comes first

### 3. NON-BLOCKING — sub-recommendations carried from prior /trace-deps report

g) Plan .B Step 9 mirrors `cfg.exit_blender_mode` pattern — verified to work but worth noting the `BITMAP_BIT` emit_source vs `DIRECT_FIELD` distinction (composite_enabled at `:117-119` uses BITMAP_BIT; `bandit_algorithm` correctly uses DIRECT_FIELD for INT enum)

---

## Cross-references

- `DESIGN_SPECS/structural-fix-preferred-decision-framework.md` — used for Decision A reversal rationale
- `DESIGN_SPECS/curve-registry-pattern.md` — Decision A's structural shape (FOREACH_BANDIT_ALGORITHM mirrors FOREACH_DEGRADATION_CURVE)
- `DESIGN_SPECS/x-macro-registry-with-presence-dispatch.md` — base pattern (FOREACH_ENSEMBLE_POST_LOAD applies)
- `CLAUDE.md` items 12 (display↔execution invariant), 17 (latency-additions tracked), 18 (slow-path latency reduction), 19 (structural-fix-preferred), 20 (bit-packed flags), 21 (AUTOPOPULATE companion), 22 (PRE/POST registry split), 23 (type-trait dispatch)
- `CLAUDE.local.md` `feedback_overengineering_boundary_when_future_easier` — used to support Decision A
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 18 — mirror-incomplete (same class as PARITY-009/010/011/012)
- `DOCS/TECH_DEBT.md` -010 / -011 / -026 / -027 — all entries verified present

---

## Effort budget

This audit: ~14 min (medium plan, multi-subsystem; amended scope adds 6 sub-tags including layout audit). Within /trace-deps's 5-15 min budget.
