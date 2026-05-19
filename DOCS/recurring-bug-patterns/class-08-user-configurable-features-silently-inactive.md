---
type: ledger-template
class_id: 8
title: User-configurable features silently inactive in sharded
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-18
---

## Class 8 — User-configurable features silently inactive in sharded

**Surface:** live (cfg-flag → runtime decision-path consumption).

**Symptom:** user flips a cfg flag, expects behavior change, sees
none. TUI may even display "enabled" status. The cfg field is parsed,
stored, displayed — but the runtime decision path that should consume
it doesn't exist in the sharded code, only in the legacy
PortfolioController.

**Root cause:** the sharded port migrated the structural execution
path (slow-path → strategy → gate parameters → hot path) but did not
port every modulator / gating layer. Cost gating (CostModel) and vol
scaling (VolScaler) were two such layers — fully implemented in
legacy, fully orphaned in sharded.

**Detection:**
```bash
# For each cfg field that's marked "enabled" or has explicit gating
# semantics, check if it's read in the sharded path
for field in $(grep -oE "[a-z_]+_enabled" CoreFrameworks/ControllerConfig.hpp | sort -u); do
    legacy_reads=$(grep -c "config.$field\|cfg.$field" CoreFrameworks/PortfolioController.hpp 2>/dev/null)
    sharded_reads=$(grep -rh "config.$field\|cfg.$field" \
        CoreFrameworks/EngineSharded.hpp \
        CoreFrameworks/ControllerEventLoop.hpp \
        Strategies/ 2>/dev/null | wc -l)
    if [ $legacy_reads -gt 0 ] && [ $sharded_reads -eq 0 ]; then
        echo "ORPHAN: $field (legacy=$legacy_reads, sharded=0)"
    fi
done
```

**Known instances:**
- v5.4.4 (DOCUMENTED, NOT YET FIXED) —
  - `cost_gate_enabled`: legacy reads at PortfolioController.hpp:1751.
    Sharded zero reads. CostModel evaluates expected cost vs
    expected gain at entry; if `cost > k × gain`, vetoes the entry.
    Sharded skip means cost-aware entry filtering is dead.
  - `foxml_vol_scaling_enabled`: legacy reads at
    PortfolioController.hpp:1168, 1789. Sharded zero reads. Scales
    risk_pct by recent volatility (cuts size in high-vol regimes).
    Sharded skip means user's risk_pct is constant regardless of
    volatility.

**Prevention:**
- Readiness skill check: when a plan touches an `*_enabled` cfg
  field, require explicit "where is this consumed" answer for both
  legacy AND sharded paths. Block ship if sharded path is empty.
- Dust scan: extend Scan 9 (orphaned function detection) to also
  scan for orphaned cfg-enabled fields.
- Long-term fix: port CostModel + VolScaler integration into the
  sharded `Strategy_BuildParameters` dispatcher path. Tracked as a
  v5.5+ feature ship.
