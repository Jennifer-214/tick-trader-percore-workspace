# /readiness re-fire — v5.15.5.F.4d.1.B.3 Phase L v1.15 amendment

**Date:** 2026-05-18
**Plan body:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` (1312 lines, v1.15 DRAFT)
**Engine HEAD:** `3d27512` (WIP-checkpoint 6 — Step 1.6.3 TYPE-SENSITIVE test mitigations)
**Scope:** post-v1.15 amendments only; prior v1.14 fire's 4 stale doc sites confirmed addressed; this fire scans for NEW staleness introduced by v1.15 + completeness of v1.15-specific scope additions.
**Focus areas:** v1.15 stale audit / sister table 23 candidates / Phase L template completeness / 4-pillar v1.15 amendments / cross-tool enumeration / effort estimate / pre-coding triggers

---

## Plan summary

- Sprint: `v5.15-live-readiness`
- In-flight ship: `v5.15.5.F.4d.1.B.3` (Legacy empty-out)
- Branch: `feat/v5.15-live-readiness` (existing branch; pre-tag rollback anchor `pre-v5.15.5.F.4d.1.B.3` to be created Step 0)
- Predecessor: `v5.15.5.F.4d.1.B.2` (engine `9b62a72`)
- Total effort estimate (claimed): Phase L `~7-10h focused + ~2.5-3h amendment pre-coding` (vs v1.14 `~4-6h`); umbrella ship total `~22-32h focused` (residual line 1312)
- 1 LINCHPIN Phase L addition (Decision G + Step 1.6.8'): X-macro auto-gen CLI flag table + extensibility test pattern + Layer 5b CLI emit invariants + --help/exit-code parity + deprecation aliases
- Bug classes structurally closed: 6 (Classes 11/12/14/18/21/24) + Path γ #3 PARTIAL → MOSTLY; v1.15 adds Class 18+19+21 closures at CLI INTERFACE + TEST layers
- 23 canonical sister registries inspected (12 pre-v1.14 + 5 v1.14 + 6 v1.15 NEW)

---

## Checklist verdicts (28 checks + 4 M-discipline checks at 36-39)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | PASS | UNTOUCHED; verification gate confirms `tools/calls_graph_diff.sh verify` |
| 2 | Train-serve parity | PASS | Both Backtest_Run + EngineSharded_Run continue using same framework consumer; SOFT v1/v2 bump preserves train-serve identity |
| 3 | Surface area | PASS | Phase L touches `tools/stamp_model_cli.cpp` (NEW ~250-300 LOC) + `CMakeLists.txt:248+` + `framework-driven-cli-binary-pattern.md` v1.0→v1.1 + `cfg-derived-consumer-framework.md` v1.2→v1.3 + `tests/controller_test.cpp` (extensibility test replaces v5.14.1.B.3.E manual block); other umbrella steps unchanged from v1.14 |
| 4 | Pointer/heap lifecycle | PASS | CLI binary owns its own arg parsing; no heap on hot path; `stamp_write_for_model` already idempotent on the engine side |
| 5 | Backward compat | PASS | Decision F SOFT compat (parser dual-recognition); v1 stamps load on v2 engine; bash deprecation shim preserves operator workflow (TECH_DEBT-110) |
| 6 | Multi-threading | PASS | CLI binary is single-threaded process; no new shared state in engine surface |
| 7 | Test coverage | PASS | L4 verification expanded: round-trip + byte-identity + legacy + extensibility (X-macro walker) + Layer 5b CLI emit invariants + workflow replication (5+ scenarios) |
| 8 | Docs + invariants | PASS | 2 DESIGN_SPECs amended (framework-driven-cli v1.0→v1.1; cfg-derived-consumer v1.2→v1.3); 4 cross-refs landed; README catalog entry verified at workspace/DESIGN_SPECS/README.md:181 |
| 9 | Forward maintenance | PASS | X-macro auto-gen eliminates manual longopts[] sync (drift impossible); adding new cfg field with stamp-binding = 1 row in master FOREACH_PER_CORE_CFG_FIELD → CLI flag auto-appears; never-refactor-again acceptance criteria documented at plan body lines 168-186 |
| 10 | Rollback story | PASS | Pre-tag `pre-v5.15.5.F.4d.1.B.3` planned at Step 0; `git tag -s -a` discipline per `feedback_bump_version_per_ship` |
| 11 | Architectural sprint detection | PASS | Phase L IS an architectural sprint (cross-tool elimination via framework call); Decision G body enumerates "calls_graph_diff.sh" concerns implicitly through framework-call invariant (CLI calls `stamp_write_for_model` — single existing entry point) |
| 12 | Display ↔ execution invariant | N/A | No GUI changes in Phase L scope |
| 13 | Strategy lifecycle | N/A | No strategy code touched |
| 14 | X-macro dispatch correctness | PASS | v1.15 X-macro auto-gen has explicit variant-selection at sketch (lines 866-906); uses existing tt::cfg_parse_field<T> dispatch (no new variant); existing canonical sister at FOREACH_STAMP_BOUND_CFG emit walker; 6 registry walkers explicitly named; CI tool defer to TECH_DEBT-111 |
| 15 | ML feature change → parity snapshot | N/A | No new ML features; no FOREACH_FEATURE row changes |
| 16 | New stamp-bearing cfg → recipe doc | PASS (with caveat) | No new STAMP_BOUND_CFG_DERIVED fields added at Phase L; existing 15-field cohort (Decision D scope) does not expand at v1.15. FEATURE_LOOKUP entry at plan body line 1259 updated for Phase L cross-tool elimination |
| 17 | Model-load path changes → strict-mode test | N/A | No model-load path changes in Phase L |
| 18 | Reuse audit | PASS | v1.15 sister table verdict "6 of 6 candidates" composed/extended; zero new dispatch infrastructure (reuses existing tt::cfg_parse_field<T> + cfg_derived::parse_stamp_cfg_to_derived meta-walker) |
| 19 | Pre-existing-work audit | PASS | All 6 X-macro registries verified to exist at HEAD (FOREACH_PER_CORE_CFG_FIELD / FOREACH_GLOBAL_CFG_FIELD / FOREACH_ML_CFG_FLAG at MlCfgFlagRegistry.hpp:58 6-col / FOREACH_GATE_CFG_FLAG at GateCfgFlagRegistry.hpp:57 6-col post-Step-0.5d.a.0 / FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG + POST_CFG); stamp_write_for_model at ModelInference.hpp:1688 verified; CMake compare_scalers sister precedent at :248-251 verified; FixedPoint64.hpp exists; FPN.hpp does NOT (HIGH-3 fix correct); workspace/DESIGN_SPECS/framework-driven-cli-binary-pattern.md v1.1 + cfg-derived-consumer-framework.md v1.3 confirmed on disk |
| 20 | Future-proofness sanity | PASS | v1.15 X-macro auto-gen IS the future-proofness expansion (eliminates manual flag-sync recurrence vector; CLI inherits registry by construction); 14th-instance answer: 14th cfg field = registry row + auto-flow |
| 21 | Test count fragility | PASS | Verification gate uses `>= N` style + named-symbol patterns; extensibility test pattern is X-macro walker (auto-scaling); v5.14.1.B.3.E manual 17-field block being eliminated |
| 22 | Auto-trigger downstream re-audit | PASS | `/precoding-audit-gate` v1.14 fire already triggered v1.15 expansion; `/readiness` re-fire (this) + `/blindspot-scan` re-fire scheduled per pre-coding triggers section |
| 23 | Latency accountability | PASS | Phase L is boot/CLI/load-time only (NOT hot/slow path); explicit "HOT_PATH_CHANGELOG: NONE entry" at plan body line 1226; verification gate confirms hot path UNTOUCHED |
| 24 | Mirror-function call-sequence | PASS | CLI binary mirrors engine wire emit via framework CALL (not duplication); call-sequence is single: `stamp_write_for_model` → existing framework walker chain; no parallel implementation |
| 25 | TECH_DEBT surface scan | PASS | TECH_DEBT-110 (deprecation shim deletion) + TECH_DEBT-111 (CI defense-in-depth) explicitly opened; existing TECH_DEBT entries reviewed (101-107 carried forward; 102/104 closed at ship close) |
| 26 | (reserved) | N/A | Placeholder |
| 27 | DESIGN_SPECS pattern application | PASS | /dod-audit applied: framework-driven-cli-binary-pattern Stage 2 DRAFT v1.1 application; cfg-derived-consumer-framework v1.3 amendment; x-macro-registry-with-presence-dispatch.md § Y3 dispatch composition; autopopulate-pattern-for-production-caller-class.md composition; tt::-namespace dispatch composition |
| 28 | Test-strength audit | PASS | No assertion weakenings in v1.15 amendments; extensibility test replaces manual block with STRONGER pattern (X-macro walker validates ALL flagged rows, including future additions) |
| 29 | Mechanical citation drift | **YELLOW** | See Findings #1-#3 below — 3 stale v1.10 attribution refs at lines 1265, 1310, 1312; effort estimate residual conflict |
| 30 | Predicate contract changed | N/A | No predicate body changes |
| 31 | Wider-build verification | DEFERRED | Predecessor `.B.2` wider-build status not verified in this fire; carry forward (not v1.15-specific) |
| 36 | Sister-registry parity (M1) | PASS | All sister registries verified at HEAD column counts (FOREACH_ML_CFG_FLAG 6-col + FOREACH_GATE_CFG_FLAG 6-col post-Step-0.5d.a.0 sig migration); Decision G's 6-registry walk has metadata_flags column on all flagged registries |
| 37 | Transitional state budget (M4/B3) | PASS | v1.12 amendment annotated transitional struct-size peak ~1.1-1.5KB per struct at Step 1.6.3; v1.15 Phase L doesn't expand transitional state (CLI binary is independent process) |
| 38 | Include topology cycle (M4/B7) | PASS | `#include "../FixedPoint/FixedPoint64.hpp"` in tools/stamp_model_cli.cpp is acyclic; tools/ is leaf consumer of ML_Headers + CoreFrameworks |
| 39 | Wire-format row ordering parity (M4/B12) | PASS | v1.12 amendment annotated Step 1.6.4 row-ordering as INTENTIONAL under SOFT-bump; Phase L's CLI emit invariants test (L4 new) verifies CLI binary's canonical body satisfies SAME I1-I5 invariants (master-registry order; line-count == popcount; locale-pinned) |

