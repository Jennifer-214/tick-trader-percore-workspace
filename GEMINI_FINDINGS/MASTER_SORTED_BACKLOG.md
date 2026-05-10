# FoxML_Trader_v2 - Master Sorted Backlog (Phases 1-10)

This document contains all 98 findings discovered during the 10-phase deep codebase audit, meticulously sorted by severity to prioritize engineering and patching efforts.

## 🔴 CRITICAL (Data Corruption, Deadlocks, Vulnerabilities, UB)
*These issues pose immediate risks to engine stability, capital safety, or mathematical determinism.*

1. **`SPSCRing` Concurrency Hazard in OrderManager** (`CoreFrameworks/OrderManager.hpp`) - Uses `result_queue` with multi-worker threads, risking race conditions.
2. **`BuyGate` Precision Logic Bug** (`CoreFrameworks/OrderGates.hpp`) - "inline positive-FPN comparison" ignores middle words for $F > 64$, breaking threshold evaluations.
3. **`BinanceAdapter` Worker Loop SPSC Hazards** (`CoreFrameworks/BinanceAdapter.hpp`) - SPSC rings used in multi-consumer patterns causing API query races.
4. **`BinanceUserData` Keepalive Race Conditions** (`DataStream/BinanceUserData.hpp`) - `rest_api` shared between WS/keepalive threads unsynchronized.
5. **`OrderManager` Partial Fill State Divergence** (`CoreFrameworks/OrderManager.hpp`) - Incorrectly frees slots on `ORDER_PARTIAL`, dropping subsequent fills.
6. **ExecutionCore Entry Deadlock on Full OMS** (`CoreFrameworks/ExecutionCore.hpp`) - Cores deadlock in an 'active' state if the OMS table rejects a submission.
7. **FP64 Multiplication Carry-Propagation Bug** (`FixedPoint/FixedPoint64.hpp`) - Missing carry-propagation in 128-bit math yields incorrect products.
8. **FauxFIX Stack Buffer Overflow** (`DataStream/FauxFIX.hpp`) - `FIX_BuildMarketDataMsg` lacks bounds checks, risking critical stack overflows.
9. **Timing Attack Vulnerability in Model Stamps** (`ML_Headers/ModelInference.hpp`) - Uses `strcmp` for HMAC signature verification, allowing side-channel deduction.
10. **Reconciliation Logic Error** (`CoreFrameworks/ReconciliationLoop.hpp`) - Ignores `PARTIALLY_FILLED` orders, causing false drift detections.
11. **GUI TradeReader Race Condition** (`GUI/TradeReader.hpp`) - Unsynchronized CSV reads in the GUI thread observe partial engine writes.
12. **Strict Aliasing Violation & UB** (`FixedPoint/FixedPointN.hpp`) - Illegal casting of `uint64_t[]` to `__uint128_t*` violates strict aliasing and risks unaligned load crashes.
13. **Unhandled SIGPIPE** (`main.cpp`) - Lacks `signal(SIGPIPE, SIG_IGN)`, meaning `EPIPE` during OpenSSL writes instantly terminates the engine.
14. **OrderPool Capacity Mismatch & Out-of-Bounds** (`MemHeaders/PoolAllocator.hpp`) - Dynamic 32-bit capacity inside a hardcoded 64-bit bitmap leads to silent memory corruption.
15. **OrderPool_Free Undefined Behavior** (`MemHeaders/PoolAllocator.hpp`) - Lacks pointer validation, triggering UB bit-shifts on invalid frees.
16. **InitArena_Owns Address Overflow** (`MemHeaders/InitArena.hpp`) - Pointer arithmetic integer overflows on high-memory 64-bit bounds, falsely rejecting valid pointers.
17. **WebSocket Frame Read Heap Overflow** (`DataStream/BinanceUserData.hpp`) - Signed vs unsigned casting flaw bypasses size checks on massive WebSocket frames.
18. **Thread-Safety Violation in Strategy Init** (`Strategies/StrategyLifecycle.hpp`) - Multi-core dynamic reconfigurations race on the `InitArena` bump allocator.
19. **Double-Buffer Race Condition in Book Snapshots** (`DataStream/BinanceDepth.hpp`) - Atomic flips without seqlocks allow the engine to read torn orderbooks.
20. **XGBoost 16-Class Weight Clipping** (`Backtest/BacktestEngine.hpp`) - Fixed 16-size stack array silently corrupts stack if multi-class regimes exceed the limit.
21. **ML Zoo Persistence Leak** (`Backtest/BacktestSharded.hpp`) - Walk-forward folds leak XGBoost `Booster` handles, eventually OOM crashing the runner.
22. **Seqlock Load-Load Barrier Missing** (`CoreFrameworks/ParameterSlot.hpp`) - Missing `std::atomic_thread_fence` allows torn reads on weakly ordered architectures.
23. **`ws_active` Relaxed Atomic Race** (`CoreFrameworks/BinanceAdapter.hpp`) - `memory_order_relaxed` without acquire/release drops fills during reconnects.
24. **ParameterSlot Seqlock Tear on Acquire Ordering** (`CoreFrameworks/ParameterSlot.hpp`) - Acquire ordering fails to prevent preceding buffer reads from reordering, breaking invariants.
25. **Short Position Logic Inversion** (`CoreFrameworks/Portfolio.hpp`) - `PositionExitGate` is hardcoded for longs; short positions ($q < 0$) trigger false exits.
26. **Multi-Word Torn Read in KillSwitch** (`CoreFrameworks/EngineSharded.hpp`) - Drainer writes a 64-word FPN balance while producer reads it non-atomically, falsely triggering the kill switch.

## 🟠 HIGH (Latency Spikes, Severe Edge Cases, State Drift)
*Issues that severely impact performance, algorithmic correctness, or trigger API/OS degradation.*

