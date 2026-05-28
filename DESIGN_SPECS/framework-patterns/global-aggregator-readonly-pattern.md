---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.1
canonical_applications:
  - v5.15.5.F.4d.1.E.1 (first canonical at .E.1)
sister_specs:
  - framework-patterns/event-sourced-aggregator-o1-pattern.md (event-driven update; sister at refinement layer)
  - framework-patterns/kill-switch-hierarchical-pattern.md (consumer; reads aggregate; sets flags)
  - meta-disciplines/single-source-of-truth-discipline.md (single-writer principle)
  - meta-disciplines/structural-enforcement-when-memory-insufficient.md (M7; structural enforcement)
tags: [framework-discipline, aggregator, read-only, seqlock, single-writer]
surface: [aggregator, account-state, kill-switch]
applies_at_skills: [/precoding-audit-gate, /dod-audit, /parity-check]
---

# Global aggregator read-only pattern

**Pattern intent:** Single deployment-wide aggregator thread reads all per-node + per-cluster state via seqlock (lock-free; multi-version). Computes hierarchical totals. Sets hierarchical kill flags. NEVER writes per-node state. Single-writer principle preserved.

## Problem statement

Multi-cluster + multi-node engine needs:
- Aggregate totals (deployment-wide P&L; per-cluster P&L)
- Hierarchical kill-switch evaluation (per-node + per-cluster + global)
- Cross-axis aggregation (e.g., per-strategy P&L across all clusters)

Without dedicated aggregator: GUI/TUI scrambles to compute totals; multiple consumers compute differently; correctness issues.

With aggregator: single canonical computation; lock-free reads everywhere else.

## Pattern description

```cpp
struct alignas(64) AggregatorState {
    // === GLOBAL TOTALS (computed each cycle OR event-driven per .E.1 D-54) ===
    alignas(64) struct {
        FPN<F> total_realized_pnl;
        FPN<F> total_open_notional;
        FPN<F> total_drawdown_current;
        uint64_t total_fills;
        std::atomic<uint64_t> cached_version;     // monotonic
    } global;

    // === PER-CLUSTER TOTALS ===
    alignas(64) struct ClusterTotals {
        FPN<F> realized_pnl;
        FPN<F> open_notional;
        FPN<F> drawdown_current;
        uint64_t fills;
    };
    ClusterTotals per_cluster[NUM_EXCHANGES];

    // === KILL FLAGS (aggregator OWNS write; nodes mirror via atomic read) ===
    alignas(64) std::atomic<uint8_t> global_kill_flag;
    std::atomic<uint8_t> per_cluster_kill[NUM_EXCHANGES];

    // === THRESHOLDS (operator-configurable; cfg-driven) ===
    FPN<F> global_kill_drawdown_threshold;
    FPN<F> per_cluster_kill_drawdown_threshold[NUM_EXCHANGES];
};

// Aggregator cycle (periodic; cfg-driven cadence default 100ms)
void Aggregator_Cycle(EngineState<F>& state) {
    // 1. Read all node state via seqlock (lock-free; multi-version)
    // 2. Compute global + per-cluster totals
    // 3. Compare to thresholds; set kill flags
    // 4. Mirror kill flags to per-node atomic state
}
```

## Single-writer principle

- **Aggregator OWNS WRITE** of: global_kill_flag, per_cluster_kill[], global totals, per-cluster totals
- **Aggregator READS ONLY** from: per-node state (via seqlock; lock-free)
- **Per-nodes OWN WRITE** of: their own per-node state (NodeState.slow_account)
- **Per-nodes READ ONLY** from: kill flags (mirror via atomic read at slow-path entry)

No multi-writer surface; lock-free reads everywhere; correctness by design.

## Seqlock read pattern

```cpp
// Per-node state publish (writer):
node.slow_account.account_state_seqlock.fetch_add(1, std::memory_order_acq_rel);  // odd = in progress
// Update fields...
node.slow_account.realized_pnl = ...;
node.slow_account.open_notional = ...;
node.slow_account.account_state_seqlock.fetch_add(1, std::memory_order_release);  // even = consistent

// Aggregator read (reader; lock-free):
FPN<F> realized, notional;
uint64_t seq1, seq2;
do {
    seq1 = node.slow_account.account_state_seqlock.load(std::memory_order_acquire);
    realized = node.slow_account.realized_pnl;
    notional = node.slow_account.open_notional;
    seq2 = node.slow_account.account_state_seqlock.load(std::memory_order_acquire);
} while (seq1 != seq2 || (seq1 & 1) != 0);  // retry if torn
```

Per `data-disciplines/cache-line-discipline.md` + H6 (cross-thread fields alignas(64)).

## Hierarchical kill switch

Per `kill-switch-hierarchical-pattern.md`:

```cpp
// Per-node slow-path entry: check 3 kill flag layers (cheap; atomic reads)
void NodeSlowPath_Cycle(NodeState<F>& node) {
    if (node.kill_flags.global_kill_mirror.load(std::memory_order_acquire) ||
        node.kill_flags.per_cluster_kill_mirror.load(std::memory_order_acquire) ||
        node.kill_flags.per_node_kill.load(std::memory_order_acquire)) {
        NodeSlowPath_HandleKilled(node);
        return;
    }
    // ... normal slow-path cycle
}
```

Aggregator's atomic stores → per-node atomic reads → kill propagation in single seqlock cycle (~100ms; tunable via D-54 event-driven for sub-fill latency).

## Read-only aggregator does NOT initiate trading actions

Aggregator computes + observes + sets kill flags. Aggregator does NOT:
- Open positions
- Submit orders
- Cancel orders
- Modify per-node state

Trading actions remain per-node responsibility. Aggregator is OBSERVATIONAL.

This preserves single-writer principle + clear separation of concerns.

## Stage progression criteria

- **Stage 3 first canonical** (`.E.1`): aggregator implemented; per-cluster + global totals; hierarchical kill flags
- **Stage 4 cohort** (when 2nd application surfaces; e.g., per-strategy aggregation): pattern proven
- **Stage 5 CLAUDE.md** (3rd application + discipline matures): promoted

## Anti-patterns avoided

- **Multi-writer kill flag** — single-writer principle violation
- **Cross-node iteration in trading-flow code** — Class 26 surface
- **Aggregator triggering trades** — separation-of-concerns violation
- **Per-cluster aggregator** — extra hop without benefit (decision D-34)

## Cross-references

- Sister: `framework-patterns/event-sourced-aggregator-o1-pattern.md` (event-driven update sister at refinement)
- Sister: `framework-patterns/kill-switch-hierarchical-pattern.md`
- Parent: `meta-disciplines/single-source-of-truth-discipline.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.1-foundation.md` § Global aggregator + hierarchical kill switches
