# Phase 12: Machine Learning Blending & Recorder Bugs

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
    - **Details:** `RidgeBlender_BuildCorr` constructs the correlation matrix without verifying that the inputs (predictions and targets) are finite. Non-finite inputs will immediately contaminate the matrix, destroying the blending process.