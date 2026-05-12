# Cache Audit — <SurfaceName> — <ship-tag>

**Surface:** `<path/to/file.hpp>` `struct <SurfaceName>`
**Cadence:** hot path / slow path / OMS drainer / boot
**Ship:** v5.15.5.<X>
**Auditor:** Claude Code session 2026-MM-DD

## Pre-audit metrics

| Metric | Value |
|---|---|
| `sizeof(<SurfaceName>)` | XXX bytes |
| Cache lines spanned | XX (sizeof / 64) |
| Field count | XX |
| Embedded sub-structs | <list with sizes> |
| Cross-thread shared fields | <list> |
| Display-only fields | <list> |

## Field tier classification (Rule 4)

| Field | Bytes | Offset | Access | Tier |
|---|---|---|---|---|
| `field_a` | 8 | 0 | slow-path read every cycle | HOT |
| `field_b` | 24 | 8 | slow-path write per transition | WARM |
| `field_c` | 256 | 32 | display read only | COLD |
| ... | | | | |

Tiers: HOT (every cycle) / WARM (per N cycles or transitions) / COLD (init / display / rare)

## Per-rule findings

### Rule 1 — Display-only field extraction

| Field | Reason it's display-only | Proposed extraction location |
|---|---|---|
| ... | ... | ... |

### Rule 2 — Tight-pack candidates

| Field cluster | Current bytes / lines | Proposed bytes / lines |
|---|---|---|
| ... | ... | ... |

### Rule 3 — Cross-thread isolation

| Field | Writer | Reader | Current isolation | Proposed |
|---|---|---|---|---|
| ... | ... | ... | none / alignas(64) / explicit pad | alignas(64) + alignas(64) next |

### Rule 4 — Hot/Warm/Cold reorganization

```
struct alignas(64) <SurfaceName> {
    // === HOT cluster ===
    alignas(64) ...
    // === WARM cluster ===
    alignas(64) ...
    // === COLD cluster ===
    alignas(64) ...
};
```

### Rule 5 — Bit-pack boolean cohorts

| Original fields (bytes) | Proposed bitmap (bits) | MASK_* constants |
|---|---|---|
| ... | ... | ... |

### Rule 6 — AVX-512 sizing candidates

| Array | Current | AVX-512 fit? | Notes |
|---|---|---|---|
| ... | ... | yes / no | sizing to 1 ZMM register? scalar fallback OK? |

### Rule 7 — Per-cycle budget verification

Pre-audit slow-path cycle access:
- HOT lines: X
- WARM lines: Y (if transition)
- Total: Z lines

Target: ≤ 3-5 lines slow-path.

Post-audit access:
- HOT lines: X'
- Savings: ΔX lines × 100 ns/miss

## Embedded sub-struct audits (in-context)

For each embedded struct touched in slow-path:

### `<EmbeddedStruct>`

- Tier classification of embedded fields
- Verify embedded struct's own layout doesn't fight parent's tier classification

## Proposed changes

1. <bullet list of specific edits>
2. ...

## Test plan

- `static_assert(sizeof(<SurfaceName>) == N)` post-audit
- `static_assert(offsetof(<SurfaceName>, field) == M)` for hot-cluster boundaries
- Snapshot parity test: post-audit struct dumps to identical bytes vs pre-audit (bytewise equivalent under same state)
- Slow-path latency profile (perf stat -e L1-dcache-load-misses) before vs after

## TECH_DEBT items closed by this audit

- TECH_DEBT-XXX: ...

## Cross-references

- `DESIGN_SPECS/cache-layout-discipline-for-hot-side-structs.md`
- `CLAUDE.md` items 7, 17, 20, 27
- `plans/v5.15-live-readiness/subplans/2026-05-12-v5.15.5-per-horizon-tp-sl-serving.md`
