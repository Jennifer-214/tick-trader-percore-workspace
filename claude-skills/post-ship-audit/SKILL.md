---
name: post-ship-audit
description: Post-ship retrospective audit. After a ship commits, runs a 2nd-pass review to catch hand-waves + optimization gaps + discipline drift + STRUCTURAL GAPS where implementation falls short of plan intent or DESIGN_SPECS expectations. Takes ship tag + plan path; identifies files-changed via git diff; runs targeted audits scoped to the ship's surface; compares actual shipped code against plan body claims + referenced DESIGN_SPECS; produces postmortem doc with severity-classified findings + optimization recommendations + triage. Encodes the kind of mid-stream catches an engaged operator makes (e.g., "shouldn't this be branchless?" "did we actually close the class structurally or just patch the symptom?") as systematic post-ship review.
type: skill
concern: post-coding
audit_cadence: per-ship
tags: [audit-methodology, structural-fix, branchless-discipline, pattern-codification]
surface: [registry, hot-path, slow-path, oms-drainer]
sister_skills: [/precoding-audit-gate, /hft-audit, /dod-audit, /bug-check, /accounting-audit, /registry-fit-audit]
loads_dynamically: [DOCS/DESIGN_PHILOSOPHY.md, DESIGN_SPECS/audit-methodologies/audit-scope-taxonomy.md, DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md, DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md, DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md]
---

# /post-ship-audit — Post-ship retrospective + structural-gap audit

> **Stage 0 preload** (workspace/DOCS/DESIGN_PHILOSOPHY.md):
> - § 4 (Latency cost framework) — real-world mispredict cost + branchless decision rules + H20 invariant
> - § 7 (Structural-fix family) — structural-fix-preferred decision framework
> - § 11 (Process discipline) — audit-driven discipline + hand-wave audit
>
> **Stage 0 preload** (workspace/DESIGN_SPECS/):
> - `audit-scope-taxonomy.md` — scope shape used by this skill (module:<sub-ship-surface> typically)
> - `branchless-dispatch-discipline.md` — H20 invariant + decision matrix; Class 28 detection
> - `decision-time-data-binding-pattern.md` — Class 27 detection
> - `pattern-codification-lifecycle.md` — DESIGN_SPEC application stages

## What this does

A SHIP-SPECIFIC 2ND-PASS RETROSPECTIVE. Different from pre-coding audits (which check the plan + design before code). Different from quarterly health audits (which scan the whole codebase). This skill takes a SHIP — a specific commit OR tag OR sub-ship boundary — and asks:

1. **Did the implementation actually achieve the plan's stated goals?** (structural-gap audit)
2. **Did any hand-waves / discipline drift / shortcuts sneak in?** (hand-wave catching)
3. **Are there optimization opportunities the implementation missed?** (2nd-pass discipline application)
4. **Did the implementation apply the DESIGN_SPECS the plan referenced?** (spec-alignment audit)

This is the SYSTEMATIZED version of mid-implementation catches an engaged operator makes (e.g., "wait, isn't this Class 28? shouldn't it be branchless?" "did you actually close the class structurally or just patch the OMS site?" "the plan said use Pattern 2 dispatch table — where is it?"). When implementation cycles are long + operator attention is finite, hand-waves accumulate. This skill is the retrospective sweep that catches them.

**Does NOT modify code.** Output is a structured postmortem report with severity-classified findings + recommended remediation triage.

## When to use

- **After a ship commits** — verify the ship achieved its stated goals; catch any compromises
- **Mid-implementation pause** — when an active ship pauses for handoff, run /post-ship-audit on the partial state to catch issues before resumption
- **Quarterly ship-quality review** — audit recent ships for structural-gap accumulation
- **Pre-sprint-close** — audit all sub-ships in a sprint before umbrella close
- **After a particularly fast or complex ship** — when hand-wave risk is highest (long implementation, many decisions, fatigue)