**Verdict legend:** PASS (item satisfied) / YELLOW (mechanical drift, non-blocking) / DEFERRED (carried forward).

---

## v1.15 amendment scope verification

### Future-oriented-plan-template completeness (Check 30 deep dive)

All 9 required sections present:

| Section | Status | Location |
|---|---|---|
| Design space + future-oriented choice | ✓ | Decision G at line 135 (Phase L); decisions A-F preserved |
| Canonical sister registries considered | ✓ | Lines 206-247 (23 candidates total; 12 + 5 + 6 NEW v1.15) |
| Bug classes this ship closes | ✓ | Lines 250-266; v1.15 adds Class 18/19/21 at CLI INTERFACE + TEST layers (lines 257-259) |
| DESIGN_SPECs landed/amended | ✓ | Lines 270-302; 6 specs documented: framework-driven-cli v1.0→v1.1 + cfg-derived-consumer v1.2→v1.3 + canonical-sister § Temporal evolution + structural-fix § Reference implementations + wire-format Layer 7 + README catalog |
| Verification gate | ✓ | Lines 1192-1227; L4 sub-step round-trip + extensibility + Layer 5b CLI emit invariants |
| TECH_DEBT auto-write | ✓ | Lines 1230-1253; TECH_DEBT-110 + 111 NEW explicitly tracked |
| Pre-coding triggers | ⚠ STALE | Lines 1263-1281 — see Finding #1 (item 1 says "v1.10" should be "v1.15") |
| Operator migration impact | ✓ | Lines 343-371; deprecation shim + flag interface continuity per `feedback_surface_operator_migration_path_proactively` |
| Novel alternative consideration | ✓ | Lines 375-387 (α-ζ table for Decision F; Decision G inherits framework-driven-cli-binary-pattern α-ζ enumeration from DESIGN_SPEC body) |

