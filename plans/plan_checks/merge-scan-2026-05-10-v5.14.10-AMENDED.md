# /merge-scan re-audit — v5.14.10 AMENDED — 2026-05-10

**Target plan:** `plans/v5.14-foxml-port-and-maker/subplans/2026-05-10-v5.14.10-bayesian-thompson-bandit.md`
**Prior report:** `plans/plan_checks/merge-scan-2026-05-10-v5.14.10-thompson-bandit.md`
**Verifies against:** HEAD (post-v5.14.9 umbrella `b09b2d5`)

---

## Verdict

**GREEN.** All 3 prior recommendations correctly absorbed at the right sub-tags. No duplication introduced. 2 NEW MEDIUM-priority opportunities surfaced by the .0 + .D scope expansion (one is a deferral candidate worth queueing; the other is a DESIGN_SPECS consolidation question for Caramel). No changes required to ship coding as planned.

---

## Prior-recommendation closure status

| Prior rec | Sub-tag landed | Plan citation | Status |
|---|---|---|---|
| **T1 — FOREACH_ENSEMBLE_POST_LOAD extension (HIGH)** | `.C` Step 5 | plan lines 228-233 (2 entries: `init_thompson_bandits`, `load_thompson_state`); +1 update at `.B` Step 4 (`initialized_thompson_bandits` flag) + `.C` Step 6 (`_IsReadyForInference` predicate) | **CORRECTLY LANDED.** Same shape as v5.14.2.E.1 close (PARITY-009/010/011/012). Boot/backtest/hot-swap inherit Thompson init+load via registry walk; mirror prevention enforced. Plan's pre-existing-work audit at line 59 cites `FOREACH_ENSEMBLE_POST_LOAD at CoreModelZoo.hpp:2088-2104 (7 entries today; +2 for Thompson)` — accurate against HEAD (HEAD shows count=7 at line 2107). |
| **T4 — tt::json_io extraction (MEDIUM)** | `.C` Step 1 | plan lines 219-220 ("Extract `Bandit_JsonFindKey` / `Bandit_JsonParseDoubleArray` / `Bandit_JsonParseIntArray` to `tt::json_io` namespace at `BanditLearning.hpp:440/455/473` (~15 min; merge-scan T4 free win)") | **CORRECTLY LANDED.** Sub-tag .C Step 1 matches T4 spec exactly. Effort estimate matches (~15 min). Pre-existing-work audit at line 65 cites the source primitives. Future ridge_state / scaler_state / future-N persistence reuse foreshadowed. |
| **M2 — FOREACH_CALIB_LOG_COL ABSORB (MEDIUM, decision-required)** | `.D` Steps 3-7 | plan lines 257-272 (registry definition + writer auto-extends + DESIGN_SPECS doc + TECH_DEBT-010 close) | **CORRECTLY LANDED with DECISION FLIPPED to STRUCTURAL-NOW.** Original M2 verdict was "ABSORB ad-hoc cheaper but RECOMMEND ASK CARAMEL"; amendment chose structural per CLAUDE.md item 19 + cfg=2 telemetry adds 5 cols (≥3 trigger). DESIGN_SPECS doc `calibration-log-column-registry.md` queued in Step 7. Closes TECH_DEBT-010. |

---

## Verifying NO duplication introduced

### ThompsonBanditState vs BanditState

Field-by-field check against the plan's struct definition (lines 137-148) + existing BanditState (`BanditLearning.hpp:60-100` shape):

| Thompson field | Bandit field | Same shape? | Same semantic? | Status |
|---|---|---|---|---|
| `mu_post[N]` | `weights[N]` | both double[N], same width | NO — Thompson is posterior mean (Gaussian conjugate); Exp3 is exponential weight (-eta * cumulative reward) | **DISTINCT** |
| `precision_post[N]` | (none) | new | new | DISTINCT |
| `total_pulls[N]` | `pulls[N]` | both uint32_t[N] | NO — Thompson tracks Bayesian observation count per arm (drives variance shrinkage); Exp3 tracks selection count per arm (drives mixing weight under IX). Mathematical role is different even though underlying counter is identical. **Plan deliberately uses `total_pulls` (not `pulls`) name to mark the semantic divergence.** | DISTINCT-by-name |
| `n_arms` | `n_arms` | same | same — both = ezoo->primary_count | mirror-of-shared-source (see S2 in prior report; intentional) |
| `mu_prior` / `precision_prior` / `precision_obs` | (none) | new | Bayesian hyperparams; no Exp3 analog | DISTINCT |
| `rng_state` | (none) | new | Thompson-only (Exp3 deterministic) | DISTINCT |

