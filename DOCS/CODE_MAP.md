# CODE_MAP.md

Auto-generated function index. Walks .hpp files in each subsystem and extracts `Pattern_FunctionName` style definitions with their one-line purpose (from the preceding `//` comment, when present).

**Re-generate**: `./tools/gen_code_map.sh`

**Last regenerated**: 2026-06-12 (commit 8352b5e)

## CoreFrameworks/

### BinanceAdapter.hpp

- `BinanceAdapter_WorkerLoop` — line 140 — shutdown_requested flips.
- `BinanceAdapter_Init` — line 253 — 1; future commits scale up after the back-to-back stress test passes.
- `BinanceAdapter_ShutdownState` — line 307 — without a successful Init (shutdown_requested is already 0 by default).
- `BinanceAdapter_SubmitMarketBuy` — line 330 — holds with worker_count == 1.
- `BinanceAdapter_SubmitMarketSell` — line 350
- `BinanceAdapter_GetBalancesImpl` — line 384 — pausing submissions during a reconciliation pass.
- `BinanceAdapter_QueryOrderImpl` — line 392
- `BinanceAdapter_ShutdownImpl` — line 409
- `BinanceAdapter_Get` — line 422

### ControllerConfig.hpp

- `Fee_Compute` — line 1365
- `ControllerConfig_ResolveForCore` — line 1383
- `ControllerConfig_PopulateCoresFromFlat` — line 1445
- `ControllerConfig_NormalizeForMode` — line 2008
- `ControllerConfig_Load` — line 2039

### ControllerEventLoop.hpp

- `CoreSlowState_Init` — line 166
- `CoreContextDisplayMeta_Init` — line 691
- `EventLoopState_ReconstructPerCoreFromEventLog` — line 835
- `EventLoopState_Init` — line 906
- `EventLoopState_InitLegacy` — line 963
- `EventLoopState_Free` — line 996
- `EventLoopState_RegisterCore` — line 1049
- `Sharded_LegSlot` — line 1099 — All slow-path / boot-time. Trivially inlined.
- `Sharded_ValidatePartialExitCfg` — line 1136
- `EventLoopState_SetCoreStrategy` — line 1188
- `EventLoopState_AttachTradeLog` — line 1212
- `EventLoopState_AttachOms` — line 1229
- `EventLoopState_Balance` — line 1247
- `EventLoopState_RealizedPnl` — line 1252
- `EventLoopState_Portfolio` — line 1263
- `EventLoopState_PortfolioMut` — line 1268
- `EventLoopState_KsMinBalance` — line 1273
- `EventLoopState_KsMaxDrawdownPct` — line 1278
- `EventLoopState_KsPeakBalance` — line 1283
- `EventLoopState_TradeLog` — line 1299
- `EventLoopState_SetIntendedParams` — line 1314
- `EventLoop_DrainPostFillOneCore` — line 1370
- `EventLoop_DrainPostFill` — line 1799
- `EventLoop_OnEvent` — line 1851
- `EventLoop_DrainEvents` — line 2010
- `EventLoop_QueueParameters` — line 2044
- `EventLoop_RebuildAllParameters` — line 2077
- `EventLoop_UpdateRollingStateOneCore` — line 2167
- `EventLoop_UpdateEmaPriceAllCores` — line 2210
- `EventLoop_RebuildOneCore` — line 2229
- `EventLoop_PushParameters` — line 3142
- `EventLoopState_ConfigureKillSwitch` — line 3177
- `EventLoop_ClearAllPermissions` — line 3187
- `EventLoop_KillSwitchTrip` — line 3198
- `EventLoop_KillSwitchEvaluate` — line 3227
- `EventLoop_TimeExitOneCore` — line 3301
- `EventLoop_FlattenAll` — line 3396
- `EventLoop_CheckWsStaleness` — line 3480
- `EventLoop_TryClearRecovery` — line 3559
- `EventLoop_TrailingSLRatchetOneCore` — line 3602
- `EventLoop_BreakevenOnProfitOneCore` — line 3681
- `EventLoop_Unpause` — line 3725
- `EventLoop_SlowPath` — line 3749
- `EventLoop_RunController` — line 3774

### CoreLatencyStats.hpp

- `CoreLatencyStats_Init` — line 128 — stats mid-run without disabling them.
- `CoreLatencyStats_Reset` — line 140
- `CoreLatencyStats_Enable` — line 151
- `CoreLatencyStats_Disable` — line 155
- `CoreLatencyStats_Sample` — line 170 — rdtsc reading at sample time, used for "last seen" tracking in the TUI.
- `CoreLatencyStats_Snapshot` — line 198 — skip the conversion (cycle counts only).

### EngineCommon.hpp

- `EngineCommon_ApplyBnbDiscount` — line 154
- `EngineCommon_BootGlobal` — line 183
- `EngineCommon_BootPerCore` — line 235
- `EngineCommon_SlowPathCycleOneCore` — line 476
- `EngineCommon_SlowPathCycleAllCores` — line 806

### EnsembleHotSwap.hpp

- `EngineSharded_HotSwapEnsemble` — line 45

### EventLoopAggregates.hpp

- `EventLoop_GetAggregates` — line 103

### ExecutionCore.hpp

- `ExecutionCore_Init` — line 195
- `ExecutionCore_SetParameters` — line 239
- `ExecutionCore_SetPermission` — line 260
- `ExecutionCore_Tick_Impl` — line 290
- `ExecutionCore_Tick` — line 647

### GateParameters.hpp

- `BG_Evaluate` — line 167
- `SG_Evaluate` — line 189
- `GateParameters_Init` — line 206

### HotSwap.hpp

- `HotSwap_ShadowLoad_Ensemble` — line 74
- `HotSwap_ShadowLoad_SingleZoo` — line 211

### LegacyReferenceDriver.hpp

- `LegacyReference_Init` — line 95
- `LegacyReference_AddSlot` — line 120
- `LegacyReference_Tick` — line 138
- `LegacyReference_SlowPath` — line 183
- `LegacyReference_Run` — line 211

### LiveReadiness.hpp

- `LiveReadiness_Verify` — line 228

### MetricCompute.hpp

- `Compute_ProfitFactor` — line 46 — → backtest-suite layering boundary.
- `Compute_AllWinsRun` — line 52 — numerical profit_factor is 0.0 in this case, separately).
- `Compute_Expectancy` — line 56
- `Compute_WinRate` — line 68
- `Compute_AvgHoldTicks` — line 74
- `Compute_ReturnPct` — line 80
- `MaxDrawdown_UpdateIncremental` — line 91 — regression test needed.

### ModelValidation.hpp

- `CoreModelZoo_ValidateAgainstCfg` — line 136

### Notify.hpp

- `NotifyState_Init` — line 169
- `Notify_Send` — line 188 — Cooldown gate uses CLOCK_MONOTONIC (NTP-jump-safe).
- `NotifyState_Shutdown` — line 238 — Drain remaining events + join worker thread + free pthread resources.
- `NotifyBackend_Stderr` — line 253 — [STDERR BACKEND] — default, always available, ships in Phase 8b
- `Notify_ShellEscape` — line 316 — Document this for users; provide a wrapper script if needed.
- `Notify_BuildCommand` — line 339 — overflowed before completion (still tries to run what fit).
- `NotifyBackend_Command` — line 366

### OrderEventLog.hpp

- `OrderEventLog_Init` — line 204
- `OrderEventLog_Free` — line 247
- `OrderEventLog_ApplyEvent` — line 291
- `OrderEventLog_Append` — line 314
- `OrderEventLog_AsyncWriterRoutine` — line 349
- `OrderEventLog_StartAsyncWriter` — line 383
- `OrderEventLog_StopAsyncWriter` — line 398
- `OrderEventLog_InitWithFile` — line 417
- `OrderEventLog_Reset` — line 492
- `OrderEventLog_LoadFromDisk` — line 534
- `OrderEvent_MakeFill` — line 624
- `OrderEvent_MakeRejection` — line 651
- `Portfolio_FromEventLog` — line 698

