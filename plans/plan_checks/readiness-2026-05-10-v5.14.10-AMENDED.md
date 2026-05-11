# /readiness report — 2026-05-10-v5.14.10-bayesian-thompson-bandit.md (AMENDED) — 2026-05-10

**Audited plan:** `plans/v5.14-foxml-port-and-maker/subplans/2026-05-10-v5.14.10-bayesian-thompson-bandit.md` (date-prefix updated 2026-05-10 amendment; physical filename in `subplans/` is `2026-05-10-...md`)
**Audit kind:** Layer 2 mid-sprint re-audit on AMENDED plan (post all 13 mechanical fixes + 4 architectural decisions baked in)
**Codebase HEAD:** `feat/v5.14-foxml-port-and-maker` @ `490618b` (post v5.14.9 umbrella `b09b2d5`)
**Engine version:** 5.14.9 (Version.hpp:5)
**Prior /readiness verdict:** YELLOW (4 must-fix mechanical items + 2 consult-decisions)
**Prior report:** `plans/plan_checks/readiness-2026-05-10-v5.14.10-thompson-bandit.md`

---

## Re-audit scope (per caller mandate)

Six focus areas:
1. Cold-pickup completeness re-verification (10 fields)
2. Mirror-fn audit (Check 24) — registry + uniform 4-arg dispatch + PostLoadSetup extension
3. TECH_DEBT scan (Check 25) — verify CLOSED/RESOLVED claims (-010, -011, -027) + OPEN status (-026)
4. Version.hpp bump discipline at each sub-tag
5. Propagation list completion (CHANGELOG, engine.cfg.example, HOT_PATH_CHANGELOG, Version.hpp)
6. /dod-audit Check 27 by-reference — DESIGN_SPECS pattern citations

Plus catch-all: any new GAPs surfaced by the larger amended plan.

---

## Plan summary (amended)

- **6 sub-tag ships** (`.0` PerCoreSnap layout audit + `.A` math + `.B` engine wiring + `.C` persistence + `.D` display + `.E` tests/propagation) + umbrella
- ~1300-1500 LOC estimated total (80-150 + 400-500 + 150 + 150 + 250 + 200)
- **~15 new tests** (was 12; +3 for FOREACH walk + slow-path-gate predicate + offset-stability)
- Branch: `feat/v5.14-foxml-port-and-maker` (matches operator policy)
- Predecessor: v5.14.9 (umbrella `b09b2d5`)
- Surface area: `ML_Headers/` (3 new files) + `Strategies/StrategyParameters.hpp` + `CoreFrameworks/CoreContext`/`SlowPathGateRegistry`/`ShardedSnapshot` + `DataStream/EngineTUI.hpp` + `GUI/MLStatusPanel`/`SettingsPanel` + `Backtest/`
- Hot path UNTOUCHED; replay-determinism via own Box-Muller on raw `mt19937_64::operator()`

---

## Checklist verdicts

### Core 10-item checklist (CLAUDE_REVIEW.md)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | PASS | Plan asserts hot path UNTOUCHED; verified via "Latency analysis" section (`tools/calls_graph_diff.sh` post-ship) |
| 2 | Train-serve parity | PASS | Bandit is RUNTIME state (no stamp body extension); `_Save/_LoadThompsonState` mirror v5.13.4.C exit_bandit symmetry; both `BacktestSharded_Run` and `EngineSharded_Run` consume same `ML_BuildParameters` dispatch via FOREACH_BANDIT_ALGORITHM table |
| 3 | Surface area | PASS | ~10-12 files touched across 6 sub-ships; well-bounded. Each sub-tag is single-concern |
| 4 | Pointer init / heap lifecycle | PASS | `ThompsonBanditState` value type embedded in `EnsembleModelZoo`; no heap; init via memset + `_InitThompsonBandits`; FOREACH_ENSEMBLE_POST_LOAD picks it up |
| 5 | Backward compat | PASS | No `MODEL_FORMAT_VERSION` bump; new persistence file is parallel-by-absence; cfg defaults preserve Exp3 behavior (`bandit_algorithm=0` unchanged); 4 stamp-bound cfg fields use Surface G `has_*` pattern via STAMP_CFG_AUTOPOPULATE |
| 6 | Multi-threading | PASS | RNG state per-bandit (per-regime, per-zoo); slow-path-only access; no new shared atomic; predicates cached at slow-path top per item 18(c) |
| 7 | Test coverage | PASS | ~15 explicit tests enumerated incl. SHA-256 sample-trace replay-determinism + FOREACH walk + slow-path-gate predicate caching + persistence round-trip cross-version |
| 8 | Docs + invariants | FIXED | Plan's .E Steps 2-4 explicitly list `DOCS/HOT_PATH_CHANGELOG.md` (Step 2), `DOCS/CHANGELOG.md` (Step 3), `engine.cfg.example` (Step 4). Was GAP in prior audit — now addressed. |
| 9 | Forward maintenance | FIXED | FOREACH_BANDIT_ALGORITHM registry baked in (Decision A, ships .A) — eliminates Class 18 mirror at compile time. Was MERGE_OPP in prior audit — now closed structurally. Per CLAUDE.md item 19. |
| 10 | Rollback story | PASS | Each sub-tag has `pre-<tag>` rollback anchor: `pre-v5.14.10` = v5.14.9 (b09b2d5); `pre-v5.14.10.0` = v5.14.9; `pre-v5.14.10.A` = .0; etc. Sequence explicit. |

