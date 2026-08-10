#!/usr/bin/env bash
# block_pipe_rc_read.sh — PreToolUse:Bash guard (Class 57 sub-shape D; M7 escalation 2026-08-10).
# Reading $? after a PIPELINE reads the LAST stage's rc (tail/tee/grep = usually 0), silently
# converting a RED verdict into green. THREE live bites in one arc — one inside a pre-commit
# gate (Check A via `python | tee`), two in the D-414 auditor's own proof-reads — recurring
# despite codified knowledge, hence this structural close. Sister to block_rg_r_typo.sh.
# Fix: capture rc directly (`cmd > /tmp/x.log 2>&1; RC=$?`) or use ${PIPESTATUS[0]} (bash) /
# $pipestatus[1] (zsh).
cmd=$(cat | jq -r '.tool_input.command // empty' 2>/dev/null)
[ -z "$cmd" ] && exit 0
if echo "$cmd" | grep -qE '\|[[:space:]]*(tail|head|tee|grep|rg|sed|awk|cat|sort|uniq|wc)[^|;]*;[^|]*\$\?' \
   && ! echo "$cmd" | grep -qiE 'PIPESTATUS|pipestatus'; then
  echo "BLOCKED: reading \$? after a pipeline reads the LAST stage's exit (tail/tee=0), not your tool's — the Class-57 pipe-swallow (3 bites this arc, one inside a gate). Capture rc directly: 'cmd > /tmp/x.log 2>&1; RC=\$?' — or \${PIPESTATUS[0]} (bash) / \$pipestatus[1] (zsh)." >&2
  exit 2
fi
exit 0
