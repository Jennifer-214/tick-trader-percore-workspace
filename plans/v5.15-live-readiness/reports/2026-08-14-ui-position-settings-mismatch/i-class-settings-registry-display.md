---
type: agent-report
status: FROZEN — verbatim agent output, saved at receipt
directive: map the GUI settings display vs the split cfg registries (per-node vs global) + operator-observed settings-display issues
agent_class: i-class
delivered: 2026-08-14 (during the E.1.2 D-305-tail pickup session; operator spot-check findings)
consumed_by: the eventual-item documentation (settings per-node render completion leaf) + O-1 triage
---

# I-CLASS REPORT — GUI settings display vs the split cfg registries (per-node vs global)

**Directive:** map what the GUI SETTINGS DISPLAY does with the H17 registry split (FOREACH_GLOBAL_CFG_FIELD vs FOREACH_PER_NODE_CFG_FIELD), the operator-visible defects, and the eventual-plan shape for "per node settings should be a different registry than the global settings."
**Repo:** /home/caramel/code/FoxML_Trader_v2 @ HEAD 3c57534 (feat/v5.15-live-readiness). All cites verified at HEAD by read/grep/tool — none recalled.
**Tools run:** `tools/check_per_node_registry_integrity.py` (all structural checks PASS; Check 6 WARN: anti-pattern-1 dual-consumer shape for `fee_floor_mult`/`partial_exit_pct`/`tp2_mult`) · `tools/check_cfg_key_prefix_drift.py` (CLEAN — but see D-2: it does not cover the GUI-writer surface). Skill methodology applied: `/registry-fit-audit` (SKILL.md walked; fitness-signal + verdict framework used in § Split-question).

**Registry naming correction to the spawn kit:** the per-core registry at HEAD is `FOREACH_PER_NODE_CFG_FIELD` (88 rows, tool-verified — not ~93; the E.1.1 Core→Node rename landed), at `CoreFrameworks/CfgFieldRegistry.hpp:581-798`. `FOREACH_GLOBAL_CFG_FIELD` = 59 rows at `:336-557`. Not a material frame error — flagging per arming § 4.

---

## 1. Render-path map (registry → UI section, file:line)

The Settings window = 1 "Global" tab + N "Engine c" per-core tabs (`GUI/SettingsPanel.hpp:2039-2062`, `GUI_Panel_Settings` :1967).

**The GLOBAL tab (`Settings_RenderGlobalTab` :1249-1424) renders THREE sequential passes, all writing flat (un-prefixed) cfg keys:**

| # | Source | Generator / walker | Storage backing | Write path | Cite |
|---|---|---|---|---|---|
| G-1 | Manual `field_defs[]` (30 hardcoded entries + 21 `FOREACH_<DOMAIN>_CFG_FLAG` auto-rows) | hand loop over `field_defs[i]` | legacy parallel arrays `float_vals[]/bool_vals[]/path_vals[]` (:811-813) | `cfg_write_field(key,…)` per edit (:1294/:1305/:1312/:1326) | :387-635, :1253-1335 |
| G-2 | `FOREACH_GLOBAL_CFG_FIELD` (59 rows) | `GlobalCfgRenderTable<64>::fns[]` (X_GEN_GLOBAL_RENDER_FN, tt-dispatch Class-23-safe) :225-246 | typed `gui_engine_cfg` (`ControllerConfig<64>`, :807) | `cfg_render_and_persist` → `cfg_write_field` (:335-344) | walk :1356-1384 over `g_global_cfg_render_mask` |
| G-3 | **`FOREACH_PER_NODE_CFG_FIELD` (88 rows) — YES, registry-driven render EXISTS, but in the GLOBAL tab** | `PerNodeCfgRenderTable<64>::fns[]` (X_GEN_PER_NODE_RENDER_FN) :265-300; the sole NO_FLAT_FIELD row (`strategy`, CfgFieldRegistry.hpp:796) renders a stub | same flat `gui_engine_cfg.<name>` — "fields haven't moved yet" (:219-221, :1387-1389) | same `cfg_write_field` with the FLAT key (no `node_N_` prefix) | walk :1392-1420 over `g_per_node_cfg_render_mask` |

`grep FOREACH_PER_NODE_CFG_FIELD GUI/` confirms SettingsPanel.hpp is the ONLY GUI consumer (:260/:291/:297/:1340). Render mask = `~(IS_BOOT_ONLY | HIDDEN_BY_DEFAULT)` (CfgFieldRegistry.hpp:1582).

