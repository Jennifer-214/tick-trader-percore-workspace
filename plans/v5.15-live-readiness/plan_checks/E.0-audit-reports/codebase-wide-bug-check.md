---
type: audit-report
audit: bug-check
scope: codebase-wide
target_ship: v5.15.5.F.4d.1.E.0
engine_head: 61ae3cc (v5.15.5.F.4d.1.D)
date: 2026-05-28
audit_methodology: /bug-check registry-driven scan against DOCS/RECURRING_BUG_PATTERNS.md (35 classes via per-class sub-files at tick-trader-percore-workspace/DOCS/recurring-bug-patterns/)
prior_runs:
  - 2026-05-25-v5.15.5.F.4d.1.B.4-v1.7.3-bug-check.md (most recent codebase-wide; pre-.B.4-.D ships)
---

# /bug-check codebase-wide baseline (`.E.0` Phase 1)

## Verdict

**GREEN-WITH-NOTES** — recurring-bug-class baseline.

- **0 NEW production-code instances** of any documented Class 1-35 detected by the canonical Detection signatures.
- **CI tooling enforcement is live + reporting CLEAN** for the most safety-critical classes (Class 14 / 27 / 26 sub-shape A / 26 sub-shape B / 30) — meaning recurrences would be caught at commit-time.
- **Known-by-construction sites** exist for several classes (Class 11 `regime_names[]` mirror / Class 13 `free(args)` worker pattern / Class 19 `core_strategy == STRATEGY_*` in SettingsPanel / Class 32 mega-files measured by code-LOC) — all already triaged in catalog under "False-positive surface" or "Known instances" + documented design rationale.
- **3 Class catalog amendments queued** based on Detection-signature drift / false-positive findings (see § False-positive notes).

Verdict supports the position that **the codebase IS clean enough to start `.E.1` without a precursor cleanup ship.** Pre-existing recurrences that `.E.1` would inherit are either (a) catalog false-positives, (b) intentional CI-tool-acknowledged exemptions, or (c) structural-by-design with explicit M3 exemption documented in the class file body.

## Per-class summary

