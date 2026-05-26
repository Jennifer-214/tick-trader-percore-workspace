---
type: audit-report
audit_skill: /blindspot-scan
target_plan: plans/v5.15-live-readiness/subplans/2026-05-24-v5.15.5.F.4d.1.B.4-train-serve-execution-layer-parity.md
target_plan_version: v1.7.4 → v1.7.5 PLANNED (D15-D18 + F13-F19 + C25-C30 transition scope per decision-logs/2026-05-24-v5.15.5.F.4d.1.B.4-v1.7.4.md)
audit_tier: HIGH-RISK
audit_scope: pre-coding gate (WIP-11 boundary → WIP-12/13/14 unlock)
engine_head: e0acb65 (WIPs 7-11 ahead of origin)
established: 2026-05-26
verdict: YELLOW (5 SILENT-RISK + 2 LOAD-BEARING-LOUD + 4 IRRELEVANT + 1 N-A; 2 NEW pillar candidates surfaced)
---

# /blindspot-scan report — `.B.4` v1.7.5 pre-amendment gate — 2026-05-26

## Summary

- **Plan target:** v5.15.5.F.4d.1.B.4 train-serve execution-layer parity structural extract; v1.7.5 SUBSTANTIVE amendment cycle pending (D15-D18 + F13-F19 + C25-C30 carry-forward from v1.7.4)
- **Trigger justification:** Multi-surface deletion (8 LIVE branches + 3 cohort wrappers + cfg field + parser entry + 2 constants + TUISnapshot field + GUI gating + boot-spawn gate) crosses 5+ files; cohort wrapper deletion = sister deletion; 9 SHAPE audit cycles preceded (v1.0 → v1.7.4) — M4 inflection signal per `feedback_iteration_spiral_signals_audit_meta_gap`
- **Pillars fired:** 12 of 12 (B1-B12) plus 2 NEW pillar candidates evaluated (B14 + B15)
- **GUARDED-BY-BUILD:** 1 (B7)
- **SILENT-RISK:** 5 (B2 / B8 / B9 / B14-NEW / B15-NEW)
- **LOAD-BEARING-LOUD:** 2 (B12 / B7-secondary at test surface)
- **IRRELEVANT:** 4 (B4 / B5 / B6 / B10)
- **N-A:** 1 (B11)

## Per-pillar verdicts

