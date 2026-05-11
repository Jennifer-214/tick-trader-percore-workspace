# /readiness report — `2026-05-06-v5.10.2-hot-swap-parity-hardening.md` — 2026-05-06

**Audited:** `plans/2026-05-06-v5.10.2-hot-swap-parity-hardening.md`
**HEAD:** `32155e1` (v5.10.1.C — AutoDetect cfg-args plumb-through)
**Predecessor plan:** `plans/2026-05-06-v5.10.1-production-caller-closure.md` (LANDED)
**Audit driver:** `plans/plan_checks/parity-2026-05-06-full.md` Findings #3, #4, #7, #10

---

## Plan summary

- 2 phases (`v5.10.2.A` extract validator helper, `v5.10.2.B` REFUSE hot swap when ensemble active)
- Closes 4 parity-check findings: #3 + #7 + #10 in Phase A (single helper extraction), #4 in Phase B (Option A REFUSE; Option B = full ensemble swap deferred)
- Effort: ~3-4h (~205 LOC total)
- Branch: `experiment/per-core-sharding` (consistent with v5.10.1 sub-ship cadence)
- Files: 2 (`EngineSharded.hpp` + new helper in `ControllerEventLoop.hpp` per plan / `ML_Headers/CoreModelZoo.hpp` per v5.10.1.B precedent)
- Hot path: UNTOUCHED (verified — `ExecutionCore_Tick` at line 1933, well outside edit zones at 885-1060 + 2425-2515)

---

