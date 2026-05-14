# LinkedIn Post: Cache Layout Discipline

**Topic ID:** #7
**Target Date:** 2026-05-30
**Primary Pillar:** Pattern Library

---

## 1. The Hook (First 2 Lines)
*Goal: Stop the scroll. Challenge an assumption or state a surprising result.*

Your C++ struct layout is probably killing your L1 cache performance. 
If you aren't grouping fields by access frequency, you're paying for "noise" in every cycle.

---

## 2. The Context/Problem
*Goal: Why does this matter? What's the pain point?*

In HFT, every cache miss is a 100ns disaster. As structs grow, they accumulate "bloat": telemetry, debug strings, and display-only metadata. 
When these are interleaved with hot-path data, a single cycle pull for a price update fetches 4 cache lines of human-readable arm names that the engine doesn't even need.

---

## 3. The Technical Solution
*Goal: High-signal insight. Use lists or code-like snippets.*

We enforce **HOT/WARM/COLD** clustering for every hot-side struct:

- **HOT Cluster:** Fields touched every single cycle (weights, barriers). Kept in the first 2 cache lines.
- **COLD Extraction:** Display-only metadata (strings, descriptions) is moved to a sibling "DisplayMeta" struct. The engine never touches it.
- **False Sharing Protection:** Use `alignas(64)` on cross-thread fields (like atomic sequence numbers) to ensure they don't share a line with single-writer hot data.

```cpp
struct alignas(64) EnsembleModelZoo {
    // HOT: Line 0
    alignas(64) float per_arm_barriers[16]; 
    // WARM: Line N
    alignas(64) RidgeWeights<F> state;
    // COLD: Extracted to EnsembleDisplayMeta
};
```

---

## 4. The "Aha!" Moment / Lesson
*Goal: What should the reader take away?*

"Feature grouping" is for humans. "Frequency grouping" is for CPUs. 
By extracting display names out of our `BanditState`, we reduced its cache footprint from 8 lines to 4, saving ~400ns per cold-cache access.

---

## 5. Call to Action (CTA)
*Goal: Drive engagement/comments.*

Do you audit your struct layout for cache-line straddling, or do you leave it to the compiler?

---

## 6. Hashtags
*Copy from TAG_LIBRARY.md*

#HFT #Cpp #LowLatency #SoftwareArchitecture #CacheOptimization #PerformanceEngineering
