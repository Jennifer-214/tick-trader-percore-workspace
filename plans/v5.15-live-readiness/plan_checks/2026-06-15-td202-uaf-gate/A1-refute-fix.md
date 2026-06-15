# A1 — Adversarial refutation: TD-202 OMS async-writer UAF fix candidates

**Auditor:** Layer-2 adversarial subagent (DEFAULT-REFUTED framing)
**Engine HEAD:** 3ee95dc
**Surface:** `CoreFrameworks/OrderEventLog.hpp`, `SPSCRing.hpp`, `MemHeaders/OmsFieldRegistry.hpp:718-759`, `OrderManager.hpp`, `EngineSharded/Async.hpp`
**Date:** 2026-06-15

---

## Ground-truth confirmations (grep-verified)

- Writer started **unconditionally** at `OmsFieldRegistry.hpp:758` (Layer-5, all modes).
- `StartAsyncWriter` has **exactly two** invocation classes: the autopopulate Layer-5 (`:758`) and **direct** test calls (`controller_test.cpp:17338`, `:17409`). Grep for `OrderEventLog_StartAsyncWriter` outside header+registry returned nothing else.
- Production callers of `OrderManager_Init`: `Run.hpp:674` passes `(int)cfg.oms_event_log_mode` (NOT hardcoded 1); `BacktestSharded.hpp:187` and `ControllerEventLoop.hpp:970` pass the default `event_log_mode=0`.
- `OrderEventLog_Reset` callers: production `Async.hpp:737` (drainer thread) + `OrderEventLog.hpp:492` (def). No others in non-test code.
- `~OrderManagerState()` → `OrderManager_Shutdown()` (`:631`, `:1608`) → `OrderEventLog_Free()` (`:1609`) → `StopAsyncWriter` (`:251`). This RAII is the EXISTING fix for the 9-test writer-leak (comment `OrderManager.hpp:597-601`).

---

## FIX-1 — gate writer-start `if (event_log_mode==1 && _has_disk_path)` — **REFUTED**

**The hole (concrete, file:line):** the event log is appended **unconditionally, with NO `event_log_mode` gate**, inside `OrderManager_HandleFill` at **`OrderManager.hpp:1355`**. HandleFill is the live-fill path. Live trading bypasses the mode-0 early-return (`:929-934` requires `!LIVE_TRADING`), so for **live trading with `oms_event_log_mode==0`** the engine reaches `:1355` and writes events into `event_log`. FIX-1's gate (`event_log_mode==1 && _has_disk_path`) would **not** start the writer in that configuration.

Two consequences:
1. **Functional, not UAF:** with no writer active, `Append` (`:324`) takes the sync fallback (`:341-342` → `ApplyEvent`). The drainer is the sole `Append` caller in production, so single-threaded `ApplyEvent` on `entries[]` is correct, and `disk_file` is null in mode-0 so no disk write is attempted. So FIX-1 does **not** corrupt live mode-0 logging — but it silently removes the disk-stall isolation the async writer was built for (`OrderEventLog.hpp:170-177`) on **any** live run that forgot to set `oms_event_log_mode=1`. That is a behavioral regression on the capital path masked as a test-UAF fix.
2. **Gate is the wrong predicate for the stated CLAIM.** The CLAIM "no writer in mode-0 → nothing to race" is TRUE for the test (the test never reaches live HandleFill), but the gate conflates "needs async disk isolation" with "writes to the in-memory log at all." `_has_disk_path` is an additional confound: `InitWithFile` can *fail to open* the file (`:459-463`) or *disable persistence* after a failed rotate (`:452`), leaving `disk_file==nullptr` even though the gate passed and the writer started — so the gate does not even guarantee the writer has a file to isolate. The inverse (live mode-0, disk path empty, fills still logged in memory) is the live hole above.

**Does anything assume `writer_thread_active==1` post-Init?** The async-writer test (`controller_test.cpp:17341-17359`, `:17409-17415`) asserts `writer_thread_active==1` after **direct** `StartAsyncWriter` and `==0` after Stop — it does NOT go through `OMS_INIT_AUTOPOPULATE`, so FIX-1's Layer-5 change does not break those asserts. No production reader of `writer_thread_active==1` as an invariant was found. So FIX-1 doesn't break the existing async tests — but that's not the same as fixing the class.