**The per-core "Engine c" tabs (`Settings_RenderPerCoreTab` :1521-1947) render NOTHING registry-driven:**

| # | Source | What | Write path | Cite |
|---|---|---|---|---|
| P-1 | "Node Configuration" hand-rolled | strategy dropdown (+ live hot-swap flag), Risk %, Model Path, Model Dir combo | `node_%d_strategy` / `node_%d_risk_pct` / `node_%d_model_path` / `node_%d_model_dir` via `cfg_write_field` | :1534-1758 |
| P-2 | "ML Ensemble" snapshot panel | read-only weights + horizon checkboxes | `node_%d_disabled_horizons` (:1869-1870) | :1781-1895 |
| P-3 | **Manual `per_node_fields[]` (43 rows, float-only)** — the second manual mirror | InputFloat per row, strategy-filtered via `per_node_field_strategy` string-prefix match (:1459-1473) | `node_%d_<suffix>` (:1936) into `per_node_vals[16][43]` float storage (:816) | table :676-781, loop :1899-1945 |

**Engine read side (the seam the GUI must agree with):** `node_N_<suffix>=` parses into `PerNodeOverrides` (`ControllerConfig.hpp:3250-3404`; field set = `PER_NODE_OVERRIDE_FIELDS` 44 float rows :91-160 + 3 Money outliers :225-227 + 3 INT :166-183 + 5 bitmap domains :205-210) → `ControllerConfig_ResolveForCore` (non-zero override wins, :1701-1737) → `ControllerConfig_PopulateCoresFromFlat` copies the resolved view into the authoritative `cfg->nodes[c]` (:1766-1815). Unrecognized `node_*` key ⇒ **`CFG_FAULT_UNKNOWN_KEY` → boot HARD-REFUSED** (:3478-3482; consumed at `main.cpp:203`); live hot-reload is warn-keep-old (`CoreFrameworks/EngineSharded/Async.hpp:325-344`).

## 2. Manual field_defs[] census

`field_defs[]` (:387-635; `NUM_FIELDS` :636). Members remaining hardcoded, by section, with the stay-reason per in-file comments:

- **Trading:** `fee_rate_maker`, `fee_rate_taker` (:392-401) — "parser has explicit_set side effect" (:391). *But both are now ALSO per-node registry rows* (CfgFieldRegistry.hpp:788-789) → double-render, see D-3.
- **Entry Filters:** `offset_stddev_mult`, `offset_stddev_min`, `offset_stddev_max` (:409-412) — "not in .F.4b registry cohort" (:407-408). *`offset_stddev_mult` since became a per-node registry row* (:772) → double-render.
- **Regime Detection:** `regime_vol_spike_ratio` (:436).
- **Session Filters:** 4 `session_*_mult` (:447-452).
- **EMA Gate:** `gate_ema_alpha` (:458) — manual parse precomputes `1-alpha` (`ControllerConfig.hpp:3454-3458`).
- **Danger Gradient:** `danger_warn_stddevs`, `danger_crash_stddevs` (:462-465).
- **Tick Recording:** `record_max_days` (:469, CFG_FLOAT) — *also a global registry row* (KIND_INT, :390) → double-render.
- **Operational Monitoring:** `notify_backend`, `notify_command`, `notify_cooldown_secs` (:473-496) — *backend + cooldown also global registry rows under a DIFFERENT section name "Notifications"* (:442/:445) → double-render, section mismatch.
- **Toggles:** `min_book_imbalance` (:503).
- **FoxML:** `confidence_window` (:509) — *also per-node registry row same section* (:671) → double-render.
- **Validation:** `held_out_fraction` (:513) — *also global registry row same section* (:488) → double-render.
- **Models/Barrier (KIND_STRING/_FILE_PATH cohort, ".F.4e scope" :633):** `ml_model_path`, `regime_model_path`, `peak_model_path`, `valley_model_path` (:525-534).
- **Per-Node:** `num_execution_nodes_PLACEHOLDER` (:544) — dead placeholder; real field migrated (:541-543).
- **ML Hyperparams:** `xgb_subsample`, `xgb_colsample_bytree`, `xgb_min_child_weight`, `xgb_seed`, `xgb_tree_method` (:575-590) — min_child_weight + seed are also global registry rows but IS_BOOT_ONLY (:394/:397) ⇒ render-mask-excluded ⇒ NOT double-rendered.
- **+ 21 auto-rows** from FOREACH_{LIFECYCLE,GATE,ML,RISK,OPS}_CFG_FLAG (:605-618).

