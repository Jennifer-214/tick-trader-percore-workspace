---
name: feedback-claude-md-guidelines-not-stuff-to-do
description: "Always-loaded docs (CLAUDE.md / CLAUDE.local.md / MEMORY.md / SKILL.md) are TIMELESS guidelines + index, not in-flight TODO content"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b025c86a-fb34-4d41-a80b-15461b4ca5ff
---

Always-loaded docs are GUIDELINES + INDEX (timeless content; "how to think about this codebase"); they are NOT a work queue. On-demand docs (plans/, ledgers, handoffs) carry the in-flight ephemeral work.

**Doc layer mapping:**

| Layer | Type | Content |
|---|---|---|
| `CLAUDE.md` (always-loaded) | TIMELESS | Orientation + invariants + priority headlines + doc-layer index |
| `CLAUDE.local.md` (always-loaded) | TIMELESS index + EPHEMERAL pointer | Going-forward rules + sprint state POINTER (not body) + auto-write contracts |
| `memory/` (always-loaded) | TIMELESS | Operator-collaboration rules + project context |
| `SKILL.md` files (loaded on invocation) | TIMELESS | WHAT/WHEN/HOW with categorical triggers |
| `DOCS/DESIGN_PHILOSOPHY.md` (on-demand) | TIMELESS depth | WHY + worked examples |
| `DESIGN_SPECS/<name>.md` (on-demand) | TIMELESS recipes | Pattern bodies |
| `DOCS/RECURRING_BUG_PATTERNS.md` (on-demand) | TIMELESS catalog | Anti-pattern instances |
| `plans/<sprint>/` (on-demand) | EPHEMERAL | In-flight ship plans + handoffs |
| `DOCS/TECH_DEBT.md` + `PARITY_ISSUES.md` + `FEATURE_LOOKUP.md` (on-demand) | EPHEMERAL | Accumulating ledgers |

**Drift sentinels in always-loaded docs:**
- "queued as v5.X.Y sub-ship" — in-flight TODO; move to TECH_DEBT
- "(NEW post-v5.X.Y)" — sprint-version stamp; remove or convert to history note
- "Recent <thing>" wording — rots over time; replace with stable pointer ("see canonical registry at X for current catalog")
- Specific TECH_DEBT-NNN in trigger bodies that should be categorical pattern triggers — convert per [[feedback-categorical-triggers-over-hardcoded-refs]]
- Sprint-specific phasing of generic concepts ("Step 1.6.3 of .B.3" in a general SKILL.md trigger) — convert to categorical

**Stable references that KEEP in always-loaded docs:**
- Catalog IDs: Class N, H N, M N, DESIGN_SPECS pattern names, FOREACH_* registry names
- History notes: "Codified at v5.X.Y after <event>" — explicit history-marker framing
- Canonical anchors: TECH_DEBT-018 → /precoding-audit-gate (the entry was the genesis; this is a canonical anchor, not drift)

**Why:** Caramel surfaced 2026-05-18 that always-loaded docs drift over time when TODO content + sprint-specific phrasing leaks in. The reason she was struggling to find things — hardcoded refs in always-loaded content. CLAUDE.md / SKILL.md / memory should function as a stable "how to think" map that doesn't need updating per sprint.

**How to apply:**

1. **Before editing always-loaded docs** — ask "is this content TIMELESS or EPHEMERAL?" Timeless = guidelines + categorical triggers + cross-ref pointers. Ephemeral = sprint-specific TODO / in-flight state / version markers.
2. **Detected drift in existing content** — extract to canonical ledger (TECH_DEBT for deferrals; plan body for in-flight phasing; sprint MASTER for sprint state); replace with stable pointer.
3. **CLAUDE.local.md sprint-state table** — table cells should be POINTERS to canonical state (plan body + sprint MASTER + handoff); not bodies of current state.
4. **When in doubt** — write the EPHEMERAL version in plans/ first; promote a GENERALIZED version to always-loaded docs only when the pattern matures past Stage 4 (≥2 codebase applications + DESIGN_SPEC body exists).

**Sister memories:**
- [[feedback-categorical-triggers-over-hardcoded-refs]] — companion axis (categorical vs hardcoded). Doc-layer-separation says WHERE content goes; categorical-triggers says WHAT SHAPE the triggers take in always-loaded docs.
- [[feedback-plans-have-explicit-end-goal]] — companion (the ephemeral side: plans should have explicit end goals so they self-bound).
- [[feedback-codify-design-principles-claude-md]] — promotion criteria (when to promote a pattern to CLAUDE.md from DESIGN_SPECS).
