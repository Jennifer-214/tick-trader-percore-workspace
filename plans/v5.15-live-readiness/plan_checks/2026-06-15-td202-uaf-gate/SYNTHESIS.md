---
type: audit-synthesis
ship_tag: .E.0.10
surface: TECH_DEBT-202 — OMS OrderEventLog async-writer UAF + the event-log thread lifecycle
gate: /precoding-audit-gate (HIGH-RISK, guard-matrix HOLE → HEAVY pass)
audit_set: 3-I (trace-deps / hft-audit / class-scan) → 3-A (refute-fix / refute-scope / refute-harm) + standing completeness-critic
date: 2026-06-15
verdict: YELLOW — the inherited "few-line, test-only Init harden" framing is INCOMPLETE + partly WRONG; amend before coding
agents: I1 a485a7af7 · I2 a62142e3c · I3 a15211e6b · A1 a84ccc1dc · A2 a04994f8b · A3 a69af9539 · CC a307284b4
---

# `.E.0.10` pre-coding gate — TECH_DEBT-202 OMS async-writer UAF

## Combined verdict: YELLOW (amend the fix scope before coding)

The literal asan-blocker (the ring-free UAF) IS test-only and has a clean cheap fix. But the gate surfaced a **bigger, production-reachable, on-by-default sibling UAF** + a **warm-restart recovery-corruption hole** that the inherited TD-202 framing missed entirely, and **refuted all three naively-stated fixes** (one as written, one as class-closure, one as harmful). The surface is now fully understood; no engine redesign is needed — but the plan must be reshaped, and one design fork needs a `/decision-check` (with a code-read, not a fiat call).

## Per-audit verdict table

| Agent | Lens | Verdict | Headline |
|---|---|---|---|
| I-1 | trace-deps / blast-radius | TEST-ONLY (ring-UAF) | Sole double-Init trigger is `controller_test.cpp:26457`; all prod callers single-init + matched Shutdown/RAII; OMS owns `event_log` by value. |
| I-2 | hft-audit / thread-lifecycle | Writer starts UNCONDITIONALLY | `OmsFieldRegistry.hpp:758` Layer-5, no `mode`/`live` gate → paper/test/backtest all spin a pointless writer. Start/Stop atomic protocol is CORRECT — don't rewrite it. |
| I-3 | class-scan | IT IS A CLASS | `OrderEventLog_Reset` = 2nd confirmed instance; `BinanceAdapter_Init` (spawns-in-Init) = sharpest latent. Class 07/13 don't cover it. |
| A-1 | refute the fixes | ALL THREE REFUTED (as stated) | FIX-1 wrong gate-condition; FIX-2 TOCTOU on concurrent class-closure (OK for the test); FIX-3 wrong shape. |
| A-2 | refute test-only scope | CLAIM-A HOLDS (ring-UAF test-only); CLAIM-B REACHABLE + ON BY DEFAULT | The Reset disk_file race is a **3-way** prod race (producer-Reset / writer-fwrite / drainer-Append), `oms_event_log_mode=1` is the default. |
| A-3 | refute no-new-harm | FIX-1 (corrected) + FIX-2 = NO HARM; **FIX-3 drainer-join = HARM (H8 ~100× budget)** | Flags the live-capital × mode × paper-reset MOOT-UNREACHABLE matrix as an AR-11 code-read before any FIX-3. |
| CC | completeness-critic | 1 CRITICAL uncovered + recovery hole | The Reset race; + `LoadFromDisk` has NO body-integrity gate → silently-wrong warm-restart balance. |

## The reshaped picture (what's actually true)

