# Plan-context sweep — Path γ spec drift across queued plans

**Date:** 2026-05-16
**Sprint:** `v5.15-live-readiness`
**Engine HEAD at sweep:** `545b0879948a0893f806dc6afe7992968acd57e3` = tag `v5.15.5.F.4d`
**Trigger:** Path γ pivot adopted at `.F.4d.1.A` planning consult — `DESIGN_SPECS/metadata-bit-driven-derived-filter-framework.md` v1.0/v1.1 mechanism (parallel runtime walker + 3 macro variants `DERIVED_FILTER_DECLARE_*` + `DerivedFilterRoster.hpp`) is SUPERSEDED by Option E (existing `FOREACH_METADATA_BIT` + `cfg_compute_mask` + `CFG_FIELD_FOR_EACH_SET_BIT` infrastructure at `CfgFieldRegistry.hpp:1020-1159`). Queued plans drafted before the Path γ pivot may reference the SUPERSEDED framework macros + walker mechanism.

**Sweep scope:** 10 plan bodies across queued sub-ships:

1. `2026-05-14-v5.15.5.F.4e-string-filepath-gui-metadata.md` (highest priority — 5 GUI metadata applications consume the framework Path γ corrected)
2. `2026-05-16-v5.15.5.F.4f-cleanup-tech-debt-076-080.md`
3. `2026-05-14-v5.15.5.F.4g-resolved-core-cfg-slow-path-cache.md`
4. `2026-05-14-v5.15.5.F.4h-k-state-enum-cohort-pack.md`
5. `2026-05-14-v5.15.5.F.4i-aos-by-core-override-relayout.md`
6. `2026-05-14-v5.15.5.F.4j-strategy-category-audit-and-bitmap-overflow-audit.md`
7. `2026-05-16-v5.15.5.F.4d.1.B-migration-consumer.md` v1.2
8. `2026-05-16-v5.15.5.F.4d.1.B-migration-consumer-examples.md` v1.1
9. `2026-05-16-v5.15.5.F.4d.1.C-sidecar-bitpacked.md` v1.2
10. `2026-05-16-v5.15.5.F.4d.1.D-ci-fixture.md` v1.2

**Drift signature looked for:**
- References to SUPERSEDED macros: `DERIVED_FILTER_DECLARE_GUI` / `DERIVED_FILTER_DECLARE_WIRE_FORMAT` / `DERIVED_FILTER_DECLARE_WIRE_FORMAT_TWO_SOURCE`
- References to SUPERSEDED file: `DerivedFilterRoster.hpp`
- References to `FOREACH_DERIVED_FILTER` as a new registry to build (removed from scope; `FOREACH_METADATA_BIT` IS the registry)
- References to `LOCKED_*_HASH` constants for derived filters (superseded by structural invariants per `.D` v1.1)
- Code samples showing runtime walker pattern (per-row branch over descriptors) instead of `CFG_FIELD_FOR_EACH_SET_BIT` branchless TZCNT iteration
- Status banners showing Stage 3 ACTIVE that should be aspirational

---

## Per-plan verdict

| # | Plan | Verdict |
|---|---|---|
| 1 | `.F.4e` string + file path + GUI metadata | **NEEDS-AMENDMENT-MAJOR** |
| 2 | `.F.4f` cleanup TECH_DEBT-076-080 | **CLEAN** (STUB body; no framework references) |
| 3 | `.F.4g` ResolvedCoreCfg | **CLEAN** (does not reference Path γ surface) |
| 4 | `.F.4h` K-state cohort pack | **CLEAN** (does not reference Path γ surface) |
| 5 | `.F.4i` AoS-by-core relayout | **CLEAN** (does not reference Path γ surface) |
| 6 | `.F.4j` strategy categorical + bitmap overflow | **CLEAN** (does not reference Path γ surface) |
| 7 | `.F.4d.1.B` migration + consumer v1.2 | **NEEDS-AMENDMENT-MINOR** (Path γ banner present; residual stale refs in body) |
| 8 | `.F.4d.1.B-examples` sidecar v1.1 | **NEEDS-AMENDMENT-MINOR** (Path γ banner present; code samples still cite framework-walker fn names) |
| 9 | `.F.4d.1.C` sidecar bit-packed v1.2 | **CLEAN** (Path γ banner correctly notes scope unaffected; FOREACH_DRIFT_OVERRIDE agnostic to walker) |
| 10 | `.F.4d.1.D` CI + fixture v1.2 | **NEEDS-AMENDMENT-MINOR** (Path γ banner present at top; some H16/EXEMPT_FROM_DERIVED_FILTER body references not fully reconciled) |

