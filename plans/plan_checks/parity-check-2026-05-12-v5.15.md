# /parity-check audit — v5.15 sprint plan

**Date:** 2026-05-12
**Audit scope:** Pre-coding gate for v5.15 sprint umbrella (.0 .1 .2 .3 .4)
**Audit verdict:** **YELLOW** — proceed with mandatory plan amendments before .0 / .3 coding starts. Several stale claims + one factual root-cause error (v5.15.3) + one design flaw (v5.15.4 snapshot/revert) require correction; HMAC chain logic + Surface G forward-compat are sound; trading_mode stamp-binding row design is correct.

**Plan files audited:**
1. `plans/v5.15-live-readiness/MASTER.md`
2. `plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.0-modelhandle-migration.md` (HIGH-RISK)
3. `plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.2-live-readiness-boot-gate.md` (introduces stamp-bound `trading_mode`)
4. `plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.3-multi-horizon-worker-stamping.md`
5. `plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.4-live-mode-strict-defaults.md`

Light review only: v5.15.1.

**Baseline:** post-v5.14.11.C (commit c4e45d1) + v5.14.post1 (commit 1752fde). 2904 tests passing per handoff.

---

## Per-surface matrix

| Parity surface | Status | Rationale |
|---|---|---|
| **1. Stamp body byte preservation (v5.15.0)** | **PASS** | Plan keeps PRE_CFG/POST_CFG halves unchanged; STAMP_HAS_FLAGS_BIT mapping preserved; pure caller-site rewrites of `h.has_X` → `HANDLE_HAS(h, X)`. Wire emit path untouched. |
| **2. Stamp body byte preservation (v5.15.2 trading_mode)** | **PASS** | New row APPENDED at end of FOREACH_STAMP_BOUND_CFG (after thompson_precision_obs at line 169). Legacy stamps lack the row → emit walk skips → byte-identical to v5.14.post1. New emits add 1 line at end → intentional differ. Surface G `has_trading_mode` flag preserves forward-compat. |
| **3. Surface G has_* forward-compat** | **PASS** | v5.15.0 (ModelHandle) preserves uint64_t has_flags; legacy stamps parse field by field, missing fields stay zero-init. v5.15.2 (trading_mode) uses BITMAP_BIT emit_source with `has_trading_mode` flag — Surface G compliant. v5.14-era stamps will load cleanly. No MODEL_FORMAT_VERSION bump. |
| **4. HMAC chain integrity** | **PASS** (with one caveat) | trading_mode appended at registry END → legacy stamps emit identical canonical body → HMAC identical to v5.14.post1 baseline. New trading_mode stamps generate intentionally-new HMACs. v5.15.0 ModelHandle migration is INTERNAL (struct layout change); HMAC operates on canonical body bytes, not C struct memory; preserved. **Caveat:** plan v5.15.0 .C Test 1's SHA-256 baseline freeze requires the SHA computed pre-migration to capture v5.14.post1 emit, then verified post-migration (operator must execute this manually; plan correctly notes the rollback-anchor capture step). |
| **5. Cross-mode byte-equivalence (v5.15.3 serial vs parallel)** | **FAIL** (root cause misdiagnosed) | Plan claims "multi-horizon worker writes models but never calls stamp_write_for_model" — INCORRECT. `mh_run_one_horizon_fv` (BacktestPanels.hpp:3633) ALREADY calls `Backtest_RunFullValidation` which auto-stamps via the RFV path (which uses STAMP_CFG_AUTOPOPULATE). The actual root cause of "4/4 handles missing grid_member_count" is that nobody populates `inf.grid_member_count` ANYWHERE in BacktestEngine.hpp or BacktestPanels.hpp. See HIGH.2 below. Cross-mode byte-equivalence test (.D Test 4) IS valuable post-fix. |
| **6. cfg-default normalize preserves byte-equivalence (v5.15.4)** | **PASS** with documentation error | The normalize pass flips `model_verify_strict` + `reconcile_mode`. NEITHER is stamp-bound (verified: no entries in FOREACH_STAMP_BOUND_CFG). So stamp body is byte-identical for ALL legacy cfgs regardless of trading_mode flip. Plan v5.15.4 line 199-205 claims "stamp body emit reads normalized value... legacy cfg WITHOUT explicit override produces DIFFERENT stamp under live mode" — FALSE for these two fields. Only the NEW trading_mode field will change emit (covered by surface 2). See MEDIUM.1. |
| **7. NaN-free feature pack chokepoint (CLAUDE.md item 9)** | **PASS** | v5.15 doesn't touch FeatureRegistry, FeatureComputeCtx, Features_PackAll. No new feature validation sites. Chokepoint discipline preserved. |
| **8. train↔serve identity across production callers** | **DRIFT-RISK** | Asymmetry: `Backtest_RunFullValidation` (BacktestEngine.hpp:1262) uses `STAMP_CFG_AUTOPOPULATE(inf, cfg)` — populates ridge_*/composite/winsor/exit_blender/risk_*/ml_buy_threshold/gap_acceptable_threshold/bandit fields. `train_model_worker_fn` (BacktestPanels.hpp:3206) does NOT call STAMP_CFG_AUTOPOPULATE — only manually sets a subset. These two production callers produce DIFFERENT stamp body field sets today. v5.15 doesn't surface this; v5.15.3 helper proposes STAMP_CFG_AUTOPOPULATE which would (good!) close the gap but the plan's "mirror canonical train_model_worker_fn (post-v5.14.post1)" framing is contradictory. See HIGH.1. |
| **9. STAMP_MODEL_CONST_AUTOPOPULATE call-site liveness** | **DRIFT-RISK** | The macro is DEFINED at StampBoundModelConstRegistry.hpp:601 but called ZERO times in production code (grep across CoreFrameworks/Backtest/ML_Headers/tests = 0 hits). The macro's `get_value` expressions reference `inf->X` (e.g., `(unsigned long)inf->training_timestamp_us`), which when expanded by `(inf).name = (type)(get_value)` produces `inf.training_timestamp_us = (uint64_t)(inf->training_timestamp_us)` — a self-referential assignment if `inf` is a struct value (not pointer). The macro as written needs `inf` to be a POINTER OR needs the registry's get_value expressions to reference a separate `meta` source. v5.15.3 helper line 172 calls `STAMP_MODEL_CONST_AUTOPOPULATE(inf, cfg_used, tt::WallClock_Now_us())` but this won't produce useful field copies under the current macro definition. See HIGH.3. |
| **10. Per-horizon grid_member_count / horizon_idx / horizon_count fields** | **FAIL** (factual error in plan) | v5.15.3 plan line 174 claims "these specific entries are in FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG" and that "grid_member_count, horizon_idx, horizon_count" are all 3 in the registry. ACTUAL state (verified at StampBoundModelConstRegistry.hpp:337-341): registry has TWO fields — `grid_member_count` + `grid_member_idx` — both in PRE_CFG (not POST_CFG), both share `inf->has_grid_member_count` flag (single `grid_member` group bit). NEITHER `horizon_idx` NOR `horizon_count` exists in the registry. MASTER line 213 claims "all 3 fields already in FOREACH_STAMP_BOUND_MODEL_CONST (verified during v5.14.8.E)" — FALSE. See HIGH.2. |
| **11. HotSwap snapshot/revert design (v5.15.4)** | **FAIL** (design flaw) | `EnsembleModelZoo_Free(swap_ezoo)` (EnsembleHotSwap.hpp:76) destroys pre-swap state IN-PLACE. Same with `CoreModelZoo_Free(swap_zoo); CoreModelZoo_Init(swap_zoo)` (EngineSharded.hpp:2923-2924). Plan v5.15.4.B captures `snap.prev_ezoo = state.cores[core_idx].ensemble_handle` BEFORE the swap — but `swap_ezoo` IS that same pointer; Free happens via the captured pointer. Capturing a pointer alone DOES NOT preserve the data it points to. Revert path "restore the pre-swap pointer" doesn't work because the pointed-to data is already gone. See HIGH.4. |
| **12. trading_mode enum semantics (paper/live/shadow)** | **PASS** with light | Enum dispatch + 3-value parse pattern mirror reconcile_mode at ControllerConfig.hpp:2371-2381 (verified). Plan correctly cohort-audits trading_mode against reconcile_mode + model_verify_strict — direct uint8/int storage is consistent with siblings. |

