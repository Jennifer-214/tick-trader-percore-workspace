# /plan-check downstream re-audit — v5.14 sub-plans after v5.14.1 close — 2026-05-09

**Scope:** /plan-check on v5.14 master + remaining sub-plans (.2 through .12)
following the v5.14.1 sub-sprint close.

**HEAD:** f973b5c (v5.14.1.F close; .G in audit)
**Tests:** 2212/0
**Trigger:** /readiness Check 22 (auto-trigger after umbrella ships
touching shared surfaces). v5.14.1 touched 7 shared surfaces.

---

## EXECUTIVE SUMMARY

**OVERALL VERDICT: YELLOW → GREEN** with <1 hour code-time fixes total.

8/10 sub-plans ready to code immediately. 2/10 YELLOW with bounded fixes:
- v5.14.7 maker MVP: BookSnapshot field wiring (~15 min)
- v5.14.8 stale gating: FOREACH_FEATURE X-macro verification gate (~30 min)

**No blocking architectural breaks.** All shared-surface changes
from v5.14.1 land cleanly into downstream plans.

---

## v5.14.1 surfaces touched (re-audit basis)

1. FOREACH_STAMP_BOUND_CFG registry (13 entries; B.3, D, E)
2. STAMP_CFG_AUTOPOPULATE companion macro (B.3.E.B)
3. FOREACH_IC_VARIANT registry (1 entry; F)
4. ConfidenceScorer struct (extended A; constrained F — no further struct fields)
5. FeatureStandardizer struct (winsor block; D)
6. EnsembleModelZoo struct (exit_ridge_state + exit_reward_ring; E)
7. CoreContext / EventLoopState (turnover field; G in flight)

---

## Per-plan verdicts

| Sub-plan | Verdict | Notes |
|---|---|---|
| v5.14.2 hot-swap ensemble | **PASS** | Atomic Free/Init/Load handles all new EnsembleModelZoo fields generically |
| v5.14.3 fingerprint binding | **PASS** | Surface G overlay non-intrusive; no FOREACH_STAMP_BOUND_CFG conflict |
| v5.14.4 multi-mode reconciliation | **PASS** | OMS-only; orthogonal to ML surfaces |
| v5.14.5 CS targets + regime + frac diff | **PASS** | FOREACH_TARGET append; LABEL_REGISTRY_HASH bump coordinated; price_buf available |
| v5.14.6 bug-check skill | N/A | Meta-tool; no engine code surfaces |
| **v5.14.7 maker MVP** | **YELLOW** | Plan assumes `book_snap.best_bid` named field; actual is `bids[0].price` array index. ~15 min fix in plan |
| **v5.14.8 stamp lineage + stale gating** | **YELLOW** | FOREACH_FEATURE row signature change (6→7 cols); hash-compute X-macro must exclude new col to preserve FEATURE_REGISTRY_HASH. ~30 min code-review verification gate |
| v5.14.9 soft risk degradation | **PASS** | Composite confidence wiring clean; reads ConfidenceScorer_ComputeComposite which now functional end-to-end (PARITY-001/002/003 closed) |
| v5.14.11 Bayesian Thompson | **PASS** | Parallel bandit; cfg-isolated; no Ridge cross-interference |
| v5.14.12 online corr matrix | **PASS** | Incremental optimization; external interface preserved |

---

## Critical findings (per Class checks)

### Class 14 (Function/struct signatures)
All downstream plans audit clean. v5.14.1.E Spearman IC drift detection
refactor is a LOCAL change at one call site (ControllerEventLoop.hpp:~1314);
no signature break to v5.14.9 or later plans.

### Class 17 (Deferrals based on stale beliefs)
- ✅ STAMP_CFG_AUTOPOPULATE macro now EXISTS (v5.14.1.B.3.E.B) — v5.14.3
  + v5.14.8 can leverage for new stamp fields
- ✅ FOREACH_FEATURE row extension pattern VERIFIED — v5.14.8 correctly
  gates FEATURE_REGISTRY_HASH via X-macro body inspection
- ✅ RollingStats.price_buf[W=128] CONFIRMED available (v5.14.5.C frac
  diff IN scope, not deferred — Class 17 catch from earlier session held)
- ✅ ModelHandle flat-field structure VERIFIED (v5.14.8 author caught
  the gap pre-coding; training_timestamp_us direct access)

### Class 18 (Mirror patterns)
v5.14.1.E introduces `exit_ridge_state` + `exit_reward_ring` mirrors of
buy-side. v5.14.12 reads buy-side only (no conflict); v5.14.11 (Thompson)
defers exit-side mirror to v5.15 (acceptable — caught in plan; not
silent-defer). Design extensible.

---

## Cross-plan integration matrix

### Shared surfaces validation

1. **ConfidenceScorer struct:** Extended A/E/F; v5.14.9 consumes
   `ConfidenceScorer_ComputeComposite` directly. ZERO new fields expected
   by other plans. ✅ PASS

2. **FeatureStandardizer struct:** v5.14.1.D adds winsor block;
   v5.14.8.B adds scaler_fit_data_hash. NO CONFLICT — separate concerns;
   sidecar versioning handles both. ✅ PASS (v5.14.8 should bump
   SCALER_MAGIC again or use forward-compat appending)

3. **EnsembleModelZoo struct:** v5.14.2 atomic hot-swap (Free/Init/Load)
   touches all fields generically. v5.14.12 reads buy-side reward_ring
   only. NO CROSS-REFERENCE CONFLICTS. ✅ PASS

