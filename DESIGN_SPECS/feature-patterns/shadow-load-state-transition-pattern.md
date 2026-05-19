---
type: feature-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-12
tags: [framework-discipline, structural-fix, concurrency]
surface: [ml-inference, slow-path, training]
sister_specs: [per-horizon-barrier-blending-with-shadow-mode.md]
applies_at_skills: []
---

# Shadow-load state transition pattern (ACTIVE v1.0)

**Date opened:** 2026-05-12 (v5.15.4 plan-time)
**Date promoted to ACTIVE:** 2026-05-12 (v5.15.4 ship close)
**Status:** ACTIVE v1.0 — 2 production applications field-tested:
`tt::HotSwap_ShadowLoad_Ensemble<F>` + `tt::HotSwap_ShadowLoad_SingleZoo<F>`
in `CoreFrameworks/HotSwap.hpp`. PARITY-023 closed via this pattern.
**CLAUDE.md cross-ref candidate:** item 28 (promotion pending after
field-testing in paper-test phase; current criteria met: 2 applications,
DESIGN_SPECS doc, broad applicability for future state-transition needs).

---

## Why this pattern exists

Hot-swap and similar state-transition operations face a fundamental
correctness challenge: while the WRITER prepares new state (allocate,
load, validate), CONCURRENT READERS may still be using the old state.
Naive approaches (Free + Init + Load in-place; capture pointer + Free
+ revert pointer) fail because they either:

- Destroy reader-visible state mid-operation (torn reads)
- Capture pointers to soon-to-be-freed data (rollback impossible)
- Block readers (defeats lock-free design)

**Shadow-load is the correctness fix.** Allocate NEW state into
SEPARATE memory. Load + validate into the new allocation. ONLY after
validation succeeds, atomically swap the pointer. Free the old state
AFTER the swap (when no new reader can acquire it).

**On failure: Free the new (failed) allocation. Pre-swap state is
untouched; readers continue on validated existing state. No rollback
needed — there was never a moment when the active pointer was
invalid.**

---

## Pattern shape (canonical)

```cpp
template <int F>
int Shadow_Load_<Surface>(
    /* state container */& container,
    int target_idx,                   // which slot to swap (if multi-slot)
    const ControllerConfig<F>& cfg,
    const char* source,               // disk path or whatever
    /* additional args for load */) {

    // 1. Allocate NEW state (pre-swap state UNTOUCHED).
    //    Use aligned_alloc(64, sizeof(T)) if T has cache-line-aware
    //    members; plain malloc only for ≤8-byte-aligned structs.
    T* new_state = (T*)aligned_alloc(64, sizeof(T));  // or malloc; see alignment table
    if (!new_state) return -1;  // OOM
    T_Init(new_state);

    // 2. Load into new_state (filesystem I/O, parsing, whatever).
    //    NOT touching pre-swap state.
    int load_rc = T_LoadFromSource(new_state, cfg, source, /* args */);
    if (load_rc != 0) {
        // Validate FAILED — Free new_state; pre-swap state untouched.
        T_Free(new_state);
        free(new_state);
        return -2;  // load failed
    }

    // 3. Validate (any boot-time invariants, hash checks, etc.).
    if (cfg.<strict_mode>) {
        if (!T_Validate(new_state, cfg)) {
            T_Free(new_state);
            free(new_state);
            return -3;  // strict validate failed
        }
    }

    // 4. ATOMIC swap pointer.
    //    Readers from this instruction onwards see new_state.
    //    Readers BEFORE this instruction were reading pre-swap state.
    //    The swap is lock-free; readers never block.
    T* old_state = (T*)__atomic_exchange_n(
        &container.<slot>[target_idx],
        (void*)new_state,
        __ATOMIC_ACQ_REL);

    // 5. Free OLD state (now-detached pre-swap state).
    //    Safe if: writer = reader = same thread (single-owner case),
    //    OR readers have a grace period before this point.
    //    See "Memory reclamation" section below for RCU-style cases.
    if (old_state) {
        T_Free(old_state);
        free(old_state);
    }
    return 0;  // success; new state active
}
```

---

## Anti-patterns this replaces

### Anti-pattern 1: in-place mutation (the v5.10.0c "log-and-leave")

```cpp
// WRONG — reader sees half-freed state
T_Free(state.handle);          // <-- reader doing inference NOW sees freed memory
T_Init(state.handle);
T_LoadFromSource(state.handle, ...);  // <-- reader sees partial state
```

The state ptr DOESN'T CHANGE but the DATA at that ptr changes. Readers
mid-cycle see inconsistent state. Validation failure leaves state
half-initialized; no rollback possible.

### Anti-pattern 2: capture pointer + revert (the broken HotSwapSnapshot)

```cpp
// WRONG — captured pointer points to soon-to-be-freed memory
T* snap = state.handle;
T_Free(state.handle);           // <-- destroys data AT THE SAME ADDRESS snap points to
state.handle = new_handle;
if (validate_failed) {
    state.handle = snap;        // <-- snap points to freed memory; UB
}
```

Variations (capture struct fields, capture ref-count) all share the
flaw: capturing a pointer doesn't protect the data it points to from
being destroyed. The captured pointer is a stale reference.

### Anti-pattern 3: read-write lock around state

```cpp
// WRONG (for hot-path) — readers block during swap
rwlock_acquire_write(lock);     // <-- blocks readers
T_Free(state.handle);
state.handle = new_handle;
rwlock_release_write(lock);
```

Locks add reader-side overhead + are catastrophic on hot paths. v5.15.4
explicitly preserves lock-free reader-side access per CLAUDE.md item 5.

---

## When this pattern applies

