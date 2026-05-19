---
name: find
description: Natural-language metadata-filtered search over the doc system. Translates query into rg patterns against YAML frontmatter (type / tags / surface / stage / sister_specs). Composes from DESIGN_SPECS/doc-tag-vocabulary.md + doc-frontmatter-convention.md. Output: list of matching files with path + type + relevant tags + brief excerpt.
type: skill
concern: workflow
audit_cadence: ad-hoc
tags: [doc-discipline]
surface: []
sister_skills: [/doc-create, /metadata-audit, /index-rebuild]
loads_dynamically: [DESIGN_SPECS/doc-tag-vocabulary.md, DESIGN_SPECS/doc-frontmatter-convention.md]
---

# /find — Metadata-filtered doc retrieval

## What this does

Translates natural-language query → metadata-filtered grep over doc system frontmatter. Returns matching files with path + type + relevant tags + brief excerpt.

Composes from `DESIGN_SPECS/doc-tag-vocabulary.md` (canonical tag list) + `DESIGN_SPECS/doc-frontmatter-convention.md` (frontmatter schema). The skill IS the operationalization of CLAUDE.md § How to find anything — grep recipes wrapped in natural language interface.

## Invocation

- `/find <query>` — natural-language query over doc system metadata
- `/find <query> --paths <root>...` — limit search to specific roots (default: DESIGN_SPECS/ + claude-skills/ + DOCS/)
- `/find <query> --type <type>` — filter by frontmatter type
- `/find <query> --stage <stage>` — filter by lifecycle stage

Examples:
- `/find specs about wire format byte preservation`
- `/find audit methodology specs at stage 2-draft`
- `/find skills that load DESIGN_SPECS/structural-fix-preferred-decision-framework`
- `/find Stage 2 DRAFTs older than 6 months` (lifecycle + date filter)

## Execution model

1. Parse natural-language query
2. Identify CONCERN tags / SURFACE tags / TYPE values from query keywords
3. Map keywords to canonical tag vocabulary (consult `DESIGN_SPECS/doc-tag-vocabulary.md`)
4. Compose `rg` patterns combining matched tags
5. Execute searches in parallel
6. Aggregate results; rank by tag-match count
7. Output: file paths + frontmatter type + matching tags + brief context excerpt

## Mapping keywords → canonical tags

| User keyword | Canonical tag |
|---|---|
| "wire format" / "byte preservation" / "HMAC" / "stamp" | surface:wire-format + tags:wire-format |
| "hot path" / "tick" / "branchless" | surface:hot-path + tags:branchless-discipline |
| "audit" / "audit methodology" | tags:audit-methodology |
| "framework" / "X-macro" / "registry" | tags:framework-discipline + surface:registry |
| "doc" / "documentation" / "docs" | tags:doc-discipline |
| "concurrency" / "thread" / "false-sharing" / "SPSC" / "seqlock" | tags:concurrency + surface based on subject |
| "DOD" / "data-oriented" / "alignas" / "cache" | tags:data-oriented-design |
| "plan" / "template" / "MASTER" / "sub-plan" | tags:plan-template |
| "TECH_DEBT" / "ledger" / "PARITY_ISSUES" | tags:ledger-discipline |
| "operator" / "collaboration" / "feedback" | tags:operator-collaboration |
| "structural fix" / "bug class" | tags:structural-fix |

## Output format

```
Found N matches:

1. <path>
   type: <type>
   tags: [<matching tags>]
   surface: [<matching surfaces>]
   excerpt: "<first matching paragraph or section header>"

2. <path>
   ...
```

If no matches: `No matches for "<query>"; consider broader terms or check `doc-tag-vocabulary.md`.`

## Trade-offs + when to apply

### Apply when:
- Searching for doc by topic / surface / discipline
- Cold-pickup discovery of relevant patterns
- Building context for a planning session
- Auditing what's queued at each lifecycle stage

### Skip when:
- Exact file path known (use Read directly)
- Looking for catalog ID (Class N / H N / TECH_DEBT-NNN — direct grep faster)
- Browsing the catalog README (use Read)

## Pattern lifecycle

- **Stage 1 (problem):** finding-issues with hardcoded refs surfaced 2026-05-18
- **Stage 2 (DRAFT):** THIS SKILL spec (2026-05-18) at `.B.3` doc-layer refresh
- **Stage 3 (first canonical):** queued at next operator-invocation
- **Stage 4 (cohort):** widely used after frontmatter cohort migration completes
- **Stage 5 (mature):** integrated into /handoff dynamic load + /readiness Check 30 verification

## Cross-references

- Sister: `/doc-create` (creates new docs; this skill finds existing)
- Sister: `/metadata-audit` (audits metadata; this skill queries metadata)
- Sister: `/index-rebuild` (regenerates indexes; this skill uses indexes)
- Reference: `DESIGN_SPECS/doc-tag-vocabulary.md` (canonical tag list)
- Reference: `DESIGN_SPECS/doc-frontmatter-convention.md` (frontmatter schema)
- Reference: CLAUDE.md § How to find anything (grep recipes)
- TECH_DEBT-115 Phase 2 (this skill lands at `.C` candidate ship)