**Sync-fallback parity (`:341-342`):** the sync path runs the *same* `ApplyEvent` (disk write, `log_full_drops`, ordering) the writer would (`:288-289` documents shared use), so functional parity holds. The gap is purely the lost disk-stall isolation + the unprincipled predicate.

**Verdict: REFUTED.** FIX-1 leaves the in-memory log written-but-unisolated on live+mode-0 (`OrderManager.hpp:1355` is mode-blind), and the gate predicate does not actually track "writer needed." It papers the *test* trigger without closing the class (the double-Init at `controller_test.cpp:26457` is still UB if any future test Starts then re-Inits). Treat as INCOMPLETE; pair with the Init hardening (FIX-2) and/or a corrected predicate (start the writer whenever the log is live at all, i.e. live OR mode-1).

---

## FIX-2 — harden `OrderEventLog_Init` to StopAsyncWriter-first when writer active — **REFUTED (TOCTOU + overwritten-handle UB)**

**TOCTOU hole 1 — the create→publish window (`StartAsyncWriter:386-393`):**
```
386  pthread_create(&log->writer_thread, ...);   // thread is LIVE, running AsyncWriterRoutine
393  writer_thread_active.store(1, release);      // flag set only AFTER
```
Between `:386` and `:393` the writer thread exists and is executing the routine, but `writer_thread_active==0`. If `OrderEventLog_Init` runs in that window (concurrent Init on another thread), the new FIX-2 guard `if (writer_thread_active.load()) StopAsyncWriter()` **reads 0, skips the stop**, and proceeds to `SPSCRing_Init(:231)` + `writer_thread_active.store(0)(:232)` **under a live writer** — the exact re-init-under-live-thread the fix claims to close. The live thread then races `SPSCRing_TryPop(:355)` against the concurrent `SPSCRing_Init` (`SPSCRing.hpp:95-99` stores head/tail/cached_* non-atomically relative to the consumer's `tail.load`).

This window is *narrow* and requires two threads in `Init`/`Start` concurrently. The known TD-202 trigger (`controller_test.cpp:26457`) is **single-threaded sequential** (Init → … → Init), so for the *known* trigger the guard's check is reliable: by `:26457` the writer (if started at `:868` via autopopulate) has `writer_thread_active==1` set, FIX-2 stops+joins it, then re-inits cleanly. **So FIX-2 closes the known single-threaded trigger.** But the CLAIM is "closes the re-init-defeats-join *class*" — and the class includes the concurrent window above, which it does NOT close. A determinism/capital-grade fix cannot claim class-closure with a live TOCTOU window.

**TOCTOU hole 2 — stopped-but-flag-not-yet-0:** symmetric window in `StopAsyncWriter`: `pthread_join(:401)` completes, then `store(0)(:402)`. A reader between join-return and `:402` sees 1 (harmless for FIX-2 — it would stop-again, but `StopAsyncWriter`'s own guard `:399` reads 1, stores 1 to `should_stop`, and joins an **already-joined** thread → **UB / EINVAL**). So FIX-2 calling StopAsyncWriter when it *races* a concurrent Stop can double-join.

**Overwritten-handle UB (independent of TOCTOU):** `writer_thread` is a single `pthread_t` (`OrderEventLog.hpp:192`). If FIX-2's guard ever misses (hole 1) and `Init` proceeds, a subsequent `StartAsyncWriter` does `pthread_create(&log->writer_thread, …)` (`:386`) **overwriting** the handle of the still-running prior thread. The prior thread is now unjoinable (its handle is lost) → `pthread_join` on the new handle (at eventual Free) does not join the leaked first thread = resource leak + the leaked thread still holds a pointer to `log` and races `entries[]`/`disk_file`. This is the *original* TD-202 UAF shape, merely relocated.

**Contract for the fresh Layer-4 callers (`:734`, `:754`):** those call `Init` on a never-started log. FIX-2's guard `if (writer_thread_active.load())` reads the freshly-zeroed flag (or, on a brand-new stack `OrderManagerState`, *uninitialized* memory before any Init — but autopopulate always runs `Init` before `:758` Start, so in the production sequence the flag is 0 by `:754`). For the production path the guard correctly no-ops. ✔ on that sub-point. But note `OrderEventLog_InitWithFile:420` calls `Init` only `if (!log->entries)` — so the *common* re-entry (LoadFromDisk then InitWithFile) does NOT re-run Init, meaning FIX-2 never fires on the production boot path anyway; it only fires on the literal double-`Init` test.

**Verdict: REFUTED as a class-closure.** Closes the *known single-threaded test trigger* (acceptable as a point-fix) but leaves two live TOCTOU windows (create→publish, join→clear) and an overwritten-`pthread_t` leak shape. **Residual condition for SURVIVES:** only if (a) the orchestrator accepts this as a *point* fix scoped to the single-threaded double-Init (not "the class"), AND (b) it is paired with FIX-1's gate so the writer never starts in the offending test at all (belt-and-suspenders), AND (c) a comment + assert documents that concurrent Init/Start is out of contract. As a standalone "closes the class" claim it fails.

---

## FIX-3 — quiesce the writer before `fclose`/`fopen disk_file` in `OrderEventLog_Reset` — **REFUTED (incomplete; restart + drainer-block gaps)**

**The race FIX-3 targets is REAL (confirmed):** `Reset` runs on the **drainer thread** (`Async.hpp:737`, inside the drainer's reset handler). `paper_reset_in_progress` (`Async.hpp:571`) parks only the **slow-path** threads (comment `:567-570`, `:746-748`) — it does **NOT** park the **async writer** thread. The writer is live (started unconditionally at boot, `:758`) and concurrently:
- `fflush(log->disk_file)` (`OrderEventLog.hpp:372`, idle path) and `fwrite(…, log->disk_file)` (`:303`, inside `ApplyEvent`),

while `Reset` does `fclose(log->disk_file)` (`:501`) then `fopen` (`:502`, `:518`) and overwrites the `disk_file` pointer + zeroes `count` (`:494`). Concurrent `fwrite`/`fflush` on a `FILE*` being `fclose`d is a **classic UAF on the stdio handle** + a torn `disk_file` pointer read. So the bug FIX-3 names exists. *(Note: the drainer is the SPSC producer per `:179`, and it is the one running Reset, so the ring `TryPush`/`TryPop` pair is not itself racing during Reset — the race is purely on `disk_file` + `count`/`entries`, which the writer touches via `ApplyEvent`.)*

**Hole 1 — who restarts the writer?** If `Reset` does stop+join the writer (to quiesce it before `fclose`), the CLAIM is silent on restart. `Reset`'s contract (`:488-490`) is "keep the same file handle open … so subsequent appends keep working without reinitializing" — i.e. logging MUST continue after reset. A stop-join with no matching `StartAsyncWriter` at the end of `Reset` means **logging silently dies after the first paper reset** (Append falls to sync `:341` — which still works functionally, but the disk-isolation is gone and `writer_thread_active` is now 0 permanently, contradicting the boot invariant). If `Reset` *does* restart via `StartAsyncWriter`, it re-enters the FIX-2 TOCTOU surface (create→publish) and overwrites `writer_thread`. So FIX-3 cannot be "stop-join" without also being a correct "restart," and a restart re-opens FIX-2's holes.

**Hole 2 — drainer-block budget.** `pthread_join` (`:401`) blocks the caller until the writer's final drain pass + `fflush` (`:368-372`) completes. The caller is the **drainer** (`Async.hpp:737`); the drainer budget is **≤10μs/cycle** (CoreFrameworks/CLAUDE.md latency table). The writer wakes on a **1ms `usleep`** cadence (`OrderEventLog.hpp:378`), so `join` can block the drainer for **up to ~1ms** — **100× over budget**, and during a disk stall (the very scenario the async writer exists to isolate) the final `fflush(:372)` can block far longer. So FIX-3's stop-join inside Reset **reintroduces the disk-stall-blocks-the-trading-thread coupling** that the async writer was built to break (`:170-177`). A pause/resume (signal-the-writer-to-idle, don't join) would avoid the join cost but still needs a handshake the current atomics don't provide (no "paused" ack).

**Hole 3 — the simpler correct form the CLAIM hints at.** The writer already *owns* `disk_file` exclusively post-Start (SPSC discipline, `:328-329` "writer-thread-only post-Start"). The principled fix is therefore **Reset should NOT touch `FILE* disk_file` at all** — it should enqueue a "reset/rotate" sentinel onto `async_ring` (or set a `should_reset` atomic the writer polls in its loop) so the **writer** performs the `fclose`/`fopen`/re-header on its own thread, preserving single-owner discipline and never blocking the drainer. FIX-3 as stated ("quiesce then the drainer does fclose/fopen") inverts ownership and is the less-correct option. Additionally, `Reset` zeroes `count`/`next_event_id` (`:494-495`) — in-memory state the writer also mutates via `ApplyEvent` (`:298`) — so even with `disk_file` handled, the `count` write races the writer's `entries[count++]`; the sentinel/owner approach fixes both, the fclose-guard approach fixes only the FILE*.

**Verdict: REFUTED.** FIX-3 correctly identifies a real writer↔Reset race on `disk_file` + `count`, but the proposed shape (drainer quiesces, drainer does fclose/fopen) (a) leaves the writer-restart unspecified → silent logging death or FIX-2 TOCTOU re-entry, (b) blocks the drainer up to ~1ms+ on join → 100× latency-budget breach + reintroduces disk-stall coupling, and (c) inverts the single-owner discipline when an enqueue-sentinel / writer-owns-the-FILE* form is strictly more correct and budget-safe. **Residual SURVIVES condition:** only if reframed as "signal the writer (sentinel/atomic) to do the rotate on its own thread; Reset never touches `disk_file`/`count` directly; drainer does not join," which is a *different* fix.

---

## Summary

| Fix | Verdict | Core hole |
|---|---|---|
| FIX-1 (gate writer-start) | **REFUTED** | `OrderManager.hpp:1355` appends to the log **mode-blind**; live+mode-0 still logs in-memory with no writer → lost disk-stall isolation; `_has_disk_path` doesn't track writer-need (InitWithFile can fail open → no file even when gated). Papers the test trigger, doesn't close the class. |
| FIX-2 (Init StopAsyncWriter-first) | **REFUTED** as class-closure | Closes the *single-threaded* double-Init (`controller_test.cpp:26457`) but leaves create→publish (`:386-393`) + join→clear (`:401-402`) TOCTOU windows and an overwritten-`pthread_t` leak shape. Survives only if scoped to "point fix for the known trigger" + paired with FIX-1. |
| FIX-3 (Reset quiesce-then-fclose) | **REFUTED** | Real race named, wrong shape: writer-restart unspecified (silent logging death or FIX-2 re-entry); `pthread_join` blocks the **drainer** up to ~1ms+ (100× the ≤10μs budget) and reintroduces disk-stall coupling; inverts single-owner discipline vs the correct enqueue-sentinel / writer-owns-FILE* form; ignores the `count`/`entries` race. |

**Cross-cutting:** all three fixes are downstream of the root smell that the writer **starts unconditionally** (`:758`) even where it is pointless (paper mode-0, backtest, all 9 direct test `Init`s). The cleanest class-closer is to (a) start the writer iff the log is actually live (live OR mode-1 — keyed on the same predicate HandleFill's `:1355` log-write implies, NOT just `_has_disk_path`), AND (b) give `Init` a "no live writer is permitted at Init" assert/guard (FIX-2's intent) made robust against the create→publish window (e.g., set `writer_thread_active=1` BEFORE `pthread_create`, or use a tri-state), AND (c) make Reset signal the writer rather than touch its `FILE*`. None of the three candidates as written reaches that bar individually.
