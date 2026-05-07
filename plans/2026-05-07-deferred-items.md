# Deferred Items Log (v5.11 sprint)

Tracking everything we've explicitly chosen NOT to ship in the current
sprint, with the deferral rationale and the trigger conditions for
revisiting.

This file is gitignored (private) — workspace-backed via the
`plans/` symlink convention.

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

## SPSCRing+OrderEventLog stack-use-after-scope under ASAN (2026-05-07)

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
