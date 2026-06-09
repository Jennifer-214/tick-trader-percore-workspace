---
type: architecture-overview
stage: 5-claude-md
version: 2.0
established: 2026-05-18 (refreshed from v1 legacy single-core)
tags: [data-oriented-design, concurrency, framework-discipline]
surface: [hot-path, slow-path, oms-drainer, producer, registry, wire-format, ml-inference, cfg-flow, gui-thread, training, paper-test, live-trading, backtest, boot-time]
sister_specs: [concurrency-model-summary.md, cache-line-discipline.md, branchless-dispatch-discipline.md]
applies_at_skills: [/handoff, /readiness, /precoding-audit-gate]
---

# Architecture (per-node sharded HFT engine)

Tick-level crypto HFT trading platform in C++. Per-node risk-sharded hot path (40-400ns p99); branchless fixed-point math; X-macro registries for multi-site additions; bitmap-packed portfolio + flags.

This doc is the high-level orientation. Per-component detail lives in canonical sources cross-referenced below.

---

## Component overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                    GLOBAL THREADS (1 each)                          │
├─────────────────────────────────────────────────────────────────────┤
│ PRODUCER (1):  Binance WS parse → ema_price replication →           │
│                fan_out to N per-core SPSC rings → GUI publish       │
│ DRAINER  (1):  OMS_DrainSubmit → OrderManager_Tick → DrainPostFill  │
│ ASYNC    (N):  Binance order API / Notify worker / Recorders / GUI  │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  │ SPSC ring per core
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                PER-CORE CONSUMERS (N = 2..16; default 4)            │
├─────────────────────────────────────────────────────────────────────┤
│  HOT thread (1 per core; ≤500ns p99; branchless):                   │
│    ExecutionCore_Tick → BG_Evaluate → SG_Evaluate ×2 →              │
│    push TradeEvent (rare branch)                                    │
│                                                                     │
│  SLOW thread (1 per core; ≤100μs p99; every poll_interval ticks):   │
│    EventLoop_UpdateRollingStateOneCore → Regime_Classify →          │
│    Strategy rebuild → ExecutionCore_SetParameters (seqlock to hot)  │
│    → TimeExitOneCore → TrailingSLRatchetOneCore                     │
└─────────────────────────────────────────────────────────────────────┘
```

Each core = self-contained strategy unit (slow + hot pthread pair).
Sharded is production. Legacy single_core LIVE is deprecated (warned at boot).
Legacy backtest is gone — `Backtest_Run` wraps `BacktestSharded_Run`.

---

## Data flow (tick → decision)

```
[Binance WSS] → [TLS Socket] → [WebSocket frame] → [simdjson parse]
                                                          │
                                                  [tt::parse_double_fast]
                                                          │
                                                          ▼
                                              [Producer fan_out]  ← ema_price replicate
                                                          │
                            ┌────────────┬────────────────┼────────────┬────────────┐
                            │            │                │            │            │
                       SPSC ring[0]  ring[1]            ring[2]     ring[3]      ...ring[N]
                            │            │                │            │            │
                            ▼            ▼                ▼            ▼            ▼
                      [Core 0 HOT] [Core 1 HOT]    [Core 2 HOT] [Core 3 HOT]   ...
                            │
                            ├─ BG_Evaluate (buy gate; branchless)
                            ├─ SG_Evaluate (sell gate; per leg A+B; branchless)
                            └─ push TradeEvent → drainer ring
                                                          │
                                                          ▼
                                                  [DRAINER thread]
                                                          │
                                                  OMS_DrainSubmit
                                                          │
                                                  OrderManager_Tick
                                                          │
                                                  DrainPostFill ← (live: BinanceOrderAPI)
                                                          │
                                                          ▼
                                                  [Per-core slow] ← post-fill events
                                                  EventLoop_UpdateRollingState
                                                  Regime_Classify
                                                  Strategy rebuild
                                                  ExecutionCore_SetParameters (seqlock)
                                                          │
                                                          ▼
                                              (next tick reads new params)