Tracked home: TECH_DEBT-063 "field_defs[] full elimination (in-progress)" (workspace `DOCS/tech-debt/open.md:3895-3910`).

## 3. Per-node override edit/display reality

- **Where the operator CAN set a `node_N_*` override:** ONLY the per-core tab surfaces P-1/P-2/P-3 above. Coverage = 43 float suffixes + strategy/risk_pct/model_path/model_dir/disabled_horizons.
- **Engine-parseable override keys with NO GUI edit surface (hand-edit-only):** `winsor_pct_low/high`, `risk_full_size_threshold`, `risk_min_size_threshold`, `risk_min_size_pct` (ControllerConfig.hpp:150-160), INT `poll_interval`/`risk_degradation_curve`/`barrier_blend_mode` (:166-183), all per-bit bitmap-domain keys (e.g. `node_N_partial_exit_enabled`, :3305-3336), `node_N_time_exit_ticks` (:3264), `node_N_symbol` (:3268), `node_N_horizon_list`/`ensemble_blend_mode` (:3346-3365), `node_N_feature_mask` (:3379).
- **Resolved-vs-default display:** the per-core tab shows the RAW override (0 = inherit) and **never shows the inherited/effective value**. The comment claiming "the current value from the Global tab is shown next to the input as a small grey hint" (:1438-1439) is **STALE — no such hint exists in the render loop** (:1899-1945; verified per arming § 2.5). The operator cannot see what a node actually trades with from Settings.
- **Dashboard:** the per-core expandable details (`GUI/DashboardPanels.hpp:721-`) show live TRADING state (gate price, halt/SHALT, strategy), not resolved cfg. The Account/Stats "TP/SL" readout (`DashboardPanels.hpp:1271-1275`) is published from the FLAT global `ctrl->config.take_profit_pct/stop_loss_pct` (`DataStream/EngineTUI.hpp:1848-1849`) — one number for the engine while nodes may run `node_N_*` or strategy-specific (`ml_tp_pct` etc.) overrides. Only `poll_interval_ticks` is published per-core-resolved (EngineTUI.hpp:1313).

## 4. Defect candidates (operator's seat)

