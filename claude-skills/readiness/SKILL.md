---
name: readiness
description: Verify a plan before coding starts. Reads a plan file, walks the 10-item checklist from DOCS/CLAUDE_REVIEW.md, and grep-verifies each claimed dependency / file / function exists in the current codebase. Outputs PASS/FIXED/GAP/DEFERRED/ACCEPTED per item plus a punch list of unstated gaps.
type: skill
concern: pre-coding-gate
audit_cadence: per-ship
tags: [audit-methodology, framework-discipline, plan-template, doc-discipline]
surface: [registry, cfg-flow, wire-format]
sister_skills: [/precoding-audit-gate, /parity-check, /trace-deps, /merge-scan, /dod-audit, /blindspot-scan, /plan-check]
loads_dynamically: [DOCS/DESIGN_PHILOSOPHY.md, DESIGN_SPECS/README.md, DESIGN_SPECS/refactor-patterns/cfg-flag-eligibility-criteria.md, DESIGN_SPECS/framework-patterns/x-macro-registry-with-presence-dispatch.md, DESIGN_SPECS/wire-format-patterns/wire-format-byte-preservation-discipline.md, DESIGN_SPECS/meta-disciplines/structural-fix-preferred-decision-framework.md, DOCS/RECURRING_BUG_PATTERNS.md]
---

# /readiness — Plan verification (pre-coding gate)

> **Uniform parameter + preload contract:**
>
> **Required invocation args:**
> - `<plan_path>` — sub-ship plan to verify
>
> **Optional invocation args:**
> - `[focus_keywords...]` — narrow which checks emphasize
>
> **Stage 0 DESIGN_PHILOSOPHY preload** (workspace/DOCS/DESIGN_PHILOSOPHY.md):
> - § 11 (Process discipline) — cold-pickup completeness; verify-handoffs-against-current-code; consult-before-coding
> - Family § matched per plan content keywords (cfg / hot path / SIMD / determinism etc.)
>
> Cite specific § N rows in PASS/GAP findings.

## What this does

Reads a plan file the user points at (default: most recently modified
`plans/<sprint-dir>/MASTER.md` or `plans/<sprint-dir>/subplans/*.md` if
no arg given; falls back to `plans/2026-*-master.md` for pre-reorg
plans in `plans/archived/`) and runs a structured
verification pass. **Does not edit files.** Output is a report. User
decides whether the plan is GREEN to start coding, or whether the
flagged gaps need to be patched first.

This is the systematized version of the manual readiness check we ran
during the v5.1 polish migration. Same checklist, automated greps,
single concrete report.

## Invocation

- `/readiness` → audits the most recently modified plan file (any of:
  `plans/<sprint-dir>/MASTER.md`, `plans/<sprint-dir>/subplans/*.md`,
  or `plans/<sprint-dir>/handoffs/*.md`)
- `/readiness <path>` → audits the specific plan file
- `/readiness <path> deep` → also runs codebase-wide cross-references
  (slower, more thorough)

## Execution model (added 2026-05-09 — recursion fix)

**ONE-WAY HIERARCHY. NO LAYER 3.**

```
LAYER 1: ORCHESTRATION
  - Main Claude session (or another orchestrator skill)
  - Decides WHEN to invoke this skill
  - Spawns ONE Explore subagent

LAYER 2: EXECUTION (this skill runs HERE)
  - The spawned Explore subagent reads this spec + applies the
    checklist BELOW directly
  - DOES NOT spawn further subagents
  - May apply OTHER skill checklists (/trace-deps, etc.) INLINE
    by reference (read their spec + execute their work in the
    same subagent run)
  - Returns a single combined report
```

**If you are reading this spec inside an Explore subagent:** YOU
ARE the auditor. Apply the checklist below using your read/grep/bash
tools. Do NOT spawn a nested subagent.

**If you need another skill's checklist** (e.g., /trace-deps Step 6
for a deep Class 18 dive): read that skill's spec + execute its
checklist as a section of your single report. By-reference
composition, not by-spawning.

See `DOCS/SKILLS_HIERARCHY.md` for the full execution model.

## Pass structure

The auditor (Layer 2 subagent):

