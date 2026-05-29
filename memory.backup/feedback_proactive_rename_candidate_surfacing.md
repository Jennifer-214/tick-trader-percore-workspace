---
name: feedback_proactive_rename_candidate_surfacing
description: "Throughout multi-ship architectural restructures, proactively flag rename candidates as encountered (not just at planned rename ships) — surface to operator with classification, maintain running candidates list, reduce operator cognitive load from inconsistent terminology"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: f8d1354c-702d-4ff6-b985-c90cafb1a1f2
---

During multi-ship architectural restructures (e.g., the `.E` sub-sprint with Cluster/Node/Deployment + multi-exchange + headless reshape), naming inconsistencies between old and new architecture accumulate confusion. Discipline: **PROACTIVELY surface rename candidates as encountered** — not just at planned rename ships.

**Why:** As the operator works through multi-ship restructure, encountering N different names for similar concepts creates cognitive load. Per operator-stated 2026-05-28: *"to reduce confusion for myself would be good"*. Operator cognitive-load reduction is part of `feedback_motivated_collaborator_for_caramel` quality bar — the codebase isn't done until the operator can navigate it without holding stale terminology in working memory.

**How to apply:**

1. **While auditing plan bodies / reviewing code / sweeping DESIGN_SPECS / drafting plan bodies / running `/bug-check`-style scans / reading any artifact:** when a name doesn't match the new post-restructure architecture, FLAG it.
2. **Don't auto-rename.** Classify the candidate per these severity tiers and surface inline to operator:
   - **CLOSE-NOW** — small + clear + fits current ship scope; rename inline within current ship
   - **QUEUE-FOR-NEXT-RENAME-SHIP** — substantive + clear new target; surface as forward-promise to next rename ship's plan body
   - **TECH_DEBT-DEFER** — substantive + needs operator triage; create TECH_DEBT entry with rationale + queue at named future ship
   - **AMBIGUOUS** — unclear if rename helps OR which new name fits; surface to operator with both-sides analysis
3. **Maintain running list** at workspace file `plans/<sprint>/rename-candidates-running-list.md` — accumulates throughout sub-sprint. Each entry: surface (file:line OR doc OR cfg field) | old name | suggested new name | tier | rationale | target ship for closure.
4. **Surface at each ship's planning gate** — at every plan body draft, ask: "any rename candidates from the list that fit this ship's scope?" Incremental absorption rather than big bang. Per `feedback_no_defer_for_effort`: close-now if clear; defer only when ambiguous.
5. **Cross-ref glossary** — every rename candidate cites the canonical glossary entry (per `.D.1` glossary anchor in `DOCS/DESIGN_PHILOSOPHY.md` § Glossary) to ensure the rename target is the canonical term. Prevents inventing yet another ad-hoc name.
6. **Sister-cohort amendment completeness** — when renaming X, enumerate sister surfaces (per `feedback_sister_cohort_amendment_completeness`) so the rename propagates correctly across docs + code + tests + plan bodies + memory.

**Worked example:** `.D.1` doc sweep surfaced `engine_mode` + `engine_arch` + `BacktestSharded_Run` as candidate renames BEYOND the Core→Node rename scope. Each classified per tier (engine_mode + engine_arch = QUEUE-FOR-NEXT (`.E.0.1` precursor); BacktestSharded_Run = QUEUE-FOR-NEXT (`.E.1` Foundation)). TECH_DEBT entries opened at `.D.1` ship close; folded into successor ship scope. Discipline let `.D.1` stay scoped to doc-rename without ballooning, while accumulating candidates for downstream closure.

**Anti-pattern this prevents:** "Surface a rename idea verbally; forget it; encounter it again 3 ships later still unaddressed; rediscover the same idea; operator confused by why it didn't get fixed". Mechanical running-list capture prevents memory-only drift per M7 parent discipline.

**Out of scope (NOT this discipline):**
- Premature renames before the new architecture stabilizes (per `feedback_consult_on_audit_findings` — surface, don't auto-execute)
- Renames that contradict canonical glossary (always cross-ref glossary first)
- Renames during pure bug-fix ships (preserve scope discipline; rename ships handle rename work)

**Sister:** [[feedback_motivated_collaborator_for_caramel]] (cognitive-load reduction = quality bar) + [[feedback_no_defer_for_effort]] (defer only when ambiguous; not when clear) + [[feedback_sister_cohort_amendment_completeness]] (renames are sister-cohort surfaces; complete enumeration matters) + [[feedback_avoid_substring_replace_all_on_member_access]] (parent rule on rename mechanics) + [[feedback_structural_enforcement_when_memory_insufficient]] (M7 — running list IS the structural mechanism preventing memory-only drift) + [[feedback_categorical_triggers_over_hardcoded_refs]] (rename candidates surface categorical patterns; track patterns not just instances).
