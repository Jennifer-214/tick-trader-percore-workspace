---
name: dust
description: Audit the tick-trader-percore codebase for cleanup candidates — rotting comments, oversized functions, copy-paste patterns, dead code, multi-site change leaks. Output is a ranked punch list, NOT actual edits. User decides which items to pick up.
---

# /dust — Codebase audit (non-destructive)

> **Uniform parameter + preload contract:**
>
> **Optional invocation args:**
> - `<scope_path>` — file_path_glob to scope cleanup scan; default = full codebase sweep
> - `[focus_keywords...]` — narrow scan focus (e.g., "rotting comments" "oversized fns" "copy-paste")
>
> **Stage 0 DESIGN_PHILOSOPHY preload** (workspace/DOCS/DESIGN_PHILOSOPHY.md):
> - § 11 (Process discipline) — what NOT to leave behind; cleanup discipline; structural-fix-preferred over local patches when bug class can recur
>
> Cite § 11 in cleanup recommendations when item suggests structural fix vs surface cleanup.

## What this does

Runs a structured pass over `/home/caramel/code/tick-trader-percore/` and
emits a ranked punch list of cleanup candidates. **Does not edit files.**
The user reads the list and decides which items (if any) to pick up.

## Pass structure

Spawn an Explore subagent with a thoroughness level set by the user's
arg (default `medium`). The subagent runs the seven scans below in
parallel where possible, aggregates findings, and returns a single
report.

**Arg parsing**:
- `/dust` → `medium`
- `/dust quick` → fewer scans, faster
- `/dust deep` → all scans + cross-references

**Scope override**: `/dust <subdir>` (e.g. `/dust GUI/`) restricts the
scan to that subdirectory.

## The seven scans

### 1. Rotting comments + stale TODOs

Find:
- `TODO`, `FIXME`, `HACK`, `XXX`, `REVIEW` markers
- Comments referencing version numbers older than `Version.hpp`'s current
  (e.g. "v4.7.x followup" when current is v5.1.x)
- Comments referencing phase names that have shipped (e.g. `phase06`,
  `phase8a` if those plans are in `DONE` status per master-roadmap.md)
- "Pre-X behavior" comments where X is now in production

Output: `file:line — comment text — staleness reason`.

### 2. Oversized functions

Find functions/lambdas where:
- Body > 100 lines
- Nesting depth > 4 (counted by `{` indentation)
- Lambda capture list > 12 items (real signal that the function is
  doing too many things and reaching too far)

For this codebase, prime candidate is `EngineSharded_Run` and the
nested lambdas inside it (`producer` thread, `fan_out`, `slow_paths[c]`).

Output: `file:line function_name lines=N nesting=M captures=K`.

### 3. Copy-paste signatures

Find blocks of 8+ lines that appear in 3+ files (potential factor-out
candidates). Use `grep -F` patterns extracted from common shapes:
- `RollingStats_Push` calls in sequence (factored — but check for new ones)
- `OMS_PushSubmit` arg lists
- `state.cores[c].slow_state->X` access patterns
- `if (state->cores[c].strategy_id == STRATEGY_NONE) continue;` skips

Output: `pattern: <signature> appears in <list of files:lines>`.

### 4. Dead code candidates

Find:
- Functions defined but referenced 0 times outside their declaration
  (use `grep -c` per function name)
- `static inline` functions in headers that are never instantiated
- Cfg fields that are parsed but never read (search for the field name
  on RHS of an `if`, comparison, or assignment)
- Test functions never invoked from `main()`
- **Enum constants defined but never emitted/used** — grep e.g. all
  `NK_*` (Notify kinds), `STRATEGY_*`, `GATE_FLAG_*`, `REGIME_*`
  constants. For each, check whether it appears anywhere except its
  own definition. Unused = "sprint debt" — enum was scaffolded but
  the emit/handler site never wired up. Common pattern: developer
  added the kind anticipating future use; future never arrived.

Caveat: header-only template instantiation is hard to detect with grep
alone — flag candidates, don't claim definitively dead.

### 4b. Dual-path proliferation

