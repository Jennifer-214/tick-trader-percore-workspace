---
type: meta-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-05-26
tags: [meta-discipline, doc-discipline, plan-template, operator-collaboration]
surface: [plan-pipeline, handoff-pipeline, session-pickup]
sister_specs:
  - structural-enforcement-when-memory-insufficient.md
  - pattern-codification-lifecycle.md
  - implementation-layer-blindspot-taxonomy.md
audit_tier: framework-pattern
applies_at_skills: [/capture-audit, /handoff, /sync-workspace, /post-ship-audit, /accept-handoff]
first_canonical_application: v5.15.5.F.4d.1.B.4 v1.7.4 + post-addendum cycles (retroactively created decision-logs/2026-05-24-v5.15.5.F.4d.1.B.4-v1.7.4.md)
---

# Session decision log discipline

## Why this discipline exists

When planning becomes amendment-cycle-heavy (typical at HIGH-RISK ships per `feedback_tiered_audit_discipline_per_plan_scope`), decisions / findings / commitments accumulate across cycles. Without structured capture, prior items silently age out as new findings hijack attention — operator-self-described "rabbit holes when planning a lot, stuff tends to get ignored in favor of new findings."

Memory codification (M7 worked example) demonstrated this for bug-class instances; same dynamic applies at decision-capture layer.

## Codification trigger

**Codified at v5.15.5.F.4d.1.B.4 v1.7.4** mid-addendum cycle after operator pushback surfaced gaps:
- "we should probably finisht the CI tool, and then update the hand off, and update any skills"
- "are you sure we arnt missing any deicisons i made for this? like we covered everyhting?"
- "i tend to go down rabbit holes when planning a lot, and stuff tends to get ignored in favor of new fingins"

9 amendment cycles (v1.0 → v1.7.4) + 3 addendum cycles accumulated dozens of operator-decisions + claude-commitments + discovered findings. Some had clear status (LANDED); some were forgotten. The addendum cycles revealed gaps despite "I think it's complete" assertions. Operator pushback caught the gaps; structural enforcement (this discipline + `/capture-audit` skill) closes the failure mode.

Per `feedback_motivated_collaborator_for_caramel` + `feedback_plan_right_not_fast`: best-software path requires investing in structural capture rather than relying on memory + diligence alone.

## Decision log artifact

### When to create

| Trigger | Action |
|---|---|
| Plan body version bump (vX.Y → vX.Y+1) AND version count > 3 | Init decision log for new version |
| Session spans > 1 calendar day with active planning amendments | Init decision log retroactively if missing |
| HIGH-RISK ship per `audit_tier` frontmatter | Init at first amendment |
| MED-RISK ship per `audit_tier` | Init at 2nd amendment |
| LOW-RISK / TRIVIAL | Optional; usually unnecessary |

### Where to write

Path: `plans/<sprint>/decision-logs/<plan-name-stem>-v<X.Y.Z>.md`

Template: `claude-skills/capture-audit/decision-log-template.md`

### Sections

```markdown
---
type: decision-log
plan_body: <plan-body-name>.md
plan_version: v<X.Y.Z>
ship_tag: v<X.Y.Z.Letter.N>
established: <YYYY-MM-DD>
session_context: <brief context>
parent_handoff: handoffs/<date>-<ship>-<purpose>-handoff.md
---

## Decisions (operator-decided)
| ID | Date | Decision | Rationale | Status |

## Commitments (claude-said-will-do)
| ID | Date | Commitment | Triggered by | Status |

## Discoveries (new findings surfaced this cycle)
| ID | Date | Finding | Severity | Status |

## Drift watch (auto-populated by /capture-audit Check 4)
(items proposed but not yet status'd; from unmatched sentinel markers)

## Cycle close summary (filled at next plan body version bump)
- Decisions landed: N / total
- Commitments landed: N / total
- Discoveries addressed: N / total
- Drift items resolved: N
- Carry-forward to next version: list
```

### Status values

- **PENDING** — decided but not yet acted on; should land within current cycle
- **LANDED** — implementation/codification complete (cite commit SHA or artifact)
- **DROPPED** — superseded or de-scoped; rationale required
- **DEFERRED** — explicitly deferred to future ship/cycle; cite TECH_DEBT entry

## Sentinel discipline (plan body)

In plan body amendments, mark each decision / commitment / finding with sentinel markers:

```markdown
<!-- D: D5 --> Use BookSnapshot<F> sister-canonical from BinanceDepth.hpp:29-41 ...
<!-- STATUS: LANDED at v1.7.3 -->
```

