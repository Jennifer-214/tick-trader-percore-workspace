# /merge-scan — Phase L amendment v1.14 (`tools/stamp_model_cli.cpp` framework-driven CLI binary)

**Scope:** Phase L NEW v1.14 amendment to `plans/v5.15-live-readiness/subplans/2026-05-17-v5.15.5.F.4d.1.B.3-legacy-empty-out.md` proposing replacement of `tools/stamp_model.sh` with `tools/stamp_model_cli.cpp` framework-driven C++ CLI binary.
**Date:** 2026-05-18
**Engine HEAD:** 3d27512 (WIP-checkpoint 6)
**Audited spec:** `tick-trader-percore-workspace/DESIGN_SPECS/framework-driven-cli-binary-pattern.md` v1.0 Stage 2 DRAFT
**DESIGN_PHILOSOPHY preload:** § 4 (Latency cost framework — N/A for cold-path CLI; tagged informational); § 7 (Structural-fix family — IS the framework Phase L applies).

## Verdicts (per focus area)

| # | Focus | Verdict | One-line |
|---|---|---|---|
| 1 | Existing C++ tool precedent reuse (`compare_scalers.cpp`) | **GREEN** | Plan correctly identifies sister precedent; CMake pattern at lines 248-251 is the template; no reuse blocker. |
| 2 | Sister bash scripts (other `tools/*.sh`) | **GREEN** | None are wire-format emitters; no sister migrations in scope for `.B.3`; Phase L is the ONLY framework-driven CLI candidate at this ship. |
| 3 | Sister DESIGN_SPECS fold opportunities | **GREEN** | All 5 sister specs correctly maintained as separate concerns; spec cross-references handle composition cleanly. |
| 4 | CLI binary architecture reuse | **YELLOW (advisory)** | One minor reuse opportunity: `ControllerConfig_Load()` could replace ad-hoc cfg construction; `getopt_long` is correct over engine.cfg parser inline reuse. Locale defense-in-depth pin is correct. |
| 5 | FOREACH_CLI_MODE cross-reference | **GREEN** | Spec already cites FOREACH_CLI_MODE 5× including roadmap line 545 explicitly naming `tools/stamp_model_cli.cpp` as precedent; no gap. |

---

## Focus 1 — Existing C++ tool precedent reuse (`compare_scalers.cpp`)

### What I checked

