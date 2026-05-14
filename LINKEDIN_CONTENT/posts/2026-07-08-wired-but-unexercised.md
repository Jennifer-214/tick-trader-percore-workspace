# LinkedIn Post Design Doc

**Topic ID:** #20
**Target Date:** 2026-07-08
**Primary Pillar:** Philosophy

**Style Checklist:**
- [x] Is it almost entirely lowercase (including "i", start of sentences)?
- [x] Is the formatting natural (no forced manual line breaks)?
- [x] Did I use ASCII arrows (`-> `) for the technical bullet points?
- [x] Is the tone calm, deeply technical, and matter-of-fact (no childish slang, no spaced-out caps)?
- [x] Does it follow the structure: Intro Feat/Problem -> Context -> "what makes it fast:" list -> Conclusion/Benchmarks?

## Strategy & Breakdown
focuses on the danger of code that compiles but is never executed in the simulation paths. the angle is about enforcing execution via call-graph diffing and in-loop assertions so that untested "shadow" code doesn't blow up production.

## Draft

---
the most dangerous code in your repo isn't the code that fails. it's the code that compiles perfectly but never actually runs. unexercised logic is a silent threat.

logic is often mirrored in shadow paths like live vs simulation. you add a risk check to live but forget the sim path. now your simulation tells you a strategy is safe but production hits a limit you never saw coming. "it compiles" is the lowest possible bar.

here's how i audit for these gaps:

-> call-graph diffing maps every market event to its final consumer. if a block isn't reached by the simulation driver, the build fails.
-> in-loop assertions use is_exercised flags during integration. if a test finishes and the flag is zero, the test fails.
-> registry-driven wiring moves shadow logic into shared registries so wiring is automatic and structural, not manual.

is your safety code actually running, or are you just hoping it is?

#hft #softwaretesting #architecture
---