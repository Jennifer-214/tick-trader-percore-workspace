---
name: plan-check
description: Audit a multi-plan sprint (master plan + sub-plans) for cohesion before coding. Combines /readiness on each sub-plan + /parity-check for surfaces touched + cross-plan integration matrix verification + dependency-edge validation. Output is a unified GREEN/YELLOW/RED verdict with per-plan + per-conflict findings. Catches the class of bugs where plan A's deliverables silently break plan B's assumptions, before any code is written.
---

# /plan-check — Multi-plan sprint cohesion audit

## What this does

Read a master plan + all its referenced sub-plans. Run the
equivalent of `/readiness` on each sub-plan, then cross-check that
the sub-plans don't silently break each other. Output is a single
unified report: PASS/FAIL per sub-plan + per cross-plan conflict.

**Distinct from `/readiness`:** /readiness audits ONE plan in
isolation. /plan-check audits N plans for COHESION — does plan A's
state of "shipped" make plan B's assumptions still hold?

**Distinct from `/parity-check`:** /parity-check audits CODE for
train↔serve identity. /plan-check audits PLANS for "I-claim-X-and-
the-other-plan-claims-Y; do they agree?"

## Skill composition (how this avoids rewriting /readiness)

**By-reference composition.** /plan-check does NOT spawn nested
/readiness invocations. Instead, the agent reading /plan-check's
spec applies the /readiness checklist (10 baseline + Checks 11-17 +
drift audit + hardening + propagation) to each sub-plan within a
single subagent run.

```
/plan-check (single subagent)
   ├── reads master plan
   ├── extracts N sub-plan paths
   ├── for each sub-plan:
   │     applies /readiness logic INLINE (same checklist;
   │     agent has both skill specs in working context)
   │     produces per-sub-plan readiness verdict
   └── runs cross-plan checks (the unique-to-plan-check work)
```

**Why not spawn nested skill calls?** Each nested /readiness
spawn would create its own subagent with its own context budget.
For a 5-plan sprint, that's 5 nested agents → 5x cost + 5x latency
+ context fragmentation. Inline by-reference keeps it ONE subagent.

**The /readiness skill stays the source of truth** for what a
"ready" plan looks like. /plan-check borrows the checklist; if
/readiness updates (new check, new pattern), /plan-check inherits
without code change because the agent reads both specs.

**Same pattern works for any skill composition in this codebase:**

| Skill | Composes by reference with | Why |
|---|---|---|
| `/parity-check` | `/readiness` (uses verdict vocabulary) | Same vocab, different audit target |
| `/parity-check` | `/ml-audit` (sister skill, distinct scope) | Distinct surfaces; don't duplicate |
| `/plan-check` | `/readiness` (per-plan checklist) | Inline, single subagent |
| `/plan-check` | `/parity-check` (for code surfaces a plan touches) | Optional invocation if a plan's surface needs deep audit |
| `/dust` | `/simplify` (overlapping cleanup ideas) | Distinct triggers; both can run |

**Hierarchy:**

```
                /plan-check  (master-plan cohesion)
                     │
                     ├──> /readiness  (per-plan structure)
                     │       │
                     │       └──> CLAUDE_REVIEW.md (10-item base)
                     │
                     └──> /parity-check  (per-surface code audit)
                             │
                             └──> /ml-audit  (sister; distinct shape)

                /ship  (post-coding ritual; standalone)
                /sync-workspace  (off-machine push; standalone)
                /dust  /simplify  /foxlib-promotion  (cleanup; standalone)
```

**Rule of thumb:** if skill A and skill B share > 50% of their
checklist, A should reference B by name + describe the delta. Do NOT
copy-paste the checklist into A. Drift between specs is a real
maintenance hazard.

**When delegation IS appropriate** (rare): when an explicit
sub-audit is needed mid-flow with a specific narrow scope. E.g.,
/plan-check finds a stamp body conflict → delegates to
`/parity-check stamp` for a targeted code audit. That's a single
nested call with focused scope, justifiable.

**When delegation is inappropriate:** running /readiness 5 times in
a row inside /plan-check. Inline the checklist; one subagent.

## When to use

- Before starting a multi-week sprint with multiple ships
- When opening a master plan that's been static for a while (codebase
  may have drifted; downstream plans may now be invalid)
- After updating ANY sub-plan (catches downstream cascade effects)
- Before declaring a sprint "ready to start" and committing to
  operator-visible delivery dates

## When to skip

- Single sub-plan, no master — use `/readiness` alone
- Hot-fix scope (single file, single PR) — just code it
- Spec/design phase before any sub-plans exist

## Invocation

- `/plan-check` → audits the most recently modified
  `plans/*MASTER*.md`
- `/plan-check <master-path>` → audits the specific master plan

## Pass structure

Spawn an Explore subagent. The subagent:

### 1. Parse the master plan

