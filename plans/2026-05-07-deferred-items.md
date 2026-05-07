# Deferred Items Log (v5.11 sprint)

Tracking everything we've explicitly chosen NOT to ship in the current
sprint, with the deferral rationale and the trigger conditions for
revisiting.

This file is gitignored (private) — workspace-backed via the
`plans/` symlink convention.

---

## v5.11.3.D — `mmap(MAP_POPULATE)` pre-alloc for `OrderEventLog`

**Original scope:** master plan v5.11.3 item 3 — pre-allocate
OrderEventLog capacity at boot via `mmap(MAP_POPULATE)`. No `realloc`
mid-trading.

**Deferred to:** v5.11.6 (allocator unification).

**Why deferred:**
- v5.11.3.C moved the realloc OFF the drainer thread (now happens on
  the async writer pthread). Drainer-side urgency dropped to zero.
- v5.11.6 will do a coordinated allocator-eradication pass across the
  whole engine. Folding pre-alloc into that pass is cleaner than a
  standalone ship.

**Re-trigger condition:** if drainer tail latency profiling shows
the realloc-on-writer-thread is itself a parity / replay issue.
Current expectation: it isn't.

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

## Stamp body / bandit / TradeReader atof sites

**Sites:** `ML_Headers/ModelInference.hpp` (~13 atof calls in stamp
parser), `ML_Headers/CoreModelZoo.hpp` (3 atof calls),
`ML_Headers/BanditLearning.hpp:407` (1 strtod call),
`GUI/TradeReader.hpp` (4 atof calls), `tests/parity_harness.cpp` (1
atof call), `tests/controller_test.cpp` (assorted).

**Deferred to:** focused parity-locale-immunity ship if locale flips
become a documented concern.

**Why deferred:**
- These are LOAD-TIME paths (stamp parsing on model load, bandit
  state load on engine boot, CSV parsing in GUI render thread). No
  hot-path or warm-path latency exposure.
- Stamp parsing already has locale pinning at EMIT time (per the v5.9
  parity audit) — `tools/stamp_model.sh` and the in-process emitter
  pin LC_NUMERIC=C. Round-trip parity is preserved in the sane case.
- The locale-flip silent-corruption hazard is theoretical for
  load-time paths; practical on hot-path (which v5.11.4.A closed).

**Re-trigger condition:** any of:
- A documented locale-flip incident on a load-time path
- A multi-locale deployment (operator on a non-C-locale system)
- A v5.x parity audit that flags load-time atof as a CRITICAL gap

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

## v5.11.0a Hardware/OS Tuning (audit Part 13)

**Status:** SHIPPED as a runbook (`DOCS/OPERATOR_DEPLOYMENT.md`),
not as code. The runbook covers isolcpus, SCHED_FIFO, IRQ affinity,
hugepages, intel_pstate / turbo, governor settings, NUMA pinning.

**Deferred to:** when the operator co-locates and applies the
runbook. Currently a laptop dev environment; the runbook reflects
deployment-box settings.

**No code change pending** — Part 13 is documentation-complete; only
the operator's manual deployment work remains.

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

## Maintenance

When deferring a future item, append a section here using the
template above. When re-triggering and shipping, leave the section
in place but add a `**RE-TRIGGERED → shipped in vX.Y.Z**` line at
the top of the section so the deferral history stays queryable.