### v5.4.0 sprint guards (Checks 11-14)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 11 | Architectural sprint detection | PASS | Not a refactor; .0 layout audit is bounded reorg without function-pointer changes |
| 12 | Display ↔ execution invariant | PASS | Decision D (full Bayesian dashboard) ships 5 PerCoreSnap fields IN SAME ship as the new dispatch path. Bit-packed `thompson_state` byte + arrays match the mu/precision/pulls in ThompsonBanditState. Display↔execution wiring happens at .D Step 2 (slow-path snapshot publish path mirroring existing `ensemble_weights` pattern). |
| 13 | Strategy lifecycle completeness | N/A | Doesn't add a strategy; extends EnsembleModelZoo state |
| 14 | Function-pointer / X-macro dispatch correctness | PASS | FOREACH_BANDIT_ALGORITHM uses uniform 4-arg signature contract (`weights_out` + `chosen_arm_out`); auto-generated dispatch table; bounds-checked wrapper; ToString/FromString round-trip test in .A Step 6; FOREACH-walk integrity test in .E Step 1 |

### v5.9 ML hardening (Checks 15-17)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 15 | ML feature change requires parity regression update | PASS | No FeatureRegistry / RegimeSignals / Features_PackAll touch; FEATURE_REGISTRY_HASH unchanged |
| 16 | New cfg field with stamp-bearing → recipe doc update | PASS | 4 of 5 cfg fields stamp-bound via FOREACH_STAMP_BOUND_CFG (autoflows STAMP_CFG_AUTOPOPULATE); 5th (`thompson_rng_seed`) explicitly NOT stamp-bound with rationale (RNG state is runtime-only). Decision documented inline. PARITY-013 fix is .B Step 9. |
| 17 | Model-load path changes → strict-mode integration test | PASS | Plan extends FOREACH_ENSEMBLE_POST_LOAD (`init_thompson_bandits`, `load_thompson_state`) at `CoreModelZoo.hpp:2088-2104`; `EnsembleModelZoo_IsReadyForInference` at `:2137-2151` updated to include Thompson init flag check (Step .C.6) |

### v5.12-v5.14 additions (Checks 18-28)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 18 | Reuse-audit | PASS | "Pre-existing work audit" section enumerates REUSE with file:line citations; tt::json_io extraction at .C.1 (merge-scan T4 free win); 5-flag cfg evaluated for FOREACH_ML_CFG_FLAG (all REJECTED non-boolean per cfg-flag-eligibility-criteria); slow-path predicate cache via existing FOREACH_SLOW_PATH_GATE pattern (Decision C) |
| 19 | Pre-existing-work audit (SHIP-BLOCKING) | GAP — false-REUSE (mild) | See Dependency Verification table. Plan cites `EngineSharded.hpp:646-694` as bandit telemetry write site — actual is `CoreFrameworks/ShardedSnapshot.hpp:682-694`. Plan cites `CoreFrameworks/ShardedSnapshot.hpp` as PerCoreSnap struct location — actual is `DataStream/EngineTUI.hpp:980`. Plan cites field name `ensemble_bandit_arm_probs[8]` — actual fields are `ensemble_weights[5][8]` + `ensemble_n_updates_per_regime[5]`. **NOT SHIP-BLOCKING** but coder will lose 5-10 min per drift on first encounter. **ACTION:** correct the 3 file:line/struct-location/field-name citations in plan body before .0 starts. |
| 20 | Future-proofness sanity | PASS | FOREACH_BANDIT_ALGORITHM registry retrofit ships .A; Decision A explicit; addresses prior DRIFT-RISK; UCB1 / EXP4 / Bayesian linear bandit foreseeable as 1-row registry additions |
| 21 | Test count assertion fragility | PASS | Plan says "~+15 new from current 2796 ≈ 2811 total" — fuzzy (~), not `==` literal; FOREACH walk test in .E uses registry COUNT (extensible) |
| 22 | Auto-trigger downstream re-audit | PASS | This re-audit IS the post-amendment auto-trigger; mid-sprint audit gate section in plan body documents the protocol |
| 23 | Latency accountability | FIXED | .E Step 2 explicitly lists `DOCS/HOT_PATH_CHANGELOG.md` entry: cfg=0 ~5ns, cfg=1 ~85ns, cfg=2 ~140ns, hot path UNTOUCHED, cache analysis included. Was GAP in prior audit — now addressed. Per CLAUDE.md item 17. |
| 24 | Mirror-function call-sequence enumeration | FIXED | **Critical re-verification:** prior audit flagged 8 mirror sites (`Bandit_*` ↔ `Thompson_*` × 5 + `EnsembleModelZoo_(Init/Save/Load)*` × 3). Amended plan resolves via TWO complementary mechanisms: (1) FOREACH_BANDIT_ALGORITHM registry with uniform 4-arg dispatch — Bandit_GetProbabilities call sites at `Strategies/StrategyParameters.hpp:899/:912` migrate to `bandit_algo_fns[cfg.bandit_algorithm](...)` indirection, eliminating "parallel implementation drift" at the dispatch level (.A Step 4-6); (2) FOREACH_ENSEMBLE_POST_LOAD extension with 2 new entries closes the boot/load mirror surface at `CoreModelZoo.hpp:2088-2104` (.C Step 5 — explicitly cites `structural-fix-preferred-decision-framework.md` + `/trace-deps` BLOCKING amendment). **No remaining mirror surface.** Pattern matches v5.14.2.E.1 PostLoadSetup precedent (closed PARITY-009/010/011/012 = 9 sub-gaps in one ship). PASS. |
| 25 | TECH_DEBT.md surface-area scan | PASS-with-context | See dedicated section below for full TECH_DEBT verification. -010 closes via FOREACH_CALIB_LOG_COL (.D); -011 substantially closes via .0 cluster restructure + new DESIGN_SPECS doc; -026 stays OPEN (LOW future); -027 RESOLVED opportunistically in .C Step 4. All 4 entries explicitly handled in plan. Plan also addresses TECH_DEBT-009 implicitly (cfg-flag-eligibility note documents 5 fields stay direct). |
| 26 | DEFERRED-FOR-FUTURE-SHIP placeholder | PASS | FOREACH_BANDIT_ALGORITHM registry walk integrity test in .E Step 1 ("enumerate all algorithms, verify dispatch table integrity (ToString/FromString round-trip)") — matches the .E.1 symmetry test pattern |
| 27 | DESIGN_SPECS pattern-application audit | PASS | See dedicated section below; 7 patterns explicitly cited + 2 NEW DESIGN_SPECS docs to ship (`per-snapshot-cluster-layout-pattern.md` from .0; `calibration-log-column-registry.md` from .D) |
| 28 | Test-strength anti-regression audit | PASS | New tests only; no test deletions/weakenings; SHA-256-locked replay-determinism test (PARITY-014) is STRICT not smoke_check |

