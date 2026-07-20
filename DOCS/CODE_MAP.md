# CODE_MAP.md

Auto-generated function index. Walks .hpp files in each subsystem and extracts `Pattern_FunctionName` style definitions with their one-line purpose (from the preceding `//` comment, when present).

**Re-generate**: `./tools/gen_code_map.sh`

**Last regenerated**: 2026-07-19 (commit 4c076ed)

## CoreFrameworks/

### BinanceAdapter.hpp

- `BinanceAdapter_WorkerLoop` — line 202
- `BinanceAdapter_Init` — line 326 — shutdown_requested flips.
- `BinanceAdapter_ShutdownState` — line 402 — 1; future commits scale up after the back-to-back stress test passes.
- `BinanceAdapter_SubmitMarketBuy` — line 435 — without a successful Init (shutdown_requested is already 0 by default).
- `BinanceAdapter_SubmitMarketSell` — line 478 — holds with worker_count == 1.
- `BinanceAdapter_GetBalancesImpl` — line 512
- `BinanceAdapter_QueryOrderImpl` — line 547 — pausing submissions during a reconciliation pass.
- `BinanceAdapter_ShutdownImpl` — line 578
- `BinanceAdapter_Get` — line 597

### ControllerConfig.hpp

- `ControllerConfig_CapitalRangeSweep` — line 1506
- `Fee_Compute` — line 1635
- `ControllerConfig_ResolveForCore` — line 1688
- `ControllerConfig_PopulateCoresFromFlat` — line 1751
- `ControllerConfig_NormalizeForMode` — line 2338
- `ControllerConfig_IsLiveCapital` — line 2372
- `ControllerConfig_Load` — line 2414

### ControllerEventLoop.hpp

- `NodeSlowState_Init` — line 184
- `NodeContextDisplayMeta_Init` — line 794
- `Sharded_SlotNode` — line 988 — early consumer precedes the definition (same tt namespace). (D-294)
- `EventLoopState_ReconstructPerCoreFromEventLog` — line 991
- `EventLoopState_Init` — line 1103
- `EventLoopState_InitLegacy` — line 1160
- `EventLoopState_Free` — line 1193
- `EventLoopState_RegisterCore` — line 1254
- `Sharded_LegSlot` — line 1328 — All slow-path / boot-time. Trivially inlined.
- `Sharded_SlotNode` — line 1365 — and ShardedSnapshot.hpp. GUI sites grandfathered for the E-series decouple. (D-294/D-295)
- `Sharded_ValidatePartialExitCfg` — line 1378
- `EventLoopState_SetCoreStrategy` — line 1429
- `EventLoopState_AttachTradeLog` — line 1476
- `EventLoopState_AttachOms` — line 1493
- `EventLoopState_Balance` — line 1511
- `EventLoopState_RealizedPnl` — line 1516
- `EventLoopState_Portfolio` — line 1527
- `EventLoopState_PortfolioMut` — line 1532
- `EventLoopState_KsMinBalance` — line 1537
- `EventLoopState_KsMaxDrawdownPct` — line 1542
- `EventLoopState_KsPeakBalance` — line 1547
- `EventLoopState_TradeLog` — line 1563
- `EventLoopState_SetIntendedParams` — line 1578
- `EventLoop_DrainPostFillOneCore` — line 1596
- `EventLoop_DrainPostFill` — line 2025
- `EventLoop_OnEvent` — line 2114
- `EventLoop_DrainEvents` — line 2298
- `EventLoop_QueueParameters` — line 2341
- `EventLoop_RebuildAllParameters` — line 2379
- `EventLoop_UpdateRollingStateOneCore` — line 2486
- `EventLoop_UpdateEmaPriceAllCores` — line 2529
- `EventLoop_RebuildOneCore` — line 2575
- `EventLoop_PushParameters` — line 3517
- `EventLoopState_ConfigureKillSwitch` — line 3579
- `EventLoop_ClearAllPermissions` — line 3589
- `EventLoop_KillSwitchTrip` — line 3600
- `EventLoop_KillSwitchEvaluate` — line 3629
- `EventLoop_TimeExitOneCore` — line 3695
- `EventLoop_FlattenAll` — line 3797
- `EventLoop_CheckWsStaleness` — line 3879
- `EventLoop_TryClearRecovery` — line 3958
- `EventLoop_TrailingSLRatchetOneCore` — line 4023
- `EventLoop_BreakevenOnProfitOneCore` — line 4121
- `EventLoop_Unpause` — line 4195
- `EventLoop_SlowPath` — line 4219
- `EventLoop_RunController` — line 4244

### EngineCommon.hpp

- `EngineCommon_ApplyBnbDiscount` — line 162
- `EngineCommon_BootGlobal` — line 207
- `EngineCommon_BootPerCore` — line 261
- `EngineCommon_SlowPathCycleOneCore` — line 518
- `EngineCommon_SlowPathCycleAllCores` — line 903

### EnsembleHotSwap.hpp

- `EngineSharded_HotSwapEnsemble` — line 35

### EventLoopAggregates.hpp

- `EventLoop_GetAggregates` — line 124

### ExecutionCore.hpp

- `ExecutionCore_Init` — line 272
- `ExecutionCore_SetParameters` — line 331
- `ExecutionCore_SetPermission` — line 366
- `ExecutionCore_Tick_Impl` — line 403
- `ExecutionCore_Tick` — line 788

### GateParameters.hpp

- `BG_Evaluate` — line 216
- `SG_Evaluate` — line 264
- `GateParameters_Init` — line 293

### HotSwap.hpp

- `HotSwap_ShadowLoad_Ensemble` — line 68
- `HotSwap_ShadowLoad_SingleZoo` — line 230

### LiveReadiness.hpp

- `LiveReadiness_Verify` — line 301

### MetricCompute.hpp

