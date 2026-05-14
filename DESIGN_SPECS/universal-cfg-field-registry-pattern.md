# Universal cfg field registry pattern — one registry, all consumers

**Established:** 2026-05-13 (v5.15.5.F.4 sprint — pre-implementation draft)
**Status:** DRAFT v1.0 (pre-coding spec; promotes to ACTIVE after .F.4b ships)
**Cross-references:**
- Parent: `heterogeneous-registry-pattern.md` (SCOPE COLUMN vs DOMAIN SPLIT framework; this is SCOPE COLUMN with `Kind` as dispatch axis)
- Sister: `autopopulate-pattern-for-production-caller-class.md` (the AUTOPOPULATE companions emit consumer code from registry)
- Sister: `x-macro-registry-with-presence-dispatch.md` (Y3 dispatch mechanism)
- Composes with: `slow-path-cfg-resolution-cache-pattern.md` (this registry feeds the resolution cache)
- Composes with: `per-bit-per-core-override-pattern.md` (per-core override emission via PER_CORE_OK metadata flag)
- Composes with: `bitmap-flag-api.md` (metadata_flags is a bitmap)
- CLAUDE.md item 13 (X-macro registry); item 16 (reuse-audit); item 19 (structural fix preferred); item 20 (BITMAP_*); item 21 (AUTOPOPULATE companion); item 22 (PRE/POST split); item 23 (tt:: type-trait dispatch)

---

## Problem statement

The engine accumulates cfg fields at ~30-50 per minor version (Thompson sampling added 5; Ridge blending added 3; composite confidence added 11; soft risk degradation added 4; barrier blending added 1; live-readiness boot gates added 11; etc.). Between v5.12 and v5.15.5, 213 cfg fields exist; 90 surface in SettingsPanel; **123 are missing**.

This is the **Class-18 mirror pattern at function-composition level**: same cfg field must appear at ~6 sites:

| Site | Purpose | Drift class |
|---|---|---|
| `ControllerConfig.hpp` struct | Field declaration + default | (none — anchor) |
| Cfg parser (`Config_Parse` or `CfgParser_HandleKV`) | Parse from text cfg file | parser_gap |
| `SettingsPanel.hpp` field_defs[] | Render in GUI | panel_gap |
| Cfg save/load (`Config_Save`, `Config_Load`) | Persist to disk | persist_gap |
| Per-core override emission (`core_<name>[16]` + `core_<name>_override_set[16]`) | Per-core overrides | per_core_gap |
| Drift check (boot + hot-swap) | Stamp parity gate | stamp_drift_gap |

Adding a cfg field requires synchronous edits at all 6 sites. Forgetting any one causes a SILENT GAP — field is parseable but invisible / not save-able / no per-core override / no drift check. Each of these classes has recurred 3+ times in the last 6 months.

This is the **AUTOPOPULATE-eligible recurring class** (CLAUDE.md item 21): single source of truth → all consumers derive → drift becomes impossible.

---

## Design

### The registry

