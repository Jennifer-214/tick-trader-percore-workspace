# Tag → files index (auto-generated snapshot)

**Auto-generated** by `tools/rebuild_doc_indexes.py`. Canonical reverse-lookup is `rg`:

```bash
rg -l "^tags:.*\bframework-discipline\b" DESIGN_SPECS/
rg -l "^surface:.*\bhot-path\b"
```

This file is a snapshot for static browsing.

## CONCERN tags

### audit-methodology (21 files)

- `DESIGN_SPECS/audit-methodologies/audit-driven-pre-coding-gate.md`
- `DESIGN_SPECS/audit-methodologies/audit-report-format.md`
- `DESIGN_SPECS/audit-methodologies/audit-scope-taxonomy.md`
- `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md`
- `claude-skills/anti-spaghetti/SKILL.md`
- `claude-skills/blindspot-scan/SKILL.md`
- `claude-skills/bug-check/SKILL.md`
- `claude-skills/dead-code-trace/SKILL.md`
- `claude-skills/dependency-chain-trace/SKILL.md`
- `claude-skills/dust/SKILL.md`
- `claude-skills/finding-analyzer/SKILL.md`
- `claude-skills/metadata-audit/SKILL.md`
- `claude-skills/parity-check/SKILL.md`
- `claude-skills/patch-planner/SKILL.md`
- `claude-skills/plan-check/SKILL.md`
- `claude-skills/plan-context-sweep/SKILL.md`
- `claude-skills/post-ship-audit/SKILL.md`
- `claude-skills/precoding-audit-gate/SKILL.md`
- `claude-skills/readiness/SKILL.md`
- `claude-skills/test-strength-audit/SKILL.md`
- `claude-skills/trace-deps/SKILL.md`

### branchless-discipline (20 files)

- `DESIGN_SPECS/data-disciplines/partner-core-bitmap-pattern.md`
- `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md`
- `DESIGN_SPECS/framework-patterns/composed-filter-mask-pattern.md`
- `DESIGN_SPECS/framework-patterns/curve-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/dual-axis-y3-dispatch-pattern.md`
- `DESIGN_SPECS/framework-patterns/enum-mode-flags-bitmap-lookup-pattern.md`
- `DESIGN_SPECS/framework-patterns/multi-state-dispatch-with-per-state-update-metadata.md`
- `DESIGN_SPECS/framework-patterns/per-bit-per-core-override-pattern.md`
- `DESIGN_SPECS/framework-patterns/sink-fn-pointer-for-optional-side-effect-pattern.md`
- `DESIGN_SPECS/framework-patterns/type-trait-dispatch-via-tt-namespace.md`
- `DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md`
- `DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md`
- `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md`
- `DESIGN_SPECS/refactor-patterns/branchless-math-kernel-pattern.md`
- `DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md`
- `DESIGN_SPECS/refactor-patterns/transient-aggregation-bitmap-pattern.md`
- `claude-skills/dod-audit/SKILL.md`
- `claude-skills/hft-audit/SKILL.md`
- `claude-skills/patch-planner/SKILL.md`
- `claude-skills/post-ship-audit/SKILL.md`

### concurrency (12 files)

- `DESIGN_SPECS/concurrency-patterns/concurrency-model-summary.md`
- `DESIGN_SPECS/concurrency-patterns/cross-thread-snapshot-publish-cluster-isolation.md`
- `DESIGN_SPECS/concurrency-patterns/phase-separated-drainer-for-safe-cross-temporal-derives.md`
- `DESIGN_SPECS/concurrency-patterns/spsc-ring-embedded-in-hot-struct-cluster-discipline.md`
- `DESIGN_SPECS/data-disciplines/cache-layout-discipline-for-hot-side-structs.md`
- `DESIGN_SPECS/data-disciplines/cache-line-discipline.md`
- `DESIGN_SPECS/data-disciplines/per-snapshot-cluster-layout-pattern.md`
- `DESIGN_SPECS/data-disciplines/raii-destructor-with-cluster-reorg-interaction.md`
- `DESIGN_SPECS/feature-patterns/shadow-load-state-transition-pattern.md`
- `DESIGN_SPECS/framework-patterns/type-erased-per-core-resource-handle-pattern.md`
- `claude-skills/dependency-chain-trace/SKILL.md`
- `claude-skills/hft-audit/SKILL.md`

### cross-tool-decoupling (2 files)

- `DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md`
- `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md`

### data-oriented-design (28 files)

