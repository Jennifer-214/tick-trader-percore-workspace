# LinkedIn Post: Why Your Lock-Free Ring is Still Slow

**Hook:** You implemented a Single-Producer Single-Consumer (SPSC) ring. It's lock-free. It's wait-free. So why are you seeing 200ns spikes in your inter-thread latency?

The culprit is likely **False Sharing**, and it's more subtle than you think.

Most devs know to keep the `head` and `tail` pointers on different cache lines using `alignas(64)`. This prevents the Producer (writing to `head`) from invalidating the Consumer's cache line (writing to `tail`).

**The "Embedded" Gotcha:**
But what happens when you embed that ring as a field inside a larger "Hot" struct? 

```cpp
struct OrderManagerState {
    uint64_t total_orders; // Producer writes this
    alignas(64) SPSCRing result_queue; // Ring's head is here
};
```

Even if `head` is aligned *inside* the ring, the compiler might place it right next to `total_orders`. Now, every time the Producer updates the order count, it invalidates the cache line containing the ring's `head`. If the Consumer is on another core trying to read that `head`, it stalls.

**The Solution: Cluster Discipline**
In our engine, we use explicit **Cluster Isolation**:

1. **Explicit Alignment:** We don't just align the ring; we wrap the preceding fields in their own `alignas(64)` clusters.
2. **Static Assertions:** We use `static_assert(offsetof(OMS, queue) % 64 == 0)` to ensure that no future field addition silently breaks the cache-line boundary.
3. **Information Density:** We cluster fields by "Thread Ownership." If Thread A writes it and Thread B reads it, it gets its own dedicated line. No exceptions.

**The Lesson:** In high-performance systems, the layout of your data in memory is just as important as the logic of your code. If you don't control your cache lines, the hardware will control your tail latency.

#HFT #Cpp #LowLatency #SoftwareArchitecture #SystemsProgramming #Performance
