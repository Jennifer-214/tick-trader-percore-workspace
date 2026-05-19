---
type: refactor-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-13
tags: [structural-fix, framework-discipline, data-oriented-design]
surface: [registry, bitmap-packed, hot-path]
sister_specs: [bitmap-flag-api.md, universal-registry-bitmap-dispatcher-pattern.md, composed-filter-mask-pattern.md, multi-bit-state-encoding-pattern.md]
applies_at_skills: []
---

# Registry-bitmap SET discipline (anti-pattern recognition + structural fixes)

**Established:** 2026-05-13 (v5.15.5.F.3 — surfaced during paper-test as 2 confirmed instances of the same anti-pattern class)
**Status:** ACTIVE
**Cross-references:**
- CLAUDE.md item 13 (X-macro registry standard pattern — substrate this discipline applies to)
- CLAUDE.md item 19 (structural fix preferred when bug class can recur — the WHY)
- CLAUDE.md item 20 (bitmap-flag-api via BITMAP_* macros — substrate)
- CLAUDE.md item 21 (AUTOPOPULATE companion macro — one structural fix template)
- `bitmap-flag-api.md` — substrate API for BITMAP_SET / IS_SET / CLR
- `autopopulate-pattern-for-production-caller-class.md` — one of the recommended structural fixes
- `x-macro-registry-with-presence-dispatch.md` — sister; presence dispatch is one consumer of bitmaps
- `structural-fix-preferred-decision-framework.md` — the meta-framework that motivates this codification
- First canonical reference applications: v5.15.5.F.3 `arms_with_barriers_mask` (missing SET site) + `drift_flags_at_load` (bypassed chokepoint)

---

## Problem statement

A registry of bit flags (e.g., `FOREACH_FAILURE_MODE`, `FOREACH_PER_ARM_FLAG`, `FOREACH_DRIFT_STATE`) provides:
- A bitmap field somewhere on a struct (`uint8_t / uint16_t / uint32_t / uint64_t flags`)
- Per-flag `MASK_<NAME>` constants
- Downstream consumers (GUI panels, `/readiness` checks, drainer gates, snapshot publishers) that **read** the bitmap + branch on per-bit state

The bits get written at **SET sites** (typically `BITMAP_SET(target->flags, MASK_<NAME>)`) on detected conditions. Each new code path that processes the underlying data potentially needs a SET call. Each new flag needs SET sites added wherever the corresponding condition can be detected.

**The failure mode:** if some code path that SHOULD set the bit doesn't, downstream consumers read the bit as zero → display "clean" / "no issue" / "no condition" — silently lying about reality.

This class is **insidious** because:
- The system functions correctly (the underlying data flow works)
- No test fails (nothing CHECKS that the bit-set path is correct)
- The GUI / `/readiness` displays look fine
- Operator trusts the display
- A real underlying condition is invisible until it bites (or until an alert ad-hoc bypass is added)

The class is **recurring** because:
- Every new loader / init / replay path is a new chance to forget the SET call
- Every new flag is a new SET site to remember at every consumer
- The data field + the bit are TWO separate writes — easy to miss the second

This spec catalogs the two anti-pattern shapes + structural fix templates (in preference order) + audit-detection signatures.

---

## The two anti-pattern shapes

### Shape A — Missing SET alongside the data write

A code site writes the **underlying data field** but forgets the companion `BITMAP_SET(mask)`. The data is correct + accessible; the bit that announces "this data exists / is valid / has condition X" stays zero.

```cpp
// ANTI-PATTERN — data field written; companion bit not set
for (int arm_idx = 0; arm_idx < N; arm_idx++) {
    if (STAMP_HAS(ezoo->buy_signal[arm_idx], label_params)) {
        ezoo->per_arm_barriers[arm_idx]      = (float)FPN_ToDouble(sr.label_tp_pct);
        ezoo->per_arm_barriers[arm_idx + 8]  = (float)FPN_ToDouble(sr.label_sl_pct);
        // ← MISSING: BITMAP_SET(ezoo->arms_with_barriers_mask, BITMAP_BIT_U8(arm_idx))
    }
}

// Downstream consumer reads arms_with_barriers_mask, sees all-zero,
// concludes "no arms have barriers" → barrier blending GATED OUT
// even though per_arm_barriers ARE populated.
```

