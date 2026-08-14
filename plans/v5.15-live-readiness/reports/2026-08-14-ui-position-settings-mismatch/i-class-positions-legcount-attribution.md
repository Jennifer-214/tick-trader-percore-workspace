---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: paired-trade "2 positions" display mechanism + open-count site map + strategy-attribution surfaces + stats-plane zeros + leg-B price (operator spot-check, 3 addenda relayed mid-run)
agent_class: i-class
delivered: 2026-08-14 (during the E.1.2 D-305-tail pickup session)
consumed_by: the eventual-item documentation (display-truth leaf, decoupling roadmap) + operator repro questions
---

# I-CLASS REPORT — Paired-trade "2 positions" display mechanism + open-count site map + strategy-attribution surfaces
**HEAD 3c57534 · branch feat/v5.15-live-readiness · 2026-08-14 · skill applied: `/dependency-chain-trace` (chain:`node_open_positions` + chain:`entries_processed/exits_processed` + cohort popcount(`active_bitmap`)) · read-only**

---

## § 1. MECHANISM (confirmed end-to-end, all cited)

One logical paired entry produces **2 fills → 2 mask bits → 2 counter bumps**, and the per-node display derives its count from those per-leg counters while the header derives from a pair-collapsed bitmap. The two planes disagree by construction.

Chain:

1. **Hot path emits per-leg events, same tick:** `ExecutionCore_Tick` entry pushes `event_a` AND `event_b` (leg=`PARTIAL_LEG_B`) — `CoreFrameworks/ExecutionCore.hpp:661` + `:690-691` (exits likewise `:640`/`:649-650`).
2. **Drainer maps each event to its own slot + own SubmitCommand:** `EngineSharded_Async_DrainWithSubmit` — `CoreFrameworks/EngineSharded/Async.hpp:841` (`Sharded_LegSlot(slot, event.leg, partial_on)`), qty split `:876-882`, `SubmitCommand` ctor comment "P.3: actual slot, not node_id" `:924`. So `Order::node_id` **is the portfolio SLOT** (2c / 2c+1).
3. **Each BUY fill sets its own slot bit:** `handle_buy_fill` → `oms->last_opened_mask |= (uint16_t)(1u << (int)o->node_id)` — `CoreFrameworks/OrderManager.hpp:1471`. SELL side: `last_closed_mask` at `OrderManager.hpp:1524`.
4. **DrainPostFillOneCore walks per-BIT and bumps per-bit:** `CoreFrameworks/ControllerEventLoop.hpp:1611` (fn), `my_mask` covers BOTH leg slots under partials `:1641-1643`; open-mask walk bumps `ctx.entries_processed++` + `state->total_entries++` **once per slot bit** `:1689-1691`; close-mask walk bumps `ctx.exits_processed++` + `state->total_exits++` per bit `:1785-1787`. **→ one paired entry = `entries_processed += 2`.** (Wrapper `EventLoop_DrainPostFill` `:2040-2064` just loops nodes.)
5. **Snapshot publisher derives per-node count from those counters:** `snap->per_node[i].node_open_positions = (uint32_t)(entries - exits)` — `CoreFrameworks/ShardedSnapshot.hpp:500-502`, inside publisher `TUI_CopySnapshotSharded` (`ShardedSnapshot.hpp:57`). The adjacent comment `:498-499` ("single-position-per-core invariant means this is 0 or 1 today") is **STALE** — under partials it is 0..2 (suggested wording: "entries−exits counts LEG fills; 0..2 under partials — see pair-collapse at :144-147").
6. **But the HEADER count is already pair-collapsed:** `ShardedSnapshot.hpp:137-150` — under partials `active_count = popcount((bm | bm>>1) & 0x5555)` (any-of-pair OR-fold, `:144-147`); else raw `agg.active_position_count` (`:149`).
7. **GUI renders the disagreement:** per-node Budget tooltip prints `node_open_positions` as `"%u open position%s"` — `GUI/DashboardPanels.hpp:1215/:1224-1226` (shows **"2 open positions"** for one pair), while TopBar `POS %d/%d` (`:312`) and Positions header `(%d/%d)` (`:1330`) show the pair-collapsed `active_count` (**1**). Positions table rows themselves are pair-aware `#0.A/#0.B` (`:1385-1393`).

