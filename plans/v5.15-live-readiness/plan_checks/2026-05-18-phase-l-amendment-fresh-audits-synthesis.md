# Fresh-audits synthesis — Phase L amendment to `.B.3`

**Date:** 2026-05-18
**Plan audited:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` v1.14 (Decision G + Step 1.6.8' Phase L)
**Engine HEAD:** `3d27512` (WIP-checkpoint 6)
**Audit set fired:** `parity,trace,readiness,merge,dod,blindspot` (6 audits in parallel via `/precoding-audit-gate` Layer-1 orchestrator)

---

## Combined verdict: **RED → YELLOW after amendments** (2 blocking gaps; ~45 min amendment punch list before coding)

| Audit | Verdict | Critical findings |
|---|---|---|
| `/parity-check` | GREEN | 2 MEDIUM + 1 LOW; wire-format byte preservation intact; cross-tool emit-site enumeration complete |
| `/trace-deps` | **RED** | **1 RED: 9 missing CLI flags (XGB + build_flags_hash)**; 2 YELLOW (spec stale include path; commit-msg root-cause drift) |
| `/readiness` | GREEN | 4 stale doc sites (non-blocking ~20 min polish); 9/9 future-oriented sections present for Phase L |
| `/merge-scan` | GREEN | 3 non-blocking advisories (Threads/ssl link + build pattern + optional --cfg-path) |
| `/dod-audit` | YELLOW | 2 HIGH (missing Audit detection section; 3 sister specs missing forward-refs) + 2 MED (README catalog; Stage 5 sharpening) |
| `/blindspot-scan` | YELLOW | **1 SILENT-RISK CRITICAL B8 (flag gap; convergent with /trace-deps)** + **1 LOAD-BEARING-LOUD B11 (CMakeLists incomplete; convergent with /merge-scan)** + 3 non-blocking |

---

## CRITICAL (blocking; convergent across 2+ audits)

### CRIT-1 — Phase L L2 missing 9 CLI flags (caught by `/trace-deps` + `/blindspot-scan` independently)

**Plan body line 803** lists 23 CLI flags for `tools/stamp_model_cli.cpp`. Actual `tools/stamp_model.sh:109-147` getopt loop accepts **32-33 flags**. Missing 9:

- `--xgb-max-depth` / `--xgb-learning-rate` / `--xgb-n-estimators` / `--xgb-subsample` / `--xgb-colsample-bytree` / `--xgb-min-child-weight` / `--xgb-seed` / `--xgb-tree-method` (8 XGBoost hyperparameters)
- `--build-flags-hash` (1 architectural)

All 9 emit to HMAC-signed canonical wire body via `FOREACH_STAMP_BOUND_MODEL_CONST` (verified at `StampBoundModelConstRegistry.hpp:324-343` + line 253). Without these flags:
- Operator's existing XGBoost-trained-model stamping workflow CANNOT byte-identity round-trip
- L4 verification gate FAILS (round-trip + byte-identity tests don't cover these fields)
- Decision F SOFT compat goal BREAKS (bash-stamped XGB models verify on engine; CLI-stamped XGB models can't round-trip)
- `feedback_surface_operator_migration_path_proactively` violated (operator scripts hardcoding `--xgb-*` flags break)

**Required amendment:** Extend Phase L Step L2 flag list 23 → 33. Effort: ~10 min plan body amendment + ~20 min CLI code expansion at coding time.

**Severity:** BLOCKING — must amend before Phase L coding starts. Per `feedback_motivated_collaborator_for_caramel`: defer is rejected (breaks operator continuity).

### CRIT-2 — Phase L L3 CMakeLists incomplete (caught by `/blindspot-scan` + `/merge-scan` independently)

**Plan body line 805** specs only 1 CMake line: `add_executable(stamp_model_cli tools/stamp_model_cli.cpp)`. Sister precedent `compare_scalers` at `CMakeLists.txt:248-251` requires **4 lines**:

```cmake
add_executable(stamp_model_cli tools/stamp_model_cli.cpp)
target_compile_options(stamp_model_cli PRIVATE -O2 -march=native)
target_include_directories(stamp_model_cli PRIVATE ${CMAKE_SOURCE_DIR}/..)
target_link_libraries(stamp_model_cli PRIVATE ssl crypto Threads::Threads)
```

Without `ssl crypto` linkage, HMAC fails to link. Without `Threads::Threads`, framework's pthread inclusion fails to link. Without `-march=native`, FPN<F> codegen may differ from engine.

**Required amendment:** Extend Phase L Step L3 to spell out the 4 CMake lines explicitly. Effort: ~5 min plan body amendment.

**Severity:** BLOCKING — partial spec fails link; cannot complete Phase L coding without.

---

## HIGH (non-blocking but should resolve before ship close)

### HIGH-1 — NEW DESIGN_SPEC `framework-driven-cli-binary-pattern.md` missing `## Audit detection` section (caught by `/dod-audit`)

Per `pattern-codification-lifecycle.md:71`, Stage 2 specs MUST have `## Audit detection` section so `/dod-audit` can auto-detect new applications. Sister Stage 2 specs (`branchless-math-kernel-pattern.md:278` + `struct-padding-determinism-pattern.md:257`) both have it.

