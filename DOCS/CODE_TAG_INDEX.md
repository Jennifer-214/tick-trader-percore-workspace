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

Converted files: 11 · unit blocks: 73

## [TAG] values → files

### BINARY_FP (1 files)

- `Strategies/RegimeDetector.hpp`

### BITMAP_PACKED (1 files)

- `CoreFrameworks/Portfolio.hpp`

### BOOT_TIME (6 files)

- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/SPSCRing.hpp`

### CAPITAL_BEARING (5 files)

- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/TradeEvent.hpp`

### CONCURRENCY (4 files)

- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/TradeEvent.hpp`

### CRITICAL (3 files)

- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/SPSCRing.hpp`

### DATA_ORIENTED_DESIGN (6 files)

- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/Tick.hpp`

### DATA_PLANE (2 files)

- `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/Tick.hpp`

### DECIMAL (4 files)

- `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/Tick.hpp`

### ENGINE (10 files)

- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/Tick.hpp`
- `CoreFrameworks/TradeEvent.hpp`
- `Strategies/RegimeDetector.hpp`

### FLOAT_DISPLAY_ONLY (1 files)

- `CoreFrameworks/NodeLatencyStats.hpp`

### FRAMEWORK_DISCIPLINE (1 files)

- `Strategies/StrategyInterface.hpp`

### HOT_PATH (8 files)

- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/Tick.hpp`
- `CoreFrameworks/TradeEvent.hpp`

### LIVE_TRADING (1 files)

- `CoreFrameworks/ExecutionCore.hpp`

### ML (1 files)

- `Strategies/RegimeDetector.hpp`

### MONITORING_PLANE (2 files)

- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/SPSCRing.hpp`

### PERSISTENCE (1 files)

- `CoreFrameworks/Portfolio.hpp`

### SLOW_PATH (5 files)

- `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/Portfolio.hpp`
- `Strategies/RegimeDetector.hpp`

### STRUCTURAL_FIX (1 files)

- `CoreFrameworks/Portfolio.hpp`

### SUPPORTIVE (2 files)

- `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/Portfolio.hpp`

## Unit blocks by [TYPE]

### ASSERT (6)

- `EPOCH_TRIPWIRE` — `CoreFrameworks/Portfolio.hpp`
- `LAYOUT_LOCK` — `CoreFrameworks/ExecutionCore.hpp`
- `LAYOUT_LOCK` — `CoreFrameworks/GateParameters.hpp`
- `LAYOUT_LOCK` — `CoreFrameworks/Portfolio.hpp`
- `LAYOUT_LOCK` — `CoreFrameworks/Tick.hpp`
- `LAYOUT_LOCK` — `CoreFrameworks/TradeEvent.hpp`

### FILE (10)

- `CoreFrameworks/ExecutionCore.hpp` — `CoreFrameworks/ExecutionCore.hpp`
- `CoreFrameworks/GateParameters.hpp` — `CoreFrameworks/GateParameters.hpp`
- `CoreFrameworks/NodeLatencyStats.hpp` — `CoreFrameworks/NodeLatencyStats.hpp`
- `CoreFrameworks/OrderGates.hpp` — `CoreFrameworks/OrderGates.hpp`
- `CoreFrameworks/ParameterSlot.hpp` — `CoreFrameworks/ParameterSlot.hpp`
- `CoreFrameworks/Portfolio.hpp` — `CoreFrameworks/Portfolio.hpp`
- `CoreFrameworks/SPSCRing.hpp` — `CoreFrameworks/SPSCRing.hpp`
- `CoreFrameworks/Tick.hpp` — `CoreFrameworks/Tick.hpp`
- `CoreFrameworks/TradeEvent.hpp` — `CoreFrameworks/TradeEvent.hpp`
- `RegimeDetector.hpp` — `Strategies/RegimeDetector.hpp`

### FUNCTION (32)

- `BG_Evaluate` — `CoreFrameworks/GateParameters.hpp`
- `BuyGate` — `CoreFrameworks/OrderGates.hpp`
- `CumDelta_Init` — `Strategies/RegimeDetector.hpp`
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
- `ParameterSlot_Init` — `CoreFrameworks/ParameterSlot.hpp`
- `ParameterSlot_Read` — `CoreFrameworks/ParameterSlot.hpp`
- `ParameterSlot_Write` — `CoreFrameworks/ParameterSlot.hpp`
- `Portfolio_AddPositionWithExits` — `CoreFrameworks/Portfolio.hpp`
- `Portfolio_CloseSlot` — `CoreFrameworks/Portfolio.hpp`
- `Portfolio_ComputePnL` — `CoreFrameworks/Portfolio.hpp`
- `Portfolio_Load` — `CoreFrameworks/Portfolio.hpp`
- `Portfolio_OpenSlot` — `CoreFrameworks/Portfolio.hpp`
- `Portfolio_Save` — `CoreFrameworks/Portfolio.hpp`
- `PositionExitGate` — `CoreFrameworks/Portfolio.hpp`
- `Position_Reset` — `CoreFrameworks/Portfolio.hpp`
- `SG_Evaluate` — `CoreFrameworks/GateParameters.hpp`
- `SPSCRing_Depth` — `CoreFrameworks/SPSCRing.hpp`
- `SPSCRing_Init` — `CoreFrameworks/SPSCRing.hpp`
- `SPSCRing_TryPop` — `CoreFrameworks/SPSCRing.hpp`
- `SPSCRing_TryPush` — `CoreFrameworks/SPSCRing.hpp`
- `SellGate` — `CoreFrameworks/OrderGates.hpp`

### REGISTRY (1)

- `FOREACH_STRATEGY` — `Strategies/StrategyInterface.hpp`

### STRUCT (15)

- `CumDeltaState` — `Strategies/RegimeDetector.hpp`
- `DataStream` — `CoreFrameworks/OrderGates.hpp`
- `ExecutionCore` — `CoreFrameworks/ExecutionCore.hpp`
- `ExitRecord` — `CoreFrameworks/Portfolio.hpp`
- `GateParameters` — `CoreFrameworks/GateParameters.hpp`
- `NodeLatencySnapshot` — `CoreFrameworks/NodeLatencyStats.hpp`
- `NodeLatencyStats` — `CoreFrameworks/NodeLatencyStats.hpp`
- `ParameterSlot` — `CoreFrameworks/ParameterSlot.hpp`
- `Portfolio` — `CoreFrameworks/Portfolio.hpp`
- `Position` — `CoreFrameworks/Portfolio.hpp`
- `PositionEntryArgs` — `CoreFrameworks/Portfolio.hpp`
- `RegimeSignals` — `Strategies/RegimeDetector.hpp`
- `SPSCRing` — `CoreFrameworks/SPSCRing.hpp`
- `Tick` — `CoreFrameworks/Tick.hpp`
- `TradeEvent` — `CoreFrameworks/TradeEvent.hpp`
