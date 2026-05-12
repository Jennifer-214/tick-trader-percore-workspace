# /readiness report — v5.15.5 per-horizon TP/SL serving — 2026-05-12

## Plan summary
- 4 phases (A: load wire-up + cache-tight-pack, B: mode dispatch + shadow, C: cfg-drift Tier 1, D: backward-compat + tests + docs)
- Plus bandled cache-layout finding: bandit arm_names extraction (~50-80 LOC; closes v5.14.10 known issue)
- Total estimated effort: ~250-300 LOC code + ~80 LOC tests/docs
- Branch: feat/v5.15-live-readiness (stay)
- Sub-tags: v5.15.5.A (load + cache-pack), .B (dispatch + shadow), .C (Tier 1), .D (umbrella)
- DESIGN_SPECS doc: per-horizon-barrier-blending-with-shadow-mode.md (created 2026-05-12)

## Checklist verdicts

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | ✅ PASS | Hot path UNCHANGED. All resolution in slow-path ML_BuildParameters. params->tp_pct seqlock-published as before. |
| 2 | Train-serve parity | ✅ PASS | Plan ADDS parity surface (per-arm barriers) via stamp body (already records label_tp_pct/sl_pct). Cfg-drift Tier 1 promotion in Phase C closes the gap. |
| 3 | Surface area | ✅ PASS | 4 files touched (CoreModelZoo.hpp, StrategyParameters.hpp, BarrierBlendModeRegistry.hpp NEW, ControllerConfig.hpp); +tests + docs. Plus bandit cache fix = 1 more file. No `if(engine_arch)` proliferation. |
| 4 | Pointer init / heap lifecycle | ✅ PASS | No new heap. Tight-pack array is inline in EnsembleModelZoo. Shadow ring is inline + alignas(64). |
| 5 | Backward compat | ✅ PASS | LEGACY mode (default) preserves pre-v5.15.5 bytewise behavior. Pre-v5.15.5 stamps fall back via has_label_params=0 sentinel. MODEL_FORMAT_VERSION unchanged. |
| 6 | Multi-threading | ✅ PASS | Single-writer ezoo (slow-path); seqlock for hot-path handoff (no change). Shadow ring head: atomic ACQ/REL + explicit alignas(64) padding to prevent false sharing with records[]. |
| 7 | Test coverage | ✅ PASS | Per-mode unit tests (5 modes); shadow determinism; cache layout static_asserts; Tier 1 strict refuse; AUTOPOPULATE round-trip. |
| 8 | Docs + invariants | ✅ PASS | DESIGN_SPECS doc + CHANGELOG + HOT_PATH_CHANGELOG + PARITY_LIFECYCLE + FEATURE_LOOKUP + PARITY_ISSUES-024 + bandit cache fix HOT_PATH_CHANGELOG entry. |
| 9 | Forward maintenance | ✅ PASS | FOREACH_BARRIER_BLEND_MODE registry (CLAUDE.md item 13). Adding 6th mode = 1 row. Bandit arm_names extraction same family. |
| 10 | Rollback story | ✅ PASS | Per-phase tags: pre-v5.15.5.A through pre-v5.15.5; LEGACY default mode = trivial revert via cfg flip. |
| 11 | Architectural sprint | ✅ PASS | Not an architectural refactor. Boundary-stable per CLAUDE.local.md rule (params->tp_pct interface preserved). |
| 12 | Display ↔ execution | ✅ PASS | MLStatusPanel reads same per_arm_barriers source the slow-path uses (single source of truth). |
| 13 | Strategy lifecycle | n/a | Doesn't touch strategy registry. |
| 14 | X-macro dispatch | ✅ PASS | New FOREACH_BARRIER_BLEND_MODE uniform compute-fn signature; loop test + count assertions. |
| 15 | ML feature change | n/a | No feature pipeline changes. FOREACH_FEATURE untouched. |
| 16 | New cfg w/ stamp | ✅ PASS | barrier_blend_mode lands in FOREACH_STAMP_BOUND_CFG via AUTOPOPULATE; recipe doc update needed (Phase D). |
| 17 | Model-load path | ✅ PASS | TryLoadRole gets per-arm barrier copy step; strict-mode refuse path inherited via cfg-drift Tier 1. PerCoreSnap surface for failure visibility (Phase B Step 2). |
| 18 | Reuse audit | ✅ PASS | Reuses weights_buf[] from prediction blend; reuses STAMP_BOUND_CFG AUTOPOPULATE; reuses FOREACH X-macro pattern from v5.13.5. |
| 19 | Pre-existing-work audit | ⚠️ AMENDED (see findings below) | Per-arm barriers ALREADY on ModelHandle via stamp; FALSE-NEW caught. Plan revised. |
| 20 | Future-proofness | ✅ PASS | FOREACH registry handles N modes. |
| 21 | Test count assertions | ✅ PASS | Per-mode loop test uses `for(...) FOREACH_BARRIER_BLEND_MODE_COUNT`; no literal counts. |
| 22 | Downstream re-audit | ⚠️ NOTE | This is itself the post-v5.15.4 re-audit. Touches stamp body shared surface — recommend /parity-check before code if scope tightens. |
| 23 | Latency accountability | ✅ PASS | Plan documents per-mode latency (LEGACY 0ns, BLEND ~25ns, DOMINANT ~12ns, BOTH ~50ns). Hot path 0ns. HOT_PATH_CHANGELOG entries planned. |
| 24 | Mirror-function call-sequence | ✅ PASS | Single ML_BuildParameters dispatch site; no mirror to validate. |
| 25 | TECH_DEBT surface scan | ⚠️ FINDING (see below) | Bandit cache fix overlaps TECH_DEBT-006 (FOREACH_STAMP_BOUND_MODEL_CONST refactor — closed) and v5.14.10 unresolved bandit arm_names issue (no TECH_DEBT entry; should add). |
| 26 | Symmetry test | ✅ PASS | Per-mode test walks FOREACH; LEGACY mode test asserts byte-equivalence to v5.15.4. |
| 27 | DESIGN_SPECS pattern | ✅ PASS | New doc created. Cross-refs all relevant patterns (bitmap, AUTOPOPULATE, PRE/POST, branchless, padding). |
| 28 | Test-strength | ✅ PASS | Plan uses `>=` registry-count assertions; no weakening. |
| 29 | Mechanical citation drift | ⚠️ FOUND 2 DRIFTS (corrected; see below) | Plan claimed Phase A would ADD per_arm arrays to ezoo; actual code shows already on ModelHandle. Citation corrected. |
| 30 | Predicate-contract-changed | ✅ PASS | `EnsembleModelZoo_IsReadyForInference` untouched. |
| 31 | Wider-build verification at predecessor close | ✅ PASS | `plans/v5.15-live-readiness/postmortems/2026-05-12-v5.15.4-postmortem.md` documents `./build.sh gui suite tsan asan all` GREEN result at v5.15.4 close. |