**Detection signature**: `data_write_without_bit_set_companion` — a write to a per-element data field (`field[N]` or `nested.field`) without a corresponding BITMAP_SET to the parallel "mark" bit.

**Cost**: silent feature loss. Operator sees feature configured but not working; engineer has to forensics-trace down to the missing BITMAP_SET.

### Shape B — Chokepoint exists but alternate path bypasses it

A function (the "chokepoint") performs SET calls for a family of related bits. The chokepoint is called from SOME loader/init/replay paths. NEW paths added later bypass the chokepoint → bits never set for those paths.

```cpp
// CHOKEPOINT — sets drift_flags_at_load bits per FOREACH_ARCH_FIELD_DRIFT
int CoreModelZoo_TryLoadRole(handle, ...) {
    // ... verify stamp ...
    #define X(name, stamp_field, runtime_value, fail_mask) \
        if ((stamp_field) != (runtime_value)) { \
            BITMAP_SET(handle->drift_flags_at_load, fail_mask); \
        }
    FOREACH_ARCH_FIELD_DRIFT(X)
    #undef X
}

// LATER: ensemble multi-horizon load path added. Bypasses TryLoadRole.
int EnsembleModelZoo_LoadFromCfg(ezoo, ...) {
    // Loads multi-horizon models DIRECTLY without going through
    // CoreModelZoo_TryLoadRole → drift detection block never runs
    // → drift_flags_at_load stays zero → GUI Model Health: "clean"
    // while engine log shows actual stamp drift WARNs.
}
```

**Detection signature**: `chokepoint_bypass` — multiple loader / init / replay functions exist for the same data category; only SOME route through the bit-setting chokepoint.

**Cost**: feature/condition appears clean in observability while engine log says otherwise — operator confusion + potential real-world damage (e.g., live-trading against stale models).

### Both shapes share the same root cause

The **bit-set is a separate action from the data write/load**. Without architectural enforcement that they happen together, they drift apart:
- New developer adds new data path (shape B) — they don't know about the bitmap
- New developer adds new data field via the existing path (shape A) — they update the data field but not the bit

Both are forgetting-by-omission failures. Structural fixes eliminate forgetting.

---

## Structural fix templates (in preference order)

### Fix 1 — AUTOPOPULATE companion macro (preferred when registry-driven)

If the bitmap's bits correspond to entries in an X-macro registry, define an AUTOPOPULATE companion that walks the registry + emits BOTH the data write AND the BITMAP_SET in one expansion.

Per `autopopulate-pattern-for-production-caller-class.md` (CLAUDE.md item 21).

```cpp
// Registry: FOREACH_PER_ARM_BARRIER_FIELD walks each (arm, tp/sl, field)
// SHAPE: X(arm_idx, kind /* TP|SL */, stamp_field_expr)
#define FOREACH_PER_ARM_BARRIER_FIELD(X)                                      \
    /* arm 0 */                                                                 \
    X(0, TP, sr.label_tp_pct)                                                   \
    X(0, SL, sr.label_sl_pct)                                                   \
    /* arm 1 */                                                                 \
    X(1, TP, sr.label_tp_pct)                                                   \
    /* ... */

// AUTOPOPULATE: emit BOTH the data write + the bit set per registry row
#define PER_ARM_BARRIER_AUTOPOPULATE(_ezoo, _sr)                                \
    do {                                                                         \
        if ((_ezoo)->buy_signal[arm].active && STAMP_HAS((_sr), label_params)) { \
            (_ezoo)->per_arm_barriers[arm_idx + (KIND == SL ? 8 : 0)] =          \
                (float)FPN_ToDouble((_sr).label_##KIND##_pct);                   \
            BITMAP_SET((_ezoo)->arms_with_barriers_mask, BITMAP_BIT_U8(arm_idx));\
        }                                                                        \
    } while (0)
```

Adding a new arm or barrier field = one row in `FOREACH_PER_ARM_BARRIER_FIELD`; AUTOPOPULATE emits the SET call automatically. **Forgetting becomes impossible.**

### Fix 2 — Single chokepoint function (preferred when no registry)

When the data writes aren't registry-driven, extract the bit-setting logic into ONE function that ALL loader/init/replay paths route through.

