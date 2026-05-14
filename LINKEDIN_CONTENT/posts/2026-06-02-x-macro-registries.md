# LinkedIn Post Design Doc

**Topic ID:** #8
**Target Date:** 2026-06-02
**Primary Pillar:** Pattern Library

**Style Checklist:**
- [x] Is it almost entirely lowercase (including "i", start of sentences)?
- [x] Is the formatting natural (no forced manual line breaks)?
- [x] Did I use ASCII arrows (`-> `) for the technical bullet points?
- [x] Is the tone calm, deeply technical, and matter-of-fact (no childish slang, no spaced-out caps)?
- [x] Does it follow the structure: Intro Feat/Problem -> Context -> "what makes it fast:" list -> Conclusion/Benchmarks?

## Strategy & Breakdown
focuses on eradicating "n-site" bugs (forgetting to update a parser/struct) by using x-macro registries as the single source of truth.

## Draft

---
adding one field to your system shouldn't require touching 5 different files.

if you're still manually updating parsers and structs, you're begging for an n-site bug. you add a config parameter and update the struct but forget the json parser. suddenly your backtest and production are completely out of sync.

here's how registry-driven architecture makes it physically impossible to forget a site:

-> i use x-macro registries with y3 dispatch where one row generates everything.
-> the registry is a single list of fields with types and metadata acting as the single source of truth.
-> y3 dispatch uses token-pasting to conditionally include fields in specific views.
-> autopopulate handles all the boilerplate. if it's in the macro, it's everywhere.

don't fix bugs, extinguish them. do you trust your memory or your compiler?

#hft #cpp #metaprogramming #cleancode
---