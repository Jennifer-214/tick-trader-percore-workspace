# D5 audit — composed-filter mask composition opportunities

**Created:** 2026-05-16 (Phase 2 Level 4 codebase pattern survey for `.F.4d.1.A`)
**Scope:** Find sites doing manual composition (per-row AND/OR/NOT of metadata bits at consumer time) that could be migrated to use a precomputed composed mask. Verify existing 3 canonicals are well-used. Identify new composed-mask opportunities at queued ships.
**Engine HEAD:** `545b0879948a0893f806dc6afe7992968acd57e3` = tag `v5.15.5.F.4d` (MERGED)
**Audit methodology:** rg over `*.{hpp,cpp}` for `metadata_flags & ...`, `g_*_cfg_*_mask`, `CFG_FIELD_FOR_EACH_SET_BIT`, `FOREACH_METADATA_BIT`; cross-checked against `CfgFieldRegistry.hpp:1064-1257` (canonical mask infra) and `composed-filter-mask-pattern.md` Stage 2 DRAFT.

---

## TL;DR — verdict GREEN-with-action-items

1. The 3 canonical composed masks (`render_mask`, `save_mask`, `cli_explain_mask`) exist symmetrically for both global + per-core registries but **only `render_mask` has live consumers** (2 sites: `SettingsPanel.hpp:1100,1136`). `save_mask`, `cli_explain_mask`, `stamp_emit_mask` are precomputed but **unused** — they are speculative scaffolding awaiting `.F.4e` (cfg.example auto-gen) + future CLI `--explain`.
2. **Top retrofit candidate found:** the registry parser cases at `ControllerConfig.hpp:2118,2134-2135` do manual composition `if (!(meta & HAS_SIDE_EFFECT))` (global) and `if constexpr (!(meta & MANUAL_PARSER) && !(meta & NO_FLAT_FIELD))` (per-core). These could be retrofitted to use a **new** composed `g_*_cfg_parse_mask`. But they live inside the X-macro EMIT body (compile-time per-row instantiation), not the consumer iteration loop — so the retrofit path is different (move from EMIT body to dispatcher walker; bigger refactor than `.A` scope warrants).
3. **`.A` (THIS ship) composition opportunity:** the new `g_*_cfg_stamp_bound_cfg_derived_mask` IS a single-bit mask, not a composition. Path γ Step 3 is right: no NEW composed mask lands at `.A`.
4. **`composed-filter-mask-pattern.md` Stage 2 → Stage 3 readiness:** **NOT YET ready to promote** at `.A`. No new composed mask is introduced at `.A`; the existing 3 canonicals are documented but underused. Recommend keeping at Stage 2 until `.F.4e` introduces a `visible_to_user_mask` or `cfg_example_emit_mask` (genuine new composition use).
5. **`CFG_COMPOSE_AUDIT_DECISIONS` scope recommendation:** enumerate the 3 existing composed masks × all 11 (soon 12) metadata bits = 33-36 cells. Each cell carries `COMPOSE_INCLUDE` / `COMPOSE_EXCLUDE` / `COMPOSE_NA` token. Adding a metadata bit at `.A` (STAMP_BOUND_CFG_DERIVED) forces explicit decision against all 3 composed masks. Tooling cost: ~50 LOC X-macro + ~30 LOC consistency CI check. Worth it at `.A` per Gap 1 mitigation.

---

## Finding 1 — Existing composed masks: consumer coverage

### `render_mask` — well-used

| Mask | Composition | Consumers | Status |
|---|---|---|---|
| `g_global_cfg_render_mask` | `~(is_boot_only \| hidden_by_default)` | `GUI/SettingsPanel.hpp:1100` (global registry render walk) | **LIVE** |
| `g_per_core_cfg_render_mask` | `~(is_boot_only \| hidden_by_default)` | `GUI/SettingsPanel.hpp:1136` (per-core registry render walk) | **LIVE** |

Popcount-verified at `tests/controller_test.cpp:1754-1764` (T13).

### `save_mask` — SCAFFOLDING (no consumers)

| Mask | Composition | Consumers | Status |
|---|---|---|---|
| `g_global_cfg_save_mask` | `~has_side_effect` | NONE | **UNUSED** |
| `g_per_core_cfg_save_mask` | `~has_side_effect` | NONE | **UNUSED** |

