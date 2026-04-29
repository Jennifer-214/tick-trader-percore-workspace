# Phase 8a — Depth Feed activation + Recording (renamed 2026-04-25 evening)

last updated: 2026-04-25 (evening — cross-plan amendments + scope expansion)

**Time budget:** ~1 day (~½ day already done in c1+c2)
**Commits:** 6 total (was 4; +2 for depth-thread activation + book_imbalance feed)
**Risk:** low-medium — pure persistence + a new background thread + slow-path field feed; no hot-path impact

## Amendments applied 2026-04-25 evening

After cross-plan analysis vs. test sidecar + master plan errata + codebase spot-check:

1. **Gap-detection logic moved INTO `DepthRecorder_Write`** (recorder owns `last_seen_id` + `last_seen_wallclock_us`). Subplan originally placed it in `depth_thread_fn`, but the test sidecar tests recorder-internal detection — the two were inconsistent. Recorder ownership is simpler and matches the tests.
2. **Gap algorithm corrected** per master plan errata: `lastUpdateId` jumps 50-500 between `@depth5@100ms` snapshots normally. The original `> last_seen + 1` check would false-positive every message. Replaced with: backward jump OR wallclock gap >2s OR explicit `_LogGap` from disconnect site.
3. Master plan errata's "add `last_seen_wallclock_us` to `DepthSharedState`" is **superseded by amendment #1** — recorder owns it, not the shared state.

## Scope expansion 2026-04-25 evening (mid-implementation)

While starting commit 3 (the original "wire recorder into depth_thread_fn" commit), discovered that **the depth thread is never actually started in the codebase.** `pthread_create` is never called with `depth_thread_fn`. The `depth_enabled` cfg field is parsed but does nothing. `book_imbalance` is initialized to 0 in `PortfolioController_Init` and stays there — the gate at `PortfolioController.hpp:1600` reads dead data.

The original Status update claim "Live depth infrastructure exists and works" was wrong as-stated: the infrastructure (struct, init, thread function) exists, but nothing activates it. Phase 8a recording would have produced empty CSVs.

**Restructure:** added 2 commits (now 6 total) to actually activate the depth feed before wiring the recorder. c1+c2 are unchanged (foundation for both activation AND recording). Original c3 → new c5; original c4 → new c6.

| Commit | Status | Scope |
|---|---|---|
| c1 | ✅ done (`afcab06`) | BookSnapshot extension (`last_update_id` + `timestamp_us`) |
| c2 | ✅ done (`b50e6b3`) | DepthRecorder primitive (allocation-free Write, gap detection, daily rotation) |
| **c3 (NEW)** | TODO | Activate depth thread in `main.cpp` — `pthread_create` gated on `cfg.depth_enabled`, `pthread_join` on shutdown, lifecycle plumbing |
| **c4 (NEW)** | TODO | Wire `book_imbalance` from `DepthSharedState` → `PortfolioController` on slow path |
| c5 (was c3) | TODO | Wire DepthRecorder into `depth_thread_fn` — recorder pointer in DepthSharedState + Write/LogGap calls |
| c6 (was c4) | TODO | `record_depth` cfg field + Settings panel + engine.cfg + changelog + test binary (17 assertions) + CLAUDE.md notes |

Original prose preserved below; corrections inline at the relevant blocks. New commit blocks for c3 + c4 added in their own sections.

## Pre-audits for new c3 + c4 (REQUIRED before commit 3)

These are issues to verify before starting the new activation work:

1. **OpenSSL global state** — `DepthStream_Init` calls `ws_ssl_setup` (creates its own SSL_CTX). The trade stream init path also creates an SSL_CTX. Verify both can coexist (OpenSSL is reentrant since 1.1.0 if `OPENSSL_init_ssl` was called once). If not, share a single global `SSL_CTX`.

2. **`min_book_imbalance` cfg default** — gate at `PortfolioController.hpp:1600` is `if (!FPN_IsZero(ctrl->config.min_book_imbalance))`. Find the default in `ControllerConfig_Default()`. If 0, gate is dead and c4 is plumbing-only (no behavior change). If non-zero, c4 changes behavior — needs documentation in changelog.

