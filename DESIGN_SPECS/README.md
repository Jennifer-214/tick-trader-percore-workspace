# DESIGN_SPECS catalog

**Auto-generated** by `tools/rebuild_doc_indexes.py`. Regenerate after adding/moving specs.

Total: 190 specs across 15 types.

Per-type catalog grouped by lifecycle stage. Cross-ref:
- `doc-frontmatter-convention.md` (frontmatter schema)
- `doc-tag-vocabulary.md` (tag canonical list)
- CLAUDE.md § How to find anything (grep recipes)

## refactor-pattern (25 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/refactor-patterns/bitmap-overflow-protection-discipline.md` | 5-claude-md | framework-discipline, data-oriented-design, structural-fix | 2 |
| `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md` | 5-claude-md | branchless-discipline, latency-discipline, structural-fix | 3 |
| `DESIGN_SPECS/refactor-patterns/branchless-math-kernel-pattern.md` | 3-first-canonical | branchless-discipline, latency-discipline, fixed-point-math | 3 |
| `DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md` | 3-first-canonical | framework-discipline, structural-fix, pattern-codification | 3 |
| `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` | 2-draft | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/refactor-patterns/cfg-section-parser-state-machine.md` | 2-draft | framework-discipline, structural-fix | 2 |
| `DESIGN_SPECS/refactor-patterns/critical-moment-determinism-over-average-latency.md` | 3-first-canonical | hot-path, determinism, branchless, +2 | 0 |
| `DESIGN_SPECS/refactor-patterns/cross-walker-struct-field-uniqueness-discipline.md` | 2-draft | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` | 5-claude-md | structural-fix, framework-discipline, latency-discipline | 3 |
| `DESIGN_SPECS/refactor-patterns/failure-attribution-buffer-pattern.md` | 2-draft | failure-observability, structural-fix, framework-discipline | 2 |
| `DESIGN_SPECS/refactor-patterns/framework-driven-cli-binary-pattern.md` | 2-draft | cross-tool-decoupling, structural-fix, framework-discipline, +1 | 3 |
| `DESIGN_SPECS/refactor-patterns/generic-ring-buffer-template-pattern.md` | 3-first-canonical | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/refactor-patterns/latency-vs-cache-decision-framework.md` | 5-claude-md | latency-discipline, data-oriented-design | 4 |
| `DESIGN_SPECS/refactor-patterns/loop-fusion-pattern.md` | 3-first-canonical | latency-discipline, data-oriented-design | 3 |
| `DESIGN_SPECS/refactor-patterns/multi-bit-state-encoding-pattern.md` | 5-claude-md | data-oriented-design, branchless-discipline, structural-fix | 4 |
| `DESIGN_SPECS/refactor-patterns/orchestration-helper-with-pod-args-pattern.md` | 3-first-canonical | framework-discipline, structural-fix | 2 |
| `DESIGN_SPECS/refactor-patterns/post-parse-normalize-with-explicit-key-bitmap-pattern.md` | 3-first-canonical | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/refactor-patterns/registry-bitmap-set-discipline.md` | 3-first-canonical | structural-fix, framework-discipline, data-oriented-design | 4 |
| `DESIGN_SPECS/refactor-patterns/rename-cascade-enumeration-tooling.md` | 2-draft | refactor-pattern, ci-tooling, bulk-rename, +3 | 3 |
| `DESIGN_SPECS/refactor-patterns/rename-ship-methodology.md` | 4-cohort | refactor-pattern, doc-discipline, terminology-evolution, +1 | 2 |
| `DESIGN_SPECS/refactor-patterns/shared-helper-extract-for-train-serve-mirror-close.md` | 2-draft | structural-fix, framework-discipline | 0 |
| `DESIGN_SPECS/refactor-patterns/sliding-window-online-statistics-pattern.md` | 3-first-canonical | fixed-point-math, latency-discipline | 2 |
| `DESIGN_SPECS/refactor-patterns/slow-path-cfg-resolution-cache-pattern.md` | 3-first-canonical | latency-discipline, data-oriented-design, structural-fix | 3 |
| `DESIGN_SPECS/refactor-patterns/template-deferred-dependency-injection.md` | 3-first-canonical | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/refactor-patterns/transient-aggregation-bitmap-pattern.md` | 3-first-canonical | data-oriented-design, branchless-discipline | 4 |

## framework-pattern (74 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/framework-patterns/autopopulate-from-arity-macro-family.md` | 3-first-canonical | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/autopopulate-pattern-for-production-caller-class.md` | 3-first-canonical | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/bitmap-flag-api.md` | 5-claude-md | framework-discipline, data-oriented-design, branchless-discipline, +1 | 4 |
| `DESIGN_SPECS/framework-patterns/built-in-observability-pattern.md` | 3-first-canonical | framework-discipline, observability, prometheus, +2 | 0 |
| `DESIGN_SPECS/framework-patterns/calibration-log-column-registry.md` | 3-first-canonical | framework-discipline, wire-format, structural-fix | 4 |
| `DESIGN_SPECS/framework-patterns/capital-allocation-policy-pattern.md` | 3-first-canonical | framework-discipline, capital-allocation, risk-management, +2 | 0 |
| `DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md` | 3-first-canonical | framework-discipline, structural-fix, pattern-codification | 3 |
| `DESIGN_SPECS/framework-patterns/cfg-derived-consumer-framework.md` | 3-first-canonical | framework-discipline, structural-fix, pattern-codification | 4 |
| `DESIGN_SPECS/framework-patterns/cfg-field-categorization-discipline.md` | 3-first-canonical | framework-discipline, data-oriented-design, structural-fix | 5 |
| `DESIGN_SPECS/framework-patterns/cluster-node-hierarchy-filesystem-layout-pattern.md` | 3-first-canonical | framework-discipline, cluster-node-hierarchy, filesystem-layout, +1 | 0 |
| `DESIGN_SPECS/framework-patterns/composed-filter-mask-pattern.md` | 3-first-canonical | framework-discipline, branchless-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/config-compiler-validation-pattern.md` | 3-first-canonical | framework-discipline, capital-safety, config-validation, +3 | 7 |
| `DESIGN_SPECS/framework-patterns/crash-recovery-action-policy-pattern.md` | 2-draft | framework-discipline, crash-recovery, operator-policy | 0 |
| `DESIGN_SPECS/framework-patterns/crash-recovery-via-mmap-state-pattern.md` | 3-first-canonical | framework-discipline, crash-recovery, mmap, +2 | 0 |
| `DESIGN_SPECS/framework-patterns/curve-registry-pattern.md` | 3-first-canonical | framework-discipline, branchless-discipline | 3 |
| `DESIGN_SPECS/framework-patterns/dev-vs-production-thread-topology-pattern.md` | 3-first-canonical | framework-discipline, thread-topology, dev-mode, +3 | 0 |
| `DESIGN_SPECS/framework-patterns/display-execution-invariant-registry-pattern.md` | 3-first-canonical | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/doc-intelligence-toolchain-architecture.md` | 3-first-canonical | framework-discipline, ssot, doc-discipline, +1 | 4 |
| `DESIGN_SPECS/framework-patterns/dual-axis-y3-dispatch-pattern.md` | 3-first-canonical | framework-discipline, branchless-discipline | 3 |
| `DESIGN_SPECS/framework-patterns/dual-format-metrics-publication-pattern.md` | 3-first-canonical | framework-discipline, metrics-publication, mmap, +2 | 0 |
| `DESIGN_SPECS/framework-patterns/dynamic-library-strategy-loading-pattern.md` | 3-first-canonical | framework-discipline, dlopen, abi-versioning, +1 | 0 |
| `DESIGN_SPECS/framework-patterns/enum-mode-flags-bitmap-lookup-pattern.md` | 3-first-canonical | framework-discipline, data-oriented-design, branchless-discipline | 3 |
| `DESIGN_SPECS/framework-patterns/event-sourced-aggregator-o1-pattern.md` | 3-first-canonical | framework-discipline, aggregator, event-sourcing, +3 | 0 |
| `DESIGN_SPECS/framework-patterns/exchange-adapter-implementation-contract.md` | 3-first-canonical | framework-discipline, exchange-adapter, implementation-contract, +1 | 0 |
| `DESIGN_SPECS/framework-patterns/exchange-adapter-tt-dispatch-pattern.md` | 3-first-canonical | framework-discipline, tt-dispatch, exchange-adapter, +2 | 0 |
| `DESIGN_SPECS/framework-patterns/fix-session-management-pattern.md` | 2-draft | framework-discipline, fix-protocol, session-management, +1 | 0 |
| `DESIGN_SPECS/framework-patterns/foreach-exchange-meta-registry-pattern.md` | 3-first-canonical | framework-discipline, multi-exchange-substrate, x-macro-registry, +1 | 0 |
| `DESIGN_SPECS/framework-patterns/foreach-subaccount-meta-registry-pattern.md` | 3-first-canonical | framework-discipline, sub-accounts, x-macro-registry, +2 | 0 |
| `DESIGN_SPECS/framework-patterns/framework-composition-overview.md` | 3-first-canonical | framework-discipline, pattern-codification, doc-discipline | 5 |
| `DESIGN_SPECS/framework-patterns/global-aggregator-readonly-pattern.md` | 3-first-canonical | framework-discipline, aggregator, read-only, +2 | 0 |
| `DESIGN_SPECS/framework-patterns/heterogeneous-registry-pattern.md` | 3-first-canonical | framework-discipline, pattern-codification | 3 |
| `DESIGN_SPECS/framework-patterns/hierarchical-config-validation-pattern.md` | 3-first-canonical | framework-discipline, config-validation, boot-time-check, +1 | 0 |
| `DESIGN_SPECS/framework-patterns/hierarchical-config-with-per-node-folders.md` | 3-first-canonical | framework-discipline, hierarchical-config, per-node-folders, +1 | 0 |
| `DESIGN_SPECS/framework-patterns/hybrid-reconciliation-cadence-pattern.md` | 2-draft | framework-discipline, reconciliation, hybrid-cadence | 0 |
| `DESIGN_SPECS/framework-patterns/ibkr-fa-structure-pattern.md` | 2-draft | framework-discipline, ibkr, financial-advisor, +1 | 0 |
| `DESIGN_SPECS/framework-patterns/isolated-per-struct-layout-probe.md` | 3-first-canonical | framework-discipline, doc-discipline, ci-tooling, +1 | 4 |
| `DESIGN_SPECS/framework-patterns/kernel-vs-userspace-networking-cfg-pattern.md` | 2-draft | framework-discipline, networking-stack, cfg-driven, +1 | 0 |
| `DESIGN_SPECS/framework-patterns/kill-switch-hierarchical-pattern.md` | 3-first-canonical | framework-discipline, kill-switch, safety, +2 | 0 |
| `DESIGN_SPECS/framework-patterns/manual-fields-inventory-pattern.md` | 3-first-canonical | framework-discipline, structural-fix, pattern-codification | 4 |
| `DESIGN_SPECS/framework-patterns/meta-registry-pattern-for-codebase-registry-discipline.md` | 5-claude-md | framework-discipline, structural-fix, meta-discipline, +1 | 4 |
| `DESIGN_SPECS/framework-patterns/metadata-bit-driven-derived-filter-framework.md` | 4-cohort | framework-discipline, structural-fix, pattern-codification | 6 |
| `DESIGN_SPECS/framework-patterns/multi-action-registry-walker-family.md` | 2-draft | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/multi-asset-class-symbol-pattern.md` | 2-draft | framework-discipline, multi-asset, symbol-normalization, +1 | 0 |
| `DESIGN_SPECS/framework-patterns/multi-state-dispatch-with-per-state-update-metadata.md` | 3-first-canonical | framework-discipline, branchless-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/native-tui-via-mmap-readonly-pattern.md` | 3-first-canonical | framework-discipline, tui, notcurses, +3 | 0 |
| `DESIGN_SPECS/framework-patterns/one-action-toolchain-update-orchestrator.md` | 2-draft | framework-pattern, dev-plane, ssot, +2 | 0 |
| `DESIGN_SPECS/framework-patterns/per-bit-per-core-override-pattern.md` | 3-first-canonical | framework-discipline, branchless-discipline, data-oriented-design | 3 |
| `DESIGN_SPECS/framework-patterns/per-cluster-producer-pattern.md` | 3-first-canonical | framework-discipline, per-cluster-producer, market-data-fan-out, +1 | 0 |
| `DESIGN_SPECS/framework-patterns/per-cluster-shared-resource-pattern.md` | 3-first-canonical | framework-discipline, per-cluster-resources, thread-topology, +1 | 0 |
| `DESIGN_SPECS/framework-patterns/per-exchange-submit-protocol-selection.md` | 3-first-canonical | framework-discipline, submit-protocol, per-exchange, +1 | 0 |
| `DESIGN_SPECS/framework-patterns/per-instance-registry-pattern.md` | 2-draft | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/per-node-economic-isolation-pattern.md` | 3-first-canonical | framework-discipline, economic-isolation, sub-accounts, +2 | 0 |
| `DESIGN_SPECS/framework-patterns/per-node-io-rings-pattern.md` | 3-first-canonical | framework-discipline, per-node-io, numa-aware, +1 | 0 |
| `DESIGN_SPECS/framework-patterns/per-node-paper-mode-flag-pattern.md` | 3-first-canonical | framework-discipline, per-node-mode, paper-trading, +3 | 0 |
| `DESIGN_SPECS/framework-patterns/persisted-struct-with-ephemeral-field-coexistence-pattern.md` | 3-first-canonical | framework-discipline, structural-fix, wire-format | 3 |
| `DESIGN_SPECS/framework-patterns/portfolio-soa-vectorization-pattern.md` | 2-draft | data-layout, soa, avx-512, +2 | 0 |
| `DESIGN_SPECS/framework-patterns/postloadsetup-registry-pattern.md` | 3-first-canonical | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/registry-coverage-ci-check-pattern.md` | 3-first-canonical | framework-discipline, structural-fix, pattern-codification | 4 |
| `DESIGN_SPECS/framework-patterns/registry-tuple-as-single-source-of-truth.md` | 5-claude-md | framework-discipline, structural-fix, pattern-codification | 4 |
| `DESIGN_SPECS/framework-patterns/runtime-mutable-vs-boot-time-config-pattern.md` | 3-first-canonical | framework-discipline, cfg-mutability, hot-reload, +1 | 0 |
| `DESIGN_SPECS/framework-patterns/sidecar-override-pattern-for-registry-auto-flows.md` | 5-claude-md | framework-discipline, structural-fix, pattern-codification | 6 |
| `DESIGN_SPECS/framework-patterns/single-authority-predicate-for-mode-gating.md` | 2-draft | framework-discipline, capital-safety, ssot, +2 | 4 |
| `DESIGN_SPECS/framework-patterns/sink-fn-pointer-for-optional-side-effect-pattern.md` | 3-first-canonical | framework-discipline, branchless-discipline | 2 |
| `DESIGN_SPECS/framework-patterns/slot-state-foreach-registry-with-storage-routing.md` | 3-first-canonical | framework-discipline, structural-fix, data-oriented-design | 3 |
| `DESIGN_SPECS/framework-patterns/slow-path-gate-registry-pattern.md` | 3-first-canonical | framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/stamp-vs-runtime-drift-detection-registry.md` | 3-first-canonical | framework-discipline, wire-format, structural-fix | 3 |
| `DESIGN_SPECS/framework-patterns/standardized-tool-io-envelope-and-payload.md` | 2-draft | framework-pattern, dev-plane, ssot, +2 | 0 |
| `DESIGN_SPECS/framework-patterns/strategy-hot-reload-via-dlopen-pattern.md` | 3-first-canonical | framework-discipline, hot-reload, dlopen, +2 | 0 |
| `DESIGN_SPECS/framework-patterns/tls-session-resumption-pattern.md` | 3-first-canonical | framework-discipline, tls-resumption, reconnect-optimization | 0 |
| `DESIGN_SPECS/framework-patterns/type-erased-per-core-resource-handle-pattern.md` | 3-first-canonical | framework-discipline, concurrency, structural-fix | 2 |
| `DESIGN_SPECS/framework-patterns/type-trait-dispatch-via-tt-namespace.md` | 5-claude-md | framework-discipline, structural-fix, branchless-discipline | 3 |
| `DESIGN_SPECS/framework-patterns/universal-cfg-field-registry-pattern.md` | 5-claude-md | framework-discipline, structural-fix, pattern-codification | 9 |
| `DESIGN_SPECS/framework-patterns/universal-registry-bitmap-dispatcher-pattern.md` | 3-first-canonical | framework-discipline, data-oriented-design, branchless-discipline, +1 | 5 |
| `DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md` | 5-claude-md | framework-discipline, structural-fix, branchless-discipline | 5 |

## feature-pattern (3 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/feature-patterns/per-horizon-barrier-blending-with-shadow-mode.md` | 2-draft | framework-discipline, structural-fix | 1 |
| `DESIGN_SPECS/feature-patterns/runtime-toggleable-bench-gate-pattern.md` | 3-first-canonical | latency-discipline, framework-discipline | 1 |
| `DESIGN_SPECS/feature-patterns/shadow-load-state-transition-pattern.md` | 3-first-canonical | framework-discipline, structural-fix, concurrency | 1 |

