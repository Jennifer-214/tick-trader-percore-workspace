# Headless polish — sub-ship vision notes (captured 2026-05-13)

**Status:** future sub-ship; defer until structural sub-sprint (`.C` + `.D` + `.E`) completes.
**Operator framing (2026-05-13):** "i wanna make it insanely polished right, if were tracking what it does by logs, or lightweight things, we need to see like decisions per core, decisions per the overall manager etc right? to watch everything and then like a minor TUI to see like per core exit and buy gates and stuff? idk we can work this out in another sub ship, or just go to headless after we polish this stuff i think, removing tech debt is more important right now."

**Decision:** structural sub-ships (`.C` + `.D` + `.E`) take priority. Headless polish comes after — likely as `.H` or a v5.16-series sub-sprint. The structural work directly positions for headless (see `decoupling-endgoal-roadmap.md` `.B` breadcrumb).

## What "insanely polished" means in this context

The vision is **observability-by-default for everything the engine does**, not a watered-down "engine without GUI". Two complementary surfaces:

### 1. Structured log channels — comprehensive event coverage

Operator should be able to watch the engine via `tail -f` on a small set of focused log files. Each captures a different decision domain:

| Channel | Captures | Cadence | Format |
|---|---|---|---|
| `decisions/core_<N>.log` | per-core slow-path decisions: strategy_id, halt_reason, gate diag (spacing/vwap/long-slope/vol-delta/stddev/tp-pct), regime, ML prediction + threshold | per `RebuildOneCore` cycle | structured (TSV or JSONL); 1 line per cycle per core |
| `decisions/manager.log` | engine-wide decisions: regime headline, ML headline, partner-pairing events, kill-switch trips, cfg-drift, paper-reset events | per-event | TSV / JSONL |
| `fills.log` | every fill (entry + exit): slot, side, price, qty, fee, P&L net, partner pairing, leg attribution | per-fill | TSV (already exists via ShardedTradeLog — extend if needed) |
| `oms.log` | OMS state transitions: submit queue depth, drainer cadence, fill bookkeeping, kill-switch arm/disarm, partial-exit leg events | per-event on drainer thread | structured |
| `ws.log` | Binance WS event stream: ticks/sec rate, depth snapshot health, staleness gate fires, reconnect events | per-second summary | TSV |
| `latency.log` | slow-path latency stats per cycle (SP_SECTION breakdown), hot-path latency percentiles | every N seconds | TSV |
| `gate_diag.log` | gate diagnostics per cycle: actual vs threshold for each gate (spacing, vwap, long-slope, vol-delta, stddev, tp_pct) | per cycle when gate fires | TSV |
| `ml/predictions.log` | per-cycle ML buy-side + exit-side predictions, dominant horizon, barrier mode | per cycle for ML cores | TSV |
| `ml/drift.log` | drift breach + auto-kill events; IC samples on update | per-event | TSV |
| `ml/bandit.log` | bandit arm pull / reward / weight update events; algorithm cfg state | per-event | TSV |
| `health.log` | existing HealthLog channel (already structured) | per-event | existing JSONL |

Operator workflow:
1. Start engine: `./bin/engine --cfg engine.cfg --log-dir logging/`
2. Open tmux session: `scripts/tmux-watch.sh` — opens 12-pane layout with each pane tailing a different log
3. Watch in real-time; operator observes every decision

### 2. Minor TUI — per-core exit/buy gates dashboard

Pure ANSI TUI (no ImGui dependency); separate small binary that reads the live engine state via mmap or a unix socket. Shows:

- Per-core summary row: strategy, halt_reason, ml_pred (if ML), buy_gate, exit_gate, P&L
- Per-core gate diagnostics: spacing actual/floor, vwap actual/threshold, etc.
- Engine-wide summary: total entries/exits, W/L, regime, ws_ticks/sec, sp_latency p99
- Refresh rate ~10-30 Hz (faster than GUI's 30-60 because no full ImGui render)

Distinct from existing TUI (`DataStream/EngineTUI.hpp`):
- Existing TUI does TUISnapshot publish — uses the same per-core publisher as ImGui. Heavyweight.
- The "minor TUI" should be much lighter: read mmap'd region directly (post-decoupling) or read snapshot file at slow cadence (pre-decoupling).
- Pre-decoupling MVP: snapshot file approach. Engine writes a `snapshot.bin` periodically; TUI mmap's it read-only. ~1ms staleness; acceptable for operator dashboard.

### 3. Operator control via signals + CLI

- `SIGUSR1` → paper-reset
- `SIGUSR2` → pause/resume engine
- `SIGTERM` → graceful shutdown
- `bin/engine-ctl <subcommand>` wraps signal sends + reads state:
  - `engine-ctl status` — query engine health
  - `engine-ctl reset-core <N>` — reset specific core
  - `engine-ctl pause` / `engine-ctl resume`
  - `engine-ctl ml-toggle` — flip ML on/off
  - etc.

## Scope estimate

- Log channel infrastructure: ~4-6 hours (most channels already exist as ad-hoc stderr writes; consolidate + structure)
- TUI dashboard: ~6-8 hours (~500-800 LOC)
- Signal + CLI control: ~2-3 hours
- tmux-watch script + cfg additions: ~1 hour
- Operator docs + cfg.example updates: ~1-2 hours
- **Total: ~14-20 hours** — one focused 2-day sub-sprint OR spread across a week of evenings

## Pre-requisites

- ✅ `.B` cluster-layout discipline established (DONE 2026-05-13)
- ✅ Engine binary builds standalone (already true — `./build.sh` builds `engine` target)
- ⏳ `.C/.D/.E` structural cleanups complete (so log channels reflect the FINAL data layout, not interim transient state)
- ⏳ Snapshot publisher loop fusion (DONE in `.B.8`) — `snapshot.bin` mmap approach builds on this
- ⏳ Audit + identify what ad-hoc `fprintf(stderr, ...)` writes already exist + which to keep / restructure

## Connection to existing infrastructure

The codebase already has:
- `MemHeaders/HealthLog.hpp` (v5.4.0 Phase 0.1) — structured operational diagnostic log (JSONL)
- `MemHeaders/RunHistory.hpp` (v5.3.2 Phase C) — JSONL append-only run history
- `CoreFrameworks/ShardedTradeLog.hpp` — per-trade CSV log with FOREACH_TRADE_LOG_COL registry
- Async log thread (v5.11.3.C) — drainer I/O isolation for high-throughput log writes
- TUISnapshot double-buffer + publish (v5.x) — already snapshot-publisher-pattern

So the foundation is mostly in place. The headless polish work is mostly:
- CONSOLIDATING ad-hoc stderr writes into structured channels
- ADDING channels for things not yet logged (gate_diag, per-cycle ML, bandit details, etc.)
- WRITING the minor TUI binary
- WRITING the operator CLI + tmux script

## Risks

- **Log volume on busy markets**: 16 cores × 1000 cycles/sec × ~200B/line = ~3.2 MB/s per log channel. With 10+ channels = ~30 MB/s sustained write. Need log rotation + maybe compression. async log thread (v5.11.3.C) handles this — verify it scales.
- **Operator information overload**: too many channels = noise. Need cfg knobs to enable/disable channels at boot.
- **Snapshot.bin staleness vs decisions log**: operator could see "core 2 just halted on VWAP" in decisions log but TUI dashboard still shows it as armed. Acceptable for paper-test; problematic for live trading observability. Mitigated by sync timestamp on both surfaces.

## Codification

When this sub-ship ships, consider:
- NEW DESIGN_SPEC: `observability-log-channel-discipline.md` (if patterns emerge)
- Update CLAUDE.md item 8 ("TUI independent of engine") with the headless variant
- Cross-reference from `decoupling-endgoal-roadmap.md` — this is a major positive breadcrumb for v6.0 colo

## Decision point at sub-ship kickoff

Three scope choices when this ship starts:
1. **Minimum**: log channels only; no TUI; manual CLI invocations (tail -f, kill -USR1)
2. **Medium (recommended)**: log channels + minor TUI + signal-based control + CLI wrapper + tmux script
3. **Maximum**: above + mmap snapshot region (closer to v6.0 architecture) + control unix socket for richer engine-ctl commands

Operator chooses at kickoff time based on then-current priorities. `.B` already positions for option 3.