### OrderGates.hpp

- `Gate_Zero` — line 62
- `Gate_ZeroAll` — line 69

### Order.hpp

- `Order_GetType` — line 210
- `Order_SetType` — line 214
- `Order_GetState` — line 220
- `Order_SetState` — line 224
- `Order_GetIsMaker` — line 230
- `Order_SetIsMaker` — line 234
- `Order_SetLeg` — line 244
- `Order_SetRetryCount` — line 254
- `Order_GetPreResolvedBound` — line 263
- `Order_MarkPreResolvedBound` — line 267
- `MBS_OrderBanditActiveState` — line 283
- `MBS_OrderBanditRegime` — line 287
- `MBS_OrderBanditChosenArm` — line 291
- `MBS_OrderSetBanditContext` — line 295
- `Order_Init` — line 318
- `Order_BindPreResolved` — line 359
- `Order_WarnIfNotPreResolved` — line 385
- `Order_IsTerminal` — line 416

### OrderManager.hpp

- `OrderManager_Init` — line 861
- `OMS_PushSubmit` — line 1076
- `OMS_DrainSubmit` — line 1107
- `OrderManager_AccountMakerTakerFee` — line 1138
- `OMS_GuardTakerBoundFeeBasis` — line 1157
- `OrderManager_HandleFill` — line 1310
- `OrderManager_ProcessFillCommand` — line 1370
- `OrderManager_ProcessReconcile` — line 1473
- `OrderManager_Tick` — line 1509
- `OrderManager_Shutdown` — line 1543
- `OrderManager_OpenCalibrationLog` — line 1565
- `OrderManager_InflightCount` — line 1610

### PaperResetArchive.hpp

- `PaperResetArchive_FormatTimestamp` — line 93 — Uses localtime_r for thread safety. out_size should be >= 20.
- `PaperResetArchive_FormatDirname` — line 107 — out_size should be >= 128 (typical ISO string + path overhead ~80 chars).
- `PaperResetArchive_CreateDirectories` — line 126 — calling mkdir() incrementally.
- `Summary_WriteJson` — line 174

### ParameterSlot.hpp

- `ParameterSlot_Init` — line 152
- `ParameterSlot_Write` — line 194
- `ParameterSlot_Read` — line 244

### PortfolioController.hpp

- `PortfolioController_Init` — line 286
- `KillSwitch_Activate` — line 538
- `KillSwitch_Reset` — line 552
- `Buying_Halt` — line 561
- `PortfolioController_DrainExits` — line 751
- `PortfolioController_StrategyBuySignal` — line 778
- `PortfolioController_StrategyDispatch` — line 869
- `PortfolioController_Tick` — line 915
- `PortfolioController_Unpause` — line 1921
- `PortfolioController_CycleRegime` — line 1932
- `PortfolioController_HotReload` — line 1958
- `PortfolioController_SaveSnapshot` — line 2035
- `PortfolioController_LoadSnapshot` — line 2110

### Portfolio.hpp

- `ExitBuffer_PendingProceeds` — line 196
- `Portfolio_AddPositionWithExits` — line 268
- `Portfolio_OpenSlot` — line 358
- `Portfolio_OpenSlot` — line 389
- `Money_FillGross` — line 408 — open-coding the 2-mul form at any site (was DrainPostFill :1536) re-introduces a 1-ULP divergence.
- `Portfolio_CloseSlot` — line 413
- `Portfolio_SlotActive` — line 421
- `Portfolio_UpdatePosition` — line 431
- `Portfolio_Save` — line 547
- `Portfolio_Load` — line 586

### Reconcile.hpp

- `ReconcileMode_ToString` — line 136 — Mode → string for logging. Uses cfg_string field (operator-friendly).
- `ReconcileMode_FromString` — line 149 — parse OR error). Accepts cfg_string values from registry.
- `Reconcile_ApplyMissedFills` — line 205
- `Reconcile_AutoCancelStale` — line 343
- `Reconcile_ParseOpenOrders` — line 498 — Output: fills `out` array up to `out_cap`. Returns count parsed.
- `Reconcile_ParseMyTrades` — line 531 — Output: fills `out` array up to `out_cap`. Returns count parsed.
- `Reconcile_Decide` — line 573 — Outputs ReconcileResult with planned actions. Caller applies them.
- `Reconcile_LogReport` — line 635 — 3. If refused_boot: caller exits / refuses to advance

### ReconciliationLoop.hpp

- `ReconciliationLoop_Pass` — line 93
- `ReconciliationLoop_Init` — line 195
- `ReconciliationLoop_Start` — line 225
- `ReconciliationLoop_TriggerNow` — line 235
- `ReconciliationLoop_Shutdown` — line 243

### ShardedBacktestDriver.hpp

- `ShardedBacktestDriver_Init` — line 144
- `ShardedBacktest_RunTick` — line 192
- `ShardedBacktest_Run` — line 393

### ShardedLiveSafety.hpp

- `EngineSharded_OrphanRecovery` — line 46 — expected positions, we can reconcile rather than blindly selling.
- `EngineSharded_ForceCloseOnShutdown` — line 146

### ShardedOrderLatency.hpp

- `ShardedOrderLatency_Reset` — line 46 — before the first order can fire.
- `ShardedOrderLatency_Sample` — line 59 — race in a future thread-pool world; safe and cheap with one writer too.

### ShardedSnapshot.hpp

- `TUI_CopySnapshotSharded` — line 42

### ShardedSnapshotPersist.hpp

- `ShardedSnapshot_Save` — line 116
- `ShardedSnapshot_Load` — line 312

### ShardedTradeLog.hpp

- `ShardedTradeLog_FormatPerCoreFilename` — line 97 — the next consumer would silently drift. Helper makes drift impossible.
- `ShardedTradeLog_WriteRow` — line 124 — non-fatal — aggregate file already has the row.
- `ShardedTradeLog_Init` — line 145 — without a trade log, you just don't get the CSV.
- `ShardedTradeLog_Flush` — line 233 — called once at engine shutdown.
- `ShardedTradeLog_Rotate` — line 253 — the existing file open).
- `ShardedTradeLog_Close` — line 314
- `ShardedTradeLog_RecordEntry` — line 344
- `ShardedTradeLog_RecordExit` — line 397

### SPSCRing.hpp

- `SPSCRing_Init` — line 95
- `SPSCRing_TryPush` — line 132
- `SPSCRing_TryPop` — line 179
- `SPSCRing_Depth` — line 201
- `SPSCRing_Capacity` — line 210

### SpSectionRegistry.hpp

- `SP_SECTION_NAME` — line 61 — Auto-generated documentation strings (for tooltips, log headers, etc.).
- `SP_SECTION_DOC` — line 69

### StampBoundDerivedFilter.hpp

- `STAMP_BOUND_CFG_emit_canonical_body` — line 40 — .B activates real per-type emit via tt::cfg_emit_synthetic_field<T>.

### TradeLogColRegistry.hpp

- `TradeLog_EmitHeader` — line 97 — the pre-v5.14.10.F hand-coded header literal at ShardedTradeLog.hpp:118-119.

## Strategies/

### MeanReversion.hpp

- `MeanReversion_Init` — line 73
- `MeanReversion_Adapt` — line 118
- `MeanReversion_BuySignal` — line 273
- `MeanReversion_ExitAdjust` — line 413
- `MeanReversion_ExitAdjustSharded` — line 520

