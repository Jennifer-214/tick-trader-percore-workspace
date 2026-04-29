# Phase 8b — Operational Monitoring + Alerting (parallel to Phase 8)

last updated: 2026-04-25 (evening — cross-plan amendments applied)

**Time budget:** ~half day to 1 day
**Commits:** 4 (planned, with commit 3 descoped to stderr-only)
**Risk:** low — slow-path / dedicated-thread only, no hot-path impact

## Amendments applied 2026-04-25 evening

After cross-plan analysis vs. master plan errata + codebase spot-check:

1. **Cooldown clock source: `CLOCK_MONOTONIC`** explicitly. Wall clock can NTP-jump backward; monotonic clock won't. Originally underspecified.
2. **`g_notify` ownership**: `extern NotifyState* g_notify;` in `Notify.hpp`, `NotifyState* g_notify = nullptr;` in `main.cpp`. Specified explicitly to avoid multi-TU link errors.
3. **Commit 3 descoped to stderr-only first ship.** Original plan said "reuse TLS pattern from BinanceCrypto.hpp" for HTTPS POST — but BinanceCrypto is streaming WSS, not one-shot HTTP POST. Real options were 4 (custom OpenSSL helper / libcurl / shell-out / stderr-only). Master plan errata picks (d) stderr-only initially, defer Slack/Telegram backends to **Phase 8b.1** when unattended-run experience tells us alerts are a real gap.
4. **Disconnect log site list correction**: `BinanceUserData.hpp:397` is a counter `fetch_add`, not a log line. Real disconnect log sites are 405, 429, 465. Drop 397 from the wire-up list.

Original prose preserved below; corrections inline at the relevant blocks.

## Context anchors — files to read FIRST

```
plans/live-readiness-master.md         ← orchestration + anti-toy discipline
CoreFrameworks/PortfolioController.hpp        ← line 853 (KILL TRIGGER), 1448, 1459 (kill switch trips)
main.cpp                                       ← line 96 (orphan-halt), 263, 771-794 (orphan logs)
DataStream/BinanceUserData.hpp                ← line 397, 405, 429, 465 (reconnect logs)
DataStream/BinanceCrypto.hpp                  ← reconnect log sites (similar pattern)
DataStream/BinanceDepth.hpp                   ← line 211-213 (reconnect)
CoreFrameworks/ControllerConfig.hpp           ← config field placement
```

Branch state expected: on `experiment/live-readiness`. Doesn't conflict with Phase 8 or 8a — touches different files.

## Failure mode IDs covered

- **Unattended live operation has no notification path** — the engine logs to file but doesn't actively notify on disconnects, kill-switch trips, orphan detection, daily loss thresholds, or order rejections. A 30-minute disconnect on a remote VPS goes unnoticed until the next manual check.
- **Logs are forensic, not actionable** — file logs work for post-mortem but require human attention to surface real-time problems.

## Status update

The engine already emits structured log lines for every alertable event (`[KILL]`, `[ENGINE]`, `[LIVE]`, etc — see context anchors). Phase 8b doesn't *find* these events; it *routes* them through a notification channel.

Design choice: the alertable-event sites stay where they are. We add a sibling `Notify_Send(level, subject, body)` call at each site. The notifier itself runs through a queue + dedicated thread to keep allocation + network I/O off the slow path.

## Commit plan (in order)

### Commit 1: `Notify.hpp` interface + queue + dedicated thread

**Goal:** the notifier primitive. Pluggable backend (stderr, Slack, Telegram). Queued + threaded so callers never block on network I/O.

**File:** `CoreFrameworks/Notify.hpp` (new) and a corresponding `.cpp` if the implementation is heavy

**Approach:**

