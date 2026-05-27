# DESIGN_SPECS catalog

**Auto-generated** by `tools/rebuild_doc_indexes.py`. Regenerate after adding/moving specs.

Total: 94 specs across 11 types.

Per-type catalog grouped by lifecycle stage. Cross-ref:
- `doc-frontmatter-convention.md` (frontmatter schema)
- `doc-tag-vocabulary.md` (tag canonical list)
- CLAUDE.md § How to find anything (grep recipes)

## refactor-pattern (21 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/refactor-patterns/bitmap-overflow-protection-discipline.md` | 5-claude-md | framework-discipline, data-oriented-design, structural-fix | 2 |
| `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md` | 5-claude-md | branchless-discipline, latency-discipline, structural-fix | 2 |
| `DESIGN_SPECS/refactor-patterns/branchless-math-kernel-pattern.md` | 3-first-canonical | branchless-discipline, latency-discipline, fixed-point-math | 3 |
| `DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md` | 3-first-canonical | framework-discipline, structural-fix, pattern-codification | 3 |
| `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` | 2-draft | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/refactor-patterns/cfg-section-parser-state-machine.md` | 2-draft | framework-discipline, structural-fix | 2 |
| `DESIGN_SPECS/refactor-patterns/cross-walker-struct-field-uniqueness-discipline.md` | 2-draft | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` | 5-claude-md | structural-fix, framework-discipline, latency-discipline | 2 |
| `DESIGN_SPECS/refactor-patterns/failure-attribution-buffer-pattern.md` | 2-draft | failure-observability, structural-fix, framework-discipline | 2 |
| `DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md` | 3-first-canonical | cross-tool-decoupling, structural-fix, framework-discipline, +1 | 3 |
| `DESIGN_SPECS/refactor-patterns/generic-ring-buffer-template-pattern.md` | 3-first-canonical | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/refactor-patterns/latency-vs-cache-decision-framework.md` | 5-claude-md | latency-discipline, data-oriented-design | 4 |
| `DESIGN_SPECS/refactor-patterns/loop-fusion-pattern.md` | 3-first-canonical | latency-discipline, data-oriented-design | 3 |
| `DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md` | 5-claude-md | data-oriented-design, branchless-discipline, structural-fix | 4 |
| `DESIGN_SPECS/refactor-patterns/orchestration-helper-with-pod-args-pattern.md` | 3-first-canonical | framework-discipline, structural-fix | 2 |
| `DESIGN_SPECS/refactor-patterns/post-parse-normalize-with-explicit-key-bitmap-pattern.md` | 3-first-canonical | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/refactor-patterns/registry-bitmap-set-discipline.md` | 3-first-canonical | structural-fix, framework-discipline, data-oriented-design | 4 |
| `DESIGN_SPECS/refactor-patterns/sliding-window-online-statistics-pattern.md` | 3-first-canonical | fixed-point-math, latency-discipline | 2 |
| `DESIGN_SPECS/refactor-patterns/slow-path-cfg-resolution-cache-pattern.md` | 3-first-canonical | latency-discipline, data-oriented-design, structural-fix | 3 |
| `DESIGN_SPECS/refactor-patterns/template-deferred-dependency-injection.md` | 3-first-canonical | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/refactor-patterns/transient-aggregation-bitmap-pattern.md` | 3-first-canonical | data-oriented-design, branchless-discipline | 4 |

## framework-pattern (35 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/framework-patterns/autopopulate-from-arity-macro-family.md` | 3-first-canonical | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md` | 3-first-canonical | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md` | 5-claude-md | framework-discipline, data-oriented-design, branchless-discipline, +1 | 4 |
| `DESIGN_SPECS/framework-patterns/calibration-log-column-registry.md` | 3-first-canonical | framework-discipline, wire-format, structural-fix | 4 |
| `DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md` | 3-first-canonical | framework-discipline, structural-fix, pattern-codification | 3 |
| `DESIGN_SPECS/framework-patterns/cfg-derived-consumer-framework.md` | 3-first-canonical | framework-discipline, structural-fix, pattern-codification | 4 |
| `DESIGN_SPECS/framework-patterns/cfg-field-categorization-discipline.md` | 3-first-canonical | framework-discipline, structural-fix, pattern-codification | 4 |
| `DESIGN_SPECS/framework-patterns/composed-filter-mask-pattern.md` | 3-first-canonical | framework-discipline, branchless-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/curve-registry-pattern.md` | 3-first-canonical | framework-discipline, branchless-discipline | 3 |
| `DESIGN_SPECS/framework-patterns/display-execution-invariant-registry-pattern.md` | 3-first-canonical | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/dual-axis-y3-dispatch-pattern.md` | 3-first-canonical | framework-discipline, branchless-discipline | 3 |
| `DESIGN_SPECS/framework-patterns/enum-mode-flags-bitmap-lookup-pattern.md` | 3-first-canonical | framework-discipline, data-oriented-design, branchless-discipline | 3 |
| `DESIGN_SPECS/framework-patterns/framework-composition-overview.md` | 3-first-canonical | framework-discipline, pattern-codification, doc-discipline | 5 |
| `DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md` | 3-first-canonical | framework-discipline, pattern-codification | 3 |
| `DESIGN_SPECS/framework-patterns/manual-fields-inventory-pattern.md` | 3-first-canonical | framework-discipline, structural-fix, pattern-codification | 4 |
| `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md` | 5-claude-md | framework-discipline, structural-fix, meta-discipline, +1 | 4 |
| `DESIGN_SPECS/framework-patterns/metadata-bit-driven-derived-filter-framework.md` | 4-cohort | framework-discipline, structural-fix, pattern-codification | 6 |
| `DESIGN_SPECS/framework-patterns/multi-action-registry-walker-family.md` | 2-draft | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/multi-state-dispatch-with-per-state-update-metadata.md` | 3-first-canonical | framework-discipline, branchless-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/per-bit-per-core-override-pattern.md` | 3-first-canonical | framework-discipline, branchless-discipline, data-oriented-design | 3 |
| `DESIGN_SPECS/framework-patterns/per-instance-registry-pattern.md` | 2-draft | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/persisted-struct-with-ephemeral-field-coexistence-pattern.md` | 3-first-canonical | framework-discipline, structural-fix, wire-format | 3 |
| `DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md` | 3-first-canonical | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/registry-coverage-ci-check-pattern.md` | 3-first-canonical | framework-discipline, structural-fix, pattern-codification | 4 |
| `DESIGN_SPECS/framework-patterns/registry-tuple-as-single-source-of-truth.md` | 5-claude-md | framework-discipline, structural-fix, pattern-codification | 4 |
| `DESIGN_SPECS/framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md` | 5-claude-md | framework-discipline, structural-fix, pattern-codification | 6 |
| `DESIGN_SPECS/framework-patterns/sink-fn-pointer-for-optional-side-effect-pattern.md` | 3-first-canonical | framework-discipline, branchless-discipline | 2 |
| `DESIGN_SPECS/framework-patterns/slot-state-foreach-registry-with-storage-routing.md` | 3-first-canonical | framework-discipline, structural-fix, data-oriented-design | 3 |
| `DESIGN_SPECS/framework-patterns/slow-path-gate-registry-pattern.md` | 3-first-canonical | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/stamp-vs-runtime-drift-detection-registry.md` | 3-first-canonical | framework-discipline, wire-format, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/type-erased-per-core-resource-handle-pattern.md` | 3-first-canonical | framework-discipline, concurrency, structural-fix | 2 |
| `DESIGN_SPECS/framework-patterns/type-trait-dispatch-via-tt-namespace.md` | 5-claude-md | framework-discipline, structural-fix, branchless-discipline | 3 |
| `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md` | 5-claude-md | framework-discipline, structural-fix, pattern-codification | 8 |
| `DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md` | 3-first-canonical | framework-discipline, data-oriented-design, branchless-discipline, +1 | 5 |
| `DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md` | 5-claude-md | framework-discipline, structural-fix, branchless-discipline | 5 |