**Consistency note:** the boot-replay reconstructor `EventLoopState_ReconstructPerCoreFromEventLog` also counts per-fill (`ControllerEventLoop.hpp:1032`/`:1045`) — replay and live agree on the (per-leg) counter semantics. But its **W/L is per-LEG** (`:1053-1055`, each SELL classifies individually) while the live drain is **per-PAIR** (v4.7.21, `:1815-1833` via `partner_pending_pnl`/`partner_pending_bitmap`) — a live-vs-replay parity divergence under partials (see § 3, finding A6).

---

## § 2. SITE ENUMERATION — every "open/active position count" derivation

| # | Site (file:line) | Derivation | Intended semantics | Correct today? |
|---|---|---|---|---|
| S1 | `CoreFrameworks/ShardedSnapshot.hpp:500-502` | `entries_processed - exits_processed` per node | **LOGICAL-PAIRS** (operator Budget tooltip "open positions") | **WRONG under partials** (=2 for one pair; coincidentally 1 mid-pair). Also underflow-fragile — wraparound warning documented at `ControllerEventLoop.hpp:1151-1152` |
| S2 | `CoreFrameworks/ShardedSnapshot.hpp:144-150` | pair-collapse `(bm\|bm>>1)&0x5555` popcount / raw agg | LOGICAL-PAIRS (headline `active_count`) | **CORRECT** — the existing (inline, un-extracted) pair-collapse idiom |
| S3 | `CoreFrameworks/EventLoopAggregates.hpp:84,:157` (`EventLoop_GetAggregates` bitmap walk `:143-156`) | raw bitmap walk count | SLOTS (internal aggregate; also drives unrealized P&L walk) | Correct as SLOTS; consumed by S2's else-branch |
| S4 | `GUI/DashboardPanels.hpp:1215,:1226` | reads S1 | LOGICAL-PAIRS (label says "open position(s)") | **WRONG label+value under partials** (unit is leg-fills) |
| S5 | `GUI/DashboardPanels.hpp:312` (TopBar), `:1330` (Positions header) | reads S2 `active_count` / `max_positions` | LOGICAL-PAIRS / node capacity (`max_positions = num_execution_nodes`, `ShardedSnapshot.hpp:151`) | Correct |
| S6 | `DataStream/EngineTUI.hpp:1290` | PerNodeSnap mirror field decl (comment repeats the entries−exits derivation) | mirror of S1 | Field defined but **never rendered by TUI** (only GUI S4 reads it); stale comment rides along |
| S7 | `DataStream/EngineTUI.hpp:2129` | `POSITIONS (%d/16)` — `s->active_count` over **hardcoded 16** | numerator LOGICAL, denominator SLOTS | **MIXED-UNIT label** (1/16 shown; capacity in slots, count in pairs) |
| S8 | `CoreFrameworks/EngineSharded/Run.hpp:2116` + render `:2143` | `popcount(active_bitmap)` → `POS %d/%u` over `num_nodes` | numerator SLOTS, denominator NODES | **MIXED-UNIT** in the built-in sharded terminal dashboard ("POS 2/4" for one pair on 4 nodes) |
| S9 | `CoreFrameworks/ShardedLiveSafety.hpp:262-278` | `popcount(active_bitmap)` = `remaining` after force-close | **SLOTS** (flatten must drain every slot; alert text says "position(s)") | Semantically correct as slots; message unit-label arguably fine (each slot is a real exchange lot to flatten) |
| S10 | `CoreFrameworks/EngineSharded/Run.hpp:1101` | `local_open = popcount(active_bitmap)` → `Reconcile_Decide` | **SLOTS** (exchange-truth compare) | Correct — reconcile predicates only test `>0`/`==0` (`CoreFrameworks/Reconcile.hpp:771,:792-793`) so pair-vs-slot is immaterial there |
| S11 | `CoreFrameworks/EngineSharded/Run.hpp:2364-2371` | `still_open` popcount at shutdown persist log | SLOTS ("N position(s) open on shutdown") | Correct as slots (persist reality); label unit = legs |
| S12 | `CoreFrameworks/Portfolio.hpp:396-398` | `Portfolio_CountActive` helper | SLOTS (generic) | Correct as slots; used by legacy TUI (`EngineTUI.hpp:274,:1718` — legacy `PortfolioController` plane, no partials) |
| S13 | `DataStream/MetricsLog.hpp:143,:179` | popcount → CSV `positions` column | SLOTS | **ORPHANED** — legacy `PortfolioController<F>` reader, no callers found in engine source (`[OVERVIEW]` tag at `MetricsLog.hpp:113` says "orphaned with the file") |
| S14 | `Backtest/BacktestSharded.hpp:843-845` | `total_trades = (total_entries + total_exits) / 2` (global per-fill heartbeats) | LOGICAL trades (backtest headline) | **WRONG under partials** — one round-trip pair = (2+2)/2 = 2 "trades". Correct partials-off |
| S15 | `GUI/DashboardPanels.hpp:1731-1752` | Stats: `logical_buys = total_buys/2` under partials; exits headline = `wins+losses` (pair-classified); fills tails = raw | LOGICAL headline + FILLS tail (deliberate v4.7.18 dual display) | Halving heuristic is **fragile**: integer-truncates when a pair is half-submitted (leg-B reject → 1 fill → "buys: 0") and assumes all entries fully paired |
| S16 | Fill-counter sources: `ControllerEventLoop.hpp:1689-1691,:1785-1787` (live), `:1032,:1045` (replay), `:2188,:2257` (mode-0 legacy/test OnEvent body — production mode-1 returns early at `:2165`) | counter bumps | PER-FILL heartbeat (doctrine: `DOCS/CLAUDE_INVARIANTS.md:21-38`) | Correct per doctrine — the defect is *display sites treating fills as positions*, not the counters |

