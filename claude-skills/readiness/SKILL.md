---
name: readiness
description: Verify a plan before coding starts. Reads a plan file, walks the 10-item checklist from DOCS/CLAUDE_REVIEW.md, and grep-verifies each claimed dependency / file / function exists in the current codebase. Outputs PASS/FIXED/GAP/DEFERRED/ACCEPTED per item plus a punch list of unstated gaps.
---

# /readiness — Plan verification (pre-coding gate)

## What this does

Reads a plan file the user points at (default: most recently modified
`plans/2026-*-master.md` if no arg given) and runs a structured
verification pass. **Does not edit files.** Output is a report. User
decides whether the plan is GREEN to start coding, or whether the
flagged gaps need to be patched first.

This is the systematized version of the manual readiness check we ran
during the v5.1 polish migration. Same checklist, automated greps,
single concrete report.

## Invocation

- `/readiness` → audits the most recently modified `plans/*.md` that
  has "master" or "plan" in its name
- `/readiness <path>` → audits the specific plan file
- `/readiness <path> deep` → also runs codebase-wide cross-references
  (slower, more thorough)

## Pass structure

Spawn an Explore subagent with the plan file in hand. The subagent:

1. **Parses the plan** — extracts:
   - Phases / ships / version bumps mentioned
   - Files claimed to be touched (from "Files touched" sections, code
     blocks with paths, or inline mentions like `EngineSharded.hpp`)
   - Functions / symbols claimed to exist or be added
   - Cfg fields claimed to be added
   - Test counts claimed
   - Dependencies stated as "use existing X" (these are the high-risk
     ones that need verification)

