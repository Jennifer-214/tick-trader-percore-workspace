# /blindspot-scan report — Phase L (v1.14 NEW amendment) — 2026-05-18

**Plan:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md`
**Scope:** Phase L (Decision G) — framework-driven C++ CLI binary `tools/stamp_model_cli.cpp` replacing `tools/stamp_model.sh`
**Verdict:** **YELLOW-with-amendments** — 1 SILENT-RISK (B8 flag-set incompleteness; CRITICAL) + 1 GUARDED-BY-BUILD (B11 build system entry omission) + 1 LOAD-BEARING-LOUD (B7 include topology depth)
**Engine HEAD:** `3d27512` (WIP-checkpoint 6)
**Fires after:** SHAPE audits returned GREEN/YELLOW at v1.14 plan body lock (parity-check + accounting-audit + readiness)

---

## Summary

- Pillars fired: 12 (all)
- GUARDED-BY-BUILD: 5 (B5, B6, B7, B10, B11)
- SILENT-RISK: 1 (B8 — flag-set incompleteness)
- LOAD-BEARING-LOUD: 1 (B11 — build.sh entry)
- IRRELEVANT: 3 (B1, B2, B4)
- N-A: 2 (B3, B9, B12)

---

## Per-pillar verdicts

| Pillar | Verdict | Finding | Action |
|---|---|---|---|
| B1 — Type-change cascade | **IRRELEVANT** | Phase L doesn't shift struct field types; CLI assigns CLI flag values (mostly `double`/`int`/`const char*`) to `StampInferenceCfgInputs` + `ControllerConfig<64>` whose types are already established at HEAD. Sister-site Step 1.6.3 owns the FPN<F> migration. | None at Phase L scope |
| B2 — Field-name collision | **IRRELEVANT** | Phase L doesn't extend struct-gen registry coverage. Plan body B2 risk lives at Step 1.6.3 (already addressed via H18 SIDECAR EXCLUSION). Phase L's CLI flag namespace is independent (operator-facing `--feature-mask`, not C++ struct field). | None |
| B3 — Transitional state coexistence | **N-A** (annotated by plan) | Deprecation shim retention 1-2 ship cycles tracked at TECH_DEBT-110. Bash shim is 1-line `exec` to `build/stamp_model_cli`. Plan body L5 annotates target ship + trigger. No struct-size growth (orthogonal concern). | None |
| B4 — Surface G applicability | **IRRELEVANT** | Phase L doesn't change `has_<name>` semantics; CLI inherits from framework via `StampInferenceCfgInputs.has_flags`. | None |
| B5 — Compile-time scaling | **GUARDED-BY-BUILD** | New target `stamp_model_cli` adds ~1 translation unit pulling `ControllerConfig.hpp` + `ModelInference.hpp` + entire framework include chain. Same scale as `controller_test` (already compiles). ~150-200 LOC binary; trivial. | None |
| B6 — STORAGE_T variant coverage | **GUARDED-BY-BUILD** | Phase L doesn't extend STORAGE_T; CLI uses already-covered tt:: family via framework call. | None |
| B7 — Include topology cycle | **GUARDED-BY-BUILD (LOAD-BEARING)** | New file `tools/stamp_model_cli.cpp` needs to include `../ML_Headers/ModelInference.hpp` which transitively pulls **deep include chain** (CfgGateRegistry → CfgFieldRegistry → ControllerConfig → Limits → FixedPointN → LinearRegression3X → ConfidenceScore → LifecycleCfgFlagRegistry → GateCfgFlagRegistry → MlCfgFlagRegistry → BanditAlgorithmRegistry → BarrierBlendModeRegistry → RiskCfgFlagRegistry → BuildFlags + simdjson + RollingStats). Verified at HEAD: no reverse-edge from MemHeaders/ → tools/. `compare_scalers.cpp` sister precedent uses `../ML_Headers/FeatureStandardizer.hpp` + `../ML_Headers/FeatureRegistry.hpp` (shallower chain). Phase L will pull MUCH wider; compile time +5-15s estimated (vs compare_scalers ~3s baseline). Recoverable; no cycle introduced. | Pre-coding NOTE: build time for `stamp_model_cli` ≥ controller_test scale; acceptable |
| B8 — Type-sensitive consumer at CLI flag → struct field layer | **SILENT-RISK** (CRITICAL) | **Plan body L2's flag list is INCOMPLETE.** Bash script's `getopt` loop has 33 unique `--*` flags (verified by `grep -oP '\-\-[a-z][a-z-]+' tools/stamp_model.sh`); plan body L2 enumerates 23. **MISSING 10 flags ALL of which emit to canonical wire body**: `--xgb-max-depth`, `--xgb-learning-rate`, `--xgb-n-estimators`, `--xgb-subsample`, `--xgb-colsample-bytree`, `--xgb-min-child-weight`, `--xgb-seed`, `--xgb-tree-method`, `--build-flags-hash`, `--help` (last one cosmetic). Bash script lines 293-326 emit `xgb_max_depth` / `xgb_learning_rate` / `xgb_n_estimators` / `xgb_subsample` / `xgb_colsample_bytree` / `xgb_min_child_weight` / `xgb_seed` / `xgb_tree_method` + `build_flags_hash` keys into the HMAC-signed canonical body. Framework's `StampInferenceCfgInputs` IS populated from `FOREACH_STAMP_BOUND_MODEL_CONST` which DOES include these (verified at `StampBoundModelConstRegistry.hpp:324-343` — `xgb_max_depth` ... `xgb_seed` + `build_flags_hash` standalone). Without CLI flag mapping, operator CANNOT reproduce existing bash workflow byte-for-byte → fails L4 byte-identity verification test + Decision F SOFT compat goal. **B8 violates `feedback_surface_operator_migration_path_proactively` — operator workflow continuity goal broken at v1.14 plan body**. | **Plan body amendment: extend L2 flag list to 33 flags** (or document explicit deferral for XGB hyperparam sub-set with cross-ref to TECH_DEBT-NEW for that sub-cohort). Required before Phase L coding starts. |
| B9 — Audit claim → evidence chain | **N-A** (verified) | Plan body's "6+ recurrence count" claim verified by `grep "^# v5\." tools/stamp_model.sh` → 7 dated entries (v5.2.3 / v5.8.8 / v5.9.3b / v5.9.4a / v5.9.5c / v5.9.5h / v5.11.18a). Claim is accurate; plan body cites correctly. Bash script header line 12 itself says "Phase 2 (v5.3.x?) replaces this with tools/stamp_model.cpp" — original author flagged the structural fix 3+ major versions ago. | None |
| B10 — Struct layout drift | **IRRELEVANT** | Phase L doesn't introduce new struct in byte-equivalence context. CLI populates existing `StampInferenceCfgInputs` (orthogonal to wire body emit). Wire body is byte-equivalence input, NOT the struct itself. H12 enforcement lives at framework side (already in place). | None |
| B11 — Build system entry (relabeled — context-dependent C++ doesn't apply at Phase L) | **GUARDED-BY-BUILD (LOAD-BEARING)** | Plan body L3 says "Add `add_executable(stamp_model_cli tools/stamp_model_cli.cpp)` to `CMakeLists.txt`". **Pattern match against `compare_scalers` precedent at CMakeLists.txt:248-251** requires 4 lines minimum: `add_executable` + `target_compile_options` + `target_include_directories` + `target_link_libraries`. `compare_scalers` uses `-O2 -march=native`; Phase L should match (engine baseline). **Plan body L3 omits the 3 supporting lines**. **Additionally: plan body doesn't update `build.sh`** — `compare_scalers` is built implicitly by `build_engine()` since it's part of the default `cmake --build` sweep (not target-restricted). Phase L's `stamp_model_cli` will inherit same behavior (built in `build/` dir when `./build.sh` runs `cmake --build build` without `--target` restriction). **Verify: confirm at coding time that no `--target engine` restriction filters out `stamp_model_cli`** (lines 100, 121, 143, 157, 168, 192, 206, 247 in build.sh) — `build_engine` uses `cmake --build build -j"$JOBS"` (no target = builds all). PASS by default. Linker needs `ssl crypto` (HMAC via openssl/hmac.h — verified at HmacSha256.hpp:28-29) + `pthread` (transitive from framework). | Pre-coding amendment: spec the 4-line CMakeLists pattern explicitly + verify build.sh inheritance + spell out linker libs (ssl crypto pthread) |
| B12 — Cross-registry row ordering | **N-A** (Phase L inherits from framework) | CLI's wire emit happens via `stamp_write_for_model` framework call (single emit walker; same as engine in-process). NO parallel emit path at CLI → row order is structurally identical to engine. **This IS the core structural-fix property of Phase L** — eliminates B12 surface at cross-tool boundary. Layer 5b structural invariants tests at `tests/wire_format_invariants.hpp` I1-I5 apply to the framework emit path; CLI inherits validation transitively. | None at Phase L scope |

---

## Step 1.6.5b walker refactor (LANDED at WIP-checkpoint 5) implementation-detail audit

(Out-of-Phase-L but requested in audit scope.)

- **B7 include cycle:** PASS — `CfgGateRegistry.hpp:45-49` shows new edges to `CfgFieldRegistry.hpp` + `ControllerConfig.hpp` + `MlCfgFlagRegistry.hpp` + `GateCfgFlagRegistry.hpp` + `BitmapMacros.hpp`. Reverse-grep confirmed: `CfgFieldRegistry.hpp:70-83` includes `LifecycleCfgFlagRegistry.hpp` + `GateCfgFlagRegistry.hpp` + `MlCfgFlagRegistry.hpp` + `RiskCfgFlagRegistry.hpp` + `OpsCfgFlagRegistry.hpp` but NOT `CfgGateRegistry.hpp`. No cycle. `GateCfgFlagRegistry.hpp:39` + `MlCfgFlagRegistry.hpp:40` include `BitmapMacros.hpp` only. Topology safe.
- **B11 if-constexpr template context:** PASS — Walker emission sites at CfgGateRegistry.hpp lines 325, 398, 500, 571 are all inside `namespace cfg_derived { ... template<unsigned F> ... }` template functions. Naming convention `BASE_X##_<SCOPE>` (PER_CORE / GLOBAL / ML_CFG_FLAG / GATE_CFG_FLAG) is enforced by token-paste failure mode (preprocessor errors on undefined identifier). Audit at line 644 confirms `STAMP_RESULT_DERIVED_FIELDS_AUTO_GEN()` uses `_STAMP_RESULT` base — file-scope expansion (not template; but consumer doesn't use if-constexpr filter — unconditional emit per Decision C Approach A). Pattern is internally consistent.
- **B12 row ordering:** Cohort meta-walker expands to 4 FOREACH invocations IN ORDER (PER_CORE → GLOBAL → ML_CFG_FLAG → GATE_CFG_FLAG) regardless of consumer site → ordering is single-sourced. No drift possible across consumer sites.
- **B2 cross-walker uniqueness:** `tools/check_struct_field_uniqueness.py` lands at .B.3 ship close + `tools/check_field_name_uniqueness.py` already at HEAD (5668 bytes) — both verify uniqueness across the 4 cohort registries.

