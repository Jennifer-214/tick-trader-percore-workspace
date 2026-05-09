# Phase 11: Deep System & Bitwise Edge Cases

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
    - **Details:** In `binance_tcp_connect`, if the `socket()` call succeeds but `connect()` fails, the loop calls `close(sockfd)` and correctly continues. However, there is a path where `getaddrinfo` structures might not be fully freed if the function bails early, causing a minor memory leak during heavy reconnect looping.