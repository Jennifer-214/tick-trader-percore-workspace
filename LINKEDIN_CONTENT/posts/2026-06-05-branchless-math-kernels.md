# LinkedIn Post Design Doc

**Topic ID:** #9
**Target Date:** 2026-06-05
**Primary Pillar:** Pattern Library

**Style Checklist:**
- [x] Is it almost entirely lowercase (including "i", start of sentences)?
- [x] Is the formatting natural (no forced manual line breaks)?
- [x] Did I use ASCII arrows (`-> `) for the technical bullet points?
- [x] Is the tone calm, deeply technical, and matter-of-fact (no childish slang, no spaced-out caps)?
- [x] Does it follow the structure: Intro Feat/Problem -> Context -> "what makes it fast:" list -> Conclusion/Benchmarks?

## Strategy & Breakdown
focuses on eliminating variable-length loops on the hot path in favor of constant-iteration branchless math kernels to ensure deterministic latency and enable simd auto-vectorization.

## Draft

---
variable-length loops are a code smell in hft math. if your inner loop has an if guard, you've already lost the battle for tail latency.

linear algebra on the hot path loves to hide variable latency behind dynamic bounds. this prevents the compiler from auto-vectorizing and makes performance non-deterministic.

here's how i use the constant-iteration plus zero-invariant pattern:

-> i pre-zero the output arrays.
-> i establish constant bounds and always iterate to the maximum possible count.
-> i rely on ieee-754 invariants where x * 0.0 = 0.0. the extra iterations become bytewise no-ops that the cpu handles in its sleep.
-> by forcing constant iterations, i allow the compiler to emit avx-512 fmadd instructions for the entire loop without branching.

deterministic code is faster because it's predictable. pure math. do you prioritize raw speed or consistency in your math kernels?

#hft #cpp #simd #lowlatency
---