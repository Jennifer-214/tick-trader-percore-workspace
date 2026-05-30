---
name: feedback_machine_portable_resolver_for_committed_tool_paths
description: "A committed tool that references a per-machine/per-user path (a $HOME dir, a hardcoded WORKSPACE/ENGINE abspath) gets a resolver — env override + derived default + .exists() guard — not a hardcode, so it works across machines / an SSH-grid without editing the tool"
metadata:
  node_type: memory
  type: feedback
  tags: [refactor-discipline, cross-tool-decoupling, ssot]
  sister_specs: [feedback_single_source_of_truth_discipline.md, project_engine_clauder_md_is_symlink.md]
  originSessionId: 30f2afef-e244-4d39-bbaf-07a8969f6ba0
---

A committed tool (CI check, migration helper, index rebuilder) that needs a path which differs per machine or per user — a `$HOME/.claude/...` dir, the repo's absolute root, a workspace path — resolves it through an indirection point, NOT a hardcoded literal: an **env-var override** first, then a **derived default** (compute from a known anchor like the repo root, rather than hardcoding `$HOME`), guarded by `.exists()`.

**Why:** a hardcoded `/home/<user>/...` path silently breaks the moment the repo is checked out on a second machine, under a different user, or on an SSH-grid/distributed node — and a committed tool is shared, so the breakage ships. The env-override makes a grid node a config change (`export FOXML_MEMORY_DIR=...`), not a code edit; the derived default keeps the single-machine case zero-config; the `.exists()` guard degrades gracefully when the path is absent. One indirection point = the SSoT for "where does X live," imported by every tool + sync step that needs it (don't duplicate the resolver).

**How to apply:** editing/writing a committed tool that references a machine-specific path → add `resolve_X()` = `os.environ.get("FOO_X_DIR") or <derived-from-anchor>`, `.exists()`-guarded; SHARE it (import the one resolver). Canonical instance: `.E.0.4` `_resolve_memory_dir()` in `tools/check_doc_metadata.py` (env `FOXML_MEMORY_DIR` + derive from the engine repo path), imported by `migrate_memory_frontmatter.py` + `rebuild_doc_indexes.py`. The engine's own `WORKSPACE`/`ENGINE` hardcodes are the same latent multi-machine hazard ([[project_engine_clauder_md_is_symlink]] is a sibling per-machine-path quirk). Composes with [[feedback_single_source_of_truth_discipline]] (the one resolver is the SSoT).