- `Compute_ProfitFactor` — line 52 — → backtest-suite layering boundary.
- `Compute_AllWinsRun` — line 58 — numerical profit_factor is 0.0 in this case, separately).
- `Compute_Expectancy` — line 62
- `Compute_WinRate` — line 74
- `Compute_AvgHoldTicks` — line 80
- `Compute_ReturnPct` — line 86
- `MaxDrawdown_UpdateIncremental` — line 97 — regression test needed.

### ModelValidation.hpp

- `NodeModelZoo_ValidateAgainstCfg` — line 147

### NodeLatencyStats.hpp

- `NodeLatencyStats_Init` — line 192
- `NodeLatencyStats_Reset` — line 224 — stats mid-run without disabling them.
- `NodeLatencyStats_Enable` — line 240
- `NodeLatencyStats_Disable` — line 244
- `NodeLatencyStats_Sample` — line 258
- `NodeLatencyStats_Snapshot` — line 300 — rdtsc reading at sample time, used for "last seen" tracking in the TUI.

### Notify.hpp

- `NotifyState_Init` — line 270 — drains remaining events before exiting (per test sidecar Group 5).
- `Notify_Send` — line 301
- `NotifyState_Shutdown` — line 370 — Drain remaining events + join worker thread + free pthread resources.
- `NotifyBackend_Stderr` — line 396
- `Notify_ShellEscape` — line 478
- `Notify_BuildCommand` — line 529 — Document this for users; provide a wrapper script if needed.
- `NotifyBackend_Command` — line 578 — overflowed before completion (still tries to run what fit).

### OrderEventLog.hpp

- `OrderEventLog_Init` — line 326
- `OrderEventLog_Free` — line 392
- `OrderEventLog_ApplyEvent` — line 433
- `OrderEventLog_Append` — line 481
- `OrderEventLog_AsyncWriterRoutine` — line 532
- `OrderEventLog_StartAsyncWriter` — line 580
- `OrderEventLog_StopAsyncWriter` — line 609
- `OrderEventLog_InitWithFile` — line 632
- `OrderEventLog_Reset` — line 721
- `OrderEventLog_LoadFromDisk` — line 777
- `OrderEvent_MakeFill` — line 883
- `OrderEvent_MakeRejection` — line 921
- `Portfolio_FromEventLog` — line 982

### OrderGates.hpp

- `Gate_Zero` — line 115
- `Gate_ZeroAll` — line 122

### Order.hpp

- `Order_GetType` — line 306
- `Order_SetType` — line 310
- `Order_GetState` — line 316
- `Order_SetState` — line 320
- `Order_GetIsMaker` — line 326
- `Order_SetIsMaker` — line 330
- `Order_SetLeg` — line 340
- `Order_SetRetryCount` — line 350
- `Order_GetPreResolvedBound` — line 359
- `Order_MarkPreResolvedBound` — line 363
- `MBS_OrderBanditActiveState` — line 379
- `MBS_OrderBanditRegime` — line 383
- `MBS_OrderBanditChosenArm` — line 387
- `MBS_OrderSetBanditContext` — line 391
- `Order_Init` — line 415
- `Order_BindPreResolved` — line 465
- `Order_WarnIfNotPreResolved` — line 506
- `Order_IsTerminal` — line 558

### OrderManager.hpp

- `OrderManager_Init` — line 966
- `OMS_PushSubmit` — line 1260
- `OMS_DrainSubmit` — line 1311
- `OrderManager_AccountMakerTakerFee` — line 1351
- `OMS_GuardTakerBoundFeeBasis` — line 1393
- `OrderManager_HandleFill` — line 1596
- `OrderManager_ProcessFillCommand` — line 1665
- `OMS_OpenPositionCost` — line 1788
- `OMS_ExpectedFreeCash` — line 1827
- `OrderManager_ProcessReconcile` — line 1871
- `OrderManager_Tick` — line 1918
- `OrderManager_Shutdown` — line 1965
- `OrderManager_OpenCalibrationLog` — line 1990
- `OrderManager_InflightCount` — line 2050

### PaperResetArchive.hpp

- `PaperResetArchive_FormatTimestamp` — line 101 — Uses localtime_r for thread safety. out_size should be >= 20.
- `PaperResetArchive_FormatDirname` — line 112 — out_size should be >= 128 (typical ISO string + path overhead ~80 chars).
- `PaperResetArchive_CreateDirectories` — line 130 — calling mkdir() incrementally.
- `Summary_WriteJson` — line 167

### ParameterSlot.hpp

- `ParameterSlot_Init` — line 161
- `ParameterSlot_Write` — line 194
- `ParameterSlot_Read` — line 261

### PortfolioController.hpp

- `PortfolioController_Init` — line 360
- `KillSwitch_Activate` — line 618
- `KillSwitch_Reset` — line 632
- `Buying_Halt` — line 641
- `PortfolioController_DrainExits` — line 848
- `PortfolioController_StrategyBuySignal` — line 891
- `PortfolioController_StrategyDispatch` — line 982
- `PortfolioController_Tick` — line 1037
- `PortfolioController_Unpause` — line 2059
- `PortfolioController_CycleRegime` — line 2070
- `PortfolioController_HotReload` — line 2096
- `PortfolioController_SaveSnapshot` — line 2180
- `PortfolioController_LoadSnapshot` — line 2255

### Portfolio.hpp

- `ExitBuffer_PendingProceeds` — line 317
- `Portfolio_AddPositionWithExits` — line 426
- `Portfolio_OpenSlot` — line 554
- `Portfolio_OpenSlot` — line 597
- `Money_FillGross` — line 622
- `Portfolio_CloseSlot` — line 649
- `Portfolio_SlotActive` — line 662
- `Portfolio_UpdatePosition` — line 672
- `Portfolio_Save` — line 831
- `Portfolio_Load` — line 885

### Reconcile.hpp

