---
description: Scan the codebase for instances of known recurring bug patterns catalogued in DOCS/RECURRING_BUG_PATTERNS.md. Reports per-class CLEAN / KNOWN-N / NEW-N with file:line citations. Registry-driven — adding a new bug class to the doc auto-includes it in the next /bug-check run, no skill spec edit needed. Distinct from /dust (generic cleanup), /dead-code-trace (unreferenced fns), /hft-audit (universal HFT principles), /ml-audit (ML pipeline structure), /trace-deps (plan-time audits): /bug-check is OUR codebase's specific recurring bug history. Output is a structured findings report, NOT actual edits — operator reviews + decides which to triage.
type: skill
concern: anti-pattern-scan
audit_cadence: ad-hoc
tags: [audit-methodology, structural-fix, framework-discipline]
surface: [registry, hot-path, slow-path, oms-drainer, cfg-flow]
sister_skills: [/dust, /dead-code-trace, /hft-audit, /ml-audit, /trace-deps, /dod-audit, /plan-context-sweep]
loads_dynamically: [DOCS/RECURRING_BUG_PATTERNS.md, DOCS/DESIGN_PHILOSOPHY.md, DESIGN_SPECS/meta-disciplines/skill-knowledge-consultation-and-auto-routing.md]
skill_kind: judgment
associated_anti_patterns: [DOCS/RECURRING_BUG_PATTERNS.md, DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md]
associated_decisions: [plans/<active-sprint>/decision-logs/]
associated_postmortems: [plans/<active-sprint>/postmortems/]
associated_ledgers: [DOCS/TECH_DEBT.md, DOCS/PARITY_ISSUES.md]
trigger_heuristics: ["recurring bug-class scan / anti-pattern instances -> suggest /bug-check"]
---

# /bug-check — Scan codebase for known bug class instances

> **Uniform parameter + preload contract:**
>
> **Optional invocation args** (already parameterized — see Invocation section below):
> - `[class_N | surface_<tag>]` — focus on one class or one surface
> - `[plans]` — extend scan to plans/**/*.md (catches stale code samples that would reintroduce just-closed bug classes; see Invocation section "plans" scope)
>
> **Stage 0 — consult institutional knowledge** (per `skill-knowledge-consultation-and-auto-routing.md`): before judging, load this skill's `associated_*` slice (specs / anti-patterns / decisions / postmortems / ledgers) + run the canonical-sister check; if running as a cold Explore/Plan subagent, ensure CLAUDE.md/MEMORY are loaded first. Then the DESIGN_PHILOSOPHY preload:
>
> **DESIGN_PHILOSOPHY preload** (workspace/DOCS/DESIGN_PHILOSOPHY.md):
> - § 3 (Hard Invariants) — H1-H13 are anti-pattern boundaries
> - Family § matched per detected Class N (e.g., Class 23 → § 3 H13 + § 7 Structural-fix; Class 18 → § 7; Class 14 → § 11 Process)
>
> Cite specific § N rows in finding descriptions.

## What this does

Reads `DOCS/RECURRING_BUG_PATTERNS.md` (the canonical record of
recurring bug classes that have hit this codebase), walks every
`## Class N` section, and runs each class's `**Detection:**` grep
against the current HEAD. Reports per-class:

- **CLEAN** — no instances found
- **KNOWN-N** — N instances found, all already in the class's
  `**Known instances:**` list (no triage needed)
- **NEW-N** — N instances found that are NOT in the known list
  (operator triage candidates)

**Does NOT modify code.** Output is a structured report saved to
`plans/plan_checks/bug-check-<YYYY-MM-DD>.md` + printed to stdout.

## Why registry-driven

The skill never hardcodes the class list. It parses the markdown
doc dynamically and dispatches based on what's there. Future
Class 19, 20, ... added to the doc are auto-included in the next
run — no skill spec edit needed.

This applies the structural-fix-preferred rule
(CLAUDE.local.md): adding the next bug class is one markdown edit,
not two-place-edit (markdown + skill spec). Same shape as
FOREACH_FEATURE X-macro (registry IS the source of truth; every
consumer reads from it).

