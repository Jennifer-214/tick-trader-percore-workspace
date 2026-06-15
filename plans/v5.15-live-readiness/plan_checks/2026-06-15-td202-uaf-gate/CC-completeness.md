# CC-completeness — Layer-2 COMPLETENESS-CRITIC (TD-202 OMS async-writer UAF gate)

Surface: OMS `OrderEventLog` async-writer UAF (TECH_DEBT-202) + its fixes (gate writer-start / harden Init / harden Reset).
Other agents covered: I-1 blast-radius/caller-set, I-2 thread-lifecycle/writer-start, I-3 class-scan, A-1 fix-refutation, A-2 scope/production-reachability, A-3 no-new-harm/H3/H8.
This critic asks: **what did they all miss?** Walked the edge checklist (persistence / observability / GUI / deploy / external-tooling / money-path).

HEAD 3ee95dc. All citations file:line against current code.

---

## TOP FINDING (CRITICAL) — the OTHER UAF in the same file: `OrderEventLog_Reset` races the LIVE writer thread on `disk_file`

The TD-202 fix targets the *Init / StartAsyncWriter* surface (double-start, entries[] race). **An identically-shaped, equally-live UAF sits in `OrderEventLog_Reset` and NO audit listed it** (I-2 was thread-lifecycle but scoped to writer-START; the Reset path is a DIFFERENT lifecycle event that also touches writer-owned state). Production-reachable in paper mode — the headline live-readiness mode.

**The race:**
- Paper reset runs on the **PRODUCER thread** (`EngineSharded_Async_FanOut`, `Async.hpp:565-750`), which calls `OrderEventLog_Reset(&state.oms->event_log)` at `Async.hpp:737`.
- `OrderEventLog_Reset` (`OrderEventLog.hpp:492-521`) does, on `disk_file`: `fclose` (:501) → `fopen "wb"` (:502) → `fwrite` header (:514) → `fflush` (:515) → `fclose` (:517) → `fopen "ab"` (:518). **Three reassignments + two closes of `log->disk_file`.**
- The **async writer thread is LIVE** the whole time. `OMS_INIT_AUTOPOPULATE` Layer 5 (`OmsFieldRegistry.hpp:758`) unconditionally `StartAsyncWriter`s at boot; nothing stops it for a paper reset. The writer's `ApplyEvent` does `fwrite(&event, ..., log->disk_file)` (`OrderEventLog.hpp:303`) + `fflush(log->disk_file)` (:308), and `AsyncWriterRoutine` does `fflush(log->disk_file)` (:372).
- **Coordination gap:** paper reset sets `paper_reset_in_progress` (`Async.hpp:571`), which parks ONLY the per-core SLOW-path threads (`Run.hpp:1671`). The **drainer** thread is NOT gated — it keeps calling `OrderEventLog_Append` → ring-push (`Async.hpp:840` path) — so the writer keeps draining + writing to `disk_file` exactly while the producer recreates it.

**This is a use-after-free / concurrent-`FILE*`-corruption window on the same `disk_file` field the TD-202 entries[]-race fix is about** — and it is *worse* than the Init surface because it touches a `FILE*` (libc stdio buffer): a write to a closed `FILE*` is UB (heap-UAF in glibc), and two threads `fwrite`/`fflush`-ing through one un-locked `FILE*` interleave bytes.

The existing code KNOWS this class — `Async.hpp:717-725` (persist-8 .E.0.10) explicitly notes the hot-path mirror is outside the reset's reach and that "the robust version (full hot-path quiesce during reset, like the slow path at Run.hpp:1670) pairs with conc-5's concurrency pass." The **writer thread is the same unquiesced-during-reset hazard, one level down, and is NOT noted.**

---

## PERSISTENCE / RECOVERY VERDICT — YES, the Reset race CAN produce a corrupt file that mis-replays balance

