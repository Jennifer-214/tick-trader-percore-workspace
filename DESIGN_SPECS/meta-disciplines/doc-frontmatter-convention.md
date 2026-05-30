---
type: meta-discipline
stage: 3-first-canonical
version: 1.1
established: 2026-05-18
tags: [doc-discipline, meta-discipline, framework-discipline]
surface: [registry]
sister_specs: [doc-tag-vocabulary.md, categorical-triggers-in-always-loaded-docs.md, design-spec-template.md]
applies_at_skills: []
---

# Universal YAML frontmatter convention

**Established:** 2026-05-18 (v5.15.5.F.4d.1.B.3 doc-layer refresh — codified after Caramel surfaced institutional-memory architecture vision)
**Status:** Stage 3 first-canonical v1.1 — landed `.E.0.4` (2026-05-29); the `### memory/*.md` schema goes first-canonical via the memory rollout (D-89 + TECH_DEBT-115)
**Cross-references:**
- Sister: `doc-tag-vocabulary.md` (the tag vocabulary this convention uses)
- Sister: `categorical-triggers-in-always-loaded-docs.md` (companion doc-discipline)
- Sister: `design-spec-template.md` (uses this convention as required frontmatter)
- Sister: `pattern-codification-lifecycle.md` (lifecycle field maps to Stage 1-6)
- CLAUDE.md § How to find anything (retrieval recipes assume this convention)

---

## Purpose

Universal discipline for YAML frontmatter on all docs > 50 lines OR cross-referenced from other docs. Makes:
- Retrieval mechanical (`rg "^type: refactor-pattern"` works because frontmatter is at top of every doc)
- Indexes auto-generatable (CI tool walks frontmatter to build CLAUDE.md skill table / DESIGN_SPECS README / etc.)
- Cross-refs bidirectionally verifiable (sister-doc linking)
- Drift detection mechanical (CI validates against `doc-tag-vocabulary.md`)

---

## Universal required fields (all doc types)

```yaml
---
type: <see per-doc-type table below>
stage: 1-problem | 2-draft | 3-first-canonical | 4-cohort | 5-claude-md | 6-cadence-locked
version: 1.0
established: YYYY-MM-DD
tags: [<concern-tags per doc-tag-vocabulary.md>]
surface: [<surface-tags per doc-tag-vocabulary.md>]
sister_specs: [<paths to related DESIGN_SPECS>]
---
```

- `type`: REQUIRED; one value from per-doc-type table below
- `stage`: REQUIRED (singular); one of 6 lifecycle stages
- `version`: REQUIRED; semver-style `X.Y` for spec body
- `established`: REQUIRED; ISO date YYYY-MM-DD
- `tags`: REQUIRED list (empty `[]` allowed if no concerns)
- `surface`: REQUIRED list (empty `[]` if no codebase surface)
- `sister_specs`: REQUIRED list (empty `[]` if first-of-kind)

---

## Per-doc-type extra fields

### DESIGN_SPECS/*.md
```yaml
type: refactor-pattern | feature-pattern | framework-pattern | audit-methodology | data-discipline | concurrency-pattern | wire-format-pattern | doc-discipline | meta-discipline | plan-template | ledger-template | architecture-overview
applies_at_skills: [/skill1, /skill2]  # which skills load this dynamically
```

### claude-skills/<skill>/SKILL.md
```yaml
type: skill
concern: pre-coding-gate | shape-audit | impl-detail-audit | domain-audit | anti-pattern-scan | post-coding | workflow | recurrence | scaffolding
audit_cadence: ad-hoc | per-ship | quarterly | post-codification
sister_skills: [/skill1, /skill2]
loads_dynamically: [DESIGN_SPECS/file.md, memory/file.md]
```

### memory/*.md

Memories use the **Claude Code harness-native** frontmatter (`name:` / `description:` / `metadata.type:` — the recall system reads these; never remove) PLUS doc-system fields nested **under `metadata:`** so they survive harness frontmatter rewrites (D-89). NOT the universal top-level `stage:`/`version:`/`surface:` block — a memory has no lifecycle stage.

```yaml
name: <type>_<slug>                  # = filename stem; feedback_/user_/project_/reference_
description: <one-line recall summary>    # harness recall relevance (load-bearing)
metadata:
  type: feedback | user | project | reference   # harness category (load-bearing)
  tags: [<concern-tags per doc-tag-vocabulary.md>]
  sister_specs: [<memory-filename | DESIGN_SPECS/path.md>, ...]   # unified: memory→memory AND memory→spec
```

