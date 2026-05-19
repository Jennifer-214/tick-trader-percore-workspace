---
name: feedback-plans-have-explicit-end-goal
description: "MASTER plans and sub-plans MUST codify explicit end goals + acceptance criteria so every ship answers \"what does this deliver\""
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b025c86a-fb34-4d41-a80b-15461b4ca5ff
---

Every MASTER plan and sub-plan body must include an explicit "End goal" section. The discipline catches plans that drift into "implementation steps without a clear deliverable" — every plan should be answerable to the question "what does this ship CLOSE / DELIVER, and how do we verify?"

**MASTER plan structure:**

- **Sprint end goal** (1-2 sentences): the overarching deliverable the sprint produces (e.g., "make codebase more maintainable for future development"). NOT a list of features; the META-goal that ALL sub-ships serve.
- **Per-sub-ship end goal column** in the ship pipeline table: each sub-ship's contribution to the sprint goal.
- **Sprint-end verification**: what proves the sprint achieved its goal (e.g., "all Class N closed; framework auto-flow at N% of cfg-derived surfaces; HOT_PATH_CHANGELOG shows N additions").

**Sub-plan structure (per `DESIGN_SPECS/plan-templates/future-oriented-plan-template.md`):**

- **Ship end goal** (1 sentence): "this ship closes <surface> via <mechanism>" OR "this ship delivers <capability> by <approach>".
- **Acceptance criteria** (bullet list):
  - CLOSED bug classes (Class N catalog entries, with /bug-check verifying N→0)
  - CLOSED TECH_DEBT entries (with ledger status flip)
  - LANDED DESIGN_SPECs (Stage 2 DRAFT → Stage 3 first reference at this ship)
  - Hot path verification (UNTOUCHED with calls_graph_diff GREEN OR TOUCHED with HOT_PATH_CHANGELOG entry)
  - Wire-format replay determinism (cfg roundtrip byte-identical)
  - 5 binaries clean + tests GREEN
- **How this contributes to sprint MASTER goal**: explicit tie-back so reviewers can verify alignment.

**Handoffs cite both:** Sprint end goal + Ship end goal at top so a fresh-context Claude understands the ship's purpose in 2 sentences before reading 100KB of detail.

**Why:** Caramel surfaced 2026-05-18 that plans currently rely on the SHIP NAME ("Legacy empty-out + Phase L cross-tool decoupling") to convey purpose. That works for senior contributors who know the surface, but fails for cold-pickup or fresh-Claude-context. Explicit end goals make plans self-bounding — verifiable "did this ship achieve its goal" gate replaces ambiguous "did this ship close enough scope".

**How to apply:**

1. **Drafting a new sub-plan** — `DESIGN_SPECS/plan-templates/future-oriented-plan-template.md` § End goal section is REQUIRED; `/plan-draft` skill scaffolds.
2. **Drafting a new MASTER plan (sprint or umbrella)** — `DESIGN_SPECS/plan-templates/sprint-master-plan-template.md` § Sprint end goal + sub-ship pipeline table with end-goal column.
3. **Retrofitting existing plans** — at per-sub-ship cycle update step, add explicit End goal section if missing. `.B.3` plan body retrofit precedent (2026-05-18).
4. **`/handoff` skill** — generated handoffs must include Sprint end goal (1 line) + Ship end goal (1 line) at top frontmatter.

**Verification:**
- `/readiness` Check 30 (extended): verify "End goal" section present in plan body (currently verifies "Design space + future-oriented choice")
- New `/readiness` Check or amendment for MASTER plan structure

**Sister memories:**
- [[feedback-new-plans-use-future-oriented-template]] — parent template discipline (this is the End goal subsection inside that template).
- [[feedback-claude-md-guidelines-not-stuff-to-do]] — companion (this is the ephemeral side: plans must self-bound so they don't leak into always-loaded docs).
- [[feedback-plan-right-not-fast]] — planning discipline (this is the structural element of plan-right).