Extract:
- Sub-plan paths (referenced via `plans/...md` in the master)
- Integration Matrix sections (file ownership, stamp body order,
  cfg additions, dependency edges, test count claims)
- Architectural invariants list
- Dependency graph

If master plan has no Integration Matrix, flag as **STRUCTURAL GAP**:
master can't verify cohesion without one. Recommend adding it before
proceeding.

### 2. Per-sub-plan: lightweight /readiness

For EACH sub-plan, run the full `/readiness` checklist (currently
28+ checks; consult `/readiness` SKILL.md for canonical list).

Report per sub-plan: PASS / FIXED / GAP / DRIFT-RISK / DEFERRED /
ACCEPTED counts + the punch list of must-fix items.

### 3. Cross-plan integration matrix verification

This is the new part — checks the master's Integration Matrix is
internally consistent + reflects current codebase reality.

#### 3.a — Files touched verification

For each file in the matrix:
- Confirm the file exists (or is marked NEW in exactly one plan)
- If multiple plans touch the same file, verify they don't have
  conflicting scopes (e.g., both adding the same field name with
  different types)
- Flag silent ordering hazards: plan A modifies struct shape, plan B
  reads from struct; if A doesn't ship before B, B fails to compile

#### 3.b — Stamp body canonical-order verification

For plans extending the stamp body:
- Each plan adds fields at the END only (canonical-order locked
  invariant)
- If two plans add at the same "position N", flag as ORDER-CONFLICT
- Verify in-process emit order matches bash CLI emit order claims
- HMAC verification: signatures across bash + in-process must agree
  byte-for-byte; if any plan reorders fields, this breaks

#### 3.c — Cfg field name conflict check

- Walk all cfg fields claimed by all plans
- Flag duplicates, near-duplicates, or pattern violations (e.g., one
  plan uses `acknowledge_X`, another uses `enable_X_check` — flag
  for refactor to the dominant pattern)
- Verify cfg fields don't collide with existing engine.cfg.example
  entries

#### 3.d — Architectural invariant preservation

Walk every invariant claimed in the master ("Hot path UNTOUCHED",
"`MODEL_FORMAT_VERSION` only bumps when X", etc.). For each plan,
verify the planned changes don't violate.

If a plan VIOLATES an invariant deliberately (e.g., bumps
MODEL_FORMAT_VERSION as part of a major migration), the master must
explicitly DOCUMENT the violation as deliberate. Otherwise = INVARIANT
BREACH.

#### 3.e — Dependency edge validation

- For each "depends on" claim: verify the predecessor plan is
  scheduled to ship BEFORE the dependent
- Verify the predecessor's deliverables list includes what the
  dependent needs
- Cycle detection: if A→B→C→A, flag CIRCULAR DEPENDENCY

#### 3.f — Test count progression check

- Sum of per-ship test count claims should match cumulative total
- Cross-check against current `./build.sh test` output (if
  invocable)
- Flag if any ship's claim differs from actual by > 10%

#### 3.g — Effort estimate sanity

- Sum of per-ship effort estimates → total sprint duration
- Cross-check against operator's stated time budget (if known)
- Flag if total > 2 weeks (suggest splitting)

### 4. Codebase-vs-plan drift check

For each plan, verify the codebase still matches the plan's
"Existing-dependency claims":
- Every claimed `file.hpp:line N` reference resolves
- Every claimed function exists (use `DOCS/CODE_MAP.md` or grep)
- Every claimed cfg field exists (or is being added by an earlier
  plan in the sprint)

If the codebase has drifted (function renamed, file moved, cfg
removed), flag as DRIFT — plan needs update before coding.

### 5. Output — single unified report

**Save the report to a private file as well as printing it.**
Convention (set 2026-05-06): write the report to
`plans/plan_checks/<YYYY-MM-DD>-<master-plan-stem>.md` where
`master-plan-stem` is the master plan's filename minus its
date prefix and `.md` extension (e.g. `2026-05-06-v5.10-sprint.md`
for `2026-05-02-MASTER-v5.9-to-v5.10.md`). Workspace-symlinked,
gitignored from public repo by virtue of `plans/` being private.

This creates a permanent audit-trail of plan-check verdicts and
their fix recommendations that survives across sessions and is
backed up to the workspace repo automatically. The agent reading
this skill should `mkdir -p plans/plan_checks` before writing.

Also print the same report to stdout so the operator sees it
immediately. Both surfaces (stdout for live triage, on-disk for
forensic reading) matter.

