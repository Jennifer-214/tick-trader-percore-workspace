---
name: trace-deps
description: /trace-deps — dependency-chain audit for new plan code
type: skill
concern: shape-audit
audit_cadence: per-ship
tags: [audit-methodology, structural-fix, framework-discipline]
surface: [registry, cfg-flow]
sister_skills: [/readiness, /parity-check, /merge-scan, /dod-audit, /precoding-audit-gate, /dependency-chain-trace]
loads_dynamically: [DOCS/DESIGN_PHILOSOPHY.md, DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md, DESIGN_SPECS/meta-disciplines/skill-knowledge-consultation-and-auto-routing.md]
skill_kind: judgment
associated_anti_patterns: [DOCS/RECURRING_BUG_PATTERNS.md, DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md]
associated_decisions: [plans/<active-sprint>/decision-logs/]
associated_postmortems: [plans/<active-sprint>/postmortems/]
associated_ledgers: [DOCS/TECH_DEBT.md, DOCS/PARITY_ISSUES.md]
trigger_heuristics: ["verify plan code deps / chokepoint not bypassed -> suggest /trace-deps"]
---

# /trace-deps — dependency-chain audit for new plan code

> **Uniform parameter + preload contract:**
>
> **Required invocation args:**
> - `<plan_path>` — sub-ship plan to audit
>
> **Optional invocation args:**
> - `[focus_keywords...]` — narrow which dependencies to verify (e.g., "tt::cfg_parse_field" "ControllerConfig_Load")
>
> **Stage 0 — consult institutional knowledge** (per `skill-knowledge-consultation-and-auto-routing.md`): before judging, load this skill's `associated_*` slice (specs / anti-patterns / decisions / postmortems / ledgers) + run the canonical-sister check; if running as a cold Explore/Plan subagent, ensure CLAUDE.md/MEMORY are loaded first. Then the DESIGN_PHILOSOPHY preload:
>
> **DESIGN_PHILOSOPHY preload** (workspace/DOCS/DESIGN_PHILOSOPHY.md):
> - § 7 (Structural-fix family) — verify chokepoint usage; verify X-macro extractor not bypassed
> - § 11 (Process discipline) — boundary-stable refactors over wide cascades
>
> Cite specific § N rows in finding descriptions.

## What this does

Reads a plan file, extracts every NEW function the plan proposes,
traces the dependency chain (what each function will call), and
verifies for each callee:

1. The callee EXISTS in the codebase (not stale claim)
2. The callee's signature matches what the plan assumes
3. The callee is NOT in a deprecated path (e.g., legacy
   PortfolioController for plans that should target sharded)
4. The callee's preconditions are satisfied by the plan's call
   site (e.g., "needs cfg pointer" — plan must show where cfg
   comes from)

Output: per-function dep tree with PASS / GAP / DRIFT verdict per
callee.

**Distinct from `/readiness` Check 19:** Check 19 is "does this
addition already exist?" (NEW vs. REUSE claims). `/trace-deps` is
"if we add this, what does it depend on, and do those dependencies
exist correctly?" Check 19 catches false-NEW + false-REUSE; this
skill catches signature drift + missing transitive dependencies.

**Distinct from `/parity-check` Section L:** Section L runs POST-
coding (greps all callers of a newly-extended struct field).
`/trace-deps` runs PRE-coding (extracts callees from plan PROSE
before code is written).

## When to use

`/readiness` Check 19 invokes this skill automatically when:
- Plan adds ≥3 new functions, OR
- Plan touches ≥5 files, OR
- Plan adds a new function whose dependency chain isn't obvious

Manually: `/trace-deps <plan-path>` for any plan you're worried
about (large refactor, cross-subsystem ship, etc.).

## When to skip

- Trivial single-file plans (Check 19 alone suffices)
- Doc-only changes
- Sub-tag splits of an already-traced master plan

## Execution model (added 2026-05-09 — recursion fix)

**ONE-WAY HIERARCHY. NO LAYER 3.**

