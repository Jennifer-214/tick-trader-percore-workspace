# A2 — ADVERSARIAL scope-refutation (TD-202 OMS async-writer UAF gate)

**Role:** Layer-2 adversarial subagent under `/precoding-audit-gate` Stage 3.5. Framing = DEFAULT-REFUTED.
**Engine HEAD:** 3ee95dc. **Surface:** OrderEventLog / OmsFieldRegistry / OrderManager / Async.hpp paper-reset / Run.hpp boot+shutdown / BinanceAdapter.
**Attack target:** CLAIM-A (UAF is test-only) + CLAIM-B (paper-reset sibling race is the ONLY prod manifestation) + I-3 latent carriers.

---

## VERDICT SUMMARY

| Claim | Verdict |
|---|---|
| CLAIM-A "ring-free UAF is TEST-ONLY (only re-Init-on-live-writer site = controller_test.cpp:26457)" | **HOLDS (test-only)** — could not break for the re-Init / double-Init / Free-while-clobbered shape. No production path re-inits or frees the event_log while its writer runs. |
| CLAIM-B "paper-reset sibling race is the ONLY production manifestation, AND it is reachable" | **REACHABLE — STANDS as a real production race.** Could not refute reachability; the default paper config arms the disk writer + the drainer is NOT parked. **Stronger than the seed states: the DRAINER (live Append producer) is also unparked, not just the writer.** |
| I-3 latent carrier `BinanceAdapter_Init` re-entry | **NO production re-entry** — called once at boot; reconnect uses a different fn that never touches the OMS. |

---

## CLAIM-A — re-Init / double-Init / Free-while-live (HOLDS test-only)

Enumerated every production lifecycle entry to the event log:

- **OMS construction is single.** `OrderManager_Init` (OrderManager.hpp:861) → `OMS_INIT_AUTOPOPULATE` (OmsFieldRegistry.hpp:693) is called **exactly once** in the sharded engine: `Run.hpp:674`. `OMS_INIT_AUTOPOPULATE` and `OrderManager_Init` appear at no other production call site (grep: only Backtest + the macro/definition). No production `OrderEventLog_Init` / `_InitWithFile` / `_StartAsyncWriter` exists outside the AUTOPOPULATE macro body (grep returned empty excluding the registry+header).
- **Model hot-reload does NOT re-init the OMS.** Run.hpp:1738+ swaps `ml_zoos[c]` / `model_handle` / `ensemble_handle` only (shadow-load pattern). Never touches `oms` or `event_log`.
- **Market-data reconnect is not the OMS.** `BinanceStream_Reconnect` (sharded path Run.hpp:1369) reconnects the price-feed websocket `bs`; the OMS / event_log / writer thread are untouched. (The other `BinanceStream_Reconnect` hits at main.cpp:667/788 are the **deprecated legacy single_core** path, which NEW-1 now boot-refuses for live capital — main.cpp:299-312.)
- **Shutdown frees AFTER joining the producer+writer.** `EngineSharded_Run` exit ordering: `drainer.join()` (Run.hpp:2308) → `OrderManager_Shutdown` (Run.hpp:2327) → `OrderEventLog_Free` (OrderManager.hpp:1609) → `StopAsyncWriter` joins the writer (OrderEventLog.hpp:251/398-403) **before** munmap/fclose. The sole `Append` producer (drainer) and the writer are both quiesced before any free. **No shutdown UAF on the event log.**
- **SIGINT/SIGTERM is async-signal-safe.** `EngineSharded_SignalHandler` (Boot.hpp:59) only flips two `sig_atomic_t` flags; it does NOT call Free/Shutdown. The actual teardown runs on the main thread after joins. No signal-path UAF.

**Could not break CLAIM-A.** It holds.