3. **Depth thread shutdown discipline** — `depth_thread_fn` reads `__atomic_load_n(&shared->quit_requested, __ATOMIC_ACQUIRE)` at the top of its loop. The poll() blocks for 200ms max, so signaling quit_requested + waiting up to ~200ms for the next loop iteration is sufficient. No socket-close needed for shutdown. Verify pattern in main.cpp's existing pthread_join discipline matches.

## Context anchors — files to read FIRST

```
plans/live-readiness-master.md         ← orchestration + anti-drift discipline
DataStream/TickRecorder.hpp                   ← pattern to mirror (daily rotation, auto-prune)
DataStream/BinanceDepth.hpp                   ← lines 28-50: BookSnapshot struct
                                               ← lines 86-162: depth_parse_json
                                               ← lines 203-243: depth_thread_fn (where the recorder taps in)
CoreFrameworks/ControllerConfig.hpp           ← record_ticks, record_max_days fields (~line 270)
main.cpp                                       ← where DepthStream is initialized (live engine startup)
```

Branch state expected: on `experiment/live-readiness`. Doesn't conflict with Phase 8 work — touches different files entirely.

## Failure mode IDs covered

- **No depth audit trail** — engine consumes `@depth5@100ms` in real time but doesn't persist it. Restart loses all depth history. Future ML/analysis has no replayable book state. Future hybrid execution (Phase 9) has no historical fill simulation data.
- **Disconnect-induced data gaps invisible** — DepthStream reconnects automatically, but gaps in the data feed aren't surfaced anywhere except as missed `lastUpdateId` jumps that no one currently observes.

## Status update

