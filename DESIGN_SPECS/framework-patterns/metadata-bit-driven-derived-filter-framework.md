---
type: framework-pattern
stage: 4-cohort
version: 1.2
established: 2026-05-14
tags: [framework-discipline, structural-fix, pattern-codification]
surface: [registry, cfg-flow, wire-format]
sister_specs: [universal-cfg-field-registry-pattern.md, sidecar-override-pattern-for-registry-auto-flows.md, composed-filter-mask-pattern.md, cfg-derived-consumer-framework.md, framework-composition-overview.md, meta-registry-pattern-for-codebase-registry-discipline.md]
applies_at_skills: []
---

# Metadata-bit-driven derived filter framework

**Established:** 2026-05-14 (v5.15.5.F.4d planning); **v1.2 Path γ correction in progress at v5.15.5.F.4d.1.A planning 2026-05-16**
**Status:** **v1.2 Path γ correction in progress (2026-05-16)** — Stage 3 ACTIVE promotion at `.F.4d` ship close was ASPIRATIONAL; `.F.4d` reserved the STAMP_BOUND_CFG_DERIVED bit but NO derived filter framework was built. First ACTUAL canonical reference now sequenced at `.F.4d.1.A` per Path γ. **v1.0/v1.1 mechanism (Option B runtime walk + 3 macro variants `DERIVED_FILTER_DECLARE_GUI / WIRE_FORMAT / WIRE_FORMAT_TWO_SOURCE`) is SUPERSEDED by Option E (existing FOREACH_METADATA_BIT + cfg_compute_mask + CFG_FIELD_FOR_EACH_SET_BIT infrastructure at `CfgFieldRegistry.hpp:1020-1159`).** Option E is strictly better on every axis: compile-time mask (`.rodata` constant; zero runtime init) + branchless TZCNT iteration (vs runtime per-row branch) + already production-tested at `GUI/SettingsPanel.hpp:1100,1136` + the canonical mechanism per CLAUDE.md item 31 (comment at `CfgFieldRegistry.hpp:1020-1022` states the discipline explicitly). Code samples in this doc still show v1.0/v1.1 macro signatures + parallel walker mechanism — both superseded. See `plans/v5.15-live-readiness/plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` for full Path γ rationale + composition sister pattern (`composed-filter-mask-pattern.md`) + invariants helper extraction (`wire-format-canonical-body-invariants-helper.md`). Full doc cleanup at `.F.4d.1.A` ship close.
**Tags:** structural-fix, wire-format, registry-driven, framework-discipline; closes Class 21 at derived-filter surface + Class 18 at framework layer (via Option E reuse — Path γ) + Class 14 (spec drift correction); serves H9 + H16; v1.2 Path γ correction in progress; 0 production applications until `.F.4d.1.A` ships

**Cross-references:**
- Parent pattern: `x-macro-registry-with-presence-dispatch.md` § "Derived filter sister registry pattern" (extends + concretizes)
- Composes with: `wire-format-byte-preservation-discipline.md` § 5b (Layer 5b hash lock for wire-format variants)
- Composes with: `sidecar-override-pattern-for-registry-auto-flows.md` (custom-semantics dispatch on derived-filter consumers)
- Composes with: `pre-post-cfg-registry-split-for-emit-order-preservation.md` (alternative mechanism for emit-order-interleaved variants)
- Composes with: `autopopulate-pattern-for-production-caller-class.md` (production-caller side mechanical)
- Composes with: `meta-registry-pattern-for-codebase-registry-discipline.md` (`FOREACH_DERIVED_FILTER` is a Level-1 meta-registry)
- Closes: Class 21 (Multiple parallel descriptors) at the derived-filter surface
- Serves: H9 (wire-format byte preservation) + H16 (metadata bit ↔ derived filter cross-check; pending codification at `.F.4d` ship)
- CLAUDE.md item 31 (Framework-driven extensibility — meta-principle)

---

## Problem statement

When a parent registry (e.g., `FOREACH_CFG_FIELD`) accumulates **metadata bits** that drive cohort-style consumer behavior — STAMP_BOUND fields participate in HMAC chains; IS_SECRET fields get password-masking; HIDDEN_BY_DEFAULT fields collapse in GUI; etc. — each metadata bit needs a way to **enumerate the rows that have it set** for the consumer to walk.

Naive approach: write a separate `FOREACH_<COHORT>_CFG` registry per metadata bit, parallel to `FOREACH_CFG_FIELD`. **This is Class 21 anti-pattern** (multiple parallel descriptors): adding a new STAMP_BOUND field requires editing TWO registries; forgetting one causes drift.