## Dependency verification

| Claimed dependency | Verified | Notes |
|---|---|---|
| `Strategies/StrategyParameters.hpp:1029` weights_buf finalize | ✅ exists | Comment "weights_buf is now finalized" at lines 1027-1032 |
| `Strategies/StrategyParameters.hpp:1040-1047` Model_Predict_Ensemble_Weighted | ✅ exists | Confirmed call site |
| `Strategies/StrategyParameters.hpp:1259-1260` cfg.ml_tp_pct cfg fallback | ✅ exists | Confirmed: `FPN<F> tp_pct = config->ml_tp_pct; FPN<F> sl_pct = config->ml_sl_pct;` |
| `Strategies/StrategyParameters.hpp:1431-1432` out->tp_pct write | ✅ exists | Confirmed |
| `CoreFrameworks/GateParameters.hpp:104-105` ParameterSlot fields | ✅ exists | tp_pct + sl_pct fields confirmed |
| `CoreFrameworks/GateParameters.hpp:167, 189` BG/SG_Evaluate hot path | ✅ exists | Confirmed; reads `params->tp_pct` (the new flow will write into this same field, no change) |
| `ML_Headers/CoreModelZoo.hpp:919` exit_predictor_count | ✅ exists | Confirmed |
| `ML_Headers/CoreModelZoo.hpp:1607-1614` TryLoadRole loop | ✅ exists | Confirmed; loads exit_predictor + buy_signal handles per horizon |
| `ML_Headers/CoreModelZoo.hpp:349-350` handle->label_tp_pct populated from stamp | ✅ exists (NEW FINDING — already populates) | `handle->label_tp_pct = sr.label_tp_pct;` already at line 349; FALSE-NEW caught for Phase A struct extension |
| `ML_Headers/StampBoundModelConstRegistry.hpp:366-369` label_tp_pct + label_sl_pct entries | ✅ exists | Already in registry; INCLUDE mode with has_label_params gate |
| FOREACH_BARRIER_BLEND_MODE registry | ❌ does not exist (NEW) | Plan creates; appropriate NEW |
| `cfg.barrier_blend_mode` | ❌ does not exist (NEW) | Plan creates; appropriate NEW; will join FOREACH_STAMP_BOUND_CFG via AUTOPOPULATE |
| Predecessor v5.15.4 wider build evidence | ✅ verified | Postmortem 2026-05-12 documents `./build.sh gui suite tsan asan all` GREEN |
| Bandit `arm_names[8][32]` field bloat in BanditState | ✅ confirmed cache concern | 256B per state × NUM_REGIMES=5 = 1280B; display-only data inside slow-path-touched struct |

