# /trace-deps report — `.B.3` Phase L (Decision G; v1.14 amendment) — 2026-05-18

**Target plan:** `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md`
**HEAD:** `3d27512` (WIP-checkpoint 6: TYPE-SENSITIVE test mitigations, 27 sites)
**Focus:** v1.14 amendment Phase L (Decision G) — replace `tools/stamp_model.sh` with `tools/stamp_model_cli.cpp` framework-driven C++ binary.

---

## Summary

| Focus area | Verdict |
|---|---|
| 1. Symbol existence chain (Phase L API) | **GREEN** — all symbols verified at HEAD |
| 2. Cross-tool consumer enumeration | **GREEN** — only `tools/stamp_model.sh` emits wire-format keys |
| 3. Build system dependency chain | **GREEN** — `compare_scalers` sister precedent valid; transitive includes work |
| 4. CLI flag interface vs bash | **RED** — plan body L2 missing **9 flags** present in bash getopt loop |
| 5. TYPE-SENSITIVE consumer chain (post-checkpoint 6) | **YELLOW** — 27 sites compile; 14 transitional failures expected; commit-msg root-cause claim is **incorrect** (legacy walker already extracts via `FPN_ToDouble`) |

**Overall verdict:** **YELLOW-→-RED on flag-coverage gap; fix before promoting `.B.3` v1.14 → ACTIVE coding.**

---

## Focus area 1 — Symbol existence chain

| Symbol | File:line | Verdict |
|---|---|---|
| `stamp_write_for_model` | `ML_Headers/ModelInference.hpp:1688` | **PASS** — sig: `(const char* model_path, const char* secret, int format_version, const char* trained_on_iso, double wf_mean_val, double held_out_metric, double gap_threshold, int force, uint64_t feature_registry_hash=0, const char* engine_version=nullptr, const StampInferenceCfgInputs* inf=nullptr)` — 11 params, last 3 defaulted |
| `Stamp_AssembleAndEmit<F>` | `ML_Headers/StampHelper.hpp:140` | **PASS** — template `<unsigned F>`, takes `(output_stamp_path, hmac_secret, ControllerConfig<F>&, StampArgs<F>&)` — alternative entry point (higher-level helper) |
| `cfg_derived::populate_stamp_cfg_from_derived<F>` | `MemHeaders/CfgGateRegistry.hpp:342` | **PASS** — sig `(char* buf, size_t cap, const ControllerConfig<F>&) → size_t`; uses `FOREACH_STAMP_BOUND_DERIVED_COHORT` (4 walkers, post-checkpoint-5 refactor) |
| `FOREACH_STAMP_BOUND_DERIVED_COHORT` | `MemHeaders/CfgGateRegistry.hpp:227` | **PASS** — action-parameterized meta-walker; 4 sites consume (line 325 populate_inf / 398 stamp_cfg / 500 drift_check / 571 parse) |
| `ControllerConfig<F>` | `CoreFrameworks/ControllerConfig.hpp:373` | **PASS** — template struct definition |
| `ControllerConfig_Default<F>()` | `CoreFrameworks/ControllerConfig.hpp:1477` | **PASS** — `template <unsigned F> inline ControllerConfig<F>`; returns a default-initialized config |
| `StampInferenceCfgInputs` | `ML_Headers/ModelInference.hpp:1655` | **PASS** — struct with `static constexpr unsigned F = 64`, `uint64_t has_flags`, X-macro generated field expansion |
| `StampWriteResult` | `ML_Headers/ModelInference.hpp:1636` | **PASS** — struct `{ int ok; char error[256]; char stamp_path[512]; }` — matches plan body claim |
| `FPN_FromDouble<F>()` | `FixedPoint/FixedPointN.hpp:162` | **PASS** — template fn |
| `FPN_ToDouble` | (multiple sites; ADL works) | **PASS** |
| `STAMP_FORMAT_VERSION_CURRENT` | (NOT YET AT HEAD) | **DEFERRED** — introduced AT Step 1.6.7.3 in same `.B.3` ship (Phase L MUST land in same commit per plan body line 836); not a HEAD-gap |