### MLStrategy.hpp

- `MLStrategy_Init` — line 55
- `MLStrategy_Adapt` — line 87
- `MLStrategy_Adapt_Canonical` — line 105
- `MLStrategy_BuySignal` — line 125
- `MLStrategy_ExitAdjust` — line 219
- `MLStrategy_ExitAdjustSharded` — line 284

### Momentum.hpp

- `Momentum_Init` — line 60
- `Momentum_Adapt` — line 92
- `Momentum_BuySignal` — line 171
- `Momentum_ExitAdjust` — line 249
- `Momentum_ExitAdjustSharded` — line 330

### RegimeDetector.hpp

- `CumDelta_Init` — line 124
- `CumDelta_Push` — line 132
- `TickRate_Init` — line 164
- `TickRate_Push` — line 172
- `TickRate_CurrentZ` — line 199
- `Regime_ComputeSignals` — line 223
- `Regime_Init` — line 481
- `Regime_Classify` — line 513
- `Regime_ToStrategy` — line 667
- `Regime_AdjustPositions` — line 685

### SimpleDip.hpp

- `SimpleDip_Init` — line 32
- `SimpleDip_Adapt` — line 43
- `SimpleDip_BuySignal` — line 57
- `SimpleDip_ExitAdjustSharded` — line 100

### StrategyLifecycle.hpp

- `Strategy_SeedFromCfg` — line 66
- `Strategy_SeedFromCfg` — line 71
- `Strategy_SeedFromCfg` — line 85
- `Strategy_FreePerCore` — line 113
- `Strategy_InitPerCore` — line 116
- `Strategy_AdaptPerCore` — line 178
- `Strategy_WriteRatchetSL` — line 264
- `Strategy_WriteRatchetTP` — line 304
- `Strategy_ExitAdjustPerCore` — line 336
- `Strategy_FreePerCore` — line 375

### StrategyParameters.hpp

- `Strategy_SpacingOk` — line 238
- `Strategy_TpFloor` — line 257
- `SimpleDip_BuildParameters` — line 342
- `MeanReversion_BuildParameters` — line 422
- `Momentum_BuildParameters` — line 494
- `EmaCross_BuildParameters` — line 609
- `ML_BuildParameters` — line 722
- `Strategy_BuildParameters` — line 1637

## Strategies/private/

### EmaCross.hpp

- `EmaCross_Init` — line 34
- `EmaCross_Adapt` — line 46
- `EmaCross_BuySignal` — line 58
- `EmaCross_ExitAdjust` — line 109
- `EmaCross_ExitAdjustSharded` — line 184

## DataStream/

### BinanceCrypto.hpp

- `BinanceStream_Init` — line 503 — (internally tracks whether its already been called)
- `BinanceStream_Close` — line 577 — clean shutdown: send close frame, SSL shutdown, close socket, free resources
- `BinanceStream_Reconnect` — line 613
- `BinanceStream_Poll` — line 659 — returns OR'd combination of POLL_NONE, POLL_SOCKET, POLL_STDIN
- `BinanceStream_ReadTick` — line 707
- `BinanceStream_InWindDown` — line 794 — BinanceStream_ShouldReconnect: returns 1 if it's time to close and reconnect
- `BinanceStream_ShouldReconnect` — line 807
- `BinanceStream_HasPending` — line 823 — returns 1 if SSL has buffered data that can be read without blocking
- `BinanceConfig_Load` — line 834 — same key=value format as ControllerConfig_Load, skips # comments and empty lines

### BinanceDepth.hpp

- `DepthStream_Init` — line 206

### BinanceOrderAPI.hpp

