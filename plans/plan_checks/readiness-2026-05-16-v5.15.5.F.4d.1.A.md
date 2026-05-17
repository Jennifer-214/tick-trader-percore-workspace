# /readiness — v5.15.5.F.4d.1.A framework-infra — 2026-05-16

**Plan body audited:** `subplans/2026-05-16-v5.15.5.F.4d.1.A-framework-infra.md` (v1.2)
**Sidecar audited:** `subplans/2026-05-16-v5.15.5.F.4d.1.A-framework-infra-examples.md` (v1.1)
**Sub-master:** `subplans/2026-05-16-v5.15.5.F.4d.1-thread-a-framework-full.md`
**Predecessor:** v5.15.5.F.4d MERGED — engine `545b087` + GPG-signed tag (verified)
**Target HEAD:** `545b087` (verified — clean working tree; Version.hpp shows `5.15.5.F.4d`)
**Audit type:** pre-coding gate (one of 5 parallel: parity-check + trace-deps + dod-audit + readiness + merge-scan)

---

## Verdict: YELLOW — minor amend (~30-45 min)

Plan is structurally sound: scope is well-defined, framework infrastructure design is correct (Option F revision is a genuine improvement), file:line refs largely verify cleanly, H1-H20 invariant audit is accurate, recovery story is concrete. Hot path is provably untouched. Risk profile (LOW-MED) is accurate.

The amend list below is **schema-shape disagreements** between plan body, sidecar, DESIGN_SPEC, and actual codebase. None of these are correctness-fatal but each will cost the coder 10-15 min mid-Step to resolve. Resolving up front is cheap.

---

## Plan summary

- 1 sub-ship of `.F.4d.1` umbrella; lands framework infrastructure (Items 1+2+10)
- 4-6h focused; LOW-MED risk; hot path UNTOUCHED
- 3 NEW headers (`DerivedFilterFramework.hpp`, `StampBoundDerivedFilter.hpp`, `DerivedFilterRoster.hpp`) + 1 row addition to `CoreFrameworks/MetaRegistry.hpp` + 1 compile-time `static_assert` block in `CfgFieldRegistry.hpp` after MetadataFlag enum + ~18 new tests in `controller_test.cpp`
- Branch: `feat/v5.15-live-readiness` (stay on sprint branch; rollback anchor `pre-v5.15.5.F.4d.1.A` GPG-signed)
- Successor: `.F.4d.1.B` consumes the framework

---

## 28-check verdict table

