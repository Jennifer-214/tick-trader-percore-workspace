---
name: doc-create
description: Type-aware doc scaffolding. Asks for type (DESIGN_SPEC variant / postmortem / handoff / ledger entry / etc.) → uses appropriate template from DESIGN_SPECS/ → pre-fills frontmatter per doc-frontmatter-convention.md → opens editor at body. Prevents ad-hoc doc creation that lacks frontmatter or skips required sections.
type: skill
concern: scaffolding
audit_cadence: ad-hoc
tags: [doc-discipline, plan-template]
surface: []
sister_skills: [/plan-draft, /find, /metadata-audit]
loads_dynamically: [DESIGN_SPECS/design-spec-template.md, DESIGN_SPECS/postmortem-template.md, DESIGN_SPECS/sprint-master-plan-template.md, DESIGN_SPECS/future-oriented-plan-template.md, DESIGN_SPECS/ledger-entry-templates.md, DESIGN_SPECS/doc-frontmatter-convention.md, DESIGN_SPECS/doc-tag-vocabulary.md]
---

# /doc-create — Type-aware doc scaffolding

## What this does

Scaffolds new docs from canonical templates with frontmatter pre-filled. Prevents:
- Ad-hoc doc creation that skips frontmatter
- Wrong template usage (postmortem written as sub-plan, etc.)
- Frontmatter typos (validates tags against `doc-tag-vocabulary.md`)
- Missing required sections per template type

Composes templates from `DESIGN_SPECS/`:
- `design-spec-template.md` (type-aware DESIGN_SPEC scaffolding)
- `postmortem-template.md` (ship / incident / sprint variants)
- `sprint-master-plan-template.md` (sprint MASTER plan)
- `future-oriented-plan-template.md` (sub-plan with end-goal + plan-type)
- `ledger-entry-templates.md` (TECH_DEBT / Bug Class / PARITY / FEATURE / LANDMINE / HOT_PATH)

## Invocation

- `/doc-create <type>` — interactive scaffolding
- `/doc-create design-spec <pattern-name>` — DESIGN_SPEC variant
- `/doc-create postmortem <ship-tag>` — ship-postmortem
- `/doc-create handoff <ship-tag>` — delegates to `/handoff` skill
- `/doc-create plan-body <ship-tag>` — sub-plan from future-oriented-plan-template
- `/doc-create master-plan <sprint-name>` — sprint MASTER plan
- `/doc-create tech-debt <title>` — TECH_DEBT entry per ledger-entry-templates.md
- `/doc-create bug-class <title>` — RECURRING_BUG_PATTERNS Class N entry
- `/doc-create memory <title> <type>` — memory rule (feedback/user/project/reference)

## Type variants

| Type | Template used | Required fields collected |
|---|---|---|
| `design-spec` | `design-spec-template.md` | pattern-type / stage / tags / surface / sister_specs |
| `postmortem` | `postmortem-template.md` | postmortem-type / ship-tag-or-incident / related-plan |
| `plan-body` | `future-oriented-plan-template.md` | plan-type / sub_ship / sprint-master-path / ship-end-goal |
| `master-plan` | `sprint-master-plan-template.md` | sprint-name / sprint-end-goal / predecessor-sprint |
| `tech-debt` | `ledger-entry-templates.md § TECH_DEBT entry` | severity / surface_tags / trigger / related_specs |
| `bug-class` | `ledger-entry-templates.md § Bug Class entry` | severity / surface_tags / closure_mechanism |
| `parity-issue` | `ledger-entry-templates.md § Parity issue entry` | parity_axis / severity / detected_at |
| `feature-lookup` | `ledger-entry-templates.md § Feature lookup entry` | introduced-version / surface_tags |
| `landmine` | `ledger-entry-templates.md § Landmine entry` | severity / debug_hours / root_cause |
| `hot-path-changelog` | `ledger-entry-templates.md § Hot path changelog entry` | ship_tag / delta_ns / measurement_method |
| `memory` | (memory file frontmatter) | memory-type (feedback/user/project/reference) / surface tags |

## Execution model

1. Parse type + initial args
2. Load matching template from DESIGN_SPECS/
3. Interactive prompt for required fields (validate tags against `doc-tag-vocabulary.md`)
4. Substitute placeholders in template
5. Write to canonical filesystem path
6. (Optional) Open editor at body section
7. Cross-ref reciprocal: if `sister_specs: [X]`, optionally amend X's `sister_specs:` for bidirectional linking

## Filesystem path resolution

Per `doc-frontmatter-convention.md § Filesystem-path-to-type mapping`:

| Doc type | Target path |
|---|---|
| `design-spec` | `DESIGN_SPECS/<kebab-case-name>.md` |
| `postmortem` | `plans/<sprint>/postmortems/<YYYY-MM-DD>-<ship>-postmortem.md` |
| `plan-body` | `plans/<sprint>/subplans/<YYYY-MM-DD>-<version>-<name>.md` |
| `master-plan` | `plans/<sprint>/MASTER.md` |
| `tech-debt` | append to `DOCS/TECH_DEBT.md` (pre file-size split) OR `DOCS/tech-debt/<status>.md` (post-split) |
| `memory` | `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/<type>_<slug>.md` |

## Validation

Before writing:
- All `tags:` values exist in `doc-tag-vocabulary.md` CONCERN axis
- All `surface:` values exist in `doc-tag-vocabulary.md` SURFACE axis
- `type:` is valid per `doc-frontmatter-convention.md`
- `stage:` is one of 6 lifecycle values
- `sister_specs:` paths exist (call `check_doc_metadata.py --paths <new-doc>` post-write)

## Trade-offs + when to apply

### Apply when:
- Creating any new DESIGN_SPEC / postmortem / plan-body / ledger entry / memory rule

### Skip when:
- Hot-fix patch that doesn't add docs
- Trivial 1-pager (not cross-referenced)
- Editing existing doc (use Edit tool)

## Pattern lifecycle

- Stage 2 DRAFT: THIS SKILL (2026-05-18)
- Stage 3 first canonical: queued at `.C` candidate ship
- Stage 4+ cohort: widely used for all new doc creation

## Cross-references

- Reference: `DESIGN_SPECS/design-spec-template.md` (template for DESIGN_SPECS)
- Reference: `DESIGN_SPECS/postmortem-template.md` (template for postmortems)
- Reference: `DESIGN_SPECS/sprint-master-plan-template.md` (MASTER plan)
- Reference: `DESIGN_SPECS/future-oriented-plan-template.md` (sub-plan)
- Reference: `DESIGN_SPECS/ledger-entry-templates.md` (TECH_DEBT / Bug Class / PARITY entries)
- Reference: `DESIGN_SPECS/doc-frontmatter-convention.md` (frontmatter schema)
- Reference: `DESIGN_SPECS/doc-tag-vocabulary.md` (canonical tags)
- Sister skill: `/find` (queries metadata; this skill creates metadata)
- Sister skill: `/metadata-audit` (audits metadata; this skill produces valid metadata)
- Sister skill: `/plan-draft` (specific plan-body scaffolding)
- Sister skill: `/handoff` (specific handoff doc scaffolding)
- TECH_DEBT-115 Phase 2 (this skill lands at `.C` candidate ship)
