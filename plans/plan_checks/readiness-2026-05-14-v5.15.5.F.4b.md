# /readiness report — v5.15.5.F.4b-foreach-cfg-field-registry-implementation — 2026-05-14

**Plan path:** `/home/caramel/code/tick-trader-percore-workspace/plans/v5.15-live-readiness/subplans/2026-05-13-v5.15.5.F.4b-foreach-cfg-field-registry-implementation.md`
**Audited at HEAD:** engine `f72caef` (v5.15.5.F.3), branch `feat/v5.15-live-readiness`.
**Auditor:** /readiness Layer 2 (inline; no nested spawn) with Stage 0 DESIGN_SPECS preload.
**Sister audits in flight:** /parity-check + /trace-deps + /merge-scan + /dod-audit (independent).

---

## Plan summary

- **1 ship** (.F.4b) as first coding ship of the 9-sub-ship `.F.4` umbrella (followed by `.F.4c-.F.4i` + 3 `v5.15.6` follow-ons).
- **Goal:** establish `CfgFieldRegistry.hpp` + `CfgFieldDispatch.hpp` (tt::) + migrate KIND_DOUBLE/_PCT cohort (~40 fields). Bake in full descriptor design (128-byte; categorical + lives_in_struct + 10-bit metadata_flags). Add STAMP_BOUND derived filter + CI hash test. Optional stretch: X-macro-generated cfg struct fields.
- **Estimated effort:** ~700 LOC net (umbrella row says ~900 LOC) — internal inconsistency between plan body + umbrella table.
- **Predecessor:** v5.15.5.F.4a (design specs DONE in workspace; no engine tag — confirmed).
- **Successor:** v5.15.5.F.4c (KIND_INT + INT_ENUM + BOOL).

---

## Stage 0 — DESIGN_SPECS preloaded (matched plan surface keywords)

| Keyword | DESIGN_SPECS loaded |
|---|---|
| "new cfg field", "FOREACH_CFG_FIELD" | `cfg-flag-eligibility-criteria.md`, `categorical-tag-applicability-pattern.md`, `universal-cfg-field-registry-pattern.md` |
| "X-macro registry" | `x-macro-registry-with-presence-dispatch.md`, `autopopulate-pattern-for-production-caller-class.md`, `heterogeneous-registry-pattern.md` |
| "bit-pack / bitmap" | `bitmap-flag-api.md`, `bitmap-overflow-protection-discipline.md` |
| "K-state field" (touches .F.4f) | `multi-bit-state-encoding-pattern.md` |
| "stamp body / HMAC / STAMP_BOUND" | `wire-format-byte-preservation-discipline.md`, `pre-post-cfg-registry-split-for-emit-order-preservation.md` |
| "per-core override" | `per-bit-per-core-override-pattern.md` |
| "audit before coding" | `audit-driven-pre-coding-gate.md` |
| "slow-path cfg cache" | `slow-path-cfg-resolution-cache-pattern.md` |

All 8 pattern bodies held in context during checklist walk.

---

## 28-check verdict table

