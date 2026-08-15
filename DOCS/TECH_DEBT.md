---
type: ledger-template
splits_into: [DOCS/tech-debt/open.md, DOCS/tech-debt/in-flight.md, DOCS/tech-debt/closed.md]
total_entries_at_split: 106
split_date: 2026-05-18
split_criteria: by-status
established: 2026-05-09
---

# TECH_DEBT (INDEX)

This file was split 2026-05-18 because size exceeded ledger hard threshold (2013 lines per `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md`).

Content is now in per-status sub-files; this doc serves as the INDEX + cross-reference shape + format template + auto-write contract.

## Sub-files

| Sub-file | Coverage |
|---|---|
| `DOCS/tech-debt/open.md` | Status: OPEN — actively deferred work with explicit triggers (also DEFERRED-INDEFINITE / OPEN — partially addressed / PARTIAL CLOSED with active scope / PHASE-N applied with subsequent phases OPEN) |
| `DOCS/tech-debt/in-flight.md` | Status: IN-FLIGHT — being addressed in an active sub-ship |
| `DOCS/tech-debt/closed.md` | Status: CLOSED — archival (includes NOT-A-BUG rationale-preservation entries and APPLIED at ship close) |

**Entry counts are NOT written here — re-derive them.** The column that used to sit in that table read `83 / 2 / 25`; the real values on 2026-08-15 were `202 / 0 / 76`. A hand-written tally in a lasting doc is stale on the very commit that writes it and fails **silently** — nothing reads it, so nothing catches it — which is exactly why counts belong in a re-derive fence and never in prose (`feedback_name_members_never_tallies_in_docs`):

```bash
for f in open in-flight closed; do
  printf "%-10s %s\n" "$f" "$(grep -c '^### TECH_DEBT-' DOCS/tech-debt/$f.md)"
done
```

## Cross-reference shape

External cross-refs use canonical ID format `TECH_DEBT-NNN`. The ID is preserved across sub-files; `rg "TECH_DEBT-NNN"` finds the canonical entry in the appropriate sub-file automatically.

Example:
- `rg "TECH_DEBT-115" DOCS/tech-debt/` — finds the entry in `open.md`
- `rg "TECH_DEBT-005" DOCS/tech-debt/` — finds the entry in `closed.md`
- `rg "TECH_DEBT-063" DOCS/tech-debt/` — finds the entry in `open.md` (an entry MOVES between sub-files as its status changes, which is exactly why you grep for the ID instead of hardcoding the file)

## Established 2026-05-09 (v5.14.2.E.3). Workspace-private (symlinked into engine repo as `DOCS/TECH_DEBT.md`).

## Purpose

Append-only ledger of known-deferred architectural cleanups + their triggers. Same shape as `PARITY_ISSUES.md` (proven mechanism) but for items that aren't bugs (operator policy: not a parity finding, not a known issue, not a recurring class). Just architectural debt that needs to live somewhere queryable.

## Why this exists

Caramel's pushback 2026-05-09 (v5.14.2.E review): "what if I forget about that stuff, like doesn't addressing the deferred items now make future maintenance easier?"

The answer is: address now if architecturally bounded; defer if separate concern. But deferred items hidden in code comments / postmortems / chat memory get forgotten. This ledger surfaces them.

`/readiness` Check 25 enforces: before declaring a ship complete, scan TECH_DEBT (now across all sub-files) for items in the ship's surface area. If any apply, decide explicitly — address now OR refresh the entry with current cost estimate. Don't silently leave it stale.

## Format per entry

