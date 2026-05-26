---
type: audit-report
audit: /parity-check
ship_tag: v5.15.5.F.4d.1.B.4
plan_path: plans/v5.15-live-readiness/subplans/2026-05-24-v5.15.5.F.4d.1.B.4-train-serve-execution-layer-parity.md
plan_version_audited: v1.7.4 LOCKED + planned v1.7.5 SUBSTANTIVE amendment (per decision-log D15-D18 + C25-C30 + F13-F19)
decision_log_path: plans/v5.15-live-readiness/decision-logs/2026-05-24-v5.15.5.F.4d.1.B.4-v1.7.4.md
engine_head: e0acb65 (WIP-11; 11 commits ahead of origin/feat/v5.15-live-readiness per per-ship-close-push workflow)
workspace_head: d3ea490
date: 2026-05-26 (PM)
fired_by: orchestrator (pre-v1.7.5-amendment audit gate)
audit_tier: HIGH-RISK (planned v1.7.5 scope includes wire-format-cohort surface deletion + cross-cutting train↔serve helper migration)
verdict: YELLOW
sister_audits_to_fire_alongside: /precoding-audit-gate (SHAPE), /blindspot-scan (M4 implementation-detail), /bug-check (Class catalog)
---

# /parity-check report — v5.15.5.F.4d.1.B.4 v1.7.5 pre-amendment gate

## Plan summary

- Engine HEAD `e0acb65` (WIP-11 LIVE slow-path migration LANDED 2026-05-26)
- Tests preserved 3217/0; B-Plus exit 0
- Phase B body coding COMPLETE; Phase C Steps C.1+C.2+C.3 LANDED
- Plan body v1.7.4 LOCKED; **v1.7.5 SUBSTANTIVE amendment scope** captured in decision-log v1.7.4 → v1.7.5 transition section (D15-D18 + C25-C30 + F13-F19)
- This audit fires BEFORE v1.7.5 amendment is drafted — purpose is to identify gaps + risks the amendment must absorb
- Cross-check baseline: post-v5.9.4a protections (FEATURE_REGISTRY_HASH + scaler binding + STAMP_CFG_AUTOPOPULATE + cross-binary handshake + v5.10+ stamp body extensions)

## Verdict: YELLOW

Planned v1.7.5 scope is **architecturally sound** for train↔serve parity preservation. The B-full SHARDED `engine_arch=centralized` deprecation does NOT touch any stamp-bound cfg fields, HMAC chain inputs, scaler sidecar, or feature pack — so wire-format byte preservation is safe by-construction (verified at A-level details below). Phase C.4 BACKTEST migration symmetry validates the N-4 REVERT logic against actual LIVE-side surface — KEEP `:354` UpdateEmaPriceAllCores + `:367` KillSwitchEvaluate cite real LIVE producer-thread sister sites at `:1405` + `:1676` (NOT inside per_core_slow lambda extract :2834-3101). PARITY-031 ordering closure is execute-after-write race-safe per existing single-threaded BACKTEST tick callback dispatch.

YELLOW (not GREEN) because:

1. **PARITY ledger drift** — PARITY-031 entry at `DOCS/PARITY_ISSUES.md:1296+` still cites pre-shift line numbers (`:541-548` / `:612`). Actual at HEAD `e0acb65` is `:423` / `:489` / `:494`. Ledger entry not yet updated.
2. **PARITY-032 NOT IN LEDGER** — Decision-log + plan body reference PARITY-032 as opened+closed at this ship, but `DOCS/PARITY_ISSUES.md` has no PARITY-032 entry. Must be auto-written at v1.7.5 amendment OR before ship close per the auto-write contract.
3. **`engine_arch` test surface** — 2 controller_test.cpp test cases will need update (`v5.0.4: topology engine_arch round-trips` at :8732 + HAS_SIDE_EFFECT count test at :1735 will lose the `engine_arch` row). Not parity-axis but visible to ship close.
4. **Pre-existing PARITY ledger entries 026-030 still status OPEN** — confirm by-construction closures land + ledger updates apply at Phase D ship close (PARITY-026 already CLOSED via predecessor hotfix; 027-031 close via this ship; 032 opens+closes via this ship).