| # | Check | Verdict | One-line note |
|---|---|---|---|
| 1 | Hot-path purity | PASS | plan explicitly hot-path-clean (boot + 60 Hz GUI only) |
| 2 | Train-serve parity | PASS | KIND_DOUBLE/_PCT migration is structural; semantics unchanged; STAMP_BOUND derived filter preserves stamp body bytes via CI hash test |
| 3 | Surface area | PASS | 5 files touched (CfgFieldRegistry.hpp NEW + CfgFieldDispatch.hpp NEW + SettingsPanel.hpp + ControllerConfig.hpp + controller_test.cpp) — under 8-file ceiling |
| 4 | Pointer init / heap lifecycle | PASS | descriptor is static const POD array; no heap |
| 5 | Backward compat | PASS | no SHARDED_SNAPSHOT_VERSION / MODEL_FORMAT_VERSION touch; STAMP_BOUND derived filter EXPLICITLY locks byte order via CI hash |
| 6 | Multi-threading | PASS | boot + 60 Hz GUI only; no new thread / atomic / shared state |
| 7 | Test coverage | GAP | plan adds registry roundtrip test + static_assert tests; CI consistency tests deferred to "Deliverable C" without explicit per-test file:line counts |
| 8 | Docs + invariants | GAP | no DOCS/CHANGELOG.md update mentioned; no CLAUDE.md item update (this pattern would warrant promotion to item 31 after 2nd application per CLAUDE.local.md "Codify design principles") |
| 9 | Forward maintenance | PASS | X-macro is the structural fix per item 13/19/21; closes 5 recurring gap classes |
| 10 | Rollback story | PASS | `pre-v5.15.5.F.4b` tag at Step 0; convention matches predecessor `pre-v5.15.5.E` precedent |
| 11 | Architectural-sprint orphans | PASS | additive infrastructure (new files); no `calls_graph_diff.sh` orphan risk |
| 12 | Display ↔ execution invariant | PASS | no PerCoreSnap / hot-path field touch |
| 13 | Strategy lifecycle | PASS | StrategyCategories.hpp is NEW (no FOREACH_STRATEGY lifecycle touch); .F.4h is when categorical column lands on FOREACH_STRATEGY |
| 14 | X-macro variant selection | GAP | KIND enum exhaustiveness OK; **but** the X-macro tuple has 7 args in plan code samples (line 127) but 12-col Option D per umbrella ("largest Option D to date") — inconsistency in plan body. Step 4 EMIT_CFG_PARSER_CASE references 7 args; descriptor design wants 12 (kind/name/label/section/meta/payload/tooltip + 3 categorical + lives_in + 1 reserved). Must reconcile before coding. |
| 15 | ML feature change → parity regression | PASS | no FOREACH_FEATURE / FEATURE_REGISTRY_HASH touch |
| 16 | New stamp-bearing cfg → recipe update | PASS | STAMP_BOUND derived filter replays existing FOREACH_STAMP_BOUND_CFG byte-for-byte; CI hash test locks |
| 17 | Model-load path changes → strict-mode test | PASS | no model load path touch |
| 18 | Reuse-audit | GAP | **FOREACH_ML_CFG_FLAG / RISK / GATE / OPS / LIFECYCLE already exist (v5.14.9.F.5)** with similar AUTOPOPULATE shape + GUI field_defs[] auto-extend; plan does not enumerate how the new FOREACH_CFG_FIELD COMPOSES with the 5 existing domain registries. Plan implies they coexist but doesn't say. Risk: duplicate boolean fields in both registries, or developer confusion about which to use. Recommend a "Coexistence with FOREACH_*_CFG_FLAG" section. |
| 19 | Pre-existing-work audit (false-NEW + false-REUSE) | GAP — false-REUSE | **CRITICAL.** Plan cites these as REUSE: `CfgParser_HandleKV` (doesn't exist; actual surface is inline parser body in `ControllerConfig_Load<F>` at ControllerConfig.hpp:1798), `Cfg_Save` (doesn't exist; field_defs[]-driven save lives in GUI/SettingsPanel.hpp around line 512+1376), `Cfg_LoadFromString` + `Cfg_LoadFromFile` (don't exist), `parse_csv_engine_config` (doesn't exist). Step 4 says `rg "void.*Parse.*Cfg.*const char" CoreFrameworks/` will locate parser — that grep yields zero hits. **Plan must replace these names with `ControllerConfig_Load<F>`** + acknowledge the parser body is inline in the templated function. |
| 20 | Future-proofness (N-of-anything) | PASS | X-macro registry is the canonical future-proof shape; explicit 12-col tuple with `_reserved` headroom; metadata_flags has 6 bits unused; LivesInStruct enum has room for future cfg files |
| 21 | Test count assertion fragility | GAP | plan Step 6 says `controller_test passes (≥1822 + new parity tests)` — current is **3108** (just verified). Stale baseline by ~1286. Will read as "passes if reach 1822" which silently masks regressions. Update to ≥3108 or use named-symbol assertions. |
| 22 | Auto-trigger downstream re-audit | PASS | sprint umbrella explicitly enumerates 9 sub-ships with surface-touched table; each later ship reads from this descriptor design (locked at .F.4b) |
| 23 | Latency accountability | PASS | plan Step 6 says "HOT_PATH_CHANGELOG entry (NONE — boot/GUI only, no hot/slow-path impact)" — explicit + correct |
| 24 | Mirror-function call-sequence | PASS | not a mirror of an existing function; new registry surface |
| 25 | TECH_DEBT.md surface scan | FIXED-IN-PLAN | TECH_DEBT-009 (FOREACH_CFG_FIELD for non-boolean cfg, PARTIAL CLOSED v5.14.9.F.4) is the EXACT ledger entry this ship advances. TECH_DEBT-022 (engine.cfg parser perfect-hash) becomes more tractable post-migration. Plan Step 6 says "TECH_DEBT.md scan (CLOSE: 1-2 entries about parser drift class)" — correct intent; specific entries to close: TECH_DEBT-009 (full close pending .F.4c-.F.4i), TECH_DEBT-022 (note as predicate-precondition). |
| 26 | DEFERRED-FOR-FUTURE-SHIP placeholder | PASS | spec is reserved/empty per skill spec |
| 27 | DESIGN_SPECS pattern application (composes /dod-audit) | PASS | plan applies: X-macro registry (item 13), AUTOPOPULATE (item 21), BITMAP_* (item 20), tt:: dispatch (item 23), bitmap-overflow guards (per `bitmap-overflow-protection-discipline.md`), categorical applicability (per `categorical-tag-applicability-pattern.md`). Comprehensive pattern coverage. |
| 28 | Test-strength anti-regression | PASS | plan adds tests; no test weakening / deletion / strict-to-loose substitution proposed |
| 29 | Mechanical citation drift | GAP | see Mechanical Citation Drift table below — multiple file:line refs need correction (line 425 → 46; line 3206 → 2937; "~90 entries" → 65; function names entirely wrong) |
| 30 | Predicate-contract-changed | PASS | no predicate body modification (registry is data, not predicate extension) |
| 31 | Wider-build verification at last sprint close | FAIL | `git log --grep="gui suite tsan asan"` against v5.15.5.E close finds only the v5.15.2 commit (where Check 31 itself was added). No evidence the v5.15.5.E close ran `./build.sh gui suite tsan asan all`. Non-blocking but flags risk that GUI/sanitizer compile errors may surface during .F.4b's build verification (Step 6). |

