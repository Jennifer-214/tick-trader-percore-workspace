# Engine Latency & Optimization Audit

This document outlines potential optimizations to reduce latency and variance in both the hot path and slow path of the FoxML Trader engine, specifically targeting the i7-11850H hardware profile with AVX-512 capabilities, branchless execution, and memory hierarchy improvements.

---

## Part 1: Hot Path Optimizations (`ExecutionCore.hpp`)

The hot path (`ExecutionCore_Tick`) is already heavily optimized and primarily branchless, but there are several areas where tail latency and absolute throughput can be improved.

### 1. Compile-Time Elision of Latency Sampling
**Current:** Latency sampling uses `if (__builtin_expect(lat_enabled, 0))` via a relaxed atomic load. While predicted not-taken, the load and branch instruction still sit on the critical path, adding ~1ns and occupying execution ports.
**Optimization:** Convert `lat_enabled` into a template boolean parameter (e.g., `template <unsigned F, bool LAT_ENABLED>`). This allows the compiler to completely compile out the `rdtsc` and branch instructions when sampling is disabled, guaranteeing zero overhead.

### 2. AVX-512 Vectorization of Pipelined Gate Evaluations (Leg B)
**Current:** The secondary position leg (Leg B) evaluation (`sg_fires_b`) is branch-gated (`if (__builtin_expect(active_b, 0))`) because fixed-point comparisons on Leg B add ~40ns per tick due to instruction pipelining limits for `FPN<64>`.
**Optimization:** Using AVX-512 (`_mm512_cmpge_epu64_mask`), we can pack both Leg A and Leg B `FPN` comparisons into a single vectorized operation. This reduces the evaluation cost of both legs to a single cycle, allowing us to remove the `__builtin_expect` branch entirely and evaluate both legs unconditionally in 0ns extra latency.

### 3. Vectorized Active/Inactive CMOV Blending
**Current:** `FPN<F> tp = active ? core->live_tp : core->cached_params.sg_take_profit_price;` uses CMOV instructions to select the TP/SL thresholds without branching.
**Optimization:** With AVX-512, use `_mm512_mask_blend_epi64` to simultaneously blend the active/inactive thresholds for both Leg A and Leg B in one instruction rather than multiple sequential CMOV chains.

### 4. Branchless Ring Buffer Event Commits
**Current:** The event pusher uses `if (__builtin_expect(can_enter | can_exit_a | can_exit_b, 0))` to conditionally construct and push events into the ring buffer via `SPSCRing_TryPush`.
**Optimization:** Make the ring buffer commit completely branchless. Write the `TradeEvent` to the current ring buffer slot unconditionally, and advance the head pointer conditionally using: `head += (can_enter | can_exit)`. This removes the final remaining control-flow branch in the hot path.

### 5. False Cache Sharing on Permission Flag
**Current:** `uint8_t permission` is written by the controller thread (Atomic Release) and read by the hot path (Atomic Acquire). It shares cache line 0 with heavily accessed hot path variables like `active`, `entry_price`, `live_tp`, and `live_sl`.
**Optimization:** Move `permission` to a dedicated `alignas(64)` block to prevent the controller's writes from invalidating the execution core's L1 cache line, which otherwise causes a 30-50ns stall on the next tick.

---

## Part 2: Slow Path Optimizations (`RollingStats.hpp`, `FixedPointN.hpp`)

The slow path runs periodically (e.g., every 100 ticks) and computes regressions, features, and parameter packs.

### 1. AVX-512 Vectorization for Fixed-Point Math (`FixedPointN.hpp`)
**Current:** The arbitrary-width fixed-point library (`FPN<F>`) uses arrays of `uint64_t` words and relies on compiler loop unrolling (`#pragma GCC unroll`) with scalar carry chains for arithmetic (e.g., `FPN_MagAddN`, `FPN_MagSubN`).
**Optimization:** For `FPN<256>` or `FPN<512>`, leverage AVX-512 (`__m512i`) intrinsics. AVX-512 supports 512-bit wide integer registers, allowing parallel processing of 8x 64-bit words. We can implement vectorized operations to handle addition, subtraction, and especially multiplication across the entire FPN structure in a few instructions, eliminating sequential scalar carry dependencies.

