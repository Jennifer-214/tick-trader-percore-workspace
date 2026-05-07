# FoxML Trader v2

This project is a high-frequency trading (HFT) engine targeting sub-microsecond latency. It operates with extreme architectural invariants to guarantee deterministic execution and eliminate tail variance.

## Architectural Invariants (HFT Requirements)

When assisting with this project, you MUST adhere strictly to these rules:

1. **Zero System Allocators:** Never use `malloc`, `calloc`, `realloc`, `new`, `std::string`, `std::vector`, or `std::map`. All dynamic allocations occur at startup. Use `PoolAllocator` or `BuddyAllocator`.
2. **Zero VTables:** Never use `virtual` functions. Use flat enumerations, template monomorphization, and X-Macros.
3. **Lock-Free Concurrency:** Never use `std::mutex`, `std::lock_guard`, or `std::this_thread::sleep_for`. Use Seqlocks (`ParameterSlot`), MPSC rings, and adaptive spin-waits (`_mm_pause()`).
4. **Branchless Hot Path:** Eliminate `if` statements on the hot execution path. Use bitwise arithmetic, AVX-512 `cmov` instructions, and template elision.
5. **AVX-512 Vectorization:** Design algorithms (like Machine Learning models and Fixed-Point Math) to map directly to 256-bit or 512-bit registers. Refactor $O(N)$ operations into $O(1)$ running sums.
6. **O(N) Single-Pass Parsing:** Never use `strstr` in a loop for JSON parsing or standard `atof` for floats. Use SIMD tokenizers (`simdjson`) and branchless float parsers.
7. **L1 Cache Optimization:** Keep hot path arrays dense. Prevent False Sharing by aligning cross-thread variables with `alignas(64)`. Consolidate memory touch sites into cache-aligned structs.
8. **OS & Kernel Tuning:** The deployment assumes `isolcpus`, `nohz_full`, `TCP_NODELAY`, `mlockall`, `SCHED_FIFO` priorities, and Huge Pages (`MAP_HUGETLB`). Do not rely on OS-level buffering.

## Documenting Plans & Audits

- The primary source of truth for upcoming tasks lives in the `tick-trader-percore-workspace` private repository.
- Changes to strategies, architecture, or latency optimizations should be appended to `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` and `DOCS/STRATEGY_AND_CODING_RULES.md`, and then pushed to the private workspace for backup.
- Use `/plan-check` to identify integration gaps between upcoming sprint plans.