0. **Stage 0 — DESIGN_SPECS preload by plan surface** (added 2026-05-14
   alongside CLAUDE.local.md condense). CLAUDE.local.md is now a
   pointer-index; rule deep-dives live in DESIGN_SPECS. To audit a plan
   correctly, the auditor must load the pattern BODIES it scans against,
   not just the names. Walk the plan body + match surface keywords to
   DESIGN_SPECS docs, then `Read` each match into context BEFORE walking
   the 28 checks:

   | Plan surface keyword | DESIGN_SPECS to load |
   |---|---|
   | "new cfg field", "boolean cfg", "cfg-flag" | `cfg-flag-eligibility-criteria.md`, `categorical-tag-applicability-pattern.md`, `universal-cfg-field-registry-pattern.md` |
   | "X-macro", "FOREACH_*", "registry entry" | `x-macro-registry-with-presence-dispatch.md`, `autopopulate-pattern-for-production-caller-class.md`, `heterogeneous-registry-pattern.md` |
   | "bit-pack", "BITMAP_*", "flag bitmap", "≥3 booleans" | `bitmap-flag-api.md`, `bitmap-overflow-protection-discipline.md`, `multi-bit-state-encoding-pattern.md` |
   | "K-state field", "state enum", "switch on state" | `multi-bit-state-encoding-pattern.md` |
   | "stamp body", "wire format", "HMAC", "byte-equivalence" | `wire-format-byte-preservation-discipline.md`, `pre-post-cfg-registry-split-for-emit-order-preservation.md`, `struct-padding-determinism-pattern.md` |
   | "hot path", "branchless", "predicate cache" | `cache-layout-discipline-for-hot-side-structs.md`, `branchless-math-kernel-pattern.md`, `latency-vs-cache-decision-framework.md` |
   | "SIMD", "AVX-512", "vectorize" | `avx512-byte-determinism-pattern.md`, `branchless-math-kernel-pattern.md` |
   | "rolling stat", "sliding window", "incremental mean/var" | `sliding-window-online-statistics-pattern.md`, `generic-ring-buffer-template-pattern.md` |
   | "mirror sites", "parallel paths", "Class 18", "recurring bug" | `structural-fix-preferred-decision-framework.md`, `DOCS/RECURRING_BUG_PATTERNS.md` |
   | "per-core override", "per-core flag" | `per-bit-per-core-override-pattern.md`, `partner-core-bitmap-pattern.md` |
   | "snapshot publish", "cross-thread state" | `cross-thread-snapshot-publish-cluster-isolation.md` |
   | "audit before coding", "pre-coding gate" | `audit-driven-pre-coding-gate.md` |

   For each loaded DESIGN_SPECS doc, hold its body in context as the
   pattern signature for the checks below. Reference the doc by
   filename in findings; quote relevant rule snippets in the report.
   This makes Check 27 (DESIGN_SPECS pattern-application via /dod-audit)
   far more accurate because pattern bodies are warm, not cold.

   **Skip Stage 0** only when the plan has NO architectural surface
   (doc-only, single-file bug fix, test addition).

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

## Cold-pickup context completeness (added 2026-05-06)

A plan must be readable in isolation by a fresh session 7+ days
later, with no chat memory. Verify each item is present and
non-stale:

| # | Field | What to check | Common stale signals |
|---|-------|---------------|----------------------|
| C.1 | **Branch state** | Plan names a SPECIFIC branch (or "stay on X") that matches current operator practice | Says "create new branch X" but operator decided to use existing branch with rollback tags |
| C.2 | **Phase execution order matches dependency order** | If phase B depends on phase C, C is listed before B (or order is explicitly noted as "execution order != tag-number order" with rationale) | Sub-tags numbered .1 .2 .3 but .2 says "depends on .3 landing first" |
| C.3 | **First concrete move** | Each phase has an explicit "Step 0" or "start with X" — a single mechanical action a fresh session can do without re-investigating | Phase says "convert mean/variance/slope" without naming where the conversion sites are or what the FIRST function to edit is |
| C.4 | **Function/constructor names cited** | Plan names the EXACT function/constructor/macro to use (or explicitly notes "constructor doesn't exist; Step 0 is to add it") | Says "use a pure-integer constructor" without saying what it's called or whether it exists |
| C.5 | **File:line refs for cited tests/baselines** | Any "re-run X test" or "verify Y baseline" cites `path:line` or at minimum the test name string | Says "Re-run v5.9.2 replay-determinism test" with no location pointer |
| C.6 | **Stale-claim audit** | Phases don't claim work already done. Spot-check by grep: if plan says "X uses double internally" → `grep "double" path/to/X.hpp` to verify | Plan says "FPN_Sqrt is missing; we'll add it" but `grep FPN_Sqrt FixedPoint/FixedPointN.hpp` shows it already exists (even as a stub) |
| C.7 | **Effort claims reconcile with actual file size deltas** | If plan says "~200 LOC convert" verify `wc -l path/to/file.hpp` and that the file actually has ≥200 LOC of the type being converted | Claim of 200 LOC of double math when grep shows only 4 sites |
| C.8 | **Source-audit references** | Plan cites the canonical source-audit doc (workspace plan / Gemini audit / KNOWN_ISSUES section) backing each non-trivial claim | Bare "per the audit" with no path |
| C.9 | **Predecessor / dependent plans named with paths** | Sub-plan that says "depends on X" cites `plans/<filename>.md` of X, not just a version number | "Predecessor: v5.10.0c" with no plan-file path |
| C.10 | **Tag names locked** | Each phase has a unique git tag name; rollback anchors (`pre-<tag>`) noted if expected | Phases share a tag name or no tag listed |

