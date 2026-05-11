# /readiness report — v5.14.11 online correlation matrix updates — 2026-05-11

**Plan:** `plans/v5.14-foxml-port-and-maker/subplans/2026-05-08-v5.14.11-online-corr-update.md`
**Predecessor:** v5.14.10 umbrella (HEAD = e0cc877; SHIPPED 2026-05-10) — VERIFIED
**Rollback anchor:** `pre-v5.14.11` (exists; created 2026-05-10) — VERIFIED
**Sprint:** v5.14-foxml-port-and-maker; v5.14.11 is Phase 4 final

---

## Plan summary

- 3 sub-tags planned: .A (scalar kernel + tests, ~200 LOC), .B (AVX-512 vectorization, ~150 LOC), .C (engine wiring + cfg, ~80 LOC)
- Umbrella tag after .C green
- Branch: `feat/v5.14-foxml-port-and-maker` — matches current branch
- Surface: ML_Headers/RidgeBlender.hpp (extend) + Strategies/StrategyParameters.hpp (swap at 2 sites) + CoreFrameworks/ControllerConfig.hpp (1 new cfg field)
- Cfg-gated default-off; bytewise-identical fallback to v5.14.0 BuildCorr when disabled
- Hot path UNTOUCHED. Slow-path latency analysis: -700-900ns/cycle when Ridge enabled (modest absolute; ~25-30% of Ridge cost)

---

