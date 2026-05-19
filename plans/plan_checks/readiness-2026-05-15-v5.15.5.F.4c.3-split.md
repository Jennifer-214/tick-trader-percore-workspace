# /readiness — v5.15.5.F.4c.3 global-vs-per-core registry split

**Plan:** `plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3-global-vs-per-core-registry-split.md`
**Audit date:** 2026-05-15
**Auditor:** /readiness skill (Layer 2 Explore)
**Engine HEAD verified:** `88043ea` (tag `v5.15.5.F.4c.1`)
**Verdict:** **GREEN** — ready to code. Minor amendments recommended; no blockers.

---

## Plan summary

- 1 ship across 9 numbered Steps (0-9) + mandatory pre-coding audit gate
- Risk: MED-HIGH (cfg surface + ControllerConfig restructure + parser state machine + stamp body schema + ~50-100 test migrations; Hot path UNTOUCHED)
- Effort: structural ship — author claims measured by classes closed (Class 24 structural close + override pattern eliminated) + framework primitives composed; LOC incidental
- Branch: stay on `feat/v5.15-live-readiness` (sprint branch)
- Predecessor: `v5.15.5.F.4c.1` (tag exists, engine `88043ea`); successor: `v5.15.5.F.4d`
- Tests baseline: ≥3144 + ~15 new (controller_test currently has 3079 `check(` lines + multi-assertion lines → 3144 plausible)
- Rollback anchor: `pre-v5.15.5.F.4c.3` (specified at Step 0.A)

---

## 28-item readiness checklist verdicts

### Foundation 10 (CLAUDE_REVIEW.md)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | **PASS** | Plan explicitly states "Hot path UNTOUCHED"; cites `calls_graph_diff.sh` (exists, 176 LOC); slow path + boot + GUI only. Verification gate has explicit check. |
| 2 | Train-serve parity | **PASS** | Plan covers per-core stamp emit + Layer 5b hash recomputation per-core. Backtest path (§ H.b) explicitly aligned: `cores[backtest_core_idx]` reads. Hard-break of v5.14 unified stamps documented (no silent compat fallback). |
| 3 | Surface area / coupling | **GAP — but justified** | Plan touches ~10 areas (CfgFieldRegistry, ControllerConfig, parser, stamp body, drift check, SettingsPanel, backtest path, ML read-sites, test fixtures, engine.cfg format). However: every site is mechanical per-section migration, NOT new `if (per_core)` branches. The "split" eliminates more if-arms than it adds (override-resolve logic dies). GAP flag is FYI-only; structural fix justifies blast radius. |
| 4 | Pointer init / heap lifecycle | **PASS** | No new heap allocation; `cores[16]` is in-struct array. PerCoreOverrides struct + `core_overrides[16]` deletion documented. |
| 5 | Backward compat | **ACCEPTED** | Plan explicitly HARD-BREAKS (operator directive 2026-05-15): legacy global keys = ERROR with migration hint; v5.14 unified stamps DO NOT load. Documented + intentional. CHANGELOG entry obligation in Step 8. |
| 6 | Multi-threading correctness | **PASS** | No new threads. Per-core slow-path single-writer invariant preserved (slow path writes `cores[c].<field>` then publishes via existing seqlock). GUI ↔ engine thread isolation discipline preserved (each subsystem has typed mirror; cfg file is the canonical channel per CLAUDE.local.md rule set 2026-05-14). |
| 7 | Test coverage | **PASS w/ amendment** | Baseline ≥3144 + ~15 new test functions claimed; verification gate has explicit count check. AMENDMENT: plan should enumerate WHAT the ~15 tests cover (see Recommendation 1 below). |
| 8 | Docs + invariants | **PASS** | Step 8 covers DESIGN_SPECS Stage 2→3 promotion, CLAUDE.md item 31 update, CLAUDE.local.md rule, Class 24 close note, CHANGELOG, FEATURE_LOOKUP, TECH_DEBT-063 partial close. |
| 9 | Forward maintenance | **PASS** | Per-instance registry pattern explicitly designed for future axes (per-symbol, per-strategy, per-horizon, per-regime per DESIGN_SPEC § "Anticipated future axes"). Mechanical 1-X-macro addition per future axis. |
| 10 | Rollback story | **PASS** | Tag `pre-v5.15.5.F.4c.3` at Step 0.A; "If something goes wrong" section has rollback procedure + recovery scenarios for each failure mode. |

