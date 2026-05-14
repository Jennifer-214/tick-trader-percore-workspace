# LinkedIn Post Design Doc

**Topic ID:** #19
**Target Date:** 2026-07-05
**Primary Pillar:** Philosophy

**Style Checklist:**
- [x] Is it almost entirely lowercase (including "i", start of sentences)?
- [x] Is the formatting natural (no forced manual line breaks)?
- [x] Did I use ASCII arrows (`-> `) for the technical bullet points?
- [x] Is the tone calm, deeply technical, and matter-of-fact (no childish slang, no spaced-out caps)?
- [x] Does it follow the structure: Intro Feat/Problem -> Context -> "what makes it fast:" list -> Conclusion/Benchmarks?

## Strategy & Breakdown
this post attacks the practice of applying the same patch multiple times instead of fixing the root architectural cause. it emphasizes the "rule of three" and structural fixes over lazy direct patches.

## Draft

---
if you're fixing the same type of bug for the third time, stop. you don't have a bug, you have an architectural debt. 

every dev has a choice between the direct patch, which is fast but lazy, or the structural fix that extinguishes the bug class entirely. one gets the pr merged today and the other makes sure you never merge it again. 

here's how i enforce the rule of three:

-> first occurrence is a direct patch because maybe it's a one-off.
-> second occurrence is a patch plus tagging it in my recurring bug patterns ledger.
-> third occurrence is a mandatory structural fix. i redesign the system so the bug is physically impossible to write.

senior engineers fix the process of writing code, not just the code itself. what bug class are you extinguishing this week?

#hft #softwarearchitecture #technicaldebt
---