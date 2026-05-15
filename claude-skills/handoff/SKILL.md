---
name: handoff
description: Generate a self-contained handoff prompt for opening a sub-ship in a fresh context window. Composes the 9-step pickup workflow (pre-flight verification → required reading → plan re-verification → pre-coding audit gate → DESIGN_SPECS pattern check → design philosophy reminders → TECH_DEBT items in surface area → filesystem conventions → sprint-close verification gate). Reads CLAUDE.local.md going-forward rules + DESIGN_SPECS/*.md catalog + auto-memory MEMORY.md + DOCS/TECH_DEBT.md dynamically so each prompt reflects current discipline. Output: /home/caramel/code/tick-trader-percore-workspace/plans/<sprint>/handoffs/<YYYY-MM-DD>-<ship>-handoff.md (WORKSPACE path explicitly, never engine-side symlink). Layer 1 orchestrator (compose-by-reference, NOT by-spawning).
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

### Stage 1.5 — Capture in-flight task state (TaskList serialization)

**NEW (set 2026-05-15 per operator request after `.F.4c.3` Step 2 partial handoff — without explicit TaskList capture, fresh-session pickup loses track of the multi-step plan progress; in-flight tasks must be recreated from memory which drifts).**

**Additional dynamic-load contracts (set 2026-05-15 at WIP2d-1.B.0c):**

When composing the handoff body, scan the in-flight plan + recent commits for surface indicators and pre-load matching DESIGN_SPECS bodies + skill references:

| Plan / commit surface contains | Pre-load reference |
|---|---|
| OMS / drainer / fee_rate / commission / slippage / P&L / kill switch | `decision-time-data-binding-pattern.md` + RECURRING_BUG_PATTERNS Class 27 + `/accounting-audit` skill reference |
| New registry introduction OR cache-on-subsystem-state | `decision-time-data-binding-pattern.md` § Framework-selection criteria + `/registry-fit-audit` skill reference + DESIGN_PHILOSOPHY § 1.5 Framework-selection criteria sub-section |
| `cfg.cores[c]` reads or per-core registry work | `cfg-scope-discipline.md` + RECURRING_BUG_PATTERNS Class 25 + Class 26 + Class 27 |
| ML cfg fields (ridge_*, thompson_*, confidence_*, bandit_*) | `cfg-scope-discipline.md` + decision-time-data-binding-pattern.md (ConfidenceScorer / ThompsonBandit state are Class 27 target subsystems) + `/accounting-audit` |
| ImGui widget / Settings panel | (no new dynamic load at .F.4c.3; existing widget-ID discipline applies) |

These cross-references go into the generated handoff Step 3 (DESIGN_SPECS pattern check) + Step 4 (design philosophy reminders) sections, so the fresh-session pickup has the relevant principle context loaded before code reads start.

Before composing the handoff body, invoke `TaskList` and serialize the result into a structured table that the generated handoff embeds verbatim. Each task entry captures:

| Field | Source |
|---|---|
| ID | TaskList task ID (e.g., `#4`) |
| Status | `completed` / `in_progress` / `pending` |
| Subject | task subject line |
| Description (optional) | task description if non-empty and load-bearing |

The captured table goes into the generated handoff doc body under a dedicated section: **"## TaskList state at handoff write (preserve verbatim for fresh-session pickup)"** between the "What remains" section and the "Paste this prompt" code block.

The generated cold-pickup prompt MUST include an instruction in its Step 0 (or wherever appropriate):

> **Recreate the TaskList** from this handoff's TaskList table — use TaskCreate for each entry to preserve the multi-step plan tracking. Mark <completed-ids> completed, <in-progress-ids> in_progress, <pending-ids> pending.

This eliminates the "TaskList evaporates between sessions" failure mode. Fresh-session-me knows immediately which sub-steps remain, which are in progress (typically only 1), and which are done.

If TaskList is empty at handoff write time, the generated handoff says "No active task list — fresh-session pickup may create one based on remaining sub-commits enumerated below."

### Stage 2 — Read source docs (DYNAMIC catalog ingestion)

Read these dynamically (NOT hardcoded). The skill's value is freshness:
each invocation pulls current state.

| Source | Read for |
|---|---|
| `/home/caramel/code/FoxML_Trader_v2/CLAUDE.local.md` | Going-forward rules INDEX (since 2026-05-14 condense: rule one-liners + DESIGN_SPECS pointers + auto-write contracts + required-reading triggers). Follow pointers into DESIGN_SPECS for rule deep-dives. |
| `/home/caramel/code/FoxML_Trader_v2/CLAUDE.md` | Codified design philosophy items 1-30 (always loaded; canonical pattern doctrine). |
| `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/MEMORY.md` | Auto-memory index; feedback / user / project / reference entries to surface |
| `tick-trader-percore-workspace/DESIGN_SPECS/README.md` | Pattern catalog + "I need to..." quick-discovery |
| `tick-trader-percore-workspace/DOCS/SKILLS_HIERARCHY.md` | Layer 1 / Layer 2 conventions; compose-by-reference rule |
| `tick-trader-percore-workspace/DOCS/TECH_DEBT.md` | Open entries; filter to ones in ship's surface area |
| `tick-trader-percore-workspace/DOCS/PARITY_ISSUES.md` | Open parity findings (cross-ref to ship surface) |
| `tick-trader-percore-workspace/DOCS/LANDMINES.md` | Operational landmines (e.g., XGBoost+libgomp pthread races); read before any segfault/race/parallelism debugging |
| `tick-trader-percore-workspace/DOCS/DESIGN_PHILOSOPHY.md` | **NEW (post-2026-05-14 refactor).** Thematic narrative + 4-tier discipline (HARD / STRONG / SOFT / PROCESS) + cross-reference index. Match plan keywords to family sections (§ 3 Hard Invariants / § 4 Latency / § 5 Determinism / § 6 Concurrency / § 7 Structural-fix / § 8 Failure observability / § 9 Architectural primitives / § 10 Operator UX / § 11 Process discipline) + cite specific § N rows in generated prompt's Step 4. |
| `plans/<sprint-dir>/MASTER.md` | Sprint context; ship's position in sub-tag sequence |
| `<plan-path>` (resolved) | Ship's stated scope; stale-claim audit target |
| `plans/<sprint-dir>/postmortems/` | Most-recent sub-ship postmortem (lessons that may apply) |
| `CLAUDE.local.md` Current Sprint State Tracker section | **NEW (post-2026-05-14).** Most-recent ship + next-ship + sprint-wide invariants in force + open architectural decisions. Embed as snapshot in generated prompt for cold-pickup-time drift detection. |

**CLAUDE.local.md as index (post-2026-05-14 condense):** the file is
~190 lines of pointer-based index, NOT a 800-line philosophy dump.
For each going-forward rule named in CLAUDE.local.md that overlaps
the ship's surface, follow its DESIGN_SPECS pointer + load that body
into context. This ensures the generated prompt's Step 3 "design check
against pattern library" references concrete pattern bodies the
future session needs, not just names.

### Stage 2.5 — Verify-on-write (anti-staleness fire)

**NEW (post-2026-05-14; addresses observed drift between handoff prompt and reality at cold-pickup time per `feedback_compaction_degrades_treat_handoffs_as_hints`).**

Before composing the handoff prompt, run `/readiness <plan-path>` AT GENERATION TIME against the target plan. Capture findings:

- **PASS items** → confirm in generated prompt as "verified at handoff write time"
- **GAP items** → embed in generated prompt as **`⚠️ VERIFY ON COLD-PICKUP — gap detected at handoff write time:`** annotated warnings
- **FIXED items** → no annotation needed (resolved)
- **DEFERRED items** → cite TECH_DEBT entry if not already done

This eliminates the class of bugs where handoffs are written with stale claims that the future cold-pickup session has to re-derive. The handoff is born with verified-at-write-time truth.

**Compose-by-reference, NOT by-spawning.** This Stage describes what to TELL the caller to do (orchestrate `/readiness` from main session). The /handoff skill itself does NOT spawn a subagent here — orchestration stays in main session for transparency.

If `/readiness` returns RED verdict (substantial gaps), HALT handoff generation + report to operator: "Plan has substantial gaps that should be amended BEFORE handoff is generated. Amending the handoff to reflect known-broken state would lock in the staleness." Operator can override or amend the plan first.

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

**Engine state at handoff write time (anchor-tag):**
- HEAD commit: `<git_sha>`
- Latest tag: `<latest_tag>`
- Version.hpp: `<engine_version_string>`
- Test count baseline: `<test_count>` passed (verify via `./build/controller_test`)
- Working tree: clean (verified at write time)

**Sprint state snapshot** (from CLAUDE.local.md Current Sprint State Tracker; verify against current at cold-pickup):
- Sprint: <sprint-name> (`plans/<sprint-dir>/MASTER.md`)
- Most recent ship at handoff write: <most-recent-ship>
- Next ship in pipeline: <ship-tag>
- Sprint-wide invariants in force: <invariants-from-tracker>
- Open architectural decisions awaiting operator input: <decisions-from-tracker>

**Verify-on-write status (`/readiness` fired at generation):**
- Verdict at write time: <GREEN / YELLOW / RED>
- Gap findings embedded as `⚠️ VERIFY ON COLD-PICKUP` warnings in body below
- Fresh-context coder MUST run `/readiness` again at pickup + diff against this baseline

---

## TaskList state at handoff write (preserve verbatim for fresh-session pickup)

| ID | Status | Subject |
|---|---|---|
<row per task from Stage 1.5 capture; e.g.,>
| #1 | completed | Step 0.A — Tag rollback anchor + verify build baseline |
| #2 | completed | Step 0.C — Cfg field scope classification table |
| #3 | completed | Step 1 — Two-registry framework infrastructure |
| #4 | **in_progress** | **Step 2 — Cohort migration + ControllerConfig restructure** |
| #5 | pending | Step 3 — Parser state machine for [core N] sections |
| <...> |

**Fresh-session pickup should recreate this TaskList** via TaskCreate for each entry so the multi-step plan stays trackable across sessions. Mark <completed-ids> completed, <in-progress-id> in_progress, <pending-ids> pending immediately after recreation.

If no in-flight tasks at handoff write: "No active task list — fresh-session pickup may create one from the remaining sub-commits below if helpful."

---

## Paste this prompt into a fresh Claude Code session to start <ship-tag>

```
I'm picking up <ship-tag> (<ship-title>) for the <sprint-name> sprint.
This is a fresh context window; do NOT trust any prior-session memory
— verify everything against current code.

## Step 0 — orient + verify state (MANDATORY — BEFORE planning anything)

**This Step 0 is NOT optional. Drift between handoff write time + cold-pickup time is the most common source of session-restart confusion. Verify EVERY claim explicitly.**

1. **SHA-diff trigger check** — compare current state to handoff anchor-tag at top of this prompt:
   - `cat /home/caramel/code/FoxML_Trader_v2/Version.hpp` — must match anchor-tag's "Version.hpp:" value
   - `cd /home/caramel/code/FoxML_Trader_v2 && git rev-parse HEAD` — must match anchor-tag's "HEAD commit:"
   - `cd /home/caramel/code/FoxML_Trader_v2 && git tag --sort=-creatordate | head -3` — confirm anchor-tag's "Latest tag:" still on top
   - `cd /home/caramel/code/FoxML_Trader_v2 && git status` — must be clean
   - `./build/controller_test 2>&1 | tail -3` — test count must be ≥ anchor-tag's "Test count baseline:"

   **If ANY value diverges from the handoff anchor-tag**: a ship landed between handoff write + this pickup. This handoff's claims may be stale. STOP planning; investigate the divergence first by reading `git log <anchor-sha>..HEAD` to understand what changed; verify each claim in this handoff body against current state before proceeding.

2. **Read these in parallel (load context):**
   - `CLAUDE.md` (engine repo; slim post-2026-05-14 refactor — operational orientation + 13 hard invariants)
   - `CLAUDE.local.md` (private overlay; INDEX of going-forward rules; auto-write contracts; Sprint State Tracker)
   - `tick-trader-percore-workspace/DOCS/DESIGN_PHILOSOPHY.md` § <matched-family-sections-per-Stage-3-pattern-match> (the WHY companion)
   - `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/MEMORY.md` (auto-memory index)
   - `plans/<sprint-dir>/MASTER.md` (sprint master plan)
   - `<plan-path>` (THE plan for this ship; **READ THE POST-SHIP AMENDMENT NOTICE AT TOP IF PRESENT** — it invalidates code samples in the body)
   - `plans/<sprint-dir>/postmortems/<latest>.md` (most-recent postmortem)
   - `plans/plan_checks/<latest synthesis doc>` (if pre-coding audit fired previously)

3. **Cross-check Sprint State Tracker against current** — read `CLAUDE.local.md` "Current sprint state" section. Compare to handoff snapshot at top:
   - Most-recent ship: matches?
   - Next ship: matches?
   - Sprint-wide invariants in force: matches?
   - Open architectural decisions: matches?

   Drift indicates ship(s) landed between handoff + pickup. Cross-reference `CLAUDE.local.md` snapshot vs handoff snapshot; flag divergences as `[DRIFT]` items requiring re-verification before coding.

4. **Recreate TaskList from the handoff's "TaskList state" section.** Use TaskCreate per entry to preserve multi-step plan tracking. After all created, set statuses to match the handoff snapshot (`completed` / `in_progress` / `pending`). Without this step the multi-step plan progress evaporates and you'll re-discover already-done work.

5. **Read BEFORE WRITING CODE (per CLAUDE.local.md required reading):**
   - `DOCS/STRATEGY_AND_CODING_RULES.md` (11 strict invariants — private)
   - `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` (7 latency-path rules + Rule 8 mask-blend)
   - `DOCS/LATENCY_OPTIMIZATION_AUDIT.md` (13-part audit — private; touch domain-relevant parts)
   - `DOCS/DESIGN_PHILOSOPHY.md` § 2 (Hard Invariants) + matched family sections per Stage 3

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

## Step 4 — design philosophy reminders (load-bearing rules from DESIGN_PHILOSOPHY.md + CLAUDE.local.md + memory)

**Required reading (matched per Stage 3 plan-pattern scan):**
- `DOCS/DESIGN_PHILOSOPHY.md` § <N> — <family-name> (relevance: <plan-keyword that matched>)
- (...one row per matched family per Stage 3...)

**Going-forward rules + feedback entries (dynamically injected from CLAUDE.local.md + memory):**

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
- Plans live in workspace; symlinked from engine `plans/` → workspace `plans/` (directory-level symlink).

**Path discipline (set 2026-05-14):** ALWAYS cite workspace paths in chat / generated prompts / cross-references. The engine-side `/home/caramel/code/FoxML_Trader_v2/plans/...` resolves identically via symlink, but using it obscures where the file actually lives. Apply to: `plans/` (dir symlink), `.claude/skills/` → workspace `claude-skills/` (dir symlink), `DESIGN_SPECS/` (workspace-native), `DOCS/<symlinked-md>` (per-file symlinks; Edit tool REFUSES writes through these). When in doubt: `readlink -f <path>` to see the real location.

- Sprint plans: `/home/caramel/code/tick-trader-percore-workspace/plans/<sprint-dir>/{MASTER.md, subplans/, plan_checks/, postmortems/, handoffs/}`
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

**ALWAYS write to the workspace path explicitly:**

```
/home/caramel/code/tick-trader-percore-workspace/plans/<sprint-dir>/handoffs/<YYYY-MM-DD>-<ship-tag>-handoff.md
```

**Do NOT write to `/home/caramel/code/FoxML_Trader_v2/plans/...` even though it resolves identically via symlink.**

**Why:** the engine repo's `/home/caramel/code/FoxML_Trader_v2/plans/` is a DIRECTORY-LEVEL SYMLINK to workspace `plans/`. Writing through the engine path technically works (the underlying file ends up in workspace), BUT the path you CITE in subsequent communication misleads about where the file actually lives. Caramel called this out 2026-05-14:

> "why did you make the plan in this directory? it should be in the tick trader one."

Use the workspace path EXPLICITLY in:
1. The `Write` tool call's `file_path` parameter
2. The Stage 7 confirmation output to the user
3. Any cross-reference paths included in the generated handoff doc body's "Quick links" section + "Plan file" / "Sprint MASTER" / "Latest postmortem" lines in the header

`mkdir -p` the dir via the workspace path if it doesn't exist (`/home/caramel/code/tick-trader-percore-workspace/plans/<sprint-dir>/handoffs/`).

**Same path-discipline rule applies to all workspace-symlinked content** when this skill or subsequent ships need to write to:
- `plans/` (directory symlink) → write via `/home/caramel/code/tick-trader-percore-workspace/plans/...`
- `.claude/skills/` (directory symlink) → write via `/home/caramel/code/tick-trader-percore-workspace/claude-skills/...`
- `DESIGN_SPECS/` (workspace-native; no engine source) → write via `/home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/...`
- `DOCS/<symlinked-md>` (per-file symlinks; Edit tool REFUSES to write through them) → write via `/home/caramel/code/tick-trader-percore-workspace/DOCS/<file>.md`

Cite workspace paths in chat / generated prompts / cross-references regardless of which path the tool harness happens to accept.

### Stage 7 — Confirm to user

Print:
- **Path of generated handoff — WORKSPACE path explicitly (`/home/caramel/code/tick-trader-percore-workspace/plans/<sprint-dir>/handoffs/<file>.md`).** Do NOT cite the engine-side `/home/caramel/code/FoxML_Trader_v2/plans/...` path even though it resolves identically via symlink. Caramel wants workspace paths for clarity (2026-05-14 feedback after the first miscited handoff).
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
- **Live `TaskList` invocation** — serialize current in-flight task state into the generated handoff (Stage 1.5; set 2026-05-15)

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
[skill writes /home/caramel/code/tick-trader-percore-workspace/plans/v5.14-foxml-port-and-maker/handoffs/2026-05-10-v5.14.10-handoff.md  (WORKSPACE path explicitly)]
[skill prints summary + WORKSPACE path]
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
