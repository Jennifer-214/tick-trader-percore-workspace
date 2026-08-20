# PARITY-044 SERVE-half map + side-marker guard shape — i-class report

> Saved verbatim at receipt 2026-08-20 (orchestrator write per `feedback_save_agent_reports_verbatim`).
> Agent: i-class "Map serve-side exit load, side-key guard" · engine HEAD `417e524`.

**Ground:** engine HEAD `417e524` (`feat/v5.15-live-readiness`), verified via `git rev-parse`. Roots covered in every membership probe (named explicitly per Landmine 19): `CoreFrameworks/ ML_Headers/ Strategies/ Backtest/ GUI/ DataStream/ MemHeaders/ FixedPoint/ tests/ tools/`. Tools run: `tools/check_identifier_retirement.py` → **GREEN, 93 identifiers** (baseline before any stamp-key add). Methodology: `/dependency-chain-trace` checklist (definition site → write sites → read sites → flow graph → cohort siblings → blast radius) walked per symbol. PARITY-044 entry read first (workspace `DOCS/PARITY_ISSUES.md:1675-1699`); all four of its measured facts re-verified true at HEAD.

---

## Q1 — Exit-slot load mechanics: NodeModelZoo_TryLoadRole end-to-end for role "exit"

**Call sequence** (all `ML_Headers/NodeModelZoo.hpp` unless noted):

1. **Entry**: `EnsembleModelZoo_LoadFromCfg` (`:2101`) loops horizons; per `<base>_horizon_<H>` dir tries roles in fixed order barrier (`:2127`) → regime (`:2138`) → **exit → `&ezoo->exit_predictor[exit_predictor_count]`** (`:2148-2157`) → buy_signal (`:2158`), each with `expected_horizon_ticks=H` threaded (`:2154`) and `expected_feature_mask=0` (`:2153` — mask check skipped on the ensemble path).
2. **File probe**: `<dir>/exit.json` then `<dir>/exit.xgb` (`:233-244`); `.txt` only for LightGBM (`:247-252`); absent file = silent 0 (`:254`).
3. **Stamp verify**: `verify_model_stamp` (`:268-274`; fn at `ML_Headers/ModelInference.hpp:1594`) unless `held_out_gate_strict == -1`; passes `MODEL_FORMAT_VERSION`, `FEATURE_REGISTRY_HASH()`, `LABEL_REGISTRY_HASH()`, mask. Drift walk `DRIFT_CHECK_FROM_DERIVED` when `cfg_ptr` non-null (`:294-308`) — **but both ensemble callers pass no `cfg_ptr`** (`:2148-2156` — 8 args, `cfg_ptr` defaults nullptr at `:227`), so the cfg drift walk never runs for ensemble-loaded exit models. `sr.valid<=0`: strict=1 → REFUSE (`:310-315`); strict=0 → WARN + load (`:317-320`).
4. **sr→handle copies** (`:363-522`): label_params (`:409-414`), scaler_sha256 (`:417-423`), model_num_outputs claim-vs-seen refuse-in-strict (`:479-500`), etc.
5. **Horizon-mismatch refusal** (`:511-521`): `stamp.label_lookahead_ticks != H` → **ALWAYS refuses** (no strict gating), skipped only for stamps without `label_params`.
6. **Scaler sidecar 3-tier** (`:530-575`): gated on `sr.feature_scaler_present`; SHA-256 vs stamp (`:536-538`) → parse (`:541`) → registry-hash/num_features vs build (`:544-545`); strict=1 refuse (`:553-559`), strict=0 warn + `handle->scaler_load_failed=1` + identity (`:562-567`).
7. **Drift chokepoint** (`:591-634`): arch-field drift bits, `FAILURE_MASK_stamp_hmac_not_verified` when secret empty (`:612-614`), model-age bit (`:621-633` — needs `cfg_ptr`, so also dead on the ensemble path).
8. **Post-load in LoadFromCfg**: exit `buy_class_idx` aliasing (`:2252-2255`), sibling-scaler WARN includes role "exit" (`:2274-2300`, exit at `:2299`), summary log (`:2259-2265`).
9. **Grid-member consistency** (AutoDetect only): `EnsembleZoo_VerifyGridMemberConsistency` (`:2389-2456`) walks exit_predictor as role 3 (`:2405`); a **mismatched** `grid_member_count` on any exit handle **unwinds the ENTIRE ensemble** (`:2565-2568`); a missing one is legacy-WARN (`:2425-2427`).

