# Easy Additions Invariants

**Read this before** adding a new strategy, ML feature, target, SHALT
code, halt reason, regime, or stateful GUI panel. Read also before
proposing a new "thing" category (some won't be worth standardizing —
this doc says which).

The codebase aims for one rule: **adding the next instance of an
extensibility category should touch as few sites as possible.** Most
common categories should be ≤3 sites. The X-macro registry is the
codebase's standard pattern.

---

## Standard X-macro pattern

Every category that's been standardized follows the same shape:

```cpp
// Define the registry as an X-macro list. Each entry = one row.
#define FOREACH_<CATEGORY>(X) \
    X(<id>, <name>, <metadata...>, <function pointer or sentinel>) \
    X(<id>, ...) \
    /* ... */

// Auto-generate consumers from the X-macro:
//   - enum constants
//   - name arrays for display
//   - dispatch tables (function pointer arrays)
//   - compile-time hash for fingerprint contribution

#define X(id, name, ...) <CATEGORY>_##id,
enum <Category>Id {
    FOREACH_<CATEGORY>(X)
    NUM_<CATEGORY>
};
#undef X
```

**Adding the N+1 instance:** append one row to `FOREACH_<CATEGORY>(X)`,
implement the function the row references, recompile. Every consumer
of the registry picks up the new entry automatically.

---

## Audited categories — pre-v5.8 → post-v5.8 (all shipped)

| Category | Pre-v5.8 sites | Post-v5.8 sites | Shipped in | Notes |
|---|---|---|---|---|
| Strategies | 8 | 3 | v5.8.0 | strategy file + `FOREACH_STRATEGY(X)` line + GUI color |
| ML features | 5-7 (per feature) | 2 | v5.8.1a + v5.8.1b | compute fn + `FOREACH_FEATURE(X)` line. Phase 2 split: 5.8.1a built infra + first 10; 5.8.1b migrated remaining 24 + flipped 5 callers + retired `ModelFeatures_Pack` |
| SHALT codes | 4 | 1 | v5.8.2 | one `FOREACH_SHALT(X)` row, names auto-gen, GUI mirror dropped |
| Controller halt_reason | 3 (+ 12 raw int sites) | 1 | v5.8.3 | one `FOREACH_HALT_REASON(X)` row + introduced `HALT_*` named constants from prior raw integers (3 direct + 8 indirect via `zero_gate(N)` lambda); `HALT_WARMUP=7` documented as reserved-but-unused |
| Regimes | 5 | 1 | v5.8.4 | one `FOREACH_REGIME(X)` row; `__has_include` fallback for `MILD_TREND_DEFAULT_STRATEGY` keeps public-release builds compiling |
| Stateful GUI panels | 4 | 2 | v5.8.4b | one `FOREACH_PANEL(X)` row + `_Init` stub. Only 4 of 14 panels are stateful — stateless 10 keep direct `GUI_Panel_X(snap)` calls. Render dispatch stays hand-coded (signatures non-uniform) — uniformization deferred to render-thread I/O cleanup |
| Backtest metrics | 5 (4-site drift) | 2 | v5.8.4c | one `FOREACH_BACKTEST_METRIC(X)` row + extracted `Compute_*` helpers in `CoreFrameworks/MetricCompute.hpp`. Reconciled 3 cross-site formula drifts (profit_factor zero-guards, expectancy fabs, max_drawdown two impls) |
| Targets (label_table) | already 2 | 2 | pre-v5.8 | reuses existing `label_table[]` in `Backtest/LabelFunctions.hpp` |
| Per-core overrides | 1 | 1 | done v5.0.x | already X-macroized as `PER_CORE_OVERRIDE_FIELDS` |

## Audited categories — DEFERRED (not standardized)

These were considered and rejected for v5.8. Each has a trigger
condition for revisiting.

