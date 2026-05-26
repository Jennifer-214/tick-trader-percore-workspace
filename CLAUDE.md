# CLAUDE.md

Always-loaded architectural orientation for this codebase. Stays GENERAL — sprint state + going-forward rules + memory live elsewhere (see Reference docs below).

## Purpose

Claude assists with **planning + implementation of an HFT trading engine** in C++. The codebase prioritizes (in order): **latency** (sub-microsecond hot path) → **determinism** (cross-run / cross-binary / cross-locale byte equivalence) → **maintainability** (structural fix preferred when a bug class can recur) → **operator UX**.

When trade-offs conflict, name which wins + why per `DOCS/DESIGN_PHILOSOPHY.md` § 1. Default to deeper architectural option when the operator is engaged + the math favors it (per `feedback_overengineering_boundary_when_future_easier` + `feedback_plan_right_not_fast`).

For sprint state, going-forward rules, and operator-collaboration discipline, see `CLAUDE.local.md` (private overlay) + `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/MEMORY.md`.

## Design philosophy + priorities

Headline summary of design principles + priority gradients. Deep discussion + WHY context + worked examples lives in `DOCS/DESIGN_PHILOSOPHY.md` (master settings portal; 14 sections + § 11.5 meta-discipline registry). Load DESIGN_PHILOSOPHY when designing rather than implementing, or when a 1-liner here isn't enough — every principle below has an inline `→ § N` cross-ref to the deep-dive.

### End state (vision)

Continuously evolving open-source per-core sharded HFT trading platform; AGPL public repo; quality bar set by hedge-fund-visibility expectations. Trajectory:

- **Current** = v5.X professionalization phase. Codebase transitioned from MVP to professional infrastructure; framework-driven extensibility, audit-driven discipline, structural-fix-over-patch are the deliverables. Active sprint goal: *make the codebase more maintainable for future development* (current sprint state lives in `CLAUDE.local.md` § Current sprint state).
- **Near-term** = decoupled runtime/viewer architecture (`plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`). Engine runs headless as systemd service; multiple viewers attach concurrently; cmdline-invocable training; per-run dirs with tailable artifacts.
- **Long-horizon** = framework-driven addition of strategies/features/markets stays 1-row-in-registry. New ML features, new bandit algos, new regime variants, new symbols — all add via single registry row + framework auto-flow.

→ DESIGN_PHILOSOPHY § 1 (priority order + conflict resolution) + § 1.5 (framework discipline meta-principle).

### Core principle: Data-Oriented Design (DOD)

Layout determines performance. Layout by ACCESS PATTERN, not LOGICAL GROUPING. Functions consuming whole structs → fields grouped by call pattern (hot reads / hot writes / cold init / cross-thread). `alignas(64)` cross-thread fields (H6).

**Bit-packing ideal.** Hand-written `BITMAP_*` + `MBS_*` (multi-bit state) accessors over `uint{8,16,32,64}_t` storage — never C++ bitfield syntax (`name : N`). Layout/signedness/packing-order are implementation-defined, which conflicts with wire byte preservation + SIMD parity + memcmp identity (H9/H10/H12/H14).

**Cache-aware.** Hot-path + slow-path state SHOULD fit L1d (32-64KB typical). Working-set placement matters; cluster cohort-accessed fields adjacent. Cold-init can sprawl; hot loops cannot.

**False-sharing prevention.** Cross-thread fields written by one thread + read by another → `alignas(64)` padding to avoid cache-line ping-pong. Producer→drainer SPSC queues, slow→hot seqlock cfg → all aligned.

→ DESIGN_PHILOSOPHY § 3 (Data-oriented design family) + § 6 (Concurrency family — false-sharing discipline).
→ DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md (K-state encoding for K=2..16).
→ DESIGN_SPECS/refactor-patterns/bitmap-overflow-protection-discipline.md (mandatory static_assert for BITMAP_* paired counts).

### Priority gradients (prefer X over Y when both work)

