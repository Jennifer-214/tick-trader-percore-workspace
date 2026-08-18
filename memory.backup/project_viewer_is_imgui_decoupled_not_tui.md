---
name: project_viewer_is_imgui_decoupled_not_tui
description: "The viewer is Dear ImGui, decoupled into a monitoring plane; fox-tui is DROPPED and the GUI hard-deprecation is reversed (D-427)"
metadata: 
  node_type: memory
  type: project
  originSessionId: 8f3fb3f9-a531-4777-92f3-afdf3af52eda
  modified: 2026-08-18T02:17:53.661Z
  sister_specs: [project_foxml_suite_refactor_queued.md]
  tags: []
---

**Dear ImGui is KEPT and decoupled into a monitoring plane. `fox-tui` is DROPPED. Nothing is archived to `legacy/`.** Operator decision 2026-08-17 (D-427), superseding D-7 + D-26 on the renderer question.

**Why this needs to be a memory and not just a plan entry:** it REVERSES two decisions still logged `STATUS: landed` — a fresh session reading the decision log, the `.E.2` plan body, or the canonical binary-name list will find `fox-tui` and "ImGui hard-deprecated at `.E.2`" and follow them. The reversal is not derivable from the code either, since both `engine_gui` and `EngineTUI.hpp` still exist at HEAD.

**Only the renderer changed.** Everything that is actually the decoupling stands: headless engine that doesn't depend on a viewer · read-only viewer + command-sender · `fox-cli` for control · multi-viewer · mmap/versioned state exposure · lifecycle independence. No landed decoupling work is invalidated.

**How to apply:** never propose archiving/deprecating the ImGui GUI, and never plan a notcurses TUI. Viewer work = decoupling ImGui into a monitoring plane. The ML/training panels stay ImGui too, on the same shape (every op cmdline-invocable via `FOREACH_CLI_MODE`; the panel drives `execv` children + tails per-run dirs) — that half is the queued producer-side work in [[project_foxml_suite_refactor_queued]].

⚠️ **`EngineTUI.hpp` is TWO things — do not delete it wholesale.** The RENDER half dies; **`TUISnapshot`/`PerNodeSnap`, the seqlock double-buffered engine→display DATA CONTRACT, SURVIVES and is promoted** — it is the one site that reads money safely and it is what BECOMES the mmap'd region. The contract IS the monitoring plane; the renderer was one consumer of it.

Consequence homed, not done: the `TUI` prefix then names a thing that's gone, but renaming needs its own leaf (`PerNodeSnap` is pinned in `tools/lib/cache_layout_baseline.txt` + `alignas(64)` cluster discipline ⇒ cache-layout re-bless). H21 doesn't bite — in-process struct names, not persisted identifiers.

Full record: D-427 in the `.E` architecture-v2 decision log + the D-427 banner in `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`. Still carrying the retired premise and needing a re-ground pass: the `.E.2` plan body, EV-3, and the canonical binary-name list.
