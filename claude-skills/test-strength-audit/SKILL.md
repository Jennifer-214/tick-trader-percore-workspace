---
description: Anti-regression audit for test weakening. Scans git diffs (working tree, staged, or commit range) for assertion-weakening patterns that hide drift — `==` → `>=` count weakenings without justification, `sr.valid == 1` → weaker format checks, deletion of `check(...)` lines without redundancy/obsolescence justification, empty assertions like `check("foo", true)`. Output is a structured findings report with severity-classified items, NOT actual edits — operator reviews + decides which to triage. Pairs with /test-deletion-justification commit-message convention. Distinct from /dod-audit (pattern application) + /bug-check (recurring bug class scan): /test-strength-audit is specifically about test SPECIFICATION integrity over time.
type: skill
concern: anti-pattern-scan
audit_cadence: per-ship
tags: [audit-methodology, failure-observability]
surface: [test-infrastructure]
sister_skills: [/dod-audit, /bug-check, /post-ship-audit]
loads_dynamically: [DOCS/DESIGN_PHILOSOPHY.md]
---

# /test-strength-audit — Anti-regression scan for test weakening

> **Uniform parameter + preload contract:**
>
> **Required invocation args:**
> - `<diff_range>` — git diff range
>
> **Optional invocation args:**
> - `[focus_keywords...]` — narrow which weakening patterns to emphasize
>
> **Stage 0 DESIGN_PHILOSOPHY preload** (workspace/DOCS/DESIGN_PHILOSOPHY.md):
> - § 11 (Process discipline) — anti-regression discipline; test SPECIFICATION integrity over time
>
> Cite § 11 in finding descriptions.

## What this does

Scans git diffs (working tree, staged, or commit range) for **assertion
weakening patterns** that erode the executable specification of correctness:

- **Count assertion weakenings** — `assert X == N` → `assert X >= N`
  without justification (sometimes legit when the count is monotonically
  growing, but needs explicit "why" or `_smoke_check` suffix)
- **Strict-to-loose substitutions** — `sr.valid == 1` → `sr.format_version == 6`
  (drops the comprehensive validation gate; replaces with a weaker
  surrogate). Concrete bad smell.
- **Deletion of `check(...)` lines without justification** — committed
  test removal must cite either:
  * "covered by `<existing_test_name>`" (redundancy removal — verifiable)
  * "property no longer testable because `<X>`" (deletion-induced obsolescence)
  * "test was wrong; correct invariant is `<new_check>`" (fix)
- **Empty assertions** — `check("foo", true)`, `check("foo", 0 == 0)`,
  `check("foo", x == x)` — pass trivially; provide no signal
- **Tautological assertions** — `check("a == a", a == a)`, `check(b, b)`
- **Comment-only test deletion** — `// check(...)` lines that previously
  asserted; retains intent but disables enforcement

**Does NOT modify code.** Output is a structured report saved to
`plans/plan_checks/test-strength-audit-<YYYY-MM-DD>.md` + printed to
stdout. Findings are severity-classified; operator decides which to
revert / strengthen / explicitly justify.

## Why this exists

Tests are the **executable specification of correctness**. In financial
trading software, a weakened test = silent edge-case loss = real-money
risk in production.

The class-1 anti-pattern: agent or operator faces a failing test, weakens
the assertion until it passes, ships. The "test passes" green light masks
the underlying drift. Tech debt accumulates silently; future audits surface
it as "we used to test X but the test no longer actually checks X."

This skill mechanizes the prevention: every weakening is flagged at PR
time + reviewed against the deletion-justification convention.

Pattern established v5.14.9.D (2026-05-10) after Caramel caught Claude
weakening `sr.valid == 1` → `sr.model_format_version == 6` to chase a
green build. Reverted to redundancy-removal with explicit justification.
Skill is the structural fix.

## Distinct from sister skills

| Skill | Scope | Relationship to /test-strength-audit |
|---|---|---|
| /dod-audit | Pattern application (does code apply DESIGN_SPECS patterns?) | Orthogonal — different concern |
| /bug-check | Codebase scan for recurring bug class instances | Orthogonal — bugs vs test integrity |
| /readiness | Plan-time pre-coding gate | Composes /test-strength-audit at Check 28 (plan-mode + commit-mode invocations) |
| /merge-scan | Computation reuse opportunities | Orthogonal |
| /parity-check | Train↔serve identity | Orthogonal |

