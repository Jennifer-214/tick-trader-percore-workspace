# Heterogeneous registry pattern — scope column vs domain split

**Established:** 2026-05-10 (v5.14.9.F sprint, pre-field-test draft)
**Status:** DRAFT v0.2 (pre-field-test; expanded 2026-05-10 post-/dod-audit with Y3 dispatch canon + cache-layout discipline + concrete worked example for stamp-binding integration)
**Cross-references:**
- `bitmap-flag-api.md` — bit-packed flag storage (BITMAP_*)
- `x-macro-registry-with-presence-dispatch.md` — base X-macro pattern + presence column
- `slow-path-gate-registry-pattern.md` — SCOPE COLUMN reference implementation
- `autopopulate-pattern-for-production-caller-class.md` — companion AUTOPOPULATE pattern
- `pre-post-cfg-registry-split-for-emit-order-preservation.md` — wire-format byte preservation
- `wire-format-byte-preservation-discipline.md` — sister concern to PRE/POST split
- `structural-fix-preferred-decision-framework.md` — meta-pattern: when does this pattern apply
- CLAUDE.md item 13 (X-macro for multi-site additions)
- CLAUDE.md item 19 (structural fix preferred)
- CLAUDE.md item 20 (BITMAP_* API)

---

## Problem statement

X-macro registries are the standard pattern for "1 row per entry → all consumers auto-flow" (CLAUDE.md item 13). But registries grow heterogeneous: not all entries share the same read cadence, mutation pattern, scope, or downstream consumer set.

Two approaches handle heterogeneity, with different trade-offs:

**SCOPE COLUMN (Y3 dispatch):** keep entries in ONE registry; add a column indicating which dispatch handler applies. Generation logic varies per axis value via token-paste dispatch (`HANDLE_GEN_<MARKER>` macros). Y3 is the canonical implementation mechanism.

**DOMAIN SPLIT (multi-registry):** split entries across N registries by axis value. Each registry has homogeneous entries; auto-flow infrastructure (struct gen, AUTOPOPULATE, parser, GUI, per-core override, slow-path cache) extends to all registries uniformly.

Choosing the wrong shape leads to:
- Column when split is correct → cluttered registry; per-entry generation logic differs unnecessarily; consumers must walk one registry but conditionally consume different subsets
- Split when column is correct → over-fragmented; pattern repeated N times; consumers must walk N registries; canonical wire-format ordering broken

This doc is the decision framework + concrete shapes for both, plus a discussion of when neither shape applies, plus the cache-layout discipline for DOMAIN SPLIT bitmap fields on parent structs.

---

## Design space

### When SCOPE COLUMN wins

Entries DIFFER in generation logic but COHERE as a registry — same domain, same caller surface, ordered. Examples:

- **FOREACH_STAMP_BOUND_MODEL_CONST**: ALL entries belong to the canonical stamp body wire format. Some are RUNTIME-INCLUDE (kept on ModelHandle); some are SKIP_HANDLE (parser-only, not propagated to runtime). Wire format order is HMAC-locked. → COLUMN (presence).
- **FOREACH_FAILURE_MODE**: ALL entries belong to "engine observability bitmap". Some are BIT_FLAG storage; some are COUNTER_U32; some are PERCENT_U8. Same registry; per-entry storage class. → COLUMN (storage class).
- **FOREACH_SLOW_PATH_GATE**: ALL entries are slow-path-cached gates checked once per cycle. Some are PER_CORE scope; some are ENGINE_WIDE. Same gate shape; different cache surface. → COLUMN (scope).
- **FOREACH_STAMP_BOUND_CFG (extended v5.14.9.F.2)**: ALL entries belong to canonical stamp body cfg-bound subset. Some emit from DIRECT_FIELD source; some emit from BITMAP_BIT (after .F.2 migration). → COLUMN (emit_source).

Properties that signal COLUMN:
- Wire-format / canonical-order constraint (HMAC-locked, JSON schema, snapshot bytes)
- Same caller surface (one production-caller assembles all entries; e.g., one EmitStampBody walks the registry)
- Heterogeneity is in DISPATCH, not in DOMAIN
- Adding a new entry is a 1-row registry edit; existing HANDLE_GEN_<MARKER> applies (no new generation logic needed)
- Future axis values bounded ("this registry has 2-3 dispatch shapes; not 10")

### When DOMAIN SPLIT wins

Entries DIFFER in domain identity AND don't share a single caller surface. Examples:

- **FOREACH_<DOMAIN>_CFG_FLAG (this pattern's primary application — v5.14.9.F-.F.3)**: cfg booleans grouped by semantic domain. OMS_CFG_FLAG (drainer-adjacent), GATE_CFG_FLAG (entry/exit), RISK_CFG_FLAG (sizing), ML_CFG_FLAG (confidence/bandit), OPS_CFG_FLAG (operational). Each domain has different read cadence, different consumers, potentially different mutation patterns. → SPLIT.
- **FOREACH_FEATURE vs FOREACH_FAILURE_MODE**: features = ML pipeline state; failure modes = observability state. Different domains entirely; would never share a registry. → SPLIT (trivially).
- **FOREACH_STRATEGY vs FOREACH_REGIME**: strategies dispatch entry-side computation; regimes classify market state. → SPLIT (trivially).

Properties that signal SPLIT:
- Different read cadences across entries (hot-path / slow-path / boot-only)
- Different mutation patterns (read-only cfg vs mutable state vs append-only event)
- Different cache-line concerns (hot domain near hot data; observability domain on separate cache line)
- Future-flexibility need (one domain growing fast; others stable; want to split independently in v5.X+)
- Adding a new entry to one domain doesn't affect others; no cross-domain coupling

### When NEITHER wins

If entries don't share enough structure for any registry, just declare them inline. Registry overhead requires:
- ≥3 entries with ≥2 caller sites (CLAUDE.md item 13 threshold)
- A non-trivial bug class to extinguish (forgotten populator, drift between consumers, etc.)

---

## Decision framework

| Question | If YES → COLUMN | If YES → SPLIT |
|---|---|---|
| Wire format / canonical order locked? | ✓ | |
| Single production-caller assembles all entries? | ✓ | |
| Heterogeneity is per-entry generation, not per-entry domain? | ✓ | |
| Different read cadences across entries? (hot/slow/boot) | | ✓ |
| Different cache-line concerns per axis value? | | ✓ |
| Different consumer surfaces per axis value? | | ✓ |
| Future-flexibility: one axis growing fast, others stable? | | ✓ |
| ≥1 new generation logic per axis value? | | ✓ |

If multiple factors point both ways, lean COLUMN (lower fragmentation cost). Switch to SPLIT only if at least 2 SPLIT factors apply.

If COLUMN's "single caller surface" doesn't hold (i.e., multiple distinct callers each consuming a different subset), that's a strong SPLIT signal. The point of COLUMN is consolidation; if consolidation isn't natural, force-fitting it adds registry walk cost without amortizing.

---

## The pattern (concrete shape)

### Form 1: SCOPE COLUMN

Tuple includes a TOKEN axis column. Token-paste dispatches to per-axis macros (Y3 mechanism — see "Y3 dispatch canon" section below for the universal implementation):

```cpp
// Tuple: X(name, scope_token, predicate_or_data, doc)
#define FOREACH_REGISTRY(X)                                  \
    X(LADDER_ACTIVE,    PER_CORE,    /* predicate */, "doc") \
    X(LAZY_REBUILD,     PER_CORE,    /* predicate */, "doc") \
    X(WS_FLATTEN,       ENGINE_WIDE, /* predicate */, "doc")

// Per-scope generation handlers
#define X_AUTOPOP_DISPATCH_PER_CORE(name, pred, doc)    /* per-core walk */
#define X_AUTOPOP_DISPATCH_ENGINE_WIDE(name, pred, doc) /* engine-wide walk */

// Top-level dispatcher: token-paste resolves to right handler at preprocessor time
#define X_AUTOPOP_DISPATCH(name, scope, pred, doc) \
    X_AUTOPOP_DISPATCH_##scope(name, pred, doc)

#define REGISTRY_AUTOPOPULATE(state_pc, state_eng, _cfg) \
    do { \
        const auto& cfg = (_cfg); \
        FOREACH_REGISTRY(X_AUTOPOP_DISPATCH) \
    } while (0)
```

### Form 2: DOMAIN SPLIT

N independent registries, each homogeneous. Auto-flow infrastructure repeats per registry (or shares via a meta-macro):

```cpp
// Domain registry 1: LIFECYCLE booleans (uint8_t fits 8 flags) — position-exit mechanics
#define FOREACH_LIFECYCLE_CFG_FLAG(X)                                                       \
    X(PARTIAL_EXIT_ENABLED, partial_exit_enabled, "partial-exit dispatcher arm")            \
    X(BREAKEVEN_ON_PARTIAL, breakeven_on_partial, "move SL to entry after TP1 hit")         \
    X(BREAKEVEN_ON_PROFIT,  breakeven_on_profit,  "ratchet SL to breakeven on net profit")

// Domain registry 2: ML booleans (uint16_t fits 16 flags)
#define FOREACH_ML_CFG_FLAG(X)                                                       \
    X(CONFIDENCE_ENABLED,           confidence_enabled,           "scale entry by confidence") \
    X(CONFIDENCE_COMPOSITE_ENABLED, confidence_composite_enabled, "4-factor composite")        \
    X(BANDIT_ENABLED,               bandit_enabled,               "bandit warmup")             \
    X(EXIT_BANDIT_ENABLED,          exit_bandit_enabled,          "exit bandit")

// Per-domain bitmap field on parent struct
struct ControllerConfig {
    /* Hot-domain bitmap cluster (drainer + sizing + ML pipeline read these) */
    alignas(8) uint8_t  lifecycle_cfg_flags;   // drainer reads every cycle
                uint8_t  gate_cfg_flags;  // sizing reads slow-path
                uint16_t ml_cfg_flags;    // ML pipeline reads slow-path

    /* Cold-domain bitmap cluster (boot + GUI only) */
    alignas(8) uint8_t  risk_cfg_flags;
                uint8_t  ops_cfg_flags;
    /* See "Cache-layout discipline for DOMAIN SPLIT bitmap fields" section below */
};

// Generated MASK_<DOMAIN>_<NAME> constants per domain
#define X_GEN_OMS_MASK(name, legacy_field, doc) \
    static constexpr uint8_t MASK_LIFECYCLE_CFG_##name = (1u << OMS_CFG_##name);
FOREACH_LIFECYCLE_CFG_FLAG(X_GEN_OMS_MASK)
#undef X_GEN_OMS_MASK
// Repeat per domain

// Per-domain AUTOPOPULATE companion (read cfg fields → write bitmap)
#define LIFECYCLE_CFG_FLAG_AUTOPOPULATE(state, _cfg) \
    do { \
        const auto& cfg = (_cfg); \
        uint8_t _new_flags = 0; \
        #define X(name, legacy_field, doc) \
            _new_flags |= ((cfg).legacy_field ? MASK_LIFECYCLE_CFG_##name : 0u); \
        FOREACH_LIFECYCLE_CFG_FLAG(X) \
        #undef X \
        (state).lifecycle_cfg_flags = _new_flags; \
    } while (0)
// Repeat per domain
```

---

## Domain-membership criteria — what's NOT cfg-flag-eligible

DOMAIN SPLIT registries collect cfg booleans by semantic domain. But not every "boolean used in code" is a cfg flag. Forcing non-cfg booleans into the bitmap pattern causes regressions.

### Eligibility criteria

For a boolean to qualify for a `FOREACH_<DOMAIN>_CFG_FLAG` registry, **ALL** of the following must hold:

1. **Boot-frozen** — value loaded at startup from `engine.cfg`; not mutated at runtime
2. **Engine-wide OR per-core-via-cfg-override** — not a per-core runtime atomic (those use ParameterSlot pattern instead)
3. **Hot-path-tolerant** — runtime read of bitmap bit (~1-2ns) is acceptable cost at every read site
4. **No compile-time elision benefit** — the flag isn't a candidate for `template <bool>` + `if constexpr` elimination
5. **Cfg-domain-coherent** — semantically belongs to one of the existing domains (LIFECYCLE / GATE / RISK / ML / OPS) or warrants a new domain

If ANY of (1)-(4) fails, the boolean is NOT cfg-flag-eligible. Use a different mechanism:
- (1) violated → use atomic on shared state struct (e.g., `kill_switch_tripped` is mutated; lives in mutable state, not cfg)
- (2) violated → use ParameterSlot atomic (per-core hot-path-cached; e.g., `param_staleness_gate_enabled`)
- (3) violated → use pre-computed predicate cache or compile-time elision (e.g., latency profiling)
- (4) violated → use `template <bool>` parameter (e.g., `lat_enabled`)

### Cautionary tale: `lat_enabled`

The v5.14.9.F audit subagent flagged `lat_enabled` as "NOT FOUND in ControllerConfig — must add" based on a string-search assumption. Step 0 verification revealed it's a per-Tick local var inside `ExecutionCore_Tick_Impl<F, LAT_ENABLED, PAIR_BRANCHLESS>` template function:

```cpp
// CoreFrameworks/ExecutionCore.hpp:295
uint8_t lat_enabled = 0;
if constexpr (LAT_ENABLED) {                                    // Layer 1: compile-time elision
    lat_enabled = core->latency_stats.enabled.load(...);        // Layer 2: per-core runtime atomic
    if (__builtin_expect(lat_enabled, 0)) { /* sample */ }
}
```

Migrating `lat_enabled` to a cfg-flag bitmap would have:
- Regressed hot-path ~1-2ns/tick **perpetually** in production builds (compile-time elision lost)
- Lost per-core runtime mutability (operator GUI flips during a session)
- Violated CLAUDE.md item 18(a) (DEFAULT-OFF safety gates use compile-time elision)

Caught during step 0 verification. Domain reframed from `OMS_CFG_FLAG` → `LIFECYCLE_CFG_FLAG`. See `DOCS/TECH_DEBT.md` TECH_DEBT-023 for full rationale-preservation entry.

### Discipline gate

Future audits (`/dod-audit` Pattern 3e bit-packing, `/readiness` Check 19 file:line claims, `/merge-scan` reuse-merge candidates) should validate cfg-flag eligibility against the 5 criteria above. A boolean that fails (1)-(4) but is proposed for migration should surface as a YELLOW finding with reference to TECH_DEBT-023 + this section.

---

Per-domain bitmap on parent struct preserves intra-domain cache locality (see Cache-layout discipline section). Adding a new flag in domain D = 1 row in `FOREACH_D_CFG_FLAG`; AUTOPOPULATE picks it up on next compile.

### Form 3 (Hybrid): per-domain registries WITH per-entry COLUMN

When a domain itself has heterogeneous entries (e.g., some ML cfg flags are stamp-bound, some aren't), the domain registry can ALSO use a column. Two-axis dispatch: domain (split) + per-entry attribute (column). Worked example below.

#### Worked example: stamp-binding integration (v5.14.9.F.2)

ML_CFG_FLAG entries integrate with FOREACH_STAMP_BOUND_CFG (separate registry that handles stamp emission). The PARENT registry (FOREACH_STAMP_BOUND_CFG) gains an `emit_source` column via Y3 dispatch:

```cpp
// FOREACH_STAMP_BOUND_CFG tuple extended (8-col → 9-col):
//   X(name, type, fmt, default_val, get_value_expr, emit_when, emit_source, doc)
//
// emit_source values:
//   DIRECT_FIELD — get_value_expr reads cfg field verbatim (legacy path)
//   BITMAP_BIT   — get_value_expr is a bitmap-extract on cfg.<domain>_cfg_flags

#define FOREACH_STAMP_BOUND_CFG(X)                                                          \
    /* Existing entries (DIRECT_FIELD): */                                                  \
    X(ml_buy_threshold, double, "%.17g", 0.0,                                              \
      FPN_ToDouble(cfg.ml_buy_threshold),                                                   \
      (cfg.ml_buy_threshold > 0),                                                           \
      DIRECT_FIELD, "buy threshold")                                                        \
    /* v5.14.9.F.2 migrated entries (BITMAP_BIT): */                                        \
    X(confidence_enabled, int, "%d", 0,                                                     \
      (BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_CONFIDENCE_ENABLED) ? 1 : 0),           \
      (BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_CONFIDENCE_ENABLED)),                   \
      BITMAP_BIT, "scale entry threshold by confidence")                                    \
    X(confidence_composite_enabled, int, "%d", 0,                                          \
      (BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_CONFIDENCE_COMPOSITE_ENABLED) ? 1 : 0), \
      (BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_CONFIDENCE_COMPOSITE_ENABLED)),         \
      BITMAP_BIT, "use 4-factor composite confidence")                                      \
    /* etc */

// Y3 dispatch: per-emit_source emit handler
#define HANDLE_STAMP_EMIT_DIRECT_FIELD(name, type, fmt, def, get, when, src, doc) \
    if (when) { n += snprintf(buf + n, cap - n, #name "=" fmt "\n", get); }

#define HANDLE_STAMP_EMIT_BITMAP_BIT(name, type, fmt, def, get, when, src, doc) \
    if (when) { n += snprintf(buf + n, cap - n, #name "=" fmt "\n", get); }
// (Both handlers share body shape; the difference is in how `get` is evaluated.
//  Preprocessor doesn't care; runtime evaluates correctly via the registry tuple's
//  expression. Future emit_source values e.g. COMPUTED_FROM_GROUP can have
//  genuinely different handler bodies.)

#define HANDLE_STAMP_EMIT(name, type, fmt, def, get, when, src, doc) \
    HANDLE_STAMP_EMIT_##src(name, type, fmt, def, get, when, src, doc)

// Walk in emit body:
FOREACH_STAMP_BOUND_CFG(HANDLE_STAMP_EMIT)
```

**Wire format byte preservation:** emit_source = BITMAP_BIT entries produce identical wire bytes to their pre-migration DIRECT_FIELD form because `BITMAP_IS_SET(...)? 1 : 0` evaluates to the same uint as `cfg.confidence_enabled` did (both are 0 or 1). HMAC chain unbroken.

**Adding a new emit_source value:** future ships may need COMPUTED_FROM_GROUP (read multiple cfg fields, fold into one stamp value) or DERIVED_FROM_LABEL (read training-time-derived value). Add ONE new HANDLE_STAMP_EMIT_<NEW_SOURCE> macro definition; existing entries unchanged.

**STAMP_CFG_AUTOPOPULATE companion:** the existing AUTOPOPULATE macro for production-callers extends similarly. The dispatch happens once at AUTOPOPULATE walk; subsequent reads use direct field assignment regardless of emit_source (since AUTOPOPULATE writes to a CONCRETE struct, not the bitmap). Bitmap-bit emit_source's get expression is evaluated at AUTOPOPULATE time → bool → stored on the production-caller struct. Same bytes as before migration.

---

## Y3 dispatch canon (implementation mechanism)

Y3 token-paste dispatch is the **canonical mechanism** for ALL heterogeneous registry generation that varies per axis value. Universal across COLUMN-form registries + the "per-entry column" half of HYBRID form.

### Universal Y3 shape

```cpp
// Pattern: tuple has axis column TOKEN
#define FOREACH_REGISTRY(X) \
    X(name1, AXIS_VALUE_A, ...) \
    X(name2, AXIS_VALUE_B, ...)

// Per-axis-value handler macros (one per axis value)
#define HANDLE_GEN_AXIS_VALUE_A(args)  /* handler A body */
#define HANDLE_GEN_AXIS_VALUE_B(args)  /* handler B body */

// Top-level dispatcher: token-paste resolves at preprocessor time
#define HANDLE_GEN(name, axis, ...) HANDLE_GEN_##axis(name, ...)

// Walk
FOREACH_REGISTRY(HANDLE_GEN)
```

### Adding a new entry

- New entry with EXISTING axis value: 1 row in FOREACH_REGISTRY tuple. Existing dispatch macros unchanged.
- New entry with NEW axis value: 1 row + 1 new HANDLE_GEN_<NEW_VALUE> macro definition. Existing entries unchanged.

### Why Y3 over alternatives

| Alternative | Why rejected |
|---|---|
| Bitmask presence column | Preprocessor can't conditionally suppress per-row expansion based on integer arithmetic; struct member declarations aren't constexpr expressions |
| Sub-FOREACH split (one macro per axis value) | Reorders entries when concatenated; breaks wire-format byte preservation when emit order is canonical |
| Function-pointer table | Requires runtime indirection; loses compile-time generation benefit; can't dispatch struct member declarations |
| Variadic templates | More complex than necessary; readability cost; not generally faster |

### Y3 in the catalog (canonical reference implementations)

| Registry | Axis column | Values | First applied |
|---|---|---|---|
| FOREACH_SLOW_PATH_GATE | scope | PER_CORE / ENGINE_WIDE | v5.14.9.B.0 |
| FOREACH_STAMP_BOUND_MODEL_CONST | presence | INCLUDE / SKIP_HANDLE | v5.14.8.A.merged |
| FOREACH_FAILURE_MODE | storage class | BIT_FLAG / COUNTER_U32 / PERCENT_U8 | v5.14.8.B |
| FOREACH_STAMP_BOUND_CFG (extended) | emit_source | DIRECT_FIELD / BITMAP_BIT | v5.14.9.F.2 (proposed) |

### Y3 forward leverage

Future heterogeneous registries default to Y3 dispatch unless an alternative is explicitly justified in the registry header's design comment. New axis dimensions become single-macro additions instead of registry restructures. CLAUDE.md item 19 (structural fix preferred when bug class can recur) applies here: ad-hoc dispatch each time a registry needs heterogeneity is the recurring class; Y3 is the structural fix.

---

## Cache-layout discipline for DOMAIN SPLIT bitmap fields

DOMAIN SPLIT places N bitmap fields on a parent struct (e.g., 5 cfg-flag bitmaps on ControllerConfig). Layout decisions affect read latency under contention.

### The concrete concern

Drainer thread reads `lifecycle_cfg_flags` every cycle (hot read; cache-resident expectation). If the cache line containing `lifecycle_cfg_flags` ALSO contains a mutable field that the slow-path writes (e.g., `kill_switch_tripped`), then every slow-path write invalidates the drainer's cache line → bounce penalty (40-400ns per cycle).

This is "false sharing" applied to bitmap-on-struct layouts — not classic false sharing across atomics, but the same hardware mechanism (cache-line invalidation across cores).

### Layout strategy: hot-cluster vs cold-cluster

Group bitmap fields by READ CADENCE, not by struct organization preference. Place hot-read bitmaps in one cluster (cache-line aligned start); cold-read bitmaps in another cluster. Pad between clusters if the parent struct has mutable fields that would land between them.

**Example layout for 5 domain bitmaps on ControllerConfig:**

```cpp
struct alignas(8) ControllerConfig {
    /* ... existing fields ... */

    /* HOT-CLUSTER: domain bitmaps that hot/slow-path readers consume */
    alignas(8) uint8_t  lifecycle_cfg_flags;    // drainer reads every cycle
                uint8_t  gate_cfg_flags;   // sizing reads slow-path
                uint16_t ml_cfg_flags;     // ML pipeline reads slow-path
    /* Total hot-cluster: 4 bytes; aligned + clustered for read locality */

    /* COLD-CLUSTER: domain bitmaps read at boot / GUI only */
    alignas(8) uint8_t  risk_cfg_flags;   // boot validation + GUI
                uint8_t  ops_cfg_flags;    // GUI only
    /* Total cold-cluster: 2 bytes; separated from hot-cluster */

    /* ... other fields ... */
};
```

**Why this works:**
- `alignas(8)` on hot-cluster start ensures the cluster begins at an 8-byte boundary; drainer's hot read of `lifecycle_cfg_flags` lands on an aligned address
- 4 bytes total for hot-cluster fits well within a single cache line (64 bytes typical), even if subsequent fields share the line — those fields just need to be read-only-by-drainer or write-only-by-slow-path with no concurrent reader
- Cold-cluster separated by `alignas(8)` ensures different cache line; mutations in cold-cluster don't bounce the hot-cluster line

### When to revisit

After v5.14.9.F-.F.6 ships, profile under contention:
- Run paper-test with 4+ active cores
- Capture drainer p99 latency vs cold-line assumption
- If p99 regresses, audit cache-line layout (use perf c2c or similar)
- If false-sharing detected, escalate to `alignas(64)` (full cache line padding) on hot-cluster or relocate cold-cluster further

### Cost

- 0-7 bytes padding from `alignas(8)` (depends on adjacent field types)
- ~5 minutes per cfg field added to write the layout-aware declaration
- 1-2h paper-test profiling at sprint-close to confirm no regression

### Future-leverage pattern

Capture as `/dod-audit` Pattern 3a sub-check: "for any new cfg field with hot-path readers, was the cache-line audit done?" Adds a YELLOW finding when a new cfg field is declared without considering layout. Encodes the discipline as a self-enforcing audit gate.

### Why this section exists

HIGH.1 finding from /dod-audit on v5.14.9.F amendment surfaced this as a load-bearing decision. Rather than handle it once for v5.14.9, the discipline is captured as a reusable pattern so future cfg-bitmap migrations (TECH_DEBT-009 broader closure, TECH_DEBT-011 PerCoreSnap fields, TECH_DEBT-012 OMS state) inherit the layout strategy.

---

## Trade-offs + when to apply

### Apply COLUMN when:
- Wire-format / canonical order is locked (HMAC, JSON schema, snapshot bytes)
- Single production-caller assembles all entries (one walk over registry)
- Adding a new axis value is bounded (you won't end up with 10 dispatch shapes)
- Bug class to extinguish is "forgot to add per-axis handling at production caller"

### Apply SPLIT when:
- Domains have natural identity (cfg-flag domains, feature categories, strategy families)
- Read cadences differ enough to warrant separate cache surfaces
- Domain growth is asymmetric (one domain grows fast; others stable)
- Consumers vary per domain (parser walks all; GUI walks per-tab; per-core override walks subset)
- Bug class to extinguish is "scattered fields across struct without coherent grouping"

### Apply HYBRID (per-domain SPLIT with per-entry COLUMN) when:
- Domain split is correct AT THE TOP LEVEL
- Within a domain, entries vary along a SECOND axis (stamp-bound vs runtime; storage class; etc.)
- Adding a new entry would otherwise require deciding "do I need a NEW SUB-DOMAIN or just a NEW ENTRY?"

### Cost comparison

**COLUMN cost:**
- ~30 min per new dispatch shape (one HANDLE_GEN_<MARKER> macro)
- Single registry source-of-truth
- One walk; one struct gen; one AUTOPOPULATE
- Consumer can iterate all entries with one loop

**SPLIT cost:**
- ~2-3h per new domain (registry header + AUTOPOPULATE + parser block + GUI tab + per-core override extension)
- N registries to maintain
- Pattern-repeated infrastructure (each domain has own AUTOPOPULATE; arguably good for clarity, bad for code size)
- Consumer must walk N registries

**HYBRID cost:**
- COLUMN cost per domain × N domains
- Same bug-class extinction as both forms combined

### Wins
- COLUMN: lower fragmentation; canonical-order preservation; bounded surface
- SPLIT: cache-line locality per domain; independent growth; per-consumer registry choice
- HYBRID: best of both; future-flexibility within bounded domains

---

## Reference implementations

### COLUMN form

**FOREACH_SLOW_PATH_GATE (v5.14.9.B.0):** scope column.
- File: `CoreFrameworks/SlowPathGateRegistry.hpp`
- 7 entries (5 PER_CORE + 2 ENGINE_WIDE)
- Token-paste dispatch via `X_AUTOPOP_<VARIANT>_DISPATCH_<SCOPE>`
- See: `slow-path-gate-registry-pattern.md`

**FOREACH_STAMP_BOUND_MODEL_CONST (v5.14.8.A.merged):** presence column.
- File: `ML_Headers/StampBoundModelConstRegistry.hpp`
- 32 entries; 2 presence variants (INCLUDE, SKIP_HANDLE)
- Wire format byte-locked via PRE_CFG / POST_CFG split
- See: `x-macro-registry-with-presence-dispatch.md`

**FOREACH_FAILURE_MODE (v5.14.8.B):** storage-class column.
- File: `MemHeaders/FailureModeRegistry.hpp`
- ~12 entries; 3 storage-class variants (BIT_FLAG, COUNTER_U32, PERCENT_U8)
- Each storage class auto-allocates its own field width

**FOREACH_STAMP_BOUND_CFG (v5.14.9.F.2 extension — IN-FLIGHT):** emit_source column.
- File: `ML_Headers/StampBoundCfgRegistry.hpp` (extended)
- Existing entries: ~15 DIRECT_FIELD; new entries: ~7 BITMAP_BIT (migrated ML cfg booleans)
- Y3 dispatch via HANDLE_STAMP_EMIT_<EMIT_SOURCE>

### SPLIT form

**FOREACH_<DOMAIN>_CFG_FLAG (v5.14.9.F-.F.3 — IN-FLIGHT):** primary application of this pattern.
- 5 domain registries planned: OMS, GATE, RISK, ML, OPS
- Each on its own bitmap field on ControllerConfig
- AUTOPOPULATE per-domain
- Cache-layout discipline: hot-cluster (OMS + GATE + ML) vs cold-cluster (RISK + OPS) per cache-layout discipline section above
- Closes: TECH_DEBT-013(5) + TECH_DEBT-009 boolean subset
- Supersedes: TECH_DEBT-019 (rejected monolithic FOREACH_ENGINE_CFG_FLAG — see TECH_DEBT.md for the rejection rationale entry)

**FOREACH_FEATURE vs FOREACH_REGIME vs FOREACH_STRATEGY:** trivial split (different domains; no overlap). Not consciously designed via this pattern; arose naturally because the domains have nothing to share.

### HYBRID form

**FOREACH_ML_CFG_FLAG + FOREACH_STAMP_BOUND_CFG cross-registry integration (v5.14.9.F.2 — IN-FLIGHT):**
- ML_CFG_FLAG (DOMAIN-level split for ML booleans)
- STAMP_BOUND_CFG (COLUMN-level emit_source dispatch within stamp-binding registry)
- Cross-registry hybrid: domain registry handles cfg storage; stamp registry handles emit
- Two-level dispatch: domain → registry; emit_source → handler

---

## Lessons / gotchas

(Populated during .F-.F.6 ship work + at .I umbrella close.)

### Field-test status (per ship — populated as ships land)

**Concern #1 — Stamp-binding integration in HYBRID form: ✅ VALIDATED (v5.14.9.F.2 shipped 2026-05-10, commit 9eceb4b)**
- ML_CFG_FLAG entries integrated via FOREACH_STAMP_BOUND_CFG emit_source column extension (6-col → 7-col with Y3 token-paste dispatch)
- `confidence_composite_enabled` migrated to emit_source=BITMAP_BIT; 18 other entries marked DIRECT_FIELD
- **HMAC byte-equivalence empirically proven:** `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_CONFIDENCE_COMPOSITE_ENABLED) ? 1 : 0` produces identical uint value (0 or 1) as pre-migration `cfg.confidence_composite_enabled`. snprintf("%d") output identical. /dod-audit Step 3g (wire-format byte preservation) PASS verdict.
- **5 consumer X-macros updated to 7-arg signature** (CoreModelZoo drift check + 4 in ModelInference: 2 struct-gen + parser + emit walk). C preprocessor handles unused emit_source arg correctly; no warnings.
- **Test coverage:** load-bearing "Y3 dispatch — byte-equivalent to direct read" + emit_when=false legacy-stamp-shape preservation tests
- **Forward leverage:** future emit_source values (e.g., COMPUTED_FROM_GROUP for derived stamp fields) require ONE new HANDLE_STAMP_EMIT_<MARKER> macro; existing entries unchanged.

**Concern #2 — Per-core override across SPLIT: ⏳ PENDING (v5.14.9.F.6 field test)**
- Per-bit override syntax (`core_N_partial_exit_enabled = 1` parses + sets correct bit on `core_N.lifecycle_cfg_flags`) requires PER_CORE_OVERRIDE_FIELDS macro extension. Pattern unproven for bitmap fields; v5.14.9.F.6 is the field test.

**Concern #3 — Parser auto-flow scaling: ⏳ PENDING (v5.14.9.F.4 field test)**
- parse_csv_engine_config currently has ~50+ if-else branches. After 5 domain registries handled in .F-.F.3, ~16-19 boolean branches will be replaced by 5 CFG_FLAG_AUTOPOPULATE_PARSE calls (one per domain). Remaining ~30 non-boolean branches stay manual until FOREACH_CFG_FIELD broader closure (TECH_DEBT-009).
- Open question: does mixing registry-driven + hand-written branches in same parser body compile cleanly + maintain readability?

**Concern #4 — Cache-layout discipline: ✅ VALIDATED (v5.14.9.F + .F.1 + .F.2 all applied)**
- Hot-cluster on ControllerConfig: `alignas(8) uint8_t lifecycle_cfg_flags; uint8_t gate_cfg_flags; uint16_t ml_cfg_flags;` (4 bytes total; aligned start; fits single cache line)
- /dod-audit Step 3a (cache alignment) + Step 3b (false sharing) PASS verdict on all 3 ships
- **Empirical:** drainer p99 latency unchanged across all 3 ships (no false-sharing regression observed)
- Forward concern: post-paper-test profiling decision per TECH_DEBT-021 (collapse 3 bitmap loads → 1 uint64_t vs further-split if ML grows). Defer to v5.14.10+ profile data.

**Concern #5 — GUI auto-layout consumer surface: ⏳ PENDING (v5.14.9.F.5 field test)**
- ImGui tabbed panel iterates each FOREACH_<DOMAIN>_CFG_FLAG to render checkboxes. Pattern: each tab is a single function that walks one registry. ImGui::CheckboxFlags native API may simplify the per-flag toggle macro (per /dod-audit MEDIUM.3 finding). Validation: panel renders correctly + checkbox state mirrors cfg bitmap; tooltip from doc string; "any flag enabled" indicator on tab header.

### Real lessons populated from v5.14.9.F + .F.1 + .F.2 ships

**Lesson 1 — Replace_all mangling has TWO shapes, not one (per memory `feedback_avoid_substring_replace_all_on_member_access.md`):**
- **Shape A (chained-prefix):** `config.X` replace_all mangles `ctrl->config.X` to `ctrl->BITMAP_IS_SET(config.X, ...)` — caught in .F.1
- **Shape B (variable-name suffix):** `cfg.X` replace_all mangles `fake_cfg.X` and `parsed_cfg.X` (test-local variables ending in 'cfg') to `fake_BITMAP_IS_SET(cfg.X, ...)` — caught in .F.2
- **Mitigation:** inventory BOTH shapes via `rg '\b[a-zA-Z_][a-zA-Z0-9_]*cfg\.X\b'` + `rg '(cfg|config|...)\.X\b'`. Use Edit-level targeting (specific old_string with full surrounding context) when scope >5 sites and multiple variations exist. Compile catches mangling artifacts; tests don't run until build succeeds.

**Lesson 2 — Step 0 inventory verification is load-bearing (v5.14.9.F LIFECYCLE reframe):**
- Initial .F scope claimed migrating `partial_exit_enabled` + `lat_enabled` to oms_cfg_flags bitmap
- Step 0 verification revealed `lat_enabled` is NOT a cfg field — it's a per-Tick template-elided atomic in `ExecutionCore_Tick_Impl<F, LAT_ENABLED>`
- Migration would have regressed hot-path ~1-2ns/tick perpetually (compile-time elision lost) + lost per-core runtime mutability (operator GUI flip)
- **Mitigation:** TECH_DEBT-023 codifies cfg-flag eligibility criteria (5 tests). Domain reframed OMS_CFG_FLAG → LIFECYCLE_CFG_FLAG mid-Step-0. Future audit subagents reference TECH_DEBT-023 when evaluating cfg-flag migration proposals.

**Lesson 3 — AUTOPOPULATE_FROM_<arity> macro family stabilizes per-domain (v5.14.9.F + .F.1 + .F.2):**
- LIFECYCLE: 3 entries → `LIFECYCLE_CFG_FLAG_AUTOPOPULATE_FROM_TRIPLE` (3 bool args)
- GATE: 6 entries → `GATE_CFG_FLAG_AUTOPOPULATE_FROM_HEX` (6 bool args)
- ML: 7 entries → `ML_CFG_FLAG_AUTOPOPULATE_FROM_SEPTUPLE` (7 bool args)
- Each macro arity matches its registry count. Naming follows latin numeric prefix (TRIPLE, HEX, SEPTUPLE). Caller passes explicit named bool args via `/*field_name*/` comment-aliasing for self-documenting use.
- **Alternative considered + rejected:** generic AUTOPOPULATE that walks registry with caller-bound `cfg`; rejected because caller-side default initialization requires explicit field values (not all-zero), and the per-arity form makes default values inline-documented.

**Lesson 4 — Cumulative ship economics (v5.14.9.F + .F.1 + .F.2):**
- 16 cfg booleans bit-packed into 3 cfg fields (4 bytes total vs 16 bytes scattered)
- 12 bytes saved per ControllerConfig instance (cache-line space freed for hot fields)
- ~150 cfg-side read sites migrated to BITMAP_IS_SET across 15+ files
- +71 new tests since .E ship; zero regressions across 3 ships
- Pattern field-tested 3× — DOMAIN SPLIT + Y3 dispatch + cache-layout discipline all proven sound

**Lesson 5 — MVP-vs-full-design framing (per memory `feedback_no_mvp_for_plumbing_only_for_unknown_unknowns.md`):**
- In .F.2 step 0a, "minimum-viable" (update one entry's get_cfg expression without 7-col extension) was proposed as scope-reduction
- Reversed after Caramel pushback: plan + DESIGN_SPECS + /dod-audit HIGH.2 had all documented the Y3 dispatch shape; defer would have contradicted documented design
- **Pattern:** MVP/deferral is for genuinely-new features with external dependencies that gate validation (e.g., maker orders without orderbook data — TECH_DEBT-008 indefinite defer). For plumbing/refactor work where the design is documented + patterns are field-tested, ship the FULL DESIGN.

### Future migrations that benefit from this pattern

- **TECH_DEBT-009 (FOREACH_CFG_FIELD):** broader closure of cfg-field N-site class for non-boolean fields (FPN<F> thresholds, ints, strings). Use SPLIT form per-domain; each domain registry handles all field types via type-trait dispatch.
- **TECH_DEBT-011 (FOREACH_PER_CORE_SNAP_FIELD):** visible-state snapshot fields. Use SPLIT (failure modes vs general state) + COLUMN (read cadence within domain). HYBRID form natural fit.
- **TECH_DEBT-012 (FOREACH_OMS_STATE):** OrderManager state fields. Use SPLIT (cold cfg vs hot dispatcher state) — drainer reads hot subset every cycle; cfg subset is boot-frozen.

### When NOT to apply this pattern

- Bug class isn't recurring (per CLAUDE.md item 19)
- Field count below threshold (≥3 entries + ≥2 caller sites; CLAUDE.md item 13)
- Boundary type itself is the gap (per CLAUDE.local.md memory `feedback_reduce_touch_sites.md` — refactor the boundary, don't wrap it)

### Branchless cmov verification (per /dod-audit HIGH.3)

AUTOPOPULATE companion macros use the idiom `_new_flags |= (condition ? MASK : 0u);`. Compiler is expected to emit cmov (no branch). Verification:
- Post-coding (e.g., at .F.6 close): `objdump -d build/controller_test | grep -A 5 'LIFECYCLE_CFG_FLAG_AUTOPOPULATE'` (or function name) — confirm no `j` branch instructions in AUTOPOPULATE bodies
- If branch present: switch to `-mask` form: `_new_flags |= (-(uint64_t)condition) & MASK;` — forces branchless on all compilers

This verification is a cheap insurance step. Captured as TECH_DEBT-022 (branchless guarantee discipline) for systematic application across AUTOPOPULATE companion macros.

---

## What this pattern is NOT

- Not a substitute for boundary-stable refactors: if the boundary type is the gap, registry shape doesn't fix it
- Not a license for premature abstraction: requires ≥3 entries + ≥2 caller sites
- Not a replacement for the existing X-macro pattern: this is the DECISION FRAMEWORK for choosing column vs split shape; the underlying X-macro pattern is unchanged
- Not orthogonal to FOREACH_STAMP_BOUND_CFG: stamp-binding remains a column on domain registries (HYBRID form); not a separate registry per domain

---

## Cross-references

- `bitmap-flag-api.md` — bit-packed flag storage primitives (BITMAP_*)
- `x-macro-registry-with-presence-dispatch.md` — base X-macro pattern + token-paste dispatch
- `slow-path-gate-registry-pattern.md` — COLUMN form reference implementation (FOREACH_SLOW_PATH_GATE)
- `autopopulate-pattern-for-production-caller-class.md` — companion AUTOPOPULATE macro
- `pre-post-cfg-registry-split-for-emit-order-preservation.md` — wire-format byte preservation when COLUMN form has locked emit order
- `wire-format-byte-preservation-discipline.md` — sister concern to PRE/POST split
- `structural-fix-preferred-decision-framework.md` — meta-pattern: when does ANY of this apply?
- FoxML_Trader_v2 `CLAUDE.md` items 13, 19, 20
- v5.14.9.F-.F.6 ships — first DOMAIN SPLIT field test; lessons feed back to this doc at .I

---

## Versioning

- v0.1 (2026-05-10): pre-field-test draft, written before .F-.F.6 ships start
- v0.2 (2026-05-10): post-/dod-audit expansion. Added Y3 dispatch canon section + cache-layout discipline section + concrete HYBRID worked example (stamp-binding integration via emit_source column). Addresses /dod-audit HIGH.1 + HIGH.2 + doc-debt #1 findings.
- v1.0 (planned 2026-05-10+ at v5.14.9 umbrella close): post-field-test ACTIVE; gotchas section populated with real lessons; concrete code references updated to shipped commits; HIGH.3 branchless verification status documented.