**`buy_class_idx = (num_outputs>=2) ? 1 : 0` semantics (`:2252-2255`), confirmed:**

- `num_outputs` is probed at `Model_Load` by a zero-row predict (`ModelInference.hpp:643-655`): binary `binary:logistic` → out_len **1**; `multi:softprob` → out_len = num_class.
- Trainer objective from `FOREACH_TARGET.num_classes` (`Backtest/BacktestPanels.hpp:3764-3791`): **WILL_PEAK has num_classes=0 → `binary:logistic`** (`Backtest/LabelFunctions.hpp:88`, `BacktestPanels.hpp:3791`).
- So a **WILL_PEAK binary exit.json → num_outputs=1 → buy_class_idx=0 → `Model_Predict` returns `out_result[0]`** (`ModelInference.hpp:933-935`), which for binary:logistic **is P(y=1) = P(peak within N ticks)** (`LabelFunctions.hpp:262` — "1 if price reaches a local max within N ticks"). **Correct.**
- 3-class PEAK_VALLEY_STABLE exit model → num_outputs=3 → idx 1 = P(peak) per "0=stable, 1=peak, 2=valley" (`LabelFunctions.hpp:90`). **Correct.**
- `Model_Predict_Normalized` (`ModelInference.hpp:710-739`) is a passthrough here: **`normalizer` has ZERO production write sites** (uncapped grep across all named roots — only `Model_Init` default + tests `controller_test.cpp:20599-20639`), so every loaded handle is `NORM_IDENTITY` (`:716` early return). For WILL_PEAK, identity IS the right mapping. The whole v5.12.3 NORM_* layer is emitted-but-unwired (D-422 register family).

**Verdict:** a WILL_PEAK-trained binary `exit.json` **loads and predicts correctly** through `Model_Predict_Normalized` at `Strategies/StrategyParameters.hpp:1440` — *conditional on* the reachability + scaler preconditions in Risks R1/R2 below, and on `label_lookahead_ticks == H` (the trainer sets it at `BacktestPanels.hpp:4345` → `StampHelper.hpp:378-381`, so this holds by construction).

