# Categorical tag applicability pattern — instance × category × consumer

**Established:** 2026-05-14 (v5.15.5.F.4 sprint — pre-implementation draft)
**Status:** DRAFT v1.0 (pre-coding spec; promotes to ACTIVE after `.F.4h` ships)
**Cross-references:**
- Parent: `x-macro-registry-with-presence-dispatch.md` (Y3 dispatch primitive; categorical applicability extends with bitmap-intersection runtime check)
- Parent: `heterogeneous-registry-pattern.md` (SCOPE COLUMN by Kind; categorical tags are a per-domain bitmap dispatch axis)
- Sister: `registry-tuple-as-single-source-of-truth.md` (tuple gains category-mask columns; this spec details the columns)
- Sister: `autopopulate-pattern-for-production-caller-class.md` (AUTOPOPULATE companions emit instance-side category declarations + consumer-side applicability checks)
- Sister: `bitmap-overflow-protection-discipline.md` (category mask uint widths require overflow static_assert guards)
- Composes with: `bitmap-flag-api.md` (category masks ARE bitmaps; `BITMAP_ANY` / `BITMAP_IS_SET` runtime check)
- Composes with: `multi-bit-state-encoding-pattern.md` (when category dimension is ordered K-state rather than independent flags; rare edge case)
- Composes with: `universal-cfg-field-registry-pattern.md` (first application — cfg fields tag applicable strategy/regime/risk/op_mode categories)
- Composes with: `wire-format-byte-preservation-discipline.md` (when category masks participate in HMAC-locked emit order — locked via CI hash test)
- FoxML_Trader_v2 `CLAUDE.md` items 13 (X-macro registry), 19 (structural fix preferred), 20 (BITMAP_*), 21 (AUTOPOPULATE companion)

---

## Problem statement

Many "X applies when Y is active" relationships exist in the engine:

- Cfg fields applicable only when certain strategies run (`bandit_blend_ratio` applies when ML strategies are active)
- Cfg fields applicable only in certain operational modes (`backtest_data_path` only in BACKTEST mode)
- ML features applicable only to certain regime types
- Risk parameters applicable only under certain trading modes
- GUI panels visible only when relevant subsystems are active

The straightforward implementation: hardcode the SPECIFIC instance name as the gating condition.

```cpp
// ANTI-PATTERN: hardcoded instance gating
if (strategy == STRATEGY_ML) render(cfg.bandit_blend_ratio);
if (strategy == STRATEGY_MOMENTUM) render(cfg.momentum_min_r2);
```

This works for single instances but fails the **N-instance generalization** test:

- Adding a new strategy (`STRATEGY_ENSEMBLE_V1`, `STRATEGY_HYBRID_V2`) means updating every gating condition that should apply to ML-style strategies
- "Strategy X uses a bandit" is the REAL predicate, not "strategy is named X"
- Multiple strategies might share capabilities (ML + future variants both use bandits); hardcoded names can't express the shared predicate without ORing instances
- Renaming a strategy cascades through every consumer's gating condition

This is the **Class 18 mirror at the predicate-condition level** — N consumers each expressing the same applicability predicate with hardcoded refs to specific instances, drifting as instances are added/renamed.

**Categorical tag applicability** generalizes the predicate:

- Each INSTANCE (strategy/regime/risk-mode/op-mode) declares its CATEGORIES (bitmap of capability tags)
- Each CONSUMER (cfg field, GUI widget, audit rule) declares the CATEGORY MASK it applies to
- RUNTIME applicability check: `BITMAP_ANY(consumer.applies_to_mask, active_instances_category_OR) != 0`

Categories describe **functional capability** axes (`USES_BANDIT`, `ONLINE_LEARNING`, `LONG_ONLY`, `REGIME_AWARE`); instances declare which categories they belong to; consumers gate on category membership rather than instance identity.

---

## Design space explored

### Option A: Hardcoded specific instances (the anti-pattern)

Each consumer enumerates applicable instance names directly.

**Rejected.** Class 18 mirror at predicate-condition level. Drift on every new instance.

### Option B: Categorical tags via per-domain bitmap (chosen)

Instances declare categories via bitmap; consumers declare category mask; runtime check is bitmap intersection.

**Wins:**
- Adding a new instance = declare its categories; all category-tagged consumers auto-apply
- Capability axes (categories) survive specific-instance churn
- Composable via bit-OR (instance belongs to multiple categories; cfg field applies to multiple categories)
- Branchless runtime check (1 AND + 1 compare)

### Option C: Hierarchical category inheritance

