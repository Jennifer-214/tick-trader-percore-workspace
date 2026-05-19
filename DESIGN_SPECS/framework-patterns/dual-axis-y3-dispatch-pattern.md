---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-12
tags: [framework-discipline, branchless-discipline]
surface: [registry, hot-path]
sister_specs: [x-macro-registry-with-presence-dispatch.md, multi-state-dispatch-with-per-state-update-metadata.md, dual-axis-y3-dispatch-pattern.md]
applies_at_skills: []
---

# Dual-axis Y3 dispatch pattern (multi-dimensional registry dispatch via independent token-paste axes)

**Established:** 2026-05-12 (v5.15.5.A.7)
**Status:** ACTIVE (DRAFT v0.1 pending field validation at .A.7 ship close)
**Cross-references:**
- Parent pattern: `x-macro-registry-with-presence-dispatch.md` (single-axis Y3 dispatch canon)
- Sister pattern: `heterogeneous-registry-pattern.md` (Form 1 scope column / Form 2 domain split / Form 3 hybrid; this extends Form 1 to multiple orthogonal axes)
- First application: `ML_Headers/CfgDriftCheckRegistry.hpp` (FOREACH_CFG_DRIFT_CHECK; 3 axes: severity × category × compare_kind)
- Companion: `bitmap-flag-api.md` (per-entry fail_mask bit-set in `drift_flags_at_load` uint16)

---

## Problem statement

Standard Y3 dispatch (`x-macro-registry-with-presence-dispatch.md`) uses one token column per registry to dispatch generation/runtime behavior to per-token handler macros:

```cpp
// Single-axis Y3 (canonical):
#define X(name, group, presence, ...) HANDLE_GEN_##presence(name, ...)
#define HANDLE_GEN_INCLUDE(name, ...)      type name;
#define HANDLE_GEN_SKIP_HANDLE(name, ...)  /* skip */
```

Some registries need **multiple INDEPENDENT dispatch axes** within one entry — each axis varies orthogonally, and combinations of values across axes are valid + meaningful.

**Concrete trigger (v5.15.5.A.7 — cfg-drift detection registry):**

19 cfg-drift checks classified across 3 orthogonal dimensions:

| Axis | Token values | What it drives |
|---|---|---|
| **severity** | `WARN_ALWAYS`, `REFUSE_STRICT` | Tier counter increment + REFUSE-in-strict return path |
| **category** | `INFERENCE_CFG`, `CROSS_BINARY` | Which ack-flag suppresses + which per-category drift bit to set |
| **compare_kind** | `EXACT`, `EPS_DEFAULT`, `STRING`, ...future | Comparison shape (`!=` vs `fabs > eps` vs `strcmp != 0`) |

Combinations: 2 × 2 × N (currently 3) = 12 distinct dispatch shapes. Manual if-else chains for 12 combinations = 12 code paths to maintain; missing one = silent bug.

**Recurring trajectory if single-axis used:**
- Collapse axes into one column: 12 distinct tokens (INF_CFG_TIER1_EPS, INF_CFG_TIER2_EXACT, CROSS_BIN_WARN_STRING, etc.). Combinatorial explosion. Adding new axis = re-derive ALL existing tokens. Future-headache multiplier inverted.
- Domain split into multiple FOREACH macros (one per category): 2 registries for category, but tier+compare_kind still need handling within each. Doesn't generalize.

Dual-axis (or N-axis) Y3 dispatch keeps each dispatch dimension independent. Adding new value to one axis = 1 new macro definition; existing entries untouched.

---

## Design space explored

### Option A: Single composite token column

```cpp
X(NAME, tier_class, ...) // tier_class = INF_CFG_TIER1, CROSS_BIN_WARN, etc.
```

**Rejected.** Combinatorial token explosion (12+ distinct tokens for the full Cartesian product). Adding new severity = re-derive all 6 category-compare combinations. Future-headache inverted.

### Option B: Multiple FOREACH macros (one per dimension)

`FOREACH_TIER1_CHECK` + `FOREACH_TIER2_CHECK` + `FOREACH_CROSS_BINARY_CHECK`...

**Rejected.** Each registry needs its own walker call site at the chokepoint. Adding new tier = new registry + new walker line. Doesn't reduce per-entry maintenance cost.