27. **Branch on the Hot Path (`active_b`)** (`CoreFrameworks/ExecutionCore.hpp`) - Data-dependent branch violates the ~60ns zero-branch rule.
28. **`BuyGate` Conditional Branch on Hot Path** (`CoreFrameworks/OrderGates.hpp`) - `if (pass)` costs 15-20 cycles on mispredict. Needs branchless masking.
29. **O(N) Pending Proceeds Calculation** (`CoreFrameworks/Portfolio.hpp`) - Loops block the hot path; needs a running $O(1)$ scalar.
30. **Sleep in Worker Thread Loop** (`CoreFrameworks/BinanceAdapter.hpp`) - `std::this_thread::sleep_for` yields the scheduler. Needs `_mm_pause()` spin-waits.
31. **Memory Ordering Deficiencies in Event Loops** (`CoreFrameworks/ControllerEventLoop.hpp`) - Uses `memory_order_relaxed` before thread handoffs.
32. **OMS Result Queue Drop Divergence** (`CoreFrameworks/OrderManager.hpp`) - Dropped fill results from full queues permanently un-sync the engine from the exchange.
33. **Blocking I/O in Health Logger** (`MemHeaders/HealthLog.hpp`) - Heavy `fopen`/`system()` calls block execution paths.
34. **OrderEventLog Latency Spike** (`CoreFrameworks/OrderEventLog.hpp`) - Drainer blocked by `usleep()` during async I/O stalls.
35. **BuddyAllocator Bitmap Collision** (`MemHeaders/BuddyAllocator.hpp`) - Documented bitmap collision across block orders remains unaddressed.
36. **Socket Descriptor Leak** (`DataStream/BinanceUserData.hpp`) - Failed TLS negotations do not close `sockfd`, exhausting FDs.
37. **Metric Aggregation Truncation** (`CoreFrameworks/EngineSharded.hpp`) - 64-bit engine counters truncate into 32-bit TUI fields, wrapping at 4.2B.
38. **Trade ID Precision Loss via Double Cast** (`DataStream/BinanceUserData.hpp`) - Casting 64-bit JSON Trade IDs through `double` mangles ID uniqueness.
39. **Inverted Risk Logic in Regime Transitions** (`Strategies/RegimeDetector.hpp`) - Widens stop-losses during trend breakdowns, actively compounding drawdowns.
40. **Sign-Blindness in Regression Overfit Check** (`Backtest/OverfitDetection.hpp`) - Signed difference correlation checks falsely pass models with massive negative correlation collapse.
41. **HTTP Chunked Encoding & Buffer Truncation** (`DataStream/BinanceOrderAPI.hpp`) - 8KB fixed buffers truncate chunked REST JSON, breaking parsers.
42. **SIMD Alignment Hazard in Replay State** (`DataStream/DepthReplayState.hpp`) - `calloc` guarantees 16-byte alignment, faulting on AVX-512 (64-byte) replay loads.
43. **FixedPoint AddSat Carry Neglect** (`FixedPoint/FixedPointN.hpp`) - Neglects the final carry flag, causing massive additions to wrap instead of saturating.
44. **FixedPoint ToDouble Exponent Overflow** (`FixedPoint/FixedPointN.hpp`) - FPN to Double conversion overflows IEEE-754 space to infinity.
45. **FixedPoint FromString Integer Wrap-Around** (`FixedPoint/FixedPointN.hpp`) - Maliciously large JSON string payloads silently integer-wrap.
46. **GUI Blocking I/O Freezes** (`GUI/SettingsPanel.hpp`) - Synchronous `fopen`/scans on the ImGui thread freeze the interface.
47. **Concurrent `localtime()` Race Condition** (`GUI/ChartPanel.hpp`) - Shared static `localtime()` buffer raced between GUI and engine. Needs `localtime_r()`.
48. **HealthLog Unsafe Rotation via `system()`** (`MemHeaders/HealthLog.hpp`) - `system("rm ...")` forks the process, devastating HFT kernel latency.
49. **Missing Signal Handlers** (`main.cpp`) - Dying instantly on `Ctrl+C` orphans open exchange orders and loses snapshot data.
50. **Build System AVX-512 & Aliasing Gaps** (`CMakeLists.txt`) - Missing `-mavx512f` and `-fno-strict-aliasing` flags invite compiler mangling.
51. **Naive SMT Topology Detection** (`CoreFrameworks/EngineSharded.hpp`) - Fails on Intel P/E or multi-numa AMD setups, destroying cache pinning.
52. **Held-Out Validation Lookahead Bias** (`Backtest/HeldOutSplit.hpp`) - Missing `h` purge gap between train/eval splits leaks future data into validation.
53. **FixedPoint 192-bit Division Overflow Truncation** (`FixedPoint/FixedPoint64.hpp`) - Schoolbook division left-shifts bits entirely out of intermediate arrays on massive dividends.
54. **Time-Density Bias in Walk-Forward Purging** (`Backtest/BacktestEngine.hpp`) - Static tick-count purges break uniformity between night sessions and open hours.
55. **Unstable Variance in VolBarrier Labels** (`Backtest/LabelFunctions.hpp`) - Naive variance formula causes catastrophic cancellation on high-priced assets.
56. **Stale Orderbook Levels on Shallow Updates** (`DataStream/BinanceDepth.hpp`) - <5 level updates fail to clear the book bottom, trading against phantom liquidity.
57. **Sequence Desync on Partial Parse** (`DataStream/BinanceDepth.hpp`) - Malformed JSON leaves `lastUpdateId` carried over, forcing full book resyncs.
58. **Float-to-Fixed Point Truncation Bias** (`FixedPoint/FixedPointN.hpp`) - Systematic downward bias parsing decimals due to truncation instead of rounding to nearest.
59. **Double-to-Fixed Point Truncation Bias** (`FixedPoint/FixedPointN.hpp`) - Same downward drift bias on direct integer casts from doubles.
60. **Float-to-Int Rounding Instability** (`DataStream/BinanceOrderAPI.hpp`) - Direct `int64_t` casts of `0.1` precision math result in off-by-one size truncations.
61. **Inverse Branch Prediction Hint in Polling** (`CoreFrameworks/SPSCRing.hpp`) - `[[unlikely]]` hint for empty queues is strictly wrong for busy-wait loops.
62. **Error Recovery Spinloop on Rate Limits** (`CoreFrameworks/ReconciliationLoop.hpp`) - Instant retries on HTTP 429 trap the thread in a tight loop and prolong IP bans.
63. **Truncated Hashing Vulnerability** (`MemHeaders/HmacSha256.hpp`) - Ignores `fread` errors, generating valid model stamps for partially-loaded files.
64. **Partial State Mutation on IO Failure** (`CoreFrameworks/Portfolio.hpp`) - Mutating active bitmaps before IO finishes leaves the portfolio in a zombie state on disk failure.
65. **Topology Race Condition** (`CoreFrameworks/EngineSharded.hpp`) - `topo_slow_cpu` array is read concurrently by fan_out threads without atomics.

