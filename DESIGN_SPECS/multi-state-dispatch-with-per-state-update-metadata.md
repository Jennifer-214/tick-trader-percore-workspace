# Multi-state dispatch with per-state update metadata

**Stage:** Stage 2 DRAFT v1.0 (drafted ahead of first canonical application at v5.15.5.F.4c.2)
**Promotes to:** Stage 3 ACTIVE v1.0 at v5.15.5.F.4c.2 ship close
**Author intent:** capture the pattern before code lands so the first canonical application validates the documented design rather than rationalizes the implemented one (per `pattern-codification-lifecycle.md`)

---

## Summary

When an algorithm enum has N states whose behaviors *differ asymmetrically* — e.g., some states update one piece of state, others update a different piece, others update both — encode the per-state behavior in the X-macro registry row's METADATA COLUMNS, not in dispatch-site mask constants. Dispatch sites read the metadata; the masks (or fn-pointer tables) are auto-computed via X-macro reduction. Adding a new state row = 1 row change that defines the new state's complete behavior in-place.

This is a specialization of `x-macro-registry-with-presence-dispatch.md` for the case where each row needs ROW-LOCAL declarative metadata about its dispatch behavior, not just an apply-fn pointer.

## When to apply

- An enum has ≥3 states OR has projected expansion past 3 states
- Per-state behavior splits along ≥2 orthogonal axes (e.g., "which posterior updates?" × "which array drives selection?" × "is this state experimental?")
- Adding a new state would otherwise require updating multiple "scattered" sites (mask constants, dispatch switch statements, etc.) — Class 18 mirror risk
- Static-time computation of derived dispatch state (masks, tables) from per-state metadata is valuable

When NOT to apply:
- 2-state enums (boolean dispatch — simple branch is fine)
- States with truly identical behavior except for a single fn-pointer (use the simpler `x-macro-registry-with-presence-dispatch.md` shape)
- States whose dispatch logic is genuinely runtime-only (not derivable from compile-time metadata)

## Pattern shape

### Registry row shape — metadata columns alongside name + value

```cpp
// FOREACH_<ENUM_NAME>(X) registry — N+M columns per row:
//   1-2 columns: name + numeric value (required by enum gen + dispatch table)
//   1 column:    apply_fn pointer (the polymorphic dispatch endpoint)
//   M columns:   per-state metadata (declarative; describes ROW-LOCAL behavior)
//   1 column:    doc string (tooltip + future-reader context)
#define FOREACH_BANDIT_ALGORITHM(X) \
    /*  name                       value  apply_fn                      exp3_up  thompson_up  drives    doc */                  \
    X(  EXP3,                      0,    BanditAlgo_Exp3_Apply,         1,       0,           EXP3,     "Exp3-IX op only")     \
    X(  EXP3_OP_THOMPSON_GHOST,    1,    BanditAlgo_Exp3_Apply,         1,       1,           EXP3,     "Exp3 op; Thompson ghost") \
    X(  THOMPSON,                  2,    BanditAlgo_Thompson_Apply,     0,       1,           THOMPSON, "Thompson op only")     \
    X(  THOMPSON_OP_EXP3_GHOST,    3,    BanditAlgo_Thompson_Apply,     1,       1,           THOMPSON, "Thompson op; Exp3 ghost") \
    X(  BLENDED,                   4,    BanditAlgo_Blended_Apply,      1,       1,           BLENDED,  "Joint blend")
```

### Auto-computed dispatch masks via X-macro reduction

Each metadata column drives a per-axis mask reduction. The mask bit at position `value` is the row's metadata value for that axis:

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

### Dispatch-site usage

```cpp
// Dispatch site reads the auto-computed mask, not hardcoded constants:
static inline bool state_updates_axis1(int state_value) {
    return (state_value >= 0 && state_value < FOREACH_BANDIT_ALGORITHM_COUNT)
        && ((AUTO_AXIS1_MASK >> state_value) & 1u);
}

// At the actual dispatch:
const int algo = config->bandit_algorithm;
if (state_updates_axis1(algo)) { /* update axis-1 state */ }
if (state_updates_axis2(algo)) { /* update axis-2 state */ }
```

## What this pattern prevents

### Class 18 (Mirror-incomplete)

