# D1 — FOREACH_METADATA_BIT Cohort Survey

**Date:** 2026-05-16
**Engine:** FoxML_Trader_v2 @ HEAD `545b0879` (tag `v5.15.5.F.4d`)
**Context:** Path γ pivot at `.F.4d.1.A` planning — `/merge-scan` caught that the
proposed `DerivedFilterFramework.hpp` parallel walker DUPLICATED existing
infrastructure at `CfgFieldRegistry.hpp:1020-1257` (FOREACH_METADATA_BIT registry
+ `cfg_compute_mask` constexpr + `CFG_FIELD_FOR_EACH_SET_BIT` TZCNT iteration).
This D1 survey checks whether OTHER cohort patterns in the codebase could
benefit from the same infrastructure but aren't yet using it.

---

## 1. Infrastructure inventory (anchor)

`CoreFrameworks/CfgFieldRegistry.hpp:1020-1257` provides:

| Surface | Where | Purpose |
|---|---|---|
| `CfgMaskArray<N_WORDS>` | line 1027 | fixed-size mask wrapper |
| `cfg_compute_mask<Bit>(arr)` | line 1038 | compile-time per-bit mask derivation; lands in `.rodata` |
| `cfg_field_count(mask)` | line 1053 | popcount over mask array |
| `FOREACH_METADATA_BIT(X)` | line 1064 | 11 metadata bits enumerated (restart_required / safety_critical / deprecated / stamp_bound / hidden_by_default / is_secret / is_boot_only / affects_stamp_parity / log_value_forbidden / has_side_effect / warn_on_clamp) |
| `X_GEN_GLOBAL_MASK` / `X_GEN_PER_CORE_MASK` | lines 1079-1089 | auto-generates `g_global_cfg_<bit>_mask` + `g_per_core_cfg_<bit>_mask` per registry per bit |
| `FOREACH_LIVES_IN_STRUCT(X)` + `cfg_compute_lives_in_struct_mask` | lines 1101-1134 | per-enum-VALUE mask analogue (equality dispatch vs bitwise AND) |
| `CFG_FIELD_FOR_EACH_SET_BIT(mask, idx, body)` | line 1150 | branchless TZCNT iteration via `__builtin_ctzll` + `word &= word - 1` |
| Composed masks (`g_*_cfg_render_mask` / `_save_mask` / `_stamp_emit_mask` / `_cli_explain_mask`) | lines 1167-1257 | per-registry compositions for canonical walker views |

**Active production consumers (today):**
- `GUI/SettingsPanel.hpp:1100` — `g_global_cfg_render_mask` walker
- `GUI/SettingsPanel.hpp:1136` — `g_per_core_cfg_render_mask` walker
- `tests/controller_test.cpp:1715-1762` — 5+ regression tests over `_is_boot_only` / `_warn_on_clamp` / `_has_side_effect` / `_render` masks

That's effectively 2 production sites + tests. Infrastructure exists but
under-leveraged.

---

## 2. All X-macro registries in the codebase

Inventoried via `rg "^#define FOREACH_"`. **57 registries total** across the engine:

### 2.1 Cfg-domain registries (already in FOREACH_METADATA_BIT scope)
- `FOREACH_GLOBAL_CFG_FIELD` (47 rows; CfgFieldRegistry.hpp:255)
- `FOREACH_PER_CORE_CFG_FIELD` (93 rows; CfgFieldRegistry.hpp:419)

These are the existing canonical applications.

### 2.2 Registries with metadata-bit-style cohort columns (candidates)

These have explicit per-row metadata columns that consumers filter by:

| Registry | File:Line | Cohort columns | Mechanism today | Migration candidate? |
|---|---|---|---|---|
| `FOREACH_OMS_FIELD` | MemHeaders/OmsFieldRegistry.hpp:217 | RESET_FLAG (DO_RESET/SKIP_RESET), STORAGE_KIND (DIRECT/BIT/MULTI_BIT/ATOMIC), PERSIST_FLAG (PERSIST/SKIP_PERSIST) | Token-paste `OMS_PROJECT_PERSIST_*` X-macro projections per consumer | YES (heavy; see § 4.1) |
| `FOREACH_FEATURE` | ML_Headers/FeatureRegistry.hpp:479 | enabled (FEATURE_ENABLED/FEATURE_DISABLED), max_staleness_minutes | Already has `FEATURE_ENABLED_BITMAP` uint64_t at line 563 + `IS_FEATURE_ENABLED(i)` macro | PARTIAL — bitmap exists but only 2 test consumers; the production `Features_PackAll` X-macro expansion does in-line `(enabled)` check + skip (line 690) instead of bitmap iteration. See § 4.2 |
| `FOREACH_FAILURE_MODE` | MemHeaders/FailureModeRegistry.hpp:123 | storage_class (BIT_FLAG/COUNTER_U32/PERCENT_U8), severity (SEV_RED/SEV_YELLOW/SEV_SAND), group_id (GROUP_STANDALONE/_DRIFT/_NAN_EVENTS) | Token-paste `FAILURE_MODE_BIT_DECL_##storage_class` per consumer | YES — see § 4.3 |
| `FOREACH_STAMP_BOUND_CFG` | ML_Headers/StampBoundCfgRegistry.hpp:99 | emit_when (predicate expr), emit_source (DIRECT_FIELD/BITMAP_BIT) | Per-row inline `if (emit_when)` in AUTOPOPULATE expansion | **IN-FLIGHT** — this IS the .F.4d.1 STAMP_BOUND_CFG_DERIVED migration target (Path γ). |
| `FOREACH_CFG_DRIFT_CHECK` | ML_Headers/CfgDriftCheckRegistry.hpp:194 | severity (WARN_ALWAYS/REFUSE_STRICT), category (CROSS_BINARY/INFERENCE_CFG), compare_kind (EXACT/EPS_DEFAULT/STRING), gate_when, fail_mask | Per-row inline switch on severity/category in `CoreModelZoo_ValidateAgainstCfg` walker | YES (most cohort-rich; see § 4.4) |
| `FOREACH_STAMP_BOUND_MODEL_CONST` | ML_Headers/StampBoundModelConstRegistry.hpp:488 | presence (INCLUDE/SKIP_HANDLE), group (gating tag), emit_when | Per-row token-paste + emit_when predicate | YES (medium; § 4.5) |
| `FOREACH_LIVE_READINESS_CHECK` | CoreFrameworks/LiveReadiness.hpp:193 | sev (LR_SEV_REFUSE / LR_SEV_WARN) | Per-row inline `sev`-switch in walker | YES (small; § 4.6) |
| `FOREACH_ML_CFG_FLAG` | ML_Headers/MlCfgFlagRegistry.hpp:52 | section (FoxML/Performance/ML-Ridge) | Section column drives GUI grouping but no mask | LOW — only 12 entries in 16-bit bitmap; semi-applicable |

### 2.3 Registries that are dispatch-table / declaration-emit only (NOT candidates)

These don't have per-row cohort metadata for filtered iteration; they auto-generate
enum + fn-ptr table + ToString:

- `FOREACH_STRATEGY`, `FOREACH_REGIME`, `FOREACH_SHALT`, `FOREACH_HALT_REASON` (Strategies/StrategyInterface.hpp:107+)
- `FOREACH_BANDIT_ALGORITHM`, `FOREACH_BANDIT_SIDE` (ML_Headers/bandit_dispatch_table.hpp + BanditAlgorithmRegistry.hpp) — these have rich per-state metadata but it's CONSUMED via auto-derived dispatch tables, not bitmap iteration; right pattern is `multi-state-dispatch-with-per-state-update-metadata.md`
- `FOREACH_DEGRADATION_CURVE`, `FOREACH_IC_VARIANT`, `FOREACH_BARRIER_BLEND_MODE`, `FOREACH_RECONCILE_MODE`, `FOREACH_SESSION_PHASE`, `FOREACH_TARGET` — enum + fn-ptr dispatch
- `FOREACH_OMS_STATE_FLAG`, `FOREACH_PER_CORE_STATE_FLAG`, `FOREACH_CORE_STATE_FLAG`, `FOREACH_PER_ARM_FLAG`, `FOREACH_EZOO_INIT_FLAG` — auto-allocated bit positions (state-storage bitmaps); no per-row cohort columns
- `FOREACH_LIFECYCLE_CFG_FLAG`, `FOREACH_GATE_CFG_FLAG`, `FOREACH_RISK_CFG_FLAG`, `FOREACH_OPS_CFG_FLAG` — cfg-flag bitmap registries (3-arg tuple: name/legacy/doc); already part of `FOREACH_PER_CORE_DOMAIN_BITMAP` meta-registry
- `FOREACH_TRADE_LOG_COL`, `FOREACH_CALIB_LOG_COL` — CSV column registries (3-arg: name/fmt/expr); no cohort columns
- `FOREACH_CORE_CTX_INIT_FIELD`, `FOREACH_CORE_CTX_RESET_FIELD`, `FOREACH_CORE_CTX_SUMMARY_FIELD`, `FOREACH_DISPLAY_META_FIELD`, `FOREACH_POSITION_FIELD`, `FOREACH_GATE_DIAG_PAIR` — typed field declaration + init registries
- `FOREACH_PANEL`, `FOREACH_BACKTEST_METRIC`, `FOREACH_ROLLING_WINDOW`, `FOREACH_SP_SECTION` — dispatch / enumeration
- `FOREACH_ENSEMBLE_POST_LOAD`, `FOREACH_SINGLE_ZOO_POST_LOAD` — initialization-step sequencers
- `FOREACH_CFG_DERIVED_INFERENCE_CFG` — sister to STAMP_BOUND_CFG (already auto-populated)
- `FOREACH_OMS_PER_SLOT_FIELD`, `FOREACH_OMS_META_SLOT` — loop body for per-slot iteration
- `FOREACH_ARCH_FIELD_DRIFT` — 4-row drift check (too small + each row has its own FAILURE_MASK_*)
- `FOREACH_STAMP_BOUND_MODEL_CONST_GROUPS` / `_STANDALONE` / `_PRE_CFG` / `_POST_CFG` — sub-projections of MODEL_CONST
- `FOREACH_PER_CORE_DOMAIN_BITMAP` — Level-1 meta-registry (binds child cfg-flag registries to PerCoreCfg fields)
- `FOREACH_REGISTRY` — Level-2 top-level meta-registry (catalogues all registries)
- `FOREACH_LIVES_IN_STRUCT` — enum value cohort (already integrated as analogue pattern at lines 1101-1134)
- `FOREACH_MANUAL_PER_CORE_FIELD`, `FOREACH_PER_CORE_NO_FLAT_FIELD_SYNC` — transition-period registries

---

## 3. Orphan mask findings (TECH_DEBT-087 signal)

Of the 11 metadata bits in `FOREACH_METADATA_BIT`, the auto-generated
`g_global_cfg_<bit>_mask` + `g_per_core_cfg_<bit>_mask` arrays are
**REFERENCED IN PRODUCTION** for these bits only:

| Bit | Direct consumer | Composed-into | Status |
|---|---|---|---|
| `is_boot_only` | (none direct) | `g_*_cfg_render_mask` (excludes boot-only from render) | INDIRECT via composition |
| `hidden_by_default` | (none direct) | `g_*_cfg_render_mask` (excludes hidden from render) | INDIRECT via composition |
| `has_side_effect` | (none direct) | `g_*_cfg_save_mask` (excludes side-effect from save) | INDIRECT via composition (also used as MANUAL_PARSER alias in parser walker — but that's via inline `(meta) & HAS_SIDE_EFFECT` check, NOT via the precomputed mask) |
| `stamp_bound` | (none direct) | `g_*_cfg_stamp_emit_mask = g_*_cfg_stamp_bound_mask` (alias for upcoming stamp walker) | ALIAS ONLY — no walker fires yet; awaits `.F.4d.1` |
| `warn_on_clamp` | tests/controller_test.cpp:1720 (count check) | — | TEST-ONLY |
| `restart_required` | (none) | — | **ORPHAN** |
| `safety_critical` | (none) | — | **ORPHAN** |
| `deprecated` | (none) | — | **ORPHAN** |
| `is_secret` | (none) | — | **ORPHAN** |
| `affects_stamp_parity` | (none) | — | **ORPHAN** |
| `log_value_forbidden` | (none) | — | **ORPHAN** |

**6 orphan masks × 2 registries = 12 unused `g_*_cfg_<bit>_mask` arrays in
`.rodata` today.** Each is ~2 uint64 words (16 bytes), so ~192 bytes of
`.rodata` is currently unconsumed. Negligible memory cost, but
discoverability + maintainability risk: adding a `FOREACH_METADATA_BIT`
row generates 2 mask arrays automatically with no enforcement that
anything consumes them.

**TECH_DEBT-087 priority signal:** **MEDIUM-HIGH.** A CI Check (or
runtime-zero `static_assert` discipline) requiring "every
`FOREACH_METADATA_BIT` row MUST have at least one production consumer
OR be marked `MASK_RESERVED_FOR_FUTURE` with a TECH_DEBT pointer" closes
the unused-by-construction class. Recommended CI shape:

```python
# tools/check_metadata_bit_consumer_coverage.py
# For each row in FOREACH_METADATA_BIT(X):
#   grep -c "g_global_cfg_${bit}_mask|g_per_core_cfg_${bit}_mask|g_*_cfg_${bit}_alias"
#   if zero AND not in EXEMPT list with rationale → BUILD FAIL
```

Note: `.F.4d.1` Path γ migration will activate `g_*_cfg_stamp_bound_mask`
via the new stamp walker (auto-flow `STAMP_BOUND_CFG_DERIVED` rows from
descriptors). After `.F.4e` the 5 GUI metadata bits get activated as well.
So 4 of the 11 will resolve naturally. The TECH_DEBT-087 close should
align with `.F.4e` ship to enforce coverage at that point.

---

## 4. Top retrofit candidates (ranked)

### 4.1 `FOREACH_CFG_DRIFT_CHECK` — HIGH-VALUE COHORT (#1 candidate)

**Surface:** `ML_Headers/CfgDriftCheckRegistry.hpp:194` (18 rows).
**Per-row metadata columns:**
- `severity`: WARN_ALWAYS / REFUSE_STRICT
- `category`: CROSS_BINARY / INFERENCE_CFG
- `compare_kind`: EXACT / EPS_DEFAULT / STRING
- `gate_when`: predicate expression
- `fail_mask`: FAILURE_MASK_* constant

**Today:** Consumer in `CoreFrameworks/ModelValidation.hpp` walks the registry
via inline X-macro expansion, branching on severity + category per row.

**Migration to FOREACH_METADATA_BIT shape:**
- Could promote `category` to a bit mask (CATEGORY_CROSS_BINARY / CATEGORY_INFERENCE_CFG) — enables `g_drift_check_inference_cfg_mask` + `g_drift_check_cross_binary_mask` precomputed masks.
- Could promote `severity` to a bit (`SEVERITY_REFUSE_STRICT` set if REFUSE, clear if WARN-only) — enables `g_drift_check_refuse_strict_mask`.
- Consumer migrates to walk + filter via mask:
  ```cpp
  CFG_FIELD_FOR_EACH_SET_BIT(g_drift_check_refuse_strict_mask.words, idx, {
      if (drift_violated(idx, h, cfg)) refuse_count++;
  });
  CFG_FIELD_FOR_EACH_SET_BIT((g_drift_check_refuse_strict_mask & strict_mode_mask).words, ...);
  ```

**Estimated retrofit effort:** **MEDIUM** — ~6-10h. Schema add `DriftDescriptor`
sidecar struct + analogous `cfg_compute_drift_mask<Bit>()` + 2-3 composed
views (refuse-on-strict / warn-on-cross-binary / etc.). The walker in
`CoreModelZoo_ValidateAgainstCfg` migrates ~20 LOC from inline switch to
mask iteration.

**Bug class closures:**
- Closes "drift check forgotten to be added to walker" recurrence (Class 21
  variant at drift surface).
- Adds CI Check for "drift descriptor without consumer" (orphan analog).

**Risk:** LOW — wire format independent; pure walker shape change.

### 4.2 `FOREACH_FEATURE` — PARTIAL RETROFIT (#2 candidate)

**Surface:** `ML_Headers/FeatureRegistry.hpp:479` (40 rows).

**Today:** Already has `FEATURE_ENABLED_BITMAP` uint64_t at line 563 +
`IS_FEATURE_ENABLED(i)` macro. BUT only 2 test consumers + 1
informational test. **Production `Features_PackAll` does in-line
expansion** with `(enabled)` check at line 690 (`do { if (!(enabled)) break; ... } while(0)`).

**Why production doesn't use bitmap iteration:** `Features_PackAll` is
called per-prediction (hot-cadence — every slow-path cycle when
prediction fires). Inline expansion = compile-time skip of DISABLED
features → smaller code-size + no runtime cost. Bitmap iteration
would add per-prediction branchless loop overhead for marginal gain.

**Verdict:** **KEEP CURRENT.** Features_PackAll's hot-cadence justifies
inline expansion. The `FEATURE_ENABLED_BITMAP` exists for cross-build
parity (hash invariant + test instrumentation) — that's its right role.

**Possible non-hot-path migration:** GUI features panel + stamp body
feature-list emit could walk via bitmap iteration. But those are
low-cadence; benefit marginal. **Defer.**

### 4.3 `FOREACH_FAILURE_MODE` — TOKEN-PASTE PATTERN (#3 candidate)

**Surface:** `MemHeaders/FailureModeRegistry.hpp:123` (~13 entries).
**Per-row metadata columns:** storage_class, severity, group_id.

**Today:** Token-paste dispatch
(`FAILURE_MODE_BIT_DECL_##storage_class(name)`) at lines 276+. Only
BIT_FLAG entries get bit-position allocation; others (COUNTER_U32 /
PERCENT_U8) get different declarations. Different shape from cohort-mask.

**Why retrofit doesn't fit perfectly:** The 3 storage classes are NOT
mutually-exclusive flags over a uniform field — they're distinct typed
field declarations. Right pattern is token-paste-on-storage-class
(current implementation; CLAUDE.md item 13 X-macro).

**Possible cohort-mask add:** `severity` column COULD be promoted to
metadata bit if a consumer needs "iterate all RED-severity failure
modes" — but no such consumer exists today + severity is already
captured in the per-entry `sev` value used at render time.

**Verdict:** **NOT A CANDIDATE.** Pattern is correctly token-paste-by-storage-class. Severity-mask migration would have no consumer. Skip.

### 4.4 `FOREACH_STAMP_BOUND_MODEL_CONST` — IN-FLIGHT (#4 candidate)

**Surface:** `ML_Headers/StampBoundModelConstRegistry.hpp:488` (~50 entries).
**Per-row metadata columns:** presence (INCLUDE/SKIP_HANDLE), group, emit_when.

**Today:** Per-row token-paste + inline emit_when predicates.

**Migration consideration:** Could add `INCLUDE` vs `SKIP_HANDLE` as metadata
bit + auto-generate "on-handle subset" mask. But this would only consolidate
the existing macro-level filtering; .F.4d.1 STAMP_BOUND_CFG_DERIVED already
covers the analogous shape for cfg-side. The MODEL_CONST side is wire-format
ordered (PRE_CFG / POST_CFG split + canonical body emit order) — bitmap
iteration would break wire ordering. **Wire-format constraint precludes
mask-driven walker.**

**Verdict:** **NOT A CANDIDATE.** Wire format byte-preservation (H9)
makes bitmap iteration unsafe.

### 4.5 `FOREACH_OMS_FIELD` — TOKEN-PASTE BY STORAGE_KIND (#5 candidate)

**Surface:** `MemHeaders/OmsFieldRegistry.hpp:217` (~30 entries).
**Per-row metadata columns:** RESET_FLAG, STORAGE_KIND, PERSIST_FLAG, MASK_BIT.

**Today:** Multiple consumer projections (OMS_PROJECT_PERSIST_DECLARE /
_SAVE / _READ / _COMMIT) walk the registry via X-macro projection + skip
non-PERSIST rows via inline check.

**Why retrofit doesn't fit:** Like FOREACH_FAILURE_MODE, this is
token-paste-by-storage-kind (DIRECT vs BIT vs MULTI_BIT vs ATOMIC each
generate different code). Bitmap iteration applies to homogeneous-shape
filter; this registry's per-row STORAGE_KIND varies the GENERATED CODE
shape itself.

**Possible cohort add:** PERSIST_FLAG could promote to a metadata bit +
`g_oms_field_persist_mask`. But the PERSIST_DECLARE / _SAVE / _READ /
_COMMIT projections are wire-format ordered (snapshot byte position
1..10) — same wire-format constraint as MODEL_CONST.

**Verdict:** **NOT A CANDIDATE.** Wire format byte-preservation precludes mask iteration; per-storage-kind token-paste is the right shape.

### 4.6 `FOREACH_LIVE_READINESS_CHECK` — SMALL/LOW-VALUE (#6 candidate)

**Surface:** `CoreFrameworks/LiveReadiness.hpp:193` (9 entries).
**Per-row metadata columns:** sev (LR_SEV_REFUSE / LR_SEV_WARN).

**Today:** Walker iterates all 9 entries + sums REFUSE vs WARN tallies via
inline severity-switch.

**Migration possibility:** Could split into `g_readiness_refuse_mask` +
`g_readiness_warn_mask` precomputed masks. Walker becomes 2 mask
iterations (one for refuse-checks, one for warn-checks).

**Effort:** **LOW** — ~2-3h. New `ReadinessCheckDescriptor` sidecar +
mask generation.

**Bug class closures:** Adds visibility — "list of REFUSE checks at boot"
becomes a 1-line popcount. But registry only has 9 entries; benefit
marginal.

**Verdict:** **DEFER.** Small registry; current walker is fine.
Revisit if registry grows past 20 entries OR if a consumer needs
"iterate REFUSE-only checks" as a distinct path.

---

## 5. Manual iteration site survey

Sites that iterate `g_global_cfg_field_descriptors[]` or
`g_per_core_cfg_field_descriptors[]` DIRECTLY (not via mask):

| Site | File:Line | Pattern | Why not mask? |
|---|---|---|---|
| `tt::cfg_parse_field(cfg.name, g_global_cfg_field_descriptors[FIELD_IDX_GLOBAL_##name], val)` | CoreFrameworks/ControllerConfig.hpp:2119 | X-macro inline + per-row HAS_SIDE_EFFECT bit check | Parser dispatches via `strcmp(key, #name)` — fundamentally a literal-name lookup, NOT a uniform-shape walk over all fields. Per-row code generated by macro expansion. |
| `tt::cfg_parse_field(cfg.name, g_per_core_cfg_field_descriptors[FIELD_IDX_PER_CORE_##name], val)` | CoreFrameworks/ControllerConfig.hpp:2137 | Same shape with MANUAL_PARSER + NO_FLAT_FIELD bit checks | Same reason — parser is per-row name-match dispatch, mask iteration would lose name-lookup mechanism. |
| Test sites tests/controller_test.cpp:1559+ | Direct indexing by `FIELD_IDX_<name>` | Targeted lookup by name | Test fixtures need named field; mask iteration not applicable. |
| `g_global_cfg_field_descriptors[i].applies_to_strategy_cat` | tests/controller_test.cpp:1596 | Iterates all descriptors checking categorical column | Mask candidate IF a consumer wants "iterate all strategy-conditional fields" but currently is just a test invariant check. |

**Verdict on manual iteration:** Parser sites are correctly inline-expanded
(name-match dispatch). Test sites are correctly direct-indexed.
**0 production sites are mask-eligible retrofit candidates** that aren't
already using mask iteration.

---

## 6. Composed-view opportunities

Per `composed-filter-mask-pattern.md` (NEW DESIGN_SPEC at Path γ), the
existing composed views are:

| View | Composition | Used by | Adoption |
|---|---|---|---|
| `g_*_cfg_render_mask` | `~(is_boot_only | hidden_by_default)` | SettingsPanel walker | 2 production sites |
| `g_*_cfg_save_mask` | `~has_side_effect` | (none) | UNUSED in production |
| `g_*_cfg_stamp_emit_mask` | `= stamp_bound_mask` | (none — awaits .F.4d.1) | UNUSED |
| `g_*_cfg_cli_explain_mask` | `all` (ones-mask) | (none) | UNUSED |

**`g_*_cfg_save_mask` orphan finding:** The save walker that should
exclude HAS_SIDE_EFFECT rows is currently NOT migrated to the composed
mask. The save path uses `tt::cfg_save_field(...)` per-field but the
**walker that iterates fields for save** isn't currently structured to
walk via mask. Either there's no full-walker save site today (most
saves go via TUI panel "Save" button → walks `field_defs[]` legacy
array?) or the walker isn't using the precomputed mask.