- `DESIGN_SPECS/concurrency-patterns/concurrency-model-summary.md`
- `DESIGN_SPECS/concurrency-patterns/cross-thread-snapshot-publish-cluster-isolation.md`
- `DESIGN_SPECS/concurrency-patterns/spsc-ring-embedded-in-hot-struct-cluster-discipline.md`
- `DESIGN_SPECS/data-disciplines/aggressive-memory-reduction-techniques.md`
- `DESIGN_SPECS/data-disciplines/cache-layout-discipline-for-hot-side-structs.md`
- `DESIGN_SPECS/data-disciplines/cache-line-discipline.md`
- `DESIGN_SPECS/data-disciplines/decision-first-cluster-layout-pattern.md`
- `DESIGN_SPECS/data-disciplines/function-struct-alignment-for-single-mov-access.md`
- `DESIGN_SPECS/data-disciplines/hot-side-array-element-alignment-for-sparse-access.md`
- `DESIGN_SPECS/data-disciplines/partner-core-bitmap-pattern.md`
- `DESIGN_SPECS/data-disciplines/per-snapshot-cluster-layout-pattern.md`
- `DESIGN_SPECS/data-disciplines/raii-destructor-with-cluster-reorg-interaction.md`
- `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md`
- `DESIGN_SPECS/framework-patterns/enum-mode-flags-bitmap-lookup-pattern.md`
- `DESIGN_SPECS/framework-patterns/per-bit-per-core-override-pattern.md`
- `DESIGN_SPECS/framework-patterns/slot-state-foreach-registry-with-storage-routing.md`
- `DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md`
- `DESIGN_SPECS/refactor-patterns/bitmap-overflow-protection-discipline.md`
- `DESIGN_SPECS/refactor-patterns/latency-vs-cache-decision-framework.md`
- `DESIGN_SPECS/refactor-patterns/loop-fusion-pattern.md`
- `DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md`
- `DESIGN_SPECS/refactor-patterns/registry-bitmap-set-discipline.md`
- `DESIGN_SPECS/refactor-patterns/slow-path-cfg-resolution-cache-pattern.md`
- `DESIGN_SPECS/refactor-patterns/transient-aggregation-bitmap-pattern.md`
- `DESIGN_SPECS/wire-format-patterns/struct-padding-determinism-pattern.md`
- `claude-skills/dod-audit/SKILL.md`
- `claude-skills/hft-audit/SKILL.md`
- `claude-skills/patch-planner/SKILL.md`

### doc-discipline (24 files)

- `DESIGN_SPECS/audit-methodologies/audit-report-format.md`
- `DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md`
- `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md`
- `DESIGN_SPECS/framework-patterns/framework-composition-overview.md`
- `DESIGN_SPECS/ledger-templates/ledger-entry-templates.md`
- `DESIGN_SPECS/meta-disciplines/doc-frontmatter-convention.md`
- `DESIGN_SPECS/meta-disciplines/doc-tag-vocabulary.md`
- `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md`
- `DESIGN_SPECS/plan-templates/design-spec-template.md`
- `DESIGN_SPECS/plan-templates/future-oriented-plan-template.md`
- `DESIGN_SPECS/plan-templates/postmortem-template.md`
- `DESIGN_SPECS/plan-templates/sprint-master-plan-template.md`
- `claude-skills/doc-create/SKILL.md`
- `claude-skills/find/SKILL.md`
- `claude-skills/foxlib-promotion/SKILL.md`
- `claude-skills/handoff/SKILL.md`
- `claude-skills/index-rebuild/SKILL.md`
- `claude-skills/metadata-audit/SKILL.md`
- `claude-skills/plan-check/SKILL.md`
- `claude-skills/plan-draft/SKILL.md`
- `claude-skills/readiness/SKILL.md`
- `claude-skills/ship/SKILL.md`
- `claude-skills/sync-models/SKILL.md`
- `claude-skills/sync-workspace/SKILL.md`

### failure-observability (4 files)

- `DESIGN_SPECS/refactor-patterns/failure-attribution-buffer-pattern.md`
- `claude-skills/accounting-audit/SKILL.md`
- `claude-skills/ml-audit/SKILL.md`
- `claude-skills/test-strength-audit/SKILL.md`

### fixed-point-math (7 files)

- `DESIGN_SPECS/refactor-patterns/branchless-math-kernel-pattern.md`
- `DESIGN_SPECS/refactor-patterns/sliding-window-online-statistics-pattern.md`
- `DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md`
- `DESIGN_SPECS/wire-format-patterns/prng-choice-for-replay-determinism.md`
- `DESIGN_SPECS/wire-format-patterns/struct-padding-determinism-pattern.md`
- `claude-skills/accounting-audit/SKILL.md`
- `claude-skills/patch-planner/SKILL.md`

### framework-discipline (81 files)