## feature-pattern (3 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/feature-patterns/per-horizon-barrier-blending-with-shadow-mode.md` | 2-draft | framework-discipline, structural-fix | 1 |
| `DESIGN_SPECS/feature-patterns/runtime-toggleable-bench-gate-pattern.md` | 3-first-canonical | latency-discipline, framework-discipline | 1 |
| `DESIGN_SPECS/feature-patterns/shadow-load-state-transition-pattern.md` | 3-first-canonical | framework-discipline, structural-fix, concurrency | 1 |

## audit-methodology (3 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/audit-methodologies/audit-driven-pre-coding-gate.md` | 3-first-canonical | audit-methodology, framework-discipline, meta-discipline | 2 |
| `DESIGN_SPECS/audit-methodologies/audit-report-format.md` | 2-draft | audit-methodology, doc-discipline, framework-discipline | 3 |
| `DESIGN_SPECS/audit-methodologies/audit-scope-taxonomy.md` | 3-first-canonical | audit-methodology, meta-discipline, framework-discipline | 2 |

## data-discipline (9 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/data-disciplines/aggressive-memory-reduction-techniques.md` | 3-first-canonical | data-oriented-design, structural-fix, framework-discipline | 6 |
| `DESIGN_SPECS/data-disciplines/cache-layout-discipline-for-hot-side-structs.md` | 3-first-canonical | data-oriented-design, latency-discipline, concurrency | 5 |
| `DESIGN_SPECS/data-disciplines/cache-line-discipline.md` | 2-draft | data-oriented-design, concurrency, latency-discipline | 3 |
| `DESIGN_SPECS/data-disciplines/decision-first-cluster-layout-pattern.md` | 3-first-canonical | data-oriented-design, latency-discipline | 4 |
| `DESIGN_SPECS/data-disciplines/function-struct-alignment-for-single-mov-access.md` | 3-first-canonical | data-oriented-design, latency-discipline | 4 |
| `DESIGN_SPECS/data-disciplines/hot-side-array-element-alignment-for-sparse-access.md` | 3-first-canonical | data-oriented-design, latency-discipline | 3 |
| `DESIGN_SPECS/data-disciplines/partner-core-bitmap-pattern.md` | 3-first-canonical | data-oriented-design, branchless-discipline | 3 |
| `DESIGN_SPECS/data-disciplines/per-snapshot-cluster-layout-pattern.md` | 3-first-canonical | data-oriented-design, concurrency, latency-discipline | 4 |
| `DESIGN_SPECS/data-disciplines/raii-destructor-with-cluster-reorg-interaction.md` | 3-first-canonical | data-oriented-design, concurrency | 3 |