---

## Cold-pickup completeness 10-point check (CLAUDE.local.md)

| # | Field | Verdict | Notes |
|---|------|---------|-------|
| C.1 | Branch state | PASS | "Branch: `feat/v5.14-foxml-port-and-maker` (stay on existing sprint branch per going-forward rule)" — explicit, matches operator policy |
| C.2 | Phase execution order matches dependency order | PASS | `.0 → .A → .B → .C → .D → .E` linear; .0 is layout audit (independent foundation); .A is math kernel + registry (depends on .0 cluster placement); .B is engine wiring (depends on .A); .C is persistence (depends on .B for cfg fields); .D is display (depends on .0 cluster + .C state); .E is tests + propagation (depends on all). Order correct. Cold-pickup section in plan explicitly notes "linear; no out-of-order deps". |
| C.3 | First concrete move per phase | PASS | All 6 sub-tags have explicit Step 0 / Step 1 mechanical first action. .0 Step 0: "identify what's currently adjacent to ensemble_bandit_arm_probs" (NOTE: field name is wrong — see Check 19 GAP). .A Step 1: "Define ThompsonBanditState struct in `ML_Headers/ThompsonBandit.hpp` (NEW)" with full struct body shown. .B Step 1: "Add 5 cfg fields to `CoreFrameworks/ControllerConfig.hpp`". .C Step 1: extract to tt::json_io. .D Step 1: 5 PerCoreSnap fields with bit-pack layout. .E Step 1: ~15 tests enumerated. |
| C.4 | Function names cited | PASS | Cold-pickup section explicitly enumerates: `BanditAlgo_Exp3_Apply`, `BanditAlgo_Thompson_Apply`, `BanditAlgo_Both_Apply`, `Thompson_Init`, `Thompson_Update`, `Thompson_Sample`, `Thompson_GetProbabilities`, `EnsembleModelZoo_InitThompsonBandits`, `EnsembleModelZoo_SaveThompsonState`, `EnsembleModelZoo_LoadThompsonState`. All 10 named. |
| C.5 | File:line refs for cited tests/baselines | PASS | Tests live in tests/controller_test.cpp (sprint-implicit per existing v5.14.X cadence); .E Step 1 enumerates 15 specific test scenarios; SHA-256 sample-trace test seed=42 + N=1000 + lock the hash specified |
| C.6 | Stale-claim audit | GAP — see Check 19 | **Three citation drifts found:** (a) plan's .D Step 2 cites `EngineSharded.hpp:646-694` as "ensemble_bandit_arm_probs pattern" — the actual write site is `CoreFrameworks/ShardedSnapshot.hpp:682-694`. (b) plan's .0 Step 1 cites `CoreFrameworks/ShardedSnapshot.hpp` as PerCoreSnap struct location — actual is `DataStream/EngineTUI.hpp:980`. (c) plan repeatedly refers to field `ensemble_bandit_arm_probs[8]` — actual fields are `ensemble_weights[5][8]` + `ensemble_n_updates_per_regime[5]`. Other claims spot-checked OK: `CoreModelZoo.hpp:833/845/862/868/1238/1286/1865/1887/1911/1942/2088-2104/2137-2151`, `BanditLearning.hpp:60/369/440/455/473`, `Strategies/StrategyParameters.hpp:899/912`, `StampBoundCfgRegistry.hpp:137-138`, `SlowPathGateRegistry.hpp:85`. **ACTION:** correct the 3 drifted citations before .0 starts. ~5 min mechanical fix. |
| C.7 | Effort claims reconcile with actual file size deltas | PASS | .0 ~80-150 LOC for layout reorg + DESIGN_SPECS doc — plausible for ~30 PerCoreSnap fields. .A ~400-500 LOC matches BanditLearning.hpp size precedent (~700 LOC for Exp3 incl JSON helpers). .B ~150 LOC matches v5.13.4.C exit_bandit pattern's diff stats. .C ~150 LOC for save/load + tt::json_io extraction. .D ~250 LOC for FOREACH_CALIB_LOG_COL + 5 PerCoreSnap fields + writer. .E ~200 LOC for 15 tests + propagation. Total ~1300-1500 LOC reconciles. |
| C.8 | Source-audit references with paths | PASS | Cross-references section cites `plans/plan_checks/2026-05-10-v5.14.10-fresh-audits-synthesis.md` + 5 audit reports + `plans/v5.14-foxml-port-and-maker/MASTER.md` + workspace DESIGN_SPECS catalog with file paths |
| C.9 | Predecessor / dependent plans named with paths | PASS | Predecessor: v5.14.9 umbrella `b09b2d5` + docs `490618b`; dependent: `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.11-online-corr-update.md` (renumbered 2026-05-10) — full paths cited |
| C.10 | Tag names locked + rollback anchors | PASS | All 6 sub-tags + umbrella named; `pre-v5.14.10` / `pre-v5.14.10.{0,A,B,C,D,E}` rollback anchors specified at each phase end |

