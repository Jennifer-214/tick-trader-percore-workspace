# CODE_MAP.md

Auto-generated function index. Walks .hpp files in each subsystem and extracts `Pattern_FunctionName` style definitions with their one-line purpose (from the preceding `//` comment, when present).

**Re-generate**: `./tools/gen_code_map.sh`

**Last regenerated**: 2026-07-17 (commit e9a8ab8)

## CoreFrameworks/

### BinanceAdapter.hpp

- `BinanceAdapter_WorkerLoop` — line 198
- `BinanceAdapter_Init` — line 322 — shutdown_requested flips.
- `BinanceAdapter_ShutdownState` — line 398 — 1; future commits scale up after the back-to-back stress test passes.
- `BinanceAdapter_SubmitMarketBuy` — line 431 — without a successful Init (shutdown_requested is already 0 by default).
- `BinanceAdapter_SubmitMarketSell` — line 474 — holds with worker_count == 1.
- `BinanceAdapter_GetBalancesImpl` — line 508
- `BinanceAdapter_QueryOrderImpl` — line 543 — pausing submissions during a reconciliation pass.
- `BinanceAdapter_ShutdownImpl` — line 574
- `BinanceAdapter_Get` — line 593

### ControllerConfig.hpp

- `ControllerConfig_CapitalRangeSweep` — line 1479
- `Fee_Compute` — line 1608
- `ControllerConfig_ResolveForCore` — line 1661
- `ControllerConfig_PopulateCoresFromFlat` — line 1724
- `ControllerConfig_NormalizeForMode` — line 2311
- `ControllerConfig_IsLiveCapital` — line 2345
- `ControllerConfig_Load` — line 2387

### ControllerEventLoop.hpp

- `NodeSlowState_Init` — line 184
- `NodeContextDisplayMeta_Init` — line 786
- `Sharded_SlotNode` — line 978 — early consumer precedes the definition (same tt namespace). (D-294)
- `EventLoopState_ReconstructPerCoreFromEventLog` — line 981
- `EventLoopState_Init` — line 1093
- `EventLoopState_InitLegacy` — line 1150
- `EventLoopState_Free` — line 1183
- `EventLoopState_RegisterCore` — line 1244
- `Sharded_LegSlot` — line 1318 — All slow-path / boot-time. Trivially inlined.
- `Sharded_SlotNode` — line 1355 — and ShardedSnapshot.hpp. GUI sites grandfathered for the E-series decouple. (D-294/D-295)
- `Sharded_ValidatePartialExitCfg` — line 1368
- `EventLoopState_SetCoreStrategy` — line 1419
- `EventLoopState_AttachTradeLog` — line 1466
- `EventLoopState_AttachOms` — line 1483
- `EventLoopState_Balance` — line 1501
- `EventLoopState_RealizedPnl` — line 1506
- `EventLoopState_Portfolio` — line 1517
- `EventLoopState_PortfolioMut` — line 1522
- `EventLoopState_KsMinBalance` — line 1527
- `EventLoopState_KsMaxDrawdownPct` — line 1532
- `EventLoopState_KsPeakBalance` — line 1537
- `EventLoopState_TradeLog` — line 1553
- `EventLoopState_SetIntendedParams` — line 1568
- `EventLoop_DrainPostFillOneCore` — line 1586
- `EventLoop_DrainPostFill` — line 2015
- `EventLoop_OnEvent` — line 2104
- `EventLoop_DrainEvents` — line 2288
- `EventLoop_QueueParameters` — line 2331
- `EventLoop_RebuildAllParameters` — line 2369
- `EventLoop_UpdateRollingStateOneCore` — line 2476
- `EventLoop_UpdateEmaPriceAllCores` — line 2519
- `EventLoop_RebuildOneCore` — line 2565
- `EventLoop_PushParameters` — line 3507
- `EventLoopState_ConfigureKillSwitch` — line 3569
- `EventLoop_ClearAllPermissions` — line 3579
- `EventLoop_KillSwitchTrip` — line 3590
- `EventLoop_KillSwitchEvaluate` — line 3619
- `EventLoop_TimeExitOneCore` — line 3685
- `EventLoop_FlattenAll` — line 3787
- `EventLoop_CheckWsStaleness` — line 3869
- `EventLoop_TryClearRecovery` — line 3948
- `EventLoop_TrailingSLRatchetOneCore` — line 4013
- `EventLoop_BreakevenOnProfitOneCore` — line 4111
- `EventLoop_Unpause` — line 4185
- `EventLoop_SlowPath` — line 4209
- `EventLoop_RunController` — line 4234

### EngineCommon.hpp

- `EngineCommon_ApplyBnbDiscount` — line 162
- `EngineCommon_BootGlobal` — line 207
- `EngineCommon_BootPerCore` — line 261
- `EngineCommon_SlowPathCycleOneCore` — line 518
- `EngineCommon_SlowPathCycleAllCores` — line 903

### EnsembleHotSwap.hpp

- `EngineSharded_HotSwapEnsemble` — line 35

### EventLoopAggregates.hpp

- `EventLoop_GetAggregates` — line 122

### ExecutionCore.hpp

- `ExecutionCore_Init` — line 272
- `ExecutionCore_SetParameters` — line 331
- `ExecutionCore_SetPermission` — line 366
- `ExecutionCore_Tick_Impl` — line 403
- `ExecutionCore_Tick` — line 788

### GateParameters.hpp

- `BG_Evaluate` — line 214
- `SG_Evaluate` — line 262
- `GateParameters_Init` — line 291

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

- `NodeModelZoo_ValidateAgainstCfg` — line 131

### NodeLatencyStats.hpp

- `NodeLatencyStats_Init` — line 188
- `NodeLatencyStats_Reset` — line 220 — stats mid-run without disabling them.
- `NodeLatencyStats_Enable` — line 236
- `NodeLatencyStats_Disable` — line 240
- `NodeLatencyStats_Sample` — line 254
- `NodeLatencyStats_Snapshot` — line 296 — rdtsc reading at sample time, used for "last seen" tracking in the TUI.

### Notify.hpp

- `NotifyState_Init` — line 266 — drains remaining events before exiting (per test sidecar Group 5).
- `Notify_Send` — line 297
- `NotifyState_Shutdown` — line 366 — Drain remaining events + join worker thread + free pthread resources.
- `NotifyBackend_Stderr` — line 392
- `Notify_ShellEscape` — line 472
- `Notify_BuildCommand` — line 523 — Document this for users; provide a wrapper script if needed.
- `NotifyBackend_Command` — line 572 — overflowed before completion (still tries to run what fit).

### OrderEventLog.hpp