### 2. O(1) Online Regression Updates (`LinearRegression3X.hpp`)
**Current:** `RollingStats_Push` and `LinearRegression3X_Fit` perform an O(W) loop (up to W=128) over the ring buffer every slow-path cycle to compute 5 sums for ordinary least squares (`sum_y`, `sum_y2`, `sum_xy`, etc.).
**Optimization:** Replace the O(W) recomputation with O(1) running sums. Since it's a fixed-size sliding window, subtract the evicted sample's contribution and add the new sample's contribution to the running sums. This reduces the regression step from ~128 iterations of fixed-point arithmetic to just a few O(1) operations, drastically cutting slow-path tail latency.

### 3. Replacing Fixed-Point Division with Multiplication
**Current:** `RollingStats_Push` performs division by `n_fp` (the current sample count, max W=128) using `FPN_DivNoAssert`. Fixed-point division of wide integers (like 256-bit or 512-bit) is iteratively branch-heavy and extremely slow.
**Optimization:** The denominator `n` is always an integer between 2 and `W`. We can precompute an array of `FPN<F>` reciprocals `1/n` at compile-time or initialization. The operation `FPN_DivNoAssert(sum, n_fp)` can then be replaced by `FPN_Mul(sum, precomputed_reciprocal[n])`, which is significantly faster and branchless.

### 4. Cache Line Padding in RollingStats
**Current:** `RollingStats` stores rapidly changing outputs (`price_avg`, `price_slope`) adjacent to internal ring-buffer management variables (`head`, `count`). The TUI/GUI thread reads these outputs via snapshot while the engine slow-path mutates them.
**Optimization:** Align and pad the read-heavy output variables (read by GUI/TUI) and the write-heavy variables (mutated by the engine) to 64-byte (L1 cache line size) or 128-byte boundaries using `alignas(64)`. This prevents false sharing where the GUI thread's reads invalidate the cache line for the engine's writes.

### 5. Branchless Wrap Refinements
**Current:** Ring buffer indices use `& (W - 1)` which is perfectly branchless. However, `count += (count < MAX_WINDOW)` creates a data dependency on a comparison result.
**Optimization:** On AVX-512 architectures, this can be further optimized using branchless `min` intrinsics or utilizing `cmov` more explicitly, though `count` typically stabilizes quickly to `W` and then remains constant.

---

## Part 3: Architectural & Structural Optimizations

Beyond local code optimizations, maintaining low latency requires strict adherence to overarching structural design invariants.

### 1. Zero-VTable Architecture
**Status:** An audit of `CoreFrameworks` and `Strategies` confirms the codebase is entirely free of `virtual` functions and dynamic dispatch.
**Optimization/Invariant:** Strict enforcement of zero dynamic polymorphism in the hot and slow paths. `virtual` functions introduce vtable lookups resulting in indirect jumps that bypass the CPU's branch predictor, leading to pipeline stalls. Strategy dispatch should continue to use switch/case on flat enumerations or template monomorphization.

### 2. Lookup Table Locality
**Current:** Parameter packs and small arrays are used for state tracking.
**Optimization:** Any lookup tables (such as index-to-strategy mappings or configuration arrays) must be bounded and contiguous. If lookup tables grow, they must be explicitly padded and aligned to fit entirely within L1 cache lines (64 bytes). Avoid sparse tables or hash maps in favor of dense, flat arrays where index calculation is purely arithmetic.

### 3. Reducing Memory Touch Sites
**Current:** The architecture already packs gate parameters into the `GateParameters` struct.
**Optimization:** As new features are added, prevent "touch site sprawl." Rather than scattering state updates across multiple disparate global or class-level variables, group temporally related variables into cache-aligned structs. When the slow path pushes an update, it should copy a single contiguous block of memory (e.g., via the existing `ParameterSlot` seqlock) to minimize the number of cache lines the hot path must fetch.

