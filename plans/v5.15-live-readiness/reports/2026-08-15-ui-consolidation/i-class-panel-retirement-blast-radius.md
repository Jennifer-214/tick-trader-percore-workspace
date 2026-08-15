---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: I-2 — GUI panel RETIREMENT blast-radius + information-subsumption matrix (candidates: Latency · Per-Node P&L · Live P&L · Equity Curve)
agent_class: i-class
delivered: 2026-08-15
ground: engine HEAD 09824e8 (pre-D-289/2), branch feat/v5.15-live-readiness
consumed_by: the UI-consolidation triage + the retire-vs-consolidate decision
sister_reports: i-class-panel-persistence.md · i-class-stats-consolidation-ia.md (this directory)
headline: the Latency panel is STRUCTURALLY empty in every build (18 TUISnapshot fields, ZERO producers) — retiring it is zero-information-loss; and retiring Equity Curve kills GUI/TradeReader.hpp entirely
---

# I-2 — GUI panel RETIREMENT blast-radius + information-subsumption matrix

**Ground:** engine `/home/caramel/code/FoxML_Trader_v2`, HEAD `09824e8`, branch `feat/v5.15-live-readiness`. Read-only investigative pass. Every claim below is a live code read at this SHA; no recalled facts.

---

## 0. TWO CORRECTIONS TO THE SUPPLIED FRAME (read these first — they invert two verdicts)

Per `DOCS/SUBAGENT_ARMING.md` § 4, a materially wrong supplied shape gets flagged loudly rather than silently built on. Both of the orchestrator's "already established" claims are **wrong at HEAD**.

### CORRECTION 1 — `Latency` is not "empty because WARMUP". It is **structurally, permanently empty in every build**. The bg/eg/pc sub-timings do not exist.

The orchestrator's bucket-(c) finding ("`Latency` is the only surface carrying hot-path bg / eg / pc sub-timings") is a **phantom capability**. Those fields have **no producer anywhere in the codebase**.

The whole `TUISnapshot` latency block is declared at `/home/caramel/code/FoxML_Trader_v2/DataStream/EngineTUI.hpp:998-1014`:

```cpp
    // latency
#ifdef LATENCY_PROFILING
    double hot_avg_ns, hot_min_ns, hot_max_ns, hot_p50_ns, hot_p95_ns, hot_p99_ns;
    uint64_t hot_count;
    double slow_avg_ns, slow_min_ns, slow_max_ns;
    uint64_t slow_count;
    // per-component hot path breakdown
    double bg_avg_ns, bg_max_ns;   // BuyGate
    double eg_avg_ns, eg_max_ns;   // ExitGate
    double eg_per_pos_ns;          // ExitGate per active position
    double pc_avg_ns, pc_max_ns;   // PortfolioController_Tick
    // fill vs no-fill PCTick breakdown
    double pc_fill_avg_ns, pc_fill_max_ns;
    uint64_t pc_fill_count;
    double pc_nofill_avg_ns, pc_nofill_max_ns;
    uint64_t pc_nofill_count;
#endif
```

Exhaustive grep across all `*.hpp` / `*.cpp` (excluding `build*`) for every one of these names returns **only reads, never a single write**:

- `hot_count` — 15 total occurrences repo-wide; the only WRITE-capable ones are on the *different* struct `EngineTUIState::hot_count` (`DataStream/EngineTUI.hpp:118`), and **that one is never written either** (its only uses are the reads at `:538-560`).
- `hot_avg_ns` / `hot_p50_ns` / `hot_p95_ns` / `hot_p99_ns` / `hot_min_ns` / `hot_max_ns` — declaration at `:1000` plus reads at `GUI/DashboardPanels.hpp:1841,1845,1849,1853`, `DataStream/TUIAnsi.hpp:1038`, `DataStream/EngineTUI.hpp:2314,2317`. Zero assignments.
- `bg_avg_ns` / `eg_avg_ns` / `eg_per_pos_ns` / `pc_avg_ns` / `slow_avg_ns` / `slow_count` — same shape. Zero assignments.
- The `EngineTUI` accumulator block that would feed them (`DataStream/EngineTUI.hpp:115-133`: `hot_sum`, `bg_sum`, `eg_sum`, `pc_sum`, `eg_pos_sum`, `hot_hist[21]`, `tsc_per_ns`) — **also never written**. `tsc_per_ns` carries the comment `// TSC cycles per nanosecond, calibrated at startup` (`:132`) and is never calibrated; the divisions at `:539/553/555/557` would be `/0.0` if reached.

Consequence: `if (s->hot_count > 0)` at `GUI/DashboardPanels.hpp:1838` and `if (s->slow_count > 0)` at `:1870` are **both permanently false**. `GUI_Panel_Latency` renders exactly `ImGui::Begin("Latency")` + `SectionHeader("LATENCY")` + `ImGui::End()` — a window title, the word LATENCY, and a separator. **Forever, in every build, warmed up or not.**

The panel *is* compiled into the operator's binary — `build.sh:162` passes `-DLATENCY_PROFILING=ON` for `build_gui`, and `CMakeLists.txt:151-152` applies it to `engine_gui`. So she sees the tab; it is simply always empty. (`./build.sh gui-lite`, `build.sh:175`, omits the flag → no tab at all.)

**This is a live Class 2 (display↔execution divergence — the dashboard lies) + Class 44 (producer-orphan) + Class 40 (dead code compiled in).** The ANSI TUI carries the identical dead surface at `DataStream/TUIAnsi.hpp:1029-1057` (`ANSI_Section_Latency`, wired live into the STANDARD layout at `:1203-1206`).

**Effect on the audit:** candidate #1's bucket (c) is EMPTY. There is nothing unique to lose. The retirement is strictly information-preserving, and the honest framing is not "retire a panel" but "delete a phantom".

### CORRECTION 2 — the per-node Alloc/Realized/Fees/W-L/Budget table is inside **`Account`**, not inside `Per-Node P&L`. Retiring `Per-Node P&L` does not drop it.

`GUI_Panel_Account` spans `GUI/DashboardPanels.hpp:1014-1248` (`ImGui::Begin("Account")` at `:1015`, `ImGui::End()` at `:1247`). The `PER-CORE P&L` section header is at `:1106` and the 7-column `per_node_pnl` table (Node / Strat / Alloc / Realized / Fees / W/L / Budget) is at `:1117-1231` — **all inside Account's Begin/End**.

`GUI_Panel_PerNodePnL` is a completely separate function at `:1624-1715` (`ImGui::Begin("Per-Node P&L")` at `:1660`) rendering an **ImPlot time-series** of each node's `node_realized` over the session — no table at all.

**Effect on the audit:** candidate #2's real bucket (c) is *only* the time-series dimension, not the tabular data. The subsumption is far better than the frame assumed.

---

## 1. COMPLETE PANEL INVENTORY

Every `ImGui::Begin("...")` in `GUI/`, `foxml_suite.cpp`, and `Backtest/` (31 sites). "DB" = present in that binary's dock-builder (`Gui_SetupDefaultLayout`, `GUI/GuiThread.hpp:355-400` / `Suite_SetupDefaultLayout`, `foxml_suite.cpp:45-83`).