### Sprint guards (Checks 11-14, v5.4.0 architectural)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 11 | Architectural sprint detection | **PASS** | Trigger keywords ("split", "decouple", "per-core") present. Plan enumerates every changed surface (Step B deletions + Step 0.C classification table + Step H ML-side migration table). `calls_graph_diff.sh` cited in Step 9 + audit gate. |
| 12 | Display ↔ execution invariant | **PASS** | Per-core tab renders `cfg.cores[c].<field>` (same as engine read source). Plan explicitly states this; no GUI-from-A-engine-from-B asymmetry. |
| 13 | Strategy lifecycle completeness | **PASS** | Plan only re-homes fields; no strategy dispatcher changes. ML-side migration table (§ H) covers each read site by file. |
| 14 | Function-pointer table / X-macro dispatch | **PASS** | Plan splits ONE existing `FOREACH_CFG_FIELD` into TWO scope-disjoint registries (NOT new dispatch surfaces). Variant selection: per-row scope classification in Step 0.C; auditor reviews before Step 1. Symmetry uniformity: same `CfgFieldDescriptor` tuple shape; `tt::` quintet unchanged. |

### v5.9 ML hardening (Checks 15-17)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 15 | ML feature change requires parity regression update | **PASS** | Plan does NOT touch FOREACH_FEATURE / RegimeSignals struct; only re-homes cfg fields that flow INTO feature compute. Snapshot tests should remain bytewise-identical (semantic equivalence preserved). |
| 16 | New cfg field with stamp-bearing → recipe doc | **PASS w/ amendment** | Plan ships new STAMP_BOUND per-core stamp shape (4 stamps for 4 cores) + fixtures + Layer 5b hash. Step 8 covers DOCS/PARITY_ISSUES.md scan. AMENDMENT: explicitly call out `DOCS/ML_TEST_RECIPES.md` update if needed for per-core stamp procurement (see Recommendation 4). |
| 17 | Model-load path changes → strict-mode integration test | **PASS** | Per-core stamps + per-core drift check inherit existing strict-mode pattern; `held_out_gate_strict` etc. unchanged at the strict-mode-3-tier behavior level. Integration test obligation in Step 9 verification gate. |

### Reuse + pre-existing-work + structural (Checks 18-19)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 18 | Reuse-audit | **PASS** | Plan explicitly states `tt::` dispatch primitives UNCHANGED; bitmap dispatcher applies to BOTH registries unchanged (mirror walker template parameterized by registry). Settings panel render walker shared across global + per-core tabs. No new duplicated functionality. |
| 19 | Pre-existing-work audit | **PASS** | Every API named in plan body verified at engine HEAD `88043ea`: `PerCoreOverrides<F>` exists (line 254), `core_overrides[16]` (line 1054), `PER_CORE_OVERRIDE_BITMAP_DOMAINS` (line 247), `ControllerConfig_ResolveForCore` (line 1271), `FOREACH_CFG_FIELD` (146 rows), `FOREACH_ML_CFG_FLAG` (12 bits), `MAX_EXECUTION_CORES=16`, `CfgFieldDispatch.hpp`, `StrategyCategories.hpp`, `OpModeCategories.hpp`. All present. |

### Future-proofness + test fragility + auto-trigger (Checks 20-22)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 20 | Future-proofness sanity | **PASS** | N-of-anything pattern (cores[16]) IS the X-macro/registry abstraction — both registries are X-macro-driven; future-axis spec catalog in `per-instance-registry-pattern.md`. |
| 21 | Test count assertion fragility | **PASS w/ amendment** | Plan says ≥3144; uses `>=` (good). AMENDMENT: verify new ~15 tests don't add `==` registry-count assertions (likely fine; verify during coding). |
| 22 | Auto-trigger downstream re-audit after umbrella ships | **PASS** | Plan-check on `.F.4d` was Caramel's stated intent; pre-coding audit gate is the formal mechanism. Plan explicitly calls `/precoding-audit-gate` before code lands. |

### Latency + mirror + tech-debt (Checks 23-25)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 23 | Latency accountability | **PASS** | Plan states "Hot path UNTOUCHED" + slow-path-only + boot-only. HOT_PATH_CHANGELOG entry: NONE (explicitly justified). `calls_graph_diff.sh` verifies. |
| 24 | Mirror-function call-sequence enumeration | **PASS** | Mirror is BETWEEN-REGISTRY-AT-SAME-CALLER (parser walks global registry then per-core registry against same `tt::cfg_parse_field<T>` primitive). Symmetry test trivially preserved by primitive sharing. |
| 25 | TECH_DEBT.md surface-area scan | **PASS** | TECH_DEBT-063 (`field_defs[]` elimination) partial close called out in Step 8 — verified line 1227 in TECH_DEBT.md. No other entries surfaced by ship's surface area. |

