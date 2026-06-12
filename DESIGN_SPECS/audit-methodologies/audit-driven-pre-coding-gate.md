---
type: audit-methodology
stage: 3-first-canonical
version: 1.0
established: 2026-05-09
tags: [audit-methodology, framework-discipline, meta-discipline]
surface: [registry]
sister_specs: [implementation-layer-blindspot-taxonomy.md, audit-scope-taxonomy.md, audit-finding-kind-taxonomy.md, adversarial-multi-agent-audit-methodology.md, characterization-test-discipline.md]
applies_at_skills: [/precoding-audit-gate, /parity-check, /trace-deps, /readiness, /merge-scan, /dod-audit, /blindspot-scan]
---

# Audit-driven pre-coding gate (multi-skill parallel pass)

**Established:** 2026-05-09 (v5.14.8 sprint)
**Status:** ACTIVE
**Cross-references:**
- Skills used (SHAPE layer): `/parity-check`, `/trace-deps`, `/readiness`, `/merge-scan`, `/dod-audit`, plus extended set `/accounting-audit`, `/registry-fit-audit`, `/hft-audit`
- Skills used (IMPLEMENTATION-DETAIL layer; added 2026-05-18): `/blindspot-scan` — fires after SHAPE returns GREEN-or-YELLOW; walks 12-category taxonomy at `implementation-layer-blindspot-taxonomy.md`. SHAPE audits answer "is design right?"; IMPLEMENTATION-DETAIL audits answer "will code compile/run without surprise?"
- First systematic application: v5.14.8.A pre-A.merged + post-A.0.b (SHAPE); first `/blindspot-scan` canonical application: v5.15.5.F.4d.1.B.3 Step 1.6.3 pre-coding (2026-05-18)
- Companion: `compaction-degraded-handoff-discipline` (sister rule)
- Master meta-discipline registry: `DOCS/DESIGN_PHILOSOPHY.md` § 11.5 (Mn entries — M4 codified 2026-05-18 as the IMPLEMENTATION-DETAIL layer extension)
- FoxML_Trader_v2 `CLAUDE.local.md` `feedback_compaction_degrades_treat_handoffs_as_hints.md` + `feedback_implementation_detail_blindspot_recovery_via_taxonomy.md`

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

### Mid-sprint audits (between sub-ships of the same sprint)

**Added v5.14.9 (post-field-test):** initial pattern fired PRE-SPRINT (before kickoff). v5.14.9 surfaced a SECOND firing point: BETWEEN SUB-SHIPS of the same sprint, when downstream sub-ships impact a new surface.

**Trigger criteria — fire mid-sprint audit when ANY of:**

- HIGH-RISK sub-ship just shipped (HMAC-chain-preservation work, hot-path migrations, structural refactors that downstream sub-ships build on). Verify the new structure doesn't have latent issues before propagating to next sub-ship.
- New pattern field-tested for the first time. Subsequent sub-ships will follow the pattern; audit verifies it's sound before propagation.
- Plan amendments may be needed before next sub-ship if findings emerge.
- Cross-cutting changes (registry extensions, X-macro changes affecting multiple files) where downstream sub-ships INHERIT the structure.
- Operator explicitly invites mid-sprint checks ("also run new checks if you need to or think its a good idea").

**Skip mid-sprint audit when:**

- Routine pattern-application sub-ship (subsequent application of an already-validated pattern; e.g., .F.1 after .F validated; .F.3 after .F.1 + .F.2 validated).
- Pure additive work (new tests, new docs, comments).
- Bug fixes with bounded scope.

**Suggestion format (operator policy from v5.14.9):**

1. Claude session presents the mid-sprint audit suggestion with 1-sentence rationale (what risk it would catch).
2. Claude recommends WHICH audits to run (typically 2 in parallel, like /dod-audit + /test-strength-audit; or /parity-check + /trace-deps if drift risk is the concern).
3. Claude waits for operator response before launching.

Operator retains decision authority + can also bring up audits independently. Mid-sprint audits should NOT be auto-triggered (friction); they ARE catching real issues at structural boundaries before downstream sub-ships inherit them.

**Validated 2026-05-10 (v5.14.9.F.2 HIGH-RISK ship):** mid-sprint audit pattern caught HIGH.1 + HIGH.2 findings PRE-CODING; GREEN post-coding. Confirmed manual mid-sprint audit pattern works.

Pattern documented in CLAUDE.local.md "suggest mid-sprint audits when work impacts downstream plans" rule.

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

Findings (synthesis: `plans/v5.14-foxml-port-and-maker/plan_checks/2026-05-09-v5.14.8-fresh-audits-synthesis.md`):
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

### Amendment-notice-on-stale-body is INSUFFICIENT (added 2026-05-14 from v5.15.5.F.4c audit)

When a previously-drafted plan has stale code samples invalidated by a post-draft architectural ship, **the standard practice was to add an amendment notice at the top while preserving the body for "scope intent."** This proved insufficient at the 5th Class 14 recurrence (`.F.4c` plan body's 6 fictional APIs).

**Failure mode:** a fresh-context coder reading top-down may copy body code samples verbatim before reaching/noticing the amendment notice block. The "scope intent" preservation argument loses to "first thing the reader sees is the literal stale sample."

**Going-forward rule (2026-05-14):** when amending a plan with stale code samples, **DELETE the stale body** — don't preserve-with-notice. The amendment note can REFERENCE what was removed (in a brief history section at the top) but must not display the lethal samples.

Plan amendment template:
```markdown
## Plan amendment history

- 2026-05-13: Original draft (pre-X ship; STALE samples).
- 2026-05-14: <X> ship invalidated body samples. Body REWRITTEN per <synthesis>; stale samples DELETED.
```

This applies to ALL plan amendments going forward; Class 14 recurrence prevention.

### Operator-policy on audit gate firing (CLAUDE.local.md rule)

Audit gate FIRES on:
- HIGH-RISK ships (wide blast radius; structural fix; wire-format-affecting)
- First application of a new pattern
- Cross-cutting changes (≥4 files; multiple subsystems)
- Cold-pickup from compaction-degraded handoff

Operator (Caramel) decides when to fire; not auto-triggered. Each fire produces a synthesis doc + consult phase before coding starts. Per `feedback_consult_on_audit_findings` memory.

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