### 4-pillar self-audit verification for v1.15 amendments (Checks 31-33)

| Pillar | Coverage | Verdict |
|---|---|---|
| DESIGN_SPECS cross-check | autopopulate-pattern + X-macro-registry-with-presence-dispatch + cross-walker-struct-field-uniqueness + tt::-dispatch + structural-fix-preferred + canonical-sister-extension-discipline all explicitly cited in v1.15 sister table or DESIGN_SPECs landed section | PASS |
| Anti-pattern catalog | Class 18 (mirror) / 19 (hardcoded names) / 21 (parallel descriptors) / 22 (runtime gating scattered) cited at WIRE EMIT + CLI INTERFACE + TEST layers; NO new anti-pattern introduced by X-macro auto-gen (verified by DESIGN_SPEC catalog already has X-macro-registry pattern as ACTIVE Stage 3+; new application is Stage 4 cohort growth, not pattern violation) | PASS |
| Operator impact | Deprecation shim (Step L5) + flag interface continuity + retention period (TECH_DEBT-110) + kebab-case alias deferral decision (L2 coding-time) + bash-stamped model forward-compat per Decision F | PASS |
| Novel alternative | DESIGN_SPEC α-ζ enumeration at framework-driven-cli-binary-pattern.md covers constexpr-generated longopts[] / runtime construction / direct X-macro auto-gen — α-ζ verdict ACCEPTED ZETA (X-macro auto-gen with tt:: dispatch). v1.15 sister table also covers compose vs no-fold decision for compare_scalers (NO-FOLD, scale-mismatch) | PASS |