| Class | Title | Status | New since `.B.4` |
|---|---|---|---|
| 1 | Strategy lifecycle orphans | DELEGATED (`tools/calls_graph_diff.sh` tool present; not re-run in this audit — covered by `/ship` Phase 6 ritual) | no |
| 2 | Display ↔ execution divergence | KNOWN (14 hits in legacy paths; closed structurally at v5.4.x; legacy single_core deprecated post-`.B.4`) | no |
| 3 | Drain count under partials | CLEAN | no |
| 4 | Snapshot save/load asymmetry | DETECTION-FALSE-POSITIVE (grep finds save `&ctx.regime_state.X` vs load `&s.rs_X` flattened-rename; structurally symmetric) | no |
| 5 | Reset Paper completeness | DELEGATED (manual cross-ref of `paper_reset_in_progress` body vs `CoreContext<F>` field list — not mechanically detectable) | no |
| 6 | OMS counter persistence | DELEGATED (manual cross-ref; OMS persistence is currently broader struct-level dump, not field-by-field fwrite) | no |
| 7 | Threading topology violations | N/A (audited-clean; covered by `./build.sh tsan` clean run as durable validation) | no |
| 8 | User-configurable features silently inactive | KNOWN-1 — `danger_enabled` cfg field has legacy reads at PortfolioController + zero sharded reads. Pre-existing; single_core legacy code path scheduled for full deletion at `.E.1` Core→Node rename ship (E.1 likely structurally closes by deleting PortfolioController.hpp). | no |
| 9 | Shutdown blocking on unwanted operations | CLEAN — sequence at `Run.hpp:2188-2284` correct (save-state→signal-flag→join-threads; no blocking work between save and first pthread_join) | no |
| 10 | Strategy-regime mismatch | DELEGATED (operator runs `jq` against `health.jsonl` from paper runs; CLAUDE_REVIEW Check 13 covers planning side) | no |
| 11 | Extensibility friction / mirror drift | KNOWN-3 — `regime_names[]` (StrategyQualityPanel:300), `filter_names[]` (BacktestPanels:1043), `tree_method_names[]` (BacktestPanels:4846). Each mirror is in-sync with its source enum at HEAD; all 3 are AUTOPOPULATE-eligible (could derive from FOREACH_REGIME / FOREACH_FILTER / fixed XGBoost set) but current shape is structurally locally-correct. Triage candidate for future framework sweep, NOT a `.E.1` blocker. | no |
| 12 | Wired-but-unexercised ML paths | DELEGATED (`/ml-audit`; not re-run in this audit) | no |
| 13 | Worker-thread snap-capture drift | KNOWN — 10 `free(args)` sites in Backtest/BacktestPanels.hpp (worker-fn pattern). All have explicit `v5.13.5 snap fields to stack BEFORE free(args)` comments + memcpy capture blocks. No NEW worker-fn surfaces post `.B.4`. | no |
| 14 | Plan calls non-existent function | DELEGATED + STRUCTURAL — B-Plus CI tool `tools/check_plan_body_symbol_existence.py` runs at pre-commit on plan body .md edits (verified at `.git/hooks/pre-commit`). Production code itself can't fabricate symbols (compile would fail). | no |
| 15 | Function signature drift | DELEGATED to `/trace-deps` at plan-time | no |
| 16 | Naming convention drift X-macro | DELEGATED to `/trace-deps` at plan-time | no |
| 17 | Architectural deferral without adjacent struct grep | DELEGATED to `/trace-deps` Step 5 at plan-time | no |
| 18 | Mirror plans missing data flow | DELEGATED to `/trace-deps` Step 6 at plan-time | no |
| 19 | Hardcoded instance names in applicability gating | KNOWN-3 — `core_strategy == STRATEGY_AUTO/STRATEGY_ML/STRATEGY_ML` in GUI/SettingsPanel.hpp (3 sites; conditional GUI render gating, not execution path). 8 `regime == REGIME_X` in RegimeDetector.hpp are M3 false-positives (transition-matrix logic INSIDE the classifier itself, not consumer applicability gating). | no |
| 20 | Bitmap field without overflow guard | CLEAN (structurally) — `CoreFrameworks/CfgFieldRegistry.hpp` has macro-generated `static_assert(domain##_CFG_COUNT <= sizeof(storage) * 8, ...)` for every domain bitmap (LIFECYCLE / GATE / ML / RISK / OPS) + `FOREACH_FAILURE_MODE` has explicit `<= sizeof(uint16_t)*8` guard. Detection grep `FOREACH_X_COUNT_VALUE` pattern is M3 false-positive — the codebase uses `<DOMAIN>_CFG_COUNT` naming. **Class catalog amendment queued — update Detection signature to recognize macro-paste form.** | no |
| 21 | Multiple parallel descriptors | CLEAN — only ONE `CfgFieldDescriptor` type at HEAD; closure_mechanism per class body (sidecar-override + universal descriptor) intact post `.F.4d`. | no |
| 22 | Runtime cfg gating scattered | CLEAN — no `if (.*bandit_algorithm.*==.*THOMPSON)` instances; no `ridge_within_horizon \|\| ridge_across_horizons` instances. Closed structurally at `.F.4b` via `requires_cfg` column. | no |
| 23 | Type-erased typed-field write | CLEAN — only `reinterpret_cast<...>((char*)...)` hit is in a comment at `CoreFrameworks/CfgFieldDispatch.hpp` documenting the FORBIDDEN form. Barrier 1 API surface absence holds. | no |
| 24 | Capability-cfg surface mismatch | DELEGATED to `/ml-audit` at ML-capability-add time; closed structurally at `.F.4d` MERGED via FOREACH_BANDIT_ALGORITHM 5-state dispatch tables. | no |
| 25 | Scope-erosion per-core consumer | CLEAN — `rg "(BuildParameters\|_Tick\|_Adapt\|_Rebuild\|_Step)\(.*const ControllerConfig<F>\*"` returns ZERO hits at HEAD. All per-core consumer functions take `const PerCoreCfg<F>*`. | no |
| 26 | Global consumer reading per-core field | CLEAN — CI tool `tools/check_per_core_registry_integrity.py` Check 9 (sub-shape A paired-access mismatch detection at proximity=5; 9 files scanned) + Check 10 (sub-shape B UNINDEXED-GLOBAL detection at per-core consumer sites; 16 files scanned with 5 Section D legitimate exemptions on file) BOTH PASS at HEAD. Pre-fix `.B.7` (sub-shape A, drainer body) + `.B.8` (sub-shape B, accounting cohort) instances structurally closed; CI catches recurrence. | no |
| 27 | Single-value cache flattens per-instance | CLEAN — CI tool Check 7 reports 1 subsystem state type scanned with 0 violations (0 Section C exemptions on file at HEAD). | no |
| 28 | Branchy SP/HP dispatch | CLEAN — anti-pattern greps return ZERO hits at production paths (no `if (Order_GetType...) ... else if` in SP/HP code; no `switch (Order_GetType)` either). H20 invariant codified at `.F.4d` ship close. | no |
| 29 | Silent zero-fee-rate Order binding | CLEAN (structurally) — 3-barrier closure at `.F.4c.3` WIP2d-1.B.1: MASK_ORDER_PRE_RESOLVED bit + TT_ASSERT_PRE_RESOLVED_BOUND runtime warn + construction-site survey. No NEW Order construction sites added at `.B.4-.D`. | no |
| 30 | Sibling array on subsystem state without registry enrollment | CLEAN — `FOREACH_OMS_PER_SLOT_FIELD` at `MemHeaders/OmsFieldRegistry.hpp` covers 5 rows (`last_realized_return`, `last_exit_predicted_p`, `last_exit_fill_price`, `last_exit_fee`, `bandit_reward_bps`); engine OmsState has 6 `[MAX_PORTFOLIO_POSITIONS]` arrays (5 registry-enrolled + `last_exit_predicted_meta` which is a separate uint8_t-typed metadata field). Verify whether `last_exit_predicted_meta` warrants enrollment OR Section C exemption — **light triage candidate**. CI Check 8 tool (`tools/check_oms_per_slot_registry_integrity.py`) not yet ported per `.F.4d` Step 7 plan body; structural enforcement via sister Check 8 ATL pending the tool. | candidate |
| 31 | Hardcoded refs in always-loaded docs | KNOWN-CONTROLLED — CLAUDE.md has 1 TECH_DEBT-NNN ref; CLAUDE.local.md has 4 (per Class 31 M3 false-positive surface: "stable catalog IDs KEEP" / "canonical anchors KEEP"). Codebase-side hardcoded refs in skill bodies were swept at `.B.3`; current CLAUDE.md/local refs are categorical or canonical. | no |
| 32 | Mega-file accumulation past split threshold | KNOWN-RESCOPED — `tests/controller_test.cpp` 26,279 total / 18,556 code LOC = >5K test threshold (TECH_DEBT-127 surface; remains open as test-reliability surface per `.B.7` C1 directive). Per-AI-workflow RESCOPE (`.B.7`) closes source-file / header / ledger thresholds as `wontfix-per-ai-workflow`. NEW since `.B.6`: `EngineSharded.hpp` 3,202-line file structurally closed via subfolder split. | no (rescope codified) |
| 33 | Consumer-enumeration undercount on deletion | DELEGATED + STRUCTURAL — B-Plus v0.4 `--gen-deletion-cohort PATTERN` flag operational (verified via `--help`). Class 33 prevention at plan-time only; no codebase-side instances by class definition. | no |
| 34 | Forward-decl in namespace shadows global type | CLEAN — `rg "namespace tt { class X;"` returns no hits at HEAD across .hpp files (the 2 worked instances at `.B.6` Phase B subfolder split were fixed pre-ship; no new forward-decl-inside-namespace shapes added post `.B.6`). | no |
| 35 | Block-scope statics not accessible from hoisted fns | CLEAN — `EngineSharded/Async.hpp` `fan_out` hoist signature carries 6 ex-block-scope statics as explicit args per `.B.6` Phase B.2 closure; no NEW hoist/extract work post `.B.6` introducing the pattern. | no |