## Checklist verdicts (Checks 1-30)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | PASS | Plan explicitly notes "Hot path UNTOUCHED" |
| 2 | Train-serve parity | PASS | No stamp body / feature pipeline / scaler changes. Plan correctly cites "no train-serve surface" |
| 3 | Surface area | PASS | 3 files touched. Sub-tag-bounded |
| 4 | Pointer init / heap lifecycle | PASS | RidgeOnlineState added inside existing EnsembleModelZoo zero-init path; no new heap allocation |
| 5 | Backward compat | PASS | No version-constant bumps; default-off cfg flag preserves byte-identical behavior |
| 6 | Multi-threading | PASS | Slow-path single-writer pattern; no new atomics; CoreContext-local state |
| 7 | Test coverage | PASS | 5 explicit test categories listed (correctness vs full BuildCorr, Welford stability, AVX-512 byte-identity, periodic recompute, default-cfg byte-identity) |
| 8 | Docs + invariants | DOCUMENT-ONLY | Plan should note HOT_PATH_CHANGELOG.md entry for slow-path -700-900ns; Check 23 captures |
| 9 | Forward maintenance | YELLOW | Two BuildCorr call sites (buy@996 + exit@1195) duplicate the ring-walk-backwards-from-head pattern. Check 24 flags this. See "Blockers" |
| 10 | Rollback story | PASS | `pre-v5.14.11` tag exists; sub-tag anchors flow from there |
| 11 | Architectural sprint detection | PASS | Not an architectural sprint (no split/extract/decouple keywords) |
| 12 | Display ↔ execution invariant | PASS | No Position field touched; no GUI surface |
| 13 | Strategy lifecycle completeness | PASS | No strategy changes |
| 14 | X-macro dispatch correctness | N/A | No X-macro entries |
| 15 | ML feature change → parity regression update | PASS | No FOREACH_FEATURE / RegimeSignals / Features_PackAll changes |
| 16 | New cfg field with stamp-bearing → recipe doc | PASS | cfg.ridge_online_corr is NOT stamp-bound (perf-only toggle; identical output guaranteed by 1000-cycle drift reset) |
| 17 | Model-load path changes → strict-mode test | PASS | No model-load path touched |
| 18 | Reuse-audit | YELLOW | (a) Welford has NO direct precedent — confirmed; RollingStats uses running-sums (a distinct technique, Plan correctly flags this in cross-refs). (b) v5.11.7 AVX-512 byte-determinism pattern at BanditLearning.hpp:147-188 — Plan cites + commits to reuse. (c) Ring-iteration walk-backwards pattern PRESENT at both call sites — see Check 24 |
| 19 | Pre-existing-work audit (Check 19) | PASS | All NEW claims verified absent (RidgeOnlineState, _UpdateOnline, _FinalizeCorr, ridge_online_corr — 0 hits). All REUSE claims verified present (BuildCorr@287, calls@996+1195, RidgeWeights@85, RidgeBlender_Compute@202, REWARD_RING_SIZE@893, reward_ring_head@903, primary_count@936) |
| 20 | Future-proofness sanity | PASS | No N-of-anything pattern. AVX-512 inner loop is fixed at N=8 (MAX_RIDGE_MODELS); test-count assertions follow established `>=` convention |
| 21 | Test count assertion fragility | PASS | Plan describes test categories, not literal `== N` counts |
| 22 | Auto-trigger downstream re-audit | N/A | v5.14.11 is Phase 4 FINAL; no downstream sub-plans in this sprint |
| 23 | Latency accountability | YELLOW | Plan provides cost estimate (~30ns AVX-512 / ~250ns scalar / ~70ns total online vs ~1µs baseline) but does NOT explicitly commit to a HOT_PATH_CHANGELOG.md entry. Slow-path change qualifies (≥10ns/cycle; saves ~700-900ns). Plan should land a HOT_PATH_CHANGELOG row in .C |
| 24 | Mirror-function call-sequence enumeration | **YELLOW — MAIN FINDING** | Two BuildCorr call sites (buy@985-998 + exit@1184-1197) share IDENTICAL ring-walk-backwards-from-head pattern + same flat-history build + same BuildCorr call shape. Plan flags this in "TWO sites" pre-audit section but design ASSUMES extending RidgeWeights propagates to both; no explicit helper extraction. Per CLAUDE.md item 19 + Check 24, structural fix (e.g., `RidgeBlender_BuildHistoryFromRing<F>(ring, head, count, primary_count, history_out)`) preferred over direct patch when call sequence is identical. See "Blockers" |
| 25 | TECH_DEBT.md surface-area scan | PASS | Cross-checked open entries: TECH_DEBT-021 (post-paper-test profiling; v5.14.11 perf data feeds this — not blocking), TECH_DEBT-029 (source file length; RidgeBlender.hpp = 384 LOC + ~300-400 add ≈ 700; well below 1500 trigger), TECH_DEBT-026/-028/-030/-031 (no overlap with Ridge surface). NO new deferral candidates surfaced from this audit |
| 26 | DEFERRED-FOR-FUTURE-SHIP placeholder | N/A | No X-macro registries added; no symmetry test required |
| 27 | DESIGN_SPECS pattern application (via /dod-audit inline) | YELLOW | (a) cfg-flag-eligibility-criteria.md: cfg.ridge_online_corr passes ALL 5 criteria → framework says MIGRATE to FOREACH_ML_CFG_FLAG. BUT three precedent ridge cfgs (ridge_within_horizon@665, ridge_across_horizons@666, exit_blender_mode@1105) stayed as direct ints. Operator decision — see "Blockers". (b) slow-path-gate-registry-pattern.md: STRONG sister candidate for MASK_RIDGE_ONLINE_CORR_ACTIVE — but only if migrated. (c) structural-fix-preferred-decision-framework.md: 1000-cycle reset is a code-smell (Welford with periodic-reset pattern is established in literature; preserve). (d) wire-format-byte-preservation-discipline.md: N/A. (e) heterogeneous-registry-pattern.md: N/A |
| 28 | Test-strength anti-regression audit | PASS | Plan ADDS tests; no test weakenings. Tolerance is correctness-bounded (1e-9), not arbitrary loosening |
| 29 | Mechanical citation drift | PASS | All citations verified at HEAD: BuildCorr@287, calls@996+1195, RidgeWeights@85, BanditLearning AVX-512@147-188, REWARD_RING_SIZE@893. Plan was just amended; clean |
| 30 | Predicate-contract-changed audit | PASS | EnsembleModelZoo_IsReadyForInference@CoreModelZoo.hpp:2429 NOT modified by plan; no test fixtures need updating |

---