The cfg save path at `GUI/SettingsPanel.hpp:1036,1047,1054,1070,1284,1311,1325,1362,1375,1390,1572,1641` uses ad-hoc `cfg_write_field(s->cfg_path, key, ...)` calls scattered across field-by-field render paths. There is **no centralized "save all renderable cfg fields" walker** that would benefit from `save_mask`. `save_mask` is forward-compat scaffolding for `.F.4e` (cfg.example auto-gen via mask iteration) — currently dead.

### `cli_explain_mask` — SCAFFOLDING (no consumers)

| Mask | Composition | Consumers | Status |
|---|---|---|---|
| `g_global_cfg_cli_explain_mask` | `~(has_side_effect \| hidden_by_default)` | NONE | **UNUSED** |
| `g_per_core_cfg_cli_explain_mask` | `~(has_side_effect \| hidden_by_default)` | NONE | **UNUSED** |

No CLI `--explain` mode exists. Scaffolding awaits future CLI feature.

NOTE on composition: the global+per-core `cli_explain_mask` constexpr fns at `:1197-1257` currently produce `~0ULL` (i.e., ALL bits set, then trailing-word masked) — **the composition expression is missing**. The signature implies `~(has_side_effect | hidden_by_default)` per spec doc + comment line 57 but the fn body just produces the full mask. This is either (a) a bug pending real consumer to drive the composition or (b) a placeholder. Either way: **flag for review**. (Lines 1200-1206 + 1247-1253 both literally produce `~0ULL` for the full word, then trailing-word truncate — no AND with `~has_side_effect` or `~hidden_by_default` happens.)

### `stamp_emit_mask` — ALIAS (zero composition)

| Mask | Composition | Consumers | Status |
|---|---|---|---|
| `g_global_cfg_stamp_emit_mask` | `= g_global_cfg_stamp_bound_mask` (alias) | NONE | **UNUSED** |
| `g_per_core_cfg_stamp_emit_mask` | `= g_per_core_cfg_stamp_bound_mask` (alias) | NONE | **UNUSED** |

Just a named alias — single-bit, no composition. Could be deleted (`stamp_bound_mask` carries the same semantics; alias adds nothing). **Recommendation:** delete in `.A` along with the metadata-bit addition (one less name to maintain). OR formalize the rename if "stamp_emit" reads more semantically than "stamp_bound" at consumer sites (none exist yet, so the question is moot).

---

## Finding 2 — Manual composition sites (retrofit candidates)

### Site A — global cfg parser case (`ControllerConfig.hpp:2118`)

```cpp
#define EMIT_GLOBAL_CFG_PARSER_CASE(KIND_TOKEN, name, label, section, meta, ...) \
    if (strcmp(key, #name) == 0 && !((meta) & CfgFieldDescriptor::HAS_SIDE_EFFECT)) { \
        tt::cfg_parse_field(cfg.name, g_global_cfg_field_descriptors[FIELD_IDX_GLOBAL_##name], val); \
        continue; \
    }
FOREACH_GLOBAL_CFG_FIELD(EMIT_GLOBAL_CFG_PARSER_CASE)
```

**Composition:** `meta & HAS_SIDE_EFFECT` — single bit, no composition. Per-row at X-macro instantiation (compile time per row). Could be skipped via `g_global_cfg_has_side_effect_mask` lookup but the parser is `strcmp`-keyed (not index-keyed) so the auto-generated case body needs the inline test. **Verdict:** NOT a composed-mask retrofit candidate — this is X-macro template instantiation, not a runtime walker. Leave as-is.

### Site B — per-core cfg parser case (`ControllerConfig.hpp:2134-2135`) — **TRUE MANUAL COMPOSITION**

```cpp
#define EMIT_PER_CORE_CFG_PARSER_CASE(STORAGE_T, KIND_TOKEN, name, label, section, meta, ...) \
    if constexpr (!((meta) & CfgFieldDescriptor::MANUAL_PARSER) && \
                  !((meta) & CfgFieldDescriptor::NO_FLAT_FIELD)) { \
        if (strcmp(key, #name) == 0) { \
            tt::cfg_parse_field(cfg.name, g_per_core_cfg_field_descriptors[FIELD_IDX_PER_CORE_##name], val); \
            continue; \
        } \
    }
FOREACH_PER_CORE_CFG_FIELD(EMIT_PER_CORE_CFG_PARSER_CASE)
```

