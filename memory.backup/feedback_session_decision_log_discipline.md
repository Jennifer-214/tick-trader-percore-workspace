---
name: session-decision-log-discipline
description: When planning cycle exceeds 3 amendments OR spans multiple sessions, maintain a structured decision log per plan body version. Captures operator-decided actions + claude-committed actions + discovered findings + per-item STATUS (pending/landed/dropped/deferred). Sidecar file at `plans/<sprint>/decision-logs/<plan-name>-v<version>.md`. Sister to feedback_structural_enforcement_when_memory_insufficient (M7 parent) — closes "rabbit hole during planning" failure mode by structural artifact + /capture-audit drift check. Sister to feedback_iteration_spiral_signals_audit_meta_gap (the spiral signal; this is the per-cycle artifact).
metadata: 
  node_type: memory
  type: feedback
  originSessionId: fc2542a7-8662-4b21-a393-f1598d05e50b
  sister_specs: [feedback_structural_enforcement_when_memory_insufficient.md, feedback_iteration_spiral_signals_audit_meta_gap.md, feedback_plan_right_not_fast.md, feedback_tiered_audit_discipline_per_plan_scope.md, feedback_motivated_collaborator_for_caramel.md, user_adhd_deferred_reward_discipline.md, feedback_no_defer_for_effort.md]
  tags: [session-continuity, planning-discipline]
---

When planning becomes amendment-cycle-heavy (typical at HIGH-RISK ships per `feedback_tiered_audit_discipline_per_plan_scope`), decisions/findings/commitments accumulate across cycles. Without structured capture, prior items silently age out as new findings hijack attention — Caramel-self-described "rabbit holes" symptom. Memory codification (M7 worked example) demonstrated this for bug-class instances; same dynamic applies at decision-capture layer.

**Why:** Codified 2026-05-26 at `.B.4` v1.7.4 cycle after operator surfaced:

> "we should probably finisht the CI tool, and then update the hand off, and update any skills or claude.md files to know it exists so we actually use it"
> "are you sure we arnt missing any deicisons i made for this? like we covered everyhting?"
> "i tend to go down rabbit holes when planning a lot, and stuff tends to get ignored in favor of new fingins"

The symptom: 9 amendment cycles (v1.0 → v1.7.4) accumulated dozens of operator-decisions + claude-commitments + discovered findings. Some had clear status (landed); some were forgotten. The handoff addendum cycle revealed 3 gaps despite my "I think it's complete" assertion at the time. Operator pushback caught the gaps; structural enforcement (`/capture-audit` skill + decision-log artifact) closes the failure mode.

Per `feedback_motivated_collaborator_for_caramel` + `feedback_plan_right_not_fast`: best-software path requires investing in structural capture rather than relying on memory + diligence alone.

**How to apply:**

1. **Trigger detection** — at plan body version bump (vX.Y → vX.Y+1), if version count > 3 OR session spans > 1 calendar day, init decision log:
   - Path: `plans/<sprint>/decision-logs/<plan-name-stem>-v<X.Y+1>.md`
   - Template at `claude-skills/capture-audit/decision-log-template.md`
   - Sections: Decisions (operator-decided) + Commitments (claude-said-will-do) + Discoveries (new findings) + Drift watch (auto-populated) + Cycle close summary (filled at next version bump)

2. **Per-decision sentinel discipline** — in plan body amendments, mark each decision/commitment/finding with `<!-- D: <id> -->` / `<!-- C: <id> -->` / `<!-- F: <id> -->` markers paired with `<!-- STATUS: <state> -->`. `/capture-audit` Check 4 enforces marker matching.

3. **/capture-audit invocation** — runs pre-commit (via /sync-workspace) + pre-handoff (via /handoff). Checks decision-log currency + status-match against artifact state.

4. **Cycle close summary** — at next plan body version bump, fill in cycle close summary: decisions landed / commitments landed / discoveries addressed / drift items resolved / carry-forward to next version.

5. **Ship-close consolidation** — at ship close, `/post-ship-audit` (when built) walks all `decision-logs/v<X.Y.Z>.md` for the ship, consolidates into postmortem.

**Recognition markers (when this rule is being violated):**

- Plan body has > 3 amendment versions BUT no decision-log file
- Decision-log file exists BUT entries have no STATUS column
- Multiple PENDING items aging across 3+ amendments without status change
- Handoff doc PENDING items not cross-referenced to decision-log
- Postmortem at ship close fails to reflect all operator-decisions made during planning
- Operator asks "did we capture X?" and Claude has to recompute from memory rather than reading log

**Sister memories:**

- [[structural-enforcement-when-memory-insufficient]] — M7 parent meta-discipline; this rule is one Stage 6 application
- [[iteration-spiral-signals-audit-meta-gap]] — recognition trigger (3+ smaller findings = spiral); this rule is the CAPTURE-artifact that prevents spiral-induced drift
- [[plan-right-not-fast]] — planning depth produces right answers; this rule structurally captures planning depth
- [[tiered-audit-discipline-per-plan-scope]] — HIGH-RISK ships are amendment-cycle-heavy; this rule applies
- [[motivated-collaborator-for-caramel]] — best-software path requires structural capture
- [[adhd-deferred-reward-discipline]] — operator's ADHD pattern is the cognitive-load amplifier this rule addresses
- [[no-defer-for-effort]] — decision log makes deferrals explicit + status'd vs implicit drop

**Structural enforcement (Stage 6 mechanism):**

- `/capture-audit` Check 3 — verifies decision-log file exists for current plan body version
- `/capture-audit` Check 4 — verifies decision-sentinel matching in plan body
- `/handoff` Stage 1.8 — writes decision log if missing; preserves across sessions
- `/sync-workspace` pre-commit invocation of /capture-audit
- `/post-ship-audit` (queued) — walks all decision logs for ship at close
- `tools/check_plan_body_symbol_existence.py` (B-Plus sister tool) — different surface but same Stage 6 escalation pattern

**Worked example (the cycle that codified this rule):**

`.B.4` v1.7.4 cycle (2026-05-26):
- 9 plan body amendments v1.0 → v1.7.4 accumulated
- Operator made 4+ explicit decisions during continuation cycle (B-Plus approval, "Finish it" approval, codify+fix+resync approval, "do existing skills need updating")
- Multiple commitments tracked across handoff addendum + memory codifications + skill builds
- 4 NEW memories codified across session
- /capture-audit skill itself born from operator's "stuff gets ignored in favor of new findings" framing
- 7 capture gaps surfaced by operator pushback rather than automatic detection
- Codified discipline + structural enforcement landed concurrently at .B.4 v1.7.4 + post-addendum cycle.

**Codification trigger (worked examples for future):**

Per `feedback_proactive_novel_alternative_consideration`: codify at 2-instance proactive threshold. The 1st instance was the M7 codification cycle (memory→structural escalation). This is the 2nd same-shape instance (capture→structural escalation). Codified PROACTIVELY at 2-instance threshold per same proactive rule.
