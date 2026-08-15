---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: /accounting-audit-lens map of the two money-path surfaces (AM-4 partner_pending persist + F-096 Money leg-split)
agent_class: i-class
delivered: 2026-08-14
consumed_by: the v11-delta + F-096 implementation + the paired a-class refute (refute-spots §8)
sister_reports: orchestrator-am4-evidence.md · i-class-d289-blast-radius.md · i-class-close-gate-surface.md (this directory)
---

# I-CLASS SURFACE MAP — E.1.2 Steps 3-5 money-path surfaces (AM-4 partner_pending persist + F-096 Money leg-split)

**Agent:** I-class investigative · **Lens:** `/accounting-audit` (10-category checklist) + H4 · **Repo:** `/home/caramel/code/FoxML_Trader_v2` @ 5ac8a7b (`feat/v5.15-live-readiness`) · **Read-only; no edits made.**
**Skill/arming honored:** `.claude/skills/accounting-audit/SKILL.md` walked; nav-infra consulted (`DOCS/CODE_MAP.md` confirms `EventLoop_DrainPostFillOneCore` @ 1611); mechanical tools RUN (results in § 7). Decided forks honored (D-291/D-302/D-305, AM-4 disposition at `plans/v5.15-live-readiness/subplans/2026-06-15-v5.15.5.F.4d.1.E.1.2-nodestate-soa-layout.md:61,216`); one plan-carried open question is now ANSWERED with code evidence (§ 1g) — this is a flag, not a re-litigation.

---

## 0. Executive summary

- All session-finding cites VERIFY (± ≤2 lines; exact table § 1a). No GUI/TUI consumer of either partner field — confirmed by repo-wide grep.
- **The XOR re-derive (AM-4) is SOUND across the full reachable state space**, including orphan single-leg trades, *because* the park at `ControllerEventLoop.hpp:1830` is an ASSIGNMENT (overwrite-heals stale pnl when bit=0) and merge-with-zero on an orphan produces the *correct* W/L classification. The plan's persist-both fallback is NOT triggered even though legs are provably non-atomic (§ 1g).
- The one non-self-healing combo is a **torn producer-thread snapshot capture** landing between drainer Phase A (position close) and Phase A.5 (park) — restored bit=1 with stale/zero pnl merging a wrong magnitude into one gross bucket. Paper-only, microsecond window, same pre-existing class as the documented balance tear (`Async.hpp:453-467`). Persist-both would NOT close it either (§ 4 H-3).
- **F-096:** `order_qty_d` has exactly two reads (`:888` guard, `:926` payload). Today's path violates `money_from_double_payload`'s own documented contract ("cfg-PAYLOAD bridge ONLY", `FixedPointN.hpp:2302,2319-2322`) and contains a live guard/payload rounding mismatch that can submit a **zero-qty Money order → un-closeable zombie position + permanent partner-parked state** (§ 2b — new finding, strengthens the fix). The Money fix is NOT bytewise-identical at leg-A qtys: half-even vs `llround` half-away diverge on genuine ties, which are *common* for pct ∈ {0.25, 0.5, 0.75} (§ 2c).
- Guard replacement must be `Money_Gt(leg_qty, Money_Zero())`, NOT `!Money_IsZero` — the clamp `[0.0,1.0]` (`CfgFieldRegistry.hpp:760`) makes negative legs unreachable *only if clamping holds*; `Money_Gt` is fail-safe if it doesn't (§ 2b).

---

## 1. SURFACE 1 — AM-4: partner_pending_pnl persist row + partner_pending_bitmap re-derive

### 1a. Session-finding verification (all VERIFY)

| Claim | Verified at | Status |
|---|---|---|
| `partner_pending_pnl` = NodeContext `Money` field | `CoreFrameworks/ControllerEventLoop.hpp:488` (WHY comment :479-487) | VERIFIED |
| `partner_pending_bitmap` = EventLoopState `uint16_t` | `ControllerEventLoop.hpp:901` (migration comment :893-900; v5.14.9.G) | VERIFIED |
| State machine in DrainPostFillOneCore | `:1815-1832` (`if (partial_on)` :1815; bit test :1816; merge `Money_Add` :1818; classify :1819-1826; clear pnl :1827 + bit :1828; park :1830-1831) | VERIFIED (directive said 1814-1831; comment line :1813-1814, body :1815-1832) |
| Park is ASSIGNMENT not add | `:1830` — `ctx.partner_pending_pnl = exit_net_pnl;` | VERIFIED — load-bearing for re-derive self-healing (§ 1f) |
| Init | `:1119` `state->partner_pending_bitmap = 0;` in `EventLoopState_Init`; `InitLegacy` delegates (:1176) | VERIFIED |
| Live boots flat | `CoreFrameworks/EngineSharded/Run.hpp:1065-1073` — `ShardedSnapshot_Load` gated `if (!live_trading)`; live path reconciles from exchange :1073-1108 | VERIFIED |
| No GUI/TUI consumers | repo-wide grep: zero hits in `GUI/`, `DataStream/EngineTUI.hpp`, `ShardedSnapshot.hpp` (TUI copy) for either field | VERIFIED |

