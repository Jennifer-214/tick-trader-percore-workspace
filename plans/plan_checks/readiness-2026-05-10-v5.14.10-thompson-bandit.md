# /readiness report — 2026-05-08-v5.14.10-bayesian-thompson-bandit.md — 2026-05-10

**Audited plan:** `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.10-bayesian-thompson-bandit.md`
**Audit kind:** Layer 2 single-pass (handoff-driven, full 28-check + cold-pickup 10-point)
**Codebase HEAD:** `feat/v5.14-foxml-port-and-maker` @ `490618b` (post v5.14.9 umbrella `b09b2d5`)
**Engine version:** 5.14.9 (Version.hpp:5)
**Plan freshness:** drafted 2026-05-08; codebase advanced through v5.14.0-.9 in the 2 days since

---

## Plan summary

- 4 sub-tag ships (`A` struct + math kernel; `B` dispatch + cfg fields; `C` persistence; `D` tests + propagation) + umbrella
- ~610 LOC estimated total (250 + 80 + 80 + 200)
- ~12 new tests
- Branch: `feat/v5.14-foxml-port-and-maker` (matches operator policy + git status)
- Predecessor: v5.14.9 (umbrella tagged + shipped)
- Surface area: ML_Headers + StrategyParameters dispatch + EnsembleModelZoo struct extension + new persistence file
- Hot path UNTOUCHED (slow-path-only); replay-determinism via seeded mt19937_64

---

## Checklist verdicts

### Core 10-item checklist (CLAUDE_REVIEW.md)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | PASS | ML dispatch is slow-path; plan asserts hot path untouched |
| 2 | Train-serve parity | PASS | Bandit is RUNTIME state (no stamp body extension); load+save symmetric via parallel `_Save/_LoadThompsonState` mirroring v5.13.4.C exit_bandit pattern; `BacktestSharded_Run` and `EngineSharded_Run` both consume `ML_BuildParameters` dispatch |
| 3 | Surface area | PASS | ~6 files touched; well-bounded |
| 4 | Pointer init / heap lifecycle | PASS | `ThompsonBanditState` is value type embedded in `EnsembleModelZoo`; no heap; init via memset + `_InitThompsonBandits` |
| 5 | Backward compat | PASS | No format-version bump needed; new persistence file is parallel-by-absence (forward-compat-by-absence per v5.13.4.C precedent); cfg defaults preserve Exp3 behavior |
| 6 | Multi-threading | PASS | RNG state per-bandit (per-regime, per-zoo); slow-path-only access; no new shared atomic |
| 7 | Test coverage | PASS | 12 explicit tests enumerated + persistence round-trip + replay-determinism |
| 8 | Docs + invariants | GAP | Plan does NOT mention `DOCS/CHANGELOG.md` entry, `engine.cfg.example` extension, or `DOCS/HOT_PATH_CHANGELOG.md` slow-path entry. See Propagation gaps below. |
| 9 | Forward maintenance | MERGE_OPP | `BanditState` ↔ `ThompsonBanditState` and 5 parallel `Bandit_*` ↔ `Thompson_*` functions = canonical mirror-fn pattern (Class 18 risk). FOREACH_BANDIT_ALGORITHM registry would compile-time-enforce the parallel maintenance. See Check 24 + Recommendations. |
| 10 | Rollback story | PASS | Rollback anchor cited: `pre-v5.14.10` = Phase 3 close (v5.14.7); but plan body says "Phase 3 close (v5.14.7)" while v5.14.7 was DEFERRED-INDEFINITE per TECH_DEBT-008 — anchor should be `pre-v5.14.10` = `v5.14.9` umbrella tag instead. Minor staleness. |

### v5.4.0 sprint guards (Checks 11-14)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 11 | Architectural sprint detection | PASS | Not a refactor sprint; pure additive |
| 12 | Display ↔ execution invariant | PASS | No new hot-path predicate term; bandit selection is slow-path-only |
| 13 | Strategy lifecycle completeness | PASS | Doesn't add a strategy; extends EnsembleModelZoo state |
| 14 | Function-pointer / X-macro dispatch correctness | N/A | Plan uses switch dispatch (3-way enum: 0/1/2); /readiness flags this as an X-macro CANDIDATE → see Check 24 below |