| Window title | Defined at | engine_gui | suite | Render call site | Notes |
|---|---|---|---|---|---|
| Price Chart | `GUI/ChartPanel.hpp:244` | **DB** `GuiThread.hpp:370` | **DB** `foxml_suite.cpp:60` | `GuiThread.hpp:527` / `foxml_suite.cpp:454` | |
| Volume | `GUI/ChartPanel.hpp:1276` | **DB** `:371` | **DB** `:61` | `GuiThread.hpp:528` / `:455` | |
| **Live P&L** | `GUI/ChartPanel.hpp:1405` | **DB** `:372` | rendered, **NOT in suite DB** | `GuiThread.hpp:529` / `foxml_suite.cpp:457` | ini-placed in suite (`foxml_suite.ini:123`) |
| **Equity Curve** | `GUI/ChartPanel.hpp:1477` | **DB** `:373` | **DB** `:62` | `GuiThread.hpp:530` / `:456` | |
| Header | `GUI/DashboardPanels.hpp:147` | **DB** `:381` | rendered, not in suite DB | `GUI_RenderDashboard:2101` | suite gated on `run_control.complete` |
| Top Bar | `:284` | **DB** `:382` | rendered, not in suite DB | `:2102` | |
| Market | `:333` | **DB** `:383` | **DB** `:77` | `:2103` | |
| Buy Gate | `:551` | **DB** `:384` | rendered, not in suite DB | `:2104` | |
| Account | `:1015` | **DB** `:385` | **DB** `:78` | `:2105` | **owns the per-node P&L table `:1104-1232`** |
| **Config** | `:1266` | — | — | **ZERO CALLERS** | **already-dead panel** (Class 40); no ini entry either |
| Positions | `:1326` | **DB** `:386` | rendered, not in suite DB | `:2106` | suite gets 11-col fallback (`shared==NULL`, `:1348`) |
| **Per-Node P&L** | `:1660` | rendered, **NOT in engine DB** | rendered, not in suite DB | `:2107` | ini-placed (`foxml_gui.ini:148`) |
| Stats | `:1733` | **DB** `:389` | **DB** `:79` | `:2108` | |
| **Latency** | `:1835` | **DB** `:391` | rendered, not in suite DB | `:2110-2112` (`#ifdef LATENCY_PROFILING`) | **structurally always empty — see Correction 1** |
| ML Intelligence | `:1918` | **DB** `:390` | **DB** `:80` | `:2109` | self-hides when no ML active (`:1916`) |
| Risk | `:2123` | rendered, **NOT in DB** | **NOT rendered in suite** | inline `:2122`, gated `&& shared` | suite passes `shared=NULL` (`foxml_suite.cpp:423`) → absent |
| Per-Node Latency | `:2248` | rendered, **NOT in DB** | rendered, not in suite DB | inline `:2247` | **the LTp99 columns that landed `47c06b9`** (`:2266`, `:2289`, `:2310`, `:2340`) |
| Engine Topology | `:2417` | rendered, **NOT in DB** | rendered, not in suite DB | inline `:2416` | |
| Settings | `GUI/SettingsPanel.hpp:1999` | **DB** `:392` | **DB** `:70` | `GuiThread.hpp:537` / `:429` | |
| Trade History | `GUI/TradeHistoryPanel.hpp:267` | **DB** `:393` | **DB** `:76` | `GuiThread.hpp:540` / `:442` | separate reader from TradeReader |
| Engine Log | `GUI/LogViewerPanel.hpp:129` | **DB** `:394` | rendered, **NOT in suite DB** | `GuiThread.hpp:541` / `:418` | |
| Engine | `GUI/EngineHeaderPanel.hpp:37` | rendered, **NOT in DB** | rendered, not in suite DB | `GuiThread.hpp:508` / `:434` | |
| ML Status | `GUI/MLStatusPanel.hpp:39` | rendered, **NOT in DB** | rendered, not in suite DB | `GuiThread.hpp:511` / `:436` | |
| Strategy Quality | `GUI/StrategyQualityPanel.hpp:345` | rendered, **NOT in DB** | **NOT rendered in suite** | `GuiThread.hpp:547` | |
| Data / Run Control / Results / Past Runs / Comparison / Optimizer / Training | `Backtest/BacktestPanels.hpp:564,675,751,1473,2454,2700,4961` | **suite only** | DB except **Past Runs** | `foxml_suite.cpp:409-417` | |

### What "not in the dock-builder" actually means (load-bearing for the retirement mechanics)

`Gui_SetupDefaultLayout` fires **only when no saved layout exists** — `GUI/GuiThread.hpp:476-484`:

```text
        if (first_frame) {
            ImGuiID dockspace_id = ImGui::GetID("DockSpace");
            // only build layout if no saved layout exists
            if (ImGui::DockBuilderGetNode(dockspace_id) == NULL ||
                ImGui::DockBuilderGetNode(dockspace_id)->ChildNodes[0] == NULL) {
                Gui_SetupDefaultLayout(dockspace_id);
            }
```
*(fence retagged cpp→text at save: a verbatim QUOTE of `GUI/GuiThread.hpp:476-484`, not a compilable sample — B-Plus compile-probe exclusion; content unchanged)*

`foxml_gui.ini` exists on this machine and already carries all 27 window entries. **Therefore the dock-builder rows are already inert for the operator's live setup.** Deleting a `DockBuilderDockWindow(...)` row changes nothing she can see; the panel vanishes only when its `Begin()` body is removed.

The ini also proves ImGui tolerates orphan window entries harmlessly: it already carries `[Window][Per-Core P&L]` (`foxml_gui.ini:119`) and `[Window][Per-Core Latency]` (`:136`) — stale survivors of the per-core→per-node rename, sitting alongside the live `[Window][Per-Node P&L]` (`:148`) and `[Window][Per-Node Latency]` (`:154`). No cleanup needed, no crash, no lie.

---

## 2. THE INFORMATION-SUBSUMPTION MATRIX

I use four buckets, not three — Correction 1 forced a fourth: **(d) PHANTOM** = the panel names a datum that no producer ever writes, so the "loss" was already incurred long before the retirement.

### Candidate 1 — `Latency` (`GUI/DashboardPanels.hpp:1834-1881`, inside `#ifdef LATENCY_PROFILING` at `:1823`/`:1887`)

| Datum | Source field | Bucket | Where else |
|---|---|---|---|
| hot avg ns | `s->hot_avg_ns` `:1841` | **(d) PHANTOM** | no producer; `Per-Node Latency` `Avg` column `:2285` is the real, populated per-node equivalent |
| hot p50 / p95 / p99 ns | `s->hot_p50_ns/p95/p99` `:1845,1849,1853` | **(d) PHANTOM** | `Per-Node Latency` p50/p95/p99 `:2286-2288` + **LTp99** `:2289` (populated, operator-verified at `47c06b9`) |
| hot sample count | `s->hot_count` `:1855` | **(d) PHANTOM** | `Per-Node Latency` `Samples` `:2283` |
| **bg avg ns** (BuyGate) | `s->bg_avg_ns` `:1859` | **(d) PHANTOM** | *nowhere* — but also **not here**: never written |
| **eg avg ns + eg per-pos ns** (ExitGate) | `s->eg_avg_ns`, `s->eg_per_pos_ns` `:1863` | **(d) PHANTOM** | same |
| **pc avg ns** (PortfolioController_Tick) | `s->pc_avg_ns` `:1867` | **(d) PHANTOM** | same |
| slow avg + count | `s->slow_avg_ns`, `s->slow_count` `:1871-1877` | **(d) PHANTOM** | `Per-Node Latency` SLOW-PATH sub-table `sp_*` `:2334-2341` (populated, incl. `sp_lifetime_p99_ns`) + the **work breakdown** table `:2354-2401` |