- `OrderEventLog_Init` — line 320
- `OrderEventLog_Free` — line 386
- `OrderEventLog_ApplyEvent` — line 427
- `OrderEventLog_Append` — line 475
- `OrderEventLog_AsyncWriterRoutine` — line 526
- `OrderEventLog_StartAsyncWriter` — line 574
- `OrderEventLog_StopAsyncWriter` — line 603
- `OrderEventLog_InitWithFile` — line 626
- `OrderEventLog_Reset` — line 715
- `OrderEventLog_LoadFromDisk` — line 771
- `OrderEvent_MakeFill` — line 877
- `OrderEvent_MakeRejection` — line 915
- `Portfolio_FromEventLog` — line 954

### OrderGates.hpp

- `Gate_Zero` — line 91
- `Gate_ZeroAll` — line 98

### Order.hpp

- `Order_GetType` — line 302
- `Order_SetType` — line 306
- `Order_GetState` — line 312
- `Order_SetState` — line 316
- `Order_GetIsMaker` — line 322
- `Order_SetIsMaker` — line 326
- `Order_SetLeg` — line 336
- `Order_SetRetryCount` — line 346
- `Order_GetPreResolvedBound` — line 355
- `Order_MarkPreResolvedBound` — line 359
- `MBS_OrderBanditActiveState` — line 375
- `MBS_OrderBanditRegime` — line 379
- `MBS_OrderBanditChosenArm` — line 383
- `MBS_OrderSetBanditContext` — line 387
- `Order_Init` — line 411
- `Order_BindPreResolved` — line 461
- `Order_WarnIfNotPreResolved` — line 502
- `Order_IsTerminal` — line 554

### OrderManager.hpp

- `OrderManager_Init` — line 938
- `OMS_PushSubmit` — line 1232
- `OMS_DrainSubmit` — line 1283
- `OrderManager_AccountMakerTakerFee` — line 1323
- `OMS_GuardTakerBoundFeeBasis` — line 1365
- `OrderManager_HandleFill` — line 1568
- `OrderManager_ProcessFillCommand` — line 1637
- `OMS_OpenPositionCost` — line 1760
- `OMS_ExpectedFreeCash` — line 1799
- `OrderManager_ProcessReconcile` — line 1843
- `OrderManager_Tick` — line 1890
- `OrderManager_Shutdown` — line 1937
- `OrderManager_OpenCalibrationLog` — line 1962
- `OrderManager_InflightCount` — line 2022

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

- `PortfolioController_Init` — line 322
- `KillSwitch_Activate` — line 580
- `KillSwitch_Reset` — line 594
- `Buying_Halt` — line 603
- `PortfolioController_DrainExits` — line 810
- `PortfolioController_StrategyBuySignal` — line 853
- `PortfolioController_StrategyDispatch` — line 944
- `PortfolioController_Tick` — line 999
- `PortfolioController_Unpause` — line 2021
- `PortfolioController_CycleRegime` — line 2032
- `PortfolioController_HotReload` — line 2058
- `PortfolioController_SaveSnapshot` — line 2142
- `PortfolioController_LoadSnapshot` — line 2217

### Portfolio.hpp

- `ExitBuffer_PendingProceeds` — line 285
- `Portfolio_AddPositionWithExits` — line 394
- `Portfolio_OpenSlot` — line 520
- `Portfolio_OpenSlot` — line 563
- `Money_FillGross` — line 588
- `Portfolio_CloseSlot` — line 615
- `Portfolio_SlotActive` — line 628
- `Portfolio_UpdatePosition` — line 638
- `Portfolio_Save` — line 797
- `Portfolio_Load` — line 851

### Reconcile.hpp

- `ReconcileMode_ToString` — line 159 — Mode → string for logging. Uses cfg_string field (operator-friendly).
- `ReconcileMode_FromString` — line 172 — parse OR error). Accepts cfg_string values from registry.
- `Reconcile_ApplyMissedFills` — line 242
- `Reconcile_AutoCancelStale` — line 420
- `Reconcile_ParseOpenOrders` — line 664
- `Reconcile_ParseMyTrades` — line 710 — Output: fills `out` array up to `out_cap`. Returns count parsed.
- `Reconcile_Decide` — line 754 — Output: fills `out` array up to `out_cap`. Returns count parsed.
- `Reconcile_LogReport` — line 832 — Outputs ReconcileResult with planned actions. Caller applies them.

### ReconciliationLoop.hpp

- `ReconciliationLoop_Pass` — line 129
- `ReconciliationLoop_Init` — line 249
- `ReconciliationLoop_Start` — line 284
- `ReconciliationLoop_TriggerNow` — line 292
- `ReconciliationLoop_Shutdown` — line 306

### ShardedBacktestDriver.hpp

- `ShardedBacktestDriver_Init` — line 170
- `ShardedBacktest_RunTick` — line 229
- `ShardedBacktest_Run` — line 449

### ShardedLiveSafety.hpp

- `EngineSharded_OrphanRecovery` — line 58
- `EngineSharded_ForceCloseOnShutdown` — line 167

### ShardedOrderLatency.hpp

- `ShardedOrderLatency_Reset` — line 78 — before the first order can fire.
- `ShardedOrderLatency_Sample` — line 95

### ShardedSnapshot.hpp

- `TUI_CopySnapshotSharded` — line 54

### ShardedSnapshotPersist.hpp

- `ShardedSnapshot_Save` — line 131
- `ShardedSnapshot_Load` — line 333

### ShardedTradeLog.hpp

- `ShardedTradeLog_FormatPerCoreFilename` — line 128
- `ShardedTradeLog_WriteRow` — line 161 — the next consumer would silently drift. Helper makes drift impossible.
- `ShardedTradeLog_Init` — line 204 — non-fatal — aggregate file already has the row.
- `ShardedTradeLog_Flush` — line 309 — without a trade log, you just don't get the CSV.
- `ShardedTradeLog_Rotate` — line 337 — called once at engine shutdown.
- `ShardedTradeLog_Close` — line 423 — the existing file open).
- `ShardedTradeLog_RecordEntry` — line 454
- `ShardedTradeLog_RecordExit` — line 524

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

- `MeanReversion_Init` — line 99
- `MeanReversion_Adapt` — line 138
- `MeanReversion_BuySignal` — line 315
- `MeanReversion_ExitAdjust` — line 461
- `MeanReversion_ExitAdjustSharded` — line 568

### MLStrategy.hpp

- `MLStrategy_Init` — line 80
- `MLStrategy_Adapt` — line 112
- `MLStrategy_Adapt_Canonical` — line 130
- `MLStrategy_BuySignal` — line 153
- `MLStrategy_ExitAdjust` — line 257
- `MLStrategy_ExitAdjustSharded` — line 322

### Momentum.hpp