- `ReconcileMode_ToString` — line 163 — Mode → string for logging. Uses cfg_string field (operator-friendly).
- `ReconcileMode_FromString` — line 176 — parse OR error). Accepts cfg_string values from registry.
- `Reconcile_ApplyMissedFills` — line 246
- `Reconcile_AutoCancelStale` — line 424
- `Reconcile_ParseOpenOrders` — line 670
- `Reconcile_ParseMyTrades` — line 716 — Output: fills `out` array up to `out_cap`. Returns count parsed.
- `Reconcile_Decide` — line 760 — Output: fills `out` array up to `out_cap`. Returns count parsed.
- `Reconcile_LogReport` — line 838 — Outputs ReconcileResult with planned actions. Caller applies them.

### ReconciliationLoop.hpp

- `ReconciliationLoop_Pass` — line 131
- `ReconciliationLoop_Init` — line 251
- `ReconciliationLoop_Start` — line 286
- `ReconciliationLoop_TriggerNow` — line 294
- `ReconciliationLoop_Shutdown` — line 308

### ShardedBacktestDriver.hpp

- `ShardedBacktestDriver_Init` — line 176
- `ShardedBacktest_RunTick` — line 235
- `ShardedBacktest_Run` — line 455

### ShardedLiveSafety.hpp

- `EngineSharded_OrphanRecovery` — line 58
- `EngineSharded_ForceCloseOnShutdown` — line 167

### ShardedOrderLatency.hpp

- `ShardedOrderLatency_Reset` — line 80 — before the first order can fire.
- `ShardedOrderLatency_Sample` — line 97

### ShardedSnapshot.hpp

- `TUI_CopySnapshotSharded` — line 54

### ShardedSnapshotPersist.hpp

- `ShardedSnapshot_Save` — line 131
- `ShardedSnapshot_Load` — line 333

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

- `SPSCRing_Init` — line 145
- `SPSCRing_TryPush` — line 170
- `SPSCRing_TryPop` — line 251
- `SPSCRing_Depth` — line 299
- `SPSCRing_Capacity` — line 319

### SpSectionRegistry.hpp

- `SP_SECTION_NAME` — line 52
- `SP_SECTION_DOC` — line 60

### StampBoundDerivedFilter.hpp

- `STAMP_BOUND_CFG_emit_canonical_body` — line 56

### TradeLogColRegistry.hpp

- `TradeLog_EmitHeader` — line 70 — for the original 11 columns.

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
- `RegimeState_FieldwiseWrite` — line 649
- `RegimeState_FieldwiseRead` — line 658
- `RegimeState_CommitPersistedFields` — line 669
- `Regime_Init` — line 704
- `Regime_Classify` — line 743
- `Regime_ToStrategy` — line 897
- `Regime_AdjustPositions` — line 915

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
- `Strategy_WriteRatchetSL` — line 291
- `Strategy_WriteRatchetTP` — line 331
- `Strategy_ExitAdjustPerCore` — line 380
- `Strategy_FreePerCore` — line 443

### StrategyParameters.hpp

- `Strategy_SpacingOk` — line 269
- `Strategy_TpFloor` — line 288
- `GateEgress_MaxPct` — line 312 — FinalizeEmit's range-validate AND the leg-B tp_pct_b clamp below (the A-class leg-B leak fix).
- `GateParameters_FinalizeEmit` — line 315
- `SimpleDip_BuildParameters` — line 427
- `MeanReversion_BuildParameters` — line 508
- `Momentum_BuildParameters` — line 599
- `EmaCross_BuildParameters` — line 729
- `ML_BuildParameters` — line 843
- `Strategy_BuildParameters` — line 1779

## Strategies/private/

### EmaCross.hpp

- `EmaCross_Init` — line 68
- `EmaCross_Adapt` — line 83
- `EmaCross_BuySignal` — line 101
- `EmaCross_ExitAdjust` — line 163
- `EmaCross_ExitAdjustSharded` — line 252

## DataStream/

### BinanceCrypto.hpp

- `BinanceStream_Init` — line 587 — as a min-size sanity guard catches truncated frames without scanning.
- `BinanceStream_Close` — line 660 — clean shutdown: send close frame, SSL shutdown, close socket, free resources
- `BinanceStream_Reconnect` — line 695
- `BinanceStream_Poll` — line 743
- `BinanceStream_ReadTick` — line 807
- `BinanceStream_InWindDown` — line 908 — returns 1 on success (out filled with price + volume), 0 on error/disconnect
- `BinanceStream_ShouldReconnect` — line 921
- `BinanceStream_HasPending` — line 936 — returns 1 if SSL has buffered data that can be read without blocking
- `BinanceConfig_Load` — line 987

### BinanceDepth.hpp

- `DepthStream_Init` — line 293

### BinanceOrderAPI.hpp

