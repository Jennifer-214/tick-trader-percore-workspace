# Stamp-vs-runtime drift detection registry pattern

**Established:** 2026-05-09 (FOREACH_ARCH_FIELD_DRIFT at v5.15.1; PROMOTED to DESIGN_SPEC 2026-05-12 at v5.15.5.A.7 with 2nd application)
**Status:** ACTIVE v1.0 (2 production applications: narrow ArchFieldDrift + wide CfgDriftCheck)
**Cross-references:**
- Companion: `x-macro-registry-with-presence-dispatch.md` (Y3 dispatch underlying mechanism)
- Companion: `dual-axis-y3-dispatch-pattern.md` (used by wide variant for severity × category × compare_kind dispatch)
- Companion: `bitmap-flag-api.md` (drift bits via BITMAP_SET on drift_flags_at_load)
- Companion: `structural-fix-preferred-decision-framework.md` (motivation: extinguish Class 18 mirror at drift-detection surface)
- First narrow application: `MemHeaders/ArchFieldDriftRegistry.hpp` (FOREACH_ARCH_FIELD_DRIFT; 4 entries; v5.15.1)
- First wide application: `ML_Headers/CfgDriftCheckRegistry.hpp` (FOREACH_CFG_DRIFT_CHECK; 19 entries; v5.15.5.A.7)
- Consumer chokepoints: `CoreModelZoo_TryLoadRole` (arch) + `CoreModelZoo_ValidateAgainstCfg` (cfg)

---

## Problem statement

A model stamp records training-time values for fields that affect inference math (cfg parameters, architectural hashes, scaler binding). At serving time, those stamp-recorded values must be COMPARED against current runtime values to detect drift. Drift = train-serve parity violation = potentially silent prediction miscalibration.

Manual drift checks recur as N-site bug class:
- Each new check = new if-block at the chokepoint function body
- Format strings drift across blocks ("%g" vs "%.6g" vs "%.17g")
- Severity classification (REFUSE-in-strict vs WARN-always) drifts as new fields are added
- Acknowledgment flag wiring drifts (which `acknowledge_*_drift` cfg flag applies?)
- Per-field telemetry (failure_flags bits) inconsistently set

Pre-pattern: 15 manual if-blocks at `CoreFrameworks/ModelValidation.hpp:94-239` (v5.15.4). Adding the 16th requires touching the function, picking the right tier, choosing the right ack flag, writing a consistent log format. Every addition risks drift from the established pattern.

This pattern provides **registry-driven drift detection** — one row per check; walker generates the dispatch at the chokepoint.

---

## Two variants

### Narrow variant (FOREACH_ARCH_FIELD_DRIFT — 4-col tuple, BIT_FLAG-only, no ack)

For drift checks on **architectural fields** (registry hashes, build flags) where:
- Severity is uniform (BIT_FLAG set on `drift_flags_at_load`; downstream consumer decides REFUSE/WARN)
- No operator-acknowledgment escape (architectural drift = always observable; never suppressed)
- Per-entry fail_mask required (each entry maps 1:1 to a FOREACH_FAILURE_MODE BIT_FLAG)

```cpp
// 4-col tuple: X(name, stamp_field_expr, runtime_value_expr, fail_mask)
#define FOREACH_ARCH_FIELD_DRIFT(X) \
    X(feature_hash,        sr.feature_registry_hash,        FEATURE_REGISTRY_HASH(), \
                           FAILURE_MASK_feature_hash_drift) \
    X(label_hash,          sr.label_registry_hash,          LABEL_REGISTRY_HASH(),   \
                           FAILURE_MASK_label_hash_drift)   \
    X(build_flags_hash,    sr.build_flags_hash,             tt::BUILD_FLAGS_HASH(),  \
                           FAILURE_MASK_build_flags_drift)  \
    X(scaler_binding,      sr.feature_registry_hash,        handle->scaler.registry_hash, \
                           FAILURE_MASK_scaler_drift)
```

Walker (at `CoreModelZoo.hpp:537` post-`verify_model_stamp` chokepoint):
```cpp
#define X(name, stamp_field, runtime_value, fail_mask) \
    if ((stamp_field) != (runtime_value)) {            \
        BITMAP_SET(handle->drift_flags_at_load, fail_mask); \
    }
FOREACH_ARCH_FIELD_DRIFT(X)
#undef X
```

### Wide variant (FOREACH_CFG_DRIFT_CHECK — 10-col tuple, multi-axis Y3, ack-aware)

For drift checks on **stamp-bound cfg fields** (operator-settable values that affect serving math) where:
- Severity varies per entry (Tier 1 REFUSE-in-strict vs Tier 2 WARN-always)
- Operator acknowledgment escape applies (per-category ack cfg flag)
- Comparison shape varies (exact `!=` for ints, `fabs > eps` for doubles, `strcmp` for strings)
- Multiple ack categories (inference_cfg vs cross_binary)

