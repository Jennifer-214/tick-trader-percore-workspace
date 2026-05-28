---
type: meta-discipline
stage: 3-first-canonical
version: 1.0
established: 2026-05-28
landing_ship: v5.15.5.F.4d.1.E.2
canonical_applications:
  - v5.15.5.F.4d.1.E.2 (fox-engine headless + fox-tui + fox-cli + foxml-train)
sister_specs:
  - framework-patterns/native-tui-via-mmap-readonly-pattern.md (viewer side)
  - framework-patterns/dual-format-metrics-publication-pattern.md (state publication)
  - framework-patterns/crash-recovery-via-mmap-state-pattern.md (mmap state file)
  - meta-disciplines/gui-deprecation-decision-rationale.md (sister; old GUI deprecated)
tags: [meta-discipline, headless-service, viewer-split, decoupling, operator-workflow]
surface: [engine-binary, viewer-binaries, command-channel, state-publication]
applies_at_skills: [/precoding-audit-gate, /dod-audit]
---

# Headless engine + viewer split pattern

**Pattern intent:** Engine becomes authoritative headless service (no GUI dep). State published via mmap'd shared memory. Commands accepted via Unix domain socket. Multiple viewers (TUI; CLI; future web) attach on-demand. Engine doesn't depend on any viewer being running.

## Problem statement

Engine integrated with GUI has problems for 24/7 production operation:
- GUI thread crash takes down trading
- GUI requires interactive session (X11/Wayland; not headless ssh)
- Operator can't attach/detach without engine restart
- Multiple operators can't observe simultaneously
- No native remote monitoring (X-forward over SSH = slow)
- GUI dependencies (SDL2/OpenGL/ImGui) bloat engine binary
- High-stakes funds operation should NOT depend on GUI being up

Decoupled engine + viewer separation solves all of these.

## Pattern description

### Process topology

```
ENGINE (fox-engine; systemd-managed; runs 24/7):
  - All trading flow
  - All exchange adapters
  - All account state
  - Writes state to mmap'd shared memory region
  - Listens on Unix domain socket for commands
  - Optional: HTTP /metrics endpoint for Prometheus scrape
  - NO GUI dependency

VIEWERS (operator-attached; multiple concurrent OK):
  - fox-tui (notcurses; reads mmap; primary monitoring)
  - fox-cli (sends commands via UDS; control)
  - foxml-train (CLI ML training; independent of engine)
  - (Future) Web dashboard via Grafana scraping Prometheus
```

### State publication (engine → viewers)

mmap'd shared memory region; engine WRITES; viewers READ (lock-free; seqlock pattern):

```cpp
// /var/lib/fox/state/state.mmap (production) OR ~/.local/share/fox/state/state.mmap (dev)

struct alignas(64) StatePublishRegion {
    // Header with seqlock for consistency
    struct Header {
        uint32_t protocol_version;
        uint32_t engine_software_version;
        std::atomic<uint64_t> writer_seqlock;
        // ...
    };

    Header header;
    AggregatorStateView global;
    ClusterStateView clusters[NUM_EXCHANGES];
    NodeStateView nodes[MAX_NODES];
    AuditEventCompact audit_ring[AUDIT_EVENT_RING_SIZE];
};

// Engine writer (single):
void StatePublish_Cycle(EngineState<F>& state) {
    state.publish_region->header.writer_seqlock.fetch_add(1, std::memory_order_acq_rel);  // odd = in progress
    // ... write all fields ...
    state.publish_region->header.writer_seqlock.fetch_add(1, std::memory_order_release);  // even = consistent
}

// Viewer reader (multiple concurrent OK):
void StatePublish_Read(const StatePublishRegion* region, ViewerSnapshot& snap) {
    uint64_t seq1, seq2;
    do {
        seq1 = region->header.writer_seqlock.load(std::memory_order_acquire);
        memcpy(&snap, region, sizeof(StatePublishRegion));
        seq2 = region->header.writer_seqlock.load(std::memory_order_acquire);
    } while (seq1 != seq2 || (seq1 & 1) != 0);
}
```

### Command channel (viewer → engine)

Unix domain socket; viewers SEND commands; engine VALIDATES + APPLIES:

```cpp
// /var/run/fox/engine.sock (production) OR ~/.local/share/fox/engine.sock (dev)
// chmod 600; only owner readable

enum CommandVerb {
    CMD_PAUSE_NODE,
    CMD_RESUME_NODE,
    CMD_HALT_CLUSTER,
    CMD_HALT_ALL,
    CMD_TRANSFER_FUNDS,
    CMD_RELOAD_NODE_CONFIG,
    CMD_SET_KILL_THRESHOLD,
    CMD_DUMP_STATE,
    CMD_ADD_NODE,
    CMD_REMOVE_NODE,
    CMD_MODEL_SWAP,
    // ... per .E.1 enumeration
};

// Engine-side listener:
void CommandChannel_Listen(EngineState<F>& state, int uds_fd) {
    Command cmd;
    while (read(uds_fd, &cmd, sizeof(Command)) > 0) {
        if (CommandChannel_Validate(cmd, state)) {
            CommandHandlers[cmd.verb](state, cmd, &response);
        }
        write(uds_fd, &response, sizeof(CommandResponse));
    }
}
```

### Remote operator access via SSH-tunneled UDS

```bash
# Direct local
fox-tui                # connects to /var/run/fox/engine.sock

# Remote via SSH tunnel
ssh -L /tmp/fox.sock:/var/run/fox/engine.sock server
fox-tui --socket /tmp/fox.sock

# fox-cli works same way
fox-cli pause-node binance/node_0 --socket /tmp/fox.sock
```

No HTTPS needed; SSH provides auth + encryption + tunneling.

## Multi-viewer concurrent attach

Multiple viewers can attach simultaneously:
- Operator on laptop: fox-tui via SSH tunnel
- Operator on phone: Grafana dashboard via Prometheus scrape
- Backup monitoring script: fox-cli queries via cron
- Engineer debugging: fox-cli dump-state for specific node

mmap is shared memory; lock-free reads via seqlock; arbitrary viewer count.

## Engine independence from viewers

- Engine starts independently of viewers (boot doesn't wait for viewer)
- Viewer crash doesn't affect engine
- Viewer attach/detach mid-operation OK
- Engine shutdown is clean even if no viewers attached
- Crash recovery via mmap state file works regardless of viewer state

## Stage progression criteria

- **Stage 3 first canonical** (`.E.2`): engine + fox-tui + fox-cli + foxml-train implemented
- **Stage 4 cohort** (when 2nd application: e.g., web dashboard via Grafana): pattern proven
- **Stage 5 CLAUDE.md** (3rd application + discipline matures): promoted

## Anti-patterns avoided

- **GUI in engine binary** — coupling; SPOF for trading
- **Single viewer per engine** — limits operator workflow
- **HTTPS for control channel** — certificate complexity; SSH baked-in security wins
- **Engine startup dependent on viewer** — coupling; production reliability concern

## Cross-references

- Sister: `framework-patterns/native-tui-via-mmap-readonly-pattern.md`
- Sister: `framework-patterns/dual-format-metrics-publication-pattern.md`
- Sister: `framework-patterns/crash-recovery-via-mmap-state-pattern.md`
- Sister: `meta-disciplines/gui-deprecation-decision-rationale.md`
- First application: `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.2-headless-configs-docs.md`
- Decoupling roadmap: `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` (this pattern realizes the vision)