- `BinanceOrderAPI_Cleanup` — line 500
- `BinanceOrderAPI_MarketBuy` — line 510 — fill_price_out/fill_qty_out receive actual execution values (NULL = don't care)
- `BinanceOrderAPI_MarketSell` — line 565 — place a market sell order
- `BinanceOrderAPI_CancelOrder` — line 639 — different operator semantics.
- `BinanceOrderAPI_GetStatus` — line 673 — fills filled_qty and avg_price on success
- `BinanceOrderAPI_LoadFilters` — line 722 — returns 1 on success, 0 on failure (caller should treat as fatal)
- `BinanceOrderAPI_GetBalance` — line 757 — returns 1 on success, 0 on failure
- `BinanceOrderAPI_GetOpenOrders` — line 789 — network-independent (testable without real REST calls).
- `BinanceOrderAPI_GetMyTrades` — line 800 — the last-known-processed trade id to catch only new fills.
- `BinanceOrderAPI_GetBalances` — line 816 — returns 1 on success, 0 on failure
- `BinanceOrderAPI_SyncClock` — line 840 — re-sync clock offset (call periodically or after reconnect)
- `BinanceOrderAPI_Init` — line 854 — must be called after Cleanup, ServerTime, SyncClock, LoadFilters are defined

### BinanceUserData.hpp

- `BinanceUserData_Init` — line 583 — ws_result_queue: pointer into the OMS's dedicated WS SPSC ring
- `BinanceUserData_Start` — line 622
- `BinanceUserData_Shutdown` — line 631

### CalibLogColRegistry.hpp

- `CalibLog_EmitHeader` — line 145 — pre-v5.14.10.D hand-coded header literal at OrderManager.hpp:1293-1295.

### DepthRecorder.hpp

- `DepthRecorder_MkdirP` — line 64
- `DepthRecorder_DateInt` — line 79
- `DepthRecorder_OpenFile` — line 87
- `DepthRecorder_PruneOld` — line 123
- `DepthRecorder_Init` — line 158
- `DepthRecorder_LogGap` — line 194 — disconnect time, or the current snapshot's timestamp_us).
- `DepthRecorder_Write` — line 222
- `DepthRecorder_Close` — line 275

### DepthReplayState.hpp

- `DepthReplay_DateInt` — line 77
- `DepthReplayState_Init` — line 95
- `DepthReplayState_Free` — line 130
- `DepthReplayState_LoadDay` — line 163
- `DepthReplayState_Advance` — line 280
- `DepthReplayState_GetSnapshot` — line 305

### EngineTUI.hpp

- `TUI_Init` — line 132
- `TUI_Cleanup` — line 165
- `TUI_Render` — line 188
- `TUI_HandleInput` — line 575
- `MLSnapshot_Populate` — line 695
- `TUISnapshot_InitSeq` — line 1382 — populated" state) — this only initializes the sequence counter.
- `TUISnapshot_Publish_Begin` — line 1397 — the new active.
- `TUISnapshot_Publish_End` — line 1413 — Any subsequent reader sees the just-filled buffer as active.
- `TUISnapshot_ReadInto` — line 1425 — effectively never observed.
- `TUI_CopySnapshot` — line 1455
- `TUI_CopySnapshot` — line 1461
- `TUI_CopySnapshot` — line 1468
- `TUI_PopulatePerCoreLatency` — line 1741
- `TUI_PopulatePerCoreSlowPathLatency` — line 1788
- `TUI_PopulateAdvancedTopology` — line 1826
- `TUI_PopulateTopology` — line 1870 — poll_interval[i]    — per-core resolved poll cadence
- `TUI_Render_Snapshot` — line 1906 — runs on TUI thread. reads only from snapshot (all doubles, no FPN_Binary).
- `TUI_ReadKey` — line 2117

### FauxFIX.hpp

- `FIX_ParseTag` — line 75 — returns the tag number, writes value start and length into out params
- `FIX_ParseDouble` — line 106 — not meant to be fast, just correct enough for test data
- `FIX_Parse` — line 182 — validates checksum if tag 10 is present
- `FIX_BuildMarketDataMsg` — line 256 — writes into buf which must be at least FIX_MAX_MSG_LEN bytes

### MetricsLog.hpp

- `MetricsLog_Init` — line 40
- `MetricsLog_Close` — line 62
- `MetricsLog_SlowPath` — line 85
- `MetricsLog_Event` — line 139

### MockGenerator.hpp

- `MockRNG_Seed` — line 31
- `MockRNG_Double` — line 42 — returns a double in [0.0, 1.0)
- `MockRNG_Range` — line 47 — returns a double in [lo, hi)
- `MockGenerator_Init` — line 75
- `MockGenerator_NextTick` — line 88 — returns the length written to buf, and fills out the parsed message for convenience
- `MockGenerator_Batch` — line 122 — buf is scratch space for building FIX messages (reused each tick)

### TickRecorder.hpp

- `TickRecorder_MkdirP` — line 43
- `TickRecorder_DateInt` — line 58
- `TickRecorder_OpenFile` — line 71
- `TickRecorder_PruneOld` — line 106
- `TickRecorder_Init` — line 141
- `TickRecorder_Push` — line 173
- `TickRecorder_Close` — line 207

### TradeLog.hpp

- `TradeLog_Init` — line 57
- `TradeLog_Buy` — line 90
- `TradeLog_Sell` — line 103
- `TradeLog_Close` — line 115
- `TradeLogBuffer_Init` — line 137
- `TradeLogBuffer_PushBuy` — line 143 — hot path: push a record to the ring buffer (~10ns, no file I/O)
- `TradeLogBuffer_PushSell` — line 162
- `TradeLogBuffer_Drain` — line 184 — slow path: drain all buffered records to the CSV file

### TUIAnsi.hpp

- `ANSI_Section_Header` — line 330
- `ANSI_Section_TopBar` — line 404
- `ANSI_Section_Market` — line 435
- `ANSI_Section_Regime` — line 479 — new section: shows R², vol_ratio, ror_slope that weren't in previous TUI backends
- `ANSI_Section_BuyGate` — line 590
- `ANSI_Section_Portfolio` — line 666
- `ANSI_Section_PnL` — line 705
- `ANSI_Section_Risk` — line 730
- `ANSI_Section_Config` — line 758
- `ANSI_Section_Stats` — line 785
- `ANSI_Section_Positions` — line 846
- `ANSI_Section_Charts` — line 923
- `ANSI_Section_Controls` — line 963
- `ANSI_Section_Latency` — line 979
- `ANSI_Section_PerCoreLatency` — line 1018 — per-core latency the moment they flip engine_mode=sharded.
- `ANSI_Section_RightPanel` — line 1058 — hidden on narrow terminals (< 100 columns)
- `ANSI_Layout_Standard` — line 1119
- `ANSI_Layout_Charts` — line 1165 — ANSI_Section_RightPanel(ab, s, h, w, start_time);
- `ANSI_Layout_Compact` — line 1203
- `ANSI_Layout_Render` — line 1218
- `ANSI_Render` — line 1240 — call from TUI thread at desired FPS

## FixedPoint/

### FixedPointN.hpp

- `FPN_BlendOnMask` — line 511
- `Money_Mul` — line 1583 — into the overflow mask -> saturate + flag (never garbage-as-value).
- `Money_Div` — line 1607 — NEVER __udivti3 (constant 128-trip cmov loop).
- `Money_Add` — line 1627 — integer ops with a closure clamp + S-17 flag). Branchless mask-select clamp by the result sign.
- `Money_Add` — line 1635
- `Money_FromString` — line 1791
- `Money_FromBinary` — line 1833 — threshold would be a wrong gate — load-bearing, per the fold).
- `Money_Zero` — line 1850 — lower to cmov (same shape as fp2_min/max); BlendOnMask mirrors the live <64> mask-select.
- `Money_Negate` — line 1851
- `Money_Abs` — line 1852
- `Money_Min` — line 1853
- `Money_Max` — line 1854
- `Money_IsZero` — line 1855
- `Money_Lt` — line 1856
- `Money_Le` — line 1857
- `Money_Eq` — line 1858
- `Money_Gt` — line 1859
- `Money_Ge` — line 1860
- `Money_QuantizeToStep` — line 1867 — NEVER a plain wide divide (no __udivti3 on any path).
- `Money_BlendOnMask` — line 1876
- `Money_FromInt` — line 1881 — Money_FromInt: whole-unit int -> money (i*10^8), clamp+flag past the closure ceiling.
- `Money_ToDouble` — line 1890 — Money_ToDouble — DISPLAY-ONLY (H4-exempt): GUI/diag/inf-bridge consumption. Never accounting.
- `Money_ToCString` — line 1915 — quantize). Returns chars written (excl. NUL); 0 on insufficient cap (needs <= 32).

## MemHeaders/

### CoreCtxSummaryFieldRegistry.hpp

- `Summary_EmitPerCoreEntry` — line 202
- `Summary_EmitPerStrategy` — line 237

### DrainerConstants.hpp

- `DrainerConstants_Init` — line 100

### HealthLog.hpp

- `HealthLog_Singleton` — line 95 — Process-singleton. Engine init writes; all callers read.
- `Health_LogConfigureWithRotation` — line 113 — directory still doesn't exist).
- `Health_LogConfigure` — line 149
- `Health_LogPruneRotated` — line 161 — Health_Log (would loop).
- `Health_LogEnabled` — line 190 — "level <= min_level" emits.
- `Health_Log` — line 201 — Returns 1 on success, 0 on i/o failure (ignored by most callers).
- `Health_LogCriticalRateLimited` — line 319 — double-emit-once on race, not data corruption).

### InitArena.hpp

- `InitArena_Create` — line 69 — reservation gets a non-fatal degraded-but-functional path.
- `InitArena_Alloc` — line 114 — are 8 (for plain structs) or 64 (for cache-line-aligned hot structures).
- `InitArena_AllocOne` — line 139
- `InitArena_Destroy` — line 145 — struct). After Destroy, the arena is empty and capacity=0.
- `InitArena_Used` — line 162 — Introspection: how many bytes have been allocated from the arena so far.
- `InitArena_Remaining` — line 168 — is unknown; this is an upper bound).
- `InitArena_Owns` — line 180 — ctrl->rolling_long = nullptr;
- `InitArena_Global` — line 199 — spawn and after they join.

### LatencyHistogram.hpp

- `LatencyHistogram_Reset` — line 119 — cross-thread races by contract — writer thread paused or not yet started).
- `LatencyHistogram_Accumulate` — line 140 — entire instrumentation block per CLAUDE.md item 18).

### OmsPhasedDrain.hpp

- `OmsDrainBuckets_Reset` — line 87 — Reset bucket counts. Called at top of DrainIntoBuckets each cycle.
- `OrderType_IsClose` — line 102 — Returns: true if order is a CLOSE (SELL-direction); false if OPEN (BUY).
- `OrderManager_DrainIntoBuckets` — line 225
- `OrderManager_ProcessBucket_Closes` — line 256
- `OrderManager_ProcessBucket_Opens` — line 272
- `OrderManager_ProcessBucket_Reconciles` — line 285

### OmsPushExitHelper.hpp

- `OMS_PushExitForSlot` — line 76

### RunHistory.hpp

- `RunHistory_Append` — line 76 — defense-in-depth for the HMAC/stamp-adjacent byte-equivalence path.)

## ML_Headers/

### BanditAlgorithmRegistry.hpp