**Cold-pickup verdict:** 9/10 PASS, 1 GAP (C.6 stale-claim — same as Check 19 GAP). Per skill spec "8/10 = GREEN; 9/10 with one fixable mechanical gap = GREEN with note". Above the threshold; the C.6 fix is a 5-min mechanical correction.

---

## TECH_DEBT.md surface-area scan (Check 25 deep verify)

Per caller mandate: verify each TECH_DEBT entry's claimed status post-v5.14.10 is realistic.

### TECH_DEBT-010 — FOREACH_CALIB_LOG_COL registry — claimed CLOSED via .D Step 3

**Verification:** Plan's .D Step 3 defines `FOREACH_CALIB_LOG_COL(X)` registry with tuple `(col_name, type, getter_expr, doc)` in `DataStream/CalibLogColRegistry.hpp` (NEW file). 5 entries today (exp3_chosen_arm, thompson_chosen_arm, regime_id_at_pick, exp3_weights_csv, thompson_mu_csv). .D Step 4 says "Per-fill calibration log writer auto-extends from registry walk (CSV header + row format generated)". .D Step 7 ships new DESIGN_SPECS doc `calibration-log-column-registry.md` as the canonical reference.

**TECH_DEBT-010 trigger** ("Next ship that adds 3+ calibration log columns in one umbrella") **is met** with 5 new columns. Registry retrofit is appropriate per the entry's "Trigger" specification.

**Gap check:** does plan's tuple shape generate ALL three target sites (header constant + writer column + reader/parser column)? .D Step 4 asserts auto-extension for "CSV header + row format" but does NOT explicitly mention the reader/parser side. **MINOR — parser side is post-process tooling per TECH_DEBT-010 Surface; if the engine doesn't read its own calibration logs then auto-extension is sufficient.** Recommend confirming during .D Step 4 whether any in-engine reader exists; if not, CLOSED is correct.

**Verdict:** CLOSED claim is REALISTIC. Suggest .D Step 4 add a one-line check: "verify no in-engine reader of calibration log exists OR registry generates reader-side parser too".

### TECH_DEBT-011 — FOREACH_PER_CORE_SNAP_FIELD registry — claimed substantially CLOSED via .0

**Verification:** Plan's .0 ships PerCoreSnap layout audit + unified bandit telemetry cluster + new DESIGN_SPECS doc `per-snapshot-cluster-layout-pattern.md`. Cost estimate ~80-150 LOC. TECH_DEBT-011 entry estimates ~10-15h architectural ship for the FULL FOREACH_PER_CORE_SNAP_FIELD registry across ~30 fields — that's ~5-10x larger than .0's scope.

**Gap check:** plan claims "substantially closes" — is this realistic?
- .0 establishes the **methodology** (cluster discipline, alignas(64), arrays-first reorder, offset stability tests) — YES
- .0 produces the reusable **DESIGN_SPECS doc** (decision tree for clustering decisions, cross-references) — YES
- .0 does NOT introduce the FOREACH_PER_CORE_SNAP_FIELD registry itself across all 30 fields — TRUE
- The TECH_DEBT-011 entry says "needs design conversation about: (a) hot/warm/cold tiers, (b) write cadence per entry, (c) cache-line alignment preservation — NOT a mechanical conversion"

