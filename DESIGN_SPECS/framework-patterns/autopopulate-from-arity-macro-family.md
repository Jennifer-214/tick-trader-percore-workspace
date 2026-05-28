---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-10
tags: [framework-discipline, structural-fix]
surface: [registry]
sister_specs: [autopopulate-pattern-for-production-caller-class.md, x-macro-registry-with-presence-dispatch.md, registry-tuple-as-single-source-of-truth.md]
applies_at_skills: []
---

# AUTOPOPULATE arity macro family (_FROM_PAIR / _FROM_TRIPLE / _FROM_HEX / _FROM_SEPTUPLE)

**Established:** 2026-05-10 (v5.14.9.F-.F.3)
**Status:** ACTIVE
**Cross-references:**
- Parent pattern: `autopopulate-pattern-for-production-caller-class.md` (X-macro-driven AUTOPOPULATE)
- Sister pattern: `bitmap-flag-api.md` (the bitmap field this writes to)
- Sister pattern: `heterogeneous-registry-pattern.md` (DOMAIN SPLIT registries that use this)
- First applications:
  - `CoreFrameworks/LifecycleCfgFlagRegistry.hpp:91` — `LIFECYCLE_CFG_FLAG_AUTOPOPULATE_FROM_TRIPLE`
  - `CoreFrameworks/GateCfgFlagRegistry.hpp:80` — `GATE_CFG_FLAG_AUTOPOPULATE_FROM_HEX`
  - `ML_Headers/MlCfgFlagRegistry.hpp:87` — `ML_CFG_FLAG_AUTOPOPULATE_FROM_SEPTUPLE`
  - `CoreFrameworks/RiskCfgFlagRegistry.hpp:45` — `RISK_CFG_FLAG_AUTOPOPULATE_FROM_TRIPLE`
  - `CoreFrameworks/OpsCfgFlagRegistry.hpp:44` — `OPS_CFG_FLAG_AUTOPOPULATE_FROM_PAIR`
- CLAUDE.md item 21 (AUTOPOPULATE companion macro discipline)

---

## Problem statement

The base AUTOPOPULATE pattern (`autopopulate-pattern-for-production-caller-class.md`) generates per-field populator code via X-macro walk + caller passes a SINGLE `source` struct that holds all fields named identically to registry entries. Works great when the source struct exists.

**v5.14.9.F-.F.3 hit a different shape:**

- Caller has N **scattered local booleans** that map to N registry entries 1:1
- NO shared source struct exists (e.g., parser locals during cfg-load)
- N varies per registry: 2 (OPS), 3 (LIFECYCLE / RISK), 6 (GATE), 7 (ML)

Two paths:

1. **Build a synthetic source struct.** Caller constructs `{bool a, b, c, ...}` matching registry order; AUTOPOPULATE walks via `source.X`. Cost: caller writes 1 struct decl + N field-init lines + 1 AUTOPOPULATE call = 2N+2 lines.

2. **Variadic-arity macro** that takes the N booleans directly. Caller writes 1 macro call with N args. Cost: 1 line for the call (+ 1 macro definition per arity in the registry header).

Option 2 won. The macro becomes the contract; caller's locals stay scattered.

**But: standard C preprocessor has no clean variadic dispatch.** `__VA_ARGS__` works for "any number of args" but doesn't dispatch DIFFERENT macros for different arity counts cleanly. Solution: define one macro PER arity.

This pattern catalogs the arity-family approach: when to use which arity, naming convention, signature contract.

---

## Design space explored

### Option A: Single synthetic source struct + base AUTOPOPULATE

Caller constructs a synthetic struct + walks via base AUTOPOPULATE pattern.

**Rejected for cfg parsers** because:
- Parser's locals are *already* the booleans (e.g., `int partial_exit_enabled = 0; ... fscanf("partial_exit_enabled=%d", &partial_exit_enabled);`)
- Forcing a synthetic struct adds 2N+2 lines (struct decl + per-field init + free)
- Synthetic struct's existence is purely-mechanical (no other use)