**Composition:** `meta & (MANUAL_PARSER | NO_FLAT_FIELD)` — true two-bit composition. **But** evaluated `if constexpr` at compile time per row inside X-macro expansion, not runtime per iteration. The COMPILER sees the bit values as compile-time constants from the X-macro row's `meta` parameter and dead-code-eliminates the unmatched cases. Net cost: 0 runtime branches (case body either compiles in or compiles out).

**Retrofit option:** introduce `g_per_core_cfg_parseable_mask` = `~(manual_parser_mask | no_flat_field_mask)` and switch the parser to walk `CFG_FIELD_FOR_EACH_SET_BIT(g_per_core_cfg_parseable_mask.words, idx, { if (strcmp(key, desc.cfg_field_name) == 0) { tt::cfg_parse_field(...); break; } })`. **Cost-benefit:** zero runtime saving (compile-time `if constexpr` already 0 cost); refactor cost ~20 LOC + retest 414+ parser fixtures. **Verdict:** SKIP — composition is already optimal at compile time, parser is `strcmp`-keyed not index-keyed (mask iteration would require auxiliary keyed lookup, adding cost).

### Site C — copy walker (`ControllerConfig.hpp:1478`)

```cpp
if constexpr (!((meta) & CfgFieldDescriptor::NO_FLAT_FIELD)) { \
    cores[c].name = cfg.name; \
}
```

**Composition:** single-bit. Not a retrofit candidate. Could be index-walked via `g_per_core_cfg_has_flat_field_mask` (the negation of `no_flat_field_mask`) but again `if constexpr` is already 0-cost.

### Site D — render walker (`GUI/SettingsPanel.hpp:222`)

```cpp
if constexpr (!((meta) & CfgFieldDescriptor::NO_FLAT_FIELD)) { \
    /* render fn ptr generation */ \
}
```

Same shape as Site C. Single-bit; `if constexpr`; not a retrofit candidate.

### Site E — clamp-warn at `CfgFieldDispatch.hpp:128,145`

```cpp
if (... && (desc.metadata_flags & CfgFieldDescriptor::WARN_ON_CLAMP)) {
    /* warn message */
}
```

**Composition:** single-bit at runtime (inside `tt::cfg_parse_field<T>` dispatcher fn, after clamp branch). Runtime cost: ~1 cycle AND + branch. Not iterated; per-call. **Verdict:** NOT a retrofit candidate (single-bit check at a per-call site, not a registry walker).

---

## Finding 3 — Recurring composition patterns (potential extractions)

Scanned all `metadata_flags & ...` and `meta & ...` patterns in codebase:

| Pattern | Sites | Compose to? |
|---|---|---|
| `~(is_boot_only \| hidden_by_default)` | 2 (already the `render_mask` definition + already consumed) | DONE |
| `~has_side_effect` | 1 (already the `save_mask` definition; unused) | DONE |
| `~(has_side_effect \| hidden_by_default)` | 1 (already the `cli_explain_mask` definition; unused) | DONE |
| `~(manual_parser \| no_flat_field)` | 1 site at `:2134-2135` (per-core parser X-macro) | candidate `parseable_mask` BUT see Finding 2 Site B — skip |
| `~no_flat_field` | 2 sites at `:1478, :222` (copy + render walker X-macros) | candidate `has_flat_field_mask` BUT see Finding 2 Sites C/D — skip |
| `~has_side_effect` × parser (separate) | 1 site at `:2118` (global parser X-macro) | Same shape as save_mask but different consumer — semantically different (parse vs save) |

**Verdict:** NO new recurring composition pattern emerged at this scan beyond the 3 already codified. The 3 existing canonicals genuinely cover the actual recurring compositions.

---

## Finding 4 — New composed-mask opportunities at queued ships

### `.F.4d.1.A` (THIS ship) — NO new composed mask

`.A` adds `STAMP_BOUND_CFG_DERIVED` to FOREACH_METADATA_BIT (1 row) → auto-generates `g_*_cfg_stamp_bound_cfg_derived_mask` (single-bit, not composed). Consumer at NEW `StampBoundDerivedFilter.hpp` walks `CFG_FIELD_FOR_EACH_SET_BIT(g_*_cfg_stamp_bound_cfg_derived_mask.words, idx, { ... })` — single-bit, no composition.

