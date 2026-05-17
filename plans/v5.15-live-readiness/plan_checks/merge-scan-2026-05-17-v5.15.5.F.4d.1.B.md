# /merge-scan report — v5.15.5.F.4d.1.B migration + consumer — 2026-05-17

**Scope:** plan body + sidecar for `.B`. Compared against engine HEAD `39b9947` (`.A` shipped Path γ+ v2).

**Top-line verdict: YELLOW.** Three structural critiques (one Path γ-class, one near-Path γ-class, one sidecar conflate). Plus 4 LOW/MED reuse-merge opportunities. Mechanical correctness OK; structural alignment with existing AUTOPOPULATE pattern + bounds-validation infrastructure needs reconciliation.

---

## CRITICAL — Path γ-class structural critique

### M-1 (CRITICAL): `CFG_DRIFT_AUTOPOPULATE` reinvents `INFERENCE_CFG_AUTOPOPULATE`'s per-row `gate_when` shape via parallel sparse-sidecar dispatch
**Section:** § Step 8 (plan body lines 234-275) + § Step 11 (β4 cohort gate sidecar lines 468-580 + 487-580); sidecar Step 8/8b lines 237-462.

**Critique.** The proposed `FOREACH_DRIFT_GATE` sparse sidecar + `DriftGateKind` enum + `g_drift_gate_table<F>[]` dispatch table + `g_drift_gate_lookup_per_core[]`/`_global[]` arrays solves the **same problem** the existing canonical `INFERENCE_CFG_AUTOPOPULATE` already solves: per-row gate predicate for cohort-aware emit/drift-check. Compare:

- **Existing canonical (`MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101-123`):** per-row 3-tuple `X(name, cfg_expr, gate_when)` — `gate_when` is an inline boolean expression evaluated per row. ~5 cohorts already encoded inline: `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)` for bandit/thompson rows; `BITMAP_IS_SET(..., MASK_GATE_CFG_COST_GATE_ENABLED)` for fees; `1` for unconditional. No sparse sidecar, no fn-pointer dispatch table, no `DriftGateKind` enum, no parallel lookup arrays.

- **`.B`'s proposal:** new registry `FOREACH_DRIFT_GATE` (15 rows enumerating 4 cohorts) + `DriftGateKind` enum (5 values) + 5 template gate fns + `g_drift_gate_table` dispatch table + 2 parallel sparse sidecar arrays (`g_drift_gate_lookup_per_core` + `g_drift_gate_lookup_global`) + `EMIT_DRIFT_GATE_INIT` populate macro + new CI check `test_drift_gate_sidecar_coverage`. ~80 LOC of new infrastructure per sidecar examples Step 8b.

**Why this is Path γ-class.** The plan body acknowledges β4 is "sister to FOREACH_DRIFT_OVERRIDE at `.C`" but FOREACH_DRIFT_OVERRIDE is solving a **different concern** (custom severity / cross-binary / EPS_TIGHT semantics per row) — it's an override sidecar for genuinely per-row deviation from default. `FOREACH_DRIFT_GATE` is solving a **cohort gating** concern that is already mechanicalized via inline `gate_when` column in the canonical sister `FOREACH_CFG_DERIVED_INFERENCE_CFG`. The β4 dispatch table is the same Class 21 shape (parallel descriptors for the same concern) the spec frames itself as preventing.

**Proposed unification.** Use per-row `gate_when` column on the derived-filter source data, NOT a sidecar:
1. EITHER extend the source descriptor at `FOREACH_PER_CORE_CFG_FIELD` / `FOREACH_GLOBAL_CFG_FIELD` rows with a `drift_gate_kind` column (1 byte; default=0/DRIFT_GATE_DEFAULT; ~24 rows touched at `.B` to set non-default values)
2. OR add a new `FOREACH_CFG_DERIVED_DRIFT_CHECK` registry parallel to `FOREACH_CFG_DERIVED_INFERENCE_CFG`, using identical 3-tuple `X(name, cfg_expr, gate_when)` shape so consumers + future editors see identical pattern across both companion macros.

Option (2) is the **clean win** — same X-macro shape as canonical sister, zero new dispatch infrastructure, zero parallel arrays, gate predicate inline + readable.