## Hidden scope detected (from cache audit per operator request)

1. **HIGH-1: Bandit arm_names cache bloat** (known since v5.14.10 cache audit; never closed via separate ship). 256B display-only data inside hot-side `BanditState`. Per-cycle slow-path access of `bandits[current_regime]` pulls ~8 cache lines where 4 are arm_names noise. Fix: extract to `BanditDisplayMeta` outside ezoo. Cost: ~50-80 LOC. Operator (Caramel 2026-05-12) explicitly requested bundling with v5.15.5 cache audit.

2. **MEDIUM-1: Shadow ring head false-sharing risk.** If `barrier_shadow_ring.head` shares a cache line with `records[]`, GUI-thread reads invalidate slow-path writes (cross-core). Fix: explicit `alignas(64)` + padding-to-end-of-line on head field. Already incorporated into DESIGN_SPECS doc.

## Cold-pickup context completeness

| # | Field | Verdict | Notes |
|---|-------|---------|-------|
| C.1 | Branch state | ✅ PASS | `feat/v5.15-live-readiness`; rollback anchor v5.15.4 cited |
| C.2 | Phase order matches deps | ✅ PASS | A → B → C → D (each phase depends on prior) |
| C.3 | First concrete move | ✅ PASS | Each phase begins with explicit Step 0/1 |
| C.4 | Function/macro names | ✅ PASS | All named: ML_BuildParameters, CoreModelZoo_TryLoadRole, FOREACH_BARRIER_BLEND_MODE, STAMP_BOUND_CFG_AUTOPOPULATE |
| C.5 | File:line refs | ✅ PASS | All citations verified above |
| C.6 | Stale-claim audit | ⚠️ FINDING | Plan claimed Phase A adds per_arm arrays to ezoo; actual is "ALREADY on ModelHandle" + add tight-pack array to ezoo for cache locality. Distinction matters: per_arm DATA is already loaded; we're adding a cache-friendly secondary access path. Corrected in plan body. |
| C.7 | Effort reconciles with file deltas | ✅ PASS | StrategyParameters.hpp = 1759 LOC (verified via wc -l); +25 LOC in ML_BuildParameters fits. CoreModelZoo.hpp = ~2700 LOC; +30 LOC for struct extension + load-time pack fits. Total plan ~300 LOC, bounded. |
| C.8 | Source-audit refs | ✅ PASS | CLAUDE.md items cited; DESIGN_SPECS docs cited; v5.14.10 postmortem cited |
| C.9 | Predecessor/dependent plans | ✅ PASS | v5.15.4 predecessor cited with path; v5.13.5 (Label Kind CSV) sister-ship cited |
| C.10 | Tag names locked | ✅ PASS | v5.15.5.A through .D + umbrella; rollback anchors named |

## Drift audit (train ↔ serve)

| Category | Verdict | Notes |
|---|---|---|
| Feature drift | ✅ PASS | No feature pipeline changes. |
| Label drift | ✅ PASS | No label-fn changes. label_table[] unchanged. |
| Metric drift | ✅ PASS | No metric formula changes. |
| Path drift | ✅ PASS | No path-builder changes; per-horizon stamp paths unchanged. |
| Format drift | ⚠️ MITIGATED | Adding `barrier_blend_mode` to stamp via Surface G `has_*` flag (forward-compat). MODEL_FORMAT_VERSION unchanged per CLAUDE.md item 15. Legacy stamps load with `has_barrier_blend_mode=0` → mode defaults to LEGACY. |
| Threshold drift | ✅ PASS | No threshold duplication; per-horizon barriers single-source-of-truth from stamp. |
| Tick-source drift | ✅ PASS | No producer changes. |
| Build-flag drift | ✅ PASS | No new build flags. |