**All Phase L API surface confirmed at HEAD.** Build is CLEAN (`cmake --build build` succeeds for all targets including sister tool `compare_scalers`).

---

## Focus area 2 — Cross-tool consumer enumeration

**Comprehensive grep across all file types (bash, python, cpp, hpp) for wire-format key emitters:**

```bash
rg -n '"stamp_format_version=|stamp_format_version=1\b|"model_format_version=|"inference_cfg_[a-z_]+=' --glob '*.{sh,py,cpp,hpp}' --glob '!build/**'
```

Production emit sites only:
- `ML_Headers/ModelInference.hpp:1759-1784` — **the canonical engine emit** (Phase L target — CLI calls this directly)
- `tools/stamp_model.sh:189-262` — **the only bash mirror** (Phase L target — replaced)

Test fixtures (NOT production emit):
- `tests/controller_test.cpp:8891-8955` — 5 hand-written canonical body literals for fixture round-trip tests (Step 1.6.7.5 scope)

Comment-only references (NOT emit):
- `MemHeaders/FailureModeRegistry.hpp:202` / `GUI/MLStatusPanel.hpp:298` / `CoreFrameworks/ModelValidation.hpp:258` / `CoreFrameworks/GateCfgFlagRegistry.hpp:29` — narrative cfg-flag names mentioning `acknowledge_inference_cfg_drift`, NOT wire emit

**Scripts/tools cross-checked:** `scripts/{download_data,sync_public,verify_ticks,sync_archives}.sh` + `tools/{chart,feature_overlay}.py` + `tools/validate_feature_mask.sh` — **none** emit wire-format keys.

**Verdict:** Phase L scope is **complete** at the cross-tool surface — `tools/stamp_model.sh` is the only non-engine wire-format emitter. No other bash/python scripts emit `stamp_format_version=` / `model_format_version=` / `inference_cfg_*=` / `model_sha256=` / `trained_on=`.

---

## Focus area 3 — Build system dependency chain

**Sister precedent verified:**
- `CMakeLists.txt:248-251` — `compare_scalers` target template
  ```cmake
  add_executable(compare_scalers tools/compare_scalers.cpp)
  target_compile_options(compare_scalers PRIVATE -O2 -march=native)
  target_include_directories(compare_scalers PRIVATE ${CMAKE_SOURCE_DIR}/..)
  target_link_libraries(compare_scalers PRIVATE ssl crypto)
  ```

**Phase L pattern lift (proposed plan body L3):**
- `add_executable(stamp_model_cli tools/stamp_model_cli.cpp)` — matches sister
- Includes via `../` relative paths — sister `compare_scalers.cpp:35-36` confirms this works:
  ```cpp
  #include "../ML_Headers/FeatureStandardizer.hpp"
  #include "../ML_Headers/FeatureRegistry.hpp"
  ```

**Transitive include sanity (for CLI):**
- `ControllerConfig.hpp` pulls in (via 15+ `#include`s): `Limits.hpp`, `FixedPointN.hpp`, `CfgFieldRegistry.hpp`, `CfgFieldDispatch.hpp`, all `*CfgFlagRegistry.hpp` registries
- `ModelInference.hpp` pulls in: `StampBoundCfgRegistry.hpp`, `StampBoundModelConstRegistry.hpp`, `CfgGateRegistry.hpp` (which provides `populate_stamp_cfg_from_derived`), `HmacSha256.hpp`, `FeatureStandardizer.hpp`, `Version.hpp`
- `StampHelper.hpp` pulls in: `ModelInference.hpp` + `LabelFunctions.hpp` + `XGBHyperparams.hpp`

So `#include "../CoreFrameworks/ControllerConfig.hpp"` + `#include "../ML_Headers/ModelInference.hpp"` would be sufficient. Linking against `ssl crypto` (HMAC) matches `compare_scalers` precedent. **Build dep chain is clean.**

**Minor DESIGN_SPEC drift:**
- `framework-driven-cli-binary-pattern.md:142` example cites `#include "../FixedPoint/FPN.hpp"` — the file is actually `FixedPointN.hpp` (or `FixedPoint64.hpp` for the F=64 specialization). Stale path in DRAFT example. **YELLOW** — fix DESIGN_SPEC example before promoting to Stage 3 first canonical.

