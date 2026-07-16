# Code-tag index (auto-generated snapshot)

**Auto-generated** by `tools/rebuild_doc_indexes.py --target code-tag-index` — the
CODE-side twin of `DESIGN_SPECS/TAG_INDEX.md`. Canonical reverse-lookup is `rg` over
the engine tree:

```bash
rg -l '\[TAG\]_\[\[SLOW_PATH' --glob '*.hpp'   # files tagged [SLOW_PATH]
rg -n '\[FUNCTION\]_\['                         # converted function blocks (with lines)
```

Snapshot for static browsing; regen via `/index-rebuild` (the `--check` currency guard
reds a stale copy). Line numbers are deliberately OMITTED — file-level granularity only,
so the snapshot stales when tags/units actually change, not on unrelated line drift;
`rg` gives exact locations. The DOCS/ template corpus is excluded (copy-source, not a
conversion).

Converted files: 27 · unit blocks: 154

## [TAG] values → files

### BINARY_FP (1 files)

- `Strategies/RegimeDetector.hpp`

### BITMAP_PACKED (6 files)

- `CoreFrameworks/GateCfgFlagRegistry.hpp`
- `CoreFrameworks/LifecycleCfgFlagRegistry.hpp`
- `CoreFrameworks/OpsCfgFlagRegistry.hpp`
- `CoreFrameworks/Order.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/RiskCfgFlagRegistry.hpp`

### BOOT_TIME (11 files)

- `CoreFrameworks/EngineSharded/Boot.hpp`
- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/OrderEventLog.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/ReconciliationLoop.hpp`
- `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/SystemInit.hpp`

### CAPITAL_BEARING (10 files)

- `CoreFrameworks/EngineSharded/SlowPath.hpp`
- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/Order.hpp`
- `CoreFrameworks/OrderEventLog.hpp`
- `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/ReconciliationLoop.hpp`
- `CoreFrameworks/TradeEvent.hpp`

### CFG_FLOW (4 files)

- `CoreFrameworks/GateCfgFlagRegistry.hpp`
- `CoreFrameworks/LifecycleCfgFlagRegistry.hpp`
- `CoreFrameworks/OpsCfgFlagRegistry.hpp`
- `CoreFrameworks/RiskCfgFlagRegistry.hpp`

### CONCURRENCY (10 files)

- `CoreFrameworks/EngineSharded/Boot.hpp`
- `CoreFrameworks/ExchangeAdapter.hpp`
- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/OrderEventLog.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/ReconciliationLoop.hpp`
- `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/ShardedOrderLatency.hpp`
- `CoreFrameworks/TradeEvent.hpp`

### CRITICAL (5 files)

- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/SystemInit.hpp`

### DATA_ORIENTED_DESIGN (8 files)

- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/Order.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/Tick.hpp`

### DATA_PLANE (2 files)

- `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/Tick.hpp`

### DECIMAL (7 files)

- `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/Order.hpp`
- `CoreFrameworks/OrderEventLog.hpp`
- `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/Tick.hpp`

### DETERMINISM (2 files)

- `CoreFrameworks/OrderEventLog.hpp`
- `CoreFrameworks/SystemInit.hpp`

### ENGINE (26 files)

- `CoreFrameworks/EngineSharded.hpp`
- `CoreFrameworks/EngineSharded/Boot.hpp`
- `CoreFrameworks/EngineSharded/SlowPath.hpp`
- `CoreFrameworks/ExchangeAdapter.hpp`
- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateCfgFlagRegistry.hpp`
- `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/LifecycleCfgFlagRegistry.hpp`
- `CoreFrameworks/MetaRegistry.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/OpsCfgFlagRegistry.hpp`
- `CoreFrameworks/Order.hpp`
- `CoreFrameworks/OrderEventLog.hpp`
- `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/ReconciliationLoop.hpp`
- `CoreFrameworks/RiskCfgFlagRegistry.hpp`
- `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/ShardedOrderLatency.hpp`
- `CoreFrameworks/SpSectionRegistry.hpp`
- `CoreFrameworks/SystemInit.hpp`
- `CoreFrameworks/Tick.hpp`
- `CoreFrameworks/TradeEvent.hpp`
- `Strategies/RegimeDetector.hpp`

### ENTRY_POINT (2 files)

- `CoreFrameworks/EngineSharded.hpp`
- `CoreFrameworks/ExchangeAdapter.hpp`

### FLOAT_DISPLAY_ONLY (2 files)

- `CoreFrameworks/ExchangeAdapter.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp`

### FRAMEWORK_DISCIPLINE (2 files)

- `CoreFrameworks/MetaRegistry.hpp`
- `Strategies/StrategyInterface.hpp`

### GUI (1 files)

