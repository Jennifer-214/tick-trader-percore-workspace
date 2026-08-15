---
type: evidence-dossier
status: FROZEN — orchestrator session code-trace, saved at completion
directive: AM-4 evidence re-locate — can a sharded leg open without its partner? (the D-291/AM-4 verify-at-code-time conditional)
engine_head: 5ac8a7b
delivered: 2026-08-14
decision: D-420 (this dossier is its evidence body)
consumed_by: the E.1.2 Steps 3-5 v11 delta implementation + the Step-5 fixture design
sister_reports: i-class money-surfaces / d289-blast-radius / close-gate-surface (same directory, at receipt)
---

# AM-4 evidence dossier — atomic-legs premise + re-derive robustness (orchestrator trace)

**Question (plan AMENDMENT 3 / D-291/AM-4):** persist `partner_pending_pnl` + RE-DERIVE
`partner_pending_bitmap` on load via slot parity — UNLESS a sharded leg can open without its
partner, in which case fall back to persist-both. Verified at code-time, per the amendment.

**Verdict: premise REFUTED in the letter; fallback trigger DEAD anyway. Re-derive stands (D-420).**

## 1. The field/geometry ground truth (c-class mis-cite resolved)

- `partner_pending_pnl` — `Money`, NodeContext field, `CoreFrameworks/ControllerEventLoop.hpp:488`.
- `partner_pending_bitmap` — `uint16_t`, EventLoopState (NOT per-node), `ControllerEventLoop.hpp:901`
  (migration comment `:894-899`: bit N = node N's old `partner_pending_active`).
- The c-class currency report's `Portfolio.hpp:488/:901` cites were the right LINES in the wrong FILE.
- State machine (drainer thread, `EventLoop_DrainPostFillOneCore`): merge `:1814-1828`
  (bit set → `total_net = Money_Add(partner_pending_pnl, exit_net_pnl)` → one W/L stat → pnl zeroed
  `:1827` + bit cleared `:1828`); park `:1830-1831` (pnl **= assignment**, not add; bit set). Init `:1119`.
- Slot geometry: leg slots = `2N`/`2N+1` under partials (`Sharded_LegSlot :1338`, `Sharded_SlotNode :1375`).

## 2. Can a leg open without its partner? YES — rare, by design

- Hot path pushes BOTH entry legs in one tick; leg B is tied to leg A's push success — "so we never
  end up with a leg B floating without leg A" (`CoreFrameworks/ExecutionCore.hpp:681-691`). The
  CONVERSE is reachable: `entry_b_pushed = SPSCRing_TryPush(...)` (`:691`) can fail alone (ring
  full); the zombie-fix discipline (`:615-630`) leaves failed pushes un-flagged, and a leg-B-only
  retry never happens (`can_enter` requires a flat node) → **permanent orphan leg A**.
- Degenerate zero-qty legs CANNOT cause it: `Sharded_ValidatePartialExitCfg`
  (`ControllerEventLoop.hpp:1388-1417`) boot-refuses `partial_exit_pct` outside (0,1) EXCLUSIVE;
  node count capped at `MAX_PORTFOLIO_POSITIONS/2`.
- Independent of open-atomicity, mid-pair CAPTURE windows exist anyway: the periodic save runs on
  the **producer thread** against drainer-owned state (`CoreFrameworks/EngineSharded/Async.hpp:447-452`; the
  documented KNOWN-RACE `:453-466`), and the shutdown save (`CoreFrameworks/EngineSharded/Run.hpp:2305`) precedes
  the thread joins (`:2384-2399`). Pre-existing, snapshot-wide (torn 16B Money reads included),
  **E.1.3 coherence scope — named here, not fixed here.**

## 3. Why re-derive still wins — every reachable single-leg state, both options

| Persisted state | Re-derive `bit N = active(2N) XOR active(2N+1)` | Persist-both |
|---|---|---|
| Normal mid-pair (TP1 exited, leg B rides — the state the row exists for) | bit=1 correct; pnl round-trips | same |
| Orphan leg A (leg B never opened) | bit=1, pnl=0 → exit merges-with-zero → **one clean W/L** (better than the runtime's own no-restart park-forever + next-merge poison) | bit=0 faithful → park-and-poison replays |
| Both legs closed, stale parked pnl (flatten closed the partner without merging) | bit=0 → stale pnl later OVERWRITTEN (park `:1830` is assignment) → self-heals | bit=1 resurrected → stale pnl merges into an unrelated trade → corrupt stat |
| Torn mid-cycle capture (producer-thread save) | degrades to the rows above | degrades to the rows above — no option is torn-proof pre-E.1.3 |

Re-derive ties-or-wins in every row → the persist-both fallback trigger is dead.

## 4. Containment

- **Live boots flat:** `ShardedSnapshot_Load` fires only `if (!live_trading)` (`Run.hpp:1065-1073`);
  live mode reconciles from exchange truth. The whole surface is **paper W/L-stats**.
- Consumers of the partner fields: the drainer state machine + `NodeCtxInitRegistry.hpp` init/reset
  rows + the F-018 tests (`tests/controller_test.cpp:9882-10016`). **Zero GUI/TUI readers.**
- Cross-geometry files refuse at load (partial-toggle mismatch refuse — `ShardedSnapshot_Load`
  closing comment), so the XOR parity is well-defined whenever the re-derive runs.

## 5. The `node_dd_pct` DROP rider

No load-side recompute code needed: the kill-switch eval recomputes `node_dd_pct` from persisted
`node_peak_balance` BEFORE reading it, in the same pass (`ControllerEventLoop.hpp:3278` compute →
`:3292` read; peak ratchet `:3267-3270`; peak stays persisted — registry row `:90`). The field is
eval-transient; a restored zero lives only until the first eval cycle and is never read before then.

## 6. Implementation spec this dossier feeds (D-420)

1. Registry `MemHeaders/NodeCtxPersistRegistry.hpp`: DROP `:91`
   `X(node_dd_pct, Money, SCALAR, 0, COMMIT)`; ADD `X(partner_pending_pnl, Money, SCALAR, 0, COMMIT)`
   in the **W/L-stats cohort** (beside `node_gross_wins/losses`) — cohort-semantic placement per
   D-420; de-number the cohort comments (indices live in the listing golden). Net 0 rows (==29
   count-lock holds — vacuously, as the triple-vacuity analysis predicted; the listing golden is the
   non-vacuous layer) / net 0 bytes (1944 holds).
2. `NodeSnap` staging (`ShardedSnapshotPersist.hpp:371`): `node_dd_pct` → `partner_pending_pnl`
   (D-305 name-match convention; READ/COMMIT projections address `s.<NAME>`/`ctx.<NAME>`).
3. Post-walk re-derive in `ShardedSnapshot_Load` (EventLoopState-level, after the per-node walk,
   with the re-activation finalizer): `bit N = ((bm>>2N) ^ (bm>>(2N+1))) & 1` under
   `partial_exit_enabled`, else 0.
4. `SHARDED_SNAPSHOT_VERSION` 10→11 (`ShardedSnapshotPersist.hpp:112`) rides the SAME commit
   (paired-bump forces it — the guard's designed maiden firing).
5. Step-5 fixtures: (i) mid-pair round-trip (bit=1 + parked pnl + one leg active → save → load →
   bit re-derived + pnl value round-trips + merge produces the combined stat); (ii) orphan-leg
   (one leg active, pnl=0 → load → bit=1 → graceful merge-with-zero = one W/L).

## 7. Baseline anchor

Suite **3702/0** + latency-path conformance clean at engine HEAD `5ac8a7b` (this session's
pre-delta baseline run; `./build.sh test`).
