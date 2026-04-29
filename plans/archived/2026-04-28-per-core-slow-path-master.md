# Per-Core Slow-Path Architecture — Master Plan

**Created:** 2026-04-28
**Goal:** migrate from centralized controller-thread slow-path to per-core slow-path threads, where each (slow-path + hot-path) pair forms a self-contained "strategy engine."

---

## Why this matters

### Today's architecture
```
                    ┌──────────────────────────────────────┐
                    │  Controller / Slow-Path Thread       │
                    │  (1 thread, multiplexes 4 cores)     │
                    │  - Regime classify × N               │
                    │  - Strategy_BuildParameters × N      │
                    │  - DrainPostFill (consumes all OMS)  │
                    │  - GateParameters seqlock writes × N │
                    └──────────────┬───────────────────────┘
                                   │ seqlock
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
        ┌─────────┐          ┌─────────┐          ┌─────────┐
        │ Hot 0   │          │ Hot 1   │          │ Hot N-1 │
        │ pinned  │          │ pinned  │          │ pinned  │
        └─────────┘          └─────────┘          └─────────┘
```

### Target architecture
```
                    ┌──────────────────┐
                    │  Orchestrator    │
                    │  (lifecycle,     │
                    │   GUI snap sync) │
                    └──────────────────┘
   ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
   │ Strategy Engine 0│ │ Strategy Engine 1│ │ Strategy Engine N│
   │  ┌─────┐ ┌─────┐ │ │  ┌─────┐ ┌─────┐ │ │  ┌─────┐ ┌─────┐ │
   │  │Slow │ │Hot 0│ │ │  │Slow │ │Hot 1│ │ │  │Slow │ │HotN │ │
   │  │ 0   │↔│     │ │ │  │ 1   │↔│     │ │ │  │ N   │↔│     │ │
   │  └─────┘ └─────┘ │ │  └─────┘ └─────┘ │ │  └─────┘ └─────┘ │
   │  pinned cores    │ │  pinned cores    │ │  pinned cores    │
   └──────────────────┘ └──────────────────┘ └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ OMS (single-     │
                    │  writer, fed by  │
                    │  slow-path SPSC  │
                    │  queues)         │
                    └──────────────────┘
```

### Wins
1. **Architectural clarity** — each strategy unit is self-contained. Add a strategy = spin up another engine pair.
2. **Slow-path optimization** — dedicated thread = cache-resident state, no multiplexing overhead, can go event-driven later.
3. **Per-core slow-path profiling** — instrument exactly like hot-path, find which strategy's slow-path is heavy.
4. **Future scaling** — at N=8+ cores or with heavy per-core ML inference, centralized slow-path becomes a real bottleneck. Per-core unblocks growth.
5. **Portfolio signal** — matches real prop-shop architecture; demonstrates the orchestrator/executor pattern explicitly.

### Cost
4-6 days focused work. Each phase is independently shippable + verifiable.

---

## Hardware constraints

**i9-9980HK target (8 physical / 16 logical):**

Measured baseline (centralized architecture, 4 cores running):
- C1-C5: 100% busy (4 hot-paths + 1 controller)
- C0, C6, C7: barely used (2-11%)
- C8-C15 (HT siblings): mostly idle

**Proposed architecture adds 4 slow-path threads** — but those are NOT 100% busy. Slow-path runs every ~100 ticks (~100ms in slow markets), takes ~10µs to execute, then yields. Effective CPU per slow-path thread: ~1-5%. Slot into existing idle headroom on cores C0/C6/C7 + HT siblings without measurable load increase.

**Net new physical core demand: zero.** Hardware fits comfortably.

**Thermal note**: hot-path cores already running at 97-100°C under sustained 100% load (visible in `htop` — thermal throttling range on this laptop). Slow-path threads at 1-5% utilization don't worsen this. The thermal headroom on idle cores stays intact.

**Past N=8 strategies** — would exceed laptop. Production deployment on Xeon/EPYC handles N=16+ cleanly with isolcpus + IRQ pinning. Architectural pattern stays the same.

### Pinning plan (i9-9980HK, N=4)

| Thread | Pin to physical core | HT sibling state | Reasoning |
|---|---|---|---|
| Hot-path 0..3 | Cores 0-3 (one each) | **Unused** | Sub-100ns p99 needs cache + execution-unit isolation. HT-sharing causes jitter. |
| Orchestrator | Core 4 | HT sibling free | Lightweight; coordinates lifecycle + GUI snap. |
| Slow-path 0..3 | Cores 5-7 (rotate) | HT-shared with utility | Slow-path is ~1-5% busy; tolerates jitter. |
| Producer | HT sibling of core 5 | Shared | Bursty WS reads. |
| Depth WS | HT sibling of core 6 | Shared | Bursty WS reads. |
| GUI / Notify | HT sibling of core 7 | Shared | Latency-tolerant. |

