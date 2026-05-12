---
name: Sprint sequencing — features first, then cleanup
description: Caramel's sprint preference 2026-05-09: implement new features (v5.14.5-12 + future) before triaging accumulated cleanup/bug debt (Gemini findings, TECH_DEBT entries)
type: project
originSessionId: 43a2b763-783f-4a6e-9b54-c3654977b44c
---
**Sprint sequencing preference (set 2026-05-09):**

When new-feature work and cleanup/bug-fixing work are both queued,
default to **features-first**. Cleanup gets a dedicated focused sprint
AFTER feature ships complete.

**Current state (v5.14 sprint):**
- v5.14.0 + .1 + .2 + .2.E + .3 + .4 shipped
- v5.14.5 → v5.14.12 remaining feature ships per master plan
- Gemini's parallel-session findings landing in `workspace/GEMINI_FINDINGS/`
  (5+ docs as of 2026-05-09; "more than 5, ~week of cleanup")
- `DOCS/TECH_DEBT.md` has 6 deferred entries

**Why:**
Caramel's framing: "i wanna get new features implemented then clean up
for functional and bug fixing." Features add operator-visible capability;
cleanup keeps the codebase healthy. Both matter, but interleaving them
fragments attention + makes both slower. Dedicated cleanup sprint with
focused mode = better outcomes than ad-hoc interspersion.

**How to apply:**

1. **During feature sprint:** Don't pause mid-feature for cleanup work.
   If cleanup candidates surface (during /merge-scan, /parity-check, or
   audit findings), capture as TECH_DEBT.md entries; don't auto-address.
2. **At feature sprint close:** Run `/readiness` Check 25 (TECH_DEBT.md
   surface scan) explicitly to inventory the accumulated debt; then
   either schedule a cleanup sub-sprint OR continue to next feature
   sprint per Caramel's call.
3. **Gemini findings:** treat as a parallel cleanup queue. Don't
   triage during feature sprint; bundle into the dedicated cleanup
   cycle after features land.
4. **TECH_DEBT.md entries:** queue without addressing during feature
   sprints. Cleanup sprint is the dedicated venue.
5. **Exception:** if a feature ship's audit surfaces a CRITICAL parity
   gap (PARITY-009.F-style — silent disabling of existing protections),
   address immediately as part of the feature ship; don't defer. Critical
   parity is not "cleanup" — it's bug-fixing inside the feature scope.

**Edge cases:**
- If a feature ship's CODE would be made simpler by addressing a
  TECH_DEBT entry first, the entry's trigger fires (per Check 25) —
  bundle the cleanup into that feature ship's scope. Otherwise defer.
- Gemini findings that overlap directly with a current feature ship's
  surface area should still be deferred; engineering attention works
  better single-threaded.

**Sister memories:**
- `feedback_no_defer_for_effort.md` — defer is last-ditch within a
  ship's scope (don't skip work that fits the ship)
- `feedback_consult_on_audit_findings.md` — present audit findings
  before coding; this memory tells you WHEN to act on findings
  (now: feature, later: cleanup)
- `feedback_structural_fix_for_recurring_class.md` — when cleanup
  sprint runs, prefer structural fix over direct patch
