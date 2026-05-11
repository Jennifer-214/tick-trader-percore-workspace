# /readiness audit — v5.15 sprint plan

**Audit date:** 2026-05-12
**Auditor:** Claude Opus 4.7 (1M ctx) — Layer 2 Explore-subagent execution per skill spec
**Plan files audited:**
- `plans/v5.15-live-readiness/MASTER.md` (39383 bytes; 643 lines)
- `plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.0-modelhandle-migration.md` (22262 bytes)
- `plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.1-model-health-panel.md` (17335 bytes)
- `plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.2-live-readiness-boot-gate.md` (30005 bytes)
- `plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.3-multi-horizon-worker-stamping.md` (27785 bytes)
- `plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.4-live-mode-strict-defaults.md` (22511 bytes)
- `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` (19030 bytes; cross-referenced)

## Verdict: YELLOW

GREEN once the HIGH-severity findings are addressed (estimated ~30 min of plan edits — all are line-number / API-name citation drift, none require redesign). The sprint architecture is sound; the gaps are mechanical citation hygiene.

## Per-check matrix (30 skill checks)

| # | Check | Status | Notes |
|---|---|---|---|
| 1 | Hot path purity | PASS | All ships explicitly slow-path/boot-only; "Hot path UNTOUCHED" gate in every verification gate. |
| 2 | Train-serve parity | PASS | New `trading_mode` stamp-bound via FOREACH_STAMP_BOUND_CFG; per-horizon stamps via existing FOREACH_STAMP_BOUND_MODEL_CONST + STAMP_MODEL_CONST_AUTOPOPULATE; Surface G `has_*` flags preserve forward-compat. |
| 3 | Surface area | PASS | Per-ship LOC estimates (~150-400 each); largest is v5.15.0 (~630 LOC) — bounded by ModelHandle's caller set; no proliferation of mode-branches. |
| 4 | Pointer init / heap | GAP-LOW | v5.15.4 introduces HotSwapSnapshot with `prev_ezoo` / `prev_single_zoo` pointers and `EnsembleModelZoo_Free` / `CoreModelZoo_Free` on the Discard path. Verify `*_Free` functions exist + ABI matches before coding (no Step 0 grep listed). |
| 5 | Backward compat | PASS | "Forward-compat Surface G `has_*` flags" invariant in MASTER; no MODEL_FORMAT_VERSION bump; legacy stamp load test in v5.15.0.C. |
| 6 | Multi-threading | PASS-WITH-NOTE | v5.15.4 HotSwapSnapshot uses release-acquire pattern correctly; thread-safety section in v5.15.3.C addresses parallel-worker reentrancy. |
| 7 | Test coverage | PASS | Each sub-ship has explicit test count target (+20 ModelHandle, +10 Model Health, +15 boot gate, +15 multi-horizon, +10 hot-swap = ~70 tests; target ~2974 from baseline 2904). |
| 8 | Docs + invariants | PASS | CHANGELOG row planned per sub-ship; HOT_PATH_CHANGELOG addressed inline; TECH_DEBT.md updates per closure; CLAUDE.local.md landmine update for v5.15.3.B. |
| 9 | Forward maintenance | PASS | v5.15.0 ModelHandle migration + v5.15.0.B parser refactor both eliminate Class 18 mirror sources; STAMP_CFG_AUTOPOPULATE + STAMP_MODEL_CONST_AUTOPOPULATE applied. |
| 10 | Rollback story | PASS | Sub-tag-per-phase + `pre-vX.Y.Z` rollback anchors; v5.15.0 explicitly cites `git reset --hard pre-v5.15.0` discipline. |
| 11 | Architectural sprint | PASS-WITH-NOTE | v5.15.0 is a MIGRATION sprint (X-macro registry application); `calls_graph_diff.sh` recommended in verification gates but not all sub-ships explicitly require it. v5.15.0 alone should run it. |
| 12 | Display ↔ execution invariant | PASS | v5.15.1 §C ("Display↔execution invariant") explicitly addresses; every new PerCoreSnap field has its GUI render in same sub-ship. |
| 13 | Strategy lifecycle | N/A | No strategy touched. |
| 14 | X-macro dispatch correctness | PASS | v5.15.0.B parser dispatch table walks FOREACH registry; Test 3 verifies table entry count == registry count. |
| 15 | ML feature change | N/A | FEATURE_REGISTRY_HASH unchanged. |
| 16 | New cfg field with stamp-binding → recipe doc | PASS-WITH-NOTE | trading_mode stamp-binding correct; missing explicit note about updating `DOCS/ML_TEST_RECIPES.md` + `DOCS/PARITY_LIFECYCLE.md` (Check 16 requires both — flagged for inclusion before .A starts). |
| 17 | Model-load path | PASS | New failure modes get PerCoreSnap fields + GUI surface (v5.15.1); 3-tier strict-mode preserved. |
| 18 | Reuse-audit | PASS | v5.15.3 explicitly extracts `stamp_emit_for_horizon` helper as single source-of-truth for serial+parallel callers; v5.15.4 reuses existing BITMAP_IS_SET. |
| 19 | Pre-existing-work / false-NEW + false-REUSE | **GAP — see HIGH findings** | Multiple file:line citations drifted from current HEAD; see HIGH section. |
| 20 | Future-proofness | PASS | All new patterns acknowledged (X-macro registry for parser table; AUTOPOPULATE for trading_mode; bitmap for has_flags). |
| 21 | Test count assertion fragility | PASS | v5.15.0.B Test 3 uses `==` against registry counts — note: should use `>=` per Check 21 (registry could grow); minor. |
| 22 | Auto-trigger downstream re-audit | PASS | MASTER §"Audit cadence" specifies post-v5.15.0 mid-sprint audit suggestion fires when HIGH-RISK ship closes. |
| 23 | Latency accountability | PASS | Each sub-ship has explicit "Latency impact (CLAUDE.md item 17)" section with cost estimate + branchless analysis + HOT_PATH_CHANGELOG decision. |
| 24 | Mirror-function call-sequence | PASS | v5.15.4.B explicitly enumerates that single-zoo + ensemble hot-swap branches both get the snapshot/revert pattern; v5.15.3.B notes XGBoost is sole OpenMP consumer. |
| 25 | TECH_DEBT scan | PASS-WITH-NOTE | All 6 cited TECH_DEBT entries (003, 005, 014, 024, 028, 033) verified in ledger except -033 (planned to be ADDED by v5.15.2.D — correct). Plan acknowledges TECH_DEBT-011, -009, -018, -022, -026, -029, -031, -032 explicitly deferred. |
| 26 | Wider-build verification | SELF-CLOSING | v5.15.2.D adds this check; plan correctly identifies meta-discipline gap. |
| 27 | DOD pattern application | PASS | Each sub-ship has DOD pass with explicit pattern citations (alignas(64), bit-packing, padding determinism, cluster layout). |
| 28 | Test-strength audit | PASS | No weakening claimed; new tests strengthen coverage. |
| 29 | Mechanical citation drift | **GAP — see HIGH findings** | Multiple file:line drifts found (most significant: train_model_worker_fn at 3206 vs actual 2847; Backtest_RunFullValidation at 1147 vs actual 1039). |
| 30 | Predicate-contract-changed | PASS | v5.15.4 normalize pass doesn't extend a shared predicate; HotSwap_Revert is new. |

