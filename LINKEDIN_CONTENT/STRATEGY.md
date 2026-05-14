# LinkedIn Content Strategy: HFT & Systems Engineering

This file outlines a 20-post content strategy based on the `tick-trader-percore-workspace`. Each idea is designed to stop the scroll with high-signal technical hooks.

## The Strategy: 4 Pillars
1.  **The "Extreme Invariants" Series:** High-level architectural bans (Rules of the road).
2.  **The "Pattern Library" Series:** Deep dives into specific C++/SIMD/Cache optimizations.
3.  **The "War Stories" Series:** Recurring bug patterns and how we extinguished entire classes of errors.
4.  **The "Philosophy of Latency" Series:** How to think about determinism, audits, and performance-first design.

---

## Content Roadmap (20 Ideas)

### Pillar 1: Extreme Invariants (The "Rules")
| # | Topic | Hook | Source |
| :--- | :--- | :--- | :--- |
| 1 | **The Bans that Buy Microseconds** | Performance isn't about what you add; it's what you ban. (malloc, virtual, mutex). | `DOCS/GEMINI.md` |
| 2 | **Zero-Allocation Boot** | If you're calling `new` during a trade, you've already lost. How to pre-allocate everything. | `BuddyAllocator.hpp` |
| 3 | **Branchless Hot Path** | Why an `if` statement is a catastrophe for tail latency. Replacing control flow with bitwise math. | `ExecutionCore.hpp` |
| 4 | **The "No Sleep" Policy** | Why `std::this_thread::sleep_for` is a bug in HFT. Adaptive spin-waits and `_mm_pause()`. | `LATENCY_AUDIT.md` |
| 5 | **Fixed-Point Determinism** | Why `double` is a landmine for cross-platform backtesting. Building a bit-identical `FPN<F>` library. | `FixedPointN.hpp` |

### Pillar 2: Pattern Library (The "How-To")
| # | Topic | Hook | Source |
| :--- | :--- | :--- | :--- |
| 6 | **AVX-512 Byte-Determinism** | SIMD is usually for speed. We use it for bit-for-bit replayability. The 8 rules of SIMD determinism. | `DESIGN_SPECS/avx512...` |
| 7 | **Cache Layout Discipline** | Moving from SoA to AoS and back again. Using `alignas(64)` to kill False Sharing. | `DESIGN_SPECS/cache-layout...` |
| 8 | **X-Macro Registries** | The ultimate single-source-of-truth. Generating C++, JSON, and GUI code from one macro. | `DESIGN_SPECS/x-macro...` |
| 9 | **Branchless Math Kernels** | Solving Cholesky decompositions without a single `if` guard. | `DESIGN_SPECS/branchless-math...` |
| 10 | **Lock-Free Seqlocks** | How to pass state between threads with zero mutexes and zero stalls using `ParameterSlot`. | `ParameterSlot.hpp` |
| 11 | **SIMD String Search** | Replacing `strstr` with AVX-512 to parse market data at 10GB/s. | `binance_parse_trade` |
| 12 | **Wait-Free Ring Buffers** | Building an SPSC ring that lives *inside* a hot struct for L1 locality. | `spsc-ring...` |

### Pillar 3: War Stories (The "Anti-Patterns")
| # | Topic | Hook | Source |
| :--- | :--- | :--- | :--- |
| 13 | **Strategy Lifecycle Orphans** | The bug where you wire the entry gate but forget the exit. How we use call-graph diffs to find them. | `RECURRING_BUGS.md` (Class 1) |
| 14 | **The "Mostly Fresh" Reset** | Why "Reset Paper" buttons are notoriously hard to implement. The danger of hand-curated state clearing. | `RECURRING_BUGS.md` (Class 5) |
| 15 | **The Silent NaN Poisoning** | How one NaN in a feature pack can kill an entire ML pipeline without a single error log. | `RECURRING_BUGS.md` (Class 12) |
| 16 | **Mirror Drift** | When your backtest says "Profit" and your live engine says "Flat" because of 1-ULP drift. | `RECURRING_BUGS.md` (Class 11) |

### Pillar 4: Philosophy of Latency (The "Mindset")
| # | Topic | Hook | Source |
| :--- | :--- | :--- | :--- |
| 17 | **The Audit-Driven Gate** | Why we don't "test" code; we "audit" it. Moving from reactive fixes to proactive verification. | `DESIGN_SPECS/audit-driven...` |
| 18 | **Determinism > Performance** | A fast engine that can't be replayed is just a random number generator. Why determinism is the #1 feature. | `CLAUDE_INVARIANTS.md` |
| 19 | **Structural Fixes vs. Patches** | When to stop patching the leak and when to redesign the pipe. The decision framework for tech debt. | `DESIGN_SPECS/structural-fix...` |
| 20 | **The "Wired but Unexercised" Gap** | The most dangerous code in your repo is the code that compiles but never runs. | `RECURRING_BUGS.md` (Class 12) |

---

## Drafting Workflow
1.  Pick a # from the roadmap.
2.  Open the referenced Source file.
3.  Draft in `LINKEDIN_CONTENT/posts/YYYY-MM-DD-topic.md`.
4.  Update `POST_TRACKER.md` status.
