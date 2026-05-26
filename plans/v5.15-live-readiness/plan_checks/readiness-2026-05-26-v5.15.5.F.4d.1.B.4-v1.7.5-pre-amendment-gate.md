---
type: audit-report
audit: /readiness
target: plans/v5.15-live-readiness/subplans/2026-05-24-v5.15.5.F.4d.1.B.4-train-serve-execution-layer-parity.md
plan_version_audited: v1.7.4 LOCKED + v1.7.5 PENDING-AMENDMENT
audit_date: 2026-05-26
verdict: YELLOW
audit_tier: HIGH-RISK (per plan frontmatter line 5)
auditor: /readiness (Layer 2 subagent)
sister_audits: [/precoding-audit-gate, /blindspot-scan, /bug-check, /trace-deps, /parity-check]
engine_head: e0acb65 (WIP-11 boundary)
---

# /readiness report — `.B.4` v1.7.5 pre-amendment gate — 2026-05-26

## Plan summary

- **Target ship:** `v5.15.5.F.4d.1.B.4` train-serve execution-layer parity structural extract
- **In-flight state:** v1.7.4 LOCKED (post-WIP-11 boundary); v1.7.5 amendment PENDING (planned scope captured in `decision-logs/2026-05-24-v5.15.5.F.4d.1.B.4-v1.7.4.md` v1.7.4 → v1.7.5 transition section D15-D18 + F13-F19 + C21-C30)
- **Audit tier:** HIGH-RISK declared per plan frontmatter (slow-path body + cross-cutting + multi-surface deletion + framework-level M5/M6/M7 promotions)
- **Verdict:** YELLOW — v1.7.4 spec is structurally GREEN for in-flight WIP execution; v1.7.5 PLANNED scope (D16/D17/D18 + F16/F17 + C25-C30) requires SUBSTANTIVE plan body amendment + full 5-agent re-audit BEFORE WIP-12 coding (per `feedback_tiered_audit_discipline_per_plan_scope` HIGH-RISK cadence)
- **Branch:** `feat/v5.15-live-readiness` (engine HEAD `e0acb65`; 11 commits ahead of `origin/feat/v5.15-live-readiness` per ship-close push workflow)
- **Tests preserved:** 3217 / 0 (B-Plus v0.3 line-anchor mode exit 0)

---

## Stage 0 — DESIGN_SPECS preload (loaded into context for this audit)

Per plan surface keywords matched:

| Keyword | DESIGN_SPECS loaded |
|---|---|
| "helper extract from inline body" / "slow-path body extract" | `refactor-patterns/shared-helper-extract-for-train-serve-mirror-close.md` + `refactor-patterns/orchestration-helper-with-pod-args-pattern.md` |
| "Class 18 mirror state/code" / "PARITY-N cluster close" | `meta-disciplines/structural-fix-preferred-decision-framework.md` + `meta-disciplines/train-serve-execution-layer-parity.md` |
| "X-macro registry / FOREACH_SLOW_PATH_GATE row-add" | `framework-patterns/slow-path-gate-registry-pattern.md` + `framework-patterns/x-macro-registry-with-presence-dispatch.md` (cross-ref CLAUDE.md item 15) |
| "BookSnapshot reuse / canonical sister" | `meta-disciplines/canonical-sister-extension-discipline.md` |
| "M6 body-content arg enumeration" / "M7 structural enforcement" | `meta-disciplines/body-content-enumeration-at-plan-time-discipline.md` (Stage 2 DRAFT) + `meta-disciplines/structural-enforcement-when-memory-insufficient.md` (Stage 3 first-canonical via B-Plus CI tool) |
| "branchless gating per H20 for SP" | `refactor-patterns/branchless-dispatch-discipline.md` |
| "centralized-arch deprecation / full surface deletion" | (NO sister DESIGN_SPEC currently exists; gap flagged below) |
| "AUTOPOPULATE_ENGINE_WIDE / scope=ENGINE_WIDE" | `framework-patterns/autopopulate-pattern-for-production-caller-class.md` |

---

## Checklist verdicts (Checks 1-34)

