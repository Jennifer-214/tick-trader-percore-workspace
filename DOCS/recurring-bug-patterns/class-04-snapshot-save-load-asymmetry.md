---
type: ledger-template
class_id: 4
title: Snapshot save/load asymmetry
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 4 — Snapshot save/load asymmetry

**Surface:** boot (snapshot serialization on shutdown + load on startup).

**Symptom:** Per-core stats reset on engine restart even though the
file exists and the user expected continuity. Stats panel shows
zero W/L until the next post-restart trade.

**Root cause:** Field added to `CoreContext` in vN.M after the
snapshot save/load was authored. Save was updated, load was forgotten
(or vice versa). The save-only fields silently get truncated on next
load; the load-only fields read garbage from disk past the saved
extent.

**Detection:**
```bash
# Save-side fields
grep -oE "fwrite\(&ctx\.[a-z_]+" ShardedSnapshotPersist.hpp | sort -u
# Load-side fields
grep -oE "fread\(&s\.[a-z_]+" ShardedSnapshotPersist.hpp | sort -u
# Any imbalance is suspect
```

**Known instances:**
- v5.4.3 (this commit) — `core_gross_wins` and `core_gross_losses`
  added in v4.7.25 but never persisted. After restart, Stats panel's
  avg_win / avg_loss / profit_factor / expectancy all read zero
  until next trade.
- v5.4.3 — `idle_cycles` (death-spiral counter) not persisted.

**Prevention:**
- Bump `SHARDED_SNAPSHOT_VERSION` whenever a CoreContext field is
  added that needs persistence.
- Readiness check: when a plan adds a `CoreContext<F>` field, require
  explicit answer to "should this be persisted?" — yes/no/deferred,
  no implicit "no answer."
