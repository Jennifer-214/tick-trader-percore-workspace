# Interview Prep — Low-Latency Systems Topics

Prep sheet for HFT / quant systems / low-latency C++ interviews. Maps your existing code in `tick-trader-percore` + `FoxLIB` to formal interview vocabulary so you can articulate fluently under pressure.

**How to use this:** drill section by section. For each topic, try answering from memory first, then check the script. Once you can paraphrase the *quick answer* without looking, move on. Save the detailed answer for if they push.

---

## 1. Lock-Free SPSC Queue

### Quick answer (30s)

> "A single-producer single-consumer ring buffer. Producer writes head, consumer writes tail. They never block on each other — only on full or empty. Power-of-two capacity so I mask instead of modulo. Head and tail live on separate cache lines so writes from the producer don't invalidate the consumer's L1 line via cache coherence. Each side caches the other's counter so the common case never reads from the remote cache line at all."

### Detailed answer (2-3 min)

> "The core insight is that with one producer and one consumer, you don't need any atomic compare-and-swap. The producer is the sole writer of `head`, the consumer is the sole writer of `tail`. They're both readers of the other side, but pure reads under the right memory ordering are safe.
>
> Three optimizations matter:
>
> 1. **Cache-line separation**: `head` and `tail` are on different 64-byte cache lines via `alignas(CACHE_LINE)`. Without this, every push invalidates the consumer's view of `head` and every pop invalidates the producer's view of `tail` — that's MESI cache coherence traffic costing ~80-100ns per op. With it, each side stays in its own L1.
>
> 2. **Cached counters**: producer keeps a local `tail_cached`. Only refreshes from the consumer's `tail` when its local view says the ring looks full. Same trick on the consumer side. So in the common case (ring not near full or empty), neither side ever loads from the remote cache line.
>
> 3. **Memory ordering**: I write payload first, then store `head` with `release` semantics. Consumer loads `head` with `acquire`. The release-acquire pair guarantees the payload write is visible before head update is visible. On x86 (TSO) `release` is a plain mov, but the C++ memory model requires the annotation for portability and to prevent compiler reorder.
>
> End result: ~3-5ns per op."

### Map to your code

`FoxLIB/include/foxlib/spsc.hpp` — your SPSCRing struct. Look at:
- `alignas(CACHE_LINE)` on the ring fields
- `head_cached` / `tail_cached` on each side
- `__atomic_store_n(..., __ATOMIC_RELEASE)` / `__atomic_load_n(..., __ATOMIC_ACQUIRE)`

### Likely follow-ups

- **"How would you make this MPSC?"** → "Multiple producers means head needs CAS. Each producer attempts `compare_exchange_strong(head, head + 1)` to reserve a slot, then writes payload. Consumer side stays the same. Cost: ~15-25ns per push due to CAS contention vs ~3ns for SPSC."

- **"How would you make this MPMC?"** → "Both sides need CAS, AND you need per-slot sequence numbers to prevent the ABA problem and to coordinate visibility. The Vyukov MPMC pattern uses a per-slot sequence counter. Significantly more complex; I'd reach for a battle-tested implementation like LMAX Disruptor or boost::lockfree before writing it from scratch."

- **"What's the ABA problem?"** → "When CAS reads value A, then by the time it tries to swap, the value went A → B → A. CAS thinks nothing changed but the world did. Causes incorrect linearization in MPMC structures. SPSC doesn't have this because there's no shared CAS — each side has a sole writer. MPMC mitigations: tagged pointers, hazard pointers, epoch-based reclamation."

- **"Why power-of-two capacity?"** → "Lets me replace modulo with bitmask: `index & (N-1)`. Single AND instruction vs an integer divide which is 20-30 cycles. Also makes the wrap-around branchless."

---

## 2. Memory Ordering (Acquire / Release / SeqCst / Relaxed)

### Quick answer (30s)

> "Memory ordering tells the compiler and CPU what reordering is allowed around an atomic operation. `relaxed` allows any reordering. `acquire` says no later loads/stores can move before this load. `release` says no earlier loads/stores can move after this store. Acquire/release pairs synchronize: everything before the release in the writer is visible to everything after the acquire in the reader. `seq_cst` is the strictest — total order across all threads — and the most expensive."