**Verdict mapping:**
- C.1-C.6 missing → fresh session loses 30-60 min re-investigating per gap → YELLOW
- C.7 missing → effort estimate is unreliable → YELLOW
- C.8-C.10 missing → not session-blocking but bad hygiene → DOCUMENT-ONLY

When auditing a plan, walk these 10 items in addition to the 17
checklist items above. The cold-pickup audit is what makes
plans-as-truth actually work for multi-day externalized state.

**Encourage rather than gate:** if plan has 8/10 cold-pickup
items, that's GREEN — the missing 2 are flagged as "fix during
coding". Don't make the perfect the enemy of the shippable.

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

## Check index (post-split 2026-05-18)

Per `DESIGN_SPECS/doc-disciplines/file-size-split-discipline.md`, per-check bodies extracted to sidecar files at `claude-skills/readiness/checks/`. SKILL.md keeps invocation + orchestration; sidecars hold check-specific body. Each sidecar carries the canonical `Check N` identifier in its title; external cross-refs of the form `/readiness Check N` resolve via `rg "Check N" claude-skills/readiness/checks/` without further translation.

Numbered checks are explicit additions on top of the 10-item checklist embedded in `## Pass structure` step 3 (items 1-10) and the cold-pickup C.1-C.10 enumeration. The numbered Check series picks up at 11 (v5.4.0 onward); gap at 35 is intentional and reserved.