The `composed-filter-mask-pattern.md` Stage 2 promotion doesn't happen at `.A` (no new composed mask to register). Stage 3 promotion deferred.

### `.F.4d.1.B` — drift check consumer

`.B` adds `CFG_DRIFT_AUTOPOPULATE` companion macro that walks via `CFG_FIELD_FOR_EACH_SET_BIT(g_*_cfg_stamp_bound_cfg_derived_mask.words, idx, { ... })` PLUS gated by the β4 sidecar cohort. The gate is per-row (`if (cohort_bit_set) { ... }`) not a composition of two precomputed masks because the sidecar is sparse (FOREACH_DRIFT_OVERRIDE indexed by FIELD_IDX) and doesn't have its own auto-generated mask.

**Composition opportunity:** could compose `g_*_cfg_drift_check_cohort_mask` = (the drift-check-eligible rows actually present in FOREACH_DRIFT_OVERRIDE) AND THEN AND `g_*_cfg_stamp_bound_cfg_derived_mask` to get `drift_check_active_mask`. Then walker becomes:

```cpp
CFG_FIELD_FOR_EACH_SET_BIT(g_global_cfg_drift_check_active_mask.words, idx, {
    /* drift check body; no per-row sidecar gate needed; mask precomputes intersection */
});
```

**Cost:** ~20 LOC compose fn + sidecar→mask transform; saves per-row hashmap lookup. **Verdict:** valid candidate for `.B` if the sidecar override registry has enough rows (currently 5 per `.F.4d` ship) to justify precomputation. SKIP at `.B` (only 5 rows = 5 per-row branches = negligible). REVISIT when sidecar grows past ~16 rows.

### `.F.4e` — 5 GUI metadata derived filters

`.F.4e` plans to add 5 GUI metadata consumers via the framework (HIDDEN_BY_DEFAULT, RESTART_REQUIRED, SAFETY_CRITICAL, IS_SECRET, DEPRECATED). All 5 already auto-generate single-bit masks (`g_*_cfg_<lname>_mask`) from FOREACH_METADATA_BIT — no new composition needed for the single-bit consumers.

**NEW composed-mask opportunity:** the cfg.example auto-gen at `.F.4e` may want `g_*_cfg_example_emit_mask` = `~(is_secret | deprecated | hidden_by_default | is_boot_only)` (i.e., "publishable to example config"). This composes 4 bits → genuine composition use. Land at `.F.4e` when cfg.example writer ships.

Similarly, restart_required is a HUD/banner-only flag (no save composition); safety_critical is a confirm-dialog flag (no save composition); is_secret is a render-as-asterisks flag (no save composition); deprecated is a "show with strikethrough" render flag (no save composition). None of these inherently demands a NEW composed mask beyond what already exists.

**Stage 3 promotion target for `composed-filter-mask-pattern.md`:** `.F.4e` cfg.example writer (1st genuine new composition since codification).

### `.F.4f` cleanup — POSSIBLE additional mask retrofit

`.F.4f` adds AUTOPOPULATE bitmap-bool migration for 28 KIND_BOOL flat fields → domain bitmaps. May surface additional manual composition sites that could compose into a `g_*_cfg_kind_bool_mask` (= `kind == KIND_BOOL`). But this is a kind-equality dispatch, not a metadata-bit composition. Likely handled by `FOREACH_LIVES_IN_STRUCT`-style per-value mask pattern (`:1099-1133`), not composed bit mask.

---

## Finding 5 — `CFG_COMPOSE_AUDIT_DECISIONS` checklist scope recommendation

Per `composed-filter-mask-pattern.md` Step 3 + Gap 1 mitigation in `2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md`: when adding a new metadata bit, audit every existing composed mask for include/exclude decision.

### Proposed X-macro shape

