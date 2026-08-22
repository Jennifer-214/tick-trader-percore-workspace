# CODE_MAP.md

Auto-generated function index. Walks .hpp files in each subsystem and extracts `Pattern_FunctionName` style definitions with their one-line purpose (from the preceding `//` comment, when present).

**Re-generate**: `./tools/gen_code_map.sh`

**Last regenerated**: 2026-08-21 (commit 6b1a9dd)

## CoreFrameworks/

### BinanceAdapter.hpp

- `BinanceAdapter_WorkerLoop` — line 203
- `BinanceAdapter_Init` — line 327 — shutdown_requested flips.
- `BinanceAdapter_ShutdownState` — line 403 — 1; future commits scale up after the back-to-back stress test passes.
- `BinanceAdapter_SubmitMarketBuy` — line 436 — without a successful Init (shutdown_requested is already 0 by default).
- `BinanceAdapter_SubmitMarketSell` — line 479 — holds with worker_count == 1.
- `BinanceAdapter_GetBalancesImpl` — line 513
- `BinanceAdapter_QueryOrderImpl` — line 548 — pausing submissions during a reconciliation pass.
- `BinanceAdapter_ShutdownImpl` — line 579
- `BinanceAdapter_Get` — line 598

### ControllerConfig.hpp

- `ControllerConfig_CapitalRangeSweep` — line 1529
- `Fee_Compute` — line 1658
- `ControllerConfig_ResolveForCore` — line 1711
- `ControllerConfig_PopulateCoresFromFlat` — line 1776
- `ControllerConfig_NormalizeForMode` — line 2376
- `ControllerConfig_IsLiveCapital` — line 2410
- `ControllerConfig_Load` — line 2456

### ControllerEventLoop.hpp

- `NodeSlowState_Init` — line 185
- `NodeContextDisplayMeta_Init` — line 812
- `Sharded_SlotNode` — line 1012 — early consumer precedes the definition (same tt namespace). (D-294)
- `EventLoopState_ReconstructPerCoreFromEventLog` — line 1015
- `EventLoopState_Init` — line 1128
- `EventLoopState_InitLegacy` — line 1185
- `EventLoopState_Free` — line 1218
- `EventLoopState_RegisterCore` — line 1279
- `Sharded_LegSlot` — line 1355 — All slow-path / boot-time. Trivially inlined.
- `Sharded_SlotNode` — line 1392 — and ShardedSnapshot.hpp. GUI sites grandfathered for the E-series decouple. (D-294/D-295)
- `Sharded_ValidatePartialExitCfg` — line 1405
- `EventLoopState_SetCoreStrategy` — line 1457
- `EventLoopState_AttachTradeLog` — line 1504
- `EventLoopState_AttachOms` — line 1521
- `EventLoopState_Balance` — line 1539
- `EventLoopState_RealizedPnl` — line 1544
- `EventLoopState_Portfolio` — line 1555
- `EventLoopState_PortfolioMut` — line 1560
- `EventLoopState_KsMinBalance` — line 1565
- `EventLoopState_KsMaxDrawdownPct` — line 1570
- `EventLoopState_KsPeakBalance` — line 1575
- `EventLoopState_TradeLog` — line 1591
- `EventLoopState_SetIntendedParams` — line 1606
- `EventLoop_DrainPostFillOneCore` — line 1641
- `EventLoop_DrainPostFill` — line 2090
- `EventLoop_OnEvent` — line 2176
- `EventLoop_DrainEvents` — line 2360
- `EventLoop_QueueParameters` — line 2403
- `EventLoop_RebuildAllParameters` — line 2441
- `EventLoop_UpdateRollingStateOneCore` — line 2549
- `EventLoop_UpdateEmaPriceAllCores` — line 2592
- `EventLoop_RebuildOneCore` — line 2643
- `EventLoop_PushParameters` — line 3611
- `EventLoopState_ConfigureKillSwitch` — line 3673
- `EventLoop_ClearAllPermissions` — line 3683
- `EventLoop_KillSwitchTrip` — line 3694
- `EventLoop_KillSwitchEvaluate` — line 3723
- `EventLoop_TimeExitOneCore` — line 3790
- `EventLoop_FlattenAll` — line 3894
- `EventLoop_CheckWsStaleness` — line 3976
- `EventLoop_TryClearRecovery` — line 4055
- `EventLoop_TrailingSLRatchetOneCore` — line 4122
- `EventLoop_BreakevenOnProfitOneCore` — line 4222
- `EventLoop_Unpause` — line 4296
- `EventLoop_SlowPath` — line 4320
- `EventLoop_RunController` — line 4345

### EngineCommon.hpp

- `EngineCommon_ApplyBnbDiscount` — line 164
- `EngineCommon_BootGlobal` — line 210
- `EngineCommon_BootPerCore` — line 267
- `EngineCommon_SlowPathCycleOneCore` — line 532
- `EngineCommon_SlowPathCycleAllCores` — line 917
- `EngineCommon_DrainPostFill` — line 970

### EventLoopAggregates.hpp

- `EventLoop_GetAggregates` — line 124

### ExecutionCore.hpp

- `ExecutionCore_Init` — line 281
- `ExecutionCore_SetParameters` — line 340
- `ExecutionCore_SetPermission` — line 375
- `ExecutionCore_Tick_Impl` — line 413
- `ExecutionCore_Tick` — line 809

### GateParameters.hpp

- `BG_Evaluate` — line 216
- `SG_Evaluate` — line 264
- `GateParameters_Init` — line 293

### HotSwap.hpp

- `HotSwap_ShadowLoad_Ensemble` — line 67
- `HotSwap_ShadowLoad_SingleZoo` — line 229

### LiveReadiness.hpp

- `LiveReadiness_Verify` — line 352

### MetricCompute.hpp

- `Compute_ProfitFactor` — line 52 — → backtest-suite layering boundary.
- `Compute_AllWinsRun` — line 58 — numerical profit_factor is 0.0 in this case, separately).
- `Compute_Expectancy` — line 62
- `Compute_WinRate` — line 74
- `Compute_AvgHoldTicks` — line 80
- `Compute_ReturnPct` — line 86
- `MaxDrawdown_UpdateIncremental` — line 97 — regression test needed.

### ModelValidation.hpp

- `NodeModelZoo_ValidateAgainstCfg` — line 149

### NodeLatencyStats.hpp

- `NodeLatencyStats_Init` — line 192
- `NodeLatencyStats_Reset` — line 224 — stats mid-run without disabling them.
- `NodeLatencyStats_Enable` — line 240
- `NodeLatencyStats_Disable` — line 244
- `NodeLatencyStats_Sample` — line 258
- `NodeLatencyStats_Snapshot` — line 300 — rdtsc reading at sample time, used for "last seen" tracking in the TUI.

### Notify.hpp

- `NotifyState_Init` — line 274 — drains remaining events before exiting (per test sidecar Group 5).
- `Notify_Send` — line 305
- `NotifyState_Shutdown` — line 374 — Drain remaining events + join worker thread + free pthread resources.
- `NotifyBackend_Stderr` — line 400
- `Notify_ShellEscape` — line 482
- `Notify_BuildCommand` — line 533 — Document this for users; provide a wrapper script if needed.
- `NotifyBackend_Command` — line 582 — overflowed before completion (still tries to run what fit).

### OrderEventLog.hpp