Better approach: declare the parent registry as single source of truth; **derive** the cohort registry from it by filtering on the metadata bit. The derived walk produces the cohort's rows in registry order; consumers operate on the derived walk; the parent registry stays the only place new fields are added.

The recurring shape: **"registry has K metadata bits; for each bit, some consumer needs to walk only the bit-set rows."** Class 21 drift latent without structural framework; recurrence guaranteed (7+ planned applications: STAMP_BOUND, IS_SECRET, HIDDEN_BY_DEFAULT, DEPRECATED, RESTART_REQUIRED, SAFETY_CRITICAL, AFFECTS_STAMP_PARITY).

---

## Design space explored

### Option A — Preprocessor-time filter via metadata bit value

```cpp
#define FOREACH_STAMP_BOUND_CFG_DERIVED(X) \
    FOREACH_CFG_FIELD(EMIT_IF_STAMP_BOUND_##X)

#define EMIT_IF_STAMP_BOUND_X(kind, name, label, section, meta, ...) \
    /* somehow skip when (meta & STAMP_BOUND) == 0 */
```

**Rejected as primary path.** Preprocessor cannot evaluate `(meta & STAMP_BOUND) == 0` at expansion time when `meta` is an OR-expression like `PER_CORE_OK | STAMP_BOUND | SAFETY_CRITICAL`. Token-paste `EMIT_IF_STAMP_BOUND_DISPATCH_##meta` yields `EMIT_IF_STAMP_BOUND_DISPATCH_PER_CORE_OK | STAMP_BOUND | SAFETY_CRITICAL` which doesn't paste to a valid macro. Workable only if each row's metadata is a SINGLE TOKEN (drops bitmap-of-bits semantics).

### Option B — Runtime walk filter over `g_cfg_field_descriptors[]`

```cpp
// Boot/load-time consumer walks the parent registry array filtering on metadata bit:
for (size_t i = 0; i < FIELD_IDX_END; i++) {
    if ((g_cfg_field_descriptors[i].metadata_flags & STAMP_BOUND) == 0) continue;
    // ... per-row consumer code ...
}
```

**Acceptable; chosen as primary mechanism for v5.15.5.F.4d.** Runtime cost is ~80 fields × 1 cycle each = ~80ns at boot/load-time. No schema change; metadata_flags column already exists. The "walk the descriptor array filtering by bit" idiom is uniform across all derived-filter variants (GUI / wire-format / two-source); single mechanism scales to all 7+ future applications.

### Option C — Per-row STAMP_YES/NO token column (Y3 dispatch)

```cpp
// Add 13th tuple column with token (not integer):
X(KIND_DOUBLE, ridge_lambda, "Ridge λ", "ML", STAMP_BOUND_YES, ...)
X(KIND_DOUBLE, fee_floor_mult, "Fee Floor", "Trading", STAMP_BOUND_NO, ...)

#define EMIT_IF_STAMP_BOUND_YES(kind, name, ...) /* emit code */
#define EMIT_IF_STAMP_BOUND_NO(kind, name, ...)  /* skip */
#define EMIT_DERIVED_DISPATCH(kind, name, _l, _s, _m, _p, _t, _ss, _osm, _r, _rk, _li, stamp_token, ...) \
    EMIT_IF_STAMP_BOUND_##stamp_token(kind, name, ...)
```

**Rejected.** Doesn't scale to 7 metadata bits: each new bit (IS_SECRET / HIDDEN_BY_DEFAULT / etc.) requires its own per-row token column → tuple grows linearly with bit count. Schema bend per metadata bit. Anti-DRY (the metadata_flags column already encodes the same info via the bit).

### Option D — PRE/POST registry split per `pre-post-cfg-registry-split-for-emit-order-preservation.md`

```cpp
// Split FOREACH_CFG_FIELD into halves around STAMP_BOUND emit-order canonical position:
#define FOREACH_CFG_FIELD(X) \
    FOREACH_CFG_FIELD_PRE_STAMP_BOUND(X) \
    FOREACH_STAMP_BOUND_CFG_DERIVED(X) \
    FOREACH_CFG_FIELD_POST_STAMP_BOUND(X)
```

**Useful for emit-order interleaving but not the primary mechanism.** PRE/POST split is when SISTER registries must interleave at HMAC-locked emit order (canonical reference: `FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG` / `_POST_CFG`). For STAMP_BOUND derived filter at `.F.4d`, the consumer walks STAMP_BOUND-only rows — no sister-registry interleaving — so PRE/POST split is unnecessary overhead.

