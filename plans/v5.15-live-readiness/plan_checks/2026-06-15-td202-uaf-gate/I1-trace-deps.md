# I-1 — Blast-radius / caller-set dep-trace (TECH_DEBT-202 OMS async-writer UAF)

**Lens:** Does ANY production (non-test) path re-init / double-init an OrderEventLog that has a RUNNING async writer — or Free one whose `writer_thread_active` was clobbered to 0 while the writer thread still runs?

**Skill:** `/trace-deps` (Layer-2 INVESTIGATIVE, read-only, no Layer-3).
**Engine HEAD:** 3ee95dc. All file:line grepped, not recalled.

---

## VERDICT: **TEST-ONLY** (latent-production-UAF REFUTED)

The double-init that defeats the join is reachable from **exactly one site**, and it is a **test**: `tests/controller_test.cpp:26457`. Every production OMS lifecycle is a clean single `Init` → single `Shutdown`/`Free` pair, with the writer thread joined before the ring is freed. No production path re-inits, double-inits, or clobbers `writer_thread_active` on a live writer.

---

## Root cause — RE-CONFIRMED independently against code (not inherited)

- `OrderEventLog_Init` (OrderEventLog.hpp:204) unconditionally `SPSCRing_Init(&log->async_ring)` (:231) + `writer_thread_active.store(0)` (:232) with **no StopAsyncWriter first**.
- `OrderEventLog_StopAsyncWriter` (:398) guards on `if(!writer_thread_active.load()) return;` (:399) → a clobbered-to-0 flag **no-ops the join**.
- `OrderEventLog_Free` (:247) calls Stop first (:251) — the join EXISTS — then `munmap`s the ring (:263). If the flag was clobbered, Free skips the join and `munmap`s the ring under the live writer → UAF at `SPSCRing_TryPop` (SPSCRing.hpp:180) inside `OrderEventLog_AsyncWriterRoutine` (:355).

Confirmed: the clobber requires an `Init` (or `OrderManager_Init` → `OMS_INIT_AUTOPOPULATE`) to run on a log whose writer is already started. `OrderEventLog_Reset` (:492) is SAFE — it touches only `count`/`next_event_id`/`disk_file` (:494-518); it does **NOT** call `SPSCRing_Init` and does **NOT** touch `writer_thread_active`.

## Ownership confirmed (Step 3)

`OrderManagerState<F>::event_log` is owned **BY VALUE** — `OrderEventLog<F> event_log;` (OrderManager.hpp:299). So `delete oms` / `~OrderManagerState()` (:631→`OrderManager_Shutdown`:1608→`OrderEventLog_Free`:1609) frees the ring. The struct is move/copy-deleted (SPSCRing deleted-copy; OrderManager.hpp:604-609) — no hidden duplication path.

## Caller-classification table

| Caller (file:line) | Function | Prod/Test | Re-inits live log? |
|---|---|---|---|
| OrderEventLog.hpp:420 | `OrderEventLog_Init` (from InitWithFile, guarded `if(!entries)`) | both | **N** — only inits if not already allocated; never after Start |
| OmsFieldRegistry.hpp:734 | `OrderEventLog_Init` (AUTOPOPULATE L4 mode-1 branch) | prod | **N** — boot-once, before L5 Start |
| OmsFieldRegistry.hpp:754 | `OrderEventLog_Init` (AUTOPOPULATE L4 mode-0 `else`) | prod | **N** — boot-once, before L5 Start |
| OmsFieldRegistry.hpp:752 | `OrderEventLog_InitWithFile` (AUTOPOPULATE L4) | prod | **N** — boot-once, before L5 Start |
| OmsFieldRegistry.hpp:758 | `OrderEventLog_StartAsyncWriter` (AUTOPOPULATE L5, unconditional) | prod | n/a (the Start) |
| OrderManager.hpp:1609 | `OrderEventLog_Free` (from `OrderManager_Shutdown`) | both | n/a — Stop+join EXISTS (flag never clobbered in prod) |
| Async.hpp:737 | `OrderEventLog_Reset` (paper-reset) | prod | **N** — Reset is truncate-only; no ring re-init, no flag touch |
| Run.hpp:674 | `OrderManager_Init` (engine boot) | prod | **N** — single init; matching Shutdown at Run.hpp:2327 |
| Run.hpp:2327 | `OrderManager_Shutdown` (engine teardown) | prod | n/a — single teardown |
| BacktestSharded.hpp:187 | `OrderManager_Init` (backtest boot) | prod | **N** — single init; RAII ~OrderManagerState frees |
| ControllerEventLoop.hpp:970 | `OrderManager_Init` (legacy single-core helper) | prod (deprecated path) | **N** — single init |
| controller_test.cpp:6990/7060/7160/7233/7465/9797/10024/11755/17000/17084/17160/20109/20205/20351/20462/20529/20570/20619/20778/28037/28054/28066 | `OrderManager_Init` | test | **N** — one Init per scoped oms |
| controller_test.cpp:16926 | `OrderEventLog_Init` (`log`) | test | **N** — single Init, Free at :16969 |
| controller_test.cpp:17320 | `OrderEventLog_Init` (`log`) | test | **N** — single Init; re-arm uses Reset (:17333), not Init |
| controller_test.cpp:17408 | `OrderEventLog_Init` (`log2`) | test | **N** — fresh object, single Init, Free at :17413 |
| **controller_test.cpp:26457** | **`OrderEventLog_Init(&oms->event_log)`** | **test** | **YES** — the TD-202 trigger (see below) |
| controller_test.cpp:26432 | `OrderEventLog_InitWithFile` (`oel`) | test | **N** — standalone log, Free at :26441 |

