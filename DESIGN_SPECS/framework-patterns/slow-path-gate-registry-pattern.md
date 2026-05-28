---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-10
tags: [framework-discipline, structural-fix]
surface: [registry, slow-path, hot-path]
sister_specs: [x-macro-registry-with-presence-dispatch.md, autopopulate-pattern-for-production-caller-class.md, display-execution-invariant-registry-pattern.md]
applies_at_skills: []
---

# Slow-path gate registry pattern (FOREACH_SLOW_PATH_GATE + AUTOPOPULATE)

**Established:** 2026-05-10 (v5.14.9.B.0)
**Status:** ACTIVE
**Cross-references:**
- `bitmap-flag-api.md` — sister BIT_FLAG storage pattern
- `x-macro-registry-with-presence-dispatch.md` — base X-macro pattern
- `autopopulate-pattern-for-production-caller-class.md` — companion AUTOPOPULATE pattern
- CLAUDE.md item 18 (slow-path latency reduction priority — sub-clauses (c) + (d))
- CLAUDE.md item 13 (X-macro for multi-site additions)
- TECH_DEBT-017 (inventory + future-migration tracking)

---

## Problem statement

The codebase accumulates cfg-toggleable gates that gate slow-path behavior:

```cpp
if (cfg->lazy_rebuild_enabled) { /* skip rebuild body */ }
if (cfg->confidence_enabled && conf_scorer) { /* damp threshold */ }
if (cfg->confidence_composite_enabled) { /* swap composite formula */ }
if (cfg->ridge_within_horizon && ezoo->barrier_count >= 2) { /* Ridge dispatch */ }
if (cfg->exit_blender_mode && ezoo->exit_predictor_count >= 2) { /* Ridge exit */ }
if (cfg->ws_dead_time_flatten_enabled) { /* WS staleness flatten */ }
// + new in v5.14.9: ladder = (curve != OFF) && composite_enabled
```

**Recurring pain points:**

1. **Inline cfg-field reads scatter across deep functions.** Per item 18(d) — "avoid sprinkling cfg-flag checks through deep functions; hoist to slow-path top + pass a small struct of resolved predicates." Each gate's predicate is computed at every check site, even though cfg is stable across a slow-path cycle.

2. **Per-node override resolution is repeated.** Some gates (ladder, future) have per-node overrides (`core_N_*` cfg fields). Resolution logic `(override.X_set ? override.X : cfg.X)` is inline at each use site — N copies if N use sites read the same gate.

3. **No single source of truth for "what gates exist."** Adding a new gate touches: cfg field declaration, parser, default, engine.cfg.example, use site. /readiness Check 23 (latency accountability) can't auto-detect gate additions.

4. **Drift detection wiring is per-gate.** Some gates' cfg fields are stamp-bound (composite_enabled, ridge_*); some aren't (lazy_rebuild_enabled). No registry says which.

5. **/dod-audit can't surface gate-specific patterns.** A new gate that fits the slow-path pattern but uses ad-hoc caching is invisible to the auditor.

This is the same N-site bug class shape that `FOREACH_FAILURE_MODE` (v5.14.8.B) and `FOREACH_STAMP_BOUND_CFG` (v5.14.1.B.3) extinguished for their respective domains. Slow-path gates are the next domain.

## Design space explored

### Cache surface: where do gate predicates live?

**Option A: Inline cfg reads (current state).** Each use site re-reads the cfg field + computes predicate. Zero cache. ~1ns/read on cache-resident cfg.

**Option B: Per-gate atomic on ParameterSlot.** Hot-path-style; v5.12.1.B precedent (`param_staleness_gate_enabled`). Slow-path writes; hot-path reads. Right for hot-path gates; overkill for slow-path-only.

**Option C: Single struct of resolved predicates, per-engine global.** All cores share. Simple but doesn't handle per-node overrides (ladder needs per-node resolution).

**Option D: Per-node struct of resolved predicates.** Each core has its own cached gate state. Global gates have same value across cores; per-node gates have core-specific value. Memory cost: 16 cores × ~8 bools × 4 bytes (int) = 512 bytes total. Negligible.

**Decision: D.** Per-node struct on `CoreContext<F>` (per-node slow-path state). Per-node overrides handled naturally; global gates duplicate value (cheap). One cache surface; uniform access pattern.