When two options both compile + both run, the gradient resolves the choice. These are NOT absolute (Hard Invariants H1-H20 are absolute) — they're how to think about borderline trade-offs.

**Performance:**
- Branchless > branched for data-dependent dispatch on hot/slow/drainer/producer paths (H7 hot-path strict; H20 generalizes). Hand-wave "branch predictor handles it" is anti-pattern (Class 28). → § 4 (latency cost) + DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md.
- `FPN<F=64>` > `double` on accounting paths; never `float` on hot/slow path math (H4). → § 5 (determinism).
- Bit-packed slots > byte-per-bool (H14 + MBS_* encoding). Memory bandwidth + cache footprint compound.
- `alignas(64)` cross-thread + cluster by access pattern > flat struct (H6). → § 3.
- L1d-cache-resident hot-path state > out-of-cache scatter. Working-set discipline applies to per-core slow_state + hot ExecutionCore params.
- SIMD with bytewise-identical scalar fallback > SIMD-only (H10). → § 5.

**Maintenance:**
- Structural fix > one-time patch when bug class can recur. → § 7 + DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md.
- Framework-driven (X-macro registry + auto-flow) > ad-hoc per-instance code when recurrence foreseeable. → § 1.5 + DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md.
- Auto-flowing registry > manual N-site sync (H15-H19 codify mandatory registry discipline). → § 7.
- `tt::` type-trait dispatch > `reinterpret_cast` punning (H13). Class 23 closure. → DESIGN_SPECS/framework-patterns/type-trait-dispatch-via-tt-namespace.md.
- Compile-time enforcement (static_assert / CI Check) > runtime check / convention.
- Categorical triggers > hardcoded refs in always-loaded content (CLAUDE.md / CLAUDE.local.md / MEMORY.md / SKILL.md). → DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md.
- Boundary-stable refactor > wide cascade across ≥4 files.

**Determinism:**
- Wire byte preservation always for HMAC-signed bodies (H9). → § 5 + DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md.
- Single-source-of-truth emit (sidecar override per H18) > parallel mirror registry. Class 21 closure.
- Constant-iter math + branchless within reductions (H11).
- Locale pinning at emit (`tt::format_double_canonical`).

**Design discipline:**
- Plan-right > plan-fast. Planning IS the hard part; indecisiveness during planning is a feature. → memory/feedback_plan_right_not_fast.md.
- Future-oriented > current-convenience when easier-future trade-off sharp. → memory/feedback_auto_pick_future_oriented.md.
- Audit-driven > debug-driven. SHAPE audits (`/precoding-audit-gate`) + IMPLEMENTATION-DETAIL audits (`/blindspot-scan`) before coding HIGH-RISK ships. → § 11 + § 11.5 (M1-M4 meta-disciplines).
- Best-software > smallest-effort. Public AGPL + hedge-fund visibility = exacting quality bar. → memory/feedback_motivated_collaborator_for_caramel.md.
- Proportionate response > first-sufficient on audit findings. → memory/feedback_proportionate_response_to_audit_findings.md.
- 4-pillar self-audit before surfacing recommendations (DESIGN_SPECS check / anti-pattern check / operator-impact / novel-alternative). → memory/feedback_audit_own_proposals_with_same_rigor.md.

→ DESIGN_PHILOSOPHY § 11 (process discipline) + § 11.5 (meta-disciplines M1-M4) for the audit-driven framework + worked examples.

### Latency budgets

| Path | p50 | p99 | p99.99 | Source |
|---|---|---|---|---|
| Hot path tick → trade decision | ~100ns | **≤500ns** | ≤2μs | H8 (ship blocker if violated) |
| Hot path BG_Evaluate alone | <50ns | <200ns | — | per-gate budget within hot path |
| Slow path rebuild cycle | — | **≤100μs** | — | H8 (ship blocker if violated) |
| Drainer cycle (OMS_DrainSubmit + OrderManager_Tick) | <5μs | ≤10μs | — | per-tick drainer cadence |
| Producer fan_out per tick | <100ns | ≤200ns | — | per-tick parser+replicate budget |
| Async (Binance WS / DepthRecorder / Notify) | — | <100μs | — | non-trading-path tolerance |
| GUI frame budget | 16.7ms | — | — | 60Hz target (H3 thread isolation) |
| Boot warm-restart | <2s | ≤5s | — | recovery scenario (live-readiness) |
| Stamp emit (HMAC-signed) | — | <50μs | — | wire-format byte preservation gate |