## 🟡 MEDIUM (Struct Integrity, Algorithmic Edge Cases, Missing Guards)
*Issues that degrade accuracy or maintainability over time but are not immediately fatal.*

66. **Cache Line Straddling for `Order` Struct** (`CoreFrameworks/Order.hpp`) - 280-byte size needs padding to 320 for alignment.
67. **False Sharing Risk in `OrderManagerState`** (`CoreFrameworks/OrderManager.hpp`) - Hot counters and cold state mixed without cache line padding.
68. **Scalable Struct Straddling in `Position`** (`CoreFrameworks/Portfolio.hpp`) - Hardcoded 7-byte padding breaks alignment if $F$ scales to 96 or 128.
69. **FP64 Overflow Truncation** (`FixedPoint/FixedPoint64.hpp`) - Fails to saturate on division overflow.
70. **NaN Propagation in VolScaler** (`ML_Headers/VolScaler.hpp`) - Missing NaN guards corrupt downstream feature math.
71. **Negative Price/Volume Ingestion** (`DataStream/BinanceCrypto.hpp`) - Lacks validation for invalid exchange ticks.
72. **Inverted Book & Negative Spreads** (`DataStream/BinanceDepth.hpp`) - Allows negative spreads from inverted order books.
73. **O(N) Parsing Violations** (`DataStream/BinanceOrderAPI.hpp`) - `strstr` and standard `atof` violate HFT rules.
74. **System Allocators During Runtime** (`CoreFrameworks/EngineSharded.hpp`) - `std::vector` violates the zero-allocator invariant.
75. **Graceful Shutdown Resource Leaks** (`CoreFrameworks/EngineSharded.hpp`) - Leaks SSL contexts and file handles.
76. **InitArena Alignment Failure** (`MemHeaders/InitArena.hpp`) - Malloc fallback path fails to guarantee 64-byte SIMD alignment.
77. **Naive JSON Parsing in Reconcile** (`CoreFrameworks/Reconcile.hpp`) - `strstr` extraction incorrectly matches substring keys (e.g., 'orderId' vs 'other_orderId').
78. **ParameterSlot False Sharing** (`CoreFrameworks/ParameterSlot.hpp`) - Uses fixed padding rather than `alignas`, risking false sharing based on template sizes.
79. **Path Truncation and Unchecked I/O** (`DataStream/DepthRecorder.hpp`) - `snprintf` buffer limits can truncate file paths silently.
80. **Double-Rounding Parity Hazard** (`DataStream/BinanceCrypto.hpp`) - Mixing `std::from_chars` and `tt::parse_double_fast` breaks bytewise determinism.
81. **FixedPoint Exp Magnitude Loss** (`FixedPoint/FixedPointN.hpp`) - Taylor series for negative $X$ converges poorly, risking zero-truncation in ML probabilities.
82. **VWAP Accumulation Precision Loss** (`GUI/CandleAccumulator.hpp`) - Endless sums cause float truncation for small inputs.
83. **Discontinuous History Gaps in TUI Rendering** (`GUI/CandleAccumulator.hpp`) - Missing "doji" padding for inactive intervals destroys visual indicator continuity.
84. **Transcendental Constant Precision Bottleneck** (`FixedPoint/FixedPointN.hpp`) - Hardcoded 64-bit Pi/e arrays bottleneck dynamic $F$ expansions.
85. **Bandit JSON Order Dependency** (`ML_Headers/BanditLearning.hpp`) - Forward-only `strstr` JSON extraction fails if regimes are not perfectly sorted.
86. **Bandit Weight Tearing** (`ML_Headers/BanditLearning.hpp`) - Lack of normalization locks enables GUI threads to display non-1.0 sums.
87. **Silent Truncation in JSON Loader** (`ML_Headers/BanditLearning.hpp`) - Ignores short reads on `fread`, risking silent fallback to default weights.
88. **SSL Non-Fatal Error Drop** (`DataStream/WebSocketUtil.hpp`) - Disconnects completely on minor network stalls (`SSL_ERROR_WANT_READ`).

## 🟢 LOW (Micro-Optimizations & Cosmetic Limits)
*Minor performance left on the table or cosmetic data limits.*

89. **Missing AVX-512 Vectorization in Fixed-Point Math** (`FixedPoint/FixedPoint64.hpp`) - Misses batching optimizations.
90. **Scalar ML Feature Operations** (`ML_Headers/LinearRegression3X.hpp`) - Unvectorized parallelizable logic.
91. **Precision Drift Risk in Rolling Sums** (`ML_Headers/RollingStats.hpp`) - $O(1)$ FPN sum risks long-window drift.
92. **Scalar Bit-by-Bit Division** (`FixedPoint/FixedPointN.hpp`) - Slow bit-loop instead of vectorized reciprocal multiplication.
93. **String Conversion Overhead** (`FixedPoint/FixedPointN.hpp`) - Variable stack arrays in `FPN_ToString`.
94. **`OrderEventLog` Yielding Behavior** (`CoreFrameworks/OrderEventLog.hpp`) - Lacks `_mm_pause()` in spin-loops.
95. **MockGenerator Sequence Wrap-around** (`DataStream/MockGenerator.hpp`) - `uint32_t` sequence numbers wrap in HFT simulations.
96. **OrderEventLog History Loss** (`CoreFrameworks/OrderEventLog.hpp`) - Startup load truncates NEWEST events instead of oldest on capacity limits.
97. **TradeReader Stale Data limit** (`GUI/TradeReader.hpp`) - Truncation at `MAX_TRADES` permanently blocks recent trades from rendering in long sessions.
98. **Latency Percentile Skew** (`CoreFrameworks/CoreLatencyStats.hpp`) - `total_count` incremented before writing sample, allowing p99 reads to hit `0`.# Phase 11: Deep System & Bitwise Edge Cases

