# Master Plan — v5.11 Optimization Sprint

**Date:** drafted 2026-05-06 (post-fresh-clone recovery)
**Branch:** TBD (`feat/v5.11-optimization`, opens after v5.10.0e ships)
**Predecessor:** v5.10.0e (closes Sprint B). Cannot start before
v5.10.0b/0c/0d/0e all green.
**Effort estimate:** ~3-4 weeks across 9 ships (large sprint;
biggest since v5.9 ML hardening). Hot path WILL be touched in
v5.11.1 (deliberate; Part 1 audit items).
**Source audits (private):**
- `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` (Gemini, 2026-05-06; gitignored)
  + workspace mirror `plans/2026-05-06-latency-optimization-audit.md`
- `DOCS/STRATEGY_AND_CODING_RULES.md` (Gemini, 2026-05-06; gitignored)
  + workspace mirror `plans/2026-05-06-strategy-and-coding-rules.md`
- `plans/2026-05-08-v5.11-OPTIMIZATION-REFERENCE.md` (Surgical implementation guide for v5.11)
- `plans/2026-05-08-v5.11-ANNOTATED-REVIEW.md` (Annotated surgical review with surgical suggestions)

---

## Theme

v5.11 is a **massive optimization sprint** that maps directly to the
13 parts of Gemini's latency audit. The audit identified ~40 specific
optimization sites; this sprint groups them into 9 ships of bounded
scope. Sprint kicks off after v5.10.0e closes; total effort ~3-4
weeks at sprint cadence.

**Architectural shift:** v5.11 elevates the engine from
"branchless + lock-free + zero-allocation in hot path" to
"branchless + lock-free + zero-allocation engine-wide, AVX-512-
vectorized, kernel-isolated, sub-microsecond tail variance." The
audit's part 13 (hardware/OS tuning) becomes a deployment runbook,
not a code ship — captured in v5.11.0a.

**What v5.11 does NOT touch:**
- ML pipeline correctness (v5.9-v5.10 hardening already shipped)
- Strategy logic (no new strategies; existing ones get vectorized)
- Stamp body / parity surface (already locked at v5.10)

---

## Audit-to-ship mapping

