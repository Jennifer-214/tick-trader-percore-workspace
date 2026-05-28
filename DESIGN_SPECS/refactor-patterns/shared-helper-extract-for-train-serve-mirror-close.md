---
name: shared-helper-extract-for-train-serve-mirror-close
type: refactor-pattern
stage: 2-draft
version: 0.1
established: 2026-05-24
first_canonical_target: v5.15.5.F.4d.1.B.4 ship close (EngineCommon_BootPerCore + EngineCommon_SlowPathCycleOneCore)
description: Pattern for closing Class 18 train-serve mirror clusters by extracting shared helpers callable from both EngineSharded + BacktestSharded
tags: [structural-fix, framework-discipline]
surface: [boot-time, slow-path, backtest]
sister_specs:
  - train-serve-execution-layer-parity.md (the M5 audit discipline that surfaces the candidates)
  - structural-fix-preferred-decision-framework.md
  - canonical-sister-extension-discipline.md
  - autopopulate-pattern-for-production-caller-class.md
  - cfg-derived-consumer-framework.md (sister at cfg/stamp layer; this pattern is the execution-layer analog)
applies_at_skills:
  - /precoding-audit-gate (post-cluster-finding architect decision)
  - /merge-scan (catches the shared-helper opportunity at slow-path/boot surface)
---

# Shared helper extract for train-serve mirror close

**Stage 2 DRAFT v0.1.** First canonical landing at `v5.15.5.F.4d.1.B.4` ship close — `EngineCommon_BootPerCore` + `EngineCommon_SlowPathCycleOneCore` shared helpers in NEW `CoreFrameworks/EngineCommon.hpp`.

## Problem this pattern addresses

`BacktestSharded.hpp` has 15+ explicit `"Mirrors EngineSharded_Run lines X-Y"` comment citations (verified 2026-05-24 at lines 141/152/162/167/233/269/350/404/430/447/470/664/761/811/872). Class 18 mirror, explicit + comment-acknowledged.

The mirror discipline relies on the comment + per-patch contributor vigilance. Drift accumulates per-patch — PARITY-026 + PARITY-027 + PARITY-028 + PARITY-029 + PARITY-030 + PARITY-031 are direct evidence drift HAS happened (4 CRITs + 3 HIGHs surviving for 1-14 months silent).

The cohort-finding shape (3+ sister mirrors at adjacent boot OR slow-path-cycle surface area) is the [[structural-fix-preferred-decision-framework]] Option D ARCHITECT trigger.

## Pattern: shared helper extract

### Helper signature shape

Extract shared helpers in NEW `CoreFrameworks/EngineCommon.hpp`:

```cpp
// CoreFrameworks/EngineCommon.hpp
namespace tt {

// Per-core boot work shared between EngineSharded_Run + BacktestSharded_Run.
// Handles: ConfigureKillSwitch + BindCompositeCfg + RollingTurnover_Init +
//          Strategy_InitPerCore + BNB fee discount per-core + bandit prior + ...
//
// Per-call-site differences handled via cfg flags + nullable state arguments:
//   - oms == nullptr → skip kill-switch configure (some backtest variants don't init OMS)
//   - state->ws_staleness_ctx == nullptr → skip WS staleness wiring (backtest)
//   - cfg.engine_arch enum → branch between centralized vs per_core_slow init
//
// CRITICAL: NEVER call from hot path. Boot-only. Branches OK at boot time.
template <unsigned F>
void EngineCommon_BootPerCore(
    const ControllerConfig<F>& cfg,
    int                        core_idx,
    EventLoopState<F>*         state,
    OrderManagerState<F>*      oms);  // nullable for OMS-less backtest variants

// Per-core slow-path-cycle body shared between EngineSharded_Run +
// ShardedBacktest_RunTick. Handles: UpdateRollingState + RebuildOneCore +
// TimeExitOneCore + TrailingSLRatchetOneCore + exit-prediction submit +
// per-core regime collection + ...
//
// Per-call-site differences handled via cfg flags + nullable args:
//   - feature_collector == nullptr → skip backtest feature collection
//   - ts_us == 0 → use cfg.epoch_synthetic (backtest replay mode)
//   - oms == nullptr → skip OMS_PushExitForSlot (backtest variant without OMS)
//
// CRITICAL: NEVER call from hot path. Slow-path only. p99 ≤100µs per H8.
template <unsigned F>
void EngineCommon_SlowPathCycleOneCore(
    const ControllerConfig<F>& cfg,
    int                        core_idx,
    EventLoopState<F>*         state,
    OrderManagerState<F>*      oms,            // nullable
    FPN<F>                     price,
    uint64_t                   ts_us,
    BacktestFeatureCollector*  feature_collector);  // nullable

}  // namespace tt
```

### Caller migration shape

`EngineSharded_Run` boot block (~line 670-1160) becomes:

```cpp
for (int c = 0; c < num_cores; c++) {
    tt::EngineCommon_BootPerCore(cfg, c, &state, &oms);
}
```

`BacktestSharded_Run` boot block (~line 180-420) becomes:

```cpp
for (int c = 0; c < num_cores; c++) {
    tt::EngineCommon_BootPerCore(cfg, c, &state, &oms);
    // backtest-specific extras (synthetic data wrapper init, etc.) AFTER
}
```