### v5.9 ML hardening (Checks 15-17)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 15 | ML feature change requires parity regression update | PASS | No FeatureRegistry / RegimeSignals / Features_PackAll touch; FEATURE_REGISTRY_HASH unchanged |
| 16 | New cfg field with stamp-bearing → recipe doc update | PASS | Plan explicitly asserts "Surface G discipline: N/A (no stamp body — runtime state only)". 5 new cfg fields are NOT stamp-bound — verified intent. **HOWEVER:** `bandit_blend_ratio` IS already stamp-bound (`ML_Headers/ModelInference.hpp:295-296`). Plan should explicitly note the new fields don't extend stamp-bound surface (decision rationale = bandit weights aren't per-model parameters; algorithm choice is engine-wide). Without this note, future ML auditors may flag as incomplete. |
| 17 | Model-load path changes → strict-mode integration test | PASS | No model load changes |

### v5.12-v5.14 additions (Checks 18-28)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 18 | Reuse-audit | PASS | Plan's "Pre-existing work audit" section enumerates REUSE claims (BanditState, EnsembleModelZoo bandit boot/save, JSON helpers, std::random) and TRULY NEW separately — exemplary pre-coding hygiene |
| 19 | Pre-existing-work audit (SHIP-BLOCKING) | GAP — false-REUSE | Plan claims `BanditState`/`Bandit_*` live in `ML_Headers/BanditLearning.hpp` (CORRECT). Plan claims `EnsembleModelZoo.bandits[NUM_REGIMES]` and `EnsembleModelZoo_InitBandits` lives in cited file path (PARTIALLY WRONG). The `EnsembleModelZoo` struct + bandit init/save/load all live in `ML_Headers/CoreModelZoo.hpp` (lines 817, 1238, 1865, 1911), NOT in a separate `EnsembleModelZoo.hpp`. Plan body uses ambiguous "EnsembleModelZoo.bandits[...]" without file path; coder will eventually find it but plan should cite `ML_Headers/CoreModelZoo.hpp:817-845` explicitly. **ACTION:** add file:line citations for all REUSE claims. |
| 20 | Future-proofness sanity | DRIFT-RISK | Plan has 3 parallel state structs (`bandits` + `exit_bandits` + new `thompson_bandits`) and 5+ parallel `_Save/_Load/_Init/...State` calls per algorithm. At the 4th algorithm (UCB1, KL-UCB, contextual bandits, etc.) this becomes 20+ sites. **No FOREACH_BANDIT_ALGORITHM note.** Caramel's framing 2026-05-09 ("structural fix preferred") + memory `feedback_structural_fix_for_recurring_class` apply. Either FOREACH_BANDIT_ALGORITHM registry OR explicit "DEFER to v5.16+ when 4th algorithm proposed" PASS-DEFERRED note. See Recommendations. |
| 21 | Test count assertion fragility | PASS | Plan says "~12 new tests" — fuzzy estimate, not `==` assertion |
| 22 | Auto-trigger downstream re-audit after umbrella ships | N/A | This IS the post-v5.14.9-umbrella audit. Caller is doing the right thing. |
| 23 | Latency accountability | GAP | Plan provides cost estimates (~80ns Thompson, ~130ns Both) but does NOT explicitly include `DOCS/HOT_PATH_CHANGELOG.md` entry in the propagation list. Per CLAUDE.md item 17, slow-path additions ≥10ns/cycle require an entry. 80-130ns extra at slow-path tail when cfg=1 or cfg=2 → MUST land an entry. |
| 24 | Mirror-function call-sequence enumeration | DRIFT-RISK | `BanditState` ↔ `ThompsonBanditState` + 5 parallel functions (`Bandit_Init` ↔ `Thompson_Init`, `Bandit_Update` ↔ `Thompson_Update`, `Bandit_GetProbabilities` ↔ `Thompson_GetProbabilities`, `Bandit_SaveJSON` ↔ `Thompson_SaveJSON`, `Bandit_LoadJSON` ↔ `Thompson_LoadJSON`) plus 2 parallel ensemble functions (`EnsembleModelZoo_SaveBanditState` ↔ `_SaveThompsonState`, `_LoadBanditState` ↔ `_LoadThompsonState`). **8 mirror sites total.** Per CLAUDE.md item 19 + structural-fix-preferred decision framework: would FOREACH_BANDIT_ALGORITHM registry compile-time-enforce parallel maintenance? **YES** — at the 3rd algorithm (UCB1, contextual) this drift class will recur exactly as STAMP_CFG_AUTOPOPULATE recurred 4× before extinction. **STRONG RECOMMENDATION:** introduce FOREACH_BANDIT_ALGORITHM registry in v5.14.10.A (not deferred to v5.16+). Pattern shape: registry tuple `(NAME, struct_type, cfg_enum_value, init_fn, update_fn, sample_fn, save_fn, load_fn, ensemble_init_fn, ensemble_save_fn, ensemble_load_fn)` → compile-time generates dispatch table + AUTOPOPULATE companion for production-callers. Estimate +2-3h vs direct mirror; eliminates the recurring class. |
| 25 | TECH_DEBT.md surface-area scan | PASS-with-context | Walked all 25+ entries. Overlapping ones: |
| | TECH_DEBT-010 | OPEN | If cfg=2 "Both" mode logs Thompson choice + Exp3 weights to calibration log → this would add 2-3 columns to CSV writer at `OrderManager.hpp:1008`. Currently logs ~20 columns. TECH_DEBT-010 trigger: "next ship that adds 3+ calibration log columns in one umbrella". **ACTION:** plan must decide either (a) defer cfg=2 telemetry to a follow-up ship that absorbs TECH_DEBT-010, OR (b) absorb the FOREACH_CALIB_LOG_COL registry into v5.14.10.B/.C if cfg=2 ships now. |
| | TECH_DEBT-018 | OPEN | This audit IS partial closure of /precoding-audit Layer 1 skill (manual 4-agent dispatch pattern). No action for v5.14.10. |
| | TECH_DEBT-022 | OPEN | 5 new cfg fields → marginal addition; trigger ("3+ new non-boolean cfg fields in one umbrella") is met technically, but TECH_DEBT-022 is non-blocking (boot-only, ~25µs total). **ACTION:** flag for sprint-end review; not blocking v5.14.10. |
| | TECH_DEBT-009 (broader FOREACH_CFG_FIELD) | PARTIAL OPEN | 5 new non-boolean cfg fields = exactly the trigger ("Next ship that adds 3+ new non-boolean cfg fields in one umbrella"). **DECISION POINT:** absorb FOREACH_CFG_FIELD registry (~6-8h) OR defer with rationale. Recommend defer (current ship has enough scope) but explicitly document. |
| 26 | DEFERRED-FOR-FUTURE-SHIP placeholder | N/A | No new X-macro registry adds in plan (yet — see Check 24 recommendation) |
| 27 | DESIGN_SPECS pattern-application audit (via /dod-audit by-reference) | MISSED-3 | See section below for full /dod-audit walk |
| 28 | Test-strength anti-regression audit (via /test-strength-audit by-reference) | PASS | New tests only; no test deletions/weakenings |