**Required preconditions:**
- State is heap-allocated (pointer in a container; not embedded value)
- Container has a single-writer (or writer-serialized) ownership model
- Readers access via pointer dereference (so atomic-exchange of ptr suffices)
- Free of old state is safe at one of: (a) same-thread (writer=reader),
  (b) post-grace-period (RCU-style), (c) deferred-free queue

**Doesn't apply when:**
- State is embedded directly in container (no pointer to swap)
- Multiple writers can mutate the state pointer concurrently (need
  CAS retry loop, not exchange)
- Readers hold persistent references across writer's "grace period"
  (need read-side ref-counting or explicit reclamation)

---

## Memory reclamation strategies

The pattern's step 5 (Free old state) requires knowing WHEN no reader
can still hold a reference to old state. Three strategies:

### Strategy A: Single-owner (writer = reader, same thread)
**Used in:** v5.15.4 HotSwap (per-core slow-path thread is the sole
owner of `state.cores[c].ensemble_handle`).

Free-immediately-after-swap is safe because the writer thread IS the
reader thread. No concurrent reader can hold a reference.

### Strategy B: RCU grace period
**Future application:** mmap'd snapshot exposure where multiple viewer
processes read.

Writer waits for one full "grace period" (e.g., next slow-path cycle
across all cores) before freeing. Readers MUST not hold references
across cycle boundaries. Engine slow-path provides natural grace
period boundaries.

### Strategy C: Deferred-free queue
**Future application:** any case where grace period isn't naturally
bounded.

Writer pushes old state to a deferred-free queue. A separate cleanup
thread (or epoch-based reclamation) Frees entries after observing that
all readers have moved past the swap point.

---

## Cache alignment considerations

When state struct T has cache-line-sensitive members:

- **T should have `alignas(64)`** so internal alignas requests can be
  satisfied at all positions within the struct.
- **`aligned_alloc(64, sizeof(T))`** instead of `malloc(sizeof(T))` —
  malloc only guarantees 16-byte alignment on most systems.
- **Free with `free()` (aligned_alloc-allocated memory works with free
  per C11 standard).**

When state struct T is small (~tens of bytes) and not cache-aware:
- Plain `malloc` is fine
- Atomic exchange of pointer is single-instruction on x86_64 for
  aligned pointers (malloc guarantees 16-byte alignment which is
  sufficient for 8-byte pointer atomicity)

---

## Canonical applications

### v5.15.4 single-zoo hot-swap (CoreModelZoo)
- **Surface:** `CoreFrameworks/EngineSharded.hpp` ~line 2914 (single-zoo
  hot-swap dispatch)
- **State:** `state.cores[c].model_handle` (CoreModelZoo<F>*)
- **Reclamation:** Strategy A (per-core slow-path thread is sole owner)
- **Validation:** model_verify_strict check on loaded handles
- **Replaces:** in-place Free + Init + LoadFromDir at EngineSharded.hpp:2923-2924

### v5.15.4 ensemble hot-swap (EnsembleModelZoo)
- **Surface:** `CoreFrameworks/EngineSharded.hpp` ~line 2846 (ensemble
  hot-swap dispatch) + refactored `EnsembleHotSwap.hpp`
- **State:** `state.cores[c].ensemble_handle` (EnsembleModelZoo<F>*)
- **Reclamation:** Strategy A (per-core slow-path thread is sole owner)
- **Validation:** sibling handle validity + EnsembleModelZoo_PostLoadSetup checks
- **Replaces:** in-place Free + Init + LoadFromDir at EnsembleHotSwap.hpp:75-76

### Future candidates (TECH_DEBT triggers)
- **Scaler hot-swap** — separate from model swap; same shape
- **cfg hot-reload** — would need RCU grace period (Strategy B) for
  cross-thread cfg read consistency
- **Strategy hot-swap** — strategy assignment per-core could swap
  without restart

---

## CLAUDE.md cross-references

- **Item 5** (atomic seqlock patterns): shadow-load complements seqlock
  by handling state TRANSITIONS while seqlock handles state READS
- **Item 16** (reuse-audit): same pattern reusable across multiple
  hot-swap surfaces
- **Item 19** (structural fix preferred): closes the v5.10.0c
  "log-and-leave" semantic gap structurally; no ad-hoc per-surface
  rollback logic
- **Item 27** (struct padding determinism): aligned_alloc + struct
  alignas ensures heap allocations satisfy struct invariants

## DESIGN_SPECS cross-references

- `wire-format-byte-preservation-discipline.md` — sister concept for
  data-format transitions (versioning); shadow-load is the
  state-instance analog
- `per-snapshot-cluster-layout-pattern.md` — what state structs SHOULD
  look like for shadow-load to work cleanly (alignas + cluster
  discipline)
- `partner-core-bitmap-pattern.md` — adjacent topic of cross-core state
  publication; shadow-load complements

---

## Open design questions (resolve during v5.15.4 implementation)

- Strategy B (RCU grace period) — how to define grace period boundary
  for future mmap'd snapshot use case?
- Deferred-free queue (Strategy C) — needed for v5.16+ viewer
  reconnection? Or is single-owner sufficient for current uses?
- Per-core hot-swap parallelism — if N cores hot-swap simultaneously,
  do they share an aligned_alloc pool, or each malloc independently?
  (Probably independent for v5.15.4; revisit for high-frequency
  hot-swap workflows)

---

## Promotion criteria to CLAUDE.md item 28

After v5.15.4 ships:
- [ ] 2 applications field-tested (single-zoo + ensemble)
- [ ] Test suite verifies revert-on-failure preserves pre-swap state
- [ ] ASan + TSan clean under concurrent reader during swap
- [ ] Cross-binary replay determinism preserved across hot-swap

When all checked: promote to CLAUDE.md item 28 with this doc as
DESIGN_SPECS reference + canonical examples cited.