- `OrderEventLog_Init` — line 329
- `OrderEventLog_Free` — line 395
- `OrderEventLog_ApplyEvent` — line 436
- `OrderEventLog_Append` — line 484
- `OrderEventLog_AsyncWriterRoutine` — line 535
- `OrderEventLog_StartAsyncWriter` — line 583
- `OrderEventLog_StopAsyncWriter` — line 612
- `OrderEventLog_InitWithFile` — line 635
- `OrderEventLog_Reset` — line 724
- `OrderEventLog_LoadFromDisk` — line 780
- `OrderEvent_MakeFill` — line 886
- `OrderEvent_MakeRejection` — line 924
- `Portfolio_FromEventLog` — line 985

### OrderGates.hpp

- `Gate_Zero` — line 115
- `Gate_ZeroAll` — line 122

### Order.hpp

- `Order_GetType` — line 309
- `Order_SetType` — line 313
- `Order_GetState` — line 319
- `Order_SetState` — line 323
- `Order_GetIsMaker` — line 329
- `Order_SetIsMaker` — line 333
- `Order_SetLeg` — line 343
- `Order_SetRetryCount` — line 353
- `Order_GetPreResolvedBound` — line 362
- `Order_MarkPreResolvedBound` — line 366
- `MBS_OrderBanditActiveState` — line 382
- `MBS_OrderBanditRegime` — line 386
- `MBS_OrderBanditChosenArm` — line 390
- `MBS_OrderSetBanditContext` — line 394
- `Order_Init` — line 418
- `Order_BindPreResolved` — line 469
- `Order_WarnIfNotPreResolved` — line 511
- `Order_IsTerminal` — line 563

### OrderManager.hpp

- `OrderManager_Init` — line 972
- `OMS_PushSubmit` — line 1269
- `OMS_DrainSubmit` — line 1320
- `OrderManager_AccountMakerTakerFee` — line 1361
- `OMS_GuardTakerBoundFeeBasis` — line 1404
- `OrderManager_HandleFill` — line 1612
- `OrderManager_ProcessFillCommand` — line 1681
- `OMS_OpenPositionCost` — line 1804
- `OMS_ExpectedFreeCash` — line 1843
- `OrderManager_ProcessReconcile` — line 1888
- `OrderManager_Tick` — line 1935
- `OrderManager_Shutdown` — line 1982
- `OrderManager_OpenCalibrationLog` — line 2009
- `OrderManager_InflightCount` — line 2069

### PaperResetArchive.hpp

- `PaperResetArchive_FormatTimestamp` — line 101 — Uses localtime_r for thread safety. out_size should be >= 20.
- `PaperResetArchive_FormatDirname` — line 112 — out_size should be >= 128 (typical ISO string + path overhead ~80 chars).
- `PaperResetArchive_CreateDirectories` — line 130 — calling mkdir() incrementally.
- `Summary_WriteJson` — line 167

### ParameterSlot.hpp

- `ParameterSlot_Init` — line 163
- `ParameterSlot_Write` — line 196
- `ParameterSlot_Read` — line 263

### PortfolioController.hpp

- `PortfolioController_Init` — line 361
- `KillSwitch_Activate` — line 620
- `KillSwitch_Reset` — line 634
- `Buying_Halt` — line 643
- `PortfolioController_DrainExits` — line 850
- `PortfolioController_StrategyBuySignal` — line 893
- `PortfolioController_StrategyDispatch` — line 984
- `PortfolioController_Tick` — line 1040
- `PortfolioController_Unpause` — line 2062
- `PortfolioController_CycleRegime` — line 2073
- `PortfolioController_HotReload` — line 2099

### Portfolio.hpp

- `ExitBuffer_PendingProceeds` — line 328
- `Portfolio_AddPositionWithExits` — line 438
- `Portfolio_OpenSlot` — line 566
- `Portfolio_OpenSlot` — line 609
- `Money_FillGross` — line 635
- `Portfolio_CloseSlot` — line 662
- `Portfolio_SlotActive` — line 675
- `Portfolio_UpdatePosition` — line 685

### Reconcile.hpp

- `ReconcileMode_ToString` — line 165 — Mode → string for logging. Uses cfg_string field (operator-friendly).
- `ReconcileMode_FromString` — line 178 — parse OR error). Accepts cfg_string values from registry.
- `Reconcile_ApplyMissedFills` — line 251
- `Reconcile_AutoCancelStale` — line 430
- `Reconcile_ParseOpenOrders` — line 676
- `Reconcile_ParseMyTrades` — line 722 — Output: fills `out` array up to `out_cap`. Returns count parsed.
- `Reconcile_Decide` — line 766 — Output: fills `out` array up to `out_cap`. Returns count parsed.
- `Reconcile_LogReport` — line 844 — Outputs ReconcileResult with planned actions. Caller applies them.

### ReconciliationLoop.hpp

- `ReconciliationLoop_Pass` — line 132
- `ReconciliationLoop_Init` — line 252
- `ReconciliationLoop_Start` — line 287
- `ReconciliationLoop_TriggerNow` — line 295
- `ReconciliationLoop_Shutdown` — line 309

### ShardedBacktestDriver.hpp

- `ShardedBacktestDriver_Init` — line 176
- `ShardedBacktest_RunTick` — line 237
- `ShardedBacktest_Run` — line 458

### ShardedLiveSafety.hpp

- `EngineSharded_OrphanRecovery` — line 58
- `EngineSharded_ForceCloseOnShutdown` — line 169

### ShardedOrderLatency.hpp

- `ShardedOrderLatency_Reset` — line 80 — before the first order can fire.
- `ShardedOrderLatency_Sample` — line 97

### ShardedSnapshot.hpp

- `TUI_CopySnapshotSharded` — line 58

### ShardedSnapshotPersist.hpp

- `ShardedSnapshot_Save` — line 138
- `ShardedSnapshot_Load` — line 269

### ShardedTradeLog.hpp

- `ShardedTradeLog_FormatPerCoreFilename` — line 130
- `ShardedTradeLog_WriteRow` — line 163 — the next consumer would silently drift. Helper makes drift impossible.
- `ShardedTradeLog_Init` — line 206 — non-fatal — aggregate file already has the row.
- `ShardedTradeLog_Flush` — line 311 — without a trade log, you just don't get the CSV.
- `ShardedTradeLog_Rotate` — line 339 — called once at engine shutdown.
- `ShardedTradeLog_Close` — line 425 — the existing file open).
- `ShardedTradeLog_RecordEntry` — line 456
- `ShardedTradeLog_RecordExit` — line 526

### SPSCRing.hpp

- `SPSCRing_Init` — line 146
- `SPSCRing_TryPush` — line 171
- `SPSCRing_TryPop` — line 252
- `SPSCRing_Depth` — line 300
- `SPSCRing_Capacity` — line 320

### SpSectionRegistry.hpp

- `SP_SECTION_NAME` — line 52
- `SP_SECTION_DOC` — line 60

### StampBoundDerivedFilter.hpp

- `STAMP_BOUND_CFG_emit_canonical_body` — line 56

### TradeLogColRegistry.hpp

- `TradeLog_EmitHeader` — line 71 — for the original 11 columns.

## Strategies/

### MeanReversion.hpp

- `MeanReversion_Init` — line 101
- `MeanReversion_Adapt` — line 140
- `MeanReversion_BuySignal` — line 317
- `MeanReversion_ExitAdjust` — line 463
- `MeanReversion_ExitAdjustSharded` — line 570

### MLStrategy.hpp

- `MLStrategy_Init` — line 82
- `MLStrategy_Adapt` — line 114
- `MLStrategy_Adapt_Canonical` — line 132
- `MLStrategy_BuySignal` — line 155
- `MLStrategy_ExitAdjust` — line 259
- `MLStrategy_ExitAdjustSharded` — line 324

### Momentum.hpp