| ID | file:line | Shape | Operator symptom | Severity |
|---|---|---|---|---|
| **D-1** | GUI/SettingsPanel.hpp:777 (writer :1933-1940) vs ControllerConfig.hpp:143-144 (override deleted v5.14.9.D) + :3478-3482 (unknown `node_*` = HARD-REFUSE) + main.cpp:203 | GUI still carries the RETIRED `confidence_freshness_tau` per-core row; editing "Conf Tau (s)" on any ML node writes `node_N_confidence_freshness_tau=` into engine.cfg — a key the parser hard-refuses | **Touching one settings widget poisons engine.cfg: every reload thereafter is inert (warn-keep-old, Async.hpp:325-344) and the NEXT BOOT is REFUSED** until the line is hand-deleted. TECH_DEBT-208 (open.md:3290-3296) claims the E.1.1 stopgap (`tools/check_gui_engine_cfg_key_parity.py` + delete-the-stale-row) contains this — **NEITHER landed at HEAD** (tool absent from tools/; row present); `check_cfg_key_prefix_drift.py` does not cover it (guards prefix+RETIRED_KEYS in shipped cfgs, not GUI writer keys — :51-141). The ledger's containment claim is stale. | **HIGH** (live boot-brick path) |
| **D-2** | SettingsPanel.hpp:1392-1420 (per-node walk in the GLOBAL tab) + ControllerConfig.hpp:1709-1714 (override wins) | All 87 renderable per-node registry fields (incl. capital fields `take_profit_pct`/`stop_loss_pct`/`risk_pct`/`kill_switch_*`, CfgFieldRegistry.hpp:583-634) render in the GLOBAL tab as flat edits with no node scoping | Class 44/A1-adjacent display-lie: for any node carrying a `node_N_` override, the Global-tab edit is silently inert for that node; nothing indicates which nodes inherit. Also the conceptual inversion the operator named — "trading params look global" | **MED-HIGH** |
| **D-3** | pairs: :392-401↔CfgFieldRegistry.hpp:788-789 · :409↔:772 · :469↔:390 · :473/:493↔:442/:445 · :509↔:671 · :513↔:488 | **8 cfg keys double-rendered in the Global tab** (`fee_rate_maker`, `fee_rate_taker`, `offset_stddev_mult`, `record_max_days`, `notify_backend`, `notify_cooldown_secs`, `confidence_window`, `held_out_fraction`) — manual widget backed by `float_vals[]` + registry widget backed by `gui_engine_cfg`, same file key | Two widgets for one setting; editing one leaves the twin showing the stale value for the whole GUI session (`Settings_Load` runs once, :1974). Bonus mismatches: `record_max_days` FLOAT-text vs INT-slider[1,365]; notify pair under two different section names; `held_out_fraction` clamp text [0.05,0.30] vs registry [0,1] | **MED** (Class 18/47 split-brain, directly "settings display issues") |
| **D-4** | walker section logic :1359/:1395 (new header on section CHANGE) + registry row order | Section-name fragmentation + tri-source collision: registry rows are NOT section-contiguous (global walk emits 'Drift Acknowledgments' 3x, 'ML' 2x, 'Trading' 2x…; per-node walk emits 'Strategies' 4x, 'ML' 4x, 'FoxML' 3x…) and sources collide ("Trading" = 1 field_defs + 2 global-walk + 2 per-node-walk headers = **5 same-label CollapsingHeaders in one tab**, sharing one ImGui ID within the `PushID("global_tab")` scope :2045) | The ".F.4c.3 plan defect #1" verbatim ("many duplicate empty section headers... operator can't usefully scan", plan §Why) — still open at HEAD. The in-file claim "iteration in FIELD_IDX_* order = section-grouped order" (:1348-1349) is FALSE — stale comment | **MED** |
| **D-5** | DashboardPanels.hpp:1271-1275 ← EngineTUI.hpp:1848-1849 | Account panel TP/SL shows flat global while nodes trade per-node/strategy-resolved values | Dashboard states a TP/SL no node may actually be using (sister of the A1 warm-restart instance; same family as the A24 GUI spacing-diagnostic inversion adjudicated at decision-log E-architecture-v2:1298) | **MED** |
| **D-6** | :1899-1945 vs comment :1438-1439 | No inherited-value hint in per-core tabs (stale comment claims one) | Operator can't determine a node's effective value anywhere in the GUI | **LOW-MED** |
| **D-7** | § 3 list above | ~13+ override key families GUI-uneditable | Contradicts the v5.15.6 goal "operator never needs to edit cfg files manually" (plans/_future/2026-05-14 §Goal) | **LOW** |
| D-8 | :816 (`float per_node_vals`), fmt %.2f-%.4f :1938 | Per-core overrides round-trip through `float` + coarse printf | Precision truncation on write of fine-grained overrides | LOW |
| D-9 | :860/:906 `char buf[16384]` in `cfg_write_field` | 16KB read cap; a >16KB engine.cfg gets truncated then REWRITTEN truncated (:913-915) | Silent cfg-tail loss on large cfgs (88-row per-node × 16 nodes future makes this reachable) | LOW (latent) |
| D-10 | mirror trio: CfgFieldRegistry rows (`momentum_min_r2`, :639) vs override/GUI (`momentum_r2_min`, ControllerConfig.hpp:108, SettingsPanel.hpp:708) | Near-identical sibling names across the three enumerations | Confusion + future wrong-key drift bait | LOW |

## 5. Split-question assessment

**The engine registries are already split (H17); the operator-visible problem is (a) + (b), not (c):**