- `BanditAlgo_Exp3_Apply` — line 91 — cfg=2 reassigns to Exp3_Drives_Thompson_Ghost_Apply per Option C wire-preserving expansion).
- `BanditAlgo_Thompson_Apply` — line 94
- `BanditAlgo_Exp3_Drives_Thompson_Ghost_Apply` — line 97
- `BanditAlgo_Thompson_Drives_Exp3_Ghost_Apply` — line 100
- `BanditAlgo_Blended_Apply` — line 103
- `BanditAlgorithm_ToString` — line 230
- `BanditAlgorithm_FromString` — line 242 — CRITICAL operator error — don't silently default).
- `BanditAlgorithm_Apply` — line 267 — parse failure; the safe fallback is the bytewise-identical default path.
- `BanditAlgo_Exp3_Apply` — line 296 — default). Thompson state + blend_alpha ignored.
- `BanditAlgo_Thompson_Apply` — line 326 — + blend_alpha ignored. Posterior state advances (rng_state mutates) as part of sampling.
- `BanditAlgo_Exp3_Drives_Thompson_Ghost_Apply` — line 354 — (Class 24 fix — pre-.F.4d Thompson never updated despite mode being settable).
- `BanditAlgo_Thompson_Drives_Exp3_Ghost_Apply` — line 390 — Both bandits update from per-arm reward signal downstream (per-arm observability invariant).
- `BanditAlgo_Blended_Apply` — line 421 — weights via cmov (H20 / Class 28 prevention). Per § J of .F.4d merged plan body.

### BanditLearning.hpp

- `BanditDisplayMeta_InitDefault` — line 86 — BanditDisplayMeta_SetArmName.
- `BanditDisplayMeta_SetArmName` — line 98 — Set a custom human-readable name for an arm (display only).
- `Bandit_Init` — line 133
- `Bandit_InitDefault` — line 156 — convenience: init with default FoxML parameters
- `Bandit_GetProbabilities` — line 185 — tests. Suppress asan here; ubsan + the normal -O3 build still exercise it. (TECH_DEBT-158 close-out.)
- `Bandit_Select` — line 268 — returns arm index. use a PRNG or hardware RNG for the random value.
- `Bandit_Update` — line 289 — with adaptive eta: min(eta_max, sqrt(ln(K) / (K * T)))
- `Bandit_GetWeights` — line 335 — returns weights summing to 1.0 (for blending / display)
- `Bandit_EffectiveBlend` — line 357 — steps >= min+ramp:             effective_blend = blend_ratio
- `Bandit_BlendWeights` — line 366
- `Bandit_Print` — line 399 — to print human-readable names.
- `Bandit_SaveJSON` — line 451 — n_regimes (NUM_REGIMES). NULL → omits the field.
- `Bandit_LoadJSON` — line 639 — caller's prior Bandit_Init call — load is overlay only.

### BarrierBlendModeRegistry.hpp

- `BarrierBlendMode_BlendDrives` — line 121 — mode is compile-time-known.
- `BarrierBlendMode_DominantDrives` — line 125
- `BarrierBlendMode_ShadowActive` — line 129
- `BarrierBlendMode_IsLegacy` — line 133
- `BarrierBlendMode_ToString` — line 144 — and stamp body cfg-drift comparison.
- `BarrierBlendMode_FromString` — line 153
- `BarrierBlendMode_Doc` — line 164

### BarrierGate.hpp

- `BarrierGate_Compute` — line 37 — compute barrier gate value from peak/valley predictions

### ConfidenceScore.hpp

- `RollingWindow_Init` — line 93
- `RollingWindow_Push` — line 102
- `RollingIC_Init` — line 158 — v5.15.5.E.C — Init via generic RollingWindow_Init on both rings.
- `RollingIC_Push` — line 167 — the parallel-array push semantics for the (prediction, actual) pair shape.
- `RollingIC_Compute` — line 194 — RollingIC_Push). Read either; using predictions's metadata canonically.
- `RollingRMSE_Init` — line 272
- `RollingRMSE_Push` — line 295 — in controller_test.cpp.
- `RollingRMSE_Compute` — line 318 — item 29 to 3 production sites.
- `Confidence_Freshness` — line 332 — stability: 1 / (1 + RMSE)
- `Confidence_Stability` — line 338
- `Confidence_Compute` — line 342
- `RollingFreshness_Init` — line 381
- `RollingFreshness_Mark` — line 386
- `RollingFreshness_Compute` — line 393 — or replay determinism), clamp to 1.0.
- `RollingCapacity_Init` — line 410
- `RollingCapacity_UpdateADV` — line 417
- `RollingCapacity_Compute` — line 427
- `ConfidenceScorer_Init` — line 510
- `ConfidenceScorer_ComputeICVariant` — line 546 — New code + sites being refactored for variant choice use this dispatcher.
- `ConfidenceScorer_InitComposite` — line 554 — explicit composite parameters. Useful for tests + v5.14.1.B cfg wiring.
- `ConfidenceScorer_BindCompositeCfg` — line 583 — FPN_ToDouble(cfg.confidence_rmse_baseline));
- `ConfidenceScorer_Update` — line 596 — feed a prediction + actual return pair (call after outcome is known)
- `ConfidenceScorer_UpdateAndMark` — line 609 — when composite is disabled (composite path is opt-in via cfg).
- `ConfidenceScorer_Compute` — line 618 — compute current confidence given data age
- `ConfidenceScorer_ComputeComposite` — line 647 — ConfidenceScorer_Update).
- `ConfidenceScorer_MarkPredict` — line 675 — fixture control.
- `Confidence_DegradationScale_Off` — line 708 — Forward-declare curve compute fns so the dispatch table can reference them.
- `Confidence_DegradationScale_Linear` — line 709
- `Confidence_DegradationScale_Exp` — line 710
- `Confidence_DegradationScale_Step` — line 711
- `DegradationCurve_ToString` — line 744 — Auto-generated ToString — for cfg parser + GUI display.
- `DegradationCurve_FromString` — line 755 — numeric ("1") forms; case-insensitive on string form. Returns -1 on miss.
- `Confidence_DegradationScale_Off` — line 781 — when cfg.risk_degradation_curve=0 (default).
- `Confidence_DegradationScale_Linear` — line 789 — To get ladder-bottom (factor=0), operator sets min_pct=0.0.
- `Confidence_DegradationScale_Exp` — line 799 — as LINEAR.
- `Confidence_DegradationScale_Step` — line 810 — without continuous-curve noise.
- `Confidence_DegradationScale` — line 818 — out-of-range returns 1.0 (degrades safely to OFF behavior).
- `DriftHistory_Init` — line 904
- `DriftHistory_Push` — line 912 — + ts_us[idx], 2 separate cache lines 2048B apart).
- `DriftHistory_CheckBreach` — line 930 — at typical 10-100Hz cadence.
- `ConfidenceScorer_FieldwiseWrite` — line 1009
- `ConfidenceScorer_FieldwiseRead` — line 1018
- `ConfidenceScorer_CommitPersistedFields` — line 1030
- `ConfidenceScorer_RecomputeRunningSums` — line 1053 — CommitPersistedFields tail; PortfolioController calls it explicitly.
- `ConfidenceScorer_ShadowLoadLegacyV1` — line 1122 — Returns 0 on success; -1 on fread failure.

### CoreModelZoo.hpp

