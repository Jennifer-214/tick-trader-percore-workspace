# /merge-scan report — v5.15.5.F.4c.3 (Global vs per-core registry split) — 2026-05-15

**Plan:** `plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3-global-vs-per-core-registry-split.md`
**Engine HEAD:** `88043ea` (post `.F.4c.1`); 3144 tests baseline
**Skill spec:** `claude-skills/merge-scan/SKILL.md` (post-2026-05-14 enhanced — Stage 0 DESIGN_PHILOSOPHY § 4 / § 7 preloaded)
**Date:** 2026-05-15

---

## Stage 0 — Preload context

**DESIGN_PHILOSOPHY § 4 (Latency cost framework):** shared atomic loads /
cfg accesses / conversions are reuse-audit targets. Slow path: merges >
50ns are worth proposing; < 10ns are noise. Hot path is UNTOUCHED at
.F.4c.3, so this scan focuses on SLOW-PATH + BOOT + GUI tier.

**DESIGN_PHILOSOPHY § 7 (Structural-fix family):** when reuse
opportunity is registry-shaped, propose X-macro registry vs helper
extraction. Direct patches reserved for one-off bugs; mirror patterns
get registries. Sister to Class 18 / Class 21 prevention.

**Sprint posture:** `.F.4c.3` composes 6 frameworks (universal cfg
registry + tt:: dispatch + bitmap dispatcher + per-instance registry +
sidecar/scope discipline + meta-registry FOREACH_LIVES_IN_STRUCT). This
scan asks: which of the NEW bodies introduced by `.F.4c.3` should be
themselves registry-parameterized so future axes (per-symbol /
per-strategy / per-horizon) compose mechanically?

---

## 1. Atomic load redundancies — N/A this ship

Hot path UNTOUCHED at `.F.4c.3` per Step 9 architectural gates +
`tools/calls_graph_diff.sh`. No new atomic loads proposed. Existing
slow-path atomic discipline (sp_last_tick_us shared by CheckWsStaleness
+ tail write per v5.12.1.A.2) preserved bytewise.

**Verdict:** clean.

---

## 2. Clock-read redundancies — N/A this ship

No new clock reads added; existing `clock_gettime` cluster pattern
unchanged. Boot path adds parser state machine but parses are
serial-once (no in-loop clock reads).

**Verdict:** clean.

---

## 3. Cfg-access redundancies (priority: SIGNIFICANT — Finding F2)

**Finding F2 — Slow-path per-core `cfg.cores[c].<field>` repetition.**

Plan Section H lists ~7 read-site files (RidgeBlender, ConfidenceScore,
ThompsonBandit, CoreModelZoo, StrategyParameters, MLStrategy,
ControllerEventLoop) that migrate `cfg.<field>` → `cfg.cores[c].<field>`.
Per-row at every consumer site = chatty + repetitive.

**The existing slow-path resolves once already**:
`ControllerConfig_ResolveForCore` produces a stack-local `resolved_cfg`
at `ControllerEventLoop.hpp:2324` THEN every downstream read uses
`resolved_cfg.<field>`. Under `.F.4c.3` the resolver is "deleted or
direct-read" per Step B deletion list, but the call-pattern survives:
**emit ONE per-core slice reference at slow-path entry; pass forward.**

**Proposal:**
```cpp
// Slow path entry (ControllerEventLoop.hpp:2321ish replacement):
// Before .F.4c.3:  ControllerConfig<F> resolved_cfg = ResolveForCore(*config, slot);
// After  .F.4c.3:  const PerCoreCfg<F>& core_cfg = config->cores[slot];
//                  // Pass core_cfg + (still-needed) global cfg refs down the call stack.
```

Downstream call signatures change from:
```cpp
void MLStrategy_BuildParameters(StrategyParams& sp, const ControllerConfig<F>& cfg, int core_idx) {
    sp.threshold = cfg.cores[core_idx].ml_buy_threshold;
    sp.tp_pct = cfg.cores[core_idx].ml_tp_pct;
    sp.sl_pct = cfg.cores[core_idx].ml_sl_pct;
    // ... ~15 reads per call site, each indexing through .cores[core_idx]
}
```
to:
```cpp
void MLStrategy_BuildParameters(StrategyParams& sp, const PerCoreCfg<F>& core_cfg) {
    sp.threshold = core_cfg.ml_buy_threshold;
    sp.tp_pct = core_cfg.ml_tp_pct;
    sp.sl_pct = core_cfg.ml_sl_pct;
}
```

