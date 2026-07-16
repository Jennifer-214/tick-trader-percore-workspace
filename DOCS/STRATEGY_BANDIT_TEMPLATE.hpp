// Copyright (c) 2026 Jennifer Lewis. All rights reserved.
// Licensed under the GNU Affero General Public License v3.0 (AGPL-3.0).
// See LICENSE file in the project root for full license text.

//======================================================================================================
// [<Name> ONLINE-LEARNING STRATEGY — BANDIT TEMPLATE]
//======================================================================================================
//
// Template for online-learning strategies driven by Bandit-Exp3 weighted
// arm selection. Pattern matches v5.10.0a-final's per-horizon ensemble
// bandit but applied to PARAMETER selection rather than prediction
// blending.
//
// Use case: you have N candidate "arms" (each a different parameter
// setting — e.g. different threshold values, lookback windows, or
// exit criteria). Bandit weights update per-trade-close based on
// realized P&L. Per-regime arm weights so the strategy can prefer
// different arms in different regimes.
//
// HOW TO USE:
//   1. cp DOCS/STRATEGY_BANDIT_TEMPLATE.hpp Strategies/<Name>.hpp
//      cp DOCS/STRATEGY_BANDIT_TEMPLATE.hpp Strategies/<Name>_Bandit.hpp
//        (split into two files: main strategy + bandit helpers)
//   2. Replace <Name> / <name> / <NAME> tokens
//   3. Implement the 4 lifecycle functions (delegate arm selection +
//      reward updates to the helper file)
//   4. Append X-macro line in Strategies/StrategyInterface.hpp
//   5. Wire reward update hook in OrderManager_Tick (drainer post-fill)
//      — search for existing v5.10.0a-final ensemble Bandit_Update
//      call site, mirror the pattern with strategy-id routing
//   6. Wire persistence: load <name>_bandit_state.json at boot,
//      save periodically (every cfg.<name>_bandit_save_interval
//      slow-paths, mirrors v5.10.0a-final's bandit_state.json)
//   7. Add cfg fields: NUM_ARMS, NUM_REGIMES, learning rate, save
//      interval, per-arm initial threshold values
//   8. ./build.sh test — should compile + dispatch correctly
//   9. Refresh the [STRATEGY] tag-block's [TAG]/[OVERVIEW] values, then prove it:
//      python3 tools/check_code_tag_blocks.py --paths Strategies/<Name>.hpp
//      (grammar SSoT: in-code-documentation-schema.md; corpus: DOCS/CODE_TAG_TEMPLATES.hpp)
//
// EFFORT: ~3-4h scaffold (vs ~30 min for static variant).
// Most time is the persistence + drainer reward hook plumbing,
// not the strategy logic itself.
//
// SHARED INFRASTRUCTURE:
//   ML_Headers/BanditLearning.hpp provides:
//     - Bandit_GetProbabilities (AVX-512, thread-safe read)
//     - Bandit_Sample (selects arm idx via softmax)
//     - Bandit_Update (Exp3 weight update on reward)
//   Use these as-is; don't reimplement.
//
// COEXISTENCE WITH v5.10.0a-final ENSEMBLE BANDIT:
//   - Each operates on different state struct
//   - Different persistence files
//   - Different reward sources (per-arm trade vs per-horizon prediction)
//   - Both can run on the same core simultaneously
//
//======================================================================================================
#pragma once

#include "../CoreFrameworks/OrderGates.hpp"
#include "../ML_Headers/RollingStats.hpp"
#include "../ML_Headers/BanditLearning.hpp"  // Bandit_GetProbabilities, _Sample, _Update
#include "../CoreFrameworks/ControllerConfig.hpp"
#include "StrategyInterface.hpp"

//======================================================================================================
// [STRATEGY]_[<Name>]
//------------------------------------------------------------------------------------------------------
// [TAG]_[[ENGINE] [SLOW_PATH] [ML]]
// [SCHEMA]_[v1.0]
// [OVERVIEW]_[online-learning strategy — Bandit-Exp3 weighted arm selection over parameter candidates, per-regime]
// [REFERENCE]_[INVARIANT]_[H22]
//======================================================================================================
// [CODE]
//======================================================================================================

//======================================================================================================
// [SECTION]_[STATE]
//======================================================================================================
// Per-core state. NUM_ARMS and NUM_REGIMES are compile-time constants;
// keep them ≤ 16 to fit BanditLearning's AVX-512 codepath bytewise.
//======================================================================================================
template <unsigned F> struct <Name>State {
    static constexpr int NUM_ARMS = 8;       // candidate parameter values
    static constexpr int NUM_REGIMES = 5;     // matches RegimeDetector

    // Per-regime, per-arm weight (raw — softmax-normalized at sample time)
    double arm_weights[NUM_REGIMES][NUM_ARMS];

    // Per-arm parameter values (e.g. threshold values to try)
    // Operator-tunable via cfg.<name>_arm_thresholds[NUM_ARMS] (CSV-parsed)
    FPN<F> arm_thresholds[NUM_ARMS];

    // Bandit Exp3 learning rate (η). Higher = faster adaptation, more noise.
    // Typical range 0.01-0.1. Default 0.05.
    double bandit_eta;

    // Last selected arm per regime (for routing reward updates back to the
    // arm that produced the trade). Indexed by regime_idx.
    int last_arm_idx[NUM_REGIMES];

    // Save-interval counter — incremented per-Adapt, persists state to disk
    // when reaches cfg.<name>_bandit_save_interval.
    int save_counter;

    int initialized;
};

