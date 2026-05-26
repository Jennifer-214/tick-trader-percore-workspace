---
type: plan-check
sprint: v5.15-live-readiness
ship: v5.15.5.F.4d.1.B.4
phase: A
step: A.4 + A.5
generated: 2026-05-25
generator: Phase A Step A.4 + A.5 enumeration sweep
engine_head: 64e7101 (Version.hpp 5.15.5.F.4d.1.B.3)
verdict: DRIFT_FOUND
recommendation: HOLD-FOR-V1.5 (plan body amendment required before Phase B unlock)
---

# .B.4 Phase A Step A.4 + A.5 enumeration — drift findings

## Verdict: DRIFT FOUND — plan body v1.4 has 3 categories of stale claims

Per `feedback_compaction_degrades_treat_handoffs_as_hints` + `feedback_plan_right_not_fast`: drift catches at planning time prevent coding-time surprises. Phase A enumeration found:

1. **Fabricated function name** (HIGH) — plan body cites `OrderManager_RegisterCore` at LIVE `:1080` + BACKTEST `:270-300`; this function DOES NOT EXIST anywhere in the codebase
2. **Line-range drift on real calls** (LOW) — plan body line numbers for `ConfidenceScorer_Init` / `BindCompositeCfg` / `RollingTurnover_Init` / `Strategy_InitPerCore` are off-by-~10 lines from HEAD code
3. **Static count overstated** (LOW) — plan body + /dod-audit v1.2 claim "~30 statics in EngineSharded_Run body"; actual count at HEAD is **21**

Per Phase A Step A.4 contract: enumeration is the source of truth; plan body MUST be amended to match before Phase B unlock.

## Drift Finding #1 — HIGH — fabricated `OrderManager_RegisterCore` function name

**Plan body v1.4 § Step A.4 EXAMPLE claims:**

```
EngineSharded_Run boot call sequence (EngineSharded.hpp:660-1177; ACTUAL ORDER per N3):
PER-CORE LOOP (c in 0..N-1):
  :1080    OrderManager_RegisterCore(c)                                  [→ BootPerCore]
```

```
BacktestSharded_Run boot call sequence (Backtest/BacktestSharded.hpp:120-410):
PER-CORE LOOP:
  :270-300 OrderManager_RegisterCore                                    [present]
```

**Verification at HEAD 64e7101:**

```bash
$ rg -n "OrderManager_RegisterCore" /home/caramel/code/FoxML_Trader_v2/
(no matches anywhere in codebase)
```

**Actual function call at the cited region:**

| Live :911 | `EventLoopState_RegisterCore(&state, &cores[i], FPN_Zero, FPN_Zero, FPN_Zero)` |
| Backtest :255 | `EventLoopState_RegisterCore(&state, &cores[i], FPN_Zero, FPN_Zero, FPN_Zero)` |

The actual per-core registration is `EventLoopState_RegisterCore` (NOT `OrderManager_RegisterCore`). Plan body conflated two distinct framework concerns: registering a core into the event loop's dispatch table (the real call) vs. registering a core into an OMS routing table (no such mechanism exists; OMS routes via `core_id` field on `Order` struct, not registration).

**Impact:** Phase B Step B.2 implementer would search for `OrderManager_RegisterCore` extraction site, find none, conclude either (a) the call was already removed (and skip it) or (b) the plan is wrong and pause for clarification. Either way → coding-time surprise.

**Plan body v1.5 fix:**

```diff
- :1080    OrderManager_RegisterCore(c)                                  [→ BootPerCore]
+ :911     EventLoopState_RegisterCore(&state, &cores[i], FPN_Zero, FPN_Zero, FPN_Zero)  [→ BootPerCore]
```

```diff
- :270-300 OrderManager_RegisterCore                                    [present]
+ :255     EventLoopState_RegisterCore(&state, &cores[i], FPN_Zero × 3)  [present; MATCH]
```

## Drift Finding #2 — LOW — line-range off-by-~10 on real calls

**Plan body v1.4 vs HEAD actual:**

