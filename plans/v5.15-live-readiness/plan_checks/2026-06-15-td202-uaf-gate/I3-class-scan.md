---
type: audit-report
audit: I-3 — IS THIS A CLASS, OR A ONE-OFF? (structural class-scan)
gate: 2026-06-15-td202-uaf-gate
target: TECH_DEBT-202 OMS async-writer UAF root cause
head: 3ee95dc
date: 2026-06-15
verdict: THIS IS A CLASS (≥2 confirmed instances) — codified discipline + CI detector warranted
---

# I-3 — Class-scan for the "re-init live thread-owning state without stop-first" UAF shape

## The SHAPE being hunted

A struct that owns a thread (pthread/`std::thread` + a `*_active`/`*_should_stop` atomic + an owned
SPSC ring or `FILE*`/buffer the thread touches) has an **Init/Reset that re-initializes that
thread-owned state WITHOUT first signalling+joining a possibly-running thread** — defeating the later
join and/or freeing/reopening memory under a live thread. Canonical: `OrderEventLog_Init`
(`CoreFrameworks/OrderEventLog.hpp:204-241`): `SPSCRing_Init(&log->async_ring)` :231 +
`writer_thread_active.store(0)` :232 with NO `StopAsyncWriter` first; its own `_Free` :247-271 DOES
stop-first (calls `OrderEventLog_StopAsyncWriter` :251).

## Triage table — every thread-owning Init/Reset/Free triple

