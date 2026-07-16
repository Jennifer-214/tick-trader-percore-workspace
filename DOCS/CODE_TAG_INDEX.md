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

Converted files: 2 · unit blocks: 5

## [TAG] values → files

### BINARY_FP (1 files)

- `Strategies/RegimeDetector.hpp`

### ENGINE (1 files)

- `Strategies/RegimeDetector.hpp`

### FRAMEWORK_DISCIPLINE (1 files)

- `Strategies/StrategyInterface.hpp`

### ML (1 files)

- `Strategies/RegimeDetector.hpp`

### SLOW_PATH (1 files)

- `Strategies/RegimeDetector.hpp`

## Unit blocks by [TYPE]

### FILE (1)

- `RegimeDetector.hpp` — `Strategies/RegimeDetector.hpp`

### FUNCTION (1)

- `CumDelta_Init` — `Strategies/RegimeDetector.hpp`

### REGISTRY (1)

- `FOREACH_STRATEGY` — `Strategies/StrategyInterface.hpp`

### STRUCT (2)

- `CumDeltaState` — `Strategies/RegimeDetector.hpp`
- `RegimeSignals` — `Strategies/RegimeDetector.hpp`