```cpp
// FOREACH_COMPOSE_AUDIT_DECISION(X) — checklist of (composed_mask, metadata_bit, decision) tuples.
// Decisions: COMPOSE_INCLUDE / COMPOSE_EXCLUDE / COMPOSE_NA.
// Adding a new metadata bit requires adding rows for each composed mask
// (render_mask, save_mask, cli_explain_mask, stamp_emit_mask if kept) →
// CI failure if a bit lacks a decision row for any active composed mask.
#define FOREACH_COMPOSE_AUDIT_DECISION(X)                                                   \
    /* (composed_mask_name,       metadata_bit_name,        decision)                    */ \
    X(render_mask,                 RESTART_REQUIRED,         COMPOSE_INCLUDE)                \
    X(render_mask,                 SAFETY_CRITICAL,          COMPOSE_INCLUDE)                \
    X(render_mask,                 DEPRECATED,               COMPOSE_INCLUDE)                \
    X(render_mask,                 STAMP_BOUND,              COMPOSE_NA)                     \
    X(render_mask,                 HIDDEN_BY_DEFAULT,        COMPOSE_EXCLUDE)                \
    X(render_mask,                 IS_SECRET,                COMPOSE_INCLUDE)                \
    X(render_mask,                 IS_BOOT_ONLY,             COMPOSE_EXCLUDE)                \
    X(render_mask,                 AFFECTS_STAMP_PARITY,     COMPOSE_NA)                     \
    X(render_mask,                 LOG_VALUE_FORBIDDEN,      COMPOSE_INCLUDE)                \
    X(render_mask,                 HAS_SIDE_EFFECT,          COMPOSE_INCLUDE)                \
    X(render_mask,                 WARN_ON_CLAMP,            COMPOSE_NA)                     \
    X(render_mask,                 STAMP_BOUND_CFG_DERIVED,  COMPOSE_NA)  /* NEW at .A   */ \
    X(save_mask,                   RESTART_REQUIRED,         COMPOSE_INCLUDE)                \
    /* ... 11 more rows for save_mask × every bit ... */                                    \
    X(cli_explain_mask,            ...)                                                     \
    /* ... 11 more rows for cli_explain × every bit ... */
```

### CI check

```cpp
// CI Check NEW — every (active_composed_mask, every metadata_bit) cell has a decision
SECTION("FOREACH_COMPOSE_AUDIT_DECISION: every composed mask × every metadata bit has explicit decision");
// Iterate active composed masks (render/save/cli_explain) × FOREACH_METADATA_BIT rows.
// For each (mask, bit), check at least one FOREACH_COMPOSE_AUDIT_DECISION row exists.
// Failure messages name the missing (mask, bit) pair.
```

### Scope cost

- ~33 rows at codification time (3 composed masks × 11 bits)
- +3 rows per new metadata bit added (e.g., STAMP_BOUND_CFG_DERIVED at `.A` = 3 rows = 1 line per composed mask)
- +11 rows per new composed mask (e.g., `cfg_example_emit_mask` at `.F.4e` = 11 lines)
- ~30 LOC CI check
- Total scope cost: ~80 LOC + ongoing 3-LOC per metadata bit + 11-LOC per composed mask

### Scope verdict — LAND AT `.A` per Gap 1

Land `CFG_COMPOSE_AUDIT_DECISIONS` X-macro at `.A` alongside the STAMP_BOUND_CFG_DERIVED bit addition. Per Path γ Gap 1 mitigation. The X-macro registry is itself a new registry → must enroll in FOREACH_REGISTRY (H15) → Level 0 standalone data registry, no parent.