| # | Item | Verdict | Notes |
|---|------|---------|-------|
| 1 | Hot path purity | PASS | Plan body explicitly declares `hot_path: UNTOUCHED` (frontmatter:30); helpers operate at boot + slow-path-cycle layer; H7/H8 budgets preserved; verified by `calls_graph_diff.sh` gate at verification table |
| 2 | Train-serve parity | PASS | THE ENTIRE SHIP IS this check; 7 PARITY entries (026-032) close by-construction; M5 Stage 3 promotion; bytewise-identical math discipline at O2 + HMAC byte preservation gate |
| 3 | Surface area | YELLOW-PENDING-v1.7.5 | v1.7.4 scope: 5 helpers + cfg/state/oms/ML zoo wiring (~8 files touched). v1.7.5 amendment scope adds B-full deletion: +6-8 surfaces (CfgFieldRegistry.hpp + ControllerConfig.hpp parser + EngineSharded.hpp 8 branches + ControllerEventLoop.hpp 3 wrappers + EngineTUI.hpp + DashboardPanels.hpp). Total ~14-16 files at WIP-13. Justified by D18 full-surface-deletion decision; needs explicit Surface section in v1.7.5 amendment |
| 4 | Pointer init / heap lifecycle | PASS | LIVE: aligned_alloc + null-check + free-on-fail per O4. BACKTEST: static array + Free+Init prior-run. Decision H nullable `*` explicit. No new heap-allocated state. |
| 5 | Backward compat | PASS-WITH-EXPLICIT-OVERRIDE | D18 LANDED — backwards compat NOT a default concern; OSS personal tool. `SHARDED_SNAPSHOT_VERSION` / `MODEL_FORMAT_VERSION` UNCHANGED (no schema bump). Legacy single_core LIVE engine preserves centralized execution semantics (operator framing: "we already have a preserved single core trading system"). Operator migration impact section needed in v1.7.5 amendment. |
| 6 | Multi-threading | PASS | No new threads; no new shared state; no new atomics. Decision G statics stay in caller. Helper signatures pass references (not pointers) for non-nullable; cross-thread cfg already seqlock-cached. |
| 7 | Test coverage | PASS | 3217 tests preserved; B.5 added 9 NEW check() calls (5 FOREACH_SLOW_PATH_GATE BREAKEVEN_ON_PROFIT + 2 EngineCommon_ApplyBnbDiscount + 2 sister cases). 6 build dirs PASS at WIP-7/8/11. B-Plus v0.3 exit 0. |
| 8 | Docs + invariants | PASS-WITH-PENDING | Plan body declares Stage 2→3 promotion: `train-serve-execution-layer-parity.md` + `shared-helper-extract-for-train-serve-mirror-close.md` (DESIGN_SPECS) + DESIGN_PHILOSOPHY § 11.5 M5 + RECURRING_BUG_PATTERNS Class 18 + CLAUDE.local.md row. v1.7.5 amendment scope adds Class 18 cohort wrapper deletion prevention rationale (F17). |
| 9 | Forward maintenance | PASS | 5-helper structure with sister-canonical inheritance (`Sharded_ValidatePartialExitCfg` precedent). Single source of truth for cfg defaults at registry. EngineCommon naming convention establishes pattern. |
| 10 | Rollback story | PASS | `pre-v5.15.5.F.4d.1.B.4` rollback anchor at Step 0 of coding. WIP-checkpoint commits 1-11 establish granular rollback. 3-WIP cadence (D17: WIP-12/13/14) gives independent rollback anchors per substantive change. |
| 11 | Architectural sprint detection | PASS | Plan IS the architectural extract sprint; properly scoped to single sub-ship; v1.7.5 B-full scope expansion DOCUMENTED at D16 + 3-WIP cadence |
| 12 | Display ↔ execution invariant | PASS-WITH-PENDING | TUISnapshot.engine_arch field deletion (D18 + F18) means display-side will lose engine_arch indicator at WIP-13; verify GUI DashboardPanels.hpp:2165/2211/2214 etc. become unconditional + no display drift |
| 13 | Strategy lifecycle completeness | PASS | BootPerCore lifecycle (item 5 ML branch + item 6 Strategy_InitPerCore) covers full lifecycle; STRATEGY_NONE branch explicit |
| 14 | X-macro dispatch correctness | PASS | FOREACH_SLOW_PATH_GATE row addition + AUTOPOPULATE_ENGINE_WIDE wiring + sister consumer pattern matched at ControllerEventLoop.hpp:2344 + :3558 (verified). v1.7.3 N-2 macro arg signature drift FIXED at v1.7.4 (compile-fail risk eliminated). |
| 15 | ML feature change parity | PASS | No NEW ML features; existing features now correctly wire BOTH paths (PARITY-027/028 closure). FeatureRegistry untouched. |
| 16 | New cfg field stamp-bearing | PASS-NA | No NEW cfg fields. Existing cfg fields (`pay_fees_in_bnb` / `breakeven_on_profit` / `confidence_composite_enabled` / etc.) now drive BOTH train + serve. |
| 17 | Model-load path strict-mode | PASS | BootPerCore preserves strict-mode unload semantics (line 800-803 plan body); CORE_STATE_FLAG_SET(MODEL_LOAD_FAILED) on strict-fail; sister between LIVE + BACKTEST. |
| 18 | Reuse-audit | PASS | 5-helper structure IS the reuse vehicle; sister-canonical extension for BookSnapshot (Option β-1) per D8 + Canonical sister section. `Sharded_ValidatePartialExitCfg` cited as ApplyBnbDiscount sibling. |
| 19 | Pre-existing-work audit | PASS | EventLoop_BreakevenOnProfitOneCore CONFIRMED EXISTS at ControllerEventLoop.hpp:3754 per M2; OneCore variants for TimeExit + TrailingSLRatchet also exist; no false-NEW claims. |
| 20 | Future-proofness sanity | PASS | 5-helper API surface uniform per Decision H; sister to v6.0 decoupling roadmap (decoupling breadcrumb section); D1-C deferred via TECH_DEBT-125 when cohort grows. |
| 21 | Test count assertion fragility | PASS | Verification gate uses range `3208 → 3210-3215` (NOT `==`); robust to add. 3217 actual preserves. |
| 22 | Auto-trigger downstream re-audit | PASS-WITH-PENDING | v1.7.5 substantive amendment WILL TRIGGER full 5-agent re-audit per C26; HIGH-RISK tier mandates per Check 34. Properly captured in commitment. |
| 23 | Latency accountability | PASS | Phase B Step B.6 micro-benchmark gate + objdump diff for SlowPathCycleOneCore + ≤5ns BITMAP_IS_SET cached gate budget for UNSET cohort + ≤100μs p99 H8 budget for SET cohort. HIGH-4 telemetry Path A INTERNAL (rdtsc bracket inside helper) explicit. |
| 24 | Mirror-function call-sequence enumeration | PASS | Phase A Step A.4 CSV at `plan_checks/2026-05-25-B4-boot-call-sequence-enumeration.csv` is authoritative source. v1.5 D1 drift catches + v1.7.3 N-6 body-args + v1.7.4 NEW-1..4 fabrications all reflect comprehensive enumeration discipline at amendment time. |
| 25 | TECH_DEBT.md surface-area scan | PASS | TECH_DEBT-119 CLOSE / -120+-122 PARTIAL CLOSE / -121+-123+-124 status unchanged / NEW -125 (D1-C defer) OPENED. Auto-write contract section explicit. |
| 26 | DEFERRED-FOR-FUTURE-SHIP placeholder | PASS | D1-C lifecycle-event action_fn_ptr dispatch DEFERRED via TECH_DEBT-125 with explicit re-visit trigger (≥2 events share signature OR cohort ≥6). |
| 27 | DESIGN_SPECS pattern-application | YELLOW-WITH-FIT-GAP | All applicable patterns cited (slow-path-gate-registry, canonical-sister-extension, branchless-dispatch, shared-helper-extract). **GAP — no DESIGN_SPEC for "full-surface-deletion vs preserve-and-deprecate" decision framework** to cite for B-full scope; sister to `structural-fix-preferred-decision-framework.md` but distinct (deletion-side). Recommend v1.7.5 cite or queue NEW DESIGN_SPEC at Phase D close. |
| 28 | Test-strength anti-regression | PASS | Verification gate at lines 1242-1248 uses `==` for count-precision (`3,210-3,215`) but `>=` for cohort-coverage assertions; no test deletion claims; cohort sweep cases ADD vs WEAKEN. |
| 29 | Mechanical citation drift discipline | YELLOW-LANDED-FOR-v1.7.4 | v1.7.5 inline-update at WIP-11 fixed primary cite (`:3044-3311` → `:2834-3101`). B-Plus v0.3 line-anchor reports 14 drifts + 6 notfounds — 3 canonical /trace-deps findings already addressed; 11 remain in amendment history references (operator-judgment retain per `feedback_proportionate_response_to_audit_findings`). Acceptable. |
| 30 | Predicate-contract-changed audit | PASS | D1-B applies slow-path-gate cache pattern to breakeven for FIRST TIME (v1.7.3 N-3 reframe corrected from "cosmetic-extension"). Predicate evaluates to same value as direct cfg read at slow-path-budget cost; non-regressive. Sister consumer pattern verified at :2344 + :3558. |
| 31 | Wider-build verification | PASS | 6 build dirs explicit at Verification gate row 1: build/ + build_gui/ + build_lat/ + build_tsan/ + build_asan/ + build_suite/. WIP-7/8/11 already PASS; Phase B Step B.6 explicit gate. |
| 32 | Plan-body symbol-existence (B-Plus CI tool) | PASS | B-Plus v0.3 EXIT 0 on v1.7.4 plan body (per frontmatter Line 657 verification status). 6 REAL Class 14 fabrications were CAUGHT + CORRECTED at v1.7.4 cycle. Tool installed as pre-commit hook. Structural M7 enforcement WORKING. |
| 33 | M6 body-content arg enumeration | PASS-WITH-RECOMMEND-FOR-v1.7.5 | v1.7.3 N-6 captured 9-arg SlowPathCycleOneCore signature via /trace-deps + /dod-audit + /readiness + /bug-check convergent finding; BookSnapshot sister-canonical reuse per D8. M6 codified; CSV at `plan_checks/2026-05-25-B4-slow-path-lambda-body-enumeration.csv` authoritative. **RECOMMEND for v1.7.5: B-full WIP-13 scope needs comparable enumeration for deletion-side** — `engine_arch != ENGINE_ARCH_PER_CORE_SLOW` branch body content + 3 sister wrapper body content (cohort-deletion safety per F17) |
| 34 | Audit tier declared in frontmatter + scope match | PASS | `audit_tier: HIGH-RISK` declared line 5; matches actual scope (slow-path-body + cross-cutting + multi-surface deletion + framework-level M5/M6/M7 promotions). 5-agent comprehensive cadence applied; re-audit at SUBSTANTIVE amendment (v1.7.3 + v1.7.5) per discipline. |

