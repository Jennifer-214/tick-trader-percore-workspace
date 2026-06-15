---
audit: /hft-audit (Layer-2 INVESTIGATIVE under /precoding-audit-gate)
lens: I-2 — thread-lifecycle / ordering / the writer-start question
target: TECH_DEBT-202 — OMS async-writer UAF (OrderEventLog)
engine_head: 3ee95dc
date: 2026-06-15
verdict_summary: >
  Writer-start is UNCONDITIONAL (OmsFieldRegistry.hpp:758 Layer 5; not gated on
  event_log_mode or live_trading). Paper/test SHOULD NOT spin a disk-writer pthread.
  Memory ordering of the Start/Stop/routine protocol is CLEAN in isolation; the UAF is
  a SEPARATE re-init data race (the test double-init clobbers writer_thread_active under
  a live thread). Shutdown mechanism is H3-compliant (atomic flag + pthread_join, no
  mutex/condvar); usleep is OFF the hot path (H8-safe).
scope: read-only; no code modified; no subagents spawned
---

# I-2 — Thread-lifecycle / Ordering / The Writer-Start Question (TECH_DEBT-202)

Re-derived from source per `feedback_capture_and_check_are_model_bounded` (the TD-202 root cause
was captured WRONG once — "the writer is never joined" — so I armed with the code, not the claim).

---

## Q1 — When EXACTLY does the writer thread start? + verdict on paper/test

### The exact condition: UNCONDITIONAL

The writer thread is started in **`MemHeaders/OmsFieldRegistry.hpp:758`**, the LAST line of
`OMS_INIT_AUTOPOPULATE` (Layer 5):

```
/* Layer 5 — MUST RUN LAST: depends on event_log being _Init-only or _InitWithFile'd */  \
OrderEventLog_StartAsyncWriter(&(_oms_target)->event_log);                                \
```

There is **NO `if` guard** around it. It is NOT gated on `event_log_mode`, NOT on `live_trading`.

The only conditional in the event-log path is **Layer 4** (`OmsFieldRegistry.hpp:730-756`), and
it only chooses HOW the log is initialized — disk vs in-memory:

- `event_log_mode == 1 && _has_disk_path` → `OrderEventLog_InitWithFile` (`:752`, disk persistence + replay)
- else → `OrderEventLog_Init` (`:754`, in-memory only)

Either branch is followed by the UNCONDITIONAL `StartAsyncWriter` at `:758`. So the TD-202 claim
is **CONFIRMED**: the test at `controller_test.cpp:26456`
(`OrderManager_Init(oms, adapter, /*live*/0, /*partials*/0, MQ(10000.0))` — `event_log_mode`
defaults to `0` per the `OrderManager_Init` signature `OrderManager.hpp:866`) **DOES** spin up the
writer pthread. `StartAsyncWriter` (`OrderEventLog.hpp:383-395`) only no-ops if the writer is
*already* active (`:384`); from a fresh `Init` it always `pthread_create`s.

Sole caller of the macro: `OrderManager_Init` (`OrderManager.hpp:868`). I grep-confirmed
`StartAsyncWriter` has exactly one functional call site (`OmsFieldRegistry.hpp:758`; the
`OrderEventLog.hpp` hits are the definition + lifecycle comments).

### Verdict: paper/test should NOT start a disk-writer pthread — DESIGN FORK = YES, fix it

This is the right architectural question and the answer is clear on H8/H3 + scale-invariance
grounds:

1. **A paper/test OMS has no disk_file** (mode 0 → `disk_path[0]=='\0'`, `disk_file==nullptr`).
   The writer routine's body (`OrderEventLog.hpp:349-380`) then does: pop ring → `ApplyEvent`
   (in-memory `entries[]` write only; the `if (log->disk_file)` fwrite at `:302` is skipped) →
   `usleep(1000)`. So in paper/test the thread exists ONLY to move events ring→array on a 1ms
   poll — work the sync path (`OrderEventLog.hpp:341-342`) already does inline at ~zero cost with
   ZERO thread. The thread is **pure overhead + a lifecycle liability** with no disk-stall to
   isolate (the entire v5.11.3.C rationale at `OrderEventLog.hpp:170-188` is "isolate fwrite
   disk-stall from the drainer" — irrelevant when there is no file).

2. **It manufactures a cross-thread hazard surface for free.** Every paper/test OMS now has a
   live consumer pthread racing `entries[]`/`writer_thread_active`/the ring against the test
   thread. That is precisely the surface TD-202 detonates on. No writer ⇒ no UAF here at all.

3. **Recommended fork (structural, closes the class):** gate Layer 5 so the writer starts ONLY
   when there's an actual disk sink to isolate — i.e. when `event_log_mode == 1 && _has_disk_path`
   (the same predicate Layer 4 already computes into `_has_disk_path`). In-memory mode keeps the
   sync Append path (already the documented `writer_thread_active==0` fallback, `OrderEventLog.hpp:341`).
   This is strictly better than the minimal "harden Init" fix because it removes the thread that
   has no reason to exist, rather than making its teardown more robust. (Note Q2: even WITH the
   gate, the re-init idempotency hole in Q2 should still be closed — they are independent.)

---

## Q2 — Memory-ordering / happens-before assessment

### The Start/Stop/routine atomic protocol in ISOLATION: CLEAN

The protocol is a correct atomic flag + join handshake (no mutex/condvar):

- **Start** (`OrderEventLog.hpp:382-395`): `writer_should_stop.store(0, relaxed)` (`:385`) →
  `pthread_create` (`:386`) → `writer_thread_active.store(1, release)` (`:393`). The `release`
  publishes; `pthread_create` itself is a full happens-before edge so the new thread sees the
  ring + `should_stop=0`.
- **Append-side gate** (`:324`): `writer_thread_active.load(acquire)` pairs with the Start
  `release` — correct acquire/release. The drainer is the sole producer; the writer is the sole
  consumer (SPSC discipline documented `OrderEventLog.hpp:179-180`).
- **Stop** (`:397-403`): `writer_should_stop.store(1, release)` (`:400`) → `pthread_join` (`:401`)
  → `writer_thread_active.store(0, release)` (`:402`). The routine reads `should_stop` with
  `acquire` (`:365`); the join is the happens-before that lets the post-join code touch
  `entries[]`/`disk_file` safely. The drain-before-stop ordering (`:362-374`) is correct — it
  flushes everything pushed before the signal, with a final drain pass for the shutdown race.

In a clean `Init → Start → … → Stop/Free` lifecycle there is no race here.

### The UAF is a SEPARATE race: re-init under a live writer (independent of any UAF "ordering bug" in Start/Stop)

`OrderEventLog_Init` (`:204-241`) **unconditionally** re-runs `SPSCRing_Init(&log->async_ring)`
(`:231`) and `writer_thread_active.store(0, relaxed)` (`:232`) with **NO StopAsyncWriter first**.
When called on a log whose writer is *already running*, this is a textbook data race:

- `SPSCRing_Init` (`SPSCRing.hpp:95-100`) does `head/tail.store(0, relaxed)` + resets cached
  counters — concurrently with the live writer's `SPSCRing_TryPop` reading `tail`/writing `tail`
  (`SPSCRing.hpp:180,193`) and `head` (`:184`). Racy resets of the ring indices.
- `writer_thread_active.store(0, relaxed)` flips the active flag to 0 **while T101 runs**. The
  subsequent `OrderEventLog_StopAsyncWriter` guard (`:399`,
  `if (!writer_thread_active.load(acquire)) return;`) then sees 0 and **no-ops the join** — the
  join that exists and is otherwise correct is DEFEATED. `delete oms` (`controller_test.cpp:26491`)
  then frees the embedded `event_log` (and its ring) out from under the still-running T101 →
  `SPSCRing_TryPop` reads freed memory → ASan heap-use-after-free at `SPSCRing.hpp:180`.

This exactly matches the test: `:26456` starts the writer (paper), `:26457`
`OrderEventLog_Init(&oms->event_log)` clobbers `writer_thread_active` while T101 runs, `:26490`
`OrderEventLog_Free` → `StopAsyncWriter` no-ops, `:26491` `delete oms` frees the ring under T101.

**Conclusion for Q2:** the Start/Stop/routine ordering is clean; the bug is a missing-quiesce on
the `Init` re-entry path — a data race that is INDEPENDENT of (and the proximate cause of) the
UAF. Re-initing the ring + flag under a live writer is itself UB regardless of the later free.

**Production-path check (I verified, not assumed):** the only `OrderEventLog_Init` site that can
run on a log with a live writer is the test `:26457`. The two production `OrderEventLog_Init`
calls (`OmsFieldRegistry.hpp:734,754`) are inside `OMS_INIT_AUTOPOPULATE` Layer 4, which runs
BEFORE Layer 5 starts the writer (no live writer yet). `OrderEventLog_InitWithFile`'s internal
`if (!log->entries) OrderEventLog_Init` (`:420`) only fires on a never-allocated log. The other
test sites (`:17320,:17408`) init standalone stack logs that never called Start. So TD-202 is
**test-triggered against a real misuse-unsafe primitive**, with no live-production re-init path
today — but the `Init` hole is a latent class (any future re-init-of-running-log detonates it).
The misuse-safe fix (StopAsyncWriter-first in `Init`, OR — better — `Init` should `assert`/refuse
on a live writer) closes the class structurally.

---

## Q3 — H3 / H8 compliance of the shutdown mechanism

### H3 (lock-free): COMPLIANT

- Shutdown = `writer_should_stop` atomic (release/acquire) + `pthread_join` (`:400-401`). **No
  `std::mutex`, no `condition_variable`, no `pthread_rwlock`** anywhere in the lifecycle. This is
  exactly the H3-sanctioned pattern (atomic flag + join), matching
  `STRATEGY_AND_CODING_RULES.md` §3.
- **`usleep` (`OrderEventLog.hpp:335` Append spin-backoff, `:378` writer idle):** H3 forbids
  `std::this_thread::sleep_for` on **active polling threads** (§3: "Never artificially sleep on an
  active polling thread (e.g. OMS worker loops)"). Assessment:
  - **`:378` (writer idle, `usleep(1000)`):** acceptable. The writer is an OFF-trading-path async
    thread (Q3/H8 below), NOT a hot/slow/drainer poller. Sleeping 1ms when the ring is empty
    avoids burning a core on an idle disk-writer. The comment (`:375-377`) correctly notes even
    100ms would be functionally fine; 1ms is chosen only to bound shutdown latency. `usleep` is a
    libc call, not `std::this_thread::sleep_for`, but the spirit is "don't sleep on a *trading*
    poller" — this is not one. **No H3 concern on this thread.** (Minor: per §3 the canonical idle
    primitive is `_mm_pause()` spin for short waits; a 1ms disk-writer idle is a legitimate sleep,
    not a spin candidate — flagging only as a note, not a finding.)
  - **`:335` (Append ring-full backoff, `usleep(100)` after 64 `__builtin_ia32_pause`):** this runs
    on the **DRAINER** thread (the sole Append caller). The drainer IS a trading-path poller
    (drainer cycle budget ≤10μs, CoreFrameworks/CLAUDE.md). A `usleep(100)` here is a 100μs stall
    that blows the drainer budget by 10x. **This is a real H3/H8 smell on the drainer** — but it
    fires ONLY when the async ring (256 slots) is genuinely full, which the header argues is
    unreachable at default-strategy event rates (`OrderEventLog.hpp:149-153`). Disposition:
    LOW/MOOT-bounded-by-ring-headroom for current rates, but it is a latent drainer-stall under a
    burst the ring can't absorb. **NB: if Q1's fork lands (no writer in paper/test), this path is
    `writer_thread_active==0` in paper/test and never taken there; in live with a real disk writer
    it remains the one place the drainer can block on the writer.** Worth a tracked note for the
    `.E` SPSC rework (drainer should drop-or-count on async-ring-full, never `usleep`, per the
    tick-ring drop policy precedent `SPSCRing.hpp:50-54`).

### H8 (writer off the hot path → join-at-shutdown is latency-safe): COMPLIANT

- The writer thread is an **async/off-trading-path** thread. It is the consumer of
  `async_ring`; the drainer (producer) only `TryPush`es (`OrderEventLog.hpp:330`, no I/O, ~5ns
  per the design note). The writer does the realloc-free `ApplyEvent` + fwrite. It is NOT on the
  hot path (BG/SG_Evaluate) and NOT on the slow path — it sits below the drainer, in the "Async"
  thread tier (CoreFrameworks/CLAUDE.md concurrency model: "Async: … Notify worker, GUI").
- Therefore `pthread_join` at `Free`/`Stop` is a **shutdown-time** operation, never on a
  latency-bearing tick. Joining a disk-writer at teardown is latency-safe by construction (H8
  governs per-tick p99, not shutdown). The boot warm-restart budget (≤5s) is the only relevant
  envelope and a 1ms-max writer drain is trivially inside it.

---

## Severity + recommended dispositions (for operator triage)

| # | Finding | Severity | Disposition |
|---|---|---|---|
| I2-1 | `StartAsyncWriter` UNCONDITIONAL at `OmsFieldRegistry.hpp:758` — paper/test spin a useless disk-writer pthread (no `disk_file` to isolate); manufactures the TD-202 hazard surface for free | HIGH (root design fork) | **Gate Layer 5 on `event_log_mode==1 && _has_disk_path`** (reuse Layer-4's `_has_disk_path`). Removes the thread that has no reason to exist. Closes TD-202 at the source for paper/test. |
| I2-2 | `OrderEventLog_Init` re-inits ring + `writer_thread_active` with NO StopAsyncWriter first → data race + defeats the existing join (the proximate TD-202 mechanism) | HIGH (UAF / memory-safety; asan-gate blocker) | **Make `Init` misuse-safe: StopAsyncWriter-first when a writer is live** (one guard; closes the re-init-on-running-log class). Independent of I2-1; do BOTH. |
| I2-3 | Drainer `usleep(100)` on async-ring-full (`OrderEventLog.hpp:335`) — 100μs drainer stall (H8 ≤10μs) under a burst the 256-slot ring can't absorb | LOW / MOOT-bounded-at-current-rates | Track for `.E` SPSC rework: drainer should drop-or-count on async-ring-full (tick-ring drop-policy precedent), never `usleep`. Not a `.E.0.10` blocker. |

The Start/Stop/AsyncWriterRoutine atomic protocol itself is **correct** — do not rewrite it; the
fix surface is (a) WHEN the writer starts (I2-1) and (b) the `Init` re-entry quiesce (I2-2).

**End of I-2 report.**