---

## Mechanical citation drift findings

| Plan claim | Actual at HEAD | Verdict |
|---|---|---|
| `ControllerConfig.hpp parser location near line 2371-2381 for reconcile_mode-style precedent` | reconcile_mode parser at ControllerConfig.hpp:2525-2540 (not 2371-2381) | DRIFT — line shifted ~150 lines |
| `BacktestPanels.hpp:3206 for train_model_worker_fn` | train_model_worker_fn at BacktestPanels.hpp:**2937** | DRIFT — line shifted ~269 lines |
| `GUI/SettingsPanel.hpp ~line 425 for field_defs[]` | field_defs[] starts at SettingsPanel.hpp:**46**; line 425 is per_core_fields[] | DRIFT — wrong array; cite 46 (field_defs) or 305 (per_core_fields) |
| `GUI/SettingsPanel.hpp size estimate ~90 entries` | field_defs[] has **65** explicit entries + 5 X-macro FOREACH_*_CFG_FLAG expansions inserted at line 299-303 (boolean cfg flags already migrated) | DRIFT — recount; 65 manual + ~30 macro-expanded = ~95 effective |
| `CfgParser_HandleKV` | DOES NOT EXIST | MISSING — actual is inline body in `ControllerConfig_Load<F>` at ControllerConfig.hpp:1798 |
| `Cfg_Save` | DOES NOT EXIST | MISSING — save lives in `SettingsPanel.hpp` `fprintf(f, "%s=%s\n", key, value)` at line 512 + ad-hoc paths |
| `parse_csv_engine_config` | DOES NOT EXIST | MISSING — no such function |
| `Cfg_LoadFromString`, `Cfg_LoadFromFile` | DO NOT EXIST | MISSING — proposed test code in Step 6 won't compile against these names |
| `static_assert(sizeof(CfgFieldDescriptor) <= 64)` (Step 6 test code + Step "If something goes wrong") | Step 1 + DESIGN_SPECS both say `<= 128` | INTERNAL INCONSISTENCY — must reconcile to 128 |
| Test baseline "1822 tests passed" (Step 0 verification + Step 6 gate) | Actual is **3108** at HEAD | DRIFT — stale baseline; use ≥3108 |
| Version.hpp "5.15.5.F.3 → 5.15.5.F.4b" (Step 7) | Version.hpp currently reads **"5.15.5.E"** (not F.3) | DRIFT — see Version.hpp section below |
| Sprint umbrella `.F.4b` LOC est = "~900 LOC" | Plan body Step 0 says "~700 LOC net" | INTERNAL INCONSISTENCY — reconcile |