---

## Part 4: Data Ingestion, ML Inference, and Memory Subsystem

Expanding the audit beyond the core engine into peripheral paths reveals additional bottlenecks in data parsing, model execution, and memory allocation.

### 1. Ingestion: Scalar JSON Parsing (`BinanceCrypto.hpp`)
**Current:** The WebSocket trade parser `binance_parse_trade` uses scalar C library functions (`strstr`) to locate keys like `"p"` and `"q"` in raw JSON byte streams.
**Optimization:** Replace scalar `strstr` with AVX-512 vectorized string search algorithms, or utilize a SIMD-accelerated JSON parser like `simdjson`. Scanning 64 bytes at a time for structural characters will drastically reduce the time it takes to parse tick data and get it into the `ExecutionCore_Tick` loop.

### 2. OMS: Artificial Sleep Tail Latency (`BinanceAdapter.hpp`)
**Current:** `BinanceAdapter_WorkerLoop` polls the `submission_queue` using `SPSCRing_TryPop`. If the queue is empty, it calls `std::this_thread::sleep_for(std::chrono::microseconds(200))`. This guarantees up to 200μs of added latency to any order that arrives while the worker is sleeping.
**Optimization:** Eliminate `sleep_for`. Replace the polling mechanism with an adaptive spin-wait utilizing CPU pause instructions (`_mm_pause()`) for immediate arrival detection, falling back to an OS-level wait (like `futex` or `std::condition_variable`) only after an extended idle period.

### 3. ML Inference: External C API Overhead (`ModelInference.hpp`)
**Current:** `CoreModelZoo` delegates inference to the XGBoost or LightGBM C APIs. While fast (~1-5μs), these external libraries are primarily optimized for batch processing and carry internal conversion and dynamic dispatch overheads.
**Optimization:** For the slow path, 1-5μs is acceptable, but for ultimate tail-latency reduction, the trained trees should be ahead-of-time (AOT) compiled directly into C++ code (e.g., using Treelite or an internal transpiler). We can also use AVX-512 to evaluate multiple trees in parallel, bringing single-row inference down to <100ns.

### 4. Memory: O(N) Buddy Allocator Search (`BuddyAllocator.hpp`)
**Current:** `buddy_alloc_bytes` uses a `for` loop to scan up to 17 orders (`BUDDY_NUM_ORDERS`) looking for the next available block size. (Note: There is also a typo in `buddy_internal_order_to_size` where `1u < order` is used instead of `1u << order`).
**Optimization:** Track the availability of free blocks using a single `uint32_t` bitmask. Finding the next available order becomes a completely branchless O(1) operation using the `__builtin_ctz` (Count Trailing Zeros) intrinsic, mapping perfectly to hardware bit-scan instructions.

---

## Part 5: Algorithm & Strategy Level Optimizations

### 1. Exp3-IX Bandit Learning Vectorization (`BanditLearning.hpp`)
**Current:** The `BanditState` tracks up to 8 strategy arms (`BANDIT_MAX_ARMS = 8`) using standard arrays of double-precision floats (`weights[8]`, `cum_reward[8]`). Functions like `Bandit_GetProbabilities` and `Bandit_Update` execute scalar `for` loops across all 8 indices to perform additions, normalizations, and exponentiations.
**Optimization:** Because the maximum number of arms is exactly 8, the entire state array fits perfectly into a single 512-bit AVX-512 register (`__m512d`). By utilizing intrinsics (`_mm512_add_pd`, `_mm512_div_pd`, `_mm512_max_pd`, `_mm512_exp_pd`), we can eliminate the loops completely and compute the probability distribution, max weights, and importance-weighted reward updates for all 8 arms in parallel with single instructions.

---

## Part 6: System & OS Level Tail Latency Variance

Examining the codebase for sources of extreme tail latency variance (p99.9, p99.99) reveals issues involving I/O, dynamic allocations, and OS-level preemption that can cascade into the hot path.

