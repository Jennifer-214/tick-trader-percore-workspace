---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: I-3 — post-retirement information architecture; where `Stats` lands + the surviving layout + EV-1/EV-2/decoupling reconciliation
agent_class: i-class
delivered: 2026-08-15
ground: engine HEAD 09824e8 (pre-D-289/2), branch feat/v5.15-live-readiness
consumed_by: the UI-consolidation triage + the fox-tui layout-spec decision
sister_reports: i-class-panel-persistence.md · i-class-panel-retirement-blast-radius.md (this directory)
headline: D-26 hard-deprecates the ImGui GUI at .E.2 (STATUS landed) AND the drafted fox-tui layout has NO session-statistics block at all — the real "where does Stats land" question is a spec edit, not a panel merge
---

# I-3 — Post-retirement information architecture: where `Stats` lands + the surviving layout

**Repo** `/home/caramel/code/FoxML_Trader_v2` @ HEAD `09824e8` · branch `feat/v5.15-live-readiness` · **read-only, nothing changed**
**Skill applied:** `/trace-deps` (`/home/caramel/code/tick-trader-percore-workspace/claude-skills/trace-deps/SKILL.md`) — Step 2/3 callee existence + signature, Step 5 transitive data-source trace, Step 6 mirror data-flow audit (the "walk the source range for struct field reads, verify the Y-side equivalent" procedure is what surfaced F-2 below), plus the COHORT-PARITY section (§ 428-436) applied to the panel cohort.
**Tools run:** `tools/check_code_tag_blocks.py` (202 files / 791 tag-blocks; 1 violation — see F-6, not mine) · `DOCS/CODE_MAP.md` consulted for `GUI_RenderDashboard` (:1005) and `GUI_Panel_Config` (:999) · `tools/lib/sharded_files.txt` read to establish `calls_graph_diff.sh` scope. Layout/latency/struct tools NOT run — no struct, wire, or hot-path change in scope (GUI render thread only, H3-isolated).

---

## § 0. FRAME CORRECTION — read this first

**The dock inventory the directive names as SSoT is dead code for this operator.**

`Gui_SetupDefaultLayout` (`/home/caramel/code/FoxML_Trader_v2/GUI/GuiThread.hpp:355-400`, dock calls `:370-394`) runs **only when no saved layout exists** — the gate at `/home/caramel/code/FoxML_Trader_v2/GUI/GuiThread.hpp:476-484`:

```text
if (ImGui::DockBuilderGetNode(dockspace_id) == NULL ||
    ImGui::DockBuilderGetNode(dockspace_id)->ChildNodes[0] == NULL) {
    Gui_SetupDefaultLayout(dockspace_id);
}
```
*(fence retagged cpp→text at save: a verbatim QUOTE of `GUI/GuiThread.hpp:476-484`, not a compilable sample — B-Plus compile-probe exclusion; content unchanged)*

Layout persists to `foxml_gui.ini` (`/home/caramel/code/FoxML_Trader_v2/GUI/GuiThread.hpp:174`), and **that file exists and is current**: `/home/caramel/code/FoxML_Trader_v2/foxml_gui.ini`, 3104 B, mtime **Aug 15 13:32** — i.e. modified today, this session. Three consequences that change the whole directive:

1. **The real layout is the `.ini`, not the C++.** Anything I say about "which node a panel sits in" must come from the `.ini`. I re-derived it (§ 2).
2. **The directive's premise about `dock_left_bottom` is wrong in her seat.** It says retiring `Live P&L` + `Equity Curve` "empties `dock_left_bottom` down to just `Volume`". In her actual layout that node also holds `Engine` and `Per-Node Latency`, so it drops to **three** tabs, not one. Nothing empties.
3. **A DockBuilder-only change is invisible to her.** Shipping a new default layout does nothing until she deletes `foxml_gui.ini` — and deleting it destroys every hand-docking she has done. `Gui_SetupDefaultLayout` places 16 windows; the code renders 23; **7 of her docked windows are hand-placed and would be lost** (`Engine`, `ML Status`, `Risk`, `Per-Node Latency`, `Engine Topology`, `Strategy Quality`, `Per-Node P&L`). That is a real operator cost of any "just change the default layout" proposal, and it is not obvious from the code.

Also: `Gui_SetupDefaultLayout` is itself **stale** — it docks 16 of 23 live windows, and its `[OVERVIEW]` tag (`GuiThread.hpp:351`) describes "price over volume/P&L/equity", a shape the retirement removes.

---

## § 1. CONTENT CENSUS — every surviving panel

The directive's list was incomplete by three: it missed **`Engine`** (the `EngineHeaderPanel` window), **`Risk`**, and the dead **`Config`**. Full enumeration from the 24 `ImGui::Begin(` sites in `GUI/`:

**23 live windows + 1 dead.** Vertical estimates are in ImGui text rows (~19 px each at her font scale); "node" is her live `.ini` assignment (§ 2).

### Retiring (4) — mapped by the sibling agent, listed here only for completeness

| Window | Site | Node | Note |
|---|---|---|---|
| `Latency` | `GUI/DashboardPanels.hpp:1834-1897` | 0x6 t1 | `#ifdef LATENCY_PROFILING` (`:1823`) — **but `build.sh:162` passes `-DLATENCY_PROFILING=ON` for `gui`**, so it IS compiled in her binary. Do not assume it is already absent. |
| `Per-Node P&L` | `GUI/DashboardPanels.hpp:1624-1715` | 0xA t0 | ImPlot line chart, 1800-sample ring, `static` state inside the fn (`:1625-1632`) |
| `Live P&L` | `GUI/ChartPanel.hpp:1405` | 0x4 t1 | |
| `Equity Curve` | `GUI/ChartPanel.hpp:1477` | 0x4 t2 | reads `TradeData` (CSV) |

