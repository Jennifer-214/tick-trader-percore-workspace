---
name: patch-planner
description: Analyzes items from the GEMINI_FINDINGS backlog and generates comprehensive, HFT-compliant patching blueprints. Details root causes, traces dependencies, evaluates latency/ML-parity impact, and proposes strict DOD/branchless C++ fixes. Does NOT edit code directly.
type: skill
concern: workflow
audit_cadence: ad-hoc
tags: [audit-methodology, data-oriented-design, branchless-discipline, fixed-point-math]
surface: [hot-path, slow-path, oms-drainer, ml-inference]
sister_skills: [/finding-analyzer, /trace-deps, /dod-audit, /hft-audit, /parity-check]
loads_dynamically: [DESIGN_SPECS/meta-disciplines/skill-knowledge-consultation-and-auto-routing.md]
skill_kind: judgment
associated_anti_patterns: [DOCS/RECURRING_BUG_PATTERNS.md, DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md]
associated_decisions: [plans/<active-sprint>/decision-logs/]
associated_postmortems: [plans/<active-sprint>/postmortems/]
associated_ledgers: [DOCS/TECH_DEBT.md, DOCS/PARITY_ISSUES.md]
trigger_heuristics: ["patching blueprint / fix-design for a backlog finding -> suggest /patch-planner"]
---

# /patch-planner — Deep Vulnerability Analysis & Fix Generation

> **Stage 0 — consult institutional knowledge** (per `skill-knowledge-consultation-and-auto-routing.md`): before judging, load this skill's `associated_*` slice (specs / anti-patterns / decisions / postmortems / ledgers) + run the canonical-sister check; if running as a cold Explore/Plan subagent, ensure CLAUDE.md/MEMORY are loaded first.

## What this does

Takes one or more findings from the codebase audit backlog and performs a rigorous, multi-dimensional analysis. It then produces a highly structured "Patching Blueprint" designed to guide an engineer (or Claude) in safely refactoring the code. 

**This skill enforces the project's strict architectural invariants:**
- Data-Oriented Design (DOD)
- Branchless Hot Paths
- Fixed-Point Math (`FPN_Binary`)
- Lock-Free Concurrency (Seqlocks, memory barriers)

**Does NOT modify source code.** Output is a markdown-formatted blueprint document.

## When to use

- Before executing any code changes for issues listed in audit backlog (e.g., `GEMINI_FINDINGS/MASTER_SORTED_BACKLOG.md`).
- When transitioning from the "Auditing" phase to the "Execution" phase.
- To thoroughly document the "why" and "how" of a complex concurrency or cache-alignment fix.

## Invocation

- `/patch-planner <finding_id>` — Analyzes a specific finding by ID from the master backlog.
- `/patch-planner <severity_tier>` — Generates blueprints for a batch of issues (e.g., `/patch-planner CRITICAL`).

## Execution Steps

The agent should spawn a subagent to trace and analyze the issue, outputting a blueprint with the following exact structure for EACH finding:

### 1. Root Cause & Description
- Explain exactly what the bug is and the mechanics of why it occurs.
- Be highly specific about the hardware or algorithmic level (e.g., "The L1 cache line is 64 bytes, but the struct is 68 bytes...").

### 2. Dependency Trace
- List the exact file paths and line contexts where the vulnerability exists.
- Map out the blast radius: What other modules or threads are impacted by this failure? (e.g., "Written by Producer thread in `BinanceAdapter.hpp`, read by Consumer in `OrderManager.hpp`").

### 3. Impact Assessment
- **Latency Impact:** How does this bug (or the lack of a fix) impact the sub-microsecond latency budget? (e.g., "False sharing causes 40ns L1 invalidation stalls").
- **Live vs. ML Parity:** Does this issue cause the live trading engine to diverge from the backtest/training environment? (e.g., "Truncating floats biases the live VWAP, breaking parity with Python training data").

### 4. Proposed Solution (HFT Compliant)
- Provide the exact C++ code snippet to fix the issue.
- **MANDATORY CONSTRAINTS:**
  - **No `if` statements on the hot path.** Use bitwise masks, `FPN_LessThanOrEqual`, or unconditional arithmetic.
  - **No `std::mutex`.** Use `std::atomic_thread_fence`, `memory_order_release/acquire`, or `_mm_pause()`.
  - **Struct Alignment.** Use `alignas(64)` and explicit padding `uint8_t _pad[X]` to mathematically enforce cache line boundaries.
  - **Zero Allocations.** No `new`, `std::vector`, etc.

## Format of the Output

```markdown
# Patch Blueprint: Issue #<ID> - <Title>

## 1. Root Cause Analysis
<Detailed explanation of the mechanical failure>

## 2. Dependency Trace
- **Location:** `File/Path.hpp:Line`
- **Blast Radius:** <Modules affected>

## 3. Impact Assessment
- **Latency:** <nanosecond cost or pipeline impact>
- **ML Parity:** <divergence risks>

## 4. Proposed DOD/Branchless Fix
<Explanation of the architectural shift>

```cpp
// Explicit C++ patch snippet enforcing invariants
```
```

## Anti-patterns (DO NOT DO THIS)
- Do **not** propose `std::mutex` or `std::lock_guard` for thread-safety.
- Do **not** propose `std::round` or `std::pow` (use fixed-point `FPN_Binary_` equivalents).
- Do **not** propose fixing a branch by adding `__builtin_expect` (fix it by removing the branch entirely with bitwise math).