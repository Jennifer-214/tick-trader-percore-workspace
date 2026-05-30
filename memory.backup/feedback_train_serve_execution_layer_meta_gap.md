---
name: feedback_train_serve_execution_layer_meta_gap
description: Pre-coding audit gate must include train-serve EXECUTION-LAYER parity walk (not just cfg/stamp surface) for any HIGH-RISK ship touching boot or slow-path cycle
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 12254fb6-c7fd-4408-b0cc-0330cd24fc0f
  sister_specs: [feedback_audit_canonical_sister_before_new_infra.md, feedback_proportionate_response_to_audit_findings.md, feedback_categorical_triggers_over_hardcoded_refs.md, feedback_iteration_spiral_signals_audit_meta_gap.md, feedback_implementation_detail_blindspot_recovery_via_taxonomy.md, feedback_enumerate_consumers_before_registry_row_deletion.md]
  tags: [meta-discipline, audit-methodology, wire-format]
---

When a HIGH-RISK ship touches boot code OR slow-path-cycle body (whether on EngineSharded side OR BacktestSharded side), the pre-coding audit gate MUST include a train-serve execution-layer parity walk. The cfg/stamp/wire-format audits ([[feedback_audit_canonical_sister_before_new_infra]] / `/parity-check` Section A-H) do NOT cover this layer.

**Why:** Codified 2026-05-24 mid-`v5.15.5.F.4d.1.B.3` ship cycle. The ship's pre-coding audit gate fired `/precoding-audit-gate` + `/parity-check` + `/dod-audit` + `/readiness` + `/trace-deps` + `/merge-scan` + `/accounting-audit` against the cfg-derived consumer framework consolidation surface. All 6 audits returned GREEN-or-YELLOW. ZERO of them flagged the 4 CRIT train-serve execution-layer breaks that an ad-hoc ML↔LIVE structural sweep agent surfaced when Caramel asked "im sure there are structural issues between ML and LIVE" — kill_switch dead in live (PARITY-026; 14+ months silent); ML exit-prediction submit absent in backtest (PARITY-027); ConfidenceScorer composite cfg unbound in backtest (PARITY-028; sister to PARITY-003 closed only on live side); Strategy_InitPerCore never called in backtest (PARITY-029; pre-v5.4 F7 bug never closed on backtest mirror).

The audit suite was layer-specific (cfg/stamp/wire-format). The gap was layer-coverage, not audit-rigor. The framework consolidation paid off — it gave us the audit tools that found these — but the audit cadence missed the boot + slow-path-cycle layer entirely.

**How to apply:**
- Before substantive coding on any HIGH-RISK ship touching `EngineSharded.hpp` boot block (~lines 670-1160) OR `BacktestSharded.hpp` boot block (~lines 180-420) OR slow-path-cycle body on either side OR a NEW Init/Bind/Configure call at boot: run `/train-serve-asymmetry-sweep <layer>` (NEW skill at `.B.4`; layer keyword = execution / oms / gui / boot / logging / stamp-cohort / datastream).
- For every `Init/Bind/Configure(...)` call in `EngineSharded_Run` boot, verify matching call in `BacktestSharded_Run` boot OR documented exemption.
- For every slow-path-cycle dispatch in `EngineSharded_Run` body (`MASK_ML_CFG_*` gated; `state.cores[c].X > threshold` triggered; `OMS_PushExitForSlot`-style submit), verify matching dispatch in `ShardedBacktestDriver` slow-path block OR documented exemption.
- Catch the [[feedback_proportionate_response_to_audit_findings]] Option D ARCHITECT case when findings cluster — extracting `EngineCommon_BootPerCore` + `EngineCommon_SlowPathCycleOneCore` shared helpers (TECH_DEBT-119) closes 4 CRITs + 3 HIGHs structurally vs N individual patches.
- File class: this is the M5 meta-discipline (sister to M1 sister-registry parity + M2 cross-tool emit enumeration + M3 anti-pattern false-positive surface + M4 implementation-detail blindspot taxonomy). Lives in `DOCS/DESIGN_PHILOSOPHY.md` § 11.5 meta-discipline registry after codification at `.B.4` ship close.
- Categorical trigger (not hardcoded refs per [[feedback_categorical_triggers_over_hardcoded_refs]]): "any HIGH-RISK ship touching EngineSharded boot OR slow-path-cycle body" — applies regardless of specific ship name / version.

Sister: [[feedback_iteration_spiral_signals_audit_meta_gap]] (the parent recognition pattern — when audit gates surface findings of fundamentally different shape than what audits target, codify the meta-gap not patch the symptom). Sister: [[feedback_implementation_detail_blindspot_recovery_via_taxonomy]] (M4; same shape but at implementation-detail layer instead of train-serve execution-layer). Sister: [[feedback_audit_canonical_sister_before_new_infra]] + [[feedback_enumerate_consumers_before_registry_row_deletion]] (cfg/stamp surface disciplines that DO work at their layer — M5 extends the cohort to execution layer).