No CRITICAL findings. Recommend v1.7.5 amendment scope expansion to include PARITY ledger updates + PARITY-032 entry creation (auto-write contract obligation).

---

## Findings by severity

### CRITICAL

None.

### HIGH

#### H-1 — PARITY-031 ledger entry cites stale pre-shift line numbers

- **File:** `DOCS/PARITY_ISSUES.md:1296-1318`
- **Stale cite:** Site(s) row references `BacktestSharded.hpp:541-548` (field) + `:612` (collapse-N-to-1 read)
- **Actual at HEAD `e0acb65`:** field at `:423`; write at `:489`; read at `:494`
- **Class:** Documentation drift — does NOT cause runtime parity divergence but mis-points future audits to non-existent line surfaces
- **Recommended fix:** v1.7.5 amendment OR Phase D ship close postmortem auto-writes corrected line numbers to PARITY-031 entry per `/parity-check` skill auto-write contract. Also update plan body Step C.4.5 site enumeration (decision-log F13 already documents the correction).
- **Effort:** 5 min mechanical
- **Cross-ref:** decision-log F13 "WIP-9 C.1+C.2 boot migration's -380 LOC EngineSharded.hpp shift made plan body file:line cites stale at 3 canonical surfaces" — PARITY-031 was one of the 3 line-shift surfaces.
- **Cross-ref existing protection:** GAP (no automated PARITY ledger line-anchor verification today; B-Plus v0.3 line-anchor mode catches plan-body drift but not ledger drift — extend per `feedback_no_defer_for_effort`)

#### H-2 — PARITY-032 has no entry in PARITY ledger (auto-write contract obligation)