```
### TECH_DEBT-NNN — <one-line title>

- **Created:** YYYY-MM-DD by <ship that surfaced it>
- **Severity:** LOW / MEDIUM / HIGH (impact if NEVER addressed)
- **Surface:** which subsystem / file path
- **What's deferred:** 1-3 sentence description
- **Why deferred (not effort-avoidance):** explicit rationale (e.g., "wider scope than ship; operator-edge; orthogonal concern")
- **Cost estimate:** hours; LOC; risk
- **Trigger:** specific event that should prompt addressing (e.g., "next time stamp body schema changes", "before v5.X release", "when count > 5")
- **Status:** OPEN / IN-FLIGHT / CLOSED / NOT-A-BUG / DEFERRED-INDEFINITE
- **Cross-ref:** related PARITY entries, code locations, plans

Status transitions:
- OPEN → IN-FLIGHT when ship starts addressing (MOVE entry from open.md to in-flight.md)
- IN-FLIGHT → CLOSED when shipped (MOVE entry from in-flight.md to closed.md)
- OPEN → NOT-A-BUG if review determines it's not actually debt (MOVE entry to closed.md preserving rationale)
```

## Status definitions

- **OPEN** — known debt, not yet scheduled (lives in `open.md`)
- **IN-FLIGHT** — ship in progress is addressing (lives in `in-flight.md`)
- **CLOSED** — fixed in a specific ship (cite commit/tag) (lives in `closed.md`)
- **NOT-A-BUG** — review determined this isn't actually debt; preserved as rationale (lives in `closed.md`)
- **DEFERRED-INDEFINITE** — debt acknowledged but no near-term plan to ship; trigger documented (often external dependency outside operator's control). Distinct from OPEN (which implies "scheduled or schedulable"). Lives in `open.md` until trigger event flips it back. If/when trigger event occurs, status flips back to OPEN (entry stays in `open.md`).

## Auto-write contract (set 2026-05-09)

When `/readiness` Check 25, `/merge-scan`, `/parity-check`, or any other audit identifies a deferral candidate, the agent **MUST** auto-write the entry to the appropriate sub-file (typically `open.md`). Don't defer to "operator copies after review" — the ledger is single source of truth. Same discipline as `PARITY_ISSUES.md` auto-write contract (CLAUDE.local.md).

A finding that exists only in a transient audit report or chat memory gets re-discovered as noise.

## Cross-references

- `DOCS/PARITY_ISSUES.md` — sister ledger for parity findings (different class)
- `DOCS/RECURRING_BUG_PATTERNS.md` — bug class catalog
- `CLAUDE.md` item 19 — "Structural fix > direct patch when bug class can recur" (philosophy)
- `CLAUDE.local.md` — going-forward rules including this auto-write contract
- `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md` — the file-size discipline that motivated this split

## Entry-to-sub-file map

| TECH_DEBT-NNN | Status | Sub-file |
|---|---|---|
| TECH_DEBT-001 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-002 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-003 | CLOSED v5.15.0 | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-004 | CLOSED v5.14.9.D | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-005 | CLOSED v5.15.4 | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-006 | CLOSED v5.14.8 | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-007 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-008 | DEFERRED-INDEFINITE | `DOCS/tech-debt/open.md` |
| TECH_DEBT-009 | PARTIAL CLOSED (active deferred) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-010 | CLOSED v5.14.10.D | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-011 | OPEN — partially addressed | `DOCS/tech-debt/open.md` |
| TECH_DEBT-012 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-013 | CLOSED v5.14.9 | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-014 | CLOSED v5.15.0 | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-015 | CLOSED v5.14.9.E | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-017 | CLOSED v5.14.11.C | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-018 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-019 | NOT-A-BUG (rationale) | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-020 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-021 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-022 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-023 | NOT-A-BUG (rationale) | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-024 | CLOSED v5.15.2 | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-025 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-026 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-027 | CLOSED v5.14.10.C | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-028 | CLOSED v5.15.1 | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-029 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-030 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-031 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-032 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-033 | CLOSED v5.15.2.D | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-034 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-035 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-036 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-037 | CLOSED v5.15.5.A.7 | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-038 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-039 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-040 | CLOSED v5.15.5.B.5 | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-041 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-042 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-043 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-044 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-045 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-046 | OPEN (awaiting 2nd-app trigger) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-049 | OPEN (awaiting 2nd-app trigger) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-050 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-051 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-052 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-053 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-054 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-055 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-056 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-057 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-058 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-059 | OPEN (blocked on .F.4d) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-063 | OPEN (in progress) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-064 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-065 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-066 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-067 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-068 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-069 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-070 | OPEN (waits on C++20) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-071 | OPEN (evaluation) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-072 | OPEN (must close pre-live) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-073 | OPEN (post-v5.15) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-074 | OPEN (post-v5.15) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-075 | OPEN (post-framework HP refactor) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-076 | OPEN (cleanup ship post-.F.4d) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-077 | OPEN (cleanup ship post-.F.4d) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-078 | OPEN (cleanup ship post-.F.4d) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-079 | OPEN (cleanup ship post-.F.4d) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-080 | OPEN (cleanup ship post-.F.4d) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-081 | OPEN (post-.F.4e) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-082 | CLOSED v5.15.5.F.4d | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-083 | CLOSED v5.15.5.F.4d | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-084 | CLOSED v5.15.5.F.4d | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-085 | OPEN (queued as .F.4d.1) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-086 | CLOSED v5.15.5.F.4d.1 planning | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-087 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-088 | OPEN (deferred to .F.4e planning) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-089 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-090 | OPEN — REFRAMED 2026-05-17 | `DOCS/tech-debt/open.md` |
| TECH_DEBT-091 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-092 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-093 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-094 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-095 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-096 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-097 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-098 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-099 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-100 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-108 | CLOSED 2026-05-18 | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-109 | CLOSED 2026-05-18 | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-110 | OPEN with explicit trigger | `DOCS/tech-debt/open.md` |
| TECH_DEBT-111 | OPEN with explicit trigger | `DOCS/tech-debt/open.md` |
| TECH_DEBT-112 | APPLIED at .B.3 (CLOSED) | `DOCS/tech-debt/closed.md` |
| TECH_DEBT-113 | OPEN with explicit trigger | `DOCS/tech-debt/open.md` |
| TECH_DEBT-114 | OPEN with explicit trigger | `DOCS/tech-debt/open.md` |
| TECH_DEBT-115 | PHASE 1 APPLIED; PHASE 2-4 OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-116 | OPEN with explicit trigger | `DOCS/tech-debt/open.md` |
| TECH_DEBT-117 | OPEN with explicit trigger | `DOCS/tech-debt/open.md` |
| TECH_DEBT-107 | PARTIAL CLOSED at v5.15.5.F.4d.1.B.3 (12 MATCH closed; 16 DIFFER pending per-row decision) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-118 | OPEN with explicit trigger | `DOCS/tech-debt/open.md` |
| TECH_DEBT-119 | OPEN (in-flight at .B.4 start) | `DOCS/tech-debt/open.md` |
| TECH_DEBT-120 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-121 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-122 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-123 | OPEN | `DOCS/tech-debt/open.md` |
| TECH_DEBT-124 | OPEN (DEFERRED-INDEFINITE acceptable) | `DOCS/tech-debt/open.md` |

## Migration history

- 2026-05-18: Split from monolithic TECH_DEBT.md (106 entries / 2013 lines) per `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md` Stage 3 first canonical application.
- 2026-05-09: TECH_DEBT.md established (v5.14.2.E.3) per `PARITY_ISSUES.md` precedent.

## Future debt findings will append here

When `/readiness` Check 25 OR `/merge-scan` OR any audit identifies deferral candidates:
1. Assign next TECH_DEBT-NNN
2. Fill in the format template above
3. Set initial status (usually OPEN) → append entry to `DOCS/tech-debt/open.md`
4. Cross-link from the audit report (`plans/plan_checks/*`)
5. Reference in commit message of the closing ship
6. On status transitions: MOVE entry to the appropriate sub-file (`open.md` → `in-flight.md` → `closed.md`). The canonical ID `TECH_DEBT-NNN` is preserved across moves; external cross-refs remain valid because `rg "TECH_DEBT-NNN"` finds the entry wherever it lives.
7. Update the entry-to-sub-file map in this INDEX when a move happens.
