# /trace-deps report — v5.15.5.F.4d.1.B migration + consumer — 2026-05-17

**Plan body:** `subplans/2026-05-16-v5.15.5.F.4d.1.B-migration-consumer.md` (v1.2 Path γ context draft)
**HEAD verified against:** `39b9947` (post-`.A` ship)
**Skill methodology:** `tick-trader-percore-workspace/claude-skills/trace-deps/SKILL.md`

---

## Top-line verdict: **YELLOW**

Plan is structurally sound: `.A` framework infrastructure (FOREACH_METADATA_BIT row, mask auto-gen, `CFG_FIELD_FOR_EACH_SET_BIT`, `StampBoundDerivedFilter.hpp` stub) verified present at HEAD; sister `tt::` dispatch helpers (`cfg_parse_field<T>` / `cfg_save_field<T>` at `CfgFieldDispatch.hpp`) verified; all cohort source rows verified present with claimed line refs. **Two HIGH-severity findings require plan amendment before coding; one MED finding warrants test-scope expansion.** No blocking GAPs that would require structural redesign — corrections are localized to plan body Item 9 enumeration + Step 9 implementation steps.

---

## Findings

### HIGH-1 — `FOREACH_STAMP_BOUND_CFG(X)` active consumer enumeration INCOMPLETE
**Severity:** HIGH (Class 18 mirror risk during migration; underestimated blast radius)
**Files:** `ML_Headers/ModelInference.hpp:1199`, `:1401`, `:1643`, `:1788` (4 sites NOT cited in plan)
**Plan claim:** "Active consumer sites (3 verified at HEAD)" — `CoreModelZoo.hpp:243` + `StampHelper.hpp:150` + `ConfidenceScore.hpp:729` (lines 240-244 of plan body).
**Actual grep at HEAD:** SEVEN active `FOREACH_STAMP_BOUND_CFG(X)` invocation sites:
  - `CoreModelZoo.hpp:243` (drift loop; cited)
  - `StampBoundCfgRegistry.hpp:230` (STAMP_CFG_AUTOPOPULATE definition; sister registry self-walk; not a downstream consumer but framework-internal)
  - `StampBoundCfgRegistry.hpp:264` (FOREACH_STAMP_BOUND_CFG_COUNT definition)
  - **`ModelInference.hpp:1199`** — struct-field declaration walk (declares `has_<name>` + `<name>` for ModelStampResult)
  - **`ModelInference.hpp:1401`** — stamp parser walk (parses key=value lines into ModelStampResult fields)
  - **`ModelInference.hpp:1643`** — second struct gen walk (different ModelStampResult variant)
  - **`ModelInference.hpp:1788`** — stamp emitter walk (writes canonical body from inf->name)