- `tags:` + `sister_specs:` nest under `metadata:` (harness-durable). `check_doc_metadata`'s flat frontmatter parser surfaces them as top-level, so they validate with no parser change.
- `sister_specs:` is the SINGLE unified cross-link field (no separate `sister_memories:` — D-89 fork 2); resolved against BOTH the memory tree and `DESIGN_SPECS/`, bidirectional over both.
- Template: `DESIGN_SPECS/plan-templates/memory-template.md` (via `/doc-create memory`).
- Inline `[[filename]]` body links use the FILENAME form, not the `name:` slug (WH-1).

### DOCS/TECH_DEBT.md ENTRIES (per-entry frontmatter)
```yaml
id: TECH_DEBT-NNN
severity: low | medium | high
surface_tags: [<surface-tags from vocabulary>]
trigger: explicit-operator | next-maintenance-window | recurrence-count-N | sub-ship-Y | etc.
status: open | in-flight | closed
related_specs: [<DESIGN_SPECS paths>]
opened: YYYY-MM-DD
closed: YYYY-MM-DD  # only when status: closed
```

### plans/<sprint>/MASTER.md
```yaml
type: sprint-master
sprint: <sprint-name>
sprint_end_goal: <one-line statement>
status: draft | active | shipped | cancelled
in_flight_ship: <ship-tag or null>
predecessor_sprint: <previous-sprint-name>
```

### plans/<sprint>/subplans/*.md
```yaml
type: sub-plan
sub_ship: <ship-tag>
plan_type: refactor | feature | live-readiness | hotfix | mixed
sprint_master: plans/<sprint>/MASTER.md
ship_end_goal: <one-line statement>
predecessor_ship: <previous-ship-tag>
status: draft | active | mid-coding | shipped | postmortem
```

### plans/<sprint>/handoffs/*.md
```yaml
type: handoff
ship_tag: <ship-tag>
plan_type: refactor | feature | live-readiness | hotfix
sprint_end_goal: <one-line>
ship_end_goal: <one-line>
predecessor_handoff: <path or null>
required_reading: [<paths>]
coding_status: planning-complete | mid-coding-checkpoint-N | post-ship-postmortem
```

### plans/<sprint>/postmortems/*.md
```yaml
type: postmortem
postmortem_type: ship-postmortem | incident-postmortem | sprint-postmortem
ship_or_incident: <tag or date>
related_plan: <path>
```

### plans/<sprint>/plan_checks/*.md (audit reports)
```yaml
type: audit-report
audit_type: shape | implementation-detail | domain | anti-pattern
audit_skills: [/skill1, /skill2]  # which skills fired
target_plan: <plan-path>
severity: green | yellow | red
findings_count: N
```

### DOCS/RECURRING_BUG_PATTERNS.md entries (per-class frontmatter — sketch)
```yaml
class_id: N
title: <one-line>
surface_tags: [<surface>]
severity: blocker | high | medium | low
recurrence_count: N
first_instance: vX.Y.Z
closure_mechanism: <how this class is closed structurally>
sister_classes: [<class IDs>]
```

### DOCS/CLAUDE_*.md (split-load orientation)
```yaml
type: orientation-doc
load_trigger: <when to read this; categorical>
related_specs: [<paths>]
```

---

## Filesystem-path-to-type mapping (post folder restructure per TECH_DEBT-113)

After folder subdivision lands (TECH_DEBT-113), folder structure matches `type:` frontmatter:

| Folder | Frontmatter `type:` |
|---|---|
| `DESIGN_SPECS/refactor-patterns/` | `refactor-pattern` |
| `DESIGN_SPECS/framework-patterns/` | `framework-pattern` |
| `DESIGN_SPECS/audit-methodologies/` | `audit-methodology` |
| `DESIGN_SPECS/data-disciplines/` | `data-discipline` |
| `DESIGN_SPECS/concurrency-patterns/` | `concurrency-pattern` |
| `DESIGN_SPECS/wire-format-patterns/` | `wire-format-pattern` |
| `DESIGN_SPECS/doc-disciplines/` | `doc-discipline` |
| `DESIGN_SPECS/meta-disciplines/` | `meta-discipline` |
| `DESIGN_SPECS/plan-templates/` | `plan-template` |
| `DESIGN_SPECS/ledger-templates/` | `ledger-template` |