//======================================================================================================
// [SECTION]_[INIT]
//======================================================================================================
// Initialize uniform weights (1/NUM_ARMS per arm). Spread arm thresholds
// from cfg or use sensible defaults. This is the only place that touches
// the bandit state without a reward signal.
//======================================================================================================
template <unsigned F>
inline void <Name>_Init(<Name>State<F> *state,
                          const RollingStats<F> *rolling,
                          BuySideGateConditions<F> *buy_conds) {
    constexpr int K = <Name>State<F>::NUM_ARMS;
    constexpr int R = <Name>State<F>::NUM_REGIMES;
    constexpr double UNIFORM = 1.0 / K;

    for (int r = 0; r < R; ++r) {
        for (int a = 0; a < K; ++a) {
            state->arm_weights[r][a] = UNIFORM;
        }
        state->last_arm_idx[r] = -1;
    }

    // Default arm thresholds spread logarithmically across a reasonable range.
    // Operator can override via cfg.<name>_arm_thresholds CSV at boot.
    // Example: 0.001%, 0.0015%, 0.0023%, 0.0034%, ... up to 0.01%.
    double base = 0.00001;  // 0.001%
    double mult = 1.5;      // ~50% step per arm
    for (int a = 0; a < K; ++a) {
        state->arm_thresholds[a] = FPN_FromDouble<F>(base);
        base *= mult;
    }

    state->bandit_eta = 0.05;
    state->save_counter = 0;
    state->initialized = 1;

    // Try to load persisted state from disk (overrides defaults if file exists)
    // <name>_Bandit_LoadState(state, "data/<name>_bandit_state.json");

    (void)rolling; (void)buy_conds;
}

//======================================================================================================
// [SECTION]_[ADAPT]
//======================================================================================================
// Per slow-path cycle. NO reward updates here (rewards arrive at trade-
// close, not per-tick). Just:
//   1. Read current regime
//   2. Sample arm from per-regime weight distribution
//   3. Cache selected arm idx for this slow-path → BuildParameters reads
//   4. Increment save counter; persist to disk if interval reached
//======================================================================================================
template <unsigned F>
inline void <Name>_Adapt(<Name>State<F> *state,
                          FPN<F> current_price,
                          FPN<F> portfolio_delta,
                          uint16_t active_bitmap,
                          const BuySideGateConditions<F> *buy_conds,
                          const ControllerConfig<F> *cfg) {
    if (!state->initialized) return;

    // Read current regime from buy_conds (RegimeDetector publishes here)
    // Adjust to your codebase's actual regime field; placeholder shown.
    int regime_idx = 0;  // ← read from buy_conds->current_regime or similar

    // Sample arm via softmax over weights[regime_idx][...]
    int arm_idx = tt::Bandit_Sample<<Name>State<F>::NUM_ARMS>(
        state->arm_weights[regime_idx],
        cfg->random_seed_per_slow_path);  // or use your own RNG

    state->last_arm_idx[regime_idx] = arm_idx;

    // Periodic persistence
    if (++state->save_counter >= cfg-><name>_bandit_save_interval) {
        state->save_counter = 0;
        // <name>_Bandit_SaveState(state, "data/<name>_bandit_state.json");
    }

    (void)current_price; (void)portfolio_delta; (void)active_bitmap;
}

//======================================================================================================
// [SECTION]_[BUILD PARAMETERS — sharded]
//======================================================================================================
// Use the ARM-SELECTED parameter (state->last_arm_idx[regime] →
// state->arm_thresholds[selected]). Fill out gate parameters with that.
//======================================================================================================
template <unsigned F, unsigned W = 128>
inline void <Name>_BuildParameters(
    const RollingStats<F, W> *rolling,
    const ControllerConfig<F> *config,
    FPN<F> allocated_balance,
    GateParameters<F> *out,
    <Name>State<F> *state)
{
    int regime_idx = 0;  // read from somewhere
    int arm_idx = (state && state->initialized && state->last_arm_idx[regime_idx] >= 0)
                ? state->last_arm_idx[regime_idx]
                : 0;
    FPN<F> selected_threshold = state->arm_thresholds[arm_idx];

    // Compute gate parameters using selected_threshold
    // ... (your strategy logic, parameterized by selected_threshold)
    out->bg_price_threshold   = /* entry price using selected_threshold */;
    out->bg_volume_threshold  = FPN_Mul(rolling->volume_avg, config->volume_multiplier);
    out->sg_take_profit_price = /* TP using selected_threshold */;
    out->sg_stop_loss_price   = /* SL */;
    out->tp_pct               = config->take_profit_pct;
    out->sl_pct               = config->stop_loss_pct;
    out->trade_size           = /* qty */;
    out->flags                = GATE_FLAG_TP_ENABLED | GATE_FLAG_SL_ENABLED;
    out->strategy_id          = STRATEGY_<NAME>;
    (void)allocated_balance;
}