## audit-methodology (8 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/audit-methodologies/adversarial-multi-agent-audit-methodology.md` | 3-first-canonical | audit-methodology, meta-discipline, framework-discipline | 3 |
| `DESIGN_SPECS/audit-methodologies/audit-driven-pre-coding-gate.md` | 3-first-canonical | audit-methodology, framework-discipline, meta-discipline | 6 |
| `DESIGN_SPECS/audit-methodologies/audit-finding-kind-taxonomy.md` | 2-draft | audit-methodology, scope-discipline, finding-triage | 2 |
| `DESIGN_SPECS/audit-methodologies/audit-report-format.md` | 2-draft | audit-methodology, doc-discipline, framework-discipline | 4 |
| `DESIGN_SPECS/audit-methodologies/audit-scope-taxonomy.md` | 3-first-canonical | audit-methodology, meta-discipline, framework-discipline | 2 |
| `DESIGN_SPECS/audit-methodologies/characterization-test-discipline.md` | 3-first-canonical | audit-methodology, test-discipline, capital-safety, +1 | 2 |
| `DESIGN_SPECS/audit-methodologies/post-implementation-verification-v-class.md` | 2-draft | audit-methodology, verification, sanitizers, +3 | 3 |
| `DESIGN_SPECS/audit-methodologies/static-latency-path-conformance-analysis.md` | 3-first-canonical | audit-methodology, latency-discipline, branchless-discipline, +2 | 0 |