- `DESIGN_SPECS/audit-methodologies/audit-driven-pre-coding-gate.md`
- `DESIGN_SPECS/audit-methodologies/audit-report-format.md`
- `DESIGN_SPECS/audit-methodologies/audit-scope-taxonomy.md`
- `DESIGN_SPECS/data-disciplines/aggressive-memory-reduction-techniques.md`
- `DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md`
- `DESIGN_SPECS/feature-patterns/per-horizon-barrier-blending-with-shadow-mode.md`
- `DESIGN_SPECS/feature-patterns/runtime-toggleable-bench-gate-pattern.md`
- `DESIGN_SPECS/feature-patterns/shadow-load-state-transition-pattern.md`
- `DESIGN_SPECS/framework-patterns/autopopulate-from-arity-macro-family.md`
- `DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md`
- `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md`
- `DESIGN_SPECS/framework-patterns/calibration-log-column-registry.md`
- `DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md`
- `DESIGN_SPECS/framework-patterns/cfg-derived-consumer-framework.md`
- `DESIGN_SPECS/framework-patterns/composed-filter-mask-pattern.md`
- `DESIGN_SPECS/framework-patterns/curve-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/display-execution-invariant-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/dual-axis-y3-dispatch-pattern.md`
- `DESIGN_SPECS/framework-patterns/enum-mode-flags-bitmap-lookup-pattern.md`
- `DESIGN_SPECS/framework-patterns/framework-composition-overview.md`
- `DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/manual-fields-inventory-pattern.md`
- `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md`
- `DESIGN_SPECS/framework-patterns/metadata-bit-driven-derived-filter-framework.md`
- `DESIGN_SPECS/framework-patterns/multi-action-registry-walker-family.md`
- `DESIGN_SPECS/framework-patterns/multi-state-dispatch-with-per-state-update-metadata.md`
- `DESIGN_SPECS/framework-patterns/per-bit-per-core-override-pattern.md`
- `DESIGN_SPECS/framework-patterns/per-instance-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/persisted-struct-with-ephemeral-field-coexistence-pattern.md`
- `DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/registry-coverage-ci-check-pattern.md`
- `DESIGN_SPECS/framework-patterns/registry-tuple-as-single-source-of-truth.md`
- `DESIGN_SPECS/framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md`
- `DESIGN_SPECS/framework-patterns/sink-fn-pointer-for-optional-side-effect-pattern.md`
- `DESIGN_SPECS/framework-patterns/slot-state-foreach-registry-with-storage-routing.md`
- `DESIGN_SPECS/framework-patterns/slow-path-gate-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/stamp-vs-runtime-drift-detection-registry.md`
- `DESIGN_SPECS/framework-patterns/type-erased-per-core-resource-handle-pattern.md`
- `DESIGN_SPECS/framework-patterns/type-trait-dispatch-via-tt-namespace.md`
- `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md`
- `DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md`
- `DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md`
- `DESIGN_SPECS/meta-disciplines/doc-frontmatter-convention.md`
- `DESIGN_SPECS/meta-disciplines/doc-tag-vocabulary.md`
- `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md`
- `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md`
- `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md`
- `DESIGN_SPECS/plan-templates/design-spec-template.md`
- `DESIGN_SPECS/plan-templates/sprint-master-plan-template.md`
- `DESIGN_SPECS/refactor-patterns/bitmap-overflow-protection-discipline.md`
- `DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md`
- `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md`
- `DESIGN_SPECS/refactor-patterns/cfg-section-parser-state-machine.md`
- `DESIGN_SPECS/refactor-patterns/cross-walker-struct-field-uniqueness-discipline.md`
- `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md`
- `DESIGN_SPECS/refactor-patterns/failure-attribution-buffer-pattern.md`
- `DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md`
- `DESIGN_SPECS/refactor-patterns/generic-ring-buffer-template-pattern.md`
- `DESIGN_SPECS/refactor-patterns/orchestration-helper-with-pod-args-pattern.md`
- `DESIGN_SPECS/refactor-patterns/post-parse-normalize-with-explicit-key-bitmap-pattern.md`
- `DESIGN_SPECS/refactor-patterns/registry-bitmap-set-discipline.md`
- `DESIGN_SPECS/refactor-patterns/template-deferred-dependency-injection.md`
- `DESIGN_SPECS/wire-format-patterns/pre-post-cfg-registry-split-for-emit-order-preservation.md`
- `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md`
- `DESIGN_SPECS/wire-format-patterns/wire-format-canonical-body-invariants-helper.md`
- `claude-skills/anti-spaghetti/SKILL.md`
- `claude-skills/blindspot-scan/SKILL.md`
- `claude-skills/bug-check/SKILL.md`
- `claude-skills/dod-audit/SKILL.md`
- `claude-skills/index-rebuild/SKILL.md`
- `claude-skills/merge-scan/SKILL.md`
- `claude-skills/metadata-audit/SKILL.md`
- `claude-skills/ml-audit/SKILL.md`
- `claude-skills/parity-check/SKILL.md`
- `claude-skills/plan-draft/SKILL.md`
- `claude-skills/precoding-audit-gate/SKILL.md`
- `claude-skills/readiness/SKILL.md`
- `claude-skills/registry-fit-audit/SKILL.md`
- `claude-skills/strategy-template/SKILL.md`
- `claude-skills/trace-deps/SKILL.md`

### latency-discipline (21 files)

- `DESIGN_SPECS/concurrency-patterns/cross-thread-snapshot-publish-cluster-isolation.md`
- `DESIGN_SPECS/concurrency-patterns/phase-separated-drainer-for-safe-cross-temporal-derives.md`
- `DESIGN_SPECS/concurrency-patterns/spsc-ring-embedded-in-hot-struct-cluster-discipline.md`
- `DESIGN_SPECS/data-disciplines/cache-layout-discipline-for-hot-side-structs.md`
- `DESIGN_SPECS/data-disciplines/cache-line-discipline.md`
- `DESIGN_SPECS/data-disciplines/decision-first-cluster-layout-pattern.md`
- `DESIGN_SPECS/data-disciplines/function-struct-alignment-for-single-mov-access.md`
- `DESIGN_SPECS/data-disciplines/hot-side-array-element-alignment-for-sparse-access.md`
- `DESIGN_SPECS/data-disciplines/per-snapshot-cluster-layout-pattern.md`
- `DESIGN_SPECS/feature-patterns/runtime-toggleable-bench-gate-pattern.md`
- `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md`
- `DESIGN_SPECS/refactor-patterns/branchless-math-kernel-pattern.md`
- `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md`
- `DESIGN_SPECS/refactor-patterns/latency-vs-cache-decision-framework.md`
- `DESIGN_SPECS/refactor-patterns/loop-fusion-pattern.md`
- `DESIGN_SPECS/refactor-patterns/sliding-window-online-statistics-pattern.md`
- `DESIGN_SPECS/refactor-patterns/slow-path-cfg-resolution-cache-pattern.md`
- `claude-skills/finding-analyzer/SKILL.md`
- `claude-skills/hft-audit/SKILL.md`
- `claude-skills/latency-track/SKILL.md`
- `claude-skills/merge-scan/SKILL.md`

### ledger-discipline (3 files)

- `DESIGN_SPECS/ledger-templates/ledger-entry-templates.md`
- `claude-skills/latency-track/SKILL.md`
- `claude-skills/ship/SKILL.md`

### meta-discipline (11 files)

