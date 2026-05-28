---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-16
tags: [framework-discipline, branchless-discipline, structural-fix]
surface: [registry, hot-path]
sister_specs: [dual-axis-y3-dispatch-pattern.md, multi-bit-state-encoding-pattern.md, x-macro-registry-with-presence-dispatch.md]
applies_at_skills: []
---

# Multi-state dispatch with per-state update metadata

**Stage:** Stage 2 DRAFT v1.0 → Stage 3 ACTIVE v1.0 at v5.15.5.F.4d ship close
**Author intent:** capture the pattern before code lands so the first canonical application validates the documented design rather than rationalizes the implemented one (per `pattern-codification-lifecycle.md`)
**Closes:** Class 18 (mirror-incomplete) + Class 19 (hardcoded enum names) + Class 24 (capability-cfg surface mismatch) + Class 28 (branchy SP/HP dispatch) structurally for the dispatch family

---

## Summary

When an algorithm enum has N states whose behaviors *differ asymmetrically* — e.g., some states update one piece of state, others update a different piece, others update both — encode the per-state behavior in the X-macro registry row's METADATA COLUMNS, not in dispatch-site mask constants. Dispatch sites read the metadata; the masks, function-pointer tables, and slow-path-gate predicates are all auto-computed via X-macro reduction. Adding a new state row = 1 row change that defines the new state's complete behavior in-place + auto-extends every dispatch site that consumes the metadata.

This is a specialization of `x-macro-registry-with-presence-dispatch.md` for the case where each row needs ROW-LOCAL declarative metadata about its dispatch behavior, not just an apply-fn pointer. Composes with `branchless-dispatch-discipline.md` Pattern 1 (auto-derived fn-pointer table), `sink-fn-pointer-for-optional-side-effect-pattern.md` Pattern 5 (per-state optional side-effect emit), and `cfg-scope-discipline.md` (per-node direct registration via `FOREACH_PER_CORE_CFG_FIELD`).

## When to apply

- An enum has ≥3 states OR has projected expansion past 3 states
- Per-state behavior splits along ≥2 orthogonal axes (e.g., "which posterior updates?" × "which array drives selection?" × "is this state experimental?")
- Adding a new state would otherwise require updating multiple "scattered" sites (mask constants, dispatch switch statements, etc.) — Class 18 mirror risk
- Static-time computation of derived dispatch state (masks, tables, predicates) from per-state metadata is valuable

When NOT to apply:
- 2-state enums (boolean dispatch — simple branch is fine OR Pattern 5 sink-fn-pointer if optional)
- States with truly identical behavior except for a single fn-pointer (use the simpler `x-macro-registry-with-presence-dispatch.md` shape)
- States whose dispatch logic is genuinely runtime-only (not derivable from compile-time metadata)

## Pattern shape

### Registry row shape — metadata columns alongside name + value

```cpp
// FOREACH_<ENUM_NAME>(X) registry — N+M columns per row:
//   1-2 columns: name + numeric value (required by enum gen + dispatch table)
//   1 column:    apply_fn pointer (the polymorphic dispatch endpoint)
//   M columns:   per-state metadata (declarative; describes ROW-LOCAL behavior on each axis)
//   1 column:    doc string (tooltip + future-reader context)
#define FOREACH_BANDIT_ALGORITHM(X) \
    /*  name                       value  apply_fn                      exp3_up  thompson_up  drives    doc */                  \
    X(  EXP3,                      0,    BanditAlgo_Exp3_Apply,         1,       0,           EXP3,     "Exp3-IX only; Thompson frozen")     \
    X(  THOMPSON,                  1,    BanditAlgo_Thompson_Apply,     0,       1,           THOMPSON, "Thompson only; Exp3 frozen")        \
    X(  EXP3_OP_THOMPSON_GHOST,    2,    BanditAlgo_Exp3_Apply,         1,       1,           EXP3,     "Exp3 drives; Thompson shadow-learns") \
    X(  THOMPSON_OP_EXP3_GHOST,    3,    BanditAlgo_Thompson_Apply,     1,       1,           THOMPSON, "Thompson drives; Exp3 shadow-learns") \
    X(  BLENDED,                   4,    BanditAlgo_Blended_Apply,      1,       1,           BLENDED,  "Experimental joint blend")
```