```
LAYER 1: ORCHESTRATION
  - Main Claude session (or another orchestrator skill)
  - Decides WHEN to invoke this skill
  - Spawns ONE Explore subagent

LAYER 2: EXECUTION (this skill runs HERE)
  - The spawned Explore subagent reads this spec + applies the
    procedure BELOW directly
  - DOES NOT spawn further subagents
  - May apply OTHER skill checklists (/readiness, /parity-check)
    INLINE by reference
  - Returns a single combined report
```

**If you are reading this spec inside an Explore subagent:** YOU
ARE the trace agent. Walk the dependencies using your read/grep/bash
tools. Do NOT spawn a nested subagent — that creates the recursion
trap that this skill, /readiness, and /parity-check all share absent
this guidance.

See `DOCS/SKILLS_HIERARCHY.md` for the full execution model.

## Procedure

The trace agent (Layer 2 subagent):

### 0. DESIGN_SPECS preload (added 2026-05-14 alongside CLAUDE.local.md condense)

Dependency-chain audits get sharper when the auditor knows what
structural-fix patterns and recurring-bug classes the plan should
have applied. Load these BEFORE walking the dep tree, so Step 6
(structural-fix-preferred call-sequence enumeration) can cite
specific pattern rules:

- `tick-trader-percore-workspace/DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md`
  — when "same pattern at multiple sites drifted apart" → registry/
  helper-extract with compile-time enforcement, not direct patch
- `tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md`
  — Class 19 (hardcoded instance names in applicability gating); plan
  should use category masks not enum-name comparisons
- `tick-trader-percore-workspace/DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md`
  — FOREACH_* registry shape; mirror-incomplete additions caught by
  Step 6 should propose registry consolidation
- `DOCS/RECURRING_BUG_PATTERNS.md` Classes 13-21 — bug class registry;
  cross-ref Step 6 findings against each known class

For each loaded doc, hold its body in context. Step 6 findings cite
DESIGN_SPECS filename + class number when proposing structural fixes.

### 1. Parse the plan

Extract from plan body:
- **NEW functions** — every "we'll add `Foo()`" / "create
  `Bar_Baz()`" / "new helper `Qux()`"
- **NEW structs** with fields that imply new code paths
- **Implementation steps** that prose-describe call sequences
  (e.g., "call X then Y then Z")

For each NEW function, build a candidate dep list from the prose:
- Every other function name mentioned in the same step
- Every cfg field referenced
- Every struct field referenced
- Every existing function the plan claims to call

### 2. Verify each callee exists

For each candidate callee `Foo`:

```bash
# Function declaration
grep -rn "^.*\b<Foo>\s*(" --include="*.hpp" --include="*.cpp" .

# Function definition (template helper)
grep -rn "inline.*<Foo>\b\|template.*<Foo>\b" \
    --include="*.hpp" .
```

Verdict per callee:
- **PASS — exists at file:line, signature matches plan**
- **GAP — does not exist** (plan claim is stale; reject or update)
- **DRIFT — exists but signature differs from plan**

#### 2a. Filename ≠ type-name confusion check (v5.14.10+)

**Recurring trap (v5.14.10 Surprise 2):** when a file defines MULTIPLE types or when type names diverge from filenames, plans often cite "TypeName.hpp" when the actual file is "DifferentName.hpp" containing the type. Specifically grep file paths AND type names AS SEPARATE QUERIES:

```bash
# (A) Does a file with the cited NAME exist?
find . -name '<TypeName>.hpp' -type f
# If 0 hits → likely filename ≠ type-name confusion; check (B)

# (B) Where is the type actually DEFINED?
rg -n "^\s*struct\s+<TypeName>\b|^\s*class\s+<TypeName>\b|^\s*template\s+.*\s+struct\s+<TypeName>\b" --glob '*.hpp'
# This finds the file containing the type declaration regardless of filename.
```

If (A) returns 0 hits but (B) returns hits, the plan has a filename ≠ type-name confusion. Update the plan to cite the ACTUAL file path (from B) for the cited type.

**Worked example (v5.14.10 plan):**
- Plan claimed `ML_Headers/EnsembleModelZoo.hpp` cited 8+ times
- (A) `find . -name 'EnsembleModelZoo.hpp'` → 0 hits
- (B) `rg -n "^\s*struct\s+EnsembleModelZoo\b" --glob '*.hpp'` → `ML_Headers/CoreModelZoo.hpp:820`
- Resolution: plan cites WRONG file; correct is `CoreModelZoo.hpp` (which defines BOTH `CoreModelZoo<F>` AND `EnsembleModelZoo<F>` structs in one file).

