# /readiness report — v5.15.5.F.4c — 2026-05-14

**Audited plan:** `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4c-int-int_enum-bool-migration.md`
**Predecessor:** `.F.4b` SHIPPED 2026-05-14 (engine `160da10`, tag `v5.15.5.F.4b`)
**Engine HEAD:** `160da10` = `v5.15.5.F.4b`; Version.hpp = `5.15.5.F.4b`; 3118 tests pass; working tree clean except `claude_session.md` untracked
**Workspace HEAD:** `bae0894`
**Operator:** Caramel
**Predecessor synthesis read:** `plans/plan_checks/2026-05-14-v5.15.5.F.4b-fresh-audits-synthesis.md` + `plans/plan_checks/readiness-recheck-2026-05-14-v5.15.5.F.4b-amended.md` (lessons-learned)
**Stage 0 DESIGN_SPECS preloaded:** type-trait-dispatch-via-tt-namespace, universal-cfg-field-registry-pattern, categorical-tag-applicability-pattern, registry-tuple-as-single-source-of-truth, bitmap-overflow-protection-discipline, wire-format-byte-preservation-discipline, autopopulate-pattern-for-production-caller-class, structural-fix-preferred-decision-framework, multi-bit-state-encoding-pattern

---

## Executive verdict: YELLOW (5-10 min fix-up to GREEN)

**Cold-pickup completeness: 8/10 with amendment-block scaffolding.** Plan was drafted PRE-.F.4b and carries known stale code samples (Class 23 anti-shape). The plan body's lines 15-66 amendment notice **invalidates Steps 1, 4, 5 code samples explicitly** and points at canonical shipped infrastructure. Scope intent (which fields migrate, which tests, which sub-ship boundary, which TECH_DEBT entries close) is preserved + valid.

**Key gap:** plan body retains stale code samples in-line; amendment notice fixes intent but does not rewrite Steps 1/4/5. A fresh-context coder must rely on `.F.4b` shipped code (`CfgFieldDispatch.hpp` + `CfgFieldRegistry.hpp` + canonical test `test_v5_15_5_F4b_cfg_field_dispatch`) as the authority, exactly as amendment notice instructs.

**Blocking gaps (must address before coding):**
1. **STAMP_BOUND derived filter** (FOREACH_STAMP_BOUND_CFG_DERIVED) has no concrete implementation spec — plan calls it out in scope but Step section is missing.
2. **Layer 5b CI hash test** carried over from `.F.4b` HIGH-3 has no procedural spec in plan body (where stored / fixture / hash compute site).
3. **Test count baseline** baseline says ≥1822 (Step 7 line 357); should say ≥3118 + new tests (amendment notice clarifies but Step 7 verification list still says 1822).

**Non-blocking but high-value fix-ups** detailed below.

---