- `DESIGN_SPECS/audit-methodologies/audit-driven-pre-coding-gate.md`
- `DESIGN_SPECS/audit-methodologies/audit-scope-taxonomy.md`
- `DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md`
- `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md`
- `DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md`
- `DESIGN_SPECS/meta-disciplines/doc-frontmatter-convention.md`
- `DESIGN_SPECS/meta-disciplines/doc-tag-vocabulary.md`
- `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md`
- `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md`
- `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md`
- `claude-skills/blindspot-scan/SKILL.md`

### operator-collaboration (6 files)

- `DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md`
- `claude-skills/handoff/SKILL.md`
- `claude-skills/precoding-audit-gate/SKILL.md`
- `claude-skills/ship/SKILL.md`
- `claude-skills/sync-models/SKILL.md`
- `claude-skills/sync-workspace/SKILL.md`

### pattern-codification (22 files)

- `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md`
- `DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md`
- `DESIGN_SPECS/framework-patterns/cfg-derived-consumer-framework.md`
- `DESIGN_SPECS/framework-patterns/framework-composition-overview.md`
- `DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/manual-fields-inventory-pattern.md`
- `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md`
- `DESIGN_SPECS/framework-patterns/metadata-bit-driven-derived-filter-framework.md`
- `DESIGN_SPECS/framework-patterns/registry-coverage-ci-check-pattern.md`
- `DESIGN_SPECS/framework-patterns/registry-tuple-as-single-source-of-truth.md`
- `DESIGN_SPECS/framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md`
- `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md`
- `DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md`
- `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md`
- `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md`
- `DESIGN_SPECS/plan-templates/future-oriented-plan-template.md`
- `DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md`
- `claude-skills/anti-spaghetti/SKILL.md`
- `claude-skills/dod-audit/SKILL.md`
- `claude-skills/plan-draft/SKILL.md`
- `claude-skills/post-ship-audit/SKILL.md`
- `claude-skills/registry-fit-audit/SKILL.md`

### plan-template (11 files)

- `DESIGN_SPECS/ledger-templates/ledger-entry-templates.md`
- `DESIGN_SPECS/plan-templates/design-spec-template.md`
- `DESIGN_SPECS/plan-templates/future-oriented-plan-template.md`
- `DESIGN_SPECS/plan-templates/postmortem-template.md`
- `DESIGN_SPECS/plan-templates/sprint-master-plan-template.md`
- `claude-skills/doc-create/SKILL.md`
- `claude-skills/handoff/SKILL.md`
- `claude-skills/plan-check/SKILL.md`
- `claude-skills/plan-context-sweep/SKILL.md`
- `claude-skills/plan-draft/SKILL.md`
- `claude-skills/readiness/SKILL.md`

### structural-fix (68 files)

- `DESIGN_SPECS/concurrency-patterns/phase-separated-drainer-for-safe-cross-temporal-derives.md`
- `DESIGN_SPECS/data-disciplines/aggressive-memory-reduction-techniques.md`
- `DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md`
- `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md`
- `DESIGN_SPECS/feature-patterns/per-horizon-barrier-blending-with-shadow-mode.md`
- `DESIGN_SPECS/feature-patterns/shadow-load-state-transition-pattern.md`
- `DESIGN_SPECS/framework-patterns/autopopulate-from-arity-macro-family.md`
- `DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md`
- `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md`
- `DESIGN_SPECS/framework-patterns/calibration-log-column-registry.md`
- `DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md`
- `DESIGN_SPECS/framework-patterns/cfg-derived-consumer-framework.md`
- `DESIGN_SPECS/framework-patterns/composed-filter-mask-pattern.md`
- `DESIGN_SPECS/framework-patterns/display-execution-invariant-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/manual-fields-inventory-pattern.md`
- `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md`
- `DESIGN_SPECS/framework-patterns/metadata-bit-driven-derived-filter-framework.md`
- `DESIGN_SPECS/framework-patterns/multi-action-registry-walker-family.md`
- `DESIGN_SPECS/framework-patterns/multi-state-dispatch-with-per-state-update-metadata.md`
- `DESIGN_SPECS/framework-patterns/per-instance-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/persisted-struct-with-ephemeral-field-coexistence-pattern.md`
- `DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/registry-coverage-ci-check-pattern.md`
- `DESIGN_SPECS/framework-patterns/registry-tuple-as-single-source-of-truth.md`
- `DESIGN_SPECS/framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md`
- `DESIGN_SPECS/framework-patterns/slot-state-foreach-registry-with-storage-routing.md`
- `DESIGN_SPECS/framework-patterns/slow-path-gate-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/stamp-vs-runtime-drift-detection-registry.md`
- `DESIGN_SPECS/framework-patterns/type-erased-per-core-resource-handle-pattern.md`
- `DESIGN_SPECS/framework-patterns/type-trait-dispatch-via-tt-namespace.md`
- `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md`
- `DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md`
- `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md`
- `DESIGN_SPECS/refactor-patterns/bitmap-overflow-protection-discipline.md`
- `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md`
- `DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md`
- `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md`
- `DESIGN_SPECS/refactor-patterns/cfg-section-parser-state-machine.md`
- `DESIGN_SPECS/refactor-patterns/cross-walker-struct-field-uniqueness-discipline.md`
- `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md`
- `DESIGN_SPECS/refactor-patterns/failure-attribution-buffer-pattern.md`
- `DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md`
- `DESIGN_SPECS/refactor-patterns/generic-ring-buffer-template-pattern.md`
- `DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md`
- `DESIGN_SPECS/refactor-patterns/orchestration-helper-with-pod-args-pattern.md`
- `DESIGN_SPECS/refactor-patterns/post-parse-normalize-with-explicit-key-bitmap-pattern.md`
- `DESIGN_SPECS/refactor-patterns/registry-bitmap-set-discipline.md`
- `DESIGN_SPECS/refactor-patterns/slow-path-cfg-resolution-cache-pattern.md`
- `DESIGN_SPECS/refactor-patterns/template-deferred-dependency-injection.md`
- `DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md`
- `DESIGN_SPECS/wire-format-patterns/pre-post-cfg-registry-split-for-emit-order-preservation.md`
- `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md`
- `DESIGN_SPECS/wire-format-patterns/wire-format-canonical-body-invariants-helper.md`
- `claude-skills/accounting-audit/SKILL.md`
- `claude-skills/anti-spaghetti/SKILL.md`
- `claude-skills/bug-check/SKILL.md`
- `claude-skills/dead-code-trace/SKILL.md`
- `claude-skills/dependency-chain-trace/SKILL.md`
- `claude-skills/dod-audit/SKILL.md`
- `claude-skills/dust/SKILL.md`
- `claude-skills/foxlib-promotion/SKILL.md`
- `claude-skills/merge-scan/SKILL.md`
- `claude-skills/plan-context-sweep/SKILL.md`
- `claude-skills/post-ship-audit/SKILL.md`
- `claude-skills/registry-fit-audit/SKILL.md`
- `claude-skills/strategy-template/SKILL.md`
- `claude-skills/trace-deps/SKILL.md`