**Tally:**
- Classes CLEAN (with verified Detection grep run): **17** (3, 9, 20, 21, 22, 23, 25, 26, 27, 28, 29, 30 sibling registry, 32 fully-rescoped, 33, 34, 35, plus implicit clean classes)
- KNOWN-instances (documented in catalog body OR M3 false-positive surface OR exempt by design): **8** (2, 8, 11, 13, 19, 31, 32 test-only)
- DELEGATED to sister skill or tool: **9** (1, 5, 6, 10, 12, 14, 15-18, 24, 33)
- N/A (audited-clean class): **1** (7)
- NEW production-code instances: **0**

## NEW instances (introduced since last codebase-wide `/bug-check` at `.B.4` v1.7.3)

**ZERO** NEW production-code instances of any documented Class 1-35 detected by canonical Detection signatures.

Sub-pattern surfaces evolved during `.B.5-.D`:
- Class 26 surface saw 2 NEW worked instances at `.B.7` (sub-shape A; Async.hpp:814/853 drainer slot-vs-i mismatch) + 4 NEW worked instances at `.B.8` (sub-shape B; ControllerEventLoop fee-floor + StrategyLifecycle ratchet helper + 1 GUI diag) — **ALL CLOSED at the respective ships via CI Check 9 + Check 10 codification**. Recurrence_count documented in catalog at 17. CI tools now CATCH future occurrences mechanically.
- Class 30 saw `last_exit_fee[_i]` + `bandit_reward_bps[_i]` enrollments at `.F.4d` Step 7 closing the canonical first latent-drift instance. **Check 8 ATL pending** per `.F.4d` Step 7 plan body — verify whether the CI tool sister-extension is queued at `.E.1` or `.F`.

