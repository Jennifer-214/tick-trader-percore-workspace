# MERGE-SCAN AUDIT — v5.14.9 Post-E (HEAD)
## Date: 2026-05-10

### SCOPE
Post-v5.14.9.E codebase audit for sharing opportunities:
- Repeated atomic loads / clock_gettime calls
- Redundant cfg accesses
- Parallel function bodies that could share helpers
- State-field reuse opportunities
- Specific focus on v5.14.9.F-.I pending cfg boolean consolidation

### KEY FINDINGS

#### 1. CFG BOOLEAN INVENTORY (Engine-wide)

**Currently SCATTERED in ControllerConfig (19 int/uint8_t boolean flags):**

ENTRY/EXIT GATES (3):
- depth_enabled [0/1] — subscribe to order book depth
- gate_ema_enabled [0/1] — EMA gate vs rolling avg
- no_trade_band_enabled [0/1] — cost-aware entry suppression

RISK/MONEY MANAGEMENT (5):
- kill_switch_enabled [0/1] — max loss/DD halt
- vol_sizing_enabled [0/1] — inverse-vol position scaling
- barrier_gate_enabled [0/1] — peak/valley predictor entry block
- ws_dead_time_flatten_enabled [0/1] — WS dead-time emergency close
- param_staleness_gate_enabled [0/1] — parameter staleness hard gate

ML/CONFIDENCE (4):
- confidence_enabled [0/1] — dynamic threshold from IC
- confidence_composite_enabled [0/1] — 4-factor composite (v5.14.1)
- bandit_enabled [0/1] — Exp3-IX regime blending
- exit_bandit_enabled [0/1] — exit prediction bandit

FEATURE/MODEL (4):
- foxml_vol_scaling_enabled [0/1] — VolScaler position sizing
- cost_gate_enabled [0/1] — trade-cost profitability gate
- use_exit_model [0/1] — sell-side ML prediction (v5.13.0)
- lazy_rebuild_enabled [0/1] — skip slow-path on stable regime (v5.12.2.B)

OPERATIONAL (3):
- session_filter_enabled [0/1] — session-aware gate multipliers
- notify_enabled [0/1] — alert notifications
- partial_exit_enabled [0/1] — TP1/TP2 leg splits (currently SPREAD in OrderManager + ControllerConfig)

TOTAL: 19 boolean cfg fields (all currently int type, stored individually)

---

#### 2. CROSS-STRUCT BOOLEAN STATE (v5.14.9.G and .H scope)

**ControllerEventLoop.CoreContext (per-core boolean):**
- partner_pending_active [uint8_t] — pending leg P&L stash (v4.7.21)
  *CONSOLIDATION OPPORTUNITY: .G targets bitmap migration*

**OrderManager.OrderManagerState (engine-wide boolean):**
- partial_exit_enabled [uint8_t] — geometry flag for slot→core mapping
  *Already marked for .F consolidation*

**ShardedSnapshot aggregates (observability booleans):**
- any_scaler_present [uint8_t] — any role's ModelHandle.scaler.has_scaler
- any_scaler_failed [uint8_t] — any role's scaler_load_failed
  *CONSOLIDATION OPPORTUNITY: .H targets summary bitmap migration*

---

#### 3. CLOCK-READ SHARING ANALYSIS

**Clock reads found (std::chrono + system_clock):**
- EngineSharded.hpp: 25 instances (sampled via include-depth grep)
- ControllerEventLoop.hpp: 12 instances
- ShardedSnapshot.hpp: 2 instances (time_t + gmtime_r for session detection)
- BinanceAdapter, Portfolio, OrderManager: 6 total

**Pattern:** Scattered time() / system_clock::now() calls across slow-path cycles.

**Sharing opportunity CLASS:** MODERATE
- Session detection (ShardedSnapshot:line~197) calls time_t every GUI frame (~60Hz)
  → Could cache session hour in state + update on slow-path cadence only
  → Saves ~1ns per GUI paint; low priority
- WS staleness check (ControllerEventLoop CheckWsStaleness) calls clock_gettime
  → Already optimized per cfg.ws_dead_time_flatten_threshold_secs (rare check)
  → No sharing opportunity identified

**Verdict:** Clock reads are already well-isolated per cfg.ws_dead_time_flatten_* pattern.
No immediate hoisting candidates found.

---

#### 4. CFG-ACCESS SHARING ANALYSIS

**Pattern:** ML_BuildParameters, RegimeClassify, and Strategy_BuildParameters (slow-path bodies)
read distinct cfg field groups:

**Confidence + Ladder group (v5.14.9.A-B):**
- cfg->confidence_composite_enabled
- cfg->confidence_enabled
- cfg->confidence_hard_block_threshold
- cfg->risk_degradation_curve (new in .A)
- cfg->risk_full_size_threshold (new in .A)
- cfg->risk_min_size_threshold (new in .A)
- cfg->risk_min_size_pct (new in .A)
→ **Already co-located in ControllerConfig** (lines 494-521)
→ **Already stamp-bound via FOREACH_STAMP_BOUND_CFG** (v5.14.9.C)
→ **No further consolidation benefit**

