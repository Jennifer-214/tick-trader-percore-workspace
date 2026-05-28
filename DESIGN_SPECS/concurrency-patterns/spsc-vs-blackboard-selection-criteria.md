---
type: concurrency-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.2
canonical_applications:
  - v5.15.5.F.4d.1.E.2 (codification of pattern-selection criteria; already-adopted-in-codebase pattern)
sister_specs:
  - concurrency-patterns/concurrency-model-summary.md (parent; full model)
tags: [concurrency, spsc-rings, seqlock-blackboard, pattern-selection]
surface: [concurrency, inter-thread-communication]
applies_at_skills: [/precoding-audit-gate, /dod-audit]
---

# SPSC vs blackboard pattern selection criteria

**Pattern intent:** Codify when to use SPSC (must-not-miss event streams) vs seqlock/atomic blackboard (latest-value-wins state visibility). Per F-13 (operator cited Concept 3 "Asymmetric Blackboard Architecture" 2026-05-28); pattern already applied in codebase; this spec codifies the SELECTION criteria.

## Problem statement

Two distinct inter-thread communication patterns serve different needs:

| Pattern | Semantic | Example use |
|---|---|---|
| SPSC ring | Must-not-miss event log | Trade events; fills; submits |
| Seqlock blackboard | Latest-value-wins state | Cfg parameters; account state; kill flags |

Using the wrong pattern degrades correctness OR wastes resources. Selection criteria must be explicit.

## Pattern selection rubric

### Use SPSC ring when:

✅ Each event represents a UNIQUE state transition that consumer must process
✅ Missing an event would lose information (e.g., a fill happened but engine didn't see)
✅ Order of events matters (must process in arrival order)
✅ Producer rate is bounded + consumer rate is sufficient to drain

**Examples in our codebase:**
- Per-node TradeEvent hot→slow ring (each strategy decision MUST be processed)
- OMS submit_queue (each submit MUST reach exchange)
- Fill ring (each fill MUST update accounting)
- Audit log queue (each event MUST be persisted)

### Use seqlock/atomic blackboard when:

✅ Latest value matters more than complete history
✅ Readers want CURRENT state (not log of changes)
✅ Multiple readers OK (multi-version concurrent reads)
✅ Producer overrides; older values implicitly discarded

**Examples in our codebase:**
- Slow→hot cfg parameters (hot path reads latest cfg; intermediate cfg states irrelevant)
- Aggregator → nodes kill flags (latest kill state; not log of state transitions)
- Per-node → aggregator state publication (latest per-node state; aggregator reads via seqlock)
- TUISnapshot publication (latest snapshot for GUI/TUI)

### Decision flow

```
Is missing an event a correctness bug?
├── YES → SPSC ring
└── NO → Is latest-value sufficient?
        ├── YES → Seqlock blackboard
        └── NO (need history) → SPSC ring + persistent log (e.g., audit log writer thread)
```

## Pattern-mismatch anti-patterns

### Using blackboard for event log (WRONG)

```cpp
// WRONG: trade events as blackboard
struct TradeEventBlackboard {
    std::atomic<TradeEvent> latest_event;  // overwrite on each fill
};
// PROBLEM: fast successive fills overwrite each other; older fills LOST
```

### Using SPSC for state visibility (WASTEFUL)

```cpp
// WRONG: kill flag as SPSC ring
SPSCRing<bool, 1024> kill_flag_ring;
// PROBLEM: consumer must drain stale events; only LATEST matters
```

### Hybrid pattern (correct for streaming-state)

```cpp
// CORRECT: aggregator updates running aggregate via blackboard;
// audit log writer thread persists via SPSC ring (event log) for forensic
struct AggregatorState {
    std::atomic<FPN_atoms> running_pnl;     // blackboard
};

struct AuditLogWriter {
    SPSCRing<AuditEvent, 4096> queue;       // event log
};
```

## Memory ordering discipline

For SPSC: producer release; consumer acquire. Standard lock-free queue ordering.

For blackboard:
- Seqlock writers: fetch_add(1) before update (odd seqlock = in-progress); fetch_add(1) after (even = consistent)
- Atomic blackboard: simple atomic store/load with release/acquire semantics

## Cache line discipline

SPSC: producer + consumer fields on SEPARATE cache lines (alignas(64) per H6) to prevent false sharing.

Blackboard: writer + readers can share cache line (lock-free read; cache-line shared-read in MESI; writes invalidate but rare).

## Stage progression criteria

- **Stage 3 first canonical** (`.E.2`): codified at documentation push (already-adopted-in-codebase pattern)
- **Stage 4 cohort** (when 2nd application of selection criteria surfaces): pattern proven
- **Stage 5 CLAUDE.md** (3rd application): promoted

## Anti-patterns avoided

- **Force-fit blackboard onto event streams** — events LOST (Class 18 risk: missing data flow)
- **Force-fit SPSC onto state visibility** — overhead; consumer drains stale events
- **Lock-based pattern instead** — H3 violation

## Cross-references

- Parent: `concurrency-patterns/concurrency-model-summary.md`
- Source: F-13 + D-56 (operator-cited Concept 3 from research 2026-05-28)
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.2-headless-configs-docs.md`
