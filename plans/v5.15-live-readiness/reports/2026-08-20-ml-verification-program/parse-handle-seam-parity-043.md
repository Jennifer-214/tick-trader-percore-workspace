# PARITY-043 surface map — the missing stamp-parse→ModelHandle population leg (".B.3 parse→handle leg")

> Saved verbatim at receipt 2026-08-20 (orchestrator write per `feedback_save_agent_reports_verbatim`).

**Repo:** `/home/caramel/code/FoxML_Trader_v2` @ HEAD 417e524, branch `feat/v5.15-live-readiness`. I-class investigative report; skill methodology: `/dependency-chain-trace` (`.claude/skills/dependency-chain-trace/SKILL.md` — symbol resolved → write sites → read sites → flow → cohort → blast radius). **Search roots covered in every membership claim:** `CoreFrameworks/ Strategies/ ML_Headers/ MemHeaders/ DataStream/ FixedPoint/ Backtest/ GUI/ tests/ tools/` (named explicitly per Landmine 19; positive controls run on each empty-returning probe). Mechanical tool run: `python3 tools/check_struct_field_uniqueness.py` → PASS (3 collisions = 3 sidecar entries).

## Executive summary

The cfg-derived cohort has a **4-of-5 walker family**: parse (stamp→`sr`), emit (cfg→stamp), inf-populate (cfg→`inf`), drift (compare) all exist in `namespace cfg_derived` (`MemHeaders/CfgGateRegistry.hpp:341-694`). The **fifth leg — copy `sr`→`handle` for the derived cohort — does not exist anywhere** (meta-walker consumer enumeration: exactly 4 template fns + 1 struct-gen macro, `MemHeaders/CfgGateRegistry.hpp:395,481,596,679,778`; no copy walker). The hand-written copy block in `NodeModelZoo.hpp` covers only MODEL_CONST-registry groups. Result: all 36 cohort fields are declared on `ModelHandle` (auto-gen at `ML_Headers/ModelInference.hpp:444`) and 12 of them are **read** by `FOREACH_CFG_DRIFT_CHECK` rows as `h-><name>`, but **33 of 36 are written by nothing, ever** (3 are written only for legacy pre-.B.3 stamps). With `bandit_enabled` now defaulting ON (`CoreFrameworks/ControllerConfig.hpp:2012`), the Thompson precision rows compare a never-written 0 against cfg default 1.0 and fire **spurious Tier-1 REFUSE_STRICT drift on every model load in a default cfg**. The data IS present in the stamp (unprefixed keys, emitted from live cfg) and IS parsed into `sr` — it is only never copied to the handle, so **the fix is parse-side-only (a load-time copy walker), no wire change**.

---

## Q1. Parse side: `sr` struct + the hand-written sr→handle copy block

**The "StampRecord" is `ModelStampResult`** — `ML_Headers/ModelInference.hpp:1417-1500`. Its cfg-derived fields are NOT hand-declared: `STAMP_RESULT_DERIVED_FIELDS_AUTO_GEN()` at `ModelInference.hpp:1484` expands `uint8_t has_<name>; STORAGE_T <name>;` per row **unconditionally over all 4 master cfg registries** (~163 fields; macro defined `MemHeaders/CfgGateRegistry.hpp:777-778`, per-scope helpers `:763-770`), with a 3-name `xgb_*` exclusion redirect (`ModelInference.hpp:1481-1487`; sidecar `MemHeaders/CfgGateRegistry.hpp:748-751`). Runtime-only fields + `uint64_t has_flags` (group bits) at `:1424-1455`. `sr` is instantiated at `ML_Headers/NodeModelZoo.hpp:265` (`ModelStampResult sr = {};`, `have_sr` `:266/275`) inside `NodeModelZoo_TryLoadRole` (`:189`).

