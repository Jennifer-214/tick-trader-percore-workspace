---
name: sync-workspace
description: Push the gitignored workspace repo (plans + claude-skills) to its private GitHub remote. Detects what changed since last push, generates a sensible commit message, commits + pushes. Run on-demand whenever you want an off-machine backup checkpoint.
---

# /sync-workspace — back up plans + skills off-machine

## What this does

The `tick-trader-percore-workspace` repo at
`/home/caramel/code/tick-trader-percore-workspace/` holds the
gitignored `plans/` + `claude-skills/` from this project. Symlinks
make editing live, but pushing to the private GitHub remote requires
a `git commit + push` cycle.

This skill does that cycle:

1. `cd` to the workspace
2. `git status` — return early if clean (nothing to back up)
3. Group changes by category (plans vs skills) for a smart commit message
4. Commit with auto-generated message + Co-Authored-By Claude
5. Push to `origin/main`
6. Report one-line summary back

## Why on-demand instead of automatic

Continuous sync (cron / file-watcher / pre-commit hook) creates noise
commits and push spam. A plan file edited 12 times in a session would
become 12 commits. Better cadence: push at meaningful checkpoints —
end of work session, after a plan is finalized, after a skill is
updated. Operator picks the moment.

## Procedure

```bash
WORKSPACE=/home/caramel/code/tick-trader-percore-workspace
cd "$WORKSPACE"

# Are there changes?
if git diff --quiet && git diff --cached --quiet && [ -z "$(git status --porcelain)" ]; then
    echo "[sync] workspace clean — nothing to push"
    exit 0
fi

# What changed?
git status --short
git diff --stat HEAD
```

### Auto-generate commit message

Look at the changed paths and group them:

- `plans/*.md` modified → "plans: update X, Y, Z"
- `plans/*.md` new → "plans: add X"
- `claude-skills/*/SKILL.md` modified → "skills: update X"
- `claude-skills/*/` new directory → "skills: add X"
- `README.md` modified → "docs: update workspace README"

If multiple categories changed, join them: "plans + skills: ...".

If the user passes an explicit message via `args`, use that instead
and skip the auto-generation.

### Commit + push

```bash
git add -A
git commit -m "$(cat <<EOF
$auto_message

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

### Report

After push completes, report to the user:
- What was committed (1-line summary)
- Commit SHA short
- "Pushed to github.com/Jennyfirrr/tick-trader-percore-workspace"

If the push fails (auth, network), surface the error clearly. Don't
retry blindly. Common failure modes:

- SSH passphrase prompt blocking → ask the user to run `! ssh-add` to
  unlock the key, then retry.
- Repo is ahead of remote (someone else pushed from another machine) →
  `git pull --ff-only` first; if that fails, surface a merge conflict.

## Invocation

- `/sync-workspace` — auto-message based on changes
- `/sync-workspace <message>` — explicit commit message

## When to use

- End of a planning session (push the plan changes)
- After /readiness updates (push the new skill version)
- Before stepping away from the machine for a while
- Any time you want an off-machine snapshot

## When to skip

- Mid-edit; the workspace is in an inconsistent half-done state
- Right after a previous /sync-workspace; nothing has changed
- When the workspace contains in-progress experimental notes you
  don't want to checkpoint yet (just wait until the thought is done)

## What this skill is NOT

- Not a continuous watcher — invoked explicitly each time
- Not a backup of binary files (model .bin, datasets) — only text in
  `plans/` and `claude-skills/`
- Not a sync FROM remote — if you edit on another machine, you have to
  `git pull` manually in the workspace before the next /sync-workspace
  to avoid a conflict