## 28+3-check verdict table

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | ✅ PASS | Boot + GUI only; verified Step 6 includes paper-trade gate |
| 2 | Train-serve parity | ⚠ YELLOW | STAMP_BOUND derived filter cutover is in scope (.F.4c closes TECH_DEBT-006 dual registry) but plan lacks concrete spec for how `FOREACH_STAMP_BOUND_CFG_DERIVED(X)` is generated (preprocessor filter? runtime walk over `g_cfg_field_descriptors[]` with `metadata_flags & STAMP_BOUND` mask?). Spec gap. |
| 3 | Surface area | ✅ PASS | Touches ~3 files (registry, dispatch, parser); LOC under 8-file threshold |
| 4 | Pointer init / heap lifecycle | ✅ PASS | All registry-driven; no heap allocation |
| 5 | Backward compat | ✅ PASS | No version bumps; registry rows are additive |
| 6 | Multi-threading | ✅ PASS | Boot-time parser only; per-thread locale pin already in `.F.4b` save path |
| 7 | Test coverage | ⚠ YELLOW | Step 6 lists 3 new tests (INT roundtrip, INT_ENUM clamp, BOOL normalization); SHOULD cite mirror of `test_v5_15_5_F4b_cfg_field_dispatch` at `tests/controller_test.cpp:1548` (canonical shape) per amendment notice |
| 8 | Docs + invariants | ⚠ YELLOW | Step 7 doesn't list `DOCS/CHANGELOG.md` update (same gap as predecessor MED-8); no FEATURE_LOOKUP.md entry mentioned for "STAMP_BOUND derived filter closes dual registry"; no TECH_DEBT-009/-006 explicit closure note |
| 9 | Forward maintenance | ✅ PASS | Pure additive — 1 row per field |
| 10 | Rollback story | ✅ PASS | `pre-v5.15.5.F.4c` tag at Step 0; reset --hard documented Step 7 fail-mode |
| 11 | Architectural sprint | N/A | Mechanical migration; no architecture change |
| 12 | Display ↔ execution invariant | N/A | No Position fields touched |
| 13 | Strategy lifecycle | N/A | No strategy changes |
| 14 | X-macro / dispatch | ✅ PASS | Per `.F.4b` shipped `EMIT_CFG_PARSER_CASE` X-macro at `ControllerConfig.hpp:1896-1904`; mechanical row additions |
| 15 | ML feature parity regression | N/A | No FeatureRegistry touch |
| 16 | New cfg field with stamp-bearing | ⚠ YELLOW | STAMP_BOUND metadata flag (`CfgFieldRegistry.hpp:66`) exists; plan lacks per-field stamp-bound annotation strategy for the 11 int-typed migration candidates currently in `FOREACH_STAMP_BOUND_CFG` (Ridge ints, exit_blender_mode, risk_degradation_curve, bandit_algorithm, ridge_within_horizon, ridge_across_horizons, confidence_composite_enabled, trading_mode). When these migrate to `FOREACH_CFG_FIELD`, the STAMP_BOUND metadata flag must be set on each row OR derived filter must point back to the old registry path. **Concrete migration sequencing absent.** |
| 17 | Model-load path strict-mode | N/A | No model load changes |
| 18 | Reuse audit | ✅ PASS | Plan correctly reuses `tt::cfg_parse_field<T>` (shipped); integer dispatch via `is_integral_v` / `is_unsigned_v` already covered at `CfgFieldDispatch.hpp:79-88` per amendment notice |
| 19 | Pre-existing-work audit | ⚠ false-NEW caught | Amendment notice correctly flags: tt:: integer specializations are ALREADY SHIPPED. Plan body Step 1 false-NEW. Fresh coder must rely on amendment notice. |
| 20 | Future-proofness | ✅ PASS | Registry-driven; pattern locked at `.F.4b`. KIND_INT_ENUM range-clamp refinement at most ~5 LOC (per amendment notice + .F.4b deferred clamp on invalid → default) |
| 21 | Test count assertion fragility | ⚠ YELLOW | Step 7 line 357 says "≥1822 + new"; ACTUAL baseline is 3118 (verified 2026-05-14 via `./build/controller_test`). Mechanical citation drift. Update to `≥3118 + new`. |
| 22 | Auto-trigger downstream re-audit | ✅ PASS-with-caveat | Plan amendment notice IS the .F.4b auto-trigger result for this plan. Subsequent plans (.F.4d / .F.4e+) need similar amendment notices — track via `/plan-context-sweep` |
| 23 | Latency accountability | ✅ PASS | "HOT_PATH_CHANGELOG entry NONE (parser + GUI only)" listed at Step 7 line 360 |
| 24 | Mirror-function call-sequence | N/A | No mirror functions added |
| 25 | TECH_DEBT.md surface-area scan | ⚠ YELLOW | TECH_DEBT-006 (stamp_drift_gap at line 1093) closure conditional on STAMP_BOUND derived filter shipping; plan claims "TECH_DEBT-006 closure scope" but lacks explicit mechanical tie. TECH_DEBT-009 (FOREACH_CFG_FIELD non-stamp-bound) partial closure also untracked in plan. |
| 26 | DEFERRED-FOR-FUTURE-SHIP | N/A | |
| 27 | DESIGN_SPECS pattern application | ✅ PASS | Applies type-trait-dispatch + categorical-tag + universal-cfg-field-registry + wire-format-byte-preservation patterns (Layer 5b is intent). MULTI_BIT_STATE pattern: 4 INT_ENUM rows (engine_arch, barrier_blend_mode, bandit_algorithm, risk_degradation_curve) are K-state candidates — plan does NOT apply multi-bit-state-encoding-pattern.md (deferred to .F.4f per umbrella line 44) ✅ correctly deferred. |
| 28 | Test-strength anti-regression | ✅ PASS | 3 new tests are mechanical; INT_ENUM clamp test value matters (verify default_val=0 for bandit_algorithm matches existing default behavior) |
| 29 | Mechanical citation drift | ⚠ 3 drifts (see findings) | `cfg_write_field` line 472 vs actual 477; test count 1822 vs 3118; per_core_fields[] line per predecessor NEW-3 |
| 30 | Predicate-contract-changed | N/A | No predicate extensions |
| 31 | Wider-build at sprint close | ✅ PASS | Step 6 includes `./build.sh test gui suite tsan asan` |