Acceptable when the source struct already exists naturally (e.g., AUTOPOPULATE from a parsed-config struct → stamp-body struct).

### Option B: True variadic macro via `__VA_ARGS__` + position-paste

```cpp
#define AUTOPOPULATE_FROM_N(target, ...) \
    do { \
        bool args[] = {__VA_ARGS__}; \
        for (int i = 0; i < FOREACH_<DOMAIN>_CFG_FLAG_COUNT; i++) { /* runtime walk */ } \
    } while (0)
```

**Rejected** because:
- Runtime walk loses the branchless mask-OR property (compiler can't const-fold)
- Position-to-mask mapping via runtime indirection adds ~5x cost vs compile-time expansion
- No compile-time check that arg count == registry count (silent miscount → wrong flags)

### Option C (chosen): Named-arity macro family

One macro per arity. Caller picks the right arity for their registry size:

```cpp
LIFECYCLE_CFG_FLAG_AUTOPOPULATE_FROM_TRIPLE(target, a, b, c);      // 3 entries
OPS_CFG_FLAG_AUTOPOPULATE_FROM_PAIR(target, a, b);                  // 2 entries
GATE_CFG_FLAG_AUTOPOPULATE_FROM_HEX(target, a, b, c, d, e, f);     // 6 entries
ML_CFG_FLAG_AUTOPOPULATE_FROM_SEPTUPLE(target, a, b, c, d, e, f, g); // 7 entries
```

Compile-time expansion preserves branchless mask-OR + compile-time arg count enforcement (preprocessor error if wrong number of args).

**Trade-off:** adding a new entry to a registry changes the arity → caller updates the macro NAME (FROM_TRIPLE → FROM_QUAD). One-time cost; co-located with the registry tuple change.

---

## The pattern (concrete shape)

### Arity naming convention

Standard math/CS terms for clarity:

| Arity | Macro suffix | Notes |
|---|---|---|
| 2 | `_FROM_PAIR` | OPS uses this (session_filter + notify) |
| 3 | `_FROM_TRIPLE` | LIFECYCLE / RISK use this |
| 4 | `_FROM_QUAD` | reserved; no registry at this size today |
| 5 | `_FROM_QUINT` | reserved |
| 6 | `_FROM_HEX` | GATE uses this |
| 7 | `_FROM_SEPTUPLE` | ML uses this |
| 8 | `_FROM_OCTET` | reserved |

Beyond 8: switch to source-struct pattern (Option A) — caller writing 9+ scattered locals is the antipattern, not the macro.

### Per-arity macro template

```cpp
#define <DOMAIN>_CFG_FLAG_AUTOPOPULATE_FROM_<ARITY>(target_flags, _arg1, _arg2, ..., _argN) \
    do {                                                                                     \
        <storage_type> _new_flags = 0;                                                       \
        _new_flags |= ((_arg1) ? MASK_<DOMAIN>_CFG_<NAME_1> : (<storage_type>)0u);          \
        _new_flags |= ((_arg2) ? MASK_<DOMAIN>_CFG_<NAME_2> : (<storage_type>)0u);          \
        /* ... one row per registry entry ... */                                             \
        _new_flags |= ((_argN) ? MASK_<DOMAIN>_CFG_<NAME_N> : (<storage_type>)0u);          \
        (target_flags) = _new_flags;                                                         \
    } while (0)
```

**Element 1:** `target_flags` is the bitmap field receiving the populated flags. Reset to 0 + OR-build (single store at the end; not incremental).

**Element 2:** `<storage_type>` is the bitmap field's type (uint8_t / uint16_t / uint32_t). Critical for high-bit safety (signed-int promotion would corrupt bits past 7).

**Element 3:** Each `((_argN) ? MASK : 0u)` is the branchless mask contribution. Compiler emits `cmov` (no branch); N rows + 1 store = N+1 instructions.

**Element 4:** Argument order MATCHES registry order. The macro is positional — `_arg1` populates the bit for the FIRST registry entry, etc. Caller MUST pass args in registry order.

### Canonical example: GATE_CFG_FLAG_AUTOPOPULATE_FROM_HEX

```cpp
// FOREACH_GATE_CFG_FLAG has 6 entries: DEPTH / GATE_EMA / NO_TRADE_BAND /
// COST_GATE / BARRIER_GATE / PARAM_STALENESS_GATE.

#define GATE_CFG_FLAG_AUTOPOPULATE_FROM_HEX(target_flags, \
    _depth, _gate_ema, _no_trade_band, _cost_gate, _barrier_gate, _param_staleness) \
    do {                                                                             \
        uint8_t _new_flags = 0;                                                      \
        _new_flags |= ((_depth)           ? MASK_GATE_CFG_DEPTH                : 0u);\
        _new_flags |= ((_gate_ema)        ? MASK_GATE_CFG_GATE_EMA             : 0u);\
        _new_flags |= ((_no_trade_band)   ? MASK_GATE_CFG_NO_TRADE_BAND        : 0u);\
        _new_flags |= ((_cost_gate)       ? MASK_GATE_CFG_COST_GATE            : 0u);\
        _new_flags |= ((_barrier_gate)    ? MASK_GATE_CFG_BARRIER_GATE         : 0u);\
        _new_flags |= ((_param_staleness) ? MASK_GATE_CFG_PARAM_STALENESS_GATE : 0u);\
        (target_flags) = _new_flags;                                                 \
    } while (0)
```

Caller usage (in `ControllerConfig.hpp` parser):

```cpp
GATE_CFG_FLAG_AUTOPOPULATE_FROM_HEX(cfg.gate_cfg_flags,
    parsed_depth_enabled,
    parsed_gate_ema_enabled,
    parsed_no_trade_band_enabled,
    parsed_cost_gate_enabled,
    parsed_barrier_gate_enabled,
    parsed_param_staleness_gate_enabled);
```

Caller's 6 scattered locals → 1 macro call → branchless bitmap populated. 6 cmov + 6 OR + 1 store = ~7 instructions.

---

## Adding a new arity

When a new registry size emerges:

1. **Pick the arity name** from the naming convention table above. If a slot doesn't have a name yet, use the natural math/CS term (QUAD, QUINT, OCTET, NONUPLE, etc.).
2. **Define the macro in the registry header** alongside the FOREACH macro. Co-located = easy to keep in sync.
3. **Update the registry's own count check** if it changes the uint8/16/32 boundary (`static_assert(<DOMAIN>_CFG_COUNT <= 8)` etc.).
4. **Update callers** with the new arity macro name + new arg.

The arity name change is intentional friction — it forces the caller to acknowledge the registry grew. Silent variadic would let parser drift; named arity catches at compile time.

---

## When N > 8: switch to source-struct pattern

Beyond ~8 args, the caller's macro call becomes unreadable:

```cpp
// BAD — 10+ args, error-prone, hard to review
ML_CFG_FLAG_AUTOPOPULATE_FROM_DECUPLE(target, a, b, c, d, e, f, g, h, i, j);
```

Refactor to a synthetic struct + base AUTOPOPULATE pattern:

```cpp
struct MlCfgInputs {
    bool confidence_enabled;
    bool composite_enabled;
    /* ... 10+ booleans ... */
};

// Caller fills the struct from locals:
MlCfgInputs inputs = {parsed_a, parsed_b, ..., parsed_j};
ML_CFG_FLAG_AUTOPOPULATE(target_flags, inputs);  // base pattern via struct fields
```

The struct is heavier (one decl + N init lines) but readable. Threshold: ~8 args.

For now (v5.14.9), the largest registry is ML at 7 entries (FROM_SEPTUPLE). If ML grows to 9, refactor it first.

---

## Trade-offs + when to apply

### Apply when:
- Registry has 2-8 entries
- Caller's source data is scattered locals (not a shared struct)
- Compile-time correctness (arg count matches registry size) is desired
- Branchless mask-OR contribution is desired (slow-path or hot-path adjacent)

### Skip when:
- Registry has 9+ entries (use source-struct pattern instead)
- Caller already has a struct with field names matching registry entries (use base AUTOPOPULATE)
- Args' types vary widely (e.g., mix of bool + int + char arrays — base AUTOPOPULATE handles via `if constexpr` type dispatch; arity-family doesn't)

