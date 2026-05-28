---
type: framework-pattern
stage: 2-draft
version: 1.0
established: 2026-05-15
tags: [framework-discipline, structural-fix]
surface: [registry]
sister_specs: [x-macro-registry-with-presence-dispatch.md, categorical-tag-applicability-pattern.md, heterogeneous-registry-pattern.md]
applies_at_skills: []
---

# Per-instance registry pattern

**Stage:** Stage 2 DRAFT v1.0 (drafted ahead of first canonical application at v5.15.5.F.4c.3)
**Promotes to:** Stage 3 ACTIVE v1.0 at `.F.4c.3` ship close (per-core registry)
**Generalizes to:** any axis where rows materialize N times — per-node is the first canonical application; per-symbol / per-strategy / per-horizon / per-regime are anticipated future axes

---

## Summary

When configuration rows should instantiate N times across some **instance axis** — one row per execution core, per symbol traded, per strategy variant, per ensemble horizon, etc. — declare the rows ONCE in an X-macro registry and have the framework **generate N independent instances** of the registry's struct shape. Operator cfg syntax uses section headers (`[core N]`, `[symbol BTCUSDT]`, etc.) to address each instance. The bitmap dispatcher, `tt::` dispatch, and stamp emit primitives compose unchanged — they operate on rows + descriptor arrays, not on the instance dimensionality.

This is the **structural fix** for "global default + per-instance override" anti-patterns (the `.F.4c.1`-era `PerCoreOverrides` shape). When per-instance variation is the DEFAULT — not an exception — eliminate the global default entirely; make each instance authoritative.

## When to apply

