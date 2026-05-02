---
name: ship
description: Run the post-coding ship ritual — build verify, calls_graph_diff orphan check, version bump, commit with structured message, tag, push branch + tag. Captures the discipline Jenny has been doing manually after every v5.x.X subship.
---

# /ship — Post-coding ship ritual

## What this does

Executes the gate sequence Jenny runs after every code subship:

1. **Build verification** — `./build.sh test gui suite` (or the
   appropriate scope based on what was touched)
2. **Test count** — capture before/after (e.g. 1080/0)
3. **Orphan check** — `./tools/calls_graph_diff.sh` must be CLEAN
   or accept-listed delta
4. **Version bump** — edit `Version.hpp` to the new version
5. **Map regen** if functions added — `./tools/gen_code_map.sh`
6. **Commit** — structured message with theme + audit refs + verify gate
7. **Tag** — `vX.Y.Zletter` matching Version.hpp
8. **Push** — branch first, tag second (separate calls for SSH-passphrase
   tolerance)
9. **Report** — SHA, tag, push status, next-ship hint

This skill DOES execute commands (commits + pushes). Other skills like
`/readiness` and `/ml-audit` only read. Be explicit about that.

The user's auto-memory has feedback `feedback_push_per_phase`: after
each phase commit+tag in a multi-phase plan, push branch+tags to
origin (validated standing instruction from filesystem-crash incident
2026-04-30). So pushing is auto-allowed.

## Invocation

- `/ship` → infer version from current Version.hpp + uncommitted
  changes; auto-generate commit message from staged diff + recent
  context. Asks for confirmation before push if commit message
  inference is uncertain.
- `/ship <version>` → ship at this exact version (e.g. `/ship 5.9.0d`,
  `/ship 5.9.1`). Bumps Version.hpp accordingly.
- `/ship <version> <theme>` → version + commit-message theme override
  (e.g. `/ship 5.9.1 "edge cases + warmup observability"`).

## Pass structure

### Stage 1 — Pre-flight checks (FAIL-FAST, surface before any commit)

1. **Working tree state.** `git status --short`. There must be at
   least one modified or new file (otherwise nothing to ship — abort
   with "no changes to commit").

2. **Branch identity.** `git rev-parse --abbrev-ref HEAD`. Should
   match the active feature branch. Refuse if on `main` /
   `experiment/per-core-sharding` directly (those merge through PR,
   not direct push).

3. **Version inference.** Read current `Version.hpp` `ENGINE_VERSION_STRING`.
   - Without `<version>` arg: ask user "ship as <X> or new version?"
   - With `<version>` arg: validate format `[0-9]+\.[0-9]+\.[0-9]+[a-z]?`
   - Confirm the bump makes sense (5.9.0d → 5.9.0e or 5.9.1, not
     5.9.0d → 6.0.0).

4. **Hot-path touch detection.** If diff touches any of:
   `CoreFrameworks/ExecutionCore.hpp`, `Strategies/StrategyParameters.hpp`
   (BG_/SG_Evaluate dispatcher), `MemHeaders/PoolAllocator.hpp` (hot
   path), then **prompt for explicit confirmation** that the change
   is branchless and benchmarked. The user's standing rule (CLAUDE.md)
   is hot path p99 ≤500ns.

5. **Memory / invariants check.** Diff lists touched files. If any
   listed file is in `tests/INVARIANTS_MAP.md` or `DOCS/CLAUDE_INVARIANTS.md`,
   surface the invariants the change might affect. Don't block —
   just remind.

### Stage 2 — Build verification (HARD GATE)

Run all three relevant builds in parallel where possible. Use a
build matrix based on what changed:

| Files touched include | Build |
|---|---|
| any `*.cpp` / `*.hpp` not in GUI/ or Backtest/ | `./build.sh test` |
| `GUI/`, `engine_gui` referenced | `./build.sh gui` |
| `Backtest/`, `foxml_suite` referenced | `./build.sh suite` |
| sanitizer-relevant (race / memory / threading change) | `./build.sh tsan` and/or `./build.sh asan` |