### wire-format (12 files)

- `DESIGN_SPECS/framework-patterns/calibration-log-column-registry.md`
- `DESIGN_SPECS/framework-patterns/persisted-struct-with-ephemeral-field-coexistence-pattern.md`
- `DESIGN_SPECS/framework-patterns/stamp-vs-runtime-drift-detection-registry.md`
- `DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md`
- `DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md`
- `DESIGN_SPECS/wire-format-patterns/pre-post-cfg-registry-split-for-emit-order-preservation.md`
- `DESIGN_SPECS/wire-format-patterns/prng-choice-for-replay-determinism.md`
- `DESIGN_SPECS/wire-format-patterns/struct-padding-determinism-pattern.md`
- `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md`
- `DESIGN_SPECS/wire-format-patterns/wire-format-canonical-body-invariants-helper.md`
- `claude-skills/ml-audit/SKILL.md`
- `claude-skills/parity-check/SKILL.md`

## SURFACE tags

### backtest (2 files)

- `DESIGN_SPECS/wire-format-patterns/prng-choice-for-replay-determinism.md`
- `claude-skills/accounting-audit/SKILL.md`

### bitmap-packed (14 files)

- `DESIGN_SPECS/data-disciplines/aggressive-memory-reduction-techniques.md`
- `DESIGN_SPECS/data-disciplines/partner-core-bitmap-pattern.md`
- `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md`
- `DESIGN_SPECS/framework-patterns/composed-filter-mask-pattern.md`
- `DESIGN_SPECS/framework-patterns/enum-mode-flags-bitmap-lookup-pattern.md`
- `DESIGN_SPECS/framework-patterns/per-bit-per-core-override-pattern.md`
- `DESIGN_SPECS/framework-patterns/slot-state-foreach-registry-with-storage-routing.md`
- `DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md`
- `DESIGN_SPECS/refactor-patterns/bitmap-overflow-protection-discipline.md`
- `DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md`
- `DESIGN_SPECS/refactor-patterns/post-parse-normalize-with-explicit-key-bitmap-pattern.md`
- `DESIGN_SPECS/refactor-patterns/registry-bitmap-set-discipline.md`
- `DESIGN_SPECS/refactor-patterns/transient-aggregation-bitmap-pattern.md`
- `claude-skills/dod-audit/SKILL.md`

### boot-time (1 files)

- `DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md`

### cfg-flow (23 files)

- `DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md`
- `DESIGN_SPECS/framework-patterns/cfg-derived-consumer-framework.md`
- `DESIGN_SPECS/framework-patterns/framework-composition-overview.md`
- `DESIGN_SPECS/framework-patterns/metadata-bit-driven-derived-filter-framework.md`
- `DESIGN_SPECS/framework-patterns/per-bit-per-core-override-pattern.md`
- `DESIGN_SPECS/framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md`
- `DESIGN_SPECS/framework-patterns/type-trait-dispatch-via-tt-namespace.md`
- `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md`
- `DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md`
- `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md`
- `DESIGN_SPECS/refactor-patterns/cfg-section-parser-state-machine.md`
- `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md`
- `DESIGN_SPECS/refactor-patterns/post-parse-normalize-with-explicit-key-bitmap-pattern.md`
- `DESIGN_SPECS/refactor-patterns/slow-path-cfg-resolution-cache-pattern.md`
- `claude-skills/anti-spaghetti/SKILL.md`
- `claude-skills/blindspot-scan/SKILL.md`
- `claude-skills/bug-check/SKILL.md`
- `claude-skills/dependency-chain-trace/SKILL.md`
- `claude-skills/ml-audit/SKILL.md`
- `claude-skills/parity-check/SKILL.md`
- `claude-skills/precoding-audit-gate/SKILL.md`
- `claude-skills/readiness/SKILL.md`
- `claude-skills/trace-deps/SKILL.md`

### ci-tooling (9 files)

