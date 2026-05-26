---
type: audit-report
audit: merge-scan
scope: v1.7.5 PENDING amendment scope for ship v5.15.5.F.4d.1.B.4
plan_body: 2026-05-24-v5.15.5.F.4d.1.B.4-train-serve-execution-layer-parity.md
decision_log: 2026-05-24-v5.15.5.F.4d.1.B.4-v1.7.4.md
ship_tag: v5.15.5.F.4d.1.B.4
engine_head: e0acb65 (WIP-11)
established: 2026-05-26
audit_skill: /merge-scan
audit_tier: HIGH-RISK (per plan body frontmatter)
focus: v1.7.5 SUBSTANTIVE amendment scope (B-full SHARDED deprecation + Phase C.4 BACKTEST migration + Phase C.4.5 PARITY-031 ordering)
---

# /merge-scan — v5.15.5.F.4d.1.B.4 v1.7.5 PRE-amendment gate

## Stage 0 DESIGN_PHILOSOPHY preload

- § 4 (Latency cost framework) — reuse-audit principle for shared atomic loads / cfg accesses / clock reads on slow-path-cycle migrated body
- § 7 (Structural-fix family) — sister-canonical extension over invention; cohort deletion as registry analog at AllCores-wrapper layer

## Scope

This scan focuses on the **PENDING v1.7.5 amendment scope** (per decision log v1.7.4 → v1.7.5 transition D15-D18 + C25-C30 + F13-F19):

1. **WIP-13 B-full SHARDED `engine_arch=centralized` FULL-SURFACE deletion** (D16+D18) — 8 conditional branches + 3 sister wrappers + cfg field + parser entry + 2 constants + TUISnapshot field + GUI gating
2. **WIP-12 Phase C.4 BACKTEST migration** — `EngineCommon_SlowPathCycleAllCores` call ADD + ShardedBacktestDriver trio DELETE
3. **WIP-14 Phase C.4.5 PARITY-031 ordering closure** — `fc_ctx.regime_state` field deletion + `BACKTEST_REGIME_SAMPLE_CORE = 0` read replacement

Plus reuse opportunities surfacing post-extract from the 5 EngineCommon helpers + B-Plus CI tool v0.3 + caller-precompute math discipline.

---

## 1. Cohort-enumeration efficiency for v1.7.5 deletion sweep

### MERGE-NOW-1 — `cfg.engine_arch` deletion is a CANONICAL "cohort-delete" sweep (Class 21 / Class 18 sister)

**Status:** MERGE-NOW (single-grep enumeration; not N separate site-by-site checks)

The v1.7.5 scope cites 11+ distinct sites that all delete because the same registry-row symbol vanishes:

| Surface | Site | Count |
|---|---|---|
| EngineSharded.hpp negated branches | `:1438 / :1453 / :1625 / :1637 / :1660 / :1695 / :1718` | 7 (NOT 8 — plan body's "8 conditional branches" off-by-one; `:2484` is positive-form boot-spawn gate) |
| EngineSharded.hpp positive boot-spawn gate | `:2484` (`if (cfg.engine_arch == ENGINE_ARCH_PER_CORE_SLOW)`) | 1 (unconditionalize block) |
| EngineSharded.hpp TUI_PopulateTopology arg | `:1773` | 1 (arg drop; sister to GUI display field delete) |
| ControllerEventLoop.hpp AllCores wrappers | `:3435 EventLoop_TimeExit / :3722 EventLoop_TrailingSLRatchet / :3796 EventLoop_BreakevenOnProfit` | 3 (cohort delete per F17) |
| ControllerConfig.hpp constants | `:88 ENGINE_ARCH_CENTRALIZED / :89 ENGINE_ARCH_PER_CORE_SLOW` | 2 |
| ControllerConfig.hpp cfg parser | `:2800-2810` (parser entry) | 1 |
| ControllerConfig.hpp cfg field declaration + doc comments | `:77-89` (cfg field comment block + `:968` + `:1003` + `:1840-1844` + `:2800` parser) | 1 cfg field + 4 doc comment blocks |
| CfgFieldRegistry.hpp registry row | `:396` row + `:266` doc reference | 1 row deletion + 1 doc text update |
| TUISnapshot field | `EngineTUI.hpp:951` + populate at `:1481/:1875/:1883` + 2 doc refs `:992/:1199/:1865` | 1 field delete + 4 populate site updates + 3 doc comment blocks |
| GUI DashboardPanels.hpp gating | `:2036` doc + `:2085` doc + `:2165 / :2211 / :2214 / :2216 / :2261 / :2274 / :2311 / :2324 / :2338 / :2357 / :2373` 11 branches | 13 sites (1 cfg display + 9-10 conditional UI dispatch) |
| tests/controller_test.cpp | `:1735` doc text + `:8721-8740 / :8767-8768` topology tests | 1 doc text + 2 test sections (REWRITE topology test fixtures) |
| Version.hpp + README.md | docs | 2 mentions (refresh) |
| engine.cfg.example | `:422` + `:435` + `:438` + `:910` | 4 lines (1 active config + 3 doc) |
| EngineCommon.hpp doc comment | `:44` | 1 doc text |
| OrderManager.hpp doc comment | `:261` | 1 doc text |

**Total deletion footprint:** ~51 distinct sites across 10 files.

**MERGE proposal:** instead of v1.7.5 plan body listing all 51 sites in a giant enumeration block (per `feedback_enumerate_consumers_before_registry_row_deletion` worst-case interpretation), use the **canonical-cohort-deletion** discipline:

```
1. Run ONE comprehensive grep at plan body amendment time:
   rg -n "engine_arch\b|ENGINE_ARCH_(CENTRALIZED|PER_CORE_SLOW)" \
       /home/caramel/code/FoxML_Trader_v2/ \
       --type-not md --type-not log

2. Output 51-site grep result becomes Appendix A artifact at plan_checks/
   (sister to v1.5 Phase A boot-call-sequence-enumeration.csv pattern).

3. Plan body cites artifact + summary table (NOT enumeration) — sister to
   v1.5 D3 21-static enumeration discipline.
```

**LOC savings (plan body):** ~150-250 LOC of enumeration body → 1 paragraph + artifact cite.

**Cohort enumeration efficiency:** consistent with `feedback_enumerate_consumers_before_registry_row_deletion` extended-to-struct-member discipline + matches v1.5 D1/D3 pattern + matches v1.6 O1 BootPerCore signature enumeration pattern. **The discipline is "ONE grep into ONE CSV artifact, not 51 prose enumerations in plan body."**

---

### MERGE-NOW-2 — 3 sister wrappers `EventLoop_TimeExit / TrailingSLRatchet / BreakevenOnProfit` ARE the canonical Class 18 mirror cohort

**Status:** MERGE-NOW (already in plan v1.7.5 scope per F17)

The 3 wrappers at `ControllerEventLoop.hpp:3435/3722/3796` ALL have IDENTICAL caller pattern: only called from `EngineSharded.hpp:1722/1724/1730` (centralized arch trio) + `ShardedBacktestDriver.hpp:378/380/383` (BACKTEST trio). Post-WIP-12 + WIP-13:
- BACKTEST trio (`:378/:380/:383`) → DELETED, replaced by SlowPathCycleAllCores wrapper
- LIVE centralized trio (`:1722/:1724/:1730`) → DELETED with the surrounding `if (cfg.engine_arch != ENGINE_ARCH_PER_CORE_SLOW)` block at `:1718`
- LIVE per_core_slow path → already uses OneCore variants (canonical)

All 3 wrappers become DEAD CODE. Cohort-delete prevents Class 18 future drift.

**Grep verification (run pre-WIP-13):**
```
rg -n "EventLoop_TimeExit\b|EventLoop_TrailingSLRatchet\b|EventLoop_BreakevenOnProfit\b" \
    /home/caramel/code/FoxML_Trader_v2/ \
    --type cpp --type-add 'hpp:*.hpp'
# Expected post-deletion: 0 hits (excluding ControllerEventLoop.hpp wrapper definitions which also delete)
# Pre-deletion HEAD shows: 9 hits total (3 wrapper definitions + 3 LIVE + 3 BACKTEST + 1 test doc comment)
```

VERIFIED at HEAD `e0acb65` — only 1 test mention exists at `tests/controller_test.cpp:18010` which references `EventLoop_TimeExitOneCore` (the OneCore variant, NOT AllCores wrapper). Tests don't reference AllCores wrappers. SAFE TO COHORT-DELETE.

**LOC savings:** ~50 LOC across 3 wrapper bodies + 3 declaration sites in ControllerEventLoop.hpp.

---

### MERGE-NOW-3 — Single-grep deletion order verification for v1.7.5 WIP-13 cohort

**Status:** MERGE-NOW (deletion ordering enforcement saves ~3 separate verify passes)

Per F19, B-full deletion is DELETE-SAFE provided 4 amendments stick. Per `feedback_enumerate_consumers_before_registry_row_deletion`, run ONE post-deletion verification pass not multiple:

```bash
# Single post-WIP-13 grep pass replacing multiple per-surface verifications:
rg -n "engine_arch\b|ENGINE_ARCH_(CENTRALIZED|PER_CORE_SLOW)" \
    /home/caramel/code/FoxML_Trader_v2/ \
    --type-not md --type-not log

# Expected: 0 hits OR limited hits in pre-existing markdown comments preserved
# during deletion (e.g., historic CHANGELOG/postmortem refs)
```

Sister: WIP-12 BACKTEST trio deletion + WIP-13 B-full LIVE trio deletion are SAME-SHAPE — `EventLoop_TimeExit\|EventLoop_TrailingSLRatchet\|EventLoop_BreakevenOnProfit` returns ZERO hits across CoreFrameworks/ + Backtest/ post-both WIPs. ONE grep gate for both.

---

## 2. Caller-precompute pattern consistency (O2 bytewise-identical math) — VERIFY across LIVE + BACKTEST

### KEEP-VERIFY-1 — LIVE Step C.1 + BACKTEST Step C.2 caller-precompute math IS bytewise-identical post-WIP-9

**Status:** KEEP-with-VERIFY (post-WIP-9 + WIP-11 land; before WIP-12 BACKTEST C.4 lands)

Both LIVE caller migration (Step C.1 at `EngineSharded.hpp:898-906 + :915-920` per v1.6 O2) and BACKTEST caller migration (Step C.2 at `BacktestSharded.hpp:234-238 + :258-263` per v1.6 O2) preserve the SAME 12-line precompute block:

```cpp
double total_balance = FPN_ToDouble(cfg.starting_balance);
double default_risk = FPN_ToDouble(cfg.risk_pct);
if (default_risk <= 0.0) default_risk = 0.10;
double default_per_core = (total_balance * default_risk) / (double)num_cores;
if (default_per_core < 1.0) default_per_core = 1.0;

for (int c = 0; c < num_cores; ++c) {
    double core_balance = default_per_core;
    if (!FPN_IsZero(cfg.core_risk_pct[c])) {
        core_balance = total_balance * FPN_ToDouble(cfg.core_risk_pct[c]);
        if (core_balance < 1.0) core_balance = 1.0;
    }
    // ... helper call
}
```

**Reuse-merge proposal NOT recommended** because both occurrences serve different arch-specific arg-passing contexts (LIVE uses `aligned_alloc` heap ML zoo; BACKTEST uses static array ML zoo). Extracting into a 5th-arg-helper would conflict with O2 discipline (helper-internal recompute could diverge from caller's clamp logic per v1.6 O2 rejection of Option C).

**Verification gate (at v1.7.5 amendment):** `diff <(rg -A 7 -B 0 "default_per_core" EngineSharded.hpp) <(rg -A 7 -B 0 "default_per_core" BacktestSharded.hpp)` should show only 1 type-prefix difference (`FPN<F>` vs `FPN<BACKTEST_FP>`). 

Status at HEAD `e0acb65`: VERIFIED via WIPs 9 + 11 — both blocks preserved verbatim per O2.

---

### MERGE-LATER-1 — Per-cycle scalar resolution for SlowPathCycleAllCores (BACKTEST sister-pattern for LIVE Step C.3)

**Status:** MERGE-LATER-AT-WIP-12 (canonical sister-pattern to LIVE; consistency check)

LIVE Step C.3 caller resolution at WIP-11 (verified at `EngineSharded.hpp:2843-2868`):

```cpp
double price_d = last_price.load(std::memory_order_relaxed);
double volume_d = last_volume.load(std::memory_order_relaxed);
FPN<F> price = price_d > 0.0 ? FPN_FromDouble<F>(price_d) : FPN_Zero<F>();
FPN<F> volume = volume_d > 0.0 ? FPN_FromDouble<F>(volume_d) : FPN_Zero<F>();
uint64_t ts_us = (uint64_t)std::chrono::duration_cast<std::chrono::microseconds>(
    std::chrono::system_clock::now().time_since_epoch()).count();
int dactive = __atomic_load_n(&g_depth_shared.active_idx, __ATOMIC_ACQUIRE);
const BookSnapshot<F>& depth = g_depth_shared.snapshots[dactive];
EngineCommon_SlowPathCycleOneCore(cfg, c, state, oms, price, volume, ts_us, now_tick, depth);
```

BACKTEST sister at WIP-12 (per plan body v1.7.4 Step C.4 caller block lines 1041-1072) resolves differently because BACKTEST runs single-threaded synchronous tick callback:

```cpp
FPN<BACKTEST_FP> price  = tick.price;             // from tick struct directly
FPN<BACKTEST_FP> volume = tick.volume;
uint64_t now_tick = (uint64_t)tick_index;          // from tick counter
uint64_t ts_us    = tick.timestamp;                // from tick struct (v1.7.4 RE-FIRE-2 fix)
BookSnapshot<BACKTEST_FP> depth = BookSnapshot_Init<BACKTEST_FP>();
if (drv && drv->book_imbalance)    { depth.imbalance = *drv->book_imbalance; }
if (drv && drv->current_spread)    { depth.spread    = *drv->current_spread; }
if (drv && drv->current_mid_price) { depth.mid_price = *drv->current_mid_price; }
EngineCommon_SlowPathCycleAllCores(cfg, state, oms, price, volume, ts_us, now_tick, depth);
```

**MERGE proposal NOT recommended** — LIVE caller has producer-thread `last_price/volume` + `system_clock::now()` clock read + `g_depth_shared` static atomic load; BACKTEST has synchronous tick + tick_index. Per `feedback_audit_canonical_sister_before_new_infra` Stage 4 cohort threshold "≥50% overlap + same consumer behavior" — caller-resolution contexts genuinely differ. Helper signature unifies (already bytewise-identical math via 9-arg signature with `BookSnapshot<F>` sister-canonical). Caller scalar resolution stays arch-specific.

**Reuse-verification:** ensure BACKTEST `BookSnapshot_Init<BACKTEST_FP>()` exists at HEAD before WIP-12 lock — if NOT, plan body needs amendment to construct snapshot via field-by-field assignment from drv pointers (sister to LIVE's `g_depth_shared.snapshots[dactive]` direct ref usage). VERIFIED at HEAD `e0acb65`: function exists per `DataStream/BinanceDepth.hpp` BookSnapshot template.

---

## 3. EngineCommon 5-helper extract — sister opportunities post-extract

### KEEP-AS-IS-1 — 5 EngineCommon helpers represent inflection point per feedback_framework_layer_payoff_diminishing_returns

**Status:** KEEP-AS-IS (no further extraction)

The 5 helpers at `CoreFrameworks/EngineCommon.hpp` (831 LOC) close 7 PARITY entries (026-032) by eliminating ~150-250 LOC of duplicated boot + slow-path-cycle code across LIVE + BACKTEST. Per `feedback_framework_layer_payoff_diminishing_returns`, the extract reaches the inflection point — further extraction would target small-duplication territory.

**No sister opportunities surfacing** for further helpers from train↔serve mirror surface:
- DepthRecorder/Notify worker/trade_log STAY in caller per M5 LIVE-only persistence sink false-positive surface
- CoreLatencyStats_Enable STAYS in caller per M5 threading observability LIVE-only
- bandit_state_prior_path override STAYS in caller per Decision B external wrapper

Per `feedback_framework_layer_payoff_diminishing_returns` "stop at inflection" — 5 helpers is the natural boundary. NEXT-natural-boundary candidate is v6.0 viewer split (covered at decoupling roadmap, not this ship).

---

### MERGE-DEFER-1 — Lifecycle-event action_fn_ptr dispatch (TECH_DEBT-125)

**Status:** DEFER (already opened as TECH_DEBT-125 at v1.7 L1)

D1-C (extend FOREACH_SLOW_PATH_GATE with action_fn_ptr column for uniform lifecycle-event dispatch) deferred per OneCore signature divergence — TimeExit (6 args incl oms*/now_tick), TrailingSLRatchet (5 args incl rolling), BreakevenOnProfit (4 args minimal) — genuinely divergent inputs make uniform fn_ptr premature generalization.

**Revisit when:** ≥2 events share signature OR cohort grows ≥6 events OR uniform-dispatch ROI clear. Not actionable at v1.7.5 amendment.

---

## 4. B-Plus CI tool v0.3 — sister opportunities

### MERGE-DEFER-2 — B-Plus CI tool v0.3 line-anchor mode at COMMIT layer

**Status:** DEFER (M7 structural enforcement evolves; not v1.7.5 scope)

WIP-10 landed B-Plus v0.3 with line-anchor verification extension (~150 LOC Python) covering D15 closure for F13/F14 line-anchor drift detection.

**Sister-extension opportunities** (per F14 "structural enforcement evolves as gaps surface"):
- Macro-call signature consistency check (already cited at v1.7.3 N-15 + Phase D Step D.6 v1.7.4 scope — pending WIP-X)
- DESIGN_SPECS cross-ref existence check (validate `sister_specs:` frontmatter links resolve at commit time)
- Plan body amendment_history monotonic ordering check (catches missing v1.X entries)

**Not v1.7.5 scope** — these are M7 evolution surface tracked via TECH_DEBT or future ship. v1.7.5 is FOCUS on engine-side scope expansion. Sister memory `feedback_structural_enforcement_when_memory_insufficient` already documents the "extend B-Plus per gap" discipline.

---

## 5. TUISnapshot field deletion — "deleted-field grep sweep" pattern

### KEEP-AS-IS-2 — `engine_arch` TUISnapshot field deletion follows existing canonical pattern

**Status:** KEEP-AS-IS (no new merge needed; canonical pattern in place)

Per `feedback_enumerate_consumers_before_registry_row_deletion` extended-to-struct-member discipline (v1.5 + N5 sister), the post-deletion grep sweep is mechanical:

```bash
# Sister to v1.5 D1 / v1.7.3 N-4 / v1.7.4 NEW-1..NEW-4 grep gates:
rg -n "snap->engine_arch|TUISnapshot.*engine_arch|->engine_arch\b" \
    /home/caramel/code/FoxML_Trader_v2/ \
    --type cpp --type-add 'hpp:*.hpp'
# Expected post-deletion: 0 hits
```

Plus tests need updating per `controller_test.cpp:8721-8768` (topology round-trip test fixtures must drop engine_arch from struct + remove the engine_arch round-trip check). Per `feedback_test_strength_audit` (if exists) OR /test-strength-audit pre-WIP-13 sweep, the test deletions need rationale (test fixtures dropping field is fine; deleting actual ASSERTIONS without rationale is not).

**No new pattern needed** — existing M6 (body-content arg enumeration) + Class 18 (mirror state) disciplines cover this. The "deleted-field grep sweep" is mechanical post-amendment verification.

---

## 6. NEW finding (NOT a merge candidate; pre-amendment alert)

### ALERT-1 — Plan body cites "8 conditional branches at :1438/:1453/:1625/:1637/:1660/:1695/:1718/+:2484" but actual is 7 NEGATED branches + 1 POSITIVE boot-spawn gate

**Status:** Surface at v1.7.5 amendment (mechanical correction; NOT a merge candidate)

Decision log F16 + plan body frontmatter v1_7_5_transition state "8 conditional branches at EngineSharded.hpp:1438/1453/1625/1637/1660/1695/1718/+2484 boot-spawn-gate" — verified at HEAD `e0acb65`:
- `:1438 / :1453 / :1625 / :1637 / :1660 / :1695 / :1718` — 7 negated branches (`if (cfg.engine_arch != ENGINE_ARCH_PER_CORE_SLOW)`)
- `:2484` — 1 POSITIVE boot-spawn gate (`if (cfg.engine_arch == ENGINE_ARCH_PER_CORE_SLOW)`)
- Total: 7 + 1 = 8 SITES BUT NOT all "conditional branches" — `:2484` is the boot-spawn-gate that UNCONDITIONALIZES post-deletion (the block body becomes unconditionally executed)

**Suggested phrasing for v1.7.5 amendment:** "8 cfg.engine_arch consumer sites in EngineSharded.hpp: 7 negated conditional branches (`!=PER_CORE_SLOW`) at `:1438/:1453/:1625/:1637/:1660/:1695/:1718` DELETE-with-block-bodies; 1 positive boot-spawn gate (`==PER_CORE_SLOW`) at `:2484` UNCONDITIONALIZE-block-body."

Also missed sites in F16 enumeration:
- `:1773` — `TUI_PopulateTopology(bs, cfg.engine_arch, ...)` argument (deletes with TUISnapshot.engine_arch field)
- `:1217 / :1849` — comment-only references (re-write or drop)
- `:2506/:2515/:2521/:2526` — `fprintf` log strings mentioning `engine_arch=per_core_slow` (drop arch-specific wording after unconditionalize)

**This is an ALERT not a MERGE candidate** — flagging mechanical drift for v1.7.5 amendment cycle to catch BEFORE coding starts.

---

## 7. NEW finding — TUI_PopulateTopology signature mutation cohort enumeration

### ALERT-2 — Removing `engine_arch` arg from TUI_PopulateTopology cascades to caller updates

**Status:** Surface at v1.7.5 amendment (sister to ALERT-1)

`DataStream/EngineTUI.hpp:1874-1883` shows `TUI_PopulateTopology(snap, engine_arch, ...)` signature; called from `EngineSharded.hpp:1773`. Post-WIP-13 B-full deletion, the `engine_arch` arg is dropped from the signature + the caller signature changes.

Plus `TUI_PopulateTopology` is called from tests (verified at `tests/controller_test.cpp:8721-8740`) — test fixtures need arg-list update sister to engine_arch struct field removal.

**Merge opportunity:** if TUI_PopulateTopology has other args ABOUT TO BE deprecated at later ships (e.g., per-core fields), batch the signature mutation. NOT applicable at v1.7.5 — single-arg drop here. Tracked as ALERT for v1.7.5 amendment cycle completeness.

---

## Top-3 highest-impact items to act on at v1.7.5 amendment

1. **MERGE-NOW-1 (cohort-enumeration sweep)** — Replace 150-250 LOC of prose-body enumeration in plan body Step C.4/B-full with ONE comprehensive grep + artifact CSV (sister to v1.5 D3 21-static enumeration pattern). Saves ~200 LOC plan body bloat + reduces drift-surface across v1.7.5 amendment cycle. Mechanical per `feedback_enumerate_consumers_before_registry_row_deletion`.

2. **ALERT-1 (mechanical correction)** — Reframe "8 conditional branches" → "7 negated branches DELETE + 1 positive boot-spawn gate UNCONDITIONALIZE" at v1.7.5 amendment. Plus add missed sites (`:1773 TUI_PopulateTopology arg + :2506/:2515/:2521/:2526 fprintf logs + :1217/:1849 comment refs`).

3. **MERGE-NOW-2 (cohort delete 3 sister wrappers)** — Already in plan v1.7.5 scope per F17; verify post-WIP-13 grep gate returns 0 hits. Confirms Class 18 mirror cohort closure structurally.

## Items deferrable to next sweep

- MERGE-DEFER-1 (TECH_DEBT-125 lifecycle-event fn_ptr dispatch)
- MERGE-DEFER-2 (B-Plus v0.3 sister extensions — macro-call signature / DESIGN_SPECS cross-ref / amendment history monotonic)

## Items to leave alone (intentional duplication or KEEP)

- KEEP-VERIFY-1 (LIVE + BACKTEST 12-line precompute block; bytewise-identical math discipline preserved)
- MERGE-LATER-1 (per-cycle scalar resolution for BACKTEST caller; arch-specific contexts genuinely differ from LIVE)
- KEEP-AS-IS-1 (5 EngineCommon helpers at framework-layer inflection point)
- KEEP-AS-IS-2 (TUISnapshot field deletion follows canonical pattern)

---

## Duplication risk in planned amendments (B-full + C.4 + C.4.5)

**Operator question:** "B-full + C.4 + C.4.5 separately or merged?"

**Answer:** SEPARATE per D17 3-WIP split — and NOT a duplication risk.

Rationale (re-stating + cross-checking):
- **WIP-12 C.4 BACKTEST migration** (CATASTROPHIC-risk: double-fire of TimeExit/TrailingSLRatchet/BreakevenOnProfit if AllCores wrapper insertion + LIVE-only delete are at different commits) — needs own rollback anchor
- **WIP-13 B-full SHARDED deprecation** (HIGH-risk: 51-site deletion footprint; sister wrapper cohort delete; cfg field + parser + constants removal) — needs own rollback anchor with FULL surface deletion semantic
- **WIP-14 C.4.5 PARITY-031 ordering** (LOW-MED-risk: 18-20 LOC delta; backtest regime sample ordering verification at fc_ctx.regime_state deletion) — needs own rollback anchor

The 3 WIPs touch DIFFERENT surfaces at DIFFERENT risk levels with DIFFERENT verification gates. Single fat commit would conflate:
- BACKTEST trio deletion (WIP-12) with LIVE trio deletion (WIP-13) — different consumers
- Sister wrapper deletion (WIP-13 F17 cohort) with feature collector struct member deletion (WIP-14)
- Cfg field/parser deletion (WIP-13) with regime sample ordering verification (WIP-14)

Per `feedback_no_defer_for_effort` + `feedback_motivated_collaborator_for_caramel`, separate WIPs with clear rollback anchors at each substantial change is the right move. Each WIP has its own grep verification gate per merge-scan MERGE-NOW-3.

**No duplication risk** between WIP-12 + WIP-13 + WIP-14 — each WIP closes a different scope. Cohort-enumeration efficiency (MERGE-NOW-1) reduces plan body LOC but doesn't change WIP separation.

---

## Cohort enumeration efficiency recommendations

1. **Adopt artifact CSV pattern for v1.7.5 amendment** — `engine_arch` deletion sites enumerated into `plan_checks/2026-05-XX-B4-engine-arch-deletion-enumeration.csv` (sister to v1.5 boot-call + static-scope CSVs). Plan body cites artifact; doesn't re-enumerate.

2. **Single-grep verification gates** — One grep covers all wrapper+constant+field+parser+TUISnapshot+GUI deletions post-WIP-13. Replace per-surface verify gates with one comprehensive sweep per `feedback_enumerate_consumers_before_registry_row_deletion`.

3. **Pre-amendment ALERT capture** — ALERT-1 + ALERT-2 mechanical drift surfaces at v1.7.5 amendment cycle BEFORE WIP-13 coding. Sister to v1.5 D1+D2+D3 mechanical drift catch discipline.

4. **B-Plus CI tool v0.3 line-anchor verification** — Already operational post-WIP-10; pre-WIP-13 plan body amendment runs B-Plus pre-commit hook + flags any drift in cited deletion sites. F13 closure infrastructure proven; reuse here.

---

## Overall recommendation

**MERGE-NOW count:** 3 (cohort-enumeration sweep + sister wrappers + single-grep verification gates)
**DEFER count:** 2 (TECH_DEBT-125 lifecycle fn_ptr / B-Plus v0.3 sister extensions)
**KEEP count:** 4 (12-line precompute block + per-cycle scalar resolution + 5 helpers at inflection + TUISnapshot deletion canonical pattern)
**ALERT count:** 2 (mechanical drift in v1.7.5 transition framing — 8 branches → 7+1 + missed sites including TUI_PopulateTopology arg + fprintf logs + comment refs)

**v1.7.5 amendment cycle should:**
1. Convert 51-site enumeration to artifact CSV reference (~200 LOC plan body savings)
2. Reframe ALERT-1 + ALERT-2 to correct enumeration discrepancies before WIP-13 coding starts
3. Document cohort grep gate as single-pass verification (replaces per-surface verify gates)
4. Carry F17 sister-wrapper cohort delete into WIP-13 explicit (already scoped at v1.7.4 transition)
5. Preserve 3-WIP split (D17); no merge between WIP-12 + WIP-13 + WIP-14

**Total LOC savings (plan body):** ~200-250 LOC via artifact CSV + grep-gate consolidation. Engine-side LOC savings (~50 LOC) from 3 sister-wrapper cohort delete already in scope.

**Inflection-point assessment** (per `feedback_framework_layer_payoff_diminishing_returns`): 5 EngineCommon helpers + 51-site `engine_arch` cohort delete REACH framework-discipline maturity for this surface. NEXT-natural-surface is v6.0 decoupling boundary at decoupling roadmap, not further extraction at this ship. v1.7.5 amendment scope is RIGHT-SIZED for the inflection point reached.

---

**End of /merge-scan v5.15.5.F.4d.1.B.4 v1.7.5 pre-amendment gate report.**
