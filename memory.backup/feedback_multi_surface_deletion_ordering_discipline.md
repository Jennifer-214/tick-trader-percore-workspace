---
name: feedback-multi-surface-deletion-ordering-discipline
description: "When deleting a feature/cfg/symbol spanning ≥3 files with compile-time interdependencies, enumerate deletion sites + classify by deletion-kind + sequence per leaves-first ordering (operator-facing docs first → stale comments → log strings → GUI gating → TUISnapshot field + caller updates → tests → sister wrapper cohort → centralized branches → unconditionalize boot-spawn gate → cfg field surface last). Without leaves-first ordering, wrong order → mid-WIP compile-fail (LOUD failure but high rework cost). B14 NEW pillar in implementation-layer-blindspot-taxonomy.md Stage 2 DRAFT."
metadata:
  node_type: memory
  type: feedback
  originSessionId: f7bb757d-2b7c-4ba6-9c4a-1c7d60bff493
  sister_specs: [feedback_enumerate_consumers_before_registry_row_deletion.md, feedback_unconditionalization_latent_assumption_audit.md, feedback_operator_facing_doc_cohort_at_cfg_deletion.md, feedback_archived_changelog_preservation_discipline.md, feedback_structural_fix_for_recurring_class.md, feedback_no_defer_for_effort.md, feedback_cpp17_inline_variable_for_shared_state_across_tus.md, feedback_test_change_enumeration_per_plan_body.md, feedback_verify_symbol_existence_at_plan_drafting_time.md]
  tags: [deletion-discipline, enumeration-discipline]
---

**When deleting a feature that spans multiple files** (cfg field removal / API surface removal / cohort wrapper deletion / centralized-arch deprecation), the deletion CAN'T be a single grep-and-delete. Each deletion site has compile-time interdependencies; wrong ordering → mid-WIP compile-fail.

**Discipline:** before coding starts, enumerate deletion sites + classify each by **deletion-kind** + sequence per **leaves-first ordering** (sites with no downstream compile dependency first; sites consumed by others last).

**Why:** Codified 2026-05-26 PM at `.B.4` v1.7.5 WIP-12 cycle after /blindspot-scan + /merge-scan audits surfaced B14 pillar candidate during HIGH-RISK pre-amendment gate for `engine_arch` cfg field deletion. Original v1.7.4 scope framed deletion as "8 conditional branches + 3 sister wrappers + cfg field + parser + TUISnapshot + GUI gating". Actual surface verified via operator-directed `rg` sweep + B-Plus v0.4 generator mode: **17 files / 81 occurrences** spanning 9 code files + 4 operator-facing docs + 6 archived changelogs (LEAVE) + 3 stale comments. Without leaves-first ordering, deleting cfg field BEFORE deleting consumers → all consumer sites compile-fail simultaneously → rebuild cycle waste.

**Deletion-kind classification (per B-Plus v0.4 `--gen-deletion-cohort` heuristic):**

