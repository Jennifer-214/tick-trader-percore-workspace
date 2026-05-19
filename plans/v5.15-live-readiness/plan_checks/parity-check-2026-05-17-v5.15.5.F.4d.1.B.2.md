# /parity-check report — v5.15.5.F.4d.1.B.2 cohort migration plan body

**Date:** 2026-05-17
**Scope:** Pre-coding plan-level audit; Layer 2 execution by Explore subagent
**Target plan:** `subplans/2026-05-17-v5.15.5.F.4d.1.B.2-cohort-migration.md` v1.0 DRAFT
**HEAD:** `725fe46` (= v5.15.5.F.4d.1.B.1 framework consolidation)
**Audit focus (per invocation):** HMAC chain byte preservation under framework walker (CRIT-6), ternary normalization for bitmap-bool emit, v5.14 stamp fixture regression, gap_acceptable_threshold migration, train-serve identity for 24+ cohort rows, PARITY-020 closure preservation
**Cross-check baseline:** post-v5.9.5b protections + v5.14.8.A.merged registry-driven emit + .B.1-shipped framework infrastructure

---

## Verdict: YELLOW

Plan body's parity reasoning is **structurally sound for the CRIT-6 byte-order issue** (option (a) `stamp_format_version` bump is the correct mechanism), BUT 5 concrete plan-level gaps need triage before coding:

- **1 CRITICAL** (struct field naming mismatch — framework consumer accesses field names not present in StampInferenceCfgInputs; would fail to compile post-cohort migration if not addressed)
- **2 HIGH** (stamp_format_version emit currently hardcoded `=1` literal at line 1747, not a constant; ml_buy_threshold + bandit_blend_ratio are ALREADY wire-bound via different registries — plan's "pre-canonical parity gap" framing is incorrect → double-emit risk)
- **1 MEDIUM** (TECH_DEBT-082 absorption decision is stale — fields already migrated at .F.4d)
- **1 DOC** (Layer 5b structural invariant tests aren't named in Step 9 plan)

NO showstopper for the architectural direction — option (a) byte-order break + framework consolidation are correct trajectories. The findings are concrete refinements to plan body wording + Step ordering, not direction changes.

---

## Stage 0 — DESIGN_SPECS preload

Loaded per skill spec:
- `wire-format-byte-preservation-discipline.md` (Layers 1-6 + Layer 5b structural invariants for derived filters; § "When wire-byte order changes" applies directly here)
- `autopopulate-pattern-for-production-caller-class.md` (STAMP_CFG_AUTOPOPULATE legacy is THE precedent the new framework replaces; PARITY-020 closure mechanism)
- `cfg-derived-consumer-framework.md` (the .B.1-shipped framework being exercised)
- `canonical-sister-extension-discipline.md` (.B.1 first canonical; .B.2 second canonical)
- `metadata-bit-driven-derived-filter-framework.md` (STAMP_BOUND_CFG_DERIVED bit 13 mechanism)
- `sidecar-override-pattern-for-registry-auto-flows.md` (CfgGateRegistry.hpp is first gate-type sidecar canonical)
- `cfg-flag-eligibility-criteria.md` (STAMP_BOUND eligibility + cohort audit triggers)
- `x-macro-registry-with-presence-dispatch.md` (presence-dispatch + Y3 source-flag dispatch shape)
- `DOCS/PARITY_ISSUES.md` — checked (PARITY-020 status, no new IDs allocated yet for .B.2 specifics)
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 14/18/21/24 (the closures plan claims)

---

## Findings by severity

### CRITICAL

#### CRIT-P1 — Framework consumer template fns access `inf.inference_cfg_<name>` but StampInferenceCfgInputs at HEAD declares `inf.<name>` (NOT `inf.inference_cfg_<name>`)

**File:line refs:**
- `MemHeaders/CfgGateRegistry.hpp:212` — `inf.inference_cfg_##name`
- `MemHeaders/CfgGateRegistry.hpp:213` — `inf.has_inference_cfg_##name`
- `MemHeaders/CfgGateRegistry.hpp:223-224` — same for global walker
- `MemHeaders/CfgGateRegistry.hpp:290` — drift check uses `handle.inference_cfg_##name` (same gap)
- `ML_Headers/ModelInference.hpp:1640-1643` — StampInferenceCfgInputs's FOREACH_STAMP_BOUND_CFG expansion: `int has_##name; type name;` → produces `int has_ridge_lambda; double ridge_lambda;` (NOT `has_inference_cfg_ridge_lambda`)
- `ML_Headers/ModelInference.hpp:1196-1199` — ModelStampResult's expansion is `uint8_t has_##name; type name;` (same scheme; `has_ridge_lambda` etc.)
- Plan Step 7.1 OLD code at line 542-547 references same — `type name;` no prefix

**Symptom:** When `.B.2` Step 1 flags 18 rows with `STAMP_BOUND_CFG_DERIVED` bit, the framework's `if constexpr` filter at `CfgGateRegistry.hpp:208` STOPS discarding those rows. The walker body becomes `tt::cfg_populate_inf_field(cfg.ridge_lambda, inf.inference_cfg_ridge_lambda, inf.has_inference_cfg_ridge_lambda, _gate)`. **`inf.inference_cfg_ridge_lambda` does NOT exist on StampInferenceCfgInputs** — only `inf.ridge_lambda` does (from the legacy FOREACH_STAMP_BOUND_CFG expansion at line 1643). Build fails at first walker site that exercises the framework with non-empty walk.

**Note on `.B.1` framework correctness:** `.B.1` shipped because the walker iterates 0 rows; if-constexpr false-branch is properly discarded from name resolution (per the template fn workaround documented in CfgGateRegistry.hpp:181-196). `.B.2` populates rows → walker becomes non-empty → name resolution kicks in → CRIT-P1 fires.

**Why this is genuinely CRITICAL vs MEDIUM:** plan body's Step 7.1 "Approach A/B/C" design note at line 575-581 PARTIALLY acknowledges this (Approach B: "let if constexpr filter at access time"; Approach C: "keep legacy FOREACH_STAMP_BOUND_CFG for struct-gen") — but it frames the choice as the struct-gen mechanism, not as a field-name decision. The actual mismatch is: cfg row names are simple (`ridge_lambda`) but the framework consumer macros' inf-side access is prefixed (`inference_cfg_ridge_lambda`). Two distinct outcomes:

1. **OUTCOME A — `.B.2` adds `inference_cfg_<name>` fields to StampInferenceCfgInputs:** struct grows by ~24 new fields with `inference_cfg_` prefix. Existing fields without prefix (e.g., `inf.ridge_lambda` from legacy FOREACH_STAMP_BOUND_CFG expansion at line 1643) co-exist → struct doubles for the migrated cohort → wire emit at line 1788 (still walking legacy) emits `ridge_lambda=X\n`; new framework emit walks master + accesses `inf.inference_cfg_ridge_lambda` → different field name but `desc.cfg_field_name = "ridge_lambda"` → wire emits the SAME key `ridge_lambda` from a DIFFERENT struct field. If the two paths run BOTH (Step 7.4 migrates :1788 to framework but Step 7.5 keeps STAMP_CFG_AUTOPOPULATE legacy populator at :156 → inf has both prefixed + unprefixed populated → emit walks framework path only) → wire output OK but struct memory wasteful.

2. **OUTCOME B — Rename to remove prefix in framework:** change `CfgGateRegistry.hpp:212` to `inf.##name` (drop `inference_cfg_` prefix). Then framework + legacy struct fields share namespace. But then the prefix in `inf.inference_cfg_bandit_blend_ratio` (already on struct via `FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG` line 296) collides with `inf.bandit_blend_ratio` if/when bandit_blend_ratio joins the cohort (Step 3's "pre-canonical parity gap"). Not actually a collision (different field names) — but it's a sign the prefix scheme is doing dual duty.

3. **OUTCOME C (PLAN'S APPROACH C):** Keep struct-gen on legacy registry → inf still has `inf.ridge_lambda` only. Framework's `inf.inference_cfg_ridge_lambda` access STILL FAILS to compile. **Approach C doesn't actually solve CRIT-P1** unless paired with framework template-fn rename to drop prefix.

**Recommended fix:** Plan body Step 7.1 must explicitly resolve the inf-side field name. Pick OUTCOME A (extend struct via new framework-driven struct-gen with prefix) OR OUTCOME B (drop prefix in framework template fns; align with legacy unprefixed name). State decision in Step 7.1 with explicit field name resolution. Approach C without further alignment is structurally incoherent.

**Auto-pick recommendation (auto_pick_future_oriented):** OUTCOME B (drop the `inference_cfg_` prefix in `CfgGateRegistry.hpp` template fn parameters). Rationale: legacy struct fields are unprefixed (lines 1196-1199, 1640-1643); the framework's prefix was a holdover from `FOREACH_CFG_DERIVED_INFERENCE_CFG` which named its rows `inference_cfg_<name>` (`StampBoundModelConstRegistry.hpp:281, 296`). That registry was deleted at `.B.1`. The prefix has no remaining purpose; align with legacy struct field names so wire bytes + struct fields share single source of truth. Plan body Step 7.1 should pre-decide this BEFORE coding starts. Cross-ref: `feedback_auto_pick_future_oriented`.

**Severity justification:** CRITICAL not HIGH because (a) silent breakage class — build fails at first non-empty walker exercise, not at parity test; (b) plan body's current design note (line 575-581) leaves the resolution implicit ("decision deferred to coding time; document chosen approach in postmortem") which violates `feedback_auto_pick_future_oriented`; (c) the prefix vs no-prefix is a SHARP trade-off (one path requires struct schema doubling; the other requires framework consumer template-fn signature edit) and the plan body conflates them as "Approach A/B/C" of a different design question.

**Cross-ref:** PARITY-020 closure depends on this resolution — if framework can't populate inf struct's fields, the canonical body emit (Step 7.4) at line 1788 still walks legacy `FOREACH_STAMP_BOUND_CFG(X)` → reads `inf->name` → emits same bytes BUT requires legacy STAMP_CFG_AUTOPOPULATE to still feed `inf->name`. Removing legacy registry at `.B.3` requires CRIT-P1 resolved first.

### HIGH

#### HIGH-P1 — `stamp_format_version` is a hardcoded `=1` literal in snprintf, NOT a named constant

**File:line refs:**
- `ML_Headers/ModelInference.hpp:1745-1748` — `if (has_stamp_ver && n > 0 && ...) { int wrote = snprintf(canonical + n, ..., "stamp_format_version=1\n"); ... }`
- `ML_Headers/ModelInference.hpp:1172-1174` — Result struct field declaration only (parser side): `int stamp_format_version;` with comment "1 = current (v5.9.0+)"

**Symptom:** Plan body Step 8 says: "Bump the constant by 1; example: `static constexpr uint32_t STAMP_FORMAT_VERSION = 7;  // was 6`". **No such constant exists.** The current code at line 1747 hardcodes the literal `"stamp_format_version=1\n"` directly in the snprintf call. There is no `STAMP_FORMAT_VERSION` constant to bump.

**Why HIGH not CRIT:** Mechanism works structurally — Step 8's intent is sound, just the implementation requires creating the constant first OR editing the literal. Plan body's bash-tool hint at line 666-668 (`grep -rn "stamp_format_version" ...`) will surface the issue but doesn't pre-resolve it. If coder unwittingly searches for `STAMP_FORMAT_VERSION` (uppercase + named-constant convention) the grep returns 0 hits.

**Recommended fix:** Plan body Step 8 should be revised to TWO sub-steps:
1. **8.0 (NEW):** Add named constant. At `ML_Headers/ModelInference.hpp` near line 1170 (next to ModelStampResult.stamp_format_version field) add:
   ```cpp
   // v5.15.5.F.4d.1.B.2 — schema version of stamp body itself.
   // Bumped at framework walker order change (.B.2 migration).
   // v5.9.0+ = 1; v5.15.5.F.4d.1.B.2+ = 2.
   static constexpr int STAMP_FORMAT_VERSION = 2;  // was 1 literal
   ```
2. **8.1:** Replace literal `"stamp_format_version=1\n"` at line 1747 with `"stamp_format_version=%d\n", STAMP_FORMAT_VERSION` (and update snprintf arg list).
3. **8.2:** Update parser-side documentation comment at line 1174 (`1 = current` → `2 = current; 1 = pre-.B.2`).

**Cross-ref to wire-format-byte-preservation-discipline.md § "Schema versioning every change":** the doc says "Reserve version bumps for BREAKING changes" — framework walker order change IS a breaking change for legacy v5.14 stamps. Plan auto-pick (a) is correct mechanism choice.

#### HIGH-P2 — `ml_buy_threshold` and `bandit_blend_ratio` are already wire-bound through DIFFERENT registries; plan's "pre-canonical parity gap" framing risks double-emit

**File:line refs:**
- `ML_Headers/StampBoundCfgRegistry.hpp:157-158` — `X(ml_buy_threshold, double, "%.17g", 0.0, FPN_ToDouble(cfg.ml_buy_threshold), 1, DIRECT_FIELD)` — ALREADY in legacy `FOREACH_STAMP_BOUND_CFG` with `emit_when=1` (always emit)
- `ML_Headers/StampBoundModelConstRegistry.hpp:296-297` — `X(inference_cfg_bandit_blend_ratio, _, INCLUDE, double, "%g", 0.0, inf->bandit_blend_ratio, inf->has_bandit, ...)` — ALREADY in `FOREACH_STAMP_BOUND_MODEL_CONST` as `inference_cfg_bandit_blend_ratio`
- `CoreFrameworks/CfgFieldRegistry.hpp:524` — `ml_buy_threshold` source row (NO STAMP_BOUND bit at HEAD)
- `CoreFrameworks/CfgFieldRegistry.hpp:528` — `bandit_blend_ratio` source row (NO STAMP_BOUND bit at HEAD)
- Plan Step 3 line 416-421 — proposes "APPEND `| CfgFieldDescriptor::STAMP_BOUND | CfgFieldDescriptor::STAMP_BOUND_CFG_DERIVED`" to both rows

**Symptom:** Adding `STAMP_BOUND_CFG_DERIVED` to `ml_buy_threshold` source row at line 524 → framework walker at Step 7 picks up the row → emits `ml_buy_threshold=X\n` via `tt::cfg_emit_field(cfg.ml_buy_threshold, desc, ...)`. But the LEGACY walker at `ModelInference.hpp:1788` ALSO continues walking `FOREACH_STAMP_BOUND_CFG` which contains ml_buy_threshold at line 157 → ALSO emits `ml_buy_threshold=X\n`. **Wire bytes: line duplicated.** HMAC chain breaks differently from intended CRIT-6 reordering — instead it becomes a duplicate-emit bug.

`bandit_blend_ratio` is more subtle: the legacy entry at `StampBoundModelConstRegistry.hpp:296` emits with wire key `inference_cfg_bandit_blend_ratio` (PREFIX!) from `inf->bandit_blend_ratio` field. The plan's new master-registry placement would emit with wire key `bandit_blend_ratio` (NO PREFIX, via `desc.cfg_field_name`). **Two DIFFERENT wire keys emitted for the SAME cfg value** → emitter writes both lines → parser reads both → drift detection compares against… which one? Plan Step 3 line 422 says "DELETE manual POST_CFG entry at StampBoundModelConstRegistry.hpp:295 per audit CRIT-1 / HIGH-A" — yes that's correct, but plan doesn't articulate WHY (the wire-key mismatch).

**Recommended fix:** Plan body Step 3 must explicitly state:
1. For `ml_buy_threshold`: this is NOT a "pre-canonical parity gap" — it's already STAMP_BOUND via the legacy registry path. The migration is a TRANSFER from legacy registry → master registry + `STAMP_BOUND_CFG_DERIVED` bit. Required deletions: (a) MASTER ADD `| STAMP_BOUND | STAMP_BOUND_CFG_DERIVED`; (b) LEGACY DELETE `StampBoundCfgRegistry.hpp:157-158` (the row); (c) ALSO needed: StampInferenceCfgInputs's `int has_ml_buy_threshold; double ml_buy_threshold;` field auto-removed when legacy registry expansion shrinks at line 1643 (FOREACH_STAMP_BOUND_CFG walks fewer rows → struct gen has fewer fields). The 2 deletions must happen TOGETHER in same coding-time edit or wire bytes duplicate.

2. For `bandit_blend_ratio`: the legacy wire key was `inference_cfg_bandit_blend_ratio` (prefixed); migration to master produces wire key `bandit_blend_ratio` (unprefixed). **This is a wire-format BREAKING change INDEPENDENT of CRIT-6 order change.** Both should be folded into the same `stamp_format_version` bump rationale — but Step 8's framing should acknowledge that the byte-level changes include: (a) field order shifts per master-registry declaration order, AND (b) wire key for bandit_blend_ratio renames from `inference_cfg_bandit_blend_ratio` to `bandit_blend_ratio`. Two distinct breaking changes wrapped in same version bump.

**Cross-ref:** Plan line 422 hints at the StampBoundModelConstRegistry.hpp:295 deletion but doesn't connect it to the wire-key mismatch. Plan should explicitly note both renamings in Step 8 wire-format-discipline DESIGN_SPEC amendment.

**Severity justification HIGH not MEDIUM:** silent duplicate emit + key rename produces operator-confusing stamp body. Could be caught by Step 9.4 byte-preservation test against the LOCKED hash, but only POST-coding (test fails after the migration lands). Pre-coding identification gives the coder the right ordering to avoid the duplicate-emit window.

#### HIGH-P3 — Layer 5b structural invariant tests not named in Step 9 plan; replaces snapshot-as-lock per `.A` REVISED Option F

**File:line refs:**
- `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` Layer 5b (lines 195-274) — REVISED Option F replaces LOCKED-hash-constant snapshot with structural invariants (I1-I5) per `feedback_principle_beats_registry_for_eliminating` 2026-05-15
- Plan Step 9.4 line 736 — "Compute canonical body hash; lock as `LOCKED_STAMP_BOUND_CFG_DERIVED_HASH_V5_15_5_F4D_1_B_2`"
- Plan Step 9.6 line 745-748 — walker integration tests "verify framework consumer macros populate same inf/result struct fields as legacy walker would have populated"

**Symptom:** Plan body Step 9.4 names a LOCKED hash mechanism. This was the v1.0 draft of Layer 5b that Caramel rejected at `.A` planning (per `.A` postmortem + DESIGN_SPECS doc revision at lines 195-274). The canonical mechanism (post-Option-F) is **structural invariant tests** (I1-I5: line count == flagged-row count; line pattern `<name>=<value>\n`; no comma decimals from locale leak; per-row name appears EXACTLY when bit set; per-core descriptors emit before global descriptors). The plan body re-introduces the LOCKED const pattern.

**Recommended fix:** Plan Step 9.4 should be revised to invoke the Layer 5b structural invariant runner (per spec line 220-227):
```cpp
// In controller_test.cpp:
SECTION("STAMP_BOUND_CFG_DERIVED generic invariants PASS (.B.2 non-empty cohort)");
STAMP_BOUND_CFG_DERIVED_run_generic_invariants();
// I1: flagged-row count matches line count
// I2: per-line format <name>=<value>\n
// I3: no comma decimal (locale-pin Layer 2 verification)
// I4: per-row name appears exactly when bit set
// I5: per-core descriptors emit before global descriptors
```

The framework auto-generates `STAMP_BOUND_CFG_DERIVED_run_generic_invariants()` per spec line 204; .B.2 just needs to invoke it. Domain-specific invariants (bitmap-bool ternary normalization for HMAC byte-equivalence) live in the consumer header per spec line 214.

Step 9.4's CURRENT v5.14 fixture mismatch test IS still valid as a CRIT-6 verification — but should be expressed as: "load v5.14 fixture; expect parse to read `stamp_format_version=1`; verify caller correctly identifies as legacy version (NOT trigger spurious HMAC mismatch error)." The framing in plan body is correct here — just the LOCKED hash mechanism in 9.4 needs replacing.

**Severity HIGH:** plan would ship a Class 18 mirror at the hash-constant layer that `.A` planning explicitly closed. Cross-ref: Caramel's "magic number" pushback at `.A` planning per `feedback_principle_beats_registry_for_eliminating`.

### MEDIUM

#### MED-P1 — TECH_DEBT-082 absorption framing is stale; 3 fields already migrated at `.F.4d`

**File:line refs:**
- Plan Step 1 line 364-370 — "Decision at Step 1 boundary: TECH_DEBT-082 absorption (3 `.F.5` residual fields — `confidence_ic_floor` + `lazy_rebuild_price_threshold_pct` + `exit_threshold`). ... **Auto-pick: ABSORB into `.B.2` Step 1**"
- Plan Scope NOT IN scope row line 302 — "TECH_DEBT-082 (3 `.F.5` residual fields — `confidence_ic_floor` / `lazy_rebuild_price_threshold_pct` / `exit_threshold`) | `.F.4f` Phase 7 OR `.B.2` Step 1 absorption (decide at coding time)"
- Engine commit `fd9ad8e` (predecessor `.F.4d`) — "TECH_DEBT-082 close — 3 `.F.5` residual fields migrate to FOREACH_PER_CORE_CFG_FIELD"
- `CoreFrameworks/CfgFieldRegistry.hpp:539` — `confidence_ic_floor_window` (already registered; NOTE this is `_window` variant)
- `CoreFrameworks/CfgFieldRegistry.hpp:641` — `lazy_rebuild_price_threshold_pct` (already registered with `.F.4d TECH_DEBT-082 close` comment)
- `CoreFrameworks/CfgFieldRegistry.hpp:644` — `exit_threshold` (already registered with `.F.4d TECH_DEBT-082 close` comment)
- `CoreFrameworks/CfgFieldRegistry.hpp:647` — `confidence_ic_floor` (already registered with `.F.4d TECH_DEBT-082 close` comment)

**Symptom:** Plan body proposes "ABSORB" of TECH_DEBT-082 = "add 3 more rows to FOREACH_PER_CORE_CFG_FIELD (or FOREACH_GLOBAL_CFG_FIELD)" + "Closes TECH_DEBT-082 at `.B.2` instead of `.F.4f` cleanup ship." **The 3 fields are ALREADY in FOREACH_PER_CORE_CFG_FIELD at HEAD** — confidence_ic_floor + lazy_rebuild_price_threshold_pct + exit_threshold are at lines 647, 641, 644 respectively. Plan's "absorption" auto-pick is referring to closed work.

**Possible plan intent:** maybe `.B.2` plan refers to FLAGGING these 3 fields with `STAMP_BOUND_CFG_DERIVED` bit (not adding them as new rows). Both `confidence_ic_floor` (line 647: clamp `DBL(0.02, -1.0, 1.0)`, used for drift gate) and `exit_threshold` (line 644: used by ML/Exit Path 3 — STAMP_BOUND-eligible by recurring-bug class). `lazy_rebuild_price_threshold_pct` is performance/slow-path config (line 641: NOT stamp-bound eligible per cfg-flag-eligibility-criteria.md — runtime tuning param).

**Recommended fix:** Plan Step 1 line 364-370 + Scope row line 302 should be REWORDED. Either:
1. **Delete the TECH_DEBT-082 absorption framing entirely** (it's not actually a decision; the fields are migrated; TECH_DEBT-082 status update should already reflect CLOSED) → revise CLAUDE.local.md sprint state row for the close.
2. **Reframe as STAMP_BOUND_CFG_DERIVED-bit-add decision for confidence_ic_floor + exit_threshold** (the 2 stamp-bound-eligible of the 3). lazy_rebuild_price_threshold_pct = NOT stamp-bound. Adds 2 rows to the 18-row mechanical cohort bit-add → 20 rows total. This is the actual semantic decision the plan should be making.

**Severity MEDIUM:** doesn't break the ship structurally, but plan reads stale. Operator triage at coding time will likely catch this when grep'ing for the fields — but pre-coding correction saves the question.

### DOC

#### DOC-P1 — Step 9.4 references `tests/wire_format_invariants.hpp` helper from `.A` but doesn't elaborate the I1-I5 invariant set

**File:line refs:**
- `tests/wire_format_invariants.hpp` (exists at HEAD per .A ship)
- Plan Step 9.4 line 735 — "Synthesize v5.15.5.F.4d.1.B.2 stamp via wire_format_invariants.hpp helper"
- Plan Step 9.6 line 744-748 — "14 walker integration tests at `controller_test.cpp:~26140` expand from vacuous PASS to substantive"

**Symptom:** Plan refers to the helper by file name but doesn't enumerate which I1-I5 invariants need to be substantive (vs vacuous PASS at .B.1's 0-row walker). At .B.2 the cohort populates → I1 (flagged-row count == line count) goes from 0==0 to 24+==24+ substantive verification; I4 (per-row name appears EXACTLY when bit set) goes from "no flagged rows; no names expected" to "24 names expected, each present once". Plan body should explicitly state which 14 → ~25-30 (per Step 9 line 708) sections cover which invariants.

**Recommended fix:** Plan Step 9.6 should enumerate by invariant:
- I1 substantive: 1 SECTION ("line count = STAMP_BOUND_CFG_DERIVED flagged row count in cfg field registry + ML_CFG_FLAG bitmap")
- I2 substantive: 1 SECTION (regex match per line)
- I3 substantive: 1 SECTION (no comma in any line — locale verification)
- I4 substantive: 1 SECTION per cohort group (Bandit/Thompson, Ridge, Composite confidence, Soft-risk, BLENDED, Per-horizon-barrier, always-emit) → 7 SECTIONS
- I5 substantive: 1 SECTION (per-core source rows emit before global rows by walker order)

Total: 11 invariant SECTIONS as a structural floor, on top of cohort-specific gate behavior tests (~12 from 9.1 + always-emit tests from 9.2 + 5 from 9.3 = ~25 cohort-specific). Step 9 totals reconcile with plan's "~25-30 NEW tests".

**Severity DOC:** organizational refinement; doesn't change ship behavior. Useful for coder at Step 9 to have explicit count discipline.

---

## Cross-cutting concerns

### CC-1 — CRIT-6 wire-byte order change combines THREE distinct byte changes, not ONE

The plan body Decision 1 frames CRIT-6 as a single "byte order change". In reality, `.B.2` introduces three concurrent wire-format changes that all need version bump rationale:

1. **Field ORDER changes** (master registry declaration order ≠ legacy registry hand-crafted order)
2. **Field NAME changes** (`inference_cfg_bandit_blend_ratio` → `bandit_blend_ratio` per HIGH-P2)
3. **Field PRESENCE changes** (potentially: `gap_acceptable_threshold` already in legacy registry at line 159 → migrated to master as STAMP_BOUND_CFG_DERIVED with different gate semantics; verify gate change preserves emit when)

Each is independently a wire-format breaking change. Combined, they justify a single `stamp_format_version` bump but the DESIGN_SPEC amendment at Step 8 should enumerate all three so future contributors understand `.B.2`'s scope when they read `wire-format-byte-preservation-discipline.md` § "Framework refactor wire-format changes".

### CC-2 — gap_acceptable_threshold migration: legacy registry row at StampBoundCfgRegistry.hpp:159 must be DELETED in same edit as Step 2 master-registry ADD

**File:line refs:**
- `ML_Headers/StampBoundCfgRegistry.hpp:159` — `X(gap_acceptable_threshold, double, "%.17g", 0.0, FPN_ToDouble(cfg.gap_acceptable_threshold), 1, DIRECT_FIELD)` — already STAMP_BOUND via legacy registry
- `ML_Headers/CoreModelZoo.hpp:796` — stamp PARSER side reads `gap_acceptable_threshold` key (reads from stamp file, not cfg; preserved)
- Plan Step 2 line 173-179 — DELETE manual decl + default + parser + GUI; ADD source row. **Does NOT mention DELETE legacy registry row at line 159.**

**Symptom:** Same duplicate-emit class as HIGH-P2: master registry adds `gap_acceptable_threshold` with `STAMP_BOUND_CFG_DERIVED` → framework walker emits at Step 7 (post-migration) → legacy walker at `ModelInference.hpp:1788` still walks `FOREACH_STAMP_BOUND_CFG` which contains line 159 → emits same key SAME bytes → wire body duplicates the line. (Actually byte-identical so HMAC would still chain — but the canonical body has a duplicate field, parser reads the SECOND value, drift detection compares against the SECOND, etc. Class 18-style mirror with hidden second source.)

**Recommended fix:** Plan Step 2 must include "DELETE row at `ML_Headers/StampBoundCfgRegistry.hpp:159`" alongside the 4 manual-site deletions already listed. Pre-coding identification gives the coder the right ordering. Cross-ref: same shape as HIGH-P2's ml_buy_threshold migration but for `gap_acceptable_threshold`.

### CC-3 — Framework gate semantics MISMATCH for migrated rows: legacy emit_when vs new sidecar gate

For each cohort row, the legacy `emit_when` expression at FOREACH_STAMP_BOUND_CFG must be encoded in the new FOREACH_CFG_GATE_PER_CORE sparse sidecar as a 2-tuple. Plan body Step 5 line 478-506 lists ~20 entries; spot-check vs legacy:

- Ridge cohort legacy emit_when (`StampBoundCfgRegistry.hpp:112-117`): `BITMAP_ANY(cfg.ml_cfg_flags, MASK_ML_CFG_RIDGE_WITHIN_HORIZON | MASK_ML_CFG_RIDGE_ACROSS_HORIZONS)` ← plan Step 5 line 493: same. **OK.**
- Composite confidence cohort legacy emit_when (`:125, :127, :129, :131, :133`): `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_CONFIDENCE_COMPOSITE_ENABLED)` ← plan Step 5 line 488: same. **OK.**
- Thompson cohort legacy emit_when (`:164, :166, :168, :170`): `cfg.bandit_algorithm != 0` ← plan Step 5 line 481-484: `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)`. **MISMATCH.**
- Soft-risk cohort legacy emit_when (`:149, :151, :153, :155`): `cfg.risk_degradation_curve != 0` ← plan Step 5 line 497-500: same. **OK.**
- Winsor cohort legacy emit_when (`:138, :141`): complex predicate `(FPN_ToDouble(cfg.winsor_pct_low) > 0.0 && FPN_ToDouble(cfg.winsor_pct_high) < 1.0 && FPN_ToDouble(cfg.winsor_pct_low) < FPN_ToDouble(cfg.winsor_pct_high))` ← plan Step 5 line 222 ("Winsor cohort: NO entries (default always-emit; cfg parse-time validation enforces bounds per Decision 4)"). **SEMANTICS CHANGE — legacy emit_when blocked emit if winsor range invalid; new always-emit policy replaces with parse-time WARN + reset to defaults.**

**Thompson cohort mismatch** is more subtle:
- Legacy: emit when bandit_algorithm != 0 (any non-EXP3 algorithm)
- New plan: emit when MASK_ML_CFG_BANDIT_ENABLED is set in ml_cfg_flags bitmap

These are different — `bandit_algorithm != 0` is the algorithm selection (THOMPSON / EXP3_OP_THOMPSON_GHOST / etc.); `MASK_ML_CFG_BANDIT_ENABLED` is the master enable flag. A cfg with `bandit_algorithm=1 bandit_enabled=0` would emit under legacy but NOT under new framework → wire bytes differ.

**Recommended fix:** Plan Step 5 must explicitly justify (or correct) the Thompson gate change. Either:
1. Use `cfg.bandit_algorithm != 0` (preserve legacy semantics)
2. Use `BITMAP_IS_SET(cfg.ml_cfg_flags, MASK_ML_CFG_BANDIT_ENABLED)` (intentional semantics change as part of `.B.2`)

Either is defensible but plan should pick one with rationale. Same applies to **Winsor cohort** — always-emit vs legacy gate change is acknowledged in Decision 4 but the wire-format impact (legacy stamps without winsor lines vs new stamps with winsor lines for invalid ranges) needs the same DESIGN_SPEC amendment treatment as CRIT-6.

**Severity:** This is part of CRIT-6 acceptance. Plan auto-pick (a) `stamp_format_version` bump covers it (any semantic change is signaled). But for clean migration, plan should pre-articulate gate semantics changes explicitly.

---

## Behavior matrix (verify train and serve agree for default cfg)

| Scenario | Trainer view (post-`.B.2`) | Engine view (post-`.B.2`) | Identical? |
|---|---|---|---|
| Default cfg → emit canonical body | Master-walker order, `stamp_format_version=2`, gap_acceptable_threshold line emitted once | Same (framework walker single source) | YES (CRIT-6 (a) accepted) |
| Default cfg → parse v5.14 stamp | Sees `stamp_format_version=1` → identifies legacy | Same | YES (Surface G has_*=0 for unknown keys) |
| bandit_algorithm=1 (Thompson) → emit | Plan: emit Thompson rows IF MASK_ML_CFG_BANDIT_ENABLED set | Legacy: emit Thompson rows IF cfg.bandit_algorithm != 0 | **MISMATCH** (CC-3) |
| Winsor cfg with valid range (0.005 / 0.995) → emit | Always emit (per plan Step 5 line 222) | Legacy: emit only if range valid | **MISMATCH** (gate semantics change; signaled by version bump) |
| ml_buy_threshold default = 0.5 → emit | Master walker emits ml_buy_threshold=0.5 | Legacy walker ALSO emits ml_buy_threshold=0.5 (line 157-158) | **DUPLICATE** until legacy row deleted (HIGH-P2) |
| bandit_blend_ratio default = 0.5 → emit | Master walker emits bandit_blend_ratio=0.5 | Legacy emits inference_cfg_bandit_blend_ratio=0.5 (line 296) | **KEY MISMATCH** → 2 different wire keys until legacy deleted (HIGH-P2) |
| gap_acceptable_threshold default = 0.05 → emit | Master walker emits gap_acceptable_threshold=0.05 | Legacy ALSO emits gap_acceptable_threshold=0.05 (line 159) | **DUPLICATE** until legacy row deleted (CC-2) |
| Drift check: stamp's ridge_lambda vs runtime cfg | Framework walks master + accesses handle.inference_cfg_ridge_lambda | Legacy walked FOREACH_STAMP_BOUND_CFG + accessed r.ridge_lambda | **NAMING MISMATCH** (CRIT-P1) |

Items in bold flag plan-body gaps where parity will silently or visibly break unless the recommendations above are accepted.

---

## Suggested plan body amendments (v1.0 → v1.1)

1. **CRIT-P1 close:** Step 7.1 pre-decides struct field name resolution (OUTCOME B recommended: drop `inference_cfg_` prefix in framework template fns). Edit `CfgGateRegistry.hpp:212-213, 223-224, 290` accordingly. Plan body documents decision + rationale.
2. **HIGH-P1 close:** Step 8 grows to 8.0/8.1/8.2 sub-steps — create `STAMP_FORMAT_VERSION` named constant before bumping it. Add fix sub-step to plan body.
3. **HIGH-P2 close:** Step 3 reframed — `ml_buy_threshold` + `bandit_blend_ratio` are MIGRATIONS (delete legacy entries simultaneously), not "pre-canonical parity gaps". Explicit deletion sites: `StampBoundCfgRegistry.hpp:157-158`, `StampBoundModelConstRegistry.hpp:296-297`. Document the wire-key rename for bandit_blend_ratio.
4. **HIGH-P3 close:** Step 9.4 replaces LOCKED hash mechanism with `STAMP_BOUND_CFG_DERIVED_run_generic_invariants()` invariant runner (I1-I5). Per `.A` REVISED Option F.
5. **MED-P1 close:** Step 1 line 364-370 + Scope row line 302 reworded — TECH_DEBT-082 already closed at `.F.4d`; reframe as STAMP_BOUND_CFG_DERIVED bit-add decision for `confidence_ic_floor` + `exit_threshold` (2 fields, not 3). Update CLAUDE.local.md sprint state if needed.
6. **CC-1 + CC-2 + CC-3:** Step 8's DESIGN_SPEC amendment captures all THREE breaking-change axes (order + name + presence/gate semantics). Step 2 explicitly DELETES `StampBoundCfgRegistry.hpp:159` (gap_acceptable_threshold). Step 5 picks Thompson cohort gate semantics + Winsor cohort always-emit with documented rationale.

---

## NOT a bug (verified-safe items)

1. **PARITY-020 closure preservation:** plan correctly identifies STAMP_CFG_POPULATE_FROM_DERIVED as the closure mechanism. Per `autopopulate-pattern-for-production-caller-class.md`, the framework consumer macros are the canonical 3rd application of the pattern (after STAMP_CFG_AUTOPOPULATE + STAMP_MODEL_CONST_AUTOPOPULATE). PARITY-020 protection is structurally preserved.
2. **Locale pinning (Layer 2):** `tt::cfg_emit_field` at `CfgFieldDispatch.hpp:332-334, 357-360` already pins LC_NUMERIC=C per-thread via `newlocale`/`uselocale`. Sister to legacy emit's pinning at ModelInference.hpp (which uses `setlocale` historically — verify Step 7.4 migration preserves this). At new framework path: each `tt::cfg_emit_field` call pins independently. Per-call overhead is slow-path/stamp-emit cadence — acceptable.
3. **`tt::cfg_emit_field` ternary normalization (per heterogeneous-registry-pattern.md Y3):** confirmed at `CfgFieldDispatch.hpp:346-347` — KIND_BOOL dispatch via `(src != 0) ? 1 : 0` ternary. Legacy registry's BITMAP_BIT emit_source rows (ridge_within_horizon, ridge_across_horizons, confidence_composite_enabled, exit_blender_mode at StampBoundCfgRegistry.hpp:106-108, 109-111, 123-125, 144-146) all use `(BITMAP_IS_SET(...) ? 1 : 0)` ternary. **Wire-byte identity preserved for boolean emit** — both paths normalize to {0, 1}. The 4 BITMAP_BIT rows are now in `FOREACH_ML_CFG_FLAG` (per Step 4 5→6 sig migration) — framework walker handles via separate walk (no direct master registry row); ensure Step 7 walker uses `FOREACH_ML_CFG_FLAG` iteration with same ternary norm.
4. **Hot path UNTOUCHED:** plan Verification Gate line 845 + Step 10 line 761 correctly assert. Cohort migration is slow-path/parse/stamp-emit only; `tools/calls_graph_diff.sh` will catch regression. No hot-path change is in scope.
5. **CRIT-6 option (a) auto-pick correctness:** sound per `wire-format-byte-preservation-discipline.md` § "Schema versioning every change". Plan body's Decision 1 reasoning is correct; the gap is HIGH-P1 (constant doesn't exist) + DOC alignment.
6. **`/anti-spaghetti` clean run sister at `.B.1`:** plan Step 4 line 472 verifies `static_assert(ML_CFG_COUNT <= 16)` preserved. 12 rows × 6-arg sig is mechanically clean migration.

---

## Cross-ref: existing PARITY_ISSUES.md entries

No new PARITY-NNN IDs allocated for this audit (findings are pre-coding plan-body gaps, not in-code regressions). Verify operator review:
- **PARITY-020 (HISTORICAL CLOSED):** STAMP_CFG_AUTOPOPULATE closure of cfg-bound field population gap. Plan preserves closure mechanism via STAMP_CFG_POPULATE_FROM_DERIVED. CRIT-P1 resolution determines whether closure stays intact post-`.B.2`.
- **PARITY-022 (HISTORICAL QUARANTINED):** STAMP_MODEL_CONST_AUTOPOPULATE; plan does not touch this surface.

If any of CRIT-P1 / HIGH-P1 / HIGH-P2 / HIGH-P3 / CC-2 / CC-3 close fails post-coding, allocate new PARITY-NNN IDs at ship close per CLAUDE.local.md auto-write contract.

---

## Suggested ship sequence

Plan body's Steps 0-10 are correctly ordered. Suggested amendments retain same ordering with these inline edits:

- **Step 0:** unchanged
- **Step 1:** reframe TECH_DEBT-082 decision per MED-P1
- **Step 2:** add explicit `StampBoundCfgRegistry.hpp:159` DELETE per CC-2
- **Step 3:** reframe as MIGRATIONS per HIGH-P2; add `StampBoundCfgRegistry.hpp:157-158` + `StampBoundModelConstRegistry.hpp:296-297` explicit DELETEs
- **Step 4:** unchanged (5→6 sig migration well-specified)
- **Step 5:** pick Thompson gate semantics + Winsor always-emit rationale per CC-3
- **Step 6:** unchanged (Winsor parse-time validation is correctly scoped)
- **Step 7:** Step 7.1 pre-decides field-name resolution per CRIT-P1 (recommend OUTCOME B); other 7.X unchanged
- **Step 8:** create constant first (8.0), then bump (8.1), update docs (8.2); DESIGN_SPEC amendment lists 3 axes per CC-1
- **Step 9:** Step 9.4 invariant runner per HIGH-P3; Step 9.6 expanded per DOC-P1
- **Step 10:** unchanged

Effort estimate impact: amendments add ~30-60 min planning revision time + ~0 LOC at coding time (amendments are reorderings + explicit deletions that would have been required anyway). Net ship effort unchanged.

---

## /parity-check verdict

**YELLOW** — plan body's architectural trajectory is correct (cohort migration via framework consumer macros; `stamp_format_version` version-bump mechanism for byte-order change; structural-invariant tests via Layer 5b Option F). 5 specific gaps require plan amendment before coding starts:

- 1 CRITICAL — struct field naming mismatch
- 2 HIGH — stamp_format_version literal vs constant; ml_buy_threshold + bandit_blend_ratio dual-registry duplicate-emit risk
- 1 HIGH — Layer 5b invariant mechanism naming
- 1 MEDIUM — TECH_DEBT-082 stale framing
- 1 DOC — Step 9.4 invariant enumeration

Plan body promotion DRAFT v1.0 → v1.1 should incorporate the 5 amendments per § "Suggested plan body amendments" above before proceeding to Step 0 coding. Pre-coding audit synthesis (Batch 1) should triage these with Caramel per `feedback_consult_on_audit_findings`.

After v1.1 amendments, /parity-check expects to re-verify GREEN at coding-time spot check (~5-10 min focused re-run on the specific changed sections).

---

**Auto-write:** No new PARITY-NNN entries to `DOCS/PARITY_ISSUES.md` (findings are plan-body gaps, not code regressions). Operator review at audit synthesis stage; PARITY-NNN allocation at ship close if any gap persists into coded state.

**Report saved to:** `plans/v5.15-live-readiness/plan_checks/parity-check-2026-05-17-v5.15.5.F.4d.1.B.2.md` per skill spec.

**End of report.**
