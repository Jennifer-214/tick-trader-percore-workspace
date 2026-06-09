---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-14
tags: [framework-discipline, data-oriented-design, branchless-discipline, structural-fix]
surface: [registry, bitmap-packed, hot-path, gui-thread]
sister_specs: [bitmap-flag-api.md, enum-mode-flags-bitmap-lookup-pattern.md, registry-bitmap-set-discipline.md, composed-filter-mask-pattern.md, x-macro-registry-with-presence-dispatch.md]
applies_at_skills: []
---

# Universal registry bitmap dispatcher pattern

**Established:** 2026-05-14 (v5.15.5.F.4c — first canonical application: cfg field GUI walker)
**Status:** DRAFT v1.0 (Stage 2 per `pattern-codification-lifecycle.md`; promotes to INVARIANT after `.F.4d` + `.F.4e` second + third applications)
**Tags:** framework-discipline, x-macro, bitmap-dispatch, type-trait, constexpr, structural-fix; closes parallel-array-indirection anti-pattern; serves H6 (cache-line discipline) + H7 (branchless dispatch) + framework-discipline meta-principle (CLAUDE.md item 31)
**Cross-references:**
- Composes: `x-macro-registry-with-presence-dispatch.md` (registry layer)
- Composes: `type-trait-dispatch-via-tt-namespace.md` (per-T dispatch layer; Class 23 prevention)
- Composes: `bitmap-flag-api.md` (1-bit specialization; `MASK_*` / `SHIFT_*` / `BITMAP_*` primitives)
- Composes: `multi-bit-state-encoding-pattern.md` (CLAUDE.md item 30 — INVARIANT)
- Sister to: `metadata-bit-driven-derived-filter-framework.md` (`.F.4d` framework — meta-registry layer ON TOP of this dispatcher)
- Cross-ref: `registry-tuple-as-single-source-of-truth.md` (registry source semantics)
- Cross-ref: CLAUDE.md H13 (Class 23 prevention — `tt::` dispatch); H14 (manual bit-packing only)
- Cross-ref: CLAUDE.md item 31 (framework-driven extensibility meta-principle)
- Cross-ref: DESIGN_PHILOSOPHY § 1.5 (Framework discipline); § 7 (Structural-fix family)

---

## Problem statement

The codebase has many "walk this registry, do something per row" surfaces — cfg parse, cfg save, cfg render, stamp emit, drift check, CLI dump, structured log emit, etc. The ad-hoc shape per surface is:

1. **Maintain a separate parallel structure** mirroring the registry (e.g., `field_defs[]` in SettingsPanel.hpp mirroring `FOREACH_CFG_FIELD`)
2. **Sync values** between the canonical registry/cfg and the parallel structure at load + commit time
3. **Per-Kind / per-bit filtering** via runtime conditional walks (`if (desc.metadata_flags & FILTER_BIT) { ... }`)
4. **Type dispatch** via Kind enum value or void* + offset reinterpret_cast (= Class 23 anti-shape)

This shape recurs across consumers because each consumer reinvents:
- Iteration discipline (linear walk over N entries)
- Per-row filter logic (check bit; branch)
- Type dispatch (Kind switch OR reinterpret_cast)
- Per-row action (parse / save / render / emit / dump)

Each reinvention drifts independently. Adding a new metadata bit means touching every consumer site to add the filter case. Adding a new Kind means touching every consumer site to add the dispatch case. The parallel structures become out-of-sync.

**The pattern:** consolidate around a single primitive — **per-metadata-bit precomputed bitmap masks over the registry + bitmap iteration + per-field function pointer tables for type-erased dispatch**. Each consumer is then a 4-line composition: compose the filter mask, iterate, dispatch per-row.

---

## The pattern (concrete shape)

### Layer 1 — Registry as single source of truth

```cpp
// X-macro registry over N items (cfg fields, OMS state flags, strategies, ...).
// Each row: (KIND_TOKEN, name, ...metadata..., type_info)
#define FOREACH_<NAME>(X)                  \
    X(KIND_TOKEN_1, item_1, ...metadata)   \
    X(KIND_TOKEN_2, item_2, ...metadata)   \
    ...

// Per-item index enum (sentinel pattern):
enum <NAME>Idx : uint16_t {
    FOREACH_<NAME>(X_GEN_IDX)
    <NAME>_IDX_END  // sentinel
};

// Descriptor array (constexpr → .rodata for compile-time mask computation):
inline constexpr <NAME>Descriptor g_<name>_descriptors[] = {
    FOREACH_<NAME>(X_GEN_DESCRIPTOR)
};
```

