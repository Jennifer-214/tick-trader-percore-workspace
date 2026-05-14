# LinkedIn Post Design Doc

**Topic ID:** #13
**Target Date:** 2026-06-17
**Primary Pillar:** Philosophy

**Style Checklist:**
- [x] Is it almost entirely lowercase (including "i", start of sentences)?
- [x] Is the formatting natural (no forced manual line breaks)?
- [x] Did I use ASCII arrows (`-> `) for the technical bullet points?
- [x] Is the tone calm, deeply technical, and matter-of-fact (no childish slang, no spaced-out caps)?
- [x] Does it follow the structure: Intro Feat/Problem -> Context -> "what makes it fast:" list -> Conclusion/Benchmarks?

## Strategy & Breakdown
focuses on the architectural flaw of orphaned code (e.g., wiring an init but forgetting the exit). advocates for an auto-dispatched x-macro registry to enforce lifecycle completeness.

## Draft

---
the most dangerous code in your repo isn't the code that fails. it's the code that is orphaned.

you're porting a feature. you wire the init and you wire the loop. it looks green but you forgot the exit logic. your strategies enter trades perfectly but they stop adapting to the market. the code compiles and tests pass, but your engine is flying blind. 

here's how i moved to a strategy interface contract enforced by x-macros:

-> every strategy is defined in one row like X(StrategyName, Init, Adapt, Build, Exit).
-> the engine auto-generates the dispatch table so you physically can't forget a lifecycle stage.
-> my custom tool diffs the call graph, and if a stage exists but isn't called, the build fails. no orphans allowed.

change the architecture so the bug becomes physically impossible. how many orphaned features are lurking in your repo?

#hft #cpp #softwarearchitecture
---