- `Momentum_Init` — line 88
- `Momentum_Adapt` — line 121
- `Momentum_BuySignal` — line 217
- `Momentum_ExitAdjust` — line 307
- `Momentum_ExitAdjustSharded` — line 388

### RegimeDetector.hpp

- `CumDelta_Init` — line 209
- `CumDelta_Push` — line 227
- `TickRate_Init` — line 282 — current rate's z-score is informative for burst detection.
- `TickRate_Push` — line 290
- `TickRate_CurrentZ` — line 317
- `Regime_ComputeSignals` — line 341
- `RegimeState_FieldwiseWrite` — line 651
- `RegimeState_FieldwiseRead` — line 660
- `RegimeState_CommitPersistedFields` — line 671
- `Regime_Init` — line 706
- `Regime_Classify` — line 745
- `Regime_ToStrategy` — line 899
- `Regime_AdjustPositions` — line 917

### SimpleDip.hpp

- `SimpleDip_Init` — line 61
- `SimpleDip_Adapt` — line 72
- `SimpleDip_BuySignal` — line 94
- `SimpleDip_ExitAdjustSharded` — line 137

### StrategyLifecycle.hpp

- `Strategy_SeedFromCfg` — line 76
- `Strategy_SeedFromCfg` — line 81
- `Strategy_SeedFromCfg` — line 95
- `Strategy_FreePerCore` — line 115
- `Strategy_InitPerCore` — line 118
- `Strategy_AdaptPerCore` — line 197
- `Strategy_WriteRatchetSL` — line 292
- `Strategy_WriteRatchetTP` — line 332
- `Strategy_ExitAdjustPerCore` — line 381
- `Strategy_FreePerCore` — line 444

### StrategyParameters.hpp

- `Strategy_SpacingOk` — line 277
- `Strategy_TpFloor` — line 296
- `GateEgress_MaxPct` — line 320 — FinalizeEmit's range-validate AND the leg-B tp_pct_b clamp below (the A-class leg-B leak fix).
- `GateParameters_FinalizeEmit` — line 323
- `SimpleDip_BuildParameters` — line 437
- `MeanReversion_BuildParameters` — line 520
- `Momentum_BuildParameters` — line 613
- `EmaCross_BuildParameters` — line 745
- `ML_BuildParameters` — line 863
- `Strategy_BuildParameters` — line 1953

## Strategies/private/

### EmaCross.hpp

- `EmaCross_Init` — line 70
- `EmaCross_Adapt` — line 85
- `EmaCross_BuySignal` — line 103
- `EmaCross_ExitAdjust` — line 165
- `EmaCross_ExitAdjustSharded` — line 254

## DataStream/

### BinanceCrypto.hpp

- `BinanceStream_Init` — line 587 — as a min-size sanity guard catches truncated frames without scanning.
- `BinanceStream_Close` — line 660 — clean shutdown: send close frame, SSL shutdown, close socket, free resources
- `BinanceStream_Reconnect` — line 695
- `BinanceStream_Poll` — line 743
- `BinanceStream_ReadTick` — line 808
- `BinanceStream_InWindDown` — line 909 — returns 1 on success (out filled with price + volume), 0 on error/disconnect
- `BinanceStream_ShouldReconnect` — line 922
- `BinanceStream_HasPending` — line 937 — returns 1 if SSL has buffered data that can be read without blocking
- `BinanceConfig_Load` — line 989

### BinanceDepth.hpp

- `DepthStream_Init` — line 296

### BinanceOrderAPI.hpp

- `BinanceOrderAPI_Cleanup` — line 585
- `BinanceOrderAPI_MarketBuy` — line 595 — fill_price_out/fill_qty_out receive actual execution values (NULL = don't care)
- `BinanceOrderAPI_MarketSell` — line 659 — place a market sell order
- `BinanceOrderAPI_CancelOrder` — line 739 — different operator semantics.
- `BinanceOrderAPI_GetStatus` — line 773 — fills filled_qty and avg_price on success
- `BinanceOrderAPI_LoadFilters` — line 822 — returns 1 on success, 0 on failure (caller should treat as fatal)
- `BinanceOrderAPI_GetBalance` — line 857 — returns 1 on success, 0 on failure
- `BinanceOrderAPI_GetOpenOrders` — line 889 — network-independent (testable without real REST calls).
- `BinanceOrderAPI_GetMyTrades` — line 900 — the last-known-processed trade id to catch only new fills.
- `BinanceOrderAPI_GetBalances` — line 916 — returns 1 on success, 0 on failure
- `BinanceOrderAPI_SyncClock` — line 940 — re-sync clock offset (call periodically or after reconnect)
- `BinanceOrderAPI_Init` — line 954 — must be called after Cleanup, ServerTime, SyncClock, LoadFilters are defined

### BinanceUserData.hpp

- `BinanceUserData_Init` — line 689
- `BinanceUserData_Start` — line 725
- `BinanceUserData_Shutdown` — line 731

### CalibLogColRegistry.hpp

- `CalibLog_EmitHeader` — line 177 — Adding a 9th arm later: append 4 more rows + bump BANDIT_MAX_ARMS at BanditLearning.hpp.

### DepthRecorder.hpp

- `DepthRecorder_MkdirP` — line 103
- `DepthRecorder_DateInt` — line 118
- `DepthRecorder_OpenFile` — line 126
- `DepthRecorder_PruneOld` — line 162
- `DepthRecorder_Init` — line 197
- `DepthRecorder_LogGap` — line 233 — disconnect time, or the current snapshot's timestamp_us).
- `DepthRecorder_Write` — line 261
- `DepthRecorder_Close` — line 314

### DepthReplayState.hpp

- `DepthReplay_DateInt` — line 119
- `DepthReplayState_Init` — line 137
- `DepthReplayState_Free` — line 172
- `DepthReplayState_LoadDay` — line 205
- `DepthReplayState_Advance` — line 322
- `DepthReplayState_GetSnapshot` — line 347

### EngineTUI.hpp

- `TUI_Init` — line 175
- `TUI_Cleanup` — line 208
- `TUI_Render` — line 236
- `TUI_HandleInput` — line 628
- `MLSnapshot_Populate` — line 777
- `TUISnapshot_InitSeq` — line 1582 — populated" state) — this only initializes the sequence counter.
- `TUISnapshot_Publish_Begin` — line 1597 — the new active.
- `TUISnapshot_Publish_End` — line 1613 — Any subsequent reader sees the just-filled buffer as active.
- `TUISnapshot_ReadInto` — line 1625 — effectively never observed.
- `TUI_CopySnapshot` — line 1663
- `TUI_CopySnapshot` — line 1669
- `TUI_CopySnapshot` — line 1676
- `TUI_PopulatePerCoreLatency` — line 1955
- `TUI_PopulatePerCoreSlowPathLatency` — line 2005
- `TUI_PopulateAdvancedTopology` — line 2044
- `TUI_PopulateTopology` — line 2088 — poll_interval[i]    — per-core resolved poll cadence
- `TUI_Render_Snapshot` — line 2145 — both dependencies are available.
- `TUI_ReadKey` — line 2356

### FauxFIX.hpp

- `FIX_ParseTag` — line 111 — returns the tag number, writes value start and length into out params
- `FIX_ParseDouble` — line 142 — not meant to be fast, just correct enough for test data
- `FIX_Parse` — line 218 — validates checksum if tag 10 is present
- `FIX_BuildMarketDataMsg` — line 312 — let the caller filter by entry_type if they care

### MetricsLog.hpp

- `MetricsLog_Init` — line 56
- `MetricsLog_Close` — line 78
- `MetricsLog_SlowPath` — line 119
- `MetricsLog_Event` — line 170

### MockGenerator.hpp

- `MockRNG_Seed` — line 44
- `MockRNG_Double` — line 55 — returns a double in [0.0, 1.0)
- `MockRNG_Range` — line 60 — returns a double in [lo, hi)
- `MockGenerator_Init` — line 119
- `MockGenerator_NextTick` — line 148
- `MockGenerator_Batch` — line 178 — buf is scratch space for building FIX messages (reused each tick)

### TickRecorder.hpp

- `TickRecorder_MkdirP` — line 82
- `TickRecorder_DateInt` — line 97
- `TickRecorder_OpenFile` — line 110
- `TickRecorder_PruneOld` — line 145
- `TickRecorder_Init` — line 180
- `TickRecorder_Push` — line 212
- `TickRecorder_Close` — line 246

### TradeLog.hpp

- `TradeLog_Init` — line 128
- `TradeLog_Buy` — line 161
- `TradeLog_Sell` — line 174
- `TradeLog_Close` — line 186
- `TradeLogBuffer_Init` — line 244
- `TradeLogBuffer_PushBuy` — line 250 — hot path: push a record to the ring buffer (~10ns, no file I/O)
- `TradeLogBuffer_PushSell` — line 269
- `TradeLogBuffer_Drain` — line 291 — slow path: drain all buffered records to the CSV file

### TUIAnsi.hpp

- `ANSI_Section_Header` — line 380
- `ANSI_Section_TopBar` — line 454
- `ANSI_Section_Market` — line 485
- `ANSI_Section_Regime` — line 529 — new section: shows R², vol_ratio, ror_slope that weren't in previous TUI backends
- `ANSI_Section_BuyGate` — line 640
- `ANSI_Section_Portfolio` — line 716
- `ANSI_Section_PnL` — line 755
- `ANSI_Section_Risk` — line 780
- `ANSI_Section_Config` — line 808
- `ANSI_Section_Stats` — line 835
- `ANSI_Section_Positions` — line 896
- `ANSI_Section_Charts` — line 973
- `ANSI_Section_Controls` — line 1013
- `ANSI_Section_Latency` — line 1029
- `ANSI_Section_PerNodeLatency` — line 1068 — per-core latency the moment they flip engine_mode=sharded.
- `ANSI_Section_RightPanel` — line 1120 — hidden on narrow terminals (< 100 columns)
- `ANSI_Layout_Standard` — line 1181
- `ANSI_Layout_Charts` — line 1227 — ANSI_Section_RightPanel(ab, s, h, w, start_time);
- `ANSI_Layout_Compact` — line 1265
- `ANSI_Layout_Render` — line 1280
- `ANSI_Render` — line 1302 — call from TUI thread at desired FPS

## FixedPoint/

### FixedPointN.hpp

- `FPN_BlendOnMask` — line 690
- `Money_Mul` — line 1877
- `Money_Div` — line 1918
- `Money_Add` — line 1955 — integer ops with a closure clamp + S-17 flag). Branchless mask-select clamp by the result sign.
- `Money_Add` — line 1963
- `Money_FromString` — line 2127
- `Money_FromBinary` — line 2208
- `Money_Zero` — line 2237 — lower to cmov (same shape as fp2_min/max); BlendOnMask mirrors the live <64> mask-select.
- `Money_Negate` — line 2238
- `Money_Abs` — line 2239
- `Money_Min` — line 2240
- `Money_Max` — line 2241
- `Money_IsZero` — line 2242
- `Money_Lt` — line 2243
- `Money_Le` — line 2244
- `Money_Eq` — line 2245
- `Money_Gt` — line 2246
- `Money_Ge` — line 2247
- `Money_QuantizeToStep` — line 2260
- `Money_BlendOnMask` — line 2282 — NEVER a plain wide divide (no __udivti3 on any path).
- `Money_FromInt` — line 2287 — Money_FromInt: whole-unit int -> money (i*10^8), clamp+flag past the closure ceiling.
- `Money_ToDouble` — line 2296 — Money_ToDouble — DISPLAY-ONLY (H4-exempt): GUI/diag/inf-bridge consumption. Never accounting.
- `Money_ToCString` — line 2361

