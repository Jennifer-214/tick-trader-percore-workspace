# /accounting-audit findings — 2026-05-17 v5.15.5.F.4d.1.B.2 (cohort migration)

**Target plan:** `subplans/2026-05-17-v5.15.5.F.4d.1.B.2-cohort-migration.md` v1.0 DRAFT
**Engine HEAD:** `725fe46` (`v5.15.5.F.4d.1.B.1` shipped LOCALLY; awaits engine remote push)
**Scope shape:** plan-time audit (Batch 1 pre-coding gate) — focused on accounting-specific concerns per parent task brief

## Summary

- **CRITICAL:** 2
- **HIGH:** 3
- **MEDIUM:** 4
- **LOW:** 2
- **DOC:** 1

**Top-line verdict: YELLOW.** Two CRITICALs are plan-doc accuracy gaps that, if left unaddressed at the body level, lead to silent miscalculation at implementation time. Both are remediable by plan body amendment without scope expansion. HIGHs and MEDs surface latent Class 27 / per-core flatten risk in the cohort fields and a wire-format procedural gap (stamp_format_version=1 has not changed since v5.9.0 — the plan body's bump procedure documentation is the FIRST canonical application).

The good news: the .B.1 framework structurally bakes in the bumped-emit + filtered-walker shape; the cohort migration's bytecount + drift behavior is largely auto-enforced. Most accounting hazards live in the wider sweep around what cohort fields are read at per-fill / per-event time, which the plan body should enumerate before coding.

---

## Findings

### [CRITICAL-1] Plan body states `FOREACH_CFG_DERIVED_INFERENCE_CFG` was "DELETED at `.B.1`" but engine HEAD still has it (`MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101` + `MetaRegistry.hpp:99` + `StampHelper.hpp:183`)
- **Severity:** CRITICAL
- **Category:** 7 (Backtest ↔ live accounting parity — wire format), DOC accuracy
- **Class:** N/A (plan-doc drift; if uncorrected, leads to Class 18 mirror at coding time)
- **Details:** Plan body line 111 in "Canonical sister registries considered" table states `FOREACH_CFG_DERIVED_INFERENCE_CFG` is "(eliminated at `.B.1`)" with verdict "**DELETED** — Already removed by `.B.1` framework consolidation". Engine HEAD `725fe46` evidence to the contrary:
  - `MemHeaders/CfgDerivedInferenceCfgRegistry.hpp:101` — `FOREACH_CFG_DERIVED_INFERENCE_CFG(X)` macro alive with 16 entries
  - `CoreFrameworks/MetaRegistry.hpp:99` — registry enrolled with annotation "legacy; deletion deferred to .B.3 after .B.2 cohort migration validates new framework"
  - `ML_Headers/StampHelper.hpp:183` — `INFERENCE_CFG_AUTOPOPULATE(inf, cfg);` production call ALIVE in `Stamp_AssembleAndEmit`
  - `tests/controller_test.cpp:24981` — `FOREACH_CFG_DERIVED_INFERENCE_CFG_COUNT == 16` test passing
  - `Version.hpp:13` — also documents legacy as still-alive ("sidecar duplicated canonical FOREACH_CFG_DERIVED_INFERENCE_CFG; eliminated entirely" refers to the would-have-been β4 PARALLEL sidecar; canonical NOT yet eliminated)

  Misclaim of "DELETED" in plan body Decision 1's sister registry table means coder may build on the assumption that legacy registry is gone — which would lead to mid-`.B.2` discovery that `.B.2` must coexist with `.B.1` framework AND legacy `FOREACH_CFG_DERIVED_INFERENCE_CFG` until `.B.3` empties both. The plan body's Step 7 walker migration is more carefully phrased ("`.B.3` deletes legacy") but the table-level claim contradicts the step-level claim.

- **Recommended fix:** Plan body amendment v1.0 → v1.1:
  - Line 111: change `FOREACH_CFG_DERIVED_INFERENCE_CFG` row verdict from "**DELETED** — Already removed by `.B.1`" to **"NO-CHANGE (coexists until `.B.3`)** — Legacy `INFERENCE_CFG_AUTOPOPULATE` walker at `StampHelper.hpp:183` STAYS ALIVE through `.B.2`; new framework's `INFERENCE_CFG_POPULATE_FROM_DERIVED` walker runs in parallel from the same `Stamp_AssembleAndEmit` site producing the same observable `inf.inference_cfg_*` fields. `.B.3` empties + deletes legacy."
  - Confirm: at `.B.2` ship close, BOTH `INFERENCE_CFG_AUTOPOPULATE(inf, cfg)` AND `INFERENCE_CFG_POPULATE_FROM_DERIVED(inf, cfg)` are called from `StampHelper.hpp:Stamp_AssembleAndEmit` (the legacy call already exists; the new call is added at Step 7's 7.5 OR at `.B.3` after legacy emptied). Plan body should make this explicit.
- **DESIGN_SPEC:** `wire-format-byte-preservation-discipline.md` § Layer 5b
- **CI Check:** N/A (plan-doc; cross-validate at handoff/readiness recheck)

### [CRITICAL-2] Step 8 implements `stamp_format_version` bump as a constant in `ModelInference.hpp` — but engine evidence shows it's a `int` field per stamp, with value HARDCODED `1` at emit (`ML_Headers/ModelInference.hpp:1747` + `:1172` + `:1346-1351`)
- **Severity:** CRITICAL
- **Category:** 1 (cfg-parse robustness), 7 (Backtest ↔ live accounting parity)
- **Class:** N/A (Step 8 plumbing accuracy)
- **Details:** Plan body Step 8 line 678 says "bump the constant by 1" with example `static constexpr uint32_t STAMP_FORMAT_VERSION = 7;  // was 6`. Engine HEAD `725fe46` shows the actual mechanism is NOT a `static constexpr` — instead, the emit at line 1747 is `"stamp_format_version=1\n"` (hardcoded literal `1`), and the parser at `:1346-1351` reads the value into `r.stamp_format_version` (int field on `ModelStampResult`). There is NO existing `STAMP_FORMAT_VERSION` constant in the engine. Comment at line 1718 says "Bumped on future stamp body schema changes" — but no actual bump path exists yet; `.B.2` is the FIRST such bump.

  Implications:
  1. Step 8 plumbing as written ("Locate `stamp_format_version` constant; bump by 1") will not find a constant — it would find the hardcoded literal `1` at one site
  2. Bumping `1` → `2` at line 1747 in the emit BUT not updating the parser-side bound check (currently `r.stamp_format_version = atoi(val);` accepts any int; no upper bound enforcement) means old engine reading new stamps would silently parse-succeed + then drift-fail on the field-order change (not "version mismatch" — would be raw HMAC mismatch). That's the very behavior CRIT-6 (a) intends to PREVENT.
  3. There's no verifier-side enforcement that mandates "fail with explicit version mismatch error if stamp_format_version > supported version". The plan body Step 9.4 test expects "verify mismatch produces expected `stamp_format_version` mismatch failure" — but the current verifier doesn't produce this; it produces an HMAC mismatch.

- **Recommended fix:** Plan body Step 8 amendment v1.0 → v1.1 to specify three concrete deliverables (not "bump the constant"):
  1. **Emit site:** `ML_Headers/ModelInference.hpp:1747` — change hardcoded `"stamp_format_version=1\n"` → `"stamp_format_version=2\n"` (or `static constexpr int STAMP_FORMAT_VERSION = 2;` introduced at file scope + referenced as `stamp_format_version=%d`)
  2. **Verifier-side enforcement:** Add `MAX_SUPPORTED_STAMP_FORMAT_VERSION` constant + bounds-check at `:1346-1351` parse — if `r.stamp_format_version > MAX_SUPPORTED_STAMP_FORMAT_VERSION` set explicit `STAMP_VERIFY_VERSION_UNSUPPORTED` failure flag (not generic parse error). Currently no version validation occurs.
  3. **Test fixture:** A v5.14-era stamp with `stamp_format_version=1` body bytes loaded against `.B.2` engine should produce explicit "supported version=2, stamp has version=1" mismatch OR HMAC body-byte-order-different signal — currently neither exists. Plan body Step 9.4 NEEDS to enumerate test for "old fixture loaded by new engine produces explicit version-failure-mode" (not just "expect HMAC fail" — which is undiagnosable).
- **DESIGN_SPEC:** `wire-format-byte-preservation-discipline.md` § Layer 5b (amendment per Step 8 per Decision 1 (a))
- **CI Check:** Add Step 9.4 specific test → assert `r.stamp_format_version >= 2` post-bump; assert v5.14 fixture parse produces explicit failure flag (not silent HMAC mismatch)

---

### [HIGH-1] `risk_degradation_curve` listed in plan body Step 1's "Per-core (17 rows)" table — but field has TWO live cfg surfaces (top-level flat field at `ControllerConfig.hpp:710` AND `FOREACH_PER_CORE_CFG_FIELD` row at `CfgFieldRegistry.hpp:608`) — accounting paths may read either
- **Severity:** HIGH
- **Category:** 1 (Class 27 candidate; per-core flatten risk), 2 (per-core indexing)
- **Class:** Class 21 candidate (parallel cfg surfaces)
- **Details:** `risk_degradation_curve` exists in TWO places at engine HEAD:
  - Top-level flat: `ControllerConfig.hpp:710` — `int risk_degradation_curve;             // default 0 (OFF)`
  - Per-core: `CfgFieldRegistry.hpp:608` — X-macro entry in `FOREACH_PER_CORE_CFG_FIELD` with metadata `STAMP_BOUND | HAS_SIDE_EFFECT | WARN_ON_CLAMP`

  Per plan body Step 5 line 497, the cfg-gate sidecar reads `cfg.risk_degradation_curve != 0` — this READS THE GLOBAL TOP-LEVEL field, not `cfg.cores[c].risk_degradation_curve`. Same for risk_full_size_threshold (line 726), risk_min_size_threshold (line 729), risk_min_size_pct (line 735). But these fields are ALSO in `FOREACH_PER_CORE_OVERRIDABLE_INT_FIELDS` (line 200-203 via `RAW()` macros) — meaning they can be set per-core via `core_N_risk_degradation_curve=...`. The per-core value goes into `cfg.cores[c].risk_degradation_curve` BUT the cfg-gate sidecar in plan body Step 5 reads the GLOBAL `cfg.risk_degradation_curve`. Implications:
  - Production drift check fires uniformly across cores (gate reads global; if `cfg.risk_degradation_curve=0` globally but `cfg.cores[1].risk_degradation_curve=1`, the per-core 1's stamp won't have risk_full_size_threshold emitted, but training would have included it → silent drift)
  - Accounting paths in `Strategies/StrategyParameters.hpp:1519-1521` read `core_cfg->risk_full_size_threshold` (per-core via `core_cfg` pointer) — these are CORRECT per-core reads
  - Plan body Step 1's table classifies all 4 risk fields as "Per-core" in the metadata bit-add table — yes structurally per-core, but the cfg-gate's `cfg.risk_degradation_curve != 0` predicate reads the GLOBAL flat field. The plan body should clarify.

- **Recommended fix:** Plan body amendment v1.0 → v1.1 to:
  1. Step 5 sidecar gate expression: change `cfg.risk_degradation_curve != 0` → either `cfg.cores[0].risk_degradation_curve != 0` (per-core indexed) OR keep global with explicit note ("intentional: stamp emit gate uses global cfg; per-core overrides DO carry through stamp via cfg.cores[c] flow"). Surface decision in plan body design space.
  2. Per-core accounting consumer audit: cite `StrategyParameters.hpp:1519` reading `core_cfg->risk_full_size_threshold` AS THE INTENDED per-core read pattern; cohort migration should not break this (it shouldn't — only metadata bit-add). Add to verification gate: "post-`.B.2`, `StrategyParameters.hpp:1519` reads still go through `core_cfg` per-core; no global cfg.risk_full_size_threshold reads introduced".
  3. Audit: Step 5 cfg-gate sidecar expressions reading `cfg.<name>` (no `cores[c]` indexing) — is this intentional or a per-core flatten? Same Q applies to all 4 soft-risk fields + composite confidence + ridge + bandit/thompson (all of which use `cfg.ml_cfg_flags` global — that's correct, ml_cfg_flags IS global single-bitmap; but the underlying field values are per-core).
- **DESIGN_SPEC:** `cfg-scope-discipline.md`; `decision-time-data-binding-pattern.md`; CLAUDE.md item 31
- **CI Check:** Plan body Step 9 should add test: "set cfg.cores[1].risk_degradation_curve=1 with global=0; verify per-core stamp includes risk_full_size_threshold (gate triggers from per-core); verify drift check correctly fires per-core"

### [HIGH-2] Step 5 sidecar gate `cfg.bandit_algorithm == 4` reads GLOBAL `cfg.bandit_algorithm` but field is in `FOREACH_PER_CORE_CFG_FIELD` (per-core via `cfg.cores[c].bandit_algorithm`)
- **Severity:** HIGH
- **Category:** 2 (per-core indexing), 1 (Class 27 candidate)
- **Class:** Class 21 sibling to HIGH-1
- **Details:** Plan body Step 5 line 486: `X(thompson_exp3_blend_alpha,        cfg.bandit_algorithm == 4)`. `bandit_algorithm` at `CfgFieldRegistry.hpp:599` is in `FOREACH_PER_CORE_CFG_FIELD` section header "Per-core ML bandit cohort" (around line 595-600 — same section as ridge/composite/winsor). But `cfg.bandit_algorithm` direct access reads the FLAT top-level field (which is the "global default" / "all cores inherit" sentinel). If core-1 has `bandit_algorithm=4` (BLENDED) but global has `bandit_algorithm=0` (EXP3), the stamp gate reads global=0 → thompson_exp3_blend_alpha NOT emitted to stamp → core-1's training-time blend ratio is silently dropped from the stamp body → drift check at load fires spuriously when stamp loaded against `cfg.cores[1]` with blend=4.
- **Recommended fix:** Same as HIGH-1 — clarify gate-expression semantics for per-core fields. Option A: per-core indexed (gate evaluates per-core). Option B: keep global with explicit note + verify all consumers use core_cfg indirection. Document in Step 5.
- **DESIGN_SPEC:** `cfg-scope-discipline.md`; CLAUDE.md item 31
- **CI Check:** Test: set `cfg.cores[0].bandit_algorithm=0`; `cfg.cores[1].bandit_algorithm=4` (BLENDED); stamp written from core-1 should include `thompson_exp3_blend_alpha=...`; stamp from core-0 should NOT include it.

### [HIGH-3] Plan body Step 8 (CRIT-6 (a) implementation) lacks `stamp_format_version` bumping PROCEDURE documentation in `wire-format-byte-preservation-discipline.md` — but plan body assumes the spec is amended
- **Severity:** HIGH (procedural gap; not silent miscalculation but ship-blocker for the spec amendment claim)
- **Category:** DOC accuracy
- **Class:** N/A
- **Details:** Plan body line 681 says "Document procedure in `DESIGN_SPECS/wire-format-byte-preservation-discipline.md` § 'Framework refactor wire-format changes'". Plan body line 147 says "DESIGN_SPECS/wire-format-byte-preservation-discipline.md v? — amendment per CRIT-6 outcome (if (a) chosen: document `stamp_format_version` bump procedure as the canonical mechanism for framework-refactor wire-format changes)". This is a FIRST-OF-KIND amendment — no prior bump has occurred (engine `STAMP_FORMAT_VERSION=1` since v5.9.0; no precedent for what a bump entails). The procedure to be documented is:
  1. Specify HOW to bump (constant vs hardcoded literal; emit-time vs cfg-time; see CRIT-2)
  2. Specify WHAT to do when verifier sees stamp_format_version < supported
  3. Specify v5.14 fixture regeneration path (does engine ship with multi-version verifier compatible with both v=1 and v=2 stamps, or hard-cut at v=2?)
  4. Specify when to bump in future (this plan body's Decision 1 (a) sets the precedent — what's the trigger? "When master-registry-walk order changes"? "When new cohort fields added"?)

  Plan body Step 8 implementation does NOT actually write this DESIGN_SPEC amendment — it just says "document procedure". A `.B.2` close without this body being written means the spec stays unchanged + future bumps lack a referenceable precedent.

- **Recommended fix:** Plan body Step 8 amendment v1.0 → v1.1: explicitly add to deliverables list: "Write NEW section in `wire-format-byte-preservation-discipline.md` titled 'Stamp format version bump procedure (framework refactor / cohort migration)' with 4 subsections: (1) When to bump, (2) Bump mechanism (emit-site + parser-bounds), (3) Backward compatibility expectations, (4) v5.14 fixture handling". Mark as "Stage 3 first reference at `.B.2` ship close" per pattern-codification-lifecycle.md.
- **DESIGN_SPEC:** `wire-format-byte-preservation-discipline.md` — needs NEW section per Step 8
- **CI Check:** Plan body Step 10 verification gate should include "DESIGN_SPECS amendment lands at ship close" item

---

### [MED-1] Cohort migration introduces no scalar cfg-mirror caches — but `bandit_blend_ratio` (Step 3 sub-item) is read on accounting/decision paths that should be audited (`MlCfgFlagRegistry.hpp` + `StampBoundModelConstRegistry.hpp:295`)
- **Severity:** MEDIUM
- **Category:** 1 (Class 27 candidate)
- **Class:** Class 27 latent — same as HIGH-4 in prior `.B` accounting-audit; cohort migration doesn't introduce, but doesn't structurally close either
- **Details:** Plan body Step 3 line 421-422 deletes `bandit_blend_ratio` manual POST_CFG entry at `StampBoundModelConstRegistry.hpp:295`. Engine evidence: this field is read in `StampHelper.hpp:185` via `STAMP_SET(inf, inference_cfg_bandit_blend_ratio);` — gated by `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)`. The field flows to stamp via `inf.inference_cfg_bandit_blend_ratio`. NO direct accounting-path consumer found at HEAD via grep on `cfg.bandit_blend_ratio` outside stamp emit / drift check. So at `.B.2` close, the field is STAMP-ONLY (training-time emit + load-time drift check). NOT a Class 27 instance.

  HOWEVER: if `.F.5` (now absorbed) introduces per-core `bandit_blend_ratio` AND if downstream accounting paths begin reading it for fee/PnL calc (e.g., blend-weighted-fee per arm), the field falls into Class 27 territory. Cohort migration doesn't introduce this risk — but the plan body should note the assumption (read-at-stamp-only) so future ship cohorts know the constraint.

- **Recommended fix:** Plan body Step 3 amendment v1.0 → v1.1: add comment "After cohort migration, `bandit_blend_ratio` remains stamp-only consumer (no accounting-path reads). If future ship makes `bandit_blend_ratio` read at per-fill / per-event time, pre-resolve onto Order/Event object per decision-time-data-binding-pattern.md (Class 27 prevention)". Add to Step 9.3 verification: grep-verify no production accounting path reads `cfg.bandit_blend_ratio` directly.
- **DESIGN_SPEC:** `decision-time-data-binding-pattern.md`; RECURRING_BUG_PATTERNS Class 27

### [MED-2] Step 6 Winsor parse-time validation uses `FPN_ToDouble` then `>=` comparison — H4 compliant (parse-time, not accounting path) but locale-pinning question
- **Severity:** MEDIUM
- **Category:** 4 (H4), 5 (lossy FPN_ToDouble), 6 (locale pinning)
- **Class:** N/A
- **Details:** Plan body Step 6 line 523-527 + line 234-241 sample:
  ```cpp
  if (FPN_ToDouble(cfg.winsor_pct_low) >= FPN_ToDouble(cfg.winsor_pct_high)) {
      fprintf(stderr, "[cfg] WARN: ...%.4f...%.4f...", ...);
      cfg.winsor_pct_low  = FPN_FromDouble<F>(0.005);
      cfg.winsor_pct_high = FPN_FromDouble<F>(0.995);
  }
  ```
  H4 evaluation: This is parse-time validation (post-cfg-load, pre-engine-run) — NOT on hot path. H4 permits double conversion here. ✓
  Lossy FPN_ToDouble: For comparison-only (no roundtrip storage), the lossy conversion is acceptable per `DESIGN_PHILOSOPHY.md` § H4 row. ✓
  Locale pinning: `fprintf(stderr, ...%.4f...)` outputs depend on current locale (would emit `0,005` on FR locale). Display-only here (not wire format) — locale impact is operator UX only. ✓
  Hot path: parse-time, called once at boot — not on hot path. ✓

  However: the COMPARISON `>=` uses double-arithmetic — if `winsor_pct_low = FPN_FromDouble(0.005)` and `winsor_pct_high = FPN_FromDouble(0.005)` (both equal — operator typo), comparison should fire correctly. If `winsor_pct_low = FPN_FromDouble(0.005)` and `winsor_pct_high = FPN_FromDouble(0.005000000000001)` (slightly above) — FPN<F=64> distinguishes these (way more than 53-bit double precision); but `FPN_ToDouble` collapses both to the same double → comparison `low < high` evaluates as `low == high` → FALSE → predicate `>=` fires → defaults applied → operator unaware of the high-precision intent. Edge case unlikely in practice; flag for awareness.

- **Recommended fix:** Plan body Step 6 amendment v1.0 → v1.1 — minor: prefer FPN-native comparison `cfg.winsor_pct_low >= cfg.winsor_pct_high` (operator overload exists on FPN<F>; `<algorithm>` comparisons via op>=) over `FPN_ToDouble(...) >= FPN_ToDouble(...)` to avoid the FPN<F=64> → double precision collapse. Verify FPN<F> has `operator>=` defined; if not, fall back to current shape with comment. Optional: change `fprintf(...%.4f...)` to locale-pinned `%.4g` or similar to keep operator log consistent across locales.
- **DESIGN_SPEC:** H4; FPN<F> arithmetic; locale-pinning sister pattern
- **CI Check:** N/A (no test surface)

### [MED-3] Plan body Step 5 sidecar gates do NOT depend on per-core variation but use `BITMAP_IS_SET(cfg.ml_cfg_flags, ...)` consistently — verify `cfg.ml_cfg_flags` is GLOBAL not per-core
- **Severity:** MEDIUM
- **Category:** 2 (per-core indexing verify)
- **Class:** Sister to HIGH-1/HIGH-2
- **Details:** Plan body Step 5 lines 481-506 use `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)`, etc. for cohort gates. `cfg.ml_cfg_flags` engine inspection: search at `MlCfgFlagRegistry.hpp` (the bitmap). If `ml_cfg_flags` is single-global bitmap (matches `FOREACH_ML_CFG_FLAG` 12-row enrollment all from "FoxML" + "ML/Ridge" + "Performance" sections), gates read consistently across cores → CORRECT pattern (the bandit-enabled FLAG is global; each core observes the same flag bitmap). If `ml_cfg_flags` becomes per-core in future (e.g., `cfg.cores[c].ml_cfg_flags`), all 20 sidecar entries silently flatten to global → all cores see the same gate result.

  Engine evidence search needed: `grep cfg.ml_cfg_flags` to confirm single-global usage pattern at HEAD.

- **Recommended fix:** Plan body Step 5 amendment v1.0 → v1.1: cite at top of Step 5 (line 477) the verification that `cfg.ml_cfg_flags` is global single-bitmap not per-core. If future ship makes it per-core, the 20 sidecar entries need parallel updating. Add to verification gate as documentation note.
- **DESIGN_SPEC:** `multi-bit-state-encoding-pattern.md` (bitmap is multi-bit-state-encoded)

### [MED-4] Plan body Step 1's `risk_min_size_pct` field row lookup ambiguous (line 351: "search line via Step 1 grep")
- **Severity:** MEDIUM
- **Category:** DOC accuracy
- **Class:** N/A
- **Details:** Plan body Step 1 line 351 says `risk_min_size_pct` is at "(search via grep — likely `:617` or `:620`)". Engine HEAD `725fe46` shows it at `CfgFieldRegistry.hpp:617` (exact line). Plan body should resolve to exact line before coding to avoid coding-time guess + potential mistake (especially in 18-row mechanical sequence where missing one row is silent).
- **Recommended fix:** Plan body Step 1 amendment v1.0 → v1.1: change line 351 to "`risk_min_size_pct` | `:617` | Risk Management" (exact line). One-character edit.

---

### [LOW-1] Step 6 Winsor validation message in stderr is operator-facing; consider `%.5f` precision for the `winsor_pct_*` defaults
- **Severity:** LOW
- **Category:** Operator UX
- **Details:** Plan body Step 6 lines 524-526 use `%.4f` in the WARN message. Default values are `0.005` (low) + `0.995` (high) — `%.4f` produces `0.0050` + `0.9950` (acceptable). If operator sets `winsor_pct_low=0.0001` (4 decimal places past zero), `%.4f` produces `0.0001` (still informative). For `0.00001`, `%.4f` shows `0.0000` (loses precision). `%.5f` would resolve up to 5 places. Not critical.
- **Recommended fix:** Optional — `%.5f` or `%.6g`. Single character edit.

### [LOW-2] `gap_acceptable_threshold` legacy backtest float read at `Backtest/BacktestPanels.hpp:651` is `float gap_acceptable_threshold` — H4 violation (display-only? or accounting-influencing?)
- **Severity:** LOW (pre-existing, NOT introduced by `.B.2`)
- **Category:** 4 (H4 float storage)
- **Class:** Pre-existing
- **Details:** `Backtest/BacktestPanels.hpp:651` has `float gap_acceptable_threshold;` (float, not FPN<F>). Read sites at `:854` (parser via atof) + `:1666` (display) + `:1751-1752` (gap_threshold cast to double). This is a panel state (likely display + cfg-edit), NOT accounting calculation — but it's a duplicate of the main `cfg.gap_acceptable_threshold` (FPN<F>). Plan body Step 2 deletes the manual `cfg.gap_acceptable_threshold` registration but does NOT touch the panel `float` mirror. Pre-existing; not introduced.
- **Recommended fix:** Pre-existing; defer to future cleanup ship. Mark for awareness — post-`.B.2` if `gap_acceptable_threshold` flows through framework + panel `float` mirror diverges, surface as TECH_DEBT entry.
- **DESIGN_SPEC:** H4 (display-only OK)

---

### [DOC-1] Plan body line 21 says ".B.2 POPULATES the cohort — exercises the framework with 25 real rows" but Step 1 table shows 18 mechanical bit-adds + 1 (gap_acceptable_threshold) + 6 retroactive = 25 fields total (matches), but the 25-row count includes ML_CFG_FLAG bits at Step 4 — clarify
- **Severity:** DOC
- **Category:** DOC accuracy
- **Details:** Plan body uses "25 rows" in §"Why this ship exists" (line 21), "18-row" in Scope §1 header (line 159), "24+ rows" in §"DESIGN_SPECS landed/amended" (line 145), and "20+ entries" in §"Verification gate" (line 837). Reader needs to triangulate: 17 per-core + 1 global + 6 retroactive/parity-gap (Step 3) + 5 ML_CFG_FLAG bits (Step 4) = 29 total (overcounts since some retroactive overlap with per-core or ML_CFG_FLAG). Clarify the math in one canonical spot.
- **Recommended fix:** Plan body amendment v1.0 → v1.1: add explicit row-count footnote near line 21 explaining "18 per-core + 1 global (Step 1) + 6 retroactive/parity-gap (Step 3, of which some overlap into the per-core 18) + 5 ML_CFG_FLAG STAMP_BOUND_CFG_DERIVED bits (Step 4) = ~25-29 total cohort fields flagged through framework after `.B.2` ship close. Exact count locked at coding-time per FIELD_IDX enumeration order".

---

## Cross-references

### Sister findings from prior `.B` accounting-audit
- `accounting-audit-2026-05-17-v5.15.5.F.4d.1.B.md` — CRITICAL-1 (consumer migration gap, which `.B.1` STRUCTURALLY closed; framework consumer macros via `INFERENCE_CFG_POPULATE_FROM_DERIVED` walker reach all sites once cohort populated)
- Prior CRITICAL-2 (Winsor predicate rejects defaults) — already closed via plan body Decision 4 auto-pick (a)
- Prior HIGH-1 (canonical body field order changes) — addressed via Decision 1 auto-pick (a) + Step 8; CRIT-2 above clarifies the implementation
- Prior HIGH-4 (Class 27 latent surface — bandit_blend_ratio) — same surface; MED-1 above re-flags + adds verification ask
- Prior MED-1 (drift-check gate per-core flatten) — sister to HIGH-1/HIGH-2 above

### DESIGN_SPECS affected
- `wire-format-byte-preservation-discipline.md` — REQUIRES new section per HIGH-3 (first canonical bump procedure documentation)
- `metadata-bit-driven-derived-filter-framework.md` v1.3 → v1.4 — wire-byte order amendment per CRIT-6 outcome
- `cfg-derived-consumer-framework.md` — first non-empty cohort walk; lessons learned from `.B.2` ship
- `decision-time-data-binding-pattern.md` — referenced in MED-1 + HIGH-1/HIGH-2

### CI checks
- Step 9.4 (HMAC byte preservation) — strengthen per CRIT-2 (assert explicit `stamp_format_version` failure mode, not generic HMAC mismatch)
- Step 9.3 (Migration verification) — add per-core gate test per HIGH-1/HIGH-2 (set `cfg.cores[1].risk_degradation_curve=1` with global=0; verify per-core stamp behavior)

### Plan body amendments recommended (v1.0 → v1.1)
1. **CRITICAL-1:** Line 111 table — `FOREACH_CFG_DERIVED_INFERENCE_CFG` verdict from "DELETED" to "NO-CHANGE (coexists until `.B.3`)" + clarify dual-walker semantics at `.B.2`
2. **CRITICAL-2:** Step 8 lines 661-694 — specify 3 concrete deliverables (emit-site + verifier-side + test fixture); not "bump the constant"
3. **HIGH-1/HIGH-2:** Step 5 cfg-gate sidecar gate expressions — clarify per-core vs global indexing semantics; add Step 9 per-core test
4. **HIGH-3:** Step 8 deliverables list — add explicit `wire-format-byte-preservation-discipline.md` new-section writing as Step 8 sub-deliverable
5. **MED-1:** Step 3 lines 421-422 — add Class 27 prevention note for `bandit_blend_ratio` future-cohort awareness
6. **MED-2:** Step 6 line 234 — prefer FPN-native comparison `cfg.winsor_pct_low >= cfg.winsor_pct_high` over `FPN_ToDouble(...)` chain (verify operator>= exists; fall back if not)
7. **MED-3:** Step 5 line 477 — cite verification that `cfg.ml_cfg_flags` is global single-bitmap
8. **MED-4:** Step 1 line 351 — resolve `risk_min_size_pct` exact line to `:617`
9. **DOC-1:** Line 21 — row-count clarification footnote

---

## Verdict

**YELLOW.** The 2 CRITICALs and 3 HIGHs are remediable via plan body amendment (no scope expansion). The cohort migration itself is structurally sound — `.B.1` framework correctly handles cohort fields once they flag the metadata bit; `cfg_gate::lookup_populate` / `lookup_drift` switch dispatch routes cohort gates correctly; `tt::cfg_emit_field` + `tt::cfg_populate_inf_field` + `tt::cfg_drift_compare` from `.B.1` are type-trait-correct for FPN<F> via `if constexpr (is_FPN_v<T>)` — H4 / H9 / H13 / H17 all preserved at cohort migration.

Hazards exist primarily in:
1. **Plan-body accuracy gaps:** CRIT-1 ("DELETED" claim that contradicts engine state) + CRIT-2 (stamp_format_version mechanism plumbing) — fix at v1.0 → v1.1 amendment
2. **Per-core gate semantics:** HIGH-1/HIGH-2 — clarify gate expressions evaluate at the right cfg scope
3. **Procedural documentation gap:** HIGH-3 — Step 8 needs to actually WRITE the DESIGN_SPECS amendment as a deliverable (not just claim it)

No CRITICAL findings would silently miscalculate money at runtime IF the plan body is implemented as-written — they would surface at coding-time discovery (e.g., "wait, FOREACH_CFG_DERIVED_INFERENCE_CFG still exists; the plan body said deleted"). The accounting safety bar is met structurally at the framework level. The plan-body amendments are clarifications + procedural completeness, not redesign.

**Cohort migration recommended to proceed** after plan body v1.0 → v1.1 amendment incorporating CRITICAL findings 1+2 and HIGH findings 1+2+3.

---

**End of `.B.2` accounting-audit findings v1.0 — written 2026-05-17.**
