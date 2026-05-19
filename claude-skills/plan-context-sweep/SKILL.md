---
name: plan-context-sweep
description: Light-weight orchestrator that fires /bug-check (against plans/) + /trace-deps in parallel against ALL queued plans in a sprint. Use case — after structural-fix ship lands, sweep all downstream plans for stale code samples that would reintroduce just-closed bug class. Returns plan-by-plan amendment recommendations. Lighter variant of /precoding-audit-gate (2 audits vs 5; sweeps all queued plans vs single plan focus). Dynamic parameterization — sprint_path (default = current sprint via Version.hpp) + bug_class_focus (optional; e.g., "Class 23" to focus sweep on specific anti-pattern). NO hardcoded sprint/version refs.
type: skill
concern: workflow
audit_cadence: post-codification
tags: [audit-methodology, structural-fix, plan-template]
surface: []
sister_skills: [/bug-check, /trace-deps, /precoding-audit-gate, /plan-check]
loads_dynamically: [DOCS/RECURRING_BUG_PATTERNS.md]
---

# /plan-context-sweep — Sweep queued plans for stale samples post-structural-fix

## What this does

When a structural-fix ship lands (e.g., v5.15.5.F.4b's 3-barrier Class 23
fix), downstream plans drafted in the prior era may have STALE code samples
that would REINTRODUCE the just-closed bug class. This skill fires
`/bug-check` (extended to scan plans/) + `/trace-deps` (plan-vs-code) in
parallel against ALL queued plans in the sprint, correlates findings,
and returns plan-by-plan amendment recommendations.

**This skill DOES execute audits via subagent dispatch.** It does NOT
modify plans (operator decides amendments). Output is a sweep report at
`plans/plan_checks/<YYYY-MM-DD>-plan-context-sweep.md`.

## When to fire

- **After structural-fix ship lands** — primary use case. Just-closed bug
  class might still appear as code samples in queued plans drafted pre-fix.
  Example: after any structural Class N fix lands → fire this skill to
  verify queued downstream sub-ships don't have anti-pattern code samples
  for the same class.
- **After API surface change** — function rename / signature change in a
  shipped ship; downstream plans may reference the old API. Fire to detect.
- **Sprint pivot** — operator priority shift; verify queued plans still
  align with current direction.
- **Pre-handoff** — confirm queued plans are cold-pickup-ready before
  generating a handoff prompt.

**Skip when:** no recent structural fix; no API surface change; sprint
just started (no queued plans yet).

## Invocation

```
/plan-context-sweep [sprint_path] [bug_class_focus]
```

**Args:**

- `sprint_path` (OPTIONAL; default = current sprint auto-detected from
  Version.hpp) — workspace path to sprint dir (e.g., `plans/v5.15-live-readiness`)
- `bug_class_focus` (OPTIONAL) — narrow `/bug-check` scan to specific Class N
  (e.g., `"Class 23"` after the .F.4b fix). If omitted, runs all classes.

**Examples:**

```
# Default — sweep current sprint with all bug classes:
/plan-context-sweep

# Focus on Class 23 only (post-.F.4b sweep):
/plan-context-sweep plans/v5.15-live-readiness "Class 23"

# Different sprint (uncommon):
/plan-context-sweep plans/v5.16-decoupling
```

**Verdict:** GREEN (all queued plans clean) / YELLOW (≤2 plans need light
amendment) / RED (≥3 plans need heavy amendment OR critical anti-pattern
reintroduction in any plan).

## Execution model — Layer 1 orchestrator

```
LAYER 1: ORCHESTRATION (this skill)
  - Auto-detect sprint via Version.hpp parse
  - List sprint's subplans/ + handoffs/
  - Spawn 2 subagents per plan in parallel:
    * /bug-check subagent (scans plan against RECURRING_BUG_PATTERNS)
    * /trace-deps subagent (scans plan-vs-code function existence)
  - Wait for all (2 × N_plans) subagents
  - Correlate findings + write sweep report
  - Return plan-by-plan amendment recommendations

LAYER 2: EXECUTION (subagents)
  - Each subagent reads its target SKILL.md + executes against single plan
  - Returns per-plan finding summary

LAYER 3: FORBIDDEN (no nested subagents)
```

## Pass structure

### Stage 1 — Auto-detect sprint + enumerate queued plans

1. Read engine `Version.hpp` `ENGINE_VERSION_STRING` (e.g., `5.15.5.F.4b`)
2. Derive sprint dir via glob `plans/v<major>.<minor>-*/` (single match required)
3. List `plans/<sprint>/subplans/*.md` (queued sub-ship plans)
4. List `plans/<sprint>/handoffs/*.md` (cold-pickup prompts)
5. Filter by status:
   - Skip plans for SHIPPED versions (e.g., if Version.hpp = 5.15.5.F.4b, skip .F.4a + .F.4b plans)
   - Sweep only plans for FUTURE sub-ships (.F.4c onwards in current state)
6. Optional: respect operator's `sprint_path` arg override

### Stage 2 — Read source docs (DYNAMIC)

| Source | Used by |
|---|---|
| `DOCS/RECURRING_BUG_PATTERNS.md` | `/bug-check` subagents (which classes to scan for) |
| Engine `CLAUDE.md` (slim) | Hard invariants reference |
| `DOCS/DESIGN_PHILOSOPHY.md` | Family sections that match anti-pattern detection |
| Engine `Version.hpp` + `git log -10` | Recent ship state (what just landed; what might be stale) |
| `CLAUDE.local.md` Sprint State Tracker | Most-recent ship + open architectural decisions |

