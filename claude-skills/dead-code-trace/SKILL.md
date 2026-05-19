---
name: dead-code-trace
description: Systematically audit the codebase for unreferenced functions, obsolete files, and legacy paths. Executes a multi-stage trace to PROVE code is truly dead before proposing removal. Outputs a structured removal plan, NOT direct edits.
type: skill
concern: anti-pattern-scan
audit_cadence: ad-hoc
tags: [audit-methodology, structural-fix]
surface: [registry, ci-tooling, test-infrastructure]
sister_skills: [/dust, /merge-scan, /anti-spaghetti]
loads_dynamically: []
---

# /dead-code-trace — Dead code identification and proof-of-obsolescence

## What this does

Scans the codebase (or a specific module) for "dead code"—functions, structures, or entire files that are no longer part of the live execution path or the test suite. 

Unlike a simple linter (like `/dust`), this skill **proves** the obsolescence of the code by tracing its call graph. It ensures that the code isn't dynamically invoked, part of a legacy feature that needs migration, or an experiment still being actively referenced.

**Does NOT delete files or modify code directly.** Output is a structured removal plan that the operator reviews and approves.

## Distinct from sister skills

| Skill | What it catches |
|---|---|
| `/dust` | Superficial code hygiene (bad formatting, rotted comments, empty blocks) |
| `/simplify` | Code review + auto-fix for overly complex live logic |
| **`/dead-code-trace`** | **Structural obsolescence and safe removal proofs** |

## When to use

- After a major architectural refactor (e.g., swapping parsing libraries, changing math models).
- During sprint "cooldown" phases to pay down technical debt.
- When you suspect an entire subsystem (like a legacy GUI panel or old order gate) is no longer wired to the main loop.

## Invocation

- `/dead-code-trace` — Full repository sweep (takes the longest).
- `/dead-code-trace <directory_or_file>` — Narrow audit of a specific subsystem (e.g., `/dead-code-trace DataStream/`).
- `/dead-code-trace <function_or_struct>` — Traces a single symbol to definitively prove if it can be purged.

## Pass structure

Spawn an Explore subagent. The subagent executes the following steps:

### 1. Identify Candidates
Run heuristic searches to find potential dead code:
- Unused `#include` statements.
- Functions defined but never called in `CoreFrameworks/`, `Strategies/`, etc.
- Template structs or enumerations that aren't instantiated.
- Files not present in `CMakeLists.txt`, `Makefile`, or `build.sh`.

### 2. The Verification Trace (The "Proof")
For every candidate identified, perform a rigorous, multi-vector search:
- **Global grep:** Search the exact symbol name across the *entire* workspace, including `tests/` and `experiments/`.
- **String literal check:** Verify the name isn't constructed via macros or passed as a string literal to dynamic loaders/loggers.
- **Header dependency check:** Ensure removing the code won't break compilation for downstream files that passively rely on its transitive includes.

### 3. Classification
Classify each verified dead code block into one of three tiers:
- **TIER 1 (Orphaned File):** The entire file is dead. (Highest ROI to remove).
- **TIER 2 (Dead Subsystem):** A cluster of functions/structs inside a live file that are no longer called.
- **TIER 3 (Vestigial Fields):** Unused struct members or function parameters (requires careful alignment checks before removal).

### 4. Emit the Removal Plan
Generate a markdown report formatted for the operator. 

Format:

```markdown
# /dead-code-trace report — <date>

## Plan summary
- Scope: <full | target>
- Total dead LOC identified: ~X lines

## TIER 1: Orphaned Files (Safe to delete)
1. `<File Path>` 
   - **Reason:** Completely unreferenced in build scripts and includes.
   - **Action:** `rm <File Path>`

## TIER 2: Dead Subsystems (Safe to excise)
1. `<File Path>:<Symbol>`
   - **Reason:** Deprecated since <context>. Zero inbound references.
   - **Proof:** Global search for `<Symbol>` yielded 0 hits outside its definition.
   - **Action:** Delete block from line X to Y.

## TIER 3: Vestigial Fields (Requires manual review)
1. `<File Path>:<Struct>:<Field>`
   - **Reason:** Never read or written.
   - **Warning:** Ensure struct alignment (e.g. `alignas(64)`) is maintained if removed.

---
## Suggested Git Command
```bash
git rm <orphan_file_1> <orphan_file_2>
```
```

## Anti-patterns to flag (DO NOT REMOVE)
- Do **not** flag code inside `tests/` as dead just because the main engine doesn't use it.
- Do **not** flag `experiments/` head-to-head comparison logic as dead unless explicitly asked.
- Do **not** remove struct padding variables (e.g., `uint8_t _pad[7]`) even if they are unreferenced; they are load-bearing for cache alignment.