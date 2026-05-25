---
type: refactor-pattern
stage: 2-draft
version: 1.1
established: 2026-05-18
last_amended: 2026-05-24
tags: [cross-tool-decoupling, structural-fix, framework-discipline, wire-format]
surface: [cross-tool, wire-format, ci-tooling]
sister_specs: [wire-format-byte-preservation-discipline.md, canonical-sister-extension-discipline.md, structural-fix-preferred-decision-framework.md]
applies_at_skills: []
---

> **Pattern status update (2026-05-24)**: Phase L first-canonical-application at v5.15.5.F.4d.1.B.3
> REVERTED. Reason: foxml_suite already stamps models in-process via
> `Backtest_RunFullValidation → Stamp_AssembleAndEmit` (cfg.auto_stamp_on_held_out_completion).
> Operator workflow doesn't require CLI binary for common case; bash CLI was edge-case-only
> infrastructure. Per `feedback_overengineering_boundary_when_future_easier` + YAGNI — pattern
> retained as DESIGN_SPEC; first canonical deferred to v5.16+ cmdline-invocable training when
> decoupling endgoal needs a true headless CLI (per `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`).
> Sister DELETED: `tools/stamp_model.sh` bash CLI + `tools/stamp_model_cli.cpp` C++ binary (no
> mirror; no maintenance burden; operator workflow via foxml_suite GUI button — queued for
> foxml_suite consolidation sub-sprint per `project_foxml_suite_refactor_queued`).

# Framework-driven CLI binary pattern (thin C++ wrapper over engine framework)