- `Momentum_Init` — line 86
- `Momentum_Adapt` — line 119
- `Momentum_BuySignal` — line 215
- `Momentum_ExitAdjust` — line 305
- `Momentum_ExitAdjustSharded` — line 386

### RegimeDetector.hpp

- `CumDelta_Init` — line 199
- `CumDelta_Push` — line 217
- `TickRate_Init` — line 249
- `TickRate_Push` — line 257
- `TickRate_CurrentZ` — line 284
- `Regime_ComputeSignals` — line 308
- `RegimeState_FieldwiseWrite` — line 588
- `RegimeState_FieldwiseRead` — line 597
- `RegimeState_CommitPersistedFields` — line 608
- `Regime_Init` — line 630
- `Regime_Classify` — line 662
- `Regime_ToStrategy` — line 816
- `Regime_AdjustPositions` — line 834

### SimpleDip.hpp

- `SimpleDip_Init` — line 59
- `SimpleDip_Adapt` — line 70
- `SimpleDip_BuySignal` — line 92
- `SimpleDip_ExitAdjustSharded` — line 135

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

- `Strategy_SpacingOk` — line 267
- `Strategy_TpFloor` — line 286
- `GateEgress_MaxPct` — line 310 — FinalizeEmit's range-validate AND the leg-B tp_pct_b clamp below (the A-class leg-B leak fix).
- `GateParameters_FinalizeEmit` — line 313
- `SimpleDip_BuildParameters` — line 425
- `MeanReversion_BuildParameters` — line 506
- `Momentum_BuildParameters` — line 597
- `EmaCross_BuildParameters` — line 727
- `ML_BuildParameters` — line 841
- `Strategy_BuildParameters` — line 1777

## Strategies/private/

### EmaCross.hpp

- `EmaCross_Init` — line 68
- `EmaCross_Adapt` — line 83
- `EmaCross_BuySignal` — line 101
- `EmaCross_ExitAdjust` — line 163
- `EmaCross_ExitAdjustSharded` — line 252

## DataStream/

### BinanceCrypto.hpp

- `BinanceStream_Init` — line 575 — as a min-size sanity guard catches truncated frames without scanning.
- `BinanceStream_Close` — line 648 — clean shutdown: send close frame, SSL shutdown, close socket, free resources
- `BinanceStream_Reconnect` — line 683
- `BinanceStream_Poll` — line 731
- `BinanceStream_ReadTick` — line 795
- `BinanceStream_InWindDown` — line 896 — returns 1 on success (out filled with price + volume), 0 on error/disconnect
- `BinanceStream_ShouldReconnect` — line 909
- `BinanceStream_HasPending` — line 924 — returns 1 if SSL has buffered data that can be read without blocking
- `BinanceConfig_Load` — line 975

### BinanceDepth.hpp

- `DepthStream_Init` — line 275

### BinanceOrderAPI.hpp

