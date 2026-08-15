---
name: feedback-save-agent-reports-verbatim
description: "Save every sub-agent report VERBATIM at receipt under plans/<sprint>/reports/<date>-<directive>/<task>.md — the orchestrator writes, agents stay read-only"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e5a36f36-28e4-4007-803e-eef6b4ebfff5
  modified: 2026-08-11T23:07:11.147Z
  sister_specs: [feedback_document_as_you_go_over_catch_at_end.md, feedback_keep_operator_scratch_files_as_history.md, feedback_name_members_never_tallies_in_docs.md]
  tags: []
---

Every sub-agent report gets saved VERBATIM to the workspace at the moment it is received —
`plans/<sprint>/reports/<YYYY-MM-DD>-<directive-slug>/<agent-task-slug>.md` with a small
frontmatter (type: agent-report · status: FROZEN · directive · agent_class · delivered ·
disposition_register pointer). Operator directive 2026-08-10: *"ideally we keep every tmp file,
and direct the sub agents to save them under like a REPORTS/[DIRECTIVE]/[AGENT TASK] … that way
theyre keepable, and i can have them always on hand."*

**Why:** agent transcripts live in /tmp and die at reboot — the D-414 sweep's raw reports + its
`sweep_facts.json` were LOST exactly this way; the registers were salvage. Raw-on-hand also lets
the operator re-read the full evidence behind any register disposition.

**How to apply:**
- The ORCHESTRATOR is the single writer — investigation agents (i/a/v/c/d-class) keep their
  read-only contract; never direct them to write their own reports.
- Save at RECEIPT, before synthesizing (the create→capture gap is where loss lives —
  [[feedback_document_as_you_go_over_catch_at_end]]).
- VERBATIM body + orchestrator post-scripts clearly marked; the curated disposition layer stays
  in `plan_checks/` registers — raw + curated are complementary, never merged.
- `/reports/` is enrolled in `frozen_record_paths` (`tools/lib/citable_id_namespaces.json`) —
  frozen truthful artifacts: cite-repair and staleness gates skip them by the same law as
  postmortems/handoffs.
- Sisters: [[feedback_keep_operator_scratch_files_as_history]] (operator-authored scratch) ·
  [[feedback_name_members_never_tallies_in_docs]].