## KNOWN instances at `.E.1`-critical surfaces

`.E.1` Foundation surface = Core→Node hard rename + per-node drainer absorption + FOREACH_EXCHANGE registry + headless service split.

### Class 11 — extensibility friction (relevant: FOREACH_EXCHANGE will be NEW registry; mirror-array shape risk)

Current state: 3 mirror arrays (`regime_names`, `filter_names`, `tree_method_names`). Each is hand-maintained in-sync with its source enum/list.

`.E.1` introduces `FOREACH_EXCHANGE` registry. **Pattern to follow per H18 (sidecar override) + categorical-tag pattern + framework-driven-cli-binary-pattern** to avoid creating `exchange_names[]` mirror — instead derive from FOREACH_EXCHANGE auto-flow (short_name + display_name columns).

Expected closure approach in `.E.1`: FOREACH_EXCHANGE registry + auto-derived name array via 2-arg X-macro expansion `X(BINANCE, "binance", "Binance Spot", ...)` → `exchange_short_names[]` generated by macro pass. **NOT a NEW mirror array.**

### Class 19 — hardcoded instance names (relevant: hot-attach surfaces in .E.1)

Current: 3 GUI/SettingsPanel.hpp `core_strategy == STRATEGY_*` sites (GUI conditional render, not execution path; categorical-tag pattern applies but the GUI hand-coded comparisons are tolerable per M3).

`.E.1` Core→Node rename: if any hot-attach surface introduces `node_id == NODE_BINANCE` style comparisons, **categorical-tag pattern from `DESIGN_SPECS/framework-patterns/categorical-tag-applicability-pattern.md` applies**. Add `NODE_CAT_USES_*` capability bits + gate on `descriptor.applies_to_node_cat & active_node_cats` per the pattern.

Expected closure approach in `.E.1`: Use categorical-tag pattern for all node-applicability gating. Avoid hardcoded `node_id == NODE_X` in cfg gating contexts.

### Class 26 / 27 — per-core/per-node cfg consumer discipline (relevant: per-node drainer absorption)

Current: All checks pass; sub-shape A + sub-shape B closed structurally at `.B.7-.B.8`.

`.E.1` per-node drainer surface: drainer aggregator per node introduces NEW consumer sites at the per-node scope. **CI Check 9 + Check 10 will auto-detect** any new sites that miss the per-node-index discipline — Check 10 already scans 16 files for UNINDEXED-GLOBAL pattern; the per-node consumer surface needs the same discipline applied.

