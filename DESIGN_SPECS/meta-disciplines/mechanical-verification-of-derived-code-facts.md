---
type: meta-discipline
tags: [doc-discipline, data-oriented-design, audit-methodology, verification, structural-enforcement]
surface: [hot-path, slow-path, cache, wire-format, ml-inference, boot-time]
stage: 3-first-canonical
established: 2026-06-16
sister_specs:
  - meta-disciplines/structural-enforcement-when-memory-insufficient.md
  - data-disciplines/cache-line-discipline.md
  - audit-methodologies/static-latency-path-conformance-analysis.md
  - meta-disciplines/calibration-corpus-non-vacuity-discipline.md
  - framework-patterns/doc-intelligence-toolchain-architecture.md
sister_docs:
  - DOCS/RECURRING_BUG_PATTERNS.md  # Class 51 (vacuously-green guard) + its inverse (false-RED)
applications:
  - 'rolling_baseline "~1.5MB" vs actual 64KB — per-core/per-engine SCOPE x 24B/16B SIZE confusion (~23x)'
  - 'RollingStats.hpp:187 "O(W)" vs actual amortized-O(1) since v5.11.2.C'
  - 'LatencyHistogram "~640B" vs actual 576B'
  - 'ParameterSlot "~1KB memcpy ~20-30ns" for GateParameters<64> vs actual 192B/~4ns'
  - 'check_struct_size_budget.py false-RED of ExecutionCore (the guard reproducing the disease — the inverse)'
  - 'the LATENCY arm reshaped runtime-bench -> static instruction-budget conformance analyzer (D-233; check_latency_path_conformance.py) — a derived latency-fact reclassified from a runtime measurement to a STATIC proxy'
  - 'stale "// CMOV verified in bench" vs the actual `je` (16B Money has no x86 128-bit cmov; comment written pre-Ship-B) — a CODEGEN derived-fact comment trusted by a subagent over the disassembly; armed into SUBAGENT_ARMING §2.5 (2026-06-30)'
  - 'check_cache_layout.py --fix refreshed 0 [DERIVED] for leaf ML structs — the EMITTER is bounded by its probe TU (main.cpp); empty != wrong, it is coverage (D-363; E.1.2.A)'
---

# Mechanical verification of derived code-facts (no hand-computed fact without a guard)

## The pattern (and its teeth)

A **derived code-fact** — a quantity computed FROM the code's structure (struct **size**, **cache-residency**, algorithmic **complexity**, **latency**) — written as a HAND-COMMENT **drifts**, because nothing forces it to agree with the code. Worse, hand-math carries **invisible assumptions** (scope: per-core vs per-engine; version: pre-flip vs post-flip; host: this-CPU vs that) that are never reconciled — so the comments become not merely stale but mutually **contradictory**, and the contradiction is the tell.

**Canonical failure:** `rolling_baseline` was commented `~1.5MB`; the struct is 64KB (`sizeof` = 65,984) — a ~23× error. Reconstructed: `1.5MB` = `rolling_baseline × 16 cores at the OLD 24B FPN` (~1.44MB) — a **per-engine total written on a per-core field declaration**. The sibling comments mixed scope AND size (`W=512` "24KB" = per-core-16B; `W=256` "393KB" = per-engine-×16-24B), proving they were hand-written at different times by different reasoning, never reconciled. `sizeof` has no "scope" assumption: it is **one unambiguous number**.

## The fix-signature: MEASURE / ASSERT — never hand-comment

| Derived fact | Verify mechanically with | Tier |
|---|---|---|
| struct **SIZE** | `static_assert(sizeof(T)==N)` + `check_struct_size_budget.py` | compile-time (strongest) |
| **CACHE**-residency | static budget (`sizeof` vs host-derived L1d/L2) **+** dynamic perf-counter (`L1-dcache-load-misses`) | static flags, **dynamic decides** |
| **COMPLEXITY** (`O(...)`) | the static analyzer's instruction-count + loop-structure (the constant-iter / loop shape is visible in ASM) **+** a benchmark for input-scaling; a stale-comment lint | **static proxy** + runtime confirm |
| **LATENCY** | the **static conformance analyzer** (`check_latency_path_conformance.py` — instruction-budget + branch-class from ASM, deterministic + gating); never hand-comment "~100-300µs" | **static (CI/pre-commit)** + dynamic PMU confirm (deferred) |
| **CODEGEN** (cmov-vs-branch · "branchless" · vectorized · inlined) | the analyzer's branch-classification + `objdump` disassembly. A comment **asserting** codegen (`// CMOV-style`, `// branchless`) is a derived-fact RESTATEMENT — verify the ASM, never the comment; SURFACE+fix a stale one | **static (ASM)** |

