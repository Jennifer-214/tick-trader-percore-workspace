# Phase 8b Tests — Operational Monitoring + Alerting

last updated: 2026-04-25

**Sidecar to:** `plans/phase8b-operational-monitoring.md`
**Time budget:** ~2 hours on top of Phase 8b implementation
**Test target:** `tests/controller_test.cpp` (queue + cooldown — pure unit) + optional `tests/notify_test.cpp` (backend integration)
**Coverage goal:** 14-16 assertions

## Why split between two binaries

- **Queue + cooldown logic** = pure POD + threading, fits in controller_test
- **Backend integration** (Slack webhook, Telegram bot) requires network or a mock HTTP server. Optional binary, defer if Phase 8b ships with stderr-only initially (see Phase 8b plan errata note about HTTPS-POST infrastructure).

## Test groups

### Group 1: NotifyState lifecycle (2 assertions)

```cpp
// Init starts thread, Shutdown joins cleanly
{
    NotifyState ns;
    NotifyState_Init(&ns, NotifyBackend_Stderr, /*state=*/NULL,
                     /*cooldown_us=*/1000000);
    ASSERT_EQ(ns.worker_started, 1);
    NotifyState_Shutdown(&ns);
    ASSERT_EQ(ns.shutdown, 1);
    // pthread_join must have returned (not blocked forever)
}
```

**2 assertions**

### Group 2: Notify_Send + backend dispatch (3 assertions)

Use a counting backend for testability — record events instead of routing to stderr:

```cpp
struct CountingBackendState {
    int events_received;
    NotifyEvent last_event;
};

int NotifyBackend_Counting(const NotifyEvent *evt, void *state) {
    CountingBackendState *s = (CountingBackendState*)state;
    s->events_received++;
    s->last_event = *evt;
    return 0;
}

// Notify_Send → backend receives event
{
    CountingBackendState bs = {0};
    NotifyState ns;
    NotifyState_Init(&ns, NotifyBackend_Counting, &bs, /*cooldown_us=*/0);

    Notify_Send(&ns, NOTIFY_ALERT, NK_KILL_TRIGGER, "test subj", "test body");

    // wait up to 200ms for the worker thread to process
    for (int i = 0; i < 20 && bs.events_received == 0; i++) {
        usleep(10000);
    }
    ASSERT_EQ(bs.events_received, 1);
    ASSERT_EQ(bs.last_event.level, NOTIFY_ALERT);
    ASSERT_EQ(bs.last_event.event_kind, NK_KILL_TRIGGER);
    ASSERT_STR_EQ(bs.last_event.subject, "test subj");

    NotifyState_Shutdown(&ns);
}
```

**3 assertions**

### Group 3: Cooldown gate (3 assertions)

This is load-bearing — uses `CLOCK_MONOTONIC` per cross-plan errata fix.

```cpp
// Same kind within cooldown is dropped
{
    CountingBackendState bs = {0};
    NotifyState ns;
    NotifyState_Init(&ns, NotifyBackend_Counting, &bs,
                     /*cooldown_us=*/100000);  // 100ms cooldown

    Notify_Send(&ns, NOTIFY_ALERT, NK_KILL_TRIGGER, "first", "");
    Notify_Send(&ns, NOTIFY_ALERT, NK_KILL_TRIGGER, "second", "");  // dropped
    Notify_Send(&ns, NOTIFY_ALERT, NK_KILL_TRIGGER, "third", "");   // dropped

    usleep(50000);  // let worker drain
    ASSERT_EQ(bs.events_received, 1);  // only "first" got through

    // wait past cooldown, fire again
    usleep(150000);
    Notify_Send(&ns, NOTIFY_ALERT, NK_KILL_TRIGGER, "fourth", "");
    usleep(50000);
    ASSERT_EQ(bs.events_received, 2);

    NotifyState_Shutdown(&ns);
}

// Different kinds fire independently within cooldown
{
    CountingBackendState bs = {0};
    NotifyState ns;
    NotifyState_Init(&ns, NotifyBackend_Counting, &bs,
                     /*cooldown_us=*/1000000);  // 1s cooldown

    Notify_Send(&ns, NOTIFY_ALERT, NK_KILL_TRIGGER,        "a", "");
    Notify_Send(&ns, NOTIFY_WARN,  NK_DISCONNECT_TRADE,    "b", "");
    Notify_Send(&ns, NOTIFY_INFO,  NK_SESSION_START,       "c", "");

    usleep(50000);
    ASSERT_EQ(bs.events_received, 3);  // all three different kinds, all fire

    NotifyState_Shutdown(&ns);
}
```

**3 assertions**

