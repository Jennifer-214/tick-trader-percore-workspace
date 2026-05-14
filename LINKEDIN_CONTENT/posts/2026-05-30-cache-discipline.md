# LinkedIn Post Design Doc

**Topic ID:** #7
**Target Date:** 2026-05-30
**Primary Pillar:** Pattern Library

**Style Checklist:**
- [x] Is it almost entirely lowercase (including "i", start of sentences)?
- [x] Is the formatting natural (no forced manual line breaks)?
- [x] Did I use ASCII arrows (`-> `) for the technical bullet points?
- [x] Is the tone calm, deeply technical, and matter-of-fact (no childish slang, no spaced-out caps)?
- [x] Does it follow the structure: Intro Feat/Problem -> Context -> "what makes it fast:" list -> Conclusion/Benchmarks?

## Strategy & Breakdown
focuses on the performance penalty of poor struct layouts and advocates for frequency-based hot/warm/cold cache discipline and false sharing protection.

## Draft

---
your cpp struct layout is probably killing your l1 cache performance.

if you aren't grouping fields by access frequency, you're just paying for noise in every cycle. grouping by logic is for humans, but grouping by frequency is for cpus. every cache miss is a 100ns disaster. if your price update fetches 4 cache lines of human-readable debug strings that the engine doesn't need, you've lost.

here's how i enforce strict cache discipline for every struct on the hot path:

-> hot fields that i touch every cycle live in the first two cache lines. no exceptions.
-> cold display metadata is extracted to a sibling struct so the engine never touches it during a trade.
-> i use alignas(64) on cross-thread fields to protect against false sharing.

moving display names out of my bandit state reduced its cache footprint from 8 lines to 4, saving me 400ns per cold access. layout is logic. do you audit your struct layout or just let the compiler scatter your data?

#hft #cpp #cacheoptimization #lowlatency
---