### Detailed answer

> "The C++ memory model is a contract about visibility and reordering. There are six orderings; in practice you use four:
>
> - **`memory_order_relaxed`** — atomic but no ordering. The atomic operation itself is indivisible, but the compiler and CPU can reorder freely around it. Used for counters where you only need atomicity, not synchronization. e.g., a hit counter.
>
> - **`memory_order_acquire`** — load-side. Nothing in this thread that comes after the acquire load can be reordered before it. Pairs with release.
>
> - **`memory_order_release`** — store-side. Nothing in this thread that comes before the release store can be reordered after it. Pairs with acquire.
>
> - **`memory_order_seq_cst`** — full sequential consistency. There's a single global total order all threads agree on. Strongest and slowest — on x86 it's a `mov + mfence`; on weak architectures it's even worse.
>
> The acquire/release pattern is the key one. If thread A writes payload, then `store(release, flag=1)`, and thread B does `load(acquire, flag) == 1`, then thread B is guaranteed to see the payload write. That's the synchronization primitive my SPSC queue is built on.
>
> On x86 specifically, the architecture is TSO (Total Store Order) — stores are not reordered with stores, loads not reordered with loads. So `release` is a plain `mov` and `acquire` is a plain `mov`. The annotations matter for the *compiler* not to reorder, and for portability to weakly-ordered architectures like ARM where the CPU itself can reorder."

### Likely follow-ups

- **"Why not just use `seq_cst` everywhere?"** → "Seq_cst on x86 stores requires `mfence` (or `lock`-prefixed instruction), which is 20-30 cycles. Acquire/release is free on x86. Performance matters in hot paths."

- **"What's a memory barrier?"** → "A CPU instruction that prevents reordering across it. `mfence` is full barrier. `lfence` is load barrier. `sfence` is store barrier. Acquire/release in C++ map to compiler-only barriers on x86; on ARM they map to `dmb ish` instructions."

- **"What does `volatile` do? Same as atomic?"** → "No. `volatile` prevents compiler optimization (no caching in registers, no reordering of volatile accesses with each other), but provides NO atomicity and NO ordering with non-volatile accesses. It's for memory-mapped I/O, not concurrency. Use `std::atomic` for thread synchronization."

---

## 3. Cache Coherence + False Sharing

### Quick answer

> "Modern CPUs have private L1/L2 caches per core, shared L3. When two cores read the same cache line, they each have a copy in L1. When one writes, the cache coherence protocol (MESI on x86) invalidates all other cores' copies. The line must be re-fetched on the next read. False sharing is when two unrelated variables happen to land on the same cache line — touching one invalidates the other, costing ~80-100ns. The fix is `alignas(64)` to put each on its own line."

### Detailed answer

> "MESI: each cache line is in one of four states across all cores — Modified, Exclusive, Shared, Invalid. When core A writes a line in Shared state, all other cores' copies transition to Invalid; A's copy goes to Modified. Other cores must re-fetch on next access.
>
> The cost: each cache miss to L1 is ~5ns, to L2 ~15ns, to L3 ~50ns, to local DRAM ~100ns, to remote socket DRAM ~300ns+. False sharing causes constant L3 round-trips between cores.
>
> Practical impact: a `std::atomic<int>` counter shared between threads is fine, but if you put two `std::atomic<int>` counters next to each other in a struct and update them from different threads, every update by either thread invalidates the other thread's copy. Throughput drops by 5-10x.
>
> Fix: `alignas(64) std::atomic<int> counter_a;` then padding (or another `alignas(64)`) for `counter_b`. Each gets its own cache line. On most x86 cache lines are 64 bytes; some Intel server chips prefetch in pairs (128-byte effective). Apple Silicon is 128-byte lines.
>
> In my SPSC ring, `head` is `alignas(CACHE_LINE)` and `tail` is `alignas(CACHE_LINE)` — separate lines. Producer touches head, consumer touches tail, no false sharing."

### Map to your code

- `FoxLIB/spsc.hpp` — `alignas(CACHE_LINE)` on head/tail
- `Tick.hpp` and `TradeEvent.hpp` — cache-line aligned for hot-path access

### Likely follow-ups