**Recommended decision for STAMP_BOUND_CFG_DERIVED across the 3 existing composed masks:**
- `render_mask`: COMPOSE_NA (this is a derived-filter bit for stamp emit/drift-check; not a render visibility decision)
- `save_mask`: COMPOSE_NA (same reason)
- `cli_explain_mask`: COMPOSE_NA (same reason; this bit doesn't gate user-visible cfg fields by behavior)

All 3 default to NA — STAMP_BOUND_CFG_DERIVED is orthogonal to the user-visibility cohort the 3 existing composed masks gate on.

---

## Finding 6 — `composed-filter-mask-pattern.md` Stage 2 → Stage 3 readiness

| Criterion | Status |
|---|---|
| 1st reference (Stage 2) | DONE at `.F.4d.1.A` planning (DESIGN_SPEC drafted) |
| 1st CODE reference (Stage 3) | NOT YET — `.A` adds no new composed mask |
| 2nd code reference (cohort migration) | Pending — likely `.F.4e` cfg.example emit_mask |
| 3rd code reference (CLAUDE.md promotion) | Pending |
| 3 existing canonicals well-used | NO — only `render_mask` has consumers; `save_mask`, `cli_explain_mask`, `stamp_emit_mask` are scaffolding |

**Verdict:** **DEFER Stage 3 promotion** to `.F.4e` (when cfg.example writer introduces 4-bit `cfg_example_emit_mask`). At `.A`, keep `composed-filter-mask-pattern.md` at Stage 2 DRAFT.

Alternative: promote to Stage 3 at `.A` on the grounds that `CFG_COMPOSE_AUDIT_DECISIONS` X-macro registry is a new framework artifact citing the pattern. That's a valid reading — the checklist IS a new code artifact that enforces the pattern's discipline. **Recommended:** promote to Stage 3 at `.A` on this basis. The 3 existing canonicals + checklist = 4 active framework artifacts.

---

## Recommendations summary

| # | Recommendation | Land at |
|---|---|---|
| 1 | Promote `composed-filter-mask-pattern.md` to Stage 3 ACTIVE on basis of `CFG_COMPOSE_AUDIT_DECISIONS` codification | `.A` (this ship) |
| 2 | Land `CFG_COMPOSE_AUDIT_DECISIONS` X-macro registry — enumerate the 3 existing composed masks × 11 metadata bits = 33 decisions; +3 for STAMP_BOUND_CFG_DERIVED | `.A` (Gap 1 mitigation) |
| 3 | Enroll FOREACH_COMPOSE_AUDIT_DECISION in FOREACH_REGISTRY (Level 0; H15) | `.A` |
| 4 | Investigate `cli_explain_mask` composition expression bug — `:1197-1257` produces `~0ULL` instead of `~(has_side_effect \| hidden_by_default)` per spec; pending real consumer drive | `.A` flag (defer fix until `.F.4e` real consumer lands) |
| 5 | Delete or formalize `g_*_cfg_stamp_emit_mask` alias (no semantic value over `stamp_bound_mask`) | `.A` or `.F.4e` |
| 6 | Defer `g_*_cfg_drift_check_active_mask` precomputation (5 sidecar rows; below threshold) — REVISIT at 16+ rows | future |
| 7 | Land `g_*_cfg_cfg_example_emit_mask` = `~(is_secret \| deprecated \| hidden_by_default \| is_boot_only)` at `.F.4e` cfg.example writer | `.F.4e` (1st genuine new composition since codification) |
| 8 | Don't retrofit parser/copy/render walker X-macros to mask-iterate — `if constexpr` is already 0-cost; mask iteration would add overhead | NEVER |

---

## Methodology notes

### Search queries run

- `rg "metadata_flags\s*&\s*\(" --type-add 'cpp:*.{hpp,cpp}' -t cpp -n` → 0 hits (no parenthesized OR composition at consumer time)
- `rg "metadata_flags\s*&\s*[A-Z]" -t cpp -n` → 2 hits (CfgFieldDispatch.hpp:128,145 — both single-bit WARN_ON_CLAMP)
- `rg "g_(global|per_core)_cfg_(render|save|cli_explain|stamp_emit)_mask" -t cpp -n` → 12 hits (declarations + tests + 2 live consumers in SettingsPanel)
- `rg "meta\s*&\s*CfgFieldDescriptor::" -t cpp -n` → 7 hits (1 single-bit + 2 single-bit + 1 single-bit + 1 single-bit + 2 in 2-bit composition site B)
- `rg "FOREACH_METADATA_BIT" -t cpp -n` → 7 hits (1 X-macro def + 2 mask gen + 1 meta-registry entry + 2 commentary)
- `rg "CFG_FIELD_FOR_EACH_SET_BIT" -t cpp -n` → 9 hits (1 macro def + 2 live consumers + 6 commentary/tests)

### Files inspected

- `CoreFrameworks/CfgFieldRegistry.hpp:1020-1257` (mask infra + 3 canonical composed masks + iteration macro)
- `GUI/SettingsPanel.hpp:1095-1160` (render walker — 2 live consumers)
- `CoreFrameworks/ControllerConfig.hpp:1467-1500, 2110-2145` (parser + copy walker X-macros — manual composition site B)
- `CoreFrameworks/CfgFieldDispatch.hpp:120-150` (clamp-warn single-bit check)
- `tests/controller_test.cpp:1700-1830` (T12+T13 popcount tests)
- `tick-trader-percore-workspace/DESIGN_SPECS/composed-filter-mask-pattern.md` (Stage 2 DRAFT — pattern spec)
- `tick-trader-percore-workspace/plans/v5.15-live-readiness/plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md` (Gap 1 source)

---

**End of D5 audit.**