```cpp
// CHOKEPOINT — owns ALL drift-detection bit setting for a model handle
void ModelHandle_DetectAndMarkDrift(ModelHandle* handle,
                                     const ModelStampResult& sr,
                                     const ControllerConfig<F>* cfg) {
    // FOREACH_ARCH_FIELD_DRIFT walk
    // cfg_binding_drift check
    // stamp_hmac_not_verified check
    // model_age_warn check
    // ... all the bit-setting logic in one place
}

// EVERY loader calls the chokepoint:
int CoreModelZoo_TryLoadRole(...) { ...; ModelHandle_DetectAndMarkDrift(handle, sr, cfg); }
int EnsembleModelZoo_LoadFromCfg(...) { ...; ModelHandle_DetectAndMarkDrift(handle, sr, cfg); }
int BacktestSharded_LoadModels(...) { ...; ModelHandle_DetectAndMarkDrift(handle, sr, cfg); }
```

When a new loader path appears, the developer hits the chokepoint immediately (the handle has no drift bits set until they call it). **Bypass becomes architecturally visible** (the GUI shows "clean" even when stamp mismatches → forces investigation → finds the missing chokepoint call).

### Fix 3 — Accessor wrapper (least preferred; relies on discipline)

Define a setter function that combines the data write + BITMAP_SET. Direct field writes get convention-banned. Less strong than 1 + 2 because direct writes are still syntactically possible (only convention enforces).

```cpp
inline void ezoo_set_per_arm_barriers(EnsembleModelZoo* ezoo, int arm_idx,
                                       float tp, float sl) {
    ezoo->per_arm_barriers[arm_idx]      = tp;
    ezoo->per_arm_barriers[arm_idx + 8]  = sl;
    BITMAP_SET(ezoo->arms_with_barriers_mask, BITMAP_BIT_U8(arm_idx));
}
```

**Use this when**:
- Registry doesn't fit the data shape (Fix 1 inapplicable)
- Multiple loader paths exist but their argument shapes differ enough that a single chokepoint function (Fix 2) is awkward
- Goal is just to make the "correct way" easier than the "wrong way"

---

## Audit detection signatures (for `/dod-audit`)

The `/dod-audit` skill walks DESIGN_SPECS at runtime. To enable auto-detection of new instances of this anti-pattern class, the skill checks these signatures:

### Signature 1 — Data field write without companion BITMAP_SET

Pattern: a write to `<struct>.<field>[N] = ...` or `<struct>.<nested>.<field> = ...` followed by ANY downstream code that branches on a BITMAP_IS_SET on the same struct, where no BITMAP_SET appears between the write site and the next end-of-function.

Symptom in code:
```cpp
// Write to data field
foo->per_X_data[idx] = ...;   // line N
// ... more code, no BITMAP_SET ...
return;  // function end without SET

// Elsewhere, consumer:
if (BITMAP_IS_SET(foo->per_X_mask, BITMAP_BIT_U8(idx))) {
    use(foo->per_X_data[idx]);   // never fires if SET was missed
}
```

Flag as **MISSED — registry-bitmap-set-discipline Shape A**.

### Signature 2 — BITMAP_SET in only some loader paths

Pattern: a `BITMAP_SET(<struct>.<flags>, MASK_X)` call exists in ONE function (`LoadA`). Another function (`LoadB`) writes to the same `<struct>` (e.g., via `LoadB_PostInit`) without going through `LoadA`'s SET site.

Heuristic: grep for all callers of `LoadB`; verify each path eventually reaches `LoadA` or sets `MASK_X` independently.

Flag as **MISSED — registry-bitmap-set-discipline Shape B**.

### Signature 3 — Bitmap with consumers but no SET site at all

Pattern: a bitmap field is read by consumers (BITMAP_IS_SET / BITMAP_ANY / branchless mask compute) but NO BITMAP_SET appears anywhere in the codebase for that bitmap.

The field is DEAD STATE — always zero → consumers never see the condition. May indicate a feature that was wired into consumers but never wired into the producer side.

Flag as **CRITICAL — registry-bitmap-set-discipline dead-bitmap**.

---

## Reference applications (v5.15.5.F.3)

### Shape A reference: `arms_with_barriers_mask` (CoreModelZoo.hpp:1683)