Categories have parent-child relationships. Declaring `USES_THOMPSON` implicitly declares parent `USES_BANDIT`.

**Rejected.** Hierarchies ossify design choices. Renaming a parent category cascades through inferred memberships. Explicit declaration of all applicable categories is verbose but honest + survives refactors. The CI consistency test (Test 3 below) catches missing-parent declarations without forcing hierarchy.

### Option D: String-tag applicability

Categories as string literals; instances declare an array of tag strings; consumers store tag strings; runtime check is string compare.

**Rejected.** Runtime cost (string compare vs single AND); typo-prone (no compile-time check on tag names); no bit-pack efficiency.

### Option E: Multi-domain composition (orthogonal extension of B)

Multiple categorical domains (strategy + regime + risk-mode + op-mode), each with its own bitmap. Consumer can declare applicability across multiple domains. AND across domains.

**Adopted as default form** alongside Option B. Each new categorical axis = new domain enum + new descriptor column; never runs out of bit space within a domain.

---

## The pattern (concrete shape)

### Step 1: Define category enum per domain

```cpp
// Strategy categories (uint32_t — 32 max; 10-15 used initially)
enum StrategyCategory : uint32_t {
    STRAT_CAT_STATIC_RULES         = 1u << 0,
    STRAT_CAT_REGRESSION_DRIVEN    = 1u << 1,
    STRAT_CAT_ML                   = 1u << 2,
    STRAT_CAT_ONLINE_LEARNING      = 1u << 3,
    STRAT_CAT_USES_BANDIT          = 1u << 4,
    STRAT_CAT_USES_THOMPSON        = 1u << 5,
    STRAT_CAT_USES_RIDGE           = 1u << 6,
    STRAT_CAT_USES_CONFIDENCE      = 1u << 7,
    STRAT_CAT_LONG_ONLY            = 1u << 8,
    STRAT_CAT_LONG_AND_SHORT       = 1u << 9,
    STRAT_CAT_REGIME_AWARE         = 1u << 10,
    STRAT_CAT_USES_DEPTH_DATA      = 1u << 11,
    STRAT_CAT_USES_FLOW_DATA       = 1u << 12,
    // ... room for 19 more bits ...
    STRAT_CAT_ALL                  = 0xFFFFFFFFu,
};

// Operational mode categories (uint16_t — 16 max; 5 used initially)
enum OpModeCategory : uint16_t {
    OP_MODE_CAT_LIVE        = 1u << 0,
    OP_MODE_CAT_PAPER       = 1u << 1,
    OP_MODE_CAT_BACKTEST    = 1u << 2,
    OP_MODE_CAT_TRAINING    = 1u << 3,
    OP_MODE_CAT_OFFLINE     = 1u << 4,    // any non-live mode
    OP_MODE_CAT_ALL         = 0xFFFFu,
};

// Regime categories (uint16_t — 4 used initially)
enum RegimeCategory : uint16_t {
    REGIME_CAT_TRENDING     = 1u << 0,
    REGIME_CAT_VOLATILE     = 1u << 1,
    REGIME_CAT_RANGING      = 1u << 2,
    REGIME_CAT_MILD_TREND   = 1u << 3,
    REGIME_CAT_ALL          = 0xFFFFu,
};

// Risk mode categories (uint16_t — 4 used initially)
enum RiskCategory : uint16_t {
    RISK_CAT_OFF            = 1u << 0,
    RISK_CAT_LINEAR         = 1u << 1,
    RISK_CAT_EXPONENTIAL    = 1u << 2,
    RISK_CAT_STEP           = 1u << 3,
    RISK_CAT_ALL            = 0xFFFFu,
};
```

**Overflow guard mandatory** (per `bitmap-overflow-protection-discipline.md`):

```cpp
static_assert(STRAT_CAT_USES_FLOW_DATA < (1ull << 32),
              "StrategyCategory overflowed uint32_t — upgrade to uint64_t");
static_assert(OP_MODE_CAT_OFFLINE < (1u << 16),
              "OpModeCategory overflowed uint16_t — upgrade to uint32_t");
```

### Step 2: Instance registry declares categories

`FOREACH_<INSTANCE>` tuple gains a category-mask column:

```cpp
// Tuple: X(NAME, category_mask, /* other instance-specific columns */)
//   NAME          — instance enum identifier
//   category_mask — bit-OR of all applicable category enums for this domain
//                   (use ALL to indicate universal applicability)

#define FOREACH_STRATEGY(X) \
    X(SIMPLE_DIP, STRAT_CAT_STATIC_RULES | STRAT_CAT_LONG_ONLY) \
    X(EMA_CROSS,  STRAT_CAT_STATIC_RULES | STRAT_CAT_LONG_AND_SHORT) \
    X(MOMENTUM,   STRAT_CAT_REGRESSION_DRIVEN | STRAT_CAT_USES_CONFIDENCE | STRAT_CAT_LONG_ONLY) \
    X(ML,         STRAT_CAT_ML | STRAT_CAT_ONLINE_LEARNING | STRAT_CAT_USES_BANDIT | \
                  STRAT_CAT_USES_THOMPSON | STRAT_CAT_USES_RIDGE | STRAT_CAT_USES_CONFIDENCE | \
                  STRAT_CAT_LONG_AND_SHORT | STRAT_CAT_REGIME_AWARE | STRAT_CAT_USES_DEPTH_DATA | \
                  STRAT_CAT_USES_FLOW_DATA)
```

Each instance explicitly declares ALL applicable categories — no implicit inheritance. Redundant declarations (`USES_THOMPSON` + `USES_BANDIT`) are FEATURES, not bugs: they're self-documenting and survive parent-category renames.

### Step 3: Compile-time lookup table

```cpp
constexpr uint32_t strategy_categories_lut[] = {
    #define X_GEN_CAT_ENTRY(name, cats) cats,
    FOREACH_STRATEGY(X_GEN_CAT_ENTRY)
    #undef X_GEN_CAT_ENTRY
};
```

Index by `Strategy` enum value → category mask. O(1) lookup; zero runtime cost; cache-warm after first access.

### Step 4: Consumer declares applicability mask

```cpp
// Cfg field registry row (universal-cfg-field-registry-pattern.md):
X(DOUBLE, bandit_blend_ratio, ..., applies_to_strategy_cat: STRAT_CAT_USES_BANDIT, ...)
X(DOUBLE, thompson_mu_prior,  ..., applies_to_strategy_cat: STRAT_CAT_USES_THOMPSON, ...)
X(DOUBLE, momentum_min_r2,    ..., applies_to_strategy_cat: STRAT_CAT_REGRESSION_DRIVEN, ...)
X(DOUBLE, take_profit_pct,    ..., applies_to_strategy_cat: STRAT_CAT_ALL, ...)
```

Cfg field declares the CATEGORY (capability) it cares about, not specific strategy names.

### Step 5: Runtime applicability check (bitmap intersection)

```cpp
// Compute active categories from active instances per-core:
uint32_t active_strategy_cats = 0;
for (int core = 0; core < N_CORES; core++) {
    Strategy s = cfg.core[core].strategy;
    active_strategy_cats |= strategy_categories_lut[s];
}

// Consumer check (per cfg field render):
if (descriptor.applies_to_strategy_cat & active_strategy_cats) {
    render(descriptor);
}
```

Branchless single-cycle AND-with-test. No string comparison; no switch-on-strategy.

### Step 6: Multi-domain composition

A consumer can declare applicability across multiple category-domains:

```cpp
X(DOUBLE, live_paper_balance, ...,
    applies_to_strategy_cat: STRAT_CAT_ALL,
    applies_to_op_mode_cat:  OP_MODE_CAT_LIVE | OP_MODE_CAT_PAPER,
    ...)
```

Runtime check is AND across domains (all domains must have non-empty intersection):

```cpp
bool applicable =
    (d.applies_to_strategy_cat & active_strategy_cats) &&
    (d.applies_to_op_mode_cat  & active_op_mode_cats);
```

Adding a new domain (e.g., `applies_to_gate_type_cat`) = new column in descriptor; never runs out of bit-space (each domain has its own uint16-32_t).

### Step 7: AUTOPOPULATE companion for emit

When the categorical metadata participates in serialization or HMAC bodies (rare; mostly for snapshot publish), use AUTOPOPULATE per `autopopulate-pattern-for-production-caller-class.md`. The category mask byte order matches enum bit order; locked via CI hash test per `wire-format-byte-preservation-discipline.md`.

---

## Vocabulary discipline rules

Categories proliferate without discipline. **5 rules:**

### Rule 1: Functional capability, not implementation detail