- `BinanceOrderAPI_Cleanup` — line 571
- `BinanceOrderAPI_MarketBuy` — line 581 — fill_price_out/fill_qty_out receive actual execution values (NULL = don't care)
- `BinanceOrderAPI_MarketSell` — line 645 — place a market sell order
- `BinanceOrderAPI_CancelOrder` — line 725 — different operator semantics.
- `BinanceOrderAPI_GetStatus` — line 759 — fills filled_qty and avg_price on success
- `BinanceOrderAPI_LoadFilters` — line 808 — returns 1 on success, 0 on failure (caller should treat as fatal)
- `BinanceOrderAPI_GetBalance` — line 843 — returns 1 on success, 0 on failure
- `BinanceOrderAPI_GetOpenOrders` — line 875 — network-independent (testable without real REST calls).
- `BinanceOrderAPI_GetMyTrades` — line 886 — the last-known-processed trade id to catch only new fills.
- `BinanceOrderAPI_GetBalances` — line 902 — returns 1 on success, 0 on failure
- `BinanceOrderAPI_SyncClock` — line 926 — re-sync clock offset (call periodically or after reconnect)
- `BinanceOrderAPI_Init` — line 940 — must be called after Cleanup, ServerTime, SyncClock, LoadFilters are defined

### BinanceUserData.hpp

- `BinanceUserData_Init` — line 678
- `BinanceUserData_Start` — line 714
- `BinanceUserData_Shutdown` — line 720

### CalibLogColRegistry.hpp

- `CalibLog_EmitHeader` — line 177 — Adding a 9th arm later: append 4 more rows + bump BANDIT_MAX_ARMS at BanditLearning.hpp.

### DepthRecorder.hpp

- `DepthRecorder_MkdirP` — line 95 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `DepthRecorder_DateInt` — line 110
- `DepthRecorder_OpenFile` — line 118
- `DepthRecorder_PruneOld` — line 154
- `DepthRecorder_Init` — line 189
- `DepthRecorder_LogGap` — line 225 — disconnect time, or the current snapshot's timestamp_us).
- `DepthRecorder_Write` — line 253
- `DepthRecorder_Close` — line 306

### DepthReplayState.hpp

- `DepthReplay_DateInt` — line 112
- `DepthReplayState_Init` — line 130
- `DepthReplayState_Free` — line 165
- `DepthReplayState_LoadDay` — line 198
- `DepthReplayState_Advance` — line 315
- `DepthReplayState_GetSnapshot` — line 340

### EngineTUI.hpp

- `TUI_Init` — line 169 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `TUI_Cleanup` — line 202
- `TUI_Render` — line 230
- `TUI_HandleInput` — line 622
- `MLSnapshot_Populate` — line 765
- `TUISnapshot_InitSeq` — line 1498 — populated" state) — this only initializes the sequence counter.
- `TUISnapshot_Publish_Begin` — line 1513 — the new active.
- `TUISnapshot_Publish_End` — line 1529 — Any subsequent reader sees the just-filled buffer as active.
- `TUISnapshot_ReadInto` — line 1541 — effectively never observed.
- `TUI_CopySnapshot` — line 1579
- `TUI_CopySnapshot` — line 1585
- `TUI_CopySnapshot` — line 1592
- `TUI_PopulatePerCoreLatency` — line 1870
- `TUI_PopulatePerCoreSlowPathLatency` — line 1917
- `TUI_PopulateAdvancedTopology` — line 1955
- `TUI_PopulateTopology` — line 1999 — poll_interval[i]    — per-core resolved poll cadence
- `TUI_Render_Snapshot` — line 2056 — both dependencies are available.
- `TUI_ReadKey` — line 2267

### FauxFIX.hpp

- `FIX_ParseTag` — line 105 — returns the tag number, writes value start and length into out params
- `FIX_ParseDouble` — line 136 — not meant to be fast, just correct enough for test data
- `FIX_Parse` — line 212 — validates checksum if tag 10 is present
- `FIX_BuildMarketDataMsg` — line 306 — let the caller filter by entry_type if they care

### MetricsLog.hpp

- `MetricsLog_Init` — line 56
- `MetricsLog_Close` — line 78
- `MetricsLog_SlowPath` — line 113
- `MetricsLog_Event` — line 164

### MockGenerator.hpp

- `MockRNG_Seed` — line 44
- `MockRNG_Double` — line 55 — returns a double in [0.0, 1.0)
- `MockRNG_Range` — line 60 — returns a double in [lo, hi)
- `MockGenerator_Init` — line 96
- `MockGenerator_NextTick` — line 119 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `MockGenerator_Batch` — line 149 — buf is scratch space for building FIX messages (reused each tick)

### TickRecorder.hpp

- `TickRecorder_MkdirP` — line 74 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `TickRecorder_DateInt` — line 89
- `TickRecorder_OpenFile` — line 102
- `TickRecorder_PruneOld` — line 137
- `TickRecorder_Init` — line 172
- `TickRecorder_Push` — line 204
- `TickRecorder_Close` — line 238

### TradeLog.hpp

- `TradeLog_Init` — line 100 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `TradeLog_Buy` — line 133
- `TradeLog_Sell` — line 146
- `TradeLog_Close` — line 158
- `TradeLogBuffer_Init` — line 210 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `TradeLogBuffer_PushBuy` — line 216 — hot path: push a record to the ring buffer (~10ns, no file I/O)
- `TradeLogBuffer_PushSell` — line 235
- `TradeLogBuffer_Drain` — line 257 — slow path: drain all buffered records to the CSV file

### TUIAnsi.hpp

- `ANSI_Section_Header` — line 374
- `ANSI_Section_TopBar` — line 448
- `ANSI_Section_Market` — line 479
- `ANSI_Section_Regime` — line 523 — new section: shows R², vol_ratio, ror_slope that weren't in previous TUI backends
- `ANSI_Section_BuyGate` — line 634
- `ANSI_Section_Portfolio` — line 710
- `ANSI_Section_PnL` — line 749
- `ANSI_Section_Risk` — line 774
- `ANSI_Section_Config` — line 802
- `ANSI_Section_Stats` — line 829
- `ANSI_Section_Positions` — line 890
- `ANSI_Section_Charts` — line 967
- `ANSI_Section_Controls` — line 1007
- `ANSI_Section_Latency` — line 1023
- `ANSI_Section_PerNodeLatency` — line 1062 — per-core latency the moment they flip engine_mode=sharded.
- `ANSI_Section_RightPanel` — line 1114 — hidden on narrow terminals (< 100 columns)
- `ANSI_Layout_Standard` — line 1175
- `ANSI_Layout_Charts` — line 1221 — ANSI_Section_RightPanel(ab, s, h, w, start_time);
- `ANSI_Layout_Compact` — line 1259
- `ANSI_Layout_Render` — line 1274
- `ANSI_Render` — line 1296 — call from TUI thread at desired FPS

## FixedPoint/

### FixedPointN.hpp

- `FPN_BlendOnMask` — line 687
- `Money_Mul` — line 1874
- `Money_Div` — line 1915
- `Money_Add` — line 1952 — integer ops with a closure clamp + S-17 flag). Branchless mask-select clamp by the result sign.
- `Money_Add` — line 1960
- `Money_FromString` — line 2124
- `Money_FromBinary` — line 2205
- `Money_Zero` — line 2234 — lower to cmov (same shape as fp2_min/max); BlendOnMask mirrors the live <64> mask-select.
- `Money_Negate` — line 2235
- `Money_Abs` — line 2236
- `Money_Min` — line 2237
- `Money_Max` — line 2238
- `Money_IsZero` — line 2239
- `Money_Lt` — line 2240
- `Money_Le` — line 2241
- `Money_Eq` — line 2242
- `Money_Gt` — line 2243
- `Money_Ge` — line 2244
- `Money_QuantizeToStep` — line 2257
- `Money_BlendOnMask` — line 2279 — NEVER a plain wide divide (no __udivti3 on any path).
- `Money_FromInt` — line 2284 — Money_FromInt: whole-unit int -> money (i*10^8), clamp+flag past the closure ceiling.
- `Money_ToDouble` — line 2293 — Money_ToDouble — DISPLAY-ONLY (H4-exempt): GUI/diag/inf-bridge consumption. Never accounting.
- `Money_ToCString` — line 2358

## MemHeaders/

### DrainerConstants.hpp

- `DrainerConstants_Init` — line 119

### HealthLog.hpp

- `HealthLog_Singleton` — line 132 — Process-singleton. Engine init writes; all callers read.
- `Health_LogConfigureWithRotation` — line 150 — directory still doesn't exist).
- `Health_LogConfigure` — line 186
- `Health_LogPruneRotated` — line 198 — Health_Log (would loop).
- `Health_LogEnabled` — line 227 — "level <= min_level" emits.
- `Health_Log` — line 238 — Returns 1 on success, 0 on i/o failure (ignored by most callers).
- `Health_LogCriticalRateLimited` — line 356 — double-emit-once on race, not data corruption).

### InitArena.hpp

- `InitArena_Create` — line 107 — reservation gets a non-fatal degraded-but-functional path.
- `InitArena_Alloc` — line 152 — are 8 (for plain structs) or 64 (for cache-line-aligned hot structures).
- `InitArena_AllocOne` — line 177
- `InitArena_Destroy` — line 183 — struct). After Destroy, the arena is empty and capacity=0.
- `InitArena_Used` — line 200 — Introspection: how many bytes have been allocated from the arena so far.
- `InitArena_Remaining` — line 206 — is unknown; this is an upper bound).
- `InitArena_Owns` — line 218 — ctrl->rolling_long = nullptr;
- `InitArena_Global` — line 237 — spawn and after they join.

### LatencyHistogram.hpp

- `LatencyHistogram_Reset` — line 167 — instrumentation overhead bound for bench gate ON-state.
- `LatencyHistogram_Accumulate` — line 189

### NodeCtxSummaryFieldRegistry.hpp

- `Summary_EmitPerCoreEntry` — line 239
- `Summary_EmitPerStrategy` — line 280

### OmsPhasedDrain.hpp

- `OmsDrainBuckets_Reset` — line 132
- `OrderType_IsClose` — line 152
- `OrderManager_DrainIntoBuckets` — line 276
- `OrderManager_ProcessBucket_Closes` — line 333
- `OrderManager_ProcessBucket_Opens` — line 349
- `OrderManager_ProcessBucket_Reconciles` — line 362

### OmsPushExitHelper.hpp

- `OMS_PushExitForSlot` — line 77

### RunHistory.hpp