**Action item:** verify whether a "save all fields to disk" walker
exists today and migrate it to `g_*_cfg_save_mask` if so. If not,
this is a forward-compat asset awaiting a `.F.4e` cfg.example auto-gen
walker.

---

## 7. Findings synthesis + recommendations

### Top 5 retrofit candidates (effort-ranked)

| # | Registry | Effort | Risk | Bug class | Decision |
|---|---|---|---|---|---|
| 1 | `FOREACH_CFG_DRIFT_CHECK` (severity + category masks) | MED (6-10h) | LOW | Drift-walker forgotten-entry class | **PROPOSE: defer to post-.F.4d.1 — Path γ + framework first, drift retrofit second** |
| 2 | `FOREACH_FEATURE` (production bitmap walk) | LOW | LOW | (none) | **KEEP CURRENT** — hot-cadence justifies inline expansion |
| 3 | `FOREACH_LIVE_READINESS_CHECK` (severity-split masks) | LOW (2-3h) | LOW | (none structural) | **DEFER** — small registry |
| 4 | `FOREACH_FAILURE_MODE` (severity mask) | MED | LOW | (none) | **NOT A CANDIDATE** — token-paste-by-storage-class is right shape |
| 5 | `FOREACH_STAMP_BOUND_MODEL_CONST` (presence mask) | HIGH | HIGH (wire format) | (none — fragile retrofit) | **NOT A CANDIDATE** — wire format precludes |