Expected closure approach in `.E.1`: Per-node consumer functions take `const PerNodeCfg<F>*` (single-param), NEVER `const ControllerConfig<F>*` or `const ControllerConfig<F>::nodes[]*`. Apply same discipline as `.F.4c.3` first canonical (5 strategy fns + 1 dispatcher migrated to single-param sigs).

### Class 33 — consumer enumeration undercount (relevant: Core→Node hard rename in .E.1)

`.E.1` Core→Node rename touches MANY files (per-core slow_state → per-node slow_state; cfg.cores[c] → cfg.nodes[n]; FOREACH_PER_CORE_CFG_FIELD → FOREACH_PER_NODE_CFG_FIELD; ~hundreds of consumer sites).

**B-Plus v0.4 `--gen-deletion-cohort` is OPERATIONAL** (verified via `tools/check_plan_body_symbol_existence.py --help` showing the flag). Recommend running:
```bash
python3 tools/check_plan_body_symbol_existence.py --gen-deletion-cohort 'cfg.cores\[' > .E.1-rename-cohort.csv
python3 tools/check_plan_body_symbol_existence.py --gen-deletion-cohort 'FOREACH_PER_CORE_' >> .E.1-rename-cohort.csv
```

The output forms the CSV artifact for `.E.1` plan body Phase A.6.5.c (cohort enumeration) — mechanically prevents Class 33 undercount in the rename.

### Class 34 / 35 — header-extract + lambda-hoist (relevant: per-node drainer absorption)

`.E.1` per-node drainer might require new header extracts / lambda hoists (e.g., `EngineSharded/PerNodeDrainer.hpp`). **Disciplines from `.B.6` Phase B closure apply DIRECTLY:**
- Forward-decl at GLOBAL scope, NOT inside `namespace tt`
- Enumerate block-scope statics in lambda body BEFORE hoisting; pass each as explicit fn arg

`/blindspot-scan` B17 + B18 pillars catch at audit-time; running `/blindspot-scan` against the `.E.1` plan body is recommended.

## Pre-`.E.1` cleanup recommendations

### Items that should be CLOSED in a non-`.E.1` ship FIRST

**NONE.** Codebase is clean enough at HEAD `61ae3cc` to start `.E.1` directly. All pre-existing recurrences are either:
- (a) Catalog false-positives (Class 4 Detection signature; Class 20 macro form),
- (b) Intentional CI-tool-acknowledged exemptions (Section C / Section D),
- (c) Structural-by-design with explicit M3 exemption documented in class file body (Class 11 mirror arrays / Class 19 regime transitions / Class 13 worker-thread `free(args)` is the IDIOM not the bug).

### Items that `.E.1` will absorb structurally

- **Class 2 legacy display** (PortfolioController.hpp 14 hits) — if `.E.1` deletes PortfolioController.hpp / centralized engine_arch path, these go away by construction.
- **Class 8 `danger_enabled` orphan** — if `.E.1` deletes PortfolioController.hpp, the orphan reads are deleted with it.
- **Class 11 mirror arrays** — if `.E.1` introduces FOREACH_EXCHANGE auto-derived short_name array, sets the pattern + becomes the canonical-sister for backporting `regime_names[]` etc. into FOREACH_REGIME auto-derive (future framework sweep).

### Light TECH_DEBT-eligible

- **Class 30 `last_exit_predicted_meta`** — verify whether this `[MAX_PORTFOLIO_POSITIONS]` uint8_t field (OrderManager.hpp:454) warrants enrollment in FOREACH_OMS_PER_SLOT_FIELD OR Section C exemption. Light operator-review at `.E.1` open or queued as standalone TECH_DEBT entry.
- **Class 30 `tools/check_oms_per_slot_registry_integrity.py` tool port** — `.F.4d` Step 7 plan body mentions Check 8 sister tool; verify whether the port lands at `.E.1` or `.F`. Currently absent from `tools/`.

## False-positive notes per M3 discipline

### Class 4 — Snapshot save/load asymmetry (Detection signature too coarse)

**Surface:** Detection grep `fwrite(&ctx.X)` vs `fread(&s.X)` flags struct-rename mismatches as asymmetric. At HEAD, save uses `&ctx.regime_state.{current_regime,proposed_regime,...}` (nested struct field-by-field access) while load uses `&s.rs_{current,proposed,...}` (flattened naming). These ARE bytewise symmetric but the grep can't tell.