| Category | Why deferred | Revisit when |
|---|---|---|
| Stateless GUI panels | `GUI_Panel_X(snap)` is already a 1-liner; abstraction adds complexity for no win | A stateless panel becomes stateful, OR 5+ are added at once |
| Snapshot fields (PerCoreSnap, TUISnapshot) | Each field is genuinely heterogeneous (different sources, types, update cadence). Abstraction cost > benefit | Individual cases — apply judgment per field |
| Cfg fields | Already covered by `CFG_PARSE_INT/FPN/PCT/STR/U32` macros | Group of 20+ related fields would benefit from a sub-X-macro |
| Health log categories | Already minimal touches (~2 sites: emit + log viewer filter) | Categories exceed 10 OR a category needs structured payload schema |
| REST endpoints (Binance) | Tightly coupled to single exchange. Belongs in broker-abstraction work | Adding a non-Binance broker |
| Order types | Currently small enum (MARKET_BUY/SELL); no pain | Adding OCO + LIMIT order types |
| Model backends | XGBoost only today | Adding LightGBM / PyTorch / etc |
| Test sections | Just `printf` banners; no abstraction needed | Never |
| Build flags | CMake-level; existing `-DUSE_*` pattern works | Never |

---

## Canonical signature audit (v5.8 Phase 0 finding)

For each category, every implementation must conform to a canonical
function signature. Drift between implementations = X-macro can't
write a uniform function pointer table.

### Strategy lifecycle (5 stages)

**`_Init` — uniform across all 5 strategies ✅**

```cpp
inline void <Name>_Init(
    <Name>State<F>* state,
    const RollingStats<F>* rolling,
    BuySideGateConditions<F>* buy_conds);
```

**`_Adapt` — drift detected ⚠**

4 of 5 strategies match:
```cpp
inline void <Name>_Adapt(
    <Name>State<F>* state,
    FPN<F> current_price,
    FPN<F> portfolio_delta,
    uint16_t active_bitmap,
    const BuySideGateConditions<F>* buy_conds,
    const ControllerConfig<F>* cfg);
```

`MLStrategy_Adapt` is the outlier — takes `const void* cfg` instead
of `const ControllerConfig<F>* cfg`. Likely was an include-cycle
workaround at the time of writing.

**Fix for v5.8.0:** add a thin adapter
`MLStrategy_Adapt_Canonical` that casts the void* and calls the
real function. The X-macro references the adapter. Real function
preserved for legacy callers.

**`_BuildParameters` — uniform across SimpleDip / MeanReversion / Momentum / EmaCross ✅**

```cpp
inline void <Name>_BuildParameters(
    const RollingStats<F, W>* rolling,
    const ControllerConfig<F>* config,
    FPN<F> allocated_balance,
    GateParameters<F>* out,
    <Name>State<F>* state = nullptr);
```

**`ML_BuildParameters` is different shape ⚠** — takes additional
`const RollingStats<F, WL>* rolling_long` parameter (ML uses long-
window features). The dispatcher in `Strategy_BuildParameters`
handles this via case-by-case dispatch.