### Cost:
- ~10-15 LOC for the macro definition per arity (mechanical; lives in registry header)
- Adding a new entry to a registry = 1 row in FOREACH + 1 arg in the arity macro + caller updates (N→N+1 args)

### Win:
- Caller writes 1 line vs N+2 (struct + inits + call)
- Compile-time arg count check (preprocessor error if wrong count)
- Branchless mask-OR preserved (compiler const-folds; same as base AUTOPOPULATE)
- No runtime walk; no array indirection

---

## Reference implementations

### v5.14.9.F-.F.3 family

5 arity variants across 5 domain registries:

| Registry | Arity | Macro | Entry count |
|---|---|---|---|
| FOREACH_OPS_CFG_FLAG | 2 | `OPS_CFG_FLAG_AUTOPOPULATE_FROM_PAIR` | session_filter, notify |
| FOREACH_LIFECYCLE_CFG_FLAG | 3 | `LIFECYCLE_CFG_FLAG_AUTOPOPULATE_FROM_TRIPLE` | partial_exit, breakeven×2 |
| FOREACH_RISK_CFG_FLAG | 3 | `RISK_CFG_FLAG_AUTOPOPULATE_FROM_TRIPLE` | kill_switch, vol_sizing, ws_flatten |
| FOREACH_GATE_CFG_FLAG | 6 | `GATE_CFG_FLAG_AUTOPOPULATE_FROM_HEX` | depth, gate_ema, no_trade_band, cost, barrier, param_staleness |
| FOREACH_ML_CFG_FLAG | 7 | `ML_CFG_FLAG_AUTOPOPULATE_FROM_SEPTUPLE` | confidence, composite, bandit, exit_bandit, use_exit_model, vol_scaling, lazy_rebuild |

