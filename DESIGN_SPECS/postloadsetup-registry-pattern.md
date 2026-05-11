# PostLoadSetup registry pattern (FOREACH_<DOMAIN>_POST_LOAD — auto-flow init/load steps to N call sites)

**Established:** 2026-05-09 (v5.14.2.E.1 — FOREACH_ENSEMBLE_POST_LOAD; PARITY-009/010/011/012 closure)
**Promoted to dedicated DESIGN_SPECS:** 2026-05-11 (after 3rd application in v5.14.10.C)
**Status:** ACTIVE
**Cross-references:**
- First application: `ML_Headers/CoreModelZoo.hpp:2370-2389` (FOREACH_ENSEMBLE_POST_LOAD; 9 entries today)
- Sister pattern: `structural-fix-preferred-decision-framework.md` (the underlying rationale: Class 18 mirror prevention)
- Sister pattern: `autopopulate-pattern-for-production-caller-class.md` (related; auto-population of struct fields at N call sites)
- Base pattern: `x-macro-registry-with-presence-dispatch.md` (registry shape this builds on)
- CLAUDE.md item 13 (X-macro registry for multi-site additions)
- CLAUDE.md item 19 (structural fix preferred when bug class can recur)

---

## Problem statement

A subsystem requires a sequence of POST-LOAD setup steps (init bandits, set blend mode, parse disabled horizons, load persisted state, etc.). These steps must run after the subsystem loads (e.g., after `EnsembleModelZoo_LoadFromCfg` populates handle arrays) and BEFORE first use.

The setup steps are needed at MULTIPLE production call sites:

- **Boot path** — engine startup loads models, runs setup
- **Backtest path** — backtest runner loads models per fold, runs setup
- **Hot-swap path** — operator-initiated model reload, runs setup
- **Test path** — synthetic harness, may bypass real loaders

Naïve approach: each call site hand-codes the sequence:

```cpp
// boot path
EnsembleModelZoo_InitBandits(ezoo, eta, warmup);
EnsembleModelZoo_InitExitBandits(ezoo, lr, warmup);
apply_blend_mode(ezoo, cfg, core);
EnsembleModelZoo_SetDisabledHorizons(ezoo, cfg.core_disabled_horizons[core]);
EnsembleModelZoo_LoadBanditState(ezoo, base_path);
EnsembleModelZoo_SetBanditSaveInterval(ezoo, cfg.ensemble_bandit_save_interval);
EnsembleModelZoo_LoadExitBanditState(ezoo, base_path);

// backtest path
EnsembleModelZoo_InitBandits(ezoo, eta, warmup);
EnsembleModelZoo_InitExitBandits(ezoo, lr, warmup);
// ... operator might forget a step here; backtest results diverge from live
```

**Recurring pain points (Class 18 mirror — same pattern at N call sites drifts apart):**

1. **Adding a new step touches N sites** — N = boot + backtest + hot-swap + test. Each site adds a new line. Forgetting one = subsystem missing the step → silent bug at that path's runtime.
2. **Reorder risk** — some steps depend on others (load_bandit_state must run AFTER init_bandits). Manual ordering drifts; one site reorders, others don't.
3. **No symmetric test** — "boot path produces same ezoo state as backtest path" requires walking both sequences and comparing; if sequences differ silently, test fails opaquely.
4. **Recurring bug class** — v5.14.2.E.1 closure of PARITY-009/010/011/012 (9 sub-gaps) was THIS exact class: init/load steps added in v5.13.4 (exit_bandits) hadn't propagated to all 3 callers. Same shape recurred 4× before structural fix landed.

The X-macro registry pattern + helper-walks-registry solves it.

---

## When does it apply? (Trigger conditions)

Apply this pattern when ALL of the following hold:

1. **Sequence of N steps** — subsystem requires N ≥ 3 post-load setup calls (≥3 = enough for drift)
2. **M ≥ 2 call sites** — boot + backtest at minimum; usually +hot-swap +test
3. **Step ordering matters** — some steps depend on prior steps (init before load; load before save-interval set)
4. **Step set grows** — future ships will add more steps (new bandit type, new persistence file, new validation step)
5. **Class 18 mirror risk** — adding a step at one call site but forgetting another would silently break that path