### Layer 2 — Per-metadata-bit bitmap masks

```cpp
// Mask sizing (rounds up to 64-bit word boundary):
static constexpr size_t <NAME>_MASK_WORDS = (<NAME>_IDX_END + 63) / 64;

// Wrapper struct for array-like access (avoids C-array return type awkwardness):
struct <Name>MaskArray {
    uint64_t words[<NAME>_MASK_WORDS];
    constexpr uint64_t operator[](size_t i) const { return words[i]; }
    constexpr uint64_t& operator[](size_t i)      { return words[i]; }
};

// FOREACH_<NAME>_METADATA_BIT(X) registry — adds new bit = 1 row + per-bit mask auto-generates:
#define FOREACH_<NAME>_METADATA_BIT(X) \
    X(per_core_ok,       PER_CORE_OK)   \
    X(deprecated,        DEPRECATED)    \
    X(is_boot_only,      IS_BOOT_ONLY)  \
    ...

// Compile-time mask computation (template-parameterized; one constexpr function per bit):
template <uint16_t Bit>
inline constexpr <Name>MaskArray <name>_compute_mask() {
    <Name>MaskArray result = {};
    for (size_t i = 0; i < <NAME>_IDX_END; i++) {
        if (g_<name>_descriptors[i].metadata_flags & Bit) {
            result.words[i / 64] |= (1ULL << (i % 64));
        }
    }
    return result;
}

// Per-bit mask declarations (X-macro generated; constexpr → .rodata):
#define X_GEN_MASK(lname, BITNAME) \
    inline constexpr <Name>MaskArray g_<name>_##lname##_mask = \
        <name>_compute_mask<<Name>Descriptor::BITNAME>();
FOREACH_<NAME>_METADATA_BIT(X_GEN_MASK)
#undef X_GEN_MASK
```

### Layer 3 — Bitmap iteration primitives

```cpp
// Branchless next-set-bit iteration (uses __builtin_ctzll → single TZCNT on Haswell+).
#define <NAME>_FOR_EACH_SET_BIT(mask, idx_var, body)               \
    for (size_t _w = 0; _w < <NAME>_MASK_WORDS; _w++) {            \
        uint64_t _word = (mask)[_w];                               \
        while (_word) {                                            \
            const size_t _bit = static_cast<size_t>(__builtin_ctzll(_word)); \
            const size_t idx_var = _w * 64 + _bit;                 \
            do { body; } while (0);                                \
            _word &= _word - 1; /* branchless next-bit-clear */    \
        }                                                          \
    }

// Popcount over mask (constexpr; folds to immediate at compile time for literal masks):
inline constexpr size_t <name>_count(const <Name>MaskArray& mask) {
    size_t n = 0;
    for (size_t i = 0; i < <NAME>_MASK_WORDS; i++) {
        n += static_cast<size_t>(__builtin_popcountll(mask.words[i]));
    }
    return n;
}

// Filter composition (cheap bitwise ops; constexpr):
inline constexpr <Name>MaskArray <name>_compose_filter(<some logic>) {
    <Name>MaskArray out = {};
    for (size_t i = 0; i < <NAME>_MASK_WORDS; i++) {
        out.words[i] = ~(g_<name>_boot_only_mask[i] | g_<name>_hidden_by_default_mask[i]);
        // OR: out.words[i] = g_<name>_deprecated_mask[i] & ~g_<name>_per_core_ok_mask[i];
        // ... any bitwise composition the consumer needs.
    }
    return out;
}
```

### Layer 4 — Per-row function pointer table for type-erased dispatch

```cpp
// Per-row static render/save/parse function — X-macro generates one per row.
// Each function takes generic (root_ref, descriptor) args; instantiates tt::<verb>_field<T>
// with T deduced from the row's typed cfg field access (Barrier 2 per Class 23 prevention).
using <name>_render_fn_t = bool (*)(Root&, const <Name>Descriptor&);

#define X_GEN_RENDER_FN(KIND_TOKEN, name, ...) \
    static bool <name>_render_##name(Root& root, const <Name>Descriptor& desc) { \
        return tt::<name>_render_field(root.name, desc); \
    }
FOREACH_<NAME>(X_GEN_RENDER_FN)
#undef X_GEN_RENDER_FN

// Function pointer table (constexpr → .rodata; compile-time addressed):
#define X_GEN_RENDER_PTR(KIND_TOKEN, name, ...) &<name>_render_##name,
inline constexpr <name>_render_fn_t g_<name>_render_fns[<NAME>_IDX_END] = {
    FOREACH_<NAME>(X_GEN_RENDER_PTR)
};
#undef X_GEN_RENDER_PTR
```

