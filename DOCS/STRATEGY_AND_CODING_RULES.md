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
  * Use fast, locale-independent parsers (e.g., `fast_float`) or parse directly to `FPN_Binary<F>`.

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

## 10. Memory Pages & TLB
Standard 4KB OS pages lead to Translation Lookaside Buffer (TLB) misses, triggering high-latency walks to RAM.
* **Huge Pages**: All critical custom allocators and memory blocks MUST be backed by 2MB or 1GB Huge Pages.
* **How**: Map arenas using `mmap` with the `MAP_HUGETLB` flag to dramatically reduce the page table footprint.

## 11. Hardware & Kernel Tuning
Software optimization stops mattering if the hardware decides to sleep or interrupts fire unexpectedly.
* **CPU Sleep States**: Disable deep C-states and P-states in the Linux boot parameters (`intel_idle.max_cstate=0`, `processor.max_cstate=0`) and use the `performance` CPU governor. Cores must never sleep.
* **NUMA Architecture**: Guarantee memory locality. The thread, its memory allocations, and the NIC interrupts must all reside on the exact same NUMA node to prevent slow cross-socket QPI/UPI links.

---

## H16. Metadata Bit ↔ Derived Filter (Structural Completeness Invariant) — Codified v5.15.5.F.4d 2026-05-16

Every bit in `CfgFieldDescriptor::MetadataFlag` enum (at `CoreFrameworks/CfgFieldRegistry.hpp:129-149`) MUST satisfy ONE of:
1. **Have a derived filter row** in `FOREACH_DERIVED_FILTER` meta-registry (declaring the auto-flow consumer); OR
2. **Have a documented exemption** with rationale in `MANUAL_FIELDS_INVENTORY.md` Section D or equivalent.

* **Why**: A metadata bit without a derived filter is a SILENT FAILURE MODE — fields flagged with the bit accumulate, but no consumer walks them; the bit becomes vestigial. CI Check `test_metadata_bit_to_derived_filter_coverage` enforces by enumerating MetadataFlag enum entries + asserting each has a `FOREACH_DERIVED_FILTER` row OR an explicit-exempt entry.
* **How**: Adding a new metadata bit = (a) bit allocation in enum (`1u << N`); (b) row in `FOREACH_METADATA_BIT` X-macro at `CfgFieldRegistry.hpp:1043+` for per-bit precomputed mask auto-generation; (c) row in `FOREACH_DERIVED_FILTER` at the meta-registry declaring consumer variant (GUI_ONLY / WIRE_FORMAT / WIRE_FORMAT_TWO_SOURCE) + locked-hash constant if wire-format.
* **Anti-pattern**: adding a metadata bit + flagging fields with it + writing per-field walker code by hand. Fix: declare a `FOREACH_DERIVED_FILTER` row + use `DERIVED_FILTER_DECLARE_*` macro to auto-generate the walker.
* **Cross-ref**: `DESIGN_SPECS/framework-patterns/metadata-bit-driven-derived-filter-framework.md` (canonical pattern body); `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md` (sister H15 + H19 invariants); CLAUDE.md table row H16.
* **First canonical**: `STAMP_BOUND_CFG_DERIVED` metadata bit @ bit 13 + `FOREACH_DERIVED_FILTER` first row (STAMP_BOUND_CFG variant; WIRE_FORMAT_TWO_SOURCE). Codified at v5.15.5.F.4d ship close 2026-05-16.

## H17. Cfg Struct Fields Auto-Generated From `FOREACH_CFG_FIELD` (Structural Integrity Invariant) — Codified v5.15.5.F.4d 2026-05-16

`ControllerConfig<F>` cfg struct fields MUST be auto-generated from `FOREACH_PER_CORE_CFG_FIELD` + `FOREACH_GLOBAL_CFG_FIELD` X-macro registries (at `CoreFrameworks/CfgFieldRegistry.hpp`). NO manual cfg field declarations.

* **Why**: Manual cfg field declarations drift from registry over time → Class 18 mirror-incomplete bug class. When parser / save / drift-check / GUI render code walks the registry but a field exists ONLY in the struct (not the registry), that field is invisible to all auto-flows. Discovered via paper-test surfacing at v5.15.5.F.4c.1 (`ml_buy_threshold` had registry row but missing STAMP_BOUND descriptor flag — auto-flows silently skipped it).
* **How**: `PerCoreCfg<F>` struct body MUST contain ONLY `FOREACH_PER_CORE_CFG_FIELD` + `FOREACH_PER_CORE_DOMAIN_BITMAP` X-macro invocations (no manual field declarations); CI Check 2 (`tools/check_per_core_registry_integrity.py`) since v5.15.5.F.4c enforces. Same shape extends to `ControllerConfig<F>` body via `FOREACH_GLOBAL_CFG_FIELD` post-`.F.4d`.
* **Anti-pattern**: adding a new cfg field as a manual struct field declaration ("just one quick addition"). Fix: add to FOREACH_*_CFG_FIELD X-macro instead — parser + save + drift-check + GUI render all auto-flow from registry row.
* **Exception**: parallel arrays declared via `FOREACH_MANUAL_PER_CORE_FIELD` X-macro (Section A of MANUAL_FIELDS_INVENTORY.md; 12 entries; CI Check 3 enforces) — these are NOT cfg fields but per-node state arrays that need parallel slot allocation; tracked in a sister X-macro registry for the same single-source-of-truth discipline.
* **Cross-ref**: `DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md`; `DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md` (bitmap dispatcher framework canonical at `.F.4c`); CLAUDE.md table row H17.
* **First canonical**: `FOREACH_PER_CORE_CFG_FIELD` at `.F.4c` (93 rows; PerCoreCfg<F> body now ONLY X-macro). H17 codified to make the discipline permanent at v5.15.5.F.4d ship close 2026-05-16.

---

## Note on numbering: H1-H14 + H20 in CLAUDE.md; H15/H18/H19 in CLAUDE.md; H16/H17 here (private overlay)

The CLAUDE.md Hard Invariants table is the public-facing canonical list (always loaded; broad framework-discipline visibility). This private overlay extends with structural-detail invariants H16 + H17 (codified `.F.4d`) that benefit from the longer-form treatment available here (Why + How + Anti-pattern + Exception + Cross-ref + First canonical).

The 11 numbered sections above (Memory Management / Dispatch & Polymorphism / Concurrency / etc.) predate the H<N> numbering convention and remain the canonical strict-invariant detail reference for the foundational HFT discipline. H15-H20 are additional metadata-discipline + framework-discipline invariants that compose ON TOP of the foundational 11.
* **NIC Tuning**: Disable adaptive interrupt coalescing on the network interface (`ethtool -C eth0 rx-usecs 0 rx-frames 0`) to receive packets immediately.