**(a) fully subsumed:** every nominal datum, by `Per-Node Latency` — and strictly *better* (per-node rather than collapsed, plus lifetime histograms, plus a 5-section slow-path work breakdown the old panel never had).
**(b) subsumed-but-worse:** none.
**(c) UNIQUE:** **none.**
**(d) PHANTOM:** all 11 fields.

**Verdict: zero information loss. The panel is a Class-2 lie that should have died when the per-node `NodeLatencyStats` surface replaced it.**

---

### Candidate 2 — `Per-Node P&L` (`GUI/DashboardPanels.hpp:1624-1715`)

| Datum | Source | Bucket | Where else |
|---|---|---|---|
| per-node realized P&L, **current value** | `s->per_node[c].node_realized` `:1652` | **(a) fully subsumed** | `Account` → PER-CORE P&L table, `Realized` column `:1192` (same field, colored, `$%+.2f`) |
| node index label | `c` `:1699` | **(a) fully subsumed** | `Account` `Node` column `:1145` (+ kill-trip `%d!` marker + dd% tooltip `:1139-1143`) |
| resolved strategy short-name | `s->per_node[c].resolved_strategy_id` `:1695-1698` | **(a) fully subsumed, and the survivor is BETTER** | `Account` `Strat` column `:1153-1186` — carries the `AUTO(resolved)` wrapper + the tri-state explicit-set marker `!`/`?` + the defaulted-strategy tooltip. The dying panel prints a **bare resolved-now name**, which is exactly the open EV-1 defect (`plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`, cites `DashboardPanels.hpp:1690-1693`) |
| breakeven zero reference line | literal `:1706-1711` | **(a)** | conceptually present via `PnlColor()` sign coloring `:1192` |
| **per-node realized P&L as a TIME SERIES** (30 min @ 1 Hz, 1800-sample ring `:1625-1628`) | derived, GUI-local | **(c) UNIQUE — dies with the panel** | **Nothing else in either binary plots per-node P&L against time.** `Live P&L` is aggregate. `Equity Curve` is aggregate and per-trade. The ANSI TUI has no per-node P&L surface (`ANSI_Section_*` family, `DataStream/TUIAnsi.hpp:380-1096` — no per-node P&L section) |
| paper-reset-aware ring clear | `s->paper_reset_seq` `:1640-1646` | machinery, not information | sole consumer — see § 3 |

**(a) fully subsumed:** current value, node id, strategy label (survivor strictly richer).
**(b) subsumed-but-worse:** none.
**(c) UNIQUE — dies:** **the trajectory.** The panel's stated purpose (`:1613-1616`: *"Useful for spotting which core is adding alpha vs which is bleeding fees"*) is a *differential-over-time* question the Account table's point-in-time snapshot cannot answer. Losing it means: to see that node 2 has been steadily bleeding for 20 minutes while node 0 spiked once, the operator must watch the number or grep logs.
**(d) PHANTOM:** none.

**Verdict: one genuine bucket-(c) loss. This is the only candidate of the four where a real capability dies.** Whether it matters is an operator judgment about how she monitors — but it should not be retired under the false belief that Account covers it.

---

### Candidate 3 — `Live P&L` (`GUI/ChartPanel.hpp:1404-1459`)

| Datum | Source | Bucket | Where else |
|---|---|---|---|
| aggregate `total_pnl`, **current value** | `s->pnl_history[ri]` head `:1419` ← `bs->total_pnl` (`CoreFrameworks/EngineSharded/Async.hpp:574`) | **(a) fully subsumed** | `Top Bar` `P&L $%+.2f` `DashboardPanels.hpp:294`; `Account` `net:` `:1045`; the SDL **window title** `GuiThread.hpp:501-502` |
| aggregate P&L **trend over wall-clock**, ~2 min (`GRAPH_LEN=120` @ ~1 Hz, `DataStream/EngineTUI.hpp:931`) | `pnl_history` ring `:1416-1420` | **(b) subsumed-but-WORSE — the "worse" is material** | `Equity Curve` plots cumulative net P&L **per closed trade** (`ChartPanel.hpp:1486-1489`). Its x-axis advances only on a SELL. **During a held position, Equity Curve is FLAT while Live P&L moves with mark-to-market.** They are different quantities on different axes, not two views of one thing |
| green-above / red-below shaded fill + zero line | `:1442-1453` | **(a)** cosmetic | `Equity Curve` has the same idiom `:1511-1522` |

**(a) fully subsumed:** the current value, three times over.
**(b) subsumed-but-worse:** the trend — and only if `Equity Curve` survives. **If both #3 and #4 retire, engine_gui loses ALL P&L-over-time visualization.** The ANSI TUI keeps a P&L sparkline (`ANSI_Section_Charts` → `ab_sparkline_pnl`, `DataStream/TUIAnsi.hpp:994`, reachable via the `[l]` layout cycle, `EngineTUI.hpp:2436`) — so the *data* survives for an ANSI operator, but not for a GUI operator.
**(c) UNIQUE — dies:** the **mark-to-market P&L trajectory inside an open position**. Nothing else in the GUI moves while a position is held and unclosed.
**(d) PHANTOM:** none.

**Verdict: information loss is conditional on the Equity Curve decision. As an isolated retirement it is near-free; as half of a pair it is not.**

---

### Candidate 4 — `Equity Curve` (`GUI/ChartPanel.hpp:1476-1566`)

Reads **zero** `TUISnapshot` fields. Its entire input is `TradeData` — a GUI-thread-local struct fed by re-parsing `logging/btcusdt_order_history.csv` (`GUI/TradeReader.hpp:169-263`).

| Datum | Source | Bucket | Where else |
|---|---|---|---|
| final cumulative net P&L | `trades->equity[en-1].cumulative_pnl` `:1488` | **(a) fully subsumed** | `Account` `realized:` `:1028` / `net:` `:1045` |
| closed-trade count | `trades->equity_count` `:1484` | **(a) fully subsumed** | `Stats` `exits:` `:1754` (= `wins + losses`, `:1736`) |
| TP-vs-other exit outcome per trade | `trades->markers[mi].is_tp` `:1532` | **(b) subsumed-but-worse** | `Trade History` panel (`GUI/TradeHistoryPanel.hpp:267`) lists per-trade rows from the same CSV — **table, not curve**; `Stats` gives `W:` / `L:` aggregates `:1762,1766` |
| drawdown geometry (depth + duration + shape) | visual, from the curve | **(b) subsumed-but-worse** | `Stats` `maxDD:` `$%.2f (%.2f%% / %.1f%%)` `:1804-1806` — the scalar summary the curve visualizes. You get the *number*, you lose *when/how long/how many times* |
| **the equity SHAPE itself** — streak structure, slope changes, recovery legs | derived | **(c) UNIQUE — dies** | Nothing else draws it in `engine_gui`. In `foxml_suite` a *different* equity plot survives — `Comparison` (`Backtest/BacktestPanels.hpp:2521`) — but it is sourced from `BacktestResults::equity_curve` (`Backtest/BacktestEngine.hpp:339`), a **backtest-run** artifact, not the live/paper trade CSV |
| hover crosshair + $ readout | `:1539-1560` | cosmetic | — |

**(c) UNIQUE — dies:** the live/paper equity curve shape and its TP/SL marker coloring. In the suite: the run-level curve survives via `Comparison`, so suite loss is smaller.
**(d) PHANTOM:** none.

**Verdict: real but modest information loss (drawdown geometry). Structurally, this is by far the biggest architectural win — see § 3.**

---

### Bonus — the operator's "roll Stats into a different tab"

