# /trace-deps — dependency-chain audit for new plan code

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

## Procedure

Spawn an Explore subagent. The subagent:

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

### 3. Verify signature compatibility

For each PASS-callee, READ the actual function signature and
compare against what the plan's call site implies:

- **Argument count match?** Plan: `Foo(a, b, c)` → actual:
  `Foo(int a, double b)` → DRIFT (3 vs 2 args)
- **Argument type match?** Plan passes `FPN<F>` → actual takes
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
# Plans should NOT call these post-v5.0+:
grep -l "deprecated\|legacy" CoreFrameworks/PortfolioController.hpp \
    CoreFrameworks/SingleCoreEngine.hpp 2>/dev/null
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

### 6. Save report

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
