# /trace-deps report — v5.15.5.F.4c.3 global-vs-per-core registry split — 2026-05-15

**Plan:** `plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3-global-vs-per-core-registry-split.md`
**HEAD:** `88043ea` (v5.15.5.F.4c.1 close)
**Auditor:** /trace-deps Layer 2 (executed inline; no nested subagents)

## Summary

- API/struct/macro references in plan: 27
- **PASS:** 22
- **GAP:** 1 (BLOCKING — symbol axis misclaim)
- **DRIFT:** 4 (signature/scope implication needs plan clarification)
- **DRIFT-RISK:** 0

**Verdict:** YELLOW. Dependency chain mostly green; 1 GAP and 4 DRIFTs require plan amendments before coding. None of the gaps are showstoppers — all are addressable via plan text refinement (no structural surprises in the codebase).

---

## Per-API verification

### Section 1 — Plan-named APIs at HEAD `88043ea`

| API/Struct/Macro | Verdict | file:line at HEAD | Notes |
|---|---|---|---|
| `PerCoreOverrides<F>` struct | PASS | `CoreFrameworks/ControllerConfig.hpp:254` | Plan deletes; deletion is clean (4 sites total to remove) |
| `core_overrides[16]` field | PASS | `CoreFrameworks/ControllerConfig.hpp:1054` | 17 consumer sites enumerated (see Section 1b) |
| `PER_CORE_OVERRIDE_BITMAP_DOMAINS` X-macro | PASS | `CoreFrameworks/ControllerConfig.hpp:247` | 6 consumer sites (declare/zero/resolve/parse + comment in OpsCfgFlagRegistry); deletion clean |
| `ControllerConfig_ResolveForCore` template fn | PASS | `CoreFrameworks/ControllerConfig.hpp:1271` | **17 caller sites enumerated** (see Section 1c) — plan claim "simplify or delete" needs concrete decision |
| `tt::cfg_parse_field<T>` | PASS | `CoreFrameworks/CfgFieldDispatch.hpp:49` | sig: `(T& dst, const CfgFieldDescriptor& desc, const char* val)` — destination-by-reference works seamlessly with `PerCoreCfg<F>` fields |
| `tt::cfg_save_field<T>` | PASS | `CoreFrameworks/CfgFieldDispatch.hpp:170` | sig: `(const T& src, const CfgFieldDescriptor& desc, char* buf, size_t cap)` — registry-agnostic |
| `tt::cfg_assign_field<T>` | PASS | `CoreFrameworks/CfgFieldDispatch.hpp:223` | sig: `(T& dst, const CfgFieldDescriptor& desc)` — registry-agnostic |
| `tt::cfg_diff_field<T>` | PASS | `CoreFrameworks/CfgFieldDispatch.hpp:264` | sig: `(const T& current, const CfgFieldDescriptor& desc)` — registry-agnostic |
| `tt::cfg_render_field<T>` | PASS | `GUI/SettingsPanel.hpp:60` | sig: `(T& field, const CfgFieldDescriptor& desc)` — registry-agnostic |
| `CfgFieldDescriptor` struct | PASS | `CoreFrameworks/CfgFieldRegistry.hpp:41` | `sizeof <= 128B` static_assert intact; unchanged for split |
| `g_cfg_field_descriptors[]` | PASS | `CoreFrameworks/CfgFieldRegistry.hpp:548` | Plan REPLACES with `g_global_*` + `g_per_core_*` — downstream consumers (Section 1d) all enumerable |
| `FOREACH_METADATA_BIT` | PASS | `CoreFrameworks/CfgFieldRegistry.hpp:640` | Reusable for two-registry mask generation |
| `FOREACH_LIVES_IN_STRUCT` | PASS | `CoreFrameworks/CfgFieldRegistry.hpp:702` | Reusable; existing pattern compatible |
| `cfg_field_names_unique` (constexpr) | PASS | `CoreFrameworks/CfgFieldRegistry.hpp:590` | Already templated on `(const CfgFieldDescriptor (&a)[N])` — invoke twice (once per registry) for per-registry uniqueness |
| `CfgRenderTable<F>` | PASS | `GUI/SettingsPanel.hpp:172` | Function-pointer table; ADD two parallel tables (`GlobalRenderTable<F>` + `PerCoreRenderTable<F>`) per plan |
| `g_cfg_render_mask` / `g_cfg_save_mask` | PASS | `CoreFrameworks/CfgFieldRegistry.hpp:784,800` | Existing single-registry pattern — ADD per-registry variants |
| `FOREACH_ML_CFG_FLAG` (FoxML 13 entries) | PASS | `ML_Headers/MlCfgFlagRegistry.hpp:52` | **DRIFT-2: plan says "all 12 ml_cfg_flags bits" — actual count = 13 entries** (CONFIDENCE_ENABLED through PER_HORIZON_BARRIER_BLEND). See DRIFT-2 below. |
| `FOREACH_STAMP_BOUND_CFG` | PASS | `ML_Headers/StampBoundCfgRegistry.hpp:101+` | Consumed by `ModelInference.hpp:1198,1400,1642,1787` — per-core stamp dispatch retrofit is mechanical |
| `FOREACH_CFG_DRIFT_CHECK` | PASS | `ML_Headers/CfgDriftCheckRegistry.hpp:194` | 18 entries; walker at `CoreFrameworks/ModelValidation.hpp:210` — per-core retrofit mechanical (loop wrap around existing walker) |
| `MAX_EXECUTION_CORES` | PASS | `Limits.hpp:19` (value=16) | Matches plan claim `cores[MAX_EXECUTION_CORES]` |
| `FIELD_IDX_<name>` enum | PASS | `CoreFrameworks/CfgFieldRegistry.hpp:534` | Need two enum families (FIELD_IDX_GLOBAL_<name> + FIELD_IDX_PER_CORE_<name>) post-split; plan didn't explicitly call this out |
| `ControllerConfig_Load<F>` | PASS | `CoreFrameworks/ControllerConfig.hpp:1800` | Parser is FLAT key-loop currently; section-state-machine retrofit required (Section 6) |

