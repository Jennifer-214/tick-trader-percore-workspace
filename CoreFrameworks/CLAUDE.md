# Working in CoreFrameworks/ — engine-core surface orientation

> On-demand: loads when you read/edit a file in `CoreFrameworks/`. CONCATENATES with the always-loaded
> root `CLAUDE.md` (universal core) — this is the engine-core SLICE, not a replacement. Universal rules
> (H1–H21, priority gradients, collaboration norms) are already loaded from root; this carries the surface
> detail root used to hold. Architecture/concurrency/budget sections below moved here VERBATIM 2026-06-11
> (TECH_DEBT-163 context-aware loading). Edit this workspace file, not the engine symlink.

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

- Per-node strategy (`core_N_strategy=simple_dip|momentum|ema_cross|ml`)
- Per-node ML model (`core_N_model_path=...` or `core_N_model_dir=...`)
- Per-node risk (`core_N_risk_pct=...`)
- Per-node ConfidenceScorer (when STRATEGY_ML)
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

## Concurrency model summary

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

## Latency budgets

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

## Memory budgets

| Surface | Budget | Reason |
|---|---|---|
| Hot path working set | ≤L1d (32-64KB typical) | Stay cache-resident; eviction kills p99 |
| Per-node slow_state | ≤64KB | Comfortable L1d+L2; per-node isolation |
| Cross-thread cfg (seqlock cached) | ≤single cache line per param group | False-sharing prevention (H6) |
| SPSC ring depth | `Limits.hpp:MAX_RING_*` | Bounded; backpressure detectable |
| Order pool | `Limits.hpp:MAX_ORDERS` | Bounded; bitmap-packed (H1 no heap) |
| Per-node ML feature window | `Limits.hpp:ML_WINDOW_MAX` | Bounded ring buffer |
| Bitmap structures (portfolio / flags) | uint64_t typical | H14 — never C++ bitfield syntax |
| Stack frames on hot path | <few KB | No deep recursion / large stack-alloc |

L1d working-set discipline: hot path SHOULD fit in single core's L1d (32-64KB). Verify via perf counters when uncertain. → DESIGN_SPECS/data-disciplines/cache-line-discipline.md (Stage 2 DRAFT).

## Surface rules (load-bearing in CoreFrameworks/)

- **Hot path BRANCHLESS** for data-dependent dispatch (H7); p99 ≤500ns / slow ≤100μs (H8). Mask/cmov/table, never a data-dependent branch (Class 28 hand-wave is the anti-pattern).
- **OMS/drainer = single-writer funnel** (H3); per-fill cfg via **decision-time binding** (pre-resolve onto the in-flight object) — NEVER a scalar cfg-mirror field (Class 27).
- **Per-core cfg indexing:** `cfg.cores[slot]` (the outer per-core slot), NOT the ring-pop counter `i` (Class 26); respect global-vs-per-core reader scope (Class 25; UNINDEXED-GLOBAL is Class 26 sub-shape B).
- **Cross-thread multi-word reads:** `Money`/`Position` are 16B = 2 machine words → read via **seqlock or published snapshot**, never a bare load (TEARS). The OMS money cluster's torn-read class is the `.E.1` aggregator's job; reader-side discipline = `cross-thread-multiword-read-consistency-discipline.md`.
- **Money math = `Money`** (decimal) for prices/qtys/fees/balances; **features = `FPN_Binary<F>`**; crossings only at named `Money_ToBinary`/`Money_FromBinary` seams (H4). Price-diff gross P&L routes through `Money_FillGross` SSoT (D-190) — never open-code a 2-mul form.
- **`alignas(64)`** cross-thread fields (H6); explicit `int<N>_t _padding = 0` in byte-equiv structs (H12); `alignas(>16)` structs NEVER bare-malloc'd (H21 — aligned_alloc/new/arena).
- **Snapshot/wire identifiers** (SHARDED_SNAPSHOT_VERSION, persisted enum CODES) are append-only + immutable (H21 Knight-Capital) — tombstone, never renumber/reuse.
- **Changing a core struct's layout** (resize/reorder a field, or swap a field type — esp. `Money`/`Position`/`Order`/`CoreContext`/cfg structs) → run the **cascade check FIRST**; the transitive downstream impact is too big to hold in your head (the 16B flip cascaded `Money`→`OrderPreResolved`→`Order`/`Position`+their persist sites). `tools/gen_code_map.sh --composition <T>` (transitive containers) + `--byte-context <T>` (byte-sensitive wire/persist/memcmp sites) + `clang -Xclang -fdump-record-layouts <TU>` for exact offsets/cache-line spans (`pahole` chokes on the `<F>` templates). `check_struct_alignment.py` (c) ENFORCES that byte-serialized types stay size-pinned (`static_assert(sizeof(T)==N)`) → a silent layout change is a compile error, then bump the snapshot VERSION (H21). Full tool design + the deferred orphan-detector: `DESIGN_SPECS/meta-disciplines/struct-change-cascade-impact-tooling.md` (D-202).