---

## Cold-pickup completeness (10 items)

| # | Item | Verdict |
|---|---|---|
| C.1 | Branch state | PASS — "stay on `feat/v5.15-live-readiness`" explicit |
| C.2 | Exec order matches deps | PASS — .F.4a → .F.4b → .F.4c → ... ordering correct |
| C.3 | First concrete move (Step 0) | PASS — `cd; git tag pre-v5.15.5.F.4b; ./build.sh test` |
| C.4 | Function/constructor names cited | FAIL — function names (CfgParser_HandleKV, Cfg_Save, parse_csv_engine_config, Cfg_LoadFromString, Cfg_LoadFromFile) all WRONG. Fresh session loses 30-60 min figuring out actual surface |
| C.5 | File:line refs for cited tests/baselines | FAIL — multiple incorrect line refs (see Mechanical Citation Drift table) |
| C.6 | Stale-claim audit | GAP — "1822 tests" stale to 3108; "5.15.5.F.3" Version.hpp stale to 5.15.5.E |
| C.7 | Effort claims reconcile with LOC | GAP — ~700 LOC (body) vs ~900 LOC (umbrella) inconsistency |
| C.8 | Source-audit references | PASS — DESIGN_SPECS docs cited; v5.14.9.F.5 precedent cited |
| C.9 | Predecessor / dependent plans named with paths | PASS — successor `.F.4c` path verifiable; `.F.4a` correctly noted as design-specs-only (no plan file) |
| C.10 | Tag names locked | PASS — `pre-v5.15.5.F.4b` + `v5.15.5.F.4b` listed |

**Cold-pickup verdict:** **YELLOW.** C.4 + C.5 fail force a fresh session to do its own audit of cfg parser/save surface (~30-60 min lost). C.6 + C.7 add another ~15 min. Total: ~1 h pre-coding re-audit needed before .F.4b can actually start.

---

## Sprint-wide concerns (descriptor design locks at .F.4b)

### Descriptor design sufficiency across all 9 sub-ships

Verified by reading all 8 sub-plans (`.F.4b` → `.F.4i`):

- **`.F.4c` (KIND_INT/INT_ENUM/BOOL)** — descriptor's `as_int` (24B) + `as_int_enum` (16B) + `as_bool` (8B) payload slots cover all three. PASS.
- **`.F.4d` (KIND_STRING/FILE_PATH + GUI metadata flags)** — `as_string` (24B) covers; HIDDEN_BY_DEFAULT / RESTART_REQUIRED / SAFETY_CRITICAL / IS_SECRET / AFFECTS_STAMP_PARITY / LOG_VALUE_FORBIDDEN are 6 of the 10 declared MetadataFlag bits. PASS.
- **`.F.4e` (ResolvedCoreCfg + slow-path)** — separate struct; descriptor unchanged. PASS.
- **`.F.4f` (K-state cohort)** — uses item 30 multi-bit pack OUTSIDE descriptor; descriptor unchanged. PASS.
- **`.F.4g` (per-core AoS-by-core re-layout)** — `PER_CORE_OK` flag drives emission; descriptor unchanged. PASS.
- **`.F.4h` (categorical audit + bitmap-overflow)** — populates `applies_to_strategy_cat` only; descriptor unchanged. PASS.
- **`.F.4i` (backtest.cfg)** — uses `lives_in_struct = STRUCT_BACKTEST_CFG`; descriptor unchanged. PASS.
- **`v5.15.6` (controller/secrets/training)** — uses `lives_in_struct` enum values 2/3/4 + `KIND_RANGE_INT/_DOUBLE` (reserved values 8/9). PASS — reserved values present.

