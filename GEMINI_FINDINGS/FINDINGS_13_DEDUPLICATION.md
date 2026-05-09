# Phase 13: Hot Path Deduplication & Architectural Debt

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
   - **Details:** Logic to read text files line-by-line, split by `=`, and trim whitespace is re-implemented four separate times to parse `.cfg`, `.stamp`, and `.secrets` files. It should be consolidated into a generic configuration loader to reduce binary size and eliminate duplicated buffer overflow risks.