---

## Cold-pickup completeness (C.1-C.10)

| # | Field | Verdict | Notes |
|---|-------|---------|-------|
| C.1 | Branch state | PASS | `feat/v5.15-live-readiness` named explicitly (line 36 + handoff) |
| C.2 | Phase execution order matches dependency | PASS | Phases A→B→C→D linear; v1.7.5 D17 captures 3-WIP cadence WIP-12 C.4 / WIP-13 B-full / WIP-14 C.4.5 / Phase D close |
| C.3 | First concrete move (Step 0) | PASS | Pre-tag rollback anchor `pre-v5.15.5.F.4d.1.B.4`; Step 0 line 668. v1.7.5 first move = amend plan body capturing v1.7.5 scope (per C25). |
| C.4 | Function/constructor names cited | PASS | 5 helpers explicitly named with full signatures; FOREACH_SLOW_PATH_GATE row name `BREAKEVEN_ON_PROFIT`; `BACKTEST_REGIME_SAMPLE_CORE` constant; all sister-canonical functions verified at HEAD |
| C.5 | File:line refs for cited tests/baselines | PASS-WITH-RESIDUAL | Plan body cites file:line for ~50+ symbols; v1.7.5 inline-update at WIP-11 corrected main span; residual 11 amendment-history line refs (operator-judgment retain) acceptable per B-Plus drift report |
| C.6 | Stale-claim audit | PASS | I spot-checked at HEAD `e0acb65`: `EngineCommon_*` 5 helpers EXIST (lines 154/183/235/476/806); `BookSnapshot<F>` EXISTS at BinanceDepth.hpp:29; `cfg.engine_arch` branches EXIST (8 sites verified); `book_imbalance`/`current_spread`/`current_mid_price` POINTER types verified in ShardedBacktestDriver.hpp:102/119/120 |
| C.7 | Effort claims reconcile with file size deltas | PASS | Helper bodies match plan estimates: ApplyBnbDiscount ~15-20 LOC (landed), BootGlobal ~20-30 LOC (landed), BootPerCore ~100-180 LOC (landed), SlowPathCycleOneCore ~200-350 LOC (landed ~260 LOC). Net engine -223 LOC at WIP-11. |
| C.8 | Source-audit references | PASS | Plan_checks artifacts at: 2026-05-25-B4-boot-call-sequence-enumeration.csv / -static-scope-enumeration.csv / -slow-path-lambda-body-enumeration.csv / 9 audit synthesis reports across v1.0→v1.7.4 |
| C.9 | Predecessor / dependent plans named with paths | PASS | predecessor: `v5.15.5.F.4d.1.B.3` (with full plan path); successor: `.B.5`; sub_master + sibling_umbrella both cite full path |
| C.10 | Tag names locked | PASS | Pre-tag + ship tag `v5.15.5.F.4d.1.B.4` named; rollback anchor at Step 0 |

