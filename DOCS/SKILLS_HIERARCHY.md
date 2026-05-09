# Skills Execution Model — One-Way Hierarchy

**Date established:** 2026-05-09
**Established after:** /readiness + /trace-deps + /parity-check
recursion-via-over-delegation incident (v5.14.1.G audit dispatch
spawned a subagent that tried to spawn nested subagents for each
skill it was told to apply, then defaulted to "monitor and wait"
when nesting failed).

---

## The model

```
LAYER 1: ORCHESTRATION (decides WHEN + spawns)
  Main Claude session, OR
  Another orchestrator skill (e.g., /sprint-recheck would live here)

  ↓ spawns ONE Explore subagent ↓

LAYER 2: EXECUTION (does the work)
  The spawned Explore subagent
  Reads skill spec(s) + applies checklist(s) INLINE
  Returns single combined report

  ✗ DOES NOT spawn further subagents
  ✓ Skills compose at this layer by REFERENCE, not by SPAWNING

NO LAYER 3 (flat composition)
```

## Why this model

**Problem the model prevents:** subagent reads `/trace-deps` spec which
says "Spawn an Explore subagent. The subagent: ..." → tries to spawn
nested → either nesting silently fails OR the agent waits indefinitely
for a subagent that never finishes → no work product → wasted dispatch.

**Solved by:** explicit "you ARE the executor" guidance at top of each
skill spec + per-skill `## Execution model` section pointing at this doc.

## Per-skill responsibilities

| Skill | Layer | Composition |
|---|---|---|
| `/readiness` | Layer 2 | May reference `/trace-deps` Step 6 inline |
| `/trace-deps` | Layer 2 | Standalone; may be referenced from `/readiness` Check 19 |
| `/parity-check` | Layer 2 | May reference `DOCS/PARITY_ISSUES.md` for known-issues lookup |
| `/plan-check` | Layer 2 | Already by-reference per its existing spec — applies `/readiness` checklist inline across N sub-plans |
| `/merge-scan` | Layer 2 | Standalone; reuse-opportunities scan |
| `/latency-track` | Layer 2 | Standalone; HOT_PATH_CHANGELOG entry drafting |

## Compose by-reference, not by-spawning

**By-reference example (correct):**

```
/readiness Check 19 deep-dive needs Class 18 mirror data-flow audit.
The /readiness subagent reads /trace-deps SKILL.md Step 6, applies
its procedure inline using its own read/grep tools, includes the
findings as a section in /readiness's report. ONE subagent runs.
ONE report returns.
```

**By-spawning example (wrong; creates recursion trap):**

```
/readiness subagent: "I need /trace-deps. Spawn a nested subagent
to run it." Nested spawn either fails or hangs. /readiness subagent
defaults to "wait for subagent reports to appear in plan_checks/".
No report ever gets written. Dispatch produces nothing.
```

## Orchestrator-side responsibilities

When dispatching from Layer 1:

1. **Be specific about what to invoke:** "Run /trace-deps + /readiness
   checklists on plan X; combine into one report" — explicit, no
   ambiguity about whether to spawn nested.
2. **Tell the subagent to use its OWN tools:** "Use your read/grep/bash
   tools to do the audit yourself; do NOT spawn nested subagents."
3. **Specify the output path:** Concrete file path for the report.
   Avoids the "audit returned only inline; report file not saved" trap.

## Auditing the hierarchy itself

If a future skill addition introduces Layer 3 (subagent spawning
sub-subagents), it violates this model. Call it out via
`/readiness` Check 22 (auto-trigger downstream re-audit) or as a
RECURRING_BUG_PATTERNS Class 18-style audit gap.

## Cross-references

- `claude-skills/readiness/SKILL.md` — has `## Execution model` section
- `claude-skills/trace-deps/SKILL.md` — has `## Execution model` section
- `claude-skills/parity-check/SKILL.md` — has `## Execution model` section
- `claude-skills/plan-check/SKILL.md` — already documents "by-reference
  composition" inline; sets the pattern
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 18 — sister concept (mirror
  plans missing data-flow dependencies); same family of "spec assumes
  something the executor doesn't validate" bugs