### Section 1b — `core_overrides[16]` consumer sites (17 total)

| File:line | Site type |
|---|---|
| `CoreFrameworks/ControllerConfig.hpp:1054` | declaration |
| `CoreFrameworks/ControllerConfig.hpp:1275` | `ResolveForCore` read |
| `CoreFrameworks/ControllerConfig.hpp:1713-1723` | `_ZERO_OV_*` defaults macros |
| `CoreFrameworks/ControllerConfig.hpp:2668` | parser write |
| `CoreFrameworks/EngineSharded.hpp:429,2362,2366,2405,2743` | sharded engine reads (5 sites — slow-path) |
| `tests/controller_test.cpp:4556,4557,22768,22770,22772,22774,22776,22795,22796,22823,22825,22827,22829,22831,22833,22836,22911,22913,22915,22917,22927,22928,22929,22953,22976,22977,22989,22998,23021,23023,23025,23027,23031` | test fixture sites (~33 sites, many in v4.0 override semantics tests at lines 22763-23031) |

Test fixture migration scope: ~33 sites in `controller_test.cpp` (plan estimates ~50-100 broader test sites including non-override test fixture initializations). All mechanical via grep + replace.

### Section 1c — `ControllerConfig_ResolveForCore` caller sites (17 total)

| File:line | Caller |
|---|---|
| `tests/controller_test.cpp:4558,4564,22783,22797,22803,22839,22842,22931,22935,22955,22961` | 11 test sites |
| `CoreFrameworks/ShardedSnapshotPersist.hpp:645` | snapshot publish |
| `CoreFrameworks/EngineSharded.hpp:1422,1443,2736` | sharded engine slow-path init |
| `CoreFrameworks/ControllerEventLoop.hpp:2325` | slow-path RebuildOneCore body (HOT slow-path site) |

**Plan claim:** *"`ControllerConfig_ResolveForCore` simplified or deleted (depending on remaining callers)"* — RECOMMENDATION: plan should declare the resolution path explicitly. With per-core authoritative, the resolved-cfg pattern collapses: `EventLoop_RebuildOneCore` can pass `cfg.cores[slot]` directly to downstream strategies (signature change cascade). Tests at lines 22763-23031 specifically exercise the override-resolve semantics; need rewrite OR deletion when override mechanism is eliminated.

### Section 1d — `g_cfg_field_descriptors[]` downstream consumers

| File:line | Site | Action post-split |
|---|---|---|
| `CoreFrameworks/ControllerConfig.hpp:1906` | parser dispatch | walker becomes section-state-aware; dispatch to `g_global_*` OR `g_per_core_*` |
| `GUI/SettingsPanel.hpp:1067` | render walker | two walkers post-split |
| (sidecar override pattern future consumers) | none currently | `.F.4d` adds; orthogonal to split |