| Pillar | Verdict | Finding | Action |
|---|---|---|---|
| **B1** type-change cascade | IRRELEVANT | No struct field type changes proposed; `uint8_t engine_arch` field deleted entirely (not type-shifted) | None |
| **B2** field-name collision | **SILENT-RISK** | Sibling field `cfg.engine_mode` (also uint8_t HAS_SIDE_EFFECT IS_BOOT_ONLY) preserved. PRE-existing test (`tests/controller_test.cpp:1735`) verifies HAS_SIDE_EFFECT mask aggregate `≥4 bits` listing 8 fields incl. `engine_arch`. After deletion, the test STILL passes (≥4 with 7 remaining) BUT the comment string becomes stale ("includes engine_arch" claim). Future operator extending the cohort can't grep for the literal string match. SILENT cosmetic drift. | Pre-coding amend: remove `engine_arch` from comment + audit any other comment-pinned references via `rg -F "engine_arch" tests/` (currently 4 occurrences, all in v5.0.4 topology field stability test block + 1 in HAS_SIDE_EFFECT aggregate test) |
| **B3** transitional state coexistence | IRRELEVANT | Plan is full surface deletion (D18); no SOURCE+TARGET coexistence window. WIP-12 (C.4 BACKTEST) + WIP-13 (B-full) + WIP-14 (C.4.5) are sequenced with commit-anchors; no transitional state at any commit boundary. | None |
| **B4** Surface G applicability | IRRELEVANT | No registry struct-gen changes; pure deletion. | None |
| **B5** compile-time scaling | IRRELEVANT | Net -LOC; instantiation count drops (fewer engine_arch dispatch branches expanded into template body). Build time should DECREASE. | None |
| **B6** STORAGE_T variant coverage | IRRELEVANT | No new STORAGE_T variants; uint8_t row deleted. | None |
| **B7** include topology cycle | **GUARDED-BY-BUILD** (primary); **LOAD-BEARING-LOUD** (secondary at test surface) | **Primary GUARDED:** No new include edges; pure deletion (header `ControllerConfig.hpp:88-89` constants removed; `DataStream/EngineTUI.hpp:951` field removed; `BinanceDepth.hpp` ↔ `EngineCommon.hpp` edge already established at WIP-11). Compile fails loud if any orphaned `ENGINE_ARCH_*` reference remains. **Secondary LOAD-BEARING-LOUD:** test surface at `tests/controller_test.cpp:1735` (HAS_SIDE_EFFECT aggregate count test) + `:8721-8772` (4× TUI_PopulateTopology / engine_arch round-trip tests). Updating mid-coding requires rebuild of 25k-line test file = ~30-60s × N attempts. **Pre-coding amendment recommended.** | Pre-coding: enumerate 4 test sites at `tests/controller_test.cpp:8721-8772` + 1 aggregate test at `:1735`; plan body amendment "Step W (WIP-13): delete topology engine_arch tests + adjust aggregate-count comment" |
| **B8** type-sensitive consumer classification | **SILENT-RISK** | Per-site classification of 21 enumerated cfg.engine_arch consumers (8 LIVE EngineSharded branches + 1 cfg parser block + 2 constants + 1 TUISnapshot field + 8 GUI gating sites + 1 TUI_PopulateTopology param) + cohort wrappers (3 sites at ControllerEventLoop.hpp:3435/3722/3796) NOT YET enumerated as TYPE-SENSITIVE-READ / TYPE-SENSITIVE-WRITE / TYPE-AGNOSTIC. **Specific risks:** (a) `cfg.engine_arch` is read via `!=`/`==` ENGINE_ARCH_PER_CORE_SLOW literal in 8 LIVE branches → TYPE-SENSITIVE-READ × 8 (delete entire `if` block, not just predicate); (b) `s->engine_arch == 1` literal-1 comparison in GUI (8 sites) → TYPE-SENSITIVE-READ × 8 (delete entire branch since centralized=0 case becomes dead); (c) TUI_PopulateTopology signature drops `uint8_t engine_arch` 2nd param → TYPE-SENSITIVE-WRITE × 1 callsite at EngineSharded.hpp:1773 + 2 test callsites at controller_test.cpp:8731/8766; (d) `cfg.engine_arch = ENGINE_ARCH_PER_CORE_SLOW` parser assignment → TYPE-SENSITIVE-WRITE × 2 (delete entire `if` block). | Pre-coding amendment: produce CSV at `plan_checks/2026-05-26-B4-engine-arch-consumer-classification.csv` per M6 body-content discipline; cite in v1.7.5 plan body C.4/B-full step. Sister to v1.7.3 N-6 9-arg body-args enumeration discipline (M6 first canonical). |
| **B9** unverified audit claim | **SILENT-RISK** | D18 framing "full surface deletion is cleaner" relies on assumption that all 21+ consumer sites are TYPE-AGNOSTIC-deletable. /trace-deps comprehensive enumeration at C.4 pre-coding gate (F16/F19) verified 8 LIVE branches + 3 sister wrappers but did NOT cite file:line evidence for the 8 GUI gating sites (`GUI/DashboardPanels.hpp:2036/2085/2165/2202/2211-2216/2261/2274/2311-2373` mapped to 10+ visible references). One uncited claim drives WIP-13 scope. | Pre-coding: verify-cite each GUI deletion site in v1.7.5 plan body (`GUI/DashboardPanels.hpp:2165/2261/2274/2311/2324/2338/2357/2373` are `s->engine_arch != 1` or `== 1` branches; verify each becomes unconditional-active or unconditional-dead post-deletion; 4 of 8 sites guard "centralized-arch-only" rendering — these become DEAD CODE on per_core_slow-default → DELETE; 4 guard "per_core_slow-only" rendering → UNCONDITIONALIZE) |
| **B10** struct layout drift | IRRELEVANT | TUISnapshot is double-buffered via seqlock (`TUISnapshot_Publish_Begin/End`); NOT in HMAC/wire/memcmp/SHA byte-equivalence context. Field deletion is layout-cosmetic only. H12 inapplicable. | None |
| **B11** if-constexpr template context | N-A | No new `if constexpr` filter walker proposed; existing FOREACH_SLOW_PATH_GATE row `BREAKEVEN_ON_PROFIT` already landed at WIP-7 inside template fn (already template-context-correct). | None |
| **B12** cross-registry row ordering | **LOAD-BEARING-LOUD** | engine_arch row deletion at `CfgFieldRegistry.hpp:396` (FOREACH_GLOBAL_CFG_FIELD) → field index shift for all rows AFTER engine_arch (rows :397+). FIELD_IDX_GLOBAL_<name> indices recompute. Stamp wire-format key ORDERING may shift (engine_arch was HAS_SIDE_EFFECT — manual parser; registry walker skipped it; but Layer 5b structural invariants verify stamp body emit by master registry declaration order; if any STAMP_BOUND_CFG_DERIVED row exists at index > engine_arch's slot, its order index shifts). | Pre-coding: verify NO STAMP_BOUND_CFG_DERIVED row index changes by inspecting `g_global_cfg_field_descriptors[FIELD_IDX_GLOBAL_engine_arch]` references + checking Layer 5b invariants tolerate the shift OR confirm shift is no-op (engine_arch is NOT STAMP_BOUND-tagged; its deletion shouldn't affect Layer 5b key ordering for STAMP_BOUND fields). |

