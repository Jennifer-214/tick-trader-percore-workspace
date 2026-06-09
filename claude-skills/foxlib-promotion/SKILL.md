---
name: foxlib-promotion
description: Identify generic primitives in tick-trader-percore that are candidates for promotion to FoxLIB (the public reusable library at ~/code/FoxLIB). Scans recent additions, filters by genericity heuristics, cross-checks against FoxLIB's existing headers to avoid duplication, and outputs a punch-list of promotion candidates with rationale.
type: skill
concern: workflow
audit_cadence: ad-hoc
tags: [doc-discipline, structural-fix]
surface: []
sister_skills: [/merge-scan, /dod-audit]
loads_dynamically: [DESIGN_SPECS/meta-disciplines/skill-knowledge-consultation-and-auto-routing.md]
skill_kind: judgment
associated_anti_patterns: [DOCS/RECURRING_BUG_PATTERNS.md, DESIGN_SPECS/meta-disciplines/meta-anti-pattern-index.md]
associated_decisions: [plans/<active-sprint>/decision-logs/]
associated_postmortems: [plans/<active-sprint>/postmortems/]
associated_ledgers: [DOCS/TECH_DEBT.md, DOCS/PARITY_ISSUES.md]
trigger_heuristics: ["generic primitive promotion to FoxLIB candidates -> suggest /foxlib-promotion"]
---

# /foxlib-promotion — find what should land in FoxLIB next

> **Stage 0 — consult institutional knowledge** (per `skill-knowledge-consultation-and-auto-routing.md`): before judging, load this skill's `associated_*` slice (specs / anti-patterns / decisions / postmortems / ledgers) + run the canonical-sister check; if running as a cold Explore/Plan subagent, ensure CLAUDE.md/MEMORY are loaded first.

## What this does

FoxLIB at `/home/caramel/code/FoxLIB/` is the public, reusable
extraction of generic primitives from this engine. It currently holds
FPN_Binary, regression, RollingStats, BuddyAllocator, SPSC ring, WebSocket
helper, ConfidenceScorer, etc. — code with no project-specific
includes or domain-specific names.

Every few versions, generic primitives get written here that should
land in FoxLIB but get forgotten. The last sync tag's commit message
references the engine-version it synced from (auto-detected via
procedure below). Anything generic written since that sync point
is potentially un-promoted.

This skill walks recent additions, scores genericity, deduplicates
against existing FoxLIB headers, and produces a list of promotion
candidates each with: file, rationale, suggested FoxLIB path.

## Invocation

- `/foxlib-promotion` — scan from the last FoxLIB sync tag forward
- `/foxlib-promotion <since>` — scan since `<since>` (a tag, branch,
  or commit ref)

## Procedure

```bash
# 1. Find the last FoxLIB sync point
LAST_SYNC=$(cd /home/caramel/code/FoxLIB && \
  git log --oneline | grep -m1 "sync from tick-trader-percore" | \
  awk '{for (i=1; i<=NF; i++) if ($i ~ /^@/) print substr($i,2)}')
# Falls back to last available tag if grep miss; ask user if unclear

# 2. List files added or significantly modified since LAST_SYNC
cd /home/caramel/code/tick-trader-percore
git diff --name-only "$LAST_SYNC..HEAD" | \
  grep -E "^(MemHeaders|FixedPoint|ML_Headers|DataStream)/.*\.hpp$"

# 3. List existing FoxLIB headers
ls /home/caramel/code/FoxLIB/include/foxlib/*.hpp | \
  xargs -n1 basename | sed 's/\.hpp$//'
```

For each candidate file, evaluate against the genericity heuristic:

### Genericity heuristic

A file is a strong promotion candidate if it satisfies ALL of:

1. **No project-specific includes.** No `#include "../CoreFrameworks/..."`
   / `"../Strategies/..."` / `"../Backtest/..."` / domain-specific
   headers. Generic primitives only depend on stdlib + each other +
   well-known third-party (openssl, etc.).

2. **No domain-specific names in the public API.** Function names like
   `Binance_*`, `OMS_*`, `ExecutionCore_*`, `Strategy_*` mean it's
   tightly bound to this engine. Names like `RollingStats_*`,
   `FPN_Binary_*`, `BuddyAllocator_*` are generic.

3. **No hardcoded domain constants.** A file with `MAX_CORES = 16` or
   `BTCUSDT` in it is engine-specific. Generic constants like buffer
   sizes are fine.

4. **Self-contained tests would make sense.** If the only way to test
   the primitive is through engine state, it's not generic enough.

### Soft signals (worth promoting even if not perfect)

- Header is small and tight (< 200 lines)
- Header has its own focused purpose (one concept, not a grab bag)
- Header would have value to someone outside this engine context
- Header is something you'd want to use in a future trading project

### Heuristic anti-patterns (NOT a candidate)

- Files in `CoreFrameworks/` (engine-specific by design)
- Files in `Strategies/` (domain-specific by design)
- Files in `GUI/` (Dear ImGui app code, not a library primitive)
- Files in `Backtest/` (engine-specific results structures)
- Files importing `EngineSharded.hpp`, `ControllerConfig.hpp`,
  `OrderManager.hpp`, etc.

## Cross-check against FoxLIB

For each candidate, check if FoxLIB already has something covering
the same concept. Naming convention there is lowercase + snake_case
(e.g., `rolling_stats.hpp` not `RollingStats.hpp`). A candidate's
content might already be covered by a different filename.

```bash
# Quick concept scan
for concept in HmacSha256 RunHistory FlowFeatures ROR; do
    found=$(grep -ril "$concept" /home/caramel/code/FoxLIB/include/foxlib/ 2>/dev/null)
    [[ -z "$found" ]] && echo "NEW: $concept" || echo "EXISTS: $concept → $found"
done
```

If a concept exists in FoxLIB but the percore version has new
features (e.g., a new method, a bug fix), suggest a back-port commit
rather than a new file.

## Output format

```
# /foxlib-promotion report — <date>

## Sync status
- Last FoxLIB sync: <tag/commit> (<date>)
- Commits since:   <N>
- Files in scope:  <M>

## Strong candidates (promote)

### <file path>
- **Why**: one-line reason it's generic
- **FoxLIB path**: include/foxlib/<lowercase_snake>.hpp
- **Notes**: any caveats (e.g., needs openssl link, depends on X)

(repeat per candidate)

## Weak candidates (worth a look)

(files that are partially generic — maybe extract a portion?)

## Back-port suggestions

(concepts already in FoxLIB but with new features in percore)

## Skip — engine-specific

(files in scope but clearly not promotion candidates;
 brief one-liner per to confirm the skill saw them)

## Recommended next steps

1. Promote <X> via cp + rename to lowercase + adjust includes
2. Cherry-pick <Y> commit onto FoxLIB main
3. Tag FoxLIB v0.<N+1> after promotion
```

## When to use

- After shipping a few versions in tick-trader-percore (v4.X+1, etc.)
- Before tagging a new FoxLIB release
- When considering whether to start a new feature in FoxLIB directly
  vs. percore-first (this skill tells you what's already accumulated)

## When to skip

- Right after a FoxLIB sync (nothing to promote)
- During active feature work in percore (let primitives stabilize
  before promoting; promote when they've been used in 2-3 places
  and the API has settled)

## What this skill is NOT

- Not an automatic promoter — it produces a punch list, the user
  reviews and acts
- Not a back-port automator — for that, use `git cherry-pick` against
  the FoxLIB repo manually
- Not a license/legal reviewer — both repos are user's, but if FoxLIB
  has different licensing terms, the user must check before promoting
