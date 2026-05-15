# Multi-action registry walker family

**Stage:** Stage 2 DRAFT v1.0 (drafted ahead of first canonical application at v5.15.5.F.4c.3)
**Promotes to:** Stage 3 ACTIVE v1.0 at `.F.4c.3` ship close (F4 reuse harvest adoption)
**Sister specs:** `per-instance-registry-pattern.md` (the per-instance axis this family operates on), `universal-cfg-field-registry-pattern.md` (the registry shape it walks), `universal-registry-bitmap-dispatcher-pattern.md` (the bitmap-dispatch primitive each action consumes)

---

## Summary

When N actions (parse / save / render / stamp emit / drift check / etc.) must be applied across M registries (global cfg / per-core cfg / future per-symbol / per-strategy / per-horizon), declare ONE walker template per action that's parameterized over the registry shape, then instantiate each action × registry combination at use sites. Adding a new registry axis = N new instantiations (mechanical); adding a new action = 1 new walker template (one-time work, then reused across all M registries).

Without this pattern: N × M = N walker bodies authored manually per (action, registry) pair. With this pattern: N + M (per-axis registry instantiation is mechanical row-add; per-action walker is mechanical template instantiation).

## When to apply

Apply when:
- N actions (≥3) each touch every row in a registry uniformly (no per-action-per-row special-case logic except via metadata)
- M registries (≥2) share the same descriptor shape (`CfgFieldDescriptor` or equivalent)
- Each action's per-row body is parameterizable on `(descriptor, target_struct&, ...action_args)`
- Future axes are anticipated (Class 24 prevention extends naturally)

Skip when:
- N=1 or M=1 (no compounding benefit)
- Per-action-per-row logic is heavily special-cased (the walker becomes if/else soup; manual walker is clearer)
- The actions have wildly different I/O signatures (each action needs its own root template anyway)

## Pattern shape

### Registry-of-actions declaration

```cpp
// FOREACH_REGISTRY_ACTION(X) — declares the family of actions applicable
// across all per-instance registries. Tuple: (action_name, action_lc, doc).
#define FOREACH_REGISTRY_ACTION(X) \
    X(PARSE,    parse,    "Text → typed field write (cfg parser)")                    \
    X(SAVE,     save,     "Typed → text emit (cfg save / engine.cfg rewrite)")        \
    X(RENDER,   render,   "Typed → ImGui widget (Settings panel)")                    \
    X(STAMP,    stamp,    "Typed → HMAC stamp body emit (parity-bound rows only)")    \
    X(DRIFT,    drift,    "Stamp value vs current cfg value compare (drift detect)")

#define X_GEN_ACTION_ENUM(ACTION, action, doc) REGISTRY_ACTION_##ACTION,
enum RegistryAction {
    FOREACH_REGISTRY_ACTION(X_GEN_ACTION_ENUM)
};
#undef X_GEN_ACTION_ENUM
```

### Walker template per action

Each action has ONE walker template parameterized over registry shape:

```cpp
// Generic walker over any registry's descriptor array + target struct
template <typename TargetStruct, typename Descriptor, size_t N, typename ActionFn>
inline void walk_registry_action(
    TargetStruct& target,
    const Descriptor (&descriptors)[N],
    const CfgMaskArray& filter_mask,
    ActionFn action_fn)
{
    CFG_FIELD_FOR_EACH_SET_BIT(filter_mask.words, idx, {
        action_fn(target, descriptors[idx]);
    });
}
```

Per-action fn-pointer tables (parameterized by registry):

