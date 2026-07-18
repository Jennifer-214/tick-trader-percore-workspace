---
type: meta-discipline
stage: 3-first-canonical
version: 1.1
established: 2026-05-18
tags: [doc-discipline, meta-discipline, framework-discipline]
surface: [registry]
sister_specs: [doc-frontmatter-convention.md, categorical-triggers-in-always-loaded-docs.md, pattern-codification-lifecycle.md]
applies_at_skills: []
---

# Doc tag vocabulary (canonical tag index)

**Established:** 2026-05-18 (v5.15.5.F.4d.1.B.3 doc-layer refresh — codified after Caramel surfaced the need for a tag index system as part of institutional-memory architecture)
**Status:** Stage 2 DRAFT v1.0 — first canonical application queued at `.C` candidate ship (institutional-memory rollout)
**Cross-references:**
- Sister: `doc-frontmatter-convention.md` (the discipline that USES this vocabulary)
- Sister: `categorical-triggers-in-always-loaded-docs.md` (the doc-discipline this enables)
- Sister: `pattern-codification-lifecycle.md` (lifecycle tags map to Stage 1-6 here)

---

## Purpose

Single source of truth for all valid tags used in YAML frontmatter across the doc system. Three orthogonal axes (CONCERN / SURFACE / LIFECYCLE) provide multi-dimensional retrieval via `rg "^<axis>:.*\b<tag>\b"`.

CI tool `check_doc_metadata.py` (queued at `.C` candidate ship) validates every `tags:`, `surface:`, `lifecycle:` field against this vocabulary. Typos / undefined tags fail CI.

---

## CONCERN axis (what the doc is ABOUT)