## NEW Ultra-Obscure Issues (99-108)

1. **Uninitialized Padding Leak in Snapshot Persist** (`CoreFrameworks/ShardedSnapshotPersist.hpp`)
   - **Severity:** HIGH
   - **Details:** When persisting the engine snapshot, `fwrite` is used to dump the entire `Portfolio` and `Position` struct arrays directly to disk. Because padding bytes (e.g., `_pad_pos[7]`) are never explicitly zeroed during `Portfolio_Init`, this leaks uninitialized stack/heap memory into the snapshot file. This completely breaks bytewise determinism for snapshot hashing and exposes sensitive memory.
2. **WebSocket Pong Stack Buffer Overflow** (`DataStream/BinanceCrypto.hpp`)
   - **Severity:** CRITICAL
   - **Details:** `binance_ws_send_pong` allocates a fixed 256-byte stack array `unsigned char frame[256];`. It then executes `memcpy(frame + pos, payload, len)` without bounds checking on `len`. If the exchange sends a ping frame with a payload larger than ~250 bytes, it triggers a catastrophic stack buffer overflow.
3. **Missing `RLIMIT_MEMLOCK` & `mlockall`** (`CoreFrameworks/SystemInit.hpp`)
   - **Severity:** HIGH
   - **Details:** `engine_set_mxcsr_ftz_daz` configures FPU latency settings, but the init sequence fails to call `mlockall(MCL_CURRENT | MCL_FUTURE)`. Without locking the engine's memory to RAM, the Linux kernel can page-out inactive segments of the executable. When a sudden burst of market activity occurs, the engine suffers massive page-fault latency spikes.
4. **WebSocket Negative Length Bounds Bypass** (`DataStream/WebSocketUtil.hpp`)
   - **Severity:** CRITICAL
   - **Details:** In `ws_read_frame`, a 64-bit frame payload length (`pay_len = 127`) is parsed into a signed `int` via bitwise shifting. A corrupt or maliciously large payload length will overflow into a negative integer. This bypasses the subsequent `if (plen > max_len) return -1;` guard, leading to infinite loops or out-of-bounds SSL reads.
5. **WebSocket Handshake Header Truncation** (`DataStream/BinanceCrypto.hpp`)
   - **Severity:** MEDIUM
   - **Details:** `binance_ws_handshake` reads the HTTP upgrade response using a static 1024-byte array `char response[1024]`. If the exchange injects large HTTP headers (e.g., massive Cloudflare tracing cookies or extended auth parameters) before the `\r\n\r\n` boundary, the loop terminates without seeing the end of headers. `strstr` then fails to find "101", trapping the engine in a reconnect loop.
6. **HTTP Request Truncation on Long Listen Keys** (`DataStream/BinanceCrypto.hpp`)
   - **Severity:** MEDIUM
   - **Details:** `binance_ws_handshake` uses a 512-byte buffer and `snprintf` to build the HTTP request. The URL `path` parameter contains the user data listen key. If the exchange rotates to a longer listen key specification, `snprintf` will silently truncate the HTTP request, leading to HTTP 400 Bad Request errors.
7. **Missing `SO_KEEPALIVE` on TCP Socket** (`DataStream/BinanceCrypto.hpp`)
   - **Severity:** MEDIUM
   - **Details:** The base TCP socket does not set the `SO_KEEPALIVE` option. If the exchange silently drops the connection (e.g., an AWS middlebox timeout dropping packets), the Linux networking stack will not detect the dead socket. The engine will hang waiting for ticks until an application-layer watchdog forces a reset.
8. **`RAND_bytes` Failure Unchecked** (`DataStream/BinanceCrypto.hpp`)
   - **Severity:** HIGH
   - **Details:** In `binance_ws_handshake` and `binance_ws_send_pong`, `RAND_bytes` is called to generate WebSocket masking keys without verifying the return value. If the OpenSSL random pool is depleted, the array is left uninitialized. This results in undefined masking keys, causing protocol desynchronization.
9. **`strlen` Buffer Overflow in `ParseFast.hpp`** (`CoreFrameworks/ParseFast.hpp`)
   - **Severity:** HIGH
   - **Details:** `parse_double_fast` relies on `std::strlen(s)` without bounds. If legacy code passes a JSON substring slice that is not null-terminated (assuming `std::from_chars` will stop on non-numeric characters), `strlen` will perform a linear out-of-bounds heap read until it crashes or hits a random null byte.
10. **`freeaddrinfo` Leak on Connection Loop** (`DataStream/BinanceCrypto.hpp`)
    - **Severity:** LOW
    - **Details:** In `binance_tcp_connect`, if the `socket()` call succeeds but `connect()` fails, the loop calls `close(sockfd)` and correctly continues. However, there is a path where `getaddrinfo` structures might not be fully freed if the function bails early, causing a minor memory leak during heavy reconnect looping.# Phase 12: Machine Learning Blending & Recorder Bugs

## NEW Ultra-Obscure Issues (109-118)

1. **Bandit Weight Explosion to Infinity/NaN** (`ML_Headers/BanditLearning.hpp`)
   - **Severity:** CRITICAL
   - **Details:** In `Bandit_Update`, the algorithm uses an exponential update rule. If the learning rate is not strictly bounded against the maximum possible reward, consecutive positive rewards can cause the weights to overflow to infinity, normalizing to NaN and permanently corrupting the ensemble.
2. **`std::sort` Undefined Behavior with NaNs** (`ML_Headers/FeatureStandardizer.hpp`)
   - **Severity:** HIGH
   - **Details:** `FeatureStandardizer_FitWinsor` uses `std::sort` to calculate quantiles for winsorization. If the feature data contains `NaN` values, it violates the strict weak ordering requirement of `std::sort`, resulting in undefined behavior, corrupted quantiles, or outright crashes during the training phase.