- **"How big is a cache line?"** → "64 bytes on most x86. 128 bytes on Apple Silicon. Some Intel server CPUs prefetch in pairs, effectively 128. Always check `std::hardware_destructive_interference_size` if portable."

- **"What's the difference between L1/L2/L3?"** → "L1 is per-core, ~32KB, ~5ns access. L2 is per-core (or per-pair), ~256KB-1MB, ~15ns. L3 is shared across all cores in a socket, ~8-64MB, ~50ns. DRAM is ~100ns local, ~300ns cross-socket."

- **"What's prefetching?"** → "CPU speculatively loads memory it predicts you'll need. Two kinds: hardware prefetcher (sees stride patterns automatically) and software (`__builtin_prefetch` hint). For a tick stream you can prefetch the next tick while processing current one — saves L1 miss latency."

---

## 4. x86 TSO vs ARM Weakly-Ordered

### Quick answer

> "x86 is Total Store Order — stores are never reordered with stores, loads never reordered with loads, but a load CAN be reordered before a prior store (StoreLoad reordering). ARM is weakly ordered — any read or write can be reordered with any other read or write unless explicitly barriered. C++ atomic ordering annotations protect you on both, but on x86 acquire/release is essentially free; on ARM it requires `dmb` instructions."

### Likely follow-ups

- **"What does `mfence` do?"** → "Prevents StoreLoad reordering. The only reordering x86 normally allows. It's the only x86 instruction that's a full barrier. Cost: ~20-30 cycles."

- **"Why is `seq_cst` more expensive than acquire/release on x86?"** → "Acquire/release are free (compiler-only barriers, no CPU instructions). seq_cst stores require `mfence` (or equivalently a `lock`-prefixed instruction), which serializes the pipeline."

---

## 5. Lock-Free vs Wait-Free vs Obstruction-Free

### Quick answer

> "Lock-free: at least one thread always makes progress system-wide. Wait-free: every thread always makes progress in bounded steps regardless of contention. Obstruction-free: a thread makes progress if all others stop. Wait-free is strongest, obstruction-free is weakest. My SPSC is wait-free for both producer and consumer — neither can block the other."

### Detailed answer

> "The three guarantees, weakest to strongest:
>
> - **Obstruction-free**: a thread completes in bounded steps if all other threads are paused. CAS-loop algorithms without retry guarantees often fall here.
>
> - **Lock-free**: at least one thread in the system always completes in bounded steps. Some thread can be starved indefinitely (livelock around CAS), but the system as a whole progresses.
>
> - **Wait-free**: every thread completes in bounded steps regardless of others. Strongest. Hard to achieve in MPMC structures, easy in SPSC.
>
> Why the distinction matters: a lock-free MPMC queue can have a producer livelock under heavy contention while other producers progress. Bad for latency tail. A wait-free version (e.g., via per-thread slots) avoids this but typically uses more memory.
>
> Rule of thumb: in HFT, you want wait-free on hot paths. SPSC is wait-free trivially. MPMC wait-free is research-paper territory; most production systems use lock-free MPMC and accept the tail."

---

## 6. CAS / Compare-and-Swap / LL-SC

### Quick answer

> "Compare-and-swap is the atomic primitive `if (*ptr == expected) { *ptr = desired; return true; } else { return false; }`. On x86 it's `lock cmpxchg`. It's the foundation of most lock-free MPMC structures. It can fail spuriously under contention, so you typically loop. ARM uses load-linked/store-conditional (LL-SC) with `ldxr`/`stxr` — different primitive, same effect."

### Detailed answer

> "CAS is the workhorse of lock-free programming. Standard pattern:
>
> ```cpp
> int expected = atomic.load();
> int desired;
> do {
>     desired = compute_new(expected);
> } while (!atomic.compare_exchange_weak(expected, desired));
> ```
>
> `compare_exchange_weak` can fail spuriously even when the values match (LL-SC implementations on ARM may fail on context switch). `compare_exchange_strong` retries internally to avoid spurious failures. Use weak in loops, strong for single-shot.
>
> Cost on x86: `lock cmpxchg` is ~20-30 cycles uncontended, much more under contention because it serializes the cache line. Avoid in hot paths where SPSC alternatives exist.
>
> The ABA problem is the classic CAS pitfall: between the read and the CAS, the value went A → B → A. CAS sees the old A and proceeds, but the world changed. Mitigations: tagged pointers (pack a counter into spare bits), hazard pointers, epoch-based reclamation."