### Orphan mask finding (TECH_DEBT-087 priority signal)

**6 of 11 metadata bits have ZERO production consumers** (restart_required,
safety_critical, deprecated, is_secret, affects_stamp_parity,
log_value_forbidden). 4 more become consumed after `.F.4e` GUI ship.
Recommend codifying CI Check for "every FOREACH_METADATA_BIT row MUST
have ≥1 production consumer OR documented EXEMPT marker" — align with
`.F.4e` ship close (when most orphans resolve naturally).

### `g_*_cfg_save_mask` orphan (no consumer found)

The composed save-mask exists but no production walker iterates it.
Either:
- (a) the save path lives elsewhere (TUI legacy `field_defs[]`) — pending migration
- (b) save was supposed to be a `.F.4e` walker target that hasn't shipped

**Action:** verify with operator whether `.F.4e` cfg.example auto-gen
walker is the intended consumer; if so, plan a Step in that ship to
activate this orphan.

### Overall verdict

**FOREACH_METADATA_BIT infrastructure is correctly designed but UNDER-LEVERAGED.**

- 2 of 11 bits drive production walkers (via composed render-mask)
- 6 bits are orphans
- 4 bits await ship activation (`.F.4d.1` stamp + `.F.4e` GUI metadata)
- 0 NEW retrofit applications surface from this survey ready for immediate adoption