This codebase has several known filename ≠ type-name pairs — when in doubt, query (A) + (B) as separate sub-checks before declaring "PASS / GAP / DRIFT".

### 3. Verify signature compatibility

For each PASS-callee, READ the actual function signature and
compare against what the plan's call site implies:

- **Argument count match?** Plan: `Foo(a, b, c)` → actual:
  `Foo(int a, double b)` → DRIFT (3 vs 2 args)
- **Argument type match?** Plan passes `FPN_Binary<F>` → actual takes
  `double` → DRIFT (need conversion at call site; plan should
  call this out)
- **Return type match?** Plan assigns to int → actual returns
  bool → DRIFT
- **Default args present?** New code passes 3 args; actual has
  2 required + 5 default — PASS (defaults handle the gap)

### 4. Check for deprecated-path traps

Cross-reference the callee location against the
"deprecated / legacy" file list:

```bash
# Plans should NOT call deprecated paths. Scan for deprecated-tagged
# files via header docstring comments OR consult current deprecated-path
# list (e.g., per CLAUDE.md `Legacy single_core LIVE is deprecated` doc):
grep -rln "deprecated\|legacy" --include='*.hpp' CoreFrameworks/ 2>/dev/null
```

If a plan call resolves to a deprecated file → flag DRIFT-RISK.
The function may exist but its call path may be unmaintained.

### 5. Trace transitive dependencies (1 level)

For each PASS-callee, READ its body briefly (head -30 lines) and
list THAT function's callees. If any TRANSITIVE callee:
- Is in a deprecated path → DRIFT-RISK
- Has a preconditions-not-met flag (e.g., requires `cfg.X` but
  the plan's call site doesn't show cfg propagation) → GAP

Don't recurse beyond 1 level (combinatorial explosion;
diminishing returns).

**For a token/identifier RENAME plan** (Core→Node-style): the consumer
enumeration across ALL file types — incl. the compiler-blind apparatus
(`tools/`/`build.sh`/`.githooks/`) a plan-time grep forgets — is
mechanized by `tools/cascade.py rename` (TD-175a;
`rename-cascade-enumeration-tooling.md`). Run it + paste the worklist
(`feedback_paste_tool_output_dont_summarize`); the compiler is the
code-token oracle, cascade covers the surface it can't see.

### 6. Mirror data-flow audit (added 2026-05-09 — Class 18 prevention)

If the plan body contains keywords:
- "mirror"
- "duplicate this for X"
- "parallel to X"
- "same pattern as X"
- "follows X's structure"

Then run a SEPARATE audit on the mirrored source code's READ surface.
Standard symbol-existence audit (Steps 2-3) verifies CALLEES; this
step verifies DATA SOURCES.

**Procedure:**