### Cross-tool emit-site enumeration completeness (Check 37/M2)

Verified comprehensively at workspace: `grep -lE "inference_cfg_|stamp_format_version|bandit_algorithm|trained_on_iso" tools/*.{sh,py,cpp}` returns ONE site only — `tools/stamp_model.sh`. No additional bash diagnostic scripts, Python tools, or C++ tools mirror wire-format keys. M2 enumeration complete at v1.10; v1.15 inherits via Phase L structural elimination at the sole cross-tool surface.

### Effort estimate verification (Check 7 deep dive)

Phase L breakdown vs claim of `~7-10h focused`:

| Sub-step | Claimed | Verified scope |
|---|---|---|
| L1 DESIGN_SPEC v1.0→v1.1 amendment | ~30 min | DONE — verified on disk at workspace; lines 142 + 199 + 403 + 489 + 609 sections present |
| L2 CLI binary | ~3-4h | ~250-300 LOC C++ including X-macro auto-gen + tt:: dispatch + getopt_long loop + apply-args-to-cfg/inf + locale pin; sketch at lines 866-946 |
| L3 CMake 4-line | ~5 min | Confirmed compare_scalers sister at CMakeLists.txt:248-251 (verified at HEAD) |
| L4 verification tests | ~2-3h | ~150-250 LOC: round-trip + byte-identity + legacy + extensibility (X-macro walker; replaces v5.14.1.B.3.E manual ~150 LOC block) + Layer 5b CLI emit invariants + workflow replication |
| L5 deprecation shim | ~5 min | 1-line `exec` redirect at tools/stamp_model.sh body replacement |
| L6 cross-ref updates | ~30 min | 4 sister specs already done at workspace (verified: canonical-sister-extension :285+289; structural-fix-preferred :187; cfg-derived-consumer-framework :354; README.md :181); residual workspace cross-refs |
| L7 cfg-derived-consumer v1.2→v1.3 | ~45 min | DONE — verified at workspace; § Extensibility test pattern at line 270 |
| L8 TECH_DEBT-111 entry | ~10 min | Tracked at plan body line 1252 |

