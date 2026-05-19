---
name: feedback-categorical-triggers-over-hardcoded-refs
description: "In always-loaded content (CLAUDE.md / CLAUDE.local.md / MEMORY.md / SKILL.md), categorical triggers > hardcoded refs; pattern-match retrieval > ID-lookup"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b025c86a-fb34-4d41-a80b-15461b4ca5ff
---

When writing always-loaded content (CLAUDE.md, CLAUDE.local.md, MEMORY.md, SKILL.md files), use categorical pattern triggers — not hardcoded refs to specific functions / files / TECH_DEBT entries / sprint versions.

**The discipline:** Always-loaded content gets retrieved by pattern-match ("does this discipline apply to what I'm doing?"), not by ID-lookup ("does this work touch TECH_DEBT-105?"). Hardcoded refs in trigger bodies force ID-lookup retrieval — Caramel (or fresh-Claude) has to ALREADY know the specific TECH_DEBT-NNN or function name to find the discipline. That defeats the purpose of always-loaded content.

**Three buckets when auditing always-loaded content:**

**A. KEEP (stable catalog IDs — designed-stable references):**
- Class N references (RECURRING_BUG_PATTERNS catalog ID; "Class 18", "Class 21")
- H invariant N references ("H6", "H13", "H20")
- M-discipline N references ("M1", "M4")
- DESIGN_SPECS pattern file names (`structural-fix-preferred-decision-framework.md`)
- FOREACH_* X-macro registry names (`FOREACH_STAMP_BOUND_DERIVED`)
- TECH_DEBT-NNN refs in CANONICAL anchors (e.g., `TECH_DEBT-018 → /precoding-audit-gate` is a canonical anchor where the entry was the genesis of the skill — NOT drift)
- Canonical doc paths (`DOCS/HOT_PATH_CHANGELOG.md`, `DOCS/CLAUDE_ML_INVARIANTS.md`)

**B. KEEP with framing (worked examples — canonical history per [[feedback-tech-debt-skill-drift-pragmatic-triage]]):**
- file:line refs INSIDE `<EXAMPLE>` or "Worked example" or "Anti-pattern caught (vX.Y.Z YYYY-MM-DD)" blocks
- "Codified at v5.X.Y after <event>" history notes — explicit history-marker framing
- "(NEW post-v5.X.Y)" markers only when explicitly history-framed
- Specific sprint anchors inside framed examples

**C. CONVERT (drift candidates — true hardcoded refs that should be categorical):**
- Hardcoded TECH_DEBT-NNN refs in TRIGGER BODIES (NOT in canonical anchors/examples) → categorical pattern triggers ("when work touches X-class issue", not "when work touches TECH_DEBT-105")
- Specific function names in WHEN sections → pattern-shape ("any cfg-derived consumer template fn", not "any modification of populate_stamp_cfg_from_derived")
- Specific file paths in WHEN/WHAT sections → glob/pattern ("any file matching `MemHeaders/*Registry.hpp`", not "MemHeaders/CfgGateRegistry.hpp")
- Sprint version markers in WHAT/WHEN sections beyond history notes → remove or generalize
- Canonical-list duplication in trigger bodies — defer to registry/ledger:
  - Stamp-bound cfg field lists → defer to `FOREACH_STAMP_BOUND_CFG_DERIVED` registry
  - Hot-path file lists → defer to `DOCS/HOT_PATH_CHANGELOG.md` cadence tier
  - Architectural-sprint-guards → defer to `DOCS/CLAUDE_ML_INVARIANTS.md` / `INVARIANTS_MAP.md`
  - Deprecated-path lists → defer to CLAUDE.md deprecation notes
  - Hardcoded counts ("19 docs as of v5.14.10") → "count grows over sprints"

**Why:** Caramel surfaced 2026-05-18 that hardcoded refs in skills/docs are why she struggles to find things. TECH_DEBT-109 (skill drift triage, sprint-phrasing-level) closed worked-example drift but did NOT close STRUCTURAL duplication where always-loaded content shadows canonical lists living in registries/ledgers. Structural skill audit (TECH_DEBT-112) found ~50 sites across 22 skills duplicating canonical lists.

**How to apply:**

1. **Editing SKILL.md / CLAUDE.md / CLAUDE.local.md / memory file** — for each trigger-body reference, ask: "is this a stable catalog ID (A KEEP) or worked example (B KEEP) or canonical-list duplication (C CONVERT)?"
2. **Canonical-list duplication detection** — if the trigger body lists 5-10 fields/files/functions, ask "is there a registry or ledger that owns this list as source of truth?" If yes → defer to that source; replace inline list with categorical pointer.
3. **Drift sentinels** — "v5.X.Y had", "(line ~N)", "as of vX.Y", "Currently N fields", "Recent <thing>" — all signal canonical-list duplication that should defer.
4. **Worked examples are fine** — explicit "Anti-pattern caught (v5.14.10 date)" / "Worked example:" / "e.g." / "Example output:" framing preserves canonical history without claiming categorical authority.
5. **Periodic audit cadence** — fire `/anti-spaghetti` or dedicated skill-audit at sprint boundary to catch new C-bucket drift before it accumulates.

**Sister memories:**
- [[feedback-claude-md-guidelines-not-stuff-to-do]] — companion (doc-layer separation; WHERE content goes). This memory is the WHAT SHAPE axis: in always-loaded content, what shape do triggers take?
- [[feedback-tech-debt-skill-drift-pragmatic-triage]] — predecessor (TECH_DEBT-109 sprint-phrasing-level drift); this memory addresses the STRUCTURAL layer below.
- [[feedback-structural-fix-for-recurring-class]] — parent (structural-fix-over-patch); the defer-to-registry pattern IS the structural fix for canonical-list-duplication drift.
- [[feedback-enumerate-consumers-before-registry-row-deletion]] — sister (consumer-enumeration discipline; this memory addresses the producer side: the SOURCE of truth for canonical lists).
