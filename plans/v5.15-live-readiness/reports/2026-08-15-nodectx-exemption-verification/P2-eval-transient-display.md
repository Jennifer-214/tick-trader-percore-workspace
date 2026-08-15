---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: P-2 — NodeContext persist-exemption VERIFICATION, group 2/3: the EVAL-TRANSIENT / DISPLAY family
agent_class: i-class
delivered: 2026-08-15
ground: engine HEAD 564f099, branch feat/v5.15-live-readiness
headline: All 12 fields SAFE-UNPERSISTED — but TWO of the four offered reason categories are FALSE for the fields they most obviously fit (WALL_CLOCK refuted by last_entry_wall_us, whose loss WAS a real bug fixed by persisting a sibling; DISPLAY_ONLY refuted by last_exit_prediction, which fires a real MARKET_SELL). Verification also surfaced F-1, a live defect - strategy_halt_reason is reset 59 lines AFTER its producer, so 17 of 20 SHALT codes have been unobservable since the commit that created the channel (bc37c62, 2026-04-30)
operator_decision_owed: OQ-1 (F-1 — hoist the SHALT_OK reset above Strategy_BuildParameters; note halt_reason's reset must STAY, the two adjacent lines have opposite correct placements) · OQ-2 (F-2 — add intended_tp/sl/qty to the cross-thread-multiword spec's enumeration, or document a deliberate exemption) · OQ-3 (vocabulary — drop WALL_CLOCK, rename DISPLAY_ONLY to DISPLAY_SINK_ONLY with a machine-checkable reader list, adopt DERIVED_BEFORE_ARM + SUPERSEDED_BY_PERSISTED_SIBLING) · OQ-4 (add the write-ordering assertion to the guard — one comparison, would have caught F-1 on ship day) · OQ-5 (delete two dead functions + an unrendered snapshot field, or track)
sister_reports: P1-handles-lifecycle.md · P3-substructs.md
---

All verification complete. Working tree byte-identical; no probe left behind.

---

# P-2 — NodeContext persist-exemption VERIFICATION, group 2/3: the EVAL-TRANSIENT / DISPLAY family

**Ground:** engine `/home/caramel/code/FoxML_Trader_v2`, branch `feat/v5.15-live-readiness`, HEAD `564f099` (verified `git rev-parse`). Read-only; `git status` byte-identical to session start (4 pre-existing untracked operator files, nothing added). No probe binary was needed — every claim below is settled by clang record-layout, mechanical control-flow analysis, or the mechanical guards, and I say explicitly where a claim is analytic rather than executed.

**Headline:** all 12 fields are **SAFE-UNPERSISTED**, but **two of the four candidate reason categories you offered are FALSE for the fields they most obviously fit**, and the verification turned up **one live defect** (`strategy_halt_reason` is clobbered after the producer writes it — the SHALT display channel has been inert since birth, 2026-04-30) plus **three unenumerated instances of the codified torn-read class** sitting on `intended_tp/sl/qty`.

---

## 0. Method + corroboration

Offsets were derived **independently** of your table — `./tools/foxtag/foxtag fields tests/controller_test.cpp NodeContext` (clang `-fdump-record-layouts` behind the foxtag layout core). **49 members, `sizeof` 7168, `alignof` 64 — and all 12 offsets match your table exactly, 12/12.** That agreement is what licenses me to reason about the set as closed.

Control-flow dominance claims (write-dominates-read) were established by a **brace-depth + control-flow scan**, not by eye: for each pair I computed nesting depth at both lines and enumerated every `for`/`while`/`do`/`goto`/`return`/`break`/`continue` in the interval. Results are quoted inline.

**Mechanical tools run** (RC captured directly, no pipe):

| Tool | RC | Result |
|---|---|---|
| `tools/node_persist_layout.py` | 0 | GREEN — 46 flattened wire rows match the frozen golden |
| `tools/check_identifier_retirement.py` | 0 | GREEN — 48 persisted/wire identifiers match the ledger |
| `tools/check_meta_registry.py` | 0 | 68/68 registries enrolled; H15/H19 clean |
| `tools/check_capital_adversarial_audit.py` | 0 | OK |
| `foxtag layout` / `foxtag fields` | 0 | `NodeContext<64>` 7168B/align 64, 0 straddlers, 49 members |

**Every guard is green and not one of them can see any finding below.** Same meta-pattern the sister sweep reported.