- `RunHistory_Append` — line 92 — defense-in-depth for the HMAC/stamp-adjacent byte-equivalence path.)

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
- `Bandit_Init` — line 199
- `Bandit_InitDefault` — line 222 — convenience: init with default FoxML parameters
- `Bandit_GetProbabilities` — line 249 — tests. Suppress asan here; ubsan + the normal -O3 build still exercise it. (TECH_DEBT-158 close-out.)
- `Bandit_Select` — line 341
- `Bandit_Update` — line 379 — eta    = min(eta_max, sqrt(ln(K) / (K * T)))
- `Bandit_GetWeights` — line 435
- `Bandit_EffectiveBlend` — line 464 — final = (1 - effective_blend) * static + effective_blend * bandit
- `Bandit_BlendWeights` — line 473
- `Bandit_Print` — line 521 — steps >= min+ramp:             effective_blend = blend_ratio
- `Bandit_SaveJSON` — line 567
- `Bandit_LoadJSON` — line 800 — caller's prior Bandit_Init call — load is overlay only.

### BarrierBlendModeRegistry.hpp

- `BarrierBlendMode_BlendDrives` — line 135 — mode is compile-time-known.
- `BarrierBlendMode_DominantDrives` — line 139
- `BarrierBlendMode_ShadowActive` — line 143
- `BarrierBlendMode_IsLegacy` — line 147
- `BarrierBlendMode_ToString` — line 158 — and stamp body cfg-drift comparison.
- `BarrierBlendMode_FromString` — line 167
- `BarrierBlendMode_Doc` — line 178

### BarrierGate.hpp

- `BarrierGate_Compute` — line 52 — compute barrier gate value from peak/valley predictions

### ConfidenceScore.hpp

- `RollingWindow_Init` — line 152
- `RollingWindow_Push` — line 161
- `RollingIC_Init` — line 265 — v5.15.5.E.C — Init via generic RollingWindow_Init on both rings.
- `RollingIC_Push` — line 274 — the parallel-array push semantics for the (prediction, actual) pair shape.
- `RollingIC_Compute` — line 315 — RollingIC_Push). Read either; using predictions's metadata canonically.
- `RollingRMSE_Init` — line 439
- `RollingRMSE_Push` — line 462 — in controller_test.cpp.
- `RollingRMSE_Compute` — line 485 — pattern (the spec tracks its production sites).
- `Confidence_Freshness` — line 513 — stability: 1 / (1 + RMSE)
- `Confidence_Stability` — line 519
- `Confidence_Compute` — line 523
- `RollingFreshness_Init` — line 599
- `RollingFreshness_Mark` — line 604
- `RollingFreshness_Compute` — line 611 — or replay determinism), clamp to 1.0.
- `RollingCapacity_Init` — line 666
- `RollingCapacity_UpdateADV` — line 673
- `RollingCapacity_Compute` — line 683
- `ConfidenceScorer_Init` — line 818
- `ConfidenceScorer_ComputeICVariant` — line 854 — New code + sites being refactored for variant choice use this dispatcher.
- `ConfidenceScorer_InitComposite` — line 862 — explicit composite parameters. Useful for tests + v5.14.1.B cfg wiring.
- `ConfidenceScorer_BindCompositeCfg` — line 892 — FPN_ToDouble(cfg.confidence_rmse_baseline));
- `ConfidenceScorer_Update` — line 905 — feed a prediction + actual return pair (call after outcome is known)
- `ConfidenceScorer_UpdateAndMark` — line 918 — when composite is disabled (composite path is opt-in via cfg).
- `ConfidenceScorer_Compute` — line 927 — compute current confidence given data age
- `ConfidenceScorer_ComputeComposite` — line 951 — stability_normalized = 1 - clamp(rmse / rmse_baseline, 0, 1)
- `ConfidenceScorer_MarkPredict` — line 979 — fixture control.
- `Confidence_DegradationScale_Off` — line 1052 — Forward-declare curve compute fns so the dispatch table can reference them.
- `Confidence_DegradationScale_Linear` — line 1053
- `Confidence_DegradationScale_Exp` — line 1054
- `Confidence_DegradationScale_Step` — line 1055
- `DegradationCurve_ToString` — line 1091 — Auto-generated ToString — for cfg parser + GUI display.
- `DegradationCurve_FromString` — line 1102 — numeric ("1") forms; case-insensitive on string form. Returns -1 on miss.
- `Confidence_DegradationScale_Off` — line 1127 — when cfg.risk_degradation_curve=0 (default).
- `Confidence_DegradationScale_Linear` — line 1135 — To get ladder-bottom (factor=0), operator sets min_pct=0.0.
- `Confidence_DegradationScale_Exp` — line 1145 — as LINEAR.
- `Confidence_DegradationScale_Step` — line 1156 — without continuous-curve noise.
- `Confidence_DegradationScale` — line 1164 — out-of-range returns 1.0 (degrades safely to OFF behavior).
- `DriftHistory_Init` — line 1323
- `DriftHistory_Push` — line 1331 — + ts_us[idx], 2 separate cache lines 2048B apart).
- `DriftHistory_CheckBreach` — line 1349 — at typical 10-100Hz cadence.
- `ConfidenceScorer_FieldwiseWrite` — line 1411
- `ConfidenceScorer_FieldwiseRead` — line 1420
- `ConfidenceScorer_CommitPersistedFields` — line 1432
- `ConfidenceScorer_RecomputeRunningSums` — line 1455 — CommitPersistedFields tail; PortfolioController calls it explicitly.
- `ConfidenceScorer_ShadowLoadLegacyV1` — line 1575

### CostModel.hpp

- `CostModel_Estimate` — line 71 — k1, k2, k3:     cost coefficients
- `CostModel_EstimateDefault` — line 98 — convenience: estimate with default coefficients
- `CostModel_Breakeven` — line 108 — cost is in bps, divide by 10000 to get decimal return
- `CostModel_ShouldTrade` — line 113 — should we trade? returns 1 if expected alpha > breakeven

### EzooInitFlagRegistry.hpp

- `EzooInitFlag_ToString` — line 116 — CRITICAL log lines + diagnostic panels.

### FeatureRegistry.hpp

