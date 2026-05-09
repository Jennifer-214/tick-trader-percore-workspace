# Phase 15: Strategies, Logging & Fixed-Point Limits

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
    - **Details:** In `DashboardPanels.hpp`, mapping strategies to theme colors (`strat_colors[sid]`) relies on `sid` not exceeding the length of the predefined color array. If a new strategy is added with an ID greater than the array bounds, it will trigger a heap out-of-bounds read during UI rendering, potentially crashing the monitoring application.