---

## The pattern (concrete shape)

### Step 1: Define the registry

```cpp
// X(step_name, call_expression). Expression invoked with (ezoo, cfg, core_id, base_run_path)
// in scope from the helper body.
//
// Adding a new step: 1 line here. All call sites inherit.
//
// ORDER MATTERS — steps execute in declaration order. Init steps before Load steps
// before SetSaveInterval. Re-ordering existing entries risks behavior change; APPEND new
// entries at the appropriate position (init early; load mid; periodic-config late).

#define FOREACH_ENSEMBLE_POST_LOAD(X)                                                  \
    X(init_bandits,          EnsembleModelZoo_InitBandits(ezoo,                         \
                                 cfg.ensemble_bandit_eta,                                 \
                                 cfg.ensemble_min_warmup_predictions))                    \
    X(init_exit_bandits,     EnsembleModelZoo_InitExitBandits(ezoo,                       \
                                 cfg.exit_bandit_lr,                                       \
                                 cfg.ensemble_min_warmup_predictions))                    \
    X(blend_mode,            ensemble_post_load_apply_blend_mode(ezoo, cfg, core_id))    \
    X(disabled_horizons,     EnsembleModelZoo_SetDisabledHorizons(ezoo,                   \
                                 cfg.core_disabled_horizons[core_id]))                    \
    X(load_bandit_state,     EnsembleModelZoo_LoadBanditState(ezoo, base_run_path))      \
    X(save_interval,         EnsembleModelZoo_SetBanditSaveInterval(ezoo,                 \
                                 cfg.ensemble_bandit_save_interval))                      \
    X(load_exit_bandit,      EnsembleModelZoo_LoadExitBanditState(ezoo, base_run_path)) \
    /* v5.14.10.C — Thompson sampling bandit init + load */                              \
    X(init_thompson_bandits, EnsembleModelZoo_InitThompsonBandits(ezoo,                   \
                                 FPN_ToDouble(cfg.thompson_mu_prior),                     \
                                 FPN_ToDouble(cfg.thompson_precision_prior),              \
                                 FPN_ToDouble(cfg.thompson_precision_obs),                \
                                 cfg.thompson_rng_seed))                                  \
    X(load_thompson_state,   EnsembleModelZoo_LoadThompsonState(ezoo, base_run_path))
```

**Caller scope contract:** the X-macro expansion expects these variables in scope at the helper body:
- `ezoo` — `EnsembleModelZoo<F>*` to the zoo being set up
- `cfg` — `const ControllerConfig<F>&` (reference; for reading cfg fields)
- `core_id` — `int` (which per-core slot is being initialized; for per-core overrides)
- `base_run_path` — `const char*` (where persistence sidecar files live)

Document this contract IN-FILE adjacent to the registry. Future contributors will write registry entries that fail to compile in the caller scope without it.

### Step 2: Auto-generated count for tests

```cpp
// Compile-time count for tests. Updated when adding entries.
#define FOREACH_ENSEMBLE_POST_LOAD_COUNT 9
```

Tests assert the count matches expected (catches "forgot to update count" + "snuck in a non-registry call" at compile time).

### Step 3: Helper that walks the registry

```cpp
template <unsigned F>
inline void EnsembleModelZoo_PostLoadSetup(EnsembleModelZoo<F>* ezoo,
                                             const ControllerConfig<F>& cfg,
                                             int core_id,
                                             const char* base_run_path) {
    if (!ezoo || !base_run_path) return;
#define X(name, expr) expr;
    FOREACH_ENSEMBLE_POST_LOAD(X)
#undef X
}
```

That's the entire helper body. The X-macro expansion produces the literal sequence of calls in registry order.

### Step 4: Production callers invoke the helper (NOT the steps directly)

Boot path (`CoreFrameworks/EngineSharded.hpp`):
```cpp
EnsembleModelZoo_PostLoadSetup<F>(&ezoo, cfg, /*core_id=*/i, base_run_path);
```