## data-discipline (16 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/data-disciplines/aggressive-memory-reduction-techniques.md` | 3-first-canonical | data-oriented-design, structural-fix, framework-discipline | 6 |
| `DESIGN_SPECS/data-disciplines/cache-layout-discipline-for-hot-side-structs.md` | 3-first-canonical | data-oriented-design, latency-discipline, concurrency | 5 |
| `DESIGN_SPECS/data-disciplines/cache-line-discipline.md` | 2-draft | data-oriented-design, concurrency, latency-discipline | 4 |
| `DESIGN_SPECS/data-disciplines/cpp17-inline-variable-for-header-shared-state.md` | 3-first-canonical | cpp17, header-only, shared-state, +1 | 2 |
| `DESIGN_SPECS/data-disciplines/decision-first-cluster-layout-pattern.md` | 3-first-canonical | data-oriented-design, latency-discipline | 4 |
| `DESIGN_SPECS/data-disciplines/fill-path-completeness-and-normalization-discipline.md` | 2-draft | capital-safety, oms-drainer, fill-path, +3 | 0 |
| `DESIGN_SPECS/data-disciplines/function-struct-alignment-for-single-mov-access.md` | 3-first-canonical | data-oriented-design, latency-discipline | 4 |
| `DESIGN_SPECS/data-disciplines/hot-side-array-element-alignment-for-sparse-access.md` | 3-first-canonical | data-oriented-design, latency-discipline | 3 |
| `DESIGN_SPECS/data-disciplines/locale-determinism-discipline.md` | 3-first-canonical | determinism, locale, parsing, +5 | 0 |
| `DESIGN_SPECS/data-disciplines/partner-core-bitmap-pattern.md` | 3-first-canonical | data-oriented-design, branchless-discipline | 3 |
| `DESIGN_SPECS/data-disciplines/per-node-position-ownership-model.md` | 2-draft | data-oriented-design, capital-safety, reconcile-recovery, +2 | 0 |
| `DESIGN_SPECS/data-disciplines/per-node-purity-scale-invariance.md` | 3-first-canonical | data-oriented-design, scale-invariance, per-node-purity, +3 | 0 |
| `DESIGN_SPECS/data-disciplines/per-snapshot-cluster-layout-pattern.md` | 3-first-canonical | data-oriented-design, concurrency, latency-discipline | 4 |
| `DESIGN_SPECS/data-disciplines/raii-destructor-with-cluster-reorg-interaction.md` | 3-first-canonical | data-oriented-design, concurrency | 3 |
| `DESIGN_SPECS/data-disciplines/register-spill-discipline.md` | 2-draft | data-oriented-design, latency-discipline, codegen | 2 |
| `DESIGN_SPECS/data-disciplines/running-aggregate-vs-cycle-recompute-discipline.md` | 2-draft | data-discipline, running-aggregate, o1-compute, +2 | 0 |