| # | Check | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | **PASS** | Zero hot-path code; framework runs at boot+test only. Walker fn-pointer callback is per-row but `calls_graph_diff.sh` will confirm post-coding |
| 2 | Train-serve parity | **PASS** | No model/feature/label changes; framework only adds derivation infrastructure |
| 3 | Surface area | **PASS** | 4 files touched (3 new headers + 1 enrollment row + 1 static_assert block); within reuse-merge bounds |
| 4 | Pointer init / heap | **PASS** | All stack-allocated; H1 preserved |
| 5 | Backward compat | **PASS** | No version constant bumps needed; no cfg fields removed; stamp body unchanged (zero rows carry STAMP_BOUND_CFG_DERIVED at `.A`) |
| 6 | Multi-threading | **PASS** | Single-threaded (boot+test); no new shared state |
| 7 | Test coverage | **PASS** | ~18 tests breakdown reasonable; Step 6 sections enumerated |
| 8 | Docs + invariants | **PASS** | DESIGN_SPECS catalog already lists 4 Thread A specs Stage 3 ACTIVE; H15-H20 already in CLAUDE.md; FEATURE_LOOKUP entry planned |
| 9 | Forward maintenance | **PASS** | Framework itself REDUCES future-add cost (1 row in FOREACH_DERIVED_FILTER for `.F.4e` GUI metadata + per-row macro invocation in consumer header) |
| 10 | Rollback story | **PASS** | Pre-tag `pre-v5.15.5.F.4d.1.A` (GPG-signed) at Step 0; concrete `git reset --hard` recovery in "if something goes wrong" |
| 11 | Architectural sprint detection | **PASS** | Framework introduction is exactly the structural-fix shape; H15/H16/H18/H19 served first canonical |
| 12 | Display ↔ execution invariant | **N/A** | No Position fields / GUI panels touched |
| 13 | Strategy lifecycle | **N/A** | No strategy changes |
| 14 | X-macro dispatch correctness | **PASS** | New `FOREACH_DERIVED_FILTER` is APPEND-only (single row); CI Checks discussed (see finding F2 re: name mismatch) |
| 15 | ML feature parity regression | **N/A** | No ML feature changes |
| 16 | Stamp-bearing cfg → recipe | **N/A** | No new stamp-bearing cfg fields at `.A` |
| 17 | Model-load path | **N/A** | No model-load changes |
| 18 | Reuse-audit (CLAUDE.md item 16) | **PASS** | Locale-pin pattern explicitly reuses `ModelInference.hpp:1697` precedent; walker fn-pointer signature reuses existing CfgFieldDescriptor walks |
| 19 | Pre-existing-work (strengthened) | **PASS w/ findings** | Sidecar `FOREACH_REGISTRY` row tuple shape DRIFT from actual schema — see F1 below |
| 20 | Future-proofness sanity | **PASS** | Framework IS the future-proofing |
| 21 | Test count assertion fragility | **PASS** | Plan uses `~18 new tests` → `~3192 expected`; not pinning literal count |
| 22 | Auto-trigger downstream re-audit | **N/A** | Pre-coding gate is THIS check |
| 23 | Latency accountability | **PASS** | Plan explicitly notes boot+test only; HOT_PATH_CHANGELOG=NONE entry; verified via `calls_graph_diff` |
| 24 | Mirror-function call-sequence | **N/A** | Not a mirror function; framework is base infrastructure |
| 25 | TECH_DEBT surface scan | **PASS** | TECH_DEBT-085 is THIS ship; status-update to IN-FLIGHT covered at ship close |
| 26 | (Placeholder) | **N/A** | |
| 27 | DESIGN_SPECS pattern application | **PASS** | All 4 Thread A specs (Stage 3 ACTIVE) referenced and applied; sister `/dod-audit` already ran (file present) |
| 28 | Test-strength anti-regression | **PASS** | No test deletions; all additions |

---

## Cold-pickup completeness (10 fields per CLAUDE.local.md going-forward rule)

| # | Field | Verdict | Notes |
|---|---|---|---|
| C.1 | Branch state | **PASS** | "stay on `feat/v5.15-live-readiness`" explicit |
| C.2 | Exec order matches dependencies | **PASS** | Steps 0→1→2→3→4→5→5b→6→7 enumerated; Variant 1 → Variant 2 → Variant 3 → first canonical → invariants → H16 → tests → ship; explicit dependency note at "Implementation order" |
| C.3 | First concrete move | **PASS** | Step 0 has concrete `git rev-parse HEAD` + baseline verify + tag command |
| C.4 | Function/macro names cited | **PASS** | `DERIVED_FILTER_DECLARE_GUI/WIRE_FORMAT/WIRE_FORMAT_TWO_SOURCE` + `STAMP_BOUND_CFG_walk_filtered_rows/emit_canonical_body/run_generic_invariants` + `FOREACH_DERIVED_FILTER` all enumerated |
| C.5 | File:line refs cited | **PASS-w-finding** | All cited refs verify exactly (CfgFieldRegistry.hpp:149, :890, :895, :947, :951, :959-962; MlCfgFlagRegistry.hpp:52+; ModelInference.hpp:1697) — see F4 re: sub-master stale ref |
| C.6 | Stale-claim audit | **PASS-w-finding** | All key claims verified at HEAD; minor discrepancies F1/F2/F3 below |
| C.7 | Effort vs LOC | **PASS** | ~4-6h focused for framework + 1 canonical + 18 tests = reasonable per past precedent (DerivedFilterFramework macros ~2-3h matches "new X-macro registry: 5 min" × scaling for 3 variants + invariant logic) |
| C.8 | Source-audit references | **PASS** | 4 Thread A DESIGN_SPECs Stage 3 ACTIVE referenced + Option F revision narrative + cross-refs to predecessor postmortem + planning handoff |
| C.9 | Predecessor / dependent paths | **PASS** | Predecessor `v5.15.5.F.4d` MERGED + `545b087` engine commit + plan body path + sub-master + planning handoff + audit-gate handoff + sidecar all cited with full paths |
| C.10 | Tag names locked | **PASS** | Pre-tag `pre-v5.15.5.F.4d.1.A` + ship tag `v5.15.5.F.4d.1.A` (both GPG-signed); rollback anchor flow concrete |