**Parse population** (verify_model_stamp key loop): PRE_CFG MODEL_CONST walker `ModelInference.hpp:1734-1740` → **derived-cohort dispatch `PARSE_STAMP_CFG_TO_DERIVED(r, key, val)` at `:1749`** (template fn `cfg_derived::parse_stamp_cfg_to_derived`, `MemHeaders/CfgGateRegistry.hpp:637-687` — sets `r.<name>` + `r.has_<name>=1` per matched unprefixed key) → POST_CFG walker `:1760-1766`.

**The hand-written copy block:** `ML_Headers/NodeModelZoo.hpp:363-522` (`if (have_sr) {` at `:363`; copies at `:376-501`; horizon-refusal `:502-521` closes it). Its own header comment (`:369-375`) names the never-built companion `STAMP_HANDLE_COPY_FROM_RESULT`. **Exactly 12 STAMP_SET calls** (14 grep matches − 2 comment lines `:365,:372`):

| # | Line | Name | Kind | Order |
|---|---|---|---|---|
| 1 | :378 | `training_poll_interval` | member (single field) | **value-before-bit** (value `:377`) — the only one |
| 2 | :384 | `xgb_hyperparams` | GROUP bit (9 fields `:385-395`) | bit-before-value |
| 3 | :399 | `build_flags_hash` | member | bit-before-value (value `:400`) |
| 4 | :404 | `xgb_train_nthread` | member | bit-before-value (value `:405`) |
| 5 | :410 | `label_params` | GROUP bit (3 fields `:411-413`) | bit-before-value |
| 6 | :418 | `scaler` | GROUP-semantics bit whose NAME collides with member `tt::FeatureStandardizer scaler` (`ModelInference.hpp:417`) | bit-before-value (`scaler_sha256` copy `:419-422`) |
| 7 | :429 | `overlay_hash` | member (char[]) | bit-before-value (`:430-433`) |
| 8 | :436 | `effective_hash` | member (char[]) | bit-before-value (`:437-440`) |
| 9 | :445 | `training_timestamp_us` | member | bit-before-value (`:446`) |
| 10 | :449 | `run_name` | member (char[]) | bit-before-value (`:450-452`) |
| 11 | :459 | `inference_cfg` | GROUP bit (3 field copies `:460-465`) | bit-before-value |
| 12 | :480 | `model_num_outputs` | member | bit-before-value (`:481`) |

D-426 tombstone comments in the block: `inference_cfg_bandit_blend_ratio` copy removed (`:469-475`), `fees` copy removed (`:476-478`). **Every copy in this block targets a MODEL_CONST-registry name or (for the 3 `inference_cfg` fields) a derived auto-gen field — none of the other 33 derived-cohort fields appear.**

## Q2. The STAMP_BOUND_CFG_DERIVED cohort — measured, not carried

Grep-derived counts (uncapped, literal `STAMP_BOUND_CFG_DERIVED`): `CoreFrameworks/CfgFieldRegistry.hpp` = 41 matches, of which **30 are field rows** (11 are the bit def `:174`, comments `:159,:168,:475`, derived-filter row `:1447`, CI Check 9 block `:1476-1500`, render mask `:1561`). `ML_Headers/MlCfgFlagRegistry.hpp` = 7 matches → **5 rows** (2 comments `:54,:177`). Plus the 4th registry the mission didn't name: `CoreFrameworks/GateCfgFlagRegistry.hpp:45` → **1 row**. **Total cohort = 36.**

