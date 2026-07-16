// SPDX-License-Identifier: AGPL-3.0
//
// DOGFOOD FIXTURE (E.1.2.A phase 3) — real unit, copied + converted, NEVER compiled.
// Source: CoreFrameworks/EngineCommon.hpp:1-124 @ engine d4812de (2026-07-15 copy).
// Shape exercised: RICH MULTI-SECTION FILE HEADER (survey B gap #7 — "the block Caramel
// flagged") + ANNOTATED INCLUDE BLOCK (survey B gap #15). This file is the FIRST CANONICAL
// of the labeled [COMMENT]_[<label>] sub-section form (build-at-pilot per the locked schema).
// Lossless accounting: ZERO drops — every source comment relocated VERBATIM (no stale
// DERIVED-class facts in this header); code lines byte-verbatim; include annotations stay
// code-local (D-326).

//======================================================================
// [FILE]_[CoreFrameworks/EngineCommon.hpp]
//----------------------------------------------------------------------
// [TAG]_[[ENGINE] [HELPER] [BACKTEST]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[shared train-serve helpers for the per-core lifecycle — collapses the EngineSharded/BacktestSharded Class-18 mirror at the execution layer]
// [REFERENCE]_[DESIGN_SPEC]_[shared-helper-extract-for-train-serve-mirror-close]
// [REFERENCE]_[PARITY]_[PARITY-031]
// [CONTAINS]
//   - [FUNCTION]_[EngineCommon_ApplyBnbDiscount]
//   - [FUNCTION]_[EngineCommon_BootGlobal]
//   - [FUNCTION]_[EngineCommon_BootPerCore]
//   - [FUNCTION]_[EngineCommon_SlowPathCycleOneCore]
//   - [FUNCTION]_[EngineCommon_SlowPathCycleAllCores]
//======================================================================
// [COMMENT]_[PURPOSE]
//----------------------------------------------------------------------
// Shared train-serve helpers for the per-core lifecycle.
// First canonical of the shared-helper-extract-for-train-serve-mirror-close pattern
// (DESIGN_SPECS/refactor-patterns/shared-helper-extract-for-train-serve-mirror-close.md).
//
// Both `EngineSharded_Run` (live; per_node_slow arch) and `BacktestSharded_Run`
// (backtest; iterates per-core via SlowPathCycleOneCore) delegate per-core boot +
// per-core slow-path-cycle work to the helpers declared here. This collapses the
// Class 18 mirror between EngineSharded.hpp + BacktestSharded.hpp at the
// execution layer; closes PARITY-026/027/028/029/030/031/032 by-construction.
//======================================================================
// [COMMENT]_[LIFECYCLE EVENTS COVERED]
//----------------------------------------------------------------------
//   1. Boot: ApplyBnbDiscount (once)     → BootGlobal (once)   → BootPerCore (N times)
//   2. Slow-path-cycle: SlowPathCycleOneCore (per-thread per-core; live)
//                       SlowPathCycleAllCores (per-tick once; backtest fans via wrapper)
//======================================================================
// [COMMENT]_[HELPER COUNT: 5]
//----------------------------------------------------------------------
//   - EngineCommon_ApplyBnbDiscount   — NON-CONST cfg ONE-SHOT mutator (sister to Sharded_ValidatePartialExitCfg)
//   - EngineCommon_BootGlobal         — const cfg one-shot global subsystem init
//   - EngineCommon_BootPerCore        — const cfg per-core boot
//   - EngineCommon_SlowPathCycleOneCore   — const cfg per-core slow-path-cycle body (atomic unit)
//   - EngineCommon_SlowPathCycleAllCores  — const cfg fan wrapper (~10 LOC; loops OneCore N times)
//======================================================================
// [COMMENT]_[CONST-CORRECTNESS DISCIPLINE]
//----------------------------------------------------------------------
// Only ONE helper takes non-const cfg: EngineCommon_ApplyBnbDiscount. This is the
// SINGLE pre-loop cfg mutator. Any future cfg mutation must create its own
// sister `EngineCommon_ApplyXxx` helper — DO NOT mutate cfg inside BootGlobal /
// BootPerCore / SlowPathCycle* helpers (their signatures enforce this via
// `const ControllerConfig<F>&` reference type). Type system prevents drift.
//
// Sister precedent for non-const pre-loop helpers: `Sharded_ValidatePartialExitCfg`
// (existing one-shot cfg validator; same shape).
//======================================================================
// [COMMENT]_[PER-CALL-SITE EXEMPTION DISCIPLINE]
//----------------------------------------------------------------------
// Legitimate live-only / backtest-only differences are handled via:
//   - cfg flag branches at boot time (e.g., cfg.lifecycle_cfg_flags BITMAP_IS_SET dispatch)
//   - Conditional compile (#ifdef LATENCY_PROFILING)
//   - External wrapper before/after helper (e.g., bandit_state_prior_path operator override)
// NOT via nullable args — every helper takes reference (`&`), no pointer (`*`) args.
// NOT via cfg flags that duplicate semantics — that's a Class 24 anti-pattern.
//
// Legitimate live-only exemptions (per M5 false-positive surface):
//   - Persistence sinks: ShardedTradeLog_Init, OrderManager_OpenCalibrationLog
//   - Threading observability: NodeLatencyStats_Enable
// These STAY in EngineSharded_Run caller scope (NOT in helpers).
//======================================================================
// [COMMENT]_[STATIC-SCOPE DISCIPLINE (Decision G)]
//----------------------------------------------------------------------
// EngineSharded_Run holds ~30 function-scope `static` objects (g_notify_state /
// g_tick_rec / g_depth_shared / g_init_arena / g_calibration_log_file / etc.).
// These STAY in caller scope (process-lifetime + thread-shared semantics).
// Helpers MUST NOT define new statics.
//======================================================================
// [COMMENT]_[PARITY-031 CLOSURE: BACKTEST_REGIME_SAMPLE_CORE]
//----------------------------------------------------------------------
// Backtest samples regime from a SINGLE canonical core to preserve the pre-.B.4
// fc_ctx.regime_state semantic (single regime value per feature collector tick).
// Per-core regime variance IS collected at per-core inference time
// (state.nodes[c].regime_state.current_regime in SlowPathCycleOneCore), but the
// backtest feature collector context downstream needs ONE regime value per tick
// (not [MAX_EXECUTION_NODES]).
//
// Live engine doesn't have this constraint: live inference accesses
// state.nodes[c].regime_state per-core directly (canonical site EngineSharded:3194).
//
// Rationale for core 0 specifically: preserves sample_regimes=0 semantic that
// fc_ctx.regime_state held pre-.B.4. Future-readable: grep BACKTEST_REGIME_SAMPLE_CORE
// to find this constant. Future contributors can change the sampling strategy
// (e.g., majority-vote across cores) by updating this constant + comment.
//======================================================================