**Reuse benefit:**
- Call-site readability: 1 dereference vs 2 per read
- Compiler-friendlier: hoisting `cfg.cores[core_idx]` once → register-cached pointer; per-field reads become direct offsets (compiler does this anyway via SROA, but explicit is clearer)
- Cognitive: `core_cfg.field` says "this is per-core scope" at the call site; `cfg.cores[c].field` repeats the contract once per row
- **Future safety:** if `.F.4f`/`.F.4g`/`.F.4h` reshape `cores[]` to AoS-vs-SoA layout (pending operator profiling per CLAUDE.local.md "open architectural decisions"), call sites that took `const PerCoreCfg<F>&` survive the re-layout unchanged. Call sites that did `cfg.cores[c].field` need re-grepping.

**Sites that benefit (~7 files × ~15-30 reads each ≈ 100-200 read sites):**
- `ML_Headers/RidgeBlender.hpp` (ridge_lambda / cost_penalty / min_ic_floor)
- `ML_Headers/ConfidenceScore.hpp` (confidence_* quartet)
- `ML_Headers/ThompsonBandit.hpp` (thompson_* triple)
- `ML_Headers/CoreModelZoo.hpp` (bandit_algorithm + winsor_* + reward)
- `Strategies/StrategyParameters.hpp` (composes from cfg reads)
- `Strategies/MLStrategy.hpp` (ml_buy_threshold + ml_tp_pct + ml_sl_pct)
- `CoreFrameworks/ControllerEventLoop.hpp` (slow-path rebuild reads)

**Effort estimate:** the migration grep+edit pass at `.F.4c.3` can ALREADY be cheaper if function signatures take `const PerCoreCfg<F>&` instead of `(const ControllerConfig<F>& cfg, int core_idx)`. Mostly a discipline directive on how the migration is performed, not extra LOC.

**Recommendation:** ADOPT. The migration the plan already calls for becomes naturally cleaner under this pattern. Document the convention in `cfg-scope-discipline.md` ("call sites consume per-core cfg via `const PerCoreCfg<F>& core_cfg` reference, never `cfg.cores[c]` repeated").

---

## 4. Function-body parallelism candidates (priority: HIGH — Finding F1)

**Finding F1 — Dual-registry walker template (Class 18 prevention).**

Plan declares `GlobalRenderTable<F>` + `PerCoreRenderTable<F>` (Step A
table) + Global tab + per-core tab walkers (Step F). Both walkers:
1. Iterate a precomputed bitmap mask via `CFG_FIELD_FOR_EACH_SET_BIT`
2. Look up `descriptor` from the registry's `g_*_field_descriptors[]` array
3. Dispatch through a function-pointer table indexed by FIELD_IDX_*
4. Handle section-header transitions + collapsing-header default-open + per-section strategy filter

**This is the same body shape parameterized only by `registry` + `struct_type`.** Pre-`.F.4c.3` the existing single walker already has this exact shape (see `GUI/SettingsPanel.hpp:1062-1101`).

**Proposal (canonical Class 18 prevention):**
```cpp
// Single template walker primitive — parameterized by:
//   - Registry: array of CfgFieldDescriptor (g_global_cfg_field_descriptors / g_per_core_cfg_field_descriptors)
//   - Mask:     precomputed render mask (g_global_cfg_render_mask / g_per_core_cfg_render_mask)
//   - Table:    function-pointer table (GlobalRenderTable<F>::fns / PerCoreRenderTable<F>::fns)
//   - Target:   cfg root struct OR cfg.cores[c] slice
//   - WORDS:    CFG_MASK_WORDS or PER_CORE_CFG_MASK_WORDS
template <typename Target, typename Table, size_t WORDS>
inline bool RenderRegistryWalker(
    Target& target,
    const CfgFieldDescriptor* descriptors,
    const uint64_t (&render_mask)[WORDS],
    const SettingsState* s,
    const char* cfg_path,
    bool default_open_filter)  // Trading/EntryFilters/EMA Gate get default_open
{
    bool changed = false;
    const char* current_section = nullptr;
    bool skip_section = false;
    for (size_t _w = 0; _w < WORDS; _w++) {
        uint64_t _word = render_mask[_w];
        while (_word) {
            const size_t _bit = static_cast<size_t>(__builtin_ctzll(_word));
            const size_t idx  = _w * 64 + _bit;
            const auto& desc = descriptors[idx];

            // Section header transition (lifted verbatim from current walker).
            if (!current_section || strcmp(current_section, desc.section) != 0) {
                current_section = desc.section;
                skip_section = false;
                int sec_strat = global_section_strategy(current_section);
                if (sec_strat >= 0 && !any_core_uses_strategy(s, sec_strat)) {
                    skip_section = true;
                    _word &= _word - 1;
                    continue;
                }
                bool open = default_open_filter && SectionIsDefaultOpen(current_section);
                if (!ImGui::CollapsingHeader(current_section, open ? ImGuiTreeNodeFlags_DefaultOpen : 0)) {
                    skip_section = true;
                    _word &= _word - 1;
                    continue;
                }
            }
            if (!skip_section) {
                ImGui::SetNextItemWidth(80);
                if (Table::fns[idx](target, desc, cfg_path)) changed = true;
            }
            _word &= _word - 1;
        }
    }
    return changed;
}

// Consumed by Global tab:
RenderRegistryWalker(s->gui_engine_cfg,
                     g_global_cfg_field_descriptors,
                     g_global_cfg_render_mask.words,
                     s, s->cfg_path, true);

// Consumed by per-core tab N:
RenderRegistryWalker(s->gui_engine_cfg.cores[c],
                     g_per_core_cfg_field_descriptors,
                     g_per_core_cfg_render_mask.words,
                     s, s->cfg_path, true);
```