- **GLOBAL (3)** (registry `:336`): `trading_mode` :469 · `gap_acceptable_threshold` :478 · `held_out_fraction` :488
- **PER_NODE (27)** (registry `:581`): `ml_buy_threshold` :665 · `ml_tp_pct` :666 · `ml_sl_pct` :667 · `bandit_blend_ratio` :675 · `confidence_threshold_scale` :676 · `ridge_lambda` :704 · `ridge_cost_penalty` :707 · `ridge_min_ic_floor` :710 · `winsor_pct_low` :714 · `winsor_pct_high` :717 · `confidence_freshness_tau_secs` :721 · `confidence_capacity_target_dollars` :724 · `confidence_capacity_kappa` :727 · `confidence_rmse_baseline` :730 · `thompson_mu_prior` :734 · `thompson_precision_prior` :737 · `thompson_precision_obs` :740 · `bandit_algorithm` :744 · `thompson_exp3_blend_alpha` :748 · `risk_degradation_curve` :753 · `risk_full_size_threshold` :756 · `risk_min_size_threshold` :759 · `risk_min_size_pct` :762 · `confidence_hard_block_threshold` :780 · `barrier_blend_mode` :782 · `fee_rate_maker` :794 · `fee_rate_taker` :795
- **ML_CFG_FLAG (5)** (`MlCfgFlagRegistry.hpp`): `confidence_composite_enabled` :66 · `ridge_within_horizon` :72 · `ridge_across_horizons` :73 · `exit_blender_mode` :74 · `per_horizon_barrier_blend` :76
- **GATE_CFG_FLAG (1)**: `barrier_gate_enabled` (`GateCfgFlagRegistry.hpp:45`)

**ModelHandle-side declarations:** ALL 36 have handle members — `STAMP_RESULT_DERIVED_FIELDS_AUTO_GEN()` at `ModelInference.hpp:444` (added ".B.3 Phase F HIGH-1 (b)", comment `:430-439`) generates `uint8_t has_<name>; STORAGE_T <name>;` for every row of all 4 registries on `ModelHandle` (struct `:342-452`), same as on `sr` and on `StampInferenceCfgInputs` (`:2087`).

**Populated today on the handle:** exactly **3 of 36** — `confidence_threshold_scale`, `barrier_gate_enabled`, `confidence_hard_block_threshold`, via the block's `inference_cfg` section (`NodeModelZoo.hpp:458-468`) — and **only when `STAMP_HAS(sr, inference_cfg)`**, a group bit that (see Q4) production emit no longer produces, so **only for legacy pre-.B.3 stamps**. The other **33 fields plus all 36 per-field `handle.has_<name>` flags are written by nothing** (only zeroed by `Model_Init` brace-init, `ModelInference.hpp:527-531`). The literal `has_thompson_precision_prior`/`has_ml_tp_pct`/`has_barrier_blend_mode` has ZERO non-macro occurrences across all 10 roots (expected — the token exists only via `has_##name` paste; positive control `Model_Load` = 5 hits).

## Q3. Every reader of the five fields on the HANDLE side (AR-19)

Full-root greps (uncapped; hits: thompson_precision_prior 24, thompson_precision_obs 24, ml_tp_pct 31, ml_sl_pct 27, barrier_blend_mode 32) — every hit classified. All non-drift hits are **cfg-side** (storage/defaults/parser `ControllerConfig.hpp:889-890,1348-1349,2081-2082,2200-2201,2268,2740-2748,2835-2836,3105-3106`; serving reads `node_cfg->ml_tp_pct`/`ml_sl_pct`/`barrier_blend_mode` at `Strategies/StrategyParameters.hpp:1645,1661-1662` — the resolved per-node CFG, not the handle; Thompson init reads `cfg.thompson_precision_*` `NodeModelZoo.hpp:3402-3414`; GUI descriptor rows, registry rows, ledger). Tests write only the **prefixed** twins (`h.inference_cfg_ml_tp_pct` etc., `tests/controller_test.cpp:28236-28245`).

**The ONLY handle-side (`h->`) readers are the five FOREACH_CFG_DRIFT_CHECK rows**, macro-expanded in exactly one consumer, `NodeModelZoo_ValidateAgainstCfg` (`CoreFrameworks/ModelValidation.hpp:148-277`; expansion `:222`; per-entry composition `:199-218`: `if ((gate_when) && !acked) { read h-> ; compare ; BITMAP_SET(h->drift_flags_at_load) ; tier counters }`). Confirmed no other macro consumer can read them: the cohort meta-walker `FOREACH_STAMP_BOUND_DERIVED_COHORT` has exactly 5 expansion sites, all in `CfgGateRegistry.hpp` (4 walkers + struct-gen).