4. **Stamp body (Surface G):** v5.14.1 (winsor) + v5.14.3 (overlay) +
   v5.14.8 (scaler-fit, removal-reasons, environment-meta) all use
   `has_*` flag pattern. CANONICAL-ORDER LOCKED. ✅ PASS; HMAC stable.

5. **Cfg fields (no namespace collisions):**
   - v5.14.1: confidence_* (15 fields)
   - v5.14.7: maker_* (5 fields)
   - v5.14.9: confidence_degradation_* + confidence_min_* (4 fields,
     distinct from confidence_composite_*)
   - v5.14.11: bandit_algorithm, thompson_* (5 fields)
   - v5.14.12: ridge_online_corr (1 field)
   ZERO COLLISIONS. ✅ PASS

6. **Registries:**
   - FOREACH_STAMP_BOUND_CFG (13 entries): v5.14.3 + v5.14.8 both read;
     neither reorder ✅
   - FOREACH_IC_VARIANT (1 entry): extensible to Pearson/Kendall in
     v5.15+ ✅
   - FOREACH_TARGET (6 → 9 post-v5.14.5): append-only ✅
   - FOREACH_FEATURE (row signature extends in v5.14.8; hash-compute
     isolated): **REQUIRES VERIFICATION GATE** ⚠️

---

## Blocking issues (must fix before coding)

### Issue 1: v5.14.7 BookSnapshot field wiring (YELLOW)

- **Plan assumes:** `book_snap.best_bid` / `book_snap.best_ask` named fields
- **Actual struct** (`DataStream/BinanceDepth.hpp:29`): `bids[5]`,
  `asks[5]` with index-0 = top-of-book
- **Fix:** Replace with `book_snap.bids[0].price` / `asks[0].price` in
  Step 3 (slow-path body)
- **Effort:** ~15 minutes during coding
- **Verdict:** PASS after wiring adjustment

### Issue 2: v5.14.8 FOREACH_FEATURE X-macro verification gate (YELLOW)

- **Change:** Row signature from 6 columns → 7 (add `max_staleness_minutes`)
- **Requirement:** All 5 X-macro call-sites MUST update macro definition
  to 7 params
- **CRITICAL:** Hash-compute body MUST still read only (id, name, version,
  enabled) — skip new column to preserve FEATURE_REGISTRY_HASH
- **Code-review gate:** Verify all 5 sites + hash-compute caller align
  before shipping
- **Effort:** ~30 minutes spot-check at code review
- **Impact:** FEATURE_REGISTRY_HASH preservation (staleness is runtime
  config, not training invariant)
- **Verdict:** PASS after verification gate

---

## Opportunities (non-blocking)

1. **STAMP_CFG_AUTOPOPULATE adoption** — v5.14.3 + v5.14.8 use Surface G
   `has_*` flags + manual populator. Acceptable, but future plans should
   leverage the macro for cfg-bound fields (1-line registry add vs N-site
   manual). Flag for v5.15+ retrain refactor.

2. **FOREACH_IC_VARIANT roadmap** — v5.14.1.F establishes registry; future
   Pearson + Kendall slot in cheaply. No blocking constraint today.

3. **Exit-side Ridge online optimization** — v5.14.12 optimizes buy-side
   correlation matrix. When exit-side Ridge needs the same treatment
   (post-v5.14.1.E), mirror Welford-style incremental update pattern for
   consistency. Design note for v5.14.12.C code comments.

---

## Codebase drift audit (sample verification)

| Claim | Verified | Location |
|---|---|---|
| FOREACH_STAMP_BOUND_CFG exists | ✅ | v5.14.1.B.3 introduces; 13 entries |
| STAMP_CFG_AUTOPOPULATE exists | ✅ | v5.14.1.B.3.E.B refactor |
| FOREACH_IC_VARIANT exists | ✅ | v5.14.1.F (1 entry) |
| RollingStats.price_buf[W=128] | ✅ | ML_Headers/RollingStats.hpp:90 |
| BookSnapshot.bids/asks arrays | ✅ | DataStream/BinanceDepth.hpp:29 |
| EnsembleModelZoo_LoadFromCfg signature | ✅ | ML_Headers/CoreModelZoo.hpp:~1248 |
| Health_LogCriticalRateLimited | ✅ | MemHeaders/HealthLog.hpp:319 |

**Zero codebase drift.** All claimed dependencies resolve.

---

## Final verdict + recommendations

**OVERALL: YELLOW → GREEN with bounded fixes**

8/10 sub-plans ready to code immediately. 2/10 YELLOW with <1h code-time
fixes:
- v5.14.7: BookSnapshot field wiring (~15 min)
- v5.14.8: FOREACH_FEATURE X-macro verification gate (~30 min)

**No blocking architectural breaks.** All shared surfaces (3 new
registries + 4 struct extensions) audit clean:
- ✅ Surface G discipline preserved across stamp body extensions
- ✅ No snapshot fwrite/fread structural changes (Class 4 avoided)
- ✅ Dependency DAG acyclic
- ✅ No cfg field name collisions
- ✅ No silent registry reorder conflicts

**Recommended shipping sequence:** Continue v5.14.1 close (.G ship +
post-mortem) → Phase 2 (v5.14.2 → v5.14.5 → v5.14.9) → Phase 3
(v5.14.3 + v5.14.8) → Phase 4 (v5.14.7 maker) → Phase 5 (v5.14.11 +
v5.14.12) per master plan ordering.

---

**Saved 2026-05-09 by /plan-check downstream re-audit per /readiness
Check 22 (auto-trigger after umbrella ships touching shared surfaces).**