Apply when:
- A configuration row could reasonably vary between two instances of the same axis (e.g., core 0 and core 1 might want different `take_profit_pct`; symbol BTCUSDT and ETHUSDT might want different `risk_pct`)
- The instance count N is small and bounded (typically ≤16 for cores; ≤32 for symbols; ≤8 for horizons)
- The instance axis is enumerable at compile time or boot time (NOT runtime-dynamic — that's a different pattern: parameter slot allocators)
- Operator wants clear per-instance configurability without inheritance confusion

Skip when:
- The row is genuinely engine-wide (`num_execution_cores`, `trading_mode`, recording toggles) — those belong in a global registry, not per-instance
- The row is read-only-once-at-boot and applies uniformly (e.g., system / OS configuration like `require_mlockall`)
- Instance count is unbounded or runtime-discovered (need a different pattern)

## Pattern shape — concrete

### Registry declaration

```cpp
// FOREACH_PER_<AXIS>_CFG_FIELD(X) — same tuple shape as global FOREACH_CFG_FIELD
//   X(KIND_TOKEN, name, label, section, meta, payload, tooltip,
//     applies_to_strategy_cat, applies_to_op_mode_cat,
//     applies_to_regime_cat, applies_to_risk_cat, lives_in_struct)
#define FOREACH_PER_CORE_CFG_FIELD(X) \
    X(KIND_DOUBLE_PCT, take_profit_pct, "TP %%", "Trading", 0, DBL(3.0, 0.0, 100.0), nullptr, \
        STRAT_CAT_ALL, OP_MODE_CAT_ALL, REGIME_CAT_ALL, RISK_CAT_ALL, CfgFieldDescriptor::STRUCT_CFG) \
    X(KIND_DOUBLE_PCT, stop_loss_pct,   "SL %%", "Trading", 0, DBL(1.5, 0.0, 100.0), nullptr, \
        STRAT_CAT_ALL, OP_MODE_CAT_ALL, REGIME_CAT_ALL, RISK_CAT_ALL, CfgFieldDescriptor::STRUCT_CFG) \
    /* ... ~50 trading rows ... */
```

### Per-instance struct generation

```cpp
template <unsigned F>
struct PerCoreCfg {
    FOREACH_PER_CORE_CFG_FIELD(EMIT_CFG_STRUCT_FIELD)
};

template <unsigned F>
struct ControllerConfig {
    // Global fields generated from FOREACH_GLOBAL_CFG_FIELD
    FOREACH_GLOBAL_CFG_FIELD(EMIT_CFG_STRUCT_FIELD)
    
    // N authoritative per-core instances — NO global default; NO inheritance
    PerCoreCfg<F> cores[MAX_EXECUTION_CORES];
};

// Cache discipline: PerCoreCfg<F> sizeof multiple of 64
static_assert(sizeof(PerCoreCfg<64>) % 64 == 0,
              "PerCoreCfg<F> must be cache-line-aligned (size % 64 == 0). "
              "Per-core access reads distinct cache lines; no false sharing.");
```

### Descriptor array (mirrors global pattern)

```cpp
inline constexpr CfgFieldDescriptor g_per_core_cfg_field_descriptors[] = {
    FOREACH_PER_CORE_CFG_FIELD(X_GEN_DESCRIPTOR)
};
static_assert(sizeof(g_per_core_cfg_field_descriptors)
              / sizeof(g_per_core_cfg_field_descriptors[0]) == PER_CORE_FIELD_IDX_END,
              "per-core descriptor array size must equal PER_CORE_FIELD_IDX_END");

// Uniqueness check per-registry (cfg_field_names_unique extended)
static_assert(cfg_field_names_unique(g_per_core_cfg_field_descriptors),
              "FOREACH_PER_CORE_CFG_FIELD has duplicate cfg_field_name");
```

### Bitmap masks (same primitive applied to per-instance registry)

```cpp
// Per-bit masks
#define X_GEN_PER_CORE_MASK_CONSTEXPR(lc, UC) \
    inline constexpr CfgMaskArray g_per_core_cfg_##lc##_mask = \
        compute_metadata_mask<CfgFieldDescriptor::UC>(g_per_core_cfg_field_descriptors);
FOREACH_METADATA_BIT(X_GEN_PER_CORE_MASK_CONSTEXPR)
#undef X_GEN_PER_CORE_MASK_CONSTEXPR

// Composed view masks (e.g., render mask = ~boot_only AND ~hidden_by_default)
inline constexpr CfgMaskArray g_per_core_cfg_render_mask = /* compose */;
```

### Cfg parser — section state machine

```cpp
enum class ParseScope { GLOBAL, CORE_N };
ParseScope parse_state = ParseScope::GLOBAL;
int active_core_idx = -1;

// Line "[core 0]" header → parse_state = CORE_N; active_core_idx = 0
// Subsequent "take_profit_pct=3.0" → parse against per-core registry, write to cfg.cores[active_core_idx]
// Line "num_execution_cores=4" before any [core N] → parse against global registry
```

### Per-instance walker (for Settings panel render, stamp emit, etc.)

```cpp
// Walk all per-core rows for each core instance
for (int c = 0; c < cfg.num_execution_cores; ++c) {
    CFG_FIELD_FOR_EACH_SET_BIT(g_per_core_cfg_render_mask.words, idx, {
        PerCoreRenderTable<F>::fns[idx](cfg.cores[c], g_per_core_cfg_field_descriptors[idx]);
    });
}
```

### Per-instance render fn-pointer table

```cpp
template <unsigned F>
struct PerCoreRenderTable {
    using RenderFn = bool (*)(PerCoreCfg<F>&, const CfgFieldDescriptor&, const char*);
    
    #define X_GEN_PER_CORE_RENDER_FN(KIND_TOKEN, name, label, section, meta, payload, tooltip, ...) \
        static bool render_##name(PerCoreCfg<F>& core_cfg, const CfgFieldDescriptor& desc, const char* cfg_path) { \
            return cfg_render_and_persist(core_cfg.name, desc, cfg_path); \
        }
    FOREACH_PER_CORE_CFG_FIELD(X_GEN_PER_CORE_RENDER_FN)
    #undef X_GEN_PER_CORE_RENDER_FN
    
    static constexpr RenderFn fns[PER_CORE_FIELD_IDX_END] = { /* X-macro pointers */ };
};
```

## Composition with other patterns

### With bitmap dispatcher framework (`.F.4c`)

UNCHANGED. The bitmap dispatcher is registry-agnostic — it operates on descriptor arrays + metadata bits + composed view masks. Two registries = two dispatcher instances. Each registry gets its own mask set, render table, walker. No special-case code.

### With `tt::` dispatch quintet (`.F.4b/.F.4c`)

UNCHANGED. The `tt::cfg_parse_field<T>` / `cfg_save_field<T>` / `cfg_assign_field<T>` / `cfg_diff_field<T>` / `cfg_render_field<T>` primitives take `T&` destination-by-reference; they're agnostic to which struct the field lives in. Same primitive consumed from either registry.

### With STAMP_BOUND derived filter framework (`.F.4d`)

Per-instance stamps. Each instance emits its own STAMP_BOUND-filtered body. For per-node: each core has its own HMAC stamp covering its per-node fields. Layer 5b hash recomputed per-instance.

### With sidecar override pattern (`.F.4d`)

Per-instance sidecars become per-instance × per-axis. For per-node × drift overrides: `g_drift_overrides[CORE_N][PER_CORE_FIELD_IDX]` — 2D sparse table. Same access pattern, just one more dimension.

### With categorical-tag-applicability-pattern (`.F.4b`)

ORTHOGONAL. The per-instance axis is structural (which CORE owns this row's value); the categorical-applicability axis is metadata (which STRATEGY/OP_MODE/REGIME the row applies to). Both compose: a per-node row with `applies_to_strategy_cat=STRAT_CAT_ML` renders only on cores running an ML strategy.

### With per-state update metadata (`.F.4c.2`/`.F.4d.1`)

ORTHOGONAL. Per-state update metadata governs WHICH state's posteriors update on each reward; per-instance governs WHICH core/symbol/horizon owns the configuration. Both compose: `cores[0].bandit_algorithm=EXP3_OP_THOMPSON_GHOST` means core 0 runs Exp3-operational + Thompson-ghost-training, independent of what core 1 does.

## First canonical application — per-core (v5.15.5.F.4c.3)

The per-node registry is the first canonical application of this pattern. Scope (see `cfg-scope-discipline.md`):

- **GLOBAL registry** (~25-30 rows): system/training/recording/engine-wide-mode/acknowledgments. Operator sets once; applies uniformly.
- **PER-NODE registry** (~55-60 rows): all trading + ML + risk + regime + strategy + entry + exit + **kill switches + max drawdown** (per Caramel's 2026-05-15 directive — different cores warrant different risk envelopes). Each core has its own authoritative values; no inheritance.

Cfg file syntax: INI-flavored `[core N]` sections.

```
# Global section (no header)
num_execution_cores=4
engine_mode=sharded
trading_mode=paper

[core 0]
strategy=ml
risk_pct=15.0
take_profit_pct=3.0
kill_switch_drawdown_pct=5.0

[core 1]
strategy=ml
risk_pct=10.0
take_profit_pct=2.5
kill_switch_drawdown_pct=3.0
```

Hard-break of legacy global trading cfg keys; operator rewrites engine.cfg once per the migration guide.

## Anticipated future axes — when each makes sense

| Axis | Trigger | Example row | Section syntax |
|---|---|---|---|
| **Per-symbol** | Multi-symbol trading (BTC + ETH + SOL with different params) | `[symbol BTCUSDT]` `[symbol ETHUSDT]` | sections by symbol |
| **Per-strategy** | Strategies grow their own ML hyperparameter spaces independent of core | `[strategy MOMENTUM]` `[strategy SIMPLEDIP]` | sections by strategy enum |
| **Per-horizon** | Ensemble horizons need independently-tunable params (ridge_lambda per horizon) | `[horizon 1000]` `[horizon 7500]` `[horizon 15000]` `[horizon 50000]` | sections by horizon tick count |
| **Per-regime** | Regime-specific tuning becomes worth it (different ridge_lambda in RANGING vs TRENDING) | `[regime RANGING]` `[regime TRENDING]` `[regime VOLATILE]` | sections by regime enum |

Each new axis = 1 new `FOREACH_PER_<AXIS>_CFG_FIELD` X-macro + new struct generation + new section parser handler. The framework primitives (bitmap dispatcher, tt:: dispatch, stamp emit, sidecar overrides) all compose unchanged.

**Caramel's stated direction (2026-05-15):** *"these can be generalized once we have it locked in to make the ML side easy to update as well? i guess thats the benefit of shared headers lol"* — the pattern is the shared-header dividend. ML side becomes 1-row-additions per future-axis registry.

## Documented exemptions via FOREACH_MANUAL_PER_<AXIS>_FIELD

Some fields legitimately can't fit the registry yet — KIND_STRING fields awaiting `.F.4e`, hex64 bitmaps awaiting type infrastructure, or fields TRANSITIONAL during migration. The per-instance-registry framework composes with `manual-fields-inventory-pattern.md` to handle these:

```cpp
// Default path: registry-driven; auto-flows everywhere
#define FOREACH_PER_CORE_CFG_FIELD(X) \
    X(FPN<F>,   KIND_DOUBLE_PCT, take_profit_pct, ...) \
    /* ... ~92 registry-driven rows ... */

// Exemption path: documented exceptions awaiting framework support OR transitional
// Each row MUST have a MANUAL_FIELDS_INVENTORY.md entry; CI cross-checks.
#define FOREACH_MANUAL_PER_CORE_FIELD(X) \
    X(char,     core_model_dir,     "[64]",  "KIND_STRING cohort at .F.4e") \
    X(uint64_t, core_feature_mask,  "",      "KIND_HEX64 needed at .F.4e") \
    X(uint8_t,  core_strategies,    "",      "TRANSITIONAL — delete at WIP2g")
    /* ... up to ~8 documented exemptions ... */
```

ControllerConfig declares parallel arrays via the X-macro ONLY:
```cpp
template <unsigned F>
struct ControllerConfig {
    PerCoreCfg<F> cores[MAX_EXECUTION_CORES];   // registry-driven (default)
    
    #define EMIT_MANUAL_PER_CORE_DECL(type, name, suffix, rationale) \
        type name[MAX_EXECUTION_CORES] suffix;
    FOREACH_MANUAL_PER_CORE_FIELD(EMIT_MANUAL_PER_CORE_DECL)
    #undef EMIT_MANUAL_PER_CORE_DECL
};
```

CI script (`tools/check_per_core_registry_integrity.py`) cross-checks bidirectionally:
- Stray `core_X[16]` declarations outside FOREACH_MANUAL_PER_CORE_FIELD = BUILD ERROR
- FOREACH_MANUAL_PER_CORE_FIELD entry without MANUAL_FIELDS_INVENTORY.md row = BUILD ERROR (and vice versa)
- Name duplication between FOREACH_PER_CORE_CFG_FIELD + FOREACH_MANUAL_PER_CORE_FIELD = BUILD ERROR
- TRANSITIONAL exemption with missing or already-shipped migration trigger = WARN/ERROR

After this discipline lands at `.F.4c.3` WIP2d-0, manual-field-bypass + parallel-array drift are STRUCTURALLY UNEXPRESSIBLE for the per-node surface.

See `manual-fields-inventory-pattern.md` (NEW Stage 2 DRAFT at .F.4c.3) for the full pattern documentation.

## X-macro struct generation closes manual-field bypass

The framework primitive at WIP2d-0 generates `PerCoreCfg<F>` struct fields via X-macro expansion:

```cpp
// Each FOREACH_PER_CORE_CFG_FIELD row carries STORAGE_TYPE as its first column:
// X(STORAGE_TYPE, KIND_TOKEN, name, label, section, meta, payload, tooltip, ...)

#define EMIT_PER_CORE_CFG_STRUCT_FIELD(STORAGE_T, KIND_TOKEN, name, label, section, meta, \
                                        payload, tooltip, ...) \
    STORAGE_T name;

template <unsigned F>
struct alignas(64) PerCoreCfg {
    FOREACH_PER_CORE_CFG_FIELD(EMIT_PER_CORE_CFG_STRUCT_FIELD)
};
```

After WIP2d-0, the struct body IS the X-macro expansion. No manual field declarations possible. Adding a field outside the registry = CI build error. Future per-node field additions flow through `FOREACH_PER_CORE_CFG_FIELD` mechanically (1-row addition).

Sister rule for parallel array exemptions: `FOREACH_MANUAL_PER_CORE_FIELD` (see above) — same X-macro discipline applied to legacy exemptions.

## Anti-patterns to avoid

- **"Global default + per-instance override" pattern.** This is the structural shape this DESIGN_SPEC eliminates. When you find yourself writing `global_value` PLUS `override_value[N]` PLUS `override_presence_bit[N]` PLUS resolve logic, stop. Either the field is genuinely global (use the global registry) OR it's per-instance (use the per-instance registry and eliminate the global default entirely). NO HYBRID.
- **"Override-set bitmaps" alongside per-instance values.** The override-presence-bitmap mechanism (per `PER_CORE_OVERRIDE_BITMAP_DOMAINS` at `.F.4c.1`-era) is a workaround for the global-default-with-override anti-pattern. Eliminating the workaround means eliminating the bitmaps too. Per-instance authoritative = no override-set bits needed.
- **Cross-instance bleeding.** Each instance's cfg lives in its OWN struct slot (`cfg.cores[c]`). Operations on `cores[i]` MUST NOT touch `cores[j]` (j ≠ i). False sharing avoided by cache-line alignment of `PerCoreCfg<F>` (size % 64 == 0 static_assert).
- **Parser scope confusion.** The cfg parser state machine must explicitly track `ParseScope`; a `take_profit_pct=3.0` line at GLOBAL scope is an ERROR (key migrated to per-node); same key inside `[core 0]` section is valid (writes to `cores[0]`). The parser must NEVER silently route a per-node key into the global registry.
- **Hidden inheritance.** Operator must not be surprised by "where does this value come from?" — the answer is always THE CORE'S OWN SECTION. If a core doesn't set a field, the cfg-init default (from the row's payload `DBL(default, ...)`) applies, but that default lives in the registry row, not in some implicit global cfg state.

## Reference implementations

(Populates at Stage 3 ACTIVE — shipped sites get file:line refs back-linked here.)

- (pending) `CoreFrameworks/CfgFieldRegistry.hpp` — `FOREACH_PER_CORE_CFG_FIELD` + `g_per_core_cfg_field_descriptors[]` (post-`.F.4c.3`)
- (pending) `CoreFrameworks/ControllerConfig.hpp` — `PerCoreCfg<F>` struct + `cores[MAX_EXECUTION_CORES]` array
- (pending) `GUI/SettingsPanel.hpp` — `PerCoreRenderTable<F>` + per-node tab walker

## Cross-references

- `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` (NEW; sister spec) — discipline for choosing WHICH axis a row belongs to
- `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md` — parent pattern (universal registry shape); per-instance is an axis-specific specialization
- `DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md` — bitmap dispatcher consumes either registry unchanged
- `DESIGN_SPECS/framework-patterns/type-trait-dispatch-via-tt-namespace.md` — tt:: dispatch is registry-agnostic; per-instance dispatch via destination-by-reference
- `DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md` — orthogonal axis (metadata vs structural)
- `DESIGN_SPECS/framework-patterns/multi-state-dispatch-with-per-state-update-metadata.md` (NEW 2026-05-14) — orthogonal to per-instance; composes
- `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` — per-instance Layer 5b applies (per-node stamps)
- `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md` — workflow this spec followed (Stage 2 DRAFT ahead of first canonical application)
- CLAUDE.md item 31 — framework discipline meta-principle (this spec is a concrete framework instance)
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 24 — structural close at per-node split (capability-cfg surface mismatch)

---

## Stage 3 ACTIVE — axis evolution note (added at v5.15.5.F.4c.3 r-8 ship close, 2026-05-15)

The per-node axis is the FIRST canonical application of per-instance registry shape. Future axes (per-symbol, per-strategy, per-horizon, per-regime) extend mechanically:

- **Per-symbol** (next likely): `FOREACH_PER_SYMBOL_CFG_FIELD` + `PerSymbolCfg<F>` struct; consumer fns add `const PerSymbolCfg<F>* symbols` param per the consumer-over-per-instance-array shape (`cfg-scope-discipline.md` Stage 3 § "consumer over per-node array" — generalizes to ANY per-instance axis)
- **Per-strategy** (when ML hyperparameters grow per-strategy independence): same shape; `FOREACH_PER_STRATEGY_CFG_FIELD` + array
- **Per-horizon / per-regime** (further future): same shape; orthogonal to per-node via type-system composition

**Sig shape evolution is structurally enforced**: each new axis adds 1 more `const Per<Axis>Cfg<F>* <axis_name>` param to multi-axis consumer fns. Type system catches every caller at axis-addition ship.

**Multi-axis composition** (per-node × per-symbol): per-instance instance count = N(cores) × N(symbols). Storage: `PerCoreCfg<F> cores[MAX_EXECUTION_CORES]; PerSymbolCfg<F> symbols[MAX_SYMBOLS];` — separate arrays, separate consumer fns. Don't conflate into a single 2D struct unless ALL trading-axis fields cross both axes (rare).

**Not deferred**: this evolution path is the structural framework. Future ships that add new axes follow this pattern WITHOUT redesign. Per `branchless-dispatch-discipline.md` composition note: Pattern 5 noop fn-pointer dispatch composes with multi-axis registry (per-axis enable bits drive fn-pointer selection).

---

**Stage 3 ACTIVE v1.0 — promoted 2026-05-15 at v5.15.5.F.4c.3 r-8 ship close.** Per-core axis live; per-symbol / per-strategy / per-horizon / per-regime axes structurally enforced by sig discipline; multi-axis composition expressible via separate per-axis arrays + sig extension.
