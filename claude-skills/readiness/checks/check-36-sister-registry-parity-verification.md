---
type: skill-check
check_id: 36
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Sister-registry parity verification (meta-discipline M1)
established: 2026-05-18
---

# /readiness Check 36 — Sister-registry parity verification (meta-discipline M1)

**When this fires:** plan body references column / bit / field on a sister registry (e.g., FOREACH_GATE_CFG_FLAG metadata_flags column when sister FOREACH_ML_CFG_FLAG was already migrated to 6-col sig).

**Why this matters:** plans assume sister-registry shape parity; sister sig migrations can drift across cohort siblings if not audited.

**What to verify:** for each referenced sister-registry column/bit, `rg "#define FOREACH_<sister>\(X\)"` to read the current sig at HEAD. Verify column count + position matches plan body assumption. If sister sig was migrated but cohort siblings deferred without rationale → flag for cohort-migration sub-step in plan body.

**Cross-references:** `DESIGN_SPECS/meta-disciplines/canonical-sister-extension-discipline.md` § Temporal evolution + cohort migration. `DESIGN_PHILOSOPHY.md` § 11.5 M1. `feedback_audit_canonical_sister_before_new_infra` + `feedback_enumerate_consumers_before_registry_row_deletion` (repointed 2026-07-19 — this line previously cited `feedback_verify_sister_registry_parity_pre_coding`, a memory that has never existed: a WH-5 dangling-cite instance) (memory rule).

**Effort:** 2-5 min per audit (one grep per sister registry).
