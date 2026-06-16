---
name: feedback_invoke_composable_skills_dont_hand_execute
description: "When an orchestrator skill says \"invoke /X via the Skill tool\", INVOKE it — don't hand-execute its body \"to be efficient\"; hand-executing silently skips the sub-skill's stages"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 1ca40db2-672f-4994-b19c-e3440ae9a8b9
  sister_specs: [feedback_exhaustive_capture_and_verify_tracking.md, feedback_run_dedicated_audit_skills_not_just_armed_prompts.md]
  tags: []
---

When running a Layer-1 orchestrator skill (`/close-session`, `/precoding-audit-gate`, …) whose spec says "invoke `/X` via the Skill tool" (e.g. close-session Stage 6 → `/handoff`), **actually invoke `/X`** — do NOT hand-execute its body with Write/Bash "to be more efficient or tailored." A composable skill carries stages you don't hold in your head; hand-executing **silently skips them.**

**Why:** this session, close-session Stage 6 said invoke `/handoff`, but I Write'd the handoff by hand "to tailor it" → skipped `/handoff` **Stage 1.5** (serialize the TaskList into the handoff verbatim) AND close-session **Stage 5.5**'s "build the review checklist from `git diff`" → the handoff dropped its TaskList table (tasks would silently vanish at the next `/accept-handoff` pickup) and the review couldn't see the un-listed items. The operator caught both via "anything we missed" + "no top-N" — exactly the operator-pushback-as-structural-gap signal. The skills HAD the steps; hand-executing them away was the failure.

**How to apply:** "invoke `/X` via the Skill tool" means INVOKE it, not approximate its body. If you deliberately hand-execute (genuine reason), you OWN every stage the skill would have run — enumerate them and do each, don't silently drop. Mechanical backstops added this session (M7): `check_handoff_capture_completeness.py` now enforces a TaskList snapshot; `rebuild_doc_indexes.py --check` (in `check_session_docs.sh`) enforces index currency. The deeper fix is this discipline. Sister: [[feedback_run_dedicated_audit_skills_not_just_armed_prompts]] (run the skill's catalog walk, don't approximate it with an armed prompt) + [[feedback_exhaustive_capture_and_verify_tracking]].
