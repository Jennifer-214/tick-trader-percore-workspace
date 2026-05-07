# /readiness report — 2026-05-06-v5.10.1-production-caller-closure.md — 2026-05-06

**Plan audited:** `plans/2026-05-06-v5.10.1-production-caller-closure.md`
**Sprint:** v5.10 close (gates Sprint C v5.11.0 kickoff alongside v5.10.2 + .3)
**Branch (claimed):** `experiment/per-core-sharding` (default branch; Sprint B sub-ship cadence)
**Predecessor:** v5.10.0e at commit `f340c37`, Sprint B merge at `7f0b9a9` (verified in git log)
**Audit driver:** `plans/plan_checks/parity-2026-05-06-full.md` Findings #1, #2, #6
**Audit run by:** Claude Opus 4.7 (1M context), readiness skill
**Audit date:** 2026-05-06

---

## Plan summary

v5.10.1 closes 2 CRITICAL + 1 HIGH parity-check findings — fields silently dead in production despite verifier coverage. Three phases:

- **A (`v5.10.1.A`)** — `LABEL_REGISTRY_HASH` plumb-through. 4 sites: BacktestEngine.hpp RFV emit + BacktestPanels.hpp×2 (worker emit + Verify Stamp consume) + CoreModelZoo.hpp consume. Effort 30m / ~8 LOC.
- **B (`v5.10.1.B`)** — `grid_member_count` per-horizon emit + AutoDetect consistency validator. Effort 1.5h / ~40 LOC.
- **C (`v5.10.1.C`)** — `EnsembleModelZoo_AutoDetectFromDir` strict/gap/secret/drift args plumb-through. 2 call sites (EngineSharded + BacktestSharded). Effort 30m / ~6 LOC.

Hot path UNTOUCHED (verifier work + emit-site work only).

---

## Checklist verdicts (17-item)