**Conclusion:** ThompsonBanditState is JUSTIFIED-NEW; field overlap with BanditState is intentional + semantically distinct. Plan's per-field naming preserves the distinction. Per-state-type Save/Load divergence (T4 partial reuse only at primitive level) is correct shape.

### thompson_state.json vs bandit_state.json

- bandit_state.json schema: `regime_id`, `weights[]`, `pulls[]`, `cum_reward[]`, `arm_names[]`, `total_steps` (per BanditState shape)
- thompson_state.json schema (per plan line 222-226): `format_version`, locale-pinned `mu_post[]`, `precision_post[]`, `total_pulls[]`, `mu_prior`, `precision_prior`, `precision_obs`, `rng_state` (hex)

**Field overlap:** ZERO meaningful. `total_pulls` vs `pulls` widths match but values diverge (different update-rule semantics). Each file is the canonical posterior persistence for its own algorithm. **No duplication.**

### thompson_state byte (PerCoreSnap bit-pack) vs other state bytes

Per `.D` Step 1 (plan line 247-251):
```
bit 0:    thompson_bandit_active
bits 1-3: thompson_chosen_arm (0-7)
bits 4-7: reserved
```

Cross-checked against existing PerCoreSnap state bytes:
- `state_flags` (uint16_t at line 1106): per-core engine state (PERMISSION_ALLOWED, IS_ML, ML_MODEL_LOADED, LADDER_BOTTOM_HIT, etc.) — different semantic concern (engine state, not algorithm state)
- `failure_flags` (uint16_t at line 1098): observability failure modes (ml_model_load_failed, ml_scaler_load_failed) — different semantic concern (errors, not algorithm choices)

**Could thompson_state bit 0 (`thompson_bandit_active`) live in `state_flags` instead of a new byte?** Field-test: `state_flags` has 7 bits used / 9 bits free per plan line 1106 + FOREACH_PER_CORE_STATE_FLAG inventory. Adding `STATE_FLAG_THOMPSON_ACTIVE` is feasible (1 row to FOREACH_PER_CORE_STATE_FLAG).

**HOWEVER:** the plan's design pairs `thompson_bandit_active` with `thompson_chosen_arm` (3 bits) — they are semantically coupled (chosen_arm is meaningful only when active=1) AND they're both bandit-algorithm-runtime-output (vs state_flags being engine-state-categorical). Splitting them would make state_flags-walkers iterate a heterogeneous mix. Plan's grouping = correct per-snapshot-cluster-layout-pattern.md (cluster by concern, not by storage type).

**Conclusion:** thompson_state byte is JUSTIFIED-NEW; not a duplication of state_flags. Bit-packing within the byte is the correct choice (3 bits chosen_arm + 1 bit active = 4 bits used + 4 bits headroom for future Thompson telemetry like "arm_was_explore"=bit 4).

---

## NEW merge candidates from .0 + .D scope expansion

### N1 — ML telemetry fields scattered across PerCoreSnap; .0 audit will resolve (PRIORITY: HANDLED-BY-DESIGN)

The .0 sub-tag explicitly does this audit (plan lines 122-128). Spot-survey of HEAD's PerCoreSnap (EngineTUI.hpp:980-1198) shows ML telemetry IS scattered across multiple regions:

- **Bandit/ensemble cluster** (lines 1184-1196): `ensemble_active`, `ensemble_n_horizons`, `ensemble_horizon_ticks[8]`, `ensemble_last_predicted_regime`, `ensemble_last_predicted_horizon_idx`, `ensemble_weights[5][8]`, `ensemble_n_updates_per_regime[5]`, `ensemble_blend_mode[16]`, `ensemble_disabled_horizon_mask` — currently the largest related ML cluster
- **Confidence/prediction cluster** (lines 1062-1080): `ml_last_prediction`, `ml_last_confidence`, `ml_confidence_ic`, `ml_confidence_rmse`, `ml_portfolio_turnover`, `ml_active_prediction`, `ml_confidence_factor` (ladder)
- **Threshold cluster** (lines 1107-1110): `ml_last_threshold`, `ml_last_effective_threshold`, `ml_nan_feature_events`, `ml_nan_prediction_events`
- **Sell-side cluster** (lines 1088-1089): `ml_last_exit_prediction`, `ml_last_exit_dominant_horizon`
- **Scaler cluster** (lines 1119-1128): `warmup_progress_pct`, `ml_scaler_present`
- **Drift cluster** (lines 1160-1163): `drift_breached`, `drift_kill_tripped`, `drift_n_samples`, `drift_avg_ic`
- **Cfg drift cluster** (lines 1132-1134): `cfg_drift_tier1_count`, `cfg_drift_tier2_count`, `cfg_drift_strict_refused`

**Question for .0 design:** should ALL ML telemetry consolidate into ONE alignas(64) ML cluster, or should sub-clusters (bandit / confidence / threshold / drift / etc.) each get their own alignas(64) block?

**Recommendation: SUB-CLUSTERS, NOT ONE-MEGA-CLUSTER.** Reasoning:
- Different sub-clusters have different write cadences (bandit weights = per slow-path cycle; threshold = per ML decision; drift = per drift-detector pass which is rarer; cfg drift = boot-only, never re-written)
- Different read patterns at the GUI side (panels read different sub-clusters)
- Cross-thread invalidation cost per cluster is dominated by the WRITE cadence; mixing rare-write fields with frequent-write fields wastes cache invalidations on the read side
- Per CLAUDE.md item 20 trade-off note: "cache-line awareness for shared bitmaps" — same applies to scalar clusters

The `.0` Step 1 ("identify ML telemetry fields by concern") + Step 2 ("design unified cluster layout per concern") — plan ALREADY says "per concern", which matches sub-cluster recommendation. Confirming the plan's reading is correct.

**This is a DESIGN INPUT to .0, not a new MERGE OPPORTUNITY.** The Thompson cluster is one of N (where N = ~5-7 sub-clusters) ML clusters that should be alignas(64)-aligned. .0's DESIGN_SPECS doc should articulate the "cluster by concern, not by storage" principle.

### N2 — Other CSV writers with the same sister-literal pattern (PRIORITY: MEDIUM, queue as TECH_DEBT)

The amendment closes TECH_DEBT-010 for the calibration log only. Verified via codebase scan that 2+ OTHER CSV writers exist with the same sister-literal pattern:

| Writer | Header literal | Body fprintf | Sister-literal drift risk |
|---|---|---|---|
| `MetricsLog` (`DataStream/MetricsLog.hpp`) | line 51-57 (~24 columns) | line 115-121 (`MetricsLog_SlowPath`) + 155-158 (`MetricsLog_Event`) | HIGH — 2 body sites both reference 24-column header |
| `ShardedTradeLog` (`CoreFrameworks/ShardedTradeLog.hpp`) | line 119 (~11 columns) | line 209-218 (`_RecordEntry`) + 248-259 (`_RecordExit`) | HIGH — 2 body sites both reference 11-column header |

**This is the same class of bug TECH_DEBT-010 captures, just at 2 more sites.** Per CLAUDE.md item 19 (structural fix preferred when bug class can recur):

If the FOREACH_CALIB_LOG_COL pattern is field-tested in v5.14.10.D + the DESIGN_SPECS doc generalizes the approach, the natural follow-up is:
1. Generalize the pattern as `FOREACH_<LOGNAME>_COL` (same shape, applied 3x: calib_log, metrics_log, trade_log)
2. Each writer auto-generates header + body via X-macro walks
3. Adding a column to ANY of them = 1 row in the relevant FOREACH_X_COL

**Recommendation: DO NOT extend v5.14.10.** v5.14.10.D ships ONE registry as documented. After Caramel field-tests the pattern + the DESIGN_SPECS doc lands, this becomes a candidate sub-ship for v5.14.11+ or the v5.14 cleanup pass. **Auto-write to TECH_DEBT.md as a new entry** per CLAUDE.local.md going-forward rule:

```
TECH_DEBT-NEW: Generalize FOREACH_CALIB_LOG_COL pattern to MetricsLog + ShardedTradeLog
- Cost: ~3-4h (per-writer registry definition + writer rewrite + tests; already-validated pattern from v5.14.10.D)
- Trigger: next ship that ADDS a column to MetricsLog OR ShardedTradeLog (currently rare; both stable for months)
- Cross-ref: TECH_DEBT-010 (closed in v5.14.10.D) + DESIGN_SPECS calibration-log-column-registry.md
- Severity: LOW (drift hasn't caused a bug in either log yet); MEDIUM if the pattern's value justifies preemptive application
```

Not a v5.14.10 amendment — separate sub-ship candidate.

### N3 — DESIGN_SPECS consolidation question for per-snapshot-cluster-layout-pattern.md (PRIORITY: LOW, document-architecture)

The `.0` Step 4 plans a NEW DESIGN_SPECS doc `per-snapshot-cluster-layout-pattern.md`. Existing DESIGN_SPECS docs in `~/code/tick-trader-percore-workspace/DESIGN_SPECS/`:
- `bitmap-flag-api.md` — bit-packed flag storage (CLAUDE.md item 20)
- `heterogeneous-registry-pattern.md` — scope column vs domain split for registries
- `transient-aggregation-bitmap-pattern.md` — adjacent (already exists)

**Question:** does `per-snapshot-cluster-layout-pattern.md` warrant its own doc, or does it consolidate into existing docs?

**Field check:**
- `bitmap-flag-api.md` covers WITHIN-WORD bit-packing, NOT struct-field clustering across cache lines. Different scope.
- `heterogeneous-registry-pattern.md` covers REGISTRY-shape decisions (column vs split), NOT struct-field clustering. Different scope.
- The cluster pattern is a SHARED concern across snapshot/state/cfg structs (PerCoreSnap is one of N candidate structs; CoreContext + EventLoopState + EnsembleModelZoo all have similar layout decisions ahead).

**Recommendation: STANDALONE DOC, with cross-refs.** Same cross-reference convention as other DESIGN_SPECS docs. Should articulate:
1. Cluster by concern (write cadence + read pattern + invalidation cost), NOT by storage type
2. alignas(64) per cluster boundary; arrays-first reorder eliminates middle padding
3. Cross-thread invalidation analysis (writer cadence × reader cadence × cluster size)
4. Decision tree: "should this new field go in existing cluster X or new cluster Y?"
5. Cross-refs: bitmap-flag-api.md (when adding a flag inside a cluster), heterogeneous-registry-pattern.md (when adding a registry-driven cluster)

Plan's .0 Step 4 already says "methodology + decision tree for clustering decisions + cross-references to TECH_DEBT-011 + CLAUDE.md item 12" — matches. **No amendment needed; flagging as DESIGN_SPECS catalog placement question for Caramel awareness.**

### N4 — Bit-pack opportunities beyond thompson_state byte (PRIORITY: LOW-DEFER, no strong byte-triple targets in scope)

Surveyed PerCoreSnap for unrelated 2-3-field byte triples that should also bit-pack per CLAUDE.md item 20:

| Candidate triple | Storage today | Bit-pack candidate? | Recommendation |
|---|---|---|---|
| `cfg_drift_tier1_count` + `cfg_drift_tier2_count` + `cfg_drift_strict_refused` (line 1132-1134) | 3× uint8_t (3 bytes) | NO — counts (1-tier1, 2-tier2) need ≥4 bits each; refused is 1 bit. Total 9-10 bits. Could pack into uint16_t but saves only 1 byte vs 3. Not worth the BITMAP_* indirection at boot-only read site. | LEAVE ALONE |
| `ml_scaler_present` (line 1128) — single uint8_t | 1× uint8_t | NO — already migration target (see line 1120-1128 comment); the SISTER `ml_scaler_load_failed` was migrated to `failure_flags` BIT_FLAG. `ml_scaler_present` was kept separate because it's a STATE flag (not failure). Could move to `state_flags` BIT_FLAG. | DEFER — separate refactor concern; not v5.14.10 scope |
| `drift_breached` + `drift_kill_tripped` (line 1160-1161) — 2× uint8_t | 2× uint8_t | YES candidate — both are 1-bit booleans; could move to `state_flags` BIT_FLAG (currently 7/16 used → 9 bits free) | TECH_DEBT candidate — same migration class as v5.14.9.B.2 (ml_scaler_load_failed → failure_flags). DEFER. |
| `core_kill_tripped` (line 1155) — single uint8_t | 1× uint8_t | YES — 1-bit boolean; migration target | TECH_DEBT candidate |