**Total verified:** ~7-10h focused estimate is REASONABLE. ~2.5-3h amendment pre-coding work (L1 + L7 DESIGN_SPECs + L6 cross-refs) already DONE — confirmed on disk.

---

## Top 5 findings ordered by severity

### Finding #1 (MED — citation drift) — Pre-coding triggers stale at v1.10 reference

**Location:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md:1265`

```
1. ✓ Plan body draft complete (this document v1.10)
```

Should now say `v1.15` post-v1.15 amendment. Similar issue at line 1273 ("v1.2 → v1.3 → ... → v1.9 → v1.10 (10 iterations)") which mechanically should track up to v1.15 (`v1.2 → ... → v1.15 (15 iterations)`).

**Severity:** MED — non-blocking but introduces compaction-degraded handoff hazard per `feedback_compaction_degrades_treat_handoffs_as_hints`.

**Fix:** Mechanical replace_all: `v1.10 → v1.15` at line 1265; update iteration count at line 1273.

### Finding #2 (MED — citation drift) — Plan body closure stale at v1.10 DRAFT

**Location:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md:1310`

```
**End of `.B.3` plan body v1.10 DRAFT.** Promoted from v1.9 via Batch 2 RE-SWEEP ...
```

This closure paragraph describes v1.10 lineage; v1.15 expanded scope substantially. Promotion narrative is stale — v1.10 promoted from v1.9 via Batch 2 RE-SWEEP is HISTORICALLY accurate but does NOT mention v1.11-v1.15 evolution (Session D discoveries + Meta-gap M4 codification + Phase L v1.14 amendment + Phase L v1.15 expansion).

**Severity:** MED — closure paragraph is load-bearing for cold-pickup; reader may incorrectly think plan ends at v1.10.

**Fix:** Rewrite closure paragraph to reflect v1.15 lineage: "End of `.B.3` plan body v1.15 DRAFT. v1.15 expands Phase L (Decision G + Step 1.6.8') per /precoding-audit-gate 6-audit fire against v1.14 — full Tier B closure for cfg-stamp-binding surface via X-macro auto-gen CLI flag table + extensibility test pattern + Layer 5b CLI emit invariants. Prior lineage: v1.14 added Phase L Decision G; v1.12 codified Meta-gap M4 mid-coding; v1.11 Session D discoveries; v1.10 closed M1+M2+M3 meta-gaps; v1.2 first canonical NEW plan body. **READY for operator final greenlight + pre-coding tag.**"

### Finding #3 (MED — effort estimate conflict) — Trailing effort estimate residual at v1.10

**Location:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md:1312`

```
Effort estimate: **~22-32h focused** (v1.10 added Step 0.5d.a.0 ~30 min sister-registry sig migration + Step 1.6.8 expansion ~15 min over v1.9; net ~45 min over v1.9 estimate).
```

This trailing summary describes umbrella ship effort at v1.10 (`~22-32h`); v1.15 Phase L expansion adds `+3-4h` per status header line 8 (Phase L `~7-10h focused + ~2.5-3h amendment pre-coding`). Trailing estimate has not been updated to reflect Phase L v1.15 expansion.

**Severity:** MED — effort estimate is operator-visible cold-pickup input; conflict with status header creates confusion.

**Fix:** Update trailing summary to: `Effort estimate: ~26-39h focused (umbrella ship; v1.15 Phase L expansion adds ~3-4h over v1.14 v1.10 baseline; Phase L alone ~7-10h focused + ~2.5-3h amendment pre-coding already done).` Also enumerate "v1.11 / v1.12 / v1.14 / v1.15" amendment deltas explicitly for transparency.

### Finding #4 (LOW — wording inconsistency) — Sister table verdict says "5 DELETE" but full table also has "DELETE entirely" rows

**Location:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md:246`

