---
name: sync-workspace
skill_kind: mechanical
trigger_heuristics: ["off-machine backup / checkpoint the workspace -> suggest /sync-workspace (pushes to remote)"]
description: Push the gitignored workspace repo (plans + claude-skills) to its private GitHub remote. Detects what changed since last push, generates a sensible commit message, commits + pushes. Run on-demand whenever you want an off-machine backup checkpoint.
type: skill
concern: workflow
audit_cadence: ad-hoc
tags: [doc-discipline, operator-collaboration]
surface: []
sister_skills: [/ship]
loads_dynamically: []
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

## What gets synced (rule added 2026-05-06)

Operator policy: **anything gitignored at the engine repo, outside
of pure data/build artifacts, gets backed up to the workspace.**

| Source (engine repo) | Destination (workspace) | Mechanism |
|---|---|---|
| `plans/*` | `plans/` (symlinked) | Auto-propagates via symlink |
| `.claude/skills/*` | `claude-skills/` (symlinked) | Auto-propagates via symlink |
| `DOCS/CLAUDE_*.md` | `DOCS/CLAUDE_*.md` (per-file symlinked) | Auto-propagates via symlink (v5.11.43 migration) |
| `DOCS/CHANGELOG.md`, `DOCS/changelogs/` | `DOCS/CHANGELOG.md`, `DOCS/changelogs/` (symlinked) | Auto-propagates via symlink |
| `DOCS/CODE_MAP.md` | `DOCS/CODE_MAP.md` (symlinked) | Auto-propagates via symlink |
| `DOCS/KNOWN_ISSUES.md`, `DOCS/RECURRING_BUG_PATTERNS.md` | `DOCS/<name>` (symlinked) | Auto-propagates via symlink |
| `DOCS/*_INVARIANTS.md`, `DOCS/PARITY_*.md` | `DOCS/<name>` (symlinked) | Auto-propagates via symlink |
| `DOCS/ARCHITECTURE.md`, `DOCS/COMPONENTS.md`, `DOCS/FEATURE_INTERFACE.md`, `DOCS/STRATEGY_INTERFACE.md`, `DOCS/TARGET_INTERFACE.md`, `DOCS/HOT_PATH_CHANGELOG.md` | `DOCS/<name>` (symlinked) | Auto-propagates via symlink |
| `DOCS/ML_TEST_RECIPES.md`, `DOCS/PERFORMANCE.md`, `DOCS/FAILED_OPTIMIZATIONS.md`, `DOCS/NEXT_STEPS.md` | `DOCS/<name>` (symlinked) | Auto-propagates via symlink |
| `DOCS/STRATEGY_REFACTOR_IDEAS.md`, `DOCS/STRATEGY_TEMPLATE.hpp` | `DOCS/<name>` (symlinked) | Auto-propagates via symlink |
| `DOCS/sizing-audit-*.md`, `DOCS/v5.4-*.md`, `DOCS/v5.11-*.md`, `DOCS/V5_*_AUDIT.md` | `DOCS/<name>` (symlinked) | Auto-propagates via symlink |
| `engine.cfg` | `configs/engine.cfg` | Explicit copy; this skill |
| `backtest.cfg` | `configs/backtest.cfg` | Explicit copy; this skill |
| `controller.cfg` | `configs/controller.cfg` | Explicit copy; this skill |
| `secrets.cfg` | `configs/secrets.cfg` | Explicit copy; this skill |
| `.env`, `.env.*` | `configs/<name>` | Explicit copy; this skill |
| `CLAUDE.local.md` | `CLAUDE.local.md.backup` | Explicit copy; this skill |
| `*.local.md` (other overlays) | `<name>.backup` (workspace root) | Explicit copy; this skill |
| `GEMINI.md` | `GEMINI.md.backup` | Explicit copy; this skill (Gemini agent's project memory) |
| `~/.claude/projects/<project>/memory/*.md` | `memory.backup/` | Explicit copy; this skill (Claude auto-memory). Source lives at `$HOME/.claude/`, NOT under any project repo. Added 2026-05-12 for off-machine memory persistence. |

**DOCS/ migration note (v5.11.43)**: 96 architectural / operator-edge
docs were moved from public engine repo to private workspace via
per-file symlinks (`DOCS/<name>` → `../../tick-trader-percore-workspace/DOCS/<name>`).
Public engine repo cloned without workspace gets `DOCS/` containing
only the 7 operator-facing tracked docs: QUICKSTART, OPERATOR_DEPLOYMENT,
CONFIGURATION, ML_USAGE, ML_TRAINING, CONTRIBUTING, LATENCY_PROFILING.
Edits to symlinked docs auto-propagate to workspace (no copy needed);
this skill's `git add -A` in the workspace picks up the changes.

**Workspace-native dirs (NO engine source; live only in workspace; written via Write tool directly to workspace path):**

| Workspace dir | Purpose | Written by |
|---|---|---|
| `DESIGN_SPECS/` | Pattern catalog (count grows over sprints; one .md per pattern + README index) | Authored as part of any sprint that solves a non-trivial design problem; cross-linked from postmortems |
| `configs/` | Operator-side cfg + secrets backups (engine.cfg / backtest.cfg / controller.cfg / secrets.cfg / .env*) | This skill (sync_if_newer block above) |
| `*.backup` (workspace root) | Project-private memory overlays (CLAUDE.local.md.backup / GEMINI.md.backup / *.local.md backups) | This skill (sync_if_newer block above) |

These dirs have no engine-side source mirror. New files added here flow through the workspace's own `git add -A` + commit + push naturally; no special sync logic needed (the table above only covers cases where an engine-side source needs explicit copy because the engine repo doesn't track that path).

