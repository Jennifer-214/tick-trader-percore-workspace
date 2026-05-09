# Phase 14: Hardware Architecture & L1/L2 Cache Spills

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
    - **Details:** Several internal math helpers directly cast the `uint64_t w[N_WORDS]` array to larger pointer types (like `__uint128_t*`) for vectorized loads. While x86 tolerates unaligned vector loads, ARM architectures will throw a `SIGBUS` (Bus Error) or silently corrupt the data if the `FPN` struct happens to fall on an unaligned stack boundary.