# LinkedIn Post Design Doc

**Topic ID:** #1
**Target Date:** 2026-05-13
**Primary Pillar:** Philosophy

**Style Checklist:**
- [x] Is it anti-corporate? (No fluff)
- [x] Did I use "Spaced-Out Caps" for the load-bearing concept?
- [x] Are pronouns lowercase (i, im, idk)?
- [x] Is punctuation minimal and conversational?
- [x] Are lines manually wrapped to 40-60 characters for LinkedIn readability?
- [x] Are there 2-3 distinct options to choose from?

## Strategy & Breakdown
Focuses on the overarching "Extreme Invariants" that define the HFT architecture. Lists the top 5 banned practices.

## Draft Options

---
**Option 1: The Blunt & Technical**

performance isnt about what you add its
about what you have the guts to B A N.

in our engine extreme invariants arent
suggestions they are the law. break them
and the build fails. we operate under a
scorched-earth policy for latency.

1. zero system allocators. malloc is
I C K Y. we pre-allocate into custom pools.
2. zero vtables. dynamic dispatch stalls
the pipeline. we use template
monomorphization and x-macros.
3. zero mutexes. asking the OS to manage
threads is a joke. lock-free only.
4. zero branches. an if statement is a
C A T A S T R O P H E. we use bitwise
math and cmov.
5. zero floating point. ieee-754 is
non-deterministic. we built a custom
fixed-point library for bytewise parity.

high performance is the result of removing
abstractions.

whats the most extreme constraint youve
worked under?

#HFT #Cpp #LowLatency #SystemsEngineering
---

---
**Option 2: The Conversational & Analogy-Heavy**

its like 3am and im thinking about how
performance is mostly just having the guts
to B A N things lol. 

we have these extreme invariants and if
you break them the build dies. crying
wont help. malloc is I C K Y so no system
allocators. no vtables because dynamic
dispatch is like asking for directions
in a city you hate. W I L D. no mutexes
because context switching is the enemy.

no branches on the hot path because an
if statement is basically a
C A T A S T R O P H E for the pipeline.
and no floating point math because ieee
754 is garbage and ruins backtests. we
use fixed-point integer math everywhere.
praise be.

if the CPU has to think youve already
lost. 

are you still using std string on the
hot path?

#HFT #SoftwareArchitecture #NoFluff
---

---
**Option 3: The Short & Punchy**

performance isnt about what you add its
about what you have the guts to B A N.

extreme invariants are the law. break them
and the build fails.

1. zero system allocators. malloc is
I C K Y. pre-allocate everything.
2. zero vtables. use templates instead.
3. zero mutexes. lock-free concurrency
only.
4. zero branches. an if statement is a
C A T A S T R O P H E. use cmov.
5. zero floating point. fixed-point
ensures byte determinism.

high performance comes from removing
abstractions. if the CPU has to guess
youve lost.

whats your most extreme constraint?

#HFT #Cpp #LowLatency #Programming
---