- `CoreFrameworks/EngineSharded/SlowPath.hpp`

### HELPER (1 files)

- `CoreFrameworks/OrderEventLog.hpp`

### HOT_PATH (8 files)

- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/Tick.hpp`
- `CoreFrameworks/TradeEvent.hpp`

### LIVE_TRADING (5 files)

- `CoreFrameworks/ExchangeAdapter.hpp`
- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/ReconciliationLoop.hpp`
- `CoreFrameworks/ShardedOrderLatency.hpp`

### ML (2 files)

- `CoreFrameworks/OrderManager.hpp`
- `Strategies/RegimeDetector.hpp`

### MONITORING_PLANE (4 files)

- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/ShardedOrderLatency.hpp`
- `CoreFrameworks/SpSectionRegistry.hpp`

### OMS_DRAINER (4 files)

- `CoreFrameworks/EngineSharded/SlowPath.hpp`
- `CoreFrameworks/Order.hpp`
- `CoreFrameworks/OrderEventLog.hpp`
- `CoreFrameworks/OrderManager.hpp`

### PERSISTENCE (3 files)

- `CoreFrameworks/Order.hpp`
- `CoreFrameworks/OrderEventLog.hpp`
- `CoreFrameworks/Portfolio.hpp`

### SLOW_PATH (7 files)

- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/SpSectionRegistry.hpp`
- `Strategies/RegimeDetector.hpp`

### STRUCTURAL_FIX (1 files)

- `CoreFrameworks/Portfolio.hpp`

### SUPPORTIVE (5 files)

- `CoreFrameworks/Order.hpp`
- `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/ReconciliationLoop.hpp`

## Unit blocks by [TYPE]

### ASSERT (8)

- `EPOCH_TRIPWIRE` — `CoreFrameworks/OrderEventLog.hpp`
- `EPOCH_TRIPWIRE` — `CoreFrameworks/Portfolio.hpp`
- `LAYOUT_LOCK` — `CoreFrameworks/ExecutionCore.hpp`
- `LAYOUT_LOCK` — `CoreFrameworks/GateParameters.hpp`
- `LAYOUT_LOCK` — `CoreFrameworks/Order.hpp`
- `LAYOUT_LOCK` — `CoreFrameworks/Portfolio.hpp`
- `LAYOUT_LOCK` — `CoreFrameworks/Tick.hpp`
- `LAYOUT_LOCK` — `CoreFrameworks/TradeEvent.hpp`

### ENUM (4)