- **(a) Render-side gap — the dominant cause.** The per-node registry HAS a generated render table (SettingsPanel.hpp:265-300) but it is parked in the GLOBAL tab writing flat keys — the explicitly-transitional ".F.4c.3 Step 1" state (":Step 2 will restructure to PerNodeCfgRenderTable receiving cfg.nodes[c]" :219-221; "per-core Settings tabs at Step 6" :276). The per-core tabs still run the pre-registry manual `per_node_fields[]`. **The operator's ask was already planned and partially executed:** `plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3-global-vs-per-core-registry-split.md` quotes her 2026-05-15 directive verbatim ("...splits into a single global registry, and then a reuseable per engine core registry") and its Step 6 is exactly "Per-core tabs walker uses g_per_core_cfg_render_mask + PerCoreRenderTable over cfg.cores[c]" (plan :365-369). Registry split + struct-gen + shadow-populate landed; Steps 3 ([core N] parser), 6 (per-core tabs), and PerNodeOverrides deletion did not (`ResolveForCore` live at HEAD; "WIP2f never landed" per decision-log E-architecture-v2:1306).
- **(b) Secondary: section metadata.** Rows are not section-contiguous and section names collide across the three render sources (D-4). Fixing (a) shrinks but does not eliminate this — per-node rows still need contiguity or a sort key.
- **(c) Registry-schema work: NOT needed.** Per-node rows already carry label/section/tooltip/payload GUI metadata (13-col tuple, CfgFieldRegistry.hpp:567-573). No schema change required — consistent with the LOCKED CfgFieldDescriptor schema (CLAUDE.local sprint invariant).
- **(d) Additional finding the frame missed: a WRITER/PARSER mirror, not just a render gap.** Three hand-maintained enumerations of "per-node settings" coexist — the 88-row registry, the ~50-key `PER_NODE_OVERRIDE_FIELDS`+INT+bitmap parse/resolve set, and the 43-row GUI `per_node_fields[]` — plus `field_defs[]`. D-1 is the proof they drift with capital-grade consequence. Per `/registry-fit-audit` verdicts: FOREACH_PER_NODE_CFG_FIELD = **KEEP** (88 rows, growing, uniform, multi-consumer); `per_node_fields[]` + `PER_NODE_OVERRIDE_FIELDS` = **MERGE-into-registry-derived views** (TECH_DEBT-208's named fix; "genuine per-node 1-touch awaits WIP2f override-registry unification", decision-log:1633); `field_defs[]` = existing DEPRECATE-in-progress (TECH_DEBT-063).

**Where the CLAUDE.md promise stops short in code:** "parser + GUI render + tooltip + per-node override emission auto-flow" (CLAUDE.md cfg-field row; `universal-cfg-field-registry-pattern.md` § Problem statement) holds for parser/tooltip/struct-gen, but **GUI render auto-flows to the WRONG SCOPE** (Global tab, flat key) for per-node rows, and **per-node override emission never joined the auto-flow** — the spec's PER_CORE_OK design was superseded by registry membership-as-scope (CfgFieldRegistry.hpp:567) with the override channel still the separate v4.7.24 macro family.

**Structural fix shape (confirmed viable, mostly already built):** per-core tabs walk `g_per_node_cfg_render_mask` with a `PerNodeCfgRenderTable` variant bound to `gui_engine_cfg.nodes[c]` (or writing `node_N_<name>` keys pre-WIP2f), remove the per-node walk from the Global tab, delete `per_node_fields[]` + the D-3 manual twins, render inherited-vs-overridden state per row. End-state per the locked .F.4c.3 plan + D-275/D-276: the `[core N]`/`[section]` parser (homed E.1.6/E.2, E-MASTER-REFERENCE:43) dissolves the flat-key question entirely.

**Option matrix (evaluated on robustness/latency/design per `feedback_evaluate_options_on_robustness_latency_design_not_time`):**

| Option | What | Assessment |
|---|---|---|
| O-1 Immediate guard (independent of any plan) | Delete the stale `confidence_freshness_tau` row + build the promised `check_gui_engine_cfg_key_parity.py` (GUI-writer-keys ⊆ parser-keys, teeth on this drift) | **Not optional** — closes the D-1 boot-brick + makes the 3-way mirror drift a build error (guards compound). The TECH_DEBT-208 stopgap that was scoped into E.1.1 but never landed |
| O-2 Render-layer completion (.F.4c.3 Step 6 shape) | Per-core tabs from the per-node registry; per-node walk out of the Global tab; kill `per_node_fields[]` + D-3 twins | The operator's ask, the smallest complete fix; no parser/wire change; framework precedent already in-file (the sister table exists) |
| O-3 Full .F.4c.3 completion (WIP2e/f/g + `[core N]` parser + PerNodeOverrides deletion) | The locked end-state | Correct destination, but the parser half is ALREADY homed E.1.6/E.2 (D-275/D-276) and the flat-field deletion behind PortfolioController retirement (TECH_DEBT-191); folding it into a GUI ship re-opens settled sequencing |
| O-4 Novel alternative considered | Per-core tab writes the FUTURE `[node N]` sectioned cfg format directly (GUI leapfrogs to the E.2 parser format) | Rejected for now: inverts the locked E-sequencing, puts a wire-format change inside a GUI ship, makes the GUI unusable against current engines mid-transition. REVISIT as the O-2→O-3 bridge when the E.2 parser lands |
| O-5 Cosmetic only (sort sections/contiguity) | Fix D-4 only | Insufficient — leaves D-1/D-2/D-3 (the actual display lies) open |

## 6. Blast radius + recommended plan home

**Blast radius of the eventual fix (O-2):** GUI-only + one registry file — `GUI/SettingsPanel.hpp` (both walkers, `per_node_fields[]`, `SettingsState.per_node_vals`), `CfgFieldRegistry.hpp` (section-contiguity reorder of per-node rows = pure-comment-level; render-mask untouched), tests for the parity tool. NO hot/slow path (GUI thread only; `calls_graph_diff` should confirm at ship). Cohort siblings to co-fix: D-3 twin deletions, D-5 snapshot field (needs a per-node resolved publish — small EngineTUI + DashboardPanels touch), D-6 hint. Wire/persist: none (cfg file keys unchanged under O-2).

**Recommended homes (split by horizon):**
1. **NOW (not eventual):** O-1 as a small leaf inside the current E.1.2.B window — D-1 is a live capital-adjacent operational hazard whose ledgered containment does not exist at HEAD. This is a TECH_DEBT-208 partial-close, not new scope.
2. **The eventual plan item:** a **dedicated `.E`-series GUI/settings leaf slotted after E.1.2 and before/at `.E.2`** — "Settings per-node render completion (.F.4c.3 Step 6 + per_node_fields[] retirement + TECH_DEBT-208 single-source)". Reasoning: (i) it is the UNSHIPPED REMAINDER of the already-locked .F.4c.3 plan, not new architecture — re-plan by reference to that body; (ii) **NOT** `plans/_future/2026-05-14-v5.15.6-master-cfg-surface-unification-followon.md` — its scope is OTHER cfg FILES (controller/secrets/training cfg integration) — adjacent surface, different deliverable (cross-link only; its "operator never edits cfg manually" goal DEPENDS on this leaf); (iii) **NOT** the decoupling roadmap as owner — it owns the viewer/runtime cfg-OWNERSHIP plane and must get the positioning breadcrumb (auto-write contract), but the render fix is pre-decoupling work; (iv) the `[core N]` parser half stays where D-275/D-276 homed it (E.1.6/E.2) — the GUI leaf should consume it if it lands first (O-4 revisit), else ship `node_N_` writes.
3. TECH_DEBT-191 (flat-field deletion) and WIP2f/WIP2g stay where the A24 decision homed them (decision-log E-architecture-v2:1298, item 4) — the GUI leaf must NOT absorb them.

## 7. Spots most worth an adversarial refute (for the paired a-class)

1. **D-1 reachability:** is there any suppression between the per-core-tab write and the parse refuse (e.g. an operator cfg lacking ML nodes never renders "Conf Tau"; `per_node_field_visible` gates it to STRATEGY_ML nodes :1497-1504 — but any ML node exposes it)? And does some cleanup pass strip unknown `node_` keys from engine.cfg before boot? I found none — refute by tracing every engine.cfg writer.
2. **ImGui ID-collision mechanics (D-4):** same-label `CollapsingHeader`s share state via label-hash within the window ID stack — verify empirically (run `bin/engine_gui`) that collapse-state coupling + duplicate headers actually present as described; my claim is code-read, not screen-verified.
3. **D-3 liveness:** could any of the 8 double-rendered manual entries be dead in practice? `global_section_strategy` (:1188-1197) gates only 8 named sections; the two `held_out_fraction` copies hide/show TOGETHER, so the double persists when visible.
4. **Count claims:** 88/59/43/30+21 — re-derive (88 = integrity tool Check 1; 59/43 = regex/hand-count, weaker).
5. **My severity on D-2:** it presumes operators actually carry `node_N_` overrides in live cfgs; if the operator's engine.cfg has none, D-2 degrades to a scoping-UX complaint (still the ask, lower urgency).
6. **Plan-home recommendation:** an a-class should test the counter-position that O-2 belongs INSIDE `.E.2` proper (headless+configs already owns cfg-surface docs + CFG_FIELD_REFERENCE auto-gen, E-MASTER-REFERENCE:289) rather than as a pre-E.2 leaf — the trade is timing (settings UX pain + D-1 now) vs one-fewer-ship.

**Stale-record corrections to propagate regardless of path:** SettingsPanel.hpp:1348-1349 (section-grouped claim FALSE) · :1438-1439 (grey-hint claim FALSE) · TECH_DEBT-208 body (claims the E.1.1 guard+row-delete landed; neither exists at HEAD) · `cfg-scope-discipline.md:253` ("ResolveForCore deleted at WIP2f" — already flagged at decision-log:1306, still uncorrected).