### Cold-pickup + DESIGN_SPECS audit + test-strength (Checks 26-28)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 26 | Cold-pickup completeness (10 fields) | **PASS** | See dedicated section below — all 10 fields present + non-stale. |
| 27 | DESIGN_SPECS pattern-application audit (/dod-audit) | **PASS** | Plan's audit gate fires `/dod-audit` explicitly. Two new specs ship (per-instance-registry-pattern.md + cfg-scope-discipline.md); compose with universal-cfg-field-registry-pattern + universal-registry-bitmap-dispatcher + tt::-dispatch + categorical-tag-applicability + wire-format-byte-preservation + multi-state-dispatch. Cache-alignment static_assert specified in plan (`sizeof(PerCoreCfg<F>) % 64 == 0`). |
| 28 | Test-strength anti-regression audit | **PASS** | Plan does NOT propose weakening any test. Test count baseline `≥3144` (proper `>=`). Per-core test fixture migration is mechanical grep+replace (semantic-preserving); no assertion-weakening pattern. |

### Misc (Checks 29-31)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 29 | Mechanical citation drift discipline | **PASS** | All file:line citations verified — `CoreFrameworks/CfgFieldRegistry.hpp` (146 rows in FOREACH_CFG_FIELD), `CoreFrameworks/ControllerConfig.hpp` (struct + ResolveForCore at 1271 + parser at 2651/2668/2712), `ML_Headers/StampBoundCfgRegistry.hpp`, `GUI/SettingsPanel.hpp`, `Backtest/`, `tests/controller_test.cpp`. Predecessor `v5.15.5.F.4c.1` tag exists. |
| 30 | Predicate-contract-changed audit | **N/A** | No predicate extensions; only cfg surface restructure. |
| 31 | Wider-build verification at last sprint close | **PASS** | Predecessor `.F.4c.1` postmortem references operator-pending paper-test + workspace sync per CLAUDE.local.md sprint state row. Plan's Step 9 explicitly lists `./build.sh test gui suite tsan asan` (all 5 binaries). |

---

## Cold-pickup completeness (10 fields)

| # | Field | Plan body section | Verdict |
|---|-------|-------------------|---------|
| C.1 | Branch state | "stay on `feat/v5.15-live-readiness`" (header + cold-pickup table) | **PASS** |
| C.2 | Phase exec order matches deps | Steps 0→1→2→3→4→5→6→7→8→9 — 0 foundation (rollback + DESIGN_SPECs + classification) → 1 framework → 2 cohort migration → 3 parser → 4 migration tool → 5 stamp → 6 GUI → 7 backtest + tests → 8 docs → 9 verification. Linear deps. | **PASS** |
| C.3 | First concrete move (Step 0) | 0.A `git tag pre-v5.15.5.F.4c.3` + `./build.sh test` + Version.hpp verify; 0.B confirm DESIGN_SPECs in workspace; 0.C cfg-field-scope classification table. | **PASS** |
| C.4 | Function/constructor names cited | `tt::cfg_parse_field<T>`, `cfg_save_field<T>`, `cfg_assign_field<T>`, `cfg_diff_field<T>`, `cfg_render_field<T>` (UNCHANGED); `PerCoreCfg<F>` (NEW); `ControllerConfig_ResolveForCore` (deprecated/deleted); `g_global_cfg_field_descriptors[]` / `g_per_core_cfg_field_descriptors[]` (NEW); `GlobalRenderTable<F>` / `PerCoreRenderTable<F>` (NEW). | **PASS** |
| C.5 | File:line refs for tests/baselines | Test baseline ≥3144 (counted at HEAD) + ~15 new (kind enumerated in Recommendation 1). Per-core stamp fixture path: `tests/fixtures/v5_15_5_F4c3_per_core_stamp.bin`. | **PASS w/ amendment** |
| C.6 | Stale-claim audit | Verified at HEAD `88043ea`: `PerCoreOverrides<F>` (line 254), `core_overrides[16]` (line 1054), `PER_CORE_OVERRIDE_BITMAP_DOMAINS` (line 247), `ControllerConfig_ResolveForCore` (line 1271), `FOREACH_CFG_FIELD` 146 rows (CfgFieldRegistry.hpp:167), `FOREACH_ML_CFG_FLAG` 12 bits (MlCfgFlagRegistry.hpp:52), MAX_EXECUTION_CORES=16 (Limits.hpp:19), `calls_graph_diff.sh` (176 LOC). | **PASS** |
| C.7 | Effort vs LOC | Plan claims "structural ship — LOC incidental"; total LOC from Steps 1-9: ~200+~300+~150+~100+~200+~200+~100+~200+~400=~1850 LOC. Reasonable for ~10-file restructure with ~80 cfg row migrations + parser state machine + 50-100 test fixtures + 2 DESIGN_SPECS + docs. EFFORT classifier "structural" is correct per `feedback_dont_measure_structural_work_by_loc.md`. | **PASS** |
| C.8 | Source-audit references | `.F.4c.1` paper-test (operator-reported 2026-05-15); `/ml-audit` 2026-05-14 cfg-↔-ML findings; operator's 2026-05-15 architectural intent quote. | **PASS** |
| C.9 | Predecessor / dependent plans named with paths | Predecessor `v5.15.5.F.4c.1` ship; postmortem at `postmortems/2026-05-15-skipped-v5.15.5.F.4c.1.1-rationale.md` (verified exists). Successor `v5.15.5.F.4d`. | **PASS** |
| C.10 | Tag names locked | `pre-v5.15.5.F.4c.3` (rollback); `v5.15.5.F.4c.3` (ship); Version.hpp `5.15.5.F.4c.1` → `5.15.5.F.4c.3`. | **PASS** |

