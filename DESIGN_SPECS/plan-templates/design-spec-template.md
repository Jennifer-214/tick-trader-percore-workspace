---
type: plan-template
stage: 2-draft
version: 1.0
established: 2026-05-18
tags: [plan-template, doc-discipline, framework-discipline]
surface: []
sister_specs: [doc-frontmatter-convention.md, doc-tag-vocabulary.md, pattern-codification-lifecycle.md]
applies_at_skills: [/doc-create]
---

# DESIGN_SPEC template (type-aware)

**Established:** 2026-05-18 (v5.15.5.F.4d.1.B.3 doc-layer refresh — codified after Caramel surfaced need for DESIGN_SPEC template with type metadata)
**Status:** Stage 2 DRAFT v1.0 — Stage 3 first canonical at `.C` candidate ship (5-10 new DESIGN_SPECS use this template)
**Cross-references:**
- Sister: `doc-frontmatter-convention.md` (frontmatter discipline)
- Sister: `doc-tag-vocabulary.md` (tag vocabulary)
- Sister: `pattern-codification-lifecycle.md` (Stage 1-6 lifecycle)
- Sister: `future-oriented-plan-template.md` (parallel pattern; plan body template)

---

## Purpose

Type-aware DESIGN_SPEC template. Different type → different required sections. Single template body; type metadata drives section dispatch.

Avoids ad-hoc section structure across 80+ DESIGN_SPECS. New docs scaffold from this template via `/doc-create <type>` (queued skill).

---

## Type variants

| Type | Trigger | Required sections (beyond universal) |
|---|---|---|
| `refactor-pattern` | Pattern that closes a bug class structurally | Problem + Discipline + 3-bucket rubric + Worked example + Pattern lifecycle |
| `feature-pattern` | Pattern for adding NEW capability | Capability + Interface + Implementation shape + Acceptance criteria |
| `framework-pattern` | Framework infrastructure (X-macro registry, auto-flowing dispatch, etc.) | Framework infrastructure + Consumer API + Auto-flow mechanics + Audit detection + Pattern lifecycle |
| `audit-methodology` | Audit shape (M1-M4 family) | Audit shape + Detection signatures + Trigger conditions + Output format + Skill cross-refs |
| `data-discipline` | DOD-flavored layout/alignment/cache rules | Layout rules + Access patterns + Alignment requirements + SIMD parity considerations + Audit detection |
| `concurrency-pattern` | Thread isolation, sync primitives | Thread isolation + Sync primitive + Visibility rules + Sister patterns |
| `wire-format-pattern` | Byte preservation, locale pinning | Byte-equivalence requirements + Locale pinning + Layer 5b discipline + Replay determinism |
| `doc-discipline` | Doc-layer separation, frontmatter, tags | Discipline statement + 3-bucket rubric (if applicable) + Drift detection + Migration order |
| `meta-discipline` | Audit-methodology-gap codification (M-codes) | Trigger condition + Recognition signal + Codification procedure + Sister meta-disciplines + DESIGN_PHILOSOPHY § 11.5 cross-ref |
| `plan-template` | MASTER / sub-plan / handoff / postmortem templates | Required sections + Type variants + How to use + Trade-offs |
| `ledger-template` | TECH_DEBT / PARITY / FEATURE entry shape | Per-entry frontmatter + Required body sections + Auto-write contracts + Cross-ref discipline |
| `architecture-overview` | High-level engine architecture | Component overview + Data flow diagram + Sub-system pointers + Cross-refs to canonical sources |

---

## Universal sections (every DESIGN_SPEC has these)

### Frontmatter (REQUIRED)

```yaml
---
type: <one of above>
stage: 1-problem | 2-draft | 3-first-canonical | 4-cohort | 5-claude-md | 6-cadence-locked
version: <X.Y>
established: <YYYY-MM-DD>
tags: [<concern-tags>]
surface: [<surface-tags>]
sister_specs: [<paths>]
applies_at_skills: [<skill-paths>]
---
```

Per `doc-frontmatter-convention.md`.

### Title + Established + Status (REQUIRED)

```markdown
# <Pattern Name>

**Established:** <YYYY-MM-DD> (<context>)
**Status:** Stage N v.X.Y — <one-line status>
**Cross-references:**
- Sister: <path>
- ...
```