Backtest path (`Backtest/BacktestSharded.hpp`):
```cpp
EnsembleModelZoo_PostLoadSetup<F>(&ml_ensemble_zoos[i], cfg, /*core_id=*/i, base_run_path);
```

Hot-swap path (`CoreFrameworks/EnsembleHotSwap.hpp`):
```cpp
EnsembleModelZoo_PostLoadSetup<F>(&ezoo, cfg, core_id, base_run_path);
```

Each caller's wiring stays as ONE LINE — never inline the step sequence.

### Step 5: Symmetry contract predicate

```cpp
// Returns 1 iff the ezoo has all the side-effects that PostLoadSetup applies.
// Adding a new step to FOREACH_ENSEMBLE_POST_LOAD requires also extending
// this predicate so the contract stays honest.
//
// Tests assert: pre-PostLoadSetup → false; post-PostLoadSetup → true.
// If anyone adds a new step at boot/backtest/hot-swap that bypasses the helper,
// the symmetry test compares boot output vs helper output and the missing step
// shows up as a false return here OR as a state divergence.
template <unsigned F>
inline int EnsembleModelZoo_IsReadyForInference(const EnsembleModelZoo<F>* ezoo) {
    if (!ezoo) return 0;
    // Step contracts (mirror FOREACH_ENSEMBLE_POST_LOAD):
    if (ezoo->primary_count >= 2 && !ezoo->initialized_bandits) return 0;
    if (ezoo->exit_predictor_count >= 2 && !ezoo->initialized_exit_bandits) return 0;
    if (ezoo->primary_count >= 2 && !ezoo->initialized_thompson_bandits) return 0;
    if (ezoo->blend_mode[0] == '\0') return 0;
    return 1;
}
```

**Important:** when adding a new step to the registry that has a checkable side-effect (e.g., sets a flag, populates a field), ALSO extend this predicate. Tests using the contract pattern will catch the omission. See v5.14.10.C "Surprise 6" in the v5.14.10 postmortem for an example where the predicate extension broke a pre-existing contract test (test fix: also set the new flag in the test setup).

### Step 6: Tests

```cpp
// Compile-time: count assertion
static_assert(FOREACH_ENSEMBLE_POST_LOAD_COUNT == 9, "Update count when adding entries");

// Runtime: contract pre/post
{
    EnsembleModelZoo<64> ezoo;
    EnsembleModelZoo_Init(&ezoo);
    ezoo.primary_count = 3;
    // primary_count >= 2 → contract requires initialized_bandits + initialized_thompson_bandits
    check("contract: pre-PostLoadSetup not-ready (bandit flags zero)",
          EnsembleModelZoo_IsReadyForInference(&ezoo) == 0);
    ControllerConfig<64> cfg = ControllerConfig_Default<64>();
    strncpy(cfg.ensemble_blend_mode, "weighted", sizeof(cfg.ensemble_blend_mode) - 1);
    EnsembleModelZoo_PostLoadSetup<64>(&ezoo, cfg, /*core_id=*/0, "/tmp/test_dir");
    check("contract: post-PostLoadSetup ready",
          EnsembleModelZoo_IsReadyForInference(&ezoo) == 1);
}

// Runtime: symmetry across callers (not yet implemented as automated test; manual
// verification today; could be added as a CI check that compares boot/backtest/hot-swap
// state after running each helper on the same input ezoo)
```

---

## Trade-offs + when to apply

### Apply when:
- N ≥ 3 setup steps + M ≥ 2 call sites
- Steps grow over time (new ship adds a step)
- Step ordering matters (init-before-load dependency)
- Symmetry across call sites is a correctness invariant

### Skip when:
- N ≤ 2 steps (registry overhead not justified; inline the 2 calls)
- M = 1 call site (no mirror risk; registry is gratuitous)
- Steps are independent + order-agnostic (less ordering risk; manual sequences OK)
- Subsystem is throwaway / experimental (registry adds permanence; weigh against churn cost)

### Cost:
- ~30-50 LOC for registry + helper + count + predicate skeleton
- ~5-10 LOC per future step addition (1 registry row + 1 predicate check if applicable)
- Test scaffolding: ~30-50 LOC for the contract pre/post tests