```cpp
// CoreFrameworks/CfgFieldRegistry.hpp — new file
//
// Single source of truth for cfg field declarations.
// All cfg consumers (parser, panel, save/load, per-core override, drift check,
// slow-path resolution cache) derive from this registry via AUTOPOPULATE companions.

#define FOREACH_CFG_FIELD(X) \
    /* ====== ML / Bandit ====== */                                                                                                                                          \
    X(DOUBLE,     bandit_blend_ratio,                "Bandit Blend",          "ML",             PER_CORE_OK,                              DBL(0.5, 0.0, 1.0),                       "Mix of bandit picks vs base model") \
    X(INT_ENUM,   bandit_algorithm,                  "Bandit Algorithm",      "ML",             PER_CORE_OK | STAMP_BOUND,                ENUM2("Exp3-IX", "Thompson", 0),          "Bayesian Thompson vs exponential-weights bandit") \
    X(DOUBLE,     thompson_mu_prior,                 "Thompson μ Prior",      "ML",             STAMP_BOUND,                              DBL(0.0, -1.0, 1.0),                      "Bayesian prior mean for Thompson arms") \
    X(DOUBLE,     thompson_precision_prior,          "Thompson τ Prior",      "ML",             STAMP_BOUND,                              DBL(1.0, 0.01, 1000.0),                   "Bayesian prior precision (inverse variance)") \
    X(DOUBLE,     thompson_precision_obs,            "Thompson Obs τ",        "ML",             STAMP_BOUND,                              DBL(1.0, 0.01, 1000.0),                   "Observation precision for updates") \
    X(INT,        thompson_rng_seed,                 "Thompson RNG Seed",     "ML",             PER_CORE_OK,                              INT(0, 0, INT_MAX),                       "RNG seed for reproducible samples") \
    /* ====== Ridge blending (v5.14.11) ====== */                                                                                                                            \
    X(DOUBLE,     ridge_lambda,                      "Ridge λ",               "ML",             STAMP_BOUND,                              DBL(0.15, 0.0, 10.0),                     "Cholesky regularization (Σ+λI)") \
    X(DOUBLE,     ridge_cost_penalty,                "Ridge Cost Penalty",    "ML",             STAMP_BOUND,                              DBL(0.5, 0.0, 5.0),                       "net_IC = IC - penalty*cost coefficient") \
    X(DOUBLE,     ridge_min_ic_floor,                "Ridge Min IC Floor",    "ML",             STAMP_BOUND,                              DBL(0.001, 0.0, 0.1),                     "Min net IC to prevent zero-weight starvation") \
    /* ====== Composite confidence (v5.14.1) ====== */                                                                                                                       \
    X(DOUBLE,     confidence_freshness_tau_secs,     "Freshness τ (sec)",     "ML",             STAMP_BOUND,                              DBL(3600.0, 60.0, 86400.0),               "Freshness decay half-life") \
    X(DOUBLE,     confidence_capacity_target_dollars,"Capacity Target ($)",   "ML",             STAMP_BOUND,                              DBL(0.0, 0.0, 1e9),                       "ADV $ target (0=unbounded)") \
    X(DOUBLE,     confidence_capacity_kappa,         "Capacity κ",            "ML",             STAMP_BOUND,                              DBL(0.1, 0.0, 1.0),                       "Proportionality factor for capacity") \
    X(DOUBLE,     confidence_rmse_baseline,          "RMSE Baseline",         "ML",             STAMP_BOUND,                              DBL(1.0, 1e-6, 100.0),                    "Training-time RMSE for stability factor") \
    X(DOUBLE,     confidence_hard_block_threshold,   "Hard Block Threshold",  "ML",             PER_CORE_OK,                              DBL(0.0, 0.0, 1.0),                       "Hard block below this confidence (0=disabled)") \
    X(DOUBLE,     confidence_ic_floor,               "IC Floor",              "ML",             PER_CORE_OK,                              DBL(0.0, -1.0, 1.0),                      "IC-based safety floor") \
    X(INT,        confidence_ic_floor_window,        "IC Floor Window",       "ML",             PER_CORE_OK,                              INT(0, 0, 10000),                         "Rolling-window samples for IC floor") \
    /* ====== Soft risk degradation (v5.14.9) ====== */                                                                                                                      \
    X(INT_ENUM,   risk_degradation_curve,            "Risk Degradation",      "Strategies",     PER_CORE_OK,                              ENUM4("OFF","LINEAR","EXP","STEP", 0),    "Confidence-gated size ladder") \
    /* ====== Momentum quality filters (v5.7.5) ====== */                                                                                                                    \
    X(DOUBLE_PCT, momentum_min_tp_margin_pct,        "Mom Min TP Margin",     "Strategies",     PER_CORE_OK,                              DBL(0.0, 0.0, 0.05),                      "Block entry if TP too tight (0=disabled)") \
    X(DOUBLE,     momentum_min_buy_delta_recent,     "Mom Min Buy Delta",     "Strategies",     PER_CORE_OK,                              DBL(0.0, 0.0, 1.0),                       "Min recent volume delta for entry") \
    X(DOUBLE,     momentum_min_r2,                   "Mom Min R²",            "Strategies",     PER_CORE_OK,                              DBL(0.0, 0.0, 1.0),                       "Min short_r2 for entry (0=disabled)") \
    X(BOOL,       momentum_require_last_win,         "Mom Require Last Win",  "Strategies",     PER_CORE_OK,                              BOOL(0),                                  "Block re-entry until previous trade was win") \
    /* ====== Live-readiness boot gates (v5.15.2) ====== */                                                                                                                  \
    X(BOOL,       require_mlockall,                  "Require mlockall",      "Live-Readiness", RESTART_REQUIRED | SAFETY_CRITICAL,       BOOL(1),                                  "HFT-safety gate (1=fatal if fails)") \
    X(INT,        model_max_age_hours,               "Model Max Age (hr)",    "Live-Readiness", SAFETY_CRITICAL,                          INT(0, 0, 8760),                          "Refuse models older than N hours (0=disabled)") \
    X(STRING,     held_out_stamp_secret,             "Held-Out Stamp Secret", "Live-Readiness", SAFETY_CRITICAL,                          STR(""),                                  "Operator secret for stamp authenticity") \
    /* ====== Lazy rebuild (v5.12.2) ====== */                                                                                                                               \
    X(INT,        lazy_rebuild_force_period_us,      "Lazy Force Period (μs)","Engine",         PER_CORE_OK,                              INT(1000000, 1000, 60000000),             "Worst-case rebuild interval") \
    X(DOUBLE_PCT, lazy_rebuild_price_threshold_pct,  "Lazy Price Threshold",  "Engine",         PER_CORE_OK,                              DBL(0.0005, 0.0, 0.01),                   "Material change threshold") \
    /* ====== ... (add the remaining ~80 entries here) ... ====== */
```

