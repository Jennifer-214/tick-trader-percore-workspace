---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-10
tags: [framework-discipline, branchless-discipline]
surface: [registry, slow-path]
sister_specs: [calibration-log-column-registry.md, x-macro-registry-with-presence-dispatch.md, registry-tuple-as-single-source-of-truth.md]
applies_at_skills: []
---

# Curve registry pattern (FOREACH_<DOMAIN>_CURVE — named compute fns chosen by enum)

**Established:** 2026-05-10 (v5.14.9.A — FOREACH_DEGRADATION_CURVE)
**Status:** ACTIVE
**Cross-references:**
- First application: `ML_Headers/ConfidenceScore.hpp:498-634` (FOREACH_DEGRADATION_CURVE)
- Sister pattern: `x-macro-registry-with-presence-dispatch.md` (registry shape)
- Sister pattern: `slow-path-gate-registry-pattern.md` (also slow-path, but boolean dispatch)
- BITMAP cousin: `bitmap-flag-api.md` (this pattern uses int enum, not bitmap)
- CLAUDE.md item 13 (X-macro for multi-site additions)
- CLAUDE.md item 17 (latency tracked) — slow-path dispatch ~1-2ns indirect call

---

## Problem statement

A feature has multiple named compute modes — risk degradation curves (LINEAR / EXP / STEP), label functions (forward_return / barrier_hit / triple_barrier), threshold curves, fee schedules, decay schedules, etc. An operator picks one via cfg (`risk_degradation_curve=1` or `risk_degradation_curve=LINEAR`); engine dispatches to the matching compute fn.

Naïve approach: enum + switch:

```cpp
enum DegradationCurve { CURVE_OFF, CURVE_LINEAR, CURVE_EXP, CURVE_STEP };
double scale(int curve, double conf, double full, double min, double min_pct) {
    switch (curve) {
        case CURVE_OFF:    return 1.0;
        case CURVE_LINEAR: return linear(conf, full, min, min_pct);
        case CURVE_EXP:    return exp_curve(conf, full, min, min_pct);
        case CURVE_STEP:   return step(conf, full, min, min_pct);
        default:           return 1.0;
    }
}
```

**Recurring pain points:**

1. **Adding a new curve touches 4+ sites:** enum entry + switch case + cfg parser (numeric + string forms) + cfg.example doc + (optionally) GUI dropdown + tests.
2. **Switch + branch:** N branches per dispatch; not branchless. Branch predictor handles cfg-stable curves OK, but mask-compute can't be applied.
3. **No reflection:** "list all curves" requires a parallel string table the operator must keep in sync with the enum.
4. **String parsing duplicates the table:** `if (strcmp(s, "LINEAR") == 0) return CURVE_LINEAR;` is a 4-line parallel list to the enum.
5. **Tests can't enumerate without hardcoding:** "test all curves at canonical input" requires the test author to list each curve manually — drift risk.

This is the same N-site bug class as cfg fields, has_* flags, failure modes. The X-macro registry pattern solves it for compute-fn dispatch.

---

## Design space explored

### Option A: enum + switch + parallel string table (current naïve baseline)

Already described above. Rejected: N-site additions.

### Option B: virtual function dispatch (C++ polymorphism)

```cpp
struct Curve { virtual double scale(...) const = 0; };
struct LinearCurve : Curve { ... };
```

**Rejected.** CLAUDE.md project conventions forbid virtual functions in hot/slow path code (CLAUDE.local.md STRATEGY_AND_CODING_RULES.md). Vtable indirection + heap allocation of curve objects + RAII overhead — anti-philosophy for this codebase.

### Option C: std::variant + std::visit

```cpp
using Curve = std::variant<Off, Linear, Exp, Step>;
std::visit([&](auto& c) { return c.scale(...); }, curve_obj);
```

**Rejected.** Same C++-class-flavored objection. std::visit emits a switch under the hood anyway; no perf win over Option A. Adds STL dependency + obscures the dispatch shape.

### Option D (chosen): X-macro registry + function-pointer dispatch table

```cpp
#define FOREACH_DEGRADATION_CURVE(X) \
    X(OFF,    0, Confidence_DegradationScale_Off,    "doc") \
    X(LINEAR, 1, Confidence_DegradationScale_Linear, "doc") \
    X(EXP,    2, Confidence_DegradationScale_Exp,    "doc") \
    X(STEP,   3, Confidence_DegradationScale_Step,   "doc")
```

- Enum auto-generated via `X_GEN_ENUM` walk
- Function-pointer dispatch table auto-generated via `X_GEN_FN_PTR` walk
- ToString / FromString auto-generated via `X_GEN_TOSTRING` / `X_GEN_FROMSTRING` walks
- Count auto-generated via X-macro `+1` reduction