**No N-more applications waiting** in the cohort sense. The infrastructure
is "saturated for its current registry surface" — adding registries (cfg
fields) auto-populates; consumer adoption is the bottleneck. The Path γ
migration at `.F.4d.1` is appropriate (uses existing infrastructure for
STAMP_BOUND_CFG_DERIVED cohort).

**Recommendations:**
1. Path γ proceeds as planned (no infrastructure changes needed).
2. Codify CI Check `test_metadata_bit_consumer_coverage` aligned with
   `.F.4e` ship close (TECH_DEBT-087).
3. **Optional, post-.F.4e:** `FOREACH_CFG_DRIFT_CHECK` retrofit to mask
   iteration if `CoreModelZoo_ValidateAgainstCfg` walker complexity
   grows past current 18 entries (estimated trigger: 25-30 drift
   checks). Don't pre-invest now.
4. Investigate `g_*_cfg_save_mask` orphan with operator (intended
   consumer? `.F.4e` walker?).

---

**File:line refs (engine-side, absolute paths):**
- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/CfgFieldRegistry.hpp:1020-1257` — FOREACH_METADATA_BIT + cfg_compute_mask + CFG_FIELD_FOR_EACH_SET_BIT infrastructure
- `/home/caramel/code/FoxML_Trader_v2/GUI/SettingsPanel.hpp:1095-1145` — canonical live consumer
- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerConfig.hpp:2115-2142` — parser inline-expansion + HAS_SIDE_EFFECT/MANUAL_PARSER/NO_FLAT_FIELD bit checks
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/CfgDriftCheckRegistry.hpp:194` — top retrofit candidate
- `/home/caramel/code/FoxML_Trader_v2/ML_Headers/FeatureRegistry.hpp:563-567` — partial-bitmap precedent (FEATURE_ENABLED_BITMAP)
- `/home/caramel/code/FoxML_Trader_v2/MemHeaders/OmsFieldRegistry.hpp:217` — wire-format constraint precedent (not a candidate)
- `/home/caramel/code/FoxML_Trader_v2/MemHeaders/FailureModeRegistry.hpp:123` — token-paste-by-storage-class precedent (not a candidate)
- `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/MetaRegistry.hpp:35` — top-level registry catalogue (57 entries enrolled)
