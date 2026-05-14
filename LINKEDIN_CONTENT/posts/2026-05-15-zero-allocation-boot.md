# LinkedIn Post Design Doc

**Topic ID:** #2
**Target Date:** 2026-05-15
**Primary Pillar:** Philosophy

**Style Checklist:**
- [x] Is it almost entirely lowercase (including "i", start of sentences)?
- [x] Is the formatting natural (no forced manual line breaks)?
- [x] Did I use ASCII arrows (`-> `) for the technical bullet points?
- [x] Is the tone calm, deeply technical, and matter-of-fact (no childish slang, no spaced-out caps)?
- [x] Does it follow the structure: Intro Feat/Problem -> Context -> "what makes it fast:" list -> Conclusion/Benchmarks?

## Strategy & Breakdown
focuses on the need for zero allocations on the hot path. attacks malloc and std::vector in favor of pre-allocated arenas and pools.

## Draft

---
calling new during a trade is bad. if you're touching the heap while the market is moving, you've already lost.

standard os allocators are built for normies, not microsecond killers. malloc involves non-deterministic kernel locks and fragmentation. if your loop triggers a heap rebalance, you're watching the trade from the sidelines.

here's how i enforce a strict zero system allocators policy:

-> all memory is mapped before the first tick. i use an init-arena pattern with huge pages to bootstrap everything.
-> orders live in bitmap-indexed pools where finding a free slot is a single __builtin_ctzll instruction.
-> hot arrays are physically backed and l1-ready before the market opens. 

determinism means being fast every single time. preallocate everything. still relying on vector growth?

#hft #lowlatency #systemsprogramming #cpp
---