- `BinanceOrderAPI_Cleanup` — line 583
- `BinanceOrderAPI_MarketBuy` — line 593 — fill_price_out/fill_qty_out receive actual execution values (NULL = don't care)
- `BinanceOrderAPI_MarketSell` — line 657 — place a market sell order
- `BinanceOrderAPI_CancelOrder` — line 737 — different operator semantics.
- `BinanceOrderAPI_GetStatus` — line 771 — fills filled_qty and avg_price on success
- `BinanceOrderAPI_LoadFilters` — line 820 — returns 1 on success, 0 on failure (caller should treat as fatal)
- `BinanceOrderAPI_GetBalance` — line 855 — returns 1 on success, 0 on failure
- `BinanceOrderAPI_GetOpenOrders` — line 887 — network-independent (testable without real REST calls).
- `BinanceOrderAPI_GetMyTrades` — line 898 — the last-known-processed trade id to catch only new fills.
- `BinanceOrderAPI_GetBalances` — line 914 — returns 1 on success, 0 on failure
- `BinanceOrderAPI_SyncClock` — line 938 — re-sync clock offset (call periodically or after reconnect)
- `BinanceOrderAPI_Init` — line 952 — must be called after Cleanup, ServerTime, SyncClock, LoadFilters are defined

### BinanceUserData.hpp

- `BinanceUserData_Init` — line 684
- `BinanceUserData_Start` — line 720
- `BinanceUserData_Shutdown` — line 726

### CalibLogColRegistry.hpp

- `CalibLog_EmitHeader` — line 177 — Adding a 9th arm later: append 4 more rows + bump BANDIT_MAX_ARMS at BanditLearning.hpp.

### DepthRecorder.hpp

- `DepthRecorder_MkdirP` — line 101
- `DepthRecorder_DateInt` — line 116
- `DepthRecorder_OpenFile` — line 124
- `DepthRecorder_PruneOld` — line 160
- `DepthRecorder_Init` — line 195
- `DepthRecorder_LogGap` — line 231 — disconnect time, or the current snapshot's timestamp_us).
- `DepthRecorder_Write` — line 259
- `DepthRecorder_Close` — line 312

### DepthReplayState.hpp

- `DepthReplay_DateInt` — line 118
- `DepthReplayState_Init` — line 136
- `DepthReplayState_Free` — line 171
- `DepthReplayState_LoadDay` — line 204
- `DepthReplayState_Advance` — line 321
- `DepthReplayState_GetSnapshot` — line 346

### EngineTUI.hpp

- `TUI_Init` — line 175
- `TUI_Cleanup` — line 208
- `TUI_Render` — line 236
- `TUI_HandleInput` — line 628
- `MLSnapshot_Populate` — line 777
- `TUISnapshot_InitSeq` — line 1544 — populated" state) — this only initializes the sequence counter.
- `TUISnapshot_Publish_Begin` — line 1559 — the new active.
- `TUISnapshot_Publish_End` — line 1575 — Any subsequent reader sees the just-filled buffer as active.
- `TUISnapshot_ReadInto` — line 1587 — effectively never observed.
- `TUI_CopySnapshot` — line 1625
- `TUI_CopySnapshot` — line 1631
- `TUI_CopySnapshot` — line 1638
- `TUI_PopulatePerCoreLatency` — line 1916
- `TUI_PopulatePerCoreSlowPathLatency` — line 1963
- `TUI_PopulateAdvancedTopology` — line 2001
- `TUI_PopulateTopology` — line 2045 — poll_interval[i]    — per-core resolved poll cadence
- `TUI_Render_Snapshot` — line 2102 — both dependencies are available.
- `TUI_ReadKey` — line 2313

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

- `TickRecorder_MkdirP` — line 80
- `TickRecorder_DateInt` — line 95
- `TickRecorder_OpenFile` — line 108
- `TickRecorder_PruneOld` — line 143
- `TickRecorder_Init` — line 178
- `TickRecorder_Push` — line 210
- `TickRecorder_Close` — line 244

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

- `FPN_BlendOnMask` — line 689
- `Money_Mul` — line 1876
- `Money_Div` — line 1917
- `Money_Add` — line 1954 — integer ops with a closure clamp + S-17 flag). Branchless mask-select clamp by the result sign.
- `Money_Add` — line 1962
- `Money_FromString` — line 2126
- `Money_FromBinary` — line 2207
- `Money_Zero` — line 2236 — lower to cmov (same shape as fp2_min/max); BlendOnMask mirrors the live <64> mask-select.
- `Money_Negate` — line 2237
- `Money_Abs` — line 2238
- `Money_Min` — line 2239
- `Money_Max` — line 2240
- `Money_IsZero` — line 2241
- `Money_Lt` — line 2242
- `Money_Le` — line 2243
- `Money_Eq` — line 2244
- `Money_Gt` — line 2245
- `Money_Ge` — line 2246
- `Money_QuantizeToStep` — line 2259
- `Money_BlendOnMask` — line 2281 — NEVER a plain wide divide (no __udivti3 on any path).
- `Money_FromInt` — line 2286 — Money_FromInt: whole-unit int -> money (i*10^8), clamp+flag past the closure ceiling.
- `Money_ToDouble` — line 2295 — Money_ToDouble — DISPLAY-ONLY (H4-exempt): GUI/diag/inf-bridge consumption. Never accounting.
- `Money_ToCString` — line 2360

## MemHeaders/

### DrainerConstants.hpp

- `DrainerConstants_Init` — line 121

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

- `LatencyHistogram_Reset` — line 169 — instrumentation overhead bound for bench gate ON-state.
- `LatencyHistogram_Accumulate` — line 191

### NodeCtxSummaryFieldRegistry.hpp

- `Summary_EmitPerCoreEntry` — line 239
- `Summary_EmitPerStrategy` — line 280

### OmsPhasedDrain.hpp

- `OmsDrainBuckets_Reset` — line 134
- `OrderType_IsClose` — line 154
- `OrderManager_DrainIntoBuckets` — line 278
- `OrderManager_ProcessBucket_Closes` — line 335
- `OrderManager_ProcessBucket_Opens` — line 351
- `OrderManager_ProcessBucket_Reconciles` — line 364

### OmsPushExitHelper.hpp

- `OMS_PushExitForSlot` — line 77

### RunHistory.hpp

- `RunHistory_Append` — line 115 — defense-in-depth for the HMAC/stamp-adjacent byte-equivalence path.)

## ML_Headers/

### BanditAlgorithmRegistry.hpp

- `BanditAlgo_Exp3_Apply` — line 58 — cfg=2 reassigns to Exp3_Drives_Thompson_Ghost_Apply per Option C wire-preserving expansion).
- `BanditAlgo_Thompson_Apply` — line 61
- `BanditAlgo_Exp3_Drives_Thompson_Ghost_Apply` — line 64
- `BanditAlgo_Thompson_Drives_Exp3_Ghost_Apply` — line 67
- `BanditAlgo_Blended_Apply` — line 70
- `BanditAlgorithm_ToString` — line 184
- `BanditAlgorithm_FromString` — line 196 — CRITICAL operator error — don't silently default).
- `BanditAlgorithm_Apply` — line 221 — parse failure; the safe fallback is the bytewise-identical default path.
- `BanditAlgo_Exp3_Apply` — line 249 — default). Thompson state + blend_alpha ignored.
- `BanditAlgo_Thompson_Apply` — line 279 — + blend_alpha ignored. Posterior state advances (rng_state mutates) as part of sampling.
- `BanditAlgo_Exp3_Drives_Thompson_Ghost_Apply` — line 307 — (Class 24 fix — pre-.F.4d Thompson never updated despite mode being settable).
- `BanditAlgo_Thompson_Drives_Exp3_Ghost_Apply` — line 343 — Both bandits update from per-arm reward signal downstream (per-arm observability invariant).
- `BanditAlgo_Blended_Apply` — line 374 — weights via cmov (H20 / Class 28 prevention). Per § J of .F.4d merged plan body.