- **File:** `DOCS/PARITY_ISSUES.md` (PARITY-031 entry ends at :1318; no PARITY-032 follows)
- **Stale cite source:** Plan body cites PARITY-032 as "NEW opened+closed at this ship" (line 379 acceptance criteria + line 513 Decision E table + line 599 Class 18 mirror evidence). Decision-log § Cycle close summary references PARITY-032 closure via D1-B fold-in.
- **Class:** Auto-write contract violation per skill spec `/parity-check` § "Auto-write contract" — any new finding MUST be added to PARITY_ISSUES.md by the audit agent BEFORE plan body lock
- **Symptom:** `DOCS/PARITY_ISSUES.md` does NOT include PARITY-032; only mention is plan body + decision-log. Future PARITY-NNN allocations may collide.
- **Recommended fix:** v1.7.5 amendment OR Phase D ship close PARITY ledger write — append standard format block (Found / Severity / Class / Site / Symptom / Root cause / Fix path / Target ship / Status: OPENED + CLOSED at v5.15.5.F.4d.1.B.4 via D1-B FOREACH_SLOW_PATH_GATE row-add) under "## Issues" section
- **Effort:** 10 min mechanical (template + content from plan body's existing PARITY-032 rationale)
- **Cross-ref existing protection:** GAP (process discipline gap; same shape as H-1)

### MEDIUM

#### M-1 — Phase C.4 BACKTEST migration's KEEP `:354`/`:367` decision relies on N-4 REVERT (v1.7.3 amendment) — verified safe at LIVE HEAD

- **Files:** `CoreFrameworks/ShardedBacktestDriver.hpp:354` (UpdateEmaPriceAllCores) + `:367` (KillSwitchEvaluate)
- **Decision-log claim:** "KEEP `:354` UpdateEmaPriceAllCores + `:367` KillSwitchEvaluate per N-4 REVERT" because these sister LIVE-side calls fire on PRODUCER THREAD (not inside per_core_slow lambda body extract :2834-3101 that becomes EngineCommon_SlowPathCycleOneCore)
- **Verified at HEAD `e0acb65`:**
  - LIVE `EventLoop_UpdateEmaPriceAllCores` at `EngineSharded.hpp:1405` — PRODUCER THREAD; OUTSIDE per_core_slow lambda extract (lambda starts ~:2834). ✓ Reasoning HOLDS.
  - LIVE `EventLoop_KillSwitchEvaluate` at `EngineSharded.hpp:1676` — PRODUCER THREAD (centralized-arch path); OUTSIDE per_core_slow lambda extract. ✓ Reasoning HOLDS.
- **Symmetry verification:** BACKTEST has no producer thread — these 2 calls in BACKTEST tick-callback PRESERVE the equivalent semantic. Deleting them would silently DROP ema_price replication + kill_switch evaluation in BACKTEST path → REVERSES PARITY-026 closure intent (`feedback_enumerate_consumers_before_registry_row_deletion` consumer-side enumeration).
- **Recommended fix:** None — N-4 REVERT was the right call. v1.7.5 plan body amendment should preserve the KEEP rationale explicitly (decision-log F19 captures it; plan body Step C.4 line 1078-1085 has the rationale embedded but is dense; consider promoting to a callout box at v1.7.5 amendment for future-reader clarity).
- **Effort:** None — verifies as-planned
- **Cross-ref existing protection:** ALREADY-PROTECTED (`feedback_enumerate_consumers_before_registry_row_deletion` triggered at v1.7.3 N-4)

#### M-2 — Phase C.4 BACKTEST migration's DELETE site `:378-383` removes 3 sister wrappers' LAST caller → cohort delete of wrappers at WIP-13

- **Files:**
  - BACKTEST callers (this ship deletes): `ShardedBacktestDriver.hpp:378` EventLoop_TimeExit + `:380` EventLoop_TrailingSLRatchet + `:383` EventLoop_BreakevenOnProfit
  - LIVE callers (B-full WIP-13 deletes): `EngineSharded.hpp:1718-1744` block contains the 3 wrappers behind `engine_arch != ENGINE_ARCH_PER_CORE_SLOW`
  - Wrapper definitions (cohort delete at WIP-13): `ControllerEventLoop.hpp:3435-3454` EventLoop_TimeExit + `:3722-3733` EventLoop_TrailingSLRatchet + `:3796-3804` EventLoop_BreakevenOnProfit
- **Class:** Class 18 mirror cohort discipline — if WIP-13 deletes LIVE callers but not the 3 wrapper definitions, wrappers become dead code; if WIP-12 deletes BACKTEST callers but B-full WIP-13 is deferred, LIVE-side wrappers stay live but BACKTEST is migrated → MID-STATE Class 18 mirror until WIP-13
- **Symptom risk:** Between WIP-12 (C.4) commit and WIP-13 (B-full) commit, LIVE-side centralized-arch code path still calls the wrappers but BACKTEST doesn't. If a rollback to WIP-12-only state happens, parity is broken until WIP-13 lands.
- **Recommended fix:** v1.7.5 amendment captures the F17 cohort-delete rationale explicitly — all 3 wrappers' last callers vanish across WIP-12 (BACKTEST) + WIP-13 (LIVE centralized). 3-WIP cadence per D17 is correct sequencing: WIP-12 first delete BACKTEST trio + ADD AllCores call; WIP-13 next delete LIVE centralized branches + COHORT delete 3 wrapper definitions. PARITY between WIP-12 commit and WIP-13 commit is technically YELLOW but acceptable per rollback-anchor-per-substantial-change discipline.
- **Effort:** Plan body must explicitly note the WIP-12 → WIP-13 mid-state YELLOW window + rollback discipline ensures parity even in mid-state.
- **Cross-ref existing protection:** ALREADY-PROTECTED (decision-log F17 + D17 capture the cohort + cadence)

#### M-3 — PARITY-031 closure ordering: ctx.current_regime read happens AFTER SlowPathCycleAllCores callback executes (race-free)

- **Files:** `Backtest/BacktestSharded.hpp:489` (Regime_Classify write site to delete) + `:494` (collapse-N-to-1 read to delete + replace)
- **Plan body claim (Step C.4.5):** ADD `ctx.current_regime = state.cores[BACKTEST_REGIME_SAMPLE_CORE].regime_state.current_regime;` after SlowPathCycleAllCores callback
- **Ordering analysis:** BACKTEST tick callback dispatch is SINGLE-THREADED (no producer/drainer/per-core-slow thread split; backtest synchronously calls `on_slow_path` hook AFTER drv work). Per ShardedBacktestDriver.hpp:391-394: `if (drv->on_slow_path) drv->on_slow_path(drv->hook_ctx, drv, tick, tick_index);` fires AFTER lines :346-388 (which will include the new `EngineCommon_SlowPathCycleAllCores` call). State.cores[].regime_state population happens BEFORE the on_slow_path callback fires.
- **Verdict:** Race-free by-construction. Feature-collector callback reads from state.cores[BACKTEST_REGIME_SAMPLE_CORE].regime_state AFTER SlowPathCycleAllCores has populated state.cores[c].regime_state for all c. ✓
- **Recommended fix:** v1.7.5 amendment Step C.4.5 explicitly documents this ordering analysis (per plan body's existing HIGH-3 verification call-out at line 1099-1105 — adequate but could be promoted to top-level of Step C.4.5 for amendment clarity).
- **Effort:** None — race-safe by-construction
- **Cross-ref existing protection:** ALREADY-PROTECTED (single-threaded BACKTEST tick callback dispatch; plan body Step C.4.5 HIGH-3 verification gate)

#### M-4 — `engine_arch` cfg field deletion impacts 2 controller_test.cpp tests (HAS_SIDE_EFFECT count + TUISnapshot topology round-trip)

- **Files:**
  - `tests/controller_test.cpp:1735` — HAS_SIDE_EFFECT count test asserts `≥4 bits (reconcile_mode/engine_mode/engine_arch/model_verify_strict/thompson_rng_seed/bandit_algorithm/risk_degradation_curve/trading_mode)`. With `engine_arch` row deleted, test asserts ≥4 of N-1 remaining rows — passes as long as ≥4 other rows have HAS_SIDE_EFFECT.
  - `tests/controller_test.cpp:8721-8775` — TUI_PopulateTopology round-trip test passes `/*engine_arch*/ 1` + asserts `snap.engine_arch == 1` round-trips. With TUISnapshot.engine_arch field deleted, this test needs deletion or rewrite to match new TUISnapshot shape.
- **Class:** Test surface drift through cfg field deletion (D18 full surface deletion includes TUISnapshot.engine_arch field per decision-log F18)
- **Symptom:** Build will fail at WIP-13 unless tests updated alongside surface deletion.
- **Recommended fix:** v1.7.5 plan body amendment Step C.4 (or new Step C.4.7 for B-full) enumerates the 2 controller_test sites to update + rewrite/delete pattern. Test :8721-8775 is the trickier one — either delete the whole test block (`v5.0.4: Topology field stability`) since engine_arch is removed, OR remove just the engine_arch assertion + update TUI_PopulateTopology call signature. Decision-log C28 mentions "+ DELETE GUI DashboardPanels.hpp gating" but does NOT mention test surface — gap to fix in v1.7.5 amendment scope.
- **Effort:** 10-15 min mechanical (rewrite test block OR delete + verify test count adjusts cleanly to 3217-N)
- **Cross-ref existing protection:** GAP (B-Plus CI tool catches symbol references in plan body but doesn't auto-detect test sites needing update)

#### M-5 — Plan body cites `EngineSharded.hpp:1718-1744` per /trace-deps F13 correction; D17/C28 enumerate 8 branches but plan body still cites OLD :1870-1954 at v1.7.4 line 1084

- **Files:**
  - Plan body Step C.4 line 1084: cites `EngineSharded.hpp:1870-1954` (v1.7.3 N-8 line range correction)
  - Decision-log F13: "WIP-9 C.1+C.2 boot migration's -380 LOC EngineSharded.hpp shift made plan body file:line cites stale"
  - Actual at HEAD: 8 branches at `:1438/:1453/:1625/:1637/:1660/:1695/:1718/+2484 boot-spawn-gate` per decision-log C28
- **Class:** Plan body line-range drift through engine HEAD shift (parallel to F13 PARITY-031 + Step B.3 lambda body cites)
- **Symptom:** Plan body v1.7.4 references different line range than actual `engine_arch != PER_CORE_SLOW` branch sites at HEAD `e0acb65`
- **Recommended fix:** v1.7.5 SUBSTANTIVE amendment per decision-log C25 should explicitly enumerate all 8 branch sites + boot-spawn-gate at `:2484`. Current v1.7.4 cite at line 1084 (`:1870-1954`) was a partial cite of only one block.
- **Effort:** Mechanical — re-enumerate from current `grep -n "engine_arch != ENGINE_ARCH_PER_CORE_SLOW" CoreFrameworks/EngineSharded.hpp`
- **Cross-ref existing protection:** ALREADY-PROTECTED at line-detection layer (B-Plus v0.3 line-anchor mode landed at WIP-10 catches this class going forward) — v1.7.4 amendment was before B-Plus v0.3 was fully validated against this file:line cite

### LOW

#### L-1 — Plan body v1.7.4 frontmatter status field references "draft v1.7.4" — needs bump to v1.7.5 at amendment

- **File:** `plans/v5.15-live-readiness/subplans/2026-05-24-v5.15.5.F.4d.1.B.4-train-serve-execution-layer-parity.md` frontmatter `status: draft v1.7.4 …`
- **Recommended fix:** v1.7.5 amendment updates `status: v1.7.5 SUBSTANTIVE — B-full SHARDED deprecation IN-SCOPE + Phase C.4 BACKTEST migration line-anchor corrections + PARITY-031 ordering verification`
- **Effort:** 1 min mechanical

#### L-2 — Plan body Step C.4.5 line 1108 cites `:541-548` + `:612` — stale per same line-shift class as M-5

- **File:** Plan body line 1108: "Consumer enumeration at HEAD `64e7101`: `:541-548` — field allocation …"
- **Note:** This is an "at HEAD `64e7101`" historical cite (the v1.5 enumeration baseline), NOT a runtime claim. Plan body could keep the historical reference + add a "(at HEAD `e0acb65` post-C.1: :423 / :489 / :494)" addendum per decision-log F13.
- **Recommended fix:** v1.7.5 amendment adds the addendum line + cross-refs to F13 closure.
- **Effort:** 2 min mechanical

#### L-3 — Phase D ship close TECH_DEBT auto-write entries do NOT yet enumerate the B-full SHARDED deprecation cleanup

- **File:** Plan body line 1276-1287 TECH_DEBT auto-write table
- **Recommended fix:** v1.7.5 amendment adds row "NEW v1.7.5 — `engine_arch=centralized` SHARDED mode FULL-SURFACE-DELETION at WIP-13" with rationale (D16 + D18 operator pref: "backwards compat not a default concern"). Could also amend `feedback_backwards_compat_not_default_concern.md` reference at memory file.
- **Effort:** 5 min mechanical

### DOCUMENT-ONLY

#### D-1 — Wire-format byte preservation through D18 deletion is SAFE by-construction (no stamp body field deletion)

- **Verification:** `engine_arch` row at `CoreFrameworks/CfgFieldRegistry.hpp:396` has metadata `HAS_SIDE_EFFECT | IS_BOOT_ONLY` ONLY — NOT `STAMP_BOUND` / `STAMP_BOUND_CFG_DERIVED`.
- **Cross-checked:** `grep "engine_arch" MemHeaders/CfgGateRegistry.hpp` → no hits. `engine_arch` is not in `FOREACH_STAMP_BOUND_CFG_DERIVED` filter. `engine_arch` does not appear in `StampInferenceCfgInputs` struct fields. HMAC chain inputs preserved across D18 deletion.
- **Verdict:** PASS — Section E (Stamp body schema parity) + Section G (Cross-binary handshake) UNTOUCHED by D18.
- **Document-only:** Future-Caramel reading this audit confirms the safety analysis.

---

## Cross-cutting concerns

### PARITY ledger drift (H-1 + H-2 + L-2) — single fix closes all three

A single v1.7.5 amendment OR Phase D ship close PARITY ledger amendment fixes:
- H-1: PARITY-031 line numbers `:541-548`/`:612` → `:423`/`:489`/`:494`
- H-2: Add PARITY-032 entry (OPENED + CLOSED at this ship via D1-B FOREACH_SLOW_PATH_GATE row-add)
- L-2: Plan body Step C.4.5 line 1108 historical-cite addendum

Recommended scope: Add to Phase D ship close TECH_DEBT auto-write checklist OR include in v1.7.5 amendment as explicit Step D.5b "PARITY ledger updates + new PARITY-032 entry".

### Test surface impact (M-4) — single test rewrite covers both sites

Both controller_test.cpp tests affected by D18 surface deletion are co-located in test domain (TUISnapshot topology + cfg field metadata aggregates). One mechanical edit pass covers both. Decision-log C28 should explicitly include "+ DELETE `controller_test.cpp:1735` HAS_SIDE_EFFECT bit count assertion update + DELETE `controller_test.cpp:8721-8775` TUI_PopulateTopology engine_arch round-trip test block" alongside the GUI gating deletion.

---

## Behavior matrix (verify train and serve agree for default cfg)

| Scenario | Trainer view (BACKTEST) | Engine view (LIVE) | Identical? |
|---|---|---|---|
| BNB discount applied (pay_fees_in_bnb=1) | Via EngineCommon_ApplyBnbDiscount before BootGlobal (PARITY-030 closed) | Via EngineCommon_ApplyBnbDiscount before BootGlobal | ✓ (closed via Step C.1+C.2) |
| ML zoo init (use_exit_model=1) | Via EngineCommon_BootPerCore ML branch (PARITY-027 closed) | Via EngineCommon_BootPerCore ML branch | ✓ (closed via Step C.1+C.2) |
| ConfidenceScorer + RollingTurnover init | Via EngineCommon_BootPerCore (PARITY-028 closed) | Via EngineCommon_BootPerCore | ✓ (closed via Step C.1+C.2) |
| Strategy_InitPerCore (stateful strategies) | Via EngineCommon_BootPerCore (PARITY-029 closed) | Via EngineCommon_BootPerCore | ✓ (closed via Step C.1+C.2) |
| KillSwitch_ConfigureKillSwitch | Via EngineCommon_BootGlobal (PARITY-026 closed at predecessor hotfix) | Via EngineCommon_BootGlobal | ✓ (closed at predecessor hotfix; preserved via helper) |
| Per-core regime classification (per_core regime_hysteresis overrides) | After v1.7.5 WIP-14 C.4.5: ctx.current_regime from state.cores[BACKTEST_REGIME_SAMPLE_CORE].regime_state (PARITY-031 closed) | Per-core via state.cores[c].regime_state | ✓ (closes at WIP-14 + named constant rationale per Decision F) |
| breakeven_on_profit lifecycle (MASK_LIFECYCLE_CFG_BREAKEVEN_ON_PROFIT cfg flag SET) | Via EngineCommon_SlowPathCycleOneCore with D1-B BREAKEVEN_ON_PROFIT cached gate (PARITY-032 closed at WIP-11) | Via EngineCommon_SlowPathCycleOneCore with D1-B cached gate | ✓ (closed at WIP-11 LIVE; will close at WIP-12 BACKTEST when AllCores call lands) |
| ema_price replication per tick | Via BACKTEST callback :354 EventLoop_UpdateEmaPriceAllCores (KEEP per N-4) | Via LIVE producer-thread :1405 EventLoop_UpdateEmaPriceAllCores | ✓ (symmetric per N-4 REVERT) |
| KillSwitch evaluation per tick | Via BACKTEST callback :367 EventLoop_KillSwitchEvaluate (KEEP per N-4) | Via LIVE producer-thread :1676 EventLoop_KillSwitchEvaluate | ✓ (symmetric per N-4 REVERT) |
| Stamp body engine_version | Unchanged by D18 (no STAMP_BOUND impact) | Unchanged by D18 | ✓ (D-1 verification) |
| Wire-format byte preservation for HMAC-signed bodies | Unchanged by D18 (engine_arch not in any FOREACH_STAMP_BOUND_* filter) | Unchanged by D18 | ✓ (D-1 verification) |

All 11 behavior axes converge to ✓ post-v1.7.5 ship close. No CRITICAL drift surfaces identified.

---

## Suggested ship sequence (v1.7.5 amendment + WIP-12 → WIP-14)

1. **v1.7.5 amendment** (next session pre-WIP-12 per C25 + C26):
   - Update plan body status frontmatter to v1.7.5 SUBSTANTIVE
   - Absorb decision-log D15-D18 + C25-C30 + F13-F19 into plan body text
   - Add explicit B-full deletion enumeration (8 LIVE branches + 3 sister wrappers + cfg field + parser + 2 constants + TUISnapshot field + GUI gating + 2 test cases)
   - Add PARITY-032 ledger auto-write step to Phase D
   - Add PARITY-031 ledger line-number correction step to Phase D
   - Re-verify line ranges via grep at amendment time + cite via decision-log F-finding IDs
   - Re-fire `/precoding-audit-gate` + `/blindspot-scan` + `/bug-check` at v1.7.5 amendment lock (per audit_tier HIGH-RISK)
2. **WIP-12 BACKTEST migration** (per C27):
   - ADD `EngineCommon_SlowPathCycleAllCores(...)` call in ShardedBacktestDriver.hpp slow-path-callback
   - DELETE `:346` UpdateRollingStateAllCores + `:356-364` RebuildAllParameters_PerCore + `:366` PushParameters + `:378-383` TimeExit/TrailingSLRatchet/BreakevenOnProfit trio
   - KEEP `:354` UpdateEmaPriceAllCores + `:367` KillSwitchEvaluate (N-4 REVERT)
   - Verify parity_harness regression sweep
3. **WIP-13 B-full SHARDED deprecation** (per C28 + D18):
   - DELETE 8 `engine_arch != PER_CORE_SLOW` branches in EngineSharded.hpp at `:1438/:1453/:1625/:1637/:1660/:1695/:1718` (each unconditionalize body)
   - DELETE boot-spawn gate at `:2484` (always-spawn per_core_slow threads now)
   - COHORT DELETE 3 sister wrappers at ControllerEventLoop.hpp:3435/3722/3796 (EventLoop_TimeExit + EventLoop_TrailingSLRatchet + EventLoop_BreakevenOnProfit) per F17 Class 18 prevention
   - DELETE cfg field `engine_arch` from ControllerConfig + parser entry + `ENGINE_ARCH_CENTRALIZED` / `ENGINE_ARCH_PER_CORE_SLOW` constants + TUISnapshot.engine_arch field + GUI DashboardPanels gating
   - UPDATE/DELETE 2 controller_test.cpp test cases (`:1735` HAS_SIDE_EFFECT count + `:8721-8775` topology round-trip)
4. **WIP-14 PARITY-031 closure** (per C29):
   - DELETE `fc_ctx.regime_state` field at `BacktestSharded.hpp:423`
   - DELETE write at `:489`
   - DELETE read at `:494` + REPLACE with `ctx.current_regime = state.cores[BACKTEST_REGIME_SAMPLE_CORE].regime_state.current_regime;`
   - Verify single-threaded BACKTEST tick callback ordering (race-safe per M-3)
5. **Phase D ship close** (per C30):
   - Version.hpp bump + GPG-signed tag + postmortem + sync-workspace
   - PARITY ledger updates (H-1 + H-2 + L-2)
   - TECH_DEBT auto-write (L-3)
   - Class 14/18 recurrence_count amendments

---

## NOT a bug (verified-safe items)

- **Wire-format byte preservation across D18 deletion** — `engine_arch` has no STAMP_BOUND metadata, no stamp body field, no scaler binding, no FOREACH_STAMP_BOUND_CFG_DERIVED row, no HMAC chain input. Verified at `CoreFrameworks/CfgFieldRegistry.hpp:396` + `MemHeaders/CfgGateRegistry.hpp` + `Strategies/StampBoundCfgRegistry.hpp` (last verified non-existent). Section E + Section G safe by-construction.
- **N-4 REVERT logic** — KEEP `:354` UpdateEmaPriceAllCores + `:367` KillSwitchEvaluate at BACKTEST verified safe at LIVE HEAD `e0acb65` (sister LIVE-side calls at producer thread `:1405` + `:1676`; OUTSIDE per_core_slow lambda extract `:2834-3101`). Deletion would have REVERSED PARITY-026 closure.
- **PARITY-031 ordering closure** — BACKTEST tick callback dispatch single-threaded; SlowPathCycleAllCores populates state.cores[c].regime_state BEFORE on_slow_path callback fires. Read at line 494 after AllCores call is race-free by-construction.
- **B-Plus CI tool coverage for v1.7.5** — Currently exits 0 against v1.7.4 plan body for symbol existence; line-anchor mode (v0.3 landed at WIP-10) reports 14 drifts + 6 notfounds (informational; canonical surfaces folded inline at WIP-11). v1.7.5 amendment will need re-run after line range updates.

---

## Map-update suggestions (post-audit)

- **DOCS/PARITY_ISSUES.md** auto-write: PARITY-032 new entry + PARITY-031 line-number correction (per H-1 + H-2 auto-write contract)
- **plans/v5.15-live-readiness/subplans/2026-05-24-v5.15.5.F.4d.1.B.4-train-serve-execution-layer-parity.md** SUBSTANTIVE amendment per decision-log D15-D18 + C25-C30 (status + Steps C.4 + C.4.5 + new B-full Step or appendix + Phase D)
- **DOCS/TECH_DEBT.md** auto-write (L-3): B-full deprecation cleanup row at WIP-13 cycle
- **tests/controller_test.cpp** edit pass (M-4): 2 test sites
- **CLAUDE.local.md** going-forward rules: `feedback_backwards_compat_not_default_concern` row added at v1.7.4 + add explicit cross-ref to D18 worked example

---

## Verdict summary

**YELLOW** — planned v1.7.5 scope is architecturally sound + train↔serve parity preserves by-construction across all 7 PARITY closures (026-032). The 5 PARITY findings:

| ID | Status at HEAD | Closure path |
|---|---|---|
| PARITY-026 | CLOSED (predecessor v5.15.5.F.4d.1.B.2.h1-killswitch-fix hotfix) | Preserved via EngineCommon_BootGlobal at WIP-9 |
| PARITY-027 | CLOSED by-construction at WIP-9 | Via EngineCommon_BootPerCore ML branch in both LIVE+BACKTEST callers |
| PARITY-028 | CLOSED by-construction at WIP-9 | ConfidenceScorer_BindCompositeCfg + RollingTurnover_Init inside EngineCommon_BootPerCore |
| PARITY-029 | CLOSED by-construction at WIP-9 | Strategy_InitPerCore inside EngineCommon_BootPerCore |
| PARITY-030 | CLOSED by-construction at WIP-9 | EngineCommon_ApplyBnbDiscount called in both LIVE+BACKTEST |
| PARITY-031 | PENDING at WIP-14 | Decision F named constant BACKTEST_REGIME_SAMPLE_CORE = 0; ordering race-free per M-3 |
| PARITY-032 | CLOSED at WIP-11 LIVE (D1-B FOREACH_SLOW_PATH_GATE) + will CLOSE at WIP-12 BACKTEST when AllCores call lands | D1-B cached-gate dispatch in EngineCommon_SlowPathCycleOneCore |

5 of 7 already CLOSED; 2 remaining close at WIP-12 + WIP-14 per planned cadence.

Blocking gaps for v1.7.5 amendment lock:
- H-1: PARITY-031 ledger line-number correction (mechanical 5 min)
- H-2: PARITY-032 ledger entry creation (mechanical 10 min)
- M-4: controller_test.cpp 2 test sites enumeration in B-full deletion scope (mechanical 10 min)
- M-5: Plan body line range re-enumeration of 8 branches at HEAD `e0acb65` (mechanical via grep)

None blocking; all mechanical fixes absorbed at v1.7.5 amendment cycle. **PROCEED** to v1.7.5 amendment after operator triage.

---

**End of /parity-check report. Findings auto-written would normally include H-1 + H-2 to PARITY_ISSUES.md per auto-write contract, but this report is the gate audit BEFORE v1.7.5 amendment lock — defer auto-write to Phase D ship close per operator instruction (this audit is pre-amendment-gate; ledger writes happen at amendment lock OR ship close). Captured here for amendment scope.**
