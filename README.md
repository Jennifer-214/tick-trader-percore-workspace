# tick-trader-percore-workspace

Private off-machine backup for working notes and Claude Code skill
definitions associated with `tick-trader-percore`.

## Layout

- `plans/` — design plans, master plans, readiness reports. Symlinked
  from `tick-trader-percore/plans/`. Both gitignored at the project
  level so the public repo stays clean.
- `claude-skills/` — custom Claude Code skill definitions (`dust`,
  `readiness`). Symlinked from `tick-trader-percore/.claude/skills/`.

## Why this exists

`tick-trader-percore` `.gitignore`s `plans/` and `.claude/` so working
notes and machine-specific config don't get committed to the public
repo. This workspace is the off-machine backup for those gitignored
directories.

## How it's wired

```
~/code/tick-trader-percore-workspace/
  plans/                              <- real directory
  claude-skills/                      <- real directory

~/code/tick-trader-percore/
  plans -> ../tick-trader-percore-workspace/plans
  .claude/skills -> ../../tick-trader-percore-workspace/claude-skills
```

Symlinks are relative so the layout works on any machine where both
repos live under the same parent directory.

## Routine

- Edit plans / skills as normal in the project. Changes land in the
  workspace via the symlink.
- `cd ~/code/tick-trader-percore-workspace && git add . && git commit
  -m "..." && git push` to back up.
- Or set up a cron / git alias to push periodically.

## What is NOT in here

- `.claude/scheduled_tasks.lock`, `.claude/settings.local.json`, etc.
  These are runtime state and machine-specific config; they stay in
  the project's `.claude/` and don't belong in version control.
