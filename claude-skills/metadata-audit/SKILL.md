---
name: metadata-audit
description: Quarterly cadence audit of doc-system metadata. Reports missing frontmatter / undefined tags / broken sister-doc links / stale Stage 2 DRAFTs / singleton tags / filesystem-path mismatches with type. Wraps tools/check_doc_metadata.py + adds advisory analysis. Sister to /anti-spaghetti quarterly cadence.
type: skill
concern: anti-pattern-scan
audit_cadence: quarterly
tags: [doc-discipline, audit-methodology, framework-discipline]
surface: [ci-tooling]
sister_skills: [/anti-spaghetti, /find, /index-rebuild, /doc-create]
loads_dynamically: [DESIGN_SPECS/meta-disciplines/doc-frontmatter-convention.md, DESIGN_SPECS/meta-disciplines/doc-tag-vocabulary.md, DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md]
---

# /metadata-audit — Periodic doc-system drift audit

## What this does

Quarterly cadence audit catching doc-system drift mechanically:
- Missing frontmatter (where required per `doc-frontmatter-convention.md`)
- Undefined tags (typos against `doc-tag-vocabulary.md`)
- Broken sister-doc links (bidirectional verification)
- Stage 2 DRAFTs older than N sprints (promotion candidates)
- Singleton tags (used by only 1 doc — consolidation candidates; ADVISORY)
- Filesystem-path mismatches with `type:` frontmatter (post folder restructure)
- File-size threshold violations (per `file-size-split-discipline.md`)
- Dead cross-references (`sister_specs:` paths that don't exist)

Sister to `/anti-spaghetti` quarterly cadence — `/anti-spaghetti` audits CODE structure; this audits DOC structure.

## Invocation

- `/metadata-audit` — full audit
- `/metadata-audit --target DESIGN_SPECS/` — limit to subset of docs
- `/metadata-audit --severity high` — only HIGH severity findings
- `/metadata-audit --post-codification <pattern-name>` — post-codification sweep (verify cohort frontmatter alignment after new spec promotion)
- `/metadata-audit --check-sizes` — file-size threshold violations only

## Execution model

1. Walk all docs in scope (DESIGN_SPECS / claude-skills / memory / DOCS / plans)
2. For each doc:
   - Parse frontmatter (call `tools/check_doc_metadata.py`)
   - Classify findings per category below
3. Aggregate: per-category counts + per-finding details
4. Generate report with severity-classified findings
5. Output: `plans/<sprint>/plan_checks/<YYYY-MM-DD>-metadata-audit.md`

## Finding categories

### CRITICAL (RED) — blocking

1. **Undefined tags** — tag in frontmatter doesn't exist in `doc-tag-vocabulary.md`
2. **Invalid type values** — type field has value not in valid set
3. **Invalid lifecycle stage** — stage not in 6-stage set
4. **Missing required fields** — frontmatter present but missing required field (type / established)

### HIGH (YELLOW) — should address pre-coding

1. **Missing frontmatter on DESIGN_SPECS** — DESIGN_SPECS/*.md without frontmatter (post-Phase 3 cohort migration)
2. **Missing frontmatter on SKILL.md** — claude-skills/*/SKILL.md without frontmatter
3. **Broken sister_specs paths** — sister_specs entries pointing to nonexistent files
4. **File-size threshold violations** — files exceeding HARD threshold per `file-size-split-discipline.md`

### MEDIUM (YELLOW) — address at next cycle

1. **Bidirectional sister-link asymmetry** — A says sister=B but B doesn't say sister=A
2. **Stage 2 DRAFTs older than 3 sprints** — promotion candidates
3. **File-size SOFT warnings** — files in soft-threshold range
4. **Filesystem-path mismatch with type** — file in DESIGN_SPECS/refactor-patterns/ has `type: framework-pattern`

### LOW (advisory) — defer / accept

1. **Singleton tags** — tags used by only 1 doc (consolidation candidates; operator judgment)
2. **Dead tag definitions** — tags in vocabulary but used by zero docs
3. **Stage progression gaps** — multiple Stage 2 DRAFTs at the same surface (cohort opportunity)
4. **Missing applies_at_skills field** — frontmatter has empty applies_at_skills when body cross-refs skills

## Output format

Per `DESIGN_SPECS/audit-methodologies/audit-report-format.md` standardized shape:

```markdown
---
type: audit-report
audit_type: anti-pattern
audit_skill: /metadata-audit
target: doc-system (workspace-wide)
severity: green | yellow | red
findings_count: N
established: YYYY-MM-DD
---

# /metadata-audit report — YYYY-MM-DD

## Severity verdict
- <GREEN/YELLOW/RED>: <rationale>

## Findings (severity-ordered)

### CRITICAL (N findings)
<list>

### HIGH (N)
<list>

### MEDIUM (N)
<list>

### LOW (advisory)
<list>

## Patterns observed
- <pattern 1>: N instances
- <pattern 2>: N instances

## Auto-write entries proposed
<list>
```

## Cadence

- **Quarterly** — every ~12 weeks; sister to `/anti-spaghetti` quarterly cadence (per `project_anti_spaghetti_audit_cadence` memory)
- **Post-codification** — fire after promoting any spec Stage 2 → Stage 3 (verify cohort alignment)
- **Post-folder-restructure** — fire after TECH_DEBT-113 folder subdivision
- **Operator-flagged** — fire when finding-issues threshold suspected
- **Sprint MASTER amendment** — fire at sprint planning boundary

## Trade-offs + when to apply

### Apply when:
- Quarterly cadence
- After major doc-system changes (frontmatter migration, folder restructure)
- Operator surfaces "I can't find X"

### Skip when:
- Mid-sub-ship coding phase
- Frequently (audit fatigue; reserve for boundary cadence)

## Pattern lifecycle

- **Stage 1 (problem):** doc-system drift accumulates invisibly; surfaced 2026-05-18
- **Stage 2 (DRAFT):** THIS SKILL (2026-05-18)
- **Stage 3 (first canonical):** queued at `.C` candidate ship after frontmatter cohort migration
- **Stage 4 (cohort):** periodic cadence locked
- **Stage 5+ (mature):** CI integration; commit-time validation (sister to `tools/check_doc_metadata.py`)

## Cross-references

- Sister skill: `/anti-spaghetti` (code structure audit; same quarterly cadence)
- Sister skill: `/find` (queries metadata; this skill audits metadata)
- Sister skill: `/index-rebuild` (regenerates indexes; this skill detects drift)
- Sister skill: `/doc-create` (creates compliant docs; this skill audits compliance)
- Reference: `DESIGN_SPECS/meta-disciplines/doc-frontmatter-convention.md` (frontmatter discipline)
- Reference: `DESIGN_SPECS/meta-disciplines/doc-tag-vocabulary.md` (canonical tag list)
- Reference: `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md` (file-size thresholds)
- Reference: `DESIGN_SPECS/audit-methodologies/audit-report-format.md` (output format)
- Tool: `tools/check_doc_metadata.py` (sister CI tool for commit-time validation)
- Memory: `feedback_metadata_audit_quarterly.md` (going-forward rule)
- Memory: `project_anti_spaghetti_audit_cadence.md` (sister cadence)
- TECH_DEBT-115 Phase 3 (this skill lands at `.D` candidate ship cadence-locked)