---

## HIGH findings (parity-breaking; must-amend before coding)

### HIGH.1 — train_model_worker_fn vs Backtest_RunFullValidation: ASYMMETRIC stamp body field set; plan v5.15.3 framing contradictory

**Class:** Class 18 mirror at production-caller level (CLAUDE.md item 19).

**Site:**
- `Backtest/BacktestEngine.hpp:1262` — RFV calls `STAMP_CFG_AUTOPOPULATE(inf, cfg)` AFTER manual population of inference_cfg/training_poll_interval/model_num_outputs/xgb_hyperparams/label_registry_hash/build_flags_hash/xgb_train_nthread/label_params. RFV's stamp carries the entire FOREACH_STAMP_BOUND_CFG cohort (ridge_*/composite/winsor/exit_blender/risk_*/ml_buy_threshold/gap_acceptable_threshold/bandit_*).
- `Backtest/BacktestPanels.hpp:3206-3289` — train_model_worker_fn manually populates the SAME `inf` fields as RFV's manual block, then calls `stamp_write_for_model` WITHOUT calling STAMP_CFG_AUTOPOPULATE. So Train Model stamps lack: 4 ridge_* + 5 composite_* + 2 winsor_* + 1 exit_blender_mode + 4 risk_* + 2 expected_thresholds + 4 bandit_* fields = 22 fields.

**Symptom (today):** Models trained via Train Model panel have stamps that lack cfg-binding drift detection for ridge/composite/winsor/exit_blender/risk/expected_thresholds/bandit cohorts. Engine boot WARN/REFUSE comparison passes silently because `has_X` flags are zero (= legacy treatment). Operator who configures ridge_lambda=0.5 in train cfg + 0.7 in serve cfg won't get a stamp_drift WARN if the model came from Train Model worker — only RFV-trained models surface the drift.

**Plan v5.15.3's contradictory framing:** The new helper `stamp_emit_for_horizon` at line 169 says `STAMP_CFG_AUTOPOPULATE(inf, cfg_used)`. This WOULD close the asymmetry for multi-horizon worker. BUT the plan describes the helper as mirroring "canonical reference at train_model_worker_fn (post-v5.14.post1)" — which DOESN'T use AUTOPOPULATE. So the plan is either:
- (a) Implementing AUTOPOPULATE for multi-horizon → CORRECT structurally but contradicts "mirror train_model_worker_fn" claim;
- (b) Faithfully mirroring train_model_worker_fn → would NOT use AUTOPOPULATE, contradicts plan's explicit AUTOPOPULATE call at line 169.

**Cross-ref to existing protections:** PARITY-002/003/004/005/008 closed the AUTOPOPULATE production-caller class for RFV. v5.14.post1 fixed train_model_worker_fn's field-name migration BUT did NOT add the AUTOPOPULATE call. This is a v5.14.post1 KNOWN GAP that should have been a follow-up TECH_DEBT entry.