- `ML_Compute_ShortSlope` — line 159
- `ML_Compute_ShortR2` — line 164
- `ML_Compute_ShortVariance` — line 169
- `ML_Compute_LongSlope` — line 174
- `ML_Compute_LongR2` — line 179
- `ML_Compute_LongVariance` — line 184
- `ML_Compute_VolRatio` — line 189
- `ML_Compute_RorSlope` — line 194
- `ML_Compute_VolumeSlope` — line 199
- `ML_Compute_VolumeDelta` — line 204
- `ML_Compute_EmaSmaSpread` — line 223
- `ML_Compute_VwapDev` — line 228
- `ML_Compute_PriceStddev` — line 233
- `ML_Compute_PriceAvg` — line 238
- `ML_Compute_VolumeAvg` — line 243
- `ML_Compute_EmaAboveSma` — line 248
- `ML_Compute_MidSlope` — line 255
- `ML_Compute_MidR2` — line 260
- `ML_Compute_CumDelta` — line 265
- `ML_Compute_HourSin` — line 270
- `ML_Compute_HourCos` — line 275
- `ML_Compute_VolRegimeRatio` — line 280
- `ML_Compute_TickRateZ` — line 285
- `ML_Compute_DistToHigh` — line 290
- `ML_Compute_DistToLow` — line 295
- `ML_Compute_BookImbMeanShort` — line 300
- `ML_Compute_BookImbMeanLong` — line 305
- `ML_Compute_BookImbDrift` — line 310
- `ML_Compute_Flow10s` — line 315
- `ML_Compute_Flow1m` — line 320
- `ML_Compute_Flow5m` — line 325
- `ML_Compute_LargeTradeZ` — line 330
- `ML_Compute_SpreadBps` — line 335
- `ML_Compute_SpreadZscore` — line 340
- `ML_Compute_RegimeTrendStrength` — line 371
- `ML_Compute_RegimeVolZscore` — line 386
- `ML_Compute_RegimeClassOneHot` — line 408
- `ML_Compute_FracDiffPrice_d04` — line 479
- `ML_Compute_FracDiffPrice_d05` — line 484
- `ML_Compute_FracDiffPrice_d06` — line 489
- `Features_PackAll` — line 720
- `Features_PackAll` — line 802

### FeatureRegistryOverlay.hpp

- `FeatureOverlay_ParseLayer2HashFromSidecar` — line 80 — key and ":" handled).
- `FeatureOverlay_PostLoadVerify` — line 162

### FeatureStandardizer.hpp

- `FeatureStandardizer_Init` — line 201
- `FeatureStandardizer_Apply` — line 244 — recommended for clarity.
- `FeatureStandardizer_Load` — line 316 — ---- the sidecar body field-map: tier-2 [WIRE_FIELD] members, ordinal-addressed (D-345) ----
- `FeatureStandardizer_VerifyAgainstBuild` — line 432 — has_scaler=1 if all upstream checks (registry_hash match) pass.
- `FeatureStandardizer_FitWinsor` — line 476 — training-side cost. Slow-path slow.
- `FeatureStandardizer_Compute` — line 514
- `FeatureStandardizer_Persist` — line 554 — Returns 1 on success, 0 on I/O failure.
- `FeatureStandardizer_Free` — line 631 — Persist writes the sidecar via atomic write (.tmp + rename).

### FlowFeatures.hpp

- `BookImbHistory_Init` — line 159
- `BookImbHistory_Push` — line 169
- `BookImbHistory_MeanLong` — line 199
- `BookImbHistory_MeanShortFast` — line 216
- `BookImbHistory_Last` — line 226
- `BookImbHistory_MeanShort` — line 235
- `FlowState_Init` — line 328
- `FlowState_Push` — line 341 — Full RegimeSignals→FPN_Binary cascade is a v5.11 ship (large blast radius).
- `LargeTradeState_Init` — line 462
- `LargeTradeState_Push` — line 472
- `LargeTradeState_ZScore` — line 495
- `LargeTradeState_Last` — line 511
- `SpreadState_Init` — line 603
- `SpreadState_Push` — line 613
- `SpreadState_ZScore` — line 631
- `SpreadState_Last` — line 646

### LinearRegression3X.hpp

- `RegressionFeederX_FieldwiseWrite` — line 89
- `RegressionFeederX_FieldwiseRead` — line 98
- `RegressionFeederX_CommitPersistedFields` — line 107

### ModelInference.hpp

- `FeatureLookback_Max` — line 264
- `FeatureLookback_CountEnabled` — line 274 — count enabled features (for validation)
- `Model_Init` — line 500
- `Model_Load` — line 548
- `Model_Predict_Normalized` — line 683
- `Model_Predict_AtClass` — line 746
- `Model_LoadAOT` — line 809
- `Model_Predict_AOT` — line 823
- `Model_Predict` — line 867
- `Model_Predict_Ensemble` — line 951
- `Model_Predict_Ensemble_Weighted` — line 1037
- `Model_PredictMulti` — line 1182
- `Model_Free` — line 1258
- `Model_IsLoaded` — line 1278
- `ModelFeatures_Pack` — line 1301

### NodeModelZoo.hpp

- `NodeModelZoo_Init` — line 157
- `NodeModelZoo_TryLoadRole` — line 184
- `NodeModelZoo_LoadFromDir` — line 662
- `NodeModelZoo_LoadLegacy` — line 771
- `NodeModelZoo_Free` — line 781
- `NodeModelZoo_HasAny` — line 790
- `NodeModelZoo_VerifyExpected` — line 828 — features in the pack, model crashes or produces garbage.
- `EnsembleZoo_FinalizeCorrupt` — line 1357
- `EnsembleModelZoo_Init` — line 1395
- `EnsembleModelZoo_EnsurePrimary` — line 1488
- `EnsembleModelZoo_RecordPrediction` — line 1544
- `EnsembleModelZoo_UpdateDrift` — line 1573
- `EnsembleModelZoo_TickRewardsFromLookback` — line 1626
- `EnsembleModelZoo_TradeCloseReward` — line 1710
- `EnsembleModelZoo_InitBandits` — line 1779
- `EnsembleModelZoo_InitExitBandits` — line 1827
- `EnsembleModelZoo_InitBuyThompsonBandits` — line 1882
- `EnsembleModelZoo_InitExitThompsonBandits` — line 1934
- `EnsembleModelZoo_SetDisabledHorizons` — line 1997
- `EnsembleModelZoo_Free` — line 2025
- `EnsembleModelZoo_LoadFromCfg` — line 2069
- `EnsembleZoo_VerifyGridMemberConsistency` — line 2357
- `EnsembleModelZoo_AutoDetectFromDir` — line 2427
- `EnsembleModelZoo_ComputeBundleId` — line 2584
- `EnsembleModelZoo_SaveBanditState` — line 2609
- `EnsembleModelZoo_SaveExitBanditState` — line 2631
- `EnsembleModelZoo_LoadBanditState` — line 2655
- `EnsembleModelZoo_LoadExitBanditState` — line 2686
- `EnsembleModelZoo_SaveThompsonState` — line 2743
- `EnsembleModelZoo_SaveExitThompsonState` — line 2831
- `EnsembleModelZoo_LoadThompsonState` — line 2914
- `EnsembleModelZoo_LoadExitThompsonState` — line 3047
- `EnsembleModelZoo_LoadBanditStateFromPath` — line 3190
- `EnsembleModelZoo_SetBanditSaveInterval` — line 3217
- `EnsembleModelZoo_MaybeSaveBanditPeriodic` — line 3235
- `EnsembleModelZoo_PostLoadSetup` — line 3371
- `EnsembleModelZoo_IsReadyForInference` — line 3390
- `NodeModelZoo_PostLoadSetup` — line 3443
- `NodeModelZoo_CheckStaleModel` — line 3478

