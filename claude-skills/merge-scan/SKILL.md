---
name: merge-scan
description: Scan the codebase + in-flight plans for reuse-merge opportunities — repeated atomic loads, redundant clock_gettime calls, duplicated cfg accesses, parallel function bodies that could share a helper, state fields that could be reused vs adding new ones. Output is a ranked punch list of merge candidates with proposed unifications, NOT actual edits. User decides which to act on. Pairs with CLAUDE.md item 16 (reuse-audit principle) and the per-plan check in /readiness item 18.
---

# /merge-scan — Reuse + sharing opportunity audit

> **Uniform parameter + preload contract:**
>
> **Optional invocation args:**
> - `<scope_path>` — plan path or code subsystem to focus reuse-merge scan; default = full sweep
> - `[focus_keywords...]` — narrow scan focus (e.g., "atomic load" "clock_gettime" "cfg access")
>
> **Stage 0 DESIGN_PHILOSOPHY preload** (workspace/DOCS/DESIGN_PHILOSOPHY.md):
> - § 4 (Latency cost framework) — reuse-audit principle; shared atomic loads / cfg accesses / conversions
> - § 7 (Structural-fix family) — when reuse opportunity is registry-shaped, propose X-macro registry vs helper extraction
>
> Cite specific § N rows in merge candidate descriptions.

## What this does

Scans the engine codebase + currently-active plans for places where
work is being duplicated and could be UNIFIED to save clock cycles
+ cognitive load. Outputs a ranked punch list of merge candidates.
**Does not edit files.** User decides which items to act on.

**Distinct from /dust:** /dust catches DEAD code, ROTTING comments,
COPY-PASTE patterns. /merge-scan catches LIVE-but-redundant work
patterns — things that are correct individually but wasteful in
aggregate (two atomic loads of the same field, two clock reads in
the same cycle, two cfg branches with same predicate).

**Distinct from /simplify:** /simplify reviews CHANGED code and may
fix issues automatically. /merge-scan is a READ-ONLY audit that
spans the whole codebase + plans, surfaces patterns, and lets the
operator pick.

**Distinct from /foxlib-promotion:** /foxlib-promotion identifies
GENERIC primitives ready to extract to FoxLIB. /merge-scan
identifies INTERNAL duplications that should stay in-tree but be
unified.

## When to use

- Before opening a new sub-ship that touches a high-cadence path
- Periodically during a multi-week sprint (every 2-3 ships)
- After a /plan-check pass surfaces > 1 plan touching the same
  function or struct
- When a slow-path or hot-path budget gets tight and you're looking
  for "free" savings

## When to skip

- Single-plan single-file work (use /simplify instead)
- Pure cleanup pass with no merge dimension (use /dust instead)
- After a structural refactor where merge opportunities were
  intentionally collapsed (no new redundancy expected)

## Invocation

- `/merge-scan` → scans the engine repo + plans/ for opportunities
- `/merge-scan <subsystem>` → narrows to a specific subsystem
  (e.g. `slow-path`, `hot-path`, `OMS`, `ML`)
- `/merge-scan plans` → only scans pending plans for cross-plan
  merge opportunities (not yet in code)

## Pass structure

Spawn an Explore subagent. The subagent runs the scans below in
parallel where possible, aggregates findings, and emits a single
report.

### 1. Repeated-atomic-load scan

For each `std::atomic<T>` field accessed in the codebase, count
distinct call sites. Flag fields read > 2 times per slow-path
cycle:
- Common pattern: kill_switch_tripped, flatten_pending,
  recovery_until_us, last_ws_tick_us
- Merge proposal: cache to local at the topmost gate; pass down

For HOT path: flag any atomic accessed > 1× per tick — should be
hoisted to ParameterSlot snapshot or seqlock-published state.

### 2. Repeated-clock-read scan

`grep -rn "system_clock::now\|steady_clock::now\|clock_gettime\|__rdtsc"`
across CoreFrameworks / DataStream / Strategies / ML_Headers.

