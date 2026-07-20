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

## `registry_id:` — REQUIRED on any doc that OWNS a citable ID (added 2026-07-19, D-389)

A doc that defines an entry in a citable-ID namespace — `Hn` hard invariant · `Mn` meta-discipline · `Class N` anti-pattern · `AR-n`/`WH-n` meta-anti-pattern · `Tn` toolchain invariant · `Bn` blindspot pillar — MUST declare that ID in frontmatter:

```yaml
registry_id: M10        # the ID this doc is the canonical body for
```

**Why:** citable IDs are how this knowledge base cross-references itself, and until 2026-07-19 nothing verified that an ID means exactly one thing. It didn't: `M9` was claimed by two disciplines and `D-1`..`D-13` by two decision logs with diverging content (**AR-14**; H21's failure mode on the doc plane). `registry_id` is the machine-readable anchor that lets a checker resolve ID → canonical doc and flag a double-claim.

### It is the REVERSE map, and most namespaces do not need it

`registry_id` answers *"which doc is the BODY of this ID?"* — **not** *"where is this ID declared?"* Those are different questions, and conflating them is what made the field look like it needed 190 rows.

Every namespace already has a **defining-form anchor** that a checker reads directly, per TECH_DEBT-249's parse spec: `Hn` ← the `CLAUDE.md` table · `Mn` ← § 11.5 · **`Class N` ← the FILENAME glob `class-(\d+)-*.md`** · `AR`/`WH`/`PL`/`CP` ← the index table · `Bn` ← `^### (B\d+)` · `Tn` ← the `tools/CLAUDE.md` table · `TECH_DEBT-nnn` ← `^### TECH_DEBT-(\d+)`. Where the declaration and the body are the SAME artifact — every `Class N` file, for instance — `registry_id` is **redundant**, and adding it is duplicate infrastructure, not coverage.

So the field belongs **only** on a doc that is the canonical body of an ID declared *somewhere else*. In practice that is the `Mn` specs (declared in § 11.5, bodied in `DESIGN_SPECS/`) and any `Hn` whose table row cites a spec as its body.

### `owns_namespace:` — for INDEX docs (added 2026-07-20)

A singular `registry_id` cannot express a doc that is the registry for a whole namespace. `meta-anti-pattern-index.md` is the canonical body for **every** `AR-n`, `WH-n`, `PL-n` and `CP-n` — dozens of IDs — and forcing it to name one would be a lie, while listing all of them would rot on every addition.

```yaml
owns_namespace: [AR, WH, PL, CP]   # this doc is the registry FOR these namespaces
```

Owning *an ID* and being *the registry for a namespace* are different relationships; a checker resolving `AR-15` should land on the index via the namespace claim, not fail to find a `registry_id: AR-15` that will never exist.

**Honest status (2026-07-20):** the field still has **zero consumers** — `check_doc_metadata.py` does not require it and TECH_DEBT-249's guard is unbuilt. Adoption is now **10 docs**, which is close to the true population rather than a fraction of 192: `M1`, `M2`, `M4`, `M5`, `M6`, `M7`, `M8`, `M10`, `H22`, plus this doc's own example. Deliberately absent: **M3** (has no spec at all — codification is PARTIAL, TECH_DEBT-248) and **M9** (its body is the multi-ID index, which wants `owns_namespace`, not `registry_id`). Until the guard ships this is documentation-only — do not treat its presence as verified.

## Per-doc-type extra fields

### DESIGN_SPECS/*.md
```yaml
type: refactor-pattern | feature-pattern | framework-pattern | audit-methodology | data-discipline | concurrency-pattern | wire-format-pattern | doc-discipline | meta-discipline | plan-template | ledger-template | architecture-overview | subsystem-design
applies_at_skills: [/skill1, /skill2]  # which skills load this dynamically
```

### claude-skills/<skill>/SKILL.md
```yaml
type: skill
concern: pre-coding-gate | shape-audit | impl-detail-audit | domain-audit | anti-pattern-scan | post-coding | workflow | recurrence | scaffolding
audit_cadence: ad-hoc | per-ship | quarterly | post-codification
sister_skills: [/skill1, /skill2]
loads_dynamically: [DESIGN_SPECS/file.md, memory/file.md]

# consult-stage + auto-routing fields (skill-knowledge-consultation-and-auto-routing.md). All OPTIONAL; mechanical skills omit them.
skill_kind: judgment | mechanical          # judgment → runs Stage-0 consult + is SUGGESTed by the router; mechanical → skips Stage 0, may auto-FIRE
consult_mode: scoped | broad               # OPTIONAL (default scoped). scoped (focused skills) = load your associated_* slice; broad (challengers / completeness — /second-opinion, /precoding-audit-gate) = range the FULL catalog (don't inherit the proposer's blind spots)
associated_specs: [DESIGN_SPECS/file.md]   # specs Stage 0 consults; defaults to loads_dynamically if omitted (SSoT — don't restate the list)
associated_anti_patterns: [DOCS/RECURRING_BUG_PATTERNS.md, DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md]
associated_decisions: [plans/<sprint>/decision-logs/]    # "did we already decide this?"
associated_postmortems: [plans/<sprint>/postmortems/]    # read when the ship resembles a past one
associated_ledgers: [DOCS/TECH_DEBT.md, DOCS/PARITY_ISSUES.md]   # surface-scoped OPEN debt
associated_refs: [DOCS/LANDMINES.md, FEATURE_LOOKUP.md]          # operational refs
trigger_heuristics: ["<input pattern> -> suggest|fire"]          # Layer B: input match → SUGGEST (judgment) / FIRE (mechanical)
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