2. **Verifies the codebase** — for each claimed dependency:
   - **FIRST: check `DOCS/CODE_MAP.md`** for the function/symbol. The
     map is auto-generated via `tools/gen_code_map.sh` and lists every
     `Pattern_FunctionName` with file:line. Hit = exists. Miss = it's
     either renamed (try fuzzy match) or genuinely new.
   - Files: `ls -la <path>` to confirm exists (or that "create new"
     paths don't conflict with existing)
   - Functions (if not in CODE_MAP): `grep -nE "^inline.*<name>|^static.*<name>|^void <name>|^int <name>"` — but be careful:
     a CODE_MAP miss might mean the name is wrong, not that the
     function is absent. Try a similarity match against CODE_MAP first.
   - Cfg fields: `grep -E "^\s*<name>" engine.cfg engine.cfg.example`
     PLUS check `CoreFrameworks/ControllerConfig.hpp` (cfg can exist in
     code with no example default — that's a doc gap, not a code gap)
   - REST endpoints / external API calls: `grep -E "/api/v3/<endpoint>"`
   - Existing test patterns: `grep -nE "test_<thing>|<thing>_test"`,
     OR check `tests/INVARIANTS_MAP.md` if the change touches a known
     invariant (the map shows which test group covers each).

   **CODE_MAP currency check**: if the most recent commit touching code
   files is later than CODE_MAP.md's "Last regenerated" header, suggest
   re-running `./tools/gen_code_map.sh` before relying on the map.

3. **Walks the 10-item checklist** from `DOCS/CLAUDE_REVIEW.md`:
   1. Hot path purity — does any item touch `ExecutionCore_Tick` /
      `BG_Evaluate` / `SG_Evaluate`? If yes, scrutinize for branches /
      allocation / float math.
   2. Train-serve parity — touches `RegimeSignals` /
      `ModelFeatures_Pack` / strategy dispatcher? Verify both
      `BacktestSharded_Run` AND `EngineSharded_Run` paths covered.
   3. Surface area — count files touched per ship; flag if > 8 or if
      `if (live_trading)` / `if (engine_arch == ...)` branches
      proliferate.
   4. Pointer init / heap lifecycle — new heap-allocated state? Check
      `_Init` / `_Free` / NULL-init pattern.
   5. Backward compat — touches `SHARDED_SNAPSHOT_VERSION`,
      `MODEL_FORMAT_VERSION`? Cfg removals?
   6. Multi-threading — new thread? new shared state? new atomic?
      Check single-writer rule against `DOCS/CLAUDE_INVARIANTS.md`.
   7. Test coverage — explicit test counts in plan? Files exist?
      Existing tests at the planned path?
   8. Docs + invariants — load-bearing rule added? Should
      `DOCS/CLAUDE_INVARIANTS.md` get a new entry? Plan mentions
      `DOCS/CHANGELOG.md` update?
   9. Forward maintenance — touches > 3 sites? Already factored via
      X-macro / OneCore helper? If similar code repeats 3+ times in
      the plan, suggest a helper.
   10. Rollback story — pre-tag mentioned per ship? Branch policy
       clear?

4. **Output** — single markdown report:

```
# /readiness report — <plan filename> — <date>

## Plan summary
- <N> ships planned across <M> versions
- Total estimated effort: <X hours>
- Branch: <branch name from plan or current>

## Checklist verdicts

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | PASS | none touched |
| 2 | Train-serve parity | FIXED | flagged backtest gap; plan amended |
| 3 | Surface area | GAP | ship 4 touches 11 files — propose helper extract |
...

## Dependency verification

| Claimed dependency | Verified | Notes |
|---|---|---|
| `BinanceOrderAPI.hpp` `/api/v3/account` | ✅ exists at line 666 | ok |
| `BinanceOrderAPI.hpp` `/api/v3/openOrders` | ❌ not found | hidden scope: ~1h to add wrapper |
...

## Hidden scope detected

1. <claimed-dep>: not in codebase. Estimated effort to add: <X>.
2. ...

## Recommendations

### Must fix before coding
- ...

### Worth fixing during coding
- ...

### Acceptable risk (don't block)
- ...

## Verdict: GREEN / YELLOW / RED

GREEN — start coding now
YELLOW — fix the must-fix items above first (~30 min)
RED — significant rescope needed; revisit plan
```

**Save the report to a private file as well as printing it.**
Convention (set 2026-05-06): write the report to
`plans/plan_checks/readiness-<YYYY-MM-DD>-<plan-stem>.md` where
`plan-stem` is the audited plan's filename without the date prefix
and `.md` extension. Workspace-symlinked, gitignored from public
repo. `mkdir -p plans/plan_checks` before writing. Also print the
same report to stdout for live triage.

## Map-update suggestions (post-verify)

After verifying the plan, suggest map updates the implementation will
need:

- **CODE_MAP.md regen** if the plan adds new `Pattern_FunctionName`
  functions or renames existing ones. Append `Run ./tools/gen_code_map.sh
  after coding completes` to the report.

- **INVARIANTS_MAP.md update** if the plan:
  - Touches a function listed in the existing invariant table —
    confirm the test still covers (or flag verdict change to
    DRIFT/PARTIAL/GAP)
  - Adds a new safety invariant to `DOCS/CLAUDE_INVARIANTS.md` —
    new row needed in the map
  - Adds a test that promotes an existing DISCIPLINE → COVERED — update
    verdict cell
  - Removes / renames a referenced test group — line numbers drift,
    update cells

These are NOT blockers — just remind the user (or the next plan)
to keep the maps fresh. The maps are not auto-updated; they're
human-curated reference docs.

## Heuristics

### Effort estimate sanity check

If plan says "1 hour" but the verifier finds 3 unverified
dependencies that each need ~30min of new code: flag as YELLOW with
revised estimate.

Reference effort costs (from past plans):
- New REST endpoint wrapper: 30-45 min each
- New cfg field with parser + default + GUI tooltip: 30 min
- New X-macro entry: 5 min
- New ML feature wired through Pack + RegimeSignals + retrain: 2-3h
- New strategy file end-to-end: 2-3 days
- New per-core override: 10 min (X-macro is generous)

### Anti-patterns to flag (RED)

- Plan touches hot path with new `if` branch → reject unless explicitly
  branchless + benchmarked
- Plan adds new global mutex → reject; codebase is lock-free by design
- Plan adds malloc to hot path or fan_out → reject (Live engine rule)
- Plan removes cfg fields → flag (breaks user cfgs)
- Plan touches `SHARDED_SNAPSHOT_VERSION` without bumping it → reject
- Plan modifies `MODEL_FORMAT_VERSION` invariant → flag (forces retrain)
- Plan introduces `if (engine_arch == ...)` in > 3 sites → flag
  (wrong abstraction; propose helper)

### Drift audit — train ↔ serve, write ↔ read, suite ↔ engine

This is the explicit version of checklist item #2. Train-serve drift is
the #1 silent-bug source in ML systems; missing it costs days of
debugging "model worked in suite but not live." Walk these eight
sub-categories on every plan that touches anything model-adjacent
(features, labels, metrics, models, stamps, snapshots, fingerprints):

1. **Feature drift** — plan adds/removes/reorders fields in
   `ModelFeatures_Pack`, `RegimeSignals`, or any struct the model sees?
   Verify: (a) fingerprint-computing code is updated; (b) every existing
   stamped model's fingerprint will mismatch (and that's intentional);
   (c) both `BacktestSharded_Run` and `EngineSharded_Run` paths build
   the new shape.

2. **Label drift** — plan changes how labels are computed (in
   `LabelFunctions.hpp` or `Backtest/`)? Old models trained on old
   labels will score nonsense against new labels. Plan must specify
   re-train requirement or explicit format-version bump.

3. **Metric drift** — plan computes a metric in two places that should
   agree (e.g. WF accuracy formula vs live confidence accumulator)?
   grep for the formula; both sites must be identical or share a
   helper. Look especially at:
   - `WalkForward_ComputeAccuracy` vs any live accuracy tracking
   - `held_out_metric` vs `wf_to_held_out_gap` vs `gap` in stamp
   - Any "score" function appearing in both Backtest/ and live paths.

4. **Path drift** — plan introduces indirection (symlink, versioning,
   rename) that breaks the assumption "X.foo's metadata lives at
   X.foo.bar"? grep callers that build paths via string concatenation;
   verify each handles the new shape. Common offenders:
   - `<model>.stamp` lookup vs symlinked model files
   - `<snapshot>.tmp` vs `<snapshot>` atomic-rename pattern
   - Per-core paths like `core_N_model_path` after auto-versioning

5. **Format drift** — plan changes a serialization format (stamp body,
   snapshot, run-history JSONL, config file) without bumping its
   version constant? grep for the relevant `*_VERSION` constant; if it
   isn't bumped, old and new readers diverge silently. Specific
   constants to check: `SHARDED_SNAPSHOT_VERSION`, `MODEL_FORMAT_VERSION`,
   stamp body's `model_format_version` field, any `_SCHEMA_VERSION`.

6. **Threshold drift** — plan threshold values used in two places that
   should agree? E.g. `gap_threshold` computed by suite, checked by
   engine — must come from the same cfg field, not duplicated as
   constants in both. grep for hardcoded threshold values that look
   like cfg shadows.

7. **Tick-source / time-source drift** — plan changes producer of tick
   data (CSV → WS, replay → live, ms → μs precision)? Training and
   serving must consume the same shape. Plan must specify which path
   each side uses.

8. **Build-flag drift** — plan adds code conditional on `-DUSE_NATIVE_128`
   / `-DLATENCY_PROFILING` / `-DUSE_XGBOOST`? Models trained under one
   flag set must behave identically under another, or the plan must
   specify which flags are baked into the model fingerprint.

Verdict per category:
- **PASS** — plan doesn't introduce drift in this category
- **DRIFT-SAFE** — plan introduces a change but the read/write paths
  symmetrically pick up the change (e.g. both sides go through the
  same helper)
- **DRIFT-RISK** — plan changes one side without the other; flag for
  fix before coding
- **DRIFT-BUG** — verified that current code mismatches; plan must
  patch as part of the ship

### Propose a fix for every DRIFT-RISK or DRIFT-BUG

Identifying drift is half the job; the other half is a concrete fix.
For each drift finding, the report must include a one-paragraph fix
proposal that meets two bars:

1. **Doesn't impact functionality** — if write/read paths agree
   today modulo the drift, the fix should keep them agreeing without
   introducing new behavior the user didn't ask for.
2. **Improves regression resistance** — prefer fixes that make
   future drift impossible (single source of truth, shared helpers,
   version pinning) over fixes that just paper over this instance.

Cheat-sheet of common fixes by category:

| Drift type | Preferred fix | Why this hardens against future regressions |
|---|---|---|
| Feature drift (add/remove ML feature) | Bump fingerprint contributor, force re-train, version-bump `MODEL_FORMAT_VERSION` | Old stamps refuse to load; can't accidentally serve a model trained with a different feature set |
| Label drift | Bump `MODEL_FORMAT_VERSION` + label_kind enum entry; gate stamp body's `label_kind` field | Old models rejected at load — no silent score divergence |
| Metric drift (two formulas) | Extract to one helper in `ML_Headers/` or `Backtest/`, both sites call it | Future metric changes propagate to both sites by construction |
| Path drift (symlink, rename, versioning) | Make BOTH companion files symlinks (e.g. `<X>.bin` AND `<X>.bin.stamp` are symlinks pointing to the same versioned base) | Engine path-builders stay simple; companion files travel together |
| Format drift (struct fields added) | Bump version constant in body + parser tolerates unknown keys forward-compat | Old readers reject new files cleanly; new readers handle missing fields with defaults |
| Threshold drift (constant in two places) | Single cfg field read at both sites; remove the duplicate | Operator changes one value, both sides agree |
| Tick-source drift (CSV vs WS) | Document explicitly in plan; assert in tests that suite + live consume same shape | Forces conscious decision when a tick source changes |
| Build-flag drift (model behavior depends on flag) | Bake flag-set into model fingerprint OR add load-time assertion that current build matches stamp's `built_with_flags` field | Model trained under flag-set A refuses to load under B |

When proposing a fix, pick the one that:
- Doesn't add user-visible behavior (no new prompts, no new defaults)
- Catches the SAME drift if introduced again later (test-friendly)
- Touches the fewest files
- Has a clear rollback (one commit, one tag)

If the plan author already proposed a fix, evaluate it against the
preferred approach above. Don't override it without reason — flag as
"plan's fix is acceptable; preferred alternative would be X" only when
the alternative is materially better at preventing future drift.

If the cheat-sheet doesn't cover the specific drift found, propose a
fix that satisfies the two bars above and explain reasoning. The goal
is a fix the user can adopt without further review unless they
disagree.

### Hardening checks (load-bearing implementation details often missed)

Plans tend to omit these because they sit at the implementation level
rather than the design level. They cause real bugs:

- **Atomic file writes** — does the plan write a file other processes
  may read concurrently (stamps, models, snapshots, run history,
  position files)? Pattern must be `fopen(tmp) + write + close +
  rename(tmp, real)`. `rename()` is atomic on POSIX within the same
  filesystem. Plain `fopen("w")` exposes a partial-file window.

- **Locale pinning for canonical bodies** — plan uses `%g`/`%f`/`%e`
  or `strtod` in code that builds a string for hashing/signing/parsing?
  Locale flips (`LC_NUMERIC=de_DE` produces `0,55` instead of `0.55`)
  silently break round-trips. Pin via `uselocale(newlocale(LC_NUMERIC_MASK,
  "C", 0))` or `setlocale` (process-wide; thread-unsafe).

- **GUI render-thread blocking I/O** — plan adds a panel that does
  `fopen` / `stat` / `opendir` / `popen` / network calls inside its
  render function? ImGui renders ~60Hz; per-frame disk I/O jams. Pattern
  is cache + Refresh button + window-appearing trigger.

- **Failure telemetry path** — plan adds an operation that can fail.
  Where does the error go? Spec must list one of: stderr only (CLI),
  GUI status bar (interactive), log file (audit), abort (load-bearing
  invariant). Default `fprintf(stderr)` for GUI-triggered features is
  YELLOW — operator running the suite never sees the message.

- **Resource cleanup audit** — every new `fopen` / `popen` / `malloc`
  / `EVP_*_new` / `system` must have its matching close on every error
  path. Mechanical scan of new code; flag any early-return that skips
  cleanup.

- **Cancellation semantics** — plan adds a worker thread or long-
  running operation? Spec must say what happens when the user cancels
  mid-way: graceful exit, state cleanup, leftover files, partial
  results visibility. Reuse existing `cancel_flag` plumbing where
  possible.

- **Cross-platform assumptions** — plan uses POSIX-only calls
  (`symlink`, `mkfifo`, `fork`, `mmap` flags, `O_DIRECT`)? Engine is
  Linux-only so this is usually fine, but call out the assumption so
  it can be revisited if the project ever ports.

### Propagation checks (where a change should land in N places)

Plans that add a cfg field, version, or load-bearing rule need to
propagate to several places. The skill should flag missing propagation:

| Adding... | Must also update... |
|---|---|
| New cfg field | parser + default in `ControllerConfig.hpp`, `engine.cfg.example`, GUI tooltip via `_T()`, `DOCS/CHANGELOG.md` entry, possibly `DOCS/CLAUDE_INTEGRATION.md` |
| New version constant bump | `DOCS/CHANGELOG.md`, snapshot/stamp/model migration note, test for old-version rejection |
| New invariant claim | `DOCS/CLAUDE_INVARIANTS.md` row + assertion(s) in tests + `tests/INVARIANTS_MAP.md` row promoted to ENFORCED |
| New `Pattern_FunctionName` function | implicitly captured by `gen_code_map.sh` next run; remind user to regen |
| New cfg default that changes behavior | `DOCS/CHANGELOG.md` BREAKING-CHANGE note, default chosen to match current behavior unless plan explicitly justifies the flip |
| New file format / serializer | version field in body, parser tolerates unknown keys forward-compat, test for old-version round-trip |

Any plan that adds a cfg field but doesn't list `engine.cfg.example`
in its files-touched table = GAP. Same for CHANGELOG.

### Behavior-change-via-default check

Adding a cfg with `default=1` when current behavior is "off" silently
flips behavior for every existing user on upgrade. Plans often do this
inadvertently. Flag any new cfg field where:

- The plan doesn't explicitly say "default=0" or "default matches current behavior"
- The plan defaults to a value that activates a new code path
- The plan has no CHANGELOG note marking the behavior change

Verdict: GAP unless the plan justifies the flip with a one-line "why
default=1" rationale.

### Pragmatic-but-ugly patterns to flag (YELLOW)

These are the patterns that bit us during v4.7.x and v5.0.x. Catch
them at plan time, not at v.next.X.bug time:

- **Dual paths surfacing** — plan adds branches on `event_log_mode`,
  `engine_arch`, `partial_exit_enabled`, `engine_mode`. Each branch
  added is a place where mode-0 and mode-1 (or legacy and sharded)
  can diverge. After implementation, use `/dust` scan 4b to count
  total branches; > 8 = propose helper extraction.

- **Half-wired enum/const additions** — plan adds e.g. `NK_NEW_KIND`
  to `Notify.hpp` but doesn't list a `Notify_Send(g_notify, ..., NK_NEW_KIND, ...)`
  emit site. The enum gets defined but never fired. Plan must
  list both the addition AND the call site. If the plan says "add
  the enum, wire later", capture as DEFERRED with explicit follow-up.

- **Snapshot-affecting struct change without persistence update** — plan
  adds field to `ExecutionCore<F>` / `CoreContext<F>` / `Position<F>`?
  Then `ShardedSnapshotPersist` must be updated in the SAME ship, or
  the field documented as "session-only, do not persist". Otherwise
  restart-while-feature-active = silent zombie behavior. (This bit us
  with `live_tp_b`/`active_b` on partials.)

- **Cfg field added but consumer not wired** — same shape as half-
  wired enums. Plan must list both parser addition AND read site,
  otherwise the user sets cfg and nothing happens.

- **New invariant claimed but no test added** — invariant docs are not
  enforcement; tests are. Plan must add at least one assertion per
  new invariant (or reuse existing, with reference). Reference
  `tests/INVARIANTS_MAP.md` to verify the test will land in the right
  group.

### Verdicts vocabulary

Match `DOCS/CLAUDE_REVIEW.md`:
- **PASS** ✅ — item satisfied as-is
- **FIXED** ✅ — patched in same review pass (rare for verification skill)
- **GAP** ⚠️ — must address before shipping
- **DRIFT** ⚠️ — pre-existing issue, flagged but not blocking
- **DEFERRED** — explicit "ship without this" decision, with reason
- **ACCEPTED** — divergence chosen, documented

## What this skill is NOT

- Not a linter — `/dust` does that
- Not a code-quality audit — code-review is separate
- Not a test runner — assumes existing tests pass
- Not predictive ("will this strategy make money?") — purely structural

## When to use

- Before starting a multi-day plan
- When picking up a plan written days/weeks ago (codebase may have drifted)
- After a CLAUDE.md / invariant doc update — re-check active plans against new rules
- When estimating effort for ship-cadence planning

## When to skip

- Single-file bug fixes
- Doc-only changes
- Plan written within the last hour by the same person who'd code it
  (already mentally fresh)

## Future variants

- `/readiness diff <commitA>..<commitB>` — re-verify when codebase
  drifts mid-plan (catches "I planned for v5.1.x, but now we're on
  v5.2.x and X has been refactored")
- `/readiness all-active` — verify every plan in `plans/` (not
  `plans/archived/`) at once
- `/readiness simulate <plan>` — rough scope estimate by category,
  no actual greps (faster, less rigorous)

## v5.4.0 additions — architectural sprint guards

These three checks were added after the v5.4.0 strategy-restoration
postmortem. The bug class they protect against: an architectural
sprint (sharding, decoupling, extraction) that wires the new entry
points but silently orphans existing function calls. Symptom is
"feature still appears to work on glance, but adaptive/transitional
logic is dead".

### Check 11 — Architectural sprint detection

Trigger keywords in plan: `split`, `decouple`, `extract`, `centralize`,
`per-core`, `shard`, `port-from-legacy`, `replace X with Y`, `extract
helpers`. When any present, require the plan to:

- Enumerate every public function of the modules being changed.
- For each function: WHERE is it called pre-sprint? WHERE will it be
  called post-sprint? If "nowhere," the plan must say so explicitly
  with a reason ("legacy path being removed in same sprint" or
  "deferred to phase N").
- Run `tools/calls_graph_diff.sh` against current vs proposed state.
  If the script flags orphans the plan didn't account for, that's a
  GAP — block ship until the plan addresses each one.

**Why this matters:** v5.4.0 postmortem F7-F10. The 4.0 sharding port
moved entry points to `Strategy_BuildParameters` but never wired the
strategy `_Init`, `_Adapt`, `_BuySignal`, `_ExitAdjust` lifecycle
calls. All five strategies had this — every adaptive behavior was
silently dead. `calls_graph_diff.sh` catches it at plan time.

### Check 12 — Display ↔ execution invariant

Trigger keywords: `Position`, `take_profit_price`, `stop_loss_price`,
`live_tp`, `live_sl`, `cached_params`, `pending_params`, GUI panel
names. When present, require that GUI display reads the SAME field
the hot path reads.

**Specific failure mode:** GUI reads `pos->stop_loss_price`, hot path
reads `core->live_sl + cached_params.ratchet_sl`. Both compile, both
look reasonable in isolation, but they diverge — display shows a
number that has nothing to do with the real exit trigger.

**Verification:** for each Position field touched by the plan,
grep both:
- Hot path callsites (under `CoreFrameworks/ExecutionCore.hpp`,
  `BG_Evaluate`, `SG_Evaluate`)
- Display callsites (under `CoreFrameworks/ShardedSnapshot.hpp`,
  `DataStream/EngineTUI.hpp`, `GUI/`)

If the same display value comes from a different source struct than
the hot-path execution decision, flag as INVARIANT BREACH — needs
explicit reconciliation in the plan.

### Check 13 — Strategy lifecycle completeness

Trigger keywords: `STRATEGY_*`, `MeanReversion`, `Momentum`,
`SimpleDip`, `EmaCross`, `MLStrategy`, `_Init`, `_Adapt`,
`_BuildParameters`, `_ExitAdjust`, `Regime_AdjustPositions`. When
plan touches any strategy, require all FIVE lifecycle stages to be
accounted for:

1. **Init** — per-core state allocation
2. **Adapt** — per-cadence state update
3. **BuildParameters** — gate parameter emit (hot path's contract)
4. **ExitAdjust** — per-cadence trailing logic for open positions
5. **RegimeAdjust** — on-transition retune

Stages can be marked "skipped — reason" (e.g. SimpleDip has no
Adapt because no regression feedback) but never silently absent.

**Verification:** read `DOCS/STRATEGY_INTERFACE.md` for the canonical
list. For each strategy the plan touches, check that all 5 stages
are either being changed or are explicitly noted as skipped.

### Check 14 — Function-pointer table / X-macro dispatch correctness

Trigger keywords: `X-macro`, `FOREACH_`, `dispatch table`, `function
pointer`, `registry`, `auto-generated dispatcher`. When plan replaces
hand-written `switch` dispatch with a function-pointer table or
X-macro registry, require these audit items before coding:

1. **Variant selection audit.** When multiple versions of a function
   exist for the same conceptual stage (e.g. legacy stub
   `Strategy_BuySignal` vs sharded `Strategy_BuildParameters`,
   or per-core sharded `_ExitAdjustSharded` vs legacy `_ExitAdjust`),
   the X-macro line MUST reference the variant currently used by the
   existing dispatcher's switch — **not** a name-pattern guess. Plan
   must enumerate which variant of each lifecycle function is
   "canonical" before writing the macro. Document choice in the
   target's interface doc (e.g. `STRATEGY_INTERFACE.md`).

2. **Signature uniformity audit.** Every function referenced by the
   table must take the SAME parameter list. Plan must list each
   strategy/feature/etc and its current signature side-by-side. If
   they don't match, the plan must include a Phase 0.5 step to
   refactor non-conforming signatures BEFORE the X-macro can be
   written. Otherwise: choosing a wider signature with `void* extra`
   ignored params silently allows semantic drift between
   "implementations."

3. **`calls_graph_diff.sh` runs before AND after each phase.**
   Catches "function defined but no caller" (orphan) and "caller
   exists but function definition missing" (broken dispatch).
   Output must show zero new orphans introduced by the refactor.

4. **Loop test in `// === EXTENSIBILITY ===`.** Plan must include a
   test that walks every entry in the X-macro and asserts dispatch
   works:

   ```cpp
   #define X(id, short, full, state, init, build, adapt, exit) \
       check(short " has all lifecycle ptrs non-null", \
             init && build && exit);
   FOREACH_STRATEGY(X)
   #undef X
   ```

   Catches "added implementation file but forgot the X-macro line"
   silent-dispatch-failure class.

5. **Snapshot test for hash stability.** If the X-macro generates a
   compile-time hash (FEATURE_REGISTRY_HASH, REGIME_REGISTRY_HASH,
   etc.) that contributes to a model fingerprint or persisted state
   key, plan must include a "hash equals snapshot value" test. Any
   change to the X-macro flips the hash and fails the test, forcing
   a deliberate "yes I'm changing the contract, here's the new
   snapshot value, retrain" acknowledgment.

**Why this matters:** v5.4.0 postmortem F7-F10. The sharding port
moved entry points but left strategy adaptive functions silently
orphaned (compiled, never called). Function-pointer / X-macro
refactors have the same risk class — the *name* of the function
doesn't tell you which *variant* you're getting. Compile-time
checks catch some failures (typos → unresolved symbols), but the
"wrong variant selected" + "added implementation but not table
entry" cases require explicit audit + tests.

**Verdict per item:**
- **PASS** ✅ — plan addresses all 5 sub-items
- **GAP** ⚠️ — one or more sub-items missing; must address before
  coding
- **INVARIANT BREACH** — variant selection is wrong (e.g. X-macro
  references legacy stub but current dispatcher uses sharded
  variant); plan must fix

This check fires in addition to Check 11 (architectural sprint) and
Check 13 (strategy lifecycle completeness). Together they cover the
v5.4.0 silent-orphan regression class plus the v5.8 X-macro variant
selection class.

## v5.9 ML hardening additions — Checks 15-17

These three checks were added after the v5.9 ML Hardening sprint
postmortem. The bug class they protect against: silent train-serve
drift through additions to the ML pipeline that LOOK forward-compat
but actually require a specific change-management discipline (snapshot
test update, retrain, stamp-binding refresh).

### Check 15 — ML feature change requires parity regression update

Trigger keywords in plan: `FOREACH_FEATURE`, `ML_Compute_`,
`Regime_ComputeSignals`, `RollingStats_Push`, `feature_matrix`,
`Features_PackAll`. When any present, require the plan to:

- Identify which v5.9.2a snapshot test will fail post-change.
  Snapshot tests live at `tests/controller_test.cpp` v5.9.2a
  EXTENSIBILITY block. Search for "Sub-area 1a" / "Sub-area 1b" /
  "Sub-area 3" depending on what's changing (features, signals,
  labels).
- For each test that will fail, plan must specify EITHER:
  - **Bytewise-equivalent refactor** — change is provably
    output-identical; no snapshot update needed (verify by running
    `./build.sh test` and confirming snapshot tests still pass).
  - **Intentional semantic shift** — recorded snapshot values
    will be updated AND the relevant `FOREACH_FEATURE` row's
    `version` field will be bumped. CHANGELOG must list the bump
    with retrain requirement.
- For pure-additive changes (new features), `FEATURE_REGISTRY_HASH`
  flips automatically (X-macro adds a row). Plan must specify the
  retrain trigger.

**Why this matters:** v5.9.2a snapshot test discipline. Pre-v5.9.2a,
function-body changes silently passed `FEATURE_REGISTRY_HASH`
verification (no X-macro change → no hash flip). Models loaded fine,
predictions silently drifted. Snapshot tests catch this at PR time;
this check catches it at plan time.

### Check 16 — New cfg field with stamp-bearing → recipe doc update

Trigger keywords: cfg field that affects ML inference. Specifically:
fields stamped via `StampInferenceCfgInputs` in v5.9.2b
(`confidence_threshold_scale`, `barrier_gate_enabled`,
`confidence_hard_block_threshold`, `held_out_fraction`,
`confidence_freshness_tau`, `bandit_blend_ratio`, `fee_rate_*`,
`feature_scaler_present`, `scaler_sha256`).

When plan adds a new such field:

- Verify it lands in `StampInferenceCfgInputs` struct.
- Verify `stamp_write_for_model` emits when has_* flag set.
- Verify `verify_model_stamp` parses + populates `ModelStampResult`.
- Verify `tools/stamp_model.sh` accepts a matching `--<field>` arg.
- Verify v5.8.8-style round-trip test extends.
- Verify `DOCS/ML_TEST_RECIPES.md` recipe entry updated with the
  new flag (operators need to know what to pass to `stamp_model.sh`).
- Verify `DOCS/PARITY_LIFECYCLE.md` row updated.

If any of these is missing → GAP, plan must address before coding.

### Check 17 — Model-load path changes → strict-mode integration test

Trigger keywords: `CoreModelZoo`, `Model_Load`, `verify_model_stamp`,
`ModelHandle`, `held_out_gate_strict`, `feature_scaler_present`,
`scaler_load_failed`, `scaler_sha256`. When plan touches the model
load path:

- Verify the 3-tier strict-mode behavior (refuse / warn / skip)
  is preserved per `DOCS/CLAUDE_ML_INVARIANTS.md`.
- For each new failure mode, verify a corresponding PerCoreSnap
  field surfaces it (the v5.9.0b `model_load_failed` /
  v5.9.3a `scaler_load_failed` pattern).
- For each new failure mode, verify ML Status panel renders
  distinct state (red for warn-mode-with-identity, sand for
  legacy-no-attempt).
- For each new failure mode, verify rate-limited CRITICAL log
  fires (using `Health_LogCriticalRateLimited` per v5.9.0b).
- Verify integration test exists for BOTH refusal path AND
  warn-mode observability path (per
  `DOCS/CLAUDE_INVARIANTS.md` "Train-Serve Handoff Verification").

**Why this matters:** The v5.9.0b + v5.9.3a Gap H pattern is the
cure for the "silent fallback" class. Every new failure mode must
inherit the pattern. Otherwise we re-introduce silent drift.

**Verdict per item:**
- **PASS** ✅ — plan addresses
- **GAP** ⚠️ — must address before coding
- **DEFERRED** — explicit out-of-scope decision

These three checks fire in addition to Checks 11-14 (sprint guards).
Together they cover the v5.9 silent-failure class plus the v5.8
X-macro variant selection class.