Distinct from sister skills:

| Skill | Scope | Question answered |
|---|---|---|
| `/precoding-audit-gate` | Plan + pre-coding | "Is the plan ready to code?" |
| `/hft-audit` | Codebase + universal HFT principles | "Are there HFT-invariant violations anywhere?" |
| `/dod-audit` | Pattern application | "Are we applying our DESIGN_SPECS patterns?" |
| `/bug-check` | Known bug classes | "Do existing instances of catalogued bug classes exist?" |
| `/accounting-audit` | Money paths | "Are there silent-correctness hazards in accounting?" |
| `/registry-fit-audit` | Framework selection | "Are existing registries the right tool?" |
| `/post-ship-audit` | **Ship retrospective + structural-gap** | **"Did this ship achieve its plan? What got hand-waved? What's the structural-gap delta?"** |

## Scope (per audit-scope-taxonomy.md)

This skill's scope is implicitly defined by the SHIP — the files changed in the target commit range OR the surface declared in the plan body. Scope arg is the SHIP IDENTIFIER:

- `<ship-tag>` — git tag of the ship (e.g., `v5.15.5.F.4c.3`); audits commits from previous tag to this tag
- `<commit-sha>` — specific commit; audits commits from previous tag to this commit
- `<commit-range>` — explicit range (e.g., `HEAD~5..HEAD`)
- `<plan-path>` — read plan body to extract intended surface; audit corresponding code paths

Recommended: pass BOTH ship-tag AND plan-path together (e.g., `/post-ship-audit v5.15.5.F.4c.3 plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3-...md`) so the skill can compare ACTUAL shipped surface against PLANNED surface.

## Invocation

- `/post-ship-audit <ship-tag>` — audit commits in the ship's range; surface inferred from git diff
- `/post-ship-audit <ship-tag> <plan-path>` — RECOMMENDED — audit + plan-vs-shipped comparison
- `/post-ship-audit <commit-range>` — audit explicit commit range
- `/post-ship-audit current` — audit uncommitted changes + current branch commits since base (use for mid-implementation pauses)

**Examples:**
- `/post-ship-audit <ship-tag>` — audit a specific ship
- `/post-ship-audit <ship-tag> <plan-path>` — full audit + plan alignment
- `/post-ship-audit current plans/...subplan.md` — mid-implementation pause check

## Workflow

Spawn an Explore subagent. The subagent executes:

### 1. Surface identification

- If ship-tag: `git diff <prev-tag>..<tag>` → list of changed files
- If commit-range: `git diff <range>` → list of changed files
- If plan-path: parse plan body for "Files touched" / "Source-audit" / "Files involved" sections → planned surface
- If both: compute INTERSECTION (planned ∩ actual) + DIFFERENCE (planned-but-not-touched + touched-but-not-planned)

The differences are the FIRST signal — files planned but not touched are POTENTIAL STRUCTURAL GAPS; files touched but not planned are SCOPE CREEP or DISCOVERED-WORK.

### 2. Plan claim extraction

If plan_path provided, parse plan body for:
- **Stated goals** ("This ship closes Class 27 structurally" / "Adds OrderPreResolved sub-struct" / "Migrates all 6 OMS consumer sites")
- **Pattern claims** ("Applies decision-time-data-binding-pattern" / "Closes Class 28 via Pattern 2 dispatch table" / "Uses fn pointer table dispatch")
- **Quantitative claims** ("Migrates ~50-100 sites" / "All 4 Section C entries delete" / "Section C zeros at this ship")
- **Discipline claims** ("Branchless dispatch" / "No new scalar cfg-mirror fields" / "HOT/COLD cluster aligned at 320B exactly")

Each claim becomes a verification target.

### 3. Targeted audits (scoped to ship surface)

Run focused audits ONLY on the ship's surface (per audit-scope-taxonomy.md):