**Total physical cores used: 8/8** with hot-path cores at sustained 100%, others at light load.

**Recommended dev/test config — N=3 instead of N=4** on the laptop:
- 3 hot-paths on cores 0-2 (HT siblings unused)
- 3 slow-paths on cores 3-4
- Cores 5-7 + HT siblings for orchestrator + producer + depth + GUI + notify
- **Real headroom** for OS noise, thermal slack, IRQ jitter
- Trade-off: one less strategy slot. For development of the migration, this is the safer baseline.

Production hardware (Xeon 16+ cores) handles N=8+ comfortably with full isolation.

**For HFT-grade isolation** (optional, production-only):
- Kernel boot param: `isolcpus=0-3 nohz_full=0-3 rcu_nocbs=0-3`
- Steer hardware IRQs away from cores 0-3 via `/proc/irq/*/smp_affinity`
- Run engine with `chrt -f 99 taskset -c 0-7`

These are deployment-time concerns, not code changes — but worth documenting for whoever runs the engine on dedicated hardware.

---

## Backwards compatibility

Default to **centralized slow-path** (existing behavior) initially. Add cfg toggle:

```
engine_arch=centralized   # default — single controller thread
engine_arch=per_core_slow # new — per-core slow-path threads
```

Once `per_core_slow` is verified with parity tests, flip default. Keep `centralized` available for benchmark comparison + safety net.

---

## Sub-plans (sequential, each independently shippable)

### Phase A: Data-plane decoupling (~1 day)
**Plan:** `plans/2026-04-28-per-core-slow-path-A-decouple.md` (TODO)
- Per-core copy of RollingStats / RollingLong (each engine owns its own)
- Per-core flow state, large-trade state (already mostly per-core; verify)
- Shared read-only: depth snapshot (single producer feeds all)
- No thread changes yet — just isolate the data each core's slow-path will eventually own
- Backtest + live both work identically with the data layout change

### Phase B: Slow-path thread spawning (~2 days)
**Plan:** `plans/2026-04-28-per-core-slow-path-B-spawn.md` (TODO)
- Add `engine_arch` cfg toggle
- When `per_core_slow`, spawn N slow-path threads at boot
- Each slow-path thread: pinned to a chosen CPU, runs its own poll loop
- Refactor `EventLoop_DrainPostFill` so per-core slow-path drains only its own slots
- Refactor `Strategy_BuildParameters` call site so per-core slow-path runs only its own core's strategy
- Centralized path stays default + intact

### Phase C: OMS multi-producer queue (~1 day)
**Plan:** `plans/2026-04-28-per-core-slow-path-C-oms.md` (TODO)
- Slow-paths now run in parallel, can submit orders concurrently
- OMS stays single-writer — slow-paths push commands via per-core SPSC into a single OMS thread
- OR: OMS becomes MPSC consumer (one queue, N producers)
- Verify no race on portfolio bitmap

### Phase D: Per-core poll cadence (~0.5 day)
**Plan:** `plans/2026-04-28-per-core-slow-path-D-cadence.md` (TODO)
- Add INT support to per-core override X-macro (deferred from settings audit)
- New override: `core_N_poll_interval`
- Each slow-path thread reads its core's resolved poll_interval

### Phase E: Per-core slow-path latency profiling (~0.5 day)
**Plan:** `plans/2026-04-28-per-core-slow-path-E-latency.md` (TODO)
- Mirror `CoreLatencyStats` for slow-path: `SlowPathLatencyStats`
- Same rolling window + lifetime histogram pattern
- Display in Per-Core Latency panel as a second table or extra columns

### Phase F: Parity verification + flip default (~1 day)
**Plan:** `plans/2026-04-28-per-core-slow-path-F-parity.md` (TODO)
- New regression tests: same scenario through `centralized` vs `per_core_slow` produces identical W/L, gross_wins/losses, per-core P&L
- Verify backtest train-serve parity (same training data with both architectures)
- Performance benchmarks: hot-path p99 unchanged, slow-path latency improved
- Flip cfg default to `per_core_slow`

### Phase H: GUI extensions for per-engine observability (~1 day, after F)
**Plan:** inline (small enough)

**Existing panels — minor extensions:**
- **Per-Core Latency**: add columns for slow-path stats (SP-Min/p50/p95/p99/Max) alongside existing hot-path columns. Same row-per-core layout. Each row shows hot + slow side-by-side.
- **Per-Core Latency**: new "Lifetime p99" column from the v4.7.36 histogram (separate from rolling 256-sample p99). Helps spot tail outliers across millions of samples.
- **Settings tabs**: Phase G rename (`Core N` → `Engine N`); slow-path config already per-engine via Phase D's `core_N_poll_interval` override.