---

## Focus area 4 — CLI flag interface vs bash script — **RED**

**Bash script accepts 32 unique flags (line 109-147):**

```
1. --model              17. --bandit-blend-ratio
2. --secret             18. --fee-rate-maker
3. --wf-mean-val        19. --fee-rate-taker
4. --held-out-metric    20. --training-poll-interval
5. --gap-threshold      21. --xgb-max-depth          ← MISSING from plan
6. --trained-on         22. --xgb-learning-rate      ← MISSING
7. --format-version     23. --xgb-n-estimators       ← MISSING
8. --feature-registry-hash  24. --xgb-subsample      ← MISSING
9. --engine-version     25. --xgb-colsample-bytree   ← MISSING
10. --feature-scaler-present  26. --xgb-min-child-weight ← MISSING
11. --scaler-sha256     27. --xgb-seed               ← MISSING
12. --model-num-outputs 28. --xgb-tree-method        ← MISSING
13. --confidence-threshold-scale  29. --build-flags-hash ← MISSING
14. --barrier-gate-enabled  30. --feature-mask
15. --confidence-hard-block-threshold  31. --force
16. --held-out-fraction 32. --freshness-tau
```

**Plan body Step 1.6.8' L2 enumerates only 23 flags** — missing:
- 8 XGBoost hyperparam flags (`--xgb-max-depth` / `--xgb-learning-rate` / `--xgb-n-estimators` / `--xgb-subsample` / `--xgb-colsample-bytree` / `--xgb-min-child-weight` / `--xgb-seed` / `--xgb-tree-method`)
- 1 build-flags-hash flag (`--build-flags-hash` — bash line 141; emit at bash line 323-324)

**Operator-impact implication:**
- These XGBoost flags ARE used by `Stamp_AssembleAndEmit` in production code path (StampHelper.hpp:216-234 reads `args.snap_max_depth` etc. into `inf.xgb_*`). Bash script emits them at lines 282-307 (verified via earlier grep). Operator scripts/training pipelines invoking `tools/stamp_model.sh --xgb-max-depth=N` would break with the proposed CLI.
- `--build-flags-hash` is provided by training scripts for forensic ID (v5.11.41 CRITICAL-2). Bash emits at line 324; C++ engine framework auto-populates via `tt::BUILD_FLAGS_HASH()` (StampHelper.hpp:238) — so CLI **doesn't strictly need** the flag if it uses framework auto-population. But the plan body L2 doesn't say this; **silent semantic change** vs bash where the operator-supplied hash is the wire value.

**Action item:** plan body L2 must either (a) ADD the 9 missing flags to match bash interface 1:1, OR (b) explicitly document them as deprecated/auto-derived with operator-migration impact called out per `feedback_surface_operator_migration_path_proactively`.

---

## Focus area 5 — TYPE-SENSITIVE consumer chain post-WIP-checkpoint 6

**Build status at HEAD (3d27512):** CLEAN — all targets compile (engine + engine_gui + foxml_suite + controller_test + depth_recorder_test + parity_harness + compare_scalers).

**Test status:** 3223 PASS / 14 FAIL — all 14 failures isolated to the `v5.14.1.B.3.E` round-trip block (10) + `v5.14.1.E.E.B autopopulate` block (4), matching WIP-checkpoint 6 commit message expectations as TRANSITIONAL pending Step 1.6.4 production walker migration.

**WIP-checkpoint 6 commit-message root-cause claim — DRIFT:**

The commit message says:
> "legacy emit walker FPN<F> in %.17g variadic context = garbage bytes"

**This is inaccurate.** Inspecting `ML_Headers/StampBoundCfgRegistry.hpp:112-172`:
```
X(ridge_lambda, double, "%.17g", 0.0, FPN_ToDouble(cfg.ridge_lambda), ...)
```
The `get_value` column already extracts via `FPN_ToDouble(cfg.X)` — the variadic receives **double**, not `FPN<F>`. The legacy walker is NOT emitting garbage; it's working correctly.