### Option E — Compile-time mask via existing FOREACH_METADATA_BIT X-macro infrastructure (added v1.2 Path γ correction 2026-05-16; CHOSEN)

The codebase ALREADY has at `CfgFieldRegistry.hpp:1020-1159` (since `.F.4c.3`, ~2 weeks before this spec was first drafted):

```cpp
// FOREACH_METADATA_BIT(X) — X-macro registry of metadata bits (line 1064-1075)
#define FOREACH_METADATA_BIT(X)                                            \
    X(restart_required,     RESTART_REQUIRED)                              \
    X(safety_critical,      SAFETY_CRITICAL)                               \
    X(deprecated,           DEPRECATED)                                    \
    X(stamp_bound,          STAMP_BOUND)                                   \
    X(hidden_by_default,    HIDDEN_BY_DEFAULT)                             \
    X(is_secret,            IS_SECRET)                                     \
    X(is_boot_only,         IS_BOOT_ONLY)                                  \
    X(affects_stamp_parity, AFFECTS_STAMP_PARITY)                          \
    X(log_value_forbidden,  LOG_VALUE_FORBIDDEN)                           \
    X(has_side_effect,      HAS_SIDE_EFFECT)                               \
    X(warn_on_clamp,        WARN_ON_CLAMP)
    /* NEW at .F.4d.1.A: X(stamp_bound_cfg_derived, STAMP_BOUND_CFG_DERIVED) */

// cfg_compute_mask<Bit>(arr) — constexpr; walks descriptor array at compile time;
// produces .rodata CfgMaskArray<N_WORDS> constant (line 1039)
template <uint16_t Bit, size_t N>
constexpr CfgMaskArray<(N + 63) / 64> cfg_compute_mask(const CfgFieldDescriptor (&arr)[N]) { ... }

// Per-registry per-bit precomputed mask arrays — X-macro generated (line 1079-1088)
#define X_GEN_GLOBAL_MASK(lname, BITNAME) \
    inline constexpr auto g_global_cfg_##lname##_mask = \
        cfg_compute_mask<CfgFieldDescriptor::BITNAME>(g_global_cfg_field_descriptors);
FOREACH_METADATA_BIT(X_GEN_GLOBAL_MASK)
#undef X_GEN_GLOBAL_MASK
/* Same pattern for X_GEN_PER_CORE_MASK */

// CFG_FIELD_FOR_EACH_SET_BIT — branchless TZCNT iteration (line 1150-1159)
//   for each set bit in mask: invoke body with idx_var bound to FIELD_IDX_*
//   Uses __builtin_ctzll (single TZCNT on Haswell+) + word &= word - 1
#define CFG_FIELD_FOR_EACH_SET_BIT(mask, idx_var, body) ...
```

Adding a new derived filter under Option E = **1 row in FOREACH_METADATA_BIT** + small consumer using CFG_FIELD_FOR_EACH_SET_BIT. Auto-generated masks live in `.rodata`. Live consumer at `GUI/SettingsPanel.hpp:1100,1136` (both global + per-node walkers in production GUI Settings panel).

The comment at `CfgFieldRegistry.hpp:1020-1022` literally states the framework discipline:
> "Per CLAUDE.md framework discipline (item 31): adding a new metadata bit = 1 row in FOREACH_METADATA_BIT below; mask arrays auto-generate for BOTH registries via X-macro instantiation pass."

**Strictly better than Option B on every axis:**

| Property | Option B (runtime walk) | **Option E (compile-time mask + TZCNT)** |
|---|---|---|
| Init cost | Runtime descriptor scan per consumer | **Zero** (`.rodata` constant) |
| Iteration cost | Per-row branch (mispredict variance) | **Branchless `__builtin_ctzll`** (single TZCNT instruction) |
| Production-tested | New (would be first canonical) | **Yes** — `SettingsPanel.hpp:1100,1136` |
| CI-tested | New | **Yes** — `tests/controller_test.cpp:1731-1747` (T12) |
| LOC at first canonical | ~80 LOC framework macros + ~30 LOC roster + ~50 LOC consumer | **~5 LOC** (1 FOREACH_METADATA_BIT row + small consumer) |
| Adding `.F.4e` 5 GUI metadata consumers | Thread through framework macro per consumer | 4 of 5 bits ALREADY enrolled at line 1065-1070; masks already auto-generated; consumer is `CFG_FIELD_FOR_EACH_SET_BIT(g_*_cfg_<name>_mask.words, idx, { gui_logic })` |
| Composition (when needed) | Re-implement per composed consumer | Use `composed-filter-mask-pattern.md` — combine masks via bitwise ops at compile time (3 existing canonicals: `render_mask` / `save_mask` / `cli_explain_mask`) |
| CLAUDE.md item 31 alignment | Violates ("don't duplicate the walker") | **Aligned** (the canonical way per `:1020-1022` comment) |