---

## Cold-pickup completeness 10-point check (CLAUDE.local.md)

| # | Field | Verdict | Notes |
|---|------|---------|-------|
| C.1 | Branch state | PASS | "Branch: feat/v5.14-foxml-port-and-maker" (matches current operator practice) |
| C.2 | Phase execution order matches dependency order | PASS | A→B→C→D linear; A independent (struct + math); B depends on A (dispatch); C depends on A (struct); D depends on B+C (tests cover full path). Order correct. |
| C.3 | First concrete move per phase | PARTIAL | Step 1 names new file path + struct definition (good). Step 2 says "EnsembleModelZoo extension" but doesn't name the line in CoreModelZoo.hpp. Step 3 says "ML_BuildParameters dispatch" but doesn't cite line 895 (existing dispatch site). Step 4 says "Persistence" — doesn't cite the v5.13.4.C exit_bandit pattern with file:line. **ACTION:** add file:line for each step's "Step 0" mechanical entry. |
| C.4 | Function/constructor names cited | PASS | `Thompson_Init/Update/Sample/GetProbabilities` named; `EnsembleModelZoo_InitThompsonBandits` named; `EnsembleModelZoo_SaveThompsonState/_LoadThompsonState` named |
| C.5 | File:line refs for cited tests/baselines | GAP | Plan doesn't cite test file path or specific test_block lines. v5.14.0/.1/.2/etc tests live in `tests/controller_test.cpp` (or split files); plan should say where new tests land. |
| C.6 | Stale-claim audit | GAP | Plan claims `EnsembleModelZoo.bandits[NUM_REGIMES]` etc — verified location is `ML_Headers/CoreModelZoo.hpp:833`, NOT a file called `EnsembleModelZoo.hpp` (no such file exists). Plan claims rollback anchor "pre-v5.14.11 = Phase 3 close (v5.14.7)" — v5.14.7 is DEFERRED-INDEFINITE per TECH_DEBT-008; anchor should be `v5.14.9` umbrella. **Plan heading still says v5.14.11; plan body explicitly says "v5.14.11" 12+ times.** Renumbered to v5.14.10 in MASTER per 2026-05-10 amendment but sub-plan body NEVER updated. |
| C.7 | Effort claims reconcile with file size deltas | PASS | Step 1 (~250 LOC) for new ThompsonBandit.hpp matches BanditLearning.hpp size (~700 LOC for Exp3 incl JSON helpers — Thompson is simpler so 250 plausible). Step 2-3 (~80 LOC each) for dispatch + cfg + persistence: roughly aligned with v5.13.4.C exit_bandit pattern's diff stats. |
| C.8 | Source-audit references with paths | PARTIAL | "Pass 2 #5 finding (FoxML_Core decisioning/bayesian_policy.py:50-120)" — cites the SOURCE-AUDIT file path. PASS for that ref. Other cross-refs cite version numbers without plan paths (e.g., "v5.14.0.B Ridge override" with no plan file). |
| C.9 | Predecessor / dependent plans named with paths | GAP | Cross-references list says "v5.14.0.B (Ridge override...)" — should cite `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.0-ridge-blending.md`. Same for "v5.13.4 (sell-side bandit pattern)". |
| C.10 | Tag names locked + rollback anchors | PASS | Each sub-tag named; umbrella tag specified; rollback anchor specified (though see C.6 for staleness). |