## HIGH findings (must-amend before coding)

### H.1 — `train_model_worker_fn` line citation drifted (off by ~360 lines)

- **Plan claim** (MASTER + multiple subplans + handoff prompt):
  `Backtest/BacktestPanels.hpp:3206-3266`
- **Actual at HEAD** (`c4e45d1` + post1 `1752fde`):
  `Backtest/BacktestPanels.hpp:2847` (entry line `static inline void *train_model_worker_fn(void *arg)`)
- **Impact:** v5.15.3 cites this as canonical reference for the multi-horizon stamping pattern; v5.15.0 cites it for migration reference. Step 0 of v5.15.3.A says "Locate insert point + verify field availability" with `sed -n '3792,3950p' Backtest/BacktestPanels.hpp` which targets `train_multi_horizon_worker_fn` (correctly), but the PATTERN REFERENCE for canonical stamp emit would mislead anyone using grep on the cited line range.
- **Action:** Update all citations in MASTER §"First concrete move..." + §"References" + v5.15.0 §"Cross-references" + v5.15.3 §"Cross-references" + the handoff prompt to `Backtest/BacktestPanels.hpp:2847-~3000`. Re-grep at plan-edit time to confirm precise end-line.

### H.2 — `Backtest_RunFullValidation` line citation drifted (off by ~110 lines)

- **Plan claim** (MASTER + multiple subplans):
  `Backtest/BacktestEngine.hpp:1147-1220`