Hot path is BRANCHLESS (H7); branch mispredicts cost 30-100ns real-world per `DESIGN_PHILOSOPHY.md` § 4 — eliminating them is the budget mechanism. → § 4 (latency cost framework).

### Memory budgets

| Surface | Budget | Reason |
|---|---|---|
| Hot path working set | ≤L1d (32-64KB typical) | Stay cache-resident; eviction kills p99 |
| Per-core slow_state | ≤64KB | Comfortable L1d+L2; per-core isolation |
| Cross-thread cfg (seqlock cached) | ≤single cache line per param group | False-sharing prevention (H6) |
| SPSC ring depth | `Limits.hpp:MAX_RING_*` | Bounded; backpressure detectable |
| Order pool | `Limits.hpp:MAX_ORDERS` | Bounded; bitmap-packed (H1 no heap) |
| Per-core ML feature window | `Limits.hpp:ML_WINDOW_MAX` | Bounded ring buffer |
| Bitmap structures (portfolio / flags) | uint64_t typical | H14 — never C++ bitfield syntax |
| Stack frames on hot path | <few KB | No deep recursion / large stack-alloc |

L1d working-set discipline: hot path SHOULD fit in single core's L1d (32-64KB). Verify via perf counters when uncertain. → DESIGN_SPECS/data-disciplines/cache-line-discipline.md (Stage 2 DRAFT).

### Concurrency model summary

Thread architecture:

```
PRODUCER (1)              DRAINER (1)         PER-CORE CONSUMERS (N=2..16)
─────────────             ──────────          ──────────────────────────────
Binance WS                OMS_DrainSubmit     SLOW thread (1 per core)
  ├─ parse tick    ──┐    OrderManager_Tick   ├─ EventLoop_UpdateRollingState
  ├─ ema_price    ──┤    DrainPostFill       ├─ Regime_Classify
  ├─ fan_out:      ──┘─→ SPSC ring          ├─ Strategy rebuild
  │   for c in N: │                          ├─ ExecutionCore_SetParameters
  │     push(c)   │                          │   (seqlock → HOT)
  └─ GUI publish  │                          ├─ TimeExitOneCore
                  │                          └─ TrailingSLRatchet
                  ↓
              SPSC ring → HOT thread (1 per core)
                          ├─ BG_Evaluate (branchless)
                          ├─ SG_Evaluate ×2
                          └─ push TradeEvent (rare branch)
```

**Sync primitives (H1-H3):**
- **SPSC rings:** producer↔consumer + slow↔hot params + post-fill events. Lock-free; bounded; align-padded.
- **Seqlock:** slow→hot cfg parameter handoff. No mutex per H3.
- **Atomic flags:** cross-thread state (kill_switch / recovery_until_us / flatten_pending). Acquire/release semantics.
- **`alignas(64)` discipline:** every cross-thread field gets cache-line padding (H6). Cluster by access pattern (hot reads / hot writes / cold init / cross-thread).

**Anti-patterns (NEVER):**
- `std::mutex` / `condition_variable` / `sleep_for` / `pthread_rwlock` anywhere (H3)
- Pointer-sharing between GUI thread and HP/SP threads (file-mediated + reload-signal instead)
- C++ bitfield syntax in cross-thread structs (H14 — layout/signedness/packing-order implementation-defined)

**False-sharing prevention:** cross-thread struct fields padded to cache-line boundaries; producer-written + consumer-read fields in separate cache lines. → DESIGN_SPECS/concurrency-patterns/concurrency-model-summary.md + DESIGN_SPECS/data-disciplines/cache-line-discipline.md (Stage 2 DRAFT).