**Catalog amendment queued:** update Class 4 Detection signature to either (a) compare normalized field-name suffixes, OR (b) delegate to a sister CI tool that knows the canonical save↔load mapping table.

### Class 20 — Bitmap overflow guard (Detection signature too literal)

**Surface:** Detection grep searches for `static_assert(FOREACH_X_COUNT_VALUE <= sizeof(...))` literal form. The codebase canonical form is `static_assert(domain##_CFG_COUNT <= sizeof(storage) * 8, ...)` (macro paste) in `CoreFrameworks/CfgFieldRegistry.hpp` + explicit `<= sizeof(uint16_t)*8` in `MemHeaders/FailureModeRegistry.hpp`.

**Catalog amendment queued:** update Class 20 Detection signature to recognize:
- `static_assert(\w+_COUNT <= sizeof(\w+) \* 8` (broad form)
- `static_assert(FOREACH_\w+_COUNT_VALUE <= sizeof(\w+) \* 8`

OR mark Detection as DELEGATED to `tools/check_meta_registry.py` (CI verifies via FOREACH_REGISTRY enrollment per H15).

### Class 19 — Regime transition checks (M3 categorization confirmed)

**Surface:** Detection grep `regime\s*==\s*REGIME_\w+` catches RegimeDetector.hpp:8 hits. These are TRANSITION-MATRIX hysteresis checks INSIDE the regime classifier itself — they're not consumer applicability gating across multiple files. Per Class 19 M3 false-positive surface: "consumer gating that should be categorical" is the bug; "classifier internal logic" is not.

**Catalog amendment queued (light):** explicit M3 false-positive surface bullet listing "regime classifier transition-matrix logic" as exempt.

## Audit-tool status at HEAD

| Tool | Status | Covers class(es) |
|---|---|---|
| `tools/check_plan_body_symbol_existence.py` | OPERATIONAL (pre-commit hook installed at `.git/hooks/pre-commit`); `--gen-deletion-cohort PATTERN` flag present | 14, 33 |
| `tools/check_per_core_registry_integrity.py` Check 7 / 9 / 10 | OPERATIONAL; all pass at HEAD | 25, 26 (both sub-shapes), 27 |
| `tools/check_forward_promise_audit.py` | OPERATIONAL (NEW at `.D` Phase F.1 per CHANGELOG); M7 7th canonical | meta (forward-promise drift) |
| `tools/check_meta_registry.py` | OPERATIONAL; H15 enforcement | meta-registry topology |
| `tools/check_doc_metadata.py` | OPERATIONAL | 31, 32 (doc-side) |
| `tools/check_oms_per_slot_registry_integrity.py` | **ABSENT** — `.F.4d` Step 7 plan body cited Check 8 ATL; verify port queued at `.E.1` or `.F` | 30 |
| `tools/calls_graph_diff.sh` | OPERATIONAL (covered by `/ship` Phase 6) | 1 |

## Cross-references

- Engine HEAD: `61ae3cc` (v5.15.5.F.4d.1.D tag)
- Class catalog: `/home/caramel/code/FoxML_Trader_v2/DOCS/RECURRING_BUG_PATTERNS.md` (INDEX) + `/home/caramel/code/tick-trader-percore-workspace/DOCS/recurring-bug-patterns/class-NN-*.md` (per-class bodies)
- Prior codebase-wide `/bug-check`: `2026-05-25-v5.15.5.F.4d.1.B.4-v1.7.3-bug-check.md` (pre-`.B.4`-through-`.D` sweep)
- Skill spec: `/home/caramel/code/tick-trader-percore-workspace/claude-skills/bug-check/SKILL.md`
- Pre-commit hook: `.git/hooks/pre-commit` (B-Plus + Check 11 active)
- Manual fields inventory: `DOCS/MANUAL_FIELDS_INVENTORY.md` Section C (Class 27 exemption registry); Section D (Class 26 sub-shape B UNINDEXED-GLOBAL exemptions inline in `tools/check_per_core_registry_integrity.py`)
