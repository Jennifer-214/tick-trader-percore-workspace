---
name: feedback-short-sessions-30-60-min
description: "Sessions are now 30–60 min, not 5-hour marathons — size leaves, commit boundaries, and handoffs to that budget"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b8ca9f0c-cb63-473c-919e-a19e87cedcbc
  modified: 2026-08-14T00:46:29.248Z
  sister_specs: [feedback_micro_commits_compile_gated.md, feedback_document_as_you_go_over_catch_at_end.md]
  tags: []
---

Caramel, 2026-08-07: *"im not going to have like 5+ hour sessions for a while so like, if we can remember for now to break stuff into like 30m to 1hr duration sessions for getting stuff done."* Said right after a laptop shutdown mid-work — which cost nothing only because everything was already committed and pushed.

**Why:** the marathon-session assumptions (open-ended dives, opening big surfaces late, "we'll close it out at the end") no longer hold. A session can end abruptly; the work must be safe at every ~30–45 min boundary.

**How to apply:**
- Pick **session-sized leaves**: one committable, gate-green deliverable per session (~30–45 min of work), chosen so its natural end IS a clean boundary.
- **Commit + push at every clean boundary** — [[feedback-micro-commits-compile-gated]] now has a cadence bound, not just a preference.
- **Never open a new large surface late in a session** — queue it as the NEXT session's whole leaf instead (the plugin-TAG-system start over (g)-step-1 was the first application).
- Keep the active handoff current cheaply (the ADDENDUM convention) so any abrupt end is a working handoff.
- Prefer FINISHING over STARTING when both compete for the remaining budget.

**REFINED 2026-08-13** (Caramel, mid-sitting: *"these sessions are intermittent and reloaded alot, so they get split up"*): sessions don't just END short — they RELOAD mid-flight (interrupt → /clear → "reload context and continue" is a normal rhythm, sometimes several times in one evening). So capture fires at every LEAF boundary, not at session end: each landed leaf immediately gets its ledger/FEATURE_LOOKUP/MASTER/handoff/decision-log writes + commit + push BEFORE the next leaf opens. The handoff `coding_status` declared-delta is the continuity mechanism — a reload picks up from the last pushed boundary with zero conversational memory needed. Session-level decisions (design forks, build-contract changes) get their D-entry the same sitting they're made — an unlogged decision is exactly what a post-reload session re-litigates ([[feedback_document_as_you_go_over_catch_at_end]]).