### Group 4: Queue full handling (2 assertions)

```cpp
// Enqueue past capacity drops + warns
{
    CountingBackendState bs = {0};
    // backend that BLOCKS so the queue fills up
    NotifyState ns;
    NotifyState_Init(&ns, BlockingBackend, &bs, /*cooldown_us=*/0);

    // queue capacity is 64; fire 100 events with different kinds
    for (int i = 0; i < 100; i++) {
        Notify_Send(&ns, NOTIFY_INFO, /*kind=*/i % NOTIFY_KINDS_MAX,
                    "spam", "");
    }
    // some should drop. unblock the backend, drain.
    UnblockBackend();
    usleep(200000);

    ASSERT_LT(bs.events_received, 100);  // some dropped (queue was full)
    ASSERT_GTE(bs.events_received, 60);  // most got through

    NotifyState_Shutdown(&ns);
}
```

**2 assertions**

### Group 5: Shutdown drains pending events (1 assertion)

```cpp
// Events enqueued just before shutdown still get through
{
    CountingBackendState bs = {0};
    NotifyState ns;
    NotifyState_Init(&ns, NotifyBackend_Counting, &bs, /*cooldown_us=*/0);

    // fire 5 events, immediately shutdown (worker thread should drain before exit)
    for (int i = 0; i < 5; i++) {
        Notify_Send(&ns, NOTIFY_INFO, /*kind=*/i, "drain test", "");
    }
    NotifyState_Shutdown(&ns);  // should drain queue before joining

    ASSERT_EQ(bs.events_received, 5);
}
```

**1 assertion**

### Group 6: Hooked event sites (3 assertions)

These are integration-y — they verify that production code correctly calls Notify_Send at the right sites. Tested by hooking the global g_notify pointer with a counting backend:

```cpp
// kill switch trip → NK_KILL_TRIGGER fires
{
    NotifyState ns;
    CountingBackendState bs = {0};
    NotifyState_Init(&ns, NotifyBackend_Counting, &bs, /*cooldown_us=*/0);
    NotifyState *prev = g_notify;
    g_notify = &ns;

    // simulate a kill switch trip
    PortfolioController<BACKTEST_FP> ctrl;
    PortfolioController_Init(&ctrl, ControllerConfig_Default<BACKTEST_FP>());
    KillSwitch_Activate(&ctrl, /*reason=*/1);  // daily loss
    // (or call the actual trip path from PortfolioController_Tick)

    usleep(50000);
    ASSERT_EQ(bs.events_received, 1);
    ASSERT_EQ(bs.last_event.event_kind, NK_KILL_TRIGGER);

    g_notify = prev;
    NotifyState_Shutdown(&ns);
}

// disconnect on trade WS → NK_DISCONNECT_TRADE
// (similar pattern)

// orphan detection at startup → NK_ORPHAN_DETECTED
// (similar pattern)
```

**3 assertions**

## Total: 14 assertions in controller_test

| Group | Count | Phase 8b commit it validates |
|---|---|---|
| Group 1: Lifecycle | 2 | Commit 1 (Notify.hpp infrastructure) |
| Group 2: Send+dispatch | 3 | Commit 1 |
| Group 3: Cooldown | 3 | Commit 1 |
| Group 4: Queue full | 2 | Commit 1 |
| Group 5: Shutdown drain | 1 | Commit 1 |
| Group 6: Hooked sites | 3 | Commit 2 |

(Backend integration tests for Slack/Telegram deferred to optional `notify_test.cpp` if HTTPS-POST backend ships.)

## Verification

```bash
cmake --build build -j$(nproc)
build/controller_test
```

Expected: **+14 assertions, 0 failed**.

## Test stubs deferred

- **HTTPS POST backend**: only if Phase 8b commit 3 ships real backends (per errata, deferred to Phase 8b.1). Tests would mock a webhook endpoint with a tiny embedded HTTP server.
- **Network failure resilience**: backend returning 500 / timing out / DNS failing. Mock server with controlled responses. Defer.
- **Throttle correctness under high concurrency**: many threads firing same kind. Defer until threading model proves problematic in real use.
- **Wallclock-jump robustness**: deliberately advance/rewind clock, verify cooldown doesn't break. Defer (usually only matters in containerized or VM environments).

## Anti-drift contract

These tests pin:
- Queue capacity behavior
- Cooldown semantics (per-kind, monotonic-clock-based)
- Lifecycle (init / shutdown ordering)
- Hooked event sites firing the right kinds

Future modifications must not break these tests without an explicit decision (e.g., "we're moving from per-kind to per-(kind,severity) cooldown" gets a new test group, old test stays until its semantic is removed).
