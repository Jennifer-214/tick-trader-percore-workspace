---
type: framework-pattern
stage: 2-draft
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.1 (cfg field) + v5.15.5.F.4d.1.E.2 (full integration)
sister_specs:
  - framework-patterns/crash-recovery-via-mmap-state-pattern.md (parent; recovery substrate)
tags: [framework-discipline, crash-recovery, operator-policy]
surface: [boot-sequence, recovery]
---

# Crash recovery action policy pattern (Stage 2 DRAFT)

**Pattern intent:** Operator-configurable policy for engine behavior on crash-restart. `on_crash_restart_action = resume | cancel-all | flatten`. Per D-47.

## Three policies

```
# configs/engine.cfg:
on_crash_restart_action = resume   # default; trust mmap state; reconcile; continue
# OR
on_crash_restart_action = cancel-all   # cancel all open orders on restart; preserve positions
# OR
on_crash_restart_action = flatten   # force-close all positions on restart; clean slate
```

### resume (default)

```cpp
case CRASH_ACTION_RESUME:
    // Read mmap state; reconcile per-node against exchange; continue
    Engine_ParallelReconcileAllNodes(state);
    state.crash_recovery_in_progress = false;
    break;
```

Best for: stable infrastructure; minor crashes (segfault; OOM); operator wants no-data-loss.

### cancel-all (cautious)

```cpp
case CRASH_ACTION_CANCEL_ALL:
    // Cancel all open orders on each sub-account
    for each cluster, each subaccount:
        tt::cancel_all_orders<AdapterT>(adapter, subaccount_id);
    // Positions preserved (Binance still has them); engine knows about them
    Engine_ParallelReconcileAllNodes(state);
    break;
```

Best for: ambiguous crash cause; want clean order book; positions still wanted.

### flatten (most cautious)

```cpp
case CRASH_ACTION_FLATTEN:
    // Force-close all positions (market orders to flatten)
    for each cluster, each node:
        if (node.has_open_position) {
            ForceClosePosition(node);
        }
    Engine_ParallelReconcileAllNodes(state);
    break;
```

Best for: suspected data corruption; operator wants clean slate; high-stakes safety.

## Stage progression

- **Stage 2 DRAFT** (this stage; .E.1 cfg field; .E.2 implementation)
- **Stage 3 first canonical** at `.E.2` when fully integrated
- **Stage 4 cohort** when 2nd application

## Cross-references

- Parent: `framework-patterns/crash-recovery-via-mmap-state-pattern.md`
- Decision: D-47
