# LinkedIn Post: Silent NaN Poisoning

**Hook:** How one `NaN` in a feature pack can kill an entire Machine Learning pipeline without a single error log.

In high-performance systems, we often bypass standard logging and exception handling because they are too slow for the hot path. But that silence comes with a price.

**The Horror Story:** 
A market data feed produces a single corrupted tick with a zero price. Your code calculates a return: `(price / last_price) - 1`. Suddenly, you have a `NaN` (Not a Number) in your feature vector.

That `NaN` propagates:
- The EMA of that feature becomes `NaN`.
- The ML model's prediction becomes `NaN`.
- The risk check (which uses `<` comparisons) fails silently because `NaN < X` is always false.
- Your engine stops trading. No errors, no crashes—just total, silent paralysis.

**The Fix: Defensive Bounds & SIMD Guards**

We implemented three layers of protection:
1. **The FPN Guard:** Our custom Fixed-Point (FPN) library treats division-by-zero as a saturated MAX value, not a `NaN`, ensuring arithmetic stays "poison-free."
2. **SIMD Masking:** During feature packing, we use AVX-512 comparison masks to "clamp" all features to a safe range `[-10, 10]`. If a `NaN` slips in, the mask replaces it with a neutral `0.0` in a single cycle.
3. **Sanity Audits:** We added a "Noise Floor" invariant. If the input is too quiet (zero volatility), we disable the model entirely before the math can fail.

**The Lesson:** In mission-critical systems, silence is not golden—it's dangerous. If you can't afford to log, you must afford to be structurally safe.

#HFT #MachineLearning #MLOps #Cpp #SystemsEngineering #LowLatency