**Win estimate.** ~80 LOC deleted (CfgDriftGate.hpp eliminated entirely) + 1 new registry header (~30 LOC) + 1 FOREACH_REGISTRY row removed + 1 CI check removed. Net: ~50-60 LOC saved + 0 dispatch tables + 0 sparse sidecars + 0 new `DriftGateKind` enum maintenance burden. **Critical Class 21 prevention:** the per-row 3-tuple shape stays uniform with `INFERENCE_CFG_AUTOPOPULATE`.

**Risk.** MED-HIGH if accepted at `.B`: re-thinks Step 11 + sidecar Step 8b. ~1-2h plan body amendment + design rework. Lower if deferred to `.C` (closes more cleanly when DRIFT_OVERRIDE actually lands; pattern-codification-lifecycle.md "2nd canonical" check can re-evaluate sidecar shape).

**Recommendation:** Pre-coding plan body amendment per per-sub-ship audit→update→implement→ship cycle. **Caramel: this is a Path γ-class find worth surfacing before coding starts.**

---

## HIGH — near-Path γ-class

### M-2 (HIGH): Winsor parse-time validation should leverage existing `WARN_ON_CLAMP` + descriptor `as_double.clamp_min/max` infrastructure for individual bounds; ad-hoc only for cross-field invariant
**Section:** § Step 10 (plan body lines 451-466) + sidecar § Step 10 lines 511-534.

**Critique.** The Winsor parse-time validation block (`if (low <= 0.0 || high >= 1.0 || low >= high) { ... return 1; }`) duplicates per-field bounds checking that already exists at `CfgFieldDispatch.hpp:70-71` (FPN branch: `v = std::clamp(v, desc.payload.as_double.clamp_min, desc.payload.as_double.clamp_max);`). Verified at HEAD:

- `winsor_pct_low` at `CfgFieldRegistry.hpp:569` uses `DBL(0.005, 0.0, 0.5)` + `WARN_ON_CLAMP` bit
- `winsor_pct_high` at `CfgFieldRegistry.hpp:572` uses `DBL(0.995, 0.5, 1.0)` + `WARN_ON_CLAMP` bit

Individual bounds (`low > 0`, `high < 1`) are **already enforced** at parse time via `std::clamp` per `tt::cfg_parse_field<T>`. The only validation NOT covered is the **cross-field invariant** `low < high`. Plan body conflates the two.