```cpp
// Per-registry × per-action fn-ptr table — auto-generated from registry rows
template <unsigned F, RegistryAction Action>
struct GlobalActionTable {
    using ActionFn = bool (*)(ControllerConfig<F>&, const CfgFieldDescriptor&, ...);
    
    #define X_GEN_GLOBAL_ACTION_FN(KIND_TOKEN, name, label, section, meta, payload, tooltip, ...) \
        static bool action_##name(ControllerConfig<F>& cfg, const CfgFieldDescriptor& desc, ...) { \
            return tt::cfg_<action_dispatch_by_RegistryAction>(cfg.name, desc, ...); \
        }
    FOREACH_GLOBAL_CFG_FIELD(X_GEN_GLOBAL_ACTION_FN)
    #undef X_GEN_GLOBAL_ACTION_FN
    
    static constexpr ActionFn fns[GLOBAL_FIELD_IDX_END] = { /* X-macro */ };
};

template <unsigned F, RegistryAction Action>
struct PerCoreActionTable {
    using ActionFn = bool (*)(PerCoreCfg<F>&, const CfgFieldDescriptor&, ...);
    
    #define X_GEN_PER_CORE_ACTION_FN(KIND_TOKEN, name, label, section, meta, payload, tooltip, ...) \
        static bool action_##name(PerCoreCfg<F>& core_cfg, const CfgFieldDescriptor& desc, ...) { \
            return tt::cfg_<action_dispatch_by_RegistryAction>(core_cfg.name, desc, ...); \
        }
    FOREACH_PER_CORE_CFG_FIELD(X_GEN_PER_CORE_ACTION_FN)
    #undef X_GEN_PER_CORE_ACTION_FN
    
    static constexpr ActionFn fns[PER_CORE_FIELD_IDX_END] = { /* X-macro */ };
};
```

### Call site — consume any action × registry combination

```cpp
// Parse global cfg fields from file
walk_registry_action(cfg, g_global_cfg_field_descriptors, 
                     g_global_cfg_parse_mask,
                     [](auto& target, const auto& desc) {
                         GlobalActionTable<F, REGISTRY_ACTION_PARSE>::fns[desc.field_idx](target, desc);
                     });

// Render per-core cfg fields in Settings panel
for (int c = 0; c < cfg.num_execution_cores; ++c) {
    walk_registry_action(cfg.cores[c], g_per_core_cfg_field_descriptors,
                         g_per_core_cfg_render_mask,
                         [](auto& target, const auto& desc) {
                             PerCoreActionTable<F, REGISTRY_ACTION_RENDER>::fns[desc.field_idx](target, desc);
                         });
}
```

Adding `FOREACH_PER_SYMBOL_CFG_FIELD` in the future = 1 new registry declaration + 1 new `PerSymbolActionTable<F, Action>` X-macro generation + use sites via `walk_registry_action`. No new walker bodies authored manually.

## Composition with other patterns

- **`per-instance-registry-pattern.md`** — this family operates over per-instance registries. Per-instance axes (per-core, per-symbol, per-strategy, per-horizon) each get their own action-table instantiations.
- **`universal-cfg-field-registry-pattern.md`** — the registry shape this family walks (`CfgFieldDescriptor` rows).
- **`universal-registry-bitmap-dispatcher-pattern.md`** — each action consumes the bitmap-dispatch primitive for filtering rows by metadata bit.
- **`type-trait-dispatch-via-tt-namespace.md`** — action body dispatches via `tt::cfg_<action>_field<T>` typed primitives.
- **`x-macro-registry-with-presence-dispatch.md`** — action enumeration via X-macro presence dispatch (FOREACH_REGISTRY_ACTION).

## First canonical application — v5.15.5.F.4c.3

5 actions × 2 registries (global + per-core) = 10 walker instantiations consumed via single template:

| Action | Global registry | Per-core registry |
|---|---|---|
| PARSE | Cfg parser (lines before `[core N]`) | Cfg parser (lines inside `[core N]` section) |
| SAVE | Cfg save (global section at top) | Cfg save (`[core N]` section per core) |
| RENDER | Settings panel Global tab | Settings panel per-core tabs |
| STAMP | Global STAMP_BOUND rows (if any after split) | Per-core STAMP_BOUND rows (per-core stamps) |
| DRIFT | Global drift check (if any) | Per-core drift check (per-core stamp vs per-core cfg) |

