---
name: feedback_terminology_evolution_bridge_not_history_rewrite
description: "When a multi-year project undergoes an architecture-wide terminology rename, sweep FORWARD-LOOKING docs to the new schema + preserve HISTORICAL-RECORD bodies truthfully + bridge the two via a canonical glossary note. Do NOT blanket-rewrite history — it falsifies the evolution record + breaks the rename-ship's own narrative coherence."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f8d1354c-702d-4ff6-b985-c90cafb1a1f2
  sister_specs: [feedback_archived_changelog_preservation_discipline.md, feedback_proactive_rename_candidate_surfacing.md, feedback_plan_body_length_no_target_loc.md, feedback_motivated_collaborator_for_caramel.md, feedback_single_source_of_truth_discipline.md]
  tags: [migration-discipline, doc-discipline]
---

When an architecture-wide terminology rename lands in a multi-year project (e.g., Core→Node / per-core→per-node at `.E.1`), the doc system splits into two populations that need OPPOSITE treatment:

**FORWARD-LOOKING docs** (describe the current + future architecture) → **SWEEP to the new schema now. No defer.**
- Timeless canonical docs: CLAUDE.md, CLAUDE.local.md, DOCS/DESIGN_PHILOSOPHY.md, DOCS/ architecture docs, DESIGN_SPECS/ narrative
- Active in-flight working docs that describe the TARGET architecture: active plan bodies for the rename sub-sprint, MASTER plan, master-reference index, running lists, future-roadmap docs
- These get the new terminology immediately because they ARE the canonical context every future decision reads.

**HISTORICAL-RECORD docs** (describe what was true at a specific past moment) → **PRESERVE the body truthfully. Bridge, don't rewrite.**
- Postmortems, handoffs, shipped plan bodies, old decision-log entries, CHANGELOG rows, archived changelogs
- These describe past states accurately. Leaving the old terminology is CORRECTNESS, not deferral.

**Why NOT blanket-rewrite history** (the load-bearing argument):
1. **The rename ship's existence depends on the historical record showing the OLD term.** `.E.1` IS "Core→Node rename." If you rewrite every pre-`.E.1` postmortem to say "node," then `.E.1`'s postmortem ("we renamed Core→Node") becomes nonsensical — renamed *from what*? The old-terminology references in history are load-bearing for understanding the rename's existence.
2. **Falsifying the evolution record damages institutional memory.** A multi-year project's memory should show HOW it got here, not a retconned monotone where it was "always" the new way. The honest evolution IS the valuable institutional memory.
3. **Effort on frozen docs has no forward payoff** — historical docs aren't read as current context; they're read as "what happened then."

This composes with [[feedback_archived_changelog_preservation_discipline]] (the changelog-specific instance) — this memory generalizes it to the whole doc system under a terminology rename.

**The bridge (how institutional memory "reflects the schema" WITHOUT falsifying history):**
1. **Canonical glossary** = single source of truth for the new schema (e.g., DESIGN_PHILOSOPHY § Glossary defining Deployment/Cluster/Node/ExecutionCore). Every new doc uses it.
2. **Terminology-evolution note** in the glossary: *"Terminology evolved at <ship>: <old>→<new>. Pre-<ship> historical docs use <old> accurately for their time; current + future docs use <new>."*
3. **Dir-level banner README** in historical-record dirs (postmortems/, handoffs/) pointing to the glossary note.
4. **Doc-find guide line** (CLAUDE.md § How to find anything) so future-search knows the old↔new bridge.

The bridge IS the institutional-memory artifact — it gives future-you/future-operator clarity at the old↔new seam without rewriting truth.

**"Don't defer" is fully satisfied by this** — every FORWARD-LOOKING doc is swept NOW (nothing punted); the bridge is built the same ship. Defer would be leaving forward docs in old terminology "for later"; that is NOT what preserving historical bodies is.

**Worked example:** v5.15.5.F.4d.1.D.1 doc-sweep. A.4 baseline found 5,087 per-core hits / 366 files. ~2,620 were in ephemeral/historical dirs (plan_checks 1,817 + handoffs 555 + postmortems 248). Operator (2026-05-28) chose option (A) bridge-note over (B) blanket-rewrite: sweep forward-looking (timeless CLAUDE/DOCS/DESIGN_SPECS ~1,150 + active `.E` plan bodies) + preserve historical bodies + glossary evolution-note + dir banners + doc-find line.

**How to apply:** at any architecture-wide rename, classify each doc population as FORWARD-LOOKING (sweep) vs HISTORICAL-RECORD (preserve+bridge) BEFORE the sweep. Build the canonical glossary + evolution-bridge the same ship. Never blanket-rewrite history.

**Sister:** [[feedback_archived_changelog_preservation_discipline]] (changelog-specific instance; this generalizes) + [[feedback_proactive_rename_candidate_surfacing]] (the rename-candidate discipline; this is the doc-population treatment side) + [[feedback_plan_body_length_no_target_loc]] (sister "institutional memory > arbitrary metric" framing) + [[feedback_motivated_collaborator_for_caramel]] (multi-year quality bar; institutional memory IS the deliverable) + [[feedback_single_source_of_truth_discipline]] (glossary as SSoT for the schema).
