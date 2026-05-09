# Phase 9: Deep Concurrency & Recovery Edge Cases

## NEW Ultra-Obscure Issues (79-88)

1. **Seqlock Load-Load Barrier Missing** (`CoreFrameworks/ParameterSlot.hpp`)
   - **Details:** `ParameterSlot_Read` copies the data payload after checking the initial sequence number but before checking the final sequence number. It relies on relaxed loads and compiler fences, but lacks an explicit `std::atomic_thread_fence(std::memory_order_acquire)`. On weakly-ordered architectures (like ARM), the data read can be reordered after the second sequence check, yielding torn reads.
2. **`ws_active` Relaxed Atomic Race** (`CoreFrameworks/BinanceAdapter.hpp`)
   - **Details:** The `ws_active` synchronization flag uses `std::memory_order_relaxed`. Without acquire/release barriers, visibility of this flag's state change is not guaranteed to propagate to other cores instantly, potentially leading to a race condition where fills are double-processed or dropped during reconnection states.
3. **Stale Orderbook Levels on Shallow Updates** (`DataStream/BinanceDepth.hpp`)
   - **Details:** If an orderbook update from the exchange contains fewer than the tracked depth levels (e.g., < 5 levels), the `depth_parse_json` logic fails to clear or zero-out the old levels at the bottom of the book array. The engine will trade against phantom liquidity.
4. **Sequence Desync on Partial Parse** (`DataStream/BinanceDepth.hpp`)
   - **Details:** If `depth_parse_json` encounters a malformed or partial JSON payload, it bails out early but sometimes leaves `lastUpdateId` carried over or partially updated. This breaks the contiguous sequence validation (`U` vs `u` events), forcing unnecessary total book resynchronizations.
5. **Float-to-Fixed Point Truncation Bias** (`FixedPoint/FixedPointN.hpp`)
   - **Details:** `FPN_FromString` algorithmically parses decimal strings by multiplying by 10 and adding digits. It completely truncates fractional remainders beyond its precision capacity rather than rounding to nearest (e.g., round half to even). This introduces a systematic downward bias in heavily decimalized pricing data.
6. **Double-to-Fixed Point Truncation Bias** (`FixedPoint/FixedPointN.hpp`)
   - **Details:** `FP64_FromDouble` and similar double conversion helpers cast the float directly to an integer format during bitwise extraction. Like string parsing, this truncates rather than rounding, causing identical systematic negative drift on high-frequency accumulations.
7. **Float-to-Int Rounding Instability** (`DataStream/BinanceOrderAPI.hpp`)
   - **Details:** `binance_round_qty` divides floating-point representations and casts directly to `int64_t`. Because of IEEE-754 representation flaws (e.g., 0.1 being slightly less than 0.1), direct int casting can result in off-by-one truncation (e.g., calculating 9.9999 as 9 instead of 10). It requires adding a small epsilon or using `std::round` before casting.
8. **Inverse Branch Prediction Hint in Polling** (`CoreFrameworks/SPSCRing.hpp`)
   - **Details:** `SPSCRing_TryPop` annotates the check for an empty queue with `[[unlikely]]` (or `__builtin_expect`). In a busy-wait polling architecture where the hot loop runs millions of times per second, the queue is actually empty 99.99% of the time. The compiler optimizes the assembly for the exact wrong branch path, devastating instruction cache and pipeline efficiency.
9. **Transcendental Constant Precision Bottleneck** (`FixedPoint/FixedPointN.hpp`)
   - **Details:** The constants used in the Taylor series approximations for `FPN_Sin` and `FPN_Exp` are stored with hardcoded 64-bit precision arrays. If the template is expanded to $F > 64$, these constants do not scale their precision, causing catastrophic precision bottlenecks in ML probability functions relying on them.
10. **Error Recovery Spinloop on Rate Limits** (`CoreFrameworks/ReconciliationLoop.hpp`)
    - **Details:** If the Binance REST API returns an HTTP 429 (Too Many Requests) or 503 during a reconciliation pass, the loop retries immediately without an exponential backoff or circuit breaker. This traps the reconciliation thread in a tight spinloop, burning CPU cycles and prolonging the IP ban from the exchange.