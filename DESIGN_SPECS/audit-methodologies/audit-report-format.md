---
type: audit-methodology
stage: 2-draft
version: 1.0
established: 2026-05-18
tags: [audit-methodology, doc-discipline, framework-discipline]
surface: [test-infrastructure, ci-tooling]
sister_specs: [audit-driven-pre-coding-gate.md, implementation-layer-blindspot-taxonomy.md, doc-frontmatter-convention.md, audit-finding-kind-taxonomy.md]
applies_at_skills: [/precoding-audit-gate, /parity-check, /trace-deps, /merge-scan, /dod-audit, /blindspot-scan, /hft-audit, /ml-audit, /accounting-audit, /registry-fit-audit, /bug-check, /anti-spaghetti, /test-strength-audit, /post-ship-audit]
---

# Audit report format (standardized output for audit skills)

**Established:** 2026-05-18 (v5.15.5.F.4d.1.B.3 doc-layer refresh — codify audit skill output standardization)
**Status:** Stage 2 DRAFT v1.0 — Stage 3 first canonical at `.C` candidate ship; full body matures with `/precoding-audit-gate` orchestrator amendment

Audit skills currently return findings in different formats. Codify standardized shape so `/precoding-audit-gate` orchestrator can parse + summarize mechanically.

---

## Standardized report frontmatter

```yaml
---
type: audit-report
audit_type: shape | implementation-detail | domain | anti-pattern | post-ship
audit_skill: /parity-check | /trace-deps | /merge-scan | /dod-audit | ...
target: <plan-path OR ship-tag OR codebase-wide>
severity: green | yellow | red
findings_count: <N>
established: <YYYY-MM-DD>
tags: [<concern-tags>]
surface: [<surface-tags>]
related_plan: <plan path or null>
---
```

---

## Standardized body sections

```markdown
# <Audit name> report — <target>

## Severity verdict
- **GREEN** / **YELLOW** / **RED**: <one-line rationale>

## Findings (severity-ordered)

### CRITICAL (RED) — blocking
1. **<finding title>** — <file:line>
   - **Current**: <what's there>
   - **Expected**: <what discipline says>
   - **Fix**: <suggested action>
   - **Cross-ref**: <DESIGN_SPECS / Class N / H N / memory>
   - **Kind**: <mechanical | structural | design>[·wide] — per `audit-finding-kind-taxonomy.md` (the per-finding work-type axis, orthogonal to severity; drives sequencing; shorthand `<SEV>·<kind>`)

### HIGH (YELLOW) — should address pre-coding
1. <same shape>

### MEDIUM (YELLOW) — address at next cycle
1. <same shape>

### LOW (advisory) — defer / accept
1. <same shape>

## Patterns observed (categorical, not per-instance)
- <pattern 1>: N instances
- <pattern 2>: N instances

## Sister-audit cross-refs
- See also `/<other-audit>` for <related concern>

## Auto-write entries proposed
- TECH_DEBT-NNN: <title> (severity / surface) — opened
- DESIGN_SPECS amendment: <spec path> — proposed
- Memory rule codification: <name> — proposed
```

---

## Severity vocabulary

| Severity | Action | When |
|---|---|---|
| GREEN | Ship without amendment | No findings; or findings are LOW advisory |
| YELLOW | Amend plan body OR address pre-coding | HIGH/MEDIUM findings present; structural concerns surfaced |
| RED | BLOCK coding until amended | CRITICAL findings; H-invariant violations; bug-class openers |

---

## Per-audit-type expected sections

### `shape` audits (SHAPE design-layer)

- `/parity-check`: train↔serve identity findings + wire byte preservation
- `/trace-deps`: dependency chain findings + cross-pattern access
- `/merge-scan`: reuse opportunities + sister-registry candidates
- `/dod-audit`: DESIGN_SPECS pattern application + missing applications

### `implementation-detail` audits

- `/blindspot-scan`: 12-pillar implementation-detail taxonomy (per `implementation-layer-blindspot-taxonomy.md`)

### `domain` audits

- `/accounting-audit`: OMS / fee / P&L invariants
- `/hft-audit`: universal HFT principles
- `/ml-audit`: ML pipeline cross-cuts
- `/registry-fit-audit`: registry misapplication

### `anti-pattern` audits

- `/bug-check`: RECURRING_BUG_PATTERNS instance scan
- `/anti-spaghetti`: codebase-wide structural sweep
- `/dust`: generic cleanup
- `/test-strength-audit`: test-weakening regression

### `post-ship` audits

- `/post-ship-audit`: retrospective per ship

---

## Orchestrator usage (`/precoding-audit-gate`)

`/precoding-audit-gate` fires N audits in parallel; each writes a standardized report; orchestrator parses + summarizes.

Synthesis report aggregates:
- Overall severity (max of constituent audits)
- Total findings count
- Common cross-cutting patterns (e.g., `Class 21 anti-pattern surfaced by 3 audits` → priority)
- Auto-write entries proposed across all audits
- Plan body amendments required

Stored at `plans/<sprint>/plan_checks/<date>-precoding-audit-gate-synthesis.md`.

---

## Pattern lifecycle

- **Stage 1 (problem):** audit skill output formats varied; orchestrator parsing required ad-hoc
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-18 sketch)
- **Stage 3 (first canonical):** queued at `.C` candidate ship — first audit fires under new format
- **Stage 4 (cohort migration):** all 14 audit skills migrate output to standardized format
- **Stage 5+ (mature):** `/precoding-audit-gate` orchestrator parses mechanically; auto-amend candidate detection

---

## Cross-references

- Sister: `audit-driven-pre-coding-gate.md` (orchestrator discipline)
- Sister: `implementation-layer-blindspot-taxonomy.md` (12-pillar IMPLEMENTATION-DETAIL audit; matches B1-B12 finding categories)
- Sister: `doc-frontmatter-convention.md` (frontmatter discipline)
- Sister: `post-ship-audit` (retrospective; sister output format)
- TECH_DEBT-115 (institutional-memory rollout)
- CLAUDE.md § Skill suite (audit-driven discipline)
- DESIGN_PHILOSOPHY.md § 11 (audit-driven discipline) + § 11.5 (meta-disciplines M1-M4)

---

**End of audit-report-format v1.0 DRAFT.** Stage 3 first canonical queued at `.C` candidate ship.
