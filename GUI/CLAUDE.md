# Working in GUI/ — Dear ImGui native dashboard surface orientation

> On-demand: loads when you read/edit a file in `GUI/`. CONCATENATES with the always-loaded
> root `CLAUDE.md` (universal core) — this is the GUI SLICE, not a replacement. Universal rules
> (H1–H21, priority gradients, collaboration norms) are already loaded from root; this carries the
> render-surface detail. Edit this workspace file, not the engine symlink.

## What this dir does

SDL2 + Dear ImGui + ImPlot native dashboard (`engine_gui` / `foxml_suite`), ~60Hz render on its OWN
pthread (`gui_thread_fn`, `GuiThread.hpp`) — a drop-in replacement for the ANSI `tui_thread_fn`. Each
panel is a standalone dockable ImGui window. The render thread is OFF the trading path: the engine hot/
slow/drainer threads are unaffected by frame cadence (16.7ms budget, H3 thread isolation).

- **Stateless panels** (`GUI_Panel_BuyGate/Market/Account/Positions/Stats/Latency/...`, `DashboardPanels.hpp`) take only `const TUISnapshot*` — pure published-snapshot readers.
- **Stateful panels** (`TradeHistory`, `LogViewer`, `Settings`, `StrategyQuality`) own per-frame state + a file cache; declared+inited via the `FOREACH_PANEL(X)` registry (`GuiThread.hpp`). Adding one = 1 X-macro row (enrolled in `FOREACH_REGISTRY`, MetaRegistry.hpp, LEVEL 1 — H15).
- **Feeds:** `CandleAccumulator` (engine WS thread writes ticks → GUI reads OHLCV via a copied snapshot) · `TradeReader`/`TradeHistory`/`LogViewer`/`StrategyQuality` (read engine CSV/JSONL logs from disk) · `EngineHeader`/`MLStatusPanel` (compile-time consts + snapshot fields) · `FoxmlTheme` (FoxML Classic palette, terminal-matched).

## Surface rules (load-bearing in GUI/)