LOC savings: 5 walker bodies × 2 registries = 10 bodies → 5 templates × 1 declaration + 2 X-macro instantiations = 7 source items. Net LOC: ~150 saved at `.F.4c.3`; ~500 saved per future axis (per-symbol / per-strategy / etc.).

## Anticipated future applications

| Axis | Trigger | New instantiations |
|---|---|---|
| Per-symbol | Multi-symbol trading | 5 actions × per-symbol registry = 5 `PerSymbolActionTable<F, Action>` instantiations + use sites |
| Per-strategy | Strategy-specific hyperparameter spaces | Same shape |
| Per-horizon | Per-horizon hyperparameter spaces (ridge_lambda per horizon, etc.) | Same shape |
| Per-regime | Regime-specific tuning | Same shape |
| Per-bandit-arm | Per-arm parameter spaces | Same shape |

Each new axis = mechanical row-by-row registry decl + N action-table instantiations. No new walker bodies authored.

## Anti-patterns to avoid

- **Walker-body duplication.** Writing parse / save / render / stamp / drift walker bodies manually for each registry. The whole point of this family is to extract the walker shape ONCE; duplicating bodies re-introduces Class 18 mirror risk + N × M maintenance burden.
- **Per-action special-case in the walker template itself.** If an action needs special-case logic for SOME rows (not all), use METADATA bits + filter masks (`g_<registry>_<action>_mask`) to scope the walker — NOT branch-in-template. Compile-time discipline; no runtime conditionals inside the walker inner loop.
- **Cross-registry name collision in action-table struct names.** Each registry × action combination needs a unique typename (`GlobalActionTable<F, REGISTRY_ACTION_PARSE>` ≠ `PerCoreActionTable<F, REGISTRY_ACTION_PARSE>`). Compile-time uniqueness via X-macro generation + per-registry namespacing.
- **Action enum value-vs-name confusion** — adding `STAMP=2` then `DRIFT=2` collides at compile time per `cfg_field_names_unique` discipline pattern. Each action enum value is unique by X-macro generation.

## Reference implementations

(Populates at Stage 3 ACTIVE — shipped sites get file:line refs back-linked here.)

- (pending) `CoreFrameworks/CfgFieldRegistry.hpp` — `FOREACH_REGISTRY_ACTION(X)` declaration (post `.F.4c.3`)
- (pending) `CoreFrameworks/CfgFieldDispatch.hpp` — `walk_registry_action` template
- (pending) `CoreFrameworks/CfgFieldRegistry.hpp` — `GlobalActionTable<F, Action>` + `PerCoreActionTable<F, Action>` X-macro instantiations
- (pending) `GUI/SettingsPanel.hpp` — call sites for RENDER action on both registries

## Cross-references

- `DESIGN_SPECS/per-instance-registry-pattern.md` — the per-instance axis this family operates on
- `DESIGN_SPECS/universal-cfg-field-registry-pattern.md` — the registry shape
- `DESIGN_SPECS/universal-registry-bitmap-dispatcher-pattern.md` — bitmap-dispatch primitive each action consumes
- `DESIGN_SPECS/type-trait-dispatch-via-tt-namespace.md` — action body's typed dispatch
- `DESIGN_SPECS/x-macro-registry-with-presence-dispatch.md` — parent presence-dispatch pattern
- `DESIGN_SPECS/cfg-scope-discipline.md` — scope decisions per registry
- `DESIGN_SPECS/pattern-codification-lifecycle.md` — workflow this followed
- CLAUDE.md item 31 — framework discipline meta-principle

---

**Stage 2 DRAFT v1.0 — committed 2026-05-15 ahead of `.F.4c.3` ship.** Promotes to Stage 3 ACTIVE v1.0 at ship close once 5 action × 2 registry reference implementations land.
