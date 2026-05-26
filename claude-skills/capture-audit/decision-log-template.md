---
type: decision-log
plan_body: <plan-body-name>.md
plan_version: v<X.Y.Z>
ship_tag: v<X.Y.Z.Letter.N>
established: <YYYY-MM-DD>
session_context: <brief-context-string>
parent_handoff: handoffs/<date>-<ship>-<purpose>-handoff.md
---

# Decision log — `<plan-body-name>` v<X.Y.Z>

Tied to plan body version bump v<X.Y-1.Z> → v<X.Y.Z>. Captures decisions made, commitments taken, discoveries surfaced, and status of each.

Used by:
- `/capture-audit` (drift check; verifies status field present + matches state)
- `/post-ship-audit` (reflective postmortem at ship close)
- `/handoff` (next-session pickup context)
- `/sync-workspace` (pre-commit verification)

## Decisions (operator-decided)

| ID | Date | Decision | Rationale | Status |
|---|---|---|---|---|
| D1 | <date> | <what was decided> | <why> | PENDING / LANDED / DROPPED / DEFERRED |
| D2 | <date> | ... | ... | ... |

Status options:
- **PENDING** — decided but not yet acted on; should land within current cycle
- **LANDED** — implementation/codification complete (cite commit SHA or artifact)
- **DROPPED** — superseded or de-scoped; rationale required
- **DEFERRED** — explicitly deferred to future ship/cycle; cite TECH_DEBT entry

## Commitments (claude-said-will-do)

| ID | Date | Commitment | Triggered by | Status |
|---|---|---|---|---|
| C1 | <date> | <what I committed to> | <what prompt/decision> | PENDING / LANDED / DROPPED / DEFERRED |
| C2 | <date> | ... | ... | ... |

## Discoveries (new findings surfaced this cycle)

| ID | Date | Finding | Severity | Status |
|---|---|---|---|---|
| F1 | <date> | <what surfaced> | CRITICAL / HIGH / MED / LOW | OPEN / ADDRESSED / DEFERRED |
| F2 | <date> | ... | ... | ... |

## Drift watch (auto-populated by /capture-audit)

Items proposed in this plan body but not yet status'd:
- (none currently — populated when /capture-audit detects unmatched sentinel markers)

## Cycle close summary (filled at next plan body version bump)

- Decisions landed: <count> / <total>
- Commitments landed: <count> / <total>
- Discoveries addressed: <count> / <total>
- Drift items resolved: <count>
- Carry-forward to next version: <list>

## Sentinel discipline

Plan body should use `<!-- D: <id> -->` / `<!-- C: <id> -->` / `<!-- F: <id> -->` markers at decision/commitment/finding citations, paired with `<!-- STATUS: <state> -->` after each. `/capture-audit` Check 4 enforces marker matching.
