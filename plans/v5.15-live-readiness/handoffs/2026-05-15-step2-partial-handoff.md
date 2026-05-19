# v5.15.5.F.4c.3 Step 2 PARTIAL — handoff prompt

**Created:** 2026-05-15
**Target ship:** v5.15.5.F.4c.3 — Architectural cfg split (global vs per-core registry); Class 24 + Class 25 structural closure
**Branch:** `feat/v5.15-live-readiness`
**Engine HEAD at handoff write:** `24a4aaf` (WIP2c.3)
**Workspace HEAD at handoff write:** `13462b4` (WIP2c.0; plus uncommitted plan-body progress note + this handoff being written)
**Plan file:** `/home/caramel/code/tick-trader-percore-workspace/plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3-global-vs-per-core-registry-split.md`
**Sprint MASTER:** `/home/caramel/code/tick-trader-percore-workspace/plans/v5.15-live-readiness/MASTER.md`

**Engine state at handoff write:**
- HEAD: `24a4aaf` (WIP2c.3)
- Branch: `feat/v5.15-live-readiness`
- Version.hpp: still `"5.15.5.F.4c.1"` (no version bump until full Step 2 + Step 3 ship)
- Tests: **3148 controller_test + 856 depth_recorder_test = 0 failures (GREEN)**
- Working tree: clean except `claude_session.md` (planning scratchpad; gitignored conceptually)
- Latest tags: `pre-v5.15.5.F.4c.3` (rollback anchor at original starting commit `88043ea`), `v5.15.5.F.4c.1`

**Sprint State Tracker (CLAUDE.local.md):** updated this session to reflect partial state.

---

## What's done — 7 commits this session

| Commit | Sub-step | Description |
|---|---|---|
| `61ff185` | WIP1 | Two-registry framework — `FOREACH_GLOBAL_CFG_FIELD` (47 rows) + `FOREACH_PER_CORE_CFG_FIELD` (79 rows initial) + templated `CfgMaskArray<N>` + per-registry mask arrays + `cfg_field_names_unique<N>` + PER_CORE_OK metadata bit REMOVED + 3 REMOVED rows dropped from registries (struct fields stay; pending WIP2f) |
| `22933ab` | WIP2a | `PerCoreCfg<F>` struct (79 fields, alignas(64), sizeof%64==0 + alignof==64 static_asserts) + `cores[MAX_EXECUTION_CORES]` field on `ControllerConfig<F>` |
| `fd67e6d` | WIP2b | `ControllerConfig_PopulateCoresFromFlat<F>` X-macro shadow walker; called at `Default()` + `Load()` end |
| `13462b4` (workspace) | WIP2c.0 | `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` § "Consumer function signatures over per-core slices" (NEW) + `RECURRING_BUG_PATTERNS.md` Class 25 (NEW) + plan body HIGH-1 amendment + `.F.4c.3.A` symbol axis stub note |
| `df1cb03` | WIP2c.1 | Classify-first — 10 un-classified per-core fields → registry + struct (strategy-TP-overrides + offset_stddev_mult + confidence_hard_block_threshold + ensemble_min_agreement_pct + barrier_blend_mode) + 5 bitmap storage fields cohort-moved to `PerCoreCfg<F>` |
| `49649b8` | WIP2c.2 | **Class 25 structurally closed.** 8 fn sigs migrate to `const PerCoreCfg<F>* core_cfg` exclusively (5 inner `_BuildParameters` + 1 `Strategy_BuildParameters` dispatcher + 2 helpers `Strategy_NotEnoughSpacing` + `Strategy_TpFloor`); 32 external call sites updated via verified perl substitution; `poll_interval_ticks` scalar arg propagates ML + dispatcher; 3 cohort additions (fee_rate_maker/_taker/foxml_vol_scaling_z_max) |
| `24a4aaf` | WIP2c.3 | Fix WIP2c.2 transient test failures — fee_rate_maker/_taker tagged HAS_SIDE_EFFECT (manual parser handles `explicit_set` flag for downstream legacy-mirror gate); 8 test blocks band-aided with `ControllerConfig_PopulateCoresFromFlat(&cfg)` post-mutation sync. **Tests GREEN: 3148 + 856 = 0 failures.** |