3. **Blocking `fprintf`/`fflush` on Hot Path** (`DataStream/TickRecorder.hpp`)
   - **Severity:** HIGH
   - **Details:** `TickRecorder_Push` performs synchronous `fprintf` and `fflush` calls directly on the MarketReader thread. During a market spike, disk I/O latency will stall the thread, causing WebSocket receive buffers to fill up and the connection to drop.
4. **False Sharing on 128-Byte Cache Lines** (`CoreFrameworks/SPSCRing.hpp`)
   - **Severity:** MEDIUM
   - **Details:** The `SPSCRing` pads the head and tail pointers with 64 bytes to prevent false sharing. However, modern architectures (like Apple Silicon or certain ARM servers) use 128-byte cache lines. On these systems, the pointers still share a cache line, causing devastating false-sharing performance penalties.
5. **Cholesky NaN Propagation** (`ML_Headers/RidgeBlender.hpp`)
   - **Severity:** CRITICAL
   - **Details:** `Cholesky_Solve` does not validate the input correlation matrix for `NaN`s before performing the decomposition. If a `NaN` is present, it silently propagates through the entire matrix inversion, resulting in invalid blending weights for the Ridge solver.
6. **`FPN_FromDouble` Floating-to-Integer Cast UB** (`FixedPoint/FixedPointN.hpp`)
   - **Severity:** HIGH
   - **Details:** The conversion algorithm casts `double` to integers. If the `double` value exceeds the representable range of the target integer type, the cast results in undefined behavior under the C++ standard, potentially resulting in wildly incorrect fixed-point values rather than a controlled saturation.
7. **String Parsing Silent Overflow** (`FixedPoint/FixedPointN.hpp`)
   - **Severity:** HIGH
   - **Details:** `FPN_FromString` accumulates parsed digits via multiplication and addition without any overflow checks. A maliciously large or malformed number string will silently wrap around, creating a corrupted fixed-point representation.
8. **JSON Precision Loss in Bandit States** (`ML_Headers/BanditLearning.hpp`)
   - **Severity:** MEDIUM
   - **Details:** `Bandit_LoadJSON` parses saved state weights. If standard parsing methods are used that don't maintain the exact precision of the fixed-point or double representations, loading and saving the state iteratively will cause the weights to drift over multiple restarts.
9. **Zero Variance Scaling Division by Zero** (`ML_Headers/FeatureStandardizer.hpp`)
   - **Severity:** CRITICAL
   - **Details:** If a feature remains constant throughout the training period (zero variance), the standardizer calculates a standard deviation of 0. During inference, scaling this feature involves dividing by the standard deviation, leading to a division by zero and injecting `NaN`s into the live inference path.
10. **Unchecked Correlation Input** (`ML_Headers/RidgeBlender.hpp`)
    - **Severity:** HIGH
    - **Details:** `RidgeBlender_BuildCorr` constructs the correlation matrix without verifying that the inputs (predictions and targets) are finite. Non-finite inputs will immediately contaminate the matrix, destroying the blending process.# Phase 13: Hot Path Deduplication & Architectural Debt

## NEW Deduplication Issues (119-123)

1. **Multi-Word FPN Comparison Duplication** (`CoreFrameworks/Portfolio.hpp` & `OrderGates.hpp`)
   - **Severity:** HIGH
   - **Details:** Multi-word fixed-point comparisons (`F > 64`) are manually implemented using custom loops and bitwise logic in both the Portfolio exit gate and the OrderGates logic. The OrderGates version is buggy for high precision. Both should be deleted and routed through the centralized, SIMD-ready `FPN_LessThanOrEqual` and `FPN_GreaterThanOrEqual` helpers in `FixedPointN.hpp`.
2. **O(N) JSON Scanning Duplication** (`DataStream/BinanceCrypto.hpp` & `BinanceOrderAPI.hpp`)
   - **Severity:** MEDIUM
   - **Details:** Manual `strstr` and `strchr` logic to find JSON keys is identically copy-pasted across the trade, depth, and order execution report parsers. This violates the single-pass parsing invariant. These should be deduplicated into a single, branchless JSON token extraction function in `ParseFast.hpp`.
3. **Adaptive Spin-Wait Duplication** (`CoreFrameworks/BinanceAdapter.hpp` & `OrderManager.hpp`)
   - **Severity:** LOW
   - **Details:** The lock-free polling logic (checking empty, counting spins, calling `_mm_pause()`, and falling back to deeper spins) is explicitly coded into multiple different worker threads. This should be abstracted into a `SPSCRing_AdaptivePop` method to ensure consistent exponential backoff across all threads.
4. **Gate Evaluation Logic Drift** (`CoreFrameworks/ExecutionCore.hpp` & `GateParameters.hpp`)
   - **Severity:** HIGH
   - **Details:** The core logic that evaluates whether a `TradeEvent` passes the configured Buy/Sell gates is implemented directly inside `ExecutionCore_Tick_Impl`, but a nearly identical copy exists in `GateParameters.hpp` for slow-path evaluation. They risk drifting out of sync. `ExecutionCore` should call the inline helper.
5. **Key-Value Config Parsing Duplication** (`CoreFrameworks/ControllerConfig.hpp` & `DataStream/BinanceCrypto.hpp`)
   - **Severity:** MEDIUM
   - **Details:** Logic to read text files line-by-line, split by `=`, and trim whitespace is re-implemented four separate times to parse `.cfg`, `.stamp`, and `.secrets` files. It should be consolidated into a generic configuration loader to reduce binary size and eliminate duplicated buffer overflow risks.# Phase 14: Hardware Architecture & L1/L2 Cache Spills

## NEW Ultra-Obscure Hardware Issues (124-133)

1. **ParameterSlot Pad Underflow / Straddling** (`CoreFrameworks/ParameterSlot.hpp`)
   - **Severity:** HIGH
   - **Details:** The struct padding uses `uint8_t _pad[64 - sizeof(std::atomic<uint64_t>) - sizeof(uint64_t) * 2]`. This calculation is completely broken because it does not subtract `sizeof(T) * 2` (the two buffers themselves). For any large `T`, the pad size underflows or causes the struct to expand far past 64 bytes in a non-cache-aligned manner, causing every parameter read to straddle L1 cache lines.