## The single triggering site (test-only)

`controller_test.cpp:26454-26457` (Ship-B P3 D-173 commission test):
```
auto* oms = new tt::OrderManagerState<64>();
tt::OrderManager_Init(oms, adapter, /*live*/0, /*partials*/0, MQ(10000.0));  // event_log_mode defaults to 0
tt::OrderEventLog_Init(&oms->event_log);   // SECOND Init on the SAME event_log
```
`OrderManager_Init` runs `OMS_INIT_AUTOPOPULATE`: with the defaulted `event_log_mode=0`, Layer-4 takes the `else` → `OrderEventLog_Init` (OmsFieldRegistry.hpp:754), then **Layer-5 `OrderEventLog_StartAsyncWriter` runs UNCONDITIONALLY** (OmsFieldRegistry.hpp:758). So the writer thread **is** running after the first Init even in mode-0. Line 26457's second `OrderEventLog_Init` then clobbers `writer_thread_active→0` + `SPSCRing_Init` under the live writer → `OrderEventLog_Free` at :26490 skips the join → UAF. This is the exact TD-202 mechanism, and the only reachable instance is this test. The test comment ("mode 0 leaves the log uninitialized; the test reads the fee slot") is a stale/incorrect assumption — mode-0 still STARTS the writer; the redundant re-Init is the bug.

## Why production is immune

1. **Boot init is once.** `OMS_INIT_AUTOPOPULATE` is the sole production initializer; it runs exactly once per OMS at boot (Run.hpp:674 / BacktestSharded.hpp:187). Its internal `OrderEventLog_Init` runs strictly BEFORE `StartAsyncWriter` (L4 before L5, enforced by ordering comments at OmsFieldRegistry.hpp:655-658) — never after.
2. **Paper-reset never re-inits the log.** `OMS_RESET_AUTOPOPULATE` (Async.hpp:703) is Layer-1 (value-field reset) + Layer-2 (Portfolio_Init) only — it does NOT touch event_log. Disk truncation uses `OrderEventLog_Reset` (Async.hpp:737), which is ring-/flag-untouching. The writer thread keeps running across a paper-reset, uninterrupted. So the `persist-8` zombie-active-flag paper-reset context does NOT touch this surface.
3. **Teardown joins before free.** Production teardown is `OrderManager_Shutdown` (Run.hpp:2327) or RAII `~OrderManagerState` → `OrderEventLog_Free` → Stop+join (:251) with the flag intact → ring freed only after the writer exits.
4. **No production InitWithFile-after-Start.** `OrderEventLog_InitWithFile`'s internal `OrderEventLog_Init` is guarded `if(!log->entries)` (:420) and only ever runs inside the boot Layer-4, before Start.

## Other lifecycle hazards tripped over (NOT the re-init one)

- **H-A (LOW, latent, NOT triggered today): unconditional Start in mode-0.** AUTOPOPULATE Layer-5 starts the async writer even when `event_log_mode==0` (no disk, in-memory-only). Functionally fine (sync vs async both correct), but it means "mode 0" does NOT imply "no writer thread" — which is precisely the stale assumption that produced the :26457 bug. Worth a one-line guard or a comment, so the next caller doesn't repeat the test's mistake. Not a UAF on its own.
- **H-B (informational): `OrderEventLog_Free` idempotency depends on the flag being truthful.** Free→Stop→`if(!active)return` is only safe-idempotent because production never clobbers the flag. The fix for TD-202 (make `Init` call `StopAsyncWriter` first, OR assert `!writer_thread_active` in Init) also hardens this invariant structurally rather than leaving it convention-protected. A defensive `OrderEventLog_Init` that Stops-first would make BOTH the test trigger and any future re-init caller safe — i.e., a structural close, not a test-only patch, even though the only CURRENT trigger is test-only.

## Scope conclusion for the fix

The **triggering bug** is test-only (a redundant `OrderEventLog_Init` at controller_test.cpp:26457; the minimal fix is to delete that line — the first `OrderManager_Init` already initialized + started the log). But per the guards-compound discipline, the **defensible structural fix** is to make `OrderEventLog_Init` `StopAsyncWriter`-first (or `assert(!writer_thread_active)`), which closes the class for any future re-init caller at ~zero cost and removes the latent H-A footgun. Either way: **no latent production UAF exists today** — the "test-only" framing of the trigger is CONFIRMED.