**Files modified across the 7 commits:**
- `CoreFrameworks/CfgFieldRegistry.hpp` (full rewrite at WIP1 + 13 row additions across WIP2c.1+c.2+c.3)
- `CoreFrameworks/ControllerConfig.hpp` (parser dual-registry walker + `PerCoreCfg<F>` declaration + `cores[16]` + `PopulateCoresFromFlat`)
- `CoreFrameworks/ControllerEventLoop.hpp` (3 call sites updated: Strategy_BuildParameters + Strategy_SpacingOk + Strategy_TpFloor)
- `CoreFrameworks/LegacyReferenceDriver.hpp` (1 call site)
- `Strategies/StrategyParameters.hpp` (8 fn sigs + ~45 `config->` → `core_cfg->` body refs via verified sed + ML scalar arg)
- `GUI/SettingsPanel.hpp` (GlobalCfgRenderTable + PerCoreCfgRenderTable + walker split)
- `tests/controller_test.cpp` (per-registry FIELD_IDX_GLOBAL_*/PER_CORE_* refs + ~25 `&cfg` → `&cfg.cores[0]` migrations + 8 band-aid populate calls)
- `experiments/per_core_sharding/test_strategy_parameters.cpp` (~8 `&config` → `&config.cores[0]` migrations)

**Workspace docs landed:**
- `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` — § "Consumer function signatures over per-core slices" (NEW; grep signatures for audit hooks)
- `DOCS/RECURRING_BUG_PATTERNS.md` — Class 25 catalog entry (NEW)
- `plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3-global-vs-per-core-registry-split.md` — HIGH-1 amendment + scope-discipline rationale (committed at WIP2c.0; progress note added in this handoff prep, uncommitted at time of writing)
- `plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3.A-symbol-axis-per-core-migration.md` — per-symbol consumer fn discipline note
- `plans/plan_checks/cfg-field-scope-classification-2026-05-15.md` — LOCKED at WIP2c.0

---

## What remains — Step 2 incomplete

| Sub-commit | Scope | Effort | Risk |
|---|---|---|---|
| **WIP2e** | A2 bitmap-bool expansion: 28 KIND_BOOL flat rows (12 ml + 3 lifecycle + 6 gate + 3 risk + 4 ops) + 28 `uint8_t` fields on `PerCoreCfg<F>` + decompose walker in `PopulateCoresFromFlat` (bitmap → flat rows during shadow window; direction reverses at WIP2g) | 1-2 hr | LOW (additive) |
| **WIP2d** | ~70 production read sites: `cfg.<per_core_field>` → `cfg.cores[c].<per_core_field>`. Files: `Backtest/BacktestSharded.hpp` (17), `ML_Headers/CfgDriftCheckRegistry.hpp` (17), `ML_Headers/CoreModelZoo.hpp` (12), `MemHeaders/DrainerConstants.hpp` (3), `main.cpp` (3), `ML_Headers/{StampHelper,ThompsonBandit,BanditAlgorithmRegistry,StampBoundModelConstRegistry,BarrierBlendModeRegistry,MlCfgFlagRegistry,FeatureStandardizer}.hpp` (small), `MemHeaders/FailureModeRegistry.hpp` (1), `CoreFrameworks/LiveReadiness.hpp` (1) | 2 hr | LOW (shadow keeps flat alive); could be done compile-error-driven AFTER WIP2g |
| **WIP2f** | Legacy deletion: `PerCoreOverrides<F>` struct + `PER_CORE_OVERRIDE_BITMAP_DOMAINS` + `core_overrides[16]` field + `ControllerConfig_ResolveForCore` + 3 REMOVED struct fields (`default_strategy` / `pay_fees_in_bnb` / `reconcile_dry_run`) + parser blocks for `core_N_<field>` syntax. Update `PopulateCoresFromFlat` direct-copy (no ResolveForCore call) | 1 hr | **MEDIUM** — legacy `core_N_<field>=` cfg syntax becomes non-functional until Step 3 ([core N] section parser) lands. Single-core unaffected. |
| **WIP2g** | Delete 89 flat per-core field declarations from `ControllerConfig<F>` | 30 min file edit + 3 hr cascade migration | **HIGH** — flag day; ~70 production + ~414 test sites break simultaneously |
| **WIP2h** | ~414 test fixture `cfg.<field> = ...` migration to `cfg.cores[0].X = ...`. 8 sites currently use `ControllerConfig_PopulateCoresFromFlat(&cfg)` band-aid (lines ~7568/7578/7593, ~8775/8788, ~9913, ~12349 in `tests/controller_test.cpp`) — convert to direct cores[0] writes here | bundled with WIP2g | mechanical volume |

