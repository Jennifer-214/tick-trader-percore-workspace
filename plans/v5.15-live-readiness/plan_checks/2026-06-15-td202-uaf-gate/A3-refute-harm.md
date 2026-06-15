---
type: audit-report
audit: A-3 — ADVERSARIAL refute-harm (Layer-2 under /precoding-audit-gate, Stage 3.5)
framing: DEFAULT-REFUTED (assume the fixes introduce harm; try to prove it)
target: TECH_DEBT-202 — OMS async-writer UAF; the three proposed fixes
fixes_under_test:
  - FIX-1 gate Layer-5 StartAsyncWriter on (event_log_mode==1 && _has_disk_path)
  - FIX-2 OrderEventLog_Init StopAsyncWriter-first when a writer is active
  - FIX-3 OrderEventLog_Reset quiesces the writer before touching disk_file
engine_head: 3ee95dc
date: 2026-06-15
scope: read-only; no code modified; no subagents spawned; no Layer 3
verdict_summary: >
  FIX-1 NO-HARM (behavior-preserving for backtest/test; determinism intact — confirmed nothing
  reads event_log.entries mid-run). FIX-2 NO-HARM (boot-once production; Init never on a latency
  path; double-join safe). FIX-3 *** HARM FOUND *** IF implemented as stop+JOIN: a pthread_join of
  the writer on the DRAINER thread (Async.hpp:737) blocks the drainer up to ~1ms (writer idle
  usleep(1000)), a 100x..>100x blow of the ≤10μs drainer-cycle budget (CoreFrameworks/CLAUDE.md).
  The "or signal" variant is the only harmless FIX-3. H3: none of the fixes add mutex/condvar/
  sleep_for. The pre-existing usleep(100) on the drainer (OrderEventLog.hpp:335) is a real latent
  H8 smell the fixes must NOT extend.
---

# A-3 — Adversarial refute-harm (TECH_DEBT-202 fixes)

Default-skeptical. Every file:line grepped/read at HEAD 3ee95dc, not inherited from the I-reports.
I read the I1/I2/I3 investigative reports AFTER forming the attack and use them only as the
agreed baseline (UAF trigger is test-only today; Reset is a 2nd live-instance write-to-closed-FILE
race). My job is the fixes, not the bug.

---

## FIX-1 — gate Layer-5 StartAsyncWriter on `(event_log_mode==1 && _has_disk_path)`

### VERDICT: **NO HARM** (couldn't break it). One behavior-change surface, confirmed benign.

The attack that mattered: FIX-1 does NOT only suppress the writer in paper/test — it ALSO suppresses
it for two production-shaped callers that pass `mode=1` with an **empty/null path**:

- **Backtest** — `Backtest/BacktestSharded.hpp:187-190`: `OrderManager_Init(..., /*mode=*/1, /*path=*/"")`.
  `_has_disk_path = (_evt_path && _evt_path[0])` (OmsFieldRegistry.hpp:732) is FALSE for `""` → under
  FIX-1 the writer **no longer starts** in backtest. Today it DOES start (Layer-5 unconditional, :758).
- **Tests** at controller_test.cpp:17004 / 17085 / 17161 / 28069 — `mode=1` + path `nullptr`. Same.

So FIX-1 IS a behavior change for backtest + in-memory-mode-1 tests, NOT a no-op. This is the load-bearing
attack, because **backtest reaches train-serve accounting parity BY CONSTRUCTION** by running the same OMS
in mode-1 (Backtest/CLAUDE.md surface rule; BacktestSharded.hpp:162-178), and the dir carries a GOLDEN-REGEN
discipline. If sync-vs-async Append produced a different in-memory event array, backtest P&L/golden could drift.

**Why it survives the attack (refutation fails):**

