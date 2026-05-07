# /readiness report — `2026-05-06-v5.10.3-display-and-observability.md` — 2026-05-06

**Audited:** `plans/2026-05-06-v5.10.3-display-and-observability.md`
**HEAD:** `9d8a464` (v5.10.2 — Hot swap parity hardening)
**Predecessors:** v5.10.1 (commit `32155e1`, tag `v5.10.1`), v5.10.2 (commit `9d8a464`, tag `v5.10.2`) — both shipped + pushed
**Audit driver:** `plans/plan_checks/parity-2026-05-06-full.md` Findings #5/#15, #8, #9 (+ #11 doc-only addendum)
**Position in epic:** LAST of the three v5.10 close-out ships before re-running `/parity-check` for GREEN at v5.10-final close.

---

## Plan summary

- 3 phases (`v5.10.3.A` strat_stats array sizing fix, `v5.10.3.B` drift_history → PerCoreSnap, `v5.10.3.C` is_buyer_maker comments + KNOWN_ISSUES entry)
- Closes 3 parity-check findings: #8 (HIGH per Section K — UB warning) + #9 (MEDIUM Section J observability) + #5/#15 (HIGH+LOW comment-only deferral)
- Effort: ~2-3h (~110 LOC delta + 1 doc edit)
- Branch: `experiment/per-core-sharding` (consistent with v5.10.1, v5.10.2)
- Files: 5 source + 1 doc — `EngineTUI.hpp` (struct + populator-loop), `TUIAnsi.hpp` (warning verifies clean), `ShardedSnapshot.hpp` (populator — see correction below), `MLStatusPanel.hpp` (panel render), `EngineSharded.hpp` + `BacktestSharded.hpp` (comments), `DOCS/KNOWN_ISSUES.md` (entry append)
- Hot path: UNTOUCHED (verified — no edits to `ExecutionCore.hpp:227`/`BG_Evaluate`/`SG_Evaluate`/`ExecutionCore_Tick`; `drift_history` does not appear in `ExecutionCore.hpp` or `GateParameters.hpp`)

---