**Reuse benefit:**
- ONE body for global + per-core tabs — Class 18 prevention by construction
- Future per-symbol / per-strategy / per-horizon axis registries get a render walker FREE — pass new descriptors[] + mask + table + target
- Section-header dedup logic + default-open whitelist + strategy filter live in ONE site

**Effort estimate:**
- Plan currently writes Global walker (Step 6) + per-core walker (Step 6 same step). Both bodies. Under this proposal: ONE walker + 2 call sites + per-row entry-point macros. Ship LOC roughly halves on Step 6.
- ~80 LOC saved at `.F.4c.3` ship; ~80 LOC × N future axes saved on every per-axis registry pattern application.

**Recommendation:** ADOPT. This is the canonical Class 18 prevention shape codified into the per-instance-registry-pattern DESIGN_SPEC currently in DRAFT v1.0.

**Companion:** the same single-walker template applies to **stamp emit**, **parser dispatch**, **save**, **drift check** — each is "iterate filtered mask + per-row action via function-pointer table." Today there is a separate body per consumer (parse vs save vs render). The dual-registry split is the canonical moment to introduce the parameterized walker primitive — see Finding F4 below.

---

## 5. State-field reuse — risk cohort (priority: HIGH — Finding F3)

**Finding F3 — kill_switch + drawdown + risk per-core cohort merge.**

The plan adds kill_switch_daily_loss_pct, kill_switch_drawdown_pct,
max_drawdown_pct, max_exposure_pct, enable_mtm_kill_switch to the
per-core registry (Section A row migrations).

**But the codebase already has parallel `core_risk_pct[16]` +
`core_max_drawdown_pct[16]` arrays + per-core parser branches** (ControllerConfig.hpp:989-994 + parser:2593+2604). These are
the pre-`.F.4c.3` per-core risk overrides — siblings of the cohort
this plan migrates.