---

## § 3. ADJACENT MISLABELED-UNIT / PARITY FINDINGS (same surface)

- **A1 (MED, display):** S4 — "N open position(s)" tooltip unit is leg-fills. The observed bug.
- **A2 (LOW, display):** S7 — TUI `(%d/16)` logical-over-slot-capacity mixed units.
- **A3 (LOW, display):** S8 — Run.hpp built-in dashboard `POS slots/nodes` mixed units.
- **A4 (MED, metrics):** S14 — backtest `total_trades` double-counts under partials; feeds the end-of-run summary (and anything consuming `stats->total_trades`).
- **A5 (LOW, display):** S15 — Stats `buys/2` truncation + full-pair assumption; misleads on a half-submitted pair (and shows "buys: 0 (1 fills)" shapes).
- **A6 (MED, parity):** replay reconstructor classifies W/L **per-leg** (`ControllerEventLoop.hpp:1053-1055`) vs live per-pair (`:1815-1847`) — after an event-log-replay boot under partials, `node_wins+node_losses` (and gross buckets) diverge from an equivalent live run. Snapshot-restore path is unaffected (restores the persisted values directly, `ShardedSnapshotPersist.hpp:561-564`).
- **A7 (LOW, correct-by-design, document):** per-node W/L "trades" tooltip (`DashboardPanels.hpp:1204`) IS pair-classified — correct; and per-leg accounting fields (`node_realized/node_fees/node_open_notional`) are deliberately per-leg (`ControllerEventLoop.hpp:2083-2091` comment). Any relabeling ship must NOT "fix" these.
- **A8 (LOW, UB, display-only):** Positions-row strategy palette `sc[]` has **5 entries** but is indexed with `sid < NUM_STRATEGIES` (=6, incl. `STRATEGY_AUTO=5` per `Strategies/StrategyInterface.hpp:177-179`) — `GUI/DashboardPanels.hpp:1401-1410`: `sc[5]` is an out-of-bounds read whenever an AUTO node has an open position. The SAME bug was already fixed in the Header panel's sibling `sc[]` (6th AUTO entry + `static_assert`, `DashboardPanels.hpp:237-244`) — a Class-18-style incomplete mirror; the Positions copy lacks both the entry and the assert.
- **A9 (INFO):** stale comment at `ShardedSnapshot.hpp:498-499` (S1) per § 1 item 5.