For each cluster of calls within the same logical cycle (slow-path
iteration, fan_out body, OMS_Tick etc), check if they could share
ONE read. If yes, propose hoist + pass-down.

Existing v5.12.1.A.2 sharing pattern is the template:
`sp_last_tick_us` write + `CheckWsStaleness` use the same `now_us`.

### 3. Repeated-cfg-access scan

For cfg fields read in the same function, check for compiler-
hostile patterns (volatile-like access, repeated dereference).
Modern compilers usually hoist via SROA, but verify by reading
generated assembly when in doubt. Flag obvious cases where
`cfg.X` appears > 5 times in the same function body.

Lower priority than #1 + #2; mostly informational.

### 4. Function-body parallelism scan

For each pair of functions that operate on the same data structure
(e.g., portfolio.active_bitmap), compare body shapes. If both:
- Walk the same bitmap with `__builtin_ctz`
- Pull the same fields per-slot
- Differ only in the ACTION per slot

then propose extracting a shared walker (template / functor /
inline lambda). Examples to watch:
- `EventLoop_TimeExitOneCore` + `EventLoop_FlattenAll` (both walk
  active_bitmap and submit market exits — but with different
  predicates and reason codes)
- `Strategy_AdaptPerCore` + `Strategy_BuildParameters` (both
  iterate per-core; different state mutations)

Don't propose extraction unless the bodies overlap > 70%.
Premature abstraction is worse than duplication.

**v5.14.2.E.3 strengthening — recommend X-macro for recurring patterns:**

When the duplication is across BOOT ↔ BACKTEST ↔ HOT-SWAP sites (or
similar mirror patterns: BUY ↔ EXIT, SINGLE-ZOO ↔ ENSEMBLE), the
recurring class is Class 18 (mirror data-flow incomplete). Recommend
**X-macro registry / helper extraction** even when overlap < 70% —
because future drift is the bigger cost, not current duplication.

Per CLAUDE.local.md going-forward rule: "Structural fix > direct patch
when bug class can recur." Direct patches are for true one-off bugs;
mirror patterns get registries.

Canonical examples:
- `STAMP_CFG_AUTOPOPULATE` (v5.14.1.E.E.B) — extracted production-caller
  field-population pattern; extinguished v5.9.5b class after 4
  recurrences (PARITY-002/003/004/005/008)
- `EnsembleModelZoo_PostLoadSetup` + `CoreModelZoo_PostLoadSetup`
  (v5.14.2.E.1) — extracted boot/backtest/hot-swap setup sequence;
  extinguished Class 18 mirror class for model-load surface after
  4 recurrences (PARITY-009/010/011/012)

When you find duplication that fits this shape, the report should
say: "Recommend X-macro registry + helper extraction (Class 18
prevention; CLAUDE.local.md item: structural fix > direct patch)."
Operator decides; bias toward structural even if more work today.

### 5. State-field reuse scan

For each plan that proposes a NEW field on a load-bearing struct
(EventLoopState, OrderManagerState, CoreContext, ModelHandle),
check if an existing field has compatible semantics. Examples:
- `recovery_until_us` (v5.12.1.A.3) — could `kill_recovery_warmup`
  have served? No — different cadence (cycles vs us). Distinct.
- `flatten_pending` (v5.12.1.A.2) — could `kill_switch_tripped`
  have served? No — different lifecycle (one-shot per WS event vs
  sticky-session). Distinct.

Most cases will be "distinct, justified". Flag the rare ones
where the new field truly duplicates an existing field's role.

### 6. Cross-plan merge scan

Walk currently-active master plan + sub-plans. For each plan that
adds a function/field/cfg, check if another plan adds something
adjacent. Examples to flag:
- v5.12.1.A.3 (recovery refusal in BuildParameters caller) +
  v5.12.1.B (publish_tick check in BuildParameters caller) — both
  add slow-path gates above the same call. Could share entry/exit
  pattern.
- v5.12.3.A (composite-signal extractor in Model_Predict) +
  v5.12.3.B (mixed-output normalizer in Model_Predict) +
  v5.12.3.E (primary-handle cleanup in Model_Predict) — all three
  ships modify the same function body. Sequence them so reads of
  `m->backend`, `m->buy_class_idx`, `m->normalizer` happen in one
  struct fetch.