**Scope bound that materially shrinks blast radius for all 12 (state it in the guard's docs):** `ShardedSnapshot_Load` has **exactly one production caller** — `CoreFrameworks/EngineSharded/Run.hpp:1069` — and it is gated `if (!live_trading)` at `Run.hpp:1065`. **Warm restart is a PAPER-MODE-ONLY path today.** Backtest never loads a snapshot (`grep` over `Backtest/` returns nothing). Live mode reconciles against the exchange instead.

---

## A. PER-FIELD VERDICT TABLE

| # | off | field | verdict | mechanism (my category) | the ONE citation that settles it |
|---|---|---|---|---|---|
| 1 | 2112 | `intended_tp` | **SAFE-UNPERSISTED** | `DERIVED_BEFORE_ARM` | write `ControllerEventLoop.hpp:3465` every full rebuild; the only capital consumer (`handle_buy_fill`) is unreachable until `permission=1`, granted only at `EngineCommon.hpp:809` — *after* the rebuild at `:621` |
| 2 | 2128 | `intended_sl` | **SAFE-UNPERSISTED** | `DERIVED_BEFORE_ARM` | `ControllerEventLoop.hpp:3466`; same gate |
| 3 | 2144 | `intended_qty` | **SAFE-UNPERSISTED** | `DERIVED_BEFORE_ARM` | `ControllerEventLoop.hpp:3467`; same gate |
| 4 | 2176 | `halt_reason` | **SAFE-UNPERSISTED** | `DERIVED_EACH_PASS` | unconditional `= HALT_OK` at `ControllerEventLoop.hpp:3116`, depth 2, dominating both reads (`:3182`, `:3196`) and the log read (`:3483`) |
| 5 | 2177 | `strategy_halt_reason` | **SAFE-UNPERSISTED** | `DERIVED_EACH_PASS` (over-strongly — see F-1) | unconditional `= SHALT_OK` at `ControllerEventLoop.hpp:3120` |
| 6 | 2208 | `last_confidence_factor` | **SAFE-UNPERSISTED** | `DISPLAY_SINK_ONLY` | written `StrategyParameters.hpp:1717`; read at `ShardedSnapshot.hpp:591` + `:598` and **nowhere else in the tree** |
| 7 | 2216 | `last_exit_prediction` | **SAFE-UNPERSISTED** | `DERIVED_EACH_PASS` | reset `= 0.0` at `ControllerEventLoop.hpp:3019`, before the exec read at `EngineCommon.hpp:669` in the same slow-path body |
| 8 | 2224 | `last_exit_dominant_horizon` | **SAFE-UNPERSISTED** | `DERIVED_EACH_PASS` | reset `= -1` at `ControllerEventLoop.hpp:3020` |
| 9 | 2228 | `last_buy_dominant_horizon` | **SAFE-UNPERSISTED** | `DERIVED_EACH_PASS` | reset `= -1` at `ControllerEventLoop.hpp:3026` |
| 10 | 2232 | `last_barrier_mode_used` | **SAFE-UNPERSISTED** | `DERIVED_EACH_PASS` | reset `= 0` at `ControllerEventLoop.hpp:3027` |
| 11 | 2280 | `last_entry_wall_us` | **SAFE-UNPERSISTED** | `SUPERSEDED_BY_PERSISTED_SIBLING` — **NOT `WALL_CLOCK`** | `ShardedSnapshot.hpp:286-291`: the primary source is `Position::entry_timestamp_us`, which **IS** persisted (raw Position dump, `ShardedSnapshotPersist.hpp:191`) |
| 12 | 2432 | `node_dd_pct` | **SAFE-UNPERSISTED** for the kill switch; **display claim is overstated** | `DERIVED_EACH_PASS` (kill-eval) + a bounded display window | write `ControllerEventLoop.hpp:3284`/`:3287` (both arms), reads `:3298`/`:3302`, same depth-4 block, no control flow between |

**Hypotheses the code REFUTED (this is the signal you asked for):**

- ❌ **`WALL_CLOCK` for `last_entry_wall_us`.** "A host-clock stamp meaningless across a restart" is **exactly backwards** here, and the codebase proves it: `ShardedSnapshot.hpp:283-285` — *"Pre-fix: hold display always read `last_entry_wall_us`, which reset to 0 on every restart → Hold column showed '0m' forever for positions loaded from snapshot."* The stamp was **meaningful** across a restart and its loss was a real (display) bug. v5.11.65 fixed it not by declaring the field transient but by **persisting a sibling**. If the CI guard accepts `WALL_CLOCK` as the reason, it enshrines a false premise and would green-light dropping a wall-clock field that has *no* persisted sibling.
- ❌ **`DISPLAY_ONLY` for `last_exit_prediction`.** It looks like an ML observability field and rides `PerNodeSnap.ml_last_exit_prediction`. It is **not** display-only: `EngineCommon.hpp:668-671` reads it as the predicate for firing a real `OMS_PushExitForSlot` MARKET_SELL. It is safe for a completely different reason (reset to `0.0` at `ControllerEventLoop.hpp:3019` earlier in the same pass).
- ❌ **The sister S1 report's claim that `last_confidence_factor` "feeds ML sizing (`ControllerEventLoop.hpp:3006`)".** `:3006` wires a **sink pointer only**. Sizing uses the function-local `factor` at `StrategyParameters.hpp:1743`; nothing ever reads the NodeContext field back into an execution path. See § E-1.
- ❌ **"`EventLoop_OnEvent` is the production `intended_*` reader."** It is not: `ControllerEventLoop.hpp:2165-2171` early-returns in mode-1, and mode-1 is the compiled default (`ControllerConfig.hpp:2330`). The production readers are on the **drainer thread** in `EngineSharded/Async.hpp`.

---

## B. THE TWO TRAPS, ANSWERED

### B.1 `node_dd_pct` — the D-420 claim is TRUE for the kill switch, OVERSTATED as written

The registry comment (`MemHeaders/NodeCtxPersistRegistry.hpp:94-95`) says: *"eval-transient display field, recomputed from `node_peak_balance` before every read in the same kill-eval pass — dead wire weight."*

**Every read of `NodeContext::node_dd_pct`, exhaustively (grep over all engine dirs + tests + tools):**

| # | site | kind | preceded by the recompute in the same pass? |
|---|---|---|---|
| R1 | `ControllerEventLoop.hpp:3298` | **kill trip evaluation** (capital control) | **YES** — proven below |
| R2 | `ControllerEventLoop.hpp:3302` | trip log (`dd=%.2f%%`) | **YES** — inside the `:3298` trip branch |
| R3 | `ShardedSnapshot.hpp:512` | TUI/GUI snapshot publish (different thread, different cadence) | **NO** |
| R4 | `MemHeaders/NodeCtxSummaryFieldRegistry.hpp:195` → `Summary_EmitPerCoreEntry` (`:239`) → `PaperResetArchive.hpp:224` | operator summary JSON at paper reset | **NO** |
| — | `GUI/DashboardPanels.hpp:1142`, `:2186`, `:2202` | ImGui render — reads `pc->node_dd_pct`, the **snapshot** `double`, not NodeContext | n/a |
| — | `tests/controller_test.cpp:6102`, `:6117`, `:6569` | test assertions | n/a |

**The dominance proof for R1/R2 (the load-bearing one).** `ControllerEventLoop.hpp:3281-3288`:

```text
Money drop = Money_Sub(state->nodes[slot].node_peak_balance, current_value);
if (Money_Gt(drop, Money_Zero()) &&
    Money_Gt(state->nodes[slot].node_peak_balance, Money_Zero())) {
    state->nodes[slot].node_dd_pct = Money_Div(drop,
        state->nodes[slot].node_peak_balance);
} else {
    state->nodes[slot].node_dd_pct = Money_Zero();
}
```

**Both arms assign** — there is no path through `:3282` that leaves the field unwritten. Mechanical check: `:3284`/`:3287` and `:3298` are all at **brace depth 4** inside the same `{ }` scope opened at `:3250`; the only loop constructs anywhere in `EventLoop_RebuildOneCore` (2603–3516) are at `:2899` and `:3262`, neither of which spans `3284→3298`; no `goto`/`return`/`break`/`continue` in the interval.

**And the recompute's inputs are all persisted**, so the reconstruction is genuine rather than a zero:
- `node_peak_balance` — row `NodeCtxPersistRegistry.hpp:96` (COMMIT)
- `allocated_balance` — row `:73` (COMMIT)
- `node_realized` — row `:80` (COMMIT)
- `Portfolio.positions[]` (the unrealized MTM walk, `:3262-3268`) — raw dump `ShardedSnapshotPersist.hpp:191`, committed `:416`

**And the first post-load rebuild cannot be lazily skipped.** The lazy-skip early return at `:2669` requires `sst_lazy->us_at_last_rebuild != 0` (`:2646`); `NodeSlowState_Init` sets it to `0` at `ControllerEventLoop.hpp:200` with the comment *"us_at_last_rebuild=0 → time-bound predicate fires"*, `slow_state` is freshly heap-allocated at boot (`NodeCtxInitRegistry.hpp:224-236`) and is **not** on the wire. So pass #1 after a load is always a full rebuild.

**And the kill STATE itself survives independently of dd:** `KILL_TRIPPED` is a persisted BIT row (`NodeCtxPersistRegistry.hpp:97`) and `node_ks_trips_total` a persisted scalar (`:99`), so a killed node comes back killed and re-zero-gates at `:3325-3327` in the first rebuild.

**Verdict: SAFE-UNPERSISTED. The capital control is sound. I found zero reads of `node_dd_pct` on an execution or risk path that are not dominated by the recompute.**

**But the comment as written is wrong about R3/R4 and should be corrected** (SUBAGENT_ARMING § 2.5 — code is truth, and here the code is *narrower* than the comment):

> ⚠ **F-3 — LOW — the "before every read" claim covers 2 of 4 reads.** Between `ShardedSnapshot_Load` (`Run.hpp:1069`) and the first slow-path rebuild, the TUI/GUI publish at `ShardedSnapshot.hpp:512` reads `node_dd_pct == 0` for a node that genuinely has drawdown. `GUI/DashboardPanels.hpp:2186` then renders `approx_current = peak × (1 − 0) = peak`, i.e. the Risk panel shows the node **at its peak**. The window is one slow-path cycle (bounded; slow-path threads are spawned at `Run.hpp:1712` for **all** `num_nodes` with no `STRATEGY_NONE` skip, and `EngineCommon_SlowPathCycleOneCore` runs the full body for every node). `PaperResetArchive.hpp:224` has the same exposure if a reset lands in that window. **Suggested wording:** *"eval-transient — recomputed from the persisted `node_peak_balance` at `ControllerEventLoop.hpp:3284` and read only at `:3298`/`:3302` in the same kill-eval pass, so no capital decision ever sees a stale value. The TUI publish (`ShardedSnapshot.hpp:512`) and the summary emit read it out-of-pass and display 0 for one cycle after a warm restart — display-only, accepted."*

**Guard-surface gap worth noting:** `tests/controller_test.cpp:6569-6570` pins the **negative** ("fresh-state zero survives load") and `:6095-6125` pins the recompute in isolation — but **no test asserts the end-to-end `load → rebuild → dd correct` chain**, which is the property the exemption actually rests on.

### B.2 `halt_reason` / `strategy_halt_reason` — the node re-halts, and `halt_reason` is not the mechanism

**Direct answer: yes, it re-halts, and it does so before it can trade.** The trace, not the assumption:

1. `halt_reason` is a **label**, not the halt. The halt is `zero_gate()` (`ControllerEventLoop.hpp:3179-3184`) writing `pending_params.bg_price_threshold = Money_Zero()` + `GATE_FLAG_BUY_BLOCKED`. `pending_params` is itself unpersisted and rebuilt from scratch every pass.
2. **Every one of the 8 zero-gate conditions re-derives from persisted or live state** (I enumerated them rather than asserting a property over the set — M9):

| site | code | condition input | source after a warm restart |
|---|---|---|---|
| `:3222` | `HALT_NODE_BUDGET` | `node_open_notional >= allocated_balance` | both persisted (rows `:82`, `:73`) |
| `:3326` | `HALT_NODE_KILL` | `KILL_TRIPPED` flag | persisted BIT row `:97` |
| `:3333` | `HALT_SL_COOLDOWN` | `sl_cooldown_remaining > 0` | persisted row `:92` |
| `:3375` | `HALT_SPACING` | `last_entry_price` + rolling stddev | price persisted (`:90`); rolling re-warms |
| `:3387` | `HALT_VWAP` | rolling stats | re-warms |
| `:3399` | `HALT_LONG_SLOPE` | `rolling_long` | re-warms |
| `:3410` | `HALT_VOL_DELTA` | rolling | re-warms |
| `:3421` | `HALT_MIN_STDDEV` | rolling | re-warms |
| `:3197` | `HALT_IMBALANCE` | live depth book | live input |

3. **Ordering guarantee.** In `EngineCommon_SlowPathCycleOneCore` (`EngineCommon.hpp:527`) the sequence per cycle is: `EventLoop_RebuildOneCore` (`:621`) → seqlock push of `pending_params` (`:644-652`) → … → **warmup permission grant (`:800-810`)**. Cores boot with `ExecutionCore_SetPermission(&core, 0)` at `EngineCommon.hpp:471`, and the snapshot loader never touches `permission` (it writes only `entry_price`/`live_tp`/`live_sl`/`active`, `ShardedSnapshotPersist.hpp:553-563`). So **the first params the hot path ever sees already carry the recomputed gate**, and permission cannot be 1 before at least one full rebuild has run.
4. `DIRTY` (which gates the push, `:644`) also cannot be stale: `node_state_flags` is init'd to `0` (`NodeCtxInitRegistry.hpp:107`) and only the `KILL_TRIPPED` bit rides the wire.

**Verdict for both: SAFE-UNPERSISTED, `DERIVED_EACH_PASS`.** `= HALT_OK` at `:3116` and `= SHALT_OK` at `:3120` are unguarded statements at brace depth 2 and dominate every read.

**But verifying `strategy_halt_reason` surfaced a real defect — see F-1.**

---

## C. FINDINGS (things you did not ask about)

### ⚠ F-1 — HIGH — `strategy_halt_reason` is reset ~55 lines AFTER its producer; the SHALT channel has been inert since the commit that created it

`ControllerEventLoop.hpp:3061-3079` passes the field's address into the strategy dispatcher:

```text
Strategy_BuildParameters(
    effective_strategy_id, ...
    &state->nodes[slot].strategy_halt_reason,  // v5.6.2 — dispatcher writes
                                               // SHALT_* codes for fee-floor /
                                               // cost-gate / no-signal paths.
```

and `ControllerEventLoop.hpp:3120`, later in the **same straight-line block**, does:

```text
state->nodes[slot].strategy_halt_reason = SHALT_OK;
```

**Mechanically verified, not eyeballed:** both lines sit at brace depth 2 in the scope opened at `:2673`; the only loops in the function are `:2899` and `:3262` (neither spans the interval); and a scan of lines 3061–3120 for `goto|return|continue|break|longjmp` returns **nothing**. `:3120` therefore executes after `:3061` on every full rebuild, unconditionally.

**Of the 20 codes in `FOREACH_SHALT` (`Strategies/StrategyInterface.hpp:295-315`), only two are written after the reset and can survive:** `SHALT_RECOVERY` (`ControllerEventLoop.hpp:3156`) and `SHALT_EXIT_PREDICTED` (`EngineCommon.hpp:750`, after `RebuildOneCore` returns). The other **17** non-OK codes — `FEE_FLOOR`, `COST_GATE`, `NO_SIGNAL`, `LOW_CONFIDENCE`, `ML_BELOW_THR`, `ML_NO_PRED`, `MOM_TP_TOO_TIGHT`, `MOM_NO_FLOW`, `MOM_LOW_R2`, `BAD_PCT`, `MODEL_CORRUPT`, … — are all written from inside `Strategy_BuildParameters`/`ML_BuildParameters`/`GateParameters_FinalizeEmit` (`StrategyParameters.hpp:326`, `:1659`, `:1737`, `:1866`, `:1876`, `:1887`, `:1916`, `:1934`, `:2012`, `:2051`, `:2094`) and are clobbered.

**The deterministic single-threaded proof this is a bug and not a design choice:** the gate health log at `ControllerEventLoop.hpp:3482-3502` reads `strategy_halt_reason` at `:3484` — *after* `:3120`, same thread, same pass — and formats `"halt=%u shalt=%u blocked=%u perm=%u"`. That log line **can never print a dispatcher-emitted SHALT code**. (The GUI path is racier still: the snapshot publisher runs on another thread and would have to sample inside the `:3070`→`:3120` microsecond window to catch one.)

**The design intent is stated in-code and contradicts the code** — `Strategies/StrategyInterface.hpp:354`: *"Reset to SHALT_OK **at the top of each rebuild**."* `:3120` is not the top; it is 59 lines below the dispatcher call.

**Born broken.** `git log -S` puts both edits in the same commit: `bc37c62` (2026-04-30, *"strategies(*): emit strategy_halt_reason for GUI visibility (v5.6.2)"*); the diff adds the pointer arg at old-line ~1786 and the reset at old-line ~1823. **The reset was placed after the write from day one.** `SHALT_RECOVERY` (v5.12.1.A.3) and `SHALT_EXIT_PREDICTED` (v5.13.0.B) were added later and happen to land after the reset, which is why the panel shows *something* and the hole went unnoticed.

**Why no guard sees it:** `grep -n "strategy_halt_reason" tests/controller_test.cpp` returns **zero hits**. The suite pins the SHALT *constants* (`:12674-12677`) but never asserts a code survives a rebuild. `check_cfg_gate_caller_coverage.py` / the latency analyzer / the persist goldens are all structurally blind to a write-ordering inversion.

**Not a capital bug** — the gate zeroing itself is carried by `out->flags |= GATE_FLAG_BUY_BLOCKED` on `pending_params`, which is independent of this byte. It is an **observability/forensics** bug: the operator's per-node "why is this node not trading?" channel, the `summary.json` archive (`NodeCtxSummaryFieldRegistry.hpp:176` → `PaperResetArchive.hpp:224`), and the gate health log all under-report.

**Fix shape (for the record, not for me to apply):** move `:3116-3120` to immediately after the `zero_gate` lambda's dependencies are established but **before** `:3061` — i.e. hoist the two-line reset above the `Strategy_ExitAdjustPerCore`/`Strategy_BuildParameters` block, which is what the `StrategyInterface.hpp:354` comment already specifies. Note `:3116` (`halt_reason = HALT_OK`) is currently **correct** where it is (its only producers, `zero_gate` at `:3179` and `:3197`, are below it) — so the two lines must be **split**, not moved together. That asymmetry is exactly what makes this easy to get wrong on the fix.

### ⚠ F-2 — MED — three unenumerated instances of the codified cross-thread multi-word read class, sitting on `intended_tp` / `intended_sl` / `intended_qty`

`DESIGN_SPECS/concurrency-patterns/cross-thread-multiword-read-consistency-discipline.md` (Stage 3, established 2026-06-10) states the rule and then enumerates **"the canonical instance (9 sites)"** — LIVE reconciler, global kill switch, per-core MTM kill switch, periodic save, TUI publish, ANSI render, GUI drag-TP/SL. **The `intended_*` trio is not among them**, and it satisfies the rule's trigger exactly:

- **Writer:** `ControllerEventLoop.hpp:3465-3467`, inside `EventLoop_RebuildOneCore`, called from `EngineCommon.hpp:621` on the **per-node slow thread** (`Run.hpp:1712` `slow_paths.emplace_back`).
- **Reader:** `EngineSharded/Async.hpp:885` (`intended_qty`), `:940` (`intended_tp`), `:972` (`intended_sl`), inside `EngineSharded_Async_DrainWithSubmit` (`Async.hpp:816`), called at `Run.hpp:1575` and `:1614` inside the **drainer thread** lambda started at `Run.hpp:1539`.
- **Type:** `Money` = `FixedPoint<10,8>`, **16 B** per the clang dump — squarely ">8B", no seqlock, no atomic, bare struct load.

The code **already knows about the cross-thread relationship** and fixed only half of it. `Async.hpp:879-884`:

> *"F-096: ONE read of `intended_qty` feeds BOTH legs. Load-bearing — the slow path writes this field (`ControllerEventLoop.hpp:3461`) while the drainer reads it bare, so two separate reads could straddle a rebuild and see different values. Conservation is then only guaranteed per-READ-PAIR, which is exactly what this single `intended` local pins."*

Hoisting to one read makes `legA + legB == intended` a theorem **for whatever value that one read returns** — it does not make that read non-torn. A torn `intended_qty` yields a leg split that conserves perfectly to a quantity that **never existed**, which is the spec's own definition of the failure. (Also: that comment cites `:3461`; the actual write is `:3467` — a stale line cite, § 2.5.)

**Blast radius is bounded but real:** `intended_qty` reaches `SubmitCommand.qty` → `OrderManager` → `Portfolio_OpenSlot` — it is order size. Exposure is a single slow-path rebuild landing inside the drainer's read; contained by the same `.E.1` aggregator rework the spec slates for the other 9 sites, but it must be **on the list** to ride that fix. Per `feedback_enumerate_set_before_categorical_claim`, a spec that says "the canonical instance (9 sites)" and is missing three is the exact shape M9 exists to catch.

### F-3 — LOW — `node_dd_pct` display window after a warm restart

Covered in § B.1. Comment correction suggested there.

### F-4 — LOW — `intended_tp`/`intended_sl` reach the forensic order-event log as zeros on a post-restart pre-first-rebuild exit

`ExecutionCore.hpp:603-605` gates entries on permission (`can_enter = ~any_active & perm & bg_fires`) but **exits are not permission-gated** (`can_exit_a = active & sg_fires_a`). The snapshot loader sets `active = 1` and arms `live_tp`/`live_sl` at `ShardedSnapshotPersist.hpp:553-563`, so a restored position **can** exit on the first tick, before any rebuild. That exit path reads `intended_tp` (`Async.hpp:940`) and `intended_sl` (`:972`) — both still `Money_Zero()` from init — and stuffs them into `SubmitCommand`.

**Capital impact: none.** `handle_sell_fill` (`OrderManager.hpp:1497-1583`) never reads them; only `handle_buy_fill` does (`:1465-1470`). **But** `OrderManager_HandleFill` appends them to the audit log unconditionally at `OrderManager.hpp:1648-1654` (`o->intended_tp, o->intended_sl`), so the `OrderEvent` record for that exit carries `tp=0, sl=0`. Adjacent to the already-tracked `PARITY_ISSUES.md:1562` (event-log replay reconstructs `original_tp` from `e.tp`) — a replay over a log containing such a record has one more way to diverge.

### F-5 — LOW — `last_confidence_factor` is a snapshot field with no renderer, and its write is not total

Two independent smells on one field:
1. `snap->per_node[i].ml_confidence_factor` is written at `ShardedSnapshot.hpp:591` and declared at `EngineTUI.hpp:1217`, but a grep over `GUI/`, `DataStream/`, `Backtest/` finds **no consumer** — only `tests/controller_test.cpp:24653` (a field-exists assertion). The derived `LADDER_BOTTOM_HIT` flag (`ShardedSnapshot.hpp:597-599`) *is* the surfaced form. Orphan sink.
2. The write at `StrategyParameters.hpp:1717` is **not on every path**: the confidence hard-floor block early-returns at `:1662`, and the ladder-bottom block early-returns at `:1738` (after writing). So on a hard-floor cycle the field keeps the previous cycle's value. Harmless today precisely because nothing reads it — but it means the field is neither reliably fresh nor `DERIVED_EACH_PASS`; the honest category is `DISPLAY_SINK_ONLY`.

### F-6 — LOW — stale comments (§ 2.5) and two dead functions found in passing

| site | claim | truth |
|---|---|---|
| `ControllerConfig.hpp:1195` | `// 0 = legacy (default), 1 = event log` | `ControllerConfig_Defaults` sets `cfg.oms_event_log_mode = 1` at `:2330`. The comment inverts the default. |
| `Async.hpp:880` | `(ControllerEventLoop.hpp:3461)` | the `intended_qty` write is `:3467` |
| `StrategyInterface.hpp:354` | `"Reset to SHALT_OK at the top of each rebuild"` | reset is at `:3120`, 59 lines *below* the producer — see F-1 |
| `ControllerEventLoop.hpp:1595` `EventLoopState_SetIntendedParams` | — | **zero callers** anywhere (engine, tests, backtest). Dead. |
| `ControllerEventLoop.hpp:4231` `EventLoop_Unpause` | doc says *"safe sequence: Rebuild → Push → Unpause"* | **zero production callers** — only doc cross-refs. Dead; but see refute target #2. |

---

## D. RECOMMENDED EXEMPTION VOCABULARY FOR THE CI GUARD

Your four candidates do not partition this family cleanly. My proposal, with the discriminating question each category must answer:

| category | definition | discriminating question the guard should force | fields |
|---|---|---|---|
| `DERIVED_EACH_PASS` | unconditionally overwritten every full slow-path pass at a cited `file:line`, dominating every read in that pass | *"cite the unconditional write and prove brace-depth dominance over every read"* | 4, 5, 7, 8, 9, 10, 12 |
| `DERIVED_BEFORE_ARM` | derived each pass, **and** the execution consumer that could act on a pre-derivation value is blocked by an independent arming flag that cannot open before the first pass | *"name the arming flag, its init site, and its ONLY grant site — and prove the grant is downstream of the derivation"* | 1, 2, 3 |
| `SUPERSEDED_BY_PERSISTED_SIBLING` | the semantic IS needed across a restart, but a **different, persisted** field carries it; this copy is a fallback | *"name the persisted sibling + its wire row + the fallback site"* | 11 |
| `DISPLAY_SINK_ONLY` | write-only from the engine's perspective; every reader is TUI/GUI/log emit | *"enumerate EVERY reader and show none is exec/risk"* | 6 |

**Two categories I recommend you do NOT ship, and why:**

- **`WALL_CLOCK`** — refuted by field 11 (§ A). "A host-clock stamp is meaningless across a restart" is a *false* general premise in this codebase; the one field it obviously fits is safe for the opposite reason. A guard that accepts it will green-light the next wall-clock field that has no persisted sibling.
- **`DISPLAY_ONLY`** as a general token — it is the sentence you warned about, and field 7 (`last_exit_prediction`) is the live counterexample: an ML *observability* field that fires a real MARKET_SELL. If you keep it, rename it `DISPLAY_SINK_ONLY` and require the **enumerated reader list** as data in the row (not prose), so the guard can re-derive it and go red when a new reader appears. That is the only version of this category that stays true over time.

**Two structural suggestions for the guard itself**, both derived from what actually found things here:

1. **Require the reason row to carry a `dominating_write` cite (`file:line`) and a `readers` list**, and make the guard re-derive the reader list by grep, going red on a new reader. A prose reason cannot rot loudly; a cited set can. (This is the generalization of OQ-4 from the sister sweep — a reason column alone was insufficient there because the reason was false; here two of four *offered* reasons are false. The fix in both cases is to make the reason **mechanically re-checkable**, not merely present.)
2. **Add a write-ordering check to the same pass.** F-1 is exactly the failure mode a "reset each pass" exemption is supposed to rest on, and it is broken. If a row claims `DERIVED_EACH_PASS`, the guard can cheaply assert that the cited reset line is **less than** every producer line in the same function — that one comparison would have caught F-1 on the day it shipped, 2026-04-30.

---

## E. SPOTS MOST WORTH AN ADVERSARIAL REFUTE (for the paired a-class)

1. **The permission gate is my single load-bearing mechanism for `intended_tp/sl/qty` — attack it, not the write site.** My chain: `permission=0` at `EngineCommon.hpp:471`; grants exist at `EngineCommon.hpp:809` (post-rebuild), `Backtest/BacktestSharded.hpp:727` (no snapshot load), `ControllerEventLoop.hpp:4239` (`EventLoop_Unpause`, no production caller); the snapshot loader never writes `permission`. **If any grant path can run before the first rebuild, all three verdicts flip.** I grepped `ExecutionCore_SetPermission` across `CoreFrameworks/`, `Backtest/`, `Strategies/` and found exactly those sites — but I did **not** walk `GUI/` or `DataStream/` for an operator "resume" control that might reach `EventLoop_Unpause`, and I did not check whether the paper-reset path re-grants. **That is the weakest link in my chain and the highest-value refute target.**
2. **`EventLoop_Unpause` is dead *today*.** If a future decoupled-runtime control surface wires it (the roadmap explicitly adds operator commands), it grants permission to every node with no rebuild — arming the hot path with `intended_*` = 0. Argue this makes `DERIVED_BEFORE_ARM` a *fragile* exemption that ought to carry a comment at `:4239`, or argue dead code doesn't count.
3. **Attack the mode-0 branch I dismissed.** I claim `EventLoop_OnEvent`'s `intended_*` reads (`:2184-2213`) are unreachable because `should_apply` is false in mode-1 (`:2165-2171`) and mode-1 is the default (`ControllerConfig.hpp:2330`). But `oms_event_log_mode` is **operator-settable** (`ControllerConfig.hpp:3415-3421`) and `Run.hpp:758` passes it through. Under `oms_event_log_mode=0`, `EventLoop_OnEvent` calls `Portfolio_OpenSlot(..., ctx->intended_tp, ctx->intended_sl, ...)` directly. I argue permission still dominates — refute by finding a mode-0 path that opens a slot without an `ExecutionCore` entry event.
4. **Attack F-1's severity in the other direction.** I graded it HIGH-observability / not-capital because the actual gate zeroing rides `pending_params.flags`. Push back: `SHALT_BAD_PCT` (`StrategyParameters.hpp:326`, the A6 egress chokepoint for corrupt tp/sl_pct, TECH_DEBT-171) and `SHALT_MODEL_CORRUPT` (`:1934`, D-221) are **corruption detectors**. If any operator runbook, alert, or future auto-response keys off those codes reaching the operator, F-1 upgrades from "panel under-reports" to "a corruption signal is silently swallowed". I did **not** audit the runbooks or `Notify_*` for SHALT consumers.
5. **Attack F-2 by arguing 16B aligned loads are atomic in practice.** `intended_tp` is at offset 2112 (16-byte aligned, clang-confirmed), and on modern x86-64 an aligned 16B SSE load is *practically* single-copy-atomic. The counter is that the codebase's own Stage-3 spec explicitly rejects that argument as **anti-pattern rule 3** (*"A comment asserting word-atomicity on a >8B field is the smell… aligned ≠ atomic for >8B"*). Someone should settle whether the trio joins the `.E.1` remediation list or gets a documented exemption — **claimed-and-absent from the enumeration is the one state that is not defensible.**
6. **Recount my reader enumerations.** I derived them by `rg` over `CoreFrameworks/ Strategies/ ML_Headers/ Backtest/ DataStream/ FixedPoint/ MemHeaders/ GUI/` plus `tests/` and `tools/`. I did **not** search `foxml_suite`-only sources or any generated code. `DISPLAY_SINK_ONLY` for `last_confidence_factor` and `DISPLAY_ONLY`-adjacent claims for the four ML observability fields rest on that enumeration being complete.
7. **Attack the paper-mode-only scope bound.** I claim warm restart is paper-only (`Run.hpp:1065`). If the v5.15 live-readiness sprint flips that gate — which is plausibly the point of the sprint — every verdict above should be re-run with live reconciliation interleaved, because `Reconcile_Decide` (`Run.hpp:1102`) can mutate positions on a path I did not trace against these 12 fields.

---

## F. OPEN QUESTIONS FOR CARAMEL

- **OQ-1 (F-1, the only one I'd call blocking):** hoist `strategy_halt_reason = SHALT_OK` from `ControllerEventLoop.hpp:3120` to above the `Strategy_BuildParameters` call at `:3061`, per the intent already stated at `StrategyInterface.hpp:354`? Note `halt_reason = HALT_OK` at `:3116` must **stay** — the two lines are currently adjacent but have opposite correct placements. And the fix needs a test, since the suite has zero `strategy_halt_reason` assertions.
- **OQ-2 (F-2):** add `intended_tp`/`intended_sl`/`intended_qty` to the 9-site enumeration in `cross-thread-multiword-read-consistency-discipline.md` so they ride the `.E.1` aggregator fix — or document a deliberate exemption with the reason?
- **OQ-3 (the vocabulary, § D):** drop `WALL_CLOCK` and rename `DISPLAY_ONLY` → `DISPLAY_SINK_ONLY` with a machine-checkable reader list? Adopt `DERIVED_BEFORE_ARM` and `SUPERSEDED_BY_PERSISTED_SIBLING`?
- **OQ-4 (§ D.2):** add the write-ordering assertion (`reset_line < every producer_line in the same function`) to the guard? It is one comparison and it catches the exact class F-1 belongs to.
- **OQ-5 (F-5 / F-6):** delete `EventLoopState_SetIntendedParams` and the unrendered `ml_confidence_factor` snapshot field per the backwards-compat-not-default gradient, or leave them tracked?

---

**Key files** (all absolute):
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerEventLoop.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EngineCommon.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EngineSharded/Async.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EngineSharded/Run.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ShardedSnapshot.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ShardedSnapshotPersist.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ExecutionCore.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/OrderManager.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerConfig.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/Portfolio.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/PaperResetArchive.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/Strategies/StrategyParameters.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/Strategies/StrategyInterface.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeCtxPersistRegistry.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeCtxInitRegistry.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/MemHeaders/NodeCtxSummaryFieldRegistry.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/GUI/DashboardPanels.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/GUI/MLStatusPanel.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/DataStream/EngineTUI.hpp` ·
`/home/caramel/code/FoxML_Trader_v2/tests/controller_test.cpp` ·
`/home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/concurrency-patterns/cross-thread-multiword-read-consistency-discipline.md` ·
`/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/reports/2026-08-15-complement-blindness-sweep/S1-capital-wire-persist.md`

---

*Note on fenced blocks: three ` ```cpp ` fences in the agent's original output are retagged ` ```text ` here — they are excerpts quoted out of their enclosing functions and the B-Plus compile probe classifies such excerpts as fabrications (TECH_DEBT-273). Content is otherwise byte-verbatim.*