- `/hft-audit module:<inferred-from-surface>` — Class 28 + cache layout + branchless opportunities in shipped files
- `/dod-audit module:<surface>` — pattern application gaps
- `/bug-check class_27 module:<surface>` + `/bug-check class_28 module:<surface>` — instances of newly-codified classes
- `/accounting-audit module:<surface>` — if accounting paths touched
- `/registry-fit-audit current` — if any registries added/modified
- `/dependency-chain-trace <claim-symbol>` — for each plan claim about a specific symbol's migration completeness

Each sub-audit's findings are evaluated against the plan's stated goals.

### 4. Structural-gap analysis (the unique value-add)

For each plan claim, verify the IMPLEMENTATION actually achieved it:

| Plan claim type | Verification |
|---|---|
| "Closes Class N structurally" | CI Check N enabled? `/bug-check class_N` returns CLEAN? Anti-pattern grep returns empty? |
| "Applies Pattern X (e.g., 2D dispatch table)" | Grep for the pattern's signature in shipped code. Is it actually present? Is it applied where the plan said? |
| "Migrates N sites" | Count migrated sites vs N claimed. Any leftover unmigrated sites? |
| "Deletes M legacy fields" | Verify fields are GONE from struct definition. CI Check 7 reports 0 exemptions for those names? |
| <plan claims `Section X zeros / cohort migrates / class closes` at ship> | Verify current registry/cohort has expected row count post-migration. Any TRANSITIONAL entries remaining? |
| "Uses branchless dispatch" | Grep for if/else if + switch in shipped code. Each one classified per discipline matrix? |
| "Hot path bytewise-identical" | `tools/calls_graph_diff.sh` confirms hot path unchanged |
| "Layer 5b hash recomputed" | Verify stamp body fixture present + hash constant updated |

For each plan claim, classify:
- ✅ **VERIFIED** — implementation matches plan
- ⚠️ **PARTIAL** — partial achievement (e.g., "migrates 50 sites" → 47 actually migrated; 3 stragglers)
- ❌ **GAP** — implementation falls short of plan (e.g., "closes Class N structurally" → only patches one instance; recurrence still possible)
- 🤔 **UNCLEAR** — plan claim ambiguous; can't verify

### 5. Hand-wave catching

Scan implementation for hand-wave patterns that snuck in:

- Comments containing "branch is fine because" / "predictor handles" / "average cost is acceptable" → Class 28 candidate
- `if (cfg_field)` with body that ignores per-core scope → Class 25/26/27 candidate
- `static const T = cfg.X` patterns → Class 27 fn-local variant
- Pre-resolution that doesn't actually pre-resolve (e.g., assignment in a path that runs AFTER the consumer reads)
- Migration TODOs left in code with no follow-up ship scheduled
- TECH_DEBT entries added for things that should have been fixed structurally per plan claims
- Comments containing "for now" / "temporary" / "MVP" / "will revisit" — flag for explicit defer-doc requirement

### 6. Optimization opportunity scan

Identify places where the implementation worked but could be improved:

- Branchless opportunities missed (Class 28-adjacent)
- Cache layout suboptimal (struct fields not aligned to access pattern)
- DESIGN_SPECS pattern application opportunities (matched to recent codifications)
- Pre-resolution opportunities (Pattern 4 from decision-time-data-binding)
- Cohort sweep candidates (related symbols + behaviors typically migrated together)

### 7. Discipline drift detection

Check for drift from established discipline:

- New scalar cfg-mirror fields on subsystem state (Class 27 prevention)
- New if/else dispatch on runtime enums in SP/HP paths (Class 28 prevention)
- New per-core consumer functions taking `const ControllerConfig<F>*` instead of `const PerCoreCfg<F>*` (Class 25 prevention)
- New global cfg fields that should be per-core (cfg-scope-discipline.md)
- New registries that should be principle + sweep instead (framework-selection criteria)

## Output format

Generate `plans/<sprint>/postmortems/<YYYY-MM-DD>-<ship>-postship-audit.md`:

```markdown
# Post-ship audit: <ship-tag> — <date>

## Plan vs shipped delta

- Planned surface: <N files>
- Actual surface: <M files>
- Planned-but-not-touched: <list>
- Touched-but-not-planned: <list>

## Plan claim verification

### ✅ VERIFIED (count)
- "Closes Class 27 structurally" — Section C 0 entries; CI Check 7 PASS; /bug-check class_27 CLEAN
- ...

### ⚠️ PARTIAL (count)
- "Migrates ~414 test fixture sites" — 408 actually migrated; 6 stragglers in tests/legacy_*.cpp
- ...

### ❌ GAP (count)
- "Closes Class 28 structurally" — Class 28 codified but only OMS HandleFill fixed; 7 other if/else dispatches on runtime enum still exist in ControllerEventLoop + ML_Headers
- ...

### 🤔 UNCLEAR (count)
- "Eliminates static const cache hazards" — only 1 instance found pre-ship; was it the only one? Need /accounting-audit wide for comprehensive
- ...

## Hand-waves caught (severity-classified)

### [HIGH] (count)
- ...

### [MEDIUM] (count)
- ...

### [LOW] (count)
- ...

## Optimization opportunities

- ...

## Discipline drift detected

- ...

## Recommended remediation triage

- **Fix at follow-up sub-ship**: <list>
- **Schedule dedicated audit-driven sweep**: <list>
- **Defer (operator decision)**: <list with rationale>
```

## Cross-skill composition

- **Invoked manually after ship commits** or **at sprint-close**
- **Composes with all audit skills** (fires scoped versions of each)
- **Output feeds `/handoff`** — generated postmortem becomes context for the next session
- **Sister to `/precoding-audit-gate`** — pre-coding gate catches what plan SHOULD do; post-ship audit catches what plan ACTUALLY did

## Anti-patterns to flag (DO NOT DO THIS in your own findings)

- Do **not** mark something as VERIFIED just because the commit message says so — verify mechanically (grep / CI run / pattern match)
- Do **not** mark something as GAP without proposing a remediation path
- Do **not** generate a postmortem with only LOW findings — that suggests the audit didn't dig deep enough; re-scope to module-by-module if so
- Do **not** scope audit to the WHOLE codebase by default — eats context fast + dilutes findings; scope to ship surface (use module:<surface>)
- Do **not** suggest fixes that contradict the locked DESIGN_SPECS (read them first)

## When to use

- **After any non-trivial ship** — ships with >5 files touched OR >2 commits typically benefit from a post-ship audit
- **Mid-implementation pause** — when active work pauses for handoff or compaction risk, run /post-ship-audit on partial state
- **Pre-sprint-close** — audit all sub-ships in the sprint as a quality gate
- **After hand-wave-prone sessions** — long implementations + fatigue raise hand-wave risk; audit catches the accumulated drift
- **Before live-readiness flip** — comprehensive pre-deploy quality check on shipped code

## Cross-references

- `DESIGN_SPECS/audit-methodologies/audit-scope-taxonomy.md` — scope shapes used by this skill
- `DESIGN_SPECS/refactor-patterns/branchless-dispatch-discipline.md` — H20 invariant + Class 28 detection
- `DESIGN_SPECS/refactor-patterns/decision-time-data-binding-pattern.md` — Class 27 detection
- `DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md` — verifies structural-vs-patch claims
- `DESIGN_SPECS/meta-disciplines/pattern-codification-lifecycle.md` — pattern Stage 3 reference application verification
- `DOCS/RECURRING_BUG_PATTERNS.md` — all classes for cross-checking
- `DOCS/DESIGN_PHILOSOPHY.md` § 4 + § 11 — discipline references
- CLAUDE.md Hard Invariants — H1-H14 + H20 verification
- CLAUDE.local.md going-forward rules — discipline drift detection baseline
- All sister audit skills (composed)
