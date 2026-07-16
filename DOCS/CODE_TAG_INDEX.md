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

Converted files: 3 · unit blocks: 18

## [TAG] values → files

### BINARY_FP (1 files)

- `Strategies/RegimeDetector.hpp`

### BOOT_TIME (1 files)

- `CoreFrameworks/ExecutionCore.hpp`

### CAPITAL_BEARING (1 files)

- `CoreFrameworks/ExecutionCore.hpp`

### CONCURRENCY (1 files)

- `CoreFrameworks/ExecutionCore.hpp`

### DATA_ORIENTED_DESIGN (1 files)

- `CoreFrameworks/ExecutionCore.hpp`

### ENGINE (2 files)

- `CoreFrameworks/ExecutionCore.hpp`
- `Strategies/RegimeDetector.hpp`

### FRAMEWORK_DISCIPLINE (1 files)

- `Strategies/StrategyInterface.hpp`

### HOT_PATH (1 files)

- `CoreFrameworks/ExecutionCore.hpp`

### LIVE_TRADING (1 files)

- `CoreFrameworks/ExecutionCore.hpp`

### ML (1 files)

- `Strategies/RegimeDetector.hpp`

### SLOW_PATH (2 files)

- `CoreFrameworks/ExecutionCore.hpp`
- `Strategies/RegimeDetector.hpp`

## Unit blocks by [TYPE]

### ASSERT (1)

- `LAYOUT_LOCK` — `CoreFrameworks/ExecutionCore.hpp`

### FILE (2)

- `CoreFrameworks/ExecutionCore.hpp` — `CoreFrameworks/ExecutionCore.hpp`
- `RegimeDetector.hpp` — `Strategies/RegimeDetector.hpp`

### FUNCTION (6)

- `CumDelta_Init` — `Strategies/RegimeDetector.hpp`
- `ExecutionCore_Init` — `CoreFrameworks/ExecutionCore.hpp`
- `ExecutionCore_SetParameters` — `CoreFrameworks/ExecutionCore.hpp`
- `ExecutionCore_SetPermission` — `CoreFrameworks/ExecutionCore.hpp`
- `ExecutionCore_Tick` — `CoreFrameworks/ExecutionCore.hpp`
- `ExecutionCore_Tick_Impl` — `CoreFrameworks/ExecutionCore.hpp`

### REGISTRY (1)

- `FOREACH_STRATEGY` — `Strategies/StrategyInterface.hpp`

### STRUCT (3)

- `CumDeltaState` — `Strategies/RegimeDetector.hpp`
- `ExecutionCore` — `CoreFrameworks/ExecutionCore.hpp`
- `RegimeSignals` — `Strategies/RegimeDetector.hpp`