Live depth infrastructure exists and works:
- `DataStream/BinanceDepth.hpp` subscribes to `@depth5@100ms` when `depth_enabled=1`
- Parsed snapshots populate `book_imbalance` field via atomic swap
- Reconnect handled in `depth_thread_fn` loop
- The `lastUpdateId` field IS parsed by the JSON parser implicitly (it's in the JSON) but **NOT stored** in `BookSnapshot`. We need to add it.

What's missing is purely persistence + gap detection. No live trading behavior changes in this phase.

## Commit plan (in order)

### Commit 1: Add `lastUpdateId` to `BookSnapshot` + parser

**Goal:** capture the monotonic update ID that Binance includes with every depth message. Used for gap detection in commit 3.

**File:** `DataStream/BinanceDepth.hpp`

**Approach:**

1. Add field to `BookSnapshot` struct after `update_count`:
   ```cpp
   uint64_t last_update_id;   // Binance "lastUpdateId" — monotonic per-symbol update sequence
   uint64_t timestamp_us;     // local microsecond clock when snapshot landed (for daily rotation)
   ```

2. Update `BookSnapshot_Init` to zero both.

3. In `depth_parse_json`, extract `lastUpdateId`:
   ```cpp
   const char *id_start = strstr(json, "\"lastUpdateId\"");
   if (id_start) {
       const char *colon = strchr(id_start, ':');
       if (colon) snap->last_update_id = strtoull(colon + 1, NULL, 10);
   }
   ```

4. In `depth_thread_fn`, set `timestamp_us` after successful parse, before atomic swap:
   ```cpp
   struct timespec ts;
   clock_gettime(CLOCK_REALTIME, &ts);
   shared->snapshots[back].timestamp_us = (uint64_t)ts.tv_sec * 1000000 + ts.tv_nsec / 1000;
   ```

**Anti-drift checks:**
- [ ] `BookSnapshot` size growth (16 bytes for two uint64_t) acceptable — verify no struct-size assumption breaks
- [ ] Existing `book_imbalance` consumers unaffected (they read different fields)
- [ ] If `lastUpdateId` parse fails, `last_update_id` stays 0 (recorder logs but doesn't crash)

**Testing:** rebuild, verify build clean. No behavior change yet.

### Commit 2: `DataStream/DepthRecorder.hpp` — sibling of TickRecorder

**Goal:** the recorder primitive. Daily rotation, CSV format, auto-prune.

**File:** `DataStream/DepthRecorder.hpp` (new)

**Approach:**

Mirror `TickRecorder.hpp` exactly, with depth-specific differences:

```cpp
#ifndef DEPTH_RECORDER_HPP
#define DEPTH_RECORDER_HPP

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <sys/stat.h>
#include <dirent.h>

struct DepthRecorder {
    FILE *file;
    uint64_t count;
    int enabled;
    int current_day;          // YYYYMMDD of currently open file
    char symbol[16];
    char data_dir[256];       // "data/{symbol}/depth/"
    uint32_t max_days;
    // Gap-detection state (amendment #1+#2): recorder owns this, not DepthSharedState.
    uint64_t last_seen_id;          // last lastUpdateId observed; 0 = no prior snapshot
    uint64_t last_seen_wallclock_us; // local wallclock when last_seen_id was recorded
};

// Daily filename: data/{symbol}/depth/YYYY-MM-DD.csv
// CSV header: timestamp_us,last_update_id,bid_price,bid_qty,ask_price,ask_qty
// One row per parsed depth snapshot.
// Gap markers: a comment line "# GAP at_us=X" inserted when:
//   - last_update_id goes BACKWARD (reconnect to stale snapshot), OR
//   - wallclock between snapshots exceeds 2s (WS was silent), OR
//   - explicit _LogGap call from disconnect site.
// Within-100ms-window lastUpdateId jumps of 50-500 are NORMAL — book updates
// faster than the 10Hz @depth5@100ms feed. Do NOT log those as gaps.

static inline void DepthRecorder_Init(DepthRecorder *rec, const char *symbol,
                                        const char *base_dir, uint32_t max_days,
                                        int enabled);

static inline void DepthRecorder_Close(DepthRecorder *rec);

// Called once per parsed snapshot from depth_thread_fn.
template <unsigned F>
static inline void DepthRecorder_Write(DepthRecorder *rec, const BookSnapshot<F> *snap);

// Called on reconnect — surfaces a gap marker even if the WS missed the
// snapshot containing the post-gap lastUpdateId.
static inline void DepthRecorder_LogGap(DepthRecorder *rec, uint64_t from_us);

// Internal: rotate file when day changes
static inline void DepthRecorder_RotateIfNeeded(DepthRecorder *rec, uint64_t timestamp_us);

// Internal: prune CSVs older than max_days (called once on Init)
static inline void DepthRecorder_AutoPrune(DepthRecorder *rec);

#endif
```

Implementation pattern follows `TickRecorder.hpp` closely:
- `Init` mkdir's `data/{symbol}/depth/`, calls AutoPrune
- `RotateIfNeeded` checks date int, fcloses + reopens if changed
- `Write` does (in order): rotate-if-needed → **gap-detect against last_seen_*** → write CSV row → update last_seen_*
- `LogGap` writes a `# GAP ...` comment line (CSV-tolerant) AND resets `last_seen_id = 0` so the next `_Write` doesn't double-flag the same gap
- `Close` flushes + closes

**Gap-detection algorithm inside `_Write` (amendment #2):**
```cpp
uint64_t cur_id = snap->last_update_id;
uint64_t cur_us = snap->timestamp_us;
if (rec->last_seen_id != 0) {
    int backward = (cur_id < rec->last_seen_id);
    int wall_gap = (cur_us > rec->last_seen_wallclock_us &&
                    cur_us - rec->last_seen_wallclock_us > 2000000ULL); // >2s
    if (backward || wall_gap) {
        DepthRecorder_LogGap(rec, cur_us);  // logs + resets last_seen_id
    }
}
// ... write CSV row ...
rec->last_seen_id = cur_id;
rec->last_seen_wallclock_us = cur_us;
```

Why the algorithm changed: `@depth5@100ms` sends snapshots every 100ms but the underlying book updates 50-500× faster. So `lastUpdateId` between consecutive snapshots normally jumps by 50-500, not +1. The original "+1 check" would false-positive every single message. Real gaps look like: backward `lastUpdateId` (reconnect to a stale snapshot) OR wallclock silence >2s (WS was dead).

**CSV row format:**
```
timestamp_us,last_update_id,bid_price,bid_qty,ask_price,ask_qty
```

(Top-of-book only initially. Full L5 deferred — same format extension would be `,bid2_p,bid2_q,...`)

**Anti-drift checks:**
- [ ] `data/{symbol}/depth/` directory created with `0755` permissions
- [ ] AutoPrune deletes only files matching `YYYY-MM-DD.csv` pattern, never any other file in the directory
- [ ] File open errors (disk full, permission) log but don't propagate as exceptions (we're called from a thread)
- [ ] No malloc on the per-snapshot path — `Write` is called ~10 Hz, must be allocation-free

**Testing:** unit-style: write 1000 snapshots manually, verify file exists and is well-formed.

### Commit 3 (NEW): Activate depth thread in main.cpp

**Goal:** make `cfg.depth_enabled=1` actually start the depth feed. Currently the cfg field is parsed but does nothing.

**Files:**
- `main.cpp` — declare `DepthSharedState`, instantiate, `pthread_create`, `pthread_join` on shutdown

**Approach:**

1. After Binance trade stream init (where the existing pthread_create for tui_thread is), conditionally start the depth thread:
   ```cpp
   pthread_t depth_tid = 0;
   DepthSharedState<F> depth_shared = {};
   if (ccfg.depth_enabled) {
       if (DepthStream_Init<F>(&depth_shared, bcfg.symbol,
                                bcfg.binance_host, 443,
                                /*reconnect_delay=*/2) == 0) {
           pthread_create(&depth_tid, NULL, depth_thread_fn<F>, &depth_shared);
           fprintf(stderr, "[ENGINE] depth feed active\n");
       } else {
           fprintf(stderr, "[ENGINE] depth feed init failed — continuing without\n");
       }
   }
   ```

2. On shutdown (alongside existing TUI thread join):
   ```cpp
   if (depth_tid) {
       __atomic_store_n(&depth_shared.quit_requested, 1, __ATOMIC_RELEASE);
       pthread_join(depth_tid, NULL);
   }
   ```

**Anti-drift checks:**
- [ ] Engine startup unchanged when `depth_enabled=0` (default) — no new thread, no Binance connection
- [ ] Depth init failure does NOT block engine startup (logs + continues without)
- [ ] `pthread_join` waits ≤ ~200ms (next poll() loop iteration)
- [ ] No new SSL_CTX leaks — verify with valgrind in dev or just structurally check `DepthStream_Init` cleanup paths

**Testing:** local smoke. Set `depth_enabled=1` in cfg, run engine, observe `[ENGINE] depth feed active` log + `book_imbalance` field starts updating in TUI.

### Commit 4 (NEW): Wire book_imbalance from DepthSharedState into controller

**Goal:** the existing buy gate at `PortfolioController.hpp:1600` reads `ctrl->book_imbalance`. Currently always 0. Feed real data on slow path.

**Files:**
- `main.cpp` — slow path tick loop reads from depth shared state
- (no PortfolioController.hpp changes needed — gate already exists)

**Approach:**

In the slow-path block of main.cpp's tick loop (where other slow-path calls happen, e.g. `PortfolioController_Tick`), atomically read the active snapshot's imbalance and update the controller:

```cpp
// Slow path: pull latest book imbalance from depth thread (if running)
if (depth_tid != 0) {
    int active = __atomic_load_n(&depth_shared.active_idx, __ATOMIC_ACQUIRE);
    ctrl.book_imbalance = depth_shared.snapshots[active].imbalance;
}
```

(The atomic load + struct field read is safe because the depth thread does atomic_store_n with RELEASE semantics on `active_idx` after writing the snapshot — the matching ACQUIRE here pairs correctly. Per the existing double-buffered pattern.)

**Anti-drift checks:**
- [ ] Hot path (PortfolioController_Tick's per-tick BuyGate path) unchanged — read happens on slow path before the tick loop body
- [ ] When `depth_enabled=0`, no read happens (depth_tid == 0), `book_imbalance` stays at its `_Init` value (0) — gate behaves as before
- [ ] When `depth_enabled=1` AND `min_book_imbalance=0` (default): real data flows but gate stays dead — no behavior change
- [ ] When `depth_enabled=1` AND `min_book_imbalance > 0`: gate fires on real data — **behavioral change**. Document in changelog: "Setting min_book_imbalance>0 with depth_enabled=1 now actually gates buys on real orderbook depth (was inert before)."

**Testing:** local smoke with `depth_enabled=1, min_book_imbalance=0.05`. Engine should occasionally show "GATE OFF (book)" in TUI when imbalance is below threshold.

### Commit 5 (was Commit 3): Wire DepthRecorder into depth_thread_fn

**Goal:** tap the existing depth thread loop. Write every parsed snapshot. Log explicit gap on disconnect.

**Files:**
- `DataStream/BinanceDepth.hpp` — add a recorder pointer to `DepthSharedState` + call recorder in thread loop
- `main.cpp` — instantiate the recorder during live engine startup

**Approach (amendment #1 — simplified):** gap detection is INSIDE `DepthRecorder_Write` per commit 2. The thread just calls `_Write` per snapshot and `_LogGap` on disconnect. `DepthSharedState` does NOT need a `last_seen_update_id` field — the recorder owns it.

1. Extend `DepthSharedState`:
   ```cpp
   template <unsigned F> struct DepthSharedState {
       BookSnapshot<F> snapshots[2];
       int active_idx;
       int quit_requested;
       DepthStream stream;
       char symbol[32];
       char host[128];
       int port;
       int reconnect_delay;
       DepthRecorder *recorder;   // NEW — null if recording disabled
   };
   ```

2. In `depth_thread_fn`, after the successful parse + atomic swap, call the recorder:
   ```cpp
   if (depth_parse_json<F>(frame_buf, plen, &shared->snapshots[back])) {
       __atomic_store_n(&shared->active_idx, back, __ATOMIC_RELEASE);

       if (shared->recorder && shared->recorder->enabled) {
           // Recorder does its own gap detection internally (commit 2).
           DepthRecorder_Write(shared->recorder, &shared->snapshots[back]);
       }
   }
   ```

3. On disconnect, log an explicit gap marker. `_LogGap` resets the recorder's `last_seen_id` so the next post-reconnect snapshot doesn't double-flag:
   ```cpp
   if (plen < 0) {
       ds->connected = 0;
       if (shared->recorder && shared->recorder->enabled) {
           struct timespec ts;
           clock_gettime(CLOCK_REALTIME, &ts);
           DepthRecorder_LogGap(shared->recorder,
               (uint64_t)ts.tv_sec * 1000000 + ts.tv_nsec / 1000);
       }
       continue;
   }
   ```

4. In `main.cpp`, instantiate the recorder if `cfg.record_depth=1`:
   ```cpp
   DepthRecorder depth_rec;
   DepthRecorder_Init(&depth_rec, cfg.symbol, "data/", cfg.record_max_days,
                       cfg.record_depth);
   shared_depth_state.recorder = (cfg.record_depth ? &depth_rec : nullptr);
   ```

**Anti-drift checks:**
- [ ] `recorder=null` path is the default; no behavior change unless `record_depth=1`
- [ ] Recorder failure (bad fopen, write error) logs once and disables itself rather than spamming
- [ ] Gap markers are written ONCE per reconnect (disconnect-site `_LogGap` resets `last_seen_id`, so the post-reconnect first `_Write` skips its internal gap-check)
- [ ] **Crash-window gap is NOT marked** (recorder state in memory only; restart resets `last_seen_id=0` → first write of new run doesn't gap-detect). Document as known limitation.

**Testing:** Manual on testnet. Run for an hour with `depth_enabled=1, record_depth=1`. Confirm:
- File `data/BTCUSDT/depth/YYYY-MM-DD.csv` appears
- ~36000 rows after one hour (at 10Hz)
- `lastUpdateId` is monotonically increasing
- Force a disconnect (kill network briefly) and verify a `# GAP` line appears

### Commit 6 (was Commit 4): Cfg field + tooltip + changelog

**Goal:** expose `record_depth` cfg field, document the recording behavior.

**Files:**
- `CoreFrameworks/ControllerConfig.hpp` — new field + parser + default
- `GUI/SettingsPanel.hpp` — UI exposure
- `engine.cfg` (live cfg file) — add documented entry
- `DOCS/changelogs/2026-04-XX-phase8a-depth-recorder.md` — new changelog

**Approach:**

1. Cfg field (add near `record_ticks`):
   ```cpp
   int record_depth;   // 0 = disabled (default), 1 = record depth snapshots to data/{symbol}/depth/
   ```

2. Default: `cfg.record_depth = 0;` (off by default — backward compat)

3. Parser: `CFG_PARSE_INT(record_depth)`

4. Settings panel field_def entry under "Tick Recording" section:
   ```cpp
   {"record_depth", "Record Depth", "Tick Recording", CFG_BOOL, NULL,
    "Persist orderbook snapshots to data/{symbol}/depth/YYYY-MM-DD.csv\n"
    "Daily rotation, auto-prune older than record_max_days.\n"
    "Format: timestamp_us, last_update_id, bid/ask price+qty (top-of-book).\n"
    "Required for backtest replay of depth-based features. ~50 MB/day."},
   ```

5. `engine.cfg`: add `record_depth=0  # 1 = persist depth snapshots for replay`

**Anti-drift checks:**
- [ ] Default is 0 (off) — no behavior change for existing setups
- [ ] Backtest cfg also accepts the field (no parse error if `record_depth=0` set in `backtest.cfg`)
- [ ] Auto-prune only fires on Init, not per-write

**Testing:** unit-test cfg parse, manual smoke on live engine.

## Verification (after EACH commit)

```bash
cmake --build build -j$(nproc)            # ANSI engine + tests
cmake --build build_gui -j$(nproc)        # engine_gui + foxml_suite
build/controller_test                      # 296/296 (post-Phase-5d baseline)
```

## Verification (after ALL 4 commits)

Manual on testnet, 1-hour run:

1. Set `depth_enabled=1`, `record_depth=1` in `engine.cfg`
2. Run `./build_gui/engine_gui`
3. Wait 60 minutes, then inspect:
   - `data/BTCUSDT/depth/YYYY-MM-DD.csv` exists, ~36000 rows
   - `lastUpdateId` column is monotonic (or has gap markers if WS reconnected)
   - File size ~50 MB
4. Force a disconnect (e.g., `sudo iptables -A OUTPUT -p tcp --dport 443 -j DROP` for 30 sec, then remove)
5. Verify a `# GAP from_us=... to_us=...` line appears in the CSV
6. Restart engine on the same day — file is appended to (not truncated)
7. Wait until day boundary — file rotates to next day's filename

## Definition of done

- [ ] All 4 commits land cleanly on `experiment/live-readiness`
- [ ] 296/296 controller_test + 17 new in depth_recorder_test (post-Phase-5d baseline + new test binary per sidecar)
- [ ] 1-hour testnet run produces well-formed CSV with valid gap markers
- [ ] `record_depth` field documented in both `engine.cfg` and Settings panel tooltip
- [ ] Auto-prune verified: create a fake old file, restart, verify it's removed

## Tag at end of Phase 8a

```bash
git tag phase8a-complete
```

## Known limitations / deferred

- **Top-of-book only initially** — full L5 (10 levels) is a CSV-format extension. Add when needed.
- **No replay path yet** — Phase 8a only records. Backtest replay of depth events is a separate work item, deferred until enough recordings exist to be worth replaying (≈ 2 weeks of data).
- **No depth-derived ML features yet** — also deferred. Phase 8a is the data-gathering prerequisite.
- **Gap markers are advisory** — don't actually correlate to a missed feature window in any consumer yet. When backtest replay lands, replay should refuse to use depth-derived features within K ms of a gap marker.