### Win:
- Adding a new step = 1 row in registry; ALL M call sites auto-flow
- Reorder discipline enforced (registry order = execution order; one site change applies everywhere)
- Symmetric across callers by construction (no inlined-divergence risk)
- Contract predicate makes test scaffolding cheap (pre/post check per setup)
- Class 18 mirror DRIFT becomes structurally impossible (N call sites all walk the same registry)

---

## Wire-format byte preservation

**N/A.** PostLoadSetup runs at init time and produces no serialized output directly (some steps internally serialize, but the helper itself doesn't). Wire-format discipline applies to the steps that DO serialize (e.g., `LoadBanditState`, `LoadThompsonState`), not to the helper composing them.

---

## Reference applications

| Application | Registry | Site | Notes |
|---|---|---|---|
| v5.10.0a.G.7 | FOREACH_ENSEMBLE_POST_LOAD | `CoreModelZoo.hpp:2370+` | Original; init_bandits + blend_mode + disabled_horizons + load_bandit_state + save_interval (5 entries) |
| v5.13.4 | FOREACH_ENSEMBLE_POST_LOAD (extended) | same | +2 entries: init_exit_bandits + load_exit_bandit. PARITY-009/010/011/012 closure (v5.14.2.E.1; backfill of mirror gaps that recurred 4× before structural fix) |
| v5.14.10.C | FOREACH_ENSEMBLE_POST_LOAD (extended) | same | +2 entries: init_thompson_bandits + load_thompson_state. /trace-deps BLOCKING amendment caught this BEFORE coding (would have been Class 18 mirror gap if PostLoadSetup pattern weren't already established) |

Single-zoo sibling (v5.10+):
| Application | Registry | Site | Notes |
|---|---|---|---|
| v5.10+ | FOREACH_SINGLE_ZOO_POST_LOAD | `CoreModelZoo.hpp:2440+` | 1 entry today (verify_expected); designed for growth; same pattern at smaller scale |

---

## Future application candidates

| Candidate | Trigger to apply |
|---|---|
| Single-zoo (`CoreModelZoo`) — add more steps | When non-trivial single-zoo init logic emerges (e.g., per-core ML cfg validation, model-version drift checks). Single-zoo POST_LOAD already exists; just append. |
| Per-core slow-path init | If `EventLoopCoreState_Init` accumulates 5+ steps; currently inline. Promote to `FOREACH_CORE_SLOW_PATH_INIT` when count threshold crossed. |
| Maker-side post-load (v6.0+) | When maker order MVP ships + has its own load discipline; mirror the ensemble pattern. |
| Multi-symbol fan-out (v5.16+) | If multi-symbol introduces per-symbol setup steps; could be `FOREACH_SYMBOL_POST_LOAD`. |

---

## Lessons / gotchas

### Step ordering matters; document dependencies

Some steps depend on prior steps (e.g., `LoadBanditState` requires `InitBandits` first because Load is overlay-only on top of uniform priors). Comment the registry with dependency notes:

```cpp
X(init_bandits, ...)        \  /* Must run before load_bandit_state (provides uniform priors to overlay onto) */
...
X(load_bandit_state, ...)   \  /* Depends on init_bandits */
```

Don't rely on contributors to know the ordering implicitly. The registry IS the ordering documentation.

### Symmetry contract predicate must stay synchronized

Adding a new step to the registry **without** extending `IsReadyForInference` causes the contract test to PASS while a new caller would fail (predicate says "ready" but the new state isn't set). Symmetric: extending the predicate **without** the registry causes the contract test to FAIL spuriously (predicate requires state that no step sets).

Treat the registry + predicate as a UNIT. Update both in the same commit.

### Caller scope contract is brittle (same as other registry patterns)

If a registry entry's call expression references a variable that ISN'T in scope at the caller, compile fails with cryptic preprocessor expansion errors. Document the caller scope contract IN-FILE adjacent to the registry definition.

### Test the helper PER-CALLER, not just standalone

The whole point is symmetry across callers. Test that:
1. Boot caller → ezoo state X
2. Backtest caller → ezoo state X (same)
3. Hot-swap caller → ezoo state X (same)

A test that only exercises the helper standalone misses the "did boot path correctly invoke the helper?" risk. The helper is correct by construction; the question is whether callers REMEMBER to invoke it.

### "Boundary-stable refactor" principle (CLAUDE.local.md going-forward rule)

When introducing this pattern to an EXISTING N-step sequence, do it as a boundary-stable refactor:
- Public API of the helper stays uniform across N call sites (one fn signature, one invocation)
- Internal X-macro is hidden implementation detail
- Existing inline sequences at call sites collapse to single helper call (1 line each)

This minimizes blast radius. The N call sites' OTHER logic stays untouched.

### Class 18 mirror prevention is the REAL value

Without this pattern: adding a new step means hand-editing N call sites. Easy to forget one. The bug manifests only at the forgotten path's runtime (which may be backtest, hot-swap, or test — all paths with less coverage than boot).

With this pattern: adding a new step = 1 row. ALL N call sites inherit. The bug class becomes STRUCTURALLY impossible. This is the load-bearing reason to invest in the pattern even when N is small.

Per CLAUDE.md item 19 (structural fix preferred when bug class can recur), this is the canonical example.

---

## Audit detection

`/dod-audit` flags missed applications by:

- Symptom: 3+ init/load fn calls in sequence at 2+ call sites (boot + backtest + hot-swap) with same shape
- Symptom: PARITY ledger entry describing "init step X added at site A but missed at site B" → suggests the pattern would prevent
- Symptom: hand-coded init sequence in a header that should call `<Domain>_PostLoadSetup` helper but inlines steps directly

When detected → flag as `MISSED — postloadsetup-registry-pattern`. Recommended fix: extract registry + helper + invoke helper at all call sites.

`/trace-deps` Step 6 (call-sequence enumeration) catches the same class at PLAN time: when a plan adds N init/load steps, verify the plan invokes the existing PostLoadSetup helper rather than inlining new sequences.

---

## Patterns NOT used here (and why)

### Virtual function dispatch (`InitializableComponent` interface)

Object-oriented design pattern. Each component implements `init()`; PostLoadSetup walks a list of components calling `init()` on each. Rejected per CLAUDE.md project conventions (no virtual; no class hierarchies in slow/hot path code). Vtable indirection + heap allocation = anti-philosophy.

### Function-pointer table

`std::array<void (*)(...), N> setup_fns;` walked at runtime. Same as registry conceptually but DYNAMIC. Adds indirection cost (single indirect call ~1-2ns) + obscures the static sequence. X-macro registry produces literal sequential calls at compile time → zero indirection.

### Builder pattern

`PostLoadBuilder().init_bandits().load_state().run()` fluent API. C++-class-flavored; same vtable / allocation objections as virtual functions. Doesn't fix the "N call sites must remember to call all setup steps" mirror class — operator can still forget to call one of the builder methods at a call site.

---

## Cross-references

- `structural-fix-preferred-decision-framework.md` — the underlying rationale (Class 18 mirror prevention via compile-time enforcement)
- `autopopulate-pattern-for-production-caller-class.md` — sister pattern (struct-field auto-population at N call sites; analogous to step auto-flow)
- `x-macro-registry-with-presence-dispatch.md` — base X-macro pattern this builds on
- `registry-tuple-as-single-source-of-truth.md` — meta-pattern (registry tuple feeds N consumers)
- FoxML_Trader_v2 `CLAUDE.md` item 13 (X-macro for multi-site additions)
- FoxML_Trader_v2 `CLAUDE.md` item 19 (structural fix preferred when bug class can recur)
- FoxML_Trader_v2 `ML_Headers/CoreModelZoo.hpp:2370-2433` — reference implementation
- v5.14.2.E.1 ship (commit history) — first systematic application; PARITY-009/010/011/012 closure documenting the 4-recurrence pattern that motivated the structural fix
- v5.14.10.C ship (commit `ca4259f`) — third application (Thompson init+load); demonstrated /trace-deps BLOCKING amendment catching what would have been the 5th recurrence of Class 18 mirror in the same domain
- v5.14.10 postmortem (Surprise 6, Lesson 5) — captures the IsReadyForInference contract-extension pattern that pairs with this DESIGN_SPECS