**Cold-pickup verdict:** 6/10 PASS, 4 PARTIAL/GAP. Per skill spec "8/10 = GREEN, missing 2 = fix during coding". 4 missing means **YELLOW** — fix the heading staleness (C.6) and Step 0 file:line citations (C.3, C.5) before coding. C.8/C.9 acceptable risk.

---

## Cfg-flag eligibility audit (5 new cfg fields)

Per `tick-trader-percore-workspace/DESIGN_SPECS/cfg-flag-eligibility-criteria.md` 5-criteria framework:

| Cfg field | Type | Bitmap-eligible? | Decision | Rationale |
|---|---|---|---|---|
| `bandit_algorithm` | int enum (0/1/2) | NO | Direct cfg field | Criterion 5 fail: enum, not boolean. The 3-way value can't pack into a bit. Stays as `int` on ControllerConfig. |
| `thompson_mu_prior` | FPN<F> | NO | Direct cfg field | Criterion 5 fail: scalar value, not boolean. |
| `thompson_precision_prior` | FPN<F> | NO | Direct cfg field | Criterion 5 fail: scalar. |
| `thompson_precision_obs` | FPN<F> | NO | Direct cfg field | Criterion 5 fail: scalar. |
| `thompson_rng_seed` | uint64_t | NO | Direct cfg field | Criterion 5 fail: scalar. |

**Verdict:** ALL 5 fields correctly stay as direct cfg fields; NONE are bitmap-eligible. **EXPECTED outcome per handoff.** TECH_DEBT-009 broader FOREACH_CFG_FIELD scope would absorb these into a non-boolean field registry, but that ship is not v5.14.10.

**ACTION:** plan should add a 1-line note "All 5 cfg fields are non-boolean → stay as direct cfg fields per `cfg-flag-eligibility-criteria.md`" to forestall future audit re-litigation. (Establishes the rejection rationale in plan body, preventing TECH_DEBT entry needed.)

---

## DESIGN_SPECS pattern-application audit (Check 27 by-reference /dod-audit)

Pattern catalog walk (17 active DESIGN_SPECS docs):