**Required amendment:** Add `## Audit detection` section to `framework-driven-cli-binary-pattern.md` with grep signatures for detecting candidate cross-tool surfaces (e.g., `tools/*.sh` files mirroring FOREACH_PER_CORE_CFG_FIELD wire emit + bash scripts with `stamp_format_version=` literals). Effort: ~10 min, ~30-50 lines.

### HIGH-2 — Forward refs to NEW spec missing in 3 sister specs (caught by `/dod-audit`)

Only `wire-format-byte-preservation-discipline.md` Layer 7 amendment landed (✓). Missing forward-refs:
- `canonical-sister-extension-discipline.md` (parent discipline)
- `cfg-derived-consumer-framework.md` (composes — CLI is new consumer)
- `structural-fix-preferred-decision-framework.md` (4× recurrence applied)

**Required amendment:** Add single-sentence forward-ref in each of the 3 sister specs pointing to `framework-driven-cli-binary-pattern.md` Stage 2 DRAFT. Effort: ~5 min total.

### HIGH-3 — DESIGN_SPEC stale include path (caught by `/trace-deps`)

`framework-driven-cli-binary-pattern.md:142` cites `#include "../FixedPoint/FPN.hpp"`. Actual file at HEAD is `FixedPoint/FixedPointN.hpp` (need to verify exact filename).

**Required amendment:** Fix include path in DESIGN_SPEC. Effort: ~2 min (after verifying actual filename via `ls FixedPoint/`).

---

## MEDIUM (polish; ~20 min batch fix; can land in Phase L coding commit or separate cleanup commit)

### MED-1 — 4 stale documentation sites in plan body (caught by `/readiness`)

- Line 8 Status header: "DRAFT v1.12" → "DRAFT v1.14 with Decision G + Phase L summary"
- Line 1034 verification gate: describes superseded v1.10 bash-patches → should describe Phase L verification (CLI builds + L4 tests + deprecation shim + DESIGN_SPEC Stage 3 + TECH_DEBT-110)
- Line 1083 FEATURE_LOOKUP entry: "Cross-tool sync (v1.10 per Layer 7)" → "Cross-tool structural elimination (v1.14 per Phase L)"
- Line 1087 pre-coding triggers heading: "DRAFT v1.10 → ACTIVE coding" → "DRAFT v1.14 → ACTIVE coding"

### MED-2 — README.md catalog entry not added (caught by `/dod-audit`)

Per future-oriented-plan-template Step 6 deliverable. Add `framework-driven-cli-binary-pattern.md` to `DESIGN_SPECS/README.md` under "Framework discipline patterns" subsection (line 163). Effort: ~5 min.

### MED-3 — WIP-checkpoint 6 commit-msg root-cause analysis questioned (caught by `/trace-deps`)

Commit `3d27512` attributes 14 transitional test failures to "legacy emit walker FPN<F> in %.17g variadic context = garbage bytes". `/trace-deps` notes:

- Legacy walker at `ModelInference.hpp:1817-1823` uses `inf->name` (passed by caller)
- `inf->name` post-Step-1.6.3 struct-gen is FPN<F>
- BUT `StampBoundCfgRegistry.hpp:112-172` get_value column reads `FPN_ToDouble(cfg.X)` — that's read from CFG, not inf
- Which path actually executes depends on framework dispatch shape

Real probable root cause is either:
- (a) FPN<F> variadic-arg behavior (operator double() invocation or undefined behavior depending on FPN definition)
- (b) Round-trip precision (FPN→double→text→double→FPN not bytewise-identity)
- (c) `has_*` flag through new struct shape

**Required action:** Diagnostic at Step 1.6.4 coding time (when legacy walker is eliminated; 14 failures will resolve or shift). Note correction in plan body Coding-time discoveries section. **NOT a Phase L blocker.**

### MED-4 — `/parity-check` non-blocking refinements

- M2 — Plan body L3 build system spec underspecifies SSL/crypto linkage (subsumed by CRIT-2)
- M3 — Plan body L4 byte-identity verification scope unclear (v1 vs v2 path coverage) — clarify test design
- L1 — Phase L L2 `--feature-mask` framework path coverage (verify `StampInferenceCfgInputs::feature_mask` field exists)

---

## LOW (advisory; informational; no action required)

- `/merge-scan` L3 advisory: optional `--cfg-path` flag (operator-additive; defer to first canonical coding)
- `/blindspot-scan` B7: transitive include depth annotation (build time +5-15s estimated; acceptable; annotate)
- `/blindspot-scan` B8 sub-finding: spell out `StampInferenceCfgInputs` population pattern in plan body L2
- `/dod-audit` M-2: Stage 5 promotion sharpening (low-probability 2nd canonical near-term)

---

## Step 1.6.5b walker refactor (LANDED at WIP-checkpoint 5) — ALL CLEAN per `/blindspot-scan`