**Verdict:** descriptor sufficient. The 128-byte budget + uint16_t metadata_flags + reserved Kind values 8/9 + 6 bits headroom in metadata_flags + 5 LivesInStruct values = correct lock at .F.4b. (Caveat: confirm `_reserved: 2 bytes` survives review — currently planned at "future use; zero-init".)

### Cohort consistency audit (per cfg-flag-eligibility-criteria.md "Cohort audit")

Plan lists 14 fields promoting to PER_CORE_OK in umbrella (correctly noted as 13 — minor typo in umbrella table header). Cohort families that need cross-checking at .F.4b registry row population:

- **momentum_* family (4 fields)** — all PER_CORE_OK per umbrella. PASS.
- **lazy_rebuild_* family (2 fields: force_period_us + price_threshold_pct)** — both PER_CORE_OK. PASS.
- **confidence_* family** — `confidence_hard_block_threshold`, `confidence_ic_floor`, `confidence_ic_floor_window` → PER_CORE_OK; rest (capacity_*, rmse_baseline, freshness_tau_secs) stay GLOBAL-ONLY (training-derived). Cohort-divided but rationale documented (item 21 separates training-time constants from runtime tuning). PASS — split is principled.
- **ridge_* family** — all GLOBAL-ONLY (training-time). PASS — coherent.
- **thompson_* family** — `thompson_rng_seed` PER_CORE_OK; `thompson_mu_prior` / `thompson_precision_prior` / `thompson_precision_obs` GLOBAL-ONLY. PASS — split justified by training-time-vs-runtime.

**Verdict:** all cohorts internally consistent OR explicitly justified.

### X-macro tuple width

Plan body uses **7-arg tuple** (`kind_token, name, label, section, meta, payload, tooltip`) in EMIT_* macros (line 127, 153-156, 180-188). DESIGN_SPECS doc + umbrella say **12-arg tuple** (adding `applies_to_strategy_cat`, `applies_to_op_mode_cat`, `applies_to_regime_cat`, `applies_to_risk_cat`, `lives_in_struct`). **INCONSISTENCY** — code samples in plan body must be updated to 12-arg tuple before coding starts; otherwise consumer macros silently drop the 5 trailing args.

### Reserved-default sentinel correctness

Plan says `applies_to_regime_cat` defaults to `REGIME_CAT_ALL = 0xFFFFu` (uint16_t all-bits). Same for `applies_to_risk_cat = RISK_CAT_ALL = 0xFFFFu`. GUI filter is `(applies_to & active_cats) != 0` — `0xFFFFu & anything_nonzero = nonzero` → permissive. **PASS.** Correctly permissive for v5.16 specialization later.

---

## Hidden scope detected

1. **Reconcile descriptor budget (Step 1 says 128 / Step 6 + recovery says 64)** — needs single-source decision. ~5 min.
2. **Reconcile LOC estimate (~700 LOC body vs ~900 LOC umbrella table)** — ~5 min.
3. **Reconcile X-macro tuple arity (7 in plan body code samples vs 12 in DESIGN_SPECS + umbrella)** — ~15 min to update all EMIT_* code samples.
4. **Correct function-name citations** (5 wrong: CfgParser_HandleKV / Cfg_Save / Cfg_LoadFromString / Cfg_LoadFromFile / parse_csv_engine_config) — must enumerate actual surface (`ControllerConfig_Load<F>` inline body + SettingsPanel.hpp save sites + new helpers needed). ~20 min.
5. **Correct file:line refs** (3 wrong: ControllerConfig.hpp 2371-2381 → 2525-2540; BacktestPanels.hpp 3206 → 2937; SettingsPanel.hpp 425 → 46) — ~5 min.
6. **Update test baseline (1822 → 3108)** — ~2 min.
7. **Address Version.hpp lag** (see dedicated section below) — needs operator decision before Step 7.
8. **Add "Coexistence with existing FOREACH_*_CFG_FLAG registries" section** to plan body (Check 18 gap). Explain: boolean-typed cfg flags already migrated; new FOREACH_CFG_FIELD covers DOUBLE/INT/STRING tail; no overlap. ~10 min.
9. **CHANGELOG.md update line missing** (Check 8) — add to Step 7. ~5 min.
10. **New CI consistency tests (categorical Deliverable C: tests/controller_test_categorical.cpp or extend)** — file path not specified; controller_test.cpp split rule (CLAUDE.md line "Test file size discipline" at 16k lines / 1822 sections) may require new test binary anyway. ~15 min planning.