---

## Section 2 — ML-side read sites (plan H rows)

For each file in plan section H, enumerate cfg reads of fields moving to per-core. Plan claim: "each call site has `core_idx` accessible."

### 2a. `Strategies/StrategyParameters.hpp` — 11 critical reads of per-core-bound fields

| Line | Read | Caller scope |
|---|---|---|
| 326-327 | `config->simpledip_tp_pct/sl_pct`, `config->take_profit_pct/stop_loss_pct` | `SimpleDip_BuildParameters` — takes `const ControllerConfig<F>* config` |
| 417-418 | `config->mr_tp_pct/sl_pct`, `config->take_profit_pct/stop_loss_pct` | `MR_BuildParameters` |
| 499-500 | `config->take_profit_pct`, `config->stop_loss_pct` | Same fn |
| 515-516 | `config->take_profit_pct`, `config->stop_loss_pct` | Same fn |
| 621-623 | `config->emacross_tp_pct/sl_pct`, `config->take_profit_pct/stop_loss_pct` | `EmaCross_BuildParameters` |
| 928, 955, 1001 | `config->bandit_algorithm` | ML branch (multiple sites) |
| 1040, 1263 | `FPN_ToDouble(config->ridge_lambda)` | Ridge dispatch |
| 1419 | `FPN_ToDouble(config->confidence_threshold_scale)` | Confidence branch |
| 1433 | `FPN_ToDouble(config->confidence_hard_block_threshold)` | Confidence branch |
| 1794 | `BITMAP_IS_SET(config->ml_cfg_flags, MASK_ML_CFG_FOXML_VOL_SCALING_ENABLED)` | Vol scaling |

**DRIFT-1 (signature implication):** The 4 `_BuildParameters` functions take `const ControllerConfig<F>* config`. Post-split, `take_profit_pct` is no longer on `ControllerConfig<F>`. Plan SHOULD specify whether:
- **Option A:** Function signatures change to `(const PerCoreCfg<F>* config, ...)` — propagates through ~20 callers; cleanest
- **Option B:** Function continues taking `ControllerConfig<F>*` but caller pre-resolves with `cfg.cores[c]` → would need conversion or a "view" struct; messier
- **Option C:** Both old `ControllerConfig<F>*` + new `int core_idx` passed; functions read `cfg->cores[core_idx].<field>` internally — minimal-touch but ugly

Plan section H is silent on this. RECOMMENDATION: explicit decision before Step 2 (struct restructure). Option A is the boundary-stable refactor (per CLAUDE.local.md "boundary-stable refactors over wide cascades" rule).

### 2b. `ML_Headers/RidgeBlender.hpp` / `ConfidenceScore.hpp` / `ThompsonBandit.hpp` / `CoreModelZoo.hpp`

- `RidgeBlender.hpp` — only comments/docs reference `cfg.ridge_lambda`; actual reads parameterized via FPN<F> args passed from `StrategyParameters.hpp` ridge dispatch (Section 2a). VERIFIED: no cfg.X reads inside the kernel.
- `ConfidenceScore.hpp:578-582` — comments reference cfg.confidence_*; actual API is `ConfidenceScorer_Score(scorer, ...)` taking doubles. Caller (StrategyParameters.hpp) reads cfg fields + passes via args. VERIFIED.
- `ThompsonBandit.hpp` — comments only. Init reads doubles from caller. Caller (`CoreModelZoo.hpp:2584-2586`) reads `cfg.thompson_*` via `FPN_ToDouble(cfg.thompson_mu_prior)` etc. VERIFIED.
- `CoreModelZoo.hpp:2552-2553,2584-2586` — reads `cfg.core_ensemble_blend_mode[core_id][...]` AND `cfg.thompson_*`. Has `core_id` in scope. VERIFIED.

### 2c. `CoreFrameworks/ControllerEventLoop.hpp:2325` (RebuildOneCore body)

The CRITICAL site. Reads via `ControllerConfig<F> resolved_cfg = ControllerConfig_ResolveForCore(*config, slot)` then `resolved_cfg.session_*_mult` (lines 2349) and `resolved_cfg.volume_multiplier` (lines 2358-2359). Has `slot` in scope. PASS — direct migration to `cfg->cores[slot]` straightforward.