| Kind | Example | Ordering |
|---|---|---|
| `operator-facing-doc` | `README.md:195` `engine_arch = per_core_slow` example | LEAVES (first — no compile dependency) |
| `stale-comment` | `OrderManager.hpp:261` "future per-core slow-path threads in engine_arch=" | LEAVES (cleanup) |
| `log-string` | `EngineSharded.hpp:2506` fprintf engine_arch log | LEAVES (cleanup or sister-log replacement) |
| `version-history-comment` | `Version.hpp:66` cfg field comment list | LEAVES (cleanup) |
| `GUI-gating` | `DashboardPanels.hpp:2036-2373` `s->engine_arch == 1` (11 sites) | MID (4 UNCONDITIONALIZE-style + 4 DELETE-style + 3 misc per per-site classification) |
| `test-surface` | `controller_test.cpp:8721-8775` topology round-trip tests | MID (after GUI deletion; before fn signature change) |
| `cohort-wrapper` | `ControllerEventLoop.hpp:3435/3722/3796-3804` `EventLoop_TimeExit/_TrailingSLRatchet/_BreakevenOnProfit` (3 sister wrappers per Class 18 cohort delete rationale) | MID (after centralized branch deletion; before cfg field removal) |
| `DELETE-with-body` | `EngineSharded.hpp:1438/1453/...` `if (cfg.engine_arch != ENGINE_ARCH_PER_CORE_SLOW) {...}` negated branches | MID (delete branch + body; body is centralized-only dead code post-deletion) |
| `UNCONDITIONALIZE-body` | `EngineSharded.hpp:2484` `if (cfg.engine_arch == ENGINE_ARCH_PER_CORE_SLOW) { spawn... }` positive gate | MID (remove `if` wrapper; body becomes unconditional; **verify B15 latent assumptions before unconditionalizing**) |
| `enum-constant` | `ControllerConfig.hpp` `ENGINE_ARCH_CENTRALIZED` + `ENGINE_ARCH_PER_CORE_SLOW` constants | LATE (after all consumer sites deleted) |
| `cfg-field-row` | `CfgFieldRegistry.hpp:396` X-macro row | LATE (LAST per H17 framework discipline; row deletion auto-removes cfg field declaration + parser entry via auto-flow walker) |

**Leaves-first sequencing rationale:** sites with no downstream compile dependency (operator docs / stale comments / log strings) delete first — these can't break compile. Then GUI gating + test surface (downstream compile only via own file). Then cohort wrappers + centralized branches (downstream callers in same files). Then enum constants (consumed by branches above). Finally cfg field row (consumed by entire codebase; LAST per H17 framework discipline — row deletion auto-removes cfg field + parser entry via FOREACH_CFG_FIELD walker).

## How to apply

**When plan body proposes feature deletion spanning ≥3 files:**

1. **Run B-Plus v0.4 generator mode** at planning time:
   ```bash
   python3 tools/check_plan_body_symbol_existence.py --gen-deletion-cohort 'PATTERN'
   ```
   Output: comprehensive enumeration sorted by deletion-kind (leaves-first ordering per this discipline).

2. **Paste enumeration into plan body Phase A.6.5.c CSV artifact** at `plan_checks/<date>-<ship>-<pattern>-deletion-enumeration.csv` per Phase A.6.5.c discipline.

3. **Plan body Phase C deletion-step enumeration** lists per-WIP ordering matching leaves-first sequencing. Wrong order = mid-WIP compile fail (LOUD but wasteful rebuild cycles).

4. **Verification gate post-deletion:** `rg <pattern>` over production code surface (excludes archived changelogs per `feedback_archived_changelog_preservation_discipline`) returns ZERO post-WIP cohort delete.

## Recognition markers (when this rule applies)

- Plan body proposes deletion of cfg field (always crosses ≥3 files: cfg struct + parser + GUI gating + tests + docs)
- Plan body proposes API surface removal (cross-file caller updates)
- Plan body proposes cohort wrapper cohort delete (sister to Class 18 mirror discipline)
- Plan body proposes centralized-arch deprecation (cross-cutting branches)
- Plan body proposes enum constant removal (cross-file consumers)
- Any case where deletion target appears in `.cpp/.hpp` + `.md` + `.cfg.example` + `tests/` simultaneously

## Sister memories

- [[feedback_enumerate_consumers_before_registry_row_deletion]] — parent meta-rule (consumer enumeration before deletion); this rule is the ORDERING side at multi-file deletion shape
- [[feedback_unconditionalization_latent_assumption_audit]] — B15 sister pillar (UNCONDITIONALIZE-body kind specifically; latent per-arch assumption verification before gate removal)
- [[feedback_operator_facing_doc_cohort_at_cfg_deletion]] — operator-facing-doc kind specifically; sister to this rule's leaves-first ordering at doc layer
- [[feedback_archived_changelog_preservation_discipline]] — LEAVE classification specifically; archived changelogs preserved per timeless-doc principle
- [[feedback_structural_fix_for_recurring_class]] — parent meta-rule; B14 codification IS structural fix at deletion-ordering surface
- [[feedback_no_defer_for_effort]] — comprehensive single-ship deletion preferred over preserve-and-deprecate per Decision I full-surface-deletion architectural-merit