| Tag | Description |
|---|---|
| `framework-discipline` | X-macro registries, auto-flowing dispatch, registry-coverage CI checks, meta-registry topology |
| `audit-methodology` | Pre-coding / post-ship audit shapes, /precoding-audit-gate orchestration, blind-spot taxonomies |
| `data-oriented-design` | Layout, alignment, bit-packing, cache discipline, struct field clustering by access pattern |
| `concurrency` | Thread isolation, sync primitives (SPSC / seqlock / atomic flags), false-sharing prevention |
| `wire-format` | Byte preservation, locale pinning, HMAC signing, stamp body parity, replay determinism |
| `doc-discipline` | Doc-layer separation, categorical triggers, frontmatter convention, tag discipline |
| `plan-template` | Plan body / MASTER / handoff / postmortem template specs |
| `ledger-discipline` | TECH_DEBT / PARITY_ISSUES / FEATURE_LOOKUP / HOT_PATH_CHANGELOG entry shape |
| `meta-discipline` | Audit-methodology-gap codification (M1-M4 style); meta-rule layer above patterns |
| `operator-collaboration` | Memory-rule-shaped collaboration discipline; behavioral rules; communication norms |
| `structural-fix` | Patterns that close bug classes structurally rather than patching symptoms |
| `pattern-codification` | Lifecycle Stage 1-6 maturation discipline; promotion criteria; spec maturity tracking |
| `branchless-discipline` | Branchless dispatch patterns; cmov / mask-select / fn-pointer-table choice (H7/H20) |
| `fixed-point-math` | FPN_Binary<F> usage; accounting paths; precision rules; locale-independent emit (H4) |
| `latency-discipline` | Hot-path / slow-path / drainer cadence budgets; per-tick cost framework |
| `failure-observability` | Silent-failure detection; PerCoreSnap field allocation; per-class observability fields |
| `cross-tool-decoupling` | Framework-driven C++ CLI binaries replacing bash mirrors; wire format single-source-of-truth |
| `decoupling-roadmap` | GUI ↔ runtime decoupling; headless engine + viewer architecture; long-horizon roadmap |
| `ssot` | Single source of truth discipline; merge-vs-mirror reasoning; SSoT violations + closure |
| `cpp17` | C++17-specific features + discipline (inline variables, if-constexpr, structured bindings) |
| `header-only` | Header-only library convention; no `.cpp` definitions; template-heavy code |
| `shared-state` | Cross-TU storage discipline; linker semantics; symbol visibility |
| `linker-deduplication` | vague linkage; inline-variable dedup mechanism; ODR safety |
| `mirror-prevention` | Class 18/21/26 family; mirror-incomplete + parallel-registry closures |
| `code-loc-counting` | Threshold-counting methodology (code-LOC vs total-LOC; comment/blank exclusion) |
| `inline-variable` | C++17 `inline` keyword on variables; sister to `header-only` |
| `forward-decl-shadow` | Class 34 / B17; namespace-scope forward-decl shadowing global type |
| `block-scope-statics` | Class 35 / B18; block-scope `static` vars inaccessible from hoisted header fns |
| `subfolder-pattern` | File-size discipline subfolder split form (INDEX shim + sub-files) |
| `wontfix-rationale` | Closure-without-action discipline; explicit deferral with rationale for non-action |
| `planning-discipline` | How to plan — plan-body shaping, explicit end-goals, plan-right-over-fast, scope, drafting rigor (distinct from `plan-template` = template specs) |
| `enumeration-discipline` | Enumerate-the-set-before-acting — consumers before deletion, members before a categorical claim, args before extract, statics before hoist |
| `deletion-discipline` | Multi-surface deletion ordering, unconditionalization latent-assumption audit, operator-facing-doc cohort, leaves-first sequencing |
| `scope-discipline` | Proportionate response, diminishing-returns inflection, future-headache-vs-optimization, over-engineering boundary, defer-vs-do-now |
| `session-continuity` | Handoff / compaction / decision-log / capture-audit / sister-cohort + forward-promise propagation across sessions |
| `test-discipline` | Test-change enumeration per plan, test-strength / anti-regression, characterization / golden-master test shape |
| `migration-discipline` | Architecture-wide rename / terminology evolution, close-the-class-vs-migrate-every-site, archived-record preservation, proactive rename surfacing |
| `refactor-discipline` | Boundary-stable refactors, reduce-touch-sites, action-parameterized walkers, safe substring/member-access edits |
| `user-profile` | Who the operator is — working style, motivations, ADHD/deferred-reward, public-work stakes, structure-as-cognition |
| `project-state` | Ongoing project facts not derivable from code/git — sprint trajectory, cadence conventions, repo quirks, queued work |
| `capital-safety` | Capital-bearing money paths; accounting correctness; loss-prevention guards; dead-capital-path / Knight-Capital discipline (Class 40-43 cohort) |
| `determinism` | Cross-run / cross-binary / cross-locale byte equivalence; reproducibility; replay-determinism nets (engine priority #2) |
| `scale-invariance` | H22 per-node purity / horizontal scaling — a node's (and cluster's) state is a pure function of its OWN local inputs; the (N+1)th node requires ZERO change to existing per-shard logic |
| `reconcile-recovery` | Boot/restart recovery semantics — venue-truth reconciliation, missed-fill replay, attribution, net-position reconstruction (vs overwrite/aggregate); the boot-reconcile-collapse class |
| `future-expansion` | LIVING-spec discipline — a spec documents a FOUNDATION now + a planned mechanism DEFERRED to a real future need (build-when-earned, NOT speculative); the `§ Future expansion` section is the gated growth, built only when the need actually arrives |
| `capital-bearing` | Unit whose correctness = MONEY (touches a position / balance / fee / P&L / price-qty) — the classify counterpart to `capital-safety` (the discipline). Code tag `[CAPITAL_BEARING]` (E.1.2.A) |
| `non-capital` | Unit with NO money-correctness stake (feature math / telemetry / display). Code tag `[NON_CAPITAL]` |
| `decimal` | Money repr — `FixedPoint<10,8>` decimal (venue-exact 8dp); the H4 money path. Code tag `[DECIMAL]` |
| `binary-fp` | Feature repr — `FPN_Binary<F>` binary fixed-point; the H4 feature path. Code tag `[BINARY_FP]` |
| `int` | Plain integer repr (counts / ids / offsets / bitmaps). Code tag `[INT]` |
| `float-display-only` | `double`/`float` used for DISPLAY only — never on hot/slow math (H4). Code tag `[FLOAT_DISPLAY_ONLY]` |
| `frozen` | Relies on staying byte-identical across changes — determinism baseline / wire-frozen body (regen DELIBERATELY, never casually). Code tag `[FROZEN]` |
| `golden` | Protected by a golden-master fixture (sister to `frozen`). Code tag `[GOLDEN]` |
| `critical` | Load-bearing on a capital / determinism / latency path — failure is high-impact. Code tag `[CRITICAL]` |
| `supportive` | Auxiliary role — not on the critical path. Code tag `[SUPPORTIVE]` |
| `helper` | A helper / utility unit (extracted shared logic). Code tag `[HELPER]` |
| `entry-point` | A top-level entry point (boot / dispatch / main loop). Code tag `[ENTRY_POINT]` |
| `deprecated` | Unit discouraged / superseded but still LIVE (a successor exists; kept for compat — e.g. the `*_LegacyV1` wire-compat readers). Code tag `[DEPRECATED]` (E.1.2.A) — MARK, never delete (H21 tombstone sister; `[OUTDATED_INFO]` is for stale COMMENTS, this is for whole UNITS). Browsable: `foxtag units --tag DEPRECATED`. |
| `marked-for-deletion` | Unit scheduled for removal — dead/rotted, no live consumer OR a retirement is planned. Code tag `[MARKED_FOR_DELETION]` (E.1.2.A) — the deletion QUEUE; a human deletes, never auto (capital codebase). |