### BanditLearning.hpp

- `BanditDisplayMeta_InitDefault` — line 96 — BanditDisplayMeta_SetArmName.
- `BanditDisplayMeta_SetArmName` — line 108 — Set a custom human-readable name for an arm (display only).
- `Bandit_Init` — line 203
- `Bandit_InitDefault` — line 226 — convenience: init with default FoxML parameters
- `Bandit_GetProbabilities` — line 253 — tests. Suppress asan here; ubsan + the normal -O3 build still exercise it. (TECH_DEBT-158 close-out.)
- `Bandit_Select` — line 345
- `Bandit_Update` — line 383 — eta    = min(eta_max, sqrt(ln(K) / (K * T)))
- `Bandit_GetWeights` — line 439
- `Bandit_EffectiveBlend` — line 468 — final = (1 - effective_blend) * static + effective_blend * bandit
- `Bandit_BlendWeights` — line 477
- `Bandit_Print` — line 525 — steps >= min+ramp:             effective_blend = blend_ratio
- `Bandit_SaveJSON` — line 571
- `Bandit_LoadJSON` — line 804 — caller's prior Bandit_Init call — load is overlay only.

### BarrierBlendModeRegistry.hpp

- `BarrierBlendMode_BlendDrives` — line 135 — mode is compile-time-known.
- `BarrierBlendMode_DominantDrives` — line 139
- `BarrierBlendMode_ShadowActive` — line 143
- `BarrierBlendMode_IsLegacy` — line 147
- `BarrierBlendMode_ToString` — line 158 — and stamp body cfg-drift comparison.
- `BarrierBlendMode_FromString` — line 167
- `BarrierBlendMode_Doc` — line 178

### BarrierGate.hpp

- `BarrierGate_Compute` — line 76 — compute barrier gate value from peak/valley predictions

### ConfidenceScore.hpp

- `RollingWindow_Init` — line 155
- `RollingWindow_Push` — line 164
- `RollingIC_Init` — line 270 — v5.15.5.E.C — Init via generic RollingWindow_Init on both rings.
- `RollingIC_Push` — line 279 — the parallel-array push semantics for the (prediction, actual) pair shape.
- `RollingIC_Compute` — line 320 — RollingIC_Push). Read either; using predictions's metadata canonically.
- `RollingRMSE_Init` — line 446
- `RollingRMSE_Push` — line 469 — in controller_test.cpp.
- `RollingRMSE_Compute` — line 492 — pattern (the spec tracks its production sites).
- `Confidence_Freshness` — line 520 — stability: 1 / (1 + RMSE)
- `Confidence_Stability` — line 526
- `Confidence_Compute` — line 530
- `RollingFreshness_Init` — line 608
- `RollingFreshness_Mark` — line 613
- `RollingFreshness_Compute` — line 620 — or replay determinism), clamp to 1.0.
- `RollingCapacity_Init` — line 677
- `RollingCapacity_UpdateADV` — line 684
- `RollingCapacity_Compute` — line 694
- `ConfidenceScorer_Init` — line 831
- `ConfidenceScorer_ComputeICVariant` — line 867 — New code + sites being refactored for variant choice use this dispatcher.
- `ConfidenceScorer_InitComposite` — line 875 — explicit composite parameters. Useful for tests + v5.14.1.B cfg wiring.
- `ConfidenceScorer_BindCompositeCfg` — line 905 — FPN_ToDouble(cfg.confidence_rmse_baseline));
- `ConfidenceScorer_Update` — line 918 — feed a prediction + actual return pair (call after outcome is known)
- `ConfidenceScorer_UpdateAndMark` — line 931 — when composite is disabled (composite path is opt-in via cfg).
- `ConfidenceScorer_Compute` — line 940 — compute current confidence given data age
- `ConfidenceScorer_ComputeComposite` — line 964 — stability_normalized = 1 - clamp(rmse / rmse_baseline, 0, 1)
- `ConfidenceScorer_MarkPredict` — line 992 — fixture control.
- `Confidence_DegradationScale_Off` — line 1065 — Forward-declare curve compute fns so the dispatch table can reference them.
- `Confidence_DegradationScale_Linear` — line 1066
- `Confidence_DegradationScale_Exp` — line 1067
- `Confidence_DegradationScale_Step` — line 1068
- `DegradationCurve_ToString` — line 1104 — Auto-generated ToString — for cfg parser + GUI display.
- `DegradationCurve_FromString` — line 1115 — numeric ("1") forms; case-insensitive on string form. Returns -1 on miss.
- `Confidence_DegradationScale_Off` — line 1140 — when cfg.risk_degradation_curve=0 (default).
- `Confidence_DegradationScale_Linear` — line 1148 — To get ladder-bottom (factor=0), operator sets min_pct=0.0.
- `Confidence_DegradationScale_Exp` — line 1158 — as LINEAR.
- `Confidence_DegradationScale_Step` — line 1169 — without continuous-curve noise.
- `Confidence_DegradationScale` — line 1177 — out-of-range returns 1.0 (degrades safely to OFF behavior).
- `DriftHistory_Init` — line 1340
- `DriftHistory_Push` — line 1348 — + ts_us[idx], 2 separate cache lines 2048B apart).
- `DriftHistory_CheckBreach` — line 1366 — at typical 10-100Hz cadence.
- `ConfidenceScorer_FieldwiseWrite` — line 1428
- `ConfidenceScorer_FieldwiseRead` — line 1437
- `ConfidenceScorer_CommitPersistedFields` — line 1449
- `ConfidenceScorer_RecomputeRunningSums` — line 1472 — CommitPersistedFields tail; PortfolioController calls it explicitly.
- `ConfidenceScorer_ShadowLoadLegacyV1` — line 1701

