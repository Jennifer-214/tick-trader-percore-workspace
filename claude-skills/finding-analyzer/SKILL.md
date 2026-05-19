---
name: finding-analyzer
description: Orchestrates a deep-dive vulnerability analysis by systematically chaining existing workspace skills (/trace-deps, /latency-track, /parity-check). Produces an exhaustive, multi-dimensional report covering the why, what, where, blast radius, and impact for any codebase finding.
---

# /finding-analyzer — Deep Vulnerability Analysis Orchestrator

## What this does

This skill acts as an **Analysis Orchestrator**. Instead of relying purely on the LLM's intuition to explain a finding, it forces the agent to methodically chain together your existing specialized workspace skills. By piping the finding through `/trace-deps`, `/latency-track`, and `/parity-check`, it generates a mathematically rigorous and structurally verified vulnerability report.

## When to use

- When you pull an item off the audit backlog (e.g., `GEMINI_FINDINGS/MASTER_SORTED_BACKLOG.md`) and need to fully understand its implications before writing code.
- To mathematically prove the latency impact of a bug.
- To automatically map out every file you will need to touch to fix the issue.

## Invocation

- `/finding-analyzer <finding_id>` — Analyzes a specific finding from the audit backlog (e.g., `GEMINI_FINDINGS/MASTER_SORTED_BACKLOG.md`).
- `/finding-analyzer "<description>"` — Analyzes a newly discovered ad-hoc bug or vulnerability.

## Execution Steps

The agent MUST spawn subagents or execute the following workspace skills in sequence before writing the final report:

### Step 1: Blast Radius Mapping (via `/trace-deps`)
- Identify the core function or struct where the finding lives.
- **Action:** Invoke the `/trace-deps` skill on the target symbol.
- **Goal:** Map out exactly *where* this lives and *what* downstream modules call it (e.g., does a bug in `FixedPointN.hpp` propagate all the way up to `OrderManager.hpp`?).

### Step 2: Latency Impact Assessment (via `/latency-track`)
- **Action:** Invoke the `/latency-track` skill on the affected hot-path functions.
- **Goal:** Determine the actual nanosecond or cycle-count impact of the bug. Does it cause L1 cache evictions? Does it force a branch misprediction penalty (~15-20 cycles)? 

### Step 3: Parity & ML Divergence (via `/parity-check`)
- **Action:** Invoke the `/parity-check` skill (or `/ml-audit` if ML-specific).
- **Goal:** Determine if this bug causes the C++ execution core to behave differently than the Python training environment (e.g., float truncation biasing the VWAP live, but not in backtest).

### Step 4: Synthesis & Report Generation
Combine the outputs of the previous skills into a comprehensive markdown report.

**Output Format:**

```markdown
# Vulnerability Analysis: <Finding Name>

## 1. The "What" & "Why" (Root Cause)
- **Mechanics:** <Detailed explanation of the failure at the hardware, arithmetic, or concurrency level>

## 2. The "Where" & "Trace" (Blast Radius)
- **Origin:** `<File/Path.hpp:Line>`
- **Dependency Trace:** 
  - <Output sourced from /trace-deps>
  - <Files required to be modified for a fix>

## 3. Impact Assessment
- **Latency Impact:** <Output sourced from /latency-track (e.g., 40ns cache penalty)>
- **Train/Serve Parity:** <Output sourced from /parity-check (e.g., drift causes ML pipeline to fail)>
- **Capital Risk:** <Assessment of whether this can lose money directly>

## 4. Architectural Fix Strategy
- **DOD/Branchless Strategy:** <High-level overview of how to patch it adhering to the invariants list>
```

## Anti-patterns
- Do **not** generate the final report without first executing the prerequisite skills (`/trace-deps`, `/latency-track`, etc.).
- Do **not** guess the dependencies; prove them with the trace.