- `DESIGN_SPECS/audit-methodologies/audit-report-format.md`
- `DESIGN_SPECS/feature-patterns/runtime-toggleable-bench-gate-pattern.md`
- `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md`
- `DESIGN_SPECS/framework-patterns/registry-coverage-ci-check-pattern.md`
- `DESIGN_SPECS/refactor-patterns/bitmap-overflow-protection-discipline.md`
- `DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md`
- `claude-skills/dead-code-trace/SKILL.md`
- `claude-skills/metadata-audit/SKILL.md`
- `claude-skills/ship/SKILL.md`

### cross-tool (2 files)

- `DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md`
- `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md`

### gui-thread (6 files)

- `DESIGN_SPECS/concurrency-patterns/concurrency-model-summary.md`
- `DESIGN_SPECS/data-disciplines/per-snapshot-cluster-layout-pattern.md`
- `DESIGN_SPECS/framework-patterns/display-execution-invariant-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md`
- `claude-skills/strategy-template/SKILL.md`

### hot-path (44 files)

- `DESIGN_SPECS/concurrency-patterns/concurrency-model-summary.md`
- `DESIGN_SPECS/concurrency-patterns/cross-thread-snapshot-publish-cluster-isolation.md`
- `DESIGN_SPECS/concurrency-patterns/spsc-ring-embedded-in-hot-struct-cluster-discipline.md`
- `DESIGN_SPECS/data-disciplines/aggressive-memory-reduction-techniques.md`
- `DESIGN_SPECS/data-disciplines/cache-layout-discipline-for-hot-side-structs.md`
- `DESIGN_SPECS/data-disciplines/cache-line-discipline.md`
- `DESIGN_SPECS/data-disciplines/decision-first-cluster-layout-pattern.md`
- `DESIGN_SPECS/data-disciplines/function-struct-alignment-for-single-mov-access.md`
- `DESIGN_SPECS/data-disciplines/hot-side-array-element-alignment-for-sparse-access.md`
- `DESIGN_SPECS/data-disciplines/partner-core-bitmap-pattern.md`
- `DESIGN_SPECS/feature-patterns/runtime-toggleable-bench-gate-pattern.md`
- `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md`
- `DESIGN_SPECS/framework-patterns/display-execution-invariant-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/dual-axis-y3-dispatch-pattern.md`
- `DESIGN_SPECS/framework-patterns/enum-mode-flags-bitmap-lookup-pattern.md`
- `DESIGN_SPECS/framework-patterns/multi-state-dispatch-with-per-state-update-metadata.md`
- `DESIGN_SPECS/framework-patterns/per-bit-per-core-override-pattern.md`
- `DESIGN_SPECS/framework-patterns/sink-fn-pointer-for-optional-side-effect-pattern.md`
- `DESIGN_SPECS/framework-patterns/slot-state-foreach-registry-with-storage-routing.md`
- `DESIGN_SPECS/framework-patterns/slow-path-gate-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md`
- `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md`
- `DESIGN_SPECS/refactor-patterns/branchless-math-kernel-pattern.md`
- `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md`
- `DESIGN_SPECS/refactor-patterns/failure-attribution-buffer-pattern.md`
- `DESIGN_SPECS/refactor-patterns/generic-ring-buffer-template-pattern.md`
- `DESIGN_SPECS/refactor-patterns/latency-vs-cache-decision-framework.md`
- `DESIGN_SPECS/refactor-patterns/loop-fusion-pattern.md`
- `DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md`
- `DESIGN_SPECS/refactor-patterns/registry-bitmap-set-discipline.md`
- `DESIGN_SPECS/refactor-patterns/transient-aggregation-bitmap-pattern.md`
- `DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md`
- `claude-skills/accounting-audit/SKILL.md`
- `claude-skills/anti-spaghetti/SKILL.md`
- `claude-skills/bug-check/SKILL.md`
- `claude-skills/dependency-chain-trace/SKILL.md`
- `claude-skills/dod-audit/SKILL.md`
- `claude-skills/finding-analyzer/SKILL.md`
- `claude-skills/hft-audit/SKILL.md`
- `claude-skills/latency-track/SKILL.md`
- `claude-skills/merge-scan/SKILL.md`
- `claude-skills/patch-planner/SKILL.md`
- `claude-skills/post-ship-audit/SKILL.md`
- `claude-skills/precoding-audit-gate/SKILL.md`

### live-trading (1 files)

- `claude-skills/accounting-audit/SKILL.md`

### ml-inference (13 files)

- `DESIGN_SPECS/feature-patterns/per-horizon-barrier-blending-with-shadow-mode.md`
- `DESIGN_SPECS/feature-patterns/shadow-load-state-transition-pattern.md`
- `DESIGN_SPECS/framework-patterns/stamp-vs-runtime-drift-detection-registry.md`
- `DESIGN_SPECS/refactor-patterns/branchless-math-kernel-pattern.md`
- `DESIGN_SPECS/refactor-patterns/sliding-window-online-statistics-pattern.md`
- `DESIGN_SPECS/wire-format-patterns/prng-choice-for-replay-determinism.md`
- `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md`
- `DESIGN_SPECS/wire-format-patterns/wire-format-canonical-body-invariants-helper.md`
- `claude-skills/ml-audit/SKILL.md`
- `claude-skills/parity-check/SKILL.md`
- `claude-skills/patch-planner/SKILL.md`
- `claude-skills/strategy-template/SKILL.md`
- `claude-skills/sync-models/SKILL.md`

### oms-drainer (15 files)