#pragma once

#include <cstdint>      // uint64_t (used in slow-path-cycle helper signatures for ts_us)
#include <cstdio>       // fprintf (used in ApplyBnbDiscount stderr message)
#include <x86intrin.h>  // __rdtsc (slow-path latency sampling — sister to EngineSharded.hpp:82)

// Phase B includes (added as helper bodies land; sister-convention relative paths):
//   B.0 ApplyBnbDiscount → ControllerConfig.hpp (cfg.nodes[c].fee_rate_*) + FixedPointN.hpp (FPN_Binary<F> arithmetic)
//   B.1 BootGlobal → ControllerEventLoop.hpp (EventLoopState_Init + ConfigureKillSwitch) + OrderManager.hpp (OrderManagerState<F>) + RegimeDetector.hpp (Regime_Init)
#include "ControllerConfig.hpp"                  // ControllerConfig<F>, MAX_EXECUTION_NODES, MASK_RISK_CFG_KILL_SWITCH_ENABLED (transitive via RiskCfgFlagRegistry)
#include "ControllerEventLoop.hpp"               // EventLoopState<F>, EventLoopState_Init, EventLoopState_ConfigureKillSwitch, EventLoopState_RegisterCore, EventLoopState_SetCoreStrategy
#include "OrderManager.hpp"                      // OrderManagerState<F>
#include "ExecutionCore.hpp"                     // ExecutionCore<F>, ExecutionCore_Init, ExecutionCore_SetPermission, SPSCRing<Tick<F>, EXECUTION_NODE_TICK_RING_SIZE>
#include "ModelValidation.hpp"                   // NodeModelZoo_ValidateAgainstCfg (extracted at v5.14.2.E.1; closes PARITY-012)
#include "../FixedPoint/FixedPointN.hpp"         // FPN_Binary<F>, FPN_Mul, FPN_FromDouble, FPN_Zero, FPN_ToDouble
#include "../MemHeaders/NodeStateFlagRegistry.hpp"  // NODE_STATE_FLAG_SET, MASK_NODE_STATE_MODEL_LOAD_FAILED
#include "../Strategies/RegimeDetector.hpp"      // Regime_Init
#include "../Strategies/StrategyInterface.hpp"   // STRATEGY_ML, STRATEGY_NONE (auto-generated via FOREACH_STRATEGY X-macro)
#include "../Strategies/StrategyLifecycle.hpp"   // tt::Strategy_InitPerCore (closes PARITY-029)
#include "../ML_Headers/ModelInference.hpp"      // MODEL_BACKEND_XGBOOST
#include "../ML_Headers/NodeModelZoo.hpp"        // NodeModelZoo<F>, EnsembleModelZoo<F>, NodeModelZoo_Init, EnsembleModelZoo_Init, NodeModelZoo_LoadFromDir, NodeModelZoo_LoadLegacy, NodeModelZoo_PostLoadSetup, EnsembleModelZoo_AutoDetectFromDir, EnsembleModelZoo_PostLoadSetup, NodeModelZoo_Free, MASK_EZOO_ACTIVE
#include "../ML_Headers/ConfidenceScore.hpp"     // ConfidenceScorer_Init, ConfidenceScorer_BindCompositeCfg, CONFIDENCE_FRESHNESS_TAU_DEFAULT
#include "../ML_Headers/RollingTurnover.hpp"     // RollingTurnover_Init
#include "../ML_Headers/FeatureRegistryOverlay.hpp"  // FeatureOverlay_PostLoadVerify
// Phase B Step B.3 includes (v1.7.3 N-6 + N-2 + N-3 + N-4; landed at v1.7.3 amendment cycle):
#include "../DataStream/BinanceDepth.hpp"             // BookSnapshot<F> sister-canonical reuse per v1.7.3 N-6 (DepthSnapshot NOT invented; reuse existing canonical per feedback_audit_canonical_sister_before_new_infra)
#include "SlowPathGateRegistry.hpp"                   // SLOW_PATH_GATE_AUTOPOPULATE_ENGINE_WIDE macro + MASK_BREAKEVEN_ON_PROFIT cached gate bit (D1-B; v1.7.3 N-2 correct arg signature is (state.global_gate_state, cfg))

// Phase B include enumeration (for body coding; uncomment as needed):
//   #include "CoreFrameworks/ControllerConfig.hpp"
//   #include "CoreFrameworks/EventLoopState.hpp"  // (if separate from ControllerEventLoop.hpp)
//   #include "CoreFrameworks/ControllerEventLoop.hpp"
//   #include "CoreFrameworks/OrderManager.hpp"
//   #include "CoreFrameworks/PortfolioController.hpp"
//   #include "CoreFrameworks/ExecutionCore.hpp"
//   #include "Strategies/StrategyParameters.hpp"
//   #include "ML_Headers/ConfidenceScore.hpp"
//   #include "ML_Headers/RollingTurnover.hpp"
//   #include "ML_Headers/ModelInference.hpp"           // per-core model load
//   #include "ML_Headers/NodeModelZoo.hpp"
//   #include "MemHeaders/BitmapMacros.hpp"
//   #include "FixedPoint/FixedPointN.hpp"
//   #include <cstdint>
// Verify at Phase B Step A audit time — actual includes resolved during body extract.

namespace tt {

// (fixture slice ends here — the helper bodies + namespace close live in the real file)
} // namespace tt
