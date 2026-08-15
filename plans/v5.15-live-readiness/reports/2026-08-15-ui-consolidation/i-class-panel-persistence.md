---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: I-1 — GUI panel DATA-BACKING + PERSISTENCE lifecycle map (operator complaint: "trade history and stats tab are not persistent between sessions")
agent_class: i-class
delivered: 2026-08-15
ground: engine HEAD 09824e8 (pre-D-289/2), branch feat/v5.15-live-readiness
consumed_by: the UI-consolidation triage + the EV-1/EV-3 routing decision
sister_reports: i-class-panel-retirement-blast-radius.md · i-class-stats-consolidation-ia.md (this directory)
prior_art: reports/2026-08-14-ui-position-settings-mismatch/ (EV-1/EV-2 display-truth cohort)
---

# I-CLASS REPORT — GUI panel DATA-BACKING + PERSISTENCE lifecycle map

**Directive:** I-1 — map every ImGui panel's data source, the survive/reset lifecycle matrix, the hardcoded-path cohort (M9), the archive story, and rank the root causes behind the operator's *"trade history and stats tab are not persistent between sessions"*.
**Ground:** engine `/home/caramel/code/FoxML_Trader_v2` @ HEAD `09824e8`, branch `feat/v5.15-live-readiness`. **All cites verified by read/grep at HEAD** — none recalled; cross-checked against `DOCS/CODE_MAP.md` (`:295`, `:301`, `:303`, `:1002`, `:1052`, `:1058` — all agree).
**Read-only.** Nothing proposed for implementation, nothing edited.
**Skills applied:** `/dependency-chain-trace` methodology (chain: `TradeHistory.csv_path` · chain: `snap->total_buys` · chain: `snap->wins`), `/bug-check` class-matching (Class 2 / 18 / 44 / 45), M9 (enumerate-the-set before a categorical claim).
**Tools RUN:** `tools/calls_graph_diff.sh` → CLEAN · `tools/scan_class_44_cfg_orphan.py` → OK, 5 KNOWN-PENDING(#9), no new orphans. Both are blind to this surface (see § HAZARDS H-7).

---

## § 0. HEADLINE — the operator's complaint decomposes into FIVE distinct mechanisms, three of which are genuine defects

The single biggest finding: **her own logs contain the smoking gun**, and it is not what the framing assumed.

`/home/caramel/code/FoxML_Trader_v2/logging/engine.log` (today's session, 2026-08-15):
```
[OrderEventLog] loaded 4 events from logging/order_events.bin
[OMS] replayed 4 events from disk, balance=$10000.00
[snapshot] data/sharded_snapshot.dat written with partial_exit_enabled=0, current cfg=1 —
           refusing load (slot geometry differs; restoring would create zombie positions). Starting fresh.
...
[sharded] final: produced=5512 consumed=22048 entries=0 exits=0 balance=10000.0000
```
`/home/caramel/code/FoxML_Trader_v2/logging/engine.log.1` (the session before):
```
[snapshot] data/sharded_snapshot.dat version 8 != current 10 — refusing load
```

**The warm-restart snapshot load REFUSED on both logged sessions, for two different reasons.** And the trade CSV she is looking at contains **10 `E` rows and ZERO `X` rows** — while the Trade History panel renders **only `X` rows**.

Three corrections to the directive's priors, stated up front per arming § 4:

1. **`GuiThread.hpp:83`'s `btcusdt` hardcode is REAL but is NOT currently firing.** `engine.cfg:19` is `symbol=btcusdt`, so the literal matches what the engine writes today. It is a latent cohort defect, not the active cause.
2. **The `_sharded_order_history.csv` "filename-split bug" hypothesis in the roadmap (EV-1, `decoupling-endgoal-roadmap.md:711-715`) is REFUTED.** It was seeded by a **stale comment**. `CoreFrameworks/ShardedTradeLog.hpp:36` and `:291` both claim `logging/SYMBOL_sharded_order_history.csv`; the **code** at `:222-223` writes `logging/%s_order_history.csv`. The `_sharded_` name survives only in `experiments/per_core_sharding/test_trade_log.cpp`. Arming § 2.5: code is truth.
3. **The Stats panel is NOT uniformly non-persistent.** Its W/L/rate/pf/avgW/avgL/E[trade]/maxDD half *does* restore from the snapshot; only the `buys`/`(N fills)` half is structurally unrestorable. The asymmetry is the defect.

---

## § 1. PER-PANEL DATA-BACKING TABLE

24 ImGui windows exist (`rg 'ImGui::Begin\("' GUI/*.hpp`). The dock-builder `Gui_SetupDefaultLayout` (`GUI/GuiThread.hpp:355-400`) names **16**.

Classification key: **(a)** file-backed · **(b)** TUISnapshot live-only · **(c)** TUISnapshot but engine-side-persisted · **(d)** other.

| # | Window | Defined at | Docked by builder? | Class | Backing detail |
|---|---|---|---|---|---|
| 1 | `Price Chart` | `GUI/ChartPanel.hpp:244` | YES `:370` | **(d) mixed** | OHLCV from `CandleAccumulator` in engine RAM (`GuiThread.hpp:519`), gate lines from snapshot, trade markers from `TradeData` (CSV) — **the CSV leg is dead, see #4** |
| 2 | `Volume` | `ChartPanel.hpp:1276` | YES `:371` | (d) | `CandleAccumulator` + snapshot |
| 3 | `Live P&L` | `ChartPanel.hpp:1405` | YES `:372` | **(b)** | snapshot only |
| 4 | `Equity Curve` | `ChartPanel.hpp:1477` | YES `:373` | **(a) — BROKEN** | `TradeData` only (`ChartPanel.hpp:1478` `equity_count < 1` early-out). **Format-mismatched reader; always 0 points — see F-1** |
| 5 | `Header` | `GUI/DashboardPanels.hpp:147` | YES `:381` | (b) | snapshot |
| 6 | `Top Bar` | `DashboardPanels.hpp:284` | YES `:382` | (b) | snapshot |
| 7 | `Market` | `DashboardPanels.hpp:333` | YES `:383` | (b) | snapshot |
| 8 | `Buy Gate` | `DashboardPanels.hpp:551` | YES `:384` | (b) | snapshot |
| 9 | `Account` | `DashboardPanels.hpp:1015` | YES `:385` | **(c)** | snapshot; balance/realized/fees ← OMS `PERSIST` rows (`MemHeaders/OmsFieldRegistry.hpp:258,:262`) |
| 10 | `Config` | `DashboardPanels.hpp:1266` | no | **(d) DEAD** | `GUI_Panel_Config` has **zero callers** repo-wide (verified `rg --no-ignore`; only CODE_MAP + its own defn). Never renders. H21 dead-code |
| 11 | `Positions` | `DashboardPanels.hpp:1326` | YES `:386` | **(c)** | snapshot `positions[]`; source `active_bitmap` + `positions[]` are persist rows (`ShardedSnapshotPersist.hpp:180,:185`) |
| 12 | `Per-Node P&L` | `DashboardPanels.hpp:1660` | **no** | **(d)** | GUI-process-local ring `pnl_history[1800][16]` (`:1625-1627`) sampled 1 Hz from `snap->per_node[c].node_realized`. **Ring is process-local → always empty at launch**, even though `node_realized` itself is a persist row |
| 13 | `Stats` | `DashboardPanels.hpp:1733` | YES `:389` | **(c) SPLIT — the defect** | see § 1.1 |
| 14 | `Latency` | `DashboardPanels.hpp:1835` | YES `:391` | (b) | `#ifdef LATENCY_PROFILING`-gated (`:1823`). **ON in her build** (`build_gui/CMakeCache.txt:208`) — renders |
| 15 | `ML Intelligence` | `DashboardPanels.hpp:1918` | YES `:390` | (b)+(c) | snapshot; confidence/prediction fields are persist rows (`NodeCtxPersistRegistry.hpp` `staged_prediction`/`active_prediction`/`last_confidence`/`confidence` delegate) |
| 16 | `Risk` | `DashboardPanels.hpp:2123` (inline in `GUI_RenderDashboard`) | **no** | **(c)** | snapshot; `node_peak_balance`/`node_kill_tripped`/`node_ks_trips_total` are persist rows |
| 17 | `Per-Node Latency` | `DashboardPanels.hpp:2248` (inline) | **no** | **(b)** | snapshot per-node latency; never persisted (in-RAM `NodeLatencyStats`) |
| 18 | `Engine Topology` | `DashboardPanels.hpp:2417` (inline) | **no** | **(b)** | snapshot topology block |
| 19 | `Trade History` | `GUI/TradeHistoryPanel.hpp:267` | YES `:393` | **(a)** | `logging/btcusdt_order_history.csv`, `stat()`-size-gated reload (`:120-123`) |
| 20 | `Strategy Quality` | `GUI/StrategyQualityPanel.hpp:345` | **no** | **(a)** | `logging/health.jsonl` — **engine writes it only if `health_log_path` is set; it is NOT set in her `engine.cfg`** (default `''` at `ControllerConfig.hpp:2112`) |
| 21 | `Settings` | `GUI/SettingsPanel.hpp:1999` | YES `:392` | **(a)** | `engine.cfg`; `Settings_Load` runs **once** (`:2001` `if (!s->loaded)`) |
| 22 | `Engine Log` | `GUI/LogViewerPanel.hpp:129` | YES `:394` | **(a)** | `logging/engine.log`, `stat()`-gated (`:86-90`) |
| 23 | `ML Status` | `GUI/MLStatusPanel.hpp:39` | **no** | (b) | snapshot + `shared` |
| 24 | `Engine` | `GUI/EngineHeaderPanel.hpp:37` | **no** | (b)+(d) | `ENGINE_VERSION_STRING` compile-time const + `snap->source_cfg_path` |

### 1.1 The `Stats` panel is TWO counter families rendered as one row

`GUI_Panel_Stats` (`DashboardPanels.hpp:1732-1816`) reads six snapshot fields with **two different provenances**:

| Rendered as | Snapshot field | Publisher | Provenance | Persisted? |
|---|---|---|---|---|
| `buys: N` / `(N fills)` | `total_buys` | `ShardedSnapshot.hpp:316` ← `agg.total_entries` ← `EventLoopAggregates.hpp:135` ← `state->total_entries` | **GLOBAL heartbeat** | **NO** |
| `(N fills)` on exits | `total_exits_fills` | `ShardedSnapshot.hpp:317` ← `state->total_exits` | GLOBAL heartbeat | **NO** |
| `exits: N` (headline) | `wins + losses` | `ShardedSnapshot.hpp:866-867` ← Σ `state->nodes[i].node_wins/node_losses` (`:418-419`) | **PER-NODE** | **YES** |
| `W:` / `L:` / `rate:` | same | `:866-872` | PER-NODE | **YES** |
| `pf:` / `avg W:` / `avg L:` / `E[trade]` | ← Σ `node_gross_wins/node_gross_losses` (`:420-421`) | `:874-886` | PER-NODE | **YES** |
| `maxDD` | `max_drawdown` ← `agg.peak_balance − agg.equity` (`EventLoopAggregates.hpp:164`) ← `state->oms->ks_peak_balance` (`:131`) | OMS | **YES** (`OmsFieldRegistry.hpp:258`) |

The per-node family is on the wire at v11 — `MemHeaders/NodeCtxPersistRegistry.hpp` rows `entries_processed`, `exits_processed`, `node_realized`, `node_fees`, `node_open_notional`, `node_wins`, `node_losses`, `node_gross_wins`, `node_gross_losses`, `partner_pending_pnl`, `idle_cycles`, all `COMMIT`.

The GLOBAL family is **zeroed at `EventLoopState_Init`** (`ControllerEventLoop.hpp:1121-1122`), bumped live at `:1696`/`:1792`, and appears in **no** wire row.

### 1.2 Why `Per-Node P&L` / `Per-Node Latency` / `Risk` / `Engine Topology` / `ML Status` / `Engine` / `Strategy Quality` are absent from the dock-builder

`Gui_SetupDefaultLayout` runs **once, only when no saved layout exists** (`GuiThread.hpp:476-484`). It is a hand-maintained list, not registry-driven — every panel added after the list was last touched simply never got a row. Consequence: on a machine with no `foxml_gui.ini`, those 7 windows float free. Once the operator docks them, `io.IniFilename = "foxml_gui.ini"` (`GuiThread.hpp:174`) persists it. Her `/home/caramel/code/FoxML_Trader_v2/foxml_gui.ini` confirms she has docked all of them.

**But that ini also carries the fossil evidence of a real persistence break:** it contains BOTH `[Window][Per-Core P&L]` / `[Window][Per-Core Latency]` (orphaned) AND `[Window][Per-Node P&L]` / `[Window][Per-Node Latency]`. Commit `baf5e5a` *"wip(.E.1.1): vocab sweep — operator-facing core->node strings (#13)"* renamed those two ImGui window titles. **An ImGui window title IS the persistence key in the ini.** The rename orphaned the saved dock state, and those two panels lost their layout at that ship — an H21-shaped move (a persistence-visible identifier renamed rather than tombstoned). This does *not* explain the Trade History/Stats complaint (neither was renamed) but it is a literal instance of "a panel not persistent between sessions."

---

## § 2. THE LIFECYCLE MATRIX

Columns: **(i)** restart with warm-restart snapshot load **succeeding** · **(ii)** restart with **no/refused** snapshot · **(iii)** **Reset Paper**.

### 2.0 First — the two gating questions the directive asked, answered

**Q: does the warm-restart snapshot load actually run in PAPER mode?**
**YES — verified.** `CoreFrameworks/EngineSharded/Run.hpp:1062-1073`:
```text
const char* snapshot_path = "data/sharded_snapshot.dat";
mkdir("data", 0755);
if (!live_trading) {
    int loaded = ShardedSnapshot_Load<F>(&state, snapshot_path,
                  BITMAP_IS_SET(oms.oms_state_flags, tt::MASK_OMS_STATE_PARTIAL_EXIT_ENABLED), &cfg);
```
*(fence retagged cpp→text at save: a verbatim QUOTE of `Run.hpp:1062-1073`, not a compilable sample — B-Plus compile-probe exclusion; content unchanged)*
The directive's line-range guess (`1065-1073`) is correct; the gate is `!live_trading` → **paper is the branch that loads**. Live goes to exchange reconciliation instead.

**BUT the load is `refuse-don't-migrate` behind FIVE gates** (`CoreFrameworks/ShardedSnapshotPersist.hpp`), any one of which silently drops the whole restore:

| Gate | Line | Trigger | Fired in her logs? |
|---|---|---|---|
| truncated-at-magic | `:281-284` | short file | no |
| legacy TICK magic | `:287-292` | old PortfolioController snapshot | no |
| magic mismatch | `:293-298` | wrong file | no |
| **version mismatch** | `:299-303` | `version != SHARDED_SNAPSHOT_VERSION` | **YES — `engine.log.1`: "version 8 != current 10"** |
| node-count mismatch | `:307-312` | `num_execution_nodes` changed | no |
| **partials-geometry mismatch** | `:319-334` | `partial_exit_enabled` toggled since save | **YES — `engine.log` today** |

**Q: do restored W/L counters reach the TUISnapshot the Stats panel reads, or is there a gap?**
**No gap on the per-node family — but a total gap on the global family, and it is a Class-45 shape.**

- Restored per-node values commit into `state->nodes[i]`, and `TUI_CopySnapshotSharded` re-derives `snap->wins/losses/avg_*/pf/expectancy` from `state->nodes[i].node_wins/...` on **every publish** (`ShardedSnapshot.hpp:418-421`, `:866-886`). No staleness, no gap. **W/L survives a successful load.**
- `snap->total_buys` reads `state->total_entries`, which **no restore path writes**:
  - `ShardedSnapshot_Load` — no global-counter block exists (grep for `total_entries` in `CoreFrameworks/` returns only the aggregates read, the paper-reset zeroing, the summary emit, and two shutdown printfs — never a persist row).
  - `EventLoopState_ReconstructPerCoreFromEventLog` (`ControllerEventLoop.hpp:1004-1067`, called at `EventLoopState_Init:1163`) bumps **`state->nodes[node_id].entries_processed`** (`:1036`) and **`state->nodes[node_id].exits_processed`** (`:1050`) — **never `state->total_*`**.
  - `EventLoopState_Init:1121-1122` zeroes them, and the reconstruct at `:1163` runs *after*.

**This is Class 45 verbatim: the reconstruct path writes a different counter than the forward path's display consumer reads.** Proof it bites in production, from her own archive `data/paper_resets/2026-05-13-223040_to_2026-05-13-223714.paper/summary.json`:
```json
"total_entries":0, "total_exits":8
```
Eight exits with zero entries — arithmetically impossible for a real session; it is the signature of the global family starting at 0 while the per-node family carried the restored state.

### 2.1 The matrix

| Panel | (i) restart, snapshot LOADS | (ii) restart, no/refused snapshot | (iii) Reset Paper |
|---|---|---|---|
| **Trade History** | **SURVIVES** — CSV opened append (`ShardedTradeLog.hpp:235` `fopen(filename,"a")`), header written only when empty (`:246`). Her file spans 2026-05-13→2026-08-13 in one file, proving cross-session accumulation | **SURVIVES** — identical; the CSV is orthogonal to the snapshot | **CLEARED** — `ShardedTradeLog_Rotate` (`:339`) renames to `logging/SYMBOL_order_history.YYYYMMDD-HHMMSS.csv` (`:361-366`), then re-`_Init`s a fresh file. Panel reloads on size change (`TradeHistoryPanel.hpp:122`) → goes blank. **BY DESIGN** (`ShardedTradeLog.hpp:404-406`) |
| **Stats — `buys` / `(N fills)`** | **LOST → 0.** No wire row; not rebuilt by replay (§ 2.0) | **LOST → 0** | **LOST → 0** (`Async.hpp:723-724` `state.total_entries = 0; state.total_exits = 0;`) |
| **Stats — `exits`/`W`/`L`/`rate`/`pf`/`avg W`/`avg L`/`E[trade]`** | **SURVIVES** — persist rows → `state->nodes[i]` → re-summed each publish | **PARTIAL** — rebuilt from `logging/order_events.bin` replay only (`ControllerEventLoop.hpp:1053-1055`), and **per-LEG not per-PAIR** (the A6 parity divergence already homed in EV-1). Zero if the event log was reset | **CLEARED** — `NODE_CTX_RESET_AUTOPOPULATE` per node (`Async.hpp:~735`) |
| **Stats — `maxDD`** | **SURVIVES** — `ks_peak_balance` PERSIST row (`OmsFieldRegistry.hpp:258`) → `EventLoopAggregates.hpp:131` | LOST (peak resets to starting balance) | **CLEARED** — `ks_peak_balance` is `DO_RESET` |
| **Account** (balance/realized/fees) | **SURVIVES** — OMS PERSIST rows | **PARTIAL** — `OrderEventLog` replay restores balance (`[OMS] replayed 4 events, balance=$10000.00`) | **CLEARED** — `OMS_RESET_AUTOPOPULATE(state.oms, cfg.starting_balance)` |
| **Positions** | **SURVIVES** — `active_bitmap`+`positions[]` restored + ExecutionCore re-activated (`ShardedSnapshotPersist.hpp:~670-690`) | **PARTIAL** — re-opened via event-log replay (her session: 4 positions from 4 replayed BUYs) | **CLEARED** + `nodes[c].active = 0` |
| **Risk** (kill switch) | **SURVIVES** — `node_peak_balance`/`node_kill_tripped`/`node_ks_trips_total` persist rows | LOST | **CLEARED** |
| **ML Intelligence / ML Status** | **SURVIVES** — confidence + prediction persist rows | LOST | **CLEARED** |
| **Per-Node P&L** (chart) | **NO** — the ring is a GUI-process `static` (`DashboardPanels.hpp:1625-1627`); it starts empty every launch regardless. `node_realized` (the *source*) survives, so the plot re-grows from the restored level | NO | NO (also ring-cleared via `paper_reset_seq`, `:1640`) |
| **Per-Node Latency / Latency / Engine Topology** | **NO** — in-RAM only, never persisted | NO | NO |
| **Equity Curve / chart markers** | N/A — **always empty** (F-1) | N/A | N/A |
| **Engine Log** | **NO — by design.** `main.cpp:82-88` renames the old log to `.1` then `freopen(log_path, "w", stderr)` **truncates**. The panel reads `logging/engine.log` only; `.1` is unreachable from the GUI | NO | unaffected (no rotation on reset) |
| **Settings** | SURVIVES (reads `engine.cfg`) — but `Settings_Load` runs once per GUI process (`SettingsPanel.hpp:2001`), so it is stale vs any engine-side hot-reload | same | same |
| **Strategy Quality** | reads `logging/health.jsonl` — **never written under her cfg** (`health_log_path` unset) | same | same |
| **Dock layout (all windows)** | SURVIVES via `foxml_gui.ini` — **except any window whose TITLE was renamed** (§ 1.2) | same | same |

---

## § 3. THE HARDCODED-PATH COHORT SWEEP (M9 — the SET, enumerated)

Sweep scope: `GUI/*.hpp`, `foxml_suite.cpp`, `main.cpp`. Every path/symbol literal, with a runtime-conformance verdict.

| # | Site | Literal | What the engine actually does | Conforms today? | Verdict |
|---|---|---|---|---|---|
| **P1** | `GUI/GuiThread.hpp:83` (`FOREACH_PANEL` row) | `"logging/btcusdt_order_history.csv"` | `ShardedTradeLog_Init(&g_sharded_trade_log, bcfg.symbol)` (`Run.hpp:791`) → `logging/%s_order_history.csv` (`ShardedTradeLog.hpp:222-223`) with `symbol` = `engine.cfg:19` | **YES today** (`symbol=btcusdt`) | **LATENT NON-CONFORMER.** Any other symbol ⇒ Trade History reads a file the engine never writes. `.E.1` multi-exchange makes this reachable |
| **P2** | `GUI/GuiThread.hpp:459` | `"logging/btcusdt_order_history.csv"` (`TradeData_Init`) | same | **YES today**, same latency | **SECOND COPY of P1** — Class-18 mirror. `ShardedTradeLog_FormatPerCoreFilename` (`ShardedTradeLog.hpp:130`) exists as an SSoT for the *per-node* pattern; the *aggregate* pattern has no helper and is open-coded at 4 sites (`ShardedTradeLog.hpp:222`, `:355`, `Async.hpp:669`, and these two GUI literals) |
| **P3** | `GUI/GuiThread.hpp:84` | `"logging/engine.log"` | `snprintf(log_path, "logging/%s", bcfg.log_file)` (`main.cpp:85`); `log_file` is cfg-settable (`engine.cfg:184`) | **YES today** (`log_file=engine.log`) | **LATENT NON-CONFORMER** — cfg-driven, GUI-hardcoded |
| **P4** | `GUI/GuiThread.hpp:85` | `"engine.cfg"` (`Settings_Init`) | `const char *cfg_path = (argc > 1) ? argv[1] : "engine.cfg"` (`main.cpp:70`) | **NO if launched with an argv cfg** | **ACTIVE NON-CONFORMER (conditional).** Launch `engine_gui alt.cfg` ⇒ the Settings panel reads *and writes* `engine.cfg` while the engine runs `alt.cfg`. **Class 2 (display↔execution) + a live mis-edit path.** Worse: the engine ALREADY publishes the truth — `snap->source_cfg_path` (`ShardedSnapshot.hpp:170-173`), rendered by `EngineHeaderPanel.hpp:60-64`. The panel that *edits* the cfg ignores the field the panel that *displays* it uses. **Class 45** |
| **P5** | `GUI/GuiThread.hpp:86` + `:547` | `"logging/health.jsonl"` (twice) | `cfg.health_log_path`, default `''` = disabled (`ControllerConfig.hpp:2112`); **absent from her `engine.cfg`** | **NO — engine writes nothing** | **NON-CONFORMER.** Also makes `StrategyQualityPanel.hpp:259-262`'s `"health_log_path not configured"` branch **dead code** (the GUI always passes a non-empty literal), so the panel shows the wrong diagnostic ("no health log yet at …") instead of "not configured" |
| **P6** | `GUI/ChartPanel.hpp:257` | `"BTCUSDT  $%.2f"` | symbol is cfg-driven | **YES today** | **LATENT NON-CONFORMER (display).** Note: **`TUISnapshot` has NO symbol field at all** (`rg "symbol" DataStream/EngineTUI.hpp` → zero hits) — so there is currently *no* correct source available to the GUI. Fixing P1/P2/P6 requires ADDING a snapshot field first |
| P7 | `GUI/GuiThread.hpp:174` | `"foxml_gui.ini"` | GUI-owned artifact | YES | conforms (GUI owns it) |
| P8 | `GuiThread.hpp:227` / `SettingsPanel.hpp:2035,:2039-2040,:2046` | `"data/foxml_gui_state.txt"` (+`.tmp`) | GUI-owned | YES | conforms — 4 sites, single logical file, mild Class-18 shape |
| P9 | `foxml_suite.cpp:126-127` | `"logging/foxml_suite.log"` / `".log.1"` | suite-owned | YES | conforms |
| P10 | `foxml_suite.cpp:174` | `"foxml_suite.ini"` | suite-owned | YES | conforms |
| P11 | `foxml_suite.cpp:213` | `"data/foxml_gui_state.txt"` | shared with GUI | YES | conforms (5th copy of P8) |
| P12 | `foxml_suite.cpp:286` | `"logging/foxml_suite.log"` | suite-owned | YES | conforms (2nd copy of P9) |
| P13 | `foxml_suite.cpp:298,:302,:334-335` | `"backtest.cfg"` / `"engine.cfg"` | suite-owned + engine cfg | partial | same argv-blindness class as P4 |

**Answer to "is `btcusdt` the only one?" — NO. There is a cohort of 6 engine-facing path literals (P1–P6), of which:**
- **1 is an ACTIVE non-conformer today**: **P5** (`health.jsonl` — engine writes nothing).
- **1 is an ACTIVE conditional non-conformer**: **P4** (`engine.cfg` vs argv), and it is the most dangerous because the panel *writes*.
- **4 are LATENT** (P1, P2, P3, P6), all keyed on cfg-settable values that happen to match right now.

**The structural shape:** the GUI's engine-facing paths are **literals in a registry**, while every one of them is **cfg-derived at runtime**. There is no published channel for three of the four (`symbol` isn't in the snapshot at all; `log_file` isn't; `health_log_path` isn't) — only `source_cfg_path` is published, and the panel that needs it ignores it.

---

## § 4. THE ARCHIVE STORY

**Where the history physically goes on Reset Paper** (handler at `CoreFrameworks/EngineSharded/Async.hpp:~600-765`):

1. **Archive dir** — `data/paper_resets/{start_iso}_to_{end_iso}.paper` (`PaperResetArchive_FormatDirname`, `PaperResetArchive.hpp:112-119`; `start_iso` from `oms->paper_session_start_us`, `end_iso` from wall clock; format `%Y-%m-%d-%H%M%S`).
2. **`snapshot.dat`** — `ShardedSnapshot_Save` into the archive dir.
3. **`trades.csv`** — byte copy of `logging/<SYMBOL>_order_history.csv` (`Async.hpp:667-673`).
4. **`trades/node_<N>.csv`** — copies of the per-node mirrors (`Async.hpp:684-689`). *(Stale comments at `Async.hpp:635` and `:675` still say `core_<N>.csv`; the operator's existing archive on disk really does contain `core_N.csv` because it predates the rename.)*
5. **`summary.json`** — `Summary_WriteJson` (`PaperResetArchive.hpp:166-245`): session / global / per_node / per_strategy blocks, `per_regime: []` placeholder.
6. **Then** the live CSV is rotated away: `ShardedTradeLog_Rotate` → `logging/<SYMBOL>_order_history.YYYYMMDD-HHMMSS.csv` (`ShardedTradeLog.hpp:361-366`) + per-node `logging/<SYMBOL>_node_<N>_order_history.YYYYMMDD-HHMMSS.csv` (`:384-388`).
7. `OrderEventLog_Reset` truncates `logging/order_events.bin`; `shared_ptr->paper_reset_seq++` (`Async.hpp:760`).

So after a reset the history exists in **two** places: the archive copy and the timestamped rotation. Her disk confirms both — `data/paper_resets/2026-05-13-223040_to_2026-05-13-223714.paper/` (complete, with a valid `summary.json`) and `logging/btcusdt_order_history.20260513-223714.csv`.

**Is there ANY GUI surface that can read an archived session?**

**NO. Stated plainly: zero.** `rg -n "paper_resets|summary\.json|trades\.csv|archive" GUI/ foxml_suite.cpp Backtest/` returns **nothing**. There is no archive browser, no session picker, no date-range selector, no `.paper` directory reader anywhere in the GUI or the suite. Every archived session — snapshot, trades, and the fully-populated `summary.json` — is write-only from the operator's seat; the only way to see it is a shell.

**Assessment:** the engine has a *complete, correct, structured* session-archive system that produces exactly the artifact a "past sessions" tab would consume, and no consumer was ever built. **"Surface the archives" is a strictly better-specified ask than "make it persist"** — the data already persists, in a better form than the live CSV, and is 100% invisible. Note also that `paper_reset_seq` bumps a counter whose *only* consumer is one ring-buffer clear (`DashboardPanels.hpp:1640`) — the notification channel for "a session boundary happened" exists and is nearly unused.

---

## § 5. ROOT-CAUSE VERDICT — ranked by evidence

### RANK 1 — `Trade History` empty because ZERO EXITS EVER COMPLETED (working-as-designed reader semantics, meeting a real trading outcome)
**Evidence: direct, from her disk.**
- `logging/btcusdt_order_history.csv` = 12 lines: 2 header + **10 `E` rows, 0 `X` rows** (`awk -F, 'NR>2 {print $4}' | sort | uniq -c` → `10 E`).
- `TradeHistoryPanel.hpp:166` — `if (kind_s[0] != 'X') continue;` — the panel renders **only exits**.
- `:271-274` — `count == 0` ⇒ literally prints `"no completed trades yet"`.
- Corroborated by `engine.log`: `entries=0 exits=0`, `total submitted: 0, total filled: 0`.
- Her three *archived* CSVs all contain `X` rows (3/6/8) — so the panel *did* work historically.

**This is the dominant cause and it is NOT a persistence failure at all.** The file persists perfectly (it spans 2026-05-13 → 2026-08-13 in one append-mode file). She is seeing a panel that only shows round-trips, during a stretch with no round-trips. **Already partially homed** as the EV-1 "Trade History shows nothing while positions are open" lane — and **this report answers that lane's open DISCRIMINATOR**: it is the semantics gap, not the filename split (the filename hypothesis is refuted, § 0.2).

### RANK 2 — `Stats` `buys` counter is structurally unrestorable (GENUINE DEFECT, Class 45)
**Evidence: code-complete chain + a production artifact.**
- `state->total_entries/total_exits` zeroed at `ControllerEventLoop.hpp:1121-1122`; no persist row; not rebuilt by `EventLoopState_ReconstructPerCoreFromEventLog` (`:1036`/`:1050` bump per-node only).
- Live proof: `summary.json` reads `"total_entries":0,"total_exits":8`.
- Live proof #2: today's session replayed 4 BUY events and held 4 open positions, yet reported `entries=0`.

**Already homed** in EV-1 ("Stats-bar zeros on warm-restart… the ONE counter family neither persisted nor rebuilt"). **My addition:** the recommended fix there (*"re-source the stats plane from the persisted per-node sums"*) is confirmed viable — `entries_processed`/`exits_processed` are already `COMMIT` rows in `NodeCtxPersistRegistry.hpp` and already summed for a different display, so no wire change is needed. **Ranked 2, not 1**, because with W=L=0 in her session, the *whole* Stats row reads zero regardless of this defect.

### RANK 3 — the warm-restart snapshot REFUSED on both logged boots (GENUINE, but a correctness guard doing its job — with a compounding hazard)
**Evidence: her logs, verbatim.** Version mismatch (`8 != 10`) on one boot; partials-geometry mismatch (`written with partial_exit_enabled=0, current cfg=1`) on the next. Gates at `ShardedSnapshotPersist.hpp:299-303` and `:319-334`.

The refusals are **correct** (a zombie-position restore is far worse). But three things compound:

- **3a.** `engine.cfg` contains **THREE `partial_exit_enabled` lines** (`:294` `=1`, `:296` `=0`, `:298` `=1`). The parser is a single-pass line loop with no break (`ControllerConfig.hpp:2464-2490`) ⇒ **LAST-WINS**. `cfg_write_field` rewrites the **FIRST** match (`SettingsPanel.hpp:889-903`, `pos` set on first line-anchored hit, then `break`). **A GUI edit to a duplicated key is silently inert** — Class 2. And the duplicate set is not one key: `node_1_offset_stddev_mult`, **`node_3_stop_loss_pct`**, `partial_exit_enabled`. A duplicated **stop-loss** override is capital-relevant.
- **3b.** The refusal is followed by an **unconditional save at shutdown** (`engine.log`: `[snapshot] final save: data/sharded_snapshot.dat`, and `4 position(s) open on shutdown — persisting via snapshot`). So a refused load still clobbers the file. Any oscillating `partial_exit_enabled` produces a **refuse-every-boot loop**.
- **3c.** During a period where `SHARDED_SNAPSHOT_VERSION` is being bumped (10→11 landed at `4277e14`/`1d3c797`), *every* stale snapshot refuses — expected, and correct per H21, but it means the operator's felt experience of "state doesn't persist" is partly the in-flight wire work.

### RANK 4 — `Equity Curve` + chart CSV trade markers are PERMANENTLY EMPTY (GENUINE DEFECT — reader parses a format the writer stopped emitting)
**Evidence: format-level, decisive.**
`GUI/TradeReader.hpp:185-206` documents and parses the **legacy `TradeLog.hpp`** schema:
```
// 0:tick, 1:side, 2:price, 3:quantity, 4:entry_price, ... 14:fee_cost ...
csv_field(line, 1, side, ...);            // :201
...
if (strcmp(side, "BUY") == 0)  { ... }    // :212
else if (strcmp(side, "SELL") == 0) { ... } // :221
```
The sharded writer emits (`ShardedTradeLog.hpp:27-28`, `TradeLogColRegistry.hpp:38`, confirmed on disk):
```
timestamp_us,core_id,strategy_id,event_type,price,entry_price,exit_price,pnl,fees,balance_after,trade_size,regime,regime_name
1778729880670964,4,5,E,79290.01000000,...
```
Column 1 is a **node id integer**, never `"BUY"`/`"SELL"` ⇒ both branches are unreachable ⇒ `marker_count` and `equity_count` stay **0 forever**. `GUI_EquityChart` then early-outs at `ChartPanel.hpp:1478` (`if (trades->equity_count < 1)`), and the marker loop at `:1528-1532` iterates zero times. Additionally `TradeData_Refresh:197` skips exactly one header line while the sharded file has **two**.

**This is Class 44 (computed-but-discarded) + Class 45 (two readers of one file diverged).** Note the sister reader `TradeHistoryPanel.hpp:129-140` was migrated to the v3 sharded format and its comment explicitly says *"No header row in the sharded log — no skip-first"* — `TradeReader.hpp` was **left behind**. `TradeData_Refresh` is called every frame (`GuiThread.hpp:522`), doing a full file re-read on every size change, to produce nothing. **This is a NEW finding — not in EV-1, not in EV-2, not in TECH_DEBT.**

### RANK 5 — `Trade History` silently caps at the OLDEST 256 exits (GENUINE DEFECT, latent-but-inevitable)
`TradeHistoryPanel.hpp:57` `MAX_HISTORY = 256`; `:167` `if (th->count >= MAX_HISTORY) break;` — the reader walks the file **from the top** and **breaks**, keeping the **first** 256 `X` rows. The render loop at `:307` (`for (int i = th->count-1; i >= 0; i--)`) is commented *"render newest first"* — but "newest" is the 256th-**oldest** exit once the file exceeds the cap. Because the CSV is append-only across all sessions and is only ever cleared by Reset Paper, **the panel freezes on ancient trades and stops showing new ones entirely** past 256 exits. That presents *exactly* as "trade history doesn't update between sessions." Same shape in `TradeReader.hpp:21`/`:198` (`MAX_TRADES = 512`), currently masked by RANK 4.

### RANK 6 — `Engine Log` panel is single-session by construction (working-as-designed, undocumented to the operator)
`main.cpp:82-88`: rename old → `.1`, then `freopen(log_path, "w", stderr)` **truncates**. The panel reads only `logging/engine.log` (`GuiThread.hpp:84`). Prior sessions live in `engine.log.1`, unreachable from the GUI. If the operator's "not persistent between sessions" impression is partly formed by the Log tab, this is why.

### RANK 7 — `foxml_gui.ini` layout orphaned by window-title renames (GENUINE, already-fired, one-time)
Commit `baf5e5a` renamed `Per-Core P&L`→`Per-Node P&L`, `Per-Core Latency`→`Per-Node Latency`. The ini keys off the title; both old sections are still present as orphans in `/home/caramel/code/FoxML_Trader_v2/foxml_gui.ini`. Those two panels lost their saved dock position at that ship. **Does not explain Trade History/Stats** (never renamed) but is the one mechanism that is *literally* "a tab not persistent between sessions."

### Explicitly SEPARATED — working-as-designed, do not conflate
- **Reset Paper clearing Trade History** is deliberate (`ShardedTradeLog.hpp:404-406`, `Async.hpp` comment *"so the GUI's Trade History panel goes blank instead of mixing pre-reset rows with new ones"*). If she pressed Reset Paper, blank is correct — and the data is in the archive (§ 4).
- **The snapshot refusals** are guards working. The defect is the *compounding* (3a/3b), not the refusal.
- **`Per-Node P&L` starting empty** is inherent to a process-local ring, not a persistence bug.

---

## § 6. E.1.2 ENTANGLEMENT CHECK — one adjacency, NAMED AND STOPPED

Per the scope fence I stopped at the boundary rather than reasoning into it:

- **`MemHeaders/NodeCtxPersistRegistry.hpp` is in-flight E.1.2 scope** (v11 wire, `partner_pending_pnl` on / `node_dd_pct` off, D-420/AM-4, 29-row count-lock + frozen golden). I **read** it to establish which counters persist. I make **no proposal** touching it.
- **The RANK-2 fix direction stays clean of it**: re-sourcing the Stats plane from `entries_processed`/`exits_processed` uses rows that **already exist** as `COMMIT` at v11 — a publisher-side change in `CoreFrameworks/ShardedSnapshot.hpp`, **zero wire delta, zero version bump, zero golden regen**. Consistent with EV-1's own "no wire change" note and with the prior I-class § 10 clean verdict.
- **RANK 3's snapshot-version refusals intersect E.1.2 temporally** (10→11 in flight) but not architecturally — the gate is correct and the paired-bump rule is already the guard.
- **`ShardedSnapshotPersist.hpp` / `Portfolio_Save/_Load` retirement / F-096: NOT ENTERED.** I read only the refusal gates (`:281-334`) to answer the load-gating question.

**Everything in RANKS 1, 4, 5, 6, 7 and the entire § 3 cohort is monitoring/display-plane — no persist wire, no HMAC body, no hot path.**

---

## § 7. RECONCILIATION WITH THE PRIOR ART (explicit overlap flags)

Both frozen reports in `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/reports/2026-08-14-ui-position-settings-mismatch/` were read in full before investigating.

| My finding | Status vs prior art |
|---|---|
| Stats global-counter family unrestorable (RANK 2) | **KNOWN** — `i-class-positions-legcount-attribution.md` § 5(a); homed EV-1. **I ADD:** production proof (`summary.json` `entries:0/exits:8`), and confirmation that the recommended fix needs no wire change |
| Snapshot load gating in paper mode | **OPEN QUESTION ANSWERED** — that report's refute-spot #6 asked *"does paper mode load the v10 snapshot unconditionally?"* → **it loads in paper (`Run.hpp:1065`) but behind 6 refuse gates, and BOTH of her logged boots refused** |
| Trade History empty — semantics vs filename | **DISCRIMINATOR ANSWERED** — roadmap EV-1 (`:706-715`) left it open. **Semantics gap; filename-split REFUTED; the hypothesis came from a stale comment** (`ShardedTradeLog.hpp:36`,`:291`) |
| `engine.cfg` duplicate keys / first-write-vs-last-read | **NEW.** Adjacent to EV-2's D-1/D-9 (both `cfg_write_field`) but a distinct mechanism, and it now involves `node_3_stop_loss_pct` |
| **`TradeReader.hpp` format drift → dead Equity Curve (RANK 4)** | **NEW** — not in EV-1, EV-2, TECH_DEBT, or PARITY_ISSUES |
| **Trade History 256-cap keeps the OLDEST (RANK 5)** | **NEW** |
| **`GUI_Panel_Config` dead (§ 1 #10)** | **NEW** — H21 dead-code |
| **P4 `engine.cfg` vs argv (§ 3)** | **NEW** — extends EV-2's cfg-writer surface |
| **P5 `health.jsonl` + dead "not configured" branch** | **NEW** |
| **Window-title rename orphaning `foxml_gui.ini` (RANK 7)** | **NEW** — H21-shaped |
| `partial_exit_enabled` has no per-node override | **CONFIRMS** prior refute-spot #4 — it is a **global** cfg row (`LifecycleCfgFlagRegistry.hpp:39`), which is why the snapshot geometry gate can be a single byte |

Per the operator directive recorded in the handoff (`2026-08-14-E.1.2-steps3-5-v11-delta-handoff.md:90,:160`), spot-check findings route to **PLAN homes, not TECH_DEBT**. Every NEW item above is display/monitoring-plane and lands naturally under **EV-1** (counter/display truth) or a **new EV-3** (GUI file-backing conformance: § 3 cohort + RANK 4 + RANK 5 + RANK 6 + RANK 7 + the archive-viewer ask). That routing call is the orchestrator's, not mine.

---

## § 8. HAZARDS

- **H-1 (HIGH, capital-adjacent).** `engine.cfg` carries duplicated keys including **`node_3_stop_loss_pct`**. Parser last-wins (`ControllerConfig.hpp:2464-2490`) vs writer first-match (`SettingsPanel.hpp:889-903`) ⇒ a GUI stop-loss edit on node 3 is **silently inert**. No guard detects duplicate keys anywhere.
- **H-2 (MED).** Refused snapshot load is still followed by an unconditional shutdown save. An oscillating `partial_exit_enabled` (which H-1 makes *more* likely, since the operator cannot reliably change it from the GUI) yields a permanent refuse-every-boot loop.
- **H-3 (MED).** `Trade History` past 256 exits freezes on the **oldest** 256 with no operator-visible signal — it looks identical to "history stopped updating."
- **H-4 (MED).** `Equity Curve` renders its empty-state indistinguishably from "no trades yet," concealing a total format break. Cross-session, cumulative-P&L operator judgment has been reading a permanently blank chart.
- **H-5 (LOW-MED).** Launching `engine_gui <alt.cfg>` makes the Settings panel edit the *wrong file*, while the Engine panel simultaneously displays the *right* path from `snap->source_cfg_path`. Two panels, two truths, one screen.
- **H-6 (LOW).** The trade CSV header is written **only when the file is empty** (`ShardedTradeLog.hpp:246`). Her live aggregate still says `core_id` in column 1 while the registry now emits `node_id` (`TradeLogColRegistry.hpp:38`). Both GUI readers parse by index so it is inert *for them* — any name-parsing consumer (a future archive viewer, a pandas script) breaks.
- **H-7 (process).** **No mechanical guard covers this surface.** `calls_graph_diff.sh` is scoped to strategy/regime symbols (missed the dead `GUI_Panel_Config`); `scan_class_44_cfg_orphan.py` covers cfg *flags*, not GUI *path literals*; `check_cfg_key_prefix_drift.py` covers per-node prefixes, not writer-target-file identity. The EV-2 leaf's promised `check_gui_engine_cfg_key_parity.py` (still unbuilt) would cover *keys*, not *paths*. A "GUI file-literal ⊆ engine-written-path" check has no owner.
- **H-8 (stale records — arming § 2.5, surface these regardless of path).**
  - `CoreFrameworks/ShardedTradeLog.hpp:36` and `:291` — claim `SYMBOL_sharded_order_history.csv`; **code writes `SYMBOL_order_history.csv`**. This stale comment actively misled a prior investigation into a wrong hypothesis. Suggested wording: `// Filename convention: logging/SYMBOL_order_history.csv (the "_sharded_" name was retired; per-node mirrors are logging/SYMBOL_node_<N>_order_history.csv)`.
  - `CoreFrameworks/EngineSharded/Async.hpp:635` and `:675` — say `<dirname>/trades/core_<N>.csv`; code writes `node_%d.csv` at `:688-689`.
  - `GUI/GuiThread.hpp:65-68` — the FOREACH_PANEL comment lists "Stateless panels (… Latency, ML Intelligence, … the ~11 dashboard panels)"; the real count is 14 stateless windows + 1 dead one, and `Config` is not mentioned as dead.
  - `GUI/TradeReader.hpp:185-189` — the column legend describes a schema no writer produces.

---

## § 9. SPOTS MOST WORTH AN ADVERSARIAL REFUTE (for the paired a-class)

1. **RANK 4 is my highest-confidence NEW claim and it is code-read only — refute it empirically.** Run `bin/engine_gui` against the existing `logging/btcusdt_order_history.csv` (which has `E` rows) and confirm the Equity Curve shows "(no equity data)" and the price chart shows zero CSV markers. Counter-hypothesis to hunt: does `ChartPanel` draw markers from a *second*, snapshot-based source (`ChartPanel.hpp:817,:909-922,:1005-1010` render `#core.leg` labels — check whether those come from `snap` rather than `trades`)? If so, only the Equity Curve is dead, not the markers, and my severity drops.
2. **RANK 1's completeness.** I proved zero `X` rows in the *current* file. Refute by checking whether she was looking at the panel during a window when the file *did* contain exits — pull `logging/btcusdt_order_history.20260513-223714.csv` (8 X rows) and confirm the panel renders it. Also: is there any path that writes `X` rows to a per-node mirror but not the aggregate? (`ShardedTradeLog_WriteRow:163-171` writes both from one buffer, so I believe not — verify the `log->file` null-gate at `:464`/`:536` can't leave mirrors alive with a dead aggregate.)
3. **The duplicate-key parse claim (H-1).** I proved the loop has no `break` (`ControllerConfig.hpp:2464-2490`) but did **not** locate the exact assignment site for `partial_exit_enabled` (it is macro-generated; no string literal exists in `ControllerConfig.hpp` or `CfgFieldRegistry.hpp`). Refute by finding the generated key-match and confirming it is a plain assignment (last-wins) and not a `explicitly_set`-guarded first-wins — `maker_explicitly_set`/`taker_explicitly_set` at `:2455-2456` prove first-wins *does* exist for some keys.
4. **RANK 2 vs the event-log channel.** I claim the global counters are unrestorable. Refute by checking whether `OrderEventLog` replay has a *second* path (outside `EventLoopState_ReconstructPerCoreFromEventLog`) that bumps `state->total_*` — specifically the mode-0 `OnEvent` body at `ControllerEventLoop.hpp:2195`/`:2264`, and whether any boot configuration reaches it (production mode-1 returns early at `:2165` per the prior report).
5. **The `snap->source_cfg_path` availability claim (P4).** I assert the sharded publisher fills it (`ShardedSnapshot.hpp:170-173`). Verify it is non-empty in a real run (`EngineHeaderPanel.hpp:60` guards on `[0]`) — if `cfg->source_cfg_path` is empty on the sharded path, the "the truth is already published" framing weakens.
6. **RANK 7's blast radius.** I claim the rename orphaned dock state. Refute/extend by enumerating **every** `ImGui::Begin("…")` title changed in `baf5e5a` and any earlier vocab sweep — if more than 2 titles moved, more panels lost layout, and the H21-for-window-titles argument gets stronger.
7. **The `MAX_HISTORY` direction (RANK 5).** I claim the break keeps the *oldest* 256. Adversarially confirm the file is read strictly top-to-bottom with no seek-to-end (`TradeHistoryPanel.hpp:126` `fopen(..., "r")` then `:149` `while (fgets(...))` — no `fseek`), and that arrival-order in the CSV really is roughly chronological (`ShardedTradeLog.hpp:33-34` warns rows are **arrival order, NOT chronological** — which makes "oldest 256" itself approximate and arguably worse).
8. **My decision to rank RANK 1 above RANK 2.** The counter-position: if the operator saw a *populated* Stats row in an earlier session and a zeroed one later, RANK 2/3 dominates and RANK 1 is incidental. **The single discriminating question for her:** *did you ever see rows in the Trade History table, and if so, did they vanish, or has it always said "no completed trades yet"?* That one answer re-orders the whole list.

---

## § 10. TOOL DISPOSITION

| Tool | Run? | Result |
|---|---|---|
| `tools/calls_graph_diff.sh` | **YES** | `CLEAN — no strategy/regime functions orphaned or dead-defined`. Did **not** catch the dead `GUI_Panel_Config` (out of scope — `SHARDED_FILES` doesn't include `GUI/`) |
| `tools/scan_class_44_cfg_orphan.py` | **YES** | `OK — oracle PASS`, 5 KNOWN-PENDING(#9) dead-path-only orphans, no new. Class-44 *cfg-flag* scope only; blind to panel/path orphans |
| `DOCS/CODE_MAP.md` | consulted | All 6 spot-checked symbols agree with my cites |
| `DOCS/TOOLS.md` | consulted (full inventory searched per arming § 3) | **No tool covers GUI-literal ⊆ engine-written-path.** Nearest siblings: `check_cfg_key_prefix_drift.py` (cfg keys), the unbuilt `check_gui_engine_cfg_key_parity.py` (EV-2 O-1). Gap named at H-7 |
| `check_struct_alignment.py` / `check_latency_path_conformance.py` / `node_persist_layout.py` / `gen_code_map.sh --composition` | **not run — deliberate** | No struct-layout, wire, or hot/slow-path change in scope; this surface is render-cadence + file I/O only |
| `check_identifier_retirement.py` | **not run** | Read-only mapping pass; no identifier motion proposed. Flagged as *relevant at fix time* for RANK 7 (window titles as persistence keys) and H-6 (CSV header names) |

---

## § 11. RECOMMENDATION

**Do not treat this as one bug.** The complaint is a bundle, and the correct disposition differs per member.

1. **Answer the § 9.8 discriminating question first.** One operator answer re-orders RANK 1 vs RANK 2 and prevents fixing the wrong thing.
2. **RANK 4 (dead Equity Curve) is the highest-value NEW find** — a whole panel plus the chart's trade markers have been silently dead since the sharded log format landed, and nothing in any ledger knew. Verify empirically (§ 9.1), then home it.
3. **RANK 2 folds into EV-1 exactly as already specified** — the "re-source from persisted per-node sums" shape is confirmed wire-free and E.1.2-clean.
4. **H-1 (duplicate cfg keys incl. a stop-loss override) is the only capital-adjacent item here** and is independent of every GUI question. It is a sibling of the EV-2 D-1/D-9 `cfg_write_field` cohort and belongs in that lane.
5. **§ 4's finding reframes the operator's ask.** The archive system already produces exactly what a "past sessions" viewer needs, in a *better* form than the live CSV, and has zero consumers. Before building persistence, consider that the persistence exists and the *window* is missing.
6. **§ 3's cohort has a shape, not a bug**: GUI engine-facing paths are literals; the engine derives all of them from cfg; only one of the four has a published channel. Any fix for `btcusdt` alone leaves five siblings — and three of them cannot be fixed at all until `TUISnapshot` publishes `symbol`, `log_file`, and `health_log_path`.

**Scope fence honored: nothing proposed for E.1.2, nothing edited, no auto-proceed.**