**New panel — Engine Topology** (warrants its own ImGui window):
- Header: current `engine_arch` (centralized | per_core_slow), N engines configured
- One row per engine: pin info (`hot=core 0, slow=core 5`), thread state (running / yielded / blocked), last slow-path tick timestamp
- Slow-path cadence: configured vs actual tick rate per engine (e.g. `100 ticks configured, 105 actual` — drift = thread contention)
- SPSC command-queue depths (if Phase C implements per-engine queues): live depth = OMS backpressure signal
- Lifecycle button per engine: `Pause` (cleanly stops slow-path thread, hot-path keeps reading stale params), `Resume`, `Restart`. Useful for debugging without restarting the whole engine.

**Deferred (not blocking initial migration):**
- Slow-path work breakdown — per-tick microsection profiling (regime classify / strategy dispatch / DrainPostFill / TimeExit etc.). Useful for tuning slow-path-heavy strategies. ~1 day on top.

### Phase G: Tab/UX rename — `Core N` → `Engine N` (~30 min, ship anytime)
**Plan:** inline (small enough)
- Settings panel tabs: `Core 0` → `Engine 0`, ..., `Global` stays
- Per-Core P&L panel header: `PER-CORE P&L` → `PER-ENGINE P&L` (or keep — stylistic)
- Per-Core Risk panel: `PER-CORE RISK` → `PER-ENGINE RISK`
- Per-Core Latency panel: `PER-CORE LATENCY` → `PER-ENGINE LATENCY`
- Buy Gate column header `Core` → `Engine`
- Reasoning: with per-core slow-path, each tab represents a self-contained strategy engine (slow + hot pair), not just an execution core. Reinforces the architectural framing and matches prop-shop vocabulary.
- Cfg keys (`core_N_strategy`, `core_N_risk_pct`, etc.) stay as-is for back-compat. UI label only.

---

## Risks + mitigations

| Risk | Mitigation |
|---|---|
| Race conditions on shared state | Per-core copies; OMS stays single-writer; explicit memory ordering on shared reads |
| Performance regression on hot path | Existing seqlock between slow/hot stays unchanged; per-core slow-path doesn't touch hot-path data structures any differently |
| Train-serve drift | Phase F parity tests are mandatory before flipping default |
| Snapshot/persistence breakage | Snapshot version bump if any per-core state struct layout changes (unlikely with phased approach) |
| Backtest determinism breakage | Backtest stays single-threaded simulated mode regardless of `engine_arch` (it doesn't use real threading; it iterates ticks linearly). **engine_arch is LIVE-ONLY**. |

---

## What this is NOT

- **Not** a hot-path change. Hot-path stays branchless, cache-aligned, ~30-50ns. p99 unaffected.
- **Not** a strategy logic change. Strategies still consume resolved cfg the same way.
- **Not** a parser/cfg field change beyond adding `engine_arch` and `core_N_poll_interval`.
- **Not** a snapshot version bump (unless per-core state grows; revisit per phase).
- **Not a backtest change.** Backtest is single-threaded and runs the slow-path body in a linear per-core loop in `ShardedBacktest_RunTick`. `engine_arch` is a live-only setting. Backtest always uses the linear-iteration path. Train-serve parity is preserved because the per-core slow-path body produces the same per-core EFFECTS regardless of whether those effects come from N parallel threads (live) or one sequential loop (backtest).

---

## Versioning plan

This migration is a **major architectural rewrite** per CLAUDE.md (X bump = architectural rewrite). v5.0.0 lands when Phase F flips the default and the feature branch merges to trunk.

| Version | Phase | Trunk merge? |
|---|---|---|
| v4.7.37 | B (OMS funneling, opt-in setup) | No — feature branch only |
| v4.7.38 | C (spawn threads, opt-in cfg) | No |
| v4.7.39 | D (per-core poll cadence) | No |
| v4.7.40 | E (slow-path latency profiling) | No |
| v4.7.41 | F prelim (parity tests, default centralized) | No |
| **v5.0.0** | **F final: flip default to per_core_slow + merge to trunk** | **YES** |
| v5.0.1+ | G (rename), H (GUI), etc. | Standard cadence |

The pre-v5.0.0 phases stay on the `feat/per-core-slow-path` branch with rollback tags between each phase (`pre-phase-c`, `pre-phase-d`, etc.). v5.0.0 commit message documents the architectural switchover.

## Order of attack

Phases are sequential. Each phase ships standalone, gets a version bump, passes existing tests + adds new ones, gets a `pre-vN` rollback tag.

Suggested cadence: one phase per session when fresh. Six sessions to land cleanly, with debugging room.

**Defer until:**
- Today's spot-checking is finished and you're confident in v4.7.x state
- Tomorrow or next session for Phase A (lowest-risk, no thread changes)

The current centralized architecture is correct and shippable. This refactor is for architectural clarity + future scaling, not for fixing anything broken.