| Pattern | Applied? | Notes |
|---|---|---|
| `bitmap-flag-api.md` | N/A | No new bool flags; cfg fields are non-boolean |
| `x-macro-registry-with-presence-dispatch.md` | **MISSED** | FOREACH_BANDIT_ALGORITHM is exactly this pattern's use case. See Check 24. |
| `autopopulate-pattern-for-production-caller-class.md` | **MISSED** | If FOREACH_BANDIT_ALGORITHM registry adopted, AUTOPOPULATE companion macro mandatory per CLAUDE.md item 21 (parallel-impl class). v5.13.4.C added exit_bandit boot wiring at SaveBanditState/LoadBanditState callsites; v5.14.10 will add Thompson at the SAME callsites — production-caller class. AUTOPOPULATE_BANDIT_ALGORITHM_BOOT_INIT etc. would extinguish at compile time. |
| `pre-post-cfg-registry-split-for-emit-order-preservation.md` | N/A | No HMAC-locked emit order |
| `wire-format-byte-preservation-discipline.md` | N/A | No stamp body extension |
| `cfg-flag-eligibility-criteria.md` | APPLIED-correctly | 5 cfg fields evaluated; all 5 fail bitmap criteria (correct decision); plan should explicitly cite |
| `audit-driven-pre-coding-gate.md` | APPLIED | This audit IS the pre-coding gate |
| `heterogeneous-registry-pattern.md` | N/A | No new domain emerging |
| `structural-fix-preferred-decision-framework.md` | **MISSED** | Plan picks "direct mirror" (parallel struct + parallel functions) when "structural fix" (FOREACH_BANDIT_ALGORITHM) is justified by Class 18 recurrence. Plan must justify the choice OR pivot. |
| `slow-path-gate-registry-pattern.md` | N/A | No slow-path gate addition |
| `transient-aggregation-bitmap-pattern.md` | N/A | No bitmap aggregation |
| `partner-core-bitmap-pattern.md` | N/A | No partner-core relationship |
| `per-bit-per-core-override-pattern.md` | N/A | No per-core override on new cfg fields proposed |
| `registry-tuple-as-single-source-of-truth.md` | **MISSED** | If FOREACH_BANDIT_ALGORITHM adopted, the tuple SHOULD be single source: enum + struct type + init/update/sample/save/load fn pointers + ensemble init/save/load fn pointers + cfg enum value. |
| `autopopulate-from-arity-macro-family.md` | N/A | No multi-arity expansion needed |
| `curve-registry-pattern.md` | N/A | No curve compute fns |

**MISSED-3 verdict:** 3 patterns (X-macro registry, AUTOPOPULATE companion, structural-fix-preferred decision) all converge on the **SAME recommendation: add FOREACH_BANDIT_ALGORITHM registry**. This is the dominant DESIGN_SPECS finding.

---

## Dependency verification (Check 19 sub-task)

| Claimed dependency | Verified | Notes |
|---|---|---|
| `BanditState` struct at `ML_Headers/BanditLearning.hpp` | EXISTS (line 65) | OK |
| `Bandit_Init` | EXISTS (line 82) | OK |
| `Bandit_Update` | EXISTS (line 222) | OK |
| `Bandit_GetProbabilities` | EXISTS (line 118) | OK |
| `Bandit_SaveJSON` | EXISTS (line 369) | OK |
| `Bandit_LoadJSON` | EXISTS (line 503) | OK |
| `EnsembleModelZoo.bandits[NUM_REGIMES]` | EXISTS but at `ML_Headers/CoreModelZoo.hpp:833` (NOT EnsembleModelZoo.hpp — no such file exists) | **GAP — plan cites wrong file path implicitly** |
| `EnsembleModelZoo.exit_bandits[NUM_REGIMES]` | EXISTS at `CoreModelZoo.hpp:845` | OK |
| `EnsembleModelZoo_InitBandits` | EXISTS at `CoreModelZoo.hpp:1238` | OK |
| `EnsembleModelZoo_InitExitBandits` | EXISTS at `CoreModelZoo.hpp:1286` | OK |
| `EnsembleModelZoo_SaveBanditState` | EXISTS at `CoreModelZoo.hpp:1865` | OK |
| `EnsembleModelZoo_LoadBanditState` | EXISTS at `CoreModelZoo.hpp:1911` | OK |
| ML_BuildParameters dispatch at `Strategies/StrategyParameters.hpp:~835` | EXISTS — actual line 895 (Bandit_GetProbabilities call) and 658 (function definition) | **GAP — line ~835 is wrong; verify the right anchor** |
| `weights_buf[ENSEMBLE_HORIZON_MAX]` | EXISTS at line 895 | OK |
| `cfg.ridge_within_horizon` (override path on top of bandit) | EXISTS at line 932 | OK |
| `BANDIT_MAX_ARMS` | EXISTS at `BanditLearning.hpp:60` (= 8) | OK |
| `NUM_REGIMES` | EXISTS via `Strategies/StrategyInterface.hpp` include | OK |
| `ENSEMBLE_HORIZON_MAX` | EXISTS at `CoreModelZoo.hpp:814` | OK |