Pre-fix:
- Site at `~CoreModelZoo.hpp:1676-1682` copies `per_arm_barriers[arm_idx]` from stamp body
- Bit `arms_with_barriers_mask` bit-`arm_idx` is NEVER set
- Reader at `~StrategyParameters.hpp:1083` gates barrier blending on `BITMAP_IS_SET(ezoo->arms_with_barriers_mask, BITMAP_BIT_U8(i))` → all arms appear barrierless → blending silently disabled

Post-fix (per Fix 3 accessor wrapper, since the iteration is bounded + simple):
- Wrap the copy + mark in a single inline helper
- ALL future "copy barriers for arm" sites use the helper

### Shape B reference: `drift_flags_at_load` (CoreModelZoo.hpp:530-573 chokepoint vs ensemble bypass)

Pre-fix:
- Chokepoint `CoreModelZoo_TryLoadRole` (lines 530-573) sets drift_flags_at_load via `FOREACH_ARCH_FIELD_DRIFT` + cfg / HMAC / age checks
- Multi-horizon ensemble load path (`EnsembleModelZoo_LoadFromCfg` or its caller) handles loading via a different code path that bypasses the chokepoint → drift_flags_at_load stays 0 even on real drift
- Aggregator at `ShardedSnapshot.hpp:652-655` ORs handle->drift_flags_at_load into PerCoreSnap.failure_flags → also zero
- ML Status panel reads failure_flags → shows "Model Health: clean" while engine log emits `[held-out gate] WARN` for the same models

Post-fix (per Fix 2 chokepoint extraction):
- Extract drift-detection logic into `ModelHandle_DetectAndMarkDrift(handle, sr, cfg)` standalone function
- BOTH single-zoo + multi-horizon load paths invoke this function after stamp verify
- `/dod-audit` Signature 2 flags any future loader that doesn't call the chokepoint

---

## Patterns NOT covered here (and why)

### Multi-writer cross-thread atomic-bitmap discipline

When bitmaps are shared across threads (e.g., snapshot publish + slow-path mutation), `BITMAP_ATOMIC_*` variants apply. The SET-discipline class HERE is about WHETHER SET happens, not HOW (single-threaded vs atomic). Per `bitmap-flag-api.md` for atomic variants; this spec assumes the SET happens (correctly or not).

### Mask compute / branchless multi-flag dispatch

Whether to do `BITMAP_IS_SET` vs `BITMAP_ANY` vs branchless mask compute for the READ side is a different decision (see `latency-vs-cache-decision-framework.md` Rule 2). This spec is about the WRITE side discipline.

### Bit-pack for memory savings

The MOTIVATION for bitmaps is covered in `bitmap-flag-api.md`. This spec adds the DISCIPLINE for keeping their SET sites complete + correct.

---

## Promotion criteria + lifecycle

Per `pattern-codification-lifecycle.md`:

- **Stage 1 (audit)** — completed 2026-05-13 via `.F.3` paper-test audit; 2 confirmed instances + 1 downstream-consequence instance found
- **Stage 2 (this DESIGN_SPEC)** — completed 2026-05-13
- **Stage 3 (first reference)** — fixes shipping in `.F.3`: `arms_with_barriers_mask` (Fix 3 accessor) + `drift_flags_at_load` (Fix 2 chokepoint)
- **Stage 4 (subsequent applications)** — TBD as wider audit surfaces more instances
- **Stage 5 (CLAUDE.md item)** — promote on 2+ canonical applications shipped (meets criterion when `.F.3` lands)
- **Stage 6 (tooling enforcement)** — `/dod-audit` integration via the 3 signatures in `## Audit detection` section (this spec)
- **Stage 7 (wider audit)** — already partially run during `.F.3` discovery; opportunistic re-audits on future sub-sprints catch new bypasses

---

## Operator framing (Caramel, 2026-05-13)

> *"is this a bug that may be replicated where ever a registry and bit maps are used? should we do a scan to see right now while the failure mode is fresh in memory?"*

The scan identified TWO confirmed instances in 7 audited registry-bitmap pairs. The class IS recurring per `structural-fix-preferred-decision-framework.md`. Codification + structural fix templates + audit detection eliminate the class going forward.

> *"should we document it as an anti pattern similar to design specs?"*

This document IS the codification. Future contributors who write a new bitmap consumer learn the discipline from the spec; `/dod-audit` flags new instances; the structural fix templates eliminate the chance to forget.

---

**End of spec.**