## Invocations

- `/test-strength-audit` — scan **working tree diff** (uncommitted changes
  vs HEAD). Highest-value invocation — catches weakenings before they're
  staged.
- `/test-strength-audit staged` — scan **staged diff** (`git diff --cached`).
  Useful right before commit.
- `/test-strength-audit <commit>` — scan a single commit (`git show <commit>`).
  Forensic / audit historical commits.
- `/test-strength-audit <ref>..<ref>` — scan a commit range
  (`git diff <ref>..<ref>`). Sprint-end audit.
- `/test-strength-audit branch <branch>` — scan all unique commits on
  branch vs main. Pre-merge audit.

Plan-mode: `/test-strength-audit plan <plan-file>` — audit plan-claimed
test changes BEFORE coding. Invoked via /readiness Check 28.

## Execution model (per SKILLS_HIERARCHY.md)

**ONE-WAY HIERARCHY. NO LAYER 3.**

```
LAYER 1: ORCHESTRATION
  - Main Claude session OR another orchestrator skill (e.g., /readiness
    Check 28 referencing /test-strength-audit by-reference)
  - Decides WHEN to invoke this skill
  - Spawns ONE Explore subagent

LAYER 2: EXECUTION (this skill runs HERE)
  - The spawned Explore subagent runs git diff + greps using its OWN
    bash/read tools
  - DOES NOT spawn further subagents
  - Returns a single combined report
```

**If you are reading this spec inside an Explore subagent:** YOU ARE the
auditor. Run git diff + grep yourself. Do NOT spawn nested subagents.

## Pass structure

Spawn an Explore subagent. The subagent:

### Step 1 — Diff acquisition

Determine diff source per invocation form:

| Invocation | Command |
|---|---|
| (no arg) | `git diff` (working tree) |
| `staged` | `git diff --cached` |
| `<commit>` | `git show <commit>` |
| `<ref>..<ref>` | `git diff <ref>..<ref>` |
| `branch <name>` | `git diff main..<name>` |
| `plan <file>` | parse the plan file's "Tests" sections + planned `check()` removals/additions |

Filter diff to test files only:
- `tests/**/*.cpp` (canonical test directory)
- `tests/**/*.hpp`
- `*_test.cpp` / `*_test.hpp` patterns
- Skip non-test files (their assertion changes are different concerns)

### Step 2 — Pattern detection (5 categories)

For each diff hunk in test files, scan for:

#### Pattern A: Count assertion weakenings (`==` → `>=`)

Detection regex (in DIFF context):
```
- \s*check\(.*==\s*\d+\s*\)
+ \s*check\(.*>=\s*\d+\s*\)
```

Severity:
- **HIGH** if test name does NOT contain `_smoke_check` suffix
- **LOW** (legitimate) if test name contains `_smoke_check` OR
  registry-COUNT pattern (e.g., `FOREACH_X_COUNT == N` → `>= N`
  when adding registry entries)

Ask: was the assertion count tied to a registry that's monotonically
growing? If yes, `>=` is correct (per /readiness Check 21). If no,
strict `==` was the contract.

#### Pattern B: Strict-to-loose substitutions (sr.valid → format_version)

Detection: removal of strict invariant assertion (e.g., `sr.valid == 1`,
`assert(invariant)`, `STAMP_HAS(...)`) replaced by a weaker surrogate
(e.g., format check, presence-only check).

Heuristic: REMOVED line + ADDED line with overlapping LHS but weaker
RHS. Specifically:
- Removed: `check(..., sr.valid == 1)` / `check(..., is_complete)`
- Added: `check(..., sr.X == N)` for some X != valid

Severity: **HIGH** unless commit message explicitly cites:
- "redundancy removal — covered by `<existing_test_name>`"
- "test was wrong; correct invariant is `<new_check>`"
- "property no longer testable because `<X>`"

#### Pattern C: Test deletion without justification

Detection: `check(...)` line deletion (DIFF removes line; not a rename
or reformat).

Heuristic: count removed `check(` lines per file. For each, scan commit
message for justification:
- "covered by `<test_name>`" — REDUNDANCY (verify the cited test exists
  + actually covers the removed property)