### Stage 3 — Spawn 2 × N_plans subagents in parallel

For each queued plan, spawn 2 subagents:

**Subagent A — /bug-check against this plan:**
```
Run /bug-check skill against plan: <plan_path>

CONTEXT:
- Skill spec: workspace/claude-skills/bug-check/SKILL.md (READ FIRST;
  ensure plans/ scope-extension is honored per Stage 1.5 of /bug-check spec)
- Bug class focus: <bug_class_focus> (or "all classes" if unset)
- Recently-shipped structural fix to watch: <recent_fix_summary>

Walk RECURRING_BUG_PATTERNS.md Detection signatures against the plan body.
Flag any anti-pattern reintroductions.

OUTPUT: per-plan finding summary (under 300 words):
- Class N detections (with line refs in plan)
- Severity (CRITICAL = anti-pattern code sample; HIGH = stale function ref;
  MED = stale baseline number; LOW = note)
- Recommended fix (light context note vs heavy code-sample invalidation)
```

**Subagent B — /trace-deps against this plan:**
```
Run /trace-deps skill against plan: <plan_path>

CONTEXT:
- Skill spec: workspace/claude-skills/trace-deps/SKILL.md (READ FIRST)
- Cross-reference plan claims against current shipped API at HEAD = <git_sha>

Detect plan references to functions / structs / fields that don't exist
in current codebase. Especially check for fictional function names that
may have been "rolled back" by a structural fix.

OUTPUT: per-plan finding summary (under 300 words):
- Missing function refs (file:line in plan + grep verification)
- Stale signature drift
- Recommended fix
```

All `2 × N` subagents fire in **parallel** via single tool-use message
with multiple Agent calls. NOT sequential.

### Stage 4 — Correlate + write sweep report

After all subagents return, orchestrator writes:

`plans/plan_checks/<YYYY-MM-DD>-plan-context-sweep.md`

Report structure:

```markdown
# Plan context sweep — <YYYY-MM-DD>

**Trigger:** <reason for sweep — e.g., "post-v5.15.5.F.4b ship">
**Sprint:** <sprint_path>
**Plans swept:** <N_plans>
**Combined verdict:** GREEN / YELLOW / RED

## Per-plan findings

| Plan | Bug-check finding | Trace-deps finding | Recommended action |
|---|---|---|---|
| .F.4c | CRITICAL Class 23 (5 reinterpret_cast samples) | HIGH (4 fictional fns) | HEAVY context-correction notice |
| .F.4d | MED Class 23 (6 void* signatures) | LOW (none) | MEDIUM notice |
| ... | ... | ... | ... |

## Detailed findings (per plan that has issues)
[Per-plan section with specific line refs + recommended fix language]

## Recommended sweep amendment plan
1. Heavy amendment: <plans>
2. Light amendment: <plans>
3. No-op: <plans>

## Cross-references
- Recently-shipped structural fix: <ship>
- DESIGN_PHILOSOPHY § N (relevant family)
- RECURRING_BUG_PATTERNS Class N (the anti-pattern detected)
```

### Stage 5 — Return verdict to operator

Print sweep report location + verdict + per-plan amendment summary.
**Do NOT auto-amend plans** — operator reviews + decides.

## Distinct from sister skills

| Skill | Scope | Relationship |
|---|---|---|
| `/precoding-audit-gate` | Full 5-audit fire against ONE plan | Sister Layer 1 orchestrator (heavier scope per plan; single plan target) |
| `/bug-check` | Single bug class scan against codebase OR plans | LAYER 2 child fired per-plan by this orchestrator |
| `/trace-deps` | Plan-vs-code function existence | LAYER 2 child fired per-plan |
| `/handoff` | Pickup prompt generation | Sister Layer 1; `/handoff` may invoke this skill as part of pre-pickup verification |
| `/readiness` | Plan completeness 28-check | Orthogonal — `/readiness` is single-plan deep verify; this skill is multi-plan shallow sweep |

## When to skip

- No recent structural-fix ship + no API surface change + sprint just started
- Single-plan focus (use `/precoding-audit-gate` instead — heavier per-plan)
- Sweep already run today (cache check via existing `plans/plan_checks/<YYYY-MM-DD>-plan-context-sweep.md`)

## Cost model

- Per-plan: 2 subagents × ~3-5 min wall clock = 5-10 min
- For sprint with N=8 queued plans: 16 subagents in parallel ≈ 10 min wall clock + 5 min synthesis
- **Total: ~15 min wall clock; ~80K tokens across all subagents combined**

vs alternative (manual sweep): I did this manually 2026-05-14 across 8 plans
in ~45 min. Skill saves ~30 min per sweep + provides repeatable structured
output.

## Anti-patterns to avoid

- ❌ Hardcoding sprint name or version refs. Auto-detect via Version.hpp.
- ❌ Auto-amending plans. Skill is observation-only.
- ❌ Spawning Layer 3 subagents.
- ❌ Re-running on plans already amended (check for amendment-notice marker
      at top of each plan; skip if found within last 7 days).
- ❌ Sweeping ALREADY-SHIPPED plans (only future sub-ships matter for staleness).

## Cross-references

- `tick-trader-percore-workspace/DOCS/DESIGN_PHILOSOPHY.md` § 11 (Process discipline)
- `tick-trader-percore-workspace/CLAUDE.local.md` going-forward rule "Verify handoffs against current code"
- Engine memory `feedback_compaction_degrades_treat_handoffs_as_hints`
- Past plan context sweep: 2026-05-14 v5.15.5.F.4b+ session (manual sweep across 8 plans; this skill formalizes that process)
