---
name: Post-v5.14 multi-branch audit + bug-fix sprint pending
description: All non-default branches likely accumulated similar drift to what audits surfaced in v5.14.8; plan dedicated audit pass after v5.14 closes
type: project
originSessionId: 3f84971f-8154-47ea-a8b9-86f7fad2325d
---
After v5.14.8 closes, expect a dedicated multi-branch audit + bug-fix sprint.

**Why:** v5.14.8 audits (parity-check / readiness / trace-deps / merge-scan re-run 2026-05-09 fresh) found 5+ structural drift items even after 6 design iterations + 3 prior audits on the same plan. Findings included: registry data dropped 3 fields during population; plan text contained uncompilable code snippets (wrong function signatures, wrong struct field paths); architectural surprises (three-way asymmetric naming, ModelHandle partial mirror) that prior audits described only as two-way. These weren't introduced by current session — they're residue from earlier sessions that experienced context compaction.

If v5.14's branch drifted this way, other long-lived branches (anything outside the default `experiment/per-core-sharding`) likely have analogous accumulated drift: stale plan files vs current code, partial-mirror surprises, stranded WIP, signature errors in design notes, dropped registry entries.

**How to apply:**
- Don't assume any branch's plan files match its current code state.
- When picking up work on a non-default branch, run `/parity-check` + `/readiness` + `/trace-deps` against its plans BEFORE starting the work.
- Caramel acknowledged this as a "known issue" 2026-05-09 — explicit cleanup sprint planned post-v5.14.
- Track candidate branches: anything with `feat/`, `experiment/`, or version-named branches that have been sitting more than ~2 weeks.
- When v5.14.8 closes, propose: a dedicated branch-audit sprint that walks each long-lived branch, runs the 4-audit pass on its plan files, and captures findings to TECH_DEBT.md or per-branch fix plans.
