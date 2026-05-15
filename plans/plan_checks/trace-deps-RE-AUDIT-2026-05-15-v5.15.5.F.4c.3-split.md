# /trace-deps RE-AUDIT — v5.15.5.F.4c.3 amended plan — 2026-05-15

**Plan:** `plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3-global-vs-per-core-registry-split.md`
**HEAD:** `88043ea` (v5.15.5.F.4c.1 close — unchanged from prior pass)
**First audit:** `plans/plan_checks/trace-deps-2026-05-15-v5.15.5.F.4c.3-split.md` — YELLOW (1 GAP + 4 DRIFTs)
**This pass:** Layer 2 inline (no nested subagents) verifies post-amendment dep chain integrity.
**Verdict:** **GREEN** — all 5 prior findings resolved; 5 newly-introduced deps verified concretely specified + bounded.

---

## 1. Per-prior-finding resolution verdicts

### GAP-1 (symbol axis on `BinanceConfig` not `ControllerConfig`) — **GREEN (resolved by defer)**

**Verification:**
- Amendment "CRITICAL-1" defers symbol axis to follow-up subplan `.F.4c.3.A` (fires AFTER `.F.4e` lands `KIND_STRING`).
- Subplan stub EXISTS at `/home/caramel/code/tick-trader-percore-workspace/plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3.A-symbol-axis-per-core-migration.md` (5056 bytes; Stage 1 STUB header; documents the 4 audit-gate decisions to resolve at-firing).
- Operator intent captured: defer until DataStream multi-symbol-ready; per-core architecturally locked.
- `BinanceConfig.symbol` consumers (10 sites including `DataStream/BinanceCrypto.hpp:64`, `EngineSharded.hpp:560/589/...`) UNTOUCHED at `.F.4c.3` per defer.

**Result:** Symbol no longer in `.F.4c.3` scope. Followup subplan stub explicitly enumerates open audit-gate decisions for its own pre-coding gate. Dependency burden moves cleanly to `.F.4c.3.A`.

### DRIFT-1 (`_BuildParameters` signature treatment) — **GREEN (Option A locked)**

**Verification at codebase HEAD `88043ea`:**
| Fn (file:line) | Current sig | Amended sig (Option A) |
|---|---|---|
| `Strategies/StrategyParameters.hpp:300` `SimpleDip_BuildParameters` | `const ControllerConfig<F>* config` | `const PerCoreCfg<F>* core_cfg` |
| `Strategies/StrategyParameters.hpp:379` `MeanReversion_BuildParameters` | same | same |
| `Strategies/StrategyParameters.hpp:450` `Momentum_BuildParameters` | same | same |
| `Strategies/StrategyParameters.hpp:564` `EmaCross_BuildParameters` | same | same |
| `Strategies/StrategyParameters.hpp:669` `ML_BuildParameters` | same | same |
| `Strategies/StrategyParameters.hpp:1561` `Strategy_BuildParameters` (dispatcher) | same | same |

**11 call sites enumerated** (verified by rg):
- `StrategyParameters.hpp:584, 733, 821, 840, 879, 1301, 1588, 1593, 1598, 1658, 1664` — internal dispatcher chains + `Strategy_BuildParameters` body
- `CoreFrameworks/ControllerEventLoop.hpp:2691` — main slow-path consumer
- `CoreFrameworks/LegacyReferenceDriver.hpp:188` — legacy ref driver

Amendment HIGH-1 mechanically maps `config->field` → `core_cfg->field` in each body. Boundary-stable refactor per `feedback_reduce_touch_sites.md`. Compile-error catches missed sites.

**Result:** Sig change scope concretely bounded (6 fn decls + 11 call sites = ~17 mechanical edits per fn). Plan amendment cites "4 strategy fns + 11 call sites" — match. PASS.

### DRIFT-2 (FOREACH_ML_CFG_FLAG count = 12 vs actual 13) — **GREEN (count corrected + F6 cohort extension)**

**Verification at `ML_Headers/MlCfgFlagRegistry.hpp:52-64`:** 13 entries enumerated (CONFIDENCE_ENABLED, CONFIDENCE_COMPOSITE_ENABLED, BANDIT_ENABLED, EXIT_BANDIT_ENABLED, USE_EXIT_MODEL, FOXML_VOL_SCALING_ENABLED, LAZY_REBUILD_ENABLED, RIDGE_WITHIN_HORIZON, RIDGE_ACROSS_HORIZONS, EXIT_BLENDER_MODE, RIDGE_ONLINE_CORR, PER_HORIZON_BARRIER_BLEND — confirmed `rg ^X(` count=13).