### Chosen: Option E (compile-time mask via FOREACH_METADATA_BIT) — Path γ correction (was Option B in v1.0/v1.1)

Under Option E, the "framework" IS the existing X-macro reduction at `CfgFieldRegistry.hpp:1020-1088`. New derived filters add **1 row** to `FOREACH_METADATA_BIT`; masks auto-generate; consumers use `CFG_FIELD_FOR_EACH_SET_BIT` for branchless iteration. Composition handled by `composed-filter-mask-pattern.md` (Stage 2 DRAFT 2026-05-16). Wire-format byte-preservation structural invariants extracted as reusable helper per `wire-format-canonical-body-invariants-helper.md` (Stage 2 DRAFT 2026-05-16).

The 3 macro variants from v1.0/v1.1 (`DERIVED_FILTER_DECLARE_GUI / WIRE_FORMAT / WIRE_FORMAT_TWO_SOURCE`) and the `DerivedFilterRoster.hpp` Level-1 meta-registry concept are **SUPERSEDED**. They were the wrong abstraction layer — the iteration mechanism doesn't need framework macros when the underlying infrastructure already provides it more cleanly.

If a future cohort genuinely needs a runtime-mutable mask (e.g., operator-toggleable filter), Option B can resurface as a 4th variant. Currently no use case projected.

---

## The pattern (concrete shape)

> **v1.1 revision banner (2026-05-16):** Variants 2 + 3 macro signatures **simplified at v5.15.5.F.4d.1 first-application time** per Caramel's "principle beats registry for ELIMINATING" rule. The original v1.0 macro signatures included `LOCKED_HASH_VAR` and `FIXTURE_PATH` parameters for Layer 5b hash-lock mechanism. **REVISED**: Layer 5b uses structural invariant tests (see `wire-format-byte-preservation-discipline.md` § 5b revised) rather than LOCKED-constant snapshot. Macro signatures now: `DERIVED_FILTER_DECLARE_WIRE_FORMAT(NAME, SOURCE_FOREACH, METADATA_BIT)` and `DERIVED_FILTER_DECLARE_WIRE_FORMAT_TWO_SOURCE(NAME, SOURCE_FOREACH, METADATA_BIT, BITMAP_SOURCE, BITMAP_FIELD)` — no LOCKED/FIXTURE columns. The framework macro auto-generates `NAME##_emit_canonical_body(buf, cap)` + `NAME##_run_generic_invariants()` runner that asserts I1-I5 (line count / format / locale-pin / row presence / canonical order). Domain-specific invariants live in consumer headers. **The code snippets below still show the v1.0 LOCKED-param signatures** — pending full doc cleanup at `.F.4d.1.A` ship close auto-write. For implementation, use the revised signatures + consult `2026-05-16-v5.15.5.F.4d.1.A-framework-infra-examples.md` sidecar for current canonical code.

### Three macro families covering 7 known applications