## Distinct from sister skills

| Skill | Scope | Relationship to /bug-check |
|---|---|---|
| /trace-deps | Plan-time audits (does plan claim X exists?) | Class 14-18 Detection delegates here |
| /ml-audit | ML pipeline silent failures | Class 12 Detection delegates here |
| /parity-check | Train↔serve identity | Orthogonal — different audit dimension |
| /dust | Generic cleanup heuristics | No overlap — /dust doesn't know specific bug class history |
| /dead-code-trace | Unreferenced functions | No overlap — opposite direction (Class 1 = enum w/o dispatch; dead-code = dispatch w/o enum) |
| /hft-audit | Universal HFT principles | No overlap — /bug-check is codebase-specific bug history |
| /merge-scan | Reuse opportunities | Orthogonal |
| /patch-planner | Generates fix blueprints | Downstream — /bug-check FINDS, /patch-planner BLUEPRINTS |
| /finding-analyzer | Deep-dive vulnerability orchestrator | Downstream — /bug-check FINDS, /finding-analyzer DEEP-DIVES |

## When to use

- **Sprint kickoff** — verify no NEW instances of known patterns
  have crept in since last run
- **Regression suspicion** — operator notices a symptom that smells
  like a Class N pattern; focused single-class scan confirms
- **Pre-paper-test gate** — fold into pre-deployment checklist
- **Post-major-refactor** — large refactors are when Class N (e.g.
  Class 13 worker-arg use-after-free) instances appear

## When to skip

- Single-file bug fix (no scan needed)
- Doc-only changes
- Recently run (within 24h) and codebase hasn't materially changed
- During paper-testing phase (run BEFORE start, not during)

## Scope (per audit-scope-taxonomy.md)

This skill accepts scope as first positional arg per `DESIGN_SPECS/audit-methodologies/audit-scope-taxonomy.md`:

- `current` (default when no scope specified) — scan recent edits + touched files for known bug class instances
- `wide` — full codebase scan across all Class N entries in RECURRING_BUG_PATTERNS.md; HIGH context cost; recommended quarterly + after new Class N codification
- `scoped <glob>` — file/dir glob
- `module:<name>` — named module per MODULE_MAP.md registry; iterative module-by-module bug-class scans
- `class_N` (legacy invocation) — focused single-class scan
- `surface_<tag>` (legacy invocation) — surface-tag-filtered scan
- `plans` (legacy invocation) — extend scan to plans/**/*.md

**Most appropriate scope shapes for /bug-check:** `current` (during active work), `class_N` (post-new-class-codification sweep), `module:<name>` (iterative module audits), `wide` (quarterly).

## Invocation

- `/bug-check` — default scope `current`
- `/bug-check <scope>` — explicit scope per taxonomy
- `/bug-check class_N` — focused single-class scan (e.g. `/bug-check class_28`) — legacy shape preserved
- `/bug-check surface_<tag>` — surface-tag filter (legacy shape)
- `/bug-check plans` — extend scan to plans/**/*.md (legacy)

**Examples:**
- `/bug-check current` — fast feedback during active coding
- `/bug-check wide` — quarterly + post-new-class-codification full sweep
- `/bug-check module:OMS class_28` — Class 28 scan limited to OMS module
- `/bug-check class_27 module:accounting` — Class 27 scan in accounting module