2. **False Sharing on `BinanceUserDataState` Atomics** (`DataStream/BinanceUserData.hpp`)
   - **Severity:** HIGH
   - **Details:** The state struct packs `std::atomic<int> keepalive_failed` and `std::atomic<uint64_t> fills_received` adjacently without `alignas(64)`. The `ud_keepalive_thread` writes to the keepalive flags while the `ud_ws_thread` constantly increments the fill counters. This causes massive L1 cache line bouncing (false sharing) between the two distinct cores running these threads.
3. **False Sharing on `OrderEventLog` Atomics** (`CoreFrameworks/OrderEventLog.hpp`)
   - **Severity:** HIGH
   - **Details:** Similar to UserData, `ring_full_spins` (written aggressively by the hot-path producer thread) shares the same cache line with `writer_thread_active` and `writer_realloc_failed_count` (written by the async I/O drainer thread). This invalidates the hot path's L1 cache constantly when the drainer updates its state.
4. **I-Cache Eviction via Massive Loop Unrolling** (`FixedPoint/FixedPointN.hpp`)
   - **Severity:** HIGH
   - **Details:** The library aggressively forces `#pragma GCC unroll 65534` on almost all mathematical inline functions (`FPN_MagAddN`, `FPN_MagSubN`, `FPN_Mul`, etc.). While this avoids loop branches for `F=64` (1 word), if a strategy utilizes `F=256` or `F=512` (4 to 8 words), unrolling nested mathematical loops blows out the CPU's 32KB L1 Instruction Cache, causing Instruction TLB misses on the hot path.
5. **False Sharing on Engine Local Variables** (`CoreFrameworks/EngineSharded.hpp`)
   - **Severity:** MEDIUM
   - **Details:** In `EngineSharded_Run`, variables like `std::atomic<uint64_t> ticks_produced` and `std::atomic<double> last_price` are declared as adjacent local stack variables and captured by reference into thread lambdas. Stack variables are packed tightly by the compiler. The producer thread pounding `ticks_produced` will cause false sharing with the TUI/GUI thread reading `last_price`.
6. **L1 D-Cache Spill in `TUISharedState`** (`main.cpp` / `DataStream/EngineTUI.hpp`)
   - **Severity:** MEDIUM
   - **Details:** The `TUISharedState` struct includes massive embedded structures (like 16 model path strings and `CandleAccumulator` pointers) and exceeds 32KB if fully expanded. Unaligned or dense access from the GUI thread evicts the engine's critical working set from the L3 cache if they share a CCX ring.
7. **Missing Cache Padding in `CoreLatencyStats`** (`CoreFrameworks/CoreLatencyStats.hpp`)
   - **Severity:** HIGH
   - **Details:** While `CoreLatencyStats` is marked `alignas(64)`, the internal fields mix the hot-path `std::atomic<uint8_t> enabled` flag with the 1,000,000-element `samples` array. The massive array pushes subsequent metadata out of alignment, and continuous writing to the ring buffer causes cache thrashing against the read-mostly flags.
8. **Double-Buffering Sync Tear in `TUISharedState`** (`DataStream/EngineTUI.hpp`)
   - **Severity:** CRITICAL
   - **Details:** `TUISnapshot_InitSeq` uses a primitive 64-bit sequence counter for double-buffering. However, on 32-bit platforms or under aggressive x86 reordering, writing to the massive `TUISnapshot` payload (thousands of bytes) is not fenced properly before the sequence bump. The GUI thread can render partially written structural data.
9. **EventLoopState Unaligned Arrays** (`CoreFrameworks/ControllerEventLoop.hpp`)
   - **Severity:** MEDIUM
   - **Details:** `EventLoopState` contains large inline arrays for core states and OMS structures. It lacks internal `alignas(64)` boundaries between the controller's active read/write fields and the read-only configuration arrays, inviting false sharing during hot-path polling.
10. **`FPN` Pointer Cast UB on ARM** (`FixedPoint/FixedPointN.hpp`)
    - **Severity:** HIGH
    - **Details:** Several internal math helpers directly cast the `uint64_t w[N_WORDS]` array to larger pointer types (like `__uint128_t*`) for vectorized loads. While x86 tolerates unaligned vector loads, ARM architectures will throw a `SIGBUS` (Bus Error) or silently corrupt the data if the `FPN` struct happens to fall on an unaligned stack boundary.# Phase 15: Strategies, Logging & Fixed-Point Limits

## NEW Ultra-Obscure Issues (119-128)

1. **`TradeLogBuffer` Cross-Thread Data Race** (`DataStream/TradeLog.hpp`)
   - **Severity:** CRITICAL
   - **Details:** The `TradeLogBuffer` is written to by the hot-path producer thread (`PushBuy`) and read by the slow-path thread (`Drain`). The `head` and `count` indices, as well as the records themselves, are plain variables lacking `std::atomic` or `seqlock` synchronization. The drainer will read torn, partially written records while the hot path mutates them, corrupting the CSV log.
2. **Q32.32 Integer Overflow on BTC Prices** (`ML_Headers/LinearRegression3X.hpp`)
   - **Severity:** HIGH
   - **Details:** The regression logic accumulates `sum_y2 = FPN_Mul(y, y)`. The comments claim Q32.32 (where $F=32$) provides enough headroom. However, for an asset like BTC at $100,000$, squaring yields $10,000,000,000$. The sum of 8 such squares is $80,000,000,000$. This massively exceeds the maximum 32-bit unsigned integer ($4.29B$), silently overflowing the integer space and completely breaking the linear regression for high-priced assets.
3. **Momentum Breakout Sign-Flip Inversion** (`Strategies/Momentum.hpp`)
   - **Severity:** HIGH
   - **Details:** The adaptive logic subtracts a shift from `live_breakout_mult` on positive P&L. If the strategy performs well for an extended period, `live_breakout_mult` can become negative. Because `FPN_Mul` respects signs, the breakout price becomes `avg - (stddev * |mult|)`. The strategy will trigger "breakout" buys BELOW the moving average, silently transforming the momentum strategy into a mean-reversion strategy.