## concurrency-pattern (12 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/concurrency-patterns/concurrency-model-summary.md` | 2-draft | concurrency, data-oriented-design | 3 |
| `DESIGN_SPECS/concurrency-patterns/cross-thread-multiword-read-consistency-discipline.md` | 3-first-canonical | concurrency, data-oriented-design, framework-discipline | 1 |
| `DESIGN_SPECS/concurrency-patterns/cross-thread-snapshot-publish-cluster-isolation.md` | 3-first-canonical | concurrency, data-oriented-design, latency-discipline | 4 |
| `DESIGN_SPECS/concurrency-patterns/dpdk-userspace-networking-pattern.md` | 2-draft | concurrency, dpdk, userspace-networking, +2 | 0 |
| `DESIGN_SPECS/concurrency-patterns/io-uring-kernel-bypass-pattern.md` | 3-first-canonical | concurrency, io-uring, kernel-bypass-lite, +2 | 0 |
| `DESIGN_SPECS/concurrency-patterns/ktls-kernel-tls-pattern.md` | 3-first-canonical | concurrency, ktls, kernel-tls, +2 | 0 |
| `DESIGN_SPECS/concurrency-patterns/persistent-ws-connection-management-pattern.md` | 3-first-canonical | concurrency, websocket, persistent-connection, +2 | 0 |
| `DESIGN_SPECS/concurrency-patterns/phase-separated-drainer-for-safe-cross-temporal-derives.md` | 3-first-canonical | concurrency, structural-fix, latency-discipline | 3 |
| `DESIGN_SPECS/concurrency-patterns/spsc-ring-embedded-in-hot-struct-cluster-discipline.md` | 3-first-canonical | concurrency, data-oriented-design, latency-discipline | 4 |
| `DESIGN_SPECS/concurrency-patterns/spsc-vs-blackboard-selection-criteria.md` | 3-first-canonical | concurrency, spsc-rings, seqlock-blackboard, +1 | 0 |
| `DESIGN_SPECS/concurrency-patterns/structured-audit-log-pattern.md` | 3-first-canonical | concurrency, audit-log, jsonl, +2 | 0 |
| `DESIGN_SPECS/concurrency-patterns/userspace-tls-pattern.md` | 2-draft | concurrency, userspace-tls, dpdk, +2 | 0 |