- "property no longer testable" — OBSOLESCENCE (verify deletion-induced)
- "test was wrong" — FIX (verify replacement assertion exists)

Severity:
- **HIGH** if no justification cited in commit
- **MEDIUM** if justification cited but cited test doesn't exist (verify)
- **LOW** if justification verified

#### Pattern D: Empty / tautological assertions

Detection regex:
```
check\(\s*"[^"]*"\s*,\s*true\s*\)
check\(\s*"[^"]*"\s*,\s*1\s*\)
check\(\s*"[^"]*"\s*,\s*\w+\s*==\s*\w+\s*\)  // where LHS == RHS literally
```

Severity:
- **HIGH** for new additions (test was added with no real check)
- **MEDIUM** for surviving instances (pre-existing tech debt)

#### Pattern E: Comment-only test deletion (`// check(...)`)

Detection: line CHANGES from `check(` to `// check(` (i.e., assertion
disabled via comment, not deleted).

Severity: **HIGH** — test is silently disabled; no enforcement; intent
preserved as documentation only. Either delete cleanly OR re-enable.

### Step 3 — Cross-reference + verification

For each finding:

1. Read the surrounding test file context (5 lines before + after)
2. If commit message cites `<test_name>` justification, grep for that
   test name + verify it covers the removed property
3. Cross-ref `_smoke_check` suffix convention — non-suffixed tests are
   STRICT by contract

### Step 4 — TECH_DEBT auto-write

For findings the operator marks DEFER (acceptance of weakening), auto-
append entry to `DOCS/TECH_DEBT.md` per CLAUDE.local.md auto-write
contract. Same discipline as /parity-check + /dod-audit.

Entry shape:
```markdown
### TECH_DEBT-NNN — Test weakening at <file:line>

- **Created:** <date> by /test-strength-audit run on <commit/range>
- **Severity:** HIGH/MEDIUM/LOW
- **Surface:** <test file:line>
- **What was weakened:** <before assertion> → <after assertion>
- **Why deferred:** <operator rationale>
- **Cost estimate:** <hours to strengthen back>
- **Trigger:** <event that should re-prompt strengthening>
- **Status:** OPEN
- **Cross-ref:** <commit hash + this audit report>
```