### Doc layer separation

| Layer | Lives in | Auto-loaded? | Content type |
|---|---|---|---|
| Orientation + invariants + priority headlines | `CLAUDE.md` (this file) | YES | TIMELESS — guidelines + index |
| Deep discussion + WHY + worked examples | `DOCS/DESIGN_PHILOSOPHY.md` | NO (load on demand) | TIMELESS — depth |
| Reusable pattern bodies | `DESIGN_SPECS/<name>.md` (80+) | NO | TIMELESS — recipes |
| Anti-pattern instances + detection | `DOCS/RECURRING_BUG_PATTERNS.md` | NO (loaded by `/bug-check`) | TIMELESS — catalog |
| Operator-collaboration rules | `memory/` (via MEMORY.md index) | YES | TIMELESS — preferences |
| Sprint state + going-forward rule index | `CLAUDE.local.md` (private overlay) | YES | TIMELESS index + EPHEMERAL pointer to in-flight |
| In-flight ship plans + handoffs | `plans/<sprint>/` (gitignored) | NO (load on demand) | EPHEMERAL — current work |
| Auto-write ledgers | `DOCS/TECH_DEBT.md` + `PARITY_ISSUES.md` + `FEATURE_LOOKUP.md` | NO | EPHEMERAL — accumulating |

**Rule:** Always-loaded docs (`CLAUDE.md` + `CLAUDE.local.md` + `MEMORY.md` + `SKILL.md` files) = GUIDELINES + INDEX (timeless; "how to think"). On-demand docs (plans/, ledgers, handoffs) = IN-FLIGHT WORK (ephemeral; "what to do this sprint"). NEVER put TODO content or sprint-version-specific phrasing in always-loaded docs — track in TECH_DEBT or plans instead. Drift sentinels: "queued as v5.X.Y sub-ship", "(NEW post-v5.X.Y)", specific TECH_DEBT-NNN in trigger bodies that should be categorical pattern triggers.

