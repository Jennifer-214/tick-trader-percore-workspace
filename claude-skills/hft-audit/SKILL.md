---
name: hft-audit
description: Systematically sweeps the codebase for deep architectural flaws, hardware-level bottlenecks, and HFT invariant violations. Focuses on cache alignment, branchless design, lock-free concurrency, and fixed-point math edge cases. Outputs new findings to the master backlog.
---

# /hft-audit — Deep Architectural & HFT Codebase Audit

> **Uniform parameter + preload contract:**
>
> **Optional invocation args:**
> - `<scope_path>` — file_path_glob to scope to subsystem; default = full sweep
> - `[focus_keywords...]` — narrow scan focus (e.g., "cache alignment" "branchless" "FPN edge case")
>
> **Stage 0 DESIGN_PHILOSOPHY preload** (workspace/DOCS/DESIGN_PHILOSOPHY.md):
> - § 3 (Hard Invariants) — H1-H13 are universal HFT principles
> - § 4 (Latency cost framework) — cycle/cache/branch costs anchor decisions
> - § 6 (Concurrency family) — lock-free, atomics, cache-line discipline, no mutexes
>
> Cite specific § N rows in finding descriptions.

## What this does

This skill directs the agent to perform an exhaustive, multi-dimensional audit of the codebase, focusing on extreme low-level system interactions that typical linters cannot catch. It specifically looks for violations of High-Frequency Trading (HFT) invariants, such as L1 cache spills, false sharing, branch mispredictions, undefined behavior, and lock-free concurrency tears.

Unlike a simple bug sweep, this audit focuses on **algorithmic complexity**, **hardware-level memory layout**, and **train-serve parity**.

## When to use

- During architectural reviews or prior to merging major system rewrites.
- When unexplained latency spikes or non-deterministic state divergences occur.
- To continuously populate the `MASTER_SORTED_BACKLOG.md` with new findings.

## Scope (per audit-scope-taxonomy.md)

This skill accepts scope as first positional arg (or `--scope=<shape>` named):

- `current` (default when no scope specified) — uncommitted edits + recent commits + symbols/types directly touched by current edits. Fast feedback during active work. LOW context cost.
- `wide` — full codebase sweep. Quarterly health audits + post-codification sweeps. HIGH context cost (may need follow-up `module:`-scoped re-audits per priority area).
- `scoped <glob>` — file/dir glob. Targeted scan (e.g., `/hft-audit scoped CoreFrameworks/OrderManager*`).
- `module:<name>` — named module per `MODULE_MAP.md` registry (e.g., `OMS`, `engine`, `ML-pipeline`, `accounting`, `wire-format`). Iterative deep analysis with bounded context per pass.
- `chain:<symbol>` — N/A for /hft-audit (use `/dependency-chain-trace` for symbol flow traces).

**Most appropriate scope shapes for /hft-audit:** `current` (during active work), `module:<name>` (iterative deep audits), `wide` (quarterly + post-new-anti-pattern-codification sweeps).

When scope is `current` or `module:<name>`, skill spawns ONE subagent loading only the in-scope files. When scope is `wide`, skill spawns subagent(s) per logical scan dir (CoreFrameworks/ + ML_Headers/ + Strategies/ + Backtest/ + DataStream/ + MemHeaders/) to avoid context overflow.

## Invocation

- `/hft-audit` — default scope `current`; audit uncommitted edits + recent commits for HFT-invariant violations.
- `/hft-audit <scope>` — explicit scope per taxonomy (`current` / `wide` / `scoped <glob>` / `module:<name>`).
- `/hft-audit <scope> [focus_keywords...]` — narrow scan focus (e.g., `module:OMS branchless cache-layout`).

**Examples:**
- `/hft-audit current` — fast feedback during active coding
- `/hft-audit wide` — quarterly full sweep
- `/hft-audit module:OMS` — deep audit of OMS module
- `/hft-audit module:OMS branchless` — focused branchless dispatch audit of OMS
- `/hft-audit scoped CoreFrameworks/EngineSharded.hpp` — single-file scan

## Execution Steps

The agent should spawn a `codebase_investigator` subagent. The subagent must execute the following steps:

### 1. Context Loading & Exclusion
- First, the agent MUST read `~/code/tick-trader-percore-workspace/GEMINI_FINDINGS/MASTER_SORTED_BACKLOG.md`.
- Extract all previously discovered issues.
- **Rule:** The new audit MUST explicitly exclude all known issues to prevent duplicate reporting.
- Per scope arg: load ONLY the in-scope files into context (per audit-scope-taxonomy.md decision matrix).

### 2. The Deep Sweep (Search Vectors)
Run heuristic investigations across the following specific HFT attack vectors:
- **Data-Oriented Design (DOD):** Look for unaligned structs (not padded to 64 bytes), L1 cache straddling, and False Sharing across heavily contended `std::atomic` variables.
- **Branchless dispatch opportunity scan:** Look for if/else if chains + switch statements on runtime enum values in SP/HP/drainer code that should be converted to fn pointer table (Pattern 1) or 2D state×type dispatch table (Pattern 2) per `DESIGN_SPECS/branchless-dispatch-discipline.md`. Flag candidates as Class 28 (per `DOCS/RECURRING_BUG_PATTERNS.md`). Detection patterns:
   - `if (X == ENUM_VAL) { ... } else if (X == OTHER_ENUM) { ... }` chains dispatching on runtime enum
   - `switch (X) { case ENUM_VAL: ...; case OTHER_ENUM: ... }` in CoreFrameworks/ / ML_Headers/ / Strategies/ / Backtest/ SP/HP paths
   - `cond ? value_a : value_b` ternaries that BOTH SIDES load from memory (causes both loads to be issued; if both target the SAME cache line, no extra cost; if DIFFERENT lines, branchless pre-resolution is the win — see `decision-time-data-binding-pattern.md`)
   - Acceptable branches: boot-time-only, `__builtin_expect`-tagged rare, `if constexpr` compile-time, genuine binary predicate (e.g., null-ptr check) without alternative computation
- **Branchless Hot Path (existing):** Look for data-dependent `if` statements, ternary operators, or missing compiler elisions (like `[[unlikely]]` applied incorrectly to spin-loops).
- **Concurrency & Lock-Free:** Search for SPSC/MPSC ring hazards, missing memory ordering fences (`std::atomic_thread_fence`), ABA problems, and sequence lock (seqlock) tearing.
- **Math & Precision:** Look for scalar math where AVX-512 could be used, floating-point truncation biases, missing `NaN` validation, and integer overflow in rolling statistics.
- **System & Network:** Look for missing OS resource limits (`mlockall`), `SO_KEEPALIVE`, unchecked cryptography returns, and blocking I/O (`fprintf`, `fflush`, `system`) on hot threads.

### 3. Classification
Classify each newly discovered issue into one of four severity tiers:
- **CRITICAL:** Data corruption, deadlocks, stack overflows, or undefined behavior (UB).
- **HIGH:** Severe latency spikes (e.g., false sharing, blocking I/O), architectural state drift, or ML logic corruption (e.g., NaN propagation).
- **MEDIUM:** Cache straddling, minor algorithmic edge cases, missing guards.
- **LOW:** Micro-optimizations, cosmetic rendering limits.

### 4. Emit the Findings
Generate a structured markdown report appending the new issues to the backlog. 

Format:

```markdown
# Phase <X>: <Theme>

## NEW Ultra-Obscure Issues (<Start ID>-<End ID>)

1. **<Vulnerability Title>** (`File/Path.hpp`)
   - **Severity:** <CRITICAL | HIGH | MEDIUM | LOW>
   - **Details:** <Deep mechanical explanation of why it fails at the hardware or algorithmic level. Be highly specific.>
```

## Anti-patterns to flag (DO NOT DO THIS)
- Do **not** report standard static analysis warnings (e.g., "missing const qualifier") unless it directly impacts the compiler's ability to vectorize or elide branches.
- Do **not** report issues that are already solved in the `MASTER_SORTED_BACKLOG.md`.
- Do **not** suggest fixing concurrency with `std::mutex`; always identify it as a hazard needing a lock-free solution.