## MemHeaders/

### DrainerConstants.hpp

- `DrainerConstants_Init` — line 123

### HealthLog.hpp

- `HealthLog_Singleton` — line 134 — Process-singleton. Engine init writes; all callers read.
- `Health_LogConfigureWithRotation` — line 152 — directory still doesn't exist).
- `Health_LogConfigure` — line 188
- `Health_LogPruneRotated` — line 200 — Health_Log (would loop).
- `Health_LogEnabled` — line 229 — "level <= min_level" emits.
- `Health_Log` — line 240 — Returns 1 on success, 0 on i/o failure (ignored by most callers).
- `Health_LogCriticalRateLimited` — line 358 — double-emit-once on race, not data corruption).

### InitArena.hpp

- `InitArena_Create` — line 109 — reservation gets a non-fatal degraded-but-functional path.
- `InitArena_Alloc` — line 154 — are 8 (for plain structs) or 64 (for cache-line-aligned hot structures).
- `InitArena_AllocOne` — line 179
- `InitArena_Destroy` — line 185 — struct). After Destroy, the arena is empty and capacity=0.
- `InitArena_Used` — line 202 — Introspection: how many bytes have been allocated from the arena so far.
- `InitArena_Remaining` — line 208 — is unknown; this is an upper bound).
- `InitArena_Owns` — line 220 — ctrl->rolling_long = nullptr;
- `InitArena_Global` — line 239 — spawn and after they join.

### LatencyHistogram.hpp

- `LatencyHistogram_Reset` — line 170 — instrumentation overhead bound for bench gate ON-state.
- `LatencyHistogram_Accumulate` — line 192

### NodeCtxSummaryFieldRegistry.hpp

- `Summary_EmitPerCoreEntry` — line 239
- `Summary_EmitPerStrategy` — line 280

### OmsPhasedDrain.hpp

- `OmsDrainBuckets_Reset` — line 134
- `OrderType_IsClose` — line 154
- `OrderManager_DrainIntoBuckets` — line 280
- `OrderManager_ProcessBucket_Closes` — line 337
- `OrderManager_ProcessBucket_Opens` — line 353
- `OrderManager_ProcessBucket_Reconciles` — line 366

### OmsPushExitHelper.hpp

- `OMS_PushExitForSlot` — line 77

### RunHistory.hpp

- `RunHistory_Append` — line 115 — defense-in-depth for the HMAC/stamp-adjacent byte-equivalence path.)

## ML_Headers/

### BanditAlgorithmRegistry.hpp

- `BanditAlgo_Exp3_Apply` — line 59 — cfg=2 reassigns to Exp3_Drives_Thompson_Ghost_Apply per Option C wire-preserving expansion).
- `BanditAlgo_Thompson_Apply` — line 62
- `BanditAlgo_Exp3_Drives_Thompson_Ghost_Apply` — line 65
- `BanditAlgo_Thompson_Drives_Exp3_Ghost_Apply` — line 68
- `BanditAlgo_Blended_Apply` — line 71
- `BanditAlgorithm_ToString` — line 185
- `BanditAlgorithm_FromString` — line 197 — CRITICAL operator error — don't silently default).
- `BanditAlgorithm_Apply` — line 222 — parse failure; the safe fallback is the bytewise-identical default path.
- `BanditAlgo_Exp3_Apply` — line 250 — default). Thompson state + blend_alpha ignored.
- `BanditAlgo_Thompson_Apply` — line 280 — + blend_alpha ignored. Posterior state advances (rng_state mutates) as part of sampling.
- `BanditAlgo_Exp3_Drives_Thompson_Ghost_Apply` — line 308 — (Class 24 fix — pre-.F.4d Thompson never updated despite mode being settable).
- `BanditAlgo_Thompson_Drives_Exp3_Ghost_Apply` — line 344 — Both bandits update from per-arm reward signal downstream (per-arm observability invariant).
- `BanditAlgo_Blended_Apply` — line 375 — weights via cmov (H20 / Class 28 prevention). Per § J of .F.4d merged plan body.

