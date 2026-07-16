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

Converted files: 87 · unit blocks: 415

## [TAG] values → files

### BACKTEST (4 files)

- `CoreFrameworks/ControllerEventLoop.hpp`
- `CoreFrameworks/EngineCommon.hpp`
- `CoreFrameworks/MetricCompute.hpp`
- `CoreFrameworks/ShardedBacktestDriver.hpp`

### BINARY_FP (7 files)

- `ML_Headers/GateControlNetwork.hpp`
- `ML_Headers/LinearRegression3X.hpp`
- `ML_Headers/LinearRegressionSimple.hpp`
- `ML_Headers/ROR_regressor.hpp`
- `ML_Headers/ReciprocalLUT.hpp`
- `ML_Headers/WelfordStats.hpp`
- `Strategies/RegimeDetector.hpp`

### BITMAP_PACKED (14 files)

- `CoreFrameworks/CfgFieldRegistry.hpp`
- `CoreFrameworks/GateCfgFlagRegistry.hpp`
- `CoreFrameworks/LifecycleCfgFlagRegistry.hpp`
- `CoreFrameworks/OpsCfgFlagRegistry.hpp`
- `CoreFrameworks/Order.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/RiskCfgFlagRegistry.hpp`
- `CoreFrameworks/SlowPathGateRegistry.hpp`
- `ML_Headers/BarrierBlendModeRegistry.hpp`
- `ML_Headers/EzooInitFlagRegistry.hpp`
- `ML_Headers/MlCfgFlagRegistry.hpp`
- `ML_Headers/PerArmFlagRegistry.hpp`
- `Strategies/OpModeCategories.hpp`
- `Strategies/StrategyCategories.hpp`

### BOOT_TIME (25 files)

- `CoreFrameworks/BinanceAdapter.hpp`
- `CoreFrameworks/ControllerConfig.hpp`
- `CoreFrameworks/ControllerEventLoop.hpp`
- `CoreFrameworks/EngineCommon.hpp`
- `CoreFrameworks/EngineSharded/Boot.hpp`
- `CoreFrameworks/EngineSharded/Run.hpp`
- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/LiveReadiness.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/Notify.hpp`
- `CoreFrameworks/OrderEventLog.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/PortfolioController.hpp`
- `CoreFrameworks/Reconcile.hpp`
- `CoreFrameworks/ReconciliationLoop.hpp`
- `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/ShardedBacktestDriver.hpp`
- `CoreFrameworks/ShardedLiveSafety.hpp`
- `CoreFrameworks/ShardedSnapshotPersist.hpp`
- `CoreFrameworks/ShardedTradeLog.hpp`
- `CoreFrameworks/SystemInit.hpp`
- `Strategies/StrategyLifecycle.hpp`

### CAPITAL_BEARING (24 files)

- `CoreFrameworks/CfgFieldRegistry.hpp`
- `CoreFrameworks/ControllerConfig.hpp`
- `CoreFrameworks/ControllerEventLoop.hpp`
- `CoreFrameworks/EngineSharded/Async.hpp`
- `CoreFrameworks/EngineSharded/Run.hpp`
- `CoreFrameworks/EngineSharded/SlowPath.hpp`
- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/LiveReadiness.hpp`
- `CoreFrameworks/Order.hpp`
- `CoreFrameworks/OrderEventLog.hpp`
- `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/PortfolioController.hpp`
- `CoreFrameworks/ReconciliationLoop.hpp`
- `CoreFrameworks/ShardedLiveSafety.hpp`
- `CoreFrameworks/TradeEvent.hpp`
- `ML_Headers/BarrierValidation.hpp`
- `Strategies/MLStrategy.hpp`
- `Strategies/MeanReversion.hpp`
- `Strategies/Momentum.hpp`
- `Strategies/StrategyLifecycle.hpp`
- `Strategies/StrategyParameters.hpp`

### CFG_FLOW (18 files)

- `CoreFrameworks/CfgFieldDispatch.hpp`
- `CoreFrameworks/CfgFieldRegistry.hpp`
- `CoreFrameworks/ControllerConfig.hpp`
- `CoreFrameworks/ControllerEventLoop.hpp`
- `CoreFrameworks/EngineCommon.hpp`
- `CoreFrameworks/GateCfgFlagRegistry.hpp`
- `CoreFrameworks/LifecycleCfgFlagRegistry.hpp`
- `CoreFrameworks/OpsCfgFlagRegistry.hpp`
- `CoreFrameworks/Reconcile.hpp`
- `CoreFrameworks/RiskCfgFlagRegistry.hpp`
- `CoreFrameworks/SessionPhaseRegistry.hpp`
- `CoreFrameworks/SlowPathGateRegistry.hpp`
- `CoreFrameworks/StampBoundDerivedFilter.hpp`
- `CoreFrameworks/TradeLogColRegistry.hpp`
- `ML_Headers/BarrierBlendModeRegistry.hpp`
- `ML_Headers/MlCfgFlagRegistry.hpp`
- `Strategies/OpModeCategories.hpp`
- `Strategies/StrategyCategories.hpp`

### CONCURRENCY (13 files)

- `CoreFrameworks/ControllerEventLoop.hpp`
- `CoreFrameworks/EngineSharded/Async.hpp`
- `CoreFrameworks/EngineSharded/Boot.hpp`
- `CoreFrameworks/EngineSharded/Run.hpp`
- `CoreFrameworks/ExchangeAdapter.hpp`
- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/OrderEventLog.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/ReconciliationLoop.hpp`
- `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/ShardedOrderLatency.hpp`
- `CoreFrameworks/TradeEvent.hpp`

### CRITICAL (11 files)

- `CoreFrameworks/EngineSharded/Async.hpp`
- `CoreFrameworks/EnsembleHotSwap.hpp`
- `CoreFrameworks/HotSwap.hpp`
- `CoreFrameworks/LiveReadiness.hpp`
- `CoreFrameworks/ModelValidation.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/ParseFast.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/SystemInit.hpp`

### DATA_ORIENTED_DESIGN (11 files)

- `CoreFrameworks/ControllerConfig.hpp`
- `CoreFrameworks/ControllerEventLoop.hpp`
- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/Order.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/PortfolioController.hpp`
- `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/Tick.hpp`

### DATA_PLANE (3 files)

- `CoreFrameworks/EngineSharded/Async.hpp`
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

### DETERMINISM (14 files)

- `CoreFrameworks/CfgFieldDispatch.hpp`
- `CoreFrameworks/CfgFieldRegistry.hpp`
- `CoreFrameworks/ControllerConfig.hpp`
- `CoreFrameworks/OrderEventLog.hpp`
- `CoreFrameworks/ParseFast.hpp`
- `CoreFrameworks/ShardedBacktestDriver.hpp`
- `CoreFrameworks/ShardedSnapshotPersist.hpp`
- `CoreFrameworks/StampBoundDerivedFilter.hpp`
- `CoreFrameworks/SystemInit.hpp`
- `ML_Headers/BuildFlags.hpp`
- `ML_Headers/CfgDriftCheckRegistry.hpp`
- `ML_Headers/FeatureRegistryOverlay.hpp`
- `ML_Headers/StampHelper.hpp`
- `ML_Headers/ThompsonBandit.hpp`