### The descriptor struct (heterogeneous payload via `Kind`-discriminated union)

```cpp
// CoreFrameworks/CfgFieldRegistry.hpp

struct CfgFieldDescriptor {
    enum Kind : uint8_t {
        KIND_DOUBLE      = 0,  // raw double; clamp_min, clamp_max
        KIND_DOUBLE_PCT  = 1,  // double formatted as percent in GUI
        KIND_INT         = 2,  // signed/unsigned int with clamp
        KIND_INT_ENUM    = 3,  // int with enum labels (radio/dropdown)
        KIND_BOOL        = 4,  // 0/1; bitmap or scalar storage
        KIND_STRING      = 5,  // const char* / std::string
        KIND_FILE_PATH   = 6,  // string + file picker hint
        KIND_FPN         = 7,  // FPN<F> direct (rare; most are converted from double at boot)
    };

    // Metadata bitmap (item 20)
    enum MetadataFlag : uint8_t {
        PER_CORE_OK         = 1 << 0,  // emit per-core override
        RESTART_REQUIRED    = 1 << 1,  // GUI badge: "restart needed"
        SAFETY_CRITICAL     = 1 << 2,  // GUI warning + confirmation prompt
        DEPRECATED          = 1 << 3,  // GUI: strikethrough + tooltip
        STAMP_BOUND         = 1 << 4,  // include in stamp drift check
        HIDDEN_BY_DEFAULT   = 1 << 5,  // GUI: collapsed section
    };

    Kind         kind;
    uint8_t      metadata_flags;
    const char*  cfg_field_name;       // matches Cfg::<name>
    const char*  label;                // GUI label
    const char*  section;              // GUI section heading
    const char*  tooltip;              // GUI tooltip + cfg.example comment

    union {
        struct { double default_val; double clamp_min; double clamp_max; }            as_double;   // KIND_DOUBLE, KIND_DOUBLE_PCT
        struct { int    default_val; int    clamp_min; int    clamp_max; }            as_int;      // KIND_INT
        struct { int    default_val; const char* const* labels; uint8_t count; }      as_int_enum; // KIND_INT_ENUM
        struct { uint8_t default_val; }                                               as_bool;     // KIND_BOOL
        struct { const char* default_val; }                                           as_string;   // KIND_STRING, KIND_FILE_PATH
    } payload;
};

static_assert(sizeof(CfgFieldDescriptor) <= 64,
              "CfgFieldDescriptor must fit one cache line — adjust packing if violated");
```