```cpp
// 10-col tuple — dual-axis Y3 dispatch (severity × category × compare_kind):
// X(NAME, type, severity, category, compare_kind,
//   get_stamp_expr, get_cfg_expr, gate_when, fail_mask, doc)
#define FOREACH_CFG_DRIFT_CHECK(X) \
    /* Inference-cfg Tier 1 (REFUSE in strict): */ \
    X(confidence_threshold_scale, double, REFUSE_STRICT, INFERENCE_CFG, EPS_DEFAULT, \
      h->inference_cfg_confidence_threshold_scale, FPN_ToDouble(cfg.confidence_threshold_scale), \
      STAMP_HAS(*h, inference_cfg), FAILURE_MASK_cfg_inference_drift, \
      "Tier 1 confidence threshold scale drift") \
    /* Cross-binary WARN: */ \
    X(xgb_subsample, double, WARN_ALWAYS, CROSS_BINARY, EPS_DEFAULT, \
      h->xgb_subsample, FPN_ToDouble(cfg.xgb_subsample), \
      STAMP_HAS(*h, xgb_hyperparams), FAILURE_MASK_cfg_cross_binary_drift, \
      "XGBoost subsample drift (cross-binary)") \
    /* ...15+ entries total */
```

Walker uses `dual-axis-y3-dispatch-pattern.md`-style per-axis dispatchers.

---

## When narrow vs wide

| Concern | Narrow (4-col) | Wide (10-col w/ Y3) |
|---|---|---|
| Severity uniform? | Yes — all set BIT_FLAG | No — Tier 1 vs Tier 2 differ |
| Operator ack escape? | No (architectural truth) | Yes (per-category cfg flag) |
| Comparison shape uniform? | Yes (uint64 hash compare) | No (int/double/string/uint) |
| Per-entry fail_mask? | Yes (1:1 with FailureMode bits) | No (per-category share bits) |
| Tuple width | 4 cols | 10 cols |
| Walker complexity | 1-line if-set | Multi-axis dispatcher composition |

Use narrow when checks are homogeneous + observability-only (no behavior gate).
Use wide when checks vary across multiple dimensions + drive behavior (REFUSE/WARN).

---

## The pattern (concrete shape)

### Step 1: Inventory drift-check sites

Walk the chokepoint function (e.g., `CoreModelZoo_ValidateAgainstCfg`) and enumerate every if-block that compares stamp value to runtime/cfg value:

| Site | Stamp field | Runtime/cfg | Compare | Severity | Ack flag | Fail bit |
|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... |

Identify dimensions of variation. If only 1-2 dimensions vary → narrow variant. If 3+ → wide variant with `dual-axis-y3-dispatch-pattern.md` Y3 dispatch.

### Step 2: Define the registry header

`MemHeaders/<Name>DriftRegistry.hpp` (or `ML_Headers/` if ML-domain):
```cpp
#ifndef <NAME>_DRIFT_REGISTRY_HPP
#define <NAME>_DRIFT_REGISTRY_HPP

#include "BitmapMacros.hpp"
#include "FailureModeRegistry.hpp"  // for FAILURE_MASK_* constants

// Tuple shape comment block
// Per-axis HANDLE macros (wide variant only)
#define FOREACH_<NAME>_DRIFT_CHECK(X) \
    X(entry1, ...) \
    X(entry2, ...) \
    ...

// Test instrumentation: FOREACH_..._COUNT
#endif
```

### Step 3: Add per-entry FAILURE_MODE BIT_FLAGs as needed

Each unique fail_mask token in the registry must correspond to an entry in `FOREACH_FAILURE_MODE` (with `BIT_FLAG` storage class). Budget: uint16_t failure_flags supports 16 bits total.

- Narrow variant: per-entry BIT_FLAG (4 entries = 4 bits)
- Wide variant: per-category BIT_FLAG (e.g., cfg_inference_drift + cfg_cross_binary_drift = 2 bits for 19+ entries)

### Step 4: Walker at the chokepoint

```cpp
// In CoreModelZoo_ValidateAgainstCfg (wide variant example):
#define X CFG_DRIFT_CHECK_ONE  // per-entry generator macro
FOREACH_CFG_DRIFT_CHECK(X)
#undef X
```

The walker macro is defined per-axis-composition. See `dual-axis-y3-dispatch-pattern.md` for the wide variant's composition shape.

### Step 5: Test instrumentation

```cpp
// In tests/controller_test_stamps.cpp:
check("registry-N-entries", FOREACH_<NAME>_DRIFT_CHECK_COUNT == N);

// Per-entry coverage test (one test per registry row):
check("entry-drift-fires-on-mismatch", ...);
```