**Proposed unification.** Tighten descriptor clamp_min for `winsor_pct_low` from `0.0` to a hairsbreadth above (e.g. `1e-9`) so `<= 0.0` is structurally impossible post-clamp — OR document that existing clamp_min=0.0 means parse normalizes to 0.0 (true at HEAD; cohort gate's emit-time check at `.B.11` becomes "STAMP_HAS(*h, inference_cfg) && cfg.winsor_pct_low > 0.0 && cfg.winsor_pct_low < cfg.winsor_pct_high"). The cross-field `low < high` invariant is the only piece needing new code (~5 LOC, not ~10).

**Sister cohort fields** that have similar parse-time bounds infrastructure (verified at HEAD):
- `ridge_lambda` `DBL(0.15, 0.0, 10.0)` + WARN_ON_CLAMP
- `confidence_capacity_kappa` `DBL(0.1, 0.0, 10.0)` + WARN_ON_CLAMP
- `risk_full_size_threshold` `DBL(0.15, 0.0, 1.0)` + WARN_ON_CLAMP
- ALL 24 cohort rows already have `WARN_ON_CLAMP` infrastructure available

**Win estimate.** ~5 LOC saved + clearer separation between individual bounds (registry descriptor) and cross-field invariants (parse-time validator). Cohort gate `gate_when` simplifies post-clamp because individual `> 0` / `< 1` are guaranteed by parse.

**Risk.** LOW. Mechanical clean-up at Step 10.

---

## MED

### M-3 (MED): `CFG_DRIFT_AUTOPOPULATE` shape diverges from sister `STAMP_CFG_AUTOPOPULATE` + `INFERENCE_CFG_AUTOPOPULATE` (callback-with-DriftCtx vs do-while-X-macro)
**Section:** § Step 8 plan body lines 262-275 + sidecar § Step 8 lines 237-302.

**Critique.** Sister AUTOPOPULATE macros are uniform shape:

```cpp
#define STAMP_CFG_AUTOPOPULATE(inf, cfg)                                          \
    do { FOREACH_STAMP_BOUND_CFG(STAMP_CFG_AUTOPOPULATE_ONE) } while (0)

#define INFERENCE_CFG_AUTOPOPULATE(inf, cfg)                                      \
    do { STAMP_SET((inf), inference_cfg);                                         \
         FOREACH_CFG_DERIVED_INFERENCE_CFG(X_INFERENCE_CFG_AUTOPOPULATE_ONE)      \
    } while (0)
```

`CFG_DRIFT_AUTOPOPULATE`'s proposed shape **breaks** the do-while-X-macro uniformity:

```cpp
#define CFG_DRIFT_AUTOPOPULATE(failure_flags, handle, cfg, drift_count_ref)       \
    do { DriftCtx<F> _drift_ctx{...};                                             \
         STAMP_BOUND_CFG_walk_filtered_rows(..., &emit_drift_check_per_row<F>, ...);\
    } while (0)
```

The runtime walker fn-pointer indirection + DriftCtx struct + per-row fn callback is structurally **different** from the X-macro per-row expansion that the sister AUTOPOPULATEs use. **Note: sidecar lines 247-302 still uses the SUPERSEDED `STAMP_BOUND_CFG_walk_filtered_rows` despite plan-body cleanup annotations** — body cleanup note at sidecar line 10-13 acknowledges this, but the sample code in § Step 8 lines 237-302 needs full rewrite to `CFG_FIELD_FOR_EACH_SET_BIT` form. The DriftCtx-fn-pointer indirection ALSO needs to be reconsidered if M-1 unification (per-row `gate_when` column) lands.

**Proposed unification (if M-1 accepted).** With per-row `gate_when` column in registry source, `CFG_DRIFT_AUTOPOPULATE` shape collapses to:

```cpp
#define X_CFG_DRIFT_AUTOPOPULATE_ONE(name, cfg_expr, gate_when)                   \
    if (gate_when && sr.has_##name && tt::cfg_drift_compare<T>(sr.name, cfg_expr)) { \
        sr.inference_cfg_drift_count++;                                           \
        BITMAP_SET(failure_flags, FAILURE_MASK_cfg_inference_drift);              \
    }

#define CFG_DRIFT_AUTOPOPULATE(sr, cfg, failure_flags)                            \
    do { FOREACH_CFG_DERIVED_DRIFT_CHECK(X_CFG_DRIFT_AUTOPOPULATE_ONE) } while (0)
```

Now sister-uniform with `STAMP_CFG_AUTOPOPULATE` + `INFERENCE_CFG_AUTOPOPULATE` shape. **No DriftCtx, no walker fn-pointer, no callback fn, no STAMP_BOUND_CFG_walk_filtered_rows even at the body-residual-cleanup-corrected form.**

**Win estimate.** ~50-80 LOC saved (DriftCtx + walker fn + 2 callback fns + helper plumbing). Sister-pattern consistency restored.

**Risk.** MED, coupled with M-1. Same plan-body amendment as M-1.

### M-4 (MED): Body residual cleanup deferred to coding time — risk of mid-implementation correction loop
**Section:** Plan body lines 10-17 + sidecar lines 8-14.

**Critique.** Plan body acknowledges ~7 sites use SUPERSEDED `STAMP_BOUND_CFG_walk_filtered_rows` + `DerivedFilterFramework` + `FOREACH_DERIVED_FILTER` references that need mechanical update at "update step" within `.B` audit→update→implement cycle. But sample code samples within both files **still encode the SUPERSEDED shape** (sidecar lines 247, 289-302; plan body Step 8 lines 262-275; Step 11 gate fns sidecar lookup logic still mixes new + old). This means coding agent reads contradictory samples: header text says "use `CFG_FIELD_FOR_EACH_SET_BIT`" but sample code at §Step 8 still walks via `STAMP_BOUND_CFG_walk_filtered_rows`.

**Proposed unification.** Apply the body residual cleanup IN THE `.B` UPDATE STEP (already planned per cycle discipline) — but BEFORE the implement step. M-1 + M-3 likely subsume most cleanup anyway. Confirm post-amendment all sample code in plan body + sidecar reflects Path γ + sister-AUTOPOPULATE uniformity.

**Win estimate.** ~30-45 min mechanical cleanup. **Already planned at `.B` update step** per cycle discipline — but coupling with M-1/M-3 amendments means cleanup grows from "mechanical sed" to "design re-think". Surface NOW so the cleanup work is bundled with structural decision.

**Risk.** LOW alone; MED if M-1/M-3 land late.

### M-5 (MED): `bandit_blend_ratio` already in `FOREACH_CFG_DERIVED_INFERENCE_CFG:108` with cohort gate — `.B`'s "DELETE manual POST_CFG entry" needs companion delete in derived registry?
**Section:** Plan body Step 6 (lines 408-412) + sidecar § Step 6 line 213.

**Critique.** Plan body says delete manual POST_CFG entry for `bandit_blend_ratio` at `StampBoundModelConstRegistry.hpp:295-297` because framework auto-generates equivalent from `STAMP_BOUND_CFG_DERIVED` bit. BUT `bandit_blend_ratio` is ALSO in `FOREACH_CFG_DERIVED_INFERENCE_CFG:108` with `gate_when = BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)`. After `.B` migration, three things flow:
1. Source row carries `STAMP_BOUND_CFG_DERIVED` (auto-flow into framework canonical body)
2. `INFERENCE_CFG_AUTOPOPULATE` row at line 108 (auto-flow into inf->bandit_blend_ratio via `STAMP_SET(inference_cfg)`)
3. Manual POST_CFG entry at `StampBoundModelConstRegistry.hpp:295-297` — DELETED

Risk: framework auto-generates POST_CFG entry **identical to deleted entry** OR is the populate semantics already handled by INFERENCE_CFG_AUTOPOPULATE (in which case neither manual POST_CFG nor framework auto-POST_CFG is needed — just the AUTOPOPULATE row is sufficient)? Plan body doesn't reconcile.

**Proposed unification.** Audit at coding time: which of the 3 paths owns each row's emit semantics post-migration? Likely: `STAMP_BOUND_CFG_DERIVED` bit drives canonical body; AUTOPOPULATE drives `inf->*` fill; manual POST_CFG is purely vestigial. Document the 3-path matrix per row at sidecar Step 6 + Step 7. Same applies to 4 `.A.7` retroactive migrations (`ml_tp_pct`, `ml_sl_pct`, `barrier_blend_mode`, `per_horizon_barrier_blend`) — they're also in `FOREACH_CFG_DERIVED_INFERENCE_CFG:120-123` already.

**Win estimate.** Prevents Class 18 (mirror-incomplete) latent if all 3 paths aren't reconciled. ~15-30 min audit at coding time.

**Risk.** LOW-MED. Audit gap, not direct bug.

---

## LOW

### M-6 (LOW): 5 cohort gate fns are appropriately atomic
**Section:** Sidecar § Step 8b lines 360-389.

**Verdict.** No shared structure across 5 fns; they're cleanly atomic — each pulls a different cfg flag + reads a unique cohort condition. **KEEP separate** (if β4 architecture survives M-1 critique; if it doesn't, fns dissolve anyway). LOW confidence merge candidate.