| ✅ Good | ❌ Bad |
|---|---|
| `STRAT_CAT_USES_BANDIT` (what it does) | `STRAT_CAT_INSTANTIATES_BANDIT_T_TEMPLATE` (how it's built) |
| `STRAT_CAT_REGIME_AWARE` (capability) | `STRAT_CAT_HAS_REGIME_DETECTOR_FIELD` (struct detail) |
| `OP_MODE_CAT_BACKTEST` (mode) | `OP_MODE_CAT_USES_HISTORICAL_DATA` (mechanism) |

Implementation choice can change without category rename; capability is the stable predicate.

### Rule 2: Operator-meaningful

Categories surface in GUI (Settings tab section names, tooltips, cfg.example comments). Names must make sense to non-developers:

✅ `OP_MODE_CAT_BACKTEST` — operator knows what backtest is
❌ `OP_MODE_CAT_NOT_LIVE_AND_NOT_PAPER_AND_NOT_TRAINING` — boolean compound; opaque

### Rule 3: Stable

Renaming a category breaks all consumers (`STRAT_CAT_USES_BANDIT` → `STRAT_CAT_BANDIT_FAMILY` would touch every registry row). Pick names that survive 3+ ships of evolution.

When renames are necessary, use **alias pattern**:

```cpp
// Transition period: both names valid; old registry rows compile unchanged
#define STRAT_CAT_USES_BANDIT STRAT_CAT_BANDIT_FAMILY
```

Migrate consumers at leisure; remove alias after a stable release cycle.

### Rule 4: Promoted from observed clustering (≥3 instances)

A category appears when 3+ instances share a capability. Don't preemptively create single-instance categories.

Example workflow: developer notices `STRATEGY_ML`, `STRATEGY_ENSEMBLE_V1`, `STRATEGY_HYBRID_GATE_V2` all call `Bandit_Update` → promote `STRAT_CAT_USES_BANDIT` after the 3rd instance.

Audit-driven promotion ensures vocabulary is grounded in code reality, not speculation. Audit script (`/dod-audit` extension) flags single-instance categories as candidates for either promotion-to-real-category or demotion-to-direct-instance-check.

### Rule 5: Tiered (core / specific / experimental)

Three category tiers, each with different stability guarantee:

| Tier | Stability | Example | Bit range |
|---|---|---|---|
| **CORE** | Stable across major versions | `STRAT_CAT_ML`, `STRAT_CAT_ONLINE_LEARNING` | bits 0-7 |
| **SPECIFIC** | Stable across minor versions; may evolve | `STRAT_CAT_USES_BANDIT`, `STRAT_CAT_USES_RIDGE` | bits 8-23 |
| **EXPERIMENTAL** | May be removed; aliased on removal | `STRAT_CAT_USES_THOMPSON_V2_ALPHA` | bits 24-31 |

Bit assignments cluster by tier for visual clarity. Tier reassignment (promoting EXPERIMENTAL → SPECIFIC) is a one-line change.

---

## Categorical applicability vs runtime cfg gating (composable axes)

Two distinct conditional axes — easy to conflate, important to keep separate:

| Axis | When defined | What it gates | Failure mode if confused |
|---|---|---|---|
| **Applicability (categorical)** | Static: declared in registry; based on instance capability tags | "Is the field RELEVANT to my current setup?" (would this field do anything if I edited it?) | Operator misses fields that ARE relevant but happen to be currently disabled |
| **Runtime gating (`requires_cfg`)** | Runtime: predicate on current cfg state | "Is the field's gating condition CURRENTLY enabled?" (will edits take effect right now?) | Operator sees fields they can edit but that have no effect until a parent flag is enabled |

**Example:** `thompson_mu_prior`:
- Applies-to: `STRAT_CAT_USES_THOMPSON` (only strategies CAPABLE of using Thompson see it)
- Requires-cfg: `bandit_algorithm == THOMPSON` (only when THOMPSON is CURRENTLY selected as the bandit algorithm)

Both must be true for GUI to show the field as active. Compose via AND:

```cpp
bool shown_and_editable =
    (descriptor.applies_to & active_cats) &&        // categorical applicability
    requires_cfg_satisfied(descriptor, cfg);        // runtime cfg gating
```

The **applicability** axis is the structural decision (what KIND of strategy can use this); the **runtime gating** axis is the operational state (what mode it's currently in).

**GUI affordance:** when a field is hidden due to applicability filter, optionally show "Show all settings" toggle that bypasses the categorical filter (operator can see all 213 fields when needed). When a field is visible but runtime-gated, gray out with tooltip "(disabled — requires `bandit_algorithm == THOMPSON`)".

---

## Cross-file cfg unification via `lives_in_struct` + `applies_to_op_mode_cat`

Engine has 4-5 cfg files: `engine.cfg`, `backtest.cfg`, `controller.cfg`, `secrets.cfg`, training params. Categorical applicability extends to unify these into one Settings tab + one registry:

```cpp
enum LivesInStruct : uint8_t {
    STRUCT_CFG             = 0,  // engine.cfg → ControllerConfig
    STRUCT_BACKTEST_CFG    = 1,  // backtest.cfg → BacktestCfg
    STRUCT_CONTROLLER_CFG  = 2,  // controller.cfg → ControllerCfg
    STRUCT_SECRETS_CFG     = 3,  // secrets.cfg → SecretsCfg
    STRUCT_TRAINING_CFG    = 4,  // training cfg (foxml_suite)
    // ... future cfg files add new enum values here ...
};

// Each cfg field declares:
// 1. Which struct it lives in (parser routes write to that struct via dispatch)
// 2. Which op-modes it applies to (GUI filters by current mode)
X(STRING, backtest_data_path, ...,
    lives_in_struct: STRUCT_BACKTEST_CFG,
    applies_to_op_mode_cat: OP_MODE_CAT_BACKTEST,
    applies_to_strategy_cat: STRAT_CAT_ALL,
    ...)
X(DOUBLE, take_profit_pct, ...,
    lives_in_struct: STRUCT_CFG,
    applies_to_op_mode_cat: OP_MODE_CAT_ALL,
    applies_to_strategy_cat: STRAT_CAT_ALL,
    ...)
X(STRING, binance_api_key, ...,
    lives_in_struct: STRUCT_SECRETS_CFG,
    applies_to_op_mode_cat: OP_MODE_CAT_LIVE,
    applies_to_strategy_cat: STRAT_CAT_ALL,
    metadata_flags: METADATA_IS_SECRET | METADATA_SAFETY_CRITICAL,
    ...)
```

**Settings tab** walks ONE registry; filters by `(applies_to_op_mode_cat & current_op_mode_cat) && (applies_to_strategy_cat & active_strategy_cats)`; routes save to the appropriate struct via `lives_in_struct` dispatch. Auto-generated `cfg.example` emits ONE file per `lives_in_struct` value, with category-grouped sections within each file.

This closes the **multi-cfg-file drift class**: one registry covers all cfg files; cfg surface is unified for operators; new cfg files added = new `lives_in_struct` enum value (no parser/save/GUI changes).

---

## CI consistency tests

Three tests verify categorical integrity at build time:

### Test 1: No orphan categories

```python
# CI script: for every defined STRAT_CAT_*, verify ≥1 strategy declares it
defined = grep_defined("STRAT_CAT_", in_files=["Strategies/StrategyCategories.hpp"])
declared = grep_declared_in_foreach("STRAT_CAT_", in_macro="FOREACH_STRATEGY")
orphans = defined - declared - {"STRAT_CAT_ALL"}  # ALL is a sentinel
assert orphans == set(), f"Orphan strategy categories: {orphans}"
```

Flags categories that exist in the enum but no strategy declares them. Either remove (dead) or assign to an instance.

### Test 2: No orphan cfg fields

```cpp
// Compile-time assert: every cfg row's applies_to_strategy_cat is non-zero
#define ASSERT_NON_ZERO_APPLIES(kind, name, label, section, meta, payload, tooltip, \
                                 applies_to_strategy, applies_to_op_mode, lives_in) \
    static_assert((applies_to_strategy) != 0, \
                  "Cfg field " #name " has no strategy applicability — use STRAT_CAT_ALL if universal");

FOREACH_CFG_FIELD(ASSERT_NON_ZERO_APPLIES)
```

Catches cfg rows that forgot to declare applicability.

### Test 3: Instance self-consistency (capability dependencies)

```python
# CI script: STRAT_CAT_USES_THOMPSON requires STRAT_CAT_USES_BANDIT (capability dep)
DEPENDENCIES = {
    STRAT_CAT_USES_THOMPSON: STRAT_CAT_USES_BANDIT,
    STRAT_CAT_USES_RIDGE:    STRAT_CAT_ML,
    STRAT_CAT_ONLINE_LEARNING: STRAT_CAT_ML,
}
for strategy in FOREACH_STRATEGY:
    for child, parent in DEPENDENCIES.items():
        if (strategy.cats & child) and not (strategy.cats & parent):
            fail(f"{strategy.name} declares {child} without parent {parent}")
```

Catches strategies that declare a child capability without its prerequisite parent.

### Test 4: Live-readiness gate (cross-domain consistency)

```python
# CI script: every cfg field with applies_to_op_mode_cat == OP_MODE_CAT_LIVE must also
# have a corresponding handling path in live-readiness boot gates
live_only_fields = grep_registry_filter(applies_to_op_mode_cat=OP_MODE_CAT_LIVE)
for field in live_only_fields:
    assert field.name in LIVE_READINESS_AUDIT_TABLE, \
        f"{field.name} is OP_MODE_CAT_LIVE but no boot-gate verification"
```

Optional; depends on how strict live-readiness is.

---

## Anti-patterns to avoid

### Anti-pattern 1: Hardcoded instance names in applicability gating

```cpp
// BAD — hardcoded strategy name
if (strategy == STRATEGY_ML) render(cfg.bandit_blend_ratio);
if (strategy == STRATEGY_ENSEMBLE_V1) render(cfg.bandit_blend_ratio);  // duplicate logic added when strategy added

// GOOD — categorical gating
if (descriptor.applies_to_strategy_cat & active_strategy_cats) render(descriptor);
```

Adding `STRATEGY_ENSEMBLE_V2` to the bad version means updating every gating condition. Good version auto-flows because `ENSEMBLE_V2` declares `STRAT_CAT_USES_BANDIT` in its category mask.

### Anti-pattern 2: Single-instance categories

```cpp
// BAD — category that only one strategy declares
enum StrategyCategory {
    STRAT_CAT_FOR_ML_STRATEGY_ONLY = 1 << 0,  // only STRATEGY_ML uses this
    // ... 30 more single-instance "categories" ...
};
```

Single-instance "categories" are really just instance identity hidden under a category name — same drift class as hardcoded names. **Rule: promote a category only when ≥3 instances share the capability** (Rule 4 above).

Audit detection: `/dod-audit` extension flags categories declared by <3 instances.

### Anti-pattern 3: Runtime gating in code instead of registry

```cpp
// BAD — gating logic scattered across multiple files
// In SettingsPanel.hpp:
if (cfg.bandit_algorithm == THOMPSON) render(cfg.thompson_mu_prior);
// In CfgValidator.cpp:
if (cfg.bandit_algorithm == THOMPSON && cfg.thompson_mu_prior < 0) error();
// In ModelInference.hpp:
if (cfg.bandit_algorithm == THOMPSON) bandit.set_mu(cfg.thompson_mu_prior);
```

The gating condition (`bandit_algorithm == THOMPSON`) is repeated 3× and could drift.

```cpp
// GOOD — registry centralizes the gating predicate
X(DOUBLE, thompson_mu_prior, ...,
    applies_to_strategy_cat: STRAT_CAT_USES_THOMPSON,
    requires_cfg: "bandit_algorithm == THOMPSON",
    ...)
```

GUI applies the gating uniformly; validators and consumers query the predicate from the registry; future audits validate every `requires_cfg` expression is reachable + non-contradictory.

### Anti-pattern 4: Multiple descriptors for similar surfaces

```cpp
// BAD — N parallel descriptors, each with its own parser/save/GUI dispatch
struct CfgFieldDescriptor          { ... };
struct BacktestCfgFieldDescriptor  { ... };  // 90% identical to CfgFieldDescriptor
struct ControllerCfgFieldDescriptor { ... }; // ...
struct SecretsCfgFieldDescriptor   { ... };  // ...
```

Multiple descriptors = N parallel parsers + N save dispatches + drift class returns when adding a feature (RESTART_REQUIRED, IS_SECRET, etc.) means updating N descriptors.

```cpp
// GOOD — ONE descriptor with lives_in_struct discriminator + extension points
struct CfgFieldDescriptor {
    Kind         kind;
    uint16_t     metadata_flags;       // METADATA_IS_SECRET, METADATA_RESTART_REQUIRED, etc.
    LivesInStruct lives_in_struct;     // discriminator for parser/save dispatch
    uint32_t     applies_to_strategy_cat;
    uint16_t     applies_to_op_mode_cat;
    /* ... */
};
```

Single source of truth; extension via metadata bits (`METADATA_IS_SECRET` for password masking) or new Kind values (KIND_RANGE_INT for training hyperparameter sweeps). Sidecar tables for sparse per-field data (encryption metadata, validation regex). **No descriptor proliferation.**

### Anti-pattern 5: Renaming categories without alias

```cpp
// BAD — direct rename breaks all registry rows referencing the old name
// Before: STRAT_CAT_USES_BANDIT = 1 << 4;
// After:  STRAT_CAT_BANDIT_FAMILY = 1 << 4;  // all consumers must update simultaneously
```

```cpp
// GOOD — alias pattern preserves backward compatibility during transition
enum StrategyCategory : uint32_t {
    STRAT_CAT_BANDIT_FAMILY = 1u << 4,  // new canonical name
    // ...
};
#define STRAT_CAT_USES_BANDIT STRAT_CAT_BANDIT_FAMILY  // transition alias

// Migrate consumers at leisure; remove alias after stable release cycle
```

### Anti-pattern 6: Vocabulary creep without audit

Categories invented opportunistically without checking the 3+ instances rule. Over time: dozens of single-instance pseudo-categories. Mitigation: `/dod-audit` extension flags single-instance categories as suspect.

### Anti-pattern 7: Implicit category hierarchy

```cpp
// BAD — assuming inheritance
// "If USES_THOMPSON is declared, USES_BANDIT is implied"
// (silent semantic; future maintainer might not know)
```

```cpp
// GOOD — explicit redundant declaration
X(ML, STRAT_CAT_USES_BANDIT | STRAT_CAT_USES_THOMPSON | ...)
```

Explicit redundancy is self-documenting + caught by CI Test 3 if the parent declaration is missing.

### Anti-pattern 8: Category bitmap overflow without static_assert

```cpp
// BAD — no overflow guard; future bit addition silently overflows uint16_t
enum SomeCategory : uint16_t {
    CAT_A = 1 << 0, CAT_B = 1 << 1, /* ... */, CAT_P = 1 << 15,
    CAT_Q = 1 << 16,  // SILENT TRUNCATION TO 0 on uint16_t
};
```

```cpp
// GOOD — overflow guard catches at compile time
static_assert(CAT_Q < (1ull << 16),
              "SomeCategory bitmap overflowed uint16_t — upgrade to uint32_t");
```

Per `bitmap-overflow-protection-discipline.md`. Every category enum needs the guard.

### Anti-pattern 9: Categorical metadata duplicated in code path checks

```cpp
// BAD — code reasoning about categories instead of querying lookup
if (strategy == STRATEGY_ML || strategy == STRATEGY_ENSEMBLE_V1) {
    // "ML-like" code path
}
```

```cpp
// GOOD — query the lookup
if (strategy_categories_lut[strategy] & STRAT_CAT_ML) {
    // ML-like code path; auto-includes future ML variants
}
```

Same N-instance class as hardcoded gating; just at a different surface.

### Anti-pattern 10: Cross-domain coupling via shared bits

```cpp
// BAD — shared bitmap across domains
enum AllCategories : uint64_t {
    STRAT_CAT_ML     = 1 << 0,
    OP_MODE_LIVE     = 1 << 1,  // sharing bit-space with strategy cats
    REGIME_TRENDING  = 1 << 2,
    // ...
};
```

Coupling: renaming one domain's enum touches the shared namespace; bit-allocation conflicts; harder to reason about which mask applies to what.

```cpp
// GOOD — independent uint per domain
enum StrategyCategory : uint32_t { /* ... */ };
enum OpModeCategory   : uint16_t { /* ... */ };
enum RegimeCategory   : uint16_t { /* ... */ };
```

Each domain has its own bit-space; never runs out via cross-domain conflict.

---

## Trade-offs + when to apply

### Apply when:
- Multiple consumers gate on "X uses capability Y" predicate
- Adding a new instance has been (or will be) a recurrent edit class
- Capability axes are stable enough for category names to survive 3+ ships
- Cross-instance commonality has 3+ representatives
- Domain has 2+ "applies_to" consumers (cfg, GUI, audit, snapshot, etc.)

### Skip when:
- Only one instance ever uses a capability (no shared predicate; just use instance name directly)
- Capability axes are highly volatile (categories rename every ship — vocabulary discipline fails)
- Set of instances is bounded + small (≤3); manual gating is tractable
- Single consumer (no parallel mirror; no drift class)

### Cost:
- Initial: ~80-150 LOC of category enum + instance category declarations + applicability checks + AUTOPOPULATE companions
- Ongoing: ~1 row per new instance (declare its categories) + ~1 row per new consumer (declare its applies_to mask)
- Audit: `/dod-audit` extension to verify rules + CI consistency tests (~30 min one-time)

### Win:
- N-site predicate mirror drift class structurally extinct
- Strategy / regime / risk-mode / op-mode evolution becomes mechanical: declare categories → consumers auto-apply
- GUI filtering by mode/strategy "just works"
- Single source of truth per domain
- Composable with `bitmap-flag-api` + `AUTOPOPULATE` + Y3 dispatch
- Decoupling-roadmap aligned: category masks are mmap-friendly + survive cross-process boundaries

---

## Reference implementations

### First application: v5.15.5.F.4 universal cfg field registry

`CoreFrameworks/CfgFieldRegistry.hpp` + `Strategies/StrategyCategories.hpp` + `Strategies/StrategyRegistry.hpp`.

- Strategy categories: 4 CORE + 6-8 SPECIFIC + room for EXPERIMENTAL
- Op-mode categories: 5 (LIVE/PAPER/BACKTEST/TRAINING/OFFLINE)
- Regime/Risk categories: 4 each (defaulted to ALL until v5.16 ships specialize)
- ~213 cfg fields gain `applies_to_strategy_cat` + `applies_to_op_mode_cat` columns
- Settings tab filters by active categories
- Cross-file unification via `lives_in_struct` for engine.cfg + backtest.cfg

### Second application: v5.16+ — feature category rollout

`ML_Headers/FeatureRegistry.hpp` extensions: each FOREACH_FEATURE entry gets a category mask. Future cfg fields gating per-feature subset can use FEATURE_CAT_* tags.

### Future application catalog

| Domain | Category enum | First application | Status |
|---|---|---|---|
| Strategies | `StrategyCategory` (uint32_t) | v5.15.5.F.4 universal cfg field registry | planned |
| Operational modes | `OpModeCategory` (uint16_t) | v5.15.5.F.4 cross-file cfg unification | planned |
| Regimes | `RegimeCategory` (uint16_t) | v5.16 regime-conditional cfg | future |
| Risk modes | `RiskCategory` (uint16_t) | v5.16 risk-mode-conditional cfg | future |
| ML features | `FeatureCategory` (uint16_t) | v5.16 feature-mode filtering | future |
| Gates | `GateCategory` (uint8_t) | future — latency-budget tier dispatch | candidate |
| Order types | `OrderTypeCategory` (uint8_t) | future — maker/taker dispatch | candidate (v6.0 maker work) |

Promotes to `CLAUDE.md` as a numbered item after the 2nd domain ships (v5.15.5.F.4 = strategy + op-mode = 2 domains → eligible at v5.15.5.F.4 close).

---

## Lessons / gotchas (collected as field-test data lands)

### Categorical applicability is GUI-only — parser/persist semantics unchanged

The applicability mask controls **DISPLAY**, not data flow. Parser writes cfg fields to their `lives_in_struct` regardless of current op-mode. Save writes them regardless. Runtime reads them regardless. Categorical filtering only hides them from operator UI when not applicable.

**Why this matters:** if the categorical filter has a bug (wrong mask), the worst case is operator UX confusion (field shown/hidden incorrectly). Engine behavior is unaffected. Bounds the bug surface for migration.

### Vocabulary lock-in risk is real

If the initial category vocabulary is wrong, renaming cascades. Mitigation:
1. Audit-driven vocabulary (don't invent; observe + promote from clustering)
2. Tiered tiers (EXPERIMENTAL bits can churn; CORE/SPECIFIC are stable)
3. Alias-on-rename pattern

### Compose with `bitmap-overflow-protection-discipline.md`

Every category enum gets the `static_assert(MAX_BIT_USED < sizeof(TYPE) * 8)` overflow guard. Without it, future category additions silently truncate. Sister pattern; co-required.

### Compose with `cfg-flag-eligibility-criteria.md` cohort audit

When adding a new boolean cfg field that has siblings in a category, audit the cohort (per `cfg-flag-eligibility-criteria.md`) — should the new field have the same applies_to_strategy_cat as its cohort? Or has the cohort drift? Cohort audit ensures intra-family categorical consistency.

---

## Cross-references

- `x-macro-registry-with-presence-dispatch.md` — Y3 dispatch primitive (parent)
- `heterogeneous-registry-pattern.md` — SCOPE COLUMN by Kind (sister)
- `registry-tuple-as-single-source-of-truth.md` — tuple expansion for multi-consumer support
- `bitmap-flag-api.md` — category masks are bitmaps; use `BITMAP_ANY` / `BITMAP_IS_SET`
- `bitmap-overflow-protection-discipline.md` — overflow guard for category masks (co-required)
- `multi-bit-state-encoding-pattern.md` — when category is ordered K-state (rare)
- `autopopulate-pattern-for-production-caller-class.md` — AUTOPOPULATE companions emit categorical declarations
- `universal-cfg-field-registry-pattern.md` — first application
- `wire-format-byte-preservation-discipline.md` — category mask byte-order CI hash test
- `cfg-flag-eligibility-criteria.md` — cohort audit for intra-family categorical consistency
- FoxML_Trader_v2 `CLAUDE.md` items 13 (X-macro registry), 19 (structural fix), 20 (BITMAP_*), 21 (AUTOPOPULATE)
- FoxML_Trader_v2 `DOCS/RECURRING_BUG_PATTERNS.md` — Class 18 mirror pattern at predicate-condition level (this spec's anti-patterns expand the catalog)