### tt:: dispatch helpers (CLAUDE.md item 23)

Heterogeneous Kind dispatch requires templated helpers so each Kind has its own instantiation:

```cpp
namespace tt {
    // Parse from text key=value
    template <CfgFieldDescriptor::Kind K>
    inline void cfg_parse_field(Cfg* dst, const CfgFieldDescriptor& desc, const char* val);

    template <> inline void cfg_parse_field<CfgFieldDescriptor::KIND_DOUBLE>(Cfg* dst, const CfgFieldDescriptor& desc, const char* val) {
        double v = parse_double_fast(val);
        v = std::clamp(v, desc.payload.as_double.clamp_min, desc.payload.as_double.clamp_max);
        *reinterpret_cast<double*>(reinterpret_cast<char*>(dst) + cfg_field_offset(desc.cfg_field_name)) = v;
    }
    template <> inline void cfg_parse_field<CfgFieldDescriptor::KIND_INT>(...) { /* strtol + clamp */ }
    template <> inline void cfg_parse_field<CfgFieldDescriptor::KIND_INT_ENUM>(...) { /* atoi, validate ∈ [0, count) */ }
    template <> inline void cfg_parse_field<CfgFieldDescriptor::KIND_BOOL>(...) { /* atoi → 0/1 */ }
    template <> inline void cfg_parse_field<CfgFieldDescriptor::KIND_STRING>(...) { /* strncpy */ }
    /* ... */

    // Render to GUI via Dear ImGui
    template <CfgFieldDescriptor::Kind K> inline bool cfg_render_field(...);

    // Save to disk (config.cfg key=value lines)
    template <CfgFieldDescriptor::Kind K> inline void cfg_save_field(FILE* fp, const Cfg* src, const CfgFieldDescriptor& desc);

    // Drift-check vs stamp body
    template <CfgFieldDescriptor::Kind K> inline bool cfg_drift_check(...);
}
```

The Kind tag is a compile-time-known token from the X-macro expansion (`KIND_DOUBLE`, `KIND_INT_ENUM`, etc.), so the dispatcher resolves at compile time — no runtime switch overhead.

### AUTOPOPULATE companions (item 21)

```cpp
// Single source of truth → all consumer code via X-macro walks

// --- 1. field_defs[] array for SettingsPanel ---
#define EMIT_PANEL_FIELD_DEF(kind_token, name, label, section, meta, payload, tooltip) \
    { CfgFieldDescriptor::KIND_##kind_token, (uint8_t)(meta), #name, label, section, tooltip, payload },

static const CfgFieldDescriptor g_cfg_field_descriptors[] = {
    FOREACH_CFG_FIELD(EMIT_PANEL_FIELD_DEF)
};
#undef EMIT_PANEL_FIELD_DEF

// --- 2. Parser: handle key=value via tt:: dispatch ---
#define EMIT_CFG_PARSER_CASE(kind_token, name, label, section, meta, payload, tooltip) \
    else if (strcmp(key, #name) == 0) { \
        tt::cfg_parse_field<CfgFieldDescriptor::KIND_##kind_token>(cfg, g_cfg_field_descriptors[FIELD_IDX_##name], val); \
    }

inline void CfgParser_HandleKV(Cfg* cfg, const char* key, const char* val) {
    if (0) {}  // anchor
    FOREACH_CFG_FIELD(EMIT_CFG_PARSER_CASE)
    else { /* per-core override matching + unknown-key handling */ }
}
#undef EMIT_CFG_PARSER_CASE

// --- 3. Save to disk ---
#define EMIT_CFG_SAVE_LINE(kind_token, name, label, section, meta, payload, tooltip) \
    tt::cfg_save_field<CfgFieldDescriptor::KIND_##kind_token>(fp, cfg, g_cfg_field_descriptors[FIELD_IDX_##name]);

inline void Cfg_Save(const Cfg* cfg, FILE* fp) {
    FOREACH_CFG_FIELD(EMIT_CFG_SAVE_LINE)
}
#undef EMIT_CFG_SAVE_LINE

// --- 4. Per-core override storage (emit ONLY for PER_CORE_OK fields) ---
#define EMIT_PER_CORE_DECL(kind_token, name, label, section, meta, payload, tooltip) \
    EMIT_PER_CORE_DECL_IF_##meta(kind_token, name)

// (PER_CORE_OK present in meta → emit `core_<name>[16]` + `core_<name>_override_set[16]`; else expand to nothing)

// --- 5. Drift check (for STAMP_BOUND fields) ---
#define EMIT_DRIFT_CHECK(kind_token, name, label, section, meta, payload, tooltip) \
    EMIT_DRIFT_CHECK_IF_##meta(kind_token, name)
```