### M-7 (LOW): `tt::cfg_emit_synthetic_field<T>` shape consistent with sister `tt::` dispatch trio
**Section:** Sidecar § Step 1 lines 21-86.

**Verdict.** **PASS reuse audit.** Identical structure to `tt::cfg_parse_field<T>` / `tt::cfg_save_field<T>` at `CoreFrameworks/CfgFieldDispatch.hpp:46-155 / 169-220`: same `static_assert` type-family guard, same `if constexpr` branches, same FPN<F> / integral / floating / array dispatch. **GREEN.** Minor: snippets are missing the Layer 2 locale pin (existing `tt::cfg_save_field` lines 178-181 pins; sidecar's emit fn at line 41-83 does NOT). Add locale pin to `tt::cfg_emit_synthetic_field` for H9 byte-equivalence consistency. ~5 LOC fix at coding time.

### M-8 (LOW): Bitmap walker activation in `StampBoundDerivedFilter.hpp` Step 3 is mechanical X-macro pass
**Section:** Plan body Step 3 lines 348-373.

**Verdict.** Standalone X-macro walker over `FOREACH_ML_CFG_FLAG` with metadata-column filter. No opportunity to fold into FOREACH_CFG_FIELD (different storage class — bitmap vs scalar). KEEP separate. **No reuse-merge opportunity to surface.** LOW priority.

### M-9 (LOW): Legacy `FOREACH_STAMP_BOUND_CFG` empty-out + FOREACH_REGISTRY removal — verify CI script catches
**Section:** Plan body Step 12 lines 644-653.

**Verdict.** Mechanical. Plan body has explicit grep verification "`grep -r FOREACH_STAMP_BOUND_CFG` returns ZERO active code hits". `tools/check_meta_registry.py` enforces FOREACH_REGISTRY enrollment count match. **GREEN** as drafted; no merge opportunity.

### M-10 (LOW): 12+ consumer migration sites — comment text only, NO duplicate migration pattern
**Section:** § Item 9 plan body lines 234-256.

**Verdict.** 3 active sites (functional) + ~8-10 comment-only sites. Comment-only sites are mechanical sed; no helper macro/template warranted. **KEEP separate.** GREEN.

---

## Verdict + recommendation

**YELLOW** — top-3 highest-impact items:

1. **M-1 (CRITICAL).** Surface this Path γ-class structural critique to Caramel pre-coding. `FOREACH_DRIFT_GATE` sparse sidecar + dispatch table is the wrong shape for cohort gating — `FOREACH_CFG_DERIVED_INFERENCE_CFG`'s inline `gate_when` column is the canonical sister and should drive `CFG_DRIFT_AUTOPOPULATE` shape too.
2. **M-3 (MED).** Coupled with M-1. `CFG_DRIFT_AUTOPOPULATE` macro shape diverges from sister AUTOPOPULATE macros; collapse to uniform do-while-X-macro shape once M-1 lands.
3. **M-2 (HIGH).** Winsor parse-time validation should split: individual bounds via existing `WARN_ON_CLAMP` + descriptor clamp_min/max infrastructure; only cross-field `low < high` invariant needs new ad-hoc code (~5 LOC, not ~10).

Deferrable to coding-time (not pre-coding amendment):
- **M-4** body residual cleanup (already planned at `.B` update step; bundles with M-1/M-3 amendments).
- **M-5** 3-path audit on `bandit_blend_ratio` + 4 retroactive `.A.7` rows.
- **M-7** `tt::cfg_emit_synthetic_field<T>` Layer 2 locale pin.

Leave alone:
- **M-6** 5 cohort gate fns (dissolves if M-1 accepted; appropriate atomic if M-1 rejected).
- **M-8** bitmap walker is mechanical X-macro pass.
- **M-9** legacy empty-out is mechanical + verified.
- **M-10** comment-only sites; no helper warranted.

**Pre-coding plan body amendment required for M-1 + M-2 + M-3 (coupled). Recommendation:** consult Caramel on M-1 + M-3 collapse (uniform AUTOPOPULATE shape) and M-2 split (parse-time vs cross-field validation) BEFORE Step 0 pre-tag.

**Pattern recognition:** This is the same Path γ shape — `.A` planning missed the existing `FOREACH_METADATA_BIT` + `CFG_FIELD_FOR_EACH_SET_BIT` infrastructure; `.B` planning is missing the existing `FOREACH_CFG_DERIVED_INFERENCE_CFG` + `INFERENCE_CFG_AUTOPOPULATE` inline-gate-when canonical. Both are framework-discipline blindspots where the plan author proposed parallel infrastructure instead of extending the canonical sister pattern. Recommend Phase 2 pre-coding sweep dimension D6: "scan plan body for proposed-new-infrastructure that has canonical-sister-already-in-code at sibling registry".

---

## Cross-references

- **Plan body:** `subplans/2026-05-16-v5.15.5.F.4d.1.B-migration-consumer.md` v1.2
- **Sidecar:** `subplans/2026-05-16-v5.15.5.F.4d.1.B-migration-consumer-examples.md` v1.1
- **Canonical sister AUTOPOPULATE registry:** `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101-123` (FOREACH_CFG_DERIVED_INFERENCE_CFG + INFERENCE_CFG_AUTOPOPULATE)
- **Canonical sister AUTOPOPULATE registry:** `ML_Headers/StampBoundCfgRegistry.hpp:226-253` (STAMP_CFG_AUTOPOPULATE)
- **Cfg parse bounds infrastructure:** `CoreFrameworks/CfgFieldDispatch.hpp:70-71, 75-76, 141-151` + `CfgFieldRegistry.hpp:191-200` (DBL/INT payload with clamp_min/max + WARN_ON_CLAMP bit)
- **Winsor source rows:** `CfgFieldRegistry.hpp:569 (low) + 572 (high)`
- **Predecessor postmortem:** `postmortems/2026-05-17-v5.15.5.F.4d.1.A-postmortem.md`
- **Sprint-wide audit registry:** `plan_checks/2026-05-16-v5.15.5.F.4d.1-tech-debt-audit-findings.md`

---

**End of report.** Path γ-class critique surfaced (M-1); recommend pre-coding plan body amendment before Step 0.