```
# /plan-check report — <master-plan-path> — <date>

## Plan summary
- Master: <path>
- Sub-plans: <N> (paths listed)
- Total estimated effort: <X>h across <Y> ships
- Critical path: <ordered list>
- Status: GREEN / YELLOW / RED

## Per-sub-plan readiness verdicts

| Sub-plan | Verdict | PASS | GAP | DRIFT-RISK | DEFERRED | Notes |
|---|---|---|---|---|---|---|
| v5.9.5h | YELLOW | 14 | 2 | 0 | 1 | Must fix: <items> |
| ...

## Cross-plan integration findings

### Files touched conflicts
- <none, or list>

### Stamp body order conflicts
- <none, or list with proposed resolution>

### Cfg field conflicts
- <none, or list>

### Architectural invariant breaches
- <none, or list with deliberate-vs-accidental flag>

### Dependency edge issues
- <none, or list with cycle / missing-predecessor flags>

### Test count progression mismatches
- Claimed cumulative: <N>
- Actual + planned: <M>
- Drift: <delta>

### Codebase drift
- <none, or list of stale references with fix recommendation>

## Recommendations

### Must fix before coding
- ...

### Worth fixing during coding
- ...

### Acceptable risk (don't block)
- ...

## Verdict: GREEN / YELLOW / RED

GREEN — start sprint with v5.9.5h
YELLOW — fix the must-fix items above first
RED — significant rescope needed; revisit master plan
```

## Heuristics

### Effort multiplier check

Sub-plans tend to underestimate by 30-50% in v5.x sprints. Multiply
the plan's claimed effort by 1.4 for a sanity-check expected
duration. If the operator has a deadline, flag if the multiplied
estimate exceeds the budget.

### Anti-patterns to flag (RED)

- **No master plan but multiple sub-plans** — sprint is uncoordinated;
  REJECT until master is written
- **Sub-plan claims "depends on X" but X isn't in any earlier plan**
  — broken dependency
- **Two plans add the same cfg field with different types/semantics**
  — name collision, will silently break one of them
- **Plan touches stamp body without acknowledging canonical order**
  — HMAC verification breaks at next ship
- **Plan claims "Hot path UNTOUCHED" but lists a hot-path file in
  files-touched** — invariant violation
- **Plan adds a new strict-mode tier without using the established
  3-tier pattern** — operator confusion + integration debt

### Pragmatic-but-ugly patterns to flag (YELLOW)

- **Plan A's deliverable enables Plan B, but A is YELLOW** — B
  silently inherits A's risk; cascade if A regresses
- **Sub-plan claims +N tests; actual current count drifts > 10% from
  cumulative** — test claim is aspirational, not contracted
- **Sub-plan's "Existing-dependency" list cites file:line that the
  current codebase has shifted by > 10 lines** — plan author wrote
  against stale code; refresh before coding
- **Plan effort estimate < 30 min for non-trivial work** — likely
  underscoped; recheck files-touched count
- **Plan ships > 5 unrelated items together** — bundle dilution;
  propose splitting into 2 ships

### Deliberate-vs-accidental invariant violation

When a plan explicitly violates an invariant (e.g., FPN-e2e bumps
`MODEL_FORMAT_VERSION`), the master plan must DOCUMENT this as
deliberate with rationale. Otherwise the violation is silent.
**Format requirement:** master's "Architectural invariants" table
has a "deliberate exception" column listing the violating ship.

If the plan author forgot to document → flag as **DOCUMENTATION
DEBT** (YELLOW).

If the plan author hid the violation in implementation detail →
flag as **INVARIANT BREACH** (RED).

## Map-update suggestions

After plan-check passes:
- If new architectural invariants surface, suggest adding to master's
  invariants table
- If a new cfg pattern emerges (e.g., `acknowledge_X` family),
  suggest updating CLAUDE.md / DOCS/CLAUDE_INVARIANTS.md
- If a sub-plan reveals a CODE_MAP staleness, suggest re-running
  `tools/gen_code_map.sh`
- If multiple plans touch a single file > 5 times in the matrix,
  suggest extracting a helper

## What this skill is NOT

- Not a code reviewer — `/parity-check` covers train-serve identity;
  `/dust` covers cleanup; `/simplify` covers code quality
- Not a project manager — won't track who's doing what, only the
  technical cohesion
- Not predictive — won't tell you if the model will make money,
  just whether the planning is internally consistent
- Not a substitute for /readiness — uses it as a building block

## Background — why this skill exists

The v5.9 ML hardening sprint (2026-05-02) demonstrated the value:
each sub-letter ship had its own `/readiness` pass, but the master
plan accumulated implicit dependencies that weren't verified across
plans. Multiple times during the sprint, an item was "deferred to
v5.10" only to surface again as a downstream dependency for a
v5.9.5x ship.

The natural fix: **plan-level parity discipline.** Master plan
integration matrix tracks cross-plan deliverables; this skill
verifies the matrix matches reality. Same shape as /parity-check
applied to code — make planning parity-tested-by-construction.

Operator (Jenny) named this discipline 2026-05-02:
> "we need a master plan to control and check for integration
> between sub plans as well, to ensure one plan doesnt break the
> next plan, and that theyre all cohesive"