### Purpose / Problem statement (REQUIRED)

What this spec is solving / codifying. 2-4 paragraphs.

### Pattern lifecycle (REQUIRED)

Stage 1-6 progression per `pattern-codification-lifecycle.md`:

```markdown
## Pattern lifecycle

- **Stage 1 (problem identification):** <when + how problem surfaced>
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (<date>)
- **Stage 3 (first canonical):** <first ship/codebase application>
- **Stage 4 (cohort migration):** <when cohort applies the pattern>
- **Stage 5 (CLAUDE.md promotion):** <when promoted to CLAUDE.md item / H invariant>
- **Stage 6 (cadence-locked):** <periodic audit + CI tool enforcement>
```

### Cross-references (REQUIRED)

```markdown
## Cross-references

- Sister: <DESIGN_SPECS path>
- Memory: <memory file path>
- TECH_DEBT-NNN: <entry>
- CLAUDE.md § N: <section>
```

---

## Type-specific required sections

### refactor-pattern

```markdown
## Problem statement
<What pattern is solving; what bug class can recur if not codified>

## The discipline
<The rule; 1 paragraph>

## 3-bucket rubric (if classifying things)
| Bucket | Description | Examples |
|---|---|---|
| A | <criteria> | <examples> |
| B | <criteria> | <examples> |
| C | <criteria> | <examples> |

## Worked example
<Canonical first-of-kind application; ship + date + outcome>

## Trade-offs + when to apply

### Apply when:
- <conditions>

### Skip when:
- <conditions>

### Cost: <estimate>
### Win: <expected outcome>

## Lessons / gotchas
<Edge cases; common drift; corrections>
```

### framework-pattern

```markdown
## Problem statement
<What recurrence the framework prevents>

## Framework infrastructure
<X-macro registry / auto-flowing dispatch / etc.>

## Consumer API
<How code USES the framework — single-row addition, walker macro, etc.>

## Auto-flow mechanics
<What auto-flows when row added — parser + GUI + tooltip + per-core override emission etc.>

## Audit detection
<How to detect drift; CI tool / `/anti-spaghetti` / etc.>

## Migration order (if cohort applies)
<Phased application across codebase>

## Cross-references
<...>
```

### audit-methodology

```markdown
## Audit shape
<What this audit looks for>

## Detection signatures
<Code/doc patterns that trigger findings>

## Trigger conditions
<When to fire this audit; sub-ship phase + risk category>

## Output format
<Standardized finding structure>

## Skill cross-refs
<Which skill(s) implement this methodology>

## Sister methodologies
<Other audits with overlapping concerns>
```

### data-discipline

```markdown
## Layout rules
<Field ordering, alignas requirements, padding discipline>

## Access patterns
<Hot reads vs hot writes vs cold init vs cross-thread — clustering rationale>

## Alignment requirements
<H6 alignas(64) for cross-thread; cache-line discipline>

## SIMD parity considerations
<H10 scalar fallback requirement; bytewise-identical output>

## Audit detection
<How to verify discipline upheld>

## Worked example
<Canonical struct demonstrating discipline>
```

### concurrency-pattern

```markdown
## Thread isolation
<Which threads access what state>

## Sync primitive
<Lock-free queue / seqlock / atomic flag / etc. — choice rationale>

## Visibility rules
<Acquire/release semantics; happens-before; memory ordering>

## Sister patterns
<Adjacent concurrency disciplines>

## Anti-patterns (NEVER)
<What violates H1-H3>
```

### wire-format-pattern

```markdown
## Byte-equivalence requirements
<H9 wire byte preservation; what must roundtrip byte-identical>

## Locale pinning
<H4 locale-independent emit; canonical formatting>

## Layer 5b discipline (if applicable)
<Hash chain ordering; HMAC input shape>

## Replay determinism
<Cross-run / cross-binary byte equivalence>

## Sister patterns
<Adjacent wire-format disciplines>
```

### doc-discipline

```markdown
## Discipline statement
<The rule>

## 3-bucket rubric (if applicable)
<A KEEP / B KEEP-WITH-FRAMING / C CONVERT style>

## Drift detection
<How drift surfaces; periodic audit cadence>

## Migration order (if cohort applies)
<Phased application across docs>

## Lessons / gotchas
<Edge cases>
```