## wire-format-pattern (6 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/wire-format-patterns/avx512-byte-determinism-pattern.md` | 3-first-canonical | wire-format, fixed-point-math, structural-fix | 2 |
| `DESIGN_SPECS/wire-format-patterns/pre-post-cfg-registry-split-for-emit-order-preservation.md` | 3-first-canonical | wire-format, framework-discipline, structural-fix | 3 |
| `DESIGN_SPECS/wire-format-patterns/prng-choice-for-replay-determinism.md` | 3-first-canonical | wire-format, fixed-point-math | 2 |
| `DESIGN_SPECS/wire-format-patterns/struct-padding-determinism-pattern.md` | 5-claude-md | wire-format, data-oriented-design, fixed-point-math | 3 |
| `DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md` | 5-claude-md | wire-format, framework-discipline, structural-fix, +1 | 6 |
| `DESIGN_SPECS/wire-format-patterns/wire-format-canonical-body-invariants-helper.md` | 3-first-canonical | wire-format, framework-discipline, structural-fix | 3 |

## doc-discipline (5 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md` | 2-draft | doc-discipline, framework-discipline, structural-fix, +1 | 6 |
| `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md` | 3-first-canonical | doc-discipline, structural-fix, pattern-codification, +1 | 6 |
| `DESIGN_SPECS/doc-disciplines/in-code-documentation-schema.md` | 3-first-canonical | doc-discipline, meta-discipline, ssot, +1 | 7 |
| `DESIGN_SPECS/doc-disciplines/module-scoped-claude-md-pattern.md` | 2-draft | doc-discipline, framework-discipline, context-aware-loading | 2 |
| `DESIGN_SPECS/doc-disciplines/toolchain-semantic-versioning.md` | 2-draft | doc-discipline, dev-plane, versioning, +1 | 0 |