## Hardening checks

- Atomic file writes: ✅ shadow stats persistence uses existing tmp+rename pattern (mirror bandit_state.json)
- Locale pinning: ⚠️ shadow stats JSON writes %g format → MUST pin LC_NUMERIC=C (mirror v5.14.10.C bandit_state.json fix). Add to Phase B.
- GUI render-thread blocking I/O: ✅ MLStatusPanel reads ring head atomically; no blocking
- Failure telemetry: ✅ NaN guards in BLEND inputs; LEGACY fallback on bad data; WARN log on mixed-stamp ensemble
- Resource cleanup: ✅ no new fopen/malloc/popen
- Cancellation: n/a (no new worker threads)
- Cross-platform: ✅ all POSIX

## Propagation checks

| Surface | Needed | In plan? |
|---|---|---|
| `engine.cfg.example` entry | ✅ | YES (Phase D) |
| GUI Settings tooltip | ✅ | YES (Phase B Step 2 dropdown + tooltip auto-derived) |
| `DOCS/CHANGELOG.md` | ✅ | YES (Phase D) |
| `DOCS/CLAUDE_INTEGRATION.md` | n/a | No new cfg integration recipe needed; existing patterns apply |
| Stamp body via AUTOPOPULATE | ✅ | YES (Phase A.0 verifies registry; AUTOPOPULATE handles wiring) |

## Behavior-change-via-default check

- `cfg.barrier_blend_mode`: default = 0 (LEGACY) → preserves pre-v5.15.5 bytewise behavior. Operator opts in to non-legacy mode explicitly. ✅ PASS

## Pragmatic-but-ugly patterns

- Dual paths: barrier_blend_mode has 5 modes but UNIFIED dispatch via FOREACH registry (CLAUDE.md item 13). Not "dual paths" in the sprawl sense. ✅
- Half-wired enum: all 5 modes have implementations + dispatch entries. ✅
- Snapshot-affecting struct change: per_arm_barriers tight-pack added to ezoo (NOT persisted state, runtime-only); shadow ring is also runtime-only. ✅
- Cfg w/o consumer: every new cfg field has both parser AND consumer in same ship. ✅
- New invariant w/o test: per-mode loop test + cache layout static_asserts + Tier 1 strict refuse tests. ✅

## Recommendations

### Must fix before coding
- **R1: Phase A simplification** — already corrected in plan body. Per-arm barriers ALREADY on ModelHandle from stamp; Phase A is "ADD ezoo cache-friendly tight-pack array + populate from handle at load time", not "ADD struct fields".

### Worth fixing during coding
- **R2: Include bandit arm_names extraction in v5.15.5** (cache-layout family bundling). HIGH-1 finding from cache audit; ~50-80 LOC; closes v5.14.10 known issue. Per CLAUDE.md item 19 (structural-fix-preferred when bug class recurs), same cache-layout class deserves one ship.
- **R3: Locale pinning on barrier_mode_shadow_stats.json** — Phase B must include `uselocale(LC_NUMERIC=C)` mirror of v5.14.10.C bandit_state.json pattern.
- **R4: Symmetric bandit_algorithm mode 3 (Thompson drives, Exp3 logs)** — Caramel asked about symmetric coverage; current registry asymmetric (mode 0/1/2, missing 3). Add as companion sub-ship v5.15.5.E or defer to TECH_DEBT entry. Recommend INCLUDE in v5.15.5.E since same shadow-mode pattern.

### Acceptable risk (don't block)
- **A1: cfg.per_horizon_barrier_blend stays direct cfg bool** (not migrated to ml_cfg_flags bitmap) — defer to v5.15.6 cohort migration sweep.
- **A2: Per-core override `core_N_barrier_blend_mode`** — defer to v5.15.6 (precedent: risk_degradation_curve per-core override v5.14.9.C).

## Map-update suggestions (post-implementation)