### ENGINE (87 files)

- `CoreFrameworks/BinanceAdapter.hpp`
- `CoreFrameworks/CfgFieldDispatch.hpp`
- `CoreFrameworks/CfgFieldRegistry.hpp`
- `CoreFrameworks/ControllerConfig.hpp`
- `CoreFrameworks/ControllerEventLoop.hpp`
- `CoreFrameworks/EngineCommon.hpp`
- `CoreFrameworks/EngineSharded.hpp`
- `CoreFrameworks/EngineSharded/Async.hpp`
- `CoreFrameworks/EngineSharded/Boot.hpp`
- `CoreFrameworks/EngineSharded/Run.hpp`
- `CoreFrameworks/EngineSharded/SlowPath.hpp`
- `CoreFrameworks/EnsembleHotSwap.hpp`
- `CoreFrameworks/EventLoopAggregates.hpp`
- `CoreFrameworks/ExchangeAdapter.hpp`
- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateCfgFlagRegistry.hpp`
- `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/HotSwap.hpp`
- `CoreFrameworks/LifecycleCfgFlagRegistry.hpp`
- `CoreFrameworks/LiveReadiness.hpp`
- `CoreFrameworks/MetaRegistry.hpp`
- `CoreFrameworks/MetricCompute.hpp`
- `CoreFrameworks/ModelValidation.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/Notify.hpp`
- `CoreFrameworks/OpsCfgFlagRegistry.hpp`
- `CoreFrameworks/Order.hpp`
- `CoreFrameworks/OrderEventLog.hpp`
- `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/PaperResetArchive.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/ParseFast.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/PortfolioController.hpp`
- `CoreFrameworks/Reconcile.hpp`
- `CoreFrameworks/ReconciliationLoop.hpp`
- `CoreFrameworks/RiskCfgFlagRegistry.hpp`
- `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/SessionPhaseRegistry.hpp`
- `CoreFrameworks/ShardedBacktestDriver.hpp`
- `CoreFrameworks/ShardedLiveSafety.hpp`
- `CoreFrameworks/ShardedOrderLatency.hpp`
- `CoreFrameworks/ShardedSnapshot.hpp`
- `CoreFrameworks/ShardedSnapshotPersist.hpp`
- `CoreFrameworks/ShardedTradeLog.hpp`
- `CoreFrameworks/SlowPathGateRegistry.hpp`
- `CoreFrameworks/SpSectionRegistry.hpp`
- `CoreFrameworks/StampBoundDerivedFilter.hpp`
- `CoreFrameworks/SystemInit.hpp`
- `CoreFrameworks/Tick.hpp`
- `CoreFrameworks/TradeEvent.hpp`
- `CoreFrameworks/TradeLogColRegistry.hpp`
- `ML_Headers/BarrierBlendModeRegistry.hpp`
- `ML_Headers/BarrierGate.hpp`
- `ML_Headers/BarrierValidation.hpp`
- `ML_Headers/BuildFlags.hpp`
- `ML_Headers/CfgDriftCheckRegistry.hpp`
- `ML_Headers/CostModel.hpp`
- `ML_Headers/EzooInitFlagRegistry.hpp`
- `ML_Headers/FeatureRegistryOverlay.hpp`
- `ML_Headers/GateControlNetwork.hpp`
- `ML_Headers/ICVariantRegistry.hpp`
- `ML_Headers/LinearRegression3X.hpp`
- `ML_Headers/LinearRegressionSimple.hpp`
- `ML_Headers/MlCfgFlagRegistry.hpp`
- `ML_Headers/PerArmFlagRegistry.hpp`
- `ML_Headers/ROR_regressor.hpp`
- `ML_Headers/ReciprocalLUT.hpp`
- `ML_Headers/RewardTracker.hpp`
- `ML_Headers/RollingTurnover.hpp`
- `ML_Headers/RollingWindowRegistry.hpp`
- `ML_Headers/StampHelper.hpp`
- `ML_Headers/ThompsonBandit.hpp`
- `ML_Headers/VolScaler.hpp`
- `ML_Headers/WelfordStats.hpp`
- `ML_Headers/bandit_dispatch_table.hpp`
- `Strategies/MLStrategy.hpp`
- `Strategies/MeanReversion.hpp`
- `Strategies/Momentum.hpp`
- `Strategies/OpModeCategories.hpp`
- `Strategies/RegimeDetector.hpp`
- `Strategies/SimpleDip.hpp`
- `Strategies/StrategyCategories.hpp`
- `Strategies/StrategyInterface.hpp`
- `Strategies/StrategyLifecycle.hpp`
- `Strategies/StrategyParameters.hpp`

### ENTRY_POINT (3 files)

- `CoreFrameworks/EngineSharded.hpp`
- `CoreFrameworks/EngineSharded/Run.hpp`
- `CoreFrameworks/ExchangeAdapter.hpp`

### FLOAT_DISPLAY_ONLY (6 files)

- `CoreFrameworks/EventLoopAggregates.hpp`
- `CoreFrameworks/ExchangeAdapter.hpp`
- `CoreFrameworks/MetricCompute.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/ShardedSnapshot.hpp`
- `CoreFrameworks/ShardedTradeLog.hpp`

### FRAMEWORK_DISCIPLINE (14 files)

- `CoreFrameworks/CfgFieldDispatch.hpp`
- `CoreFrameworks/CfgFieldRegistry.hpp`
- `CoreFrameworks/LiveReadiness.hpp`
- `CoreFrameworks/MetaRegistry.hpp`
- `CoreFrameworks/SessionPhaseRegistry.hpp`
- `CoreFrameworks/SlowPathGateRegistry.hpp`
- `CoreFrameworks/TradeLogColRegistry.hpp`
- `ML_Headers/CfgDriftCheckRegistry.hpp`
- `ML_Headers/ICVariantRegistry.hpp`
- `ML_Headers/RollingWindowRegistry.hpp`
- `ML_Headers/bandit_dispatch_table.hpp`
- `Strategies/StrategyInterface.hpp`
- `Strategies/StrategyLifecycle.hpp`
- `Strategies/StrategyParameters.hpp`

### FROZEN (1 files)

- `CoreFrameworks/StampBoundDerivedFilter.hpp`

### GUI (1 files)

- `CoreFrameworks/EngineSharded/SlowPath.hpp`

### HELPER (2 files)

- `CoreFrameworks/LiveReadiness.hpp`
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

### LIVE_TRADING (13 files)

- `CoreFrameworks/BinanceAdapter.hpp`
- `CoreFrameworks/ControllerConfig.hpp`
- `CoreFrameworks/ControllerEventLoop.hpp`
- `CoreFrameworks/EngineSharded/Run.hpp`
- `CoreFrameworks/ExchangeAdapter.hpp`
- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/LiveReadiness.hpp`
- `CoreFrameworks/Notify.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/Reconcile.hpp`
- `CoreFrameworks/ReconciliationLoop.hpp`
- `CoreFrameworks/ShardedLiveSafety.hpp`
- `CoreFrameworks/ShardedOrderLatency.hpp`

