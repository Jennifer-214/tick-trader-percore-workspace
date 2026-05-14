# LinkedIn Post: Lock-Free Seqlocks

**Hook:** In a sub-microsecond trading engine, a `mutex` isn't just slow—it's a bug. 

When you need to pass high-frequency parameters (like entry thresholds or risk limits) from a slow-path "Adapt" thread to a hot-path "Execution" thread, you can't afford to block. Even a uncontended mutex involves a system call or a heavy atomic operation that can stall the pipeline.

**The Problem:** How do you read a multi-word struct (like a set of 24-byte FPN prices) without risking a "torn read" where you get half of the old values and half of the new ones?

**The Solution:** The Seqlock (implemented in our engine as `ParameterSlot`).

Here is how the discipline works:

1. **The Version Counter:** We use a single atomic `uint64_t` version counter.
2. **The Writer:**
   - Increment the version (it's now odd).
   - Write the data (relaxed memory order is fine here).
   - Increment the version again (it's now even).
3. **The Reader:**
   - Read the version. If it's odd, a write is in progress; spin and wait.
   - Read the data into a local cache.
   - Read the version again. 
   - **The Catch:** If the version changed (or is still odd), the data was "torn" during the read. Discard and retry.

**The Result:**
- **Wait-Free Writer:** The producer never blocks for a reader. 
- **Lock-Free Reader:** The hot path only retries in the rare event of a collision (nanoseconds).
- **Zero System Calls:** Purely in-process, cache-coherent synchronization.

In HFT, we don't share memory by communicating; we communicate by sharing memory—very, very carefully.

#HFT #Cpp #LowLatency #Concurrency #SystemsProgramming #SoftwareArchitecture
