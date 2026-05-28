---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.2
canonical_applications:
  - v5.15.5.F.4d.1.E.2 (mmap state file + reconcile-on-restart + on_crash_restart_action)
sister_specs:
  - framework-patterns/crash-recovery-action-policy-pattern.md (sister; resume/cancel-all/flatten)
  - framework-patterns/native-tui-via-mmap-readonly-pattern.md (sister; same mmap region)
  - meta-disciplines/headless-engine-viewer-split-pattern.md (parent; mmap is state-publication boundary)
tags: [framework-discipline, crash-recovery, mmap, state-persistence, reconciliation]
surface: [state-persistence, boot-sequence, recovery]
applies_at_skills: [/precoding-audit-gate]
---

# Crash recovery via mmap state pattern

**Pattern intent:** Engine state persisted to mmap'd file. Survives crash (kernel-flushed). Engine restart reads state file; reconciles per-node against exchange truth; resumes per `on_crash_restart_action` policy.

## Problem statement

Engine in production runs 24/7. Crashes happen (kernel issue; OOM; segfault; etc.). After crash:
- Open positions on Binance: still there (Binance doesn't care engine crashed)
- Open orders on Binance: still there (potentially)
- Engine state: lost (in-memory)
- mmap state file: SURVIVES (kernel page cache flushed to disk)

Without state file: engine starts blank; doesn't know about open positions; could open additional positions on top (over-leveraging).

With mmap state file: engine reads pre-crash state; reconciles against Binance truth; resumes safely.

## Pattern description

### State file path

```
/var/lib/fox/state/state.mmap          (production)
~/.local/share/fox/state/state.mmap    (dev)
```

cfg-overridable via `--state-dir` engine arg.

### State layout

Mirrors `StatePublishRegion` from `native-tui-via-mmap-readonly-pattern.md` + adds persistence-specific fields:

```cpp
struct alignas(64) PersistentEngineState {
    struct Header {
        uint32_t protocol_version;
        uint32_t engine_software_version;
        uint64_t last_clean_shutdown_us;     // 0 if not clean shutdown
        std::atomic<uint64_t> writer_seqlock;
        char engine_id[32];                   // unique per engine instance
    } header;

    // Per-cluster state (subset; recoverable)
    ClusterStateView clusters[NUM_EXCHANGES];

    // Per-node state (full; for resumption)
    struct NodePersistState {
        char cluster_name[32];
        uint32_t subaccount_id;
        char symbol[16];
        NodeMode mode;
        FPN<F> realized_pnl;
        FPN<F> open_notional;
        FPN<F> capital_allocated;
        // Positions (for reconcile)
        uint8_t has_open_position;
        FPN<F> position_qty;
        FPN<F> position_entry_price;
        char client_order_id_prefix[16];
    };
    NodePersistState nodes[MAX_NODES];

    // Audit-event ring (recent N events; for post-crash forensic)
    AuditEventCompact audit_ring[AUDIT_EVENT_RING_SIZE];
};
```

### Write cadence

Per `state_flush_mode` cfg field (per D-18 6-mode enum):
- `max`: every state change flushed
- `more`: every state change flushed batched per 1ms
- `standard`: per-fill flushed; per-tick aggregates per 100ms
- `relaxed`: per-fill flushed; per-tick per 1s
- `minimal`: per-fill only; periodic checkpoint per 10s
- `none`: no persistence (backtest mode)

Atomic seqlock writes; readers (fox-tui; etc.) see consistent state.

### Boot-time restoration sequence

```cpp
int Engine_BootRestoreFromMmap(EngineState<F>& state) {
    int fd = open(state_path, O_RDWR);
    if (fd < 0) {
        LOG_INFO("No state file; starting blank");
        return 0;  // OK: first boot
    }

    PersistentEngineState* persist = mmap(...);

    // Validate header
    if (persist->header.protocol_version != CURRENT_PROTOCOL_VERSION) {
        LOG_ERROR("State file protocol version %u; engine expects %u",
                  persist->header.protocol_version, CURRENT_PROTOCOL_VERSION);
        // Backwards-compat: refuse per D-9
        return -EPROTONOSUPPORT;
    }

    // Detect clean vs crash shutdown
    if (persist->header.last_clean_shutdown_us == 0) {
        LOG_WARN("Last shutdown was unclean (crash); recovery mode");
        state.crash_recovery_in_progress = true;
    }

    // Restore per-node state
    for (uint32_t n = 0; n < state.node_count; ++n) {
        state.nodes[n].slow_account.realized_pnl = persist->nodes[n].realized_pnl;
        state.nodes[n].slow_account.open_notional = persist->nodes[n].open_notional;
        // ... etc
    }

    // Parallel reconcile against Binance truth
    Engine_ParallelReconcileAllNodes(state);

    // Apply on_crash_restart_action policy
    if (state.crash_recovery_in_progress) {
        switch (state.cfg.engine.on_crash_restart_action) {
            case CRASH_ACTION_RESUME:
                LOG_INFO("Crash recovery: resume mode; positions preserved");
                break;
            case CRASH_ACTION_CANCEL_ALL:
                LOG_INFO("Crash recovery: cancel-all mode; cancelling open orders");
                Engine_CancelAllOpenOrders(state);
                break;
            case CRASH_ACTION_FLATTEN:
                LOG_INFO("Crash recovery: flatten mode; closing all positions");
                Engine_FlattenAllPositions(state);
                break;
        }
    }

    munmap(persist, ...);
    close(fd);
    return 0;
}
```

### Reconciliation against exchange truth

Engine queries Binance for actual positions; compares to mmap state; logs discrepancy; trusts Binance.

```cpp
void Engine_ReconcileNode(NodeState<F>& node) {
    PositionList<F> exchange_positions;
    tt::query_positions<BinanceAdapter<F>>(adapter, &exchange_positions);

    if (!PositionEqual(node.slow_account.position, exchange_positions[node.binding.subaccount_id])) {
        LOG_WARN("Node %u state mismatch: engine=%s, exchange=%s",
                 node.binding.subaccount_id, ...);
        // Trust exchange truth
        node.slow_account.position = exchange_positions[node.binding.subaccount_id];
        // Emit alert
        AuditLog_Append(reconcile_discrepancy_event);
    }
}
```

### Backup / restore workflow

```bash
# Operator-triggered state snapshot
fox-cli backup-state --output snapshot-2026-05-28.bin

# Restore on new server (one-time migration; data preserved)
fox-engine --restore snapshot-2026-05-28.bin --state-dir /var/lib/fox/state/
```

## Stage progression criteria

- **Stage 3 first canonical** (`.E.2`): crash recovery via mmap implemented
- **Stage 4 cohort** (when 2nd application surfaces): pattern proven
- **Stage 5 CLAUDE.md** (3rd application): promoted

## Anti-patterns avoided

- **Engine starts blank after crash** — over-leveraging risk
- **No reconciliation against exchange truth** — drift accumulates
- **Single recovery action** — operator should choose resume/cancel/flatten policy

## Cross-references

- Sister: `framework-patterns/crash-recovery-action-policy-pattern.md`
- Sister: `framework-patterns/native-tui-via-mmap-readonly-pattern.md` (same mmap region)
- Parent: `meta-disciplines/headless-engine-viewer-split-pattern.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.2-headless-configs-docs.md`