## Checklist verdicts

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | PASS | No edits to BG_Evaluate / SG_Evaluate / ExecutionCore_Tick. All edits are slow-path / boot-time. |
| 2 | Train-serve parity | PASS | This plan IS a parity hardening — extends drift detection to ensemble + hot-swap paths. No new compute that must agree across sites. |
| 3 | Surface area | PASS | 2 files touched. Within audit scope. |
| 4 | Pointer init / heap lifecycle | PASS | No new heap allocations; helper is stateless. |
| 5 | Backward compat | PASS | No format/version bumps. |
| 6 | Multi-threading | PASS | Helper called from slow-path only. No new shared state, no atomics. |
| 7 | Test coverage | YELLOW | +4 tests promised; test names + scope described conceptually but no `check()` patterns spelled out. v5.10.1's 0xDEADBEEF handle pattern would be relevant precedent. |
| 8 | Docs + invariants | YELLOW | No mention of `DOCS/CHANGELOG.md` update or new entry. CLAUDE_INVARIANTS.md may want a row about "all post-load validators must run on hot-swap reload too." |
| 9 | Forward maintenance | PASS | The helper extraction is itself the forward-maintenance fix (multi-site → single site). Inherits v5.10.1.B precedent shape. |
| 10 | Rollback story | PASS | `pre-v5.10.2` anchor + per-phase tags + final tag named explicitly. |
| 11 | Architectural sprint | PASS | Not an architectural sprint; targeted extraction with explicit before/after wiring. |
| 12 | Display ↔ execution | PASS | Plan explicitly preserves `cfg_drift_tier1_count` / `tier2_count` / `strict_refused` writeback, restoring accuracy of ML Status panel post-hot-swap (Finding #10). |
| 13 | Strategy lifecycle | N/A | Plan does not touch strategies. |
| 14 | X-macro / function-pointer | N/A | No X-macro touched. |
| 15 | ML feature change → snapshot | PASS | No FOREACH_FEATURE / FEATURE_REGISTRY_HASH change. |
| 16 | Stamp-bound cfg → recipe | PASS | No new cfg field added; uses existing stamp_inf_* fields. |
| 17 | Model-load path → strict-mode | PASS | Plan EXTENDS strict-mode coverage (was boot-only, now also hot-swap). PerCoreSnap fields already exist. Distinct log shape preserved. |

---

## Dependency verification (file:line claims at HEAD `32155e1`)

| Plan claim | Verified at HEAD | Status |
|---|---|---|
| `EngineSharded.hpp:957-1064` (drift block) | Block actually at **964-1077** | NIT — shifted +7 due to v5.10.1.C plumb |
| `EngineSharded.hpp:885-953` (xgb block) | Block actually at **885-960** (xgb subsection ~906-948) | NIT — start matches; end +7 |
| `EngineSharded.hpp:2456-2502` (hot swap reload) | Range actually **2435-2513** (full block); reload site **2483-2510** | NIT — entire block shifted; plan's "after `loaded > 0` succeeds" landmark is at line 2491 |
| `EngineSharded.hpp:858` (ensemble_handle set at boot) | Actually at **865** | NIT — shifted +7 |
| `EngineSharded.hpp:860` (ensemble_handle nullptr branch) | Actually at **867** | NIT — shifted +7 |
| `Strategies/StrategyParameters.hpp:794` (dispatcher reads ensemble first) | Verified at **793-794** (`(mctx ? mctx->ensemble_zoo : nullptr)` lands on 794) | OK |
| `EngineSharded.hpp:1052-1054` (cfg_drift counter writers) | Actually at **1059-1061** | NIT — shifted +7 |
| `ControllerEventLoop.hpp:601-603` (cfg_drift counters init zero) | Verified — exact match | OK |
| `EngineSharded.hpp:2424-2506` (hot swap branch range, cfg_drift counters not reset) | Verified semantics — branch only resets `model_load_failed` (lines 2491, 2500); no cfg_drift counter writes anywhere in 2435-2513 | OK |

**All file:line shifts trace to v5.10.1.C's AutoDetect-args plumb (added 7 lines around boot ensemble setup at line 832).** Plan's stale-claim audit (lines 245-258) verified against v5.10.1's predecessor HEAD `7f0b9a9`, which is now off by +7 lines.

---

## CRITICAL field-name corrections (plan's helper code WILL NOT COMPILE as written)

### 1. Plan code references `h->stamp_inf_present` — field does not exist

**Plan line 84:**
```cpp
if (!h || !h->has_xgb_hyperparams && !h->stamp_inf_present) return;
```

**Actual ModelHandle field name:** `has_stamp_inference_cfg` (`ML_Headers/ModelInference.hpp:273`)

The plan's `stamp_inf_present` is fictional. The existing v5.9.5i drift block at line 986 uses:
```cpp
if (!h->has_stamp_inference_cfg) continue;
```

Plan must replace `h->stamp_inf_present` → `h->has_stamp_inference_cfg`.

### 2. Plan code references `ezoo->exit[h]` and `ezoo->exit_count` — wrong field names

**Plan lines 110-111:**
```cpp
for (int h = 0; h < ezoo->exit_count; ++h)
    check_handle(&ezoo->exit[h], "exit", h);
```

**Actual EnsembleModelZoo field names** (`ML_Headers/CoreModelZoo.hpp:616, 620`):
```cpp
ModelHandle<F> exit_predictor[ENSEMBLE_HORIZON_MAX];  // not "exit"
int exit_predictor_count;                             // not "exit_count"
```

Verified by v5.10.1.B precedent (`EnsembleZoo_VerifyGridMemberConsistency` at `CoreModelZoo.hpp:1157`):
```cpp
case 3: role_arr = ezoo->exit_predictor; count = ezoo->exit_predictor_count; break;
```

Plan must replace `ezoo->exit[h]` → `ezoo->exit_predictor[h]` and `ezoo->exit_count` → `ezoo->exit_predictor_count`.

(The single-zoo `zoo->exit` reference at plan line 100 IS correct — see `CoreModelZoo` struct at `ML_Headers/CoreModelZoo.hpp:60`. Only the ensemble field name is wrong.)

### 3. Plan helper signature is missing the cfg acknowledgement guards

The existing boot drift block (line 970-971) is guarded by:
```cpp
if (loaded && cfg.core_model_dir[i][0] && !cfg.acknowledge_inference_cfg_drift) {
```

The xgb block (line 885-886) uses a DIFFERENT cfg flag:
```cpp
if (loaded && cfg.core_model_dir[i][0] && !cfg.acknowledge_cross_binary_version_drift) {
```

Plan's helper signature passes neither flag. The plan's call sites (lines 127-133, 146-152) likewise omit them. As written, the extracted helper either:
- Always runs both checks unconditionally (loses both acknowledgement paths), OR
- Caller must early-skip — but plan doesn't show this either.

Plan must either:
- Add `int acknowledge_inference_cfg_drift, int acknowledge_cross_binary_version_drift` params to the helper signature
- OR add early-return guards at both call sites BEFORE the helper call

### 4. Plan undersells the xgb block's scope

Plan says (lines 89-92): "xgb_hyperparams WARN ... copy-paste from EngineSharded.hpp:885-953".

The block 885-960 actually contains THREE distinct WARN groups:
- `training_poll_interval` mismatch (lines 895-905) — v5.9.4
- `xgb_hyperparams` mismatch (lines 906-948) — v5.9.5h
- `build_flags_hash` mismatch (lines 949-960) — v5.9.5h Phase 10

If the helper subsumes "the xgb block", it must subsume all three. Plan implicitly assumes this but the comment only names xgb_hyperparams.

---

## Helper-location decision (plan's open question #3)

Plan suggests `CoreFrameworks/ControllerEventLoop.hpp` (line 51) "since it owns CoreContext".

**v5.10.1.B precedent contradicts this.** The recent extraction of `EnsembleZoo_VerifyGridMemberConsistency` lives at `ML_Headers/CoreModelZoo.hpp:1141` — the same source-tree neighborhood as the EnsembleModelZoo struct itself. This is the more cohesive choice:
- Header dependencies stay local (helper sees `CoreModelZoo<F>`, `EnsembleModelZoo<F>`, `ModelHandle<F>`, `ModelStampResult` — all already in `ML_Headers/`)
- Forward-declared in `ControllerEventLoop.hpp` already includes `ML_Headers/CoreModelZoo.hpp` (transitively)
- Pattern symmetry: validators live next to validated structs

**Recommendation:** Place `EventLoop_ValidateLoadedZooAgainstCfg` in `ML_Headers/CoreModelZoo.hpp` (or a new `ML_Headers/ZooValidation.hpp` if the file is feeling crowded — currently 1760 lines). NOT in `ControllerEventLoop.hpp`. The "EventLoop_*" prefix is also slightly misleading once the helper lives in ML_Headers — consider renaming to `CoreModelZoo_ValidateAgainstCfg` (matching v5.10.1.B's `EnsembleZoo_*` naming convention).

---

## Drift audit — train ↔ serve, write ↔ read, suite ↔ engine

| Sub-category | Verdict | Notes |
|---|---|---|
| Feature drift | PASS | No FOREACH_FEATURE change. |
| Label drift | PASS | No label change. |
| Metric drift | PASS | No new metric. |
| Path drift | PASS | No path/symlink/versioning change. |
| Format drift | PASS | No serialization format change. |
| Threshold drift | PASS | No new threshold; existing cfg fields read at single (helper) site. |
| Tick-source drift | PASS | No tick source change. |
| Build-flag drift | PASS | No new build flag. |

**Net:** plan is drift-neutral (extraction-only, behavior-preserving for non-ensemble + non-hot-swap paths). Drift HARDENING for ensemble + hot-swap paths.

---

## Hidden scope detected

1. **Field-name corrections** (~10 min): two field-name fixes in helper code (`stamp_inf_present` → `has_stamp_inference_cfg`; `ezoo->exit*` → `ezoo->exit_predictor*`).

2. **Acknowledgement-flag plumbing** (~15 min): helper signature needs to accept (or call sites need to early-skip on) the two suppression flags. Otherwise extraction silently drops the existing acknowledgement contract.

3. **xgb block scope expansion** (~10 min documentation; behavior unchanged): comment in helper that all three v5.9.4/5.9.5h WARN groups land in here, not just xgb_hyperparams.

4. **Test scaffolding** (~30 min): the v5.10.1.B test pattern uses 0xDEADBEEF mock handles in `EXTENSIBILITY` block. The 3 new tests in v5.10.2.A will likely need a similar fakery shape — load handle data into a stack ModelHandle without going through the full file-read path. Plan describes these conceptually only; flag for implementation-time refinement.

Total hidden scope: ~65 min (within audit's 3h estimate).

---

## Cold-pickup completeness audit (10 fields per CLAUDE.local.md)

| # | Field | Verdict | Notes |
|---|-------|---------|-------|
| C.1 | Branch state | PASS | `experiment/per-core-sharding` named explicitly (line 4) |
| C.2 | Phase order | PASS | A → B; A is "extract helper", B uses helper context. Order correct. |
| C.3 | First concrete move | PASS | "Step 0: Helper extraction" (line 49) + Step 1 + Step 2 each have explicit start. |
| C.4 | Function names cited | YELLOW | Helper name + signature given. BUT field names `stamp_inf_present` (line 84) and `ezoo->exit*` (lines 110-111) are wrong — fresh session would discover at compile time. |
| C.5 | File:line refs for tests | YELLOW | "Existing v5.9.5i drift tests at controller_test.cpp (line ranges TBD; spot-check before write)" — line 174 explicitly defers. v5.9.5i tests start at controller_test.cpp:12055. Plan should include this. |
| C.6 | Stale-claim audit | YELLOW | Plan has a stale-claim audit section (245-258) but it's verified against `7f0b9a9` (pre-v5.10.1) — line numbers shifted +7 after v5.10.1.C landed. |
| C.7 | Effort vs LOC | PASS | ~205 LOC for ~3h is consistent (~70 LOC/hour for moderate-complexity extraction). |
| C.8 | Source-audit refs | PASS | Cites parity audit + master plan + predecessor plans with paths. |
| C.9 | Predecessor plans | PASS | All cited with full paths (lines 280-285). |
| C.10 | Tag names | PASS | `pre-v5.10.2`, `v5.10.2.A`, `v5.10.2.B`, `v5.10.2` all unique + ordered. |

**Score: 7/10 PASS, 3/10 YELLOW.** All YELLOW items are LINE-NUMBER STALENESS (not structural defects) — fresh session would auto-correct on first grep.

---

## Hardening checks

| Check | Verdict | Notes |
|---|---|---|
| Atomic file writes | N/A | No file writes. |
| Locale pinning | N/A | No string-formatting hash. |
| GUI render-thread blocking I/O | N/A | No GUI panel touched. |
| Failure telemetry path | PASS | All new failure modes log via `fprintf(stderr, "[boot] FATAL ..."` or `[hot_swap] core %d REFUSED ..."` — explicit, distinguishable. |
| Resource cleanup | PASS | Helper allocates nothing. |
| Cancellation semantics | N/A | Synchronous helper. |
| Cross-platform | PASS | No new POSIX-only call. |

---

## Propagation checks

| Adding... | Plan covers? |
|---|---|
| New helper function | Tests planned. CODE_MAP regen needed post-coding. |
| New invariant claim ("post-load validators run on hot-swap too") | NOT mentioned. Worth adding to `DOCS/CLAUDE_INVARIANTS.md`. |
| CHANGELOG entry | NOT mentioned. v5.10.2 must add. |

---

## Risks specifically called out by user

### Risk 1: v5.10.1 line-shift caveat — CONFIRMED
All 7 cited line numbers in `EngineSharded.hpp` have shifted +7 due to v5.10.1.C's AutoDetect args plumb at line 832. None are catastrophic — a fresh session greps the relevant token and finds the new location in <30s. But the plan's stale-claim audit is itself stale. **Fix during coding.**

### Risk 2: Helper location open question — RESOLVE NOW
Plan says `ControllerEventLoop.hpp` OR new `EventLoopValidation.hpp`. Recommend `ML_Headers/CoreModelZoo.hpp` per v5.10.1.B precedent (and rename to `CoreModelZoo_ValidateAgainstCfg`). Alternative: new `ML_Headers/ZooValidation.hpp` if 1760 LOC of CoreModelZoo.hpp feels too dense. **Decision: ML_Headers, NOT CoreFrameworks.**

### Risk 3: Hot-swap rollback semantics — ACCEPT log-and-leave
- No pre-swap path caching infrastructure exists (verified — `swap_model_path_requested[]` + `pending_model_path[]` is the only swap state)
- `ml_zoos[]` is `static CoreModelZoo<F>` inside the engine boot scope; not directly accessible to slow-path
- True rollback would require operator-level cfg work or a two-phase load
- Plan's choice (log + `model_load_failed=1`) matches the existing failed-swap behavior at line 2497-2500 (also nulls `model_handle` + sets flag). Symmetric, intuitive.
- **ACCEPT**: log-and-leave is correct given current infrastructure. Capture as DEFERRED for v5.10.X if operator wants stronger semantics.

### Risk 4: `stamp_inf_present` field name — CONFIRMED WRONG
Field is `has_stamp_inference_cfg` (`ML_Headers/ModelInference.hpp:273`). Plan must amend.

### Risk 5: Phase A test scope realism — YELLOW
Plan describes 3 tests conceptually but doesn't spell out the fakery shape. v5.10.1.B's recent test in EXTENSIBILITY block (the 0xDEADBEEF handle pattern) is the relevant precedent — fresh session would mimic that. Worth adding a one-line cross-ref to plan.

### Risk 6: v5.10.1.B helper precedent cross-reference — YELLOW
Plan does NOT name the v5.10.1.B precedent (`EnsembleZoo_VerifyGridMemberConsistency` at `CoreModelZoo.hpp:1141`). This is the canonical "extraction with iteration over single + ensemble" shape that the plan reinvents from scratch. Fresh session would benefit from "see also v5.10.1.B".

---

## Recommendations

### Must fix before coding (~30 min)

1. **Fix field names in helper code:**
   - `stamp_inf_present` → `has_stamp_inference_cfg` (plan line 84)
   - `ezoo->exit[h]` → `ezoo->exit_predictor[h]` (plan line 111)
   - `ezoo->exit_count` → `ezoo->exit_predictor_count` (plan line 110)

2. **Decide helper location explicitly:** Recommend `ML_Headers/CoreModelZoo.hpp` per v5.10.1.B precedent + rename to `CoreModelZoo_ValidateAgainstCfg`. Update plan §A.Step 0 + §"Open questions" #3 to reflect the decision.

3. **Add acknowledgement-flag handling to helper signature OR call sites.** Either:
   - Helper signature: add `int acknowledge_inference_cfg_drift, int acknowledge_cross_binary_version_drift` params
   - OR call sites: add early-skip guards before the helper call (matching existing semantics)

4. **Update file:line refs for v5.10.1.C shift (+7 lines).** Specifically:
   - 957-1064 → 964-1077 (drift block)
   - 885-953 → 885-960 (xgb-and-friends block)
   - 2456-2502 → 2483-2510 (hot swap reload site within 2435-2513 branch)
   - 858 → 865 (ensemble_handle set at boot)
   - 860 → 867 (ensemble_handle nullptr branch)
   - 1052-1054 → 1059-1061 (drift counter writers)

### Worth fixing during coding

5. **Cite v5.9.5i drift test entry point** (`tests/controller_test.cpp:12055`) in plan §A.Verification.

6. **Cross-reference v5.10.1.B precedent** in plan §A.Step 0 ("see CoreModelZoo.hpp:1141 for the extraction shape").

7. **Document the xgb block's full scope** in helper comment (training_poll_interval + xgb_hyperparams + build_flags_hash; not just xgb_hyperparams).

8. **Add CHANGELOG entry** to plan's final-tag composite verification list.

9. **Consider new invariant entry** in `DOCS/CLAUDE_INVARIANTS.md`: "All post-load model validators (drift, hyperparams, build-flags, label hash) must run on hot-swap reload too — extraction enforced via `CoreModelZoo_ValidateAgainstCfg`."

### Acceptable risk (don't block)

10. Phase A test fakery shape (use v5.10.1.B's 0xDEADBEEF handle pattern; refine at test-write time).
11. Helper-name "EventLoop_*" prefix is mild misnomer once moved to ML_Headers; rename to `CoreModelZoo_*` consistent with v5.10.1.B precedent.
12. Phase B Option B (full ensemble swap) deferred is correct given operator hasn't requested it; plan's Option A REFUSE is the safer ship.

---

## Map-update suggestions (post-coding)

- Run `./tools/gen_code_map.sh` after coding (one new function: `CoreModelZoo_ValidateAgainstCfg` if location-rename adopted, else `EventLoop_ValidateLoadedZooAgainstCfg`).
- `INVARIANTS_MAP.md`: consider promoting the v5.9.5i drift test row to ENFORCED-with-ensemble-coverage after Phase A's +2 ensemble tests land.

---

## Verdict: YELLOW

**YELLOW — fix the must-fix items above first (~30 min).**

Plan is structurally sound (correct architecture, correct phase order, hot path untouched, audit findings cleanly mapped). The 30 min of fixes are mechanical (field-name corrections + line-number refresh + helper-location decision + acknowledgement-flag handling). Once those land, the plan is GREEN to start coding — Phase A's helper extraction is well-bounded and Phase B's REFUSE guard is trivially small.

Risk profile is LOW: Phase A is a behavior-preserving extraction (replay-determinism test will catch any accidental drift); Phase B is a guard-only addition that activates only when ensemble is active. Pre-tag rollback anchor (`pre-v5.10.2`) provides clean recovery path.

**Top recommendation:** Spend 30 min before opening the file to: (a) fix the three field-name typos in the helper code, (b) settle helper location at `ML_Headers/CoreModelZoo.hpp`, (c) add acknowledgement-flag plumbing — then start coding.