### BanditLearning.hpp

- `BanditDisplayMeta_InitDefault` — line 96 — BanditDisplayMeta_SetArmName.
- `BanditDisplayMeta_SetArmName` — line 108 — Set a custom human-readable name for an arm (display only).
- `Bandit_Init` — line 203
- `Bandit_InitDefault` — line 226 — convenience: init with default FoxML parameters
- `Bandit_GetProbabilities` — line 254 — tests. Suppress asan here; ubsan + the normal -O3 build still exercise it. (TECH_DEBT-158 close-out.)
- `Bandit_Select` — line 346
- `Bandit_Update` — line 385 — eta    = min(eta_max, sqrt(ln(K) / (K * T)))
- `Bandit_GetWeights` — line 441
- `Bandit_EffectiveBlend` — line 470 — final = (1 - effective_blend) * static + effective_blend * bandit
- `Bandit_BlendWeights` — line 479
- `Bandit_Print` — line 527 — steps >= min+ramp:             effective_blend = blend_ratio
- `Bandit_SaveJSON` — line 574
- `Bandit_LoadJSON` — line 807 — caller's prior Bandit_Init call — load is overlay only.

### BarrierBlendModeRegistry.hpp

- `BarrierBlendMode_BlendDrives` — line 136 — mode is compile-time-known.
- `BarrierBlendMode_DominantDrives` — line 140
- `BarrierBlendMode_ShadowActive` — line 144
- `BarrierBlendMode_IsLegacy` — line 148
- `BarrierBlendMode_ToString` — line 159 — and stamp body cfg-drift comparison.
- `BarrierBlendMode_FromString` — line 168
- `BarrierBlendMode_Doc` — line 179

### BarrierGate.hpp

- `BarrierGate_Compute` — line 76 — compute barrier gate value from peak/valley predictions

### ConfidenceScore.hpp

- `RollingWindow_Init` — line 153
- `RollingWindow_Push` — line 162
- `RollingIC_Init` — line 268 — v5.15.5.E.C — Init via generic RollingWindow_Init on both rings.
- `RollingIC_Push` — line 277 — the parallel-array push semantics for the (prediction, actual) pair shape.
- `RollingIC_RestoreLockstep` — line 302 — both rings from cfg, so they are already equal (and equal is all lockstep needs).
- `RollingIC_Compute` — line 343 — RollingIC_Push). Read either; using predictions's metadata canonically.
- `RollingRMSE_Init` — line 469
- `RollingRMSE_Push` — line 492 — in controller_test.cpp.
- `RollingRMSE_Compute` — line 515 — pattern (the spec tracks its production sites).
- `Confidence_Freshness` — line 543 — stability: 1 / (1 + RMSE)
- `Confidence_Stability` — line 549
- `Confidence_Compute` — line 553
- `RollingFreshness_Init` — line 631
- `RollingFreshness_Mark` — line 636
- `RollingFreshness_Compute` — line 643 — or replay determinism), clamp to 1.0.
- `RollingCapacity_Init` — line 700
- `RollingCapacity_UpdateADV` — line 707
- `RollingCapacity_Compute` — line 717
- `ConfidenceScorer_Init` — line 856
- `ConfidenceScorer_ComputeICVariant` — line 892 — New code + sites being refactored for variant choice use this dispatcher.
- `ConfidenceScorer_InitComposite` — line 900 — explicit composite parameters. Useful for tests + v5.14.1.B cfg wiring.
- `ConfidenceScorer_BindCompositeCfg` — line 930 — FPN_ToDouble(cfg.confidence_rmse_baseline));
- `ConfidenceScorer_Update` — line 943 — feed a prediction + actual return pair (call after outcome is known)
- `ConfidenceScorer_UpdateAndMark` — line 956 — when composite is disabled (composite path is opt-in via cfg).
- `ConfidenceScorer_Compute` — line 965 — compute current confidence given data age
- `ConfidenceScorer_ComputeComposite` — line 989 — stability_normalized = 1 - clamp(rmse / rmse_baseline, 0, 1)
- `ConfidenceScorer_MarkPredict` — line 1017 — fixture control.
- `Confidence_DegradationScale_Off` — line 1090 — Forward-declare curve compute fns so the dispatch table can reference them.
- `Confidence_DegradationScale_Linear` — line 1091
- `Confidence_DegradationScale_Exp` — line 1092
- `Confidence_DegradationScale_Step` — line 1093
- `DegradationCurve_ToString` — line 1129 — Auto-generated ToString — for cfg parser + GUI display.
- `DegradationCurve_FromString` — line 1140 — numeric ("1") forms; case-insensitive on string form. Returns -1 on miss.
- `Confidence_DegradationScale_Off` — line 1165 — when cfg.risk_degradation_curve=0 (default).
- `Confidence_DegradationScale_Linear` — line 1173 — To get ladder-bottom (factor=0), operator sets min_pct=0.0.
- `Confidence_DegradationScale_Exp` — line 1183 — as LINEAR.
- `Confidence_DegradationScale_Step` — line 1194 — without continuous-curve noise.
- `Confidence_DegradationScale` — line 1202 — out-of-range returns 1.0 (degrades safely to OFF behavior).
- `DriftHistory_Init` — line 1366
- `DriftHistory_Push` — line 1374 — + ts_us[idx], 2 separate cache lines 2048B apart).
- `DriftHistory_CheckBreach` — line 1392 — at typical 10-100Hz cadence.
- `ConfidenceScorer_FieldwiseWrite` — line 1454
- `ConfidenceScorer_FieldwiseRead` — line 1463
- `ConfidenceScorer_RecomputeRunningSums` — line 1475
- `ConfidenceScorer_CommitPersistedFields` — line 1477
- `ConfidenceScorer_RecomputeRunningSums` — line 1532 — must call this itself — that is the contract, not an exception list.

### CostModel.hpp

- `CostModel_Estimate` — line 95 — k1, k2, k3:     cost coefficients
- `CostModel_EstimateDefault` — line 122 — convenience: estimate with default coefficients
- `CostModel_Breakeven` — line 132 — cost is in bps, divide by 10000 to get decimal return
- `CostModel_ShouldTrade` — line 137 — should we trade? returns 1 if expected alpha > breakeven

### EzooInitFlagRegistry.hpp

- `EzooInitFlag_ToString` — line 117 — CRITICAL log lines + diagnostic panels.

### FeatureRegistry.hpp