The presence-dispatch idiom (`EMIT_X_IF_<TOKEN>`) is the standard CLAUDE.md item 13 mechanism, already used in `FOREACH_STAMP_BOUND_MODEL_CONST` and `FOREACH_FAILURE_MODE`.

### Compile-time enforcement

**Once the parser derives from the registry, "adding a cfg field" requires editing the registry.** There's no alternate parser site to bypass — the manually-maintained if-else chain is gone. This closes the parser_gap class structurally.

Additional guards:
- `static_assert(sizeof(CfgFieldDescriptor) <= 64)` enforces the cache-line budget for the descriptor.
- A `cfg_field_offset_table[]` (compile-time array of field offsets) lets the parser do `reinterpret_cast<T*>(cfg + offset)` without per-field if-chain dispatch.
- CI script (`tests/cfg_field_registry_audit.py`): greps `ControllerConfig.hpp` for `cfg.<X>` reads and verifies every X has a registry entry. Refuses commit otherwise.

---

## Robustness analysis

### What this closes

| Recurring gap class | Before | After |
|---|---|---|
| panel_gap | Manual field_defs[] edits; 123 missed in v5.12→v5.15 | Registry-driven; impossible to forget |
| parser_gap | Manual if-else chain; ~600 LOC | Registry-driven via tt:: dispatch |
| persist_gap | Manual fwrite/fread; drift from parser | Registry-driven via tt:: dispatch |
| per_core_gap | Manual per-field core_X[16] + core_X_override_set[16] | Auto-emit from PER_CORE_OK metadata flag |
| stamp_drift_gap | Separate FOREACH_STAMP_BOUND_CFG; drift from main | Unified via STAMP_BOUND metadata flag (or kept as PRE/POST split per item 22 if HMAC ordering matters) |

### What this enables

- **Future-flexibility for new Kinds.** Adding KIND_VEC3, KIND_ENUM_BITMAP, KIND_FPN_VEC: one tt:: specialization per Kind; no registry rewrites.
- **GUI panel layout via metadata.** HIDDEN_BY_DEFAULT auto-collapses "Engine Diagnostics" section. RESTART_REQUIRED auto-badges. SAFETY_CRITICAL auto-prompts.
- **Composition with per-core override pattern** (`per-bit-per-core-override-pattern.md`): PER_CORE_OK fields auto-emit override storage + branchless resolution.
- **Composition with slow-path cfg cache** (`slow-path-cfg-resolution-cache-pattern.md`): registry drives ResolvedCoreCfg field declarations + resolution body.

### Trade-offs

