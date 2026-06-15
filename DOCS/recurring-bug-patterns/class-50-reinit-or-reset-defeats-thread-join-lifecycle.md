# Class 50 — Re-init / reset defeats the thread-join lifecycle (spawn-in-Init)

> Codified 2026-06-15 at v5.15.5.F.4d.1.E.0.10 (the TD-202 OMS event-log UAF /precoding-audit-gate, 3-I→3-A + completeness-critic). Per-class file per file-size-split-discipline. **H-promotion deferred to Stage 5** per pattern-codification-lifecycle.

## Shape

A struct **owns a thread** (a `pthread_t` / `*_thread` handle + a `*_thread_active` / `*_should_stop` atomic), and its **`_Init` or `_Reset` re-initializes thread-touched state** (a lock-free ring, a `FILE*`, the active flag, a counter) **WITHOUT first signalling+joining a possibly-running thread**. Two failure modes:

1. **Join-defeat (UAF):** the re-init clobbers the `*_thread_active` flag to 0 while the thread runs → the later `_Free`/teardown join is guarded `if(!active) return` → the join **no-ops** → the resource is freed under the live thread → use-after-free.
2. **Concurrent-resource race:** the re-init mutates a resource the live thread is touching (`fclose`/`fopen` a `FILE*` the thread `fwrite`s; `SPSCRing_Init` a ring the thread pops; zero a non-atomic `count` the thread increments) → use-after-fclose / torn-state / data race, independent of any free.

Root enabler in both: **the spawn lives in `_Init` (or runs unconditionally at construction), not in an explicit `_Start`** — so "initialize" and "a thread is now live" are conflated, and any re-`_Init` / `_Reset` re-enters with a live thread.

## Detection heuristic

Flag any `*_Init` / `*_Reset` body that:
- zeroes a `*_thread_active` / `*_should_stop` atomic, OR
- calls `SPSCRing_Init` / `fclose` / `fopen` / a buffer re-init on a struct field,

with **no preceding `*_Stop*` / `pthread_join` / `assert(active==0)` in the same body** — AND the struct has a thread-spawn (`pthread_create`) reachable from its `_Init` / `_Start`.

(No clean mechanical signature for "is a re-entry reachable in production" — that needs the caller-graph; the heuristic flags the *shape*, a `/trace-deps` pass confirms reachability.)

## Instances (recurrence_count = 2 confirmed + 3 latent)

- **CONFIRMED — `OrderEventLog_Init`** (`CoreFrameworks/OrderEventLog.hpp:204-241`): re-runs `SPSCRing_Init` + `writer_thread_active.store(0)` (`:231-232`) with no `StopAsyncWriter` first. The writer is started UNCONDITIONALLY at construction (`MemHeaders/OmsFieldRegistry.hpp:758`, Layer-5, no mode/live gate). The test double-init (`controller_test.cpp:26457`) defeats `_Free`'s join (`:399` guard) → ASan UAF at `SPSCRing_TryPop:180`. **TEST-ONLY today** (TD-202; prod Init always precedes Start).
- **CONFIRMED — `OrderEventLog_Reset`** (`:492-521`, called from paper-reset `Async.hpp:737`): `fclose`/`fopen`×2 on `disk_file` + `count=0` while the **live writer** `fwrite`s/`fflush`es the same `FILE*` (`:303`/`:372`) and the **drainer** `Append`s — a **3-way race**; `oms_event_log_mode=1` is the default → **PRODUCTION-reachable, on-by-default.** Paper-reset parks only slow paths (`paper_reset_in_progress`), never the writer/drainer.
- **LATENT (sharpest) — `BinanceAdapter_Init`** (`DataStream/BinanceAdapter.hpp`): spawns worker threads *inside* `_Init` → a future reconnect / per-symbol / WS-resubscribe re-`_Init` lights up the exact UAF. Safe today only because boot calls it once.
- **LATENT — `NotifyState_Init` / `BinanceUserData_Init` / `ReconciliationLoop_Init`**: spawn-in-Init; their `_Shutdown` stops-first but `_Init` doesn't — safe by call-graph accident (no re-entry), not by construction.

## Structural fix

- **Spawn belongs in an explicit `_Start`, never in `_Init`** — `_Init` only initializes data; `_Start` spawns; the two are separable lifecycle steps.
- **`_Init` / `_Reset` MUST quiesce first** — stop+join the thread, OR `assert(active==0)`, OR (best) **single-own the resource**: the owning thread owns its `FILE*` / ring / counter; other threads SIGNAL via a polled atomic (`reopen_requested`, `should_stop`) and NEVER touch the resource cross-thread (the SPSC discipline the resource already claims for its data buffer).
- **Do NOT quiesce via a cross-thread `pthread_join` on a latency-budgeted thread** (the gate refuted this for the OMS Reset: a drainer-thread join blocks ~1ms = ~100× the ≤10μs budget, H8). Signal-and-poll, not join, on hot/drainer/producer paths.

## Distinct from / sibling of

- **Class 07** (audited-clean topology) and **Class 13** (snap-capture-drift) do NOT cover this re-init-defeats-join lifecycle shape — genuinely new.
- Thread-lifecycle / concurrency family (NOT the SSoT-violation family of Classes 43/45/47/49). Sibling concern to the cross-thread-coherence torn-read class.

## Closure mechanism

- A CI detector implementing the heuristic above (candidate; recurrence-gated).
- The **lifecycle-idempotency discipline** + **single-owner-resource** rule, owned by the `.E.1` SPSC/event-log rework (`subplans/2026-05-28-...E.1-foundation.md` OrderEvent section).
- The **V-class** (`feedback_v_class_post_implementation_verification`) surfaces instances per-implementation (asan/ubsan), which is how the canonical instance was caught.

## False-positive surface (per M3)

- **Single-init-per-object structs are SAFE** — a struct spawned once and joined once with NO re-init/reset path is correct; the detector must not flag plain `_Init`/`_Free` pairs that have no re-entry. (E.g. EngineSharded producer/drainer/executor/slow-path threads: spawn-once→join-once, no re-init.)
- **Resource-only structs (no owned thread) are SAFE** — `DepthRecorder` / `TickRecorder` own a `FILE*` but no thread; their Reset touching the file is single-threaded. The flag fires ONLY on thread-owning structs with a re-init/reset path.
- **`_Reset` that touches only thread-private value fields is SAFE** — the hazard is shared/thread-touched state; a reset of fields the thread never reads is fine.
