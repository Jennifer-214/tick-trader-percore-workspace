# Auto-populate pattern for production-caller field-population class

**Established:** 2026-05-09 (v5.14.1.E.E.B + v5.14.8.A.merged)
**Status:** ACTIVE
**Cross-references:**
- First application: `STAMP_CFG_AUTOPOPULATE` (v5.14.1.E.E.B; cfg-bound stamp body fields)
- Second application: `STAMP_MODEL_CONST_AUTOPOPULATE` (v5.14.8.A.merged; architectural stamp body fields)
- Companion: `x-macro-registry-with-presence-dispatch.md`
- Closes recurring-bug class: v5.9.5b production-caller field-population gap

---

## Problem statement

A struct (e.g., `StampInferenceCfgInputs`) is constructed by production callers, populated with field values, and passed to a downstream consumer (e.g., `stamp_write_for_model`). When a NEW field is added to the struct, every production caller must update to populate the new field — otherwise the field is silently zero/empty in production output.

This is the **production-caller field-population class** (v5.9.5b). Diagnosed at FoxML_Trader_v2 across 4 separate recurrences (PARITY-002, -003, -004, -005, -008) before being structurally extinguished:

- v5.9.5b: 10 inference cfg fields added; production caller `Backtest_RunFullValidation` passed `nullptr` for `inf` → all 10 fields silently absent from auto-stamped models
- v5.14.1.B.3: ridge cfg fields; required manual update at `BacktestPanels.hpp:3206` and `BacktestEngine.hpp:1147`
- Each recurrence cost: 1-3h debug + retraining

The shape: someone adds a field to the registry/struct, runs tests (which pass via synthetic constructor), but production-caller construction sites silently emit zeros. Verifier downstream sees `has_<field>=0` and skips checks → fields are unprotected in production while looking protected in tests.

---

## Design space explored

### Option A: Manual discipline + grep-based audit gate

Add a `/parity-check` Section L step: grep for `StampInferenceCfgInputs\s+[a-z_]\+\s*=` and verify each construction site populates new fields.

**Rejected as primary fix** — discipline-based mitigations don't scale. Reviewer drift; PR descriptions don't always trigger Section L checks; new contributors miss the discipline.

Acceptable as DEFENSE IN DEPTH alongside structural fix.

### Option B: Required builder pattern (factory function)

Force production callers to use `make_StampInferenceCfgInputs(...)` constructor that takes ALL fields.

**Rejected** — adding a new field changes the constructor signature, requiring every production caller to update anyway. Same N-site problem; just shifts where the manual work happens.

### Option C (chosen): X-macro-driven AUTOPOPULATE companion

The registry already drives field declarations via X-macro. Add a COMPANION X-macro that auto-generates the per-field populator code at production callers:

```cpp
// At production caller:
StampInferenceCfgInputs inf{};
STAMP_CFG_AUTOPOPULATE(inf, cfg);  // expands to populator for ALL registry fields
stamp_write_for_model(..., &inf);
```

`STAMP_CFG_AUTOPOPULATE` expands at preprocessor time into per-field gated populator code. Adding a new registry field automatically gets picked up by every existing AUTOPOPULATE call site at next compile. **Forgetting the populator becomes IMPOSSIBLE.**

---

## The pattern (concrete shape)

### Step 1: Per-entry populator macro (token-paste-aware)

```cpp
#define STAMP_MODEL_CONST_AUTOPOPULATE_ONE(name, group, presence, type, fmt, def, get, when, doc) \
    if (when) {                                                                        \
        STAMP_AUTOPOPULATE_SET_HAS_##group(name);  /* group-aware has_* dispatch */    \
        if constexpr (std::is_array_v<type>) {                                         \
            strncpy((inf).name, (get), std::extent_v<type> - 1);                       \
            (inf).name[std::extent_v<type> - 1] = '\0';                                \
        } else {                                                                       \
            (inf).name = (type)(get);                                                  \
        }                                                                              \
    }
```

Key elements:
- `if (when)` — emit_when boolean from registry; gates whether THIS field gets populated
- `STAMP_AUTOPOPULATE_SET_HAS_##group(name)` — sets the right has_* (group bit for grouped entries; entry bit for standalone)
- `if constexpr (std::is_array_v<type>)` — char[N] vs scalar dispatch via type traits
- Caller variables `inf` (target struct) + scope variable referenced in `get` expression

### Step 2: Group-aware has_* dispatch

Token-paste pattern dispatches on the registry's `group` column:

```cpp
#define STAMP_AUTOPOPULATE_SET_HAS__(name)                  (inf).has_##name = 1
#define STAMP_AUTOPOPULATE_SET_HAS_inference_cfg(name)      (inf).has_inference_cfg = 1
#define STAMP_AUTOPOPULATE_SET_HAS_scaler(name)             (inf).has_scaler = 1
#define STAMP_AUTOPOPULATE_SET_HAS_fees(name)               (inf).has_fees = 1
#define STAMP_AUTOPOPULATE_SET_HAS_xgb_hyperparams(name)    (inf).has_xgb_hyperparams = 1
#define STAMP_AUTOPOPULATE_SET_HAS_grid_member(name)        (inf).has_grid_member = 1
#define STAMP_AUTOPOPULATE_SET_HAS_label_params(name)       (inf).has_label_params = 1
```

For `group="_"` (standalone), `STAMP_AUTOPOPULATE_SET_HAS_##_` becomes `STAMP_AUTOPOPULATE_SET_HAS__` which sets `has_<name>` directly.

For each group, `STAMP_AUTOPOPULATE_SET_HAS_##<groupname>` becomes `STAMP_AUTOPOPULATE_SET_HAS_<groupname>` which sets `has_<groupname>`.

Adding new group: 1 new dispatcher #define line. Adding new entry to existing group: 0 new dispatcher #defines (reuses existing).

### Step 3: Top-level AUTOPOPULATE macro

```cpp
#define STAMP_MODEL_CONST_AUTOPOPULATE(inf, src)                                     \
    do {                                                                              \
        _Pragma("GCC diagnostic push")                                                \
        _Pragma("GCC diagnostic ignored \"-Wunused-value\"")                          \
        FOREACH_STAMP_BOUND_MODEL_CONST(STAMP_MODEL_CONST_AUTOPOPULATE_ONE)           \
        _Pragma("GCC diagnostic pop")                                                 \
    } while (0)
```

Caller usage:
```cpp
StampInferenceCfgInputs inf{};
STAMP_MODEL_CONST_AUTOPOPULATE(inf, source_state);
stamp_write_for_model(..., &inf);
```

### Step 4 (optional): Belt-and-suspenders sentinel

Add a `_autopopulate_called` boolean to the struct:

```cpp
struct StampInferenceCfgInputs {
    uint64_t has_flags;
    bool _autopopulate_called;
    // ... fields
};

#define STAMP_MODEL_CONST_AUTOPOPULATE(inf, src)                                     \
    do {                                                                              \
        FOREACH_STAMP_BOUND_MODEL_CONST(STAMP_MODEL_CONST_AUTOPOPULATE_ONE)           \
        (inf)._autopopulate_called = true;                                            \
    } while (0)

// At downstream consumer:
inline StampWriteResult stamp_write_for_model(..., const StampInferenceCfgInputs* inf) {
    if (inf && !inf->_autopopulate_called) {
        // CRITICAL log + REFUSE: production caller forgot AUTOPOPULATE
    }
    // ... rest
}
```

Adds runtime check (boot-only, ~1ns) that catches future contributors who add a NEW production-caller construction site but forget AUTOPOPULATE. Defensive — costs 1 byte per struct, negligible.

---

## Trade-offs + when to apply

### Apply when:
- The pattern "add field to struct + forget to populate at production caller" has recurred 2+ times (recurring-bug class signal)
- The struct is constructed at multiple production sites (1 site = manual is fine)
- Field count growth is open-ended (not capped at small N)
- Compile-time enforcement is achievable (the registry pattern provides the X-macro)

### Skip when:
- Single production-caller site (use grep audit; structural overhead exceeds benefit)
- Field set is closed and small (5-7 fields max; no growth pressure)
- Per-field population logic varies wildly per field (autopopulate's uniform `if (when) inf.X = (type)(get)` doesn't fit)

### Cost:
- ~30-50 LOC for AUTOPOPULATE companion macros + dispatch helpers
- ~5-15 min per existing production-caller site to migrate from manual to AUTOPOPULATE call
- Sentinel adds 1 byte + 1 runtime check (negligible)

### Win:
- N-site bug class structurally extinct
- New field addition: 1 row in registry; AUTOPOPULATE auto-handles it at next compile
- Recurrence cost (was: 1-3h debug + retraining per instance) → 0
- Caller code becomes 1-line vs N-line manual population block

---

## Reference implementations

### First applied: STAMP_CFG_AUTOPOPULATE (v5.14.1.E.E.B)

- Registry: `ML_Headers/StampBoundCfgRegistry.hpp` (FOREACH_STAMP_BOUND_CFG)
- Companion macro: `STAMP_CFG_AUTOPOPULATE`
- Production caller migrated: `Backtest/BacktestEngine.hpp` (Train Model worker at ~line 1147)
- Closes: PARITY-002, -003, -004, -005, -008 (5 recurrences of v5.9.5b class)

### Second application: STAMP_MODEL_CONST_AUTOPOPULATE (v5.14.8.A.merged)

