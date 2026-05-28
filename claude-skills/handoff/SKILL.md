---
name: handoff
description: Generate a self-contained handoff prompt for opening a sub-ship in a fresh context window. Composes the 9-step pickup workflow (pre-flight verification → required reading → plan re-verification → pre-coding audit gate → DESIGN_SPECS pattern check → design philosophy reminders → TECH_DEBT items in surface area → filesystem conventions → sprint-close verification gate). Reads CLAUDE.local.md going-forward rules + DESIGN_SPECS/*.md catalog + auto-memory MEMORY.md + DOCS/TECH_DEBT.md dynamically so each prompt reflects current discipline. Output: /home/caramel/code/tick-trader-percore-workspace/plans/<sprint>/handoffs/<YYYY-MM-DD>-<ship>-handoff.md (WORKSPACE path explicitly, never engine-side symlink). Layer 1 orchestrator (compose-by-reference, NOT by-spawning).
type: skill
concern: workflow
audit_cadence: per-ship
tags: [operator-collaboration, doc-discipline, plan-template]
surface: []
sister_skills: [/readiness, /precoding-audit-gate, /plan-draft]
loads_dynamically: [CLAUDE.local.md, CLAUDE.md, DOCS/DESIGN_PHILOSOPHY.md, DESIGN_SPECS/README.md, memory/MEMORY.md, DOCS/TECH_DEBT.md, DOCS/PARITY_ISSUES.md, DOCS/LANDMINES.md]
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

- `/handoff <ship-tag>` — auto-resolve plan path via glob: `plans/<active-sprint-dir>/subplans/*<ship-tag>*.md`
- `/handoff <ship-tag> <plan-path>` — explicit plan path (use when glob is ambiguous or the plan lives outside the standard subplans dir)
- `/handoff` (no args) → ERROR. Sub-ship target must be specified.

The `<ship-tag>` is whatever uniquely identifies the sub-ship in the workspace (typically a version sub-tag like the rightmost `.X` of the plan's target ship; the skill substitutes it everywhere in the generated handoff via placeholders).

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

1. Parse `<ship-tag>` (any sub-ship identifier — typically a version sub-tag of the form `vMAJOR.MINOR.PATCH[.LETTER...]` or shorter rightmost form like `.A.1`).
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

Without explicit TaskList capture, fresh-session pickup loses track of the multi-step plan progress; in-flight tasks must be recreated from memory which drifts.

**Additional dynamic-load contracts:**

When composing the handoff body, scan the in-flight plan + recent commits for surface indicators and pre-load matching DESIGN_SPECS bodies + skill references:

| Plan / commit surface contains | Pre-load reference |
|---|---|
| OMS / drainer / fee_rate / commission / slippage / P&L / kill switch | `decision-time-data-binding-pattern.md` + RECURRING_BUG_PATTERNS Class 27 + `/accounting-audit` skill reference |
| New registry introduction OR cache-on-subsystem-state | `decision-time-data-binding-pattern.md` § Framework-selection criteria + `/registry-fit-audit` skill reference + DESIGN_PHILOSOPHY § 1.5 Framework-selection criteria sub-section |
| `cfg.cores[c]` reads or per-core registry work | `cfg-scope-discipline.md` + RECURRING_BUG_PATTERNS Class 25 + Class 26 + Class 27 |
| ML cfg fields (ridge_*, thompson_*, confidence_*, bandit_*) | `cfg-scope-discipline.md` + decision-time-data-binding-pattern.md (ConfidenceScorer / ThompsonBandit state are Class 27 target subsystems) + `/accounting-audit` |
| ImGui widget / Settings panel | (no new dynamic load required; existing widget-ID discipline applies) |

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

### Stage 1.6 — Multi-session ship awareness

Detect when ship state spans multiple sessions. Without this Stage, fresh-session pickup loses visibility into in-flight ship progress; handoffs become brittle when intra-ship WIP-checkpoint commits or plan body amendments accumulate mid-ship.

**Detection commands:**

1. **Pre-tag rollback anchor** (always exists for any ship that's started coding): `git tag --list 'pre-<ship-tag>'`
2. **WIP-checkpoint commits** (present when ship has had mid-session commits): `git log <pre-tag>..HEAD --oneline --grep='WIP-checkpoint'` — captures commit hash + subject + LOC stats per commit via `--stat`
3. **Plan body iteration history**: parse plan body status banner (line starting with `**Status:**`) — extract current version + each "v1.N closes" / "v1.N supersedes" sub-clause referenced
4. **Audit batch history**: glob `plans/<sprint-dir>/plan_checks/*<ship-tag>*synthesis*.md` — list all audit synthesis docs with their batch labels (Batch 1, Batch 2 RE-SWEEP, Batch N pre-coding, etc.)

**Embed in generated handoff prompt body** as a "Ship state across sessions" section. Use placeholder rows; the dynamic-load fills in actual values per ship. If WIP-checkpoint commits don't exist (single-session ship), omit that sub-section. If plan body has only 1 iteration (no v1.N history), omit history table.

Template shape (skill substitutes actual values):

```markdown
## Ship state across sessions (multi-session awareness)

**Pre-tag rollback anchor:** `pre-<ship-tag>` at engine commit `<sha>` (initial coding start)

**Mid-ship WIP-checkpoint commits** (intra-ship rollback anchors; omit if none):
- `<sha>` — `<commit subject>` (<files>/<insertions>/<deletions>)

**Plan body iteration history** (omit if single iteration):
- v1.<N> → `<one-line summary of what landed>`
- ...

**Audit batches fired** (omit if no audits):
| Batch | Date | Verdict | Synthesis doc |
|---|---|---|---|
| <batch label> | <date> | <verdict> | `plan_checks/<filename>` |
```

### Stage 1.7 — Per-Step landed/pending status enumeration

Parse the plan body's Steps section for Step identifiers + cross-reference to commit log:

1. Extract all Step identifiers from plan body (regex `Step \d+(\.\d+([.a-zA-Z0-9]+)*)?`)
2. For each Step: grep commits between pre-tag and HEAD for the Step reference (commit subject or body)
3. Categorize each Step:
   - **LANDED**: commit message references Step with verbiage like "complete" / "landed" / "closure" / "shipped"
   - **IN_PROGRESS**: current TaskList shows the Step as `in_progress`, OR commit references it as WIP/partial
   - **PENDING**: neither LANDED nor IN_PROGRESS
4. For LANDED Steps, capture short SHA of landing commit
5. For PENDING Steps, parse plan body BUILD-FORCED sequencing list to identify what's BLOCKING (predecessor Steps)

**Embed in generated handoff prompt body** as a "Per-Step status at handoff write" section. Table shape (skill substitutes actual rows):

```markdown
## Per-Step status at handoff write

| Step | Status | Landed at | Blocked by |
|---|---|---|---|
| <step identifier> | LANDED | `<commit-sha>` | — |
| <step identifier> | IN_PROGRESS | — | — |
| <step identifier> | **NEXT** (ready) | — | — |
| <step identifier> | PENDING | — | <blocking predecessor> |
```

Visualizes ship progress at a glance + makes "where to start" unambiguous for fresh-session pickup. For single-session ships where everything is PENDING, the table is still useful as a checklist.

### Stage 1.8 — Decision log writer + /capture-audit pre-write gate (added 2026-05-26)

**Decision log capture** (sister to TaskList capture at Stage 1.5):

If planning cycle exceeded 3 amendments (detected via plan body version history at Stage 1.6) OR session spans multiple days, write/update session decision log at:
`plans/<sprint>/decision-logs/<plan-name-stem>-v<X.Y.Z>.md`

Template at `claude-skills/capture-audit/decision-log-template.md`. Sections:
- **Decisions** (operator-decided actions; capture from conversation + plan body amendments)
- **Commitments** (claude-said-will-do; capture from response history)
- **Discoveries** (new findings surfaced this cycle; capture from audit reports)
- **Drift watch** (auto-populated by /capture-audit Check 4 from sentinel markers)
- **Cycle close summary** (filled at next plan body version bump)

Cite the decision log in the generated handoff doc under "Required reading files" so receiver session loads it.

**Pre-write /capture-audit gate (deterministic invocation per .D Phase F.3):**

Before writing the handoff doc, run the Check 11 forward-promise verification deterministically as a hard gate. If HIGH findings: BLOCK handoff write; resolve drift first.

```bash
# Deterministic invocation — replaces LLM-orchestrated /capture-audit Skill invocation:
python3 /home/caramel/code/FoxML_Trader_v2/tools/check_forward_promise_audit.py \
    --strict \
    --since "${LAST_TAG:-HEAD~5}"

# Exit code != 0 → BLOCK handoff write; address drift or # CHECK_11_EXEMPT marker
# Sister to B-Plus pre-commit hook (Class 14 fabrication detection at commit time)
# Sister to /capture-audit --deep invocation (full 11-check coverage; Check 11 is now mechanical)
```

The above MUST run before writing the handoff doc; LLM-orchestrated invocation can drift, miss the gate, or misinterpret output. Per `feedback_structural_enforcement_when_memory_insufficient` (M7), tool invocation replaces memory-driven discipline at this load-bearing surface.

The deep gate ALSO verifies (sister checks beyond Check 11):

```
- MEMORY.md index sync check
- Plan body frontmatter completeness (audit_tier + sister_specs + deletion_scope)
- Decision-log artifact existence + sentinel matching
- Stage 6 promotion candidates per M7
- Skill-in-CLAUDE.md-suite linkage
```

If findings present:
- HIGH severity: ABORT handoff write; surface findings to operator + require fix before re-invocation
- MED/LOW: include findings in handoff doc under "Drift items to address at pickup" section + proceed

Per `feedback_structural_enforcement_when_memory_insufficient` (M7) + `feedback_session_decision_log_discipline`: handoff writer is the structural-capture surface; pre-write verification closes the "I forgot to capture X" failure mode.

**NEW v5.15.5.F.4d.1.B.4 v1.7.5 WIP-12 — `deletion_scope:` frontmatter field:**

Handoff doc frontmatter MUST declare `deletion_scope:` field when in-flight plan body proposes deletion-class scope. Values:

- `none` — no deletion-class scope (most ships); receiver-side /accept-handoff doesn't fire deletion-class audits
- `minor` — single-file or trivial deletion (no B14 audit needed; standard pre-coding gate sufficient)
- `major` — feature/cfg/symbol deletion spanning ≥3 files with compile-time interdependencies (B14 multi-surface deletion ordering audit REQUIRED at pre-coding gate; B-Plus v0.4 `--gen-deletion-cohort PATTERN` mechanizes; sister B15 audit fires if UNCONDITIONALIZE-body kind sites present per generator classification)

Receiver-side /accept-handoff Stage 4 reads `deletion_scope:` field + auto-fires `/blindspot-scan B14`/`B15` audits at pre-coding gate when `major`. Sister: `feedback_multi_surface_deletion_ordering_discipline` + `feedback_unconditionalization_latent_assumption_audit` + `feedback_operator_facing_doc_cohort_at_cfg_deletion` + /readiness Check 41/42/43 sidecars + /precoding-audit-gate deletion-class auto-fire (sister Stage 1 auto-derived focus keyword).

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
| `tick-trader-percore-workspace/DOCS/DESIGN_PHILOSOPHY.md` | Thematic narrative + 4-tier discipline (HARD / STRONG / SOFT / PROCESS) + cross-reference index. Match plan keywords to family sections (§ 3 Hard Invariants / § 4 Latency / § 5 Determinism / § 6 Concurrency / § 7 Structural-fix / § 8 Failure observability / § 9 Architectural primitives / § 10 Operator UX / § 11 Process discipline) + cite specific § N rows in generated prompt's Step 4. |
| `plans/<sprint-dir>/MASTER.md` | Sprint context; ship's position in sub-tag sequence |
| `<plan-path>` (resolved) | Ship's stated scope; stale-claim audit target |
| `plans/<sprint-dir>/postmortems/` | Most-recent sub-ship postmortem (lessons that may apply) |
| `CLAUDE.local.md` Current Sprint State Tracker section | Most-recent ship + next-ship + sprint-wide invariants in force + open architectural decisions. Embed as snapshot in generated prompt for cold-pickup-time drift detection. |

**CLAUDE.local.md as index:** the file is
a pointer-based index, NOT a long philosophy dump.
For each going-forward rule named in CLAUDE.local.md that overlaps
the ship's surface, follow its DESIGN_SPECS pointer + load that body
into context. This ensures the generated prompt's Step 3 "design check
against pattern library" references concrete pattern bodies the
future session needs, not just names.

### Stage 2.5 — Verify-on-write (anti-staleness fire)

Addresses observed drift between handoff prompt and reality at cold-pickup time per `feedback_compaction_degrades_treat_handoffs_as_hints`.

Before composing the handoff prompt, run `/readiness <plan-path>` AT GENERATION TIME against the target plan. Capture findings:

- **PASS items** → confirm in generated prompt as "verified at handoff write time"
- **GAP items** → embed in generated prompt as **`⚠️ VERIFY ON COLD-PICKUP — gap detected at handoff write time:`** annotated warnings
- **FIXED items** → no annotation needed (resolved)
- **DEFERRED items** → cite TECH_DEBT entry if not already done

This eliminates the class of bugs where handoffs are written with stale claims that the future cold-pickup session has to re-derive. The handoff is born with verified-at-write-time truth.

**Compose-by-reference, NOT by-spawning.** This Stage describes what to TELL the caller to do (orchestrate `/readiness` from main session). The /handoff skill itself does NOT spawn a subagent here — orchestration stays in main session for transparency.

If `/readiness` returns RED verdict (substantial gaps), HALT handoff generation + report to operator: "Plan has substantial gaps that should be amended BEFORE handoff is generated. Amending the handoff to reflect known-broken state would lock in the staleness." Operator can override or amend the plan first.

### Stage 2.6 — Coding-time discoveries auto-extraction

If plan body has a "Coding-time discoveries" section (any plan body that follows the convention of capturing session-real findings as `D-N` numbered entries; common shape: `## Coding-time discoveries` header followed by `### D-N: <title>` entries with Catalyst / Resolution / Lesson sub-fields), auto-extract entries verbatim into the generated handoff body.

These entries capture what coding sessions ACTUALLY found vs what plan-time audits initially expected (e.g., missed consumer X-macro caught at build break; field-type asymmetry surfaced at struct-gen; sequencing dependency discovered at implementation). Fresh-session pickup reads them BEFORE diving in to avoid re-discovering the same issues.

**Extraction shape** in generated prompt (skill substitutes actual D-N entries from plan body):

```markdown
## Coding-time discoveries from prior session(s)

Pulled verbatim from plan body "Coding-time discoveries" section. Session-real findings; assume they shape what you'll hit next.

### D-<N>: <title>
- **Catalyst:** <what triggered the discovery>
- **Resolution:** <what was done>
- **Lesson:** <what to watch for>

(...one entry per D-N row in plan body...)
```

If plan body has no "Coding-time discoveries" section, omit this section entirely from the generated handoff.

### Stage 2.7 — Mid-session meta-gap codification detection

Detect DESIGN_SPECS amendments made since the pre-tag rollback anchor via workspace git log:

```bash
cd /home/caramel/code/tick-trader-percore-workspace
git log <pre-tag-creation-time>..HEAD --pretty=format:'%h %s' --diff-filter=AM -- DESIGN_SPECS/
```

For each DESIGN_SPEC amendment found:
1. Cross-reference to plan body "Meta-gaps surfaced" / "DESIGN_SPECs landed/amended" sections if present
2. Categorize: NEW Stage 2 DRAFT / EXTENDED with new sub-section / Banner-only revision
3. Identify any PROMISED ship-close auto-writes referenced in plan body Step 9 list (feedback memories / skill amendments / CLAUDE.local.md going-forward rule additions)

**Embed in generated prompt** as a "Mid-ship DESIGN_SPEC amendments" section:

```markdown
## Mid-ship DESIGN_SPEC amendments (and PROMISED ship-close auto-writes)

| Spec amended this ship | Change type | Promised auto-writes at ship close |
|---|---|---|
| `<spec-filename>` | <NEW Stage 2 DRAFT / EXTENDED § / Banner-only> | <e.g., NEW feedback memory / /readiness Check N / skill amendment> |
```

This makes mid-ship discipline codification visible across sessions — fresh-session pickup knows what's already landed in DESIGN_SPECs vs what's still pending in feedback/memory/skill auto-writes scheduled at ship close.

If no DESIGN_SPEC amendments since pre-tag, omit this section entirely.

### Stage 2.8 — Enumerate predecessor ship verification checklist (added 2026-05-27)

Sister to Stage 2.7 (mid-session DESIGN_SPECS amendments). Where 2.7 captures what landed THIS ship, 2.8 makes the PREDECESSOR ship's claims mechanically verifiable at receiver-side pickup.

**Why this exists:** Predecessor ship close ritual can leave artifacts incomplete (memory file written but MEMORY.md not indexed; DESIGN_SPECS Stage promotion frontmatter not bumped; TECH_DEBT entry not moved from open.md to closed.md; etc.). A receiver picking up the next ship is the natural overlapping-check surface to catch predecessor incompleteness — they'll be reading these artifacts to plan their own ship and can mechanically verify each claim in the handoff body's "What landed at <predecessor-tag> ship close" section.

This overlap between Step 1 (current state verify) + Step 1.4 (predecessor verify; NEW) + Step 1.5/1.6 (in-flight ship verify) + Step 0 /accept-handoff is intentional. Overlapping checks across phases catch drift that single checks miss.

For each artifact claim cited in the handoff body's predecessor-context section, ensure the citation is concrete enough for receiver-side mechanical verification. Required citation format per claim:

- **Tag name + date** — exact git tag string + ISO date
- **Test count baseline** — exact pass count at ship close
- **TECH_DEBT closures** — list of `TECH_DEBT-NNN` IDs
- **PARITY closures** — list of `PARITY-NNN` IDs
- **DESIGN_SPECS Stage promotions** — `<spec-filename> Stage X → Stage Y` per row
- **Class catalog amendments** — `Class N recurrence_count A→B` per row
- **NEW DESIGN_SPECS landed** — full file paths (workspace-prefixed; the DESIGN_SPECS dir is workspace-only, not symlinked into engine repo)
- **NEW memories** — full file paths (`~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/<name>.md`)
- **NEW going-forward rules** — title + date as cited in CLAUDE.local.md `Going-forward rules (index)` section
- **Version.hpp value** — exact string at predecessor ship close

These are enumerated in the handoff body's `## What landed at <predecessor-tag> ship close (PREDECESSOR CONTEXT)` section. Stage 2.8 of /handoff ensures the citation discipline is followed; Step 1.4 of the generated prompt enables the receiver to verify mechanically.

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

### Stage 4 — Scan TECH_DEBT for ship-scoped in-flight status

Two passes:

**Pass A — Surface overlap (existing debt that the ship might absorb):**

For each OPEN TECH_DEBT entry:
1. Parse `Surface:` line
2. Check if surface mentions any path/file/registry the ship will touch
3. If overlap: include the entry in the handoff with the surface match highlighted

This surfaces existing-debt that the ship might naturally absorb or explicitly defer.

**Pass B — Ship-scoped in-flight status (NEW):**

For TECH_DEBT entries cited in the ship's plan body (either as closure targets or as NEW entries to open):
1. Parse plan body for `TECH_DEBT-NNN` references (closures + new-opens)
2. For each cited entry, check current status in `DOCS/TECH_DEBT.md` (OPEN / CLOSED / IN-FLIGHT / PARTIAL)
3. Check commits between pre-tag and HEAD for the entry reference (commit messages)
4. Categorize at handoff write time:
   - **CLOSED IN SHIP**: commit references entry as closed; verify ledger entry updated
   - **PARTIAL CLOSED**: some sites migrated but plan body lists remaining work
   - **PENDING CLOSURE**: cited as ship closure target but no commit references yet
   - **NEW OPENED MID-SHIP**: commit message references entry as NEW; verify ledger
   - **NEW SCHEDULED**: plan body Step 9 list includes entry but not yet opened

**Embed in generated prompt** as a "TECH_DEBT scoreboard at handoff write" section:

```markdown
## TECH_DEBT scoreboard (in-flight status at handoff write)

**Closure targets cited in plan body:**
| TECH_DEBT | Title | Status |
|---|---|---|
| -<N> | <title> | <CLOSED IN SHIP / PARTIAL / PENDING> @ `<commit-sha if landed>` |

**NEW entries this ship:**
| TECH_DEBT | Title | Status |
|---|---|---|
| -<N> NEW | <title> | <NEW OPENED MID-SHIP / NEW SCHEDULED at ship close> |

**Overlapping existing debt (Pass A surface match):**
| TECH_DEBT | Surface match | Decision |
|---|---|---|
| -<N> | <surface line> | <absorb / refresh / explicit defer> |
```

If any overlapping entry exists, the generated handoff Step 5 still includes the explicit `/readiness` Check 25 (TECH_DEBT scan) reminder.

### Stage 4.5 — Pre-pickup self-audit per 4-pillar discipline

Per the discipline pattern "audit own proposals with same rigor as operator-proposed plans" (any plan body that triggers a handoff should pass a 4-pillar self-audit before claiming "ready for pickup"). The 4 dimensions:

1. **DESIGN_SPECS cross-check**: which patterns in the catalog apply to the ship's next-action? Cite each by filename + relevance per Stage 3 pattern-symptom scan.

2. **Anti-pattern catalog check**: review `DOCS/RECURRING_BUG_PATTERNS.md` Classes 1-N against the ship's next-action. Verify no anti-pattern instances introduced by the staged next-action; explicit CLEAN status per relevant class.

3. **Operator-impact dimension**: what action does the operator (Caramel) need? Migration burden? Workflow disruption? Default toward non-breaking alternatives unless breaking is structurally necessary.

4. **Novel-alternative consideration**: could a novel design fit better given the SPECIFIC purpose of THIS code? Don't default to existing patterns out of inertia; don't default to novelty out of cleverness.

**Embed in generated prompt** as a "Pre-pickup self-audit" section:

```markdown
## Pre-pickup self-audit (4-pillar discipline)

Verified at handoff write time. Fresh-session pickup may re-evaluate if scope shifts.

| Pillar | Verdict | Notes |
|---|---|---|
| 1. DESIGN_SPECS cross-check | <patterns-matched-list per Stage 3> | <relevance per pattern> |
| 2. Anti-pattern catalog | CLEAN per Classes <enumerate-relevant-classes> | <verification notes> |
| 3. Operator-impact | <None / Documented migration steps / Workflow note> | <details> |
| 4. Novel alternative | <Considered, rejected because... / Accepted, supersedes default pattern> | <details> |
```

Fresh-session pickup can verify each pillar against current state. If any pillar's verdict has DRIFTED (e.g., new anti-pattern Class codified post-handoff), pickup re-evaluates before coding.

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
<row per task from Stage 1.5 capture — generic placeholders; the skill substitutes actual TaskList rows at generation time>
| #<n> | <completed / in_progress / pending> | <task subject line> |
| <...one row per task...> |

For a canonical example of how this table looks when populated with real tasks, see any committed handoff in `plans/<sprint>/handoffs/*.md` — the skill regenerates the table per-ship; do NOT hardcode values here.

**Fresh-session pickup should recreate this TaskList** via TaskCreate for each entry so the multi-step plan stays trackable across sessions. Mark <completed-ids> completed, <in-progress-id> in_progress, <pending-ids> pending immediately after recreation.

If no in-flight tasks at handoff write: "No active task list — fresh-session pickup may create one from the remaining sub-commits below if helpful."

---

<insert "Ship state across sessions" section here per Stage 1.6 output — omit entirely if single-session ship with no WIP-checkpoint commits + no plan body iteration history + no audit batches fired>

<insert "Per-Step status at handoff write" section here per Stage 1.7 output>

<insert "Coding-time discoveries from prior session(s)" section here per Stage 2.6 output — omit entirely if plan body has no "Coding-time discoveries" section>

<insert "Mid-ship DESIGN_SPEC amendments" section here per Stage 2.7 output — omit entirely if no DESIGN_SPECS amendments since pre-tag>

<insert "TECH_DEBT scoreboard (in-flight status at handoff write)" section here per Stage 4 Pass B output — include even if empty (says "No TECH_DEBT cited in plan body")>

<insert "Pre-pickup self-audit (4-pillar discipline)" section here per Stage 4.5 output>

---

## Paste this prompt into a fresh Claude Code session to start <ship-tag>

```
---
type: handoff
ship_tag: <ship-tag>
plan_type: refactor | feature | live-readiness | hotfix
sprint_end_goal: <one-line statement from sprint MASTER plan>
ship_end_goal: <one-line statement from sub-plan body>
predecessor_handoff: <path or null>
required_reading: [CLAUDE.md, CLAUDE.local.md, MEMORY.md, plan-body, sprint-MASTER]
coding_status: planning-complete | mid-coding-checkpoint-N | post-ship-postmortem
---

I'm picking up <ship-tag> (<ship-title>) for the <sprint-name> sprint.

**Sprint end goal:** <sprint-end-goal from sprint MASTER plan; e.g., "make the codebase more maintainable for future development">

**Ship end goal:** <1-sentence: what this ship CLOSES / DELIVERS; e.g., "close cfg-derived consumer drift via FOREACH_<COHORT>(BASE_X) meta-walker">

**Plan type:** <refactor | feature | live-readiness | hotfix> — drives acceptance criteria sections per `tick-trader-percore-workspace/DESIGN_SPECS/plan-templates/future-oriented-plan-template.md` § Ship type.

**Required reading BEFORE planning** (load in parallel):
- `CLAUDE.md § Design philosophy + priorities` (NEW 2026-05-18 — End state + DOD + Priority gradients + Doc layer separation)
- `CLAUDE.md § How to find anything` (search guide; metadata-driven retrieval)
- This handoff (entire doc)
- Plan body (cited above)

This is a fresh context window; do NOT trust any prior-session memory
— verify everything against current code.

## Step 0 — Run /accept-handoff (RECOMMENDED — automates Step 0.1-0.7 below)

**ONE COMMAND replaces manual pickup ritual.** Per `feedback_structural_enforcement_when_memory_insufficient` (M7), the receiver-side handoff verification is structurally enforced by the `/accept-handoff` skill rather than relying on manual discipline.

```
/accept-handoff <path-to-this-handoff-doc>
```

This invocation does ALL of the following automatically:

1. Parses this handoff doc; loads every cited file (CLAUDE.md, CLAUDE.local.md, MEMORY.md, plan body, sister plans, predecessor handoff, all "Critical pickup-time reads")
2. Verifies engine + workspace git state matches handoff claims (HEAD SHAs / branch / clean-vs-dirty)
3. Runs `/capture-audit --deep` to verify NO decision-capture drift since handoff written (PENDING items still PENDING? new commits not reflected? Stage 6 promotion candidates surfaced?)
4. Runs `/readiness` against the in-flight plan body cited above
5. Recreates TaskList from the "TaskList state at handoff write" section below
6. Reads always-loaded baseline (CLAUDE.md + CLAUDE.local.md + MEMORY.md)
7. Outputs PICKUP-READY status + concrete "your immediate next action is X" instruction

If `/accept-handoff` returns CLEAN: proceed to coding per the concrete next action.
If `/accept-handoff` returns BLOCK findings: address them before continuing.

**Skip /accept-handoff ONLY if** you need to manually pace through each verification step (rare; use Step 0.1-0.7 below for that). For typical pickup, /accept-handoff is faster, more reliable, and structurally enforced.

## Step 0.1-0.7 (Manual pickup; use ONLY if /accept-handoff unavailable or you have specific reason to manually pace) — orient + verify state

**This Step 0.x is NOT optional if skipping /accept-handoff. Drift between handoff write time + cold-pickup time is the most common source of session-restart confusion. Verify EVERY claim explicitly.**

1. **SHA-diff trigger check** — compare current state to handoff anchor-tag at top of this prompt:
   - `cat /home/caramel/code/FoxML_Trader_v2/Version.hpp` — must match anchor-tag's "Version.hpp:" value
   - `cd /home/caramel/code/FoxML_Trader_v2 && git rev-parse HEAD` — must match anchor-tag's "HEAD commit:"
   - `cd /home/caramel/code/FoxML_Trader_v2 && git tag --sort=-creatordate | head -3` — confirm anchor-tag's "Latest tag:" still on top
   - `cd /home/caramel/code/FoxML_Trader_v2 && git status` — must be clean
   - `./build/controller_test 2>&1 | tail -3` — test count must be ≥ anchor-tag's "Test count baseline:"

   **If ANY value diverges from the handoff anchor-tag**: a ship landed between handoff write + this pickup. This handoff's claims may be stale. STOP planning; investigate the divergence first by reading `git log <anchor-sha>..HEAD` to understand what changed; verify each claim in this handoff body against current state before proceeding.

1.4. **Predecessor ship verification (NEW 2026-05-27)** — mechanically verify each artifact claim in this handoff body's `## What landed at <predecessor-tag> ship close (PREDECESSOR CONTEXT)` section. Sister to Step 1 (CURRENT state) + Step 1.5 (IN-FLIGHT ship state) — this step covers PREDECESSOR claims. Overlapping checks across phases catch drift single-check phases miss.

   For each cited predecessor artifact, run the corresponding verify command:

   | Artifact claim | Verify command | Pass criterion |
   |---|---|---|
   | Predecessor tag exists | `git tag --list <predecessor-tag>` | Exact match |
   | Predecessor tag GPG-signed | `git tag --verify <predecessor-tag>` | Signature valid |
   | CHANGELOG.md row landed | `rg "^### <predecessor-tag>" DOCS/CHANGELOG.md` | Returns 1 match |
   | Postmortem file exists | `ls plans/<sprint>/postmortems/<date>-<predecessor-tag>-postmortem.md` | File exists |
   | TECH_DEBT closures actually moved | For each `TECH_DEBT-N` closure cited: `rg "id: TECH_DEBT-N" tick-trader-percore-workspace/DOCS/tech-debt/closed.md` AND `rg "id: TECH_DEBT-N" tick-trader-percore-workspace/DOCS/tech-debt/open.md` | First returns match; second returns NO match |
   | PARITY closures marked closed | For each `PARITY-NNN`: `rg -A3 "^id: PARITY-NNN" tick-trader-percore-workspace/DOCS/PARITY_ISSUES.md` | Shows `status: closed` |
   | DESIGN_SPECS Stage promotions | For each cited Stage X→Y: `grep "^stage:" tick-trader-percore-workspace/DESIGN_SPECS/<path>.md` | Shows promoted stage |
   | NEW memory files exist + indexed | For each cited memory: `ls ~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/<name>.md` AND `grep <name>.md ~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/MEMORY.md` | Both succeed |
   | NEW going-forward rules cited | For each rule: `grep -A2 "<rule-title>" CLAUDE.local.md` | Returns match in "Going-forward rules (index)" section |
   | Version.hpp matches predecessor | `cat Version.hpp` (engine repo) | String matches predecessor-tag's claimed Version.hpp value at the time of its ship close |

   **If ANY predecessor claim fails verification:** the predecessor ship close ritual was incomplete OR an intervening commit reverted/moved the artifact. Common failure modes:
   - Memory file written but MEMORY.md index never updated → orphan memory
   - DESIGN_SPECS amendment landed but `stage:` frontmatter not bumped to match the cited promotion
   - TECH_DEBT entry not moved from `open.md` to `closed.md` despite ship narrative claiming closure
   - PARITY entry status flag still `open` despite cited closure

   For each failure: investigate via `git log --all <commit-author>..HEAD -- <path>` to find when the artifact was last touched; fix immediately if it's a close-ritual gap (NOT defer per `feedback_no_defer_for_effort`); re-run /capture-audit --deep to verify CLEAN before continuing to Step 1.5.

   **This step is OVERLAPPING with `/capture-audit` Check 1 (MEMORY.md sync) + Check 7 (DESIGN_SPECS promotion) + Check 8 (skill linkage) by design.** Overlapping checks at different phases catch drift the other might miss — defense in depth at handoff seam.

1.5. **Multi-session ship anchor check (NEW)** — if this is a multi-session ship (handoff "Ship state across sessions" section lists WIP-checkpoint commits), verify those anchors are still in the log:
   - `git log <pre-tag>..HEAD --oneline --grep='WIP-checkpoint'` — should match handoff's listed WIP-checkpoint commits
   - `git log <pre-tag>..HEAD --stat | head -50` — review LOC stats per commit against handoff claims
   - If a WIP-checkpoint commit listed in the handoff is MISSING from log: someone rebased/squashed mid-ship; investigate before proceeding
   - If EXTRA WIP-checkpoint commits appear (handoff doesn't list them): handoff is stale; verify what those commits did before assuming any "Per-Step status" claim in handoff is current

1.6. **Per-Step status drift check (NEW)** — handoff's "Per-Step status at handoff write" table may have drifted:
   - For each LANDED Step listed: `git log --oneline --grep='<Step identifier>' <pre-tag>..HEAD` — verify the cited landing commit still exists
   - For each IN_PROGRESS Step listed: verify TaskList recreation at Step 0.4 below preserves that status
   - For PENDING Steps: verify BUILD-FORCED sequencing in plan body hasn't been amended since handoff (re-read plan body BUILD-FORCED list)

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

Per `tick-trader-percore-workspace/DESIGN_SPECS/audit-methodologies/audit-driven-pre-coding-gate.md`, fire the gate when ship has 2+ of: closes recurring bug class structurally, touches wire format, adds 5+ new fields/functions/cfg entries, refactors fn used at 5+ sites, picks up work from previous (possibly compacted) session.

<conditionally-included if ship qualifies>

**SHAPE-layer audits (always fire):** Spawn these audits IN PARALLEL via Agent tool with Explore subagents:
1. `/parity-check` — focus: train↔serve identity; stamp body if applicable; production-caller field-population
2. `/trace-deps` — focus: plan file:line claims; function signatures match planned; dependency-chain
3. `/readiness` (full 28-check pass + Checks 36-39 per M4) — cold-pickup completeness; new cfg field eligibility; X-macro variant selection; sister-registry parity / transitional state / include topology / row-order parity
4. `/merge-scan` — focus: reuse opportunities; mirror-incomplete patterns
5. `/dod-audit` — focus: DESIGN_SPECS pattern application; missed bit-packing / X-macro / cache-alignment candidates

**IMPLEMENTATION-DETAIL-layer audit (conditional fire per meta-discipline M4):** AFTER SHAPE audits return GREEN/YELLOW, fire `/blindspot-scan` if ANY of:
6. Struct-gen migration crosses ≥2 registries
7. Type unification migration (STORAGE_T column adoption; type shifts across rows)
8. Cross-registry consumer (single struct/function reads fields from ≥2 registries)
9. Macro hoisting (X-macro walker bodies extracted from call sites into framework primitive)
10. Include surface change (new cross-directory includes proposed)
11. Wire-format ordering change (master registry order differs from legacy walker emit order)
12. SHAPE audits returned GREEN/YELLOW after 3+ iterations on same plan (inflection signal)

`/blindspot-scan` walks the 12-category implementation-detail taxonomy at `tick-trader-percore-workspace/DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` (per `DOCS/DESIGN_PHILOSOPHY.md` § 11.5 meta-discipline M4). SHAPE audits answer "is design right?"; IMPLEMENTATION-DETAIL answers "will code compile/run without surprise?" — both layers needed.

After all reports return, synthesize convergent findings to `plans/plan_checks/<date>-<ship-tag>-fresh-audits-synthesis.md`. THEN consult Caramel before coding. Do NOT auto-proceed even if findings look addressable (per CLAUDE.local.md feedback_consult_on_audit_findings memory).
</conditionally-included>

## Step 3 — design check against pattern library

Required reading (DESIGN_SPECS catalog — workspace-only, NOT symlinked into engine repo; cite workspace path explicitly):
- `tick-trader-percore-workspace/DESIGN_SPECS/README.md` (full pattern catalog + "I need to..." quick discovery)
<for each pattern matched in Stage 3 above:>
- `tick-trader-percore-workspace/DESIGN_SPECS/<pattern>.md` — <reason it matched the plan>
</for>

Don't write code until the matched-pattern docs are read + integration plan articulated.

## Step 4 — design philosophy reminders (load-bearing rules from DESIGN_PHILOSOPHY.md + CLAUDE.local.md + memory)

**Required reading (matched per Stage 3 plan-pattern scan):**
- `DOCS/DESIGN_PHILOSOPHY.md` § <N> — <family-name> (relevance: <plan-keyword that matched>)
- (...one row per matched family per Stage 3...)

**Going-forward rules + feedback entries (dynamically injected from CLAUDE.local.md + memory):**

<inject going-forward rules + relevant feedback entries dynamically from CLAUDE.local.md + memory/MEMORY.md indexes>; do NOT hardcode specific rule bodies — they're the index source. Sample rules to inject based on plan's surface tags: defer-discipline, structural-fix, boundary-stable, hot-path-discipline, branchless-on-slow-path, reuse-audit, latency-additions-tracked, replay-determinism, bump-Version.hpp-on-ship, no-AskUserQuestion, evaluate-on-robustness-not-time, consult-on-audit-findings, address-Caramel-as-Caramel.

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
- DESIGN_SPECS catalog: `workspace/DESIGN_SPECS/` — pattern catalog + README. New patterns promote in via 2+ canonical applications per `pattern-codification-lifecycle.md`. Catalog grows over time; do NOT hardcode count here (consult README.md for current set).
- Skill outputs go to `plans/plan_checks/<skill>-<YYYY-MM-DD>-<scope>.md` (neutral); batches into sprint dir at close.
- TECH_DEBT auto-write: `DOCS/TECH_DEBT.md` (symlinked from workspace)
- PARITY_ISSUES auto-write: `DOCS/PARITY_ISSUES.md` (symlinked from workspace)
- HOT_PATH_CHANGELOG: `DOCS/HOT_PATH_CHANGELOG.md` (symlinked from workspace)
- **DOCS/ symlinks editing convention:** many `DOCS/*.md` files in the engine repo are PER-FILE SYMLINKS to workspace. The `Edit` tool REFUSES to write through symlinks. ALWAYS check `readlink -f path` before editing a `DOCS/*.md` file; if it resolves to a workspace path, edit via the workspace path directly. Symlink-resolved files include: HOT_PATH_CHANGELOG, PARITY_ISSUES, TECH_DEBT, plus most CLAUDE_*.md / RECURRING_BUG_PATTERNS / EASY_ADDITIONS_INVARIANTS / sister-architectural docs. Engine-tracked exceptions (NOT symlinked): QUICKSTART, OPERATOR_DEPLOYMENT, CONFIGURATION, ML_USAGE, ML_TRAINING, CONTRIBUTING, LATENCY_PROFILING.

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

If you find yourself writing complex plumbing, stop — check `tick-trader-percore-workspace/DESIGN_SPECS/README.md` "I need to..." section. There's almost certainly a pattern that applies.

Good luck. Caramel will iterate with you on findings before coding.
```

---

## Notes for future-Claude reading this handoff doc

- Prompt above is self-contained — paste as FIRST message in a fresh `claude code` session.
- Includes 9 steps + design philosophy reminders + filesystem conventions.
- Follow them in order; don't skip Step 1 (re-verification against current code).

---

## Quick links

- Sprint MASTER: <link to plans/<sprint>/MASTER.md (workspace path)>
- This ship's plan: <link to plans/<sprint>/subplans/<plan>.md (workspace path)>
- Latest postmortem: <link to plans/<sprint>/postmortems/<latest>.md (workspace path)>
- DESIGN_SPECS catalog: `tick-trader-percore-workspace/DESIGN_SPECS/README.md`
- Latency rules: `plans/_cross-cutting/2026-05-06-latency-path-discipline.md` (workspace path; symlinked from engine)
- Coding invariants: `DOCS/STRATEGY_AND_CODING_RULES.md` (engine repo; private)
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

## Example invocation (generic flow)

```
$ /handoff <ship-tag>
[skill reads Version.hpp → extracts ENGINE_VERSION_STRING → resolves active sprint dir via glob]
[skill globs plans/<active-sprint-dir>/subplans/*<ship-tag>*.md → 1 match expected]
[skill reads MASTER, plan, CLAUDE.local.md, MEMORY.md, DESIGN_SPECS/README.md, TECH_DEBT.md]
[skill scans plan for DESIGN_SPECS pattern symptoms — matches per Stage 3 indicator table]
[skill scans TECH_DEBT for ship-scope status (Pass A surface overlap + Pass B in-flight)]
[skill detects multi-session state per Stage 1.6 (WIP-checkpoints / iteration history / audit batches)]
[skill enumerates Per-Step status per Stage 1.7]
[skill extracts Coding-time discoveries (Stage 2.6) + DESIGN_SPEC amendments (Stage 2.7) if present]
[skill runs Stage 4.5 4-pillar self-audit]
[skill composes handoff prompt per Stage 5 + writes via Stage 6 workspace path]
[skill prints summary + WORKSPACE path per Stage 7]
```

For a canonical example output, see any committed handoff in `plans/<sprint-dir>/handoffs/*-handoff.md` — each one represents the actual generated output for a specific ship. Do NOT use any specific handoff as a hardcoded template here; the skill regenerates per-ship dynamically.

## Pattern provenance

This skill formalizes the ad-hoc handoff prompt convention that emerged in early sprints. Pattern captured because every sprint sub-ship pickup was hitting the same checklist; ad-hoc handoffs drifted in completeness vs the canonical shape.

Documented in:
- `tick-trader-percore-workspace/DOCS/SKILLS_HIERARCHY.md` (Layer 1 entry)
- This file
- Canonical example handoffs: `plans/<sprint-dir>/handoffs/*-handoff.md` — each committed handoff is a real ship's generated output. Reference the most recent multi-session ship handoff (one with WIP-checkpoint commits in its "Ship state across sessions" section) for canonical multi-session output shape.
