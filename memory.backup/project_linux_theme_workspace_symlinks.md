---
name: project-linux-theme-workspace-symlinks
description: "Linux_Theme repo's plans/ + CLAUDE.md + docs are symlinks into ~/code/linux-theme-workspace (its private workspace repo)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 71bbd731-1825-494a-915b-919cf155b39e
  modified: 2026-08-09T21:10:35.978Z
  sister_specs: [project_engine_clauder_md_is_symlink.md]
  tags: []
---

`~/code/Linux_Theme` mirrors the trader's layout: `plans/`, `CLAUDE.md`, `CLAUDE.local.md`, `AGENT.md`, `TECHDEBT.md`, `INVARIANTS.md`, `CONTRIBUTING.md` are symlinks into `~/code/linux-theme-workspace` (a separate private git repo, branch `main`, remote alive — commit+push plans there, never to the public Linux_Theme repo). Same convention as [[project_engine_clauder_md_is_symlink]]: plans/docs belong to the workspace; the code repo stays code-only. Writes through the symlink land correctly, but prefer workspace paths when a path ambiguity matters. The workspace has pre-commit hooks (capture-audit, idempotent-file-edits) that run on plan commits.
