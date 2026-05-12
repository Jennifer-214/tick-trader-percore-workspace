---
name: Prefer ripgrep over grep when searching
description: Caramel installed ripgrep (rg) on the dev machine 2026-05-09; use it instead of grep for any code search
type: feedback
originSessionId: 43a2b763-783f-4a6e-9b54-c3654977b44c
---
Use `rg` (ripgrep) instead of `grep` for searching the codebase or
files of any kind. Caramel installed ripgrep on 2026-05-09
specifically so I'd have a faster + better tool for code search.

**Why:** rg is significantly faster (parallel + .gitignore-aware by
default), produces cleaner output (file:line:content), respects
.gitignore so it doesn't search build/ vendor/ etc. without flags,
and is a Rust binary tuned for code-scale searches.

**How to apply:**
- Default to `rg` over `grep` in Bash tool calls
- Common patterns:
  - `rg "pattern" path/`               (recursive by default)
  - `rg -l "pattern" path/`            (just file names)
  - `rg -n "pattern" file.hpp`         (with line numbers — `-n` is default for terminal output)
  - `rg --type cpp "pattern"`          (filter by file type)
  - `rg -g "*.hpp" "pattern"`          (custom glob)
  - `rg -A 3 -B 1 "pattern"`           (3 lines after, 1 before)
  - `rg -i "pattern"`                  (case-insensitive)
  - `rg -F "literal.string"`           (fixed string, no regex)
  - `rg -w "word"`                     (word boundaries)
  - `rg --hidden "pattern"`            (include hidden files)
- Skill specs that say "grep" still work — internally I should use rg
- The Grep tool in Claude Code is a separate primitive (uses ripgrep
  internally already); use it for non-Bash search calls
- If rg is missing on a system: fall back to grep without comment
- Don't cite "grep" in user-facing text — say "search the codebase"
  or "rg" if specific tool name matters

Saved 2026-05-09.