**Counts:** PASS=14; YELLOW=8; N/A=8; FAIL=0; DRIFT=1

---

## Cold-pickup completeness (10 fields)

| # | Field | Verdict | Notes |
|---|-------|---------|-------|
| C.1 | Branch state | ✅ PASS | "stay on `feat/v5.15-live-readiness`" matches current operator practice |
| C.2 | Phase exec order matches deps | ✅ PASS | Step 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 dependency-consistent |
| C.3 | First concrete move | ✅ PASS | Step 0 cites `git tag pre-v5.15.5.F.4c; ./build.sh test; ./build/controller_test 2>&1 \| tail -20` |
| C.4 | Function/constructor names cited | ⚠ MIXED | Amendment notice cites CORRECT names (`ControllerConfig_Load<F>`, `cfg_write_field`); body retains stale `Cfg_LoadFromString`/`Cfg_Save` Step 6 examples. Fresh coder confused if they read body without amendment notice. |
| C.5 | File:line refs | ⚠ DRIFT | `GUI/SettingsPanel.hpp:472` for `cfg_write_field` → ACTUAL line 477; `ControllerConfig.hpp:1798` for parser body ✅ correct; `tests/controller_test.cpp:1548` for canonical test ✅ correct |
| C.6 | Stale-claim audit | ⚠ HANDLED BY NOTICE | Amendment notice catches all known stale claims (Class 23 anti-shape, test count 1822, fictional functions). Plan body retention of stale samples is intentional per "preserve scope intent" instruction. |
| C.7 | Effort claims reconcile | ⚠ PARTIAL | "~400 LOC net (additive registry rows + 3 tt:: specializations; deletes ~150 LOC)" at line 11 + amendment-revised "~250 LOC net (was ~400)" at line 56. Net delta unclear; tt:: specializations are LIKELY ZERO LOC per amendment ("KIND_INT / _BOOL already covered"). Realistic estimate ~150 LOC additive (registry rows + INT_ENUM label arrays + clamp refinement) + ~80-120 LOC deletions (manual parser CFG_PARSE_INT/_U32 lines + manual field_defs[]). |
| C.8 | Source-audit references | ✅ PASS | Cites `.F.4b` plan, predecessor audit synthesis (`plans/plan_checks/2026-05-14-v5.15.5.F.4b-fresh-audits-synthesis.md`), DESIGN_SPECS, RECURRING_BUG_PATTERNS Class 23 |
| C.9 | Predecessor / dependent plans named with paths | ✅ PASS | Predecessor `.F.4b` cited with engine commit + tag; successor `.F.4d` cited with scope summary |
| C.10 | Tag names locked | ✅ PASS | `pre-v5.15.5.F.4c` rollback anchor; `v5.15.5.F.4c` ship tag (Step 7 line 373) |