## meta-discipline (32 specs)

| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| `DESIGN_SPECS/meta-disciplines/adversarial-pessimistic-simulation-discipline.md` | 3-first-canonical | meta-discipline, backtest, paper-mode, +3 | 0 |
| `DESIGN_SPECS/meta-disciplines/audit-driven-sub-sprint-trajectory-verification.md` | 3-first-canonical | audit-methodology, sub-sprint-discipline, plan-trajectory-verification, +2 | 0 |
| `DESIGN_SPECS/meta-disciplines/backtest-paper-live-convergence-discipline.md` | 3-first-canonical | meta-discipline, strategy-lifecycle, backtest-to-live, +1 | 0 |
| `DESIGN_SPECS/meta-disciplines/backwards-compat-not-default-concern.md` | 3-first-canonical | meta-discipline, backwards-compat, breaking-changes, +2 | 0 |
| `DESIGN_SPECS/meta-disciplines/body-content-enumeration-at-plan-time-discipline.md` | 3-first-canonical | meta-discipline, plan-template, framework-discipline, +1 | 0 |
| `DESIGN_SPECS/meta-disciplines/calibration-corpus-non-vacuity-discipline.md` | 2-draft | audit-methodology, verification, structural-enforcement, +2 | 3 |
| `DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md` | 3-first-canonical | meta-discipline, framework-discipline, pattern-codification, +2 | 5 |
| `DESIGN_SPECS/meta-disciplines/dead-code-and-identifier-retirement-discipline.md` | 5-claude-md | meta-discipline, structural-fix, framework-discipline, +1 | 4 |
| `DESIGN_SPECS/meta-disciplines/definition-of-done-and-armed-scout-verification.md` | 3-first-canonical | audit-methodology, meta-discipline, session-continuity, +2 | 0 |
| `DESIGN_SPECS/meta-disciplines/doc-frontmatter-convention.md` | 3-first-canonical | doc-discipline, meta-discipline, framework-discipline | 3 |
| `DESIGN_SPECS/meta-disciplines/doc-tag-vocabulary.md` | 3-first-canonical | doc-discipline, meta-discipline, framework-discipline | 3 |
| `DESIGN_SPECS/meta-disciplines/fix-toward-future-trajectory-not-static-state.md` | 2-draft | audit-methodology, design-discipline, future-oriented, +1 | 3 |
| `DESIGN_SPECS/meta-disciplines/gui-deprecation-decision-rationale.md` | 3-first-canonical | meta-discipline, gui-deprecation, power-user-design, +1 | 0 |
| `DESIGN_SPECS/meta-disciplines/handoff-active-state-machine.md` | 3-first-canonical | handoff, workflow, doc-discipline, +3 | 3 |
| `DESIGN_SPECS/meta-disciplines/headless-engine-viewer-split-pattern.md` | 3-first-canonical | meta-discipline, headless-service, viewer-split, +2 | 0 |
| `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` | 3-first-canonical | meta-discipline, audit-methodology, framework-discipline | 7 |
| `DESIGN_SPECS/meta-disciplines/iteration-spiral-signals-audit-meta-gap.md` | 3-first-canonical | audit-methodology, meta-discipline, iteration-spiral, +1 | 0 |
| `DESIGN_SPECS/meta-disciplines/mechanical-verification-of-derived-code-facts.md` | 3-first-canonical | doc-discipline, data-oriented-design, audit-methodology, +2 | 0 |
| `DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md` | 3-first-canonical | meta-discipline, anti-pattern-index, audit-methodology, +3 | 0 |
| `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md` | 5-claude-md | meta-discipline, pattern-codification, doc-discipline, +1 | 5 |
| `DESIGN_SPECS/meta-disciplines/plan-decomposition-and-future-aware-agent-arming.md` | 2-draft | audit-methodology, plan-decomposition, future-aware, +3 | 0 |
| `DESIGN_SPECS/meta-disciplines/plan-hierarchy-and-sub-master-decomposition.md` | 2-draft | planning, plan-hierarchy, sub-master, +3 | 0 |
| `DESIGN_SPECS/meta-disciplines/public-private-boundary-and-ecosystem-discipline.md` | 3-first-canonical | privacy-boundary, ecosystem, workspace, +2 | 0 |
| `DESIGN_SPECS/meta-disciplines/representation-migration-completeness.md` | 3-first-canonical | capital-safety, ssot, structural-fix, +2 | 0 |
| `DESIGN_SPECS/meta-disciplines/session-decision-log-discipline.md` | 3-first-canonical | meta-discipline, doc-discipline, plan-template, +1 | 0 |
| `DESIGN_SPECS/meta-disciplines/single-source-of-truth-discipline.md` | 3-first-canonical | meta-discipline, ssot, refactor-discipline, +1 | 3 |
| `DESIGN_SPECS/meta-disciplines/sister-cohort-amendment-completeness-discipline.md` | 3-first-canonical | meta-discipline, framework-discipline, doc-discipline, +2 | 0 |
| `DESIGN_SPECS/meta-disciplines/skill-knowledge-consultation-and-auto-routing.md` | 2-draft | meta-discipline, framework-discipline, doc-discipline, +1 | 0 |
| `DESIGN_SPECS/meta-disciplines/struct-change-cascade-impact-tooling.md` | 2-draft | data-oriented-design, ci-tooling, static-analysis, +4 | 2 |
| `DESIGN_SPECS/meta-disciplines/structural-enforcement-when-memory-insufficient.md` | 3-first-canonical | meta-discipline, framework-discipline, structural-fix, +1 | 0 |
| `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md` | 5-claude-md | meta-discipline, structural-fix, pattern-codification, +1 | 4 |
| `DESIGN_SPECS/meta-disciplines/train-serve-execution-layer-parity.md` | 3-first-canonical | audit-methodology, meta-discipline, structural-fix | 0 |

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