Adding a new state without updating dispatch-site mask constants → state's behavior never fires at the dispatch site. Bug class history:
- v5.15.5.A.2.a: per-arm-barriers data write without setting the arms_with_barriers_mask → ensemble barrier blending SILENTLY DISABLED
- v5.14.10.B (THIS pattern's first canonical fix at v5.15.5.F.4c.2): Thompson_Update defined + tested but NEVER CALLED in production reward attribution → Thompson sampling effectively-disabled despite cfg=1 being settable

Both are the same shape: capability exists, dispatch site doesn't read it.

With this pattern: dispatch sites read FROM the metadata. The state row declares its own behavior. Adding a row that updates Thompson means setting `thompson_up = 1` in the row → mask recomputes → dispatch site reads new mask → behavior fires. Class 18 mirror closed at the row level.

### Class 19 (Hardcoded enum names)

Mask constants like `MASK_EXP3_UPDATE = (1<<0) | (1<<1)` hardcode state numerical values into named constants. Renumbering or reordering states silently breaks dispatch. With metadata-driven: row order + value are still the source of truth; mask bits are computed BY VALUE not BY NAME.

### Class 24 (Capability-cfg surface mismatch)

The recurring class where ML capability exists in code but the dispatch/cfg surface doesn't expose it. This pattern fixes the structural cause: row metadata IS the dispatch source of truth, so a state cannot exist with behavior the dispatch site doesn't read.

## Extensibility contract

**Adding a new state requires exactly ONE row addition.** The row carries its complete dispatch metadata. Masks recompute. Dispatch sites work unchanged. Compile-time sanity assertions catch obvious mistakes (dead states, non-dense enum values, mask overflow).

This is what "framework discipline meta-principle" (CLAUDE.md item 31) means in concrete terms for this pattern family.

## Composition with other patterns

### With per-core override (this ship adds `PER_CORE_OVERRIDE_SCALAR_DOMAINS`)

A multi-state dispatch enum can become per-core-overridable by adding it to `PER_CORE_OVERRIDE_SCALAR_DOMAINS`. The composition:

```cpp
// Per-state metadata (this pattern) declares state behavior.
// Per-core override (PER_CORE_OVERRIDE_SCALAR_DOMAINS) declares which core sees which state.
// Together: each core independently picks its state; each state's behavior comes from its row metadata.
```

### With STAMP_BOUND parity binding

When the enum value is parity-relevant (training-time vs serve-time), tag the cfg field STAMP_BOUND. The derived filter framework (`.F.4d`) automatically wires drift detection for the field; this pattern handles the per-state runtime semantics.

### With X_GEN_LABEL extern reuse (CLAUDE.md Class 19 prevention)

GUI labels for state names come from `X_GEN_LABEL` extern walking the X-macro registry — NO hardcoded label arrays. Adding a new state row also adds its GUI label automatically.

## First canonical application

**v5.15.5.F.4c.2 — Bandit 5-state ghost-training expansion**

- Registry: `ML_Headers/BanditAlgorithmRegistry.hpp` `FOREACH_BANDIT_ALGORITHM`
- States: EXP3 / EXP3_OP_THOMPSON_GHOST / THOMPSON / THOMPSON_OP_EXP3_GHOST / BLENDED
- Metadata axes: `exp3_up` (does this state update bandits[]?), `thompson_up` (does this state update thompson_bandits[]?), `drives` (which array does this state's apply_fn read for arm selection?)
- Auto-computed masks: BANDIT_EXP3_UPDATE_MASK + BANDIT_THOMPSON_UPDATE_MASK
- Dispatch sites: 3 (or 4) reward-attribution call sites in `CoreModelZoo.hpp` + `ControllerEventLoop.hpp`
- Per-core override: yes — via `PER_CORE_OVERRIDE_SCALAR_DOMAINS` (sister X-macro shipped same ship)

Closes: Class 18 (mirror) + Class 19 (enum naming) + Class 24 (capability-cfg surface mismatch) recurrence risk for this family.

## Future applications (anticipated)

- Strategy variant enum (when strategies grow asymmetric secondary axes — e.g., "uses-bandit?" / "uses-confidence?" / "has-side-effect?")
- Regime classifier states (when regime detection asymmetry grows)
- OMS reconcile mode enum (when modes split into more than the current 3-state)
- Fallback path selector (capability-on-mismatch / capability-off-on-mismatch / hybrid)

Adoption order: codify-on-first-application (this ship); audit cohort eligibility on subsequent enums per CLAUDE.local.md cohort-audit rule.

## Anti-patterns to avoid

- **Hardcoded mask constants** at dispatch sites (the Class 18 shape this pattern fixes)
- **Switch statements** dispatching on state value (works for 2-3 states; doesn't scale; reverses to mirror-incomplete on state addition)
- **Per-state mutable globals** carrying behavior config (race-prone; doesn't compose with per-core override)
- **Sentinel enum values for "default"** when 0 is a valid state value (use the `override_presence` bit pattern from `PER_CORE_OVERRIDE_SCALAR_DOMAINS`)

## Reference implementations

(populates at Stage 3 ACTIVE — shipped sites get file:line refs back-linked here)

- (pending) `ML_Headers/BanditAlgorithmRegistry.hpp` — FOREACH_BANDIT_ALGORITHM with metadata columns (post-v5.15.5.F.4c.2)
- (pending) `ML_Headers/bandit_dispatch_mask.hpp` — auto-computed BANDIT_EXP3_UPDATE_MASK + BANDIT_THOMPSON_UPDATE_MASK

## Cross-references

- `x-macro-registry-with-presence-dispatch.md` — parent pattern this specializes
- `multi-bit-state-encoding-pattern.md` — sister pattern for K-state encoding in single records (different scope: single-record state encoding vs. dispatch metadata)
- `categorical-tag-applicability-pattern.md` — sister pattern for cfg-field categorical applicability (uses similar per-row metadata column approach)
- `pattern-codification-lifecycle.md` — workflow this followed (Stage 2 DRAFT ahead of first canonical application)
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 18 + Class 24 — bug classes this pattern structurally prevents
- CLAUDE.md item 31 — framework discipline meta-principle (this pattern is a concrete framework instance)

---

**Stage 2 DRAFT v1.0 — committed 2026-05-14 ahead of v5.15.5.F.4c.2 ship.** Promotes to Stage 3 ACTIVE v1.0 at ship close once reference implementations land.
