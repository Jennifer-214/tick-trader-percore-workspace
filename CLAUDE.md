# CLAUDE.md

Always-loaded architectural orientation for this codebase. Stays GENERAL — sprint state + going-forward rules + memory live elsewhere (see Reference docs below).

## Purpose

Claude assists with **planning + implementation of an HFT trading engine** in C++. The codebase prioritizes (in order): **latency** (sub-microsecond hot path) → **determinism** (cross-run / cross-binary / cross-locale byte equivalence) → **maintainability** (structural fix preferred when a bug class can recur) → **operator UX**.

When trade-offs conflict, name which wins + why per `DOCS/DESIGN_PHILOSOPHY.md` § 1. Default to deeper architectural option when the operator is engaged + the math favors it (per `feedback_overengineering_boundary_when_future_easier` + `feedback_plan_right_not_fast`).

For sprint state, going-forward rules, and operator-collaboration discipline, see `CLAUDE.local.md` (private overlay) + `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/MEMORY.md`.

## Overview

Tick-level crypto HFT trading engine in C++. Per-core risk-sharded hot
path (40-400ns p99); branchless fixed-point math (`FPN<F=64>` = 24B);
X-macro registries for multi-site additions; bitmap-packed portfolio +
flags. Single producer thread fans Binance ticks across SPSC rings →
N per-core consumers (default 4, cap 16); each core = self-contained
strategy unit (slow + hot pthread pair). Sharded is production. Legacy
single_core LIVE is deprecated (warned at boot). Legacy backtest is
gone — `Backtest_Run` wraps `BacktestSharded_Run`.

## Build

`./build.sh test` (engine + controller_test), `gui` (engine_gui +
foxml_suite), `suite` (suite with XGBoost), `tsan` / `asan` (sanitizer
builds), `all`, `clean`. Build flags: `-DLATENCY_PROFILING=ON`,
`-DLATENCY_LITE=ON`, `-DLATENCY_BENCH=ON`, `-DBUSY_POLL=ON`,
`-DUSE_NATIVE_128=ON`.

Build dirs (different compile flags → different outputs): `build/`
(ANSI + tests, zero deps), `build_gui/` (engine_gui + foxml_suite —
SDL2 + OpenGL3 + ImGui), `build_suite/` (same + XGBoost), `build_lat/`
(LATENCY_PROFILING), `build_tsan/`, `build_asan/`.

XGBoost C library (for `-DUSE_XGBOOST=ON`): clone `dmlc/xgboost`
recursive, cmake with `-DBUILD_STATIC_LIB=OFF`, install + ldconfig.

`build.sh` symlinks `engine.cfg` into each build dir; `bin/engine_gui`
→ `build_gui/engine_gui`.

## Architecture (sharded)

```
HOT PATH (per tick, per core, branchless; ≤500ns p99):
  BG_Evaluate → SG_Evaluate ×2 → TradeEvent push (rare branch)

SLOW PATH (per-core thread, every poll_interval ticks; ≤100μs p99):
  EventLoop_UpdateRollingStateOneCore → RebuildOneCore (regime + strategy)
  → ExecutionCore_SetParameters (seqlock to hot path)
  → TimeExitOneCore → TrailingSLRatchetOneCore

GLOBAL THREADS:
  Producer: tick read + fan_out + ema_price replication + GUI publish
  Drainer:  OMS_DrainSubmit + OrderManager_Tick + DrainPostFill
  Async:    Binance trade WS, depth WS, Tick/DepthRecorder, Notify worker, GUI
```

- Per-core strategy (`core_N_strategy=simple_dip|momentum|ema_cross|ml`)
- Per-core ML model (`core_N_model_path=...` or `core_N_model_dir=...`)
- Per-core risk (`core_N_risk_pct=...`)
- Per-core ConfidenceScorer (when STRATEGY_ML)
- Per-core slow_state owns rolling/regime/flow data (v5.1.2+)
- Partial exits (`partial_exit_enabled=1`): each core owns 2 slots (legs A+B); max cores = 8
- `engine_arch=per_core_slow` (default v5.0+) | `centralized` (legacy)

