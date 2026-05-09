# Phase 8: Advanced Backtest & Edge Parsing Bugs

## NEW Ultra-Obscure Issues (69-78)

1. **Held-Out Validation Lookahead Bias** (`Backtest/HeldOutSplit.hpp`)
   - **Details:** The `HeldOutSplit_Make` boundary sets the eval set immediately after the training set without injecting the required $h$ (maximum hold time) purge gap. This causes temporal data leakage, as the first labels in the held-out eval set use future market state that overlaps with the final training samples.
2. **Double-Buffer Race Condition in Book Snapshots** (`DataStream/BinanceDepth.hpp`)
   - **Details:** The depth thread populates a double-buffer system for order book snapshots. However, the atomic swap pointer (`active_book`) lacks an accompanying seqlock or RCU mechanism. If the engine thread reads it while the depth thread flips and overwrites the background buffer, the engine will read a partially corrupted (torn) order book.
3. **VWAP Accumulation Precision Loss** (`GUI/CandleAccumulator.hpp`)
   - **Details:** `CandleAccumulator_Push` maintains a running `vwap_pv` (Price × Volume sum). Over long chart sessions without resetting, this scalar accumulates massively, leading to floating-point truncation when adding small tick volumes, corrupting the VWAP plot.
4. **SSL Non-Fatal Error Drop** (`DataStream/WebSocketUtil.hpp`)
   - **Details:** `ws_read_frame` calls `SSL_read` but does not adequately handle `SSL_ERROR_WANT_READ` or `SSL_ERROR_WANT_WRITE` in non-blocking contexts. Instead of spinning or polling, it treats it as a fatal disconnect, needlessly tearing down the WebSocket connection during minor network congestion.
5. **FixedPoint 192-bit Division Overflow Truncation** (`FixedPoint/FixedPoint64.hpp`)
   - **Details:** The schoolbook division logic (`FP64_DivNoAssert`) utilizes a 192-bit temporary intermediate for shifting. If the dividend is extremely large, the left-shift prior to division pushes bits entirely out of the 192-bit array, truncating the value silently and returning a heavily deflated quotient.
6. **XGBoost 16-Class Weight Clipping** (`Backtest/BacktestEngine.hpp`)
   - **Details:** `XGBoost_ComputeMulticlassWeights` allocates a fixed stack array of size 16 for class distributions. If the system is trained on a strategy with $>16$ discrete classes (e.g., granular regime grids), it will silently write out of bounds and corrupt the stack.
7. **Time-Density Bias in Walk-Forward Purging** (`Backtest/BacktestEngine.hpp`)
   - **Details:** The `nn_purge` calculation for temporal walk-forward gaps uses a static number of *ticks* rather than a strict *time window*. During periods of extreme low volatility (night sessions), the tick gap covers vastly more time than during open sessions, breaking the temporal uniformity of the validation splits.
8. **Discontinuous History Gaps in TUI Rendering** (`GUI/CandleAccumulator.hpp`)
   - **Details:** If the market halts or no trades occur for several intervals, `CandleAccumulator` does not insert empty "doji" candles to pad the time gap. This shifts the entire visual X-axis, destroying the temporal continuity of moving averages rendered on the chart.
9. **Unstable Variance in VolBarrier Labels** (`Backtest/LabelFunctions.hpp`)
   - **Details:** `Label_VolBarrier` uses a naive $E[X^2] - (E[X])^2$ formula for variance computation rather than a numerically stable Welford pass. For prices far from 0 (like BTC at 60,000), catastrophic cancellation occurs, resulting in negative or zero variance and broken labels.
10. **ML Zoo Persistence Leak** (`Backtest/BacktestSharded.hpp`)
    - **Details:** Between consecutive walk-forward validation folds, the `EnsembleModelZoo` is not completely destructed before being re-initialized. Memory handles for underlying XGBoost `Booster` instances from previous folds are leaked into the heap, eventually causing the training runner to OOM on long backtests.