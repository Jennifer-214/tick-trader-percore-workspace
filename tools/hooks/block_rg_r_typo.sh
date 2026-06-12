#!/usr/bin/env bash
# Claude Code PreToolUse(Bash) guard — block the 'rg -r<x>' typo.
#
# WHY: ripgrep's -r is --replace (NOT grep's recursive; rg is recursive BY DEFAULT). So `rg -rn "X"`
# silently parses as --replace=n and rewrites EVERY match to the literal 'n' in the output — a trap
# that has manufactured phantom findings repeatedly (meta-anti-pattern-index AR-1: the .E.0.10 false
# TECH_DEBT-168 "placeholder id: n" alarm + the FOREACH-macro investigation mangling, recurring even
# minutes after being written up). Memory codification kept failing -> M7 escalation to this guard.
#
# PRECISION (shlex-tokenized, NOT a raw-string grep): blocks only when an actual `rg` TOKEN is
# immediately followed by a `-r<letter>` TOKEN. Because shlex respects quotes, content that merely
# MENTIONS the pattern in a quoted arg is a single token and does NOT trip it — e.g.
# `git commit -m "fix rg -rn bug"` is allowed (the message is one token). Allowed: rg -n,
# rg --replace=, spaced `rg -r REPL`, `rg "self-reflect"`, grep -rn. Residual rare FPs: an UNQUOTED
# multi-word arg that happens to be `... rg -rn ...` (e.g. `echo rg -rn`, or a heredoc body) — reword
# those (write `-r<x>` or `rg's -r`). Exit 2 = block; stderr is fed back as the reason.
#
# ENABLE (project-scoped): a PreToolUse(Bash) hook in <project>/.claude/settings.local.json pointing
# at this script (wired .E.0.10 2026-06-11). For global: the same block in ~/.claude/settings.json.
# DISABLE: remove that PreToolUse block. Hooks reload per-invocation, so edits to THIS script apply now.
python3 -c '
import sys, json, shlex
try:
    cmd = json.load(sys.stdin).get("tool_input", {}).get("command", "")
except Exception:
    sys.exit(0)
try:
    toks = shlex.split(cmd)
except ValueError:
    toks = cmd.split()
for i, t in enumerate(toks):
    if (t == "rg" or t.endswith("/rg")) and i + 1 < len(toks):
        nxt = toks[i + 1]
        if nxt.startswith("-r") and len(nxt) > 2 and nxt[2].isalpha():
            sys.stderr.write("BLOCKED: rg -r<x> is --replace, NOT recursive (rg is recursive by default; -rn silently becomes --replace=n and rewrites matches to the letter n). Use rg -n or grep -rn; for a genuine replace use rg --replace=VALUE.\n")
            sys.exit(2)
sys.exit(0)
'