### Orthogonal axes structure — typical pattern

A frequently-occurring shape: per-state metadata splits into TWO orthogonal axes — one bitmap-style "which sub-states update?" and one enum-style "which sub-state drives the primary output?":

| Axis type | Example | Cells |
|---|---|---|
| **UPDATE axis** (bitmap of N independent sub-bits) | `(exp3_up, thompson_up)` — which posteriors update from each reward | 2^N possible values; one combination per row |
| **DECIDE axis** (single enum picking the primary output source) | `drives ∈ {EXP3, THOMPSON, BLENDED}` — which algorithm's output picks the actual decision | One value per row |

The cross-product is `(2^N) × |DECIDE|` possible cells; typically only a subset is legal. Repetition on the UPDATE axis is EXPECTED and CORRECT — multiple states can share the same update pattern (`(1, 1)` "both update") while differing on the DECIDE axis. The metadata makes this orthogonality explicit so future additions slot in naturally.

For the bandit example: `(1, 1)` appears 3× (states 2, 3, 4) because "both algorithms learn" is shared by 3 different decision-drivers. The mask reductions (below) OR-fold each axis bit independently, so the repetition is harmless — it produces the correct aggregate mask.

The compile-time `(0, 0)` "dead state" assertion (below) catches the one cell that should never be a legal row.

### Auto-computed dispatch masks via X-macro reduction

Each UPDATE axis column drives a per-axis mask reduction. The mask bit at position `value` is the row's metadata value for that axis:

```cpp
// Reduction: OR-fold a per-row bit into a mask, where each row contributes
// (metadata_value << row_enum_value).
#define _AXIS1_MASK_BIT(name, val, fn, axis1, axis2, drives, doc) \
    | (((uint8_t)axis1) << val)
constexpr uint8_t AUTO_AXIS1_MASK = (uint8_t)0 FOREACH_BANDIT_ALGORITHM(_AXIS1_MASK_BIT);
#undef _AXIS1_MASK_BIT

#define _AXIS2_MASK_BIT(name, val, fn, axis1, axis2, drives, doc) \
    | (((uint8_t)axis2) << val)
constexpr uint8_t AUTO_AXIS2_MASK = (uint8_t)0 FOREACH_BANDIT_ALGORITHM(_AXIS2_MASK_BIT);
#undef _AXIS2_MASK_BIT
```

Adding a new state automatically extends both masks via the reduction. Adding a new orthogonal axis = 1 new column + 1 new mask reduction.

### Compile-time row-shape sanity assertions

```cpp
// Reject "dead state" rows: every state must update SOMETHING (at least one axis = 1).
// Adding a row with all axes = 0 fails build with a clear message naming the state.
#define _STATE_NONDEAD_ASSERT(name, val, fn, axis1, axis2, drives, doc) \
    static_assert((axis1) || (axis2), \
        "Enum state " #name " updates nothing — would be a dead state. " \
        "Either give it a behavior axis = 1 OR remove the row.");
FOREACH_BANDIT_ALGORITHM(_STATE_NONDEAD_ASSERT)
#undef _STATE_NONDEAD_ASSERT
```

### Predicate derivation — slow-path gates read masks, not hardcoded values

Slow-path gate predicates that previously hardcoded value checks (`(cfg.bandit_algorithm == 2)`) derive from the auto-computed masks instead. Adding a new state with metadata `(axis1=1, axis2=1)` automatically extends the predicate's "active" set without touching the predicate body:

```cpp
// Predicate: "this state has axis1 active" = bit `algo` set in AUTO_AXIS1_MASK
static inline bool state_updates_axis1(int algo) {
    return (algo >= 0 && algo < FOREACH_BANDIT_ALGORITHM_COUNT)
        && ((AUTO_AXIS1_MASK >> algo) & 1u);
}

// Predicate: "this state has BOTH axes active" = AND-fold of mask bits at position `algo`
static inline bool state_updates_both_axes(int algo) {
    return (algo >= 0 && algo < FOREACH_BANDIT_ALGORITHM_COUNT)
        && (((AUTO_AXIS1_MASK & AUTO_AXIS2_MASK) >> algo) & 1u);
}
```

The slow-path-gate registry consumes these derived predicates directly:

```cpp
X(PER_CORE, THOMPSON_ACTIVE,
  state_updates_axis2((_gate_cfg).bandit_algorithm),
  "Thompson posterior is being updated (any state with thompson_up=1)")

X(PER_CORE, BANDIT_SHADOW_LEARNING,
  state_updates_both_axes((_gate_cfg).bandit_algorithm),
  "Both algorithms learning from rewards (any state with exp3_up=1 AND thompson_up=1)")
```

Adding a 6th state with metadata `(1, 1)` automatically adds it to the `BANDIT_SHADOW_LEARNING` predicate's active set. Class 18 mirror closure works because adding a row with the right metadata extends every consumer that reads the masks.

## Composition with `branchless-dispatch-discipline.md` Pattern 1 (auto-derived fn-pointer table)

The dispatch site itself converts from a metadata-gated branchy form to a Pattern 1 fn-pointer table whose entries are auto-derived FROM the metadata via X-macro reduction. This combines two structural wins: branchless dispatch (H20) AND 1-row-mechanical future additions (framework discipline).

```cpp
// Type-erased handler signature; matches all per-state implementations.
template <unsigned F>
using RewardUpdateFn = void(*)(EnsembleModelZoo<F>*, int regime, int chosen_arm, double reward_bps);

// Per-axis handlers — one per (axis1, axis2) combination that needs to fire.
template <unsigned F>
inline void exp3_only_reward(EnsembleModelZoo<F>* ezoo, int regime, int arm, double r) {
    Bandit_Update(&ezoo->bandits[regime], arm, r);
}
template <unsigned F>
inline void thompson_only_reward(EnsembleModelZoo<F>* ezoo, int regime, int arm, double r) {
    ezoo->thompson_update_fn(&ezoo->thompson_bandits[regime], arm, r);  // Pattern 5 noop-safe
}
template <unsigned F>
inline void both_reward(EnsembleModelZoo<F>* ezoo, int regime, int arm, double r) {
    Bandit_Update(&ezoo->bandits[regime], arm, r);
    ezoo->thompson_update_fn(&ezoo->thompson_bandits[regime], arm, r);
}

// Dispatch table — entries computed at compile time from metadata via X-macro reduction.
// Adding a 6th state = 1 row in FOREACH_BANDIT_ALGORITHM → table auto-extends; no scattered changes.
#define _REWARD_DISPATCH_ENTRY(name, val, fn, exp3_up, thompson_up, drives, doc) \
    /* axis1×axis2 = 4 cells; (1,1) → both_reward; (1,0) → exp3_only; (0,1) → thompson_only; (0,0) → static_assert rejects */ \
    [val] = ((exp3_up) && (thompson_up)) ? &both_reward<F> \
          : (exp3_up)                    ? &exp3_only_reward<F> \
          : &thompson_only_reward<F>,

template <unsigned F>
static constexpr RewardUpdateFn<F> g_reward_dispatch[FOREACH_BANDIT_ALGORITHM_COUNT] = {
    FOREACH_BANDIT_ALGORITHM(_REWARD_DISPATCH_ENTRY)
};
#undef _REWARD_DISPATCH_ENTRY
```

Dispatch site at reward-attribution:

```cpp
// Branchless: 1 indirect call (~3-5ns deterministic); no per-state branch
g_reward_dispatch<F>[algo](ezoo, regime, arm, reward_bps);
```

This is Pattern 1 of `branchless-dispatch-discipline.md` SPECIALIZED for metadata-driven auto-derivation: the dispatch table isn't hand-coded — it's COMPUTED from the row metadata. Future row additions update the table automatically; no scattered changes; Class 18 + Class 28 closed in one shape.