---

## Finding details

### Plan 1 — `.F.4e` MAJOR drift (highest priority)

**File:** `/home/caramel/code/tick-trader-percore-workspace/plans/v5.15-live-readiness/subplans/2026-05-14-v5.15.5.F.4e-string-filepath-gui-metadata.md`

**Drafted:** 2026-05-14 (same window as the SUPERSEDED spec; no Path γ banner present).

**Top findings:**

1. **Line 271-285 — Step 3a (FAILURE_MODE GUI Class-18 closure) references SUPERSEDED framework:**
   - "applies the framework to a sister source registry (`FOREACH_FAILURE_MODE`) alongside the 5 `FOREACH_CFG_FIELD` applications"
   - Code sample: `DERIVED_FILTER_DECLARE_GUI_BY_GROUP(MODEL_HEALTH_FAILURE, FOREACH_FAILURE_MODE, tt::GROUP_DRIFT)` — extends SUPERSEDED macro family
   - "Option 2 — add a `metadata_flags` column to FOREACH_FAILURE_MODE tuple + add a `GUI_DRIFT_HEADER_RENDERABLE` metadata bit + use the existing `DERIVED_FILTER_DECLARE_GUI` variant"
   - **Recommendation:** Re-plan Step 3a entirely against `FOREACH_METADATA_BIT` mechanism. Option 2 (metadata-bit column extension to FOREACH_FAILURE_MODE) reads better under Path γ since FOREACH_FAILURE_MODE could enroll in a meta-bit framework analogous to `FOREACH_METADATA_BIT` (sister registry per-source). Alternative: skip framework + render via `CFG_FIELD_FOR_EACH_SET_BIT(g_failure_mode_drift_group_mask.words, idx, { ... })` if FAILURE_MODE gains compatible mask infrastructure.

2. **Step 3 (lines 167-265) GUI metadata features — implicit reliance on parallel-walker framework that doesn't exist post-Path γ:**
   - HIDDEN_BY_DEFAULT collapse (lines 175-191) uses `EMIT_RENDER_FILTERED` X-macro with per-row branch on `(meta) & HIDDEN_BY_DEFAULT` — this is exactly the runtime-walker shape Path γ rejected.
   - RESTART_REQUIRED badge (lines 194-201), SAFETY_CRITICAL modal (lines 207-229), DEPRECATED gray-out (lines 234-242), IS_SECRET masking (line 246), LOG_VALUE_FORBIDDEN redaction (Cfg_DumpForLogging lines 250-265) — all show per-field if-check pattern.
   - **Recommendation:** Reshape to use existing `g_global_cfg_hidden_by_default_mask` / `g_global_cfg_restart_required_mask` / etc. (4 of 5 bits ALREADY enrolled in `FOREACH_METADATA_BIT` at `CfgFieldRegistry.hpp:1065-1070` per `.F.4d.1.A` tech-debt-audit-findings.md Finding 2). Settings panel walker loop uses `CFG_FIELD_FOR_EACH_SET_BIT(mask.words, idx, { gui_logic })`. Each metadata bit's UX behavior (hide / badge / modal / gray / mask) becomes a per-bit walker case inside the `EMIT_RENDER_FILTERED` rewrite — `~5 LOC` per consumer instead of the v1.0 if-chain.

3. **Path γ banner ABSENT — entire plan body presents v1.0 mechanism as canonical:**
   - The 2026-05-14 amendment notice at lines 15-49 addresses Class 23 / `.F.4b` lock; does NOT mention Path γ pivot.
   - **Recommendation:** Add v1.1 banner at file top noting Path γ pivot affects Step 3 + Step 3a; defer detailed body update until coding-time OR pre-coding audit gate fire.