**Total hidden scope:** ~80 min of plan corrections before coding can start cleanly.

---

## Version.hpp lag — discrepancy resolution

**Observed at HEAD:** `Version.hpp` reads `"5.15.5.E"`. Last 4 ships (`.F.1` / `.F.2` / `.F.3` / `.F.6`) bumped tags but did NOT bump Version.hpp.

**Evidence:**
- `git log -- Version.hpp` shows last bump at `5296e30 v5.15.5.E complete` (2026-05-13).
- `git log -10` shows 4 `.F.*` commits since the .E version bump; none touched Version.hpp.

**Memory ref:** `feedback_bump_version_per_ship.md` — operator caught this gap after 17 ships missed.

**Recommendation:** **NOT an intentional convention; this is the recurring gap class.** Two options:

- **Option A (canonical per memory):** Plan Step 7 should bump `5.15.5.E → 5.15.5.F.4b` (skipping the missed `.F.1/.F.2/.F.3/.F.6` intermediate). Document the skip in commit message: "Version.hpp lag from v5.15.5.E through v5.15.5.F.* sub-ships catches up at .F.4b per feedback_bump_version_per_ship.md."
- **Option B (catch-up dedicated ship):** Land a tiny `v5.15.5.F.7` ship that bumps Version.hpp to "5.15.5.F.6" first (matching last tag), then .F.4b bumps to .F.4b. Cleaner monotonic history; more commits.

**Preferred:** Option A. Simpler. Avoids extra commit. Caramel's intent per the memory is "Version.hpp tracks shipped state" — at .F.4b's ship time, that's `.F.4b`. The intermediate misses are documented in the commit message + closed.

**Update plan Step 7:** change `5.15.5.F.3 → 5.15.5.F.4b` to `5.15.5.E → 5.15.5.F.4b` with explanatory commit-message line.

---

## Punch list (must-fix before coding)

### RED (block coding)

1. **Function-name citations (false-REUSE)** — `CfgParser_HandleKV` + `Cfg_Save` + `Cfg_LoadFromString` + `Cfg_LoadFromFile` + `parse_csv_engine_config` DO NOT EXIST. Replace with actual `ControllerConfig_Load<F>` (inline parser body) + SettingsPanel save sites + new helpers as needed.
2. **X-macro tuple arity inconsistency (7 in plan code vs 12 in spec)** — choose 12 to match DESIGN_SPECS; update all EMIT_* code samples in Steps 3/4/5.
3. **Descriptor budget inconsistency** — Step 1 says 128, Step 6 + recovery section say 64. Reconcile to 128 per DESIGN_SPECS + latency-vs-cache framework.

### YELLOW (fix during coding setup — ~30 min)

4. **Test baseline stale (1822 → 3108).**
5. **Version.hpp lag** (Version.hpp shows 5.15.5.E; plan assumes 5.15.5.F.3) — adopt Option A: bump 5.15.5.E → 5.15.5.F.4b at Step 7.
6. **Mechanical line-ref drift** — 3 wrong line refs (ControllerConfig.hpp:2371 → 2525; BacktestPanels.hpp:3206 → 2937; SettingsPanel.hpp:425 → 46).
7. **LOC estimate inconsistency** (~700 body / ~900 umbrella).
8. **Add coexistence section** for existing FOREACH_*_CFG_FLAG registries.
9. **Add DOCS/CHANGELOG.md update line to Step 7.**

### DEFERRED (acceptable risk; document)

10. **CI hash test for STAMP_BOUND derived filter** — DESIGN_SPECS doc names constant `LOCKED_STAMP_BOUND_DERIVED_HASH_V5_15_5_F4`; plan correctly notes locking at .F.4b ship time. Document concrete locked value after first build.
11. **Check 31 (wider-build verification at v5.15.5.E close)** — no evidence. Non-blocking; .F.4b's own `./build.sh test gui suite tsan asan` will surface any latent GUI/sanitizer compile errors first.