- `CoreModelZoo_Init` — line 102
- `CoreModelZoo_TryLoadRole` — line 123
- `CoreModelZoo_LoadFromDir` — line 578
- `CoreModelZoo_LoadLegacy` — line 670
- `CoreModelZoo_Free` — line 681
- `CoreModelZoo_HasAny` — line 691
- `CoreModelZoo_VerifyExpected` — line 719 — features in the pack, model crashes or produces garbage.
- `EnsembleModelZoo_Init` — line 1129
- `EnsembleModelZoo_EnsurePrimary` — line 1221
- `EnsembleModelZoo_RecordPrediction` — line 1263
- `EnsembleModelZoo_UpdateDrift` — line 1292
- `EnsembleModelZoo_TickRewardsFromLookback` — line 1345
- `EnsembleModelZoo_TradeCloseReward` — line 1429
- `EnsembleModelZoo_InitBandits` — line 1493
- `EnsembleModelZoo_InitExitBandits` — line 1541
- `EnsembleModelZoo_InitBuyThompsonBandits` — line 1596
- `EnsembleModelZoo_InitExitThompsonBandits` — line 1648
- `EnsembleModelZoo_SetDisabledHorizons` — line 1690
- `EnsembleModelZoo_Free` — line 1718
- `EnsembleModelZoo_LoadFromCfg` — line 1752
- `EnsembleZoo_VerifyGridMemberConsistency` — line 2012
- `EnsembleModelZoo_AutoDetectFromDir` — line 2082
- `EnsembleModelZoo_ComputeBundleId` — line 2225
- `EnsembleModelZoo_SaveBanditState` — line 2250
- `EnsembleModelZoo_SaveExitBanditState` — line 2272
- `EnsembleModelZoo_LoadBanditState` — line 2296
- `EnsembleModelZoo_LoadExitBanditState` — line 2327
- `EnsembleModelZoo_SaveThompsonState` — line 2370
- `EnsembleModelZoo_SaveExitThompsonState` — line 2459
- `EnsembleModelZoo_LoadThompsonState` — line 2542
- `EnsembleModelZoo_LoadExitThompsonState` — line 2676
- `EnsembleModelZoo_LoadBanditStateFromPath` — line 2805
- `EnsembleModelZoo_SetBanditSaveInterval` — line 2832
- `EnsembleModelZoo_MaybeSaveBanditPeriodic` — line 2850
- `EnsembleModelZoo_PostLoadSetup` — line 2970
- `EnsembleModelZoo_IsReadyForInference` — line 2989
- `CoreModelZoo_PostLoadSetup` — line 3030
- `CoreModelZoo_CheckStaleModel` — line 3063

### CostModel.hpp

- `CostModel_Estimate` — line 56 — k1, k2, k3:     cost coefficients
- `CostModel_EstimateDefault` — line 83 — convenience: estimate with default coefficients
- `CostModel_Breakeven` — line 93 — cost is in bps, divide by 10000 to get decimal return
- `CostModel_ShouldTrade` — line 98 — should we trade? returns 1 if expected alpha > breakeven

### EzooInitFlagRegistry.hpp

- `EzooInitFlag_ToString` — line 120 — CRITICAL log lines + diagnostic panels.

### FeatureRegistry.hpp

- `ML_Compute_ShortSlope` — line 116
- `ML_Compute_ShortR2` — line 121
- `ML_Compute_ShortVariance` — line 126
- `ML_Compute_LongSlope` — line 131
- `ML_Compute_LongR2` — line 136
- `ML_Compute_LongVariance` — line 141
- `ML_Compute_VolRatio` — line 146
- `ML_Compute_RorSlope` — line 151
- `ML_Compute_VolumeSlope` — line 156
- `ML_Compute_VolumeDelta` — line 161
- `ML_Compute_EmaSmaSpread` — line 180
- `ML_Compute_VwapDev` — line 185
- `ML_Compute_PriceStddev` — line 190
- `ML_Compute_PriceAvg` — line 195
- `ML_Compute_VolumeAvg` — line 200
- `ML_Compute_EmaAboveSma` — line 205
- `ML_Compute_MidSlope` — line 212
- `ML_Compute_MidR2` — line 217
- `ML_Compute_CumDelta` — line 222
- `ML_Compute_HourSin` — line 227
- `ML_Compute_HourCos` — line 232
- `ML_Compute_VolRegimeRatio` — line 237
- `ML_Compute_TickRateZ` — line 242
- `ML_Compute_DistToHigh` — line 247
- `ML_Compute_DistToLow` — line 252
- `ML_Compute_BookImbMeanShort` — line 257
- `ML_Compute_BookImbMeanLong` — line 262
- `ML_Compute_BookImbDrift` — line 267
- `ML_Compute_Flow10s` — line 272
- `ML_Compute_Flow1m` — line 277
- `ML_Compute_Flow5m` — line 282
- `ML_Compute_LargeTradeZ` — line 287
- `ML_Compute_SpreadBps` — line 292
- `ML_Compute_SpreadZscore` — line 297
- `ML_Compute_RegimeTrendStrength` — line 328
- `ML_Compute_RegimeVolZscore` — line 343
- `ML_Compute_RegimeClassOneHot` — line 365
- `ML_Compute_FracDiffPrice_d04` — line 436
- `ML_Compute_FracDiffPrice_d05` — line 441
- `ML_Compute_FracDiffPrice_d06` — line 446
- `Features_PackAll` — line 679
- `Features_PackAll` — line 761

### FeatureRegistryOverlay.hpp

- `FeatureOverlay_ParseLayer2HashFromSidecar` — line 66 — key and ":" handled).
- `FeatureOverlay_PostLoadVerify` — line 148

### FeatureStandardizer.hpp

- `FeatureStandardizer_Init` — line 172 — recommended for clarity.
- `FeatureStandardizer_Apply` — line 213 — MLStrategy.hpp:129, PortfolioController.hpp:1639/1806).
- `FeatureStandardizer_Load` — line 256 — magic / num_features / embedded SHA.
- `FeatureStandardizer_VerifyAgainstBuild` — line 356 — per held_out_gate_strict.
- `FeatureStandardizer_FitWinsor` — line 396 — training-side cost. Slow-path slow.
- `FeatureStandardizer_Compute` — line 434
- `FeatureStandardizer_Persist` — line 474 — Returns 1 on success, 0 on I/O failure.
- `FeatureStandardizer_Free` — line 536 — the struct so future use re-initializes).

### FlowFeatures.hpp

- `BookImbHistory_Init` — line 113
- `BookImbHistory_Push` — line 123
- `BookImbHistory_MeanLong` — line 153
- `BookImbHistory_MeanShortFast` — line 170
- `BookImbHistory_Last` — line 180
- `BookImbHistory_MeanShort` — line 189
- `FlowState_Init` — line 240
- `FlowState_Push` — line 253 — Full RegimeSignals→FPN_Binary cascade is a v5.11 ship (large blast radius).
- `LargeTradeState_Init` — line 333
- `LargeTradeState_Push` — line 343
- `LargeTradeState_ZScore` — line 366
- `LargeTradeState_Last` — line 382
- `SpreadState_Init` — line 430
- `SpreadState_Push` — line 440
- `SpreadState_ZScore` — line 458
- `SpreadState_Last` — line 473

### ModelInference.hpp

- `FeatureLookback_Max` — line 225 — used by: ValidationSplit (purge gap), PortfolioController (warmup check)
- `FeatureLookback_CountEnabled` — line 235 — count enabled features (for validation)
- `Model_Init` — line 425
- `Model_Load` — line 462
- `Model_Predict_Normalized` — line 621
- `Model_Predict_AtClass` — line 674
- `Model_LoadAOT` — line 703
- `Model_Predict_AOT` — line 717
- `Model_Predict` — line 733
- `Model_Predict_Ensemble` — line 827
- `Model_Predict_Ensemble_Weighted` — line 900
- `Model_PredictMulti` — line 1012
- `Model_Free` — line 1067
- `Model_IsLoaded` — line 1088
- `ModelFeatures_Pack` — line 1116

### PerArmFlagRegistry.hpp

- `PerArmFlag_ToString` — line 148 — diagnostic panels.

### RewardTracker.hpp

- `RewardTracker_Init` — line 37
- `RewardTracker_Push` — line 42
- `RewardTracker_DrainCSV` — line 59 — append all pending records to CSV, then clear

### RidgeBlender.hpp