### ML (6 files)

- `CoreFrameworks/EnsembleHotSwap.hpp`
- `CoreFrameworks/HotSwap.hpp`
- `CoreFrameworks/LiveReadiness.hpp`
- `CoreFrameworks/ModelValidation.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `Strategies/RegimeDetector.hpp`

### ML_INFERENCE (22 files)

- `CoreFrameworks/CfgFieldDispatch.hpp`
- `CoreFrameworks/ControllerEventLoop.hpp`
- `CoreFrameworks/EngineCommon.hpp`
- `ML_Headers/BarrierBlendModeRegistry.hpp`
- `ML_Headers/BarrierGate.hpp`
- `ML_Headers/BarrierValidation.hpp`
- `ML_Headers/BuildFlags.hpp`
- `ML_Headers/CfgDriftCheckRegistry.hpp`
- `ML_Headers/CostModel.hpp`
- `ML_Headers/EzooInitFlagRegistry.hpp`
- `ML_Headers/FeatureRegistryOverlay.hpp`
- `ML_Headers/GateControlNetwork.hpp`
- `ML_Headers/ICVariantRegistry.hpp`
- `ML_Headers/MlCfgFlagRegistry.hpp`
- `ML_Headers/PerArmFlagRegistry.hpp`
- `ML_Headers/RollingTurnover.hpp`
- `ML_Headers/StampHelper.hpp`
- `ML_Headers/ThompsonBandit.hpp`
- `ML_Headers/VolScaler.hpp`
- `ML_Headers/bandit_dispatch_table.hpp`
- `Strategies/MLStrategy.hpp`
- `Strategies/StrategyParameters.hpp`

### MONITORING_PLANE (16 files)

- `CoreFrameworks/ControllerEventLoop.hpp`
- `CoreFrameworks/EngineSharded/Run.hpp`
- `CoreFrameworks/EventLoopAggregates.hpp`
- `CoreFrameworks/MetricCompute.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/Notify.hpp`
- `CoreFrameworks/PaperResetArchive.hpp`
- `CoreFrameworks/PortfolioController.hpp`
- `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/ShardedOrderLatency.hpp`
- `CoreFrameworks/ShardedSnapshot.hpp`
- `CoreFrameworks/SpSectionRegistry.hpp`
- `CoreFrameworks/TradeLogColRegistry.hpp`
- `ML_Headers/RewardTracker.hpp`
- `ML_Headers/RollingTurnover.hpp`
- `Strategies/StrategyInterface.hpp`

### OMS_DRAINER (8 files)

- `CoreFrameworks/BinanceAdapter.hpp`
- `CoreFrameworks/ControllerEventLoop.hpp`
- `CoreFrameworks/EngineSharded/Async.hpp`
- `CoreFrameworks/EngineSharded/SlowPath.hpp`
- `CoreFrameworks/Order.hpp`
- `CoreFrameworks/OrderEventLog.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/ShardedTradeLog.hpp`

### PARSER (2 files)

- `CoreFrameworks/ControllerConfig.hpp`
- `CoreFrameworks/ParseFast.hpp`

### PERSISTENCE (11 files)

- `CoreFrameworks/CfgFieldDispatch.hpp`
- `CoreFrameworks/ControllerEventLoop.hpp`
- `CoreFrameworks/Order.hpp`
- `CoreFrameworks/OrderEventLog.hpp`
- `CoreFrameworks/PaperResetArchive.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/PortfolioController.hpp`
- `CoreFrameworks/ShardedSnapshotPersist.hpp`
- `CoreFrameworks/ShardedTradeLog.hpp`
- `ML_Headers/RewardTracker.hpp`
- `ML_Headers/StampHelper.hpp`

### PRODUCER (1 files)

- `CoreFrameworks/EngineSharded/Async.hpp`

### SLOW_PATH (36 files)

- `CoreFrameworks/BinanceAdapter.hpp`
- `CoreFrameworks/ControllerConfig.hpp`
- `CoreFrameworks/ControllerEventLoop.hpp`
- `CoreFrameworks/EngineCommon.hpp`
- `CoreFrameworks/EnsembleHotSwap.hpp`
- `CoreFrameworks/EventLoopAggregates.hpp`
- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/HotSwap.hpp`
- `CoreFrameworks/ModelValidation.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/ShardedSnapshot.hpp`
- `CoreFrameworks/ShardedSnapshotPersist.hpp`
- `CoreFrameworks/ShardedTradeLog.hpp`
- `CoreFrameworks/SlowPathGateRegistry.hpp`
- `CoreFrameworks/SpSectionRegistry.hpp`
- `ML_Headers/BarrierGate.hpp`
- `ML_Headers/CostModel.hpp`
- `ML_Headers/LinearRegression3X.hpp`
- `ML_Headers/LinearRegressionSimple.hpp`
- `ML_Headers/ROR_regressor.hpp`
- `ML_Headers/ReciprocalLUT.hpp`
- `ML_Headers/RollingWindowRegistry.hpp`
- `ML_Headers/ThompsonBandit.hpp`
- `ML_Headers/VolScaler.hpp`
- `ML_Headers/WelfordStats.hpp`
- `Strategies/MLStrategy.hpp`
- `Strategies/MeanReversion.hpp`
- `Strategies/Momentum.hpp`
- `Strategies/RegimeDetector.hpp`
- `Strategies/SimpleDip.hpp`
- `Strategies/StrategyInterface.hpp`
- `Strategies/StrategyLifecycle.hpp`
- `Strategies/StrategyParameters.hpp`

### STRUCTURAL_FIX (1 files)

- `CoreFrameworks/Portfolio.hpp`

### SUPPORTIVE (6 files)

- `CoreFrameworks/Order.hpp`
- `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/ReconciliationLoop.hpp`
- `CoreFrameworks/ShardedLiveSafety.hpp`

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

### ENUM (8)