Walk the failure: writer `fwrite`s a partial `OrderEvent` (or the producer's header `fwrite` at :514 interleaves with a writer event `fwrite`) → `order_events.bin` ends up with a torn body OR a valid-looking header followed by a stale-epoch event tail, OR (UAF) a glibc crash.

Does `OrderEventLog_LoadFromDisk` (`:533-614`) catch it on next boot?
- Header: validates magic OMSEL02 (:553), rejects OMSEL01 (:545 H21 tombstone), `format_version` (:558), `fpn_width` (:565), `entry_size` (:571). **Robust on the header.**
- **Body: NOT robust.** The replay loop (`:590`) is `while (fread(&event, sizeof(event), 1, f) == 1)`. A torn final record (short read) is silently dropped by the `== 1` guard — *benign*. BUT: there is **NO per-event sanity check** (no `event_id` monotonicity assert, no `type`/`order_type` enum-range check, no `core_id ∈ [0,MAX)` validation pre-fold; the fold's `slot` guard at `:712` only skips out-of-range core_id, it does not reject a *garbage in-range* event). A reset-race that leaves a full-width but **semantically scrambled** record (e.g. a header's 32 bytes landing mid-event-stream because the producer's `fwrite(&hdr,...)` at :514 interleaved a writer `fwrite(&event,...)` at :303) is read as a valid 176B `OrderEvent` and folded into balance/portfolio.
- **The silently-wrong replayed balance is real:** `Portfolio_FromEventLog` (:697) replays a scrambled FULL_FILL → wrong `Money_Mul(price,qty)` notional → wrong balance, then `OMS_INIT_AUTOPOPULATE` adopts it as the boot balance (`OmsFieldRegistry.hpp:744-748`) and seeds `ks_peak_balance` from it. **A capital-bearing warm-restart boots on a corrupted balance with no integrity gate.** (Aggravator: the OMSEL02 header carries `reserved` = "future: checksum" (`OrderEventLog.hpp:147`) — the checksum slot exists but is UNUSED, so there is no whole-file integrity check to catch any of this.)

So the chain is real but **multi-step + low-probability** (requires the reset `fwrite` to interleave a writer `fwrite` at a record boundary that survives header validation). Severity: the *race* is HIGH (UAF/UB on a live `FILE*`); the *silently-wrong-replay* downstream is MED (low probability, but capital-bearing + no integrity net). Both are uncovered.

---

## CHEAPER / MORE-CORRECT FIX nobody proposed

**Candidate A (best — structural, kills BOTH UAF surfaces): make `disk_file` writer-thread-owned.** Today the producer (Reset) and the boot path both touch `disk_file` directly; the writer also touches it. Move ALL `disk_file` open/close/rotate into the writer thread via a command (a `reset_requested` / `reopen_requested` atomic flag the writer polls in its drain loop, alongside `writer_should_stop`). Then `OrderEventLog_Reset` sets the flag + spins until the writer ACKs; the producer NEVER touches `disk_file`. This collapses the Init-race AND the Reset-race into one invariant: **`disk_file` is single-thread-owned (writer)** — the SPSC discipline the file already claims for `entries[]` (`:179`) extended to the file handle. Sister to the existing `writer_should_stop` quiesce primitive; ~no new infra.

**Candidate B (cheapest correct — single shared quiesce primitive):** the file already has `StopAsyncWriter` (join) + `StartAsyncWriter`. `OrderEventLog_Reset` should bracket its `disk_file` churn with `StopAsyncWriter` … `StartAsyncWriter` (drain + join the writer first, exactly as `Free` does at `:251`). This is the *same* primitive the TD-202 Init fix will lean on. One quiesce primitive (Stop/Start) shared by Init + Reset + Free = the unified answer. Downside vs A: stop/start thrash per paper-reset (acceptable — paper reset is operator-rare), and it must pair with parking the DRAINER too (or accept the ring buffering across the gap — fine, ring is bounded + writer drains on restart).

**Recommendation:** the TD-202 fix should be scoped to the **`disk_file` ownership class**, not just the Init entry-point. Candidate B is the minimal correct close (reuse Stop/Start in Reset); Candidate A is the design-once-maintain-forever close (writer-owned handle). Either way: **add the unused `reserved` checksum** (or a per-record `event_id`-monotonic gate in `LoadFromDisk`) so a torn/scrambled file is REJECTED, not silently folded into a capital balance.

---

## OTHER UNCOVERED SURFACES (ranked)

2. **Observability staleness (MED) — counters mislead under any writer-disable.** `log_full_drops` / `ring_full_spins` / `writer_realloc_failed_count` (`OrderEventLog.hpp:195-197`) are surfaced via snapshot (`ShardedSnapshot.hpp:110-119`) → TUISnapshot (`EngineTUI.hpp:939-941`) → one-shot Health_Log WARN/CRIT (`Async.hpp:511-551`). **If a TD-202 fix gates the writer OFF in mode-0** (the prompt's FIX-1), these counters stay zero forever and the observability path goes silent — but that's *correct* in mode-0 (no writer = no distress; nothing to observe). The real gap: the WARN strings (`Async.hpp:517-519`, :527-529) describe the **legacy malloc/realloc-growth model** ("entries[] cannot grow", "investigate disk health or bump ring size"). Post-v5.11.5.C the buffer is fixed mmap; `writer_realloc_failed_count` is documented dead ("should stay 0", `:196`/`:940`). The CRITICAL Health_Log at `:527` fires on a counter that can no longer increment — a misleading/dead observability row. Not a TD-202 blocker, but a finding the gate touches (it lives in the same FanOut block).

3. **GUI display↔execution (LOW, Class-2) — no panel reads event-log STATE cross-thread.** Only the three distress counters reach the GUI (via the snapshot, already-published, no live cross-thread read of `event_log`). Trade History reads the CSV (`ShardedTradeLog` / TradeReader), not `order_events.bin`. No panel folds the event log live. A writer-gate fix changes NO display. CLEAN on Class-2.

4. **Deploy / decimal-epoch interaction (LOW — already handled, but verify the gate doesn't bypass it).** Warm-restart across the decimal epoch (LANDMINE 3) is handled: `InitWithFile` ROTATEs a stale-magic file aside (`:441-455`, D-175a) and `LoadFromDisk` refuses OMSEL01 (`:545`). **Caveat:** the Reset race (finding 1) writes an OMSEL02 header but could leave mixed-content; the rotate guard only fires on a *stale magic*, not on a *current-magic-but-torn-body* file — so the epoch guard does NOT cover the Reset-corruption case. A writer-disable gate in mode-0 does not change the boot banner (`OMS_INIT` prints replay/persistence lines on stderr only). No live-readiness boot-gate currently asserts event-log integrity (the unused checksum is the missing hook).

5. **External tooling (CLEAN).** Grep of `tools/` `Backtest/` `tests/` for `order_events` returns NOTHING — no tool, backtest, or parity harness reads `order_events.bin`, and nothing depends on async-written timing. Backtest uses `Backtest_Run`→sharded with mode-0 (no disk persistence in backtest). So the gate has no external-tool blast radius. (One-liner caveat: `controller_test` exercises the event-log fold in-memory; verify a writer-gate change keeps the sync-path fold tests green — they run writer-inactive, which is exactly the gated path, so they should be unaffected / actually MORE representative.)

6. **OMS money-path / oms-ts-2 reconciliation (CLEAN — async vs sync does not affect booking).** Fee/P&L booking visibility is on `HandleFill`/`DrainPostFill` (the live authoritative path, `OrderManager.hpp:311-314`), NOT the event log — the event log is a *derived replay* source, and `Portfolio_FromEventLog` is explicitly best-effort (passes `Money_Zero()` fee_rate, `OmsFieldRegistry.hpp:741-743`). `sum(core_realized)==realized_pnl` (oms-ts-2) is computed off live OMS state, independent of writer sync/async. Async-vs-sync writer timing changes only WHEN the disk copy lands, never the in-memory booking. The gate has no money-path correctness impact.

---

## Net

The formal audits boxed the **Init/StartAsyncWriter** entry-point. The completeness gap is that **`disk_file` has a SECOND unquiesced concurrent-access site in `OrderEventLog_Reset` (paper-reset path, producer thread, live writer)** — same field, same class, equally production-reachable, and capable of corrupting `order_events.bin` into a silently-wrong replayed capital balance because `LoadFromDisk` has header-validation but NO body/whole-file integrity gate (the `reserved` checksum slot is unused). Recommend scoping the TD-202 fix to the **`disk_file`-ownership class** (writer-owned handle, or a single Stop/Start quiesce primitive shared by Init+Reset+Free) + adding the file-integrity gate so a torn replay is rejected, not booked.