**Architectural sequencing observation:** WIP2f deletes legacy `core_N_<field>=` parser → multi-core configs need `[core N]` section parser (Step 3) for replacement. WIP2f + Step 3 are co-dependent for multi-core operators. Pure-single-core operators unaffected by WIP2f alone.

---

## TaskList state at handoff write (preserve verbatim for fresh-session pickup)

| ID | Status | Subject |
|---|---|---|
| #1 | completed | Step 0.A — Tag rollback anchor + verify build baseline |
| #2 | completed | Step 0.C — Cfg field scope classification table |
| #3 | completed | Step 1 — Two-registry framework infrastructure |
| #4 | **in_progress** | **Step 2 — Cohort migration + ControllerConfig restructure** |
| #5 | pending | Step 3 — Parser state machine for [core N] sections |
| #6 | pending | Step 5 — Per-core stamp body emit + drift check |
| #7 | pending | Step 6 — Settings panel — Global tab + per-core tabs + Reset/Modified UI |
| #8 | pending | Step 7 — Backtest path + ~414 test fixture migrations |
| #9 | pending | Step 8 — DESIGN_SPECs Stage 2→3 + documentation |
| #10 | pending | Step 9 — Verification gate + ship close |

**Fresh-session pickup should recreate this TaskList** (via TaskCreate for each) so the multi-step plan stays trackable across sessions.

---

## Test state — CRITICAL for fresh-session pickup

- **All tests GREEN at WIP2c.3 (commit `24a4aaf`):** 3148 controller_test + 856 depth_recorder_test = 0 failures.
- **9 test sites use `ControllerConfig_PopulateCoresFromFlat(&cfg)` band-aid** for shadow-window staleness. Locations in `tests/controller_test.cpp` (approximate; grep `PopulateCoresFromFlat` to find exact post-edit lines):
  - P.4 partial-exit tests (3 sites; around 7568-7593): bitmap mutations of `cfg.lifecycle_cfg_flags` + `cfg.tp2_mult`
  - v5.1.10 fee-floor tests (2 sites; around 8775-8788): `cfg.take_profit_pct` + `cfg.fee_rate_taker` + `cfg.fee_rate` mutations
  - v5.4.0p2.2 state-aware MR (1 site; around 9913): `cfg.entry_offset_pct` + `cfg.offset_stddev_mult` + `cfg.volume_multiplier`
  - v5.9.2a SimpleDip tp/sl propagates (1 site; around 12349): `cfg.take_profit_pct` + `cfg.stop_loss_pct`
  - These are TRANSIENT — at WIP2g (flat field deletion) the band-aid calls become no-ops; WIP2h removes them entirely + replaces with direct `cfg.cores[0].X = ...` writes.

- **fee_rate_maker / fee_rate_taker HAS_SIDE_EFFECT in registry** — manual parser block at `CoreFrameworks/ControllerConfig.hpp:~2266` handles parsing + `explicit_set` flag for downstream legacy-mirror logic at `~3144`. **Don't remove HAS_SIDE_EFFECT from these without also removing the legacy-mirror logic.**

---

## Class 25 (NEW) — codification reference

**Title:** Scope-erosion in per-core consumer function (registry says per-core; consumer reads from wrong scope)
**Catalog:** `DOCS/RECURRING_BUG_PATTERNS.md` (NEW entry at WIP2c.0)
**Discipline spec:** `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` § "Consumer function signatures over per-core slices" (NEW at WIP2c.0)
**First canonical application:** `Strategies/StrategyParameters.hpp` 8-fn family (closed at WIP2c.2)
**Grep signatures (anti-pattern detection):**
```bash
# A1: Per-core consumer fn taking ControllerConfig<F>* (forbidden)
rg -n "(BuildParameters|_Tick|_Adapt|_Rebuild|_Step)\(.*const ControllerConfig<F>\*" --type cpp

# A2: Mixed-scope (PerCoreCfg<F>* param AND `config->` body reads)
rg -nP "(?s)PerCoreCfg<F>\*.*?config->[a-z_]+" --multiline --type cpp
```

---

