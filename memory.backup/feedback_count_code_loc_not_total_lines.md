---
name: feedback-count-code-loc-not-total-lines
description: "When checking file-size thresholds (split discipline / function length / complexity audit), count ACTUAL CODE LOC (exclude comments + blanks). NOT total lines via `wc -l`. Heavily-documented files shouldn't be penalized vs sparse ones of same code mass. Codified 2026-05-27 post-`.B.6` B.4.1 revert after splitting Run.hpp on total-lines metric (2,436) when actual code-LOC (1,406) was already UNDER 1,500 threshold."
metadata: 
  node_type: memory
  type: feedback
  originSessionId: phase-e-ship-close-v5.15.5.F.4d.1.B.6
  sister_specs: [feedback_file_size_split_discipline.md, feedback_dont_measure_structural_work_by_loc.md]
  tags: [code-loc-counting, doc-discipline]
---

**When checking file-size thresholds (split discipline / function length / complexity audit), count ACTUAL CODE LOC.** Exclude:

- Comment-only lines (single-line `//` + block-comment lines `/*` / `*` / `*/`)
- Blank lines
- Lines containing ONLY closing braces `}` (debatable; usually included)

**Why:** A heavily-documented file with rich cold-pickup context shouldn't be penalized vs a sparsely-documented one of the same code mass. Navigation cost + cognitive load track code-LOC; comments REDUCE cognitive load (more context per code line = better). Total-lines counting incentivizes stripping useful documentation to dodge the threshold, which is wrong direction.

**Counting tool:**
```bash
grep -vE '^\s*(//|\*|/\*|$)' <file> | wc -l   # approximate
cloc <file>                                    # more precise (if installed)
```

## Worked example — the lesson that codified this discipline

At v5.15.5.F.4d.1.B.6 Phase B Step B.4.1 (2026-05-27 AM):
- `CoreFrameworks/EngineSharded/Run.hpp` was 2,436 total lines (62% over 1,500-line source-header threshold by total-lines count)
- Operator approved Option A "full sub-split" based on total-lines metric
- Agent executed ~30 min of work creating 5 Run/* sub-sub-files
- THEN actual-code count surfaced: Run.hpp pre-B.4.1 was 1,406 code-LOC (58% comments+blanks) — already UNDER threshold by code-LOC
- B.4.1 was reverted (commit 6323c17)

**Lesson:** COUNT CODE-LOC, NOT TOTAL-LINES BEFORE triggering split work.

## How to apply

1. **At threshold check time:** run `grep -vE '^\s*(//|\*|/\*|$)' <file> | wc -l` BEFORE deciding split is warranted
2. **At plan-draft time:** include code-LOC count alongside total-lines in any "file is over threshold" framing
3. **At /metadata-audit / /ship audit:** if reporting size violations, report BOTH total + code-LOC; flag only when code-LOC exceeds threshold

## Anti-patterns

- **Triggering split work on `wc -l` total-lines alone** — adds churn + LOC overhead (file headers + arg-list translations) for cosmetic threshold compliance with no real maintainability win
- **Stripping useful documentation to dodge total-lines threshold** — wrong direction; comments are NET-POSITIVE for cognitive load
- **Counting all comment styles separately** — the `^\s*(//|\*|/\*|$)` regex catches single-line `//`, block-comment continuation `*`, block-comment start `/*`, and blank lines; sufficient for typical C++ codebases

## Sister memories

- [[feedback_file_size_split_discipline]] — parent discipline (file-size threshold split + INDEX pattern); this rule is the methodology sub-discipline for HOW to count
- [[feedback_dont_measure_structural_work_by_loc]] — sister at the "LOC is incidental" axis; this rule applies the same principle to file-size thresholds

## DESIGN_SPECS sister

- `doc-disciplines/file-size-split-discipline.md` § "Threshold counting methodology" (v1.2 amendment 2026-05-27 codified this discipline as part of the parent file-size discipline)

## Recognition markers

- Considering split work on a file
- File-size violation report from /metadata-audit / /ship
- "This file is over threshold" framing in plan body / audit report
- Comparing two files of similar code-mass with different documentation density

## When this rule applies

Per feedback_categorical_triggers_over_hardcoded_refs:

- Any file-size threshold check (per `file-size-split-discipline.md` table)
- Any function length / complexity audit
- Any "file is too big" decision moment
- Any maintenance-overhead claim based on `wc -l` numbers
