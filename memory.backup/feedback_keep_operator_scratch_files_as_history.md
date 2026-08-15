---
name: feedback-keep-operator-scratch-files-as-history
description: "Operator scratch/temp files in the tree are historical record — keep, never clean; home record-valuable ones"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: e5a36f36-28e4-4007-803e-eef6b4ebfff5
  modified: 2026-08-11T01:16:42.894Z
  sister_specs: [feedback_document_as_you_go_over_catch_at_end.md, feedback_name_members_never_tallies_in_docs.md, feedback_save_agent_reports_verbatim.md, feedback_spotcheck_findings_route_to_plan_homes_not_techdebt.md, project_public_repo_is_code_only.md]
  tags: []
---

Untracked operator scratch files (notes, bookmarks, probe .cpp, jotted ideas) are HISTORICAL
INFORMATION to go back over — keep them, never clean them up (operator call, 2026-08-10).

**Why:** The project has been bitten in BOTH directions. The D-414 sweep's raw agent transcripts +
`sweep_facts.json` lived in `/tmp` and were LOST to a reboot (the register is the salvage). And
`notes_update.md` (one line: "straddled cache line, NotifyEvent struct, Line 10") turned out to be
the FOUNDING OBSERVATION of the whole D-413 integrity arc — cited by the decision log itself. The
raw observation ≠ the refined diagnosis (the note says NotifyEvent; the real straddler was
NotifyState.cond) — the original carries information the polished record loses.

**How to apply:**
- NEVER delete or `git clean` operator-authored untracked files; leave them VISIBLE-untracked
  (visibility in `git status` is a feature — they stay in her face as reminders).
- Record-valuable scratch (anything a decision/register cites, or a founding observation) → home a
  FROZEN verbatim copy with provenance into workspace `plan_checks/`; leave the original in place.
- Regenerable build trees are NOT history → gitignore them like their siblings (`build_clangd/`
  precedent, 2026-08-10).
- Everything is pushable — all repos private since 2026-07-06 ([[project_public_repo_is_code_only]]).
- Sisters: [[feedback_document_as_you_go_over_catch_at_end]] (the create→capture gap) ·
  [[feedback_name_members_never_tallies_in_docs]] (anchors over summaries).