## NEW pillar candidates surfaced

### B14-NEW — Multi-surface deletion ordering across files

**Definition:** When a feature surface spans ≥3 files (cfg field declaration + manual parser entry + N consumer branches + cohort wrappers + UI display gating + tests), the DELETION ORDER across commits matters. Wrong order → mid-deletion commit fails to compile.

**Detection mechanism:**
- Enumerate all consumer sites by include-graph topology
- Sort by "leaves first" (UI + tests → consumers → manual parser → cfg field declaration → constants)
- Plan body MUST annotate per-WIP deletion ordering OR commit as ONE atomic WIP (no intermediate commits)

**Specific risks for v1.7.5 B-full:**
- If WIP-13 deletes `cfg.engine_arch` field FIRST → cfg parser entry `:2802-2807` referencing `cfg.engine_arch = ...` compile-fails
- If WIP-13 deletes manual parser `:2802-2807` FIRST → cfg.engine_arch field becomes effectively unreachable (cosmetic) but still references valid struct; compile clean
- If WIP-13 deletes `ENGINE_ARCH_CENTRALIZED`/`ENGINE_ARCH_PER_CORE_SLOW` constants FIRST → 8 LIVE branches + parser + boot-spawn gate + EngineCommon comment + test fixture references compile-fail
- If WIP-13 deletes 8 LIVE EngineSharded branches FIRST → constants become unused but valid; compile clean
- If WIP-13 deletes TUISnapshot::engine_arch field FIRST → GUI 8 sites + 4 tests + TUI_PopulateTopology fn + EngineSharded:1773 caller compile-fail