**FALSE-NEW check:**

| Proposed NEW thing | Already exists? | Verdict |
|---|---|---|
| `ML_Headers/ThompsonBandit.hpp` file | NO | OK — truly NEW |
| `ThompsonBanditState` struct | NO | OK — truly NEW |
| `Thompson_*` functions | NO (no grep matches) | OK — truly NEW |
| `cfg.bandit_algorithm` enum | NO (only existing `bandit_enabled` boolean in MlCfgFlagRegistry) | OK — truly NEW |
| `thompson_*` cfg fields | NO | OK — truly NEW |
| `EnsembleModelZoo.thompson_bandits[]` array | NO | OK — truly NEW |
| `thompson_state.json` persistence file path | NO matches | OK — truly NEW |

**No FALSE-NEW errors.** Plan's "TRULY NEW" section is accurate.

---

## CRITICAL pre-existing finding — `MlCfgFlagRegistry.hpp` description drift

`/home/caramel/code/FoxML_Trader_v2/ML_Headers/MlCfgFlagRegistry.hpp:55-56`:

```cpp
X(BANDIT_ENABLED,               bandit_enabled,               "Bandit",                "FoxML",       "Thompson-sampling bandit for buy-signal arm selection")
X(EXIT_BANDIT_ENABLED,          exit_bandit_enabled,          "Exit Bandit",           "FoxML",       "Thompson-sampling bandit for exit-side arm selection")
```

**Doc says "Thompson-sampling bandit" — current implementation is Exp3-IX, not Thompson.** Pre-existing doc bug independent of this ship. v5.14.10 should EITHER:
- Update these descriptions during .B (cfg dispatch ship) to clarify "Bandit (Exp3-IX or Thompson based on `cfg.bandit_algorithm`)", OR
- File as separate TECH_DEBT entry for cleanup

This catches the gap before operator confusion. Recommend updating in .B.

---

## Latency analysis (Check 23)

Plan claims:
- cfg=0 (Exp3 default): ~5ns enum check (slow path)
- cfg=1 (Thompson): ~80ns Gaussian draws
- cfg=2 (Both): ~130ns