- **Actual at HEAD:**
  `Backtest/BacktestEngine.hpp:1039` (entry line)
- **Impact:** v5.15.0 §"Canonical references" + v5.15.3 §"Cross-references" both cite this as the migration-pattern sibling. Step 0 references would land in the wrong region.
- **Action:** Update all citations to `Backtest/BacktestEngine.hpp:1039-~1220` (approximate; end-line varies with whole-function span).

### H.3 — `STAMP_HAS / SET / CLR` macros cited at wrong file

- **Plan claim** (MASTER §"Cold-pickup completeness" item 4):
  `STAMP_HAS / SET / CLR macros at MemHeaders/BitmapMacros.hpp:78-90`
- **Actual at HEAD:**
  `ML_Headers/StampBoundModelConstRegistry.hpp:567-569` (STAMP_HAS / SET / CLR are aliases of BITMAP_* defined there)
  `MemHeaders/BitmapMacros.hpp:78-90` defines GENERIC `BITMAP_IS_SET / SET / CLR / TOGGLE / ANY / ALL` macros (not STAMP_*).
- **Impact:** v5.15.0.A Step 3 says "Reuse pattern from ModelStampResult (already established). Define in `ML_Headers/ModelInference.hpp` if not already" — implies the STAMP_HAS variant for ModelHandle may need to be defined fresh. Net effect: the citation is misleading but the plan still works because Step 3 doesn't depend on the exact citation location.
- **Action:** Correct MASTER §4 line to `STAMP_HAS / SET / CLR macros at ML_Headers/StampBoundModelConstRegistry.hpp:567-569; underlying BITMAP_* primitives at MemHeaders/BitmapMacros.hpp:78-99`. Also note v5.15.0 will need to introduce HANDLE_HAS / SET / CLR aliases (not yet defined; the plan implicitly assumes this via Step 3 — make it explicit).

### H.4 — `tt::stamp_parse_field<T>` cited at wrong line

- **Plan claim** (v5.15.0.B Step 1):
  `ML_Headers/StampBoundModelConstRegistry.hpp:680+`
- **Actual at HEAD:**
  `ML_Headers/StampBoundModelConstRegistry.hpp:86-99` (forward declaration `inline double parse_double_fast(const char* s);` at :99, definition logic in surrounding lines)
- **Impact:** v5.15.0.B EXPAND_PARSER_ROW macro design depends on calling `tt::stamp_parse_field<T>`; coder grepping line 680 would land near `STAMP_MODEL_CONST_AUTOPOPULATE_ONE` at :680 instead.
- **Action:** Correct citation to `ML_Headers/StampBoundModelConstRegistry.hpp:86+` (or grep `tt::stamp_parse_field` at plan-edit time for precise line).

### H.5 — Wrong macro names in v5.15.0.B Test 3

- **Plan claim** (v5.15.0.B Test 3):
  ```cpp
  int registry_count = STAMP_BOUND_MODEL_CONST_ENTRY_COUNT + STAMP_BOUND_CFG_ENTRY_COUNT;
  ```
- **Actual at HEAD:** the macros are `FOREACH_STAMP_BOUND_MODEL_CONST_COUNT` and `FOREACH_STAMP_BOUND_CFG_COUNT` (with the `FOREACH_` prefix preserved).
- **Action:** Update Test 3 to use the actual macro names.

### H.6 — Wrong FAILURE_* API shape in v5.15.1.A

- **Plan claim** (v5.15.1 §A Step 2):
  ```cpp
  FAILURE_SET(per_core_snap.failure_flags, BUILD_FLAGS_DRIFT);
  ```
- **Actual API at `MemHeaders/FailureModeRegistry.hpp:236`:**
  ```cpp
  #define FAILURE_SET(snap, name)  BITMAP_SET((snap).failure_flags, FAILURE_MASK_##name)
  ```
  So it should be `FAILURE_SET(per_core_snap, BUILD_FLAGS_DRIFT)` — i.e., pass the SNAPSHOT struct, not its `failure_flags` field. The macro internally accesses `.failure_flags`.
- **Plan claim** (v5.15.1 §B + §C):
  Uses `MASK_FAILURE_*` constants (e.g., `MASK_FAILURE_FEATURE_HASH_DRIFT`).