| Struct / fn | Owns thread? | Stop-first on re-init? | Flag-clobberable join? | Verdict |
|---|---|---|---|---|
| **`OrderEventLog_Init`** `OrderEventLog.hpp:204` | YES (`writer_thread`, spawned by `StartAsyncWriter`) | **NO** — re-inits `async_ring` + `writer_thread_active=0` with no Stop | **YES** — clobbers `writer_thread_active`→0, so a later `_Free`/`_Stop` `if(active) join` is skipped → thread runs on freed `entries[]`/closed `disk_file` | **SAME-CLASS (canonical / TD-202 root)** |
| **`OrderEventLog_Reset`** `OrderEventLog.hpp:492` (called `Async.hpp:737`, paper-reset) | YES (same writer) | **NO** — `fclose(disk_file)`+`fopen` (:501-518) while the writer thread concurrently `fwrite`s `disk_file` (:303/:308/:372) and the `async_ring` keeps draining | N/A for join (doesn't touch the flag) but **UAF/write-to-closed-FILE on the live writer** | **SAME-CLASS (2nd confirmed instance)** |
| `OrderEventLog_Free` `OrderEventLog.hpp:247` | YES | YES (`_StopAsyncWriter` first :251) | — (correct reference impl) | SAFE (the correct shape) |
| `OrderEventLog_StopAsyncWriter` `:398` | YES | — (it IS the stop) | join guarded by `writer_thread_active` :399 — **this is the flag `_Init`/`_Reset` can defeat** | (mechanism, not a site) |
| `ReconciliationLoop_Init` `ReconciliationLoop.hpp:182` | thread owned by struct, but **spawned in separate `_Start` :213, NOT in `_Init`** | NO stop-first, but `_Init` re-inits ring+flags only (`reconcile_queue` :199, `shutdown_requested=0` :194) | latent: a 2nd `_Init` on a live obj WOULD clobber `shutdown_requested` + reset the ring under the live thread | **SAFE-in-practice / LATENT** — boot-once→Start→Shutdown-once lifecycle; no Reset; `_Init` not reachable on a live object. Same latent shape, no live trigger. |
| `BinanceAdapter_Init` `BinanceAdapter.hpp:255` | YES (`workers[]` — **spawned IN `_Init` :293** after ring :266 + `ws_active`/`shutdown_requested` re-init :267-269) | NO stop-first | latent: a 2nd `_Init` clobbers `shutdown_requested`/`ws_active` + re-inits `submission_queue` under live workers → `_ShutdownState` join over a reset flag | **SAFE-in-practice / LATENT (highest latent risk)** — `_Init` spawns the threads itself, so a re-`_Init` is the exact canonical defeat; SAFE only because nothing calls it twice + no Reset. Worth a stop-first guard or a re-entrancy assert. |
| `BinanceUserData_Init/_Start/_Shutdown` `BinanceUserData.hpp:~590/622/631` | YES (`ws_thread`+`keepalive_thread`, `std::thread`, spawned in separate `_Start` :623-624) | `_Shutdown` stops-first (`shutdown_requested=1` :632 → join :633-634) | `_Init` re-inits `shutdown_requested=0` :601 — latent if re-called live | **SAFE-in-practice / LATENT** — boot-once→Start→Shutdown-once; no Reset; Shutdown is correct. |
| `NotifyState_Init` `Notify.hpp:169` (spawns worker IN Init :178) / `_Shutdown` :238 | YES (`worker_tid`) | `_Shutdown` stops-first (`shutdown=1`+signal :241 → join :244) | `_Init` `memset`s the whole struct :172 incl. `worker_started` — latent if re-called live | **SAFE-in-practice / LATENT** — uses mutex+cond (H3 off-path async, not SPSC); boot-once; no Reset. NOTE: `_Init` spawns in-Init like BinanceAdapter → same latent re-entrancy. |
| `DepthRecorder_Init` `DepthRecorder.hpp:158` / `TickRecorder_Init` `TickRecorder.hpp:141` | **NO** (`FILE*` only, no thread, no ring, no active flag) | n/a | n/a | **SAFE by construction** — no thread owned; CSV writers on the caller's async thread. |
| EngineSharded producer/drainer/executors/slow_paths `Run.hpp:1275/1456/1392/1571` (`std::thread`) | threads owned by local vectors | — spawned once, joined once at shutdown (`:2304-2311`); no Init/Reset re-init path | NO | **SAFE by construction** — RAII `std::thread`, single spawn→single join; no re-init-while-running shape. |
| EngineSharded depth/gui `Run.hpp:839/1208` (raw `pthread`) | global `g_depth_tid`/`gui_tid` | spawned once, joined once (`:2299-2316`); `g_depth_tid` guarded by `!=0` :2299 | NO | **SAFE by construction** — single spawn→single join. |
| ExecutionCore `event_ring` (`ExecutionCore.hpp:224`) / OMS `result/ws_result/reconcile/submit` queues (`OmsFieldRegistry.hpp:723-727`) / EngineCommon `tick_ring` (`:245`) | rings crossed by EXTERNAL threads (hot/slow/drainer); struct spawns no thread of its own | n/a | n/a | **SAFE by construction** — no struct-owned thread + no in-struct active-flag-guarded join to defeat. |

## "Is this a class?" verdict

**YES — a class, not a one-off.** TWO confirmed live instances (`OrderEventLog_Init` + `OrderEventLog_Reset`,
both inside the same struct), PLUS three LATENT same-shape carriers (`BinanceAdapter_Init`,
`NotifyState_Init`, `BinanceUserData_Init`/`ReconciliationLoop_Init`) that are SAFE only because nothing
re-enters their `_Init` on a live object and none has a Reset — i.e. safe by *call-graph accident*, not
by *construction*. `BinanceAdapter_Init` is the sharpest latent: it spawns the workers INSIDE `_Init`
(BinanceAdapter.hpp:293), so a future second `_Init` (a re-connect refactor, a per-symbol re-init) is the
exact canonical UAF. The shape recurs across 5 structs; the safety is non-structural. That is the
signature of a bug CLASS.

## Recommendation: codified discipline + CI detector (NOT a one-site fix)

A one-site fix on TD-202 leaves `OrderEventLog_Reset` (2nd instance) AND three latent carriers a future
refactor can light up. Recommend:

1. **Fix BOTH OrderEventLog sites now** — `_Init` and `_Reset` must `StopAsyncWriter` (or assert
   `!writer_thread_active`) before touching ring/`disk_file`; `_Reset` must quiesce the writer for the
   `fclose`/`fopen` window (the paper-reset at `Async.hpp:737` parks only the SLOW paths via
   `paper_reset_in_progress`, NOT the async writer — same already-known quiesce gap the `:724-725` comment
   flags for the hot path / "conc-5").
2. **Codify a discipline** (new DESIGN_SPEC, data/concurrency family): *"An Init/Reset on a thread-owning
   struct MUST stop-and-join the owned thread (or assert its active-flag is 0) before re-initializing any
   thread-touched state (ring / buffer / FILE / the active flag itself). Spawn belongs in a separate
   `_Start`, never in `_Init`."* — the `_Free`-stops-first / `_Init`-clobbers asymmetry is the tell.
3. **New RBP Class + CI detector** (mechanical, high-confidence): flag any fn matching `*_Init`/`*_Reset`
   that writes a `*_thread_active`/`*_should_stop` atomic to 0 **or** calls `SPSCRing_Init`/`fclose`/`fopen`
   on a struct field, WITHOUT a preceding `*_Stop*`/`pthread_join`/`.join()`/active-flag assert in the same
   body. Pairs with the H3/Class-07 threading family; Class 07 is "audited-clean topology" and Class 13 is
   "snap-capture-drift" — neither covers the re-init-defeats-join LIFECYCLE shape, so this is a NEW class.

Cross-ref: TD-202 root (`OrderEventLog.hpp:204/231-232` vs `:247/251`); 2nd instance `:492` ←
`Async.hpp:737`; latent `BinanceAdapter.hpp:293`, `Notify.hpp:178`, `BinanceUserData.hpp:623`,
`ReconciliationLoop.hpp:213`.