4. **Step 1 (KIND_STRING + KIND_FILE_PATH tt:: dispatch — lines 69-132)** also uses pre-`.F.4b` patterns (`*reinterpret_cast<X*>` shape) — already flagged in existing 2026-05-14 amendment notice as STALE per Class 23. Unaffected by Path γ but worth re-verifying at coding time.

**Effort estimate:** ~2-3h to amend body — Path γ banner + Step 3 + Step 3a rewrite to use `FOREACH_METADATA_BIT` mask infrastructure. Substantial because Step 3 is the FIRST canonical of the GUI metadata derived filter family; Step 3a was added at `.F.4d` pre-coding audit and assumes the v1.0 framework family that doesn't exist anymore.

**Re-plan recommendation:** YES — re-plan `.F.4e` body OR mark current body as STALE with strong banner + queue full re-plan at `.F.4f`/`.F.4d.1.A` ship close (whichever lands first). Without amendment, coder will reinvent the v1.0 macros + introduce parallel walker mechanism Path γ explicitly rejected.

---

### Plan 7 — `.F.4d.1.B` MINOR drift (banner present; body residual refs)

**File:** `/home/caramel/code/tick-trader-percore-workspace/plans/v5.15-live-readiness/subplans/2026-05-16-v5.15.5.F.4d.1.B-migration-consumer.md`

**v1.2 banner present at line 10 — correctly notes Path γ pivot affects `.A` not `.B`.** Banner says `CFG_DRIFT_AUTOPOPULATE` walks via `CFG_FIELD_FOR_EACH_SET_BIT` (Path γ canonical) — CORRECT.

**Residual drift in body:**

1. **Lines 114, 234, 247, 260-265, 642, 827 — references to `STAMP_BOUND_CFG_walk_filtered_rows` framework function:** This is the SUPERSEDED v1.0/v1.1 walker fn name (Variant 1 `DERIVED_FILTER_DECLARE_GUI` expansion). Under Path γ canonical mechanism, the walker is `CFG_FIELD_FOR_EACH_SET_BIT(g_*_cfg_stamp_bound_cfg_derived_mask.words, idx, { ... })` — different surface.
   - **Recommendation:** Sweep body + replace all `STAMP_BOUND_CFG_walk_filtered_rows(...)` invocations with `CFG_FIELD_FOR_EACH_SET_BIT(g_*_cfg_stamp_bound_cfg_derived_mask.words, idx, { lambda body })`. Particularly Step 3 (line 339-361 bitmap walker activation), Step 8 (CFG_DRIFT_AUTOPOPULATE definition lines 253-266), Step 9 (consumer site migrations line 247).

2. **Line 116 — predecessor description: "lands DerivedFilterFramework + StampBoundDerivedFilter":** the `DerivedFilterFramework.hpp` file was deleted from `.A` scope per Path γ. `StampBoundDerivedFilter.hpp` may stay as the consumer of the auto-generated mask (still a NEW file) but its body uses `CFG_FIELD_FOR_EACH_SET_BIT`, not custom macros.
   - **Recommendation:** Update predecessor description: "lands STAMP_BOUND_CFG_DERIVED row in FOREACH_METADATA_BIT (1 line at CfgFieldRegistry.hpp:1075) + StampBoundDerivedFilter.hpp consumer + invariant tests via reusable wire-format helper". Delete "DerivedFilterFramework" reference.

3. **Line 641 — "FOREACH_DERIVED_FILTER row in FOREACH_REGISTRY already enrolled at `.A`":** FOREACH_DERIVED_FILTER does not exist post-Path γ. FOREACH_METADATA_BIT already enrolled in FOREACH_REGISTRY per `.F.4d` ship close at MetaRegistry.hpp.
   - **Recommendation:** Replace with "FOREACH_METADATA_BIT row in FOREACH_REGISTRY already enrolled (added at `.F.4d`); STAMP_BOUND_CFG_DERIVED bit row added at `.A` Step 5". Step 12 legacy STAMP_BOUND_CFG empty-out + FOREACH_REGISTRY removal stays correct.

4. **Line 827 — commit message body: "FOREACH_DERIVED_FILTER + StampBoundDerivedFilter still enrolled":** same SUPERSEDED reference.
   - **Recommendation:** Update commit message template at ship-close time.