### meta-discipline

```markdown
## Trigger condition
<When this meta-discipline fires; recognition signal>

## Recognition signal
<What pattern in audit findings surfaces this gap>

## Codification procedure
<How to write up a new Mn entry per DESIGN_PHILOSOPHY § 11.5>

## Sister meta-disciplines
<Other M-codes with overlapping concerns>

## DESIGN_PHILOSOPHY § 11.5 cross-ref
<Where this M-code lives in the meta-discipline registry>
```

### plan-template

```markdown
## Template body
<The template content for copy-paste>

## Type variants
<Different plan types → different required sections>

## How to use the template
<For new plan creation + retrofitting + skill invocation>

## Trade-offs + when to apply
<Apply when / skip when / cost / win>

## Lessons / gotchas
<Edge cases>
```

### ledger-template

```markdown
## Per-entry frontmatter
<YAML schema>

## Required body sections
<Required fields beyond frontmatter>

## Auto-write contracts
<When entries get added/updated>

## Cross-ref discipline
<Related entries / specs / memories>
```

### architecture-overview

```markdown
## Component overview
<Top-level engine components>

## Data flow diagram
<ASCII diagram showing tick → decision flow>

## Sub-system pointers
<Where each component lives + canonical sources>

## Cross-refs
<Per-invariant + per-discipline references>
```

---

## How to use the template

### For NEW DESIGN_SPEC creation:

1. Pick `type:` based on what's being codified
2. Copy this template
3. Fill universal sections (frontmatter + title + status + purpose + lifecycle + cross-refs)
4. Fill type-specific sections per type-variants table above
5. Mark `stage: 2-draft`
6. Add to `tags:` per `doc-tag-vocabulary.md` CONCERN axis
7. Add to `surface:` per `doc-tag-vocabulary.md` SURFACE axis (empty `[]` if no codebase surface)
8. Add `sister_specs:` pointing to related specs
9. (When first canonical application lands) update `stage: 3-first-canonical`

### For `/doc-create <type>` invocation (queued skill):

The `/doc-create` skill scaffolds this template + asks for:
- Pattern name
- Type
- Initial tags + surface
- Sister specs

Pre-fills frontmatter + opens editor at body sections.

---

## Trade-offs + when to apply

### Apply when:
- Drafting a new DESIGN_SPEC for any codified pattern
- Retrofitting older DESIGN_SPEC during periodic audit

### Skip when:
- Trivial 1-pager that doesn't warrant cross-referencing
- Internal-only design notes (use `plans/<sprint>/` instead)

### Cost: ~10-15 min initial draft using template; ~30 min retrofit per existing spec
### Win: Required sections impossible to forget; frontmatter mechanical; `/doc-create` skill scaffolds

---

## Pattern lifecycle

- **Stage 1 (problem identification):** Caramel surfaced 2026-05-18 — "do we need like a DESIGN_SPEC template? with like type of design [refactor, feature, framework, etc]?"
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-18)
- **Stage 3 (first canonical):** queued at `.C` candidate ship — 5-10 new DESIGN_SPECS use this template
- **Stage 4 (cohort migration):** all 80+ DESIGN_SPECS retrofit to template structure at `.D` candidate ship
- **Stage 5 (CLAUDE.md promotion):** when template is load-bearing for spec creation (1+ year)
- **Stage 6 (cadence-locked):** `/doc-create` skill enforces; CI validates frontmatter

---

## Cross-references

- Sister: `doc-frontmatter-convention.md` (frontmatter discipline this template uses)
- Sister: `doc-tag-vocabulary.md` (tag vocabulary referenced in frontmatter)
- Sister: `pattern-codification-lifecycle.md` (Stage 1-6 lifecycle)
- Sister: `future-oriented-plan-template.md` (parallel pattern at plan-body layer)
- Sister: `sprint-master-plan-template.md` (parallel pattern at sprint-MASTER layer)
- Sister: `postmortem-template.md` (parallel pattern at postmortem layer)
- TECH_DEBT-115 (institutional-memory rollout phases)
- Memory: `feedback_claude_md_guidelines_not_stuff_to_do.md`

---

**End of design-spec-template v1.0 DRAFT.** Stage 3 first canonical queued at `.C` candidate ship.
