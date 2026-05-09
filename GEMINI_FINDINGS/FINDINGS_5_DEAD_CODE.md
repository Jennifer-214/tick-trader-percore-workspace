# Phase 5: Deep System Audit & Dead Code Trace

## Part 1: NEW Obscure Issues

1. **Strict Aliasing Violation & UB** (`FixedPoint/FixedPointN.hpp`)
   - **Details:** The `_to_fp64` and `_from_fp64` helpers cast `uint64_t[]` to `__uint128_t*`. This violates C++ strict aliasing rules, potentially leading to incorrect compiler optimizations. Additionally, `w` arrays are not guaranteed to be 16-byte aligned, which causes undefined behavior on architectures that don't support unaligned vector loads.
2. **Unhandled SIGPIPE** (`main.cpp`)
   - **Details:** The engine lacks `signal(SIGPIPE, SIG_IGN)`. In HFT, sockets (Binance WS/REST) may reset unexpectedly. An `EPIPE` during `SSL_write` will trigger a `SIGPIPE` and immediately terminate the engine process.
3. **Socket Descriptor Leak** (`DataStream/BinanceUserData.hpp`)
   - **Details:** The `ud_ws_thread` loop calls `ud_tcp_connect`, then `ud_tls_setup` and `ud_ws_handshake`. If the TLS setup or WebSocket upgrade fails *after* TCP connect, the socket descriptor (`sockfd`) is not closed, leaking file descriptors until process exhaustion.
4. **Metric Aggregation Truncation** (`CoreFrameworks/EngineSharded.hpp` / `TUISnapshot`)
   - **Details:** `TUISnapshot` fields (e.g., `total_buys`, `total_exits_fills`) use `uint32_t`, but the source counters in `OrderManager` and `EventLoopAggregates` are `uint64_t`. Under high-frequency volume, these will wrap after ~4.2 billion events, corrupting TUI displays and downstream logging.
5. **Path Truncation and Unchecked I/O** (`DataStream/DepthRecorder.hpp`)
   - **Details:** `DepthRecorder_Init` uses `snprintf` to build `data_dir` without validating if the symbol string truncated the path. Furthermore, `mkdir` in `DepthRecorder_MkdirP` is called without checking return codes, risking data being written to invalid or root paths.
6. **Double-Rounding Parity Hazard** (`DataStream/BinanceCrypto.hpp` vs `ParseFast.hpp`)
   - **Details:** Although `BinanceCrypto.hpp` uses `FPN_ToDouble` and string parsers, legacy fallback paths use `tt::parse_double_fast`. Subtle rounding variations between `std::from_chars` and the manual fixed-point parser can break bytewise determinism across different compiler optimization levels.

## Part 2: Safe to Remove (Dead Code)

The following files/structures were traced and confirmed to be safely removable without impacting the production engine:

7. `ML_Headers/LinearRegressionSimple.hpp`
   - **Status:** Completely unused. All regression logic has moved to `LinearRegression3X.hpp`. 
8. `CoreFrameworks/LegacyReferenceDriver.hpp`
   - **Status:** Only referenced in the `experiments/` directory for head-to-head testing. It is not compiled into the main `build/engine` or `build/suite` paths. It should be moved out of `CoreFrameworks/` or deleted.
9. `DataStream/FauxFIX.hpp`
   - **Status:** Redundant. It relies on the legacy `FIX_ParseDouble`. The production engine now strictly uses `BinanceCrypto.hpp` combined with `ParseFast.hpp`.
10. `DataStream/WebSocketUtil.hpp` (Partial / Duplication)
    - **Status:** High code duplication. `BinanceCrypto.hpp` implemented its own inline WebSocket helpers, leaving `WebSocketUtil.hpp` loosely coupled only to `BinanceDepth.hpp`. This should be deduplicated and the file likely removed or consolidated.