**Recommended ordering for atomic WIP-13:** (leaves first → root last)
1. Tests (4 sites at `controller_test.cpp:8721-8772` + 1 aggregate comment at `:1735`)
2. GUI gating (8 sites at `GUI/DashboardPanels.hpp:2036/2085/2165/2202/2211-2216/2261/2274/2311-2373`)
3. 8 LIVE EngineSharded branches (`:1438/:1453/:1625/:1637/:1660/:1695/:1718-1744`)
4. 3 sister wrappers (`ControllerEventLoop.hpp:3435/3722/3796`) — caller sites at LIVE :1722/:1724/:1730 deleted at step 3 already; backtest sites at `ShardedBacktestDriver.hpp:378/380/383` deleted at WIP-12 already
5. EngineSharded.hpp:1773 TUI_PopulateTopology caller — drop `cfg.engine_arch` arg
6. DataStream/EngineTUI.hpp:1874 TUI_PopulateTopology signature — drop `uint8_t engine_arch` param + body :1883 assignment
7. DataStream/EngineTUI.hpp:951 TUISnapshot::engine_arch field declaration
8. EngineSharded.hpp:2484 boot-spawn-gate — unwrap `if (cfg.engine_arch == ENGINE_ARCH_PER_CORE_SLOW) {...}` (closes at `:2882`; ~398 LOC scope; unwrap means remove the `if` + 1-level indent strip ~398 lines)
9. ControllerConfig.hpp:2802-2807 manual parser entry — delete entire `if (strcmp(key, "engine_arch") == 0)` block
10. CfgFieldRegistry.hpp:396 — delete FOREACH_GLOBAL_CFG_FIELD row
11. ControllerConfig.hpp:88-89 — delete ENGINE_ARCH_CENTRALIZED + ENGINE_ARCH_PER_CORE_SLOW constants
12. Comment cleanup: 6 cited locations in ControllerConfig.hpp (lines 77 / 79 / 81 / 968 / 1840 / 1844 / 2800) + comments in EngineCommon.hpp:44 + OrderManager.hpp:261 + EngineSharded.hpp:1217/1849/2464/2469 + EngineTUI.hpp:992/1199/1481/1865/2036/2085/2202/2214/2216 + Backtest comment + Version.hpp:66

**Loud vs silent:** LOUD (compile failure if order wrong; commit-by-commit verification possible). Pre-coding ordering enumeration prevents wasted rebuild cycles.

**Detection guard recommendation:** New /readiness Check 35 — "Multi-surface deletion ordering enumeration at plan-time when deletion crosses ≥3 files." (Stage 2 DRAFT; codify at this ship as worked example with B14 row in this taxonomy.)

**Verdict: SILENT-RISK** at plan-body layer (ordering NOT annotated in v1.7.4 D17/D18); LOUD at coding layer. Pre-coding amendment recommended.

---

### B15-NEW — Unconditional-by-default semantic shift via gate unconditionalization

**Definition:** When a boolean cfg-gate (e.g., `if (cfg.engine_arch == ENGINE_ARCH_PER_CORE_SLOW)`) is REMOVED via `if (true)` simplification (the gate predicate becomes always-true), the formerly-gated block ALWAYS executes. This is a SEMANTIC SHIFT for any cohort that historically set the gate to FALSE (centralized cohort in this case). Latent assumptions in the formerly-gated block — assumptions that the block ran ONLY when the gate was TRUE — silently become wrong for the no-longer-existent cohort.

**Detection mechanism:**
- For each gate-deletion site, enumerate latent assumptions in the formerly-gated block
- Verify each assumption either (a) remains true post-deletion OR (b) is documented as "was only true when cfg.X = Y; now always" with consequences

**Specific risk for boot-spawn-gate `:2484`:** The `if (cfg.engine_arch == ENGINE_ARCH_PER_CORE_SLOW) { ... spawn N slow-path threads ... }` block at :2484-2882 currently spawns slow-path threads ONLY when per_core_slow is selected. Under the centralized cohort, threads were NOT spawned + the centralized arch path (the 8 branches at :1438+/-) handled slow-path work inline on the producer thread.

After B-full deletion of centralized arch + unconditionalization at :2484:
- Slow-path threads ALWAYS spawn (good — desired behavior)
- Producer thread NO LONGER does inline slow-path work (good — the 8 branches deleted at step 3 above)
- **Latent assumption check:** What downstream code assumed "slow-path threads exist"? Anything that previously had `if (cfg.engine_arch == ENGINE_ARCH_PER_CORE_SLOW)` predicate guarding access to slow-path thread state (e.g., `slow_paths.emplace_back(...)` vector size, per-core slow_state allocation, slow-path latency stats)?