## Cold-pickup completeness (10 fields)

| # | Field | Verdict | Notes |
|---|-------|---------|-------|
| C.1 | Branch state | PASS | "feat/v5.14-foxml-port-and-maker" cited explicitly |
| C.2 | Phase execution order matches dependency order | PASS | .A → .B → .C → umbrella; matches dependency (kernel before vectorization before wiring) |
| C.3 | First concrete move per phase | YELLOW | Each sub-tag has a description but no explicit "Step 0". E.g., .A: which fn first, which line in RidgeBlender.hpp |
| C.4 | Function/constructor/macro names cited | PASS | RidgeBlender_UpdateOnline, _FinalizeCorr, RidgeOnlineState all named precisely |
| C.5 | File:line refs for cited tests/baselines | YELLOW | Plan cites "v5.11.7 Bandit_GetProbabilities" without `BanditLearning.hpp:147-188` line ref; cite RollingStats.hpp:83-87 IS present (good) |
| C.6 | Stale-claim audit | PASS | Verified: BuildCorr at 287, both call sites at 996/1195, predecessor at e0cc877 |
| C.7 | Effort claims reconcile with file sizes | PASS | RidgeBlender.hpp is 384 LOC; +200/150/80 LOC realistic |
| C.8 | Source-audit references with paths | PASS | "Pass 2 #9 finding" cited |
| C.9 | Predecessor/dependent plans named with paths | YELLOW | Predecessor cited as "v5.14.10 close" but not full path. Should be `plans/v5.14-foxml-port-and-maker/subplans/2026-05-10-v5.14.10-bayesian-thompson-bandit.md` |
| C.10 | Tag names locked + rollback anchors | PASS | `pre-v5.14.11` cited; sub-tag names locked |