### Layer 5 — Consumer site (4-line composition)

```cpp
// GUI render consumer:
<Name>MaskArray render_mask = <name>_compose_filter(/* GUI filter logic */);
<NAME>_FOR_EACH_SET_BIT(render_mask, idx, {
    g_<name>_render_fns[idx](root, g_<name>_descriptors[idx]);
});

// CLI list consumer:
<NAME>_FOR_EACH_SET_BIT(g_<name>_deprecated_mask, idx, {
    fprintf(stdout, "%s (deprecated)\n", g_<name>_descriptors[idx].name);
});

// Stats consumer (one-shot popcount; no iteration):
size_t n_deprecated = <name>_count(g_<name>_deprecated_mask);
fprintf(stdout, "engine uses %zu deprecated fields\n", n_deprecated);
```

---

## When to use this pattern

✅ Registry of N items (typically 10-1000) where consumers walk + filter + dispatch
✅ Multiple consumer surfaces over the same registry (cfg has parse/save/render/CLI/stamp/drift — bitmap framework consolidates)
✅ Per-metadata-bit filtering recurs across consumers
✅ Type-erased dispatch needed (per-row T varies)
✅ Stats / introspection ("how many items match filter X?") are useful operationally
✅ Forward extension expected (new metadata bits / new consumer surfaces)

## When NOT to use this pattern