### Option C (chosen): Independent token columns per dispatch axis

Each axis gets its own column in the tuple. Y3 token-paste dispatches independently per axis:

```cpp
// Tuple has 3 dispatch-axis columns (severity, category, compare_kind):
X(NAME, type, severity, category, compare_kind,
  get_stamp_expr, get_cfg_expr, gate_when, fail_mask, doc)

// Per-axis dispatcher macros:
#define HANDLE_DRIFT_SEVERITY_WARN_ALWAYS(...)      ++tier2_count
#define HANDLE_DRIFT_SEVERITY_REFUSE_STRICT(...)    if (strict) ++tier1_refused_count; ++tier1_count

#define HANDLE_DRIFT_CATEGORY_INFERENCE_CFG(...)    \
    if (!BITMAP_IS_SET(cfg.ops_cfg_flags, MASK_OPS_CFG_ACKNOWLEDGE_INFERENCE_CFG_DRIFT)) { ... }
#define HANDLE_DRIFT_CATEGORY_CROSS_BINARY(...)     \
    if (!BITMAP_IS_SET(cfg.ops_cfg_flags, MASK_OPS_CFG_ACKNOWLEDGE_CROSS_BINARY_DRIFT)) { ... }

#define HANDLE_DRIFT_CMP_EXACT(stamp, cfg)        ((stamp) != (cfg))
#define HANDLE_DRIFT_CMP_EPS_DEFAULT(stamp, cfg)  (fabs((stamp)-(cfg)) > 1e-6)
#define HANDLE_DRIFT_CMP_STRING(stamp, cfg)       (strcmp((stamp),(cfg)) != 0)

// Walker composes all 3 axes per entry:
#define CFG_DRIFT_CHECK_ONE(NAME, type, severity, category, compare_kind, ...) \
    HANDLE_DRIFT_CATEGORY_##category({                                          \
        if (gate_when && HANDLE_DRIFT_CMP_##compare_kind(stamp_val, cfg_val)) { \
            HANDLE_DRIFT_SEVERITY_##severity(...);                              \
            BITMAP_SET(h->drift_flags_at_load, fail_mask);                      \
            log_fn(...);                                                        \
        }                                                                       \
    })
```

**Wins:**
- Each axis is an independent dispatch dimension; values combine freely
- Adding a new severity / category / compare_kind = 1 new macro definition; ZERO existing entries change
- Tuple grows by 1 column per dispatch axis (not by N combinations)
- Each per-entry dispatch is statically resolved at preprocessor time (no runtime branch tables)

---

## The pattern (concrete shape)

### Step 1: Identify orthogonal dispatch axes

Before writing the tuple, list the dimensions of variation across entries. Each dimension that VARIES INDEPENDENTLY across entries is a candidate axis:

| Dimension | Independent of other dims? | Distinct values | Axis? |
|---|---|---|---|
| Severity (tier 1 vs tier 2) | Yes (cross-binary can be either tier in future) | 2 | YES |
| Ack-flag category | Yes (drives different cfg flag) | 2 | YES |
| Comparison shape | Yes (varies by type + precision needs) | 3+ | YES |
| Failure-mask bit | Derivable from category | — | NO (derive) |
| Gate-when condition | Per-entry specific (not categorical) | N/A | NO (column, not Y3) |

3 independent axes → 3 Y3 dispatch columns.

### Step 2: Define per-axis dispatcher macros

For each axis, one macro per value:

```cpp
// Axis: severity
#define HANDLE_DRIFT_SEVERITY_WARN_ALWAYS(loc, role, name, fmt, stamp_v, cfg_v) \
    log_fn("[%s] WARN (Tier 2): %s role=%s stamp %s=%" fmt " cfg=%" fmt "\n",   \
           name, loc, role, #name, stamp_v, cfg_v);                              \
    ++tier2_count

#define HANDLE_DRIFT_SEVERITY_REFUSE_STRICT(loc, role, name, fmt, stamp_v, cfg_v) \
    log_fn("[%s] %s (Tier 1): %s role=%s stamp %s=%" fmt " cfg=%" fmt "\n",       \
           name, strict ? "REFUSE" : "WARN", loc, role, #name, stamp_v, cfg_v);    \
    ++tier1_count;                                                                  \
    if (strict) ++tier1_refused_count

// Axis: category
#define HANDLE_DRIFT_CATEGORY_INFERENCE_CFG(body)                                     \
    if (!BITMAP_IS_SET(cfg.ops_cfg_flags,                                              \
                       MASK_OPS_CFG_ACKNOWLEDGE_INFERENCE_CFG_DRIFT)) {                \
        body;                                                                          \
        BITMAP_SET(h->drift_flags_at_load, FAILURE_MASK_cfg_inference_drift);          \
    }

#define HANDLE_DRIFT_CATEGORY_CROSS_BINARY(body)                                       \
    if (!BITMAP_IS_SET(cfg.ops_cfg_flags,                                              \
                       MASK_OPS_CFG_ACKNOWLEDGE_CROSS_BINARY_DRIFT)) {                 \
        body;                                                                          \
        BITMAP_SET(h->drift_flags_at_load, FAILURE_MASK_cfg_cross_binary_drift);       \
    }

// Axis: compare_kind
#define HANDLE_DRIFT_CMP_EXACT(stamp, cfg)        ((stamp) != (cfg))
#define HANDLE_DRIFT_CMP_EPS_DEFAULT(stamp, cfg)  (fabs((stamp) - (cfg)) > 1e-6)
#define HANDLE_DRIFT_CMP_STRING(stamp, cfg)       (strcmp((stamp), (cfg)) != 0)
```

### Step 3: Walker composes all axes via nested expansion

```cpp
#define CFG_DRIFT_CHECK_ONE(NAME, type, severity, category, compare_kind,    \
                            get_stamp_expr, get_cfg_expr, gate_when,         \
                            fail_mask, doc)                                  \
    HANDLE_DRIFT_CATEGORY_##category({                                       \
        if (gate_when) {                                                     \
            auto stamp_val = (get_stamp_expr);                               \
            auto cfg_val   = (get_cfg_expr);                                 \
            if (HANDLE_DRIFT_CMP_##compare_kind(stamp_val, cfg_val)) {       \
                HANDLE_DRIFT_SEVERITY_##severity(                            \
                    loc, role_name, NAME, /* fmt token */, stamp_val,        \
                    cfg_val);                                                \
            }                                                                \
        }                                                                    \
    })

#define X CFG_DRIFT_CHECK_ONE
FOREACH_CFG_DRIFT_CHECK(X)
#undef X
```

### Step 4: Add new axis value = 1 new macro

Future case: need `EPS_TIGHT` (1e-9 epsilon) for a very-small-value field.

```cpp
#define HANDLE_DRIFT_CMP_EPS_TIGHT(stamp, cfg)  (fabs((stamp) - (cfg)) > 1e-9)
```

Add row in registry:
```cpp
X(my_tiny_field, double, REFUSE_STRICT, INFERENCE_CFG, EPS_TIGHT,
  h->inference_cfg_my_tiny_field, FPN_ToDouble(cfg.my_tiny_field),
  1, FAILURE_MASK_cfg_inference_drift, "very-small precision field")
```

Zero existing entries change. Walker auto-flows.

### Step 5: Add new axis entirely = new dispatcher family + new tuple column

Hypothetical future: need a 4th axis `log_destination` (STDERR / SYSLOG / DASHBOARD).

```cpp
// Define new dispatcher family:
#define HANDLE_DRIFT_LOG_STDERR(...)     log_to_stderr(__VA_ARGS__)
#define HANDLE_DRIFT_LOG_SYSLOG(...)     log_to_syslog(__VA_ARGS__)
#define HANDLE_DRIFT_LOG_DASHBOARD(...)  log_to_dashboard(__VA_ARGS__)

// Add column to tuple (11-col):
X(NAME, type, severity, category, compare_kind, log_destination,
  get_stamp_expr, get_cfg_expr, gate_when, fail_mask, doc)

// Update walker to invoke the new dispatcher:
#define CFG_DRIFT_CHECK_ONE(NAME, type, severity, category, compare_kind, \
                            log_destination, ...)                          \
    /* ...existing dispatch chain... */                                     \
    HANDLE_DRIFT_LOG_##log_destination(NAME, /* args */);
```

