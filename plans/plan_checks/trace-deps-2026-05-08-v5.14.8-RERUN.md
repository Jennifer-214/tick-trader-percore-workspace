# /trace-deps RERUN — v5.14.8 stamp lineage + stale gating — 2026-05-08

**Verdict:** **GREEN on plan clarity; CODE NOT YET WRITTEN (expected)**

## Audit context

This rerun is a PRE-CODING audit. The first round (verdict RED)
flagged 2 BLOCKING + 3 YELLOW gaps. All 5 plan-clarity gaps are
now closed.

Agent rendered verdict as RED again because it found the new
fields/logic NOT in the codebase — but that's expected pre-coding.
Plan correctly enumerates all of these as NEW additions.

## Gap-fix verification (5 of 5 closed)

1. **ModelHandle field access** — Plan now uses FLAT-FIELD pattern:
   `m->training_timestamp_us` + `m->run_name[64]` listed as NEW
   ModelHandle fields. No nested `.stamp` sub-struct. Plan correct.

2. **Health_LogCriticalRateLimited signature** — PASS verified by
   agent at `MemHeaders/HealthLog.hpp:319-323`. Plan now uses
   canonical 5-arg signature with static `last_*_log_us = 0`
   per-call-site state. Plan correct.

3. **feature_last_update_us[] storage** — Plan now defines as
   `FeatureComputeCtx const uint64_t*` field (nullptr-safe;
   plumbed from per-feature compute fn captures). Plan correct.

4. **stale_feature_events_total counter** — Plan now defines as
   `FeatureComputeCtx uint32_t*` (mirrors v5.9.0b
   `nan_feature_events_total` pattern). Plan correct.

5. **FOREACH_FEATURE row signature** — Plan now shows explicit
   change `X(id, name, version, enabled, fn, note)` →
   `X(id, name, version, enabled, fn, note, max_staleness_minutes)`.
   Hash-compute X-macro at `FeatureRegistry.hpp:385-398` ignores
   7th column → hash STABLE → no operator retrain. Plan correct.

## REUSE verification (PASS)

Agent verified at re-audit time:
- `Health_LogCriticalRateLimited` signature: PASS at HealthLog.hpp:319
- Surface G `has_*` flag pattern: PASS (multiple existing examples)
- `FeatureComputeCtx` struct extension target: PASS at FeatureRegistry.hpp:67-77
- `Features_PackAll` choke point: PASS at FeatureRegistry.hpp:449
- `EnsembleModelZoo_LoadFromCfg` extension target: PASS at CoreModelZoo.hpp:1248
- FEATURE_REGISTRY_HASH compute fn: PASS at FeatureRegistry.hpp:385-398
- `clock_gettime` infrastructure: PASS

## NEW additions (correctly enumerated; not yet coded — that's the point)

| Item | Type |
|---|---|
| `ModelHandle.training_timestamp_us` + `run_name[64]` | NEW flat fields |
| `CoreModelZoo_CheckStaleModel` fn | NEW |
| `cfg.model_max_age_hours` | NEW cfg |
| FOREACH_FEATURE 7th column (`max_staleness_minutes`) | NEW row sig |
| `FeatureComputeCtx.feature_last_update_us` | NEW field |
| `FeatureComputeCtx.stale_feature_events_total` | NEW counter |
| Features_PackAll stale-check loop | NEW logic |
| 7 stamp body Surface G fields (scaler hash + removal_reasons + 5 env meta) | NEW |

## Sprint readiness verdict

**Plan is ready to code.** All 5 first-round gaps closed. Sprint
unblocked.

## Skill-spec note

`/trace-deps` skill needs explicit PRE-CODING vs POST-CODING mode
distinction. Current default ("is the code there?") is wrong
question pre-coding. Will fix as part of v5.14.6 skill cleanup ship.