5. **Line 872 — cross-ref: `metadata-bit-driven-derived-filter-framework.md Stage 3 ACTIVE (revised signatures per Option F)`:** spec is now v1.2 in-progress (per spec line 3); Stage 3 ACTIVE is aspirational per Path γ pivot until `.F.4d.1.A` actually ships.
   - **Recommendation:** Update cross-ref to "Stage 3 ACTIVE PENDING `.A` ship close; per spec v1.2 Path γ correction in progress".

**Effort estimate:** ~30-45 min mechanical sweep of `.B` body + ~15 min `.B-examples` sidecar parallel sweep.

---

### Plan 8 — `.F.4d.1.B-examples` MINOR drift

**File:** `/home/caramel/code/tick-trader-percore-workspace/plans/v5.15-live-readiness/subplans/2026-05-16-v5.15.5.F.4d.1.B-migration-consumer-examples.md`

**v1.1 banner present at line 8 — correctly notes Path γ pivot.**

**Residual drift in body:**

1. **Lines 247, 289, 292 — `STAMP_BOUND_CFG_walk_filtered_rows` walker invocations** in concrete CFG_DRIFT_AUTOPOPULATE code sample (§ Step 8). Same SUPERSEDED function name as `.B` body.
   - **Recommendation:** Replace with `CFG_FIELD_FOR_EACH_SET_BIT(g_per_core_cfg_stamp_bound_cfg_derived_mask.words, idx, { lambda body })` + `CFG_FIELD_FOR_EACH_SET_BIT(g_global_cfg_stamp_bound_cfg_derived_mask.words, idx, { lambda body })`. Lambda body uses `g_per_core_cfg_field_descriptors[idx]` / `g_global_cfg_field_descriptors[idx]` for descriptor access (same data; different walker shape).

2. **Line 558 — cross-ref: "DESIGN_SPECS: `metadata-bit-driven-derived-filter-framework.md` Stage 3 ACTIVE (revised macros)":** Stage 3 ACTIVE is aspirational; "revised macros" framing is moot post-Path γ.
   - **Recommendation:** Update to "Stage 3 ACTIVE PENDING `.A` ship close; canonical mechanism = `FOREACH_METADATA_BIT` per Option E (v1.2 Path γ correction in progress)".

3. **Walker code samples present in § Step 8 (lines 240-296) show v1.0 walker-fn callback shape** with `void (*per_row_fn)(size_t idx, const CfgFieldDescriptor& desc, void* ctx)`. Path γ mechanism doesn't use callback indirection — `CFG_FIELD_FOR_EACH_SET_BIT` is a macro that inlines the lambda body directly. The `DriftCtx` struct + free function `emit_drift_check_per_row` shape comes from runtime-walker design; under Path γ, the same logic inlines into the macro body without callback indirection (faster, branchless TZCNT iteration).
   - **Recommendation:** Restructure code sample to inline the per-row work in the macro body (eliminates ctx struct + free function); see `GUI/SettingsPanel.hpp:1100,1136` for canonical reference (production application of `CFG_FIELD_FOR_EACH_SET_BIT`).

**Effort estimate:** ~30-45 min code-sample sweep + verify against `GUI/SettingsPanel.hpp` canonical reference.

---

### Plan 10 — `.F.4d.1.D` MINOR drift

**File:** `/home/caramel/code/tick-trader-percore-workspace/plans/v5.15-live-readiness/subplans/2026-05-16-v5.15.5.F.4d.1.D-ci-fixture.md`

**v1.2 banner present at line 10 — H16 enforcement reformulated under Path γ.**

**Residual drift:**

1. **Line 86 — "`EXEMPT_FROM_DERIVED_FILTER` constant moves 5 bits to `COVERED_DERIVED_FILTER_BITS` as `FOREACH_DERIVED_FILTER` gains rows":** post-Path γ, the analogous constants would be `EXEMPT_FROM_FOREACH_METADATA_BIT` / `COVERED_BY_FOREACH_METADATA_BIT_BITS` (since `FOREACH_METADATA_BIT` is the enrollment registry, not `FOREACH_DERIVED_FILTER`). Banner at line 10 hints at this rename but body still uses old names.
   - **Recommendation:** Sweep body to align constant names with `FOREACH_METADATA_BIT` mechanism; specifically update line 86 to use the banner's `EXEMPT_FROM_FOREACH_METADATA_BIT` term.

