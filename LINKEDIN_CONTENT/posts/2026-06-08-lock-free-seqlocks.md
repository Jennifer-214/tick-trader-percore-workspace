# LinkedIn Post Design Doc

**Topic ID:** #10
**Target Date:** 2026-06-08
**Primary Pillar:** Philosophy

**Style Checklist:**
- [x] Is it almost entirely lowercase (including "i", start of sentences)?
- [x] Is the formatting natural (no forced manual line breaks)?
- [x] Did I use ASCII arrows (`-> `) for the technical bullet points?
- [x] Is the tone calm, deeply technical, and matter-of-fact (no childish slang, no spaced-out caps)?
- [x] Does it follow the structure: Intro Feat/Problem -> Context -> "what makes it fast:" list -> Conclusion/Benchmarks?

## Strategy & Breakdown
focuses on the need for wait-free synchronization (seqlocks) instead of traditional mutexes, highlighting the pipeline stall cost.

## Draft

---
in a sub-microsecond trading engine, a mutex isn't just slow, it's a bug.

when you pass data from a slow-path thread to a hot-path thread, you cannot afford to block. even an uncontended mutex involves a system call or heavy atomic that stalls the pipeline.

here's how i use the seqlock to read a multi-word struct without tearing:

-> the writer increments an atomic version to an odd number, writes the data, then increments to an even number. wait-free and happy.
-> the producer never blocks and performs zero system calls. 
-> the reader checks the version. if it's odd, a write is in progress, so it spins.
-> if even, the reader reads the data into local cache and checks the version again. if it changed, the data tore, so discard and retry.

wait-free writer and lock-free reader. i don't share memory by communicating, i communicate by sharing memory very carefully. are you still using locks for updates like it's 1995?

#hft #cpp #lowlatency #concurrency
---