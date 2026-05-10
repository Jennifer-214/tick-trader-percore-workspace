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

## Initial seed library (v5.14.8 sprint deliverables)

| Doc | Pattern | Status |
|---|---|---|
| `bitmap-flag-api.md` | Reusable bit-packed flag accessor (BITMAP_*) | ACTIVE |
| `x-macro-registry-with-presence-dispatch.md` | X-macro registry with token-paste dispatch for partial-mirror struct generation | ACTIVE |
| `autopopulate-pattern-for-production-caller-class.md` | Production-caller field-population class extinction | ACTIVE |
| `audit-driven-pre-coding-gate.md` | Multi-audit pattern + compaction-handoff verification | ACTIVE |
| `wire-format-byte-preservation-discipline.md` | Guarding HMAC chains across registry refactors | ACTIVE |
| `structural-fix-preferred-decision-framework.md` | When to invest in structural fix vs direct patch | ACTIVE |
| `pre-post-cfg-registry-split-for-emit-order-preservation.md` | PRE/POST registry split when emit order must interleave with sister registry | ACTIVE |
| `slow-path-gate-registry-pattern.md` | FOREACH_SLOW_PATH_GATE + AUTOPOPULATE; SCOPE COLUMN form (Y3 token-paste dispatch) | ACTIVE (v5.14.9.B.0) |
| `heterogeneous-registry-pattern.md` | Decision framework: SCOPE COLUMN vs DOMAIN SPLIT for heterogeneous registry shape; Y3 dispatch canon; cache-layout discipline | DRAFT v0.2 (pre-field-test; finalizes v1.0 ACTIVE at v5.14.9 umbrella close) |

These are extracted from v5.14.8 + v5.14.9 sprint work. Future sprints add more as they solve new problems.

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