---

## 7. Memory Reclamation (Hazard Pointers, RCU, Epoch)

### Quick answer

> "In lock-free data structures, freeing memory is hard because another thread might still be reading. The three standard solutions: hazard pointers (each thread publishes what it's reading; reclaimer skips those), RCU (read-copy-update — reclaim after a grace period when no readers exist), and epoch-based (group reclamations into epochs, free when all threads have crossed a barrier). Hazard pointers have the lowest reader cost; RCU has zero reader cost but requires a quiescent state; epoch is a middle ground."

### Likely follow-up

- **"What's RCU? When would you use it?"** → "Read-Copy-Update — readers access data with no synchronization, writers create a new version and atomically swap. Old versions are reclaimed once all readers that might see them have completed (a 'grace period'). Used heavily in the Linux kernel for read-mostly data structures. Reader cost: zero. Writer cost: significant, plus reclamation latency."

---

## 8. Branchless Programming

### Quick answer

> "Replacing conditional branches with mask-and-arithmetic so the CPU's branch predictor can't mispredict. Pattern: `result = condition ? a : b` becomes `result = (mask & a) | (~mask & b)` where `mask = -(uint64_t)condition`. Eliminates the ~15-cycle penalty of a misprediction at the cost of computing both branches unconditionally. Worth it on hot paths where misprediction would be common; not worth it where the branch is highly predictable."

### Detailed answer

> "The CPU pipeline speculates on branches. Modern branch predictors hit ~95% on predictable branches, but mispredictions cost ~15-20 cycles to flush the pipeline. On a hot path that runs millions of times per second with unpredictable conditions, that's brutal.
>
> Branchless patterns:
> - `mask = -(uint64_t)condition` — produces 0xFF...F if true, 0 if false
> - `result = (a & mask) | (b & ~mask)` — selects a or b without branching
> - `min = a ^ ((a ^ b) & -(a > b))` — branchless min
> - CMOV (conditional move) — compiler often generates this for ternary expressions when it judges the branch unpredictable
>
> In my hot path, the gate evaluation is fully branchless:
>
> ```cpp
> can_enter = !active & permission & bg_fires
> can_exit  = active & sg_fires
> ```
>
> Each of these is a bitmask AND. No branch, no misprediction risk. Combined with FPN comparisons that return 0 or 1 (not booleans), the entire decision is straight-line code. ~30-40 cycles."

### Map to your code

- `ExecutionCore.hpp` — `ExecutionCore_Tick` is end-to-end branchless
- The `__builtin_expect(active_b, 0)` is a *branch hint* — predicts not-taken, lets the leg-B SG check be skipped via cheap mispredict-avoidance when partials are off

### Likely follow-ups

- **"When is branchy code better than branchless?"** → "When the branch is highly predictable (>99%). Then prediction is essentially free, and branchless wastes CPU computing the unused branch. Rule: profile first."

- **"What's CMOV?"** → "Conditional move instruction. `cmov a, b, condition` writes b to a only if condition is true. No branch, but executes both sides. Compilers emit it for `result = cond ? a : b` when they decide branch prediction is unreliable."

---

## 9. Fixed-Point Arithmetic

### Quick answer

> "Integer math with an implicit decimal point. A 64-bit value with 32 fractional bits represents fractions of 2^-32, giving sub-cent precision for prices. No floating-point rounding errors, exact addition/subtraction, deterministic across architectures. Cost: multiplication is a 64x64=128-bit multiply followed by a shift; division is more expensive but rare in hot paths."

### Detailed answer