**Verdict:** GREEN cold-pickup (10/10 PASS) — fresh session can pick up at v1.7.5 amendment from current artifacts.

---

## Future-oriented plan template required sections (per feedback_new_plans_use_future_oriented_template)

| Section | Verdict | Notes |
|---|---|---|
| Design space + future-oriented choice | YELLOW-INCOMPLETE-FOR-v1.7.5 | v1.7.4 articulates Decision A (5-helper split rationale); Decision F (named constant for PARITY-031); Decision G (statics in caller); Decision H (refs vs nullable `*`). **MISSING for v1.7.5:** explicit "Decision I — full surface deletion vs preserve-and-deprecate for engine_arch" articulating WHY full deletion is preferred (D18 captures the operator framing but plan body needs the architectural-merit articulation: legacy single_core LIVE engine preserves centralized semantics; SHARDED-mode `engine_arch=centralized` is genuinely redundant; per `feedback_motivated_collaborator_for_caramel` cleanest deprecation; per `feedback_no_defer_for_effort` no defer-to-future-ship) |
| Canonical sister registries considered | YELLOW-INCOMPLETE-FOR-v1.7.5 | v1.7.4 well-articulated for ApplyBnbDiscount sister (`Sharded_ValidatePartialExitCfg`) + BookSnapshot reuse + FOREACH_SLOW_PATH_GATE row-add. **MISSING for v1.7.5:** sister deletion patterns considered (e.g., legacy single_core LIVE preservation as architectural sister — cite explicitly per operator framing "we already have a preserved single core trading system"); B-full sister wrapper cohort deletion sister (F17 captures rationale but plan body needs to cite the cohort-deletion-prevents-Class-18-recurrence linkage) |
| Bug classes this closes | PASS-WITH-MINOR-ADD-FOR-v1.7.5 | v1.7.4 lists Class 18 + 21 + 24 + NEW Class 33 candidate. **ADD for v1.7.5:** Class 18 cohort wrapper deletion prevention per F17 — wrappers EventLoop_TimeExit / EventLoop_TrailingSLRatchet / EventLoop_BreakevenOnProfit become dead after B-full deletion; not cohort-deleting risks future Class 18 recurrence (someone re-fires from cleanup ship). |
| DESIGN_SPECs landed-amended | PASS | Comprehensive list at "DESIGN_SPECs landed / amended" section; Stage 2→3 promotions explicit; v1.7 D3 structural amendments captured; M5 + M6 + M7 codification + sister memory + skill amendments + CLAUDE.local.md row |
| Verification gate | PASS-WITH-MINOR-ADD-FOR-v1.7.5 | 6 build dirs + 3217 tests + B-Plus exit 0 + objdump byte-equivalence + double-fire grep gates + parity_harness regression + HMAC byte preservation + slow-path latency-neutral micro-benchmark. **ADD for v1.7.5:** post-B-full grep `engine_arch` returns ZERO non-historical hits in source + 8-branch deletion verified at EngineSharded.hpp + 3 sister wrapper deletion verified at ControllerEventLoop.hpp |
| TECH_DEBT auto-write contract | PASS | TECH_DEBT-119/120/122/125 explicit + auto-write at ship close + NEW v1.7 D3 structural fix entries CLOSED at Phase D Steps D.6-D.10 + plan-context-sweep .B.5-.B.11 amendment as OPENED separate cycle |
| Pre-coding triggers | PASS | All audit gates fired + verification status checked at "Pre-coding triggers (audit gate) — VERIFICATION STATUS" section; 11 gates accounted for through v1.7.4 |
| **End goal** | PASS-WITH-MINOR-ADD-FOR-v1.7.5 | v1.7.4 declares "Close the train-serve execution-layer Class 18 mirror structurally" + acceptance criteria + how this contributes to sprint MASTER. **ADD for v1.7.5:** end goal expansion to include "Close `engine_arch=centralized` SHARDED-mode deprecation by full surface deletion" + acceptance criteria for B-full (post-B-full grep returns ZERO; 3 wrapper cohort dead; cfg field gone; TUISnapshot field gone; GUI display unconditional). |
| **Operator migration impact** | GAP-FOR-v1.7.5 | **MUST ADD for v1.7.5 per feedback_surface_operator_migration_path_proactively:** B-full deletion is breaking change for any user with `engine_arch=centralized` in their cfg files. Migration impact section must articulate: (a) `engine_arch=centralized` users will see cfg parser unknown-key warning at next boot (current parser handling); (b) SHARDED mode `engine_arch=per_core_slow` users (default since v5.0+; the v5.15.x established default) UNAFFECTED — code path becomes unconditional; (c) legacy single_core LIVE binary (NOT the SHARDED engine) PRESERVES centralized execution semantics for users wanting non-sharded; (d) no schema bump needed (cfg parser tolerates unknown keys per existing convention); (e) GUI DashboardPanels engine_arch indicator goes away (display-side cleanup at WIP-13) |