### PerArmFlagRegistry.hpp

- `PerArmFlag_ToString` — line 144 — diagnostic panels.

### RewardTracker.hpp

- `RewardTracker_Init` — line 70 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `RewardTracker_Push` — line 75
- `RewardTracker_DrainCSV` — line 92 — append all pending records to CSV, then clear

### RidgeBlender.hpp

- `Cholesky_Solve` — line 186
- `RidgeBlender_Compute` — line 329
- `RidgeBlender_FinalizeCorrFromSums` — line 424
- `RidgeBlender_BuildCorr` — line 541 — byte-determinism tests). Sister to Bandit_GetProbabilities. TECH_DEBT-158.
- `RidgeBlender_UpdateOnline` — line 644
- `RidgeBlender_BuildHistoryFromRing` — line 793
- `RidgeBlender_OnlineCycleStep` — line 853
- `RidgeWeights_Init` — line 945

### RollingStats.hpp

- `RollingStats_Push` — line 266
- `RollingStats_VolumeSignificant` — line 517
- `RollingStats_EntrySpacing` — line 542
- `RollingStats_BuyPrice` — line 572

### RollingTurnover.hpp

- `RollingTurnover_Init` — line 60 — Validates window + topk; clamps to safe range. Zero-init buffers.
- `RollingTurnover_Push` — line 127 — exactly K bits. Yields [0, 1] range.
- `RollingTurnover_Compute` — line 159 — until profiler flags this as load-bearing.

### ROR_regressor.hpp

- `RORRegressor_Init` — line 50
- `RORRegressor_Push` — line 72

### StampHelper.hpp

- `Stamp_AssembleAndEmit` — line 170

### ThompsonBandit.hpp

- `Thompson_RawToUniform` — line 153 — Muller's log(0) handling).
- `Thompson_BoxMuller_Pair` — line 165 — Caller must ensure u1, u2 ∈ [0, 1).
- `Thompson_Init` — line 183 — applied if caller passes <= 0 for prior/observation precision.
- `Thompson_InitDefault` — line 202 — Typical for unit tests + boot-time init before cfg fields wire in (.B).
- `Thompson_Update` — line 222 — No-op for invalid arm (defensive).
- `Thompson_Sample` — line 300 — Mutates tb->rng_state (advances the PRNG); not thread-safe.
- `Thompson_GetProbabilities` — line 347 — are zeroed.
- `Thompson_GetSoftmaxWeights` — line 400 — are zeroed. Defensive on nullptr / degenerate n_arms < 2.

### VolScaler.hpp

- `VolScaler_Size` — line 50 — default parameters (from FoxML DEFAULT_CONFIG)
- `VolScaler_SizeDefault` — line 65 — convenience: scale with default parameters
- `VolScaler_InverseAlpha` — line 73 — useful for: "what alpha does this position size imply?"
- `VolScaler_RawZ` — line 81 — raw z-score without clipping (for analytics / display)

### WelfordStats.hpp

- `Welford_Init` — line 43
- `Welford_Push` — line 55
- `Welford_Variance` — line 83
- `Welford_Stddev` — line 92
- `Welford_ZScore` — line 100
- `Welford_Reset` — line 109

## GUI/

### CandleAccumulator.hpp

- `CandleAccumulator_Init` — line 86 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `CandleAccumulator_Push` — line 108 — called from engine thread on every tick
- `CandleAccumulator_PushWithTime` — line 168 — instead of using wall-clock time(NULL)
- `CandleAccumulator_Snapshot` — line 246 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `CandleAccumulator_SetInterval` — line 286 — reset accumulator with new interval (clears all candle data)
- `CandleAccumulator_Destroy` — line 312

### ChartPanel.hpp

- `ChartState_Prepare` — line 116 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `GUI_PriceChart` — line 222 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `GUI_VolumeChart` — line 1256
- `GUI_LivePnLChart` — line 1386
- `GUI_EquityChart` — line 1458

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

- `LogViewer_Init` — line 57 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `LogViewer_Refresh` — line 78
- `GUI_Panel_LogViewer` — line 122

### MLStatusPanel.hpp

- `MLStatus_Render` — line 36 — nullptr; the row is rendered only when a swap is actually pending.

### SettingsPanel.hpp

- `Settings_RescanModels` — line 929 — stays free of opendir/stat (per /readiness check 17 hardening).
- `Settings_Init` — line 1017 — so Settings_Load knows where to read.
- `Settings_Load` — line 1042
- `Settings_RenderGlobalTab` — line 1232
- `Settings_RenderPerCoreTab` — line 1504
- `GUI_Panel_Settings` — line 1950 — running cores, not cfg-only intent — engine doesn't add/remove cores live.

### StrategyQualityPanel.hpp

- `StrategyQuality_Init` — line 94 — log path is passed at render time via GUI_Panel_StrategyQuality).
- `StrategyQuality_Refresh` — line 239
- `GUI_Panel_StrategyQuality` — line 331

### TradeHistoryPanel.hpp

- `TradeHistory_Init` — line 87 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `TradeHistory_Refresh` — line 107
- `GUI_Panel_TradeHistory` — line 254

### TradeReader.hpp

- `TradeData_Init` — line 74 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `TradeData_Refresh` — line 141

## Backtest/

### BacktestEngine.hpp

