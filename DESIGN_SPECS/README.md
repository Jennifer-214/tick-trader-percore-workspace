# DESIGN_SPECS — reusable architectural pattern reference library

**Established 2026-05-09 (mid v5.14.8 sprint).** Workspace-private. Each doc captures ONE solved design problem so future ships can reuse the pattern without re-deriving.

## Purpose

When a session solves a non-trivial architectural problem (e.g., "how do we make this registry handle partial-mirror struct generation cleanly?"), the design exploration + decision rationale + final pattern is valuable beyond the specific ship. It often reveals a REUSABLE TEMPLATE that applies elsewhere.

This directory is the library of those templates. Each doc:
- Names the pattern + its problem
- Walks the design space (options considered, why we picked one)
- Shows the concrete shape (code snippets, file references, examples)
- Documents the trade-offs + when NOT to apply
- Cross-references where the pattern was first applied + subsequent uses

## Naming convention

`<pattern-kebab-case>.md` — describe the pattern, not the specific ship.

Good: `bitmap-flag-api.md`, `x-macro-registry-with-presence-dispatch.md`, `audit-driven-pre-coding-gate.md`

Bad: `v5.14.8-stamp-body.md` (ship-specific; not reusable), `bitmap-stuff.md` (too vague)

## Structure per doc (~200-400 lines target)

```markdown
# <Pattern Name>

**Established:** YYYY-MM-DD (ship vX.Y.Z)
**Status:** ACTIVE / DEPRECATED / SUPERSEDED-BY-X
**Cross-references:** related design specs, code files, postmortems

## Problem statement
1-3 paragraphs. Recurring symptom + root cause class. WHY this pattern exists.

## Design space explored
Options A/B/C... considered, with trade-offs. WHY the chosen option won.

## The pattern (concrete shape)
Code snippets, macro definitions, struct shapes. Self-contained enough that a future
session can implement it without reading the original ship.

## Trade-offs + when to apply
- Apply when: <symptoms>
- Skip when: <symptoms>
- Cost: <effort, complexity, blast-radius>
- Win: <bug-class extinction, latency, etc.>

## Reference implementations
- First applied: <code path + commit/tag>
- Subsequent uses: <list>

## Lessons / gotchas
Surprises during implementation. Compaction-degraded handoff watch-outs. Etc.
```

## Catalog (v5.14.8 + v5.14.9 + v5.14.10 deliverables — 19 patterns)

Organized by category for quick discovery. Each pattern is one file in this dir.

### Core registry patterns (X-macro-driven extensibility)

| Doc | Pattern | Status |
|---|---|---|
| `x-macro-registry-with-presence-dispatch.md` | X-macro registry with token-paste (Y3) dispatch for partial-mirror struct generation. Emit_source column extension. | ACTIVE (v5.14.8) |
| `autopopulate-pattern-for-production-caller-class.md` | Production-caller field-population class extinction (AUTOPOPULATE companion macro from source-struct) | ACTIVE (v5.14.8) |
| `autopopulate-from-arity-macro-family.md` | _FROM_PAIR / _FROM_TRIPLE / _FROM_HEX / _FROM_SEPTUPLE — AUTOPOPULATE variant for callers with SCATTERED locals (no source struct) | ACTIVE (v5.14.9.F-.F.3) |
| `pre-post-cfg-registry-split-for-emit-order-preservation.md` | PRE/POST registry split when emit order must interleave with sister registry | ACTIVE (v5.14.8) |
| `registry-tuple-as-single-source-of-truth.md` | Option D — 5-col tuple feeds cfg + parser + GUI + override + stamp-binding + docs from ONE source | ACTIVE (v5.14.9.F.5) |
| `curve-registry-pattern.md` | FOREACH_<DOMAIN>_CURVE — named compute fns chosen by enum (LINEAR/EXP/STEP) via fn-pointer dispatch | ACTIVE (v5.14.9.A) |
| `calibration-log-column-registry.md` | FOREACH_<LOGNAME>_COL — auto-generated CSV header + row from registry; Variant A (fprintf direct) + Variant B (snprintf to buffer) | ACTIVE (v5.14.10.D + .F; 2 reference applications: calib log + trade log) |
| `postloadsetup-registry-pattern.md` | FOREACH_<DOMAIN>_POST_LOAD — auto-flow init/load steps to N call sites (boot + backtest + hot-swap); Class 18 mirror prevention via single helper walking registry | ACTIVE (v5.10.0a.G.7 + v5.13.4 + v5.14.10.C; 3 applications) |

### Registry decision frameworks