Cost: boundary refactor to add tuple column + update all existing entries with default for the new axis. Bounded — pattern still scales.

---

## Trade-offs + when to apply

### Apply when:
- Registry has 2+ INDEPENDENT dimensions of variation
- Each dimension has 2-5 distinct token values
- Combinations across dimensions are valid + meaningful
- Adding a new value to ONE axis should be cheap (1 macro definition)

### Skip when:
- Only one dimension varies (use canonical single-axis Y3 per `x-macro-registry-with-presence-dispatch.md`)
- Dimensions are tightly coupled (collapse into composite token)
- Registry has < 5 entries (manual dispatch is tractable)
- Some combinations are illegal (use Form 2 domain split with per-domain registries)

### Cost:
- 1 new tuple column per axis (visual width grows linearly with axis count)
- Per-axis dispatcher macro family (N values × M lines per macro)
- Walker complexity: nested HANDLE_*_## expansion (preprocessor-time; no runtime cost)
- Tuple-width budget per `registry-tuple-as-single-source-of-truth.md` recommends ≤8-10 columns — 3 dispatch axes + value/identity columns fits

### Win:
- N-dimensional dispatch scales linearly (1 macro per new value) instead of combinatorially
- Each axis is independently auditable + extensible
- Zero runtime cost (preprocessor-time dispatch)
- Future additions: 1 row in registry + 0-1 new macros per affected axis

---

## Reference implementations

### v5.15.5.A.7 — `FOREACH_CFG_DRIFT_CHECK` (first explicit dual+ axis application)

- Registry header: `ML_Headers/CfgDriftCheckRegistry.hpp`
- 19 entries spanning 12+ dispatch shapes
- 3 axes: severity (2 values) × category (2 values) × compare_kind (3 values; extensible)
- Walker: `CoreFrameworks/ModelValidation.hpp` `CoreModelZoo_ValidateAgainstCfg` body — single FOREACH_CFG_DRIFT_CHECK expansion replaces 15 manual if-blocks
- Closes Class 18 mirror at drift-detection surface

### Adjacent precedents (single-axis Y3 + multi-column heterogeneity)

- `FOREACH_FAILURE_MODE` (v5.14.8.B) — single-axis Y3 on `storage_class` (BIT_FLAG / COUNTER_U32 / PERCENT_U8); has additional non-Y3 columns (severity token, group_id, format_str, tooltip_str) but those drive runtime rendering, not preprocessor dispatch
- `FOREACH_STAMP_BOUND_CFG` (v5.14.9.F.2) — single-axis Y3 on `emit_source` (DIRECT_FIELD / BITMAP_BIT); 7-col with type + format dimensions
- `FOREACH_SLOW_PATH_GATE` (v5.14.9.B.0) — single-axis Y3 on `SCOPE` (PER_CORE / ENGINE_WIDE)

The PRINCIPLE in all of these is the same: token-paste dispatch via `HANDLE_GEN_##axis`. v5.15.5.A.7 extends to MULTIPLE simultaneous axes in one registry.

### Future application candidates

- Any registry where entries vary across 3+ independent dimensions
- Hypothetical `FOREACH_BACKTEST_METRIC` could need (window_type × aggregation × format) = 3 dispatch axes
- Hypothetical `FOREACH_PARITY_GATE` could need (boot_phase × gate_kind × strict_behavior) = 3 dispatch axes

---

## Lessons / gotchas

### Axes that "feel" independent might be coupled — audit before splitting

Initial v5.15.5.A.7 design had severity and category as ONE column (tier_class with 4 values: INF_CFG_TIER1, INF_CFG_TIER2, CROSS_BIN_WARN, future). Splitting into 2 axes (severity × category) revealed independence — cross-binary entries CAN be Tier 1 in future (e.g., build_flags_hash for live deploys). Splitting preserved that orthogonality.

**Test for orthogonality:** can you imagine a future entry that combines axis_A_value_X with axis_B_value_Y in a way no current entry does? If yes, axes are orthogonal.

### Tuple width concern