**Cold-pickup verdict:** **GREEN.** Fresh session 7+ days later could pick up cleanly without losing >15 min context. Sidecar substantially aids implementation. Plan body's H1-H20 audit table + Option F rationale capture is excellent for cold-pickup.

---

## Top findings (severity-classified)

### F1 — MEDIUM — `FOREACH_REGISTRY` row tuple shape MISMATCH between sidecar example + actual schema

**Evidence:** `CoreFrameworks/MetaRegistry.hpp:16` declares the canonical shape:
```
Row shape: X(registry_name, LEVEL, PARENT_NAME, description)  // 4 columns
```
Real rows (e.g., `MetaRegistry.hpp:39-90`) follow this 4-column shape with `PARENT_NAME = FOREACH_REGISTRY` (not `ROOT`) for LEVEL=1 rows.

**Discrepancy:** Sidecar § Step 4 (lines 453-457) shows a fabricated 7-column tuple:
```cpp
X(DERIVED_FILTER,
  "CoreFrameworks/DerivedFilterRoster.hpp", 1, ROOT,
  "metadata-bit-driven-derived-filter-framework.md", Class_21, MIXED,
  "Manages 7 cfg-derived filters; ...")
```
And the parent plan body line 260 says "PARENT=ROOT" — but actual schema uses `PARENT_NAME = FOREACH_REGISTRY` for non-root rows (the sentinel `ROOT_NONE` is reserved for the Level-0 self-row only).

**Severity:** MEDIUM. Coder will compile-error trying to use the sidecar's example as-is. Easy to discover but wastes a build cycle.

**Fix:** Update sidecar § Step 4 row to the canonical 4-column shape:
```cpp
X(FOREACH_DERIVED_FILTER, 1, FOREACH_REGISTRY,
  "Manages cfg-derived filters; Stage 3 ACTIVE first canonical at .F.4d.1.A.")
```
And update plan body line 260 to say `PARENT=FOREACH_REGISTRY, LEVEL=1`.

---

### F2 — MEDIUM — CI Check names `test_meta_registry_coverage` / `test_meta_registry_topology` DON'T EXIST as runnable tests

**Evidence:**
- `grep -rn "test_meta_registry_coverage\|test_meta_registry_topology"` in `tools/` and `tests/` returns **EMPTY**.
- `tools/check_meta_registry.py` EXISTS but is **NOT invoked from `build.sh`** (sister `check_per_core_registry_integrity.py` IS auto-invoked at `build.sh:260`).
- The actual mechanism: Python tool that operator runs manually (per `check_meta_registry.py` docstring "Adding a new registry without registering it FAILS the build" — but it doesn't fail the build because build.sh doesn't invoke it).

**Severity:** MEDIUM. Plan body verification gate references invented test names; ship close will check the wrong thing.

**Fix:** Update verification gate at plan body line 421+533:
- Replace "CI Check `test_meta_registry_coverage` PASS" with "Manual run: `python3 tools/check_meta_registry.py` shows DERIVED_FILTER + STAMP_BOUND_CFG enrolled cleanly"
- Same for `test_meta_registry_topology` — that's a NEW LEVEL+PARENT discipline check that should be added INTO `check_meta_registry.py` Check 3 (already covers "LEVEL > 0 rows have PARENT that exists in FOREACH_REGISTRY OR is ROOT_NONE" per docstring)
- Optional cleanup: add `tools/check_meta_registry.py` invocation to `build.sh` so the discipline is auto-enforced

---

### F3 — MEDIUM — `calls_graph_diff.sh verify` is invalid syntax

**Evidence:** Plan body line 457 says `tools/calls_graph_diff.sh verify` and the verification gate "expect: NONE."

`tools/calls_graph_diff.sh` (lines 1-12 of docstring): "Usage: `./tools/calls_graph_diff.sh`" — **no subcommand**. Outputs orphan list to stdout; empty = clean.

**Severity:** MEDIUM. Coder will get an error or unexpected behavior trying to run with the `verify` arg.

**Fix:** Replace line 457 + line 537 with:
```
tools/calls_graph_diff.sh                # expect: empty output (no orphans)
```

---

### F4 — LOW — Sub-master file:line ref STALE (predecessor docs only; plan body wins)