4. **`FPN_FromDouble` Fractional Overflow UB** (`FixedPoint/FixedPointN.hpp`)
   - **Severity:** HIGH
   - **Details:** To extract the fractional component, the logic computes `double frac_hi = floor(frac_part * 18446744073709551616.0);`. Due to IEEE-754 precision rounding, if `frac_part` is `0.9999999999`, the multiplication can round exactly to `18446744073709551616.0` ($2^{64}$). Casting $2^{64}$ to `uint64_t` results in Undefined Behavior (UB), commonly wrapping to 0, which zeroes out the fractional value.
5. **SimpleDip Falling Knife Vulnerability** (`Strategies/SimpleDip.hpp`)
   - **Severity:** MEDIUM
   - **Details:** The strategy computes its entry purely as a percentage drop from `state->recent_high`. It lacks a regime filter or trailing time-decay on the high. If the asset enters a multi-month bear market, `recent_high` remains anchored to the all-time high, causing the strategy to continuously buy into severe downtrends (catching falling knives) whenever the volume gate is met.
6. **Silent Trade Drop on Burst** (`DataStream/TradeLog.hpp`)
   - **Severity:** HIGH
   - **Details:** `TradeLogBuffer_PushBuy` guards against overflow with `if (buf->count >= TRADE_LOG_BUF_SIZE) return;`. During a cascading liquidation event where many fills occur in the same millisecond, the buffer instantly fills, and all subsequent trades are dropped and lost forever without triggering any alert or metric increment.
7. **LogViewerPanel First Line Truncation** (`GUI/LogViewerPanel.hpp`)
   - **Severity:** LOW
   - **Details:** When the file size exceeds `LOG_BUF_SIZE`, `LogViewer_Refresh` seeks into the middle of the file. It then uses `strchr` to find the first `\n` and skips to it to avoid rendering a partial line. However, it does this unconditionally. If the `fread` happened to land exactly at the start of a clean newline, it still skips the entire first valid line of logs.
8. **TradeLog Blocking `fflush` Fallback** (`DataStream/TradeLog.hpp`)
   - **Severity:** MEDIUM
   - **Details:** The raw `TradeLog_Buy` and `TradeLog_Sell` functions include an explicit `fflush(log->file)` after every `fprintf`. If a developer or a new strategy directly calls these functions instead of the buffered variants, it will inject hundreds of microseconds of blocking disk I/O directly into the event loop.
9. **`parse_double_fast_advance` Pointer Drift** (`CoreFrameworks/ParseFast.hpp`)
   - **Severity:** MEDIUM
   - **Details:** The function updates the string pointer to the end of the parsed number. However, if the JSON value has trailing whitespace or unexpected characters before the closing quote or comma, the pointer will not advance past them. Subsequent manual parsing logic relying on this pointer will desync and fail.
10. **GUI Theme Color Array Out-of-Bounds** (`GUI/DashboardPanels.hpp`)
    - **Severity:** LOW
    - **Details:** In `DashboardPanels.hpp`, mapping strategies to theme colors (`strat_colors[sid]`) relies on `sid` not exceeding the length of the predefined color array. If a new strategy is added with an ID greater than the array bounds, it will trigger a heap out-of-bounds read during UI rendering, potentially crashing the monitoring application.# Phase 16: ODR Violations, Simulation Divergence & Cryptography

## NEW Ultra-Obscure Issues (134-143)

1. **ODR/Static Linkage Violation in Header Functions** (`Backtest/BacktestSharded.hpp` & `BacktestPanels.hpp`)
   - **Severity:** HIGH
   - **Details:** Local `static` variables (like `ml_zoos`, `tick_rings`, `depth_replay_initialized`) are declared inside `static inline` functions inside header files. In C++, this violates the One Definition Rule (ODR) across translation units. Every `.cpp` file that includes this header gets its own completely separate instance of the `static` variable, resulting in fragmented memory states and silent data isolation between subsystems.
2. **Paper Mode Zero-Slippage Matching Anomaly** (`CoreFrameworks/OrderManager.hpp`)
   - **Severity:** HIGH
   - **Details:** The Paper Mode matching engine logic instantly fills orders at the exact current market price (`event_price`) regardless of order size. It does not check orderbook depth or apply slippage. This creates a massive divergence between simulation and reality, making backtests and paper trading appear artificially profitable on highly illiquid momentum breakouts.
3. **Incomplete OpenSSL `SSL_shutdown` Protocol** (`DataStream/BinanceCrypto.hpp`)
   - **Severity:** MEDIUM
   - **Details:** `binance_ws_close` calls `SSL_shutdown` once and then destroys the socket. The TLS 1.3 protocol requires a bidirectional shutdown (calling it until it returns 1). Premature TCP closure sends a TCP RST instead of FIN, which Binance API firewalls log as a dirty disconnect, eventually triggering IP-level rate-limiting or soft bans.
4. **FPN to Double Precision Loss at Exchange Boundary** (`CoreFrameworks/ExchangeAdapter.hpp`)
   - **Severity:** MEDIUM
   - **Details:** `OrderResult` structs force quantities and prices to pass through standard `double` types before string formatting for REST API requests. A 64-bit double only has 53 bits of mantissa. For high-precision fixed-point values (`F > 64`), this completely truncates the lowest bits, causing small pricing/quantity mismatches on the exchange.
5. **Unchecked `TCP_NODELAY` Optimization** (`DataStream/BinanceCrypto.hpp`)
   - **Severity:** LOW
   - **Details:** `setsockopt(sockfd, IPPROTO_TCP, TCP_NODELAY, ...)` is called, but the return value is not strictly asserted. If the OS denies the request (e.g., due to lack of privileges or specific virtualized NIC drivers), the socket falls back to Nagle's algorithm, secretly batching packets and destroying the sub-microsecond latency profile.
6. **Intentional Memory Leaks in Test Rigs** (`tests/controller_test.cpp`)
   - **Severity:** LOW
   - **Details:** Test rigs (like `PartialsRig`) allocate state using `new` but intentionally omit `delete` to save teardown time. While acceptable for short-lived unit tests, running these tests under CI/CD memory sanitizers (ASan/Valgrind) floods the output with false-positive leak reports, masking genuine engine leaks.
