# Phase 6: Advanced Edge Cases & System Constraints

## NEW Ultra-Obscure Issues (49-58)

1. **OrderPool Capacity Mismatch & Out-of-Bounds** (`MemHeaders/PoolAllocator.hpp`)
   - **Details:** `OrderPool` uses a 64-bit bitmap but accepts a 32-bit capacity. If `capacity < 64`, `__builtin_ctzll(free_mask)` can return an index beyond the requested capacity, leading to silent out-of-bounds writes into adjacent memory.
2. **OrderPool_Free Undefined Behavior** (`MemHeaders/PoolAllocator.hpp`)
   - **Details:** `OrderPool_Free` lacks pointer validation. Passing a pointer outside the pool array results in a negative or out-of-bounds index calculation, causing UB via an invalid bit-shift (`1ULL << index`).
3. **InitArena_Owns Address Overflow** (`MemHeaders/InitArena.hpp`)
   - **Details:** The `InitArena_Owns` function calculates `ptr < arena->base + arena->capacity`. On 64-bit systems, if the arena sits high in memory, `base + capacity` can integer overflow, causing valid pointers to be falsely rejected.
4. **WebSocket Frame Read Heap Overflow** (`DataStream/BinanceUserData.hpp`)
   - **Details:** `ud_ws_read_frame` contains an integer casting bug (`signed` vs `unsigned` payload length). Large frames or crafted masking keys can bypass size checks, leading to a heap overflow.
5. **Trade ID Precision Loss via Double Cast** (`DataStream/BinanceUserData.hpp`)
   - **Details:** `ud_parse_execution_report` extracts 64-bit integer Trade IDs but casts them through a `double` intermediary during JSON parsing. This silently loses precision for large IDs, causing identical trade mappings and reconciliation failures.
6. **Thread-Safety Violation in Strategy Init** (`Strategies/StrategyLifecycle.hpp`)
   - **Details:** `Strategy_InitPerCore` performs allocations from `InitArena`. During live reconfigurations or multi-core initialization, multiple threads calling this concurrently will race on the `InitArena` bump pointer, corrupting memory.
7. **Inverted Risk Logic in Regime Transitions** (`Strategies/RegimeDetector.hpp`)
   - **Details:** `Regime_AdjustPositions` widens stop losses on LONG positions during trend breakdowns in an attempt to maintain static reward/risk ratios. This contradicts safe HFT practice, increasing drawdown exactly when risk should be tightened.
8. **Sign-Blindness in Regression Overfit Check** (`Backtest/OverfitDetection.hpp`)
   - **Details:** `OverfitDetection_CheckRegression` checks correlation gaps using a signed difference. If the out-of-sample correlation plunges to a large negative number, the signed check passes, failing to detect catastrophic overfitting.
9. **HTTP Chunked Encoding & Buffer Truncation** (`DataStream/BinanceOrderAPI.hpp`)
   - **Details:** `binance_rest_request` uses a fixed 8KB buffer and doesn't handle HTTP `Transfer-Encoding: chunked`. Large REST responses (e.g., full account info) are truncated, breaking the JSON parser downstream.
10. **SIMD Alignment Hazard in Replay State** (`DataStream/DepthReplayState.hpp`)
    - **Details:** `DepthReplayState_LoadDay` uses standard `calloc` for row storage, guaranteeing only 16-byte alignment. If `BookSnapshot` rows are processed via AVX-512 (which requires 64-byte alignment), it will cause immediate segmentation faults.