2. **Line 172 — H16 invariant row in audit table: "FOREACH_DERIVED_FILTER roster":** SUPERSEDED registry name.
   - **Recommendation:** Update to "FOREACH_METADATA_BIT enrollment" per banner's reformulation.

**Effort estimate:** ~10 min mechanical sweep (small surface).

---

### Plans 2-6, 9 — CLEAN

- **Plan 2 `.F.4f` cleanup (STUB):** No framework references; cleanup ship is pure TECH_DEBT-076-080 mechanical work. No amendment needed.
- **Plan 3 `.F.4g` ResolvedCoreCfg:** Touches slow-path cache + cfg surface but does NOT reference derived-filter framework family. Path γ is orthogonal to ResolvedCoreCfg's per-field resolution. No amendment needed.
- **Plan 4 `.F.4h` K-state pack:** Multi-bit-state-encoding application; orthogonal to derived filter framework. No amendment needed.
- **Plan 5 `.F.4i` AoS-by-core:** Per-core override storage re-layout; orthogonal. No amendment needed.
- **Plan 6 `.F.4j` strategy categorical + bitmap overflow:** Categorical applicability + bitmap audit; touches different surface. No amendment needed.
- **Plan 9 `.F.4d.1.C` sidecar bit-packed v1.2:** Banner correctly notes scope unaffected (FOREACH_DRIFT_OVERRIDE indexed by FIELD_IDX which is walker-agnostic). Body references to `STAMP_BOUND_CFG_DERIVED` parent (line 293, 298, etc.) are CORRECT under Path γ. No amendment needed.

---

## Effort estimate summary

| Plan | Effort | Priority |
|---|---|---|
| `.F.4e` MAJOR amendment | ~2-3h focused | HIGH — coder will reinvent superseded macros |
| `.F.4d.1.B` MINOR sweep | ~30-45 min | MED-HIGH — next sub-ship in `.F.4d.1` sequence |
| `.F.4d.1.B-examples` MINOR sweep | ~30-45 min | MED-HIGH (sibling to `.B`) |
| `.F.4d.1.D` MINOR sweep | ~10 min | LOW (smaller surface; lands later in `.F.4d.1` umbrella) |
| **Total** | **~3.5-4.5h** | — |

---

## Recommendations — what amends NOW vs at own planning time

### NOW (before next coding session)
- **`.F.4d.1.B` + `.F.4d.1.B-examples`** — these are the immediate next ship after `.F.4d.1.A` lands. Coder will hit the SUPERSEDED walker fn refs at Step 3 (bitmap walker activation) and Step 8 (CFG_DRIFT_AUTOPOPULATE definition) within the first hour of coding. ~75-90 min total sweep cost is well under the cost of mid-flight pivot during `.B` coding.
- **`.F.4d.1.D`** — quick 10-min mechanical sweep; do it now while sweep context is loaded.

### At pre-coding audit gate (when ship is next-up)
- **`.F.4e`** — major re-plan. Body is large + needs rewriting against Path γ canonical mechanism. Coder at `.F.4e` pre-coding gate will need to re-derive Step 3 + Step 3a regardless; better to capture the re-plan at the same point. **STRONG RECOMMENDATION:** Add v1.1 banner now flagging the major drift so the pre-coding agent doesn't get blindsided. Defer body update to pre-coding audit gate fire.

### At own planning time
- **Plans 2, 3, 4, 5, 6, 9** — CLEAN; no amendment needed. Their planning at coding time will not encounter Path γ drift surface.

---

## `.F.4e` deep-dive — how much depends on Path γ-corrected framework?