**Verdict:** "substantially closes" is HONEST framing — .0 closes the CLUSTERING + design-doc subset but does NOT eliminate the underlying TECH_DEBT-011 N-site pattern (the registry + ~30-field migration remains for a future ship). Plan should explicitly say "substantially closes the layout discipline subset; FOREACH_PER_CORE_SNAP_FIELD registry remains OPEN as separate ship per TECH_DEBT-011 cost estimate". .0 Step 6 ("TECH_DEBT-011 status update — close substantially; document any deferred items") is the right plan-time treatment; the ledger update should refresh the entry's scope to reflect the post-.0 state.

PASS — claim is realistic with the qualifier. Recommend ledger update at .0 close: change TECH_DEBT-011 wording from "convert PerCoreSnap field additions to a registry" to "[POST .0]: clustering + layout discipline established; remaining work is FOREACH_PER_CORE_SNAP_FIELD registry across 30 fields per the new DESIGN_SPECS methodology — deferred to dedicated ship".

### TECH_DEBT-026 — Per-core override of `bandit_algorithm` — stays OPEN (LOW future)

**Verification:** Plan does NOT ship per-core override. TECH_DEBT-026 explicitly says deferred until "operator requests per-core A/B testing of TRADING DECISIONS (not telemetry-only)". Plan's `bandit_algorithm=2` dual-mode handles telemetry comparison without per-core override. Status correctly stays OPEN.

**Verdict:** OPEN status is CORRECT. Plan's verification gate row "TECH_DEBT.md: ... -026 OPEN (per-core bandit_algorithm override; LOW future)" matches.

### TECH_DEBT-027 — Locale pinning gap in `Bandit_SaveJSON` — claimed RESOLVED opportunistically via .C Step 4

**Verification:** Plan's .C Step 4 says "Apply same locale pinning fix to existing Bandit_SaveJSON at `BanditLearning.hpp:369` (currently missing; flagged as dormant bug by /dod-audit)". Verified — `Bandit_SaveJSON` is at `BanditLearning.hpp:369` (matches). The fix is to wrap the fprintf body with `uselocale(newlocale(LC_NUMERIC_MASK, "C", 0))` save-restore.

**Verdict:** RESOLVED opportunistic claim is GENUINE — same file family (BanditLearning.hpp), same pattern (wire-format-byte-preservation Layer 2), ~5 extra LOC on top of Thompson_SaveJSON locale pinning. Trigger criterion (b) in TECH_DEBT-027 ("opportunistically when v5.14.10's MEDIUM-2 Thompson_SaveJSON locale pinning is implemented") is met. PASS.

### TECH_DEBT-009 — broader FOREACH_CFG_FIELD — implicitly addressed

**Verification:** Plan adds 5 new non-boolean cfg fields (bandit_algorithm INT enum + 3 thompson FPN + 1 thompson_rng_seed uint64). TECH_DEBT-009 trigger ("Next ship that adds 3+ new non-boolean cfg fields in one umbrella") IS met. Plan's "Cfg-flag eligibility analysis" section explicitly evaluates per cfg-flag-eligibility-criteria.md and REJECTS all 5 for FOREACH_ML_CFG_FLAG migration with rationale. This is the CORRECT plan-time treatment per TECH_DEBT-009's defer policy.

**Verdict:** TECH_DEBT-009 stays OPEN; plan's explicit evaluation + rejection-with-rationale documents the case for the broader registry without forcing absorption now. PASS-DEFERRED per Check 18 vocabulary.

---

## Mirror-fn audit (Check 24) deep dive

**Prior audit count:** 8 mirror sites (`BanditState ↔ ThompsonBanditState`; 5 fn pairs `Bandit_*` ↔ `Thompson_*`; 2 ensemble fn pairs `_SaveBanditState/_LoadBanditState ↔ _SaveThompsonState/_LoadThompsonState`).

**Amended plan structural fixes:**

1. **Dispatch surface** — FOREACH_BANDIT_ALGORITHM registry with uniform 4-arg signature contract eliminates the "switch on algorithm" mirror at `Strategies/StrategyParameters.hpp:899/:912`. New code calls `bandit_algo_fns[cfg.bandit_algorithm](ezoo, regime_id, n_arms, weights_out, &chosen_arm)`. Adding UCB1 = 1 row in registry + 1 compute fn — mirror cannot recur.

2. **Boot/load surface** — FOREACH_ENSEMBLE_POST_LOAD extension at `CoreModelZoo.hpp:2088-2104` (currently 7 entries via .C Step 5: `init_thompson_bandits`, `load_thompson_state`). PostLoadSetup helpers already centralize the boot/backtest/hot-swap callers (per v5.14.2.E.1 closure of PARITY-009/010/011/012 = 9 sub-gaps). Adding Thompson init/load to the registry inherits the centralization. Mirror cannot recur at boot surface.