---

## Hidden scope detected (v1.7.5 amendment scope)

| # | Surface | Effort estimate | Source |
|---|---|---|---|
| 1 | B-full SHARDED `engine_arch=centralized` deprecation | 8 branches in EngineSharded.hpp (lines 1438/1453/1625/1637/1660/1695/1718/2484) + 3 sister wrappers in ControllerEventLoop.hpp (lines 3435/3722/3796-3804) + cfg field at ControllerConfig.hpp + parser entry at :2800-2810 + ENGINE_ARCH_* constants + CfgFieldRegistry.hpp row + TUISnapshot.engine_arch field at EngineTUI.hpp + GUI DashboardPanels.hpp gating at lines 2165/2211/2214/2261/2274/2311/2324/2338/2357/2373 = ~14-16 file touches. Effort ~4-6h focused (mechanical + verify). | F16 + F17 + C28 |
| 2 | v1.7.5 plan body amendment itself | Substantive amendment per C25; comparable cycle to v1.7.3 (CRITICAL+HIGH+MED). ~2-3h focused. | C25 |
| 3 | Full 5-agent re-audit at v1.7.5 | /precoding-audit-gate + /blindspot-scan + /bug-check + /trace-deps + /readiness per HIGH-RISK Check 34 | C26 |

Total v1.7.5 + remaining Phase C/D scope: ~10-15h focused (~2-3 days) before ship close. Plan estimate at frontmatter line 29 needs amendment for v1.7.5 scope.

