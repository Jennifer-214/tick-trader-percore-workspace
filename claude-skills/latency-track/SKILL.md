---
name: latency-track
description: Audit recent edits / pending commits for changes to latency-critical code (hot path, producer fan_out, slow-path body). For each touched site, emit a draft HOT_PATH_CHANGELOG.md entry with cost estimate, branchless analysis, and optimization notes. Output is review-and-paste, NOT actual edits to the changelog. Pairs with CLAUDE.md item 16 (reuse-audit) and the /merge-scan codebase sweep — /merge-scan looks for SHARING opportunities; /latency-track tracks ADDITIONS.
type: skill
concern: post-coding
audit_cadence: per-ship
tags: [latency-discipline, ledger-discipline]
surface: [hot-path, slow-path, producer, oms-drainer]
sister_skills: [/merge-scan, /hft-audit, /ship]
loads_dynamically: [DOCS/DESIGN_PHILOSOPHY.md]
---

# /latency-track — Latency-additions audit + draft changelog entries

> **Uniform parameter + preload contract:**
>
> **Required invocation args:**
> - `<diff_range>` — git diff range
>
> **Optional invocation args:**
> - `[focus_keywords...]` — narrow which paths to emphasize
>
> **Stage 0 DESIGN_PHILOSOPHY preload** (workspace/DOCS/DESIGN_PHILOSOPHY.md):
> - § 4 (Latency cost framework) — cycles vs cache vs branch costs; ROI table; reuse-audit principle (CLAUDE.md item 16); latency-additions tracked (item 17)
>
> Cite § 4 cost-table values in HOT_PATH_CHANGELOG drafts.

## What this does

Scans recent edits / pending commits for changes to latency-critical
code paths and emits draft entries for `DOCS/HOT_PATH_CHANGELOG.md`.
Each entry pins WHERE the change happened, ESTIMATED cost in ns,
whether it's branchless, cache-line impact, and an optimization
note for future revisit.

**Does NOT modify the changelog.** Output is a draft block the
operator reviews + pastes into `HOT_PATH_CHANGELOG.md` themselves.

## Why this exists

Operator (Jenny) explicitly dislikes adding latency to hot paths.
The CLAUDE.md item 16 reuse-audit principle catches OPPORTUNITIES
for sharing existing computation; this skill catches ADDITIONS that
slipped through and ensures they're visible in the changelog so
future optimization passes have a punch list.

The v5.12.1.B.3 staleness gate added ~1-2 ns to the hot path for
the safety value of detecting slow-path stalls. That's a deliberate
trade-off, not a regression — but it MUST be documented so next
year's optimization sprint can revisit (template elision, runtime
predicate cache, or slow-path liveness flag).

## Distinct from sister skills

| Skill | What it catches |
|---|---|
| `/merge-scan` | Sharing opportunities — "two consumers, one read" |
| `/parity-check` | Train↔serve identity drift |
| `/dust` | Dead code, rotting comments, copy-paste |
| `/simplify` | Code review + auto-fix |
| **`/latency-track`** | **NEW work that adds latency on a critical path** |

## When to use