- `ML_Compute_ShortSlope` — line 163
- `ML_Compute_ShortR2` — line 168
- `ML_Compute_ShortVariance` — line 173
- `ML_Compute_LongSlope` — line 178
- `ML_Compute_LongR2` — line 183
- `ML_Compute_LongVariance` — line 188
- `ML_Compute_VolRatio` — line 193
- `ML_Compute_RorSlope` — line 198
- `ML_Compute_VolumeSlope` — line 203
- `ML_Compute_VolumeDelta` — line 208
- `ML_Compute_EmaSmaSpread` — line 227
- `ML_Compute_VwapDev` — line 232
- `ML_Compute_PriceStddev` — line 237
- `ML_Compute_PriceAvg` — line 242
- `ML_Compute_VolumeAvg` — line 247
- `ML_Compute_EmaAboveSma` — line 252
- `ML_Compute_MidSlope` — line 259
- `ML_Compute_MidR2` — line 264
- `ML_Compute_CumDelta` — line 269
- `ML_Compute_HourSin` — line 274
- `ML_Compute_HourCos` — line 279
- `ML_Compute_VolRegimeRatio` — line 284
- `ML_Compute_TickRateZ` — line 289
- `ML_Compute_DistToHigh` — line 294
- `ML_Compute_DistToLow` — line 299
- `ML_Compute_BookImbMeanShort` — line 304
- `ML_Compute_BookImbMeanLong` — line 309
- `ML_Compute_BookImbDrift` — line 314
- `ML_Compute_Flow10s` — line 319
- `ML_Compute_Flow1m` — line 324
- `ML_Compute_Flow5m` — line 329
- `ML_Compute_LargeTradeZ` — line 334
- `ML_Compute_SpreadBps` — line 339
- `ML_Compute_SpreadZscore` — line 344
- `ML_Compute_RegimeTrendStrength` — line 375
- `ML_Compute_RegimeVolZscore` — line 390
- `ML_Compute_RegimeClassOneHot` — line 412
- `ML_Compute_FracDiffPrice_d04` — line 483
- `ML_Compute_FracDiffPrice_d05` — line 488
- `ML_Compute_FracDiffPrice_d06` — line 493
- `Features_PackAll` — line 724
- `Features_PackAll` — line 806

### FeatureRegistryOverlay.hpp

- `FeatureOverlay_ParseLayer2HashFromSidecar` — line 80 — key and ":" handled).
- `FeatureOverlay_PostLoadVerify` — line 162

### FeatureStandardizer.hpp

- `FeatureStandardizer_Init` — line 203
- `FeatureStandardizer_Apply` — line 246 — recommended for clarity.
- `FeatureStandardizer_Load` — line 319
- `FeatureStandardizer_VerifyAgainstBuild` — line 435 — has_scaler=1 if all upstream checks (registry_hash match) pass.
- `FeatureStandardizer_FitWinsor` — line 479 — training-side cost. Slow-path slow.
- `FeatureStandardizer_Compute` — line 517
- `FeatureStandardizer_Persist` — line 557 — Returns 1 on success, 0 on I/O failure.
- `FeatureStandardizer_Free` — line 634 — Persist writes the sidecar via atomic write (.tmp + rename).

### FlowFeatures.hpp

- `BookImbHistory_Init` — line 162
- `BookImbHistory_Push` — line 172
- `BookImbHistory_MeanLong` — line 202
- `BookImbHistory_MeanShortFast` — line 219
- `BookImbHistory_Last` — line 229
- `BookImbHistory_MeanShort` — line 238
- `FlowState_Init` — line 333
- `FlowState_Push` — line 346 — Full RegimeSignals→FPN_Binary cascade is a v5.11 ship (large blast radius).
- `LargeTradeState_Init` — line 469
- `LargeTradeState_Push` — line 479
- `LargeTradeState_ZScore` — line 502
- `LargeTradeState_Last` — line 518
- `SpreadState_Init` — line 612
- `SpreadState_Push` — line 622
- `SpreadState_ZScore` — line 640
- `SpreadState_Last` — line 655

### LinearRegression3X.hpp

- `RegressionFeederX_FieldwiseWrite` — line 111
- `RegressionFeederX_FieldwiseRead` — line 120
- `RegressionFeederX_CommitPersistedFields` — line 129

### ModelInference.hpp

- `FeatureLookback_Max` — line 286
- `FeatureLookback_CountEnabled` — line 296 — count enabled features (for validation)
- `Model_Init` — line 530
- `Model_Load` — line 578
- `Model_Predict_Normalized` — line 713
- `Model_Predict_AtClass` — line 776
- `Model_PrimaryBuyClassIdx` — line 838 — Model_Predict_AtClass(m, features, n, m->buy_class_idx).
- `Model_ExitClassIdx` — line 870 — unspottable by reading either site alone.
- `Model_LoadAOT` — line 900
- `Model_Predict_AOT` — line 914
- `Model_Predict` — line 958
- `Model_Predict_Ensemble` — line 1044
- `Model_Predict_Ensemble_Weighted` — line 1132
- `Model_PredictMulti` — line 1277
- `Model_Free` — line 1353
- `Model_IsLoaded` — line 1373
- `ModelFeatures_Pack` — line 1397

### NodeModelZoo.hpp

- `NodeModelZoo_Init` — line 159
- `Model_RoleCheckDecide` — line 195
- `NodeModelZoo_TryLoadRole` — line 208
- `NodeModelZoo_LoadFromDir` — line 726
- `NodeModelZoo_LoadLegacy` — line 844
- `NodeModelZoo_Free` — line 854
- `NodeModelZoo_HasAny` — line 863
- `NodeModelZoo_VerifyExpected` — line 901 — features in the pack, model crashes or produces garbage.
- `EnsembleZoo_FinalizeCorrupt` — line 1478
- `EnsembleModelZoo_Init` — line 1519
- `EnsembleModelZoo_EnsurePrimary` — line 1612
- `EnsembleModelZoo_RecordPrediction` — line 1672
- `EnsembleModelZoo_UpdateDrift` — line 1701
- `EnsembleModelZoo_TickRewardsFromLookback` — line 1754
- `EnsembleModelZoo_TradeCloseReward` — line 1838
- `EnsembleModelZoo_InitBandits` — line 1910
- `EnsembleModelZoo_InitExitBandits` — line 1969
- `EnsembleModelZoo_InitBuyThompsonBandits` — line 2024
- `EnsembleModelZoo_InitExitThompsonBandits` — line 2076
- `EnsembleModelZoo_SetDisabledHorizons` — line 2139
- `EnsembleModelZoo_Free` — line 2167
- `EnsembleModelZoo_LoadFromCfg` — line 2212
- `Model_ParseHorizonSibling` — line 2462 — BITMAP_IS_SET(ezoo->init_flags, MASK_EZOO_ACTIVE)=1 if any role got at least one horizon loaded.
- `EnsembleZoo_VerifyGridMemberConsistency` — line 2539
- `EnsembleModelZoo_AutoDetectFromDir` — line 2609
- `EnsembleModelZoo_ComputeBundleId` — line 2762
- `EnsembleModelZoo_SaveBanditState` — line 2787
- `EnsembleModelZoo_SaveExitBanditState` — line 2809
- `EnsembleModelZoo_LoadBanditState` — line 2833
- `EnsembleModelZoo_LoadExitBanditState` — line 2864
- `EnsembleModelZoo_SaveThompsonState` — line 2922
- `EnsembleModelZoo_SaveExitThompsonState` — line 3010
- `EnsembleModelZoo_LoadThompsonState` — line 3093
- `EnsembleModelZoo_LoadExitThompsonState` — line 3226
- `EnsembleModelZoo_LoadBanditStateFromPath` — line 3369
- `EnsembleModelZoo_SetBanditSaveInterval` — line 3396
- `EnsembleModelZoo_MaybeSaveBanditPeriodic` — line 3414
- `EnsembleModelZoo_PostLoadSetup` — line 3579
- `EnsembleModelZoo_IsReadyForInference` — line 3598
- `NodeModelZoo_PostLoadSetup` — line 3651
- `NodeModelZoo_CheckStaleModel` — line 3686

### PerArmFlagRegistry.hpp

- `PerArmFlag_ToString` — line 144 — diagnostic panels.

### RewardTracker.hpp

- `RewardTracker_Init` — line 99
- `RewardTracker_Push` — line 104
- `RewardTracker_DrainCSV` — line 121 — append all pending records to CSV, then clear