**Skipped (regenerable / runtime data):**
- `build*/`, `bin/`, `vendor/`, `.cache/`, `.clangd/`, `compile_commands.json`
- `*.log`, `paper_runs/`, `data/`, `baseline_run/`, `*_metrics.csv`, `*_order_history.csv`
- `models/` — handled separately if operator wants per-model backup
- IDE state: `.vscode/`, `.idea/`, `foxml_*.ini`, `continue.md`

When the engine `.gitignore` adds a NEW non-data category, update the
table above so this skill mirrors it.

## Procedure

```bash
WORKSPACE=/home/caramel/code/tick-trader-percore-workspace
ENGINE=/home/caramel/code/FoxML_Trader_v2
cd "$WORKSPACE"

# Cross-shell: make unmatched globs expand to empty instead of erroring.
# zsh errors with "(eval): no matches found" on `.env.*` when no files
# match; bash silently treats glob as literal unless nullglob is set.
# Both behaviors break the for-loops below — enable both shells' equivalent.
[ -n "$ZSH_VERSION" ]  && setopt NULL_GLOB
[ -n "$BASH_VERSION" ] && shopt -s nullglob

# Mirror non-symlinked private files: cfgs, secrets, local memory overlays.
# newer-mtime wins; only copies if source file exists.
sync_if_newer() {
    local src="$1" dst="$2"
    [ -f "$src" ] || return 0
    if [ ! -f "$dst" ] || [ "$src" -nt "$dst" ]; then
        cp "$src" "$dst"
        echo "[sync] mirrored $src -> $dst"
    fi
}

mkdir -p configs
sync_if_newer "$ENGINE/engine.cfg"     configs/engine.cfg
sync_if_newer "$ENGINE/backtest.cfg"   configs/backtest.cfg
sync_if_newer "$ENGINE/controller.cfg" configs/controller.cfg
sync_if_newer "$ENGINE/secrets.cfg"    configs/secrets.cfg

# .env files
for env_file in "$ENGINE"/.env "$ENGINE"/.env.*; do
    [ -f "$env_file" ] && sync_if_newer "$env_file" "configs/$(basename "$env_file")"
done

# Project-private memory overlays
sync_if_newer "$ENGINE/CLAUDE.local.md" CLAUDE.local.md.backup
sync_if_newer "$ENGINE/GEMINI.md"       GEMINI.md.backup
for local_md in "$ENGINE"/*.local.md; do
    base=$(basename "$local_md")
    [ -f "$local_md" ] && [ "$base" != "CLAUDE.local.md" ] && \
        sync_if_newer "$local_md" "$base.backup"
done

# Claude auto-memory mirror (added 2026-05-12 — off-machine persistence
# for ~/.claude/projects/<project>/memory/). Source is in $HOME/.claude/,
# NOT in any project repo. Sync to workspace/memory.backup/ so memories
# survive machine reimage. Operator-policy: memory dir is workspace-private
# (not pushed to public engine repo).
CLAUDE_MEMORY_DIR="$HOME/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory"
if [ -d "$CLAUDE_MEMORY_DIR" ]; then
    # Canonicalize + validate memories BEFORE backup (D-89 / R6 self-heal).
    # The harness re-serializes agent-Write'd memory frontmatter inline->block;
    # the helper canonicalizes block->inline + re-derives/symmetrizes sisters from
    # body [[links]], then the guard red-builds a one-way sister / broken ref /
    # undefined tag (CP-1/WH-1). This is what makes the self-heal REAL, not aspirational.
    ENGINE_TOOLS="/home/caramel/code/FoxML_Trader_v2/tools"
    if [ -f "$ENGINE_TOOLS/migrate_memory_frontmatter.py" ]; then
        python3 "$ENGINE_TOOLS/migrate_memory_frontmatter.py" --apply \
            || echo "WARN: memory canonicalize had issues; continuing to backup"
        python3 "$ENGINE_TOOLS/check_doc_metadata.py" --bidirectional --memories \
            || echo "WARN: memory guard (CP-1/WH-1) flagged issues — review before trusting the backup"
    fi
    mkdir -p memory.backup
    for mem_file in "$CLAUDE_MEMORY_DIR"/*.md; do
        [ -f "$mem_file" ] && sync_if_newer "$mem_file" "memory.backup/$(basename "$mem_file")"
    done
fi

# Pre-commit /capture-audit gate (added 2026-05-26)
# Per `feedback_structural_enforcement_when_memory_insufficient` (M7) +
# `feedback_session_decision_log_discipline`: mechanical drift check at sync-time
# catches decision-capture gaps that memory codification alone would miss.
if command -v claude >/dev/null 2>&1 || [ -x "$HOME/.claude/skills/capture-audit/SKILL.md" ]; then
    # Deterministic invocation per .D Phase F.5 — replaces LLM-orchestrated /capture-audit
    # Skill invocation with explicit Python tool call. Mechanical Check 11 detection at
    # commit time per M7 (structural-enforcement-when-memory-insufficient).
    FWD_TOOL="/home/caramel/code/FoxML_Trader_v2/tools/check_forward_promise_audit.py"
    if [ -f "$FWD_TOOL" ]; then
        echo "[sync] Firing Check 11 mechanical forward-promise verification..."
        if [ "${CAPTURE_AUDIT_STRICT:-0}" = "1" ]; then
            # STRICT mode: exit on HIGH findings
            if ! python3 "$FWD_TOOL" --strict --since HEAD~5 2>&1; then
                echo "[sync] BLOCKING per CAPTURE_AUDIT_STRICT=1 + Check 11 HIGH findings"
                exit 1
            fi
        else
            # Default: WARN mode (run for visibility; don't block)
            python3 "$FWD_TOOL" --since HEAD~5 2>&1 | head -30 || true
        fi
    else
        echo "[sync] WARN: check_forward_promise_audit.py not found at $FWD_TOOL; skipping Check 11"
    fi
    # Legacy preserved for env-var compat (will be retired post broader skill-tool integration sweep at .F):
    if [ "${CAPTURE_AUDIT_PASSED:-0}" != "1" ]; then
        echo "[sync] (Legacy LLM-orchestrated /capture-audit invocation skipped per F.5 deterministic-integration)"
        if [ "${CAPTURE_AUDIT_STRICT:-0}" = "1" ]; then
            : # Strict mode already handled above by Python tool directly
            exit 1
        fi
    fi
fi

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
