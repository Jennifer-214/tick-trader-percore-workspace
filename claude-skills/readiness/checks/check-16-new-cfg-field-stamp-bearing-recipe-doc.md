---
type: skill-check
check_id: 16
parent_skill: /readiness
parent_path: claude-skills/readiness/SKILL.md
title: New cfg field with stamp-bearing → recipe doc update
established: 2026-05-18
---

# /readiness Check 16 — New cfg field with stamp-bearing → recipe doc update

Trigger keywords: cfg field that affects ML inference. Specifically:
fields tagged STAMP_BOUND_CFG_DERIVED in the master cfg registry
(walk current FOREACH_STAMP_BOUND_CFG cohort).

When plan adds a new such field:

- Verify it lands in `StampInferenceCfgInputs` struct.
- Verify `stamp_write_for_model` emits when has_* flag set.
- Verify `verify_model_stamp` parses + populates `ModelStampResult`.
- Verify `tools/stamp_model.sh` accepts a matching `--<field>` arg.
- Verify v5.8.8-style round-trip test extends.
- Verify `DOCS/ML_TEST_RECIPES.md` recipe entry updated with the
  new flag (operators need to know what to pass to `stamp_model.sh`).
- Verify `DOCS/PARITY_LIFECYCLE.md` row updated.

If any of these is missing → GAP, plan must address before coding.