| # | Item | Verdict | Notes |
|---|---|---|---|
| 1 | Plan goal stated up front | PASS | Lines 13-19: theme is explicit. Same regression class as v5.9.5b cited. |
| 2 | Phases ordered in dependency order | PASS | A → B → C. Phases are independent (no internal dep edges); plan correctly notes "can ship in any order, A first since smallest." |
| 3 | Each phase has a Step 0 (concrete first move) | PASS | A: insert 2-line block at BacktestEngine.hpp:1140 neighborhood. B: spot-check BacktestEngine.hpp:1019-1184 for horizon loop, then per-horizon code shape. C: insert 4 args at EngineSharded.hpp:832 + BacktestSharded.hpp:296. |
| 4 | All function/macro names cited exist | PASS-with-1-NIT | Verified: `LABEL_REGISTRY_HASH()` (LabelFunctions.hpp:345), `verify_model_stamp` 6-arg (ModelInference.hpp:1005-1010), `stamp_write_for_model` (1495-1507), `EnsembleModelZoo_AutoDetectFromDir` 7-arg (CoreModelZoo.hpp:1120-1127), `inf.has_label_registry_hash` (1491), `inf.has_grid_member_count`/`grid_member_count`/`grid_member_idx` (1484-1486), `EnsembleModelZoo_Free` (986). NIT: plan's B.2 validator code references `role_arr[h].stamp_result.has_grid_member_count` — **`ModelHandle` has no `stamp_result` field** (see Hidden Scope #1). |
| 5 | All file:line refs verified vs HEAD | PASS | 14 of 15 refs spot-checked directly: BacktestEngine.hpp:1019 ✓, :1105 (`has_inference_cfg=1`) ✓, :1140 (`has_xgb_hyperparams=1`) ✓, :1167 (`has_build_flags_hash=1`) ✓, :1172 (`stamp_write_for_model`) ✓; BacktestPanels.hpp:2641 (`StampInferenceCfgInputs inf={}`) ✓, :2699 (`stamp_write_for_model`) ✓, :1289 (`verify_model_stamp`) ✓; CoreModelZoo.hpp:134 (`verify_model_stamp` call) ✓, :1120 (AutoDetectFromDir) ✓, :1211 (`EnsembleModelZoo_LoadFromCfg` call) ✓, :1093-1114 (docstring describing unimpl check) ✓; EngineSharded.hpp:832 (drops args) ✓; BacktestSharded.hpp:296 (drops args) ✓; tests/controller_test.cpp:13331 ✓ + :13751 (existing synthetic grid_member test) ✓; :10251 (replay-determinism) ✓. |
| 6 | LOC estimate reconciled to file size deltas | PASS-with-FLAG | Plan claims ~140 LOC delta (~54 src + ~85 test). Phase A reconciles fine. **Phase B underestimated** (see Hidden Scope #2): per-horizon emit assumption is wrong AND ModelHandle needs new fields. Realistic Phase B is 80-120 LOC source + tests. |
| 7 | Source-audit refs cited with paths | PASS | parity-2026-05-06-full.md (Findings #1, #2, #6) — exists in plan_checks/ verified. References to `.claude/skills/parity-check/SKILL.md` § Section L cited. |
| 8 | Predecessor and successor named with paths | PASS | Predecessor v5.10.0e f340c37 + 7f0b9a9; sister sub-plans 2026-05-06-v5.10.2-hot-swap-parity.md + v5.10.3-display-observability.md (TBD); v5.11.0 successor at 2026-05-06-v5.11.0-system-foundation.md (audited GREEN+); MASTER plan cited. |
| 9 | Tag names locked + rollback anchor named | PASS | `pre-v5.10.1` + `v5.10.1.A/B/C` + final `v5.10.1`. Push command at lines 224-233 explicit. |
| 10 | Stale-claim audit performed before write | PASS | Section at lines 237-262: 15 claims, 14 VERIFIED + 1 ACCEPTED (replay-determinism test). I re-checked 8 independently — all true. |
| 11 | Hot path UNTOUCHED (or modifications justified) | PASS | Plan grep returns 0 matches for `BG_Evaluate`/`SG_Evaluate`/`ExecutionCore_Tick` modifications. All edits are stamp emit / verify call sites — slow-path / orchestration code. |
| 12 | Display ↔ execution invariant respected | PASS (N/A) | No new hot-path predicate terms; no new GUI surface obligation triggered. |
| 13 | X-macro registry pattern used where multi-site addition | PASS (N/A) | LABEL_REGISTRY_HASH already uses FOREACH_TARGET (LabelFunctions.hpp:340). Phase B's grid_member_count is 1 field, not a registry-eligible category. |
| 14 | NaN-free feature pack (v5.9.0+) preserved | PASS (N/A) | Plan doesn't modify `Features_PackAll` or feature compute path. |
| 15 | Parity-tested-by-construction lifecycle respected | PASS | Plan IS the parity-lifecycle closure ship — every emit-side change is matched by consume-side change (A: emit + consume both; B: emit + consume validator both; C: consume args). Round-trip test for A.4 mirrors the v5.10.0d existing-synthetic-test pattern but uses production helpers. |
| 16 | Failure telemetry path captured by operator's logging | PASS | All new errors go to stderr via `fprintf(stderr, ...)` matching existing engine pattern. AutoDetect's `[ensemble_auto_detect] REFUSED:` log goes through same channel as `[ensemble] auto-detected ...` at CoreModelZoo.hpp:1227. |
| 17 | Resource cleanup paths covered | PASS-with-NIT | B.2 validator calls `EnsembleModelZoo_Free(ezoo)` on REFUSE — verified Free() exists at CoreModelZoo.hpp:986. NIT: plan's `return -1;` from AutoDetectFromDir is INCONSISTENT with the function's documented contract — function returns "total models loaded" (return 0 for failure per existing :1166, :1192). Should return 0, not -1. See Hidden Scope #4. |

---

## Dependency verification (claimed deps + verification)

| Plan claim | Verification | Status |
|---|---|---|
| `Backtest_RunFullValidation` def | BacktestEngine.hpp:1019 — exact match | VERIFIED |
| `inf.has_inference_cfg = 1` (RFV emit start) | BacktestEngine.hpp:1105 — exact match | VERIFIED |
| `inf.has_xgb_hyperparams = 1` (insert neighbor) | BacktestEngine.hpp:1140 — exact match | VERIFIED |
| `inf.has_build_flags_hash = 1` (alt insert) | BacktestEngine.hpp:1167-1168 — exact match | VERIFIED |
| `verify_model_stamp(...)` in CoreModelZoo_TryLoadRole | CoreModelZoo.hpp:134-138 — 5 args confirmed (drops 6th) | VERIFIED |
| `StampInferenceCfgInputs inf = {}` (worker init) | BacktestPanels.hpp:2641 — exact match | VERIFIED |
| `stamp_write_for_model(...)` worker emit | BacktestPanels.hpp:2699-2710 — exact match | VERIFIED |
| `verify_model_stamp(...)` Verify Stamp UI | BacktestPanels.hpp:1289-1294 — 5 args (drops 6th) | VERIFIED |
| `EnsembleModelZoo_AutoDetectFromDir` def + 7 args | CoreModelZoo.hpp:1120-1127 — confirmed `secret/gap/strict/ack_drift` arg order | VERIFIED |
| `EnsembleModelZoo_LoadFromCfg` call inside AutoDetect | CoreModelZoo.hpp:1211-1217 — exact match | VERIFIED |
| AutoDetect docstring describes unimpl check | CoreModelZoo.hpp:1093-1114 — exact match | VERIFIED |
| Live AutoDetect call drops args | EngineSharded.hpp:832-835 — confirmed 3-arg call (drops 4) | VERIFIED |
| Backtest AutoDetect call drops args | BacktestSharded.hpp:296-299 — confirmed 3-arg call (drops 4) | VERIFIED |
| Existing synthetic LABEL_REGISTRY_HASH test | tests/controller_test.cpp:13331-13343 — full v5.10.0d test confirmed (lines 13325-13360) | VERIFIED |
| Existing synthetic grid_member_count test | tests/controller_test.cpp:13751 — synthetic StampInferenceCfgInputs test confirmed | VERIFIED |
| Replay-determinism test | tests/controller_test.cpp:10251 — exact match | VERIFIED |
| `verify_model_stamp` 6-arg sig accepts `expected_label_registry_hash` | ModelInference.hpp:1005-1010 — confirmed; default 0 | VERIFIED |
| `stamp_write_for_model` accepts `inf*` | ModelInference.hpp:1495-1507 — confirmed | VERIFIED |
| Refusal logic for label hash mismatch | ModelInference.hpp:1300-1321 — confirmed; `if (expected_label_registry_hash != 0)` guard at 1306 | VERIFIED |
| Verifier back-compat for `has_grid_member_count=0` | ModelInference.hpp:1058 (zero-init), parser 1232-1238 (sets has_*=1 only on parse) | VERIFIED — back-compat works as plan claims |
| `cfg.held_out_stamp_secret`, `gap_acceptable_threshold`, `held_out_gate_strict`, `acknowledge_cross_binary_version_drift`, `horizon_count`, `horizon_list` | ControllerConfig.hpp:483 / :465 / :474 / :516 / :737-738 — all confirmed | VERIFIED |
| `LABEL_REGISTRY_HASH()` definition | LabelFunctions.hpp:345 — confirmed | VERIFIED |
| `EnsembleModelZoo_Free` (used in B.2 unwind) | CoreModelZoo.hpp:986 — confirmed | VERIFIED |
| Test count baseline 1621/0 | Cannot run build; accepting operator's 2026-05-06 verification | ACCEPTED |
| `MODEL_FORMAT_VERSION` constant | ModelInference.hpp:115 (= 6) — confirmed | VERIFIED |
| `tt::BUILD_FLAGS_HASH()` | called at BacktestEngine.hpp:1168, BacktestPanels.hpp:2680 — confirmed reachable | VERIFIED |

---

## Hidden scope detected

### 1. ModelHandle missing `stamp_result` field — Phase B.2 validator won't compile as written (P1 — must fix)

**Plan code shape (lines 122-162):**
```cpp
const ModelStampResult &sr = role_arr[h].stamp_result;
if (!sr.has_grid_member_count) { ... }
```

**Reality:** `ModelHandle` (ModelInference.hpp:222-283) does NOT have a `stamp_result` field. It has selectively-flattened `stamp_inf_*` fields (`stamp_inf_confidence_threshold_scale`, `stamp_inf_freshness_tau`, etc.) — and notably does NOT include any `grid_member_count` / `grid_member_idx` / `has_grid_member_count` fields.

`CoreModelZoo_TryLoadRole` (CoreModelZoo.hpp:134-) calls `verify_model_stamp` and gets a `ModelStampResult sr`, then copies SELECT fields onto `ModelHandle` (e.g. ModelInference.hpp:223-247 copy `stamp_inf_*` from sr). It does NOT keep the full `sr` on the handle.

**Required additional work for Phase B.2:**
- Add 3 fields to `ModelHandle`: `uint8_t has_grid_member_count`, `int grid_member_count`, `int grid_member_idx`.
- Init in `Model_Init` (ModelInference.hpp:287).
- Copy from `sr` to `m` in `CoreModelZoo_TryLoadRole` post-verify (ML_Headers/CoreModelZoo.hpp:134-247 has the existing copy block; this fits the pattern).
- Update plan's B.2 validator code from `role_arr[h].stamp_result.has_grid_member_count` to `role_arr[h].has_grid_member_count` (etc.).

Without this fix, B.2 won't compile. Plan said B.2 was "~30 LOC validator." With this fix it's 30 LOC validator + ~30 LOC ModelHandle field plumbing across 4 sites (struct decl + Model_Init + TryLoadRole copy + maybe Model_Free + freshness audit). **Phase B realistic effort: 2-3h, not 1.5h.**

Alternative design: don't store on ModelHandle. Instead, re-parse stamp file in the validator via an extra `verify_model_stamp` call. Wasteful (re-opens file) but no struct changes. Plan should pick one.

### 2. Per-horizon emit assumption is wrong; multi-horizon trainer doesn't emit stamps at all — Phase B effort badly underestimated (P1 — must fix design)

**Plan's open question #1 (line 268):** "Audit assumes the trainer emits one stamp per horizon … Spot-check `Backtest_RunFullValidation` body for the horizon loop."

**Spot-check result:** `Backtest_RunFullValidation` (BacktestEngine.hpp:1019-1184) takes a SINGLE `int horizon` parameter (line 1022), runs `Backtest_RunWalkForward` once on it (line 1050), emits ONE stamp per call (line 1172). **There is no horizon loop inside RFV.** Same for the Train Model worker (BacktestPanels.hpp:2641-2710) — single `snap_horizon` is implicit in the single-shot training; one `stamp_write_for_model` call per worker run.

**Worse:** The actual multi-horizon trainer is `train_multi_horizon_worker_fn` (BacktestPanels.hpp:2817-3063), which IS a per-horizon loop (line 2871: `for (int h = 0; h < horizon_count; ++h)`). It saves per-horizon models to `models/<class>/<run>_horizon_<H>/<role>.json` (line 2994) — exactly the layout `EnsembleModelZoo_AutoDetectFromDir` scans. **But it does NOT call `stamp_write_for_model` at all.** It writes a tiny `summary.txt` (line 3017-3027) with run name, role, label_type, horizon, and 3 hyperparams — but no stamp file, no signature, no LABEL_REGISTRY_HASH, no FEATURE_REGISTRY_HASH.

**Implication:** The "ensemble auto-detect" path that B.2 wants to validate has stamps that don't exist. Multi-horizon ensembles deployed today are **stamp-less**. Adding `grid_member_count` to RFV/Train Model emit (which only ever produce 1-stamp single-horizon models) does NOT close finding #2's gap — those stamps are not the ones AutoDetect reads.

**To genuinely close finding #2, need EITHER:**
- (a) Wire `stamp_write_for_model` INTO `train_multi_horizon_worker_fn` per-iter (substantial — needs full inf struct build, scaler binding, held-out fields, etc.; matches RFV's ~80-LOC stamp emit block). Realistic: 3-5h work.
- (b) Document that multi-horizon ensemble stamps don't exist yet, and B.2's validator only fires when stamps happen to be present (legacy path). Closes the docstring gap (CoreModelZoo.hpp:1093-1114) but not the protection gap.
- (c) Defer Phase B's emit side and ship only B.2 (validator), with explicit caveat "consistency check fires only on legacy single-horizon stamps that happen to be in an ensemble dir." Effectively a no-op safety net.

**Plan's Phase B as written is incoherent** — it adds `grid_member_count` fields to single-horizon emit sites that have no horizon ensemble context. The trainer ALREADY knows it's not a multi-horizon run when running RFV; emitting `grid_member_count=cfg.horizon_count, grid_member_idx=h_idx_in_horizon_list` from a single-shot RFV call uses values that aren't defined (RFV doesn't iterate `cfg.horizon_list`).

**Recommend:** Restructure Phase B as either (a) — wire stamp emission into the multi-horizon worker (3-5h, large LOC; this is the right architectural fix); OR (c) — ship only the validator (small) + flag (a) for v5.10.X. **30m of restructuring before kickoff prevents 4-6h of confusion mid-implementation.**

### 3. CoreModelZoo.hpp does NOT include LabelFunctions.hpp — Phase A.3 won't compile as written (P1 — must fix)

**Plan A.3 code shape (lines 65-67):**
```cpp
sr = verify_model_stamp(found_path, secret, gap, MODEL_FORMAT_VERSION,
                        FEATURE_REGISTRY_HASH(), LABEL_REGISTRY_HASH());
```

**Reality:** `CoreModelZoo.hpp` includes (lines 36-47):
- `ModelInference.hpp` — provides `verify_model_stamp` + `FEATURE_REGISTRY_HASH` is defined in `FeatureRegistry.hpp` which is included at line 37
- `FeatureRegistry.hpp`, `BanditLearning.hpp`, `Strategies/StrategyInterface.hpp`, `Version.hpp`, system headers

Notably absent: `Backtest/LabelFunctions.hpp`. There is no transitive include chain reaching it (`ModelInference.hpp` only has a comment reference at line 1301). `LABEL_REGISTRY_HASH()` is undefined here.

**Required fix:** Add `#include "../Backtest/LabelFunctions.hpp"` to `CoreModelZoo.hpp` near line 47. This is a 1-line fix but the plan doesn't note it. (BacktestPanels.hpp:1289 is fine — already transitively reaches LabelFunctions through BacktestEngine.hpp:27.)

**Side note — layering concern:** CoreModelZoo.hpp is in `ML_Headers/`, and including from `Backtest/` reverses the architectural dependency direction (ML core → backtest). May be acceptable given the small 1-function dependency, but operator should consider whether to (a) include it, (b) move `LABEL_REGISTRY_HASH` somewhere lower (e.g. ML_Headers/LabelRegistry.hpp), or (c) forward-declare `inline uint64_t LABEL_REGISTRY_HASH();`. (a) is the path of least resistance.

### 4. Validator return value inconsistency — refuse-on-mismatch returns -1 instead of 0 (P2 — fix during)

**Plan B.2 code (line 152):**
```cpp
EnsembleModelZoo_Free(ezoo); // unwind partial load
return -1; // refuse
```

**Reality:** `EnsembleModelZoo_AutoDetectFromDir` is documented to return "total models loaded" (line 1103: "Returns total models loaded across all roles + horizons"). All existing failure paths return 0:
- Line 1166: `if (!dir) return 0;`
- Line 1194: `if (n_discovered == 0) return 0;`
- Line 1128: `if (!ezoo || !base_dir || base_dir[0] == '\0') return 0;`

Callers at EngineSharded.hpp:836 (`if (n_loaded > 0 && ml_ensemble_zoos[i].active)`) and BacktestSharded.hpp:300 (same check) gate on `n_loaded > 0`. A return value of `-1` would technically pass `n_loaded > 0 == false` (negative is not greater than zero), but it's inconsistent with the function's contract.

**Fix:** Change `return -1;` to `return 0;` on REFUSE path. Cosmetic, but contract-clarity matters.

### 5. Phase A round-trip test uses production helpers that don't extract cleanly (P2 — design choice during)

**Plan A.4 verification text (lines 75-81):**
> 1. Construct StampInferenceCfgInputs as RFV would (NOT synthetic — call the production helper if extractable)

**Reality:** RFV's `inf` build (BacktestEngine.hpp:1104-1168) is ~65 lines of inline code — it's NOT extracted into a helper, it's open-coded inside the body of `Backtest_RunFullValidation`. Same for the Train Model worker (BacktestPanels.hpp:2641-2686 — also open-coded). To "call the production helper," operator has to first extract one, which expands Phase A scope beyond "additive only."

**Fix:** Either (a) accept that the round-trip test will partially mirror RFV's `inf` build (reasonable since the test's job is to verify the LABEL_REGISTRY_HASH 2-line block specifically — not all 25 fields); or (b) extract a `Stamp_BuildInferenceCfgInputs(const ControllerConfig<F> &cfg, int label_type, ...)` helper as a Phase A.0 pre-step. (a) is simpler.

### 6. Plan claims test count 1626/0 final, but Phase B's "+3 tests" number doesn't match the description (P3 — cosmetic)

**Plan tag B (line 28):** `+3 new tests = 1624/0 cumulative`
**Verification described in plan (lines 165-167):** 3 verification scenarios for B (round-trip, mismatch negative, back-compat). OK.

But Phase A claims `+1 new round-trip test = 1622/0` (line 87) and the round-trip text covers BOTH "matching hash" and "perturbed/wrong expected" cases — that's 2 sub-checks bundled into one `check()` macro pair, or 1 `check()` with assertions. The numbering math (1+3+1 = 5 added → 1626) works if each phase's test count maps 1:1 to a single `check()`-style entry. Test additions in `tests/controller_test.cpp` typically use multiple `check()` calls per scenario (the existing v5.10.0d block at :13338-13360 uses 6 `check()` calls for 3 "scenarios"). Plan's count is approximate; not blocking but operator should expect ±3-5 actual added `check()` lines vs. round number.

---

## Cold-pickup context completeness (10 items, independent re-walk)

Plan self-audits 10/10 GREEN at lines 290-300. Independent re-walk:

| # | Field | Self-audit | Re-walk verdict |
|---|---|---|---|
| 1 | Branch state named specifically | "experiment/per-core-sharding (default branch; Sprint B sub-ship cadence)" | PASS — explicit, consistent with v5.10.0a-e cadence visible in `git log`. |
| 2 | Phase order matches dependency | A → B → C (independent) | PASS — phases are independent (no shared file targets except possibly Phase A and Phase B both touching CoreModelZoo.hpp:134, but A.3 only adds the 6th arg while B is a separate validator add). |
| 3 | Each phase Step 0 concrete | Yes | PASS — Phase A has concrete file:line + 2-line code shape; Phase B has explicit "spot-check at write time" with the question that should be resolved (and Hidden Scope #2 above identifies the actual answer); Phase C has explicit code shape. |
| 4 | Function/macro names | All cited | PASS-with-1-NIT — `LABEL_REGISTRY_HASH()`, `verify_model_stamp(...)`, etc. all exist. NIT: B.2 uses `role_arr[h].stamp_result.*` which doesn't compile (Hidden Scope #1). |
| 5 | File:line refs verified | 14 of 15 spot-checked | PASS — 14 verified by me independently + 1 ACCEPTED (replay test, accepting operator's claim). |
| 6 | Stale-claim audit | Dedicated section | PASS — present, accurate, comprehensive. |
| 7 | Effort vs LOC reconciled | ~140 LOC for ~3h | PASS-with-FLAG — A and C reconcile fine. **B underestimates by ~50-80 LOC** + 2-3h additional time due to Hidden Scope #1 + #2. |
| 8 | Source-audit refs with paths | parity-2026-05-06-full.md cited | PASS — paths spelled. |
| 9 | Predecessor / dependent named with paths | v5.10.0e + 7f0b9a9; v5.10.2/.3/.v5.11.0 forward | PASS — all paths spelled. |
| 10 | Tag names locked + rollback anchor | pre-v5.10.1 + v5.10.1.A/B/C + v5.10.1 final | PASS — push command at lines 224-233 explicit. |

**Cold-pickup verdict: 9.5/10 PASS.** Plan reads like cold-pickup-ready. The 0.5 deduction is for Hidden Scope #2 — the open question on per-horizon emit was flagged by the plan but the wrong answer was assumed. A fresh session would discover this at Phase B kickoff (correctly per the plan's own instructions to "spot-check at write time"); the plan would then need redesign mid-implementation. Better to resolve now.

---

## Drift audit (8 categories)

| Category | Status | Detail |
|---|---|---|
| 1. Boundary-stable refactor (memory file: feedback_reduce_touch_sites.md) | NO RISK (with caveat) | Phase A is purely additive (2 lines per emit site, 1 arg per consume site). Phase C is purely additive (4 args at 2 sites). **Phase B as written would breach this rule:** the validator wants to access stamp result data on ModelHandle, which requires either (a) ModelHandle field additions (cascade across struct decl + init + load + free + 4 ezoo arrays), OR (b) re-parse stamp file in validator (wasteful but boundary-stable). Recommend approach (b) for v5.10.1 → defer Surface integration to v5.10.X if operator wants it. |
| 2. Hot-path purity | NO RISK | Zero modifications to hot-path symbols. All edits in stamp emit/consume sites + slow-path orchestration. |
| 3. NaN-free feature pack (CLAUDE.md decision 14) | NO RISK | Plan doesn't touch feature compute or `Features_PackAll`. |
| 4. Train-serve parity | PASS | Plan adds plumb-throughs across BOTH train (RFV emit + Train Model worker emit) AND serve (live load via CoreModelZoo + Verify Stamp UI consume) sides. Phase B intent is correct (close per-horizon parity loop) but implementation needs Hidden Scope #2 redesign. |
| 5. Display ↔ execution invariant (CLAUDE.md 12) | NO RISK | No new hot-path predicate terms. |
| 6. Easy-additions invariant (CLAUDE.md 13) | NO RISK | No FOREACH_* registry category triggered. LABEL_REGISTRY_HASH/FEATURE_REGISTRY_HASH already use FOREACH_TARGET/FOREACH_FEATURE registries — plan plumbs them through, doesn't add new instances. |
| 7. Snapshot field forward-compat | NO RISK | Plan adds stamp body fields that already exist (verifier supports them; emitter supports them). No new schema versions; back-compat preserved by `if (expected_*_hash != 0)` and `if (has_*_count)` guards. |
| 8. Build-flag drift / `BUILD_FLAGS_HASH` | NO RISK | Plan doesn't change build flags or `BUILD_FLAGS_HASH`. |

---

## Hardening checks

| Check | Status | Notes |
|---|---|---|
| Atomic file writes | N/A | Plan doesn't write any new files; existing `stamp_write_for_model` already does atomic-rename. |
| Locale pinning (LC_ALL=C) | N/A | No locale-sensitive parsing introduced; existing `strtoull` (hex) and `atoi` paths unchanged. |
| GUI render-thread blocking I/O | N/A | No GUI changes; Verify Stamp button (BacktestPanels.hpp:1289) already runs on UI thread but only opens a single file (existing code). |
| Failure telemetry visibility | PASS | All new error paths use `fprintf(stderr, ...)` matching existing engine pattern. |
| Resource cleanup | PASS-with-NIT | Phase B.2 calls `EnsembleModelZoo_Free(ezoo)` on REFUSE; verified function exists. NIT: return value should be 0 (not -1) per Hidden Scope #4. |
| Boot-time fatal-vs-warn split | PASS | Phase A: `verify_model_stamp` already has the strict/warn split via `held_out_gate_strict`; LABEL_REGISTRY_HASH plumbing inherits it. Phase B: plan states REFUSE on mismatch + WARN on legacy back-compat, matching existing pattern. Phase C: plumbs `held_out_gate_strict` through; default 0 (warn-only) preserves pre-fix behavior. |
| Header reachability | YELLOW | Phase A.3 needs `LabelFunctions.hpp` include in `CoreModelZoo.hpp` (Hidden Scope #3). 1-line fix. |
| Round-trip test extracts production helper | YELLOW | Plan A.4 says "call the production helper if extractable" — actual code is open-coded inside RFV body. Acceptable to mirror inline (Hidden Scope #5). |
| ModelHandle struct extension | YELLOW | Phase B.2 references field that doesn't exist (Hidden Scope #1); needs design decision (add ModelHandle fields vs. re-parse) before kickoff. |
| Validator covers all 4 ensemble roles | YELLOW | Plan B.2 code uses `role==0..3` mapping but writes `(role==2)?...:ezoo->exit;` — actual field name is `exit_predictor` (CoreModelZoo.hpp:614). Plus count fields are role-specific (`barrier_count`, `regime_count`, `exit_predictor_count`, `buy_signal_count`) — plan's `int count = ...; // role-specific count` is an unfinished placeholder. |

---

## Recommendations

### Must fix before coding (P1)

1. **Phase B redesign — choose a path before kickoff.** The current plan emits `grid_member_count` from single-shot trainers (RFV, Train Model worker) where there's no ensemble context. Three options, each clear-cut:
   - **(Recommended for v5.10.1) Option C — ship validator only.** Implement B.2 (consistency check) only; explicitly note the multi-horizon trainer doesn't emit stamps yet, so the check fires only on legacy single-horizon stamps that happen to be in an ensemble dir. Closes the docstring gap (CoreModelZoo.hpp:1093-1114) and the verifier-side parity loop (every parsed `grid_member_count` is now compared cross-handle). Defer the multi-horizon trainer stamp emission to v5.10.X. Effort: ~1.5h matches the original Phase B estimate (since the validator IS the work).
   - **Option A — wire stamp_write_for_model into train_multi_horizon_worker_fn.** Mirrors RFV's ~80-line stamp emit block, with `grid_member_count = horizon_count, grid_member_idx = h`. Plus B.2 validator. Realistic effort: 3-5h. This is the fully-correct architectural fix.
   - **Option B — accept that Phase B's emit side is dead-on-arrival** until the multi-horizon trainer learns to emit stamps; ship the validator as the documentation of "what AutoDetect would check IF stamps existed."
   Pick one before opening Phase B. Operator can decide; I'd default to **Option C** for v5.10.1 (close audit's dead-protection finding via consume-side, defer emit-side to a v5.10.X follow-up). Update the plan's open-question #1 with the resolution.

2. **Phase B.2 — fix ModelHandle.stamp_result reference.** Pick one:
   - (Recommended) Re-parse stamp file inside the validator. Loop over each loaded handle, derive stamp path from `m->model_path`, call `verify_model_stamp(...)` again to re-extract `grid_member_count`. Wasteful (double-parse) but boundary-stable per CLAUDE.local.md "prefer boundary-stable refactors."
   - Add 3 new fields to `ModelHandle` struct (`has_grid_member_count`, `grid_member_count`, `grid_member_idx`); init in `Model_Init`; copy from `sr` in `CoreModelZoo_TryLoadRole`. Cleaner long-term but breaches boundary-stable rule for marginal gain.
   Plan currently picks neither.

3. **Phase A.3 — add LabelFunctions include to CoreModelZoo.hpp.** 1-line: `#include "../Backtest/LabelFunctions.hpp"` near line 47 of CoreModelZoo.hpp. Without this, `LABEL_REGISTRY_HASH()` is unknown at the verify_model_stamp call site. (Note: this reverses architectural layering ML_Headers → Backtest; consider moving the macro to ML_Headers/LabelRegistry.hpp in v5.10.X if layering matters.)

### Worth fixing during coding (P2)

4. **Phase B.2 validator — fix exit field name + count fields.** Plan's code shape uses `ezoo->exit` (actual: `exit_predictor`, CoreModelZoo.hpp:614) and `int count = ...; // role-specific count` placeholder. Concrete:
   ```cpp
   ModelHandle<F> *role_arr;
   int count;
   switch (role) {
     case 0: role_arr = ezoo->buy_signal;     count = ezoo->buy_signal_count;     break;
     case 1: role_arr = ezoo->barrier;        count = ezoo->barrier_count;        break;
     case 2: role_arr = ezoo->regime;         count = ezoo->regime_count;         break;
     case 3: role_arr = ezoo->exit_predictor; count = ezoo->exit_predictor_count; break;
   }
   ```

5. **Phase B.2 — use return 0 (not -1) on REFUSE.** Matches existing function contract. Cosmetic but contract-honoring.

6. **Phase A.4 round-trip test — accept that production `inf` build is open-coded.** Drop the "call the production helper if extractable" aspirational language in the verification spec. Just write the round-trip test with a faithful subset of RFV's `inf` build (or extract a helper as Phase A.0, but that's its own ship — not v5.10.1's scope).

### Acceptable risk (don't block)

7. **Phase A and C are clean.** Phase A's 4-site plumb-through is exactly the kind of additive change that reads + reviews well; matches v5.9.5b's Backtest_RunFullValidation closure shape. Phase C's args plumb-through is canonical. Both ship as-described.

8. **Test count approximations.** Plan's "+1, +3, +1 = 1626" math is a rough estimate; actual may be ±3-5 `check()` calls. Don't block.

9. **Replay-determinism gate.** Phase B's "ensemble loads now perform additional comparison logic; backtest replay must still bytewise-pass v5.9.2 replay-determinism test" is well-flagged. Add explicit gate in the sub-ship test plan.

10. **Section L formalization deferred.** Plan's open question #3 (formalize stamp body field addition checklist) is correctly deferred to v5.10.X doc-only ship. Acceptable.

---

## Verdict: YELLOW

**One-line summary:** Plan structure is exceptionally well-prepared (15/15 file:line refs verified, 9.5/10 cold-pickup, hot path UNTOUCHED, parity-aware emit+consume coverage); but Phase B's design is incoherent on close inspection — the per-horizon emit assumption is wrong AND the multi-horizon trainer doesn't emit stamps at all, with two compile-blocking gaps (ModelHandle missing stamp_result; CoreModelZoo missing LabelFunctions include). 30-60m of design resolution before kickoff prevents 4-6h of mid-implementation rework.

**5-bullet executive summary:**
- Phases A and C are clean and ship-ready: 4-site plumb-through (LABEL_REGISTRY_HASH) and 2-site args plumb-through (AutoDetect strict/gap/secret/drift). Both additive, parity-correct, ~30 LOC each. Same shape as v5.9.5b's closure.
- All 15+ cited file:line references independently verified vs HEAD `7f0b9a9`. Hot path UNTOUCHED — zero edits to BG_Evaluate / SG_Evaluate / ExecutionCore_Tick.
- **Genuine design gap #1 (Phase B):** Plan assumes RFV / Train Model emit stamps per-horizon; spot-check confirms they emit ONE stamp per call (no horizon loop). Worse, the actual multi-horizon trainer (`train_multi_horizon_worker_fn`) doesn't call `stamp_write_for_model` at all — multi-horizon ensemble dirs have unstamped models. Adding `grid_member_count = cfg.horizon_count` to single-shot RFV emits values that aren't defined (RFV doesn't iterate horizons). Recommend Option C: ship validator only, defer multi-horizon stamp emit to v5.10.X.
- **Genuine compile-blocking gaps:** (a) Phase B.2 validator code references `role_arr[h].stamp_result.has_grid_member_count` — `ModelHandle` has no `stamp_result` field, only selectively-flattened `stamp_inf_*` fields, and notably no `grid_member_count` field. (b) Phase A.3 adds `LABEL_REGISTRY_HASH()` to `CoreModelZoo.hpp:134` but `CoreModelZoo.hpp` doesn't include `LabelFunctions.hpp`. (c) Phase B.2's switch uses `ezoo->exit` (actual: `exit_predictor`) and a placeholder `int count = ...; // role-specific count`.
- Phase A.1, A.2, A.3 (after include fix), A.4, C.1, C.2 all green — purely additive, correct shapes, parity-symmetric. Plan's stale-claim audit is rigorous (15 refs spot-checked); cold-pickup completeness 9.5/10. Verdict YELLOW (not RED) because Phase A + C alone close 2 of 3 audit findings, and Phase B has clear path to closure with redesign.

**Top recommendation (single sentence):** Resolve Phase B's design by picking Option C (ship the consistency validator only, defer multi-horizon stamp emission to v5.10.X) and add the missing `LabelFunctions.hpp` include to `CoreModelZoo.hpp` for Phase A.3 — both fixes are explicit code-level decisions that take 30-60m to lock in, after which Phases A + C ship as-written and B becomes a straightforward validator implementation.
