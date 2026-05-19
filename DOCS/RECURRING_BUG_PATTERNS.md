---
type: ledger-template
splits_into: [DOCS/recurring-bug-patterns/class-01-strategy-lifecycle-orphans.md, DOCS/recurring-bug-patterns/class-02-display-execution-divergence.md, DOCS/recurring-bug-patterns/class-03-drain-count-under-partials.md, DOCS/recurring-bug-patterns/class-04-snapshot-save-load-asymmetry.md, DOCS/recurring-bug-patterns/class-05-reset-paper-completeness.md, DOCS/recurring-bug-patterns/class-06-oms-counter-persistence.md, DOCS/recurring-bug-patterns/class-07-threading-topology-violations.md, DOCS/recurring-bug-patterns/class-08-user-configurable-features-silently-inactive.md, DOCS/recurring-bug-patterns/class-09-shutdown-blocking-on-unwanted-operations.md, DOCS/recurring-bug-patterns/class-10-strategy-regime-mismatch.md, DOCS/recurring-bug-patterns/class-11-extensibility-friction-silent-drift.md, DOCS/recurring-bug-patterns/class-12-wired-but-unexercised-ml-paths.md, DOCS/recurring-bug-patterns/class-13-worker-thread-snap-capture-drift.md, DOCS/recurring-bug-patterns/class-14-plan-calls-non-existent-function.md, DOCS/recurring-bug-patterns/class-15-function-signature-drift.md, DOCS/recurring-bug-patterns/class-16-naming-convention-drift-x-macro.md, DOCS/recurring-bug-patterns/class-17-architectural-deferral-without-adjacent-struct-grep.md, DOCS/recurring-bug-patterns/class-18-mirror-plans-missing-data-flow.md, DOCS/recurring-bug-patterns/class-19-hardcoded-instance-names-applicability-gating.md, DOCS/recurring-bug-patterns/class-20-bitmap-field-without-overflow-guard.md, DOCS/recurring-bug-patterns/class-21-multiple-parallel-descriptors.md, DOCS/recurring-bug-patterns/class-22-runtime-cfg-gating-scattered.md, DOCS/recurring-bug-patterns/class-23-type-erased-typed-field-write.md, DOCS/recurring-bug-patterns/class-24-capability-cfg-surface-mismatch.md, DOCS/recurring-bug-patterns/class-25-scope-erosion-per-core-consumer.md, DOCS/recurring-bug-patterns/class-27-single-value-cache-flattens-per-instance.md, DOCS/recurring-bug-patterns/class-28-branchy-sp-hp-dispatch.md, DOCS/recurring-bug-patterns/class-29-silent-zero-fee-rate-order-binding.md, DOCS/recurring-bug-patterns/class-30-sibling-array-without-registry-enrollment.md]
total_entries_at_split: 30
split_date: 2026-05-18
split_criteria: per-class
---

# RECURRING_BUG_PATTERNS (INDEX)