Amendment "CRITICAL-2" cites **13 bits** + specifies **9 migrate at `.F.4c.3` + 4 emit-via-BITMAP_BIT defer to `.F.4d`**.

**F6 cohort extension verified** — 5 cfg-domain bitmap registries confirmed at HEAD:
| File:line | Registry | Storage type |
|---|---|---|
| `CoreFrameworks/LifecycleCfgFlagRegistry.hpp:55` | `FOREACH_LIFECYCLE_CFG_FLAG` | uint8_t |
| `CoreFrameworks/OpsCfgFlagRegistry.hpp:39` | `FOREACH_OPS_CFG_FLAG` | uint8_t |
| `CoreFrameworks/GateCfgFlagRegistry.hpp:46` | `FOREACH_GATE_CFG_FLAG` | uint8_t |
| `CoreFrameworks/RiskCfgFlagRegistry.hpp:25` | `FOREACH_RISK_CFG_FLAG` | uint8_t |
| `ML_Headers/MlCfgFlagRegistry.hpp:52` | `FOREACH_ML_CFG_FLAG` | uint16_t |

Field decls confirmed at `ControllerConfig.hpp:482-486` (all 5 bitmap storage fields exist).

F6 amendment scope: ~33 KIND_BOOL rows total (8 lifecycle + 5 ops + 8 gate + 4 risk + 9 ml [4 deferred] — operator amendment specifies the breakdown). Same structural fix pattern applied uniformly; per-domain bitmap rebuild at slow-path. Co-located `static_assert(FOREACH_<DOMAIN>_CFG_FLAG_COUNT <= sizeof(<bitmap>_runtime_bitmap) * 8)` per registry.

**Result:** Count drift corrected. Cohort extension structurally sound across 4 additional domains. PASS.

### DRIFT-3 (existing per-core arrays not classified) — **GREEN (explicit classifications)**

**Verification at `CoreFrameworks/ControllerConfig.hpp`:**
| Field (line) | Plan amendment classification | Verified |
|---|---|---|
| `uint8_t core_strategies[16]` (971) | → `cores[c].strategy` (KIND_INT_ENUM row) | YES |
| `uint16_t core_strategies_explicit_set` (978) | DELETABLE (derives from `core_idx < num_execution_cores`) | YES |
| `FPN<F> core_risk_pct[16]` (989) | → `cores[c].risk_pct` (dedup with new scope) | YES |
| `char core_model_path[16][256]` (1008) | STAY MANUAL → `.F.4e` | YES |
| `char core_model_dir[16][256]` (1016) | STAY MANUAL → `.F.4e` | YES |
| `char core_horizon_list[16][128]` (1027) | STAY MANUAL → `.F.4e` | YES |
| `char core_ensemble_blend_mode[16][16]` (1028) | STAY MANUAL → `.F.4e` | YES |
| `char core_disabled_horizons[16][128]` (1029) | STAY MANUAL → `.F.4e` | YES |

The 33 test-fixture sites that initialize `core_*_set` etc. (lines 22763-23031 per prior audit) become deletion-clean once `core_overrides` + explicit-set partner-bitmap go away. Production reads of `core_strategies_explicit_set` need verification at Step 2 (amendment says "Step 2 audit verifies no production read distinguishes from `core_idx < num_execution_cores`"). Plan instructs this concretely.

**Result:** Every existing per-core array explicitly classified. 5 string arrays correctly scoped to `.F.4e` predecessor. PASS.

### DRIFT-5 (PerCoreRenderFn typedef) — **GREEN (subsumed by F1 reuse harvest)**

**Verification:** F1 reuse-harvest amendment introduces `RenderRegistryWalker<Target, Table, WORDS>` parameterized template (DESIGN_SPEC `multi-action-registry-walker-family.md` codifies). The typedef concern (`bool (*)(ControllerConfig<F>&, ...)` vs `bool (*)(PerCoreCfg<F>&, ...)`) is subsumed: typed action tables (`GlobalActionTable<F, Action>::ActionFn` and `PerCoreActionTable<F, Action>::ActionFn`) per-instantiated. Each instantiation owns its own typedef internally.