**Likely consequence:** Pretty much none — per_core_slow has been the DEFAULT since v5.0+ (per CLAUDE.md "Legacy single_core LIVE is deprecated"; per registry row `INT(1, 0, 1)` default `=1`). The centralized cohort was already a corner case maintained for opt-out. But latent assumption walk should still be performed.

**Loud vs silent:** SILENT for assumption-violation case (no compile error; runtime behavior change may not surface until specific cohort runs). LOUD only if formerly-gated block has compile-time assertion of the gate predicate.

**Detection guard recommendation:** Pre-coding amendment: enumerate "latent assumptions in the formerly-gated block at :2484-2882" + verify each. Worth codifying as B15 in this taxonomy (sister to B14 multi-surface deletion ordering).

**Verdict: SILENT-RISK** (latent assumption enumeration not in v1.7.4 plan body). Pre-coding amendment small (~10-20 min walk through the 398-LOC scope at :2484-2882; document any non-obvious "this used to be conditional" assumptions).

---

## Punch-list (ordered by severity)

1. **(B12 LOAD-BEARING-LOUD)** Verify FIELD_IDX_GLOBAL_engine_arch deletion does NOT shift STAMP_BOUND_CFG_DERIVED row indices that affect wire-format key ordering. (~15 min: grep `STAMP_BOUND_CFG_DERIVED` rows in FOREACH_GLOBAL_CFG_FIELD; verify all are at index < engine_arch row OR none exist at index > engine_arch row OR Layer 5b invariants tolerate index shift OR confirm `engine_arch` row's deletion doesn't affect STAMP_BOUND ordering. Effort ≤30 min.)

2. **(B14-NEW SILENT-RISK)** Add deletion ordering enumeration to v1.7.5 WIP-13 plan body. Annotate 12-step sequence (tests → GUI → LIVE branches → wrappers → TUI_PopulateTopology callers → signature → field → boot-spawn-gate → manual parser → registry row → constants → comments). (~30 min amendment.)

3. **(B7 LOAD-BEARING-LOUD secondary)** Plan body amendment "Step W (WIP-13.A): delete 4 topology tests at `tests/controller_test.cpp:8721-8772` + adjust HAS_SIDE_EFFECT aggregate comment at `:1735`." Prevents mid-coding test file rebuild cycle (~30-60s × N catches). (~10 min amendment.)

4. **(B8 SILENT-RISK)** Produce CSV at `plan_checks/2026-05-26-B4-engine-arch-consumer-classification.csv` enumerating 21+ consumer sites with TYPE-SENSITIVE-READ / TYPE-SENSITIVE-WRITE / TYPE-AGNOSTIC classification. Sister to M6 v1.7.3 N-6 body-args discipline. (~45 min enumeration.)

5. **(B9 SILENT-RISK)** Cite each GUI deletion site at `GUI/DashboardPanels.hpp:2165/2261/2274/2311/2324/2338/2357/2373` in v1.7.5 plan body WIP-13 step with UNCONDITIONALIZE vs DELETE-AS-DEAD-CODE classification. (~15 min enumeration.)

6. **(B15-NEW SILENT-RISK)** Walk boot-spawn-gate `:2484-2882` 398-LOC scope; enumerate any "this used to be conditional on per_core_slow" assumptions. Likely no findings but cost ~10-20 min to verify. (Insurance step.)

7. **(B2 SILENT-RISK)** Refresh `tests/controller_test.cpp:1735` HAS_SIDE_EFFECT aggregate comment to drop engine_arch from listed fields (cosmetic; would otherwise leave stale comment). (~5 min mechanical.)

## Recommended next move

Operator decision matrix:

| Option | Action | Effort | Verdict |
|---|---|---|---|
| **(A)** Audit-first | Apply all 7 punch-list amendments to v1.7.5 plan body BEFORE WIP-12 coding | ~2-3h amendment cycle | RECOMMENDED — HIGH-RISK ship + 2 NEW pillar candidates surfaced; pre-coding amendment cost << mid-coding rebuild cost |
| **(B)** Coding with annotations | Land amendments 1-3 (B12 + B14 + B7-secondary; the LOUD/blocking ones); defer 4-7 to WIP coding-time enumeration | ~1h amendment cycle; ~30-60 min × 7 mid-coding catches | NOT-RECOMMENDED for HIGH-RISK; mid-coding catches break audit-tier discipline per `feedback_consult_on_audit_findings` |
| **(C)** Defer 1+2+3 to inline at WIP coding | Skip plan-body amendment; rely on /trace-deps coverage + B-Plus CI tool catch | ~0 amendment; UNBOUNDED rebuild cycle cost if any LOUD finding surfaces mid-coding | REJECT per `feedback_no_defer_for_effort` + HIGH-RISK tier discipline |

**Recommended next move: Option A (audit-first amendment cycle).**

## Inflection check

Per `feedback_iteration_spiral_signals_audit_meta_gap`:

- **Iteration count since last meta-gap codification:** 4 (M4 at .B.3 / M5 at .B.4 boot extract / M6 at .B.4 v1.7.3 body-args / M7 at .B.4 v1.7.4 B-Plus CI tool)
- **NEW pillars surfaced this fire:** **2** (B14 multi-surface deletion ordering + B15 unconditional-by-default semantic shift)
- **Meta-gap signal:** YES — 2 NEW pillars on a single fire signals existing 12-pillar taxonomy needs expansion for the DELETION class of structural fix (taxonomy was originally codified for ADDITION + MIGRATION classes — 12 pillars all assume code is being ADDED or TRANSFORMED, not bulk-DELETED). DELETE-class operations have distinct blind-spot shapes.
- **Recommendation:** Amend `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` Stage 3 with B14 + B15 rows at this ship close (Phase D). Sister to M5/M6/M7 promotions per decision-log C12 (DESIGN_PHILOSOPHY § 11.5 M1-M7 catch-up).

## Cross-references

- Plan body: `plans/v5.15-live-readiness/subplans/2026-05-24-v5.15.5.F.4d.1.B.4-train-serve-execution-layer-parity.md` (v1.7.4 → v1.7.5 transition)
- Decision log: `plans/v5.15-live-readiness/decision-logs/2026-05-24-v5.15.5.F.4d.1.B.4-v1.7.4.md` (v1.7.5 transition section D15-D18 + F13-F19 + C25-C30)
- Sister audit: `plan_checks/2026-05-25-v5.15.5.F.4d.1.B.4-v1.6-blindspot-scan.md` (v1.6 prior fire; B1-B12 walk at struct-gen migration class)
- Engine HEAD: `e0acb65` (WIPs 7-11 ahead of origin)
- Engine code refs cited:
  - `CoreFrameworks/EngineSharded.hpp:1438/:1453/:1625/:1637/:1660/:1695/:1718-1744/:1773/:2484-2882`
  - `CoreFrameworks/ControllerConfig.hpp:77/79/81/88-89/968/1840/1844/2800/2802-2807`
  - `CoreFrameworks/CfgFieldRegistry.hpp:396`
  - `CoreFrameworks/ControllerEventLoop.hpp:3435/3722/3796`
  - `DataStream/EngineTUI.hpp:951/992/1199/1481/1865/1874-1883`
  - `GUI/DashboardPanels.hpp:2036/2085/2165/2202/2211-2216/2261/2274/2311-2373`
  - `tests/controller_test.cpp:1735/8721-8772`
  - `CoreFrameworks/EngineCommon.hpp:44`
  - `CoreFrameworks/OrderManager.hpp:261`
  - `Version.hpp:66`

**End of report. Operator triage required before WIP-12 coding unlock per audit-first recommendation + HIGH-RISK tier per audit_tier frontmatter.**