### CLAIM-A side-finding (NEW, not a UAF — ordering smell, LOW)
LIVE-only: the reconciler thread (`ReconciliationLoop.hpp:147` pushes `oms->reconcile_queue`) and user-data WS thread (`BinanceUserData.hpp:481` pushes `&oms->ws_result_queue`) are shut down at Run.hpp:2392/2399 — **AFTER** `OrderManager_Shutdown` (2327). This is NOT an event-log UAF (`OrderEventLog_Free` only frees `event_log`'s `entries[]`/`disk_file`, not the reconcile/ws rings; the OMS struct itself is stack-local and outlives both threads to function return). Worst case is a late push into a still-valid ring that nothing drains (drainer already joined). Latent — homes alongside TD-202's conc pass, not a blocker.

---

## CLAIM-B — paper-reset sibling race (REACHABLE; STANDS)

Tried to refute reachability on three axes; all failed.

**Axis 1 — is the disk writer actually armed in a PAPER deployment?** YES, by DEFAULT.
- `cfg.oms_event_log_mode = 1` is the unconditional default (`ControllerConfig.hpp:1977`), independent of live/paper. `engine.cfg` does NOT set the key → default stands.
- `event_log_path` defaults to `"logging/order_events.bin"` — non-empty (`OrderManager.hpp:867`).
- So `OMS_INIT_AUTOPOPULATE` Layer 4 predicate `(_event_log_mode)==1 && _has_disk_path` is TRUE → `OrderEventLog_InitWithFile` opens `disk_file` (OmsFieldRegistry.hpp:733/752), then Layer 5 `StartAsyncWriter` (OmsFieldRegistry.hpp:758) spawns the writer **with disk_file != nullptr**. → The fwrite-in-`ApplyEvent` path (OrderEventLog.hpp:302-308) is LIVE in default paper.

**Axis 2 — is the reset on the same thread as Append (serialized)?** NO — three distinct threads.
- `OrderEventLog_Reset` (Async.hpp:737) runs inside `EngineSharded_Async_FanOut` → called from the **PRODUCER thread**'s `fan_out` lambda (Run.hpp:1315/1349/1375).
- `OrderEventLog_Append` callers (OrderManager.hpp:1355/1465/1561) run on the **DRAINER thread** (`OrderManager_Tick`/`ProcessFillCommand` in the drainer body Run.hpp:1456-1503).
- `ApplyEvent` (`entries[count++]` + `fwrite(disk_file)`) runs on the **WRITER thread** (OrderEventLog.hpp:349-380).

**Axis 3 — are the Append producer and writer parked during the reset?** NO.
- The reset sets `paper_reset_in_progress` (Async.hpp:571) which parks **only the SLOW paths** (Run.hpp:1671). The DRAINER loop gates on `!g_engine_sharded_shutdown` ONLY (Run.hpp:1464) — it does **not** read `paper_reset_in_progress`. So the drainer keeps calling `Append` during the reset.
- The reset path contains **no** `StopAsyncWriter` — the writer thread is never signaled/joined. It keeps `ApplyEvent`-ing.
- `cores[c].active = 0` (the hot-path quiesce) is set **AFTER** the OMS reset (Async.hpp:715-727), and only governs the HOT path's TP/SL eval — not the drainer's Append nor the writer.
- The yield at Async.hpp:576 is explicitly best-effort ("Worst case they don't yet... proceed concurrently").

**Resulting race (3-way) during a default-paper reset:**
1. PRODUCER: `OrderEventLog_Reset` → `fclose(disk_file)` then `fopen` new (OrderEventLog.hpp:501-518); sets `count=0`, `next_event_id=1`.
2. WRITER: mid `ApplyEvent` — `fwrite(&event, …, disk_file)` on the handle the producer just `fclose`d → **fwrite on a closed/dangling FILE\*** + `entries[count++]` against a `count` the producer just zeroed (lost/overwritten events, torn `count`).
3. DRAINER: concurrently `Append` → `SPSCRing_TryPush` + `next_event_id.fetch_add` racing the producer's plain `count=0` / `next_event_id.store` (the store is relaxed; `count` is a **non-atomic** `size_t` written by producer + read/written by writer = data race / torn).

The `disk_file fclose/fopen` vs writer-`fwrite` is the sharp UAF-class edge (use-after-fclose on FILE\*); the `count`/`entries` overlap is a concurrent non-atomic data race. **This is the ground-truth seed's race, confirmed reachable under the shipping default config — CLAIM-B's manifestation STANDS, and is reachable without any operator opt-in.**

Note the seed undersold it: the seed says reset "parks SLOW paths but NOT the async writer." True — but **the DRAINER (the live Append producer) is also unparked**, so the race is producer↔writer↔drainer (3-way), not just producer↔writer (2-way). The writer can be fwriting an *already-pushed* event AND the drainer can be pushing a *new* one, both straddling the fclose+count=0.

**Could not refute CLAIM-B reachability.** It stands as a real production race in default paper mode.

---

## I-3 latent carriers (Init-spawns-thread re-entry)

- **`BinanceAdapter_Init`** (BinanceAdapter.hpp:255, spawns workers): single call site `Run.hpp:589`, boot-only, live-only. No reconnect/per-symbol/resubscribe path re-Inits it (`BinanceUserData` reconnect re-obtains the listen key + forces a WS reconnect inside the already-spawned thread; it does NOT call `BinanceAdapter_Init`). **No production re-entry.**
- **`OrderEventLog_StartAsyncWriter`**: only fires inside `OMS_INIT_AUTOPOPULATE` (single boot call). No standalone re-arm.
- No other Init-spawns-thread struct shows a production re-entry on this surface.

---

## NET

- CLAIM-A: **HOLDS test-only** (re-Init/double-Init/Free-while-live shape).
- CLAIM-B: **REACHABLE in default paper** — the sharded paper-reset is a genuine 3-way prod race (producer fclose/fopen + count=0 vs writer fwrite/entries vs drainer Append), gated by the default `oms_event_log_mode=1` + non-empty default path, with neither writer nor drainer parked. This is the real prod manifestation and it is **on by default**.
- New prod trigger surfaced: drainer (not just writer) is unparked during reset (3-way, not 2-way).
- New LOW side-finding: live shutdown stops reconciler/user-data threads AFTER `OrderManager_Shutdown` (ordering smell, not an event-log UAF).