- `Cholesky_Solve` — line 150
- `RidgeBlender_Compute` — line 285
- `RidgeBlender_FinalizeCorrFromSums` — line 378
- `RidgeBlender_BuildCorr` — line 474 — byte-determinism tests). Sister to Bandit_GetProbabilities. TECH_DEBT-158.
- `RidgeBlender_UpdateOnline` — line 563
- `RidgeBlender_BuildHistoryFromRing` — line 699
- `RidgeBlender_OnlineCycleStep` — line 758
- `RidgeWeights_Init` — line 806

### RollingStats.hpp

- `RollingStats_Push` — line 194
- `RollingStats_VolumeSignificant` — line 410
- `RollingStats_EntrySpacing` — line 423
- `RollingStats_BuyPrice` — line 440

### RollingTurnover.hpp

- `RollingTurnover_Init` — line 45 — Validates window + topk; clamps to safe range. Zero-init buffers.
- `RollingTurnover_Push` — line 112 — exactly K bits. Yields [0, 1] range.
- `RollingTurnover_Compute` — line 144 — until profiler flags this as load-bearing.

### ROR_regressor.hpp

- `RORRegressor_Init` — line 38
- `RORRegressor_Push` — line 60

### StampHelper.hpp

- `Stamp_AssembleAndEmit` — line 143

### ThompsonBandit.hpp

- `Thompson_RawToUniform` — line 114 — Muller's log(0) handling).
- `Thompson_BoxMuller_Pair` — line 126 — Caller must ensure u1, u2 ∈ [0, 1).
- `Thompson_Init` — line 144 — applied if caller passes <= 0 for prior/observation precision.
- `Thompson_InitDefault` — line 163 — Typical for unit tests + boot-time init before cfg fields wire in (.B).
- `Thompson_Update` — line 183 — No-op for invalid arm (defensive).
- `Thompson_Sample` — line 261 — Mutates tb->rng_state (advances the PRNG); not thread-safe.
- `Thompson_GetProbabilities` — line 308 — are zeroed.
- `Thompson_GetSoftmaxWeights` — line 361 — are zeroed. Defensive on nullptr / degenerate n_arms < 2.

### VolScaler.hpp

- `VolScaler_Size` — line 45 — positive = long, negative = short (we only go long in current engine)
- `VolScaler_SizeDefault` — line 60 — convenience: scale with default parameters
- `VolScaler_InverseAlpha` — line 68 — useful for: "what alpha does this position size imply?"
- `VolScaler_RawZ` — line 76 — raw z-score without clipping (for analytics / display)

### WelfordStats.hpp

- `Welford_Init` — line 28
- `Welford_Push` — line 40
- `Welford_Variance` — line 68
- `Welford_Stddev` — line 77
- `Welford_ZScore` — line 85
- `Welford_Reset` — line 94

## GUI/

### CandleAccumulator.hpp

- `CandleAccumulator_Init` — line 34
- `CandleAccumulator_Push` — line 41 — called from engine thread on every tick
- `CandleAccumulator_PushWithTime` — line 86 — instead of using wall-clock time(NULL)
- `CandleAccumulator_Snapshot` — line 132
- `CandleAccumulator_SetInterval` — line 157 — reset accumulator with new interval (clears all candle data)
- `CandleAccumulator_Destroy` — line 168

### ChartPanel.hpp

- `ChartState_Prepare` — line 67
- `GUI_PriceChart` — line 144
- `GUI_VolumeChart` — line 1166 — VOLUME CHART — separate dockable window
- `GUI_LivePnLChart` — line 1284 — LIVE P&L — streaming chart from pnl_history ring buffer
- `GUI_EquityChart` — line 1344 — EQUITY CURVE — separate dockable window (only renders with trade data)

### DashboardPanels.hpp

- `GUI_R2Bar` — line 28 — slope_dir: positive slope → green, negative → red, near zero → neutral
- `GUI_Panel_Header` — line 71 — PANEL: HEADER — fox kaomoji, version, state, uptime, session
- `GUI_Panel_TopBar` — line 196 — PANEL: TOP BAR — key metrics at a glance
- `GUI_Panel_Market` — line 233 — PANEL: MARKET (merged Market Structure + Regime Signals)
- `GUI_Panel_BuyGate` — line 439 — PANEL: BUY GATE
- `GUI_Panel_Account` — line 891 — PANEL: ACCOUNT (merged Portfolio + P&L + Risk)
- `GUI_Panel_Config` — line 1130 — PANEL: CONFIG
- `GUI_Panel_Positions` — line 1178 — PANEL: POSITIONS — proper table with aligned columns
- `GUI_Panel_PerCorePnL` — line 1461 — Pure GUI thread, doesn't touch engine state.
- `GUI_Panel_Stats` — line 1557 — PANEL: STATS
- `GUI_Panel_Latency` — line 1647 — PANEL: LATENCY (conditional on LATENCY_PROFILING)
- `GUI_Panel_MLIntelligence` — line 1703 — PANEL: ML INTELLIGENCE — bandit arms, confidence, cost, model info
- `GUI_RenderDashboard` — line 1888

### EngineHeaderPanel.hpp

- `EngineHeader_Render` — line 38 — nullptr (legacy callers), only the 3 build-time fields render.

### FoxmlTheme.hpp

- `Foxml_ApplyTheme` — line 45

### GuiThread.hpp

- `Gui_Init` — line 85 — GUI INIT
- `Gui_Shutdown` — line 222 — GUI SHUTDOWN
- `Gui_BeginFrame` — line 235 — GUI FRAME
- `Gui_EndFrame` — line 259
- `Gui_SetupDefaultLayout` — line 274 — chart 60% left, dashboard panels stacked 40% right
- `Gui_HandleKeys` — line 324 — GUI KEYBOARD — same controls as ANSI TUI

### LogViewerPanel.hpp

- `LogViewer_Init` — line 22
- `LogViewer_Refresh` — line 28
- `GUI_Panel_LogViewer` — line 57

### MLStatusPanel.hpp

- `MLStatus_Render` — line 38 — nullptr; the row is rendered only when a swap is actually pending.

### SettingsPanel.hpp

- `Settings_RescanModels` — line 801 — stays free of opendir/stat (per /readiness check 17 hardening).
- `Settings_Init` — line 859 — so Settings_Load knows where to read.
- `Settings_Load` — line 869
- `Settings_RenderGlobalTab` — line 1017 — GLOBAL TAB — renders the auto-generated field_defs[] layout
- `Settings_RenderPerCoreTab` — line 1249
- `GUI_Panel_Settings` — line 1683 — running cores, not cfg-only intent — engine doesn't add/remove cores live.

### StrategyQualityPanel.hpp

- `StrategyQuality_Init` — line 60 — log path is passed at render time via GUI_Panel_StrategyQuality).
- `StrategyQuality_Refresh` — line 160
- `GUI_Panel_StrategyQuality` — line 237

### TradeHistoryPanel.hpp

- `TradeHistory_Init` — line 35
- `TradeHistory_Refresh` — line 40
- `GUI_Panel_TradeHistory` — line 172

### TradeReader.hpp

- `TradeData_Init` — line 39
- `TradeData_Refresh` — line 76

## Backtest/

### BacktestEngine.hpp