---

## SURFACE axis (what the doc TOUCHES)

| Tag | Description |
|---|---|
| `hot-path` | ExecutionCore / BG_Evaluate / SG_Evaluate / per-tick branchless dispatch |
| `slow-path` | slow_state / Regime_Classify / RebuildOneCore / per-poll-interval rebuilds |
| `oms-drainer` | OMS_DrainSubmit / OrderManager_Tick / fill handling / drainer cycle |
| `producer` | DataStream fan_out / ws-tick parsing / per-tick replication |
| `parser` | JSON parsing / cfg field parser / simdjson / fast_float entry points |
| `registry` | X-macro registries / FOREACH_* walks / MetaRegistry enrollment |
| `wire-format` | HMAC-signed bodies / stamps / snapshots / RunHistory emit |
| `ml-inference` | Model prediction / FeatureStandardizer / scaler / ConfidenceScorer / drift checks |
| `cfg-flow` | Cfg parser → ControllerConfig → per-node override → GUI render → stamp-binding |
| `gui-thread` | ImGui / panels / TUISnapshot / GUI publish; SDL2 / OpenGL3 |
| `training` | Backtest / train-time / model-zoo loading / WF / Held-Out |
| `paper-test` | Simulated trading / paper-mode boot / sandboxed live path |
| `live-trading` | Binance live REST + WS / kill switch / circuit breaker / paper→live transition |
| `backtest` | Backtest_Run / BacktestSharded / replay determinism |
| `boot-time` | Engine startup / warm-restart / recovery / boot-gate |
| `ci-tooling` | tools/check_*.py / tools/calls_graph_diff.sh / CI checks at commit time |
| `test-infrastructure` | controller_test / parity_harness / test fixtures / test_common.hpp |
| `bitmap-packed` | uint{8,16,32,64}_t bit-packed slot structures + BITMAP_*/MBS_* accessors |
| `cross-tool` | tools/*.sh + tools/*_cli.cpp binaries; cross-tool wire-format surfaces |
| `doc-pipeline` | Doc-system generation / index / frontmatter discipline / metadata-audit surface |
| `plan-pipeline` | Plan body drafting / sub-master / handoff / postmortem doc shape |
| `handoff-pipeline` | Handoff doc creation + receiver-side verification (/handoff + /accept-handoff) |
| `header-split` | File-size discipline subfolder split / INDEX shim / sub-file boundaries |
| `helper-extraction` | Lambda hoisting / function extraction / shared-helper discipline (M5/M6 cohort) |
| `session-pickup` | Fresh-context onboarding / required reading / drift-check / TaskList recreation |
| `skill-pipeline` | claude-skills SKILL.md spec / pre-coding gate / sister-skill composition |
| `persistence` | Snapshot save/load / warm-restart recovery / RunHistory / ShardedSnapshot money-exact round-trip |
| `engine` | Core trading-engine code (CoreFrameworks / Strategies / ExecutionCore / OMS) — the shipped hot/slow path. Code tag `[ENGINE]` |
| `gui` | GUI component (ImGui panels / rendering) — broader than the `gui-thread` surface. Code tag `[GUI]` |
| `ml` | ML component (features / model / inference / training) — broader than the `ml-inference` step. Code tag `[ML]` |
| `data-plane` | The market-data ingest / fan-out / replication plane. Code tag `[DATA_PLANE]` |
| `monitoring-plane` | The observability / telemetry / snapshot / metrics plane. Code tag `[MONITORING_PLANE]` |
| `dev-plane` | Dev-apparatus (tools / tests / docs / CI) — NOT shipped engine code. Code tag `[DEV_PLANE]` |

---

## LIFECYCLE axis (where in pattern lifecycle per `pattern-codification-lifecycle.md`)

| Tag | Stage | Description |
|---|---|---|
| `1-problem` | Problem identification | Issue surfaced; no codification yet |
| `2-draft` | DESIGN_SPEC drafted | Body written; awaiting first canonical reference |
| `3-first-canonical` | First reference landed | First ship/codebase application; pattern proven minimally |
| `4-cohort` | Multiple applications | ≥2 cohort applications; pattern proven; promotion candidate |
| `5-claude-md` | CLAUDE.md item promotion | Promoted to CLAUDE.md headline + Hard invariant table OR DESIGN_PHILOSOPHY § N |
| `6-cadence-locked` | Periodic enforcement | Quarterly audit + CI tool enforcement + skill cadence locked |

Lifecycle tag is SINGULAR (one value per doc); CONCERN + SURFACE are LISTS (multiple tags).

---

## Tag combination examples

**A typical framework-pattern spec (DOD-flavored):**
```yaml
type: framework-pattern
stage: 4-cohort
tags: [framework-discipline, data-oriented-design]
surface: [hot-path, registry, bitmap-packed]
```

**A meta-discipline spec (audit-methodology-gap):**
```yaml
type: meta-discipline
stage: 3-first-canonical
tags: [audit-methodology, meta-discipline]
surface: [registry]
```

**An operator-collaboration memory rule:**
```yaml
type: feedback
stage: 5-claude-md
tags: [operator-collaboration, doc-discipline]
surface: []
```

**A wire-format pattern spec:**
```yaml
type: wire-format-pattern
stage: 3-first-canonical
tags: [wire-format, framework-discipline]
surface: [wire-format, ml-inference, parser]
```

**A plan template spec:**
```yaml
type: plan-template
stage: 3-first-canonical
tags: [plan-template, doc-discipline, pattern-codification]
surface: []
```

---

## Retrieval recipes

(Documented canonical in `CLAUDE.md § How to find anything` — copy here for context.)

**By concern tag:**
```bash
rg "^tags:.*\bframework-discipline\b" DESIGN_SPECS/
rg "^tags:.*\bdata-oriented-design\b"
```

**By surface tag:**
```bash
rg "^surface:.*\bhot-path\b"
rg "^surface:.*\bregistry\b.*\bml-inference\b"  # both surfaces
```

**By lifecycle:**
```bash
rg "^stage: 2-draft" DESIGN_SPECS/    # promotion candidates
rg "^stage: 4-cohort" DESIGN_SPECS/   # mature; ready for CLAUDE.md promotion
```

**Combined (compose):**
```bash
# All framework-discipline specs at hot-path surface, Stage 3+:
rg -l "^tags:.*\bframework-discipline\b" DESIGN_SPECS/ | \
  xargs rg -l "^surface:.*\bhot-path\b" | \
  xargs rg -l "^stage: [3-6]-"
```

---

## Adding new tags (easy)

**Concern + Surface tags are EASILY EXTENSIBLE.** Adding a new tag is 1 line:

1. Append row to the CONCERN or SURFACE axis table in THIS DOC: `| <tag> | <one-line description> |`
2. Use it in your doc's `tags:` or `surface:` frontmatter list
3. Done

**No min-count gatekeeping.** First doc to introduce a tag is fine — usefulness emerges over time. CI tool `check_doc_metadata.py` (queued) validates tag-EXISTS-in-vocabulary; it does NOT validate min-usage.

**Periodic `/metadata-audit` (advisory only):** reports singleton tags (used by only 1 doc) as consolidation CANDIDATES. Decision to consolidate is YOUR call, not auto-applied. Singletons often legitimately describe a unique concern.

**When to consolidate:**
- Two tags clearly mean the same thing (e.g., `wire-format` + `byte-preservation` would consolidate to one)
- Tag name was unclear; better name surfaces later (rename it)
- Tag legitimately splits in two (one becomes two more specific tags)

**When to NOT consolidate:**
- Tag is singleton because it's NEW; usage will grow
- Tag is intentionally specific (precision > generality)
- No clear better grouping exists

**Lifecycle tag:** FIXED (1-problem through 6-cadence-locked). Adding new stages requires amending `pattern-codification-lifecycle.md` first since these tags are TIED to that lifecycle.

**Renaming tags:** safe; CI catches all sites; `rg` finds usages mechanically. No discipline barrier.

**Removing tags:** safe if zero usage. CI catches stale references. Periodic audit reports dead tags.

---

## Tag → files index (reverse lookup)

**Don't hand-maintain a tag-index file.** The canonical reverse-lookup is `rg`:

```bash
rg -l "^tags:.*\bframework-discipline\b" DESIGN_SPECS/    # files using this concern tag
rg -l "^surface:.*\bhot-path\b"                            # files at this surface
rg -l "^applies_at_skills:.*\b/readiness\b"                # what /readiness loads
```

Hand-maintained tag index DRIFTS as new docs add tags. Grep computes the current state in <1s.

**Optional snapshot:** `/index-rebuild` skill (queued at `.C` candidate ship) can regenerate a `DESIGN_SPECS/TAG_INDEX.md` snapshot at sprint-close. AUTO-GENERATED; never hand-edited. Useful for static reading (catalog browse); grep remains source of truth.

---

## Drift detection

**`/metadata-audit` skill (Stage 1 — queued at `.C` candidate ship) reports:**
- Specs with undefined tags (typos)
- Specs missing required frontmatter fields
- Singleton tags (used by only 1 doc — consolidation candidates)
- Stage 2 DRAFTs older than N sprints (promotion candidates)
- Broken sister-doc links (bidirectional verification)
- Filesystem path mismatches with `type:` frontmatter (folder restructure post TECH_DEBT-113)

---

## Cross-references

- Sister: `doc-frontmatter-convention.md` (the discipline using this vocabulary)
- Sister: `categorical-triggers-in-always-loaded-docs.md` (the doc-discipline this enables)
- Sister: `pattern-codification-lifecycle.md` (Stage 1-6 lifecycle mapping)
- Sister: `categorical-tag-applicability-pattern.md` (in-code tag applicability pattern; sister at code level)
- Sister: `meta-registry-pattern-for-codebase-registry-discipline.md` (FOREACH_REGISTRY meta-registry; this is the doc-level analog)
- Memory: `feedback_categorical_triggers_over_hardcoded_refs.md` (going-forward rule)
- Memory: `feedback_claude_md_guidelines_not_stuff_to_do.md` (doc-layer separation rule)
- TECH_DEBT-115 (institutional-memory rollout; this spec lands Stage 3 first canonical at `.C` candidate ship)
- CLAUDE.md § How to find anything (the retrieval guide referencing this vocabulary)

---

## Pattern lifecycle

- **Stage 1 (problem identification):** Caramel surfaced 2026-05-18 — "well need like a tag index system, with a brief description of what is what i think"
- **Stage 2 (DESIGN_SPEC draft):** THIS DOC (2026-05-18)
- **Stage 3 (first canonical reference):** queued at `.C` candidate ship — first DESIGN_SPEC uses frontmatter validated against this vocabulary
- **Stage 4 (cohort migration):** all 80+ DESIGN_SPECS migrate to frontmatter using this vocabulary
- **Stage 5 (CLAUDE.md promotion):** ALREADY landed — CLAUDE.md § How to find anything references this vocabulary
- **Stage 6 (cadence-locked):** CI tool `check_doc_metadata.py` enforces vocabulary at commit time; quarterly `/metadata-audit` reports drift

---

**End of doc-tag-vocabulary v1.0 DRAFT.** Stage 3 first canonical queued at `.C` candidate ship.
