---
type: ledger-template
class_id: 31
title: Hardcoded refs in always-loaded docs accumulate canonical-list duplication that drifts past sprint cycles
parent_index: DOCS/RECURRING_BUG_PATTERNS.md
established: 2026-05-19
surface_tags: [ci-tooling, registry]
severity: medium
recurrence_count: 50
first_instance: 2026-05-18 (skill structural audit at v5.15.5.F.4d.1.B.3; surfaced ~50 sites across 22 skills)
closure_mechanism: categorical-triggers-in-always-loaded-docs discipline + defer-to-source-of-truth registries/ledgers + /metadata-audit quarterly cadence + tools/check_doc_metadata.py CI tool
sister_classes: [11, 18, 21]
---

# Class 31 — Hardcoded refs in always-loaded docs accumulate canonical-list duplication that drifts past sprint cycles

**Detected:** 2026-05-18 (during institutional-memory refresh at v5.15.5.F.4d.1.B.3; structural skill audit surfaced ~50 sites across 22 SKILL.md files duplicating canonical lists).
**Severity:** MEDIUM — silent doc-system drift; not a runtime bug but causes finding-issues when operator can't retrieve discipline via pattern-match. Compounds invisibly past sprint cycles until threshold is hit.

## Recurring symptom

Always-loaded docs (CLAUDE.md / CLAUDE.local.md / MEMORY.md / SKILL.md files) accumulate hardcoded references in trigger bodies that should be CATEGORICAL pattern triggers. Common shapes:

```yaml
# WRONG: hardcoded TECH_DEBT-NNN in trigger body
trigger: "when work touches TECH_DEBT-105"
# RIGHT: categorical pattern
trigger: "when work touches <bug-class-pattern>"

# WRONG: specific function name in WHEN section
WHEN: "refactoring populate_stamp_cfg_from_derived"
# RIGHT: pattern shape
WHEN: "refactoring cfg-derived consumer template fns"

# WRONG: canonical-list duplication (5-10 fields enumerated inline)
"Stamp-bound cfg fields: confidence_threshold_scale, barrier_gate_enabled, ..."
# RIGHT: defer-to-registry
"Stamp-bound cfg fields: walk current FOREACH_STAMP_BOUND_CFG_DERIVED registry rows"
```

The dominant shape is **canonical-list duplication** — trigger bodies enumerate 5-10 fields/files/functions that ALSO live in a canonical registry or ledger (FOREACH_* / DOCS/HOT_PATH_CHANGELOG.md / DOCS/CLAUDE_ML_INVARIANTS.md / CoreFrameworks/MetaRegistry.hpp). The inline list drifts; the registry stays correct; the skill body becomes wrong.

## Why this is a class (not a one-off bug)

The drift accumulates invisibly past sprint cycles. Each sprint adds new cfg fields / new bug classes / new hot-path functions to the canonical source. Skill bodies referencing those lists by literal enumeration get stale automatically.

Recurrence is GUARANTEED unless structural discipline applied:
- Predecessor TECH_DEBT-109 closed sprint-phrasing-level drift (22 sites at v5.15.5.F.4d.1.B.3); structural-level drift remained
- Structural skill audit found ~50 sites across 22 of 30 skills duplicating canonical lists
- 5 canonical lists were duplicated across multiple skills (stamp-bound cfg fields / hot-path file enumeration / architectural-sprint guards / per-strategy line refs / etc.)

## False-positive surface (per M3 discipline)

Not all hardcoded refs are Class 31:
- **Stable catalog IDs (KEEP):** Class N references / H invariant N / M-discipline N / DESIGN_SPECS pattern filenames / FOREACH_* registry names / canonical doc paths — designed-stable references, not drift candidates
- **Worked examples (KEEP with framing):** `Anti-pattern caught (vX.Y.Z YYYY-MM-DD):` / `e.g.` / `Worked example:` / `Codified at v5.X.Y` — explicit history-marker framing preserves canonical history without claiming categorical authority
- **Canonical anchors (KEEP):** TECH_DEBT-NNN refs that genesis-anchor a skill (e.g., TECH_DEBT-018 → /precoding-audit-gate)

## Closure mechanism

**Structural fix** per `DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md`:

1. **3-bucket audit rubric** — every reference in always-loaded content classified as A KEEP / B KEEP-WITH-FRAMING / C CONVERT
2. **Defer-to-registry pattern** — when trigger body lists 5-10 fields/files/functions that ALSO live in a canonical registry/ledger, replace inline list with categorical pointer (`walk current FOREACH_<COHORT> rows`)
3. **Periodic audit cadence** — `/metadata-audit` quarterly + post-codification sweep catches new drift before it accumulates past finding-issues threshold
4. **CI verification** — `tools/check_doc_metadata.py` validates frontmatter at commit time; sister to `/metadata-audit` discipline
5. **Doc-system frontmatter discipline** — `DESIGN_SPECS/meta-disciplines/doc-frontmatter-convention.md` codifies the metadata schema that enables grep-driven retrieval (eliminates need for inline lists)

## Worked instances

- **v5.15.5.F.4d.1.B.3 (2026-05-18):** Structural skill audit fired Agent against 30 SKILL.md files; ~50 C-bucket findings across 22 skills (canonical-list duplication of stamp-bound cfg fields / hot-path file enumeration / architectural-sprint guards / per-strategy line refs). All converted to categorical pattern triggers at this ship. TECH_DEBT-112 closure.

## Sister classes

- **Class 18** (Mirror-incomplete) — parent family; Class 31 is doc-layer instance shape of structural mirror drift
- **Class 21** (Multiple parallel descriptors) — sister at registry layer; same canonical-list-duplication root cause
- **Class 11** (Extensibility friction / silent drift) — parent meta-class; Class 31 is one shape of silent drift

## Cross-references

- `DESIGN_SPECS/doc-disciplines/categorical-triggers-in-always-loaded-docs.md` (closure mechanism; 3-bucket audit rubric)
- `DESIGN_SPECS/meta-disciplines/doc-frontmatter-convention.md` (frontmatter-driven retrieval; eliminates inline-list duplication)
- `DESIGN_SPECS/meta-disciplines/doc-tag-vocabulary.md` (canonical tag list; same defer-to-source-of-truth shape applied to tags)
- `tools/check_doc_metadata.py` (CI enforcement)
- `/metadata-audit` skill (quarterly drift detection)
- `feedback_categorical_triggers_over_hardcoded_refs.md` (going-forward rule)
- `feedback_claude_md_guidelines_not_stuff_to_do.md` (companion doc-layer separation)
- TECH_DEBT-112 (structural skill audit closure; canonical first canonical application)
- TECH_DEBT-115 (institutional-memory rollout that codified the discipline)