- **Actual at HEAD:** mask constants are `FAILURE_MASK_*` (e.g., `FAILURE_MASK_feature_hash_drift`). Note also: masks use the lowercase `name` form per FAILURE_MASK_DECL_BIT_FLAG generator. So `MASK_FAILURE_FEATURE_HASH_DRIFT` should be `FAILURE_MASK_feature_hash_drift`.
- **Action:** Update v5.15.1 to use correct API: `FAILURE_SET(pc, X)` not `FAILURE_SET(pc.failure_flags, X)`; `FAILURE_MASK_<name>` not `MASK_FAILURE_<NAME>`. Same correction applies to v5.15.2.B (LiveReadiness checks reference `MASK_FAILURE_MODEL_AGE_WARN` etc.).

### H.7 — `tt::GROUP_DRIFT` does not exist; must be added

- **Plan claim** (v5.15.1 §A Step 1): registry entries tagged `tt::GROUP_DRIFT`.
- **Actual at HEAD** (`MemHeaders/FailureModeRegistry.hpp:97-100`):
  ```cpp
  GROUP_STANDALONE  = 0,
  GROUP_NAN_EVENTS  = 1,
  ```
  `GROUP_DRIFT` does not exist.
- **Impact:** v5.15.1 §C Header design uses `FOREACH_FAILURE_MODE_IN_GROUP(GROUP_DRIFT, X_RENDER_DRIFT_ROW)` — that macro doesn't exist either.
- **Action:** Either (a) add `GROUP_DRIFT = 2` to the namespace tt enum in v5.15.1.A Step 0.5 (explicit), AND introduce `FOREACH_FAILURE_MODE_IN_GROUP` filter macro, OR (b) reuse `GROUP_STANDALONE` and let the Model Health header iterate by mask. Choose now to avoid mid-coding scope inflation. Recommend (a) — it's still ≤15 LOC and keeps the group-based filter pattern available for future drift cohorts.

## MEDIUM findings (consider amending)

### M.1 — PerCoreStateFlagsRegistry has 7 entries, not 6

- **Plan claim** (v5.15.1 §B Step 0): "6 existing state_flags entries; +4 = 10 of 16 used"
- **Actual** (`MemHeaders/PerCoreStateFlagsRegistry.hpp:67-88`): 7 entries (PERMISSION_ALLOWED, BITMAP_CONSISTENT, GATE_BUY_ABOVE, IS_ML, ML_MODEL_LOADED, STRATEGY_EXPLICITLY_SET, LADDER_BOTTOM_HIT). +4 = 11 of 16. Still safe but plan count is off by 1.
- **Action:** Update v5.15.1 §B Step 0 expected: "7 existing state_flags entries; +4 = 11 of 16 used; safe."

### M.2 — `model_verify_strict` line claim mixes declaration + default

- **Plan claim** (MASTER §"Stale-claim audit"): `model_verify_strict (1538)`
- **Actual** (`CoreFrameworks/ControllerConfig.hpp`): declaration at line **882**; default-init at line 1538.
- **Action:** Clarify the citation: declaration at :882, default-init at :1538.

### M.3 — v5.15.0.A 14 vs 16 has_* count inconsistency in MASTER vs subplan

- **MASTER claim** §"Why this sprint exists": "16 uint8_t `has_*` direct fields"
- **MASTER claim** §"Cold-pickup completeness" item 4: "16 uint8_t has_* fields"
- **v5.15.0 subplan** §"Why this subplan exists": "**14 uint8_t `has_*` direct fields**"
- **Actual** (`ML_Headers/ModelInference.hpp` greps): 14 uint8_t has_* fields (verified by `rg -n "^\s*uint8_t\s+has_" ML_Headers/ModelInference.hpp` → 14 hits at lines 267, 269, 274, 284, 290, 295, 297, 306, 313, 323, 328, 330, 339, 341).
- **Action:** MASTER says 16 in two places; subplan says 14 (correct). Update MASTER to 14 to reconcile. Plan also says "16 uint8_t has_* fields" in §"Why this sprint exists" — same fix.

### M.4 — v5.15.4 cites hot-swap line range 2836-2860 covers only the entry of each branch