### RidgeBlender.hpp

- `Cholesky_Solve` — line 188
- `RidgeBlender_Compute` — line 331
- `RidgeBlender_FinalizeCorrFromSums` — line 426
- `RidgeBlender_BuildCorr` — line 544 — byte-determinism tests). Sister to Bandit_GetProbabilities. TECH_DEBT-158.
- `RidgeBlender_UpdateOnline` — line 648
- `RidgeBlender_BuildHistoryFromRing` — line 798
- `RidgeBlender_OnlineCycleStep` — line 858
- `RidgeWeights_Init` — line 950

### RollingStats.hpp

- `RollingStats_Push` — line 267
- `RollingStats_VolumeSignificant` — line 518
- `RollingStats_EntrySpacing` — line 543
- `RollingStats_BuyPrice` — line 573

### RollingTurnover.hpp

- `RollingTurnover_Init` — line 86 — Validates window + topk; clamps to safe range. Zero-init buffers.
- `RollingTurnover_Push` — line 153 — exactly K bits. Yields [0, 1] range.
- `RollingTurnover_Compute` — line 185 — until profiler flags this as load-bearing.

### ROR_regressor.hpp

- `RORRegressor_Init` — line 74
- `RORRegressor_Push` — line 96

### StampHelper.hpp

- `Stamp_AssembleAndEmit` — line 178

### ThompsonBandit.hpp

- `Thompson_RawToUniform` — line 159 — Muller's log(0) handling).
- `Thompson_BoxMuller_Pair` — line 171 — Caller must ensure u1, u2 ∈ [0, 1).
- `Thompson_Init` — line 189 — applied if caller passes <= 0 for prior/observation precision.
- `Thompson_InitDefault` — line 208 — Typical for unit tests + boot-time init before cfg fields wire in (.B).
- `Thompson_Update` — line 228 — No-op for invalid arm (defensive).
- `Thompson_Sample` — line 306 — Mutates tb->rng_state (advances the PRNG); not thread-safe.
- `Thompson_GetProbabilities` — line 353 — are zeroed.
- `Thompson_GetSoftmaxWeights` — line 406 — are zeroed. Defensive on nullptr / degenerate n_arms < 2.

### VolScaler.hpp

- `VolScaler_Size` — line 50 — default parameters (from FoxML DEFAULT_CONFIG)
- `VolScaler_SizeDefault` — line 65 — convenience: scale with default parameters
- `VolScaler_InverseAlpha` — line 73 — useful for: "what alpha does this position size imply?"
- `VolScaler_RawZ` — line 81 — raw z-score without clipping (for analytics / display)

### WelfordStats.hpp

- `Welford_Init` — line 67
- `Welford_Push` — line 79
- `Welford_Variance` — line 107
- `Welford_Stddev` — line 116
- `Welford_ZScore` — line 124
- `Welford_Reset` — line 133

## GUI/

### CandleAccumulator.hpp

- `CandleAccumulator_Init` — line 101
- `CandleAccumulator_Push` — line 123 — called from engine thread on every tick
- `CandleAccumulator_PushWithTime` — line 183 — instead of using wall-clock time(NULL)
- `CandleAccumulator_Snapshot` — line 267
- `CandleAccumulator_SetInterval` — line 307 — reset accumulator with new interval (clears all candle data)
- `CandleAccumulator_Destroy` — line 333

### ChartPanel.hpp

- `ChartState_Prepare` — line 128
- `GUI_PriceChart` — line 240
- `GUI_VolumeChart` — line 1274
- `GUI_LivePnLChart` — line 1404
- `GUI_EquityChart` — line 1476

### DashboardPanels.hpp

- `GUI_R2Bar` — line 61 — slope_dir: positive slope → green, negative → red, near zero → neutral
- `GUI_Panel_Header` — line 146
- `GUI_Panel_TopBar` — line 283
- `GUI_Panel_Market` — line 332
- `GUI_Panel_BuyGate` — line 550
- `GUI_Panel_Account` — line 1014
- `GUI_Panel_Config` — line 1265
- `GUI_Panel_Positions` — line 1325
- `GUI_Panel_PerNodePnL` — line 1624 — Pure GUI thread, doesn't touch engine state.
- `GUI_Panel_Stats` — line 1732
- `GUI_Panel_Latency` — line 1834
- `GUI_Panel_MLIntelligence` — line 1899
- `GUI_RenderDashboard` — line 2099

### EngineHeaderPanel.hpp

- `EngineHeader_Render` — line 36 — nullptr (legacy callers), only the 3 build-time fields render.

### FoxmlTheme.hpp

- `Foxml_ApplyTheme` — line 63

### GuiThread.hpp

- `Gui_Init` — line 134 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `Gui_Shutdown` — line 282
- `Gui_BeginFrame` — line 306
- `Gui_EndFrame` — line 330
- `Gui_SetupDefaultLayout` — line 355
- `Gui_HandleKeys` — line 416

### LogViewerPanel.hpp

- `LogViewer_Init` — line 63
- `LogViewer_Refresh` — line 84
- `GUI_Panel_LogViewer` — line 128

### MLStatusPanel.hpp

- `MLStatus_Render` — line 37 — nullptr; the row is rendered only when a swap is actually pending.

### ModelBundleScan.hpp

- `ModelBundle_ScanParent` — line 132
- `ModelBundleScan_Run` — line 256
- `ModelBundle_FormatPreview` — line 288

### SettingsPanel.hpp

- `Settings_RescanModels` — line 979
- `Settings_VerifyBundleStamps` — line 1001
- `Settings_Init` — line 1101 — so Settings_Load knows where to read.
- `Settings_Load` — line 1126
- `Settings_RenderFieldDefRow` — line 1315
- `Settings_BuildGlobalTabLayout` — line 1407
- `Settings_BuildPerNodeTabLayout` — line 1419
- `Settings_RenderGlobalTab` — line 1439
- `Settings_RenderPerCoreTab` — line 1585
- `GUI_Panel_Settings` — line 2063 — running cores, not cfg-only intent — engine doesn't add/remove cores live.

### SettingsSectionIndex.hpp

- `Settings_CanonicalSection` — line 27 — keep THIS header self-contained for any include site.
- `SectionLayout_Build` — line 145
- `SettingsSection_GlobalRegistrySectionOf` — line 253
- `SettingsSection_PerNodeRegistrySectionOf` — line 258

### StrategyQualityPanel.hpp

- `StrategyQuality_Init` — line 106 — log path is passed at render time via GUI_Panel_StrategyQuality).
- `StrategyQuality_Refresh` — line 251
- `GUI_Panel_StrategyQuality` — line 343

### TradeHistoryPanel.hpp

- `TradeHistory_Init` — line 99
- `TradeHistory_Refresh` — line 119
- `GUI_Panel_TradeHistory` — line 266

### TradeReader.hpp

- `TradeData_Init` — line 102
- `TradeData_Refresh` — line 169

## Backtest/

### BacktestEngine.hpp

