# Deferred Items Log (v5.11 sprint)

Tracking everything we've explicitly chosen NOT to ship in the current
sprint, with the deferral rationale and the trigger conditions for
revisiting.

This file is gitignored (private) — workspace-backed via the
`plans/` symlink convention.

---

## v5.11.45 — XGBoost + libgomp + pthread parallelism (LANDMINE)

**Status:** Default flipped to forced-serial (`cfg.multi_horizon_max_threads = 1`). Parallel mode opt-in only.

**Symptom:** SIGSEGV in `RowsWiseBuildHistKernel` / `PredValueByOneTree` inside `libgomp::GOMP_parallel`. Hits during fold training in WF or during prediction. Two operator reports during v5.11.41-44 testing on 2026-05-07.

**Root cause:** XGBoost's libgomp internal state races across pthread workers even when each pthread calls `omp_set_num_threads(1)`. Team-allocation cache in libgomp uses process-global state. v5.11.44's per-pthread cap was insufficient.

**Why we didn't permanently fix it:**
- The clean fix: `setenv("OMP_NUM_THREADS", "1", 1)` at process start in `foxml_suite.cpp:main()` and engine binaries' main(). Sets libgomp's global default once before any pthreads exist; all subsequent threads inherit it. No per-thread races.
- Trade-off: forces XGBoost to use 1 thread for ALL training, including serial-mode Train Model which currently uses `cfg.xgb_train_nthread = 4`. Net effect: serial training 4x slower.
- For the operator's workflow (train rarely, paper-test for hours), this is a NET LOSS — losing 4x on common case to gain 3x on rare case.

**Re-trigger conditions:**
- Operator finds they actually NEED Multi-Horizon parallelism in their workflow (e.g. retraining 8+ horizons frequently). Then the 4x serial slowdown is worth the 8x parallel speedup.
- Process-level parallelism (shell-script that spawns N foxml_suite processes for N horizons) is enough — each process is independent, no libgomp interaction. Cumbersome but parity-safe + keeps the 4-thread serial XGBoost.
- Future XGBoost release fixes their libgomp pthread interaction. Then we can simply re-enable parallel default.

**See also:** `CLAUDE.local.md` "Known landmine" section for the full forensic write-up.

## v5.11.46 candidate — Collect Features per-file parallelism

**Original scope (v5.11.45 plan):** add `cfg.csv_load_workers` opt-in to spawn N pthreads, each processing one CSV file independently. Per-day file workflow → ~Nx wall-time speedup.

**Why deferred:** scope estimation error. I estimated 1-1.5h; actually 3-4h refactor of `BacktestSharded_Run` (lines 102-2000 area). Cross-file shared state: per-core engine state (RollingStats, regime, flow), `total_processed`, `feature_matrix` write position, backtest stats (cumulative wins/losses), `prev_file_last_ts`. Per-file parallelism requires:
1. Per-thread copies of `cores[]` state
2. Per-thread feature_matrix slices (pre-sized from file_tick_counts estimate)
3. Per-thread backtest stats accumulators
4. Post-join merge in file order (concat feature_matrix, sum stats)

Risk: BacktestSharded_Run is load-bearing for both backtest stats AND feature collection. Bug there could hit other workflows (Run Backtest, Run WF, Run Full Validation).

**Re-trigger conditions:**
- Operator runs Collect Features and finds it's actually too slow (>10 min per run, blocks iteration loop).
- Multi-day datasets with 10+ files (worst case for serial path).

**Effort:** 3-4h with proper /readiness + /parity-check given the load-bearing nature.

## v5.11.45 (also deferred from this ship) — NumPy-style broadcast

**Original scope:** generalize the broadcast-or-match rule. Currently anchors on horizon_count: TP/SL must be 1 (broadcast) or N (positional). NumPy-style would let effective N = max(tp_count, sl_count, horizon_count). Enables "3 TP, 1 SL, 1 horizon" as a TP-sweep.

**Why deferred:** operator said "this requires way more work than i thought" — they wanted simpler UI consolidation instead. Current rule handles their common workflow (3 horizons + 3 TP + 3 SL positional, OR single TP+SL broadcast across N horizons).

**Re-trigger conditions:**
- Operator workflow evolves to "TP sweep at fixed horizon" or "SL sweep at fixed TP" — then broadcasting becomes valuable.

---

## v5.11.5.C — MPSC drain queue replacing N×SPSC fan-in

**Original scope:** master plan v5.11.5 item 2 — replace
`OMS_DrainSubmit`'s 16×SPSC scan with a single MPSC queue. O(1)
arrival handling; no per-core empty-queue scans.

**Deferred to:** when profiling shows the empty-poll overhead is
load-bearing (probably never, on the current architecture).

**Why deferred:**
- N=16 SPSCRing_TryPop attempts per drain cycle ≈ ~80ns worst case
  (branch predictor reduces empty-poll cost to near-zero).
- Drainer thread cadence is poll_interval-driven (default 100 ticks),
  so the cumulative cost is microsecond-scale per second.
- Implementing a correct lock-free MPSC (Vyukov bounded queue or
  Michael-Scott) is ~200 LOC + 10+ tests + careful CAS reasoning.
  Risk vs reward is unfavorable for a sub-100ns drainer win.
- The hot path (BG_Evaluate / SG_Evaluate) is unaffected by drainer
  topology.

**Re-trigger condition:** profiling on a co-located deployment shows
drainer-thread p99 is the order-submit bottleneck AND the empty-poll
overhead is the dominant component within that.

**Effort estimate when re-triggered:** ~1-2 days, with explicit MPSC
correctness tests under N=4 producers (per master plan tests +8
scope).

---

## v5.11.8 — ML AOT compile (Treelite)

**Original scope:** master plan v5.11.8. Treelite-style transpiler
emits compiled C++ for trained XGBoost/LightGBM trees. Brings
single-row inference from ~1-5μs (XGBoost C API) down to <100ns.

**Status:** DEFERRED at v5.11 sprint close. Master plan flagged it as
SPECULATIVE up front.

**Why deferred:**
- ML inference happens on the SLOW path (every poll_interval ticks),
  not the hot path. Slow-path is already 50-150 μs avg per cycle.
- Saving 1-5 μs on the inference component is ~2-5% of slow-path —
  real but not load-bearing for a non-colo / public-WS engine.
- Adds dependency complexity: Treelite version coupling, AVX-512
  codegen variability, stamp body schema bump (`aot_compiled_sha256`
  field).
- Master plan flags it as speculative + "defer if v5.11 cumulative
  effort exceeds 3 weeks." We've been under 3 weeks but the
  speculative tag stands.

**Re-trigger condition:**
- ML strategy becomes the dominant trading mode (vs current
  AUTO/regime-gated strategies where ML fires only sometimes).
- Profiling shows XGBoost C API inference is the slow-path
  bottleneck (currently it's not — slow-path p99 is OS-bound at
  ~1ms).
- Operator targets sub-microsecond inference (FPGA-class).

**Effort estimate when re-triggered:** 2-3 days. Treelite integration
(~1 day) + stamp body extension via Surface G pattern (~30 min) +
engine load path with fallback (~half day) + train-serve parity test
(~half day).

---

## v5.11.9 — Carryover backlog items (status update 2026-05-08)

