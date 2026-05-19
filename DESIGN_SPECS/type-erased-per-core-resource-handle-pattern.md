---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-16
tags: [framework-discipline, concurrency, structural-fix]
surface: [registry, slow-path]
sister_specs: [type-trait-dispatch-via-tt-namespace.md, per-instance-registry-pattern.md]
applies_at_skills: []
---

# Type-erased per-core resource handle pattern

**Established:** 2026-05-16 (v5.15.5.F.4d.1 planning; codified at the moment of 3rd canonical application landing per `pattern-codification-lifecycle.md` Stage 2 DRAFT threshold met)
**Status:** **Stage 2 DRAFT v1.0** (3 canonical applications observed at `.F.4d` ship close; framework codification at the freshest moment per CLAUDE.md item 31 + `feedback_overengineering_boundary_when_future_easier` — pick harder now when future cohort migrations become 1-row mechanical against this reference)
**Tags:** structural-fix, framework-discipline, cross-layer-isolation, cluster-placement; closes "ad-hoc cross-layer crossings" class structurally; serves H1 (no virtual dispatch), H6 (cache cluster discipline), H17 (cfg struct independence); Stage 2 (DRAFT); 3 applications

**Cross-references:**
- Sister pattern: `decision-time-data-binding-pattern.md` (Pattern 4 — per-instance data flows with in-flight Order/Position carrier; this pattern is sister for cross-layer-but-not-per-fill state references)
- Composes with: `framework-composition-overview.md` (cfg infra at `.F.4d` — void* fields on layer-X state pointing to layer-Y typed objects are part of the composition substrate)
- Composes with: `cache-layout-discipline-for-hot-side-structs.md` (void* fields fit COLD cluster placement; populated at boot; read at consumer site infrequently)
- Composes with: `meta-registry-pattern-for-codebase-registry-discipline.md` (engine-wide singleton state + per-core void* arrays indexed by `Order::core_id` mirrors meta-registry's parent-child indexing scheme)
- Anti-pattern this prevents: Class 21 latent at cross-layer surfaces (would manifest as parallel typed-pointer descriptors per consumer subsystem)
- Closes: "ad-hoc cross-layer crossings" — pre-codification, each new cross-layer reference invented its own mechanism (typed pointer + forward decl, OR templated layer-X, OR polymorphic base); framework discipline codifies the void*+cast choice + variant decision
- Serves: **H1** (no virtual dispatch — void*+cast doesn't introduce vtable), **H6** (void* fields fit cluster placement discipline), **H17** (layer-X cfg struct stays independent of layer-Y type instantiation)
- CLAUDE.md item 31 (Framework-driven extensibility — meta-principle)

---

## Problem statement

The codebase has multiple structural layers with deliberate type-isolation:

| Layer | Owns | Headers |
|---|---|---|
| **CoreFrameworks** | ExecutionCore + OMS + Portfolio + ControllerEventLoop + EngineSharded — engine plumbing | `CoreFrameworks/` |
| **ML_Headers** | CoreModelZoo + EnsembleModelZoo + ModelInference + ConfidenceScore + bandit/thompson — ML state | `ML_Headers/` |
| **Strategies** | RegimeDetector + MeanReversion + Momentum + EmaCross + MLStrategy — per-strategy logic | `Strategies/` |

**Constraint:** CoreFrameworks state (e.g., `OrderManagerState<F>`, `CoreContext<F>`) sometimes needs to reference ML_Headers objects (e.g., `EnsembleModelZoo<F>*` for calib log emit; `PerCoreCfg<F>*` for fee resolution context) — but pulling ML_Headers types into CoreFrameworks headers would:

1. **Break separability** — CoreFrameworks should compile standalone (engine plumbing without ML hooks should be possible for testing + simpler builds)
2. **Inflate template instantiation** — every ML_Headers template (`EnsembleModelZoo<F>`, `PerCoreCfg<F>`, `CoreModelZoo<F>`) would force re-instantiation through CoreFrameworks at every F variant
3. **Create circular include risk** — ML_Headers already pulls CoreFrameworks (for OrderManagerState, etc.); reverse direction adds cycles
4. **Conflict with H1** — polymorphic base-class alternative would introduce vtables (virtual dispatch FORBIDDEN on hot path)

The recurring shape: **"Layer X state holds a reference to a Layer Y resource; layer Y is in scope at consumer site only; cross-thread / cross-core indexing applies."** Without a framework, each instance picks its own mechanism (forward decl, templated host, polymorphic base) — Class 21 (parallel descriptors) latent at cross-layer surfaces; future contributors invent N+1th mechanism for application N+1.

---

## Design space explored

### Option A — Forward declarations + typed pointer

```cpp
// CoreFrameworks/OrderManager.hpp
template<unsigned F> struct EnsembleModelZoo;  // forward decl

template <unsigned F>
struct OrderManagerState {
    EnsembleModelZoo<F>* ezoo_refs[MAX_EXECUTION_CORES] = {nullptr};
    ...
};
```

**Rejected.** Forward decl works for the pointer type, but consumer site MUST include the full `EnsembleModelZoo` definition (to call methods on it). At consumer site (`OrderManager.hpp`, slow-path body), pulling `<ML_Headers/CoreModelZoo.hpp>` creates inverted include dependency (CoreFrameworks → ML_Headers). Cycles emerge if ML_Headers ever wants to call back. Also forces every CoreFrameworks consumer to instantiate `EnsembleModelZoo<F>` for type-checking even if they don't use it.

### Option B — Template the layer-X struct on layer-Y type

```cpp
template <unsigned F, typename EZooT, typename CfgT>
struct OrderManagerState {
    EZooT*       ezoo_refs[MAX_EXECUTION_CORES];
    const CfgT*  core_cfg_refs[MAX_EXECUTION_CORES];
    ...
};
```

**Rejected.** Inflates template instantiation N× (each consumer site instantiates the full state struct anew with its concrete type params). Forces every layer-X consumer to know layer-Y's type. Breaks layer-X-without-ML build configurations. Adds compile-time cost without benefit (the layer-X consumer doesn't NEED layer-Y type info except at the cast site).

### Option C — Polymorphic base class via virtual interface

```cpp
struct AbstractEnsembleZoo {
    virtual ~AbstractEnsembleZoo() = default;
    virtual void on_exit_calibration_data(...) = 0;
};

template <unsigned F>
struct EnsembleModelZoo : AbstractEnsembleZoo { ... };

// CoreFrameworks/OrderManager.hpp
struct OrderManagerState {
    AbstractEnsembleZoo* ezoo_refs[MAX_EXECUTION_CORES] = {nullptr};
};
```

**Rejected.** **H1 violation** — `virtual` is forbidden in this codebase (no virtual / no vtable / no shared_ptr / no unique_ptr per CLAUDE.md hard invariants). Polymorphic dispatch would inject vtable lookup at consumer call site (~3-5ns latency + cache miss on indirect target). For hot/slow path consumers this would be a strict regression.

### Option D — Type-erased void* + cast at consumer (chosen)

```cpp
// CoreFrameworks/OrderManager.hpp — ML-agnostic
template <unsigned F>
struct OrderManagerState {
    // void* keeps OmsState ML-agnostic; cast to EnsembleModelZoo<F>* / const PerCoreCfg<F>*
    // at consumer site where ML_Headers / PerCoreCfg types are in scope.
    void*       ezoo_refs[MAX_EXECUTION_CORES]     = {nullptr};
    const void* core_cfg_refs[MAX_EXECUTION_CORES] = {nullptr};
};

// CoreFrameworks/EngineSharded.hpp — boot wires (ML_Headers in scope here)
oms.ezoo_refs[i]     = (void*)ezoo_ptr;
oms.core_cfg_refs[i] = (const void*)&cfg.cores[i];

// CoreFrameworks/OrderManager.hpp real_on_exit_calibration body — cast at consumer
auto* ezoo     = static_cast<EnsembleModelZoo<F>*>(oms->ezoo_refs[pslot]);
auto* core_cfg = static_cast<const PerCoreCfg<F>*>(oms->core_cfg_refs[pslot]);
```

**Chosen.** Layer X state stays type-agnostic; layer X header stays minimal; consumer site (where layer-Y types ARE in scope via include) does the cast. Zero virtual dispatch (no H1 violation). Single header include for layer-X consumers without ML. Cluster placement fits naturally (void* fields are 8-byte aligned + can sit in cold cluster). 1 cycle for cast at consumer (just register reinterpret; no runtime work).

---

## The pattern (concrete shape)

Two sub-variants exist based on the parent struct's ownership topology:

### Variant A — Single void* on per-core context

When the **parent struct is itself per-core** (one instance per execution core in the engine state's `state.cores[]` array), the resource handle is a single void* field on the per-core member:

```cpp
// CoreFrameworks/ControllerEventLoop.hpp — CoreContext<F> at ControllerEventLoop.hpp:279
template <unsigned F>
struct CoreContext {
    // ... per-core engine state ...
    void* ensemble_handle;  // EnsembleModelZoo<F>* when multi-horizon active; nullptr = single-zoo path
    // ... more per-core fields ...
};

// Boot wiring (CoreFrameworks/EngineSharded.hpp:1061): one assignment per core
state.cores[i].ensemble_handle = ezoo_ptr;

// Consumer cast (CoreFrameworks/ControllerEventLoop.hpp:1688-1689): from ctx
if (ctx.ensemble_handle) {
    auto* ezoo = static_cast<EnsembleModelZoo<F>*>(ctx.ensemble_handle);
    // ... per-core ezoo work ...
}
```

**Use when:** parent struct's ownership topology is per-core; consumer always has per-core context (ctx, slow-state, etc.) in scope.

### Variant B — Per-core void* array on engine-wide singleton state

When the **parent struct is engine-wide singleton** (single instance shared by all cores; not per-core), the resource handle is a **per-core array indexed by core_id**:

```cpp
// CoreFrameworks/OrderManager.hpp — OrderManagerState<F> at OrderManager.hpp:624-625
template <unsigned F>
struct OrderManagerState {
    // ... engine-wide OMS state ...
    void*       ezoo_refs[MAX_EXECUTION_CORES]     = {nullptr};   // EnsembleModelZoo<F>* per-core (lazy-cast)
    const void* core_cfg_refs[MAX_EXECUTION_CORES] = {nullptr};   // const PerCoreCfg<F>* per-core (lazy-cast)
    // ... more engine-wide fields ...
};

// Boot wiring (CoreFrameworks/EngineSharded.hpp:1067-1068): N assignments — one per core
// inside the per-core init loop
oms.ezoo_refs[i]     = (void*)ezoo_ptr;
oms.core_cfg_refs[i] = (const void*)&cfg.cores[i];

// Consumer cast (CoreFrameworks/OrderManager.hpp:707-708): indexed by Order::core_id
auto* ezoo     = static_cast<EnsembleModelZoo<F>*>(oms->ezoo_refs[o->core_id]);
auto* core_cfg = static_cast<const PerCoreCfg<F>*>(oms->core_cfg_refs[o->core_id]);
```

**Use when:** parent struct's ownership topology is engine-wide singleton; consumer site has an in-flight object carrying `core_id` (Order, Position, Event, TradeEvent). Indexing by `core_id` mirrors the sibling-array pattern (per-slot `last_exit_fee[]` + `bandit_reward_bps[]` on OmsState).

### Topology decision — which variant?

Verify parent struct's ownership topology BEFORE writing code. The decision question:

> *"Is the parent struct instantiated per-core (one in `state.cores[i].my_state`) OR engine-wide singleton (one in `state.my_state`)?"*

Variant choice falls out:

| Parent struct topology | Variant | Example |
|---|---|---|
| Per-core member of `state.cores[]` | **Variant A** (single void*) | `state.cores[i].ensemble_handle` |
| Engine-wide singleton state | **Variant B** (per-core void* array indexed by core_id) | `state.oms.ezoo_refs[core_id]` |

**Anti-pattern (caught at `.F.4d` § F):** assuming the parent struct is per-core when it's actually engine-wide singleton. Sidecar examples doc draft proposed `state.cores[i].oms.ezoo_ref` (Variant A shape) without verifying that `state.cores[i].oms` actually exists. It doesn't — OmsState is engine-wide singleton at `state.oms` (EngineSharded line 662). Correct design: Variant B (per-core array on engine-wide state). See "Lessons / gotchas" below for the codified discipline.

---

## Trade-offs + when to apply

### Apply when:
- Cross-layer reference is from CoreFrameworks → ML_Headers / Strategies (or any low-layer → high-layer pull)
- Pulling the high-layer's typed header into low-layer would break separability / inflate templates / create cycles
- Consumer site DOES have the high-layer types in scope (via its own include path)
- Resource is boot-wired (not allocated per-fill / per-tick) — single late-binding wire site
- No virtual dispatch (H1 protected)

### Skip when:
- Cross-layer reference is needed at per-fill / per-tick hot-path latency budget — use `decision-time-data-binding-pattern.md` Pattern 4 (pre-resolve onto in-flight Order/Position carrier; eliminates per-fill cast indirection)
- Parent struct is a small POD where adding a void* doubles its size disproportionately (rare for typical state structs which are already cache-line-sized)
- Consumer site doesn't have the high-layer types in scope — fix the include path or refactor consumer; void* without a known cast target is just hiding a missing dependency

### Cost:
- 1 field per resource per parent struct (8 bytes single void*, or 16×8=128 bytes per-core void* array)
- 1 cast at each consumer site (zero runtime cost — register reinterpret)
- 1 wire site at boot (per-core loop assignment)
- Type-safety obligation at consumer (cast must match boot-wire type; mismatch = silent UB)

### Win:
- Layer X header stays minimal (single void* declaration vs full typed include chain)
- Build separability preserved (CoreFrameworks builds standalone for testing / simpler configs)
- Template instantiation count unchanged
- No virtual dispatch (H1 served)
- Cluster placement flexibility (void* fits cold cluster naturally; boot-wired + occasional consumer read)
- Adding a new cross-layer reference = 1 void* field + 1 wire site + 1 cast site (no framework redesign)

---

## Reference implementations

### Application 1 (PRE-EXISTING; canonical Variant A reference) — `void* ensemble_handle`

- **File:** `CoreFrameworks/ControllerEventLoop.hpp:279`
- **Declaration:** `void* ensemble_handle;` field on `CoreContext<F>` (per-core context)
- **Established:** v5.10.0a.G.5 (multi-horizon ensemble path)
- **Boot wire:** `CoreFrameworks/EngineSharded.hpp:1061` (`state.cores[i].ensemble_handle = ezoo_ptr;` inside per-core init loop)
- **Consumer cast sites:** `ControllerEventLoop.hpp:1688-1689 + 1730-1731 + 2640` (slow-path body); `HotSwap.hpp:94 + 174` (hot-swap path); `ShardedSnapshot.hpp:681 + 713` (snapshot path)
- **Resource pointed-to:** `EnsembleModelZoo<F>*` (per-core ML ensemble state)
- **Nullable semantics:** `nullptr` = single-zoo path (no ensemble); guards at consumer sites check before cast

### Application 2 (NEW at `.F.4d` § F; canonical Variant B reference) — `void* ezoo_refs[MAX_EXECUTION_CORES]`

- **File:** `CoreFrameworks/OrderManager.hpp:624`
- **Declaration:** `void* ezoo_refs[MAX_EXECUTION_CORES] = {nullptr};` per-core array on `OrderManagerState<F>` (engine-wide singleton)
- **Established:** v5.15.5.F.4d Step 7 § F (Pattern 5 path consolidation for calib log emit)
- **Boot wire:** `CoreFrameworks/EngineSharded.hpp:1067` (`oms.ezoo_refs[i] = (void*)ezoo_ptr;` inside per-core init loop, alongside Application 1's per-core member wire)
- **Consumer cast site:** `OrderManager.hpp:707` (`real_on_exit_calibration` body; cast indexed by `o->core_id` aliased as `pslot`)
- **Resource pointed-to:** `EnsembleModelZoo<F>*` (per-core; same resource pool as Application 1)
- **Why TWO references to the same resource pool:** Application 1 lives on per-core CoreContext for slow-path access; Application 2 lives on engine-wide OmsState for drainer-side calib log emit. Both wire to same `ezoo_ptr` at same boot moment.

### Application 3 (NEW at `.F.4d` § F; canonical Variant B sister) — `const void* core_cfg_refs[MAX_EXECUTION_CORES]`

- **File:** `CoreFrameworks/OrderManager.hpp:625`
- **Declaration:** `const void* core_cfg_refs[MAX_EXECUTION_CORES] = {nullptr};` per-core array on `OrderManagerState<F>` (engine-wide singleton)
- **Established:** v5.15.5.F.4d Step 7 § F (Pattern 5 path consolidation, sister to ezoo_refs)
- **Boot wire:** `CoreFrameworks/EngineSharded.hpp:1068` (`oms.core_cfg_refs[i] = (const void*)&cfg.cores[i];`)
- **Consumer cast site:** `OrderManager.hpp:708` (`real_on_exit_calibration` body; cast to `const PerCoreCfg<F>*`)
- **Resource pointed-to:** `const PerCoreCfg<F>*` (per-core cfg slice owned by `ControllerConfig<F>`)
- **Const-correctness:** `const void*` declaration preserves the constness contract — consumer cannot mutate cfg through this pointer; matches `&cfg.cores[i]`'s const semantics.

### Future application catalog

Likely future cohort members:
- **Per-core regime classifier reference** on engine-wide state (when regime detector becomes per-core-with-engine-wide-aggregation)
- **Per-core strategy reference** on engine-wide state (when strategy selection moves to engine-wide dispatch table)
- **Per-core scaler reference** on engine-wide state (when feature scalers go per-core for cross-symbol experiments)

Each would be **1 void* field + 1 boot-wire site + 1 cast site per consumer** — mechanical against this reference doc.

---

## Lessons / gotchas

### § F architectural-correction lesson (codified at `.F.4d` ship close 2026-05-16)

**Always verify parent struct's ownership topology BEFORE writing sidecar examples.** Original `.F.4d` sidecar F.1 examples doc proposed `state.cores[i].oms.ezoo_ref` (Variant A shape; single void* on per-core member). Coding revealed `state.cores[i].oms` doesn't exist — OmsState is engine-wide singleton at `state.oms` (EngineSharded line 662). Correction: Variant B (per-core arrays `ezoo_refs[MAX_EXECUTION_CORES]` + `core_cfg_refs[MAX_EXECUTION_CORES]` on shared OmsState; indexed by `Order::core_id` at consumer site).

**Lesson generalizes to all sidecar examples that name a struct path** — `grep` target struct ownership before writing code samples that assume per-core-vs-engine-wide topology. Sister to `feedback_compaction_degrades_treat_handoffs_as_hints`: verify against actual code at HEAD before acting on claims.

This lesson lands in CLAUDE.local.md going-forward rule "Sub-plan sidecar files for substantial sections" — sidecars should be checked against actual struct ownership at planning time, not discovered to be wrong at coding time.

### Cluster placement discipline

void* fields are 8-byte aligned (16-byte slack with `alignas(64)` on parent struct). They fit naturally into **cold clusters** (boot-wired; read infrequently). Don't place void* arrays in HOT or PRODUCER WRITE clusters — they'd waste cache lines on data that's read once per consumer call.

For Variant B (per-core array): the entire 128-byte array (16 cores × 8 bytes) is typically read sequentially when a consumer iterates cores; cache-line packing is incidental (~2 cache lines per array) but acceptable since consumers don't iterate this array per fill.

### Type-safety obligation

void* + cast is a contract — the cast MUST match the boot-wire type. Mismatch = silent UB. Discipline:

1. **Adjacent comments on the field declaration name the expected typed cast** (see `OrderManager.hpp:624-625` for canonical comment shape)
2. **Wire site cast matches the field's declared expected type** (see `EngineSharded.hpp:1067-1068`)
3. **Consumer cast matches the wire site cast** — `static_cast` (not `reinterpret_cast`) because the type relationship is a single-pointer-erasure round-trip (void* ← T* ← void*)
4. **Nullable semantics documented** — `nullptr` is the canonical "not wired" value; consumer checks before cast (Application 1's pattern). Default-init at declaration enforces this (`= {nullptr}`).

### Nullable vs non-nullable per variant

- **Variant A (single void*):** nullptr-checking at consumer is mandatory; `nullptr` = "feature not active for this core" (e.g., single-zoo cores have `ensemble_handle = nullptr`)
- **Variant B (per-core array):** array slots default-init to nullptr; some slots may stay nullptr legitimately (cores without the feature); consumer checks per-slot before cast

### Per-core array size = MAX_EXECUTION_CORES (16)

`MAX_EXECUTION_CORES = 16` at `Limits.hpp:19`. The per-core array size is fixed at this cap; runtime active core count `<= 16` indexes into the array safely. Boot wire loop iterates `for (i = 0; i < cfg.execution_core_count; i++)` so cores past the active count stay nullptr-initialized.

### Composition with decision-time-data-binding for per-fill access

The pattern is for cross-layer state references (boot-wired; cast occasionally). For per-fill / per-tick access, use `decision-time-data-binding-pattern.md` Pattern 4 (pre-resolve onto in-flight Order/Position/Event carrier). Don't cast through a void* at hot-path budget — even 1 cycle for register reinterpret + 1 cache touch for the per-core array index is dispatch-cost in a tight loop.

Sister case: at `.F.4d` Pattern 5 sink-fn dispatch, the consumer calls `real_on_exit_calibration` from the slow-side drainer (not hot path) — void* + cast fits the latency budget there.

---

## Patterns NOT used here (and why)

### `std::any` / `std::variant`

Heap allocation (std::any) or type-tag matching (std::variant runtime cost). Not allowed on slow/hot/drainer paths per H1. Static void* + compile-time-known cast type is the codebase's idiom.

### CRTP base-class pattern

Considered. CRTP would inline the dispatch without virtual, BUT every consumer site would need to know the concrete derived type via template — same as Option B above. Defeats the layer-isolation goal.

### Untyped opaque handle struct (e.g., `struct EzooHandle { void* p; };`)

Considered. Adds a wrapper layer with no extra type safety (the void* member is still untyped at the wrapper level). Pure cosmetic; cast sites stay identical. Skipped to avoid unnecessary indirection in headers.

---

## Cross-references

- `decision-time-data-binding-pattern.md` — Pattern 4 (per-instance data flows with in-flight carrier; sister for per-fill access)
- `framework-composition-overview.md` — `.F.4d` cfg infra composition; this pattern is part of the substrate enabling layer-X-state to reference layer-Y typed objects without inflating layer-X
- `cache-layout-discipline-for-hot-side-structs.md` — void* fields fit cold cluster placement
- `meta-registry-pattern-for-codebase-registry-discipline.md` — per-core void* arrays indexed by `Order::core_id` mirror meta-registry's parent-child indexing scheme
- `pattern-codification-lifecycle.md` — Stage 2 DRAFT this pattern is currently at
- `DOCS/RECURRING_BUG_PATTERNS.md` — no codified class yet; if cross-layer crossings drift without this pattern's discipline, candidate Class 31 (cross-layer reference fragmentation)
- CLAUDE.md item 31 (Framework-driven extensibility — meta-principle)
- CLAUDE.md H1 (no virtual on hot path — served), H6 (cluster discipline — served), H17 (cfg struct independence — served)
- `feedback_compaction_degrades_treat_handoffs_as_hints` — sister discipline at planning-time (verify sidecar struct paths against actual code)

---

## Pattern lifecycle status (per `pattern-codification-lifecycle.md`)

- **Stage 1** (audit / problem identification): ✅ 3 applications observed at `.F.4d` ship close 2026-05-16 (ensemble_handle pre-existing + ezoo_refs + core_cfg_refs NEW)
- **Stage 2** (DESIGN_SPEC draft): ✅ THIS DOC (DRAFT v1.0; 2026-05-16, at `.F.4d.1` planning per Decision 1 lock)
- **Stage 3** (first reference): pending — would land on next cross-layer reference application after `.F.4d.1` (likely `.F.4e` GUI metadata or v5.16+ ML side parity ship)
- **Stage 4** (cohort migration): pending — when 4th+ application emerges, sweep existing cross-layer references for compliance
- **Stage 5** (CLAUDE.md item promotion): pending — when 5+ applications + 2+ variants validated, promote to CLAUDE.md item (likely in `framework-discipline` family alongside item 31)
- **Stage 6** (tooling enforcement): pending — `/dod-audit` scan signature could flag any cross-layer pointer field that's neither void* + cast NOR explicit forward-decl with documented include-chain rationale
- **Stage 7** (wider audit): pending — sweep codebase for cross-layer references that don't fit this pattern (legitimate forward-decl cases vs candidates for migration)

---

**End of spec.**