1. **Identify the mirrored source range.** Plan must cite file:line
   range of the source code being mirrored (e.g., "v5.14.0 buy-side
   ridge_within_horizon block at StrategyParameters.hpp:891-947").
   If not cited explicitly, GAP — plan must add the citation.

2. **Walk the source range for struct field reads.** Grep for
   patterns matching `obj->field` or `obj.field`:

```bash
# Extract source range, find all struct member accesses:
sed -n '<start>,<end>p' source.hpp | \
    grep -oE '[a-zA-Z_][a-zA-Z0-9_]*->[a-zA-Z_][a-zA-Z0-9_]*' | \
    sort -u
# Also check `.` accesses on local references:
sed -n '<start>,<end>p' source.hpp | \
    grep -oE '[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*' | \
    sort -u
```

3. **For each (obj, field) read pair, identify the obj's struct type.**
   At the source call site, what type is `obj`? Usually a function
   parameter or a local variable; read the function signature or
   the local declaration to identify the struct.

4. **For each (struct, field) pair, verify the Y-side equivalent.**
   The plan claims the mirrored block runs in a NEW context (Y).
   Does the Y-side caller scope have the same (or parallel-named)
   struct + field available?

   Example: buy-side reads `ezoo->reward_ring`. For exit-side mirror,
   the Y-side caller scope has `ezoo_ex` of the same EnsembleModelZoo
   type. Does EnsembleModelZoo have a parallel `exit_reward_ring`
   field? If not → GAP.

5. **For each missing data source, flag RED.** Plan must EITHER:
   - Add the missing data source as a NEW item in the plan
     (e.g., "add exit_reward_ring field to EnsembleModelZoo"), OR
   - Document an explicit data-flow gap rationale (e.g., "exit
     side will use uniform fallback because the source ring isn't
     yet available; full Ridge deferred to vN+M")

6. **Output:** add a "Mirror data-flow audit" section to the trace
   report. List:
   - Source code range mirrored
   - Every (obj, field) read inventoried
   - Per read: PASS (Y-side has equivalent) / GAP (Y-side missing) /
     DOCUMENTED-RISK (plan acknowledges + handles)

**v5.14.2.E.1 strengthening (Class 18 → CALL-SEQUENCE enumeration):**

Steps 1-6 above audit DATA-FLOW INPUTS (struct field reads). Equally
critical for mirrors is auditing the CALL SEQUENCE — which functions
the mirrored body invokes. PARITY-009/010/011/012 (4 separate Class 18
findings closed by v5.14.2.E.1) all stemmed from /trace-deps Step 6
auditing inputs but missing the call sequence.

**Procedure for call-sequence audit (run alongside Steps 1-6):**

A. **Walk the source range for function CALLS.** Grep for patterns
   matching identifier-then-paren (function invocations):

```bash
sed -n '<start>,<end>p' source.hpp | \
    grep -oE '[A-Z][a-zA-Z0-9_]+\s*\(' | \
    sort -u
# Also lower-case helpers:
sed -n '<start>,<end>p' source.hpp | \
    grep -oE '[a-z][a-zA-Z0-9_]+\s*\(' | \
    sort -u
```

B. **For each call, verify the Y-side mirror invokes it OR has
   explicit reason not to.** Plan must either:
   - Show the mirror's pseudocode includes the equivalent call
   - Document explicitly why the mirror doesn't need it
     (e.g., "boot does Free+null on validate-fail; hot-swap does
     log-only — preserved for v5.10.0c semantics")

C. **For ≥3 calls in mirrored sequence + caller in different file:**
   recommend X-macro registry / helper extraction (CLAUDE.md item 19).
   Don't duplicate; extract. Mirror becomes a single helper call.

D. **Output:** add "Call-sequence audit" subsection to the Mirror
   report. List every call in source; per call: MIRROR-PRESENT /
   MIRROR-MISSING-WITH-RATIONALE / MIRROR-MISSING-GAP.

**Anti-pattern caught (v5.14.2.E.1 2026-05-09):** v5.14.2.A
EnsembleHotSwap.hpp mirrored boot ensemble setup but enumerated only
INPUTS (cfg fields read), not CALLS. Missed 6 of 8 boot post-load
calls (PARITY-009 sub-gaps .C-.F). Same pre-coding /trace-deps audit
that ran Step 6 caught only 1 of those 6. Strengthening Step 6 with
call-sequence audit catches the pattern at audit time.

**Why this step exists:** standard symbol-existence audit (Steps
2-3) verifies that NAMED CALLABLES (functions, struct types) exist
on both sides. It does NOT verify DATA-FLOW PRECONDITIONS —
specifically, the upstream reads that the mirrored code performs.
Class 18 (RECURRING_BUG_PATTERNS.md) is the canonical instance:
v5.14.1.E.B's exit-side Ridge mirror would have read uninitialized
data because exit_reward_ring didn't exist; audit GREEN'd because
all named symbols were present.

### 7. Save report

Write to `plans/plan_checks/trace-deps-<YYYY-MM-DD>-<plan-stem>.md`.
Print summary to stdout.

```
# /trace-deps report — <plan-path> — <date>

## Summary
- NEW functions analyzed: N
- Callees verified: M
- PASS: A
- GAP: B  (BLOCKING — plan must update)
- DRIFT: C (review; may need adapter code)
- DRIFT-RISK: D (deprecated-path callees)

## Per-function dep tree

### Foo()  [NEW; plan v5.X.Y]
  Plan call site: <plan file:line excerpt>
  Callees:
    - Bar()  PASS at CoreFrameworks/X.hpp:123 — sig matches
    - Baz()  GAP — does not exist; near-synonym BazV2 at Y.hpp:456
    - Qux()  DRIFT — sig (int, double) but plan assumes (FPN<F>)

### ...

## Recommendations
- Plan must update line N to use BazV2 instead of Baz
- Plan must show conversion FPN<F> → double at Qux call site
- ...
```

## Verdict

- **GREEN** — all callees PASS or DRIFT-with-adapter
- **YELLOW** — DRIFT findings need plan update but not blocking
- **RED** — GAP findings; plan must update before ship

## TYPE-SENSITIVE consumer classification (added 2026-05-18 — meta-discipline M4 / Pillar B8)

When enumerating consumer sites for a struct-gen migration or type-unification migration, classify each call site by TYPE-SENSITIVITY. Plain consumer enumeration (Class 14 prevention) is necessary but not sufficient — type-change cascades (Pillar B1 from `implementation-layer-blindspot-taxonomy.md`) require knowing WHICH sites would break compile on a struct field type shift.

**Per-site classification:**

| Class | Definition | Action on type change |
|---|---|---|
| **TYPE-SENSITIVE-READ** | Site compares field against literal of OLD type (e.g., `sr.ridge_lambda == 0.005` against `double`) | Wrap with conversion OR add cross-type operator |
| **TYPE-SENSITIVE-WRITE** | Site assigns field to OR from a variable of OLD type (e.g., `handle->ridge_lambda = double_var`) | Conversion OR field-type alignment |
| **TYPE-AGNOSTIC** | Site passes through; copies value-by-value; doesn't compare or write by-type | No action |

**Procedure (per migration crossing 2+ registries OR involving STORAGE_T column adoption):**

1. After standard consumer enumeration (Class 14 prevention), revisit each cited site
2. For each: classify per the table above
3. Emit per-file site count split by class: TYPE-SENSITIVE-READ / TYPE-SENSITIVE-WRITE / TYPE-AGNOSTIC
4. Compute total TYPE-SENSITIVE = READ + WRITE
5. Effort estimate: ~5 min per TYPE-SENSITIVE site for conversion/operator-add; TYPE-AGNOSTIC sites are mechanical replace_all

**Verdict:**
- TOTAL TYPE-SENSITIVE ≥30 → LOAD-BEARING-LOUD (consider pre-coding type-diff to surface ALL sites at once)
- TOTAL TYPE-SENSITIVE <30 → GUARDED-BY-BUILD (compile failures surface remaining incrementally)

**Cross-references:**
- `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` § B1 + § B8
- `DESIGN_PHILOSOPHY.md` § 11.5 meta-discipline M4
- `claude-skills/blindspot-scan/SKILL.md` Pillar B1 + B8

## Cross-references

- `/readiness` Check 19 — calls this skill for deep dives
- `/parity-check` Section L — post-coding sister; greps all
  callers of newly-extended fields
- `DOCS/RECURRING_BUG_PATTERNS.md` Class 13 — worker-arg use-after-
  free pattern that this skill would catch at plan-time

## What this skill is NOT

- Not a code reviewer — `/dust` covers that
- Not a parity audit — `/parity-check` covers that post-coding
- Not a merge-scan — `/merge-scan` covers reuse opportunities
- Not a ship gate by itself — it's a `/readiness` Check 19
  sub-procedure; `/readiness` is the ship gate

## Background — why this exists

v5.13.5.A + v5.13.5.B were both "extend existing struct without
updating downstream callers" failures. Caught by `/parity-check`
Section L POST-coding. Operator 2026-05-08: "we should update the
plan check or readiness skill to check for existing code and trace
through what a function will need."

Strengthened Check 19 + this new skill catch the same class
PRE-coding, before any time is spent writing the bug.

## Effort budget

- Trivial plan (1-3 NEW fns, all callees in same file): ~2 min
- Medium plan (5-10 NEW fns, cross-file): ~5-8 min
- Large plan (>10 NEW fns, multi-subsystem): ~10-15 min

If the agent hits a 15-min cap, save partial report + flag
"PARTIAL — plan too large for single audit; recommend splitting"
and surface to operator.