3. **`EnsembleModelZoo_IsReadyForInference` predicate** at `CoreModelZoo.hpp:2137-2151` updated to include Thompson init flag check (.C Step 6). Single source of truth for "is ezoo ready?" — no parallel readiness check.

4. **Persistence symmetry** — `_SaveThompsonState` ↔ `_LoadThompsonState` mirror v5.13.4.C `_SaveExitBanditState` ↔ `_LoadExitBanditState` (verified at `CoreModelZoo.hpp:1887/1942`). This is a single struct family pair (not a 5-fn mirror) and uses `tt::json_io` extracted helpers (.C Step 1) — mirror surface is minimized.

**Remaining mirror surfaces:** ZERO at dispatch / boot / readiness. Single struct save/load pair is unavoidable + uses extracted helpers.

**Verdict:** PASS — Decision A (FOREACH_BANDIT_ALGORITHM) + .C Step 5 (FOREACH_ENSEMBLE_POST_LOAD extension) + .C Step 1 (tt::json_io extraction) + .C Step 6 (IsReadyForInference unified) close ALL 8 prior mirror sites at structural level. Pattern matches v5.14.2.E.1 PostLoadSetup precedent. Adding 4th algorithm = 1 row in registry; recurrence prevented at compile time. Per CLAUDE.md item 19.

---

## DESIGN_SPECS pattern-application audit (Check 27 by-reference /dod-audit)

Pattern catalog walk (17 active DESIGN_SPECS docs at `~/code/tick-trader-percore-workspace/DESIGN_SPECS/`):

| Pattern | Status in amended plan | Notes |
|---|---|---|
| `bitmap-flag-api.md` | APPLIED | Decision D — `thompson_state` byte bit-packs `thompson_bandit_active` (bit 0) + `thompson_chosen_arm` (bits 1-3) per CLAUDE.md item 20 |
| `x-macro-registry-with-presence-dispatch.md` | APPLIED | FOREACH_BANDIT_ALGORITHM (.A Step 4) + FOREACH_CALIB_LOG_COL (.D Step 3) + FOREACH_SLOW_PATH_GATE extension (.B Step 8) + FOREACH_ENSEMBLE_POST_LOAD extension (.C Step 5) |
| `autopopulate-pattern-for-production-caller-class.md` | APPLIED | STAMP_CFG_AUTOPOPULATE auto-flows 4 stamp-bound cfg fields (.B Step 9) |
| `pre-post-cfg-registry-split-for-emit-order-preservation.md` | N/A | No HMAC-locked emit order |
| `wire-format-byte-preservation-discipline.md` | APPLIED | thompson_state.json discipline: format_version=1 + locale pinning + %.17g + %016lx hex (.C Step 3) |
| `cfg-flag-eligibility-criteria.md` | APPLIED-correctly | 5 cfg fields evaluated; all 5 REJECTED for bitmap migration (non-boolean); explicit rejection-with-rationale documented |
| `audit-driven-pre-coding-gate.md` | APPLIED | This re-audit IS the pre-coding gate per the plan's "Mid-sprint audit gate" section |
| `heterogeneous-registry-pattern.md` | N/A | No new domain emerging |
| `structural-fix-preferred-decision-framework.md` | APPLIED | Decision A (FOREACH_BANDIT_ALGORITHM retrofit) + Decision E (.0 layout audit) + .C Step 5 (FOREACH_ENSEMBLE_POST_LOAD extension) all explicit applications |
| `slow-path-gate-registry-pattern.md` | APPLIED | Decision C — THOMPSON_ACTIVE + BANDIT_BOTH_ACTIVE predicates extend FOREACH_SLOW_PATH_GATE per existing pattern at `SlowPathGateRegistry.hpp:69-150` |
| `transient-aggregation-bitmap-pattern.md` | N/A | No transient aggregation surface |
| `partner-core-bitmap-pattern.md` | N/A | No partner-core relationship |
| `per-bit-per-core-override-pattern.md` | N/A (acknowledged) | TECH_DEBT-026 explicitly defers per-core override; pattern noted as future work |
| `registry-tuple-as-single-source-of-truth.md` | APPLIED | FOREACH_BANDIT_ALGORITHM tuple `(name, enum_value, compute_fn, doc_string)` is single source for dispatch table + ToString/FromString + bounds-checked wrapper |
| `autopopulate-from-arity-macro-family.md` | N/A | No multi-arity expansion needed |
| `curve-registry-pattern.md` | APPLIED — REFERENCE | Plan explicitly cites `FOREACH_DEGRADATION_CURVE` at `ConfidenceScore.hpp:498-634` (verified line range) as the canonical shape to mirror for FOREACH_BANDIT_ALGORITHM |

**NEW DESIGN_SPECS docs to ship:** 2
- `per-snapshot-cluster-layout-pattern.md` (ships with .0 — methodology + decision tree for clustering decisions; cross-refs TECH_DEBT-011 + CLAUDE.md item 12)
- `calibration-log-column-registry.md` (ships with .D — canonical reference for FOREACH_CALIB_LOG_COL registry pattern)