**Evidence:** Sub-master line 294 says `CoreFrameworks/CfgFieldRegistry.hpp:144-145` for `STAMP_BOUND_CFG_DERIVED` bit. Actual location: line 149 (verified). Plan body cites the correct line 149 throughout. Sub-master is the older sibling doc.

**Severity:** LOW. Plan body wins per handoff convention; sub-master is reference/scope only.

**Fix:** Suggest a one-line correction to sub-master line 294 for cold-pickup accuracy. NOT blocking.

---

### F5 — MEDIUM — Sidecar test code uses `SECTION(...)` macro that does NOT exist in `controller_test.cpp`

**Evidence:** Sidecar test examples (lines 95, 250, 258, 320, 507, 513, 518) wrap test blocks in `SECTION("...")` calls. But the actual test harness uses bare `check(name, condition)` calls — no SECTION wrapper (verified: `grep -n "SECTION(" tests/controller_test.cpp` returns empty).

**Severity:** MEDIUM. Coder will compile-error trying to paste sidecar examples verbatim. Must translate each block to bare `check()` calls.

**Fix:** Either (a) add a one-line note at top of sidecar Step 1 explaining `SECTION` is for clarity in the example and should be dropped or translated, or (b) rewrite sidecar test blocks to use the actual `check(name_string, condition)` pattern. Option (b) preferred for first-time-implementer convenience.

---

### F6 — LOW — Sidecar Step 3 uses non-canonical `ControllerConfig<64> cfg{};` zero-init

**Evidence:** Sidecar line 336: `ControllerConfig<64> cfg{};` (default-init zero). All other test sites (verified at `controller_test.cpp:4381,4408,4431,4588,4618,4774`) use `ControllerConfig<64> cfg = ControllerConfig_Default<64>();` (explicit Default function).

**Severity:** LOW. Difference is `{}` zero-init vs default-init via fn. For walker-stub-no-op test the difference shouldn't matter, but non-canonical pattern can mask actual default-value semantics later.

**Fix:** Replace with `ControllerConfig_Default<64>()` for consistency.

---

### F7 — LOW — Plan body lacks explicit `tools/check_per_core_registry_integrity.py` GREEN verification at Step 7

**Evidence:** `build.sh:260` invokes `check_per_core_registry_integrity.py` as part of build. Plan body Step 7 lists `./build.sh test` (which triggers the check transitively) but doesn't explicitly call out that "6 checks PASS + 0 Section C exemptions" stays GREEN. The predecessor `.F.4d` ship verification gate did call this out (per postmortem).

**Severity:** LOW. The check fires automatically via build.sh; explicit callout is hygiene-level.

**Fix:** Add to plan body verification gate (line 522 area): "tools/check_per_core_registry_integrity.py GREEN (6 checks PASS + 0 Section C exemptions; per `.F.4d` precedent)."

---

### F8 — LOW — DESIGN_SPECS catalog doesn't list `.F.4d.1.A` as application; auto-write at ship close should verify

**Evidence:** Plan body line 664 says "verify `metadata-bit-driven-derived-filter-framework.md` Stage 3 ACTIVE first canonical application = `.F.4d.1.A`". The spec (line 4) already says "first canonical reference application landed at v5.15.5.F.4d ship close" — that was Thread A foundation (bit reservation). The actual first **structural** application is `.F.4d.1.A`. The spec has v1.1 banner (line 93) noting macro signatures revised at `.F.4d.1` but still references v1.0 LOCKED-param signatures inline at line 137 — pending full doc cleanup at `.A` ship close (per banner).

**Severity:** LOW. Documented gap pending ship close. Ship close auto-write should remove the v1.0 inline references.

**Fix:** Plan body ship-close ritual (line 664) explicitly says "rewrite line 137+ inline macro signature examples in `metadata-bit-driven-derived-filter-framework.md` to remove LOCKED_HASH_VAR / FIXTURE_PATH params (matches v1.1 banner)."

---

## Unstated gaps (none material; all minor refinements)