1. **Backtest is single-threaded and never reads `event_log.entries[]`/`.count` mid-run.** Grepped
   `Backtest/` + `ShardedBacktestDriver.hpp` for `event_log.count|entries` → ZERO reads. Backtest stats
   derive from the **synchronously-mutated** `portfolio`/`balance`/`realized_pnl` (HandleFill →
   FillRecord → `EventLoop_DrainPostFill`, ShardedBacktestDriver.hpp:239/421 on the SAME tick), not from
   the async event array. The event log in backtest is a write-only sink. Sync vs async only changes WHEN
   the event lands in `entries[]`; the FINAL array contents are identical (same events, same Append order
   — `next_event_id.fetch_add` is monotonic and the drainer is the sole producer in both modes).
   `ORDER_EVENT_LOG_FORMAT_VERSION`/header/magic unchanged → no wire/replay byte change → **H9 intact**.
2. **`disk_file==nullptr` in every suppressed case** (mode-0, or mode-1 empty-path). `ApplyEvent`'s
   disk branch (`if (log->disk_file)`, OrderEventLog.hpp:302) is skipped identically on sync and async
   paths. So there is no "disk drops accounting" delta: there is no disk file. The `log_full_drops` /
   `ring_full_spins` / `writer_realloc_failed_count` counters — read by the GUI via ShardedSnapshot.hpp:110-119
   — are *advisory observability* (comment :106-109 "not transactional state"). With no writer: `ring_full_spins`
   stays 0 (sync Append never touches the ring, :341-342), `writer_realloc_failed_count` stays 0 (only the
   writer routine bumps it, :357), `log_full_drops` still fires correctly from `ApplyEvent` (:295) on the
   sync path. No counter goes wrong; one (ring_full_spins) simply becomes structurally-0, which is *more*
   honest (there's no ring to saturate).
3. **No production OR test path depends on the writer THREAD existing in mode-0/empty-path.** The only
   tests that assert `writer_thread_active`/Start/Stop (controller_test.cpp:17338-17415) build **standalone
   stack `OrderEventLog`s** and call `OrderEventLog_StartAsyncWriter` *explicitly* — they do NOT go through
   `OrderManager_Init`/Layer-5, so FIX-1 (which only gates the Layer-5 call) leaves them untouched.
4. **Warm-restart / `Portfolio_FromEventLog` / LoadFromDisk** only run in the `mode==1 && _has_disk_path`
   branch (OmsFieldRegistry.hpp:733-752) — exactly the branch where FIX-1 KEEPS the writer. The replay
   consumer reads `entries[]` populated by `LoadFromDisk` (synchronous, pre-Start) — unaffected.

**Residual (not harm, disclosure):** FIX-1 means live-with-disk is now the ONLY config that spins the
writer. That is the *intended* narrowing and matches the v5.11.3.C rationale ("isolate fwrite disk-stall",
OrderEventLog.hpp:170-188) — the writer only earns its keep when there's a `disk_file` to stall on. I
could not manufacture a regression. **NO HARM.**

---

## FIX-2 — `OrderEventLog_Init` calls `StopAsyncWriter`-first when a writer is active

### VERDICT: **NO HARM** (couldn't break it).

Attacks tried:

1. **"FIX-2 puts a `pthread_join` inside `OrderEventLog_Init` → H8 latency hit."** REFUTED. `OrderEventLog_Init`
   is reachable on a live writer from EXACTLY the test site (controller_test.cpp:26457; confirmed by I1/I2
   independently and by my own caller grep — the two production Inits at OmsFieldRegistry.hpp:734/754 run in
   Layer-4 BEFORE Layer-5 starts the writer, and `InitWithFile`'s internal Init is `if(!entries)`-guarded at
   :420). Init is a **boot-once** operation (Run.hpp:674, BacktestSharded.hpp:187) — never per-tick, never on
   the drainer/hot/slow path. The `StopAsyncWriter`-first only does work when `writer_thread_active==1`, which
   in production is NEVER at an Init call. So the join is (a) a no-op in all production Init calls (guard at
   OrderEventLog.hpp:399 short-circuits), and (b) at the one test trigger it's a shutdown-shaped join, not a
   latency path. **H8 not engaged.**
2. **"Double-join / stale-handle reuse."** REFUTED. `StopAsyncWriter` (:398-403) is idempotent-by-guard:
   `if(!writer_thread_active.load(acquire)) return;` then `pthread_join` then `store(0)`. FIX-2 calling it at
   the top of Init means: if active→join+clear (handle valid, set by the prior `pthread_create` at :386);
   if inactive→return. A subsequent `OrderEventLog_Free`→`StopAsyncWriter` then sees `active==0`→no-ops. No
   pthread_t is joined twice (the flag gates it), and `pthread_create` always overwrites `writer_thread`
   before the next Start sets `active=1` — no stale-handle join.
3. **"Lost events on the Init stop."** N/A for the production trigger (Init-on-live-writer doesn't happen in
   prod). For the test trigger, FIX-2 makes it SAFER: `StopAsyncWriter` triggers the routine's drain-before-stop
   (:362-374) so any ring contents flush before the re-Init wipes the ring. Strictly better than today's
   clobber.
4. **H3.** `StopAsyncWriter` = atomic flag (release) + `pthread_join`. No mutex/condvar/sleep_for added. Compliant.

**NO HARM.** (FIX-2 is the structural close of the re-init class; I1-H-B and I3 agree, and I can't break it.)

---

## FIX-3 — `OrderEventLog_Reset` quiesces (stop+restart, OR signal) the writer before touching `disk_file`

### VERDICT: *** HARM FOUND *** — the **stop+restart (join)** variant blows the drainer-cycle budget. The **signal-only** variant is harmless.

This is the fix where the prompt's own phrasing ("stop+restart, **or signal**") hides a fork, and one fork
is genuinely harmful. The harm is concrete and quantified.

**The call site is the DRAINER thread.** `OrderEventLog_Reset` is invoked at
`CoreFrameworks/EngineSharded/Async.hpp:737`, inside `EngineSharded_Async_HandleControlAndReset`, which runs
ON the drainer thread (the same function body that calls `OMS_RESET_AUTOPOPULATE` at :703 and is reached from
the drainer loop — paper-reset is handled drainer-side, Run.hpp:1456-1528 drainer body + the control/reset
handler). The drainer-cycle budget is **≤10μs p99** (CoreFrameworks/CLAUDE.md "Drainer cycle ... p99 ≤10μs").

**Quantified blocking of the stop+join variant:**

- A `pthread_join` of the writer waits for the routine to observe `writer_should_stop` (read with `acquire`
  at OrderEventLog.hpp:365) and return. The routine only re-checks the stop flag at the TOP of its loop,
  AFTER draining; when the ring is empty it sleeps **`usleep(1000)`** (OrderEventLog.hpp:378) before looping
  back to the stop check. So worst-case latency from `should_stop=1` to thread exit ≈ **one full `usleep(1000)`
  = ~1ms** (plus scheduler wake jitter). That is a **~1,000,000 ns** stall vs a **10,000 ns** budget — a
  **~100x** blow at minimum, worse under scheduler contention. Even the *best* case (writer happens to be at
  the top of its loop) is a cross-thread join scheduling round-trip — well over 10μs.
- During that join, the drainer is BLOCKED inside the reset handler. Consequences:
  - **Producer back-pressure / tick drops:** the producer fans ticks into per-core tick rings (drop policy,
    SPSCRing.hpp:50-51). The producer itself does not block on the drainer, BUT a stalled drainer stops
    consuming `submit_queues`/`result_queue`; on a ~1ms stall the rings can fill and ExecutionCore's
    `SPSCRing_TryPush` of TradeEvents starts failing → `core->ring_push_failures++` (ExecutionCore.hpp:589-591)
    and the documented zombie-position-avoidance path (:487-501). A 1ms drainer stall is exactly the
    "drainer briefly stalled" condition the hot path is hardened against — FIX-3-join would make it a
    *guaranteed* 1ms stall every paper-reset, not a rare micro-stall.
  - This is a **self-inflicted H8 regression on a code path that is currently fast.** Today `OrderEventLog_Reset`
    (OrderEventLog.hpp:492-521) does only `count=0` + `next_event_id` + `fclose`/`fopen` — microseconds, no
    join. Adding a stop+join makes the drainer's reset cycle ~1ms. That is harm the fix introduces that did
    not exist before.

**The restart half adds a SECOND drainer cost:** `StartAsyncWriter`→`pthread_create` (OrderEventLog.hpp:386)
on the drainer thread. `pthread_create` is not free (page-table/stack setup, ~10-50μs typical) — another
budget blow, plus it spawns a thread from the drainer, which is an unusual ownership move (every other writer
spawn is boot-time off the drainer).

**Why "signal-only" is the harmless variant (and why it's also INSUFFICIENT alone):** if FIX-3 instead sets
`writer_should_stop` is the WRONG primitive (that's terminal). The genuinely-correct cheap quiesce is a
*pause/resume* handshake — e.g. a new `writer_paused` atomic the Reset sets, the routine observes at the top
of its loop and spins/parks until cleared, and Reset waits for a `writer_acked_pause` atomic before touching
`disk_file`. But note: **even a signal/pause still makes the drainer SPIN-WAIT for the writer's ack**, and
the writer may be mid-`usleep(1000)` → the drainer spins up to ~1ms anyway unless the idle sleep is shortened
or the writer is woken. So the naive "signal" is *also* a potential ~1ms drainer spin. The ONLY fully
budget-safe FIX-3 is one that does NOT make the drainer wait on the writer's 1ms-granularity loop at all —
which points back to the I2-3 / `.E`-SPSC observation that the writer's idle cadence + the drainer's coupling
to it is the real defect.

**Sharper alternative (refutes "stop+restart is the fix"):** the prompt's FIX-1 already removes the writer in
every config that lacks a `disk_file`. `OrderEventLog_Reset`'s dangerous window (the `fclose`/`fopen` at
:501-518) ONLY exists when `disk_file != nullptr` — i.e. live-with-disk. In backtest/paper (no disk_file)
Reset early-returns at :497 (`if (!log->disk_file ...) return;`) and there's no race at all. So the Reset
race is a **live-with-disk-only** concern, and on that path the drainer stalling ~1ms during an operator-
initiated paper-reset of a LIVE session is… still a real stall, but paper-reset on a live-capital session is
itself gated (`!ControllerConfig_IsLiveCapital(cfg)`, Async.hpp:565 / Run.hpp). **Verify the interaction:**
if paper-reset cannot fire while live-capital is engaged, then in the only config where the writer exists
(live-with-disk), is paper-reset even reachable? If NOT, FIX-3 may be fixing a window that FIX-1 + the
live-capital interlock together render **unreachable** (MOOT-UNREACHABLE candidate) — in which case adding a
drainer-stalling join is pure downside. This needs an operator code-read of the live-capital × event-log-mode
× paper-reset matrix before any join lands. (I flag it; I do not resolve it by fiat — AR-11.)

### H3 on FIX-3: compliant either way (no mutex/condvar/sleep_for added); the harm is **H8**, not H3.

---

## Cross-cutting H3 / H8 assessment (prompt Q1/Q2)

- **H3 (no mutex/condvar/sleep_for):** NONE of the three fixes introduce a `std::mutex`,
  `condition_variable`, `pthread_rwlock`, or `std::this_thread::sleep_for`. FIX-2/FIX-3 reuse the existing
  atomic-flag + `pthread_join` shutdown (OrderEventLog.hpp:398-403), which is the H3-sanctioned pattern
  (STRATEGY_AND_CODING_RULES.md §3). **All three H3-COMPLIANT.**
- **Pre-existing `usleep(100)` on the drainer (OrderEventLog.hpp:335):** CONFIRMED runs on the drainer
  (Append's sole caller is the drainer — OMS single-writer funnel, OrderEventLog.hpp:179). It fires only on
  async-ring-full (256-slot ring; argued unreachable at default rates, :149-153). It is a latent **H8** smell
  (100μs vs ≤10μs) the I2 report already tracked (I2-3) for the `.E` SPSC rework. **The fixes must NOT worsen
  it** — FIX-1 actually *removes* this path in paper/test (no writer ⇒ `writer_thread_active==0` ⇒ Append
  takes the sync branch :341, never the ring-spin), so FIX-1 is net-positive here. FIX-3-with-join is the one
  that adds NEW drainer blocking (the join), which is the same category of harm as the usleep(100) but
  unconditional-per-reset rather than burst-only.

---

## Per-fix harm verdict (summary)

| Fix | Verdict | Concrete harm (file:line) | Quantified blocking |
|---|---|---|---|
| FIX-1 (gate Layer-5) | **NO HARM** | — (behavior change for backtest/mode-1-empty-path is determinism-safe: nothing reads event_log.entries mid-run; disk_file==nullptr so no disk-drop delta; H9 wire unchanged) | n/a |
| FIX-2 (Init stop-first) | **NO HARM** | — (Init is boot-once; join is no-op in all prod Inits; double-join guarded; no stale handle) | 0 in prod (guard short-circuits); shutdown-shaped at the single test trigger |
| FIX-3 **stop+JOIN** variant | **HARM FOUND** | `OrderEventLog_Reset` join on DRAINER thread @ Async.hpp:737 ; writer idle `usleep(1000)` @ OrderEventLog.hpp:378 ; restart `pthread_create` @ :386 | drainer stall **~1ms (1,000,000ns)** vs ≤10μs budget = ~100x blow; `pthread_create` adds ~10-50μs |
| FIX-3 **signal-only** variant | NO HARM **only if** it does not make the drainer wait on the writer's 1ms loop; naive signal still risks a ~1ms drainer spin | (potential) drainer spin up to one `usleep(1000)` waiting for the writer's pause-ack | up to ~1ms unless the writer idle cadence is shortened/woken |

## Correctness / determinism regressions found

- **FIX-1:** none. Confirmed (a) backtest/single-thread never reads the async-written `entries[]` mid-run
  (zero grep hits in `Backtest/` + `ShardedBacktestDriver.hpp`); (b) final event-array contents are
  Append-order-identical sync vs async; (c) header/magic/`ORDER_EVENT_LOG_FORMAT_VERSION` unchanged → no
  wire/replay/HMAC byte change (H9); (d) observability counters stay correct (`ring_full_spins` becomes a
  structurally-honest 0; `log_full_drops` still fires from `ApplyEvent`).
- **FIX-2:** none.
- **FIX-3:** no *data* corruption from the fix itself (it's a latency regression, not a correctness one) —
  BUT the **stop+restart variant introduces a NEW latency-determinism (jitter) regression on the drainer**,
  which for a determinism-prioritizing HFT system (variance is the cost, per H20/DESIGN_PHILOSOPHY §4) is a
  real harm even though no byte diverges.

## Bottom line for the operator

FIX-1 and FIX-2 are safe to land as specified. **FIX-3 must NOT be implemented as stop+restart(join) on
the drainer thread** — that is a quantified ~100x drainer-budget violation (~1ms vs ≤10μs) every paper-reset.
Before landing ANY FIX-3, get an operator code-read on the **live-capital × event_log_mode × paper-reset**
reachability matrix (Async.hpp:565 `!IsLiveCapital` interlock vs the writer-only-exists-with-disk_file
condition that FIX-1 establishes): the Reset disk-race window may be **unreachable** post-FIX-1, making FIX-3
a MOOT-UNREACHABLE candidate (pin the guarantee, don't add a drainer-stalling join). If FIX-3 is genuinely
needed, it must be a pause/resume handshake that does NOT block the drainer on the writer's 1ms idle loop
(shorten the writer idle cadence or wake it), not a `pthread_join`.