```
**Verdict (UPDATED v1.15):** 23 candidates considered total ... 8 EXTEND/COMPOSE; 5 DELETE; 1 EXTEND PARTIAL ...
```

Counting verdict cells: 12-row pre-v1.14 table has `EXTEND, EXTEND, DELETE, DELETE, DELETE, NO-FOLD, EXTEND PARTIAL, EXTEND, EXTEND, DELETE, MIGRATE, INLINE MERGE` (12 cells). v1.14 5-row: `NO-FOLD, NO-FOLD, EXTEND, EXTEND, NEW DRAFT` (5). v1.15 6-row: `COMPOSE, COMPOSE, COMPOSE, NO-FOLD, COMPOSE, EXTEND` (6). Total 23 cells; counting DELETE: 4 (rows 3, 4, 5, 10 of pre-v1.14 table). Summary says 5 — likely a +1 counting drift.

**Severity:** LOW — informational only; doesn't block coding.

**Fix:** Mechanical recount; adjust to `4 DELETE` OR `5 DELETE` after re-verifying. Cross-check: Decision D 15-entry scope is itself partial-DELETE coupled at registry deletion — could be counted as +1.

### Finding #5 (LOW — wording consistency) — CLI flag naming convention reconciliation deferred to L2

**Location:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md:948`

```
**Naming reconciliation needed at L2 coding:** either (a) accept BOTH forms ... (b) auto-convert ... (c) standardize on snake everywhere. Decision deferred to L2 coding-time per /readiness Check 30 operator-impact discipline. Lean: (c) snake_case CLI flags matching registry...
```

L2 deferral is consistent with `feedback_plan_right_not_fast` (planning depth produces right answers; some decisions belong at coding-time when concrete data is available). However the related deprecation alias scope at lines 956-957 also defers to L2, which means TWO coding-time L2 sub-decisions (CLI naming + deprecation alias scope). If both decisions interact, defer-to-L2 is the right place; but a brief note acknowledging the interaction would clarify cold-pickup intent.

**Severity:** LOW — judgment-call; could be left as-is if operator prefers L2 freshness.

**Fix:** Optional 1-line annotation at line 948: "Note: deprecation alias scope (lines 956-957) interacts with this decision; both resolve at L2 coding-time atomically."

---

## Cold-pickup completeness verdict for v1.15 amendment

**Cold-pickup score: 9/10 GREEN**

| Item | Status | Notes |
|---|---|---|
| C.1 Branch state | ✓ | `feat/v5.15-live-readiness` named at line 3 |
| C.2 Phase execution order | ✓ | Lines 1140-1188 BUILD-FORCED A-K phases enumerated; L1-L8 sub-steps in Phase H |
| C.3 First concrete move | ✓ | Step 0 + 0.5d.a.0 (sister-registry sig migration) named explicitly |
| C.4 Function/constructor names | ✓ | `stamp_write_for_model` (verified at ModelInference.hpp:1688), `tt::cfg_parse_field<T>`, `cfg_derived::parse_stamp_cfg_to_derived` (verified at CfgGateRegistry.hpp:421) |
| C.5 File:line refs for tests/baselines | ✓ | v5.14.1.B.3.E block at controller_test.cpp:4039 (verified); Layer 5b at wire_format_invariants.hpp (verified); compare_scalers CMake at :248-251 (verified) |
| C.6 Stale-claim audit | ⚠ | 3 stale v1.10 refs (Findings #1-#3) |
| C.7 Effort reconciles with file deltas | ✓ | Phase L ~7-10h reasonable per L1-L8 breakdown verification above |
| C.8 Source-audit refs | ✓ | 6 audit reports + 5 RE-SWEEP audit reports + fresh-audit synthesis at workspace plan_checks/ all cited |
| C.9 Predecessor/dependent paths | ✓ | Predecessor `v5.15.5.F.4d.1.B.2` at engine `9b62a72`; successor `v5.15.5.F.4d.1.C`; sub-master at `subplans/2026-05-16-v5.15.5.F.4d.1-thread-a-framework-full.md` v1.3 |
| C.10 Tag names locked | ✓ | `v5.15.5.F.4d.1.B.3` with rollback anchor `pre-v5.15.5.F.4d.1.B.3` |

Item C.6 stale-claim audit is the YELLOW driver. Findings #1-#3 are mechanical citation drift; non-blocking but should be addressed before final greenlight.

---

## Pre-coding triggers section completeness (Check 7 specific verification)

Pre-coding triggers section at lines 1263-1281 enumerates 14 items. v1.15-specific verification:

- ✓ Item 1 references `/precoding-audit-gate` 6-audit fire (v1.14 → v1.15 amendment trigger) per status header — TRIGGERED
- ✓ Item 2.5 RE-SWEEP audit synthesis at workspace — DONE
- ✓ Items 3 + 3.5 DESIGN_SPEC Stage 2 DRAFT on disk — VERIFIED (framework-driven-cli v1.1 + cfg-derived-consumer v1.3 at workspace)
- ✓ Items 4-10 SHAPE audit + 4-pillar self-audit — DONE per Batch 1/2 syntheses + v1.15 fresh audit synthesis
- ⚠ Item 11 operator final greenlight — PENDING (this audit re-fire is the gate)
- ⚠ Item 12 pre-tag rollback anchor — PENDING (Step 0 of coding)
- ⚠ Item 13 CI checks PASS at HEAD — verified earlier sessions; re-verify at coding start

**Pre-coding triggers** section reflects audit firings adequately. Operator greenlight is the only remaining gate.

---

## Recommendations

### Must fix before coding (mechanical; ~10 min)

1. **Finding #1 fix** — Replace `v1.10` → `v1.15` at line 1265; update iteration count at line 1273.
2. **Finding #2 fix** — Rewrite closure paragraph at line 1310 to reflect v1.15 lineage.
3. **Finding #3 fix** — Update trailing effort estimate at line 1312 to reflect Phase L v1.15 expansion.

### Worth fixing during coding (optional polish)

4. Finding #4 sister-table verdict recount.
5. Finding #5 optional cross-ref annotation at L2 naming decision.

### Acceptable risk (don't block)

- Wider-build verification (Check 31) deferred to predecessor `.B.2` postmortem review; not v1.15-specific.

---

## Verdict: **GREEN-WITH-MECHANICAL-AMENDMENTS**

Phase L v1.15 coding can start once Findings #1-#3 are addressed (~10 min mechanical edits). All architectural decisions sound; all DESIGN_SPECs on disk; sister table comprehensive (23 candidates); 4-pillar self-audit PASS; cross-tool enumeration complete; effort estimate reasonable.

The 3 stale-v1.10 references at lines 1265, 1310, 1312 are MECHANICAL CITATION DRIFT (Check 29 class) — exactly the pattern Caramel codified as `feedback_compaction_degrades_treat_handoffs_as_hints`. Fix at plan body, then operator final greenlight, then Step 0 pre-tag, then Phase L coding.

**Effort to GREEN:** ~10 min mechanical plan-body amendment.

**v1.15-specific scope (X-macro auto-gen + extensibility test + Layer 5b CLI emit invariants + --help/exit-code parity + deprecation aliases) is INTERNALLY COMPLETE.** No structural gaps surfaced by this fire.

---

**End of /readiness re-fire report.**
