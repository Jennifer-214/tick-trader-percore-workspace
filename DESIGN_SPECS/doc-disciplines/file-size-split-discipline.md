---
type: doc-discipline
stage: 3-first-canonical
version: 1.4
established: 2026-05-18
last_amended: 2026-05-27
tags: [doc-discipline, structural-fix, pattern-codification, wontfix-rationale]
surface: [doc-pipeline]
sister_specs: [doc-frontmatter-convention.md, ledger-entry-templates.md, categorical-triggers-in-always-loaded-docs.md, cpp17-inline-variable-for-header-shared-state.md, single-source-of-truth-discipline.md]
applies_at_skills: [/metadata-audit, /ship]
---

# File-size split discipline

**Established:** 2026-05-18 (v5.15.5.F.4d.1.B.3 doc-layer refresh — codified after Caramel surfaced "if file X becomes greater than Y, split it up and add an index entry")
**Status:** Stage 3 FIRST CANONICAL v1.4 — RESCOPED at v5.15.5.F.4d.1.B.7 per AI-driven solo workflow (operator C1 directive); test 5K rule retained; all other thresholds become guidelines not mandates; subfolder pattern (`.B.6` first canonical) stays Stage 3 frozen for future cohort use

---

## AI-driven workflow scoping (added v1.4, 2026-05-27)

**Discipline applies SELECTIVELY in AI-driven solo workflow.** This scoping section captures the operator C1 decision 2026-05-27 to cancel the `.B.5-.B.11` file-size discipline maintenance umbrella + close TECH_DEBT-029/-114/-116/-117/-118 as `wontfix-per-ai-workflow`.

**WHY the discipline was originally codified (2026-05-18):** human contributors navigating large files incur cognitive load; code review by contributors scales poorly on multi-thousand-line files; IDE/editor performance degrades on mega-files; mega-file accumulation produces Class 32 anti-pattern. These concerns motivated the universal threshold table.