```cpp
#ifndef NOTIFY_HPP
#define NOTIFY_HPP

#include <stdint.h>
#include <pthread.h>

// Severity levels — callers tag their events. Backend decides routing.
enum NotifyLevel {
    NOTIFY_INFO    = 0,  // status updates, session start/end, info-level
    NOTIFY_WARN    = 1,  // recoverable issues (reconnect, transient errors)
    NOTIFY_ALERT   = 2,  // user-attention-required (kill switch trip, orphan)
    NOTIFY_CRITICAL = 3, // engine cannot continue safely
};

// One queued event. Heap-free per-event (queue holds POD).
struct NotifyEvent {
    int level;                  // NotifyLevel
    int event_kind;             // user-defined kind id for throttling key
    uint64_t timestamp_us;
    char subject[128];
    char body[512];
};

// Backend interface — function pointer, set at Init.
typedef int (*NotifyBackendFn)(const NotifyEvent *evt, void *backend_state);

// Throttling: per-event-kind cooldown. Same kind firing within cooldown_us is dropped.
#define NOTIFY_KINDS_MAX 16

struct NotifyState {
    pthread_mutex_t lock;
    pthread_cond_t  cond;
    NotifyEvent     queue[64];   // ring buffer
    int             head;
    int             tail;
    int             count;
    int             shutdown;

    // throttle state
    uint64_t        last_fired_us[NOTIFY_KINDS_MAX];
    uint64_t        cooldown_us;  // default: 60000000 = 60 sec

    // backend
    NotifyBackendFn backend;
    void           *backend_state;

    pthread_t       worker_tid;
    int             worker_started;
};

// API:
//   NotifyState_Init    — set up queue + start worker thread + install backend
//   Notify_Send         — enqueue an event. Non-blocking. Drops on full queue
//                         (rate-limit failsafe; warn to stderr if drops).
//   NotifyState_Shutdown — drain + stop thread + free
static inline void NotifyState_Init(NotifyState *ns,
                                      NotifyBackendFn backend, void *backend_state,
                                      uint64_t cooldown_us);
static inline void Notify_Send(NotifyState *ns, int level, int kind,
                                 const char *subject, const char *body);
static inline void NotifyState_Shutdown(NotifyState *ns);

// Default backend: stderr only (works without internet, useful for dev)
static inline int NotifyBackend_Stderr(const NotifyEvent *evt, void *state);

// Slack webhook backend (POST to incoming webhook URL)
struct NotifySlackState {
    char webhook_url[512];   // https://hooks.slack.com/services/...
};
static inline int NotifyBackend_Slack(const NotifyEvent *evt, void *state);

// Telegram backend (POST to bot API)
struct NotifyTelegramState {
    char bot_token[128];
    char chat_id[64];
};
static inline int NotifyBackend_Telegram(const NotifyEvent *evt, void *state);

#endif
```

**Implementation outline:**

- Worker thread loops on cond_wait, pops events, calls backend
- `Notify_Send`:
  1. Check throttle: `now_monotonic_us - last_fired_us[kind] >= cooldown_us`? If not, drop (no enqueue). **Use `clock_gettime(CLOCK_MONOTONIC, ...)` — amendment #1.** Wall clock can NTP-jump backward; monotonic clock won't.
  2. Lock, push event into ring buffer (drop on full + log to stderr)
  3. Update `last_fired_us[kind]`
  4. Signal cond