`EngineSharded_Run` slow-path body (~line 3036-3320 per-node-slow lambda) becomes:

```cpp
tt::EngineCommon_SlowPathCycleOneCore(cfg, c, &state, &oms, price, ts_us, nullptr);
```

`ShardedBacktest_RunTick` slow-path block (~line 336+) becomes:

```cpp
for (int c = 0; c < num_cores; c++) {
    tt::EngineCommon_SlowPathCycleOneCore(cfg, c, &state, &oms, price, ts_us, &feature_collector);
}
```

### Per-call-site exemption handling

NOT every difference between live + backtest is a parity break (per [[train-serve-execution-layer-parity]] § False-positive surface). Legitimate exemptions handled via:

1. **Nullable arguments** for genuinely-absent state on one side (oms / feature_collector / WS staleness ctx)
2. **cfg flags** for runtime-mode branching (engine_arch enum; replay vs realtime)
3. **Conditional compile** if a difference is build-flag-driven (e.g., `LATENCY_PROFILING`)
4. **External wrapper** for operator-explicit overrides that don't fit the shared shape (e.g., `bandit_state_prior_path` operator override per PARITY-031/TECH_DEBT-121 — call the override AFTER `EngineCommon_BootPerCore` returns)

## When to apply (categorical trigger)

Per [[feedback_proportionate_response_to_audit_findings]] Option D ARCHITECT:

- Audit surfaces 3+ sister Class 18 mirrors at adjacent boot OR slow-path-cycle surface area
- Cohort math justifies: N findings × cost-per-individual-patch > 1 × cost-of-shared-helper-extract
- Boundary-stable: helper signature IS the boundary; existing call sites delegate without cascading
- Both sides have legitimate need for the same work (NOT one-side-only feature; that's a different shape — [[autopopulate-pattern-for-production-caller-class]] for cfg/stamp; this pattern for boot/slow-path)

## When NOT to apply

- One-time mirror at small surface (<3 sister findings) → individual patch + comment is appropriate; ARCHITECT is overkill
- Helper signature would require >3-4 nullable args or cfg flags → boundary not stable; refactor first OR accept individual patches
- One side has genuinely different semantic (e.g., backtest replay vs live realtime fill simulation) → wrap with thin facade, don't force into shared shape

## Sister patterns

- [[autopopulate-pattern-for-production-caller-class]] — same N-site → 1-site closure shape, but at cfg/stamp emit layer (companion-macro level instead of function-extract level)
- [[cfg-derived-consumer-framework]] — same intent at cfg/stamp layer; this pattern is the execution-layer analog
- [[canonical-sister-extension-discipline]] — companion discipline; before extracting, verify sister patterns considered; after extraction, the helper IS the canonical sister for future train-serve work

## Anti-patterns this avoids

- **Class 18 mirror with `// Mirrors X lines Y-Z` comment** — comment-pinned discipline that drifts per-patch (today's `BacktestSharded.hpp` has 15+ such citations; drift evidence at PARITY-026/027/028/029/030/031)
- **Per-patch contributor vigilance as discipline** — fails when contributor doesn't notice the sister site
- **Parallel function bodies with same logic + different surrounding context** — the helper-extract eliminates the parallel by making both call sites delegate

## First canonical (forward-looking; lands at .B.4)

`v5.15.5.F.4d.1.B.4` ship will:
1. Extract `EngineCommon_BootPerCore` + `EngineCommon_SlowPathCycleOneCore` per signatures above
2. Migrate EngineSharded_Run + BacktestSharded_Run + ShardedBacktest_RunTick to call shared helpers
3. Close PARITY-026 + PARITY-027 + PARITY-028 + PARITY-029 + PARITY-030 + PARITY-031 in same commit (verifies by construction)
4. Add unit tests asserting helper signature stability + per-call-site exemption validity
5. Apply M5 [[train-serve-execution-layer-parity]] discipline as first canonical reference

After `.B.4` ship, this pattern goes Stage 3 (first canonical landed). Goes to Stage 4 (cohort) after 2+ applications (likely at GUI panel parallelism sweep + OMS sweep — Layer 1 + Layer 2 of the 6-layer cadence).

## Cross-references

- `train-serve-execution-layer-parity.md` (M5 audit discipline that surfaces application candidates)
- `structural-fix-preferred-decision-framework.md` (Option D ARCHITECT trigger framework)
- `canonical-sister-extension-discipline.md` (companion sister-registry inspection)
- `autopopulate-pattern-for-production-caller-class.md` (sister at cfg/stamp companion-macro layer)
- `cfg-derived-consumer-framework.md` (sister at cfg/stamp layer; this is execution-layer analog)
- `pattern-codification-lifecycle.md` (Stage 2 → Stage 3 progression at first canonical)
- TECH_DEBT-119 (the queued application at `.B.4`)
- PARITY-026 / 027 / 028 / 029 / 030 / 031 (first canonical findings this pattern closes)
- `plans/v5.15-live-readiness/plan_checks/2026-05-24-train-serve-asymmetry-sweep.md` (audit that surfaced the cohort)
