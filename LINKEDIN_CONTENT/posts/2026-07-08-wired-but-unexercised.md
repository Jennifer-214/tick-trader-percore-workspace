# LinkedIn Post: Wired but Unexercised

**Hook:** The most dangerous code in your repository isn't the code that fails the build. It's the code that compiles perfectly but never actually runs.

We call this the **"Wired but Unexercised"** gap. 

It happens in large-scale systems where logic is mirrored across multiple "shadow" paths—like a live trading path and a background "Simulation" path. You add a new risk check to the live path. It works. It passes tests. But you forgot to wire it into the simulation path.

**The Consequence:** 
The simulation path (which you use to validate new strategies) now uses stale risk logic. It tells you a strategy is safe when it isn't. You ship the strategy, and it hits a limit in production that the simulation never saw.

**How We Audit for Gaps:**

1. **Call-Graph Diffing:** We use custom tooling to map every incoming market data event to its final consumer. If a logic block exists but isn't reached by the "Simulation" driver, the build fails.
2. **In-Loop Assertions:** We add `is_exercised` flags to our shadow paths during integration tests. If a test completes and the flag is zero, the test fails.
3. **Registry-Driven Wiring:** We move all "shadow" logic into shared registries so that wiring is automatic and structural, not manual.

**The Lesson:** "It compiles" is the lowest possible bar. "It's exercised" is the only one that matters. 

#HFT #SoftwareTesting #SystemsEngineering #SoftwareArchitecture #Reliability #Cpp