| Audit Part | Item count | Lands in |
|---|---|---|
| 1 — Hot Path (`ExecutionCore.hpp`) | 5 | v5.11.1 |
| 2 — Slow Path (RollingStats, FPN) | 5 | v5.11.2 |
| 3 — Architectural invariants | check-only | v5.11.0 (verify) |
| 4 — Data Ingestion + ML + Memory | 4 | split: 4.1 → v5.11.4, 4.2 → v5.11.5, 4.3 → v5.11.8, 4.4 → v5.11.6 |
| 5 — Bandit AVX-512 | 1 | v5.11.7 |
| 6 — System & OS Tail Variance | 3 | split: 6.1+6.2 → v5.11.3 + v5.11.5; 6.3 → v5.11.0a |
| 7 — Eradicate System Allocators | 4 | v5.11.6 |
| 8 — WebSocket Parsing | 2 | v5.11.4 |
| 9 — OMS Variance | 2 | v5.11.5 |
| 10 — Concurrency Variance | 2 | split: 10.1 → v5.11.3; 10.2 → v5.11.4 |
| 11 — FPN Libraries | 4 | **folded into v5.10.0b Phase B.3** (amended 2026-05-06; all 4 items ship there since B.4's retrain absorbs the Newton-Raphson divide bit changes). Plus NEW Phase B.2.5 in 0b adds FPN_Exp + FPN_Sqrt primitives — required for FlowFeatures conversion; surfaced by /plan-check 2026-05-06. |
| 12 — HFT System Ops | 4 | v5.11.0 |
| 13 — Hardware/OS Tuning | 4 | v5.11.0a (runbook, not code) |

---

## Sprint structure (9 ships)

### v5.11.0 — System foundation (~4-6h, SHIP FIRST)
**Audit:** Part 12 (TCP_NODELAY, mlockall, FTZ/DAZ, PGO/LTO build).

Easy wins, table stakes for everything else. Ship first so
subsequent measurements are on a clean baseline.

**Items:**
1. **`TCP_NODELAY`** on all sockets (`BinanceOrderAPI.hpp`,
   `BinanceCrypto.hpp`). `setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)`
   right after socket creation. Closes the up-to-40ms Nagle stall
   on order submit.
2. **`mlockall(MCL_CURRENT | MCL_FUTURE)`** on engine boot. Locks
   memory pages into physical RAM; closes page-fault tail variance.
   Add to `main.cpp` post-cfg-parse.
3. **FTZ/DAZ in `main()`**: `_MM_SET_FLUSH_ZERO_MODE(_MM_FLUSH_ZERO_ON)`
   + `_MM_SET_DENORMALS_ZERO_MODE(_MM_DENORMALS_ZERO_ON)`. Kills FPU
   subnormal stalls in ML/exp decay paths.
4. **PGO + LTO build flags**: extend `build.sh` and `CMakeLists.txt`
   with `-fprofile-generate` / `-fprofile-use` orchestration. Already
   have `-flto`. Add a `./build.sh pgo` target that drives
   profile-gen → run-backtest → profile-use rebuild.
5. **Verify Part 3 architectural invariants**: zero `virtual`,
   zero scalar lookups in hot path, dense+aligned lookup tables.
   No code change expected; this is a parity-check pass.

**Tests:** +6 (smoke tests on socket opts, mlockall return value,
MXCSR state probe, PGO-flag presence in build flags hash).

### v5.11.0a — Operator deployment runbook (~2-3h, doc-only)
**Audit:** Part 13 + Part 6.3.

Not a code ship; produces `DOCS/OPERATOR_DEPLOYMENT.md` covering:
- Boot params: `isolcpus`, `nohz_full=N,M,...`, `rcu_nocbs=N,M,...`
- `chrt -f 99 <pid>` for SCHED_FIFO promotion of hot path threads
- `ethtool -C eth0 rx-usecs 0 rx-frames 0` for NIC coalescing
- `numactl --cpunodebind=N --membind=N` for NUMA locality
- Huge pages: `/etc/sysctl.d/40-hugepages.conf` + `MAP_HUGETLB`
- C-states: `intel_idle.max_cstate=0 processor.max_cstate=0`
- CPU governor: `performance`
- IRQ affinity for NIC

Public-safe doc (operator guide, not edge content). Lives in DOCS/.

### v5.11.1 — Hot path AVX-512 (~1-2 days, HOT PATH TOUCHED)
**Audit:** Part 1 (5 items).

**Hot path WILL be modified.** First v5.x ship that deliberately
changes hot path; requires bench gate.

**Items:**
1. Compile-time elision of `lat_enabled` — `template <bool LAT_ENABLED>`
   on `ExecutionCore_Tick`. Zero overhead when off.
2. AVX-512 vectorization of leg A+B comparisons via
   `_mm512_cmpge_epu64_mask`. Removes the `__builtin_expect(active_b, 0)`
   branch entirely; both legs evaluated in 1 cycle.
3. AVX-512 CMOV blending via `_mm512_mask_blend_epi64` for
   active/inactive TP/SL across both legs in one instruction.
4. Branchless ring buffer commit: `head += (can_enter | can_exit_a | can_exit_b)`
   with unconditional `TradeEvent` write. Removes final hot path
   control-flow branch.
5. Move `permission` flag to its own `alignas(64)` block. Fixes
   false sharing with `active`/`entry_price`/`live_tp`/`live_sl`.
   ~30-50ns/tick saved.

**Bench gate:** must show p99 ≤ pre-ship p99 across 10M-tick
backtest replay; p99.9 should improve. Pre-tag `pre-v5.11.1` for
rollback.

**Tests:** +8 (template-elision, AVX-512 mask correctness vs.
scalar reference, branchless head-advance bytewise equality with
prior ring buffer state, permission cache-line alignment static
assert, p99 latency regression test).

### v5.11.2 — Slow path O(1) regression + RollingStats padding (~1-2 days)
**Audit:** Part 2 (5 items).

**Items:**
1. **O(1) running sums in `LinearRegression3X_Fit`** — biggest absolute
   slow-path win. Replace W=128 loop with maintain-on-insert sums:
   subtract evicted sample contribution, add new sample. ~128× speedup
   on the regression step.
2. **Precomputed reciprocal LUT for `1/n`**: `n_fp` runs 2..W=128.
   Compile-time `static constexpr FPN<F> reciprocals[129]`.
   `FPN_Mul(sum, reciprocals[n])` replaces `FPN_DivNoAssert`. Branchless,
   no FPU.
3. **AVX-512 `FPN<256>`/`FPN<512>` vectorization** of `FPN_MagAddN` /
   `FPN_MagSubN`. `__m512i` parallel processing of 8× 64-bit words.
   Eliminates scalar carry chains.
4. **`alignas(64)` on RollingStats output vs. internal state** —
   read-heavy outputs (`price_avg`, `price_slope`) on separate cache
   lines from write-heavy ring buffer state (`head`, `count`).
   Closes GUI-thread → engine-thread false sharing.
5. **Branchless wrap refinement**: `count = std::min<int>(count + 1, W)`
   via CMOV/SIMD min. Minor; mostly cosmetic since `count` saturates
   quickly.

**Replay-determinism gate:** O(1) running sums must produce bytewise-
equal output to O(W) recomputation across 10M-tick replay. Test
explicitly.

**Tests:** +12 (running-sum bytewise equality, reciprocal LUT correctness
across n=2..128, AVX-512 FPN<256> add bytewise equality with scalar,
cache-line-isolation static asserts).

### v5.11.3 — TUISnapshot Seqlock + async log thread (~1 day)
**Audit:** Part 10.1 + Part 6.1 + Part 6.2.

Closes a **correctness gap** (torn TUISnapshot reads) AND a tail-
variance gap (synchronous I/O on drainer).

**Items:**
1. **`TUISnapshot` Seqlock**: replace double-buffer toggle with a
   sequence-counter Seqlock matching `ParameterSlot`. Reader retries
   on tear; writer never blocks. Closes "GUI sees torn buffer when
   producer laps it" hazard.
2. **Async log thread for `OrderEventLog_Append`**: lock-free queue
   feeding a dedicated background log writer. Drainer thread no longer
   blocks on `fwrite`/`fflush`. Disk-stall isolation for hot path.
3. **Pre-allocated OrderEventLog capacity**: `mmap(MAP_POPULATE)` at
   boot for max expected log size. No `realloc` mid-trading. Pairs
   with v5.11.6 allocator unification.

**Tests:** +8 (seqlock retry path coverage, torn-read regression test,
async-log queue bytewise-ordering preservation, pre-alloc bounds).

### v5.11.4 — Parsing SIMD (~1-2 days)
**Audit:** Part 4.1 + Part 8 + Part 10.2.

Replaces all scalar JSON + float parsing with SIMD/branchless
equivalents. Not on hot path; on WS ingest + REST + reconcile paths.

**Items:**
1. **simdjson integration** for WS trade parser
   (`binance_parse_trade`), execution report parser
   (`ud_parse_execution_report`), and reconcile parser
   (`Reconcile_ParseOpenOrders`). Single-pass O(N) tokenize; all keys
   extracted simultaneously. Eliminates current `O(N*K)` strstr scan.
2. **`fast_float` for numeric parsing** (`fill_price`, `fill_qty`).
   Replace `atof`. Locale-independent, branchless.
3. **Direct parse-to-`FPN<F>`**: skip the intermediate double when
   the consumer immediately converts to FPN.

**Vendor:** `vendor/simdjson/` and `vendor/fast_float/` (gitignored,
header-only). Document in CLAUDE.md / OPERATOR_DEPLOYMENT.md.

**Tests:** +10 (simdjson round-trip vs. scalar baseline on synthetic
WS messages, fast_float boundary values, FPN-direct parse precision
vs. atof+FPN_FromDouble two-step).

### v5.11.5 — OMS variance (~1-2 days)
**Audit:** Part 4.2 + Part 6 (residual) + Part 9.

**Items:**
1. **Kill `BinanceAdapter_WorkerLoop` `sleep_for(200μs)`** — replace
   with `_mm_pause()` adaptive spin-wait, fall back to `futex` after
   N idle iterations. Closes up-to-200μs order-submit tail.
2. **MPSC drain queue** replacing N×SPSC fan-in in `OMS_DrainSubmit`.
   `O(1)` arrival handling; no per-core empty-queue scans. Or
   eventfd/io_uring for kernel wakeup (defer if MPSC is enough).
3. **clientOrderId slot encoding**: `oms_<id>_<slot>` format. Parse
   slot index out of execution report's clientOrderId for O(1) lookup.
   Replaces `O(N)` linear scan over `MAX_INFLIGHT_ORDERS` bitmap.

**Tests:** +8 (MPSC arrival ordering preservation under N=4 producers,
slot-encoded clientOrderId round-trip parse, spin-wait → futex
transition timing).

### v5.11.6 — Allocator unification (~2-3 days, BIG SHIP)
**Audit:** Part 7 (4 items) + Part 4.4.

Eradicates libc allocators engine-wide. Largest architectural ship
of v5.11.

**Items:**
1. **Single `mmap(MAP_POPULATE | MAP_HUGETLB)` arena at boot.**
   All custom allocators draw from this. Pre-faulted (no first-touch
   stalls), huge-paged (TLB pressure ~zero).
2. **Refactor `PoolAllocator` and `BuddyAllocator`** to draw from the
   arena, not `calloc`/`malloc`. Bootstrap from static `.bss` if
   needed.
3. **Init-time allocations** (`PortfolioController`, `ControllerEventLoop`):
   replace `malloc`/`new` for `RollingStats`, `CoreSlowState` with
   arena allocations.
4. **Buddy bitmask O(1) order lookup**: `__builtin_ctz` over a
   `uint32_t` free-block mask. Replaces 17-iteration order scan.
   Also fix the `1u < order` typo in `buddy_internal_order_to_size`.
5. **Strict zero-allocation in `DataStream`**: enforce static buffers
   / pool slabs throughout the network/TLS layer. No `std::string` /
   `std::vector` runtime allocations.

**Migration risk:** large blast radius (every allocator site).
Sub-tag every phase: `v5.11.6.A` (arena boot), `v5.11.6.B` (Pool/Buddy
refactor), `v5.11.6.C` (PortfolioController), `v5.11.6.D` (DataStream),
`v5.11.6.E` (buddy bitmask + typo fix). Operator validates between
each.

**Tests:** +15 (arena pre-fault verification, Pool/Buddy bytewise
behavior preservation, allocation-count regression test = zero libc
allocs after init, buddy O(1) lookup correctness, typo fix).

### v5.11.7 — Bandit AVX-512 (~4h)
**Audit:** Part 5.

Bandit state arrays (`weights[8]`, `cum_reward[8]`) fit perfectly in
a single `__m512d`. Vectorize the slow-path bandit ops.

**Items:**
1. `Bandit_GetProbabilities` → `_mm512_div_pd` for normalization,
   `_mm512_max_pd` for argmax.
2. `Bandit_Update` → `_mm512_add_pd` + `_mm512_exp_pd` for importance-
   weighted reward updates.
3. Maintain bytewise determinism — same input sequence + same prior
   weights = bytewise-identical output. Replay-determinism test
   already exists from v5.10.0a.next.2; extend.

**Tests:** +5 (AVX-512 vs. scalar bytewise equality across 600-cycle
synthetic reward sequence, exp/div precision boundary tests).

### v5.11.8 — ML AOT compile (speculative; ~2-3 days)
**Audit:** Part 4.3.

Speculative ship. Treelite or in-house transpiler converts trained
XGBoost/LightGBM trees into compiled C++. Brings single-row
inference from ~1-5μs (XGBoost C API) down to <100ns.

**Defer if v5.11 cumulative effort exceeds 3 weeks.** Standalone
ship; doesn't block other v5.11 items.

**Items:**
1. Treelite integration: emit `inference.h` per model, link into engine.
2. Stamp body extension: `aot_compiled_sha256` field (canonical
   position 22 — TBD; coordinate with v5.10.0a/0d position claims).
3. Engine load: prefer compiled `.h` symbol if present, fall back to
   XGBoost C API otherwise. Operator opt-in via cfg.
4. Train-serve parity test: AOT compiled prediction = XGBoost C API
   prediction within float epsilon, across 1000 random feature vectors.

**Tests:** +8 (AOT vs. C API equivalence, fallback path coverage,
stamp round-trip with new field).

**Risk:** treelite version coupling, AVX-512 codegen variability.
Pre-tag carefully.

### v5.11.9 — Carryover backlog close (~optional, flexible)
**From `2026-05-08-v5.11-deferred-items.md` (existing):**
- #5 feature mask cfg per-core (3-4h)
- #7 scaler comparison tool (2h)
- #18 RFV scaler binding (TBD)
- Doc gap: `OPERATOR_QUICKSTART.md` (3-4h)
- Test file split (`controller_test.cpp` ~12k lines → 4 files; 2-3h)
- Skill versioning frontmatter (~1-2h)

These are flexible; pick items as time permits at sprint close. Not
blocking the v5.11 → v5.12 transition.

---

## Cross-ship dependencies

```
v5.11.0 (system foundation: TCP_NODELAY, mlockall, FTZ/DAZ, PGO/LTO)
   ├──> v5.11.1 (hot path AVX-512; needs FTZ/DAZ for clean math)
   ├──> v5.11.2 (slow path; same)
   └──> ALL downstream ships (build flags + system invariants)

v5.11.0a (deployment runbook) — independent doc ship; can land any time

v5.11.4 (parsing SIMD) — independent; touches DataStream/, no engine internals

v5.11.5 (OMS) — needs v5.11.0 socket flags pattern; otherwise independent

v5.11.6 (allocator unification) — touches everything; ship NEAR END or
   in parallel sub-ships per area; coordinate with v5.11.3 (which uses
   pre-allocated OrderEventLog from arena)

v5.11.7 (Bandit AVX-512) — independent; isolated to BanditLearning.hpp

v5.11.8 (ML AOT) — independent; speculative; defer if time-pressed
```

**Critical path:** v5.11.0 → v5.11.1 → v5.11.2 → v5.11.6
**Parallelizable:** v5.11.0a, v5.11.3, v5.11.4, v5.11.5, v5.11.7, v5.11.8

---

## Architectural invariants (every ship must preserve)

| Invariant | Verification |
|---|---|
| Hot path UNTOUCHED — **EXCEPTION: v5.11.1 deliberately touches hot path** | All other ships verify via `tools/calls_graph_diff.sh` |
| Bytewise replay determinism | All ships add a determinism test against pre-ship reference output |
| Stamp body forward-compat | v5.11.8 only ship that touches stamps; canonical position TBD |
| Train-serve parity | v5.11.8 must verify AOT compiled = XGBoost C API |
| `MODEL_FORMAT_VERSION` only bumps if stamp structure changes | v5.11.8 may bump → 7 (TBD); else stays at 6 (post-v5.10.0b) |
| `FEATURE_REGISTRY_HASH` / `LABEL_REGISTRY_HASH` stable | No v5.11 ship modifies feature/label registries |
| Coding rules adherence | Every ship verified against `DOCS/STRATEGY_AND_CODING_RULES.md`; no malloc/virtual/mutex/sleep_for/atof/strstr violations |

---

## Operator-validation gates per ship

- **v5.11.0:** `mlockall` returns 0; MXCSR FTZ/DAZ bits set; PGO build
  produces measurable speedup vs. -O3 baseline on backtest.
- **v5.11.0a:** docs published; operator validates one boot config
  matches doc on dev box.
- **v5.11.1:** p99 ≤ baseline, p99.9 improved. Bench gate explicit.
- **v5.11.2:** O(1) regression bytewise = O(W) baseline; slow-path
  cycle time reduced by ≥80%.
- **v5.11.3:** torn-read test reliably catches the prior bug; new
  Seqlock path passes.
- **v5.11.4:** simdjson round-trips bytewise = scalar parser on 10k
  synthetic messages.
- **v5.11.5:** order-submit p99 reduced (sleep_for elimination); MPSC
  preserves arrival ordering.
- **v5.11.6:** zero libc allocations after init phase (verify via
  malloc hook); arena fully pre-faulted at boot.
- **v5.11.7:** Bandit AVX-512 = scalar bytewise on 600-cycle sequence.
- **v5.11.8:** AOT prediction = C API prediction within epsilon.

---

## Sprint kickoff checklist

Before opening v5.11.0 (after v5.10.0e ships):
- [ ] All v5.10 ships green; tests passing
- [ ] Master plan v5.10 Sprint B updated to 6/6 SHIPPED
- [ ] Workspace synced + pushed
- [ ] `/parity-check` GREEN at v5.10 close
- [ ] Re-read `DOCS/STRATEGY_AND_CODING_RULES.md` Parts 1-11 for
      sprint context
- [ ] Re-read `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` Parts 1-13 for
      sprint context
- [ ] Bench harness baseline captured (latency p99/p99.9 + slow-path
      cycle time + WS ingest ms-per-burst) on operator hardware

If any unchecked, do NOT start v5.11.0.

---

## Cross-references

- Predecessor: `2026-05-02-MASTER-v5.9-to-v5.10.md` Sprint B (v5.10
  ships 0b/0c/0d/0e pending)
- Source audits: `plans/2026-05-06-latency-optimization-audit.md`
  + `plans/2026-05-06-strategy-and-coding-rules.md`
- Existing v5.11 backlog (carried over to v5.11.9):
  `plans/2026-05-08-v5.11-deferred-items.md`
- Local Claude memory referencing both audits:
  `CLAUDE.local.md` (gitignored at engine repo root)

---

## Per-sub-ship tag summary

```
v5.11.0     — System foundation (TCP_NODELAY, mlockall, FTZ/DAZ, PGO/LTO)  [PENDING]
v5.11.0a    — Operator deployment runbook                                  [PENDING]
v5.11.1     — Hot path AVX-512 (Part 1)                                    [PENDING; HOT PATH TOUCHED]
v5.11.2     — Slow path O(1) regression + RollingStats padding (Part 2)    [PENDING]
v5.11.3     — TUISnapshot Seqlock + async I/O log (Parts 6, 10)            [PENDING]
v5.11.4     — Parsing SIMD: simdjson + fast_float (Parts 4.1, 8, 10.2)     [PENDING]
v5.11.5     — OMS variance (Parts 4.2, 6, 9)                               [PENDING]
v5.11.6     — Allocator unification (Parts 4.4, 7); 5 sub-tags             [PENDING; BIG]
v5.11.7     — Bandit AVX-512 (Part 5)                                      [PENDING]
v5.11.8     — ML AOT compile (Part 4.3, speculative)                       [PENDING; DEFERRABLE]
v5.11.9     — Carryover backlog close                                      [FLEXIBLE]
v5.11-final — Optimization sprint COMPLETE                                 [PENDING]
```

`git reset --hard <tag>` for surgical rollback at any granularity.

---

## Smell-test reminder

The audit lists ~40 items. This plan covers ~35 of them across 9
ships + carryover backlog. The 5 items NOT in this plan ship in
**v5.10.0b** instead:
- Part 11 (FPN libs, 4 items) — folded into v5.10.0b Phase B.3
  per amendment 2026-05-06.
- Buddy `1u < order` typo from Part 4.4 — folded into v5.11.6.E.

Additionally, **FPN_Exp + FPN_Sqrt primitives** (NEW work, not in
the original audit; surfaced by /plan-check 2026-05-06) ship in
v5.10.0b Phase B.2.5 because FlowFeatures conversion requires them.
v5.11 inherits the FPN library in a more complete state than the
original audit assumed. Vectorization of those primitives via
AVX-512 can fold into v5.11.X if profiling shows wins, but isn't
on the critical path.

If a future audit pass surfaces new items: add to v5.11.9 if small,
or open a v5.12 plan if architectural.

### NEW: Ultra-Metal Backlog (v5.11+)
The following items were identified during the Annotated Review and should be prioritized after the core sprint:
1. **Instruction Alignment Audit:** Explicitly align hot-path loop entries to 64-byte boundaries (`.p2align 6`).
2. **Bit-Field Refactor:** Convert strategy boolean chains into single-byte bit-fields to use the CPU's `test` instruction.
3. **Write-Combining Buffers:** Utilize `_mm_stream` (non-temporal) hints for background log ring-buffer writes.

---

## Inherited Gaps from v5.10 (Sprint B)

The following items were identified as scope drift or gaps during the `v5.10` sprint and have been formally absorbed into the `v5.11` optimization sprint for future scheduling or vectorization:

### 1. Vectorization of `FPN_Exp` and `FPN_Sqrt`
- **Origin:** Surfaced during `v5.10.0b` plan check (`2026-05-06-v5.10-sprint.md`). `FlowFeatures.hpp` requires native fixed-point exponential and square root primitives.
- **v5.11 Action:** While `v5.10.0b` implements the scalar versions of these primitives, `v5.11` will absorb the **AVX-512 vectorization** of these functions. This should fold into `v5.11.2` (Slow Path Vectorization) or a later ship if profiling dictates it is a bottleneck.

### 2. `strcmp` Jump Table Refactoring & AVX-512 Feature Masks
- **Origin:** Elevated from "Deferred Items" to "HFT Invariants" by the `v5.11` HFT Sidecar.
- **v5.11 Action:** Must be explicitly scheduled. The `strcmp` refactor fits into `v5.11.0` or `v5.11.4`, while the AVX-512 Feature Mask must execute unconditionally via `_mm512_mask_blend_epi64`, folding into `v5.11.2`.

---

## Technical Implementation Considerations

The following technical risks and mitigations must be addressed during the execution of this sprint to ensure safety and determinism:

### 1. v5.11.1 (Hot Path) — Register Pressure
Using `__m512i` registers on the hot path introduces the risk of the compiler spilling other hot variables (like `active` or `entry_price`) to the stack.
- **Mitigation:** Inspect assembly output (`-S`) to ensure no stack traffic is introduced in `ExecutionCore_Tick`. Use `register` hints or refactor scope if spills occur.

### 2. v5.11.2 (Slow Path) — Bitwise Sum Drift
$O(1)$ running sums (subtract evicted, add new) can accumulate floating-point or fixed-point bitwise drift over millions of ticks compared to a full $O(W)$ recalculation.
- **Mitigation:** Implement a "Periodic Resync." Every 100,000 ticks, force a full $O(W)$ recalculation of the sums to clear any cumulative rounding or precision errors.

### 3. v5.11.4 (Parsing) — simdjson Padding
`simdjson` requires its input buffer to have an explicit padding (typically 32-64 bytes) beyond the end of the string to safely perform SIMD read-ahead without causing a segmentation fault.
- **Mitigation:** Audit `DataStream` buffer allocations to ensure `JSON_PADDING` is added to all WebSocket and REST response buffers.

### 4. v5.11.6 (Allocators) — The Bootstrap Slab
If the unified arena handles all allocations, we face a circular dependency where the allocator cannot initialize because the arena state isn't live.
- **Mitigation:** Reserve a "Bootstrap Slab"—a statically allocated `uint8_t` array in the `.bss` section—to hold the initial metadata for the `BuddyAllocator` and `PoolAllocator` before the `mmap` call is executed.

### 5. v5.11.8 (ML AOT) — Mandatory Parity Gate
AOT-compiled tree math must be bit-identical (within float epsilon) to the XGBoost C API.
- **Mitigation:** Every model deployment MUST include a mandatory 1,000-row parity test script. If the AOT prediction diverges from the C API reference, the model must be rejected at load-time.