---

## Top gaps recommended for v1.7.5 amendment

| # | Gap | Section to amend | Priority |
|---|---|---|---|
| **G1** | Operator migration impact section MISSING for B-full deletion | NEW section after "How this contributes to sprint MASTER goal" | CRITICAL (per `feedback_surface_operator_migration_path_proactively`) |
| **G2** | Decision I — full surface deletion vs preserve-and-deprecate articulation | "Design space + future-oriented choices" — add Decision I | HIGH |
| **G3** | Canonical sister cite — legacy single_core LIVE engine preservation as architectural sister | "Canonical sister registries considered" — add row + rationale | HIGH |
| **G4** | Class 18 cohort wrapper deletion prevention rationale (F17) | "Bug classes this ship closes" — extend Class 18 entry | HIGH |
| **G5** | Verification gate — B-full grep `engine_arch` returns ZERO + 8-branch + 3 wrapper deletion gates | "Verification gate" — add 3-4 new mechanical rows | HIGH |
| **G6** | End goal expansion to include B-full closure | "Ship end goal" — extend statement + acceptance criteria | MED |
| **G7** | Phase C.4 expansion to capture WIP-12 C.4 BACKTEST migration distinctly from WIP-13 B-full | "Phase C — Caller migration" — split Step C.4 into C.4 + C.4.B-full | MED |
| **G8** | NEW Phase WIP-13 step capturing B-full deletion sequence + rollback granularity | "Phase C — Caller migration" — add Step C.B-full or rename | MED |
| **G9** | TECH_DEBT auto-write — close `engine_arch=centralized` deprecation at this ship; update FEATURE_LOOKUP entry | TECH_DEBT + FEATURE_LOOKUP sections | LOW |
| **G10** | Audit cycle log — v1.7.4 → v1.7.5 entry capturing scope expansion + re-audit firing | NEW v1.7.5 amendment summary section at top (per existing convention) | LOW (mechanical) |
| **G11** | DESIGN_SPEC gap — no canonical "full-surface-deletion-vs-preserve" decision framework | Recommend queue NEW DESIGN_SPEC at Phase D close (or cite `feedback_backwards_compat_not_default_concern` memory as sufficient codification for v1.7.5) | LOW |
| **G12** | M6 body-content enumeration extended to B-full deletion-side (sister to v1.7.3 N-6 extract-side enumeration) | NEW Phase A Step A.6.5.c verifying B-full deletion comprehensive enumeration completeness | MED (per `feedback_enumerate_helper_signature_args_before_extract` extended to deletion-side; analog to v1.4 N5 struct-member discipline) |