**Bandit + Ridge group (ML):**
- cfg->bandit_enabled
- cfg->bandit_blend_ratio
- cfg->ridge_within_horizon
- cfg->ridge_across_horizons
- cfg->ridge_lambda
- cfg->ridge_cost_penalty
- cfg->ridge_min_ic_floor
→ **Scattered across ControllerConfig** (lines 590-594, 646-649)
→ **Read together in ML_BuildParameters** (same slow-path cycle)
→ **Opportunity: Could co-locate in struct + use single cache line** (LOW priority; reads per ~100-tick cycle, not hot)

**Gate + Risk group:**
- cfg->depth_enabled, gate_ema_enabled, no_trade_band_enabled, param_staleness_gate_enabled
- cfg->vol_sizing_enabled, cost_gate_enabled, barrier_gate_enabled
→ **Scattered across ControllerConfig** (lines 393-806 range)
→ **Read in different slow-path functions** (RegimeClassify, BuyGate, ExitGate, etc.)
→ **Opportunity: MINIMAL** — already hot-path elided; slow-path reads are 1-3 per 100-tick cycle

**Verdict:** .F and beyond should NOT create a monolithic FOREACH_ENGINE_CFG_FLAG covering all 19.
**NARROW focus (.F as planned: 2 fields) is correct.** Broader consolidation would:
- Create a single large bitmap read per slow-path cycle (1-2 cache misses)
- Force high coupling between unrelated features (bandit, barrier, cost, vol)
- Cache-line false sharing if mixed read/write patterns (e.g., danger gate read-only, but kill_switch updated)

---

#### 5. STATE-FIELD REUSE OPPORTUNITIES

**v5.14.9.G scope (partner_pending_active):**
- Current: uint8_t boolean on CoreContext (1 byte per core, 16 cores max = 16B overhead)
- Opportunity: Pack into bitmap alongside existing per-core state flags
- **Already identified in plan** → migrate to ControllerEventLoop.partner_pending_bitmap uint16_t

**v5.14.9.H scope (any_scaler_present + any_scaler_failed):**
- Current: 2 uint8_t aggregates computed per snapshot copy from zoo aggregation
- Opportunity: Pack into single uint8_t scaler_summary_flags (2 bits used)
- **Already identified in plan** → migrate to ShardedSnapshot.scaler_summary_flags
- Back-compat parser preserves legacy snapshot format

**Latency additions (.B, .B.2, .C) sharing check:**
- .B added slow_state pred cache (1 double per core) — READ-ONLY, no sharing opportunity
- .B.2 added PerCoreSnap state_flags bitmap (1 uint16_t per core) — independent bit patterns per field
- .C added stamp-binding writes (4 new cfg fields) — write-once at config load, zero slow-path cost
→ **No cross-addition clock/cfg read sharing found**

---

#### 6. CROSS-PLAN ADJACENCY (.F-.I scope)

**.F (TECH_DEBT-013(5)): OrderManager.partial_exit_enabled → cfg_flags uint16_t**
- **Currently in:** OrderManagerState (line 313), ControllerConfig (line 371)
- **Scope:** Consolidate these 2 booleans + lat_enabled hot-path gate into engine-wide cfg_flags
- **Decision point:** Broad vs Narrow
  - NARROW (as planned): Just partial_exit_enabled + lat_enabled (2 flags in 16-bit cfg_flags)
  - BROAD alternative: Include all 19 cfg booleans in one FOREACH_ENGINE_CFG_FLAG registry
  - **RECOMMENDATION: STAY NARROW**
    - lat_enabled is a compile-time gate (LAT_ENABLED template bool) + runtime hot-path check
    - Grouping it with config-level booleans creates hot/cold mixing
    - partial_exit_enabled is geometry (infrequently read after boot); cfg_flags is the right home
    - Future .J/K (post v5.14.9) should profile whether bandit_enabled + ridge_* warrant a separate FOREACH_ML_CFG_FLAG
    
**.G (TECH_DEBT-013(6)): ControllerEventLoop.partner_pending_active → bitmap**
- **Currently in:** CoreContext.partner_pending_active (uint8_t, per-core)
- **Plan:** Migrate to ControllerEventLoop.partner_pending_bitmap (uint16_t, max 16 cores)
- **Storage gain:** 1 byte per core → 2 bytes total (16 cores: 16 bytes → 2 bytes)
- **No cfg access involved** (this is transient state)
- **No clock-sharing opportunity**

**.H (TECH_DEBT-013(7)): ShardedSnapshot.any_scaler_* → bitmap**
- **Currently in:** Local uint8_t aggregates during TUI_CopySnapshotSharded
- **Plan:** Cache as ShardedSnapshot.scaler_summary_flags (uint8_t, 2 bits used)
- **Storage gain:** Transient (no heap impact); codegen simplification
- **Back-compat:** Snapshot parser v3 → v3 (no format bump; just logical-bit interpretation)

**.I (v5.14.9.I): Docs + close TECH_DEBT**
- No cfg/clock sharing impact

---

#### 7. SLOW-PATH GATE CACHE REUSABILITY (v5.14.9.B.0 AUTOPOPULATE)

