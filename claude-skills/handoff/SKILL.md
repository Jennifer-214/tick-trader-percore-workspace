---
name: handoff
description: Generate a self-contained handoff prompt for opening a sub-ship in a fresh context window. Composes the 9-step pickup workflow (pre-flight verification → required reading → plan re-verification → pre-coding audit gate → DESIGN_SPECS pattern check → design philosophy reminders → TECH_DEBT items in surface area → filesystem conventions → sprint-close verification gate). Reads CLAUDE.local.md going-forward rules + DESIGN_SPECS/*.md catalog + auto-memory MEMORY.md + DOCS/TECH_DEBT.md dynamically so each prompt reflects current discipline. Output: plans/<sprint>/handoffs/<YYYY-MM-DD>-<ship>-handoff.md. Layer 1 orchestrator (compose-by-reference, NOT by-spawning).
---

# /handoff — Generate a sub-ship handoff prompt

## What this does

Composes a self-contained handoff prompt that a FRESH Claude Code session
can paste in to pick up a specific sub-ship. The prompt always reflects
CURRENT discipline because the skill reads the source docs (CLAUDE.local.md,
DESIGN_SPECS catalog, auto-memory, TECH_DEBT.md) at invocation time.

Forces consistency: every handoff includes the same 9-step skeleton +
the same design philosophy reminders + the same DESIGN_SPECS catalog
quick-discovery + the same operator collaboration norms.

This skill DOES write a file (the handoff doc); does NOT execute audits
or modify code. The handoff doc TELLS the future session to run audits.

## Invocation

- `/handoff <ship-tag>` — auto-resolve plan path via glob
  - `/handoff v5.14.10` → finds `plans/<active-sprint>/subplans/*v5.14.10*.md`
- `/handoff <ship-tag> <plan-path>` — explicit plan path
  - `/handoff v5.14.10 plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.10-bayesian-thompson-bandit.md`
- `/handoff` (no args) → ERROR. Sub-ship target must be specified.

## Execution model (Layer 1 orchestrator)

**ONE-WAY HIERARCHY. NO LAYER 3.**

```
LAYER 1: ORCHESTRATION
  - Main Claude session invokes this skill
  - This skill composes other skills BY REFERENCE in the generated prompt
    (the prompt tells the future session to run /readiness + /parity-check
    + etc., but THIS skill does not spawn subagents itself)

LAYER 2: EXECUTION (referenced by-text in output)
  - The generated handoff prompt instructs the future session to run
    /readiness, /parity-check, /trace-deps, /merge-scan, /dod-audit
    as Layer 2 skills (or via Explore subagents from Layer 1)
```

**DO NOT** spawn subagents from inside /handoff. If you are reading this
spec inside an Explore subagent: you are NOT the handoff generator —
return an error. /handoff is only invoked from main session.

## Pass structure

### Stage 1 — Resolve sub-ship target + active sprint

1. Parse `<ship-tag>` (e.g., `v5.14.10`, `v5.14.10.A`, `v5.14.11`).
2. Detect active sprint from current `Version.hpp`:
   - Read `/home/caramel/code/FoxML_Trader_v2/Version.hpp`
   - Extract `ENGINE_VERSION_STRING` (e.g., "5.14.9")
   - Active sprint name = `v<major>.<minor>-<sprint-name>` from glob
     `plans/v<major>.<minor>-*/` (only one matching dir; fail if multiple)
3. Resolve plan path:
   - If passed as arg, use it
   - Else glob `plans/<active-sprint-dir>/subplans/*<ship-tag>*.md`
   - If 0 matches: ERROR. Ship-tag's plan file doesn't exist.
   - If >1 matches: ERROR. Disambiguate via explicit plan path.
4. Detect git state:
   - Current branch (should be the sprint branch)
   - Latest tag (rollback anchor for the new ship)
   - Clean working tree status

### Stage 2 — Read source docs (DYNAMIC catalog ingestion)

Read these dynamically (NOT hardcoded). The skill's value is freshness:
each invocation pulls current state.

| Source | Read for |
|---|---|
| `/home/caramel/code/FoxML_Trader_v2/CLAUDE.local.md` | Going-forward rules; design philosophy entries; required-reading map; auto-write contracts |
| `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/MEMORY.md` | Auto-memory index; feedback / user / project / reference entries to surface |
| `tick-trader-percore-workspace/DESIGN_SPECS/README.md` | Pattern catalog + "I need to..." quick-discovery |
| `tick-trader-percore-workspace/DOCS/SKILLS_HIERARCHY.md` | Layer 1 / Layer 2 conventions; compose-by-reference rule |
| `tick-trader-percore-workspace/DOCS/TECH_DEBT.md` | Open entries; filter to ones in ship's surface area |
| `tick-trader-percore-workspace/DOCS/PARITY_ISSUES.md` | Open parity findings (cross-ref to ship surface) |
| `plans/<sprint-dir>/MASTER.md` | Sprint context; ship's position in sub-tag sequence |
| `<plan-path>` (resolved) | Ship's stated scope; stale-claim audit target |
| `plans/<sprint-dir>/postmortems/` | Most-recent sub-ship postmortem (lessons that may apply) |

### Stage 3 — Scan plan for DESIGN_SPECS pattern symptoms

Read the plan body + extract pattern symptoms. For each pattern in
`DESIGN_SPECS/README.md` catalog, check if the plan mentions
indicator phrases (heuristic, not exhaustive):

| Plan indicator | Likely pattern |
|---|---|
| "new cfg field", "boolean toggle", "cfg-flag" | `cfg-flag-eligibility-criteria.md` + `heterogeneous-registry-pattern.md` + `registry-tuple-as-single-source-of-truth.md` |
| "named compute modes", "dispatch table", "enum + switch" | `curve-registry-pattern.md` |
| "3+ booleans", "bit-pack", "state flags" | `bitmap-flag-api.md` + variant docs |
| "per-core override" | `per-bit-per-core-override-pattern.md` |
| "stamp body", "wire format", "HMAC" | `wire-format-byte-preservation-discipline.md` + `x-macro-registry-with-presence-dispatch.md` |
| "production callers", "auto-populate", "construction sites" | `autopopulate-pattern-for-production-caller-class.md` + `autopopulate-from-arity-macro-family.md` |
| "X-macro registry", "FOREACH_*" | `x-macro-registry-with-presence-dispatch.md` |
| "recurring bug class", "drift", "Class 18 mirror" | `structural-fix-preferred-decision-framework.md` |
| "per-core <N> boolean", "per-core flag" | `partner-core-bitmap-pattern.md` |
| "aggregation summary", "any-of check" | `transient-aggregation-bitmap-pattern.md` |
| "audit + ship", "before coding" | `audit-driven-pre-coding-gate.md` |
| "interleaved registry", "PRE/POST emit" | `pre-post-cfg-registry-split-for-emit-order-preservation.md` |
| "slow-path gate", "predicate cache" | `slow-path-gate-registry-pattern.md` |

Record matched patterns + cite the relevant DESIGN_SPECS doc by filename.
Future session reads these as recommended (not mandatory) starting points.

### Stage 4 — Scan TECH_DEBT for surface overlap

For each OPEN TECH_DEBT entry:
1. Parse `Surface:` line
2. Check if surface mentions any path/file/registry the ship will touch
3. If overlap: include the entry in the handoff with the surface match
   highlighted

This surfaces existing-debt that the ship might naturally absorb or
explicitly defer.

### Stage 5 — Compose handoff prompt

Assemble the prompt with this structure:

```markdown
# <ship-tag> handoff prompt — <ship-title>

**Created:** <YYYY-MM-DD>
**Target ship:** <ship-tag> — <description from plan or MASTER>
**Branch:** <current branch>
**Pre-tag rollback anchor:** <latest tag>
**Plan file:** <plan-path>
**Sprint MASTER:** plans/<sprint-dir>/MASTER.md
**Predecessor postmortem:** <most-recent postmortem in plans/<sprint-dir>/postmortems/>

---

## Paste this prompt into a fresh Claude Code session to start <ship-tag>

```
I'm picking up <ship-tag> (<ship-title>) for the <sprint-name> sprint.
This is a fresh context window; do NOT trust any prior-session memory
— verify everything against current code.

## Step 0 — orient + verify state (BEFORE planning anything)

1. Run in parallel:
   - `cat /home/caramel/code/FoxML_Trader_v2/Version.hpp` — confirm "<current-version>"
   - `cd /home/caramel/code/FoxML_Trader_v2 && git log --oneline -5` — confirm latest commit is <latest-commit-or-tag>
   - `cd /home/caramel/code/FoxML_Trader_v2 && git tag --sort=-creatordate | head -5` — confirm <latest-tag> exists
   - `cd /home/caramel/code/FoxML_Trader_v2 && git status` — confirm clean tree

2. Read these in parallel (load context):
   - `CLAUDE.md` (engine repo project instructions)
   - `CLAUDE.local.md` (private overlay; design philosophy + going-forward rules)
   - `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/MEMORY.md`
   - `plans/<sprint-dir>/MASTER.md` (sprint master plan)
   - `<plan-path>` (THE plan for this ship)
   - `plans/<sprint-dir>/postmortems/<latest>.md` (most-recent postmortem)

3. Read BEFORE WRITING CODE (per CLAUDE.local.md required reading):
   - `DOCS/STRATEGY_AND_CODING_RULES.md` (11 strict invariants)
   - `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` (7 latency-path rules)
   - `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` (Gemini sweep; touch domain-relevant parts)

## Step 1 — re-verify plan against current code (HEAD)

The plan was drafted <plan-draft-date>. Codebase has moved through <recent-ships-since>. Plan's "Pre-existing work audit" REUSE claims and file:line refs may be stale.

Run `/readiness <plan-path>` and address every GAP / stale-reference finding. Common stale claims to verify:
- File:line refs (do the cited functions/files exist? renamed?)
- Struct shapes (any fields added/renamed since plan date?)
- Cfg-flag overlap (does the plan add a cfg field already migrated to FOREACH_<DOMAIN>_CFG_FLAG?)
- Function signatures (any refactored since plan date?)
- Dispatch sites (still at the line ref claimed?)

## Step 2 — pre-coding audit gate (multi-skill parallel)

Per `DESIGN_SPECS/audit-driven-pre-coding-gate.md`, fire the gate when ship has 2+ of: closes recurring bug class structurally, touches wire format, adds 5+ new fields/functions/cfg entries, refactors fn used at 5+ sites, picks up work from previous (possibly compacted) session.

<conditionally-included if ship qualifies>
Spawn these audits IN PARALLEL via Agent tool with Explore subagents:
1. `/parity-check` — focus: train↔serve identity; stamp body if applicable; production-caller field-population
2. `/trace-deps` — focus: plan file:line claims; function signatures match planned; dependency-chain
3. `/readiness` (full 28-check pass) — cold-pickup completeness; new cfg field eligibility; X-macro variant selection
4. `/merge-scan` — focus: reuse opportunities; mirror-incomplete patterns
5. `/dod-audit` — focus: DESIGN_SPECS pattern application; missed bit-packing / X-macro / cache-alignment candidates

After all reports return, synthesize convergent findings to `plans/plan_checks/<date>-<ship-tag>-fresh-audits-synthesis.md`. THEN consult Caramel before coding. Do NOT auto-proceed even if findings look addressable (per CLAUDE.local.md feedback_consult_on_audit_findings memory).
</conditionally-included>

## Step 3 — design check against pattern library

Required reading (DESIGN_SPECS catalog):
- `DESIGN_SPECS/README.md` (full 16-pattern catalog + "I need to..." quick discovery)
<for each pattern matched in Stage 3 above:>
- `DESIGN_SPECS/<pattern>.md` — <reason it matched the plan>
</for>

Don't write code until the matched-pattern docs are read + integration plan articulated.

## Step 4 — design philosophy reminders (load-bearing rules from CLAUDE.local.md + memory)

<inject going-forward rules + relevant feedback entries dynamically>
- **Defer is last-ditch, never effort-avoidance.** Implement properly the first time. Smaller-scope recommendations have been wrong 3/3 times in v5.14 sprint vs Caramel's "do it right now" instinct.
- **Structural fix > direct patch for recurring bug classes.** If the ship has any "same pattern at multiple sites" shape, use X-macro registry / helper extraction with compile-time enforcement.
- **No MVP for plumbing/refactor work.** MVP framing is reserved for genuinely-new features with unknown unknowns. Pattern-application work ships the full documented design.
- **Boundary-stable refactors preferred over wide cascades.** Keep public boundary types unchanged + isolate behavior inside.
- **Hot path UNTOUCHED.** Hot path target ≤500ns p99. Add work to slow path only.
- **Branchless mask compute > switch on enum on slow path** (per CLAUDE.md item 18). Prefer template-bool dispatch or fn-pointer table over switch.
- **Reuse-audit before adding new code** (per CLAUDE.md item 16). Scan for existing functions / shared state / conversion paths.
- **Latency-additions get tracked** (per CLAUDE.md item 17). Log new slow-path / drainer / parser cost in `DOCS/HOT_PATH_CHANGELOG.md` with cost estimate + branchless analysis.
- **Replay determinism is sacred.** Any RNG must use seeded mt19937_64 or equivalent with saved state. Never `std::random_device` in production paths.
- **Bump Version.hpp on every ship.** Each `vX.Y.Z` tag must include a Version.hpp bump in the same commit.
- **Don't use AskUserQuestion modal boxes.** Present options inline as text; Caramel wants full conversation scrollable.
- **Evaluate options on robustness + latency + design philosophy, NOT time.** Time is essentially never the deciding factor.
- **After pre-coding audits, ALWAYS consult before coding.** Present findings + list potential fixes + iterate with Caramel. Do NOT auto-proceed.
- **Address Caramel as Caramel / she / her** in conversation. Persisted docs can keep "operator" for general-collaborator audiences.

## Step 5 — TECH_DEBT items in surface area

<for each TECH_DEBT entry that overlaps ship's surface:>
- **TECH_DEBT-<N>** (<status>): <one-line title>
  - Surface: <surface line>
  - Trigger: <trigger>
  - Cost estimate: <estimate>
  - Decide: absorb into ship OR refresh entry OR explicit defer
</for>

If any overlapping entry exists, run `/readiness` Check 25 (TECH_DEBT scan) explicitly.

## Step 6 — operator collaboration norms

- Address Caramel as Caramel / she / her. Not "operator" in conversation.
- Don't use AskUserQuestion modal boxes. Present options inline as text.
- Evaluate options on robustness + latency + design philosophy, NOT time.
- When pre-coding checks complete, present findings + fixes + iterate BEFORE coding.
- Suggest mid-sprint audit when downstream sub-ships impact a new surface (per CLAUDE.local.md going-forward rule). Wait for greenlight.
- Auto-write TECH_DEBT entries for any deferred items (auto-write contract).
- Auto-write PARITY_ISSUES entries for any new parity findings.

## Step 7 — filesystem conventions

- Workspace path: `/home/caramel/code/tick-trader-percore-workspace`
- Engine repo: `/home/caramel/code/FoxML_Trader_v2`
- Plans live in workspace; symlinked from engine `plans/` → workspace `plans/`.
- Sprint plans: `workspace/plans/<sprint-dir>/{MASTER.md, subplans/, plan_checks/, postmortems/, handoffs/}`
- DESIGN_SPECS catalog: `workspace/DESIGN_SPECS/` (19 patterns + README; promoted from 16 in v5.14.10 with per-snapshot-cluster-layout-pattern + calibration-log-column-registry + postloadsetup-registry-pattern)
- Skill outputs go to `plans/plan_checks/<skill>-<YYYY-MM-DD>-<scope>.md` (neutral); batches into sprint dir at close.
- TECH_DEBT auto-write: `DOCS/TECH_DEBT.md` (symlinked from workspace)
- PARITY_ISSUES auto-write: `DOCS/PARITY_ISSUES.md` (symlinked from workspace)
- HOT_PATH_CHANGELOG: `DOCS/HOT_PATH_CHANGELOG.md` (symlinked from workspace)
- **DOCS/ symlinks editing convention** (post-v5.11.43 migration; surfaced as Surprise 7 in v5.14.10 postmortem): many `DOCS/*.md` files in the engine repo are PER-FILE SYMLINKS to workspace. The `Edit` tool REFUSES to write through symlinks. ALWAYS check `readlink -f path` before editing a `DOCS/*.md` file; if it resolves to a workspace path, edit via the workspace path directly. Symlink-resolved files include: HOT_PATH_CHANGELOG, PARITY_ISSUES, TECH_DEBT, plus most CLAUDE_*.md / RECURRING_BUG_PATTERNS / EASY_ADDITIONS_INVARIANTS / sister-architectural docs. Engine-tracked exceptions (NOT symlinked): QUICKSTART, OPERATOR_DEPLOYMENT, CONFIGURATION, ML_USAGE, ML_TRAINING, CONTRIBUTING, LATENCY_PROFILING.

## Step 8 — sprint-close verification gate

Before declaring <ship-tag> shipped:
- Tests pass (currently <test-count>; expect ~<estimated-new-tests> new)
- `/parity-check` GREEN at <ship-tag>
- `/merge-scan` GREEN (no missed reuse)
- `/latency-track` entry for any slow-path / drainer addition
- `/bug-check` CLEAN (no new recurring-bug-class instances)
- Replay determinism test passes (if RNG involved)
- Cfg.example doc updated for any new cfg field
- Persistence round-trip verified (if state persisted)
- Version.hpp bumped in the same commit as the ship tag

## Closing reminder

<ship-specific value statement — what's the value of this ship?>

If you find yourself writing complex plumbing, stop — check `DESIGN_SPECS/README.md` "I need to..." section. There's almost certainly a pattern that applies.

Good luck. Caramel will iterate with you on findings before coding.
```

---

## Notes for future-Claude reading this handoff doc

- Prompt above is self-contained — paste as FIRST message in a fresh `claude code` session.
- Includes 9 steps + design philosophy reminders + filesystem conventions.
- Follow them in order; don't skip Step 1 (re-verification against current code).

---

## Quick links

- Sprint MASTER: <link>
- This ship's plan: <link>
- Latest postmortem: <link>
- DESIGN_SPECS catalog: <link>
- Latency rules: <link>
- Coding invariants: <link>
```

### Stage 6 — Write to disk

Save to `plans/<sprint-dir>/handoffs/<YYYY-MM-DD>-<ship-tag>-handoff.md`.

`mkdir -p` the dir if it doesn't exist (sprint-dir/handoffs/ may not exist if no prior handoffs in that sprint).

### Stage 7 — Confirm to user

Print:
- Path of generated handoff
- Top-level structure summary (which patterns matched, which TECH_DEBT items overlapping, audit-gate qualified?)
- Reminder that the handoff is GENERATED, not iterated — operator can edit if they want to customize

## What this skill is NOT

- **Not /readiness.** /readiness AUDITS a plan against current code. /handoff GENERATES a handoff prompt that INCLUDES /readiness as one step. Different scope.
- **Not /ship.** /ship is post-coding close ritual (commit + tag + push). /handoff is PRE-coding pickup ritual.
- **Not a runtime audit.** /handoff doesn't run audits; it instructs the future session to run them.
- **Not a plan generator.** /handoff requires an EXISTING plan file. To author a plan, use a different workflow.
- **Not for trivial bug fixes.** /handoff overhead unjustified for single-file changes. Skip when ship is < 1 day of work.

## When to invoke

- After a sprint sub-ship lands + before the next sub-ship opens (if next sub-ship will run in a fresh context)
- After a sprint umbrella ships + before opening the next sprint's first sub-ship
- After plan amendment + before the amended sub-ship picks up coding
- After compaction event in a long session (warm context becomes cold)

Don't invoke for:
- Immediate same-session continuation (no fresh context needed)
- Single-file bug fixes
- Doc-only ships

## Catalog cross-references

The skill consumes (READS) these dynamically:
- `tick-trader-percore-workspace/DESIGN_SPECS/*.md` — pattern catalog
- `tick-trader-percore-workspace/DOCS/SKILLS_HIERARCHY.md` — Layer model
- `tick-trader-percore-workspace/DOCS/TECH_DEBT.md` — deferral ledger
- `tick-trader-percore-workspace/DOCS/PARITY_ISSUES.md` — known parity findings
- `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/MEMORY.md` — auto-memory index
- `/home/caramel/code/FoxML_Trader_v2/CLAUDE.local.md` — going-forward rules
- `/home/caramel/code/FoxML_Trader_v2/CLAUDE.md` — public project instructions
- `/home/caramel/code/FoxML_Trader_v2/Version.hpp` — current version (for sprint detection)
- Plan file at the resolved path

The skill INSTRUCTS the generated prompt to invoke these as Layer 2:
- `/readiness` — plan re-verification + cold-pickup check (Step 1 of generated prompt)
- `/parity-check` + `/trace-deps` + `/readiness` + `/merge-scan` + `/dod-audit` — pre-coding audit gate (Step 2)

## Going-forward rule for new sprints

When opening a new sprint:
1. Create the sprint dir (`plans/<v.major.minor>-<sprint-name>/`)
2. Subdirs: `subplans/`, `plan_checks/`, `postmortems/`, `handoffs/`
3. MASTER.md at sprint-dir root
4. First sub-ship gets a handoff via this skill (`/handoff <first-sub-tag>`) so the discipline is locked in from sprint start

## Example invocation

```
$ /handoff v5.14.10
[skill reads Version.hpp → 5.14.9 → active sprint dir = v5.14-foxml-port-and-maker]
[skill globs plans/v5.14-foxml-port-and-maker/subplans/*v5.14.10*.md → 1 match]
[skill reads MASTER, plan, CLAUDE.local.md, MEMORY.md, DESIGN_SPECS/README.md, TECH_DEBT.md]
[skill scans plan for DESIGN_SPECS pattern symptoms — matches: curve-registry, bitmap-flag-api, x-macro-registry, autopopulate (because Thompson dispatch + new bandit state + persistence)]
[skill scans TECH_DEBT for surface overlap — matches TECH_DEBT-008 (bandit telemetry deferral)]
[skill writes plans/v5.14-foxml-port-and-maker/handoffs/2026-05-10-v5.14.10-handoff.md]
[skill prints summary + path]
```

## Pattern provenance

This skill formalizes the ad-hoc handoff prompt convention used through
v5.14.x sprint. First applied retroactively for v5.14.10 (Thompson
sampling bandit) post v5.14.9 close. Pattern captured because every
sprint sub-ship pickup was hitting the same checklist; ad-hoc handoffs
drifted in completeness vs the canonical shape.

Documented in:
- `tick-trader-percore-workspace/DOCS/SKILLS_HIERARCHY.md` (Layer 1 entry)
- This file
- First example: `plans/v5.14-foxml-port-and-maker/handoffs/2026-05-10-v5.14.10-thompson-bandit-handoff.md`