| Doc | Pattern | Status |
|---|---|---|
| `heterogeneous-registry-pattern.md` | SCOPE COLUMN vs DOMAIN SPLIT vs HYBRID (Form 1/2/3); Y3 dispatch canon; cache-layout discipline | ACTIVE v1.0 (field-tested v5.14.9.F-.F.6 + .G + .H) |
| `cfg-flag-eligibility-criteria.md` | 5-criteria decision algorithm — when a boolean is cfg-flag-eligible (and when it's not; `lat_enabled` cautionary tale) | ACTIVE (v5.14.9.F step 0) |
| `slow-path-gate-registry-pattern.md` | FOREACH_SLOW_PATH_GATE + AUTOPOPULATE; SCOPE COLUMN form canonical example | ACTIVE (v5.14.9.B.0) |
| `structural-fix-preferred-decision-framework.md` | When to invest in structural fix vs direct patch | ACTIVE (v5.14.8) |

### Bitmap variants

| Doc | Variant | Status |
|---|---|---|
| `bitmap-flag-api.md` | Base BITMAP_* macros (BITMAP_IS_SET / BITMAP_SET / BITMAP_BIT_U16 etc.) + 5 applied-variant cross-refs | ACTIVE (v5.14.8) |
| `partner-core-bitmap-pattern.md` | Per-core bool[N] → 1-bit-per-core in uint16/32/64 on parent struct (v5.14.9.G — `partner_pending_bitmap`) | ACTIVE (v5.14.9.G) |
| `transient-aggregation-bitmap-pattern.md` | Function-local aggregation bitmap with headroom (v5.14.9.H — `scaler_summary_flags`) | ACTIVE (v5.14.9.H) |
| `per-bit-per-core-override-pattern.md` | PER_CORE_OVERRIDE_BITMAP_DOMAINS — branchless bit-select for per-core overrides on bitmap fields (v5.14.9.F.6) | ACTIVE (v5.14.9.F.6) |

### Discipline / process patterns

| Doc | Pattern | Status |
|---|---|---|
| `audit-driven-pre-coding-gate.md` | Multi-audit pattern + compaction-handoff verification + MID-sprint audit guidance | ACTIVE (v5.14.8 + .9 update) |
| `wire-format-byte-preservation-discipline.md` | Guarding HMAC chains across registry refactors | ACTIVE (v5.14.8) |

### Cross-thread snapshot patterns

| Doc | Pattern | Status |
|---|---|---|
| `per-snapshot-cluster-layout-pattern.md` | alignas(64) clustering of cross-thread snapshot fields by concern; cache-line span budgeting; static_assert(offsetof) enforcement | ACTIVE (v5.14.10.0; first application: PerCoreSnap bandit telemetry cluster) |

**19 patterns total.** Adding new patterns: write the doc, add a row above, cross-link from related docs.

## Quick discovery — "I need to..."

- **...add a cfg flag (boolean toggle)** → `cfg-flag-eligibility-criteria.md` (decide eligibility) → `heterogeneous-registry-pattern.md` (pick domain) → `registry-tuple-as-single-source-of-truth.md` (5-col tuple)
- **...add a compute mode chosen by enum** → `curve-registry-pattern.md`
- **...replace multiple booleans with a bitmap** → `bitmap-flag-api.md` (which VARIANT?) → variant-specific doc:
  - Engine cfg domain → `heterogeneous-registry-pattern.md`
  - Per-core boolean → `partner-core-bitmap-pattern.md`
  - Function-local summary → `transient-aggregation-bitmap-pattern.md`
  - Registry has_flags → `x-macro-registry-with-presence-dispatch.md`
- **...add per-core override to a bitmap field** → `per-bit-per-core-override-pattern.md`
- **...stamp-bind a registry-derived field** → `wire-format-byte-preservation-discipline.md` (HMAC byte-equivalence) + `x-macro-registry-with-presence-dispatch.md` (emit_source column)
- **...avoid forgetting to populate a field at a production caller** → `autopopulate-pattern-for-production-caller-class.md` OR `autopopulate-from-arity-macro-family.md` (depending on caller shape)
- **...decide between structural fix vs direct patch** → `structural-fix-preferred-decision-framework.md`
- **...verify a sprint plan before coding** → `audit-driven-pre-coding-gate.md`
- **...add CSV columns to a log writer (fprintf-style)** → `calibration-log-column-registry.md` (pick Variant A=fprintf-direct OR Variant B=snprintf-to-buffer based on writer characteristics)
- **...add a post-load init/load step that runs at boot + backtest + hot-swap** → `postloadsetup-registry-pattern.md` (registry walk by single helper; prevents Class 18 mirror gap at N call sites)
- **...add fields to a cross-thread snapshot struct (PerCoreSnap-style)** → `per-snapshot-cluster-layout-pattern.md` (cluster by concern with alignas(64); cache-line span budget)

These are extracted from v5.14.8 + v5.14.9 + v5.14.10 sprint work. Future sprints add more as they solve new problems.

## Going-forward

When a session solves a non-trivial design problem:
1. Capture in postmortem doc DURING the work (mid-session, low-cost)
2. After the ship lands, extract a DESIGN_SPECS doc from the postmortem
3. Cross-link from postmortem → DESIGN_SPEC + from DESIGN_SPEC → first-application commit/tag

Example flow: v5.14.8.A.merged ships → postmortem captures the design pivots → extract `x-macro-registry-with-presence-dispatch.md` referencing the merged ship's commits.

## Cross-references

- `DOCS/EASY_ADDITIONS_INVARIANTS.md` (engine repo) — companion: registry pattern audited categories table; this directory holds the FULL design rationale per pattern.
- `DOCS/RECURRING_BUG_PATTERNS.md` — bug-class catalog. DESIGN_SPECS often correspond to "we extinguished class N via pattern X" entries.
- `DOCS/TECH_DEBT.md` — deferral ledger. DESIGN_SPECS often unblock TECH_DEBT items.
- `CLAUDE.local.md` going-forward rules — high-level discipline rules; DESIGN_SPECS are the concrete how-to backing them.