| Check N | Title | Provenance | Sidecar |
|---|---|---|---|
| 11 | Architectural sprint detection | v5.4.0 sprint guard | `checks/check-11-architectural-sprint-detection.md` |
| 12 | Display ↔ execution invariant | v5.4.0 sprint guard | `checks/check-12-display-execution-invariant.md` |
| 13 | Strategy lifecycle completeness | v5.4.0 sprint guard | `checks/check-13-strategy-lifecycle-completeness.md` |
| 14 | Function-pointer table / X-macro dispatch correctness | v5.4.0 sprint guard (X-macro variant audit) | `checks/check-14-function-pointer-table-xmacro-dispatch-correctness.md` |
| 15 | ML feature change requires parity regression update | v5.9 ML hardening | `checks/check-15-ml-feature-change-parity-regression.md` |
| 16 | New cfg field with stamp-bearing → recipe doc update | v5.9 ML hardening | `checks/check-16-new-cfg-field-stamp-bearing-recipe-doc.md` |
| 17 | Model-load path changes → strict-mode integration test | v5.9 ML hardening | `checks/check-17-model-load-path-strict-mode.md` |
| 18 | Reuse-audit | v5.12.1+ | `checks/check-18-reuse-audit.md` |
| 19 | Pre-existing-work audit (SHIP-BLOCKING) | v5.12.3+; STRENGTHENED v5.13.6+ | `checks/check-19-pre-existing-work-audit.md` |
| 20 | Future-proofness sanity (N-of-anything pattern) | v5.14.1.E.E.B+ | `checks/check-20-future-proofness-sanity.md` |
| 21 | Test count assertion fragility (`==` vs `>=`) | v5.14.1.E.E.B+ | `checks/check-21-test-count-assertion-fragility.md` |
| 22 | Auto-trigger downstream re-audit after umbrella ships | v5.14.1.E.E.B+ | `checks/check-22-auto-trigger-downstream-reaudit.md` |
| 23 | Latency accountability | v5.14.1.F+ | `checks/check-23-latency-accountability.md` |
| 24 | Mirror-function call-sequence enumeration | v5.14.2.E+ | `checks/check-24-mirror-function-call-sequence-enumeration.md` |
| 25 | TECH_DEBT.md surface-area scan | v5.14.2.E+ | `checks/check-25-tech-debt-surface-area-scan.md` |
| 26 | DEFERRED-FOR-FUTURE-SHIP (placeholder) | v5.14.2.E+ | `checks/check-26-deferred-for-future-ship-placeholder.md` |
| 27 | DESIGN_SPECS pattern-application audit (via /dod-audit) | v5.14.9+ | `checks/check-27-design-specs-pattern-application-audit.md` |
| 28 | Test-strength anti-regression audit (via /test-strength-audit) | v5.14.9.D+ | `checks/check-28-test-strength-anti-regression.md` |
| 29 | Mechanical citation drift discipline | v5.14.10+ | `checks/check-29-mechanical-citation-drift-discipline.md` |
| 30 | Predicate-contract-changed audit | v5.14.10+ | `checks/check-30-predicate-contract-changed-audit.md` |
| 31 | Wider-build verification at last sprint close | v5.15.2+ (TECH_DEBT-033 closure) | `checks/check-31-wider-build-verification.md` |
| 32 | Plan-body symbol-existence verification (B-Plus CI tool) | v5.15.5.F.4d.1.B.4+ (Class 14 Stage 6 enforcement) | `checks/check-32-plan-body-symbol-existence-verification.md` |
| 33 | Body-content arg enumeration completeness (M6 META) | v5.15.5.F.4d.1.B.4+ (M6 codification) | `checks/check-33-body-content-arg-enumeration.md` |
| 34 | Audit tier declared in plan frontmatter + scope match | v5.15.5.F.4d.1.B.4+ (tiered-audit codification) | `checks/check-34-audit-tier-declaration-and-scope-match.md` |
| 36 | Sister-registry parity verification | meta-discipline M1 | `checks/check-36-sister-registry-parity-verification.md` |
| 37 | Transitional state coexistence budget | meta-discipline M4 / Pillar B3 | `checks/check-37-transitional-state-coexistence-budget.md` |
| 38 | Include topology cycle risk | meta-discipline M4 / Pillar B7 | `checks/check-38-include-topology-cycle-risk.md` |
| 39 | Wire-format row ordering parity | meta-discipline M4 / Pillar B12 | `checks/check-39-wire-format-row-ordering-parity.md` |
| 40 | Cross-walker struct-field uniqueness | meta-discipline M4 / Pillar B13 | `checks/check-40-cross-walker-struct-field-uniqueness.md` |

### Bug-class groupings

- **v5.4.0 sprint guards (Checks 11-14):** an architectural sprint (sharding, decoupling, extraction) wires new entry points but silently orphans existing function calls. Symptom: "feature still appears to work on glance, but adaptive/transitional logic is dead."
- **v5.9 ML hardening (Checks 15-17):** silent train-serve drift through additions to the ML pipeline that LOOK forward-compat but actually require specific change-management discipline (snapshot test update, retrain, stamp-binding refresh).
- **Reuse + pre-existing-work (Checks 18-19):** missed merges + false-NEW / false-REUSE plan claims. Check 19 is SHIP-BLOCKING.
- **Future-proofness + observability (Checks 20-23):** N-of-anything ad-hoc patterns; fragile literal test-count assertions; downstream-staleness after umbrella ships; unaccounted latency additions.
- **Mirror-function audit + ledger hygiene (Checks 24-26):** mirror functions duplicate data-flow but miss call sequence; TECH_DEBT entries silently rot at shared surfaces.
- **DESIGN_SPECS + test-spec integrity (Checks 27-28):** pattern application gate via /dod-audit; test-weakening anti-regression via /test-strength-audit.
- **Citation drift + contract extensions (Checks 29-30):** file:line refs go stale across sprint boundaries; predicate contract extensions break test fixtures.
- **Wider-build verification (Check 31):** test-target-only sprint close hides GUI/sanitizer compile errors.
- **Plan-body integrity (Checks 32-34):** Class 14 fabrication compile-time enforcement (Check 32 CI tool); M6 body-content arg enumeration at helper extract (Check 33); tiered-audit declaration in plan frontmatter for scope-appropriate audit cadence (Check 34).
- **Meta-discipline (Checks 36-40):** M1 sister-registry parity / M4 implementation-layer blind-spot taxonomy (transitional-state budget B3, include topology B7, wire-format row order B12, cross-walker struct-field uniqueness B13).