---

## Sister DESIGN_SPECS that should be cross-referenced in v1.7.5 plan body

| DESIGN_SPEC | Why cite |
|---|---|
| `meta-disciplines/canonical-sister-extension-discipline.md` | Already cited; reinforce for B-full deletion (legacy single_core sister) |
| `meta-disciplines/structural-fix-preferred-decision-framework.md` | Already cited at v1.7; reinforce for B-full deletion-side (deletion as structural fix vs preserve-and-deprecate as discipline-application) |
| `framework-patterns/slow-path-gate-registry-pattern.md` | Already cited at D1-B v1.7; no change needed |
| `meta-disciplines/body-content-enumeration-at-plan-time-discipline.md` (Stage 2 DRAFT) | EXTEND v1.7.5 to capture deletion-side enumeration (sister to extract-side; analog to v1.4 N5 struct-member discipline) |
| `meta-disciplines/structural-enforcement-when-memory-insufficient.md` (M7 Stage 3 first-canonical) | Cross-ref B-Plus v0.3 line-anchor extension as M7 second canonical (per F14 + C21 already captured in decision log) |
| `refactor-patterns/branchless-dispatch-discipline.md` (H20) | Cross-ref the "removing entire if-branch surfaces" as cleaner-than-keeping-branchless-but-conditional — eliminating branches by deletion is the cleanest form of branchless discipline |
| Memory `feedback_backwards_compat_not_default_concern.md` (codified 2026-05-26 at D18 closure) | EXPLICITLY cite as the going-forward rule justifying full surface deletion (operator preference codified; this ship is first canonical application) |