## Composition with Pattern 5 sink-fn-pointer (per-state side effects)

When optional side effects (telemetry, calibration log emission, debug capture) should fire per certain states, compose with `sink-fn-pointer-for-optional-side-effect-pattern.md` Pattern 5: place the optional-emit fn-pointer on subsystem state with default = noop; set to real at boot if subsystem is enabled; ALWAYS call via fn-pointer (no callsite branch). Per-state semantics layer on top: the real fn can early-return based on metadata, OR a state-indexed table of fn-pointers selects per-state.

Example: per-trade-close calibration log emission. The calibration log should emit ALL diagnostic data (per-arm Thompson posteriors + per-arm Exp3 weights + cfg.bandit_algorithm + chosen arm + reward) whenever the calibration log file is configured — independent of state. Pattern 5 makes the callsite branchless. **Variant choice:** the GENERIC example below shows a STANDALONE parallel sink on subsystem state (for cases where no existing sister sink exists). If a sister sink already exists on a related subsystem (e.g., `oms->on_exit_calibration` already provides per-fill calib emission via Pattern 5), prefer **EXTENDING that existing sink** rather than adding a parallel one — see `sink-fn-pointer-for-optional-side-effect-pattern.md` Anti-pattern 4 ("parallel sinks") + the bandit/thompson canonical's actual choice (plan body § F at `.F.4d`):

```cpp
template <unsigned F>
struct EnsembleModelZoo {
    // ... existing fields ...
    void (*on_trade_close_calib_emit)(EnsembleModelZoo<F>*, int regime, int chosen_arm,
                                       double reward_bps, int active_state);
    // Default member init = &noop_calib_emit<F>; set to &real_calib_emit<F> at boot when
    // calibration_log_file != nullptr.
};

// Real emit reads ALL diagnostic state directly from ezoo at emit time (post-update state)
template <unsigned F>
inline void real_calib_emit(EnsembleModelZoo<F>* ezoo, int regime, int chosen_arm,
                            double reward_bps, int active_state) {
    // Reads ezoo->bandits[regime] + ezoo->thompson_bandits[regime] for per-arm columns;
    // emits via FOREACH_CALIB_LOG_COL registry walker. Maximum data; subsystem-gated; no
    // per-state branch (operator wants comprehensive diagnostic; state value itself is logged
    // as a column so analysis can filter post-hoc).
}
template <unsigned F>
inline void noop_calib_emit(EnsembleModelZoo<F>*, int, int, double, int) {}
```

The composition: metadata-driven dispatch (this spec) handles the STATE-conditional behavior; Pattern 5 sink-fn-pointer handles the SUBSYSTEM-conditional emission (calibration log enabled or not). Different axes; both branchless.

When per-state side effects DO differ semantically (e.g., one state's reward attribution emits to calibration log + another state's emits to a different log), the metadata can include a side-effect column (`emit_to_calib`, `emit_to_telemetry`) and the dispatch table at the emit site indexes by state into a Pattern 5 fn-pointer array auto-derived from the metadata column. Future side-effect axes = 1 metadata column added; emit table auto-extends.

## Composition with `cfg-scope-discipline.md` per-node registry (direct, NOT override-mechanism)

Per-node multi-state-dispatch enums (e.g., `bandit_algorithm` where different cores can run different bandit shapes) live as direct rows in `FOREACH_PER_CORE_CFG_FIELD` per `cfg-scope-discipline.md` § "Per-node default" rule. Each core's `cfg.cores[c].bandit_algorithm` is THE value for that core; no global default; no resolver; no inherit-sentinel.