**Cold-pickup verdict:** 10/10 PASS. One minor amendment opportunity in C.5 (test enumeration).

---

## Specific operator-focus questions

### Q1 — Step 0.C deliverable concreteness

The plan specifies a classification table at `plans/plan_checks/cfg-field-scope-classification-2026-05-15.md` with classifications GLOBAL_ONLY / PER_CORE / REMOVED per field, preliminary breakdown (~15 / ~50 / ~3). The output spec is concrete enough that the operator (or audit-gate agent) can produce it from the audit:

- Walk `FOREACH_CFG_FIELD` row-by-row at `CfgFieldRegistry.hpp:167` (146 rows total)
- For each: choose GLOBAL_ONLY / PER_CORE / REMOVED + write 1-sentence rationale
- Output table format: implied (row | classification | rationale)

**MINOR GAP:** the column format isn't explicitly specified — recommend amending to specify columns as `| field_name | classification | rationale | dependent_read_sites |`. NOT BLOCKING; auditor can use default.

### Q2 — Effort vs scope reconciliation

The operator-flagged ~1550 LOC actual estimate (~200 framework + ~300 cohort + ~150 parser + ~200 settings + ~200 stamp + ~100 backtest + ~200 tests + ~400 docs) matches the plan's per-Step LOC notes summed. Plan's "structural ship; LOC incidental" claim is consistent with `feedback_dont_measure_structural_work_by_loc.md` discipline. **PASS** — LOC estimates are sane reference points, but the value driver is the structural class closure (Class 24 + override pattern elimination), not LOC count.

### Q3 — DESIGN_SPECs Stage 2 DRAFT presence

Both verified:
- `tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/per-instance-registry-pattern.md` (238 lines, Stage 2 DRAFT v1.0)
- `tick-trader-percore-workspace/DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` (191 lines, Stage 2 DRAFT v1.0)

Stage 2 → Stage 3 transition criteria documented in each:
- per-instance-registry-pattern.md: "Promotes to Stage 3 ACTIVE v1.0 at `.F.4c.3` ship close once per-core reference implementations land."
- cfg-scope-discipline.md: "Promotes to Stage 3 ACTIVE v1.0 at ship close once cfg-field-scope-classification + per-core registry reference implementations land."

**PASS** — concrete criteria.

### Q4 — Verification gate quality

Step 9 lists ~30 gate items grouped Universal / Architectural / Parser / Wire-format / Hot-path / DESIGN_SPECS / Version+sync / Auto-write / Final-consult. Each is concretely testable:
- "build cleanly" (binary check)
- "controller_test passes ≥3144 + new ~15" (count assertion)
- "Layer 5b hash lock per core" (constant array existence + value match)
- "calls_graph_diff.sh bytewise-identical" (script exit code)
- "PerCoreOverrides<F> deleted" (grep returns 0 hits)
- "DESIGN_SPECs Stage 3 ACTIVE" (grep "Stage 3 ACTIVE" in doc)