| Plan body claim | HEAD actual | Delta |
|---|---|---|
| `:1080 OrderManager_RegisterCore` | (n/a — see Finding #1) | n/a |
| `:1125 ConfidenceScorer_Init` | `:1136 ConfidenceScorer_Init` | +11 |
| `:1130 ConfidenceScorer_BindCompositeCfg` | `:1141 ConfidenceScorer_BindCompositeCfg` | +11 |
| `:1138 RollingTurnover_Init` | `:1149 RollingTurnover_Init` | +11 |
| `:1154 tt::Strategy_InitPerCore` | `:1165 tt::Strategy_InitPerCore` | +11 |
| `:1160+ per-core model load + bandit prior override` | per-core model load region :931-1152; bandit prior override is BACKTEST-only at :358-363 (NOT in live boot at all) | mixed |

**Likely cause:** plan body v1.0 line numbers came from a fork-point before `.B.3` ship-close added ~11 lines around the per-core ML region (sister-helper insertion for PARITY-026 hotfix block at :744-753 = 10 lines added between killswitch + per-core loop).

**Impact:** Phase B Step B.2 implementer can find the calls via `rg` (function names ARE correct here, just line numbers stale). Less risky than Finding #1, but still a planning-discipline gap.

**Plan body v1.5 fix:** simple line-number refresh on Step A.4 example (4 numbers, no semantic change).

**Note on bandit prior override:** plan body Step A.4 says `:1160+ per-core model load + bandit prior override`. The bandit override is BACKTEST-only (`run_cfg->bandit_state_prior_path` at backtest :358-363); LIVE has no bandit prior override mechanism. Update plan body Step A.4 to reflect this asymmetry (or drop the bandit override mention from the live boot enumeration).

## Drift Finding #3 — LOW — static count overstated (21 actual vs ~30 claimed)

**Plan body v1.4 § Step A.5 claims:**

> Static-scope enumeration — **~30** `static` objects in `EngineSharded_Run` body (verified at /dod-audit v1.2). Classify (stay-in-caller default).

**Plan body v1.4 § H2 audit finding (line 68 cited from /dod-audit v1.2):**

> H2 — Static-scope discipline (~30 statics stay in caller; per /dod-audit verified actual count is 30 not 50)

**Verification at HEAD 64e7101 (Artifact 2 CSV at `plans/v5.15-live-readiness/plan_checks/2026-05-25-B4-static-scope-enumeration.csv`):**

| Region | Count |
|---|---|
| Boot region statics (:525..878) | 14 |
| GUI region statics (:1392, 1414) | 2 |
| Loop-scope counter/cache statics (:1861, 2000, 2001, 2028, 3201) | 5 |
| **Total inside `EngineSharded_Run` body** | **21** |

**Likely cause of 30→21 discrepancy:** /dod-audit v1.2 may have included:
- File-scope statics at lines 106-127 (`g_engine_sharded_shutdown`, `g_sharded_order_lat`, `g_engine_sharded_gui_quit_ptr`) — NOT in Run scope (file-scope helpers)
- Inner-lambda statics inside per_core_slow / fan_out / drainer lambda bodies — those are technically lambda-capture-scope, not Run scope, even though they're textually nested inside the file
- Helper-function statics inside `EngineSharded_CalibrateTscGhz` / `EngineSharded_PinThread` / `EngineSharded_SmartSlowPathPins` / `EngineSharded_DumpLatency` — file-scope helpers above Run definition

**Impact:** Low — Decision G discipline still applies regardless of count (every static STAYS_IN_CALLER per Phase A Step A.5 classification at Artifact 2). The count drift is informational, not behavioral.

**Plan body v1.5 fix:** update Step A.5 from "~30 statics" to "21 function-scope statics in EngineSharded_Run body (verified at Phase A Step A.5 Artifact 2 CSV)".

## Recommended plan body v1.5 amendment

**Section: Step A.4 example block**

```diff
EngineSharded_Run boot call sequence (EngineSharded.hpp:660-1177; ACTUAL ORDER per N3):

GLOBAL SECTION (one-shot; before per-core loop):
  :690     cfg.pay_fees_in_bnb BNB multiply cfg.cores[c].fee_rate_*    [→ ApplyBnbDiscount]
  :742     EventLoopState_Init(&state, &oms)                            [→ BootGlobal]
  :750     EventLoopState_ConfigureKillSwitch (per PARITY-026 hotfix)  [→ BootGlobal]
- :760-770 DepthRecorder_Init + Notify worker spawn refs                [→ BootGlobal partial; statics stay]
+ :760-762 Regime_Init loop over MAX_EXECUTION_CORES                    [→ BootGlobal]
+ :767-822 BinanceUserData / NotifyState init (LIVE-only)               [STAYS_IN_CALLER — M5 threading observability]
+ :826-857 TickRecorder/DepthRecorder/depth_thread (LIVE-only)          [STAYS_IN_CALLER — M5 persistence + threading]
- :800+    trade_log opens + global cfg state                            [→ BootGlobal]
+ :710-712 ShardedTradeLog_Init + oms.trade_log wire (LIVE-only)        [STAYS_IN_CALLER — M5 persistence sink]

PER-CORE LOOP (c in 0..N-1; live :908..1177; backtest :251..418):
  :909     SPSCRing_Init(&tick_rings[i])                                 [→ BootPerCore]
  :910     ExecutionCore_Init(&cores[i] uint16_t(i) &tick_rings[i])      [→ BootPerCore]
- :1080    OrderManager_RegisterCore(c)                                  [→ BootPerCore]
+ :911     EventLoopState_RegisterCore(&state, &cores[i], FPN_Zero × 3)  [→ BootPerCore]
  :921     EventLoopState_SetCoreStrategy(&state, i, strategy, balance)  [→ BootPerCore]
  :931+    ML branch: zoo_ptr aligned_alloc + LoadFromDir + PostLoadSetup [→ BootPerCore]
- :1125    ConfidenceScorer_Init(c)                                       [→ BootPerCore]
+ :1136    ConfidenceScorer_Init(c)                                       [→ BootPerCore]
- :1130    ConfidenceScorer_BindCompositeCfg(c)                           [→ BootPerCore]
+ :1141    ConfidenceScorer_BindCompositeCfg(c)                           [→ BootPerCore]
- :1138    RollingTurnover_Init(c)                                        [→ BootPerCore]
+ :1149    RollingTurnover_Init(c)                                        [→ BootPerCore]
- :1154    tt::Strategy_InitPerCore(c)                                    [→ BootPerCore]
+ :1165    tt::Strategy_InitPerCore(c)                                    [→ BootPerCore]
- :1160+   per-core model load + bandit prior override                   [→ BootPerCore + external wrapper]
+ :1173    ExecutionCore_SetPermission(&cores[i], 0)                      [→ BootPerCore]
+ :1176    CoreLatencyStats_Enable (LIVE-only)                            [STAYS_IN_CALLER — M5 threading observability]
```

```diff
BacktestSharded_Run boot call sequence (Backtest/BacktestSharded.hpp:104-418):

GLOBAL SECTION:
- :140-160 EventLoopState_Init                                          [present]
+ :143     Sharded_ValidatePartialExitCfg                                [present; sister to ApplyBnbDiscount]
+ :186-189 OrderManager_Init                                            [present; LIVE has extra args at :671]
+ :198     EventLoopState_Init(&state, &oms)                             [present]
  ?? BNB cfg mutation                                                   [MISSING per PARITY-030 — ADD via ApplyBnbDiscount]
  :217-221 EventLoopState_ConfigureKillSwitch                            [present per PARITY-026]
+ :210-212 Regime_Init loop over MAX_EXECUTION_CORES                    [present]
- ??       DepthRecorder/Notify equivalent                              [verify presence]
+ N/A      DepthRecorder/Notify are LIVE-only (backtest uses DepthReplayState from CSV at :482-488)

PER-CORE LOOP (i in 0..num_cores-1):
- :270-300 OrderManager_RegisterCore                                    [present]
+ :252     SPSCRing_Init                                                 [MATCH]
+ :253     ExecutionCore_Init                                            [MATCH]
+ :255     EventLoopState_RegisterCore                                   [MATCH]
+ :264     EventLoopState_SetCoreStrategy                                [MATCH]
+ :273+    ML branch: CoreModelZoo_Init / LoadFromDir / PostLoadSetup    [MATCH]
- :408     ConfidenceScorer_Init                                        [present; MISSING BindCompositeCfg + RollingTurnover_Init per PARITY-028]
+ :408     ConfidenceScorer_Init                                         [MATCH; MISSING BindCompositeCfg per PARITY-028 + RollingTurnover_Init per PARITY-028 sister]
- :420+    per-core model load                                          [present]
+ :417     ExecutionCore_SetPermission(&cores[i], 0)                     [MATCH]
- ??       Strategy_InitPerCore                                         [MISSING per PARITY-029 — ADD via BootPerCore]
+ N/A      Strategy_InitPerCore                                          [MISSING per PARITY-029 — closes by-construction via BootPerCore extract]
+ N/A      CoreLatencyStats_Enable                                       [LIVE-only by design]
```

**Section: Step A.5 description**

```diff
- **Step A.5 (v1.2 NEW per H2):** Static-scope enumeration — ~30 `static` objects in `EngineSharded_Run` body (verified at /dod-audit v1.2). Classify (stay-in-caller default). Verify helpers do NOT define new statics.
+ **Step A.5 (v1.5 CORRECTED per Phase A enumeration sweep):** Static-scope enumeration — **21 function-scope `static` objects** in `EngineSharded_Run` body (verified at Phase A Step A.5 Artifact 2 CSV). All 21 classified STAY_IN_CALLER per Decision G discipline. Helpers MUST NOT define new statics (signature enforces — helpers accept references to caller statics; don't own them).
```

**Section: H2 audit finding line 68**

```diff
- | **H2** — Static-scope discipline (~30 statics stay in caller; per /dod-audit verified actual count is 30 not 50) | HIGH | blindspot B11 |
+ | **H2** — Static-scope discipline (21 statics stay in caller; verified at Phase A Step A.5 Artifact 2 CSV — was estimated at ~30 at /dod-audit v1.2 + ~50 at v1.0) | HIGH | blindspot B11 |
```

**Section: line 237 introductory body**

```diff
- ~30 function-scope statics in `EngineSharded_Run` (verified at /dod-audit v1.2; was estimated at ~50 in v1.0) stay in caller scope. Helpers don't define new statics. Enumeration at Step A.5.
+ 21 function-scope statics in `EngineSharded_Run` (verified at Phase A Step A.5 enumeration; was estimated at ~30 at /dod-audit v1.2 and ~50 at v1.0) stay in caller scope. Helpers don't define new statics (signature enforces). Enumeration at Step A.5 Artifact 2 CSV.
```

## Phase B unlock recommendation

**HOLD-FOR-V1.5** — plan body amendments required before Phase B helper body coding can start.

**Rationale:**
- Finding #1 (HIGH) is a fabricated function name that would cause coding-time confusion at Step B.2 (BootPerCore body extract). Implementer would search for `OrderManager_RegisterCore` site, find none, pause to ask "did this get removed?" — wasted cycle.
- Findings #2 + #3 (LOW) are off-by-N drift that don't block coding but degrade plan-body authority. Trusting drifted line numbers is the kind of error Caramel's `feedback_compaction_degrades_treat_handoffs_as_hints` rule was codified to prevent.
- All three findings are mechanical to fix in plan body v1.5 (~10 min editing); no design change needed.

**Suggested next step:** apply v1.5 amendments per diffs above, mark Phase A Step A.4 + A.5 as CLOSED with v1.5 plan body lock, then unlock Phase B (5 helper body coding).

## Reference artifacts

- `2026-05-25-B4-boot-call-sequence-enumeration.csv` — Artifact 1 (~71 rows; full per-call classification with section + live-line + backtest-line + helper-target + rationale)
- `2026-05-25-B4-static-scope-enumeration.csv` — Artifact 2 (21 rows; all classified STAY_IN_CALLER per Decision G)
- `CoreFrameworks/EngineCommon.hpp` — Phase 0 skeleton landed 2026-05-25 (5 helper declarations + BACKTEST_REGIME_SAMPLE_CORE constant + 200+ LOC documentation block; ready for Phase B body coding once plan body v1.5 lands)
