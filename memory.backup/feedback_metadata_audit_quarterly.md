---
name: feedback-metadata-audit-quarterly
description: Fire /metadata-audit skill on quarterly cadence to catch doc-system drift mechanically
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b025c86a-fb34-4d41-a80b-15461b4ca5ff
---

Fire `/metadata-audit` skill on quarterly cadence (sister to `/anti-spaghetti` quarterly cadence per [[project-anti-spaghetti-audit-cadence]]). Catches doc-system drift mechanically: undefined tags / missing frontmatter / broken sister-doc links / Stage 2 DRAFTs older than N sprints / singleton tags.

**Trigger conditions:**

- **Quarterly cadence** — regular sweep regardless of sprint phase
- **Post-codification sweep** — after any new DESIGN_SPEC promotion (Stage 2 → Stage 3) verify cohort frontmatter alignment
- **Post-folder restructure** — TECH_DEBT-113 folder subdivision triggers full audit
- **Ad-hoc** — when "I can't find X" surfaces or finding-issues threshold suspected

**What `/metadata-audit` reports:**

1. Specs missing frontmatter (where doc-frontmatter-convention.md requires it)
2. Specs with undefined tags (typos against doc-tag-vocabulary.md)
3. Broken sister-doc links (bidirectional verification)
4. Stage 2 DRAFTs older than N sprints (promotion candidates)
5. Singleton tags (used by only 1 doc — consolidation candidates; ADVISORY)
6. Filesystem path mismatches with `type:` frontmatter (post TECH_DEBT-113 folder restructure)
7. Dead cross-references (sister_specs pointing to nonexistent paths)

**Why:** Doc-system drift accumulates invisibly. Caramel surfaced 2026-05-18 — "instead of generalized stuff we made hardcoded references, which is why we're having so many issues finding stuff." Quarterly mechanical audit catches drift before it reaches finding-issues threshold.

**How to apply:**

1. **Quarterly:** fire `/metadata-audit` at sprint boundary (every ~12 weeks); report total findings + classify A KEEP / B WORTH-FIXING / C CONSOLIDATE
2. **Post-codification:** after promoting any spec from Stage 2 → Stage 3, fire targeted audit on cohort
3. **Operator-flagged:** if Caramel surfaces "I can't find X" or any finding-issues signal, fire ad-hoc audit
4. **CI defense-in-depth:** `check_doc_metadata.py` runs at commit time; catches drift faster but with narrower scope (per-commit-changed files only)

**Skill status:** `/metadata-audit` is QUEUED at `.C` candidate ship per TECH_DEBT-115 Phase 2. Doesn't exist yet. Manual audit via `rg` patterns from CLAUDE.md § How to find anything is the interim workflow.

**Sister memories:**
- [[project-anti-spaghetti-audit-cadence]] — sister cadence-locked quarterly audit (code-structural sweep)
- [[feedback-categorical-triggers-over-hardcoded-refs]] — the discipline this audit enforces
- [[feedback-claude-md-guidelines-not-stuff-to-do]] — the doc-layer separation this audit verifies
- [[feedback-iteration-spiral-signals-audit-meta-gap]] — sister meta-pattern (recognition trigger)