**Cold-pickup score: 8/10** (C.4 + C.5 + C.7 are YELLOW — fresh session will lose ~15-25 min sorting stale code samples vs amendment notice).

**Compaction-degrades risk:** ~MED-HIGH. A compacted session reading only the plan body without explicit attention to the amendment notice block (lines 15-66) will reintroduce Class 23 anti-shapes from Step 1/4/5 code samples. The amendment notice MUST be the first thing a fresh coder reads.

---

## Findings (severity-classified)

### CRITICAL — none

### HIGH

**HIGH-1 — STAMP_BOUND derived filter implementation spec missing**
- Plan body line 9: "Closes panel_gap + parser_gap + persist_gap classes for these subset Kinds"
- Plan does NOT specify: (a) is `FOREACH_STAMP_BOUND_CFG_DERIVED(X)` preprocessor-filtered from `FOREACH_CFG_FIELD` at compile time, OR is it a runtime walk over `g_cfg_field_descriptors[]` with `(desc.metadata_flags & STAMP_BOUND) != 0` mask? (b) How does it interoperate with the EXISTING `FOREACH_STAMP_BOUND_CFG` at `ML_Headers/StampBoundCfgRegistry.hpp:99-176` (24 rows currently)? (c) When does the old registry retire?
- Per predecessor synthesis HIGH-3 verdict: Layer 5b lock was explicitly deferred from `.F.4b` to `.F.4c` exactly so the int-typed rows migrate FIRST and the hash actually locks something meaningful. But `.F.4c` plan body doesn't have a concrete spec.
- **Cite:** `CfgFieldRegistry.hpp:66` (STAMP_BOUND metadata bit declared); `StampBoundCfgRegistry.hpp:99-176` (24 rows; 11 int-typed; 4 already migrated to ml_cfg_flags BITMAP_BIT); `TECH_DEBT.md:1093` (TECH_DEBT-006 stamp_drift_gap closure conditional on Layer 5b filter)
- **Fix:** add Step N to plan: explicit derived-filter design (preprocessor vs runtime walk + which rows migrate vs stay + retirement criterion for `FOREACH_STAMP_BOUND_CFG`).

**HIGH-2 — Layer 5b hash lock procedural spec absent**
- Plan body amendment notice (line 56) says "INT_ENUM may need a small range-validation refinement"; predecessor synthesis HIGH-3 says hash lock test BELONGS at `.F.4c`.
- Plan does NOT specify: (a) Where the synthetic-population fixture lives (test file + function name). (b) Hash compute site (CI script? compile-time `static_assert(hash == LOCKED_VALUE)`? runtime test?). (c) Storage location for LOCKED_STAMP_BOUND_DERIVED_HASH_V5_15_5_F4 (header file? snapshot test?).
- Per `wire-format-byte-preservation-discipline.md` Layer 5b. Spec must be concrete enough to code from.
- **Fix:** add procedural spec OR explicitly defer to `.F.4d` with rationale (acceptable since Layer 5b is anti-reorder protection; defer until int rows are stable).

**HIGH-3 — Test count baseline drift**
- Plan Step 7 line 357: "`controller_test` passes (≥1822 + new INT/INT_ENUM/BOOL roundtrip tests)"
- Verified 2026-05-14: `./build/controller_test 2>&1 \| tail -3` → `RESULTS: 3118 passed, 0 failed`
- Amendment notice at line 39 says "actual is **3118**" but Step 7 verification list still says 1822.
- **Fix:** Step 7 line 357 → "≥3118 + new INT/INT_ENUM/BOOL roundtrip tests"

### MED