All called from `ControllerConfig.hpp:1316-1343` after parser locals are populated.

### Related: SLOW_PATH_GATE arity variants

`SlowPathGateRegistry.hpp:209-218` defines `_PER_CORE` and `_ENGINE_WIDE` variants — same arity-family idea but axis = scope (per-node vs engine-wide) instead of arg count. Same principle: caller picks the right variant based on their context.

---

## Lessons / gotchas

### Arity name MUST appear in macro name

Tempting to write `LIFECYCLE_CFG_FLAG_AUTOPOPULATE(target, ...)` and try to overload by arg count. **Rejected** — C preprocessor can't dispatch on arg count cleanly. Naming the arity in the macro symbol (FROM_TRIPLE) makes the contract explicit + breaks loudly at compile time when registry size changes.

### Argument names start with underscore to avoid shadowing

`_kill_switch`, `_vol_sizing` — leading underscore prevents accidental shadowing of caller's variable names (e.g., caller has `int kill_switch = ...;` — without underscore, the macro expansion would create ambiguity).

### Storage type cast on the `0u` arm

```cpp
_new_flags |= ((_arg) ? MASK_FOO : (uint8_t)0u);
```

Without the cast, `0u` is `unsigned int`; the ternary promotes to int → assignment to `uint8_t` triggers `-Wconversion`. Explicit cast suppresses + makes type uniform across arms.

