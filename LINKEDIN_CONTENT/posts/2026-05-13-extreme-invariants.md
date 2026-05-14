# LinkedIn Post Design Doc

**Topic ID:** #1
**Target Date:** 2026-05-13
**Primary Pillar:** Philosophy

**Style Checklist:**
- [x] Is it almost entirely lowercase (including "i", start of sentences)?
- [x] Is the formatting natural (no forced manual line breaks)?
- [x] Did I use ASCII arrows (`-> `) for the technical bullet points?
- [x] Is the tone calm, deeply technical, and matter-of-fact (no childish slang, no spaced-out caps)?
- [x] Does it follow the structure: Intro Feat/Problem -> Context -> "what makes it fast:" list -> Conclusion/Benchmarks?

## Strategy & Breakdown
focuses on the overarching extreme invariants that define the hft architecture. lists the top 5 banned practices.

## Draft

---
performance isn't about what you add, it's about what you have the guts to ban.

in my engine, extreme invariants aren't suggestions, they are the law. break them and the build fails. i operate under a scorched-earth policy for latency.

what makes it fast:

-> zero system allocators. malloc is banned. i pre-allocate into custom pools.
-> zero vtables. dynamic dispatch stalls the pipeline. i use template monomorphization and x-macros.
-> zero mutexes. asking the os to manage threads is a joke. lock-free only.
-> zero branches. an if statement is a catastrophe. i use bitwise math and cmov.
-> zero floating point. ieee-754 is non-deterministic. i built a custom fixed-point library for bytewise parity.

high performance is the result of removing abstractions. what's the most extreme constraint you've worked under?

#hft #cpp #lowlatency #systemsengineering
---