**MED-1 — Step 1 stale code samples are explicitly invalidated but retained verbatim**
- Plan body Step 1 (lines 82-176) has full `template <Kind K>` + `cfg_dispatch_target<KIND>` + `reinterpret_cast<X*>` pattern (Class 23 anti-shape).
- Amendment notice (lines 15-66) explicitly invalidates with "STALE patterns in this plan body — do NOT use as-written".
- Risk: compacted-context reader applies Step 1 samples literally. Mitigation: amendment notice is at top, before Step 1.
- **Fix:** add inline `>**STALE**:` note marker inside each affected Step (1, 4, 5) pointing back to amendment notice block.

**MED-2 — Tooltip preservation discipline for INT/BOOL fields not articulated**
- Plan Step 4 says "delete manual `field_defs[]` entry" but doesn't address: 11+ INT/BOOL fields in `GUI/SettingsPanel.hpp:35-306` have HAND-TUNED operator tooltips (e.g., `max_hold_ticks` at line 81-84 has 4-line tooltip; `notify_backend` at line 149-154 has 6-line backend explanation; `notify_command` at line 155-168 has full multi-protocol example).
- Per predecessor HIGH-6 (CLOSED at `.F.4b`): byte-identical tooltip preservation via `R"(...)"` raw strings is mandatory. Plan must mandate same discipline for INT/BOOL migration.
- Specific fields requiring byte-identical preservation per grep against `GUI/SettingsPanel.hpp:35-306`: `max_hold_ticks` (4 lines), `kill_recovery_warmup` (2 lines), `regime_hysteresis` (2 lines), `idle_reset_cycles` (2 lines), `sl_cooldown_cycles` (2 lines), `record_ticks` (3 lines), `record_depth` (5 lines), `record_max_days` (2 lines), `notify_backend` (6 lines), `notify_command` (~15 lines), `notify_cooldown_secs` (3 lines), `confidence_window` (3 lines), `num_execution_cores` (5 lines), `poll_interval` (4 lines), `warmup_ticks` (2 lines), `min_warmup_samples` (3 lines), `xgb_*` (4 fields × 2-3 lines each).
- **Fix:** add HIGH-6-equivalent discipline gate to plan Step 4: "All migrated INT/BOOL fields with hand-tuned tooltips MUST be preserved byte-identical via `R"(...)"` raw strings."

**MED-3 — BOOL field exclusion list (bitmap-resident bools) acknowledged in plan but not enumerated**
- Plan body lines 221-228 has the rule "BOOL fields that already live in `*_cfg_flags` BITMAP REGISTRIES are NOT migrated here" with an `rg` recipe.
- Per actual `FOREACH_<DOMAIN>_CFG_FLAG` audit: 5 domain registries (LIFECYCLE / GATE / ML / RISK / OPS) already absorb ~21 bool fields (per `GUI/SettingsPanel.hpp:273` "Registry is the SINGLE SOURCE OF TRUTH for these 21 boolean cfg flags").
- Plan lacks: explicit enumerated list of SCALAR uint8_t bool fields that DO enter the new registry vs the bitmap-resident bool fields that do NOT.
- **Fix:** add fenced-block enumeration of the SCALAR bool migration list (recommend ~10-15 fields per audit of `ControllerConfig.hpp` declarations not in `FOREACH_*_CFG_FLAG`).