### Surviving (19)

| Window | Definition | Node·tab | What it shows | Vert. |
|---|---|---|---|---|
| `Price Chart` | `GUI/ChartPanel.hpp:244` | 0x3 t0 | candlesticks + VWAP/SMA/session overlays + per-node entry/TP/SL markers w/ drag-edit + ML overlay | fills (large) |
| `Volume` | `GUI/ChartPanel.hpp:1276` | 0x4 t0 | per-candle buy/sell volume bars | fills (short OK) |
| `Header` | `GUI/DashboardPanels.hpp:146-266` | 0xB t0 | kaomoji + version, LIVE/PAPER, STATE, warmup progress, UPTIME, PAUSED+gate reason, session, `CORES:` strategy strip | ~8 rows |
| `Top Bar` | `GUI/DashboardPanels.hpp:283-315` | 0xB t1 | price, volume, total P&L, regime short-name, POS n/max — the compact strip | **1 row** |
| `Market` | `GUI/DashboardPanels.hpp:332-549` | 0xB t2 | regime, slope, ror, stddev, dev, vwap, book, vol ratio, long/short, node census, FoxML conf/cost/bandit | ~14 rows |
| `Buy Gate` | `GUI/DashboardPanels.hpp:550-1013` | 0x3 t1 | entry-gate diagnostics — the display half of the display↔execution invariant; 1 table + 1 CollapsingHeader per-node detail | ~20+ rows |
| `Account` | `GUI/DashboardPanels.hpp:1014-1248` | 0xA t1 | equity/balance, realized/unrealized/return, gross/net/fees, maker-taker split, exposure/risk/breaker, **+ embedded `PER-CORE P&L` 7-col table (`:1104-1232`)**, + `Reset Paper` button (`:1235-1245`) | ~17 rows |
| `Positions` | `GUI/DashboardPanels.hpp:1325-1608` | 0xC t0 | 12-col open-position table: `# Strat Entry Now Diff TP SL Value Gross Net Hold Act`, pair-aware `#0.A/#0.B` | ~5 + N rows |
| **`Stats`** | `GUI/DashboardPanels.hpp:1732-1816` | **0x6 t0** | see § 3 | **~5 rows** |
| `ML Intelligence` | `GUI/DashboardPanels.hpp:1899-2087` | 0x6 t7 | 5 CollapsingHeaders: Bandit Arms / Confidence / Cost Model / Models / Per-Node ML; 2 tables | ~25 rows collapsed-dependent |
| `Risk` | `GUI/DashboardPanels.hpp:2122-2243` | 0xB t3 | per-node kill-switch: Node/Strat/Peak/Curr/DD%/Trips/Status/**Reset button**. Gated `sharded_mode_active && per_node_count>0 && shared` | ~6 rows |
| `Per-Node Latency` | `GUI/DashboardPanels.hpp:2247-2406` | 0x4 t4 | 3 sections: hot-path (10 col), slow-path, slow-path work breakdown. Gated sharded | ~25 rows |
| `Engine Topology` | `GUI/DashboardPanels.hpp:2416-2596` | 0x6 t5 | nproc, pin offset, shared-thread table, per-engine thread table + **Pause/Resume buttons**. Gated sharded | ~20 rows |
| `Engine` | `GUI/EngineHeaderPanel.hpp:37` | 0x4 t3 | one-line build-time version/format/registry-hash + cfg path + WS heartbeat freshness | **1-2 rows** |
| `ML Status` | `GUI/MLStatusPanel.hpp:39` | 0x6 t4 | per-ML-node model load tri-state, prediction/threshold/confidence, NaN/Inf counters, ConfidenceScorer IC+RMSE (4 CollapsingHeaders, 2 tables) | ~20 rows |
| `Settings` | `GUI/SettingsPanel.hpp:1999` | 0x3 t2 | Global tab + N per-node tabs; 8 CollapsingHeaders; **the EV-2 surface** | fills (very large) |
| `Trade History` | `GUI/TradeHistoryPanel.hpp:267` | 0x6 t2 | sortable 12-col completed-round-trip table from **CSV on disk** | fills (`ImVec2(0,-1)` at `:290`) |
| `Strategy Quality` | `GUI/StrategyQualityPanel.hpp:345` | 0x6 t3 | per-strategy entry/exit quality aggregates from `health.jsonl`, Refresh button | ~10 rows |
| `Engine Log` | `GUI/LogViewerPanel.hpp:129` | 0x3 t3 | tail of `engine.log`, color-coded, auto-scroll | fills |

**Data-plane split (load-bearing for § 4):** 16 of 19 read **only** `const TUISnapshot*` (in-memory, seqlock-published). **Three read disk**: `Trade History` (CSV), `Strategy Quality` (`health.jsonl`), `Engine Log` (`engine.log`) — these are the `FOREACH_PANEL` stateful set (`GUI/GuiThread.hpp:82-86`) plus `Settings` (writes `engine.cfg`). `Equity Curve` (retiring) is a fourth disk reader.

**Not surveyed:** `Backtest/BacktestPanels.hpp` windows — those belong to `foxml_suite`, a different binary. Out of scope; flagging so nobody assumes coverage.

---

## § 2. HER ACTUAL LAYOUT (parsed from `foxml_gui.ini`)

```
DockSpace 0xE485E63A  1896x1014  Split=X
├─ 0x1  left   SizeRef 1125x1014  Split=Y
│  ├─ 0x3  1125x628 : Price Chart(0) · Buy Gate(1) · Settings(2) · Engine Log(3)
│  └─ 0x4  1125x384 : Volume(0) · Live P&L(1)† · Equity Curve(2)† · Engine(3) · Per-Node Latency(4)
└─ 0x2  right  SizeRef  761x1014  Split=Y
   ├─ 0x5  Split=Y
   │  ├─ 0x9  Split=Y
   │  │  ├─ 0xB  769x176 : Header(0) · Top Bar(1) · Market(2) · Risk(3)
   │  │  └─ 0xC  769x239 : Positions(0)
   │  └─ 0xA  769x231 : Per-Node P&L(0)† · Account(1)
   └─ 0x6  769x362  CentralNode=1 :
            Stats(0) · Latency(1)† · Trade History(2) · Strategy Quality(3)
            · ML Status(4) · Engine Topology(5) · [Per-Core Latency(6) STALE] · ML Intelligence(7)
```
† = retiring. Two `.ini` entries are **stale renames** with no live window: `Per-Core Latency` (now `Per-Node Latency`, `DashboardPanels.hpp:2248`) and `Per-Core P&L` (now `Per-Node P&L`, `:1660`). Harmless ImGui leftovers; they will never be selected.

**The one overloaded node is `0x6`** — 7 live tabs in a 362 px-tall node. It is also the `CentralNode`. Every "where does `Stats` go" question is really "how do I get `0x6` down to something scannable".

---

## § 3. WHAT `Stats` ACTUALLY CONTAINS — and is it cohesive?

`GUI_Panel_Stats(const TUISnapshot *s)` — `/home/caramel/code/FoxML_Trader_v2/GUI/DashboardPanels.hpp:1732-1816`. Stateless; takes the snapshot and nothing else. Four rendered rows:

| Row | Datum | Snapshot field | Publisher (sharded/production) |
|---|---|---|---|
| 1 | `buys:` | `total_buys / 2` under partials (`:1741-1742`) | `ShardedSnapshot.hpp:316` ← `agg.total_entries` |
| 1 | `(N fills)` | `total_buys` | same |
| 1 | `exits:` | `wins + losses` (`:1736`) | `ShardedSnapshot.hpp:866-867` |
| 1 | `(N fills)` | `total_exits_fills` | `ShardedSnapshot.hpp:317` |
| 1 | `W:` / `L:` | `wins` / `losses` | `ShardedSnapshot.hpp:866-867` (Σ per-node) |
| 2 | `rate:` | `win_rate` | `ShardedSnapshot.hpp:869/871` |
| 2 | `pf:` (or ∞) | `profit_factor` / `all_wins_run` | `ShardedSnapshot.hpp:882-883` |
| 2 | `avg W:` / `L:` | `avg_win` / `avg_loss` | `ShardedSnapshot.hpp:876-877` |
| 2 | `(mkt: $…)` | **`avg_loss_market`** | **NEVER WRITTEN — see F-2** |
| 3 | `E[trade]:` | `expectancy` | `ShardedSnapshot.hpp:884-886` |
| 3 | `maxDD:` + `(% / %)` | `max_drawdown`, `max_drawdown_pct`, `max_dd` | `ShardedSnapshot.hpp:152-154` |
| 3 | `fees/wins:` | **`fee_ratio`** | **NEVER WRITTEN — see F-2** |
| — | partials gating | `partial_exit_enabled` | `ShardedSnapshot.hpp:367` |

### Cohesion verdict: **COHESIVE — do not split.**

All four rows answer one question: *how has this session's closed-trade population performed?* Counts → rates → per-trade magnitudes → risk. Every field except the two broken ones comes from the **same aggregation block** in the same publisher (`ShardedSnapshot.hpp:855-888`, the post-loop aggregate-publishing block) or the drawdown trio at `:152-154`. There is no seam where a natural sub-group wants a different home. A split would scatter one derivation cluster across panels and make the EV-1 unit fixes an N-site edit instead of a 1-site edit.

The one *arguable* seam is `maxDD` (a risk number, arguably `Risk`-adjacent), but `Risk` is per-node kill-switch state while `max_drawdown` is the session aggregate — different scope. Keep it with Stats.

**Vertical footprint: ~5 text rows (~95 px) in a 362 px node.** `Stats` uses roughly a quarter of the tab it occupies. That is the strongest single argument that it should not own a tab.

### Two NEW findings inside `Stats` (not in the frozen EV-1 report)

**F-1 · MED · dead render branch.** `fee_ratio` is read at `GUI/DashboardPanels.hpp:1807` but its **only writer repo-wide** is `DataStream/EngineTUI.hpp:1932`, inside the legacy `TUI_CopySnapshot` (`PortfolioController`) publisher. The production GUI feed is `TUI_CopySnapshotSharded` (`CoreFrameworks/ShardedSnapshot.hpp:58`), published at the single site `CoreFrameworks/EngineSharded/Async.hpp:493` → `:507`; it `memset`s the snapshot at `ShardedSnapshot.hpp:66` and never assigns `fee_ratio`. So `fee_ratio` is **always 0.0** and the guard `if (s->fee_ratio > 0.0)` is **always false** — the `fees/wins:` row has never rendered on the sharded path.

**F-2 · MED-HIGH · the dashboard states a false number.** Same mechanism for `avg_loss_market` (only writer `DataStream/EngineTUI.hpp:1915-1916`). But its guard is not protective:

```text
if (s->losses > 0 && s->avg_loss_market < s->avg_loss) {          // :1792
    ImGui::TextColored(FoxmlColors::comment, "(mkt: $%.2f)", s->avg_loss_market);
```
*(fence retagged cpp→text at save: a verbatim QUOTE of `GUI/DashboardPanels.hpp:1792-1795`, not a compilable sample — B-Plus compile-probe exclusion; content unchanged)*

`avg_loss` is a **positive magnitude** — `node_gross_losses` accumulates `Money_Negate(...)` at `CoreFrameworks/ControllerEventLoop.hpp:1830-1831` and `:1850-1851`. So with `avg_loss_market == 0.0` the condition is **true whenever any loss exists**, and the panel prints `(mkt: $0.00)` — asserting that the ex-fee market component of the average loss is zero, i.e. that 100 % of every average loss was fees. That is a Class-2 display↔execution lie on a money readout, and it is live today.

The ANSI TUI carries the identical pair — `DataStream/TUIAnsi.hpp:855-856` and `:866-867` — so this is a 2-surface instance, not a GUI one-off.

This is **exactly the EV-1 family**: EV-1 § 5 found the Stats plane reading a counter family the sharded path doesn't persist; F-1/F-2 are the Stats plane reading two fields the sharded path doesn't **write at all**. Same shape, one layer worse. It belongs in EV-1, and it materially raises the value of touching `Stats` at all.

---

## § 4. CANDIDATE HOMES — ranked

Evaluated on information cohesion, screen-space, target-node room, decoupling-trajectory effect, and operator gain/loss (per `feedback_evaluate_options_on_robustness_latency_design_not_time` — time is not an axis here).

| # | Option | Cohesion | Space | Target room (her layout) | Decoupling effect | Verdict |
|---|---|---|---|---|---|---|
| **1** | **Fold into `Account`** | **HIGH** — both are session-aggregate money/outcome from the *same publisher block*; `Account` is **already** a composite (it embeds a `PER-CORE P&L` table at `:1104-1232`); both are pure `const TUISnapshot*` readers → **zero new coupling** | `0x6` 7→6 tabs; `Account` ~17→~21 rows | `0xA` is 769×231 and `Account` already overflows it; **but `Per-Node P&L` retires from `0xA`, leaving `Account` alone in the node** → she can grow it | **NEUTRAL-POSITIVE** — one snapshot plane, one window; transfers cleanly to a fox-tui "node/global summary" pane | **RECOMMENDED** (composed with #6) |
| 2 | **Keep standalone** | n/a | costs 1 of 7 tabs at ~25 % fill | n/a | neutral | **Viable.** The honest baseline: zero risk, zero churn, and given D-26 (§ 6) the opportunity cost is small |
| 3 | Fold into `Trade History` | **Semantically high, mechanically bad** — Stats reads the *snapshot*; Trade History reads *CSV from disk* (`GuiThread.hpp:83`, refresh `TradeHistoryPanel.hpp:269`). The two planes **already disagree** (EV-1: CSV = completed round-trips; Stats = per-fill heartbeats + a non-persisted counter family). Merging renders the contradiction side-by-side in one window | `0x6` 7→6; table is `ImVec2(0,-1)` (`:290`) so it must be re-sized | fine | **NEGATIVE** — couples a stateless snapshot reader into a stateful file-cache panel; mixes mmap-plane and disk-plane in one view, the opposite of the viewer-reads-one-published-plane shape | **REJECT now.** Interesting long-run: the roadmap says "trade history file is canonical; everything else is derivable" (`plans/_future/2026-05-12-decoupling-endgoal-roadmap.md:853-856`) — but that argues for making Stats *derived from* the log, a far bigger change than a panel merge |
| 4 | Fold into `Positions` | **LOW** — `Positions` is open/live per-slot state; Stats is closed-trade outcomes. Different time domain, different cardinality | — | `0xC` holds only `Positions`, so room exists | neutral | **REJECT** — the incoherent merge the directive warns about |
| 5 | Compact strip in `Header`/`Top Bar` | Medium for 2-3 numbers | ~free | **`0xB` is 176 px and `Header`/`Top Bar`/`Market`/`Risk` are TABS in it, not a persistent strip** — so a "strip" would only be visible when that tab is selected, defeating at-a-glance | neutral | **REJECT as stated.** Salvageable variant: promote `W/L` + `win_rate` into `Top Bar` (already the 1-row metric strip, `:283-315`) and fold the rest into `Account` — but that *splits* a cohesive unit (§ 3), so only if she wants those two numbers permanently visible |
| **6** | **NOVEL ALTERNATIVE — `feedback_proactive_novel_alternative_consideration`: extract a reusable DRAW-HELPER instead of moving a window** | — | — | — | **POSITIVE** | **RECOMMENDED, composed with #1** |

### The novel alternative (#6), stated properly

**Don't move a window. Extract the block.** Lift the body of `GUI_Panel_Stats` (`DashboardPanels.hpp:1734-1813`) into a helper — `GUI_Draw_SessionOutcome(const TUISnapshot *s)` — living beside the existing draw helpers in the same file (`PnlColor:34`, `RSquaredBar:54`, `SectionHeader:99`, `LabeledValue:114`). Then `GUI_Panel_Account` calls it at the end, and the `Stats` window + its `GUI_RenderDashboard` call (`:2108`) are deleted.

Why this is better than a plain body-move:

- **It separates the taste call from the engineering.** "Which window shows session outcome" becomes a one-line change she can flip any time. The block itself becomes a stable, named unit.
- **It is the in-file canonical sister pattern**, not new infrastructure (`feedback_audit_canonical_sister_before_new_infra`) — this file already keeps its shared drawing in exactly this shape.
- **It composes with EV-1's O4 instead of competing.** EV-1's locked fix shape is a *unit-typed snapshot contract* (`node_open_legs` / `node_open_trades`, roadmap `:674-679`). A named session-outcome block is the render-side counterpart: one place binds the fields, so the O4 relabelling is a 1-site edit.
- **It survives D-26.** When `engine_gui` is archived, the ImGui calls die but the *contract* — "these 13 fields constitute session outcome, with these units" — is exactly what the fox-tui layout spec needs (§ 6).
- Cost: ~20 lines, no behavior change, no new state, no new coupling.

### Recommendation

**#1 composed with #6, sequenced AFTER EV-1 — and only after the § 6 reconciliation is accepted.** Concretely:

1. `GUI_Draw_SessionOutcome(const TUISnapshot*)` extracted from `DashboardPanels.hpp:1734-1813`.
2. Called from the tail of `GUI_Panel_Account` (after the per-node table at `:1232`, before the Reset-Paper block at `:1235`).
3. `GUI_Panel_Stats` + its call at `:2108` deleted; the `Stats` row dropped from `Gui_SetupDefaultLayout` (`GuiThread.hpp:389`).
4. F-1/F-2 fixed **in the same touch** (they live in the lines being moved).

**What would change this recommendation:**
- **If she wants `Stats` visible at the same time as `Positions`** (i.e. compare open state against session outcome without tab-switching) — `Account` and `Positions` are in *different* nodes (`0xA` vs `0xC`), so #1 preserves that. But if she instead wants it beside the **chart**, none of these options deliver it and the answer is a new node, not a merge.
- **If the operator's real complaint is tab-count in `0x6` rather than `Stats` specifically** — then the higher-leverage move is retiring/merging `Engine Topology` + `ML Status` + `Strategy Quality` (three low-frequency diagnostics sharing that node), and `Stats` should stay put.
- **If EV-1 is going to land soon** — then do nothing here and let EV-1 carry the whole `Stats` touch, including F-1/F-2. Two ships editing the same 80 lines is worse than one.
- **If she declines the D-26 reconciliation** (i.e. wants the ImGui GUI maintained past `.E.2`) — then the calculus flips and a fuller panel-consolidation pass becomes worth real investment.

---

## § 5. POST-RETIREMENT LAYOUT

Against her **real** `.ini`, retiring the four candidates and applying the recommendation:

```
0x3  1125x628 : Price Chart · Buy Gate · Settings · Engine Log          [4 tabs, unchanged]
0x4  1125x384 : Volume · Engine · Per-Node Latency                      [5 -> 3 tabs]
0xB   769x176 : Header · Top Bar · Market · Risk                        [4 tabs, unchanged]
0xC   769x239 : Positions                                               [1 tab, unchanged]
0xA   769x231 : Account (now carries the session-outcome block)         [2 -> 1 tab]
0x6   769x362 : Trade History · Strategy Quality · ML Status
                · Engine Topology · ML Intelligence                     [7 -> 5 tabs]  <- CentralNode
```

- **No node becomes empty.** `0xA` and `0xC` become single-tab, which ImGui handles fine.
- **`0x6` goes 7 → 5 tabs** — the real win. Still the busiest node; still the CentralNode.
- **The freed left-bottom space:** `0x4` keeps three tabs but loses both time-series charts. `Volume` is a short bar chart and `Engine` is one line — the node no longer needs 384 px. **Recommendation: give the height to `0x3` (`Price Chart`), which is the panel that actually benefits from vertical.** Caveat from § 0: `SizeRef` lives in the `.ini`, so this is a drag she performs, not a code change — unless she deletes the ini and accepts the rebuilt default (losing 7 hand-dockings).
- **If a code-side default is wanted anyway:** `Gui_SetupDefaultLayout` should drop `Live P&L`/`Equity Curve`/`Latency`/`Stats` rows (`GuiThread.hpp:372-373`, `:389`, `:391`) and change the left split from `0.70f` to ~`0.82f` (`:369`). Ship it as a *default* correction with the explicit note that her running instance is unaffected.

---

## § 6. RECONCILIATION — EV-1 / EV-2 / the decoupling roadmap

### 6a. The dominant fact: **D-26 — the GUI is hard-deprecated at `.E.2`**

`plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md:118-120`:

> **D-26: GUI hard-deprecate at `.E.2`.** engine_gui binary removed from build; Dear ImGui code archived to legacy/. Replaced by fox-tui + fox-cli + Grafana. Clean break.
> `<!-- STATUS: landed -->`

Corroborated at `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.2-headless-configs-docs.md:270` and `:696` ("Hard deprecation (archived to legacy/; not in build) — **CHOSEN per D-26**"), and at `:714` ("Existing engine_gui Dear ImGui binary → **REPLACE**"). The decoupling roadmap repeats it twice (`plans/_future/2026-05-12-decoupling-endgoal-roadmap.md:54`, `:64`).

**So: every hour of ImGui *layout* work is written off at `.E.2`.** That does not make the exercise worthless — but it relocates where the value is. Which brings the highest-value finding in this report:

### 6b. **The drafted `fox-tui` layout has NO session-statistics block at all**

The fox-tui mock at `plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.2-headless-configs-docs.md:567-595` shows: global P&L / notional / drawdown / kill · per-cluster rate / WS / realized / open · per-node realized / open / hot p99 / slow p99 / last fill · an event tail. **There is no W/L, no win-rate, no profit factor, no expectancy, no avg win/loss.** The entire `Stats` content — the closed-trade performance plane she built — is absent from the replacement viewer's design.

**That is the real "where does Stats land" question, and its answer is a spec edit, not a panel merge.** The consolidation thinking she is doing right now is the *right* thinking aimed at the *soon-to-be-archived* surface. Redirecting it at the fox-tui layout section of the `.E.2` plan is the same taste call with a ~10× longer half-life.

### 6c. Does this work BELONG to EV-1/EV-2, extend them, or warrant a sibling?

- **F-1 and F-2 belong to EV-1, unambiguously.** EV-1's stated cohort already includes "Stats-bar zeros on warm-restart" and "Stats `buys/2` truncation on half-pairs (S15)" (`plans/_future/2026-05-12-decoupling-endgoal-roadmap.md:665-668`). F-1/F-2 are the same counter-family-SSoT shape at the same 80 lines. **Recommend: append to the EV-1 bullet list, no new home.**
- **The `Stats` relocation itself does NOT belong to EV-1.** EV-1 is a correctness cohort (units, counter families, display truth). Panel placement is ergonomics. Filing ergonomics inside a correctness leaf dilutes the leaf's acceptance oracle.
- **It does not belong to EV-2** either — EV-2 is `SettingsPanel.hpp` + the cfg registry render scope (`:731-760`). Zero file overlap with `GuiThread.hpp`/dock layout.
- **Recommend a SIBLING with a specific shape:** a small "viewer information-architecture" item homed in the **decoupling roadmap alongside EV-1/EV-2**, whose *primary* deliverable is the **fox-tui layout content spec** (§ 6b) and whose *optional* secondary is the ImGui merge. Naming it EV-3 keeps it beside its siblings under the same auto-write contract (the roadmap explicitly owns "any ship touching GUI ↔ runtime, TUISnapshot, cfg ownership" per `CLAUDE.local.md`). This routes to a plan home per her directive, not TECH_DEBT.

### 6d. CONFLICT with EV-1 — one real one

**Line-level collision.** EV-1 commits to editing `DashboardPanels.hpp:1731-1752` (S15/A5, the `buys/2` halving) and to re-sourcing the Stats plane from persisted per-node sums (roadmap `:665-668`). A consolidation ship that moves those exact lines first would **invalidate EV-1's cited line ranges** in a frozen report. Two ships editing one 80-line block is the avoidable cost.

**Resolution: EV-1 first, or one leaf.** Either (a) EV-1 lands its Stats fixes, then the merge is a trivial verified body-move; or (b) the merge rides *inside* EV-1 as a final cosmetic step after the correctness edits. **Do not run them as independent concurrent ships.** No other conflict found — EV-1's fix sites are `ShardedSnapshot.hpp` / `ControllerEventLoop.hpp` / `EngineTUI.hpp` / `ChartPanel.hpp`, none of which a dock-layout change touches.

### 6e. Does consolidating help or hurt the decoupled trajectory?

The roadmap's **Anti-breadcrumbs** section (`plans/_future/2026-05-12-decoupling-endgoal-roadmap.md:860-864`) is still empty, and its stated test is "adds in-process-only state that can't be mmap-exposed". Judged against that:

- **Recommendation #1+#6 does NOT hard-couple anything.** `GUI_Panel_Stats` and `GUI_Panel_Account` are both pure `const TUISnapshot*` readers with no state; the merge introduces zero shared mutable state and zero new engine coupling. **Not an anti-breadcrumb.**
- **Option #3 (Trade History) WOULD be a step backwards** and I am saying so explicitly, as the directive asks. It couples a stateless snapshot reader into a stateful disk-cache panel, and mixes the mmap plane with the disk plane inside one view — against the `.E.0.10` breadcrumb's core insight that the viewer reads *the published snapshot* (`:39-46`). If someone proposes it later, it earns an Anti-breadcrumbs entry.
- **The genuinely positive move is #6 + § 6b**: naming the session-outcome block as a *contract* and putting it in the fox-tui spec is a decoupling-shaped move of exactly the kind EV-1's O4 already is.

---

## § 7. E.1.2 ENTANGLEMENT CHECK — **CLEAN**

Nothing in this proposal touches the in-flight E.1.2 scope. `GUI_Panel_Stats` reads only in-memory `TUISnapshot` fields published by `TUI_CopySnapshotSharded` — a struct that is never written to disk and never HMAC'd. No v11 capital-wire field, no `Portfolio_Save/_Load`, no `SHARDED_SNAPSHOT_VERSION`, no F-096 surface. The two dead fields (F-1/F-2) live in `TUISnapshot` (`DataStream/EngineTUI.hpp:984`, `:989`), also non-persisted. **No H21 identifier motion, no version bump, no hot/slow path.**

**One in-flight item I must NAME and stop on (per the scope fence):**

**F-6 · the tag validator is RED on an E.1.2 file.** `tools/check_code_tag_blocks.py` reports exactly one violation repo-wide:
```
CoreFrameworks/Portfolio.hpp:833  UNKNOWN category [TOMBSTONE]
```
The tag is `// [TOMBSTONE]_[Portfolio_Save / Portfolio_Load — DELETED at E.1.2/D-289]` — squarely the in-flight `Portfolio_Save/_Load` retirement. `[TOMBSTONE]` is not in the closed category set the parser accepts (arming § 2.6). **This is E.1.2's to fix, not mine** — either enroll `TOMBSTONE` in the vocabulary or re-express it as a `[COMMENT]` partition. Flagging because it will fail `check_session_docs` at the E.1.2 ship gate.

---

## § 8. FINDINGS REGISTER

| # | Sev | Finding | Cite | Home |
|---|---|---|---|---|
| **F-1** | MED | `fee_ratio` never written on the sharded path → the `fees/wins:` row has never rendered | render `GUI/DashboardPanels.hpp:1807-1812`; only writer `DataStream/EngineTUI.hpp:1932`; sharded publisher `CoreFrameworks/ShardedSnapshot.hpp:58,66`; sibling `DataStream/TUIAnsi.hpp:866-867` | **EV-1** |
| **F-2** | **MED-HIGH** | `avg_loss_market` never written → panel prints `(mkt: $0.00)` on every loss, falsely asserting the loss was 100 % fees. Guard is non-protective because `avg_loss` is a positive magnitude | render `GUI/DashboardPanels.hpp:1792-1795`; only writer `DataStream/EngineTUI.hpp:1915-1916`; sign proof `CoreFrameworks/ControllerEventLoop.hpp:1830-1831,:1850-1851`; sibling `DataStream/TUIAnsi.hpp:855-856` | **EV-1** |
| **F-3** | LOW-MED | **`GUI_Panel_Config` is dead code** — defined, zero callers repo-wide. `calls_graph_diff.sh` cannot catch it (`tools/lib/sharded_files.txt` has no `GUI/` entry), and unused-`inline` deadness is not compiler-caught (H21 explicitly) | `GUI/DashboardPanels.hpp:1265-1308`; absent from `GUI_RenderDashboard` `:2099-2112`; `DOCS/CODE_MAP.md:999` still indexes it | quick-kill, or EV-3 |
| **F-4** | LOW | **Stale comments in `ShardedTradeLog.hpp`** claim the sharded log is `SYMBOL_sharded_order_history.csv`; the code writes `logging/%s_order_history.csv`. **This REFUTES one of EV-1's two open discriminator candidates** for "Trade History shows nothing" — the panel reads the right file (it exists: `logging/btcusdt_order_history.csv`, 1451 B). The remaining candidate (completed-round-trips-only semantics, `TradeHistoryPanel.hpp:230-247,:272`) stands alone | stale `CoreFrameworks/ShardedTradeLog.hpp:36-37` + `:291`; truth `:223` + `:356`; reader `GUI/GuiThread.hpp:83`. Suggested wording: *"Filename: `logging/SYMBOL_order_history.csv` — the aggregate the GUI TradeReader reads; per-node mirrors are `logging/SYMBOL_node_N_order_history.csv` (`:133`)."* | **EV-1** (narrows its open lane) |
| **F-5** | LOW | `Gui_SetupDefaultLayout` is stale: docks 16 of 23 live windows; `[OVERVIEW]` at `:351` describes a chart stack the retirement removes; and it is inert for any operator with a saved `.ini` | `GUI/GuiThread.hpp:351`, `:370-394`, gate `:476-484` | EV-3 |
| **F-6** | MED | Tag validator RED — `[TOMBSTONE]` unknown category | `CoreFrameworks/Portfolio.hpp:833` | **E.1.2 — NAMED, not touched** |
| F-7 | INFO | Two stale window names persist in the `.ini` (`Per-Core Latency`, `Per-Core P&L`) from the E.1.1 Core→Node rename | `foxml_gui.ini` vs `DashboardPanels.hpp:1660`, `:2248` | cosmetic |
| F-8 | INFO | `Latency` is compiled into her GUI binary despite the `#ifdef` — `build.sh:162` sets `-DLATENCY_PROFILING=ON` for the `gui` target (also `:197` debug, `:213` suite) | `GUI/DashboardPanels.hpp:1823`; `build.sh:162` | note for the retirement agent |

---

## § 9. OPEN QUESTIONS — what Caramel must decide

| # | Question | What I'd decide if delegated |
|---|---|---|
| **Q1** | **Given D-26 archives the GUI at `.E.2`, do we invest in ImGui panel consolidation at all?** | **Mostly no.** Do the three near-free things that are true regardless (F-1/F-2 correctness, F-3 dead-code delete, F-4/F-5 stale-comment sweep), and put the *content* decision into the fox-tui layout spec (§ 6b). Treat the `Stats`→`Account` merge as optional ergonomics — worth doing only if it reduces her daily friction now, not as engineering investment. |
| **Q2** | **Where does `Stats` land?** | **`Account`, via the extracted `GUI_Draw_SessionOutcome` helper** (#1 + #6). Highest cohesion, zero new coupling, and the helper is the part that transfers to fox-tui. |
| **Q3** | **Does the session-outcome block (W/L, win-rate, profit factor, expectancy, avg win/loss, maxDD) survive into `fox-tui`?** — the mock at `E.2:567-595` omits all of it. | **Yes — add it.** She built those numbers; a viewer that drops them is a regression dressed as a rewrite. This is the highest-value output of this whole exercise and it is a spec edit she should make while the thinking is fresh. |
| **Q4** | **Sequencing vs EV-1** (§ 6d line collision). | **EV-1 first, or one leaf.** Never concurrent. |
| **Q5** | **New home: EV-3 sibling, or fold into EV-1?** | **EV-3 sibling in the decoupling roadmap**, carrying the fox-tui content spec + F-3/F-5. F-1/F-2/F-4 go to **EV-1** (correctness). Keeps EV-1's acceptance oracle clean. |
| **Q6** | **Do we ship a corrected `Gui_SetupDefaultLayout` knowing it is inert for her** unless she deletes `foxml_gui.ini` and loses 7 hand-dockings? | **Yes, ship the correction; do NOT ask her to delete the ini.** The default should be right for a fresh clone; her layout is hers. |
| **Q7** | **Is her actual complaint `Stats` specifically, or that node `0x6` carries 7 tabs?** — I cannot tell from "stats can probably be rolled into a different tab as well". | **Ask.** If it is `0x6` congestion, the higher-leverage targets are `Engine Topology` + `ML Status` + `Strategy Quality` (three low-frequency diagnostics), and `Stats` should stay. This single answer could invert Q2. |
| Q8 | Does `foxml_suite`'s `Backtest/BacktestPanels.hpp` need the same census? | Out of this directive's scope; flag only. It is a different binary with its own D-6/D-244 CLI trajectory. |

---

## § 10. SPOTS MOST WORTH AN ADVERSARIAL REFUTE (for the paired a-class)

1. **F-2's severity.** I claim `(mkt: $0.00)` renders on every loss. Refute by checking whether `avg_loss` can be ≤ 0 in practice (`Money_Negate` of a positive `total_net` at `ControllerEventLoop.hpp:1831` — is there a path where `exit_net_pnl` is positive but lands in the loss branch, making `gross_losses` negative?), and whether any *other* publisher (a test harness, `BacktestSnapshot_Copy` via `Backtest/BacktestSnapshot.hpp:39`) can write `avg_loss_market` in a GUI-visible run.
2. **The § 0 frame correction.** My whole layout analysis rests on `foxml_gui.ini` being the live layout. Refute by checking the process CWD at launch — `io.IniFilename = "foxml_gui.ini"` is **relative**, and `build.sh` symlinks `engine.cfg` into each build dir. If she runs from `build_gui/`, ImGui writes/reads `build_gui/foxml_gui.ini`, and the repo-root file may be from a different invocation. The Aug 15 13:32 mtime is strong evidence but not proof.
3. **The D-26 argument.** It is the load-bearing claim behind "don't invest in ImGui". Refute by checking whether `.E.2` has slipped, been re-scoped, or whether any later decision softens D-26 — I verified the decision-log entry says `STATUS: landed` and found no superseding entry, but I did not read the full 1600-line decision log.
4. **The fox-tui content-gap claim (§ 6b).** I read one mock at `E.2:567-595`. Refute by searching the rest of the `.E.2` plan (and `E-MASTER-REFERENCE.md`) for a drill-down/detail view that *does* carry win-rate/expectancy — the mock says "`Enter` to drill into a node (detailed view)" without showing that view. If the detail view carries them, my headline gap softens to "not in the top-level mock".
5. **F-3's deadness.** I grepped source excluding `build/`. Refute by including `tests/`, `tools/`, and `Backtest/` with `--no-ignore` (gitignored-in-place dirs), and by checking whether `foxml_suite.cpp` pulls `DashboardPanels.hpp` and calls it.
6. **`Account`'s room.** I estimate `Account` at ~17 rows in a 231 px node — already overflowing before adding Stats' 4. Refute empirically by running `bin/engine_gui`; my estimate is arithmetic on text rows, not screen-verified. If `Account` is already unusably scrolled, option #1 gets worse and #2 (keep standalone) may win.
7. **The `Stats` cohesion verdict.** I claim no natural split. The sharpest counter is `maxDD` + `max_drawdown_pct` + `max_dd` (`:1802-1806`) being risk-plane and arguably belonging with `Risk` (`:2122`). Push on whether session-drawdown and per-node kill-switch drawdown should be co-located for the operator's actual risk workflow.
8. **The EV-1 collision claim (§ 6d).** I assert EV-1 owns `DashboardPanels.hpp:1731-1752`. Verify against the frozen report's § 8 disposition list (`plans/v5.15-live-readiness/reports/2026-08-14-ui-position-settings-mismatch/i-class-positions-legcount-attribution.md:141`) — if S15's fix is snapshot-side only (publisher emits a logical count, GUI just reads it), the GUI-side collision may be one line, not a block, and the sequencing constraint relaxes.

**Files referenced (absolute):** `/home/caramel/code/FoxML_Trader_v2/GUI/GuiThread.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/DashboardPanels.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/ChartPanel.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/TradeHistoryPanel.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/MLStatusPanel.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/EngineHeaderPanel.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/StrategyQualityPanel.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/LogViewerPanel.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/SettingsPanel.hpp` · `/home/caramel/code/FoxML_Trader_v2/foxml_gui.ini` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ShardedSnapshot.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ShardedTradeLog.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerEventLoop.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EngineSharded/Async.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/Portfolio.hpp` · `/home/caramel/code/FoxML_Trader_v2/DataStream/EngineTUI.hpp` · `/home/caramel/code/FoxML_Trader_v2/DataStream/TUIAnsi.hpp` · `/home/caramel/code/FoxML_Trader_v2/build.sh` · `/home/caramel/code/FoxML_Trader_v2/plans/_future/2026-05-12-decoupling-endgoal-roadmap.md` · `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/subplans/2026-05-28-v5.15.5.F.4d.1.E.2-headless-configs-docs.md` · `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/decision-logs/v5.15.5.F.4d.1.E-architecture-v2.md` · `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/reports/2026-08-14-ui-position-settings-mismatch/` (both frozen reports)