### 1b. Complete reader/writer map (repo-wide, exhaustive)

**`partner_pending_pnl` (Money, per-node):**
- WRITE `Money_Zero()` — boot init via registry row `MemHeaders/NodeCtxInitRegistry.hpp:138` (`RST` column) walked by `_node_ctx_init_value_fields` :201-206 from `NODE_CTX_INIT_AUTOPOPULATE` (`ControllerEventLoop.hpp:1136-1138`).
- WRITE `Money_Zero()` — paper reset via `_node_ctx_reset_value_fields` (`NodeCtxInitRegistry.hpp:209-218`, RST presence dispatch) from `NODE_CTX_RESET_AUTOPOPULATE` (`:327-337`), called at `EngineSharded/Async.hpp:734-735`.
- WRITE `Money_Zero()` — pair-resolve clear `ControllerEventLoop.hpp:1827`.
- WRITE assign — park `ControllerEventLoop.hpp:1830`.
- READ — merge `ControllerEventLoop.hpp:1818`.
- READ — tests `tests/controller_test.cpp:9968,10017` (`Money_IsZero` asserts).
- **NOT persisted today** — absent from `FOREACH_NODE_PERSIST_FIELD` (`MemHeaders/NodeCtxPersistRegistry.hpp:67-103`) and from `NodeSnap` staging (`ShardedSnapshotPersist.hpp:356-389`). Not in summary.json (`NodeCtxSummaryFieldRegistry.hpp:171-198` — absent). Not replay-reconstructed (`ControllerEventLoop.hpp:1013-1058` — absent).

**`partner_pending_bitmap` (uint16_t, engine-level on EventLoopState):**
- WRITE 0 — `EventLoopState_Init` `ControllerEventLoop.hpp:1119`.
- WRITE `BITMAP_CLR` per-core — paper reset, `NodeCtxInitRegistry.hpp:336` (AUTOPOPULATE Layer 2, alongside the RST pnl clear — **reset moves both together, atomically-in-sequence on the producer thread**).
- WRITE `BITMAP_CLR` — pair resolve `:1828`; WRITE `BITMAP_SET` — park `:1831`.
- READ — `:1816`; tests `:9967,10016,10112,10184,10271,25282-25283`.
- No other writer/reader anywhere (incl. `ShardedSnapshot.hpp`, GUI, tools). `tools/node_persist_layout.py:13` and `PaperResetArchive.hpp:42` are comments only.

**RESET semantics answer (directive a):** operator paper reset clears BOTH — pnl via the RST registry walk, bit via the explicit `BITMAP_CLR` at `NodeCtxInitRegistry.hpp:336`. They cannot drift on reset (single AUTOPOPULATE macro). Note the reset runs on the **producer** thread (inside `EngineSharded_Async_FanOut`, `Async.hpp:590-768`) with only slow-paths parked on `paper_reset_in_progress` (:590-595) — the drainer is not documented as parked (pre-existing; § 4 H-6).

### 1c. Persist infrastructure state (what Steps 3-5 lands on)

- Persist SSoT = `FOREACH_NODE_PERSIST_FIELD`, **29 rows pinned** (`NodeCtxPersistRegistry.hpp:119-124`), 1944B/node at v10; ROW ORDER IS WIRE ORDER (:27-30). SAVE walk `ShardedSnapshotPersist.hpp:200-203`; READ walk :395-398 (STORAGE_KIND-only dispatch — the A2 invariant :146-149); COMMIT walk :457-464.
- `SHARDED_SNAPSHOT_VERSION 10u` at `ShardedSnapshotPersist.hpp:112` (plan cite ":109" has 3-line drift — cosmetic).
- The planned delta per `tools/node_persist_layout.py:11-14` + plan :61: **row SWAP — drop `node_dd_pct` (golden index 019, `tools/goldens/node_persist_layout.txt`), add `partner_pending_pnl`** (net 0 rows / 0 bytes — the D-302 triple-vacuity case the name-listing golden exists to catch). Forcing chain on the commit: `node_persist_layout.py` diff (currently GREEN, 46 flattened rows) → `--bless` via D-394 TTY; paired-bump rule in `check_identifier_retirement.py` REDs unless version→11 rides the same commit; byte-golden `tests/sharded_snapshot_v10_golden.hpp` regen/RENAME per the `==29` static_assert text (:119-124).
- `node_dd_pct` drop is SAFE: display field "recomputed each rebuild" (`ControllerEventLoop.hpp:532`); its restore is overwritten on the first slow-path cycle.
- Staging edits required: `NodeSnap` (`ShardedSnapshotPersist.hpp:371`) drops `node_dd_pct`, gains `partner_pending_pnl` (NodeSnap IS the hand-kept DECLARE view — names must match row NAMEs, :352-355).