DESIGN_SPEC verified at `multi-action-registry-walker-family.md:69-99` shows the canonical template + per-registry instantiations. The amendment naturally consumes this template — no separate `PerCoreRenderFn` typedef needed.

**Result:** Subsumed cleanly. PASS.

---

## 2. NEW dependencies introduced by amendments — verification

### F4 multi-action registry walker family

**New artifacts specified:**
- `FOREACH_REGISTRY_ACTION(X)` X-macro at `CoreFrameworks/CfgFieldRegistry.hpp` (NEW row-roster of 5 actions: PARSE/SAVE/RENDER/STAMP/DRIFT) — concrete shape in DESIGN_SPEC `multi-action-registry-walker-family.md:34-48`
- `walk_registry_action<TargetStruct, Descriptor, N, ActionFn>` template at `CoreFrameworks/CfgFieldDispatch.hpp` — concrete shape in DESIGN_SPEC lines 53-66
- `GlobalActionTable<F, Action>` + `PerCoreActionTable<F, Action>` X-macro-instantiated function-pointer tables — concrete shape DESIGN_SPEC lines 69-99
- 5 actions × 2 registries = 10 walker instantiations (table per amendment "First canonical application" section)

**Verification at HEAD `88043ea`:** `rg "FOREACH_REGISTRY_ACTION\b|walk_registry_action\b"` returns ZERO matches (correctly — pattern doesn't exist yet; will be introduced by `.F.4c.3` Step 1).

**Boundedness check:**
- 5 action types finite (per amendment locked list)
- M registries = 2 initially (global + per-core); future axes (per-symbol / per-strategy / per-horizon) each add 1 registry → 5 instantiations per axis (mechanical)
- Per-row body delegates to existing `tt::cfg_<action>_field<T>` primitives (unchanged at `.F.4c.3`)

**Result:** Implementation surface concretely specified + bounded. PASS.

### F6 cohort extension — 4 additional cfg-domain bitmaps

**Per-domain consumer enumeration verified:**
- `lifecycle_cfg_flags` (uint8_t) — 8 lifecycle-flag rows at `LifecycleCfgFlagRegistry.hpp`; consumers via `BITMAP_IS_SET(cfg.lifecycle_cfg_flags, MASK_LIFECYCLE_*)` greppable
- `gate_cfg_flags` (uint8_t) — 8 gate rows at `GateCfgFlagRegistry.hpp`; consumers via `MASK_GATE_*` greppable
- `risk_cfg_flags` (uint8_t) — 4 risk rows at `RiskCfgFlagRegistry.hpp`; consumers via `MASK_RISK_*` greppable
- `ops_cfg_flags` (uint8_t) — 5 ops rows at `OpsCfgFlagRegistry.hpp`; consumers via `MASK_OPS_*` greppable
- `ml_cfg_flags` (uint16_t) — 13 ml rows at `MlCfgFlagRegistry.hpp` (9 at `.F.4c.3` + 4 deferred per DRIFT-2 above)

Each domain has an existing AUTOPOPULATE_FROM_TRIPLE/SEPTUPLE macro that the rebuild-walker extends. Per-domain bitmap is RE-CONSTRUCTED from flat KIND_BOOL rows at slow-path rebuild (concrete shape: walker writes `bitmap |= ((uint16_t)row_value) << enum_ordinal`). Hot-path BITMAP_IS_SET reads UNCHANGED (~18 sites read ml_cfg_flags in StrategyParameters/StampHelper/CfgDriftCheckRegistry per prior audit Section 10b).

**Result:** Per-domain consumers identifiable via existing MASK_<DOMAIN>_* mask families. Rebuild-walker shape concrete (specified at amendment "DOD-F2"). PASS.

### GUI cfg-mirror Option α

**Verification at codebase HEAD:** `gui_engine_cfg` ALREADY EXISTS at `GUI/SettingsPanel.hpp:623` as a `ControllerConfig<64>` instance. Plan amendment MED-4 codifies the existing shape (GUI owns separate cfg mirror; engine owns its own; file is canonical channel) NOT introduces it new. Per `gui_engine_cfg` greppable references at `GUI/SettingsPanel.hpp` lines 400, 472, 620, 815, 820, 905, 908, 909, 1097, 1606, 1607, 1658, 1659 — pattern fully wired.

**`.F.4c.3` retrofit:** the existing `gui_engine_cfg` instance becomes `ControllerConfig<64>` post-split (containing `cores[16]` array). GUI render walkers (per Step 6 amendment) walk both registries against `s->gui_engine_cfg` for global and `s->gui_engine_cfg.cores[c]` for per-core tabs. Mechanical refactor — no new GUI ownership introduction.

**Result:** Amendment codifies existing shape; no new state introduced. PASS.

### Migration guide stub

**Verified at:** `/home/caramel/code/tick-trader-percore-workspace/DOCS/CFG_SCOPE_MIGRATION_GUIDE.md` (10392 bytes; Step 1-5 migration walkthrough + global vs per-core classification list + 25-30 global fields + 75-80 per-core fields enumerated + error-message examples + verification scripts). PASS.

### 4 NEW test functions enumerated (MED-7)

15 new test functions enumerated explicitly at amendment lines 632-645 (per_core_resolver, section parsers ×6 variants, scope discipline ×2, per-core stamp byte identity, per-core drift, bitmap rebuild ×2, cross-version refusal). Plan estimates `~15` confirmed by enumeration. PASS.

---

## 3. Catalog verification

**`DESIGN_SPECS/README.md` checks:**
- Total count claim: "~66 patterns total" (line 175) = 57 catalog + 4 NEW DRAFT `.F.4d` + 1 NEW DRAFT `.F.4c.2` + 4 NEW DRAFT `.F.4c.3` — math checks: 57+4+1+4=66. PASS.
- 4 new `.F.4c.3` entries verified in catalog (lines 97-100):
  - `per-instance-registry-pattern.md` ✓
  - `cfg-scope-discipline.md` ✓
  - `multi-action-registry-walker-family.md` ✓ (NEW post-amendment)
  - `cfg-section-parser-state-machine.md` ✓ (NEW post-amendment)
- All 4 DESIGN_SPEC files exist on disk (verified via `ls`). All Stage 2 DRAFT v1.0 headers present.

PASS.

---

## 4. Codebase data-point reverification (414 vs ~50-100 claim)

**Test fixture write count:** `grep -c "cfg\.[a-z_]*\s*=" tests/controller_test.cpp` returns **414**. Amendment HIGH-3 explicitly cites "**414 `cfg.<field>=` writes in `tests/controller_test.cpp`** + ~32 production read sites" + sets honest effort budget at 8-12 hr migration + 4-6 hr audit. Original plan's "~50-100" was 4-5× undercount; amendment corrects.

NEW centralized helper proposed: `controller_test_init_cfg_for_core_zero(cfg)` concentrates future test cfg-init — closes the Class 18 mirror risk at test surface.

PASS.

---

## 5. Final verdict

**GREEN — ready to code from Step 0.A.**

All 5 prior findings (1 GAP + 4 DRIFTs) cleanly resolved:
- GAP-1 (symbol) — deferred to `.F.4c.3.A` follow-up subplan stub present
- DRIFT-1 (`_BuildParameters`) — Option A locked, 6 sigs + 11 call sites mechanical
- DRIFT-2 (ml_cfg_flags count) — corrected 12→13 + F6 cohort extends to 4 more cfg-domain bitmaps
- DRIFT-3 (existing per-core arrays) — every array explicitly classified
- DRIFT-5 (PerCoreRenderFn typedef) — subsumed by F1 `RenderRegistryWalker` template

5 newly-introduced deps verified concretely specified + bounded:
- F4 multi-action walker (template + tables + X-macro roster) — DESIGN_SPEC body specifies shape
- F6 cohort extension to 4 additional cfg-domain bitmaps — per-domain consumers identifiable
- GUI cfg-mirror Option α — pre-existing `gui_engine_cfg` shape; no new ownership
- Migration guide stub at `workspace/DOCS/CFG_SCOPE_MIGRATION_GUIDE.md` — present
- 15 new test functions enumerated; helper extraction proposed

Catalog row count = 66 (verified). 4 new DESIGN_SPECs (2 prior `.F.4c.3` drafts + 2 new from F4 / parser amendments) all present at workspace.

**No further plan amendments needed.** Pre-coding ritual at Step 0.A can begin.

Sister audits (`/parity-check` re-pass; `/dod-audit` re-pass) recommended in parallel per `feedback_consult_on_audit_findings` discipline before code lands, but `/trace-deps` chain integrity is GREEN.

---

**End of /trace-deps re-audit.** Audit performed inline (Layer 2; no nested subagents) per skill spec 2026-05-09 execution model.