Markers:
- `<!-- D: <id> -->` decision
- `<!-- C: <id> -->` commitment
- `<!-- F: <id> -->` finding
- `<!-- STATUS: <state> -->` status — pending / landed / dropped / deferred

`/capture-audit` Check 4 enforces marker matching:
- Unmatched markers → DROPPED decision suspect; flag for operator review
- `<!-- STATUS: pending -->` older than 3 amendments → STALE; flag

## Sister disciplines

| Sister | Relationship |
|---|---|
| `feedback_session_decision_log_discipline` | Operator-collaboration memory codifying this pattern |
| `structural-enforcement-when-memory-insufficient.md` | M7 parent meta-discipline (this is one Stage 6 application) |
| `feedback_iteration_spiral_signals_audit_meta_gap` | Recognition trigger (3+ smaller findings = spiral); this discipline is CAPTURE artifact that prevents spiral-induced drift |
| `feedback_plan_right_not_fast` | Planning depth produces right answers; this discipline structurally captures planning depth |
| `feedback_tiered_audit_discipline_per_plan_scope` | HIGH-RISK ships are amendment-cycle-heavy → decision log required |
| `feedback_motivated_collaborator_for_caramel` | Best-software path requires structural capture |
| `user_adhd_deferred_reward_discipline` | Operator's cognitive-load amplifier this discipline addresses |
| `feedback_no_defer_for_effort` | Decision log makes deferrals explicit + status'd vs implicit drop |

## Structural enforcement (Stage 6 mechanism)

| Mechanism | Check |
|---|---|
| `/capture-audit` Check 3 | Verifies decision-log file exists for current plan body version |
| `/capture-audit` Check 4 | Verifies decision-sentinel matching in plan body |
| `/handoff` Stage 1.8 | Writes decision log if missing; preserves across sessions |
| `/sync-workspace` pre-commit invocation of `/capture-audit` | Pre-push verification |
| `/post-ship-audit` | Walks all decision logs for ship at close (postmortem) |
| `/accept-handoff` Stage 5 | Receiver-side `/capture-audit --deep` cross-checks log currency |

## Anti-patterns this prevents

- "Rabbit holes during planning" — finding new things hijacks attention; prior decisions silently dropped
- Cycle close without consolidation — decisions made but never verified as landed
- Operator asks "did we capture X?" and Claude has to recompute from session memory rather than reading log
- Handoff doc PENDING items not cross-referenced to decision-log
- Postmortem at ship close fails to reflect all operator-decisions made during planning
- Stale PENDING items aging across multiple amendments without status change

## Worked example: the cycle that codified this rule

`.B.4` v1.7.4 + post-addendum cycles (2026-05-26):
- 9 plan body amendments v1.0 → v1.7.4 accumulated
- Operator made 14+ explicit decisions during continuation cycle
- Multiple commitments tracked across handoff addendum + memory codifications + skill builds
- 5 NEW memories codified across session
- `/capture-audit` skill itself born from operator's "stuff gets ignored in favor of new findings" framing
- 9 capture gaps surfaced by operator pushback (across 2 pushback rounds) rather than automatic detection
- Codified discipline + structural enforcement landed concurrently
- Decision log created retroactively at `plans/v5.15-live-readiness/decision-logs/2026-05-24-v5.15.5.F.4d.1.B.4-v1.7.4.md` capturing 14 D / 20 C / 12 F entries
- Real-time rabbit-hole recognition mid-execution: operator flagged "se what i mean about the rabbit holes though?" while I was scope-creeping into 3-group memory consolidation; deferred per `feedback_proportionate_response_to_audit_findings`

## Lifecycle status

- **Stage 3 first-canonical (current)** — Worked example landed at `.B.4` v1.7.4
- **Stage 4 promotion** — `/handoff` Stage 1.8 + `/capture-audit` Check 3 fire on subsequent ships
- **Stage 5 promotion** — Multi-agent audits consistently invoke `/capture-audit` against decision logs
- **Stage 6 promotion** — Already at Stage 6 via `/capture-audit` skill + planned pre-commit hook integration

## Promotion-and-evolution path

Future enhancements:
- Auto-derivation from conversation transcript (parse "you decided X" patterns); hybrid with operator confirmation to avoid parsing fragility
- Per-cycle artifact rotation tied to plan body version bumps (NOT per-session)
- Composite with `/post-ship-audit` for ship-close consolidation
- CI tool that greps plan body for sentinels + reports unmatched OR stale entries