**Verdict:** APPLIED across 8 active patterns + 2 NEW patterns shipping. Correctly REJECTED for 4 patterns where N/A (per-bit-per-core, partner-core, transient-aggregation, heterogeneous, autopopulate-from-arity, pre-post-cfg-split). N/A for 3 patterns where surface doesn't apply. **No MISSED candidates.** Plan-time DESIGN_SPECS application is complete.

---

## Version.hpp bump discipline (caller focus #4)

**Verification:** Plan .E Step 5 explicitly lists:
```
Version.hpp bump per sub-tag commit:
  5.14.9 → 5.14.10.0 → .A → .B → .C → .D → .E → 5.14.10 umbrella
  Per memory `feedback_bump_version_per_ship`
```

This is 7 Version.hpp bumps total (one per sub-tag + umbrella). Matches `feedback_bump_version_per_ship` memory rule. PASS.

**Caveat:** Step 5 lives in .E (Tests + propagation phase). The Version.hpp bumps actually happen at EACH sub-tag commit (.0 commit bumps to 5.14.10.0; .A commit bumps to 5.14.10.A; etc.) — NOT all at .E close. Plan's wording could be read as "all bumps land at .E" which would violate the per-ship discipline. **ACTION:** clarify in plan body that "each sub-tag commit bumps Version.hpp to its tag value; .E Step 5 documents the cumulative sequence + the umbrella bump. Per-ship discipline applies." 1-line clarification, ~2 min mechanical fix.

---

## Propagation list completion (caller focus #5)

| Item | Plan location | Verdict |
|---|---|---|
| `DOCS/CHANGELOG.md` entry | .E Step 3 | PASS |
| `engine.cfg.example` doc entries (5 new cfg fields) | .E Step 4 | PASS |
| `DOCS/HOT_PATH_CHANGELOG.md` slow-path entry (cfg=0/1/2 cost breakdown) | .E Step 2 | PASS |
| `Version.hpp` bumps per sub-tag | .E Step 5 | PASS (with clarification per above) |
| Workspace sync via /sync-workspace | .E Step 6 | PASS |

**ALL 4 propagation items addressed.** Was prior-audit GAP — now FIXED.

---

## Latency analysis (Check 23 verify)

Plan's "Latency analysis" section explicitly tabulates:
- cfg=0 (Exp3 default): ~5ns dispatch lookup overhead → 0.005% slow-path budget
- cfg=1 (Thompson only): ~85ns → 0.085% budget
- cfg=2 (Both): ~140ns → 0.14% budget
- Hot path UNTOUCHED, p99 ≤500ns target unaffected
- Cache: unified bandit telemetry cluster occupies 3 cache lines (192 bytes/core); writer-side invalidations 1-3 lines/cycle; reader-side fetches 1-3 lines/frame; ~60 cache misses/sec/core for cfg=1 or cfg=2 — negligible
- Replay determinism: own Box-Muller using raw `mt19937_64::operator()` (NOT std::normal_distribution); SHA-256-locked sample-trace test in .A Step 7

PASS. Per CLAUDE.md item 17, slow-path additions ≥10ns/cycle DO require HOT_PATH_CHANGELOG entry — addressed in .E Step 2.

---

## Hidden scope detected (NEW vs prior audit)

1. **Three citation drifts** in plan body (Check 19 GAP): EngineSharded.hpp:646-694 → ShardedSnapshot.hpp:682-694; ShardedSnapshot.hpp PerCoreSnap → EngineTUI.hpp:980; field name `ensemble_bandit_arm_probs[8]` → actual `ensemble_weights[5][8]` + `ensemble_n_updates_per_regime[5]`. ~10 min mechanical fix BEFORE .0 starts. (Coder will lose this time + risk first-encounter confusion.)

2. **Version.hpp bump location ambiguity** in .E Step 5 wording. ~2 min clarification.

3. **TECH_DEBT-011 wording refresh at ledger** — plan's "substantially closes" is honest framing; the ledger entry should be updated at .0 close to reflect the post-.0 state (clustering done; FOREACH_PER_CORE_SNAP_FIELD migration remains separate). ~5 min.

4. **TECH_DEBT-010 reader-side gap** — plan's .D Step 4 says writer auto-extends from registry; should add 1-line check that no in-engine reader exists OR registry generates parser too. ~2 min check.

5. **MlCfgFlagRegistry.hpp:55-56 doc rot fix** — plan's .D Step 8 covers this (orthogonal cleanup; ~2 min). Was prior-audit recommendation — now baked in.

**Total amendment time before coding: ~20 min mechanical fixes** (vs. prior YELLOW estimate of ~30-60 min must-fix + ~30 min consult).

---

## Recommendations

### MUST FIX before .0 starts (~15-20 min total)