**WHY AI-driven workflow weakens the motivation:** the original motivations PRESUME human contributors. In a single-contributor AI-driven workflow (FoxML_Trader_v2 development pattern as of 2026-05-27):
- Claude 1M context handles 6K-line files trivially via single Read tool call
- AI doesn't experience "cognitive load" from large files the way humans do
- Code review concern doesn't apply (single contributor)
- IDE perf is irrelevant (Claude reads file content directly, not via interactive IDE)
- Compile time UNCHANGED for header-only template code (subfolder split doesn't speed compile; only `.cpp` split would, and most code is `.hpp`)
- Git diff scoping helps human reviewers; AI processes diffs differently (less scope-sensitive)

**WHAT REMAINS load-bearing:**
- **Test 5K rule RETAINED** — test infrastructure genuinely benefits from split: test binaries compile faster when split into domain-aligned units; test reliability concern (large test files harder to verify completeness); test parallel execution benefits from binary boundary; TECH_DEBT-127 stays OPEN as the test-reliability surface (sister to test 5K rule)
- **Subfolder pattern stays Stage 3 FROZEN** — `.B.6` first canonical at EngineSharded subfolder split is preserved as institutional knowledge; pattern is validated + ready for application if/when human contributors join project OR if a specific file's complexity genuinely benefits from sub-file boundaries (operator-decided per-instance)
- **Ledger 2K threshold reviewed inline at TECH_DEBT-116 closure** — TECH_DEBT.md @ 2013 lines is grep-driven access not navigation-driven; AI handles trivially; threshold not load-bearing
- **RECURRING_BUG_PATTERNS.md split DONE incidentally** — closed as `done-incidentally` at TECH_DEBT-117 (file was split into per-class sub-files 2026-05-18 prep work; original intent already realized)

**WHEN to revisit:** if (a) human contributors join the project, OR (b) AI tooling changes meaningfully (smaller context window, different file-reading patterns), OR (c) a specific file's complexity genuinely benefits from sub-file boundaries (operator-decided per-instance), reopen this discipline for that file/cohort. The subfolder pattern at `.B.6` is the canonical shape ready for application; the discipline body below (threshold table + split+index pattern) provides the mechanical procedure.

**Cross-references:**
- Operator C1 directive 2026-05-27 (this scoping codifies)
- TECH_DEBT-029/-114/-116/-117/-118 closure at v5.15.5.F.4d.1.B.7 (all 5 closed; see `DOCS/tech-debt/open.md` for closure rationales + closure_at fields)
- `.B.6` first canonical subfolder pattern (frozen institutional knowledge)
- CLAUDE.md § File-size split discipline (scoped 2026-05-27 with pointer here)
- CLAUDE.local.md going-forward rule "File-size split discipline" (amended 2026-05-27 with scoping)

---

Generalizes the existing test-file-size discipline (CLAUDE.md `Test file size discipline` rule + TECH_DEBT-029 source-file analog) to ALL files. When file size crosses threshold, split + create index entry.

---

## Threshold counting methodology (NEW 2026-05-27 PM)

**Thresholds count ACTUAL CODE LOC, NOT total lines.** Exclude:
- Comment-only lines (single-line `//` + block-comment lines `/*` / `*` / `*/`)
- Blank lines
- Lines containing ONLY closing braces `}` (debatable; usually included)

**Rationale:** A heavily-documented file with rich cold-pickup context shouldn't be penalized vs a sparsely-documented one of the same code mass. Navigation cost + cognitive load track code-LOC; comments REDUCE cognitive load (more context per code line = better). Total-lines counting incentivizes stripping useful documentation to dodge the threshold, which is wrong.

**Counting tool:** `grep -vE '^\s*(//|\*|/\*|$)' <file> | wc -l` (approximate; misses `/* ... */` block boundaries occasionally). For more precise counts: `cloc <file>` (if installed).

**Worked example (the lesson that codified this discipline, 2026-05-27 PM):**

At v5.15.5.F.4d.1.B.6 Phase B Step B.4.1, Run.hpp was 2,436 total lines (62% over 1,500 threshold by total-lines count). Operator approved Option A "full sub-split" based on total-lines metric. Agent executed ~30 min of work creating 5 Run/* sub-sub-files. THEN actual-code count surfaced:

- Run.hpp pre-B.4.1: 2,436 total / **1,406 code** (58% comments+blanks)
- Threshold by code-LOC: **already UNDER 1,500** ✓

B.4.1 was reverted (commit 6323c17). Methodology lesson: COUNT CODE-LOC, NOT TOTAL-LINES. File-size-split-discipline.md amended this section.

**Anti-pattern to avoid:** triggering split work based on `wc -l` (total-lines) without first computing code-LOC. Adds churn + LOC overhead (file headers + arg-list translations) for cosmetic threshold compliance with no real maintainability win.

---

## Thresholds by file type

| File type | Soft warning | Hard threshold | Action at threshold |
|---|---|---|---|
| ALWAYS-LOADED docs (CLAUDE.md / CLAUDE.local.md / MEMORY.md) | 400 lines | **600 lines OR the harness BYTE cap — see below (binding)** | Compress index entries to their ≤1-line contract; extract sections to on-demand reference docs |
| Test files (`tests/*.cpp`) | 3000 lines OR 60 sections | 5000 lines OR 100 sections | Split into domain-aligned sub-files (per CLAUDE.md existing rule) |
| Source headers (`*.hpp` / `*.h`) | 1000 lines | 1500 lines | Split into decl/parser/defaults/validate sub-files (per TECH_DEBT-029) |
| Source bodies (`*.cpp` / `*.c`) | 1500 lines | 2000 lines | Split by concern (per TECH_DEBT-029) |
| Ledger files (TECH_DEBT.md / PARITY_ISSUES.md / RECURRING_BUG_PATTERNS.md / FEATURE_LOOKUP.md / HOT_PATH_CHANGELOG.md / LANDMINES.md) | 1500 lines | 2000 lines | Split into per-cohort or per-entry files + ledger becomes INDEX |
| SKILL.md files | 1000 lines | 1500 lines | Extract per-section sidecar files; SKILL.md keeps invocation + section index |
| DESIGN_SPECS | 800 lines | 1200 lines | Extract worked-example sidecar (`<spec-name>-examples.md`); main spec keeps body + cross-refs |
| Plan body docs | 800 lines | 1200 lines | Extract code-sample sidecar (`<plan-name>-examples.md`) per existing convention |
| Memory rules | 300 lines | 500 lines | Memory rules SHOULD be terse — if exceeding, consider whether the rule is doing too much |

### Always-loaded docs: the BYTE budget is the binding ceiling (not the line count) — added 2026-06-02

**The 600-line threshold above is a PROXY; the real ceiling is the harness's per-doc context-load BYTE budget** — `CLAUDE.md` / `CLAUDE.local.md` ≈ **40,000 bytes** each; `MEMORY.md` ≈ **24.4 KB**. Exceed it and the harness **silently TRUNCATES** the doc mid-file (observed 2026-06-02: `MEMORY.md` clipped — "Only part of it was loaded"), dropping load-bearing governance content with NO error. A doc can be UNDER 600 lines but OVER the byte cap (`CLAUDE.local.md` hit 42.3 KB at 229 lines — dense one-liners), **so the line count alone misses it.**

- **Guard (mechanical, not a guideline):** `tools/check_always_loaded_budget.py` — HARD in `check_session_docs.sh`, teeth-proofed via `--selftest`, caps as SSoT in the tool, NEAR-band warning ≥90%. `.absolute()`-resolved so it works when symlinked from the private workspace (LANDMINE 5).
- **Fix order — compress before split:** the bloat is usually a CONTRACT VIOLATION (index entries grown past their "≤1 line / ≤200 char" rule), not too-many-entries → **compress first** (zero info loss; detail lives in the canonical doc/memory body). Only when a genuinely-large entry-count can't fit is it time to **split** (e.g. `MEMORY.md` → hot index + an extended index loaded at `/accept-handoff`) — the guard's recurring NEAR/OVER is what tells you you've hit that point.
- This is the **M7 structural close** of the "always-loaded doc silently truncates" class (meta-anti-pattern **WH-4**): convention-only compression RECURRED (`MEMORY.md` compressed 2026-05-26, over budget again 2026-06-02) → a standing guard replaces periodic manual trimming. The deeper rule: **guard the REAL limit (harness bytes), not a human proxy (line count)** — a guideline in the wrong unit is a hole.

---

## Split + index pattern

When file exceeds hard threshold:

1. **Identify split criteria** — by cohort / by status / by domain / by date / by concern
2. **Create sub-files** — one per split segment; each retains canonical content
3. **Convert original file to INDEX** — single doc lists all sub-files with brief description + cross-ref
4. **Update cross-references** — `rg` sweep across codebase for refs to original file; update to point at sub-file
5. **Add `splits_into:` frontmatter field** to original (index) file pointing at sub-files
6. **Add `parent_index:` frontmatter field** to each sub-file pointing back to index

---

## Index file shape (after split)

```markdown
---
type: <original type>
splits_into: [<sub-file paths>]
total_entries_at_split: N
split_date: YYYY-MM-DD
split_criteria: by-status | by-cohort | by-domain | by-concern | by-date
---

# <Original title> (INDEX)

This file was split at <date> because size exceeded <type> hard threshold (<lines> lines).
Content is now in sub-files; this doc serves as INDEX.

## Sub-files

| Sub-file | Coverage | Entry count |
|---|---|---|
| <path> | <brief: what this sub-file contains> | N |
| ... | ... | ... |

## Cross-reference shape

When referring to entries: cite the canonical ID (TECH_DEBT-NNN / Class N / etc.) — the index dispatches to the right sub-file automatically via `rg`.

Example:
- `rg "id: TECH_DEBT-115" DOCS/tech-debt/` — finds the right sub-file
- Sub-files can be discovered via `splits_into:` frontmatter on this index

## Migration history

- <YYYY-MM-DD>: Split from monolithic <original-path> (N entries; N lines)
- Future splits: when sub-file exceeds threshold, sub-split + amend this index
```

---

## Sub-file shape (after split)

```markdown
---
type: <original type sub-variant>
parent_index: <path to index>
covers: <what this sub-file owns; e.g., "open entries" or "registry-cohort entries">
established: YYYY-MM-DD
---

# <Sub-title>

<entries / content for this sub-file>
```

---

## Auto-flow at sprint close

`/metadata-audit` skill (queued at `.C` candidate ship) reports any file exceeding threshold. `/ship` skill amends suggest split before adding more entries to mega-files.

CI tool `check_doc_metadata.py` can flag file-size violations at commit time (sister to TECH_DEBT-114 test file split discipline enforcement).

---

## Examples (canonical)

### TECH_DEBT.md split candidate (queued at TECH_DEBT-116)

Current: 2013 lines, ~115 entries, monolithic. Exceeds 2000-line ledger threshold.

Proposed split criteria: by-status
- `DOCS/tech-debt/open.md` — status: open
- `DOCS/tech-debt/in-flight.md` — status: in-flight
- `DOCS/tech-debt/closed.md` — status: closed (archival)
- `DOCS/TECH_DEBT.md` — INDEX (`splits_into:` frontmatter; brief table of contents)

OR by-cohort (alternative):
- `DOCS/tech-debt/registry-discipline/` — entries tagged surface:registry
- `DOCS/tech-debt/wire-format/` — entries tagged surface:wire-format
- etc. — per-surface

Decision deferred to TECH_DEBT-116 ship: which split criteria works best for retrieval workflow.

### RECURRING_BUG_PATTERNS.md split candidate (queued at TECH_DEBT-117)

Current: 2198 lines, 32 classes, monolithic. Exceeds 2000-line ledger threshold.

Proposed split criteria: per-class file
- `DOCS/recurring-bug-patterns/class-01-name.md` through `class-32-name.md`
- `DOCS/RECURRING_BUG_PATTERNS.md` — INDEX with class-table + cross-refs

### /readiness SKILL.md split candidate (queued at TECH_DEBT-118)

Current: 1674 lines, 30+ checks. Exceeds 1500-line SKILL.md threshold.

Proposed split criteria: per-check sidecar files
- `claude-skills/readiness/SKILL.md` (~300 lines) — invocation + check index
- `claude-skills/readiness/checks/check-01.md` through `check-NN.md`

### EngineSharded.hpp subfolder split (FIRST CANONICAL subfolder pattern; v5.15.5.F.4d.1.B.6; 2026-05-27)

**Surface:** `CoreFrameworks/EngineSharded.hpp` — monolithic header at 3,202 total lines (well above 1500-line source-header threshold).

**Split criteria:** by concern — subfolder + INDEX-shim pattern (first canonical of the subfolder split shape; sister to per-status / per-class / per-cohort criteria already covered above).

**Pre-split:**
- `CoreFrameworks/EngineSharded.hpp` — 3,202 lines monolithic (boot + slow-path + async/drainer + run loop intermixed)

**Post-split:**
- `CoreFrameworks/EngineSharded.hpp` — 96 total / 5 code-lines (INDEX SHIM; `#include`s the 4 sub-files; preserves external API surface)
- `CoreFrameworks/EngineSharded/Boot.hpp` — 67 total / 12 code (signal handlers + globals + boot setup)
- `CoreFrameworks/EngineSharded/SlowPath.hpp` — 188 total / 78 code (per-node slow-path thread body)
- `CoreFrameworks/EngineSharded/Async.hpp` — 905 total / 460 code (drainer + fan-out + manual-close + post-fill hoisted lambdas)
- `CoreFrameworks/EngineSharded/Run.hpp` — 2,436 total / 1,406 code (engine run loop — under 1500-line threshold per code-LOC counting methodology above)

**Why subfolder (not flat split):** All 4 sub-files are tightly cohesive (boot → spawns threads that body lives in slow-path/async/run; subfolder GROUPING signals that to maintainers). Flat split (`EngineSharded_Boot.hpp` + `EngineSharded_SlowPath.hpp` + ...) loses the visual grouping cue.

**INDEX shim pattern:**
```cpp
// CoreFrameworks/EngineSharded.hpp — INDEX shim post-split
#pragma once
#include "EngineSharded/Boot.hpp"      // signal handlers + globals
#include "EngineSharded/SlowPath.hpp"  // per-core slow-path body
#include "EngineSharded/Async.hpp"     // drainer + fan-out + post-fill
#include "EngineSharded/Run.hpp"       // engine run loop
// External callers continue to #include "CoreFrameworks/EngineSharded.hpp"
// 30 external caller files: ZERO bypass-shim found
```

**Composes with sister disciplines:**
- `cpp17-inline-variable-for-header-shared-state.md` — 2 globals migrated `static` → `inline volatile sig_atomic_t` to preserve cross-TU shared storage post-split (`g_engine_sharded_shutdown` + `g_engine_sharded_gui_quit_ptr`)
- `single-source-of-truth-discipline.md` — Decision H merge of `drain_manual_closes` LIVE + NO-OP into single function (1 function + `#ifdef` body vs 2 functions with identical signatures)
- 5 lambdas hoisted from monolithic header into named functions: `fan_out` (25-arg signature; block-scope statics enumerated + passed explicitly per `feedback_enumerate_helper_signature_args_before_extract` M6); `drain_with_submit`; `drain_post_fill`; `drain_manual_closes` (single merged function per Decision H)

**Lessons:**
- **Code-LOC vs total-LOC threshold counting matters** — initial proposal split Run.hpp further (2,436 total → ~1,500 each sub-sub-file); actual code-LOC was 1,406 (already under threshold). Reverted. See "Threshold counting methodology" above.
- **Sub-files inherit `parent_index:` frontmatter convention** — `CoreFrameworks/EngineSharded.hpp` is the INDEX; sub-files point back via header comments (frontmatter not applicable to `.hpp` source headers, but consumer pointer-back convention preserved via header banner comments)
- **External cross-refs continue to point at INDEX** — 30 external caller `#include`s of `CoreFrameworks/EngineSharded.hpp` ALL still work (zero bypass shim found); sub-files only accessed via INDEX

---

## Trade-offs + when to apply

### Apply when:
- File crosses hard threshold
- Operator-flagged "this file is hard to navigate"
- `/metadata-audit` reports file-size violation
- Adding new entries would push over threshold (split BEFORE adding)

### Skip when:
- File is monolithic by design (single CANONICAL reference like `Limits.hpp` or `Version.hpp`)
- File is auto-generated (split happens at generation, not at file level)
- Split would create more cross-ref overhead than current monolithic state (rare; usually false economy)

### Cost:
- Initial split: 2-4h per mega-file (depending on cross-ref count + cohort criteria decision)
- Ongoing maintenance: minimal once split (sub-files stay smaller; index updates trivial)

### Win:
- Faster navigation
- Reduced load-time when only sub-section needed
- Drift reduction (sub-files easier to keep current than monoliths)
- Token budget improvement (less context burn per load)

---

## Lessons / gotchas

### Cross-ref breakage is the dominant risk

Splitting a file BREAKS all cross-refs that point at it. `rg <original-path>` sweep BEFORE split + sed-based update DURING split + verification AFTER are mandatory.

CI tool `check_doc_metadata.py` validates `sister_specs:` paths exist post-split.

### Index file becomes the canonical "where to look"

After split, ALL external refs should point at the INDEX. Sub-files reference each other via `parent_index:` frontmatter; external refs traverse via INDEX.

This avoids the problem where some external refs point at sub-file directly + others point at index = confusion.

### Don't split prematurely

Soft warning threshold is HINT, not requirement. Hard threshold is MANDATORY. Between soft + hard is judgment call: if file is still navigable, don't split.

### Sub-split when sub-files grow

If a sub-file exceeds threshold post-split, sub-split again. Index file's `splits_into:` frontmatter grows recursively. Sister to filesystem hierarchy growth.

### Choose split criteria carefully

Wrong criteria = split makes retrieval HARDER. Examples:
- Split by date in active ledger = forces users to know date of entry; bad
- Split by status in ledger = easy retrieval ("show open / show closed"); good
- Split by cohort (surface tag) = enables `rg` filtering; good

---

## Pattern lifecycle

- **Stage 1 (problem identification):** Caramel surfaced 2026-05-18 — "maybe split up things that become mega files to have an index and like 'if file X becomes greater than Y, split it up and add an index entry'"
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-18)
- **Stage 3 (first canonical):** TECH_DEBT-116/-117/-118 ledger splits 2026-05-18 (per-class / per-status criteria); EngineSharded.hpp subfolder split 2026-05-27 (subfolder + INDEX-shim subcriterion — first canonical of subfolder split shape per v5.15.5.F.4d.1.B.6)
- **Stage 4 (cohort migration):** all mega-files surfaced by `/metadata-audit` get split
- **Stage 5 (CLAUDE.md promotion):** when threshold rules are load-bearing (currently in this doc; could promote to CLAUDE.md if multiple file types reach threshold)
- **Stage 6 (cadence-locked):** CI tool catches file-size violations at commit time

---

## Cross-references

- Sister: `doc-frontmatter-convention.md` (frontmatter discipline; this spec extends with `splits_into:` / `parent_index:`)
- Sister: `ledger-entry-templates.md` (per-entry templates; this spec governs when ledgers themselves get split)
- Sister: `categorical-triggers-in-always-loaded-docs.md` (always-loaded discipline; mega-files violate "fits in context")
- Sister: CLAUDE.md `Test file size discipline` rule (sister rule for tests)
- TECH_DEBT-029 (source file length sister — header/non-test files)
- TECH_DEBT-114 (test file split queued — applies this discipline to tests/controller_test.cpp)
- TECH_DEBT-116 (TECH_DEBT.md split queued — applies this discipline)
- TECH_DEBT-117 (RECURRING_BUG_PATTERNS.md split queued)
- TECH_DEBT-118 (/readiness SKILL.md split queued)
- Memory: `feedback_file_size_split_discipline.md` (going-forward rule — queued)

---

**End of file-size-split-discipline v1.3 STAGE 3 FIRST CANONICAL.** Subfolder split pattern first canonical landed at v5.15.5.F.4d.1.B.6 ship close (EngineSharded.hpp 3,202 → 96 INDEX + 4 sub-files); cohort migration continues at queued `.B.7+` ships per file-size discipline maintenance umbrella.