```

---

## Sub-system pointers (canonical sources)

| Concern | Canonical source |
|---|---|
| Hot path discipline + cadence tiers | `DOCS/HOT_PATH_CHANGELOG.md` |
| Code map (per-file responsibilities) | `DOCS/CODE_MAP.md` |
| Hard invariants H1-H20 | `CLAUDE.md § Hard Invariants` table |
| Coding rules + 11 strict invariants | `DOCS/STRATEGY_AND_CODING_RULES.md` (private) |
| Per-component invariants | `DOCS/CLAUDE_INVARIANTS.md` |
| ML pipeline invariants | `DOCS/CLAUDE_ML_INVARIANTS.md` |
| Thread architecture + sync primitives | `DESIGN_SPECS/concurrency-patterns/concurrency-model-summary.md` |
| Cache layout + alignment discipline | `DESIGN_SPECS/data-disciplines/cache-line-discipline.md` |
| Branchless dispatch discipline | `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md` |
| Wire-format byte preservation | `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` |
| X-macro registry pattern | `DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md` |
| Meta-registry topology | `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md` |
| Bug class catalog | `DOCS/RECURRING_BUG_PATTERNS.md` |
| Decoupling roadmap (long-horizon) | `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` |

---

## Per-component highlights

### CoreFrameworks/
ExecutionCore (hot-path tick dispatcher) / OrderGates / Portfolio (bitmap-packed) / ControllerEventLoop (slow-path orchestrator) / EngineSharded (producer + per-node thread spawning) / OMS (drainer thread) / CfgFieldRegistry + CfgFieldDispatch (X-macro auto-flow) / **MetaRegistry** (H15 enforcement).

### Strategies/
RegimeDetector (RANGING / TRENDING / VOLATILE / MILD_TREND with hysteresis) / MeanReversion / Momentum / SimpleDip / EmaCross / MLStrategy / StrategyParameters (X-macro dispatcher) / StrategyInterface / StrategyCategories + OpModeCategories (categorical applicability gates).

### DataStream/
BinanceCrypto (WSS tick stream) / Depth (orderbook stream) / DepthReplayState / DepthRecorder / TickRecorder / BinanceOrderAPI (live REST) / EngineTUI (text dashboard).

### FixedPoint/
`FPN<F=64>` = 16-byte 128-bit `__int128` (64.64 two's-complement fixed-point). `is_FPN_v` type trait. NEVER `float`/`double` on accounting paths (H4).

### MemHeaders/
PoolAllocator (bitmap order pool) / BuddyAllocator / BitmapMacros / FailureModeRegistry / CfgGateRegistry (FOREACH_STAMP_BOUND_DERIVED_COHORT meta-walker).

### ML_Headers/
RollingStats / ROR_regressor / ConfidenceScore / ModelInference (XGBoost) / FlowFeatures / StampBoundCfgRegistry / StampBoundModelConstRegistry / FeatureRegistry (FOREACH_FEATURE) / FeatureStandardizer (scaler).

### GUI/
Dear ImGui native (SDL2 + OpenGL3): FoxmlTheme / DashboardPanels / ChartPanel / CandleAccumulator / TradeReader / SettingsPanel / TradeHistoryPanel / LogViewerPanel / GuiThread.

### Backtest/
`Backtest_Run` wrapper + `BacktestSharded_Run` / BacktestPanels / LabelFunctions / HeldOutSplit / ValidationSplit / Walk-Forward / Held-Out gates.

### tests/
`controller_test.cpp` (3118 tests; queued split per TECH_DEBT-114) / `parity_harness.cpp` / `depth_recorder_test.cpp`.

---

## Hard invariants (NEVER break — full table at CLAUDE.md § Hard Invariants)

H1 no heap alloc / H2 no virtual on hot path / H3 no mutex anywhere / H4 FPN<F> on accounting paths / H5 no scalar JSON / H6 alignas(64) cross-thread / H7 hot path branchless / H8 ≤500ns hot p99 + ≤100μs slow p99 / H9 wire byte preservation / H10 SIMD scalar fallback / H11 constant-iter math / H12 padding fields default-init / H13 tt:: dispatch (no reinterpret_cast) / H14 NO C++ bitfield syntax (hand-written BITMAP_*/MBS_*) / H15 FOREACH_REGISTRY enrollment / H16 metadata-bit derived-filter / H17 cfg struct auto-gen / H18 sidecar override / H19 meta-registry topology / H20 branchless on SP/HP.

---

## Build summary

- `./build.sh test` — engine + controller_test
- `./build.sh gui` — engine_gui + foxml_suite (SDL2+OpenGL3+ImGui)
- `./build.sh suite` — same + XGBoost
- `./build.sh tsan` / `asan` — sanitizer builds
- Flags: `-DLATENCY_PROFILING=ON` / `-DLATENCY_LITE=ON` / `-DBUSY_POLL=ON` / `-DUSE_NATIVE_128=ON`

5 binaries clean = ship gate (engine + engine_gui + foxml_suite + controller_test + parity_harness).

---

## End state / trajectory

See CLAUDE.md § Design philosophy + priorities for the end-state vision:
- **Current** = v5.X professionalization phase (framework-driven extensibility, audit-driven discipline)
- **Near-term** = v6.0 decoupled runtime/viewer (per `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`)
- **Long-horizon** = framework-driven extensibility (1-row-in-registry adds for new strategies/features/markets)

---

## Cross-references

- `CLAUDE.md` (always-loaded orientation; Design philosophy + Hard invariants + How to find anything)
- `DOCS/DESIGN_PHILOSOPHY.md` (deep WHY discussion; 14 sections + § 11.5 meta-disciplines)
- `DOCS/CODE_MAP.md` (per-file responsibilities)
- `DOCS/HOT_PATH_CHANGELOG.md` (hot path cadence tier classification)
- `DOCS/STRATEGY_AND_CODING_RULES.md` (private; 11 strict invariants)
- `DESIGN_SPECS/concurrency-patterns/concurrency-model-summary.md` (thread architecture detail)
- `DESIGN_SPECS/data-disciplines/cache-line-discipline.md` (DOD layout discipline detail)
- `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md` (Class 28 + H20 detail)
- `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` (long-horizon roadmap)

---

**Refreshed:** 2026-05-18 from v1 legacy single-core description (was stale: described `PortfolioController_Tick` + 134-test era).
**Refresh trigger:** Caramel's institutional-memory architecture push at v5.15.5.F.4d.1.B.3 doc-layer refresh; companion to `concurrency-model-summary.md` Stage 2 DRAFT.