**Items SHIPPED in the late-night close:**
- ✓ `OPERATOR_QUICKSTART.md` → in-place rewrite of `DOCS/QUICKSTART.md`
  (commit `6059278`). Stale 100-line doc replaced with 286-line current
  onboarding doc covering build / first paper run / GUI reading /
  tuning / strategy authoring / backtest / going live / troubleshooting.
- ✓ GUI UX (PERM_OFF refinement + font scale slider, v5.11.10).

**Items still DEFERRED (operator preference 2026-05-08):**

### #5 — Feature mask cfg per-core (4-5h, parity-critical)

Spec: `plans/2026-05-08-v5.11-deferred-items.md` #5. Cfg field
`feature_mask_<core_id>` (uint64_t bitmap). Features_PackAll checks
mask before each FOREACH_FEATURE compute fn. Stamp body extension
`feature_mask` + 3-tier strict-mode load-time check.

**Why deferred:** parity-critical. Half-shipping it (cfg field
without stamp binding + 3-tier strict-mode) leaves a silent ML
input-drift hazard. Operator prefers a focused future session where
the full parity-safe version ships in one go vs a partial cut.

**Re-trigger:** when an ML ablation study workflow becomes
load-bearing (training a model with feature subset, comparing
generalization vs full feature set).

### #7 — Scaler comparison tool (2h)

Spec: `plans/2026-05-08-v5.11-deferred-items.md` #7. CLI
`tools/compare_scalers.sh <a.scaler> <b.scaler>`. Loads both via
FeatureStandardizer_Load, reports per-feature mean/stddev delta,
flags > 50% change as potential regime shift.

**Why deferred:** lowest risk + clean ship, but operator chose
to call the night rather than push past 6h of session. Trivial
re-pickup; the diagnostic value emerges only when investigating
a scaler-drift incident.

**Re-trigger:** first time an operator needs to investigate why a
new scaler reads differently than the previous one (regime shift
detection).

### #18 — RFV scaler binding (TBD scope)

Original spec mentions only "TBD" — needs investigation before
implementation. Likely requires understanding how RFV (recursive
feature value? ranked-feature-value?) interacts with the existing
FeatureStandardizer Q32 sidecar binding (v5.9.3a).

**Why deferred:** scope unclear; investigation is the first step,
not the implementation.

**Re-trigger:** when RFV becomes a load-bearing model type beyond
ad-hoc experimentation.

### Test file split (controller_test.cpp 15.5k → 4 files)

Original spec: split by domain (portfolio/oms, regime/strategies,
ml/parity, extensibility). ~4h mechanical surgery, risks breaking
1772 tests.

**Why deferred:** operator explicitly cut from scope (2026-05-08
"we don't have to do the test split"). High effort, internal-dev-
hygiene only, minimal user-visible value.

**Re-trigger:** when controller_test.cpp's compile time becomes
a development-iteration bottleneck (currently ~10s, not painful).

---

## Original v5.11.9 entry follows for reference

**Original scope:** master plan v5.11.9. Quality-of-life items from
the existing deferred-items doc:
- #5 feature mask cfg per-core (~3-4h)
- #7 scaler comparison tool (~2h)
- #18 RFV scaler binding (TBD)
- Doc gap: `OPERATOR_QUICKSTART.md` (~3-4h)
- Test file split (`controller_test.cpp` ~12k lines → 4 files; ~2-3h)

**Status:** ALL DEFERRED at v5.11 sprint close.

**Why deferred:**
- Quality-of-life, not optimization — none affect engineering
  correctness.
- All items have been on backlog for at least one sprint cycle.
- The v5.11 sprint focus was structural + performance; v5.11.9
  items are operator-workflow QoL.

**Re-trigger conditions** (per item):
- Feature mask cfg: when an operator wants per-core feature
  selection without rebuilding.
- Scaler comparison tool: when investigating a scaler-drift
  incident on a specific deployment.
- RFV scaler binding: when RFV becomes a load-bearing model
  type beyond ad-hoc experiments.
- OPERATOR_QUICKSTART.md: when a new operator joins or open-source
  uptake demands it.
- Test file split: when controller_test.cpp's compile time
  becomes a development-iteration bottleneck (currently ~10s,
  not painful).

---

## Multi-exchange parser pattern (2026-05-07 decision)

**Status:** ARCHITECTURALLY DEFERRED. Decision pending the second-
exchange ship.

**Context:** when reviewing simdjson vs strstr+from_chars during
v5.11.4.D, operator pushed back on "ingestion is a place where branches
aren't acceptable." Investigated three approaches:

  1. **simdjson with strict-typed accessors** — ~+200ns / parse, ~5-10
     branches per field. Industry standard, multi-exchange-friendly.
  2. **Hand-rolled branchless parser per exchange** — ~300-500 LOC per
     exchange, fragile against schema changes, maximum branchlessness.
     Right answer for FPGA / kernel-bypass / sub-μs target.
  3. **Stay with strstr+from_chars** — already locale-immune via
     v5.11.4.A. Glibc-SIMD strstr is internally vectorized. Branches
     limited to error-handling at field boundaries (~3-4 per message).

**Decision:** stay with #3 for the current single-exchange (Binance)
scope. simdjson amalgamation was vendored to vendor/simdjson/ but
NOT wired into CMakeLists.txt — leaving it on disk for if/when
multi-exchange work re-triggers this decision.

**Why deferred:**
- Branch geometry of the producer thread is dominated by the kernel
  + TLS layer (5-15μs of inherent branchiness). Adding 5-10 more
  in the parser is ~0.1-0.2% of total. Architectural floor isn't
  the parser; it's `SSL_read`.
- For non-colo target, parser branchiness is irrelevant.
- For multi-exchange, the second-exchange ship is the right time
  to choose simdjson vs hand-rolled — at that point the operator
  has concrete data on whether they're targeting FPGA-class latency
  or comfortable middle-tier.

**Re-trigger condition:** start of multi-exchange work (adding the
second exchange). Re-evaluate options 1 vs 2 in light of operator's
deployment target at that time.

**Architectural recommendation when re-triggered:**
- If target is non-colo public-WS (current trajectory): option 1
  (simdjson with strict-typed accessors). Vendor is already on
  disk. ~2 days to wire + convert 3 parsers.
- If target is colo + io_uring + FPGA-class latency: option 2
  (hand-rolled branchless per exchange). 1-2 weeks per exchange.
  Re-architect to binary protocol where exchange supports it
  (Binance has FIX 4.4 for some endpoints).

**What "branchless ingestion" actually requires** (for completeness):
- Replace `SSL_read` with kernel-bypass TCP/TLS (DPDK, Solarflare
  OpenOnload). Eliminates the 5-15μs kernel/TLS branchiness.
- Replace JSON entirely with binary protocol where possible (FIX
  4.4 for orders, custom binary for market data).
- Schema-typed extraction with pre-known field offsets (no parse,
  just `memcpy(&field, frame + OFFSET, sizeof(field))`).
- This is v6+ architecture; out of v5.11 scope.

---

## v5.11.4.B — simdjson on all 3 parsers (full rewrite)

**Original scope:** master plan v5.11.4 item 1 — simdjson for
binance_parse_trade + ud_parse_execution_report +
Reconcile_ParseOpenOrders. Single-pass O(N) tokenize replacing the
current O(N×K) strstr scans.

**Deferred to:** when the SECOND exchange is added (Coinbase / Kraken /
Bybit / dYdX / hyperliquid).