CI tool verifies frontmatter `type:` matches enclosing folder (drift detection).

---

## YAML frontmatter discipline rules

**Greppability:**
- Frontmatter STARTS at line 1 (between `---` markers)
- Each field on its own line for `rg "^<field>:"` queries
- Lists on single line: `tags: [tag1, tag2, tag3]` — greppable per element via `rg "^tags:.*\btag1\b"`
- Avoid multi-line YAML lists in always-loaded docs (breaks per-line greppability)

**Stability:**
- Field names are STABLE — don't rename without `/metadata-audit` sweep
- `type:` values are STABLE — extending requires amending `doc-tag-vocabulary.md`
- Lifecycle stages STABLE (1-problem through 6-cadence-locked)

**Bidirectional sister linking:**
- If doc A has `sister_specs: [B]`, doc B MUST have `sister_specs: [A]`
- CI tool verifies bidirectional
- Broken links detected by `/metadata-audit`

**Validation:**
- All `tags:` values MUST exist in `doc-tag-vocabulary.md` CONCERN axis
- All `surface:` values MUST exist in `doc-tag-vocabulary.md` SURFACE axis
- `stage:` MUST be one of 6 lifecycle stages
- `type:` MUST be one of the per-doc-type values

---

## Migration order (per TECH_DEBT-115 phases)

**Phase 1 (`.C` candidate ship — first canonical):**
- Land THIS DOC + `doc-tag-vocabulary.md` + `design-spec-template.md` + `postmortem-template.md` at Stage 3
- 5-10 high-traffic DESIGN_SPECS get frontmatter (canonical demonstrations)
- CI tool `check_doc_metadata.py` lands (validates frontmatter at commit)

**Phase 2 (`.D` candidate ship — cohort migration):**
- All 80+ DESIGN_SPECS migrate to frontmatter (Stage 4 cohort)
- 30 SKILL.md files get frontmatter (CLAUDE.md skill suite auto-generates)
- TECH_DEBT entries get YAML frontmatter
- Folder subdivision per TECH_DEBT-113 (folder = type)

**Phase 3 (`.E` candidate ship — auto-flow):**
- `/index-rebuild` skill builds CLAUDE.md tables + DESIGN_SPECS/README from frontmatter
- `/metadata-audit` skill quarterly cadence
- `/find` skill natural-language → metadata-filtered grep
- `/doc-create` skill type-aware scaffolding

---

## Cross-references

- Sister: `doc-tag-vocabulary.md` (the tag vocabulary this convention uses)
- Sister: `categorical-triggers-in-always-loaded-docs.md` (the doc-discipline this enables)
- Sister: `design-spec-template.md` (uses this frontmatter convention)
- Sister: `postmortem-template.md` (uses this frontmatter convention)
- Sister: `sprint-master-plan-template.md` (uses this frontmatter convention)
- Sister: `future-oriented-plan-template.md` (uses this frontmatter convention)
- TECH_DEBT-115 (institutional-memory rollout)
- TECH_DEBT-113 (folder subdivision pairs with this convention)
- Memory: `feedback_categorical_triggers_over_hardcoded_refs.md`
- Memory: `feedback_claude_md_guidelines_not_stuff_to_do.md`
- CLAUDE.md § How to find anything (retrieval guide assumes this convention)

---

## Pattern lifecycle

- **Stage 1 (problem identification):** Caramel surfaced 2026-05-18 institutional-memory architecture vision
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-18)
- **Stage 3 (first canonical):** LANDED `.E.0.4` (2026-05-29) — 80+ DESIGN_SPECS carry frontmatter + the `### memory/*.md` schema first-canonical via the memory rollout (D-89)
- **Stage 4 (cohort migration):** queued at `.D` candidate ship — 80+ DESIGN_SPECS + 30 SKILL.md + TECH_DEBT YAML
- **Stage 5 (CLAUDE.md promotion):** ALREADY landed — CLAUDE.md § How to find anything references this convention
- **Stage 6 (cadence-locked):** CI tool + `/metadata-audit` quarterly enforce

---

**End of doc-frontmatter-convention v1.0 DRAFT.** Stage 3 first canonical queued at `.C` candidate ship.