## Data Flow: Regime Detection

Per-engine slow_state (RollingStats × 4 + RORRegressor + flow + depth)
→ RegimeSignals (slope, R², variance, ror_slope, ema_sma_spread,
book_imbalance, spread_z, flow_*_ewma, large_trade_z, ...) →
Regime_Classify (trending_score + volatile_score with hysteresis) →
RANGING / TRENDING / VOLATILE / MILD_TREND → strategy dispatch.

`RegimeSignals` is the extensibility point — see
`DOCS/CLAUDE_INTEGRATION.md` for the recipe.

## Directory Structure

| Dir | Contents |
|---|---|
| `CoreFrameworks/` | OrderGates, Portfolio, ExecutionCore, ControllerEventLoop, EngineSharded, ShardedSnapshot/Persist, GateParameters, TradeEvent, OrderManager, ShardedBacktestDriver, **CfgFieldRegistry / CfgFieldDispatch (v5.15.5.F.4b+)** |
| `Strategies/` | RegimeDetector, MeanReversion, Momentum, SimpleDip, EmaCross, MLStrategy, StrategyParameters (dispatcher), StrategyInterface, **StrategyCategories / OpModeCategories (v5.15.5.F.4b+)** |
| `DataStream/` | BinanceCrypto/Depth, DepthReplayState, DepthRecorder, TickRecorder, BinanceOrderAPI, EngineTUI |
| `FixedPoint/` | FPN<F=64> (4096-bit) + `is_FPN_v` type trait |
| `MemHeaders/` | PoolAllocator (bitmap order pool), BuddyAllocator, BitmapMacros, FailureModeRegistry |
| `ML_Headers/` | RollingStats, ROR_regressor, ConfidenceScore, ModelInference (XGBoost), FlowFeatures, StampBoundCfgRegistry, StampBoundModelConstRegistry |
| `GUI/` | Dear ImGui native: FoxmlTheme, DashboardPanels, ChartPanel, CandleAccumulator, TradeReader, SettingsPanel, TradeHistoryPanel, LogViewerPanel, GuiThread |
| `Backtest/` | `Backtest_Run` wrapper + `BacktestSharded_Run`, BacktestPanels, LabelFunctions, HeldOutSplit, ValidationSplit |
| `tests/` | controller_test.cpp (3118 tests), parity_harness.cpp |
| `DOCS/` | CHANGELOG.md, changelogs/, CLAUDE_*.md (split-load reference docs), RECURRING_BUG_PATTERNS.md, STRATEGY_AND_CODING_RULES.md (private) |
| `plans/` | gitignored (symlinked to workspace); working plans + plan_checks + handoffs + postmortems |
| `Version.hpp`, `Limits.hpp` | single source of truth |

## Hard Invariants (NEVER BREAK)

Full discussion: `DOCS/DESIGN_PHILOSOPHY.md` § 2 + `DOCS/STRATEGY_AND_CODING_RULES.md` (private; 11 strict invariants).