**Why deferred:**
- For Binance flat trade messages (3-5 fields, ~200B), simdjson's
  amortized win over glibc-SIMD-accelerated strstr is marginal at best
  and adds ~+200ns producer-thread latency per WS tick.
- For tick-to-trade end-to-end, that 200ns is ~1-3% of the producer
  pipeline (which is dominated by kernel SSL_read at 5-15μs).
- The real value of simdjson is multi-exchange architectural
  consistency — uniform parser API across exchanges with different
  message shapes (deeply nested for Coinbase / Kraken account
  endpoints; snapshot-based for dYdX / hyperliquid).
- For a single-exchange (Binance-only) workload, the maintainability
  win is theoretical; locking it in now adds dependency surface
  without producing observable user-side benefit.

**v5.11.4.A SHIPPED:** `tt::parse_double_fast` / `parse_double_fast_n` /
`parse_uint64_fast` (std::from_chars wrapper) on the WS-ingest +
extract_double + Reconcile_get_double surfaces. Locale-immune,
sufficient for current workload.

**Re-trigger condition:** start of the multi-exchange refactor.
Specifically: when adding the second exchange's WS / REST adapter.
At that point the simdjson vendoring + uniform parser API becomes
the load-bearing investment.

**Architectural recommendation when re-triggered:** hybrid pattern
documented at the time of re-trigger — flat WS messages stay on
strstr+from_chars (per-tick, marginal cost); deeply-nested REST
responses use simdjson (architectural fit). Per-message-shape parser
choice, not all-or-nothing.

---

## Strategy_FreePerCore AUTO/NONE state-pointer root-cause (2026-05-08)

**Symptom:** at engine shutdown, `Strategy_FreePerCore` was firing
`unknown kind 5` WARN on cores that should have had concrete strategy
kinds (e.g. SIMPLE_DIP=2, MOMENTUM=1, EMA_CROSS=4 per cfg). Kind=5
is `STRATEGY_AUTO` — a sentinel that shouldn't have a state pointer.

**Patched in v5.11.11 (commit pending):** turned the AUTO/NONE case
into a quiet null-out (no WARN, no `delete` — would be type-cast UB
without knowing concrete type; arena owns the memory so reclamation
happens via InitArena_Destroy at engine shutdown). Pre-fix the WARN
cluttered shutdown logs without pointing to actionable operator
response. Reproducible on cfgs with duplicate `core_N_strategy=`
lines (last-wins parse).

**Root-cause investigation deferred.** Reading the code, AUTO cores
should have `state=null` post-Strategy_InitPerCore (line 153-158:
case STRATEGY_AUTO/STRATEGY_NONE/default → `ctx.strategy_state =
nullptr`). The shutdown observation says state is non-null, kind=AUTO.
Three theories worth investigating:

1. **AUTO resolution path allocates state on demand** without
   updating `strategy_state_kind` to the resolved concrete strategy.
   If true: write site is somewhere in `EventLoop_RebuildOneCore`
   when AUTO resolves to a concrete strategy.
2. **Snapshot persist/load** (ShardedSnapshotPersist.hpp:498) restores
   `strategy_state_kind` from disk but doesn't restore the matching
   `strategy_state` pointer. Then `Strategy_InitPerCore` runs and
   sets a NEW kind, but somewhere a state alloc happened with the
   OLD kind preserved.
3. **Hot-swap path** (EngineSharded.hpp:1566 / :2543 set
   `strategy_id = pending`) without calling Strategy_FreePerCore +
   InitPerCore in a paired sequence. State from previous strategy
   could persist with old kind.

**Re-trigger:** when an operator sees the WARN reappear under a
specific reproducer (then the root cause is investigable from the
specific cfg + lifecycle sequence). The v5.11.11 quiet-null patch
preserves correctness for now.

---

## DepthReplayState calloc — backtest-only (deferred 2026-05-07)

**Site:** `DataStream/DepthReplayState.hpp:205` —
`calloc((size_t)line_count, sizeof(BookSnapshot<F>))`. Allocates a
backtest-only depth replay buffer, sized at line_count from CSV.

**Status:** kept as calloc.