**MED-4 — TECH_DEBT closure mechanically untied**
- Plan amendment notice says "TECH_DEBT-006 (stamp-bound dual registry) — plan closes at .F.4c" (per audit-specific focus item 10 in the orchestrator's brief).
- Plan body Step 7 verification gate line 364: "TECH_DEBT.md: parser-drift class entries for INT/INT_ENUM/BOOL marked CLOSED" — generic, doesn't tie TECH_DEBT-006 closure to derived-filter cutover specifically.
- **Fix:** add explicit closure mechanics: "TECH_DEBT-006 (stamp_drift_gap; `DOCS/TECH_DEBT.md:1093`) marked CLOSED when `FOREACH_STAMP_BOUND_CFG_DERIVED` lands AND Layer 5b hash lock test passes. TECH_DEBT-009 (FOREACH_CFG_FIELD non-stamp-bound) partial closure when all KIND_INT/_INT_ENUM/_BOOL fields migrated."

**MED-5 — INT field storage width audit absent**
- Plan body Step 4 says "INT/INT_ENUM/BOOL rows" without enumerating ACTUAL storage widths in `ControllerConfig.hpp`. Per `is_integral_v` / `is_unsigned_v` branches at `CfgFieldDispatch.hpp:79-88`: int8_t / int16_t / int32_t / int64_t / uint8_t-uint64_t all dispatch correctly via `static_cast<T>(v)` — but the descriptor's `as_int.clamp_min/max` is `int64_t`. If a `int8_t` cfg field has clamp range `[−128, 127]` but the registry row specifies `INT(0, 0, 1000)`, the cast truncates silently.
- Per actual code: `param_max_age_ticks` is `uint64_t` (`ControllerConfig.hpp:580`); `ws_dead_time_flatten_threshold_secs` is `int`; `recovery_delay_secs` is `int`; `model_max_age_hours` is `uint32_t`. Mixed widths.
- **Fix:** add Step 2.5 (between row additions and parser cutover): "Each INT row's clamp_min/max must fit destination type's range; verify via per-field `static_assert(payload.as_int.clamp_min >= std::numeric_limits<destination_type>::min())` style check."

**MED-6 — Step 5 GUI section dispatch code is stale (cfg_render_field doesn't exist yet)**
- Plan body Step 5 lines 270-303 shows `EMIT_PANEL_RENDER` macro with `tt::cfg_render_field<CfgFieldDescriptor::KIND_##kind>` calls.
- Verified: `tt::cfg_render_field` is NOT YET implemented anywhere in shipped code. `CoreFrameworks/CfgFieldDispatch.hpp:143` only contains a comment "Note: cfg_render_field<T> is implemented inline in GUI/SettingsPanel.hpp at T12".
- The `.F.4b` ship deferred render dispatch to GUI/SettingsPanel.hpp at "T12" (which would be a future task). Plan `.F.4c` Step 5 assumes it exists; it does not.
- **Fix:** Step 5 must FIRST add `tt::cfg_render_field<T>` to `CfgFieldDispatch.hpp` (or a new GUI-bound header), THEN extend with INT/INT_ENUM/BOOL render specializations. Existing render path uses CFG_FLOAT-only auto-extend at `GUI/SettingsPanel.hpp:302-309`.

### LOW

**LOW-1 — `cfg_write_field` line citation drift**
- Plan amendment notice line 38 says `GUI/SettingsPanel.hpp:472`. ACTUAL line 477.
- Mechanical citation drift; ~5 line shift since plan draft.

**LOW-2 — `per_core_fields[]` location note inherited from predecessor NEW-3**
- Plan body doesn't address per-core override emission (deferred to `.F.4g`); not a `.F.4c` concern.

**LOW-3 — Test count assertion fragility post-`.F.4c`**
- After `.F.4c` ships, the baseline becomes ≥3118 + N new INT/INT_ENUM/BOOL tests (likely +5-10). Step 7 verification should use `≥3118 + 3` form (Check 21 anti-pattern protection).

**LOW-4 — DOCS/CHANGELOG.md update not listed at Step 7**
- Same gap as predecessor MED-8. Mechanical fix at coding time.

**LOW-5 — Sub-ship-close FEATURE_LOOKUP.md auto-write contract not invoked**
- Plan ships "STAMP_BOUND derived filter" + "Layer 5b hash lock" — both operator-visible discipline surfaces. Auto-write contract (CLAUDE.local.md) requires FEATURE_LOOKUP entry on operator-visible features.
- Verdict: arguable — these are internal discipline patterns, not operator-facing GUI features. Defer to ship-close audit; not blocking.

**LOW-6 — Compound-literal note for INT_ENUM labels (plan body line 254)**
- "Note: the inline array literal pattern (`(const char* const[]){a, b}`) is a C99 compound literal. Verify C++20 accepts it"
- C++20 does NOT accept C99 compound literals (extension via -fms-extensions or GCC compound-literal extension only). Plan correctly hedges with "if not, declare the label array as a named static" — adopt the named-static form upfront to avoid GCC-extension dependency.

---

## Hidden scope detected

1. **Layer 5b CI test scaffolding** — synthetic fixture + hash compute + commit-locked value. ~20-40 LOC if runtime walk; ~10-15 LOC if compile-time static_assert + macro.
2. **`tt::cfg_render_field<T>` implementation** — Step 5 assumes exists. Actually needs adding (ImGui::SliderInt / Combo / Checkbox specializations); ~30-50 LOC.
3. **Per-field `static_assert` on int width-vs-clamp-range** — MED-5; ~5-15 LOC per cohort.
4. **TECH_DEBT-006 + -009 closure entry edits** — ~10 LOC each.
5. **CHANGELOG.md entry** — ~10 LOC.
6. **Tooltip byte-identity verification** — automated grep or manual diff against `GUI/SettingsPanel.hpp:35-306` snapshot; defer to coding time.

**Realistic scope re-estimate:** ~250-350 LOC net additive (registry rows + INT_ENUM label arrays + render specializations + Layer 5b test + closure edits) − ~80-120 LOC deletions (manual parser/panel sites) = **~150-270 LOC NET**. Plan body's "~400 LOC" is overstated; amendment notice's "~250 LOC" is closer to reality but still optimistic if Layer 5b + render specs land in same ship.

---

## Drift audit (train ↔ serve, write ↔ read)

| Category | Verdict | Notes |
|---|---|---|
| Feature drift | N/A | No FeatureRegistry changes |
| Label drift | N/A | No LabelFunctions changes |
| Metric drift | N/A | |
| Path drift | N/A | |
| **Format drift (stamp body)** | **⚠ DRIFT-RISK** | Migrating 11 int-typed stamp-bound fields from `FOREACH_STAMP_BOUND_CFG` to derived filter over `FOREACH_CFG_FIELD` MUST preserve canonical byte order (HMAC chain in `wire-format-byte-preservation-discipline.md`). Plan acknowledges Layer 5b but spec missing → mid-migration hash flip risk if row order in `FOREACH_CFG_FIELD` doesn't match historical emit order from `FOREACH_STAMP_BOUND_CFG`. **Fix proposal:** snapshot existing `FOREACH_STAMP_BOUND_CFG` emit order BEFORE migration; ensure derived filter walks `FOREACH_CFG_FIELD` in the same logical order (interleave by metadata bit position; verify via byte-equivalent stamp output test); commit a `LOCKED_STAMP_BOUND_DERIVED_HASH_V5_15_5_F4` constant + static_assert. |
| Threshold drift | N/A | |
| Tick-source drift | N/A | |
| Build-flag drift | N/A | |

---

## Cross-plan checks

- Sprint umbrella `2026-05-13-v5.15.5.F.4-universal-cfg-registry-sprint.md` correctly lists `.F.4c` (line 41) as in-scope; amendment notice (line 6) acknowledges `.F.4b` SHIPPED + LOCKED descriptor schema.
- Successor `.F.4d` correctly references KIND_STRING + KIND_FILE_PATH scope; plan boundary is clean.
- No conflicting dependencies between `.F.4c` and queued `.F.4e` (slow-path migration) / `.F.4g` (per-core re-layout) — those are independent.

---

## Recommendations

### Must fix before coding (~10-15 min)

1. **HIGH-1** — add concrete STAMP_BOUND derived filter implementation spec (preprocessor filter vs runtime walk; interop with existing `FOREACH_STAMP_BOUND_CFG`; retirement criterion).
2. **HIGH-2** — add Layer 5b CI hash test procedural spec OR explicitly defer to `.F.4d` with rationale.
3. **HIGH-3** — update Step 7 test count baseline 1822 → 3118.
4. **MED-2** — add tooltip byte-identity preservation gate (HIGH-6 equivalent) to Step 4.
5. **MED-6** — clarify that `tt::cfg_render_field<T>` needs implementing in Step 5 (not yet shipped).

### Worth fixing during coding (non-blocking, ~5 min each)

6. **MED-1** — annotate Steps 1/4/5 with inline `>**STALE**:` markers pointing back to amendment notice.
7. **MED-3** — enumerate SCALAR vs bitmap-resident bool migration list.
8. **MED-4** — explicit TECH_DEBT-006 + -009 closure mechanics in Step 7.
9. **MED-5** — int width-vs-clamp-range static_asserts.
10. **LOW-1** — fix `cfg_write_field` line citation 472 → 477.
11. **LOW-3** — Step 7 test count use `≥3118 + N` form (Check 21).
12. **LOW-4** — add `DOCS/CHANGELOG.md` to Step 7 list.
13. **LOW-6** — adopt named-static label arrays upfront (skip C99 compound-literal hedge).

### Acceptable risk (don't block)

- Compaction-degradation risk on plan body Steps 1/4/5: amendment notice mitigates as long as fresh coder reads top-of-plan first.
- LOC estimate variance: scope is registry-driven; mechanical work; LOC is incidental per `feedback_dont_measure_structural_work_by_loc.md`.

---

## Verdict: YELLOW

**Recommendation:** patch HIGH-1/-2/-3 + MED-2 + MED-6 (~10-15 min of plan-body edits) before coding starts. The remaining MED/LOW items can be addressed during coding as mechanical fix-ups.

**Coding path summary if Caramel proceeds after patch:**
1. Step 0: rollback tag + clean baseline ✅ as written
2. Step 1: SKIP — tt:: integer dispatch already shipped per amendment notice; add INT_ENUM range-clamp refinement only (~5 LOC) + adopt named-static label arrays
3. Step 2: add ~30 INT + ~10 INT_ENUM + ~15 BOOL rows to `FOREACH_CFG_FIELD` (mechanical; mirror `.F.4b` DOUBLE/_PCT shape)
4. Step 3: declare INT_ENUM label arrays as named statics
5. Step 4: delete manual `CFG_PARSE_INT/_U32` + `field_defs[]` entries for migrated fields; verify tooltip byte-identity
6. Step 5: implement `tt::cfg_render_field<T>` for INT/INT_ENUM/BOOL (with KIND-dispatch on Combo/Checkbox); extend `EMIT_CFG_FIELD_DEF_FROM_REGISTRY` macro at `SettingsPanel.hpp:302-309`
7. Step 5.5 (NEW): STAMP_BOUND derived filter + Layer 5b hash test
8. Step 6: build + test + paper trade
9. Step 7: verification gate + closure entries + version bump

**Original verdict before audit:** assumed-GREEN (operator queued `.F.4c` after `.F.4b` ship). **Audited verdict:** YELLOW — amendment notice handles most stale-code drift but several procedural spec gaps remain (derived filter, Layer 5b, render dispatch, tooltip preservation). 5-10 min of patches converts to GREEN.

---

## Synthesis cross-ref

Lessons-learned reference: predecessor audits at `plans/plan_checks/2026-05-14-v5.15.5.F.4b-fresh-audits-synthesis.md` + `readiness-recheck-2026-05-14-v5.15.5.F.4b-amended.md` document the structural fixes that closed Class 23 + made this plan's amendment notice possible. The `.F.4c` audit benefits directly from `.F.4b`'s YELLOW-to-GREEN trajectory; same path forward applies here.