Adding a new curve = 1 row + 1 free function. All sites mechanically extend.

**Trade-off:** dispatch goes from switch (Option A) → indirect call (Option D). Single function-pointer-table read + indirect call (~1-2ns on modern x86 with branch prediction on a cfg-stable curve choice). Slow-path-only dispatch absorbs this trivially.

---

## The pattern (concrete shape)

### Step 1: Forward-declare compute fns (one per curve)

```cpp
inline double Confidence_DegradationScale_Off    (double, double, double, double);
inline double Confidence_DegradationScale_Linear (double, double, double, double);
inline double Confidence_DegradationScale_Exp    (double, double, double, double);
inline double Confidence_DegradationScale_Step   (double, double, double, double);
```

All curves share the same signature (uniform dispatch contract). Branchless internals preferred (`fma` + `fmin/fmax`); cmov-friendly avoids per-curve branch overhead.

### Step 2: Registry tuple

```cpp
// Tuple: X(name, enum_value, compute_fn, doc_string)
//   name        — UPPERCASE token; used for CURVE_<name> enum
//   enum_value  — numeric value (chosen by author; serialized in cfg + stamp)
//   compute_fn  — free-function symbol matching the dispatch contract
//   doc_string  — operator-facing description for cfg.example + GUI tooltip

#define FOREACH_DEGRADATION_CURVE(X)                                                                  \
    X(OFF,    0, Confidence_DegradationScale_Off,    "disabled — factor=1.0; preserves pre-v5.14.9") \
    X(LINEAR, 1, Confidence_DegradationScale_Linear, "linear interp between (min, min_pct) and (full, 1.0)") \
    X(EXP,    2, Confidence_DegradationScale_Exp,    "quadratic falloff; preserves more size in middle") \
    X(STEP,   3, Confidence_DegradationScale_Step,   "binary 1.0 above midpoint else min_pct (debug)")
```

### Step 3: Auto-generated enum + count

```cpp
#define X_GEN_ENUM(name, val, fn, doc) CURVE_##name = val,
enum DegradationCurve {
    FOREACH_DEGRADATION_CURVE(X_GEN_ENUM)
};
#undef X_GEN_ENUM

// Count via +1 reduction
#define X_GEN_DEGRADATION_COUNT_ONE(name, val, fn, doc) +1
#define FOREACH_DEGRADATION_CURVE_COUNT (0 FOREACH_DEGRADATION_CURVE(X_GEN_DEGRADATION_COUNT_ONE))
```

NOTE: the count helper macro stays defined (used at consumer sites that walk the registry for bounds checks). Same pattern as FOREACH_STAMP_BOUND_CFG_COUNT.

### Step 4: Function-pointer dispatch table

```cpp
typedef double (*DegradationCurveFn)(double conf, double full, double min, double min_pct);

#define X_GEN_FN_PTR(name, val, fn, doc) fn,
static const DegradationCurveFn degradation_curve_fns[] = {
    FOREACH_DEGRADATION_CURVE(X_GEN_FN_PTR)
};
#undef X_GEN_FN_PTR
```

Array is indexed by enum value. **Important:** enum values must be dense + contiguous starting at 0. If a registry needs sparse enum values, use a switch dispatch instead (Option A) — fn-pointer table waste justifies it.

### Step 5: Auto-generated ToString / FromString

```cpp
static inline const char* DegradationCurve_ToString(int curve) {
    switch (curve) {
        #define X_GEN_TOSTRING(name, val, fn, doc) case val: return #name;
        FOREACH_DEGRADATION_CURVE(X_GEN_TOSTRING)
        #undef X_GEN_TOSTRING
        default: return "INVALID";
    }
}

static inline int DegradationCurve_FromString(const char* s) {
    if (!s || !*s) return -1;
    if (s[0] >= '0' && s[0] <= '9') {
        int v = atoi(s);
        return (v >= 0 && v < FOREACH_DEGRADATION_CURVE_COUNT) ? v : -1;
    }
    #define X_GEN_FROMSTRING(name, val, fn, doc) \
        if (strcasecmp(s, #name) == 0) return val;
    FOREACH_DEGRADATION_CURVE(X_GEN_FROMSTRING)
    #undef X_GEN_FROMSTRING
    return -1;
}
```

