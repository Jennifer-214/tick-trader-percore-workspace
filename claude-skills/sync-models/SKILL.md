---
name: sync-models
skill_kind: mechanical
trigger_heuristics: ["back up trained models off-machine -> suggest /sync-models (pushes to remote)"]
description: /sync-models — back up trained models off-machine
type: skill
concern: workflow
audit_cadence: ad-hoc
tags: [doc-discipline, operator-collaboration]
surface: [training, ml-inference]
sister_skills: [/sync-workspace, /ship]
loads_dynamically: []
---

# /sync-models — back up trained models off-machine

## What this does

The `Trader_Models` repo at `/home/caramel/code/Trader_Models/` (private,
`Jennyfirrr/Trader_Models`) mirrors the engine's `models/` dir for
backup + cross-machine sync. Unlike `/sync-workspace` which mirrors via
symlinks, `/sync-models` does an explicit copy + commit because:
- Models are binary blobs (~600KB JSON each); symlinking from a separate
  repo into `models/` would couple the engine path to the backup repo's
  layout.
- Operator may want to delete a model locally without losing the backup
  — explicit sync gives that control.

This skill does:

1. `cp -a` (or rsync if installed) `models/` contents → `Trader_Models/`
2. `cd Trader_Models`, `git add -A` (catches additions, modifications,
   AND deletions to mirror local state)
3. Auto-generate a commit message from the diff
4. Commit + push to `origin/main`
5. Report 1-line summary

## Why on-demand instead of automatic

Same reasoning as `/sync-workspace`: continuous sync (cron / file-watcher)
creates noise commits — a single model train produces 3-4 files, and
running auto-sync per-file would make the history unreadable. Better
cadence: end of training session, after deleting old runs, before
stepping away from the machine.

## What gets synced

| Source (engine repo) | Destination (Trader_Models) |
|---|---|
| `models/<class>/<run>/barrier.json`         | mirrored 1:1 |
| `models/<class>/<run>/barrier.json.stamp`   | mirrored 1:1 |
| `models/<class>/<run>/barrier.json.scaler`  | mirrored 1:1 (if present) |
| `models/<class>/<run>/summary.txt`          | mirrored 1:1 |
| `models/<class>/<run>/bandit_state.json`    | mirrored 1:1 (runtime state, valuable across restarts) |
| `models/<top-level>.json` (legacy)          | mirrored 1:1 |
| `models/<top-level>.json.scaler` (legacy)   | mirrored 1:1 |

**State mirrors local.** Deletions propagate (when you click Delete in
Past Runs, the next sync removes the dir from the backup too — git
history preserves it though, recovery via `git checkout <sha> -- <path>`).

## Procedure

```bash
ENGINE=/home/caramel/code/FoxML_Trader_v2
MODELS_REPO=/home/caramel/code/Trader_Models
cd "$MODELS_REPO"

# Snapshot current backup state for diff later
PRE_FILES=$(find . -type f -not -path './.git/*' -not -name 'README.md' -not -name '.gitignore' | wc -l)

# Mirror engine's models/ → backup repo. cp -a preserves attributes.
# Key trick: clear non-tracked files first so deletions propagate cleanly.
# Approach: stage a fresh copy, let git diff reveal additions/deletions.
#
# Use rsync if installed (faster, has --delete); fall back to cp -a + manual
# delete-detection via git.
if command -v rsync >/dev/null 2>&1; then
    rsync -a --delete \
        --exclude='.git/' --exclude='README.md' --exclude='.gitignore' \
        "$ENGINE/models/" ./
else
    # Manual mirror: clear non-meta dirs first, then copy
    find . -mindepth 1 -maxdepth 1 \
        -not -name '.git' -not -name 'README.md' -not -name '.gitignore' \
        -exec rm -rf {} +
    cp -a "$ENGINE/models/." ./
fi

# Stage all changes (additions, mods, deletions)
git add -A

# Quick check: is anything actually different?
if git diff --quiet --cached; then
    echo "[sync-models] backup already up to date — nothing to commit"
    exit 0
fi
```

### Auto-generate commit message

Look at the staged diff and group:

- New `<class>/<prefix>_horizon_<H>/` dirs → "models: add <class> run <prefix> (N horizons)"
- Deleted dirs → "models: remove <prefix> (N horizons)"
- Modified existing → "models: update <prefix>"
- Bandit state changes only → "models: bandit state update"

If multiple categories changed: "models: ..." composed.

If user passed an explicit message via `args`, use that.

### Commit + push

```bash
git commit -m "$(cat <<EOF
$auto_message

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
git push origin main
```

### Report

After push completes, report 1-line summary:
- Files added / modified / deleted (counts from `git diff --shortstat`)
- New commit SHA short
- "Pushed to github.com/Jennyfirrr/Trader_Models"

If push fails (auth, network), surface clearly. Common failure modes:
- SSH passphrase prompt → `! ssh-add` to unlock, retry
- Repo ahead (synced from another machine) → `git pull --ff-only` first

## Invocation

- `/sync-models` — auto-message
- `/sync-models <message>` — explicit message

## When to use

- End of a training session (you just trained N models)
- After Past Runs deletion (mirror the cleanup)
- Before stepping away from the machine
- After a known-good model is deployed (pin a backup point)

## When to skip

- Mid-training — `models/` is in inconsistent state (partial writes)
- Right after a previous /sync-models with no model changes
- When `models/` contains experimental runs you haven't decided to keep yet

## What this skill is NOT

- Not a continuous watcher — invoked explicitly each time
- Not a backup of training logs / metrics CSVs / Tick CSVs (those are
  derivable; only models are the irreplaceable artifact)
- Not a sync FROM remote — if you sync from another machine first, you
  must `git pull` here manually before the next /sync-models to avoid
  a conflict

## Cross-machine restore (one-time setup)

```bash
git clone git@github.com:Jennyfirrr/Trader_Models.git ~/code/Trader_Models
# Then either:
ln -s ~/code/Trader_Models ~/code/FoxML_Trader_v2/models
# OR copy:
cp -a ~/code/Trader_Models/. ~/code/FoxML_Trader_v2/models/
```

The engine's `EnsembleModelZoo_AutoDetectFromDir` doesn't care if
`models/` is a symlink — same paths resolve.

## Storage growth note

A multi-horizon training run is ~2.5MB (4 horizons × ~650KB each).
At 1 run per training session, ~1GB/year. Plenty of headroom for free
GitHub private repos (1GB soft warning, no hard cap).

If this grows past comfort: prune old test runs locally before sync,
or move to a dedicated archive (Backblaze / S3 / Garage) for cold
storage with `git-annex` or LFS. Not today's problem.