- `DESIGN_SPECS/concurrency-patterns/concurrency-model-summary.md`
- `DESIGN_SPECS/concurrency-patterns/phase-separated-drainer-for-safe-cross-temporal-derives.md`
- `DESIGN_SPECS/concurrency-patterns/spsc-ring-embedded-in-hot-struct-cluster-discipline.md`
- `DESIGN_SPECS/data-disciplines/raii-destructor-with-cluster-reorg-interaction.md`
- `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md`
- `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md`
- `DESIGN_SPECS/refactor-patterns/failure-attribution-buffer-pattern.md`
- `DESIGN_SPECS/refactor-patterns/template-deferred-dependency-injection.md`
- `claude-skills/accounting-audit/SKILL.md`
- `claude-skills/bug-check/SKILL.md`
- `claude-skills/hft-audit/SKILL.md`
- `claude-skills/latency-track/SKILL.md`
- `claude-skills/merge-scan/SKILL.md`
- `claude-skills/patch-planner/SKILL.md`
- `claude-skills/post-ship-audit/SKILL.md`

### parser (6 files)

- `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md`
- `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md`
- `DESIGN_SPECS/refactor-patterns/cfg-section-parser-state-machine.md`
- `DESIGN_SPECS/refactor-patterns/post-parse-normalize-with-explicit-key-bitmap-pattern.md`
- `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md`
- `claude-skills/parity-check/SKILL.md`

### producer (4 files)

- `DESIGN_SPECS/concurrency-patterns/concurrency-model-summary.md`
- `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md`
- `claude-skills/hft-audit/SKILL.md`
- `claude-skills/latency-track/SKILL.md`

### registry (60 files)

- `DESIGN_SPECS/audit-methodologies/audit-driven-pre-coding-gate.md`
- `DESIGN_SPECS/audit-methodologies/audit-scope-taxonomy.md`
- `DESIGN_SPECS/framework-patterns/autopopulate-from-arity-macro-family.md`
- `DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md`
- `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md`
- `DESIGN_SPECS/framework-patterns/calibration-log-column-registry.md`
- `DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md`
- `DESIGN_SPECS/framework-patterns/cfg-derived-consumer-framework.md`
- `DESIGN_SPECS/framework-patterns/composed-filter-mask-pattern.md`
- `DESIGN_SPECS/framework-patterns/curve-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/display-execution-invariant-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/dual-axis-y3-dispatch-pattern.md`
- `DESIGN_SPECS/framework-patterns/enum-mode-flags-bitmap-lookup-pattern.md`
- `DESIGN_SPECS/framework-patterns/framework-composition-overview.md`
- `DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/manual-fields-inventory-pattern.md`
- `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md`
- `DESIGN_SPECS/framework-patterns/metadata-bit-driven-derived-filter-framework.md`
- `DESIGN_SPECS/framework-patterns/multi-action-registry-walker-family.md`
- `DESIGN_SPECS/framework-patterns/multi-state-dispatch-with-per-state-update-metadata.md`
- `DESIGN_SPECS/framework-patterns/per-instance-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/persisted-struct-with-ephemeral-field-coexistence-pattern.md`
- `DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/registry-coverage-ci-check-pattern.md`
- `DESIGN_SPECS/framework-patterns/registry-tuple-as-single-source-of-truth.md`
- `DESIGN_SPECS/framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md`
- `DESIGN_SPECS/framework-patterns/slot-state-foreach-registry-with-storage-routing.md`
- `DESIGN_SPECS/framework-patterns/slow-path-gate-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/stamp-vs-runtime-drift-detection-registry.md`
- `DESIGN_SPECS/framework-patterns/type-erased-per-core-resource-handle-pattern.md`
- `DESIGN_SPECS/framework-patterns/type-trait-dispatch-via-tt-namespace.md`
- `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md`
- `DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md`
- `DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md`
- `DESIGN_SPECS/meta-disciplines/doc-frontmatter-convention.md`
- `DESIGN_SPECS/meta-disciplines/doc-tag-vocabulary.md`
- `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md`
- `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md`
- `DESIGN_SPECS/refactor-patterns/bitmap-overflow-protection-discipline.md`
- `DESIGN_SPECS/refactor-patterns/cross-walker-struct-field-uniqueness-discipline.md`
- `DESIGN_SPECS/refactor-patterns/orchestration-helper-with-pod-args-pattern.md`
- `DESIGN_SPECS/refactor-patterns/registry-bitmap-set-discipline.md`
- `DESIGN_SPECS/wire-format-patterns/pre-post-cfg-registry-split-for-emit-order-preservation.md`
- `claude-skills/anti-spaghetti/SKILL.md`
- `claude-skills/blindspot-scan/SKILL.md`
- `claude-skills/bug-check/SKILL.md`
- `claude-skills/dead-code-trace/SKILL.md`
- `claude-skills/dependency-chain-trace/SKILL.md`
- `claude-skills/dod-audit/SKILL.md`
- `claude-skills/dust/SKILL.md`
- `claude-skills/finding-analyzer/SKILL.md`
- `claude-skills/hft-audit/SKILL.md`
- `claude-skills/merge-scan/SKILL.md`
- `claude-skills/post-ship-audit/SKILL.md`
- `claude-skills/precoding-audit-gate/SKILL.md`
- `claude-skills/readiness/SKILL.md`
- `claude-skills/registry-fit-audit/SKILL.md`
- `claude-skills/strategy-template/SKILL.md`
- `claude-skills/trace-deps/SKILL.md`

### slow-path (41 files)