- **Plan claim** (MASTER + v5.15.4): `EngineSharded.hpp:2836-2860` = "TWO branches (single-zoo at :2836, ensemble at :2846)"
- **Actual** (`CoreFrameworks/EngineSharded.hpp`):
  - Hot-swap pickup block starts at :2796
  - REFUSE path (`swap_zoo == nullptr`) at :2837-2845 (this is the "single-zoo" of the plan — but it's the EARLY-EXIT REFUSE, not a "swap" branch)
  - Ensemble swap branch at :2846-2913 (`else if (ensemble_handle != nullptr)`)
  - Single-zoo SWAP branch at :2914-onward (`else` branch)
- **Impact:** v5.15.4.B Step 0 grep `sed -n '2800,2870p'` would miss the actual single-zoo swap site at 2914+. The plan's diagram in §"Why this subplan exists" labels the single-zoo branch as line ~2836, which is the REFUSE check, not the swap. The actual single-zoo swap branch is line ~2914-3000.
- **Action:** Update v5.15.4 §B Step 0 to grep `sed -n '2796,3050p'` for the full hot-swap dispatch; correct the line refs in §"Why this subplan exists" + §B Site 1/Site 2 to single-zoo at :2914+ and ensemble at :2846+.

### M.5 — v5.15.3 cites foxml_suite.cpp path inconsistently

- **Plan claim** (v5.15.3 §B Step 1): `foxml_suite.cpp:main()`
- **Actual:** `/home/caramel/code/FoxML_Trader_v2/foxml_suite.cpp` (repo ROOT, not under `GUI/`). Plan uses correct path; just confirming.
- **Note:** The CLAUDE.local.md landmine entry says "(workspace-private file; sync via /sync-workspace)" — when updating it, sync workspace per CLAUDE.local.md auto-write rule.

### M.6 — Effort estimate sanity check: v5.15.0 hold up at ~630 LOC?

- **Plan claim:** v5.15.0 total ~400 LOC migration + ~150 LOC parser + ~80 LOC tests = ~630 LOC
- **Reality check:**
  - 14 has_* field migration × ~25-40 read sites + ~30-50 write sites = ~55-90 line edits (mostly 1-line each)
  - Parser refactor from ~700 LOC if-else chain → ~40 LOC dispatch loop + ~30 row table-init lines = ~70 LOC NEW + ~700 LOC REMOVED. Net negative LOC (~-600).
  - Tests ~80 LOC
- **Verdict:** ~150 LOC NET added; plan's ~630 LOC is the GROSS edit count (touches), not net. Both interpretations valid; flag is informational.

### M.7 — engine.cfg.example update missing from v5.15.2 + v5.15.4 explicit files-touched

- **Plan v5.15.2 §A Step 2** includes an engine.cfg.example row sketch ✓ — good.
- **Plan v5.15.4** does NOT update engine.cfg.example for the normalize-pass behavior change. The post-parse normalize is operator-visible (operator's effective cfg differs from what they wrote); should be documented in engine.cfg.example comments OR in a CHANGELOG-style note.
- **Action:** Add to v5.15.4 verification gate: "engine.cfg.example documentation comment added near reconcile_mode + model_verify_strict explaining the live-mode flip behavior."

## LOW findings (informational)

### L.1 — v5.15.2.A Step 4 cites `cfg_had_explicit_trading_mode_key` — flag-tracking infrastructure

The boot WARN for legacy cfgs uses `cfg_had_explicit_trading_mode_key`. This requires extending the parser to track which keys were seen. v5.15.4 also depends on this (`ControllerConfigKeyExplicit` struct). v5.15.2.A doesn't explicitly say "add this tracking"; v5.15.4.A Step 0 mentions "if tracking infrastructure absent, build minimal bitmap in .A." Sequencing: v5.15.2.A or v5.15.4.A needs to land it FIRST. Cleaner: v5.15.2.A introduces it (since v5.15.2 introduces trading_mode), and v5.15.4 reuses.

### L.2 — `Backtest/StampBody.hpp` referenced in /readiness skill but doesn't exist

The /readiness skill spec at line 882-883 says `grep -n "has_<X>" ML_Headers/StampInference.hpp Backtest/StampBody.hpp`. Neither file exists in this codebase (parser lives in `ML_Headers/ModelInference.hpp`; stamp body emit lives in `ML_Headers/StampBoundModelConstRegistry.hpp` + `ML_Headers/StampBoundCfgRegistry.hpp`). Not a plan defect — this is a skill spec staleness for a different sprint. Logged informational only.

### L.3 — v5.15.2.B kLiveReadinessChecks[] uses C++ constexpr lambda complexity

`kLiveReadinessChecks` is `static constexpr LiveReadinessCheck<F>[]` with function pointer initializers. C++17 requires the function-pointer expressions to be constant. Defined per-template-instantiation. Cost: harmless redundant per-F binary copy of the table. If F is single-valued (F=64 typical), only one instantiation exists. Flagged for awareness; not blocking.

### L.4 — v5.15.4 normalize stamp body change vs HMAC byte-equivalence: tension acknowledged

§A Step 3 + DOD table state: "legacy cfg WITHOUT explicit override produces DIFFERENT stamp under live mode (intentional change documented in CHANGELOG)." Good. But this also means cross-binary replay-determinism (CLAUDE.md item 25) doesn't hold for legacy-cfg+live-mode runs. Verify intent: the operator's mental model should be "training-time normalized cfg, including live-mode flips, is what the stamp records — to retrain with the same effective cfg, set the flipped values explicitly." Acknowledged but warrants a sentence in the v5.15.4 CHANGELOG entry.

## Stale claims verified (file:line evidence)

| Plan claim | Verified | Action |
|---|---|---|
| `ModelHandle` struct at `ML_Headers/ModelInference.hpp:239` | ✅ Verified at line 239 | OK |
| 14 has_* fields in ModelHandle | ✅ 14 entries at lines 267/269/274/284/290/295/297/306/313/323/328/330/339/341 | OK; MASTER says 16 in two places — needs reconcile (M.3) |
| `FOREACH_STAMP_BOUND_CFG` 7-column tuple at `StampBoundCfgRegistry.hpp:99` | ✅ Confirmed; 7-tuple is `(name, type, fmt, default_val, get_cfg_expr, emit_when, emit_source)` | OK |
| `STAMP_MODEL_CONST_AUTOPOPULATE` at `StampBoundModelConstRegistry.hpp:601` | ✅ Confirmed at line 601 | OK |
| `breakeven_on_profit` dormant at `LifecycleCfgFlagRegistry.hpp:58` | ✅ Confirmed; DORMANT marker present | OK |
| `breakeven_on_partial` wired at `PortfolioController.hpp:670` | ✅ Confirmed | OK |
| `train_multi_horizon_worker_fn` at `Backtest/BacktestPanels.hpp:3792` | ✅ Confirmed | OK |
| `mh_per_horizon_parallel_worker` at `Backtest/BacktestPanels.hpp:3763` | ✅ Confirmed | OK |
| `train_model_worker_fn` at `Backtest/BacktestPanels.hpp:3206-3266` | ❌ **Actual line 2847** | **H.1** |
| `Backtest_RunFullValidation` at `Backtest/BacktestEngine.hpp:1147-1220` | ❌ **Actual line 1039** | **H.2** |
| `MLStatusPanel.hpp` at `GUI/MLStatusPanel.hpp` | ✅ Confirmed (28553 bytes; ~504 LOC) | OK |
| CollapsingHeaders at MLStatusPanel.hpp:320 ("Ensemble") + :420 ("Thompson") | ✅ Confirmed at lines 320 + 420 | OK |
| `FOREACH_FAILURE_MODE` at `MemHeaders/FailureModeRegistry.hpp:122` | ✅ Confirmed | OK |
| uint16_t failure_flags with 2 BIT_FLAG entries pre-v5.15 | ✅ Confirmed (entries 1+2: ml_model_load_failed, ml_scaler_load_failed at lines 123, 130; PERCENT_U8 + COUNTER_U32 entries don't take bitmap bits) | OK |
| static_assert at FailureModeRegistry.hpp:212 | ✅ Confirmed (FAILURE_BIT_COUNT <= 16) | OK |
| Engine hot-swap at `EngineSharded.hpp:2836-2860` "TWO branches single-zoo + ensemble" | ⚠️ **Single-zoo SWAP is at :2914+, not :2836** | **M.4** |
| foxml_suite.cpp main at line 86 | ✅ Confirmed | OK |
| XGBoost SOLE OpenMP consumer | ✅ Verified — only hits: `<omp.h>` include at BacktestPanels.hpp:25, `omp_set_num_threads(1)` at :3772 (v5.11.44 hotfix); no `#pragma omp` anywhere | OK |
| `cfg.engine_mode` exists for SHARDED/SINGLE_CORE | ✅ Confirmed at line 885 (`ENGINE_MODE_SINGLE_CORE=0`, `ENGINE_MODE_SHARDED=1`); parser at :2396 | OK |
| `cfg.trading_mode` does NOT exist | ✅ Confirmed (0 hits) | OK; v5.15.2 introduces it |
| `cfg.reconcile_mode` parser at `ControllerConfig.hpp:2371-2381` | ✅ Confirmed | OK |
| PerCoreSnap at `DataStream/EngineTUI.hpp:981` | ✅ Confirmed | OK |
| 4 bool-as-uint8 fields target (ml_scaler_present etc.) at PerCoreSnap | ✅ Verified at EngineTUI.hpp:1129/1156/1161/1162 (entries exist; TECH_DEBT-028 valid) | OK |
| `PerCoreStateFlagsRegistry.hpp` exists with FOREACH_PER_CORE_STATE_FLAG | ✅ Confirmed at `MemHeaders/PerCoreStateFlagsRegistry.hpp:67` | OK |
| 6 existing state_flags entries | ❌ **Actual 7** | **M.1** |
| `STATE_FLAG_IS_SET / SET / CLR` API exists | ✅ Confirmed at `MemHeaders/PerCoreStateFlagsRegistry.hpp:132-134` | OK |
| `tt::GROUP_DRIFT` exists | ❌ Only GROUP_STANDALONE=0, GROUP_NAN_EVENTS=1 exist | **H.7** |
| `STAMP_HAS / SET / CLR` macros at `MemHeaders/BitmapMacros.hpp:78-90` | ❌ **Actual at `ML_Headers/StampBoundModelConstRegistry.hpp:567-569`** | **H.3** |
| `tt::stamp_parse_field<T>` at `StampBoundModelConstRegistry.hpp:680+` | ❌ **Actual at :86+** | **H.4** |
| TECH_DEBT-003 / -005 / -014 / -024 / -028 exist in workspace ledger | ✅ Verified (lines 120, 145, 367, 562, 618) | OK |
| TECH_DEBT-033 absent | ✅ Confirmed (0 hits) | OK; v5.15.2.D adds it |
| v5.14 tag at commit `c4e45d1` | ✅ Confirmed | OK |
| v5.14.post1 patch at commit `1752fde` | ✅ Confirmed | OK |
| Engine sprint baseline ~2904 tests | ✅ Plausible (`tests_passed` counter at controller_test.cpp:63; full count requires test run not done here) | OK; treat as handoff claim |

## TECH_DEBT scan results (overlapping entries v5.15 should/shouldn't absorb)

Per CLAUDE.local.md "deferred items must be queryable" rule, scanned `tick-trader-percore-workspace/DOCS/TECH_DEBT.md` for entries whose surface area overlaps v5.15 files-touched.

**Open entries v5.15 plan covers:**
- TECH_DEBT-003 (verify_model_stamp parser refactor) → v5.15.0 ✓
- TECH_DEBT-005 (single-zoo hot-swap unification) → v5.15.4 (broadened to BOTH surfaces) ✓
- TECH_DEBT-014 (ModelHandle migration) → v5.15.0 ✓
- TECH_DEBT-024 (breakeven_on_profit wire-up) → v5.15.2 ✓
- TECH_DEBT-028 (PerCoreSnap bool-as-uint8 migration) → v5.15.1 ✓
- TECH_DEBT-033 (/readiness wider-build check) → v5.15.2.D (plan writes the entry) ✓

**Open entries v5.15 plan EXPLICITLY DEFERS (with rationale documented):**
- TECH_DEBT-011 (FOREACH_PER_CORE_SNAP_FIELD full registry) — 10-15h architectural ship; would scope-creep v5.15.1 by ~5x ✓ reasonable
- TECH_DEBT-009 (FOREACH_CFG_FIELD non-bool subset) — trigger requires 3+ new non-bool cfg fields; v5.15 adds 1 (trading_mode) ✓ reasonable
- TECH_DEBT-018 (/precoding-audit Layer 1 orchestrator skill) — workflow improvement ✓
- TECH_DEBT-022 (cfg parser perfect-hash dispatch) — boot-only optimization; not live-readiness scope ✓
- TECH_DEBT-026 (per-core bandit_algorithm override) — different feature ✓
- TECH_DEBT-029 (Source file length reduction) — separate cleanup sprint ✓
- TECH_DEBT-031 (MetricsLog FOREACH registry) — different surface ✓
- TECH_DEBT-032 (CLAUDE.md context-management cleanup) — separate sprint ✓

**Open entries v5.15 does NOT mention but COULD absorb (consider):**

- **TECH_DEBT-012** — FOREACH_OMS_STATE registry for OrderManager state fields. v5.15.2 touches `PortfolioController.hpp` near `breakeven_on_partial`/`breakeven_on_profit`. Surface overlap with OMS state is minor (breakeven flags are lifecycle_cfg_flags, not OMS state). No absorb needed — different surface despite proximate filenames. **Verdict: leave deferred.**
- **TECH_DEBT-001** — `tools/stamp_model.sh` bash CLI replacement with C++ wrapper. v5.15.2 introduces `trading_mode` cfg field stamp-bound; `tools/stamp_model.sh` would need `--trading_mode` flag added (per /readiness Check 16). Plan v5.15.2.A doesn't mention this. **Verdict: ⚠️ should add to v5.15.2.A — operators using `stamp_model.sh` won't be able to pre-stamp models with trading_mode otherwise.** Minor scope addition (~20 LOC bash). Or explicitly defer with rationale (e.g., "operators use STAMP_CFG_AUTOPOPULATE via production callers; bash CLI gap acknowledged in TECH_DEBT-001").
- **TECH_DEBT-027** — Locale pinning gap in `Bandit_SaveJSON` (LC_NUMERIC drift risk). Independent surface; no v5.15 touch needed. **Verdict: leave deferred.**

**Recommendation:** Add a one-paragraph note to v5.15.2.A acknowledging tools/stamp_model.sh trading_mode flag gap (close as TECH_DEBT-001 dependency OR add the flag in same ship; minor).

## Cohort audit verdict (trading_mode)

Per CLAUDE.local.md going-forward rule 2026-05-11 (cohort-audit when new cfg field has siblings), verified:

| Sibling | Type | Boolean? | BIT_FLAG-eligible? |
|---|---|---|---|
| `reconcile_mode` | uint8_t (enum: 0=STRICT, 1=WARN, 2=AUTO_SYNC) | No (3-state enum) | No |
| `model_verify_strict` | int (tri-state: -1=skip, 0=warn, 1=strict) | No (3-state) | No |
| `trading_mode` | uint8_t (enum: 0=PAPER, 1=LIVE, 2=SHADOW) | No (3-state enum) | No |

**Verdict:** All 3 are enum-valued, not boolean. Per `cfg-flag-eligibility-criteria.md` Criteria 1 (boolean-only), the cohort is homogeneous enum-class; no migration needed. Direct uint8_t/int storage is correct for all three.

**Plan v5.15.2 DOD table** correctly documents this verdict at the "Cohort audit verdict" row. ✓ Verdict is correct AND documented.

## Synthesis (1-paragraph: ready to code? what to fix?)

The v5.15 sprint plan is **architecturally sound + ready to code after a ~30 minute citation-cleanup pass**. The plan correctly applies all v5.14-era discipline (X-macro registries, AUTOPOPULATE companions, bit-packed has_flags, Surface G `has_*` flags for forward-compat, stamp-binding via FOREACH_STAMP_BOUND_CFG, per-snapshot cluster layout). The cohort audit for `trading_mode` is correct + documented. TECH_DEBT scan shows all 6 cited closures are valid + the deferred-entry list is well-justified, with one absorbable consideration (TECH_DEBT-001 stamp_model.sh trading_mode flag — minor add or document defer). The **HIGH findings are entirely mechanical citation drift** — `train_model_worker_fn` is at line 2847 not 3206 (off by ~360 lines), `Backtest_RunFullValidation` is at 1039 not 1147 (off by ~110 lines), `STAMP_HAS / SET / CLR` are at StampBoundModelConstRegistry.hpp:567 not BitmapMacros.hpp:78, the FAILURE_* API plan uses (`MASK_FAILURE_*`, `FAILURE_SET(pc.failure_flags, X)`) doesn't match the actual API (`FAILURE_MASK_<name>`, `FAILURE_SET(pc, X)`), and `tt::GROUP_DRIFT` doesn't exist (must be added as Step 0.5 of v5.15.1.A). These are exactly the v5.14.10-class "mechanical citation drift" hits (Check 29) — non-blocking to architecture but Step 0 of coding would trip without the fixes. Recommend: amend the 7 HIGH items + the 7 MEDIUM items in a single sweep at plan-edit time (30 min total), then GREEN to start v5.15.0 with the pre-coding audit gate (`/parity-check + /trace-deps + /readiness + /dod-audit` in parallel) as MASTER specifies.