**Root enabler (HIGH·design):** the async disk-writer thread starts **unconditionally** at `OmsFieldRegistry.hpp:758` (OMS_INIT_AUTOPOPULATE Layer 5), even in paper / test / backtest where it is pointless (mode-0 has no `disk_file`; the writer's only purpose is fwrite-disk-stall isolation, `OrderEventLog.hpp:170-177`). Everything below is downstream of this.

**Bug 1 — the test ring-UAF (MED·mechanical; the literal asan-blocker; TEST-ONLY):** `OrderEventLog_Init` (`:231-232`) re-runs `SPSCRing_Init` + `writer_thread_active.store(0)` with no StopAsyncWriter first. The test double-inits (`controller_test.cpp:26457`) on a log whose writer is already running → the later Free's join no-ops (`:399` guard sees 0) → `delete oms` frees the ring under the live writer → ASan UAF at `SPSCRing_TryPop:180`. **No production path hits this** (A-1/A-2 verified: prod Init always precedes Start; shutdown order joins the writer first; hot-reload/reconnect don't touch the OMS).

**Bug 2 — the PRODUCTION Reset disk_file race (CRIT·design; ON BY DEFAULT; NOT test-only):** `OrderEventLog_Reset` (`:492-521`, called from paper-reset `Async.hpp:737`) does `fclose`/`fopen`×2 on `disk_file` + `count=0` while the **live async writer** `fwrite`s/`fflush`es that same `FILE*` (`:303`/`:308`/`:372`) and `count++`s (`:298`) — and the **drainer** keeps `Append`ing (unparked; `paper_reset_in_progress` parks only slow paths). A **3-way race**: `fclose`-vs-`fwrite` = use-after-fclose on a libc `FILE*` (glibc heap-UAF); `count` is a non-atomic `size_t` raced across all three threads. `oms_event_log_mode=1` is the **default** (`ControllerConfig.hpp:1977`) + default path → the disk writer is armed by default → reachable in any paper session with a reset. The code already half-knows this (`Async.hpp:717-725` flags the hot-path quiesce as unfinished "conc-5" work; the writer level was never noted).

**Bug 3 — warm-restart recovery corruption (HIGH·structural):** `OrderEventLog_LoadFromDisk` (`:533-614`) validates the header (magic/version/width) but has **no body / whole-file integrity gate** — a full-width-but-scrambled record from the Bug-2 interleave is read as a valid `OrderEvent` and folded by `Portfolio_FromEventLog` into the warm-restart `balance` + `ks_peak_balance` seed (`OmsFieldRegistry.hpp:744-748`) → silently-wrong booted capital. The OMSEL02 `reserved` field is literally commented "future: checksum" (`:147`) but unwired.

**The class (MED·structural·wide):** "Init/Reset re-initializes thread-touched state without quiescing the owned thread first; spawn lives in `_Init` not `_Start`." Confirmed instances: `OrderEventLog_Init` + `OrderEventLog_Reset`. Latent carriers: `BinanceAdapter_Init` (spawns workers inside Init — a future reconnect/per-symbol refactor lights up the exact UAF), `NotifyState_Init`/`BinanceUserData_Init`/`ReconciliationLoop_Init` (safe by call-graph accident, not construction). Class 07 (audited-clean topology) + Class 13 (snap-capture-drift) do NOT cover it → genuinely new RBP class.

## Fix candidates — refuted / corrected / survived