---

## Sister-audit interactions

- **/parity-check:** likely surfaces STAMP_BOUND derived filter byte-order question — verify their finding aligns with Layer 5b CI hash test plan here.
- **/trace-deps:** likely surfaces the cfg field offset lookup design choice (Option A offsetof vs B member pointers); cross-check their recommendation against this audit's "Step 2 Option A" preference.
- **/merge-scan:** likely surfaces the coexistence question (FOREACH_CFG_FIELD vs FOREACH_*_CFG_FLAG). Treat as Check 18 confirmation; address in plan body.
- **/dod-audit:** likely confirms Check 27 PASS verdict (comprehensive pattern coverage); look for any single-instance category warning per categorical-tag-applicability-pattern.md Anti-pattern 2.

---

## Verdict: **YELLOW**

**Coding cannot start without addressing the 3 RED items** (~50 min total fix). Once RED is cleared, the YELLOW items become quick polish during Step 0 setup.

**Strengths:**
- Comprehensive DESIGN_SPECS pattern coverage (item 13/19/20/21/22/23 all applied)
- Descriptor design verified sufficient across all 9 sub-ships including v5.15.6
- Cohort consistency rigorously verified across momentum / lazy_rebuild / confidence / ridge / thompson families
- Sprint scope properly split (engine+backtest at .F.4 / controller+secrets+training at v5.15.6)
- All sub-ship plan files exist + chain correctly

**Weaknesses:**
- Mechanical citation drift (5 wrong function names, 3 wrong line refs, 1 stale test baseline, 1 Version.hpp staleness) — classic 1-2-sprint-old-plan symptom per Check 29
- Internal inconsistencies (descriptor budget 64 vs 128; tuple arity 7 vs 12; LOC 700 vs 900) — needs reconciliation pass
- Coexistence with existing FOREACH_*_CFG_FLAG registries unspecified (Check 18 gap)

**Estimated fix-up cost:** ~80 min before coding starts.

**Coding effort after fix-up:** plan body's "~700 LOC" estimate is plausible given the structural-fix nature; umbrella's "~900 LOC" is the more honest figure given 12-col tuple + 40 registry rows + descriptor + tt:: dispatch + 5 file touches + tests.

---

## Map-update suggestions (post-coding)

- **CODE_MAP regen:** after .F.4b ships, `./tools/gen_code_map.sh` should add `CfgFieldRegistry.hpp` + `CfgFieldDispatch.hpp` + new `Pattern_FunctionName` entries.
- **INVARIANTS_MAP update:** if v5.14.9.F.4 partial-close of TECH_DEBT-009 has invariant entry, update verdict to track .F.4b/c/d/e/g extension.
- **DESIGN_SPECS catalog (`DESIGN_SPECS/README.md`):** add `universal-cfg-field-registry-pattern.md` + `categorical-tag-applicability-pattern.md` if not yet indexed; both promote from DRAFT v1.0 to ACTIVE after .F.4b lands.
- **TECH_DEBT-009 status:** partial-close annotation update at .F.4b (DOUBLE/_PCT subset) + final close at .F.4d (STRING/FILE_PATH subset) + .F.4e (slow-path resolution).

---

## Recommendations summary

### Must fix before coding (~50 min)

1. Replace 5 wrong function-name citations with actual `ControllerConfig_Load<F>` + SettingsPanel save sites + new helpers.
2. Update EMIT_* code samples to 12-col tuple.
3. Reconcile descriptor budget to 128 in Step 6 test code + recovery section.

### Worth fixing during Step 0 (~30 min)

4. Update test baseline 1822 → 3108.
5. Adopt Version.hpp bump 5.15.5.E → 5.15.5.F.4b (Option A).
6. Update 3 wrong line refs.
7. Reconcile LOC estimate.
8. Add coexistence-with-FOREACH_*_CFG_FLAG section.
9. Add DOCS/CHANGELOG.md update to Step 7.

### Acceptable risk

10. CI hash test locked-constant placeholder (document concrete value after first build).
11. Predecessor wider-build verification absent (Check 31 FAIL non-blocking).

**Overall:** plan is structurally sound; coding can start once 3 RED items + ~30 min YELLOW polish are addressed.