---

## Recommendations

### Must fix before WIP-12 coding (v1.7.5 amendment scope)

1. **Add Operator migration impact section** (G1) — CRITICAL per `feedback_surface_operator_migration_path_proactively`
2. **Add Decision I — full surface deletion vs preserve-and-deprecate** (G2) with architectural-merit articulation citing operator framing + legacy single_core LIVE preservation + `feedback_backwards_compat_not_default_concern` memory
3. **Add canonical sister cite for legacy single_core LIVE preservation** (G3)
4. **Extend Class 18 entry to capture cohort wrapper deletion prevention** (G4)
5. **Add verification gate rows for B-full grep gates** (G5)
6. **Extend ship end goal to include B-full closure** (G6)
7. **Fire full 5-agent re-audit at v1.7.5 spec** (C26) — HIGH-RISK Check 34 cadence

### Worth fixing during WIP-12/13 coding

8. **Split Phase C.4 into C.4 + C.B-full** (G7+G8) — gives clear WIP-12 vs WIP-13 boundary
9. **Add Phase A Step A.6.5.c for B-full deletion-side enumeration** (G12) — sister to extract-side discipline

### Acceptable risk (don't block)

10. **Queue NEW DESIGN_SPEC for full-surface-deletion-vs-preserve at Phase D** (G11) — operator memory + this ship's first canonical may be sufficient codification; promote to DESIGN_SPEC only if recurs ≥2nd cohort

---

## Verdict: YELLOW

**Rationale:**
- v1.7.4 LOCKED state is structurally GREEN for in-flight WIP execution (WIPs 1-11 LANDED; Phase B body coding COMPLETE; Phase C.1+C.2+C.3 LANDED)
- v1.7.5 PLANNED scope (D16/D17/D18 + F13-F19 + C25-C30) is COMPREHENSIVELY ARTICULATED in decision log, but plan body amendment is PENDING
- Plan body needs SUBSTANTIVE amendment incorporating G1-G6 (CRITICAL + HIGH gaps) BEFORE WIP-12 coding
- Full 5-agent re-audit at v1.7.5 spec is properly captured (C26) per HIGH-RISK Check 34
- B-Plus v0.3 + 3217 tests + 6 build dirs + B-Plus exit 0 + cold-pickup 10/10 + 34/34 checks substantively PASS (with v1.7.5-amendment-pending caveat)
- No SHIP-BLOCKING issues; YELLOW captures "amendment-cycle-needed-before-substantive-coding" status per HIGH-RISK discipline

**Next concrete action:** Operator triages this readiness report → applies G1-G12 amendments to plan body at v1.7.5 → fires full 5-agent re-audit (C26) → triages re-audit findings + applies amendments → operator GREEN → WIP-12 coding unlocks.

---

## Map-update suggestions (post-verify)

- **CODE_MAP.md regen** — 5 NEW EngineCommon_* functions LANDED at WIPs 1-11; `EngineCommon_ApplyBnbDiscount`, `_BootGlobal`, `_BootPerCore`, `_SlowPathCycleOneCore`, `_SlowPathCycleAllCores`. Run `./tools/gen_code_map.sh` at Phase D ship close.
- **INVARIANTS_MAP.md update** — M5 Stage 3 first canonical promotion; new invariant claim (train-serve execution-layer parity) needs test row in INVARIANTS_MAP.
- **FOREACH_REGISTRY (H15 meta-registry)** — verify `FOREACH_SLOW_PATH_GATE` row enrollment at `MetaRegistry.hpp` after BREAKEVEN_ON_PROFIT row addition; CI Check `test_meta_registry_coverage` should pass.

---

**End of /readiness report — v5.15.5.F.4d.1.B.4 v1.7.5 pre-amendment gate** — 2026-05-26