Default: `./build.sh test gui suite` (covers 90% of ships).

Output of each build is captured. **If any build returns non-zero
exit, ABORT** — don't commit broken state. Surface the build error
to the user and let them fix before retrying `/ship`.

If `./build.sh test` succeeds, capture the test count. The
controller_test prints `<N> assertions across <M> tests` — record
both. Compare against the test count claimed in the commit message
or the previous tag.

### Stage 3 — Orphan check (HARD GATE)

```bash
./tools/calls_graph_diff.sh 2>&1
```

Output should be `CLEAN` or list only deliberate additions. If
unexpected orphans appear, surface them and **abort the ship** —
fix or accept-list before proceeding.

Common false positives:
- Test-only functions (covered by accept list in calls_graph_diff.sh)
- New X-macro entries (FOREACH_FEATURE, FOREACH_STRATEGY) — these
  are referenced via macro expansion the static analyzer can't see
- Forward-declared fns that get linked in different units

If output is anything other than CLEAN, paste it to the user verbatim
and ask: "accept this delta?" before proceeding.

### Stage 4 — Optional: regen CODE_MAP

```bash
# Get list of new Pattern_FunctionName functions
git diff --staged --unified=0 | grep -E '^\+(static |inline |void |int |size_t |uint32_t )?\w+_\w+\(' | wc -l
```

If > 0, run `./tools/gen_code_map.sh` and stage the resulting
`DOCS/CODE_MAP.md`. Otherwise skip.

### Stage 5 — Version bump

Edit `Version.hpp`:

```cpp
#define ENGINE_VERSION_STRING "<new-version>"
```

If this is the only edit being staged for this stage, do it now.
If the version was already bumped in a previous edit (likely — most
ships bump version inline with the change), skip.

### Stage 6 — Commit

The commit message structure for this codebase, distilled from the
last N tags:

```
v<X.Y.Z[letter]> — <theme> (<scope or audit ref>)

<one-paragraph context: what motivated this change, what gap or audit
finding it closes, what the user-visible impact is>

<implementation summary: the design decisions made + key tradeoffs.
Use bullet points for >3 items. Reference file:line for new functions.>

<verification gate: tests N/0, calls_graph_diff state, hot path
state, GUI build state, suite build state.>

<phase status / next ship hint>

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

Theme generation rules:
- If user passed `<theme>`, use it verbatim
- If commit closes an audit finding (V5_X_AUDIT-#N), include the ID
- If commit is a sub-letter polish ship (5.9.0d), say "Phase X polish"
  or specific theme
- If commit is a major-version bump (5.10.0), summarize the sprint

Auto-derive theme by inspecting:
- `git diff --staged --stat` (which files dominate)
- New `Pattern_FunctionName` functions added (suggests new feature)
- Recent plan file (most recently modified `plans/*.md`) — extract
  this ship's goal

If the auto-derived theme looks weak, ask the user to clarify rather
than commit a vague message. Bad commit messages last forever.

### Stage 7 — Tag

```bash
git tag v<X.Y.Z[letter]>
```

The tag matches the Version.hpp string with a `v` prefix. No
annotation message — the commit it points to has the full context.

### Stage 8 — Push (branch first, tag second)

This is two separate `git push` calls, NOT `git push --follow-tags`.
The reason: SSH passphrase prompts. If the agent is invoked
non-interactively, the first push triggers the prompt; once SSH
agent is unlocked, the second push goes through. Combining them
into one call hides the structure when one half fails.

```bash
git push origin <branch-name>
git push origin v<X.Y.Z[letter]>
```

If `git push origin <branch>` fails with "Permission denied (publickey)"
or "Could not read from remote repository":

- Surface to user: "Push needs SSH agent. Run `! ssh-add` and I'll
  retry."
- DO NOT loop / retry repeatedly. One try, surface the error, wait.

If push succeeds, report the GitHub URL (constructed from the remote):
```
git remote get-url origin
# e.g. git@github.com:Jennyfirrr/tick-trader-percore.git
# → https://github.com/Jennyfirrr/tick-trader-percore/tree/<branch>
```

### Stage 9 — Report

Report to the user with this format:

```markdown
## Shipped: v<version>

- Commit: `<short-sha>` on branch `<branch-name>`
- Tag: `v<X.Y.Z[letter]>`
- Build: test ✅ / gui ✅ / suite ✅
- Tests: <N>/0 (Δ <+M> from previous)
- calls_graph_diff: CLEAN
- Push: branch ✅ / tag ✅

<one-line theme>

Next: <auto-suggest based on plan or audit findings — e.g. "Phase 2
(v5.9.1) — edge cases + warmup observability">
```

If any gate failed, report what failed + what needs human attention,
not a success summary.

## Heuristics

### When build can be skipped

NEVER. Build verification is non-negotiable. Even doc-only ships
should run `./build.sh test` because docs sometimes break the build
(generated headers, included markdown, etc.). The cost of running it
is ~30s; the cost of a broken HEAD is hours of debugging "what
changed" later.

The one exception: if the `git diff --stat` shows ONLY
`plans/*.md` or `DOCS/*.md` files (no code), build can be skipped
with explicit user confirmation.

### Sub-letter ships vs minor bumps

Codebase convention (validated across v5.x.X history):
- **`X.Y.Z`** — new feature or significant addition
- **`X.Y.Z` + `X.Y.Za`, `X.Y.Zb`...** — same-day or short-cycle
  polish ships that finish a feature without bumping minor.
  E.g. v5.9.0a (audit doc), v5.9.0b (visibility), v5.9.0c (cfg
  awareness), v5.9.0d (worker thread)
- **`X.Y.(Z+1)`** — separate ship that's part of the same sprint
  but a distinct theme. E.g. v5.9.1 = Phase 2 (edge cases) where
  v5.9.0/0a/0b/0c/0d = Phase 1 (silent-failure)

When in doubt: if the ship closes the same plan-phase as the
previous one, use a sub-letter; if it opens a new plan-phase, bump
the patch number.

### Hot-path-touch confirmation prompt

If the diff includes ExecutionCore.hpp, BG_/SG_Evaluate, fan_out, or
any of the file:line ranges in `DOCS/CLAUDE_INVARIANTS.md`, surface
this BEFORE running build:

```
Diff touches hot path. Confirm:
  - [ ] No new `if` branches added (or new branches are branchless masks)
  - [ ] No malloc / free / mutex / float math
  - [ ] If LATENCY_PROFILING benchmark exists, run it and confirm
        p99 ≤ 500ns

Type "confirmed" to proceed, or describe the change for review.
```

This is a YELLOW gate — not auto-fail, but requires explicit
acknowledgment.

### Snapshot-version safety

If the diff touches `CoreFrameworks/ShardedSnapshot.hpp` or
`ShardedSnapshotPersist.hpp`:

- Verify `SHARDED_SNAPSHOT_VERSION` is bumped (if struct shape
  changed) OR explicitly note "no shape change, version held"
- Verify a migration story exists for old snapshots on disk

This is a HARD gate — old snapshots silently failing to load is the
exact bug pattern v5.0 introduced and v5.1 had to fix.

### Stamp-format-version safety

If the diff touches `ML_Headers/ModelInference.hpp` stamp body fields:

- Verify `MODEL_FORMAT_VERSION` bumped (or `stamp_format_version`
  field updated)
- Verify both bash (`tools/stamp_model.sh`) and in-process emitters
  match
- Verify the v5.8.8 regression test still passes

HARD gate. Stamp/registry mismatch causes "model loaded but predicts
random values" — invisible to the operator until paper-test surprise.

### Multi-tag scenarios (rare)

If the user asks for `/ship` after multiple version bumps were made
without an interim ship (Version.hpp shows v5.9.0e but last tag was
v5.9.0d), surface the gap and ask: "ship just v5.9.0e (current
working tree), or land v5.9.0d-v5.9.0e separately?"

Default behavior: ship the current state under the current
Version.hpp. Don't try to retroactively split commits.

### git index hygiene

Before `git add`, list what would be staged:

```bash
git status --short
git diff --stat
```

Never use `git add -A` blindly. Specifically refuse to stage:
- `.env`, `*.key`, `*credentials*`, `*.pem` (security)
- Files in `gitignored` directories that show up via stale git state
- `plans/` directory contents — it's symlinked but should be ignored
  via `.gitignore` (the v5.9.0 incident with the plans symlink)
- Build directories (`build/`, `build_gui/`, `build_suite/`, etc.)
- Model files (`*.bin`, `*.xgb`, `*.json` in models/)
- Tick recordings (`*.csv` in `data/`)

If any of these would be staged, surface to the user before
proceeding.

### Commit signing

The user has an established commit signing setup. NEVER use
`--no-gpg-sign` or `-c commit.gpgsign=false`. If signing fails,
surface the error and ask the user to investigate — don't bypass.

### Auto-suggest "next ship"

After a successful ship, look at:
- The most recently modified `plans/*.md` for context
- `DOCS/V5_X_ML_HARDENING_AUDIT.md` (or successor) for open findings
- TODO comments added in this ship's diff

Auto-suggest:
- "Phase X (vX.Y.Z) — <theme>" if the plan continues
- "/ml-audit parity" if the ship modified ML pipeline
- "/readiness <plan>" if a new phase plan is queued

Make the suggestion ONE LINE — the user can ignore it. Don't
prescribe; just hint.

## What this skill is NOT

- Not a release-tagging tool for the public — that's
  `experiment/per-core-sharding` PR + GitHub release flow
- Not a `git rebase` / amend tool — every ship is a new commit
- Not a `--force` push tool — refuses to force push, ever
- Not a `--no-verify` skip-hooks tool — pre-commit hooks run
  unmodified
- Not a CI replacement — runs local builds only, doesn't trigger
  remote CI

## When to use

- After completing a sub-letter ship's coding (e.g. just finished
  the v5.9.0d worker refactor)
- After completing a phase that maps to a single tag (e.g. v5.9.1
  Phase 2)
- After a hotfix needs to land on the current branch

## When to skip

- Mid-coding; the work isn't done. Just `git add` + `git commit` if
  you want a checkpoint without all the gates
- Multi-commit work — `/ship` is for atomic ships, not multi-commit
  PRs. Use `git commit` directly for intermediate commits, then
  `/ship` only on the last one
- Doc-only changes that don't warrant a tag — direct
  `git commit + git push` is faster

## Alignment with project conventions

This skill embeds rules from:
- `CLAUDE.md` — hot path purity, code conventions, version singleton
- `DOCS/CLAUDE_REVIEW.md` — multi-day-change checklist
- `DOCS/CLAUDE_INVARIANTS.md` — load-bearing invariants
- `tests/INVARIANTS_MAP.md` — test coverage cross-reference
- Auto-memory `feedback_push_per_phase.md` — push per phase
  (filesystem-crash incident)

If any of these docs change in ways that affect the ship ritual,
update this skill alongside.

## Author intent

Jenny has been running this ritual manually after every subship
(v5.7.x, v5.8.x, v5.9.0/0a/0b/0c/0d). Same gates each time. Same
commit message structure. Same push-branch-then-tag pattern. The
skill captures that ritual so it stays consistent — no drift between
"good ship discipline week 1" and "tired Friday ship discipline".

The skill MAY be slower than typing the commands manually (build
verification adds ~30s on a clean cache). The discipline is the
point: every ship gets the same gate. Bad ships caught here don't
become next-week's debugging session.

If a gate is genuinely too slow for the change scope (e.g. doc-only
ship building the GUI), the skill takes a `--fast` flag (TODO if
needed) — but the default is full discipline.
