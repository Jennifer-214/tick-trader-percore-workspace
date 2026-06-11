---
type: doc-discipline
stage: 2-draft
version: 1.0
established: 2026-06-10
tags: [doc-discipline, framework-discipline, context-aware-loading]
surface: [doc-pipeline]
sister_specs: [categorical-triggers-in-always-loaded-docs.md, file-size-split-discipline.md]
---

# Module-scoped CLAUDE.md pattern (context-aware loading)

**Established:** 2026-06-10 (TECH_DEBT-163 — the always-loaded byte-budget close). Validated feasible via claude-code-guide: nested `CLAUDE.md` files load **on-demand** when a file in that subdir is read/edited, and do **NOT** count toward the session-start budget.

## The mechanic (LAYERED, not COPIED)

Editing a file in `CoreFrameworks/` loads root `CLAUDE.md` (the universal core — always present) **PLUS** `CoreFrameworks/CLAUDE.md`. They **CONCATENATE**, not override. So at any moment I have:

```
  root CLAUDE.md (universal core, always-loaded)
+ <module>/CLAUDE.md (the surface slice, on-demand)
+ work-mode disciplines (pulled by the active skill / on-demand index)
= every rule reachable, through the right layer
```

**The one hard rule: NEVER copy a universal rule into a nested file.** Same rule in N files = the Class-18 mirror-drift anti-pattern this codebase closes everywhere else. One source per rule; nested files hold ONLY the module slice + a scoped index into the shared apparatus + a pointer back to the core.

## The three buckets (where each rule lives)

| Bucket | Lives in | Loads | Examples |
|---|---|---|---|
| **① Universal CORE** | root `CLAUDE.md` (+ MEMORY.md core) | always | prime directive · priority order · H1–H21 (title+1-line) · doc-layer-separation · the reference/skill/how-to index spine · collaboration + correctness must-haves |
| **② File-surface** | `<module>/CLAUDE.md` (nested) | on edit in `<module>/` | hot-path/OMS/drainer rules · Money/FPN_Binary discipline · ML determinism · strategy registry · GUI thread-isolation |
| **③ Work-mode** | on-demand index (skills `loads_dynamically`) | when a work-mode skill fires + categorical trigger | planning · audit-gate · codification · deletion-ordering · session-decision-log disciplines |

② is file-surface (nested CLAUDE.md triggers on the path). ③ is work-MODE (not tied to a code path) → it rides the slim core + the on-demand index the planning/audit skills already pull, NOT nested CLAUDE.md.

## The nested-module CLAUDE.md TEMPLATE (every ② file follows this)

```markdown
# Working in <Module>/ — surface-scoped orientation

> On-demand: loads when you read/edit a file in `<Module>/`. CONCATENATES with the always-loaded
> root CLAUDE.md (universal core) — this is the `<Module>` SLICE, not a replacement. Do NOT copy
> universal rules here (already loaded; duplicating = Class-18 mirror drift) — link them.

## Surface rules (load-bearing here)
- <the module-specific hard-rules / invariants that bite on this surface>

## Hard invariants most active here
- <H-N: one-line why it matters here>   (full table: root CLAUDE.md / DESIGN_PHILOSOPHY § 2)

## Tools for this surface (slice of DOCS/TOOLS.md)
- `<tool>` — <what it guards here>  (run: `<invocation>`)

## Skills for this surface
- `/<skill>` — <when to fire it here>

## Patterns + anti-patterns here
- DESIGN_SPECS: `<spec>.md` — <relevance>
- RECURRING_BUG_PATTERNS: Class <N> — <the recurring trap on this surface>

## Reach for more
- Universal rules/invariants: root `CLAUDE.md` (already loaded)
- Planning / audit / codification disciplines: `<on-demand work-mode index>` (work-mode skills auto-load)
```

## Anti-silent-absence guarantee (what makes deferral safe)

The risk of context-aware loading is a rule that ISN'T loaded for the surface where it applies, missed silently. Three structural defenses make deferral **strictly safer than the status quo** (which silently TRUNCATES past the byte cap, with zero breadcrumb — observed: MEMORY.md "only part was loaded"):

1. **Every moved block leaves a one-line POINTER in the always-loaded root.** Nothing is silently absent — it is *visibly deferred* ("Architecture → `CoreFrameworks/CLAUDE.md`, loads on-demand"). The root stays a COMPLETE map of what moved + where. (Byte-cap truncation drops content with NO pointer — that is the genuinely invisible failure this REPLACES.)
2. **CORE stays conservative.** Anything correctness-critical needed regardless of surface — H1–H21, capital/money rules, determinism rules, collaboration rules — stays in the always-loaded CORE. Budget is bought back from clear surface-DETAIL, never from correctness-critical universals. When in doubt whether a rule is universal or surface-specific → **keep it universal.**
3. **The consistency guard enforces pointer-completeness** (`check_module_claude_md.py`): a nested file with no root pointer (an invisible move) = red build; a root pointer that resolves to nothing = red build.

**Belt-and-suspenders for the "working a surface WITHOUT touching its files" gap** (planning / Q&A — the file-read trigger never fires): the optional `UserPromptSubmit` hook reads the PROMPT's intent (keywords) and surfaces the matching pointer even when no file is opened. Build it when the surface-trigger coverage proves insufficient.

## Consistency guarantee (CI-enforceable)

Because every ② file follows the template, a guard (`tools/check_module_claude_md.py`, sister to `check_tools_inventory.py`) can verify each nested `CLAUDE.md`: has the required sections · every cited `tool`/`skill`/`spec` resolves (no dangling refs) · holds NO universal rule (the no-copy discipline) · sits in a real module dir. Consistency becomes a red-build, not a hope.

## Sister patterns
- `categorical-triggers-in-always-loaded-docs.md` — the ③ work-mode trigger discipline.
- `file-size-split-discipline.md` — the always-loaded byte-cap this dissolves.
- `DOCS/TOOLS.md` — the tool inventory the ② "Tools for this surface" sections slice from.