❌ Registry has <10 items (manual switch is simpler)
❌ Single consumer surface (the framework overhead doesn't amortize)
❌ Filtering is purely runtime-dynamic (compile-time bitmap precompute doesn't help)
❌ Items have heterogeneous structure (no single descriptor type — use heterogeneous-registry-pattern instead)

---

## Worked example: FOREACH_CFG_FIELD bitmap dispatcher

First canonical application at v5.15.5.F.4c. Pre-Option-2:

- Parallel-array indirection in SettingsPanel.hpp (`s->float_vals[i]` mirrors cfg)
- Sync logic at load + commit time
- Per-Kind dispatch in render loop via `CfgFieldType` enum + `if (fd->type == CFG_FLOAT) ...`
- Adding new Kind = touch render loop + load path + commit path

Post-Option-2:

- Direct `ControllerConfig<F>&` access in SettingsPanel API
- Bitmap walker `CFG_FIELD_FOR_EACH_SET_BIT(g_cfg_render_mask, idx, { g_cfg_render_fns[idx](cfg, g_cfg_field_descriptors[idx]); })`
- Per-Kind dispatch handled by `tt::cfg_render_field<T>` via type-trait branches (compile-time)
- Adding new Kind = extend `tt::cfg_render_field<T>` with one new `if constexpr` branch (single site)
- Adding new metadata bit = 1 row in `FOREACH_METADATA_BIT` (mask + iteration helpers auto-generate)
- Adding new consumer surface = 4-line composition (compose filter, iterate, dispatch)
- field_defs[] + parallel arrays + sync logic delete (TECH_DEBT-063 progresses 80% → 90%)

---

## Composition with `.F.4d` derived filter framework

`.F.4d` adds `FOREACH_DERIVED_FILTER` — a meta-registry of NAMED filters declared declaratively:

```cpp
#define FOREACH_DERIVED_FILTER(X) \
    X(stamp_bound_derived, STAMP_BOUND, identity)        \
    X(per_core_override,    PER_CORE_OK, identity)       \
    X(boot_only_derived,    IS_BOOT_ONLY, identity)      \
    X(gui_renderable,       /* composed */, NOT(IS_BOOT_ONLY | HIDDEN_BY_DEFAULT)) \
    ...
```

Each row generates a NAMED composed mask + iteration helper (`FOREACH_STAMP_BOUND_CFG_FIELD(X)` etc.). The IMPLEMENTATION of each filter is the bitmap mask + iteration primitive from THIS pattern.

`.F.4d` layers names + composition declarations on top of the dispatcher primitive `.F.4c` ships. Together they form the complete framework.

---

## GUI ↔ engine thread isolation (load-bearing rule)

**Never pointer-share state across the GUI thread and the HP/SP threads.** The bitmap dispatcher enables clean per-thread typed mirrors of cfg state:

- GUI thread owns a `ControllerConfig<F> gui_engine_cfg` instance (its mirror of `engine.cfg`)
- Engine HP/SP threads own a separate `ControllerConfig<F> engine_cfg` instance (loaded at boot + on reload signal)
- GUI edits modify `gui_engine_cfg` via `tt::cfg_render_field<T>` + persist to file via `cfg_write_field` per edit
- Engine reloads from file on `reload_flag` signal; the GUI never touches engine memory directly

This is the canonical channel: **file is the source of truth; reload-signal is the IPC primitive**. Aligns with H3 (no mutex/condition_variable/sleep_for/rwlock anywhere — the synchronization primitives that "share state across threads" designs rely on are forbidden in this codebase, so the file-based separation falls out naturally). Aligns with H8 (hot-path latency budget — GUI mutations of running state would force the hot path to acquire locks; forbidden by H3 + H8).

The pattern generalizes to all subsystems with their own thread:
- **GUI** owns its mirror; engine owns the running state; file is the channel
- **Training thread** owns its training state; engine owns inference state; stamp file is the channel
- **Backtest thread** owns backtest cfg; engine owns live cfg; backtest.cfg is the channel
- **Future structured-log emitter** owns its emit cadence cfg; engine owns hot-path cadence; cfg file or atomic seqlock-snapshot is the channel (per CLAUDE.md design)

**Anti-pattern (forbidden):** `void GUI_RenderSettings(ControllerConfig<F>& engine_cfg_running)` — GUI edits running engine state. This couples GUI thread to hot path, requires synchronization (H3 forbidden), and breaks the file-is-source-of-truth invariant. Reviewers MUST reject this shape.

---

## Caveats

1. **Descriptor array MUST be constexpr** for compile-time mask computation. If members aren't trivially constexpr-init (e.g., contain function pointers initialized at runtime, or string concatenation requiring runtime), masks fall back to static-init via runtime function call (still works; slight boot cost).

2. **Function pointer table is constexpr** for `.rodata` placement. Static member functions and free functions are constexpr-friendly; lambda captures are not.

3. **Bitmap iteration order matches `<NAME>_IDX_*` enum order.** Section-grouping consumers need to ensure descriptors are emitted in section order OR track section transitions during iteration.

4. **Mask bits beyond `<NAME>_IDX_END`** in the last word must be cleared before iteration (otherwise `__builtin_ctzll` returns bit position past end → out-of-bounds descriptor read). The composed-filter helpers in this pattern apply the mask automatically; bespoke compositions must remember.

5. **Filter mutation post-init is FORBIDDEN.** Masks are `inline constexpr` → `.rodata` → OS-enforced read-only. Runtime mutation would segfault. Use a separate uint64_t array if runtime-mutable filters are needed (rare; usually composition + bitwise ops are sufficient).

6. **Wire-format byte preservation (H9):** if a bitmap is part of an HMAC-signed body OR memcmp comparison context, mask iteration order MUST be deterministic — controlled by `<NAME>_IDX_*` enum order. Renumbering enum values changes mask bit positions → breaks HMAC chain.

---

## Implementation checklist (per new application)

- [ ] Registry exists as X-macro with constexpr descriptor array
- [ ] Per-metadata-bit FOREACH_<NAME>_METADATA_BIT registry declared
- [ ] CFG_MASK_WORDS computed from <NAME>_IDX_END
- [ ] CfgMaskArray wrapper struct declared
- [ ] compute_mask<Bit>() constexpr function added
- [ ] Per-bit mask declarations via X-macro
- [ ] FOR_EACH_SET_BIT iteration macro
- [ ] count() popcount helper
- [ ] Per-row function pointer table per consumer surface (render/save/parse/etc.)
- [ ] Composed filter helpers for canonical consumers (render, save, etc.)
- [ ] Bitmap overflow guard: `static_assert(highest_bit < (1u << SIZE_BITS))` per `bitmap-overflow-protection-discipline.md`
- [ ] Last-word valid-bits mask in composed filters
- [ ] Unit test: per-bit mask matches descriptor walk (sanity)
- [ ] Unit test: popcount matches descriptor walk count (sanity)
- [ ] Unit test: bitmap iteration covers exactly the matching indices (no false positives, no false negatives)

---

## Applied at

### First application: cfg field GUI walker (v5.15.5.F.4c) — Stage 2 → Stage 3 in progress

**Framework primitive — LANDED at v5.15.5.F.4c WIP checkpoint 2026-05-14:**

- `CoreFrameworks/CfgFieldRegistry.hpp:297+` — `[BITMAP DISPATCHER FRAMEWORK — v5.15.5.F.4c]` section
  - `CFG_MASK_WORDS` constant (sized from `FIELD_IDX_END`)
  - `CfgMaskArray` wrapper struct (operator[] for natural array-like access)
  - `cfg_compute_mask<uint16_t Bit>()` constexpr template
  - `FOREACH_METADATA_BIT(X)` X-macro registry with 12 rows (PER_CORE_OK, RESTART_REQUIRED, SAFETY_CRITICAL, DEPRECATED, STAMP_BOUND, HIDDEN_BY_DEFAULT, IS_SECRET, IS_BOOT_ONLY, AFFECTS_STAMP_PARITY, LOG_VALUE_FORBIDDEN, HAS_SIDE_EFFECT, WARN_ON_CLAMP)
  - 12 `inline constexpr CfgMaskArray g_cfg_<lname>_mask` arrays (compile-time computed; `.rodata`)
  - `CFG_FIELD_FOR_EACH_SET_BIT(mask, idx, body)` iteration macro (branchless `__builtin_ctzll`)
  - `cfg_field_count(mask)` constexpr popcount helper
  - 5 composed view masks: `g_cfg_render_mask`, `g_cfg_save_mask`, `g_cfg_stamp_emit_mask`, `g_cfg_cli_explain_mask`, `g_cfg_per_core_override_mask` (all `inline constexpr`)
  - `g_cfg_field_descriptors[]` at line 280 promoted `inline const` → `inline constexpr` to enable compile-time mask computation

- `CoreFrameworks/CfgFieldDispatch.hpp` — `tt::` dispatch quartet
  - `tt::cfg_parse_field<T>` at line ~47 (Step 0.5 / Step 1.5 — INT_ENUM string-token + WARN_ON_CLAMP emission)
  - `tt::cfg_save_field<T>` at line ~104 (locale-pinned save)
  - `tt::cfg_assign_field<T>` NEW at `.F.4c` (descriptor default → typed field)
  - `tt::cfg_diff_field<T>` NEW at `.F.4c` (current vs default → bool)

- `GUI/SettingsPanel.hpp` — consumer layer (PARTIAL — Stage 3 first-application in progress)
  - `tt::cfg_render_field<T>` at line ~57 (Step 0.5 landed)
  - `CfgRenderTable<F>::fns[FIELD_IDX_END]` at line ~150 (per-field function pointer table; constexpr; `.rodata`)
  - **Pending Stage 3 completion (Option 2 GUI refactor)**:
    - SettingsPanel API restructure to take `ControllerConfig<F>&` + `PerCoreOverrides&` directly
    - Bitmap walker replacing `EMIT_CFG_FIELD_DEF_FROM_REGISTRY` field_defs[] auto-extender
    - Section-grouping (track `desc.section` transitions during bitmap iteration)
    - Per-node override path (consume `g_cfg_per_core_override_mask`)
    - Reset-to-defaults (consume `tt::cfg_assign_field<T>`)
    - Modified detection (consume `tt::cfg_diff_field<T>`)
    - KIND_STRING/_FILE_PATH bridge (parallel-array layer survives for these until `.F.4e`)
    - Delete old `EMIT_CFG_FIELD_DEF_FROM_REGISTRY` walker + `field_defs[]` entries for scalar Kinds

- `ControllerConfig.hpp:1896+` — parser walker
  - `EMIT_CFG_PARSER_CASE` with `HAS_SIDE_EFFECT` bit check (registry walker skips parse for side-effect rows)

**Parallel-array drift class** (recurring drift surface this pattern closes):

Pre-Option-2, SettingsPanel maintained `s->float_vals[i]`, `s->bool_vals[i]`, `s->path_vals[i]` parallel arrays mirroring cfg field values. Required:
- Load-time sync (cfg file → parallel arrays)
- GUI edits to parallel arrays (not direct cfg)
- Commit-time sync (parallel arrays → cfg)
- Per-Kind dispatch via `CfgFieldType` enum (CFG_FLOAT/INT/BOOL/PATH) in render loop

The bitmap dispatcher eliminates this indirection: SettingsPanel takes `ControllerConfig<F>&` directly; render fn table per row dispatches via type-trait (`is_fp_binary_v<T>` / etc.); bitmap walker iterates set bits in composed render mask. Single source of truth (`ControllerConfig<F>` itself) — no sync required.

### Future applications

**Cfg-side:**
- **Stamp emit** (`.F.4d`): uses `g_cfg_stamp_bound_mask` + per-row emit fn table; replaces FOREACH_STAMP_BOUND_CFG manual emit
- **Drift check** (`.F.4d`): uses STAMP_BOUND derived filter; replaces CfgDriftCheckRegistry manual walker
- **CLI subcommands** (`.F.4e` per TECH_DEBT-066): consumes per-bit masks for `--list-cfg --filter=<bit>`; popcount stats for `--status --json`
- **Structured log emit** (TECH_DEBT-065/067): per-node emit walker uses composed filter for "which fields to emit per snapshot"
- **`.F.4d` `FOREACH_DERIVED_FILTER`** (meta-registry): layers named filters ON TOP of this dispatcher primitive
- **`.F.4j` `FOREACH_BACKTEST_CFG_FIELD`** (via `lives_in_struct = STRUCT_BACKTEST_CFG`): backtest panel renders via per-struct walker
- **v5.15.6.A `FOREACH_CONTROLLER_CFG_FIELD`** (via `lives_in_struct = STRUCT_CONTROLLER_CFG`): controller settings tab
- **v5.15.6.B `FOREACH_SECRETS_CFG_FIELD`** (via `lives_in_struct = STRUCT_SECRETS_CFG`): secrets tab with IS_SECRET bit gating
- **v5.15.6.C `FOREACH_TRAINING_CFG_FIELD`** (via `lives_in_struct = STRUCT_TRAINING_CFG`): training tab

**ML-side (separate registries; same pattern):**

The dispatcher pattern is registry-agnostic. Future ML-side applications consuming this primitive:

- **`FOREACH_FEATURE`** (ML features registry; ~50-100 rows projected): per-feature metadata (LIVE_AVAILABLE vs TRAINING_ONLY, AVX_FRIENDLY, DEPENDS_ON_ROLLING_STATS, etc.); consumers: GUI feature picker (filter by LIVE_AVAILABLE), training-time feature selector (TRAINING_ONLY), CLI `engine --list-features`, AVX-512 vectorization gate (AVX_FRIENDLY)
- **`FOREACH_STRATEGY`** (strategies registry; ~5-10 rows): per-strategy metadata (REGIME_APPLICABLE_RANGING/TRENDING/VOLATILE/MILD_TREND, ML_DRIVEN vs STATIC_RULE, etc.); consumers: strategy dispatch (regime + applicability filter), GUI strategy picker, categorical applicability per cfg field via `applies_to_strategy_cat` mask
- **`FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG/_POST_CFG`** (model constants in stamp; ~10-20 rows): consolidate at `.F.4d` via bitmap framework; replaces bespoke emit_when + emit_source dispatch
- **`FOREACH_CFG_DERIVED_INFERENCE_CFG`** (cfg → inference_cfg derived state; ~10 rows): same shape
- **TECH_DEBT-068 ML enum registries** (ml_backend / regime_model_backend / confidence_ic_variant / csv_sort_check_mode / reconcile_mode / ensemble_blend_mode): once these get X-macro registries (per TECH_DEBT-068), each can be a bitmap dispatcher application — but at 3-5 entries each, manual switch may still win until the registry grows past ~10 items

**Heuristic for when the pattern pays off:**
- Registry size ≥10 rows
- ≥2 consumer surfaces with different filter needs
- Per-row metadata exists (bits OR categorical enum values)
- Forward extension expected (new rows / new bits / new consumers)

Below ~10 items, the framework overhead doesn't amortize; manual switch is simpler.

---

**End of spec.** Updates as future applications validate the pattern; promotes to INVARIANT after 3 canonical applications (cfg GUI walker + .F.4d stamp emit + .F.4e CLI consumer).