These 4 `ModelInference.hpp` sites are the actual stamp-parser/struct-gen/canonical-emit consumers — load-bearing wire-format paths. Each takes a 7-arg X macro per current sig (line 1196, 1396, 1640, 1782 each define `#define X(name, type, fmt, default_val, get_cfg_expr, emit_when, emit_source)`). Migrating CFG_DRIFT_AUTOPOPULATE swap-in at `CoreModelZoo.hpp:243` only addresses 1 of 5 ModelInference-or-equivalent walker sites; the OTHER 4 still walk the legacy macro and MUST be migrated at Step 12 empty-out OR retained via wrapper.
**Recommended action:** Update Item 9 enumeration to ENUMERATE THE 4 MODELINFERENCE.HPP CONSUMER SITES (~lines 240-244 of plan body) + Step 9 + Step 12 (empty-out) MUST account for these 4 walker sites. Either:
  (a) Migrate all 4 ModelInference walks to derive from `STAMP_BOUND_CFG_DERIVED` filter via `CFG_FIELD_FOR_EACH_SET_BIT` (consistent with `.A`'s direction), OR
  (b) Document explicitly that ModelInference walker sites are wire-format byte-preservation surfaces and migrate them via the same canonical body emit path landed at `.A`'s `StampBoundDerivedFilter.hpp` (which already targets canonical body emit).
Without addressing these, "Step 12 — legacy registry empty-out" will fail to compile (4 callers referencing empty macro body).

### HIGH-2 — `ConfidenceScore.hpp:729` mischaracterized as active consumer
**Severity:** HIGH (stale-claim drift; plan describes non-existent migration)
**File:** `ML_Headers/ConfidenceScore.hpp:729`
**Plan claim:** "COUNT usage" — "Replace with X-macro reduction over the derived filter walk (count of flagged rows)" (Item 9 table + Step 9 site 3).
**Actual at HEAD:** Line 729 is a COMMENT inside `FOREACH_DEGRADATION_CURVE` machinery: `// would break later expansions). Same pattern as FOREACH_STAMP_BOUND_CFG_COUNT.`. NOT an active consumer; just a textual cross-reference.
**Real `FOREACH_STAMP_BOUND_CFG_COUNT` consumers** (grep result):
  - `tests/controller_test.cpp:4057, 4893, 22189, 25381` — 4 test assertions checking minimum row count
  - `StampBoundCfgRegistry.hpp:264` — the definition site
**Recommended action:** REMOVE `ConfidenceScore.hpp:729` from Item 9 active-consumer table. ADD the 4 `tests/controller_test.cpp` COUNT-assertion sites — these test sites WILL break post-migration (count will change from 24 to 0 once macro emptied; assertions check `>= 12 / 15 / 17`). Plan must either (a) update test expectations to walk new derived-filter `FOREACH_METADATA_BIT_COUNT(STAMP_BOUND_CFG_DERIVED)` macro, OR (b) replace each test with an equivalent assertion over derived filter mask popcount. Step 13 (tests) should explicitly call out these 4 test-fixture migrations.

### MED-1 — Plan body residual references to SUPERSEDED v1.0 framework symbols
**Severity:** MED (already flagged in plan body header; cycle discipline correct but blast radius understated)
**Files cited by plan itself:** Plan body lines 114, 234, 247, 260-265, 642, 827 — references `STAMP_BOUND_CFG_walk_filtered_rows(...)` and `FOREACH_DERIVED_FILTER` (both don't exist at HEAD; superseded by FOREACH_METADATA_BIT + CFG_FIELD_FOR_EACH_SET_BIT per Path γ).
**Status:** Plan body header (lines 10-17) ACKNOWLEDGES this residual + plans mechanical cleanup at `.B` update step.
**Stale-claim verified:**
  - `STAMP_BOUND_CFG_walk_filtered_rows` — grep CONFIRMS does NOT exist at HEAD (zero hits in source). Plan body lines 234, 247, 260-265, 269-274 prescribe consumer migration to this nonexistent walker.
  - `FOREACH_DERIVED_FILTER` — grep CONFIRMS does NOT exist at HEAD (zero hits). Plan body lines 605-608 (FOREACH_REGISTRY enrollment row for FOREACH_DRIFT_GATE) cite `PARENT=DERIVED_FILTER` referencing a registry that wasn't built.
**Recommended action:** Apply the listed mechanical corrections at `.B` update step BEFORE coding Step 0. Replace `STAMP_BOUND_CFG_walk_filtered_rows(g_*_descriptors, FIELD_IDX_*_END, &cb, &ctx)` → `CFG_FIELD_FOR_EACH_SET_BIT(g_*_cfg_stamp_bound_cfg_derived_mask.words, idx, { ... })` (verified to exist at `CfgFieldRegistry.hpp:1076` row, `:1082-1089` X_GEN_*_MASK auto-gen, `:1288` CFG_FIELD_FOR_EACH_SET_BIT macro). Replace `FOREACH_DERIVED_FILTER` PARENT in Step 11 FOREACH_REGISTRY enrollment with the actual parent registry (`FOREACH_PER_CORE_CFG_FIELD` + `FOREACH_GLOBAL_CFG_FIELD` are the cfg-side registries; `FOREACH_METADATA_BIT` is the metadata-bit registry — choose per `.A`'s actual enrollment shape — verify against `MetaRegistry.hpp` post-`.A`).

### LOW-1 — `MlCfgFlagRegistry.hpp:52+` line-ref off by 1 (cosmetic)
**Severity:** LOW
**File:** `ML_Headers/MlCfgFlagRegistry.hpp`
**Plan claim:** "12 existing rows" at `:52+`.
**Actual:** Comment "Tuple: X(NAME, ...)" at `:51`, `#define FOREACH_ML_CFG_FLAG(X)` at `:52`, rows at `:53-64` (12 rows, exact). Plan's per-row line refs (e.g., `RIDGE_WITHIN_HORIZON (line 60)` → confirmed `:60`) are accurate. The "starts at line 52" framing is mechanically right (macro definition starts at `:52`); the rows themselves are at `:53-64`.
**Recommended action:** No change required; cosmetic only.

### LOW-2 — `StampBoundModelConstRegistry.hpp:295-297` `bandit_blend_ratio` POST_CFG entry line range
**Severity:** LOW
**File:** `ML_Headers/StampBoundModelConstRegistry.hpp`
**Plan claim:** `:295-297`
**Actual:** X-macro entry at `:296-297` (comment header at `:295`: `/* === bandit (standalone) — emitted at line 2189 === */`). Plan's range is acceptable since comment header is part of the entry's context.
**Recommended action:** No change required.

---

## Per-symbol verification matrix

| Plan-cited symbol/site | Status at HEAD `39b9947` |
|---|---|
| `STAMP_BOUND_CFG_DERIVED` metadata bit (declared) | **PASS** — `CfgFieldRegistry.hpp:149` (1u<<13) + `:1076` FOREACH_METADATA_BIT row + `:1082-1089` mask auto-gen |
| `gap_acceptable_threshold` field already exists | **PASS** — `ControllerConfig.hpp:889` field decl; manual parser at `:2554`; **plan correctly identifies need for X-macro row** (no source row in FOREACH_GLOBAL_CFG_FIELD verified via grep) |
| `tt::cfg_emit_synthetic_field<T>` (NEW helper) | **PASS (NEW; zero existing references)** — only DESIGN_SPECS comments at `StampBoundDerivedFilter.hpp:22+39+54` and `Version.hpp:142` reference it. Sister helpers exist: `tt::cfg_parse_field<T>` at `CfgFieldDispatch.hpp:52,59,302`; `tt::cfg_save_field<T>` at `:176,303`. Consistent dispatch trio pattern. |
| `FOREACH_DRIFT_GATE` / `DriftGateKind` / `g_drift_gate_table` (NEW sidecar) | **PASS (NEW)** — zero references at HEAD; sister `FOREACH_PER_CORE_CFG_FIELD` + `FOREACH_GLOBAL_CFG_FIELD` exist at `CfgFieldRegistry.hpp:255,419`. Sparse-sidecar pattern shape valid per `sidecar-override-pattern-for-registry-auto-flows.md`. |
| `CFG_DRIFT_AUTOPOPULATE` (NEW companion macro) | **PASS (NEW; sister to existing)** — sister `STAMP_CFG_AUTOPOPULATE` at `StampBoundCfgRegistry.hpp:226`; sister `INFERENCE_CFG_AUTOPOPULATE` at `StampHelper.hpp:183`. Consistent trio. |
| Winsor parse-time validation insertion at `ControllerConfig.hpp` parser post-parse | **PASS** — `CFG_PARSE_FPN(winsor_pct_low)` and `(winsor_pct_high)` parsed via existing CFG_PARSE_FPN macros; post-parse insertion can occur after the parse block (~line 2554+). Plan-cited "ControllerConfig.hpp parser" anchor is correct. |
| `CfgFieldRegistry.hpp:524` `ml_buy_threshold` (NO STAMP_BOUND bit) | **PASS** — verified: row at `:524` carries `0` in metadata_flags position (no STAMP_BOUND bit) |
| `CfgFieldRegistry.hpp:528` `bandit_blend_ratio` (NO STAMP_BOUND bit) | **PASS** — verified: row at `:528` carries `0` in metadata_flags position |
| `CfgFieldRegistry.hpp:525-526` `ml_tp_pct` + `ml_sl_pct` (`.A.7` retro cohort) | **PASS** — verified at `:525-526` |
| `CfgFieldRegistry.hpp:637` `barrier_blend_mode` (`.A.7` retro cohort) | **PASS** — verified at `:637` |
| `MlCfgFlagRegistry.hpp:53-64` 12 rows + `:70` X_GEN_ML_CFG_BIT + `:82` X_GEN_ML_CFG_MASK | **PASS** — verified all line refs; 12 rows at `:53-64`; consumer macros at `:70` + `:82-83`; AUTOPOPULATE_FROM_SEPTUPLE at `:92-103` is hand-written and correctly excluded from sig migration per plan |
| `StampBoundCfgRegistry.hpp:99-179` legacy registry empty-out range | **PASS** — `#define FOREACH_STAMP_BOUND_CFG(X)` at `:99`; final row (trading_mode) at `:178-179`; cohort range correct (`:99-179`) |
| `StampBoundModelConstRegistry.hpp:295-297` `bandit_blend_ratio` POST_CFG | **PASS (with cosmetic line-ref noted under LOW-2)** |
| `CoreModelZoo.hpp:225-247` drift loop | **PASS** — verified: drift-loop block at `:228-248`; `FOREACH_STAMP_BOUND_CFG(X)` invocation at `:243`; `sr.inference_cfg_drift_count++` at `:235` |
| `StampHelper.hpp:150` populate walk anchor | **PASS** — comment at `:150` ("Walks FOREACH_STAMP_BOUND_CFG and populates inf.<field>"); actual `STAMP_CFG_AUTOPOPULATE(inf, cfg)` invocation at `:156` |
| `ConfidenceScore.hpp:729` COUNT usage | **GAP — see HIGH-2 finding** |
| `ModelInference.hpp:1199, 1401, 1643, 1788` walker sites (4 ADDITIONAL) | **GAP-MISSING-FROM-PLAN — see HIGH-1 finding** |
| 4 `tests/controller_test.cpp` count assertions (`:4057, 4893, 22189, 25381`) | **GAP-MISSING-FROM-PLAN — must be migrated at Step 13 — see HIGH-2** |

---

## Mirror data-flow + call-sequence audit

`.B` is migration only (no mirror in the "duplicate X for Y" sense). Per-cohort `gate_when` predicates are NEW dispatch via FOREACH_DRIFT_GATE sparse sidecar — replaces existing inline-X-macro `emit_when` expressions in legacy registry (`StampBoundCfgRegistry.hpp:108, 110, 113, 115, 117, 125, 127, 129, 131, 133, 137-138, 140-141, 145, 149, 151, 153, 155, 158, 160, 164, 166, 168, 170, 173`). All gate functions (`gate_default`, `gate_bandit_thompson`, `gate_risk_degradation`, `gate_ridge_any`, `gate_composite_confidence`) use only existing primitives (`STAMP_HAS`, `BITMAP_IS_SET`, `BITMAP_ANY`, ml_cfg_flags field). No transitive dependency gaps.

---

## Recommendations summary (priority order)

1. **BLOCKING — apply residual body cleanup BEFORE Step 0** (MED-1; already scheduled per plan body header).
2. **BLOCKING — expand Item 9 consumer enumeration** to add 4 ModelInference.hpp walker sites + remove ConfidenceScore.hpp:729 + add 4 controller_test.cpp count-assertion sites (HIGH-1 + HIGH-2). Update Step 9 + Step 12 + Step 13 to account.
3. **Verify FOREACH_DRIFT_GATE FOREACH_REGISTRY parent** — plan body Step 11 cites `PARENT=DERIVED_FILTER`; this registry doesn't exist per Path γ — set to actual parent registry (likely a meta-registry topology decision; check `MetaRegistry.hpp` post-`.A`).
4. **Test expectations** — Step 13 must specify migration of `FOREACH_STAMP_BOUND_CFG_COUNT` test assertions to derived-filter popcount equivalents (else 4 tests immediately fail after Step 12 empty-out).
5. **Re-run `/parity-check`** post-amendment to verify the 4 `ModelInference.hpp` walker sites are wire-format-byte-preserved post-migration (highest-stakes surface for HMAC chain integrity).

---

## Verdict rationale

YELLOW (not RED) because: no symbol GAPs that block coding; the framework infrastructure landed at `.A` (verified); sister `tt::` dispatch + AUTOPOPULATE patterns exist; cohort source rows exist with correct line refs. YELLOW (not GREEN) because: plan body's "3 active consumer sites" enumeration is materially incomplete (4 ModelInference.hpp sites + 4 test assertion sites unrecognized), and one cited site (`ConfidenceScore.hpp:729`) is stale-mischaracterized. These are addressable mechanical corrections, not structural redesigns — but they MUST be reflected in plan body before Step 0, else Step 12 empty-out will break the build and Step 13 test count will diverge by >4 immediately.