---

## § 4. STRATEGY-ATTRIBUTION SURFACE MAP (addendum lane)

Field ground truth: `strategy_id_display` = **configured** `nodes[i].strategy_id` (`ShardedSnapshot.hpp:431`); `resolved_strategy_id` = **per-slow-cycle** resolution output (`ControllerEventLoop.hpp:2806` start-as-configured, AUTO→regime `:2845-2860`, stored `:3030`) — for non-AUTO nodes resolved ≡ configured every cycle. TUIPositionSnap carries **no strategy field** (`ShardedSnapshot.hpp:219-301` — nothing stamped); position rows attribute at RENDER time from `per_node[]`. Trade CSV rows stamp `cmd.strategy_id = state.nodes[slot].strategy_id` (**configured**) at submit (`Async.hpp:931`).

| Surface | Field read | Node-derive | At-entry vs now | Verdict (file:line) |
|---|---|---|---|---|
| Positions table row | `strategy_id_display` (configured) | `ps->idx >> 1` gated on `s->partial_exit_enabled` (grandfathered open-code) | **NOW-configured**; no at-entry stamp exists | Derive CORRECT; semantics defect for AUTO nodes: shows literal "AUTO" (no resolved fallback) + OOB color (A8) — `DashboardPanels.hpp:1385,:1408-1414` |
| Per-node P&L (Account) | cfg + resolved; non-AUTO renders `live_sid` (=resolved≡cfg), AUTO renders "AUTO(resolved-NOW)" | self-indexed `i` | NOW | Correct-for-static; AUTO shows now-resolved which can postdate the open position's entry resolution — `DashboardPanels.hpp:1153-1175` |
| Header CORES line | cfg + "(resolved)" for AUTO | self-indexed | NOW | Correct; fixed palette + static_assert — `DashboardPanels.hpp:245-261` |
| Buy Gate panel | cfg + AUTO(resolved) | self-indexed | NOW | Correct — `DashboardPanels.hpp:600-616,:727-733` |
| PerNodePnL chart labels | **resolved bare-name** (cfg fallback), NO "AUTO()" wrapper | self-indexed `c` | **NOW-resolved** | **Display-truth defect for AUTO nodes**: an AUTO node labels as plain "MOM"/"MR" per current regime — can contradict Positions' "AUTO" and the entry-time strategy — `DashboardPanels.hpp:1690-1693` |
| MLIntelligence rows | cfg + resolved | self-indexed | NOW | Correct — `DashboardPanels.hpp:2159-2168,:2267-2269` |
| Market panel census | resolved (cfg fallback) counts | n/a | NOW | Correct as census — `DashboardPanels.hpp:368-388` |
| **Headline strategy** (`snap->strategy_id`) | **node 0's resolved** only | node 0 hardcoded | NOW | **Defect-shaped**: a global-looking "strategy" label that is node-0-only — `ShardedSnapshot.hpp:364-377` |
| TUI ANSI "strategy:" line | `s->strategy_id` (headline) with **binary collapse** `== MOM ? "MOMENTUM" : "MEAN REVERSION"` | node 0 | NOW | **Defect**: DIP/ML/EMA/AUTO all render "MEAN REVERSION"; node-0-only — `DataStream/EngineTUI.hpp:2234-2239` region (the `strat_name` ternary) |
| TUI ANSI positions rows | **no strategy shown**; row id = display ordinal `displayed`, not slot/leg | none | n/a | **Not pair-aware at all**: one pair renders as two anonymous rows `#0`,`#1` — `EngineTUI.hpp:2131-2141` (`snprintf("#%-2d", displayed)`) |
| Trade History rows | CSV `strat` column = configured-at-submit (`Async.hpp:931`); core = `e->node_id >> 1` gated | flag passed correctly from snapshot (`GuiThread.hpp:540` → `TradeHistoryPanel.hpp:266,:317`) | **AT-SUBMIT configured** (AUTO nodes log "AUTO", not the resolved entry strategy) | Derive correct; semantics: no at-entry-resolved attribution — `TradeHistoryPanel.hpp:244,:317-327` |
| Chart exit labels / markers | `#core.leg` notation | `slot >> 1` gated | n/a | Correct — `ChartPanel.hpp:817,:909-922,:1005-1010` |
| Chart gate-line labels | `strategy_id_display` per node `ci` | self-indexed | NOW-configured | Correct labels; ADJACENCY-misread risk: node 3's MOM-labeled gate line can sit visually near node 0's position marker — `ChartPanel.hpp:1226-1231` |

