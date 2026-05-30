---
name: TYPE_SLUG
description: ONE_LINE_RECALL_SUMMARY
metadata:
  type: feedback
  tags: []
  sister_specs: []
---

FACT_BODY

**Why:** WHY_LINE

**How to apply:** HOW_LINE

Related: [[related_memory_filename]]

<!-- TEMPLATE GUIDANCE — delete this block on instantiate (/doc-create strips it).

This is the canonical Claude Code institutional-memory file: ONE fact per file.

Frontmatter — two layers, do not collapse them:
  HARNESS-NATIVE (load-bearing — the recall system reads these; never remove):
    name:         = the filename stem, prefixed feedback_/user_/project_/reference_.
    description:  one line. Recall RANKS relevance on this string — make it a precise trigger, not a title.
    metadata.type: feedback (how Claude should work) | user (who Caramel is) |
                   project (ongoing work, not derivable from code/git) | reference (external pointer).
  DOC-SYSTEM (nested UNDER metadata: on purpose — survives harness frontmatter rewrites):
    metadata.tags:         concern-axis tags from doc-tag-vocabulary.md (e.g. audit-methodology,
                           framework-discipline). Empty [] is allowed.
    metadata.sister_specs: UNIFIED cross-links — related memory FILENAMES (feedback_x) AND
                           DESIGN_SPECS paths (meta-disciplines/y.md) in one list. Bidirectional:
                           a load-bearing sister should point back (check_doc_metadata --bidirectional
                           red-builds one-way links). A forward-link to a not-yet-written memory = INFO.

Body:
  - ONE fact, stated plainly.
  - feedback / project → follow with **Why:** + **How to apply:** lines.
  - Link related memories inline with [[filename]] (filename form, NOT the name: slug — WH-1).

Path + index:
  - Write to ~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/TYPE_SLUG.md
  - Add a one-line pointer to MEMORY.md: `- [Title](TYPE_SLUG.md) — short hook.`

Per doc-frontmatter-convention.md § memory/*.md (Stage 3) + D-89 (the schema decision).
-->