## Checklist verdicts

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | PASS | All edits are TUI snap struct, populator (slow-path), panel render (GUI thread), and comment additions. `drift_history` is read only in the populator (slow-path triggered). |
| 2 | Train-serve parity | PASS | Phase A is display-side only. Phase B is observability-side only (no compute). Phase C is comment-only and Section A audit explicitly verified parity preservation (`is_buyer_maker=0` on both train + serve sides — Finding #5 severity rationale). |
| 3 | Surface area | PASS | 5 files + 1 doc. Within audit scope. Phase B's PerCoreSnap field add is the only multi-site addition (struct + populator + panel + test = 4 sites; consistent with established v5.9.0b pattern for `ml_model_load_failed`). |
| 4 | Pointer init / heap lifecycle | PASS | No new heap allocations. PerCoreSnap fields are POD; populator uses stack-local sum/cnt. |
| 5 | Backward compat | PASS | RESOLVED — see "Open question #2 resolution" below. PerCoreSnap is NOT persisted (TUI-side mirror only); `SHARDED_SNAPSHOT_VERSION=6` applies to CoreContext, not PerCoreSnap. No version bump needed. |
| 6 | Multi-threading | PASS | Populator is the sole writer on snap fields (single-writer producer thread); panel renders on GUI thread reads from double-buffered TUISnapshot. Existing seqlock pattern. |
| 7 | Test coverage | YELLOW | 2 tests promised. `test_strat_stats_array_sizing` (static_assert — PASS conceptually). `test_drift_history_snapshot_population` — plan describes conceptually; the v5.10.0e drift test pattern at `tests/controller_test.cpp:13186-13205` is the relevant precedent. Plan should cite this entry point. |
| 8 | Docs + invariants | YELLOW | Plan mentions KNOWN_ISSUES entry (Phase C.4) but no `DOCS/CHANGELOG.md` entry mentioned. v5.10.3 must add a CHANGELOG row. Phase A's static_assert serves as a self-documenting invariant; no `INVARIANTS_MAP.md` row needed. |
| 9 | Forward maintenance | PASS | Phase A's `strat_stats[NUM_STRATEGIES]` fix is the EASY_ADDITIONS_INVARIANTS pattern (single source of truth). Phase B's PerCoreSnap field add follows v5.9.0b precedent. |
| 10 | Rollback story | PASS | `pre-v5.10.3` anchor + per-phase tags + final tag explicitly named. |
| 11 | Architectural sprint | PASS | Not architectural; targeted display + observability fixes. |
| 12 | Display ↔ execution | PASS | Phase A directly closes a display↔execution invariant breach (`-Waggressive-loop-optimizations` UB). Phase B adds a Section J distinct-failure-mode field (drift-kill ≠ MTM-kill ≠ manual-kill). |
| 13 | Strategy lifecycle | N/A | No strategy code touched. |
| 14 | X-macro / function-pointer | PASS | Phase A's fix RESPECTS the EASY_ADDITIONS_INVARIANTS X-macro pattern by sourcing array size from `NUM_STRATEGIES` (StrategyInterface.hpp:131). |
| 15 | ML feature change → snapshot | PASS | No FOREACH_FEATURE / FEATURE_REGISTRY_HASH change. |
| 16 | Stamp-bound cfg → recipe | PASS | No new cfg field added. |
| 17 | Model-load path → strict-mode | PASS | No model-load path touched. |

---

## Dependency verification (file:line claims at HEAD `9d8a464`)

| Plan claim | Verified at HEAD | Status |
|---|---|---|
| `EngineTUI.hpp:906` `StrategyStatsSnap strat_stats[5]` | Verified — exact match at line 906 | PASS |
| `TUIAnsi.hpp:824, 828` iteration with `< NUM_STRATEGIES` | Loop A at line 824 verified; second loop is at **line 827** (not 828) | NIT — minor offset, plan's "824, 828" is "824, 827" actually |
| `StrategyInterface.hpp:131` `NUM_STRATEGIES = NUM_STRATEGIES_REAL + 1` | Verified — exact match | PASS |
| `EngineTUI.hpp:1405` population loop `< 5` | Loop is at **line 1404** (`for (int i = 0; i < 5; i++)`); body lines 1405-1408 | NIT — plan cites the body line, loop header is line 1404 |
| NUM_STRATEGIES in scope at EngineTUI.hpp:906 | VERIFIED — chain `EngineTUI → PortfolioController → Strategies/MeanReversion → StrategyInterface` brings in NUM_STRATEGIES (PortfolioController.hpp uses it at lines 391, 564, 579, 646, 668) | PASS |
| `ConfidenceScore.hpp:265-273` DriftHistory struct | Verified — struct at line 265, fields `ic_samples[256]`, `ts_us[256]`, `count` (int), `head` (int), `breached` (int), `breach_first_us` (uint64_t), `kill_tripped` (int) | PASS — note: `count` is `int`, plan's `uint16_t cnt = state->cores[i].drift_history.count` does an implicit narrowing conversion (safe since count saturates at 256) |
| `ControllerEventLoop.hpp:185` drift_history field | Verified — `DriftHistory drift_history;` at line 185 | PASS |
| `ControllerEventLoop.hpp:344` core_kill_tripped (CoreContext) | Verified — `uint8_t core_kill_tripped;` at line 344 | PASS — plan correctly notes audit conflated CoreContext field with PerCoreSnap mirror |
| `ControllerEventLoop.hpp:526` DriftHistory_Init at boot | Verified — `DriftHistory_Init(&state->cores[i].drift_history);` at line 526 | PASS |
| `ControllerEventLoop.hpp:1196-1227` drift_history.breached/kill_tripped writes | Verified — `breached=1` at line 1207, `kill_tripped=1` at line 1219, also clear at 1229 | PASS |
| `EngineTUI.hpp:1103` `core_kill_tripped` in PerCoreSnap | Verified — `uint8_t core_kill_tripped;` at line 1103 in PerCoreSnap struct (lines 952-1137) | PASS |
| `EngineSharded.hpp:1399` "is_buyer_maker not available" comment | **STALE — actually at line 1467** (+68 lines from v5.10.2 helper extraction) | **GAP — must update** |
| `EngineSharded.hpp:2550` hardcoded `/*is_buyer_maker=*/0,` | **STALE — actually at line 2663** (+113 lines from v5.10.2 helper extraction + REFUSE guard) | **GAP — must update** |
| `Backtest/BacktestSharded.hpp:78-86` SharedBacktest_FromHistorical | Verified — function at lines 78-86 exactly, `t.is_buyer_maker` is dropped via `memset` zero with no later assignment; line 741 USES `ticks[i].is_buyer_maker` separately for CandleAccumulator (not for slow-path) | PASS |
| `RollingStats.hpp:116` RollingStats_Push default arg | Verified — `int is_buyer_maker = 0` at line 116 | PASS |
| `MLStatusPanel.hpp:184-203` cfg drift coverage | Verified — cfg drift summary block at lines 184-203 (line 188: `if (pc.cfg_drift_tier1_count > 0 ...` ) | PASS |

**All EngineSharded.hpp line shifts trace to v5.10.2's helper extraction + REFUSE guard.** Plan's stale-claim audit at lines 261-278 declares "verified 2026-05-06 against HEAD `7f0b9a9`" — that is the PRE-v5.10.1 head. After v5.10.1 (+7) + v5.10.2 (+~110 net), citations 1399 and 2550 are off. Phase C citations need refreshing.

---

## CRITICAL corrections (must fix before coding ~10 min)

### 1. Phase C — EngineSharded.hpp line numbers stale (+68 / +113)

**Plan §C.1 says** `CoreFrameworks/EngineSharded.hpp:1399`. **Actual at HEAD `9d8a464`:** line **1467**.

```
1467:            // is_buyer_maker not available from the sharded fan_out yet; pass 0.
```

**Plan §C.2 says** `CoreFrameworks/EngineSharded.hpp:2550`. **Actual at HEAD `9d8a464`:** line **2663**.

```
2663:                        /*is_buyer_maker=*/0,
```

Update §C.1 and §C.2 with corrected line numbers before coding. Mechanical fix; fresh session would auto-correct on first grep but the plan should be self-consistent.

### 2. Phase B — populator location is `ShardedSnapshot.hpp`, not `EngineTUI.hpp`

**Plan §B.2 says** "DataStream/EngineTUI.hpp — find `TUI_CopySnapshotSharded` (or equivalent populator). Per audit, this is where ShardedSnapshot.hpp populates per-core fields."

**Actual:** `TUI_CopySnapshotSharded` is defined at `CoreFrameworks/ShardedSnapshot.hpp:39` (CODE_MAP.md says line 38). The existing `core_kill_tripped` populator line is at **`ShardedSnapshot.hpp:478`**:

```
478:        snap->per_core[i].core_kill_tripped    = state->cores[i].core_kill_tripped;
```

Phase B.2 populator block should land in `CoreFrameworks/ShardedSnapshot.hpp` right after line 478, not in `DataStream/EngineTUI.hpp`. Plan's parenthetical inside §B.2 ("Per audit, this is where ShardedSnapshot.hpp populates") nearly says this but the lead sentence misroutes. Update §B.2 to direct edits at `CoreFrameworks/ShardedSnapshot.hpp:~478` (after `core_kill_tripped` populator).

(Audit Finding #9 step 2 explicitly says "ShardedSnapshot.hpp populator: copy `state->cores[i].drift_history.{breached,kill_tripped}`" — plan's phrasing was looser.)

### 3. Phase B Open question #2 — RESOLVED

Plan §Phase B Open question #2: "Does PerCoreSnap participate in `SHARDED_SNAPSHOT_VERSION`? If yes, bump to 7."

**Resolution:** NO bump needed.

`grep -n "PerCoreSnap" CoreFrameworks/ShardedSnapshotPersist.hpp` returns NOTHING. PerCoreSnap is the TUI-side mirror struct (rebuilt every snapshot cycle from CoreContext); ShardedSnapshotPersist serializes CoreContext fields. Per `RECURRING_BUG_PATTERNS.md:206` and `INVARIANTS_MAP.md` row 27, `SHARDED_SNAPSHOT_VERSION` bumps are for CoreContext field changes, not PerCoreSnap.

PerCoreSnap field additions are zero-rebuild-cost forward-compatible by construction. **Update §"Open questions" #2 to read "RESOLVED — no bump needed; PerCoreSnap is in-process-only TUI buffer."**

This also implies §"Phase B B.1 Risk" wording "(check SHARDED_SNAPSHOT_VERSION semantics — if PerCoreSnap is part of the persisted snapshot, version bump per CLAUDE.md Decision 5)" can be simplified to "no version bump needed".

### 4. Phase A — TUIAnsi.hpp line 828 is actually 827

**Plan §A.3 says** `TUIAnsi.hpp:824, 828`. Actual loops are at lines **824 and 827** (not 828). Mechanical fix; both lines verified to use `< NUM_STRATEGIES`.

---

## Phase B field-name verification

Plan proposes 4 new PerCoreSnap fields:

```cpp
uint8_t  drift_breached;
uint8_t  drift_kill_tripped;
uint16_t drift_n_samples;
double   drift_avg_ic;
```

`grep "drift_breached\|drift_kill_tripped\|drift_n_samples\|drift_avg_ic"` across the repo returns **NO matches** outside the plan file. **No clashes.** Field types match audit Finding #9 step 1 recommendation.

Field placement after `core_kill_tripped` (line 1103) is appropriate — keeps the kill-related observability fields adjacent for at-a-glance reading.

---

## Cold-pickup completeness audit (10 fields per CLAUDE.local.md)

| # | Field | Verdict | Notes |
|---|-------|---------|-------|
| C.1 | Branch state | PASS | `experiment/per-core-sharding` named explicitly (line 4). |
| C.2 | Phase order | PASS | A (smallest, build-warning closure) → B (PerCoreSnap field add) → C (comment-only). Order correct. |
| C.3 | First concrete move | PASS | Each phase has Step 0 with file:line + before/after code shape. |
| C.4 | Function/macro names | YELLOW | `NUM_STRATEGIES`, `DriftHistory_*`, `RollingStats_Push`, `SharedBacktest_FromHistorical` — all verified. **`TUI_CopySnapshotSharded` cited as living in EngineTUI.hpp (§B.2 lead sentence) — actually in ShardedSnapshot.hpp.** Fresh session would discover at edit time. |
| C.5 | File:line refs for tests | YELLOW | Phase B test mentions `test_drift_history_snapshot_population` but doesn't cite where existing v5.10.0e drift tests live (`tests/controller_test.cpp:13186-13205`). Add this cite. |
| C.6 | Stale-claim audit | **YELLOW** | Plan has stale-claim section (lines 261-278) but it's verified against `7f0b9a9` (pre-v5.10.1). After v5.10.1.C (+7) + v5.10.2 (+~110 net), the EngineSharded.hpp citations have shifted. Plan must refresh. |
| C.7 | Effort vs LOC | PASS | ~110 LOC for ~3h is consistent (~37 LOC/hour for moderate-complexity boundary additions + comments). |
| C.8 | Source-audit refs | PASS | Cites parity audit with full path at line 6. |
| C.9 | Predecessor plans named | YELLOW | Line 305 says "Predecessors: v5.10.1 (production-caller closure), v5.10.2 (hot-swap parity)" — names without paths. Should reference `plans/2026-05-06-v5.10.1-production-caller-closure.md` and `plans/2026-05-06-v5.10.2-hot-swap-parity-hardening.md` per CLAUDE.local.md rule #9. Successor IS path-cited. |
| C.10 | Tag names locked | PASS | `pre-v5.10.3`, `v5.10.3.A`, `v5.10.3.B`, `v5.10.3.C`, `v5.10.3` (final). All unique, ordered, no clash with existing tag list. |

**Score: 7/10 PASS, 3/10 YELLOW.** All YELLOW items are CITATION ACCURACY (line shifts + function-location specificity + path completeness), not structural defects.

---

## Drift audit — train ↔ serve, write ↔ read

| Sub-category | Verdict | Notes |
|---|---|---|
| Feature drift | PASS | No FOREACH_FEATURE change. |
| Label drift | PASS | No label change. |
| Metric drift | PASS | No new metric. |
| Path drift | PASS | No path/symlink change. |
| Format drift | PASS | No serialization format change (PerCoreSnap NOT in snapshot persist). |
| Threshold drift | PASS | No new threshold cfg. |
| Tick-source drift | PASS | No tick source change. Phase C explicitly DOCUMENTS the existing is_buyer_maker carry-forward (Finding #5 deferred — parity preserved on both sides). |
| Build-flag drift | PASS | No new build flag. |
| Display drift | **HARDENING** | Phase A closes UB display divergence across `-O3`/`-Og`. Phase B adds distinct drift-kill diagnostic (was conflated with manual-kill / MTM-kill). |

**Net:** plan is drift-neutral at the parity surface, drift-HARDENING at the display surface, and explicitly DOCUMENTS one pre-existing carry-forward as deferred (Finding #5).

---

## Hidden scope detected

1. **EngineSharded.hpp citation refresh** (~5 min): plan's two C citations are off by +68 / +113. Re-grep before write.

2. **Populator file misroute** (~2 min documentation; behavior identical): Phase B.2 should explicitly direct to `CoreFrameworks/ShardedSnapshot.hpp:~478`, not `DataStream/EngineTUI.hpp`. The existing `core_kill_tripped` populator at line 478 is the right neighbor.

3. **CHANGELOG.md entry** (~5 min): Plan does not mention adding a `DOCS/CHANGELOG.md` row for v5.10.3. Operator's discipline (per v5.10.2 readiness) calls this out. Phase final tag should include CHANGELOG addition.

4. **Open question #2 resolution** (~2 min): Update plan to mark §"Open questions" #2 as RESOLVED (no SHARDED_SNAPSHOT_VERSION bump; PerCoreSnap is TUI-only).

5. **Predecessor path completeness** (~1 min): Lines 305-308 should add `plans/...` paths for v5.10.1 + v5.10.2 predecessor cites.

6. **Test entry-point cite** (~1 min): Phase B verification block should cite `tests/controller_test.cpp:13186-13205` as the v5.10.0e drift test precedent.

Total hidden scope: ~16 min — well within plan's ~30m final-tag budget.

---

## Hardening checks

| Check | Verdict | Notes |
|---|---|---|
| Atomic file writes | N/A | No file writes. |
| Locale pinning | N/A | No string-formatting hash. |
| GUI render-thread blocking I/O | PASS | Panel render in §B.3 is plain ImGui; no I/O. |
| Failure telemetry path | PASS | Drift state newly distinguishable in TUI; pre-existing core_kill_tripped log unchanged. |
| Resource cleanup | PASS | No new allocations. |
| Cancellation semantics | N/A | No threads added. |
| Cross-platform | PASS | No new POSIX-only call. |

---

## Risks specifically called out by user

### Risk 1: v5.10.2 line-shift caveat — CONFIRMED

User predicted EngineSharded.hpp citations 1399 → ~1466 and 2550 → ~2617. Actual at HEAD `9d8a464`: 1399 → **1467** and 2550 → **2663**. The 2663 vs predicted 2617 is +46 further than predicted because v5.10.2 also added the Phase B REFUSE guard around the swap reload site (~lines 2480-2520 region). **Plan's two C citations need refresh.**

### Risk 2: Field name verification — PASS

The 4 proposed PerCoreSnap field names (`drift_breached`, `drift_kill_tripped`, `drift_n_samples`, `drift_avg_ic`) do not clash with any existing identifier in the repo. Safe to add.

### Risk 3: KNOWN_ISSUES.md file existence — VERIFIED EXISTS

`DOCS/KNOWN_ISSUES.md` exists (last updated 2026-05-06 post-v5.10.0a.next.2). Phase C.4 should APPEND a new section, not CREATE the file. Plan §C.4 line 222 says "if not, this becomes a new file" — that branch will not trigger; the entry is an append.

### Risk 4: PerCoreSnap snapshot version bump — RESOLVED NO

Verified PerCoreSnap is TUI-side mirror only. `grep "PerCoreSnap" ShardedSnapshotPersist.hpp` returns nothing. SHARDED_SNAPSHOT_VERSION applies to CoreContext fields. Plan §"Open questions" #2 can be closed at write-time as RESOLVED-NO.

### Risk 5: Hot path purity — VERIFIED CLEAN

`grep "drift_history\." CoreFrameworks/ExecutionCore.hpp CoreFrameworks/GateParameters.hpp` returns nothing. `BG_Evaluate`/`SG_Evaluate`/`ExecutionCore_Tick` (ExecutionCore.hpp:227, 280, 300) are all untouched by this plan. `drift_history` is read only on the slow path (snapshot populator + drift detection at ControllerEventLoop.hpp:1196-1227). **Hot path UNTOUCHED.**

### Risk 6: Phase A AUTO bin (idx=5) zero-init semantics — ACCEPTABLE

Plan recommends zero-init the AUTO sentinel slot. Population loop iterates real strategies 0..NUM_STRATEGIES_REAL-1; idx=NUM_STRATEGIES_REAL=5 = STRATEGY_AUTO is dispatcher-side, not a real strategy. Zero-init means TUI shows 0/0/0 for AUTO column (signals "unspecified"). Acceptable for v5.10.3.A. Aggregate stats across all real strategies = v5.11.X polish (plan-deferred).

---

## Recommendations

### Must fix before coding (~15 min)

1. **Refresh EngineSharded.hpp citations:**
   - §C.1: `1399` → `1467`
   - §C.2: `2550` → `2663`
   - Update plan §"Stale-claim audit" rows for the same two cells

2. **Re-route Phase B.2 populator location:** `DataStream/EngineTUI.hpp` → `CoreFrameworks/ShardedSnapshot.hpp:~478` (after the existing `core_kill_tripped` populator).

3. **Resolve Open question #2 inline:** Add "RESOLVED — no SHARDED_SNAPSHOT_VERSION bump; PerCoreSnap is TUI-side mirror only (verified `grep PerCoreSnap ShardedSnapshotPersist.hpp` returns nothing)."

4. **Refresh TUIAnsi.hpp citation:** `824, 828` → `824, 827` (mechanical).

5. **Add CHANGELOG entry to final-tag composite verification list** (Phase v5.10.3 final tag).

### Worth fixing during coding

6. **Cite v5.10.0e drift test entry point** (`tests/controller_test.cpp:13186`) in plan §B.Verification.

7. **Add `plans/...` paths for predecessor plans** at lines 305-306 to satisfy CLAUDE.local.md rule #9.

8. **Update §"Stale-claim audit" header** from "verified against HEAD `7f0b9a9`" to "verified against HEAD `9d8a464`" once items 1-2 land.

### Acceptable risk (don't block)

9. Phase B test fakery shape (use the v5.10.0e drift test pattern from controller_test.cpp:13186-13205; refine at test-write time).
10. Phase A AUTO bin zero-init is correct for v5.10.3.A (aggregate-across-strategies polish deferred to v5.11.X).
11. Phase C is_buyer_maker plumb-through deferred is correct given audit's severity rationale (parity preserved, feature dead-but-symmetric).

---

## Map-update suggestions (post-coding)

- `tools/gen_code_map.sh` — re-run to refresh PerCoreSnap field count (no new functions added).
- `INVARIANTS_MAP.md` — Phase A's `static_assert(sizeof(strat_stats) / sizeof(strat_stats[0]) == NUM_STRATEGIES)` is itself the new invariant; consider adding a row "TUI snap arrays sized by canonical N count macros" after coding.

---

## Verdict: YELLOW

**YELLOW — fix the must-fix items above first (~15 min), then GREEN to start coding.**

Plan is structurally sound: correct architecture (3 narrow-scope phases), correct phase order (smallest → comment-only last), hot path untouched (verified), audit findings cleanly mapped (Finding #8 → Phase A; Finding #9 → Phase B; Finding #5/#15 → Phase C; Finding #11 → addendum to Phase C.4). Field names verified non-clashing. Phase B SHARDED_SNAPSHOT_VERSION question RESOLVED-NO before coding starts. Phase A is a near-trivial 2-LOC source change with self-documenting `static_assert` invariant. Phase B is the meatiest (4 fields + populator + panel render + 1 test) but the v5.9.0b precedent (`ml_model_load_failed`) gives the exact shape. Phase C is comment-only with one append to existing KNOWN_ISSUES.md.

Risk profile is LOW: Phase A is a fix-by-construction (no behavior change for non-AUTO strategies; AUTO slot was reading garbage, now reads zero); Phase B's populator addition is additive; Phase C touches no executable code. Pre-tag rollback anchor (`pre-v5.10.3`) provides clean recovery.

Once the 15 min of citation refreshes land, this is the CLEANEST of the three v5.10 close-out ships and should land in the planned ~3h. After v5.10.3 ships and `/parity-check` is re-run, the verdict should flip to GREEN at v5.10-final close, unblocking the v5.11 epic.

**Top recommendation:** Spend 15 minutes before opening any source file to (a) refresh the two EngineSharded.hpp citations to 1467 and 2663, (b) re-route Phase B.2 to ShardedSnapshot.hpp:~478, and (c) mark Open question #2 as RESOLVED-NO inline — then start coding Phase A.