**Why deferred:** DepthReplayState is BACKTEST-ONLY. Used in
`Backtest/BacktestSharded.hpp:451` for replay during offline analysis.
The live engine never instantiates this struct (live depth comes from
the WS feed via `BinanceDepth.hpp`'s SPSC ring). The audit's
"production hot path zero-alloc" goal applies to live trading; offline
backtest tooling can have malloc with no production impact.

**Re-trigger condition:** if backtest startup latency becomes a
bottleneck for the operator workflow (currently runs in seconds at
typical CSV sizes).

---

## Backtest suite mallocs (BacktestSharded.hpp / BacktestPanels.hpp)

**Sites:** ~12 malloc/calloc/realloc calls in:
- `Backtest/BacktestSharded.hpp:620,637` (file_tick_counts, ticks
  buffer)
- `Backtest/BacktestPanels.hpp:263,1467,1540,1775,2399,2400,...`
  (worker args, equity curves, training buffers)
- `GUI/StrategyQualityPanel.hpp:133,162` (rotated log buffer)

**Status:** kept as malloc.

**Why deferred:** all in offline-tools paths (backtest workflow,
GUI panels for the suite). Live trading engine doesn't touch any
of these. The audit's "production zero-alloc" doesn't apply to
the suite tooling; converting them is research-grade hygiene
without runtime performance benefit on the engine.

**Re-trigger condition:** unlikely. The suite is operator-driven
(human invokes Run Full Validation → backtest workflow). Latency
of these allocations is invisible against the multi-second
backtest pass.

---

## v5.11.6.B — PoolAllocator mmap bootstrap (deferred 2026-05-07)

**Original scope:** master plan v5.11.6 + audit Part 7 Item 3 — replace
`PoolAllocator.hpp:47` `calloc` with `mmap(MAP_ANONYMOUS|MAP_POPULATE)`.

**Status:** ATTEMPTED in v5.11.6.B; REVERTED after reproducing
test segfault.

**What blocked it:** 30 production + test sites use the pattern
`free(pool.slots);` to reclaim the calloc'd backing memory. Calling
`free()` on an mmap'd pointer is UB and triggered SIGSEGV in the
controller_test integration suite.

Conversion would require either:
1. Sed-replace 30 sites from `free(pool.slots)` →
   `OrderPool_DestroyBacking(&pool)` + extending the OrderPool struct
   with bookkeeping fields. Mechanical but high risk (any miss
   silently corrupts).
2. Side-table tracking `{ptr → size, is_mmap}`. Adds map dependency
   to a header that historically has zero allocator overhead.

**Why defer:** The PoolAllocator is sized at 64 entries × ~56 bytes
= ~3.5 KB. That fits in ONE 4 KB page. MAP_POPULATE pre-faulting
1 page provides essentially zero observable benefit vs calloc
(which also single-pages on first-touch).

**Re-trigger condition:**
- PoolAllocator capacity grows to multi-page sizes (e.g. > 64 KB)
- Page-fault measurement on first OMS Submit shows the calloc
  lazy-fault is observable.

**Effort estimate when re-triggered:** ~2 hours (sed-replace + verify
all 30 sites + add OrderPool_DestroyBacking + tests).

---

## AVX-512 FPN primitives (FPN_Min/Max, Lemire divmod, asm AddSat)

**RE-EVALUATED 2026-05-07:** considered for shipping under v5.11.6.A;
deferred again after honest assessment of impact vs effort.

### Detailed rationale (2026-05-07)

**FPN_Min / FPN_Max AVX-512 vectorization:**
- Current scalar FPN_Min is already branchless mask-blend (~6 instructions
  for F=64).
- AVX-512 wins on ARRAY operations — the only such loop in our code
  (rolling stats min/max scan) was replaced by O(1) monotonic deque in
  v5.11.2.C.
- Current call sites are all scalar (single FPN_Min per regime check,
  per slope guard, etc.). AVX-512 gives no benefit on scalar callers.
- Status: **negligible benefit at current call sites.**

**Lemire divmod for FPN_DivNoAssert:**
- ~30-50% faster division on 192/128 long-division path.
- But v5.11.2.A's reciprocal LUT eliminated most divisions in
  RollingStats. Remaining: ~1-2 per slow-path cycle for R²/slope.
- Slow-path cycle is 50-100μs (mostly OS interference); shaving ~100ns
  off division is sub-percent of total work.
- Status: **marginal at current cadence.**

**Asm-implemented AddSat:**
- Saturating add — clamp to max on overflow.
- gcc -O3 already produces branchless cmov for compiler-recognized
  saturation patterns. The current FPN_AddSat hits this via FP64_AddSat
  which uses `int diff = a.sign ^ b.sign;` + branchless arithmetic.
- Hand-written asm might save 1-2 cycles compounded across many calls;
  with ~thousands of FPN_AddSat per slow-path cycle, that's tens of ns.
- Status: **marginal-to-zero benefit.**

**Why deferred (again):**
- Session-time-vs-impact ratio unfavorable: ~1-2 days work for
  collectively ~hundreds of ns (or less) shaved off a slow-path cycle
  whose p99 is dominated by OS interference (~1ms).
- v5.11.6 (allocator eradication) and v5.11.7 (Bandit AVX-512) have
  bigger structural wins on the same time budget.
- For showcase value: the existing branchless FPN<F> primitives + the
  reciprocal LUT + monotonic deque ARE the demonstration of
  hand-tuning. Adding AVX-512 vectorization on scalar call sites
  doesn't reinforce that story.

**Re-trigger condition:**
- Profiling shows FPN ops dominating slow-path p50 (not p99 — p99 is
  OS-bound).
- Or: an array-parallel FPN workload emerges (e.g. multi-symbol
  parallel regime classify, batch ML feature pack across N cores).

### Original (pre-2026-05-07) text follows for reference

**Original scope:** AVX-512 FPN_Min / FPN_Max, Lemire divmod, asm
AddSat. Identified in `LATENCY_OPTIMIZATION_AUDIT.md` Part 11.

**Status:** deferred to v5.11 perf sprint per the v5.10.0b master
plan. Partially shipped (FPN_Sqrt + FPN_Exp + FPN_Sin/Cos in 5.10.0b
phases B.2.5.A/B/D/C). The remaining items are micro-perf wins for
the FPN library.

**Deferred to:** later v5.11 sub-phase OR v5.12 perf sprint.

**Why deferred:**
- v5.10.0b shipped the load-bearing FPN-end-to-end determinism
  primitives (Sqrt / Exp / Sin / Cos / DivNoAssert).
- The remaining AVX-512 SIMD wins are nano-second optimizations on
  primitives already determined-correct. Marginal value at this
  stage.
- FlowFeatures conversion (Phase B.2.5.C boundary-stable refactor)
  intentionally kept double at the API boundaries to avoid 6-file
  cascade. Full FPN cascade is a separate v5.11+ ship if profiling
  ever warrants it.

**Re-trigger condition:** profiling that shows FPN_Min / FPN_Max in
hot enough call paths to warrant SIMD.

---

## v5.11.0/.1 hot-path items 1.3 + 1.4 — maker-order optimizations

**Original scope:** items deferred from the v5.11.1 hot-path AVX-512
review for "future maker-order update" per session memory.

**Deferred to:** the maker-order feature ship (whenever maker-side
strategies become a focus).

**Why deferred:** these are maker-quote-specific hot-path optimizations
that don't apply to the current taker-only strategies. Wiring them
in before there's a maker-side codepath would be premature
abstraction.

**Re-trigger condition:** start of maker-quote strategy implementation.

---

## io_uring async I/O on Binance WS connection

**Why on this list:** the user asked about path to lower tick-to-trade
latency; io_uring would save 3-8μs of the current 7-25μs envelope.

**Status:** never planned for v5.11 (master plan never included it).
Listed here so the path-to-lower-latency conversation has a place to
land.

**Deferred to:** when the operator co-locates AND has a real
production target. Without colocation, the network RTT (100-300ms
to non-colo Binance) dwarfs the io_uring-saveable 3-8μs.

**Effort estimate:** ~hundreds of lines new code in BinanceCrypto.hpp,
moderate complexity (replacing `SSL_read` with async io_uring patterns
that still wrap OpenSSL).

**Re-trigger condition:** operator co-locates to a Binance-adjacent
datacenter (AWS Tokyo / Singapore for Binance Asia; AWS Ireland for
Binance global).

---

## Kernel-bypass NIC (DPDK / Solarflare OpenOnload)

**Why on this list:** the endgame for absolute lowest tick-to-trade.

**Status:** never planned for v5.11. Listed for completeness.

**Deferred to:** v6+ if the operator targets serious latency
arbitrage (cross-exchange, sub-ms strategies).

**Effort estimate:** major rewrite — full TCP/TLS implementation
needed (or vendor a kernel-bypass TCP/TLS library).

**Re-trigger condition:** evidence that the operator is in a
strategy regime where the Tier-2 latency floor (~2-5μs tick-to-trade
post io_uring + colo) isn't sufficient.

---

## Parser convention for multi-exchange (when added)

**Recommended pattern (documented here for future reference):**

When adding the second exchange:
1. Vendor `simdjson` into `vendor/simdjson/` (gitignored — already
   in .gitignore via the `vendor/` rule).
2. Define an exchange-agnostic parser interface in
   `CoreFrameworks/ExchangeParser.hpp` — minimal API:
   - `parse_trade(const char *json, size_t n, ParsedTrade *out)`
   - `parse_execution_report(...)`
   - `parse_open_orders(...)`
3. Per-exchange implementations choose the parser strategy:
   - Flat / small messages: strstr + std::from_chars (current
     Binance pattern). ~500-1000ns/parse, no vendor dep.
   - Deep / large messages: simdjson on_demand API. ~1-3μs/parse,
     uniform handling of nesting.
4. Document the choice in the per-exchange header comment.
   Reviewers can see at a glance which strategy was picked and
   why.

**Don't:** rewrite the Binance flat-WS parser to simdjson during
the multi-exchange refactor. The cost is real, the win is
theoretical, and you've already proved the parser correctness via
v5.11.4.A's parity tests.

---

## Walk-Forward + held-out 0.0% accuracy regression (2026-05-07)

**Surfaced by:** operator GUI screenshot at v5.11.17. Training panel
shows:
- Train Multi-Horizon → models/test_case1.json: 44.2% in-sample
- auto-stamp FAILED: REFUSE: gap 0.4417 > threshold 0.0000
  (i.e. train=44.2%, held-out≈0.0% → gap≈44%)
- Run Walk-Forward → all visible folds (2-5) at 0.0% / 0.0% / 0.0%
- Diagnosis: "no edge — val accuracy at or below the always-predict-best baseline"

**Symptom shape:** model can predict in-sample but is at-or-below
random on every held-out / WF-test slice. Both held-out (auto-stamp
check) and walk-forward folds report ~0%. Status="clean" so no NaN
or warning fired — predictions DID happen, they just don't match
labels at all.

**Hypotheses to test:**
1. **Test-fold labels are all-zero** — if WF's split places non-event
   labels (binary 0 / multiclass 0) entirely in the test fold and
   the model predicts class>=1, accuracy = 0/N. Check fold split's
   label-distribution diagnostic + per-fold class_counts.
2. **Locale or parsing regression in stamp body** — v5.11.4.C swept
   atof/strtod to ParseFast across ML_Headers/ModelInference.hpp
   (~13 sites) + CoreModelZoo.hpp (3 sites) + BanditLearning.hpp.
   Could a number be mis-parsed (off-by-1000 from comma-vs-period
   under some locale), shifting label thresholds. Re-run with
   `LC_NUMERIC=C` env var to control for this.
3. **FPN end-to-end (v5.10.0b) round-trip** changed an internal
   double→FPN conversion that affects label generation.
   `LabelFunctions.hpp` is FOREACH_TARGET-driven (v5.10.0d) — bisect
   to v5.10.0b vs v5.11.x to localize.
4. **Test data quirk** — operator was using `test_case1.json` /
   `test_case_01` run name, suggesting synthetic / hand-built data.
   May not be a real regression at all; could be data-side issue
   that pre-existed.

**Investigation plan (deferred):**
- Step 0: re-run with a known-good prior model (one that worked at
  v5.10.0e) — does WF still report 0%? If yes, the WF computation
  itself is broken; if no, the model trained at v5.11.x is the
  problem.
- Step 1: bisect v5.11.x ships against the WF accuracy. Most
  suspicious: v5.11.4.C (parsing sweep), v5.11.7 (Bandit AVX-512;
  but that's inference-time, not training).
- Step 2: dump per-fold label histograms to confirm hypothesis 1
  (test fold all-zero labels would show class_counts[0] = N,
  others = 0).

**Code review findings (2026-05-07, no test data required):**

Walked the ML/Backtest/FPN commit list between v5.10.0e (last
known-good operator banner) and HEAD (v5.11.23). 12 commits
touched ML/Backtest/FPN paths. Bisect priority order:

1. **v5.11.2.C (O(1) running sums + monotonic deque)** ← TOP
   SUSPECT. Largest refactor of the lot — RollingStats_Push
   internals replaced with O(1) accumulator math instead of
   O(W) loops over the window. Subtle accumulator drift would
   compound over 128-1024 tick windows + flow into every
   feature that reads `price_sum` / `price_sum_y2` /
   `price_sum_xy` / `volume_sum` / `vol_sum_xy`. If labels
   compute via the same RollingStats path (LabelFunctions.hpp
   + Backtest/BacktestEngine.hpp), they'd drift the same way.
   First place to bisect.

2. **v5.11.2.A (reciprocal LUT for 1/n)** ← SECOND. Commit msg
   acknowledges "1e-10 relative drift" in non-power-of-2 n
   averages. Power-of-2 n (window sizes 128, 512, 1024) are
   exact, so for the canonical pipeline the LUT should match
   bytewise. If labels or features use a non-power-of-2 n
   (e.g. R² regression with off-by-one sample counts), drift
   could compound at decision boundaries.

3. **v5.11.2.B (RollingStats cache-line layout reorder)**
   ← THIRD. Pure layout change; no math touched. But if any
   site reads RollingStats by RAW OFFSET (snapshot persist,
   GUI surface, ML feature pack), a reorder breaks them
   silently. Less likely (compiler catches member references)
   but worth a `grep` for `offsetof(RollingStats` or any
   pointer-arithmetic on the struct.

4. **v5.11.4.C (atof/strtod → ParseFast)** ← LOW. Affects
   STAMP body parsing + bandit state load + TradeReader CSV.
   Doesn't touch label CSV ingestion (FPN_FromString is the
   primary parser there + that's locale-immune by
   construction; v5.11.4.C didn't change it).

5. **v5.11.7 (Bandit AVX-512)** ← VERY LOW. Inference-time
   probability normalization, not training/labels. Verified
   bytewise-deterministic vs scalar in commit tests.

**Quick sanity (sub-question to bisect):** in the operator's
training pipeline, does the model's `objective` get set
correctly? If WalkForward_ComputeMulticlassAccuracy at
BacktestEngine.hpp:1293 receives `num_classes < 2`, it
returns 0.0 unconditionally. Could explain "0.0% across all
folds" exactly. Worth checking before doing a full bisect.

**Bisect order if quick sanity passes:**
1. Check out `v5.11.2` rollup tag, run WF on test_case_01.
2. If WF still 0% → bisect goes earlier (v5.10.1.A label
   registry hash plumb? but that was part of v5.10.0e).
3. If WF non-zero → narrow to v5.11.2.A vs .2.B vs .2.C by
   checking each individually.

**Re-trigger condition:** before any v5.11.x trained model goes
live OR before declaring v5.11 sprint definitively complete. v5.11
optimization sprint shipped 17+ optimization items; some bytewise-
determinism preserved (replay-determinism baseline GREEN per
CHANGELOG), but the ML training/inference path may have
unaccounted parity drift this regression exposes.

**v5.11.18a/.18 status:** does NOT block. v5.11.18a adds cfg +
stamp infrastructure with all-on default mask (no behavior
change). v5.11.18 (full ML wiring) MUST land after this is
understood — adding feature_mask machinery on top of an ML pipeline
that's already producing 0% held-out is not actionable.

Operator stance 2026-05-07: "we probably broke some stuff, but
these optimizations will make it better going forward and were
worth it." Confirms forward-motion preference; this regression is
catalogued for fix-during-paper-testing.

---

## Trade History C2/A + C2/B partial-exit legs show $0 notional + $0 P&L (2026-05-07)

**Surfaced by:** operator GUI screenshot at v5.11.20. Trade History
panel shows 3 trades:

```
#  Co… L… Entry  Exit   P&L     Fee   Reas Strat In    Out   Hold
1  C2  B  $81060 $80940 -$0.00  $0.00 SL   AUTO  $0    $0    33m37s
2  C2  A  $81060 $80940 -$0.00  $0.00 SL   AUTO  $0    $0    33m37s
3  C0  A  $81141 $80942 -$6.68  $3.00 SL   DIP   $1500 $1496 39m24s
```

**Symptom shape:** trades 1+2 are the partial-exit A/B leg pair
from core 2 (AUTO strategy). Both show:
- Entry $81060, Exit $80940 (same prices)
- P&L $0.00 (display rounding? or actual zero?)
- Fee $0.00 (suspicious — fee should be ~ taker_fee × notional)
- In $0, Out $0 (notional zero)

Trade 3 is the C0 leg-A (DIP strategy) with normal-looking values:
$1500 in, $1496 out, fee $3.00 (= 0.10% × $1500 × 2 round-trip),
P&L = $1500 - $1496 - $3.00 = -$6.68 ✓ math checks.

**Hypotheses:**
1. **AUTO core notional accounting bug.** AUTO cores allocate
   risk fraction differently than concrete strategies. Maybe
   `core_2_risk_pct` defaulted to 0 and AUTO bypassed the global
   default, allocating $0 notional. Check `cfg.core_risk_pct[2]`
   and `Strategy_AdaptPerCore` for AUTO strategy.
2. **Partial-exit leg-pair accounting bug.** When core 2 took a
   position with partial exits (A+B legs), only the leg-A leg got
   notional accounting; leg-B got $0. But both legs ARE shown
   with $0, so it's not "leg B specifically" — both legs of core
   2 have the issue.
3. **Display bug, not accounting bug.** TradeReader CSV may have
   the right notional but the GUI is reading the wrong column /
   misformatting. Run `cat logs/trade_history.csv` to confirm.
4. **Connection to the WF regression.** Both this + the WF 0%
   accuracy were surfaced 2026-05-07 on v5.11.x. Could be related
   if a v5.11.x parsing/conversion regression affects both
   feature-extraction and notional-tracking sites.

**Investigation plan (deferred):**
- Step 0: dump `logs/trade_history.csv` for the C2/A + C2/B rows;
  confirm whether stored notional is $0 (accounting bug) or
  non-zero (display bug).
- Step 1: cross-check `oms->portfolio.positions[slot].notional`
  at exit time for AUTO cores via debug logging.
- Step 2: bisect like the WF regression — if the same v5.11.x ship
  produced both issues, root-causing once fixes both.

**Re-trigger condition:** before any v5.11.x trained model goes
live OR any AUTO-strategy core deploys to live. Connected to the
WF regression investigation; root-cause both together if they
share a cause.

**Code review findings (2026-05-07, no live data needed):**

Inspected `logging/btcusdt_order_history.csv` directly:
```
timestamp_us,core_id,strategy_id,event_type,price,...,trade_size
1778144580 0 2 E $81140 ... 0.01848239   <- DIP, slot 0, OK
1778144590 2 5 E $81140 ... 0.01848241   <- AUTO, slot 2, OK
1778145938 4 5 E $81060 ... 0.00000199   <- AUTO, slot 4 (partial leg A), BROKEN
1778145938 5 5 E $81060 ... 0.00000199   <- AUTO, slot 5 (partial leg B), BROKEN
```

The non-zero `trade_size = 0.00000199` (~$0.16 at $81060) is the
giveaway — not literally 0, but ~1/10000 of slot 0/2's normal
value. Suggests `allocated_balance` for slots 4+5 is small but
non-zero (FPN precision noise or genuinely tiny).

`Sharded_LegSlot` (ControllerEventLoop.hpp:772) maps logical-core
N + leg L to portfolio slot 2N+L when partial_exit_enabled=1. So
slots 4+5 = logical core 2's A+B legs.

`state->cores[]` is indexed by LOGICAL core (0..N-1 for
num_cores=4). `state->oms->portfolio.positions[]` is indexed by
PORTFOLIO SLOT (0..7 under partials). Boot loop sets
`state->cores[i].allocated_balance` for i=0..3 (logical cores)
correctly. Strategy_BuildParameters reads
`state->cores[logical_core].allocated_balance` — so allocated
$1500 for core 2 SHOULD produce trade_size ≈ 0.0185.

**Mystery:** if allocated_balance for logical core 2 is $1500,
where does the $0.16 trade_size come from? Possibilities:
- `core_open_notional` mid-trade-cycle subtraction leaves the
  available balance near-zero on a re-entry attempt
- Strategy_BuildParameters reads a different field for AUTO cores
  vs concrete strategies (need to trace the AUTO resolution code
  path's allocated_balance source)
- partial-split logic at order-submission time divides the
  trade_size by something that rounds it to ~0

**Next investigation step:** add `Health_Log(WARN)` at
`Strategy_BuildParameters` entry showing
`(slot, allocated_balance, intended_qty)` and at the partial-split
site to trace where the qty drops by 4 orders of magnitude.

Operator-side workaround: set `partial_exit_enabled=0` in
engine.cfg (single-slot mode). Engine has been working there
since the start of the v5.11 cycle.

---

## Run Full Validation auto-stamp internal copy failure (2026-05-07)

**Surfaced by:** operator screenshot at v5.11.33 — WF passed, held-out
0.427, gap 0.024 < threshold 0.05 (so stamp SHOULD have written),
but worker emitted yellow status:

```
Held-out OK; auto-stamp skipped — model_path='models/test_case_05.json'
snapshot non-empty but auto_stamp_path empty (internal copy failure;
report bug)
```

**Code path** (`Backtest/BacktestPanels.hpp:2347-2410`): the worker
copies `model_path_snap → fv_results.auto_stamp_path` at line
2351-2355 ONLY if `cfg.auto_stamp_on_held_out=1`. After
Backtest_RunFullValidation, the diagnostic at line 2402 fires when
`fv_results.auto_stamp_path[0] == '\\0'` despite `model_path_snap`
being non-empty. The "report bug" framing is the original author
labelling the case as "shouldn't be reachable post-v5.10.0E."

**Hypotheses:**
1. `Backtest_RunFullValidation` (the worker's main call) MUTATES or
   CLEARS fv_results.auto_stamp_path internally, e.g. on failure of
   one of the validation steps. Need to grep the function for
   writes to `.auto_stamp_path`.
2. cfg.auto_stamp_on_held_out is actually 0 in operator's cfg
   (DESPITE held-out OK), and the diagnostic-cascade logic took the
   wrong branch (a `!auto_stamp_enabled` check exists at 2384 but
   maybe it's not what fires).
3. fv_results was zeroed mid-flight by a different worker thread or
   code path — race with the GUI render.

**Investigation (deferred):**
- Step 0: grep the Backtest_RunFullValidation body for any
  mutation of `out->auto_stamp_path` after the input copy.
- Step 1: log auto_stamp_enabled + auto_stamp_path values before +
  after the worker call to confirm which copy was lost.

**Re-trigger condition:** before relying on auto-stamp output (i.e.,
before any operator workflow that depends on having a `.stamp` file
post-Run Full Validation). Manual workaround:
`./tools/stamp_model.sh --model models/test_case_05.json --secret '...'`
with the WF/held-out numbers from the screenshot.

**Severity:** MEDIUM. Auto-stamp is operator-convenience. The bash
CLI path (`tools/stamp_model.sh`) is the canonical fallback +
already exists. Not blocking.

---

## STRATEGY QUALITY panel can't open health.jsonl (2026-05-07)

**Surfaced by:** operator GUI screenshot at v5.11.20. Strategy
Quality panel shows:
```
fopen failed: logging/health.jsonl
Click Refresh. Reads last 2000 lines from health.jsonl
(set health_log_path in engine.cfg to enable per-trade logging)
```

**Symptom shape:** Operator's engine.cfg does NOT have
`health_log_path=logging/health.jsonl` (or the path is unset and
the panel hardcoded the default). The engine isn't writing health
records, so the panel has nothing to read.

**This is not an engine bug** — the panel's tooltip already
explains the operator-config gap. Two possible improvements:

1. **Better empty-state UI:** instead of "fopen failed:", say
   "health.jsonl not found — set `health_log_path` in engine.cfg
   to enable. Default suggestion: `health_log_path=logging/
   health.jsonl`". Less alarming for new operators.
2. **Auto-create the path:** engine could create the directory
   when `health_log_path` is set + auto-emit a single
   "engine started" record so the panel always has at least one
   row to render. Avoids the empty-state path entirely.

**Re-trigger condition:** operator workflow polish ship. Low
priority; doesn't block any production functionality. Would
fold naturally into a future "operator UX cleanup" sprint after
the WF regression + accounting bug from above are root-caused.

---

## FP64_Sqrt assertion under ASAN (2026-05-07)

**Surfaced by:** v5.11.26 ASAN run, after the SPSCRing
stack-use-after-scope was closed by the OrderManagerState RAII
destructor. Test progressed past the writer-thread bug + into
v5.10.0a.next.2 bandit replay-determinism tests, then aborted on:

```
controller_test: FixedPoint/FixedPoint64.hpp:298: FP64 FP64_Sqrt(FP64):
  Assertion `value.sign == 0 || value.magnitude == 0' failed.
```

**Why ASAN-only:** the assertion is in a header that's pre-built
with `-O3 -DNDEBUG` for the engine + release controller_test, so
asserts are stripped — sqrt(negative) silently NaNs in release.
ASAN builds with `-O1 -g` (no NDEBUG) and asserts fire. ASAN
caught a path where some caller passes a negative FP64 to
FP64_Sqrt without checking sign first.

**Why pre-existing:** the assert has been at
FixedPoint64.hpp:298 since v5.0+; the test path that triggers it
predates this v5.11 sprint. v5.11.26's RAII destructor only
revealed it (by getting ASAN past the earlier crash).

**Investigation plan:**
- Step 0: identify which test in v5.10.0a.next.2 triggers it.
  ASAN output shows the test progressed past the bandit
  replay-determinism `prediccontroller_test` line — the truncated
  output suggests it's mid-test (the line shows "predic"
  indicating in-progress).
- Step 1: find the call site. `grep -rnE "FP64_Sqrt\(" --include="*.hpp"`
- Step 2: most likely it's a stat that computes `sqrt(variance)` where
  variance went slightly negative due to FPN accumulator drift
  (an FPN<F=64> sum-of-squares minus square-of-sum can underflow
  by a tiny amount and become negative). Add a `fmax(0, value)`
  clamp before FP64_Sqrt.

**Re-trigger condition:** before any future ASAN-clean gate, OR
before declaring the engine free of latent FP edge cases.

---

## SPSCRing+OrderEventLog stack-use-after-scope under ASAN (2026-05-07)
**RESOLVED 2026-05-07 in v5.11.26** — OrderManagerState RAII
destructor calls OrderManager_Shutdown at scope exit; writer
thread is joined before stack memory becomes invalid. Verified
by ASAN run: 672+ tests progressed past the prior crash point
(SPSCRing_TryPop:168). New failure (FP64_Sqrt assertion) is
unrelated — captured above as a separate deferred item.

**Surfaced by:** v5.11.17 ASAN run (build_asan controller_test).

**Symptom:** AddressSanitizer reports
`stack-use-after-scope at SPSCRing.hpp:143 in SPSCRing_TryPop<OrderEvent<64>, 256>`.
Cited stack frames are nearby in main(): `stack_var` (line 14013, v5.11.6.A
InitArena_Owns test) + `on_stack_dummy` (line 15617, v5.11.15 AUTO/NONE
defensiveness test). Actual access is at offset 12094304 in the frame —
i.e., a different test's `EventLoopState<FP> state;` stack region whose
scope has ended, reused by subsequent stack allocations, but the
OrderEventLog async writer thread (started in OrderManager_Init at
OrderEventLog.hpp:369, v5.11.3.B feature) is still draining the
SPSC ring and reading from those stale stack addresses.

**Why pre-existing:** ASAN error reproduces on v5.11.16 binary as well as
v5.11.17 binary. v5.11.17 (PoolAllocator mmap backing) does NOT touch
SPSCRing, OrderEventLog, or OrderManager. The bug has been latent since
v5.11.3.B introduced the async writer thread — non-ASAN tests pass
because the read happens at addresses that still hold valid bytes (the
program just keeps running), so functional tests can't catch it.

**Why not a current-engine bug:** in production the async writer's lifetime
is bounded by OrderManagerState's lifetime which is bounded by the engine
process's lifetime. The use-after-scope only manifests at test-suite
scale where N test cases each `{ ... EventLoopState state; ... }` and a
leftover thread from an earlier test sees freed-then-reused stack.

**Possible fixes:**
1. **EventLoopState_Free joins all spawned threads before returning.**
   The right answer if EventLoopState_Free already promises symmetry
   with EventLoopState_Init. Verify `OrderEventLog_StopAsyncWriter` is
   called transitively. This is the boundary-stable refactor.
2. **Test harness allocates engine state on heap.** Replace
   `EventLoopState<FP> state;` with `auto* state = new EventLoopState<FP>;
   ... delete state;`. Heap allocations don't have ASAN's
   stack-use-after-scope detector. Less invasive but doesn't actually
   fix the race — just hides it.
3. **Disable async writer for tests.** Add a cfg / env-var override
   so tests run with the synchronous-write fallback that v5.11.3.B
   introduced as the FALLBACK path.

**Re-trigger condition:** any v5.11.x ship that touches OrderEventLog
or OrderManager, OR if the operator decides the ASAN test-isolation
gap is worth a focused ship. Estimate: 1-2h for fix #1; 30 min for #2.

**v5.11.17 status:** does NOT block. PoolAllocator changes verified
green on non-ASAN controller_test (1797/0 both calloc + mmap
backings). Deferred for follow-up.

---

## v5.11.62 — Role-aliasing patch is tactical, not architectural

**Status:** Tactical patch SHIPPED in v5.11.62 (2026-05-08). Cleaner
architectural refactor deferred.

**What v5.11.62 does:** When a multi-horizon training run saves models
under role names other than `buy_signal` (e.g. PEAK_VALLEY_STABLE
3-class saves as `barrier.json`), the loader memcpy's the ModelHandle
struct from the source role array (e.g. `ezoo->barrier[i]`) into the
`ezoo->buy_signal[i]` slot, marks the copy as `borrowed=1`, and sets
`buy_class_idx=1` so `Model_Predict` returns class 1 (peak) probability
as the buy signal. All existing `buy_signal_count` callers (MLStrategy,
StrategyParameters dispatch, Bandit ops, snapshot population) work
unchanged.

**Why it's tactical:**
- Two ModelHandle structs reference the same XGBoost booster (one owns,
  one borrows). The `borrowed` flag is the single check site that keeps
  this safe — easy to forget on future struct field additions.
- The aliasing is implicit. Reading `ezoo->buy_signal[i]` doesn't tell
  you it came from `ezoo->barrier[i]`. Forensics for "which model is
  this prediction from" needs to traverse `model_path` strings.
- Bandit weights for the aliased role are tracked via the buy_signal
  arrays. If operator later wants to train BOTH a buy_signal AND a
  barrier model and use both, they conflict on the buy_signal slot.

**Why it's fine for now:**
- 3 label kinds covered: binary buy_signal (existing), 3-class barrier
  PEAK_VALLEY_STABLE (aliased to buy_signal), regression buy_signal
  (existing). New label kinds add one branch in alias logic.
- `borrowed` flag has exactly one check site (`Model_Free`). Reviewable.
- Ships in 30 min vs 3-4 hours for the full refactor; unblocks paper
  trading today.

**The cleaner refactor (when re-triggered):**
- `EnsembleModelZoo` gains `primary_handles` (ModelHandle**),
  `primary_count`, `primary_target_class`, `primary_role_name[16]`.
- Loader picks primary role at end of `LoadFromCfg`/`AutoDetect`:
  buy_signal > barrier > regime fallback. No memcpy, no borrowed flag.
- `MLStrategy.hpp` predict path reads `ezoo->primary_handles` +
  `primary_target_class`. No knowledge of role-name semantics in
  strategy code.
- `StrategyParameters.hpp` dispatch (Bandit_GetProbabilities, weighted
  blend, per-arm preds) all use `primary_*` instead of `buy_signal_*`.
- Snapshot population uses `primary_count` (not `buy_signal_count`).
- Settings panel reads `primary_role_name` for display.
- New `Model_Predict_AtClass(handle, features, n, class_idx)` helper
  decouples the class-extraction concern from the role concern.

**Re-trigger conditions:**
1. Operator adds a 4th label kind whose buy semantics aren't "extract
   one class probability" (e.g. multi-class exit signal that combines
   class probabilities, or regime-conditional buy logic).
2. Operator wants to train BOTH a buy_signal AND a barrier model and
   use both simultaneously (the alias would clobber).
3. The `borrowed` flag causes a real bug (it shouldn't — single check
   site, but a future struct addition could break it).
4. Bandit weights need per-role isolation (currently aliased into
   buy_signal).

**Estimate:** ~3-4 hours including snapshot/settings-panel updates,
test coverage, boot-log message updates, hot-swap path coordination.
Could be a v5.12.x ship or a focused v5.11.x sub-ship if a re-trigger
fires earlier.

**Files that would change in the refactor:**
- `ML_Headers/CoreModelZoo.hpp` (struct fields + LoadFromCfg/AutoDetect)
- `ML_Headers/ModelInference.hpp` (new `Model_Predict_AtClass` helper)
- `Strategies/MLStrategy.hpp` (predict path)
- `Strategies/StrategyParameters.hpp` (Bandit dispatch)
- `CoreFrameworks/ShardedSnapshot.hpp` (population of n_horizons)
- `DataStream/EngineTUI.hpp` (PerCoreSnap field rename or addition)
- `GUI/SettingsPanel.hpp` (Settings UI display)
- `tests/controller_test.cpp` (new role-priority + class-extraction tests)

---

## Maintenance

When deferring a future item, append a section here using the
template above. When re-triggering and shipping, leave the section
in place but add a `**RE-TRIGGERED → shipped in vX.Y.Z**` line at
the top of the section so the deferral history stays queryable.

### v5.11.12 cleanup (2026-05-07)

Three sections removed because they were never genuinely deferred —
they shipped under different sub-version names. Listed here as a
back-pointer so the audit trail isn't lost:

- **v5.11.3.D `mmap(MAP_POPULATE)` for OrderEventLog** → SHIPPED in
  v5.11.5.C (per `DOCS/CHANGELOG.md` v5.11 row).
- **Stamp body / bandit / TradeReader atof sites** → SHIPPED in
  v5.11.4.C (locale-immune parsing sweep covered all three site
  groups).
- **v5.11.0a Hardware/OS Tuning (audit Part 13)** → SHIPPED as
  `DOCS/OPERATOR_DEPLOYMENT.md` runbook (no code change pending;
  operator deployment work, not engine code).

Per future-rule (added with this cleanup): if a deferred-items
section is actually a "shipped under different name" entry,
remove it during the next /readiness pass on a related plan rather
than letting it accumulate. Doc is meant to reflect what's TRULY
deferred, not history of what was renamed mid-sprint.

## Orderbook-depth microstructure features (queue position, new-player detection, etc.)

**Status:** Deferred. Current engine uses `BinanceCrypto/Depth` WS feed
+ `DepthReplayState` for slow-path features (book_imbalance, spread_z,
flow_*_ewma, large_trade_z) but does NOT extract microstructure-grade
features that would matter for sub-second alpha at colo.

**Candidate additions (HFT microstructure tier):**

1. **Queue position estimation** — when our limit order rests at a
   price level, estimate where we are in the FIFO queue. Inputs:
   level depth at order placement time + cumulative trades + cancels
   at that level since. Output: time-to-fill probability per second
   of waiting. Strategy uses it to decide between aggressive (cross
   spread) vs passive (rest) entries.

2. **New-player / iceberg detection** — track unique participants by
   order ID patterns (Binance exposes per-order modifications, not
   trader IDs, but iceberg refresh patterns + symmetric replenishment
   on opposite sides + size clustering reveal hidden players).
   Output: per-level "informed/uninformed" prior that feeds the
   ConfidenceScore as an additional feature.

3. **Spoofing / layering detection** — orders placed > 5 levels deep
   that get cancelled within 100ms × N occurrences = likely spoof.
   Output: a "manipulation probability" gate that dampens entries
   when spoof activity is high.

4. **Toxic order flow indicator** — short-window post-trade P&L of
   the LIQUIDITY TAKER (us, when we cross the spread). If our taker
   trades consistently lose money in the next N seconds, the venue
   is "toxic" (informed traders are picking us off). Output: spread-
   threshold widening when toxicity rises.

5. **Multi-level depth aggregation** — currently slow-path uses
   limited depth tiers; full L2 book aggregation across N price
   levels with weighted-by-distance imbalance gives a richer
   regression signal than top-of-book ratio alone.

6. **Trade-through / price-improvement detection** — when a trade
   prints at a price BETWEEN BBO levels, that's a hidden order or
   sub-tick improvement. Useful for detecting "real" market intent
   vs mechanical fills.

**Why deferred:**
- Solo-developer tier; not all 6 are worth the engineering cost
  before live trading proves the basic ML signal works.
- HFT microstructure features primarily pay off at colo (sub-ms
  decision windows). Current paper-trading-from-laptop deployment
  has 50-200ms WS round-trip latency, dwarfing the value of
  queue-position estimation.
- Each feature requires non-trivial new state in slow_state +
  feature pack additions + train-serve parity verification +
  retraining of all models. Big sprint, not single-ship.

**Re-trigger conditions:**
1. Operator moves to colo / kernel-bypass deployment (sub-ms decision
   loop). At that point, queue position + new-player detection
   become first-order alpha sources.
2. Paper trading reveals systematic adverse selection (taker fills
   consistently lose money) — toxicity indicator becomes load-bearing.
3. Cross-venue arbitrage strategy (multi-exchange) — spoofing
   detection per venue + new-player tracking become critical.

**Approximate sprint shape:**
- v5.X.0: queue position estimator (1 week — needs DepthReplayState
  extension + per-order tracking ring + exit attribution math)
- v5.X.1: new-player / iceberg detection (1 week — pattern matching
  on book updates + statistics ring)
- v5.X.2: spoof detector (3-4 days)
- v5.X.3: toxicity indicator (1 week — needs trade-fill attribution
  + post-trade P&L lookback)
- v5.X.4: multi-level depth aggregation (3-4 days)
- v5.X.5: trade-through / price improvement (2-3 days)

**Estimate:** ~4-5 weeks for full set. Do partial pickup based on
strategy's actual paper-trading pain points, not exhaustive port.

**Reference docs:**
- The optimization audit (private workspace) Section 12 has more
  detail on which colo-tier optimizations pair well with each
  microstructure feature. Re-read before opening any of these as
  active work.