## Tools for this surface (slice of `DOCS/TOOLS.md`)

- `check_per_node_registry_integrity.py` — PerCoreCfg X-macro integrity (H17) + Class 25/26 paired-access + UNINDEXED-GLOBAL detector (SKILL-WIRED).
- `check_money_gross_single_source.py` — D-190 gross-SSoT guard (pre-commit Check G/L): realized+unrealized price-diff gross MUST route through `Money_FillGross`.
- `check_struct_alignment.py` — (a) `alignas(>16)` vs bare malloc/calloc/realloc (Knight/H21) + (c) byte-serialization size-pin coverage: a type serialized via fwrite/fread/memcmp/SHA/HMAC must carry `static_assert(sizeof(T)==N)` (H9/H12 — silent layout change = compile error, not a wire break; D-202). Pre-commit Check K.
- `check_identifier_retirement.py` — snapshot/format VERSION + persisted enum CODE tombstone guard vs the golden ledger (H21; pre-commit Check H).
- `calls_graph_diff.sh` — strategy/regime orphan-diff; run to verify the hot path stayed UNTOUCHED after any CoreFrameworks change.
- `check_latency_path_conformance.py` — `.E.1.0` STATIC latency-path analyzer: disassembles the PRODUCTION hot (`ExecutionCore_Tick`) + slow (`RollingStats_Push`) paths + gates instruction-budget + **branch-classification {loop / rare-cold / data-dependent-warm = the H7/H20 meter}** + no-float(H4)/div/malloc/indirect/spill; asserts its own non-vacuity (Class-51 self-defense). Mechanizes `latency-path-discipline.md` + the hot/slow invariants. Sister to `check_struct_size_budget.py` (the derived-fact-budget framework). RUN after any hot/slow-path change (D-234/D-235/D-236).
- `check_reset_before_producer.py` — **a per-pass RESET must sit on the correct side of its PRODUCER** (Class 44 sub-B). `strategy_halt_reason = SHALT_OK` sat 59 lines BELOW the dispatcher that writes it, so 17 of 20 SHALT codes were unobservable from 2026-04-30 until D-421 — it compiled, passed every test, and silently discarded the producer's output. Fires at pre-commit **Check M2** on a staged `ControllerEventLoop.hpp` + as a HARD row in the doc sweep. Declarative `RULES`; source order inside one function, no CFG (PARTIAL by design). Note the two `halt_reason`/`strategy_halt_reason` resets look interchangeable and are not — both are reset-first, and the tool pins each.
- `scan_class_27_full.py` — full Class-27 (scalar cfg-mirror) scan (fired by `/bug-check`).

## Skills for this surface

- `/accounting-audit` — money / fee / commission / kill-switch / P&L / balance / backtest-accounting paths.
- `/hft-audit` — cache alignment · branchless · lock-free concurrency · fixed-point edge cases.
- `/dod-audit` — DESIGN_SPECS pattern application (bit-packing / X-macro / cache-line / branchless).
- `/trace-deps` — dependency-chain for OMS/drainer/registry changes before coding.

## Patterns + anti-patterns here

- DESIGN_SPECS: `concurrency-patterns/cross-thread-multiword-read-consistency-discipline.md` · `decision-time-data-binding-pattern.md` · `refactor-patterns/branchless-dispatch-discipline.md` · `data-disciplines/cache-line-discipline.md` · `framework-patterns/universal-cfg-field-registry-pattern.md`.
- RECURRING_BUG_PATTERNS: **Class 25** (per-core scope) · **Class 26** (per-core cfg slot index + UNINDEXED-GLOBAL) · **Class 27** (scalar cfg-mirror) · **Class 28** (branch hand-wave on SP/HP) · **Class 41** (raw `.v` encoding-blind compares).

## Reach for more

- Universal rules/invariants: root `CLAUDE.md` (already loaded) + `DOCS/DESIGN_PHILOSOPHY.md` § 2 (invariants) / § 3 (DOD) / § 4 (latency) / § 6 (concurrency).
- Hot-path discipline (required reading before per-tick code): `DOCS/STRATEGY_AND_CODING_RULES.md` + `plans/_cross-cutting/2026-05-06-latency-path-discipline.md`.
- OMS / kill-switch / snapshot / threading changes: `DOCS/CLAUDE_INVARIANTS.md`.
- Planning / audit / codification disciplines: the work-mode rule index (the work-mode skills auto-load it).