### 7. Branch-vs-branchless audit

For high-frequency paths (hot path BG_Evaluate / SG_Evaluate /
ExecutionCore_Tick + producer fan_out), flag any predicates that
look like `if (X) { ... } else { ... }` and aren't compile-time
elided. Propose conversion to branchless mask-select where the
branch is data-dependent and could mispredict.

For slow-path: leave branches alone unless they're obviously
high-mispredict (e.g., guard predicates that flip based on
runtime state at unpredictable cadence).

Distinguish carefully — branchless is faster only when:
1. Predictor working set is tight (hot path)
2. Branch direction is data-dependent + flip-flop
3. Both arms must be cheap (no expensive work being skipped)

If skipping the branch would mean wasted work (e.g.,
`Strategy_BuildParameters` body that's expensive), the branch is
correct because the savings dominate the mispredict cost.

## Output format

```
# /merge-scan report — <subsystem or "all"> — <date>

## Atomic load redundancies (priority: HIGH if hot/producer; MEDIUM if slow-path)
- Field `oms.flatten_pending` — read in CheckWsStaleness CAS
  + RebuildOneCore recovery check. 2 reads per cycle.
  Cost: ~10ns. Proposal: cache to local in caller; pass down.

## Clock-read redundancies (priority: HIGH on slow-path)
- ...

## Cfg-access redundancies (priority: LOW; informational)
- ...

## Function-body parallelism candidates
- ...

## State-field reuse candidates
- ...

## Cross-plan merge candidates
- ...

## Branch-vs-branchless flags
- ...

## Overall recommendation
- Top-3 highest-impact items to act on
- Items deferrable to next sweep
- Items to leave alone (intentional duplication)
```

## Heuristics

### Don't propose merges that

- Cross hot-path / slow-path boundaries (different cadence, different
  budget, different optimization rules)
- Combine independent concerns (kill switch + recovery — both safety
  but different semantics; merging conflates the cause-of-halt)
- Reduce code clarity below the line where future contributors can
  follow ("clever" merges that need a paragraph of comment)

### Do propose merges that

- Share a SCALAR computation (clock read, cfg flag, atomic load) across
  callers in the same logical cycle
- Extract a SHARED ITERATOR over a common data structure (bitmap walk)
- Sequence reads of nearby struct fields so they hit the same cache line

### Latency rule of thumb

- Hot path: every saved branch matters; propose branchless aggressively
- Producer fan_out: every saved syscall matters; propose batching, rdtsc
  over clock_gettime, etc.
- Slow path: every saved μs matters but NOT every saved ns. Propose
  merges that save > 50ns; ignore < 10ns.
- Cold path (boot, shutdown, debug): merges only worth it if they
  improve clarity, not for cycle savings

## What this skill is NOT

- Not a code rewriter — proposes merges, doesn't apply them
- Not a benchmark — doesn't measure actual cycle savings, only
  estimates from the pattern
- Not a substitute for /readiness — /readiness item 18 (added v5.12.1)
  is the per-plan reuse check; /merge-scan is the codebase-wide sweep

## Background — why this skill exists

v5.12.1.A.2 surfaced a missed merge during initial implementation:
`EventLoop_CheckWsStaleness` had its own `clock_gettime` while the
existing `sp_last_tick_us` update at slow-path tail did the same
read ~100ns later. Operator (Jenny) caught it in code review:

> "is there not a way to reduce the latency added, by analyzing
> deeper and like rolling stuff into single usge patterns?"

Refactor unified the two reads (saved ~50-100ns/cycle/core). The
discipline added to CLAUDE.md item 16 + this skill exist to surface
similar opportunities BEFORE they ship as separate-clock-read
implementations.

The pattern generalizes beyond clock reads — atomic loads, cfg
accesses, struct-field fetches, function bodies that walk the
same bitmap. Whenever two consumers in the same cycle do the same
work, there's a merge candidate.