DO NOT auto-write findings the operator marks ADDRESS-NOW (those land in
current ship's plan). DO NOT auto-write LOW findings unless explicitly
flagged for follow-up.

### Step 5 — Output

Save report to `plans/plan_checks/test-strength-audit-<YYYY-MM-DD>-<scope>.md`
where `<scope>` is:
- `working` for `git diff`
- `staged` for `git diff --cached`
- `<commit_short>` for `git show <commit>`
- `<ref_range>` for `git diff <ref>..<ref>` (e.g., `v5.14.8..HEAD`)
- the plan filename stem for plan-mode

Output format:

```markdown
# /test-strength-audit report — <scope> — <date>

## Summary

| Pattern | HIGH | MEDIUM | LOW | Total |
|---|---|---|---|---|
| A: Count weakenings (== → >=) | 0 | 0 | 2 | 2 |
| B: Strict-to-loose substitutions | 1 | 0 | 0 | 1 |
| C: Test deletion w/o justification | 0 | 0 | 4 | 4 |
| D: Empty / tautological assertions | 0 | 0 | 0 | 0 |
| E: Comment-only test deletion | 0 | 0 | 0 | 0 |

## Findings (severity-ordered)

### HIGH — Strict-to-loose substitution at tests/controller_test.cpp:21680

**Removed:** `check("v5.14.9.D: stamp parses cleanly post-deletion", sr.valid == 1);`
**Added:**   `check("v5.14.9.D: stamp parses without crash post-deletion", sr.model_format_version == 6);`

**Why this is suspicious:** `sr.valid == 1` is the STRICT comprehensive
validation gate (HMAC + format + gap + held_out + ...). `sr.model_format_version == 6`
is a presence check on a single field. The substitution drops the
comprehensive gate.

**Commit message check:** no justification cited (no "covered by", "property no
longer testable", "test was wrong").

**Recommendation:** revert weakening. Either:
1. Investigate why `sr.valid == 1` failed (test setup might be incomplete)
2. Delete the test entirely with redundancy-removal justification (cite
   the existing comprehensive test)
3. Justify the weakening explicitly per Pattern B convention

### MEDIUM — ...

### LOW — ...

## Recommendations

### Must fix before merge / commit
- ...

### Worth fixing during current sprint
- ...

### Defer with TECH_DEBT entry
- ... (auto-written entries listed)

## Verdict: GREEN / YELLOW / RED

GREEN — no HIGH findings; ready to commit/merge
YELLOW — one or more HIGH findings; revert or justify before commit
RED — multiple HIGH findings + pattern of weakening; revisit approach
```

## Severity calibration

- **HIGH** — assertion weakening hides drift. Block ship until
  reverted or explicitly justified per the deletion convention.
- **MEDIUM** — borderline pattern; weakening is mildly justified but
  could be tightened. Address during current sprint.
- **LOW** — legitimate weakening (`_smoke_check` suffix, registry COUNT
  loosening when registry grows, redundancy removal with verified
  citation). No action required.

## Heuristics

### Test naming convention enforcement

Tests with `_smoke_check` suffix are explicitly weak by design.
`/test-strength-audit` skips Pattern A/B/C reports for these. Tests
without the suffix are STRICT by contract.

If operator wants to add a smoke check, name it `<feature>_smoke_check`
to signal intent + suppress weakening alerts on future changes to it.

### Plan-mode emphasis

Plan-mode is high-value invocation. /readiness Check 28 invokes
/test-strength-audit on plan-claimed test changes BEFORE coding. Catches
"plan says we'll change `==` to `>=`" type drift at design time.

### Commit-message scanning

When scanning commits (`<commit>` or range invocation), the skill READS
the commit message body looking for justification patterns:
- "covered by"
- "property no longer testable"
- "test was wrong"
- "_smoke_check" suffix in test name

Justification quality matters: cited test must exist + cited property
must actually be covered. Auditor verifies via grep.

### False-positive mitigation

Some legitimate weakenings:
- Registry COUNT assertions (`FOREACH_X_COUNT == N` → `>= N`) when
  adding entries — `/readiness` Check 21 already canonical
- Test renames (apparent deletion + addition; same assertion preserved)
- Reformatting (no semantic change; whitespace-only diff)
- Adding _smoke_check suffix to existing test (signals intentional
  weakness)

The skill's heuristics filter these via:
- `_smoke_check` suffix detection
- Diff context analysis (paired removal + addition with same content)
- Whitespace-normalized comparison

### Output format reuse

Same structure as /readiness, /trace-deps, /merge-scan, /bug-check,
/dod-audit — report at `plans/plan_checks/test-strength-audit-<YYYY-MM-DD>-<scope>.md`.

## Cross-references

- `DOCS/SKILLS_HIERARCHY.md` — execution model (Layer 1 / Layer 2)
- `DOCS/TECH_DEBT.md` — deferral ledger; /test-strength-audit auto-writes
  per the auto-write contract
- `.claude/skills/readiness/SKILL.md` Check 28 — invokes /test-strength-audit
  by-reference for plan-mode + pre-commit gate
- `.claude/skills/dod-audit/SKILL.md` — sister skill for pattern application
- `.claude/skills/bug-check/SKILL.md` — sister registry-driven skill

## What this skill is NOT

- Not a unit-test runner (assumes existing tests pass)
- Not a code formatter
- Not a security scanner (`/security-review` does that)
- Not a benchmark
- Not predictive ("will weakening this test cause a regression?") —
  purely structural; investigates assertion shapes, not test outcomes

## Future variants

- `/test-strength-audit watch` — Monitor mode that fires on every
  `git commit` via post-commit hook. Catches weakenings at commit
  time before push.
- `/test-strength-audit annotated <commit>` — Embeds findings as
  inline annotations in a fixup-commit ready for git rebase.
- `/test-strength-audit history` — Sprint-end report scanning
  every commit on the current branch since the last release.
- Pattern-doc reuse across projects: future consideration. Test
  weakening is universal CI/CD anti-pattern; templating to other
  workspaces would make the skill broadly useful.

## Versioning

Skill v0.1 (initial) — 5-pattern baseline. Future v0.2+ may add:
- Pattern F: Skip-test markers (`#if 0`, `if (false)`, etc.)
- Pattern G: Test name renaming that obscures coverage scope
- Pattern H: Mock-based weakening (replacing real assertion with
  trivially-passing mock)
