# /readiness re-check report — v5.15.5.F.4b AMENDED — 2026-05-14

**Audited plan:** `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4b-foreach-cfg-field-registry-implementation.md` (rewritten 2026-05-14)
**Predecessor in synthesis:** `plans/plan_checks/2026-05-14-v5.15.5.F.4b-fresh-audits-synthesis.md` (2 CRITICAL + 7 HIGH + 13 MED + 6 LOW findings)
**Engine HEAD:** `f72caef` = v5.15.5.F.3 (matches plan's predecessor citation)
**Operator:** Caramel
**Stage 0 DESIGN_SPECS preloaded:** type-trait-dispatch-via-tt-namespace, universal-cfg-field-registry-pattern, categorical-tag-applicability-pattern, registry-tuple-as-single-source-of-truth, bitmap-overflow-protection-discipline, wire-format-byte-preservation-discipline, autopopulate-pattern-for-production-caller-class, structural-fix-preferred-decision-framework

---

## Executive verdict: YELLOW

**Closure summary:**
- 2 CRITICAL: 1 CLOSED, 1 PARTIAL (NEW issue introduced — see below)
- 7 HIGH: 6 CLOSED, 1 NOT-CLOSED (HIGH-7 INFERENCE_CFG_AUTOPOPULATE orthogonality note absent)
- 13 MED: 9 CLOSED, 4 PARTIAL/missing
- 6 LOW: 3 CLOSED, 2 PARTIAL/deferred, 1 NOT-CLOSED
- 4 NEW issues introduced by rewrite (1 build-blocking)

**Cold-pickup completeness: IMPROVED but not yet 10/10** — function names + line refs corrected (was the major cold-pickup blocker per original synthesis); 1 contradiction remains within Step 3 (T::FRAC_BITS vs T::F).

The plan is much closer to GREEN than the original. **One blocker (NEW finding NEW-1: T::FRAC_BITS will compile-fail)** must be fixed before coding starts (~5 min mechanical edit). Once that and HIGH-7 land, plan is GREEN.

---

## CRITICAL closure verdicts

### CRITICAL-1 — FPN<F>-vs-double type dispatch
**Status: CLOSED via 3-barrier structural fix; NEW NEW-1 introduced (see below).**

Verified:
- ✅ Step 1 adds `is_FPN_v` type trait with proper `template <typename T> struct is_FPN : std::false_type` + `template <unsigned F> struct is_FPN<FPN<F>> : std::true_type` specialization (plan lines 49-51)
- ✅ Step 3's `tt::cfg_parse_field<T>` is `template <typename T>` with T deduced from field reference (plan lines 299-300, 351-352, 399-400) — NOT `template <Kind K>` per anti-pattern
- ✅ Type-family `static_assert` present in all 3 dispatch helpers (plan lines 305-312, 353-358, 401-406)
- ✅ X-macro extractor in Step 4 passes field BY REFERENCE: `tt::cfg_parse_field(cfg.name, ...)` (plan line 464)
- ✅ NO `reinterpret_cast` or `void*+offset` patterns in planned NEW code (verified via grep — only mentions are explicit BANS at plan lines 269, 434, 832)
- ✅ Step 1 ALREADY pre-implemented in working tree (uncommitted) — `FixedPoint/FixedPointN.hpp:54-79` has `is_FPN_v` + `FPN<F>::F = FRAC_BITS` exposed; `tests/controller_test.cpp:88-100` has 7 static_asserts. The rewrite is partially landed; coding can pick up from existing state.

But: **NEW-1 (build-blocking) — see "New issues introduced by rewrite" below.**

### CRITICAL-2 — False function-name claims
**Status: CLOSED.**

Verified:
- ✅ `ControllerConfig_Load<F>` exists at `CoreFrameworks/ControllerConfig.hpp:1798` (plan citation correct)
- ✅ `cfg_write_field(path, key, value)` exists at `GUI/SettingsPanel.hpp:472` (plan citation correct)
- ✅ `field_defs[]` exists at `GUI/SettingsPanel.hpp:46` (plan citation correct)
- ✅ NO references to `CfgParser_HandleKV` / `Cfg_Save` / `Cfg_LoadFromString` / `Cfg_LoadFromFile` / `parse_csv_engine_config` anywhere in amended plan body (confirmed via grep)
- ✅ Special cases preserved correctly identified: `fee_rate_maker/taker` at lines 1968-1977 with `_explicitly_set` side effect; `session_*_mult` via FOREACH_SESSION_PHASE at lines 1957-1959; `param_max_age_ticks` (uint64_t with explicit handling) at line 1994

**Minor doc nit (NEW-3 — see below):** plan claims `per_core_fields[]` is at "line 425"; actual location is line 326. The corrective note in Step 6 has a small inaccuracy. Not blocking — `field_defs[]` location at line 46 is what's actually load-bearing for Step 6 work.

---

## HIGH closure verdicts

### HIGH-1 — Descriptor cache-line budget consistency
**Status: CLOSED.** All 3 sites (lines 181, 621, 838) say `<= 128`. No `<= 64` references remain. ✅

### HIGH-2 — X-macro tuple arity (7 vs 12)
**Status: CLOSED.** All EMIT_* macros use 12-arg tuple. Plan lines 460-466 (parser), 511-518 (save), 563-566 (render auto-extend) all consistent. The "(KIND_TOKEN, name, label, section, meta, payload, tooltip, applies_to_strategy_cat, applies_to_op_mode_cat, applies_to_regime_cat, applies_to_risk_cat, lives_in_struct)" canonical 12-col tuple at line 192-194 is referenced consistently throughout. ✅

### HIGH-3 — Layer 5b hash lock deferred to .F.4c
**Status: CLOSED.** Plan line 737-738 explicitly defers STAMP_BOUND derived filter + Layer 5b hash lock to .F.4c with rationale "need full type coverage so Layer 5b hash lock is meaningful". HIGH-3 fix Option (A) per synthesis recommendation adopted. ✅

### HIGH-4 — Locale pinning in tt::cfg_save_field
**Status: CLOSED.** Plan line 365-367 + 389-392 add `newlocale` / `uselocale` / `freelocale` per `wire-format-byte-preservation-discipline.md` Layer 2 in `tt::cfg_save_field`. Save-side only (parse-side via `parse_double_fast` is already locale-independent via `std::from_chars` at `CoreFrameworks/ParseFast.hpp:44-50`). ✅

**Bonus quality point:** parse-side migration is a SILENT IMPROVEMENT — the existing `atof(val)` calls at ControllerConfig.hpp:1879, 1887, 1908 are NOT locale-pinned today. Migrating to `parse_double_fast` ALSO closes the parse-side locale risk. Plan implicitly addresses both directions of locale safety.

### HIGH-5 — Stretch goal "X-macro generates Cfg struct fields" dropped
**Status: CLOSED at .F.4b body level; STALE in umbrella plan.** Plan line 739 + 831 explicitly DROPPED. ✅

**Caveat (NEW-4 — see below):** Umbrella plan `2026-05-13-v5.15.5.F.4-universal-cfg-registry-sprint.md:38, 118` STILL lists "stretch: X-macro generates Cfg struct fields" as in-scope for .F.4b. Umbrella needs sync amendment. Not blocking .F.4b coding (the .F.4b body is authoritative); but a future cold-pickup of the umbrella will mislead.

### HIGH-6 — SettingsPanel migration table + tooltip preservation
**Status: CLOSED.** Plan lines 534, 537, 569 explicitly mandate byte-identical tooltip preservation via R"(...)" raw strings. Step 7 line 671-678 includes regression test. Migration table location lines 536-540. Auto-extend coexistence with existing 5 FOREACH_*_CFG_FLAG sources documented at lines 540-558. ✅

### HIGH-7 — INFERENCE_CFG_AUTOPOPULATE orthogonality concern
**Status: NOT-CLOSED.** Plan body has zero mention of `INFERENCE_CFG_AUTOPOPULATE` or `FOREACH_CFG_DERIVED_INFERENCE_CFG`. Original synthesis recommended adding a header design comment in `CfgFieldRegistry.hpp` documenting the orthogonality (~7 cfg fields overlap: confidence_hard_block_threshold, held_out_fraction, bandit_blend_ratio, fee_rate_*, ml_tp_pct, ml_sl_pct, barrier_blend_mode). The synthesis explicitly noted "no .F.4b code change required" — just a documentation comment in the new header.

**Severity:** LOW-MEDIUM. The two registries serve different consumers (cfg parse/save/render vs inference cfg stamp emit); no functional overlap. But future contributors may not notice the orthogonality and try to consolidate. ~5 min fix at coding-time (paste a header comment block in CfgFieldRegistry.hpp).

---

## MEDIUM item closure

| # | Item | Status |
|---|---|---|
| MED-1 | test count 3108 (not 1822) | ✅ CLOSED — plan line 29 + 782 |
| MED-2 | Version.hpp 5.15.5.E → 5.15.5.F.4b | ✅ CLOSED — Step 8 commit message documents 4-ship lag backfill (lines 689-693, 744-747) |
| MED-3 | line refs corrected (1798 / 472 / 46) | ✅ CLOSED — all 3 plan citations match HEAD |
| MED-4 | file-byte memcmp test | ✅ CLOSED — plan line 601 |
| MED-5 | StrategyCategory tier (CORE / SPECIFIC / EXPERIMENTAL) discipline documented | ✅ CLOSED — plan lines 218, 223, 233 |
| MED-6 | Layer 5b CI hash test procedural spec | ⏸ DEFERRED — consistent with HIGH-3 deferral to .F.4c (lock + spec ship together) |
| MED-7 | LOC estimate consistency | ⚠ PARTIAL — line 10 says "net +650 LOC" but math (600 - 250 = 350) doesn't reconcile to "~900 LOC net" headline. Minor; not session-blocking. |
| MED-8 | DOCS/CHANGELOG.md update missing from Step 7 | ⚠ NOT-CLOSED — Step 7 + Step 8 don't list CHANGELOG.md update; mechanical fix at coding |
| MED-9 | "90 used / 38 padding" actual is 96/32 | ⚠ PARTIAL — plan line 174 still says "90 bytes used + 38 padding". With natural alignment (cstring* needs 8B alignment after 10-byte categorical block → 6B padding to offset 56 → uint64+payload32 to 96 used), actual is 96 used + 32 padding to 128. Comment incorrect; static_assert protects against overflow so functionally OK. |
| MED-10 | _reserved default-init to 0 | ✅ CLOSED — plan line 144 has `uint16_t _reserved = 0;` |
| MED-11 | KIND_FPN reserved without payload union member (drop) | ✅ ACCEPTABLE — KIND_FPN at plan line 107 is COMMENTED OUT in "RESERVED for future" block; not active so no half-defined drift. Synthesis recommended drop; commented-out is functionally equivalent. |
| MED-12 | wider-build at sprint close (Check 31) | ✅ CLOSED — plan Step 7 line 578 + 781 runs `./build.sh test gui suite tsan asan` |
| MED-13 | Y3 dispatch token-paste form | ⏸ DEFERRED — not addressed; impl detail decided at coding-time |

**MED summary:** 9/13 CLOSED, 1 acceptable, 1 deferred for HIGH-3 dependency, 2 missing (MED-8 CHANGELOG, MED-13 Y3 dispatch — both <5 min coding-time fixes).

---

## LOW item closure

| # | Item | Status |
|---|---|---|
| LOW-1 | EMIT_PANEL_RENDER categorical-mask filter | ✅ CLOSED — plan line 571 documents `(descriptor.applies_to_strategy_cat & active_strategy_cats) != 0` filter |
| LOW-2 | Per-field categorical mask values strategy | ✅ CLOSED — plan line 197 explicit "STRAT_CAT_ALL conservative default; .F.4h refines" |
| LOW-3 | `static_assert(lives_in_struct == STRUCT_CFG)` companion macro | ⚠ NOT-CLOSED — would catch accidental NEW non-STRUCT_CFG row landing at .F.4b. ~5 min addition. |
| LOW-4 | FOREACH_STRATEGY adding category_mask column | ⏸ DEFERRED to .F.4h per plan line 197 — synthesis recommended adding now (zeros first, populate later) but plan defers; not blocking for .F.4b's KIND_DOUBLE/_PCT scope |
| LOW-5 | metadata_flags dispatch shape (Option A/B) | ⏸ DEFERRED — impl detail |
| LOW-6 | Categorical-vs-state-enum dual representation | ⏸ DEFERRED — design discussion |

---

## NEW issues introduced by the rewrite

### NEW-1 (BUILD-BLOCKING) — `T::FRAC_BITS` will not compile; should be `T::F`

**Sites:** plan lines 327, 418, 436. Code samples use `FPN_FromDouble<T::FRAC_BITS>(v)`.

**Why this fails:** `FRAC_BITS` is the template parameter NAME of `FPN<FRAC_BITS>` (per `FixedPoint/FixedPointN.hpp:32`). It's NOT a class member accessible via `T::FRAC_BITS`. The class members exposed for outside-template access are:
- `static constexpr unsigned F = FRAC_BITS;` (line 38 — pre-staged this session)
- `static constexpr unsigned TOTAL_BITS = FRAC_BITS * 2;` (line 39)
- `static constexpr unsigned N = TOTAL_BITS / 64;` (line 40)
- `static constexpr unsigned FRAC_WORDS = FRAC_BITS / 64;` (line 41)

The pre-staged work explicitly added `F = FRAC_BITS` (with commentary "expose template parameter as member for T::F access in templated dispatchers. tt::cfg_parse_field<T> needs FPN_FromDouble<T::F>(v)") for EXACTLY this Step 3 use case. **The plan body's code samples contradict the pre-staged work.**

Plan line 322 comment says "Use T::F to instantiate FPN_FromDouble at the right F" — comment is RIGHT, code below is WRONG. Plan line 436 explanatory note also incorrectly says "if not exposed today, add it" — actual fact: already exposed via the staged work.

**Fix:** mechanical replace `T::FRAC_BITS` → `T::F` at plan lines 327, 418, 436. ~2 min. **Must be done before coding starts** or build will fail at the FPN dispatch case.

### NEW-2 — Plan claims `is_FPN_v` and `FPN<F>::F` need to be ADDED at Step 1, but both are PRE-STAGED in working tree

**Sites:** plan lines 38-60 (Step 1).

**Reality:** `git diff HEAD FixedPoint/FixedPointN.hpp` shows both already added with v5.15.5.F.4b commentary; `git diff HEAD tests/controller_test.cpp` shows 7 static_asserts already added (lines 88-100 of controller_test.cpp). Working tree has uncommitted (`M`) state for these two files.

**Severity:** LOW — accelerates ship (Step 1 already done); coder just needs to verify the staged work matches Step 1 spec. Plan should add a 1-line note "Step 1 partially pre-staged in working tree (FixedPointN.hpp + controller_test.cpp); verify and continue" so a fresh-context coder doesn't get confused by `git status` output.

### NEW-3 — `per_core_fields[]` location citation is wrong (326 not 425)

**Site:** plan line 532. Says "(NOT line 425; that's `per_core_fields[]`)".

**Reality:** `per_core_fields[]` is at `GUI/SettingsPanel.hpp:326`, NOT line 425.

**Severity:** LOW — the corrective note is mostly right (warns away from wrong location); just the SPECIFIC wrong location it cites is itself wrong. The actually-load-bearing `field_defs[]` at line 46 is correct, so .F.4b coding can proceed.

### NEW-4 — Umbrella plan stale relative to .F.4b rewrite

**Sites:** `plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4-universal-cfg-registry-sprint.md:38, 118`.

Umbrella plan still lists "stretch: X-macro generates Cfg struct fields" as in-scope for .F.4b. The .F.4b body REWROTE this to DROPPED (HIGH-5 closure). Cross-plan inconsistency.

**Severity:** LOW — .F.4b body is authoritative; not session-blocking. But fresh-context cold-pickup of umbrella will mislead. Sync amendment ~3 min: edit umbrella line 38 to remove "stretch" mention; line 118 to note "REMOVED at .F.4b rewrite".

### Bonus observation — `TECH_DEBT-006` reference imprecision

Plan line 813 says "TECH_DEBT-006 (stamp-bound dual registry) → DEFERRED to .F.4c". But `DOCS/TECH_DEBT.md:162` has TECH_DEBT-006 already CLOSED (different topic — "FOREACH_STAMP_BOUND_MODEL_CONST registry for architectural fields", closed v5.14.8). The plan is referring to the related-but-distinct concept at TECH_DEBT.md:1087 ("stamp_drift_gap: TECH_DEBT-006: FOREACH_STAMP_BOUND_CFG vs FOREACH_CFG_FIELD dual registry"). Should clarify which TECH_DEBT entry — the two share a number incidentally. ~2 min doc fix.

---

## Cold-pickup completeness re-verdict

| # | Field | Original | Amended |
|---|-------|----------|---------|
| C.1 | Branch state | PASS | PASS — `feat/v5.15-live-readiness` |
| C.2 | Phase order matches deps | PASS | PASS — Step 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 |
| C.3 | First concrete move | PASS | PASS — Step 0: `git tag pre-v5.15.5.F.4b; ./build.sh test` |
| C.4 | Function/constructor names | **FAIL (CRITICAL-2)** | **PASS** — all citations resolve to actual code |
| C.5 | File:line refs | **FAIL (3 wrong)** | **PASS modulo NEW-3** — major refs corrected; 1 minor inaccuracy in corrective-note |
| C.6 | Stale-claim audit | PASS | PASS |
| C.7 | Effort claims reconcile | PASS | ⚠ MED-7 — math doesn't tie out (~900 LOC net vs 600-250=350 net); minor |
| C.8 | Source-audit references | PASS | PASS — synthesis at `plans/plan_checks/2026-05-14-v5.15.5.F.4b-fresh-audits-synthesis.md` cited line 14 |
| C.9 | Predecessor / dependent plans named with paths | PASS | PASS |
| C.10 | Tag names locked | PASS | PASS — `pre-v5.15.5.F.4b`, `v5.15.5.F.4b` |

**Cold-pickup: improved from 7/10 to 9/10** (C.4 + C.5 critical failures closed; C.7 still YELLOW). Fresh session would lose ~5-10 min on the 3 NEW-1 sites + ~5 min noting pre-staged work + ~5 min on MED-9/MED-7 internal contradictions = ~20 min total. Was ~1 hour pre-amendment.

---

## Other 28-check items (not addressed in original audit)

| # | Check | Status |
|---|---|---|
| 1 | Hot path purity | ✅ PASS — boot + GUI only; explicit verification gate at plan line 786 |
| 2 | Train-serve parity | ✅ PASS — HIGH-3 explicitly defers stamp body change to .F.4c; .F.4b is parity-neutral |
| 3 | Surface area | ⚠ YELLOW — touches 4 NEW files + 2 EXISTING files; ~900 LOC. Acceptable for X-macro infrastructure ship; under "8 file" threshold per /readiness ≤8 rule. |
| 4 | Pointer init / heap lifecycle | ✅ PASS — descriptor + tt:: helpers are stack/static; no heap allocation |
| 5 | Backward compat | ✅ PASS — no version constants bumped; descriptor is BOOT-only metadata |
| 6 | Multi-threading | ✅ PASS — `uselocale` is per-thread by design (POSIX); no shared state |
| 7 | Test coverage | ✅ PASS — Step 7 lists 8+ new tests; test count baseline 3108 → ≥3108 + new |
| 8 | Docs + invariants | ⚠ MED-8 — DOCS/CHANGELOG.md update missing |
| 9 | Forward maintenance | ✅ PASS — registry-driven; CLAUDE.md item 13 X-macro principle |
| 10 | Rollback story | ✅ PASS — `pre-v5.15.5.F.4b` tag + reset --hard documented at plan line 845 |
| 11 | Architectural sprint | ✅ PASS — calls_graph_diff scheduled at plan line 786 |
| 12 | Display ↔ execution invariant | N/A — no Position fields touched |
| 13 | Strategy lifecycle completeness | N/A — no strategy lifecycle changes |
| 14 | X-macro / dispatch | ✅ PASS — Step 7 has CI Test 1 (no orphan strategy categories) + CI Test 2 (no orphan cfg fields); EXTENSIBILITY block per Check 14 sub-item 4 |
| 15 | ML feature parity regression | N/A — no FeatureRegistry / ML pipeline touch |
| 16 | New cfg field with stamp-bearing | N/A at .F.4b — STAMP_BOUND derived filter deferred to .F.4c |
| 17 | Model-load path strict-mode | N/A — no model load changes |
| 18 | Reuse-audit | ✅ PASS — plan reuses `tt::stamp_parse_field<T>` precedent (StampBoundModelConstRegistry.hpp:101-124); reuses existing `cfg_write_field` (no replacement); reuses existing 5 FOREACH_*_CFG_FLAG auto-extends; reuses `parse_double_fast` from ParseFast.hpp |
| 19 | Pre-existing-work audit | ⚠ NEW-2 — `is_FPN_v` + `F = FRAC_BITS` ALREADY pre-staged in working tree; plan doesn't acknowledge |
| 20 | Future-proofness | ✅ PASS — registry shape locks at .F.4b; future kinds add 1 row; lives_in_struct discriminator covers v5.15.6 cfg files |
| 21 | Test count assertion fragility | ✅ PASS — Step 7 uses `≥3108` not `==3108` (plan line 782) |
| 22 | Auto-trigger downstream re-audit | ⚠ NEW-4 — umbrella plan `2026-05-13-v5.15.5.F.4-universal-cfg-registry-sprint.md` STALE on stretch goal |
| 23 | Latency accountability | ✅ PASS — plan line 808 explicit "HOT_PATH_CHANGELOG entry: NONE — boot/GUI only" verbatim |
| 24 | Mirror-function call-sequence | N/A — no mirror functions added |
| 25 | TECH_DEBT.md surface scan | ⚠ partial — TECH_DEBT-006 reference imprecise (see NEW issues bonus); TECH_DEBT-009 / -013 correctly referenced |
| 26 | DEFERRED-FOR-FUTURE-SHIP | N/A |
| 27 | DESIGN_SPECS pattern application | ✅ PASS — applies type-trait-dispatch + universal-cfg-field-registry + categorical-tag + bitmap-overflow + registry-tuple + wire-format-byte-preservation patterns; all referenced from plan body |
| 28 | Test-strength anti-regression | ✅ PASS — no test deletions/weakenings; 2 tautological `check(..., true)` at lines 625, 634 are intentional wrappers for compile-time `static_assert`s (Pattern D legitimate) |
| 29 | Mechanical citation drift | ⚠ NEW-1 + NEW-3 + NEW-4 cited above |
| 30 | Predicate-contract-changed | N/A |
| 31 | Wider-build at sprint close (Check 31) | ✅ PASS — plan Step 7 runs full `./build.sh test gui suite tsan asan` |

---

## Top blocker findings (must address before .F.4b coding)

1. **NEW-1 (BUILD-BLOCKING):** mechanical replace `T::FRAC_BITS` → `T::F` at plan lines 327, 418, 436. ~2 min. The pre-staged code explicitly added `F = FRAC_BITS` for this purpose; using `T::FRAC_BITS` will compile-fail.

2. **HIGH-7 (DOC):** add `INFERENCE_CFG_AUTOPOPULATE` orthogonality header comment to `CfgFieldRegistry.hpp` design comment block. Synthesis explicitly recommended this at "no .F.4b code change required" — just a documentation comment listing the ~7 overlapping cfg fields and noting different consumers. ~5 min at coding time.

## Worth fixing during coding (non-blocking)

3. **MED-9:** plan line 174 byte recount ("90 used + 38 padding" → "96 used + 32 padding") — comment correctness only; static_assert protects against overflow.

4. **NEW-2:** add 1-line note in Step 1 acknowledging Step 1 is pre-staged in working tree (FixedPointN.hpp + controller_test.cpp `M` status) so fresh-context coder doesn't get confused.

5. **NEW-3:** correct `per_core_fields[]` line citation at plan line 532 (326 not 425).

6. **NEW-4:** sync umbrella plan `2026-05-13-v5.15.5.F.4-universal-cfg-registry-sprint.md` to remove "stretch" mention at lines 38, 118.

7. **MED-8:** add CHANGELOG.md update step to Step 7 sequence.

8. **TECH_DEBT-006 reference:** clarify which TECH_DEBT-006 (the closed v5.14.8 entry vs the stamp_drift_gap at TECH_DEBT.md:1087).

9. **LOW-3:** add `static_assert(lives_in_struct == STRUCT_CFG)` companion macro to catch accidental NEW non-STRUCT_CFG entries during .F.4b scope.

## Acceptable risk (don't block)

- MED-7 LOC reconciliation (math doesn't tie out)
- MED-13 Y3 dispatch token-paste form (impl detail)
- LOW-4 FOREACH_STRATEGY category_mask column (deferred to .F.4h)
- LOW-5 / LOW-6 deferred design discussions

---

## Sprint-wide concerns (for downstream subplans)

### Check 22 auto-trigger — umbrella sync needed

Per Check 22, when an "umbrella ship" closes that touches a SHARED SURFACE (cfg field surface in this case), downstream sub-plans should be re-checked. .F.4b's CRITICAL-1 + CRITICAL-2 amendments closed structural design errors that would have rippled into .F.4c / .F.4d / .F.4e / .F.4f / .F.4g / .F.4h / .F.4i if not caught. Recommend running `/plan-check` over the full v5.15.5.F.4 sub-ship list (`.F.4c` through `.F.4i` + `v5.15.6.A/B/C`) AFTER .F.4b ships, with focus on:

- Any sub-plan citing `tt::cfg_parse_field<KIND_DOUBLE>` (per-Kind dispatch) — should rewrite per CRITICAL-1 fix to `tt::cfg_parse_field<T>` (per-type dispatch)
- Any sub-plan citing `CfgParser_HandleKV` / `Cfg_Save` / etc. — should rewrite per CRITICAL-2 fix
- Any sub-plan referencing the .F.4b stretch goal — should remove (HIGH-5 closure)

### Auto-write contract action

Per CLAUDE.local.md auto-write contract, an entry should land in `tick-trader-percore-workspace/FEATURE_LOOKUP.md` after .F.4b ships ("registry-driven Settings tab"). Plan acknowledges this at line 809.

---

## Verdict: YELLOW (proceed to coding after ~10-min fix-up)

**GREEN gate requires:** NEW-1 (T::FRAC_BITS → T::F) + HIGH-7 (orthogonality doc note) addressed in the plan body OR explicitly accepted as coding-time fix-ups. The two together are ~7 min of mechanical edits.

**Original verdict was RED** (2 CRITICAL design errors + cold-pickup hostility from wrong function names). **Rewrite closed both CRITICAL items structurally** + 6/7 HIGH items + 9/13 MED items + 3/6 LOW items. The remaining 1 NEW build-blocker is mechanical (search-replace).

**Recommendation:** address NEW-1 in the plan (3 mechanical replaces) BEFORE coding starts; document HIGH-7 as 5-min fold-in at coding time (header comment in `CfgFieldRegistry.hpp`); proceed to .F.4b implementation.
