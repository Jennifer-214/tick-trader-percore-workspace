---
name: engine-claude-md-is-symlink-to-workspace
description: /home/caramel/code/FoxML_Trader_v2/CLAUDE.md (and possibly other engine-root docs) is a symlink into /home/caramel/code/tick-trader-percore-workspace/; edits must target the workspace path directly
metadata: 
  node_type: memory
  type: project
  originSessionId: cde2db64-4da3-4d80-aeb6-00c06bcca15a
  sister_specs: [feedback_machine_portable_resolver_for_committed_tool_paths.md, project_linux_theme_workspace_symlinks.md]
  tags: [project-state, doc-discipline]
---

The engine repo's `CLAUDE.md` is a symlink:

```
/home/caramel/code/FoxML_Trader_v2/CLAUDE.md → ../tick-trader-percore-workspace/CLAUDE.md
```

Writes through the symlink path fail with "Refusing to write through
symlink: ... Resolve the symlink and pass the real target path
explicitly."

**Why:** Caramel uses a workspace-private mirror to keep edge content
(DESIGN_SPECS, plans, claude-skills) backed up off-machine while the
public engine repo gets the AGPL-licensed code + the symlinked public
CLAUDE.md. The symlink means editing one reflects in both — but the
HARNESS safety guard refuses symlink writes, so you must always edit
the workspace target directly.

**How to apply:** when an Edit/Write fails with "Refusing to write
through symlink":
1. Run `readlink -f <path>` to get the real target
2. Re-do the Edit/Write against the target path
3. The symlink path will reflect the change automatically

**Likely other symlinked files** (check with `ls -la` if uncertain):
- `plans/` directory (symlinked to workspace `plans/`)
- `.claude/skills/` (symlinked to workspace `claude-skills/`)
- Possibly some DOCS/ files

Operator framing 2026-05-12: "can you make a memory that its a
symlink or something, we run into this issues alot" — codified to
prevent re-tripping.
