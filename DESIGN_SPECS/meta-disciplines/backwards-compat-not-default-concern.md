---
type: meta-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-05-28 (promoted from memory rule + 2026-05-26 origin)
canonical_applications:
  - v5.15.5.F.4d.1.B.4 v1.7.5 D18 (centralized SHARDED full surface deletion)
  - v5.15.5.F.4d.1.D D-9 + .E sub-sprint clean break
sister_specs:
  - meta-disciplines/structural-fix-preferred-decision-framework.md
  - meta-disciplines/gui-deprecation-decision-rationale.md
tags: [meta-discipline, backwards-compat, breaking-changes, deletion-scope, oss-project]
surface: [refactor-scope, deletion-decisions]
sister_memory: feedback_backwards_compat_not_default_concern
applies_at_skills: [/precoding-audit-gate]
---

# Backwards-compat not default concern

**Pattern intent:** This is an OSS personal tool, not a managed product. Default to cleanest architectural answer (full surface deletion; clean break) over preserve-and-deprecate layers. Operator flags explicitly when load-bearing exceptions apply.

## Problem statement

Conventional software engineering: preserve backwards compatibility by default. Add new behavior alongside old; deprecate old; remove after N versions.

For this OSS personal tool: backwards compat layer has high cost (maintenance burden; ambiguity; code complexity) and low value (operator is also developer; can absorb breaking changes; no external client base needing compat).

Default policy: clean break per architectural decision. Preserve compat only when load-bearing.

## Pattern description

### Default action on refactor / deletion

**DEFAULT (this rule):** full surface deletion; NO preserve-and-deprecate layer.

```cpp
// OLD code in v5.X
void old_drainer_lambda() { /* 200 lines */ }

// At .E.1: DELETE entirely. Replace with per-node slow-path absorption.
// No "deprecated" wrapper; no preserve-and-warn layer.
```

### Load-bearing exceptions (preserve compat)

Operator explicitly flags when preserve-and-deprecate IS warranted:

- **Stamp body / persistence format** (Per H9 byte preservation): cannot break without invalidating ALL existing models
- **API key permission semantics**: security-load-bearing
- **Locked cfg field semantics**: behavioral compat for live trading
- **Audit log forensic record**: legal / compliance

For these: preserve old layer + warn / migrate path.

### Refinement: SECTION required even when PATH not (per D-22 refinement)

Operator migration impact SECTION in plan body is REQUIRED even when backwards compat not preserved. SECTION captures REASONING + categorization (who's affected; what happens; sister-architectural preservation if any). PATH (actual preserve-and-deprecate implementation) is OPTIONAL per exceptions list.

SECTION ≠ PATH. Always document the migration impact in plan body; only implement preservation when load-bearing.

## Worked examples

### .E (clean break) — full surface delete

`.E` sub-sprint deletes engine_gui + foxml_suite + drainer body + monolithic engine.cfg. No backwards-compat layer; operator runs `fox-migrate-cfg` one-shot at deployment.

Plan body operator-facing migration impact section documents:
- What changes for operator (workflow shift)
- What's archived to legacy/ (reference preserved)
- Migration tool (one-shot helper)
- Rollback path (pre-tag rollback anchor)

No code path preserves v5.X cfg parser; no API surface preserves single-account-only mode.

### .B.4 v1.7.5 D18 (full SHARDED deletion)

Original plan considered "preserve + REFUSE" for `engine_arch=centralized` cfg value. Operator clarification: "OSS personal tool; default to cleanest architectural answer". Simplified to "full surface delete".

Plan body amended to:
- Delete all `engine_arch=centralized` references
- Engine refuses to parse cfg with `engine_arch != sharded`
- Operator migrates one-shot

### NOT applicable: stamp body extension

`.E.1` extends stamp body with cluster_id + sub_account_id + variant_id + software_version fields. Operator-facing migration: regenerate models post-`.E.2` foxml-train (cannot reuse v5.X stamps; clean break consistent with rule).

But: format itself byte-preserved (H9); not "backwards compat" — just "different schema".

Distinguishes: schema EVOLUTION (preserve byte layout discipline) vs API surface PRESERVATION (compat).

## When to invoke

✅ Refactor scope where operator + dev are same person
✅ OSS public AGPL where forking is the migration path for external users
✅ Internal API surfaces (not stamp body; not audit log)
✅ Clean architectural rework

❌ Wire-format / HMAC chain — preserve byte layout
❌ Persistent state file format — migrate path required
❌ External-facing API (if any) — preserve compat
❌ Security boundaries — load-bearing

## Cross-references

- Parent memory: `memory/feedback_backwards_compat_not_default_concern.md`
- Sister: `meta-disciplines/structural-fix-preferred-decision-framework.md`
- Sister: `meta-disciplines/gui-deprecation-decision-rationale.md`
- Decision log entries: D-9 (no backwards compat directive); D-22 (refinement: SECTION required); D-61 (dead code deletion at .E)
- Refinement: SECTION always required even when PATH not (per `feedback_surface_operator_migration_path_proactively`)