- `CommandType` — `CoreFrameworks/OrderManager.hpp`
- `LiveReadinessSeverity` — `CoreFrameworks/LiveReadiness.hpp`
- `NotifyKind` — `CoreFrameworks/Notify.hpp`
- `OpModeCategory` — `Strategies/OpModeCategories.hpp`
- `OrderEventType` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderState` — `CoreFrameworks/Order.hpp`
- `OrderType` — `CoreFrameworks/Order.hpp`
- `StrategyCategory` — `Strategies/StrategyCategories.hpp`

### FILE (87)

- `CoreFrameworks/BinanceAdapter.hpp` — `CoreFrameworks/BinanceAdapter.hpp`
- `CoreFrameworks/CfgFieldDispatch.hpp` — `CoreFrameworks/CfgFieldDispatch.hpp`
- `CoreFrameworks/CfgFieldRegistry.hpp` — `CoreFrameworks/CfgFieldRegistry.hpp`
- `CoreFrameworks/ControllerConfig.hpp` — `CoreFrameworks/ControllerConfig.hpp`
- `CoreFrameworks/ControllerEventLoop.hpp` — `CoreFrameworks/ControllerEventLoop.hpp`
- `CoreFrameworks/EngineCommon.hpp` — `CoreFrameworks/EngineCommon.hpp`
- `CoreFrameworks/EngineSharded.hpp` — `CoreFrameworks/EngineSharded.hpp`
- `CoreFrameworks/EngineSharded/Async.hpp` — `CoreFrameworks/EngineSharded/Async.hpp`
- `CoreFrameworks/EngineSharded/Boot.hpp` — `CoreFrameworks/EngineSharded/Boot.hpp`
- `CoreFrameworks/EngineSharded/Run.hpp` — `CoreFrameworks/EngineSharded/Run.hpp`
- `CoreFrameworks/EngineSharded/SlowPath.hpp` — `CoreFrameworks/EngineSharded/SlowPath.hpp`
- `CoreFrameworks/EnsembleHotSwap.hpp` — `CoreFrameworks/EnsembleHotSwap.hpp`
- `CoreFrameworks/EventLoopAggregates.hpp` — `CoreFrameworks/EventLoopAggregates.hpp`
- `CoreFrameworks/ExchangeAdapter.hpp` — `CoreFrameworks/ExchangeAdapter.hpp`
- `CoreFrameworks/ExecutionCore.hpp` — `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateCfgFlagRegistry.hpp` — `CoreFrameworks/GateCfgFlagRegistry.hpp`
- `CoreFrameworks/GateParameters.hpp` — `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/HotSwap.hpp` — `CoreFrameworks/HotSwap.hpp`
- `CoreFrameworks/LifecycleCfgFlagRegistry.hpp` — `CoreFrameworks/LifecycleCfgFlagRegistry.hpp`
- `CoreFrameworks/LiveReadiness.hpp` — `CoreFrameworks/LiveReadiness.hpp`
- `CoreFrameworks/MetaRegistry.hpp` — `CoreFrameworks/MetaRegistry.hpp`
- `CoreFrameworks/MetricCompute.hpp` — `CoreFrameworks/MetricCompute.hpp`
- `CoreFrameworks/ModelValidation.hpp` — `CoreFrameworks/ModelValidation.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp` — `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/Notify.hpp` — `CoreFrameworks/Notify.hpp`
- `CoreFrameworks/OpsCfgFlagRegistry.hpp` — `CoreFrameworks/OpsCfgFlagRegistry.hpp`
- `CoreFrameworks/Order.hpp` — `CoreFrameworks/Order.hpp`
- `CoreFrameworks/OrderEventLog.hpp` — `CoreFrameworks/OrderEventLog.hpp`
- `CoreFrameworks/OrderGates.hpp` — `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/OrderManager.hpp` — `CoreFrameworks/OrderManager.hpp`
- `CoreFrameworks/PaperResetArchive.hpp` — `CoreFrameworks/PaperResetArchive.hpp`
- `CoreFrameworks/ParameterSlot.hpp` — `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/ParseFast.hpp` — `CoreFrameworks/ParseFast.hpp`
- `CoreFrameworks/Portfolio.hpp` — `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/PortfolioController.hpp` — `CoreFrameworks/PortfolioController.hpp`
- `CoreFrameworks/Reconcile.hpp` — `CoreFrameworks/Reconcile.hpp`
- `CoreFrameworks/ReconciliationLoop.hpp` — `CoreFrameworks/ReconciliationLoop.hpp`
- `CoreFrameworks/RiskCfgFlagRegistry.hpp` — `CoreFrameworks/RiskCfgFlagRegistry.hpp`
- `CoreFrameworks/SPSCRing.hpp` — `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/SessionPhaseRegistry.hpp` — `CoreFrameworks/SessionPhaseRegistry.hpp`
- `CoreFrameworks/ShardedBacktestDriver.hpp` — `CoreFrameworks/ShardedBacktestDriver.hpp`
- `CoreFrameworks/ShardedLiveSafety.hpp` — `CoreFrameworks/ShardedLiveSafety.hpp`
- `CoreFrameworks/ShardedOrderLatency.hpp` — `CoreFrameworks/ShardedOrderLatency.hpp`
- `CoreFrameworks/ShardedSnapshot.hpp` — `CoreFrameworks/ShardedSnapshot.hpp`
- `CoreFrameworks/ShardedSnapshotPersist.hpp` — `CoreFrameworks/ShardedSnapshotPersist.hpp`
- `CoreFrameworks/ShardedTradeLog.hpp` — `CoreFrameworks/ShardedTradeLog.hpp`
- `CoreFrameworks/SlowPathGateRegistry.hpp` — `CoreFrameworks/SlowPathGateRegistry.hpp`
- `CoreFrameworks/SpSectionRegistry.hpp` — `CoreFrameworks/SpSectionRegistry.hpp`
- `CoreFrameworks/StampBoundDerivedFilter.hpp` — `CoreFrameworks/StampBoundDerivedFilter.hpp`
- `CoreFrameworks/SystemInit.hpp` — `CoreFrameworks/SystemInit.hpp`
- `CoreFrameworks/Tick.hpp` — `CoreFrameworks/Tick.hpp`
- `CoreFrameworks/TradeEvent.hpp` — `CoreFrameworks/TradeEvent.hpp`
- `CoreFrameworks/TradeLogColRegistry.hpp` — `CoreFrameworks/TradeLogColRegistry.hpp`
- `ML_Headers/BarrierBlendModeRegistry.hpp` — `ML_Headers/BarrierBlendModeRegistry.hpp`
- `ML_Headers/BarrierGate.hpp` — `ML_Headers/BarrierGate.hpp`
- `ML_Headers/BarrierValidation.hpp` — `ML_Headers/BarrierValidation.hpp`
- `ML_Headers/BuildFlags.hpp` — `ML_Headers/BuildFlags.hpp`
- `ML_Headers/CfgDriftCheckRegistry.hpp` — `ML_Headers/CfgDriftCheckRegistry.hpp`
- `ML_Headers/CostModel.hpp` — `ML_Headers/CostModel.hpp`
- `ML_Headers/EzooInitFlagRegistry.hpp` — `ML_Headers/EzooInitFlagRegistry.hpp`
- `ML_Headers/FeatureRegistryOverlay.hpp` — `ML_Headers/FeatureRegistryOverlay.hpp`
- `ML_Headers/GateControlNetwork.hpp` — `ML_Headers/GateControlNetwork.hpp`
- `ML_Headers/ICVariantRegistry.hpp` — `ML_Headers/ICVariantRegistry.hpp`
- `ML_Headers/LinearRegression3X.hpp` — `ML_Headers/LinearRegression3X.hpp`
- `ML_Headers/LinearRegressionSimple.hpp` — `ML_Headers/LinearRegressionSimple.hpp`
- `ML_Headers/MlCfgFlagRegistry.hpp` — `ML_Headers/MlCfgFlagRegistry.hpp`
- `ML_Headers/PerArmFlagRegistry.hpp` — `ML_Headers/PerArmFlagRegistry.hpp`
- `ML_Headers/ROR_regressor.hpp` — `ML_Headers/ROR_regressor.hpp`
- `ML_Headers/ReciprocalLUT.hpp` — `ML_Headers/ReciprocalLUT.hpp`
- `ML_Headers/RewardTracker.hpp` — `ML_Headers/RewardTracker.hpp`
- `ML_Headers/RollingTurnover.hpp` — `ML_Headers/RollingTurnover.hpp`
- `ML_Headers/RollingWindowRegistry.hpp` — `ML_Headers/RollingWindowRegistry.hpp`
- `ML_Headers/StampHelper.hpp` — `ML_Headers/StampHelper.hpp`
- `ML_Headers/ThompsonBandit.hpp` — `ML_Headers/ThompsonBandit.hpp`
- `ML_Headers/VolScaler.hpp` — `ML_Headers/VolScaler.hpp`
- `ML_Headers/WelfordStats.hpp` — `ML_Headers/WelfordStats.hpp`
- `ML_Headers/bandit_dispatch_table.hpp` — `ML_Headers/bandit_dispatch_table.hpp`
- `RegimeDetector.hpp` — `Strategies/RegimeDetector.hpp`
- `Strategies/MLStrategy.hpp` — `Strategies/MLStrategy.hpp`
- `Strategies/MeanReversion.hpp` — `Strategies/MeanReversion.hpp`
- `Strategies/Momentum.hpp` — `Strategies/Momentum.hpp`
- `Strategies/OpModeCategories.hpp` — `Strategies/OpModeCategories.hpp`
- `Strategies/SimpleDip.hpp` — `Strategies/SimpleDip.hpp`
- `Strategies/StrategyCategories.hpp` — `Strategies/StrategyCategories.hpp`
- `Strategies/StrategyInterface.hpp` — `Strategies/StrategyInterface.hpp`
- `Strategies/StrategyLifecycle.hpp` — `Strategies/StrategyLifecycle.hpp`
- `Strategies/StrategyParameters.hpp` — `Strategies/StrategyParameters.hpp`

### FUNCTION (216)

- `BG_Evaluate` — `CoreFrameworks/GateParameters.hpp`
- `BUILD_FLAGS_HASH` — `ML_Headers/BuildFlags.hpp`
- `BarrierGate_Compute` — `ML_Headers/BarrierGate.hpp`
- `BinanceAdapter_Get` — `CoreFrameworks/BinanceAdapter.hpp`
- `BinanceAdapter_GetBalancesImpl` — `CoreFrameworks/BinanceAdapter.hpp`
- `BinanceAdapter_Init` — `CoreFrameworks/BinanceAdapter.hpp`
- `BinanceAdapter_QueryOrderImpl` — `CoreFrameworks/BinanceAdapter.hpp`
- `BinanceAdapter_ShutdownImpl` — `CoreFrameworks/BinanceAdapter.hpp`
- `BinanceAdapter_ShutdownState` — `CoreFrameworks/BinanceAdapter.hpp`
- `BinanceAdapter_SubmitMarketBuy` — `CoreFrameworks/BinanceAdapter.hpp`
- `BinanceAdapter_SubmitMarketSell` — `CoreFrameworks/BinanceAdapter.hpp`
- `BinanceAdapter_WorkerLoop` — `CoreFrameworks/BinanceAdapter.hpp`
- `BuyGate` — `CoreFrameworks/OrderGates.hpp`
- `ControllerConfig_CapitalRangeSweep` — `CoreFrameworks/ControllerConfig.hpp`
- `ControllerConfig_Default` — `CoreFrameworks/ControllerConfig.hpp`
- `ControllerConfig_Load` — `CoreFrameworks/ControllerConfig.hpp`
- `ControllerConfig_NormalizeForMode` — `CoreFrameworks/ControllerConfig.hpp`
- `ControllerConfig_PopulateCoresFromFlat` — `CoreFrameworks/ControllerConfig.hpp`
- `ControllerConfig_ResolveForCore` — `CoreFrameworks/ControllerConfig.hpp`
- `CostModel_Estimate` — `ML_Headers/CostModel.hpp`
- `CumDelta_Init` — `Strategies/RegimeDetector.hpp`
- `EmaCross_BuildParameters` — `Strategies/StrategyParameters.hpp`
- `EngineCommon_ApplyBnbDiscount` — `CoreFrameworks/EngineCommon.hpp`
- `EngineCommon_BootGlobal` — `CoreFrameworks/EngineCommon.hpp`
- `EngineCommon_BootPerCore` — `CoreFrameworks/EngineCommon.hpp`
- `EngineCommon_SlowPathCycleAllCores` — `CoreFrameworks/EngineCommon.hpp`
- `EngineCommon_SlowPathCycleOneCore` — `CoreFrameworks/EngineCommon.hpp`
- `EngineSharded_Async_DrainWithSubmit` — `CoreFrameworks/EngineSharded/Async.hpp`
- `EngineSharded_Async_FanOut` — `CoreFrameworks/EngineSharded/Async.hpp`
- `EngineSharded_CalibrateTscGhz` — `CoreFrameworks/EngineSharded/Run.hpp`
- `EngineSharded_DumpLatency` — `CoreFrameworks/EngineSharded/Run.hpp`
- `EngineSharded_ForceCloseOnShutdown` — `CoreFrameworks/ShardedLiveSafety.hpp`
- `EngineSharded_HotSwapEnsemble` — `CoreFrameworks/EnsembleHotSwap.hpp`
- `EngineSharded_OrphanRecovery` — `CoreFrameworks/ShardedLiveSafety.hpp`
- `EngineSharded_PinThread` — `CoreFrameworks/EngineSharded/Run.hpp`
- `EngineSharded_Run` — `CoreFrameworks/EngineSharded/Run.hpp`
- `EngineSharded_SignalHandler` — `CoreFrameworks/EngineSharded/Boot.hpp`
- `EngineSharded_SlowPath_DrainManualCloses` — `CoreFrameworks/EngineSharded/SlowPath.hpp`
- `EngineSharded_SlowPath_DrainPostFill` — `CoreFrameworks/EngineSharded/SlowPath.hpp`
- `EngineSharded_SmartSlowPathPins` — `CoreFrameworks/EngineSharded/Run.hpp`
- `EventLoopState_Init` — `CoreFrameworks/ControllerEventLoop.hpp`
- `EventLoopState_ReconstructPerCoreFromEventLog` — `CoreFrameworks/ControllerEventLoop.hpp`
- `EventLoopState_RegisterCore` — `CoreFrameworks/ControllerEventLoop.hpp`
- `EventLoopState_SetCoreStrategy` — `CoreFrameworks/ControllerEventLoop.hpp`
- `EventLoop_BreakevenOnProfitOneCore` — `CoreFrameworks/ControllerEventLoop.hpp`
- `EventLoop_DrainEvents` — `CoreFrameworks/ControllerEventLoop.hpp`
- `EventLoop_DrainPostFillOneCore` — `CoreFrameworks/ControllerEventLoop.hpp`
- `EventLoop_FlattenAll` — `CoreFrameworks/ControllerEventLoop.hpp`
- `EventLoop_GetAggregates` — `CoreFrameworks/EventLoopAggregates.hpp`
- `EventLoop_KillSwitchEvaluate` — `CoreFrameworks/ControllerEventLoop.hpp`
- `EventLoop_OnEvent` — `CoreFrameworks/ControllerEventLoop.hpp`
- `EventLoop_PushParameters` — `CoreFrameworks/ControllerEventLoop.hpp`
- `EventLoop_QueueParameters` — `CoreFrameworks/ControllerEventLoop.hpp`
- `EventLoop_RebuildAllParameters` — `CoreFrameworks/ControllerEventLoop.hpp`
- `EventLoop_RebuildOneCore` — `CoreFrameworks/ControllerEventLoop.hpp`
- `EventLoop_TimeExitOneCore` — `CoreFrameworks/ControllerEventLoop.hpp`
- `EventLoop_TrailingSLRatchetOneCore` — `CoreFrameworks/ControllerEventLoop.hpp`
- `EventLoop_Unpause` — `CoreFrameworks/ControllerEventLoop.hpp`
- `EventLoop_UpdateRollingStateOneCore` — `CoreFrameworks/ControllerEventLoop.hpp`
- `ExecutionCore_Init` — `CoreFrameworks/ExecutionCore.hpp`
- `ExecutionCore_SetParameters` — `CoreFrameworks/ExecutionCore.hpp`
- `ExecutionCore_SetPermission` — `CoreFrameworks/ExecutionCore.hpp`
- `ExecutionCore_Tick` — `CoreFrameworks/ExecutionCore.hpp`
- `ExecutionCore_Tick_Impl` — `CoreFrameworks/ExecutionCore.hpp`
- `ExitBuffer_PendingProceeds` — `CoreFrameworks/Portfolio.hpp`
- `FeatureOverlay_PostLoadVerify` — `ML_Headers/FeatureRegistryOverlay.hpp`
- `Fee_Compute` — `CoreFrameworks/ControllerConfig.hpp`
- `GCN_forward` — `ML_Headers/GateControlNetwork.hpp`
- `GateParameters_Init` — `CoreFrameworks/GateParameters.hpp`
- `GetReciprocalLUT` — `ML_Headers/ReciprocalLUT.hpp`
- `HotSwap_ShadowLoad_Ensemble` — `CoreFrameworks/HotSwap.hpp`
- `HotSwap_ShadowLoad_SingleZoo` — `CoreFrameworks/HotSwap.hpp`
- `KillSwitch_Activate` — `CoreFrameworks/PortfolioController.hpp`
- `LinearRegression3X_Fit` — `ML_Headers/LinearRegression3X.hpp`
- `LinearRegression_Fit` — `ML_Headers/LinearRegressionSimple.hpp`
- `LiveReadiness_Verify` — `CoreFrameworks/LiveReadiness.hpp`
- `MLStrategy_BuySignal` — `Strategies/MLStrategy.hpp`
- `MLStrategy_ExitAdjust` — `Strategies/MLStrategy.hpp`
- `ML_BuildParameters` — `Strategies/StrategyParameters.hpp`
- `MeanReversion_Adapt` — `Strategies/MeanReversion.hpp`
- `MeanReversion_BuildParameters` — `Strategies/StrategyParameters.hpp`
- `MeanReversion_BuySignal` — `Strategies/MeanReversion.hpp`
- `MeanReversion_ExitAdjust` — `Strategies/MeanReversion.hpp`
- `Momentum_Adapt` — `Strategies/Momentum.hpp`
- `Momentum_BuildParameters` — `Strategies/StrategyParameters.hpp`
- `Momentum_BuySignal` — `Strategies/Momentum.hpp`
- `Momentum_ExitAdjust` — `Strategies/Momentum.hpp`
- `Money_FillGross` — `CoreFrameworks/Portfolio.hpp`
- `NodeLatencyStats_Init` — `CoreFrameworks/NodeLatencyStats.hpp`
- `NodeLatencyStats_Reset` — `CoreFrameworks/NodeLatencyStats.hpp`
- `NodeLatencyStats_Sample` — `CoreFrameworks/NodeLatencyStats.hpp`
- `NodeLatencyStats_Snapshot` — `CoreFrameworks/NodeLatencyStats.hpp`
- `NodeModelZoo_ValidateAgainstCfg` — `CoreFrameworks/ModelValidation.hpp`
- `NotifyBackend_Command` — `CoreFrameworks/Notify.hpp`
- `NotifyBackend_Stderr` — `CoreFrameworks/Notify.hpp`
- `NotifyState_Init` — `CoreFrameworks/Notify.hpp`
- `NotifyState_Shutdown` — `CoreFrameworks/Notify.hpp`
- `Notify_BuildCommand` — `CoreFrameworks/Notify.hpp`
- `Notify_NowMonotonicUs` — `CoreFrameworks/Notify.hpp`
- `Notify_Send` — `CoreFrameworks/Notify.hpp`
- `Notify_ShellEscape` — `CoreFrameworks/Notify.hpp`
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
- `PortfolioController_DrainExits` — `CoreFrameworks/PortfolioController.hpp`
- `PortfolioController_Init` — `CoreFrameworks/PortfolioController.hpp`
- `PortfolioController_SaveSnapshot` — `CoreFrameworks/PortfolioController.hpp`
- `PortfolioController_StrategyBuySignal` — `CoreFrameworks/PortfolioController.hpp`
- `PortfolioController_Tick` — `CoreFrameworks/PortfolioController.hpp`
- `PortfolioController_Unpause` — `CoreFrameworks/PortfolioController.hpp`
- `Portfolio_AddPositionWithExits` — `CoreFrameworks/Portfolio.hpp`
- `Portfolio_CloseSlot` — `CoreFrameworks/Portfolio.hpp`
- `Portfolio_ComputePnL` — `CoreFrameworks/Portfolio.hpp`
- `Portfolio_FromEventLog` — `CoreFrameworks/OrderEventLog.hpp`
- `Portfolio_Load` — `CoreFrameworks/Portfolio.hpp`
- `Portfolio_OpenSlot` — `CoreFrameworks/Portfolio.hpp`
- `Portfolio_Save` — `CoreFrameworks/Portfolio.hpp`
- `PositionExitGate` — `CoreFrameworks/Portfolio.hpp`
- `Position_Reset` — `CoreFrameworks/Portfolio.hpp`
- `RORRegressor_Compute` — `ML_Headers/ROR_regressor.hpp`
- `Reconcile_ApplyMissedFills` — `CoreFrameworks/Reconcile.hpp`
- `Reconcile_AutoCancelStale` — `CoreFrameworks/Reconcile.hpp`
- `Reconcile_Decide` — `CoreFrameworks/Reconcile.hpp`
- `Reconcile_LogReport` — `CoreFrameworks/Reconcile.hpp`
- `Reconcile_ParseMyTrades` — `CoreFrameworks/Reconcile.hpp`
- `Reconcile_ParseOpenOrders` — `CoreFrameworks/Reconcile.hpp`
- `Reconcile_SeedWatermark` — `CoreFrameworks/Reconcile.hpp`
- `ReconciliationLoop_Init` — `CoreFrameworks/ReconciliationLoop.hpp`
- `ReconciliationLoop_Pass` — `CoreFrameworks/ReconciliationLoop.hpp`
- `ReconciliationLoop_Shutdown` — `CoreFrameworks/ReconciliationLoop.hpp`
- `RewardTracker_Push` — `ML_Headers/RewardTracker.hpp`
- `RollingTurnover_Push` — `ML_Headers/RollingTurnover.hpp`
- `SG_Evaluate` — `CoreFrameworks/GateParameters.hpp`
- `SPSCRing_Depth` — `CoreFrameworks/SPSCRing.hpp`
- `SPSCRing_Init` — `CoreFrameworks/SPSCRing.hpp`
- `SPSCRing_TryPop` — `CoreFrameworks/SPSCRing.hpp`
- `SPSCRing_TryPush` — `CoreFrameworks/SPSCRing.hpp`
- `STAMP_BOUND_CFG_emit_canonical_body` — `CoreFrameworks/StampBoundDerivedFilter.hpp`
- `SellGate` — `CoreFrameworks/OrderGates.hpp`
- `ShardedBacktestDriver_Init` — `CoreFrameworks/ShardedBacktestDriver.hpp`
- `ShardedBacktest_Run` — `CoreFrameworks/ShardedBacktestDriver.hpp`
- `ShardedBacktest_RunTick` — `CoreFrameworks/ShardedBacktestDriver.hpp`
- `ShardedOrderLatency_Sample` — `CoreFrameworks/ShardedOrderLatency.hpp`
- `ShardedSnapshot_Load` — `CoreFrameworks/ShardedSnapshotPersist.hpp`
- `ShardedSnapshot_Save` — `CoreFrameworks/ShardedSnapshotPersist.hpp`
- `ShardedTradeLog_Close` — `CoreFrameworks/ShardedTradeLog.hpp`
- `ShardedTradeLog_Flush` — `CoreFrameworks/ShardedTradeLog.hpp`
- `ShardedTradeLog_FormatPerCoreFilename` — `CoreFrameworks/ShardedTradeLog.hpp`
- `ShardedTradeLog_Init` — `CoreFrameworks/ShardedTradeLog.hpp`
- `ShardedTradeLog_RecordEntry` — `CoreFrameworks/ShardedTradeLog.hpp`
- `ShardedTradeLog_RecordExit` — `CoreFrameworks/ShardedTradeLog.hpp`
- `ShardedTradeLog_Rotate` — `CoreFrameworks/ShardedTradeLog.hpp`
- `ShardedTradeLog_WriteRow` — `CoreFrameworks/ShardedTradeLog.hpp`
- `Sharded_SlotNode` — `CoreFrameworks/ControllerEventLoop.hpp`
- `SimpleDip_BuildParameters` — `Strategies/StrategyParameters.hpp`
- `SimpleDip_BuySignal` — `Strategies/SimpleDip.hpp`
- `Stamp_AssembleAndEmit` — `ML_Headers/StampHelper.hpp`
- `Strategy_AdaptPerCore` — `Strategies/StrategyLifecycle.hpp`
- `Strategy_BuildParameters` — `Strategies/StrategyParameters.hpp`
- `Strategy_ExitAdjustPerCore` — `Strategies/StrategyLifecycle.hpp`
- `Strategy_FreePerCore` — `Strategies/StrategyLifecycle.hpp`
- `Strategy_InitPerCore` — `Strategies/StrategyLifecycle.hpp`
- `Strategy_SpacingOk` — `Strategies/StrategyParameters.hpp`
- `Strategy_WriteRatchetSL` — `Strategies/StrategyLifecycle.hpp`
- `Summary_WriteJson` — `CoreFrameworks/PaperResetArchive.hpp`
- `TUI_CopySnapshotSharded` — `CoreFrameworks/ShardedSnapshot.hpp`
- `Thompson_Sample` — `ML_Headers/ThompsonBandit.hpp`
- `VolScaler_Size` — `ML_Headers/VolScaler.hpp`
- `Welford_Push` — `ML_Headers/WelfordStats.hpp`
- `aggregate_zoo_drift` — `CoreFrameworks/LiveReadiness.hpp`
- `barrier_is_corrupt` — `ML_Headers/BarrierValidation.hpp`
- `cfg_assign_field` — `CoreFrameworks/CfgFieldDispatch.hpp`
- `cfg_diff_field` — `CoreFrameworks/CfgFieldDispatch.hpp`
- `cfg_drift_compare` — `CoreFrameworks/CfgFieldDispatch.hpp`
- `cfg_drift_format_reason` — `CoreFrameworks/CfgFieldDispatch.hpp`
- `cfg_emit_field` — `CoreFrameworks/CfgFieldDispatch.hpp`
- `cfg_parse_field` — `CoreFrameworks/CfgFieldDispatch.hpp`
- `cfg_populate_inf_field` — `CoreFrameworks/CfgFieldDispatch.hpp`
- `cfg_save_field` — `CoreFrameworks/CfgFieldDispatch.hpp`
- `check_live_capital_gated_until_e` — `CoreFrameworks/LiveReadiness.hpp`
- `engine_set_mxcsr_ftz_daz` — `CoreFrameworks/SystemInit.hpp`
- `g_buy_reward_dispatch` — `ML_Headers/bandit_dispatch_table.hpp`
- `handle_buy_fill` — `CoreFrameworks/OrderManager.hpp`
- `handle_sell_fill` — `CoreFrameworks/OrderManager.hpp`
- `notify_worker_fn` — `CoreFrameworks/Notify.hpp`
- `parse_double_fast` — `CoreFrameworks/ParseFast.hpp`
- `reconcile_thread_body` — `CoreFrameworks/ReconciliationLoop.hpp`

### MACRO (1)

- `SHARDED_SNAPSHOT_VERSION` — `CoreFrameworks/ShardedSnapshotPersist.hpp`

### REGISTRY (30)

- `FOREACH_BACKTEST_METRIC` — `CoreFrameworks/MetricCompute.hpp`
- `FOREACH_BARRIER_BLEND_MODE` — `ML_Headers/BarrierBlendModeRegistry.hpp`
- `FOREACH_CFG_DRIFT_CHECK` — `ML_Headers/CfgDriftCheckRegistry.hpp`
- `FOREACH_EZOO_INIT_FLAG` — `ML_Headers/EzooInitFlagRegistry.hpp`
- `FOREACH_GATE_CFG_FLAG` — `CoreFrameworks/GateCfgFlagRegistry.hpp`
- `FOREACH_GLOBAL_CFG_FIELD` — `CoreFrameworks/CfgFieldRegistry.hpp`
- `FOREACH_HALT_REASON` — `Strategies/StrategyInterface.hpp`
- `FOREACH_IC_VARIANT` — `ML_Headers/ICVariantRegistry.hpp`
- `FOREACH_LIFECYCLE_CFG_FLAG` — `CoreFrameworks/LifecycleCfgFlagRegistry.hpp`
- `FOREACH_LIVE_READINESS_CHECK` — `CoreFrameworks/LiveReadiness.hpp`
- `FOREACH_MANUAL_PER_NODE_FIELD` — `CoreFrameworks/CfgFieldRegistry.hpp`
- `FOREACH_ML_CFG_FLAG` — `ML_Headers/MlCfgFlagRegistry.hpp`
- `FOREACH_OPS_CFG_FLAG` — `CoreFrameworks/OpsCfgFlagRegistry.hpp`
- `FOREACH_PER_ARM_FLAG` — `ML_Headers/PerArmFlagRegistry.hpp`
- `FOREACH_PER_NODE_ARRAY_OVERRIDE` — `CoreFrameworks/CfgFieldRegistry.hpp`
- `FOREACH_PER_NODE_CFG_FIELD` — `CoreFrameworks/CfgFieldRegistry.hpp`
- `FOREACH_PER_NODE_DOMAIN_BITMAP` — `CoreFrameworks/CfgFieldRegistry.hpp`
- `FOREACH_PER_NODE_NO_FLAT_FIELD_SYNC` — `CoreFrameworks/CfgFieldRegistry.hpp`
- `FOREACH_RECONCILE_MODE` — `CoreFrameworks/Reconcile.hpp`
- `FOREACH_REGIME` — `Strategies/StrategyInterface.hpp`
- `FOREACH_REGISTRY` — `CoreFrameworks/MetaRegistry.hpp`
- `FOREACH_RISK_CFG_FLAG` — `CoreFrameworks/RiskCfgFlagRegistry.hpp`
- `FOREACH_ROLLING_WINDOW` — `ML_Headers/RollingWindowRegistry.hpp`
- `FOREACH_SESSION_PHASE` — `CoreFrameworks/SessionPhaseRegistry.hpp`
- `FOREACH_SHALT` — `Strategies/StrategyInterface.hpp`
- `FOREACH_SLOW_PATH_GATE` — `CoreFrameworks/SlowPathGateRegistry.hpp`
- `FOREACH_SP_SECTION` — `CoreFrameworks/SpSectionRegistry.hpp`
- `FOREACH_STRATEGY` — `Strategies/StrategyInterface.hpp`
- `FOREACH_TRADE_LOG_COL` — `CoreFrameworks/TradeLogColRegistry.hpp`
- `PER_NODE_OVERRIDE_FIELDS` — `CoreFrameworks/ControllerConfig.hpp`

### STRUCT (55)

- `BinanceAdapterState` — `CoreFrameworks/BinanceAdapter.hpp`
- `CfgFieldDescriptor` — `CoreFrameworks/CfgFieldRegistry.hpp`
- `ControllerConfig` — `CoreFrameworks/ControllerConfig.hpp`
- `CumDeltaState` — `Strategies/RegimeDetector.hpp`
- `DataStream` — `CoreFrameworks/OrderGates.hpp`
- `EventLoopAggregates` — `CoreFrameworks/EventLoopAggregates.hpp`
- `EventLoopState` — `CoreFrameworks/ControllerEventLoop.hpp`
- `ExchangeAdapter` — `CoreFrameworks/ExchangeAdapter.hpp`
- `ExecutionCore` — `CoreFrameworks/ExecutionCore.hpp`
- `ExitRecord` — `CoreFrameworks/Portfolio.hpp`
- `GateParameters` — `CoreFrameworks/GateParameters.hpp`
- `MLBuildContext` — `Strategies/StrategyParameters.hpp`
- `MLStrategyState` — `Strategies/MLStrategy.hpp`
- `MeanReversionState` — `Strategies/MeanReversion.hpp`
- `MomentumState` — `Strategies/Momentum.hpp`
- `NodeContext` — `CoreFrameworks/ControllerEventLoop.hpp`
- `NodeContextDisplayMeta` — `CoreFrameworks/ControllerEventLoop.hpp`
- `NodeLatencySnapshot` — `CoreFrameworks/NodeLatencyStats.hpp`
- `NodeLatencyStats` — `CoreFrameworks/NodeLatencyStats.hpp`
- `NodeSlowState` — `CoreFrameworks/ControllerEventLoop.hpp`
- `NotifyCommandState` — `CoreFrameworks/Notify.hpp`
- `NotifyEvent` — `CoreFrameworks/Notify.hpp`
- `NotifyState` — `CoreFrameworks/Notify.hpp`
- `Order` — `CoreFrameworks/Order.hpp`
- `OrderEvent` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderEventLog` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderEventLogFileHeader` — `CoreFrameworks/OrderEventLog.hpp`
- `OrderManagerState` — `CoreFrameworks/OrderManager.hpp`
- `OrderPreResolved` — `CoreFrameworks/Order.hpp`
- `OrderResult` — `CoreFrameworks/ExchangeAdapter.hpp`
- `ParameterSlot` — `CoreFrameworks/ParameterSlot.hpp`
- `PendingSubmission` — `CoreFrameworks/BinanceAdapter.hpp`
- `PerNodeCfg` — `CoreFrameworks/ControllerConfig.hpp`
- `Portfolio` — `CoreFrameworks/Portfolio.hpp`
- `PortfolioController` — `CoreFrameworks/PortfolioController.hpp`
- `Position` — `CoreFrameworks/Portfolio.hpp`
- `PositionEntryArgs` — `CoreFrameworks/Portfolio.hpp`
- `ReconcileOpenOrder` — `CoreFrameworks/Reconcile.hpp`
- `ReconcileResult` — `CoreFrameworks/Reconcile.hpp`
- `ReconcileTrade` — `CoreFrameworks/Reconcile.hpp`
- `ReconciliationLoopState` — `CoreFrameworks/ReconciliationLoop.hpp`
- `RegimeSignals` — `Strategies/RegimeDetector.hpp`
- `RewardTracker` — `ML_Headers/RewardTracker.hpp`
- `SPSCRing` — `CoreFrameworks/SPSCRing.hpp`
- `ShardedBacktestDriver` — `CoreFrameworks/ShardedBacktestDriver.hpp`
- `ShardedOrderLatency` — `CoreFrameworks/ShardedOrderLatency.hpp`
- `ShardedTradeLog` — `CoreFrameworks/ShardedTradeLog.hpp`
- `SimpleDipState` — `Strategies/SimpleDip.hpp`
- `SlowPathTelemetry` — `CoreFrameworks/ControllerEventLoop.hpp`
- `StampArgs` — `ML_Headers/StampHelper.hpp`
- `SubmitCommand` — `CoreFrameworks/OrderManager.hpp`
- `ThompsonBanditState` — `ML_Headers/ThompsonBandit.hpp`
- `Tick` — `CoreFrameworks/Tick.hpp`
- `TradeEvent` — `CoreFrameworks/TradeEvent.hpp`
- `WsHeartbeatTelemetry` — `CoreFrameworks/ControllerEventLoop.hpp`