Per `registry-tuple-as-single-source-of-truth.md`, target ≤ 8-10 columns. 3-axis Y3 + 5-6 identity/value columns = 10 columns — at the upper bound. If a 4th axis emerges, consider:
1. Whether the 4th axis can be DERIVED from existing columns (compute, not store)
2. Whether the 4th axis warrants a DIFFERENT registry (domain split per Form 2)
3. Whether to accept 11-12 columns (still tractable per Boost.PP precedent)

### Macro hygiene — each axis dispatcher should be self-contained

Per-axis HANDLE macros should not reach across axes (e.g., HANDLE_DRIFT_SEVERITY_REFUSE_STRICT shouldn't reference cfg ack flags — that's category territory). Each axis's dispatcher does ONE thing for ONE axis. Composition happens at the walker.

### Code-gen stays compile-time

Y3 token-paste resolves at preprocessor time. No runtime branch on per-entry tokens. Each generated check is a static code path. This preserves the X-macro registry pattern's "no runtime cost" guarantee.

### When 2-axis becomes 1-axis post-refactor

If you find ALL entries cluster around 2-3 combinations and never combine freely, axes are not truly orthogonal — collapse back to single-axis. v5.15.5.A.7's 3 axes have 12+ distinct combinations actually used (not just 2-3) → orthogonality confirmed.

---

## Patterns NOT used here (and why)

### Composite token enum + lookup table

Considered: enumerate all valid (severity, category, compare_kind) tuples as DRIFT_KIND_INF_CFG_TIER1_EPS_DEFAULT etc., dispatch via lookup. Rejected — combinatorial token count + lose orthogonality + need re-enumeration on any axis change.

### Runtime function-pointer dispatch table

Considered: each axis combination → function pointer in a static table. Walker reads pointer per entry, invokes. Rejected — loses compile-time enforcement (forgotten combination = null pointer at runtime); loses type safety (function pointer hides per-type compare semantics).

### Variadic template metaprogramming

Considered: template parameter pack with 3 enum class types for the axes. Rejected — adds instantiation surface area + loses preprocessor-time enforcement (mismatched axis values are instantiation errors, not compile errors at registry definition site).

---

## Cross-references

- `x-macro-registry-with-presence-dispatch.md` — single-axis Y3 dispatch canon (parent pattern)
- `heterogeneous-registry-pattern.md` — Form 1 scope column / Form 2 domain split (sister patterns; dual-axis extends Form 1)
- `registry-tuple-as-single-source-of-truth.md` — Option D multi-consumer tuple expansion (tuple-width budget)
- `bitmap-flag-api.md` — BITMAP_* primitives used in HANDLE_DRIFT_CATEGORY macros
- `stamp-vs-runtime-drift-detection-registry.md` — pattern that v5.15.5.A.7 instantiates this dispatch for
- FoxML_Trader_v2 `CLAUDE.md` item 13 — X-macro registry pattern (umbrella)
- FoxML_Trader_v2 `CLAUDE.md` item 19 — structural fix preferred (motivation)
- FoxML_Trader_v2 `CLAUDE.md` item 23 — type-trait dispatch via templated helpers (compare_kind axis uses this for type-driven dispatch)
- FoxML_Trader_v2 `ML_Headers/CfgDriftCheckRegistry.hpp` — first explicit application
- FoxML_Trader_v2 `CoreFrameworks/ModelValidation.hpp` — walker consumer

---

## Pattern lifecycle status (per pattern-codification-lifecycle.md)

- **Stage 1 (audit / problem identification):** ✅ v5.15.5.A.7 pre-coding consult 2026-05-12; surfaced when single-axis Y3 didn't fit 3 orthogonal dimensions
- **Stage 2 (DESIGN_SPEC draft):** ✅ This doc (DRAFT v0.1 — 2026-05-12)
- **Stage 3 (first reference):** ✅ `ML_Headers/CfgDriftCheckRegistry.hpp` + `CoreFrameworks/ModelValidation.hpp` walker at v5.15.5.A.7
- **Stage 4 (cohort migration):** N/A — single application
- **Stage 5 (CLAUDE.md item):** Pending — promote to item 29 after 2nd application surfaces
- **Stage 6 (tooling enforcement):** `/dod-audit` could detect "registry with 2+ tightly-coupled token columns" → suggest splitting into Y3 axes
- **Stage 7 (wider audit):** Sweep codebase for collapsed-axis registries that could split into Y3 dispatch