```cpp
// CoreFrameworks/DerivedFilterFramework.hpp
//
// Pattern: metadata-bit-driven-derived-filter-framework.md
// Composes: x-macro-registry-with-presence-dispatch.md + wire-format-byte-preservation-discipline.md § 5b

// ============================================================================
// VARIANT 1: GUI-only derived filter (cheap; no wire-format machinery)
// ============================================================================
// Use when: consumer walks the filtered rows for GUI presentation (collapse,
// badging, modal confirmation, password-masking) — NO HMAC chain, NO Layer 5b lock.
//
// Example: IS_SECRET → password-masking; HIDDEN_BY_DEFAULT → collapsed sections.
//
//   DERIVED_FILTER_DECLARE_GUI(NAME, SOURCE_FOREACH, METADATA_BIT)

#define DERIVED_FILTER_DECLARE_GUI(NAME, SOURCE_FOREACH, METADATA_BIT)            \
    inline void NAME##_walk_filtered_rows(                                        \
        const CfgFieldDescriptor* descriptors, size_t count,                      \
        void (*per_row_fn)(size_t idx, const CfgFieldDescriptor& desc, void* ctx),\
        void* ctx)                                                                \
    {                                                                             \
        for (size_t i = 0; i < count; i++) {                                      \
            if ((descriptors[i].metadata_flags & (METADATA_BIT)) == 0) continue;  \
            per_row_fn(i, descriptors[i], ctx);                                   \
        }                                                                         \
    }

// ============================================================================
// VARIANT 2: Wire-format derived filter (full Layer 5b + round-trip HMAC)
// ============================================================================
// Use when: consumer walks the filtered rows to produce wire-format bytes (HMAC
// chain). Mandates Layer 5b hash lock + round-trip HMAC test against committed
// fixture per wire-format-byte-preservation-discipline.md § 5b.
//
// Example: STAMP_BOUND → stamp body emit; AFFECTS_STAMP_PARITY → training cfg stamp.
//
//   DERIVED_FILTER_DECLARE_WIRE_FORMAT(NAME, SOURCE_FOREACH, METADATA_BIT,
//                                       LOCKED_HASH_VAR, FIXTURE_PATH)

#define DERIVED_FILTER_DECLARE_WIRE_FORMAT(NAME, SOURCE_FOREACH, METADATA_BIT,    \
                                            LOCKED_HASH_VAR, FIXTURE_PATH)        \
    DERIVED_FILTER_DECLARE_GUI(NAME, SOURCE_FOREACH, METADATA_BIT)                \
    /* Layer 5b hash-lock test scaffold: */                                       \
    inline uint64_t NAME##_compute_canonical_body_hash() {                        \
        char body[8192] = {0};                                                    \
        int pos = 0;                                                              \
        auto emit_row = [&](size_t idx, const CfgFieldDescriptor& d, void* /*ctx*/) {\
            pos += snprintf(body + pos, sizeof(body) - pos,                       \
                            "%s=", d.cfg_field_name);                             \
            /* tt::cfg_save_field with synthetic populate value per Kind */       \
            /* ... per Layer 5b methodology ... */                                \
            pos += snprintf(body + pos, sizeof(body) - pos, "\n");                \
        };                                                                        \
        NAME##_walk_filtered_rows(g_cfg_field_descriptors, FIELD_IDX_END,         \
                                   +emit_row, nullptr);                           \
        return fnv1a_64(body, pos);                                               \
    }

// ============================================================================
// VARIANT 3: Wire-format + bitmap-resident two-source variant
// ============================================================================
// Use when: some flagged fields are bitmap-resident (in a sister FOREACH_*_CFG_FLAG
// registry) rather than scalar in the parent registry. Aggregates from BOTH sources;
// emit_source dispatch per HANDLE_STAMP_EMIT_BITMAP_BIT pattern (v5.14.9.F.2):
// `(get_cfg) ? 1 : 0` ternary normalization preserves HMAC byte-equivalence across
// bool→int promotion variance.
//
// Example: STAMP_BOUND_CFG (14 fields in FOREACH_CFG_FIELD + 4 bitmap-bools in
// cfg.ml_cfg_flags).
//
//   DERIVED_FILTER_DECLARE_WIRE_FORMAT_TWO_SOURCE(NAME,
//                                                  SOURCE_FOREACH, METADATA_BIT,
//                                                  BITMAP_SOURCE, BITMAP_FIELD,
//                                                  LOCKED_HASH_VAR, FIXTURE_PATH)

// (Concrete macro definition extends Variant 2 with bitmap-source walking;
//  ~50 LOC; see .F.4d implementation for canonical form.)
```

### Layer 5b integration (for wire-format variants)

When `DERIVED_FILTER_DECLARE_WIRE_FORMAT(*)` is used, the consumer registers:

1. **Synthetic populate function** — populates every flagged field with deterministic test values
2. **Canonical body hash test** — `fnv1a_64` over the populated wire-format body output
3. **`LOCKED_<NAME>_HASH_<VERSION>` constant** — locked at ship time; test fires on accidental reorder
4. **Round-trip HMAC test** — parse committed v(N-1) fixture; re-emit via derived walk; verify HMAC byte-identical

On intentional change (new flagged field added): recompute hash → update LOCKED constant → CHANGELOG note. Forces deliberate decision.

### Y3 dispatch on the variant (optional roster-level meta)

When the codebase has 3+ derived filters, declare them in a Level-1 meta-registry per `meta-registry-pattern-for-codebase-registry-discipline.md`:

```cpp
#define FOREACH_DERIVED_FILTER(X) \
    X(STAMP_BOUND_CFG,       WIRE_FORMAT_TWO_SOURCE, FOREACH_CFG_FIELD, STAMP_BOUND, \
      FOREACH_ML_CFG_FLAG, ml_cfg_flags, LOCKED_STAMP_BOUND_DERIVED_HASH_V5_15_5_F4D, \
      "tests/fixtures/v5_14_stamp_canonical.bin") \
    X(IS_SECRET_CFG,         GUI_ONLY,               FOREACH_CFG_FIELD, IS_SECRET, _, _, _, _) \
    X(HIDDEN_BY_DEFAULT_CFG, GUI_ONLY,               FOREACH_CFG_FIELD, HIDDEN_BY_DEFAULT, _, _, _, _) \
    /* ... etc ... */

// Y3 dispatch macros expand each row to the appropriate DERIVED_FILTER_DECLARE_* invocation:
#define HANDLE_DERIVED_FILTER_GUI_ONLY(name, src, bit, ...) \
    DERIVED_FILTER_DECLARE_GUI(name, src, bit)
#define HANDLE_DERIVED_FILTER_WIRE_FORMAT(name, src, bit, _a, _b, hash, fixture) \
    DERIVED_FILTER_DECLARE_WIRE_FORMAT(name, src, bit, hash, fixture)
#define HANDLE_DERIVED_FILTER_WIRE_FORMAT_TWO_SOURCE(name, src, bit, bsrc, bfield, hash, fixture) \
    DERIVED_FILTER_DECLARE_WIRE_FORMAT_TWO_SOURCE(name, src, bit, bsrc, bfield, hash, fixture)

#define EMIT_DERIVED_FILTER(name, kind, ...) HANDLE_DERIVED_FILTER_##kind(name, __VA_ARGS__)
FOREACH_DERIVED_FILTER(EMIT_DERIVED_FILTER)
```

This roster-level Y3 dispatch closes the meta-Class-18 (adding a metadata bit but forgetting the derived filter) — CI test enumerates `MetadataFlag` values + asserts each has a row in `FOREACH_DERIVED_FILTER` OR a documented exemption. H16 invariant.

### AUTOPOPULATE companion for production-caller side

Each derived filter often pairs with consumer code that does per-row work (drift check, stamp-emit, GUI render). The AUTOPOPULATE pattern per `autopopulate-pattern-for-production-caller-class.md` extends:

```cpp
// CFG_DRIFT_AUTOPOPULATE walks the STAMP_BOUND derived filter + emits a drift check per row:
#define EMIT_CFG_DRIFT_CHECK(idx, desc) \
    do { \
        bool drifted = tt::cfg_drift_compare(stamp.<field>, cfg.<field>); \
        if (drifted) { BITMAP_SET(failure_flags, FAILURE_MASK_cfg_inference_drift); } \
    } while (0)

STAMP_BOUND_CFG_walk_filtered_rows(g_cfg_field_descriptors, FIELD_IDX_END,
                                    +emit_drift_check_lambda, &drift_ctx);
```

Production callers replace manual blocks (per-field if-chains) with one walker invocation. Class 18 extinct at consumer surface.

---

## Trade-offs + when to apply

### Apply when:
- Parent registry has metadata bits driving cohort-style consumer behavior
- 2+ future applications projected for the framework (recurrence foreseeable per CLAUDE.md item 19)
- Wire-format variant: cohort participates in HMAC chain (byte preservation load-bearing)
- GUI variant: cohort drives presentation (collapse, badging, modal)
- Two-source variant: some flagged fields live in a sister bitmap registry rather than scalar parent

### Skip when:
- Single cohort + no recurrence signal (one-off bug fix; direct walker)
- Cohort fields don't share consumer semantics (no shared shape)
- Schema can't accommodate the metadata bit (schema LOCKED + no headroom)

### Cost:
- Framework macros: ~150 LOC (3 variants × `DECLARE` + Layer 5b helpers + AUTOPOPULATE companion)
- Roster (`FOREACH_DERIVED_FILTER`) + Y3 dispatch: ~50 LOC
- Layer 5b hash-lock per wire-format application: ~30 LOC (synthetic populate + fnv1a_64 + LOCKED const + CI test)
- Round-trip HMAC test per wire-format application: ~50 LOC (fixture file + parse + re-emit + verify)
- AUTOPOPULATE consumer migration: ~80 LOC for 12+ consumer-site migration (replacing manual drift/emit/render code)

