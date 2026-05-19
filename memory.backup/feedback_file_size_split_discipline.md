---
name: feedback-file-size-split-discipline
description: "When file exceeds threshold (varies by file type), split into sub-files + convert original to INDEX"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: b025c86a-fb34-4d41-a80b-15461b4ca5ff
---

When a file exceeds its hard threshold, split into sub-files + convert original to INDEX. Generalizes the existing test-file-size discipline to ALL files (docs / sources / skills / ledgers).

**Thresholds:**

| File type | Hard threshold |
|---|---|
| Always-loaded docs (CLAUDE.md / CLAUDE.local.md / MEMORY.md) | 600 lines |
| Tests | 5000 lines OR 100 sections (existing CLAUDE.md rule) |
| Source headers | 1500 lines (TECH_DEBT-029 sister) |
| Source bodies | 2000 lines |
| Ledger files (TECH_DEBT / RBP / PARITY / FEATURE / HOT_PATH / LANDMINES) | 2000 lines |
| SKILL.md | 1500 lines |
| DESIGN_SPECS | 1200 lines |
| Plan body docs | 1200 lines (use `<plan-name>-examples.md` sidecar) |
| Memory rules | 500 lines (terseness expected) |

**Split + index pattern:**

1. Identify split criteria (by-cohort / by-status / by-domain / by-concern / by-date)
2. Create sub-files; each retains canonical content
3. Convert original to INDEX (`splits_into:` frontmatter; table of contents)
4. `rg`-sweep cross-refs; update to index OR sub-file as appropriate
5. Sub-files get `parent_index:` frontmatter pointing back

**Why:** Caramel surfaced 2026-05-18 — "maybe split up things that become mega files to have an index and like 'if file X becomes greater than Y, split it up and add an index entry'." Mega-files have invisible cumulative cost: slow to navigate, slow to load, drift-prone, token-budget-heavy when loaded.

**How to apply:**

1. **At doc creation time**: if predicting file will exceed threshold, design split from inception
2. **At entry-addition time**: if adding entries would push file over threshold, split FIRST then add (per CLAUDE.md test file size discipline pattern)
3. **At quarterly `/metadata-audit`**: report files exceeding soft warning + hard threshold
4. **At `/ship` skill close**: suggest split if any modified file crosses threshold this ship
5. **Choose split criteria carefully**: wrong criteria makes retrieval HARDER (split by date in active ledger = bad; split by status = good)

**Anti-patterns:**

- Splitting prematurely (file below threshold + still navigable)
- Splitting without rollback anchor (cross-ref breakage risk)
- Pointing external refs at sub-files directly (forces users to know split layout); ALL external refs should point at INDEX
- Wrong split criteria (forces retrieval through wrong axis)

**Skill cadence:**

- `/metadata-audit` (quarterly) reports threshold violations
- `/ship` skill amends suggest splits at ship-close
- CI tool `check_doc_metadata.py` flags violations at commit time

**Sister memories:**
- [[feedback-claude-md-guidelines-not-stuff-to-do]] — doc-layer separation; mega-files violate "fits in always-loaded context"
- [[feedback-categorical-triggers-over-hardcoded-refs]] — same axis; categorical structure prevents accumulation that leads to mega-files
- [[feedback-metadata-audit-quarterly]] — companion cadence that detects threshold violations
- [[feedback-iteration-spiral-signals-audit-meta-gap]] — sister meta-pattern (recognition trigger)