- `BacktestData_DetectFormat` — line 61 — timestamp_us,price,quantity,is_buyer_maker
- `BacktestData_Load` — line 68
- `HistoricalTick_CmpByTime` — line 141 — Caller in STRICT mode should treat -1 as "abort run".
- `BacktestData_ValidateSort` — line 149
- `BacktestResults_Init` — line 275
- `BacktestResults_Free` — line 287
- `BacktestResults_Reset` — line 315 — against zero capacity (defense-in-depth) but this is the load-bearing fix.
- `BacktestResults_EnsureCapacity` — line 338 — grow sample buffers by 2x when full
- `BacktestResults_EnsureEquityCapacity` — line 365 — array, so silent truncation produces wrong Sharpe / max DD / return.
- `XGBoost_ComputeScalePosWeight` — line 398 — (0.0 = negative, 1.0 = positive, 0.5 = neutral and already filtered).
- `XGBoost_ComputeMulticlassWeights` — line 430 — receives per-class sample counts so caller can log them.
- `BacktestStats_Compute` — line 466 — fabs() inconsistency + 2-site max_drawdown reimplementation.
- `BacktestStats_ComputeFromEquity` — line 499 — sharpe — needs equity curve data too
- `BacktestSharded_Run` — line 537
- `Backtest_ComputeLabelsFromSamples` — line 585 — through samples; no per-file O(N) sample scans.
- `Backtest_Run` — line 845 — equity curve).
- `HeldOutSplit_TrainEval` — line 966 — helper has visibility into WalkForward_Compute* and XGBoost_Compute* funcs.
- `Backtest_RunWalkForward` — line 1050 — behavior bytewise.
- `Backtest_RunFullValidation` — line 1059
- `WalkForward_ComputeAccuracy` — line 1267 — uses > 0.5f for truth so neutral (0.5) labels are never counted as positive
- `WalkForward_ComputeMulticlassAccuracy` — line 1314 — argmax over each row, compare to integer truth (rounded from label float).
- `WalkForward_ComputeMSE` — line 1333 — regression: mean squared error. Lower = better. Sensitive to outliers.
- `WalkForward_ComputeCorrelation` — line 1349 — gets low MSE on small-magnitude targets while having zero predictive power).
- `Backtest_RunWalkForward` — line 1373
- `HeldOutSplit_TrainEval` — line 1995 — functions it uses (WalkForward_Compute*, XGBoost_Compute*) are visible.
- `ConfigField_Set` — line 2240 — handles both FPN_Binary and PCT fields (PCT keys are stored as decimal, value comes in as %).
- `Backtest_RunSweep` — line 2344
- `Backtest_RunHyperparamTrainSweep` — line 2434 — mean_val_correlation (regression). Stored as positive number; higher = better.

### BacktestPanels.hpp

- `DataPanel_Init` — line 52
- `DataPanel_Scan` — line 57
- `RunControl_Init` — line 158
- `SamplesSnapshot_Compute` — line 169 — only when running==0, giving a safe happens-before relationship.
- `RunControl_Start` — line 335
- `GUI_Panel_DataBrowser` — line 375
- `GUI_Panel_RunControl` — line 474
- `GUI_Panel_Results` — line 523
- `PastRuns_Init` — line 733
- `PastRuns_LoadOne` — line 773 — scan one run directory's metadata files
- `PastRuns_DeleteDir` — line 875
- `PastRun_ParseHorizon` — line 886 — out_horizon_ticks = 0).
- `PastRuns_ScanOneDir` — line 925
- `PastRuns_Scan` — line 947
- `PastRun_MetricLabel` — line 1017 — label-type-aware metric label
- `GUI_Panel_PastRuns` — line 1027 — Pass NULL to keep pre-v5.11.57 behavior (devmode-only).
- `Comparison_Init` — line 1900
- `Comparison_Free` — line 1904
- `Comparison_SaveRun` — line 1911
- `GUI_Panel_Comparison` — line 1952
- `OptimizerPanel_Init` — line 2102
- `GUI_Panel_Optimizer` — line 2140
- `TrainingPanel_Init` — line 2550
- `GUI_Panel_Training` — line 4164

### BacktestSharded.hpp

- `SharedBacktest_FromHistorical` — line 81
- `BacktestSharded_Run` — line 105 — aggregates results.

### BacktestSnapshot.hpp

- `BacktestSnapshot_Copy` — line 20

### Fingerprint.hpp

- `SHA256_Init` — line 78
- `SHA256_Update` — line 85
- `SHA256_Final` — line 103
- `SHA256_ToHex` — line 125 — convenience: hash to hex string (65 bytes including null terminator)
- `Fingerprint_HashFile` — line 140 — streams file through SHA256 in 64KB chunks — handles multi-GB files.
- `Fingerprint_Compute` — line 174
- `Fingerprint_Short` — line 203 — short fingerprint (first 12 hex chars) for display

### HeldOutSplit.hpp

- `HeldOutSplit_GenToken` — line 77 — non-reproducible by construction. Removed.
- `HeldOutSplit_Make` — line 92
- `HeldOutSplit_TestAccessAllowed` — line 125
- `HeldOutSplit_Unlock` — line 132 — Logs unlock event to stderr — caller can also Notify_Send for audit trail.
- `HeldOutSplit_Relock` — line 154 — not _Relock.

### LabelFunctions.hpp

- `Label_WinLoss` — line 79 — no trade was entered at that point.
- `Label_Barrier` — line 100 — same as win/loss but with configurable asymmetric barriers.
- `Label_ForwardPnl` — line 118 — useful for regression (predict magnitude, not just direction).
- `Label_Regime` — line 135 — useful for training a regime classifier model.
- `Label_VolBarrier` — line 158 — source: ~/FoxML/private/DATA_PROCESSING/targets/barrier.py
- `LabelType_NumClasses` — line 431 — ≥2 = multiclass softmax       (label values 0..K-1 as floats)
- `LabelType_IsBinary` — line 436
- `LabelType_IsRegression` — line 440
- `LabelType_IsMulticlass` — line 444

### OverfitDetection.hpp

- `OverfitDetection_CheckDefaults` — line 136 — convenience: check with default FoxML thresholds
- `OverfitDetection_CountOverfit` — line 225 — returns: number of folds flagged as overfit
- `OverfitDetection_Print` — line 236 — print report (for logging / debugging)

### PhaseTimers.hpp

- `PhaseTimer_Global` — line 48 — header inline-only (no separate .cpp).
- `PhaseTimer_Reset` — line 59
- `PhaseTimer_Summary` — line 75 — wf_eval / held_out_eval since it's nested inside both.
- `PhaseTimer_PopulateSnapshot` — line 117

### ValidationSplit.hpp

- `PurgeGap_Compute` — line 66 — first test tick to prevent any form of temporal leakage.
- `PurgeGap_ComputeExplicit` — line 73 — overload: caller provides explicit max_lookback (for testing or custom feature sets)
- `ValidationSplit_Generate` — line 126 — returns: number of valid folds generated (may be < n_splits if early folds skipped)
- `ValidationSplit_GenerateExplicit` — line 230 — used by walk-forward when splitting in non-neutral sample space where raw lookback doesn't apply
- `ValidationSplit_Verify` — line 296 — returns 1 if all folds are clean, 0 if leakage detected
- `ValidationSplit_Print` — line 317 — print fold summary (for logging / debugging)

### XGBHyperparams.hpp

- `XGBHyperparams_Defaults` — line 52 — modify the returned struct in-place.
- `XGBHyperparams_Apply` — line 62 — use 1 (deterministic per-fold output). Caller chooses.

---

## Top-level files

- `main.cpp` — 1320 lines
- `Version.hpp` — 1022 lines
- `Limits.hpp` — 30 lines

## Conventions

- Function names follow `Pattern_FunctionName` convention (e.g. `Portfolio_Init`, `BG_Evaluate`)
- Headers are inline-heavy — most functions live in `.hpp` and are `inline`
- Templates parameterize on `unsigned F` (frac-bits); FPN_Binary<64> = the 16B two's-complement binary core
- Lowercase helpers (`fan_out`, `drain_with_submit`) are local to a function and not in this map
- ALL_CAPS macros are not in this map; see headers directly