**Recommendation: NO additional bit-packing in v5.14.10.** The thompson_state byte adds NEW packed fields (correct shape for new fields, no migration concern). The above migration candidates are SEPARATE from Thompson scope; bundling them into v5.14.10 would dilute the ship's focus. **Auto-write 1 TECH_DEBT entry** to capture the inventory for a future TECH_DEBT-013-style sweep (the v5.14.9.H ship that closed scaler aggregation flags is the canonical precedent).

```
TECH_DEBT-NEW: PerCoreSnap byte-per-bool migration sweep (post-Thompson)
- Targets: ml_scaler_present, drift_breached, drift_kill_tripped, core_kill_tripped (all uint8_t booleans)
- Cost: ~1-2h (each = 1 row to FOREACH_PER_CORE_STATE_FLAG + reader-site rewrite via STATE_FLAG_IS_SET + writer-site rewrite via STATE_FLAG_SET/CLR + tests)
- Trigger: any further state-flag additions OR a v5.14.9.H-style sweep
- Cross-ref: v5.14.9.B.2 (PerCoreStateFlagsRegistry) + v5.14.9.H (TECH_DEBT-013(7)) + CLAUDE.md item 20
- Severity: LOW (each is correct as-is; migration is for consistency, not bug fix)
```

---

## Atomic load redundancies — none flagged

Thompson is per-core slow-path-only state. No new atomic loads introduced. Same conclusion as prior report.

## Clock-read redundancies — none flagged

Thompson_Sample uses mt19937_64; doesn't read clock. The `.C` Step 4 (TECH_DEBT-027 opportunistic locale fix at `Bandit_SaveJSON`) doesn't add clock reads. Same conclusion as prior report.

## Cfg-access redundancies — none flagged

Plan adds 5 cfg fields read at well-defined sites (parser, populator, dispatch). `cfg.bandit_algorithm` = single read per ML cycle. No 5+-times-in-function pattern. Same conclusion as prior report.

## Branch-vs-branchless flags — none flagged

Slow path; bandit_algorithm static-after-boot. Same conclusion as prior report.

---

## Overall recommendation

### Top-3 highest-impact items

1. **No amendment-required action.** All prior recs correctly absorbed; no new HIGH-priority opportunities. Coding can start on .0.

2. **Ship awareness for Caramel — N1 cluster decision in .0:** confirm "sub-clusters by concern" (NOT one-mega-cluster) as the .0 design principle. Plan reads this way already; this is verification-not-amendment.

3. **Auto-write 2 TECH_DEBT entries** (per CLAUDE.local.md going-forward rule for deferred items):
   - **TECH_DEBT-NEW (N2):** generalize FOREACH_<LOGNAME>_COL pattern to MetricsLog + ShardedTradeLog (post-v5.14.10.D pattern field-test)
   - **TECH_DEBT-NEW (N4):** PerCoreSnap byte-per-bool migration sweep (ml_scaler_present + drift_breached + drift_kill_tripped + core_kill_tripped)

### Items to leave alone

- ThompsonBanditState fields vs BanditState fields — semantically distinct, plan-naming preserves distinction
- thompson_state byte vs state_flags / failure_flags — distinct concern, correct grouping
- Plan's existing structural choices (registries, AUTOPOPULATE, persistence, dispatch, slow-path gates) — all match precedent
- per-snapshot-cluster-layout-pattern.md as standalone DESIGN_SPECS — correct scope, doesn't consolidate into existing docs

### No-changes verdict on plan

The amendment correctly absorbed all 3 prior recommendations at the right sub-tags with the right shape. The 2 NEW opportunities (N2, N4) are explicitly scoped OUT-OF-PLAN as separate TECH_DEBT entries. N1 is a verification of plan-design-intent, not an amendment. N3 is a documentation-architecture flag for awareness.

**Plan ships as-amended.** Auto-write 2 TECH_DEBT entries to ledger; coding starts on .0.

---

## Audit-write contract (per CLAUDE.local.md going-forward rule)

This skill ran in audit-only mode; TECH_DEBT entries N2 + N4 are CANDIDATES, not auto-written by the skill. Operator (Caramel) reviews + agent writes via main session if approved.