### CostModel.hpp

- `CostModel_Estimate` — line 95 — k1, k2, k3:     cost coefficients
- `CostModel_EstimateDefault` — line 122 — convenience: estimate with default coefficients
- `CostModel_Breakeven` — line 132 — cost is in bps, divide by 10000 to get decimal return
- `CostModel_ShouldTrade` — line 137 — should we trade? returns 1 if expected alpha > breakeven

### EzooInitFlagRegistry.hpp

- `EzooInitFlag_ToString` — line 116 — CRITICAL log lines + diagnostic panels.

### FeatureRegistry.hpp

- `ML_Compute_ShortSlope` — line 161
- `ML_Compute_ShortR2` — line 166
- `ML_Compute_ShortVariance` — line 171
- `ML_Compute_LongSlope` — line 176
- `ML_Compute_LongR2` — line 181
- `ML_Compute_LongVariance` — line 186
- `ML_Compute_VolRatio` — line 191
- `ML_Compute_RorSlope` — line 196
- `ML_Compute_VolumeSlope` — line 201
- `ML_Compute_VolumeDelta` — line 206
- `ML_Compute_EmaSmaSpread` — line 225
- `ML_Compute_VwapDev` — line 230
- `ML_Compute_PriceStddev` — line 235
- `ML_Compute_PriceAvg` — line 240
- `ML_Compute_VolumeAvg` — line 245
- `ML_Compute_EmaAboveSma` — line 250
- `ML_Compute_MidSlope` — line 257
- `ML_Compute_MidR2` — line 262
- `ML_Compute_CumDelta` — line 267
- `ML_Compute_HourSin` — line 272
- `ML_Compute_HourCos` — line 277
- `ML_Compute_VolRegimeRatio` — line 282
- `ML_Compute_TickRateZ` — line 287
- `ML_Compute_DistToHigh` — line 292
- `ML_Compute_DistToLow` — line 297
- `ML_Compute_BookImbMeanShort` — line 302
- `ML_Compute_BookImbMeanLong` — line 307
- `ML_Compute_BookImbDrift` — line 312
- `ML_Compute_Flow10s` — line 317
- `ML_Compute_Flow1m` — line 322
- `ML_Compute_Flow5m` — line 327
- `ML_Compute_LargeTradeZ` — line 332
- `ML_Compute_SpreadBps` — line 337
- `ML_Compute_SpreadZscore` — line 342
- `ML_Compute_RegimeTrendStrength` — line 373
- `ML_Compute_RegimeVolZscore` — line 388
- `ML_Compute_RegimeClassOneHot` — line 410
- `ML_Compute_FracDiffPrice_d04` — line 481
- `ML_Compute_FracDiffPrice_d05` — line 486
- `ML_Compute_FracDiffPrice_d06` — line 491
- `Features_PackAll` — line 722
- `Features_PackAll` — line 804

### FeatureRegistryOverlay.hpp

- `FeatureOverlay_ParseLayer2HashFromSidecar` — line 80 — key and ":" handled).
- `FeatureOverlay_PostLoadVerify` — line 162

### FeatureStandardizer.hpp

- `FeatureStandardizer_Init` — line 203
- `FeatureStandardizer_Apply` — line 246 — recommended for clarity.
- `FeatureStandardizer_Load` — line 318 — ---- the sidecar body field-map: tier-2 [WIRE_FIELD] members, ordinal-addressed (D-345) ----
- `FeatureStandardizer_VerifyAgainstBuild` — line 434 — has_scaler=1 if all upstream checks (registry_hash match) pass.
- `FeatureStandardizer_FitWinsor` — line 478 — training-side cost. Slow-path slow.
- `FeatureStandardizer_Compute` — line 516
- `FeatureStandardizer_Persist` — line 556 — Returns 1 on success, 0 on I/O failure.
- `FeatureStandardizer_Free` — line 633 — Persist writes the sidecar via atomic write (.tmp + rename).

### FlowFeatures.hpp

- `BookImbHistory_Init` — line 161
- `BookImbHistory_Push` — line 171
- `BookImbHistory_MeanLong` — line 201
- `BookImbHistory_MeanShortFast` — line 218
- `BookImbHistory_Last` — line 228
- `BookImbHistory_MeanShort` — line 237
- `FlowState_Init` — line 332
- `FlowState_Push` — line 345 — Full RegimeSignals→FPN_Binary cascade is a v5.11 ship (large blast radius).
- `LargeTradeState_Init` — line 468
- `LargeTradeState_Push` — line 478
- `LargeTradeState_ZScore` — line 501
- `LargeTradeState_Last` — line 517
- `SpreadState_Init` — line 611
- `SpreadState_Push` — line 621
- `SpreadState_ZScore` — line 639
- `SpreadState_Last` — line 654

### LinearRegression3X.hpp

- `RegressionFeederX_FieldwiseWrite` — line 111
- `RegressionFeederX_FieldwiseRead` — line 120
- `RegressionFeederX_CommitPersistedFields` — line 129

### ModelInference.hpp

- `FeatureLookback_Max` — line 286
- `FeatureLookback_CountEnabled` — line 296 — count enabled features (for validation)
- `Model_Init` — line 524
- `Model_Load` — line 572
- `Model_Predict_Normalized` — line 707
- `Model_Predict_AtClass` — line 770
- `Model_LoadAOT` — line 833
- `Model_Predict_AOT` — line 847
- `Model_Predict` — line 891
- `Model_Predict_Ensemble` — line 975
- `Model_Predict_Ensemble_Weighted` — line 1061
- `Model_PredictMulti` — line 1206
- `Model_Free` — line 1282
- `Model_IsLoaded` — line 1302
- `ModelFeatures_Pack` — line 1325