- `tools/compare_scalers.cpp` (159 LOC; standalone CLI)
- `tools/compare_scalers.sh` (35 LOC; rebuilds-on-demand wrapper invoking cmake target then exec'ing binary)
- CMake target at `CMakeLists.txt:248-251`
- Build flag inheritance + dependency declaration

### Findings

**CMake target structure (CMakeLists.txt:248-251):**
```cmake
add_executable(compare_scalers tools/compare_scalers.cpp)
target_compile_options(compare_scalers PRIVATE -O2 -march=native)
target_include_directories(compare_scalers PRIVATE ${CMAKE_SOURCE_DIR}/..)
target_link_libraries(compare_scalers PRIVATE ssl crypto)
```

The spec's L3 CMake skeleton at `framework-driven-cli-binary-pattern.md:204-214` is **structurally identical** — same pattern (`add_executable` + `target_compile_options` + `target_include_directories` + `target_link_libraries`). Plan can copy this skeleton directly. **Important addition Phase L needs that compare_scalers doesn't have:** pthread linkage (framework includes `<thread>` headers transitively via ControllerConfig + ModelInference); the spec mentions pthread at line 209 as a placeholder. **RECOMMEND: explicit `pthread` linkage line in the new CMake target,** matching `parity_harness` at `CMakeLists.txt:242` (`target_link_libraries(parity_harness PRIVATE Threads::Threads ssl crypto)`).

**Build flag inheritance:** `compare_scalers` uses `-O2 -march=native`. Phase L's CLI binary doesn't need O3/LTO (cold path; ~30s validate-then-write run; not p99-bounded). `-O2 -march=native` is correct match.

**Framework primitive reuse — does compare_scalers use anything Phase L could too?**

NO direct framework primitive reuse opportunity. `compare_scalers.cpp` uses `FeatureStandardizer_Load` (loader) + `FEATURE_NAMES` (registry name table); these are not framework wire-emit primitives. The reuse direction Phase L needs is into the framework's `stamp_write_for_model` API which `compare_scalers` doesn't touch. **They're sister tools in build pattern only, not framework consumers in common.** The spec correctly notes this at line 13 + 320-325.

**Header include patterns from tools/ subdir at HEAD:**

`compare_scalers.cpp:35-36` uses relative paths `../ML_Headers/FeatureStandardizer.hpp` + `../ML_Headers/FeatureRegistry.hpp`. The spec's example at lines 139-142 uses the same pattern (`../CoreFrameworks/ControllerConfig.hpp` etc.). **Confirmed: relative-from-tools/ includes work at HEAD; no path quirks.**

### Verdict: GREEN

Plan correctly identifies sister precedent. RECOMMENDATION: in Phase L L3 step, change CMake `target_link_libraries` placeholder to explicitly include `Threads::Threads ssl crypto` (matches parity_harness; required by framework's pthread transitively).

---

## Focus 2 — Other `tools/*.sh` — sister-migration candidates for Phase L scope

### What I checked

All bash scripts in `tools/`:
- `calls_graph_diff.sh` (orphan-function detection)
- `compare_scalers.sh` (wrapper for compare_scalers binary — already C++)
- `gen_code_map.sh` (DOCS/CODE_MAP.md generation)
- `stamp_model.sh` (Phase L target)
- `validate_feature_mask.sh` (4-surface feature_mask binding check)

### Classification

| Script | What it does | Class | Phase L scope? |
|---|---|---|---|
| `calls_graph_diff.sh` | grep-based orphan function detection across legacy/sharded entrypoints | (c) Static analysis tool; no wire-format emit; no framework mirror | NO — skip |
| `compare_scalers.sh` | Rebuild-on-demand wrapper for `compare_scalers` C++ binary | (c) Already C++ — already structurally correct | NO — skip |
| `gen_code_map.sh` | Generates DOCS/CODE_MAP.md from grep'd function definitions | (c) Doc generation, no engine framework mirror | NO — skip |
| `stamp_model.sh` | Constructs HMAC-signed stamp body (716 lines mirroring engine emit) | **(a) Wire-format emitter mirroring engine `stamp_write_for_model`** | **YES — Phase L target** |
| `validate_feature_mask.sh` | grep-checks engine.cfg + stamp body for feature_mask wire key presence; 4 surfaces | (b) Diagnostic/verification only — READS wire format, doesn't EMIT it | NO — Layer 7 applies but no structural-fix recurrence |

**Key finding:** **`stamp_model.sh` is the ONLY wire-format-emitting bash script in `tools/`.** All others are diagnostic/static-analysis/doc-generation. Phase L's scope is correctly bounded to a single migration target; no sister bash scripts need migrating in `.B.3`.

**Note on `validate_feature_mask.sh`:** Does grep-check wire-format keys (`feature_mask=` at line 75, `core_feature_mask` at line 57), but it's READ-side verification (against an already-emitted stamp file), not EMIT-side mirroring. If the engine renames `feature_mask`, the validate script breaks too — but it's a verification tool, not a producer. Per spec lines 286-289 ("CLI surface is internal-only ... can be a foxml_suite GUI panel instead"), validate_feature_mask.sh is a one-off post-train verification helper; recurrence count = 1; **doesn't meet 3+ structural-fix threshold.** Layer 7 § per-site disposition still applies — the v1.10 Step 1.6.8 cross-tool enumeration should have included this file in the per-site disposition sweep. **VERIFY:** Step 1.6.8 enumeration scope at v1.9 + the M2 catch at v1.10 covered `tools/stamp_model.sh` lines 221/244 specifically; check if `validate_feature_mask.sh:75` `feature_mask=` grep pattern was enumerated.

### Verdict: GREEN

No sister bash migration in `.B.3`; Phase L's single-target scope correct. **Advisory (not blocker):** confirm `validate_feature_mask.sh:75` is in Layer 7 cross-tool enumeration sweep (or document why it's not — script is READ-side verification, not EMIT-side mirror).

---

## Focus 3 — Sister DESIGN_SPECS fold opportunities

### What I checked

For each sibling spec, evaluated fold/no-fold per the canonical-sister-extension-discipline § Verdict menu (lines 64-77):

| Sister | Existing concern | Phase L `framework-driven-cli-binary-pattern.md`'s concern | Verdict | Rationale |
|---|---|---|---|---|
| `registry-coverage-ci-check-pattern.md` | CI tooling that asserts struct↔registry consistency (positive/negative shape) | Replaces parallel bash mirror with framework-call C++ binary | **NO-FOLD** | Distinct mechanism — registry-coverage uses CI ENFORCEMENT (build-fail on drift); framework-driven-cli uses STRUCTURAL ELIMINATION (no parallel surface to drift). Both serve "structural-fix family" parent. Overlap is goal-level (close Class 18/19/21) not mechanism-level. |
| `structural-fix-preferred-decision-framework.md` | Parent decision framework — N occurrence threshold + recurrence gating | Phase L spec invokes it (line 4 cites § Step 2 4×-recurrence threshold) | **NO-FOLD (parent-child)** | Parent is the meta-rule; Phase L is one specific mechanism the framework applies to. Correctly cited as parent at spec line 21. |
| `canonical-sister-extension-discipline.md` | Discipline for when to extend canonical sister vs build new | Phase L spec's drafting applied this discipline (lines 12 + 16) | **NO-FOLD (parent-child)** | Discipline-level; Phase L is a Stage 3 application instance. Correctly cited as parent. |
| `wire-format-byte-preservation-discipline.md` Layer 7 (cross-tool emit-site enumeration) | Discipline for sync-checking cross-tool emit sites | Structural elimination of cross-tool seam at framework-driven surfaces | **NO-FOLD (complementary)** | Layer 7 codifies DISCIPLINE for surfaces that CAN'T use framework (bash diagnostic tools); Phase L STRUCTURALLY ELIMINATES at surfaces that CAN. Correctly framed at Phase L spec line 8 + Layer 7 cross-ref note at `wire-format-byte-preservation-discipline.md:352`. Folding would conflate "discipline for surfaces without framework option" with "elimination at framework-driven surfaces" — two genuinely different scopes. |
| `pattern-codification-lifecycle.md` | Stage progression meta-framework | Phase L spec explicitly traces Stage 1 → Stage 5 progression (lines 416-429) | **NO-FOLD (meta-framework)** | Phase L IS a canonical lifecycle application; lifecycle spec is meta-framework. Folding would collapse meta into instance. |

### Verdict: GREEN

All 5 sister specs correctly maintained as separate concerns. Spec cross-references compose cleanly:
- `framework-driven-cli-binary-pattern.md` § "Cross-references" (lines 7-22 + 433-451) names each sibling with role articulated
- `wire-format-byte-preservation-discipline.md:352-359` reciprocally cites the framework-driven pattern
- `canonical-sister-extension-discipline.md:71-77` expanded fold-menu drove the spec's own drafting decision (NO-FOLD as structural fix verdict captured in plan body Decision G § canonical sister inspection)

**No fold opportunities; no merge candidates surfaced.**

---

## Focus 4 — CLI binary architecture reuse opportunities

### What I checked

Specific reuse opportunities the spec mentions or implies:
- (4a) CLI flag parsing — `getopt_long(3)` from `<getopt.h>` vs engine.cfg parser reuse vs inline
- (4b) ControllerConfig construction — `ControllerConfig_Default<64>()` + CLI overrides vs `ControllerConfig_Load("engine.cfg")` reuse vs ad-hoc inline
- (4c) Locale pinning — defense-in-depth in main() AND framework's internal pin

### Findings

**(4a) CLI flag parsing:** Spec correctly chooses `getopt_long(3)` (line 137 + 154-162). **NO reuse opportunity from engine.cfg parser** — the cfg parser at `ControllerConfig_Load` (ControllerConfig.hpp:1998) reads `key=value` lines from a file with X-macro dispatch; CLI args are `--flag value` getopt-shaped. Different shape; the spec is correct that getopt_long is right. **NO MERGE opportunity here.**

**(4b) ControllerConfig construction:** Spec example at line 167 shows `ControllerConfig<64> cfg = ControllerConfig_Default<64>();` with per-CLI-flag overrides afterward. **REUSE OPPORTUNITY (YELLOW — advisory):** could the CLI accept an optional `--cfg-path /path/to/engine.cfg` flag that calls `ControllerConfig_Load<64>(path)` directly? Two arguments for this:

1. **Operator continuity:** the bash script's flag interface doesn't have `--cfg-path`, so adding it is operator-additive (no breakage); operator may already have `engine.cfg` configured and want to inherit defaults from it for stamp emit (e.g., feature_mask, fee rates) without retyping every flag at CLI.
2. **Framework reuse:** `ControllerConfig_Load` already does X-macro dispatch across FOREACH_CFG_FIELD; the CLI inherits the same parse semantics for free.

**Against this:** spec line 67 frames CLI as "thin wrapper" (~150-200 LOC); operator may not WANT the CLI to read engine.cfg (stamp-emit context may be different from runtime engine context). **Recommendation:** spec/plan-body could add a sentence in Step L2 acknowledging this option + deferring decision to first canonical implementation (Phase L coding). NOT a blocker; operator-additive feature post-Phase-L.

**(4c) Locale pinning:** Spec at line 197 + 351 says "defense in depth: pin LC_NUMERIC=C in main() AND framework's internal pin". **Verified:** framework's internal pin is at `ModelInference.hpp:1630-1633` (uselocale-based per-thread pin); is invoked inside `stamp_write_for_model` before any %g/%f formatting. **Defense-in-depth pin in `main()` IS cheap (1 line, ~10ns at startup) + correct policy.** Risk: any code path in main()-before-framework that uses %g/%f locale-sensitive formatting (e.g., error fprintf with double argument) would emit wrong locale without the early pin. Defense-in-depth is correct.

### Verdict: YELLOW (advisory only)

One opt-in operator-additive feature opportunity (`--cfg-path` flag invoking `ControllerConfig_Load`); does not block Phase L. NO functional reuse merges (`getopt_long` is correct over inline; locale defense-in-depth is correct).

---

## Focus 5 — FOREACH_CLI_MODE cross-reference (decoupling-endgoal-roadmap.md)

### What I checked

- `framework-driven-cli-binary-pattern.md` cross-ref count for FOREACH_CLI_MODE
- `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` content for tools/stamp_model_cli.cpp precedent claims
- Whether `.B.3` plan body Phase L should add additional roadmap cross-reference

### Findings

**Spec already references FOREACH_CLI_MODE 5×:**
- Line 22: "Decoupling positioning: ... 'Training entry points' axis (GUI button → execv child via FOREACH_CLI_MODE registry); this pattern IS a precedent for the FOREACH_CLI_MODE registry's eventual instantiation"
- Line 450: roadmap cross-ref in "Cross-references" section
- Line 545 of roadmap (verified): "`tools/stamp_model_cli.cpp`" explicitly named as precedent for FOREACH_CLI_MODE registry instantiation
- Lines 560, 573 of roadmap: framework-driven CLI as foundation for future registry
- Line 712: roadmap timeline includes v5.15.3 FOREACH_CLI_MODE registry

**Reciprocal cross-reference verified:** roadmap line 545 already names `tools/stamp_model_cli.cpp` as precedent. Cross-references mutually link.

### Verdict: GREEN

No additional cross-ref needed. FOREACH_CLI_MODE relationship correctly captured bidirectionally. Phase L's spec is a Stage 3 first canonical that the future FOREACH_CLI_MODE registry can build on top of (registry would enroll N CLI binaries; each binary uses framework-driven pattern internally).

---

## Top 3 reuse opportunities Phase L should leverage

### 1. CMake `target_link_libraries` explicit pthread (PRIORITY HIGH)

The spec L3 CMake skeleton at lines 207-214 leaves `target_link_libraries(stamp_model_cli PRIVATE ...)` as a placeholder. Framework includes pthread transitively (ControllerConfig + ModelInference); the CLI binary will fail to link without explicit `Threads::Threads`. **Match `parity_harness` (CMakeLists.txt:242):** `target_link_libraries(stamp_model_cli PRIVATE Threads::Threads ssl crypto)`. **Action:** plan body Step L3 should explicitly state the link line.

### 2. compare_scalers.cpp build-pattern direct copy (PRIORITY HIGH)

`compare_scalers.cpp` (159 LOC; established 2026-05-07; in production) is structurally the sister C++ tool. Phase L coding can:
- Copy the CMake target shape from CMakeLists.txt:248-251 verbatim (then add pthread linkage per item 1)
- Use the same `#include "../ML_Headers/..."` relative-include pattern (proven at HEAD)
- Use the same `-O2 -march=native` flags (correct for cold-path CLI)

### 3. ControllerConfig_Load optional `--cfg-path` flag (PRIORITY LOW — advisory)

Spec L2 example shows `ControllerConfig_Default<64>()` baseline + per-CLI-flag overrides. **Additive enhancement:** support `--cfg-path /path/to/engine.cfg` invoking `ControllerConfig_Load<64>(path)` for operators who want CLI to inherit cfg-file defaults (e.g., feature_mask). Defer decision to first-canonical coding; explicit acknowledgment in plan body Step L2 makes the operator-experience design point visible.

---

## Sister tool migrations Phase L should also handle

**NONE.** Per Focus 2 classification: `stamp_model.sh` is the only wire-format-emitting bash tool. All others are diagnostic/static-analysis/doc-generation — out of structural-fix scope (recurrence < 3 and/or not mirror-shaped).

**EXPLICITLY DEFER:** `validate_feature_mask.sh:75` `feature_mask=` grep reads engine wire format; verify it was enumerated in Layer 7 cross-tool emit-site sweep (per v1.10 Meta-gap M2). Recurrence count = 1; doesn't meet 3+ structural-fix threshold; Layer 7 discipline (cross-ref comments + per-site disposition) suffices.

---

## Blocking gaps where Phase L misses reuse opportunities

**NONE BLOCKING.**

**ADVISORY (not blocker):**
1. Plan body Step L3 should make pthread linkage explicit in the CMake line (defense against link error at first canonical build). Use `Threads::Threads ssl crypto`.
2. Plan body Step L2 should acknowledge `--cfg-path` flag option as a deferred-to-first-canonical decision (operator-additive; supports framework reuse via `ControllerConfig_Load`).
3. Confirm `validate_feature_mask.sh:75` was scanned during Step 1.6.8 Layer 7 enumeration (READ-side; no structural fix needed; cross-ref comment optional).

---

## Overall recommendation

Phase L amendment is **structurally correct + reuse-clean**. No fold opportunities; no parallel-infrastructure proliferation. Sister precedent (`compare_scalers.cpp`) directly reusable for build pattern. Sister DESIGN_SPECS correctly maintained as separate concerns with clean composition cross-references. FOREACH_CLI_MODE relationship bidirectional and captured.

**Two specific plan-body amendments recommended (both advisory, neither blocking):**
1. Step L3: explicit `Threads::Threads ssl crypto` link line (match `parity_harness`).
2. Step L2: acknowledge optional `--cfg-path` operator-additive flag as deferred-to-first-canonical decision.

Phase L can proceed to coding without further restructure.

---

**End of merge-scan findings.**