- `BacktestData_DetectFormat` — line 81 — timestamp_us,price,quantity,is_buyer_maker
- `BacktestData_Load` — line 88
- `HistoricalTick_CmpByTime` — line 172 — Caller in STRICT mode should treat -1 as "abort run".
- `BacktestData_ValidateSort` — line 180
- `BacktestResults_Init` — line 358
- `BacktestResults_Free` — line 370
- `BacktestResults_Reset` — line 398 — against zero capacity (defense-in-depth) but this is the load-bearing fix.
- `BacktestResults_EnsureCapacity` — line 421 — grow sample buffers by 2x when full
- `BacktestResults_EnsureEquityCapacity` — line 448 — array, so silent truncation produces wrong Sharpe / max DD / return.
- `XGBoost_ComputeScalePosWeight` — line 486
- `XGBoost_ComputeMulticlassWeights` — line 518 — receives per-class sample counts so caller can log them.
- `BacktestStats_Compute` — line 575 — (0.0 = negative, 1.0 = positive, 0.5 = neutral and already filtered).
- `BacktestStats_ComputeFromEquity` — line 619
- `BacktestSharded_Run` — line 662
- `Backtest_ComputeLabelsFromSamples` — line 717 — through samples; no per-file O(N) sample scans.
- `Backtest_Run` — line 988 — equity curve).
- `HeldOutSplit_TrainEval` — line 1176 — operator set. That metric is the one gating deployment.
- `Backtest_RunWalkForward` — line 1282 — behavior bytewise.
- `Backtest_RunFullValidation` — line 1302
- `WalkForward_ComputeAccuracy` — line 1540 — uses > 0.5f for truth so neutral (0.5) labels are never counted as positive
- `WalkForward_ComputeMulticlassAccuracy` — line 1587 — argmax over each row, compare to integer truth (rounded from label float).
- `WalkForward_ComputeMSE` — line 1606 — regression: mean squared error. Lower = better. Sensitive to outliers.
- `WalkForward_ComputeCorrelation` — line 1622 — gets low MSE on small-magnitude targets while having zero predictive power).
- `Backtest_RunWalkForward` — line 1660
- `HeldOutSplit_TrainEval` — line 2304 — functions it uses (WalkForward_Compute*, XGBoost_Compute*) are visible.
- `ConfigField_Set` — line 2565 — handles both FPN_Binary and PCT fields (PCT keys are stored as decimal, value comes in as %).
- `Backtest_RunSweep` — line 2718 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `Backtest_RunHyperparamTrainSweep` — line 2837 — mean_val_correlation (regression). Stored as positive number; higher = better.

### BacktestPanels.hpp

- `DataPanel_Init` — line 87
- `DataPanel_Scan` — line 107
- `RunControl_Init` — line 264
- `SamplesSnapshot_Compute` — line 290 — only when running==0, giving a safe happens-before relationship.
- `RunControl_Start` — line 531
- `GUI_Panel_DataBrowser` — line 583
- `GUI_Panel_RunControl` — line 701
- `GUI_Panel_Results` — line 777
- `PastRuns_Init` — line 1068
- `PastRuns_LoadOne` — line 1138 — scan one run directory's metadata files
- `PastRuns_DeleteDir` — line 1270
- `PastRun_ParseHorizon` — line 1296 — out_horizon_ticks = 0).
- `PastRuns_ScanOneDir` — line 1350
- `PastRuns_Scan` — line 1387
- `PastRun_MetricLabel` — line 1472 — label-type-aware metric label
- `GUI_Panel_PastRuns` — line 1498 — Pass NULL to keep pre-v5.11.57 behavior (devmode-only).
- `Comparison_Init` — line 2391
- `Comparison_Free` — line 2410
- `Comparison_SaveRun` — line 2432
- `GUI_Panel_Comparison` — line 2485
- `OptimizerPanel_Init` — line 2672
- `GUI_Panel_Optimizer` — line 2737
- `Training_AnyWorkerRunning` — line 3189
- `TrainingPanel_Init` — line 3223 — different answer — the same reason Training_ResolveRole was extracted.
- `GUI_Panel_Training` — line 5132

### BacktestSharded.hpp

- `SharedBacktest_FromHistorical` — line 82
- `BacktestSharded_Run` — line 117

### BacktestSnapshot.hpp

- `BacktestSnapshot_Copy` — line 35

### Fingerprint.hpp

- `SHA256_Init` — line 115
- `SHA256_Update` — line 122
- `SHA256_Final` — line 140
- `SHA256_ToHex` — line 162 — convenience: hash to hex string (65 bytes including null terminator)
- `Fingerprint_HashFile` — line 187
- `Fingerprint_Compute` — line 232
- `Fingerprint_Short` — line 261 — short fingerprint (first 12 hex chars) for display

### HeldOutSplit.hpp

- `HeldOutSplit_GenToken` — line 115 — non-reproducible by construction. Removed.
- `HeldOutSplit_Make` — line 143
- `HeldOutSplit_TestAccessAllowed` — line 178 — refuse-if-locked checks).
- `HeldOutSplit_Unlock` — line 184 — Logs unlock event to stderr — caller can also Notify_Send for audit trail.
- `HeldOutSplit_Relock` — line 206 — not _Relock.

### LabelFunctions.hpp

- `Label_WinLoss` — line 115 — no trade was entered at that point.
- `Label_Barrier` — line 137 — same as win/loss but with configurable asymmetric barriers.
- `Label_ForwardPnl` — line 156 — useful for regression (predict magnitude, not just direction).
- `Label_Regime` — line 177 — MILD_TREND (4) exceeds num_class=4; tracked as TECH_DEBT-241.
- `Label_VolBarrier` — line 201 — source: ~/FoxML/private/DATA_PROCESSING/targets/barrier.py
- `LabelType_NumClasses` — line 499 — ≥2 = multiclass softmax       (label values 0..K-1 as floats)
- `LabelType_IsBinary` — line 504
- `LabelType_IsRegression` — line 508
- `LabelType_IsMulticlass` — line 512
- `Training_ResolveRole` — line 560
- `Training_SideLabelGate` — line 583

### OverfitDetection.hpp

- `OverfitDetection_CheckDefaults` — line 160 — convenience: check with default FoxML thresholds
- `OverfitDetection_CountOverfit` — line 274 — returns: number of folds flagged as overfit
- `OverfitDetection_Print` — line 285 — print report (for logging / debugging)

### PhaseTimers.hpp

- `PhaseTimer_Global` — line 91 — header inline-only (no separate .cpp).
- `PhaseTimer_Reset` — line 102
- `PhaseTimer_Summary` — line 118 — wf_eval / held_out_eval since it's nested inside both.
- `PhaseTimer_PopulateSnapshot` — line 173

### ValidationSplit.hpp

- `PurgeGap_Compute` — line 83 — first test tick to prevent any form of temporal leakage.
- `PurgeGap_ComputeExplicit` — line 90 — overload: caller provides explicit max_lookback (for testing or custom feature sets)
- `ValidationSplit_Generate` — line 153
- `ValidationSplit_GenerateExplicit` — line 257 — used by walk-forward when splitting in non-neutral sample space where raw lookback doesn't apply
- `ValidationSplit_Verify` — line 321 — production leakage guard; this standalone form is available for tests)
- `ValidationSplit_Print` — line 342 — print fold summary (for logging / debugging)

### XGBHyperparams.hpp

- `XGBHyperparams_Defaults` — line 97 — modify the returned struct in-place.
- `XGBHyperparams_Apply` — line 108 — WF/HeldOut/full-validation; both default 4, boot-only). Caller chooses.

---

## Top-level files

- `main.cpp` — 225 lines
- `Version.hpp` — 1148 lines
- `Limits.hpp` — 37 lines

## Conventions

- Function names follow `Pattern_FunctionName` convention (e.g. `Portfolio_Init`, `BG_Evaluate`)
- Headers are inline-heavy — most functions live in `.hpp` and are `inline`
- Templates parameterize on `unsigned F` (frac-bits); FPN_Binary<64> = the 16B two's-complement binary core
- Lowercase helpers (`fan_out`, `drain_with_submit`) are local to a function and not in this map
- ALL_CAPS macros are not in this map; see headers directly