**Recommended fix:**
1. v5.15.3.A amend: helper `stamp_emit_for_horizon` uses STAMP_CFG_AUTOPOPULATE (matches RFV's canonical path).
2. Additionally bundle into v5.15.3: add `STAMP_CFG_AUTOPOPULATE(inf, cfg_used)` to train_model_worker_fn at BacktestPanels.hpp:3265 (right after the manual ridge/composite/winsor population would have gone — but since it's not there today, it's a PURE ADDITION). This makes all 3 production callers symmetric.
3. Document the train_model_worker_fn closure in CHANGELOG as a parity gap-close (effectively closing the AUTOPOPULATE-coverage class for the third production caller).

**Effort:** +30 min on top of v5.15.3.A scope; closes an existing CRITICAL silent train↔serve identity gap.

**PARITY-NNN allocation:** PARITY-020 (new).

---

### HIGH.2 — v5.15.3 root cause MISDIAGNOSED: multi-horizon DOES stamp via RFV; gap is that `grid_member_count` field is never populated by any production caller

**Class:** Plan-level factual error; affects entire v5.15.3 ship structure.

**Sites verified:**
- `Backtest/BacktestPanels.hpp:3633` — `mh_run_one_horizon_fv` calls `Backtest_RunFullValidation` which auto-stamps when `auto_stamp_path[0] != '\0'` (set unconditionally at :3525). So multi-horizon DOES emit per-horizon stamps; the model file at `<dir>/<role>.json` already gets a `.stamp.json` companion.
- `mh_per_horizon_parallel_worker` (BacktestPanels.hpp:3763) also delegates to `mh_run_one_horizon_fv` → also stamps via RFV.
- Registry verification at StampBoundModelConstRegistry.hpp:337-341: `grid_member_count` + `grid_member_idx` exist as 2 entries in PRE_CFG (NOT POST_CFG as plan claims). Both gated by single `inf->has_grid_member_count` flag (group `grid_member`).
- Grep for `grid_member_count` or `grid_member_idx` populators in Backtest/BacktestPanels.hpp and Backtest/BacktestEngine.hpp = 0 hits. **Nobody populates these fields anywhere.** The registry entries exist but are orphaned wire-format placeholders.
- `horizon_idx` and `horizon_count` do NOT exist anywhere in the registry. Plan's MASTER line 213 "all 3 fields already in FOREACH_STAMP_BOUND_MODEL_CONST (verified during v5.14.8.E)" — FALSE.

**Symptom:** "4/4 handles missing grid_member_count" boot warning fires because `verify_model_stamp` parses the stamp body, finds no `grid_member_count=...` line, leaves `has_grid_member_count=0`. The boot check that surfaces this warning sees the missing flag and logs the warning. The model files ARE stamped — the stamps just lack this specific field.

**Real fix path:**
1. Acknowledge the actual root cause: RFV's stamp emit doesn't populate grid_member_count because nobody passes the grid identity into RFV. The 2 registry fields are orphan placeholders.
2. Wire grid identity into RFV via `FullValidationResults` fields (e.g., `req_grid_member_count`, `req_grid_member_idx`) — same pattern as v5.11.41's `req_label_lookahead_ticks` plumbing through `out->req_*` (BacktestEngine.hpp:1235-1239).
3. `mh_run_one_horizon_fv` populates `fv->req_grid_member_count = horizon_count;` and `fv->req_grid_member_idx = h;` BEFORE calling RFV.
4. RFV's emit block (BacktestEngine.hpp:~1230) reads `out->req_grid_member_count` and sets `inf.grid_member_count = out->req_grid_member_count; inf.grid_member_idx = out->req_grid_member_idx; STAMP_SET(inf, grid_member);`.
5. Single-horizon callers (train_model_worker_fn, RFV directly) leave `req_grid_member_count = 0` (or = 1 for single-horizon = "grid of 1") → group bit stays unset OR group bit set with grid_member_count=1 / grid_member_idx=0 (operator can grep-distinguish from multi-horizon stamps).

**The plan's `stamp_emit_for_horizon` helper is REDUNDANT and INCORRECT:** Adding it creates a SECOND stamp emit path that conflicts with RFV's stamp emit path. Two stamps could end up written to the same file (or stomp each other), or the helper's version differs in field set from RFV's. The structural-fix-preferred rule (CLAUDE.md item 19) says wire the missing field into the EXISTING RFV emit path — don't add a parallel path.

**MASTER + subplan amendments required:**
- Reframe v5.15.3 root cause description (boot log claims "missing grid_member_count" = field not populated, NOT stamp-file missing).
- Drop `stamp_emit_for_horizon` helper (it duplicates RFV's emit path; structural fix preferred).
- Add `req_grid_member_count` + `req_grid_member_idx` fields to FullValidationResults.
- RFV emit block: 4 LOC added to populate from `out->req_*`.
- mh_run_one_horizon_fv: 2 LOC added to set `fv->req_*` from horizon context.
- Tests: per-horizon stamps now carry grid_member_count + grid_member_idx; boot log no longer warns.

**Effort:** REDUCES from ~150 LOC to ~30 LOC. v5.15.3.A scope shrinks. v5.15.3.C (parallel-mode stamping) becomes trivial because mh_per_horizon_parallel_worker also goes through mh_run_one_horizon_fv → already inherits the fix.

**Cross-mode byte-equivalence (.D Test 4) is still valuable** — verify serial vs parallel mode produce identical per-horizon stamps (same cfg snap → same RFV emit → same grid populator).

**Effort saved by correct framing:** ~3 hours.

**PARITY-NNN allocation:** PARITY-021 (new).

---

### HIGH.3 — STAMP_MODEL_CONST_AUTOPOPULATE macro is a non-functioning stub (defined but unused; expansion would self-assign)

**Class:** Macro definition error; not yet a parity bug because nobody calls it, but v5.15.3 plan proposes to use it.

**Site:** `ML_Headers/StampBoundModelConstRegistry.hpp:601-607`. Macro signature: `STAMP_MODEL_CONST_AUTOPOPULATE(inf, meta, now_us)`. Expansion at :680-688 does `(inf).name = (type)(get_value)`. The `get_value` column in the registry references `inf->X` (e.g., `inf->confidence_threshold_scale`, `(unsigned long)inf->training_timestamp_us` at lines 270, 401-402).

**Symptom (today):** Zero call sites in production code (grep confirmed: 0 hits in CoreFrameworks/Backtest/ML_Headers/tests/). The macro IS expanded inside the struct field declarations — but that's separate (uses different inner X-macro). For runtime population, calling `STAMP_MODEL_CONST_AUTOPOPULATE(inf, meta, now_us)` would expand to `(inf).training_timestamp_us = (uint64_t)((unsigned long)inf->training_timestamp_us)` — which is a self-referential assignment that does nothing useful when `inf` is a struct (or copies the field to itself when `inf` is a pointer dereference).

**Plan v5.15.3 line 172** calls `STAMP_MODEL_CONST_AUTOPOPULATE(inf, cfg_used, tt::WallClock_Now_us())` expecting it to populate fields from `cfg_used` + `now_us` — but the macro's get_value expressions reference `inf->X`, not `cfg.X` or `meta.X`. The macro is **definitionally inert** when called.

**Real fix path (orthogonal to v5.15 but uncovered by this audit):**
- Option A — make the macro functional by adding a separate META source struct. Registry get_value column changes from `inf->X` to something like `META_X(meta, now_us)`. This requires defining META_* macros per-entry. Substantial work; not in v5.15 scope.
- Option B — drop STAMP_MODEL_CONST_AUTOPOPULATE from v5.15 scope; production callers continue manual population of architectural fields (today's pattern). When the macro gets fixed later (separate sprint), production callers migrate to the single call.
- **Option C (RECOMMENDED for v5.15)** — v5.15.3 helper does NOT call STAMP_MODEL_CONST_AUTOPOPULATE; manually populates the few architectural fields needed (e.g., training_timestamp_us, run_name, scaler binding) following RFV's pattern at BacktestEngine.hpp manual block. Cleaner alternative aligned with HIGH.2's revised approach (wire into RFV, drop helper).

**v5.15.3 implications:** Plan must NOT rely on STAMP_MODEL_CONST_AUTOPOPULATE. If keeping any version of the helper, manually populate the required fields. Better: drop the helper entirely per HIGH.2's revised approach.

**Cross-ref:** This finding overlaps with TECH_DEBT-006 ("FOREACH_STAMP_BOUND_MODEL_CONST refactor"). TECH_DEBT-006 mentions the AUTOPOPULATE companion needs source-of-truth resolution. Today's macro definition is a placeholder that v5.14.8.0 set up but didn't complete the wiring for.

**PARITY-NNN allocation:** PARITY-022 (new). Severity = MEDIUM (no production caller today; would become HIGH if v5.15.3 plan proceeds as written).

---

### HIGH.4 — v5.15.4 HotSwapSnapshot/Revert design DOES NOT preserve pre-swap data

**Class:** Design-level error; would not catch in pure code review without runtime simulation.

**Sites:**
- `CoreFrameworks/EnsembleHotSwap.hpp:75-76`: `EnsembleModelZoo_Free(swap_ezoo)` destroys pre-swap state in-place. The `swap_ezoo` parameter IS `state.cores[core_idx].ensemble_handle` (caller at EngineSharded.hpp:2855-2861 passes the pointer cast from state).
- `CoreFrameworks/EngineSharded.hpp:2923-2924`: single-zoo branch does `CoreModelZoo_Free(swap_zoo); CoreModelZoo_Init(swap_zoo);` — destroys + reinits in-place.

**Plan v5.15.4.B claim (line 240-254):** "HotSwap_CaptureSnapshot captures pre-swap state. Cheap — pointer copy + counter copy. No data deep-copy needed because the next operation will Free these AFTER successful swap, OR restore them on failure (in which case the original allocations are still valid)."

**Why this fails:** The "next operation" (EngineSharded_HotSwapEnsemble or the inline Free+Init+Load in single-zoo branch) DESTROYS the pointed-to data BEFORE returning. By the time the caller observes the rc and considers Revert, the pre-swap state is gone. Capturing `prev_ezoo = state.cores[core_idx].ensemble_handle` only saves a stale pointer to memory that's been Free'd + reinit'd.

**Correct revert designs (incompatible with current Free-in-place pattern):**
- **Option A — relocate Free to caller:** EngineSharded_HotSwapEnsemble doesn't call Free; takes a SECOND output ezoo pointer. Caller passes new + old; on success Frees old; on failure Frees new + keeps old. Requires substantial API restructure (~100 LOC).
- **Option B — deep-copy before Free:** Capture function does a deep clone of the pre-swap ezoo (handles + bandit counts + horizon arrays). Costly: deep-copy of a ModelHandle includes XGBoost booster pointers, scaler, etc. Roughly ~1MB+ per core to clone. Not free.
- **Option C (RECOMMENDED — log-and-leave, acknowledge limitation):** Drop the "true revert" goal for v5.15.4. Single-zoo branch keeps existing Free+Init+Load semantics. On post-load validate failure, the new model stays loaded but flagged degraded — operator manually reverts via cfg+restart. This is the existing v5.10.0c semantics; just makes it explicit. TECH_DEBT-005 stays open as "true rollback requires API restructure" with effort estimate.
- **Option D — restructure with shadow load:** Both Free + Load happen on a SHADOW zoo; only on success does the shadow get atomically swapped into state.cores[c]. This is the "load new before destroying old" pattern. Same scope as Option A — significant API change.

**Plan v5.15.4 effort claim:** ~130 LOC for "HotSwapSnapshot infrastructure". Realistic estimate for Option A or D: 300-400 LOC + new tests. Plan amendment OR scope reduction required.

**Recommended amendment:**
- Either de-scope TECH_DEBT-005 from v5.15.4 (close it as DOCUMENTED-RISK with effort estimate for proper closure deferred) — current v5.10.0c "log-and-leave" semantics persist; v5.15.4 strict-mode flips already provide much of the operational safety benefit by REFUSING boot in live mode if held_out_stamp_secret empty etc.
- Or restructure v5.15.4 ship to ~6-8 hour scope with shadow-load (Option D) — moves into a more focused dedicated ship.

**Cross-ref:** PARITY-009, PARITY-011, PARITY-012 closed PostLoadSetup parity at single-zoo + ensemble; they did NOT close the "validate failure leaves degraded state" surface. The current "log-and-leave" semantics are CLAUDE.md item 19 documented pattern — restructuring requires planning.

**PARITY-NNN allocation:** PARITY-023 (new). Severity = MEDIUM (existing behavior is functional; plan's proposed revert is the new design flaw).

---

## MEDIUM findings (parity-risk; consider amending)

### MEDIUM.1 — v5.15.4 stamp body byte-equivalence claim contains documentation error

**Site:** Plan v5.15.4 line 199-205.
**Issue:** Plan claims "legacy cfg loaded under `trading_mode=live` will emit a stamp body with `model_verify_strict=1` (normalized value) — DIFFERENT from a pre-v5.15.4 stamp emitted with the same legacy cfg".
**Verification:** Neither `model_verify_strict` nor `reconcile_mode` is in FOREACH_STAMP_BOUND_CFG (grep confirmed). They are runtime engine cfg fields, never stamp-bound. The normalize pass does not affect stamp body bytes for these fields.
**Real difference:** ONLY the NEW `trading_mode` field changes stamp body bytes between legacy cfg + v5.15.4 cfg (covered by Surface 2 PASS).
**Amendment required:** Plan v5.15.4 line 199-205 reword to remove the false claim. The normalize pass IS observable via engine boot WARN log + runtime behavior change, but NOT via stamp body bytes.
**Severity:** LOW-MEDIUM (documentation error; doesn't cause runtime bug, but misleads readers + audit reproducers).

### MEDIUM.2 — Stale line numbers + file paths across multiple subplans

**Issues found:**
- MASTER line 41 (v5.15.0 §): "16 uint8_t has_* direct fields" — actual count is 14. (Plan's own subplan + Step 0 grep both say 14.)
- v5.15.2 line 100-101: parser location "`CoreFrameworks/ControllerConfigParser.hpp` parse_csv_engine_config" — actual file is `CoreFrameworks/ControllerConfig.hpp` (no separate `ControllerConfigParser.hpp`); parser starts at line ~2371.
- v5.15.4 line 217: "v5.10.0c log-and-leave comment at :2803-2806" — actual comment appears at EngineSharded.hpp:2879 + :2943 + :2964 (3 different locations).
- v5.15.4 line 295: "single-zoo branch (line ~2836)" — actual single-zoo branch starts at EngineSharded.hpp:2914 (the `} else {` after ensemble branch). Line 2836 is the `swap_zoo = (CoreModelZoo<F>*)state.cores[c].model_handle;` cast that's used by BOTH branches.
- v5.15.4 line 333: "ensemble branch (line ~2846)" — actual ensemble branch is at line 2846 (close enough).
- v5.15.1 line 162: "6 existing state_flags entries" — actual count is 7 X entries in PerCoreStateFlagsRegistry.hpp.
- MASTER §v5.15.0 line 425 says "14 has_* fields" — correct; contradicts the line 41 "16 has_*" claim — internal MASTER inconsistency.

**Recommended amendment:** Step 0 of v5.15.0 .A includes `rg -n "^\s*uint8_t\s+has_"` to enumerate actual count + paths; verify line numbers in all subplans match HEAD before coding starts. Same for v5.15.2 / v5.15.4 file path references.

**Severity:** MEDIUM (stale paths waste audit reproducer cycles; line numbers can be re-grep'd at code time).

### MEDIUM.3 — v5.15.0 plan calls bare `STAMP_HAS(result, TRAINING_POLL_INTERVAL)` macro from outside the registry header; verify reachable from tests

**Site:** Plan v5.15.0 .C Test 2 (line 372-376) uses `STAMP_HAS(result, TRAINING_POLL_INTERVAL)` and individual TIRE_POLL_INTERVAL constants. Verify that the new STAMP_HAS aliases (HANDLE_HAS / HANDLE_SET / HANDLE_CLR per plan Step 3 line 196-198) and MASK_HANDLE_HAS_* constants are visible to test code via header inclusion.

**Recommended:** v5.15.0 .C tests verify static_assert(MASK_HANDLE_HAS_TRAINING_POLL_INTERVAL == (1ULL << 0)) etc. so bit positions are tested. Otherwise a future re-ordering could silently change wire format.

**Severity:** MEDIUM (operational discipline; reachability is easy to add).

### MEDIUM.4 — v5.15.2 trading_mode emit_when=1 vs trading_mode parsed value mismatch on legacy stamps

**Site:** v5.15.2 registry row at plan line 165-167. `emit_when=1` (always emit). Legacy stamps lack the row → parser leaves `parsed_result.trading_mode = 0` (default_val) + `parsed_result.has_trading_mode = 0`.

**Issue:** v5.15.2 plan §3 (Step 3) "Site 7 — CoreModelZoo drift check" (line 247-258) generates a drift check `if (STAMP_HAS(parsed_result, TRADING_MODE) && parsed_result.trading_mode != cfg.trading_mode) WARN`. Legacy stamp has STAMP_HAS=0 → drift check NOT fired → no WARN. **Correct behavior. PASS.**

**But:** Live-mode boot gate (v5.15.2.B) checks `cfg.trading_mode == LIVE` and proceeds with pre-flight checks. A legacy stamp loaded under live cfg gets has_trading_mode=0 (effective PAPER at training time per plan default). Operator running engine under LIVE cfg sees no WARN about training-time mode (because has=0 means "pre-v5.15.2 stamp; mode unknown"). **This is a gap:** for v5.15.2+ stamps with has=1 + trading_mode=PAPER (model trained under paper), engine running LIVE should WARN ("model trained under paper, serving in live"). The drift check at Site 7 covers this — IF the stamp has the flag.

**Recommended:** Plan v5.15.2 §B add an additional pre-flight check: "ALL loaded models' stamps carry has_trading_mode=1 (= v5.15.2+ models) AND parsed_result.trading_mode == cfg.trading_mode". For legacy stamps (has=0), pre-flight WARN: "model predates v5.15.2; training-time mode unknown — recommend retraining under explicit trading_mode=live for full audit trail". Severity = WARN, not REFUSE.

**Severity:** LOW-MEDIUM (defense-in-depth; doesn't break current parity but improves operational clarity).

### MEDIUM.5 — v5.15.3 setenv at foxml_suite.cpp:main() — engine binary unaffected confirmed; but ./engine and other binaries inherit env if shell-spawned

**Site:** v5.15.3.B plan line 324, sets `OMP_NUM_THREADS=1` at foxml_suite.cpp:main() entry.

**Issue:** plan correctly notes ./engine binary is unaffected (engine doesn't run XGBoost training). However if an operator workflow involves shell-spawning ./engine FROM the foxml_suite GUI (or vice versa), the env var inherits. Today there's no such workflow, but future automation might.

**Recommended:** plan add comment that the setenv affects ONLY the foxml_suite process — child processes will inherit. Not a parity issue today; flag for future workflow design.

**Severity:** LOW (informational).

### MEDIUM.6 — v5.15.0 plan parser dispatch table refactor: ensure parser preserves "unknown key → silent skip" semantics

**Site:** Plan v5.15.0.B (line 295-301). Plan says "Future-compat: unknown key = WARN log, keep loading". 

**Issue:** Current `verify_model_stamp` parser (around ModelInference.hpp:1420) silently ignores unknown keys (per CLAUDE.md item Surface G forward-compat). Changing to "WARN log" alters the operational behavior — operator running v5.15.0 engine with a v5.15.future stamp will see WARNs in logs for any new key.

**Recommended:** Plan amend to preserve "silent skip" for unknown keys (= existing behavior) OR add cfg.parser_warn_unknown_keys=0 default (preserves silent skip; operator can opt in to verbose WARNs).

**Severity:** LOW (boot-only log noise; not a parity bug; preserves Surface G).

---

## LOW findings (informational; documented exception cases)

### LOW.1 — train_model_worker_fn doesn't use scaler_sha256_buf var; plan v5.15.3 helper expects it

Plan v5.15.3 helper signature line 156 includes `scaler_sha256_hex` (may be empty); but the per-horizon worker path doesn't have a `scaler_sha256_buf` populated at the call site (verified — no such variable in `mh_run_one_horizon_fv` context). Either:
- helper accepts empty string for missing sidecar (already does; no-op),
- per-horizon caller needs to compute SHA256 of the per-horizon scaler if persisted,
- RFV-routed approach (HIGH.2) inherits scaler binding from RFV's existing scaler_sha256 path — no extra work.

Recommendation: per HIGH.2's RFV-routed approach, this concern dissolves. Otherwise plan needs to specify how per-horizon scaler SHA gets computed.

### LOW.2 — DOC: v5.15.0 plan says `STAMP_HAS_FLAGS_BIT` enum exists; verify in ModelStampResult

Plan v5.15.0 §3 line 196-198 defines HANDLE_HAS / SET / CLR macros that resolve to BITMAP_* primitives on `MASK_HANDLE_HAS_*`. ModelStampResult already uses `MASK_STAMP_HAS_*` per the workspace pattern. The dual naming (`MASK_HANDLE_HAS_*` for ModelHandle + `MASK_STAMP_HAS_*` for ModelStampResult/StampInferenceCfgInputs) is intentional — they are different structs — but the plan should note that future maintainers don't accidentally cross-pollinate the masks. Add inline comment in ModelInference.hpp post-migration: "MASK_HANDLE_HAS_* applies to ModelHandle; MASK_STAMP_HAS_* applies to ModelStampResult + StampInferenceCfgInputs. Don't share."

### LOW.3 — DOC: v5.15.3 trade-off table (line 537-548) — "fork-based process pool" deferred is fine; no recommended action

Plan correctly captures the trade-off + recommendation. No action needed.

### LOW.4 — v5.15.2 has_trading_mode parser auto-generation: verify the data-driven parser table (v5.15.0.B) handles the new row cleanly

Plan v5.15.0.B refactors parser to data-driven dispatch. v5.15.2 adds 1 new entry to FOREACH_STAMP_BOUND_CFG. Verify that v5.15.0.B's dispatch table auto-grows by walking FOREACH_STAMP_BOUND_CFG (per plan Step 1 line 268-272) so v5.15.2's row Just Works. **PASS by registry-driven design — adding the row auto-grows the table.** Document as expected; no action.

---

## HMAC chain analysis (legacy + new stamp byte sequences)

**Setup:** HMAC-SHA256 keyed by `cfg.held_out_stamp_secret` over the canonical body (all key=value lines concatenated). Verified at ModelInference.hpp:1949 (write) + :1697 (verify).

**Pre-v5.15 baseline (v5.14.post1):**
```
model_sha256=<64-hex>
trained_on=YYYY-MM-DD
wf_mean_val=0.62
held_out_metric=0.53
... (PRE_CFG entries from FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG: inference_cfg_*, bandit_blend_ratio, fees, training_poll_interval, scaler, model_num_outputs, xgb_hyperparams, build_flags_hash, grid_member_count, grid_member_idx [if populated; today never], label_registry_hash, feature_mask, label_lookahead_ticks, label_tp_pct, label_sl_pct, xgb_train_nthread)
... (FOREACH_STAMP_BOUND_CFG entries: ridge_within_horizon, ridge_across_horizons, ridge_lambda, ridge_cost_penalty, ridge_min_ic_floor, confidence_composite_enabled, confidence_freshness_tau_secs, confidence_capacity_target_dollars, confidence_capacity_kappa, confidence_rmse_baseline, winsor_pct_low, winsor_pct_high, exit_blender_mode, risk_degradation_curve, risk_full_size_threshold, risk_min_size_threshold, risk_min_size_pct, ml_buy_threshold, gap_acceptable_threshold, bandit_algorithm, thompson_mu_prior, thompson_precision_prior, thompson_precision_obs)
... (POST_CFG entries from FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG: expected_num_classes, expected_role, expected_num_features, expected_feature_format_version, overlay_hash, effective_hash, training_timestamp_us, run_name, scaler_fit_data_hash, removal_reasons_csv, environment_*)
signature=<HMAC-SHA256 over all above>
```

**v5.15.0 ModelHandle migration:** Wire format UNCHANGED. The HANDLE_HAS macro and uint64_t has_flags are RUNTIME representation; wire format still emits one line per field with key=value. Migration is INTERNAL-ONLY. **HMAC byte-identical.**

**v5.15.2 trading_mode addition:** New row APPENDED at end of FOREACH_STAMP_BOUND_CFG → new line `trading_mode=<int>\n` appears between `thompson_precision_obs` and the POST_CFG `expected_num_classes`. **For new emits:** new HMAC value (intentional; documented in CHANGELOG). **For legacy stamps loaded on v5.15 engine:** parser doesn't find `trading_mode=`, leaves has_trading_mode=0 + trading_mode=0; **HMAC verification is unaffected** because the verifier re-computes the canonical body from the stamp file (NOT the C struct) + computes HMAC over the bytes read. Legacy stamp's HMAC matches its own canonical body.

**v5.15.4 normalize pass:** Doesn't change any stamp-bound field (verified: model_verify_strict + reconcile_mode are NOT in registry). **HMAC byte-identical to v5.14.post1 for any cfg.**

**v5.15.3 grid_member_count fix (per HIGH.2 revised approach):** After fix, multi-horizon stamps will INCLUDE `grid_member_count=3\n` and `grid_member_idx=2\n` lines (where they were absent before). Per-horizon stamp file's HMAC will be NEW (incorporates the new lines). Single-horizon stamps (RFV called from Train Model + RFV directly) will continue NOT emitting these lines (req_grid_member_count=0 → group bit unset → emit walk skips). **Single-horizon HMAC byte-identical to v5.14.post1; multi-horizon HMAC NEW for v5.15.3+ models (intentional; documented).**

**Verdict:** HMAC chain integrity preserved across v5.15. Each new emit has a verifiable HMAC; legacy stamps load + verify cleanly.

---

## Cross-mode byte-equivalence verdict (v5.15.3 serial vs parallel)

**Plan Test 4 (line 469-477):** Serial-mode + parallel-mode per-horizon stamps must be SHA-256-identical byte-for-byte (same cfg + label snap + horizon params + seed).

**Current state:** Both serial-mode (`train_multi_horizon_worker_fn` direct loop) and parallel-mode (`mh_per_horizon_parallel_worker` pthread) call `mh_run_one_horizon_fv`, which calls `Backtest_RunFullValidation`. RFV's stamp emit is deterministic given inputs.

**Sources of potential divergence:**
1. **xgb_train_nthread cfg field:** parallel mode pins `job->isolated_results.config_used.xgb_train_nthread = 1` (BacktestPanels.hpp:3961). Serial mode uses `results->config_used.xgb_train_nthread` directly (operator's cfg value, could be > 1 by default). The stamp emit reads `data->config_used.xgb_train_nthread` (BacktestEngine.hpp:1227). **Different value → different stamp body bytes.**
2. **xgb_eval_nthread cfg field:** parallel mode also pins to 1. Stamp doesn't bind this (verified: no entry in FOREACH_STAMP_BOUND_CFG for xgb_eval_nthread). No stamp divergence.
3. **Training random seed:** both modes use the same `state->ui_seed` snap → identical XGBoost training inputs → identical model bytes → identical model_sha256.
4. **Wall-clock timestamps (training_timestamp_us):** if both modes are run in same session, timestamps differ by milliseconds. Stamp binds training_timestamp_us in POST_CFG (verified at registry line 401-403). **Different value → different stamp body bytes.**
5. **Build flags hash + label registry hash:** identical across both modes (compile-time).

**v5.15.3 Test 4 cannot pass for #1 + #4 without adjustment:** the test must either (a) compare stamp bodies EXCEPT for xgb_train_nthread + training_timestamp_us (filtered comparison) or (b) set serial-mode cfg.xgb_train_nthread = 1 explicitly AND mock clock to a fixed value. Approach (b) is closer to a true byte-identity test; approach (a) is more practical.

**Recommended plan amendment:** Test 4 description should clarify the "byte-equivalent EXCEPT for known-different fields" contract, OR formalize the test setup (fixed clock + pinned xgb_train_nthread). The current plan text suggests pure byte-equality which is achievable only with explicit setup.

**Verdict:** TEST 4 CONCEPT VALID, but plan needs amendment for executability. Severity = MEDIUM (test design, not parity bug).

---

## PARITY_ISSUES.md entries written (new findings — 4 total)

- **PARITY-020** (HIGH) — train_model_worker_fn missing STAMP_CFG_AUTOPOPULATE (asymmetric with RFV); v5.14.post1 closed field-name migration but not AUTOPOPULATE wiring. 22 cfg fields silently absent from Train Model stamps.
- **PARITY-021** (HIGH) — v5.15.3 plan root cause MISDIAGNOSED. Multi-horizon DOES stamp via RFV; gap is that grid_member_count/_idx fields are never populated by any production caller. Plan's `stamp_emit_for_horizon` helper is redundant; fix should plumb req_grid_member_count through FullValidationResults into RFV's existing emit path.
- **PARITY-022** (MEDIUM) — STAMP_MODEL_CONST_AUTOPOPULATE macro is defined but unused; expansion is self-referential (would assign field to itself). Plan v5.15.3 relies on this macro working.
- **PARITY-023** (MEDIUM) — v5.15.4 HotSwapSnapshot/Revert design captures only pointers; pre-swap data is destroyed in-place by Free. Revert is non-functional.

---

## Synthesis

The v5.15 sprint plan is **structurally sound on the v5.15.0 ModelHandle migration + v5.15.2 trading_mode introduction + v5.15.1 Model Health panel** — these are well-scoped, the patterns are established (X-macro migration, BITMAP_* API, Surface G has_* forward-compat, cohort-audit), and the HMAC chain logic checks out.

**Three substantive issues block green-lighting v5.15.3 + v5.15.4 as written:**

1. **v5.15.3 has a factual root-cause error (PARITY-021):** Multi-horizon worker already stamps via RFV. The "missing grid_member_count" warning is because NO production caller populates grid_member_count anywhere — the registry fields are orphan placeholders. The correct fix is plumbing req_grid_member_count through FullValidationResults into RFV's existing emit, NOT adding a parallel stamp_emit_for_horizon helper. This REDUCES v5.15.3 scope from ~150 LOC to ~30 LOC + closes the same boot warning cleanly + avoids creating a parallel emit path.

2. **train_model_worker_fn is missing STAMP_CFG_AUTOPOPULATE (PARITY-020):** A v5.14.post1-era gap. RFV uses AUTOPOPULATE for ~22 stamp-bound cfg fields; Train Model worker doesn't. Today's Train Model stamps lack drift detection for ridge/composite/winsor/exit_blender/risk/expected_thresholds/bandit cohorts. v5.15.3 should bundle this 1-LOC addition for symmetry across all 3 production callers (RFV + train_model_worker_fn + multi-horizon via RFV).

3. **v5.15.4's HotSwapSnapshot/Revert design (PARITY-023) doesn't work** because pre-swap state is destroyed in-place by Free. Capturing pointers alone is insufficient. Recommended de-scope: keep current "log-and-leave" semantics; close TECH_DEBT-005 as DOCUMENTED-RISK with effort estimate for proper restructure (300-400 LOC shadow-load) deferred to a future sprint. v5.15.4 keeps the trading_mode strict-default flip (cleanly delivers operational safety improvement) but drops the hot-swap unification.

**Plus 6 MEDIUM and 4 LOW findings** that are easier corrections (stale line numbers, documentation accuracy, parser-warn semantics).

**Suggested ship sequence after amendments:**
- v5.15.0 — ModelHandle migration + parser refactor (HIGH-RISK as planned; baseline freeze SHA-256 captured pre-migration)
- v5.15.1 — Model Health panel (LOW-RISK as planned; PerCoreStateFlagsRegistry headroom 7+4=11/16)
- v5.15.2 — trading_mode + boot gate + breakeven wire-up + readiness check (MEDIUM-RISK as planned; add MEDIUM.4 pre-flight check)
- v5.15.3 — REVISED scope: plumb req_grid_member_count through FullValidationResults + RFV; add STAMP_CFG_AUTOPOPULATE to train_model_worker_fn for symmetry; libgomp setenv at foxml_suite main; remove v5.11.45 forced-serial. **DROP stamp_emit_for_horizon helper.** ~30 LOC + tests vs original ~150 LOC. Same TECH_DEBT closures.
- v5.15.4 — REVISED scope: trading_mode strict-default flip only. **DROP hot-swap unification.** TECH_DEBT-005 stays open with effort estimate. ~50 LOC vs original ~180 LOC.

**Net effect of amendments:** v5.15 sprint shrinks by ~250 LOC + ~5 hours; closes 4 TECH_DEBT (003, 014, 024, 028, 033) instead of original 6 (TECH_DEBT-005 deferred); ships are cleaner + parity-safe.
