---
name: feedback-operator-facing-doc-cohort-at-cfg-deletion
description: "When deleting cfg field/feature/operator-facing surface, comprehensive sweep of operator-facing doc surfaces beyond code (distinct from code-side consumer enumeration). Cohort surfaces: README.md + DOCS/QUICKSTART.md + engine.cfg.example + sister operator-facing docs. Sister to enumerate-consumers extended to operator-facing layer."
metadata:
  node_type: memory
  type: feedback
  originSessionId: f7bb757d-2b7c-4ba6-9c4a-1c7d60bff493
  sister_specs: [feedback_enumerate_consumers_before_registry_row_deletion.md, feedback_multi_surface_deletion_ordering_discipline.md, feedback_archived_changelog_preservation_discipline.md, feedback_backwards_compat_not_default_concern.md, feedback_surface_operator_migration_path_proactively.md, feedback_verify_symbol_existence_at_plan_drafting_time.md]
  tags: [deletion-discipline, doc-discipline]
---

**When deleting a cfg field / operator-facing feature / surface**, code-side consumer enumeration (per `feedback_enumerate_consumers_before_registry_row_deletion`) catches `.cpp/.hpp` references. But OPERATOR-FACING DOC surfaces are typically MISSED — README examples, QUICKSTART tables, cfg.example sister docs, sister operator-onboarding files all reference the deleted surface and become stale post-deletion.

**Discipline:** include operator-facing doc surfaces in the deletion-cohort enumeration. Sister to code-side consumer enumeration but at OPERATOR-FACING layer.

**Why:** Codified 2026-05-26 PM at `.B.4` v1.7.5 WIP-12 cycle after operator-directed `rg` sweep + B-Plus v0.4 generator mode revealed `engine_arch` references in 4 operator-facing doc surfaces (README.md:195 + DOCS/QUICKSTART.md:174 + engine.cfg.example:422/435/438/910) that the original v1.7.4 D17 framing "8 branches + 3 wrappers + cfg field + parser + TUISnapshot + GUI gating" MISSED entirely. Sister code-side audits (/trace-deps + /parity-check + /merge-scan + /dod-audit + /blindspot-scan + /bug-check) focused on `.cpp/.hpp` surfaces; none surfaced the operator-facing doc cohort. Mechanical `rg` sweep caught them.

## How to apply

**When plan body proposes deletion of a cfg field / operator-facing surface:**

1. **Run comprehensive `rg <pattern>`** beyond `.cpp/.hpp` surface — include `.md` + `.cfg.example` + sister operator-facing doc surfaces. B-Plus v0.4 `--gen-deletion-cohort PATTERN` does this mechanically + classifies per deletion-kind including `operator-facing-doc` category.

2. **Identify operator-facing doc surfaces:**
   - `README.md` — main operator entry point; cfg examples + walkthrough
   - `DOCS/QUICKSTART.md` — operator quickstart; cfg option tables
   - `engine.cfg.example` — annotated cfg file template; per-field documentation
   - `DOCS/CHANGELOG.md` current — version-history doc; new row added at ship close; HISTORICAL rows LEAVE per archived-changelog-preservation
   - Sister operator-facing docs: TESTING_NOTES + onboarding docs + tutorial docs

3. **Delete operator-facing doc references** as part of deletion cohort (leaves-first per `feedback_multi_surface_deletion_ordering_discipline`; operator-facing docs delete first since no compile dependency).

4. **Verification post-deletion:** `rg <pattern>` over operator-facing doc surface returns ZERO.

## Recognition markers (when this rule applies)

- Plan body proposes deletion of cfg field (operators may have cfg field in their cfg files; cfg.example needs update)
- Plan body proposes deletion of operator-facing feature (README/QUICKSTART operator docs need update)
- Plan body proposes removal of cfg option from operator-facing table (QUICKSTART table needs row removed)
- Any case where deletion target appears in operator-facing surfaces (README + QUICKSTART + cfg.example)

## Sister memories

- [[feedback_enumerate_consumers_before_registry_row_deletion]] — parent meta-rule (consumer enumeration before deletion); this rule extends to operator-facing layer
- [[feedback_multi_surface_deletion_ordering_discipline]] — B14 sister; operator-facing-doc kind is leaves-first in deletion ordering
- [[feedback_archived_changelog_preservation_discipline]] — sister at archived-doc layer; archived changelogs LEAVE even when feature deleted
- [[feedback_backwards_compat_not_default_concern]] — operator migration impact section captures reasoning + cited surfaces; this rule is the surface-enumeration side
- [[feedback_surface_operator_migration_path_proactively]] — sister rule when load-bearing exception applies (stamp body / persistence / model handle); this rule applies more broadly

## Worked example

`.B.4` v1.7.5 WIP-14 — `engine_arch` cfg field deletion operator-facing doc cohort (4 sites):

| Site | Action |
|---|---|
| `README.md:195` `engine_arch = per_core_slow      # v5.0+ default` | DELETE line + sister context |
| `DOCS/QUICKSTART.md:174` `\| \`engine_arch\` \| \`per_core_slow\` (default) vs \`centralized\` (legacy) \| startup-only \|` | DELETE row from cfg option table |
| `engine.cfg.example:422` `# engine_arch — slow-path threading model under sharded mode.` | DELETE comment block (lines 422-438 cluster) |
| `engine.cfg.example:435` `engine_arch=per_core_slow` | DELETE (part of comment block cluster) |
| `engine.cfg.example:438` `# (only used when engine_arch=per_core_slow).` | DELETE (part of comment block cluster) |
| `engine.cfg.example:910` `# engine_arch (per_core_slow/centralized). Stamp-bound: every model` | DELETE (sister context line) |

POST-DELETION verification: `rg "engine_arch|ENGINE_ARCH_" --no-heading -g "*.md" -g "*.cfg.example"` over operator-facing doc surface returns ZERO.

LEAVE per archived-changelog-preservation: `DOCS/changelogs/2026-04-*` historical rows (record what shipped at v5.0.x; rewriting violates timeless-doc principle) + `DOCS/CHANGELOG.md` v5.15.2 row historical context (records context at v5.15.2 ship; not actively maintained).

## Stage progression

- **Codification:** memory + going-forward rule at WIP-12 (this ship is 1st canonical application)
- **Sister DESIGN_SPEC:** NOT codified inline at v1.7.5 (premature without 2nd canonical per `feedback_framework_layer_payoff_diminishing_returns`); promote to DESIGN_SPEC at 2nd canonical surfacing
- **Audit-time check:** `/readiness` Check 43 sidecar (NEW; operator-facing doc cohort enumeration when cfg field deletion detected in plan body scope)
- **Structural enforcement:** B-Plus v0.4 `--gen-deletion-cohort` mode includes operator-facing-doc kind in classification (sister to code-reference kind)

## Trade-off

Operator-facing doc cohort sweep adds ~5 min per cfg field deletion at planning time. Catches operator-facing-doc staleness BEFORE ship. Without this rule: operators read README/QUICKSTART/cfg.example post-ship; encounter references to deleted feature; confusion + support burden.

For internal-only deletions (no operator-facing surface): this rule N/A; just delete + rebuild. The discipline applies WHEN operator-facing surface is part of cohort.

## When this rule applies

Per `feedback_categorical_triggers_over_hardcoded_refs`:

- Any cfg field deletion (operators may have field in cfg files; cfg.example needs update)
- Any operator-facing feature deletion (README/QUICKSTART tables need update)
- Any cfg option removal from documented operator table
- Any deletion where B-Plus v0.4 generator classifies sites as `operator-facing-doc` kind