> "Floats have rounding errors and non-deterministic behavior across compilers and CPUs. For trading systems where every cent matters and reproducibility is required, fixed-point is the answer.
>
> My FPN<F> is templated on F = number of fractional bits. F=64 gives 4096-bit total width with 64 frac bits — way more precision than any market price needs. Each operation is implemented as integer arithmetic with explicit shifts.
>
> Add/sub: trivial integer add/sub, exact, no rounding.
>
> Multiply: `a * b` is a multi-word multiply producing a 2N-wide result, then right-shifted by F to restore the fixed-point format. For F=64 this means 128-bit intermediate from 64-bit operands; on x86 the `mulq` instruction produces this natively.
>
> Divide: harder, requires multi-word long division. Avoided in hot paths.
>
> Why arbitrary width: BTC at $100k with cent precision needs ~17 bits for integer part, ~14 for fractional cent. 32 bits total would suffice for that. But intermediate calculations can blow up — `notional × fee_rate × ...` chains. Wider FPN absorbs this without overflow.
>
> Determinism: same input produces same output bit-for-bit on any x86 / ARM. Critical for backtest-replay parity."

### Map to your code

- `FoxLIB/fpn.hpp` — your FPN implementation
- `FoxLIB/fp64.hpp` — optimized Q64.64 specialization using `__uint128_t`
- All hot-path math in `ExecutionCore_Tick` uses FPN

### Likely follow-ups

- **"Why not just use `double`?"** → "Doubles have 53 bits of mantissa. At BTC $76,740 that's ~12 bits of fractional precision available — fine for display but accumulates rounding errors over many operations. Also non-deterministic across CPU vendors (different rounding modes, transcendental approximations). Backtest results wouldn't replay bit-exact."

- **"Why not Decimal/BigDecimal?"** → "Variable precision means heap allocation, no inline operations, no SIMD. FPN is fixed-width, stack-allocated, branchless-compatible."

---

## 10. Hot-Path Latency Engineering

### Quick answer

> "On a tick processing path, every nanosecond costs you. Principles: no syscalls, no heap allocation, no exceptions, no virtual dispatch, no locks, no surprises. Branchless decision logic. Cache-resident hot data via prefetching and layout. Pinning threads to isolated cores. SPSC queues for cross-core communication. Profile with rdtsc, not gettimeofday."

### Detailed answer

> "Hot path latency at the nanosecond scale is mostly about *what you don't do*. The list of forbidden operations:
>
> - **Syscalls** — `getpid()` is ~50-100ns. `mmap`, `munmap`, anything that crosses kernel boundary kills latency.
> - **Heap allocation** — `malloc` is ~50-200ns. Pre-allocate everything; use pool allocators with bitmap tracking.
> - **Exceptions** — even *not throwing* costs nothing in modern compilers, but exception tables add code-size pressure on icache. We compile with `-fno-exceptions`.
> - **Virtual dispatch** — vtable indirection plus prevented inlining. Templates instead.
> - **Locks** — `pthread_mutex_lock` is ~30ns uncontended, ~1µs+ contended. Lock-free queues instead.
> - **Logging** — printf is ~1µs. Defer to slow path or async writer.
> - **Floating point** — non-deterministic, slower than integer ops. FPN instead.
>
> Things you DO do:
> - Pin threads to specific cores with `taskset`/`pthread_setaffinity_np`
> - Isolate those cores from kernel scheduler via `isolcpus`
> - Use real-time priority via `chrt -f 90`
> - Pre-touch all memory at startup so no minor page faults at runtime
> - Use SPSC queues for cross-thread communication
> - Branchless gate logic
> - Profile with rdtsc (cycle counter, ~30 cycles overhead) not gettimeofday (~50ns syscall)
>
> Net result on my engine: 37-47ns p50 per gate evaluation, ~200ns p99 with kernel preemption tail."

### Likely follow-ups

- **"What's `rdtsc`?"** → "Read Time-Stamp Counter — a CPU instruction that returns a 64-bit cycle counter. Fast (~30 cycles overhead). Pair with `lfence` or `cpuid` for serialization. Convert to nanoseconds via the CPU's nominal frequency. Caveat: on older CPUs the counter could vary across cores or with frequency scaling; modern Intel/AMD have invariant TSC."

- **"How do you handle NUMA?"** → "Pin threads to cores on the same NUMA node as the memory they access. Use `numactl` for binding. Cross-socket access is 2-3x slower than local. For my SPSC queues, producer and consumer are on cores in the same socket whenever possible."

- **"What's `__builtin_expect`?"** → "Branch hint to the compiler. `__builtin_expect(x, 0)` says 'expect x to be false.' Compiler arranges code so the expected path is the fall-through (no branch taken), which the CPU's static branch predictor handles well even on cold paths."