- `BacktestData_DetectFormat` — line 80 — timestamp_us,price,quantity,is_buyer_maker
- `BacktestData_Load` — line 87
- `HistoricalTick_CmpByTime` — line 171 — Caller in STRICT mode should treat -1 as "abort run".
- `BacktestData_ValidateSort` — line 179
- `BacktestResults_Init` — line 345
- `BacktestResults_Free` — line 357
- `BacktestResults_Reset` — line 385 — against zero capacity (defense-in-depth) but this is the load-bearing fix.
- `BacktestResults_EnsureCapacity` — line 408 — grow sample buffers by 2x when full
- `BacktestResults_EnsureEquityCapacity` — line 435 — array, so silent truncation produces wrong Sharpe / max DD / return.
- `XGBoost_ComputeScalePosWeight` — line 467 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `XGBoost_ComputeMulticlassWeights` — line 499 — receives per-class sample counts so caller can log them.
- `BacktestStats_Compute` — line 556 — (0.0 = negative, 1.0 = positive, 0.5 = neutral and already filtered).
- `BacktestStats_ComputeFromEquity` — line 600
- `BacktestSharded_Run` — line 643
- `Backtest_ComputeLabelsFromSamples` — line 698 — through samples; no per-file O(N) sample scans.
- `Backtest_Run` — line 969 — equity curve).
- `HeldOutSplit_TrainEval` — line 1122 — helper has visibility into WalkForward_Compute* and XGBoost_Compute* funcs.
- `Backtest_RunWalkForward` — line 1221 — behavior bytewise.
- `Backtest_RunFullValidation` — line 1239
- `WalkForward_ComputeAccuracy` — line 1462 — uses > 0.5f for truth so neutral (0.5) labels are never counted as positive
- `WalkForward_ComputeMulticlassAccuracy` — line 1509 — argmax over each row, compare to integer truth (rounded from label float).
- `WalkForward_ComputeMSE` — line 1528 — regression: mean squared error. Lower = better. Sensitive to outliers.
- `WalkForward_ComputeCorrelation` — line 1544 — gets low MSE on small-magnitude targets while having zero predictive power).
- `Backtest_RunWalkForward` — line 1582
- `HeldOutSplit_TrainEval` — line 2216 — functions it uses (WalkForward_Compute*, XGBoost_Compute*) are visible.
- `ConfigField_Set` — line 2472 — handles both FPN_Binary and PCT fields (PCT keys are stored as decimal, value comes in as %).
- `Backtest_RunSweep` — line 2603 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `Backtest_RunHyperparamTrainSweep` — line 2722 — mean_val_correlation (regression). Stored as positive number; higher = better.

### BacktestPanels.hpp

- `DataPanel_Init` — line 81 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `DataPanel_Scan` — line 101
- `RunControl_Init` — line 245 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `SamplesSnapshot_Compute` — line 271 — only when running==0, giving a safe happens-before relationship.
- `RunControl_Start` — line 482
- `GUI_Panel_DataBrowser` — line 534
- `GUI_Panel_RunControl` — line 645
- `GUI_Panel_Results` — line 721
- `PastRuns_Init` — line 994 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `PastRuns_LoadOne` — line 1064 — scan one run directory's metadata files
- `PastRuns_DeleteDir` — line 1196
- `PastRun_ParseHorizon` — line 1222 — out_horizon_ticks = 0).
- `PastRuns_ScanOneDir` — line 1276
- `PastRuns_Scan` — line 1313
- `PastRun_MetricLabel` — line 1398 — label-type-aware metric label
- `GUI_Panel_PastRuns` — line 1423 — Pass NULL to keep pre-v5.11.57 behavior (devmode-only).
- `Comparison_Init` — line 2311
- `Comparison_Free` — line 2330
- `Comparison_SaveRun` — line 2352
- `GUI_Panel_Comparison` — line 2405
- `OptimizerPanel_Init` — line 2584 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `GUI_Panel_Optimizer` — line 2649
- `TrainingPanel_Init` — line 3088 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `GUI_Panel_Training` — line 4819

### BacktestSharded.hpp

- `SharedBacktest_FromHistorical` — line 81
- `BacktestSharded_Run` — line 113

### BacktestSnapshot.hpp

- `BacktestSnapshot_Copy` — line 35

### Fingerprint.hpp

- `SHA256_Init` — line 93
- `SHA256_Update` — line 100
- `SHA256_Final` — line 118
- `SHA256_ToHex` — line 140 — convenience: hash to hex string (65 bytes including null terminator)
- `Fingerprint_HashFile` — line 165
- `Fingerprint_Compute` — line 210
- `Fingerprint_Short` — line 239 — short fingerprint (first 12 hex chars) for display

### HeldOutSplit.hpp

- `HeldOutSplit_GenToken` — line 109 — non-reproducible by construction. Removed.
- `HeldOutSplit_Make` — line 137
- `HeldOutSplit_TestAccessAllowed` — line 172 — refuse-if-locked checks).
- `HeldOutSplit_Unlock` — line 178 — Logs unlock event to stderr — caller can also Notify_Send for audit trail.
- `HeldOutSplit_Relock` — line 200 — not _Relock.

### LabelFunctions.hpp

- `Label_WinLoss` — line 108 — no trade was entered at that point.
- `Label_Barrier` — line 130 — same as win/loss but with configurable asymmetric barriers.
- `Label_ForwardPnl` — line 149 — useful for regression (predict magnitude, not just direction).
- `Label_Regime` — line 170 — MILD_TREND (4) exceeds num_class=4; tracked as TECH_DEBT-241.
- `Label_VolBarrier` — line 194 — source: ~/FoxML/private/DATA_PROCESSING/targets/barrier.py
- `LabelType_NumClasses` — line 469 — ≥2 = multiclass softmax       (label values 0..K-1 as floats)
- `LabelType_IsBinary` — line 474
- `LabelType_IsRegression` — line 478
- `LabelType_IsMulticlass` — line 482

### OverfitDetection.hpp

- `OverfitDetection_CheckDefaults` — line 154 — convenience: check with default FoxML thresholds
- `OverfitDetection_CountOverfit` — line 268 — returns: number of folds flagged as overfit
- `OverfitDetection_Print` — line 279 — print report (for logging / debugging)

### PhaseTimers.hpp

- `PhaseTimer_Global` — line 85 — header inline-only (no separate .cpp).
- `PhaseTimer_Reset` — line 96
- `PhaseTimer_Summary` — line 112 — wf_eval / held_out_eval since it's nested inside both.
- `PhaseTimer_PopulateSnapshot` — line 166

### ValidationSplit.hpp

- `PurgeGap_Compute` — line 83 — first test tick to prevent any form of temporal leakage.
- `PurgeGap_ComputeExplicit` — line 90 — overload: caller provides explicit max_lookback (for testing or custom feature sets)
- `ValidationSplit_Generate` — line 147 — [DERIVED]   (tool-refreshed — layout emitter cannot probe this block yet; quartet lands when the emitter covers it, D...
- `ValidationSplit_GenerateExplicit` — line 251 — used by walk-forward when splitting in non-neutral sample space where raw lookback doesn't apply
- `ValidationSplit_Verify` — line 315 — production leakage guard; this standalone form is available for tests)
- `ValidationSplit_Print` — line 336 — print fold summary (for logging / debugging)

### XGBHyperparams.hpp

- `XGBHyperparams_Defaults` — line 91 — modify the returned struct in-place.
- `XGBHyperparams_Apply` — line 102 — WF/HeldOut/full-validation; both default 4, boot-only). Caller chooses.

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
