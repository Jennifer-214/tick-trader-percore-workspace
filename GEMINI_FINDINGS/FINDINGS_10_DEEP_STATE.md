# Phase 10: Deep State & Memory Ordering

## NEW Ultra-Obscure Issues (89-98)

1. **ParameterSlot Seqlock Tear on Acquire Ordering** (`CoreFrameworks/ParameterSlot.hpp`)
   - **Severity:** CRITICAL
   - **Details:** `ParameterSlot_Read` uses `std::memory_order_acquire` for the second sequence load. While this prevents subsequent reads from moving before it, it *does not* prevent the preceding data buffer reads from being reordered *after* it by the compiler or CPU (load-load reordering). This violates the seqlock invariant, risking torn reads on weakly-ordered architectures.
2. **Short Position Logic Inversion** (`CoreFrameworks/Portfolio.hpp`)
   - **Severity:** CRITICAL
   - **Details:** `PositionExitGate` and related evaluation logic are hardcoded for long positions (e.g., `price >= TP` or `price <= SL`). If a short position is entered (`quantity < 0`), the logic will trigger an immediate false exit or fail to exit completely when the price moves against the position.
3. **Multi-Word Torn Read in KillSwitch** (`CoreFrameworks/EngineSharded.hpp`)
   - **Severity:** CRITICAL
   - **Details:** The producer thread reads `oms->balance` (a 64-word FPN structure) while the drainer thread writes to it. Because `FPN<64>` cannot be read atomically, the producer can read a partially updated, torn balance, leading to massive false spikes and triggering the emergency kill switch.
4. **Bandit JSON Order Dependency** (`ML_Headers/BanditLearning.hpp`)
   - **Severity:** MEDIUM
   - **Details:** `Bandit_LoadJSON` searches for regime states using `strstr` moving strictly forward through the file buffer. If the JSON keys are not strictly alphabetically/sequentially ordered, the loader will miss them and fail to load specific regime states.
5. **Truncated Hashing Vulnerability** (`MemHeaders/HmacSha256.hpp`)
   - **Severity:** HIGH
   - **Details:** `sha256_file_hex_inproc` uses `fread` in a loop but ignores potential read errors. If `fread` fails mid-file (e.g., due to a disk stall), the loop terminates and produces a valid SHA256 hash for a partially read file, tricking the system into verifying a corrupted model stamp.
6. **Partial State Mutation on IO Failure** (`CoreFrameworks/Portfolio.hpp`)
   - **Severity:** HIGH
   - **Details:** `Portfolio_Load` mutates the `active_bitmap` before all corresponding position fields and the total balance are successfully read from disk. If the read fails mid-way, the portfolio is left in an inconsistent zombie state with active bits but corrupted data.
7. **Latency Percentile Skew** (`CoreFrameworks/CoreLatencyStats.hpp`)
   - **Severity:** LOW
   - **Details:** `CoreLatencyStats_Sample` increments `total_count` *before* writing the actual sample to the ring buffer. If `CoreLatencyStats_Snapshot` reads concurrently, it will include an uninitialized or extremely old sample from the ring, drastically skewing p99 latency metrics.
8. **Bandit Weight Tearing** (`ML_Headers/BanditLearning.hpp`)
   - **Severity:** MEDIUM
   - **Details:** `BanditState` lacks synchronization between the slow-path weight update/normalization and the TUI/GUI thread reads. The GUI can read weights mid-normalization, displaying non-1.0 sums or corrupted blending ratios.
9. **Topology Race Condition** (`CoreFrameworks/EngineSharded.hpp`)
   - **Severity:** HIGH
   - **Details:** The `topo_slow_cpu` array is populated by the main thread but read concurrently by the producer thread (via `fan_out`) without atomics or fences, leading to undefined behavior and potential mis-pinning if read during initialization.
10. **Silent Truncation in JSON Loader** (`ML_Headers/BanditLearning.hpp`)
    - **Severity:** MEDIUM
    - **Details:** `Bandit_LoadJSON` fails to verify the return value of `fread` against the expected file size. If a short read occurs, it processes the truncated JSON buffer without warning, risking a silent fallback to default weights.