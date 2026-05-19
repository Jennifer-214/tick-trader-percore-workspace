---
type: plan-template
stage: 2-draft
version: 1.0
established: 2026-05-18
tags: [plan-template, doc-discipline]
surface: []
sister_specs: [doc-frontmatter-convention.md, future-oriented-plan-template.md, sprint-master-plan-template.md]
applies_at_skills: [/ship, /post-ship-audit]
---

# Postmortem template (type-aware)

**Established:** 2026-05-18 (v5.15.5.F.4d.1.B.3 doc-layer refresh)
**Status:** Stage 2 DRAFT v1.0 — Stage 3 first canonical at next post-ship postmortem

Type-aware postmortem template. Postmortems are currently ad-hoc; this codifies required sections per type.

---

## Type variants

| Type | Trigger | Required sections (beyond universal) |
|---|---|---|
| `ship-postmortem` | Post-sub-ship retrospective; auto-fired by `/ship` | What shipped + What worked + What didn't + Lessons + Auto-write entries |
| `incident-postmortem` | Post-incident (bug / regression / outage) | Root cause + Timeline + Detection mechanism + Fix + Prevention |
| `sprint-postmortem` | Post-sprint umbrella retrospective | Sprint goal vs delivered + Per-sub-ship retrospective + Patterns codified + Cohort analysis |

---

## Universal frontmatter

```yaml
---
type: postmortem
postmortem_type: ship-postmortem | incident-postmortem | sprint-postmortem
ship_or_incident: <ship-tag OR YYYY-MM-DD incident>
related_plan: <plan body path>
established: YYYY-MM-DD
tags: [postmortem, <other tags>]
surface: [<surface-tags>]
---
```

---

## ship-postmortem required sections

```markdown
# Postmortem: <ship-tag> — <ship name>

## What shipped
<Brief: what closed; what landed; verifiable acceptance criteria met>

## What worked
<What about the approach was right; bullet list>

## What didn't work
<What was harder / surprising / required pivots; bullet list>

## Lessons
<Categorical lessons; should drive memory rules / DESIGN_SPECs / TECH_DEBT entries>

## Auto-write entries (per CLAUDE.local.md auto-write contracts)
- TECH_DEBT entries opened: <list>
- TECH_DEBT entries closed: <list>
- DESIGN_SPECs landed (Stage 2 → 3): <list>
- DESIGN_SPECs amended: <list>
- Memory rules codified: <list>
- Bug class N codified: <Class N + entry>
- Meta-discipline Mn codified: <Mn + cross-ref>

## Acceptance criteria verification
<Each criteria from plan body → met? skipped? deferred?>

## Cross-references
- Plan body: <path>
- Predecessor postmortem: <path>
- Audit reports: <plan_checks paths>
```

---

## incident-postmortem required sections

```markdown
# Incident postmortem: <YYYY-MM-DD> — <short title>

## Root cause
<Why did this happen; 1-2 paragraphs>

## Timeline
<When detected; when diagnosed; when fixed; when verified>

## Detection mechanism
<How was the incident detected (test / audit / paper-test / live-trading observation / etc.)>

## Fix
<What changed; commits + ship-tag>

## Prevention
<What discipline / CI tool / audit catches this class going forward>

## Sister incidents
<Similar past incidents; pattern>

## Cross-references
- TECH_DEBT entries opened: <list>
- Bug class codified or amended: <Class N>
- DESIGN_SPECs landed: <list>
- LANDMINES.md entry (if 1+h debug effort): <yes/no>
```

---

## sprint-postmortem required sections

```markdown
# Sprint postmortem: <sprint-name>

## Sprint goal vs delivered
<Sprint end goal from MASTER plan vs what actually shipped>

## Per-sub-ship retrospective
<Summary table: sub-ship + end goal + delivered? + auto-write entries>

## Patterns codified during sprint
- DESIGN_SPECs landed (Stage 2 → 3): <list>
- DESIGN_SPECs promoted (Stage 3 → 5): <list>
- Memory rules codified: <list>
- Hard invariants H added: <list>
- Meta-disciplines Mn added: <list>
- Bug classes N codified: <list>

## Cohort analysis
<Cross-sub-ship patterns; recurring themes; sister lessons>

## Sprint-end verification
<Per MASTER plan acceptance criteria; met? deferred?>

## Next sprint candidates
<What surfaces remain for next sprint; cross-ref to MASTER queue>

## Cross-references
- MASTER plan: <path>
- All sub-ship postmortems: <list>
```

---

## Auto-fire from /ship skill (queued)

`/ship` skill (existing) should be amended to scaffold a `ship-postmortem` doc at ship-close. Per `feedback_plans_have_explicit_end_goal`, postmortem verifies acceptance criteria from plan body.

---

## Pattern lifecycle

- **Stage 1 (problem identification):** Caramel surfaced 2026-05-18 need for postmortem template
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC
- **Stage 3 (first canonical):** queued at next ship close
- **Stage 4 (cohort migration):** existing postmortems retrofit opportunistically
- **Stage 5-6:** when template is load-bearing + `/ship` skill auto-fires

---

## Cross-references

- Sister: `doc-frontmatter-convention.md`
- Sister: `future-oriented-plan-template.md` (plan body template; postmortem verifies)
- Sister: `sprint-master-plan-template.md` (MASTER plan; sprint postmortem verifies)
- Sister: `audit-driven-pre-coding-gate.md` (pre-coding audit; postmortem retrospectively reviews findings)
- Memory: `feedback_plans_have_explicit_end_goal.md`
- TECH_DEBT-115 (institutional-memory rollout)

---

**End of postmortem-template v1.0 DRAFT.**