- `DESIGN_SPECS/concurrency-patterns/concurrency-model-summary.md`
- `DESIGN_SPECS/concurrency-patterns/cross-thread-snapshot-publish-cluster-isolation.md`
- `DESIGN_SPECS/concurrency-patterns/phase-separated-drainer-for-safe-cross-temporal-derives.md`
- `DESIGN_SPECS/data-disciplines/cache-layout-discipline-for-hot-side-structs.md`
- `DESIGN_SPECS/data-disciplines/cache-line-discipline.md`
- `DESIGN_SPECS/data-disciplines/decision-first-cluster-layout-pattern.md`
- `DESIGN_SPECS/data-disciplines/function-struct-alignment-for-single-mov-access.md`
- `DESIGN_SPECS/data-disciplines/hot-side-array-element-alignment-for-sparse-access.md`
- `DESIGN_SPECS/data-disciplines/per-snapshot-cluster-layout-pattern.md`
- `DESIGN_SPECS/data-disciplines/raii-destructor-with-cluster-reorg-interaction.md`
- `DESIGN_SPECS/feature-patterns/per-horizon-barrier-blending-with-shadow-mode.md`
- `DESIGN_SPECS/feature-patterns/runtime-toggleable-bench-gate-pattern.md`
- `DESIGN_SPECS/feature-patterns/shadow-load-state-transition-pattern.md`
- `DESIGN_SPECS/framework-patterns/curve-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/sink-fn-pointer-for-optional-side-effect-pattern.md`
- `DESIGN_SPECS/framework-patterns/slow-path-gate-registry-pattern.md`
- `DESIGN_SPECS/framework-patterns/type-erased-per-core-resource-handle-pattern.md`
- `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md`
- `DESIGN_SPECS/refactor-patterns/branchless-math-kernel-pattern.md`
- `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md`
- `DESIGN_SPECS/refactor-patterns/failure-attribution-buffer-pattern.md`
- `DESIGN_SPECS/refactor-patterns/generic-ring-buffer-template-pattern.md`
- `DESIGN_SPECS/refactor-patterns/latency-vs-cache-decision-framework.md`
- `DESIGN_SPECS/refactor-patterns/loop-fusion-pattern.md`
- `DESIGN_SPECS/refactor-patterns/sliding-window-online-statistics-pattern.md`
- `DESIGN_SPECS/refactor-patterns/slow-path-cfg-resolution-cache-pattern.md`
- `DESIGN_SPECS/refactor-patterns/template-deferred-dependency-injection.md`
- `DESIGN_SPECS/refactor-patterns/transient-aggregation-bitmap-pattern.md`
- `DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md`
- `claude-skills/accounting-audit/SKILL.md`
- `claude-skills/anti-spaghetti/SKILL.md`
- `claude-skills/bug-check/SKILL.md`
- `claude-skills/dependency-chain-trace/SKILL.md`
- `claude-skills/dod-audit/SKILL.md`
- `claude-skills/finding-analyzer/SKILL.md`
- `claude-skills/hft-audit/SKILL.md`
- `claude-skills/latency-track/SKILL.md`
- `claude-skills/merge-scan/SKILL.md`
- `claude-skills/patch-planner/SKILL.md`
- `claude-skills/post-ship-audit/SKILL.md`
- `claude-skills/precoding-audit-gate/SKILL.md`

### test-infrastructure (5 files)

- `DESIGN_SPECS/audit-methodologies/audit-report-format.md`
- `DESIGN_SPECS/framework-patterns/registry-coverage-ci-check-pattern.md`
- `claude-skills/dead-code-trace/SKILL.md`
- `claude-skills/strategy-template/SKILL.md`
- `claude-skills/test-strength-audit/SKILL.md`

### training (6 files)

- `DESIGN_SPECS/feature-patterns/per-horizon-barrier-blending-with-shadow-mode.md`
- `DESIGN_SPECS/feature-patterns/shadow-load-state-transition-pattern.md`
- `DESIGN_SPECS/wire-format-patterns/prng-choice-for-replay-determinism.md`
- `claude-skills/ml-audit/SKILL.md`
- `claude-skills/parity-check/SKILL.md`
- `claude-skills/sync-models/SKILL.md`

### wire-format (24 files)

- `DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md`
- `DESIGN_SPECS/framework-patterns/calibration-log-column-registry.md`
- `DESIGN_SPECS/framework-patterns/cfg-derived-consumer-framework.md`
- `DESIGN_SPECS/framework-patterns/framework-composition-overview.md`
- `DESIGN_SPECS/framework-patterns/metadata-bit-driven-derived-filter-framework.md`
- `DESIGN_SPECS/framework-patterns/persisted-struct-with-ephemeral-field-coexistence-pattern.md`
- `DESIGN_SPECS/framework-patterns/stamp-vs-runtime-drift-detection-registry.md`
- `DESIGN_SPECS/framework-patterns/type-trait-dispatch-via-tt-namespace.md`
- `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md`
- `DESIGN_SPECS/refactor-patterns/cross-walker-struct-field-uniqueness-discipline.md`
- `DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md`
- `DESIGN_SPECS/refactor-patterns/orchestration-helper-with-pod-args-pattern.md`
- `DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md`
- `DESIGN_SPECS/wire-format-patterns/pre-post-cfg-registry-split-for-emit-order-preservation.md`
- `DESIGN_SPECS/wire-format-patterns/struct-padding-determinism-pattern.md`
- `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md`
- `DESIGN_SPECS/wire-format-patterns/wire-format-canonical-body-invariants-helper.md`
- `claude-skills/accounting-audit/SKILL.md`
- `claude-skills/blindspot-scan/SKILL.md`
- `claude-skills/dod-audit/SKILL.md`
- `claude-skills/ml-audit/SKILL.md`
- `claude-skills/parity-check/SKILL.md`
- `claude-skills/precoding-audit-gate/SKILL.md`
- `claude-skills/readiness/SKILL.md`
