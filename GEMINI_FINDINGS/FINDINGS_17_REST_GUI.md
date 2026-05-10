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