---

## HMAC byte-preservation interaction

Drift detection registries READ stamp body fields. The stamp body itself is HMAC-signed via `FOREACH_STAMP_BOUND_<KIND>` registries (CFG, MODEL_CONST). Any new drift check on a NEW field requires the field to ALSO be added to the appropriate stamp registry — with the **append-at-END** discipline per `wire-format-byte-preservation-discipline.md`.

Two-step workflow for adding a stamp-bound cfg field with drift detection:
1. APPEND row to `FOREACH_STAMP_BOUND_CFG` at registry END (auto-flows through STAMP_CFG_AUTOPOPULATE)
2. ADD row to `FOREACH_CFG_DRIFT_CHECK` referencing the new stamp field (`h->inference_cfg_<name>`)

Adding to drift registry alone WITHOUT stamp-binding = drift can't detect (no stamp value to compare against).
Adding to stamp registry alone WITHOUT drift check = no drift detection at runtime.
Both are needed for the train-serve parity surface to be fully load-bearing.

---

## Trade-offs + when to apply

### Apply when:
- 3+ manual drift checks exist at a chokepoint
- Pattern of "stamp value vs runtime value compare + set failure bit + log + tier counter" repeats
- New checks have been added in 3+ recent sprints (recurrence signal per `structural-fix-preferred-decision-framework.md`)
- Wire-format byte preservation is load-bearing (HMAC chain)

