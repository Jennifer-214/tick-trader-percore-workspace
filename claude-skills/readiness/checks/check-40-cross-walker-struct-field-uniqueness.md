---
type: skill-check
check_id: 40
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: Cross-walker struct-field uniqueness (meta-discipline M4 / Pillar B13)
established: 2026-05-18
---

# /readiness Check 40 — Cross-walker struct-field uniqueness (meta-discipline M4 / Pillar B13)

**When this fires:** plan body proposes new X-macro walker that generates struct fields on a struct that ALREADY has fields from another walker (e.g., adding STAMP_RESULT_DERIVED_FIELDS_AUTO_GEN to ModelStampResult which has FOREACH_STAMP_BOUND_MODEL_CONST walker).

**What to verify:** any name appearing in BOTH walker registries must be registered in the appropriate SIDECAR EXCLUSION (per H18 SIDECAR pattern). Run `tools/check_struct_field_uniqueness.py` to mechanically detect cross-walker collisions + verify sidecar registration.

**Verdict:** PASS if no collisions OR all collisions in exclusion sidecar; GAP if any collision is unregistered. Sister to Check 36 (sister-registry parity); B13 is the cross-walker-scope extension.

**Cross-references:** `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` § B13. `DESIGN_SPECS/refactor-patterns/cross-walker-struct-field-uniqueness-discipline.md` (NEW). `DESIGN_PHILOSOPHY.md` § 11.5 meta-discipline M4. `tools/check_struct_field_uniqueness.py` CI tool.

**Effort:** 2-5 min per audit (run CI tool; inspect sidecar).