| Field | Row | Severity | Compare | gate_when | Gate kind | Reachable? | Fires at default cfg? |
|---|---|---|---|---|---|---|---|
| `thompson_precision_prior` | `ML_Headers/CfgDriftCheckRegistry.hpp:282-285` | REFUSE_STRICT | EPS_DEFAULT | `COHORT_GATE_BANDIT_ENABLED` | **cfg-only** (`MlCfgFlagRegistry.hpp:143`) | YES — `bandit_enabled` defaults ON (`ControllerConfig.hpp:2012`) | **YES**: h=0 vs cfg 1.0 (`:2200`) → Tier-1 drift every load |
| `thompson_precision_obs` | `:286-289` | REFUSE_STRICT | EPS_DEFAULT | same | cfg-only | YES | **YES**: 0 vs 1.0 (`:2201`) |
| `ml_tp_pct` | `:318-321` | REFUSE_STRICT | EPS_DEFAULT | `COHORT_GATE_PER_HORIZON_BARRIER` (`MlCfgFlagRegistry.hpp:134`) | cfg-only | when operator enables per-horizon barrier | then YES: 0 vs 0.015 (`:2081`) |
| `ml_sl_pct` | `:322-325` | REFUSE_STRICT | EPS_DEFAULT | same | cfg-only | same | then YES: 0 vs 0.008 (`:2082`) |
| `barrier_blend_mode` | `:326-329` | REFUSE_STRICT | EXACT | same | cfg-only | same | 0 vs 0 no; fires the moment mode≠LEGACY set |

**STAMP_HAS was intentionally dropped from these gates** — registry comment `CfgDriftCheckRegistry.hpp:273`: drift is supposed to fire when the cfg cohort is on even if the stamp lacks the field ("trained without feature, now using feature"). Honor that decision (settled fork); the fix must make `h->` truthful, not re-gate the rows.

**Sibling unwritten-and-read rows at the same surface** (widens PARITY-043 beyond the named five): `bandit_blend_ratio` `:268-271` (WARN, BANDIT_ENABLED gate — **fires at default**: 0 vs 0.30, `ControllerConfig.hpp:2106`) · `bandit_algorithm` `:274-277` (WARN) · `thompson_mu_prior` `:278-281` (REFUSE_STRICT — silent at default only because cfg default is 0.0, `:2199`) · `thompson_exp3_blend_alpha` `:290-293` (REFUSE_STRICT, gate `bandit_algorithm==4`) · `fee_rate_maker`/`fee_rate_taker` `:294-301` (WARN, COST_GATE) · `per_horizon_barrier_blend` `:330-333` (REFUSE_STRICT, gated `STAMP_HAS(*h, inference_cfg)` → dead for new stamps, live-and-wrong for legacy stamps with the feature on).

**Walker callers (all 4):** boot funnel `CoreFrameworks/EngineCommon.hpp:416` (step 5g; **return code ignored** — comment `:410-411` "FATAL log fires on REFUSE in strict mode; engine continues (TODO v5.10: free + refuse)"; serves LIVE and BACKTEST per PARITY-012, `Backtest/BacktestSharded.hpp:40`), ensemble hot-swap `CoreFrameworks/EngineSharded/Run.hpp:1915` (rc<0 → MODEL_LOAD_FAILED), second hot-swap site `:1980`. `strict` = `cfg.held_out_gate_strict`, registry default 0 (`ControllerConfig.hpp:2121`), so default-cfg damage = spurious WARN logs + tier counters + `drift_flags_at_load` bit + `CFG_DRIFT_STRICT_REFUSED` machinery (`ModelValidation.hpp:255-275`); strict=1 operators get hot-swap refusal and boot FATAL logs.