### Wrap in `do { ... } while (0)`

Standard idiom for multi-statement macros. Allows use after `if (cond)` without braces (`if (cond) AUTOPOPULATE(...);` works correctly). Don't use `({ ... })` GCC extension; portability + clarity.

### Single end-store, not incremental ORs

```cpp
// GOOD — single store at end
uint8_t _new_flags = 0;
_new_flags |= ...;
_new_flags |= ...;
(target_flags) = _new_flags;

// BAD — multiple stores to (target_flags)
(target_flags) = 0;
(target_flags) |= ...;
(target_flags) |= ...;
```

Compiler may struggle to coalesce the second form if `target_flags` is an aliased field. Single end-store is canonical.

### Caller arg order MUST match registry order

The arity macro is positional. If caller writes args in a different order than registry, the WRONG bits get set. There's no compile-time check for this — relies on caller discipline.

**Mitigation:** put arg names in the macro definition that strongly hint at registry order (`_kill_switch, _vol_sizing, _ws_flatten`) so caller's compile fails on typo (`_kill_swich`).

### When adding a registry entry, update ALL callers

The arity changes (FROM_TRIPLE → FROM_QUAD). Every caller must update. Compile-time enforcement makes this safe — the OLD macro name no longer exists, so `grep` finds all sites + compile errors guide the update.

### Don't bury arity macros far from FOREACH macro

Co-locate in the same registry header. A maintainer reading FOREACH should see the arity macro right below, with matching arg count + naming. Splitting them across files breaks discoverability.

### `_new_flags |= 0u` per arm — compiler eliminates

For args that are statically `false` (e.g., legacy field absent), the compiler folds `(false) ? MASK : 0u` → `0u`, then `_new_flags |= 0u` is a no-op + dropped. Branchless property preserved end-to-end.

---

## Audit detection

`/dod-audit` detects missed applications by:

- Symptom: parser body with ≥3 inline `cfg.X_flags |= (parsed_X ? MASK_X : 0)` lines for a single bitmap field
- Symptom: caller pattern `cfg.flags = 0; if (a) cfg.flags |= MASK_A; if (b) cfg.flags |= MASK_B; ...` (incremental form)
- Symptom: synthetic struct decl `struct LocalInputs { bool a, b, c; } inputs = {parsed_a, ...};` followed by per-field copy

When detected → flag as `MISSED — autopopulate-from-arity-macro-family`. Recommended fix: define an arity macro in the registry header; replace caller with single-line call.

---

## Patterns NOT used here (and why)

### `__VA_ARGS__` variadic macros

Single macro accepting any number of args. Rejected because no compile-time arg count check + runtime walk loses branchless property.

### Templated populator (C++ template parameter pack)

```cpp
template <typename... Bools> void populate(uint8_t& target, Bools... vals);
```

Heavier; can't const-fold MASK constants known at preprocessor time; harder to debug expansion. Macros stay simpler.

### Recursive macro expansion (PP_FOR_EACH)

Used by Boost.Preprocessor for variadic walks. Adds external dependency + obscure debug output. Named arity is simpler.

---

## Cross-references

- `autopopulate-pattern-for-production-caller-class.md` — parent pattern (source-struct variant)
- `bitmap-flag-api.md` — the bitmap field being populated
- `heterogeneous-registry-pattern.md` — DOMAIN SPLIT registries that use arity macros
- `registry-tuple-as-single-source-of-truth.md` — meta-pattern (registry feeds N consumers including AUTOPOPULATE)
- FoxML_Trader_v2 `CLAUDE.md` item 21 — AUTOPOPULATE companion macro discipline
- FoxML_Trader_v2 `CoreFrameworks/{Lifecycle,Gate,Risk,Ops}CfgFlagRegistry.hpp` — reference implementations
- FoxML_Trader_v2 `ML_Headers/MlCfgFlagRegistry.hpp` — 7-arity (largest current)