`GUI_Panel_Stats` (`:1732-1816`) reads: `wins`, `losses`, `total_buys`, `total_exits_fills`, `partial_exit_enabled`, `win_rate`, `profit_factor`, `all_wins_run`, `avg_win`, `avg_loss`, `avg_loss_market`, `expectancy`, `max_drawdown`, `max_drawdown_pct`, `max_dd`, `fee_ratio`.
`GUI_Panel_Account` (`:1014-1248`) reads: `equity`, `balance`, `realized`, `unrealized`, `return_pct`, `total_pnl`, `fees`, maker/taker quartet, `exposure_pct`, `max_exp`, `risk_amt`, `breaker_tripped`, `live_trading` + the per-node table.

**Field-set intersection is EMPTY.** Rolling Stats into Account is a pure layout MOVE (relocate the `:1734-1813` body inside Account's `Begin`/`End`, drop the `Begin("Stats")`/`End()` pair and the dock rows `GuiThread.hpp:389` + `foxml_suite.cpp:79`) with **zero information change and zero snapshot-surface change**. It is the cheapest and safest of everything on the table. It is *not* a retirement and must not be executed as one.

---

## 3. DEAD SNAPSHOT SURFACE (the Class-44 producer-orphan enumeration)

### Candidate 1 — `Latency`

Retiring the GUI panel frees **nothing by itself**, because `DataStream/TUIAnsi.hpp:1029-1057` (`ANSI_Section_Latency`, live-wired at `:1203-1206`) still reads the same fields. But the fields **already have no producer**, so the real accounting is:

| Field(s) | Decl | Producers | Consumers after GUI retirement |
|---|---|---|---|
| `hot_avg_ns`, `hot_p50/p95/p99_ns`, `hot_count` | `EngineTUI.hpp:1000-1001` | **ZERO** | `TUIAnsi.hpp:1034-1039` (live, permanently inert) + `EngineTUI.hpp:2312-2317` (**dead fn**, see below) |
| `hot_min_ns`, `hot_max_ns` | `:1000` | **ZERO** | **only** `EngineTUI.hpp:2314` = dead fn ⇒ **fully orphaned today** |
| `slow_avg_ns`, `slow_count` | `:1002-1003` | **ZERO** | `TUIAnsi.hpp:1047-1052` (inert) + dead fn |
| `slow_min_ns`, `slow_max_ns` | `:1002` | **ZERO** | **only** dead fn ⇒ **fully orphaned today** |
| `bg_avg_ns`, `eg_avg_ns`, `eg_per_pos_ns`, `pc_avg_ns` | `:1005-1008` | **ZERO** | `TUIAnsi.hpp:1044` (inert) + dead fn |
| `bg_max_ns`, `eg_max_ns`, `pc_max_ns` | `:1005-1008` | **ZERO** | **only** dead fn ⇒ **fully orphaned today** |
| `pc_fill_avg_ns/max_ns/count`, `pc_nofill_avg_ns/max_ns/count` | `:1010-1013` | **ZERO** | **only** dead fn — never read by the GUI at all ⇒ **fully orphaned today** |

**Count: 18 `TUISnapshot` fields, 0 producers, 0 slow-path cost** (nothing computes them — that is the whole point). The dead weight is *declaration* weight, not compute weight.

**The dead-consumer chain (out of my scope, but it is what makes the above provable):**
`TUI_Init` (`EngineTUI.hpp:175`), `TUI_Cleanup` (`:208`), `TUI_Render` (`:236`), `TUI_HandleInput` (`:628`), `TUI_Render_Snapshot` (`:2145`), `TUI_ReadKey` (`:2356`) — **all six are defined and have ZERO callers anywhere** (grep for `TUI_Render(` / `TUI_Render_Snapshot(` / `TUI_Init(` etc. across all `*.cpp`/`*.hpp` returns only the definitions). The live ANSI thread is `tui_thread_fn` (`:2379`), which calls `ANSI_Render` (`TUIAnsi.hpp:1302`) instead — confirmed at `EngineTUI.hpp:2421`.

**⚠ E.1.2 INTERSECTION — STOP LINE.** The `EngineTUI` struct (which carries the dead `#ifdef LATENCY_PROFILING` accumulator block at `:115-133`) is an **embedded member of `TUISharedState`**: `EngineTUI tui;` at `DataStream/EngineTUI.hpp:1545`. `TUISharedState` carries `static_assert(alignof(TUISharedState) == 64, ...)` at `:1552`, was **realigned this ship** (commit `7778c66`, "H6 cache-line realign — regime_state + TUISharedState control cluster (4 D-414 keys closed)"), and is under the `tools/check_cache_layout.py` shrink-only baseline. **Deleting the `EngineTUI` accumulator block changes `TUISharedState`'s layout and re-opens E.1.2.A work. That half is OUT OF SCOPE — I am naming it and stopping.**

Similarly, deleting the `TUISnapshot` latency block shifts `PerNodeSnap`'s offset and will re-trigger `static_assert(offsetof(TUISnapshot::PerNodeSnap, ensemble_active) % 64 == 0, ...)` at `EngineTUI.hpp:1429`, plus the four `[STRADDLE_EXEMPT]` tags at `:1100-1103` (one of which was added **2026-08-14** for exactly this reason: *"shifted onto the 64B boundary by the v5.15.5 lifetime_p99 field append"*). Layout-touching is a cache-layout-gate event, not a free deletion.

### Candidate 2 — `Per-Node P&L`

| Field | Decl | Producer | Other consumers | Verdict |
|---|---|---|---|---|
| `TUISnapshot::paper_reset_seq` | `EngineTUI.hpp:983` | `CoreFrameworks/ShardedSnapshot.hpp:321` (zero-init) + `CoreFrameworks/EngineSharded/Async.hpp:523` (`bs->paper_reset_seq = (uint32_t)shared_ptr->paper_reset_seq;`) | **NONE** — the only reads in the entire repo are `DashboardPanels.hpp:1640` and `:1641` | **→ Class-44 producer-orphan** |
| `per_node[].node_realized` / `resolved_strategy_id` / `strategy_id_display` / `per_node_count` | `:1292,1136,1135,1061` | populator | `Account`, `Buy Gate`, `Market`, `Header`, `Risk`, `Positions`, … | survive |

**Count: 1 field, 4 bytes.** Producer lines to remove: `Async.hpp:523` (one `uint32` copy on the async snapshot-assembly path — **not the slow path proper, and not the hot path**) and `ShardedSnapshot.hpp:321`. `TUISharedState::paper_reset_seq` (`EngineTUI.hpp:1499`) stays alive — it is bumped at `Async.hpp:760` and logged at `:764`.

**A stale comment to correct at fix time** (`SUBAGENT_ARMING` § 2.5 — the code is truth): `EngineTUI.hpp:979-982` says *"paper_reset_seq mirror so retained-history GUI panels (Per-Core P&L ring, **equity curve**, etc.) can detect reset events"*. The equity curve does **not** read it (`GUI_EquityChart`, `ChartPanel.hpp:1476-1566`, reads no snapshot field at all). The comment names a consumer that never existed.

### Candidate 3 — `Live P&L`

| Field | Decl | Producer | Other consumers |
|---|---|---|---|
| `pnl_history[120]` | `EngineTUI.hpp:934` | `Async.hpp:574` + back-buffer memcpy `:499` | `TUIAnsi.hpp:994` (`ab_sparkline_pnl`, live CHARTS layout) |
| `graph_head` | `:935` | `Async.hpp:575` + `:500` | `TUIAnsi.hpp:985,994,1003` |
| `graph_count` | `:936` | `Async.hpp:576` + `:501` | `TUIAnsi.hpp:974,985,994,1003` |

**Count: ZERO dead snapshot surface.** Every field keeps a live ANSI consumer. Retiring Live P&L buys no architectural win whatsoever — it is a pure UI-declutter move.

*(Adjacent observation, no action implied: `price_history` (`:932`) and `volume_history` (`:933`) are already GUI-orphans — read only by `TUIAnsi.hpp:985,1003`. Unchanged by any of these retirements.)*

### Candidate 4 — `Equity Curve` — **the real architectural win**

`GUI_EquityChart` reads no snapshot fields. Its input is `TradeData`. And `TradeData` has exactly **one other consumer — which turns out to be no consumer at all**:

`GUI_PriceChart` (`GUI/ChartPanel.hpp:240-1257`) takes `TradeData *trades` (`:241`) and **never dereferences it**. Verification: `grep -n 'trades' GUI/ChartPanel.hpp` returns exactly 9 hits — one is the `GUI_PriceChart` parameter declaration at `:241`, and the other eight are all inside `GUI_EquityChart` (`:1476,1478,1479,1484,1488,1528,1529,1532`). The price chart's entry/TP/SL markers come from `snap->positions[]` / `snap->per_node[]`, not the CSV.

**Therefore retiring `Equity Curve` makes the ENTIRE `GUI/TradeReader.hpp` module dead** — a TIER-1 orphaned file per `/dead-code-trace` classification:

- `EquityPoint` (`GUI/TradeReader.hpp:51-53`)
- `TradeMarker::is_sell` / `is_tp` (`:34-35`) — `price` too; nothing reads any of it
- `TradeData` (`:65-77`) — **`[DERIVED] [SIZE]_[12568B]`** per its own tag block at `:84`
- `TradeData_Init` (`:102-105`), `TradeData_Refresh` (`:169-263`), `csv_field` (`:123-152`)
- the whole FIFO fee-pairing machinery inside `_Refresh`: `pending_entry_fees[MAX_TRADES]` (`:193`), the stash at `:217-220`, the pop-and-shift at `:227-235`, the `cumulative_pnl` accumulation at `:238-239` — **this exists solely to build `equity[]`**
- the `TradeData trades` instances: `GuiThread.hpp:458-459` + `foxml_suite.cpp:289-290`
- the per-frame refresh calls: `GuiThread.hpp:521-522` + `foxml_suite.cpp:448-449`
- the now-unused `trades` arg at both `GUI_PriceChart` call sites: `GuiThread.hpp:527`, `foxml_suite.cpp:454`
- `#include "TradeReader.hpp"` at `GUI/ChartPanel.hpp:19` and `foxml_suite.cpp:28`

**Quantification:** 269-line file removed · ~12.5 KB per instance × 2 binaries ≈ 25 KB of resident state · and **a `stat()` syscall removed from the 60 Hz render loop** (`TradeData_Refresh` does `stat(td->csv_path, &st)` unconditionally on entry, `TradeReader.hpp:170-171`, called every frame at `GuiThread.hpp:522`), plus a full CSV reparse on every file-size change.

**None of this sits on the slow path or the hot path** — it is entirely GUI-thread. So the win is codebase-surface + render-loop-syscall, not engine latency. Stating that honestly matters: it is a maintainability win, not an H8 win.

---

## 4. DELETION ORDERING + MECHANICS (M4 pillar B14)

### Direct answer to the `ChartState` question: **no coupling. No ordering constraint.**

`ChartState_Prepare` (`GUI/ChartPanel.hpp:128-193`) produces `ChartState`, consumed by `GUI_PriceChart(const ChartState *cs, ...)` (`:240`) and `GUI_VolumeChart(const ChartState *cs, ...)` (`:1274`) **only**. `GUI_LivePnLChart(const TUISnapshot *s)` (`:1404`) and `GUI_EquityChart(TradeData *trades)` (`:1476`) take **no `ChartState`**. Deleting either or both leaves `Price Chart` and `Volume` untouched.

### Leaves-first ordering

**Order rationale:** each step must leave the tree compiling. Deleting a `Begin()` body before its last consumer is removed is fine (nothing depends on a panel); deleting a struct/field before its last reader is not.

**PHASE 0 — free-standing, no dependencies, do first (or skip entirely and still have a coherent ship):**

| # | Action | Sites |
|---|---|---|
| 0.1 | Delete the already-dead `GUI_Panel_Config` | `GUI/DashboardPanels.hpp:1255-1313` (whole tagged unit incl. `[FUNCTION]`/`[CODE]`/`[END_*]` blocks). Zero callers — verified. Pure Class-40 close, unrelated to the four candidates |
| 0.2 | Move `Stats` into `Account` (NOT a deletion) | relocate `DashboardPanels.hpp:1734-1813` body inside `Account`'s Begin/End (before `:1247`); delete `Begin("Stats")` `:1733` + `End()` `:1815` + the fn wrapper `:1732-1816`; drop the `GUI_Panel_Stats(s)` call `:2108`; drop dock rows `GuiThread.hpp:389` + `foxml_suite.cpp:79` |

**PHASE 1 — `Latency` (leaf-most of the four; nothing depends on it):**

| # | Action | Sites |
|---|---|---|
| 1.1 | Delete the panel body | `GUI/DashboardPanels.hpp:1823-1887` (the `#ifdef LATENCY_PROFILING` … `#endif` wrapper *and* the whole tagged unit inside) |
| 1.2 | Delete the call site | `GUI/DashboardPanels.hpp:2110-2112` (`#ifdef` / `GUI_Panel_Latency(s);` / `#endif`) |
| 1.3 | Delete the dock row | `GUI/GuiThread.hpp:391` (inert — the ini already owns placement) |
| 1.4 | Update the stale panel-inventory comment | `GUI/GuiThread.hpp:69-70` lists `"Latency"` among the stateless dashboard panels |
| 1.5 | Update nav-infra | `DOCS/CODE_MAP.md:1003` (`GUI_Panel_Latency — line 1834`) → regen via `./tools/gen_code_map.sh` |
| — | **DO NOT** touch `EngineTUI.hpp:998-1014` (TUISnapshot block) or `:115-133` (EngineTUI block) in this phase | layout cascade + **E.1.2 entanglement** — see § 3 STOP LINE |

*Breaks a sibling?* No. Nothing reads the panel; the `#ifdef` is self-contained.

**PHASE 2 — `Per-Node P&L`:**

| # | Action | Sites |
|---|---|---|
| 2.1 | Delete the panel body | `GUI/DashboardPanels.hpp:1606-1720` (whole tagged unit) |
| 2.2 | Delete the call site | `GUI/DashboardPanels.hpp:2107` |
| 2.3 | *(no dock row exists)* | — |
| 2.4 | **Only after 2.1**: `TUISnapshot::paper_reset_seq` becomes an orphan → decide keep-or-drop | field `DataStream/EngineTUI.hpp:983` (+ comment `:979-982` which is already stale) · producer `CoreFrameworks/EngineSharded/Async.hpp:523` · init `CoreFrameworks/ShardedSnapshot.hpp:321`. **Dropping it is a `TUISnapshot` LAYOUT CHANGE** → same cache-layout-gate caveat as Phase 1. Recommend: leave the field, tombstone-comment it, defer the layout-touching removal to a dedicated snapshot-slimming leaf |
| 2.5 | Update nav-infra + the EV-1 roadmap item | `DOCS/CODE_MAP.md:1001`; `plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` EV-1 bullet citing `DashboardPanels.hpp:1690-1693` becomes **MOOT-BY-DELETION** and must be marked so, not silently dropped |

*Breaks a sibling?* No. `Account`'s per-node table is independent (Correction 2).

**PHASE 3 — `Live P&L`:**

| # | Action | Sites |
|---|---|---|
| 3.1 | Delete the panel body | `GUI/ChartPanel.hpp:1394-1464` (whole tagged unit) |
| 3.2 | Delete the call sites | `GUI/GuiThread.hpp:529` · `foxml_suite.cpp:457` |
| 3.3 | Delete the dock row | `GUI/GuiThread.hpp:372` (none in suite) |
| 3.4 | Update the file-level overview | `GUI/ChartPanel.hpp:8` names "Live P&L" in `[OVERVIEW]`; `:10-13` prose header |
| 3.5 | Update nav-infra | `DOCS/CODE_MAP.md:988` |
| — | Snapshot fields: **no change** — `pnl_history`/`graph_head`/`graph_count` keep live ANSI consumers | |

*Breaks a sibling?* No.

**PHASE 4 — `Equity Curve` (deepest cascade; do LAST):**

| # | Action | Sites | Must precede |
|---|---|---|---|
| 4.1 | Delete the panel body | `GUI/ChartPanel.hpp:1466-1571` | — |
| 4.2 | Delete the call sites | `GUI/GuiThread.hpp:530` · `foxml_suite.cpp:456` | 4.3 |
| 4.3 | Delete the dock rows | `GUI/GuiThread.hpp:373` · `foxml_suite.cpp:62` | — |
| 4.4 | **Now** `TradeData` has zero readers → drop the unused param from `GUI_PriceChart` | signature `GUI/ChartPanel.hpp:241`; call sites `GuiThread.hpp:527` + `foxml_suite.cpp:454` | after 4.1 |
| 4.5 | Delete the `TradeData` instances + refresh calls | `GuiThread.hpp:457-459, 521-522` · `foxml_suite.cpp:288-290, 447-449` | after 4.4 |
| 4.6 | Delete the file | `GUI/TradeReader.hpp` (269 lines) | after 4.5 |
| 4.7 | Delete the includes | `GUI/ChartPanel.hpp:19` · `foxml_suite.cpp:28` | after 4.6 |
| 4.8 | Update comments + nav-infra | `ChartPanel.hpp:8,10-11` (`[OVERVIEW]` names "Equity Curve"); `GuiThread.hpp:458` ("trade CSV reader for chart markers + equity curve"); `foxml_suite.cpp:288`; `DOCS/CODE_MAP.md:989,1057-1058`; `CoreFrameworks/ShardedTradeLog.hpp:75` (the "GUI/TradeReader reads" claim) | last |

**⚠ Sibling break in Phase 4:** 4.6 before 4.4/4.5 breaks the build (dangling `TradeData` type). 4.4 before 4.1 breaks the build (`GUI_EquityChart` still needs it). The ordering above is the only safe one.

**⚠ Phase-4 ↔ EV-1 intersection:** the roadmap's open "Trade History shows nothing" lane (`plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`) turns on a filename-split hypothesis quoting `ShardedTradeLog.hpp:75` — *"the aggregate `SYMBOL_order_history.csv` is what GUI/TradeReader reads"*. Deleting `TradeReader.hpp` removes one of the two readers named in that open investigation. **Not a blocker** (the panel under investigation is `TradeHistoryPanel.hpp`, a different reader) — but the EV-1 body must be amended at fix time or a future reader will chase a deleted file.

### Tests and DOCS

- **Tests: ZERO.** Grep of `tests/` for `GUI_Panel_Latency` / `GUI_Panel_PerNodePnL` / `GUI_LivePnLChart` / `GUI_EquityChart` / `TradeData` / `pnl_history` returns nothing. The two `equity_count` hits (`tests/controller_test.cpp:3714,3718`) are `BacktestResults::equity_count` (`Backtest/BacktestEngine.hpp:340`) — a different field entirely. **No test coverage exists for any of the four panels, which is itself worth noting: their deletion is unverifiable by the suite.**
- **DOCS:** only `DOCS/CODE_MAP.md` (regen) and `plans/_ideas/2026-05-12-foxml-suite-ux-cleanup.md:71-72` (names "Volume / Equity Curve / Live P&L" as the suite tab set). `DOCS/EXECUTION_DISPLAY_INVARIANTS.md` contains **no** reference to any of the four — grep returns nothing.
- **`foxml_gui.ini` / `foxml_suite.ini`:** leave alone. Orphan entries are harmless (proven by the surviving `[Window][Per-Core P&L]` at `foxml_gui.ini:119`).

---

## 5. H21 VERDICT — **NOT ENGAGED** (enumerated, not asserted)

Mechanical check run: `python3 tools/check_identifier_retirement.py` → `[identifier-retirement] GREEN — 47 persisted/wire identifiers match the ledger; no renumber/reuse/drop.` None of the 47 is a panel name, a window title, or a display-visibility key.

Enumeration of every candidate surface that *could* be an H21 identifier:

| Surface | Evidence | Verdict |
|---|---|---|
| A `show_*` cfg key gating a candidate panel | grep of `GUI/` + `foxml_suite.cpp` for `bool show_` returns only `ChartSettings` **overlay** toggles (`ChartPanel.hpp:38-44,50,57`) — `show_ribbon`, `show_price_tag`, `show_session_hl`, `show_session_div`, `show_spread`, `show_crosshair`, `show_ml_overlay`, `show_all_levels`. None is a panel-visibility flag; none belongs to a retirement candidate; `ChartSettings` is a stack local (`GuiThread.hpp:462`, `foxml_suite.cpp:293`) and is **never persisted** | **not an identifier** |
| A cfg-field-registry key for any panel | grep of `CoreFrameworks/CfgFieldRegistry.hpp` for `latency\|equity\|chart\|panel\|gui_` returns only doc-comment cross-refs (`:114,240,242,246`) and one unrelated kill-switch tooltip (`:630`). **No panel cfg key exists** | **not an identifier** |
| Persisted GUI state file | `data/foxml_gui_state.txt` contains exactly `font_scale=0.600`; writer/reader at `GuiThread.hpp:226-241` + `foxml_suite.cpp:212-227`. No panel key | **not an identifier** |
| ImGui layout ini window-name keys | `foxml_gui.ini` (27 windows) / `foxml_suite.ini` (28 windows). ImGui-owned operator state, rewritten on every exit, **not** an engine wire/persist identifier. Already demonstrably tolerant of orphans (`[Window][Per-Core P&L]` `:119`, `[Window][Per-Core Latency]` `:136` — stale since the per-core→per-node rename, harmless) | **not an H21 identifier;** no tombstone owed |
| A persisted enum CODE or bitmap bit owned by a candidate | none — the four panels are pure readers; the only bits they consult (`gate_flags`, `state_flags`) are read-shared with surviving panels | **not engaged** |
| `TUISnapshot` / `PerNodeSnap` as a persisted or HMAC'd struct | grep for `sizeof(TUISnapshot)` / `fwrite.*TUISnapshot` / `static_assert.*TUISnapshot` returns **only** `static_assert(offsetof(TUISnapshot::PerNodeSnap, ensemble_active) % 64 == 0, ...)` (`EngineTUI.hpp:1429`) — an **H6 cache-line** assert, not an H9/H12 wire size-pin. `TUISnapshot` is an in-memory seqlock double-buffer, never serialized. The persisted wire spec is `FOREACH_NODE_PERSIST_FIELD` / `SHARDED_SNAPSHOT_VERSION`, a different structure entirely | **H21 not engaged by field removal — but H6 / `check_cache_layout.py` IS** |

**Verdict: no tombstone is owed for any of the four panel retirements.** The one caveat is that *snapshot-field* removal (the § 3 follow-on work) is an **H6/cache-layout** event, not an H21 event — different gate, still a gate.

---

## 6. OPTION MATRIX

| # | Option | Info loss | Dead-surface freed | Cascade | E.1.2 collision | Verdict |
|---|---|---|---|---|---|---|
| **O1** | Retire all four as asked | Per-node P&L trajectory · equity shape/drawdown geometry · MTM-in-open-position trend | 18 phantom latency fields (declaration-only) · `paper_reset_seq` · **`TradeReader.hpp` entirely (269 lines, 25 KB, a 60 Hz `stat()`)** | 4 phases, 30+ sites | none if § 3 STOP LINE honored | **Viable — but discards a real trajectory capability** |
| **O2** | Retire `Latency` only | **ZERO** | phantom block exposed for a later leaf | 5 sites, 1 phase | none | **Strictly free. Should happen regardless of every other decision.** |
| **O3** | Retire `Latency` + `Equity Curve`; **keep** `Per-Node P&L` + `Live P&L` | equity shape/drawdown geometry only | phantom block + **all of `TradeReader.hpp`** | Phases 1 + 4 | none | **Best win-to-loss ratio.** Gets 100% of the architectural payoff for one modest visual loss |
| **O4** | Retire `Latency` + `Live P&L` + `Equity Curve`; **keep** `Per-Node P&L`; roll `Stats` into `Account` | all P&L-over-time visualization in the GUI | phantom + `TradeReader.hpp` | Phases 1, 3, 4, 0.2 | none | Viable; the "all P&L trend dies" coupling (§ 2 candidate 3 bucket b) is the thing to weigh |
| **O5** | Full O1 **plus** the snapshot-field deletion (`TUISnapshot` latency block + `paper_reset_seq` + the `EngineTUI` accumulators + the 6 dead `TUI_*` fns) | same as O1 | everything, for real | 4 phases + a layout-gate re-run | **⚠ DIRECT — `EngineTUI` is a `TUISharedState` member (`:1545`), realigned at `7778c66` this ship** | **DO NOT do now.** Name it, home it, ship it after E.1.2 closes |
| **O6 — NOVEL ALTERNATIVE CONSIDERED** *(`feedback_proactive_novel_alternative_consideration`)* | **Consolidate rather than retire: fold `Live P&L` + `Equity Curve` + `Per-Node P&L` into ONE "P&L" window with three ImPlot tabs (`ImGui::BeginTabBar`), and delete `Latency` outright.** Net window count 27→25 (same declutter as O1), but every bucket-(c) datum survives. `Stats` folds into `Account` per 0.2 | **ZERO** | phantom block; `TradeReader.hpp` **retained** (still feeds the equity tab) | ~3 sites + one new tab-bar wrapper; no signature changes, no file deletion | none | **The "have both" option.** Costs the `TradeReader.hpp` win and adds one small piece of UI code. Include it so the fork is decided on merit, not by default |

---

## 7. RECOMMENDATION

**Two decisions, decoupled — they are not one ship.**

**(A) Retire `Latency` NOW, unconditionally, independent of everything else.** It is a Class-2 GUI lie (a panel titled LATENCY that structurally cannot ever display latency), a Class-44 producer-orphan, and Class-40 dead code compiled into the operator's binary. Zero information loss, five sites, no cascade, no E.1.2 collision. It is not a "minor cleanup" item — it is a correctness item on a monitoring surface for a capital-bearing engine, and the operator's screenshot was the system telling her so. **This is the strongest finding of the pass and I would fire it on its own.**

Note loudly for the operator: **this does not remove hot-path latency observability.** `Per-Node Latency` (`DashboardPanels.hpp:2248-2405`) is the surface that actually carries it — per-node samples/min/avg/p50/p95/p99/**LTp99**/max plus a slow-path table plus a 5-section work breakdown, and the LTp99 columns are the just-landed, operator-verified work from `47c06b9`. Retiring `Latency` **protects** that work by removing the empty panel that makes the real one look redundant.

**(B) For the other three, take O3 or O6 depending on one operator answer:** *does she read the per-node P&L trajectory, or only the current numbers?*

- If she reads the trajectory → **O6** (consolidate into one tabbed P&L window). Same declutter, zero loss, costs the `TradeReader.hpp` deletion win.
- If she does not → **O3** (`Latency` + `Equity Curve` out; `Per-Node P&L` + `Live P&L` stay). This banks the entire architectural payoff — the 269-line orphan file, the 25 KB, the 60 Hz `stat()` — for one modest visual loss (drawdown geometry, whose scalar summary already lives in `Stats` at `:1804-1806`).

**In both branches, additionally do:** delete `GUI_Panel_Config` (`:1255-1313`, zero callers — a free Class-40 close), and treat "roll Stats in" as a **MOVE into `Account`**, never a delete (field-set intersection is empty; the information is 100% unique).

**Defer explicitly (homed, not dropped):** the `TUISnapshot`/`EngineTUI` latency-block deletion and the six dead `TUI_*` functions. That is O5, it collides with E.1.2.A's `TUISharedState` realign, and it deserves its own leaf with the cache-layout gate re-run. **Per `feedback_no_unhomed_debt_code_smell`, this needs a plan home before the retirement ships** — the natural one is the same roadmap file that owns EV-1/EV-2 (`plans/_future/2026-05-12-decoupling-endgoal-roadmap.md`), since it is squarely GUI↔runtime/TUISnapshot plane.

---

## 8. HAZARDS

| ID | Severity | Hazard |
|---|---|---|
| **H-1** | **HIGH** | **The `Latency` panel's emptiness is not a warmup artifact.** Any plan built on "it fills in once hot_count > 0" is built on a false premise. `TUISnapshot::hot_count` has no producer (`EngineTUI.hpp:1001`; exhaustive grep: reads only). |
| **H-2** | **HIGH** | **`TUISnapshot` / `EngineTUI` field removal is a LAYOUT event.** `static_assert(offsetof(TUISnapshot::PerNodeSnap, ensemble_active) % 64 == 0)` (`:1429`) + four `[STRADDLE_EXEMPT]` tags (`:1100-1103`, newest dated 2026-08-14) + the `check_cache_layout.py` shrink-only HARD gate. Not a free deletion. |
| **H-3** | **HIGH** | **E.1.2 COLLISION — `EngineTUI tui;` is a member of `TUISharedState` (`:1545`)**, whose control cluster was realigned this ship (`7778c66`) under `static_assert(alignof == 64)` (`:1552`). Removing the dead accumulators touches in-flight scope. **Named and stopped.** |
| **H-4** | **MED** | **`Per-Node P&L` retirement voids an open EV-1 item.** The roadmap's "3 genuine AUTO-mode display defects" list cites `DashboardPanels.hpp:1690-1693` — inside the retirement candidate. Must be marked MOOT-BY-DELETION in the roadmap, not silently orphaned (`feedback_moot_unreachable_disposition` shape). |
| **H-5** | **MED** | **Phase-4 ordering is load-bearing.** Deleting `TradeReader.hpp` before removing `GUI_PriceChart`'s dead `trades` param and the two `TradeData` instances breaks the build in both binaries. |
| **H-6** | **MED** | **`foxml_suite` is a co-equal consumer and is easy to forget.** `foxml_suite.cpp:423` calls `GUI_RenderDashboard`, so it renders `Per-Node P&L` and `Latency` too; `:456-457` render both charts. Every deletion is a two-binary change. The suite's `Suite_SetupDefaultLayout` (`:45-83`) has different rows than the engine's. |
| **H-7** | **MED** | **Zero test coverage for all four panels.** The deletion cannot be verified green by `./build.sh test`; only a compile + a live eyeball proves it. `feedback_passing_test_is_not_verification` applies with force — a green suite here means nothing. |
| **H-8** | **LOW** | **Two stale comments will mislead the next reader if not swept:** `EngineTUI.hpp:979-982` names the equity curve as a `paper_reset_seq` consumer (it isn't); `EngineTUI.hpp:132` claims `tsc_per_ns` is "calibrated at startup" (it never is). Both are `SUBAGENT_ARMING` § 2.5 stale-code-fact instances. |
| **H-9** | **LOW** | **`GUI_PriceChart`'s dead `trades` param is a pre-existing Class-40 instance**, live at HEAD independent of any retirement decision (`ChartPanel.hpp:241`). |
| **H-10** | **LOW** | **`GUI_Panel_Config` is a pre-existing dead panel** (`:1265-1308`, zero callers) — Class 40, unrelated to the four, free to close. |

---

## 9. SPOTS MOST WORTH AN ADVERSARIAL REFUTE (for the paired a-class)

Ranked by how much damage a wrong answer does. These are where I would push hardest at myself.

1. **⭐ THE LOAD-BEARING CLAIM — "`TUISnapshot::hot_count` and the 17 sibling latency fields have ZERO producers."** My entire Correction 1, the O2 recommendation, and the "zero information loss" verdict all rest on this single negative-existence claim, and **a negative existence claim from grep is exactly the shape that fails silently** (`feedback_verify_by_context_not_count`). Attack vectors I did NOT fully exclude: (i) a whole-struct assignment `*snap = something` where the RHS has the fields set; (ii) a macro that constructs the field name by token-paste; (iii) a `memcpy` into the snapshot from a differently-typed source; (iv) population in a build configuration I did not exercise. **The decisive refutation is empirical, not textual: run `./build.sh gui`, start the engine, let warmup complete, and look at the Latency tab.** If it stays empty after `hot_count` would plausibly be nonzero, I am right. If it populates, my strongest finding is dead and O2 inverts.
2. **The "`GUI_PriceChart` never uses `trades`" claim** (`ChartPanel.hpp:241`) — the sole load-bearer for "retiring Equity Curve kills all of `TradeReader.hpp`", which is the entire architectural payoff of O3. My evidence is a 9-hit grep over one file. Refute by compiling with `-Wunused-parameter` on that TU, or by deleting the param and seeing if it links.
3. **Correction 2 — "the per-node table lives in `Account`, not `Per-Node P&L`."** I read `Begin("Account")` at `:1015` and `End()` at `:1247` and placed the table at `:1104-1232` between them. A misread of an intervening `End()` would invert the candidate-2 verdict entirely. Re-verify the brace/Begin-End nesting directly.
4. **"`pnl_history` keeps a live ANSI consumer, so Live P&L frees nothing."** This depends on `ANSI_Section_Charts` being *reachable* — it is only in the CHARTS layout (`TUIAnsi.hpp:1227+`), reached by cycling `[l]` at `EngineTUI.hpp:2436`. If the operator never uses the ANSI TUI at all, the field is *de facto* orphaned and Live P&L's retirement DOES free surface. **This is an operator-behavior question my code-read cannot answer.**
5. **My deferral of O5 on E.1.2-collision grounds.** `feedback_no_defer_for_effort` says defer is last-ditch. Push me: is the `TUISharedState` layout collision *real*, or am I over-reading it? `EngineTUI tui;` at `:1545` is a member, and the struct carries `alignof == 64`; but if `tui` sits after every `alignas(64)` anchor, shrinking it might disturb nothing measurable. **The mechanical arbiter is `tools/check_cache_layout.py --strict-new`, which I did not run against a hypothetical shrink.** If it comes back clean, O5 folds into the same ship and my deferral was effort-avoidance wearing a safety hat.
6. **"Zero tests reference these panels."** Another negative-existence claim, same failure mode as #1. I grepped `tests/` for six symbol names. A test that exercises them via a wrapper, a string literal, or a golden-output comparison would not match.
7. **The `Stats`↔`Account` "field-set intersection is EMPTY" claim.** I enumerated both read-sets by hand from `:1732-1816` and `:1014-1248`. A hand enumeration is exactly what M9 (`feedback_enumerate_set_before_categorical_claim`) exists to distrust. One missed overlapping field turns a "pure move" into a de-duplication decision.
8. **Whether `Latency` deserves deletion at all, versus REPAIR.** The genuinely adversarial reading of my own recommendation: the bg/eg/pc sub-timing *capability* was presumably real once and is architecturally desirable (per-component hot-path attribution is exactly what an HFT engine wants). "Delete the phantom" and "restore the producer" are both valid closures of a Class-2 lie, and I chose the cheaper one. **A refuter should argue for restoration** — wire `NodeLatencyStats` sub-timers into the per-node path and give the operator real bg/eg/pc columns in `Per-Node Latency` — and make me defend deletion on merit rather than on cost.

---

## 10. FILES READ (all absolute paths)

`/home/caramel/code/FoxML_Trader_v2/GUI/GuiThread.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/DashboardPanels.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/ChartPanel.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/TradeReader.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/CLAUDE.md` · `/home/caramel/code/FoxML_Trader_v2/foxml_suite.cpp` · `/home/caramel/code/FoxML_Trader_v2/DataStream/EngineTUI.hpp` · `/home/caramel/code/FoxML_Trader_v2/DataStream/TUIAnsi.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EngineSharded/Async.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ShardedSnapshot.hpp` · `/home/caramel/code/FoxML_Trader_v2/build.sh` · `/home/caramel/code/FoxML_Trader_v2/CMakeLists.txt` · `/home/caramel/code/FoxML_Trader_v2/foxml_gui.ini` · `/home/caramel/code/FoxML_Trader_v2/foxml_suite.ini` · `/home/caramel/code/FoxML_Trader_v2/data/foxml_gui_state.txt` · `/home/caramel/code/FoxML_Trader_v2/DOCS/CODE_MAP.md` · `/home/caramel/code/FoxML_Trader_v2/DOCS/TOOLS.md` · `/home/caramel/code/FoxML_Trader_v2/DOCS/SUBAGENT_ARMING.md` · `/home/caramel/code/FoxML_Trader_v2/plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` · `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/reports/2026-08-14-ui-position-settings-mismatch/i-class-positions-legcount-attribution.md` · `/home/caramel/code/FoxML_Trader_v2/.claude/skills/dead-code-trace/SKILL.md` · `/home/caramel/code/FoxML_Trader_v2/.claude/skills/trace-deps/SKILL.md`

**Mechanical tools RUN:** `tools/calls_graph_diff.sh` → `CLEAN — no strategy/regime functions orphaned or dead-defined` (note: its `SHARDED_FILES` scope does not cover `GUI/`, which is why the GUI orphans above required manual tracing) · `tools/check_identifier_retirement.py` → `GREEN — 47 persisted/wire identifiers match the ledger`.

**Skills walked:** `/dead-code-trace` (candidate identification → multi-vector verification trace → TIER 1/2/3 classification → removal plan, no edits) · `/trace-deps` Step 5 transitive-dependency + Step 6 call-sequence + COHORT-PARITY (the engine_gui ↔ foxml_suite sibling pair) · `/bug-check` Class 2 / 40 / 44 keying per the spawn kit.