### 2d. `Strategies/MLStrategy.hpp` — minimal cfg reads

Strategy uses callbacks + ML inference; cfg reads delegated to StrategyParameters. VERIFIED.

---

## Section 3 — Backtest path

`Backtest_Run` is a thin wrapper around `BacktestSharded_Run` (E.7 refactor, v4.4.0).

### 3a. `BacktestSharded_Run` cfg reads

`Backtest/BacktestSharded.hpp:239` reads `FPN_ToDouble(cfg.risk_pct)` as DEFAULT across cores, overridden per-core by `cfg.core_risk_pct[i]` at line 264-265. With the split, `cfg.risk_pct` (global default) DISAPPEARS — only `cfg.cores[i].risk_pct` exists. The "default + override" semantics collapse: each core's risk_pct is authoritative.

**Plan claim H.b:** *"Replace `cfg.take_profit_pct` reads with `cfg.cores[backtest_core_idx].take_profit_pct`"*

**DRIFT-3:** plan doesn't address the existing `core_risk_pct[16]` array that already encodes per-core risk. Same for `core_strategies[16]`, `core_model_path[16][256]`, `core_model_dir[16][256]`, `core_horizon_list[16][128]`, `core_ensemble_blend_mode[16][16]`, `core_disabled_horizons[16][128]`. Plan section B mentions strings stay manual (good), but doesn't specify what happens to `core_risk_pct[16]` + `core_strategies[16]` (FPN/uint8 arrays). RECOMMENDATION: Step 0.C classification table MUST explicitly classify each existing per-core array — they either (a) collapse into the new `PerCoreCfg<F>.risk_pct` / `.strategy` row instances (preferred — eliminates parallel paths) OR (b) stay as parallel `core_*[]` arrays (rejected — defeats the split's intent).

### 3b. Plan section H.b backtest path

Plan says *"backtest reads from the loaded engine.cfg's per-core sections matching the core index it's simulating"* — works mechanically if every test site has access to the core index it's simulating. Test sites already use `cores[i]` semantics (lines 255-405); all sites have `i` in scope. PASS.

---

## Section 4 — Symbol axis (plan section A, "symbol axis NEW")

### 4. **GAP: `cfg.symbol` does not exist on `ControllerConfig<F>`**

Plan claim: *"symbol axis (NEW): `symbol` migrated per-core with boot-time uniformity check until multi-symbol DataStream support"* — IMPLIES `cfg.symbol` is currently on `ControllerConfig<F>` and gets moved.

**FINDING:** `cfg.symbol` is NOT on `ControllerConfig<F>`. The `symbol` field lives on `BinanceConfig` at `DataStream/BinanceCrypto.hpp:64`:

```cpp
struct BinanceConfig {
    char symbol[32];            // e.g. "btcusdt" (lowercase)
    ...
};
```

Consumer sites (all use `bcfg.symbol`):
- `DataStream/BinanceCrypto.hpp:543,568,826,864` — strcpy/strncpy + WS endpoint format
- `DataStream/MockGenerator.hpp:103` — `gen->config.symbol`
- `CoreFrameworks/EngineSharded.hpp:560,589,714,763,814,824,833,839,855` — 9 sites read `bcfg.symbol`
- `tests/binance_test.cpp:25`, `tests/integration_test.cpp:90,129,203` — test fixtures

**Plan implication needs amendment:** the per-core symbol migration is fundamentally a `BinanceConfig` (DataStream) restructure, NOT a `ControllerConfig<F>` cfg-field migration. BLOCKING.

**Recommended resolutions:**
- (a) Add `symbol[32]` as a new per-core row in `FOREACH_PER_CORE_CFG_FIELD` (KIND_STRING — but plan locks `.F.4e` for string registry support; so .F.4c.3 can't ship per-core symbol via the framework)
- (b) Add `char symbol[32]` to `PerCoreCfg<F>` as a non-registry manual field with boot-time uniformity check (lives alongside string fields per plan section B's `core_model_path[]` etc. handling)
- (c) Defer symbol axis to `.F.4e` (when string-cfg per-core ships)

Plan must select. RECOMMENDATION: (b) for `.F.4c.3` — non-registry manual field with uniformity check at boot — OR (c) defer. (a) is blocked by the `.F.4e` dependency.

---

## Section 5 — Stamp emit + drift check

### 5a. `StampBoundCfgRegistry.hpp` consumers

Walked by `ML_Headers/ModelInference.hpp:1198,1400,1642,1787` (4 sites: declarations, init, populate-from-cfg, emit-canonical-body). Drives `inference_cfg_<field>` + `has_inference_cfg_<field>` fields on inference handle. Per-core retrofit:
- Each core has its own `inference_cfg_*` per-core (already implicit via `model_handle.inference_cfg`)
- Each core's stamp body emit reads `cfg.cores[c].<field>`
- Layer 5b hash recompute: 4 stamps for 4 cores
- Mechanical: replace `cfg.<field>` → `cfg.cores[c].<field>` in `STAMP_BOUND_AUTOPOPULATE_FROM_CFG` macro

### 5b. `FOREACH_CFG_DRIFT_CHECK` walker

`CoreFrameworks/ModelValidation.hpp:153-210` — single-handle drift check. Per-core retrofit: wrap walker in outer `for (int c = 0; c < num_execution_cores; ++c)` loop; pass `cfg.cores[c]` as drift-check input vs `core[c].model_handle->inference_cfg_*`. Mechanical.

### 5c. Per-core stamp file layout (plan section E open question)

Plan presents 3 options: (a) `models/core_N.stamp`, (b) unified `models/cores.stamp`, (c) `models/<core_N_model_dir>/cfg.stamp`. Plan leans (c). RECOMMENDATION: confirm (c) at audit gate. (c) fits existing `core_model_dir` convention naturally; per-core stamp follows model directory.

---

## Section 6 — Cfg parser state machine

### 6. **DRIFT-4 — Parser refactor scope**

Current parser at `CoreFrameworks/ControllerConfig.hpp:1800-2700+` is a **flat key-loop**: reads `key=value` lines one at a time, does substring/strcmp matches, dispatches via `FOREACH_CFG_FIELD(EMIT_CFG_PARSER_CASE)` walker (line 1909) — NO section state. The plan claims `[core N]` section header detection needs adding.

**Existing per-core key handling** (lines 2593-2731 in plan-referenced range): parser already detects `core_<N>_<key>` flat-prefix keys (e.g., `core_0_risk_pct=0.10`). This is the legacy per-core override syntax that ALSO needs to be deprecated/migrated alongside the section-aware refactor.

**Scope assessment:**
- Add section-state machine: ~50 LOC additive (track `parse_state` enum, detect `[core N]` headers, set active_core_idx)
- Replace `core_<N>_<key>` flat-prefix handling: ~100 LOC of legacy code to remove (15 sites in lines 2593-2731)
- Migration-hint error for unknown global key under no-section AND unknown per-core key after `[core N]` (plan section C item 3-4) — ~30 LOC
- Total: ~150-180 LOC parser changes. Within plan's estimate of "Step 3 ~150 LOC".

PASS — parser is structured for the refactor (linear fgets loop; section state additive).

---

## Section 7 — Settings panel

### 7. SettingsPanel walker

Current state per `GUI/SettingsPanel.hpp:1066-1097`:
- Single walker over `g_cfg_render_mask.words` via `CFG_FIELD_FOR_EACH_SET_BIT` macro
- Dispatches `CfgRenderTable<64>::fns[idx](s->gui_engine_cfg, desc, s->cfg_path)`
- Operates on a single `ControllerConfig<64>` mirror

Plan-required restructure:
- Global tab walker: walks `g_global_cfg_render_mask` + `GlobalRenderTable<F>::fns[]` over `cfg` (whole struct)
- Per-core tab walker (per engine core): walks `g_per_core_cfg_render_mask` + `PerCoreRenderTable<F>::fns[]` over `cfg.cores[c]` slice
- Section headers: deduplicate naturally (each registry's section header column is independent)

**DRIFT-5 (minor):** `RenderFn` typedef at line 176 is `bool (*)(ControllerConfig<F>&, const CfgFieldDescriptor&, const char*)`. PerCore variant needs `bool (*)(PerCoreCfg<F>&, const CfgFieldDescriptor&, const char*)`. Mechanical typedef change; plan should call out the new typedef explicitly. RECOMMENDATION: add `PerCoreRenderFn` typedef to plan section F.

---

## Section 8 — DESIGN_SPECs verification

Both DRAFT v1.0 specs exist at workspace paths per plan Step 0.B:
- `/home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/per-instance-registry-pattern.md` ✓
- `/home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` ✓

Referenced existing specs all present:
- `universal-cfg-field-registry-pattern.md` ✓
- `universal-registry-bitmap-dispatcher-pattern.md` ✓
- `type-trait-dispatch-via-tt-namespace.md` ✓
- `wire-format-byte-preservation-discipline.md` ✓
- `categorical-tag-applicability-pattern.md` ✓
- `cfg-flag-eligibility-criteria.md` ✓

Class 24 verified at `DOCS/RECURRING_BUG_PATTERNS.md:1563`.

---

## Section 9 — Mirror data-flow audit (Class 18 prevention)

Plan body keywords matched: *"mirrors `CfgRenderTable<F>`"* (plan section A row 5) — TWO new render tables parallel structure to existing one.

**Source range mirrored:** `GUI/SettingsPanel.hpp:172-200` (existing `CfgRenderTable<F>` body).

**Call-sequence audit of mirrored source:**
| Source call | Mirror present in plan? | Verdict |
|---|---|---|
| `tt::cfg_render_field<T>(field, desc)` | YES (plan section F) | MIRROR-PRESENT |
| `tt::cfg_save_field<T>` (in `cfg_render_and_persist`) | YES (implicit via shared `cfg_render_and_persist`) | MIRROR-PRESENT |
| `cfg_write_field` (persist) | YES (implicit) | MIRROR-PRESENT |
| `ImGui::PushID` (around field render) | Implicit | MIRROR-PRESENT |
| `FIELD_IDX_<name>` indexing | DRIFT — plan didn't specify FIELD_IDX_GLOBAL_<name> + FIELD_IDX_PER_CORE_<name> split | DRIFT (plan amendment needed; see Section 1 row 21) |

Mirror data-flow inputs (struct field reads):
- `desc.name`, `desc.kind`, `desc.metadata_flags` — all on `CfgFieldDescriptor`, unchanged; PASS for both registries

---

## Section 10 — Cross-cutting findings

### 10a. **DRIFT-2: `FOREACH_ML_CFG_FLAG` entry count**

Plan claim section A row 2: *"all 12 ml_cfg_flags bits"*. Actual count at `ML_Headers/MlCfgFlagRegistry.hpp:52` = **13 entries** (CONFIDENCE_ENABLED, CONFIDENCE_COMPOSITE_ENABLED, BANDIT_ENABLED, EXIT_BANDIT_ENABLED, USE_EXIT_MODEL, FOXML_VOL_SCALING_ENABLED, LAZY_REBUILD_ENABLED, RIDGE_WITHIN_HORIZON, RIDGE_ACROSS_HORIZONS, EXIT_BLENDER_MODE, RIDGE_ONLINE_CORR, PER_HORIZON_BARRIER_BLEND — and confirmed via `grep -c "X(" = 14` matches incl. the FOREACH_ML_CFG_FLAG line itself = 13 actual entries).

RECOMMENDATION: plan amendment — update "12" → "13" in section A row 2.

### 10b. New helper functions implied

Plan section A row 2 says: *"A2 bitmap-bool migration: all 12 ml_cfg_flags bits migrate to flat KIND_BOOL rows in the per-core registry; runtime bitmap rebuilt from rows at slow-path rebuild"*.

**NEEDS-NEW helper:** `BuildBitmapFromFlatRows` (or similarly-named) — composes runtime `ml_cfg_flags` uint16_t bitmap from per-core flat KIND_BOOL row values at slow-path rebuild. Pattern precedent: `ML_CFG_FLAG_AUTOPOPULATE_FROM_SEPTUPLE` macro at `ML_Headers/MlCfgFlagRegistry.hpp:92-103` — extend to 13-row version OR replace with X-macro-driven walker.

RECOMMENDATION: plan section A row 2 amendment — explicitly cite this helper as NEW (or as an extension of the existing AUTOPOPULATE macro). Without this helper, hot-path bitmap reads of `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_*)` (~18 sites in `StrategyParameters.hpp` + `StampHelper.hpp` + `CfgDriftCheckRegistry.hpp`) silently get stale data.

### 10c. **DRIFT-3 (recap): existing per-core arrays**

Currently in `ControllerConfig<F>`:
- `uint8_t core_strategies[16]` (line 971)
- `uint16_t core_strategies_explicit_set` (line 972 — partner bitmap)
- `FPN<F> core_risk_pct[16]` (line 989)
- `char core_model_path[16][256]` (line 1008)
- `char core_model_dir[16][256]` (line 1016)
- `char core_horizon_list[16][128]` (line 1027)
- `char core_ensemble_blend_mode[16][16]` (line 1028)
- `char core_disabled_horizons[16][128]` (line 1029)

Plan section B mentions string fields stay manual but doesn't classify the FPN/uint8 ones (`core_strategies[16]`, `core_risk_pct[16]`). RECOMMENDATION: plan Step 0.C classification table MUST explicitly classify these. The clean migration: collapse `core_strategies[i]` → `cfg.cores[i].strategy`, `core_risk_pct[i]` → `cfg.cores[i].risk_pct`. Eliminates parallel encoding; closes a Class 21 (parallel-descriptors) risk.

### 10d. Cohort-eligibility for new per-core risk gates

Plan section A row 2 introduces NEW per-core fields: `kill_switch_daily_loss_pct`, `kill_switch_drawdown_pct`, `max_drawdown_pct`, `max_exposure_pct`, `enable_mtm_kill_switch`. Per CLAUDE.local.md "Cohort-audit when new cfg field has 2+ siblings" — these 5 are a clear cohort. RECOMMENDATION: plan should call out cohort audit at Step 0.C boundary.

---

## Recommendations summary (plan amendments before coding)

**BLOCKING (must amend before code lands):**

1. **GAP-1 (Section 4):** Plan's symbol axis claim references `cfg.symbol` which doesn't exist. The symbol lives on `BinanceConfig` (DataStream). Plan must select resolution: defer to `.F.4e`, OR add manual field to `PerCoreCfg<F>`, OR explicitly remove from `.F.4c.3` scope.

**Strongly recommended (improves plan quality):**

2. **DRIFT-1 (Section 2a):** Choose function-signature treatment (Option A/B/C above) for `_BuildParameters` families. Document at Step 2 boundary.

3. **DRIFT-2 (Section 10a):** Correct `FOREACH_ML_CFG_FLAG` entry count from 12 → 13.

4. **DRIFT-3 (Section 3a + 10c):** Step 0.C classification table must explicitly handle existing `core_strategies[16]`, `core_risk_pct[16]`, + 5 string arrays. Recommend: collapse FPN/uint8 arrays into `PerCoreCfg<F>` row instances.

5. **DRIFT-4 (Section 6):** Parser scope estimate — add explicit ~100 LOC for legacy `core_<N>_<key>` flat-prefix removal alongside section-state addition.

6. **DRIFT-5 (Section 7):** Add `PerCoreRenderFn` typedef explicitly to plan section F.

7. **NEEDS-NEW helper (Section 10b):** Document `BuildBitmapFromFlatRows` (or equivalent) for ml_cfg_flags rebuild at slow-path; cite extension of existing `ML_CFG_FLAG_AUTOPOPULATE_FROM_SEPTUPLE`.

8. **FIELD_IDX_<name> namespace split (Section 1 row 21):** Explicitly call out `FIELD_IDX_GLOBAL_<name>` + `FIELD_IDX_PER_CORE_<name>` separation; or rename existing enum to namespaced form.

9. **Cohort-eligibility audit (Section 10d):** Per CLAUDE.local.md cohort-audit rule, the 5 new per-core risk gates are a 2+ sibling cohort; plan should note inclusion of cohort audit at Step 0.C.

---

## Verdict

**Dependency chain: GREEN with caveats → upgrade to GREEN after plan amendments 1-9.**

The plan's structural intent is sound. Every named API/struct/macro exists at `88043ea`. The split is mechanically achievable given current code shape. The audit surfaces 1 BLOCKING gap (symbol axis misclaim) and several DRIFT items that need explicit plan resolution — all addressable via plan text refinement, none requiring re-architecture.

**Estimated plan-amendment effort:** 60-90 min of plan editing + Caramel consult on Option A/B/C for ML signature treatment. Code remains as-scoped (~1200 LOC code + ~600 LOC specs + parser/test fixture migrations).

**Per CLAUDE.local.md "after pre-coding audits, ALWAYS consult before coding":** synthesize findings + present to Caramel for resolution decisions (especially DRIFT-1 and GAP-1) before Step 1 (registry framework infrastructure) coding starts.

---

**End of /trace-deps report.** Audit performed inline (Layer 2; no nested subagents) per skill spec 2026-05-09 execution model.