→ DESIGN_PHILOSOPHY § 0 (purpose hierarchy) + § 13 (cross-reference index).
→ DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md (the discipline).

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
| **H15** | **Every X-macro registry in the codebase MUST have a row in `FOREACH_REGISTRY` meta-registry** at `CoreFrameworks/MetaRegistry.hpp` (codified `.F.4d` 2026-05-16). Adding a new registry without enrollment fails CI Check `test_meta_registry_coverage`. Closes meta-Class-18 (added registry but forgot to document). See `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md`. |
| H16 | (Structural detail; full discussion in `DOCS/STRATEGY_AND_CODING_RULES.md` § H16 private overlay.) Every `CfgFieldDescriptor::MetadataFlag` bit MUST have a derived filter row in `FOREACH_DERIVED_FILTER` OR a documented exemption with rationale. CI Check `test_metadata_bit_to_derived_filter_coverage` enforces. Codified `.F.4d` 2026-05-16. |
| H17 | (Structural detail; full discussion in `DOCS/STRATEGY_AND_CODING_RULES.md` § H17 private overlay.) `ControllerConfig<F>` cfg struct fields auto-generated from `FOREACH_CFG_FIELD`; NO manual cfg field declarations. `PerCoreCfg<F>` body = X-macro only (CI Check 2 since `.F.4c`). Codified `.F.4d` 2026-05-16. |
| **H18** | **Custom-semantics for registry auto-flows via SIDECAR OVERRIDE pattern** (sparse `FOREACH_<DOMAIN>_OVERRIDE` indexed by parent's `FIELD_IDX`); NEVER parallel wide-variant registries (Class 21 anti-pattern at auto-flow surface). STRONG initially; **HARD after 2nd cohort application** per pattern-codification-lifecycle.md. Codified `.F.4d` 2026-05-16 (1st canonical: XGBoost drift override cohort, 5 rows in `FOREACH_DRIFT_OVERRIDE`). See `DESIGN_SPECS/framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md`. |
| **H19** | **Every `FOREACH_REGISTRY` row with LEVEL > 0 (meta-registry) MUST declare a valid PARENT** (the registry it manages). Topology discipline; CI Check `test_meta_registry_topology` enforces (Level 0 = standalone data registries; Level 1 = meta-registries managing cohorts; Level 2 = top-level `FOREACH_REGISTRY` itself). Codified `.F.4d` 2026-05-16. See `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md`. |
| **H20** | **Branchless preferred for SP/HP data-dependent dispatch EVEN WHEN NOMINALLY SLOWER** (added v5.15.5.F.4c.3 WIP2d-1.B.0d). Mask code / fn pointer tables / cmov / mask-select / dummy-redirect can be optimized later (better instruction selection, vectorization, prefetch hints). Branch mispredicts CANNOT be optimized (hardware cost; 30-100ns real-world per `DESIGN_PHILOSOPHY.md` § 4 updated). For a determinism-prioritizing system (HFT premise), variance from branches is the bigger cost. Sister to H7 (hot path strict); H20 generalizes the discipline to SP + drainer + producer-fan-out. Exceptions per decision matrix in `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md` (boot-time-only / `__builtin_expect`-rare / `if constexpr` compile-time / genuine binary predicate with no alternative computation). Closes Class 28. |

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

Test split is queued as a focused effort (3118 tests at risk warrants
rollback anchor + dedicated ship); tracking lives in TECH_DEBT (sister
TECH_DEBT-029 covers the source-side analog for header/non-test files;
TECH_DEBT-114 tracks this specific test split).

### File-size split discipline (generalized; added 2026-05-18)

Test file size rule above generalizes to ALL files. Thresholds per
file type at `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md`:

| File type | Hard threshold |
|---|---|
| Always-loaded docs (CLAUDE.md / CLAUDE.local.md / MEMORY.md) | 600 lines |
| Tests | 5000 lines / 100 sections (above) |
| Source headers (`.hpp`) | 1500 lines (TECH_DEBT-029 sister) |
| Source bodies (`.cpp`) | 2000 lines |
| Ledger files (TECH_DEBT / RBP / PARITY / FEATURE / HOT_PATH / LANDMINES) | 2000 lines |
| SKILL.md | 1500 lines |
| DESIGN_SPECS | 1200 lines |
| Plan body docs | 1200 lines (use `<plan-name>-examples.md` sidecar) |
| Memory rules | 500 lines (terseness expected) |

**Split + index pattern:** at threshold, split into sub-files; convert
original to INDEX file with `splits_into:` frontmatter; sub-files get
`parent_index:` frontmatter; `rg`-sweep all external cross-refs to
point at INDEX (not sub-files).

Specific mega-file splits queued: TECH_DEBT-116 (TECH_DEBT.md @ 2013
lines) / TECH_DEBT-117 (RECURRING_BUG_PATTERNS.md @ 2198 lines) /
TECH_DEBT-118 (/readiness SKILL.md @ 1674 lines). Each warrants
dedicated sub-ship with rollback anchor + sed-based cross-ref sweep.

## How to find anything (search guide)

Doc system is institutional memory + type-tag driven + greppable. Retrieval recipes below. Tag vocabulary lives at `DESIGN_SPECS/meta-disciplines/doc-tag-vocabulary.md` (CONCERN + SURFACE + LIFECYCLE axes); frontmatter discipline at `DESIGN_SPECS/meta-disciplines/doc-frontmatter-convention.md`.

### By type
```
rg "^type: refactor-pattern" DESIGN_SPECS/    # refactor patterns
rg "^type: framework-pattern" DESIGN_SPECS/   # framework infrastructure
rg "^type: audit-methodology" DESIGN_SPECS/   # audit shapes (M1-Mn family)
rg "^type: data-discipline" DESIGN_SPECS/     # DOD / cache / alignment specs
rg "^type: concurrency-pattern" DESIGN_SPECS/ # thread / sync / SPSC / seqlock
rg "^type: wire-format-pattern" DESIGN_SPECS/ # byte preservation / HMAC / locale
rg "^type: meta-discipline" DESIGN_SPECS/     # audit-methodology-gap (M-codes)
rg "^type: plan-template" DESIGN_SPECS/       # MASTER / sub-plan / handoff / postmortem
rg "^type: ledger-template" DESIGN_SPECS/     # TECH_DEBT / PARITY / FEATURE entry shape
```

### By tag (concern axis — what doc is ABOUT)
```
rg "^tags:.*\bframework-discipline\b"
rg "^tags:.*\baudit-methodology\b"
rg "^tags:.*\bdata-oriented-design\b"
rg "^tags:.*\bconcurrency\b"
rg "^tags:.*\bwire-format\b"
rg "^tags:.*\bdoc-discipline\b"
```

### By surface (what doc TOUCHES)
```
rg "^surface:.*\bhot-path\b"        # ExecutionCore / BG_Evaluate / SG_Evaluate
rg "^surface:.*\bslow-path\b"       # slow_state / Regime / RebuildOneCore
rg "^surface:.*\boms-drainer\b"     # OMS_DrainSubmit / OrderManager_Tick
rg "^surface:.*\bregistry\b"        # X-macro registries / FOREACH_*
rg "^surface:.*\bml-inference\b"    # model predict / scaler / ConfidenceScorer
rg "^surface:.*\bwire-format\b"     # HMAC bodies / stamps / snapshots
rg "^surface:.*\blive-trading\b"    # kill switch / paper-test / circuit breaker
rg "^surface:.*\bboot-time\b"       # warm-restart / recovery / boot-gate
```

### By catalog ID (use word-boundary `\b` for short IDs)
```
rg "\bClass 18\b"                   # anti-pattern Class N
rg "\bH13\b"                        # hard invariant H N
rg "\bM4\b"                         # meta-discipline M N
rg "TECH_DEBT-112"                  # ledger entry
rg "PARITY-009"                     # parity ledger entry
```

### By severity / status (ledger queries)
```
rg "^severity: high" DOCS/TECH_DEBT.md      # high-severity deferrals
rg "^status: open" DOCS/TECH_DEBT.md        # open TECH_DEBT
rg "^status: in-flight" DOCS/TECH_DEBT.md   # being addressed this sprint
rg "^surface_tags:.*\bregistry\b" DOCS/TECH_DEBT.md
```

### By lifecycle stage (promotion-readiness)
```
rg "^stage: 2-draft" DESIGN_SPECS/          # awaiting first canonical reference
rg "^stage: 3-first-canonical" DESIGN_SPECS/ # first canonical landed
rg "^stage: 4-cohort" DESIGN_SPECS/         # ≥2 applications; promotion candidate
rg "^stage: 5-claude-md" DESIGN_SPECS/      # promoted to CLAUDE.md item
rg "^stage: 6-cadence-locked" DESIGN_SPECS/ # periodic audit + CI enforcement
```

### By cross-ref (related docs)
```
rg "sister_specs:.*\bcategorical-triggers-in-always-loaded-docs\b"
rg "sister_docs:.*\b<doc-name>\b"
rg "applies_at_skills:.*\b/readiness\b"
```

### Helper skills (when grep is awkward)
- `/find <natural language>` (Stage 1 problem — skill queued at `.C` candidate ship) — fuzzy search over metadata
- `/doc-create <type>` (queued) — type-aware doc scaffolding using current canonical template
- `/index-rebuild` (queued) — regenerate CLAUDE.md tables + READMEs from frontmatter
- `/metadata-audit` (queued) — periodic audit: missing frontmatter / undefined tags / broken sister-doc links / Stage 2 DRAFTs older than N sprints

### Filesystem layout (where each type lives)

| Doc type | Location | Naming convention |
|---|---|---|
| Pattern bodies | `DESIGN_SPECS/<name>.md` | kebab-case + `<concept>-<discipline>` |
| Plan bodies | `plans/<sprint>/subplans/<YYYY-MM-DD>-<version>-<name>.md` | date + version + name |
| Handoffs | `plans/<sprint>/handoffs/<YYYY-MM-DD>-<version>-<purpose>-handoff.md` | date + version + purpose |
| Postmortems | `plans/<sprint>/postmortems/<YYYY-MM-DD>-<version>-postmortem.md` | date + version |
| Audit reports | `plans/<sprint>/plan_checks/<date>-<audit>-<scope>.md` | date + audit-name + scope |
| Sprint MASTER | `plans/<sprint>/MASTER.md` | (singular per sprint) |
| Memory rules | `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/<name>.md` | `feedback_*` / `user_*` / `project_*` / `reference_*` |
| Always-loaded orientation | `CLAUDE.md` + `CLAUDE.local.md` + `MEMORY.md` | singular files |
| On-demand orientation | `DOCS/CLAUDE_*.md` + `DOCS/DESIGN_PHILOSOPHY.md` | per concern |
| Auto-write ledgers | `DOCS/TECH_DEBT.md` + `PARITY_ISSUES.md` + `FEATURE_LOOKUP.md` + `HOT_PATH_CHANGELOG.md` + `LANDMINES.md` | singular per concern |
| Bug class catalog | `DOCS/RECURRING_BUG_PATTERNS.md` | singular |

Read this section once + you know how to find ANYTHING in the doc system without prior knowledge of "where stuff is."

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
| Add a cfg field | 1 row in master registry at `CoreFrameworks/CfgFieldRegistry.hpp` (parser + GUI render + tooltip + per-core override emission auto-flow per framework state — see `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md` for current capabilities) |
| Add a STAMP_BOUND cfg field | Set `STAMP_BOUND_CFG_DERIVED` bit in master registry row's metadata column (drift check + Layer 5b hash + wire emit auto-flow per `DESIGN_SPECS/framework-patterns/metadata-bit-driven-derived-filter-framework.md`) |
| Add a new derived filter (metadata-bit cohort) | 1 row in `FOREACH_DERIVED_FILTER` (framework auto-flow per `DESIGN_SPECS/framework-patterns/metadata-bit-driven-derived-filter-framework.md`) |
| Add an ML feature | `ML_Headers/FeatureRegistry.hpp` + `DOCS/CLAUDE_ML_INVARIANTS.md` |
| Add a SHALT code / halt reason / regime / strategy / bandit algo | Registry table per X-macro pattern (`DESIGN_PHILOSOPHY.md` § 7 + `DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md`) |
| Add a stateful GUI panel | `DOCS/CLAUDE_INTEGRATION.md` § "GUI panels" + display↔execution invariant check |
| Plan a non-trivial change | `/readiness` skill + `DOCS/CLAUDE_REVIEW.md` checklist + new plan body uses `DESIGN_SPECS/plan-templates/future-oriented-plan-template.md` |
| Audit a plan before coding | `/precoding-audit-gate` (orchestrator) → SHAPE audits in parallel + (`/blindspot-scan` if struct-gen / type unification / cross-registry consumer / wire-format ordering migration) |
| Audit existing code for anti-patterns | `/bug-check` (against RECURRING_BUG_PATTERNS classes) + `/dod-audit` (against DESIGN_SPECS catalog) + `/anti-spaghetti` (codebase-wide structural sweep) |
| Verify plan body code samples compile (Class 14 fabrication catch) | `python3 tools/check_plan_body_symbol_existence.py <plan>.md` — B-Plus CI tool; runs as pre-commit hook (install via `tools/install-git-hooks.sh`); /readiness Check 32 invokes |
| Verify decisions/memories/skills made this session got propagated | `/capture-audit` — mechanical drift check (~30 sec); 10 checks (MEMORY.md sync + plan body frontmatter + decision-log existence + sentinel matching + handoff currency + Stage 6 candidates + DESIGN_SPECS promotion + skill→CLAUDE.md linkage + memory→DESIGN_SPECS sister + going-forward-rule currency); runs pre-commit via /sync-workspace + pre-handoff via /handoff |
| Track a new bug class | Add to `DOCS/RECURRING_BUG_PATTERNS.md` (auto-included in `/bug-check`); include "False-positive surface" subsection per M3 discipline |
| Track a new meta-discipline (audit-methodology gap) | Codify per `DESIGN_PHILOSOPHY.md` § 11.5 procedure (NEW DESIGN_SPEC + skill amendment + `/readiness` Check + memory + CI tool if mechanical) |
| Ship a sub-ship | `/ship` skill (build verify + version bump + commit + tag + push) |
| Generate handoff prompt for fresh context | `/handoff` skill |

## Skill suite (audit-driven discipline)

Skills group by concern. Read each skill's `claude-skills/<name>/SKILL.md` for invocation details.

| Concern | Skills |
|---|---|
| **Pre-coding plan verification** | `/precoding-audit-gate` + `/readiness` |
| **SHAPE audits (design-layer)** | `/dod-audit` + `/merge-scan` + `/parity-check` + `/trace-deps` |
| **IMPLEMENTATION-DETAIL audits** | `/blindspot-scan` |
| **DOMAIN audits** | `/accounting-audit` + `/hft-audit` + `/ml-audit` + `/registry-fit-audit` |
| **Anti-pattern scans** | `/anti-spaghetti` + `/bug-check` + `/dead-code-trace` + `/dust` + `/metadata-audit` + `/test-strength-audit` |
| **Post-coding** | `/latency-track` + `/post-ship-audit` + `/ship` |
| **Workflow** | `/dependency-chain-trace` + `/find` + `/finding-analyzer` + `/foxlib-promotion` + `/handoff` + `/index-rebuild` + `/patch-planner` + `/plan-check` + `/plan-context-sweep` + `/sync-models` + `/sync-workspace` |
| **Capture + handoff discipline (M7 enforcement)** | `/capture-audit` (mechanical drift check — MEMORY.md sync / plan frontmatter / decision-log / sentinel matching / handoff currency / Stage 6 candidates / skill→CLAUDE.md linkage; runs as pre-commit + pre-handoff gate) + `/accept-handoff` (RECEIVER-side; loads handoff + cited files + runs /capture-audit + /readiness + recreates TaskList + outputs PICKUP-READY + concrete next action — ONE COMMAND for fresh-session pickup) + `/close-session` (SENDER-side meta-orchestrator; fires /capture-audit + operator triage + re-fires /capture-audit clean + /handoff + /sync-workspace + final close-out report — ONE COMMAND for session-close ritual; closes the "operator-pushback caught codification gap" failure mode per M7 structural enforcement) |
| **Scaffolding** | `/doc-create` + `/plan-draft` + `/strategy-template` |

Audit-driven discipline: HIGH-RISK ships fire `/precoding-audit-gate` (SHAPE) + `/blindspot-scan` (IMPLEMENTATION-DETAIL) in parallel before coding. Per-ship cycle: audit → consult → update plan → implement → ship → postmortem. See `DESIGN_PHILOSOPHY.md` § 11 + § 11.5 + `DESIGN_SPECS/audit-methodologies/audit-driven-pre-coding-gate.md` + `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md`.

---

**End of CLAUDE.md.** Always-loaded orientation: Purpose + Hard Invariants (H1-H20) + Reference table + How-to discovery + Skill suite categories. Architectural detail + WHY context lives in `DOCS/DESIGN_PHILOSOPHY.md` (master settings portal). Operator preferences + sprint state + going-forward rule index live in `CLAUDE.local.md` (private overlay). Collaboration rules live in `memory/MEMORY.md`. Patterns live in `DESIGN_SPECS/`. Anti-patterns live in `DOCS/RECURRING_BUG_PATTERNS.md`. Each layer has ONE home; no duplication across layers.
