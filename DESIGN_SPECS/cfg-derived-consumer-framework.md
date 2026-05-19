# Cfg-derived consumer framework

**Established:** 2026-05-17 (v5.15.5.F.4d.1.B planning — codified as the master pattern doc for cfg-derived behavior; landed alongside `canonical-sister-extension-discipline.md` after Batch 1+2 pre-coding audit gate identified the 3-way triplet `FOREACH_CFG_DERIVED_INFERENCE_CFG × FOREACH_CFG_DRIFT_CHECK × FOREACH_STAMP_BOUND_CFG` consolidation opportunity)
**Status:** **Stage 3 ACTIVE v1.3** (v1.3 amends pre-coding at `v5.15.5.F.4d.1.B.3` Phase L v1.15 amendment 2026-05-18 — adds canonical "Extensibility test pattern for cohort consumers" section codifying X-macro test walker discipline. Pattern is REGISTRY-AGNOSTIC; applies to ANY cfg-derived consumer cohort. Stage 3 first canonical reference at Phase L's L4 extensibility test at `tests/controller_test.cpp` — replaces v5.14.1.B.3.E manual 17-field test block as Class 21 closure at TEST LAYER. Sister spec: `framework-driven-cli-binary-pattern.md` v1.1 § 5.2 (1st application). v1.2 → v1.3) (v1.2 added canonical "Action-parameterized meta-walker for cohort consumer template fns" section + clarified "Adding a new consumer concern" walker dichotomy at Phase L Step 1.6.5b. v1.1 → v1.2.) (v1.1 Stage 3 ACTIVE promoted at `.B.1` ship close 2026-05-17 = first canonical reference; full cohort activation at `.B.2` cohort migration.)
**Tags:** framework-discipline, master-pattern, cfg-infrastructure, registry-driven, future-easier; serves H15 + H17 + H18 + H19 + item 31; composes with metadata-bit-driven-derived-filter-framework + sidecar-override-pattern + tt:: dispatch via tt:: namespace + autopopulate-pattern-for-production-caller-class

**Cross-references:**
- Parent discipline: `canonical-sister-extension-discipline.md` (this is the 1st canonical application of that discipline)
- Composes with: `metadata-bit-driven-derived-filter-framework.md` v1.3+ (STAMP_BOUND_CFG_DERIVED metadata bit drives walker)
- Composes with: `sidecar-override-pattern-for-registry-auto-flows.md` (FOREACH_CFG_GATE is 1st canonical of gate-type sidecar)
- Composes with: `type-trait-dispatch-via-tt-namespace.md` (tt::cfg_emit_field + tt::cfg_populate_inf_field + tt::cfg_drift_compare type-trait dispatchers)
- Composes with: `autopopulate-pattern-for-production-caller-class.md` (3 new consumer macros sister to STAMP_CFG_AUTOPOPULATE + INFERENCE_CFG_AUTOPOPULATE)
- Sister: `framework-composition-overview.md` v1.2+ (composition narrative)
- Skill: `/anti-spaghetti` (codebase-wide audit catching parallel cfg-derived registries)
- CLAUDE.md item 31 (framework-driven extensibility meta-principle)
- H15 (every X-macro registry enrolled in FOREACH_REGISTRY)
- H17 (cfg struct fields auto-generated from FOREACH_CFG_FIELD)
- H18 (custom-semantics via sidecar override)
- H19 (meta-registry topology)

---

## Problem statement

Cfg fields have multiple derived behaviors that need to flow through wire-format / drift-check / inference-cfg populate / stamp body emit / parse paths. Historically (pre-`.B`), the codebase had MULTIPLE PARALLEL REGISTRIES encoding subsets of this behavior:

- `FOREACH_STAMP_BOUND_CFG` — cfg fields participating in stamp body
- `FOREACH_CFG_DERIVED_INFERENCE_CFG` — cfg → inference_cfg_* populate mapping (with inline gate_when)
- `FOREACH_CFG_DRIFT_CHECK` — cfg drift check rows
- `FOREACH_STAMP_BOUND_MODEL_CONST` (sister; different concern — model state vs cfg-derived; stays separate)

The CFG_DERIVED_INFERENCE_CFG × CFG_DRIFT_CHECK × STAMP_BOUND_CFG triplet has 93% row overlap (Batch 2 `/anti-spaghetti` audit confirmed). Each row exists in 2-3 registries with parallel encoding. Drift potential: bug fix in one registry's row doesn't auto-flow to siblings. The 5th BANDIT_THOMPSON field that β4 plan body MISSED was already in canonical CFG_DERIVED_INFERENCE_CFG — direct evidence of drift-induced incompleteness.

Naive fix: keep parallel registries; add CI to check row-overlap consistency. Mechanicalizes the wrong shape; entrenches Class 18 mirror anti-pattern at registry granularity.

Better fix: ONE master registry (`FOREACH_PER_CORE_CFG_FIELD` + `FOREACH_GLOBAL_CFG_FIELD` + `FOREACH_ML_CFG_FLAG` for bitmap-bool) with metadata bits; canonical sidecars for cohort-specific behavior; uniform consumer macros each walking master + applying appropriate filter. ONE source of truth; many consumer views; impossible to drift.

This pattern is the FUTURE-EASIER shape — adding a new cfg field = 1 row in master + (rare) 1 row in sidecar. Adding a new consumer concern = 1 new consumer macro walking master.

---

## The 4-axis taxonomy

Every cfg field with derived behavior has 4 orthogonal axes:

### Axis A — Master registry (where the row lives)

Already canonical at HEAD (`.F.4c.3`+):
- `FOREACH_PER_CORE_CFG_FIELD` — per-core cfg state (in `PerCoreCfg<F>`)
- `FOREACH_GLOBAL_CFG_FIELD` — global cfg state (in `ControllerConfig<F>`)
- `FOREACH_ML_CFG_FLAG` — bitmap-resident bool fields (in `cfg.ml_cfg_flags`)

**No new master registries should ever be added** for cfg fields. New scope = new metadata bit + extend existing master.

### Axis B — Metadata bits (what derived behavior applies)

Already canonical at HEAD (`.F.4c.3`+):
- `FOREACH_METADATA_BIT` — single source of truth for per-bit derived filter mask auto-generation
- Bits at HEAD: STAMP_BOUND + HIDDEN_BY_DEFAULT + IS_SECRET + IS_BOOT_ONLY + AFFECTS_STAMP_PARITY + LOG_VALUE_FORBIDDEN + HAS_SIDE_EFFECT + WARN_ON_CLAMP + RESTART_REQUIRED + SAFETY_CRITICAL + DEPRECATED + STAMP_BOUND_CFG_DERIVED (added `.A`)

**Adding a new behavior axis** = 1 row in `FOREACH_METADATA_BIT` + auto-generated per-bit + per-core sister masks via `cfg_compute_mask` at `CfgFieldRegistry.hpp:1064-1075`.

### Axis C — Gate sidecar (when the behavior applies per row)

NEW at `.B.1`:
- `FOREACH_CFG_GATE` — sparse sidecar mapping `row name → gate_when_expr`
- Sister to `FOREACH_DRIFT_OVERRIDE` (`.C`; severity-type override sidecar)

Per H18 (custom-semantics via sidecar): if a row's behavior differs from the default, an entry exists; if absent, default applies. Sparse → most rows don't need an entry.

**Default gates:**
- For drift check: `STAMP_HAS(*handle, inference_cfg)` (always-emit canonical Q3.G; drift check fires when stamp present)
- For populate: `1` (always populate; gate-time check at row content level when needed via `gate_when_expr`)

**Cohort gates** (custom per-cohort; sparse sidecar entries):
- Bandit/Thompson cohort → `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)`
- Ridge cohort → `BITMAP_ANY(cfg.ml_cfg_flags, MASK_ML_CFG_RIDGE_WITHIN_HORIZON | MASK_ML_CFG_RIDGE_ACROSS_HORIZONS)`
- Composite confidence cohort → `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_CONFIDENCE_COMPOSITE_ENABLED)`
- Soft-risk degradation cohort → `cfg.risk_degradation_curve != 0`

### Axis D — Value extraction (how to get the row's value from cfg)

Already canonical at HEAD (`.F.4c.3`+):
- `tt::` namespace type-trait dispatchers — `tt::cfg_save_field<T>`, `tt::cfg_parse_field<T>`
- Pattern: `if constexpr (is_FPN_v<T>) { ... } else if constexpr (std::is_integral_v<T>) { ... } else if constexpr (std::is_array_v<T>) { ... }` etc.

NEW at `.B.1`:
- `tt::cfg_emit_field<T>` — wire-format byte emit (sister to `tt::cfg_save_field<T>`; locale-pinned Layer 2 per `ModelInference.hpp:1697` precedent)
- `tt::cfg_populate_inf_field<T>` — populate `inf.*` field from `cfg.*`
- `tt::cfg_drift_compare<T>` — drift compare `stamp.*` vs `cfg.*` value

---

## End-state architecture

```
                    +-----------------------+
                    |  Master cfg registry  |
                    |  (per_core + global)  |
                    |  metadata_bits column |
                    +-----------+-----------+
                                |
                  +-------------+-------------+
                  |     FOREACH_METADATA_BIT  |
                  |  auto-gen per-bit masks   |
                  +-------------+-------------+
                                |
                                | walks via CFG_FIELD_FOR_EACH_SET_BIT
                                |
+-------------------+-----------+-----------+--------------------+
|                   |                       |                    |
v                   v                       v                    v
+-------------+ +-----------+ +-------------------+ +-----------------+
| INFERENCE_  | | STAMP_CFG | | DRIFT_CHECK_      | | (future         |
| CFG_POPU... | | _POPU...  | | AUTOPOPULATE      | |  consumer N)    |
+------+------+ +-----+-----+ +---------+---------+ +--------+--------+
       |              |                 |                    |
       |              |                 |                    |
       +--------------+-----------------+--------------------+
                                |
                                | per-row gate lookup
                                v
                    +-----------------------+
                    |  FOREACH_CFG_GATE     |
                    |  sparse sidecar       |
                    |  default if absent    |
                    +-----------------------+
                                |
                                | per-row value extract
                                v
                    +-----------------------+
                    |  tt:: type-trait      |
                    |  dispatch             |
                    +-----------------------+
```

---

## Adding a new cfg field with derived behavior (the discipline this framework produces)

**Step 1.** Add 1 row to `FOREACH_PER_CORE_CFG_FIELD` or `FOREACH_GLOBAL_CFG_FIELD` (master) with metadata_flags column set to relevant bits (e.g., `STAMP_BOUND | STAMP_BOUND_CFG_DERIVED`).

**Step 2 (rare).** If the field needs a non-default gate_when, add 1 row to `FOREACH_CFG_GATE` sparse sidecar with `X(<field_name>, <gate_when_expr>)`.

**Step 3 (rare).** If the field is bitmap-resident (KIND_BOOL → ml_cfg_flags), add to `FOREACH_ML_CFG_FLAG` instead (post-5→6 sig migration at `.B.2`).

**That's it.** All consumer macros (INFERENCE_CFG_POPULATE_FROM_DERIVED + STAMP_CFG_POPULATE_FROM_DERIVED + DRIFT_CHECK_AUTOPOPULATE + future consumers) automatically pick up the new row. No consumer code touches.

This is the "never worry about this again" shape for cfg fields with derived behavior. The framework is the discipline; adding rows can't drift because all consumers walk the same master.

---

## Adding a new consumer concern (the discipline this framework produces)

**Walker dichotomy decision** (v1.2 clarification): two canonical walker shapes exist; pick by consumer's value-extraction needs:

- **(W1) FOREACH-X-macro walker with `if constexpr (meta & BIT)` filter inside X-macro body** — use when consumer needs **compile-time field-name access** (`cfg.<name>`, `inf.<name>`, `handle.<name>` direct member access; tt:: type-trait dispatch with T deduced from destination field). This is the canonical shape for production value-extraction consumers (parser / emit / drift-check / populate). Class 23 avoidance: runtime offset access is forbidden per H13; compile-time name access requires X-macro walker semantics.
- **(W2) `CFG_FIELD_FOR_EACH_SET_BIT(g_*_cfg_<bit>_mask.words, idx, { ... })` precomputed-mask walker** — use when consumer needs only **runtime idx + descriptor access** (GUI render walk reading descriptor metadata; observability / diagnostic walks; synthetic-emit test cases). Branchless TZCNT iteration over `.rodata` mask; production-canonical at `GUI/SettingsPanel.hpp:1100,1136`.

Most cfg-derived consumer template fns are W1 (need compile-time name access for tt:: dispatch over `cfg.<name>`). Most GUI / observability consumers are W2.

---

### Single consumer concern — W1 shape (single-registry walker)

**Step 1.** Inside the consumer template fn, define X-macro with `if constexpr ((meta) & <BIT>) != 0` filter + per-row action body referencing `cfg.<name>` / `inf.<name>` etc.

**Step 2.** Invoke `FOREACH_<REGISTRY>(X_<consumer>)` to expand the walker.

**Step 3.** `#undef` the X-macro at end of fn body (scope hygiene).

**Step 4.** Per-row, look up gate via `FOREACH_CFG_GATE` sidecar (default if absent).

**Step 5.** Per-row, dispatch value extraction via `tt::` namespace (add new `tt::cfg_<verb>_field<T>` helper if a new value-extraction shape is needed).

**Step 6.** Enroll the new consumer macro in `FOREACH_REGISTRY` meta-registry per H15 + H19.

---

### Multi-consumer cohort sharing a registry family — action-parameterized meta-walker (v1.2 canonical)

When **≥2 sister consumer template fns walk the SAME registry cohort** with different per-row actions (e.g., populate / emit / drift / parse over the same N registries with same metadata-bit filter), the per-consumer-per-registry walker shape is **prone to sister-consumer drift**: each consumer must remember to add a walker for EVERY registry in the cohort; missing one causes silent stamp-binding / wire-emit / drift-check / parser gaps (Class 21 instance at consumer template fn level).

**Structural fix: action-parameterized meta-walker.** A meta-macro takes a BASE token + expands to N FOREACH invocations with token-pasted X-macro names. Each consumer defines N X-macros following the `BASE##_<SCOPE>` naming convention; meta-macro dispatches each FOREACH walker to its scope-specific X-macro.

**Drift impossibility by construction:**
- Consumer **cannot** silently skip a registry. The meta-macro expands to N walker invocations unconditionally.
- The N X-macros must exist by naming convention. Missing one = compile error at FOREACH expansion site (preprocessor fails on undefined identifier in macro body).
- The X-macros themselves can be no-op for legitimate skip-cases (consumer documents rationale via comment) — but the skip is EXPLICITLY VISIBLE.

#### Pattern shape (concrete)

```cpp
// In the cfg-derived-consumer header (e.g., MemHeaders/CfgGateRegistry.hpp):

// Meta-walker — single source of truth for the cohort's registry coverage.
// Consumer passes BASE token; meta-macro expands to N FOREACH invocations
// with token-pasted X-macro names (BASE##_<SCOPE>).
#define FOREACH_<COHORT>_COHORT(BASE_X)                  \
    FOREACH_<R1>(BASE_X##_<S1>)                          \
    FOREACH_<R2>(BASE_X##_<S2>)                          \
    /* ... one per registry in the cohort ... */         \
    FOREACH_<RN>(BASE_X##_<SN>)
```

#### Per-consumer X-macro family (function-scope for local context)

```cpp
template <unsigned F, typename DestT>
inline void <consumer>_<verb>(DestT& dst, const ControllerConfig<F>& cfg) {
    (void)dst; (void)cfg;

    #define X_<consumer>_<S1>(/* registry-R1 X-macro signature */) \
        if constexpr (((meta) & BIT) != 0) {                       \
            /* per-row action referencing cfg.name / dst.name */    \
        }
    /* ... one per registry in the cohort ... */
    #define X_<consumer>_<SN>(/* registry-RN X-macro signature */) \
        if constexpr (((meta) & BIT) != 0) {                       \
            /* per-row action */                                    \
        }

    FOREACH_<COHORT>_COHORT(X_<consumer>)

    #undef X_<consumer>_<S1>
    /* ... one #undef per X-macro for scope hygiene ... */
    #undef X_<consumer>_<SN>
}
```

#### Per-consumer X-macro family (file-scope for unconditional struct-gen)

Sister meta-walker for struct-field declarations (unconditional; no metadata filter):

```cpp
// File-scope X-macros (no consumer-local context needed for struct field decl):
#define _<STRUCT_PREFIX>_<S1>(/* registry-R1 X-macro signature */) \
    uint8_t has_##name; STORAGE_T name;
/* ... one per scope ... */

// Sister meta-walker invocation at struct scope:
#define <STRUCT>_DERIVED_FIELDS_AUTO_GEN() \
    FOREACH_<COHORT>_COHORT(_<STRUCT_PREFIX>)
```

The unconditional sibling (struct-gen) uses the SAME meta-walker as the filtered consumer template fns — new registry added to the cohort meta-walker auto-extends BOTH struct-gen AND all consumer template fns.

#### Recognition trigger

Recognition: ≥2 consumer template fns walking the same registry cohort with different per-row actions. Drift signal: one consumer walks N of K registries; sister walks M of K (M ≠ N) at HEAD — even if both started symmetric, incremental ship-by-ship registry additions tend to drift coverage.

#### When to use which shape

| Shape | When |
|---|---|
| W1 (FOREACH-X-macro walker; single FOREACH per consumer fn) | Single consumer, single registry; no sister consumers projected |
| W2 (CFG_FIELD_FOR_EACH_SET_BIT) | Runtime idx access sufficient (GUI / observability); no compile-time field-name access needed |
| **Action-parameterized meta-walker** | **≥2 sister consumer template fns over a shared registry cohort with compile-time field-name access requirement** |

#### Enrollment in FOREACH_REGISTRY

Meta-walker is itself an X-macro registry entry (no rows of its own; dispatches to underlying data registries). Enroll at H15 + H19 as Level 1 meta-walker with parent FOREACH_REGISTRY (sister to FOREACH_PER_CORE_DOMAIN_BITMAP pattern; meta-walker over derived cohort rather than over per-core domain bitmap members).

---

**That's it.** Adding a new consumer concern (e.g., a new GUI surface, new diagnostic output, new stamp variant) doesn't touch master registry rows. It doesn't touch existing consumer macros. It doesn't risk drift. Adding a NEW REGISTRY to the cohort = ONE row in the meta-walker; ALL N existing consumers + struct-gen auto-extend at next compile.

---

## Extensibility test pattern for cohort consumers (NEW v1.3)

The cfg-derived consumer framework has a complementary **test recurrence vector** that the v1.1/v1.2 sections don't address: the test code that validates per-field round-trip (e.g., "set ridge_lambda=0.15 + emit stamp + parse back + assert sr.ridge_lambda matches") historically enumerates each field explicitly. **That's Class 21 (multiple parallel descriptors) at the TEST LAYER** — the test enumeration is itself a parallel descriptor of the registry. Adding a new flagged row requires manual sync of the test enumeration; forgetting → silent runtime failure (e.g., new STORAGE_T edge case in `tt::cfg_emit_field<T>` that breaks round-trip; FPN precision issue at specific value ranges; missing has_* parsing).

**Concrete instance at HEAD pre-v1.3:** `tests/controller_test.cpp` v5.14.1.B.3.E section enumerates 17 flagged rows with explicit per-field assertions. Each new STAMP_BOUND_CFG_DERIVED-flagged row requires manual sync of this block.

**Structural fix codified v1.3:** X-macro walker validates round-trip per row.

### The pattern (concrete shape)

```cpp
// Helper: deterministic synthetic value per field (FNV-1a hash of field name → value).
// Coverage: every STORAGE_T variant the registry uses MUST have a branch; sister discipline
// to check_storage_t_coverage.py for tt::cfg_*_field<T>. Per /blindspot-scan v1.15 B6:
// include is_floating_point_v + is_array_v branches + dependent-type static_assert in else.
// Order matters: bool check BEFORE integral check (bool is_integral in C++; would match wrong branch).
template <typename T>
T synthetic_value_for_field(const char* field_name) {
    uint64_t h = tt::fnv1a_64(field_name, strlen(field_name));
    if constexpr (is_FPN_v<T>) {
        return FPN_FromDouble<64>((double)(h % 1000) / 1000.0 + 0.001);
    } else if constexpr (std::is_floating_point_v<T>) {
        return T((double)(h % 1000) / 1000.0 + 0.001);
    } else if constexpr (std::is_same_v<T, bool>) {
        return (h & 1) != 0;
    } else if constexpr (std::is_integral_v<T>) {
        return T((h % 100) + 1);
    } else if constexpr (std::is_array_v<T>) {
        T result{};
        const char* cs = "abcdefghijklmnopqrstuvwxyz0123456789";
        constexpr size_t cap = std::extent_v<T> - 1;
        for (size_t i = 0; i < cap; i++) result[i] = cs[(h >> (i * 4)) % 36];
        return result;
    } else {
        static_assert(!std::is_same_v<T, T>,
                      "extend synthetic_value_for_field<T> with branch for new STORAGE_T");
    }
}

// Helper: type-aware equality (FPN_ToDouble where applicable; bit-exact otherwise):
template <typename T>
bool values_equal_for_test(const T& a, const T& b) {
    if constexpr (is_FPN_v<T>) {
        return FPN_ToDouble(a) == FPN_ToDouble(b);
    } else {
        return a == b;
    }
}

// Extensibility test (X-macro walker):
SECTION("extensibility: <cohort name> round-trip per flagged row");
{
    ControllerConfig<64> cfg = ControllerConfig_Default<64>();

    // Walk all flagged rows; synthesize value per row; set cfg field.
    #define X_SYNTH_POPULATE(STORAGE_T, KIND_TOKEN, name, ...) \
        if constexpr (((meta) & CfgFieldDescriptor::<BIT>) != 0) { \
            cfg.name = synthetic_value_for_field<STORAGE_T>(#name); \
        }
    FOREACH_<REGISTRY>(X_SYNTH_POPULATE)
    #undef X_SYNTH_POPULATE

    // Set cohort gate bits so all flagged rows pass emit_when filter
    /* ... cfg.ml_cfg_flags = MASK_*; cfg.bandit_algorithm = N; etc. ... */

    // Run consumer (stamp emit + parse cycle, or whatever the consumer's round-trip is)
    /* ... */

    // Validate per-row round-trip byte-identity
    #define X_VALIDATE_ROUNDTRIP(STORAGE_T, KIND_TOKEN, name, ...) \
        if constexpr (((meta) & CfgFieldDescriptor::<BIT>) != 0) { \
            check("extensibility: " #name " has_*=1", result.has_##name == 1); \
            check("extensibility: " #name " round-trips byte-identical", \
                  values_equal_for_test(result.name, cfg.name)); \
        }
    FOREACH_<REGISTRY>(X_VALIDATE_ROUNDTRIP)
    #undef X_VALIDATE_ROUNDTRIP
}
```

### Why this is structural (not discipline)

- **Adding a new flagged row** = X-macro walker auto-includes it in the test
- **Adding a new STORAGE_T** = `synthetic_value_for_field<T>` static_asserts unreachable; compile-time catch
- **Test failure** = specific row's round-trip is broken; bisect via per-row check messages

The test ENFORCES the framework invariant "every flagged row round-trips byte-identical via emit→parse cycle." Adding ANY new flagged row that fails this invariant = test FAILS at CI; operator never sees the bug.

### When to apply

- **Apply** when a cfg-derived consumer cohort has ≥3 rows + value-round-trip is a load-bearing invariant (stamp body / wire format / cross-process serialization)
- **Apply** when manual enumeration of test code is itself a recurring drift surface (audit catches stale enumeration)
- **Skip** when consumer has ≤2 rows + low growth pressure (manual test fine; X-macro overhead exceeds benefit)
- **Skip** when round-trip is NOT a load-bearing invariant (consumer doesn't have parse-side complement; emit-only)

### Sister patterns + canonical applications

- **Stage 3 first canonical at v5.15.5.F.4d.1.B.3 Phase L** (`tests/controller_test.cpp` extensibility test for STAMP_BOUND_CFG_DERIVED cohort) — replaces v5.14.1.B.3.E manual 17-field block
- **Sister pattern at framework-driven-cli-binary-pattern.md v1.1 § 5.2** — same X-macro walker discipline applied at CLI binary's test layer
- **Future canonical:** FOREACH_STAMP_BOUND_MODEL_CONST cohort extensibility test (defer to next ship that warrants it; pattern applies registry-agnostic)

### Cost vs win

- **Cost:** ~50-80 LOC per cohort (one-time; X-macro walker + synthetic_value helpers + validation block)
- **Win:** Class 21 closure at TEST LAYER; adding new flagged row = automatic test coverage; STORAGE_T edge cases caught at compile time via static_assert; precision/serialization regressions caught at CI time

---

## Reference implementation (`.B.1` ship)

### Files created

- `MemHeaders/CfgGateRegistry.hpp` — `FOREACH_CFG_GATE(X)` sparse sidecar + 3 consumer macros
- `tick-trader-percore-workspace/DESIGN_SPECS/cfg-derived-consumer-framework.md` — THIS DOC

### Files migrated

- `ML_Headers/StampHelper.hpp:183` — `INFERENCE_CFG_AUTOPOPULATE` → `INFERENCE_CFG_POPULATE_FROM_DERIVED`
- `CoreFrameworks/MetaRegistry.hpp:99` — remove FOREACH_CFG_DERIVED_INFERENCE_CFG; add FOREACH_CFG_GATE + 3 consumer macros
- `tests/controller_test.cpp:24962-25047` — A.7 round-trip + gate-off semantics tests update

### Files NOT touched at `.B.1` (deferred to `.B.2`/`.B.3`)

- 24-row cohort source rows in master (cohort migration at `.B.2`)
- FOREACH_CFG_GATE sidecar entries (populated at `.B.2` per cohort)
- 4 ModelInference.hpp walker site migrations (`.B.2`)
- StampHelper.hpp:156 STAMP_CFG_AUTOPOPULATE migration (`.B.2`)
- 14 controller_test.cpp count-assertion migrations (`.B.3`)
- DELETE FOREACH_CFG_DERIVED_INFERENCE_CFG (`.B.3` after `.B.2` verifies)

### Behavior at `.B.1` close

- Walker iterates 0 rows (STAMP_BOUND_CFG_DERIVED bit flagged on 0 source rows at `.B.1`)
- All 3 consumer macros vacuous PASS for empty body
- HMAC chain byte preservation verified via `wire_format_invariants.hpp` helper from `.A` (vacuous PASS)
- Framework infrastructure ready for cohort exercise at `.B.2`

---

## Trade-offs + when to apply

### Apply when:

- New cfg field with stamp body / drift / wire-format / inference_cfg derived behavior
- New consumer concern over existing cfg fields (e.g., new GUI surface walking flagged cohort)
- Refactoring parallel registries with overlapping row name sets (per `canonical-sister-extension-discipline.md` audit findings)

### Skip when:

- Cfg field with no derived behavior (display-only / parse-only / runtime-only with no stamp participation)
- One-off consumer that doesn't recur (use direct field access)
- Concerns that genuinely warrant their own master registry (model state vs cfg-derived; HMAC body ordering)

### Cost:

- ~80-150 LOC framework infrastructure per derived-filter family (1-time cost at framework consolidation; e.g., this `.B.1`)
- ~5-15 LOC per consumer macro
- ~1 LOC per new cfg field (add metadata bit; rare gate sidecar row)

### Win:

- Adding new cfg field = 1 row in master; framework auto-flows behavior to all consumers
- Adding new consumer concern = 1 new macro; doesn't touch master or existing consumers
- ZERO drift potential between parallel structures (no parallel structures exist)
- Bug fix in one consumer applies to all rows automatically
- Compile-time verifiable (X-macro static_assert + H15/H17/H18/H19 CI checks)

---

## Lessons / gotchas

### Sidecar default semantics differ per consumer

- Drift check default: `STAMP_HAS(*handle, inference_cfg)` (drift fires when stamp present)
- Populate default: `1` (always populate; row content level gate via gate_when_expr if needed)
- Emit default: typically `1` (always-emit canonical Q3.G); cohort exceptions via sidecar

Different consumer macros encode default differently in their walker. This is OK; sidecar entries override the default uniformly.

### Locale pin is consumer-side

`tt::cfg_emit_field<T>` MUST honor Layer 2 locale-pin per `ModelInference.hpp:1697` precedent (`uselocale(LC_NUMERIC=C)` per-thread). I3 invariant in `wire_format_invariants.hpp` helper from `.A` catches drift.

### Sidecar registry is enrolled in meta-registry per H15 + H19

`FOREACH_CFG_GATE` row in `FOREACH_REGISTRY` at Level 1 with PARENT = `FOREACH_METADATA_BIT` (since the sidecar's purpose is to qualify rows that flag a specific metadata bit).

### `.B.1` walker is 0-row at ship close (and that's correct)

Don't confuse "vacuous PASS" tests with "tests not exercising the code". The walker mechanism itself is exercised; the rows being iterated are empty. `.B.2` populates the cohort; framework exercises non-empty thereafter.

### Multi-consumer pattern is the structural shape, not the API

Don't expose "Multi-consumer registry" as a public API. The discipline is: ONE master + many private consumer macros. External callers see only the consumer macros (e.g., `STAMP_CFG_POPULATE_FROM_DERIVED`); they don't see or touch master registry directly.

### Emit-side source-of-truth discipline: cfg vs caller-supplied inf (NEW v1.3)

When migrating a CONSUMER from caller-supplied input struct (e.g., `inf` populated by caller) to cfg-driven framework call, the **semantic source-of-truth shifts** in a way that's easy to miss:

- **Pre-migration (caller-inf-driven):** Stamp body captures whatever the CALLER populated in `inf` before invoking the emit. Tests can set `inf.ridge_lambda = 0.15` directly; stamp emits `0.15`.
- **Post-migration (cfg-driven):** Stamp body captures whatever's in `cfg` at emit time (via `populate_stamp_cfg_from_derived` walker). Tests must set `cfg.ridge_lambda = FPN_FromDouble<64>(0.15)`; stamp emits whatever framework's tt::cfg_emit_field renders from cfg.ridge_lambda.

**This is THE CORRECT semantic per cfg-derived-consumer framework discipline** — cfg IS the canonical source of truth for derived fields; consumers walk cfg, not inf. But existing tests that pre-populated inf as a shortcut become broken under migration.

**Migration discipline at consumer-switch ship:**

1. **Identify tests that set inf-fields directly** for migrated consumers. Grep: `inf.<name> = ...` for any field flagged STAMP_BOUND_CFG_DERIVED.
2. **Migrate test setup from inf → cfg** for each: replace `inf.<name> = value` with `cfg.<name> = value` (with FPN_FromDouble<64> wrap for FPN<F> types).
3. **Consolidate via extensibility test pattern** (§ above) — replace explicit per-field test enumeration with X-macro walker that auto-validates all flagged rows. Sister benefit: future flagged-row additions auto-include in extensibility test.

**Why this matters at coding time:** Step 1.6.4 (production canonical body emit migration at `ModelInference.hpp:~1817`) flips this semantic for the stamp body's cfg-derived fields. Tests that pre-set inf for flagged fields will silently pass (no compile error) but their assertions will check stale inf values vs cfg-at-emit-time values — false-positive test pass. Catch via:

- Pre-migration build: tests that fail on cfg/inf type mismatch after struct-gen (TYPE-SENSITIVE Pillar B8 issue — 27 instances at .B.3 WIP-checkpoint 6)
- Post-migration runtime: test failures where expected values diverge from cfg defaults
- Extensibility test pattern: replaces brittle per-field tests with registry-driven walker

**Sister patterns that follow this discipline:** `wire-format-byte-preservation-discipline.md` Layer 5b structural invariants (verifies emit shape independent of caller-supplied input).

---

## Pattern lifecycle (per `pattern-codification-lifecycle.md`)

- **Stage 1 (problem identification):** Path γ #2 caught at `.B` planning 2026-05-17 (3-way triplet overlap analysis surfaced 93% drift surface)
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-17 at `.B.1` planning)
- **Stage 3 (first canonical reference):** `.B.1` ship — `FOREACH_CFG_GATE` + 3 consumer macros land
- **Stage 4 (cohort migration / exercise):** `.B.2`/`.B.3` — 24-row cohort flags STAMP_BOUND_CFG_DERIVED; legacy registries deleted; framework exercised non-empty
- **Stage 5+ (CLAUDE.md item promotion):** when 3+ derived-filter consumer families ship over this framework AND the "1 row in master = 1 row everywhere" discipline becomes load-bearing for sprint planning

---

## Cross-references

- Parent discipline: `canonical-sister-extension-discipline.md` (this is the 1st canonical application)
- Composes: `metadata-bit-driven-derived-filter-framework.md` v1.3+ (provides STAMP_BOUND_CFG_DERIVED bit + walker primitive)
- Composes: `sidecar-override-pattern-for-registry-auto-flows.md` (provides FOREACH_CFG_GATE sidecar shape)
- Composes: `type-trait-dispatch-via-tt-namespace.md` (provides tt:: per-type dispatchers)
- Composes: `autopopulate-pattern-for-production-caller-class.md` (provides AUTOPOPULATE consumer macro shape)
- Sister: `framework-composition-overview.md` v1.2+ (composition narrative)
- Skill: `/anti-spaghetti` at `claude-skills/anti-spaghetti/SKILL.md` (catches future parallel cfg-derived registries)
- CLAUDE.md item 31 (framework-driven extensibility meta-principle)
- H15 + H17 + H18 + H19 (the structural invariants this framework serves)
- RECURRING_BUG_PATTERNS.md Class 14 / 18 / 21 (the classes this framework closes)
- Memory: `feedback_audit_canonical_sister_before_new_infra.md`
- Memory: `feedback_plans_cite_sister_registry_inspection.md`
- Memory: `project_anti_spaghetti_audit_cadence.md`

---

**End of pattern v1.0 DRAFT.** Stage 3 first reference lands at `.B.1` ship close.