### 1d. Downstream consumers of node_wins / node_losses / node_gross_wins / node_gross_losses (directive b)

Writers (for completeness): paired classify `:1820-1825`; unpaired leg-A `:1839-1846`; legacy mode-0 OnEvent `:2242-2243` (test-only in production sharded — mode-1 returns at `:2165`); event-log replay `:1053-1055` (per-LEG, **no pairing** — § 3 MED-3).

Readers — ALL display/summary plane, ZERO decision plane:
1. TUI/GUI snapshot copy: aggregation `ShardedSnapshot.hpp:418-421` → `snap->wins/losses/win_rate/avg_win/avg_loss/profit_factor/expectancy` `:864-886`; per-node copy `:496-497` → GUI Per-Core panel.
2. GUI direct: `GUI/DashboardPanels.hpp:1198-1202` (W/L + win%).
3. summary.json: per-core rows `MemHeaders/NodeCtxSummaryFieldRegistry.hpp:187-191`; per-strategy aggregation `:305-308` (paper-reset archive via `Summary_WriteJson`, `Async.hpp:699`).
4. Persist rows `NodeCtxPersistRegistry.hpp:80-83`.
5. Health log line `ControllerEventLoop.hpp:1665`.

**NOT consumers:** bandit reward uses `exit_net_pnl` (buy-side `:1936-1944`; exit-side `:1999-2003,2017`); ConfidenceScorer uses `oms->last_realized_return[slot]` (`:1848,1858`); pnl_feeder uses `realized` (`:1923`); no read in `Strategies/`, `ML_Headers/`, `Backtest/` (grep-zero).

**Answer:** a merge-with-zero on an orphan leg perturbs exactly **one W/L tally + one gross-bucket add** in display/summary stats — and with pnl=0 the classification (`total_net = 0 + exit_net`) and gross magnitude are *correct* for a single-leg trade. No capital, no reward, no model-feedback consumer is touched.

### 1e. Invariant/test coverage (directive c)

- `tests/controller_test.cpp` F-018 (:9866-10030): asserts the RESOLVED joint state only — "bit CLEARED + pnl==0" `:9966-9968` (case L), `:10015-10017` (case W). v4.7.21 suite: cleared-after-pair `:10110-10112`, never-set-when-partials-off `:10184`, backtest-driver parity `:10269-10271`. Default-zero `:25282-25283`.
- **GAP:** no test pins the PARKED intermediate (bit=1 ∧ pnl==legA-net after first exit only) — both legs close within one `DrainPostFill` call in every fixture. AM-4's re-derive premise is exactly that intermediate; a Save→Load round-trip fixture of the parked state is the missing coverage (§ 5 OQ-2).

### 1f. Load-side re-derive: insertion point, ordering, soundness (directive d)