### Win:
- Adding new cohort = 1 row in `FOREACH_DERIVED_FILTER` + 1 metadata bit (within 6-bit headroom) + 1 row per cfg field gaining the bit
- Class 21 extinct at derived-filter surface (single source of truth; no parallel registries)
- Future cohort migrations are mechanical (~30 LOC per new cohort)
- Wire-format byte preservation enforced structurally (Layer 5b hash test fires on accidental reorder)

---

## Reference implementations

### v5.15.5.F.4d (FIRST canonical application — pending ship)

- `CoreFrameworks/DerivedFilterFramework.hpp` (framework macros + roster)
- `CoreFrameworks/StampBoundDerivedFilter.hpp` (first concrete application via WIRE_FORMAT_TWO_SOURCE variant):
  - Source registry: `FOREACH_CFG_FIELD` (filter on `STAMP_BOUND` metadata bit)
  - Bitmap source: `FOREACH_ML_CFG_FLAG` + `cfg.ml_cfg_flags` field (for 4 bitmap-resident bools)
  - Locked hash: `LOCKED_STAMP_BOUND_DERIVED_HASH_V5_15_5_F4D`
  - Fixture path: `tests/fixtures/v5_14_stamp_canonical.bin`
- Cohort: 14 fields (11 FPN<F> doubles + 3 ints) + 4 bitmap-resident bools
- 12+ consumer-site migration via `CFG_DRIFT_AUTOPOPULATE` + manual stamp emit body migration

### Future application catalog (7 surfaces planned)

| Application | Variant | Status | Notes |
|---|---|---|---|
| STAMP_BOUND_CFG | WIRE_FORMAT_TWO_SOURCE | `.F.4d` (first canonical) | HMAC chain; v5.14 fixture |
| AFFECTS_STAMP_PARITY (training) | WIRE_FORMAT | `v5.15.6.C` | Training cfg participates in model stamp |
| IS_SECRET_CFG | GUI_ONLY | `v5.15.6.B` | secrets.cfg integration + password masking |
| HIDDEN_BY_DEFAULT_CFG | GUI_ONLY | `.F.4e` | GUI collapse |
| DEPRECATED_CFG | GUI_ONLY | `.F.4e` | GUI strikethrough |
| RESTART_REQUIRED_CFG | GUI_ONLY | `.F.4e` | GUI badge |
| SAFETY_CRITICAL_CFG | GUI_ONLY | `.F.4e` | GUI modal confirmation |

Pattern lifecycle (per `pattern-codification-lifecycle.md`):
- Stage 2 (DRAFT) — this doc; pending ship
- Stage 3 (first reference) — `.F.4d` STAMP_BOUND_CFG application
- Stage 4 (cohort migration) — `.F.4e` adds 5 GUI-only applications (validates framework via real second-source applications)
- Stage 5 (CLAUDE.md item promotion) — after `.F.4e` ships with 6 active applications, item 31 promoted to full CLAUDE.md item status (currently codified as meta-principle in DESIGN_PHILOSOPHY § 1.5)

---

## Lessons / gotchas

### Mechanism choice is internal to the framework

Operator/contributor invokes `DERIVED_FILTER_DECLARE_*(NAME, SOURCE_FOREACH, METADATA_BIT, ...)`. The mechanism (runtime walk vs Y3 token vs PRE/POST split) is encapsulated. If future requirements need a different mechanism (e.g., emit-order interleaving), add a 4th variant without breaking the API surface.

### Bitmap-bool two-source variant requires `HANDLE_STAMP_EMIT_BITMAP_BIT`

The 4 STAMP_BOUND bitmap-resident bools in `cfg.ml_cfg_flags` need `(get_cfg) ? 1 : 0` ternary normalization for HMAC byte-equivalence (per v5.14.9.F.2 emit_source extension at `x-macro-registry-with-presence-dispatch.md:99-117`). Without the ternary, bool→int promotion may differ across compilers/architectures.

### Layer 5b first-application discipline

The first wire-format derived filter to ship validates the Layer 5b methodology:
- Synthetic populate must cover EVERY flagged field with a known value
- Canonical body emit must use locale-pinned formatting (per wire-format-byte-preservation-discipline.md § 5b Layer 2)
- LOCKED hash recomputed only on intentional change + CHANGELOG note

If Layer 5b doesn't fire on accidental reorder in production (subsequent ship), the framework's Layer 5b implementation is missing a path. Audit + extend.

### CI cross-check (H16 pending invariant)

Every metadata bit on `FOREACH_CFG_FIELD` must have either a derived filter in `FOREACH_DERIVED_FILTER` OR a documented "no-derived-filter" exemption with rationale. CI test:

```cpp
void test_metadata_bit_to_derived_filter_coverage() {
    // Forward: every bit set on any cfg row must have a corresponding row in
    // FOREACH_DERIVED_FILTER (or exemption list).
    uint16_t bits_used = 0;
    for (size_t i = 0; i < FIELD_IDX_END; i++) {
        bits_used |= g_cfg_field_descriptors[i].metadata_flags;
    }
    // Compare against FOREACH_DERIVED_FILTER coverage + exemption list
    // (PER_CORE_OK, IS_BOOT_ONLY, LOG_VALUE_FORBIDDEN are exempt — they're consumer-side
    //  metadata, not derived-filter sources)
}
```

### Sidecar override compatibility

When a derived filter's consumer has custom-semantics overrides for a minority of rows (e.g., 5 of 19 STAMP_BOUND rows need WARN_ALWAYS + CROSS_BINARY drift semantics instead of default REFUSE_STRICT + INFERENCE_CFG), use the sidecar override pattern per `sidecar-override-pattern-for-registry-auto-flows.md`. Sidecar is indexed by parent's FIELD_IDX; lookup is branchless O(1) array access. CI cross-check enforces every sidecar row maps to a derived-filter-included parent row.

---

## Patterns NOT used here (and why)

### Function-pointer dispatch table per derived filter

Considered: each derived filter = function pointer in a `static const DerivedFilter[]` table; walker iterates the table. Rejected — loses compile-time type info (the per-row Kind dispatch via tt:: is template-parameterized; runtime function-pointer table can't preserve T); loses Y3 dispatch elegance for variant selection.

### C++23 reflection

Would obviate this entire pattern (metadata-bit reflection → auto-derived consumer code). Not yet available; revisit at C++26 reflection landing.

---

## Cross-references

- `x-macro-registry-with-presence-dispatch.md` § "Derived filter sister registry pattern" — parent pattern; this spec concretizes the mechanism
- `wire-format-byte-preservation-discipline.md` § 5b — Layer 5b hash lock methodology (mandatory for wire-format variants)
- `sidecar-override-pattern-for-registry-auto-flows.md` — companion pattern for custom-semantics dispatch on derived-filter consumers
- `meta-registry-pattern-for-codebase-registry-discipline.md` — `FOREACH_DERIVED_FILTER` is a Level-1 meta-registry
- `pre-post-cfg-registry-split-for-emit-order-preservation.md` — alternative mechanism for emit-order-interleaved variants (not primary for `.F.4d`)
- `autopopulate-pattern-for-production-caller-class.md` — production-caller mechanical for consumer side
- `categorical-tag-applicability-pattern.md` — sister metadata-bit pattern (applies_to_*_cat masks instead of metadata_flags)
- `pattern-codification-lifecycle.md` — 7-stage lifecycle this pattern is currently at Stage 2 (DRAFT)
- `DOCS/DESIGN_PHILOSOPHY.md` § 1.5 (Framework discipline meta-principle) + § 7 (Structural-fix family)
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 21 (Multiple parallel descriptors — closed at derived-filter surface)
- CLAUDE.md item 31 (Framework-driven extensibility — meta-principle codification)
- H9 (wire-format byte preservation) + H16 (metadata bit ↔ derived filter — pending codification at `.F.4d` ship)

---

## Pattern lifecycle status (per `pattern-codification-lifecycle.md`)

- **Stage 1** (audit / problem identification): ✅ 2026-05-14 pre-coding audit gate caught Class 21 risk at STAMP_BOUND derived filter surface
- **Stage 2** (DESIGN_SPEC draft): ✅ THIS DOC (DRAFT v1.0; 2026-05-14)
- **Stage 3** (first reference): ✅ landed at v5.15.5.F.4d ship close 2026-05-16 (STAMP_BOUND_CFG_DERIVED first canonical application — bandit/thompson cohort + retroactive `.A.7` cohort + bandit_blend_ratio + 5-6 other inference_cfg fields)
- **Stage 4** (cohort migration): pending v5.15.5.F.4e ship (5 GUI-only applications validate framework via real second-source applications)
- **Stage 5** (CLAUDE.md item promotion): pending v5.15.5.F.4e ship close (CLAUDE.md item 31 elevation from meta-principle stub to full CLAUDE.md item with framework-discipline section)
- **Stage 6** (tooling enforcement): pending v5.15.6+ ship (CI cross-check tests for H16 invariant)
- **Stage 7** (wider audit): pending v5.16+ sprint (scan codebase for other parent-registry + metadata-bit cohort patterns to apply this framework)