### 1. Cascading Stalls from Synchronous I/O (`OrderEventLog.hpp`)
**Current:** `OrderEventLog_Append` writes through to disk synchronously using `std::fwrite` and calls `std::fflush` every 16 events. Because this runs on the central OMS/drainer thread, any disk I/O latency stall directly blocks the drainer. If the drainer is blocked, the execution cores' `event_ring` (SPSC queues) back up and fill. When full, `ExecutionCore_Tick` fails its `SPSCRing_TryPush`, leading to dropped events and "zombie" positions on the hot path.
**Optimization:** Decouple all file I/O from the OMS/drainer thread. The drainer should append events to a lock-free queue consumed by a dedicated asynchronous background logging thread, ensuring disk stalls never backpressure the execution cores.

### 2. Dynamic Memory Allocation in the Event Path (`OrderEventLog.hpp`)
**Current:** `OrderEventLog_Append` uses `std::realloc` to double its buffer size when capacity is reached. This is an unbounded `O(N)` operation that requires OS page allocation and memory copying, completely stalling the OMS thread during the reallocation.
**Optimization:** Pre-allocate the maximum necessary log capacity at startup. To ensure physical memory is actually backed, use `mmap` with `MAP_POPULATE` or `madvise(MADV_WILLNEED)` to pre-fault pages. If dynamic growth is strictly necessary, use a segmented list of chunks (e.g., a lock-free list of 16KB arrays) rather than a contiguous `realloc` that forces a copy of all historical events.

### 3. OS Scheduling Jitter & Kernel Preemption
**Current:** The engine uses `pthread_setaffinity_np` to pin execution cores (via `EngineSharded_PinThread`). However, standard user-space pinning does not prevent the Linux kernel from preempting those threads to run RCU callbacks, timer interrupts, or other system tasks.
**Optimization:** For deterministic sub-microsecond tail latency, user-space pinning must be paired with kernel-level isolation.
- Boot the OS with `isolcpus`, `nohz_full`, and `rcu_nocbs` for the designated execution cores.
- Set the hot path threads to real-time priority using `SCHED_FIFO` (`chrt -f 99`).
- Ensure the network card's IRQ affinity is routed away from the hot path execution cores to dedicated I/O or background cores.

---

## Part 7: Complete Eradication of System Allocators (`malloc` / `new`)

While the hot path avoids dynamic allocation, the slow path, initialization phases, and the OMS drainer currently rely on system allocators (`malloc`, `calloc`, `realloc`, `new`), which introduce non-deterministic OS-level locks and page faults.

### 1. `OrderEventLog` Reallocation
**Current:** As noted in Part 6, `OrderEventLog_Append` uses `std::realloc` to dynamically grow its array on the slow path/OMS drainer.
**Optimization:** Completely eradicate `std::realloc`. Allocate a static contiguous block from a custom memory pool (like `BuddyAllocator` or a pre-allocated slab) at initialization. If growth is necessary, use a chunked linked-list of fixed-size slabs drawn exclusively from the pre-allocated pool, preventing OS page faults during trading.

### 2. Initialization Allocations (`PortfolioController`, `ControllerEventLoop`)
**Current:** During engine startup, large structs like `RollingStats` and `CoreSlowState` are allocated using `malloc` or `new` (e.g., `ctrl->rolling_long = malloc(...)`).
**Optimization:** Even for startup allocations, the engine must transition to a unified custom memory arena (`BuddyAllocator` or a dedicated monolithic `mmap` arena). This eliminates `malloc` entirely, improves spatial locality (keeping all engine state packed closely in physical memory), and allows the entire arena to be explicitly backed by huge pages (`MAP_HUGETLB`) and pre-faulted (`MAP_POPULATE`).

### 3. PoolAllocator Bootstrapping (`PoolAllocator.hpp`)
**Current:** The existing `PoolAllocator` utilizes `calloc` during initialization (`pool->slots = calloc(...)`).
**Optimization:** Refactor the `PoolAllocator` and all other custom allocators to draw from a statically allocated `.bss` buffer or a single global `mmap` block at startup. No part of the custom allocators should depend on `libc`'s memory management.

