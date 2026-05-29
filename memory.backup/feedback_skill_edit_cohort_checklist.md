---
name: skill-edit-cohort-checklist
description: "When editing a SKILL.md (new stage/check/capability), update the cross-cutting cohort via this checklist so it doesn't drift — sister-cohort-amendment-completeness specialized to the skill surface."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: c95ac2bd-d963-485c-b028-60d593bce711
---

Editing a `claude-skills/<name>/SKILL.md` (adding a stage/check/capability)? Run this before "done" — the recurring miss is forward edits landing while the cohort updates drift:

1. **The skill's own Cross-references / Sister-disciplines section** — add what the new stage/check references (catalog, memories, sister skills). `[tool-partial: check_doc_metadata catches sister_specs frontmatter, NOT prose cross-ref sections]`
2. **Frontmatter** — `loads_dynamically` (new stage reads new docs?), `sister_skills` / `sister_specs` (new relationships, BOTH directions). `[tool: check_doc_metadata --bidirectional catches sister_specs asymmetry]`
3. **CLAUDE.md skill suite table** — only if it's a NEW skill (not for a stage/check added to an existing skill). `[tool-target: index-completeness check, #14]`
4. **The catalog / index it now consumes or writes** — cross-ref BOTH ways (e.g. a stage that writes meta-anti-pattern-index).
5. **CLAUDE.local.md going-forward rules** — if the stage/check codifies a NEW discipline (not just mechanics).
6. **Run `python3 tools/check_doc_metadata.py --bidirectional`** — the mechanical backstop for items 1-2/4.

**Why:** this session edited 3 skills (close-session / capture-audit / precoding-audit-gate) and the cohort updates (cross-ref sections, frontmatter `loads_dynamically`, indexes) drifted repeatedly — caught only by operator pushback. The checklist makes the cohort explicit, not memory-dependent.

**How to apply:** AMENDMENT-layer sister to [[feedback_sister_cohort_amendment_completeness]] specialized to the skill-edit surface; run at every SKILL.md edit. Items marked `[tool]` are or will be mechanically enforced (the doc-hygiene tool / #14); the rest are judgment. This checklist is the human-facing reminder for the judgment half + the backstop until the tool covers it. Sister: [[feedback_independence_for_judgment_not_mechanical]] (the tool-enforced items are mechanical; the prose-cross-ref items are judgment).