Surface vocabulary (per RECURRING_BUG_PATTERNS.md):
- `live` — production hot/slow path
- `ml` — ML pipeline (feature pack, inference, scaler, stamp)
- `training` — backtest training matrix, walk-forward, overfit
- `gui` — display panels, GUI worker threads
- `drainer` — OMS drainer, fill consumption
- `boot` — initialization, snapshot load, model load
- `plan-time` — pre-coding plan audits (delegated to /trace-deps)
- `audited-clean` — historically-cleared category (delegated skip)
- `plans` — scan plans/**/*.md for anti-pattern
  CODE SAMPLES that would reintroduce a just-closed bug class. Use after
  structural-fix ship lands (e.g., `/bug-check plans` to verify
  queued sub-plans don't have void*+offset+reinterpret_cast samples). Also
  invoked indirectly by `/plan-context-sweep` orchestrator.

**Scope expansion:** Detection greps run by default against
`CoreFrameworks/`, `ML_Headers/`, `Strategies/`, `DataStream/`, `Backtest/`,
`MemHeaders/`, `FixedPoint/`, `GUI/`, `tests/` (codebase). Adding `plans` to
invocation extends targets to include `plans/**/*.md` (workspace-symlinked).
This catches stale plan code samples that would reintroduce closed bug
classes — e.g., Class 23 (type-erased reinterpret_cast) detection signature
catches `*reinterpret_cast<X*>((char*)Y + offset)` in plan body code blocks
just as it does in real code. Same Detection signature; different scan target.

## Pass structure

Spawn an Explore subagent. The subagent:

### Step 1 — Format-invariant validation

First, verify `DOCS/RECURRING_BUG_PATTERNS.md` is well-formed:

For each `## Class N` section:
- Confirm `**Surface:**` line present
- Confirm `**Detection:**` line present (followed by either an
  executable `\`\`\`bash\n...\n\`\`\`` block OR a delegation marker
  in `[brackets]`)

If any class missing either tag → emit **CRITICAL doc-debt finding**
at top of report; continue scanning the well-formed classes; do
NOT silent-skip.

### Step 2 — Classification

For each class N, classify by Detection content:

- **EXECUTABLE** — Detection contains `\`\`\`bash` block. Run it.
- **DELEGATED** — Detection starts with `[delegates to /SKILL]`.
  Skip; emit one-liner note.
- **N/A** — Detection contains `[audited-clean — N/A]` or similar.
  Skip; emit one-liner note.

For EXECUTABLE classes, parse out the `**Known instances:**` list
file:line citations into a `known_set`.

### Step 3 — Run Detection greps

**Mechanical scanners first (run the tool, don't hand-grep — agents miss instances):**
- **Class 27 (scalar cfg-mirror caches):** `python3 tools/scan_class_27_full.py` — the dedicated full scanner; its output IS the Class-27 candidate list (supersedes the manual grep for this class).
- **Class 44 (cfg-flag orphans):** `python3 tools/scan_class_44_cfg_orphan.py` — the dedicated full scanner; flags operator-settable `MASK_*_CFG_*` flags with NO live sharded reader (read only on the dead `PortfolioController`/TUI/GUI path). Its output IS the Class-44 cfg-flag-orphan candidate list. (The standalone sibling of `check_per_node_registry_integrity.py` Check 11's cfg-MUTATION; the full struct-field produce/consume tracker is TECH_DEBT-175.)

For each EXECUTABLE class:
- Execute the bash block (within reason — sanitize against `rm`,
  destructive commands; if unclear, skip + flag for operator
  review)
- Capture output as candidate file:line list
- Diff against `known_set`:
  - All hits in known_set → CLEAN-OR-KNOWN-N (already documented)
  - Some hits NOT in known_set → NEW-M instances

**Plan scope extension (when `plans` invocation surface present):**
- After running Detection against codebase, ALSO run against `plans/**/*.md`
- Use the same Detection bash block but extend grep targets to plan files
- Plan file matches are SEPARATELY reported as "PLAN-NEW-M" (distinct from
  CODE-NEW-M to make the staleness vs production-bug distinction clear)
- Plan matches typically need amendment notice (light context-correction
  note at top) rather than code fix — different remediation path
- Cross-link plan matches to the plan's amendment-notice block if one
  exists (search plan body for "amendment notice" marker; if present,
  the plan acknowledges the staleness; flag as KNOWN-AMENDED)

### Step 4 — Filter (if invoked with class_N or surface_<tag>)

- `class_N` — only report for that one class
- `surface_<tag>` — only report classes whose `**Surface:**`
  matches; treat `live` as matching `live + drainer + boot` for
  convenience (operator-facing surface vs internal categorization)

### Step 5 — Save + report

Save report to `plans/plan_checks/bug-check-<YYYY-MM-DD>.md`
(`mkdir -p` first). Workspace-symlinked, gitignored from public
repo.

Print to stdout the same content for live operator review.

```markdown
# /bug-check report — <date>

## Summary

| Verdict | Count |
|---|---|
| CLEAN | N |
| KNOWN-only | N |
| NEW instances | N |
| Delegated | N |
| N/A (audited-clean) | N |
| **Doc-debt findings** | N |

## Doc-debt findings (if any)

(if format-invariant validation surfaced any classes missing
**Surface:** or **Detection:**, list here at TOP — must fix
before next /bug-check run)

## Per-class verdicts

### Class 1 — <name>
- Surface: <tag>
- Detection: EXECUTABLE / DELEGATED / N/A
- Verdict: CLEAN / KNOWN-N / NEW-M
- Hits: (file:line list if NEW)
- Triage notes: (if NEW)

(repeat per class)

## Delegation summary

- Class N → /SISTER_SKILL — run separately
  (e.g. Class 12 → /ml-audit; Class 14-18 → /trace-deps)

## Suggested next actions

(operator-facing: which NEW instances warrant triage; which can
be added to **Known instances:** list as accepted/by-design)
```

## Heuristics

### Triage classification of NEW instances

When a Detection grep finds a NEW instance:

1. **TRUE POSITIVE** — actual bug; fix + add to known list with
   ship reference
2. **FALSE POSITIVE** — pattern matches but context is OK (e.g.
   intentional asymmetry, test fixture, documented exception);
   add to known list as accepted with rationale comment
3. **CLASS DRIFT** — pattern caught instances that don't match
   the class's true intent; consider tightening the Detection
   grep OR splitting into a sub-class

### Detection grep safety

If a class's Detection block contains anything beyond grep / awk /
ripgrep / sed (read-only) — refuse to execute. Examples to
refuse:
- `rm`, `mv`, `cp`, `>` redirection to existing files
- `git commit`, `git push`, `git reset`
- Anything writing to disk OR network calls

If unclear, skip the class + emit "DETECTION-UNSAFE: skipped, needs
operator review."

### Cross-class hit deduplication

If a single file:line hits multiple class Detection greps (rare
but possible — e.g. a place that violates Class 1 + Class 2), report
under each class with cross-references. Don't pick one arbitrarily.

## What this skill is NOT

- Not a fixer — finds instances; operator triages + fixes
- Not a generic linter — only tracks OUR codebase's documented
  recurring patterns
- Not a static analyzer — uses grep/awk; doesn't parse C++ ASTs
- Not a substitute for /readiness or /trace-deps — those audit
  PLANS; /bug-check audits CODEBASE
- Not a substitute for /parity-check or /ml-audit — those have
  deeper structural walks; /bug-check is faster + broader but
  shallower per surface
- Not a continuous watcher — invoked explicitly per cadence

## Map-update suggestions (post-audit)

When /bug-check finds NEW instances:
- **RECURRING_BUG_PATTERNS.md** update: add file:line to the
  class's `**Known instances:**` list with ship tag (so future
  /bug-check runs classify as KNOWN-N not NEW)
- **TECH_DEBT.md** update: if NEW instance is deferred (not
  fixed this ship), add ledger entry with class reference +
  trigger for follow-up
- **PARITY_ISSUES.md** update: if NEW instance overlaps with
  parity surface, cross-reference

## Background — why this skill exists

The v5.13.5.B postmortem identified that RECURRING_BUG_PATTERNS.md
had grown to 13 classes (and now 18) but no automated scan
verified the codebase stayed clean against them. Each class's
Detection block existed but had to be manually run by operator
when suspicion arose.

The skill makes the doc load-bearing: every documented pattern
gets actively scanned at sprint kickoff. Catches the class of
silent regressions where "we documented this bug class but
nothing watches for new instances."

Operator (Caramel) framing 2026-05-08:
> "we should mechanize the recurring bug doc — every sprint
> kickoff verifies the codebase stays clean against patterns we
> already learned about."

The registry-driven design means future Class additions are
zero-friction: write the markdown class entry with `**Surface:**`
+ `**Detection:**`, and /bug-check picks it up next run. Same
shape as FOREACH_FEATURE X-macro pattern — one source of truth,
all consumers derive.