Priority gradient (the engine's general law): **compile-time `static_assert` > CI tool > convention.** If a number is kept in a comment at all, it **references the assert** (the SSoT), it does not restate it.

**Reclassify runtime→static when a sound static proxy exists (D-233).** A fact assumed to need a RUNTIME measurement can sometimes be lifted to a STATIC proxy that is *stronger* for CI: LATENCY was reshaped from a wall-clock-ns bench (non-deterministic, non-CI-able, box-dependent) into a **static instruction-budget + branch-classification from ASM** — deterministic, diffable, gating, zero engine behavior (`static-latency-path-conformance-analysis.md`). Prefer the static proxy when it is sound; keep the dynamic measurement as the *deferred confirm* (the PMU arm), not the gate. The "runtime" tier is the floor, not the destination.

## The INVERSE failure — don't over-correct into a false-RED

A guard can *reproduce* the disease: `check_struct_size_budget.py`'s whole-struct-vs-L1d check **false-RED'd `ExecutionCore`** (66.8KB) — a *cache-disciplined* struct (hot cluster in cache line 0; the 64KB is an embedded `event_ring` **write-drain FIFO** with no residency requirement; cold fields deliberately tail-placed). A guard that cries wolf on correct code is the **inverse of the vacuously-green guard** (Class 51). **Fix:** a *static* guard FLAGS for review; the residency VERDICT is *dynamic*. Tier a struct by what it should **honestly** fit, and route the un-static-decidable part (hot-working-set ≤ L1d) to **measurement**, not a `sizeof` verdict.

## Coverage-boundedness of the EMITTER — empty != wrong (D-363)

The verify-side of this discipline (a guard that CHECKS a fact) has a producer twin: the **emitter** that WRITES the fact (`check_cache_layout.py --fix` materializing `[SIZE]`/`[ALIGN]` into a `[STRUCT]` block from `-fdump-record-layouts`). An emitter's coverage is **bounded by its probe TU**: a struct's fact is written ONLY if that struct is laid out in the probe translation unit. `--fix --tu main.cpp` refreshed **0** for a leaf struct (`RollingTurnover`, `TradingCosts`) that main.cpp never materializes, and for a template (`WelfordTracker<F>`) never instantiated at a concrete `F` (the `[INSTANTIATION]` axis, D-318). This is **coverage, not drift** — an empty `[DERIVED]` is *honestly absent*, not *wrongly stated* (unlike the ~1.5MB hand-comment, which asserts a false number). The gate MUST distinguish them: an ABSENT-because-uncovered fact is **advisory** (extend the emitter — the C4-advisory of `in-code-documentation-schema.md`), a PRESENT-but-drifted fact is a **hard fail**. Full emitter coverage = a dedicated all-headers probe TU (`#include` every header + instantiate templates at their real `F`), gated for its corpus-wide blast radius (a newly-surfaced cross-thread straddle is a genuine H6 finding, NOT auto-suppressed). See D-327 (WRITTEN-vs-LIVE-PREVIEW) + D-363.

## Why a guard, not memory (M7)

Convention proved insufficient at ~15-20 hand-commented sites. Per `structural-enforcement-when-memory-insufficient.md` (M7): escalate to a compile-time assert / CI tool. The **sweep cleans the backlog; the tool is the permanent net** (it catches the NEXT one). A grep-based sweep is bounded by its patterns and can never be provably exhaustive — only the standing guard closes the recurrence.

## Sister guards (canonical — extend, do not duplicate)

`check_struct_size_budget.py` (this discipline's first guard — non-serialized struct size + cache budget) · `check_struct_alignment.py` (c) (byte-serialized-type size-pins) · `check_fpn_doc_size_currency.py` (doc FPN sizes) · the **static latency-path conformance analyzer** (`check_latency_path_conformance.py` — the LATENCY arm, instruction-budget + branch-class from ASM; `static-latency-path-conformance-analysis.md`), its deferred `perf`/PMU step being the *dynamic* confirm.

## Mn registry

Candidate meta-discipline (DESIGN_PHILOSOPHY § 11.5). The size/cache arm has its guard (`check_struct_size_budget.py`); the latency/complexity arm's guard IS the static conformance analyzer (`check_latency_path_conformance.py`; D-233 reshaped it runtime-bench → static-instruction-budget). Promote to a numbered Mn at the codification batch close.