- **One-time migration cost:** ~600 LOC parser + ~1500 LOC panel field_defs + ~200 LOC save/load consolidate into ~200 LOC of AUTOPOPULATE walks + ~250 registry rows. Net LOC: NEGATIVE (~-1350 LOC). Effort: 2-3 days focused.
- **Macro debug pain:** misformed registry rows produce cryptic preprocessor errors. Mitigations:
  - Each row gets a `static_assert(strlen(#name) > 0, ...)` via metadata expansion (catches malformed names at compile).
  - Token-paste idioms via `EMIT_X_IF_<TOKEN>` use explicit token names (no anonymous `__VA_ARGS__`).
- **tt:: specializations exhaustiveness:** if a new Kind is added to the enum but tt:: specialization missing, COMPILE error (not link error) — Kind enum is used in template instantiation. Acceptable.

### When NOT to apply this pattern

- Single cfg field added to plug a one-off bug. (Registry overhead requires ≥3 entries per CLAUDE.md item 13 threshold.)
- Cfg fields with truly per-field bespoke parse logic (e.g., regex-driven). Either generalize the parse logic or special-case at the registry consumer.
- Cfg fields with INDIRECT storage (e.g., computed-from-N-other-fields). These belong in `Cfg_PostLoadSetup`, not the registry.

---

## Implementation checklist

When migrating a cfg field FROM manual TO registry-driven:

1. **Add registry row** to FOREACH_CFG_FIELD with correct Kind + metadata.
2. **Delete manual parser case** in CfgParser (if exists).
3. **Delete manual SettingsPanel entry** (if exists).
4. **Delete manual save/load line** (if exists).
5. **Verify per-core override** auto-emits if PER_CORE_OK set (look for `core_<name>[16]` in generated header).
6. **Verify drift check** auto-emits if STAMP_BOUND set.
7. **Build all 5 binaries** + run controller_test for registry parity.
8. **Add to `cfg.example`** the new field with comment from tooltip (or auto-generate cfg.example from registry — see Future Work).

When ADDING a new cfg field:

1. Pick the appropriate Kind.
2. Choose metadata flags (PER_CORE_OK / RESTART_REQUIRED / SAFETY_CRITICAL / etc.).
3. Add ONE registry row.
4. Done — parser, panel, save, per-core override, drift check all auto-flow.

---

## Future work (not in initial scope)

- **Auto-generate cfg.example** from registry tooltips. Closes a 7th gap class (cfg.example documentation drift).
- **Reverse drift check:** at boot, walk registry and verify Cfg struct has matching field names (catches Cfg refactors that miss registry update).
- **Cohort migration:** apply `cfg-flag-eligibility-criteria.md` cohort-audit at registry insertion time (e.g., new ridge_* sibling triggers existing ridge_* cohort review).
- **Composable with snapshot publish:** if a cfg field is also published per-cycle in PerCoreSnap, derive snapshot field declaration + populate from same registry (closes display↔execution invariant gap for new fields).

---

## Field-test plan

Stage migration in 3-4 sub-ships to keep PR sizes reviewable:

- **.F.4a** — Write this design spec + slow-path-cfg-resolution-cache spec + audit existing cfg fields (DONE in v5.15.5.F.4 plan)
- **.F.4b** — Implement FieldDescriptor + tt:: dispatchers + migrate KIND_DOUBLE + KIND_DOUBLE_PCT (~40 fields). Build all binaries; verify byte-identical cfg roundtrip.
- **.F.4c** — Migrate KIND_INT + KIND_INT_ENUM + KIND_BOOL (~80 fields).
- **.F.4d** — Migrate KIND_STRING + KIND_FILE_PATH + add metadata-driven GUI features (HIDDEN_BY_DEFAULT collapse, RESTART_REQUIRED badge).
- **.F.4e** — Migrate per-core override emission to PER_CORE_OK metadata.
- **.F.4f** — Migrate stamp drift check to STAMP_BOUND metadata; deprecate separate FOREACH_STAMP_BOUND_CFG (or keep as PRE/POST split per item 22 if HMAC ordering requires).

Each sub-ship is independently testable + rollback-able; the registry grows additively.