**Established:** 2026-05-18 (v5.15.5.F.4d.1.B.3 Phase L planning — codified during deep design conversation after `feedback_audit_canonical_sister_before_new_infra` + `feedback_motivated_collaborator_for_caramel` + `feedback_no_defer_for_effort` triangulated on the cross-tool seam at `tools/stamp_model.sh`)
**Status:** **Stage 2 DRAFT v1.1** (v1.1 amendment 2026-05-18 expands v1.0 per `/precoding-audit-gate` 6-audit fire findings: NEW section "X-macro auto-gen of CLI flag table" — eliminates Class 21 at CLI INTERFACE LAYER (longopts[] + value-receiver struct + parse dispatch auto-generated from FOREACH_*_CFG_FIELD walkers; sister to engine's emit walker discipline); NEW section "Extensibility test pattern" — X-macro walker synthesizes value per flagged row + validates round-trip byte-identity (closes test recurrence vector; sister codified at `cfg-derived-consumer-framework.md` v1.3); NEW `## Audit detection` section per `pattern-codification-lifecycle.md` Stage 2 discipline; FIX stale include path `FixedPoint/FPN.hpp` → `FixedPoint/FixedPoint64.hpp`. v1.0 → v1.1) (Stage 3 first canonical reference = `tools/stamp_model_cli.cpp` at `.B.3` ship close; replaces `tools/stamp_model.sh` which has tracked 6+ cross-tool sync events across versions v5.2.3 / v5.8.8 / v5.9.3b / v5.9.4a / v5.9.5c / v5.11.18a — well over the 4× recurrence threshold per `structural-fix-preferred-decision-framework.md` § Step 2 → STRUCTURAL FIX MANDATORY)
**Tags:** framework-discipline, structural-fix, cross-tool, cli-binary, wire-format, registry-driven, future-easier; closes Class 18 + 19 + 21 + 22 at cross-tool surface; sister to Layer 7 cross-tool emit-site enumeration discipline (Layer 7 codifies DISCIPLINE; this pattern provides STRUCTURAL ELIMINATION at framework-driven surfaces); composes with `cfg-derived-consumer-framework.md` (this pattern IS a new consumer of the framework — CLI binary calls framework API directly, no mirror)

**Cross-references:**
- Sister discipline: `wire-format-byte-preservation-discipline.md` Layer 7 (cross-tool emit-site enumeration) — Layer 7 codifies discipline for cross-tool surfaces; this pattern is the STRUCTURAL FIX that obviates Layer 7 at framework-driven surfaces. Layer 7 still applies for cross-tool surfaces that can't use the framework (e.g., bash diagnostic tools, codegen tooling)
- Composes with: `cfg-derived-consumer-framework.md` v1.2 (this pattern is a new consumer of the framework — CLI is THIN wrapper over `populate_stamp_cfg_from_derived` + sister framework APIs)
- Composes with: `autopopulate-pattern-for-production-caller-class.md` (existing framework API uses AUTOPOPULATE; CLI binary inherits)
- Composes with: `meta-registry-pattern-for-codebase-registry-discipline.md` (CLI binary tool may enroll in `FOREACH_REGISTRY` if it carries its own registry; typical CLI binaries don't)
- Parent discipline: `canonical-sister-extension-discipline.md` (this pattern WAS proposed via the discipline's audit — bash↔C++ mirror caught at /merge-scan + Layer 7 cross-tool enumeration)
- Sister tools: `tools/compare_scalers.cpp` (existing standalone C++ tool — DIFFERENT concern; doesn't use engine framework; sister precedent in tools/ dir for C++ tool builds via CMake)
- Memory: `feedback_motivated_collaborator_for_caramel.md` (best-software discipline applied here)
- Memory: `feedback_no_defer_for_effort.md` (the rule that caught my initial `.B.4`-split-as-deferral and triggered the structural-fix recommendation)
- Memory: `feedback_audit_canonical_sister_before_new_infra.md` (the producer-side discipline applied during this spec's drafting)
- Memory: `feedback_structural_fix_for_recurring_class.md` (recurring class structural-fix discipline; 6+ recurrence count at `tools/stamp_model.sh`)
- Bug classes closed: Class 18 (mirror state/code) + Class 19 (hardcoded instance names) + Class 21 (multiple parallel descriptors) + Class 22 (runtime cfg gating scattered) — ALL at cross-tool surface for framework-driven workflow tools
- CLAUDE.md item 31 (framework-driven extensibility meta-principle)
- CLAUDE.md item 19 (structural fix preferred when bug class can recur)
- `structural-fix-preferred-decision-framework.md` § "Structural fix (4+ occurrences; mandatory)" — recurrence count gating applied
- Decoupling positioning: `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` "Training entry points" axis (GUI button → execv child via FOREACH_CLI_MODE registry); this pattern IS a precedent for the FOREACH_CLI_MODE registry's eventual instantiation

---

## Problem statement

Some workflows need a CLI surface for operations the engine performs internally (e.g., signing a model file with HMAC after post-training validation; rebuilding a stamp from operator-supplied metrics; offline schema migration). These workflows historically get implemented as **bash scripts** because:

- Quick to prototype
- No build dependency on engine
- Operator-readable

The COST emerges over time. Whenever the engine's wire format / cfg schema / behavior changes, the bash script must be **manually re-synchronized** to stay parity-compatible with the C++ runtime. Each cfg field added with stamp-binding = new bash flag + new emit logic + new format string. Each version bump = new version literal in bash. Each key rename = grep + replace in bash. The bash script becomes a **mirror** of the engine's wire emit logic — Class 18 (mirror state/code) + Class 21 (multiple parallel descriptors).

**Evidence at FoxML_Trader_v2 — `tools/stamp_model.sh`:**

Script header explicitly notes (line 12, since v5.2.3): *"Phase 2 (v5.3.x?) replaces this with `tools/stamp_model.cpp` that runs validation directly from CLI."* Phase 2 was planned years ago.

Cross-tool sync events documented in script history:
- v5.8.8 — `--feature-registry-hash` + `--engine-version` added
- v5.9.3b — `--feature-scaler-present` + `--scaler-sha256` added
- v5.9.4a — `--model-num-outputs` added
- v5.9.5c — 9 more flags for inference cfg parity
- v5.11.18a — `--feature-mask` added
- v5.14.x — various cohort tracking
- v5.15.5.F.4d.1.B.3 — 6 wire-key renames + version literal bump + orphan delete (currently planned)

**6+ recurrence count.** Per `structural-fix-preferred-decision-framework.md`: at 4+ occurrences, structural fix is MANDATORY. Direct-patching the 7th, 8th, 9th sync event wastes time + the bug class WILL recur.

The framework consolidation that landed at `.B` series (FOREACH_STAMP_BOUND_DERIVED_COHORT meta-walker + `populate_stamp_cfg_from_derived` + sister consumers) provides the structural foundation: the C++ engine has ONE single-source-of-truth wire emit path. The structural fix at the cross-tool layer is to make the CLI tool USE that path directly instead of mirroring it.

---

## Design space explored

### Option α (chosen): Replace bash with C++ CLI binary that calls framework API directly

```
+----------------+         +----------------+         +----------------+
| stamp_model_   |         | stamp_write_   |         |  framework API |
|  cli (C++)     | ──call─►| for_model      | ──uses─►| (populate_     |
|  (CLI wrapper) |         | (engine API)   |         |  stamp_cfg_*)  |
+----------------+         +----------------+         +----------------+
```

The CLI is a **thin wrapper** (~150-200 LOC):
1. Parse CLI flags
2. Construct `ControllerConfig<64>` from flags (or read from engine.cfg)
3. Construct `StampInferenceCfgInputs` / `ModelStampResult` equivalents
4. Call existing `stamp_write_for_model(...)` from `ML_Headers/ModelInference.hpp` OR `Stamp_AssembleAndEmit(...)` from `ML_Headers/StampHelper.hpp`
5. Output the .stamp file

**No drift possible by construction** — CLI uses framework, doesn't mirror it. Adding a new cfg field with stamp-binding = 1 row in master FOREACH_PER_CORE_CFG_FIELD → framework auto-flows → CLI inherits for free.

### Option β: Python codegen tool emits bash from FOREACH_*_CFG_FIELD

Parse C++ headers via clang AST or regex; emit equivalent bash logic to a derived `tools/stamp_model.gen.sh`.

**Rejected.** Adds maintenance surface (python codegen + build-time step). Bash file becomes derived artifact (operator can't read directly without inferring from codegen). More moving parts than α. Doesn't preserve the goal of "operator-readable script" because the script is now generated. And clang-AST-parsing of FOREACH X-macros is fragile (preprocessor + template-heavy code).

### Option γ: Keep bash; add CI check `tools/check_bash_stamp_parity.py`

Python script compares wire keys emitted by engine (via grep of FOREACH_PER_CORE_CFG_FIELD + STAMP_BOUND_CFG_DERIVED filter) vs bash script's emit lines. Flag drift at PR/CI time.

**Rejected.** Catches drift POST-implementation; doesn't eliminate the seam. Operator must STILL manually sync bash on every cfg field add; CI just catches when they forget. Inferior structural close. **Acceptable as DEFENSE IN DEPTH alongside α (e.g., post-α-migration, the CI check verifies bash deprecation is complete + no NEW bash scripts emit wire format).**

### Option δ: Eliminate CLI surface entirely (suite-only workflow)

Move the stamp-signing workflow into `foxml_suite` GUI panel + remove the CLI entry point.

**Partial accept.** Operator workflow includes CLI signing of pre-validated models (script header line ~30: *"you've already run walk-forward + held-out validation in `foxml_suite` and have the metric numbers in hand. This script just signs them."*). Removing the CLI surface forces the operator into the GUI for signing. Reasonable IF the GUI surface fully replaces the CLI; not reasonable IF the CLI is scriptable/automatable use case. **Hybrid with α: CLI surface preserved via C++ binary; same operator workflow; framework underneath.**

### Option ε: Shared library `.so`; bash wraps the lib

Extract framework into `libfoxml_stamp.so`; bash uses `ldopen` or links via a small invoker.

**Rejected.** Adds `.so` build target complexity. Bash wrapping a `.so` is awkward (FFI-style; not idiomatic). α achieves the same goal (use framework) without the indirection.

### Option ζ: Schema-driven wire format (JSON/YAML/protobuf)

Make wire format schema-driven; both languages agree on schema.

**Rejected.** Biggest refactor (changes wire format + breaks legacy stamp HMAC verification). Current wire format is text-line key=value with `%.17g` precision; HMAC-friendly + human-readable. Changing it loses both properties for the benefit of cross-language schema sharing. **Cost/benefit doesn't justify** for stamp body workflow.

### Verdict: α (with δ hybrid for workflow preservation)

α is the structural fix per the framework. CLI surface preserved (operator workflow continuity); framework drives the wire emit (no drift possible).

---

## The pattern (concrete shape)

### Step 1: Identify the workflow + framework API

For stamp model signing:
- **Workflow:** post-training, operator has metrics → signs model file with HMAC stamp
- **Framework API:** `stamp_write_for_model(model_path, secret, format_version, trained_on, wf_mean_val, held_out_metric, gap_threshold, force, feature_registry_hash, engine_version, inf)` at `ML_Headers/ModelInference.hpp`

The CLI must:
- Accept all operator-controllable parameters as CLI flags
- Construct the framework API's input types (ControllerConfig, StampInferenceCfgInputs)
- Invoke the framework API
- Return exit code based on success/failure

### Step 2: Build the CLI binary

```cpp
// tools/stamp_model_cli.cpp
//
// Pattern: framework-driven-cli-binary-pattern.md Stage 3 first canonical
// (replaces tools/stamp_model.sh — closes Class 18/19/21/22 at cross-tool surface).

#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <getopt.h>

#include "../CoreFrameworks/ControllerConfig.hpp"
#include "../ML_Headers/ModelInference.hpp"    // stamp_write_for_model
#include "../ML_Headers/StampHelper.hpp"       // Stamp_AssembleAndEmit (optional)
#include "../FixedPoint/FixedPoint64.hpp"      // FPN_FromDouble<64> + FPN_ToDouble (verified filename at HEAD per /trace-deps HIGH-3)

int main(int argc, char** argv) {
    // Parse CLI flags via getopt_long (or sister parser).
    // Flag names MATCH tools/stamp_model.sh for operator workflow continuity.
    const char* model_path = nullptr;
    const char* secret = nullptr;
    double wf_mean_val = 0.0;
    double held_out_metric = 0.0;
    double gap_threshold = 0.0;
    /* ... all CLI-controllable parameters ... */

    static struct option longopts[] = {
        {"model",                       required_argument, 0, 'm'},
        {"secret",                      required_argument, 0, 's'},
        {"wf-mean-val",                 required_argument, 0, 'w'},
        {"held-out-metric",             required_argument, 0, 'h'},
        {"gap-threshold",               required_argument, 0, 'g'},
        /* ... per-cfg flags inherit naming from bash script for operator continuity ... */
        {0, 0, 0, 0}
    };

    /* ... parse loop ... */

    // Construct ControllerConfig from CLI flags + engine.cfg defaults.
    ControllerConfig<64> cfg = ControllerConfig_Default<64>();
    if (have_ridge_lambda) cfg.ridge_lambda = FPN_FromDouble<64>(ridge_lambda);
    /* ... per-cfg field assignments from CLI flags ... */

    // Construct StampInferenceCfgInputs equivalents (model-state side).
    StampInferenceCfgInputs inf{};
    inf.has_feature_registry_hash = (feature_registry_hash != 0);
    if (inf.has_feature_registry_hash) inf.feature_registry_hash = feature_registry_hash;
    /* ... model-state side per-field setup ... */

    // INVOKE FRAMEWORK API directly. No drift possible — same code path as engine.
    StampWriteResult r = stamp_write_for_model(
        model_path, secret, format_version, trained_on_iso,
        wf_mean_val, held_out_metric, gap_threshold,
        force, feature_registry_hash, engine_version, &inf);

    if (r.ok != 1) {
        fprintf(stderr, "stamp_model_cli: %s\n", r.error);
        return 1;
    }

    fprintf(stderr, "stamp_model_cli: wrote %s\n", r.stamp_path);
    return 0;
}
```

Key points:
- **CLI flag interface matches bash script** for operator continuity (sister to `feedback_surface_operator_migration_path_proactively`)
- **Direct framework API call** — no mirror; no drift
- **ControllerConfig + StampInferenceCfgInputs** constructed from CLI flags using same types engine uses
- **Locale handling** inherited from framework (`stamp_write_for_model` does internal `LC_NUMERIC=C` pin)

### Step 2.5: X-macro auto-gen of CLI flag table + value-receiver + parse dispatch (NEW v1.1)

**Problem (caught by /precoding-audit-gate at v1.0):** Step 2's CLI binary construction sketch describes ControllerConfig construction "from operator-provided CLI flags" but doesn't address HOW the flag list is maintained. The naive approach is a manual `static struct option longopts[]` array enumerating each cfg field. **That's Class 21 (multiple parallel descriptors) at the CLI INTERFACE LAYER** — a parallel descriptor of FOREACH_PER_CORE_CFG_FIELD that requires manual sync whenever a new cfg field with stamp-binding is added. Phase L's wire-emit-via-framework closure (Step 2 above) eliminates Class 21 at the WIRE EMIT layer but leaves it alive at the CLI INTERFACE layer.

**Structural fix:** X-macro auto-gen the CLI flag table FROM the same registries that drive wire emit. Sister discipline to engine's `populate_stamp_cfg_from_derived` walker — both consume FOREACH_*_CFG_FIELD; both auto-flow.

```cpp
// X-macro extractors per registry signature shape:

// For per_core / global cfg fields (13-tuple FOREACH_*_CFG_FIELD sig):
#define X_GEN_LONGOPT_CFG(STORAGE_T, KIND_TOKEN, name, label, section, meta, payload, tooltip, applies_strat, applies_op, applies_regime, applies_risk, lives_in_struct) \
    if constexpr (((meta) & CfgFieldDescriptor::STAMP_BOUND_CFG_DERIVED) != 0) { \
        /* emit longopts row at compile time via constexpr append OR inline if-constexpr filter */ \
    }

// Practical approach: emit ALL rows; filter at parse time via descriptor metadata bit.
// Avoids if-constexpr compile-time filter on static array initializers (C++ doesn't support).
#define X_GEN_LONGOPT_ALL_CFG(STORAGE_T, KIND_TOKEN, name, label, section, meta, payload, tooltip, applies_strat, applies_op, applies_regime, applies_risk, lives_in_struct) \
    {#name, required_argument, 0, 0},

// For bitmap-bool registries (6-tuple FOREACH_ML/GATE_CFG_FLAG sig):
#define X_GEN_LONGOPT_BITMAP(NAME, legacy_field, display_label, section, metadata_flags, doc) \
    {#legacy_field, required_argument, 0, 0},

// For FOREACH_STAMP_BOUND_MODEL_CONST (9-tuple sig; unfiltered architectural constants):
#define X_GEN_LONGOPT_MC(name, group, presence, type, fmt, default_val, get_value, emit_when, doc) \
    {#name, required_argument, 0, 0},

static struct option longopts[] = {
    // Workflow flags (CLI-only; hardcoded — not registry-driven)
    {"model",           required_argument, 0, 'm'},
    {"secret",          required_argument, 0, 's'},
    {"wf-mean-val",     required_argument, 0, 0},
    {"held-out-metric", required_argument, 0, 0},
    {"gap-threshold",   required_argument, 0, 0},
    {"trained-on",      required_argument, 0, 0},
    {"format-version",  required_argument, 0, 0},
    {"force",           no_argument,       0, 'f'},

    // Auto-gen from cfg-derived cohort (all rows; filter applied at parse-dispatch time via descriptor.metadata_flags)
    FOREACH_PER_CORE_CFG_FIELD(X_GEN_LONGOPT_ALL_CFG)
    FOREACH_GLOBAL_CFG_FIELD(X_GEN_LONGOPT_ALL_CFG)
    FOREACH_ML_CFG_FLAG(X_GEN_LONGOPT_BITMAP)
    FOREACH_GATE_CFG_FLAG(X_GEN_LONGOPT_BITMAP)

    // Auto-gen from model-const cohort (unfiltered architectural constants)
    FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG(X_GEN_LONGOPT_MC)
    FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG(X_GEN_LONGOPT_MC)

    {0, 0, 0, 0}  // sentinel
};

#undef X_GEN_LONGOPT_ALL_CFG
#undef X_GEN_LONGOPT_BITMAP
#undef X_GEN_LONGOPT_MC
```

**Value-receiver struct (parallel X-macro discipline):**

```cpp
struct CliReceived {
    // workflow flags (hardcoded)
    const char* model_path = nullptr;
    const char* secret = nullptr;
    /* ... etc ... */

    // cfg-derived cohort — auto-gen has_*+value per field
    #define X_GEN_CLI_FIELD(STORAGE_T, KIND_TOKEN, name, label, section, meta, payload, tooltip, applies_strat, applies_op, applies_regime, applies_risk, lives_in_struct) \
        uint8_t has_##name = 0; STORAGE_T name = {};
    FOREACH_PER_CORE_CFG_FIELD(X_GEN_CLI_FIELD)
    FOREACH_GLOBAL_CFG_FIELD(X_GEN_CLI_FIELD)
    #undef X_GEN_CLI_FIELD

    #define X_GEN_CLI_BITMAP(NAME, legacy_field, display_label, section, metadata_flags, doc) \
        uint8_t has_##legacy_field = 0; int legacy_field = 0;
    FOREACH_ML_CFG_FLAG(X_GEN_CLI_BITMAP)
    FOREACH_GATE_CFG_FLAG(X_GEN_CLI_BITMAP)
    #undef X_GEN_CLI_BITMAP

    /* model-const cohort similarly */
};
```

**Per-flag parse dispatch via `tt::cfg_parse_field<T>`:**

```cpp
void cli_args_dispatch(const char* flag_name, const char* optarg, CliReceived& args) {
    // Walk the registries; per-row strcmp dispatch (sister to existing cfg_derived::parse_stamp_cfg_to_derived).

    #define X_DISPATCH_CFG(STORAGE_T, KIND_TOKEN, name, label, section, meta, payload, tooltip, applies_strat, applies_op, applies_regime, applies_risk, lives_in_struct) \
        if (strcmp(flag_name, #name) == 0) { \
            constexpr size_t _idx = FIELD_IDX_PER_CORE_##name; \
            tt::cfg_parse_field(args.name, g_per_core_cfg_field_descriptors[_idx], optarg); \
            args.has_##name = 1; \
            return; \
        }
    FOREACH_PER_CORE_CFG_FIELD(X_DISPATCH_CFG)
    #undef X_DISPATCH_CFG

    /* Sister X-macros for GLOBAL / ML_CFG_FLAG / GATE_CFG_FLAG / MC_PRE / MC_POST */
}
```

**Apply received args to cfg + inf:**

Per `/blindspot-scan` v1.15 B8 finding: `cfg.name = args.name` MUST filter rows flagged NO_FLAT_FIELD (e.g., `strategy` row at HEAD has NO_FLAT_FIELD bit; no `cfg.strategy` scalar exists — compile fail without filter). Sister precedent: `ControllerConfig.hpp:1447-1454` uses `if constexpr (!((meta) & NO_FLAT_FIELD))` filter. Per `/blindspot-scan` v1.15 B11-ALT: `apply_cli_args_to_cfg` must be template-parameterized on `unsigned F` for FPN<F> dispatch (sister to `populate_inference_cfg_from_derived<F, InfT>`).

```cpp
template <unsigned F>
void apply_cli_args_to_cfg(const CliReceived& args, ControllerConfig<F>& cfg) {
    #define X_APPLY_CFG(STORAGE_T, KIND_TOKEN, name, label, section, meta, payload, tooltip, applies_strat, applies_op, applies_regime, applies_risk, lives_in_struct) \
        if constexpr (!((meta) & CfgFieldDescriptor::NO_FLAT_FIELD)) { \
            if (args.has_##name) cfg.name = args.name; \
        }
    FOREACH_PER_CORE_CFG_FIELD(X_APPLY_CFG)
    FOREACH_GLOBAL_CFG_FIELD(X_APPLY_CFG)
    #undef X_APPLY_CFG

    /* Sister X-macros for ML/GATE_CFG_FLAG — set bitmap bit if args.has_<flag>:
     *   if (args.has_<legacy_field>) {
     *       if (args.<legacy_field>) BITMAP_SET(cfg.ml_cfg_flags, MASK_ML_CFG_<NAME>);
     *       else                     BITMAP_CLR(cfg.ml_cfg_flags, MASK_ML_CFG_<NAME>);
     *   }
     */
}

template <unsigned F>
void apply_cli_args_to_inf(const CliReceived& args, StampInferenceCfgInputs& inf) {
    /* Sister X-macros for MC_PRE/POST — apply directly to inf.<name>; inf has all
     * fields auto-genned via STAMP_RESULT_DERIVED_FIELDS_AUTO_GEN per cfg-derived-
     * consumer-framework.md v1.2 § "Action-parameterized meta-walker". */
}

int main(int argc, char** argv) {
    /* parse loop … */
    ControllerConfig<64> cfg = ControllerConfig_Default<64>();
    StampInferenceCfgInputs inf{};
    apply_cli_args_to_cfg<64>(args, cfg);
    apply_cli_args_to_inf<64>(args, inf);

    // Then call framework API directly:
    StampWriteResult r = stamp_write_for_model(args.model_path, args.secret, /* ... */, &inf);
}
```

**B13 cross-walker longopts[] collision resolution** (per `/blindspot-scan` v1.15 finding): 3 names appear in BOTH FOREACH_GLOBAL_CFG_FIELD AND FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG at HEAD (`xgb_min_child_weight` / `xgb_seed` / `xgb_train_nthread`). Existing sister sidecar `FOREACH_STAMP_RESULT_FIELD_EXCLUSION` at `MemHeaders/CfgGateRegistry.hpp:512-515` already excludes these 3 names at struct-gen layer (per H18 SIDECAR OVERRIDE pattern + Pillar B13). **REUSE the same sidecar at longopts[] auto-gen layer:** cfg walker (`X_GEN_LONGOPT_ALL_CFG`) wraps each row with `#define/#undef` redirect bracket; excluded names redirect to dead `_longopts_excluded_<name>` macro (zero bytes emitted). MC walker emits authoritative entry per architectural-constant semantic. Future cross-walker collisions = add 1 row to existing sidecar + 2 #define/#undef lines per consumer site (struct-gen + longopts[]). Bounded scope; CI check (TECH_DEBT-111) detects new collisions.

**Drift impossibility by construction:**

- Adding a new cfg field with stamp-binding to FOREACH_PER_CORE_CFG_FIELD = `--<name>` flag auto-appears in longopts[] at next compile
- Value-receiver struct field auto-gens; parse dispatch auto-dispatches; apply-to-cfg auto-applies
- **Operator capability: `tools/stamp_model_cli --new_field=value` works immediately after registry row added; no CLI code edit required**
- Compile error if registry row's STORAGE_T doesn't have a matching tt::cfg_parse_field<T> branch — same discipline as engine

**Naming convention:**

Registry uses `snake_case` field names. CLI flag = `--<snake_case>` direct mapping. If operator scripts hardcoded `--kebab-case` flags (some bash scripts do this), provide a deprecation alias layer at the CLI binary main() — translates `--kebab-case` → `--snake_case` with warning emitted. Per `feedback_surface_operator_migration_path_proactively`.

**Sister patterns this composes with:**

- `x-macro-registry-with-presence-dispatch.md` § Y3 dispatch (token-paste registry name → emit longopts entry)
- `autopopulate-pattern-for-production-caller-class.md` (CLI flag auto-gen IS the CLI's AUTOPOPULATE companion at flag interface layer; sister to existing AUTOPOPULATE at value-population layer)
- `cross-walker-struct-field-uniqueness-discipline.md` (parallel X-macro discipline for struct field uniqueness)

### Step 3: Build system integration

Add to `build.sh` + `CMakeLists.txt`:

```cmake
# tools/stamp_model_cli — framework-driven CLI binary (replaces tools/stamp_model.sh).
# Pattern: framework-driven-cli-binary-pattern.md.
add_executable(stamp_model_cli tools/stamp_model_cli.cpp)
target_link_libraries(stamp_model_cli PRIVATE
    # Framework dependencies (same as engine):
    # — pthread, crypto (HMAC), etc.
)
target_include_directories(stamp_model_cli PRIVATE
    ${CMAKE_SOURCE_DIR}
)
```

Built alongside `engine` / `engine_gui` / `foxml_suite` / etc. Same compile flags + dependencies.

### Step 4: Deprecate the bash script

Two options:
- **Deprecation notice + symlink:** keep `tools/stamp_model.sh` but make it a 1-line shim that invokes `tools/stamp_model_cli` with same flags. Operator scripts/aliases that invoke the bash script continue working.
- **Direct delete:** remove `tools/stamp_model.sh`; document the change in CHANGELOG.

**Recommend: Deprecation notice + 1-line shim for ≥1 ship cycle, then delete.** Smooth operator migration; matches Decision F SOFT compat philosophy.

```bash
#!/bin/bash
# tools/stamp_model.sh — DEPRECATED; redirects to tools/stamp_model_cli.
#
# v5.15.5.F.4d.1.B.3 Phase L: bash script replaced with framework-driven C++ CLI
# (closes Class 18/19/21/22 at cross-tool surface). See:
# - DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md
# - tools/stamp_model_cli.cpp
#
# This shim preserves operator workflow continuity. Delete after `.B.N` (TBD per
# TECH_DEBT-110).

exec "$(dirname "$0")/../build/stamp_model_cli" "$@"
```

### Step 5: Verification — round-trip + extensibility (EXPANDED v1.1)

**5.1 — Round-trip test (engine-side; per ship):** Confirms structural close at THIS ship's flagged-row set:

```cpp
// In tests/controller_test.cpp (or new tests/stamp_model_cli_test.cpp).
{
    // 1. Stamp a model via CLI binary (subprocess call).
    int rc = system("./build/stamp_model_cli --model /tmp/test_model "
                    "--secret test --wf-mean-val 0.5 --held-out-metric 0.48 "
                    "--gap-threshold 0.05 --format-version 6");
    check("stamp_model_cli: exit code 0", rc == 0);

    // 2. Verify the stamp via engine verify_model_stamp.
    ModelStampResult sr = verify_model_stamp("/tmp/test_model.stamp", "test", 0.05, 6);
    check("stamp_model_cli: HMAC verifies", sr.valid == 1);

    // 3. Round-trip: stamp same model via engine in-process; compare canonical body bytes.
    /* ... */
    check("stamp_model_cli: canonical body byte-identical to engine in-process emit",
          memcmp(cli_body, engine_body, n) == 0);
}
```

**5.2 — Extensibility test pattern (NEW v1.1; structural close for test recurrence vector):**

The manual round-trip test enumerates each field explicitly (e.g., `controller_test.cpp` v5.14.1.B.3.E section listed 17 fields with per-field set + emit + parse + assert blocks). **That's Class 21 at the TEST LAYER** — manual sync of test enumeration when new flagged rows are added. The structural fix: X-macro walker that synthesizes value per flagged row + runs stamp emit/parse + validates round-trip byte-identity per row. Adding a new flagged row = test auto-validates that row's round-trip; no test code edit required.

```cpp
// Per-type synthetic value generator (deterministic per field-name hash).
// Coverage: every STORAGE_T variant in tt:: family (per check_storage_t_coverage.py at HEAD: 7 variants)
// MUST have a branch + a dependent-type static_assert in the else for compile-time unreachable enforcement.
// Per /blindspot-scan v1.15 B6 finding: missing `is_floating_point_v<T>` (raw double — appears in PER_CORE
// per check_storage_t_coverage.py) + `is_array_v<T>` (char[N] forward-compat) + proper static_assert in else.
template <typename T>
T synthetic_value_for_field(const char* field_name) {
    uint64_t h = tt::fnv1a_64(field_name, strlen(field_name));
    if constexpr (is_FPN_v<T>) {
        // Deterministic FPN<F> value in [0.001, 1.001) range
        return FPN_FromDouble<64>((double)(h % 1000) / 1000.0 + 0.001);
    } else if constexpr (std::is_floating_point_v<T>) {
        // Raw double/float STORAGE_T (e.g., per_core fee/slippage fields if present)
        return T((double)(h % 1000) / 1000.0 + 0.001);
    } else if constexpr (std::is_same_v<T, bool>) {
        return (h & 1) != 0;
    } else if constexpr (std::is_integral_v<T>) {
        // Order matters: bool check before integral check (bool is integral in C++)
        return T((h % 100) + 1);
    } else if constexpr (std::is_array_v<T>) {
        // char[N] / tt::stamp_str_N — generate deterministic string fitting buffer
        T result{};
        const char* charset = "abcdefghijklmnopqrstuvwxyz0123456789";
        constexpr size_t cap = std::extent_v<T> - 1;  // leave room for \0
        for (size_t i = 0; i < cap; i++) result[i] = charset[(h >> (i * 4)) % 36];
        return result;
    } else {
        // Dependent-type static_assert: triggers only when this branch instantiates
        // (i.e., a new STORAGE_T variant entered the registry without adding a branch here).
        // Sister discipline to check_storage_t_coverage.py — that CI tool catches missing
        // tt::cfg_parse_field<T> branches; this static_assert catches missing
        // synthetic_value_for_field<T> branches at first instantiation.
        static_assert(!std::is_same_v<T, T>,
                      "extend synthetic_value_for_field<T> with branch for new STORAGE_T; "
                      "sister discipline to check_storage_t_coverage.py for tt::cfg_*_field<T>");
    }
}

// Helper: deterministic equality check (FPN_ToDouble where applicable)
template <typename T>
bool values_equal(const T& a, const T& b) {
    if constexpr (is_FPN_v<T>) {
        return FPN_ToDouble(a) == FPN_ToDouble(b);  // bit-exact double comparison
    } else {
        return a == b;
    }
}

// Extensibility test (lives in controller_test.cpp; replaces v5.14.1.B.3.E manual block):
{
    SECTION("extensibility: STAMP_BOUND_CFG_DERIVED cohort round-trip");

    ControllerConfig<64> cfg = ControllerConfig_Default<64>();

    // Walk all flagged rows; synthesize value per row; set cfg field.
    #define X_SYNTH_POPULATE_PER_CORE(STORAGE_T, KIND_TOKEN, name, label, section, meta, payload, tooltip, applies_strat, applies_op, applies_regime, applies_risk, lives_in_struct) \
        if constexpr (((meta) & CfgFieldDescriptor::STAMP_BOUND_CFG_DERIVED) != 0) { \
            cfg.name = synthetic_value_for_field<STORAGE_T>(#name); \
        }
    FOREACH_PER_CORE_CFG_FIELD(X_SYNTH_POPULATE_PER_CORE)
    #undef X_SYNTH_POPULATE_PER_CORE

    /* Sister X-macros for GLOBAL / ML_CFG_FLAG / GATE_CFG_FLAG */

    // Set cohort gate bits so all flagged rows pass emit_when filter
    cfg.ml_cfg_flags = MASK_ML_CFG_RIDGE_WITHIN_HORIZON | MASK_ML_CFG_RIDGE_ACROSS_HORIZONS
                     | MASK_ML_CFG_CONFIDENCE_COMPOSITE_ENABLED;
    cfg.gate_cfg_flags = MASK_GATE_CFG_BARRIER_GATE_ENABLED;
    cfg.bandit_algorithm = 1;  // Thompson active
    cfg.risk_degradation_curve = 1;  // LINEAR active

    // Build stamp + verify
    char tmp_model[] = "/tmp/foxml_extensibility_XXXXXX";
    int fd = mkstemp(tmp_model); write(fd, "x", 1); close(fd);

    StampInferenceCfgInputs inf{};
    INFERENCE_CFG_POPULATE_FROM_DERIVED(inf, cfg);
    StampWriteResult sw = stamp_write_for_model(tmp_model, "test", /* ... */, &inf);
    check("extensibility: stamp written", sw.ok == 1);

    ModelStampResult sr = verify_model_stamp(tmp_model, "test", /* ... */);
    check("extensibility: HMAC verifies", sr.valid == 1);

    // Walk again; validate per-row round-trip byte-identity.
    #define X_VALIDATE_ROUNDTRIP_PER_CORE(STORAGE_T, KIND_TOKEN, name, label, section, meta, payload, tooltip, applies_strat, applies_op, applies_regime, applies_risk, lives_in_struct) \
        if constexpr (((meta) & CfgFieldDescriptor::STAMP_BOUND_CFG_DERIVED) != 0) { \
            check("extensibility: " #name " has_*=1 after round-trip", sr.has_##name == 1); \
            check("extensibility: " #name " value round-trips byte-identical", \
                  values_equal(sr.name, cfg.name)); \
        }
    FOREACH_PER_CORE_CFG_FIELD(X_VALIDATE_ROUNDTRIP_PER_CORE)
    #undef X_VALIDATE_ROUNDTRIP_PER_CORE

    /* Sister X-macros for GLOBAL / ML_CFG_FLAG / GATE_CFG_FLAG */

    char stamp_path[1024]; snprintf(stamp_path, sizeof(stamp_path), "%s.stamp", tmp_model);
    unlink(stamp_path); unlink(tmp_model);
}
```

**Drift impossibility at TEST LAYER:** Adding a new STAMP_BOUND_CFG_DERIVED-flagged row = test walker auto-validates it round-trips. No test code edit required. If round-trip fails for ANY flagged row (e.g., new STORAGE_T not handled by tt::cfg_emit_field; FPN precision edge case; missing has_* parsing), the test FAILS the build at CI time — caught before any operator hits the bug.

**Sister pattern:** The extensibility test pattern is REGISTRY-AGNOSTIC. Applies to ANY cfg-derived consumer cohort. Codified separately in `cfg-derived-consumer-framework.md` v1.3 § "Extensibility test pattern for cohort consumers" so future canonical applications (e.g., FOREACH_STAMP_BOUND_MODEL_CONST cohort) inherit the pattern without re-inventing.

**5.3 — Layer 5b CLI emit invariants test (NEW v1.1):**

Extend `tests/wire_format_invariants.hpp` I1-I5 structural invariants to ALSO test the CLI binary's emit path. Sister to existing engine-side Layer 5b test; same I1-I5 invariants apply to both emit paths (line count == popcount; format consistency; locale pin; row presence; canonical order). CLI emit produces canonical body bytes via framework call — invariants should hold by construction; this test catches any regression from build-system-induced compile flag drift or include topology change.

### Step 6: Document the pattern + enroll

- Add DESIGN_SPEC entry (this doc) to `DESIGN_SPECS/README.md` catalog
- Cross-reference `wire-format-byte-preservation-discipline.md` Layer 7 (note that Layer 7 still applies for non-framework-driven cross-tool surfaces)
- Add CLAUDE.local.md going-forward rule pointer
- TECH_DEBT-110 entry: bash script shim deletion target ship

---

## Trade-offs + when to apply

### Apply when:

- Cross-tool surface produces wire format that mirrors an in-process emit path
- Recurrence count ≥ 3 (cross-tool drift has happened 3+ times) per `structural-fix-preferred-decision-framework.md`
- Engine framework provides single-source-of-truth API (e.g., `populate_stamp_cfg_from_derived` exists + handles the relevant cfg surface)
- CLI surface is operator-load-bearing (workflow involves running the tool from shell)
- Build system can accommodate another C++ binary target

### Skip when:

- Cross-tool surface is one-off (e.g., a debugging script that emits non-wire-format diagnostics; doesn't drift against engine)
- Engine framework doesn't have a corresponding API (cross-tool concern doesn't have a framework consumer)
- CLI surface is internal-only (no operator workflow continuity concern; can be a foxml_suite GUI panel instead)
- Recurrence count < 3 (per `structural-fix-preferred-decision-framework.md` § Step 2 — don't structural-fix without recurrence evidence)

### Cost:

- ~150-300 LOC C++ CLI binary (thin wrapper)
- ~10-20 LOC CMake target + build system integration
- ~50-100 LOC verification tests (round-trip + workflow replication)
- ~1 deprecation shim (bash 1-liner) for ≥1 ship cycle
- ~30-60 min total for typical surface (most code is CLI flag parsing + ControllerConfig construction)

### Win:

- **Zero drift surface** — CLI uses framework directly; future cfg field add = 1 row in master registry; framework + CLI auto-flow
- **Class 18 + 19 + 21 + 22 closed** at cross-tool surface (mirror + hardcoded keys + parallel descriptors + scattered gating)
- **Layer 7 discipline obviated** at this specific surface (still applies for cross-tool surfaces that CAN'T use framework)
- **Operator workflow preserved** via flag interface continuity + optional deprecation shim
- **Build-time verification** — CLI is C++; type errors caught at compile, not runtime
- **HMAC byte preservation by construction** — same locale pin, same `%.17g` format, same tt::cfg_emit_field<T> path

---

## Reference implementations

### Stage 3 first canonical: `tools/stamp_model_cli.cpp` (v5.15.5.F.4d.1.B.3 Phase L)

- Replaces `tools/stamp_model.sh` (6+ cross-tool sync recurrence count)
- Closes Class 18/19/21/22 at cross-tool stamp model surface
- ~150-200 LOC; thin wrapper over `stamp_write_for_model`
- CLI flags match bash script for operator continuity
- Verification: round-trip test + bash-stamped legacy model HMAC verifies on engine post-migration

### Sister C++ tool precedent: `tools/compare_scalers.cpp` (predates this pattern)

- Standalone C++ tool in `tools/` dir (sister to bash diagnostic tools)
- Does NOT use engine framework (different concern — scaler comparison; not wire-format emit)
- Build system precedent: `tools/compare_scalers.cpp` compiles via CMake as standalone target
- Pattern this spec inherits: tools/ dir is the canonical home for C++ CLI binaries; build system supports them

### Future application candidates (≥ 2nd canonical justifies Stage 5 CLAUDE.md item promotion)

| Workflow | Existing CLI? | Framework API? | Pattern applies? |
|---|---|---|---|
| Schema migration (cfg file upgrade between versions) | future need | `cfg_parse_*` framework | YES if recurrence count ≥ 3 |
| Snapshot inspection / dump | `tools/calls_graph_diff.sh` (different concern) | per-core snapshot API | NO — diagnostic concern, not wire-format mirror |
| Feature mask compute | `tools/validate_feature_mask.sh` | feature registry API | MAYBE — if recurrence accumulates |
| Per-core override emission CLI | future need | per-core override emission framework | YES if recurrence count ≥ 3 |
| Backtest CLI driver | foxml_suite (in-process) | `BacktestSharded_Run` | NO — workflow lives in suite GUI |

Most cross-tool surfaces are DIAGNOSTIC (no wire-format mirror) and don't fit this pattern. The pattern applies specifically to cross-tool surfaces that PRODUCE wire format the engine consumes.

---

## Lessons / gotchas

### CLI flag interface naming continuity

Operator scripts may have hardcoded `tools/stamp_model.sh --model X --wf-mean-val Y` invocations. The C++ CLI binary MUST preserve the exact flag names (`--model`, `--secret`, `--wf-mean-val`, etc.) to avoid operator-side breakage. Per `feedback_surface_operator_migration_path_proactively`.

If a flag is renamed for clarity, support BOTH names with a deprecation warning emitted on the old name. Match the SOFT compat discipline from Decision F (wire-format-byte-preservation-discipline.md Layer 6 Surface G).

### Locale handling in CLI binary

The bash script does `export LC_NUMERIC=C` at the top. The C++ CLI inherits locale pinning from the framework API's internal `uselocale()`. The CLI binary itself can also pin LC_NUMERIC=C in main() for defense in depth — costs nothing + protects against any non-framework code paths.

### Build system: separate target vs library

The CLI binary should be a separate target (`add_executable(stamp_model_cli ...)`) rather than a library shared with the engine. Shared library introduces .so loading complexity for operator workflow. Separate target keeps the CLI self-contained.

### Test coverage

A thin wrapper still deserves tests:
- **CLI flag parsing** — verify each flag parses correctly + invalid flags rejected
- **Framework integration** — verify CLI invokes framework API with correct types
- **Round-trip** — CLI emits stamp; engine verifies stamp; byte-identical to in-process engine emit
- **Workflow replication** — bash script scenarios reproduced via CLI flags

### Deprecation shim discipline

The bash shim should be a 1-line `exec` redirect, NOT a fully-working bash fallback. Fallback bash creates a second source of truth + Class 18 instance recurs. The shim's only job is operator continuity (don't break `tools/stamp_model.sh --model X` invocations); the actual logic lives ONLY in the C++ CLI.

### Build dependency

The CLI binary depends on engine framework headers. If the engine framework changes (e.g., `stamp_write_for_model` signature change), the CLI binary rebuilds automatically (same TU compilation). This is the STRUCTURAL CLOSE: drift becomes a COMPILE error, not a silent wire-format mismatch.

### What if `stamp_write_for_model` evolves?

Future ships may evolve `stamp_write_for_model` signature (e.g., add cfg parameter; rename). The CLI binary updates atomically as part of the same ship that changes the API — compile error guides the update. Same discipline as updating any framework consumer (engine, foxml_suite, etc.).

---

## Audit detection (NEW v1.1; per `pattern-codification-lifecycle.md` Stage 2 discipline)

For `/dod-audit` + `/anti-spaghetti` + `/merge-scan` to detect candidate applications of this pattern in the codebase, the audit signatures are:

**Primary signature — bash script mirroring wire-format keys:**

```bash
# Find bash scripts that emit wire-format keys mirroring engine emit:
rg -l 'stamp_format_version=|model_format_version=|inference_cfg_|model_sha256=' tools/*.sh scripts/*.sh

# For each match, check recurrence count via git log:
git log --oneline --follow tools/<script>.sh | wc -l

# If recurrence count ≥ 3 + script emits wire format that engine framework has API for
# → STRUCTURAL FIX CANDIDATE per this pattern
```

**Secondary signature — manual longopts[] mirror of FOREACH_*_CFG_FIELD in C++ tool:**

```bash
# Find C++ CLI binaries with manual longopts[] arrays:
rg -A 50 'static struct option longopts\[\]' tools/*.cpp

# For each match, check if entries are auto-generated (X_GEN_LONGOPT pattern) or manual:
# Manual entries enumerate cfg field names explicitly → MISSED APPLICATION of this pattern
# Auto-gen entries use FOREACH_PER_CORE_CFG_FIELD(X_GEN_LONGOPT) → already applies pattern
```

**Tertiary signature — manual round-trip test enumerating registry fields:**

```bash
# Find test sections that manually enumerate flagged cfg fields for round-trip validation:
rg -B 2 'has_ridge_lambda == 1.*fabs.*ridge_lambda' tests/

# Manual enumeration → MISSED extensibility test pattern (see § 5.2 above)
```

**When `/dod-audit` flags MISSED — recommended remediation:**

1. Verify recurrence count via `git log --follow <file>` — confirm ≥ 3 events
2. Verify engine framework has the relevant API (e.g., `populate_stamp_cfg_from_derived` for stamp body; could be a different framework for other concerns)
3. Plan structural fix per this spec: thin C++ CLI wrapper + X-macro auto-gen flag table + extensibility test pattern + deprecation shim
4. Add `framework-driven-cli-binary-pattern.md` cross-ref to plan body

**False-positive surface:**

- Bash scripts that READ wire format but don't EMIT it (diagnostic tools; comparison tools) — Layer 7 discipline doesn't apply to read-side; this pattern doesn't either
- Bash scripts with `stamp_format_version=` ONLY in usage/comment lines (not actual emit) — false positive; verify actual emit via getopt loop scan
- C++ tools with manual longopts[] BUT bounded flag set (≤ 6 flags + no registry mirror) — over-engineering risk per `feedback_framework_layer_payoff_diminishing_returns`; manual is fine at small scale (e.g., `tools/compare_scalers.cpp`)

---

## Patterns NOT used here (and why)

### Code-gen tool (Option β)

Considered: a Python codegen tool that emits bash from FOREACH_PER_CORE_CFG_FIELD. Rejected because:
- Adds maintenance surface (codegen tool + build-time step)
- Bash file becomes derived artifact (operator can't read directly without inferring from codegen)
- Codegen tools that parse C++ X-macros are fragile (preprocessor + template-heavy code)
- α achieves the same goal with simpler shape

### Shared library `.so`

Considered: extract framework into `libfoxml_stamp.so`; bash uses `ldopen`. Rejected because:
- `.so` build target adds complexity
- Bash wrapping a `.so` is awkward (FFI-style; not idiomatic)
- α uses the same framework code without indirection

### Schema-driven wire format (JSON/protobuf)

Considered: replace text key=value wire format with schema-driven format. Rejected because:
- Biggest refactor (changes wire format byte shape → breaks legacy HMAC chain)
- Loses human-readable property of current text format
- Loses HMAC-friendly property (clear canonical byte representation)
- Cost/benefit doesn't justify for cross-tool sync goal

### CI parity check (Option γ — defensive only)

Considered: Python CI tool comparing bash wire keys vs C++ FOREACH_PER_CORE_CFG_FIELD. Rejected as PRIMARY structural fix because:
- Catches drift POST-implementation; doesn't eliminate the seam
- Operator still must manually sync bash on every cfg field add
- CI catches when they forget; not when the drift happens

**Acceptable as defense-in-depth** post-α-migration: tools/check_no_cross_tool_emit.py could verify no NEW bash scripts emit wire format (i.e., enforce that future cross-tool surfaces use the framework-driven pattern). Defer to TECH_DEBT entry once 2+ framework-driven CLI binaries ship.

---

## Pattern lifecycle (per `pattern-codification-lifecycle.md`)

- **Stage 1 (problem identification):** 6+ cross-tool sync events at `tools/stamp_model.sh` across versions v5.2.3 / v5.8.8 / v5.9.3b / v5.9.4a / v5.9.5c / v5.11.18a; well over the 4× recurrence threshold per `structural-fix-preferred-decision-framework.md`. Layer 7 codified the discipline at v5.15.5.F.4d.1.B.3 v1.10 but didn't structurally eliminate.

- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-18 at `.B.3` Phase L planning)

- **Stage 3 (first canonical reference):** `.B.3` ship — `tools/stamp_model_cli.cpp` lands as the first canonical framework-driven CLI binary; replaces `tools/stamp_model.sh` (with deprecation shim); round-trip tests verify HMAC + byte-identical canonical body

- **Stage 4 (subsequent applications):** future ships with cross-tool wire-format surfaces apply this pattern per the spec; ≥1 future canonical (e.g., schema migration CLI; per-core override emission CLI) justifies Stage 5

- **Stage 5 (CLAUDE.md item promotion):** after ≥2 canonical applications + pattern proves load-bearing for sprint planning, promote to CLAUDE.md item (e.g., item 32 "framework-driven CLI binaries for cross-tool surfaces; replaces bash scripts that mirror wire emit logic")

- **Stage 6 (tooling enforcement):** future `tools/check_no_cross_tool_emit.py` CI tool verifies no NEW bash scripts emit wire-format; cross-tool surfaces use framework-driven pattern by structural enforcement

- **Stage 7 (wider audit):** post-promotion, scan codebase for other cross-tool surfaces that mirror engine wire emit; apply pattern to identified surfaces

---

## Cross-references

- Sister discipline: `wire-format-byte-preservation-discipline.md` Layer 7 (cross-tool emit-site enumeration — discipline for surfaces that can't use this pattern)
- Composes: `cfg-derived-consumer-framework.md` v1.2 — CLI is new consumer of framework
- Composes: `autopopulate-pattern-for-production-caller-class.md` — existing framework API uses AUTOPOPULATE
- Composes: `meta-registry-pattern-for-codebase-registry-discipline.md` — CLI binary may enroll in `FOREACH_REGISTRY` if it owns a registry; thin wrappers typically don't
- Parent discipline: `canonical-sister-extension-discipline.md` — this pattern's drafting applied the discipline
- `structural-fix-preferred-decision-framework.md` § Step 2 — 4+ occurrence → structural fix MANDATORY
- `pattern-codification-lifecycle.md` — stage progression
- `feedback_no_defer_for_effort.md` — caught my initial `.B.4`-split-as-deferral
- `feedback_motivated_collaborator_for_caramel.md` — best-software discipline
- `feedback_structural_fix_for_recurring_class.md` — parent meta-rule applied here
- `feedback_audit_canonical_sister_before_new_infra.md` — producer-side discipline applied during drafting
- `feedback_surface_operator_migration_path_proactively.md` — CLI flag continuity discipline + deprecation shim
- CLAUDE.md item 31 (framework-driven extensibility)
- CLAUDE.md item 19 (structural fix preferred when bug class can recur)
- RECURRING_BUG_PATTERNS.md Class 18 / 19 / 21 / 22 (the classes this pattern closes at cross-tool surface)
- `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` "Training entry points" axis (this pattern is precedent for FOREACH_CLI_MODE registry)

---

**End of pattern v1.0 DRAFT.** Stage 3 first canonical lands at `.B.3` Phase L ship.
