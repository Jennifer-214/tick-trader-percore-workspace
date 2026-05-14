# LinkedIn Post Design Doc

**Topic ID:** #5
**Target Date:** 2026-05-24
**Primary Pillar:** Pattern Library

**Style Checklist:**
- [x] Is it almost entirely lowercase (including "i", start of sentences)?
- [x] Is the formatting natural (no forced manual line breaks)?
- [x] Did I use ASCII arrows (`-> `) for the technical bullet points?
- [x] Is the tone calm, deeply technical, and matter-of-fact (no childish slang, no spaced-out caps)?
- [x] Does it follow the structure: Intro Feat/Problem -> Context -> "what makes it fast:" list -> Conclusion/Benchmarks?

## Strategy & Breakdown
focuses on eradicating ieee-754 floating point numbers in favor of strict fixed-point integer math to achieve cross-binary determinism.

## Draft

---
using double for backtesting is a landmine. 

if your dev machine and production server disagree on the last digit of a price, your backtest is just expensive fiction. ieee-754 is not deterministic across compilers or hardware. a 1-ulp diff causes mirror drift and ruins models.

here's how i replaced the fpu with a custom fixed-point library:

-> prices are stored as wide 256-bit integers with fixed fractional bits.
-> bitwise exactness is enforced everywhere.
-> i use branchless math for min and max via word-level mask-selection.
-> scalar and avx-512 builds produce identical signals.

determinism is the foundation of confidence. if you can't replay a live session and get byte-identical results, you're guessing. still trust double in your critical paths?

#hft #cpp #softwareengineering #lowlatency
---