**Real probable root-cause** (compatible with the failure pattern):
- 14 failures are `has_*` flag tests + round-trip value tests
- After Step 1.6.3 Approach A struct-gen (StampInferenceCfgInputs::ridge_lambda etc. shifted to `FPN<F>` storage), tests writing `inf.ridge_lambda = FPN_FromDouble<64>(0.15)` then parsing back via `parse_stamp_cfg_to_derived` may have a precision-roundtrip issue: `FPN<F=64>` → `double` (via FPN_ToDouble in emit) → text (`%.17g`) → `double` (via parse) → `FPN<F>` (via FPN_FromDouble) is **not** bytewise-identity. Or the `has_*` flag isn't being set correctly when parsing back into the new struct shape.
- This is consistent with "TRANSITIONAL until Step 1.6.4 lands" — Step 1.6.4 is the production walker migration that closes the round-trip gap end-to-end.

**Action item (low priority):** correct the WIP-checkpoint 6 commit message root-cause description OR add a clarifying note in plan body Step 1.6.3 amendment narrative. Doesn't block Phase L coding; matters for retrospective accuracy and the failure-attribution chain.

---

## Top 5 blocking findings

1. **(RED) Flag-coverage gap.** Plan body L2 lists 23 flags; bash script accepts 32. Missing 8 XGBoost hyperparams + 1 build-flags-hash. **MUST resolve before coding** — either add to CLI flag list OR document deprecation with operator-migration impact.

2. **(YELLOW) DESIGN_SPEC stale include path.** `framework-driven-cli-binary-pattern.md:142` references nonexistent `../FixedPoint/FPN.hpp`. Actual file is `FixedPointN.hpp`. Trivial fix; matters because DESIGN_SPEC is the canonical referent for Stage 3 first canonical implementation.

3. **(YELLOW) Commit-message root-cause drift.** WIP-checkpoint 6 attributes 14 transitional failures to "FPN<F> in %.17g variadic context" — but the legacy walker already extracts via `FPN_ToDouble` at X-macro expansion. Real root-cause is likely precision roundtrip OR has_* flag drift through new struct shape. Plan body Step 1.6.3 amendment narrative should be corrected for retrospective accuracy.

4. **(GREEN-with-note) STAMP_FORMAT_VERSION_CURRENT does NOT exist at HEAD** — introduced via Step 1.6.7.3 same-commit coupling. Plan body Step 836/1003 commit-coupling clauses are correct. Phase L coding depends on Step 1.6.7.3 also landing in the same commit.

5. **(GREEN) Cross-tool surface scope is comprehensive.** Phase L correctly identifies `tools/stamp_model.sh` as the only non-engine wire-format emit site. No missed scripts/tools.

---

## Recommendations

- **Plan body Step 1.6.8' L2 amendment v1.15:** add full 32-flag inventory (or document 9 omissions with operator-migration impact per `feedback_surface_operator_migration_path_proactively`). Specifically: explicitly choose for `--build-flags-hash` whether the CLI accepts operator-supplied (bash parity) OR auto-derives via `tt::BUILD_FLAGS_HASH()` (StampHelper.hpp:238 precedent). Both are valid; the choice belongs in plan body, not deferred to coding.
- **DESIGN_SPEC fix:** `framework-driven-cli-binary-pattern.md:142` change `FPN.hpp` → `FixedPointN.hpp` before Stage 3.
- **Commit-message retrospective:** add a brief note to plan body Coding-time discoveries Session D section correcting the FPN-`%.17g`-variadic claim — the actual root-cause is likely struct-shape round-trip drift, not snprintf format mismatch.
- **NO blocking concerns** on Phase L symbol existence, build dep chain, cross-tool consumer enumeration, OR overall structural design. Phase L is structurally ready; flag-coverage is the lone material gap.

---

**End of report.** Phase L is ARCHITECTURALLY SOUND but the L2 CLI flag list needs alignment with `tools/stamp_model.sh` before promoting v1.14 amendment to ACTIVE coding.
