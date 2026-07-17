---
name: project-workspace-remote-gone-commit-only
description: "Workspace repo (tick-trader-percore-workspace) has NO current remote — sync/close rituals COMMIT ONLY, never push; don't re-diagnose the push failure"
metadata: 
  node_type: memory
  type: project
  originSessionId: 48cf1e7d-3242-4daf-951a-a95b831f0804
---

As of 2026-07-16 (confirmed by Caramel): the workspace repo `~/code/tick-trader-percore-workspace` has **no current remote** — the old `origin` (`git@github.com:Jennyfirrr/tick-trader-percore-workspace.git`) is dead (publickey denied / repo gone, consistent with the 2026-07-06 all-private divergence per [[project-public-repo-is-code-only]]). ~47 commits sit "unpushed"; that is EXPECTED, not a backlog.

**How to apply:** `/sync-workspace` and `/close-session` end at the workspace COMMIT — skip `git push`, skip SSH/agent diagnosis. Engine repo is likewise commit-local-only. If a push ever matters again, Caramel will re-point the remote first.