## Q4. Emit side — the data IS in the stamp; the fix is parse-side-only

Producer chain: `Stamp_AssembleAndEmit` (`ML_Headers/StampHelper.hpp:178+`) → `INFERENCE_CFG_POPULATE_FROM_DERIVED(inf, cfg)` `:198` → `stamp_write_for_model` (`ModelInference.hpp`, ends `:2394`) which emits PRE_CFG MODEL_CONST rows `:2298-2304`, then **`cfg_derived::populate_stamp_cfg_from_derived<F>(canonical+n, …, *cfg_ptr)` at `:2320-2324`** — reads **live cfg** per row (`CfgGateRegistry.hpp:425-489`) gated by `cfg_gate::lookup_populate` (`:157-176`, default **always-emit**; sidecar `FOREACH_CFG_GATE_PER_NODE` `:87-111` = 16 cohort-gated entries), then POST_CFG `:2331-2337`, then HMAC + atomic rename `:2351-2391`.

Per-field verdict for the five: `ml_tp_pct`, `ml_sl_pct`, `barrier_blend_mode` have **no gate sidecar entry → always emitted** in every post-.B.3 stamp. `thompson_precision_prior`/`_obs` gated `COHORT_GATE_BANDIT_THOMPSON` = `cfg.bandit_algorithm != 0` (`CfgGateRegistry.hpp:94-95`, `MlCfgFlagRegistry.hpp:129`) → present when the trainer cfg ran a Thompson-class bandit. Parse lands each into `sr.<name>` + `sr.has_<name>` (Q1). **So: value present in the file, parsed into `sr`, never copied to the handle. Parse-side-only fix confirmed.**

**Adjacent finding (changes reachability, not the fix):** production emit **never sets the `inference_cfg` group bit** — tree-wide, the only `STAMP_SET(…, inference_cfg)` writers are the parser dispatch macro (`StampBoundModelConstRegistry.hpp:947`, fires only on the 9 legacy **prefixed** keys `:593-622`) and one hand-set test (`tests/controller_test.cpp:15583`). `StampHelper` sets only `xgb_hyperparams`/`label_params`/`grid_member`/`scaler` (`:339,378,388,394`). Consequences: (a) the 9 prefixed `inference_cfg_*` POST_CFG rows never emit (emit gate `STAMP_EMIT_CHECK_HAS_inference_cfg` = `STAMP_HAS(*inf, inference_cfg)`, `:931`) — dead registry rows still holding H21 wire-key slots (`tools/identifier_ledger.txt:89-91`); (b) new stamps parse with `STAMP_HAS(sr, inference_cfg)=0`, so the block's 3-field copy never runs and **the sr-side `DRIFT_CHECK_FROM_DERIVED` at `NodeModelZoo.hpp:294-308` is fully vacuous for post-.B.3 stamps** (`lookup_drift` default AND sidecar both require `stamp_has_inference_cfg`, `CfgGateRegistry.hpp:187-199`; ML/GATE-flag walkers likewise `:568,:588`).

## Q5. D-426 guard residual — extending the opt-in to ModelHandle

Mechanism (all in `ML_Headers/StampBoundModelConstRegistry.hpp`): trait primary `tt::is_stamp_emit_inputs_v = false` `:197-198`; sole specialization `StampInferenceCfgInputs` at `ModelInference.hpp:2160-2163`; guard `STAMP_SET` `:816-825` (`static_assert(!is_stamp_emit_inputs_v<decay_t<decltype(s)>> || !TT_HAS_MEMBER(s, name))`); `STAMP_PUT` `:776-780` (value first via `tt::stamp_put_field` `:164-175` — **handles char arrays**: bounded strnlen+memcpy+NUL, byte-identical to the hand-written copies; then bit); `TT_HAS_MEMBER` `:236-237` over `tt::is_valid` `:224-230` (C++17 detection idiom). The guard's own scope comment `:782-798` names this exact surface: the handle side "is unguarded because it is not opted in, NOT because it is safe; extending the opt-in there is tracked follow-up. Site #4 of the D-426 pattern lived there."