- **(NIT)** Sidecar Step 2's macro lambda uses an `EmitCtx` struct declared inside macro expansion. Nested-struct-in-macro has subtle gotchas under some compilers (-Wpedantic). Mention as recovery note in "if something goes wrong" if expansion fails on suite/asan builds.
- **(NIT)** Plan body Step 1-3 says "expect 3174 + ~3 new tests GREEN" / "+ ~5" / "+ ~3" progressively, but these intermediate counts are speculative — test sections live in `controller_test.cpp` Step 6 (not landed until then). Suggest collapsing per-step expectations into single "Step 6: expect ~18 new tests" gate. Mild over-specification today.
- **(NIT)** Plan body line 692 references `feedback_consult_on_audit_findings` — confirmed in MEMORY.md index. Good practice cite.

---

## Punch list (resolve before tagging `pre-v5.15.5.F.4d.1.A`)

| # | Finding | Severity | Effort |
|---|---|---|---|
| 1 | Fix sidecar Step 4 FOREACH_REGISTRY tuple shape (4 cols, PARENT=FOREACH_REGISTRY) + plan body line 260 same | MEDIUM | 5 min |
| 2 | Fix plan body CI Check naming (lines 421, 533) — refer to `check_meta_registry.py` tool, not invented test names | MEDIUM | 5 min |
| 3 | Fix `calls_graph_diff.sh` invocation (no `verify` subcommand; lines 457, 537) | MEDIUM | 2 min |
| 4 | (Optional) Sub-master line 294 file:line ref correction (144-145 → 149) | LOW | 1 min |
| 5 | Sidecar test blocks: either annotate that `SECTION(...)` is descriptive-only, or rewrite to bare `check()` pattern | MEDIUM | 10 min |
| 6 | Sidecar line 336: `ControllerConfig<64> cfg{}` → `ControllerConfig_Default<64>()` | LOW | 1 min |
| 7 | Add explicit `check_per_core_registry_integrity.py` GREEN line to plan body Step 7 verification gate | LOW | 2 min |
| 8 | Ship-close auto-write (line 664): rewrite `metadata-bit-driven-derived-filter-framework.md` line 137+ inline LOCKED examples per v1.1 banner | LOW | 5 min at ship close |

**Total: ~30-45 min focused amends.**

---

## What's working well (capture for reuse)

- **Option F discipline correction at first-application time** is exemplary: caught LOCKED-const Class 18 mirror BEFORE the spec became authoritative; per `pattern-codification-lifecycle.md` Stage 3 first-reference revision allowance
- **H1-H20 audit table** (plan body lines 69-90) is concrete + every row has a "how preserved" cell — easy to verify; should become a plan-template element going forward
- **Sidecar's "Design decision: X chose Y because Z" callouts** (lines 86, 88, 237, 240, 310, 460) capture architectural intent at planning time, exactly per CLAUDE.local.md "Sub-plan sidecar files" rule (set 2026-05-16 — first applied here!)
- **"At `.A` landing — empty body case"** discussion (plan body lines 293+, sidecar 501+) is a beautiful intent specification — invariants exercise zero rows now, same invariants exercise N rows after `.B` lands them. Pattern reusable across all framework-then-consumers ship pairs
- **Pre-coding rollback anchor `pre-v5.15.5.F.4d.1.A` GPG-signed** + 5-binary build matrix verify (test/gui/suite/tsan/asan) — discipline is internalized

---

## Recommendation

**YELLOW — minor amend (~30-45 min focused).**

Findings F1, F2, F3, F5 (all MEDIUM) each represent a single mid-Step "wait, this doesn't compile / this command doesn't work" stall. Together they'd cost 20-40 min during coding to discover + resolve. Fixing up front is cheaper.

After amend → **GREEN**: tag `pre-v5.15.5.F.4d.1.A` + start Step 0.

---

## Cross-references

- Sister audits run in this gate cycle: `parity-check-2026-05-16-v5.15.5.F.4d.1.A.md`, `trace-deps-2026-05-16-v5.15.5.F.4d.1.A.md`, `dod-audit-2026-05-16-v5.15.5.F.4d.1.A.md` (all in `plans/plan_checks/`)
- Audit-gate handoff: `plans/v5.15-live-readiness/handoffs/2026-05-16-v5.15.5.F.4d.1-audit-gate-handoff.md`
- Predecessor postmortem: `plans/v5.15-live-readiness/postmortems/2026-05-16-v5.15.5.F.4d-merged-postmortem.md`
- Per `feedback_consult_on_audit_findings`: consult Caramel on these findings before resolving + tagging.

**End of /readiness report.**