## concurrency-pattern (4 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/concurrency-patterns/concurrency-model-summary.md` | 2-draft | concurrency, data-oriented-design | 2 |
| `DESIGN_SPECS/concurrency-patterns/cross-thread-snapshot-publish-cluster-isolation.md` | 3-first-canonical | concurrency, data-oriented-design, latency-discipline | 4 |
| `DESIGN_SPECS/concurrency-patterns/phase-separated-drainer-for-safe-cross-temporal-derives.md` | 3-first-canonical | concurrency, structural-fix, latency-discipline | 3 |
| `DESIGN_SPECS/concurrency-patterns/spsc-ring-embedded-in-hot-struct-cluster-discipline.md` | 3-first-canonical | concurrency, data-oriented-design, latency-discipline | 4 |

## wire-format-pattern (6 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md` | 3-first-canonical | wire-format, fixed-point-math, structural-fix | 2 |
| `DESIGN_SPECS/wire-format-patterns/pre-post-cfg-registry-split-for-emit-order-preservation.md` | 3-first-canonical | wire-format, framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/wire-format-patterns/prng-choice-for-replay-determinism.md` | 3-first-canonical | wire-format, fixed-point-math | 2 |
| `DESIGN_SPECS/wire-format-patterns/struct-padding-determinism-pattern.md` | 5-claude-md | wire-format, data-oriented-design, fixed-point-math | 3 |
| `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` | 5-claude-md | wire-format, framework-discipline, structural-fix, +1 | 6 |
| `DESIGN_SPECS/wire-format-patterns/wire-format-canonical-body-invariants-helper.md` | 3-first-canonical | wire-format, framework-discipline, structural-fix | 3 |

## doc-discipline (2 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md` | 2-draft | doc-discipline, framework-discipline, structural-fix, +1 | 5 |
| `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md` | 2-draft | doc-discipline, structural-fix, pattern-codification | 3 |

## meta-discipline (6 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md` | 3-first-canonical | meta-discipline, framework-discipline, pattern-codification, +1 | 3 |
| `DESIGN_SPECS/meta-disciplines/doc-frontmatter-convention.md` | 2-draft | doc-discipline, meta-discipline, framework-discipline | 3 |
| `DESIGN_SPECS/meta-disciplines/doc-tag-vocabulary.md` | 2-draft | doc-discipline, meta-discipline, framework-discipline | 3 |
| `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` | 3-first-canonical | meta-discipline, audit-methodology, framework-discipline | 3 |
| `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md` | 5-claude-md | meta-discipline, pattern-codification, doc-discipline, +1 | 5 |
| `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md` | 5-claude-md | meta-discipline, structural-fix, pattern-codification, +1 | 4 |

## plan-template (4 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/plan-templates/design-spec-template.md` | 2-draft | plan-template, doc-discipline, framework-discipline | 3 |
| `DESIGN_SPECS/plan-templates/future-oriented-plan-template.md` | 3-first-canonical | plan-template, doc-discipline, pattern-codification | 5 |
| `DESIGN_SPECS/plan-templates/postmortem-template.md` | 2-draft | plan-template, doc-discipline | 3 |
| `DESIGN_SPECS/plan-templates/sprint-master-plan-template.md` | 2-draft | plan-template, doc-discipline, framework-discipline | 3 |

## ledger-template (1 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/ledger-templates/ledger-entry-templates.md` | 2-draft | ledger-discipline, plan-template, doc-discipline | 2 |