**Two stale comments found on this exact surface (verified against code per arming §2.5):**
- `NodeModelZoo.hpp:2243-2246` claims default `buy_class_idx=0` = "VALLEY class". **False** — index 0 is **STABLE** (`LabelFunctions.hpp:90`, and the file's own header at `:40` says `multi[0]=stable`). The hazard direction described survives; the class name is wrong.
- `NodeModelZoo.hpp:2349` tells the operator `core_N_model_dir=...`. **The `core_` prefix boot-REFUSES at HEAD** (`ControllerConfig.hpp:3486-3489`, FATAL "RETIRED 'core_' key prefix"). Correct key: `node_N_model_dir` (`:3282`). This comment is an active instruction to write a cfg that refuses boot.

## Q2 — Primary-chain isolation: confirmed, plus a 3-site "exit-blindness" cohort

- **Ensemble**: `LoadFromCfg` primary selection = buy_signal (`:2204`) > barrier (`:2213`) > regime (`:2224`); `exit_predictor` never assigned (`:2200-2234`). `EnsembleModelZoo_EnsurePrimary` (`:1504-1527`) identical chain, no exit. Exit aliasing block explicitly independent (`:2236-2255`).
- **Single-zoo**: `LoadFromDir` primary = buy_signal > barrier > regime (`:722-739` region, verified — no exit branch); `zoo->exit` loads (`:701-705`, sets `NODE_MODEL_EXIT`) but its ONLY consumers are observability/validation walks: `ShardedSnapshot.hpp:671/:675/:707`, `LiveReadiness.hpp:66`, `ModelValidation.hpp:234`, `FeatureRegistryOverlay.hpp:216`, `Free :787`. **No predict-time consumer** — the live exit consumer reads only `ezoo->exit_predictor` (`StrategyParameters.hpp:1437-1438`).
- **No promotion path exists**: `AutoDetectFromDir` scans **directory names** `<base>_horizon_<digits>` only (`:2508-2528`) — it never inspects role files; role files bind to role arrays by exact filename in `LoadFromCfg`. A co-located `exit.json` can never enter a buy slot short of a hand-rename.
- **The inverse failure exists instead** — three `role_files[]` lists that **exclude** exit and go blind on it:
  1. `GUI/SettingsPanel.hpp:978-983` (`Settings_RescanModels` — hot-swap dir picker; an exit-only dir is invisible),
  2. `Backtest/BacktestPanels.hpp:1169-1171` (PastRuns `has_stamp` detection — exit-only run shows unstamped),
  3. `Backtest/BacktestPanels.hpp:2170-2173` (Verify Stamp button — exit-only dir reports "no model file found").
  PastRuns `Role=%s` display (`:2115-2116`) is display-only, from `expected.cfg`, no load.

## Q3 — What feeds `base_run_path`

| Caller | file:line | base_run_path source | horizon source |
|---|---|---|---|
| **BOOT (LIVE + BACKTEST)** | `EngineCommon_BootPerCore` (`CoreFrameworks/EngineCommon.hpp:267`) step 5e `:363-372` → `EnsembleModelZoo_AutoDetectFromDir(ezoo, cfg.node_model_dir[c], …)` → internal `LoadFromCfg` at `NodeModelZoo.hpp:2550` | **`cfg.node_model_dir[c]`** — cfg key **`node_N_model_dir`** (parse `ControllerConfig.hpp:3262` prefix + `:3282` suffix; `core_N_` REFUSED `:3486-3489`) | disk scan of `<base>_horizon_<digits>` siblings (`:2508-2528`), sorted (`:2537-2545`) |
| **HOT-SWAP (production)** | `tt::HotSwap_ShadowLoad_Ensemble` (`CoreFrameworks/HotSwap.hpp:68`; LoadFromCfg at `:128`) invoked from `CoreFrameworks/EngineSharded/Run.hpp:1893` | **NOT a cfg field** — GUI request: `SettingsPanel.hpp:1744-1772` writes `g_shared.pending_model_path[c]` + `swap_model_path_requested[c]` (TUISnapshot shared region, `DataStream/EngineTUI.hpp:1538-1543`); slow path copies it at `Run.hpp:1845-1847` | cached from pre-swap `ezoo->horizon_ticks_at_idx[]` (`HotSwap.hpp:97-109`) — **a swap target must have the SAME horizon set as boot** |
| **`EnsembleHotSwap.hpp:77`** (`EngineSharded_HotSwapEnsemble`) | ⚠ **Correction to the mission premise: NOT a production caller at HEAD.** Callers = tests only (`tests/controller_test.cpp:23696-23751`); `Run.hpp:126` include comment: "legacy in-place; superseded v5.15.4 by HotSwap.hpp"; the shadow-load branch's own comment `Run.hpp:1873-1877`: "kept compiled but not called from this production path" | (same shape as HotSwap when tests call it) | same cached-horizons pattern (`:51-63`) |

- **BOOT and swap use the same loader** (`EnsembleModelZoo_LoadFromCfg`) — boot via the AutoDetect wrapper, swap directly with cached horizons. Complete non-test caller set (uncapped grep): `NodeModelZoo.hpp:2550`, `EnsembleHotSwap.hpp:77`, `HotSwap.hpp:128`.
- **`cfg.exit_signal_model_dir`** (`ControllerConfig.hpp:856`, default `:2300`, parse `:2814-2817`): re-verified at HEAD across all 10 roots — consumers are 2 parse-round-trip tests (`controller_test.cpp:21458, :21621`) + 5 trainer comments/tooltips (`BacktestPanels.hpp:3115, 4300, 4988, 4998, 5977`). **Parsed-never-read stands.** So the ONLY cfg the operator points at exit.json's future home is `node_N_model_dir` (under convention (a) co-location).

## Q4 — The side-key guard shape

**The pivotal find: a sister key ALREADY EXISTS.** `expected_role` is a live stamp wire key, end-to-end except enforcement:

- **Registry row**: `ML_Headers/StampBoundModelConstRegistry.hpp:533-535` (POST_CFG; `SKIP_HANDLE`, `tt::stamp_str_16`; doc: "operator's training-time role choice (buy_signal | barrier | regime | **exit**)"). Bit `STAMP_BIT_expected_role :702`, `MASK_expected_role :735`.
- **Emit**: `StampHelper.hpp:411-413` (`STAMP_PUT(inf, expected_role, args.req_role)`) inside `Stamp_AssembleAndEmit` (`:179`) — **the** canonical emit funnel; both production trainers route through it (header `:16-19`). The trainer plumbs `req_role` from label_type at `BacktestPanels.hpp:4356-4360` — **today `role` ∈ {buy_signal, barrier, regime} only (`:4291-4293`); `training_side` never changes it (`:4303` is directory routing only — PARITY-044 fact 1 re-confirmed)**.
- **Parse**: registry-driven POST_CFG walk inside `verify_model_stamp` (`ModelInference.hpp:1765`) → `sr.expected_role` + has-bit. Round-trip tested (`controller_test.cpp:23453-23474`).
- **Enforcement: NONE.** `NodeModelZoo_TryLoadRole` never reads `sr.expected_role` (grep of the fn body); the only other consumer, `NodeModelZoo_VerifyExpected` (`:831`, expected.cfg sidecar path, single-zoo-only), parses it (`:897-899`) and **only logs it** (`:974-975`) — never compares. Two unenforced role advertisements today.
- **Ledger**: `tools/identifier_ledger.txt:75` — `stamp-key|expected_role|22`.

**Mechanics for a NEW key `training_side`** (what the registry itself prescribes):

- One row appended to `FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG` + 1 enum bit in `StampHasFlagBit` (`:671-713`) + 1 MASK — the documented 3-site add (`StampBoundModelConstRegistry.hpp:524`). `STAMP_BIT_COUNT <= 64` static_assert (`:715`) has headroom. The row auto-flows: struct fields (`ModelInference.hpp:427/:1461/:2077`), parse (`:1765`), emit (`:2337`, gated `STAMP_EMIT_CHECK_HAS`).
- Emit via `STAMP_PUT` (`StampBoundModelConstRegistry.hpp:776` — value+bit together; the D-426/76e4b8e guard makes bit-without-value non-compiling) in `Stamp_AssembleAndEmit`, from a new `StampArgs` member beside `label_kind`/`req_role` (`StampHelper.hpp:127-132`).
- **Nearest-sister behavior**: `label_kind` exists in StampArgs (`:127`) but is **NOT a wire key** (only drives `LabelType_NumClasses` at `:333`); `label_params` group (`:378-382`) is the horizon-pinning sister whose absent-key handling (has-bit unset → check skips, `NodeModelZoo.hpp:511`) is the model for legacy handling.
- **MODEL_FORMAT_VERSION: NO bump required.** Surface G discipline is explicit in the registry header (`StampBoundModelConstRegistry.hpp:~30-35`): "MODEL_FORMAT_VERSION stays at 6 (UNCHANGED …); new fields are optional canonical body lines." Constants: `MODEL_FORMAT_VERSION 6` (`ModelInference.hpp:151`; checked at `Model_Load :619-628` via the XGBoost `foxml_version` attr — REFUSE on mismatch — and passed into `verify_model_stamp` at `NodeModelZoo.hpp:271`); `STAMP_FORMAT_VERSION_CURRENT/MAX = 3`, `EPOCH_FLOOR = 3` (`ModelInference.hpp:159-166`) — also unbumped for an optional key (future-version refuse at `:1793+` check 0b; pre-epoch hard-invalid check 0c). Legacy stamps (no key) → has-bit 0 → the load-site policy decides WARN-vs-skip; epoch breaks are free anyway per `project_no_live_models_dev_test_only`, but none is needed.
- **H21 flow**: the `stamp-key` SOURCES row (`tools/check_identifier_retirement.py:179-180`) parses `FOREACH_STAMP_BOUND_MODEL_CONST` with `value: positional` — key ordinal = emit position. **Append the new row at the very END of POST_CFG** (after the last current row; ledger tail today = `…thompson_exp3_blend_alpha|44`, `identifier_ledger.txt:97`): an append lands as `ADD (ok)`; a mid-list insert shifts every later ordinal → RENUMBERED red. Then bless via the tool's TTY-gated `--update` (NAME_KEYED semantics `:192-203`: the NAME is the identity; a retired emitting row must be DROPPED + burned in `RETIRED_NAMES`, never tombstoned in place — Rule 1a).

## Q5 — 3-tier strict mirror sites (template = `ml_scaler_load_failed`)

Contract text: `DOCS/CLAUDE_ML_INVARIANTS.md:331-355` — strict=1 REFUSE + ML→SimpleDip CRITICAL; strict=0 WARN + distinct PerCoreSnap surface + rate-limited CRITICAL; "Silent fallback is forbidden"; how-to-apply names exactly: **PerCoreSnap field + populator + ML Status panel branch + rate-limited CRITICAL log + tests for BOTH paths**.

The scaler sister's full site set (the template to mirror):

| Site | file:line |
|---|---|
| FOREACH_FAILURE_MODE registry row (BIT_FLAG, severity, GUI label auto-flow) | `MemHeaders/FailureModeRegistry.hpp:141` (`ml_scaler_load_failed`, SEV_YELLOW, "scaler: LOAD FAILED"); sisters `:134` (model_load_failed SEV_RED), `:250` (ml_model_corrupt) |
| Handle-side state | `ModelInference.hpp:378` (`scaler_load_failed` on ModelHandle) |
| Load-gate setter (refuse + warn arms) | `NodeModelZoo.hpp:558` (strict refuse), `:567` (warn-continue), CRITICAL fprintf `:562-565` |
| Snapshot populator | `CoreFrameworks/ShardedSnapshot.hpp:666-683` → `FAILURE_SET(snap->per_node[i], ml_scaler_load_failed)` at `:682` |
| GUI ML Status branch | `GUI/MLStatusPanel.hpp:253-262` (`FAILURE_IS_SET` → red "scaler: WARN — load failed" + tooltip) |
| PerNodeSnap carrier (TUISnapshot contract — survives the D-427 viewer decoupling) | `DataStream/EngineTUI.hpp:1276-1277` (failure_flags BIT_FLAG) |
| Rate-limited CRITICAL (runtime, ML no-signal path) | `Strategies/StrategyParameters.hpp:1610-1615` (`Health_LogCriticalRateLimited`) — the refuse arm surfaces via `ml_model_load_failed`→`ShardedSnapshot.hpp:632-634` + the `:913-933` fall-through log |
| Tests | `tests/controller_test.cpp:15082-15091`, `:24226-24256` |

**Template defect the new path must NOT copy:** the scaler aggregation walks **single-zoo handles only** (`ShardedSnapshot.hpp:667-676`). The drift-flags aggregation got the `.F.3` dual-walk fix — single-zoo `:703-707` PLUS ensemble arrays including `exit_predictor` `:735-738` (comment `:692-702`: "Operator (Caramel) nearly traded against stale ensemble models"). A side-mismatch flag set on `handle->drift_flags_at_load` at the TryLoadRole chokepoint (a new `FAILURE_MASK_ml_side_mismatch` bit via `FOREACH_FAILURE_MODE`) inherits the fixed dual-walk **for free** — that is the structurally cheapest warn-arm surface. The scaler ensemble gap itself is a candidate ledger item.

## Q6 — `MASK_ML_CFG_USE_EXIT_MODEL` + `exit_threshold` consumer chain

- Flag: `FOREACH_ML_CFG_FLAG` row `use_exit_model` (`ML_Headers/MlCfgFlagRegistry.hpp:69`; bit 0x0010 pinned `controller_test.cpp:25374-25375`; default 0).
- Threshold: `exit_threshold` registry row `CoreFrameworks/CfgFieldRegistry.hpp:787-788` (DBL 0.6 [0,1], per-node eligible); struct `ControllerConfig.hpp:855`.
- Chain: cycle reset + sink wiring `ControllerEventLoop.hpp:3030-3032` (`ml_ctx.out_exit_prediction = &state->nodes[slot].last_exit_prediction`, inside RebuildOneCore; handles wired at `:2957-2958`) → **producer** `Strategies/StrategyParameters.hpp:1425-1598`: gate (`:1425-1429`: flag + `ezoo_ex->exit_predictor_count>0` + sink non-null) → per-handle `Model_Predict_Normalized` (`:1440`) → exit reward-ring (`:1446-1462`) → D-423 exit-bandit SELECT (`:1497-1538`, needs `count>=2` `:1500`) → Ridge override (`:1544-1588`) → blended write (`:1594-1596`) → **actor** `EngineCommon_SlowPathCycleOneCore` (`CoreFrameworks/EngineCommon.hpp:527`): compare `> FPN_ToDouble(cfg.nodes[c].exit_threshold)` (`:668-671`) → per-slot bitmap walk (`:676-694`) → attribution meta (`:706-743`) → **`tt::OMS_PushExitForSlot` (`:746-748`)** → `SHALT_EXIT_PREDICTED` (`:750-751`). Observability: `ShardedSnapshot.hpp:604-605` → `GUI/MLStatusPanel.hpp:186-208`; reward attribution reads `last_exit_dominant_horizon` (`EngineCommon.hpp:707`).

---

## Option matrix (guard leg)

| Option | Shape | Cost | Catches | Weakness |
|---|---|---|---|---|
| **O1 — enforce the EXISTING `expected_role`** (canonical-sister EXTEND per `feedback_audit_canonical_sister_before_new_infra`) | Trainer sets `req_role="exit"` when `training_side==1` (`BacktestPanels.hpp:4291-4293/:4360`); `TryLoadRole` compares `sr.expected_role` vs its own `role_name` param (already in scope, `:189-190`), 3-tier | Smallest: **zero new wire keys, zero ledger change**; check ~15 LOC | Buy-in-exit-slot AND exit-in-buy-slot, both by hand-rename or wrong emit | Conflates file-slot with semantic side; a barrier 3-class deliberately trained for exit use must be stamped role=exit; legacy stamps (pre-v5.15.3) skip |
| **O2 — NEW `training_side` key** (the mission's named plan) | POST_CFG row (END-append) + enum bit + MASK + `StampArgs.training_side` + `STAMP_PUT` + ledger bless + `TryLoadRole` side-vs-slot check (role_name→side map: exit→1, others→0) | Registry 3-site + ledger + check | Semantic side independent of filename; survives any future filename convention | New H21 wire identifier forever; redundant with O1 for every currently-plannable case |
| **O3 — both** | O1 slot-integrity + O2 side-semantics | Sum | Everything either catches | Two keys asserting overlapping facts = future drift surface between them |
| **O4 — novel alternative considered** (`feedback_proactive_novel_alternative_consideration`): side-appropriate **label-kind vocabulary** as the marker — emit `label_kind` as a wire key (it already sits in StampArgs `:127`, unemitted) + a per-role allowed-label-kind table at load (exit slot requires {WILL_PEAK, PEAK_VALLEY_STABLE}; forbids WIN_LOSS) | 1 new key + a small table | The **semantic** failure PARITY-044 names (WIN_LOSS-trained model in the exit tree) — which NO side/role key catches, since side keys record intent, not label truth | PVS is legitimately both-side, so label alone cannot fully determine side; complement, not substitute |

**Recommendation:** **O2 as the plan's named guard, with O1 folded in as the same-commit sister** (the enforcement is one comparison in the same TryLoadRole block; the trainer's `req_role="exit"` line is required by convention (a) anyway so exit.json stamps `expected_role=exit`), and **O4's label-kind emit queued as the PARITY-044 leg (b) semantic complement** — a side key alone still admits an entry-goodness WIN_LOSS model trained side=1. Absent-key policy per the 3-tier: strict=1 REFUSE only when the SLOT is exit (buy slots must keep loading legacy stamps), strict=0 WARN + new `FOREACH_FAILURE_MODE` bit, -1 skip.

## Exact change list (for the plan body)

1. **Trainer emit leg** (`Backtest/BacktestPanels.hpp`): `role="exit"` when `training_side==1` (`:4291-4293` derivation + save `:4336-4337` + `req_role :4360`); decide co-location (drop the `exit/` side_prefix `:4303-4318`) vs keep-tree; keep `grid_member_count` consistent (else `NodeModelZoo.hpp:2565-2568` unwinds the whole ensemble).
2. **Stamp key** (O2): END-append row to `FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG` (`StampBoundModelConstRegistry.hpp` after the last row; 3-site per `:524`) + `StampArgs` member (`StampHelper.hpp:127-132`) + `STAMP_PUT` in `Stamp_AssembleAndEmit` (beside `:411-413`) + plumb from `FullValidationResults.req_*` like `:4348-4360`.
3. **Ledger bless**: `tools/check_identifier_retirement.py --update` (SOURCES `:179-180`; baseline GREEN/93 confirmed).
4. **Load-time check** in `NodeModelZoo_TryLoadRole` (`NodeModelZoo.hpp:189`), after `have_sr`: side/role vs `role_name`, 3-tier; set a NEW `FOREACH_FAILURE_MODE` bit (`MemHeaders/FailureModeRegistry.hpp`, beside `:141`) on `handle->drift_flags_at_load` in the warn arm (rides the fixed dual-walk aggregation `ShardedSnapshot.hpp:703-747`).
5. **3-tier mirror sites** per the Q5 table: panel branch (`MLStatusPanel.hpp` beside `:253`), refuse-arm CRITICAL, tests both arms.
6. **exit-blindness cohort**: add `exit.json`/`exit.xgb` to the three `role_files[]` lists (`SettingsPanel.hpp:978`, `BacktestPanels.hpp:1169`, `:2170`) or record the explicit skip.
7. **`exit_signal_model_dir` disposition** (D-422 three end-states): wire as loader base, or retire field+parse+5 tooltips (`:3115/:4300/:4988/:4998/:5977`) — under convention (a) retire is the clean answer.
8. **Stale comment fixes**: `NodeModelZoo.hpp:2349` (`core_N_`→`node_N_`) and `:2243-2246` (VALLEY→STABLE).

## Risks / unknowns / refute-spots (where the a-class should push)

- **R1 — reachability (HIGHEST-VALUE REFUTE)**: the exit block is unreachable unless the SINGLE-zoo loaded ≥1 role — `ML_BuildParameters` early-returns SimpleDip at `StrategyParameters.hpp:913` on `!zoo || !NodeModelZoo_HasAny(zoo)` (`NodeModelZoo.hpp:793-795` = `loaded_mask != 0`), and boot sets `model_handle` only when the single-zoo load succeeded (`EngineCommon.hpp:342-343`). A pure `<base>_horizon_*` deployment (base is a name prefix, not a dir) appears to leave `model_handle` NULL → exit path (and the ensemble buy path, gated inside `:1069`) dead. **Refute by compiled probe or a real deployment layout** — if it holds, co-located exit.json alone does not enable the exit path, and the plan needs a base-dir model or a dispatch change.
- **R2 — scaler application seam**: exit predictions consume `features[]` standardized in-place by the SINGLE-zoo `barrier`/`buy_signal` handle's scaler (`:1032`, `:1071`) — never by the exit handle's own scaler. If the single-zoo has only a regime role, features reach exit predict RAW. Sibling-scaler WARN (`NodeModelZoo.hpp:2274-2300`) is the only guard and does not cover cross-RUN single-zoo-vs-ensemble mixes.
- **R3** — ensemble callers pass no `cfg_ptr`/mask (`:2148-2156`) → cfg-drift walk + model-age bit dead for ALL ensemble-loaded models (exit included); adjacent to PARITY-042/-043, not created by this plan.
- **R4** — a REGIME 4-class model in the exit slot gets `buy_class_idx=1` = P(regime class 1): garbage that loads clean today; the side guard is what kills it — a-class should verify the guard covers all 4 role-file names, not just buy/exit.
- **R5** — positional stamp-key ledger: any NON-append insertion REDs Check H for every later key (`check_identifier_retirement.py:166-180`).
- **R6** — swap-path horizons are cached from pre-swap (`HotSwap.hpp:97-109`): hot-swapping toward a run with a different horizon set fails by design; exit.json adoption via hot-swap inherits this.
- **R7** — `Settings_RescanModels` blindness (Q2) means an exit-only dir can't even be SELECTED for hot-swap; interacts with R1.
- **Unknown** — whether any operator cfg on disk sets `node_N_model_dir` to a layout where both single-zoo and `_horizon_*` siblings exist (bears on R1's practical severity; cfgs are workspace-private, unread here).