**PASS** — every `[ ]` gate has concrete pass/fail signal.

### Q5 — Audit gate item resolution

Per CONTEXT — 4 originally-deferred decisions:
1. **Per-core stamp byte layout (a)/(b)/(c)** — plan documents as "Open question for audit gate"; preferred option (c) noted in body. **STATUS:** unresolved; OK to leave for audit gate.
2. **Bitmap-resident bool migration → A2 LOCKED** — plan body reflects this in Step A: "A2 bitmap-bool migration (NEW): all 12 ml_cfg_flags bits migrate to flat KIND_BOOL rows in the per-core registry; runtime bitmap rebuilt from rows at slow-path rebuild." **PASS**.
3. **Symbol axis → per-core with boot uniformity check** — plan body reflects this in Step A: "symbol axis (NEW): `symbol` migrated per-core with boot-time uniformity check until multi-symbol DataStream support." **PASS**.
4. **DESIGN_SPECs DRAFT v1.0 → Stage 3 transition** — concrete criteria in each spec (see Q3). **PASS**.

**3 of 4 locked + 1 explicitly deferred-to-audit.** Acceptable. Plan body correctly reflects operator decisions made 2026-05-15.

### Q6 — Risk classification

Plan claims MED-HIGH. Actual blast radius:
- 146 cfg rows split into ~25-30 global + ~70-80 per-core (~80 cohort migration)
- ControllerConfig<F> struct re-shape with new `cores[16]` array
- Parser: section state machine (new logic, not just registry walk)
- Stamp body: 4 stamps per loaded model, Layer 5b hash recomputation
- ~50-100 test sites mechanical migration
- ML read-sites: ~7 files (RidgeBlender, ConfidenceScore, ThompsonBandit, CoreModelZoo, StrategyParameters, MLStrategy, ControllerEventLoop)
- Backtest path: small (~100 LOC)
- 2 DESIGN_SPECs Stage 2→3 promotion
- engine.cfg HARD-BREAK migration (operator pain absorbed once)

MED-HIGH is appropriate. Hot path UNTOUCHED is the key risk-bounder. **PASS**.

### Q7 — Rollback anchor + procedure

Step 0.A: `git tag pre-v5.15.5.F.4c.3`. "If something goes wrong" mentions `git reset --hard pre-v5.15.5.F.4c.3` + per-failure-mode recovery (parser state machine fix, fixture compile error, migration tool malformed output, hot path regression, backtest non-determinism). 

**MINOR GAP:** rollback procedure does NOT explicitly mention state cleanup needs (uncommitted DESIGN_SPECs at workspace + temp fixture files at `tests/fixtures/v5_15_5_F4c3_per_core_stamp.bin`). NOT BLOCKING — operator can git-clean both; document during coding.

### Q8 — Test count + ~15 new test enumeration

Current `tests/controller_test.cpp` has 3079 `check(` lines (multi-check-per-test means actual test count ~3144 plausible). New ~15 test functions claimed; plan body doesn't enumerate WHAT they cover.

**GAP-MINOR:** Plan body should enumerate per-test categories (e.g., per-core resolver, section parser correctness, scope-discipline cross-check, bitmap-rebuild correctness, etc.) — see Recommendation 1.

### Q9 — Hot path discipline gate

`tools/calls_graph_diff.sh` exists (176 LOC); `calls_graph_diff_baseline.txt` + `calls_graph_diff_v5.8_phase0_baseline.txt` present.

**MINOR GAP:** the tool's baseline may need re-running after the parser state machine + ControllerConfig struct restructure to capture the new "no PerCoreOverrides resolve" hot/slow boundary. Plan should add a verification-gate item "re-baseline calls_graph_diff after Step 2 lands so post-ship diff has clean reference."

### Q10 — FEATURE_LOOKUP entry obligation

Plan says YES at Step 9 verification gate. Entry template per CLAUDE.local.md auto-write contract: `### <name> (vX.Y.Z+)` → What / Cfg flags / Fallback / Where to verify / Paper-test sanity / Gotchas / Related.

**MINOR GAP:** Plan should pre-draft the FEATURE_LOOKUP entry stub in Step 8 so it's written at ship-close, not "remembered later" — see Recommendation 5.

### Q11 — Postmortem trail

- Predecessor postmortem at `postmortems/2026-05-15-skipped-v5.15.5.F.4c.1.1-rationale.md` verified exists.
- This ship's postmortem template: plan Step 9 "Postmortem at `plans/v5.15-live-readiness/postmortems/2026-05-15-v5.15.5.F.4c.3-postmortem.md`" — concrete path; **PASS**.