**Step 1.6.5b implementation-detail verdict: ALL CLEAN** (Class 18/21 sister-consumer-asymmetric-coverage closure structurally enforced).

---

## Punch-list (ordered by severity)

1. **(B8 SILENT-RISK CRITICAL)** Plan body L2 amendment: **extend CLI flag list from 23 → 33 flags** to match bash script's `getopt` loop. Specifically add: `--xgb-max-depth`, `--xgb-learning-rate`, `--xgb-n-estimators`, `--xgb-subsample`, `--xgb-colsample-bytree`, `--xgb-min-child-weight`, `--xgb-seed`, `--xgb-tree-method`, `--build-flags-hash`. All 9 emit to HMAC-signed canonical wire body via `FOREACH_STAMP_BOUND_MODEL_CONST` (verified at `StampBoundModelConstRegistry.hpp:324-343`). Without them, operator's existing trained-model stamping workflow CANNOT round-trip bytewise-identically. (~10 min plan body amendment; ~20 min CLI implementation for the additional getopt cases). **Closes B8.**

2. **(B11 LOAD-BEARING-LOUD)** Plan body L3 amendment: **spec the 4-line CMakeLists.txt pattern** matching `compare_scalers` precedent (lines 248-251):
   ```cmake
   add_executable(stamp_model_cli tools/stamp_model_cli.cpp)
   target_compile_options(stamp_model_cli PRIVATE -O2 -march=native)
   target_include_directories(stamp_model_cli PRIVATE ${CMAKE_SOURCE_DIR}/..)
   target_link_libraries(stamp_model_cli PRIVATE ssl crypto Threads::Threads)
   ```
   Explicit linker libs (ssl crypto for HMAC + Threads for framework's transitive pthread). Verify at coding time that `build.sh`'s `build_engine()` runs `cmake --build build -j"$JOBS"` with no `--target` restriction (it doesn't; new binary builds by default). (~5 min plan body amendment.) **Closes B11.**

3. **(B7 GUARDED-BY-BUILD)** Plan body L3 amendment: **add note about transitive include depth**. `tools/stamp_model_cli.cpp` pulls the full framework chain via `ModelInference.hpp` (~15+ headers). Build time +5-15s estimated (vs `compare_scalers` ~3s); same scale as `controller_test`. Acceptable but worth noting in plan body so cold-pickup reader doesn't suspect drift. (~3 min plan body annotation.) **Closes B7.**

4. **(B8 sub-finding)** Plan body L2 should specify **the exact framework call site** the CLI uses. `stamp_write_for_model` at `ML_Headers/ModelInference.hpp:1688` takes `const StampInferenceCfgInputs* inf` as final arg. CLI's main() needs to: (a) construct `StampInferenceCfgInputs inf{}`, (b) populate via `STAMP_HAS_SET(inf, <field>)` + value assignment per supplied flag, (c) call `stamp_write_for_model(...&inf)`. Plan body L2 mentions the API but doesn't spell out the population pattern. (~5 min plan body amendment.)

5. **(B9 strengthening)** Plan body L1 says "framework-driven-cli-binary-pattern.md Stage 2 DRAFT (LANDED at workspace)". **Verify** this spec lives at workspace path before Phase L coding starts (skill spec requires Stage 2 DRAFT in place for Stage 3 first canonical to refer back to it). Quick check: `ls /home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md`. If not present, L1 must precede L2-L6.

---

## Recommended next move

**Option (X) — Audit-first plan body amendment (RECOMMENDED).** Apply findings 1+2+3+4 to plan body Phase L sub-steps before any coding starts. Total effort: ~25-30 min plan body editing.

Option (Y) — Code with annotations (alternative). Write the CLI binary with all 33 flags + 4-line CMakeLists + transitive-include-depth comment in the code itself; surface plan body gap as TECH_DEBT entry post-ship. Lower upfront cost but breaks `feedback_plan_right_not_fast` discipline.

Option (Z) — Defer the 9 XGB flags. **REJECTED** per `feedback_no_defer_for_effort` — defer would break operator workflow continuity for existing XGBoost-trained models; defeats Decision F SOFT compat goal.

**Inflection check** (per `feedback_iteration_spiral_signals_audit_meta_gap`):
- This is the FIRST `/blindspot-scan` invocation against Phase L (just-amended v1.14 scope)
- 1 SILENT-RISK + 1 LOAD-BEARING-LOUD pillar surfaced; 1 of them is CRITICAL (B8 flag-set incompleteness)
- NEW pillars surfaced this fire: 0 (B1-B12 taxonomy covers all findings; no B13+ needed)
- Iteration depth: 1 (recommendation: amend plan body once with findings 1-5; re-fire /blindspot-scan only if a new code-state changes the surface)

---

## Blocking gaps that MUST resolve before Phase L coding starts

1. **B8 flag-set completeness** — plan body L2 amendment to 33 flags (or explicit deferral with TECH_DEBT entry). **NON-NEGOTIABLE** per `feedback_motivated_collaborator_for_caramel` + `feedback_surface_operator_migration_path_proactively`.
2. **B11 CMakeLists 4-line pattern** — plan body L3 amendment. **CRITICAL** because partial spec (1 of 4 lines) would fail compile or fail link (HMAC needs `ssl crypto`).

**Non-blocking but recommended:**
- B7 transitive-include-depth annotation (plan body L3 note)
- B8 framework call site population pattern spec (plan body L2 mini-example)
- B9 DESIGN_SPEC pre-existence verification (1-line ls check)

---

## Per-finding cross-references

- **B8** — `tools/stamp_model.sh:109-147` (getopt loop) vs plan body `subplans/2026-05-17-...-legacy-empty-out.md:803` (L2 flag list). Framework-side coverage at `ML_Headers/StampBoundModelConstRegistry.hpp:324-343` (XGBoost group) + line 253 (build_flags_hash standalone).
- **B11** — `CMakeLists.txt:244-251` (compare_scalers precedent) vs plan body L3.
- **B7** — `tools/compare_scalers.cpp:35-36` (shallow chain) vs `ML_Headers/ModelInference.hpp:22-34` (deep chain via stamp helpers).
- **B9** — `tools/stamp_model.sh:11-25` (recurrence dates) verifies plan body line 138 claim.
- **Step 1.6.5b** — `MemHeaders/CfgGateRegistry.hpp:185-231` (meta-walker definition); HEAD state CLEAN; included for completeness per audit scope.

---

**Audit fired:** 2026-05-18 against engine HEAD `3d27512`. Honors `consult-before-coding` — operator decides next move; this skill never auto-proceeds. Per `feedback_consult_on_audit_findings` + `feedback_audit_own_proposals_with_same_rigor` (4-pillar self-audit: cross-checked DESIGN_SPECS + anti-pattern catalog + operator-impact + novel-alternative).
