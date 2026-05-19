---
type: ledger-template
class_id: 6
title: OMS counter persistence
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 6 — OMS counter persistence

**Surface:** boot (snapshot save/load of OMS state — counters must round-trip).

**Symptom:** session-cumulative counters on the OMS (fee totals,
maker/taker breakdown, fill counts) reset to zero on engine restart
even though `balance` and `realized_pnl` continue from the snapshot.
After restart, the GUI's fees tooltip / session forensics drop the
session totals and the user can't reconcile cumulative spend.

**Root cause:** `ShardedSnapshotPersist.hpp` save/load was authored
for the financial-state primitives (balance, realized_pnl, peak,
kill_switch_tripped) and never expanded as the OMS grew counter
fields. Maker/taker / fee-totals were added in Phase 8; never
propagated into the snapshot file.

**Detection:**
```bash
# Fields on OMS struct that look like cumulative counters
grep -E "uint(32|64)_t|FPN<F>" CoreFrameworks/OrderManager.hpp \
    | grep -iE "total|count|fee|fill" | head -20
# What's actually persisted
grep "fwrite(&state->oms->" CoreFrameworks/ShardedSnapshotPersist.hpp
# Diff: counters that exist but aren't written are candidates
```

**Known instances:**
- v5.4.4 — `total_fees`, `total_maker_fees`, `total_taker_fees`,
  `maker_fills_count`, `taker_fills_count` not persisted. Snapshot
  version bumped 5→6.

**Prevention:**
- Same as Class 4: bump SHARDED_SNAPSHOT_VERSION when adding any OMS
  counter that needs continuity, with a save/load symmetry check.
- Future refactor: snapshot save/load should iterate fields from a
  schema struct rather than open-coded fwrite/fread. A schema
  mismatch then becomes a static_assert at compile time.