**What the extension requires:**
1. A partial specialization over the template param: `template <unsigned F> inline constexpr bool tt::is_stamp_emit_inputs_v<ModelHandle<F>> = true;` placed after the struct (sister to `ModelInference.hpp:2160-2163`; legal C++14+ variable-template partial specialization).
2. Convert the 8 single-field member-named STAMP_SETs in the block to STAMP_PUT — **mechanical**, with one semantic care point: the char-array entries (`overlay_hash` :428-434, `effective_hash` :435-441, `run_name` :448-453) keep their outer `sr.X[0] != '\0'` condition (STAMP_PUT would otherwise set the bit on an empty copy).
3. The 3 true group bits (`xgb_hyperparams` :384, `label_params` :410, `inference_cfg` :459) stay STAMP_SET — legal under the guard (no member of that name).
4. **The non-mechanical wrinkle: `scaler` (:418).** On ModelHandle the bit name collides with a real member (`tt::FeatureStandardizer scaler`, `ModelInference.hpp:417`), so `TT_HAS_MEMBER(*handle, scaler)` = true and the group-semantics `STAMP_SET(*handle, scaler)` becomes a **false-positive compile error**. Resolution options for the plan: rename the bit (internal-only mask name — not a wire identifier, H21-safe; verify), or an explicit group-bit escape macro (`STAMP_SET_GROUP`), or STAMP_PUT-ing `scaler_sha256` and hand-setting the bit differently. This is the one design decision in the residual.
5. Test sweep: `tests/controller_test.cpp:27966-27967` (`STAMP_SET(h, training_poll_interval)` / `(h, run_name)`) become compile errors → convert; `:27965` (group bit) survives; audit the other handle-touching among the 36 test STAMP_SETs.