7. **Correlated LCG Seeds in Sharded Backtest** (`DataStream/MockGenerator.hpp`)
   - **Severity:** MEDIUM
   - **Details:** The `MockRNG` uses a Linear Congruential Generator (LCG). If multiple sharded cores initialize their RNG sequences with monotonically increasing or identical seeds, the pseudo-random price paths across the shards will be mathematically correlated, severely compromising the statistical independence of multi-core Monte Carlo simulations.
8. **EVP_DigestUpdate Unchecked Return Code** (`MemHeaders/HmacSha256.hpp`)
   - **Severity:** MEDIUM
   - **Details:** The OpenSSL hashing functions (`EVP_DigestUpdate` and `EVP_DigestFinal_ex`) are called during model stamp verification without checking their integer return codes. If the crypto engine fails (e.g., due to an internal allocation failure), it silently proceeds and produces a garbage hash.
9. **Epoch Microsecond Wrap-Around Logic** (`CoreFrameworks/ReconciliationLoop.hpp`)
   - **Severity:** LOW
   - **Details:** Time differences are calculated using `uint64_t` subtractions of epoch microseconds. If the system clock undergoes a sudden backward NTP synchronization (e.g., leap second correction or time-sync jump), the subtraction underflows to a massive 64-bit integer, instantly triggering timeout deadlocks or massive drift corrections.
10. **Implicit Struct Conversion Scaling Bug** (`ML_Headers/LinearRegression3X.hpp`)
    - **Severity:** HIGH
    - **Details:** The conversion of the raw sample `count` into the `FPN` denominator `n_fp` uses `FPN_FromDouble<F>((double)count)`. Passing the integer through a double before casting it back to a wide fixed-point struct introduces unnecessary overhead and precision risks. It should use an explicit `FPN_FromInt` helper to ensure bitwise-perfect scaling.
# Phase 17: REST API Desyncs, GUI Allocators & Math Propagation

## NEW Ultra-Obscure Issues (144-153)

1. **Locale-Dependent REST Formatting** (`DataStream/BinanceOrderAPI.hpp`)
   - **Severity:** HIGH
   - **Details:** The API uses `snprintf` with `%f` to format order quantities. In locales like `de_DE`, this generates numbers with commas (e.g., `0,001`). The Binance REST API strictly requires dot-decimals. A system booting with a European locale will instantly fail every single order submission with a formatting error.
2. **Inverted Clock Offset in Retries** (`DataStream/BinanceOrderAPI.hpp`)
   - **Severity:** HIGH
   - **Details:** In `binance_retry_request`, upon receiving a Timestamp Outside RecvWindow error, the engine calculates the offset to adjust its clock. The math subtracts the local clock from the server clock instead of vice versa (or applies the offset with the wrong sign), doubling the time divergence on the next retry and guaranteeing a permanent lock-out.
3. **BinanceAdapter Sync Race** (`CoreFrameworks/BinanceAdapter.hpp`)
   - **Severity:** CRITICAL
   - **Details:** `BinanceAdapter_GetBalancesImpl` executes synchronous REST queries. It accesses the same thread-unsafe `BinanceOrderAPI` instances and internal TCP/TLS buffers currently being utilized by the background `worker_thread` polling loop. This race condition tears the TLS framing and crashes OpenSSL.
4. **Violation of Zero-Allocation Invariant** (`GUI/StrategyQualityPanel.hpp`)
   - **Severity:** HIGH
   - **Details:** `StrategyQuality_Refresh` and `sq_tail_read` aggressively call `malloc` and `free` to allocate temporary text buffers for log reading. Executing system allocators on the GUI thread introduces OS-level locking latency that can stall the engine if the allocator lock is contended.
5. **BuddyAllocator Out-of-Bounds Free** (`MemHeaders/BuddyAllocator.hpp`)
   - **Severity:** CRITICAL
   - **Details:** `buddy_free_ptr` calculates the block index from the provided pointer. It lacks bounds checking against the arena's `base` and `capacity`. If an external pointer is accidentally passed, it calculates an invalid bit-index and corrupts the buddy bitmap, crashing the entire memory manager on the next allocation.
6. **CostModel NaN Propagation** (`ML_Headers/CostModel.hpp`)
   - **Severity:** HIGH
   - **Details:** `CostModel_Estimate` accepts volatility and spread inputs from the market data without validating them. If the exchange sends a corrupt tick (or during a halt), `NaN` is propagated through the total cost calculation, causing the gate logic to fail open or closed unpredictably.
7. **BarrierGate Negative Sqrt NaN Vulnerability** (`ML_Headers/BarrierGate.hpp`)
   - **Severity:** HIGH
   - **Details:** `BarrierGate_Compute` uses `pow(..., 0.5)` (square root). If the internal tracking parameter `p_valley` drifts below `-1.0` due to a severe momentum crash, the square root of a negative number generates a `NaN`. This immediately poisons the entire gate evaluation.
8. **Missing URL Encoding on Client Order IDs** (`DataStream/BinanceOrderAPI.hpp`)
   - **Severity:** MEDIUM
   - **Details:** Parameters like `newClientOrderId` are injected directly into the query string before HMAC signing. It fails to URL-encode these strings. If a strategy dynamically generates an ID containing special characters (e.g., `+` or `&`), the signature generated locally will not match Binance's decoded signature, resulting in an unauthorized rejection.
9. **Brittle HTTP Content Parsing** (`DataStream/BinanceOrderAPI.hpp`)
   - **Severity:** MEDIUM
   - **Details:** `binance_rest_request` assumes the HTTP response headers and body arrive in the exact same SSL packet. If the network fragments the packet such that the body arrives in a subsequent `SSL_read`, the parser breaks early without checking `Content-Length`, resulting in an empty or truncated JSON response.
10. **2GB Log File Limit** (`GUI/StrategyQualityPanel.hpp`)
    - **Severity:** LOW
    - **Details:** `sq_tail_read` uses standard `long` variables for `fseek` file offsets. On 32-bit platforms (or LP32/ILP32 models), `long` is 32 bits and overflows at 2GB. Attempting to tail an `engine.log` file larger than 2GB will wrap around and seek to a negative offset, failing to read the log.