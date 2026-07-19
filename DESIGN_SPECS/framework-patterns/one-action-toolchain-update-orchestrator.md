---
type: framework-pattern
stage: 2-draft
version: 1.0
established: 2026-07-19
tags: [framework-pattern, dev-plane, ssot, structural-fix, doc-pipeline]
surface: [ci-tooling, doc-pipeline]
sister_specs: []
applies_at_skills: []
---

# One-action toolchain update orchestrator (write-side; gates stay verify-only)

**Established:** 2026-07-19 (decision-log **D-374**, E.1.2.B planning; operator: *"we also need a codified update skill... to ensure it all gets updated at once"*). **Stage: 2-DRAFT** — first canonical at E.1.2.B `0.2`.

## Problem

The system's thesis is *one core, N consumers*. But the UPDATE operation was never codified: a single change (a new vocab row, a reconverted file, a new producer) must propagate to several surfaces — the in-comment `[DERIVED]` facts, the doc/code indexes, the grammar, the parity gate — and a **remembered N-step ritual is exactly what drifts.** Observed drift (2026-07-19 survey): the plugin's own `DOCS/` drifted from its own code (`[DATA_SIZE]`/`[DEP_CHAIN]` in the doc vs `[SIZE]`/`[UPSTREAM]` in the code); `ExecutionCore`'s `[ORIGIN]`/`[UPDATED]` provenance was never backfilled.

## The pattern

**ONE explicitly-invoked skill regenerates all WRITTEN derived state + indexes from ground truth, in dependency order, idempotently, verify-after:**

1. **Dependency order** (each stage consumes the prior's output): vocab → grammar → `check_cache_layout --fix` (struct layout DERIVED) → the call-graph writer (`[UPSTREAM]`/`[CONSUMERS]`) → `rebuild_doc_indexes` → `parity_check`.
2. **WRITTEN-only** (per the schema's WRITTEN-vs-LIVE-PREVIEW split, D-327): regenerate the *stable* derived facts (layout / call-graph); NEVER write the volatile ones (instr-count/`[SIMD]`/`[BRANCHES]` — they flip with `-O`/`-march`; the plugin shows those LIVE).
3. **Idempotent** (D-369 stamp-on-change / the Class-56 non-idempotent-writer guard): a no-op refresh does NOT restamp `[UPDATED]`; a second run is a 0-diff. This is the currency-check contract ("run the producer, expect 0-diff").
4. **Verify-after**: end by running the read-only verify sweep (`check_session_docs.sh`) to prove the write produced a consistent state.

## The load-bearing guardrail — WRITE vs VERIFY separation

The orchestrator **WRITES**; the CI **GATES stay VERIFY-ONLY** (red on drift). The gates never call the writer, and a commit-hook NEVER silently rewrites files under the operator — the same "CI flags, a human acts, never auto" rule the schema uses for `[OUTDATED_INFO]` and the `[DERIVED]` regenerate-only discipline. The update skill is the **write-side SISTER** of the verify sweep (`check_session_docs.sh`), and a **dependency** of the gates (they verify its output is clean) — so it lands early in a build sequence.

## Why not (rejected)

- **Each tool updated independently, remembered sequence** — the drift itself (the problem).
- **A commit-hook that auto-rewrites** — silent file mutations under the operator; violates flag-not-auto; a mis-generated fact would land in a commit unreviewed.

## Cross-references

- Decision log: **D-374** (this pattern) · D-369 (provenance/idempotency) · D-327 (WRITTEN-vs-LIVE-PREVIEW) · D-337/D-349 (one-core / migration).
- Sister (prose): `check_session_docs.sh` (the VERIFY-side sister) · `in-code-documentation-schema.md` § "DERIVED — WRITTEN vs LIVE-PREVIEW" · `doc-intelligence-toolchain-architecture.md`.
- Applied at: E.1.2.B `0.2`.

**End — Stage 2 DRAFT.** Reciprocal `sister_specs` links + index enrollment land at first-canonical (E.1.2.B `0.2`).