## Paste this prompt into a fresh Claude Code session

```
I'm picking up v5.15.5.F.4c.3 (Architectural cfg split — global vs per-core registry) Step 2 PARTIAL state. 7 commits landed in `feat/v5.15-live-readiness`; tests GREEN; remaining: WIP2e/WIP2d/WIP2f/WIP2g/WIP2h mechanical migration sweep.

This is a fresh context window. Verify everything against current code; don't trust prior-session memory.

## Step 0 — orient + verify state (MANDATORY)

1. **SHA-diff trigger check** against handoff write-time anchor:
   - `git -C /home/caramel/code/FoxML_Trader_v2 rev-parse HEAD` → expect `24a4aaf` (WIP2c.3). If diverges, read `git log 24a4aaf..HEAD` for in-flight changes.
   - `git -C /home/caramel/code/FoxML_Trader_v2 log --oneline -10` → expect 7 WIP commits since `88043ea` (`v5.15.5.F.4c.1`).
   - `cat /home/caramel/code/FoxML_Trader_v2/Version.hpp` → expect `"5.15.5.F.4c.1"` (no bump yet; Step 2 partial).
   - `./build/controller_test 2>&1 | grep RESULTS:` → expect `3148 passed, 0 failed`.

2. **Read these in parallel (load context):**
   - `/home/caramel/code/FoxML_Trader_v2/CLAUDE.md` (slim; always-loaded orientation)
   - `/home/caramel/code/FoxML_Trader_v2/CLAUDE.local.md` (Sprint State Tracker → "In-progress ship: v5.15.5.F.4c.3 — Step 2 PARTIAL")
   - `/home/caramel/code/tick-trader-percore-workspace/plans/v5.15-live-readiness/subplans/2026-05-15-v5.15.5.F.4c.3-global-vs-per-core-registry-split.md` (THE plan body + "## Progress as of 2026-05-15" section at bottom — lists landed commits + remaining sub-commits)
   - `/home/caramel/code/tick-trader-percore-workspace/plans/v5.15-live-readiness/handoffs/2026-05-15-step2-partial-handoff.md` (THIS document — landed/remaining/test-state/Class 25)
   - `/home/caramel/code/tick-trader-percore-workspace/DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` (§ "Consumer function signatures over per-core slices" — the discipline that locked at WIP2c.2)
   - `/home/caramel/code/FoxML_Trader_v2/DOCS/RECURRING_BUG_PATTERNS.md` Class 25 (NEW; structural fix applied at WIP2c.2)
   - `/home/caramel/code/tick-trader-percore-workspace/plans/plan_checks/cfg-field-scope-classification-2026-05-15.md` (LOCKED classification table; 47 GLOBAL / 79 PER_CORE / 3 REMOVED + later 3 cohort additions)
   - `~/.claude/projects/-home-caramel-code-FoxML-Trader-v2/memory/MEMORY.md` (auto-memory index)

3. **Recreate the TaskList** from this handoff's TaskList table — use TaskCreate for each entry to preserve the multi-step plan tracking. Mark #1-#3 completed, #4 in_progress, #5-#10 pending.

4. **Required reading BEFORE writing code** (per CLAUDE.local.md):
   - `DOCS/STRATEGY_AND_CODING_RULES.md` (11 strict invariants; private)
   - `plans/_cross-cutting/2026-05-06-latency-path-discipline.md`
   - `DOCS/DESIGN_PHILOSOPHY.md` § 1.5 + § 3 + § 7 (framework discipline + hard invariants + structural-fix family)
   - Class 25 + cfg-scope-discipline.md § "Consumer function signatures"

## Step 1 — pick up at WIP2e (the next sub-commit)

Per the plan body progress note: WIP2e is the most architecturally bounded next step. A2 expansion adds 28 KIND_BOOL flat rows + decompose walker. Mechanics:

1. Enumerate bits from the 5 `FOREACH_<DOMAIN>_CFG_FLAG` registries (`MlCfgFlagRegistry.hpp` / `LifecycleCfgFlagRegistry.hpp` / `GateCfgFlagRegistry.hpp` / `RiskCfgFlagRegistry.hpp` / `OpsCfgFlagRegistry.hpp`).
2. Add 28 KIND_BOOL rows to `FOREACH_PER_CORE_CFG_FIELD` in `CoreFrameworks/CfgFieldRegistry.hpp`. Each row tagged HAS_SIDE_EFFECT (registry walker skips parse; bitmap is source of truth during shadow window).
3. Add 28 `uint8_t` fields to `PerCoreCfg<F>` in `CoreFrameworks/ControllerConfig.hpp` (group by domain).
4. In `ControllerConfig_PopulateCoresFromFlat`, add domain-by-domain decompose: `cfg->cores[c].<field> = BITMAP_IS_SET(resolved.<domain>_cfg_flags, MASK_<DOMAIN>_CFG_<NAME>) ? 1 : 0;` for each bit.
5. Build + test verify GREEN.
6. Commit WIP2e.

Alternative ordering: WIP2d/2f/2g/2h first (the mechanical migration sweep) before WIP2e (the A2 expansion). Trade-off: WIP2d/2g/2h compounds to flat-field deletion = structural payoff; WIP2e is additive + independent. Operator preference: consult Caramel.

## Step 2 — design check + consultation

Per `feedback_consult_on_audit_findings` going-forward rule: when surfacing structural questions (e.g., WIP2f deletion of legacy override path + multi-core regression until Step 3 ships), pause + consult Caramel before coding.

Pattern library reference: `DESIGN_SPECS/framework-patterns/per-instance-registry-pattern.md` (this ship's first canonical application) + `DESIGN_SPECS/refactor-patterns/cfg-scope-discipline.md` (the discipline framework).

## Step 3 — operator collaboration norms

- Address Caramel as Caramel / she / her.
- Don't use AskUserQuestion modal boxes. Present options inline.
- Evaluate options on robustness + latency + design philosophy, NOT time.
- After pre-coding checks, present findings + iterate BEFORE coding.
- Bump `Version.hpp` per ship when v5.15.5.F.4c.3 finally tags.

## Step 4 — verification gate at full Step 2 close

- All 5 binaries build: `./build.sh test gui suite tsan asan`
- `controller_test` ≥ 3148 (current GREEN baseline)
- `depth_recorder_test` 856/0
- Paper-trade 60sec sectioned cfg loads cleanly (Step 3 [core N] parser must ship in tandem for multi-core; single-core works post-WIP2g)
- `calls_graph_diff` confirms hot path bytewise-identical
- Architectural gates: `FOREACH_GLOBAL_CFG_FIELD` + `FOREACH_PER_CORE_CFG_FIELD` populated; `PerCoreCfg<F>` size aligned; `PerCoreOverrides<F>` + `core_overrides[16]` deleted; `ControllerConfig_ResolveForCore` deleted; 89 flat per-core fields gone

## Step 5 — ship-close (after Step 2 + Step 3 both done)

- `Version.hpp` 5.15.5.F.4c.1 → 5.15.5.F.4c.3
- Tag `v5.15.5.F.4c.3` annotated + signed
- Postmortem at `plans/v5.15-live-readiness/postmortems/<date>-v5.15.5.F.4c.3-postmortem.md`
- 4 DESIGN_SPECs Stage 2 → Stage 3 (per-instance-registry / cfg-scope-discipline / multi-action-registry-walker-family / cfg-section-parser-state-machine)
- CLAUDE.md item 31 update
- DESIGN_SPECS/README.md catalog count → 66
- CHANGELOG row
- `/sync-workspace`

Good luck. Caramel will iterate with you on findings. Per `feedback_consult_on_audit_findings`: present findings → list potential fixes → iterate → operator greenlights → THEN start coding.
```

---

## Closing notes for future-Claude

- The 5 commits between `61ff185` and `49649b8` represent the LOAD-BEARING STRUCTURAL WORK of this ship — Class 25 closure + per-core authoritative registry + strict single-param consumer discipline. The remaining sub-commits (WIP2e/2d/2f/2g/2h) are mechanical migration sweep + cleanup; the architectural intellectual work is done.
- Hot path UNTOUCHED through every commit — verify via `calls_graph_diff verify` post-WIP2g cascade.
- The shadow-window staleness IS a real architectural caveat for GUI runtime mutations too (Step 6 wires GUI sync). Both close at WIP2g flat-field deletion.
- If you find yourself writing complex plumbing, check `DESIGN_SPECS/README.md` "I need to..." section first. This ship's 4 NEW DESIGN_SPECs are the canonical applications; reference them rather than inventing parallel structures.