- Registry: `ML_Headers/StampBoundModelConstRegistry.hpp` (FOREACH_STAMP_BOUND_MODEL_CONST)
- Companion: `STAMP_MODEL_CONST_AUTOPOPULATE`
- Production callers: `Backtest/BacktestPanels.hpp:3206` + `Backtest/BacktestEngine.hpp:1147`
- Closes TECH_DEBT-006 + extinguishes class for architectural stamp body fields

### Pattern fully extinguished for stamp body domain after v5.14.8.A.merged

Both cfg-bound + architectural stamp body fields are now AUTOPOPULATE-driven. Future stamp body field additions auto-flow without any production-caller manual updates.

---

## Lessons / gotchas

### Caller variable names are HARD-CODED in the registry

The `get_value_expr` column references caller-scope variables (e.g., `cfg.ridge_within_horizon` or `inf->confidence_threshold_scale`). Production callers MUST name their variables to match what the registry references. Document this in the registry header.

Trade-off: registry knows caller scope (one-way coupling — registry depends on caller var names). Acceptable because there's typically ONE conceptual call shape; alternatives (lambdas, function pointers) add C++-class-flavored indirection.

### `if constexpr` type dispatch must cover ALL types in the registry

If the registry has a `tt::stamp_str_65` entry but AUTOPOPULATE_ONE's if constexpr branch only handles scalar types, the char-array entry compiles wrong (or fails). Add an `else if constexpr (std::is_array_v<type>)` branch. Use `std::extent_v<type>` to get the array size at compile time.

Pattern: each new type in the registry → 1 new `if constexpr` branch in AUTOPOPULATE_ONE + parser dispatch. Mechanical and discoverable.

### Group has_* dispatch requires per-group #defines

Each group gets one `STAMP_AUTOPOPULATE_SET_HAS_<groupname>` dispatcher macro. Adding a new group = 1 new macro definition. Caught by build-time test that asserts `FOREACH_GROUPS_COUNT == STAMP_AUTOPOPULATE_DISPATCHER_COUNT`.

### emit_when and the AUTOPOPULATE-time vs emit-time distinction

`emit_when` in the registry tuple is evaluated at AUTOPOPULATE time. It typically references `inf->has_<group>` — but at AUTOPOPULATE time, that bit may not be set yet.

Two design intents:
1. Caller manually pre-sets `has_<group>=1` BEFORE AUTOPOPULATE. AUTOPOPULATE only populates fields when caller decided to bind that group.
2. AUTOPOPULATE sets `has_<group>` itself based on a different condition (e.g., `cfg.X != 0` for "operator opted into this feature").

Pattern (1) makes AUTOPOPULATE the conditional populator. Pattern (2) makes AUTOPOPULATE the unconditional populator with cfg-driven gating.

FOREACH_STAMP_BOUND_CFG uses pattern (2) — emit_when references `cfg.X` (operator-driven). FOREACH_STAMP_BOUND_MODEL_CONST currently uses pattern (1) — emit_when references `inf->has_<group>` (caller-driven precondition).

Document the chosen pattern per registry to avoid confusion.

### Sentinel runtime check is opt-in

The `_autopopulate_called` sentinel is defense-in-depth. For most cases, structural extinction (AUTOPOPULATE picks up new fields) is sufficient. Add the sentinel when:
- The downstream consumer can act on the failed check (REFUSE load, log CRITICAL)
- The struct is large enough that 1 byte sentinel + 1 runtime branch is negligible
- The historical recurrence is severe enough that defense-in-depth is warranted

---

## Patterns NOT used here (and why)

### `[[nodiscard]]` attribute on the struct

Doesn't apply — the struct is a passive data container; nothing's "discarded".

### Constructor-required fields (no default-construction)

Tried during exploration. Rejected because:
- C-style struct (no constructors enforced)
- Snapshot serialization requires default-construct + memcpy
- Forces production callers into a constructor signature that grows with each new field (same N-site problem)

### Verification at type-system level (template tag types)

Considered: a template parameter that says "this struct was AUTOPOPULATE'd". Too heavy; runtime sentinel is simpler.

---

## Cross-references

- `x-macro-registry-with-presence-dispatch.md` — the registry pattern AUTOPOPULATE complements
- `bitmap-flag-api.md` — has_flags storage backend
- `wire-format-byte-preservation-discipline.md` — AUTOPOPULATE preserves wire format byte-for-byte under all-or-nothing population semantics
- FoxML_Trader_v2 `DOCS/RECURRING_BUG_PATTERNS.md` Class 14 — production-caller class catalog entry
- FoxML_Trader_v2 `CLAUDE.md` item 13 — auto-populate companion macro discipline
- FoxML_Trader_v2 `DOCS/PARITY_ISSUES.md` PARITY-002/003/004/005/008 — historical recurrences