- Run `./tools/gen_code_map.sh` after coding (new FOREACH_BARRIER_BLEND_MODE registry + new functions)
- INVARIANTS_MAP.md: add row for per-arm barrier blend invariant; mark COVERED by per-mode parity_harness test
- HOT_PATH_CHANGELOG.md: append entries per phase

## Verdict: 🟡 YELLOW

Plan is structurally sound but has TWO must-fix items already addressed mid-audit (Phase A simplification + DESIGN_SPECS cache discipline), and TWO recommended-during-coding scope expansions (bandit arm_names + symmetric mode 3).

Address R2 + R4 scope decisions before Phase A starts. After those decisions:
- If R2 included: scope ~330 LOC; same single ship
- If R4 included: +50 LOC; v5.15.5.E sub-tag
- If both deferred: v5.15.5 stays narrow at ~250 LOC; both go to TECH_DEBT

Then GREEN to code.

---

## Cache-layout deep-dive (per operator request 2026-05-12)

Caramel: "we should audit for more issues like this around the bandit and thompson as well" + "i know we had a known cache miss for thompson, we should try to figure that out right now" + "during the shadowed mode"

### Identified

| Site | Bytes | Cache lines | Severity |
|---|---|---|---|
| `EnsembleModelZoo.bandits[NUM_REGIMES=5]` total | 5 × ~460B = ~2300B | ~36 lines | active regime: 8 lines/cycle |
| `BanditState.arm_names[8][32]` (HIGH-1) | 256B per state | 4 of 8 lines wasted per access | HIGH-1 |
| `EnsembleModelZoo.thompson_bandits[NUM_REGIMES=5]` | 5 × 112B = ~560B | ~9 lines | active regime: 2 lines/cycle |
| `ezoo->primary_handles[h].label_tp_pct` (CURRENT) | 8 handles × 1 line | 8 lines | MEDIUM (solved by v5.15.5 tight-pack) |
| `barrier_shadow_ring.head` cross-thread (NEW v5.15.5) | 8B atomic | 1 line if isolated | MEDIUM (alignas(64) fix) |
| `BanditState` per-regime BOTH-mode access (cfg=2) | Exp3 + Thompson | ~10 lines combined | LOW (mitigated by ezoo's per-core locality) |

### Per-cycle slow-path cache traffic (current vs post-v5.15.5)

**Current (pre-v5.15.5):**
- bandits[regime]: 8 cache lines (arm_names bloat)
- thompson_bandits[regime]: 2 lines
- primary_handles[h].label_tp_pct (h=0..7) for current cfg-fallback flow: N/A (cfg direct used)
- weights_buf compute: 1 line (local)
- Total: ~11 lines for bandit + ~0 for cfg-fallback barriers

**Post-v5.15.5 with HIGH-1 fix bundled:**
- bandits[regime]: 4 lines (arm_names extracted)
- thompson_bandits[regime]: 2 lines
- per_arm_barriers (NEW tight-pack): 1 line
- barrier_shadow_ring.head: 1 line (cross-thread isolated; not on shared line)
- Total: ~8 lines for bandit + 1 for barriers + 1 for shadow

**Savings:** 4 lines × ~100 ns / miss = ~400 ns/cycle/core when arm_names extraction lands. Per CLAUDE.md item 7.

### Shadow-mode-specific cache risk

In BOTH_*_DRIVES modes (3 and 4):
- Both blend AND dominant computed per cycle from same weights_buf + per_arm_barriers (already in L1 from prediction blend)
- Shadow record write: 1 cache line per record (records aligned to 32B; 2 records per line)
- Head update: atomic store (own cache line via alignas(64) + padding) — no false sharing

Net additional cache cost in BOTH mode vs single-mode: ~1 cache line per cycle (the shadow ring write). Acceptable.

---

## Final actions before coding starts

1. Caramel decides R2 (bundle bandit arm_names extraction) — recommend YES
2. Caramel decides R4 (bundle symmetric bandit mode 3) — recommend YES for symmetry close
3. Phase A code follows the DESIGN_SPECS doc (per-horizon-barrier-blending-with-shadow-mode.md)
4. Run /trace-deps + /parity-check before Phase B (recommended)
5. /dod-audit (Check 27) on final plan post-decision

Report saved to: `plans/plan_checks/readiness-2026-05-12-v5.15.5-per-horizon-tp-sl-serving.md`
