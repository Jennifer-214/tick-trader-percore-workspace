---
type: audit-cadence-plan
audit_kind: train-serve-asymmetry-sweeps-by-layer
established: 2026-05-24
predecessor: plans/v5.15-live-readiness/plan_checks/2026-05-24-train-serve-asymmetry-sweep.md (the execution-layer first canonical sweep that surfaced 4 CRITs)
cadence: per-layer rolling, ~1 per week post-.B.4 ship close; or sooner if blocking finding surfaces
sprint: v5.15-live-readiness (extends into .F.5.X scope sizing)
status: planning
---

# Future train-serve asymmetry sweeps — 6-layer audit cadence

## Why this doc exists

Caramel surfaced 2026-05-24: "im sure there are structural issues between ML and LIVE." First canonical sweep (execution layer, captured at `plan_checks/2026-05-24-train-serve-asymmetry-sweep.md`) found 4 CRIT + 3 HIGH + 2 MED train-serve breaks — all surviving from prior framework consolidation work because the cfg/stamp audit suite doesn't walk this layer.

The same pattern likely repeats at OTHER layers. Per the M5 meta-discipline ([[feedback_train_serve_execution_layer_meta_gap]]), pre-coding audit gates need layer-coverage extension. This doc catalogs the 6 candidate layers + their audit-agent prompts + expected surfaces + priorities + scheduling.

## Cadence model

**Per `feedback_motivated_collaborator_for_caramel` + `feedback_plan_right_not_fast`:** sweeps are bounded + scheduled, NOT continuous. Each layer gets ONE focused agent run. Findings auto-write per [[feedback_consult_on_audit_findings]] auto-write contracts (PARITY_ISSUES + TECH_DEBT + plan_checks doc). Sub-ship scope sized BY findings.

**Cadence:** ~1 layer per week AFTER `.B.4` ship close (so EngineCommon extract is in place — many GUI/OMS findings may collapse once execution-layer helpers exist). EARLIER if a blocking finding surfaces during `.B.4` coding.

**File the cadence under [[project_anti_spaghetti_audit_cadence]]** — same quarterly-cadence shape; this is the train-serve subset.

**NEW SKILL CANDIDATE:** `/train-serve-asymmetry-sweep <layer>` lands at `.B.4` ship close per [[feedback_train_serve_execution_layer_meta_gap]] codification procedure. Captures today's prompt shape parameterized by layer keyword. Future-Claude invokes consistently across layers.

## The 6 layers

| # | Layer | Audit-agent prompt | Expected surface | Priority | Target plan_checks file |
|---|---|---|---|---|---|
| 1 | **OMS / order submission** | Backtest fill simulation vs live OMS fill processing; fee model parity; partial-fill handling; kill_switch trip propagation; OrderManager_Tick + DrainPostFill cycle | Order pool, drainer, post-fill events | **HIGH** (financial correctness) | `plan_checks/2026-XX-XX-asymmetry-sweep-oms.md` |
| 2 | **GUI panel parallelism** | engine_gui DashboardPanels vs foxml_suite BacktestPanels; parallel SettingsPanel / TradeHistory / LogViewer init paths; per-panel cfg dispatch + render parity | foxml_suite has likely 5-10 mirror sites (sister to today's foxml_suite cfg-source-of-truth finding) | **MED-HIGH** (operator UX) | `plan_checks/2026-XX-XX-asymmetry-sweep-gui.md` |
| 3 | **Boot / init triple entry** | main.cpp vs engine_gui vs foxml_suite — argv handling / cfg loader / PostLoadSetup chain / SHALT init / EnsembleModelZoo_PostLoadSetup | Init sequencing drift between 3 main() entry points | **MED** | `plan_checks/2026-XX-XX-asymmetry-sweep-boot.md` |
| 4 | **Logging / observability** | backtest trade/calibration/metrics CSV vs live engine output; per-symbol metrics CSV; trade log column parity; calibration log emit | Format drift between modes | **MED** | `plan_checks/2026-XX-XX-asymmetry-sweep-logging.md` |
| 5 | **Stamp body PRE_CFG / POST_CFG model-state cohort** | Phase F closed cfg-derived cohort; model-state cohort (PRE_CFG + POST_CFG halves at FOREACH_STAMP_BOUND_MODEL_CONST_*) may still mirror; Class 32 prefix asymmetry residuals | Surviving prefixed vs unprefixed field-name drift in model-const cohort | **MED** | `plan_checks/2026-XX-XX-asymmetry-sweep-stamp-cohort.md` |
| 6 | **DataStream parsing** | Backtest replay parser vs live Binance WS parser; depth book reconstruction parity; flow features parity; TickRecorder/DepthRecorder format vs runtime parse | Tick / depth byte-level | **LOW-MED** (relatively independent) | `plan_checks/2026-XX-XX-asymmetry-sweep-datastream.md` |

## Recommended fire order (post-.B.4)

1. **Layer 1 (OMS)** — financial correctness; highest blast radius
2. **Layer 2 (GUI)** — operator UX + sister to foxml_suite finding (`v5.15.6.A/B/C` may absorb some)
3. **Layer 5 (Stamp cohort)** — recent surface (Class 32 residuals could affect post-`.B.3` ship close)
4. **Layer 3 (Boot)** — parallel init shape; sister to GUI Layer 2
5. **Layer 4 (Logging)** — operator observability; less critical
6. **Layer 6 (DataStream)** — relatively independent; lowest priority

## Per-sweep deliverable shape

Each sweep produces:
1. A `plan_checks/2026-XX-XX-asymmetry-sweep-<layer>.md` capture doc (same shape as `2026-05-24-train-serve-asymmetry-sweep.md`)
2. PARITY_ISSUES entries for any train-serve break (next PARITY-NNN per ID assignment)
3. TECH_DEBT entries for structural deferrals (next TECH_DEBT-NNN)
4. RECURRING_BUG_PATTERNS additions for any NEW anti-pattern class instance
5. Sub-ship scoping recommendation (which queued sub-ship absorbs the findings, OR NEW sub-ship needed)

## Honest gap

This cadence covers train↔serve parity. It does NOT cover other audit dimensions (latency / SIMD parity / cache layout / etc.) — those have their own audit suite + cadence (`/dod-audit` / `/anti-spaghetti` / `/latency-track` / etc.). Don't conflate.

## Cross-references

- Predecessor sweep: `plans/v5.15-live-readiness/plan_checks/2026-05-24-train-serve-asymmetry-sweep.md` (execution-layer first canonical; 4 CRIT)
- M5 meta-discipline: `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/feedback_train_serve_execution_layer_meta_gap.md`
- M5 DESIGN_SPEC at `.B.4` ship close: `DESIGN_SPECS/meta-disciplines/train-serve-execution-layer-parity.md` (DRAFT v0.1)
- NEW skill at `.B.4`: `/train-serve-asymmetry-sweep <layer>` parameterized
- Sister cadence: `project_anti_spaghetti_audit_cadence` (quarterly anti-spaghetti audit; this train-serve cadence is a subset)
- Sprint MASTER: `plans/v5.15-live-readiness/MASTER.md` (post-`.B.4` audit-cadence row added at MASTER amendment)