Find branches on legacy/architecture mode flags that have spread
across the codebase. These are the "dual paths" pattern flagged in
CLAUDE_REVIEW.md item 3 ("`if (live_trading)` branches = wrong
abstraction"). Common offenders to grep:

- `engine_arch == ENGINE_ARCH_PER_CORE_SLOW` / `!= PER_CORE_SLOW`
- `engine_mode == ENGINE_MODE_SHARDED` / legacy single_core
- `event_log_mode == 1` (mode 0 vs mode 1 OMS path)
- `partial_exit_enabled` (legacy single-leg vs paired-leg)

For each, count call sites. > 8 sites in production code = flag for
helper extraction. > 15 = strong "the abstraction is wrong, factor a
helper" signal. Rule: if you can write the helper signature in your
head, it's the right call.

Example output: `event_log_mode==1: 12 sites across 4 files —
candidate for OMS_HandleFill_ModeAware() helper`.

### 4c. Geometry mismatches (snapshot vs struct)

Cross-reference fields in stateful structs against their snapshot
serialize/deserialize sites. When new fields are added without
updating snapshot persist, the result is "zombie behavior on restart"
— state restored partially, mismatched fields default-init silently.

Compare:
- `ExecutionCore<F>` fields ↔ `ShardedSnapshotPersist::write_core` /
  `read_core` field list
- `CoreContext<F>` fields ↔ `ShardedSnapshotPersist::write_context` /
  `read_context` (if exists)
- `OrderManagerState<F>` fields ↔ snapshot if persisted

Find fields present in the struct but missing in serializer (or vice
versa). Output: `ExecutionCore<F>::live_tp_b — in struct (line X) but
NOT in serialize (lines Y-Z); restart will zero this and break partials`.

### 5. Multi-site-change leaks (5+ site rule)

Identify "every time you add an X you have to touch N files" patterns.
Walk the recent commits (last 30 commits) and count file touches per
commit message keyword. If a feature category consistently touches 5+
files, flag the pattern + propose a factoring.

Existing factorings (don't re-flag):
- `PER_CORE_OVERRIDE_FIELDS` X-macro for per-core cfg overrides
- `PER_CORE_OVERRIDE_INT_FIELDS` X-macro for INT cfg overrides
- `EventLoop_*OneCore` helpers for per-core slow-path work
- `EventLoop_UpdateRollingStateOneCore` helper for cadence pushes
- `STRATEGY_*` constants + dispatcher case in `StrategyParameters.hpp`

Categories worth scanning for new patterns:
- New cfg field — usually 6+ touches: `ControllerConfig.hpp` (struct +
  default + parser) + `engine.cfg` + `engine.cfg.example` +
  `GUI/SettingsPanel.hpp` (field_defs + tooltip)
- New ML feature — `FEAT_*` + count bump + version bump + Pack site +
  RegimeSignals + Regime_ComputeSignals — 6+ touches
- New TUI display field — `TUISnapshot` struct + `TUI_CopySnapshotSharded`
  + GUI panel render + populator helper — 4+ touches
- New strategy — interface + dispatcher + RegimeDetector mapping +
  tests — 4+ touches (manageable, don't refactor unless 6+)

Output: `category: <description> — recent commits touching N files —
proposed factoring`.

### 6. Load-bearing assumptions not enforced

CLAUDE.md "Safety Invariants" section documents rules. Scan for the
invariant phrases and check whether each has a test or assertion in
code:

| Invariant | Where verified |
|---|---|
| `take_profit_pct >= 3 × fee_rate` | boot warn in v5.1.3 ✓ |
| Position TP > entry > SL | partial check in adjust functions |
| Snapshot re-activation | controller_test ✓ |
| Snapshot tick-counter drift | guard in EngineSharded ✓ |
| Per-core data-plane single-writer | structural (single thread per slow_state) ✓ |
| Confidence loop single-update site | tests in controller_test |
| Maker/taker fee accuracy | sanity check `total = maker + taker` |
| OMS submit funneling | tests v4.7.37 ✓ |

Output: list of invariants with NO direct test or assertion in the
codebase. These are at risk of silent regression.

### 7. Documentation drift

For each `.md` file in `DOCS/` and `plans/`:
- If filename contains a version number, check whether it matches a
  current shipped version vs an old one
- If body references a feature that doesn't exist in code (e.g.
  function names that don't grep), flag it
- If "Status: " marker is `WIP` / `IN PROGRESS` / `TODO`, flag for review

Output: `<file>: <issue>`.

## Output format

The skill returns a single markdown report:

```
# /dust report — <date> — <scope>

## High-leverage items (do these first)
1. <description> — <scope estimate: 5 min / 1 hour / 1 day> — <rationale>
2. ...

## Medium-leverage items
1. ...

## Low-leverage / cosmetic
1. ...

## Acceptable noise (don't fix unless you're already in the file)
1. ...
```

Each item:
- Cite file:line
- Brief description
- Scope estimate
- Rationale ("touched 8 files in last 5 commits", "comment from v4.3
  still references PortfolioController", etc.)

## What this skill is NOT

- Not a linter (cppcheck/clang-tidy run separately)
- Not a refactor — it never edits
- Not a test runner — green tests are necessary but separate from this
- Not a perf audit — latency/throughput is separate work

## Anti-patterns specific to this codebase

When prioritizing items, weigh these as high-priority signals:

1. **`if (cfg.engine_arch == ENGINE_ARCH_PER_CORE_SLOW)` proliferation**
   — CLAUDE.md item 3 calls out "if (live_trading) branches = wrong
   abstraction". If `engine_arch` checks scatter beyond ~3 sites in a
   single function, propose extracting an arch-aware helper.

2. **Per-tick / hot-path comment violations** — if a function comment
   says "hot path, must be branchless" but the body has `if`/`switch`,
   high priority.

3. **Comment vs code drift on load-bearing invariants** — if CLAUDE.md
   names a function as the single-source-of-truth for X but X is
   written elsewhere too, that's a real bug waiting to happen.

4. **Static-storage state with no `_Init` / `_Reset` / `_Free` triplet**
   — heap allocations or stateful structs need lifecycle clarity.
   Backtest panels enforce this rule (Dynamic Sizing in CLAUDE.md);
   live engine should too.

## Invocation

User runs `/dust [scope]`. Skill spawns Explore subagent with the seven
scans, returns the punch list. User then picks items and either:
- Asks Claude to fix one specific item
- Saves the punch list to `plans/YYYY-MM-DD-dust-pass.md` and works
  through it later

Skill takes 2-5 minutes typically. Report length: 200-500 lines depending
on scope.

## Future variants

If this proves useful:
- `/dust diff <commitA>..<commitB>` — only audit code added in that range
- `/dust regression` — audit invariants for missing tests, propose tests
- `/dust touched <file>` — audit just the file currently being edited

## v5.4.0 additions — orphan & dead-write detection

Added after the v5.4.0 strategy-restoration postmortem.

### Scan 8 — Dead-write detection (Position fields, GateParameters fields)

For each struct field that gets written outside of init/free, verify
there is at least one HOT-PATH or DISPLAY read of the field. Writes
with no matching read are candidate dead-writes.

**Pattern:** find `field = ...` and `field.x = ...` writes, then check
if `field` is read in any of:
- `CoreFrameworks/ExecutionCore.hpp` (hot path)
- `CoreFrameworks/ShardedSnapshot.hpp` (display/snapshot)
- `DataStream/EngineTUI.hpp` (legacy display)
- `GUI/*` panels (live display)

If a field is only read by tests or not at all, flag as dead-write.

**Specific high-risk fields to scan first** (these caused v5.4.0
postmortem F4):
- `Position::stop_loss_price`
- `Position::take_profit_price`
- `Position::original_tp`

**Why this matters:** legacy strategy `_ExitAdjust` functions write
to `pos->stop_loss_price`, but the sharded hot path reads
`core->live_sl + cached_params.ratchet_sl`. Both paths compile, both
look reasonable. Dead-write detection makes the divergence visible.

### Scan 9 — Orphaned function detection (active-build calls only)

For each `Pattern_FunctionName` definition in `Strategies/`,
`CoreFrameworks/`, `ML_Headers/`: grep call sites in active-build
source files (filter out tests + experiments + commented-out code).
Functions with zero call sites in any active build are candidate
dead code.

**Workflow:**

1. Get function definitions via `tools/gen_code_map.sh` output (or
   grep `^inline.*<name>(`).
2. For each, run `grep -rn "\\b<name>\\s*(" engine_files/` excluding
   tests/, experiments/, *_archived/.
3. Zero-hit functions go on the orphan list.

**Specific high-risk pattern from v5.4.0:** strategy lifecycle
functions (`_Init`, `_Adapt`, `_BuySignal`, `_ExitAdjust`,
`_BuildParameters`) for each of the 5 strategies. The pre-v5.4 audit
found 19 orphans plus 1 dead-defined function via this exact pattern.

A complementary tool exists: `tools/calls_graph_diff.sh` for the
"called in legacy but not sharded" diff. The dust scan is broader
("called nowhere in any path") and runs during routine cleanup.