### NodeModelZoo.hpp

- `NodeModelZoo_Init` — line 159
- `NodeModelZoo_TryLoadRole` — line 186
- `NodeModelZoo_LoadFromDir` — line 664
- `NodeModelZoo_LoadLegacy` — line 773
- `NodeModelZoo_Free` — line 783
- `NodeModelZoo_HasAny` — line 792
- `NodeModelZoo_VerifyExpected` — line 830 — features in the pack, model crashes or produces garbage.
- `EnsembleZoo_FinalizeCorrupt` — line 1367
- `EnsembleModelZoo_Init` — line 1405
- `EnsembleModelZoo_EnsurePrimary` — line 1498
- `EnsembleModelZoo_RecordPrediction` — line 1554
- `EnsembleModelZoo_UpdateDrift` — line 1583
- `EnsembleModelZoo_TickRewardsFromLookback` — line 1636
- `EnsembleModelZoo_TradeCloseReward` — line 1720
- `EnsembleModelZoo_InitBandits` — line 1789
- `EnsembleModelZoo_InitExitBandits` — line 1837
- `EnsembleModelZoo_InitBuyThompsonBandits` — line 1892
- `EnsembleModelZoo_InitExitThompsonBandits` — line 1944
- `EnsembleModelZoo_SetDisabledHorizons` — line 2007
- `EnsembleModelZoo_Free` — line 2035
- `EnsembleModelZoo_LoadFromCfg` — line 2079
- `EnsembleZoo_VerifyGridMemberConsistency` — line 2367
- `EnsembleModelZoo_AutoDetectFromDir` — line 2437
- `EnsembleModelZoo_ComputeBundleId` — line 2594
- `EnsembleModelZoo_SaveBanditState` — line 2619
- `EnsembleModelZoo_SaveExitBanditState` — line 2641
- `EnsembleModelZoo_LoadBanditState` — line 2665
- `EnsembleModelZoo_LoadExitBanditState` — line 2696
- `EnsembleModelZoo_SaveThompsonState` — line 2753
- `EnsembleModelZoo_SaveExitThompsonState` — line 2841
- `EnsembleModelZoo_LoadThompsonState` — line 2924
- `EnsembleModelZoo_LoadExitThompsonState` — line 3057
- `EnsembleModelZoo_LoadBanditStateFromPath` — line 3200
- `EnsembleModelZoo_SetBanditSaveInterval` — line 3227
- `EnsembleModelZoo_MaybeSaveBanditPeriodic` — line 3245
- `EnsembleModelZoo_PostLoadSetup` — line 3381
- `EnsembleModelZoo_IsReadyForInference` — line 3400
- `NodeModelZoo_PostLoadSetup` — line 3453
- `NodeModelZoo_CheckStaleModel` — line 3488

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
- `RidgeBlender_BuildCorr` — line 543 — byte-determinism tests). Sister to Bandit_GetProbabilities. TECH_DEBT-158.
- `RidgeBlender_UpdateOnline` — line 646
- `RidgeBlender_BuildHistoryFromRing` — line 795
- `RidgeBlender_OnlineCycleStep` — line 855
- `RidgeWeights_Init` — line 947

### RollingStats.hpp

- `RollingStats_Push` — line 266
- `RollingStats_VolumeSignificant` — line 517
- `RollingStats_EntrySpacing` — line 542
- `RollingStats_BuyPrice` — line 572

### RollingTurnover.hpp

- `RollingTurnover_Init` — line 84 — Validates window + topk; clamps to safe range. Zero-init buffers.
- `RollingTurnover_Push` — line 151 — exactly K bits. Yields [0, 1] range.
- `RollingTurnover_Compute` — line 183 — until profiler flags this as load-bearing.

### ROR_regressor.hpp

- `RORRegressor_Init` — line 74
- `RORRegressor_Push` — line 96

### StampHelper.hpp

- `Stamp_AssembleAndEmit` — line 176

### ThompsonBandit.hpp

- `Thompson_RawToUniform` — line 155 — Muller's log(0) handling).
- `Thompson_BoxMuller_Pair` — line 167 — Caller must ensure u1, u2 ∈ [0, 1).
- `Thompson_Init` — line 185 — applied if caller passes <= 0 for prior/observation precision.
- `Thompson_InitDefault` — line 204 — Typical for unit tests + boot-time init before cfg fields wire in (.B).
- `Thompson_Update` — line 224 — No-op for invalid arm (defensive).
- `Thompson_Sample` — line 302 — Mutates tb->rng_state (advances the PRNG); not thread-safe.
- `Thompson_GetProbabilities` — line 349 — are zeroed.
- `Thompson_GetSoftmaxWeights` — line 402 — are zeroed. Defensive on nullptr / degenerate n_arms < 2.

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

- `CandleAccumulator_Init` — line 98
- `CandleAccumulator_Push` — line 120 — called from engine thread on every tick
- `CandleAccumulator_PushWithTime` — line 180 — instead of using wall-clock time(NULL)
- `CandleAccumulator_Snapshot` — line 264
- `CandleAccumulator_SetInterval` — line 304 — reset accumulator with new interval (clears all candle data)
- `CandleAccumulator_Destroy` — line 330

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
- `GUI_Panel_PerNodePnL` — line 1619 — Pure GUI thread, doesn't touch engine state.
- `GUI_Panel_Stats` — line 1727
- `GUI_Panel_Latency` — line 1829
- `GUI_Panel_MLIntelligence` — line 1894
- `GUI_RenderDashboard` — line 2094

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

- `MLStatus_Render` — line 36 — nullptr; the row is rendered only when a swap is actually pending.

### SettingsPanel.hpp

