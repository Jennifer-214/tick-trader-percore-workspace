# Audit-driven pre-coding gate (multi-skill parallel pass)

**Established:** 2026-05-09 (v5.14.8 sprint)
**Status:** ACTIVE
**Cross-references:**
- Skills used: `/parity-check`, `/trace-deps`, `/readiness`, `/merge-scan`
- First systematic application: v5.14.8.A pre-A.merged + post-A.0.b
- Companion: `compaction-degraded-handoff-discipline` (sister rule)
- FoxML_Trader_v2 `CLAUDE.local.md` `feedback_compaction_degrades_treat_handoffs_as_hints.md`

---

## Problem statement

For ships that close recurring bug classes structurally (e.g., introduce a new registry, refactor a parser, change wire format), individual audits catch DIFFERENT classes of gaps:

- `/parity-check` catches train↔serve identity drift, wire-format risks, production-caller field-population gaps
- `/trace-deps` catches dependency-chain gaps in plan claims (function signatures, file:line refs, missing struct fields)
- `/readiness` catches plan-level gaps (cold-pickup completeness, X-macro variant selection, behavior-change-via-default)
- `/merge-scan` catches reuse opportunities + Class 18 mirror-incomplete patterns + branch-density regressions

Running ONE of these is partial coverage. Running them SEQUENTIALLY adds latency. Running them in PARALLEL on the same plan + code state catches the most gaps in the least wall-time.

The pattern: spawn all 4 audits in parallel, synthesize convergent findings, then act.

---

## Design space explored

### Option A: Sequential audit chain

Run /parity-check first; act on findings; then /trace-deps; etc.

**Rejected.** Sequential adds wall-time (~10-15 min × 4 = 40-60 min). Each audit is read-only; they don't conflict.

### Option B: One mega-audit skill

Combine into a single skill that does all 4 walks.

**Rejected.** Each skill has a focused mental model + dedicated test patterns; combining loses focus. Maintainability suffers (one giant skill spec vs 4 focused ones).

### Option C (chosen): Parallel spawn + synthesis

Spawn 4 Explore subagents in one message; each runs its skill spec inline (Layer 2 hierarchy); each returns a structured report. Main session synthesizes convergent findings.