| # | Rule |
|---|---|
| H1 | NO `malloc` / `new` / `std::vector` / `std::string` / `std::function` — anywhere |
| H2 | NO `virtual` / `std::shared_ptr` / `std::unique_ptr` on hot path |
| H3 | NO `std::mutex` / `condition_variable` / `sleep_for` / `pthread_rwlock` — anywhere |
| H4 | `FPN<F=64>` for accounting math; NEVER `float`/`double` on accounting paths (display-only OK) |
| H5 | NO scalar JSON / `strstr` / `atof` in parser inner loops; use `simdjson` / `fast_float` / `tt::parse_double_fast` |
| H6 | Cross-thread fields get `alignas(64)`; cluster fields by access pattern (hot reads / hot writes / cold init / cross-thread) |
| H7 | Hot path BRANCHLESS for data-dependent dispatch (mask compute, cmov; per Rule 8 of latency-path-discipline) |
| H8 | Hot path p99 ≤500ns; slow path p99 ≤100μs (regression = ship blocker) |
| H9 | Wire-format byte preservation for HMAC-signed bodies (stamps, snapshots, RunHistory); locale pinning at emit |
| H10 | AVX-512 SIMD kernels MUST have scalar fallback producing BYTEWISE IDENTICAL output |
| H11 | Math kernels on slow/hot path: CONSTANT-ITER + branchless within reductions |
| H12 | Structs in byte-equivalence contexts (memcmp / SHA-256 / wire format / HMAC input): EXPLICIT `int<N>_t _padding<N> = 0;` default-init fields |
| H13 | Type-erased `*reinterpret_cast<T*>((char*)cfg + offset) = v` style dispatch is FORBIDDEN — use `tt::<verb>_field<T>` with T deduced (Class 23 3-barrier fix) |
| H14 | NO C++ bitfield syntax (`name : N`) anywhere — multi-bit state encoding uses manual `SHIFT_*`/`MASK_*` constants + `MBS_*`/`BITMAP_*` branchless accessors over `uint{8,16,32,64}_t` storage; layout/signedness/packing-order are implementation-defined (conflicts with H6/H9/H10/H12) |
| **H15** | **Every X-macro registry in the codebase MUST have a row in `FOREACH_REGISTRY` meta-registry** at `CoreFrameworks/MetaRegistry.hpp` (codified `.F.4d` 2026-05-16). Adding a new registry without enrollment fails CI Check `test_meta_registry_coverage`. Closes meta-Class-18 (added registry but forgot to document). See `DESIGN_SPECS/meta-registry-pattern-for-codebase-registry-discipline.md`. |
| H16 | (Structural detail; full discussion in `DOCS/STRATEGY_AND_CODING_RULES.md` § H16 private overlay.) Every `CfgFieldDescriptor::MetadataFlag` bit MUST have a derived filter row in `FOREACH_DERIVED_FILTER` OR a documented exemption with rationale. CI Check `test_metadata_bit_to_derived_filter_coverage` enforces. Codified `.F.4d` 2026-05-16. |
| H17 | (Structural detail; full discussion in `DOCS/STRATEGY_AND_CODING_RULES.md` § H17 private overlay.) `ControllerConfig<F>` cfg struct fields auto-generated from `FOREACH_CFG_FIELD`; NO manual cfg field declarations. `PerCoreCfg<F>` body = X-macro only (CI Check 2 since `.F.4c`). Codified `.F.4d` 2026-05-16. |
| **H18** | **Custom-semantics for registry auto-flows via SIDECAR OVERRIDE pattern** (sparse `FOREACH_<DOMAIN>_OVERRIDE` indexed by parent's `FIELD_IDX`); NEVER parallel wide-variant registries (Class 21 anti-pattern at auto-flow surface). STRONG initially; **HARD after 2nd cohort application** per pattern-codification-lifecycle.md. Codified `.F.4d` 2026-05-16 (1st canonical: XGBoost drift override cohort, 5 rows in `FOREACH_DRIFT_OVERRIDE`). See `DESIGN_SPECS/sidecar-override-pattern-for-registry-auto-flows.md`. |
| **H19** | **Every `FOREACH_REGISTRY` row with LEVEL > 0 (meta-registry) MUST declare a valid PARENT** (the registry it manages). Topology discipline; CI Check `test_meta_registry_topology` enforces (Level 0 = standalone data registries; Level 1 = meta-registries managing cohorts; Level 2 = top-level `FOREACH_REGISTRY` itself). Codified `.F.4d` 2026-05-16. See `DESIGN_SPECS/meta-registry-pattern-for-codebase-registry-discipline.md`. |
| **H20** | **Branchless preferred for SP/HP data-dependent dispatch EVEN WHEN NOMINALLY SLOWER** (added v5.15.5.F.4c.3 WIP2d-1.B.0d). Mask code / fn pointer tables / cmov / mask-select / dummy-redirect can be optimized later (better instruction selection, vectorization, prefetch hints). Branch mispredicts CANNOT be optimized (hardware cost; 30-100ns real-world per `DESIGN_PHILOSOPHY.md` § 4 updated). For a determinism-prioritizing system (HFT premise), variance from branches is the bigger cost. Sister to H7 (hot path strict); H20 generalizes the discipline to SP + drainer + producer-fan-out. Exceptions per decision matrix in `DESIGN_SPECS/branchless-dispatch-discipline.md` (boot-time-only / `__builtin_expect`-rare / `if constexpr` compile-time / genuine binary predicate with no alternative computation). Closes Class 28. |

**H15-H19 codified at v5.15.5.F.4d ship close 2026-05-16** (per `plans/v5.15-live-readiness/subplans/2026-05-16-v5.15.5.F.4d-merged-framework-bandit-thompson.md` Charter 11 closure). Placement decision: H15/H18/H19 in this CLAUDE.md table (broad framework-discipline visibility); H16/H17 in `DOCS/STRATEGY_AND_CODING_RULES.md` private overlay (structural enforcement detail). See `DOCS/DESIGN_PHILOSOPHY.md` § 2 for the family-grouped narrative discussion of all 20 invariants.

## Code Conventions

- `using namespace std;` throughout
- C-style with templates, no classes (with one exception: RAII destructors on resource-owning structs that own threads or mmap'd memory; e.g., `~OrderManagerState()` since v5.11.26 — see destructor comment in `CoreFrameworks/OrderManager.hpp` for criteria)
- `Pattern_FunctionName` (e.g., `Portfolio_Init`, `BG_Evaluate`, `OMS_DrainSubmit`)
- Hot-path math is `FPN<F>` only, no floats (F=64 = 4096-bit; 24 bytes)
- Branchless: mask tricks `-(uint64_t)pass`, word-level mask-select
- Inline comments explain WHY, not WHAT (well-named identifiers handle the WHAT)
- **Preserve user's voice in existing comments when editing**
- New cfg field of recognized Kind = 1 row in `FOREACH_CFG_FIELD` (`CoreFrameworks/CfgFieldRegistry.hpp`); parser + GUI render + tooltip + per-core override emission auto-flow

### Test file size discipline (added v5.11.35)

`tests/controller_test.cpp` is currently ~25k lines + 3118 tests.
That's too big — slow to compile, hard to navigate, easy to break
during refactors. The build system already supports multiple test
binaries (`depth_recorder_test`, `parity_harness` are precedents).

**Rule:** any test file > 5k lines OR > 100 test sections must be
split BEFORE adding more tests. Categories should be domain-aligned:
`controller_test_engine.cpp` / `_features.cpp` / `_stamps.cpp` /
`_ml.cpp` / `_misc.cpp`. Helpers extract into `tests/test_common.hpp`.

The actual split is queued as a v5.11.35 sub-ship (deferred from
multiple sessions because 3118 tests at risk warrants a focused
effort with rollback anchor).

## Reference Docs (portal hierarchy — read on demand)

CLAUDE.md is orientation; the portal hierarchy descends from here:

```
CLAUDE.md                          (orientation — this doc; always loaded)
     ↓
DOCS/DESIGN_PHILOSOPHY.md          (WHY + meta-rules; master settings portal)
     ↓
DESIGN_SPECS/                      (HOW patterns — 80+ specs; read per topic)
     ↓
DOCS/RECURRING_BUG_PATTERNS.md     (anti-patterns; pre-coding sweep)
     ↓
memory/                            (operator-collaboration rules; auto-loaded)
     ↓
CLAUDE.local.md                    (operator overlay + sprint state index; auto-loaded)
```

If you can't find the answer at the layer you're looking at, go DOWN the hierarchy.

**Read on-demand when the work matches:**

| When working on... | Read |
|---|---|
| Cold-pickup / WHY any principle / contributor onboarding / cross-family trade-off / new pattern codification | `DOCS/DESIGN_PHILOSOPHY.md` (master settings portal; 14 sections with cross-ref index) |
| Reusable architectural pattern catalog (80+ patterns; tagged by surface/concern/lifecycle/applications) | `DESIGN_SPECS/README.md` |
| Bug class catalog + detection signatures (30+ recurring anti-pattern classes) | `DOCS/RECURRING_BUG_PATTERNS.md` |
| Operator-collaboration rules (how Claude should engage with the operator on this codebase) | `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/MEMORY.md` |
| Going-forward rules + sprint state + auto-write contracts | `CLAUDE.local.md` (private overlay) |
| Hard invariants (full discussion of H1-H11 strict rules; private) | `DOCS/STRATEGY_AND_CODING_RULES.md` |
| Latency optimization audit findings (13-part private audit) | `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` |
| Latency-path discipline (architectural rules + anti-pattern history) | `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` |
| Adding cfg field / GUI panel / strategy / ML feature / per-core override | `DOCS/CLAUDE_INTEGRATION.md` |
| Changing OMS / kill switch / snapshot / hot path / slow-path threading | `DOCS/CLAUDE_INVARIANTS.md` |
| Touching FeatureRegistry / scaler / stamp / train→serve path | `DOCS/CLAUDE_ML_INVARIANTS.md` |
| Planning a multi-day change | `DOCS/CLAUDE_REVIEW.md` |
| Backtest suite (Run Control, Training, WF, Held-Out) | `DOCS/CLAUDE_FOXML_SUITE.md` |

These are *never* automatically loaded — read on-demand when the
conversation matches a row above. Keeps always-on context small
(~2000 words) so routine changes are fast; detailed rules + WHY are
authoritative when needed.

## How to ... (Quick Discovery)

Each entry: GENERAL task → where to start. For sprint-specific phasing of cfg-field auto-flow + stamp-binding readiness, see `CLAUDE.local.md` "Current sprint state" + `DOCS/DESIGN_PHILOSOPHY.md` § 11.

| Task | Where to start |
|---|---|
| Add a strategy | `/strategy-template` skill + `DOCS/CLAUDE_INTEGRATION.md` |
| Add a cfg field | 1 row in master registry at `CoreFrameworks/CfgFieldRegistry.hpp` (parser + GUI render + tooltip + per-core override emission auto-flow per framework state — see `DESIGN_SPECS/universal-cfg-field-registry-pattern.md` for current capabilities) |
| Add a STAMP_BOUND cfg field | Set `STAMP_BOUND_CFG_DERIVED` bit in master registry row's metadata column (drift check + Layer 5b hash + wire emit auto-flow per `DESIGN_SPECS/metadata-bit-driven-derived-filter-framework.md`) |
| Add a new derived filter (metadata-bit cohort) | 1 row in `FOREACH_DERIVED_FILTER` (framework auto-flow per `DESIGN_SPECS/metadata-bit-driven-derived-filter-framework.md`) |
| Add an ML feature | `ML_Headers/FeatureRegistry.hpp` + `DOCS/CLAUDE_ML_INVARIANTS.md` |
| Add a SHALT code / halt reason / regime / strategy / bandit algo | Registry table per X-macro pattern (`DESIGN_PHILOSOPHY.md` § 7 + `DESIGN_SPECS/x-macro-registry-with-presence-dispatch.md`) |
| Add a stateful GUI panel | `DOCS/CLAUDE_INTEGRATION.md` § "GUI panels" + display↔execution invariant check |
| Plan a non-trivial change | `/readiness` skill + `DOCS/CLAUDE_REVIEW.md` checklist + new plan body uses `DESIGN_SPECS/future-oriented-plan-template.md` |
| Audit a plan before coding | `/precoding-audit-gate` (orchestrator) → SHAPE audits in parallel + (`/blindspot-scan` if struct-gen / type unification / cross-registry consumer / wire-format ordering migration) |
| Audit existing code for anti-patterns | `/bug-check` (against RECURRING_BUG_PATTERNS classes) + `/dod-audit` (against DESIGN_SPECS catalog) + `/anti-spaghetti` (codebase-wide structural sweep) |
| Track a new bug class | Add to `DOCS/RECURRING_BUG_PATTERNS.md` (auto-included in `/bug-check`); include "False-positive surface" subsection per M3 discipline |
| Track a new meta-discipline (audit-methodology gap) | Codify per `DESIGN_PHILOSOPHY.md` § 11.5 procedure (NEW DESIGN_SPEC + skill amendment + `/readiness` Check + memory + CI tool if mechanical) |
| Ship a sub-ship | `/ship` skill (build verify + version bump + commit + tag + push) |
| Generate handoff prompt for fresh context | `/handoff` skill |

## Skill suite (audit-driven discipline)

Skills group by concern. Read each skill's `claude-skills/<name>/SKILL.md` for invocation details.

| Concern | Skills |
|---|---|
| **Pre-coding plan verification** | `/readiness` (28-check pass) + `/precoding-audit-gate` (orchestrator firing parallel audits) |
| **SHAPE audits (design-layer)** | `/parity-check` (train↔serve identity; wire byte preservation) + `/trace-deps` (dependency chains) + `/merge-scan` (reuse opportunities) + `/dod-audit` (DESIGN_SPECS pattern application) |
| **IMPLEMENTATION-DETAIL audits (code-layer)** | `/blindspot-scan` (12-category implementation taxonomy; fires after SHAPE returns GREEN/YELLOW per `DESIGN_PHILOSOPHY.md` § 11.5) |
| **DOMAIN audits** | `/accounting-audit` (OMS / fee / P&L) + `/hft-audit` (universal HFT principles) + `/ml-audit` (ML pipeline) + `/registry-fit-audit` (registry misapplication) |
| **Anti-pattern scans** | `/bug-check` (RECURRING_BUG_PATTERNS instances) + `/anti-spaghetti` (codebase-wide structural sweep) + `/dust` (generic cleanup) + `/test-strength-audit` (test-weakening regression) |
| **Post-coding** | `/ship` (build verify + version bump + commit + tag + push) + `/post-ship-audit` (retrospective) + `/latency-track` (HOT_PATH_CHANGELOG draft) |
| **Workflow** | `/handoff` (self-contained pickup prompt) + `/plan-draft` (scaffold future-oriented plan body) + `/sync-workspace` (mirror to workspace backup) |
| **Recurrence** | `/loop` (recurring task on interval) + `/schedule` (remote-agent cron) |

Audit-driven discipline: HIGH-RISK ships fire `/precoding-audit-gate` (SHAPE) + `/blindspot-scan` (IMPLEMENTATION-DETAIL) in parallel before coding. Per-ship cycle: audit → consult → update plan → implement → ship → postmortem. See `DESIGN_PHILOSOPHY.md` § 11 + § 11.5 + `DESIGN_SPECS/audit-driven-pre-coding-gate.md` + `DESIGN_SPECS/implementation-layer-blindspot-taxonomy.md`.

---

**End of CLAUDE.md.** Always-loaded orientation: Purpose + Hard Invariants (H1-H20) + Reference table + How-to discovery + Skill suite categories. Architectural detail + WHY context lives in `DOCS/DESIGN_PHILOSOPHY.md` (master settings portal). Operator preferences + sprint state + going-forward rule index live in `CLAUDE.local.md` (private overlay). Collaboration rules live in `memory/MEMORY.md`. Patterns live in `DESIGN_SPECS/`. Anti-patterns live in `DOCS/RECURRING_BUG_PATTERNS.md`. Each layer has ONE home; no duplication across layers.