**ACTION:** plan must include explicit `DOCS/HOT_PATH_CHANGELOG.md` entry in propagation list (per CLAUDE.md item 17). The 80-130ns slow-path addition under cfg=1/2 EXCEEDS the 10ns threshold for slow-path entries. Also include cumulative-cost sanity (recent ships' per-cycle adds; current slow-path budget headroom).

---

## Hidden scope detected

1. **Heading + body version staleness (v5.14.11 → v5.14.10).** ~5 min mechanical fix. **MUST FIX before coding** (cold-pickup C.6).
2. **File path citations.** Plan claims `EnsembleModelZoo.bandits[...]` without naming `ML_Headers/CoreModelZoo.hpp:817-845`. Add explicit citations. ~5 min.
3. **Step 0 file:line for each step.** Plan lists steps but doesn't pin "first mechanical action". Per cold-pickup C.3 + C.5. ~10 min.
4. **Propagation list missing items.** `DOCS/CHANGELOG.md`, `engine.cfg.example`, `DOCS/HOT_PATH_CHANGELOG.md`, `Version.hpp` bump. ~5 min to add to plan.
5. **MlCfgFlagRegistry pre-existing description drift.** "Thompson-sampling bandit" labels on Exp3-IX flags. Address in v5.14.10.B during cfg field add. ~5 min.
6. **TECH_DEBT-010 decision (calibration log columns).** If cfg=2 telemetry adds calibration log columns, decide absorb-or-defer in plan body. ~10 min decision; ~3-4h work if absorb (FOREACH_CALIB_LOG_COL registry).
7. **FOREACH_BANDIT_ALGORITHM registry decision (Check 24 + dod-audit MISSED-3).** Single biggest finding. Decide structural-fix-now vs PASS-DEFERRED. ~30 min decision; ~2-3h work if absorb (registry + AUTOPOPULATE + dispatch generation).
8. **TECH_DEBT-009 (FOREACH_CFG_FIELD broader).** 5 new non-boolean cfg fields hits the trigger. Decide absorb-or-defer; recommend defer with explicit `// FUTURE OPPORTUNITY:` comment in plan. ~5 min decision.

---

## Recommendations

### MUST FIX before coding (~30-60 min total)

1. **Fix heading + body**: change all 12+ "v5.14.11" references to "v5.14.10" (cold-pickup C.6 stale-claim). Update rollback anchor `pre-v5.14.11` → `pre-v5.14.10`. Confirm rollback baseline = `v5.14.9` umbrella tag (b09b2d5), NOT v5.14.7 (deferred-indefinite).
2. **Add file:line citations**: every REUSE claim should cite `ML_Headers/CoreModelZoo.hpp:<line>` or `ML_Headers/BanditLearning.hpp:<line>`. Address Check 19 GAP-false-REUSE.
3. **Add Step 0 mechanical action per phase**: per cold-pickup C.3 ("first concrete move").
4. **Add to propagation list**:
   - `DOCS/CHANGELOG.md` entry (v5.14.10 row)
   - `engine.cfg.example` extension (5 new cfg lines with defaults + comments)
   - `DOCS/HOT_PATH_CHANGELOG.md` slow-path entry (80-130ns when cfg=1 or cfg=2)
   - `Version.hpp` bump per sub-tag (5.14.9 → 5.14.10.A → 5.14.10.B → 5.14.10.C → 5.14.10) — per memory `feedback_bump_version_per_ship`
5. **Add cfg-flag-eligibility note**: 1 line confirming all 5 cfg fields stay as direct cfg fields per `cfg-flag-eligibility-criteria.md` (preempts future audit noise).

### CONSULT-with-Caramel decisions (~30 min discussion before coding)

6. **FOREACH_BANDIT_ALGORITHM registry — structural fix or defer?** Check 24 + dod-audit MISSED-3 + Class 18 recurrence history all converge. Per CLAUDE.md item 19 + memory `feedback_structural_fix_for_recurring_class`: at the 3rd algorithm (UCB1, contextual), this drift class WILL recur. Two options to present:
   - **Option A (structural-fix-now):** introduce FOREACH_BANDIT_ALGORITHM in v5.14.10.A. Tuple: `(NAME, struct_type, init_fn, update_fn, sample_fn, save_fn, load_fn, json_filename)` + AUTOPOPULATE_BANDIT companion macro. Adding 3rd algorithm = 1 row in registry. ~+2-3h vs direct mirror (~300 LOC vs ~250 LOC for .A). Eliminates Class 18 recurrence.
   - **Option B (PASS-DEFERRED):** ship direct mirror; add explicit `// FUTURE OPPORTUNITY: when 3rd bandit algorithm proposed (UCB1 etc.), refactor to FOREACH_BANDIT_ALGORITHM` in plan + TECH_DEBT entry. Reasoning: 2 algorithms is below the typical Class 18 trigger of 3+ sites.
   - Caramel's framing 2026-05-09 ("structural fix preferred when bug class can recur") + 4× recurrence history of analogous classes argues Option A.

7. **Calibration log columns under cfg=2 (TECH_DEBT-010 decision)**: if cfg=2 logs Thompson choice + Exp3 weights per fill, this adds 2-3 columns to `OrderManager.hpp:1008` writer. Trigger met. Two options:
   - **Option A (absorb):** introduce FOREACH_CALIB_LOG_COL registry now (~3-4h). Folds TECH_DEBT-010 close into v5.14.10.D.
   - **Option B (defer):** ship cfg=2 telemetry with manual column adds; flag in plan that the registry refactor is queued.

### Worth FIXING during coding (no block; ~10 min total during .B)

- **MlCfgFlagRegistry description drift**: update `BANDIT_ENABLED` + `EXIT_BANDIT_ENABLED` descriptions to reflect "Exp3-IX or Thompson per `cfg.bandit_algorithm`" during .B cfg field addition.
- **Add cross-ref plan paths** in plan body's Cross-references section: `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.0-ridge-blending.md` etc.

### Acceptable risk (don't block)

- TECH_DEBT-022 (perfect-hash parser) — boot-only, ~25µs total; non-blocking.
- TECH_DEBT-009 (broader FOREACH_CFG_FIELD) — 5 new non-boolean fields hits trigger but recommend defer with explicit `// FUTURE OPPORTUNITY:` comment + TECH_DEBT entry append (the 5 fields document the case for the registry).

---

## Verdict: **YELLOW**

GREEN — start coding now
**YELLOW — fix the must-fix items (1-5 above; ~30-60 min) + consult Caramel on items 6-7 (~30 min discussion) BEFORE coding starts**
RED — significant rescope needed; revisit plan

**Rationale:** plan is structurally sound, well-pre-audited (REUSE/NEW separation is exemplary), and verifies clean against ALL FALSE-NEW checks. All 5 cfg fields correctly evaluated as non-boolean (handoff-expected outcome). NO ship-blocking GAPs. The 4 must-fix items (heading staleness, file:line citations, Step 0 actions, propagation list) are mechanical and bounded (~30-60 min). The two consult-decisions (FOREACH_BANDIT_ALGORITHM registry + calibration log absorb-or-defer) are EXACTLY the kind of decision that benefits from the structural-fix-preferred + audit-driven-pre-coding-gate framework — caught before coding lands a Class 18 mirror gap.

The plan is shipper-ready after the must-fix items + Caramel decisions on 6-7. Estimate ~1-2h plan amendment + decision time before coding starts.

---

## Map-update suggestions (post-coding)

- Run `./tools/gen_code_map.sh` after .D — will pick up `Thompson_*` family + `EnsembleModelZoo_(Init|Save|Load)ThompsonBandits/State` family.
- Append CHANGELOG.md v5.14.10 row covering: bandit_algorithm cfg + ThompsonBanditState + 8 mirror functions + persistence file.
- If FOREACH_BANDIT_ALGORITHM adopted (recommended): document in `DESIGN_SPECS/x-macro-registry-with-presence-dispatch.md` with bandit-family as canonical 3rd application alongside FOREACH_FAILURE_MODE + FOREACH_DEGRADATION_CURVE. Update CLAUDE.md item 13 audited categories list.
- TECH_DEBT entry append (open or close):
  - If FOREACH_BANDIT_ALGORITHM adopted: close TECH_DEBT-NNN (new entry to be appended now documenting the structural choice).
  - If deferred: open TECH_DEBT-NNN with the FUTURE OPPORTUNITY note + trigger ("3rd bandit algorithm proposed").

---

## Attached context

- Plan file: `/home/caramel/code/FoxML_Trader_v2/plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.10-bayesian-thompson-bandit.md`
- MASTER plan reference: `/home/caramel/code/FoxML_Trader_v2/plans/v5.14-foxml-port-and-maker/MASTER.md` (lines 287-290 confirm v5.14.10 renumber, 322-323 + 415-419 confirm scope)
- TECH_DEBT scan: 25 entries walked; 4 overlapping (010, 018, 022, 009 partial); none ship-blocking
- DESIGN_SPECS catalog: 17 docs at `/home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/`; 3 patterns MISSED converge on FOREACH_BANDIT_ALGORITHM
- Predecessor: v5.14.9 umbrella `b09b2d5` + docs `490618b` (working tree clean)
- Mirror-function inventory (Check 24): 8 sites total
  - `BanditState` ↔ `ThompsonBanditState` (1 struct pair)
  - `Bandit_Init` ↔ `Thompson_Init`, `Bandit_Update` ↔ `Thompson_Update`, `Bandit_GetProbabilities` ↔ `Thompson_GetProbabilities`, `Bandit_SaveJSON` ↔ `Thompson_SaveJSON`, `Bandit_LoadJSON` ↔ `Thompson_LoadJSON` (5 fn pairs)
  - `EnsembleModelZoo_InitBandits` ↔ `EnsembleModelZoo_InitThompsonBandits` (1 ensemble fn pair)
  - `EnsembleModelZoo_SaveBanditState` ↔ `_SaveThompsonState`, `_LoadBanditState` ↔ `_LoadThompsonState` (2 ensemble fn pairs)