Wall-time: ~10-15 min total (max of 4 parallel runs, not sum).
Coverage: all 4 audit lenses on same code state.
Cost: 4 subagent invocations (token-cheap; agents don't share context).

---

## The pattern (concrete shape)

### When to fire

Fire the pre-coding gate when the upcoming ship has 2+ of:
- Closes a recurring bug class structurally (new registry, new pattern)
- Touches wire format / serialization
- Adds 5+ new fields/functions/cfg entries
- Refactors a function used at 5+ call sites
- Picks up work from a previous (possibly compacted) session

For trivial single-file changes, skip — overkill.

### Spawn shape

```
Main session (Layer 1):
  ├─ Explore agent: /parity-check  (focus: stamp body / cfg parity / production-caller)
  ├─ Explore agent: /trace-deps    (focus: plan dependency verification + mirror data-flow)
  ├─ Explore agent: /readiness     (focus: 26-check pass; cold-pickup completeness)
  └─ Explore agent: /merge-scan    (focus: subsystem-narrow reuse opportunities)
```

Each subagent prompt includes:
- The skill spec path: `.claude/skills/<skill-name>/SKILL.md`
- Layer 2 instruction: "DO NOT spawn nested subagents" (prevents recursion trap)
- Specific files + plan paths to audit
- Architectural surprises ALREADY found (so audits build on them, not re-discover)
- Concise summary requirement: ≤250-300 words
- Save report to `plans/plan_checks/<skill>-<date>-<scope>.md`

### Synthesis pattern

After all 4 reports return, write a single synthesis doc:

```
# <ship> fresh audits — synthesis (4 audits, <date>)

## Verdicts
| Audit | Verdict | Conclusion |

## Convergent findings (all audits agree)
- F1: <finding> — caught by parity-check + readiness + trace-deps
- F2: ...

## Audit-specific findings
- Parity-check unique: ...
- Trace-deps unique: ...
- Readiness unique: ...
- Merge-scan unique: ...

## Decisions made (if any)
| Decision | Pick | Rationale |

## Action sequence
1. <item> (closes F1 + F2)
2. ...
```

Convergent findings have HIGH confidence (3+ audits independently agree). Audit-specific findings need verification before acting.

### Re-run after amendments

If the synthesis drives plan amendments (or a pre-flight ship like v5.14.8.A.0.b), re-run the most relevant 2 audits on the amended plan to verify amendments don't introduce NEW gaps:

- `/readiness` (verify cold-pickup completeness post-amendment)
- `/trace-deps` (verify amendment dependencies all resolve)

`/parity-check` and `/merge-scan` re-runs typically NOT needed after amendments (their findings are baked in).

---

## Trade-offs + when to apply

### Apply when:
- Ship is non-trivial (closes bug class structurally, touches wire format, large refactor)
- Plan was written in a different session (compaction-degraded handoff likely)
- Architectural surprises are surfacing mid-coding (audits formalize what's been found ad-hoc)
- Pre-tag rollback anchor is being created (audit-driven gate tags signal "we know what we're shipping")

### Skip when:
- Single-file bug fix
- Doc-only changes
- Plan written within the last hour by current session (already mentally fresh)

### Cost:
- 4 subagent invocations (~10-15 min wall-time max)
- 1 synthesis doc (~30-60 min to write convergent findings)
- 1-2 re-runs after amendments (~10 min each)

### Win:
- Catches 2-5x more gaps than single-audit pass (audits are complementary)
- Forces explicit decision-making BEFORE coding starts (no quiet design pivots mid-implementation)
- Creates persistent audit reports for postmortem learning
- Gives next session (if compaction occurs) verifiable starting state

---

## Reference implementations

### First systematic application: v5.14.8 sprint (2026-05-09)

Two passes:

**Pass 1 (post-A.1, pre-amendments):** Spawned all 4 audits on the plan + then-current code state.

Findings (synthesis: `plans/plan_checks/2026-05-09-v5.14.8-fresh-audits-synthesis.md`):
- F1: Registry data dropped 3 fields (CRITICAL; parity-check)
- F2: Plan code snippets uncompilable (CRITICAL; trace-deps)
- F3: cfg.model_max_age_hours doesn't exist (BLOCKING; all 3 audits)
- F4: STAMP_MODEL_CONST_AUTOPOPULATE not wired (CRITICAL; parity-check)
- F5: Three-axis asymmetric naming (HIGH; all 4 audits)
- F6: ModelHandle is partial mirror (HIGH; all audits)
- F7: Stranded WIP macro (HIGH; readiness + trace-deps)
- F8: FOREACH_FEATURE 7 caller sites not 6 (MEDIUM; trace-deps + readiness)
- F9: xgb_tree_method handling incomplete (HIGH; parity-check)

9 findings; prior session's 6 audits had caught NONE of these post-A.1 because they ran on stale code state.

**Pass 2 (post-amendments):** Re-spawned `/readiness` + `/trace-deps` on amended plan.

Verdicts:
- /readiness: GREEN (all 9 findings resolved by amendments)
- /trace-deps: YELLOW (only cfg.model_max_age_hours gap remained, scoped into pre-flight ship)

Confirmed amendments didn't introduce new gaps; greenlit pre-flight ship + A.merged.

---

## Lessons / gotchas

### Each agent must read its skill spec inline (Layer 2 hierarchy)

Older skill design spawned subagents that THEMSELVES spawned subagents — infinite recursion trap. Fix (added 2026-05-09): explicit "Layer 2 — DO NOT spawn nested subagents" instruction in each spawn prompt.

The skill specs themselves include:
> "If you are reading this spec inside an Explore subagent: YOU ARE the [auditor]. Do NOT spawn a nested subagent."

### Architectural surprises feed forward

Each spawn prompt includes the architectural surprises already found in earlier audits. This prevents:
- Duplicate work (next agent re-discovering the same thing)
- Verdict regressions (next agent ignoring known issues)
- Lost context (each agent gets full surprise list, not just skill scope)

### Subagent file-write permissions

Explore agents may report "I cannot create the report file due to read-only mode restrictions." Workaround: have them return findings as text in the agent return value; main session writes the synthesis.

Even better: pre-create the report file path so subagents can append. Or instruct them to return content INLINE for main session to save.

### Re-runs are CHEAPER than initial runs

Re-runs typically take less time than initial runs because:
- Skill spec is in agent's read cache
- Architectural surprises already enumerated (less exploration)
- Plan amendments are small targeted changes (focused audit scope)

Plan to re-run after every plan amendment that touches >2 sub-tags.

### Convergent findings have HIGH confidence

If 3+ audits independently flag the same gap, it's a real gap. Act on convergent findings without further verification.

Audit-specific findings (one audit only) need cross-check before acting — could be a false positive (skill-specific edge case) OR a real gap that other audits missed.

### Verdicts are SNAPSHOT-IN-TIME

GREEN today doesn't mean GREEN tomorrow. If the codebase changes between audit-run and ship-land, re-run. Especially for compaction-degraded handoffs (next session's audits may surface things this session's missed).

---

## Anti-pattern: relying on prior-session audit verdicts

The compaction-degraded handoff problem (`feedback_compaction_degrades_treat_handoffs_as_hints.md`):
- Session A runs audits, gets GREEN, ships partial work
- Session A's context compacts; some precision lost
- Session A writes "DO NOT re-run audits — they were re-run on the amended plan" handoff prompt
- Session B picks up; session A's audit verdicts are STALE (post-A.1 code differs from when audits ran)

**Treat prior-session audit verdicts as HINTS, not authority.** Re-run on current code state before acting. The 9 findings caught in v5.14.8 Pass 1 (despite the handoff prompt explicitly saying not to re-run) prove this.

---

## Cross-references

- `compaction-degraded-handoff-discipline.md` (future doc) — sister rule
- `wire-format-byte-preservation-discipline.md` — common audit subject
- FoxML_Trader_v2 `DOCS/RECURRING_BUG_PATTERNS.md` — bug class catalog (audits map to classes)
- FoxML_Trader_v2 `CLAUDE.local.md` — going-forward rules (this pattern formalizes)
- FoxML_Trader_v2 `.claude/skills/{parity-check,trace-deps,readiness,merge-scan}/SKILL.md` — individual skill specs
