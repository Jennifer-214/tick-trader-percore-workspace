# LinkedIn Post: Extreme HFT Invariants

**Hook:** In a sub-microsecond trading engine, performance isn't about what you *add*. It's about what you have the discipline to *ban*.

In our latest HFT engine iteration, we operate under a set of "Extreme Invariants." These aren't just suggestions; they are hard rules that, if broken, fail the build.

Here are 5 things we banned to guarantee deterministic, low-latency execution:

### 1. Zero System Allocators
No `malloc`, no `new`, no `std::vector`, no `std::string`. 
Why? The system allocator is a black box. It has locks. It has fragmentation. It has non-deterministic tail latency. 
**The Fix:** Everything is pre-allocated at startup into custom `PoolAllocator` or `BuddyAllocator` structures. If we run out of memory during a trade, we have a design flaw, not a runtime error.

### 2. Zero VTables
No `virtual` functions. 
Why? Dynamic dispatch requires a vtable lookup, which is an indirect jump. This often bypasses the CPU's branch predictor, leading to pipeline stalls.
**The Fix:** We use flat enumerations, template monomorphization, and X-Macros to handle polymorphism at compile-time.

### 3. Zero Mutexes
No `std::mutex`, no `std::lock_guard`. 
Why? Context switching and thread suspension are the enemies of microsecond consistency. 
**The Fix:** Lock-free concurrency only. We use Seqlocks (ParameterSlots) for single-writer/multiple-reader state, and MPSC rings for event passing. If we need to wait, we use adaptive spin-waits with `_mm_pause()`.

### 4. Zero Branches on Hot Path
If it's in the `ExecutionCore_Tick` loop, it can't have an `if`. 
Why? Even a correctly predicted branch consumes execution ports. A mispredicted one is a catastrophe (~20-50 cycles). 
**The Fix:** Bitwise arithmetic and AVX-512 `cmov` instructions. We evaluate both "Leg A" and "Leg B" of a trade unconditionally and use mask blending to select the result.

### 5. Zero Floating Point (Mostly)
We avoid `double` and `float` on the hot path.
Why? IEEE-754 is non-deterministic across different compilers and hardware (rounding modes, FMA vs. separate mul/add). 
**The Fix:** We built a custom `FPN<F>` (Fixed-Point Number) library using `uint64_t` words. It’s bytewise-deterministic, ensuring that a backtest on a dev machine matches live execution exactly, down to the last bit.

**The Lesson:** High performance is often the result of removing abstractions, not adding them.

What’s the most "extreme" constraint you’ve ever worked under? 

#HFT #Cpp #LowLatency #Programming #SoftwareArchitecture #SystemsEngineering