1. **Correct 3 citation drifts** in plan body (Check 19 + cold-pickup C.6):
   - `.D Step 2`: change `EngineSharded.hpp:646-694` → `CoreFrameworks/ShardedSnapshot.hpp:682-694`
   - `.0 Step 1`: change `CoreFrameworks/ShardedSnapshot.hpp` → `DataStream/EngineTUI.hpp:980` for PerCoreSnap struct location
   - Replace mentions of `ensemble_bandit_arm_probs[8]` (which doesn't exist) with the actual field set: `ensemble_weights[5][8]` + `ensemble_n_updates_per_regime[5]`. Update .0 Step 0 ("identify what's currently adjacent to ensemble_bandit_arm_probs") accordingly.

2. **Clarify Version.hpp bump cadence** in .E Step 5: add 1-line "each sub-tag commit bumps Version.hpp at commit time; .E Step 5 documents the cumulative sequence + umbrella bump. Per-ship discipline applies."

### Worth FIXING during coding (no block; ~5-10 min total)

3. **TECH_DEBT-011 ledger refresh** at .0 close — update entry wording to reflect post-.0 state (clustering done; registry migration deferred).
4. **TECH_DEBT-010 reader-side check** at .D Step 4 — confirm no in-engine reader OR add reader-side parser auto-gen.

### Acceptable risk (don't block)

5. TECH_DEBT-026 stays OPEN (LOW future) — correct status.
6. TECH_DEBT-009 stays OPEN — explicit deferral with rationale documented.
7. PARITY-013/014/015 RESOLVED via .B/.A/.D respectively — verify gate row in plan matches implementation.

---

## Verdict: **GREEN (with 15-20 min mechanical citation fixes before .0 starts)**

GREEN — start coding now (after the 3 citation drifts are corrected — they're load-bearing for .0 Step 0 and .D Step 2)
**YELLOW** — fix the must-fix items above first
RED — significant rescope needed; revisit plan

**Rationale:** Amended plan addresses ALL 4 prior must-fix items (heading staleness, propagation list completeness, latency accountability, file:line citations for major REUSE) AND both prior consult-decisions (FOREACH_BANDIT_ALGORITHM registry baked in via Decision A; FOREACH_CALIB_LOG_COL absorbed via Decision B). Mirror-fn audit (Check 24) is FIXED via dual mechanism (registry + PostLoadSetup extension). DESIGN_SPECS coverage is complete (8 patterns APPLIED + 2 NEW shipping). Cold-pickup is 9/10 PASS. TECH_DEBT scan confirms -010/-011/-027 closures realistic; -026 OPEN correct.

Three remaining citation drifts surfaced by deeper grep verification (Check 19 GAP — mild) are mechanical 5-min fixes. They are NOT ship-blocking but ARE load-bearing for .0 Step 0 (which directly cites the wrong field name) and .D Step 2 (which directly cites the wrong write site). Coder would hit drift on first attempted edit.

**GAP delta vs prior audit:** prior had 4 must-fix mechanical + 2 consult-decisions; now has 1 must-fix mechanical (citation drifts grouped as 1 fix). Net reduction: 5 of 6 prior items closed.

Estimate: ~15-20 min mechanical amendment before .0 coding starts. Then GREEN.

---

## Map-update suggestions (post-coding)

- Run `./tools/gen_code_map.sh` after .E — picks up `Thompson_*`, `BanditAlgo_*`, `EnsembleModelZoo_(Init|Save|Load)Thompson*`, `tt::json_io::*`, `BanditAlgo_*_Apply` families.
- Append CHANGELOG.md v5.14.10 row covering: 6 sub-tags + bandit_algorithm cfg + ThompsonBanditState + FOREACH_BANDIT_ALGORITHM + FOREACH_CALIB_LOG_COL + per-snapshot-cluster-layout-pattern.md + calibration-log-column-registry.md.
- Update CLAUDE.md item 13 audited categories list to include FOREACH_BANDIT_ALGORITHM + FOREACH_CALIB_LOG_COL.
- TECH_DEBT-011 entry refresh at .0 close (per recommendation 3 above).
- TECH_DEBT-010 status flip OPEN → CLOSED at .D close (per Decision B).
- TECH_DEBT-027 status flip OPEN → CLOSED at .C Step 4 close.

---

## Attached context

- Amended plan: `/home/caramel/code/FoxML_Trader_v2/plans/v5.14-foxml-port-and-maker/subplans/2026-05-10-v5.14.10-bayesian-thompson-bandit.md`
- Prior /readiness report: `plans/plan_checks/readiness-2026-05-10-v5.14.10-thompson-bandit.md`
- Pre-coding audit synthesis: `plans/plan_checks/2026-05-10-v5.14.10-fresh-audits-synthesis.md`
- 5 prior audit reports (all 2026-05-10): `plans/plan_checks/{parity-check,trace-deps,readiness,merge-scan,dod-audit}-2026-05-10-v5.14.10-thompson-bandit.md`
- TECH_DEBT.md entries -010/-011/-026/-027 walked + verified
- DESIGN_SPECS catalog (17 docs) walked; 8 APPLIED + 2 NEW + 4 N/A documented
- Mirror-fn structural-fix verification: 8 prior mirror sites → 0 remaining via FOREACH_BANDIT_ALGORITHM + FOREACH_ENSEMBLE_POST_LOAD extension
- Cold-pickup: 9/10 PASS, 1 GAP (C.6 stale-claim — same as Check 19 GAP; ~5 min fix)