**Heavily.** `.F.4e` Step 3 was originally drafted to be **the FIRST 5 canonical applications of the GUI metadata derived filter family** (HIDDEN_BY_DEFAULT, RESTART_REQUIRED, SAFETY_CRITICAL, IS_SECRET, DEPRECATED). Each metadata bit drives one operator-facing GUI behavior. Under v1.0/v1.1 framework, each would have gotten its own `DERIVED_FILTER_DECLARE_GUI(NAME, FOREACH_CFG_FIELD, METADATA_BIT)` macro invocation in a new `GuiMetadataFilters.hpp` file with parallel walker bodies. **All 5 are SUPERSEDED.**

Under Path γ canonical mechanism:
- **4 of 5 bits ALREADY enrolled in `FOREACH_METADATA_BIT`** at `CfgFieldRegistry.hpp:1065-1070` (RESTART_REQUIRED, SAFETY_CRITICAL, DEPRECATED, HIDDEN_BY_DEFAULT, IS_SECRET — all enrolled per `.F.4d.1.A` tech-debt-audit-findings.md Finding 1). Per `.F.4d.1.A` Gap 3 / TECH_DEBT-NEW-B: these bits exist with auto-generated masks (`g_global_cfg_hidden_by_default_mask` etc.) but ZERO consumers read them. `.F.4e`'s scope shrinks to just adding the consumers using `CFG_FIELD_FOR_EACH_SET_BIT(mask.words, idx, { ui_logic })`.
- **Net `.F.4e` effort under Path γ: REDUCES significantly** — instead of building 5 framework consumers via parallel walker, just call existing `CFG_FIELD_FOR_EACH_SET_BIT` over already-auto-generated masks. Step 3 body should DROP from ~150 LOC to ~30 LOC (1 walker invocation per UX behavior).
- **Step 3a (FAILURE_MODE GUI Class-18 closure)** is the structural-rewrite candidate — Option 2 path (add metadata column to FOREACH_FAILURE_MODE; create sister `FOREACH_FAILURE_MODE_METADATA_BIT` X-macro analog) becomes the recommended approach; OR add an `applies_to_drift_group` filter via the existing mask infrastructure pattern.

**Re-plan `.F.4e` post-Path γ verdict:** **YES, re-plan body BEFORE coding fires.** The mechanism delta is substantial enough that body presents wrong code samples + wrong scope estimate (would understate the simplification). Sequence the re-plan to fire at `.F.4e` pre-coding gate (after `.F.4d.1.D` umbrella close), NOT now — `.F.4d.1.A` framework infra hasn't landed yet, so Path γ canonical surface isn't fully shipped to validate against.

---

## Cross-cutting observations

- **Drift was concentrated in plans drafted between 2026-05-14 and 2026-05-16** — same window as the SUPERSEDED spec versions. `.F.4d.1.B`/`.C`/`.D` updates 2026-05-16 captured Path γ banners but residual code-sample refs slipped through.
- **`.F.4f`-`.F.4j` plans (2026-05-14)** weren't touching the derived-filter surface at all, so escaped drift. Categorical applicability + slow-path cache + AoS layout are orthogonal concerns.
- **The Class 18 mirror pattern Path γ closed at framework layer recurred in the plans themselves** — plans drafted same window as the spec mirrored the v1.0 mechanism in code samples; updating the spec without updating the plans = parallel descriptors at the planning surface. Same shape as the bug class we close in production code. Worth a NEW TECH_DEBT-NEW-E entry: "Plan-context drift detection cadence — sweep all queued sub-plans for SUPERSEDED spec mechanism refs after every spec amendment of Stage 3 ACTIVE patterns".

---

## Phase 3 recommended actions

1. **Amend `.F.4d.1.B` + `.F.4d.1.B-examples` NOW** — ~75-90 min mechanical sweep; replaces SUPERSEDED walker fn refs with `CFG_FIELD_FOR_EACH_SET_BIT` canonical surface.
2. **Amend `.F.4d.1.D` NOW** — ~10 min mechanical sweep; aligns body with banner's H16 reformulation.
3. **Add v1.1 STALE banner to `.F.4e` plan body NOW** — ~5 min; defer body re-plan to pre-coding audit gate.
4. **Open TECH_DEBT-NEW-E** — Plan-context drift detection cadence.
5. **Plans 2, 3, 4, 5, 6, 9** — no action needed.

**Total Phase 3 amendment effort: ~95-115 min focused (1.5-2h).**

---

**End of sweep.**