### 4. String and Buffer Management (`DataStream`)
**Current:** The data ingestion streams and TLS layers (like `BinanceCrypto.hpp` and `BinanceAdapter.hpp`) can sometimes trigger implicit allocations depending on the TLS library or string processing used.
**Optimization:** Enforce a strict zero-allocation policy. All network buffers, JSON parsers, and string builders must use statically sized stack buffers or pre-allocated slabs from the `PoolAllocator`. No `std::string` or `std::vector` should be utilized in `DataStream` or `CoreFrameworks` during runtime execution.

---

## Part 8: WebSocket and Order Parsing Efficiency

Handling bursts of market data without falling behind requires extreme efficiency at the ingestion layer. The current parsing implementations in `DataStream` rely on repeated scalar string operations that scale poorly with message size.

### 1. O(N*K) JSON Extraction Penalty (`BinanceUserData.hpp`, `BinanceOrderAPI.hpp`)
**Current:** The execution report parser (`ud_parse_execution_report`) extracts 10 separate fields from the JSON payload by calling `binance_json_extract_*` 10 times. Each call executes `strstr(json, search)`, which iterates through the entire JSON string from the beginning to find the key. For a message of length `N` and `K` keys, this is an `O(N * K)` operation. Under high burst volumes, this repeated scanning will cause the WebSocket thread to fall behind.
**Optimization:** Implement a single-pass JSON tokenizer. Utilizing SIMD instructions (like AVX-512) or a dedicated parser like `simdjson`, the entire JSON object can be structurally mapped in a single `O(N)` pass, allowing all 10 keys to be extracted simultaneously without rescanning the payload.

### 2. Float Parsing Overheads (`BinanceOrderAPI.hpp`)
**Current:** Numeric values like `fill_price` and `fill_qty` are extracted as substrings, copied into a small stack buffer (`char buf[64]`), null-terminated, and then parsed using the standard C library function `atof(buf)`. `atof` is notoriously slow and branch-heavy as it handles locales, scientific notation, and generic edge cases.
**Optimization:** Replace `atof` with a fast, locale-independent, and branchless float parser (e.g., `fast_float` or a custom parser designed specifically for Binance's strict decimal formats). Furthermore, extract these directly into the fixed-point (`FPN<F>`) representation where possible, skipping the intermediate double-precision float representation entirely.

---

## Part 9: Order Management System (OMS) Variance

The OMS is the central hub for dispatching and reconciling orders. The drainer thread must remain fully unblocked to prevent the hot path execution cores from stalling.

### 1. Serial Polling of SPSC Queues (`OrderManager.hpp`)
**Current:** `OMS_DrainSubmit` loops over all `MAX_EXECUTION_CORES` and performs `SPSCRing_TryPop` on each core's dedicated submit queue serially. This linear `O(C)` scan introduces cache-miss variance depending on which core pushes an order and which queue is checked first.
**Optimization:** Replace the multiple `MAX_EXECUTION_CORES` SPSC queues with a single Multi-Producer Single-Consumer (MPSC) lock-free queue or an event-driven mechanism (e.g., using `eventfd` or `io_uring` for immediate wakeups). This guarantees `O(1)` order arrival handling on the drainer thread without continuous polling across empty queues.

### 2. O(N) Order ID Lookups (`OrderManager.hpp`)
**Current:** `OrderManager_ProcessFillCommand` performs a linear `O(N)` scan over the `MAX_INFLIGHT_ORDERS` bitmap to match the incoming `cmd.order_id` to an active `orders[]` slot. While `N` is small, linear scans still introduce unnecessary variance.
**Optimization:** Achieve `O(1)` Order Lookup. Instead of scanning to match `cmd.order_id`, embed the `slot_id` directly into the `clientOrderId` string sent to Binance (e.g., `oms_<id>_<slot>`). When the execution report arrives, parse the slot index directly for an instantaneous `O(1)` array lookup.