---

## 11. C++ Memory Model (the big picture)

### Quick answer

> "Every atomic operation has a memory ordering that constrains what other operations can be reordered around it. The model defines 'happens-before' relationships across threads via release/acquire pairs. If thread A's store-release happens-before thread B's load-acquire, then everything sequenced before A's store is visible to everything sequenced after B's load. This is how you reason about concurrent code without locks."

### Likely follow-up

- **"Sequenced-before vs happens-before vs synchronizes-with?"** → "Sequenced-before is within a single thread's program order. Synchronizes-with is the cross-thread relationship from a release store to a matching acquire load. Happens-before is the transitive closure — A happens-before B if A is sequenced-before B, or A synchronizes-with B, or there's a chain. The memory model defines which writes are visible to which reads via happens-before."

---

## Mental Model: How to Walk Through Your Engine

If they ask "explain your trading engine" — have a 5-minute spiel ready. Structure:

1. **Architecture** (1 min): "Per-core sharded. N execution cores, each pinned to a CPU. One producer thread reads market data and fans ticks across SPSC rings to each core. Each core is a branchless state machine: not-in-trade or in-trade. Slow path runs on a separate cadence — every ~100 ticks — to update gate parameters via seqlock."

2. **Hot path** (1 min): "The critical loop is `ExecutionCore_Tick`. Read tick. Evaluate buy gate against cached parameters: branchless mask AND of permission, bg_fires, !active. Evaluate sell gate similarly: active AND sg_fires. Push trade event to SPSC ring on rare branch. Mask-update active flag. ~30-40ns end to end on hot cache."

3. **Slow path** (1 min): "Separate thread drains TradeEvents from each core's ring. Updates portfolio, balance, P&L. Computes RegimeSignals from rolling stats every poll_interval. Pushes new gate parameters via seqlock so hot path picks them up without contention. Runs ML inference, kill switch evaluation, regime classification."

4. **Why it's fast** (1 min): "Branchless math means no mispredictions. FPN instead of float means deterministic and integer-fast. SPSC queues with cache-line-separated head/tail mean no MESI traffic between threads. Cached counters mean common-case ops never read remote cache lines. Pre-allocated everything — no malloc on the hot path. Pinned threads with isolated cores."

5. **Tradeoffs** (1 min): "Single producer means one thread for market data — a bottleneck if you wanted to multiplex many feeds. The seqlock-cached parameter pattern means slow path can preempt itself but readers are wait-free. Snapshot persistence requires careful versioning under partials. ML inference cost lives entirely on slow path so hot path latency is unaffected."

---

## Drill Schedule

Day 1: Sections 1, 2, 3 (lock-free + memory ordering + cache coherence). Read once, then close the doc and try answering each "Quick answer" out loud. Check yourself.

Day 2: Sections 4, 5, 6, 7 (TSO/ARM, progress guarantees, CAS, memory reclamation). Same drill.

Day 3: Sections 8, 9, 10 (branchless, FPN, hot-path engineering). Same drill.

Day 4: Section 11 + the engine walkthrough. Practice the 5-minute spiel out loud. Time it. Record yourself if you can stomach playback.

Day 5: Mock interview. Pramp, interviewing.io, or a friend. Even one mock collapses 80% of the nerves.

---

## Cheat tactics for the actual interview

1. **Get them to ask about your work first.** "Before we dive in, would it help if I gave you a quick architectural tour of the engine?" Most senior interviewers say yes. Now you're in show-mode, not test-mode.

2. **Slow down deliberately.** Take a sip of water before answering. The pause feels long to you but reads as thoughtful to them.

3. **Think out loud, even if it's wrong.** Interviewers grade on reasoning, not just answer. Walking through "I'd start with X because... wait, that has Y issue, so probably Z..." is exactly what they want to see.

4. **If you're stuck, say so.** "I haven't thought about this exact case before. Let me reason through it." Honesty beats panic.

5. **Connect to your code.** "My SPSC queue handles this case via..." beats "I think you'd do it like..." — you have a concrete reference, use it.

---

This sheet is yours. Edit it. Add the questions you actually got asked. Iterate.