- `CommandType` — `CoreFrameworks/OrderManager.hpp`
- `OrderEventType` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderState` — `CoreFrameworks/Order.hpp`
- `OrderType` — `CoreFrameworks/Order.hpp`

### FILE (26)

- `CoreFrameworks/EngineSharded.hpp` — `CoreFrameworks/EngineSharded.hpp`
- `CoreFrameworks/EngineSharded/Boot.hpp` — `CoreFrameworks/EngineSharded/Boot.hpp`
- `CoreFrameworks/EngineSharded/SlowPath.hpp` — `CoreFrameworks/EngineSharded/SlowPath.hpp`
- `CoreFrameworks/ExchangeAdapter.hpp` — `CoreFrameworks/ExchangeAdapter.hpp`
- `CoreFrameworks/ExecutionCore.hpp` — `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateCfgFlagRegistry.hpp` — `CoreFrameworks/GateCfgFlagRegistry.hpp`
- `CoreFrameworks/GateParameters.hpp` — `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/LifecycleCfgFlagRegistry.hpp` — `CoreFrameworks/LifecycleCfgFlagRegistry.hpp`
- `CoreFrameworks/MetaRegistry.hpp` — `CoreFrameworks/MetaRegistry.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp` — `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/OpsCfgFlagRegistry.hpp` — `CoreFrameworks/OpsCfgFlagRegistry.hpp`
- `CoreFrameworks/Order.hpp` — `CoreFrameworks/Order.hpp`
- `CoreFrameworks/OrderEventLog.hpp` — `CoreFrameworks/OrderEventLog.hpp`
- `CoreFrameworks/OrderGates.hpp` — `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/OrderManager.hpp` — `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/ParameterSlot.hpp` — `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/Portfolio.hpp` — `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/ReconciliationLoop.hpp` — `CoreFrameworks/ReconciliationLoop.hpp`
- `CoreFrameworks/RiskCfgFlagRegistry.hpp` — `CoreFrameworks/RiskCfgFlagRegistry.hpp`
- `CoreFrameworks/SPSCRing.hpp` — `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/ShardedOrderLatency.hpp` — `CoreFrameworks/ShardedOrderLatency.hpp`
- `CoreFrameworks/SpSectionRegistry.hpp` — `CoreFrameworks/SpSectionRegistry.hpp`
- `CoreFrameworks/SystemInit.hpp` — `CoreFrameworks/SystemInit.hpp`
- `CoreFrameworks/Tick.hpp` — `CoreFrameworks/Tick.hpp`
- `CoreFrameworks/TradeEvent.hpp` — `CoreFrameworks/TradeEvent.hpp`
- `RegimeDetector.hpp` — `Strategies/RegimeDetector.hpp`

### FUNCTION (73)

- `BG_Evaluate` — `CoreFrameworks/GateParameters.hpp`
- `BuyGate` — `CoreFrameworks/OrderGates.hpp`
- `CumDelta_Init` — `Strategies/RegimeDetector.hpp`
- `EngineSharded_SignalHandler` — `CoreFrameworks/EngineSharded/Boot.hpp`
- `EngineSharded_SlowPath_DrainManualCloses` — `CoreFrameworks/EngineSharded/SlowPath.hpp`
- `EngineSharded_SlowPath_DrainPostFill` — `CoreFrameworks/EngineSharded/SlowPath.hpp`
- `ExecutionCore_Init` — `CoreFrameworks/ExecutionCore.hpp`
- `ExecutionCore_SetParameters` — `CoreFrameworks/ExecutionCore.hpp`
- `ExecutionCore_SetPermission` — `CoreFrameworks/ExecutionCore.hpp`
- `ExecutionCore_Tick` — `CoreFrameworks/ExecutionCore.hpp`
- `ExecutionCore_Tick_Impl` — `CoreFrameworks/ExecutionCore.hpp`
- `ExitBuffer_PendingProceeds` — `CoreFrameworks/Portfolio.hpp`
- `GateParameters_Init` — `CoreFrameworks/GateParameters.hpp`
- `Money_FillGross` — `CoreFrameworks/Portfolio.hpp`
- `NodeLatencyStats_Init` — `CoreFrameworks/NodeLatencyStats.hpp`
- `NodeLatencyStats_Reset` — `CoreFrameworks/NodeLatencyStats.hpp`
- `NodeLatencyStats_Sample` — `CoreFrameworks/NodeLatencyStats.hpp`
- `NodeLatencyStats_Snapshot` — `CoreFrameworks/NodeLatencyStats.hpp`
- `OMS_DrainSubmit` — `CoreFrameworks/OrderManager.hpp`
- `OMS_ExpectedFreeCash` — `CoreFrameworks/OrderManager.hpp`
- `OMS_GuardTakerBoundFeeBasis` — `CoreFrameworks/OrderManager.hpp`
- `OMS_OpenPositionCost` — `CoreFrameworks/OrderManager.hpp`
- `OMS_PushSubmit` — `CoreFrameworks/OrderManager.hpp`
- `OrderEventLog_Append` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderEventLog_ApplyEvent` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderEventLog_AsyncWriterRoutine` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderEventLog_Free` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderEventLog_Init` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderEventLog_InitWithFile` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderEventLog_LoadFromDisk` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderEventLog_Reset` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderEventLog_StartAsyncWriter` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderEventLog_StopAsyncWriter` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderEvent_MakeFill` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderManager_AccountMakerTakerFee` — `CoreFrameworks/OrderManager.hpp`
- `OrderManager_FillResultCallback` — `CoreFrameworks/OrderManager.hpp`
- `OrderManager_HandleFill` — `CoreFrameworks/OrderManager.hpp`
- `OrderManager_Init` — `CoreFrameworks/OrderManager.hpp`
- `OrderManager_OpenCalibrationLog` — `CoreFrameworks/OrderManager.hpp`
- `OrderManager_ProcessFillCommand` — `CoreFrameworks/OrderManager.hpp`
- `OrderManager_ProcessReconcile` — `CoreFrameworks/OrderManager.hpp`
- `OrderManager_Shutdown` — `CoreFrameworks/OrderManager.hpp`
- `OrderManager_Submit` — `CoreFrameworks/OrderManager.hpp`
- `OrderManager_Tick` — `CoreFrameworks/OrderManager.hpp`
- `Order_BindPreResolved` — `CoreFrameworks/Order.hpp`
- `Order_Init` — `CoreFrameworks/Order.hpp`
- `Order_WarnIfNotPreResolved` — `CoreFrameworks/Order.hpp`
- `ParameterSlot_Init` — `CoreFrameworks/ParameterSlot.hpp`
- `ParameterSlot_Read` — `CoreFrameworks/ParameterSlot.hpp`
- `ParameterSlot_Write` — `CoreFrameworks/ParameterSlot.hpp`
- `Portfolio_AddPositionWithExits` — `CoreFrameworks/Portfolio.hpp`
- `Portfolio_CloseSlot` — `CoreFrameworks/Portfolio.hpp`
- `Portfolio_ComputePnL` — `CoreFrameworks/Portfolio.hpp`
- `Portfolio_FromEventLog` — `CoreFrameworks/OrderEventLog.hpp`
- `Portfolio_Load` — `CoreFrameworks/Portfolio.hpp`
- `Portfolio_OpenSlot` — `CoreFrameworks/Portfolio.hpp`
- `Portfolio_Save` — `CoreFrameworks/Portfolio.hpp`
- `PositionExitGate` — `CoreFrameworks/Portfolio.hpp`
- `Position_Reset` — `CoreFrameworks/Portfolio.hpp`
- `ReconciliationLoop_Init` — `CoreFrameworks/ReconciliationLoop.hpp`
- `ReconciliationLoop_Pass` — `CoreFrameworks/ReconciliationLoop.hpp`
- `ReconciliationLoop_Shutdown` — `CoreFrameworks/ReconciliationLoop.hpp`
- `SG_Evaluate` — `CoreFrameworks/GateParameters.hpp`
- `SPSCRing_Depth` — `CoreFrameworks/SPSCRing.hpp`
- `SPSCRing_Init` — `CoreFrameworks/SPSCRing.hpp`
- `SPSCRing_TryPop` — `CoreFrameworks/SPSCRing.hpp`
- `SPSCRing_TryPush` — `CoreFrameworks/SPSCRing.hpp`
- `SellGate` — `CoreFrameworks/OrderGates.hpp`
- `ShardedOrderLatency_Sample` — `CoreFrameworks/ShardedOrderLatency.hpp`
- `engine_set_mxcsr_ftz_daz` — `CoreFrameworks/SystemInit.hpp`
- `handle_buy_fill` — `CoreFrameworks/OrderManager.hpp`
- `handle_sell_fill` — `CoreFrameworks/OrderManager.hpp`
- `reconcile_thread_body` — `CoreFrameworks/ReconciliationLoop.hpp`