FromString accepts both numeric form (`"1"`) and string form (`"LINEAR"`); case-insensitive on string. Returns -1 on miss. **Important:** FromString miss is OPERATOR ERROR — caller logs CRITICAL + REFUSEs cfg load (don't silently default).

### Step 6: Top-level dispatch wrapper (bounds-checked)

```cpp
static inline double Confidence_DegradationScale(int curve, double conf,
                                                  double full, double min, double min_pct) {
    if (curve < 0 || curve >= FOREACH_DEGRADATION_CURVE_COUNT) return 1.0;
    return degradation_curve_fns[curve](conf, full, min, min_pct);
}
```

Bounds-check guards against corrupted cfg / stamp-bound parse failures. The fn-ptr dispatch is ~1-2ns; bounds check is a single CMP+JLT (predictable, mostly-not-taken).

---

## Compute fn discipline

Each compute fn:

1. **Same signature** as the dispatch table contract (uniform).
2. **Branchless internals** preferred (use `fma`, `fmin`, `fmax`, ternary → cmov). Switch statements inside compute fns defeat the registry's dispatch advantage.
3. **Pure** (no side effects, no global state). Caller passes ALL inputs; compute fn returns single value.
4. **Defensive on degenerate inputs.** If `full <= min` (operator misconfig), return a sentinel (e.g., `min_pct`) instead of NaN/inf. Don't trust caller args.
5. **Documented endpoint behavior.** What's the value at `conf == min`? At `conf == full`? At `conf` between? Document so operators can reason about ladder shape.

Example (LINEAR):

```cpp
inline double Confidence_DegradationScale_Linear(double conf, double full, double min, double min_pct) {
    if (full <= min) return min_pct;  // misconfig guard
    double clamped = fmin(fmax(conf, min), full);
    double t = (clamped - min) / (full - min);  // ∈ [0, 1]
    return fma(t, 1.0 - min_pct, min_pct);      // min_pct + t*(1-min_pct)
}
```

`fmin/fmax` → cmov; `fma` → 1 cycle on modern x86. Whole function compiles to ~6-8 instructions.

---

## Trade-offs + when to apply

### Apply when:
- ≥3 named compute modes exist for the same domain (registry overhead justified)
- Mode is operator-selectable via cfg (string-form parsing needs the registry's FromString)
- Compute fns share a uniform signature (dispatch contract holds)
- Slow-path dispatch is acceptable (indirect call ~1-2ns; hot-path needs branchless inline)
- Future modes are likely (extensibility win compounds)

### Skip when:
- Single mode (no choice = no registry)
- Hot-path single-mode (indirect call cost > register-allocate cost; inline the fn)
- Modes have widely different signatures (uniform dispatch fails — use std::variant or split into separate registries by signature)
- Modes' enum values are sparse (fn-ptr array would have holes — use switch dispatch instead)
- Mode count is small + closed (≤2 modes; one if-else is more readable)

### Cost:
- ~100-150 LOC for registry + dispatch table + ToString/FromString + bounds-checked dispatch wrapper
- ~30-50 LOC per compute fn (varies with curve complexity)
- ~1-2ns slow-path indirect call dispatch overhead per evaluation
- New mode addition: 1 registry row + 1 compute fn = ~30 min including tests

### Win:
- Adding a new mode = 1 row + 1 free function (no enum / switch / ToString / FromString / cfg.example / tests touch)
- Cfg parser auto-handles new mode via FromString
- Tests can enumerate via `for (int c = 0; c < FOREACH_DEGRADATION_CURVE_COUNT; ++c)` (test-by-construction extensibility)
- GUI dropdown auto-populates from ToString walk (canonical name comes from registry)
- Documentation co-located with data (doc column embedded in registry tuple)

---

## Reference implementations

### First applied: FoxML_Trader_v2 v5.14.9.A

- Registry: `ML_Headers/ConfidenceScore.hpp:498-634` (FOREACH_DEGRADATION_CURVE)
- 4 curves shipped: OFF / LINEAR / EXP / STEP
- 8 tests in `tests/controller_test.cpp` (per-curve correctness + dispatch table + ToString/FromString round-trip)
- Cfg field: `risk_degradation_curve` (stamp-bound via FOREACH_STAMP_BOUND_CFG)

### Adjacent patterns / future application candidates

- **Label functions** (`LabelFunctions.hpp`): forward_return / barrier_hit / triple_barrier — currently a switch dispatch. Migration candidate when 4th label fn lands.
- **Threshold curves** (composite confidence → entry threshold scaling): currently a single linear damping; if multi-mode threshold curves emerge, this is the pattern.
- **Fee schedules** (maker/taker bifurcation extended to multiple tier shapes): pattern fits if 3+ schedules ever needed.
- **Decay schedules** (model freshness decay, IC drift decay): currently single exp; pattern fits if alternative decays needed.

---

## Lessons / gotchas

### Enum values must be dense for fn-ptr array indexing

If `FOREACH_DEGRADATION_CURVE` has `X(NEW, 5, ...)` with gaps from `X(STEP, 3, ...)`, the fn-ptr array at index 4 is whatever follows STEP in declaration order — likely WRONG (calls the wrong fn) or sentinel-zeroed (crashes on indirect call).

**Mitigation:** enum values must be sequential 0..N-1 in registry order. Static_assert at compile time:

```cpp
static_assert(CURVE_OFF == 0 && CURVE_LINEAR == 1 && CURVE_EXP == 2 && CURVE_STEP == 3,
              "Curve enum values must be dense 0..N-1 for fn-ptr dispatch");
```

If sparse values are needed (rare; backwards-compat with serialized stamps), use a switch dispatch instead.

### Switch fallback for sparse enum values

```cpp
static inline double Confidence_DegradationScale_SwitchDispatch(int curve, double conf, ...) {
    switch (curve) {
        #define X_GEN_SWITCH(name, val, fn, doc) case val: return fn(conf, full, min, min_pct);
        FOREACH_DEGRADATION_CURVE(X_GEN_SWITCH)
        #undef X_GEN_SWITCH
        default: return 1.0;
    }
}
```

Switch dispatch handles sparse enum values; compiler optimizes to a jump table when values are dense (effectively the same as fn-ptr) and to a branch chain when sparse.

Pick fn-ptr when enum values are dense + count is large (jump table wins); pick switch when sparse OR count is small (≤4; branch chain is fast).

### Stamp binding for the curve choice

The curve enum value is operator config → must be stamp-bound to detect train/serve drift (operator can't change `risk_degradation_curve=LINEAR` between train and serve without invalidating the model). Pattern:

- Add the cfg field to FOREACH_STAMP_BOUND_CFG
- Stamp binding stores the integer value; verify at load time
- Drift check compares serve-time cfg value against stamp-bound train-time value

See v5.14.9.C for the ladder field stamp-binding precedent.

### Compute fn placement: same header or separate?

For 4-curve registry with ~30 LOC per fn, same header (under the registry) is fine — readers see registry + compute fns together. For 10+ modes or 100+ LOC per fn, separate file (`ML_Headers/<DomainName>ComputeFns.hpp`) — header doesn't bloat.

### Forward declaration ordering

Forward-declare the compute fns BEFORE the registry + dispatch table; define the fns AFTER. Allows the dispatch table to reference fn names that aren't fully defined yet. Same pattern as cyclic struct declarations.

### Don't bloat the dispatch contract

The signature is shared by ALL compute fns. If one curve needs an extra input, DON'T add it to the signature for all — extract per-curve helpers OR pass via a config struct + access via `cfg->extra_param`. Adding an arg to the dispatch contract breaks every existing curve fn.

### "Default" mode is OFF (sentinel)

Reserve `OFF` (enum value 0) as the "feature disabled" sentinel that's safe at boot before any cfg loads. Compute fn returns the identity factor (1.0 for scale; pass-through for filters). Defaults preserve pre-feature behavior bytewise.

---

## Audit detection

`/dod-audit` detects missed applications by:

- Symptom: switch statement with ≥3 cases dispatching to similarly-named free functions (`linear_X`, `exp_X`, `step_X`)
- Symptom: enum with `_OFF`/`_LINEAR`/`_EXP`/`_STEP`-style naming + parallel string table
- Symptom: parser if-else chain with 3+ `strcasecmp(s, "MODE_NAME") == 0` checks alongside an enum

When detected → flag as `MISSED — curve-registry-pattern`. Recommended fix: 1-row registry + fn-ptr dispatch.

---

## Patterns NOT used here (and why)

### virtual function polymorphism

Vtable indirection + heap allocation of mode objects + RAII. CLAUDE.local.md STRATEGY_AND_CODING_RULES.md forbids virtual in hot/slow path.

### std::variant + std::visit

C++-class-flavored. Same perf as switch under the hood; adds STL dependency; obscures dispatch shape.

### Tag dispatch via templates

```cpp
template <int Curve> double scale(...);
```

Each call site requires compile-time-known curve choice; operator can't pick at runtime. Wrong fit for cfg-driven mode selection.

### Function objects (functors)

C++-class-flavored. Same drawbacks as virtual; no win over fn-ptr.

---

## Cross-references

- `x-macro-registry-with-presence-dispatch.md` — base X-macro pattern this builds on
- `slow-path-gate-registry-pattern.md` — sister slow-path registry (boolean dispatch vs named-mode dispatch)
- `bitmap-flag-api.md` — cousin pattern for boolean bitmap fields (no compute-fn dispatch)
- `registry-tuple-as-single-source-of-truth.md` — meta-pattern (registry tuple feeds N consumers)
- FoxML_Trader_v2 `CLAUDE.md` item 13 — X-macro for multi-site additions
- FoxML_Trader_v2 `CLAUDE.md` item 17 — latency-additions tracked (slow-path indirect call ~1-2ns documented)
- FoxML_Trader_v2 `ML_Headers/ConfidenceScore.hpp:498-634` — canonical reference implementation