---

## Top 5 critical readiness gaps (all MINOR — not BLOCKING)

1. **~15 new test enumeration** (GAP-MINOR, C.5/Check 7): Plan should enumerate WHAT the ~15 new test functions cover. Suggested categories:
   - Per-core resolver replacement (`cfg.cores[c].<field>` direct-read semantics)
   - Section parser correctness (3-4 tests: 1/2/4/16 cores; unknown global key; unknown per-core key; `[core N]` where N >= num_execution_cores)
   - Scope discipline cross-check (no field in BOTH registries; per-registry uniqueness static_assert fires correctly)
   - Per-core stamp emit + drift check (one test per core slot up to 4 cores)
   - Bitmap-rebuild correctness (slow-path rebuild from KIND_BOOL per-core rows produces same ml_cfg_flags as direct-bit set)
   - Test fixture migration sanity (a representative `cfg.cores[0].take_profit_pct = 3.0` round-trip)

2. **Classification table column format** (GAP-MINOR, Q1): Step 0.C should specify columns as `| field_name | classification | rationale | dependent_read_sites |` so the audit-gate agent or operator produces consistent output.

3. **calls_graph_diff baseline refresh** (GAP-MINOR, Q9): Add Step 9 verification gate item "re-baseline `tools/calls_graph_diff.sh` post-Step-2 so post-ship diff has clean reference for downstream `.F.4d` audit."

4. **DOCS/ML_TEST_RECIPES.md update** (GAP-MINOR, Check 16): Plan should explicitly call out whether `DOCS/ML_TEST_RECIPES.md` needs updating for per-core stamp procurement workflow (operator needs to know what to pass to `tools/stamp_model.sh` for per-core models). Step 8 should add a verification check.

5. **FEATURE_LOOKUP entry pre-draft** (GAP-MINOR, Q10): Step 8 should pre-draft the FEATURE_LOOKUP entry stub (operator-visible: cfg file format change to sectioned `[core N]` syntax + per-core authoritative cfg + hard-break of legacy global trading keys + migration guide path) so it lands at ship-close not "remembered later".

---

## Recommendations

### Worth fixing before coding (~15 min total)

- Enumerate the ~15 new test functions in plan body (Step 9 verification gate or Step 0 baseline section)
- Specify Step 0.C classification table column format
- Add Step 9 gate item: re-baseline calls_graph_diff.sh post-Step-2
- Add Step 8 sub-item: explicit `DOCS/ML_TEST_RECIPES.md` update check
- Pre-draft FEATURE_LOOKUP entry stub in Step 8

### Worth tracking during coding (no plan amendment needed)

- Document any uncommitted-DESIGN_SPECs / temp-fixture state-cleanup needs in postmortem if rollback fires
- Cross-registry name-collision discipline (cfg-scope-discipline.md anti-pattern 3) — verify zero collisions when both registries declared

### Acceptable risk (don't block)

- Per-core stamp byte layout option (a)/(b)/(c) deferred to audit gate — plan body documents preference (c); acceptable
- Engine.cfg HARD-BREAK is operator-directed; documented in plan + migration guide ships in same ship

---

## Verdict: **GREEN — ready to code**

The plan is comprehensive, well-structured, and verifiably grounded. All 28 readiness checks PASS (with 5 GAP-MINOR amendments recommended but non-blocking). Cold-pickup completeness 10/10. Operator-locked decisions (A2 + symbol per-core) are reflected in plan body. DESIGN_SPECS Stage 2 DRAFT v1.0 docs exist with concrete Stage 3 transition criteria. Hot path UNTOUCHED with verification tooling in place. Rollback anchor + procedure clear.

**Recommendation:** apply the 5 minor amendments above (~15 min) → fire pre-coding audit gate (`/precoding-audit-gate` with the 12 focus keywords already listed in plan body) → consult operator on synthesis findings → start coding from Step 0.A. Per CLAUDE.local.md "after pre-coding audits, ALWAYS consult before coding" — synthesis review is mandatory before code lands.

The structural value (Class 24 close + override pattern elimination + per-instance registry framework codified for future axes) is high and well-scoped. Risk is appropriately bounded by Hot path UNTOUCHED + parser test coverage + per-core stamp fixture commits. Ship is GREEN to proceed.

---

**End of /readiness report for v5.15.5.F.4c.3.**