- `Settings_RescanModels` — line 941 — stays free of opendir/stat (per /readiness check 17 hardening).
- `Settings_Init` — line 1029 — so Settings_Load knows where to read.
- `Settings_Load` — line 1054
- `Settings_RenderGlobalTab` — line 1244
- `Settings_RenderPerCoreTab` — line 1516
- `GUI_Panel_Settings` — line 1962 — running cores, not cfg-only intent — engine doesn't add/remove cores live.

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

- `BacktestData_DetectFormat` — line 80 — timestamp_us,price,quantity,is_buyer_maker
- `BacktestData_Load` — line 87
- `HistoricalTick_CmpByTime` — line 171 — Caller in STRICT mode should treat -1 as "abort run".
- `BacktestData_ValidateSort` — line 179
- `BacktestResults_Init` — line 357
- `BacktestResults_Free` — line 369
- `BacktestResults_Reset` — line 397 — against zero capacity (defense-in-depth) but this is the load-bearing fix.
- `BacktestResults_EnsureCapacity` — line 420 — grow sample buffers by 2x when full
- `BacktestResults_EnsureEquityCapacity` — line 447 — array, so silent truncation produces wrong Sharpe / max DD / return.
- `XGBoost_ComputeScalePosWeight` — line 485
- `XGBoost_ComputeMulticlassWeights` — line 517 — receives per-class sample counts so caller can log them.
- `BacktestStats_Compute` — line 574 — (0.0 = negative, 1.0 = positive, 0.5 = neutral and already filtered).
- `BacktestStats_ComputeFromEquity` — line 618
- `BacktestSharded_Run` — line 661
- `Backtest_ComputeLabelsFromSamples` — line 716 — through samples; no per-file O(N) sample scans.
- `Backtest_Run` — line 987 — equity curve).
- `HeldOutSplit_TrainEval` — line 1168 — helper has visibility into WalkForward_Compute* and XGBoost_Compute* funcs.
- `Backtest_RunWalkForward` — line 1273 — behavior bytewise.
- `Backtest_RunFullValidation` — line 1291
- `WalkForward_ComputeAccuracy` — line 1514 — uses > 0.5f for truth so neutral (0.5) labels are never counted as positive
- `WalkForward_ComputeMulticlassAccuracy` — line 1561 — argmax over each row, compare to integer truth (rounded from label float).
- `WalkForward_ComputeMSE` — line 1580 — regression: mean squared error. Lower = better. Sensitive to outliers.
- `WalkForward_ComputeCorrelation` — line 1596 — gets low MSE on small-magnitude targets while having zero predictive power).
- `Backtest_RunWalkForward` — line 1634
- `HeldOutSplit_TrainEval` — line 2268 — functions it uses (WalkForward_Compute*, XGBoost_Compute*) are visible.
- `ConfigField_Set` — line 2524 — handles both FPN_Binary and PCT fields (PCT keys are stored as decimal, value comes in as %).
- `Backtest_RunSweep` — line 2677 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `Backtest_RunHyperparamTrainSweep` — line 2796 — mean_val_correlation (regression). Stored as positive number; higher = better.

### BacktestPanels.hpp

- `DataPanel_Init` — line 87
- `DataPanel_Scan` — line 107
- `RunControl_Init` — line 257 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `SamplesSnapshot_Compute` — line 283 — only when running==0, giving a safe happens-before relationship.
- `RunControl_Start` — line 510
- `GUI_Panel_DataBrowser` — line 562
- `GUI_Panel_RunControl` — line 673
- `GUI_Panel_Results` — line 749
- `PastRuns_Init` — line 1040
- `PastRuns_LoadOne` — line 1110 — scan one run directory's metadata files
- `PastRuns_DeleteDir` — line 1242
- `PastRun_ParseHorizon` — line 1268 — out_horizon_ticks = 0).
- `PastRuns_ScanOneDir` — line 1322
- `PastRuns_Scan` — line 1359
- `PastRun_MetricLabel` — line 1444 — label-type-aware metric label
- `GUI_Panel_PastRuns` — line 1469 — Pass NULL to keep pre-v5.11.57 behavior (devmode-only).
- `Comparison_Init` — line 2357
- `Comparison_Free` — line 2376
- `Comparison_SaveRun` — line 2398
- `GUI_Panel_Comparison` — line 2451
- `OptimizerPanel_Init` — line 2630 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `GUI_Panel_Optimizer` — line 2695
- `TrainingPanel_Init` — line 3140
- `GUI_Panel_Training` — line 4947

### BacktestSharded.hpp

- `SharedBacktest_FromHistorical` — line 81
- `BacktestSharded_Run` — line 113

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

- `Label_WinLoss` — line 114 — no trade was entered at that point.
- `Label_Barrier` — line 136 — same as win/loss but with configurable asymmetric barriers.
- `Label_ForwardPnl` — line 155 — useful for regression (predict magnitude, not just direction).
- `Label_Regime` — line 176 — MILD_TREND (4) exceeds num_class=4; tracked as TECH_DEBT-241.
- `Label_VolBarrier` — line 200 — source: ~/FoxML/private/DATA_PROCESSING/targets/barrier.py
- `LabelType_NumClasses` — line 497 — ≥2 = multiclass softmax       (label values 0..K-1 as floats)
- `LabelType_IsBinary` — line 502
- `LabelType_IsRegression` — line 506
- `LabelType_IsMulticlass` — line 510

### OverfitDetection.hpp

- `OverfitDetection_CheckDefaults` — line 160 — convenience: check with default FoxML thresholds
- `OverfitDetection_CountOverfit` — line 274 — returns: number of folds flagged as overfit
- `OverfitDetection_Print` — line 285 — print report (for logging / debugging)

### PhaseTimers.hpp

- `PhaseTimer_Global` — line 91 — header inline-only (no separate .cpp).
- `PhaseTimer_Reset` — line 102
- `PhaseTimer_Summary` — line 118 — wf_eval / held_out_eval since it's nested inside both.
- `PhaseTimer_PopulateSnapshot` — line 172

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
