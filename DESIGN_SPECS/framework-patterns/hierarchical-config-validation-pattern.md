---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.2
canonical_applications:
  - v5.15.5.F.4d.1.E.2 (cross-file cfg validation at boot)
sister_specs:
  - framework-patterns/hierarchical-config-with-per-node-folders.md (parent; layout)
  - framework-patterns/cluster-node-hierarchy-filesystem-layout-pattern.md (sister; filesystem)
  - framework-patterns/runtime-mutable-vs-boot-time-config-pattern.md (sister; mutability)
tags: [framework-discipline, config-validation, boot-time-check, cross-reference]
surface: [config-parser, boot-sequence]
applies_at_skills: [/precoding-audit-gate, /readiness]
---

# Hierarchical config validation pattern

**Pattern intent:** Boot-time cross-file validation of hierarchical config. Every per-node references valid cluster + sub-account; every credential parseable; every symbol valid for cluster; every strategy.cfg loadable. Engine refuses to start on validation failure with explicit error.

## Pattern

### Validation order

```cpp
int Cfg_ValidateAll(EngineState<F>& state) {
    int errors = 0;

    // 1. Validate engine.cfg integrity
    errors += Cfg_ValidateEngineLevel(state.cfg.engine);

    // 2. Per enabled cluster: validate cluster.cfg
    for each enabled cluster:
        errors += Cfg_ValidateClusterLevel(cluster);

    // 3. Per cluster's sub-account: validate credentials cfg
    for each cluster:
        for each subaccount:
            errors += Cfg_ValidateSubAccountCredentials(cluster, subaccount);

    // 4. Per cluster's node: validate node cfgs (core + strategy + ml + observability)
    for each cluster:
        for each node:
            errors += Cfg_ValidateNodeLevel(cluster, node);

    // 5. CROSS-FILE: every node references valid cluster
    for each node:
        if (!IsClusterEnabled(node.binding.cluster_id)) {
            LOG_ERROR("Node references disabled cluster %u", node.binding.cluster_id);
            errors++;
        }
        // Verify subaccount_id < cluster.subaccount_count
        // Verify symbol valid for cluster's exchange
        // Verify strategy.cfg.strategy_name is a registered strategy

    if (errors > 0) {
        LOG_FATAL("Config validation failed with %d errors; refusing to start", errors);
        return -1;
    }
    return 0;
}
```

### Atomic validate-then-apply for hot-reload

```cpp
int Cfg_HotReload(EngineState<F>& state) {
    // Parse new configs into TEMPORARY state
    EngineConfig new_cfg;
    if (Cfg_ParseAll(&new_cfg) != 0) return -1;

    // Validate entire new state BEFORE applying
    if (Cfg_ValidateAll(new_cfg) != 0) {
        LOG_ERROR("Hot-reload validation failed; reverting");
        return -1;
    }

    // ATOMIC SWAP: apply new cfg
    // ... via slow→hot seqlock per runtime-mutable fields ...
    // ... refuse runtime change for boot-time fields ...

    return 0;
}
```

## Cross-references

- Parent: `framework-patterns/hierarchical-config-with-per-node-folders.md`
- First application: `plans/v5.15.5.F.4d.1.E.2-headless-configs-docs.md`