### Recompute cadence

**Option A: Boot-only.** Compute once at boot; gates frozen. No runtime cfg-flip support.

**Option B: Per slow-path cycle.** Recompute at slow-path entry every cycle. Matches existing inline-read semantics (cfg-flip at runtime would re-evaluate). Cost: ~7 predicate evaluations × 16 cores per cycle = ~110 ALU ops at slow-path entry. Negligible at 100µs slow-path budget.

**Option C: On-cfg-change-event.** Wire cfg-hot-reload to invalidate cache. Complex; adds cfg-change observer surface.

**Decision: B.** Recompute every cycle preserves current semantics + supports runtime cfg edits (operator changes cfg file + sends SIGHUP-style reload — though this isn't currently wired, doing so later is cheap). Cost is rounding error.

### Hot-path gates

**Option A: Force migration of `param_staleness_gate_enabled` to the new registry.** Hot path reads from per-node slow_state cache → adds a load to hot path. **Bad.**

**Option B: Hot-path gates stay outside this registry.** They keep their existing ParameterSlot-atomic caching (set by slow-path rebuild + read by hot path via flags bitmap). FOREACH_SLOW_PATH_GATE is for slow-path-only gates.

**Decision: B.** Hot-path caching is its own pattern (atomic + seqlock). Don't conflate. Future ship may define `FOREACH_HOT_PATH_GATE` separately.

### Per-node gate predicates

**Option A: Predicate uses CORE-EFFECTIVE cfg (already-merged with per-node override).** AUTOPOPULATE caller pre-merges before evaluation.

**Option B: Predicate takes (cfg, override) pair; merge logic inline in predicate.**

**Decision: B.** Cleaner — registry entry tells you EXACTLY how the predicate is computed (no implicit pre-merge). Pattern below uses macro args `cfg` + `override`.

## The pattern (concrete shape)

### Per-node gate state struct (BIT-PACKED via BITMAP_* API)

```cpp
// Per-core slow-path gate state. Lives on CoreContext<F>.
// Updated at slow-path entry per cycle via SLOW_PATH_GATE_AUTOPOPULATE.
// Read by ML_BuildParameters (via mctx pointer) + ControllerEventLoop direct.
//
// Bit-packed via BITMAP_* API (CLAUDE.md item 20; same shape as v5.14.8.B
// FailureModeRegistry). 7 gates today; 9 bits headroom on uint16_t.
//
// Single-threaded access (per-core slow-path); no atomics needed. GUI display
// reads PerCoreSnap (double-buffered), not gate_state directly.
struct SlowPathGateState {
    uint16_t flags;  // 7 bits used; 9 bits headroom
};
```

**Auto-generated MASK_* constants from registry walk:**

```cpp
// Bit positions (one per registry entry)
enum SlowPathGate {
#define X_GEN_GATE_BIT(name, predicate, doc) GATE_##name,
    FOREACH_SLOW_PATH_GATE(X_GEN_GATE_BIT)
    GATE_COUNT
#undef X_GEN_GATE_BIT
};

// MASK_<NAME> constants (for use sites + multi-flag mask compute)
#define X_GEN_GATE_MASK(name, predicate, doc) \
    static constexpr uint16_t MASK_##name = (1u << GATE_##name);
FOREACH_SLOW_PATH_GATE(X_GEN_GATE_MASK)
#undef X_GEN_GATE_MASK

static_assert(GATE_COUNT <= 16, "SlowPathGateState uint16_t exhausted; expand to uint32_t");
```

### Registry definition (5 per-node ML gates)

```cpp
// FOREACH_SLOW_PATH_GATE(X) — registry of cfg-toggleable slow-path gates
// checked WITHIN ML_BuildParameters body. Per-core; uses resolved_cfg
// (already merged with per-core overrides).
//
// Scope decision: this registry covers per-core gates inside the ML build
// path. Function-entry gates (lazy_rebuild_enabled) and engine-wide gates
// (ws_dead_time_flatten_enabled) stay outside — different cadence + cfg
// semantics. TECH_DEBT-017 catalogs them for future systematic application.
//
// Tuple: X(name, predicate_expr, doc_string)
//   name           — UPPERCASE token used for MASK_<name> + GATE_<name>
//   predicate_expr — expression yielding bool; uses bare `cfg` reference
//                    bound by SLOW_PATH_GATE_AUTOPOPULATE caller. Caller
//                    passes resolved_cfg (already merged with per-core
//                    overrides via ControllerConfig_ResolveForCore), so
//                    predicates don't need explicit override resolution
//   doc_string     — human-readable description
//
// Adding a new gate: append 1 row + all callers automatically pick up
// the new bit on SlowPathGateState.flags + automatic recompute via
// AUTOPOPULATE walk. Use site reads via BITMAP_IS_SET(flags, MASK_<name>).
//
// Pattern documented in DESIGN_SPECS/framework-patterns/slow-path-gate-registry-pattern.md.

#define FOREACH_SLOW_PATH_GATE(X)                                                                   \
    /* v5.14.9.A — soft risk degradation ladder. Composite must be on */                            \
    X(LADDER_ACTIVE,                                                                                 \
      ((cfg).risk_degradation_curve != CURVE_OFF) && ((cfg).confidence_composite_enabled != 0),    \
      "soft risk degradation ladder (curve != OFF AND composite required)")                         \
    /* Pre-v5.14.x — confidence-damped threshold */                                                  \
    X(CONFIDENCE_ENABLED,                                                                            \
      (cfg).confidence_enabled != 0,                                                                 \
      "scale entry threshold by confidence")                                                         \
    /* v5.14.1.B — composite (4-factor) vs legacy (3-factor) confidence */                         \
    X(COMPOSITE_ENABLED,                                                                             \
      (cfg).confidence_composite_enabled != 0,                                                       \
      "use 4-factor composite confidence formula (vs legacy 3-factor)")                             \
    /* v5.14.0 — Ridge within-horizon blend */                                                      \
    X(RIDGE_WITHIN_ACTIVE,                                                                           \
      (cfg).ridge_within_horizon != 0,                                                               \
      "Ridge blend across role-arms within a horizon")                                              \
    /* v5.14.1.E — Ridge exit-side blend */                                                          \
    X(EXIT_BLENDER_ACTIVE,                                                                           \
      (cfg).exit_blender_mode != 0,                                                                  \
      "Ridge blend across exit_predictor handles")
```

### AUTOPOPULATE companion macro (BIT-PACKED via BITMAP_*)

```cpp
// SLOW_PATH_GATE_AUTOPOPULATE(state, cfg, override)
// Walks FOREACH_SLOW_PATH_GATE; uses BITMAP_SET / BITMAP_CLR to set the
// uint16_t bit for each gate based on its predicate.
// Called at slow-path entry per cycle (production cost ~1µs per core total).
//
// Same pattern as STAMP_CFG_AUTOPOPULATE (v5.14.1.B.3) — extinguishes the
// production-caller field-population class for slow-path gate caching.
//
// Adding a new gate = 1 registry row; ALL callers automatically get the
// new bit on SlowPathGateState.flags + automatic recompute.
//
// Branchless variant: build the desired flags value via ternary OR-mask,
// then store once. Avoids per-gate branches; ~7 mask-OR ops + 1 store
// per call vs N conditional stores.

#define SLOW_PATH_GATE_AUTOPOPULATE(state, _cfg_arg, _override_arg)                                  \
    do {                                                                                             \
        const auto& cfg = (_cfg_arg);                                                                \
        const auto& override = (_override_arg);                                                      \
        uint16_t _new_flags = 0;                                                                     \
        #define X_GEN_GATE_AUTOPOP(name, predicate, doc)                                             \
            _new_flags |= ((predicate) ? MASK_##name : 0u);                                          \
        FOREACH_SLOW_PATH_GATE(X_GEN_GATE_AUTOPOP)                                                   \
        #undef X_GEN_GATE_AUTOPOP                                                                    \
        (state).flags = _new_flags;                                                                  \
        (void)cfg; (void)override;  /* suppress unused if no predicate references */                 \
    } while (0)
```

**Branchless property:** each gate's mask contribution is `(predicate ? MASK : 0u)` — compiler emits cmov (no branch). N predicates → N cmovs → 1 OR-reduction → 1 store. No conditional stores; no per-gate branches.

**Note on macro hygiene:** `cfg` + `override` are bound as `const auto&` aliases inside the do-while so registry predicates can reference them as bare identifiers. Same shape as `STAMP_CFG_AUTOPOPULATE` (v5.14.1.B.3).

### Use site: reading from cache (BITMAP_IS_SET)

```cpp
// In ML_BuildParameters (via mctx->gate_state pointer):
if (mctx->gate_state && BITMAP_IS_SET(mctx->gate_state->flags, MASK_LADDER_ACTIVE)) {
    factor = Confidence_DegradationScale(cfg->risk_degradation_curve, ...);
}

// In ControllerEventLoop slow-path (direct access):
if (BITMAP_IS_SET(state->cores[c].gate_state.flags, MASK_LAZY_REBUILD_ACTIVE)
    && /* other conditions */) {
    continue;  // skip rebuild body
}

// Multi-flag check (any blend gate active): branchless mask AND
const uint16_t blend_mask = MASK_RIDGE_WITHIN_ACTIVE | MASK_EXIT_BLENDER_ACTIVE;
if (BITMAP_ANY(state->cores[c].gate_state.flags, blend_mask)) {
    /* shared blend pre-init for either Ridge or exit blender */
}
```

### Recompute call site

```cpp
// In ControllerEventLoop slow-path entry, before RebuildOneCore:
for (int c = 0; c < state->registered_count; ++c) {
    SLOW_PATH_GATE_AUTOPOPULATE(state->cores[c].gate_state,
                                 *config,
                                 cfg->cores[c]);
}
```

## Trade-offs + when to apply

### Apply when:

- ≥3 cfg-toggleable slow-path gates exist (item 13 X-macro threshold met)
- Gates' predicates are stable across a slow-path cycle (cache amortizes cost)
- Use sites span ≥2 files (item 18(d) — pass small struct of resolved predicates)
- New gate additions follow the same shape (cfg field + cached bool + use site)

### Skip when:

- Single-gate situation (registry overhead unjustified for N=1)
- Gate predicates change WITHIN a cycle (cache is incoherent)
- Hot-path gate (use ParameterSlot atomic + flags bitmap pattern instead)

### Cost:

- ~7 predicate evaluations × N cores at slow-path entry per cycle (all branchless via cmov + OR reduction)
- ~2 bytes × N cores memory (negligible: 32 bytes for 16 cores; 14× shrink vs int-per-gate)
- 1 pointer field on `MLBuildContext` (gate_state pointer; 8 bytes)
- Migration of 6 existing gates: ~1 hour each (find use site; replace cfg read with `BITMAP_IS_SET(state.flags, MASK_*)`; update tests) = ~6 hours

### Win:

- Single source of truth for cfg-toggleable slow-path gates
- Per-node override resolution centralized (no inline `(override.X_set ? override.X : cfg.X)` at use sites)
- Adding a new gate = 1 registry row; ALL callers auto-pick-up
- /readiness Check 23 (latency accountability) auto-detects via registry
- /dod-audit Check 27 detects new gates that should fit the pattern
- Drift detection alignment (per-gate emit_when via FOREACH_STAMP_BOUND_CFG cross-ref)

## Reference implementations

- **First applied:** v5.14.9.B.0 (commit pending; tag `v5.14.9.B.0`)
- **Initial registry size:** 7 gates (1 new + 6 migrated existing)
- **Future expansions:** TECH_DEBT-017 inventory tracks `use_aot_inference` + `ridge_across_horizons` (currently infrastructure-only; no consumers; migrate when consumers land)

## Lessons / gotchas

### `param_staleness_gate_enabled` stays outside the registry

Hot-path gate; cached in `cached_params.flags` bitmap (set by slow-path rebuild via ParameterSlot atomic store; read by hot path with seqlock semantics). Different mechanism from per-node bool cache. Keeping it separate avoids forcing slow_state load on hot path.

Future ship may define `FOREACH_HOT_PATH_GATE` for hot-path gates if more accumulate. For now: only 1 hot-path gate; no registry justified.

### `use_aot_inference` + `ridge_across_horizons` are infrastructure-only

Both have cfg fields + parser entries but no current code consumers (per /trace-deps audit 2026-05-10). They're INFRASTRUCTURE from v5.12.2.D + v5.14.0 respectively, awaiting full implementation. NOT migrated in v5.14.9 — they don't have use sites to migrate.

When a future ship adds consumers, the consumer adds the gate to FOREACH_SLOW_PATH_GATE in the same commit. TECH_DEBT-017 catalogs them.

### Macro hygiene: `#define cfg _cfg` inside AUTOPOPULATE

The rebinding looks weird but is necessary so registry predicates can use bare `(cfg).X` syntax (consistent with STAMP_CFG_AUTOPOPULATE). The do-while ensures undef restoration. Alternative would be passing cfg/override as function-style macro args throughout (e.g., `FOREACH_SLOW_PATH_GATE(X, cfg_arg, override_arg)`), but that requires every X helper macro to accept the args — verbose.

### Per-node override consistency check

For per-node gates (ladder), the AUTOPOPULATE merge logic must match what the use site would compute. Verified: ladder predicate uses `((override).risk_degradation_curve_set ? (override).risk_degradation_curve : (cfg).risk_degradation_curve)` — same pattern as existing per-node resolution at `EngineSharded.hpp:1222-1224` for `tau_eff` (legacy field, soon-to-be-deleted).

### Recompute cost amortization

7 predicates × 16 cores = 112 boolean computations per slow-path cycle. Each is ~3 ALU ops (logical AND/OR + ternary). Total: ~350 ALU ops. At slow-path entry, this is ~50ns of work amortized across the cycle. Cheaper than re-reading 7 cfg fields × N use sites within RebuildOneCore.

### Future stamp-bound integration

Several gates' cfg fields are already stamp-bound via FOREACH_STAMP_BOUND_CFG (composite_enabled, ridge_*, exit_blender_mode). v5.14.9.C ADDS the ladder fields. Drift detection per-gate is automatic via the existing FOREACH_STAMP_BOUND_CFG mechanism — orthogonal to the slow-path cache. Both registries coexist (different concerns: stamp-binding for train/serve drift; slow-path cache for runtime perf).

## Migration sequence (v5.14.9.B.0 implementation)

1. Define `SlowPathGateState` struct + `FOREACH_SLOW_PATH_GATE` registry in new header `CoreFrameworks/SlowPathGateRegistry.hpp`
2. Define `SLOW_PATH_GATE_AUTOPOPULATE` companion macro in same header
3. Add `SlowPathGateState gate_state` field to `CoreContext<F>` (per-node)
4. Add `gate_state` pointer to `MLBuildContext`
5. Wire AUTOPOPULATE call at `EventLoop_RebuildOneCore` entry per core
6. Migrate 6 existing use sites:
   - `ControllerEventLoop.hpp:1992` — lazy_rebuild
   - `ControllerEventLoop.hpp:~522` — ws_dead_time_flatten
   - `Strategies/StrategyParameters.hpp:1222, 1257` — confidence_enabled
   - `Strategies/StrategyParameters.hpp:1227` — confidence_composite_enabled
   - `Strategies/StrategyParameters.hpp:908` — ridge_within_horizon
   - `Strategies/StrategyParameters.hpp:1106` — exit_blender_mode
7. Add ladder gate use site (in v5.14.9.B; reads `mctx->gate_state->ladder_active`)
8. Tests: per-gate predicate correctness + per-node override resolution + AUTOPOPULATE walk + count assertion

Estimated effort: 8-10h (audit+design 2h, registry+AUTOPOPULATE 2h, migration 4-5h, tests 1-2h).

## What this pattern is NOT

- Not for hot-path gates (use ParameterSlot atomic + flags bitmap instead)
- Not for non-cfg gates (e.g., runtime-state predicates that aren't cfg-toggleable)
- Not for one-off boot-time validation (boot REFUSE checks live in EngineSharded boot, not here)
- Not a replacement for FOREACH_STAMP_BOUND_CFG (orthogonal — drift detection vs runtime cache)

## Cross-ref: TECH_DEBT-017 inventory

After v5.14.9.B.0 ships, TECH_DEBT-017 catalogs:
- `use_aot_inference` — INFRASTRUCTURE-ONLY; trigger: consumer added
- `ridge_across_horizons` — INFRASTRUCTURE-ONLY; trigger: consumer added
- `param_staleness_gate_enabled` — HOT-PATH; trigger: FOREACH_HOT_PATH_GATE registry created if N hot-path gates ≥ 3
- (Future cfg-toggleable slow-path gates) — append to FOREACH_SLOW_PATH_GATE per the established pattern

Each entry has trigger conditions documented; future ships address per natural boundary.
