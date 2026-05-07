# FoxML Trader: Strategy & Coding Rules
**Derived from the Latency Optimization Audit (v5.x)**

This document defines the strict architectural and coding invariants required to maintain sub-microsecond latency, deterministic execution, and zero tail-variance in the FoxML Trader engine. When building new strategies, modifying the execution core, or integrating new feeds, you **must** adhere to these rules.

---

## 1. Memory Management: Zero System Allocators
Dynamic memory allocation causes non-deterministic OS-level locks, page faults, and ruins spatial locality.
* **NO `malloc`, `calloc`, `realloc`, or `new`**: These are strictly forbidden in the hot path, slow path, and event drainers.
* **NO `std::vector`, `std::string`, or `std::map`**: STL containers implicitly allocate.
* **What to use instead**: 
  * Use statically sized arrays (e.g., `char buf[64]`).
  * Use the custom `PoolAllocator` or `BuddyAllocator` drawing from a pre-allocated, `MAP_POPULATE` (pre-faulted) `mmap` arena.
  * For growing arrays (like event logs), use a lock-free chunked linked-list of fixed-size slabs drawn from a custom memory pool.

## 2. Dispatch & Polymorphism: Zero VTables
Dynamic dispatch introduces vtable lookups and indirect jumps, which bypass CPU branch predictors and cause pipeline stalls.
* **NO `virtual` functions**: The codebase must remain 100% devirtualized.
* **What to use instead**: 
  * For strategy dispatch, use template monomorphization or `switch/case` over flat, contiguous enumerations (`StrategyId`).
  * Use X-Macros for generating static dispatch tables (as seen in `StrategyInterface.hpp`).

## 3. Concurrency: Lock-Free & Wait-Free Only
Standard synchronization primitives induce OS context switches and scheduling jitter.
* **NO `std::mutex`, `std::lock_guard`, or `std::condition_variable`**.
* **NO `std::this_thread::sleep_for()`**: Never artificially sleep on an active polling thread (e.g., OMS worker loops).
* **What to use instead**:
  * **SPSC/MPSC Rings**: Use lock-free rings for cross-thread messaging.
  * **Seqlocks**: Use the `ParameterSlot` pattern for hot-path data handoffs. A writer should never block, and a reader should detect tears via odd/even sequence counters. Do *not* rely on unprotected double-buffering.
  * **Adaptive Spin-Waits**: Use `_mm_pause()` (CPU pause instructions) when waiting for events.

## 4. Branchless Execution
Branches inside the hot-path loop cost execution ports and branch-prediction penalties.
* **Eliminate `if` statements in critical sections**: Especially those depending on data (e.g., `if (price > threshold)`).
* **Compile-time elision**: Use template booleans (e.g., `template <bool LAT_ENABLED>`) to allow the compiler to compile out feature flags completely instead of checking `__builtin_expect` at runtime.
* **What to use instead**:
  * Use bitwise arithmetic: `head += (can_enter | can_exit)` instead of `if (can_enter || can_exit) head++;`.
  * Rely on AVX-512 masked operations and `cmov` instructions.

## 5. Structuring for AVX-512 Vectorization
New algorithms (especially ML and Strategies) must be designed to map directly to SIMD hardware.
* **Data alignment**: Design arrays to fit cleanly into 256-bit or 512-bit registers. For example, a bandit tracking 8 strategy arms (`double weights[8]`) fits perfectly in a single `__m512d` register.
* **Horizontal operations**: Avoid scalar `for` loops (like `O(W)` running sums) on the slow path. Convert sliding window logic to `O(1)` running sums.
* **Fixed-Point math**: Replace slow, multi-branch arbitrary-width fixed-point divisions with precomputed array multiplications (`FPN_Mul(sum, precomputed_reciprocal[n])`).

## 6. Parsing & Ingestion: O(N) Single-Pass Only
Network ingestion cannot fall behind during market bursts.
* **NO scalar JSON searches**: Do not use `strstr` inside a loop to extract multiple JSON keys (which results in an `O(N*K)` scan).
* **NO `atof`**: Avoid the C standard library float parser, as it is branch-heavy and slow.
* **What to use instead**:
  * Use SIMD-accelerated JSON parsers (e.g., `simdjson`) for single-pass `O(N)` extraction.
  * Use fast, locale-independent parsers (e.g., `fast_float`) or parse directly to `FPN<F>`.

## 7. Memory Hierarchy & L1 Cache Optimization
Fetching data from main RAM costs ~100ns (hundreds of CPU cycles), which absolutely destroys sub-microsecond latency. The hot path must execute entirely out of the L1/L2 cache.
* **Prioritize L1 Cache**: Ensure that all critical path variables, state arrays, and lookup tables are small enough to remain resident in the 32KB L1 data cache.
* **Cache Alignment (`alignas(64)`)**: Variables read and written by different threads (e.g., atomic permissions, `TUISnapshot` buffers, `RollingStats` GUI outputs) MUST be isolated on their own 64-byte cache lines using `alignas(64)`.
* **Prevent False Sharing**: Never pack variables mutated by the hot path on the same cache line as variables mutated by the slow path or GUI. Doing so causes cross-core cache invalidation storms and massive tail latency spikes.
* **Consolidate Touch Sites**: Do not scatter state updates across disparate memory locations. Group temporally related variables into cache-aligned, contiguous structs so they are fetched into L1 cache with a single memory load.
* **Dense Arrays over Pointers**: Use dense, flat arrays where index calculation is pure arithmetic. Avoid pointer chasing (e.g., linked lists, trees, hash maps) on the hot path, as each pointer dereference risks an L1 cache miss and forces a slow RAM fetch.

## 8. OS Jitter Mitigation
User-space thread pinning (`pthread_setaffinity_np`) is insufficient for sub-microsecond determinism.
* The execution cores must be protected from Linux kernel preemption.
* The deployment environment must boot with `isolcpus`, `nohz_full`, and `rcu_nocbs`.
* Thread priority must be elevated to `SCHED_FIFO` (`chrt -f 99`).
* IRQ affinity (NIC interrupts) must be explicitly routed away from the hot-path cores.

## 9. Advanced System & Compiler Optimizations
Sub-microsecond determinism requires controlling the OS and CPU at the lowest levels.
* **Disable Nagle's Algorithm**: All TCP sockets must be initialized with `TCP_NODELAY`. An order submission must hit the wire immediately, not wait in an OS buffer.
* **Lock Memory Pages**: The engine must call `mlockall(MCL_CURRENT | MCL_FUTURE)` on boot to prevent the Linux kernel from ever paging out critical execution memory.
* **Flush Denormals (FTZ/DAZ)**: The `main()` function must configure the CPU's `MXCSR` register to flush subnormal floating-point numbers to zero (`_MM_SET_FLUSH_ZERO_MODE`). Denormals cause catastrophic FPU microcode stalls.
* **Compiler Flags**: Production binaries must be built with `-O3`, `-march=native`, Link-Time Optimization (`-flto`), and ideally Profile-Guided Optimization (PGO) to maximize instruction cache alignment.