**v5.14.9.B.0 introduced SlowPathGateState (struct with flags bitmap):**
- Populated once per slow-path cycle via SLOW_PATH_GATE_AUTOPOPULATE_PER_CORE
- Reads: cfg.lazy_rebuild_enabled, param_staleness_gate_enabled, ws_dead_time_flatten_enabled, etc.
- **Opportunity:** Could extend SlowPathGateState to cache **all 19 engine-wide cfg booleans** on one slow-path-read cycle

**Cost/Benefit analysis:**
- Benefit: Scatter cfg reads (every strategy, gate, risk fn) → 1 cached read per slow-path cycle
- Cost: SlowPathGateState struct now 19 bits + alignment = ~4-5 bytes per core (current: < 4 bytes)
- Coupling cost: Every gate read now couples to slow-path-gate cache (future feature-gating changes require SLOW_PATH_GATE_AUTOPOPULATE edits)

**Verdict:** DEFER to v5.14.10+ after .F-.H close. Benefit is modest (~10-20ns per slow-path cycle = 0.01% overhead at 100-tick cadence). Not worth increasing coupling pre-paper-test. If v5.14.10 paper-test shows slow-path hotspot at gate reads, resurrection justified.

---

### 8. HIDDEN REUSE OPPORTUNITIES (Non-cfg)

**PerCoreSnap field adjacency (cache locality):**
- ml_confidence_factor (new in .B via ladder) sits adjacent to ml_* cluster ✓ (verified in .B.2 prep)
- No reordering needed

**FOREACH_FEATURE registry reuse (.E → .F+):**
- .E added enabled_bitmap (uint64_t) for feature gating
- .F cfg_flags uses uint16_t (2-4 features max per flag)
- Different semantic granularity; no merge opportunity

**Stamp-bound cfg consolidation (.C):**
- Four new fields added via FOREACH_STAMP_BOUND_CFG (risk_degradation_curve, thresholds x3)
- All read as a group (ladder math), already co-located
- No further bundling opportunity within .C scope

---

### MERGE-SCAN SEVERITY-CLASSIFIED FINDINGS

**CRITICAL:** None. All identified opportunities are ALREADY in the plan.

**HIGH:**
1. Confirm .F stays NARROW (partial_exit_enabled + lat_enabled only); don't attempt monolithic FOREACH_ENGINE_CFG_FLAG yet
   - Broad consolidation now would create hot/cold mixing + future coupling risk
   - Post-paper-test: revisit when we know which features are actually ML-bottleneck-critical

**MEDIUM:**
2. Post-v5.14.9.H, profile slow-path gate cache (SlowPathGateState) for cost/benefit of caching all 19 booleans
   - Only pursue if slow-path gate reads show >1% cycle overhead
   - Deferred to v5.14.10+ planning

**LOW:**
3. Monitor for train-serve parity drift in new stamp-bound cfg fields (.C)
   - 4 new fields (ladder thresholds + curve enum); already in FOREACH_STAMP_BOUND_CFG
   - /parity-check should catch any mismatches at Section L (stale-claims audit)
   - No action needed; covered by existing gate infrastructure

4. ShardedSnapshot clock-read optimization (session hour caching)
   - Current: time_t + gmtime_r every GUI frame (~60Hz)
   - Opportunity: Cache in TUISnapshot, update only on slow-path cadence
   - Cost: Negligible (~1ns saved per frame); LOW priority

---

### RECOMMENDATIONS FOR UPCOMING SUB-SHIPS

**.F (soon):** NARROW consolidation as planned. Validates the principle ("when multiple booleans are truly coupled, bitmap them") without overcommitting.

**.G:** Partner bitmap is disjoint from cfg; no reuse with .F. Proceed as planned.

**.H:** Scaler summary bitmap is observability aggregation (read 1x per snapshot copy). No clock/cfg sharing with .F/.G.

**Post-.I (v5.14.10+ planning):**
1. Profile slow-path latency breakdown per strategy (ML_BuildParameters slowest component?)
2. If gate-read overhead > 1%, extend SlowPathGateState to cache all 19 cfg booleans
3. If bandit/ridge together are always-read, consider FOREACH_ML_CFG_FLAG (separate from general gate flags)

**Config file long-term:**
- Current: 19 scattered booleans + 4 ladder fields (v5.14.9.A-C adds)
- After .F: 16-bit cfg_flags (2 bits used) + 17 scattered booleans still at top level
- Operator UX: No change (cfg file syntax unchanged; internal consolidation only)

---

### CONCLUSION

All major consolidation opportunities identified in the plan (.F, .G, .H) are correctly scoped:
- ✓ .F: NARROW boolean consolidation (partial_exit_enabled + lat_enabled) — DO NOT broaden to all 19
- ✓ .G: Per-core boolean → bitmap — orthogonal to cfg consolidation
- ✓ .H: Observability boolean → bitmap — observability-only, no cache-locality wins

**No missed opportunities** in the critical path. Post-paper-test profiling will guide whether broader consolidation (SlowPathGateState caching all 19) warranted at v5.14.10+.

