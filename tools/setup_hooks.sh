#!/bin/bash
# setup_hooks.sh — wire the pre-commit gate in BOTH repos (idempotent). D-300/D-301; closes TECH_DEBT-204.
#
# ONE canonical pre-commit hook lives at the WORKSPACE's .githooks/pre-commit (TRACKED — the union of
# every check A-P). Both repos run it via core.hooksPath=.githooks:
#   - the WORKSPACE runs its own tracked .githooks/pre-commit directly;
#   - the ENGINE's .githooks is a DIR-SYMLINK to the workspace's (matching the tools/ & plans/ pattern);
#     it is gitignored (engine .gitignore:151 = /.githooks) → machine-local → RE-CREATED by this script.
#
# WHY THIS EXISTS: core.hooksPath (both repos) + the engine dir-symlink are machine-local (NOT tracked),
# so a fresh clone silently loses the ENTIRE gate — the "workspace gated nothing → a RED-floor handoff
# committed" bug this closes (D-299). Convention (remember to wire it) already failed: the workspace's
# core.hooksPath was never set, and the hook drifted + was hand-propagated twice (TECH_DEBT-204). Run this
# ONCE per machine / fresh clone. Idempotent + self-verifying.
set -euo pipefail
WS="${WS:-$HOME/code/tick-trader-percore-workspace}"
ENG="${ENG:-$HOME/code/FoxML_Trader_v2}"

[ -f "$WS/.githooks/pre-commit" ] || { echo "FATAL: canonical hook missing at $WS/.githooks/pre-commit"; exit 1; }

# 1. engine .githooks = DIR-symlink → workspace .githooks (idempotent; matches tools/ & plans/)
if [ -L "$ENG/.githooks" ]; then
    echo "ok   engine .githooks already a symlink → $(readlink "$ENG/.githooks")"
else
    [ -e "$ENG/.githooks" ] && rm -rf "$ENG/.githooks"
    ln -s ../tick-trader-percore-workspace/.githooks "$ENG/.githooks"
    echo "SET  engine .githooks → dir-symlink to the workspace canonical"
fi

# 2. core.hooksPath=.githooks in BOTH repos (the wiring that actually makes git run it)
for repo in "$ENG" "$WS"; do
    name=$(basename "$repo")
    cur=$(git -C "$repo" config core.hooksPath || echo "")
    if [ "$cur" = ".githooks" ]; then
        echo "ok   $name core.hooksPath already .githooks"
    else
        git -C "$repo" config core.hooksPath .githooks
        echo "SET  $name core.hooksPath=.githooks"
    fi
done

# 3. verify both hooks resolve + are executable + syntax-clean (fail loud if not)
for repo in "$ENG" "$WS"; do
    name=$(basename "$repo"); h="$repo/.githooks/pre-commit"
    if [ -x "$h" ] && bash -n "$h" 2>/dev/null; then
        echo "ok   $name hook resolves + executable + syntax-clean"
    else
        echo "FATAL: $name hook is missing/broken at $h"; exit 1
    fi
done

echo "DONE — pre-commit gate wired in BOTH repos. A broken handoff / stale MASTER (workspace, Check P)"
echo "       or an open-coded slot→node derive (engine, Check O) now BLOCKS the commit."