- After a hot-path-touching commit lands (verify HOT_PATH_CHANGELOG entry exists)
- Before merging a feature branch back to main (final tracking pass)
- After a sprint closes (sweep across the whole sprint's commits)
- Before any v5.X release tag (ensure all latency-additions in the
  release are documented)

## When to skip

- Pure refactor commits with measured 0-impact (no new branches, no
  new struct fields, no new atomic ops)
- Cleanup-only commits (/dust scope)
- Test-only commits (no shipped code)
- Doc-only commits

## Invocation

- `/latency-track` — audits unstaged + staged changes (working tree)
- `/latency-track HEAD` — audits the most recent commit
- `/latency-track HEAD~5..HEAD` — audits a range of recent commits
- `/latency-track <branch>` — audits a feature branch vs main
- `/latency-track <commit-sha>` — audits a specific commit

## Pass structure

Spawn an Explore subagent with the audit instructions. The subagent:

### 1. Identify the diff scope

Resolve the operator's arg into a git diff:
- No arg: `git diff HEAD` (working tree)
- Single ref: `git show <ref>`
- Range: `git diff <range>`
- Branch: `git diff main..<branch>`

### 2. Classify changed files

For each changed file, classify by latency tier:

**Hot path (per-tick, target p99 ≤ 500 ns):**
- Files containing functions tagged `// HOT PATH` or appearing in the
  inlined dispatch chain (e.g., `ExecutionCore_Tick → BG/SG_Evaluate`).
  Consult `DOCS/HOT_PATH_CHANGELOG.md` cadence-tier classification for
  the current canonical set.

**Producer fan_out (per-WS-tick, ~50-1000/sec):**
- Files containing producer fan_out body + parser callbacks. Consult
  `DOCS/HOT_PATH_CHANGELOG.md` cadence tier.

**Slow path (per poll cycle, target p99 ≤ 100 μs):**
- Files containing slow-path functions per cadence: rebuild/exit/ratchet
  helpers, strategy build-parameters bodies, rolling/flow push, regime
  compute, feature pack, confidence scorer, bandit, model predict.
  Consult `DOCS/CODE_MAP.md` slow-path section + `DOCS/HOT_PATH_CHANGELOG.md`
  cadence tier for the current canonical set.

**Cold path (init/shutdown/once-per-run, no budget):**
- Init functions, snapshot persist/load, GUI panels (rendered ≤ 60 Hz)

Files that DON'T match any tier are flagged informational; not in scope.

### 3. Per-touched-tier-file: line-level analysis

For each hot-path or producer or slow-path file in the diff, walk
the diff hunks and classify each ADDED line:

**Latency-impacting additions** (require changelog entry):
- New atomic operation (`std::atomic` load/store/CAS/fetch_add)
- New `clock_gettime` / `system_clock::now()` / `steady_clock::now()` /
  `__rdtsc` call
- New branch with data-dependent predicate
- New struct field on a struct accessed in the tier's path
- New function call (especially from outside the same translation unit)
- New SIMD intrinsic (`_mm*`, `__builtin_*`)
- New mask compute / branchless predicate
- New memory load (especially uncached / cross-cache-line)
- New writes that could cause false sharing

**Latency-neutral additions** (no entry needed):
- Comments
- Existing-pattern reuse (calling an already-existing helper)
- Renames / refactors that don't change instruction count
- Dead code or ifdef'd-out code
- Tests + assertions inside `#ifdef`-disabled paths

### 4. Per-impacting-line: cost estimate

For each impacting addition, estimate the cycles + ns:

| Operation | Cycles (3 GHz) | ns |
|---|---|---|
| Add / Sub / mask / shift | 1 | ~0.3 |
| Multiply (int) | 3-5 | ~1-2 |
| Multiply (FPN<64> partial-products) | 30-60 | ~10-20 |
| Atomic relaxed load | 1 | ~0.3 |
| Atomic acquire load | 1-3 | ~0.3-1 |
| Atomic CAS (uncontended) | 5-10 | ~2-3 |
| `clock_gettime` (vDSO) | 100-300 | ~30-100 |
| L1 cache load | 4-5 | ~1.5 |
| L2 cache load | 12-15 | ~4-5 |
| Branch (predicted) | 1 | ~0.3 |
| Branch mispredict | 15-20 | ~5-7 |
| `_mm512_*` (AVX-512) | 1-3 per op | ~0.3-1 each |

Sum the per-line estimates; round to a sensible total. Flag values
that look implausible (e.g., "+100ns to hot path" likely indicates
a missing optimization opportunity to surface).

### 5. Per-impacting-site: branchless / cache audit

For each impacting addition, check:
- Is the predicate branchless? (mask compute, no `if`/`while` on hot
  path / producer fan_out)
- Is the new data on the same cache line as nearby fields it's read
  with? (avoid cross-line straddles)
- Does the addition reuse already-cached values? (per CLAUDE.md
  item 16 reuse-audit)
- Is there a compile-time-elidable variant possible? (template `bool`
  parameter, `if constexpr`)
- Is there a runtime-cacheable variant? (precompute once on slow path,
  read on hot path)

### 6. Emit draft changelog entry

Format:

```markdown
### YYYY-MM-DD — vX.Y.Z phase / feature [LATENCY ADD]

**Files:**
- `<path>:<line>` — what changed in one sentence.
- (additional files if multi-site)

**Cost:** estimated ns/tick (leg-A vs leg-B when paired); calibration
notes if any.

**Branchless:** yes/no/conditional. If conditional, what gates it.
What the steady-state branch direction is. Mispredict classes.

**Cache impact:** field offset + cache line. Note any new straddles
or false-sharing risks.

**Optimization note (FUTURE):** what could be cheaper later. Use the
canonical patterns:
1. Compile-time elision via `template <bool X_ENABLED>` — saves all
   cycles when off; recompile to toggle.
2. Runtime predicate caching — precompute on slow-path, read on hot.
3. Slow-path liveness flag — shift the work entirely to slow-path,
   hot-path reads a flag.
4. Reuse existing computation — point to the value/site already
   computed; refer to CLAUDE.md item 16.

**Tracker:** is this addition the FIRST in a sprint? Reference back
to the relevant master plan + sub-plan path. Note if operator
flagged it as an acceptable trade-off vs. a "must revisit" item.

---
```

### 7. Output

Emit:

```
# /latency-track report — <range> — <date>

## Summary
- Hot-path additions: N (ranked by cost)
- Producer fan_out additions: M
- Slow-path additions: K
- Cold-path additions: ignored (Q files)

## Draft HOT_PATH_CHANGELOG.md entries

<entry 1>
<entry 2>
...

## Audit findings (informational)
- <site>: <reason it was/wasn't included>
- <merge-scan suggestion>: if any addition could share existing
  computation per CLAUDE.md item 16, surface here. Cross-link to
  /merge-scan for the codebase-wide sweep.

## Recommendations

### Must add to changelog
- <list of entries the operator must paste>

### Worth verifying
- <items where cost estimate uncertain; suggest a benchmark>

### Acceptable as-is (no entry needed)
- <items that don't affect a latency tier>
```

## Heuristics

### Cost rounding

- ≥10 ns or 1+ instruction added on hot path → entry REQUIRED
- ~5-10 ns slow-path → entry RECOMMENDED
- < 1 ns / cold path → entry OPTIONAL (informational)

### When the cost is "0 ns"

If the addition is fully eliminated by the optimizer (e.g.,
`if constexpr` block when condition false, dead-stripped function),
report as "0 ns (compile-elided)" with the elision mechanism noted.
This is GOOD — prefer this pattern when possible (per CLAUDE.md
item 16's "Hot/producer paths get branchless mask compute on shared
data; slow-path can use predictable branches").

### Anti-patterns to flag (RED)

- New `if (X)` on hot path with data-dependent predicate, NOT
  preceded by branchless mask conversion
- New atomic CAS on hot path (slow path is fine; hot path should
  use seqlock or single-writer non-atomic)
- New struct field that causes existing fields to straddle cache
  lines (use `offsetof` math to verify)
- New `clock_gettime` on hot path (use `tick.sequence` or
  `__rdtsc` instead — hot path is per-tick, the sequence number
  is already there)
- New memory load that misses cache (verify the field is on a
  hot cache line via `offsetof` or explicit alignment)

### Cross-link to /merge-scan

If a new addition does work that an adjacent site ALREADY does
(e.g., another clock_gettime in the same cycle), do not fabricate
the sharing — call out the opportunity in the report. The operator
runs `/merge-scan` for that scope, surfaces the merge candidate,
and decides whether to refactor.

## What this skill is NOT

- Not a benchmark — estimates from instruction patterns, not measured
  cycles. Real benchmarks via `bench_*.cpp` give the truth.
- Not a code editor — proposes changelog entries, doesn't apply them.
- Not a substitute for `/merge-scan` — sister tool; ADDITIONS vs
  SHARING.
- Not a hook — invoked explicitly, not on every edit. (Hook variant
  could fire on commit if operator wants automation; see /update-config
  for adding a PostToolUse hook.)

## Background — why this skill exists

v5.12.1.B.3 added ~1-2 ns to the hot path for the staleness mask.
Operator (Jenny) explicitly noted "i dont like adding latency"
2026-05-08 and asked for a tracker so future-you knows what was
added + how to drop it later.

The discipline:
1. Hot-path / producer-fan_out additions are visible in
   `DOCS/HOT_PATH_CHANGELOG.md`
2. Each entry has a "FUTURE" optimization note pointing the way to
   drop the cost
3. Sprint-end review: scan the changelog for "still cheap" or
   "now load-bearing" — the latter become candidates for an
   optimization pass

This skill is the audit step that ensures (1) actually happens.
Catching missed entries is the value; the operator does the
final review + paste.

The pattern generalizes: any disciplinary doc (CHANGELOG.md,
KNOWN_ISSUES.md, DOCS/RECURRING_BUG_PATTERNS.md) could have a
sister `/X-track` skill that drafts entries from diffs. Open new
ones as needed.
