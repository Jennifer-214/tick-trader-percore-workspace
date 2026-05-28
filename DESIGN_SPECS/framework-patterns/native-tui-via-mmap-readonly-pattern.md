---
type: framework-pattern
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.2
canonical_applications:
  - v5.15.5.F.4d.1.E.2 (fox-tui binary; notcurses; reads mmap state-publish)
sister_specs:
  - meta-disciplines/headless-engine-viewer-split-pattern.md (parent; engine + viewer split)
  - framework-patterns/dual-format-metrics-publication-pattern.md (sister; Prometheus + mmap)
tags: [framework-discipline, tui, notcurses, mmap, read-only, viewer]
surface: [viewer, mmap-state, terminal-ui]
applies_at_skills: [/precoding-audit-gate]
---

# Native TUI via mmap read-only pattern

**Pattern intent:** fox-tui binary reads engine state via mmap'd shared memory region (lock-free; seqlock-consistent reads). Operator-customizable layout. vi-style keybindings. Multiple concurrent viewers OK.

## Problem statement

Operator needs real-time visibility into engine state:
- Per-node trading status + P&L
- Per-cluster connection health + rate budget usage
- Global aggregate state + kill switch state
- Recent fill events
- Latency histograms

Options:
1. **Built-in GUI** (Dear ImGui) — engine binary couples to GUI; can't run headless
2. **Web dashboard** (Grafana) — requires Prometheus + browser; not native-terminal
3. **CLI dump-state** (fox-cli) — one-shot snapshot; not live-updating
4. **Native TUI** (notcurses; reads mmap) — live; native; multi-viewer

**Pattern: option 4** (with Grafana via Prometheus complementary per `dual-format-metrics-publication-pattern.md`).

## Pattern description

### Viewer architecture

```cpp
// fox-tui main loop
int main(int argc, char** argv) {
    // Parse CLI args (--socket; --refresh-hz; etc.)
    const char* mmap_path = ResolveMmapPath();  // /var/lib/fox/state/state.mmap or ~/.local/share/fox/state/state.mmap

    // mmap engine's state publication region (read-only)
    int fd = open(mmap_path, O_RDONLY);
    void* region_addr = mmap(nullptr, sizeof(StatePublishRegion), PROT_READ, MAP_SHARED, fd, 0);
    const StatePublishRegion* region = (const StatePublishRegion*)region_addr;

    // Initialize notcurses
    notcurses_options nopts = {};
    notcurses* nc = notcurses_init(&nopts, stdout);

    // Main loop
    while (!quit_flag) {
        // Read state snapshot (lock-free; seqlock-consistent)
        ViewerSnapshot snap;
        StatePublish_Read(region, &snap);

        // Render panels
        RenderGlobalPanel(nc, &snap);
        RenderClusterPanels(nc, &snap);
        RenderNodePanels(nc, &snap);
        RenderAuditEventRing(nc, &snap);

        notcurses_render(nc);

        // Wait for input (or refresh tick)
        ncinput ni;
        if (notcurses_get_blocking(nc, &ni)) {
            HandleInput(ni);  // vi-style; q to quit; : for command mode
        }
    }

    notcurses_stop(nc);
    munmap(region_addr, sizeof(StatePublishRegion));
    return 0;
}
```

### Display layout (operator-customizable)

```
┌─ FOX-ENGINE  v0.1.0  ─────────────────────────────────  PID 12345  Uptime 4d 3h 17m ─┐
│ GLOBAL: P&L +$847.23 (+3.4%)  Notional $24,500  Drawdown -1.2%  Kill: OFF             │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ ┌─ CLUSTER: binance (4 nodes; live) ─────────────────────────────────────────────┐   │
│ │ Rate: 234/1200 (19%)  WS: ✓ (uptime 4d)  Realized +$523  Open $18,400          │   │
│ │ ┌─ node_0  BTCUSDT  momentum_v3.1 ─────  live  ─┐                             │   │
│ │ │ Realized: +$182  Open: $5,200 (long 0.12 @ $43,250)                       │   │
│ │ │ Hot p99: 187ns  Slow p99: 12μs  Last fill: 2m 14s ago                     │   │
│ │ └────────────────────────────────────────────────┘                             │   │
│ │ ... (other nodes; per-node panel)                                              │   │
│ └────────────────────────────────────────────────────────────────────────────────┘   │
│ ┌─ CLUSTER: alpaca ─  CLOSED (market hours) ─┐                                       │
│ │ ... (when market open)                       │                                      │
│ └──────────────────────────────────────────────┘                                      │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ Recent events:                                                                       │
│ 2026-05-28 14:23:17  binance/node_0  FILL  BUY 0.05 @ $43,250.50                    │
│ ... (audit_ring tail)                                                                │
├──────────────────────────────────────────────────────────────────────────────────────┤
│ [hjkl] navigate  [Enter] drill into  [q] quit  [:] command  [r] refresh  [?] help    │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Operator customization

```
configs/operators/caramel/tui-keybindings.cfg:
quit = q
refresh = r
help = ?
drill_into = Enter
navigate_up = k
navigate_down = j
navigate_left = h
navigate_right = l
command_mode = :
search = /
```

vi-style by default; operator can override.

### Drill-down navigation

```
Top-level view: cluster grid
  ↓ Enter on cluster
Cluster view: node grid + cluster health
  ↓ Enter on node
Node view: detailed state + recent fills + latency histogram
  ↓ Enter on event
Event detail: full audit log entry
```

### Multi-viewer concurrent attach

mmap is read-only shared memory; arbitrary number of viewers can attach:

```bash
# Operator on laptop:
ssh -L /tmp/fox.sock:/var/run/fox/engine.sock server
fox-tui --socket /tmp/fox.sock

# Operator on phone (via SSH from terminal app):
fox-tui --refresh-hz 1

# Backup monitor (cron + parser):
fox-cli dump-state --json | jq '.global.drawdown_pct'
```

All concurrent; no engine coupling.

## Stage progression criteria

- **Stage 3 first canonical** (`.E.2`): fox-tui implemented with notcurses
- **Stage 4 cohort** (when 2nd TUI consumer: e.g., per-strategy viewer): pattern proven
- **Stage 5 CLAUDE.md** (3rd application): promoted

## Anti-patterns avoided

- **GUI in engine binary** — coupling
- **Single-viewer** — limits workflow
- **Polling via fox-cli** — high overhead; not live
- **Lock-based mmap reads** — H3 violation; seqlock pattern preferred

## Cross-references

- Parent: `meta-disciplines/headless-engine-viewer-split-pattern.md`
- Sister: `framework-patterns/dual-format-metrics-publication-pattern.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.2-headless-configs-docs.md`
