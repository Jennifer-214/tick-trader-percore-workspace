---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: S-5 — complement-blindness sweep, shard 5/5: EMIT/DISPLAY registries + CLOSING THE 68-ROW SET
agent_class: i-class
delivered: 2026-08-15
ground: engine HEAD 7240f3d, branch feat/v5.15-live-readiness
headline: "J2-A — STRATEGY_AUTO / STRATEGY_EMA_CROSS enum values SHIFT depending on __has_include of Strategies/private/, so the same engine.cfg and the same persisted snapshot decode to DIFFERENT strategies in a public build; the H21 guard cannot see it because its row parser silently drops the nested FOREACH_STRATEGY_EMACROSS. Plus E-1: GUI/TradeReader.hpp reads the LEGACY trade-log schema, so chart markers + Equity Curve are unconditionally empty in production — the operator-observed 'the pnl ones arent really working'."
set_closure: all 68 meta-registry rows accounted (47 shards 1-4 + 7 JOB-1 + 14 JOB-2)
novel_proposal: a DOMAIN column on FOREACH_REGISTRY (SSOT / ENUM: / STRUCT: / COUNT: / RANGE: / FORMAT: / PROSE:) so check_meta_registry.py grows ONE dispatching Check 4 instead of ~8 bespoke guards
sister_reports: S1-capital-wire-persist.md · S2-cfg-surface.md · S3-stamp-hmac-ml.md · S4-nodectx-state-bitflags.md
---

# S-5 — COMPLEMENT-BLINDNESS sweep, shard 5/5: EMIT/DISPLAY registries + CLOSING THE SET

**Ground:** engine `/home/caramel/code/FoxML_Trader_v2`, HEAD `7240f3d` (verified `git rev-parse`), branch `feat/v5.15-live-readiness`. Read-only; nothing edited.
**Method template:** `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/reports/2026-08-15-ui-consolidation/i-class-nodecontext-partition.md` (read first).

**Mechanical tools run** (SUBAGENT_ARMING § 3):
| Tool | Result |
|---|---|
| `tools/check_meta_registry.py` | **RC=0** — 68 codebase macros / 68 rows / H15+H19 clean |
| `tools/check_identifier_retirement.py` | **RC=0** — "GREEN — 47 persisted/wire identifiers match the ledger" |
| `tools/check_identifier_retirement.py --print` | RC=0 — used to prove the `STRATEGY_EMA_CROSS` parse blindness (§ J2-A) |
| `g++ -fsyntax-only` shadow-tree probes | used to prove the public-clone enum shift + initializer overflow (§ J2-A) |
| `tools/calls_graph_diff.sh` | **NOT run** — `tools/lib/sharded_files.txt` has **0** `GUI/` entries, so it is structurally incapable of answering any question in this shard. That fact is itself finding **P-3**. |

