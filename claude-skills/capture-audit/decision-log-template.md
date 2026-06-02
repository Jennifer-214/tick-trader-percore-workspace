---
type: decision-log
plan_body: <plan-body-name>.md
plan_version: v<X.Y.Z>
ship_tag: v<X.Y.Z.Letter.N>
established: <YYYY-MM-DD>
session_context: <brief-context-string>
parent_handoff: handoffs/<date>-<ship>-<purpose>-handoff.md
---

# Decision log — `<plan-body-name>`

The SSoT for a multi-session sub-sprint's decisions. **Canonical shape (proven over the `.E` sub-sprint,
Sessions 3–9, D-97..D-146): sequential PROSE entries with stable cross-referenceable `D-NNN` IDs + paired
sentinels, organized into per-session addenda.** Prose, not tables — because each decision carries its
rationale + the alternatives-considered-and-rejected + sister memory/DESIGN_SPECS links + file:line anchors,
all of which table cells truncate. The log IS the institutional memory the next (cold) session reads, so
write the nuance.

Trigger (per `feedback_session_decision_log_discipline`): maintain a decision log when a planning cycle
exceeds ~3 amendments OR spans multiple sessions.

Used by:
- `/capture-audit` Check 3 + 4 (drift check — verifies the log exists + every `<!-- D/C/F -->` is paired with a `<!-- STATUS -->`)
- `/accept-handoff` Stage 4.6 (decision-status reconciliation — reads STATUS to tell the receiver decided-vs-open; flags stale-plan-prose drift)
- `/handoff` Stage 1.8 (next-session pickup; cited in the handoff's required reading)
- `/post-ship-audit` (reflective postmortem at ship close)
- `/sync-workspace` + `/close-session` (pre-commit / pre-close verification via `tools/check_session_docs.sh`)

## Entry format (the proven `.E` shape)

Decisions, commitments, AND findings are numbered in ONE sequential `D-NNN` series across the whole
sub-sprint (D-1, D-2, … — never reset per-cycle; stable IDs survive sessions + cross-references). Each is a
PROSE entry bracketed by two sentinels:

```
<!-- D/C/F: D-NNN -->
**D-NNN (<one-line title — what was decided / committed / found>).** <body: the decision + WHY + the
alternatives considered-and-rejected + sister memories / DESIGN_SPECS links + any file:line anchors. As much
context as the next-session cold-reader needs — this is the SSoT, not a summary.>
<!-- STATUS: <verbose state — e.g. "decided/executed; landed at <sha>" / "decided; <sub-part> deferred to <ship>" /
"in-progress — <what's pending>" / "superseded by D-MMM" / "decided (reconciliation); <what it corrects>"> -->
```

- The `<!-- D/C/F: D-NNN -->` marker is the SAME for decisions, commitments, and findings (one series, one
  matcher); the entry title + STATUS text carry the kind + the nuance.
- `/capture-audit` Check 4 enforces that every `<!-- D/C/F: D-NNN -->` is FOLLOWED by a `<!-- STATUS: -->`
  (paired). An unpaired marker is a red build.
- The STATUS text is VERBATIM-meaningful — `/accept-handoff` Stage 4.6 reads it to tell the receiver
  decided-vs-open, so write the nuance ("decided; rounding-MODE subpart was a research item, later closed by
  D-MMM"), not a bare flag. A bare "decided" loses the sub-part history that misleads pickup.

## Session addenda (multi-session organization)

The earliest foundational decisions sit at the top (pre-addenda). As the sub-sprint progresses, group new
entries under per-session headers; each session's addendum opens with 1–2 lines of context (what the session
did + the commits/artifacts it produced), then its `D-NNN` entries, and closes with an end marker:

```
### Session N — <one-line session summary> (<YYYY-MM-DD>)

<context: what this session did; commits on anchor <sha>; artifacts produced>

<!-- D/C/F: D-NNN -->
**D-NNN (...).** ...
<!-- STATUS: ... -->

End of Session N addendum.
```

## Ship-close summary (filled at ship close)

- Decisions decided/executed: <count> / <total>
- Genuinely-open at close (carry-forward): <explicit list, or "none — decisions done; next move is execution">
- Superseded / reconciled: <list, each citing the superseding D-NNN>
- Codification slate written at close (memories / DESIGN_SPECS / catalog amendments): <list>
