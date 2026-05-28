---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.2
canonical_applications:
  - v5.15.5.F.4d.1.E.2 (per-node config file parser refactor)
sister_specs:
  - framework-patterns/cluster-node-hierarchy-filesystem-layout-pattern.md (filesystem layout)
  - framework-patterns/hierarchical-config-validation-pattern.md (validation discipline)
  - framework-patterns/universal-cfg-field-registry-pattern.md (existing; per-node fields auto-flow)
  - framework-patterns/runtime-mutable-vs-boot-time-config-pattern.md (mutability axis)
tags: [framework-discipline, hierarchical-config, per-node-folders, cfg-parser]
surface: [config-parser, filesystem]
applies_at_skills: [/precoding-audit-gate, /readiness]
---

# Hierarchical config with per-node folders

**Pattern intent:** Engine config split into hierarchical filesystem layout: deployment-level engine.cfg → per-cluster cluster.cfg → per-node `core.cfg + strategy.cfg + ml.cfg + observability.cfg`. Each per-node has dedicated folder. No template inheritance (each per-node fully self-contained per operator clarification 2026-05-28).

## Problem statement

Per `cluster-node-hierarchy-filesystem-layout-pattern.md` (sister spec): monolithic engine.cfg doesn't scale. But how does the parser handle the hierarchical layout?

This spec codifies the PARSER side. Sister covers the filesystem layout.

## Pattern description

### Loading order

Engine boot performs hierarchical loading:

```cpp
void Engine_LoadConfigs(EngineState<F>& state) {
    // 1. Deployment-level (global)
    ParseCfg("configs/engine.cfg", &state.cfg.engine);

    // 2. Per-cluster (per enabled exchange row)
    for (uint32_t c = 0; c < NUM_EXCHANGES; ++c) {
        if (!IsClusterEnabled(c)) continue;
        char path[512];
        snprintf(path, sizeof(path), "configs/clusters/%s/cluster.cfg", EXCHANGE_NAME(c));
        ParseCfg(path, &state.clusters[c].cfg);

        // 3. Per-sub-account credentials (sparse; per FOREACH_SUBACCOUNT row)
        // Handled by SubAccountCredentials loader

        // 4. Per-node configs
        for (uint32_t n = 0; n < state.clusters[c].node_count; ++n) {
            char node_dir[512];
            snprintf(node_dir, sizeof(node_dir),
                     "configs/clusters/%s/nodes/node_%u",
                     EXCHANGE_NAME(c), n);

            ParseCfg_NodeFolder(node_dir, &state.nodes[n].cfg);
        }
    }

    // 5. Cross-file validation
    ValidateConfigCrossReferences(state);
}

// Parse all .cfg files in a node folder
int ParseCfg_NodeFolder(const char* node_dir, NodeConfig<F>* out) {
    char path[1024];

    snprintf(path, sizeof(path), "%s/core.cfg", node_dir);
    ParseCfg(path, &out->core);

    snprintf(path, sizeof(path), "%s/strategy.cfg", node_dir);
    ParseCfg(path, &out->strategy);

    snprintf(path, sizeof(path), "%s/ml.cfg", node_dir);
    if (FileExists(path)) ParseCfg(path, &out->ml);

    snprintf(path, sizeof(path), "%s/observability.cfg", node_dir);
    if (FileExists(path)) ParseCfg(path, &out->observability);

    // notes.md is operator-only; not parsed by engine
    return 0;
}
```

### No template inheritance (per operator clarification)

Original design considered strategy templates (e.g., `strategies/momentum.template.cfg`) with per-core overrides. Operator clarified: each per-node fully self-contained; no inheritance.

**Rationale:** templates introduce magic resolution; per-node deviation from "template default" surprising. Self-contained per-node is operator-clearer.

**Trade-off accepted:** 4 nodes with similar configs duplicate values. Mitigated by `cp -r` operator workflow.

### Hot-reload semantics

SIGUSR1 → engine reloads ALL per-node configs:
1. New configs parsed into NEW cfg struct (NOT yet applied)
2. Cross-reference validation against ENTIRE new state
3. If validation fails: ROLLBACK; old configs remain; log error
4. If validation succeeds: ATOMIC swap to new configs
5. Runtime-mutable parameters (per `runtime-mutable-vs-boot-time-config-pattern.md`) update via slow→hot seqlock
6. Boot-time-only parameters (e.g., exchange binding): refuse hot-reload; operator must restart

Per-node SIGUSR1-equivalent via fox-cli:

```bash
# Reload one node's configs
fox-cli reload-node-config binance/node_0

# Reload all nodes in cluster
fox-cli reload-cluster-config binance

# Engine validates atomically; reports per-node result
```

### Field-level cfg discipline

Each cfg file's fields registered in FOREACH_PER_NODE_CFG_FIELD (existing X-macro registry; per `universal-cfg-field-registry-pattern.md`).

Adding new per-node field:
1. Add row to FOREACH_PER_NODE_CFG_FIELD
2. Field auto-parses from cfg file
3. GUI/TUI render auto-flows
4. Tooltip auto-generated
5. Per-cluster override semantics auto-flow

No manual parser code per new field.

## Stage progression criteria

- **Stage 3 first canonical** (`.E.2`): per-node folder parser implemented
- **Stage 4 cohort** (when 2nd application: future cfg refactor): pattern proven
- **Stage 5 CLAUDE.md** (3rd application): promoted

## Anti-patterns avoided

- **Monolithic engine.cfg** — doesn't scale at multi-exchange + multi-sub-account
- **Template inheritance** — magic resolution; per-node deviation surprising
- **Manual parser per cfg field** — FOREACH_PER_NODE_CFG_FIELD canonical
- **No atomic hot-reload** — partial config update creates inconsistent state

## Cross-references

- Sister: `framework-patterns/cluster-node-hierarchy-filesystem-layout-pattern.md`
- Sister: `framework-patterns/hierarchical-config-validation-pattern.md`
- Sister: `framework-patterns/universal-cfg-field-registry-pattern.md` (existing)
- Sister: `framework-patterns/runtime-mutable-vs-boot-time-config-pattern.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.2-headless-configs-docs.md`