**Headline:** the emit/display plane is where complement-blindness has already *landed*, not just where it *could*. Four live divergences (**E-1** trade-log reader dead in production · **E-2** metric registry with zero production consumers and a format-drifted real renderer · **E-3** session-phase "coverage assert" that is vacuous by construction · **E-4** the H21 guard's own SOURCES table missing `FOREACH_HALT_REASON` and silently dropping `STRATEGY_EMA_CROSS`), plus a **new sub-shape worth naming: the CONSUMER-SIDE COMPLEMENT** (§ C).

---

# JOB 1 — the 7 emit/display registries

## 1. `FOREACH_TRADE_LOG_COL` — SSoT for EMIT, **blind on READ** ⚠ **E-1 (HIGH)**

**Definition:** `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/TradeLogColRegistry.hpp:36-55` — 13 rows.
**Kind:** SOURCE-OF-TRUTH in the emit direction. It *generates* both the header (`TradeLog_EmitHeader`, `:71-82`) and the row (`TRADE_LOG_EMIT_ROW_TO_BUFFER`, `:98-128`). Writer: `CoreFrameworks/ShardedTradeLog.hpp:254` (header) + `:488`/`:555` (rows).
**Complement check:** none — and none is possible in the read direction, which is the point.

The registry states its own read-side obligation at `TradeLogColRegistry.hpp:134-136`:
> `ORDER MATTERS — operator parsers (TradeReader / TUI history panel / offline analysis tools) read columns by position.`

It names three consumer classes and **cannot enumerate or verify any of them.** I enumerated them:

| Consumer | Schema it assumes | Verdict |
|---|---|---|
| `CoreFrameworks/ShardedTradeLog.hpp` (writer) | registry, 13 cols + 2 header lines | SSoT ✓ |
| `GUI/TradeHistoryPanel.hpp:129-186` | sharded, by index 0,1,2,3,5,6,7,8,10 | **parse CORRECT, doc WRONG** |
| `GUI/TradeReader.hpp:185-206` | **legacy 19-col** `tick,side,price,…` | **BROKEN — produces nothing** |
| `tools/chart.py:145,150` | **legacy** `side == 'BUY'/'SELL'` | **BROKEN** |
| `DataStream/TradeLog.hpp:152` (legacy writer) | 19-col, literal `BUY`/`SELL` at `:163`/`:176` | single_core-only path |

### E-1: `GUI/TradeReader.hpp` is dead code against the production log

Emitted column order (`TradeLogColRegistry.hpp:37-55`):
`0 timestamp_us · 1 node_id · 2 strategy_id · 3 event_type · 4 price · 5 entry_price · 6 exit_price · 7 pnl · 8 fees · 9 balance_after · 10 trade_size · 11 regime · 12 regime_name`

`GUI/TradeReader.hpp:185-189` documents `// CSV columns (from TradeLog.hpp): 0:tick, 1:side, 2:price, 3:quantity, 4:entry_price, 5:delta_pct, 6:exit_reason, … 14:fee_cost …` and reads accordingly:

```text
csv_field(line, 1, side, sizeof(side));      // actual field 1 = node_id  ("%u")
csv_field(line, 2, price_s, sizeof(price_s));// actual field 2 = strategy_id
csv_field(line, 14, fee_s, sizeof(fee_s));   // OUT OF RANGE (only 0..12 exist)
...
if (strcmp(side, "BUY") == 0) { ... } else if (strcmp(side, "SELL") == 0) { ... }
```
— `GUI/TradeReader.hpp:201-224`

`node_id` renders as `"0".."15"` and **never** equals `"BUY"`/`"SELL"` → both branches are unreachable. Index 14 falls off the end; `csv_field` returns `out[0]='\0'` (`GUI/TradeReader.hpp:150`) → `parse_double_fast("")`.

**Net effect:** `TradeData_Refresh` yields **zero markers and zero equity points, unconditionally**. `GUI_PriceChart(&cs, snap, &trades, …)` (`GUI/GuiThread.hpp:515`) draws no trade markers and `GUI_EquityChart(&trades)` (`GUI/GuiThread.hpp:518`) draws an empty Equity Curve — while the engine trades. That is a **Class-2 display↔execution divergence**.

**The path is confirmed, not inferred.** `CoreFrameworks/ShardedTradeLog.hpp:75` annotates the aggregate file verbatim: `// aggregate: logging/SYMBOL_order_history.csv (GUI/TradeReader reads this)`; built at `:223`; `GUI/GuiThread.hpp:459` opens exactly `"logging/btcusdt_order_history.csv"`. Sharded is production (root `CLAUDE.md` Overview). Scope caveat: under legacy `engine_mode=single_core`, `DataStream/TradeLog.hpp` writes the 19-col schema and TradeReader **works** — so this is "broken in production mode, correct in the deprecated mode."

### E-1b: `TradeHistoryPanel` parses right for the wrong reason (MED — latent)

`GUI/TradeHistoryPanel.hpp:129-140` states `(11 cols)` and `:140` states `No header row in the sharded log — no skip-first`. **Both are false at HEAD:** the registry emits **13** columns (regime + regime_name appended, `TradeLogColRegistry.hpp:48-55`) and `ShardedTradeLog.hpp:252-254` writes **two** header lines (a `#` sentinel then the column header).

It survives only because `:150` skips `'#'` lines and the column-header line's field 3 is `"event_type"` — lowercase `'e'`, which fails both `kind_s[0]=='E'` (`:157`) and `kind_s[0]=='X'` (`:164`). **A column rename to `Event_type`, or an uppercasing header emitter, would make it ingest the header row as a trade.**

### E-1c: `tools/chart.py:145,150` carries the same legacy `BUY`/`SELL` assumption → also broken against the sharded log.

---

## 2. `FOREACH_CALIB_LOG_COL` — the **positive example**, with one side-axis gap

**Definition:** `/home/caramel/code/FoxML_Trader_v2/DataStream/CalibLogColRegistry.hpp:81-131` — 47 rows (9 legacy + 6 singletons + 32 per-arm).
**Kind:** SOURCE-OF-TRUTH for emit; **COVERAGE over the arm domain `[0, BANDIT_MAX_ARMS)`**.
**Complement check: YES, and it is the right shape.**

```cpp
static_assert(BANDIT_MAX_ARMS == 8,
              "FOREACH_CALIB_LOG_COL hand-written for 8 arms; bump arm rows + BANDIT_MAX_ARMS together");
```
— `DataStream/CalibLogColRegistry.hpp:137-138`, tagged `[ASSERT]_[REGISTRY_COVERAGE]` at `:136`

This **pins the domain cardinality at the domain's own definition site**, so growing `BANDIT_MAX_ARMS` is a hard compile failure rather than 4 silently-missing columns. This is the pattern the other emit registries lack — cite it as the canonical fix shape.

### E-5 (MED): the calib log covers **one of two** bandit sides

Every Thompson column reads `ezoo->buy_thompson_bandits[...]` (`CalibLogColRegistry.hpp:101-130`). `exit_thompson_bandits` (`ML_Headers/NodeModelZoo.hpp:1233`) is never emitted. `FOREACH_BANDIT_SIDE` (`ML_Headers/bandit_dispatch_table.hpp:82-84`) declares the domain as `{buy, exit}` and claims at `:97-104`:

> `Adding a future side … = 1 row here → all consumer-site mirrors auto-extend:` *(then enumerates 6 consumer families)*

The calib-log emit is a **7th consumer family, absent from that enumerated list**, and it does not auto-extend. Worse, the same file admits the claim is aspirational at `:157-159`: *"Hand-mirror today; true symmetric rename + macro-name-concat auto-gen tracked at TECH_DEBT-084."* Per SUBAGENT_ARMING § 2.5 the present-tense "auto-extend" wording actively misleads — it reads as a landed guarantee.

---

## 3. `FOREACH_BACKTEST_METRIC` — ⚠ **E-2 (MED/HIGH): a COVERAGE registry with ZERO production consumers, over a domain it covers 8/20**

**Definition:** `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/MetricCompute.hpp:121-129` — 8 rows.
**Kind:** the registry *declares* its authoritative domain at `:160-161`:
> `IDs are append-only — never reorder. The values match the offset of the corresponding field on BacktestStats.`

So the domain is **`BacktestStats`** (`/home/caramel/code/FoxML_Trader_v2/Backtest/BacktestEngine.hpp:275-305`, 20 fields).

**Complement (computed):** 8 covered / **12 uncovered, with no stated exclusion**:
`total_pnl · total_fees · total_trades · wins · losses · avg_win · avg_loss · elapsed_ms · ticks_processed · all_wins_run · nan_labels_total · nan_labels_dropped`

**The `:160-161` claim is also false as written.** `METRIC_RETURN_PCT == 6` but `return_pct` is field index 8 / byte offset 64; `METRIC_AVG_HOLD_TICKS == 7` but `avg_hold_ticks` is field index 14. The identity holds only for the first six rows. A guard author trusting that column doc would mis-partition (same trap class as HAZ-1 in the NodeContext report).

**Existing checks are rows-forward and self-referential:**
```cpp
static_assert(sizeof(BACKTEST_METRIC_NAMES)/sizeof(*BACKTEST_METRIC_NAMES) == NUM_BACKTEST_METRICS, …);
static_assert(sizeof(BACKTEST_METRIC_FORMATS)/sizeof(*BACKTEST_METRIC_FORMATS) == NUM_BACKTEST_METRICS, …);
```
— `CoreFrameworks/MetricCompute.hpp:151-154`. Both compare the registry's own generated arrays to the registry's own generated count.

**Zero production consumers.** Full-tree search including gitignored `tests/`/`tools/`: `NUM_BACKTEST_METRICS` / `BACKTEST_METRIC_NAMES` / `BACKTEST_METRIC_FORMATS` / `METRIC_*` appear **only** in `CoreFrameworks/MetricCompute.hpp:136-154` and `tests/controller_test.cpp:13330-13410`. The test is itself rows-forward (`row_count == NUM_BACKTEST_METRICS`, `NAMES[i]` non-empty). **Nothing in the engine or GUI reads this registry.** → **Class-51 vacuously-green guard** over an orphan artifact.

**And the real display plane has already drifted from it.** `Backtest/BacktestPanels.hpp` hand-writes the labels + formats:

| Metric | Registry format | Actual render | |
|---|---|---|---|
| SHARPE_RATIO | `"%.3f"` (`MetricCompute.hpp:122`) | `"%.2f"` (`BacktestPanels.hpp:799`, again `:2572`) | **DIVERGED** |
| EXPECTANCY | `"$%+.2f"` (`:124`) | `"$%.2f"` (`BacktestPanels.hpp:786`) | **DIVERGED** (loses forced sign) |
| PROFIT_FACTOR | `"%.2f"` (`:123`) | `"%.2f"` (`:785`) | match |
| WIN_RATE | `"%.1f%%"` (`:127`) | `"%.1f%%"` (`:784`) | match |
| MAX_DRAWDOWN(+_PCT) | `"$%.2f"` / `"%.2f%%"` (`:125-126`) | merged `"$%.2f (%.2f%%)"` (`:798`) | 2 rows → 1 render |
| AVG_HOLD_TICKS | `"%.0f"` (`:129`) | `"%.0f"` (`:801`) | match |
| RETURN_PCT | `"%.2f%%"` (`:128`) | `"%.2f%%"` (`:2553`) / `"%+.2f%%"` (`GUI/DashboardPanels.hpp:1036`) | partial |

**And there is a fourth, un-enrolled parallel enumeration of the same domain:**
```cpp
#define OPT_METRIC_SHARPE      0
#define OPT_METRIC_PF          1
#define OPT_METRIC_EXPECTANCY  2
#define OPT_METRIC_RETURN      3
#define OPT_METRIC_PNL         4
```
— `Backtest/BacktestEngine.hpp:2647-2651`, dispatched at `:2655-2659`, defaulted at `BacktestPanels.hpp:2637`.

Not an X-macro, not in `FOREACH_REGISTRY`, not derived from `FOREACH_BACKTEST_METRIC`, and **set-different from it in both directions**: `OPT_METRIC_PNL` (`total_pnl`) has no registry row; `MAX_DRAWDOWN`/`MAX_DRAWDOWN_PCT`/`WIN_RATE`/`AVG_HOLD_TICKS` have no `OPT_METRIC_*`. So one conceptual domain has **four** partial enumerations (`BacktestStats` 20 · registry 8 · `OPT_METRIC_*` 5 · hand-written render rows), and the only guard compares the registry to itself.

---

## 4. `FOREACH_PANEL` — COVERAGE over a **prose-defined** domain; the 16-vs-24 divergence is real but is *not* this registry's

**Definition:** `/home/caramel/code/FoxML_Trader_v2/GUI/GuiThread.hpp:82-86` — **4** rows.
**Kind:** SOURCE-OF-TRUTH for declaration + init of *stateful* panels; it generates `state_type var_id; init_fn(&var_id, init_param);` at `GUI/GuiThread.hpp:466-470` and the `PANEL_*` enum at `:89-94`.

**Domain is prose, not mechanical** — `:65-69` states: *"Stateless panels (Header, Market, BuyGate, Account, Positions, Stats, Latency, ML Intelligence, … the ~11 dashboard panels that take only `snap`…) keep their direct `GUI_Panel_X(snap)` calls."* Because the domain boundary ("has per-frame state") is a judgment, **no complement is computable.** That is the structural verdict on this registry.

**Direct answer to the orchestrator's lead: `FOREACH_PANEL` is NOT the registry the 16-vs-23 divergence belongs to.** The docking list is a separate hand-written enumeration.

### P-1 (MED) — the window-set complement

`Gui_SetupDefaultLayout` (`GUI/GuiThread.hpp:355-400`) docks **16** windows: `Price Chart · Volume · Live P&L · Equity Curve` (`:370-373`) + `Header · Top Bar · Market · Buy Gate · Account · Positions` (`:381-386`) + `Stats · ML Intelligence · Latency · Settings · Trade History · Engine Log` (`:389-394`).

There are **24** `ImGui::Begin(` sites in `GUI/`, i.e. 24 declared windows; **23 are reachable** (one is orphaned, § P-2). The 8 that exist but are **never docked in the default layout**:

| Window | Site |
|---|---|
| `ML Status` | `GUI/MLStatusPanel.hpp:39` |
| `Engine` | `GUI/EngineHeaderPanel.hpp:37` |
| `Per-Node P&L` | `GUI/DashboardPanels.hpp:1660` |
| `Risk` | `GUI/DashboardPanels.hpp:2123` |
| `Per-Node Latency` | `GUI/DashboardPanels.hpp:2248` |
| `Engine Topology` | `GUI/DashboardPanels.hpp:2417` |
| `Strategy Quality` | `GUI/StrategyQualityPanel.hpp:345` |
| `Config` | `GUI/DashboardPanels.hpp:1266` — **and never rendered at all** (§ P-2) |

Consequence: on a fresh install (no `foxml_gui.ini`) seven live panels — including **`Risk`, the per-node kill-switch dashboard with the reset controls** (`DashboardPanels.hpp:2118-2121` calls it *"for taking action when a core gets in trouble"*) — float undocked rather than appearing in the layout. That is a capital-control surface with degraded default discoverability.

Also note: `"Latency"` **is** docked (`:391`) but `GUI_Panel_Latency` is `#ifdef LATENCY_PROFILING`-only (`DashboardPanels.hpp:2110-2112`), so in a default build the layout docks a window that does not exist (harmless no-op, but it is domain drift in the same table).

### P-2 (MED) — `GUI_Panel_Config` is a fully-formed orphan

`GUI/DashboardPanels.hpp:1265-1312` defines a complete `ImGui::Begin("Config")` panel. Full-tree search including `tests/`: the only other occurrence is `DOCS/CODE_MAP.md:997`. **Zero callers** — absent from `GUI_RenderDashboard` (`DashboardPanels.hpp:2099-2112`), absent from `FOREACH_PANEL`, absent from the dock list. H21's "remove dead code, don't leave it compiled-in" applies.

### P-3 (MED, structural) — why no tool caught P-2

`tools/lib/sharded_files.txt` contains **zero** `GUI/` paths (verified: `grep -c "GUI/"` → 0). Its own header declares it the SSoT for `calls_graph_diff.sh`. So the orphan detector is **structurally incapable** of seeing GUI dead code. This is a *scope* complement: the tool proves the files it has are clean and cannot prove those are all the files.

### P-4 (LOW) — an unenrolled row-shaped sibling + a duplicated path literal

Immediately above the registry walk:
```cpp
TradeData trades;
TradeData_Init(&trades, "logging/btcusdt_order_history.csv");
```
— `GUI/GuiThread.hpp:458-459`

`TradeData_Init(TradeData*, const char* csv_path)` (`GUI/TradeReader.hpp:102`) matches the registry's row contract **exactly** (`state_type var_id; init_fn(&var_id, init_param);`) and would be a legal row: `X(trades, TradeData, TradeData_Init, "logging/btcusdt_order_history.csv")`. It is excluded because it is a *feed*, not a *panel* — defensible under the prose domain, but the same path literal now appears twice (`:83` and `:459`) with no SSoT. Note this is the same file § E-1 shows is broken; enrolling it would at least have surfaced it in the registry's blast radius.

### P-5 (LOW) — `NUM_STATEFUL_PANELS` (`GUI/GuiThread.hpp:93`) is commented *"Panel ID enum — for tests"* and has **zero references anywhere**, tests included.

---

## 5. `FOREACH_LIVE_READINESS_CHECK` — COVERAGE-CLEAN; a cheap complement exists and is unlanded

**Definition:** `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/LiveReadiness.hpp:239-259` — **10** rows. Walked at `:318-324`.
**Kind:** SOURCE-OF-TRUTH over a judgment domain ("what must hold before live"). Row→fn is compile-enforced (a row naming a missing fn fails to build).
**Complement:** the reverse direction *is* mechanically computable — **a `check_*` fn defined in this file with no row is a silently-dead gate.** I computed it: `rg "^inline bool check_"` returns **10** fns (`:87, :93, :103, :113, :125, :140, :152, :164, :176, :201`) against 10 rows → **complement is empty at HEAD. CLEAN.** But nothing enforces it; a 3-line CI grep would.

**LR-1 (LOW, stale comment):** `:271` says *"~10us total for **9** checks"* — there are 10 rows since `live_capital_gated_until_e` landed. Code is truth (§ 2.5).
**LR-2 (informational, already homed):** `:216-218` carries an explicit H21 tombstone directive to remove `check_live_capital_gated_until_e` + its row at `.E`/v5.16, tracked at TECH_DEBT-203. This is the *good* pattern — a stated, homed exclusion with a removal trigger.

---

## 6. `FOREACH_ROLLING_WINDOW` — SOURCE-OF-TRUTH; **3 unenrolled hand-written mirrors** (LOW/MED)

**Definition:** `/home/caramel/code/FoxML_Trader_v2/ML_Headers/RollingWindowRegistry.hpp:59-63` — 4 rows (`short 128 · long 512 · medium 256 · baseline 1024`).
**Kind:** SOURCE-OF-TRUTH — generates the `NodeSlowState` field declarations (`CoreFrameworks/ControllerEventLoop.hpp:159-160`) and the init calls (`:185-187`). On that surface the complement is closed *by construction*: no hand-written `rolling_*` member can exist on `NodeSlowState`.

**RW-1 (LOW/MED):** the registry's own scoping note (`RollingWindowRegistry.hpp:20-29`) says consumer sites "stay manual". Three sibling structures hand-declare the same 4-window cohort with **no registry linkage**:
- `CoreFrameworks/PortfolioController.hpp:312,315,316` — `rolling_long` / `rolling_medium` / `rolling_baseline` (legacy centralized path)
- `CoreFrameworks/ShardedBacktestDriver.hpp:87,99,100` — same three as pointers
- `Strategies/StrategyParameters.hpp:155,156` — `void* rolling_medium` / `rolling_baseline` (type-erased, so not even type-checked)

Adding a 5th window auto-flows the per-node declaration/init but **silently leaves all three mirrors at 4**, and the `void*` pair at `StrategyParameters.hpp:155-156` will not even produce a compile diagnostic. Bounded and non-capital, but it is the same shape.

---

## 7. `FOREACH_LIVES_IN_STRUCT` — a **true COVERAGE registry over an enum**, clean today, unguarded

**Definition:** `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/CfgFieldRegistry.hpp:1679-1684` — 5 rows.
**Authoritative domain:** the `CfgFieldDescriptor::LivesInStruct` enum, `CfgFieldRegistry.hpp:200-206` — 5 values (`STRUCT_CFG=0 … STRUCT_TRAINING_CFG=4`).
**Kind:** **COVERAGE.** The registry's own comment at `:1689` says so: *"Mirrors the LivesInStruct enum."*
**Complement computed:** `enum − rows = ∅`. **COVERAGE-CLEAN.**
**Complement check exists?** **No.** Nothing ties the two. Each row generates two mask arrays (`CfgFieldRegistry.hpp:1712-1723`); a 6th enum value would produce **no mask**, and every consumer of `g_global_cfg_struct_*_mask` / `g_per_node_cfg_struct_*_mask` would silently omit that cohort's fields. The enum is explicitly forward-looking (`:199` — *".F.4b only populates STRUCT_CFG; full enum declared for v5.15.6 forward-compat"*), so the 6th value is a **planned** event, not hypothetical.

**Fix is one line, using the pattern the calib log already proves:** `static_assert(FOREACH_LIVES_IN_STRUCT_COUNT == STRUCT_TRAINING_CFG + 1, …)` — or better, a `LIVES_IN_STRUCT_COUNT` sentinel in the enum pinned against the row count.

---

# C. The NEW SUB-SHAPE — **CONSUMER-SIDE COMPLEMENT** (recommend codifying)

The four shards so far have swept *producer-side* complements: `domain_source − registry_rows` (fields, bits, enum values). `FOREACH_TRADE_LOG_COL` exposes a structurally different one:

> **A registry that is SSoT for an EMITTED FORMAT is authoritative in one direction only. Its READ direction has N independent hand-written parsers that the registry cannot enumerate. The complement is `{parsers of this format} − {parsers verified against the registry}` — and it is normally 100%.**

Why it is distinct from the producer-side shape:
1. **The domain lives outside the compiler.** A missing struct field is at least *in the same TU*; a stale CSV parser is in a different binary (`tools/chart.py`) or a different subsystem (`GUI/`), and no build ever links them.
2. **It fails silently and asymmetrically.** The writer stays green forever. The reader degrades to empty output (§ E-1), which reads to an operator as "no trades yet" — indistinguishable from correct behavior.
3. **The registry's own doc names the consumers it cannot check** (`TradeLogColRegistry.hpp:134-136` names three) — the gap is *acknowledged in prose and unenforced in code*, exactly the `drift_history` correlation.
4. **It has already fired at three of four consumers here** (TradeReader broken, chart.py broken, TradeHistoryPanel doc-stale), so it is an observed class, not a hypothetical.

**Mechanizable check** (cheap, high leverage): emit the registry's column names into a generated golden (`tools/goldens/trade_log_columns.txt`) at the emit site, and have a CI tool assert that every file that opens `*_order_history.csv` carries a `[SCHEMA]_[trade_log_v<N>]` tag matching the current golden. Any consumer that does not declare its schema version is the complement.

---

# JOB 2 — CLOSING THE SET: the complete 68-row accounting

`CoreFrameworks/MetaRegistry.hpp` rows `:36`–`:115`, verified by `tools/check_meta_registry.py` (68 macros / 68 rows, RC=0).

**Attribution arithmetic closes exactly: 47 (shards 1-4) + 7 (my JOB 1) + 14 (my JOB 2) = 68.** Shard attribution below is inferred *by surface* (the orchestrator holds the authoritative shard→registry map); my JOB-1 and JOB-2 columns are independently derived and are the ones I own.

| # | Line | Registry | Disposition | Kind + one-line justification |
|---|---|---|---|---|
| 1 | :36 | `FOREACH_REGISTRY` | **JOB-2 · COVERAGE-CLEAN** | The ROOT. Domain = every `FOREACH_<X>` in the codebase — an *external, mechanically enumerable* domain, and `check_meta_registry.py` Check 1 **is** the domain-complement (scans the codebase, not the rows). **This is the one registry in the codebase that already does exactly what this sweep is asking for.** RC=0 at HEAD. |
| 2 | :38 | `FOREACH_GLOBAL_CFG_FIELD` | covered-by-shard (cfg) | — |
| 3 | :39 | `FOREACH_PER_NODE_CFG_FIELD` | covered-by-shard (cfg) | — |
| 4 | :40 | `FOREACH_MANUAL_PER_NODE_FIELD` | covered-by-shard (cfg) | — |
| 5 | :41 | `FOREACH_PER_NODE_DOMAIN_BITMAP` | **JOB-2 · SOURCE-OF-TRUTH-N/A** | Level-1 meta over 5 children; **generates** the bitmap storage fields on `PerNodeCfg<F>` via `EMIT_DOMAIN_BITMAP_FIELD` (`CfgFieldRegistry.hpp:986-987`), so no hand-written sibling can exist. H19 topology CI-enforced (Check 3 PASS); H17 forbids manual `PerCoreCfg` fields. Complement closed by construction. |
| 6 | :42 | `FOREACH_PER_NODE_NO_FLAT_FIELD_SYNC` | covered-by-shard (cfg) | — |
| 7 | :43 | `FOREACH_PER_NODE_ARRAY_OVERRIDE` | covered-by-shard (cfg) | — |
| 8 | :44 | `FOREACH_METADATA_BIT` | covered-by-shard (cfg) | — (H16 pairs it to `FOREACH_DERIVED_FILTER`) |
| 9-13 | :46-:50 | `FOREACH_{LIFECYCLE,GATE,ML,RISK,OPS}_CFG_FLAG` | covered-by-shard (cfg, L2) | — |
| 14 | :53 | `FOREACH_STAMP_BOUND_MODEL_CONST_PRE_CFG` | covered-by-shard (stamp) | — |
| 15 | :54 | `FOREACH_STAMP_BOUND_MODEL_CONST_POST_CFG` | covered-by-shard (stamp) | — |
| 16 | :56 | `FOREACH_STRATEGY` | **JOB-2 · ⚠ COVERAGE-WITH-GAP** | **§ J2-A — the shard's biggest JOB-2 finding.** Four hidden couplings: a hardcoded cfg parser, two GUI tables, and an H21-guard parse blindspot. |
| 17 | :57 | `FOREACH_BANDIT_ALGORITHM` | **JOB-2 · COVERAGE-CLEAN** | Explicit values 0-4 (`BanditAlgorithmRegistry.hpp:89-95`) + per-value density `static_assert`s (`:114-118`) + 3-bit wire-slot cap `static_assert` (`bandit_dispatch_table.hpp:132-135`) + **enrolled in the H21 ledger** (`check_identifier_retirement.py:99`). Best-guarded enum in the codebase. |
| 18 | :58 | `FOREACH_BANDIT_SIDE` | **JOB-2 · ⚠ COVERAGE-WITH-GAP** | 2 rows (`bandit_dispatch_table.hpp:82-84`). Claims 6 consumer families "auto-extend" (`:97-104`) but admits hand-mirroring at `:157-159`. The calib-log emit is a 7th, buy-only (§ E-5). |
| 19 | :59 | `FOREACH_FAILURE_MODE` | covered-by-shard (state-flags) | — (explicitly + **homed** exempt from H21 SOURCES at `check_identifier_retirement.py:110-114` → TECH_DEBT-152 — the model exclusion) |
| 20 | :61 | `FOREACH_OMS_FIELD` | covered-by-shard (OMS) | — |
| 21-23 | :63-:65 | `FOREACH_STAMP_BOUND_MODEL_CONST{,_GROUPS,_STANDALONE}` | covered-by-shard (stamp) | — |
| 24 | :70 | `FOREACH_STAMP_RESULT_FIELD_EXCLUSION` | covered-by-shard (stamp) | — |
| 25 | :71 | `FOREACH_BARRIER_BLEND_MODE` | **JOB-2 · ⚠ COVERAGE-WITH-GAP (partially homed)** | 5 rows, positional; generates enum + `MODE_FLAGS[]` (`BarrierBlendModeRegistry.hpp:109-125`). **Self-documents stamp-visibility**: `:94-96` — *"Reordering or removing a row shifts enum values, which would invalidate any stamp body that recorded the prior enum value (TECH_DEBT-024)."* **Not in H21 SOURCES.** Homed to TECH_DEBT-024 but not to the mechanized guard. |
| 26 | :72 | `FOREACH_IC_VARIANT` | **JOB-2 · coupling-noted, currently 1 row** | `[COLUMN]_[variant_id]_[cfg.confidence_ic_variant value — STABLE, append-only]` (`ICVariantRegistry.hpp:50`) — a cfg-visible append-only code, **not in H21 SOURCES**. 1 live row (`:57`) + 2 commented-out future rows; exposure is nil today, real on the 2nd row. |
| 27 | :73 | `FOREACH_DEGRADATION_CURVE` | **JOB-2 · SOURCE-OF-TRUTH-N/A** | 4 rows with **explicit** values 0-3 (`ConfidenceScore.hpp:1071-1076`); generates the enum + fn-ptr table (`:1084-1099`). Explicit-in-registry values make a renumber diff-visible. Cfg-selected; not in H21 SOURCES (low exposure — no persisted history depends on it). |
| 28 | :74 | `FOREACH_RECONCILE_MODE` | **JOB-2 · SOURCE-OF-TRUTH-N/A — the positive pattern** | 3 rows with explicit values **and a `cfg_string` column** (`Reconcile.hpp:141-147`); the registry **generates both** `ReconcileMode_ToString` (`:166-175`) **and the cfg parser's accepted-string table** (`:177+`). This is precisely what `FOREACH_STRATEGY` fails to do — **cite it as the fix template for § J2-A.** |
| 29 | :75 | `FOREACH_REGIME` | **JOB-2 · COVERAGE-CLEAN + doc-drift** | 5 rows (`StrategyInterface.hpp:240-245`); generates `REGIME_INFO[]` + `REGIME_STRATEGY_TABLE[]` with count `static_assert`s (`:272-275`); sizes 6 arrays on `EnsembleModelZoo` (`NodeModelZoo.hpp:1215-1284`); 3-bit wire cap asserted (`bandit_dispatch_table.hpp:138-140`); **enrolled in H21** (`check_identifier_retirement.py:103`; ledger rows 0-4). Clean. **Doc drift:** `MetaRegistry.hpp:75` and root `CLAUDE.md` both name only 4 regimes — `TRENDING_DOWN` (`:244`) is missing from both. |
| 30 | :76 | `FOREACH_TARGET` | covered-by-shard (ML) | — |
| 31 | :77 | `FOREACH_FEATURE` | covered-by-shard (ML) | — |
| 32 | :78 | `FOREACH_SHALT` | **JOB-2 · COVERAGE-CLEAN** | 20 rows (`StrategyInterface.hpp:295-316`); `SHALT_SHORT_NAMES` generated + count-asserted (`:332-339`); GUI reads the generated table directly, **no mirror** (`GUI/DashboardPanels.hpp:684,699,774,784`); **enrolled in H21** (`check_identifier_retirement.py:107`, ledger 0-19). The reference-quality persisted enum. |
| 33 | :79 | `FOREACH_HALT_REASON` | **JOB-2 · ⚠ COVERAGE-WITH-GAP — the `drift_history` shape** | § J2-B. |
| 34 | :80 | `FOREACH_LIVE_READINESS_CHECK` | **JOB-1 · COVERAGE-CLEAN** | § 5. 10 rows / 10 fns; reverse complement empty but unenforced. |
| 35 | :81 | `FOREACH_LIVES_IN_STRUCT` | **JOB-1 · COVERAGE-CLEAN, unguarded** | § 7. Mirrors a 5-value enum with nothing tying them. |
| 36 | :82 | `FOREACH_NODE_STATE_FLAG` | covered-by-shard (state-flags) | — (enrolled in H21, `check_identifier_retirement.py:115`) |
| 37 | :83 | `FOREACH_PER_NODE_STATE_FLAG` | covered-by-shard (state-flags) | — |
| 38 | :84 | `FOREACH_PER_ARM_FLAG` | covered-by-shard (state-flags) | — |
| 39 | :85 | `FOREACH_EZOO_INIT_FLAG` | covered-by-shard (state-flags) | — |
| 40 | :86 | `FOREACH_SESSION_PHASE` | **JOB-2 · ⚠ COVERAGE-WITH-GAP** | § J2-C — a "coverage assert" that is **vacuous by construction**. |
| 41 | :87 | `FOREACH_NODE_CTX_FIELD` | covered-by-shard (NodeCtx) | — |
| 42 | :88 | `FOREACH_NODE_CTX_SUMMARY_FIELD` | covered-by-shard (NodeCtx) | — |
| 43 | :89 | `FOREACH_DISPLAY_META_FIELD` | covered-by-shard (display) | — |
| 44 | :90 | `FOREACH_GATE_DIAG_PAIR` | covered-by-shard (display) | — |
| 45 | :91 | `FOREACH_SINGLE_ZOO_POST_LOAD` | covered-by-shard (ML) | — |
| 46 | :92 | `FOREACH_ENSEMBLE_POST_LOAD` | covered-by-shard (ML) | — |
| 47 | :93 | `FOREACH_OMS_PER_SLOT_FIELD` | covered-by-shard (OMS) | — |
| 48 | :94 | `FOREACH_OMS_META_SLOT` | covered-by-shard (OMS) | — |
| 49 | :95 | `FOREACH_OMS_STATE_FLAG` | covered-by-shard (OMS) | — |
| 50 | :96 | `FOREACH_OMS_STATE_MULTI_BIT` | covered-by-shard (OMS) | — |
| 51 | :97 | `FOREACH_POSITION_FIELD` | covered-by-shard (persist) | — |
| 52 | :98 | `FOREACH_POSITION_FIELD_SKIP_PERSIST` | covered-by-shard (persist) | — |
| 53 | :99 | `FOREACH_BACKTEST_METRIC` | **JOB-1 · ⚠ COVERAGE-WITH-GAP** | § 3. 8/20 of `BacktestStats`; zero production consumers; renderer already drifted; 4th parallel enumeration at `OPT_METRIC_*`. |
| 54 | :100 | `FOREACH_CALIB_LOG_COL` | **JOB-1 · COVERAGE-CLEAN (arm axis) + gap (side axis)** | § 2. `BANDIT_MAX_ARMS==8` is the model complement check; buy-only vs `FOREACH_BANDIT_SIDE` is the gap. |
| 55 | :101 | `FOREACH_TRADE_LOG_COL` | **JOB-1 · ⚠ CONSUMER-SIDE GAP (HIGH)** | § 1 / § C. 3 of 4 consumers stale; 2 fully broken. |
| 56 | :102 | `FOREACH_CONFIDENCE_PERSIST_FIELD` | covered-by-shard (persist) | — |
| 57 | :103 | `FOREACH_REGIME_PERSIST_FIELD` | covered-by-shard (persist) | — |
| 58 | :104 | `FOREACH_FEEDER_PERSIST_FIELD` | covered-by-shard (persist) | — |
| 59 | :105 | `FOREACH_NODE_PERSIST_FIELD` | covered-by-shard (persist) | — (the `drift_history` founding instance) |
| 60 | :107 | `FOREACH_CFG_DRIFT_CHECK` | covered-by-shard (cfg-derived) | — |
| 61 | :108 | `FOREACH_CFG_GATE_PER_NODE` | covered-by-shard (cfg-derived) | — |
| 62 | :109 | `FOREACH_CFG_GATE_GLOBAL` | covered-by-shard (cfg-derived) | — |
| 63 | :110 | `FOREACH_STAMP_BOUND_DERIVED_COHORT` | covered-by-shard (cfg-derived) | — |
| 64 | :111 | `FOREACH_ARCH_FIELD_DRIFT` | covered-by-shard (drift) | — |
| 65 | :112 | `FOREACH_SLOW_PATH_GATE` | covered-by-shard (slow-path) | — |
| 66 | :113 | `FOREACH_SP_SECTION` | **JOB-2 · SOURCE-OF-TRUTH-N/A (soft domain, computable residual)** | 5 rows (`SpSectionRegistry.hpp:32-36`); sizes `slow_path_breakdown[SP_SECTION_COUNT]` (`ControllerEventLoop.hpp:793`); 5 instrumentation sites, one per row (`EngineCommon.hpp:611,636,657,763,797`). Domain = "the timed slow-path phases" — no authoritative external list, so not mechanically closable. **But a residual complement IS computable at runtime**: `slow_path_latency − Σ slow_path_breakdown[s] > 0` ⇒ unattributed time ⇒ a phase with no row. Not landed; see § NOVEL. |
| 67 | :114 | `FOREACH_PANEL` | **JOB-1 · COVERAGE, prose-domain (not computable)** | § 4 + P-1..P-5. |
| 68 | :115 | `FOREACH_ROLLING_WINDOW` | **JOB-1 · SOURCE-OF-TRUTH, 3 unenrolled mirrors** | § 6. |

**No row unaccounted.**

---

## § J2-A — `FOREACH_STRATEGY`: four hidden couplings, one of them Knight-shaped ⚠ **E-4a (HIGH)**

`FOREACH_STRATEGY` (`Strategies/StrategyInterface.hpp:130-143`) documents itself as *"add a strategy = 1 row"* (`:121`) and *"IDs … are append-only so cfg files / stamps survive (H21)"* (`:154-155`). **Four consumers of that ID domain are hand-written and hardcode the integers as literals.**

**(a) The engine cfg parser** — `CoreFrameworks/ControllerConfig.hpp:3270-3283`:
```cpp
if (strcmp(val, "mr") == 0 || strcmp(val, "mean_reversion") == 0) sid = 0;
else if (strcmp(val, "momentum") == 0 || strcmp(val, "mom") == 0) sid = 1;
else if (strcmp(val, "simple_dip") == 0 || strcmp(val, "dip") == 0) sid = 2;
else if (strcmp(val, "ml") == 0) sid = 3;
else if (strcmp(val, "ema_cross") == 0 || strcmp(val, "ema") == 0) sid = 4;
else if (strcmp(val, "auto") == 0 || strcmp(val, "regime") == 0) sid = 5;  // v4.0.3 STRATEGY_AUTO
```
Numeric literals, not `STRATEGY_*` symbols. `sid` is stored to `cfg.node_strategies[node_idx]` (`:3280`) and thence persisted as `strategy_id` / `resolved_strategy_id` (`MemHeaders/NodeCtxPersistRegistry.hpp:69-70`).

**(b) The GUI name→id mapper** — `GUI/SettingsPanel.hpp:1030-1039`: the same six mappings, again as literals `return 0..5`.
**Divergence between (a) and (b), live at HEAD:** (a) accepts `"regime"` as an alias for auto (`:3277`); (b) does not (`:1036` accepts only `"auto"`). A cfg containing `node_0_strategy=regime` parses correctly in the engine and shows as *unmapped* (`-1`) in the Settings panel.

**(c) The GUI cfg writer table** — `GUI/SettingsPanel.hpp:1603-1605`:
```cpp
static const char* strat_cfg_names[NUM_STRATEGIES] = { "mr","momentum","simple_dip","ml","ema_cross","auto" };
```
Sized by the domain, positionally filled by hand, consumed at `:1609` as `cfg_write_field(s->cfg_path, key, strat_cfg_names[*chosen])`. **Add a strategy row and this array silently zero-fills → `cfg_write_field(..., nullptr)`.**

**(d) The H21 Knight-Capital guard cannot see half the domain — proven mechanically.**

`check_identifier_retirement.py --print` at HEAD returns:
```text
enum:StrategyId|STRATEGY_MEAN_REVERSION|0
enum:StrategyId|STRATEGY_MOMENTUM|1
enum:StrategyId|STRATEGY_SIMPLE_DIP|2
enum:StrategyId|STRATEGY_ML|3
```
`STRATEGY_EMA_CROSS` (=4 in this tree, which **does** have `Strategies/private/EmaCross.hpp`) and `STRATEGY_AUTO` are absent. Mechanism: `_rows()` (`tools/node_persist_layout.py:102-121`) extracts only literal `X(` invocations, and the 5th strategy arrives through the nested `FOREACH_STRATEGY_EMACROSS(X)` (`StrategyInterface.hpp:113,143`), which is never yielded — **no warning, no count check.** `STRATEGY_AUTO` is declared outside the X-macro entirely (`:178`).

This is a **new sub-shape: partial coverage *inside* an enrolled row.** It is worse than an un-enrolled registry, because the ledger category exists and reads as covered.

**(e) The presence-dispatch shifts persisted IDs. Proven by shadow-tree compile.**

I built a public-clone include tree (all repo dirs symlinked, `Strategies/private/` omitted) and compiled the same probe against both:

| Symbol | public tree (no `private/`) | full tree |
|---|---|---|
| `NUM_STRATEGIES_REAL` | 4 | 5 |
| `NUM_STRATEGIES` | **5** | **6** |
| `STRATEGY_AUTO` | **4** | **5** |
| `NUM_REGIMES` | 5 | 5 |

`Strategies/private/` is untracked and gitignored (`git check-ignore -v` → `.gitignore:168`), so a public clone is the left column. Consequences:

1. **The hardcoded parser meanings invert.** In a public build `node_0_strategy=ema_cross` → `sid=4`, but `4` **is** `STRATEGY_AUTO` there; `node_0_strategy=auto` → `sid=5`, which is **out of range** (valid 0..4). *The same `engine.cfg` and the same persisted snapshot decode to different strategies depending on a build-time `__has_include`* — the exact Knight-Capital shape H21 exists to prevent, on an externally-visible identifier, invisible to the guard that mechanizes H21.

2. **Six `[NUM_STRATEGIES]` initializer sites become hard compile errors in a public clone.** Reproduced with the exact declaration shape against both trees:
   - public tree → `error: too many initializers for 'const V4 [5]'` and `for 'const char* [5]'`
   - full tree → RC=0
   
   Affected: `GUI/DashboardPanels.hpp:375, 560, 1108, 2143` · `GUI/ChartPanel.hpp:1194` · `GUI/SettingsPanel.hpp:1603` — all six carry 6 initializers. Scope: `main.cpp:30-32` gates `GUI/GuiThread.hpp` behind `#ifdef USE_IMGUI_GUI`, so `./build.sh test` (build/, zero-dep) is unaffected; **`./build.sh gui` and `suite` are not** (`CMakeLists.txt:97` defaults `USE_IMGUI_GUI` **ON**).

**(f) The class has already fired twice, and both fixes were per-instance.** The codebase records the zero-fill failure in its own comments:
```text
{0.90f, 0.80f, 0.50f, 0.9f},  // 5 AUTO — gold (was missing — array
                               //   defaulted strat_colors[5] to zero
                               //   = transparent black, making any
                               //   AUTO core's row invisible)
```
— `GUI/DashboardPanels.hpp:565-568`; the identical story at `GUI/ChartPanel.hpp:1200-1203` (*"gate lines for AUTO cores rendered as transparent black, invisible on chart"*). **Two independent instances, two point fixes, no structural guard.** Per M7 (`feedback_structural_enforcement_when_memory_insufficient`), a class that recurs at the same surface despite a fix earns compile-time enforcement.

---

## § J2-B — `FOREACH_HALT_REASON`: the `drift_history` shape at the H21 surface ⚠ **E-4b (MED/HIGH)**

`tools/check_identifier_retirement.py`'s `SOURCES` list (`:90-125`) is itself a **COVERAGE registry** over "persisted / wire-visible identifier sources." It enrolls 5 enum registries: `FOREACH_BANDIT_ALGORITHM` (`:99`), `FOREACH_STRATEGY` (`:101`), `FOREACH_REGIME` (`:103`), `FOREACH_SHALT` (`:107`), `FOREACH_NODE_STATE_FLAG` (`:115`).

**`FOREACH_HALT_REASON` is not among them** — despite `Strategies/StrategyInterface.hpp:428-431` stating verbatim:

> `IDs are append-only — never reorder or remove. Trade logs and per-core snapshots persist this value as a raw integer; reordering breaks historical decode.`

That is *the same sentence* `FOREACH_SHALT` uses (`:369-371`) to justify its enrollment — the enrollment comment at `check_identifier_retirement.py:105-106` cites it explicitly. The two registries sit **60 lines apart in the same file**, are the paired controller-level / strategy-level halt vocabularies, and one is guarded while the other is not.

**Why this is the `drift_history` shape exactly:** the tool *does* practice stated exclusion elsewhere — its docstring (`:31-35`) names the queued cohort ("Bitmap bit-assignments + cfg-field name keys enroll next … paced enrollment"), and `FOREACH_FAILURE_MODE`'s exemption is stated **and homed** at TECH_DEBT-152 with a code-side pointer (`:110-114`). `FOREACH_HALT_REASON` fits **neither** the stated queue (it is not a bitmap or a cfg key — it is a persisted enum, the category already fully enrolled) **nor** an exemption. It is the one domain member of an enrolled category with **no row and no stated reason**.

Corroborating: `HALT_WARMUP (=7)` is already a **live tombstone** (`:435-439`: *"reserved-but-unused … Kept in the registry for back-compat with older trade logs"*) — i.e. this registry has already exercised H21's tombstone mechanism, unguarded.

**Also un-enrolled with self-documented persistence claims** (lesser exposure, listed for completeness per M9): `FOREACH_BARRIER_BLEND_MODE` (stamp-body-visible, `BarrierBlendModeRegistry.hpp:94-96`; homed to TECH_DEBT-024) · `FOREACH_IC_VARIANT` (cfg-visible append-only, `ICVariantRegistry.hpp:50`) · `FOREACH_DEGRADATION_CURVE` + `FOREACH_RECONCILE_MODE` (explicit in-registry values → renumber is diff-visible).

---

## § J2-C — `FOREACH_SESSION_PHASE`: a coverage assert that is vacuous by construction ⚠ **E-3 (MED)**

`CoreFrameworks/SessionPhaseRegistry.hpp:40-44` — 4 rows carrying `[START, END)` hour ranges **and a gate multiplier**:
```text
X(ASIAN, asian, 0, 7, 1.5, …)  X(EUROPEAN, european, 7, 13, 1.0, …)
X(US, us, 13, 20, 0.8, …)      X(OVERNIGHT, overnight, 20, 24, 1.3, …)
```

The registry's authoritative domain is the hour set `[0,24)`, and the file **claims** to check it (`:71-72`: *"Coverage asserts (no gaps, no overlaps) follow via the SESSION_BY_HOUR table"*). It does not:

```cpp
constexpr uint8_t session_phase_for_hour(int h) {
#define X(...) if (h >= (START) && h < (END)) return (uint8_t)SESSION_PHASE_##NAME_U;
    FOREACH_SESSION_PHASE(X)
#undef X
    return (uint8_t)SESSION_PHASE_ASIAN;  // fallback for malformed input (shouldn't happen given coverage asserts below)
}
```
— `SessionPhaseRegistry.hpp:61-67`

and the "coverage asserts" are `static_assert(SESSION_BY_HOUR[h] < SESSION_PHASE_COUNT, …)` for h=0..23 (`:104+`).

**The fallback defeats the assert.** An uncovered hour returns `SESSION_PHASE_ASIAN` (0), which is always `< SESSION_PHASE_COUNT` — so **every assert stays green for every possible gap**. Change `EUROPEAN`'s start from 7 to 8 and hour 7 silently becomes ASIAN with a **1.5× gate multiplier instead of 1.0×**, with 24 green static_asserts and no diagnostic. Overlaps are equally undetected (first-match-wins).

This is **Class-51 (vacuously-green guard)** in its purest form: a check named "coverage assert" that structurally cannot fail. The comment at `:66` (*"shouldn't happen given coverage asserts below"*) is the self-reinforcing part — it tells the next reader the domain is closed.

**Fix is 4 lines:** return a `0xFF` sentinel instead of `SESSION_PHASE_ASIAN`, then `static_assert(SESSION_BY_HOUR[h] != 0xFF)`. That converts a rows-forward assert into a genuine domain-complement check, and non-overlap follows from a second constexpr counting matches per hour.

---

# HAZARDS

- **HAZ-1 (blocks any tool that extends `SOURCES`):** `_parse_foreach` (`tools/check_identifier_retirement.py:153-173`) calls `_rows(body)` **without** `_strip_comments`, while its sibling consumer of the same shared library does strip (`node_persist_layout.py:139-153`). Additionally `_rows` locates rows by naive `body.find("X(")` (`node_persist_layout.py:104`), so **any token ending in `X` immediately followed by `(`** — `MAX(`, `IDX(`, `FPN_MAX(` — inside a registry body or its comments would be parsed as a row. No current registry trips it; enrolling one that does would corrupt the ledger silently.
- **HAZ-2 (public-repo build break):** § J2-A(e). Six `[NUM_STRATEGIES]` sites are hard compile errors in a public clone's GUI build. `CMakeLists.txt:97` defaults `USE_IMGUI_GUI` ON. Per `project_public_repo_is_code_only`, the public snapshot is career-load-bearing.
- **HAZ-3 (silent capital-path ID reassignment):** § J2-A(e)(1). `STRATEGY_AUTO`/`STRATEGY_EMA_CROSS` numeric meanings depend on `__has_include`, and both are outside the H21 guard's view. This is a persisted-identifier hazard on the strategy-selection path.
- **HAZ-4 (operator sees "no trades"):** § E-1. The Price Chart's markers and the whole Equity Curve are unconditionally empty in sharded mode. The failure mode is *indistinguishable from an idle engine*, which is the worst possible signature for a monitoring surface.
- **HAZ-5 (fixing E-1 could break E-1b):** `TradeHistoryPanel` and `TradeReader` share `csv_field` and read the same file with **opposite** schema assumptions. A "fix TradeReader by pointing it at the sharded columns" patch must not disturb `TradeHistoryPanel`'s accidental header-skip (§ E-1b), which depends on the header token `"event_type"` staying lowercase.
- **HAZ-6 (guard-authoring trap, same class as the report's HAZ-1):** `MetricCompute.hpp:160-161` asserts a metric-ID↔`BacktestStats`-offset correspondence that holds for 6 of 8 rows. Any partition tool written to that doc will mis-bucket.
- **HAZ-7 (default-layout regression risk):** the 8 undocked windows (§ P-1) include `Risk`, a kill-switch **action** panel. Any dock-list edit should be checked against the `ImGui::Begin` set, not against `FOREACH_PANEL` — they are different domains and conflating them is how this drifted.
- **HAZ-8 (doc drift feeding future agents):** `MetaRegistry.hpp:75` + root `CLAUDE.md` name 4 regimes; there are 5 (`TRENDING_DOWN`, `StrategyInterface.hpp:244`). `LiveReadiness.hpp:271` says 9 checks; there are 10. `TradeHistoryPanel.hpp:129-140` says 11 cols / no header; actual 13 cols / 2 header lines. Each is a §2.5 stale-code-fact.

---

# SPOTS MOST WORTH AN ADVERSARIAL REFUTE (for the paired a-class)

1. **E-1 severity — attack the reachability, not the parse.** I proved field 1 is `node_id` and the `BUY`/`SELL` branches are dead *in sharded mode*. **Try to break it:** is there any deployment where `DataStream/TradeLog.hpp` still writes `logging/btcusdt_order_history.csv` concurrently or after a mode switch (`engine_mode=single_core`, backtest, `PaperResetArchive` restore at `CoreFrameworks/PaperResetArchive.hpp:39`)? If an operator ever ran single_core, an old file with the legacy schema would make TradeReader work on *stale* data — arguably worse than empty. Also probe: does the Equity Curve have any *other* feed I missed? I traced only `GUI/GuiThread.hpp:515,518`.
2. **E-2's "zero production consumers" claim.** I searched `CoreFrameworks Backtest GUI tests tools` with `--no-ignore`. **Try to break it:** any consumer reached via a generated JSONL/stamp emitter that constructs the key strings by concatenation rather than referencing `BACKTEST_METRIC_NAMES`? Any `foxml_suite`-only path? If a real consumer exists, E-2 downgrades from "orphan registry" to "single-consumer registry with a format drift."
3. **My public-build breakage claim (HAZ-2/§ J2-A(e)).** I proved it with a symlink shadow tree + a shape reproduction, **not** by compiling the actual `GUI/DashboardPanels.hpp` TU (that needs SDL2/ImGui). **Refute by:** finding a `-D` or an `#if` in the real GUI build that supplies EmaCross another way, or showing the public repo ships a stub. Conversely, **strengthen it** by attempting a real `./build.sh gui` with `Strategies/private/` temporarily moved aside — that is the decisive test and I did not run it (it would mutate the working tree).
4. **§ J2-A(e)(1), the ID-inversion claim.** I argue `node_0_strategy=ema_cross` → `sid=4` → `STRATEGY_AUTO` in a public build. **Probe the downstream:** is `sid` range-validated anywhere before use (`cfg.node_strategies[...]` consumers, `Strategy_InitPerCore` dispatch)? If a bounds check rejects `sid=5` at boot in a public build, the "auto" case degrades to a refusal rather than a silent misroute — still a bug, lower severity. And check whether `STRATEGY_AUTO`'s resolve step re-derives from regime before any capital decision.
5. **§ J2-B — is `FOREACH_HALT_REASON` genuinely un-exempt?** I checked `SOURCES` (`:90-125`), the docstring's queued cohort (`:31-35`), and the `RETIRED_NAMES` set (`:86-88`). **Refute by:** finding a TECH_DEBT row or plan body that explicitly defers HALT_REASON enrollment. If one exists, this downgrades from `drift_history`-shaped to "homed-deferred" — which is the *safe* state per `feedback_no_unhomed_debt_code_smell`, and the finding becomes a doc-pointer gap instead.
6. **§ J2-C — is the vacuity reachable?** I showed the fallback defeats the assert *in principle*. **Refute by:** arguing the row set is effectively frozen (session boundaries are a market fact, not a tuning knob), so the guard's vacuity is inert. **Counter-probe:** is `MULT` operator-tunable via cfg, and does anything else index `SESSION_BY_HOUR` in a way a gap would corrupt? If MULT is cfg-overridable the ranges become editable and the vacuity goes live.
7. **My "`FOREACH_PANEL` is not the right registry" verdict (§ 4).** I concluded the 16-vs-24 divergence belongs to the docking list, not the panel registry, because the registry's domain is prose-scoped to *stateful* panels. **Refute by:** arguing the registry *should* be widened to all panels (making the dock list auto-generated from it), which would convert an uncomputable prose domain into a computable one and close P-1/P-2/P-5 in one move. That is the stronger design position and I deliberately did not take it — I only mapped.
8. **My shard-attribution inference.** The 47/7/14 arithmetic closes exactly and my residual set matches the 7 enums the directive predicted, which is strong corroboration — **but I never saw shards 1-4's actual registry lists.** If any shard's scope differs from my surface-based inference, a row I marked `covered-by-shard` may be genuinely unswept. The orchestrator should reconcile my column against the real map before treating the set as closed.
9. **The `_rows` naive-`X(` hazard (HAZ-1).** I asserted no current registry trips it, based on reading the enrolled five. **Verify independently** across all 68 registry bodies — a single `MAX(` inside an enrolled body would mean the H21 ledger has been silently wrong, and `check_identifier_retirement.py` is a capital-path guard.

---

# NOVEL ALTERNATIVE CONSIDERED (`feedback_proactive_novel_alternative_consideration`)

The obvious remedy for this whole shard is *"add a complement `static_assert` / CI check per registry"* — ~8 new bespoke checks. Considered and **not recommended as the primary move**, for two reasons: it scales linearly with registries (against `feedback_framework_layer_payoff_diminishing_returns`), and it cannot touch the two hardest cases here (`FOREACH_PANEL`'s prose domain, `FOREACH_TRADE_LOG_COL`'s out-of-binary consumers).

**The alternative: make the domain declarable, and let the existing root registry do the work.**

`FOREACH_REGISTRY` is *already* the one registry in this codebase with a real domain-complement check — `check_meta_registry.py` Check 1 scans the **codebase** for `FOREACH_<X>` macros and diffs against the rows, rather than validating rows-forward. That is precisely the inverted check every registry in this report lacks, and it is already written, wired, and green.

So: add a **DOMAIN column** to `FOREACH_REGISTRY` — one token per row declaring what the registry must cover and how to enumerate it:

| token | meaning | example rows |
|---|---|---|
| `SSOT` | defines its own domain; no complement exists | `FOREACH_STRATEGY`(as a roster), `FOREACH_SP_SECTION` |
| `ENUM:<Name>` | must cover an enum's values | `FOREACH_LIVES_IN_STRUCT` → `LivesInStruct` |
| `STRUCT:<Type>` | must cover a struct's fields | `FOREACH_BACKTEST_METRIC` → `BacktestStats`; `FOREACH_NODE_PERSIST_FIELD` → `NodeContext` |
| `COUNT:<Macro>` | must cover `[0,N)` | `FOREACH_CALIB_LOG_COL` → `BANDIT_MAX_ARMS` (**already implemented by hand** at `CalibLogColRegistry.hpp:137`) |
| `RANGE:<lo,hi>` | must totally cover an integer range | `FOREACH_SESSION_PHASE` → `0,24` |
| `FORMAT:<golden>` | emits a format read by out-of-binary consumers | `FOREACH_TRADE_LOG_COL`, `FOREACH_CALIB_LOG_COL` |
| `PROSE:<reason>` | domain is a judgment; **complement not computable, reason stated** | `FOREACH_PANEL` — *"stateful panels only; stateless keep direct calls"* |

Then `check_meta_registry.py` grows **one** Check 4 that dispatches on the token — reusing the clang backend already in-tree at `tools/check_cache_layout.py:105,519,529,540` for `STRUCT:`, and the shared `_macro_body`/`_rows`/`_args` library for the rest.

Why this is the better shape:
- **It closes the meta-gap, not the instances.** The recurring failure is not "this registry lacks a check", it is *"nobody records what a registry is supposed to cover"*. A DOMAIN column makes the domain a **declared, greppable fact** instead of prose in a `[COLUMN]` comment that drifts (`MetricCompute.hpp:160` / `TradeLogColRegistry.hpp:134` are both such prose, and both are now wrong).
- **`PROSE:` is the load-bearing token, not a cop-out.** It forces the `drift_history` lesson into the schema: the NodeContext report's OQ-3 observed that *the only unpersisted field with no stated reason was the only real finding.* A registry that declares `PROSE:` has stated its reason; a registry that declares nothing fails Check 4. **That single rule would have caught `FOREACH_HALT_REASON`, `FOREACH_BACKTEST_METRIC`, and `FOREACH_LIVES_IN_STRUCT` at their introduction.**
- **It is H18-conformant** (sidecar override indexed by the parent registry, sparse) and H15/H19-native — it extends the existing meta-registry rather than standing up parallel infrastructure, per `feedback_audit_canonical_sister_before_new_infra`.
- **It composes with `SOURCES`.** `check_identifier_retirement.py`'s `SOURCES` becomes derivable: any `FOREACH_REGISTRY` row whose DOMAIN or tags mark it persisted-code-bearing must have a `SOURCES` row — which is § J2-B's complement, mechanized.
- **Cost is bounded and front-loaded:** 68 tokens, most of them `SSOT`. The residual after this shard is ~10 rows needing real thought, and I have named all of them.

**Recommended sequencing** (I do not proceed; this is for Caramel's disposition):
1. **Now, independent of any framework work — E-1** (`GUI/TradeReader.hpp:185-206`): a live Class-2 display lie on the trading dashboard, ~10 lines to correct the column indices. § E-1's blast radius is display-only, and HAZ-5 names the one interaction.
2. **Now — § J2-A(e)/HAZ-2**: the public-clone GUI build break. Six sites; the structural fix (generate the color/name tables from `FOREACH_STRATEGY` the way `FOREACH_RECONCILE_MODE` generates its cfg-string table, `Reconcile.hpp:166-177`) closes the recurring zero-fill class at the same time — M7 territory, and the code already documents two prior instances.
3. **Same ship — § J2-B**: one `SOURCES` row for `FOREACH_HALT_REASON` + `--update`. Trivial, and it is a capital-adjacent H21 hole.
4. **Then** the DOMAIN-column framework, with `FOREACH_LIVES_IN_STRUCT` (§ 7) and `FOREACH_SESSION_PHASE` (§ J2-C) as the first two canonical applications — both are 1-4 line fixes that the framework then generalizes.
5. **Defer / decide**: `FOREACH_BACKTEST_METRIC` (§ 3) is a *disposition* question, not a fix question — either delete it (H21 dead-code removal; it has no production consumer) or make `BacktestPanels` render *from* it and fold `OPT_METRIC_*` in. Half-measures leave four partial enumerations.

---

# OPEN QUESTIONS (for Caramel)

- **OQ-1:** `FOREACH_BACKTEST_METRIC` — delete as dead capital-free infrastructure (H21 "remove dead code"), or promote it to actually drive `BacktestPanels.hpp:784-801` + subsume `OPT_METRIC_*` (`BacktestEngine.hpp:2647-2651`)? Both close the gap; only the second keeps the registry.
- **OQ-2:** Is the public-clone GUI build (`Strategies/private/` absent) a supported configuration? If yes, HAZ-2 is a live release blocker. If the public snapshot is now purely historical (`project_public_repo_is_code_only`, all-private since 2026-07-06), it downgrades to a latent trap that only bites if the private strategy is ever removed — but HAZ-3 (the ID shift) is a hazard **in this tree** regardless.
- **OQ-3:** Should `FOREACH_PANEL` widen to cover **all 24** windows and generate the dock list, converting P-1/P-2/P-5 from three findings into one registry row each? That is the § 4 refute-spot-7 position.
- **OQ-4:** Does `tools/lib/sharded_files.txt` gain a GUI section (making `calls_graph_diff.sh` able to see P-2-class orphans), or does GUI orphan detection get its own scope? The file's header calls itself the SSoT for "the hot/sharded entrypoint file list", so widening it may be the wrong move and a second list the right one.
- **OQ-5:** Does the DOMAIN-column proposal (§ NOVEL) belong in this sweep's ship, or as its own `.E` sub-ship with this report as its input? It is a 68-row touch on the H15 root registry.

---

**Key files (absolute):**
`/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/MetaRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/TradeLogColRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ShardedTradeLog.hpp` · `/home/caramel/code/FoxML_Trader_v2/DataStream/CalibLogColRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/DataStream/TradeLog.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/MetricCompute.hpp` · `/home/caramel/code/FoxML_Trader_v2/Backtest/BacktestEngine.hpp` · `/home/caramel/code/FoxML_Trader_v2/Backtest/BacktestPanels.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/GuiThread.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/TradeReader.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/TradeHistoryPanel.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/DashboardPanels.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/ChartPanel.hpp` · `/home/caramel/code/FoxML_Trader_v2/GUI/SettingsPanel.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/LiveReadiness.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/CfgFieldRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/ControllerConfig.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/SessionPhaseRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/SpSectionRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/Reconcile.hpp` · `/home/caramel/code/FoxML_Trader_v2/CoreFrameworks/EngineCommon.hpp` · `/home/caramel/code/FoxML_Trader_v2/Strategies/StrategyInterface.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/RollingWindowRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/BanditAlgorithmRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/bandit_dispatch_table.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/BarrierBlendModeRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ICVariantRegistry.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/ConfidenceScore.hpp` · `/home/caramel/code/FoxML_Trader_v2/ML_Headers/NodeModelZoo.hpp` · `/home/caramel/code/tick-trader-percore-workspace/tools/check_identifier_retirement.py` · `/home/caramel/code/tick-trader-percore-workspace/tools/identifier_ledger.txt` · `/home/caramel/code/tick-trader-percore-workspace/tools/node_persist_layout.py` · `/home/caramel/code/tick-trader-percore-workspace/tools/lib/sharded_files.txt` · `/home/caramel/code/tick-trader-percore-workspace/tools/chart.py` · `/home/caramel/code/FoxML_Trader_v2/plans/v5.15-live-readiness/reports/2026-08-15-ui-consolidation/i-class-nodecontext-partition.md`
