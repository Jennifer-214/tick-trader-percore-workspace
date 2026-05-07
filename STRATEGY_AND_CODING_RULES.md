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

## 7. Data Structure Locality & Touch Sites
Fetching scattered memory into the L1 cache is a primary source of memory latency.
* **Align and Pad**: Heavily contended variables (e.g., atomic permissions or `RollingStats` outputs read by the GUI) must be isolated onto their own cache lines using `alignas(64)` to prevent **False Sharing**.
* **Consolidate Touch Sites**: Do not scatter state updates. Group temporally related variables into cache-aligned structs so they can be copied in a single memory block.
* **Dense Lookup Tables**: Any configuration array or index mapping must be bounded, contiguous, and fit within an L1 cache line (64 bytes).

## 8. OS Jitter Mitigation
User-space thread pinning (`pthread_setaffinity_np`) is insufficient for sub-microsecond determinism.
* The execution cores must be protected from Linux kernel preemption.
* The deployment environment must boot with `isolcpus`, `nohz_full`, and `rcu_nocbs`.
* Thread priority must be elevated to `SCHED_FIFO` (`chrt -f 99`).
* IRQ affinity (NIC interrupts) must be explicitly routed away from the hot-path cores.