**Cohort audit per CLAUDE.local.md "Cohort-audit rule" (2026-05-11):**
- `core_risk_pct[16]` → MIGRATE to `cores[c].risk_pct` (per-core scope, plan calls for this)
- `core_max_drawdown_pct[16]` → MIGRATE to `cores[c].max_drawdown_pct` (per-core scope; plan does this)
- `min_kill_loss` (FPN, single global) → CLASSIFY: global (absolute USDT floor doesn't vary per core) → KEEP global per scope-classification table
- `enable_mtm_kill_switch` (uint32_t global) → plan moves to per-core ✓
- `core_overrides[c].risk_full_size_threshold` + `risk_min_size_threshold` + `risk_min_size_pct` (per-core soft-risk-degradation) → already per-core via PerCoreOverrides; MIGRATE under per-core registry as flat rows (deletes the override mechanism)

**Proposal:** ensure the `.F.4c.3` Step 0.C scope-classification table EXPLICITLY enumerates the existing `core_*_pct` arrays + the `PerCoreOverrides::risk_*` triple as in-scope rows for the per-core migration, NOT leftover at global. Otherwise the .F.4c.3 ship leaves a partial migration where new fields go per-core but pre-existing fields still hold the legacy `cfg.core_X[16]` array shape — exactly the "half-migration" anti-pattern Step 9 architectural gates ban.

**Sites that benefit:**
- Deletes 4 fields from global cfg surface (`core_risk_pct[16]` etc.)
- Deletes 4 parser branches (lines 2593, 2604, +2)
- Deletes 4 init loops (lines 1647, 1649, +2)
- 1 fewer "is this field per-core" decision point

**Effort:** zero extra effort if Step 0.C enumerates these correctly; HIGH cost if missed (next time someone adds a risk-cohort sibling, the legacy arrays drift further apart).

**Recommendation:** ADOPT into Step 0.C classification table. Caramel reviews + confirms 4 fields are in-cohort.

---

## 6. Function-body parallelism — multi-walker family (priority: HIGH — Finding F4)

**Finding F4 — Multi-action registry walker family (parse / save / render / stamp emit / drift / cli-explain).**

Beyond the render walker (Finding F1), there are FOUR other registry-walker bodies in the codebase that all share shape:

| Walker | Current location | Action per row |
|---|---|---|
| Parse | `ControllerConfig.hpp:1900ish` registry walker block | strcmp(key) → tt::cfg_parse_field<T> |
| Save | `ControllerConfig.hpp:save_cfg` (similar) | tt::cfg_save_field<T> → file |
| Render | `GUI/SettingsPanel.hpp:1062-1101` | tt::cfg_render_field<T> via CfgRenderTable<F>::fns |
| Drift check | `ML_Headers/CfgDriftCheckRegistry.hpp` (FOREACH_STAMP_BOUND_CFG walker) | compare cfg.field vs stamp body |
| Stamp emit | `StampBoundCfgRegistry.hpp:FOREACH_STAMP_BOUND_CFG` consumer | snprintf cfg.field → canonical body |

Each is "iterate filtered mask + per-row dispatch through fn-pointer table over (descriptor, struct_field_ref)." The plan adds the dual-registry split as Class 21 prevention (no parallel descriptors), but does NOT propose unifying the WALKER body family. That asymmetry leaves Class 18 risk on the table for the FOUR non-render walkers when each gets dual-registry'd.

**Proposal:**
```cpp
// In CfgFieldRegistry.hpp (alongside FOREACH_METADATA_BIT + FOREACH_LIVES_IN_STRUCT):
//
// FOREACH_REGISTRY_ACTION(X) — tuple: X(lname, UpperName, FnTableType, MaskName)
// each row generates the typed registry walker for that action.
#define FOREACH_REGISTRY_ACTION(X) \
    X(render,     Render,     CfgRenderTable,   g_cfg_render_mask) \
    X(parse,      Parse,      CfgParseTable,    g_cfg_parse_mask) \
    X(save,       Save,       CfgSaveTable,     g_cfg_save_mask) \
    X(stamp_emit, StampEmit,  CfgStampTable,    g_cfg_stamp_emit_mask) \
    X(drift,      Drift,      CfgDriftTable,    g_cfg_stamp_emit_mask)
```

Each row produces an instance of `RegistryWalker<Target, Table, WORDS>`
parameterized for that action. ONE walker primitive (per-action body
differs; iteration scaffold is shared).

**Sites that benefit:**
- 5 walkers × 2 registries (global + per-core) = 10 future walker instances; with this pattern = 5 walker types × 1 template
- ANY future axis registry (per-symbol / per-strategy / per-horizon) gets all 5 walkers FREE on its declaration
- Class 18 prevention by construction — adding a new ACTION (e.g., snapshot serialize for hot-swap) = 1 row in FOREACH_REGISTRY_ACTION; not 5 new walker bodies

**Effort estimate:** ~150 LOC added at .F.4c.3 (FOREACH_REGISTRY_ACTION + RegistryWalker primitive) saves ~500 LOC at successor ships (.F.4d adds stamp emit walker over per-core registry; .F.4e adds cfg.example auto-gen consumer; .F.5+ adds per-axis registries that each need all 5 actions).

**Recommendation:** STRONG ADOPT. This is the canonical pre-coding moment per CLAUDE.md item 31 — "frameworks designed before second-application" rule. Building the multi-action walker family at .F.4c.3 means .F.4d / .F.4e / .F.4i / per-axis registries all consume it mechanically. Document in NEW spec
`DESIGN_SPECS/framework-patterns/multi-action-registry-walker-family.md` (or fold into per-instance-registry-pattern.md).

---

## 7. Cross-plan / cross-spec merge (priority: HIGH — Finding F5)

**Finding F5 — Section parser state machine reusability.**

Plan Step 3 introduces `[core N]` section parser state machine (lines 81-122 of plan). Today the codebase has ZERO INI-style sectioned parsers (grep verified — only `[strategy-lifecycle]` log prefix and `[core N]` log prefixes appear; no parser sections).

**The plan's parser logic is a primitive that will be reused:**
- `.F.4c.3` ship — `[core N]` for per-core cfg sections
- `.F.4d` audit calls for STAMP_BOUND derived filter — possibly per-core stamp parsing if stamp text format gets sectioned
- `v5.16+` multi-symbol DataStream — `[symbol BTCUSDT]` sections per the plan's own future-roadmap note (Section A, "boot-time uniformity check until multi-symbol DataStream support")
- `v5.x` future per-strategy / per-horizon / per-regime axes — same axis-registry pattern composes

**Proposal:**
Extract section-state-machine as a reusable primitive in `CoreFrameworks/CfgSectionParser.hpp` (NEW header):
```cpp
// Generic [<token> <id>] section parser state.
// section_lookup_fn(token, id) → registry & target slice pointer.
// Unknown section → operator-friendly error with migration hint.
struct CfgSectionParseState {
    enum { GLOBAL, AXIS_SECTION } state;
    uint32_t axis_idx;       // populated for axis sections
    const char* axis_token;  // "core" / "symbol" / "strategy" — populated for axis sections
    const CfgFieldDescriptor* active_registry;  // descriptors[] for active section
    void* active_target;     // cfg root or cfg.cores[c] or cfg.symbols[s]
};

// Detect [token id] header; transition state. Returns true if line consumed as header.
inline bool cfg_section_parse_header(CfgSectionParseState& st, const char* line, ...);
```

**Sites that benefit:**
- `.F.4c.3` parser body uses primitive (cleaner code; explicit state)
- Future per-axis ships (v5.16 multi-symbol, future strategy/horizon ships) — section parser FREE
- Unknown-key error helper centralized (migration hint format consistent)

**Effort:** ~80 LOC primitive added at .F.4c.3; saves ~80 LOC × future axes. Lower priority than F4 (multi-action walker family) because section parsing is less recurring than walker action.

**Recommendation:** MODERATE ADOPT — primitive worth extracting; lower urgency than F4. If time-boxed, defer to .F.5+ pre-coding gate when 2nd axis (per-symbol) is concrete.

---

## 8. Function-body parallelism — bitmap rebuild walker (priority: MEDIUM — Finding F6)

**Finding F6 — ml_cfg_flags A2 bitmap rebuild from KIND_BOOL rows.**

Plan Section A row 4 (under Section A, the per-core registry table)
describes the A2 hybrid migration: "all 12 ml_cfg_flags bits migrate
to flat KIND_BOOL rows in the per-core registry; runtime bitmap rebuilt
from rows at slow-path rebuild."

The current `MlCfgFlagRegistry.hpp:92-103`
`ML_CFG_FLAG_AUTOPOPULATE_FROM_SEPTUPLE` macro is the **manual** version
of this rebuild — it takes 7 explicit bool args + ORs them into a
target. Not registry-walker-driven.

**Proposal:** generate the bitmap-rebuild walker via the existing
`FOREACH_ML_CFG_FLAG` registry composed with FOREACH_PER_CORE_CFG_FIELD
filter:
```cpp
// At slow-path rebuild — walk per-core registry filtered by "former_ml_cfg_flag"
// metadata bit (NEW metadata bit at .F.4c.3); OR-set the corresponding bit.
// Branchless OR-reduction; compiler emits cmov per row.
inline uint16_t rebuild_ml_cfg_flags_from_per_core_bools(const PerCoreCfg<F>& core_cfg) {
    uint16_t flags = 0;
    #define X_OR(name, legacy_field, dl, sec, doc) \
        flags |= (core_cfg.legacy_field ? MASK_ML_CFG_##name : (uint16_t)0u);
    FOREACH_ML_CFG_FLAG(X_OR)
    #undef X_OR
    return flags;
}
```

This reuses the existing `FOREACH_ML_CFG_FLAG` registry (12 entries +
each row's bit position) and the existing MASK_ML_CFG_* constants
(auto-generated from the registry per
`MlCfgFlagRegistry.hpp:82-85`). Hot path BITMAP_IS_SET accessors remain
unchanged — only the SOURCE OF TRUTH for the bitmap moves from a
manual cfg parser to per-core KIND_BOOL row reads.

**Reuse benefit:**
- The 12 MASK_ML_CFG_* constants ALREADY exist + ALREADY have bit positions assigned → drop-in reuse
- Same pattern applies to FOREACH_LIFECYCLE_CFG_FLAG / FOREACH_GATE_CFG_FLAG / FOREACH_RISK_CFG_FLAG / FOREACH_OPS_CFG_FLAG — 4 more domain bitmaps that today get cfg parser handling at `ControllerConfig.hpp:2207-2258`. ALL FIVE domain bitmaps could rebuild from flat per-core KIND_BOOL rows under .F.4c.3.

**Effort:** ~80 LOC for the rebuild function + 60-row migration of FOREACH_*_CFG_FLAG entries to per-core KIND_BOOL rows. Plan currently scopes only ML domain at .F.4c.3 (A2 migration). Could expand to all 5 domains in the same ship.

**Recommendation:** STRONG ADOPT for ML domain (already in plan); CONSULT operator on extending to remaining 4 domains (lifecycle/gate/risk/ops) in the same ship since the structural pattern is identical + the rebuild logic is reused.

---

## 9. Per-core stamp emit reuse (priority: HIGH — Finding F7)

**Finding F7 — Per-core stamp emit walker reuses existing canonical-body builder.**

Plan Section E proposes "Each core's HMAC stamp covers ITS per-core
cfg fields (filtered by STAMP_BOUND metadata)" + per-core stamp fixture
+ Layer 5b hash lock per core.

The current StampBoundCfgRegistry walker (`StampBoundCfgRegistry.hpp:99`
FOREACH_STAMP_BOUND_CFG) is already X-macro-driven. It builds canonical
body via `STAMP_CFG_AUTOPOPULATE` (line 219+) — autopopulate pattern.

Plan does NOT propose introducing a new emit body; it should REUSE
the existing `FOREACH_STAMP_BOUND_CFG` walker template, just with
the cfg target SWITCHED from `cfg.<field>` (global) to `cfg.cores[c].<field>`
(per-core slice).

**Proposal:**
Parameterize the existing autopopulate walker by cfg target ref:
```cpp
// Was:
#define STAMP_CFG_AUTOPOPULATE(handle, cfg) \
    FOREACH_STAMP_BOUND_CFG(STAMP_CFG_AUTOPOPULATE_ONE)
// Cfg target ref baked into the X expansion as `cfg.field`.

// Becomes:
#define STAMP_CFG_AUTOPOPULATE_FROM_REF(handle, cfg_ref) \
    FOREACH_STAMP_BOUND_CFG(STAMP_CFG_AUTOPOPULATE_FROM_REF_ONE)
// X expansion uses `cfg_ref.field`.

// .F.4c.3 consumer for per-core stamp emit:
for (int c = 0; c < num_execution_cores; ++c) {
    STAMP_CFG_AUTOPOPULATE_FROM_REF(stamp_handle[c], cfg.cores[c]);
}
```

**Sites that benefit:**
- Reuses 200+ LOC of existing autopopulate walker logic
- Per-core stamp drift check at `CfgDriftCheckRegistry.hpp` follows the same parameterization
- Future per-axis stamp emit (per-symbol if model is per-symbol) FREE

**Effort:** ~30 LOC of macro refactor at `.F.4c.3` (autopopulate walker parameterization); ZERO new emit body. Single-call-site loop in boot.

**Recommendation:** STRONG ADOPT. Listed as already-implicit in plan Section E, but verify the implementation reuses the macro vs writing a parallel emit body. NO parallel body — extend existing autopopulate to take target ref.

---

## 10. Test fixture centralization (priority: MEDIUM — Finding F8)

**Finding F8 — Test cfg-init helper extraction opportunity.**

Plan Section I notes ~50-100 sites in `tests/controller_test.cpp`
that set cfg fields directly (`cfg.take_profit_pct = 3.0`). Grep
confirms: 231 `cfg.<field> = ` sites; 96 directly affected by the
fields moving global→per-core.

There is NO centralized test-cfg-init helper today (verified by
search for `make_test_cfg`, `setup_minimal_cfg`, `cfg_init_for_test`,
etc. — none found in `tests/`). Each test function does
`ControllerConfig<FP> cfg = ControllerConfig_Default<FP>();` then
overrides specific fields inline.

**Proposal:**
Extract a `tests/test_common.hpp` (per CLAUDE.md "Test file size
discipline" rule) with helpers:
```cpp
// Initialize cfg for a 1-core test.
template <unsigned F>
inline ControllerConfig<F> test_cfg_one_core() {
    auto cfg = ControllerConfig_Default<F>();
    cfg.num_execution_cores = 1;
    return cfg;
}

// Get reference to per-core slice for the canonical 1-core test.
template <unsigned F>
inline PerCoreCfg<F>& test_core_slice(ControllerConfig<F>& cfg) {
    return cfg.cores[0];
}
```

Test sites then read like:
```cpp
auto cfg = test_cfg_one_core<FP>();
auto& cc = test_core_slice(cfg);
cc.take_profit_pct = FPN_FromDouble<FP>(0.03);
cc.stop_loss_pct = FPN_FromDouble<FP>(0.015);
```

vs the mechanical migration:
```cpp
auto cfg = ControllerConfig_Default<FP>();
cfg.cores[0].take_profit_pct = FPN_FromDouble<FP>(0.03);
cfg.cores[0].stop_loss_pct = FPN_FromDouble<FP>(0.015);
```

The migration is mechanical either way. The helper extraction is OPTIONAL
QUALITY-OF-LIFE for future test additions; not load-bearing.

**Reuse benefit:**
- Test sites read more clearly post-migration
- Future cohort-axis migrations (per-symbol if it happens) have ONE site to update test helpers
- Aligns with CLAUDE.md "Test file size discipline" + queued v5.11.35 test split

**Effort:** ~30 LOC helper extract + grep+sed migration to use helpers; OPTIONAL — mechanical migration to `cfg.cores[0].<name>` is equally correct and what the plan calls for. Don't pad scope.

**Recommendation:** MODERATE — propose to operator as polish; ACCEPT only if Caramel wants test-quality improvement folded into this ship vs. queued for v5.11.35 split-ship.

---

## 11. MlCfgFlagRegistry residual usage (priority: LOW — Finding F9)

**Finding F9 — clean layer split runtime ↔ cfg-surface.**

Plan Section A.2 notes the registry's cfg-surface role ends but
"runtime BITMAP_IS_SET accessor pattern (MASK_ML_CFG_*) continues."

Verification grep:
- `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_*)` reads appear at: `ConfidenceScore.hpp:578`, `MLStatusPanel.hpp:173`, `StampBoundCfgRegistry.hpp:107`+108+110+...145, `CfgDriftCheckRegistry.hpp:250`+270+...289.
- All sites are: hot path (BG_Evaluate / SG_Evaluate via params slot) ✗ — NONE
- All sites are: slow path runtime branchless dispatch + stamp emit + drift check ✓

**Layer split verified:** operator-facing cfg surface (flat KIND_BOOL
rows in per-core registry; Section A.2) is DISTINCT from runtime
dispatch (ml_cfg_flags uint16_t bitmap accessed via BITMAP_IS_SET).
Slow-path rebuild produces the bitmap; runtime stays branchless.

**Recommendation:** clean; no merge needed; document the layer split
explicitly in `cfg-scope-discipline.md` or `per-instance-registry-pattern.md`
under "Runtime bitmap is downstream of flat row source-of-truth."

---

## 12. Branch-vs-branchless flags — N/A this ship

No new hot-path branches added. Plan Section G explicit: hot path
UNTOUCHED + `tools/calls_graph_diff.sh` confirms bytewise-identical.

**Verdict:** clean.

---

## Overall recommendation

### Top reuse-merge opportunities (act on at .F.4c.3 pre-coding audit gate)

**REQUIRED — operator should review before coding starts:**

1. **F1 — Dual-registry walker template** (HIGH; ~80 LOC saved in `.F.4c.3` + ~80 LOC × future axes saved long-term; Class 18 prevention by construction). The plan declares `GlobalRenderTable<F>` + `PerCoreRenderTable<F>` as parallel tables but does not declare a shared walker body. The fix: `RenderRegistryWalker<Target, Table, WORDS>` template consumed twice.

2. **F4 — Multi-action registry walker family** (HIGH; ~150 LOC at `.F.4c.3` saves ~500 LOC across `.F.4d` / `.F.4e` / `.F.5+` consumers). FOREACH_REGISTRY_ACTION roster of 5 actions (parse / save / render / stamp emit / drift) parameterized over registry + target struct. The canonical pre-coding moment per CLAUDE.md item 31.

3. **F2 — Per-core slice reference convention** (HIGH; cleanup, not LOC reduction). Function signatures take `const PerCoreCfg<F>& core_cfg` instead of `(cfg, core_idx)`. Forward-compat for `.F.4f`+ AoS-vs-SoA re-layout. Document in `cfg-scope-discipline.md`.

4. **F7 — Per-core stamp emit autopopulate parameterization** (HIGH; ~30 LOC refactor at `.F.4c.3`; zero new emit body). Existing `STAMP_CFG_AUTOPOPULATE` macro takes a cfg ref parameter; per-core consumer loops over `cfg.cores[c]`.

5. **F3 — Risk cohort migration must include pre-existing arrays** (HIGH; prevents half-migration). Step 0.C scope-classification table EXPLICITLY enumerates `core_risk_pct[16]` / `core_max_drawdown_pct[16]` / `PerCoreOverrides::risk_*` triple as IN-COHORT.

**STRONG-CANDIDATE — operator chooses:**

6. **F6 — Extend A2 bitmap-rebuild to all 5 domain bitmaps** (HIGH; consistency across cohort). Plan scopes ML only; lifecycle / gate / risk / ops follow identical pattern. Adds ~60-row migration but extinguishes the "cfg-flag domains parsed via X-macro at parser, walker varies per domain" residual asymmetry.

**MODERATE — defer-OK:**

7. **F5 — Section parser state machine primitive** (MODERATE; ~80 LOC). Worth it when 2nd axis (per-symbol) lands; not load-bearing for `.F.4c.3` alone.
8. **F8 — Test cfg-init helper extraction** (MODERATE; quality-of-life). Mechanical migration to `cfg.cores[0].<name>` already correct; helper is polish.

### Class 18 mirror-risk findings

- **F1 (dual-registry walker)** — the explicit Class 18 prevention; parallel walker bodies in the plan body are the symptom.
- **F4 (multi-action walker family)** — Class 18 prevention applied to the 5-action × 2-registry matrix.
- **F7 (stamp emit parameterization)** — Class 18 prevention by reusing existing autopopulate walker vs writing parallel per-core stamp emit.
- **F6 (bitmap rebuild)** — Class 18 prevention if extended to all 5 domains; otherwise ML rebuild + 4 manual parser branches drift apart.

### Future-application catalog (axes/patterns this ship's framework enables)

- **Per-symbol cfg registry** — `cfg.symbols[s].<field>` axis (when multi-symbol DataStream lands; v5.16+ per plan)
- **Per-strategy cfg registry** — strategy-axis tuning per Strategy enum (vs current per-core where the strategy is a row IN per-core)
- **Per-horizon cfg registry** — multi-horizon ensemble currently hardcoded; could be a registry axis (operator picks lambda per horizon)
- **Per-regime cfg registry** — regime-specific cfg overrides (today via `requires_cfg` gating expression; could be a per-instance axis)
- **Per-bandit-arm cfg registry** — bandit-specific tuning (mu_prior / precision_prior per arm) when bandit moves from 5-arm to N-arm scaling
- **Per-backtest-run cfg registry** — backtest cfg differs from engine cfg in subtle ways (already 4 LivesInStruct enum values exist; the meta-registry pattern composes)

EACH future axis above is "registry of N descriptors + 5 walkers + per-core-style storage layout." If `.F.4c.3` ships F1 + F4 + F7 together, each future axis = ~1 row in FOREACH_REGISTRY + descriptor declarations + automatic walker dispatch. WITHOUT F1/F4/F7, each axis = duplicate 5 walker bodies + duplicate stamp-emit body + ~500 LOC repeated per axis.

### Recommendation: SUBSTANTIAL REUSE HARVEST

The plan as written ships a working per-core split but does NOT
maximize the framework reuse opportunity at-hand. The 5 high-priority
findings (F1 + F4 + F2 + F7 + F3) all compose with the plan's existing
sequencing — they don't require re-architecting; they reuse the
existing primitives MORE thoroughly.

Quantitatively:
- LOC saved at `.F.4c.3`: ~150-250 (walker dedup + autopopulate refactor)
- LOC saved per future per-axis ship: ~400-600 (walker family + section parser + stamp emit + drift check all free)
- Classes prevented: 18 (mirror data flow) + 21 (parallel descriptors) — both reinforced structurally
- Frameworks codified: 1 NEW (multi-action registry walker family DESIGN_SPEC); 2 STRENGTHENED (per-instance-registry-pattern + universal-registry-bitmap-dispatcher both gain explicit "any axis, any action, any target" parameterization examples)

**Consult-before-coding recommendation:** present F1/F2/F3/F4/F7 to
Caramel as adoption-candidates for `.F.4c.3` Step 0/1 scope refinement.
F6/F5/F8 are optional polish.

Caramel decides which to fold in; this scan does not auto-proceed.

---

## File-path index (absolute)

- Plan: `/home/caramel/code/tick-trader-percore-workspace/plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3-global-vs-per-core-registry-split.md`
- Registry: `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/CfgFieldRegistry.hpp`
- Dispatch: `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/CfgFieldDispatch.hpp`
- ControllerConfig: `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerConfig.hpp`
  - PerCoreOverrides struct + PER_CORE_OVERRIDE_FIELDS macro: lines 117-270
  - `core_risk_pct[16]` + `core_max_drawdown_pct[16]` (pre-existing per-core fields): lines 985-994
  - `ControllerConfig_ResolveForCore`: lines 1270-1301
  - Parser body (`ControllerConfig_Load`): lines 1800-2750+
  - Parser per-core branch: lines 2659-2742
- ml_cfg_flags registry: `/home/caramel/code/FoxML_Trader_v2/ML_Headers/MlCfgFlagRegistry.hpp`
- Stamp registry: `/home/caramel/code/FoxML_Trader_v2/ML_Headers/StampBoundCfgRegistry.hpp`
- SettingsPanel walker: `/home/caramel/code/FoxML_Trader_v2/GUI/SettingsPanel.hpp:1062-1101`
- CfgRenderTable<F>: `/home/caramel/code/FoxML_Trader_v2/GUI/SettingsPanel.hpp:172-199`
- Per-core tab generator: `/home/caramel/code/FoxML_Trader_v2/GUI/SettingsPanel.hpp:1159+`
- Tests: `/home/caramel/code/FoxML_Trader_v2/tests/controller_test.cpp` (231 `cfg.<field> =` sites; no central init helper)

**End of merge-scan report.**