The complement to `tests/INVARIANTS_MAP.md`. That doc tracks
**positive** invariants ("X must hold true"); this doc tracks
**negative** patterns ("this class of bug keeps showing up — here's
the detection signature, here's where it bites").

Each pattern has:
- **Class N** identifier — stable, referenced from postmortems
- **Symptom** — what the user sees
- **Root cause** — why it happens
- **Detection** — exact grep / script to find new instances
- **Known instances** — file:line of past occurrences + commit that fixed
- **Prevention** — what to add to readiness/dust skills or to tests

When a new instance is found, add it under "Known instances" with
the fix commit. When a new class emerges (>2 fixes of the same
shape), add a new Class entry (file).

Read this doc before any architectural sprint, especially anything
that mentions "split", "shard", "decouple", "extract", "centralize",
or "per-core". Run each Class's detection script as a pre-coding
gate.

This file was split 2026-05-18 because size exceeded ledger hard threshold (2198 lines per `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md`).

Content is now in per-class sub-files; this doc serves as INDEX.

## Sub-files

| Class | Title | Surface | Severity | File |
|---|---|---|---|---|
| 1 | Strategy lifecycle orphans | live (slow-path strategy dispatch) | HIGH | `DOCS/recurring-bug-patterns/class-01-strategy-lifecycle-orphans.md` |
| 2 | Display ↔ execution divergence | gui + live | HIGH | `DOCS/recurring-bug-patterns/class-02-display-execution-divergence.md` |
| 3 | Drain count under partials | drainer | HIGH | `DOCS/recurring-bug-patterns/class-03-drain-count-under-partials.md` |
| 4 | Snapshot save/load asymmetry | boot | MEDIUM | `DOCS/recurring-bug-patterns/class-04-snapshot-save-load-asymmetry.md` |
| 5 | Reset Paper completeness | boot | MEDIUM | `DOCS/recurring-bug-patterns/class-05-reset-paper-completeness.md` |
| 6 | OMS counter persistence | boot | MEDIUM | `DOCS/recurring-bug-patterns/class-06-oms-counter-persistence.md` |
| 7 | Threading topology violations (audited clean post-v5.4.x) | audited-clean | N/A | `DOCS/recurring-bug-patterns/class-07-threading-topology-violations.md` |
| 8 | User-configurable features silently inactive in sharded | live (cfg → runtime consumption) | HIGH | `DOCS/recurring-bug-patterns/class-08-user-configurable-features-silently-inactive.md` |
| 9 | Shutdown blocking on operations the user didn't want | boot (shutdown ordering) | MEDIUM | `DOCS/recurring-bug-patterns/class-09-shutdown-blocking-on-unwanted-operations.md` |
| 10 | Strategy-regime mismatch | live (regime → strategy coupling) | HIGH | `DOCS/recurring-bug-patterns/class-10-strategy-regime-mismatch.md` |
| 11 | Extensibility friction causing silent drift | live (multi-site addition pattern) | HIGH | `DOCS/recurring-bug-patterns/class-11-extensibility-friction-silent-drift.md` |
| 12 | Wired-but-unexercised ML paths (v5.9 sprint) | ml | HIGH | `DOCS/recurring-bug-patterns/class-12-wired-but-unexercised-ml-paths.md` |
| 13 | Worker-thread struct extended without updating snap-capture-before-free block | training / GUI worker threads | HIGH | `DOCS/recurring-bug-patterns/class-13-worker-thread-snap-capture-drift.md` |
| 14 | Plan calls a function or struct field that doesn't exist | plan-time | HIGH | `DOCS/recurring-bug-patterns/class-14-plan-calls-non-existent-function.md` |
| 15 | Function signature drift between plan and canonical typedef | plan-time | HIGH | `DOCS/recurring-bug-patterns/class-15-function-signature-drift.md` |
| 16 | Naming convention drift breaks X-macro dispatcher | plan-time | MEDIUM | `DOCS/recurring-bug-patterns/class-16-naming-convention-drift-x-macro.md` |
| 17 | Architectural deferral made without grepping adjacent struct fields | plan-time | MEDIUM | `DOCS/recurring-bug-patterns/class-17-architectural-deferral-without-adjacent-struct-grep.md` |
| 18 | "Mirror" plans missing data-flow dependencies (incl. STRENGTHENED call-sequence enumeration) | plan-time | HIGH | `DOCS/recurring-bug-patterns/class-18-mirror-plans-missing-data-flow.md` |
| 19 | Hardcoded instance names in applicability gating | live + slow-path + GUI | HIGH | `DOCS/recurring-bug-patterns/class-19-hardcoded-instance-names-applicability-gating.md` |
| 20 | Bitmap field without overflow guard (silent-truncation) | registry + bitmap pairs codebase-wide | HIGH | `DOCS/recurring-bug-patterns/class-20-bitmap-field-without-overflow-guard.md` |
| 21 | Multiple parallel descriptors for similar surfaces (cross-file drift) | cfg + descriptor surfaces | HIGH | `DOCS/recurring-bug-patterns/class-21-multiple-parallel-descriptors.md` |
| 22 | Runtime cfg gating scattered in code paths (instead of registry) | cfg gating consumers | MEDIUM | `DOCS/recurring-bug-patterns/class-22-runtime-cfg-gating-scattered.md` |
| 23 | Type-erased typed-field write via reinterpret_cast through char* offset | registry-driven typed-field access | HIGH | `DOCS/recurring-bug-patterns/class-23-type-erased-typed-field-write.md` |
| 24 | Capability-cfg surface mismatch (ML pipeline supports it; operator can't see / configure / verify it) | ml ↔ cfg surface | HIGH | `DOCS/recurring-bug-patterns/class-24-capability-cfg-surface-mismatch.md` |
| 25 | Scope-erosion in per-core consumer function (registry says per-core; consumer reads from wrong scope) | per-core consumer execution | HIGH | `DOCS/recurring-bug-patterns/class-25-scope-erosion-per-core-consumer.md` |
| 27 | Single-value cache flattens per-instance distinction (subsystem state mirrors cfg as a scalar) | subsystem state caches | HIGH | `DOCS/recurring-bug-patterns/class-27-single-value-cache-flattens-per-instance.md` |
| 28 | Branchy SP/HP dispatch when branchless feasible (variance injection in determinism-prioritizing path) | SP/HP/drainer/producer dispatch | HIGH | `DOCS/recurring-bug-patterns/class-28-branchy-sp-hp-dispatch.md` |
| 29 | Silent zero-fee-rate from Order missing pre-resolution binding | Order construction sites | HIGH | `DOCS/recurring-bug-patterns/class-29-silent-zero-fee-rate-order-binding.md` |
| 30 | Sibling array on subsystem state created without registry enrollment | subsystem-state struct ↔ canonical registry | LATENT | `DOCS/recurring-bug-patterns/class-30-sibling-array-without-registry-enrollment.md` |

Note on numbering: Class 26 is referenced in Class 27's body as a sister concept (global consumer reading per-core field) but does not have its own canonical entry yet. Classes 31 and 32 are cited from CLAUDE.local.md sprint state but have not yet been codified into their own files; they should be added as sub-files (e.g., `class-31-<name>.md`, `class-32-<name>.md`) and listed in the table above when codified.

## Cross-reference shape

External cross-refs use canonical ID format `Class N`. Preserved across sub-files; `rg "\bClass 18\b"` finds the canonical class file automatically. The ID is the stable contract — file path is incidental.

## Migration history

- 2026-05-18: Split from monolithic RECURRING_BUG_PATTERNS.md (30 codified classes / 2198 lines)
- Per `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md` discipline (Stage 3 first canonical application)