**Fix for v5.8.0:** the X-macro can reference each strategy's
`_BuildParameters` directly via case-block dispatch (preserving
ML's wider signature) rather than via uniform function pointer.
Slightly less clean than full table-dispatch but matches existing
pattern.

**`_ExitAdjustSharded` — uniform across all 5 ✅**

Verified by `tools/calls_graph_diff.sh` — all 5 wired correctly
in `StrategyLifecycle.hpp`.

### ML feature compute (canonical post-v5.8.1b)

```cpp
template <unsigned F>
inline FPN<F> ML_Compute_<Name>(const FeatureComputeCtx<F>* ctx);
```

`FeatureComputeCtx` is the bundle of all available inputs (rolling,
EMA, ROR, flow, depth, spread). Each compute fn reads what it needs,
returns FPN<F>. `FPN_Zero` is the safe "I don't have data yet" return.

`Features_PackAll(ctx, out)` loops the registry, invokes each enabled
compute fn, writes float result into out[i]. `FEATURE_REGISTRY_HASH`
is an FNV-1a fold over enabled `(name, version)` pairs and contributes
to the model fingerprint — flipping the hash forces retrain via
`MODEL_FORMAT_VERSION` rejection at load.

### Backtest metric compute (canonical post-v5.8.4c)

```cpp
static inline double Compute_<MetricName>(<scalar inputs>);
static inline void   <Stateful>_UpdateIncremental(/* in-out state */);
```

Helpers in `CoreFrameworks/MetricCompute.hpp` (CoreFrameworks-level
so both runtime and backtest paths can include without crossing the
runtime → backtest-suite layering). `MaxDrawdown_UpdateIncremental`
is the canonical example of "shared inner helper called from two
different cadences" — post-hoc walk in `BacktestStats_ComputeFromEquity`
loops it; per-tick replay in `BacktestSharded` invokes it once per
sample. Same code path → bytewise FP identity by construction (formal
equivalence ≠ bytewise equivalence for floating-point; structural
single-source eliminates drift class).

`FOREACH_BACKTEST_METRIC(X)` is metadata-only (name + printf format),
not dispatch — the Compute_* helpers take varying input shapes and
aren't function-pointer dispatchable.

### Target / label functions (already canonical via label_table)

```cpp
inline float Label_<Name>(
    const HistoricalTick* ticks,
    int n_ticks,
    int idx,
    /* label-specific params */);
```

Returns float label value. label_kind dictates interpretation
(0=binary, 1=regression, ≥2=multiclass).

---

## Public/private split

Some implementations live in `Strategies/private/` (alpha-flavored).
Currently this is just `EmaCross.hpp`. The X-macro should
conditionally include via `__has_include`:

```cpp
#define FOREACH_STRATEGY(X) \
    X(MEAN_REVERSION, /* ... */) \
    X(MOMENTUM,       /* ... */) \
    X(SIMPLE_DIP,     /* ... */) \
    X(ML,             /* ... */) \
    EMACROSS_X_LINE(X)

#if __has_include("private/EmaCross.hpp")
#  define EMACROSS_X_LINE(X) \
    X(EMA_CROSS, /* ... */)
#else
#  define EMACROSS_X_LINE(X) /* nothing */
#endif
```

**Honest caveat (2026-05-01):** the existing README claim "rm -rf
Strategies/private/ and the build still passes" is aspirational.
Removing private/ today breaks compilation because `EmaCrossState<F>`
references in StrategyParameters.hpp + StrategyLifecycle.hpp aren't
guarded. v5.8.0 Phase 0 added `__has_include` guards around the
`#include` statements, but the type-references still need
`#ifdef HAS_EMACROSS` guards for the public-release snapshot to work.
Filing as future work in `STRATEGY_REFACTOR_IDEAS.md`.

---

## Recurring bug pattern this prevents

**Class 1 — Strategy lifecycle orphans** (see
`DOCS/RECURRING_BUG_PATTERNS.md`). Adding a strategy stage in code
but forgetting the dispatcher wiring → silent dead behavior.
v5.4.0 had this in all 5 strategies for `_Init`, `_Adapt`,
`_BuySignal`, `_ExitAdjust`. The X-macro registry forces the
dispatcher entry to exist or fail compilation.

**Prevention:** readiness Check 14 (function-pointer table
correctness) requires:
- Variant selection audit (which `_BuildParameters` did existing
  dispatcher reference?)
- Signature uniformity audit (this doc)
- `tools/calls_graph_diff.sh` before AND after
- Loop test that walks every X-macro entry asserting non-null
  function pointers
- Hash snapshot test for any hash that contributes to fingerprints

---

## Future categories to consider (not in v5.8)

If any of the following becomes painful in a future ship, revisit:

- **Risk gate types** — currently mixed (cfg-driven thresholds,
  hardcoded checks). Could become a registry with checker function
  pointers.
- **Notification channels** — when alerting infrastructure lands.
- **Backtest output formats** — CSV / JSONL / stamp metadata.
  Currently each is its own writer.
- **Model backends** — XGBoost only today. Future LightGBM /
  PyTorch would need an X-macro at the `Model_Load`/`Model_Predict`
  layer.

---

## Maintenance discipline

- **Don't add a category to the audit table without a real cost-benefit.**
  Theoretical "we might add 5 of these someday" doesn't justify the
  refactor.
- **Don't remove an entry from the deferred table without a trigger.**
  The triggers are in this doc for a reason.
- **When you add a new entry to a registry, verify** the
  `calls_graph_diff.sh` baseline still shows clean (no new orphans),
  the loop test passes, and any hash snapshot tests get their values
  updated deliberately.

---

## Storage classes within X-macro registries (v5.14.8+)

Some registries have entries that can be EFFICIENTLY STORED via different
mechanisms. v5.14.8 introduced the concept of explicit STORAGE CLASS per
entry, allowing the X-macro to dispatch storage strategy alongside
typed-value declaration.

### Storage class vocabulary

| Storage class | C++ representation | When to use |
|---|---|---|
| `BIT_FLAG` | 1 bit in a uint16_t / uint32_t / uint64_t bitmap | Boolean state (on/off, set/unset, fired/idle). Auto-allocates bit position. |
| `COUNTER_U32` | Standalone `uint32_t` field | Incrementing event counter (NaN events, stale events, retry counts). |
| `PERCENT_U8` | Standalone `uint8_t` field | 0-100 percentage (warmup progress, fill ratio). |
| `TYPED_VALUE` | Per-entry typed field (int, double, char[N], etc.) | Architectural metadata (timestamps, hashes, names, hyperparams). |

### Why BIT_FLAG matters

Reference precedent: CLAUDE.md item 1 (`Portfolio<uint16_t>` bitmap;
`OrderManagerState.order_bitmap`). Wins when applied:

1. **Memory compactness** — 64 binary states in 8 bytes (vs 64 bytes byte-per-flag)
2. **Branchless multi-flag check** — `(flags & (MASK_X | MASK_Y))` in a single uint64_t compare
3. **Atomic multi-flag update** — `__atomic_fetch_or` instead of N separate atomic stores
4. **Branchless "any flag set?" gate** — single uint64_t compare `(flags != 0)`
5. **Auto-allocated bit positions** via X-macro (no manual collision risk)
6. **Cache-friendly** — flag-state for an entire core fits in one word

### Group has_* flags (preserves existing wire-format semantics)

When migrating an existing structure that uses GROUP has_* flags (one
flag gates N typed fields populated together), the registry can
preserve the group semantic:

```cpp
// Two separate macros: groups + typed fields
//   GROUPS lists the group has_* names + their bit positions
//   FIELDS lists every typed value with its group association
//   group="_" means standalone (auto-allocates own has_* bit)

#define FOREACH_STAMP_BOUND_MODEL_CONST_GROUPS(X)                       \
    X(xgb_hyperparams,     "any XGBoost hyperparam set?")     /* bit 7 */ \
    X(stamp_inference_cfg, "any inference cfg field set?")    /* bit 8 */ \
    X(stamp_fees,          "fee rates set?")                  /* bit 9 */ \
    X(stamp_label_params,  "label params set?")               /* bit 10 */

#define FOREACH_STAMP_BOUND_MODEL_CONST(X)                              \
    /* bit 0 — standalone */                                            \
    X(training_poll_interval,    _,    uint32_t, "%u",   0,   /*...*/) \
    /* bit 1 — standalone */                                            \
    X(stamp_model_num_outputs,   _,    int,      "%d",   0,   /*...*/) \
    /* bit 7 (shared) — xgb_hyperparams group */                        \
    X(stamp_xgb_max_depth,       xgb_hyperparams,   int, "%d", 0, /*..*/) \
    X(stamp_xgb_learning_rate,   xgb_hyperparams,   double, "%.17g", 0.0, /*..*/) \
    /* etc */
```

Wire format preserved: existing stamps still emit per-group flag lines
(`has_xgb_hyperparams=1`, `xgb_max_depth=6`, ...). Internal storage
shifts from N×uint8_t flags to bit positions in a single uint64_t.
Caller migration: `m->has_X` → `STAMP_HAS(m, X)` accessor (mechanical
find/replace).

### Migration discipline (when applying BIT_FLAG to existing surface)

1. **Preserve wire format** — registry entry order must match canonical
   stamp body emit order. Verify byte-for-byte that v5.14.x stamps
   continue to load identically.
2. **Provide accessor macros** — `STAMP_HAS(result, name)`,
   `STAMP_SET(result, name)`, `STAMP_CLR(result, name)`. Callers don't
   touch raw bitmap fields.
3. **Document bit allocation** — comments in the registry show which
   bit means what. Future readers can cross-reference debug output.
4. **Compile-time uniqueness** — X-macro auto-allocates bits via counter;
   compiler enforces no duplicates. Manual bit assignment risks collisions.
5. **Round-trip test** — emit → parse → field-access must produce
   identical pre/post values for every registry entry.

### Candidate sites for BIT_FLAG application (TECH_DEBT-013 sweep)

Current byte-per-flag locations in the codebase that should adopt
BIT_FLAG when the next ship touches their surface:

| Site | Flags today | Bit-pack target | Notes |
|---|---|---|---|
| `ModelStampResult` has_* / `StampInferenceCfgInputs` has_* / `ModelHandle` has_* | 24+ | uint64_t `has_flags` | DONE in v5.14.8.A (mixed per-field + group semantics preserved) |
| `PerCoreSnap` failure-mode flags | 2 binary + 4 counters/percent | uint16_t `failure_flags` + standalone counters | DONE in v5.14.8.B/C via FOREACH_FAILURE_MODE registry |
| `PerCoreSnap` non-failure state flags (`ml_scaler_present`, `ensemble_active`, etc.) | 3-5 | merge into `failure_flags` OR new `state_flags` uint16_t | TECH_DEBT-013; trigger: next ship touching PerCoreSnap |
| `FOREACH_FEATURE.enabled` (40 features) | 40 byte-per-flag | uint64_t `enabled_bitmap` + `IS_FEATURE_ENABLED(i)` macro | TECH_DEBT-013; trigger: next FeatureRegistry storage refactor |
| `OrderManager.partial_exit_enabled` + `ExecutionCore.lat_enabled` | 2 | engine-wide uint16_t `cfg_flags` | TECH_DEBT-013; trigger: next ship adding 3+ engine-wide flags |
| `ControllerEventLoop.partner_pending_active` | 1 per-node | merge into per-node flags bitmap | TECH_DEBT-013; trigger: next ship adding 2+ per-node flags |
| `ShardedSnapshot.any_scaler_present` + `any_scaler_failed` | 2 | snapshot summary bitmap | TECH_DEBT-013; trigger: next ship touching snapshot serialization |
| `Order.is_maker` / `is_buyer_maker` / `Tick.is_buyer_maker` | per-record | Standalone — KEEP byte-per-flag | Per-record storage; bit-packing across records adds indirection cost > savings |
| `FeatureStandardizer.has_winsor_bounds` | 1 | could fold into scaler header bitmap | Low-priority (single flag); revisit when 3+ scaler-side flags exist |

When a future ship touches one of these surfaces and would otherwise
add another byte-per-flag field, **stop and apply BIT_FLAG instead**.
Each migration is small (~30 min for accessor-macro substitution at
caller sites). Cumulative win across all candidates: ~70-100 bytes per
core; cache-line alignment benefits compound.

---

## Post-v5.8 rule (CLAUDE.md decision #13)

**Any new category that requires multi-site addition must use an
X-macro registry from the start.**

Concretely: if you find yourself writing a comment like *"to add a
new X, append to enum here, then to names array there, then to
dispatcher case in another file..."* — stop. Use the X-macro idiom
instead. The pattern is mature; the compile-time enforcement
(`static_assert` on array-vs-enum size parity, `calls_graph_diff.sh`
on dispatch orphans) makes drift impossible by construction.

The audit table above is the binding registry of categories. Adding
a new category to the table is a deliberate act — document why the
category is "the next instance shape" and not just an ad-hoc enum +
names mirror.

Categories in the **DEFERRED** table can be promoted later if their
trigger condition fires. The trigger conditions exist precisely so
the bar for new category standardization is "real pain experienced",
not "theoretical scalability."