**Hypothesis (a) — grandfathered derives:** D-295 grandfathered GUI open-coded derives; Check O tool exempts all of `GUI/` (`tools/check_slot_node_derive.py:11-12`). Current GUI derive-shape census (9 sites, all `partial_exit_enabled`-gated, all arithmetically correct): `DashboardPanels.hpp:1377,:1385,:1528,:1541` · `ChartPanel.hpp:376,:817,:913,:1005` · `TradeHistoryPanel.hpp:317`. The GUI flag source (`snap->partial_exit_enabled`, published from cfg at `ShardedSnapshot.hpp:367`) and the engine drain flag (`oms_state_flags` bit) both derive from the same cfg bit — consistent. **No wrong-node derive found.** (Note: D-295's "4 sites" tally has drifted to 9 shapes — name-members-not-tallies violation in the decision record; worth a currency touch.)

**Hypothesis (b) — cfg vs resolved split:** CONFIRMED as the real semantic split, with three concrete defect-shaped instances (PerNodePnL bare resolved-now for AUTO; node-0-only headline; TUI binary collapse). **However** — see § 7: under the operator's screenshot cores (all static, C0:MR…C3:MOM), resolved≡configured, so (b) cannot alone produce her "MR position shown as MOM."

---

## § 5. STATS-PLANE vs POSITION-PLANE ZERO (addendum lane 1)

Stats bar source chain: `total_buys = agg.total_entries = state->total_entries` / `total_exits_fills = state->total_exits` (`ShardedSnapshot.hpp:316-317` ← `EventLoopAggregates.hpp:135-136`); `wins/losses` = sum of per-node `node_wins/node_losses` (`ShardedSnapshot.hpp:417-419,:866`); gross/avg from `node_gross_*` (`:420-421,:874`). Published by `TUI_CopySnapshotSharded` unconditionally each publish.

Three counter families exist:
1. **Global heartbeats** `state->total_entries/total_exits` — EventLoopState, zeroed at `EventLoopState_Init` (`ControllerEventLoop.hpp:1115-1116`), **NOT in the v10 persist record** (fwrite inventory `ShardedSnapshotPersist.hpp:154-257` — no row) and **NOT rebuilt by the event-log reconstructor** (`:1032/:1045` bump only `nodes[node_id].*`, never `state->total_*`).
2. **Per-node counters** `entries_processed/exits_processed/node_wins/node_losses/node_gross_*` — **persisted + restored** (`ShardedSnapshotPersist.hpp:206-219` write, `:473-481` read, `:556-564` apply).
3. **Bitmap/positions** — persisted (`active_bitmap` `:180`, `positions[]` `:185`) and re-activated (`:670-690`).

Verdicts:
- **(a) warm-restart provenance — CONFIRMED-plausible, the mechanism.** A snapshot-restored open position renders in Positions/Risk (family 3) and in the per-node counters (family 2), while the Stats bar reads family 1, which restarts at 0. `buys: 0 (0 fills)` + open `#0.A` at 74s uptime + WARMUP 3/128 (a fresh session cannot have entered at 3 samples — entry gating requires warmup) is exactly this signature. W:0/L:0 is consistent (persisted wins/losses genuinely 0 — no completed pair pre-restart).
- **(b) warmup gating — REFUTED.** No warmup gate around the stats publish; warmup fields are display-only mirrors (`ShardedSnapshot.hpp:160-166`).
- **(c) different-counter-family labeled "buys" — REFUTED as stated** (total_buys IS entry-fill-derived), but (a) IS a family-split: the stats plane is the only consumer of the non-persisted family. Structural note: this is the same Class-18 snapshot-vs-replay mirror shape the reconstructor was built to close for per-node fields (`ControllerEventLoop.hpp:1063-1078` comment) — the GLOBAL totals were left out of that closure.

---

## § 6. LEG-B "HIGHER BUY PRICE" (addendum lane 2)

Leg-B **entry**-price write sites (exhaustive): (1) drainer split writes **qty only** (`Async.hpp:861-882`); leg-B **TP** is scaled by `tp2_mult` (`Async.hpp:899-917` absolute, `:946-955` `cmd.tp_pct` fraction); (2) `handle_buy_fill` opens the slot at the fill price (`OrderManager.hpp:1465-1470`); paper synthetic fill = `event_price + event_price×slippage_pct` at the A9 Submit chokepoint (`OrderManager.hpp:1157-1166`) — both legs are emitted **on the same tick** (`ExecutionCore.hpp:661,:690-691`) with the same `event.price` and same per-node slip → **paper leg entries are identical by construction**; (3) snapshot re-activation sets `entry_price_b = pos.entry_price` untransformed; only `live_tp_b` is elevated (`entry×(1+tp_pct×tp2_mult)`) — `ShardedSnapshotPersist.hpp:650-687`; (4) `breakeven_on_partial` ratchet is **deferred/unimplemented** (`DOCS/CLAUDE_INVARIANTS.md:245-246`); trailing/regime ratchets write TP/SL only.

**Disposition: EXPECTED-RATCHET/TP2-DISPLAY (most probable) + UNDETERMINED-needs-repro on which readout.** No code path produces a distinct leg-B ENTRY price in paper mode; the only leg-B number that legitimately sits ABOVE leg A's is its TP2 (by design, `tp2_mult` default 2.0). EXPECTED-FILL-MECHANICS applies only to live (two sequential market buys). DISPLAY-DEFECT (leg-B row rendering TP in the Entry column) is NOT evidenced — the Entry column reads `ps->entry = pos->entry_price` (`ShardedSnapshot.hpp:225`, render `DashboardPanels.hpp:1418-1419`).

**Footer reconcile:** leg B gets its own `#0.B` row **only after its BUY fill activates slot 2c+1** (rows render from `positions[idx].idx >= 0`, set only for active-bitmap slots — `ShardedSnapshot.hpp:219-224`). There is **no pending-orders UI surface** (grep for open/pending-order panels in GUI/ returned none). So with only `#0.A` visible, a "leg-B buy price" cannot have come from the positions table; nearest candidates are a per-node gate line/TP figure. In paper mode fills are synchronous-synthetic, so a lone `#0.A` under partials itself implies a half-pair (leg-B submit rejected/failed, or a restored pre-partials/half-pair snapshot) — which is ALSO the state that breaks the Stats `buys/2` halving (A5). Worth one targeted repro question to the operator: which panel showed the leg-B price.

---

## § 7. THE 0→3 (MR-shown-as-MOM) HUNT (addendum lane 3)

With static cores C0:MR C1:EMA C2:DIP C3:MOM, resolved≡configured on every node, so the cfg-vs-resolved split (§ 4 hypothesis b) is inert. Code-read found **no indexing path that maps node 0 → per_node[3]**: all per-position attribution routes `ps->idx>>1` (gated, correct); all per-node rows are self-indexed loops; the headline is node-0-pinned (would show MR, not MOM); the publisher `memset`s and re-marks `positions[].idx=-1` every publish (`ShardedSnapshot.hpp:66-68`) so stale-row ghosting is excluded. **NOT-REPRODUCED-FROM-CODE.** Remaining candidates, in order: (i) chart ADJACENCY misread — C3's MOM-labeled gate line rendered near node 0's position marker (`ChartPanel.hpp:1226-1231`); (ii) the Settings panel node-combo showing a different node's strategy than the position being looked at (`SettingsPanel.hpp:1540,:1772` — correct code, easy operator cross-read); (iii) the TUI headline binary-collapse line — refuted for this instance (MR renders "MEAN REVERSION"). Discriminating repro info needed: which panel displayed "MOM".

---

## § 8. PROPOSED STRUCTURAL SHAPE (do-not-implement; for the eventual plan item)

**No pair-aware count helper exists today.** The geometry family (`Sharded_LegSlot` `ControllerEventLoop.hpp:1338` · `Sharded_NodeSlotMask` `:1356` · `Sharded_SlotNode` `:1375` (canonical, Check-O-enforced) · `Sharded_ValidatePartialExitCfg` `:1388`) has no count member; the one correct pair-collapse lives inline at `ShardedSnapshot.hpp:144-147`.

**Option matrix:**

| Option | Shape | Verdict |
|---|---|---|
| O1 — extract pair-aware helpers into the geometry family | `Sharded_LogicalOpenCount(uint16_t bitmap, int partial_on)` (the `(bm\|bm>>1)&0x5555` fold, extracted from S2) + `Sharded_NodeAnyOpen(uint16_t bitmap, int node_id, int partial_on)` (`(bitmap & Sharded_NodeSlotMask(...)) != 0`); route S1/S2 through them; S1 becomes bitmap-derived (kills both the ×2 and the `:1151` underflow-wraparound class) | **RECOMMENDED core** — Class 43/45 single-source; H22-pure (function of bitmap+cfg only); branchless (H20-friendly); zero persist-wire impact |
| O2 — new per-node logical-trade counters bumped in DrainPostFill (leg-A rule) | new counter family + new persist rows | REJECTED — duplicates bitmap-derivable state (Class 43 violation), touches the v10 persist wire (E.1.2 entanglement + H21 version bump), adds a mirror to keep in sync |
| O3 — GUI-side patches only (labels + divides) | per-panel fixes | REJECTED — leaves N sites re-deriving pair geometry; the sc[] palette history (A8: fixed in Header, still broken in Positions) is this exact mirror-rot in evidence |
| **O4 — novel alternative**: **unit-typed snapshot contract** — PerNodeSnap carries BOTH `node_open_legs` and `node_open_trades` as explicit publisher-computed fields (via O1 helpers); viewers never compute pair geometry; labels bind to field names ("1 trade (2 legs)") | snapshot-seam fix | **RECOMMENDED composed with O1** — it is the decoupled-viewer-future shape (viewers must stay geometry-dumb per the decoupling roadmap); in-memory only (TUISnapshot is not persisted/HMAC'd); H21-safe append of fields |

**Deliberate SLOT-count exemptions (tag with a `// SLOT-COUNT-DELIBERATE` style comment at fix time):** S9 live-safety `remaining`, S10 reconcile `local_open`, S11 shutdown `still_open`, S3 aggregates walk, S12 `Portfolio_CountActive`. **Also in the eventual leaf:** S14 backtest `total_trades` (leg-A-entry or pair-aware divide), S15 Stats halving (replace with a leg-A-derived logical count or O4 fields), S7/S8 label units, A6 replay W/L pair-parity, A8 sc[] palette + static_assert, A9/S6 stale comments.

**Blast radius by plane:** engine geometry +2 helpers (1 file) · snapshot publisher 2 sites + 2 new PerNodeSnap fields (`ShardedSnapshot.hpp`, `EngineTUI.hpp` struct) · GUI 3-4 render sites (`DashboardPanels.hpp`) · TUI/Run built-in 2 label sites · backtest 1 site · replay parity 1 block (`ControllerEventLoop.hpp:1053-1055`) · tests: 50 existing counter references in `tests/controller_test.cpp` remain valid (counters untouched); +new helper tests. No persist wire, no hot path (all slow/publish/render cadence; `calls_graph_diff.sh` should confirm hot-path-untouched at fix time).

**One flagged risk for the helper design (H22/future):** the `0x5555` fold and `Sharded_NodeSlotMask` both assume `partial_exit_enabled` is GLOBAL (all nodes paired or none). `partial_exit_pct`/`tp2_mult` already have per-node overrides (`Async.hpp:873-875,:912-914`) — if per-node partial-ENABLE ever ships, every pair-collapse must become per-node-mask-driven; putting the collapse in ONE helper is exactly what makes that future change 1-site.

---

## § 9. RECOMMENDED PLAN HOME

**The decoupling roadmap (`plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`).** Reasoning: every defective site is display/monitoring-plane (snapshot publisher + viewers + summary tallies); the auto-write contract routes "any ship touching GUI ↔ runtime / TUISnapshot" there; and O4's unit-typed snapshot contract IS a decoupling-roadmap-shaped move (viewer-dumb snapshot seam). Not E.1.2 (capital persist — untouched, § 10). Not a generic E-series capital leaf: no money math is wrong (per-leg accounting is deliberately per-leg, A7). The A6 replay-W/L parity item is the one engine-behavior (non-display) finding — it can ride the same leaf or a small standalone parity fix.
[Orchestrator note at receipt: per the operator's directive these are homed as PLAN items (roadmap section + named leaf), NOT TECH_DEBT entries.]

## § 10. E.1.2 ENTANGLEMENT CHECK — CLEAN

The two planes are distinct files with distinct consumers: `CoreFrameworks/ShardedSnapshot.hpp` = in-memory TUI/GUI publish (`TUI_CopySnapshotSharded` → TUISnapshot seqlock double-buffer; never written to disk, never HMAC'd) vs `CoreFrameworks/ShardedSnapshotPersist.hpp` = versioned disk persist (`SHARDED_SNAPSHOT_VERSION 10u` at `:109`). `node_open_positions` exists only in PerNodeSnap (display) and is derived at publish; it is not persisted. The persisted counters (`entries_processed/exits_processed`, `:206-207`) keep their per-fill semantics untouched under the recommended O1/O4 shape → **no version bump, no H21 identifier motion, no overlap with the in-flight capital-persist work.** (O2 is the only option that would entangle — rejected partly for that.)

## § 11. SPOTS MOST WORTH AN ADVERSARIAL REFUTE (for the paired a-class)

1. **Half-pair failure modes:** the +2 claim — refute via the leg-B `OMS_PushSubmit`/`OrderManager_Submit` reject paths (queue-full, pool-exhausted, balance): a 1-fill pair makes S1 read 1 (accidentally "right"), breaks S15's `/2`, and is the state § 6's footer leans on. Enumerate the reject sites and their frequency.
2. **Bitmap-vs-counter transient skew:** S1→bitmap-derived changes WHEN the count moves (HandleFill sets the bit; the counter bumps at DrainPostFill later in the same drainer cycle). Verify no consumer depends on the counter-cadence timing.
3. **"Paper legs fill identical" claim** rests on same-tick emission + same `event.price` + the A17 full-qty single-fill (`OrderManager.hpp:1170`) — refute by checking whether the drainer can pop leg A and leg B in DIFFERENT drain cycles (ring-full partial pop at `MAX_EVENTS_PER_DRAIN_PER_NODE`, `Async.hpp:829`) — events carry their own price captured at emit; check whether leg-B's event price is re-read or copied.
4. **The `0x5555` global-partials assumption** — confirm `partial_exit_enabled` truly has no per-node override row in `FOREACH_CFG_FIELD`.
5. **MetricsLog orphan claim (S13)** — re-run the caller search including `main.cpp` legacy dispatch and any tool/test harness before anyone deletes it (H21 dead-code discipline wants it removed if truly dead).
6. **§ 5 restore-path claim** — verify which restore actually ran for the operator's paper session (does paper mode load the v10 snapshot unconditionally?) — the counter-family split is code-verified; the boot gating of snapshot load in her cfg is not.
7. **§ 7 negative result** — a second pass over `GUI/GuiThread.hpp` + SettingsPanel selected-node plumbing for any cross-panel shared index variable not traced.

**Tool disposition:** `DOCS/CODE_MAP.md` consulted; `check_slot_node_derive.py` read for the Check-O exemption scope; layout/latency/struct tools not run — no type/layout/hot-path change in scope; `calls_graph_diff.sh` deferred to the fix-time V-class pass.