**Verdict: mechanical except item 4** (plus item 2's empty-string care point).

## Q6. Recommended fix shape + ordering

**Primary (closes PARITY-043): add the missing 5th walker to the existing family.** A `cfg_derived::copy_stamp_result_to_handle<F, ResultT, HandleT>(HandleT& h, const ResultT& r)` (+ thin `COPY_RESULT_TO_HANDLE_FROM_DERIVED(handle, sr)` wrapper, matching `:795-820` house style) in `MemHeaders/CfgGateRegistry.hpp`, expanding `FOREACH_STAMP_BOUND_DERIVED_COHORT(X_COPY)` with per-scope bodies filtered `if constexpr (meta & STAMP_BOUND_CFG_DERIVED)` and per-field Surface-G gating:

- PER_NODE/GLOBAL: `if (r.has_<name>) { h.<name> = r.<name>; h.has_<name> = 1; }`
- ML/GATE flag scopes: same with `legacy_field`.

**Populate-then-bit discipline is satisfied by construction** — value and presence are emitted by the same X-macro body, the same structural pairing that makes the parse side "safe-by-shape" (`StampBoundModelConstRegistry.hpp:182-183`). Note the derived cohort's presence flags are the per-field `uint8_t has_<name>` (Surface G), NOT `has_flags` bits — STAMP_PUT/STAMP_SET are the wrong primitive here, and no `MASK_<name>` exists for these names.

**Call site:** inside the existing `if (have_sr)` block in `NodeModelZoo_TryLoadRole` — recommended immediately after the MODEL_CONST copies (`NodeModelZoo.hpp:~501`, before the horizon-refusal at `:502`), i.e. after `Model_Load` success (`:356-357`) so a refused load never carries copied state. Ordering within the block is not concurrency-sensitive (boot/hot-swap thread-local handle, pre-publish), but copy-after-load-success is the correctness-clean point. One chokepoint covers boot + hot-swap + backtest (ensemble loads route `EnsembleModelZoo_LoadFromCfg → NodeModelZoo_TryLoadRole` per `NodeModelZoo.hpp:2415-2418`; verify in plan).

**What makes the drift rows compare true values:** exactly this copy. When the stamp carried the key, `h-><name>` = training-time value → drift compares truth. When the trainer's cohort was off (key absent), `h->` stays 0 with `has_=0` → the cfg-cohort-on gate still fires drift, which is the **intended** "trained-without-feature" catch per `CfgDriftCheckRegistry.hpp:273` — do not re-gate the rows.

**Secondary, separable (the Q5 residual):** opt ModelHandle into the guard + STAMP_PUT-convert the block (items 1-5 above). Order it AFTER the copy walker lands (the walker removes zero pressure from the block; the block conversion doesn't touch the walker).

**Novel alternative considered** (4-pillar; `feedback_proactive_novel_alternative_consideration`):

| Option | Shape | Verdict |
|---|---|---|
| A (recommended) | 5th cfg_derived walker, sr→handle, per-field Surface-G gate | Completes the registry family the codebase already committed to (Class 14/18/21 closure pattern, `CfgGateRegistry.hpp:700-717`); future cohort rows auto-flow |
| B | Re-point the 12 drift rows' `get_stamp_expr` at a retained `sr` instead of the handle | REJECTED: `sr` is a local of `TryLoadRole` (`NodeModelZoo.hpp:265`); ValidateAgainstCfg runs later per-handle at boot/hot-swap (`ModelValidation.hpp:168`); retaining = +5,248B/handle (`ModelInference.hpp:1520`) or re-parse-per-validate; contradicts the handle-is-runtime-SSoT design (`ModelInference.hpp:434`) |
| C | Move the 12 rows into the sr-side `DRIFT_CHECK_FROM_DERIVED` and delete them from FOREACH_CFG_DRIFT_CHECK | REJECTED-leaning: loses per-role/per-ensemble-member granularity, tier counters, ack-flag + display-meta writeback (`ModelValidation.hpp:194-197,255-265`); and the sr-side check is currently group-bit-vacuous — building on it inherits that defect |
| D (novel) | The registry-comment's own `STAMP_HANDLE_COPY_FROM_RESULT` companion (`NodeModelZoo.hpp:369-375`) walking FOREACH_STAMP_BOUND_MODEL_CONST | Complementary, NOT a substitute: covers the MODEL_CONST half (replaces the hand-written block), not the derived half. Clean follow-up that would also dissolve most of Q5's conversion |

## Surfaces that must change (fix plan checklist)

1. `MemHeaders/CfgGateRegistry.hpp` — new walker + wrapper (+ `[FUNCTION]` tag block; file overview `:11-16` list).
2. `ML_Headers/NodeModelZoo.hpp` — one call inside the `:363` block (~`:501`); update the false "FUTURE OPPORTUNITY"-adjacent state if the plan also does Option D.
3. `ML_Headers/ModelInference.hpp:433-436` — **FALSE comment fix**: "NodeModelZoo load-time copy… flows sr → handle" describes a copy that does not exist for the derived cohort (this comment is plausibly why the leg was never noticed — same failure mode as SUBAGENT_ARMING §2.5's SlowPathGateRegistry canonical).
4. `tests/` — walker unit tests (parse→copy→drift round-trip; the existing hand-set-group-bit test at `controller_test.cpp:15567-15583` is the template for the legacy path).
5. If Q5 residual is in scope: `ModelInference.hpp` (trait specialization), `NodeModelZoo.hpp:376-501` (conversion), `StampBoundModelConstRegistry.hpp` scaler-collision resolution, `tests/controller_test.cpp:27965-27972`.
6. Stale-comment sweep (same commit as the fix, per M8/§2.5): `ControllerConfig.hpp:2000` ("all 7 flags off" — false since `:2012` flipped bandit to 1) · `CfgDriftCheckRegistry.hpp:302-317` (describes superseded STAMP_HAS gating; actual gates substituted at Step 6.10 per `:273`) · `CfgFieldRegistry.hpp:783` ("legacy inference_cfg_barrier_blend_mode wire key deleted at Step 2" vs the live row at `StampBoundModelConstRegistry.hpp:599`).

## Risks / unknowns

- **Dead prefixed rows (H21):** the 9 `inference_cfg_*` POST_CFG rows (`StampBoundModelConstRegistry.hpp:593-622`) never emit and their `sr` fields are only populated from legacy stamps. Whether to tombstone them (and the group bit's emit-side death) is a plan decision — Knight-Capital discipline says tombstone, never reuse; they're in the identifier ledger (`tools/identifier_ledger.txt:89-91`).
- **Per-node resolution (H22):** the drift rows compare `cfg.<name>` (flat global) and the cohort gates read `cfg.ml_cfg_flags` (global), while per-node overrides exist (`ControllerConfig.hpp:114-115,180-183,1815`). A node with `node_N_ml_tp_pct` overridden validates against the global value — pre-existing A1-adjacent scent, not introduced by this fix, but the plan should name it.
- **Legacy-stamp path:** for pre-.B.3 stamps, the copy walker adds values the 3-field hand copy already provided plus 30 more; interaction with the legacy prefixed parse (both `sr.inference_cfg_ml_tp_pct` and `sr.ml_tp_pct` may be populated on a transition-era stamp that carried both key families) is benign for the walker (it copies unprefixed only) but worth a test.
- **Boot rc ignored:** even with truthful values, strict-mode boot refusal is log-only (`EngineCommon.hpp:410-416` TODO) — the fix makes the SIGNAL truthful; the enforcement gap is separate, tracked in-code.

## Spots most worth an adversarial refute (for the paired a-class)

1. **"Production never sets the `inference_cfg` group bit at emit"** — rests on the tree-wide STAMP_SET enumeration + `STAMP_EMIT_CHECK_HAS_inference_cfg` (`:931`). Refute by finding a raw `BITMAP_SET(inf.has_flags, MASK_inference_cfg)` bypass, or a live production caller of the "quarantined" `STAMP_MODEL_CONST_AUTOPOPULATE` (whose dispatcher `:917` would set it). I verified quarantine only via the section header `:831` and StampHelper's manual PUTs.
2. **"The five fields' only handle-side readers are the drift rows"** — macro-mediated readers evade literal greps; I closed it via the meta-walker consumer enumeration (5 sites) + FOREACH_CFG_DRIFT_CHECK's single consumer (`ModelValidation.hpp:222`). Refute by finding another expander of either registry or a `memcpy`/whole-struct consumer of ModelHandle's cold cluster (GUI snapshot publisher?).
3. **"Fires at default cfg"** — depends on `bandit_enabled=1` default (`:2012`) reaching the resolved cfg the boot caller passes, and on `EPS_DEFAULT` = 1e-6 semantics (`CfgDriftCheckRegistry.hpp:106`). A backtest-path counter-check (does `config_used` carry the same default?) would confirm or scope it.
4. **Chokepoint completeness** — my claim that all model loads (boot, both hot-swap sites, backtest, ensemble members) route through `NodeModelZoo_TryLoadRole`'s `have_sr` block. `Model_LoadAOT` (`ModelInference.hpp:836`) and any direct `Model_Load` caller bypassing TryLoadRole would dodge the new copy.
5. **The scaler-collision resolution** in Q5 — an a-class should pressure-test whether renaming an internal mask constant is genuinely H21-safe (it is not persisted/wire-emitted as a NAME, but the golden ledger tool `tools/check_identifier_retirement.py` should be run against the change).
6. **Option C dismissal** — I leaned on granularity/writeback arguments from one read of ModelValidation; if the sr-side check were instead FIXED (group-bit vacuity resolved), C shrinks the surface by one whole walker family and deserves a fair re-hearing.