**Exact insertion point:** `ShardedSnapshotPersist.hpp`, inside `ShardedSnapshot_Load`, AFTER the re-activation walk + its log (`:493-556` walk, `:557-562` log), BEFORE the success log/`return 1` (`:564-566`).
- Data dependencies: `state->oms->portfolio.active_bitmap` (committed at `:406`), `partial_exit_enabled` (function param, geometry-gated equal to the file's toggle by the refuse-load check `:311-330`), `state->registered_count` (validated `:303-308`). All available from `:406` onward.
- **Ordering hazard vs the finalizer: NONE.** The `:495-556` walk writes only ExecutionCore hot mirrors (`:544-554`) and never touches `active_bitmap`. Placing the re-derive before OR after the finalizer is byte-equivalent; after (as planned) is cleanest.
- The finalizer's `continue` guards (`:500` node out of range, `:502` null core) can leave a bitmap-active slot un-re-activated; an XOR bit derived for such a node is inert (its `DrainWithSubmit` skips on null core, `Async.hpp:827-828`).
- Form: gate on `partial_exit_enabled`; whole-value ASSIGNMENT (not OR) over nodes `0..registered_count-1`; under partials `registered_count ≤ 8` so `2N+1 ≤ 15` (leg-slot geometry per `Sharded_SlotNode`, fwd-decl `ControllerEventLoop.hpp:995`, same mapping the finalizer uses at `:498`). `partial_on` source at the consumer (`ControllerEventLoop.hpp:1640`) is the same `oms_state_flags` bit as the loader param source (`Run.hpp:1070`) — no flag-source skew.

**Soundness walk (every reachable pre-snapshot state; entry gate `can_enter = ~(active|active_b)` at `ExecutionCore.hpp:602-603` forbids re-entry while any leg is open, so no other states exist):**

| Pre-snapshot truth | active(2N),active(2N+1) | XOR bit | persisted pnl | Post-restore behavior | Verdict |
|---|---|---|---|---|---|
| Both legs open (fresh pair) | 1,1 | 0 | 0 | park-then-merge as normal | CORRECT |
| Leg A closed, parked; B open | 0,1 | 1 | parked net | B's exit merges parked+net | CORRECT (the AM-4 payoff) |
| Pair resolved; flat | 0,0 | 0 | 0 | fresh | CORRECT |
| Orphan single leg open (partner never opened) | 1,0 or 0,1 | 1 | 0 | exit merges 0+net → one correct W/L | CORRECT (semantic conflation "never-opened ≡ closed" is benign because pnl=0) |
| Stale pnl≠0 with bit=0 (tear: park captured, close not) | 1,1 | 0 | stale | next park OVERWRITES (`:1830` assignment) | SELF-HEALS |
| bit=1 + wrong pnl (tear: close captured in Phase A, park not yet in Phase A.5) | 0,1 | 1 | stale/0 | merge with wrong magnitude → 1 mis-magnitude gross bucket | **the one bad combo** — § 4 H-3 |

### 1g. Plan-carried open question ANSWERED: legs are NOT atomic (flag to orchestrator)

The subplan carries "AM-4's atomic-legs evidence RE-LOCATE (the old `:1120` site moved)" (:47) and conditions persist-both on "can a sharded leg open without its partner?" (:216). **Answer: YES, four structural orphan sources exist at HEAD:**
1. Hot-path ring-full, leg B accepted-lost by design: `ExecutionCore.hpp:729-734` — *"If leg A succeeded but leg B failed … accept losing that one leg this trade."*
2. Drainer qty-zero guard skip: `Async.hpp:888` (pct exactly 0.0/1.0 today; any leg rounding to Money-zero post-fix).
3. OMS order-table-full drop of one leg: `OrderManager.hpp:1095-1101`.
4. Submit-queue-full: `OMS_PushSubmit` returns false (`OrderManager.hpp:1279-1286`) and the return is DISCARDED at `Async.hpp:956`.

**However the plan's "if yes → persist-both fallback" conditional does NOT follow:** § 1f row 4 shows the XOR re-derive handles orphans *benignly-correctly* (merge-with-zero), and persist-both narrows but does not close the tear window (the save could still land between `:1830` and `:1831`). Recommendation § 6.

---

## 2. SURFACE 2 — F-096: Money leg-split (`EngineSharded/Async.hpp:853-932`)

### 2a. `order_qty_d` consumer enumeration (directive a) — CLOSED SET

Writes: declare `:853`; exit-read `:859-860` (`Money_ToDouble(positions[portfolio_slot].quantity)`); entry legA `:877` (`full_qty * Money_ToDouble(partial_pct)`); entry legB `:879` (`full_qty * (1.0 - Money_ToDouble(partial_pct))`); no-partials `:881`; with `full_qty` itself from `:872` (`Money_ToDouble(intended_qty)`).
Reads: **exactly two** — the guard `:888` (`(is_entry || is_exit) && order_qty_d > 0.0`, gating the ENTIRE submit block `:888-983` incl. TP2 calc, ctor, `OMS_PushSubmit`, prediction stamp `:964-968`, entry stamps `:972-982`) and the ctor payload `:926` (`Money{ money_from_double_payload(order_qty_d) }`). `EventLoop_OnEvent` at `:885` does NOT consume it (and is a mode-1 near-noop in production — early return `ControllerEventLoop.hpp:2159-2165`). Nothing else between `:853` and `:932` touches it.

### 2b. Guard replacement (directive a cont.) — and a live bug the fix must close deliberately

- **Replacement: `Money_Gt(leg_qty, Money_Zero())` per leg — NOT `!Money_IsZero`.** `partial_exit_pct` clamp is `DBL(0.5, 0.0, 1.0)` (`CoreFrameworks/CfgFieldRegistry.hpp:760`); within-clamp, `legB = Money_Sub(intended, legA)` ≥ 0 always (Money_Mul of pct ≤ 1.0 cannot exceed the operand: `round(q·p/1e8) ≤ q` for `p ≤ 1e8`). But if an unclamped value ever reached the drainer, `!Money_IsZero` would submit a NEGATIVE-qty order; `Money_Gt` fail-safes to skip. `Money_IsZero`/`Money_Gt` at `FixedPointN.hpp:2242` ff.
- **Leg-skip semantics — TODAY'S LIVE MISMATCH (new finding, HIGH):** the guard checks the *double* (`> 0.0`) but the submitted qty is `llround`-rounded at `:926`/`FixedPointN.hpp:2308-2313`. A leg with true qty in `(0, 0.5e-8)` (double positive → guard passes; Money rounds to 0) submits a **zero-qty order**. OrderManager has no zero-qty defense (`OrderManager.hpp:1061-1129` books `requested_qty = qty` verbatim at `:1123`) → paper opens a 0-qty position → on its exit event, the exit-side read `:859-860` yields 0.0 → guard `:888` skips the SELL **forever** → hot mirror clears on event-push (`ExecutionCore.hpp:736-737`) but `portfolio.active_bitmap` never clears → **un-closeable zombie slot + permanent bitmap DRIFT + the partner XOR stuck at 1**. The Money fix (guard on the actual Money leg) eliminates this class: sub-unit legs SKIP instead of zombifying. This flips those edges from "zombie" to "orphan-leg pairing wobble" — strictly better, and the AM-4 re-derive makes the restore side of that wobble correct.
- Population change: today's skip set is `{double exactly ≤ 0.0}` = pct ∈ {0.0, 1.0}; post-fix it is `{Money leg == 0}` ⊇ that (adds `intended_qty·pct < 0.5e-8` and half-even ties to 0). At directive-typical scales (qty 1e-3..1e2 BTC, pct 0.25-0.75) leg qtys are ≥ 2.5e-4 BTC = 25,000 units — the widened set is unreachable in normal operation.

### 2c. Rounding semantics delta (directive b) — NOT bytewise-identical; quantified

- **New path:** `legA = Money_Mul(intended_qty, partial_pct)` — exact 128-bit integer product, ONE half-even reduce at 1e-8 (`Money_Mul` `FixedPointN.hpp:1877-1890`; `money_round_half_even` `:1839-1847` — real ties exist since d=10^8 is even; saturate + `MONEY_FLAG_OVERFLOW` sticky, unreachable at qty×pct scales). `legB = Money_Sub(intended, legA)` — exact by domain (`:1963,1952-1954`). Conservation `legA+legB == intended` **exact by construction**.
- **Old path:** TWO inexact `Money_ToDouble` conversions (`/1e8` binary-inexact even for small values, `:2296`) → double multiply → `llround(d*1e8)` = **half-away-from-zero** (`:2308-2313`). LegB additionally computed independently as `full·(1.0-pct)` → conservation only within ±1 unit.
- **Divergence is real and common, bounded at 1 unit (1e-8 BTC):** for pct = 0.25 (units/4), every `qty_units ≡ 2 (mod 4)` lands a genuine `.5` tie — e.g. qty `0.10000002` × 0.25: true 2500000.5 units → half-even 2500000 vs llround 2500001. pct = 0.5/0.75 tie similarly on parity classes. Double representation error can additionally flip which side of a boundary the old path saw. **Consequence: leg-A entry qtys (and thus fills, fees, pnl traces) shift by ULPs after the fix — do NOT gate this change on byte-identical paper traces; the plan's determinism gate (Save→Load byte-compare, subplan BLK-4) is self-consistent post-change and unaffected.** Economically ≤ $0.001/leg at $100k/BTC.
- Downstream re-quantization: none in paper (Submit books `cmd.qty` verbatim); live venue LOT_SIZE truncation only at the API boundary (`DataStream/BinanceOrderAPI.hpp:242-246`) — conservation-vs-intended breaks at the venue regardless (inherent).

### 2d. Exit-side (directive c) — CONFIRMED

`:854-860` reads `positions[portfolio_slot].quantity` (already Money) → `Money_ToDouble` → back through the payload bridge at `:926`. Exit legs need NO split — the fix carries the slot's Money quantity straight into the `SubmitCommand` qty (ctor takes `Money q`, `OrderManager.hpp:202`). Round-trip today is provably exact for `quantity < 2^51` units (~2.25e7 BTC; total relative error ≤ 2·2^-53 ⇒ |Δ| < 0.5 unit) — so the exit-side change is behavior-neutral for every realistic qty; it removes a theoretical-magnitude loss and, more importantly, an H4 contract violation.

### 2e. Payload-bridge round-trip today (directive d)

`money_from_double_payload` is documented as "the cfg-PAYLOAD bridge ONLY (registry default/clamp literals, <=8dp by authoring convention) — NOT a general money ingress" (`FixedPointN.hpp:2302,2319-2322`). The `:926` use feeds it a *computed double product* — outside contract. Exit-side: exact round-trip for realistic magnitudes (§ 2d) — **no live drift today on exits**. Entry-side: genuinely double-valued (not a round-trip of a representable Money) — the last unit is double-arithmetic-determined; deterministic (IEEE) but not equal to the decimal half-even result. The fix deletes both uses of the bridge in this function.

### 2f. Other double-on-money-path residue, `:820-960` sweep (directive e)

Complete list of doubles in range: `:853` (`order_qty_d`), `:859` (`Money_ToDouble` exit), `:872` (`full_qty`), `:877/:879` (double mul + the `1.0 - pct` double subtract), `:881`, `:888` (`> 0.0`), `:926` (payload bridge). **All are the F-096 core — one coherent sweep removes every one.** Everything else in range is already Money: `partial_pct` resolve `:874-875`, TP2 chain `:898-916` (`Money_Sub/Mul/Add`), ctor optionals `:929-932`, `tp_pct` resolve `:946-954`. No stragglers. (Out of range but same file: `mtm_price` via the `last_price` atomic-double vehicle at `:404-405` is the S-8 item riding P3 — separately homed, do not fold.)

---

## 3. FINDINGS (accounting-audit format)

**Summary: CRITICAL 0 · HIGH 2 · MEDIUM 3 · LOW 3**

- **[HIGH-1] F-096 H4 violation + out-of-contract money ingress** (`Async.hpp:859,872,877-881,926`; contract at `FixedPointN.hpp:2302,2319-2322`). Category 4/5 (H4 / lossy conversion). Class: TD-167. Fix = the decided Phase-E shape (legA `Money_Mul`, legB `Money_Sub`, exit = slot qty). CI: `check_latency_path_conformance.py` H4 lane does not cover the drainer; the conservation assert (subplan :115,:192) is the guard.
- **[HIGH-2] Guard/payload rounding mismatch → zero-qty zombie position** (`Async.hpp:888` vs `:926`; no OMS defense `OrderManager.hpp:1123`; zombie mechanics § 2b). Category 6 (position/balance atomicity). Silent in W/L, bitmap-DRIFT visible. Closed for free by the F-096 fix **iff** the guard moves to `Money_Gt` on the actual submitted Money value.
- **[MED-1] Non-atomic legs — 4 orphan sources** (`ExecutionCore.hpp:729-734`; `Async.hpp:888`; `OrderManager.hpp:1095-1101`; ignored push `Async.hpp:956` + `OrderManager.hpp:1279-1286`). Resolves the plan's carried A2 question (§ 1g); orphans are benign under the XOR re-derive but cause the pre-existing live-session off-by-one pairing (next trade's first exit merges with the stale park). Cross-trade contamination of ONE W/L tally per orphan; display-plane only (§ 1d).
- **[MED-2] Torn producer-thread snapshot capture** — periodic save on producer (`Async.hpp:446-452`; thread identity per `:453-455` + `fan_out` call sites `Run.hpp:1407,1432`) vs drainer writes (drainer thread `Run.hpp:1539-1590`; Phase A close `:1587` vs A.5 park `:1588`). Bad combo: bit=1 + un-parked pnl (§ 1f last row). Also raw 16B Money tear on the pnl fwrite itself. Same documented class as the balance tear (`Async.hpp:453-467`); `.E.1` aggregator scope per `CoreFrameworks/CLAUDE.md` cross-thread-multiword rule. AM-4 should NOT try to fix this; it should document acceptance (paper-only, μs window, display-stat blast radius).
- **[MED-3] Event-log replay path counts W/L per-LEG with no pairing and no partner state** (`ControllerEventLoop.hpp:1053-1055`; fn `:1013-1058`) — the OTHER restore mechanism diverges from live pairing semantics under `partial_on`. AM-4 covers only the snapshot path. Track (TECH_DEBT or fold into the replay path's owning plan) — do not silently absorb.
- **[LOW-1] Merge-with-zero orphan blast radius** = 1 W/L tally + 1 gross-bucket in GUI/TUI/summary.json only (§ 1d). No action beyond the re-derive.
- **[LOW-2] `node_dd_pct` persist row is dead weight** (restored value overwritten next rebuild, `ControllerEventLoop.hpp:532`) — confirms the planned drop is safe.
- **[LOW-3] Drainer reads `state.nodes[slot].intended_qty` (16B Money) bare while the slow path writes it** (`Async.hpp:872` read; writer `ControllerEventLoop.hpp:3461`). Pre-existing torn-read class (`.E.1` aggregator); ALSO means the two legs' adjacent pops can straddle a rebuild and see different `intended_qty` — conservation-by-construction holds per-read-pair only under stable `intended_qty` (the practical case: both entry events are pushed in one hot tick, `ExecutionCore.hpp:653-707`, and popped in consecutive `i`-loop iterations `Async.hpp:829-831`). Phrase the F-096 runtime conservation assert accordingly (§ 5 OQ-3).

---

## 4. HAZARDS — what the implementer must not break

- **H-1 (wire discipline):** the swap is a wire change — `SHARDED_SNAPSHOT_VERSION` 10→11 (`ShardedSnapshotPersist.hpp:112`), golden regen/RENAME `tests/sharded_snapshot_v10_golden.hpp`, `node_persist_layout.py --bless`, `==29` count-pin update, `NodeSnap` staging edit — ALL in the SAME commit (paired-bump rule in `check_identifier_retirement.py`; H21/H9). v10 tombstones, never reuses.
- **H-2 (A2 READ invariant):** any new row's READ projection dispatches on STORAGE_KIND ONLY (`NodeCtxPersistRegistry.hpp:146-149`); `partner_pending_pnl` is a plain `SCALAR/COMMIT` — do not invent a conditional read.
- **H-3 (re-derive form):** gate on `partial_exit_enabled`; ASSIGN the whole bitmap; place after `:556`; do NOT re-derive from anything but `portfolio.active_bitmap`. Do not attempt to "fix" the torn-capture combo here (MED-2) — that is `.E.1` aggregator territory; a partial fix (e.g. clearing pnl when bit=0) would break the assignment-park self-heal.
- **H-4 (park stays ASSIGNMENT):** `:1830` overwrite semantics is load-bearing for the re-derive's self-healing (§ 1f row 5). Never change it to `Money_Add`.
- **H-5 (guard is `Money_Gt`, per-leg, on the submitted value):** and the skip must remain BEFORE the entire `:888-983` block (prediction/entry stamps must not fire for a skipped leg — today they don't; preserve that).
- **H-6 (reset coherence):** paper reset already clears both fields together (`NodeCtxInitRegistry.hpp:333,336`); the persist row changes nothing there, but any new RST row must NOT be added for the bitmap (it is engine-level, cleared per-core by the macro — a per-node registry row would be a category error).
- **H-7 (no byte-parity claim for F-096):** leg-A qtys shift by ULPs (§ 2c). The acceptance oracle is the conservation assert + Save→Load byte-compare, NOT old-vs-new trace equality.
- **H-8 (F-018 stays green):** F-018 bypasses the split structurally (`tests/controller_test.cpp:9885-9888` — Money-literal legs through `OrderManager_HandleFill`); nothing in Steps 3-5 should touch its goldens. If F-018 moves, the change leaked outside the mapped surface.

## 5. OPEN QUESTIONS (for orchestrator/operator)

- **OQ-1 — row position for `partner_pending_pnl`:** in-place at old index 019 (kill-switch cluster — semantically odd) vs appended to the P&L cluster after `node_gross_losses` (row 13/14 region, matching `NodeCtxInitRegistry.hpp:137-141` order). v11 is a fresh wire either way; semantic grouping costs nothing extra. Recommend the P&L-cluster position; pure taste call, flag for the operator.
- **OQ-2 — test shape:** the plan's "mid-pair reopen fixture" (:216) is IMPOSSIBLE — re-entry while any leg is open is gated off (`ExecutionCore.hpp:602-603`). Substitute a **mid-pair SAVE→LOAD fixture**: park leg A (single exit), `ShardedSnapshot_Save`, fresh state, `Load`, assert bit re-derived 1 + pnl committed, then leg-B exit classifies the pair. Plus an orphan fixture (bit=1, pnl=0 → merge-with-zero = 1 correct W/L).
- **OQ-3 — conservation assert phrasing:** runtime `Money_Eq(Money_Add(legA, legB), intended)` can only be asserted where both legs derive from ONE `intended_qty` read (LOW-3). Options: assert inside the leg-B branch recomputing legA from the same local read; or a paper-fill-level invariant. Needs a decision before Step 5 coding.
- **OQ-4 — live-session orphan off-by-one (MED-1):** out of AM-4 scope, but now evidence-backed. Home it (TECH_DEBT with the four-source enumeration, or the `.E.1` plan) rather than leave unhomed.

## 6. RECOMMENDATION + option matrix

**AM-4 — recommend Option A (the decided D-291 shape), now evidence-confirmed:**

| Option | Shape | Verdict |
|---|---|---|
| **A (decided)** | persist pnl row (SCALAR/COMMIT) + XOR re-derive of the bitmap post-finalizer | **SOUND across the full state space (§ 1f); orphans benign; self-healing via assignment-park. RECOMMEND.** |
| B (plan fallback) | persist both (bitmap as an engine-level wire row) | Not triggered: non-atomicity does NOT break A; narrower but non-zero tear window (save between `:1830`/`:1831`); needs a new engine-level row kind the per-node registry doesn't model. Reject. |
| C (novel alternative considered) | derive pnl too — reconstruct the closed leg's net from the event log for XOR pairs | Rejected: event log truncates on paper reset (`Async.hpp:756`), replay path lacks pairing (MED-3), and it re-derives money from a lossier source; pnl is genuinely non-derivable from the snapshot alone. |
| D (novel alternative considered) | stash parked pnl in the surviving leg's `Position` (rides the existing positions block) | Rejected: bloats the capital-bearing 16-slot `Position` wire array for a display stat; larger H9/H12 cascade than one per-node row; disproportionate. |

**F-096 — recommend the decided Phase-E shape with the `Money_Gt` guard:** `legA = Money_Mul(intended_qty, partial_pct)` on LEG_A; `legB = Money_Sub(intended_qty, Money_Mul(intended_qty, partial_pct))` on LEG_B (recompute-from-same-formula; both events carry the same locals); exit = slot `quantity` verbatim; no-partials = `intended_qty` verbatim; per-leg `Money_Gt(qty, Money_Zero())` guard. Novel alternative considered — `legB = Money_Mul(intended, Money_Sub(one, pct))`: rejected, reintroduces the two-independent-roundings conservation leak this fix exists to close.

## 7. Mechanical tool baseline at HEAD (all GREEN — any post-change RED is the ship's delta)

- `tools/node_persist_layout.py` → rc 0, "46 flattened wire rows match the frozen golden".
- `tools/check_identifier_retirement.py` → rc 0, 48 identifiers GREEN (advisory: 2 un-recorded wire-consts `ROLLING_IC_MAX_WINDOW=64`, `MAX_WINDOW=8`).
- `tools/check_money_gross_single_source.py` → rc 0 (D-190 SSoT clean).
- `tools/check_struct_alignment.py` → rc 0, all 4 byte-serialized types size-pinned (13 advisory alignof locks).

## 8. Spots most worth an adversarial refute (for the paired a-class)

1. **The soundness table (§ 1f)** — try to construct a reachable state outside it. Sharpest attack surfaces: the manual-close path (`EngineSharded_SlowPath_DrainManualCloses`, `Run.hpp:1576` — does it route exits through `DrainPostFill`'s pairing, and can it close a leg in a way that skews the XOR?), and flatten/emergency paths (`OMS_FlattenAll`) closing both legs across cycles.
2. **The merge-with-zero-is-correct claim (§ 1d/1f row 4)** — verify `Money_Gt(total_net, Zero)` with `total_net == exit_net` yields the same classification the unpaired leg-A branch (`:1839-1846`) would; and that gross-bucket magnitude parity holds for the negative case (`Money_Negate` at `:1825`).
3. **The zero-qty zombie mechanics (§ 2b / HIGH-2)** — I traced it structurally (hot mirror clear `ExecutionCore.hpp:736-737`, portfolio bit only cleared by Phase-A close that never comes) but did not run a repro; also check whether the paper synthetic-fill chokepoint (A9, `OrderManager_Submit` fill path) has any zero-qty rejection I missed.
4. **The tie-frequency quantification (§ 2c)** — the "qty_units ≡ 2 (mod 4) at pct=0.25" claim assumes the OLD double path also lands exactly on the tie; double representation error may move it off `.5` in either direction, changing which side diverges (the *existence* of 1-unit divergence stands; the *frequency* argument is refutable).
5. **The exit-side round-trip exactness bound (§ 2d, `v < 2^51`)** — paper napkin math; refute with a brute scan of representable qtys if the a-class wants a mechanical proof.
6. **Insertion-point independence (§ 1f)** — confirm nothing between `:406` and `:566` mutates `active_bitmap` (I verified by read; a grep-anchored recheck of `Portfolio_` calls inside `ShardedSnapshot_Load` is cheap).

**Key files:** `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerEventLoop.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ShardedSnapshotPersist.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeCtxPersistRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeCtxInitRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EngineSharded/Async.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EngineSharded/Run.hpp` · `/home/caramel/code/FoxML_Trader_v2/FixedPoint/FixedPointN.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ExecutionCore.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/OrderManager.hpp` · `/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeCtxSummaryFieldRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ShardedSnapshot.hpp` · `/home/caramel/code/FoxML_Trader_v2/tests/controller_test.cpp` · `/home/caramel/code/FoxML_Trader_v2/tools/node_persist_layout.py` · `/home/caramel/code/FoxML_Trader_v2/tools/goldens/node_persist_layout.txt`