```cpp
// Per-core cfg row — bandit_algorithm lives in FOREACH_PER_CORE_CFG_FIELD per cfg-scope-discipline default
// (set 2026-05-15 at v5.15.5.F.4c.3). Each core's cores[c].bandit_algorithm is THE value; no override
// mechanism; no global default to inherit from.
X(int, KIND_INT, bandit_algorithm, "Bandit Algorithm", "ML/Bandit",
    CfgFieldDescriptor::STAMP_BOUND | CfgFieldDescriptor::HAS_SIDE_EFFECT | CfgFieldDescriptor::WARN_ON_CLAMP,
    INT(0, 0, FOREACH_BANDIT_ALGORITHM_COUNT - 1),
    "Bandit selector: 5-state enum; see FOREACH_BANDIT_ALGORITHM tooltip",
    STRAT_CAT_ML, OP_MODE_CAT_ALL, REGIME_CAT_ALL, RISK_CAT_ALL, CfgFieldDescriptor::STRUCT_CFG)
```

Consumer functions read per-node via single-param `const PerCoreCfg<F>*` sig (Class 25 prevention):

```cpp
// Per-core consumer reads core_cfg->bandit_algorithm; type-system rejects scope erosion
void SomePerCoreFn(const PerCoreCfg<F>* core_cfg, ...) {
    int algo = core_cfg->bandit_algorithm;
    g_reward_dispatch<F>[algo](ezoo, regime, arm, reward_bps);
}
```

**FORBIDDEN composition (do NOT do):**

```cpp
// FORBIDDEN — extends the TRANSITIONAL PerCoreOverrides<F> mechanism (cfg-scope-discipline.md
// Anti-pattern 1; mechanism deletes at WIP2f). Use FOREACH_PER_CORE_CFG_FIELD direct registration
// instead.
#define PER_CORE_OVERRIDE_SCALAR_DOMAINS(X) \
    X(bandit_algorithm, int, BANDIT_ALGO_EXP3)   // NO
```

The override mechanism's sentinel-for-inherit shape is a relic of the pre-`.F.4c.3` "global default + per-instance override" anti-pattern. Direct per-node registration eliminates the sentinel entirely (each core's value is explicit; no inherit-from-where question).

## Composition with STAMP_BOUND parity binding

When the enum value is parity-relevant (training-time vs serve-time), tag the cfg field STAMP_BOUND. The derived filter framework (`.F.4d` series) automatically wires drift detection for the field; this pattern handles the per-state runtime semantics. The stamp body emits the engine-wide training-time cfg value (not per-node) — model carries its training-time mode; runtime drift check compares against current resolved per-node value.

## Composition with X_GEN_LABEL extern reuse (CLAUDE.md Class 19 prevention)

GUI labels for state names come from `X_GEN_LABEL` extern walking the X-macro registry — NO hardcoded label arrays. Adding a new state row also adds its GUI label automatically. The tooltip text comes from the `doc` column of the same row, also via X-macro reduction. Single source of truth for the state's identity, tooltip, and GUI label.

## What this pattern prevents

### Class 18 (Mirror-incomplete)

Adding a new state without updating dispatch-site mask constants → state's behavior never fires at the dispatch site. Bug class history:
- v5.15.5.A.2.a: per-arm-barriers data write without setting the arms_with_barriers_mask → ensemble barrier blending SILENTLY DISABLED
- v5.14.10.B (first canonical fix at v5.15.5.F.4d): `Thompson_Update` defined + tested but NEVER CALLED in production reward attribution → Thompson sampling effectively-disabled despite cfg=1 being settable

Both are the same shape: capability exists, dispatch site doesn't read it.

With this pattern: dispatch sites read FROM the metadata. The state row declares its own behavior. Adding a row that updates Thompson means setting `thompson_up = 1` in the row → mask recomputes → dispatch site reads new mask → behavior fires. Class 18 mirror closed at the row level.

### Class 19 (Hardcoded enum names)

Mask constants like `MASK_EXP3_UPDATE = (1<<0) | (1<<1)` hardcode state numerical values into named constants. Renumbering or reordering states silently breaks dispatch. With metadata-driven: row order + value are still the source of truth; mask bits are computed BY METADATA not BY HARDCODED VALUE.

### Class 24 (Capability-cfg surface mismatch)

The recurring class where ML capability exists in code but the dispatch/cfg surface doesn't expose it. This pattern fixes the structural cause: row metadata IS the dispatch source of truth, so a state cannot exist with behavior the dispatch site doesn't read.