## Worked example

`.B.4` v1.7.5 — `engine_arch` cfg field deletion (17 files / 81 occurrences):

WIP-14 12-step leaves-first deletion ordering per Phase C Step C.B-full:

1. Pre-deletion verification gates (B12 STAMP_BOUND_CFG_DERIVED index shift + H6 TUISnapshot cache-line + B-Plus v0.4 cohort completeness)
2. DELETE 4 operator-facing doc references (README + QUICKSTART + cfg.example)
3. DELETE 3 stale code comment surfaces (Version.hpp + OrderManager.hpp + EngineCommon.hpp)
4. DELETE 5 fprintf log strings + comment refs
5. DELETE 11 GUI gating sites (4 UNCONDITIONALIZE + 4 DELETE + 3 misc)
6. DELETE TUISnapshot::engine_arch field + TUI_PopulateTopology fn signature change + 3 callers
7. DELETE 5 controller_test.cpp test surface sites
8. COHORT DELETE 3 sister wrappers (Class 18 cohort delete per F17)
9. DELETE 7 NEGATED centralized-arch branches at EngineSharded.hpp
10. UNCONDITIONALIZE 1 POSITIVE boot-spawn gate (B15 verification first)
11. DELETE cfg field surface (cfg field declaration + parser entry + enum constants)
12. POST-DELETION VERIFICATION (rg returns ZERO + 81-occurrence baseline → 0)

## Stage progression

- **Stage 2 DRAFT v1.0** landed at `.B.4` v1.7.5 WIP-12 — `DESIGN_SPECS/meta-disciplines/implementation-layer-blindspot-taxonomy.md` B14 pillar row (NEW addition; sister to B7/B8/B12 pillars)
- **Stage 3 first-canonical promotion** at Phase D ship close — this ship's 51-site B-full cohort = 1st canonical application
- **Stage 4 audit-time check** at WIP-12 — `/readiness` Check 41 sidecar (NEW; multi-surface deletion ordering verification when plan body proposes deletion crossing ≥3 files)
- **Stage 5 multi-agent audit** at WIP-12 — `/blindspot-scan` default `all` pillar additions (B14 fires alongside B1-B12)
- **Stage 6 STRUCTURAL ENFORCEMENT** at WIP-12 — B-Plus v0.4 `--gen-deletion-cohort` mode (operator-facing planning helper; produces leaves-first enumeration mechanically); `--verify-deletion-cohorts` mode queued for v0.5 IF Class 33 instances surface that generator mode doesn't catch (post-MVP per `feedback_framework_layer_payoff_diminishing_returns`)

## Trade-off

LEAVES-FIRST ordering adds ~5-15 min planning time per ship (vs naive grep-and-delete). Catches LOUD failure mode (compile-fail mid-WIP) BEFORE it happens. Rework cost without ordering: 30-60 min rebuild cycles × N retries until ordering converges. ROI overwhelmingly positive for multi-file deletions.

For simple deletions (1-file 1-site removal): this rule N/A; just delete + rebuild. The discipline scales WITH deletion-cohort size.

## When this rule applies

Per `feedback_categorical_triggers_over_hardcoded_refs`:

- Any feature/cfg/symbol deletion spanning ≥3 files
- Any cohort wrapper cohort delete (sister Class 18 mirror prevention)
- Any cfg field deletion (always crosses ≥3 files: struct + parser + GUI + tests + docs)
- Any centralized-arch / mode-flag deprecation (cross-cutting branches)
- Any enum constant deletion (cross-file consumers)