//======================================================================================================
// [SECTION]_[EXIT ADJUST — sharded]
//======================================================================================================
// Same as static template — trail SL via Strategy_WriteRatchetSL etc.
// See DOCS/STRATEGY_TEMPLATE.hpp for pattern.
//======================================================================================================
template <unsigned F, unsigned W>
inline void <Name>_ExitAdjustSharded(
    EventLoopState<F>* state,
    int slot,
    <Name>State<F>* strat_state,
    FPN<F> current_price,
    const RollingStats<F, W>* rolling,
    const ControllerConfig<F>* cfg)
{
    // ... copy from STRATEGY_TEMPLATE.hpp [EXIT ADJUST] section ...
    (void)state; (void)slot; (void)strat_state;
    (void)current_price; (void)rolling; (void)cfg;
}

//======================================================================================================
// [SECTION]_[REWARD UPDATE HOOK — called from drainer post-fill]
//======================================================================================================
// Goes in <Name>_Bandit.hpp (separate file). Drainer's OrderManager_Tick
// post-fill block calls this when a trade closes:
//
//   if (filled_order.strategy_id == STRATEGY_<NAME>) {
//       double reward = filled_order.realized_pnl_pct;  // or another reward
//       <name>_Bandit_Update(strat_state, regime_at_open, arm_at_open, reward);
//   }
//
// Each arm's contribution is the trades that USED that arm. Reward is
// realized P&L (or another scalar — Sharpe contribution, etc.).
//======================================================================================================
template <unsigned F>
inline void <name>_Bandit_Update(<Name>State<F> *state, int regime_idx,
                                   int arm_idx, double reward) {
    if (!state || !state->initialized) return;
    if (regime_idx < 0 || regime_idx >= <Name>State<F>::NUM_REGIMES) return;
    if (arm_idx < 0 || arm_idx >= <Name>State<F>::NUM_ARMS) return;

    // Exp3 update: w[arm] *= exp(eta * reward / weights[arm])
    // Then renormalize row to sum=1
    tt::Bandit_UpdateExp3<<Name>State<F>::NUM_ARMS>(
        state->arm_weights[regime_idx],
        arm_idx,
        reward,
        state->bandit_eta);
}

//======================================================================================================
// [SECTION]_[PERSISTENCE — atomic write + load on boot]
//======================================================================================================
// Goes in <Name>_Bandit.hpp. Mirrors v5.10.0a-final's bandit_state.json
// pattern. JSON format: {"version": 1, "weights": [[r0a0, r0a1, ...], ...]}
//======================================================================================================
template <unsigned F>
inline void <name>_Bandit_SaveState(const <Name>State<F> *state, const char *path) {
    // ... write JSON to <path>.tmp, fsync, rename(<path>.tmp, <path>)
    // (atomic write pattern — engine readers see consistent state)
    (void)state; (void)path;
}

template <unsigned F>
inline void <name>_Bandit_LoadState(<Name>State<F> *state, const char *path) {
    // ... fopen, parse JSON, copy weights into state
    // If file missing or corrupt, leave state at Init defaults (no error)
    (void)state; (void)path;
}

//======================================================================================================
// [SECTION]_[CFG FIELDS NEEDED]
//======================================================================================================
//
// Add to CoreFrameworks/ControllerConfig.hpp:
//
//   FPN<F> <name>_arm_thresholds[<Name>State<F>::NUM_ARMS];  // CSV-parsed
//   double <name>_bandit_eta;                                  // default 0.05
//   int    <name>_bandit_save_interval;                        // default 1000
//
// Defaults:
//   for (int a = 0; a < <Name>State<F>::NUM_ARMS; ++a)
//       cfg.<name>_arm_thresholds[a] = FPN_FromDouble<F>(0.001 * pow(1.5, a));
//   cfg.<name>_bandit_eta = 0.05;
//   cfg.<name>_bandit_save_interval = 1000;
//
// Parser entries:
//   else if (strcmp(key, "<name>_arm_thresholds") == 0) {
//       parse_csv_to_fpn_array(val, cfg.<name>_arm_thresholds, NUM_ARMS);
//   }
//   else if (strcmp(key, "<name>_bandit_eta") == 0) {
//       cfg.<name>_bandit_eta = parse_double_fast(val);
//   }
//   else if (strcmp(key, "<name>_bandit_save_interval") == 0) {
//       cfg.<name>_bandit_save_interval = atoi(val);
//   }
//======================================================================================================
// [END_CODE]
//======================================================================================================
// [DERIVED]   (tool-refreshed at conversion — leave empty; the tools fill it, D-327)
//======================================================================================================
// [END_STRATEGY]_[<Name>]
//======================================================================================================