- Backend dispatch (amendment #3): commit 1 supports the function-pointer interface but only `NotifyBackend_Stderr` ships in this phase. Slack/Telegram backends deferred to Phase 8b.1.
- `NotifyState_Shutdown`: set shutdown flag, signal cond, join thread, free state

**`g_notify` ownership (amendment #2):**
```cpp
// In Notify.hpp (after struct NotifyState):
extern NotifyState* g_notify;

// In main.cpp (single TU that defines storage):
NotifyState* g_notify = nullptr;
```

Backtest leaves `g_notify` null → all `Notify_Send` callers must `if (g_notify) Notify_Send(...)` — no-op when not initialized.

**Anti-drift checks:**
- [ ] `Notify_Send` is non-blocking — never holds lock for I/O
- [ ] Queue full = drop + stderr warning (no infinite memory growth)
- [ ] Backend failure = log + continue (one bad webhook doesn't break engine)
- [ ] No allocations in `Notify_Send` (events are POD; the queue is fixed-size)

**Anti-toy checks:**
- [ ] Worker thread doesn't run during backtest (no Init → no thread → no surprises)
- [ ] Default cooldown is 60s — prevents spam on disconnect storms
- [ ] Subject/body are bounded char arrays — no format-string injection or arbitrary length

**Testing:** unit-style. Init with stderr backend, fire 10 events, verify all printed. Init with stderr backend + 60s cooldown, fire 10 events with same kind — only first prints. Shutdown cleanly.

### Commit 2: Wire `Notify_Send` into existing alertable-event sites

**Goal:** every existing alertable `fprintf` gets a sibling `Notify_Send` call. No new event sources — just routing existing ones.

**Files (each adds 1-2 lines):**
- `CoreFrameworks/PortfolioController.hpp:853` — `[KILL] TRIGGER` ✓ verified 2026-04-25
- `CoreFrameworks/PortfolioController.hpp:1448` — `[KILL] daily loss exceeded` ✓ verified
- `CoreFrameworks/PortfolioController.hpp:1459` — `[KILL] drawdown exceeded` ✓ verified
- `main.cpp:96` — `[ENGINE] halting - refusing to reconnect with orphaned positions` ✓ verified
- `main.cpp:263` — `[LIVE] orphaned BTC ... selling to recover` ✓ verified
- `main.cpp:771` — `[LIVE] WARNING: orphaned real positions` ✓ verified
- `DataStream/BinanceUserData.hpp:405, 429, 465` — disconnect/reconnect logs (amendment #4: 397 dropped, it's a counter `fetch_add` not a log line)
- `DataStream/BinanceCrypto.hpp:reconnect_sites` — same
- `DataStream/BinanceDepth.hpp:211` — same. **Note: 8a also adds `_LogGap` here. Both calls coexist on different lines; ensure ordering is `_LogGap` first (Phase 8a), then `Notify_Send` (this phase).**

**Approach:**

Define event kind enum in a central place (e.g. `Notify.hpp`):
```cpp
enum NotifyKind {
    NK_KILL_TRIGGER         = 0,
    NK_KILL_DAILY_LOSS      = 1,
    NK_KILL_DRAWDOWN        = 2,
    NK_ORPHAN_HALT          = 3,  // engine refuses to start with orphans
    NK_ORPHAN_DETECTED      = 4,  // engine detected and recovering
    NK_DISCONNECT_TRADE     = 5,
    NK_DISCONNECT_DEPTH     = 6,
    NK_DISCONNECT_USERDATA  = 7,
    NK_ORDER_REJECTED       = 8,
    NK_SESSION_START        = 9,  // optional: info-level "engine started"
    // ... add as needed
};
```

Pattern at each site (example for kill switch trip):
```cpp
{ char ts[16]; log_ts(ts, sizeof(ts));
  fprintf(stderr, "[%s] [KILL] daily loss %.2f%% exceeded limit — trading halted\n", ts, pct);
  if (g_notify) {
      char body[256];
      snprintf(body, sizeof(body),
                "Daily loss %.2f%% exceeded the configured limit. "
                "Engine has halted all buying. Investigate immediately.",
                pct);
      Notify_Send(g_notify, NOTIFY_ALERT, NK_KILL_DAILY_LOSS,
                   "[ENGINE] Kill switch — daily loss", body);
  }
}
```

`g_notify` is a global pointer set at engine init (or passed through context where threading allows). Backtest leaves it null → `Notify_Send` is a no-op (or doesn't fire because the global isn't set up).

**Anti-drift checks:**
- [ ] Backtest behavior unchanged (no Notify state initialized → all calls no-op)
- [ ] Existing fprintf lines stay as-is (file logs are unchanged)
- [ ] Each site uses the same NotifyKind for the same logical event (so cooldown applies consistently)

**Anti-toy checks:**
- [ ] No `Notify_Send` calls in the hot path (verify by inspecting tick loop)
- [ ] Critical events (NOTIFY_CRITICAL) bypass cooldown? No — even critical events must respect cooldown to prevent storms. Document this as a tradeoff.

**Testing:** unit-test each site fires the right kind. Manual: trigger kill switch via testnet, verify alert fires.

### Commit 3: Backend implementations (stderr-only initial ship — amendment #3)

**Goal:** stderr backend lands here. Slack/Telegram deferred to Phase 8b.1 follow-up.

**Why descoped (amendment #3):** original plan said "reuse the TLS pattern from BinanceCrypto.hpp." That's a streaming WSS connection, not a one-shot HTTP POST. Real options were 4: (a) custom OpenSSL helper ~150 lines, (b) link libcurl new dependency, (c) shell-out via `popen()`, (d) stderr-only initial. Per master plan errata, picking (d) for the first ship — stderr alerts piped through `tail -f` or syslog are sufficient until unattended-run experience tells us otherwise. Real backends land in Phase 8b.1 when the gap is real.

**Files:**
- `CoreFrameworks/Notify.hpp` (or split into Notify.cpp if large)
- `CoreFrameworks/ControllerConfig.hpp` — webhook URL / bot token cfg fields

**Approach:**

1. **Stderr backend** (default, ships now):
   ```cpp
   int NotifyBackend_Stderr(const NotifyEvent *evt, void *state) {
       (void)state;
       const char *level_str[] = {"INFO", "WARN", "ALERT", "CRITICAL"};
       fprintf(stderr, "[NOTIFY %s] %s — %s\n",
               level_str[evt->level], evt->subject, evt->body);
       return 0;
   }
   ```

2. **Slack webhook backend**: **DEFERRED to Phase 8b.1.** Will use HTTP POST when implemented; backend choice (custom OpenSSL helper / libcurl / popen-curl) decided then based on operational need.

3. **Telegram backend**: **DEFERRED to Phase 8b.1.** Same reasoning.

4. **Cfg fields** in `ControllerConfig.hpp` — keep all fields defined now even though only stderr backend works in this phase. Phase 8b.1 will add backend impls without changing cfg shape:
   ```cpp
   int notify_enabled;            // 0 = disabled (default)
   int notify_backend;            // 0 = stderr (only working option in 8b)
                                  // 1 = slack (deferred to 8b.1)
                                  // 2 = telegram (deferred to 8b.1)
   char notify_slack_webhook[512];   // unused in 8b, parsed for forward-compat
   char notify_telegram_token[128];  // unused in 8b, parsed for forward-compat
   char notify_telegram_chat[64];    // unused in 8b, parsed for forward-compat
   uint32_t notify_cooldown_secs;    // default 60
   ```

   On engine init, if `notify_backend != 0`, log warning: "[NOTIFY] backend %d not yet implemented (Phase 8b.1), falling back to stderr" and use stderr.

5. Engine init (in main.cpp) — amendments #2 + #3, stderr-only this phase:
   ```cpp
   // amendment #2 — definition lives in main.cpp
   NotifyState* g_notify = nullptr;

   static NotifyState g_notify_state;
   if (cfg.notify_enabled) {
       if (cfg.notify_backend != 0) {
           fprintf(stderr, "[NOTIFY] backend=%d not yet implemented "
                           "(Phase 8b.1), falling back to stderr\n",
                   cfg.notify_backend);
       }
       NotifyState_Init(&g_notify_state, NotifyBackend_Stderr, /*state=*/nullptr,
                        cfg.notify_cooldown_secs * 1000000ULL);
       g_notify = &g_notify_state;
   }
   ```

**Anti-drift checks:**
- [ ] Default `notify_enabled=0` — no behavior change unless opted in
- [ ] Webhook URL / bot token are NOT logged (leak protection)
- [ ] Backend failure (network down, 403 from webhook) logs once per cooldown, doesn't keep retrying

**Anti-toy checks:**
- [ ] HTTPS calls run on the worker thread, never on slow path
- [ ] Connection timeouts set (don't block the worker thread forever on a hung webhook)
- [ ] Tokens stored in cfg file with same secret-handling rules as exchange API keys (don't commit, separate file, file permissions checked)

**Testing:** Manual. Set up a test Slack webhook (free tier), configure cfg, fire a kill switch on testnet, verify the message arrives.

### Commit 4: Cfg + UI + changelog

**Goal:** expose notify cfg in Settings panel, document.

**Files:**
- `GUI/SettingsPanel.hpp` — Settings UI fields
- `engine.cfg` — documented entries
- `DOCS/changelogs/2026-04-XX-phase8b-operational-monitoring.md`
- `CLAUDE.md` — add "Operational Monitoring" subsection under Safety Invariants

**Approach:**

1. Settings panel section:
   ```cpp
   {"notify_enabled", "Enabled", "Operational Monitoring", CFG_BOOL, NULL,
    "0 = file logs only (default)\n"
    "1 = enable real-time alerts via configured backend"},
   {"notify_backend", "Backend", "Operational Monitoring", CFG_INT, "%d",
    "0 = stderr only (dev default)\n"
    "1 = Slack webhook\n"
    "2 = Telegram bot"},
   {"notify_cooldown_secs", "Cooldown s", "Operational Monitoring", CFG_INT, "%d",
    "Min seconds between alerts of the same kind\n"
    "Default 60. Lower = more spam on storms."},
   // Slack/Telegram fields — CFG_PATH for the URL/token to allow editing without showing the value in plaintext
   ```

2. CLAUDE.md Safety Invariants new subsection:

   ```markdown
   ### Operational Alerting

   When adding a new alertable event:
   1. Add a new `NK_*` kind in `Notify.hpp`
   2. Call `Notify_Send(g_notify, level, kind, subject, body)` alongside the existing fprintf
   3. Choose level: INFO (status), WARN (recoverable), ALERT (attention required), CRITICAL (engine unsafe)
   4. Use the same kind for the same logical event everywhere (cooldown is per-kind)
   5. NEVER call `Notify_Send` from the hot path — only slow path / threads
   6. Subject ≤ 128 chars, body ≤ 512 chars
   ```

**Anti-drift checks:**
- [ ] Cfg fields all have sane defaults
- [ ] Settings panel handles disabled state (greys out webhook fields when notify_enabled=0)
- [ ] Phase 8b never required to run engine — backtest, paper, and live (with notify_enabled=0) all work unchanged

## Verification (after EACH commit)

```bash
cmake --build build -j$(nproc)
cmake --build build_gui -j$(nproc)
build/controller_test
```

## Verification (after ALL 4 commits)

Manual on testnet:

1. Configure a test Slack webhook (or Telegram bot)
2. Set `notify_enabled=1`, `notify_backend=1` (Slack), webhook URL in cfg
3. Run engine, manually trip the kill switch (set very low daily_loss_pct, run until it fires)
4. Verify Slack message arrives within cooldown window
5. Trip again immediately — verify cooldown drops the duplicate (no spam)
6. Wait > cooldown_secs, trip again — verify a new message arrives
7. Disconnect network briefly — verify reconnect alerts fire

## Definition of done

- [ ] All 4 commits land cleanly on `experiment/live-readiness`
- [ ] controller_test passes after each (296/296 post-5d baseline; +14 after Phase 8b tests = 310/310 by end)
- [ ] Manual end-to-end test passes (Slack OR Telegram at minimum)
- [ ] CLAUDE.md "Operational Alerting" invariant added
- [ ] All existing alertable fprintf sites have sibling `Notify_Send` calls (verify with grep)

## Tag at end of Phase 8b

```bash
git tag phase8b-complete
```

## Known limitations / deferred

- **Email backend** — deferred. SMTP integration is more code than webhook. Use Slack/Telegram email-bridges if email is required.
- **PagerDuty / SMS** — deferred. Webhook backends can route to these via downstream tooling.
- **Per-level filtering** — current design routes all levels to the configured backend. Future enhancement: route INFO to one channel, ALERT to another.
- **Persistent event log** — alerts are fire-and-forget; no on-disk record beyond the file logs. Add SQLite-based event log if forensic queries become useful.
- **Retry on backend failure** — current design fails forward (logs the failure, drops the event). Add exponential-backoff retry if reliability needs it.