12-pillar implementation-detail audit on the LANDED walker refactor confirms:
- B7 verified (no cycle; FOREACH_STAMP_BOUND_DERIVED_COHORT enrolled at `CfgGateRegistry.hpp:185-231`)
- B11 verified (template-context expansion sites at lines 325/398/500/571)
- B12 verified (single-sourced cohort order)
- B2 verified (uniqueness CI tool PASSes at HEAD)
- Class 18/21 sister-consumer-asymmetric-coverage closure structurally enforced

No regressions from WIP-checkpoint 5 detected.

---

## Cross-tool emit-site enumeration verification — COMPLETE per `/parity-check` + `/trace-deps`

Comprehensive grep across `tools/`, `scripts/`, `OPS/`, `experiments/`, `tests/` confirmed `tools/stamp_model.sh` is the SOLE bash/python script emitting wire-format keys (`stamp_format_version`, `inference_cfg_*`, `model_sha256=`, HMAC body). Other bash scripts (`calls_graph_diff.sh`, `compare_scalers.sh`, `validate_feature_mask.sh`, `gen_code_map.sh`) are diagnostic / read-side / static-analysis — none mirror engine emit; none require Phase L treatment.

Phase L scope at this surface is COMPLETE. No sister tool migrations missed.

---

## Recommended amendment punch list (ordered by blocking severity)

| # | Amendment | Where | Effort | Blocking? |
|---|---|---|---|---|
| 1 | Extend Phase L Step L2 CLI flag list 23 → 33 (add 9 XGB + build_flags_hash) | Plan body Step 1.6.8' L2 | ~10 min | **BLOCKING** |
| 2 | Spec 4-line CMakeLists pattern (target_compile_options + target_include_directories + target_link_libraries) | Plan body Step 1.6.8' L3 | ~5 min | **BLOCKING** |
| 3 | Add `## Audit detection` section to `framework-driven-cli-binary-pattern.md` | Workspace DESIGN_SPECS/ | ~10 min | HIGH (non-blocking) |
| 4 | Add forward-refs in 3 sister specs (canonical-sister-extension + cfg-derived-consumer + structural-fix-preferred) | Workspace DESIGN_SPECS/ | ~5 min | HIGH (non-blocking) |
| 5 | Fix stale include path `FixedPoint/FPN.hpp` → actual filename | Workspace DESIGN_SPEC line 142 | ~2 min | HIGH (non-blocking) |
| 6 | Fix 4 stale documentation sites (status header / verification gate / FEATURE_LOOKUP / pre-coding triggers heading) | Plan body lines 8 / 1034 / 1083 / 1087 | ~10 min | MED |
| 7 | Add catalog entry to `DESIGN_SPECS/README.md` | Workspace README.md | ~5 min | MED |
| 8 | Annotate transitive include depth in Phase L L3 | Plan body Step 1.6.8' L3 | ~3 min | LOW (advisory) |
| 9 | Spell out `StampInferenceCfgInputs` population pattern in L2 | Plan body Step 1.6.8' L2 | ~5 min | LOW (advisory) |
| 10 | Note WIP-checkpoint 6 root-cause correction (defer diagnostic to Step 1.6.4) | Plan body Coding-time discoveries section | ~5 min | LOW (informational) |

**Total: ~60 min amendment work** before substantive Phase L coding starts (BLOCKING items 1-2 = 15 min; HIGH 3-5 = 17 min; MED + LOW = 28 min). Per `feedback_plan_right_not_fast`: plan body amendment is the right work; don't compress for speed.

---

## Cold-pickup completeness verdict: 9/10 GREEN

A fresh session would orient on Phase L within ~5 min via Decision G (line 131) + canonical sister table (line 188-198) + L1-L6 sub-steps (line 795-842). After CRIT-1 + CRIT-2 amendments land, cold-pickup completeness improves to 10/10.

---

## Recommended path forward

1. **Operator triage** (this consult per `feedback_consult_on_audit_findings`)
2. **If greenlit**: amend punch list items 1-7 (~37 min focused; items 8-10 are advisory)
3. **Optional `/blindspot-scan` re-fire** if amendments are substantial (CRIT-1 flag list expansion may surface secondary B8 concerns at the XGB cfg field set)
4. **`/sync-workspace`** to back up amended plan body + DESIGN_SPEC + sister-spec amendments off-machine
5. **Then code through full sequence**: Step 1.6.2 → Step 0.5d.b/c → Step 1.5 → Step 1.6.4 + 1.6.7 + 1.6.8' Phase L (same commit) → Step 1.6.6 → Step 2 → Steps 3-9 ship close

---

## Anti-patterns avoided

- ✅ No auto-proceed past audit findings (per `feedback_consult_on_audit_findings`)
- ✅ Surfacing full menu (CRIT/HIGH/MED/LOW with effort estimates) per `feedback_proportionate_response_to_audit_findings`
- ✅ Convergent findings (CRIT-1 + CRIT-2) caught by independent subagents — strong signal
- ✅ Audit gate fired BEFORE coding (per `feedback_plan_right_not_fast` + audit-driven-pre-coding-gate.md)

---

**End of synthesis.** Awaiting operator triage decision.
