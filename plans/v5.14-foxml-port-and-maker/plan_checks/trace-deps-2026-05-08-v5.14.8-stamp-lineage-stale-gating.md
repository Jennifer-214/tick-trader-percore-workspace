# /trace-deps report — v5.14.8-stamp-lineage-stale-gating — 2026-05-08

**Verdict:** **RED** (2 BLOCKING gaps, 3 YELLOW; plan needs update)

## Summary
- NEW functions analyzed: 1 main (`CoreModelZoo_CheckStaleModel`) + 4 stamp body extensions
- Callees verified: 4
- PASS: 3
- GAP: 0
- DRIFT: 1 (Health_LogCriticalRateLimited signature)

## Gaps (BLOCKING — RED)

### 1. `ModelHandle.stamp` sub-struct does not exist

Plan assumes `m->stamp.training_timestamp_us` + `m->stamp.run_name`
syntax. Actual `ModelHandle` (ML_Headers/ModelInference.hpp:237)
has FLAT fields:
- `training_poll_interval`
- `has_training_poll_interval`
- `scaler_sha256`
- `has_stamp_scaler_sha256`
- etc.

NO nested `.stamp` sub-struct exists. Plan code wouldn't compile.

**Fix options:**
- Option A: Add nested struct field `ModelStampData stamp` to
  ModelHandle; populate at load time from individual flat fields.
- Option B: Refactor plan code to access flat fields directly:
  `m->training_timestamp_us` (need to verify this field exists on
  ModelHandle; if not, need to ADD it as flat field).

**Recommendation:** Option B — flat fields are the established
pattern; adding nested struct would require migrating all existing
flat-field consumers.

**Required check at code time:** does `ModelHandle.training_timestamp_us`
exist? If not, plan must list this as NEW field on ModelHandle.

### 2. `Health_LogCriticalRateLimited` signature mismatch

Plan call (line 78-80):
```cpp
Health_LogCriticalRateLimited(
    "[stale_model] %s is %lluh old > max %lluh",
    m->stamp.run_name, age_hours, max_age_hours);
```

Actual signature at MemHeaders/HealthLog.hpp:319:
```cpp
Health_LogCriticalRateLimited(
    uint64_t* last_emit_us, uint64_t gate_us, int core_id,
    const char* category, const char* fmt, ...);
```

Plan passed 3 args; actual requires 5 mandatory + variadic. Plan
code wouldn't compile.

**Fix:** Update plan call site to:
```cpp
static uint64_t last_stale_model_log_us = 0;
Health_LogCriticalRateLimited(
    &last_stale_model_log_us, /*gate_us=*/60000000ULL,
    /*core_id=*/-1,  // global; not per-core
    "stale_model",
    "%s is %lluh old > max %lluh",
    run_name, age_hours, max_age_hours);
```

## Yellow (clarifications needed)

### 3. `feature_last_update_us[]` array undefined

Plan Step 2 assumes this state exists. Not in `FeatureComputeCtx`
(FeatureRegistry.hpp:67-77 has only `signals` + `short_rolling`).

**Fix:** Add to FeatureComputeCtx OR pass as separate param OR
plumb from RegimeSignals (if per-feature timestamps available).
Recommend: add to FeatureComputeCtx as `const uint64_t*
feature_last_update_us` (nullptr-safe for legacy callers).

### 4. `stale_feature_events_total` counter undefined

Plan increments this counter. Not in FeatureComputeCtx or visible
caller path.

**Fix:** Add `uint32_t* stale_feature_events_total` field to
FeatureComputeCtx (mirrors v5.9.0b's `nan_feature_events_total`
+ `nan_prediction_events_total` pattern).

### 5. FOREACH_FEATURE macro signature change not shown

Plan describes intention ("extend with `max_staleness_minutes`
column; exclude from hash") but doesn't show:
- Exact new row signature: `X(id, name, version, enabled, fn,
  note, max_staleness_minutes)`
- Verify hash compute fn at FeatureRegistry.hpp:385-398 only loops
  over name+version+enabled (correct — line 388-393); plan's
  recommendation to exclude max_staleness from hash holds IF the
  X-macro caller in hash compute uses fewer params than the row
  definition.

**Fix:** Show updated FOREACH_FEATURE row signature explicitly +
confirm hash compute X-macro pattern matches `X(id, name, version,
enabled, ...)` (ignoring extra cols).

## REUSE Verification

| Claim | Location | Status |
|---|---|---|
| Surface G `has_*` flag pattern | Multiple existing examples | PASS (`has_feature_mask`, `has_engine_version`, etc.) |
| Stamp body emit + verify pipeline | tools/stamp_model.sh + tools/verify_model_stamp.cpp | PASS |
| `Features_PackAll` choke point | FeatureRegistry.hpp:449 | PASS |
| `EnsembleModelZoo_LoadFromCfg` | CoreModelZoo.hpp:1248 | PASS |
| `clock_gettime` infra | Used at Portfolio.hpp:228 | PASS |
| FEATURE_REGISTRY_HASH compute fn | FeatureRegistry.hpp:385-398 | PASS (will not flip if plan's macro change excludes max_staleness column) |

## Recommendations

**BLOCKING fixes (must update plan):**
1. Resolve ModelHandle.stamp access pattern (flat vs nested struct)
2. Update Health_LogCriticalRateLimited call signatures throughout

**YELLOW fixes (helpful before coding):**
3. Define feature_last_update_us[] storage location
4. Define stale_feature_events_total storage location
5. Show explicit FOREACH_FEATURE macro signature change

**Then re-run /trace-deps to confirm GREEN.**

## Note

This is the SECOND test of the new `/trace-deps` skill on a real
plan. It successfully caught:
- A signature drift (Health_LogCriticalRateLimited)
- A stale mental-model assumption (`.stamp` sub-struct doesn't
  exist on ModelHandle)
- 3 undefined-state-references that would break compile

**Skill is doing what it was designed to do.** Both blocking gaps
would have caused compile failures and required mid-coding plan
revision. Catching them at plan-time saves the wasted code-write
effort.