- **Read the published snapshot, NEVER a live engine pointer/struct** (H3 thread isolation). The engine→GUI handoff is the `TUISnapshot` **seqlock + double-buffer** (`TUISnapshot_Publish_Begin/End` writer / `TUISnapshot_ReadInto` reader, `DataStream/EngineTUI.hpp`). Each frame copies ONE snapshot tear-free into a stack-local (`snap_local`, `GuiThread.hpp`) — the pointer-into-shared pattern was REMOVED v5.11.3.B because it observed torn buffers when the slow path lapped the renderer. **GUI is the canonical POSITIVE example** of the cross-thread-multiword-read discipline (`Money`/`Position` are 16B = 2 words → tear without a consistent copy); read it tear-free here, don't reach past it into engine memory.
- **Display↔execution invariant — every new snapshot field gets its GUI render in the SAME ship.** Cardinal rule (`DOCS/EXECUTION_DISPLAY_INVARIANTS.md` + Class 2): every term in the hot-path entry/exit predicate MUST have an operator-visible surface, or the dashboard lies (the 2026-04-30 "READY while silently refusing to fire" incident). Gate diagnostics flow through `FOREACH_GATE_DIAG` → render rows in `MLStatusPanel.hpp`/`DashboardPanels.hpp` (5-site mirror; the registry is the structural fix). A snapshot field with no render row is an unmatched-term reject.
- **NO blocking I/O in a render function.** `fopen`/`stat`/`opendir`/`popen`/network in the 60Hz frame jams every frame on disk/syscall latency. Mediate via a `_Refresh()` helper that `stat()`-size-checks BEFORE reopening (TradeReader/LogViewer/TradeHistory cache on `st_size` change), a **Refresh button**, or a window-appearing trigger (`SettingsPanel.hpp:800` model scan "stays free of opendir/stat per /readiness check 17"). `CandleAccumulator` feeds from engine memory, not a per-frame file read.
- **GUI→engine = atomic command flags + file-mediated writes, NEVER a shared pointer** (H3). Keyboard/buttons set `__atomic_store_n(&shared->{quit,pause,reload,swap_strategy[core],swap_model_path[core]}_requested, …, RELEASE)`; SettingsPanel writes `engine.cfg` via `cfg_write_field` + raises `reload_requested`. The engine consumes the file + flag — the GUI never mutates engine structs directly (the positive H3 file-mediation example).
- **Locale + float discipline.** `Gui_Init` re-pins `setlocale(LC_NUMERIC,"C")` AFTER `SDL_Init` (SDL/X11 can reset LC_* process-wide; `.E.0.1`) — a global process-state pin (Class 38/39 territory; keep it, it's load-bearing for deterministic float parse). CSV/JSONL fields parse via `tt::parse_double_fast` (locale-immune), never `atof`. `double` is DISPLAY-ONLY here (snapshot fields arrive pre-converted via `FPN_ToDouble` on the publish side) — never round-trip a display `double` back into an accounting decision (H4).

## Tools for this surface (slice of `DOCS/TOOLS.md`)

- `calls_graph_diff.sh` — orphan-diff; run after any GUI change to confirm the **hot path stayed UNTOUCHED** (the render thread must not have grown a trading-path edge).
- `check_identifier_retirement.py` — `TUISnapshot`/`PerCoreSnap` persisted/wire-visible field keys are append-only + immutable (H21); tombstone, never renumber/reuse a snapshot slot (pre-commit Check H).
- (No dedicated panel-coverage CI tool exists — the display↔execution invariant is enforced by the `FOREACH_GATE_DIAG` registry + the `DOCS/EXECUTION_DISPLAY_INVARIANTS.md` matrix + PR review / `/bug-check` Class 2.)

## Skills for this surface

- `/readiness` — its "NEW GUI panels → display↔execution invariant verified" check + the no-blocking-I/O-in-render hardening (Check 17) gate any panel ship.
- `/bug-check` — Class 2 (display↔execution divergence) · Class 13 (worker-thread snap-capture drift) · Class 19 (hardcoded instance names in GUI gating).
- `/dod-audit` — X-macro registry application (FOREACH_PANEL) + snapshot cluster layout.
- `/trace-deps` — trace a new snapshot field GUI←snapshot←CoreContext before adding a render row.

## Patterns + anti-patterns here

- DESIGN_SPECS: `concurrency-patterns/cross-thread-multiword-read-consistency-discipline.md` (GUI = the positive consumer) · `framework-patterns/display-execution-invariant-registry-pattern.md` (FOREACH_GATE_DIAG) · `data-disciplines/per-snapshot-cluster-layout-pattern.md` · `framework-patterns/x-macro-registry-with-presence-dispatch.md` (FOREACH_PANEL) · `framework-patterns/built-in-observability-pattern.md`.
- RECURRING_BUG_PATTERNS: **Class 2** (display↔execution divergence — dashboard lies) · **Class 13** (worker/render-thread struct extended without updating snap-capture) · **Class 7** (threading-topology violation — pointer-share across threads) · **Class 19** (hardcoded instance names in GUI applicability gating) · **Class 38/39** (phantom invariant / global process-state mutation — the `setlocale` pin).

## Reach for more

- Universal rules/invariants: root `CLAUDE.md` (already loaded) + `DOCS/DESIGN_PHILOSOPHY.md` § 6 (concurrency / thread isolation) + § 5 (determinism / locale).
- Snapshot publish + thread topology + cross-thread reader discipline: `CoreFrameworks/CLAUDE.md` (the writer/publication side) + `DataStream/EngineTUI.hpp` (TUISnapshot/TUISharedState definitions).
- Cardinal display↔execution rule (full matrix): `DOCS/EXECUTION_DISPLAY_INVARIANTS.md`.
- Adding a GUI panel / snapshot field / per-node override surface: `DOCS/CLAUDE_INTEGRATION.md` (§ GUI panels + display↔execution check).
