---
name: Compaction degrades context — verify handoff prompts against current code state
description: Earlier sessions with compaction lose precision; handoff prompts and prior audit reports from those sessions are HINTS not authority — always verify against current code before acting on them
type: feedback
originSessionId: 3f84971f-8154-47ea-a8b9-86f7fad2325d
---
When picking up work from a session-handoff prompt (or any persisted context that was written by a previous session), treat it as a SUGGESTION not as authoritative truth. Always verify against the current code state before acting on it.

**Why:** Caramel observation 2026-05-09: "compacting degrades output." Previous session that shipped v5.14.8.0 + v5.14.8.A.1 + wrote the handoff prompt experienced context compaction. Resulting artifacts had multiple precision losses:

- Plan code snippets had uncompilable signatures (`Health_LogCriticalRateLimited("[stale_model] ...")` shown with 1 arg; actual sig requires 5 args).
- Plan code referenced `m->stamp.run_name` — but ModelHandle has no `.stamp` substruct (it's FLAT).
- Registry data was populated but dropped 3 fields between training_poll_interval and xgb_hyperparams (scaler pair + model_num_outputs).
- Stranded uncommitted WIP macro that doc text already referenced.
- "Asymmetric naming" described as two-way but was actually three-way.
- FOREACH_FEATURE described as 6-param + 7th column extension — count of caller sites stale.
- 6 prior audits gave GREEN/YELLOW/RED verdicts; fresh re-run on current state (post-handoff) found 15+ NEW findings the prior runs missed.

**How to apply:**
- Read the handoff prompt to orient (goals, locked decisions, sub-tag plan).
- Then read the actual code state (struct definitions, registry contents, parser/emitter, current branch state).
- Cross-check every concrete claim in the handoff against current code: function signatures, struct field paths, registry contents, file:line citations.
- When the handoff says "do X first then Y", verify X is still the right starting point given current code state.
- For multi-day plans + handoffs, re-run audits (`/parity-check`, `/readiness`, `/trace-deps`, `/merge-scan`) BEFORE proposing first concrete moves. Don't trust prior audit verdicts that were run on stale code state.
- Especially distrust verdicts of "GREEN — start coding" from prior sessions; the verdict was for code state at that time, not now.
- Caramel called this out explicitly 2026-05-09: "good to note that compacting degrades output." Apply across all session-handoff scenarios going forward.

**Sister rule:** This pairs with `feedback_consult_on_audit_findings.md` — even after fresh audits, present findings + iterate before coding. Don't auto-proceed on prior or fresh audit verdicts; check with Caramel.
