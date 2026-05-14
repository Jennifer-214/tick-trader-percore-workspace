# LinkedIn Post: Fixed-Point Determinism

**Topic ID:** #5
**Target Date:** 2026-05-24
**Primary Pillar:** Pattern Library

---

## 1. The Hook (First 2 Lines)
Why `double` is a landmine for cross-platform backtesting. If your dev machine and your production server don't agree on the last digit of a price, your backtest is lying to you.

---

## 2. The Context/Problem
IEEE-754 floating-point math is fast, but it’s not always deterministic across different compilers, optimization levels, or hardware architectures. A 1-ULP (Unit in the Last Place) difference in a price calculation might seem tiny, but when that value is used as a threshold for a trade signal, it can cause your backtest to enter a trade that the live server skips. This "mirror drift" makes alpha research a nightmare.

---

## 3. The Technical Solution
We replaced floating-point math in our core engine with a custom **Fixed-Point Library** (`FixedPointN.hpp`).

- **Integer Underpinnings:** Prices and quantities are stored as wide integers (e.g., 256-bit or 512-bit) with a fixed number of fractional bits. 
- **Bitwise Exactness:** Comparisons like `FPN_LessThanOrEqual` produce the exact same bit-for-bit result regardless of the CPU or optimization flags.
- **Branchless Min/Max:** We implement `Min` and `Max` using word-level mask-selection, ensuring no data-dependent branches even in our math kernels.
- **Cross-Binary Parity:** By avoiding the FPU entirely, we guarantee that a scalar build and an AVX-512 build produce identical trade signals for the same input.

---

## 4. The "Aha!" Moment / Lesson
Determinism is the foundation of confidence. In trading, performance is secondary to correctness. If you can't replay a live session in your backtester and get the exact same byte-identical fills, you can't trust your strategy's performance metrics.

---

## 5. Call to Action (CTA)
Have you ever chased a "ghost" bug that only appeared in production but disappeared in your local debug build? How much do you trust `double` in your critical decision paths?

---

## 6. Hashtags
#HFT #Cpp #SoftwareEngineering #LowLatency #ModernCpp #QuantitativeFinance #AlgorithmicTrading #PerformanceOptimization