**Score: 7/10 PASS + 3/10 YELLOW. Above the 8/10 GREEN threshold? No, but flagged 3 are all DOCUMENT-ONLY (cosmetic; doesn't block coding).**

---

## MAIN FINDINGS (severity-ordered)

### YELLOW.1 (Check 24 / item 19) — Mirror call-sequence at TWO BuildCorr sites

Buy-side (StrategyParameters.hpp:985-994) and exit-side (:1184-1193) share the IDENTICAL pattern:

```
for (int k = 0; k < avail; ++k) {
    int ring_idx = (HEAD - 1 - k + REWARD_RING_SIZE) % REWARD_RING_SIZE;
    for (int i = 0; i < primary_count; ++i) {
        history[k * primary_count + i] = RING[ring_idx].predictions[i];
    }
}
RidgeBlender_BuildCorr<F>(corr_matrix, history, avail, primary_count);
```

Differences: ring source (`reward_ring` vs `exit_reward_ring`), head field (`reward_ring_head` vs `exit_reward_ring_head`), count field (`primary_count` vs `exit_predictor_count`). Body is structurally identical.

**Per CLAUDE.md item 19** (Structural fix preferred when bug class can recur) + **Check 24** (mirror-function call-sequence enumeration): same pattern at multiple sites = Class 18 recurrence risk. With the v5.14.11 plan extending BOTH sites in the SAME way (push latest → finalize → 1000-cycle reset), each future modification (e.g., variable history depth, sliding window, drift threshold tuning) must touch BOTH sites.

**Plan's current treatment:** flags both sites in pre-audit section; assumes extending RidgeWeights propagates. Implicitly correct but doesn't EXTRACT the shared helper.

**Recommended structural fix** (operator decision):
- Extract `RidgeBlender_BuildHistoryFromRing<F>(ring, head, count_used, primary_count, history_out)` to RidgeBlender.hpp
- Both call sites collapse from ~10 LOC to ~2 LOC each
- Future variants (sliding window, weighted history) modify ONE helper, not two sites
- Symmetry test at CI: call helper from buy + exit contexts, assert bytewise-identical history given identical inputs

**Cost:** ~30 min during .C; reduces both call sites; closes Class 18 vector preemptively.

### YELLOW.2 (Check 27 / cfg-flag-eligibility) — cfg.ridge_online_corr migration tension

Applying `cfg-flag-eligibility-criteria.md`'s 5-criteria framework to `cfg.ridge_online_corr`:

1. Runtime-mutable (engine.cfg boot toggle): **PASS**
2. Engine-wide scope: **PASS**
3. BITMAP_IS_SET cost acceptable (slow-path, ~5ns vs ~1µs of work): **PASS**
4. No compile-time elision benefit (both modes are real operating modes): **PASS**
5. Cfg-domain-coherent (ML pipeline behavior, fits FOREACH_ML_CFG_FLAG): **PASS**

**All 5 PASS → framework says MIGRATE.**

But the existing precedents (`ridge_within_horizon@665`, `ridge_across_horizons@666`, `exit_blender_mode@1105`) all stayed as DIRECT int cfg fields, NOT migrated despite the v5.14.9.F.2 sweep + v5.14.10 audit. The MlCfgFlagRegistry comment at line 47 says "Add here if the flag governs ML pipeline behavior" — ridge_online_corr clearly fits, but so did the prior ridge fields.

**Operator decision needed:**
- Option A — Migrate `ridge_online_corr` to FOREACH_ML_CFG_FLAG NOW (one new row in v5.14.11.C; ~5 min); document precedent. Then schedule a future cleanup ship to migrate the 3 existing ridge cfgs (consistency).
- Option B — Add as direct int cfg field (matches local precedent); add TECH_DEBT entry for "migrate ridge cfg cluster to FOREACH_ML_CFG_FLAG in a future cleanup ship."
- Option C — Migrate all 4 ridge cfgs in v5.14.11.C as part of the ridge cluster (consistency now; ~30 min extra).

Caramel's framing 2026-05-09 ("structural-fix-preferred"): Option A or C are aligned. Option B defers — acceptable if scoping discipline matters.

### YELLOW.3 (Check 23) — HOT_PATH_CHANGELOG entry not committed in plan

Plan provides good cost analysis (latency analysis section) but does NOT explicitly say "Add HOT_PATH_CHANGELOG.md entry in .C." Per CLAUDE.md item 17 + Check 23, slow-path additions ≥10ns/cycle (this saves 700-900ns; the toggle adds ~5ns when off, ~70-250ns when on) require an entry.

**Recommended fix:** add one line to plan's "Step 5 — Tests" section: "HOT_PATH_CHANGELOG.md entry: slow-path Ridge cycle: -700-900ns when enabled, +5ns when disabled (flag check)."

---

## Dependency verification

| Claimed dependency | Verified | Notes |
|---|---|---|
| `RidgeBlender_BuildCorr` @ RidgeBlender.hpp:287 | EXISTS at line 287 | EXACT match |
| BuildCorr call buy @ StrategyParameters.hpp:996 | EXISTS at line 996 | EXACT match (caller line; called body 985-994) |
| BuildCorr call exit @ StrategyParameters.hpp:1195 | EXISTS at line 1195 | EXACT match (caller line; called body 1184-1193) |
| `RidgeWeights<F>` struct @ RidgeBlender.hpp:85 | EXISTS at line 85 | EXACT match |
| `EnsembleModelZoo.reward_ring` PredictionRecord ring | EXISTS at CoreModelZoo.hpp:902-911 | EXACT match |
| `RidgeBlender_Compute` downstream consumer | EXISTS at RidgeBlender.hpp:202 | EXACT match |
| `ML_BuildParameters` dispatch site | EXISTS in StrategyParameters.hpp | EXACT match (current dispatch is ~887-1009 per Check 29 reconciliation) |
| `RollingStats.hpp:83-87` running-sums precedent | VERIFIED | RollingStats uses naive sum-of-squares; Plan correctly says "this is a distinct technique" |
| v5.11.7 AVX-512 pattern @ BanditLearning.hpp | EXISTS at lines 147-188 | EXACT match. Plan cites pattern but not line range (cold-pickup YELLOW C.5) |
| NEW: `RidgeOnlineState` struct | 0 hits — NOT present | TRULY NEW ✓ |
| NEW: `RidgeBlender_UpdateOnline` | 0 hits — NOT present | TRULY NEW ✓ |
| NEW: `RidgeBlender_FinalizeCorr` | 0 hits — NOT present | TRULY NEW ✓ |
| NEW: `cfg.ridge_online_corr` | 0 hits — NOT present | TRULY NEW ✓ |

All 14 dependency verifications PASS.

---

## Drift audit (8 train-serve categories)

| Category | Verdict | Notes |
|---|---|---|
| Feature drift | PASS | No feature additions/removals |
| Label drift | PASS | No label changes |
| Metric drift | PASS | Correlation matrix is internal-only (slow-path scratch); not a published metric |
| Path drift | PASS | No file path / serialization indirection |
| Format drift | PASS | No version constant bumps; no stamp body changes |
| Threshold drift | PASS | No shared thresholds |
| Tick-source / time-source drift | PASS | No tick source changes |
| Build-flag drift | YELLOW | AVX-512 path is `cfg.ridge_online_corr=1`-gated, not build-flag-gated. Plan should specify whether the AVX-512 kernel uses runtime detection (`__builtin_cpu_supports`) or compile-time flag (`-mavx512f`). If compile-time, document the assumption + fallback for non-AVX-512 builds |

---

## Recommendations

### Must fix before coding (BLOCKER)

NONE. No GAP findings; all checks PASS or YELLOW.

### Worth fixing during coding (YELLOW; address in .C or earlier)

1. **YELLOW.1 — Extract `RidgeBlender_BuildHistoryFromRing<F>` helper** to eliminate mirrored ring-walk pattern at 2 sites. ~30 min during .C. Closes Class 18 vector preemptively.
2. **YELLOW.2 — cfg.ridge_online_corr migration decision.** Operator picks Option A/B/C above. ~5-30 min depending on choice.
3. **YELLOW.3 — HOT_PATH_CHANGELOG.md entry** for slow-path -700-900ns delta. Land in .C commit. ~5 min.
4. **YELLOW Build-flag drift** — clarify AVX-512 detection strategy (runtime vs compile-time). ~5 min plan edit.

### Acceptable risk (don't block)

- Cold-pickup C.3, C.5, C.9 cosmetic items (Step 0 absent, missing line refs, predecessor path missing) — fix during coding kickoff.
- Mid-sprint audit suggestion: Phase 4 final; no downstream plans depend on v5.14.11 (item 22 N/A).

---

## Auto-write contract

**No new TECH_DEBT entries surfaced.** YELLOW.1 (helper extraction) is BLOCKING-OPTION; YELLOW.2 (cfg-flag migration) has Option B as a DEFERRAL path — if operator picks B, a new TECH_DEBT entry "Ridge cfg cluster migration to FOREACH_ML_CFG_FLAG" would be auto-written. Pending operator decision; entry not written yet.

---

## Verdict: **YELLOW**

GREEN-with-amendments. None of the YELLOW findings BLOCK coding:
- YELLOW.1 is an enhancement (structural fix preferred but not strictly required; current plan correctness holds either way)
- YELLOW.2 is an operator decision (3 valid paths; all preserve correctness)
- YELLOW.3 is mechanical bookkeeping (HOT_PATH_CHANGELOG entry; lands in .C commit)

**Recommendation:** Operator picks resolution for YELLOW.1 (extract helper Y/N) + YELLOW.2 (cfg-flag migration A/B/C) before .C kickoff. Resolution recommended in pre-coding consult per CLAUDE.local.md going-forward rule.

If YELLOW.1 → extract helper + YELLOW.2 → Option A (migrate ridge_online_corr only): **GREEN**, ~35 min added scope, structural-fix-preferred discipline upheld.

If YELLOW.1 → defer + YELLOW.2 → Option B (direct int + TECH_DEBT entry): **GREEN-CONDITIONAL**, plan ships as-drafted, two TECH_DEBT entries auto-written (helper extraction follow-up + cfg-cluster migration follow-up).

Either resolution path passes verification.