### Class 28 (Branchy SP/HP data-dependent dispatch)

Composing with Pattern 1 fn-pointer dispatch tables (auto-derived from metadata) gives branchless SP/HP dispatch on the state value. Slow-path predicates derive from auto-computed masks instead of hardcoded value checks (`if (algo == 2)`) — also branchless via mask-extract. No data-dependent SP/HP branches on the state value remain after applying this pattern.

## Extensibility contract

**Adding a new state requires exactly ONE row addition.** The row carries its complete dispatch metadata. Masks recompute. Dispatch tables (Pattern 1) auto-extend. Slow-path predicates auto-extend. GUI labels auto-flow. Stamp body emit auto-flows (if STAMP_BOUND). Cfg parser accepts the new numeric value. Operator opt-in via `cfg.cores[c].<field> = N`. Dispatch sites work unchanged. Compile-time sanity assertions catch obvious mistakes (dead states `(0,0,...)`, non-dense enum values, mask overflow).

This is what "framework discipline meta-principle" (CLAUDE.md item 31) means in concrete terms for this pattern family.

## First canonical application

**v5.15.5.F.4d — Bandit 5-state ghost-training expansion**

- Registry: `ML_Headers/BanditAlgorithmRegistry.hpp` `FOREACH_BANDIT_ALGORITHM`
- States: EXP3 / THOMPSON / EXP3_OP_THOMPSON_GHOST / THOMPSON_OP_EXP3_GHOST / BLENDED (values 0..4; Option C semantic-preserving wire-format-byte numbering)
- Metadata axes: `exp3_up` (does this state update bandits[] from rewards?), `thompson_up` (does this state update thompson_bandits[] from rewards?), `drives` (which array does this state's apply_fn read for arm selection?)
- Auto-computed masks: `BANDIT_EXP3_UPDATE_MASK` + `BANDIT_THOMPSON_UPDATE_MASK`
- Auto-derived predicates: `MASK_THOMPSON_ACTIVE` (any thompson_up=1) + `MASK_BANDIT_SHADOW_LEARNING` (any exp3_up=1 AND thompson_up=1) — both via mask-extract from auto-computed masks
- Pattern 1 fn-pointer dispatch tables: `g_buy_reward_dispatch<F>[5]` + `g_exit_reward_dispatch<F>[5]` — entries computed from metadata at compile time
- Pattern 5 sink-fn-pointer composition: `ezoo->thompson_update_fn` (subsystem-gated noop-or-real for Thompson init guard). For calib emit path at the bandit/thompson canonical: **EXTEND existing `oms->on_exit_calibration` sink rather than adding parallel `ezoo->on_trade_close_calib_emit`** (per Anti-pattern 4 in `sink-fn-pointer-for-optional-side-effect-pattern.md` + plan body § F at `.F.4d`). The "Composes with Pattern 5" section above teaches the GENERIC parallel-sink variant; canonical applications check for existing sister sink first + prefer extension when available. Per-state branching ABSENT from callsites either way.
- Per-node registration: `bandit_algorithm` row in `FOREACH_PER_CORE_CFG_FIELD` (per `cfg-scope-discipline.md` default-per-node rule); NO override mechanism

Closes: Class 18 (mirror) + Class 19 (enum naming) + Class 24 (capability-cfg surface mismatch) + Class 28 (branchy SP/HP dispatch) recurrence risk for the bandit dispatch family.

## Future applications (anticipated)

- Strategy variant enum (when strategies grow asymmetric secondary axes — e.g., "uses-bandit?" / "uses-confidence?" / "has-side-effect?")
- Regime classifier states (when regime detection asymmetry grows)
- OMS reconcile mode enum (when modes split into more than the current 3-state)
- Fallback path selector (capability-on-mismatch / capability-off-on-mismatch / hybrid)

Adoption order: codify-on-first-application (this ship); audit cohort eligibility on subsequent enums per CLAUDE.local.md cohort-audit rule. After the 2nd application, extract a separate "compose-registry-via-metadata-axes" generic framework spec if the composition shape repeats with minor variations.

## Anti-patterns to avoid

- **Hardcoded mask constants** at dispatch sites (the Class 18 shape this pattern fixes)
- **Switch statements** dispatching on state value (works for 2-3 states; doesn't scale; reverses to mirror-incomplete on state addition)
- **Per-state mutable globals** carrying behavior config (race-prone; doesn't compose with per-node)
- **Sentinel enum values for "default" / "inherit"** when 0 is a valid state value (use direct per-node registration via `FOREACH_PER_CORE_CFG_FIELD` — no inherit-sentinel needed when each instance has its own explicit value)
- **Extending the TRANSITIONAL `PerCoreOverrides<F>` mechanism with new scalar-override X-macros** (`cfg-scope-discipline.md` Anti-pattern 1; mechanism deletes at WIP2f; future scalar overrides must go through `FOREACH_PER_CORE_CFG_FIELD` direct)
- **Hardcoding state-value checks in predicates** (`if (algo == 2)` instead of `(AUTO_MASK >> algo) & 1` — derive from auto-computed masks)

## Reference implementations

Populated at Stage 3 ACTIVE — shipped sites get file:line refs back-linked here.

- (pending at v5.15.5.F.4d ship close) `ML_Headers/BanditAlgorithmRegistry.hpp` — `FOREACH_BANDIT_ALGORITHM` with 7-column tuple including metadata columns (`exp3_up`, `thompson_up`, `drives`) — first canonical
- (pending at v5.15.5.F.4d ship close) `ML_Headers/bandit_dispatch_table.hpp` (NEW) — `g_buy_reward_dispatch<F>[5]` + `g_exit_reward_dispatch<F>[5]` Pattern 1 fn-pointer tables auto-derived via X-macro reduction from `FOREACH_BANDIT_ALGORITHM` metadata
- (pending at v5.15.5.F.4d ship close) `CoreFrameworks/SlowPathGateRegistry.hpp` — `THOMPSON_ACTIVE` + `BANDIT_SHADOW_LEARNING` predicates derive from auto-computed masks (NOT hardcoded value checks)

## Cross-references

- `x-macro-registry-with-presence-dispatch.md` — parent pattern this specializes
- `branchless-dispatch-discipline.md` — Pattern 1 (auto-derived fn-pointer table composition); Class 28 prevention
- `sink-fn-pointer-for-optional-side-effect-pattern.md` — Pattern 5 (per-state side-effect emit composition)
- `cfg-scope-discipline.md` — per-node direct registration (avoids the override-mechanism anti-pattern)
- `multi-bit-state-encoding-pattern.md` — sister pattern for K-state encoding in single records (different scope: single-record state encoding vs. dispatch metadata)
- `categorical-tag-applicability-pattern.md` — sister pattern for cfg-field categorical applicability (uses similar per-row metadata column approach)
- `pattern-codification-lifecycle.md` — workflow this followed (Stage 2 DRAFT ahead of first canonical application)
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 18 + Class 19 + Class 24 + Class 28 — bug classes this pattern structurally prevents
- CLAUDE.md item 31 — framework discipline meta-principle (this pattern is a concrete framework instance)
- CLAUDE.md H20 invariant — branchless preferred for SP/HP (Pattern 1 composition produces branchless dispatch)

---

**Stage 2 DRAFT v1.0 → Stage 3 ACTIVE v1.0 — promoted 2026-05-16 at v5.15.5.F.4d ship close.** First canonical: bandit 5-state ghost-training dispatch (`FOREACH_BANDIT_ALGORITHM` with metadata columns) + Pattern 1 fn-pointer dispatch table composition (buy + exit) + Pattern 5 sink-fn-pointer composition (thompson_update + calib emit) + auto-derived slow-path-gate predicates + per-node direct registration via `FOREACH_PER_CORE_CFG_FIELD`. Closes Class 18 + Class 19 + Class 24 + Class 28 structurally for the bandit dispatch family.