### REGISTRY (7)

- `FOREACH_GATE_CFG_FLAG` — `CoreFrameworks/GateCfgFlagRegistry.hpp`
- `FOREACH_LIFECYCLE_CFG_FLAG` — `CoreFrameworks/LifecycleCfgFlagRegistry.hpp`
- `FOREACH_OPS_CFG_FLAG` — `CoreFrameworks/OpsCfgFlagRegistry.hpp`
- `FOREACH_REGISTRY` — `CoreFrameworks/MetaRegistry.hpp`
- `FOREACH_RISK_CFG_FLAG` — `CoreFrameworks/RiskCfgFlagRegistry.hpp`
- `FOREACH_SP_SECTION` — `CoreFrameworks/SpSectionRegistry.hpp`
- `FOREACH_STRATEGY` — `Strategies/StrategyInterface.hpp`

### STRUCT (26)

- `CumDeltaState` — `Strategies/RegimeDetector.hpp`
- `DataStream` — `CoreFrameworks/OrderGates.hpp`
- `ExchangeAdapter` — `CoreFrameworks/ExchangeAdapter.hpp`
- `ExecutionCore` — `CoreFrameworks/ExecutionCore.hpp`
- `ExitRecord` — `CoreFrameworks/Portfolio.hpp`
- `GateParameters` — `CoreFrameworks/GateParameters.hpp`
- `NodeLatencySnapshot` — `CoreFrameworks/NodeLatencyStats.hpp`
- `NodeLatencyStats` — `CoreFrameworks/NodeLatencyStats.hpp`
- `Order` — `CoreFrameworks/Order.hpp`
- `OrderEvent` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderEventLog` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderEventLogFileHeader` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderManagerState` — `CoreFrameworks/OrderManager.hpp`
- `OrderPreResolved` — `CoreFrameworks/Order.hpp`
- `OrderResult` — `CoreFrameworks/ExchangeAdapter.hpp`
- `ParameterSlot` — `CoreFrameworks/ParameterSlot.hpp`
- `Portfolio` — `CoreFrameworks/Portfolio.hpp`
- `Position` — `CoreFrameworks/Portfolio.hpp`
- `PositionEntryArgs` — `CoreFrameworks/Portfolio.hpp`
- `ReconciliationLoopState` — `CoreFrameworks/ReconciliationLoop.hpp`
- `RegimeSignals` — `Strategies/RegimeDetector.hpp`
- `SPSCRing` — `CoreFrameworks/SPSCRing.hpp`
- `ShardedOrderLatency` — `CoreFrameworks/ShardedOrderLatency.hpp`
- `SubmitCommand` — `CoreFrameworks/OrderManager.hpp`
- `Tick` — `CoreFrameworks/Tick.hpp`
- `TradeEvent` — `CoreFrameworks/TradeEvent.hpp`