| Fix | Status | Detail |
|---|---|---|
| **FIX-2** harden `OrderEventLog_Init` → StopAsyncWriter-first | ✅ SURVIVES for the asan-blocker (NO HARM, A-3) | Closes the known single-threaded double-Init (the test). A-1: NOT a robust *concurrent* class-closure (create→publish TOCTOU at `Start:386`-before-`:393`; double-join; overwritten `pthread_t`) — but those windows are unreachable for the sequential test + boot-once prod Init. Sufficient to make asan green; the robust concurrent form is .E-rework. |
| **FIX-1** gate the writer-start | ⚠️ CORRECTED CONDITION | A-1 refuted `event_log_mode==1 && _has_disk_path` (events are appended **mode-blind** at `OrderManager.hpp:1355`; live + mode-0 still logs; `Run.hpp:674` passes `cfg.oms_event_log_mode`, default 1 → the gate would kill the writer in a live-mode-0 run). The *correct* axis is **live-capital** (start the writer iff `ControllerConfig_IsLiveCapital`), which A-3 then ties to the MOOT question. NO HARM to backtest/tests (A-3: no async-state reads; sync fallback Append-order-identical; H9 intact). |
| **FIX-3** Reset quiesce via stop+**join** on the drainer/producer thread | ❌ REFUTED — HARM (A-1 + A-3) | `pthread_join` there blocks up to ~1ms (writer's `usleep(1000)` cadence `:378`) = **~100× the ≤10μs drainer budget** → guaranteed back-pressure per reset. The *correct* shape is **signal-only** (writer owns `disk_file`; Reset enqueues a `reopen_requested` atomic the writer polls — never touches the `FILE*` from another thread). |

## The one open DECISION (→ `/decision-check`; AR-11 code-read FIRST, do not fiat)

**The writer/disk-ownership design + the MOOT-UNREACHABLE reachability matrix.** Settle, by reading the live-capital × `event_log_mode` × disk × paper-reset × (sync-vs-async, producer/drainer/writer thread assignment) matrix:
- Does gating the writer-start to **live-capital-only** moot the Reset race? (Paper-reset is gated `!ControllerConfig_IsLiveCapital`, `Async.hpp:565`; live never paper-resets.) **CAUTION (orchestrator note):** gating only the *writer* does NOT fully moot it — in paper-mode-1 the drainer would then `fwrite` **synchronously** while the producer-thread Reset `fclose`s, so the producer-vs-drainer disk_file race persists unless paper *also* drops disk logging or the reset coordinates the drainer. The clean invariant is **single-owner `disk_file`** (completeness-critic option A): the writer owns open/close/rotate via a polled flag; nobody else touches the `FILE*`.
- Does paper *need* the async writer / disk persistence at all (warm-restart replay), or can paper go sync / no-disk?
- Wire the unused `reserved` checksum (or an `event_id`-monotonic gate) in `LoadFromDisk` so a torn file is rejected, not booked.

## Recommended path forward (for operator consult — gate does NOT auto-proceed)

1. **Unblock the asan ship-gate now (small, safe, do-now):** FIX-2 (harden `Init` StopAsyncWriter-first) — closes the test double-init; A-3 cleared it; structural-fix-over-patch + guards-compound. (Engine repo; LANDMINE 10.) Optionally also delete the redundant test `:26457` re-init. Re-run `run_all_tests.sh --full` → asan green = the gate clears.
2. **The production Reset race + recovery hole + the class** = the event-log-lifecycle concurrency work the code already homes to the **.E SPSC/event-log rework** (conc-5). Decision: do-now-vs-`.E.1` is a marginal-cost call that hinges on the reachability matrix → run the `/decision-check` above first. If the single-owner-`disk_file` fix is cheap + the matrix confirms it, do-now (heavier-default-for-capital; it's an on-by-default prod UAF). Else home to `.E.1` with a TD entry — **homed, not unhomed; never a silent defer.**
3. **Do NOT** implement FIX-3 as a drainer-thread join (H8).
4. **Codify the class:** new DESIGN_SPEC (spawn-in-`_Start`-not-`_Init`; Init/Reset quiesce-first) + new RBP Class (recurrence 2 confirmed + 3 latent) + a CI detector candidate.

## Ledger writes owed (propose at consult; not pre-written pending homing)
- TECH_DEBT-202: confirm root cause + **expand scope** (Bug-2 Reset race + Bug-3 recovery hole are new; were not in the original entry).
- New TD (or fold into the .E SPSC-rework home) for the disk_file single-ownership + LoadFromDisk integrity.
- New RBP Class candidate + DESIGN_SPEC.
- LOW side-findings: `usleep(100)` drainer stall (`:335`, burst-only); dead `writer_realloc_failed_count` observability row; live-shutdown late-push ordering smell (A-2).
