# ML_OPTIMIZATIONS: Performance & Latency Targets (v5.11)

Following the architectural spirit of v5.11 (decoupling, breakdown profiling, and per-core efficiency), the following ML infrastructure optimizations are proposed to reduce latency and improve throughput under the 32GB RAM envelope, while ensuring no behavioral drift between live and backtest.

## 1. Feature Registry & Compute Profiling
Similar to the "Per-Section Latency Stats" in v5.11, the ML execution pipeline (specifically `ModelInference.hpp`) lacks visibility into the cost of individual feature compute functions.

- **Proposal:** Implement `FeatureComputeStats` bracketed around `FEATURE_COMPUTE_FN` invocations.
- **Goal:** Identify "heavy" feature functions (e.g., complex windowing/rolling stats) that contribute to slow-path jitter.
- **Safety:** Use the same `__rdtsc` bracketing as the slow-path breakdown. Observability only — no behavioral change.

## 2. SIMD-Friendly Feature Standardization
Current `FeatureStandardizer` uses `mean` and `stddev` scalars. With AVX-512 available, we can standardize multiple features in parallel.

- **Proposal:** Vectorize `FeatureStandardizer` to operate on blocks of 8-16 features at once using `_mm512_sub_pd` and `_mm512_div_pd`.
- **Hardware Tuning:** Align `FeatureRegistry` output buffers to 64-byte boundaries (Cache Line) to ensure full vectorization efficiency.
- **Invariants Check:** Ensure standardization floor (`stddev > 1e-6`) remains bit-identical to current logic to avoid live/backtest divergence.

## 3. Model Inference Warm-up & Pinning
ML model inference (`ModelInference.hpp`) is currently invoked on-demand in the slow path.

- **Proposal:** Explicitly pre-warm the instruction cache for loaded models at boot/reload. Given the 32GB RAM limit, we can afford to pin model weights in `mlockall` regions and potentially pre-load branch predictors with dummy calls to the `XGBoosterPredict` entry points.
- **Impact:** Reduces tail latency on the first prediction call after a model reload.

## 4. Memory Alignment & Cache Locality
- **Proposal:** Audit `FeatureRegistry` and `RollingStats` structs. Ensure that rolling window state is dense in memory.
- **Target:** 32GB RAM is large, but L3 cache is the bottleneck. Consolidate features into a single, contiguous cache-aligned array per-core rather than multiple allocations, reducing TLB pressure.

---
**Implementation Note:** Any changes MUST satisfy the bitwise-identical requirement (standardized against the current `FeatureStandardizer` reference implementation). Verify with `tests/ml_parity_test` (if available) or create a regression test capturing input/output pairs from current production runs.
