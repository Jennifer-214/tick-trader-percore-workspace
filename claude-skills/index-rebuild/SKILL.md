---
name: index-rebuild
description: Auto-regenerate index files (CLAUDE.md skill suite table / DESIGN_SPECS/README.md / DESIGN_SPECS/TAG_INDEX.md / etc.) from current frontmatter state. Walks all docs with frontmatter; aggregates by type/concern/tag/lifecycle; rewrites canonical index files. Eliminates manual maintenance of index drift.
type: skill
concern: workflow
audit_cadence: per-ship
tags: [doc-discipline, framework-discipline]
surface: []
sister_skills: [/find, /doc-create, /metadata-audit]
loads_dynamically: [DESIGN_SPECS/doc-frontmatter-convention.md, DESIGN_SPECS/doc-tag-vocabulary.md]
---

# /index-rebuild — Auto-regenerate doc-system indexes

## What this does

Walks all docs with YAML frontmatter; aggregates by type / concern / surface / lifecycle; rewrites canonical index files mechanically.

Eliminates the manual maintenance of:
- CLAUDE.md "Skill suite" table (auto-generated from SKILL.md frontmatter)
- DESIGN_SPECS/README.md (auto-generated from DESIGN_SPECS/*.md frontmatter)
- DESIGN_SPECS/TAG_INDEX.md (auto-generated tag → files reverse-lookup snapshot)
- Memory file index in MEMORY.md (auto-generated from memory/*.md frontmatter)

When a new spec/skill/memory lands, this skill regenerates the indexes — no manual edit of CLAUDE.md tables required.

## Invocation

- `/index-rebuild` — regenerate all indexes
- `/index-rebuild --target claude-md` — regenerate CLAUDE.md skill suite table only
- `/index-rebuild --target design-specs-readme` — regenerate DESIGN_SPECS/README.md only
- `/index-rebuild --target tag-index` — regenerate DESIGN_SPECS/TAG_INDEX.md snapshot
- `/index-rebuild --target memory` — regenerate MEMORY.md index
- `/index-rebuild --dry-run` — print proposed changes without writing

## Execution model

For each target index:

1. Walk source docs (e.g., `claude-skills/*/SKILL.md` for CLAUDE.md skill suite)
2. Parse YAML frontmatter from each
3. Aggregate by relevant axis (concern for skill suite; type+stage for DESIGN_SPECS README)
4. Compose new index content using template (see § Templates below)
5. Verify diff against existing index (catch unintended changes)
6. Write index file (or output diff if `--dry-run`)
7. Report: source count + index entries + diff summary

## Per-target rebuild logic

### `claude-md` — CLAUDE.md "Skill suite" table

Source: all `claude-skills/*/SKILL.md` with frontmatter
Group by: `concern:` field
Output table replaces existing "Skill suite (audit-driven discipline)" section

```markdown
## Skill suite (audit-driven discipline)

| Concern | Skills |
|---|---|
| Pre-coding plan verification | <list skills with concern: pre-coding-gate> |
| SHAPE audits (design-layer) | <list skills with concern: shape-audit> |
| IMPLEMENTATION-DETAIL audits | <list skills with concern: impl-detail-audit> |
| DOMAIN audits | <list skills with concern: domain-audit> |
| Anti-pattern scans | <list skills with concern: anti-pattern-scan> |
| Post-coding | <list skills with concern: post-coding> |
| Workflow | <list skills with concern: workflow> |
| Scaffolding | <list skills with concern: scaffolding> |
| Recurrence | <list skills with concern: recurrence> |
```

### `design-specs-readme` — DESIGN_SPECS/README.md catalog

Source: all `DESIGN_SPECS/*.md` with frontmatter
Group by: `type:` then `stage:`
Output: catalog table per type with lifecycle stage + tags + sister_specs count

```markdown
# DESIGN_SPECS catalog (auto-generated)

## refactor-pattern (N specs)
| Spec | Stage | Tags | Sister count |
|---|---|---|---|
| <path> | <stage> | <comma-separated-tags> | N |

## framework-pattern (N specs)
...
```

### `tag-index` — DESIGN_SPECS/TAG_INDEX.md (reverse lookup snapshot)

Source: all docs with frontmatter
For each tag in vocabulary: list files using that tag

```markdown
# Tag → files index (auto-generated snapshot)

## Concern tags

### framework-discipline (N files)
- DESIGN_SPECS/meta-registry-pattern.md
- DESIGN_SPECS/structural-fix-preferred-decision-framework.md
- ...

### audit-methodology (N files)
- ...

## Surface tags
...
```

This snapshot is regenerated; canonical reverse-lookup remains `rg "^tags:.*\b<tag>\b"`.

### `memory` — MEMORY.md index

Source: all `~/.claude/projects/.../memory/*.md` with frontmatter (excluding MEMORY.md itself)
Output: re-render MEMORY.md "Memory index" section preserving entry order + descriptions

## Auto-trigger at sprint close

`/ship` skill amends: at ship-close, fire `/index-rebuild` if any doc with frontmatter was created/modified this ship.

Optionally fire at CI pre-commit for ALL indexes; verifies indexes match current frontmatter state.

## Trade-offs + when to apply

### Apply when:
- Sprint close (after new docs land)
- After cohort migration (post-Phase 3 TECH_DEBT-115)
- When CLAUDE.md skill suite table feels stale
- Quarterly with `/metadata-audit` cadence

### Skip when:
- No frontmatter changes since last rebuild
- Mid-coding (rebuild at boundaries, not constantly)

## Pattern lifecycle

- **Stage 1 (problem):** manual maintenance of CLAUDE.md skill table + DESIGN_SPECS catalog risks drift
- **Stage 2 (DRAFT):** THIS SKILL (2026-05-18)
- **Stage 3 (first canonical):** queued at `.C` candidate ship after frontmatter cohort migration
- **Stage 4 (cohort):** all index regeneration mechanical; ship close auto-fire
- **Stage 5+ (cadence-locked):** CI integration; commit-time verification

## Cross-references

- Sister: `/find` (queries metadata; this skill maintains canonical indexes)
- Sister: `/doc-create` (creates new docs; this skill re-indexes after creation)
- Sister: `/metadata-audit` (audits metadata; this skill repairs index drift)
- Reference: `DESIGN_SPECS/doc-frontmatter-convention.md` (frontmatter schema)
- Reference: `DESIGN_SPECS/doc-tag-vocabulary.md` (canonical tag list)
- TECH_DEBT-115 Phase 2 (this skill lands at `.C` candidate ship)