### Skip when:
- Drift checks are < 3 manual sites; X-macro overhead exceeds direct-code clarity
- Each check has wildly different semantics (no shape repeats)
- Stamp body not HMAC-signed (Surface G discipline doesn't apply)

### Cost:
- Registry header: ~50-150 LOC depending on variant
- Walker integration: 5-15 LOC at chokepoint
- Per-axis HANDLE macros (wide variant): ~50-100 LOC for 3-axis dispatch
- Tests: 1-3 LOC per entry for coverage

### Win:
- Adding next drift check = 1 row in registry
- Class 18 mirror extinct at the drift-detection surface
- Per-entry severity / ack / compare semantics visible per row (audit-friendly)
- Future categories / severity tiers / comparison shapes scale linearly (1 macro per new value)

---

## Reference implementations

### v5.15.1 — `FOREACH_ARCH_FIELD_DRIFT` (narrow variant — first application)

- `MemHeaders/ArchFieldDriftRegistry.hpp` (99 LOC; 4 entries)
- Walker: `CoreModelZoo_TryLoadRole` chokepoint (post-`verify_model_stamp`)
- Bit-set on `ModelHandle.drift_flags_at_load uint16_t`
- Surfaces: GUI Model Health panel + boot-gate consumption
- Closes: scattered manual feature_hash / label_hash / build_flags drift checks pre-v5.15.1

### v5.15.5.A.7 — `FOREACH_CFG_DRIFT_CHECK` (wide variant — second application; PROMOTED this DESIGN_SPEC to ACTIVE)

- `ML_Headers/CfgDriftCheckRegistry.hpp` (~250 LOC; 19 entries)
- 3-axis Y3 dispatch (severity × category × compare_kind) per `dual-axis-y3-dispatch-pattern.md`
- Walker: `CoreFrameworks/ModelValidation.hpp` `CoreModelZoo_ValidateAgainstCfg` (~120 LOC of manual blocks → registry-driven walker)
- Per-category bits in `drift_flags_at_load`: `cfg_inference_drift` + `cfg_cross_binary_drift`
- Ack flags migrated to `ops_cfg_flags` bitmap (cohort closure; TECH_DEBT-009 boolean orphan resolved)
- Log injection via `LogFn` template parameter (per `template-deferred-dependency-injection.md`)
- Closes: 15 manual drift checks across 2 subgroups (inference_cfg Tier 1/2 + cross-binary WARN)

### Future application candidates

- `FOREACH_SCALER_DRIFT_CHECK` — scaler binding integrity checks (currently 1 entry in ArchFieldDrift; could expand)
- `FOREACH_BUILD_DRIFT_CHECK` — extends cross-binary checks to git-sha / dependency-version drift
- `FOREACH_THREAD_DRIFT_CHECK` — per-core SCHED_FIFO / isolcpus consistency at boot

---

## Lessons / gotchas

### Stamp-binding must precede drift detection

Adding to drift registry without stamp-binding the field = no value to compare against (stamp-field reads `h->inference_cfg_<unknown>` which doesn't exist). Stamp-bind FIRST, drift-check SECOND.

### Per-category vs per-entry fail_mask

Wide variant CAN do per-entry fail_mask (each registry entry = 1 FailureMode BIT_FLAG). But this consumes uint16_t failure_flags slots fast. Per-CATEGORY (multiple entries share a bit) is the practical default. Per-entry granularity is a future option if `failure_flags` widens to uint32_t.

### Type-dispatched comparison via templated helper

For the wide variant's `compare_kind` axis, prefer a templated helper `tt::cfg_drift_compare<T>` over manual per-entry comparison code:
```cpp
namespace tt {
    template <typename T>
    inline bool cfg_drift_compare(const T& stamp_val, const T& cfg_val) {
        if constexpr (std::is_array_v<T>) return strncmp(stamp_val, cfg_val, std::extent_v<T>) != 0;
        else if constexpr (std::is_floating_point_v<T>) return fabs(stamp_val - cfg_val) > 1e-6;
        else return stamp_val != cfg_val;
    }
}
```
Mirrors `tt::stamp_parse_field<T>` (CLAUDE.md item 23). Each instantiation properly discards branches per T. The compare_kind Y3 axis can OVERRIDE this default for special-precision cases.

### Log injection unlocks testability

Wide variant chokepoint functions emit log lines for every drift. Without injection, tests must capture stderr via `freopen` or similar. With `template-deferred-dependency-injection.md` (LogFn template parameter defaulting to `tt::StderrLog`), tests pass a capturing lambda — log capture without I/O.

### Forward-compat via Surface G

Drift checks on STAMP-BOUND fields are AUTOMATICALLY forward-compat: legacy stamps (without the new field) have `has_<name>=0` → drift check skips silently per Surface G discipline. No `MODEL_FORMAT_VERSION` bump needed.

---

## Patterns NOT used here (and why)

### Function-pointer dispatch table

Considered: each drift check = function pointer in a `static const DriftCheck[]` table; walker iterates the table. Rejected — loses compile-time enforcement (forgotten field = null pointer); loses templated comparison dispatch.

### Per-check templated function specialization

Considered: each drift check = `tt::cfg_drift_check<FieldEnum>()` template specialization. Rejected — adds 1 specialization per field; less concise than X-macro registry rows; doesn't match codebase pattern.

---

## Cross-references

- `x-macro-registry-with-presence-dispatch.md` — Y3 dispatch underlying mechanism
- `dual-axis-y3-dispatch-pattern.md` — wide variant's multi-axis dispatch
- `bitmap-flag-api.md` — drift bits via BITMAP_SET on drift_flags_at_load
- `wire-format-byte-preservation-discipline.md` — append-at-END for new stamp-bound drift entries
- `structural-fix-preferred-decision-framework.md` — motivation (Class 18 mirror extinction)
- `template-deferred-dependency-injection.md` — log injection for testability
- `autopopulate-pattern-for-production-caller-class.md` — STAMP_CFG_AUTOPOPULATE auto-flows stamp-bound fields into handles
- FoxML_Trader_v2 `CLAUDE.md` item 13 — X-macro registry pattern
- FoxML_Trader_v2 `CLAUDE.md` item 15 — parity-tested-by-construction
- FoxML_Trader_v2 `CLAUDE.md` item 19 — structural fix preferred
- FoxML_Trader_v2 `MemHeaders/ArchFieldDriftRegistry.hpp` — narrow variant first application
- FoxML_Trader_v2 `ML_Headers/CfgDriftCheckRegistry.hpp` — wide variant first application
- FoxML_Trader_v2 `CoreFrameworks/ModelValidation.hpp` — wide variant walker

---

## Pattern lifecycle status (per pattern-codification-lifecycle.md)

- **Stage 1 (audit / problem identification):** ✅ v5.15.1 + v5.15.5.A.7 pre-coding consults
- **Stage 2 (DESIGN_SPEC draft):** ✅ This doc (ACTIVE v1.0 — 2026-05-12)
- **Stage 3 (first reference):** ✅ Narrow: `FOREACH_ARCH_FIELD_DRIFT` (v5.15.1); Wide: `FOREACH_CFG_DRIFT_CHECK` (v5.15.5.A.7)
- **Stage 4 (cohort migration):** ✅ Wide variant absorbs 15 manual drift checks at v5.15.5.A.7
- **Stage 5 (CLAUDE.md item):** Pending — promote to CLAUDE.md item once 3rd application surfaces (e.g., FOREACH_SCALER_DRIFT_CHECK or similar). 2 applications today; mature enough for ACTIVE status, not yet for CLAUDE.md codification.
- **Stage 6 (tooling enforcement):** `/parity-check` could audit "all stamp-bound fields have a corresponding drift check entry" — registry-completeness audit
- **Stage 7 (wider audit):** Sweep codebase for non-registry drift detection sites (e.g., scaler sidecar load checks; future model-quality checks)
