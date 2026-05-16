# Cfg scope discipline

**Stage:** Stage 2 DRAFT v1.0 (drafted ahead of first canonical application at v5.15.5.F.4c.3)
**Promotes to:** Stage 3 ACTIVE v1.0 at `.F.4c.3` ship close
**Closes:** Class 24 (Capability-cfg surface mismatch) at the architectural-scope-decision level
**Sister specs:** `cfg-flag-eligibility-criteria.md` (boolean cfg-flag eligibility), `categorical-tag-applicability-pattern.md` (which strategies/op-modes/regimes a row applies to), `per-instance-registry-pattern.md` (the framework that consumes this discipline's classification)

---

## Summary

When adding a new cfg field, the FIRST question is: **what scope does this field live at?** This DESIGN_SPEC codifies the decision discipline + scope categories + anti-patterns. Operator-refined 2026-05-15: the default scope for trading/ML/risk fields is **per-core**, not global. Global is reserved for system/training/recording/engine-wide-mode/acknowledgment fields. The "global default + per-core override" pattern is FORBIDDEN — it's the recurring anti-pattern this spec eliminates structurally.

## The decision question

**"Could two cores reasonably want different values for this knob?"**

| Answer | Scope |
|---|---|
| YES — *"core 0 running SimpleDip wants different ridge_lambda than core 1 running ML"* | **PER-CORE** registry |
| NO — *"this controls engine startup; all cores see the same engine"* | **GLOBAL** registry |
| MIXED — *"it could vary but I want to enforce uniformity for safety"* | **GLOBAL** registry (uniformity is the intent; explicit) |
| UNCLEAR — *"hmm maybe"* | Default to **PER-CORE**. Operator-preferred default when in doubt (per Caramel 2026-05-15: *"finer control, no global overrides"*). |

The criterion errs toward per-core. If you're unsure, per-core is the right default — the alternative ("global default + override later") is the anti-pattern.

## Scope categories

### GLOBAL — fields that genuinely apply engine-wide

A cfg field belongs in `FOREACH_GLOBAL_CFG_FIELD` iff one of these conditions holds:

1. **System / OS configuration** — applies before any core runs trading logic. Examples: `num_execution_cores` (decides core count itself), `engine_mode`, `engine_arch`, `require_mlockall`, `init_arena_use_hugepages`.

2. **Training-time hyperparameter** — operates outside the trading loop, during model training. Examples: `xgb_train_nthread`, `xgb_subsample`, `xgb_colsample_bytree`, `xgb_seed`, `multi_horizon_max_threads`, `feature_collect_max_gb`, `held_out_stamp_secret`, `held_out_gate_strict`.

3. **File I/O policy** — applies uniformly across cores (no value in per-core variation). Examples: `record_ticks`, `record_depth`, `record_max_days`, `auto_stamp_on_held_out`.

4. **Engine-wide mode / lifecycle** — applies uniformly by intent. Examples: `trading_mode` (paper/shadow/live — the whole engine is one or the other; mixing live + paper across cores is a safety nightmare), `model_verify_strict`, `reconcile_mode`, `oms_event_log_mode`, `oms_bench_enabled`, `use_aot_inference`, `pay_fees_in_bnb`, `sharded_force_synthetic`.

5. **Explicit acknowledgments** — opt-in safety gates that apply across the whole engine. Examples: `acknowledge_hardcoded_strategy_in_live`, `acknowledge_hot_swap_with_open_positions`, `allow_cross_major_engine`.

6. **Boot-time operational tuning** — read once at boot; applies uniformly. Examples: `slow_path_max_secs`, `slow_path_pin_offset`.

Total expected: ~25-30 fields in the global registry at `.F.4c.3`.

### PER-CORE — fields that own trading behavior

A cfg field belongs in `FOREACH_PER_CORE_CFG_FIELD` iff it controls anything a core does to trade. This is the DEFAULT for trading + ML + risk + regime + strategy + entry + exit fields. **Including kill switches and max drawdown** (per Caramel's 2026-05-15 directive — different cores warrant different risk envelopes).

Categories of per-core fields:

- **Strategy selector + per-core model paths**: `strategy`, `model_path`, `model_dir`, `horizon_list`, `ensemble_blend_mode`, `disabled_horizons`
- **Trading params**: `take_profit_pct`, `stop_loss_pct`, `fee_rate*`, `slippage_pct`, `risk_pct`, `fee_floor_mult`
- **Entry filters**: `entry_offset_pct`, `offset_min/max`, `volume_multiplier`, `spacing_multiplier`, `min_long_slope`, `min_buy_delta`, `vwap_offset`, `min_stddev_pct`
- **Regime thresholds**: `regime_slope_threshold`, `regime_crossover_threshold`, `regime_strong_crossover`, `regime_r2_threshold`, `regime_hysteresis`
- **ML/Bandit/Confidence/Ridge/Winsor/Thompson**: `ml_*`, `bandit_algorithm`, `thompson_*`, `ridge_*`, `winsor_*`, `confidence_*`, `barrier_blend_mode`, `exit_blender_mode`
- **Exits**: `tp_*`, `sl_*`, `hold_score`, `time_exit`, `partial_exit_*`, `breakeven_*`
- **Strategy-specific tuning**: `momentum_*`, `simpledip_*`, `mr_*`, `emacross_*`
- **Gate recovery**: `sl_cooldown_*`, `recovery_delay_secs`
- **Per-core risk envelope** (NEW per Caramel 2026-05-15): `kill_switch_daily_loss_pct`, `kill_switch_drawdown_pct`, `max_drawdown_pct`, `max_exposure_pct`, `enable_mtm_kill_switch`
- **Symbol axis** (NEW per Caramel 2026-05-15): `symbol` migrated to per-core with boot-time uniformity enforcement (all cores must share symbol) until multi-symbol DataStream support ships. Forward-compatibility — cfg surface ready when ingest path grows
- **A2 bitmap-bool migration** (NEW per Caramel 2026-05-15): all 12 `ml_cfg_flags` bits migrate to flat `KIND_BOOL` rows in the per-core registry (`ridge_within_horizon`, `ridge_across_horizons`, `confidence_composite_enabled`, `exit_blender_mode`, `bandit_enabled`, `exit_bandit_enabled`, `per_horizon_barrier_blend`, `foxml_vol_scaling_enabled`, `confidence_enabled`, `lazy_rebuild_enabled`, `use_exit_model`, `confidence_composite_enabled`). Runtime bitmap is REBUILT from rows at slow-path rebuild (one-time per cfg-reload); hot path keeps branchless mask dispatch via `gate_state->flags & MASK` unchanged. Cfg surface = flat rows uniform with other cfg fields.

Total expected: ~75-80 fields per-core × 16 max cores = up to 1280 cfg row-instances; in practice operator runs ~2-8 cores so 150-640 row-instances.

### Future axes — anticipated extensions

When adding a NEW axis (per-symbol, per-strategy, per-horizon, per-regime), apply the same decision question recursively:

- "Could two symbols reasonably want different values for this knob?" → if YES, the field belongs in the per-symbol registry; if NO, the field stays at whatever its current parent scope is.
- Decision: a field could be **per-core × per-symbol** (a row instance per `(core, symbol)` pair) if both axes warrant variation. The framework supports arbitrary axis composition via nested per-instance struct generation.

See `per-instance-registry-pattern.md` § "Anticipated future axes" for the catalog.

## Anti-patterns — FORBIDDEN at this discipline

### Anti-pattern 1: Global default + per-instance override

The pre-`.F.4c.3` shape:

```cpp
// FORBIDDEN — Class 24 anti-shape
struct ControllerConfig {
    FPN<F> take_profit_pct;           // global default
    PerCoreOverrides<F> core_overrides[16];  // per-core override values
    // ... resolver picks override-or-global at slow-path rebuild
};
```

Why FORBIDDEN: this shape carries TWO sources of truth for "what's core C's take_profit_pct?" — the global value AND the override-or-not state. Operator must reason about inheritance. Stamp body has to encode resolved-per-core (which adds complexity to drift check). Settings panel must show "global value + per-core override badge" which is the UX problem this discipline closes.

Correct: every trading field is in `FOREACH_PER_CORE_CFG_FIELD`; each core's `cores[c].take_profit_pct` is THE value. No global default; no resolver; no override-or-not state.

### Anti-pattern 2: Per-instance fields in the global registry "for convenience"

Someone might be tempted to put `take_profit_pct` in the global registry because "most cores use the same value anyway" or "easier to type once than four times." This is the wrong tradeoff:

- Easier to type once → cfg file is shorter by ~50 lines × N cores
- Cost: brings back the override-or-not state; every core has to reason about whether its value comes from global or from override

The hard-break decision at `.F.4c.3` accepts the cfg file gets longer (~200 lines for 4 cores × 50 fields) in exchange for eliminating the inheritance confusion entirely. Every cfg line is intentional + traceable to a specific core.

### Anti-pattern 3: Mixing scopes in the same field family

Sibling fields should ALWAYS share the same scope. If `ridge_lambda` is per-core, then `ridge_cost_penalty` and `ridge_min_ic_floor` must also be per-core — they're part of the same Ridge configuration cohort; splitting them across scopes creates confusing operator semantics (set λ per-core, but penalty is engine-wide?).

The cohort-audit rule (CLAUDE.local.md, set 2026-05-11) enforces this: when a new field has 2+ semantic siblings, all-or-none must migrate to the same scope.

### Anti-pattern 4: Backward-compat shim that re-introduces the override pattern

After hard-break, someone might propose "legacy `take_profit_pct=3.0` at global scope → set on ALL cores via WARN" — that's re-introducing the global-default mechanism. FORBIDDEN. Legacy global trading keys = hard error with migration hint. The migration guide is the operator's path forward; the parser does NOT silently rescue.

## Examples — concrete field classifications

(See full classification table at `plans/plan_checks/cfg-field-scope-classification-2026-05-15.md` produced at `.F.4c.3` Step 0.C.)

### GLOBAL examples + rationale

| Field | Rationale |
|---|---|
| `num_execution_cores` | Decides core count itself; meta-level over the per-core axis |
| `trading_mode` | Engine-wide mode; mixing live + paper across cores is a safety nightmare |
| `xgb_train_nthread` | Training-time only; operates outside trading loop |
| `record_ticks` | File I/O policy; uniform across engine; no value in per-core variation |
| `held_out_stamp_secret` | Engine-wide HMAC secret; per-core is meaningless (all cores' stamps share the secret) |
| `require_mlockall` | OS boot-time configuration; applies before any core runs |

### PER-CORE examples + rationale

| Field | Rationale |
|---|---|
| `take_profit_pct` | Strategies have different optimal TPs (Momentum vs SimpleDip); each core picks its own |
| `risk_pct` | Each core has its own risk envelope per Caramel's allocation principle |
| `ridge_lambda` | Different model regimes warrant different regularization strength |
| `bandit_algorithm` | Caramel's design intent: different cores can run different bandit algorithms (Exp3 op + Thompson ghost, etc.); per-instance ghost-training |
| `kill_switch_daily_loss_pct` | Per Caramel 2026-05-15: conservative core gets tight kill; experimental core gets loose kill |
| `max_drawdown_pct` | Same rationale: per-core risk envelope |
| `model_dir` | Per-core model loading (already per-core today; preserved in new registry) |

### EDGE CASES — decisions documented

- `trading_mode` (paper/shadow/live): GLOBAL by safety intent (mixing paper + live cores = nightmare). Even though theoretically each core could have its own mode, the discipline says NO — uniformity is the SAFETY-CRITICAL intent.
- `reconcile_mode` (STRICT/WARN/AUTO_SYNC): GLOBAL because reconcile applies to the OMS layer which is engine-wide (not per-core).
- `xgb_seed`: GLOBAL because training is engine-wide (one training pipeline produces models for all cores).
- `model_verify_strict`: GLOBAL because model-verify-policy applies uniformly to all cores' model loads.
- `held_out_gate_strict`: GLOBAL same reason.
- `symbol`: PER-CORE (decided 2026-05-15) — even though single-symbol today is the runtime constraint (one WS feed per engine), cfg surface is per-core to future-proof for multi-symbol DataStream support. Boot-time uniformity check enforces "all active cores have the same symbol" until DataStream is multi-symbol. Operator-facing cfg shape doesn't need to change when DataStream grows.
- `ml_cfg_flags` bits (12 booleans like ridge_within_horizon, confidence_enabled, exit_blender_mode, ...): PER-CORE flat KIND_BOOL rows (A2 hybrid migration, decided 2026-05-15). Runtime bitmap rebuilt from rows at slow-path rebuild. Decision rationale: maximum framework uniformity at cfg surface; preserves runtime hot-path mask dispatch unchanged; future-add cost = 1 row in per-core registry.

## Application discipline — going-forward rule

CLAUDE.local.md going-forward rule (set 2026-05-15, codified at `.F.4c.3`):

> **Per-core scope by default for trading config.** Trigger: any new cfg field touching trading / ML / risk / regime / strategy / entry / exit logic → answer the scope decision question; default to per-core. If proposing GLOBAL scope for a trading-adjacent field, document the rationale (one of the 6 GLOBAL categories) at the field's registry row declaration as a comment. Reviewers reject GLOBAL placement of trading-adjacent fields without documented rationale.

Sister to:
- `cfg-flag-eligibility-criteria.md` (set 2026-05-09 at `.F.4` series start) — when a boolean cfg is registry-eligible
- `categorical-tag-applicability-pattern.md` (set 2026-05-14) — categorical applicability metadata
- Cohort-audit rule (set 2026-05-11) — sibling fields share scope + metadata

## Consumer function signatures over per-core slices

The cfg-scope-discipline applies not just to FIELD DECLARATION but also to CONSUMER FUNCTION SIGNATURES that read per-core fields. The structural rule:

> **Per-core consumer functions take `const PerCoreCfg<F>*` (single-param), NEVER `const ControllerConfig<F>*`.** Genuinely-global reads (e.g., `poll_interval` for tick→time conversion) are CALLER-RESOLVED as scalar args, not in-function reads through a passed cfg pointer.

Canonical example — strategy `_BuildParameters` family at `Strategies/StrategyParameters.hpp`:

```cpp
// CORRECT — single per-core slice param; globals (if any) as explicit scalars
template <unsigned F, unsigned W = 128>
inline void SimpleDip_BuildParameters(
    const RollingStats<F, W>* rolling,
    const PerCoreCfg<F>* core_cfg,        // per-core slice — body reads core_cfg->X
    FPN<F> allocated_balance,
    GateParameters<F>* out,
    /* ... other args ... */
);

// Caller pre-resolves globals when needed:
ML_BuildParameters(rolling, rolling_long, core_cfg, allocated_balance, out, model_ctx, now_us,
                    /*global*/ (int)cfg.poll_interval);   // poll_interval extracted at call site
```

```cpp
// FORBIDDEN — full cfg pointer = scope-erosion bug bait (see Class 25)
template <unsigned F, unsigned W = 128>
inline void SimpleDip_BuildParameters(
    const RollingStats<F, W>* rolling,
    const ControllerConfig<F>* config,   // <-- WRONG: per-core fn taking full cfg
    /* ... */
);
```

### Why the single-param sig matters

If a per-core consumer fn takes `const ControllerConfig<F>*`, the FIELD READS inside the body can land anywhere — `config->take_profit_pct` reads the FLAT field, not `config->cores[c].take_profit_pct`. Under the two-storage shadow window of `.F.4c.3` Step 2, this works accidentally because `PopulateCoresFromFlat` syncs the values. After Step 7 deletes the flat fields, the read becomes a compile error (good — caught early). But the WORSE case is: future contributor adds a new consumer fn, reaches for `const ControllerConfig<F>*` "because it's simpler," reads `config->some_per_core_field` (flat) — code works for core 0 but silently uses core 0's values for ALL cores. That's the Class 25 anti-pattern.

The single-param sig makes this impossible by construction: there's no flat-field access path through `core_cfg`. Every per-core read goes through the per-core slice.

### Grep signatures — anti-pattern detection

Audit hooks (firable via `/dod-audit` or `/bug-check`). Most are now build-failing via `tools/check_per_core_registry_integrity.py` at `.F.4c.3` WIP2d-0; greps remain for manual audit or external-PR review.

```bash
# A1: Consumer fn taking ControllerConfig<F>* (forbidden for per-core consumers)
# Class 25 anti-pattern; closed structurally at WIP2g flat-field deletion.
rg -n "(BuildParameters|_Tick|_Adapt|_Rebuild)\(.*const ControllerConfig<F>\*" --type cpp

# A2: Per-core field read through `config->` instead of `core_cfg->` (in any fn taking PerCoreCfg<F>*)
# Heuristic: a fn body containing both `core_cfg` and `config->` is suspicious — likely two-param
# legacy that needs cleanup. Mixed-scope = Class 25 risk.
rg -nP "(?s)PerCoreCfg<F>\*.*?config->[a-z_]+" --multiline --type cpp

# A3 (NEW at WIP2d-0): Parallel array shadowing per-core registry row.
# Scans ControllerConfig.hpp for `<type> core_<name>[(16|MAX_EXECUTION_CORES)]` declarations.
# Every match MUST appear inside FOREACH_MANUAL_PER_CORE_FIELD X-macro expansion;
# stray declarations elsewhere = Class A bug shape.
rg -nP '^\s+\S+\s+core_\w+\[(16|MAX_EXECUTION_CORES)\]' CoreFrameworks/ControllerConfig.hpp

# A4 (NEW at WIP2d-0): Anti-pattern 1 consumer (global default + per-core override).
# Co-occurrence of cfg.<X> and cfg.core_overrides[<c>].<X> for same field X in same scope.
# UNEXPRESSIBLE after WIP2f deletes core_overrides[16]; signature catches regression attempts.
rg -nP '(?s)cfg\.(\w+).*?cfg\.core_overrides\[\w+\]\.\1' --type cpp

# A5 (NEW at WIP2d-0): Manual struct field bypass in PerCoreCfg<F>.
# After WIP2d-0 X-macro struct gen, PerCoreCfg<F> body should be EMPTY except for the
# FOREACH_PER_CORE_CFG_FIELD(EMIT_PER_CORE_CFG_STRUCT_FIELD) call. Any other declaration
# inside the struct body = Class B bug shape.
# (Build-failing via CI; this grep is for manual cross-check.)
rg -nP -A50 'struct alignas\(64\) PerCoreCfg' CoreFrameworks/ControllerConfig.hpp | \
    rg -v 'FOREACH_PER_CORE_CFG_FIELD|alignas|^[\s-]*(struct|template|};|//|static_assert|$)'

# A6 (NEW at WIP2d-0): Transitional exemption rot detection.
# MANUAL_FIELDS_INVENTORY.md TRANSITIONAL entries with missing or already-shipped migration triggers.
# (Build-WARN via CI; full automation at .F.4d.)
rg -nP 'TRANSITIONAL.*delete at' DOCS/MANUAL_FIELDS_INVENTORY.md
```

False-positive cases (documented exemptions):
- `ControllerConfig_ResolveForCore` itself — the resolver that produces per-core views; takes `const ControllerConfig<F>&` by design. (Deleted at WIP2f.)
- Boot-time engine init paths that legitimately need the full cfg (multi-core setup; non-trading consumer; documented per Class 25 catalog).
- `ControllerConfig_NormalizeForMode` — operates on the whole cfg by design.
- `FOREACH_MANUAL_PER_CORE_FIELD` X-macro expansion in ControllerConfig.hpp — A3 signature matches BUT the regex check excludes the X-macro expansion area (delimited by macro define + EMIT_MANUAL_PER_CORE_DECL undef).

### CI enforcement (build-failing at WIP2d-0)

The grep signatures above are codified in `tools/check_per_core_registry_integrity.py` (NEW at `.F.4c.3` WIP2d-0). The script runs at every `build.sh` invocation pre-compile:

1. PerCoreCfg<F> field declarations cross-checked bidirectionally against FOREACH_PER_CORE_CFG_FIELD
2. Parallel arrays must appear inside FOREACH_MANUAL_PER_CORE_FIELD expansion region
3. FOREACH_MANUAL_PER_CORE_FIELD ↔ MANUAL_FIELDS_INVENTORY.md bidirectional cross-check
4. No name duplication between FOREACH_PER_CORE_CFG_FIELD + FOREACH_MANUAL_PER_CORE_FIELD
5. Anti-pattern 1 consumer scan (WARN; becomes ERROR after WIP2f)
6. TRANSITIONAL exemption trigger sanity (WARN on missing; ERROR on already-shipped triggers)

Violations BREAK the build with diff suggesting registry migration. New per-core fields flow through `FOREACH_PER_CORE_CFG_FIELD` mechanically (1-row addition); no other path exists.

### Caller-resolved globals — when to use scalar args vs adding a global param

- **One-off global read (1-2 sites):** caller pre-resolves + passes as scalar arg. Documented edge; minor sig growth.
- **Many global reads (5+):** consider whether the consumer should actually be DECOMPOSED into per-core part + global-resolved part. The per-core part reads only per-core fields; the global-resolved part returns pre-resolved scalars the per-core part consumes.
- **NEVER:** add `const ControllerConfig<F>* config` "for convenience" alongside `const PerCoreCfg<F>* core_cfg`. Two-param sig silently re-introduces Class 25.

### Future axes — same discipline

When per-symbol / per-strategy / per-horizon / per-regime axes ship (per `per-instance-registry-pattern.md` § "Anticipated future axes"), per-axis consumer fns follow the same single-param discipline:

```cpp
PerSymbol_BuildIngestPipeline(const PerSymbolCfg<F>* symbol_cfg, ...);
PerHorizon_TrainModel(const PerHorizonCfg<F>* horizon_cfg, ...);
```

Globals are caller-resolved; cross-axis access happens at the caller, never inside the per-axis fn body.

## Why this discipline matters — Class 24 structural close

Class 24 (Capability-cfg surface mismatch) is the recurring bug where ML capability exists in code but cfg/Settings/stamp/drift surface doesn't expose it. The cfg-scope-discipline closes this class at the architectural-decision level:

- **Pre-`.F.4c.3`**: trading field could live anywhere (global with override; or just global; or partially per-core). Discipline-less. Result: 17 ML fields shipped invisible to operator (`.F.4c.1` paper-test surfaced).
- **Post-`.F.4c.3`**: trading field BELONGS in per-core registry by discipline. New ML feature add → 1 row in per-core registry → Settings panel renders it on per-core tabs automatically (via bitmap dispatcher + tt:: dispatch). "I added the feature in ML code but forgot the cfg surface" failure mode dies structurally.

Plus: the cfg-↔-ML surface-alignment going-forward rule (CLAUDE.local.md, set 2026-05-14 at `.F.4c.1`) fires `/ml-audit` at sub-ship close for any ship touching ML capability. The scope discipline is the FIRST line of defense (correctness at field-add time); the surface-alignment audit is the SECOND line (detection at ship close).

## Reference implementations

(Populates at Stage 3 ACTIVE — shipped sites get file:line refs back-linked here.)

- (pending) `plans/plan_checks/cfg-field-scope-classification-2026-05-15.md` — full classification table for current FOREACH_CFG_FIELD rows (Step 0.C of `.F.4c.3`)
- (pending) `CoreFrameworks/CfgFieldRegistry.hpp` — `FOREACH_GLOBAL_CFG_FIELD` + `FOREACH_PER_CORE_CFG_FIELD` declarations
- (pending) `workspace/DOCS/CFG_SCOPE_MIGRATION_GUIDE.md` — operator-facing migration guide (manual rewrite checklist)

## Cross-references

- `DESIGN_SPECS/per-instance-registry-pattern.md` (NEW; sister spec) — the framework that consumes this discipline's GLOBAL vs PER-CORE classification
- `DESIGN_SPECS/cfg-flag-eligibility-criteria.md` — sister: when a boolean is cfg-flag-eligible
- `DESIGN_SPECS/categorical-tag-applicability-pattern.md` — sister: which strategies/op-modes/regimes a row applies to
- `DESIGN_SPECS/structural-fix-preferred-decision-framework.md` — meta-decision motivating this discipline
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 24 — structural close at per-core scope discipline
- CLAUDE.md item 31 — framework discipline meta-principle
- CLAUDE.local.md going-forward rules — "Per-core scope by default for trading config" (set 2026-05-15)

---

## Stage 3 ACTIVE amendments (added at v5.15.5.F.4c.3 r-8 ship close, 2026-05-15)

Two new canonical consumer-fn-sig shapes are first-applied at the `.F.4c.3` B.1 ship. Added to this spec to durably codify the discipline:

### Shape: consumer over per-core array (multi-slot dispatch)

When a consumer fn iterates ALL per-core slices (force-close, flatten-all, reconcile multi-fill replay), the canonical sig is:

```cpp
template <unsigned F>
inline int fn_name(/* primary state */, const PerCoreCfg<F>* cores, /* other args */);
```

Caller passes `&cfg.cores[0]` (full array base). Body indexes `cores[slot]` per-iteration. Type-safe against Class 25 (no `ControllerConfig<F>*` access). Future axis additions (per-symbol, per-strategy) extend by adding additional slice-pointer params — STRUCTURALLY ENFORCED + type-checked.

**First canonical applications (v5.15.5.F.4c.3 r-1/r-2):**
- `CoreFrameworks/ShardedLiveSafety.hpp::EngineSharded_ForceCloseOnShutdown` — boot/safety force-close
- `CoreFrameworks/ControllerEventLoop.hpp::EventLoop_FlattenAll` — slow-path flatten-all on WS staleness

### Shape: recovery-path nullable pointer (with branchless stub fallback)

When a fn is on a RECOVERY path (Reconcile, post-crash replay) where cfg may legitimately be absent, sig is:

```cpp
template <unsigned F>
inline int fn_name(/* primary state */, /* args */, const PerCoreCfg<F>* cores = nullptr);
```

Body uses branchless stub-array fallback at entry:
```cpp
static const PerCoreCfg<F> NULL_PER_CORE_CFG_STUB_ARRAY[MAX_EXECUTION_CORES] = {};
const PerCoreCfg<F>* effective_cores = cores ? cores : NULL_PER_CORE_CFG_STUB_ARRAY;
// ... loop body uses effective_cores[idx] — pure ALU, no per-iter branch
```

Nullable semantic = "recovery path; missing cfg is graceful no-op (FPN_Zero fees)." Sister to OrderManager_Submit nullable `core_cfg` pattern (.F.4c.3 r-1).

**First canonical applications (v5.15.5.F.4c.3 r-2/r-3):**
- `CoreFrameworks/Reconcile.hpp::Reconcile_ApplyMissedFills` — recovery replay of missed fills
- `CoreFrameworks/ControllerEventLoop.hpp::EventLoopState_ReconstructPerCoreFromEventLog` — boot replay from event log
- `CoreFrameworks/ControllerEventLoop.hpp::EventLoop_OnEvent` + `EventLoop_DrainPostFillOneCore` — legacy + slow-path consumers with optional cfg
- `CoreFrameworks/OrderManager.hpp::OrderManager_Submit` + `OMS_PushSubmit` — test-fixture nullable form (production callers MUST pass cfg per discipline)

---

**Stage 3 ACTIVE v1.0 — promoted 2026-05-15 at v5.15.5.F.4c.3 r-8 ship close.** 4 canonical sig shapes: (1) single per-core slice for single-core consumer (original), (2) consumer over per-core array for multi-slot dispatch (NEW), (3) recovery-path nullable pointer with branchless stub fallback (NEW), (4) caller-resolved globals as scalar args (original).
